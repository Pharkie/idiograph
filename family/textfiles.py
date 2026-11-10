"""Text the family's apps read from a file, the same way in each (22 October 2026, the family codebase's
second build, from Idiograph's `convert.py` and Sift's `sift.py`): bytes decoded as text, a Word file's
words and its paragraphs with their heading levels, read with zipfile and the standard library's XML
parser, and markup some sources put in a record's text taken out. Idiograph's transcript import reads a
Word file through here and Trace a manuscript.

Text is UTF-8 with or without a byte order mark, falling back to Windows-1252. The standard library only,
and nothing here writes.
"""
from __future__ import annotations

import html
import io
import re
import zipfile
from pathlib import Path
from xml.etree import ElementTree

import i18n


# ------------------------------------------------------------------ text

class Unreadable(ValueError):
    """A file the readers can make nothing of, with the one line the card shows."""


def unreadable(path) -> Unreadable:
    return Unreadable(i18n.t("errors.idiograph_could_read_passages_from", name=Path(path).name))


def decode(data: bytes) -> str:
    """UTF-8 with or without a byte order mark, then Windows-1252. UTF-16 with its mark is read
    too, since a Word file saved as plain text on Windows can come out that way."""
    if data.startswith((b"\xff\xfe", b"\xfe\xff")):
        return data.decode("utf-16")
    if data.startswith(b"\xef\xbb\xbf"):
        data = data[3:]
    try:
        return data.decode("utf-8")
    except UnicodeDecodeError:
        return data.decode("cp1252", errors="replace")


# ------------------------------------------------------------------ Word

_W = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"
_FALLBACK = "{http://schemas.openxmlformats.org/markup-compatibility/2006}Fallback"
# what a paragraph's words never come from: its settings, a run's settings, a deletion tracked in
# it, a field's code, a paragraph inside it (a text box's, taken as its own after it) and the
# second copy Word keeps of a drawing
_NOT_WORDS = {_W + "pPr", _W + "rPr", _W + "sectPr", _W + "del", _W + "delText", _W + "instrText",
              _W + "p", _FALLBACK}
DOCX_MAX = 64 * 1024 * 1024        # the most a Word file's body may unpack to


def _words_of(el, out: list) -> None:
    for child in el:
        tag = child.tag
        if tag == _W + "t":
            out.append(child.text or "")
        elif tag in (_W + "tab", _W + "ptab"):
            out.append("\t")
        elif tag in (_W + "br", _W + "cr"):
            out.append("\n")
        elif tag == _W + "noBreakHyphen":
            out.append("-")
        elif tag not in _NOT_WORDS:
            _words_of(child, out)


def _paragraphs(el, out: list, levels: list | None = None, styles: dict | None = None) -> None:
    for child in el:
        if child.tag == _FALLBACK:
            continue
        if child.tag == _W + "p":
            words: list = []
            _words_of(child, words)
            out.append("".join(words))
            if levels is not None:
                levels.append(_level(child, styles or {}))
        _paragraphs(child, out, levels, styles)


HEADING_NAME = re.compile(r"^heading\s*([1-9])$", re.I)


def _outline(el) -> int:
    """A paragraph's or a style's own outline level as a heading's, 1 to 9, or 0 for none."""
    ppr = el.find(_W + "pPr")
    lvl = ppr.find(_W + "outlineLvl") if ppr is not None else None
    try:
        n = int(lvl.get(_W + "val")) if lvl is not None else -1
    except (TypeError, ValueError):
        n = -1
    return n + 1 if 0 <= n <= 8 else 0


def _level(p, styles: dict) -> int:
    """A paragraph's heading level, 1 to 9, from its own outline level, else its style's, by the
    style's outline level or its name, Heading 1 and Title among them, and 0 for a paragraph of the
    body."""
    own = _outline(p)
    if own:
        return own
    ppr = p.find(_W + "pPr")
    style = ppr.find(_W + "pStyle") if ppr is not None else None
    sid = style.get(_W + "val") if style is not None else ""
    return styles.get(sid, 0) if sid in styles else _style_level(sid, sid)


def _style_level(sid: str, name: str) -> int:
    for word in (name, sid):
        m = HEADING_NAME.match(str(word or "").strip())
        if m:
            return int(m.group(1))
        if str(word or "").strip().lower() == "title":
            return 1
    return 0


def _styles(book) -> dict:
    """Each paragraph style's heading level by its id, from its outline level or its name, so a Word
    in another language, whose ids are its own words, still has its headings."""
    try:
        xml = book.read("word/styles.xml")
    except (KeyError, OSError, RuntimeError, ValueError, NotImplementedError, zipfile.BadZipFile):
        return {}
    if b"<!DOCTYPE" in xml or b"<!ENTITY" in xml or len(xml) > DOCX_MAX:
        return {}
    try:
        root = ElementTree.fromstring(xml)
    except ElementTree.ParseError:
        return {}
    out = {}
    for st in root.iter(_W + "style"):
        sid = st.get(_W + "styleId") or ""
        name_el = st.find(_W + "name")
        level = _outline(st) or _style_level(sid, name_el.get(_W + "val") if name_el is not None else "")
        if sid:
            out[sid] = level
    return out


def _docx_body(data: bytes, name=""):
    """A Word file's body as XML and its styles' heading levels. A file that is not a Word document,
    one whose body would unpack past DOCX_MAX, and one declaring entities raise Unreadable."""
    try:
        with zipfile.ZipFile(io.BytesIO(data)) as book:
            info = book.getinfo("word/document.xml")
            if info.file_size > DOCX_MAX:
                raise unreadable(name)
            xml = book.read(info)
            styles = _styles(book)
    except Unreadable:
        raise
    except (zipfile.BadZipFile, KeyError, OSError, RuntimeError, ValueError, NotImplementedError) as exc:
        raise unreadable(name) from exc
    if b"<!DOCTYPE" in xml or b"<!ENTITY" in xml:
        raise unreadable(name)
    try:
        return ElementTree.fromstring(xml), styles
    except ElementTree.ParseError as exc:
        raise unreadable(name) from exc


def docx_text(data: bytes, name="") -> str:
    """A Word file's words as plain text, a paragraph a line and a line break inside one a line of
    its own, as Word saves the file as plain text. A file that is not a Word document, one whose
    body would unpack past DOCX_MAX, and one declaring entities raise Unreadable."""
    root, _ = _docx_body(data, name)
    paragraphs: list[str] = []
    _paragraphs(root, paragraphs)
    return "\n".join(paragraphs)


def docx_paragraphs(data: bytes, name="") -> list[tuple[int, str]]:
    """A Word file's paragraphs in order, each with its heading level, 1 to 9, or 0 for the body, as
    Sift's reference check reads a document (14 October). Unreadable as `docx_text` raises it."""
    root, styles = _docx_body(data, name)
    paragraphs: list[str] = []
    levels: list[int] = []
    _paragraphs(root, paragraphs, levels, styles)
    return list(zip(levels, paragraphs))


# ------------------------------------------------------------------ markup

BLOCK = re.compile(r"</?(?:h[1-6]|p|div|br|li|ul|ol|sec|title|jats:p|jats:sec|jats:title)\b[^<>]*>", re.I)
TAG = re.compile(r"</?[A-Za-z][A-Za-z0-9:_-]*(?:\s[^<>]*)?/?>")


def plain(text) -> str:
    """Text as the screen shows it: the markup some sources put in an abstract taken out, a heading or
    a paragraph a line of its own, entities read and the spacing tidied."""
    s = BLOCK.sub("\n", str(text or ""))
    s = html.unescape(TAG.sub("", s))
    lines = (" ".join(line.split()) for line in s.split("\n"))
    return "\n".join(line for line in lines if line)
