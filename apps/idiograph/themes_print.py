#!/usr/bin/env python3
"""The print view of a board: one HTML page, rendered by the server from the board, for the
browser to print or save as PDF on landscape A4, as the book's tables are set, the PET document he
sends his supervisor. It is the table of Personal Experiential Themes that Smith, Flowers and Larkin
(2022) set out in Box 5.6, their table of PETs for Elisa, the Word document's content typeset in the
app's faces. The Word document stays portrait, a statement with its quote under it.

The page opens with the participant as its main heading, "P9 Wren", the dash of the case key dropped,
or the name alone for a case with no number, the table's name, Table of Personal Experiential Themes,
smaller beside it on the same line (Adam, 20 October: three printed tables each opening on the same
title hid what differed), and the project and the research question in a block to their right, each
after its label, the labels in a column of their own (Adam, 31 October). No rule under the head, as
PET A's shaded bar parts it from the table, and nothing at its top right: the date and the board are
in the foot. A case printed after another is headed by its own participant.
With For sending ticked the board stays out of the foot and the page's title, which names the PDF the
browser saves, is the case alone, "P9 - Wren", where it is "P9 - Wren - Board 3 - PETs" without it
(Adam, 19 October). The PETs marked complete are not said on the page (Adam, 31 October). The
board's note stays out unless asked for with `note=1`, and then sits under the head. There is no list
of the PETs at the head.

Then the PETs in the order the canvas reads them, each lettered "A.", "B." as Box 5.6 letters them,
with its title in capitals, a quiet rule in its tint down its side and a pale band of the tint behind
its title, and its note in italics under it when it has one. A sub-theme sits under its PET in bold,
"A1. Mornings", and a group, a label inside a sub-theme, in bold italic, "A1.1 Early light", each set
in a little further and a little smaller. A group inside a group, "A1.1.1", takes the fifth step, and
any deeper stays at that step's size and indent, as the Word document's headings stop at Heading 5.
A project set to numbers has "PET 1.", "PET 1a. Mornings" and "1a.1 Early light" in their place.
The headings and the notes run across the full width of the page. Under each heading come its
statements in the order the canvas reads them, a label inside it taking its place among the cards
where its frame's top sits, each a row of two columns about equal, as a long line across a landscape
page is hard to read. On the left the statement in the serif, followed by where it is, "(Initial,
12:04)", in a smaller, quieter face, and on the right its own quote in italics in single curly
quotation marks, never doubled when the workbook keeps marks round it, the quotes' column the same
width all down the page. A statement with no quote of its own leaves the right empty, and no picked
quotes are listed, since every statement carries its own. The labels and the order come from
`themes`, where the Word document takes them, so the two never disagree. Not placed and Binned
experiential statements, the bin, come at the end with their counts, "Not placed (18)", each only when it holds anything and only
when its tick is on, their statements in the same rows, a discard with the reason an AI proposal
gave under its statement. Both ticks are off on a new install, so the table holds the PETs alone. The
PETs flow on from page to page, a title kept with its first row and a row never split across a page, so a
statement never parts from its quote, and nothing spills onto a page of its own after the last row (Adam,
31 October). A small line at the foot of every page names the participant, the table and the page, "Page 2
of 4", where until 31 October it named the themes file.

The workbook is only read, the themes file too, and nothing is written. The page carries four
controls, three ticks, Board note, Include not placed and Include statements set aside,
each of which draws the page again, the last two saving his choice in the settings for the next
export, and Print, and opens the
print dialog itself once its fonts have loaded, so Save as PDF in the macOS dialog is one step.

The GETs print sets out each case's PETs as they came into the GETs in this same table, through
`block_html` and the table's own rules, `BLOCKS`, set under the part that holds them by `scoped`.
"""
from __future__ import annotations

import html
import json
import re
from datetime import datetime
from pathlib import Path

import boot
import formats
import i18n
import themes as th
# a quote without the marks the workbook keeps round it, as the PET draft and the CSV take it too
from themes import MARKS, bare
from workbook import WorkbookError

# The tints the canvas draws the themes in, as paper shows them: eight for the top-level themes,
# each its own, a lighter step of its theme's for a sub-theme, and grey past the eight.
HUES = ("#3E7C8A", "#5B6FA8", "#6E8B3D", "#8A5A8C", "#8F7A1F", "#A4566A", "#4F8A6B", "#6B6B80")
GREY = "#8C8C8C"
# the depth the indent and type steps stop at, a group inside a group, the Word document's Heading 5
DEEP = 3
# The page's words are in static/i18n/en/page_print.json (i18npage, 28 October 2026): a board the case's file no
# longer holds said in the app's own words, page_print.pets.board_gone, and the book's name for the table, a smaller
# heading under the participant, who heads the page, page_print.pets.table_name. The Word document takes the
# table's name as TITLE, read as this module loads, until its own words move
TITLE = i18n.t("page_print.pets.table_name")
# the heading of the bin's part at the end of the print view, the Word document and the PET draft, with its
# count, in the words of its tick (Adam, 19 October)
BINNED = th.BINNED_HEADING

esc = lambda text: html.escape(str(text or ""), quote=True)


def tints(groups: list[dict]) -> dict[str, tuple]:
    """Each group's tint and step, the way the canvas works them out: a top-level theme takes the
    tint its number gives it, g1 the first, while no theme before it holds that one, and the next
    free one when one does, and grey past the eight. A sub-theme takes its theme's a step lighter."""
    by_id = {g["id"]: g for g in groups}
    parents = th.parents_of(groups)
    out: dict[str, tuple] = {}
    used: set[int] = set()
    for g in groups:
        if g["id"] in parents:
            continue
        number = re.search(r"(\d+)$", str(g["id"]))
        want = (int(number.group(1)) + len(HUES) - 1) % len(HUES) if number else 0
        hue = next(((want + i) % len(HUES) for i in range(len(HUES)) if (want + i) % len(HUES) not in used), "grey")
        if hue != "grey":
            used.add(hue)
        out[g["id"]] = (hue, 0)

    def walk(gid: str, hue, step: int, seen: frozenset) -> None:
        for m in by_id[gid]["members"]:
            if m in by_id and m not in seen:
                out[m] = (hue, min(step, 2))
                walk(m, hue, step + 1, seen | {m})

    for gid in list(out):
        walk(gid, out[gid][0], 1, frozenset({gid}))
    for g in groups:
        out.setdefault(g["id"], ("grey", 0))
    return out


def case_title(case: str) -> str:
    """The case as the page's main heading names it, "P9 Wren" for `P9 - Wren`, the dash of the case key
    dropped. A name with no number, the demo's Juno, comes back as it is."""
    return re.sub(r"^(P\d+)\s*-\s*", r"\1 ", " ".join(str(case or "").split()))


# ------------------------------------------------------------- the table

def reference(s: dict) -> str:
    """Where a statement is, in brackets as the Word document has it, "(Initial, 12:04)", and
    "(Initial, 12:04, no longer in the workbook)" for a line gone from the workbook."""
    where = th.where_said(s)
    return f"({where})" if where else ""


def quoted(quote) -> str:
    """A quote as every print view sets it, the table of PETs, the GETs table and the trail alike, in single curly
    quotation marks as the book's tables and the Word document set it, once, whatever marks the workbook keeps round
    it, where the GETs table and the trail set straight double ones (17 October, later)."""
    return f"\u2018{bare(quote)}\u2019"


def statement_html(s: dict, reasons: bool = False) -> str:
    """A statement as a row of the table, two columns side by side: on the left its words in the
    serif followed by its reference in a smaller, quieter face, and on the right its own quote in
    italics in single curly quotation marks, the right left empty when it has none. A page never
    splits the row. With `reasons` the reason an AI proposal gave for a discard follows under the
    statement, on the left."""
    ref = reference(s)
    out = [f'<div class="item"><p class="st">{esc(s["text"])}'
           + (f' <span class="ref">{esc(ref)}</span>' if ref else "") + "</p>"]
    said = bare(s.get("quote"))
    if said:
        out.append(f'<p class="kq">{esc(quoted(said))}</p>')
    if reasons and s.get("reason"):
        out.append(f'<p class="why">{esc(s["reason"])}</p>')
    # the statements stacked under it, when the export asks for them: under a small line of their own,
    # "Stacked under it (3)", each with its reference in the soft ink and no quote, inside the row,
    # so the page never parts them from their top
    if s.get("stacked"):
        out.append('<div class="stacked">'
                   + f'<p class="stk-head">{esc(th.counted(th.STACKED_HEAD, len(s["stacked"])))}</p>'
                   + "".join(f'<p class="stk">{esc(x["text"])}'
                             + (f' <span class="ref">{esc(reference(x))}</span>' if reference(x) else "") + "</p>"
                             for x in s["stacked"]) + "</div>")
    return "".join(out) + "</div>"


def block_html(theme: dict, shades: dict, depth: int = 0, numbers: dict | None = None, empty: bool = True) -> str:
    """A label's block in the table: a PET under its label and its title in capitals, "A. HOME
    LIFE", a band of its tint behind the title and a rule of it down its side, a sub-theme under its
    label and title in bold, "A1. Mornings", and a group in bold italic, "A1.1 Early light", each
    set in a little further and a little smaller, its heading a level down. A group inside a group,
    "A1.1.1", takes the fifth step, its heading an h5, and anything deeper stays at that step's size
    and indent. Then its note in italics when it has one, then its statements and the labels inside
    it in the order the canvas reads them. `numbers` are `themes.pet_numbers`', the Word document's,
    letters or numbers as the project labels its PETs. With `empty` off a label with nothing under it
    says nothing, for the GETs print's Selected, which leaves rows out by choice.

    The blocks flow on from page to page, a row never split, and a title is kept with its first row
    (Adam, 31 October: a PET's title fell at a page's foot with its rows on the next, in the Mac's
    print, whose engine keeps no heading with what follows it). So a block is two parts one after the
    other, each with the block's rule down its side, the rule unbroken between them: `.lead`, its
    heading, its note and its first row, which a page never splits, and `.cont`, the rest, which flows.
    When the first item is a sub-theme, the sub-theme's own lead goes inside this one, so its title is
    kept with its first row too, and its `.cont` comes first in this one's. A lead moved to the next page
    takes its rule with it, where a block's rule begun around a lead moved on left a stub of the rule at
    the foot of the page before, in the Mac's print. A block with nothing after its first row is its
    lead alone, `.end`, which takes the space below the block.

    Nothing else is kept together: the rows flow freely across pages, each row whole, so the pages fill
    (Adam, 31 October, later: a sub-PET kept whole on a page left half of the first and third pages empty,
    and he wants a heading never to end a page, nothing more; until then a sub-PET that fitted was kept
    whole and a block's last two rows went together)."""
    lead, rest = _block(theme, shades, depth, numbers or {}, empty)
    return lead + rest


def _block(theme: dict, shades: dict, depth: int, numbers: dict, empty: bool) -> tuple[str, str]:
    """A label's block as its two parts, the lead a page keeps together and the rest, empty when there is
    none, which flows after it."""
    number = numbers.get(theme["id"], "")
    hue, step = shades.get(theme["id"], ("grey", 0))
    # the steps stop at a group inside a group, the fifth, and a deeper block is set in no further
    kind = "pet" if depth == 0 else f"sub d{min(depth, DEEP)}" + (" deep" if depth > DEEP else "")
    level = min(DEEP + 2, depth + 2)
    # its description, when it has one and the Descriptions tick leaves it in, a line of the heading under
    # its title, in the serif and never in capitals (Adam, 21 October)
    desc = f'<span class="desc">{esc(theme[th.DESCRIPTION])}</span>' if theme.get(th.DESCRIPTION) else ""
    if depth == 0:
        head = (f'<h2 class="pet-title"><span class="number">{esc(number + "." if number else "")}</span> '
                f'<span class="title">{esc(theme["label"])}{desc}</span></h2>')
    else:
        said = th.numbered(number, theme["label"]) if number else theme["label"]
        head = f'<h{level} class="{"sub-title" if depth == 1 else "group-title"}">{esc(said)}{desc}</h{level}>'
    lead = [head]
    if theme.get("note"):
        lead.append(f'<p class="tnote">{esc(theme["note"])}</p>')
    items = th.in_order(theme)
    after = []
    if items:
        (what, first), others = items[0], items[1:]
        if what == "theme":
            opening, its_rest = _block(first, shades, depth + 1, numbers, empty)
            lead.append(opening)
            after += [its_rest] if its_rest else []
        else:
            lead.append(statement_html(first))
        after += [block_html(item, shades, depth + 1, numbers, empty) if what == "theme" else statement_html(item)
                  for what, item in others]
    elif empty:
        lead.append(f'<p class="none">{esc(i18n.t("page_print.pets.empty"))}</p>')
    classes = f'block {kind} hue-{hue}{f" step-{step}" if step else ""}'
    return (f'<section class="{classes} lead{"" if after else " end"}">\n' + "\n".join(lead) + "\n</section>",
            f'\n<section class="{classes} cont">\n' + "\n".join(after) + "\n</section>" if after else "")


# ------------------------------------------------------------- the head

def when_printed(now: datetime | None = None) -> str:
    """The day the page is printed, 28 October 2026, in the dates format (formats.py)."""
    now = now or datetime.now().astimezone()
    return formats.date_words(now)


# The faint ink of the print, `PRINT_FAINT`, is the light faint ink of static/tokens.css, 5.3 to 1 on the
# white paper, where until 17 October (the cards' sweep) it was a paler grey, 3.8 to 1, under the 4.5 to 1 small
# print takes, on the board's name, the labels, a statement's reason, the GET table's counts, the audit
# trail's places and the foot line on paper.
PRINT_FAINT = "#756A5C"
# The warning tint of the print, `PRINT_AMBER`, is the light amber of static/tokens.css, the screen's colour for a
# case not complete, with no PETs yet or changed since it came in and for an item no longer in its file, where
# until 17 October the GETs print set those in an orange brown of its own, #8A5A1F, that no token carries.
PRINT_AMBER = "#936000"

# The print views' two faces, carried in the app so the screen and the PDF are set in the same type on every system
# (Adam, 9 November 2026): Charis SIL for the text and Nunito Sans for the headings, labels and the foot, both under
# the SIL Open Font Licence, from family/static/fonts, which the server serves at /fonts/. Typst sets the PDF in the
# same two files. The system's faces after them are only for a page opened where the fonts cannot be reached
FONTS_LINK = '<link rel="stylesheet" href="/fonts/fonts.css">'

# the faces, the tints, the controls and the head, which the table and the GETs print share
HEAD = """
:root {
  --paper: #FFFFFF; --ink: #1F1B16; --ink-soft: #554C41; --ink-faint: """ + PRINT_FAINT + """; --rule: #E3D9C7;
  --rule-firm: #CBBFA8; --crux: #C25E0B; --amber: """ + PRINT_AMBER + """;
  --serif: "Charis SIL", "Charter", "Iowan Old Style", "Palatino Linotype", Palatino, Georgia, serif;
  --sans: "Nunito Sans", "Avenir Next", "Avenir", "Segoe UI", system-ui, sans-serif;
  --mono: "SF Mono", ui-monospace, Menlo, Consolas, monospace;
  color-scheme: light;
}
.hue-0 { --hue-base: #3E7C8A; } .hue-1 { --hue-base: #5B6FA8; } .hue-2 { --hue-base: #6E8B3D; }
.hue-3 { --hue-base: #8A5A8C; } .hue-4 { --hue-base: #8F7A1F; } .hue-5 { --hue-base: #A4566A; }
.hue-6 { --hue-base: #4F8A6B; } .hue-7 { --hue-base: #6B6B80; } .hue-grey { --hue-base: #8C8C8C; }
.theme, .block { --hue: var(--hue-base); }
.step-1 { --hue: color-mix(in srgb, var(--hue-base) 64%, #fff); }
.step-2 { --hue: color-mix(in srgb, var(--hue-base) 42%, #fff); }
* { box-sizing: border-box; -webkit-print-color-adjust: exact; print-color-adjust: exact; }
html, body { background: var(--paper); color: var(--ink); }
body { margin: 0 auto; padding: 24px 16px 32px; font-family: var(--sans); font-size: 10pt; }
.controls { display: flex; flex-wrap: wrap; justify-content: flex-end; align-items: center; gap: 8px 16px; margin: 0 0 12px; }
.controls button {
  font: inherit; font-size: 12px; padding: 6px 16px; cursor: pointer; color: var(--ink);
  background: #FFFDF8; border: 1px solid var(--rule-firm); border-radius: 3px;
}
.controls button:hover { border-color: var(--ink-faint); }
.tick { display: flex; align-items: center; gap: 6px; font-size: 12px; color: var(--ink-soft); cursor: pointer; }
.tick input { margin: 0; accent-color: var(--ink-soft); }
.tick:has(input:disabled) { color: var(--ink-faint); cursor: default; }
.head { border-bottom: 1px solid var(--rule-firm); padding-bottom: 8pt; margin-bottom: 12pt; }
.top { display: flex; justify-content: space-between; align-items: flex-start; gap: 16pt; }
h1 { margin: 0; font-family: var(--serif); font-weight: normal; font-size: 22pt; line-height: 1.15; }
.table-name { margin: 3pt 0 0; font-family: var(--serif); font-size: 14pt; line-height: 1.3; color: var(--ink-soft); }
.stamp { flex: none; text-align: right; }
.date { margin: 2pt 0 0; font-size: 10pt; color: var(--ink-soft); }
.board { margin: 2pt 0 0; font-size: 8pt; letter-spacing: .08em; text-transform: uppercase; color: var(--ink-faint); }
.chosen { margin: 2pt 0 0; font-size: 8pt; letter-spacing: .08em; text-transform: uppercase; font-weight: 600; color: var(--ink-soft); }
.question { margin: 8pt 0 0; font-family: var(--serif); font-size: 11pt; line-height: 1.4; }
.label { margin-right: 6pt; font-family: var(--sans); font-size: 8pt; letter-spacing: .08em; text-transform: uppercase; color: var(--ink-faint); }
.done { margin: -4pt 0 12pt; font-size: 9pt; color: var(--ink-soft); }
.note { margin: 0 0 12pt; font-size: 9pt; line-height: 1.4; color: var(--ink-soft); white-space: pre-line; }
"""

# the foot line on screen, and what paper leaves out, after the rest so it wins. The Mac's web view, WebKit,
# prints a CSS pixel as 0.8 of a point where Chrome, Edge and Windows's web view print it as 0.75, the
# point it is, so the same page came out a fifteenth larger on a Mac, its type larger than set and its pages
# more (31 October, measured on the demo's Juno). WebKit alone knows the system font -apple-system-body, so
# under it the page is printed at 0.9375 of itself, each point a point on every system. The print info's
# own scale did the same for the type but broke WebKit's pages, cutting rows across them
TAIL = """
footer { margin-top: 18pt; padding-top: 4pt; border-top: 1px solid var(--rule); font-size: 7.5pt; color: var(--ink-faint); }
@media print {
  body { padding: 0; max-width: none; }
  .noprint { display: none !important; }
  footer { display: none; }
}
@supports (font: -apple-system-body) {
  @media print { html { zoom: .9375; } }
}
"""

# the table of PETs, landscape A4 as the book's tables are set, in the app's faces, designed as a research
# document read on screen and on paper at arm's length (Adam, 31 October 2026): the type a step under the
# screen's, a scale of five steps, the participant 18pt, a PET's title 11.5pt in capitals, a sub-PET's 10.5pt in
# bold, a statement 10pt, its quote 9pt in italics and where it was said 7pt in the quiet sans, with room between
# the PETs and between the rows so the page breathes. The headings and notes run the full width, and each
# statement is a row, `.item`, of two columns, its words and reference on the left and its quote, the longer
# of the two as a rule, on the right, 136mm at every level, so the quotes line up down the page and the left
# takes what the PET's rule, a sub-PET's indent and the 7mm gap leave, about 115mm at a PET's own level. On a
# narrow screen the right takes no more than 58%. `PAGE` is the print view's page, and `BLOCKS` the table
# itself, which the GETs print sets under its own part. A title is kept with its first row by `.lead` (see
# `block_html`), and the rows are spaced by their own padding, never a margin, so the space after a row
# never falls between a sub-PET's two parts and breaks its rule. Nothing hangs below the last row, no
# padding at a PET's foot and no margin after the last block, so no page is left with a sliver of a rule
# alone on it (Adam, 31 October: the last page was blank but for one green bar).
# `ROW` is the head both printed tables share, a grid of two rows and two sides (Adam, 1 November 2026): at the
# left the title with the table's name under it, smaller, at the right PROJECT and its value level with the title
# and RESEARCH QUESTION and its value level with the table's name, the labels in a column of their own so the
# values line up and the question wrapping in its own column, no rule. Each row's parts share their first line,
# and a long title wraps in the left two fifths of the width.
ROW = """
h1 { font-size: 18pt; }
.head { border-bottom: 0; padding-bottom: 0; margin-bottom: 10pt; }
.top { display: grid; grid-template-columns: fit-content(40%) max-content minmax(0, 1fr); align-items: baseline;
  justify-content: start; gap: 2pt 8pt; }
.titles, .about { display: contents; }
.top h1 { grid-column: 1; grid-row: 1; }
.table-name { grid-column: 1; grid-row: 2; margin: 0; font-size: 11pt; }
.about .label { grid-column: 2; margin: 0 0 0 16pt; }
.about .value { grid-column: 3; font-family: var(--serif); font-size: 10pt; line-height: 1.35; }
.about .row1 { grid-row: 1; }
.about .row2 { grid-row: 2; }
"""
PAGE = ROW + """
@page { size: A4 landscape; margin: 14mm 16mm 16mm }
body { max-width: 265mm; }
.date { font-size: 9pt; }
.note { font-size: 8.5pt; }
main > :last-child, main > :last-child > :last-child { margin-bottom: 0; }
"""
BLOCKS = """
.pet { margin: 0; padding: 0 0 0 11pt; border-left: 2pt solid var(--hue); }
.pet.cont, .pet.end { margin-bottom: 14pt; }
.lead { break-inside: avoid; page-break-inside: avoid; }
.pet-title {
  display: flex; align-items: baseline; gap: 6pt; margin: 0 0 5pt -11pt; padding: 3.5pt 8pt 3.5pt 11pt;
  font-family: var(--serif); font-weight: 700; font-size: 11.5pt; line-height: 1.3; letter-spacing: .05em;
  text-transform: uppercase; background: color-mix(in srgb, var(--hue) 11%, #fff);
  break-after: avoid; page-break-after: avoid;
}
.pet-title .number { flex: none; color: color-mix(in srgb, var(--hue) 82%, #000); }
.sub { margin: 0 0 0 3pt; padding-left: 10pt; border-left: 1pt solid var(--hue); }
.sub.lead { margin-top: 7pt; }
.sub-title, .group-title {
  margin: 0 0 3.5pt; font-family: var(--serif); font-weight: 700; font-size: 10.5pt; line-height: 1.3;
  break-after: avoid; page-break-after: avoid;
}
.group-title { font-style: italic; font-size: 10pt; }
.desc {
  display: block; margin-top: 1pt; font-family: var(--serif); font-weight: normal; font-style: normal;
  font-size: 9pt; line-height: 1.35; letter-spacing: normal; text-transform: none; color: var(--ink-soft);
}
.deep { margin-left: -11pt; }
.tnote {
  margin: 0 0 5pt; font-family: var(--serif); font-size: 9pt; font-style: italic; line-height: 1.4;
  color: var(--ink-soft); white-space: pre-line; break-after: avoid; page-break-after: avoid;
}
.item {
  display: grid; grid-template-columns: minmax(0, 1fr) min(136mm, 58%); column-gap: 7mm; align-items: baseline;
  margin: 0; padding: 0 0 4.5pt; break-inside: avoid; page-break-inside: avoid;
}
.st { margin: 0; font-family: var(--serif); font-size: 10pt; line-height: 1.35; grid-column: 1; }
.ref { margin-left: 3pt; font-family: var(--sans); font-size: 7pt; letter-spacing: .02em; color: var(--ink-faint); white-space: nowrap;
  font-variant-numeric: tabular-nums; }
.kq { grid-column: 2; grid-row: 1; margin: 0; font-family: var(--serif); font-size: 9pt; font-style: italic; line-height: 1.4; color: var(--ink-soft); }
.why { grid-column: 1; margin: 1pt 0 0; font-family: var(--sans); font-size: 7.5pt; color: var(--ink-faint); }
.stacked { grid-column: 1; margin: 2pt 0 0 2pt; padding-left: 7pt; border-left: 1pt solid var(--rule-firm); }
.stk-head { margin: 0 0 1pt; font-family: var(--sans); font-size: 7pt; color: var(--ink-faint); }
.stk { margin: 0; font-family: var(--serif); font-size: 9pt; line-height: 1.35; color: var(--ink-soft); }
.none { margin: 1pt 0 4.5pt; font-size: 8.5pt; color: var(--ink-faint); }
.rest { margin-top: 16pt; }
.rest h2 {
  margin: 12pt 0 6pt; padding-bottom: 3pt; border-bottom: 1px solid var(--rule-firm); font-family: var(--serif);
  font-weight: normal; font-size: 12pt; break-after: avoid; page-break-after: avoid;
}
"""
TABLE = PAGE + BLOCKS

# the print view's whole style, the shared head, its own and the tail
STYLE = HEAD + TABLE + TAIL


def scoped(css: str, scope: str) -> str:
    """Rules with every selector set under `scope`, `.pets .item` for `.item`, so the table's rules
    reach only the part of a page that holds a table, as in the GETs print, whose GET table and audit
    trail keep rules of the same names. Plain rules only, with no @-rule among them, as `BLOCKS` is."""
    out = []
    for rule in css.split("}"):
        if "{" not in rule:
            continue
        heads, body = rule.split("{", 1)
        out.append(", ".join(f"{scope} {h.strip()}" for h in heads.split(",")) + " {" + body + "}")
    return "\n" + "\n".join(out) + "\n"


SCRIPT = """
document.getElementById('print').onclick = () => window.print();
// the Board note tick draws the page again with the board's note under the head, the dialog shut
const tick = document.getElementById('board-note');
tick.onchange = () => {
  const url = new URL(window.location.href);
  if (tick.checked) url.searchParams.set('note', '1'); else url.searchParams.delete('note');
  url.searchParams.set('auto', '0');
  window.location.replace(url.href);
};
// Include not placed and Include statements set aside draw the page again with the part or
// without it, the dialog shut, after saving the choice in the settings, so the next export, the table
// or Word, takes it too. A save that fails still draws the page as ticked
for (const [id, key, query] of INCLUDES) {
  const box = document.getElementById(id);
  box.onchange = async () => {
    try {
      await fetch('/api/settings', { method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ [key]: box.checked }) });
    } catch (err) { /* the page still draws as ticked */ }
    const url = new URL(window.location.href);
    url.searchParams.set(query, box.checked ? '1' : '0');
    url.searchParams.set('auto', '0');
    window.location.replace(url.href);
  };
}
if (AUTO) {
  const ready = document.fonts && document.fonts.ready ? document.fonts.ready : Promise.resolve();
  ready.then(() => setTimeout(() => window.print(), 150));
}
"""


FOOT_FAMILY = '"Nunito Sans", "Avenir Next", "Avenir", "Segoe UI", system-ui, sans-serif'
FOOT_SIZE = "7pt"
# the clear gap the foot's parts keep between them, in millimetres (Adam, 1 November 2026)
FOOT_GAP_MM = 6


def css_string(part: str) -> str:
    """`part` as a CSS string, its quotes, backslashes, angle brackets and control characters escaped."""
    return '"' + "".join(f"\\{ord(c):X} " if c in '"\\<>' or ord(c) < 32 else c for c in str(part)) + '"'


def page_foot(text, middle: str = "", numbered: bool = False, fit: int = -1) -> str:
    """The foot line on paper, set in the bottom margin of every page so it never takes a page of
    its own. On screen it sits at the foot of the page as before. `text` is its left part, a string or its
    pieces (`foot_pieces`), `middle` its middle, and with `numbered` its right says the page's number and the
    count, "Page 2 of 4", in the run's language, from the page's own counters (Adam, 31 October: the
    participant, the project and the table at the left, his name and Confidential in the middle, the page at
    the right). With `fit` the left box says which of its pieces, the project, may be shortened to keep the
    parts apart, `--idiograph-fit` (Adam, 1 November), which the page's own script (`foot_fit`) and the Mac's
    window read. The right box is marked important, since the server puts an empty one in every print view it
    serves, after the page's own style, to keep out the page count Chromium prints (`server.PRINT_MARGINS`).
    A margin box is Chrome's and Windows's web view's, so the Mac's web view, WebKit, which draws none, prints
    none, and the Mac's window draws the foot itself from these boxes (main.rs, `draw_border`)."""
    quoted = css_string
    face = f"font-family: {FOOT_FAMILY}; font-size: {FOOT_SIZE}; color: {PRINT_FAINT};"
    pieces = [text] if isinstance(text, str) else [p for p in text if p]
    marked = f" --idiograph-fit: {fit};" if 0 <= fit < len(pieces) else ""
    boxes = [f"@bottom-left {{ content: {' '.join(quoted(p) for p in pieces)};{marked} {face} }}"]
    if middle:
        boxes.append(f"@bottom-center {{ content: {quoted(middle)}; {face} }}")
    if numbered:
        # the words round the two numbers, each number its counter
        mark, marks = "", ""
        content = []
        for part in re.split(f"({mark}|{marks})", i18n.t("page_print.page_of", page=mark, pages=marks)):
            if part == mark:
                content.append("counter(page)")
            elif part == marks:
                content.append("counter(pages)")
            elif part:
                content.append(quoted(part))
        boxes.append(f"@bottom-right {{ content: {' '.join(content)} !important; {face} }}")
    return "\n@page { " + " ".join(boxes) + " }\n"


def foot_parts(case: str, project: str, table: str, researcher: str = "", confidential: bool = True,
               board: str = "", day: str = "") -> tuple[str, str]:
    """The foot's left and middle (Adam, 31 October): at the left the participant with the board in brackets,
    the project and the table, "P2 Wren (Board 3) · Living with a dog · Table of Personal Experiential Themes",
    the board and the project each left out when there is none, and in the middle the researcher's name,
    Settings' Your name or else the Interviewer's name, Confidential and the day printed, "Ada Lark ·
    Confidential · 31 October 2026", so the date is on every page, Confidential left out with `confidential`
    off."""
    pieces, _fit = foot_pieces(case, project, table, board)
    middle = FOOT_DOT.join(part for part in (" ".join(str(researcher or "").split()),
                                             i18n.t("page_print.confidential") if confidential else "", day) if part)
    return "".join(pieces), middle


FOOT_DOT = "  \u00b7  "


def foot_pieces(case: str, project: str, table: str, board: str = "", cut_case: bool = False) -> tuple[list[str], int]:
    """The foot's left part in its pieces, the participant, the board in brackets, the project and the table with
    the dots between them, and the index of the one piece that may be shortened when the foot is too long for its
    line, the project (Adam, 1 November 2026: the participant, the board, his name, Confidential, the date and the
    page never cut), or -1 when there is none. On the GETs' foot the project stands where the participant does,
    so `cut_case` makes that piece the one."""
    named = " ".join(str(board or "").split())
    pieces: list[str] = []
    fit = -1
    who = case or named
    bracket = f" ({named})" if case and named else ""
    for i, (part, cut) in enumerate(((who, cut_case and bool(case)), (" ".join(str(project or "").split()), True),
                                     (table, False))):
        if not part:
            continue
        if pieces:
            pieces.append(FOOT_DOT)
        if cut:
            fit = len(pieces)
        pieces.append(part)
        if i == 0 and bracket:
            pieces.append(bracket)
    return pieces, fit


# The page's own script that keeps the foot's parts apart on paper (Adam, 1 November 2026): Chrome centres the
# middle margin box on the page, so a long left part ran into it. The script measures the three parts in the foot's
# own type, shortens the project with an ellipsis until the three keep a clear gap, and sets the left and middle parts in
# the left box, the middle centred in the room between the left's end and the right's start, the space before it
# made of no-break spaces to the width measured, the middle box then left empty. Run as the page
# loads, so Print, Chrome's headless PDF and Windows's web view all print the same foot. Its style is marked
# `data-foot-fitted` so the Mac's window, which draws the foot itself, reads the server's boxes beneath it.
FOOT_FIT = """
(function () {
  const F = FOOT;
  if (!F || !document.body) return;
  const probe = document.createElement('span');
  probe.style.cssText = 'position:absolute;left:-100000px;top:0;visibility:hidden;white-space:nowrap;font-family:'
    + F.family + ';font-size:' + F.size;
  document.body.appendChild(probe);
  const width = (s) => { probe.textContent = s; return probe.getBoundingClientRect().width; };
  const px = 96 / 25.4;
  const room = F.width * px;
  const gap = F.gap * px;
  const pieces = F.left.slice();
  const right = F.right ? width(F.right) : 0;
  const centre = F.centre ? width(F.centre) : right;
  const middle = F.middle ? width(F.middle) : 0;
  const parts = (F.middle ? 1 : 0) + (F.right ? 1 : 0);
  const fits = (left) => width(left) + middle + right + gap * parts <= room;
  let left = pieces.join('');
  if (!fits(left) && F.fit >= 0 && F.fit < pieces.length) {
    const whole = pieces[F.fit];
    // cut at a word, the words before it kept with any comma or colon after the last taken off, as the Mac's
    // window cuts (main.rs, `cut_at_word`)
    const ends = [0];
    for (let i = 1; i < whole.length; i++) if (/\\s/.test(whole[i]) && !/\\s/.test(whole[i - 1])) ends.push(i);
    const cut = (n) => { const p = pieces.slice(); p[F.fit] = whole.slice(0, n).replace(/[\\s,;:.]+$/, '') + '\\u2026'; return p.join(''); };
    let lo = 0;
    let hi = ends.length - 1;
    while (lo < hi) {
      const k = Math.ceil((lo + hi) / 2);
      if (fits(cut(ends[k]))) lo = k; else hi = k - 1;
    }
    left = cut(ends[lo]);
  }
  let said = left;
  if (F.middle) {
    // where the middle starts, then as many no-break spaces as come nearest to it, measured as the line sets them
    const wide = width(left);
    const start = wide + (room - centre - wide - middle) / 2;
    const one = Math.max(0.5, (width('x' + '\\u00a0'.repeat(20) + 'x') - width('xx')) / 20);
    let n = Math.max(1, Math.round((start - wide) / one));
    while (n > 1 && width(left + '\\u00a0'.repeat(n)) > start + one / 2) n--;
    while (width(left + '\\u00a0'.repeat(n)) < start - one / 2) n++;
    said = left + '\\u00a0'.repeat(n) + F.middle;
  }
  probe.remove();
  const quoted = '"' + said.replace(/["\\\\<>\\u0000-\\u001f]/g, (c) => '\\\\' + c.charCodeAt(0).toString(16).toUpperCase() + ' ') + '"';
  const style = document.createElement('style');
  style.setAttribute('data-foot-fitted', '');
  style.textContent = '@page { @bottom-left { content: ' + quoted + '; } @bottom-center { content: none; } }';
  document.head.appendChild(style);
})();
"""


def foot_room(css: str) -> float:
    """The width in millimetres between a page's left and right margins, from its last `@page` rule's size and
    margin in `css`, A4 portrait unless it says landscape, as the foot's margin boxes have it."""
    width = 210.0
    right = left = 0.0
    for rule in re.findall(r"@page\s*\{([^{}]*)", css):
        size = re.search(r"size:\s*([^;]+)", rule)
        if size:
            width = 297.0 if "landscape" in size.group(1) else 210.0
        margin = re.search(r"margin:\s*([^;]+)", rule)
        values = [float(v) for v in re.findall(r"([\d.]+)mm", margin.group(1))] if margin else []
        if values:
            right = values[0] if len(values) == 1 else values[1]
            left = values[3] if len(values) >= 4 else right
    return width - right - left


def foot_fit(pieces: list[str], fit: int, middle: str, css: str, numbered: bool = True) -> str:
    """The page's script that keeps the foot apart (`FOOT_FIT`), with what it measures: the left part's pieces,
    the one it may shorten, the middle, the widest the right is likely to be, "Page 00 of 00", and the room the
    page's margins leave."""
    said = {"left": [p for p in pieces if p], "fit": fit, "middle": middle,
            "right": i18n.t("page_print.page_of", page="00", pages="00") if numbered else "",
            "centre": i18n.t("page_print.page_of", page="0", pages="0") if numbered else "",
            "width": foot_room(css), "gap": FOOT_GAP_MM, "family": FOOT_FAMILY, "size": FOOT_SIZE}
    return f"<script>const FOOT = {json.dumps(said, ensure_ascii=False).replace('</', '<' + chr(92) + '/')};{FOOT_FIT}</script>"


# the export's ticks, each by its id on the page, its key in config.json, the query the page is drawn by
# and its words, all off on a new install: the two that put Not placed and Discarded in the export (18
# October), the third that puts the statements stacked under a top beneath it (19 October), and For
# sending, which leaves the board's name off the page and out of the file's name (Adam, 19 October)
INCLUDES = (("include-descriptions", "export_descriptions", "descriptions"),
            ("include-unplaced", "export_not_placed", "unplaced"),
            ("include-binned", "export_binned", "binned"),
            ("include-stacked", "export_stacked", "stacked"),
            ("for-sending", "export_for_sending", "sending"))


def include_words() -> tuple:
    """Each tick's words in INCLUDES' order, in the run's language."""
    return (i18n.t("page_print.tick.descriptions"), i18n.t("page_print.tick.unplaced"), i18n.t("page_print.tick.binned"),
            i18n.t("page_print.tick.stacked"), i18n.t("page_print.tick.sending"))


def include_ticks(unplaced: bool, binned: bool, stacked: bool = False, sending: bool = False,
                  descriptions: bool = True) -> str:
    """The page's ticks, each toggling from its whole row inside its label, as the page is drawn."""
    return "".join(f'<label class="tick"><input type="checkbox" id="{box}"' + (" checked" if on else "")
                   + f"> {esc(words)}</label>"
                   for (box, _key, _query), words, on in zip(INCLUDES, include_words(),
                                                              (descriptions, unplaced, binned, stacked, sending)))


def about_block(project: str, asked: str) -> list[str]:
    """The project and the research question at the right of the head, each after its label, the labels in a
    column of their own so the two values line up (Adam, 31 October 2026: so the head takes less of the page),
    the project in the title's row and the question in the table's name's (Adam, 1 November: a two by two
    grid). The values take the width the title and the table's name leave, their lines wrapping there."""
    rows = [f'<span class="label {row}">{esc(label)}</span><span class="value {row}">{esc(said)}</span>'
            for label, said, row in ((i18n.t("page_print.project"), project, "row1"),
                                     (i18n.t("page_print.research_question"), asked, "row2")) if said]
    return ['<div class="about">', *rows, "</div>"] if rows else []


def page_lang() -> str:
    """The print view's language, the locale the run's catalogue reads in, en-GB in English (i18nleft)."""
    return i18n.locale_of(i18n.LANGUAGE())


def title_of(case: str, board_name: str, sending: bool = False) -> str:
    """The page's title, which the browser takes as the PDF's name: the case alone for sending,
    "P9 - Wren", and otherwise with the board, "P9 - Wren - Board 3 - PETs"."""
    return case if sending else i18n.t("page_print.pets.title", case=case, board=board_name)


def walk(workbook: Path, board: str | None, labels: str = th.LETTERS, stacked: bool = False,
         descriptions: bool = True) -> tuple[dict, dict, dict]:
    """The one walk of a board the HTML view (`page`) and the Typst view (`typst_data`) both read, so the two
    cannot disagree about what is on it: the board as the canvas reads it, the stacks and the descriptions as
    the ticks ask, each group's tint and the labels the Word document gives, letters or numbers. A board the
    file does not hold is refused."""
    workbook = Path(workbook)
    read = th.read_cards(workbook)
    data = th.load(workbook)
    version = th.pick_version(data, board)
    if version is None:
        if board and th.boards_of(data):
            raise WorkbookError(i18n.t("page_print.pets.board_gone"))
        version = th.blank_version(read["cards"])
    version = th.normalise(version)
    board_ = th.descriptions_shown(th.stacks_shown(th.outline(read, version), stacked), descriptions)
    # the labels the Word document gives, from the one place both take them
    return board_, tints(version["groups"]), th.pet_numbers(board_["themes"], labels)


# ------------------------------------------------------------- the Typst view

# The table of PETs as a Typst template (typst2, 9 November 2026, Adam about 18:10: Typst is the one engine for
# every PDF, no fallback): `typst/pets_table.typ` holds the view, `pets-table(d)`, and `typst/pets_table_main.typ`
# reads the data and calls it, the folder Typst's root, found through boot as the guidance files are and shipped
# in the frozen app as one of `app_identity.FILES`' folders. The data is `typst_data`'s, from `walk`, the walk `page`
# reads, every word on the page in it already in the run's language, so the template holds none. The design lives
# twice now, here in `STYLE` and there: a change to one is made in the other, and area 363 compares their text.
TYPST_DIR = boot.resource("typst")
TEMPLATE = TYPST_DIR / "pets_table_main.typ"


def hue_of(shades: dict, gid: str) -> dict:
    """A group's tint as the template draws it, its base colour and its step, as `HEAD`'s `.hue-*` and `.step-*`."""
    hue, step = shades.get(gid, ("grey", 0))
    return {"hue": GREY if hue == "grey" else HUES[hue], "step": step}


def statement_data(s: dict, reasons: bool = False) -> dict:
    """A statement as `statement_html` sets it: its words, where it was said, its quote in single curly marks or
    "", the reason a discard gave with `reasons`, and the statements stacked under it with their line."""
    said = bare(s.get("quote"))
    stacked = s.get("stacked") or []
    return {"kind": "st", "text": str(s["text"]), "ref": reference(s), "quote": quoted(said) if said else "",
            "reason": str(s.get("reason") or "") if reasons else "",
            "stacked": {"head": th.counted(th.STACKED_HEAD, len(stacked)),
                        "items": [{"text": str(x["text"]), "ref": reference(x)} for x in stacked]} if stacked else None}


def block_data(theme: dict, shades: dict, depth: int, numbers: dict) -> dict:
    """A label's block as `_block` sets it: a PET's number with its stop and its title, a sub-theme's or a group's
    title numbered, its description, its note and its items in the canvas's order, each a statement or a block."""
    number = numbers.get(theme["id"], "")
    if depth == 0:
        number, label = (number + "." if number else ""), str(theme["label"])
    else:
        number, label = "", th.numbered(number, theme["label"]) if number else str(theme["label"])
    return {"kind": "theme", "depth": depth, "number": number, "label": label,
            "desc": str(theme.get(th.DESCRIPTION) or ""), "note": str(theme.get("note") or ""), **hue_of(shades, theme["id"]),
            "items": [block_data(x, shades, depth + 1, numbers) if what == "theme" else statement_data(x)
                      for what, x in th.in_order(theme)]}


def typst_data(workbook: Path, case: str, board: str | None = None, question: str = "",
               now: datetime | None = None, note: bool = False, labels: str = th.LETTERS,
               unplaced: bool = False, binned: bool = False, stacked: bool = False, sending: bool = False,
               descriptions: bool = True, project: str = "", researcher: str = "", confidential: bool = True) -> dict:
    """The table of PETs as the Typst template reads it, from the same walk and the same arguments as `page`:
    the head, the board's note with `note`, the PETs, the empty board's line, Not placed and the statements set
    aside with their ticks, and the foot in its three parts, the project the one piece that may be cut. With
    `sending` the board stays out of the foot and the document's title, as on the HTML view."""
    board_, shades, numbers = walk(workbook, board, labels, stacked, descriptions)
    named = "" if sending else board_["name"]
    table = i18n.t("page_print.pets.table_name")
    project = " ".join(str(project or "").split())
    foot, middle = foot_parts(case_title(case), project, table, researcher, confidential, board=named,
                              day=when_printed(now))
    pieces, fit = foot_pieces(case_title(case), project, table, board=named)
    said = str(board_["note"] or "").strip()
    rest = []
    if unplaced and board_["unplaced"]:
        rest.append({"heading": th.counted(th.NOT_PLACED, len(board_["unplaced"])),
                     "items": [statement_data(s) for s in board_["unplaced"]]})
    if binned and board_["discarded"]:
        rest.append({"heading": th.counted(BINNED, len(board_["discarded"])),
                     "items": [statement_data(s, reasons=True) for s in board_["discarded"]]})
    lang = page_lang()
    return {
        "lang": lang.split("-")[0], "region": lang.split("-")[1] if "-" in lang else "",
        "title": title_of(case, board_["name"], sending), "author": " ".join(str(researcher or "").split()),
        "case": case_title(case), "table": table, "project": project,
        "question": " ".join(str(question or "").split()),
        "labels": {"project": i18n.t("page_print.project"), "question": i18n.t("page_print.research_question"),
                   "board_note": i18n.t("page_print.pets.board_note")},
        "note": said if note else "",
        "themes": [block_data(t, shades, 0, numbers) for t in board_["themes"]],
        "none": "" if board_["themes"] else i18n.t("page_print.pets.none"),
        "empty": i18n.t("page_print.pets.empty"),
        "rest": rest,
        "foot": {"left": [p for p in pieces if p], "fit": fit, "middle": middle, "whole": foot,
                 "page_of": i18n.t("page_print.page_of", page="{page}", pages="{pages}"),
                 "room_mm": foot_room(STYLE), "gap_mm": FOOT_GAP_MM},
    }


def page(workbook: Path, case: str, board: str | None = None, question: str = "", auto: bool = True,
         now: datetime | None = None, note: bool = False, labels: str = th.LETTERS,
         unplaced: bool = False, binned: bool = False, stacked: bool = False, sending: bool = False,
         descriptions: bool = True, project: str = "", researcher: str = "", confidential: bool = True) -> str:
    """The print view of a board of a case, the current one when `board` names none, as one HTML
    page, the table of Personal Experiential Themes. The case is named as given, by its pseudonym. A
    board the file does not hold is refused. `auto` opens the print dialog once the fonts have
    loaded, `note` puts the board's note under the head, and `labels` is the project's way of
    labelling its PETs, the book's letters unless it says numbers. Not placed comes at the end only
    with `unplaced` and Discarded only with `binned`, each left out entirely otherwise. A top stands
    for the statements stacked under it, which come under it, in a quieter row, only with `stacked`.
    With `sending` the board's name and Current board stay off the page and out of its title, the
    foot kept. Each label's description sits under its title only with `descriptions`, on by default."""
    board_, shades, numbers = walk(workbook, board, labels, stacked, descriptions)
    asked = " ".join(str(question or "").split())
    said = str(board_["note"] or "").strip()
    # the participant heads the page with the table's name under it, smaller, the project and the research question
    # to their right, each level with one of them (Adam, 1 November), and since 31 October nothing at its top right:
    # the date and the board went to the foot, and Current board went (Adam, 31 October)
    head = ['<header class="head">', '<div class="top">', '<div class="titles">', f'<h1 class="case">{esc(case_title(case))}</h1>',
            f'<p class="table-name">{esc(i18n.t("page_print.pets.table_name"))}</p>', "</div>",
            *about_block(" ".join(str(project or "").split()), asked), "</div>", "</header>"]
    if note and said:
        head.append(f'<p class="note"><span class="label">{esc(i18n.t("page_print.pets.board_note"))}</span>{esc(said)}</p>')
    body = [block_html(t, shades, numbers=numbers) for t in board_["themes"]]
    if not board_["themes"]:
        body.append(f'<p class="none">{esc(i18n.t("page_print.pets.none"))}</p>')
    # Not placed and Discarded only when they hold anything, since an empty one tells him nothing,
    # each with its count, and only when its tick asks for it
    rest = []
    if unplaced and board_["unplaced"]:
        rest += [f"<h2>{esc(th.counted(th.NOT_PLACED, len(board_['unplaced'])))}</h2>",
                 *(statement_html(s) for s in board_["unplaced"])]
    if binned and board_["discarded"]:
        rest += [f"<h2>{esc(th.counted(BINNED, len(board_['discarded'])))}</h2>",
                 *(statement_html(s, reasons=True) for s in board_["discarded"])]
    if rest:
        rest = ['<section class="rest">', *rest, "</section>"]
    tick = ('<label class="tick"><input type="checkbox" id="board-note"' + (" checked" if note else "")
            + ("" if said or note else f' disabled title="{esc(i18n.t("page_print.pets.no_note"))}"')
            + f"> {esc(i18n.t('page_print.pets.board_note'))}</label>")
    title = title_of(case, board_["name"], sending)
    # the foot names the participant, the project and the table, the researcher and Confidential, and on paper the
    # page and how many (Adam, 31 October), where it named the themes file, the participant's folder name and all
    foot, middle = foot_parts(case_title(case), project, i18n.t("page_print.pets.table_name"), researcher, confidential,
                              board="" if sending else board_["name"], day=when_printed(now))
    # in its pieces on paper, so the project can be shortened where the line is too long (Adam, 1 November)
    pieces, fit = foot_pieces(case_title(case), project, i18n.t("page_print.pets.table_name"),
                              board="" if sending else board_["name"])
    return "\n".join([
        "<!doctype html>", f'<html lang="{page_lang()}">', "<head>", '<meta charset="utf-8">',
        '<meta name="viewport" content="width=device-width, initial-scale=1">',
        f"<title>{esc(title)}</title>", FONTS_LINK, f"<style>{STYLE}{page_foot(pieces, middle, numbered=True, fit=fit)}</style>", "</head>", "<body>",
        f'<div class="controls noprint">{tick}{include_ticks(unplaced, binned, stacked, sending, descriptions)}<button type="button" id="print">{esc(i18n.t("page_print.print"))}</button></div>',
        *head, "<main>", *body, *rest, "</main>",
        f"<footer>{esc(foot + ('  ' + chr(183) + '  ' + middle if middle else ''))}</footer>",
        foot_fit(pieces, fit, middle, STYLE),
        f"<script>const AUTO = {'true' if auto else 'false'};"
        f"const INCLUDES = {json.dumps([[box, key, query] for box, key, query in INCLUDES])};{SCRIPT}</script>", "</body>", "</html>", ""])


# the refusal's one line on the print views' paper, in their faces and ink, where until 17 October it stood in the
# system's own font, and on their page, centred at its width, where it stood 16px from the window's left (17
# October, later)
REFUSED = "\n.refused { margin: 24px 0; font-size: 12pt; line-height: 1.45; }\n"


def refusal(line: str) -> str:
    """A page of one line, for a print view that cannot be made, in the print views' faces, ink and paper, and in
    the run's language as every page of the app is."""
    return "\n".join(["<!doctype html>", f'<html lang="{page_lang()}">', f'<head><meta charset="utf-8"><title>{esc(i18n.t("page_print.print"))}</title>', FONTS_LINK,
                      f"<style>{HEAD}{PAGE}{REFUSED}</style>", "</head>", f'<body><p class="refused">{esc(line)}</p></body>',
                      "</html>", ""])
