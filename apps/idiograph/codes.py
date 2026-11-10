#!/usr/bin/env python3
"""A thematic analysis project's code list (codes, 2 November 2026, Adam's ruling of 28 October, choice 1 (a), and
his choice of the drawings on 2 November: coding A, the code list as its own tab, the board's code cards).

A code is a label many coded extracts share, and each extract is still one quote. In the workbook nothing changes
in kind: a code on an extract is a passage's statement, the code's name, with the extract as its quote, so two codes
on one extract are two statements of the passage with the same quote, which the Coding screen shows as one extract
with two codes. Every reader that takes a statement with its quote (the exports, the theme table in Word, Search,
QDPX, the command line's turn lines) reads it as before. IPA projects never have a code list, and keep one quote per
statement.

The list is `idiograph-codes.json` at the project's root, beside the project file, only in a thematic analysis
project:

    {"schema": 1, "created": "...", "updated": "...",
     "codes": [{"id": "k1", "name": "The walk as a fixed route", "description": "..."}],
     "history": [{"when": "...", "changes": ["Routine renamed The daily round."], "tool": "", "note": ""}],
     "recent": ["k1"], "undo": {...}, "redo": {...}}

`recent` is the codes used last, the last one first, by id, for the Coding screen's quick keys (quickkeysB).

A code's name is its link to the rows: names are unique ignoring case and outer spaces (`norm`), so a row whose
statement reads "the walk as a fixed route " is that code. A name in the rows the list lacks, typed on the Codes
screen as New code, by an agent's turn write or by hand in Excel, joins the list with an empty description the next
time the list is read (`sync`). A code with no extracts stays in the list until it is deleted.

Rename and merge write every participant's workbook that holds the code, every board and the list as one change:
each file is checked first (a workbook open in Excel, the list changed since the page read it) and nothing is
written when one fails, a copy of each file goes into an `_Archive` folder first, and a failure halfway puts back
what was written. The change is one step of undo (`undo`), which puts the copies back only while no file has
changed since, else refuses whole.

A project made before the list (`ensure`): on its first read the list is built from its rows, rows of the same
name one code, every description empty, and each board keeps a revision first and then gathers each code's cards
in one place (see `gather`). Its History says how many codes it made and which codes it gathered.

On the GETs board of a thematic analysis project (the Themes board) a code is one card. The file keeps a card for
each row as before, so every reader of the board reads each extract under its theme: `gather` keeps all of a
code's row cards where its lead card is, in the same theme, at the same place and set aside with it, `fold` gives
the page the lead alone, and `unfold` lays a saved page's lead's rows back beside it.
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import shutil
from datetime import datetime
from pathlib import Path

import openpyxl

import i18n
import themes
import workbook as wb_mod
from workbook import WorkbookError

FILE = "idiograph-codes.json"
SCHEMA = 1
NAME_MAX = 200
DESCRIPTION_MAX = 2000
HISTORY_MAX = 200
ARCHIVE_LABEL = "pre-codes"
LIST_OPS = ("new", "rename", "describe", "merge", "delete")
EXTRACT_OPS = ("add", "remove")
# the codes used last, kept for the Coding screen's quick keys (quickkeysB, 9 November 2026)
RECENT_MAX = 5
QUICK_OPS = ("last", "in-vivo")
# the stop an in vivo code's name is trimmed of at its end, and the dots at its start
VIVO_STOPS = ".,;:!?\u2026"


class Stale(WorkbookError):
    """The list changed since the page or the agent read it, with nothing written."""


# ---------------------------------------------------------------------- names

def words(text) -> str:
    """A name as it is kept: its words with single spaces, no outer spaces."""
    return " ".join(str(text or "").split())


def norm(text) -> str:
    """A name as two names are compared: its words, any case."""
    return words(text).casefold()


def is_ta(method) -> bool:
    return str(method or "") == "ta"


def refuse_unless_ta(method) -> None:
    """Every op of the list in a thematic analysis project alone: an IPA project's statements each keep their own
    quote, and it has no code list."""
    if not is_ta(method):
        raise WorkbookError(i18n.t("codes.refused_ipa"))


# ---------------------------------------------------------------------- the file

def path_of(root: Path) -> Path:
    return Path(root) / FILE


def load(root: Path) -> dict | None:
    """The list as it sits on disk, None when there is none yet. One there that cannot be read is refused, so
    nothing is ever written over a file that can be recovered."""
    path = path_of(root)
    if not path.exists():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        raise WorkbookError(i18n.t("server.could_read_nothing_written", name=path.name))
    if not isinstance(data, dict):
        raise WorkbookError(i18n.t("codes.file_unreadable", name=path.name))
    return normal(data)


def normal(data: dict) -> dict:
    """The file's codes as the list reads them, anything it cannot read left out, and a second code of a name
    already there dropped."""
    codes, seen, ids = [], set(), set()
    for c in data.get("codes") if isinstance(data.get("codes"), list) else []:
        if not isinstance(c, dict):
            continue
        cid, name = str(c.get("id") or ""), words(c.get("name"))
        if not cid or not name or cid in ids or norm(name) in seen:
            continue
        ids.add(cid)
        seen.add(norm(name))
        codes.append({"id": cid, "name": name, "description": str(c.get("description") or "").strip()})
    history = [h for h in data.get("history") or [] if isinstance(h, dict)] if isinstance(data.get("history"), list) else []
    return dict(data, codes=codes, history=history)


def fresh(when: str) -> dict:
    return {"schema": SCHEMA, "created": when, "updated": when, "codes": [], "history": []}


def write(root: Path, data: dict) -> Path:
    """Written to a temporary file beside it and moved over the old one, as the GETs file is."""
    path = path_of(root)
    tmp = path.with_name(path.name + ".tmp")
    tmp.write_text(themes.render(data) + "\n", encoding="utf-8", newline="\n")
    os.replace(tmp, path)
    wb_mod.note_written(path)
    return path


def next_id(data: dict) -> str:
    taken = [int(c["id"][1:]) for c in data["codes"] if re.match(r"^k\d+$", c["id"])]
    return f"k{max(taken, default=0) + 1}"


def by_norm(data: dict) -> dict[str, dict]:
    return {norm(c["name"]): c for c in data["codes"]}


def find(data: dict, said) -> dict:
    """A code by its id, `k3`, or its name, any case."""
    text = words(said)
    for c in data["codes"]:
        if c["id"] == text:
            return c
    found = by_norm(data).get(norm(text))
    if found is None:
        raise WorkbookError(i18n.t("codes.not_a_code", name=text or "?"))
    return found


def version(data: dict | None, extracts: list[dict]) -> str:
    """The list's version as the page and an agent read it: its codes and where each extract stands, so a change
    from another window, an agent or a turn written since is seen."""
    held = {"codes": (data or {}).get("codes") or [],
            "extracts": sorted((x["case"], x["sheet"], x["row"], x["line"], x["code"]) for x in extracts)}
    return hashlib.sha1(json.dumps(held, sort_keys=True, ensure_ascii=False).encode("utf-8")).hexdigest()[:16]


# ---------------------------------------------------------------------- the rows

# each workbook's rows as `rows_of` read them, kept against its time and size, as the case list keeps its reads
ROWS: dict[str, tuple] = {}


def file_mark(path: Path):
    try:
        st = Path(path).stat()
    except OSError:
        return None
    return st.st_mtime_ns, st.st_size


def rows_of(book: Path, form: str | None = None) -> list[dict]:
    """Every passage of a workbook that holds a code or an extract: its sheet, row, time and its pairs by place,
    each a statement (the code's name) and its quote (the extract), as `workbook.pairs_of` reads them. Read
    only, and kept until the file changes."""
    book = Path(book)
    form = form or wb_mod.timecodes_for(book)
    key, mark = f"{book}|{form}", file_mark(book)
    held = ROWS.get(key)
    if mark is not None and held and held[0] == mark:
        return held[1]
    wb_mod.guard_lock(book)
    try:
        wb = openpyxl.load_workbook(book, read_only=True)
    except Exception as exc:  # noqa: BLE001
        raise WorkbookError(i18n.t("codes.workbook_unreadable", name=book.name)) from exc
    out = []
    try:
        for ws in wb.worksheets:
            cols = wb_mod.detect_columns(ws)
            if not {"name", "ts", "transcript"} <= set(cols) or "es" not in cols:
                continue
            width = max(cols.values())
            for number, values in enumerate(ws.iter_rows(min_row=2, max_col=width, values_only=True), start=2):
                cell = lambda role: values[cols[role] - 1] if role in cols and cols[role] <= len(values) else None  # noqa: E731
                es, kq = cell("es"), cell("kq")
                if es is None and kq is None:
                    continue
                pairs = wb_mod.pairs_of(es, kq)
                if not pairs:
                    continue
                seconds = wb_mod.ts_seconds(cell("ts"))
                out.append({"sheet": ws.title, "row": number, "seconds": seconds,
                            "time": wb_mod.timecode(seconds, form), "pairs": pairs})
    finally:
        wb.close()
    if mark is not None:
        ROWS[key] = (mark, out)
    return out


def who(case: str) -> str:
    return re.sub(r"^P\d+\s*-\s*", "", str(case or "")).strip() or str(case or "")


def case_order(case: str) -> list:
    return [int(t) if t.isdigit() else t.lower() for t in re.split(r"(\d+)", str(case or ""))]


def study_rows(books: list[dict]) -> list[dict]:
    """Each participant of the study with the rows of their workbook, in case order."""
    out = []
    for b in sorted(books, key=lambda b: case_order(b["case"])):
        out.append({"case": b["case"], "who": who(b["case"]), "workbook": Path(b["workbook"]),
                    "rows": rows_of(Path(b["workbook"]))})
    return out


def quote_words(text) -> str:
    """An extract as two are compared: its words with single spaces."""
    return " ".join(str(text or "").split())


def extracts_of(people: list[dict]) -> list[dict]:
    """Every code on an extract, one a statement of a passage: its participant, sheet, row and place among the
    passage's statements, `line`, the key a board's card names it by, its time, the extract and the code's name as
    the row spells it and as compared, `code`. A statement with no quote is a code on no extract, which the list
    counts as none."""
    out = []
    for p in people:
        for r in p["rows"]:
            for i, pair in enumerate(r["pairs"]):
                name, quote = words(pair.get("es")), quote_words(pair.get("kq"))
                if not name:
                    continue
                out.append({"case": p["case"], "who": p["who"], "workbook": str(p["workbook"]), "sheet": r["sheet"],
                            "row": r["row"], "line": i, "key": themes.card_key(r["sheet"], r["row"], i),
                            "time": r["time"], "seconds": r["seconds"], "quote": quote, "name": name,
                            "code": norm(name)})
    return out


def sync(data: dict, extracts: list[dict]) -> list[str]:
    """Each name the rows hold that the list lacks joins it, in the order the rows hold them, its description
    empty. The names added."""
    have = by_norm(data)
    added = []
    for x in extracts:
        if x["code"] in have:
            continue
        code = {"id": next_id(data), "name": x["name"], "description": ""}
        data["codes"].append(code)
        have[x["code"]] = code
        added.append(x["name"])
    return added


# ---------------------------------------------------------------------- the list as it is read

def listing(data: dict, people: list[dict], extracts: list[dict] | None = None) -> dict:
    """The list as the Code list screen draws it and an agent reads it: each code by name, any case, with its
    description, how many extracts and participants it has, and its extracts by participant in case order, each
    with its sheet, row, place and time, and the totals."""
    extracts = extracts_of(people) if extracts is None else extracts
    by_code: dict[str, list[dict]] = {}
    for x in extracts:
        by_code.setdefault(x["code"], []).append(x)
    codes = []
    for c in sorted(data["codes"], key=lambda c: (norm(c["name"]), c["id"])):
        mine = by_code.get(norm(c["name"]), [])
        by_case: dict[str, list[dict]] = {}
        for x in mine:
            by_case.setdefault(x["case"], []).append(x)
        by = [{"case": case, "who": who(case),
               "extracts": [{k: x[k] for k in ("sheet", "row", "line", "key", "time", "seconds", "quote", "workbook")}
                            for x in sorted(xs, key=lambda x: (x["seconds"] if x["seconds"] is not None else 1e12,
                                                               x["sheet"], x["row"], x["line"]))]}
              for case, xs in sorted(by_case.items(), key=lambda kv: case_order(kv[0]))]
        codes.append({"id": c["id"], "name": c["name"], "description": c["description"],
                      "extracts": len(mine), "participants": len(by), "by": by})
    places = {(x["case"], x["sheet"], x["row"], x["quote"]) for x in extracts if x["quote"]}
    return {"codes": codes, "total": {"codes": len(codes), "extracts": len(places),
                                      "participants": len({x["case"] for x in extracts})},
            "participants": [{"case": p["case"], "who": p["who"], "workbook": str(p["workbook"])} for p in people],
            "v": version(data, extracts), "updated": data.get("updated"),
            "history": list(data.get("history") or [])[-20:],
            "recent": [c["name"] for c in recent_of(data)],
            "undo": (data.get("undo") or {}).get("what") or "", "redo": (data.get("redo") or {}).get("what") or ""}


def code_of(view: dict, said) -> dict:
    """One code of a listing, by id or name."""
    text = words(said)
    for c in view["codes"]:
        if c["id"] == text or norm(c["name"]) == norm(text):
            return c
    raise WorkbookError(i18n.t("codes.not_a_code", name=text or "?"))


# ---------------------------------------------------------------------- the GETs board

def gets_mod():
    import gets
    return gets


def inside(data: dict, case: str) -> bool:
    """Whether a case is in the study, as the GETs file's `study` says, in when it says nothing."""
    held = (data.get("study") or {}).get(case)
    return not isinstance(held, dict) or held.get("in", True) is not False


def line_codes(data: dict) -> dict[str, str]:
    """Each statement card's key on the GETs board, `<case>/es/<line>`, with its code as compared, from the copies
    the GETs file holds of the cases in the study."""
    out = {}
    for case, rec in (data.get("cases") or {}).items():
        if not inside(data, case):
            continue
        for ident, line in ((rec or {}).get("lines") or {}).items():
            if isinstance(line, dict) and words(line.get("text")):
                out[f"{case}/es/{ident}"] = norm(line.get("text"))
    return out


def reading_key(key: str, card: dict):
    """A card's place in reading order on the canvas, row by row, then its key."""
    return (round(float(card.get("y", 0)) / themes.CARD_H), float(card.get("x", 0)), key_order(key))


def key_order(key: str):
    case, _, rest = str(key).partition("/es/")
    sheet, row, line = themes.split_card_key(rest)
    return (case_order(case), str(sheet), row if row is not None else 0, line if line is not None else 0)


def where_of(board: dict, key: str, parents: dict) -> tuple:
    """Where a card stands: the label holding it and whether it is set aside."""
    return (parents.get(key), key in set(board.get("discarded") or []))


def gather(board: dict, data: dict, leads: dict[str, str] | None = None, keep_out: set | None = None) -> list[str]:
    """Each code on a board one card's worth: every row of a code with a card on the board stands where its lead
    stands, in its label, set aside with it, at its place, and a row of a placed code with no card yet comes in
    there too, so a code's extracts follow it. `leads` names a code's lead by its code, the card the page moved;
    without one the lead is where most of the code's cards stood, a tie the first in reading order. A code in
    `keep_out` has every card taken off. The board is changed in place, and the answer is the names of the codes
    whose cards stood in more than one place."""
    codes = line_codes(data)
    cards = board.setdefault("cards", {})
    groups = [g for g in board.get("groups") or [] if isinstance(g, dict)]
    parents = themes.parents_of(groups)
    names = {}
    for case, rec in (data.get("cases") or {}).items():
        for ident, line in ((rec or {}).get("lines") or {}).items():
            if isinstance(line, dict) and words(line.get("text")):
                names.setdefault(norm(line.get("text")), words(line.get("text")))
    on: dict[str, list[str]] = {}
    for key in cards:
        code = codes.get(key)
        if code:
            on.setdefault(code, []).append(key)
    every: dict[str, list[str]] = {}
    for key, code in codes.items():
        every.setdefault(code, []).append(key)
    discarded = list(board.get("discarded") or [])
    gathered = []
    for code in sorted(set(on) | set(keep_out or ())):
        keys = on.get(code) or []
        if keep_out and code in keep_out:
            for key in keys:
                cards.pop(key, None)
            continue
        lead = (leads or {}).get(code)
        if lead not in keys:
            places: dict[tuple, list[str]] = {}
            for key in keys:
                places.setdefault(where_of(board, key, parents), []).append(key)
            first = lambda ks: min(ks, key=lambda k: reading_key(k, cards[k]))  # noqa: E731
            best = max(places.values(), key=lambda ks: (len(ks), [-x for x in reading_key(first(ks), cards[first(ks)])[:2]]))
            lead = first(best)
            if len(places) > 1:
                gathered.append(names.get(code) or code)
        group, aside = where_of(board, lead, parents)
        spot = {"x": cards[lead].get("x", 0), "y": cards[lead].get("y", 0)}
        rows = sorted(every.get(code) or [], key=key_order)
        for key in rows:
            if key == lead:
                continue
            card = cards.get(key)
            if card is None:
                card = cards[key] = {"x": 0, "y": 0, "text": (cards[lead].get("text") or "")}
            card.update(spot)
            # out of any other label, into the lead's just after it
            for g in groups:
                members = g.get("members") or []
                if key in members and g.get("id") != group:
                    g["members"] = [m for m in members if m != key]
            if group is not None:
                g = next(g for g in groups if g.get("id") == group)
                members = [m for m in g.get("members") or [] if m != key]
                at = members.index(lead) + 1 if lead in members else len(members)
                members.insert(at, key)
                g["members"] = members
            if aside and key not in discarded:
                discarded.append(key)
            elif not aside and key in discarded:
                discarded.remove(key)
    board["discarded"] = [k for k in discarded if k in cards]
    for g in groups:
        g["members"] = [m for m in g.get("members") or [] if m in cards or any(x.get("id") == m for x in groups)]
    return gathered


def place_of(board: dict, key: str, parents: dict) -> tuple:
    """Where a card stands, its label, whether it is set aside, and its place on the canvas."""
    card = (board.get("cards") or {}).get(key) or {}
    return where_of(board, key, parents) + (round(float(card.get("x", 0))), round(float(card.get("y", 0))))


def follow_moved(before: dict, after: dict, data: dict) -> dict:
    """An agent's change to a board (`gets apply`, MCP's the same) in a thematic analysis project: a card of a code it
    moved, set aside or brought in leads, and the code's other cards follow it, so the file never holds a code in two
    places. Two cards of one code moved to different places is refused with nothing written. A code whose every card
    the change took off stays off. The board after is changed in place and answered."""
    codes = line_codes(data)
    was = themes.parents_of(before.get("groups") or [])
    now = themes.parents_of(after.get("groups") or [])
    # a card put in another label, set aside or back, or brought in, moved, and one only shifted on the canvas, as
    # a settle shifts what stands near a drop, leads only where no card of its code moved
    moved: dict[str, list[str]] = {}
    shifted: dict[str, list[str]] = {}
    for key in after.get("cards") or {}:
        code = codes.get(key)
        if not code:
            continue
        if key not in (before.get("cards") or {}) or where_of(before, key, was) != where_of(after, key, now):
            moved.setdefault(code, []).append(key)
        elif place_of(before, key, was) != place_of(after, key, now):
            shifted.setdefault(code, []).append(key)
    def far(k):
        a, b = before["cards"][k], after["cards"][k]
        return -(abs(float(a.get("x", 0)) - float(b.get("x", 0))) + abs(float(a.get("y", 0)) - float(b.get("y", 0))))

    leads = {code: min(keys, key=lambda k: (far(k), key_order(k))) for code, keys in shifted.items()}
    for code, keys in moved.items():
        if len({where_of(after, k, now) for k in keys}) > 1:
            raise WorkbookError(i18n.t("codes.split_refused", name=words(next(
                (line.get("text") for rec in (data.get("cases") or {}).values()
                 for line in (rec.get("lines") or {}).values() if isinstance(line, dict) and norm(line.get("text")) == code),
                code))))
        leads[code] = min(keys, key=key_order)
    held = {codes[k] for k in after.get("cards") or {} if codes.get(k)}
    gone = {codes[k] for k in before.get("cards") or {} if codes.get(k)} - held
    gather(after, data, leads, keep_out=gone)
    return after


def lead_of(keys: list[str], cards: dict) -> str:
    return min(keys, key=key_order)


def fold(board: dict, data: dict, extracts: dict | None = None) -> tuple[dict, dict]:
    """The board as the page draws it in a thematic analysis project: each code's lead card alone, the first of
    its rows, and each lead's code, its name, how many extracts it has and how many are each participant's, from
    the GETs file's copies of the cases. The board given is left as it is."""
    out = json.loads(json.dumps(board))
    codes = line_codes(data)
    cards = out.get("cards") or {}
    on: dict[str, list[str]] = {}
    for key in cards:
        if codes.get(key):
            on.setdefault(codes[key], []).append(key)
    every: dict[str, list[str]] = {}
    names: dict[str, str] = {}
    for case, rec in (data.get("cases") or {}).items():
        for ident, line in ((rec or {}).get("lines") or {}).items():
            if isinstance(line, dict) and words(line.get("text")):
                every.setdefault(norm(line["text"]), []).append(case)
                names.setdefault(norm(line["text"]), words(line["text"]))
    drop = set()
    shown = {}
    for code, keys in on.items():
        lead = lead_of(keys, cards)
        drop |= set(keys) - {lead}
        by: dict[str, int] = {}
        for case in every.get(code) or []:
            by[case] = by.get(case, 0) + 1
        shown[lead] = {"code": code, "name": (extracts or {}).get(code, {}).get("name") or names.get(code) or code,
                       "n": len(every.get(code) or []),
                       "by": [[case, n] for case, n in sorted(by.items(), key=lambda kv: case_order(kv[0]))]}
    if drop:
        out["cards"] = {k: c for k, c in cards.items() if k not in drop}
        for g in out.get("groups") or []:
            g["members"] = [m for m in g.get("members") or [] if m not in drop]
        out["discarded"] = [k for k in out.get("discarded") or [] if k not in drop]
        out["stacks"] = {t: [k for k in ks if k not in drop] for t, ks in (out.get("stacks") or {}).items() if t not in drop}
    return out, shown


def unfold(kept: dict, data: dict, was: dict | None) -> dict:
    """A board the page saved, which holds each code's lead alone, with each code's rows laid back beside its
    lead (see `gather`). A code with two cards sent, one the page just brought in from the Participants panel, takes
    that one's place. A code the page sent no card of has every card taken off the board."""
    codes = line_codes(data)
    held = set((was or {}).get("cards") or {})
    sent: dict[str, list[str]] = {}
    for key in kept.get("cards") or {}:
        if codes.get(key):
            sent.setdefault(codes[key], []).append(key)
    leads = {}
    for code, keys in sent.items():
        new = [k for k in keys if k not in held]
        leads[code] = lead_of(new or keys, kept["cards"])
        for k in keys:
            if k != leads[code]:
                kept["cards"].pop(k, None)
    gone = {codes[k] for k in held if codes.get(k)} - set(sent)
    gather(kept, data, leads, keep_out=gone)
    return kept


# ---------------------------------------------------------------------- changes to the rows

def plan_rows(people: list[dict], change) -> dict:
    """What a change does to each workbook's rows: `change(pairs)` gives a passage's pairs after, each pair
    carrying `src`, its place before, or None for a pair new to the passage. The passages changed by workbook,
    each with its pairs before and after and `moved`, each statement's place before and its place after or None."""
    out: dict[str, dict] = {}
    for p in people:
        for r in p["rows"]:
            before = [dict(x, src=i) for i, x in enumerate(r["pairs"])]
            after = change(p, r, [dict(x) for x in before])
            if [(x["es"], x["kq"]) for x in after] == [(x["es"], x["kq"]) for x in before]:
                continue
            kept = [x for x in after if words(x.get("es"))]
            moved = {}
            for i, x in enumerate(before):
                if not words(x.get("es")):
                    continue
                to = next((j for j, y in enumerate(kept) if y.get("src") == i), None)
                moved[i] = to
            book = out.setdefault(str(p["workbook"]), {"case": p["case"], "workbook": p["workbook"], "rows": []})
            book["rows"].append({"sheet": r["sheet"], "row": r["row"], "before": r["pairs"],
                                 "after": [{"es": words(x.get("es")), "kq": x.get("kq") or ""} for x in after],
                                 "moved": moved})
    return out


def sha_of(path: Path) -> str | None:
    try:
        return hashlib.sha1(Path(path).read_bytes()).hexdigest()
    except OSError:
        return None


def rel(root: Path, path: Path) -> str:
    try:
        return Path(path).resolve().relative_to(Path(root).resolve()).as_posix()
    except ValueError:
        return Path(path).as_posix()


def absolute(root: Path, said: str) -> Path:
    p = Path(said)
    return p if p.is_absolute() else Path(root) / p


def root_archive(root: Path, path: Path, label: str) -> Path:
    """A copy of a file at the project's root in the root's `_Archive`, `<stem> (<label> <date-time>)<suffix>`,
    as `workbook.archive_copy` keeps a workbook's."""
    archive = Path(root) / "_Archive"
    archive.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d-%H%M")
    backup = archive / f"{path.stem} ({label} {stamp}){path.suffix}"
    n = 2
    while backup.exists():
        backup = archive / f"{path.stem} ({label} {stamp}-{n}){path.suffix}"
        n += 1
    shutil.copy2(path, backup)
    return backup


def keep_copy(root: Path, path: Path, label: str = ARCHIVE_LABEL) -> Path:
    if Path(path).suffix.lower() == ".xlsx":
        return wb_mod.archive_copy(path, label)
    return root_archive(root, Path(path), label)


def write_rows(book: Path, rows: list[dict]) -> None:
    """A workbook's passages written from their pairs, as `save_turn` writes a passage's, in one save."""
    wb_mod.guard_lock(book)
    wb = openpyxl.load_workbook(book, rich_text=True)
    try:
        for r in rows:
            ws = wb[r["sheet"]]
            cols = wb_mod.detect_columns(ws)
            es, kq = wb_mod.pairs_to_cells(r["after"])
            ws.cell(r["row"], cols["es"]).value = es
            if "kq" in cols:
                ws.cell(r["row"], cols["kq"]).value = kq
            elif kq:
                raise WorkbookError(i18n.t("codes.no_quote_column", name=Path(book).name, sheet=r["sheet"]))
        wb_mod._atomic_save(wb, Path(book))
    finally:
        wb.close()


def rekey_board(board: dict, case: str, rows: list[dict]) -> None:
    """A board's statement cards of a case moved with their statements' places after a change (see `plan_rows`): a
    card whose statement is gone comes off, the rest take their new key."""
    mapping: dict[str, str | None] = {}
    for r in rows:
        for i, to in r["moved"].items():
            old = f"{case}/es/{themes.card_key(r['sheet'], r['row'], i)}"
            mapping[old] = None if to is None else f"{case}/es/{themes.card_key(r['sheet'], r['row'], to)}"
    if not mapping:
        return
    cards = board.get("cards") or {}
    out = {}
    for key, card in cards.items():
        to = mapping.get(key, key)
        if to is not None and to not in out:
            out[to] = card
    board["cards"] = out
    for g in board.get("groups") or []:
        seen, members = set(), []
        for m in g.get("members") or []:
            to = mapping.get(m, m)
            if to is not None and to not in seen:
                seen.add(to)
                members.append(to)
        g["members"] = members
    board["discarded"] = list(dict.fromkeys(mapping.get(k, k) for k in board.get("discarded") or [] if mapping.get(k, k)))
    if isinstance(board.get("stacks"), dict):
        board["stacks"] = {mapping.get(t, t): [mapping.get(k, k) for k in ks if mapping.get(k, k)]
                           for t, ks in board["stacks"].items() if mapping.get(t, t)}


def follow_gets(root: Path, plan: dict, books: list[dict], revision: str, when: str) -> dict | None:
    """The GETs file after a change to the rows: each board kept as it stood in its History first, under
    `revision`, its cards moved with their statements, each participant's copy read again from their workbook,
    and each code's cards gathered in one place. The file in memory, None when the project has none."""
    gets = gets_mod()
    data = gets.load(root)
    if data is None:
        return None
    for board in themes.boards_of(data):
        themes.add_revision(board, name=revision, at=when)
        for item in plan.values():
            rekey_board(board, item["case"], item["rows"])
    by_book = {str(Path(b["workbook"])): b for b in books}
    for item in plan.values():
        b = by_book.get(str(Path(item["workbook"])))
        if b is None or b["case"] not in (data.get("cases") or {}):
            continue
        snap = gets.fresh_of({"workbook": Path(item["workbook"])})
        data["cases"][b["case"]] = gets.record(snap, Path(item["workbook"]), when)
    for board in themes.boards_of(data):
        gather(board, data)
        board["updated"] = when
    return data


# ---------------------------------------------------------------------- the list's own changes

def checked_name(data: dict, name, but: str | None = None) -> str:
    name = words(name)
    if not name:
        raise WorkbookError(i18n.t("codes.needs_name"))
    if len(name) > NAME_MAX:
        raise WorkbookError(i18n.t("codes.name_long", most=NAME_MAX))
    other = by_norm(data).get(norm(name))
    if other is not None and other["id"] != but:
        raise WorkbookError(i18n.t("codes.name_taken", name=other["name"]))
    return name


def apply(data: dict, people: list[dict], ops) -> tuple[list[str], list]:
    """Each operation run on the list in `data` in order, in place, and what each does to the rows, refused as a
    whole when one is wrong, `data` then to be thrown away:

    - `new`, `name`, and `description`
    - `rename`, `code` by its id or name, `name`, its new name, which every row of it takes
    - `describe`, `code`, `description`, an empty one clearing it
    - `merge`, `code`, `into`, another code: every extract of the one goes to the other, an extract that had both
      keeping one, its description added to the other's, and the one leaves the list
    - `delete`, `code`, a code with no extracts

    Answers a line for each change and the changes to the rows, each a function of a passage's pairs."""
    if not isinstance(ops, list) or not ops:
        raise WorkbookError(i18n.t("codes.ops_list"))
    extracts = extracts_of(people)
    counts: dict[str, int] = {}
    for x in extracts:
        counts[x["code"]] = counts.get(x["code"], 0) + 1
    said, changes = [], []
    for n, op in enumerate(ops, start=1):
        kind = str((op or {}).get("op") or "").strip().lower() if isinstance(op, dict) else ""
        if kind not in LIST_OPS:
            raise WorkbookError(i18n.t("codes.not_an_op", n=n, op=kind or "?"))
        if kind == "new":
            name = checked_name(data, op.get("name"))
            text = str(op.get("description") or "").strip()
            if len(text) > DESCRIPTION_MAX:
                raise WorkbookError(i18n.t("codes.description_long", most=DESCRIPTION_MAX))
            data["codes"].append({"id": next_id(data), "name": name, "description": text})
            said.append(i18n.t("codes.said.new", name=name))
            continue
        code = find(data, op.get("code"))
        if kind == "rename":
            old = code["name"]
            name = checked_name(data, op.get("name"), but=code["id"])
            if name == old:
                continue
            code["name"] = name
            gone = norm(old)
            changes.append(lambda p, r, pairs, gone=gone, name=name: [
                dict(x, es=name) if norm(x.get("es")) == gone else x for x in pairs])
            counts[norm(name)] = counts.pop(gone, 0) + (counts.get(norm(name), 0) if norm(name) != gone else 0)
            said.append(i18n.t("codes.said.renamed", old=old, new=name))
        elif kind == "describe":
            text = str(op.get("description") or "").strip()
            if len(text) > DESCRIPTION_MAX:
                raise WorkbookError(i18n.t("codes.description_long", most=DESCRIPTION_MAX))
            if text != code["description"]:
                code["description"] = text
                said.append(i18n.t("codes.said.described", name=code["name"]) if text
                            else i18n.t("codes.said.description_cleared", name=code["name"]))
        elif kind == "merge":
            into = find(data, op.get("into"))
            if into["id"] == code["id"]:
                raise WorkbookError(i18n.t("codes.merge_itself", name=code["name"]))
            gone, to = norm(code["name"]), norm(into["name"])

            def merged(p, r, pairs, gone=gone, to=to, name=into["name"]):
                out, seen = [], set()
                for x in pairs:
                    if norm(x.get("es")) == to:
                        seen.add(quote_words(x.get("kq")))
                for x in pairs:
                    if norm(x.get("es")) == gone:
                        q = quote_words(x.get("kq"))
                        if q in seen:
                            continue
                        seen.add(q)
                        x = dict(x, es=name)
                    out.append(x)
                return out

            changes.append(merged)
            if code["description"]:
                into["description"] = (into["description"] + "\n\n" + code["description"]).strip() \
                    if code["description"] not in into["description"] else into["description"]
            data["codes"] = [c for c in data["codes"] if c["id"] != code["id"]]
            # the codes used last keep the one merged as the code that keeps its extracts
            data["recent"] = [into["id"] if x == code["id"] else x for x in data.get("recent") or []]
            counts[to] = counts.get(to, 0) + counts.pop(gone, 0)
            said.append(i18n.t("codes.said.merged", old=code["name"], new=into["name"]))
        else:
            if counts.get(norm(code["name"]), 0):
                raise WorkbookError(i18n.t("codes.delete_has_extracts", name=code["name"],
                       n=i18n.t("codes.n.extracts", n=counts[norm(code["name"])])))
            data["codes"] = [c for c in data["codes"] if c["id"] != code["id"]]
            said.append(i18n.t("codes.said.deleted", name=code["name"]))
    return said, changes


def named_in(data: dict, ops) -> dict:
    """The codes the first operation names, by their names as the list held them before it, for a line that says
    what waits for his yes."""
    first = ops[0] if isinstance(ops, list) and ops and isinstance(ops[0], dict) else {}
    out = {}
    for key in ("code", "into"):
        if first.get(key):
            try:
                out[key] = find(data, first[key])["name"]
            except WorkbookError:
                pass
    return out


def chained(changes: list):
    def run(p, r, pairs):
        for fn in changes:
            pairs = fn(p, r, pairs)
        return pairs
    return run


def record(data: dict, said: list[str], when: str, note: str = "", tool: str = "") -> None:
    data["updated"] = when
    data["history"] = (data.get("history") or []) + [
        dict({"when": when, "changes": said}, **({"note": note} if note else {}), **({"tool": tool} if tool else {}))]
    data["history"] = data["history"][-HISTORY_MAX:]


def checked_first(root: Path, files: list[Path]) -> None:
    """Every file a change writes checked before any is written: a workbook open in Excel, a file that cannot
    be written."""
    for f in files:
        f = Path(f)
        if f.suffix.lower() == ".xlsx":
            wb_mod.guard_lock(f)
        if f.exists() and not os.access(f, os.W_OK):
            raise WorkbookError(i18n.t("codes.cannot_write", name=f.name))


def land(root: Path, plan: dict, books: list[dict], codes_after: dict, before_codes: list, what: str,
         when: str) -> dict:
    """A change written whole, or not at all: a copy of every file it writes kept first, each workbook written
    with its passages, then the GETs file following them (`follow_gets`) and the list, and on a failure every
    file written put back from its copy. The list keeps the change as its step of undo, each file with its copy
    and how it reads after."""
    gets = gets_mod()
    gets_file = gets.gets_path(root)
    files = [Path(item["workbook"]) for item in plan.values()]
    files += [gets_file] if plan and gets_file.exists() else []
    checked_first(root, files + [path_of(root)])
    copies = [(f, keep_copy(root, f)) for f in files]
    written = []
    try:
        for item in plan.values():
            write_rows(Path(item["workbook"]), item["rows"])
            written.append(Path(item["workbook"]))
        if gets_file in files:
            revision = themes.revision_name("codes_changed", what=what)
            gets_after = follow_gets(root, plan, books, revision, when)
            if gets_after is not None:
                gets.write(root, gets._file(gets_after, when))
                written.append(gets_file)
    except Exception:
        for f, copy in copies:
            if f in written:
                shutil.copy2(copy, f)
                wb_mod.note_written(f)
        raise
    codes_after["undo"] = {"what": what, "at": when,
                           "files": [{"path": rel(root, f), "copy": rel(root, c), "after": sha_of(f)} for f, c in copies],
                           "codes": before_codes}
    codes_after.pop("redo", None)
    write(root, codes_after)
    return {"files": [rel(root, f) for f in files], "copies": [rel(root, c) for _, c in copies]}


def change(root: Path, books: list[dict], ops, when: str, dry_run: bool = False, note: str = "", tool: str = "",
           seen: str | None = None) -> dict:
    """The operations applied to the list and to every row they reach, written whole unless `dry_run` or nothing
    changed, the History naming each change. `seen` is the list's version the page or the agent read, and a change
    over a list changed since is refused with nothing written. Answers `changes`, a line each, `dry_run`, the
    files it writes or would write, and the list after."""
    data = ensure(root, books, when, tool)
    people = study_rows(books)
    now_v = version(data, extracts_of(people))
    if seen and str(seen) != now_v:
        raise Stale(i18n.t("codes.stale"))
    after = json.loads(json.dumps(data))
    said, changes = apply(after, people, ops)
    plan = plan_rows(people, chained(changes)) if changes else {}
    files = [rel(root, Path(item["workbook"])) for item in plan.values()]
    gets = gets_mod()
    if plan and gets.gets_path(root).exists():
        files.append(rel(root, gets.gets_path(root)))
    if said:
        files.append(rel(root, path_of(root)))
    rows = sum(len(item["rows"]) for item in plan.values())
    out = {"changes": said, "dry_run": bool(dry_run), "files": files, "rows": rows,
           "participants": sorted({item["case"] for item in plan.values()}, key=case_order),
           "named": named_in(data, ops)}
    if dry_run or not said:
        if plan:
            checked_first(root, [Path(item["workbook"]) for item in plan.values()])
        out["list"] = listing(after if dry_run else data, people)
        return out
    what = said[0] if len(said) == 1 else i18n.t("codes.said.several", n=len(said))
    record(after, said, when, note, tool)
    land(root, plan, books, after, data["codes"], what, when)
    out["list"] = listing(after, study_rows(books))
    return out


# ---------------------------------------------------------------------- an extract's codes

def passage(people: list[dict], case: str, sheet: str, row: int) -> tuple[dict, dict]:
    for p in people:
        if p["case"] == case or p["who"].lower() == str(case).lower():
            for r in p["rows"]:
                if r["sheet"] == sheet and r["row"] == int(row):
                    return p, r
            return p, {"sheet": sheet, "row": int(row), "pairs": []}
    raise WorkbookError(i18n.t("codes.not_a_participant", name=case))


def extract_change(root: Path, books: list[dict], op: str, case: str, sheet: str, row, quote, code, when: str,
                   dry_run: bool = False, note: str = "", tool: str = "") -> dict:
    """A code put on an extract of a passage, or taken off it, as the Coding screen's Add a code and a chip's x
    do: `add` a code of the list or a new name, which joins the list, `remove` the code, the extract kept with no
    code when it was its last. The extract is one the passage holds already, by its words. Answers the passage's
    pairs after and the line said."""
    op = str(op or "").lower()
    if op not in EXTRACT_OPS:
        raise WorkbookError(i18n.t("codes.not_an_op", n=1, op=op or "?"))
    data = ensure(root, books, when, tool)
    people = study_rows(books)
    p, r = passage(people, case, sheet, int(row))
    q = quote_words(quote)
    pairs = [dict(x) for x in r["pairs"]]
    here = [i for i, x in enumerate(pairs) if quote_words(x.get("kq")) == q]
    if not q or not here:
        raise WorkbookError(i18n.t("codes.not_an_extract", quote=q or "?"))
    name = words(code)
    if not name:
        raise WorkbookError(i18n.t("codes.needs_name"))
    known = by_norm(data).get(norm(name))
    if op == "add":
        name = known["name"] if known else checked_name(data, name)
        if any(norm(pairs[i].get("es")) == norm(name) for i in here):
            raise WorkbookError(i18n.t("codes.has_it", name=name))
        loose = next((i for i in here if not words(pairs[i].get("es"))), None)
        if loose is not None:
            pairs[loose]["es"] = name
        else:
            pairs.append({"es": name, "kq": pairs[here[0]]["kq"]})
        said = i18n.t("codes.said.put_on", name=name, who=p["who"], time=r.get("time") or "")
    else:
        at = next((i for i in here if norm(pairs[i].get("es")) == norm(name)), None)
        if at is None:
            raise WorkbookError(i18n.t("codes.has_not", name=name))
        others = [i for i in here if i != at and words(pairs[i].get("es"))]
        if others:
            pairs.pop(at)
        else:
            pairs[at]["es"] = ""
        said = i18n.t("codes.said.taken_off", name=(known or {}).get("name") or name, who=p["who"],
                      time=r.get("time") or "")
    book = Path(p["workbook"])
    out = {"changes": [said], "dry_run": bool(dry_run), "case": p["case"], "sheet": sheet, "row": int(row),
           "pairs": pairs, "workbook": str(book)}
    if dry_run:
        wb_mod.guard_lock(book)
        return out
    result = wb_mod.save_turn(book, sheet, int(row), None, None, None, pairs=pairs)
    out["pairs"] = result["pairs"]
    after = load(root) or data
    added = sync(after, extracts_of(study_rows(books)))
    if op == "add":
        used(after, [name])
    record(after, [i18n.t("codes.said.new", name=x) for x in added] + [said], when, note, tool)
    write(root, after)
    return out


# ---------------------------------------------------------------------- the codes used last and the quick keys

def recent_of(data: dict) -> list[dict]:
    """The codes used last, the last one first, up to RECENT_MAX, kept in the list by id so a rename follows them,
    a code no longer on the list left out."""
    have = {c["id"]: c for c in data.get("codes") or []}
    out = []
    for cid in data.get("recent") or []:
        c = have.get(str(cid))
        if c is not None and c not in out:
            out.append(c)
    return out[:RECENT_MAX]


def used(data: dict, names) -> bool:
    """Each of `names`, in the order they were put on an extract, made the code used last, in place. Answers
    whether the codes used last changed."""
    have = by_norm(data)
    ids = [c["id"] for c in recent_of(data)]
    for name in names:
        c = have.get(norm(name))
        if c is not None:
            ids = [c["id"]] + [x for x in ids if x != c["id"]]
    ids = ids[:RECENT_MAX]
    if ids == list(data.get("recent") or []):
        return False
    data["recent"] = ids
    return True


def put_on(before, after) -> list[str]:
    """The codes a passage's save put on an extract, its statements before and after, each a code's name: every
    name the passage holds more often after than before, in the order they stand, the last put on standing last."""
    had: dict[str, int] = {}
    for name in before or []:
        if words(name):
            had[norm(name)] = had.get(norm(name), 0) + 1
    out = []
    for name in after or []:
        if not words(name):
            continue
        if had.get(norm(name), 0):
            had[norm(name)] -= 1
        else:
            out.append(words(name))
    return out


def note_used(root: Path, names, when: str) -> list[str]:
    """After a passage is saved, the codes it put on an extract made the codes used last, the list written only
    when they changed, with no line in its History. Answers the codes used last by name."""
    data = load(root)
    if data is None:
        return []
    if names and used(data, names):
        write(root, data)
    return [c["name"] for c in recent_of(data)]


def vivo_name(quote) -> str:
    """An in vivo code's name: the extract's words, the inverted commas round them set aside, trimmed of the stop
    at their end and of any dots at their start."""
    name = words(themes.quote_words(quote))
    return words(name.rstrip(" " + VIVO_STOPS).lstrip(" .\u2026"))


def passage_text(book: Path, sheet: str, row: int) -> tuple[str, str, str]:
    """A passage's words, its speaker and its time, as the workbook holds them."""
    wb_mod.guard_lock(book)
    try:
        wb = openpyxl.load_workbook(book, rich_text=True)
    except Exception as exc:  # noqa: BLE001
        raise WorkbookError(i18n.t("codes.workbook_unreadable", name=Path(book).name)) from exc
    try:
        if sheet not in wb.sheetnames:
            raise WorkbookError(i18n.t("codes.not_a_passage", sheet=sheet, row=row))
        ws = wb[sheet]
        cols = wb_mod.detect_columns(ws)
        if not {"name", "transcript"} <= set(cols) or "es" not in cols or "kq" not in cols:
            raise WorkbookError(i18n.t("codes.no_quote_column", name=Path(book).name, sheet=sheet))
        if int(row) < 2 or int(row) > ws.max_row:
            raise WorkbookError(i18n.t("codes.not_a_passage", sheet=sheet, row=row))
        seconds = wb_mod.ts_seconds(ws.cell(int(row), cols["ts"]).value) if "ts" in cols else None
        return (wb_mod._text_at(ws, cols, int(row)), str(ws.cell(int(row), cols["name"]).value or "").strip(),
                wb_mod.timecode(seconds, wb_mod.timecodes_for(book)))
    finally:
        wb.close()


def quick(root: Path, books: list[dict], how: str, case: str, sheet: str, row, words_given, when: str, n=1,
          dry_run: bool = False, note: str = "", tool: str = "") -> dict:
    """The Coding screen's quick keys as one op: the words, `words_given`, which the passage holds, become a new
    extract of it with a code at once. `how` is `last`, the code used last, or with `n` of 2 to 5 that one of the
    codes used last (R, and 1 to 5), or `in-vivo`, a code whose name is the words themselves, trimmed of the stop
    at their end, which joins the list unless a code of that name is on it already (V). Words the passage holds as
    an extract already take the code on that extract. Answers the passage's pairs after, the code, the line said
    and the codes used last."""
    how = str(how or "").lower()
    if how not in QUICK_OPS:
        raise WorkbookError(i18n.t("codes.not_a_quick_op", op=how or "?"))
    data = ensure(root, books, when, tool)
    people = study_rows(books)
    p, r = passage(people, case, sheet, int(row))
    q = words(themes.quote_words(" ".join(str(words_given or "").split())))
    if not q:
        raise WorkbookError(i18n.t("codes.quick_no_words"))
    quote = themes.quoted(q)
    book = Path(p["workbook"])
    text, speaker, time = passage_text(book, sheet, int(row))
    interviewer = wb_mod.interviewer_name()
    if interviewer and speaker.casefold() == interviewer.strip().casefold():
        raise WorkbookError(i18n.t("codes.quick_interviewer"))
    if not wb_mod.quote_reach(quote, [text]):
        raise WorkbookError(i18n.t("codes.quick_not_there", quote=q))
    if how == "last":
        recent = recent_of(data)
        try:
            at = int(n or 1)
        except (TypeError, ValueError):
            at = 0
        if not 1 <= at <= RECENT_MAX:
            raise WorkbookError(i18n.t("codes.quick_place", most=RECENT_MAX))
        if not recent:
            raise WorkbookError(i18n.t("codes.quick_none_used"))
        if at > len(recent):
            raise WorkbookError(i18n.t("codes.quick_fewer", codes=i18n.t("codes.n.codes", n=len(recent))))
        name = recent[at - 1]["name"]
    else:
        name = vivo_name(q)
        known = by_norm(data).get(norm(name))
        name = known["name"] if known else checked_name(data, name)
    pairs = [dict(x) for x in r["pairs"]]
    here = [i for i, x in enumerate(pairs) if words(themes.quote_words(x.get("kq"))) == q]
    if any(norm(pairs[i].get("es")) == norm(name) for i in here):
        raise WorkbookError(i18n.t("codes.has_it", name=name))
    loose = next((i for i in here if not words(pairs[i].get("es"))), None)
    if loose is not None:
        pairs[loose]["es"] = name
    elif here:
        pairs.append({"es": name, "kq": pairs[here[0]]["kq"]})
    else:
        pairs.append({"es": name, "kq": quote})
    new = by_norm(data).get(norm(name)) is None
    said = ([i18n.t("codes.said.new", name=name)] if new else []) + [
        i18n.t("codes.said.put_on", name=name, who=p["who"], time=r.get("time") or time)]
    out = {"changes": said, "dry_run": bool(dry_run), "case": p["case"], "sheet": sheet, "row": int(row),
           "code": name, "extract": quote, "pairs": pairs, "workbook": str(book)}
    if dry_run:
        wb_mod.guard_lock(book)
        out["recent"] = [c["name"] for c in recent_of(data)]
        return out
    result = wb_mod.save_turn(book, sheet, int(row), None, None, None, pairs=pairs)
    out["pairs"] = result["pairs"]
    after = load(root) or data
    sync(after, extracts_of(study_rows(books)))
    used(after, [name])
    record(after, said, when, note, tool)
    write(root, after)
    out["recent"] = [c["name"] for c in recent_of(after)]
    return out


# ---------------------------------------------------------------------- first read and the names typed since

def ensure(root: Path, books: list[dict], when: str, tool: str = "") -> dict:
    """The project's list, made on its first read from the rows, and with each name the rows hold that it lacks
    added (see `sync`). A project made before the list: its GETs boards each keep a revision first, named for how
    many codes it made, and gather each code's cards in one place, a copy of the GETs file kept in the root's
    `_Archive` first. Written only when something changed."""
    data = load(root)
    people = study_rows(books)
    extracts = extracts_of(people)
    if data is not None:
        added = sync(data, extracts)
        if added:
            record(data, [i18n.t("codes.said.new", name=x) for x in added], when, tool=tool)
            write(root, data)
        return data
    data = fresh(when)
    sync(data, extracts)
    n = len(data["codes"])
    gets = gets_mod()
    said = [i18n.t("codes.said.made", codes=i18n.t("codes.n.codes", n=n))]
    held = gets.load(root) if gets.gets_path(root).exists() else None
    if held is not None:
        gathered_all: list[str] = []
        boards = themes.boards_of(held)
        for board in boards:
            trial = json.loads(json.dumps(board))
            gathered = gather(trial, held)
            if trial == board:
                continue
            name = (themes.revision_name("codes_listed_moved", codes=i18n.t("codes.n.codes", n=n),
                                         names=", ".join(f'"{x}"' for x in gathered))
                    if gathered else themes.revision_name("codes_listed", codes=i18n.t("codes.n.codes", n=n)))
            themes.add_revision(board, name=name, at=when)
            gather(board, held)
            board["updated"] = when
            gathered_all += [x for x in gathered if x not in gathered_all]
        if any(b.get("updated") == when for b in boards):
            root_archive(root, gets.gets_path(root), ARCHIVE_LABEL)
            gets.write(root, gets._file(held, when))
        if gathered_all:
            said.append(i18n.t("codes.said.gathered", names=", ".join(gathered_all)))
    record(data, said, when, tool=tool)
    write(root, data)
    return data


def names_typed(root: Path, names, when: str) -> list[str]:
    """After a passage is saved on the Coding screen, each name it holds that the list lacks joins it, the list
    written only when one is new. Nothing when the project has no list yet, which its first read makes."""
    data = load(root)
    if data is None:
        return []
    have = by_norm(data)
    added = []
    for name in names:
        name = words(name)
        if name and norm(name) not in have:
            code = {"id": next_id(data), "name": name, "description": ""}
            data["codes"].append(code)
            have[norm(name)] = code
            added.append(name)
    if added:
        record(data, [i18n.t("codes.said.new", name=x) for x in added], when)
        write(root, data)
    return added


def came_back(root: Path, sent: list[dict], when: str, dry_run: bool = False, who: str = "") -> list[str]:
    """A shared copy's codes coming back: each code its list holds that the project's lacks, by name ignoring case,
    joins it with its description, and a code the project has keeps its own description. The names added."""
    data = load(root) or fresh(when)
    have = by_norm(data)
    added = []
    for c in sent:
        name = words(c.get("name"))
        if not name or norm(name) in have:
            continue
        code = {"id": next_id(data), "name": name, "description": str(c.get("description") or "").strip()}
        data["codes"].append(code)
        have[norm(name)] = code
        added.append(name)
    if added and not dry_run:
        record(data, [i18n.t("codes.said.came_back", names=", ".join(added), who=who or "?")], when)
        write(root, data)
    return added


# ---------------------------------------------------------------------- undo

def undo(root: Path, books: list[dict], when: str, redo: bool = False, dry_run: bool = False, tool: str = "") -> dict:
    """The list's last change put back, or with `redo` made again: each file it wrote put back from the copy kept
    before, after a copy of the file as it stands, only while every file still reads as the change left it, else
    refused whole with nothing written. The list takes its codes as they were. Answers `changes`, the line, and
    the list after."""
    data = load(root)
    step = (data or {}).get("redo" if redo else "undo")
    if not step:
        raise WorkbookError(i18n.t("codes.nothing_to_redo") if redo else i18n.t("codes.nothing_to_undo"))
    for f in step.get("files") or []:
        path = absolute(root, f["path"])
        if sha_of(path) != f.get("after"):
            raise WorkbookError(i18n.t("codes.changed_since", name=path.name))
        if not absolute(root, f["copy"]).exists():
            raise WorkbookError(i18n.t("codes.copy_gone", name=absolute(root, f["copy"]).name))
    what = step.get("what") or ""
    line = i18n.t("codes.said.redone", what=what) if redo else i18n.t("codes.said.undone", what=what)
    if dry_run:
        return {"changes": [line], "dry_run": True, "list": listing(data, study_rows(books))}
    checked_first(root, [absolute(root, f["path"]) for f in step.get("files") or []])
    back = []
    for f in step.get("files") or []:
        path = absolute(root, f["path"])
        mine = keep_copy(root, path, "pre-undo" if not redo else "pre-redo")
        shutil.copy2(absolute(root, f["copy"]), path)
        wb_mod.note_written(path)
        back.append({"path": f["path"], "copy": rel(root, mine), "after": sha_of(path)})
    other = {"what": step.get("what") or "", "at": when, "files": back, "codes": data["codes"]}
    data["codes"] = normal({"codes": step.get("codes") or []})["codes"]
    # the step taken leaves its own place for the other way's
    data.pop("redo" if redo else "undo", None)
    data["undo" if redo else "redo"] = other
    record(data, [line], when, tool=tool)
    write(root, data)
    return {"changes": [line], "dry_run": False, "list": listing(data, study_rows(books))}
