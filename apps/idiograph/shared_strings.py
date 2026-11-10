#!/usr/bin/env python3
"""Convert an xlsx's inline strings into a shared-strings part, the way Excel writes them.

Ported from the repo's own `xlsx_inline_to_shared_strings.py`, beside the study's other scripts, so
this tool folder can be zipped and run on its own. Keep the two in step if either changes.

Why it exists. openpyxl saves every string cell inline in the worksheet
(`<c t="inlineStr"><is>...</is></c>`), and when a cell carries rich text it writes the run
properties inline too, in its own element order. Excel does neither: it puts every string in
`xl/sharedStrings.xml` and writes run properties as `sz, color, rFont, family, scheme`. The inline
form is legal OOXML, but Excel for Mac rejected a workbook written that way on 19 September 2026
("We found a problem with some content"), which cost a re-save of every annotated workbook.
Matching Excel's own layout removes the risk.

What it does, losslessly: collects every inline string, plain and rich, from every sheet, writes
`xl/sharedStrings.xml` with one `<si>` per distinct string, rewrites each cell as
`<c t="s"><v>N</v></c>`, registers the part, and leaves every other part byte for byte as it was.
It is idempotent: a file that already uses shared strings is left alone.

One string whichever XML writer openpyxl used (17 October). openpyxl writes with lxml when lxml is
installed and with Python's own ElementTree when it is not, and the app as it ships, both installers
and a run from source, has no lxml. The two writers differ, so each string is set out here as Excel
writes it, and the shared strings come out byte for byte the same either way:

- an empty element as `<sz val="11"/>`, as lxml and Excel write it, never `<sz val="11" />`
- a character past ASCII as itself, as ElementTree and Excel write it, never as `&#233;`
- a carriage return in the words as `&#13;`. ElementTree writes it bare, and the next read takes a
  bare one for a line feed, so every save without lxml turned each one into a line feed.
- `xml:space="preserve"` on every `<t>` whose words begin or end with a space, as Excel writes it.
  openpyxl leaves the mark off a run of spaces alone with either writer, and off a cell of spaces
  alone without lxml, and Excel may drop spaces left unmarked.

A line feed stays a line feed on Windows (20 October). Without lxml, openpyxl writes each sheet
through et_xmlfile into a temporary file named by its path, and et_xmlfile opens a path in text mode,
so Windows wrote every line feed in a cell's words as a carriage return and a line feed. The next
read used to fold the pair back into a line feed, but since the carriage return is kept as `&#13;`
above, each save on Windows put one more carriage return before every line feed in every cell of
several lines. `keep_line_feeds` below opens that path in binary mode, which writes the words as they
are on every system, and it is in place as soon as this module is imported.
"""
import contextlib
import os
import re
import shutil
import sys
import zipfile
from pathlib import Path

CELL = re.compile(r'<c([^>]*?)\st="inlineStr"([^>]*?)>(<is>.*?</is>)</c>', re.S)
RPR = re.compile(r"<rPr>(.*?)</rPr>", re.S)
# an empty element with the space before its slash that ElementTree writes
EMPTY = re.compile(r'<([\w:]+)((?:\s+[\w:]+="[^"]*")*)\s+/>')
# a character reference, which lxml writes for every character past ASCII
CHARREF = re.compile(r"&#(?:([0-9]+)|x([0-9a-fA-F]+));")
TEXT = re.compile(r"<t(\s[^>]*)?>(.*?)</t>", re.S)
# a space, a tab, a line feed or a carriage return at either end of a run's words, written or as a reference
EDGE = re.compile(r"^(?:\s|&#(?:9|10|13|x9|xA|xD);)|(?:\s|&#(?:9|10|13|x9|xA|xD);)$")
# the theme's body font, in the theme part openpyxl writes or keeps
THEME_BODY = re.compile(r'<(?:\w+:)?minorFont>\s*<(?:\w+:)?latin typeface="([^"]*)"', re.S)
SS_TYPE = "application/vnd.openxmlformats-officedocument.spreadsheetml.sharedStrings+xml"
SS_REL = "http://schemas.openxmlformats.org/officeDocument/2006/relationships/sharedStrings"
# Excel's order inside rPr. Anything not listed keeps its relative place at the end.
ORDER = ["b", "i", "strike", "u", "vertAlign", "sz", "color", "rFont", "family", "charset", "scheme"]


def keep_line_feeds() -> None:
    """Have et_xmlfile write a file it is given by path in binary mode, so no system turns a line feed
    into anything else (see the module's head). With lxml, or with no et_xmlfile, nothing changes."""
    try:
        from et_xmlfile import incremental_tree
    except ImportError:
        return
    plain = getattr(incremental_tree, "_get_writer", None)
    if plain is None or getattr(plain, "keeps_line_feeds", False):
        return

    @contextlib.contextmanager
    def writer(file_or_filename, encoding):
        if isinstance(file_or_filename, (str, os.PathLike)) and str(encoding).lower() != "unicode":
            with open(file_or_filename, "wb") as handle, plain(handle, encoding) as pair:
                yield pair
        else:
            with plain(file_or_filename, encoding) as pair:
                yield pair

    writer.keeps_line_feeds = True
    incremental_tree._get_writer = writer


keep_line_feeds()


def body_font(parts: dict) -> str:
    """The theme's body font, its minor font, the one a run marked `<scheme val="minor"/>` is drawn
    in. Calibri, openpyxl's own theme's, when the workbook names none."""
    for name in sorted(n for n in parts if re.fullmatch(r"xl/theme/theme\d*\.xml", n)):
        m = THEME_BODY.search(parts[name].decode("utf-8", errors="replace"))
        if m:
            return m.group(1)
    return "Calibri"


def normalise_rpr(body: str, body_font: str = "Calibri") -> str:
    """Re-order an rPr's children into Excel's sequence and add family/scheme as Excel does.

    The scheme goes only on a run in the theme's body font, `body_font`, or in no named font, as
    Excel marks it. A run marked so is the theme's body font to Excel whatever its rFont says, so a
    run in Georgia that gained the mark could come back in Calibri (17 October)."""
    tags = re.findall(r"<(\w+)[^>]*/>", body)
    elems = {t: m.group(0) for t in tags for m in [re.search(rf"<{t}[^>]*/>", body)] if m}
    if "rFont" in elems and "family" not in elems:
        elems["family"] = '<family val="2"/>'
    named = re.search(r'val="([^"]*)"', elems.get("rFont", ""))
    if (elems.get("color", "").find('theme="1"') != -1 and "scheme" not in elems
            and (named is None or named.group(1) == body_font)):
        elems["scheme"] = '<scheme val="minor"/>'
    ordered = [elems[t] for t in ORDER if t in elems]
    ordered += [v for k, v in elems.items() if k not in ORDER]
    return "<rPr>" + "".join(ordered) + "</rPr>"


def _character(m: "re.Match[str]") -> str:
    """A reference past ASCII as the character itself. ASCII's references, `&#13;` among them,
    stay as they are, and so does one that names no character XML allows."""
    code = int(m.group(1)) if m.group(1) else int(m.group(2), 16)
    if code < 0x80 or 0xD800 <= code <= 0xDFFF or code in (0xFFFE, 0xFFFF) or code > 0x10FFFF:
        return m.group(0)
    return chr(code)


def _words(m: "re.Match[str]") -> str:
    """One `<t>` as Excel writes it: a carriage return as `&#13;`, and `xml:space="preserve"` on
    words with a space at either end."""
    attrs, text = m.group(1) or "", m.group(2).replace("\r", "&#13;")
    if EDGE.search(text) and "xml:space=" not in attrs:
        attrs += ' xml:space="preserve"'
    return f"<t{attrs}>{text}</t>"


def normalise_string(body: str, font: str = "Calibri") -> str:
    """One string's XML, plain or rich, set out as Excel writes it, the same whichever writer made
    it (see the module's head), `font` the theme's body font."""
    body = EMPTY.sub(r"<\1\2/>", body)
    body = CHARREF.sub(_character, body)
    body = RPR.sub(lambda r: normalise_rpr(r.group(1), font), body)
    return TEXT.sub(_words, body)


def convert(path: Path, check: bool = False) -> int:
    """Rewrite `path` in place. Returns the number of cells converted."""
    path = Path(path)
    with zipfile.ZipFile(path) as z:
        names = z.namelist()
        parts = {n: z.read(n) for n in names}
    if "xl/sharedStrings.xml" in parts:
        return 0

    strings: list[str] = []
    index: dict[str, int] = {}

    def intern(si_body: str) -> int:
        if si_body not in index:
            index[si_body] = len(strings)
            strings.append(si_body)
        return index[si_body]

    converted = 0
    font = body_font(parts)
    for name in [n for n in names if n.startswith("xl/worksheets/sheet")]:
        xml = parts[name].decode("utf-8")

        def repl(m: "re.Match[str]") -> str:
            nonlocal converted
            before, after, is_block = m.group(1), m.group(2), m.group(3)
            body = normalise_string(is_block[4:-5], font)     # strip <is> ... </is>
            converted += 1
            return f'<c{before} t="s"{after}><v>{intern(body)}</v></c>'

        new = CELL.sub(repl, xml)
        if new != xml:
            parts[name] = new.encode("utf-8")

    if not converted or check:
        return converted

    si = "".join(f"<si>{b}</si>" for b in strings)
    parts["xl/sharedStrings.xml"] = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n'
        '<sst xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" '
        f'count="{converted}" uniqueCount="{len(strings)}">{si}</sst>'
    ).encode("utf-8")

    ct = parts["[Content_Types].xml"].decode("utf-8")
    if SS_TYPE not in ct:
        ct = ct.replace("</Types>", f'<Override PartName="/xl/sharedStrings.xml" ContentType="{SS_TYPE}"/></Types>')
        parts["[Content_Types].xml"] = ct.encode("utf-8")

    rels_name = "xl/_rels/workbook.xml.rels"
    rels = parts[rels_name].decode("utf-8")
    if SS_REL not in rels:
        used = {int(n) for n in re.findall(r'Id="rId(\d+)"', rels)}
        rid = max(used) + 1 if used else 1
        rels = rels.replace("</Relationships>", f'<Relationship Id="rId{rid}" Type="{SS_REL}" Target="sharedStrings.xml"/></Relationships>')
        parts[rels_name] = rels.encode("utf-8")

    tmp = path.with_suffix(".sharedstrings.tmp.xlsx")
    with zipfile.ZipFile(tmp, "w", zipfile.ZIP_DEFLATED) as out:
        for n in list(parts):
            out.writestr(n, parts[n])
    # verify before replacing the original
    with zipfile.ZipFile(tmp) as z:
        assert z.testzip() is None
        import xml.dom.minidom as md
        for n in z.namelist():
            if n.endswith(".xml") or n.endswith(".rels"):
                md.parseString(z.read(n))
    shutil.move(str(tmp), str(path))
    return converted


if __name__ == "__main__":
    for a in sys.argv[1:]:
        if a != "--check":
            n = convert(Path(a), check="--check" in sys.argv)
            print(f"  {Path(a).name}: {n} cells")
