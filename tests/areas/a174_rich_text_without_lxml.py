"""Area 174: a workbook's rich text kept whole by the XML writer the app ships with (17 October).

The app as it ships, both installers and a run from source, has openpyxl without lxml, so openpyxl
writes with Python's own ElementTree, and the repo's own venv has lxml, so the gate wrote with lxml
alone and never saw what the shipped writer does. Here a workbook set out by hand as Excel writes
it, on an invented allotment with rich text in every column the app reads and writes, goes through
each of the app's save paths twice: in a child Python with `OPENPYXL_LXML=False`, which is exactly
the shipped writer whether lxml is installed or not, and in this one. Every cell is read back from
the file's own XML with the standard library, run by run, and compared with the fixture.

Only the standard library at the top of this file: the child loads it by its path and calls `drive`.
"""
from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import sys
import zipfile
import xml.etree.ElementTree as ET
from pathlib import Path

MAIN = "http://schemas.openxmlformats.org/spreadsheetml/2006/main"
NS = "{" + MAIN + "}"
REL = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
PKG = "http://schemas.openxmlformats.org/package/2006/relationships"
XMLSPACE = "{http://www.w3.org/XML/1998/namespace}space"
BOOK = "Odile - EN & ES.xlsx"
SOURCE = "Odile - transcript.xlsx"
SHEET, LATER, ADDED = "Initial", "Two weeks", "Three months"
INTERVIEWER = "Pim"
HEADER = ["Name", "Timestamp", "Experiential statements", "Transcript", "Exploratory notes", "Key quotes",
          "Interviewer notes"]
# run properties as Excel writes them: the orange highlight as the build script and the demo carry it,
# the body text, and the rest
CRUX = '<rPr><sz val="11"/><color theme="9"/><rFont val="Calibri"/><family val="2"/></rPr>'
BODY = '<rPr><sz val="11"/><color theme="1"/><rFont val="Calibri"/><family val="2"/><scheme val="minor"/></rPr>'
BOLD = '<rPr><b/><sz val="11"/><color theme="1"/><rFont val="Calibri"/><family val="2"/><scheme val="minor"/></rPr>'
ITALIC = '<rPr><i/><sz val="11"/><color theme="1"/><rFont val="Calibri"/><family val="2"/><scheme val="minor"/></rPr>'
UNDER = '<rPr><u/><sz val="11"/><color theme="1"/><rFont val="Calibri"/><family val="2"/><scheme val="minor"/></rPr>'
STRIKE = '<rPr><strike/><sz val="11"/><color theme="1"/><rFont val="Calibri"/><family val="2"/><scheme val="minor"/></rPr>'
RED = '<rPr><sz val="11"/><color rgb="FFFF0000"/><rFont val="Calibri"/><family val="2"/><scheme val="minor"/></rPr>'
TINT = ('<rPr><sz val="11"/><color theme="4" tint="0.39997558519241921"/><rFont val="Calibri"/><family val="2"/>'
        '<scheme val="minor"/></rPr>')
SERIF = '<rPr><b/><i/><sz val="14"/><color theme="1"/><rFont val="Georgia"/><family val="1"/></rPr>'
SUPER = ('<rPr><vertAlign val="superscript"/><sz val="11"/><color theme="1"/><rFont val="Calibri"/><family val="2"/>'
         '<scheme val="minor"/></rPr>')
DOUBLE = ('<rPr><u val="double"/><vertAlign val="subscript"/><sz val="11"/><color theme="1"/><rFont val="Calibri"/>'
          '<family val="2"/><scheme val="minor"/></rPr>')
SHAPED = ('<rPr><condense/><extend/><outline/><shadow/><sz val="11"/><color theme="1"/><rFont val="Calibri"/>'
          '<family val="2"/><charset val="0"/><scheme val="minor"/></rPr>')
BLUE = '<rPr><b/><sz val="11"/><color rgb="FF0070C0"/><rFont val="Calibri"/><family val="2"/><scheme val="minor"/></rPr>'
GREEN = '<rPr><sz val="11"/><color rgb="FF00B050"/><rFont val="Calibri"/><family val="2"/><scheme val="minor"/></rPr>'
# the cell styles of the fixture's styles.xml: plain, the header's bold, a person's own yellow fill,
# a theme fill with a tint
PLAIN, HEAD, YELLOW, THEMED = 1, 2, 3, 4


def r(props, words):
    """A run as Excel writes it, `xml:space` on words with a space at either end."""
    space = ' xml:space="preserve"' if words != words.strip() else ""
    return f"<r>{props}<t{space}>{words}</t></r>"


def t(words):
    space = ' xml:space="preserve"' if words != words.strip() else ""
    return f"<t{space}>{words}</t>"


# the highlighted passage, every run's properties written as Excel writes them, and the phrase its
# correction keeps
EDITED = "Now I keep a trowel by the gate and "
PHRASE = "the robin waits on the handle"
PASSAGE = r(BODY, EDITED) + r(CRUX, PHRASE) + r(BODY, " for me.")


def fixture_sheets():
    """The workbook's two sheets, each a list of rows, each row seven cells of (string XML, style)."""
    head = [(t(h), HEAD) for h in HEADER]
    blank = (None, PLAIN)
    initial = [head]
    initial.append([(t(INTERVIEWER), PLAIN), (t("00:02"), PLAIN), blank,
                    (r(BODY, "Can you tell me how the ") + r(ITALIC, "plot") + r(BODY, " began?"), PLAIN), blank, blank,
                    (r(BLUE, "Leading question") + r(BODY, ", I asked two things at once."), PLAIN)])
    initial.append([(r(BOLD, "Odile"), PLAIN), (t("00:09"), PLAIN),
                    (r(BOLD, "Taking on a neglected plot") + r(BODY, "\n\nFinding the shed beyond repair"), PLAIN),
                    ("".join([r(BODY, "So the plot was "), r(CRUX, "overgrown with bindweed"),
                              r(BODY, " when I took it on, and "), r(BOLD, "nobody"), r(BODY, " had "),
                              r(ITALIC, "touched"), r(BODY, " it for "), r(UNDER, "years"), r(BODY, ", the shed "),
                              r(STRIKE, "falling"), r(BODY, " "), r(RED, "down"), r(BODY, ". "), r(TINT, "Blue"),
                              r(SERIF, " door"), r(SUPER, "2"), r(BODY, ".")]), THEMED),
                    (r(BODY, "She laughs at ") + r(ITALIC, "nobody") + r(BODY, "."), PLAIN),
                    (r(UNDER, '"overgrown with bindweed"') + r(BODY, "\n\n(no quote)"), PLAIN), blank])
    initial.append([(t("Odile"), PLAIN), (t("00:31"), PLAIN), (t("Feeling the soil alive"), PLAIN),
                    ("".join([r(BODY, "First line\nsecond line, "), r(BOLD, "  "), r(ITALIC, "a &amp; b &lt; c &gt; d"),
                              r(BODY, " café and the bees \U0001F41D\tthere, "), r(CRUX, "the soil is "),
                              r(BOLD.replace('theme="1"', 'theme="9"'), "alive"), r(ITALIC, " after rain  ")]), YELLOW),
                    blank, blank, blank])
    initial.append([(t("Odile"), PLAIN), (t("00:58"), PLAIN), blank, (PASSAGE, PLAIN),
                    (r(BODY, "A note with a ") + r(BOLD, "carriage&#13;\nreturn") + r(BODY, " in a run"), PLAIN),
                    blank, blank])
    initial.append([(t(INTERVIEWER), PLAIN), (t("01:15"), PLAIN), blank,
                    (t("line one&#13;\nline two, a plain cell with a carriage return"), PLAIN), blank, blank, blank])
    initial.append([(t("Odile"), PLAIN), (t("01:30"), PLAIN), blank,
                    (r(BODY, "Did the ") + r(DOUBLE, "frost") + r(BODY, " get them? ") + r(SHAPED, "Every one") + r(BODY, "?"),
                     PLAIN), (t("   "), PLAIN), blank, blank])
    initial.append([(t(INTERVIEWER), PLAIN), (t("02:00"), PLAIN), blank, (t("Thank you, that is lovely."), PLAIN),
                    blank, blank, blank])
    initial.append([(t("Odile"), PLAIN), (t("02:05"), PLAIN), blank,
                    (r(ITALIC, "Bye then") + r(BODY, ", see you at the gate."), PLAIN), blank, blank, blank])
    later = [head]
    later.append([(t(INTERVIEWER), PLAIN), (t("00:03"), PLAIN), blank, (t("How is the plot now?"), PLAIN),
                  blank, blank, blank])
    later.append([(t("Odile"), PLAIN), (t("00:08"), PLAIN), (r(ITALIC, "Seeing the beans climb"), PLAIN),
                  (r(BODY, "Better. The ") + r(CRUX, "beans are climbing") + r(BODY, " and the ")
                   + r(SERIF, "tomatoes") + r(BODY, " are in again."), PLAIN), blank, blank, blank])
    return [(SHEET, initial), (LATER, later)]


def source_sheets():
    """The raw source a workbook is made from, Name, Timestamp and Transcript, rich text in its words."""
    head = [(t(h), HEAD) for h in ("Name", "Timestamp", "Transcript")]
    first = [head, [(t(INTERVIEWER), PLAIN), (t("00:02"), PLAIN),
                     (r(BODY, "Tell me about the ") + r(ITALIC, "plot") + r(BODY, "."), PLAIN)],
             [(t("Odile"), PLAIN), (t("00:07"), PLAIN),
              (r(BODY, "It was ") + r(CRUX, "a jungle") + r(BODY, ", ") + r(BOLD, "honestly") + r(BODY, " ")
               + r(UNDER, "a jungle") + r(BODY, "."), PLAIN)]]
    added = [head, [(t("Odile"), PLAIN), (t("00:04"), PLAIN),
                    (r(BODY, "Now it ") + r(GREEN, "feeds") + r(BODY, " the street."), PLAIN)]]
    return [(SHEET, first), (ADDED, added)]


STYLES = (
    f'<styleSheet xmlns="{MAIN}"><fonts count="2">'
    '<font><sz val="11"/><color theme="1"/><name val="Calibri"/><family val="2"/><scheme val="minor"/></font>'
    '<font><b/><sz val="11"/><color theme="1"/><name val="Calibri"/><family val="2"/><scheme val="minor"/></font>'
    '</fonts><fills count="4"><fill><patternFill patternType="none"/></fill>'
    '<fill><patternFill patternType="gray125"/></fill>'
    '<fill><patternFill patternType="solid"><fgColor rgb="FFFFFF00"/><bgColor indexed="64"/></patternFill></fill>'
    '<fill><patternFill patternType="solid"><fgColor theme="7" tint="0.79998168889431442"/><bgColor indexed="64"/>'
    '</patternFill></fill></fills><borders count="1"><border><left/><right/><top/><bottom/><diagonal/></border>'
    '</borders><cellStyleXfs count="1"><xf numFmtId="0" fontId="0" fillId="0" borderId="0"/></cellStyleXfs>'
    '<cellXfs count="5"><xf numFmtId="0" fontId="0" fillId="0" borderId="0" xfId="0"/>'
    '<xf numFmtId="0" fontId="0" fillId="0" borderId="0" xfId="0" applyAlignment="1">'
    '<alignment vertical="top" wrapText="1"/></xf>'
    '<xf numFmtId="0" fontId="1" fillId="0" borderId="0" xfId="0" applyFont="1" applyAlignment="1">'
    '<alignment vertical="top" wrapText="1"/></xf>'
    '<xf numFmtId="0" fontId="0" fillId="2" borderId="0" xfId="0" applyFill="1" applyAlignment="1">'
    '<alignment vertical="top" wrapText="1"/></xf>'
    '<xf numFmtId="0" fontId="0" fillId="3" borderId="0" xfId="0" applyFill="1" applyAlignment="1">'
    '<alignment vertical="top" wrapText="1"/></xf></cellXfs>'
    '<cellStyles count="1"><cellStyle name="Normal" xfId="0" builtinId="0"/></cellStyles></styleSheet>')


def excel_book(path: Path, sheets) -> None:
    """An xlsx with every string shared and every run set out as Excel writes them."""
    strings: list[str] = []
    xml_sheets = []
    for _, rows in sheets:
        body = []
        for n, row in enumerate(rows, start=1):
            cells = []
            for col, (si, style) in enumerate(row):
                ref = f"{'ABCDEFG'[col]}{n}"
                if si is None:
                    cells.append(f'<c r="{ref}" s="{style}"/>')
                    continue
                if si not in strings:
                    strings.append(si)
                cells.append(f'<c r="{ref}" s="{style}" t="s"><v>{strings.index(si)}</v></c>')
            body.append(f'<row r="{n}">{"".join(cells)}</row>')
        xml_sheets.append(
            f'<worksheet xmlns="{MAIN}" xmlns:r="{REL}"><sheetViews><sheetView zoomScale="160" workbookViewId="0">'
            '<pane xSplit="2" ySplit="1" topLeftCell="C2" activePane="bottomRight" state="frozen"/></sheetView>'
            '</sheetViews><sheetFormatPr defaultRowHeight="15"/><cols><col min="1" max="1" width="11" customWidth="1"/>'
            '<col min="4" max="4" width="60" customWidth="1"/></cols>'
            f'<sheetData>{"".join(body)}</sheetData></worksheet>')
    count = sum(1 for _, rows in sheets for row in rows for si, _ in row if si is not None)
    parts = {
        "[Content_Types].xml": (
            '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
            '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
            '<Default Extension="xml" ContentType="application/xml"/>'
            '<Override PartName="/xl/workbook.xml" '
            'ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml"/>'
            + "".join(f'<Override PartName="/xl/worksheets/sheet{i}.xml" '
                      'ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/>'
                      for i in range(1, len(sheets) + 1))
            + '<Override PartName="/xl/styles.xml" '
            'ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.styles+xml"/>'
            '<Override PartName="/xl/sharedStrings.xml" '
            'ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sharedStrings+xml"/></Types>'),
        "_rels/.rels": (f'<Relationships xmlns="{PKG}"><Relationship Id="rId1" '
                        f'Type="{REL}/officeDocument" Target="xl/workbook.xml"/></Relationships>'),
        "xl/workbook.xml": (f'<workbook xmlns="{MAIN}" xmlns:r="{REL}"><sheets>'
                            + "".join(f'<sheet name="{name}" sheetId="{i}" r:id="rId{i}"/>'
                                      for i, (name, _) in enumerate(sheets, start=1))
                            + "</sheets></workbook>"),
        "xl/_rels/workbook.xml.rels": (
            f'<Relationships xmlns="{PKG}">'
            + "".join(f'<Relationship Id="rId{i}" Type="{REL}/worksheet" Target="worksheets/sheet{i}.xml"/>'
                      for i in range(1, len(sheets) + 1))
            + f'<Relationship Id="rId{len(sheets) + 1}" Type="{REL}/styles" Target="styles.xml"/>'
            f'<Relationship Id="rId{len(sheets) + 2}" Type="{REL}/sharedStrings" Target="sharedStrings.xml"/>'
            "</Relationships>"),
        "xl/styles.xml": STYLES,
        "xl/sharedStrings.xml": (f'<sst xmlns="{MAIN}" count="{count}" uniqueCount="{len(strings)}">'
                                 + "".join(f"<si>{s}</si>" for s in strings) + "</sst>"),
    }
    for i, xml in enumerate(xml_sheets, start=1):
        parts[f"xl/worksheets/sheet{i}.xml"] = xml
    path.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as z:
        for name, xml in parts.items():
            z.writestr(name, '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n' + xml)


# ── reading a workbook back from its own XML, the standard library alone

BOOLS = {"b", "i", "strike", "condense", "extend", "outline", "shadow"}


def _number(value: str) -> str:
    try:
        return repr(float(value))
    except ValueError:
        return value


def _props(rpr):
    """A run's properties, each as Excel means it: a bare `<b/>` is bold, a bare `<u/>` a single line."""
    if rpr is None:
        return None
    out = []
    for el in rpr:
        tag, attrs = el.tag.replace(NS, ""), dict(el.attrib)
        if tag in BOOLS:
            attrs["val"] = "0" if attrs.get("val") in ("0", "false") else "1"
        if tag == "u":
            attrs.setdefault("val", "single")
        out.append((tag, tuple(sorted((k, _number(v)) for k, v in attrs.items()))))
    return tuple(sorted(out))


def runs_of(si):
    """An `<si>` as Excel reads it: each run's words, its properties, and whether a space at either end
    of its words is kept (`xml:space`), runs with no properties at all taken as one plain string."""
    raw = []
    for el in si:
        tag = el.tag.replace(NS, "")
        if tag == "t":
            raw.append((el.text or "", el.get(XMLSPACE) == "preserve", None))
        elif tag == "r":
            words = el.find(NS + "t")
            raw.append(((words.text or "") if words is not None else "",
                        words is not None and words.get(XMLSPACE) == "preserve", _props(el.find(NS + "rPr"))))
    runs = [[w, p, keep or w == w.strip()] for w, keep, p in raw]
    if runs and all(p is None for _, p, _ in runs):
        runs = [["".join(w for w, _, _ in runs), None, all(k for _, _, k in runs)]]
    return [tuple(x) for x in runs if x[0] or len(runs) == 1]


def read_xml(path: Path) -> dict:
    """{sheet: {cell: runs}} for every cell holding a string, from the workbook's own parts."""
    with zipfile.ZipFile(path) as z:
        parts = {n: z.read(n) for n in z.namelist()}
    sst = parts.get("xl/sharedStrings.xml")
    strings = [runs_of(si) for si in ET.fromstring(sst).findall(NS + "si")] if sst else []
    rels = {el.get("Id"): el.get("Target") for el in ET.fromstring(parts["xl/_rels/workbook.xml.rels"])}
    out = {}
    for sheet in ET.fromstring(parts["xl/workbook.xml"]).iter(NS + "sheet"):
        target = rels[sheet.get("{%s}id" % REL)].lstrip("/")
        target = target if target.startswith("xl/") else "xl/" + target
        cells = {}
        for c in ET.fromstring(parts[target]).iter(NS + "c"):
            v = c.find(NS + "v")
            if c.get("t") == "s" and v is not None:
                cells[c.get("r")] = strings[int(v.text)]
            elif c.get("t") == "inlineStr":
                cells[c.get("r")] = runs_of(c.find(NS + "is"))
            elif v is not None:
                cells[c.get("r")] = [(v.text, None, True)]
        out[sheet.get("name")] = cells
    return out


# ── the save paths, run in whichever Python calls this

def drive(fixtures: str, out: str) -> None:
    """Every save path the app has, each on its own copy of the fixture case, the results under `out`,
    and `out/answers.json` saying which XML writer openpyxl used here."""
    import openpyxl

    import wipe_draft
    import workbook as wb_mod

    fixtures, out = Path(fixtures), Path(out)
    if out.exists():
        shutil.rmtree(out)
    out.mkdir(parents=True)
    answers = {"lxml": bool(openpyxl.LXML)}

    def case(name):
        shutil.copytree(fixtures, out / name)
        return out / name / BOOK

    book = case("save")
    wb = openpyxl.load_workbook(book, rich_text=True)
    wb_mod._atomic_save(wb, book)
    wb.close()
    wb_mod.save_turn(case("statements"), SHEET, 3, None, "A note on the bindweed", None,
                     pairs=[{"es": "Taking on a neglected plot", "kq": '"overgrown with bindweed"'},
                            {"es": "Finding the shed past saving", "kq": ""}])
    wb_mod.save_interviewer_note(case("note"), SHEET, 2, "Asked two things at once", INTERVIEWER)
    wb_mod.edit_statement(case("statement"), SHEET, 3, 0, "Taking on a plot nobody wanted")
    wb_mod.edit_turn(case("edit"), SHEET, 5, "So I keep a trowel by the gate and " + PHRASE + " for me.")
    book = case("replace")
    done = wb_mod.replace_words(book, "trowel", "spade")
    wb_mod.put_back(book, [{"sheet": x["sheet"], "row": x["row"], "old": x["old"], "new": x["text"],
                            "crux": x.get("crux"), "cells": x.get("cells")} for x in done["rows"]], "old")
    answers["replaced"] = done["replaced"]
    wb_mod.rename_speaker(case("rename"), "Odile", "Odette", INTERVIEWER)
    book = case("trim")
    cut = wb_mod.trim_rows(book, SHEET, 8, "after")
    wb_mod.restore_trim(book, SHEET, cut["first"], cut["removed"], Path(cut["backup"]))
    book = case("assign")
    moved = wb_mod.assign_rows(book, SHEET, 9, INTERVIEWER, 0, 8)
    block = moved["block"]
    wb_mod.restore_rows(book, SHEET, block["first"], block["before"], block["after"], Path(moved["backup"]),
                        moved["row"], moved["after"])
    answers["assigned"] = moved["kind"]
    wipe_draft.wipe(case("wipe"), SHEET, 4, [LATER])
    folder = case("made").parent
    wb_mod.create_from_source(folder / "Source" / SOURCE, folder / "Made - EN & ES.xlsx")
    book = case("added")
    wb_mod.add_from_source(book.parent / "Source" / SOURCE, [ADDED], book)
    (out / "answers.json").write_text(json.dumps(answers), encoding="utf-8")


def _expected(si: str):
    return runs_of(ET.fromstring(f'<si xmlns="{MAIN}">{si}</si>'))


def _plain(text: str):
    return [(text, None, True)]


def _first_apart(want, got):
    """The first run a cell holds otherwise than it should, as the check's detail: its place, the run
    wanted and the run found, and how many runs each has."""
    want, got = list(want or []), list(got or [])
    at = next((i for i, (a, b) in enumerate(zip(want, got)) if list(a) != list(b)), min(len(want), len(got)))
    return [at, want[at] if at < len(want) else None, got[at] if at < len(got) else None, len(want), len(got)]


def test_rich_text_without_lxml(scratch):
    print("\n174. A workbook's rich text kept whole by the XML writer the app ships with, openpyxl without lxml, "
          "through every save path, cell by cell and run by run, and the shared strings the same bytes with lxml "
          "and without")
    import openpyxl

    from . import support
    from .support import TOOL, check

    base = scratch / "rich-text-174"
    fixtures = base / "fixture"
    if base.exists():
        shutil.rmtree(base)
    excel_book(fixtures / BOOK, fixture_sheets())
    excel_book(fixtures / "Source" / SOURCE, source_sheets())
    before = read_xml(fixtures / BOOK)
    source = read_xml(fixtures / "Source" / SOURCE)

    # the shipped writer in a child Python, and this Python's own
    shipped, here = base / "shipped", base / "here"
    env = dict(os.environ, OPENPYXL_LXML="False", PYTHONIOENCODING="utf-8")
    code = ("import importlib.util, sys; sys.path.insert(0, sys.argv[1]); "
            "spec = importlib.util.spec_from_file_location('a174_driver', sys.argv[2]); "
            "m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m); m.drive(sys.argv[3], sys.argv[4])")
    child = subprocess.run([sys.executable, "-c", code, str(TOOL), __file__, str(fixtures), str(shipped)],
                           capture_output=True, text=True, encoding="utf-8", errors="replace", env=env, timeout=300)
    drive(str(fixtures), str(here))
    told = (json.loads((shipped / "answers.json").read_text(encoding="utf-8"))
            if (shipped / "answers.json").exists() else {})
    check("174: the save paths ran in a child Python on openpyxl's own ElementTree writer, the one the app ships with, "
          "and here",
          child.returncode == 0 and told.get("lxml") is False and told.get("replaced") == 1
          and (here / "answers.json").exists(),
          f"{child.returncode} {told} {child.stderr.strip()[-300:]}")
    if child.returncode != 0:
        return

    def path_of(root, name):
        return root / name / ("Made - EN & ES.xlsx" if name == "made" else BOOK)

    paths = ("save", "statements", "note", "statement", "edit", "replace", "rename", "trim", "assign", "wipe",
             "made", "added")
    names = [f"A{n}" for n in (3, 4, 5, 7, 9)]
    # the cells each path writes, and what each then holds. The key quotes cell of the statements' save
    # reads the same as before, its "(no quote)" kept, so it is left as it was. A correction and a
    # replace keep the highlight by its phrase and write the words around it as the cell's own text.
    written = {
        "statements": {(SHEET, "C3"): _plain("Taking on a neglected plot\n\nFinding the shed past saving"),
                       (SHEET, "E3"): _plain("A note on the bindweed")},
        "note": {(SHEET, "G2"): _plain("Asked two things at once")},
        "statement": {(SHEET, "C3"): _plain("Taking on a plot nobody wanted\n\nFinding the shed beyond repair")},
        "edit": {(SHEET, "D5"): _expected(t("So I keep a trowel by the gate and ") + r(CRUX, PHRASE) + t(" for me."))},
        "replace": {(SHEET, "D5"): _expected(t(EDITED) + r(CRUX, PHRASE) + t(" for me."))},
        "rename": {**{(SHEET, ref): _plain("Odette") for ref in names}, (LATER, "A3"): _plain("Odette")},
        "wipe": {**{(SHEET, f"{col}{n}"): None for col in "CEF" for n in range(5, 10)},
                 **{(LATER, f"{col}{n}"): None for col in "CEF" for n in (2, 3)}},
    }
    wrong = {}
    for name in paths:
        now = read_xml(path_of(shipped, name))
        if name == "made":
            # a new workbook from the raw source: each transcript cell holds the source's runs
            want = {(sheet, f"D{n}"): runs for sheet, cells in source.items() if sheet == SHEET
                    for ref, runs in cells.items() for n in [int(ref[1:])] if ref[0] == "C" and n > 1}
            got = {key: now.get(key[0], {}).get(key[1]) for key in want}
        else:
            want = {(sheet, ref): runs for sheet, cells in before.items() for ref, runs in cells.items()}
            if name == "added":
                want.update({(ADDED, f"D{ref[1:]}"): runs for ref, runs in source[ADDED].items()
                             if ref[0] == "C" and ref != "C1"})
            want.update(written.get(name, {}))
            got = {key: now.get(key[0], {}).get(key[1]) for key in want}
            extra = {(sheet, ref) for sheet, cells in now.items() for ref in cells} - set(want)
            got.update({key: now[key[0]][key[1]] for key in extra if not (name == "added" and key[0] == ADDED)})
            want.update({key: None for key in extra if not (name == "added" and key[0] == ADDED)})
        missed = {f"{s}!{c}": _first_apart(want[(s, c)], got[(s, c)]) for (s, c) in want
                  if [list(x) for x in want[(s, c)] or []] != [list(x) for x in got[(s, c)] or []]}
        if missed:
            wrong[name] = missed
    check("174: through every save path on the shipped writer, every cell keeps each run's words, its spaces and its "
          "formatting as Excel wrote them, the highlight, bold, italic, underlines, strike, colours, size, font, super "
          "and subscript, a carriage return and a cell of spaces among them, and each cell a path writes holds what "
          "it wrote", not wrong, json.dumps(wrong, ensure_ascii=False)[:1500])

    # the fills, fonts and alignment a person gave the cells, after a save that changes nothing
    def styles(path):
        wb = openpyxl.load_workbook(path)
        out = {}
        for ws in wb.worksheets:
            for row in ws.iter_rows():
                for c in row:
                    f, fill, a = c.font, c.fill, c.alignment
                    out[f"{ws.title}!{c.coordinate}"] = (
                        f.name, f.sz, f.b, f.i, fill.fill_type, getattr(fill.fgColor, "rgb", None),
                        getattr(fill.fgColor, "theme", None), round(getattr(fill.fgColor, "tint", 0) or 0, 6),
                        a.wrap_text, a.vertical)
        wb.close()
        return out
    was, now = styles(fixtures / BOOK), styles(path_of(shipped, "save"))
    check("174: a save on the shipped writer keeps every cell's fill, a person's yellow highlight and a theme tint "
          "among them, its font and its alignment",
          was == now and was.get(f"{SHEET}!D4", ())[4:6] == ("solid", "FFFFFF00"),
          str({k: (was.get(k), now.get(k)) for k in set(was) | set(now) if was.get(k) != now.get(k)})[:600])

    # the shared strings the same bytes whichever writer wrote them, so the gate's lxml and the app's own agree
    def strings(path):
        with zipfile.ZipFile(path) as z:
            return z.read("xl/sharedStrings.xml")
    apart = [name for name in paths if strings(path_of(shipped, name)) != strings(path_of(here, name))
             or read_xml(path_of(shipped, name)) != read_xml(path_of(here, name))]
    lxml_here = json.loads((here / "answers.json").read_text(encoding="utf-8")).get("lxml")
    check("174: every save path writes the same shared strings, byte for byte, and the same cells on the shipped "
          "writer as on this Python's own" + (", lxml here" if lxml_here else ", which has no lxml either"),
          not apart, str(apart))

    # Windows: et_xmlfile opens a file it is given by path in text mode, and Windows writes each line
    # feed there as a carriage return and a line feed, which every save then kept as one more carriage
    # return (20 October). A third child plays Windows's text mode on any system, and every save path
    # must write what the shipped writer wrote.
    windows = base / "windows"
    played = ("import builtins; from et_xmlfile import incremental_tree as it; "
              "it.open = lambda f, mode='r', *a, **k: builtins.open(f, mode, *a, "
              "**(dict(k, newline='\\r\\n') if 'w' in mode and 'b' not in mode and 'newline' not in k else k)); ")
    child = subprocess.run([sys.executable, "-c", played + code, str(TOOL), __file__, str(fixtures), str(windows)],
                           capture_output=True, text=True, encoding="utf-8", errors="replace", env=env, timeout=300)
    apart = ([name for name in paths if strings(path_of(shipped, name)) != strings(path_of(windows, name))
              or read_xml(path_of(shipped, name)) != read_xml(path_of(windows, name))]
             if child.returncode == 0 else [child.stderr.strip()[-300:]])
    check("174: with Windows's line endings in et_xmlfile's text mode, every save path writes each line feed as a "
          "line feed, the same shared strings and cells as the shipped writer elsewhere", not apart, str(apart))

    # the highlight run as the build script and the demo write it comes out byte for byte the same
    with zipfile.ZipFile(path_of(shipped, "save")) as z:
        sst = z.read("xl/sharedStrings.xml").decode("utf-8")
    check("174: the highlighted passage's shared string comes out of a save on the shipped writer byte for byte as "
          "Excel wrote it", f"<si>{PASSAGE}</si>" in sst)

    # GitHub's suite on the writer the installers ship: openpyxl and et_xmlfile at the build's own pins
    workflow = support.source(".github/workflows/windows-installer.yml").read_text(encoding="utf-8")
    build_src = support.source("packaging/build_mac.py").read_text(encoding="utf-8")
    pins = re.findall(r'"((?:openpyxl|et_xmlfile)==[0-9.]+)"', build_src.split("PINS = ", 1)[-1].split("\n", 1)[0])
    check("174: GitHub's suite, on Windows, a Mac and Linux, installs openpyxl and et_xmlfile at the versions the "
          "build pins, et_xmlfile being the writer openpyxl uses without lxml",
          len(pins) == 2 and workflow.count("python -m pip install --disable-pip-version-check " + " ".join(pins)) == 3,
          str(pins))
