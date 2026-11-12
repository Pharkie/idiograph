#!/usr/bin/env python3
"""The GETs in print, and the audit trail the GETs screen shows: HTML pages the server renders from
the GETs file, for the browser to print or save as PDF on landscape A4.

`/gets/print` offers three. The GET table: each GET in canvas order with its note and its count,
then a row for every case in the study in case order, what of the case sits under the GET, its key
quote and the analyst's note for the row. The audit trail: for each GET a block per participant in
five columns, transcript turn, quote, statement, PET and GET, joined by thin lines in the GET's
tint, each block kept whole on a page. And the full set: a contents page, each case's PET table as
it came into the GETs, the GET table and the trail. Full sets out every item, Selected the quote
alone. A case's PET table is the table of PETs the print view draws, `themes_print.block_html` under
the rules it shares, `themes_print.BLOCKS`, set under the PET tables' part alone. Participant notes
are the analyst's own words on a participant, and they appear in none of it unless he ticks Include
participant notes.

Each page opens with a head as the table of PETs has it: the project as the title with the table's name
beside it, smaller, the research question in a block to their right, no rule, then the minimum and any case
not complete or changed since it came in. The board and the date are in the foot, and the GETs marked
complete are not said on the page (Adam, 31 October). The lines between the trail's columns are drawn by the page's
own layout, so they stay true at any width and on paper.

The GETs file, the themes files and the workbooks are only read, the workbooks read-only for the
words of a turn, and nothing is written anywhere.
"""
from __future__ import annotations

import html
import re
from datetime import datetime
from pathlib import Path

import openpyxl

import boot
import gets as gt
import i18n
import participants as people_mod
import themes as th
import themes_print as tp
from workbook import WorkbookError, detect_columns, ts_seconds

WHATS = ("table", "trail", "all")
DETAILS = ("full", "selected")
# The same views as Typst templates (typst3, 9 November 2026): the main file, which reads `typst_data`'s JSON and
# sets the head, the foot and the parts, each part a function in its own file beside it (gets-table.typ,
# gets-trail.typ) that a full set can import
TEMPLATE = boot.resource("typst") / "gets.typ"
# the full set, a contents page, each participant's table of PETs, the GET table and the trail (typst5)
FULL_TEMPLATE = boot.resource("typst") / "gets-all.typ"
# the two faces every print view is set in, Charis SIL and Nunito Sans, where the server serves family/static/fonts/
FONTS_CSS = "/fonts/fonts.css"
# The page's words are in static/i18n/en/page_print.json (i18npage, 28 October 2026), shared with the table of PETs


def ta() -> bool:
    """Whether the print is of a thematic analysis project (tagaps, 1 November 2026), whose themes hold its
    participants' codes with no PET between, so its trail has no PET column and no line speaks of PETs."""
    return i18n.method_now() == "ta"


def four_of(get: dict) -> bool:
    """Whether a GET's trail goes in four columns, the PETs' left out: a thematic analysis project's, whose themes
    hold codes alone, unless one holds a PET brought from elsewhere."""
    return ta() and not any(it.get("kind") in ("pet", "sub") for row in get.get("rows") or [] for it in row.get("items") or [])


def shown(four: bool = False) -> list[int]:
    """The trail's columns a print shows: all five, or four with the PETs' left out (see `four_of`)."""
    return [0, 1, 2, 4] if four else [0, 1, 2, 3, 4]


def heads(four: bool = False) -> str:
    """The five columns' heads, once under a GET's title and on paper at the top of each block with paths (see
    block_html), in the run's language, or the four of a thematic analysis project (see `four_of`)."""
    cols = (i18n.t("page_print.kind.passage"), i18n.t("page_print.kind.quote"), i18n.t("page_print.kind.statement"),
            i18n.t("page_print.kind.pet"), i18n.t("page_print.kind.get"))
    cols = tuple(cols[n] for n in shown(four))
    return '<div class="tr-cols" aria-hidden="true">' + "".join(f"<span>{esc(c)}</span>" for c in cols) + "</div>"


ROOM = 320          # the most characters of a turn the trail shows round a quote

esc = lambda text: html.escape(str(text or ""), quote=True)


# ------------------------------------------------------------------ the turns

def turns(workbook: Path, wanted) -> dict:
    """The words of the turns the trail names, by sheet and row, read from the workbook opened
    read-only. A workbook that cannot be read is refused, and nothing is written."""
    wanted = {(str(s), int(r)) for s, r in wanted if r is not None}
    if not wanted:
        return {}
    by_sheet: dict[str, set] = {}
    for sheet, row in wanted:
        by_sheet.setdefault(sheet, set()).add(row)
    try:
        book = openpyxl.load_workbook(workbook, read_only=True, data_only=True)
    except Exception as exc:
        raise WorkbookError(f"{Path(workbook).name} could not be read: {exc}")
    out = {}
    try:
        for ws in book.worksheets:
            rows = by_sheet.get(ws.title)
            if not rows:
                continue
            cols = detect_columns(ws)
            if "transcript" not in cols:
                continue
            width = max(cols.values())
            low, high = min(rows), max(rows)
            for r, values in enumerate(ws.iter_rows(min_row=low, max_row=high, max_col=width, values_only=True), start=low):
                if r not in rows:
                    continue
                values = tuple(values) + (None,) * (width - len(values))
                seconds = ts_seconds(values[cols["ts"] - 1]) if "ts" in cols else None
                out[(ws.title, r)] = {"text": str(values[cols["transcript"] - 1] or "").strip(), "seconds": seconds}
    finally:
        book.close()
    return out


# characters that read the same, so a quote typed with straight marks finds its curly ones
SAME = str.maketrans({"\u2019": "'", "\u2018": "'", "\u201c": '"', "\u201d": '"', "\u2013": "-", "\u2014": "-"})
SENTENCE = re.compile(r"[.!?\u2026][\"'\u201d\u2019)\]]*\s+")


def pieces(quote: str) -> list[str]:
    """A quote's pieces, its inverted commas off and split where an ellipsis joined them or a
    clarifying insert in square brackets stands, the insert not the turn's words."""
    text = str(quote or "").strip()
    if len(text) >= 2 and text[0] in "\"\u201c" and text[-1] in "\"\u201d":
        text = text[1:-1]
    return [p.strip(" ,.;:") for p in re.split(r"\s*(?:\u2026|\.\.\.|\[[^\]]*\])\s*", text)
            if any(ch.isalnum() for ch in p)]


def flat(text: str) -> tuple[str, list[int]]:
    """A turn's words in lower case with every run of space one space, and where each character of
    that came from, so a piece found in it is found in the turn."""
    out, at, space = [], [], False
    for i, ch in enumerate(str(text).translate(SAME)):
        if ch.isspace():
            if not space and out:
                out.append(" ")
                at.append(i)
            space = True
            continue
        space = False
        out.append(ch.lower())
        at.append(i)
    return "".join(out), at


def around(text: str, quote: str, room: int = ROOM) -> list[tuple[str, bool]]:
    """The sentence round a quote in its turn, as parts of words, the quote's own in bold. A
    turn the quote cannot be found in gives its opening words, none of them bold."""
    text = str(text or "")
    if not text.strip():
        return []
    low, at = flat(text)
    spans, start = [], 0
    for piece in pieces(quote):
        want = " ".join(piece.translate(SAME).lower().split())
        i = low.find(want, start) if want else -1
        if i < 0:
            continue
        spans.append((at[i], at[i + len(want) - 1] + 1))
        start = i + len(want)
    if not spans:
        cut = text[:room].rsplit(" ", 1)[0] if len(text) > room else text
        return [(cut + (" \u2026" if len(cut) < len(text) else ""), False)]
    first, last = spans[0][0], spans[-1][1]
    ends = [m.end() for m in SENTENCE.finditer(text, 0, first)]
    lo = ends[-1] if ends else 0
    after = SENTENCE.search(text, last)
    hi = after.end() if after else len(text)
    # a sentence that runs on is cut back to a little either side of the quote
    lo = max(lo, first - room // 2)
    hi = min(hi, last + room // 2)
    parts: list[tuple[str, bool]] = []
    if lo > 0:
        parts.append(("\u2026 ", False))
    at_ = lo
    for s, e in spans:
        if s > at_:
            parts.append((text[at_:s], False))
        parts.append((text[max(s, at_):e], True))
        at_ = max(at_, e)
    tail = text[at_:hi].rstrip()
    if tail:
        parts.append((tail, False))
    if hi < len(text.rstrip()):
        parts.append((" \u2026", False))
    return parts


# ------------------------------------------------------------------ the trail

def stamp(sheet: str, time: str) -> str:
    return " · ".join(p for p in (sheet, time) if p)


def tree(row: dict, rec: dict, notes: bool, selected: bool) -> list[dict]:
    """A participant's paths under one GET, as nodes in the five columns, 0 the transcript turn and
    4 the GET. A PET or a sub-theme goes through its statements and their quotes, statements of
    one turn together, a statement through its quotes to its turn, and a participant note stands
    alone, not from the transcript. Selected keeps the path of the row's quote alone."""
    lines = rec.get("lines") or {}
    key = (row.get("quote") or {}).get("key")

    def quotes_of(sheet, r, line, seconds, time) -> list[dict]:
        qs = gt.line_quotes(line) if line else []
        if selected:
            qs = [q for q in qs if q["key"] == key]
        turn = {"col": 0, "kind": "turn", "sheet": sheet, "row": r, "time": time, "seconds": seconds}
        if not qs:
            return [] if selected else [dict(turn, quote="")]
        return [{"col": 1, "kind": "quote", "text": q["text"], "key": q["key"] == key,
                 "kids": [dict(turn, quote=q["text"])]} for q in qs]

    def group(keys: list[str]) -> list[dict]:
        """Statements of one turn together, in the order they come, each turn once."""
        out, seen = [], {}
        for k in keys:
            line = lines.get(k)
            if line is None:
                continue
            at = (line.get("sheet"), line.get("row"))
            if at in seen:
                seen[at]["statements"].append(line)
                continue
            node = {"col": 2, "kind": "es", "statements": [line],
                    "kids": quotes_of(line.get("sheet"), line.get("row"), line, line.get("seconds"), line.get("time") or "")}
            seen[at] = node
            out.append(node)
        return [n for n in out if n["kids"] or not selected]

    nodes = []
    for it in row["items"]:
        if it["kind"] == "pn":
            if notes:
                nodes.append({"col": 2, "kind": "pn", "text": it["text"], "kids": []})
            continue
        if it["kind"] == "es":
            if it["gone"]:
                if not selected:
                    nodes.append({"col": 2, "kind": "es", "statements": [{"text": it["text"], "sheet": "", "time": ""}],
                                  "gone": True, "kids": []})
                continue
            kids = group([it["line"]])
            nodes.extend(kids)
            continue
        kids = group(it["lines"])
        if kids or not selected:
            nodes.append({"col": 3, "kind": it["kind"], "title": it["title"], "within": it["within"],
                          "gone": it["gone"], "kids": kids})
    if selected:
        # the first path that reaches the quote, and a participant note when he asked for them
        found = next((n for n in nodes if n["kind"] != "pn"), None)
        nodes = ([found] if found else []) + [n for n in nodes if n["kind"] == "pn"]
    return nodes


def flatten(get: dict, nodes: list[dict]) -> list[dict]:
    """The paths as rows of five cells, each node in the first row of the rows it spans, the line
    to its parent from that row, and for each column boundary the piece of upright line each row
    carries: `down` from a first child, `full` between, `up` to a last child."""
    rows: list[dict] = []

    def place(node: dict, parent_col: int | None, dashed: bool = False) -> None:
        start = len(rows)
        kids = node.get("kids") or []
        if not kids:
            rows.append({"cells": [None] * 5, "spines": {}})
        for kid in kids:
            place(kid, node["col"], dashed)
        row = rows[start]
        cell = dict(node, linked_in=parent_col is not None, linked_out=bool(kids), dashed=dashed or node["kind"] == "pn")
        row["cells"][node["col"]] = cell
        if parent_col is not None:
            for c in range(node["col"] + 1, parent_col):
                row["cells"][c] = {"kind": "pass", "dashed": cell["dashed"]}
        if len(kids) > 1:
            firsts = []
            at = start
            for kid in kids:
                firsts.append(at)
                at += span(kid)
            for r in range(firsts[0], firsts[-1] + 1):
                rows[r]["spines"][node["col"]] = "down" if r == firsts[0] else "up" if r == firsts[-1] else "full"

    def span(node: dict) -> int:
        kids = node.get("kids") or []
        return sum(span(k) for k in kids) if kids else 1

    place({"col": 4, "kind": "get", "label": get["label"], "kids": nodes}, None)
    return rows


def cell_html(cell: dict | None, col: int, audio) -> str:
    if cell is None:
        return f'<div class="tr-c c{col}"></div>'
    kind = cell["kind"]
    if kind == "pass":
        return f'<div class="tr-c c{col} pass{" dashed" if cell.get("dashed") else ""}"></div>'
    marks = " node" + (" in" if cell.get("linked_in") else "") + (" out" if cell.get("linked_out") else "") \
        + (" dashed" if cell.get("dashed") and cell.get("linked_in") else "")
    if kind == "get":
        return f'<div class="tr-c c{col}{marks} get"><span class="tr-title">{esc(cell["label"])}</span></div>'
    if kind in ("pet", "sub"):
        within = (f'<span class="tr-within">{esc(i18n.t("page_print.trail.in_pets", pets=", ".join(cell["within"])))}</span>'
                  if cell.get("within") else "")
        gone = f'<span class="tr-mark">{esc(i18n.t("page_print.trail.not_in_pets"))}</span>' if cell.get("gone") else ""
        said = i18n.t("page_print.kind.pet") if kind == "pet" else i18n.t("page_print.kind.sub_theme")
        return (f'<div class="tr-c c{col}{marks} pet"><span class="tr-kind">{esc(said)}</span>'
                f'<span class="tr-title">{esc(cell["title"])}</span>{within}{gone}</div>')
    if kind == "pn":
        return (f'<div class="tr-c c{col}{marks} pn"><span class="tr-kind">{esc(i18n.t("page_print.kind.participant_note"))}</span>'
                f'<span class="tr-said">{esc(cell["text"])}</span><span class="tr-mark">{esc(gt.NOT_FROM)}</span></div>')
    if kind == "es":
        said = "".join(f'<span class="tr-st">{esc(s.get("text"))}</span>' for s in cell["statements"])
        first = cell["statements"][0]
        where = stamp(first.get("sheet") or "", first.get("time") or "")
        gone = f'<span class="tr-mark">{esc(i18n.t("page_print.trail.not_in_workbook"))}</span>' if cell.get("gone") else ""
        return (f'<div class="tr-c c{col}{marks} es">{said}'
                + (f'<span class="tr-where">{esc(where)}</span>' if where else "") + f"{gone}</div>")
    if kind == "quote":
        tag = f'<span class="tr-key">{esc(i18n.t("page_print.kind.quote"))}</span>' if cell.get("key") else ""
        return f'<div class="tr-c c{col}{marks} quote"><span class="tr-q">{esc(tp.quoted(cell["text"]))}</span>{tag}</div>'
    # the turn: its sheet and timecode, and the sentence round the quote with the quote in bold
    words = cell.get("words")
    if words is None:
        body = f'<span class="tr-said tr-unread">{esc(i18n.t("page_print.trail.unread"))}</span>'
    else:
        body = '<span class="tr-said">' + "".join(f"<b>{esc(t)}</b>" if bold else esc(t) for t, bold in words) + "</span>"
    where = stamp(cell.get("sheet") or "", cell.get("time") or "")
    url = audio(cell) if audio else None
    # the recording's offset, which playback adds to every time code (20 October)
    shift = audio.offset(cell) if url and hasattr(audio, "offset") else 0
    at = max(0.0, (cell.get("seconds") or 0) + shift)
    from_ = (i18n.t("page_print.trail.play_from", time=cell["time"]) if cell.get("time")
             else i18n.t("page_print.trail.play_from_start"))
    play = (f' data-audio="{esc(url)}" data-at="{at:g}" role="button" tabindex="0"'
            f' title="{esc(from_)}"') if url else ""
    return f'<div class="tr-c c{col}{marks} turn{" playable" if url else ""}"{play}><span class="tr-where">{esc(where)}</span>{body}</div>'


def rows_html(rows: list[dict], audio, four: bool = False) -> str:
    """Each row's five cells, the upright piece of line in the gap before a column drawn inside that
    column's cell, half a gap to its left, so it follows the column wherever the column's words put it
    (17 October, later)."""
    out = []
    for row in rows:
        cells = []
        for c in shown(four):
            cell = cell_html(row["cells"][c], c, audio)
            how = row["spines"].get(c)
            if how:
                cell = cell[:-len("</div>")] + f'<i class="tr-sp b{c} {how}"></i></div>'
            cells.append(cell)
        out.append(f'<div class="tr-row">{"".join(cells)}</div>')
    return "".join(out)


def block_nodes(row: dict, rec: dict, words: dict | None, notes: bool, selected: bool) -> list[dict]:
    """A participant's paths under one GET (`tree`), each turn given the sentence round its quote, the words the
    HTML trail and the Typst trail both set."""
    nodes = tree(row, rec, notes, selected)
    for node in walk(nodes):
        if node["kind"] == "turn":
            node["case"] = row["case"]
            turn = (words or {}).get((node["sheet"], node["row"])) if words is not None else None
            if words is None:
                node["words"] = None
            elif turn is None:
                node["words"] = around(node.get("quote") or "", node.get("quote") or "")
            else:
                node["words"] = around(turn["text"], node.get("quote") or "")
                if node.get("seconds") is None:
                    node["seconds"] = turn["seconds"]
    return nodes


def block_html(get: dict, row: dict, rec: dict, words: dict | None, notes: bool, selected: bool, audio) -> str:
    """One participant's block: the pseudonym and the case's marks, then the paths."""
    nodes = block_nodes(row, rec, words, notes, selected)
    # a participant with no PETs and nothing here says so in one line, with no mark by the name
    bare = row["none"] and not row["counted"] and not ta()
    marks = row_marks(row, bare)
    head = (f'<h3 class="tr-who">{badge_of(row)}{esc(row["who"])}'
            + "".join(f'<span class="tr-mark">{esc(m)}</span>' for m in marks) + "</h3>")
    body = ""
    if not row["counted"]:
        body += f'<p class="tr-none">{esc(gt.NOTHING_NO_PETS if bare else gt.NOTHING)}</p>'
    elif selected and not (row.get("quote") and nodes):
        body += f'<p class="tr-none">{esc(i18n.t("page_print.gets.no_quote"))}</p>'
    if nodes:
        body += f'<div class="tr-rows">{rows_html(flatten(get, nodes), audio, four_of(get))}</div>'
    # On paper each block with paths carries the five columns' heads at its top, where the screen shows them once
    # under the GET's title, so every printed page, which opens on a block kept whole, carries them as a table's
    # headings do (17 October, later, where the PDF showed them at each GET's start alone)
    again = heads(four_of(get)).replace('class="tr-cols"', 'class="tr-cols tr-again"') if nodes else ""
    return f'<article class="tr-block">{again}{head}{body}</article>'


def walk(nodes: list[dict]):
    for n in nodes:
        yield n
        yield from walk(n.get("kids") or [])


def wanted(get: dict, recs: dict) -> dict[str, set]:
    """The turns each case's paths under a GET name, by case."""
    out: dict[str, set] = {}
    for row in get["rows"]:
        rec = recs.get(row["case"]) or {}
        for node in walk(tree(row, rec, True, False)):
            if node["kind"] == "turn":
                out.setdefault(row["case"], set()).add((node["sheet"], node["row"]))
    return out


def read_turns(get_list: list[dict], recs: dict, books: dict) -> dict:
    """The words of every turn the trails of these GETs name, by case, None for a case whose
    workbook cannot be read."""
    need: dict[str, set] = {}
    for g in get_list:
        for case, keys in wanted(g, recs).items():
            need.setdefault(case, set()).update(keys)
    out = {}
    for case, keys in need.items():
        book = books.get(case)
        try:
            out[case] = turns(book, keys) if book else None
        except (WorkbookError, OSError):
            out[case] = None
    return out


def badge_of(row: dict) -> str:
    """A participant's badge beside the name, the initial in a dot of the case's colour (16 October),
    the name beside it saying it for a screen reader. A row with no colour has none."""
    if row.get("colour") is None:
        return ""
    return f'<span class="gt-badge case-{int(row["colour"])}" aria-hidden="true">{esc(row.get("badge") or "")}</span>'


def badge(get: dict, total: int, minimum: int) -> str:
    under = get["count"] < minimum
    said = (i18n.t("page_print.gets.under_minimum", minimum=minimum) if under
            else i18n.t("page_print.gets.count", count=get["count"], n=total))
    short = i18n.t("page_print.gets.count_short", count=get["count"], total=total)
    return (f'<span class="tr-count{" under" if under else ""}" title="{esc(said)}">{esc(short)}</span>'
            + (f'<span class="tr-under">{esc(said)}</span>' if under else ""))


def trail_section(get: dict, tint: str, recs: dict, words: dict, total: int, minimum: int, notes: bool,
                  selected: bool, audio, head: bool = True) -> str:
    """One GET's audit trail: its title and count, the five columns' heads, and a block per
    participant of the study in case order."""
    out = [f'<section class="tr-get {tint}" id="trail-{esc(get["id"])}">']
    if head:
        out.append(f'<h2 class="tr-head"><span class="tr-title">{esc(get["label"])}{get_desc(get)}</span>'
                   f'{badge(get, total, minimum)}</h2>')
        if get["note"]:
            out.append(f'<p class="tr-gnote">{esc(get["note"])}</p>')
    # the columns' heads and the blocks in one box, `.tr-wide`, whose five columns they share (17 October, later)
    four = four_of(get)
    out.append(f'<div class="tr-wide{" tr-four" if four else ""}">')
    out.append(heads(four))
    for row in get["rows"]:
        out.append(block_html(get, row, recs.get(row["case"]) or {}, words.get(row["case"], {}), notes, selected, audio))
    out.append("</div>")
    out.append("</section>")
    return "\n".join(out)


# ------------------------------------------------------------------ the table

def item_html(it: dict, notes: bool) -> str:
    within = (f' <span class="within">{esc(i18n.t("page_print.gets.in_pets", pets=", ".join(it["within"])))}</span>'
              if it.get("within") else "")
    if it["kind"] == "pn":
        return (f'<div class="it pn"><span class="kind">{esc(i18n.t("page_print.kind.participant_note"))}</span> {esc(it["text"])}'
                f' <span class="mine">{esc(gt.NOT_FROM)}</span></div>') if notes else ""
    if it["kind"] in ("pet", "sub"):
        n = it["statements"]
        gone = f' <span class="gone">{esc(i18n.t("page_print.gets.not_in_pets"))}</span>' if it["gone"] else ""
        kind = i18n.t("page_print.kind.pet") if it["kind"] == "pet" else i18n.t("page_print.kind.sub_theme")
        return (f'<div class="it"><span class="kind">{esc(kind)}</span> '
                f'{esc(it["title"])} <span class="n">{esc(i18n.t("page_print.gets.statements", n=n))}</span>{within}{gone}</div>')
    where = f' <span class="tc">{esc(it["time"])}</span> <span class="sheet">{esc(it["sheet"])}</span>' if not it["gone"] else \
        f' <span class="gone">{esc(i18n.t("page_print.gets.not_in_workbook"))}</span>'
    out = f'<div class="it"><span class="kind">{esc(i18n.t("page_print.kind.statement"))}</span> {esc(it["text"])}{where}{within}'
    out += "".join(f'<p class="kq">{esc(tp.quoted(q["text"]))}</p>' for q in it["quotes"])
    out += "".join(f'<p class="en">{esc(n)}</p>' for n in it["notes"])
    return out + "</div>"


def quote_html(q: dict | None, bold=None) -> str:
    """A row's key quote in its cell, his bold in it kept on its words as Trajectories shows it (lpetmarks)."""
    if not q:
        return f'<span class="none">{esc(i18n.t("page_print.gets.no_quote"))}</span>'
    words = "".join(f"<b>{esc(t)}</b>" if on else esc(t) for t, on in gt.quote_bold(q["text"], bold))
    return (f'<i>‘{words}’</i> <span class="tc">{esc(q["time"])}</span>'
            f' <span class="sheet">{esc(q["sheet"])}</span>')


def get_desc(get: dict) -> str:
    """A GET's description, a line of its title's heading under it, or nothing for none or with the
    Descriptions tick off, which leaves it out of `get` (Adam, 21 October)."""
    said = get.get(th.DESCRIPTION) or ""
    return f'<span class="gdesc">{esc(said)}</span>' if said else ""


def row_marks(row: dict, bare: bool) -> list[str]:
    """What a participant's row says by their name: no PETs yet or PETs not complete, then changed since it came
    in. A thematic analysis project's participants have no PETs to say so of (tagaps)."""
    marks = []
    if ta():
        pass
    elif row["none"] and not bare:
        marks.append(gt.NO_PETS)
    elif row["open"]:
        marks.append(gt.NOT_COMPLETE)
    if row.get("changed"):
        marks.append(gt.CHANGED)
    return marks


def table_section(get: dict, tint: str, total: int, minimum: int, notes: bool, selected: bool) -> str:
    """One GET of the table: its bar in its tint with its count, its note, then a row for every case
    of the study, what of the case sits under it, its quote and his note for the row."""
    out = [f'<section class="get {tint}">',
           f'<h3 class="bar"><span class="title">{esc(get["label"])}{get_desc(get)}</span>{badge(get, total, minimum)}</h3>']
    if get["note"]:
        out.append(f'<p class="tnote">{esc(get["note"])}</p>')
    cols = ([i18n.t("page_print.gets.participant")] + ([] if selected else [i18n.t("page_print.gets.under_this_get")])
            + [i18n.t("page_print.kind.quote"), i18n.t("page_print.gets.note")])
    # the table in a box of its own, which scrolls sideways where a narrow window cannot give its columns room
    out.append('<div class="gt-wide"><table class="gt"><thead><tr>' + "".join(f"<th>{esc(h)}</th>" for h in cols) + "</tr></thead><tbody>")
    for row in get["rows"]:
        bare = row["none"] and not row["counted"] and not ta()
        marks = row_marks(row, bare)
        who = (f'<td class="who">{badge_of(row)}{esc(row["who"])}'
               + "".join(f'<span class="mark">{esc(m)}</span>' for m in marks) + "</td>")
        # Selected keeps the quote alone, and a participant note only when he ticked them
        items = "".join(item_html(it, notes) for it in row["items"] if not selected or it["kind"] == "pn")
        nothing = "" if row["counted"] else f'<p class="none">{esc(gt.NOTHING_NO_PETS if bare else gt.NOTHING)}</p>'
        quote = quote_html(row["quote"], row.get("bold")) if row["counted"] else ""
        cells = [who]
        if selected:
            cells.append(f'<td class="kqcell">{nothing}{quote}{items}</td>')
        else:
            cells += [f'<td class="items">{nothing}{items}</td>', f'<td class="kqcell">{quote}</td>']
        cells.append(f'<td class="rnote">{esc(row["note"])}</td>')
        out.append(f'<tr class="{"" if row["counted"] else "empty"}">{"".join(cells)}</tr>')
    out.append("</tbody></table></div></section>")
    return "\n".join(out)


# ------------------------------------------------------------- the participants table

def people_section(rows: list[dict]) -> str:
    """The participants table (pbioexport, 11 November 2026, with Participants table ticked), the first part of
    the page, under its heading as a full set's parts are: a row for each participant in order, their number, their
    pseudonym, their label and their pen portrait, a cell empty where they have none, and never a picture. The
    heads repeat on each page and a row is never split, as the GET table's."""
    heads = "".join(f"<th>{esc(h)}</th>" for h in people_mod.table_heads())
    body = "".join(f'<tr><td class="pt-n">{esc(r["number"])}</td><td class="pt-who">{esc(r["pseudonym"])}</td>'
                   f'<td class="pt-label">{esc(r["label"])}</td><td class="pt-portrait">{esc(r["portrait"])}</td></tr>'
                   for r in rows)
    return (f'<section class="part first people" id="participants"><h2>{esc(i18n.t("page_print.people.heading"))}</h2>'
            f'<div class="gt-wide"><table class="pt"><thead><tr>{heads}</tr></thead><tbody>{body}</tbody></table></div>'
            "</section>")


# ------------------------------------------------------------- the PET tables

def pet_tops(rec: dict, selected: bool, descriptions: bool) -> tuple[list[dict], dict]:
    """A case's PETs from its copy as the table of PETs reads them, each PET with its statements, or under Selected
    its picks alone, and its sub-themes under it, the descriptions as Descriptions asks, and each PET's tint. The one
    walk the HTML full set (`pet_section`) and the Typst one (`pet_data`) both read."""
    pets = {p["id"]: p for p in rec.get("pets") or []}
    lines = rec.get("lines") or {}
    shades = tp.tints([{"id": p["id"], "members": list(p.get("subs") or [])} for p in rec.get("pets") or []])

    def row(key: str) -> dict:
        line = lines[key]
        own = gt.line_quotes(line, key)
        return {"key": key, "text": line.get("text") or "", "sheet": line.get("sheet") or "",
                "time": line.get("time") or "", "quote": own[0]["text"] if own else ""}

    def picked(q: dict) -> dict:
        # a pick is a statement's own quote, the statement at its place, and its words when the copy
        # holds them
        return {"key": q["key"], "text": (lines.get(q["key"]) or {}).get("text") or "", "sheet": q["sheet"],
                "time": q["time"], "quote": q["text"]}

    def theme(p: dict, seen: frozenset) -> dict:
        subs = [theme(pets[s], seen | {s}) for s in p.get("subs") or [] if s in pets and s not in seen]
        if selected:
            keys = dict.fromkeys(k for k in p.get("picks") or [])
            own = [picked(q) for q in (gt.quote_at(rec, k) for k in keys) if q]
        else:
            own = [row(k) for k in dict.fromkeys(p.get("statements") or []) if k in lines]
        return dict({"id": p["id"], "label": p["title"], "note": p.get("note") or "", "statements": own, "themes": subs},
                    **gt.described(p))

    tops = th.descriptions_shown({"themes": [theme(p, frozenset({p["id"]})) for p in rec.get("pets") or []
                                             if p.get("parent") is None]}, descriptions)["themes"]
    return tops, shades


def pet_data(case: str, rec: dict, selected: bool, labels: str = th.LETTERS, sending: bool = False,
             descriptions: bool = True) -> dict:
    """A case's PET table in the full set as the Typst template reads it (typst5, 9 November 2026), from the walk
    `pet_section` reads: its kicker, the case, its board unless for sending, whether its PETs are complete, and its
    PETs as the table of PETs' blocks, or the line saying it has none."""
    done = ""
    if rec.get("complete"):
        done = i18n.t("page_print.gets.pets_complete") if sending else i18n.t("page_print.gets.pets_complete_board")
    elif rec.get("state") == "in":
        done = gt.NOT_COMPLETE
    out = {"kicker": i18n.t("page_print.gets.pet_table"), "who": gt.who(case),
           "board": str(rec.get("name") or "") if not sending else "", "done": done, "none": "", "themes": [],
           "empty": "" if selected else i18n.t("page_print.pets.empty")}
    if rec.get("state") != "in" or not rec.get("pets"):
        return dict(out, none=gt.NO_PETS)
    tops, shades = pet_tops(rec, selected, descriptions)
    numbers = th.pet_numbers(tops, labels)
    return dict(out, themes=[tp.block_data(t, shades, 0, numbers) for t in tops])


def pet_section(case: str, rec: dict, selected: bool, labels: str = th.LETTERS, sending: bool = False,
                descriptions: bool = True) -> str:
    """A case's PET table as it came into the GETs, from its copy, in the shape of the table of PETs
    the print view draws: PET by PET in the order its board reads them, each under its label and
    title, its note under it, then a row for each statement, its words and reference on the left and
    its own quote on the right, and its sub-themes under it after its own statements, as the copy
    keeps no order between the two. The labels are `themes.pet_numbers`', the project's `labels`.
    Selected keeps each PET's picks alone, a row for each with the statement whose quote it is on the
    left, and leaves its other statements out. For sending the case's board goes unnamed."""
    board = f'<span class="board">, {esc(rec["name"])}</span>' if rec.get("name") and not sending else ""
    head = (f'<header class="case-head" id="pets-{esc(gt.who(case))}"><p class="kicker">{esc(i18n.t("page_print.gets.pet_table"))}</p>'
            f'<h2>{esc(gt.who(case))}{board}</h2>')
    if rec.get("complete"):
        done = i18n.t("page_print.gets.pets_complete") if sending else i18n.t("page_print.gets.pets_complete_board")
        head += f'<p class="done">{esc(done)}</p>'
    elif rec.get("state") == "in":
        head += f'<p class="done">{esc(gt.NOT_COMPLETE)}</p>'
    head += "</header>"
    if rec.get("state") != "in" or not rec.get("pets"):
        return f'<section class="case">{head}<p class="none">{esc(gt.NO_PETS)}</p></section>'
    tops, shades = pet_tops(rec, selected, descriptions)
    numbers = th.pet_numbers(tops, labels)
    # its statements left out by choice under Selected, a PET is not empty, so it never says so
    body = "\n".join(tp.block_html(t, shades, numbers=numbers, empty=not selected) for t in tops)
    return f'<section class="case">{head}{body}</section>'


# ------------------------------------------------------------------- the page

# the page, landscape A4 with a 14mm margin, and the rules of the GET table's bars, its note, a line
# gone and an empty cell, which the table of PETs, under `.pets`, sets its own way
PAGE = """
@page { size: A4 landscape; margin: 14mm }
body { max-width: 277mm; }
.bar {
  display: flex; flex-wrap: wrap; align-items: baseline; gap: 2pt 10pt; margin: 0 0 4pt; padding: 4pt 8pt;
  font-family: var(--serif); font-weight: normal; font-size: 13pt; line-height: 1.3; color: var(--ink);
  background: color-mix(in srgb, var(--hue) 16%, #fff); border-left: 4pt solid var(--hue);
  break-after: avoid; page-break-after: avoid;
}
.bar .title { flex: 1 1 auto; }
.gdesc { display: block; margin-top: 1pt; font-size: 10pt; line-height: 1.35; color: var(--ink-soft); }
.get .tnote { margin: 2pt 0 5pt; padding: 0 8pt; font-family: var(--serif); font-size: 10pt; line-height: 1.4;
  color: var(--ink-soft); white-space: pre-line; break-after: avoid; page-break-after: avoid; }
.gone { font-family: var(--sans); font-size: 8pt; color: var(--ink-faint); margin-left: 4pt; }
.none { margin: 2pt 0 0 6pt; }
"""

STYLE = """
.waiting { margin: 3pt 0 0; font-size: 9pt; color: var(--amber); }
.contents { break-after: page; page-break-after: always; }
.contents h2, .part > h2 { font-family: var(--serif); font-weight: normal; font-size: 16pt; margin: 0 0 8pt;
  border-bottom: 1px solid var(--rule-firm); padding-bottom: 3pt; }
.contents ol { margin: 4pt 0 0; padding-left: 18pt; font-size: 11pt; line-height: 1.6; }
.contents a { color: var(--ink); text-decoration: none; }
.part { break-before: page; page-break-before: always; }
.part.first { break-before: auto; page-break-before: auto; }
.case { margin: 0 0 18pt; font-family: var(--sans); font-size: 10pt; line-height: normal; color: var(--ink); }
.case + .case { break-before: page; page-break-before: always; }
.case-head { margin: 0 0 10pt; }
.case-head h2 { margin: 2pt 0 0; font-family: var(--serif); font-weight: normal; font-size: 16pt; }
.case-head .board { color: var(--ink-soft); }
.case-head .done { margin: 3pt 0 0; }
.get { margin: 0 0 16pt; --hue: var(--hue-base); }
.get .bar { break-after: avoid; page-break-after: avoid; }
.tr-count { flex: none; font-family: var(--sans); font-size: 8.5pt; color: var(--ink-soft); padding: 0 6pt;
  border: 1px solid color-mix(in srgb, var(--hue) 60%, #fff); border-radius: 8pt; }
.tr-count.under { border-style: dashed; }
.tr-under { flex: none; font-family: var(--sans); font-size: 8pt; color: var(--ink-soft); }
/* The GET table keeps 720px, room for its four columns, and in a narrower window scrolls sideways in its own box
   under the GET's bar, as the trail does, where at 360 its columns stood a word a line (17 October, later). Paper,
   A4 landscape, is wider and never scrolls. */
.gt-wide { overflow-x: auto; }
table.gt { width: 100%; min-width: 720px; border-collapse: collapse; }
.gt thead { display: table-header-group; }
.gt th { text-align: left; font-weight: 600; font-size: 7.5pt; letter-spacing: .08em; text-transform: uppercase;
  color: var(--ink-faint); padding: 2pt 6pt 3pt; border-bottom: 1px solid var(--rule-firm); }
.gt td { vertical-align: top; padding: 4pt 6pt; border-bottom: 1px solid var(--rule); }
.gt tr { break-inside: avoid; page-break-inside: avoid; }
.gt td.who { width: 22mm; font-family: var(--serif); font-size: 11pt; }
.gt td.who .mark { display: block; font-family: var(--sans); font-size: 7.5pt; color: var(--amber); }
.gt td.kqcell { width: 70mm; font-family: var(--serif); font-size: 10.5pt; line-height: 1.35; }
.gt td.rnote { width: 50mm; font-size: 9pt; line-height: 1.4; color: var(--ink-soft); white-space: pre-line; }
.gt tr.empty td.who { color: var(--ink-faint); }
/* the participants table (pbioexport): the GET table's heads and rules, the number in the quiet sans, the pseudonym
   and the label in the serif, the pen portrait taking the rest of the width */
.part.people { margin-bottom: 18pt; }
table.pt { width: 100%; min-width: 720px; border-collapse: collapse; }
.pt thead { display: table-header-group; }
.pt th { text-align: left; font-weight: 600; font-size: 7.5pt; letter-spacing: .08em; text-transform: uppercase;
  color: var(--ink-faint); padding: 2pt 6pt 3pt; border-bottom: 1px solid var(--rule-firm); }
.pt td { vertical-align: top; padding: 4pt 6pt; border-bottom: 1px solid var(--rule); }
.pt tr { break-inside: avoid; page-break-inside: avoid; }
.pt td.pt-n { width: 18mm; font-family: var(--sans); font-size: 9pt; line-height: 1.5; color: var(--ink-soft);
  font-variant-numeric: tabular-nums; }
.pt td.pt-who { width: 34mm; font-family: var(--serif); font-size: 11pt; line-height: 1.35; }
.pt td.pt-label { width: 60mm; font-family: var(--serif); font-size: 10.5pt; line-height: 1.35; }
.pt td.pt-portrait { font-family: var(--serif); font-size: 10pt; line-height: 1.4; }
.it { font-family: var(--serif); font-size: 10.5pt; line-height: 1.35; margin: 0 0 4pt; }
.it .kind { font-family: var(--sans); font-size: 7.5pt; font-weight: 600; letter-spacing: .04em; color: var(--ink-faint); }
.it .n, .it .within, .it .mine { font-family: var(--sans); font-size: 8pt; color: var(--ink-faint); }
.it .kq { margin: 2pt 0 0 10pt; font-style: italic; }
.it .en { margin: 2pt 0 0 10pt; font-family: var(--sans); font-size: 8.5pt; color: var(--ink-soft); }
.it.pn { border-left: 2px dashed var(--rule-firm); padding-left: 6pt; }
.kqcell i { font-style: italic; }
.tc, .sheet { font-family: var(--mono); font-size: 8pt; color: var(--ink-soft); white-space: nowrap; }
.none { color: var(--ink-faint); font-size: 9pt; font-family: var(--sans); }
.tr-get { --hue: var(--hue-base); margin: 0 0 14pt; }
.tr-get + .tr-get { break-before: page; page-break-before: always; }
@media print { .gt-wide { overflow: visible; } }
.tr-head { display: flex; flex-wrap: wrap; align-items: baseline; gap: 2pt 10pt; margin: 0 0 4pt; padding: 4pt 8pt;
  font-family: var(--serif); font-weight: normal; font-size: 13pt; background: color-mix(in srgb, var(--hue) 16%, #fff);
  border-left: 4pt solid var(--hue); break-after: avoid; page-break-after: avoid; }
.tr-head .tr-title { flex: 1 1 auto; }
.tr-gnote { margin: 2pt 0 6pt; padding: 0 8pt; font-family: var(--serif); font-size: 10pt; color: var(--ink-soft); white-space: pre-line; }
""" + "\n"

# The cases' colours as the light theme gives them in themes.css, `--th-case0` to `--th-case24`, since
# the page is always light, and the badge of each participant beside the name in the GET table and the
# audit trail (16 October), the initial in the paper's white on the case's colour, at 8.5pt so it reads
# on paper and on the screen alike (16 October, later), where at 7pt it was a dot.
CASE_COLOURS = ("#0D6ABB", "#706D06", "#774E6D", "#5B4315", "#2841B9", "#02544C", "#851286", "#616491",
                "#2A311A", "#325453", "#6C36BE", "#47055B", "#113434", "#3F5F8A", "#61573E", "#513A49",
                "#333D01", "#5C509D", "#372D02", "#4B3882", "#076C92", "#5E1C94", "#013728", "#033B7A",
                "#412F50")
CASES = "".join(f".case-{i} {{ --case: {c}; }} " for i, c in enumerate(CASE_COLOURS)) + """
.gt-badge { display: inline-block; min-width: 13pt; height: 13pt; margin-right: 4pt; padding: 0 3.5pt; box-sizing: border-box;
  border-radius: 7pt; background: var(--case); color: var(--paper); font-family: var(--sans); font-size: 8.5pt; font-weight: 600;
  line-height: 13pt; text-align: center; vertical-align: 1pt; }
"""

# The trail's own rules, the same on paper as on the screen: five columns at their shares of the width,
# each taking the room its longest word needs where its share falls short, so a word wraps whole and
# never through a letter (17 October, later), every row of every block on the same five columns as
# subgrids of `.tr-wide`, and the lines between them drawn from each row, a stub from a node to the
# middle of the gap and an upright piece there, drawn in the cell of the column after it, so they meet at
# any width. Where the columns need more than the window, the trail scrolls sideways in its own box
# under the GET's title on the screen, and paper, A4 landscape, holds them. A browser with no subgrid
# keeps each row's own five shares, as before.
TRAIL = """
.tr-wide { display: grid; column-gap: var(--g); overflow-x: auto;
  grid-template-columns: minmax(min-content, 31fr) minmax(min-content, 21fr) minmax(min-content, 21fr) minmax(min-content, 15fr) minmax(min-content, 12fr); }
.tr-cols, .tr-block, .tr-rows, .tr-row { grid-column: 1 / -1; display: grid; column-gap: var(--g);
  grid-template-columns: minmax(0, 31fr) minmax(0, 21fr) minmax(0, 21fr) minmax(0, 15fr) minmax(0, 12fr);
  grid-template-columns: subgrid; }
.tr-who, .tr-none { grid-column: 1 / -1; }
/* on a narrow screen the five columns keep about 720px together, at their shares, as the GET table keeps its
   width, by the heads under the GET's title, so the trail scrolls in its box where its columns squeezed to a word
   or two a line at 360 (17 October, later). Paper, which hides those heads, holds them as before. */
.tr-wide > .tr-cols > :nth-child(1) { min-width: 198px; }
.tr-wide > .tr-cols > :nth-child(2), .tr-wide > .tr-cols > :nth-child(3) { min-width: 134px; }
.tr-wide > .tr-cols > :nth-child(4) { min-width: 96px; }
.tr-wide > .tr-cols > :nth-child(5) { min-width: 77px; }
/* a thematic analysis project's trail, four columns with no PET's (tagaps, 1 November 2026) */
.tr-wide.tr-four { grid-template-columns: minmax(min-content, 31fr) minmax(min-content, 21fr) minmax(min-content, 21fr) minmax(min-content, 12fr); }
.tr-four .tr-cols, .tr-four .tr-block, .tr-four .tr-rows, .tr-four .tr-row {
  grid-template-columns: minmax(0, 31fr) minmax(0, 21fr) minmax(0, 21fr) minmax(0, 12fr); grid-template-columns: subgrid; }
.tr-wide.tr-four > .tr-cols > :nth-child(4) { min-width: 77px; }
.tr-get { --g: 20px; --c: 11px; --rp: 6px; }
.tr-cols { margin: 6pt 0 2pt; font-size: 7pt; letter-spacing: .08em; text-transform: uppercase; font-weight: 600; color: var(--ink-faint); }
.tr-cols.tr-again { display: none; margin: 0 0 4pt; }
.tr-block { break-inside: avoid; page-break-inside: avoid; padding: 6pt 0 4pt; border-top: 1px solid var(--rule); }
.tr-who { margin: 0 0 5pt; font-family: var(--serif); font-weight: normal; font-size: 12pt; }
.tr-who .tr-mark { margin-left: 8pt; }
.tr-none { margin: 0 0 4pt; font-size: 9pt; color: var(--ink-faint); }
.tr-row { position: relative; padding-bottom: var(--rp); }
.tr-c { position: relative; min-width: 0; }
.tr-c.node { padding: 3px 7px 4px; border-radius: 4px; box-shadow: inset 0 0 0 1px color-mix(in srgb, var(--hue) 45%, transparent);
  background: color-mix(in srgb, var(--hue) 5%, var(--paper)); font-size: 9pt; line-height: 1.35; overflow-wrap: break-word; }
.tr-c.in::after { content: ""; position: absolute; top: var(--c); right: calc(var(--g) / -2); width: calc(var(--g) / 2);
  border-top: 1px solid var(--hue); }
.tr-c.out::before { content: ""; position: absolute; top: var(--c); left: calc(var(--g) / -2); width: calc(var(--g) / 2);
  border-top: 1px solid var(--hue); }
.tr-c.pass::after { content: ""; position: absolute; top: var(--c); left: calc(var(--g) / -2); right: calc(var(--g) / -2);
  border-top: 1px solid var(--hue); }
.tr-c.dashed::after { border-top-style: dashed; }
.tr-sp { position: absolute; width: 0; left: calc(var(--g) / -2); border-left: 1px solid var(--hue); }
.tr-sp.down { top: var(--c); bottom: calc(-1 * var(--rp)); }
.tr-sp.full { top: 0; bottom: calc(-1 * var(--rp)); }
.tr-sp.up { top: 0; height: var(--c); }
.tr-kind, .tr-where, .tr-within, .tr-key, .tr-mark { display: block; font-family: var(--sans); font-size: 7.5pt; color: var(--ink-faint); }
.tr-kind { font-weight: 600; letter-spacing: .04em; }
.tr-title { font-family: var(--serif); font-size: 10pt; }
.tr-c.get .tr-title { color: var(--ink); }
.tr-st { display: block; font-family: var(--serif); font-size: 9.5pt; }
.tr-st + .tr-st { margin-top: 3px; }
.tr-q { font-family: var(--serif); font-style: italic; font-size: 9.5pt; }
.tr-key { color: var(--ink-soft); font-weight: 600; }
.tr-mark { color: var(--amber); }
.tr-said { display: block; font-family: var(--serif); font-size: 9pt; color: var(--ink-soft); }
.tr-said b { color: var(--ink); font-weight: 600; }
.tr-unread { color: var(--ink-faint); font-family: var(--sans); }
.tr-c.pn { box-shadow: none; outline: 1px dashed var(--rule-firm); outline-offset: -1px; background: var(--paper); }
.tr-c.playable { cursor: pointer; }
.tr-c.playable.playing { box-shadow: inset 0 0 0 2px var(--hue); }
@media print {
  .tr-wide { overflow: visible; }
  .tr-wide > .tr-cols { display: none; }
  .tr-cols.tr-again { display: grid; }
}
"""

SCRIPT = """
document.getElementById('print').onclick = () => window.print();
const player = document.createElement('audio');
let playing = null;
document.addEventListener('click', (e) => {
  const turn = e.target.closest('[data-audio]');
  if (!turn) return;
  if (playing === turn && !player.paused) { player.pause(); turn.classList.remove('playing'); return; }
  if (playing) playing.classList.remove('playing');
  if (player.getAttribute('src') !== turn.dataset.audio) player.src = turn.dataset.audio;
  const go = () => { player.currentTime = Number(turn.dataset.at) || 0; player.play().catch(() => {}); };
  if (player.readyState >= 1) go(); else player.addEventListener('loadedmetadata', go, { once: true });
  playing = turn;
  turn.classList.add('playing');
});
if (AUTO) {
  const ready = document.fonts && document.fonts.ready ? document.fonts.ready : Promise.resolve();
  ready.then(() => setTimeout(() => window.print(), 150));
}
"""


def tint_of(board: dict) -> dict:
    """Each group's tint class, worked out as the canvas works it out."""
    return {gid: f"hue-{hue}" + (f" step-{step}" if step else "") for gid, (hue, step) in tp.tints(board.get("groups") or []).items()}


def study_parts(root: Path, books: list[dict], board: str | None, when: str) -> dict:
    """The GETs as the screen would show them, read afresh and in memory, and nothing written: the
    file with every case not yet in taken in, the board, the study's cases, the minimum and the
    cases changed since they came in."""
    data, cases, _disk, _taken = gt.assemble(root, books, when)
    shown = (th.find_version(data, board) if board else None)
    if board and shown is None:
        raise WorkbookError(i18n.t("page_print.gets.board_gone"))
    shown = shown or th.current_version(data)
    study = gt.study_of(data, [e["case"] for e in cases])
    inside = [e["case"] for e in cases if study[e["case"]]["in"]]
    settings = gt.settings_of(data)
    minimum, is_band = gt.minimum_of(settings, len(inside))
    changed = {e["case"] for e in cases if e["status"] == "changed"}
    return {"data": data, "board": shown, "inside": inside, "minimum": minimum, "band": is_band,
            "changed": changed, "books": {e["case"]: e["workbook"] for e in cases},
            "looks": gt.looks([e["case"] for e in cases], data)}


def gets_table(parts: dict) -> list[dict]:
    """The table of the board, each row saying whether its case changed since it came in, with its
    case's colour and badge as the GETs board gives them."""
    out = gt.table(parts["data"], parts["board"], parts["inside"])
    looks = parts.get("looks") or {}
    for g in out:
        for row in g["rows"]:
            row["changed"] = row["case"] in parts["changed"]
            look = looks.get(row["case"])
            if look:
                row.update(colour=look["colour"], badge=look["badge"])
    return out


def header(project: dict, parts: dict, what: str, selected: bool, notes: bool, now: datetime | None,
           sending: bool = False) -> list[str]:
    """The page's head, the table of PETs' own (Adam, 1 November 2026: "it should be consistent across the PETs
    and GETs tables"): the document's name as the title, where the table of PETs has the participant, "Table of
    Group Experiential Themes", the audit trail's or the full set's own name likewise, with PROJECT and RESEARCH
    QUESTION to its right, and under it the board's note as the table of PETs has its own and any case not
    complete, with no PETs or changed since it came in. The minimum, Smith's band and what each row shows are
    left off the page ("I don't know what that's doing, just get rid of that"), the settings staying where they
    are set."""
    said = head_of(project, parts, what)
    out = ['<header class="head">', '<div class="top">', '<div class="titles">', f'<h1>{esc(said["title"])}</h1>', "</div>",
           *tp.about_block(said["project"], said["question"]), "</div>"]
    if said["note"]:
        out.append(f'<p class="note">{esc(said["note"])}</p>')
    out += [f'<p class="waiting">{esc(line)}</p>' for line in said["waiting"]]
    out.append("</header>")
    return out


def head_of(project: dict, parts: dict, what: str) -> dict:
    """What the page's head says (see `header`), for the HTML page and the Typst data alike: the document's name,
    the project, the research question, the board's note, and a line for each state a participant is waiting in."""
    board = parts["board"]
    trail = i18n.t("page_print.gets.trail")
    title = {"table": i18n.t("page_print.gets.table_name"), "trail": trail, "all": i18n.t("page_print.gets.all")}[what]
    # a project of two or more timepoints prints its LGETs, and a participant's LPETs their own (21 October)
    if gt.in_lgets():
        title = {"table": i18n.t("page_print.gets.lget_table_name"), "trail": trail,
                 "all": i18n.t("page_print.gets.lgets_all")}[what]
    elif gt.in_lpets():
        title = {"table": i18n.t("page_print.gets.lpet_table_name"), "trail": trail,
                 "all": i18n.t("page_print.gets.lpets_all")}[what]
    asked = " ".join(str(project.get("research_question") or "").split())
    # a participant not complete, with no PETs yet or changed since it came in, said under the head, since it
    # matters to the analysis, and only when there is one (Adam, 1 November: only the minimum and what each row
    # shows went)
    held = parts["data"].get("cases") or {}
    late = [c for c in parts["inside"] if (held.get(c) or {}).get("state") == "in" and not (held.get(c) or {}).get("complete")]
    none = [c for c in parts["inside"] if (held.get(c) or {}).get("state") == "none"]
    changed = [c for c in parts["inside"] if c in parts["changed"]]
    # a thematic analysis project's participants have no PETs, complete or not (tagaps)
    if ta():
        late, none = [], []
    waiting = [i18n.t("page_print.gets.waiting", state=said, names=gt.said_list([gt.who(c) for c in names]))
               for said, names in ((gt.NOT_COMPLETE, late), (gt.NO_PETS, none), (gt.CHANGED, changed)) if names]
    return {"title": title, "project": " ".join(str(project.get("name") or "").split()), "question": asked,
            "note": str(board.get("note") or "").strip(), "waiting": waiting}


def walked(root: Path, books: list[dict], project: dict, board: str | None, what: str, get: str | None,
           sending: bool, descriptions: bool, now: datetime | None, people: dict | None = None) -> dict:
    """One walk of a board of the GETs for a print, which the HTML page (`page`) and the Typst data (`typst_data`)
    both read, so the two cannot disagree about what is on it: what is printed, the study's parts, the table, the
    GETs whose trails are printed, the cases' copies, the words of the trails' turns, the part's name, the
    page's title and, with `people` (Participants table ticked, every participant's set), the participants
    table's rows, every participant of the study in order (`participants.table_rows`), and none for a
    participant's LPETs, whose columns are their timepoints. A board or a GET the file no longer holds is
    refused."""
    what = what if what in WHATS else "table"
    parts = study_parts(root, books, board, th.now_iso())
    table_ = gets_table(parts)
    if not descriptions:
        table_ = [{k: v for k, v in g.items() if k != th.DESCRIPTION} for g in table_]
    if get and not any(g["id"] == get for g in table_):
        raise WorkbookError(i18n.t("page_print.gets.no_get"))
    trails = [g for g in table_ if not get or g["id"] == get]
    recs = parts["data"].get("cases") or {}
    words = read_turns(trails, recs, parts["books"]) if what in ("trail", "all") else {}
    gets_word = i18n.t("page_print.gets.project")
    name = project.get("name") or gets_word
    kind = {"table": i18n.t("page_print.gets.table"), "trail": i18n.t("page_print.gets.trail"), "all": gets_word}[what]
    title = (i18n.t("page_print.gets.title_sending", name=name, what=kind) if sending
             else i18n.t("page_print.gets.title", name=name, board=parts["board"].get("name") or th.FIRST_NAME, what=kind))
    rows = None
    if people is not None and not gt.in_lpets():
        rows = people_mod.table_rows(people, parts["inside"], gt.who)
    return {"what": what, "parts": parts, "table": table_, "trails": trails, "recs": recs, "words": words,
            "kind": kind, "title": title, "people": rows}


def foot_of(project: dict, parts: dict, kind: str, sending: bool, researcher: str, confidential: bool,
            now: datetime | None) -> tuple[str, str, list[str], int]:
    """The foot as the table of PETs has it (Adam, 31 October): the project and the part printed, the researcher and
    Confidential, and the page, where the screen's foot named the GETs file. Its left whole, its middle, and the left
    in its pieces with the one that may be shortened, the project in the participant's place on the GETs' foot."""
    named = "" if sending else (parts["board"].get("name") or th.FIRST_NAME)
    foot, middle = tp.foot_parts(project.get("name") or "", "", kind, researcher, confidential, board=named,
                                 day=tp.when_printed(now))
    pieces, fit = tp.foot_pieces(project.get("name") or "", "", kind, board=named, cut_case=True)
    return foot, middle, pieces, fit


def page(root: Path, books: list[dict], project: dict, board: str | None = None, what: str = "table",
         detail: str = "full", notes: bool = False, get: str | None = None, auto: bool = True, audio=None,
         now: datetime | None = None, sending: bool = False, descriptions: bool = True, researcher: str = "",
         confidential: bool = True, people: dict | None = None) -> str:
    """The GET table, the audit trail or the full set of a board of the GETs, the current one when
    `board` names none, as one HTML page. `get` keeps the trail to one GET. `audio` gives a turn the
    address of its recording, or None when its case has none. A board the file does not hold is
    refused. `auto` opens the print dialog once the fonts have loaded. With `sending`, For sending
    ticked, no board is named on the page or in its title, which names the PDF, "Study - GET table"
    in place of "Study - Board 2 - GET table", and the foot is kept (Adam, 19 October). Each GET's and
    PET's description sits under its title only with `descriptions`, on by default (21 October). With
    `people`, Participants table ticked (pbioexport, 11 November 2026), the participants table comes first,
    after a full set's contents, and the part after it from a new page under its own heading."""
    w = walked(root, books, project, board, what, get, sending, descriptions, now, people)
    what, parts, table_, trails, recs = w["what"], w["parts"], w["table"], w["trails"], w["recs"]
    selected = detail == "selected"
    tints = tint_of(parts["board"])
    total, minimum = len(parts["inside"]), parts["minimum"]
    body: list[str] = []
    pet_tables, get_table = esc(i18n.t("page_print.gets.pet_tables")), esc(i18n.t("page_print.gets.table"))
    audit, none = esc(i18n.t("page_print.gets.trail")), esc(i18n.t("page_print.gets.none"))
    rows = w["people"]
    if what == "all":
        # a thematic analysis project's full set has no PET tables, its participants having none (tagaps)
        pets = "" if ta() else (f'<li><a href="#pets">{pet_tables}</a><ol>'
                                + "".join(f'<li><a href="#pets-{esc(gt.who(c))}">{esc(gt.who(c))}</a></li>' for c in parts["inside"])
                                + "</ol></li>")
        listed = (f'<li><a href="#participants">{esc(i18n.t("page_print.people.heading"))}</a></li>'
                  if rows is not None else "")
        body.append(f'<section class="contents"><h2>{esc(i18n.t("page_print.gets.contents"))}</h2><ol>'
                    + listed + pets + f'<li><a href="#table">{get_table}</a></li><li><a href="#trail">{audit}</a><ol>'
                    + "".join(f'<li><a href="#trail-{esc(g["id"])}">{esc(g["label"])}</a></li>' for g in table_)
                    + "</ol></li></ol></section>")
    # the participants table first, after a full set's contents (pbioexport), and then the part printed after it
    # from a new page under its own heading, as a full set's parts are
    if rows is not None:
        body.append(people_section(rows))
    headed, first = what == "all" or rows is not None, rows is None
    if what == "all" and not ta():
        labels = th.pet_labels_of(project.get("pet_labels"))
        body.append(f'<section class="part{" first" if first else ""} pets" id="pets"><h2>{pet_tables}</h2>'
                    + "".join(pet_section(c, recs.get(c) or {}, selected, labels, sending, descriptions)
                              for c in parts["inside"])
                    + "</section>")
    if what in ("table", "all"):
        tables = "".join(table_section(g, tints.get(g["id"], "hue-grey"), total, minimum, notes, selected) for g in table_)
        if not table_:
            tables = f'<p class="none">{none}</p>'
        body.append(f'<section class="part{" first" if what == "table" and first else ""}" id="table">'
                    + (f"<h2>{get_table}</h2>" if headed else "") + tables + "</section>")
    if what in ("trail", "all"):
        words = w["words"]
        sections = "".join(trail_section(g, tints.get(g["id"], "hue-grey"), recs, words, total, minimum, notes,
                                         selected, audio) for g in trails)
        if not trails:
            sections = f'<p class="none">{none}</p>'
        body.append(f'<section class="part{" first" if what == "trail" and first else ""}" id="trail">'
                    + (f"<h2>{audit}</h2>" if headed else "") + sections + "</section>")
    title = w["title"]
    foot, middle, pieces, fit = foot_of(project, parts, w["kind"], sending, researcher, confidential, now)
    style =f"{tp.HEAD}{tp.ROW}{PAGE}{tp.scoped(tp.BLOCKS, '.pets')}{STYLE}{CASES}{TRAIL}{tp.TAIL}"
    return "\n".join([
        "<!doctype html>", f'<html lang="{tp.page_lang()}">', "<head>", '<meta charset="utf-8">',
        '<meta name="viewport" content="width=device-width, initial-scale=1">',
        f"<title>{esc(title)}</title>", f'<link rel="stylesheet" href="{FONTS_CSS}">',
        f"<style>{style}{tp.page_foot(pieces, middle, numbered=True, fit=fit)}</style>", "</head>", "<body>",
        f'<div class="controls noprint"><button type="button" id="print">{esc(i18n.t("page_print.print"))}</button></div>',
        *header(project, parts, what, selected, notes, now, sending), "<main>", *body, "</main>",
        f"<footer>{esc(foot + ('  ' + chr(183) + '  ' + middle if middle else ''))}</footer>", tp.foot_fit(pieces, fit, middle, style),
        f"<script>const AUTO = {'true' if auto else 'false'};{SCRIPT}</script>", "</body>", "</html>", ""])


def trail_view(root: Path, books: list[dict], board: str | None, get: str, audio=None) -> dict:
    """One GET's audit trail for the GETs screen, every item and his participant notes with it,
    since the screen is his own: the trail's HTML, without the head the screen draws itself, and
    the GET's title, tint, count and minimum. Reads only, and writes nothing."""
    parts = study_parts(root, books, board, th.now_iso())
    table_ = gets_table(parts)
    g = next((x for x in table_ if x["id"] == get), None)
    if g is None:
        raise WorkbookError(i18n.t("page_print.gets.no_get"))
    recs = parts["data"].get("cases") or {}
    words = read_turns([g], recs, parts["books"])
    tint = tint_of(parts["board"]).get(get, "hue-grey")
    total, minimum = len(parts["inside"]), parts["minimum"]
    return {"html": trail_section(g, tint, recs, words, total, minimum, True, False, audio, head=False),
            "get": get, "label": g["label"], "note": g["note"], "tint": tint, "count": g["count"], "total": total,
            "minimum": minimum, "under": g["count"] < minimum}


# ------------------------------------------------------------------ the Typst data

def hues_of(board: dict) -> dict:
    """Each group's tint as the Typst templates take it, its base colour and its step, worked out as `tint_of`."""
    return {gid: {"hue": tp.HUES[hue] if hue != "grey" else tp.GREY, "step": step}
            for gid, (hue, step) in tp.tints(board.get("groups") or []).items()}


def count_data(get: dict, total: int, minimum: int) -> dict:
    """A GET's count as `badge` says it: "3 of 5", and under the minimum dashed with its line."""
    under = get["count"] < minimum
    return {"short": i18n.t("page_print.gets.count_short", count=get["count"], total=total), "under": under,
            "said": i18n.t("page_print.gets.under_minimum", minimum=minimum) if under else ""}


def who_data(row: dict, marks: list[str]) -> dict:
    """A participant as a row or a block names them: the pseudonym, the badge in the case's colour, the marks."""
    colour = row.get("colour")
    return {"who": row["who"], "badge": row.get("badge") or "" if colour is not None else "",
            "colour": CASE_COLOURS[int(colour) % len(CASE_COLOURS)] if colour is not None else "", "marks": marks}


def item_data(it: dict) -> dict:
    """What of a case sits under a GET, as `item_html` sets it."""
    within = i18n.t("page_print.gets.in_pets", pets=", ".join(it["within"])) if it.get("within") else ""
    if it["kind"] == "pn":
        return {"kind": "pn", "kind_said": i18n.t("page_print.kind.participant_note"), "text": it["text"], "mine": gt.NOT_FROM}
    if it["kind"] in ("pet", "sub"):
        return {"kind": "pet", "kind_said": i18n.t("page_print.kind.pet") if it["kind"] == "pet" else i18n.t("page_print.kind.sub_theme"),
                "title": it["title"], "n": i18n.t("page_print.gets.statements", n=it["statements"]), "within": within,
                "gone": i18n.t("page_print.gets.not_in_pets") if it["gone"] else ""}
    return {"kind": "es", "kind_said": i18n.t("page_print.kind.statement"), "text": it["text"],
            "time": "" if it["gone"] else it["time"], "sheet": "" if it["gone"] else it["sheet"], "within": within,
            "gone": i18n.t("page_print.gets.not_in_workbook") if it["gone"] else "",
            "quotes": [tp.quoted(q["text"]) for q in it["quotes"]], "notes": list(it["notes"])}


def quote_data(q: dict, bold=None) -> dict:
    """A row's key quote as the Typst table takes it: its words in their quotation marks, and with his bold in it
    `words`, its runs, each with whether it is bold, as `quote_html` sets them (lpetmarks), else none."""
    runs = gt.quote_bold(q["text"], bold)
    return {"text": tp.quoted(q["text"]), "words": [[t, on] for t, on in runs] if any(on for _t, on in runs) else None}


def table_data(get: dict, hue: dict, total: int, minimum: int, notes: bool, selected: bool) -> dict:
    """One GET of the table, as `table_section` sets it."""
    heads = ([i18n.t("page_print.gets.participant")] + ([] if selected else [i18n.t("page_print.gets.under_this_get")])
             + [i18n.t("page_print.kind.quote"), i18n.t("page_print.gets.note")])
    rows = []
    for row in get["rows"]:
        bare = row["none"] and not row["counted"] and not ta()
        items = [item_data(it) for it in row["items"] if (not selected or it["kind"] == "pn") and (notes or it["kind"] != "pn")]
        q = row["quote"] if row["counted"] else None
        rows.append(dict(who_data(row, row_marks(row, bare)), empty=not row["counted"], items=items,
                         nothing="" if row["counted"] else (gt.NOTHING_NO_PETS if bare else gt.NOTHING),
                         quote=dict(quote_data(q, row.get("bold")), time=q["time"], sheet=q["sheet"]) if q else None,
                         no_quote=i18n.t("page_print.gets.no_quote") if row["counted"] and not q else "",
                         note=row["note"] or ""))
    return dict({"id": get["id"], "label": get["label"], "desc": get.get(th.DESCRIPTION) or "", "note": get["note"] or "",
                 "count": count_data(get, total, minimum), "heads": heads, "rows": rows}, **hue)


def cell_data(cell: dict | None) -> dict | None:
    """A cell of the trail, as `cell_html` sets it, its links to its parent and its children."""
    if cell is None:
        return None
    kind = cell["kind"]
    if kind == "pass":
        return {"kind": "pass", "dashed": bool(cell.get("dashed"))}
    out = {"kind": kind, "in": bool(cell.get("linked_in")), "out": bool(cell.get("linked_out")),
           "dashed": bool(cell.get("dashed") and cell.get("linked_in"))}
    if kind == "get":
        return dict(out, title=cell["label"])
    if kind in ("pet", "sub"):
        return dict(out, kind="pet", kind_said=i18n.t("page_print.kind.pet") if kind == "pet" else i18n.t("page_print.kind.sub_theme"),
                    title=cell["title"], within=i18n.t("page_print.trail.in_pets", pets=", ".join(cell["within"])) if cell.get("within") else "",
                    gone=i18n.t("page_print.trail.not_in_pets") if cell.get("gone") else "")
    if kind == "pn":
        return dict(out, kind_said=i18n.t("page_print.kind.participant_note"), text=cell["text"], mark=gt.NOT_FROM)
    if kind == "es":
        first = cell["statements"][0]
        return dict(out, statements=[str(s.get("text") or "") for s in cell["statements"]],
                    where=stamp(first.get("sheet") or "", first.get("time") or ""),
                    gone=i18n.t("page_print.trail.not_in_workbook") if cell.get("gone") else "")
    if kind == "quote":
        return dict(out, text=tp.quoted(cell["text"]), key=i18n.t("page_print.kind.quote") if cell.get("key") else "")
    words = cell.get("words")
    return dict(out, where=stamp(cell.get("sheet") or "", cell.get("time") or ""),
                words=[[t, bool(b)] for t, b in words] if words is not None else None,
                unread=i18n.t("page_print.trail.unread") if words is None else "")


def trail_data(get: dict, hue: dict, recs: dict, words: dict, total: int, minimum: int, notes: bool,
               selected: bool) -> dict:
    """One GET's audit trail, as `trail_section` sets it: a block per participant, each row of its paths in the
    columns the print shows with the upright piece of line each column's gap carries."""
    four = four_of(get)
    cols = shown(four)
    named = (i18n.t("page_print.kind.passage"), i18n.t("page_print.kind.quote"), i18n.t("page_print.kind.statement"),
             i18n.t("page_print.kind.pet"), i18n.t("page_print.kind.get"))
    blocks = []
    for row in get["rows"]:
        nodes = block_nodes(row, recs.get(row["case"]) or {}, words.get(row["case"], {}), notes, selected)
        bare = row["none"] and not row["counted"] and not ta()
        none = ""
        if not row["counted"]:
            none = gt.NOTHING_NO_PETS if bare else gt.NOTHING
        elif selected and not (row.get("quote") and nodes):
            none = i18n.t("page_print.gets.no_quote")
        rows = [{"cells": [cell_data(r["cells"][c]) for c in cols], "spines": [r["spines"].get(c) or "" for c in cols]}
                for r in (flatten(get, nodes) if nodes else [])]
        blocks.append(dict(who_data(row, row_marks(row, bare)), none=none, rows=rows))
    return dict({"id": get["id"], "label": get["label"], "desc": get.get(th.DESCRIPTION) or "", "note": get["note"] or "",
                 "count": count_data(get, total, minimum), "four": four, "heads": [named[c] for c in cols],
                 "blocks": blocks}, **hue)


def typst_data(root: Path, books: list[dict], project: dict, board: str | None = None, what: str = "table",
               detail: str = "full", notes: bool = False, get: str | None = None, now: datetime | None = None,
               sending: bool = False, descriptions: bool = True, researcher: str = "", confidential: bool = True,
               people: dict | None = None) -> dict:
    """The GET table, the audit trail or both of a board of the GETs as the Typst templates take them (TEMPLATE),
    from the same walk as the HTML page (`walked`), with the same arguments as `page`, every word the page prints
    in the run's language: the head, the foot in its pieces, and each GET's part. `all` gives the table and the
    trail, a full set's PET tables being the table of PETs' own. With `people` (Participants table ticked) the
    participants table's heads and rows under `people`, which the templates set first (pbioexport). Reads only,
    and writes nothing."""
    w = walked(root, books, project, board, what, get, sending, descriptions, now, people)
    what, parts = w["what"], w["parts"]
    selected = detail == "selected"
    hues = hues_of(parts["board"])
    grey = {"hue": tp.GREY, "step": 0}
    total, minimum = len(parts["inside"]), parts["minimum"]
    _foot, middle, pieces, fit = foot_of(project, parts, w["kind"], sending, researcher, confidential, now)
    lang = tp.page_lang()
    page_of = i18n.t("page_print.page_of", page="\x00", pages="\x01")
    before, rest = page_of.split("\x00", 1) if "\x00" in page_of else (page_of, "")
    between, after = rest.split("\x01", 1) if "\x01" in rest else (rest, "")
    out = {"what": what, "title": w["title"], "lang": lang.split("-")[0], "region": (lang.split("-") + [""])[1],
           "head": dict(head_of(project, parts, what), labels={"project": i18n.t("page_print.project"),
                                                                "question": i18n.t("page_print.research_question")}),
           "foot": {"left": [p for p in pieces if p], "fit": fit, "middle": middle, "page": [before, between, after]},
           "none": i18n.t("page_print.gets.none"), "selected": selected,
           "names": {"table": i18n.t("page_print.gets.table"), "trail": i18n.t("page_print.gets.trail"),
                     "people": i18n.t("page_print.people.heading")}}
    if w["people"] is not None:
        out["people"] = {"heads": people_mod.table_heads(), "rows": w["people"]}
    if what in ("table", "all"):
        out["table"] = [table_data(g, hues.get(g["id"], grey), total, minimum, notes, selected) for g in w["table"]]
    if what in ("trail", "all"):
        out["trail"] = [trail_data(g, hues.get(g["id"], grey), w["recs"], w["words"], total, minimum, notes, selected)
                        for g in w["trails"]]
    if what == "all":
        # the full set as `page` orders it: the contents, each participant's table of PETs (none in a thematic
        # analysis project, whose participants have none), the GET table and the trail, each part from a new page
        cases = [] if ta() else parts["inside"]
        labels = th.pet_labels_of(project.get("pet_labels"))
        out["names"].update(contents=i18n.t("page_print.gets.contents"), pets=i18n.t("page_print.gets.pet_tables"))
        out["contents"] = {"cases": [gt.who(c) for c in cases], "gets": [g["label"] for g in w["table"]],
                           "pets": not ta()}
        out["pets"] = [pet_data(c, w["recs"].get(c) or {}, selected, labels, sending, descriptions) for c in cases]
    return out
