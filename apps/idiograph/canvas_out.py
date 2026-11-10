#!/usr/bin/env python3
"""The canvas as a PDF and as an image (1 November 2026, exportA, Adam: "Canvas should give both a PDF and an
image", the names saying the output you get), made by Typst from the board as its file keeps it (typst5, 9
November 2026, Adam about 18:10: Typst is the one engine for every PDF and picture, with no fallback, "it should
work or error").

The window, a browser's tab and the agents all ask the server, which reads the board as the screen reads it
(`pets_data`, `gets_data`), has the template lay it out by the canvas's own rule and draw it (`typeset_canvas`),
and writes the file where it goes (`place`, `write`): beside the workbook as the table's PDF goes, at the project's
root for the GETs, or where `out` names. No window and no browser takes part, so the file is the same on every
computer. When Typst cannot make it, the catalogue's plain sentence is the answer and nothing is written. The
picture is the board at its own size at twice its scale, so a slide or a thesis figure stays sharp.
"""
from __future__ import annotations

import os
import re
import struct
from datetime import datetime
from pathlib import Path

import boot
import i18n
import print_pdf
import themes_word
from workbook import WorkbookError

KINDS = ("pdf", "png")


def kind_of(value) -> str:
    """`pdf` or `png`, refused otherwise."""
    kind = str(value or "").strip().lower()
    if kind not in KINDS:
        raise WorkbookError(i18n.t("server.canvas_pdf_or_png"))
    return kind


def stem_of(title: str) -> str:
    """The file's name without its ending: the table's name with " canvas" after it, "P9 - Wren - Board 3 - PETs
    canvas", any character a file name cannot carry made a hyphen."""
    return print_pdf.safe_stem(f"{title} canvas")


def place(folder: Path, stem: str, kind: str, out=None, replace: bool = False,
          now: datetime | None = None) -> dict:
    """Where the canvas's file goes: `folder`, beside the workbook or at the project's root, named `stem` with its
    ending, the date and time in the name when a file has it, or over it with `replace`, or where `out` names,
    a folder or a file ending as the kind does. Nothing is written."""
    now = now or datetime.now().astimezone()
    ext = f".{kind}"
    if out is not None and str(out).strip():
        given = Path(str(out).strip()).expanduser()
        if given.is_dir():
            folder = given.resolve()
        elif given.suffix.lower() == ext and given.parent.is_dir():
            folder, stem = given.parent.resolve(), print_pdf.safe_stem(given.stem)
        else:
            raise WorkbookError(i18n.t("server.canvas_out_names", ext=ext))
    plain = Path(folder) / f"{stem}{ext}"
    if replace:
        path, dated = plain, False
    else:
        path, dated = themes_word.free_name(Path(folder), stem, now, ext)
    return {"path": str(path), "name": path.name, "folder": str(Path(folder)), "dated": dated, "kind": kind,
            "replaced": bool(replace and plain.exists())}


def write(made: dict, data: bytes) -> dict:
    """The bytes put at the place `place` named: a new file never over one there, or with `replaced` a whole new
    file in the old one's place, so a reader holding it never sees half."""
    path = Path(made["path"])
    if made.get("replaced"):
        part = path.with_name(f".{path.name}.part")
        part.write_bytes(data)
        os.replace(part, path)
        return made
    folder, stem, ext = path.parent, path.stem, path.suffix
    while True:
        try:
            with open(path, "xb") as handle:
                handle.write(data)
            return dict(made, path=str(path), name=path.name)
        except FileExistsError:
            path, _dated = themes_word.free_name(folder, stem, datetime.now().astimezone(), ext)
            made = dict(made, dated=True)


def checked(data: bytes, kind: str) -> bytes:
    """The bytes when they are the kind asked for, refused otherwise."""
    if kind == "pdf" and data.startswith(b"%PDF"):
        return data
    if kind == "png" and data.startswith(b"\x89PNG\r\n\x1a\n"):
        return data
    raise WorkbookError(i18n.t("server.canvas_not_made"))


def png_size(data: bytes) -> tuple[int, int]:
    """A PNG's width and height in pixels, from its header."""
    if not data.startswith(b"\x89PNG\r\n\x1a\n") or data[12:16] != b"IHDR":
        return 0, 0
    return struct.unpack(">II", data[16:24])


# ---- the canvas drawn by Typst from the board's saved layout (typst4, 9 November 2026)
#
# Adam, 9 November about 18:10: Typst is the one engine for every PDF and picture, with no fallback. The canvas
# needs no window for it: `typst_data` reads the board as the screen's own answer gives it (themes.state on PETs and
# LPETs, gets.state on GETs), what the canvas draws and where the file keeps it, and the template
# `typst/canvas-main.typ` measures every card itself and lays the board out by the canvas's own rule (thLayout and
# thCanvasWhole carried whole into canvas.typ), so a board never opened in a window comes out as one that was. Every
# word on the page comes in the data, in the user's language.

TYPST = boot.resource("typst")
TEMPLATE = TYPST / "canvas-main.typ"
QUOTES = ("off", "short", "full")
# a sticky note's four papers in the light theme (themes.css)
STICKY_PAPERS = {"yellow": "#FFF0A3", "pink": "#FDD5DF", "green": "#D3EDC4", "blue": "#CDE3F7"}
HUES = 8


def heading_of(name: str, board: str) -> str:
    """The canvas's title as thCanvasTitle makes it: the case by its pseudonym, "P9 Wren" for `P9 - Wren`, on GETs
    the project's name, with the board's name after it."""
    who = re.sub(r"^(P\d+)\s*-\s*", r"\1 ", " ".join(str(name or "").split()))
    return " · ".join(part for part in (who, str(board or "").strip()) if part)


def tints_of(groups: list[dict]) -> dict[str, dict]:
    """Each group's tint as thTints gives it: top-level groups take the eight hues in turn by their number, each its
    own, then grey, and a sub-group its group's hue a step lighter, and a step lighter again below that."""
    import themes_print
    parents = {m: g["id"] for g in groups for m in g.get("members") or []}
    ids = {g["id"] for g in groups}
    out: dict[str, dict] = {}
    used: set[int] = set()
    for g in groups:
        if g["id"] in parents:
            continue
        found = re.search(r"(\d+)$", str(g["id"]))
        want = (int(found.group(1)) + HUES - 1) % HUES if found else 0
        hue = next(((want + i) % HUES for i in range(HUES) if (want + i) % HUES not in used), None)
        if hue is not None:
            used.add(hue)
        out[g["id"]] = {"hue": hue, "step": 0}
    by_id = {g["id"]: g for g in groups}

    def walk(gid: str, hue, step: int, seen: frozenset) -> None:
        for m in by_id[gid].get("members") or []:
            if m not in ids or m in seen:
                continue
            out[m] = {"hue": hue, "step": min(step, 2)}
            walk(m, hue, step + 1, seen | {m})

    for gid in list(out):
        walk(gid, out[gid]["hue"], 1, frozenset({gid}))
    for g in groups:
        out.setdefault(g["id"], {"hue": None, "step": 0})
    return {gid: {"hue": themes_print.HUES[t["hue"]] if t["hue"] is not None else themes_print.GREY, "step": t["step"]}
            for gid, t in out.items()}


def bare_quote(said) -> str:
    """A quote's words without the inverted commas round it, "(no quote)" as none (thBareQuote)."""
    text = str(said or "").strip()
    if text.lower() == "(no quote)":
        return ""
    marks = ('"“”', "'‘’")
    while len(text) >= 2 and any(text[0] in m and text[-1] in m for m in marks):
        text = text[1:-1].strip()
    return text


def _language() -> dict:
    import themes_print
    lang = themes_print.page_lang()
    head, _, region = lang.partition("-")
    return {"lang": head.lower() or "en", **({"region": region.upper()} if region else {})}


def _card(**given) -> dict:
    """A card as the template reads it, every field there."""
    out = {"key": "", "x": 0, "y": 0, "text": "", "time": "", "sheet": "", "mark": "", "missing": False,
           "stack": "", "edges": 0, "more": False, "quote": "", "why": "", "in": False, "hue": "#8C8C8C", "step": 0,
           "drawn": True, "kind": "es", "badge": "", "case": "", "kicker": "", "desc": "", "from": "", "count": "",
           "fold": False, "marks": [], "empty": False}
    out.update(given)
    return out


def typst_data(state: dict, heading: str, *, gets: bool = False, lgets: bool = False, lpets: bool = False,
               notes: bool = True, quotes: str = "off", image: bool = False, close: int | None = None,
               ta: bool | None = None) -> dict:
    """The canvas of the board in `state`, the screen's own answer for it (themes.state, or gets.state on GETs), as
    the Typst template draws it: each card on the canvas where the board keeps it, with its words, timecode, sheet,
    marks, tint and stack, each label with what it holds, its description, its marks and its frame's badge, and each
    sticky note, in the order the canvas draws them. What waits in Not placed, what is set aside and what is
    stacked under a top stay off it, as on the canvas. On GETs a participant note comes only with `notes`, and the
    cards carry their case's colour and badge, their kicker and what they name. `quotes`, Off, Short or Full, is the
    canvas's Quotes on cards. `image` asks for the picture's page, sized to the board. `close`, the gap in seconds
    while Close pairs is on, draws each close pair's line on PETs as the canvas does (typst5). In a thematic analysis
    project's board of themes (`ta`, its own when left out) a statement's card is its code's, drawn as the code's
    card: Code with its extracts, the code's name and each participant's letter with how many are theirs."""
    way = quotes if quotes in QUOTES else "off"
    groups = state.get("groups") or []
    ids = {g["id"] for g in groups}
    discarded = set(state.get("discarded") or [])
    stacks = (state.get("stacks") or {}) if not gets else {}
    stacked = {k for keys in stacks.values() for k in keys}
    parents = {m: g["id"] for g in groups for m in g.get("members") or []}
    raw = state.get("cards") or []

    def on_canvas(c: dict) -> bool:
        key = c["key"]
        if key in discarded or key in stacked:
            return False
        # on PETs a statement in no PET waits in Not placed unless the board has it loose (thWaiting)
        return gets or key in parents or bool(c.get(th_loose()))

    cards = [c for c in raw if on_canvas(c)]
    shown = {c["key"] for c in cards}
    tints = tints_of(groups)
    reasons = state.get("discard_reasons") or {}
    sheets = state.get("sheets") or []
    first = sheets[0] if sheets else None
    gets_cases = {c["case"]: c for c in state.get("cases") or []} if gets else {}
    order = [c["case"] for c in state.get("cases") or []]
    if ta is None:
        ta = gets and not lgets and not lpets and i18n.method_now() == "ta"
    codes = _codes(state) if gets and ta else {}
    import gets_print
    out_cards = []
    for c in cards:
        key = c["key"]
        owner = parents.get(key)
        tint = tints.get(owner) if owner else None
        sheet = c.get("sheet") or ""
        item = _card(key=key, x=c.get("x", 0), y=c.get("y", 0), text=c.get("text") or "", time=c.get("time") or "",
                     sheet=sheet if sheet and sheet != first else "", missing=bool(c.get("missing")),
                     why=reasons.get(key, "") if owner is None else "", **({"in": True, **tint} if tint else {}))
        if not gets:
            item["mark"] = i18n.t("themes.card.missing") if c.get("missing") else (
                i18n.t("themes.card.changed") if c.get("changed") else "")
            held = len(stacks.get(key) or [])
            if held:
                item.update(stack=i18n.t("themes.stack.count", n=held), edges=min(4, held), more=held > 4)
            if way != "off":
                kept = (state.get("quotes") or {}).get(f"{c.get('sheet')}:{c.get('row')}") or {}
                q = next((x for x in kept.get("quotes") or [] if x.get("key") == key), None)
                item["quote"] = bare_quote(q and q.get("text"))
        else:
            item.update(_gets_card(c, state, gets_cases, order, parents, groups, lgets, way, gets_print))
            item["drawn"] = c.get("kind") != "pn" or notes
            if ta and (c.get("kind") or "pet") == "es":
                item.update(_code_card(c, codes, gets_cases, order, gets_print))
        out_cards.append(item)
    under = _counts(groups, shown, ids)
    out_groups = []
    for g in groups:
        members = [m for m in g.get("members") or [] if m in ids or m in shown]
        label = str(g.get("label") or "").strip()
        badge, short = str(under[g["id"]]["n"]), False
        if gets:
            n = _gets_count(g["id"], groups, ids, shown, {c["key"]: c for c in cards}, state)
            badge = i18n.t("themes.gets.of", count=n, total=state.get("total") or 0)
            short = g["id"] not in parents and n < (state.get("minimum") or 0)
        out_groups.append({
            "id": g["id"], "x": g.get("x", 0), "y": g.get("y", 0), "members": members,
            "label": i18n.t("themes.untitled") if not label or label == "Untitled" else label,
            "desc": " ".join(str(g.get("description") or "").split()), "upper": any(m in ids for m in members),
            **tints[g["id"]], "noted": bool(str(g.get("note") or "").strip()),
            "picked": bool((state.get("picks") or {}).get(g["id"])) and not gets, "badge": badge, "under": short})
    out_stickies = []
    for n in state.get("stickies") or []:
        if not isinstance(n, dict) or not n.get("id"):
            continue
        out_stickies.append({"id": str(n["id"]), "x": n.get("x", 0), "y": n.get("y", 0),
                             "text": str(n.get("text") or "").replace("\r\n", "\n").replace("\r", "\n").strip(),
                             "colour": STICKY_PAPERS.get(n.get("colour"), STICKY_PAPERS["yellow"]),
                             "in": n.get("in") if n.get("in") in ids else None})
    unit = _unit(gets, lgets, lpets)
    pairs = _pairs(state, {c["key"] for c in out_cards if c["drawn"] and not c["missing"]}, close) \
        if close and not gets else []
    return {**_language(), "heading": heading, "mode": "gets" if gets else "pets", "image": bool(image),
            "quotes": way, "title": i18n.t("themes.canvas.page_title", name=heading.replace(" · ", " - "), unit=unit),
            "cards": out_cards, "groups": out_groups, "stickies": out_stickies, "pairs": pairs}


def _pairs(state: dict, shown: set, gap: int) -> list[list[str]]:
    """The board's close pairs as the canvas draws their lines (thClosePairs): two statements on the canvas in one
    group, from one sheet, within `gap` seconds or its rows, those marked Not the same left out, each pair's two keys
    in transcript order (`themes.close_pairs`, the one rule the command line's board show gives)."""
    import themes
    cards = {c["key"]: c for c in state.get("cards") or [] if c["key"] in shown}
    version = {"groups": state.get("groups") or [], "cards": {k: {"x": 0, "y": 0} for k in cards},
               "not_same": state.get("not_same") or [], "discarded": [], "picks": {}}
    return [list(p["items"]) for p in themes.close_pairs(version, cards, gap)]


def _codes(state: dict) -> dict:
    """A thematic analysis project's codes as its board of themes counts them (gtCodes): each code by its words, any
    case, with its name as first written, how many extracts carry it, and how many are each participant's, in the
    order of the participants, a participant left out of the study not counted."""
    out: dict = {}
    for c in state.get("cases") or []:
        if c.get("in") is False:
            continue
        for line in (c.get("lines") or {}).values():
            code = _code_norm((line or {}).get("text"))
            if not code:
                continue
            held = out.setdefault(code, {"name": " ".join(str(line.get("text")).split()), "n": 0, "by": {}})
            held["n"] += 1
            held["by"][c["case"]] = held["by"].get(c["case"], 0) + 1
    return out


def _code_norm(text) -> str:
    return " ".join(str(text or "").split()).lower()


def _code_card(c: dict, codes: dict, cases: dict, order: list[str], gets_print) -> dict:
    """A statement's card on a thematic analysis project's board of themes as its code's card (gtCodeCardHtml):
    Code with how many extracts, the code's name, and under it each participant's letter on their colour with how
    many of the code's extracts are theirs. No participant's colour along its top, and no time or sheet."""
    entry = cases.get(c.get("case") or "") or {}
    line = (entry.get("lines") or {}).get(str(c["key"]).split("/es/", 1)[-1]) or {}
    code = codes.get(_code_norm(line.get("text") or c.get("text")))
    n = code["n"] if code else 1
    whos = []
    for case, k in (code["by"].items() if code else []):
        at = order.index(case) if case in order else -1
        held = cases.get(case) or {}
        colour = held.get("colour")
        colour = colour if isinstance(colour, int) and 0 <= colour < len(gets_print.CASE_COLOURS) \
            else max(0, at) % len(gets_print.CASE_COLOURS)
        who = str(held.get("who") or case)
        initial = (re.sub(r"[^\w]", "", who.replace("_", "")) or "?")[:1].upper()
        whos.append({"badge": held.get("badge") or initial, "colour": gets_print.CASE_COLOURS[colour], "n": str(k)})
    return {"kind": "code", "case": "", "badge": "", "time": "", "sheet": "", "desc": "", "from": "", "count": "",
            "fold": False, "quote": "", "text": code["name"] if code else (c.get("text") or ""), "empty": False,
            "kicker": i18n.t("codes.card_kicker", extracts=i18n.t("codes.n.extracts", n=n)), "whos": whos}


def th_loose() -> str:
    import themes
    return themes.LOOSE


def _unit(gets: bool, lgets: bool, lpets: bool) -> str:
    if lpets:
        return i18n.t("themes.unit.lpets")
    if lgets:
        return i18n.t("themes.unit.lgets")
    return i18n.t("themes.unit.gets") if gets else i18n.t("themes.unit.pets")


def _counts(groups: list[dict], shown: set, ids: set) -> dict:
    """The statements on the canvas under each group at any depth (thCardsUnder), its badge's number on PETs."""
    by_id = {g["id"]: g for g in groups}

    def under(gid: str, seen: frozenset) -> list[str]:
        out = []
        for m in by_id[gid].get("members") or []:
            if m in ids and m not in seen:
                out += under(m, seen | {m})
            elif m in shown:
                out.append(m)
        return out

    return {g["id"]: {"n": len(under(g["id"], frozenset({g["id"]})))} for g in groups}


def _gets_count(gid: str, groups: list[dict], ids: set, shown: set, cards: dict, state: dict) -> int:
    """The cases with a card anywhere under a GET, of those in the study, a participant note never counting
    (gtCount)."""
    inside = {c["case"] for c in state.get("cases") or [] if c.get("in")}
    by_id = {g["id"]: g for g in groups}
    found, todo, seen = set(), [gid], set()
    while todo:
        at = todo.pop()
        if at in seen:
            continue
        seen.add(at)
        for m in by_id[at].get("members") or []:
            if m in ids:
                todo.append(m)
            elif m in shown:
                c = cards.get(m) or {}
                if c.get("kind") != "pn" and c.get("case") in inside:
                    found.add(c["case"])
    return len(found)


def _gets_card(c: dict, state: dict, cases: dict, order: list[str], parents: dict, groups: list[dict], lgets: bool,
               way: str, gets_print) -> dict:
    """What a GETs card shows over the PETs card's: its case's colour along its top and its badge, its kind and
    pseudonym, a PET's description and count, what it names under its words, and its marks (gtCardHtml)."""
    case = c.get("case") or ""
    kind = c.get("kind") or "pet"
    entry = cases.get(case) or {}
    at = order.index(case) if case in order else -1
    colour = entry.get("colour")
    colour = colour if isinstance(colour, int) and 0 <= colour < len(gets_print.CASE_COLOURS) else max(0, at) % len(gets_print.CASE_COLOURS)
    who = c.get("who") or ""
    initial = (re.sub(r"[^\w]", "", who.replace("_", "")) or "?")[:1].upper()
    words = {"pet": i18n.t("themes.unit.lpet") if lgets else i18n.t("themes.unit.pet"), "sub": i18n.t("themes.kind.sub"),
             "es": i18n.t("themes.statement"), "pn": i18n.t("themes.kind.pn")}
    out = {"kind": kind, "case": gets_print.CASE_COLOURS[colour], "badge": entry.get("badge") or initial,
           "kicker": f"{words.get(kind, words['pet'])} · {who}", "text": c.get("text") or (words["pn"] if kind == "pn" else ""),
           "empty": not c.get("text")}
    if kind in ("pet", "sub") and not c.get("gone"):
        out["desc"] = " ".join(str(c.get("description") or "").split())
        n = int(c.get("statements") or 0)
        out["count"] = i18n.t("themes.count.statements", n=n)
        pet = next((p for p in entry.get("pets") or [] if p.get("id") == c.get("pet")), None)
        lines = entry.get("lines") or {}
        out["fold"] = bool(pet) and (any(k in lines for k in pet.get("statements") or []) or bool(pet.get("subs")))
    if kind != "es":
        out["time"], out["sheet"] = "", ""
    out["from"] = _gets_from(c, state, cases, parents, groups, lgets)
    marks = []
    if c.get("gone"):
        marks.append(i18n.t("themes.table.gone") if kind == "es" else i18n.t("themes.gets.gone", who=who))
    elif c.get("open"):
        marks.append(i18n.t("themes.gets.not_complete_l") if lgets else i18n.t("themes.gets.not_complete"))
    out["marks"] = marks
    if way != "off" and kind == "es" and not c.get("gone"):
        line = (entry.get("lines") or {}).get(str(c["key"]).split("/es/", 1)[-1]) or {}
        place = str(c["key"]).rsplit(":", 1)[-1]
        said = line.get("quotes") or []
        at_q = int(place) if place.isdigit() else -1
        out["quote"] = bare_quote(said[at_q]) if 0 <= at_q < len(said) else ""
    return out


def _gets_from(c: dict, state: dict, cases: dict, parents: dict, groups: list[dict], lgets: bool) -> str:
    """What a GETs card names under its words (gtFrom): a statement its PET and that PET's GET, and a second card of
    a PET the GETs its other cards are under."""
    by_id = {g["id"]: g for g in groups}

    def top_label(key: str) -> str | None:
        at, seen = parents.get(key), set()
        last = None
        while at is not None and at not in seen:
            seen.add(at)
            last = at
            at = parents.get(at)
        if last is None:
            return None
        label = str(by_id[last].get("label") or "").strip()
        return i18n.t("themes.untitled") if not label or label == "Untitled" else label

    kind = c.get("kind")
    cards = {x["key"]: x for x in state.get("cards") or []}
    discarded = set(state.get("discarded") or [])
    base = lambda key: "/".join(str(key).split("/")[:2]) if "/es/" not in key and "/pn/" not in key else key
    if kind == "es":
        entry = cases.get(c.get("case")) or {}
        pet = next((p for p in entry.get("pets") or [] if p.get("id") == c.get("pet")), None) if c.get("pet") else None
        ident = str(c["key"]).split("/es/", 1)[-1]
        line = (entry.get("lines") or {}).get(ident)
        if not pet:
            return i18n.t("themes.gets.from_aside") if line and line.get("discarded") else i18n.t("themes.gets.from_unplaced")
        holder = next((k for k in cards if base(k) == f"{c.get('case')}/{pet['id']}" and k not in discarded), None)
        get = top_label(holder) if holder else None
        unit = i18n.t("themes.unit.lpet") if lgets else i18n.t("themes.unit.pet")
        if get:
            return i18n.t("themes.gets.from_get", unit=unit, title=pet.get("title") or "",
                          get=i18n.t("themes.unit.lget") if lgets else i18n.t("themes.unit.get"), label=get)
        return i18n.t("themes.gets.from_pet", unit=unit, title=pet.get("title") or "")
    if kind not in ("pet", "sub"):
        return ""
    others = [k for k in cards if k != c["key"] and base(k) == base(c["key"]) and k not in discarded]
    if not others:
        return ""
    names = list(dict.fromkeys(n for n in (top_label(k) for k in others) if n))
    return i18n.t("themes.gets.also_under", names=", ".join(names)) if names else i18n.t("themes.gets.also_here")


def quotes_of(config: dict) -> str:
    """Quotes on cards as the canvas shows it from the settings: off, short or full (thQuotesWay)."""
    if config.get("card_quotes") is not True:
        return "off"
    return "full" if config.get("card_quotes_full") is True else "short"


def close_of(config: dict) -> int | None:
    """The gap in seconds while Close pairs is on in the settings, its lines drawn on a PETs canvas, or None
    (thCloseOn, thCloseGap)."""
    import themes
    return themes.close_gap(config.get("close_gap")) if config.get("close_pairs") is True else None


def pets_data(workbook: Path, case: str, board: str | None = None, **how) -> dict:
    """A PETs board's canvas data, the current board when `board` names none, read afresh as the screen reads it,
    the case named by its pseudonym in the title. Nothing is written."""
    import themes
    state = themes.state(Path(workbook), case, board=board)
    name = (state.get("version") or {}).get("name") or themes.FIRST_NAME
    return typst_data(state, heading_of(case, name), **how)


def gets_data(root: Path, books: list[dict], project: str, board: str | None = None, **how) -> dict:
    """A GETs board's canvas data, the board last open when `board` names none, under the project's name, read as
    the GETs screen reads it, inside a participant's LPETs or the project's LGETs when the request runs there (its
    words the LPETs' and LGETs'). Nothing is written."""
    import gets
    import themes
    state = gets.state(Path(root), books, board=board)
    name = (state.get("version") or {}).get("name") or themes.FIRST_NAME
    how.setdefault("lpets", gets.in_lpets())
    how.setdefault("lgets", gets.in_lgets())
    return typst_data(state, heading_of(project, name), gets=True, **how)


def drawn(data: dict) -> bool:
    """Whether anything is on the canvas to draw: a card, a label or a sticky note."""
    return any(c.get("drawn", True) for c in data.get("cards") or []) or bool(data.get("groups")) \
        or bool(data.get("stickies"))


def typeset_canvas(data: dict, kind: str) -> bytes:
    """The canvas's PDF, or its picture at two pixels a point, from `typst_data`'s data, through the one engine.
    A canvas with nothing on it is refused, and a failure is the engine's plain sentence. Nothing is written."""
    import typeset
    kind = kind_of(kind)
    if not drawn(data):
        raise WorkbookError(i18n.t("server.canvas_empty"))
    try:
        if kind == "pdf":
            return checked(typeset.render(TEMPLATE, dict(data, image=False), fmt="pdf"), "pdf")
        pages = typeset.render(TEMPLATE, dict(data, image=True), fmt="png", ppi=144.0)
    except typeset.Failed as exc:
        raise WorkbookError(str(exc)) from None
    return checked(pages[0] if pages else b"", "png")


def made(place_: dict, data: dict, dry_run: bool = False) -> dict:
    """The canvas typeset and written at the place `place` named, its size in bytes, and a picture's in pixels. With
    `dry_run` nothing is made or written. A failure writes nothing."""
    if dry_run:
        return place_
    out = typeset_canvas(data, place_["kind"])
    done = dict(write(place_, out), bytes=len(out))
    if place_["kind"] == "png":
        done["pixels"] = list(png_size(out))
    return done
