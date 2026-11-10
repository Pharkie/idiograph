"""A researcher's own tables of PETs and LPETs read and matched to a participant's statements (ayabuild34, 9 November
2026, the Ayahuasca plan's builds 3 and 4, Adam, 9 November about 13:40).

A table of PETs, one per timepoint, has a row for each statement placed: PET, Sub-theme, Experiential statements,
Location and Quote, a PET's or sub-theme's title written once and carried down the rows under it. Each row is
matched to a statement of the participant at that timepoint: by its words first, then by a ratio of `FUZZY` or more
against a statement of the passage at its Location, then against one of the passage its quote is in. Adam's answer
3: the table is later, so where its wording differs it replaces the nearest statement on that passage, a fuzzy
match's and, below `FUZZY` but at `CLOSE` or more, the passage's nearest statement's. Where nothing on the passage is
close, the row is added there as a new statement with its quote, or skipped, as the command says. A statement two
rows name is placed once, at the first, and the second named as a duplicate.

A table of LPETs has a row for each LPET: its title on the first line of its first cell and its description on
the second, then a cell for each timepoint, his summary and short quotes. Each cell goes into the LPET's note as a
paragraph headed by the timepoint (Adam's answer 5), and the PETs it draws on are proposed by matching the cell's
quotes and lines to that timepoint's PETs' statements (Adam's answer 4: he confirms them on the canvas).

Only reading and matching are here. The writes go through the command line's own ops, `turn write` for a
statement reworded or added, `board new` for the board, `gets new` and `gets apply` for the LPETs (idiograph_cli).
"""
from __future__ import annotations

import difflib
import re
from pathlib import Path

import convert
import i18n
import themes
import themes_ai

# a ratio of words at or above which a row is the same statement worded a little differently
FUZZY = 0.8
# and at or above which the passage's nearest statement is the one the table rewords, below it nothing is close
CLOSE = 0.5
# the seconds a Location may be off its passage's time and still name it
SLACK = 2
# the quotes of a cell of LPETs, in double inverted commas, straight or curly, of two words or more
CELL_QUOTE = re.compile(r"[\"“„]([^\"“”„]+?)[\"”]")
# where a quote is cut, as the turn screen cuts one: an ellipsis and a clarifying insert
CUTS = r"\s*(?:\.\.\.|…|\[[^\]]*\])\s*"

# a table of PETs' headings, each as `key` reads it
PET_HEADS = {
    "pet": ("pet", "pets", "theme", "personal experiential theme", "personal experiential themes", "pet title"),
    "sub": ("sub theme", "sub themes", "subtheme", "subthemes", "sub pet", "sub pets", "sub theme title"),
    "es": ("experiential statements", "experiential statement", "statements", "statement", "es"),
    "at": ("location", "time", "timestamp", "timecode", "at", "where"),
    "kq": ("quote", "quotes", "key quote", "key quotes"),
}
LPET_HEADS = ("lpet", "lpets", "longitudinal pet", "longitudinal pets", "theme", "themes", "title")


class TableError(Exception):
    """A table that cannot be read as asked, said in one line."""


def key(text) -> str:
    """A heading or a line as it is compared: lower case, every mark but the apostrophe a space."""
    return " ".join(re.sub(r"[^\w\s']", " ", str(text or "").replace("’", "'").lower()).split())


def ratio(a: str, b: str) -> float:
    return difflib.SequenceMatcher(None, key(a), key(b)).ratio()


def read_table(path: Path, sheet: str | None = None) -> tuple[list[str], list[list], str]:
    """A CSV's or an Excel file's headings and rows, an Excel file's at its sheet by name or its first with anything
    in it, and the sheet read, "" for a CSV."""
    path = Path(path)
    if not path.is_file():
        raise TableError(i18n.t("cli.table_import.no_file", path=str(path)))
    ext = path.suffix.lower()
    try:
        if ext in (".xlsx", ".xlsm"):
            info: dict = {}
            heads, rows = convert.table_of_xlsx(path, path.name, sheet, info)
            return heads, rows, str(info.get("sheet") or "")
        if ext in (".csv", ".tsv", ".txt"):
            if " ".join(str(sheet or "").split()):
                raise TableError(i18n.t("cli.import.sheet_for_excel"))
            heads, rows = convert.table_of_csv(path.read_text(encoding="utf-8-sig"))
            return heads, rows, ""
    except convert.Unreadable as exc:
        raise TableError(str(exc)) from None
    except (OSError, UnicodeDecodeError) as exc:
        raise TableError(i18n.t("cli.table_import.could_not_read", name=path.name, exc=exc)) from None
    raise TableError(i18n.t("cli.table_import.not_a_table", name=path.name))


def cell(value) -> str:
    """A cell's words, its lines kept, each line's spacing collapsed and empty lines dropped."""
    if value is None:
        return ""
    lines = [" ".join(x.split()) for x in str(value).replace("\r", "\n").split("\n")]
    return "\n".join(x for x in lines if x)


def at_seconds(value) -> int | None:
    """A Location as whole seconds: an Excel time, a fraction of a day as Excel keeps one, or a clock."""
    if isinstance(value, float) and 0 < value < 1:
        return int(round(value * 86400))
    return convert.seconds_of(value)


CLOCK = re.compile(r"(?<![\d:])\d{1,2}:\d{2}(?::\d{2})?(?![\d:])")


def ats_seconds(value) -> list[int]:
    """Every time a Location holds, in whole seconds and the order written: one time as `at_seconds` reads it, or
    each clock in a cell that holds several ("18:15 and 05:59", two lines, a comma, a slash or "&")."""
    one = at_seconds(value)
    if one is not None:
        return [one]
    if not isinstance(value, str):
        return []
    return [x for x in (convert.seconds_of(c) for c in CLOCK.findall(value)) if x is not None]


def at_said(seconds: int | None) -> str:
    if seconds is None:
        return ""
    h, rest = divmod(int(seconds), 3600)
    m, s = divmod(rest, 60)
    return f"{h}:{m:02d}:{s:02d}" if h else f"{m:02d}:{s:02d}"


# ------------------------------------------------------------------ a table of PETs

def pet_columns(heads: list[str]) -> dict:
    found: dict = {}
    for i, h in enumerate(heads):
        k = key(h)
        for role, words in PET_HEADS.items():
            if role not in found and k in words:
                found[role] = i
                break
    return found


def pet_rows(heads: list[str], rows: list[list], name: str) -> list[dict]:
    """Each row of a table of PETs with a statement, its PET's and sub-theme's titles carried down from the rows
    above, its Location in seconds and its quote, numbered as the sheet numbers it, the headings row 1."""
    cols = pet_columns(heads)
    if "es" not in cols:
        raise TableError(i18n.t("cli.board_import.no_statements_column", name=name, heads=", ".join(heads)))
    if "pet" not in cols:
        raise TableError(i18n.t("cli.board_import.no_pet_column", name=name, heads=", ".join(heads)))
    get = lambda r, role: r[cols[role]] if role in cols and cols[role] < len(r) else None
    out, pet, sub = [], "", ""
    for n, r in enumerate(rows, start=2):
        title = themes_ai.clean_label(get(r, "pet"))
        if title:
            pet, sub = title, ""
        under = themes_ai.clean_label(get(r, "sub"))
        if under:
            sub = under
        words = " ".join(cell(get(r, "es")).split())
        if not words:
            continue
        loc = get(r, "at")
        ats = ats_seconds(loc)
        out.append({"row": n, "pet": pet, "sub": sub, "statement": words, "at": ats[0] if ats else None, "ats": ats,
                    "location": cell(loc) if isinstance(loc, str) else at_said(at_seconds(loc)),
                    "quote": " ".join(cell(get(r, "kq")).split())})
    if not out:
        raise TableError(i18n.t("cli.board_import.no_rows", name=name))
    untitled = [x["row"] for x in out if not x["pet"]]
    if untitled:
        raise TableError(i18n.t("cli.board_import.no_pet_above", name=name, rows=", ".join(map(str, untitled))))
    return out


def pieces(quote: str) -> list[str]:
    body = themes.quote_words(quote)
    return [p for p in (key(x) for x in re.split(CUTS, body)) if p]


def quote_in(quote: str, text: str) -> bool:
    """Every piece of a quote, cut at an ellipsis or an insert, in the words in that order."""
    said, at, found = key(text), 0, False
    for p in pieces(quote):
        hit = said.find(p, at)
        if hit < 0:
            return False
        at, found = hit + len(p), True
    return found


def match_pets(rows: list[dict], turns: list[dict], interviewer: str, add: bool) -> list[dict]:
    """Each row of a table of PETs matched to a statement of `turns`, the passages of the participant's sheets at
    the timepoint as `turns_of` reads them, in their order. Each answer is the row with `how`: `exact`, `fuzzy`
    (with its `ratio`), `rewritten` (the passage's nearest statement, with its `ratio`), `added`, `skipped` or
    `duplicate` (with `of`, the row placed first), `key` the statement's key (a new statement's is set when it is
    written), `was` the words it had, `by` how the passage was found, and the passage's `sheet`, `passage` and
    `time`."""
    who = key(interviewer)
    statements = [{"key": themes.card_key(t["sheet"], t["row"], i), "text": s, "turn": t, "line": i}
                  for t in turns for i, s in enumerate(t.get("statements") or [])]
    taken: dict[str, int] = {}
    near = lambda t, at: abs((t["seconds"] if t.get("seconds") is not None else 10 ** 9) - at)
    nearest = lambda t, ats: min((near(t, a) for a in ats), default=10 ** 9)
    own = lambda t: key(t.get("name")) != who or not who
    out = []
    for r in rows:
        m = dict(r, how="", ratio=None, key="", was="", by="", sheet="", passage=None, time="", why="")

        def place(s: dict, how: str, by: str, score: float | None = None) -> None:
            t = s["turn"]
            m.update(how=how, key=s["key"], by=by, sheet=t["sheet"], passage=t["row"], time=t.get("time") or "",
                     ratio=None if score is None else round(score, 2), was=s["text"] if how != "exact" else "")
            if how in ("fuzzy", "rewritten") and not own(t):
                # the interviewer's passage keeps its words, which only he writes
                m["why"] = "interviewer"

        same = [s for s in statements if key(s["text"]) == key(r["statement"])]
        ats = r.get("ats") or ([] if r["at"] is None else [r["at"]])
        if ats:
            same.sort(key=lambda s: nearest(s["turn"], ats))
        free = [s for s in same if s["key"] not in taken]
        if free:
            place(free[0], "exact", "words")
        elif same:
            place(same[0], "duplicate", "words")
            m["of"] = taken[same[0]["key"]]
        else:
            at_loc = []
            for a in ats:
                close = [t for t in turns if t.get("seconds") is not None and near(t, a) <= SLACK]
                best = min((near(t, a) for t in close), default=None)
                at_loc += [t for t in close if near(t, a) == best and t not in at_loc]
            by_quote = [t for t in turns if r["quote"] and quote_in(r["quote"], t["text"])]
            found = None
            for by, passages in (("location", at_loc), ("quote", by_quote)):
                scored = sorted(((ratio(s["text"], r["statement"]), s) for s in statements if s["turn"] in passages),
                                key=lambda x: -x[0])
                if scored and scored[0][0] >= FUZZY:
                    found = (scored[0][1], "fuzzy", by, scored[0][0])
                    break
            if found is None:
                for by, passages in (("quote", by_quote), ("location", at_loc)):
                    scored = sorted(((ratio(s["text"], r["statement"]), s) for s in statements
                                     if s["turn"] in passages and own(s["turn"])), key=lambda x: -x[0])
                    if scored and scored[0][0] >= CLOSE:
                        found = (scored[0][1], "rewritten", by, scored[0][0])
                        break
            if found is not None:
                s, how, by, score = found
                if s["key"] in taken:
                    place(s, "duplicate", by, score)
                    m["of"] = taken[s["key"]]
                else:
                    place(s, how, by, score)
            else:
                passage = next((t for t in by_quote if own(t)), None)
                by = "quote" if passage else ""
                if passage is None:
                    passage = next((t for t in at_loc if own(t)), None)
                    by = "location" if passage else ""
                m.update(how="added" if add and passage else "skipped", by=by,
                         sheet=passage["sheet"] if passage else "", passage=passage["row"] if passage else None,
                         time=(passage.get("time") or "") if passage else "")
                if passage is None:
                    m["why"] = "nowhere"
                elif not quote_in(r["quote"], passage["text"]):
                    # a quote that is not the passage's own words goes with no quote, as a write refuses one
                    m["no_quote"] = True
        if m["how"] in ("exact", "fuzzy", "rewritten"):
            taken[m["key"]] = r["row"]
        out.append(m)
    return out


def counts(matched: list[dict]) -> dict:
    out = {k: 0 for k in ("rows", "exact", "fuzzy", "rewritten", "added", "skipped", "duplicate")}
    out["rows"] = len(matched)
    for m in matched:
        out[m["how"]] += 1
    out["unmatched"] = out["added"] + out["skipped"]
    out["reworded"] = sum(1 for m in matched if m["how"] in ("fuzzy", "rewritten") and m["why"] != "interviewer")
    return out


def passage_writes(matched: list[dict]) -> dict:
    """What each passage takes, by its sheet and row: `reword`, each statement's line to the table's words, and
    `add`, the new statements, each with its quote or "" for none."""
    out: dict = {}
    for m in matched:
        if m["how"] in ("fuzzy", "rewritten") and m["why"] != "interviewer":
            line = themes.split_card_key(m["key"])[2]
            out.setdefault((m["sheet"], m["passage"]), {"reword": {}, "add": []})["reword"][line] = m["statement"]
        elif m["how"] == "added":
            out.setdefault((m["sheet"], m["passage"]), {"reword": {}, "add": []})["add"].append(
                {"m": m, "quote": "" if m.get("no_quote") else m["quote"]})
    return out


def board_spec(matched: list[dict], note: str) -> tuple[dict, list[str]]:
    """The board the rows make, as `board new` takes one: the PETs in the table's order, each with its statements
    and then its sub-theme's, a label with nothing placed under it left out and named."""
    pets: list[dict] = []
    by_title: dict = {}
    for m in matched:
        if m["how"] not in ("exact", "fuzzy", "rewritten", "added") or not m["key"]:
            continue
        pet = by_title.get(m["pet"])
        if pet is None:
            pet = by_title[m["pet"]] = {"title": m["pet"], "members": [], "subs": [], "_subs": {}}
            pets.append(pet)
        if m["sub"]:
            sub = pet["_subs"].get(m["sub"])
            if sub is None:
                sub = pet["_subs"][m["sub"]] = {"title": m["sub"], "members": []}
                pet["subs"].append(sub)
            sub["members"].append(m["key"])
        else:
            pet["members"].append(m["key"])
    for pet in pets:
        pet.pop("_subs")
    titles = list(dict.fromkeys(m["pet"] for m in matched))
    left = [t for t in titles if t not in by_title]
    return {"pets": pets, "note": note}, left


# ------------------------------------------------------------------ a table of LPETs

def lpet_columns(heads: list[str], tps: list[dict]) -> tuple[int | None, dict]:
    """The LPET's column and each timepoint's, by its key, T2, or its label, a heading T2 or T2 - On the walk."""
    found: dict = {}
    for i, h in enumerate(heads):
        k = key(h)
        for t in tps:
            if t["case"] in found:
                continue
            names = {key(t["case"]), key(t.get("cite") or "")} - {""}
            if any(k == n or k.startswith(n + " ") for n in names):
                found[t["case"]] = i
                break
    taken = set(found.values())
    title = next((i for i, h in enumerate(heads) if key(h) in LPET_HEADS and i not in taken), None)
    if title is None:
        title = next((i for i in range(len(heads)) if i not in taken), None)
    return title, found


def lpet_rows(heads: list[str], rows: list[list], tps: list[dict], name: str) -> list[dict]:
    """Each row of a table of LPETs with a title: its title, its description, and each timepoint's cell by the
    timepoint's key, numbered as the sheet numbers it."""
    title, found = lpet_columns(heads, tps)
    if not found or title is None:
        raise TableError(i18n.t("cli.gets_import.no_columns", name=name, labels=", ".join(t["case"] for t in tps),
                                heads=", ".join(heads)))
    out = []
    for n, r in enumerate(rows, start=2):
        lines = cell(r[title] if title < len(r) else None).split("\n")
        head = themes_ai.clean_label(lines[0]) if lines and lines[0] else ""
        if not head:
            continue
        out.append({"row": n, "title": head, "description": " ".join(" ".join(lines[1:]).split()),
                    "cells": {tp: cell(r[i] if i < len(r) else None) for tp, i in found.items()}})
    if not out:
        raise TableError(i18n.t("cli.gets_import.no_rows", name=name))
    return out


def pets_at(data: dict, tp: str) -> list[dict]:
    """A timepoint's PETs as the LPETs file holds its copy: each top PET's card key, title and every statement under
    it at any depth, with its words and quotes."""
    held = (data.get("cases") or {}).get(tp) or {}
    groups = {g["id"]: g for g in held.get("pets") or []}
    lines = held.get("lines") or {}

    def under(gid: str, seen: frozenset) -> list[str]:
        g = groups.get(gid) or {}
        return list(g.get("statements") or []) + [k for s in g.get("subs") or [] if s not in seen
                                                  for k in under(s, seen | {s})]

    out = []
    for g in groups.values():
        if g.get("parent") is not None:
            continue
        said = []
        for k in under(g["id"], frozenset({g["id"]})):
            line = lines.get(k) or {}
            said.append({"key": k, "text": str(line.get("text") or ""),
                         "quotes": [str(q) for q in line.get("quotes") or [] if q]})
        out.append({"card": f"{tp}/{g['id']}", "title": str(g.get("title") or ""), "statements": said})
    return out


def cell_quotes(text: str) -> list[str]:
    return [q.strip() for q in CELL_QUOTE.findall(text) if len(q.split()) >= 2]


def propose(lrows: list[dict], pets: dict) -> list[dict]:
    """Each LPET with the PETs proposed for it, each with why: a quote of its cell that is a statement's quote or
    its words, or a line of the cell at a ratio of `FUZZY` or more to a statement or holding its words. A PET goes
    to the first LPET that proposes it, and a later one names it as proposed already."""
    given: dict[str, str] = {}
    out = []
    for r in lrows:
        members, also, empty = [], [], []
        for tp, text in r["cells"].items():
            hits = []
            quotes = cell_quotes(text)
            rest = [x for x in (CELL_QUOTE.sub(" ", line).strip(" -,.") for line in text.split("\n")) if len(x.split()) >= 3]
            for pet in pets.get(tp) or []:
                why = None
                for s in pet["statements"]:
                    for q in quotes:
                        if any(quote_in(q, x) or quote_in(x, q) for x in s["quotes"] + [s["text"]]):
                            why = {"by": "quote", "said": q}
                            break
                    if why is None:
                        for line in rest:
                            if ratio(line, s["text"]) >= FUZZY or (len(key(s["text"]).split()) >= 3
                                                                   and key(s["text"]) in key(line)):
                                why = {"by": "words", "said": line}
                                break
                    if why:
                        why.update(statement=s["text"], key=s["key"])
                        break
                if why:
                    hits.append(dict(why, card=pet["card"], pet=pet["title"], timepoint=tp))
            if not hits and text:
                empty.append(tp)
            for h in hits:
                if h["card"] in given:
                    also.append(dict(h, taken_by=given[h["card"]]))
                elif all(x["card"] != h["card"] for x in members):
                    given[h["card"]] = r["title"]
                    members.append(h)
        out.append(dict(r, members=members, also=also, unmatched=empty))
    return out


def note_of(r: dict, labels: dict) -> str:
    """An LPET's note: a paragraph for each timepoint whose cell has words, headed by its label, in order."""
    return "\n\n".join(f"{labels.get(tp, tp)}: {text}" for tp, text in r["cells"].items() if text)
