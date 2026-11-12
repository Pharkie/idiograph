#!/usr/bin/env python3
"""A board as a Word document, the table of Personal Experiential Themes as Smith, Flowers and
Larkin (2022) set it out in Box 5.6, their table of PETs for Elisa, for the times the print view
looks too finished to send.

The document opens with the participant under Heading 1, large, "P9 Wren", or the name alone when the
case has no number, "Juno", so Word's navigation pane names the participant, and under it the table's
name, "Table of Personal Experiential Themes", smaller in Word's Subtitle style (Adam, 20 October). With Pen
portrait ticked under Export (pbioexport, 11 November 2026) the participant's label follows in italics and their
pen portrait under it, each only when they have one, and never their picture. Then the
PETs in the order the canvas reads them, the order he sets for the story they tell, each lettered
in bold capitals as Box 5.6 letters them, "A. HOME LIFE", the title kept in its own case in the text
and shown in capitals by the run's All caps, so a copy keeps his casing, under Heading 2. A
sub-theme sits under its PET in bold, "A1. Mornings", under Heading 3, and a group, a label inside a
sub-theme, in bold italic, "A1.1 Early light", under Heading 4. A group inside a group, "A1.1.1",
takes Heading 5, and any deeper, "A1.1.1.1", keeps Heading 5, the same style as the level above it.
A project set to numbers has "PET 1. HOME LIFE", "PET 1a. Mornings" and "1a.1 Early light" in their
place. A label's description, when it has one and the Descriptions tick leaves it in (on on a new install),
is a second line of its heading, plain, smaller and grey, never bold or in capitals (Adam, 21 October). A
note, when a label has one, follows its heading in italics. Under each heading come its
statements as the canvas reads them, a label inside it taking its place among the cards where its
frame's top sits. Each statement is a paragraph followed by where it is, its sheet and timecode,
"(Initial, 12:04)", and on the next line its own quote in single curly quotation marks, set in
a little, never doubled when the workbook keeps marks round it. A statement with no quote of its own
has no quote line. Not placed and Experiential statements set aside come after under plain headings
with their counts, "Not placed (18)", each only when it holds anything and only when its tick asks for it, Include not
placed and Include statements set aside, both off on a new install, their statements set
out the same way. A statement
no longer in the workbook says so in its reference, "(Initial, 12:04, no longer in the workbook)".

The order is `themes.outline`'s and the labels `themes.pet_numbers`', read through `themes.in_order`
as the print view reads them, so the two never disagree, and the PET draft takes the same labels.
The styles are plain: Normal in a serif at 11pt, Heading 1 to 5 under Word's own names, so the
navigation pane and a reference document take them, restyled to the book's look, real bold, italic
and All caps, and no colour, no fill, no list and no table anywhere in the table of PETs. The one table
the writer sets is a theme table's participants table (`table_xml`, `gets_word`).

A `.docx` is a zip of XML parts, and this module writes them with the standard library alone. The
file goes at the case's root, beside the workbook, as `<P9 Wren> - PETs (<board name>).docx`, and
never over a file there: when that name is taken the date and time go in it,
"(Board 3, 6 Oct 14.20)". With For sending ticked it goes as the case alone, `<P9 - Wren>.docx`,
then "P9 - Wren (6 Oct 14.20).docx" when that is taken (Adam, 19 October). The document itself
names no board either way. The workbook and the themes file are only read.
"""
from __future__ import annotations

import io
import re
import zipfile
from datetime import datetime, timezone
from pathlib import Path
from xml.sax.saxutils import escape

import i18n
import themes as th
# a quote without the marks the workbook keeps round it, as the print view takes them off
from themes_print import BINNED, TITLE, bare, case_title
from workbook import WorkbookError

FONT = "Times New Roman"
# Word measures a font in half points and a page in twentieths of a point
SIZE = 22
# the participant's size, then a PET's, a sub-theme's, a group's and a group's inside a group, each at the
# body's size as in the book. Anything deeper takes the last, Heading 5
HEADING_SIZES = (40, 22, 22, 22, 22)
# the table's name under the participant, smaller, in Word's Subtitle style, which the navigation pane leaves out
SUBTITLE, SUBTITLE_SIZE = "subtitle", 28
DEEPEST = len(HEADING_SIZES)
# the space before each heading, and how far a quote is set in under its statement
HEADING_BEFORE = (0, 360, 240, 200, 160)
SET_IN = 360
# a label's description, the second line of its heading: 10pt in a grey, plain (Adam, 21 October)
DESC_SIZE, DESC_COLOUR = 20, "595959"
# the two kinds of paragraph that are neither Normal nor a heading
STATEMENT, QUOTE = "statement", "quote"
# and two that are no paragraph (pbioexport, 11 November 2026): a table, its `heads` and `rows` of plain text with
# its columns' `widths` in twentieths of a point, a theme table's participants table, and a page's end
TABLE, BREAK = "table", "break"
# the participants table's type, 10pt, its rules a thin grey and its heads' a step darker, as the print's
TABLE_SIZE, TABLE_RULE, TABLE_RULE_FIRM = 20, "D9D9D9", "A6A6A6"
MIME = "application/vnd.openxmlformats-officedocument.wordprocessingml"
W = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
R = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
PACKAGE = "http://schemas.openxmlformats.org/package/2006/relationships"
OFFICE = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
# characters XML 1.0 cannot carry, which a cell can, and which would leave Word unable to open the file
UNWRITABLE = re.compile("[\x00-\x08\x0b\x0c\x0e-\x1f￾￿]")


# ------------------------------------------------------------ the words

def heading(case: str) -> str:
    """The document's heading, the participant as the case's label gives them, "P9 Wren" for
    `P9 - Wren`, or "Juno" for a case with no number."""
    return case_title(case)


def doc_title(case: str) -> str:
    """The document's title in its properties, "P9 Wren, Table of Personal Experiential Themes"."""
    return f"{heading(case)}, {TITLE}"


def walk(themes: list[dict]):
    for t in themes:
        yield t
        yield from walk(t.get("themes") or [])


def run(text: str, bold: bool = False, italic: bool = False, caps: bool = False) -> dict:
    return {"text": str(text), "b": bold, "i": italic, "caps": caps}


def statement_blocks(s: dict) -> list[dict]:
    """A statement as the book's table sets it out: its words followed by where it is, "(Initial,
    12:04)", and on the next line its own quote in single curly quotation marks, set in a
    little, when it has one."""
    where = th.where_said(s)
    said = bare(s.get("quote"))
    out = [{"style": STATEMENT, "keep": bool(said), "runs": [run(f"{s['text']} ({where})" if where else s["text"])]}]
    if said:
        out.append({"style": QUOTE, "runs": [run(f"‘{said}’")]})
    # the statements stacked under it, when the export asks for them, set in as a quote is, under a
    # line of their own, "Stacked under it (3)", each with where it is and no quote
    if s.get("stacked"):
        out[-1]["keep"] = True
        out.append({"style": QUOTE, "keep": True, "runs": [run(th.counted(th.STACKED_HEAD, len(s["stacked"])), italic=True)]})
        for i, x in enumerate(s["stacked"]):
            where_x = th.where_said(x)
            out.append({"style": QUOTE, "keep": i < len(s["stacked"]) - 1,
                        "runs": [run(f"{x['text']} ({where_x})" if where_x else x["text"])]})
    return out


def who_blocks(who: dict | None) -> list[dict]:
    """The participant's label and pen portrait under the head, with Pen portrait ticked (pbioexport, 11 November
    2026): the label in italics, kept with the portrait, and the portrait under it, each only when there is one,
    and nothing for a participant with neither. `who` is `participants.printed`'s, so never a picture."""
    who = who or {}
    out = []
    if who.get("label"):
        out.append({"style": STATEMENT, "keep": bool(who.get("portrait")), "runs": [run(who["label"], italic=True)]})
    if who.get("portrait"):
        out.append({"style": 0, "runs": [run(who["portrait"])]})
    return out


def blocks(case: str, board: dict, labels: str = th.LETTERS, unplaced: bool = False,
           binned: bool = False, who: dict | None = None) -> list[dict]:
    """The document as a list of paragraphs, each with its style and its runs. `board` is what
    `themes.outline` gives, and a theme's `order` places its sub-themes among its statements.
    `labels` is the project's way of labelling its PETs, the book's letters unless it says numbers.
    Not placed comes after only with `unplaced` and Discarded only with `binned`, the print view's
    two ticks, each left out entirely otherwise. `who`, with Pen portrait ticked, puts the participant's
    label and pen portrait under the head."""
    out = [{"style": 1, "runs": [run(heading(case))]}, {"style": SUBTITLE, "runs": [run(TITLE)]}, *who_blocks(who)]
    # the labels and the order the print view takes too, from `themes`, so the two never disagree
    numbers = th.pet_numbers(board["themes"], labels)

    def theme(t: dict, depth: int) -> None:
        title = th.numbered(numbers[t["id"]], t["label"])
        runs = [run(title, bold=True, italic=depth >= 2, caps=depth == 0)]
        if t.get(th.DESCRIPTION):
            runs.append(dict(run(t[th.DESCRIPTION]), desc=True))
        out.append({"style": min(DEEPEST, depth + 2), "runs": runs})
        for line in str(t.get("note") or "").splitlines():
            if line.strip():
                out.append({"style": 0, "runs": [run(line.strip(), italic=True)]})
        for kind, item in th.in_order(t):
            if kind == "theme":
                theme(item, depth + 1)
            else:
                out.extend(statement_blocks(item))

    for t in board["themes"]:
        theme(t, 0)
    for title, items, wanted in ((th.NOT_PLACED, board["unplaced"], unplaced), (BINNED, board["discarded"], binned)):
        if wanted and items:
            out.append({"style": 2, "runs": [run(th.counted(title, len(items)))]})
            for s in items:
                out.extend(statement_blocks(s))
    return out


def plain(paras: list[dict]) -> list[str]:
    """The document's paragraphs as plain lines, as Word shows them, a PET's title in capitals and a
    quote set in, for a look at it without Word and for the suite."""
    out = []
    for p in paras:
        # a table a line a row, its cells parted by " | ", and a page's end no line at all
        if p["style"] == TABLE:
            out.extend(" | ".join(cells) for cells in [p["heads"], *p["rows"]])
            continue
        if p["style"] == BREAK:
            continue
        text = "".join(r["text"].upper() if r.get("caps") else r["text"] for r in p["runs"] if not r.get("desc"))
        out.append(f"    {text}" if p["style"] == QUOTE else text)
        # a description is a line of its own in its heading
        out.extend(r["text"] for r in p["runs"] if r.get("desc"))
    return out


# ------------------------------------------------------------- the parts

def xml_text(text: str) -> str:
    return escape(UNWRITABLE.sub("", " ".join(str(text).replace("\t", " ").splitlines())))


def cell_xml(text: str, width: int, head: bool = False, span: int = 1) -> str:
    """A table's cell, its words in one paragraph at the table's size with no space after, a head's in bold over
    the firmer rule, and with `span` across that many of the table's columns (demobuild, the pen portrait's line)."""
    rule = (f'<w:tcBorders><w:bottom w:val="single" w:sz="6" w:space="0" w:color="{TABLE_RULE_FIRM}"/></w:tcBorders>'
            if head else "")
    words = (f'<w:r><w:rPr>{"<w:b/><w:bCs/>" if head else ""}<w:sz w:val="{TABLE_SIZE}"/><w:szCs w:val="{TABLE_SIZE}"/>'
             f'</w:rPr><w:t xml:space="preserve">{xml_text(text)}</w:t></w:r>') if text else ""
    spans = f'<w:gridSpan w:val="{span}"/>' if span > 1 else ""
    return (f'<w:tc><w:tcPr><w:tcW w:w="{width}" w:type="dxa"/>{spans}{rule}</w:tcPr>'
            f'<w:p><w:pPr><w:spacing w:before="0" w:after="0"/></w:pPr>{words}</w:p></w:tc>')


def row_cells(cells: list, widths: list[int]) -> str:
    """A row's cells at their columns' widths, a cell given as `{"text", "span"}` taking that many columns."""
    out, at = [], 0
    for c in cells:
        span = max(1, int(c.get("span") or 1)) if isinstance(c, dict) else 1
        text = c.get("text", "") if isinstance(c, dict) else c
        out.append(cell_xml(text, sum(widths[at:at + span]), span=span))
        at += span
    return "".join(out)


def table_xml(p: dict) -> str:
    """A table (pbioexport, 11 November 2026, the theme table's participants table): plain, as a write-up's table is
    set, a rule over it, one under its heads and one under it, a thin grey one between the rows, the heads repeated
    on each page and a row never split across one, its columns at their `widths`."""
    widths = [int(w) for w in p["widths"]]
    rules = (f'<w:tblBorders><w:top w:val="single" w:sz="6" w:space="0" w:color="{TABLE_RULE_FIRM}"/>'
             f'<w:bottom w:val="single" w:sz="6" w:space="0" w:color="{TABLE_RULE_FIRM}"/>'
             f'<w:insideH w:val="single" w:sz="4" w:space="0" w:color="{TABLE_RULE}"/></w:tblBorders>')
    margins = ('<w:tblCellMar><w:top w:w="60" w:type="dxa"/><w:left w:w="100" w:type="dxa"/>'
               '<w:bottom w:w="60" w:type="dxa"/><w:right w:w="100" w:type="dxa"/></w:tblCellMar>')
    rows = [f'<w:tr><w:trPr><w:cantSplit/><w:tblHeader/></w:trPr>'
            + "".join(cell_xml(h, w, head=True) for h, w in zip(p["heads"], widths)) + "</w:tr>"]
    rows += ['<w:tr><w:trPr><w:cantSplit/></w:trPr>' + row_cells(cells, widths) + "</w:tr>" for cells in p["rows"]]
    grid = "".join(f'<w:gridCol w:w="{w}"/>' for w in widths)
    return (f'<w:tbl><w:tblPr><w:tblW w:w="{sum(widths)}" w:type="dxa"/>{rules}<w:tblLayout w:type="fixed"/>{margins}'
            f'</w:tblPr><w:tblGrid>{grid}</w:tblGrid>' + "".join(rows) + "</w:tbl>")


def paragraph(p: dict) -> str:
    style = p["style"]
    if style == TABLE:
        return table_xml(p)
    if style == BREAK:
        return '<w:p><w:r><w:br w:type="page"/></w:r></w:p>'
    if style == QUOTE:
        props = f'<w:pPr><w:ind w:left="{SET_IN}"/></w:pPr>'
    elif style == SUBTITLE:
        props = '<w:pPr><w:pStyle w:val="Subtitle"/></w:pPr>'
    elif style == STATEMENT:
        # a statement with a quote stays with it, on the same page and with no space between them
        props = '<w:pPr><w:keepNext/><w:spacing w:after="0"/></w:pPr>' if p.get("keep") else ""
    elif style:
        props = f'<w:pPr><w:pStyle w:val="Heading{style}"/></w:pPr>'
    else:
        props = ""
    runs = []
    for r in p["runs"]:
        if r.get("desc"):
            # the description on a line of its own in the heading, plain whatever the heading's style is
            runs.append('<w:r><w:rPr><w:b w:val="0"/><w:bCs w:val="0"/><w:i w:val="0"/><w:iCs w:val="0"/><w:caps w:val="0"/>'
                        f'<w:color w:val="{DESC_COLOUR}"/><w:sz w:val="{DESC_SIZE}"/><w:szCs w:val="{DESC_SIZE}"/></w:rPr>'
                        f'<w:br/><w:t xml:space="preserve">{xml_text(r["text"])}</w:t></w:r>')
            continue
        marks = (("<w:b/><w:bCs/>" if r["b"] else "") + ("<w:i/><w:iCs/>" if r["i"] else "")
                 + ("<w:caps/>" if r.get("caps") else ""))
        runs.append(f'<w:r>{"<w:rPr>" + marks + "</w:rPr>" if marks else ""}'
                    f'<w:t xml:space="preserve">{xml_text(r["text"])}</w:t></w:r>')
    return f"<w:p>{props}{''.join(runs)}</w:p>"


def document_xml(paras: list[dict]) -> str:
    # A4 portrait with margins of an inch, as the approved draft's reference document has them
    section = ('<w:sectPr><w:pgSz w:w="11906" w:h="16838"/><w:pgMar w:top="1440" w:right="1440" '
               'w:bottom="1440" w:left="1440" w:header="708" w:footer="708" w:gutter="0"/></w:sectPr>')
    return (f'<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n'
            f'<w:document xmlns:w="{W}" xmlns:r="{R}"><w:body>'
            + "".join(paragraph(p) for p in paras) + section + "</w:body></w:document>")


def fonts(size: int, bold: bool = False, italic: bool = False) -> str:
    return (f'<w:rFonts w:ascii="{FONT}" w:hAnsi="{FONT}" w:eastAsia="{FONT}" w:cs="{FONT}"/>'
            + ("<w:b/><w:bCs/>" if bold else "") + ("<w:i/><w:iCs/>" if italic else "")
            + f'<w:sz w:val="{size}"/><w:szCs w:val="{size}"/>')


def styles_xml() -> str:
    # the headings as the book's table has them, bold at the body's size, a group's in italics too
    heads = "".join(
        f'<w:style w:type="paragraph" w:styleId="Heading{n}"><w:name w:val="heading {n}"/>'
        f'<w:basedOn w:val="Normal"/><w:next w:val="Normal"/><w:uiPriority w:val="9"/><w:qFormat/>'
        f'<w:pPr><w:keepNext/><w:keepLines/><w:spacing w:before="{before}" w:after="{60 if n == 1 else 120}"/>'
        f'<w:outlineLvl w:val="{n - 1}"/></w:pPr><w:rPr>{fonts(size, bold=True, italic=n >= 4)}</w:rPr></w:style>'
        for n, (size, before) in enumerate(zip(HEADING_SIZES, HEADING_BEFORE), 1))
    return (f'<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n<w:styles xmlns:w="{W}">'
            f'<w:docDefaults><w:rPrDefault><w:rPr>{fonts(SIZE)}<w:lang w:val="en-GB" w:eastAsia="en-GB"/>'
            '</w:rPr></w:rPrDefault><w:pPrDefault><w:pPr><w:spacing w:after="120" w:line="264" w:lineRule="auto"/>'
            '</w:pPr></w:pPrDefault></w:docDefaults>'
            '<w:style w:type="paragraph" w:default="1" w:styleId="Normal"><w:name w:val="Normal"/><w:qFormat/>'
            f'<w:rPr>{fonts(SIZE)}</w:rPr></w:style>'
            + heads +
            '<w:style w:type="paragraph" w:styleId="Subtitle"><w:name w:val="Subtitle"/><w:basedOn w:val="Normal"/>'
            '<w:next w:val="Normal"/><w:uiPriority w:val="11"/><w:qFormat/><w:pPr><w:keepNext/>'
            f'<w:spacing w:before="0" w:after="240"/></w:pPr><w:rPr>{fonts(SUBTITLE_SIZE)}</w:rPr></w:style>' +
            '<w:style w:type="character" w:default="1" w:styleId="DefaultParagraphFont">'
            '<w:name w:val="Default Paragraph Font"/><w:uiPriority w:val="1"/><w:semiHidden/></w:style>'
            "</w:styles>")


def settings_xml() -> str:
    # the current Word's own mode, so the file never opens in Compatibility Mode
    return (f'<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n<w:settings xmlns:w="{W}">'
            '<w:defaultTabStop w:val="720"/><w:characterSpacingControl w:val="doNotCompress"/>'
            '<w:compat><w:compatSetting w:name="compatibilityMode" w:uri="http://schemas.microsoft.com/office/word" '
            'w:val="15"/></w:compat></w:settings>')


def core_xml(title: str, when: datetime, author: str = "") -> str:
    """The package's own properties: the title, the dates, and since 31 October the author, Settings' Your name
    (or the interviewer's name), as Word shows it under Info, left out when there is none."""
    stamp = when.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    return ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n'
            '<cp:coreProperties xmlns:cp="http://schemas.openxmlformats.org/package/2006/metadata/core-properties" '
            'xmlns:dc="http://purl.org/dc/elements/1.1/" xmlns:dcterms="http://purl.org/dc/terms/" '
            'xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">'
            f"<dc:title>{xml_text(title)}</dc:title>"
            + (f"<dc:creator>{xml_text(author)}</dc:creator>" if author else "") +
            f'<dcterms:created xsi:type="dcterms:W3CDTF">{stamp}</dcterms:created>'
            f'<dcterms:modified xsi:type="dcterms:W3CDTF">{stamp}</dcterms:modified></cp:coreProperties>')


def content_types() -> str:
    over = (("/word/document.xml", f"{MIME}.document.main+xml"), ("/word/styles.xml", f"{MIME}.styles+xml"),
            ("/word/settings.xml", f"{MIME}.settings+xml"),
            ("/docProps/core.xml", "application/vnd.openxmlformats-package.core-properties+xml"))
    return ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n'
            '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
            '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
            '<Default Extension="xml" ContentType="application/xml"/>'
            + "".join(f'<Override PartName="{p}" ContentType="{t}"/>' for p, t in over) + "</Types>")


def relationships(items: list[tuple[str, str]]) -> str:
    return (f'<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n<Relationships xmlns="{PACKAGE}">'
            + "".join(f'<Relationship Id="rId{i}" Type="{t}" Target="{target}"/>'
                      for i, (t, target) in enumerate(items, 1)) + "</Relationships>")


def parts(paras: list[dict], title: str, when: datetime, author: str = "") -> dict[str, str]:
    """Every part of the package by its name, [Content_Types].xml first, as Word reads them."""
    return {
        "[Content_Types].xml": content_types(),
        "_rels/.rels": relationships([(f"{OFFICE}/officeDocument", "word/document.xml"),
                                      (f"{PACKAGE}/metadata/core-properties", "docProps/core.xml")]),
        "word/document.xml": document_xml(paras),
        "word/styles.xml": styles_xml(),
        "word/settings.xml": settings_xml(),
        "word/_rels/document.xml.rels": relationships([(f"{OFFICE}/styles", "styles.xml"),
                                                       (f"{OFFICE}/settings", "settings.xml")]),
        "docProps/core.xml": core_xml(title, when, author),
    }


def package(paras: list[dict], title: str, when: datetime | None = None, author: str = "") -> bytes:
    when = when or datetime.now().astimezone()
    stamp = when.timetuple()[:6]
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as z:
        for name, text in parts(paras, title, when, author).items():
            info = zipfile.ZipInfo(name, date_time=stamp)
            info.compress_type = zipfile.ZIP_DEFLATED
            z.writestr(info, text.encode("utf-8"))
    return buffer.getvalue()


# ------------------------------------------------------------- the board and the file

def board_of(workbook: Path, vid=None) -> tuple[dict, dict]:
    """The board named, the current one when none is, as `themes.outline` sets it out, and the board
    itself. A case with no themes file yet gives the board an open offers, everything not placed. A
    board the file does not hold is refused."""
    workbook = Path(workbook)
    read = th.read_cards(workbook)
    data = th.load(workbook)
    version = th.pick_version(data, vid)
    if version is None:
        if vid and data:
            raise WorkbookError(i18n.t("server.board_gone_themes_exported"))
        version = th.blank_version(read["cards"])
    version = th.follow(version, read["cards"], read["quotes"])
    return th.outline(read, version), version


def file_stem(case: str, name: str, sending: bool = False) -> str:
    """`P9 Wren - PETs (Board 3)`, any character a file name cannot carry in the board's name made
    a hyphen, as the PET draft's name makes it. For sending the case alone, `P9 - Wren`, the board
    left out."""
    if sending:
        return " ".join(str(case or "").translate(th.UNSAFE).split()) or th.FIRST_NAME
    safe = " ".join(str(name or th.FIRST_NAME).translate(th.UNSAFE).split()) or th.FIRST_NAME
    return f"{case_title(case)} - PETs ({safe})"


def free_name(folder: Path, stem: str, now: datetime, ext: str = ".docx") -> tuple[Path, bool]:
    """The file the export writes, and whether the date had to go in its name: the plain name while
    it is free, then "(Board 3, 6 Oct 14.20)", then the same with a count, never a file there. A
    name for sending, with no brackets of its own, takes "P9 - Wren (6 Oct 14.20)"."""
    plain_path = folder / f"{stem}{ext}"
    if not plain_path.exists():
        return plain_path, False
    when = f"{now.day} {now:%b} {now:%H.%M}"
    dated = f"{stem[:-1]}, {when}" if stem.endswith(")") else f"{stem} ({when}"
    for n in range(1, 1000):
        path = folder / f"{dated}{'' if n == 1 else f', {n}'}){ext}"
        if not path.exists():
            return path, True
    raise WorkbookError(i18n.t("server.too_many_exports_board_share"))


def write(workbook: Path, case: str, vid=None, now: datetime | None = None, dry_run: bool = False,
          labels: str = th.LETTERS, unplaced: bool = False, binned: bool = False, stacked: bool = False,
          sending: bool = False, descriptions: bool = True, author: str = "", who: dict | None = None) -> dict:
    """Write a board as a Word document at the case's root, beside the workbook, never over a file
    there, its PETs labelled the project's way, `labels`, Not placed in it only with `unplaced` and
    Discarded only with `binned`, the statements stacked under a top beneath it only with `stacked`,
    and named by the case alone with `sending`, each label's description under its title only with
    `descriptions`, on by default, and with `who`, Pen portrait ticked, the participant's label and pen
    portrait under the head. With `dry_run` nothing is written and the answer names the file it would
    write."""
    workbook = Path(workbook)
    now = now or datetime.now().astimezone()
    board, version = board_of(workbook, vid)
    paras = blocks(case, th.descriptions_shown(th.stacks_shown(board, stacked), descriptions), labels, unplaced, binned,
                   who)
    folder = workbook.parent
    stem = file_stem(case, version.get("name"), sending)
    counts = {"pets": len(board["themes"]), "statements": sum(len(t["statements"]) for t in walk(board["themes"])),
              "not_placed": len(board["unplaced"]), "discarded": len(board["discarded"])}
    path, dated = free_name(folder, stem, now)
    out = {"path": str(path), "name": path.name, "dated": dated, "counts": counts, "version": th.summary(version),
           "labels": th.pet_labels_of(labels)}
    if dry_run:
        return dict(out, dry_run=True)
    data = package(paras, doc_title(case), now, author)
    while True:
        try:
            # opened only when no file has the name, so a file there is never written over, even one
            # that arrived after the name was chosen
            with open(path, "xb") as handle:
                try:
                    handle.write(data)
                except BaseException:
                    handle.close()
                    path.unlink(missing_ok=True)
                    raise
            break
        except FileExistsError:
            path, dated = free_name(folder, stem, now)
    return dict(out, path=str(path), name=path.name, dated=dated)
