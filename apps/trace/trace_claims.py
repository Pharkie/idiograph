#!/usr/bin/env python3
"""Trace (15 October), the third part of Idiograph beside Sift and Distil: each claim a manuscript makes
of a reference, held by him against the reference itself. It grew out of Sift's Check references of 14
October and is no part of Sift, since a manuscript's references are no part of a literature review alone.
His first use is a review protocol, and any paper after it.

A Trace project is a folder of its own, `trace-project.json` in it holding its name and the reference
list he loaded, if any. He adds a manuscript, Markdown or Word, or a reference list alone, a CSV with
whatever columns a reference manager's export holds, or an RIS or BibTeX export. Both are read where
they stand, afresh each time, and never written. `analyse` reads a manuscript's reference list and every
in-text citation in APA's author and year forms, one author, two, et al., a group's name and its
abbreviation, several in one bracket, a run of years, a page, and the narrative form, Smith (2020),
matching each citation to its reference. A manuscript with no reference list of its own is matched to
the project's list, and one with its own takes a DOI and a Zotero item from the project's list where its
own entry has none. A citation with no reference and a reference never cited are given as such.

The unit is the claim: each reference a sentence cites, with that sentence whole, the heading of the
section it stands in, and the sentence before it where the citation closes a sentence that leans on the
one before, one that opens This, These, However or the like. His judgement of a claim is his alone:
Supports, Y, Question, Q, or Doesn't support, N, none until he gives one, with a note.

What he does is kept in the project's folder, never beside the manuscript: for each manuscript
`<name>.log.jsonl`, one JSON line an act, appended and never rewritten, and `<name>.json`, plain and
readable, written afresh from the log after each act. Undo is a line of its own. `judge` is the one act
that sets a judgement, which the screen sends when he presses Y, Q or N, and its line says it was the
researcher's, with whether the AI's passages were shown.

A reference's PDF is found, never fetched: in the project's `pdfs/`, by the reference's key as its name
or its DOI in the file's name or on its first page, else in a screening of any Sift project he keeps,
by Sift's own list, read and never written,
the record with the same DOI or title, its `pdfs/<rec_id>.pdf`, and that record's Zotero item.
Add PDF keeps one in `pdfs/` under the reference's key, never over a file there. Every relative path
Trace answers is written with forward slashes on any system, and joined back with Path when opened.

With the app's AI switch on, `find_passages` asks the app's AI where the PDF supports each claim, one
call for one reference, through `ai_suggest.complete`, its transport a parameter, the PDF's own text sent
page by page. Every passage the answer gives is looked for in that text before it is kept, its letters
and digits in order, case, spacing and punctuation set aside, and kept in the PDF's own words with the
page it stands on. One that is not there is never kept as a quote. Passages never set a judgement.

A Sift project's `reference_check/` folder from the 14 October step is read in place as a Trace project:
its documents, its PDFs and its log as they are. Its lines of Checked, Y or N on a whole reference, are
kept and listed in its history, and never read as a judgement of a claim.

The standard library and the family's modules alone, `locks.py`, `ai_suggest.py`, `errors.py`, `files.py`,
`textfiles.py`, `pdftext.py` and `screenings.py`, which reads Sift's screenings and never writes them.
"""
from __future__ import annotations

import csv
import hashlib
import io
import json
import os
import re
import unicodedata
from pathlib import Path, PureWindowsPath

import ai_suggest as ai_mod
import i18n
import locks
import pdftext
import screenings
import textfiles
from errors import AppError, ScreeningError
from files import now_iso, write_atomic

# The words this module says, read in the run's language when said (i18nleft4, 2 November 2026): other
# modules and the checks read them as the module's names, through `__getattr__`, as themes_ai's are
SAID = {
    "NOT_KIND": lambda **v: i18n.t("trace_server.said.not_kind", v),
    "NOT_THERE": lambda **v: i18n.t("trace_server.said.not_there", v),
    "NO_DOC": lambda **v: i18n.t("trace_server.said.no_doc", v),
    "NO_REF": lambda **v: i18n.t("trace_server.said.no_ref", v),
    "NO_CLAIM": lambda **v: i18n.t("trace_server.said.no_claim", v),
    "NO_REF_LIST": lambda **v: i18n.t("trace_server.said.no_ref_list", v),
    "NO_LIST_REFS": lambda **v: i18n.t("trace_server.said.no_list_refs", v),
    "NOTHING_TO_JUDGE": lambda **v: i18n.t("trace_server.said.nothing_to_judge", v),
    "NO_PDF": lambda **v: i18n.t("trace_server.said.no_pdf", v),
    "NO_CITES": lambda **v: i18n.t("trace_server.said.no_cites", v),
    "PDF_UNREAD": lambda **v: i18n.t("trace_server.said.pdf_unread", v),
    "NO_PASSAGES": lambda **v: i18n.t("trace_server.said.no_passages", v),
    "NOT_PDF": lambda **v: i18n.t("trace_server.said.not_pdf", v),
    "PDF_THERE": lambda **v: i18n.t("trace_server.said.pdf_there", v),
    "NOT_A_PROJECT": lambda **v: i18n.t("trace_server.said.not_a_project", v),
    "JUDGE_VALUES": lambda **v: i18n.t("trace_server.said.judge_values", v),
    "LIST_GONE": lambda **v: i18n.t("trace_server.said.list_gone", v),
}


def _w(name: str, **vals) -> str:
    return SAID[name](**vals)


def __getattr__(name: str) -> str:
    """This module's words other modules and the checks name, read in the run's language."""
    if name in SAID:
        return SAID[name]()
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")

NAME = "Trace"
TOOL = "Trace"
PROJECT_FILE = "trace-project.json"
LEGACY_DIR = "reference_check"
PDF_DIR = "pdfs"
LOCK_NAME = "trace.lock"
STATE_SUFFIX = ".json"
LOG_SUFFIX = ".log.jsonl"
KINDS = {".md": "markdown", ".markdown": "markdown", ".txt": "markdown", ".docx": "word"}
LIST_KINDS = {".csv": "csv", ".tsv": "csv", ".ris": "ris", ".bib": "bibtex", ".bibtex": "bibtex"}
DOC_MAX = 32 * 1024 * 1024
PDF_MAX = 200 * 1024 * 1024
SUPPORTS, QUESTION, NOT_SUPPORTED = "Y", "Q", "N"
JUDGEMENTS = {SUPPORTS: "Supports", QUESTION: "Question", NOT_SUPPORTED: "Doesn't support"}
NO_HEADING = "No heading"
RESEARCHER = "The researcher"


class TraceError(AppError):
    """A manuscript, a list or an act Trace cannot take, said in one plain line."""


NOT_JSON = ai_mod.NOT_JSON


# ------------------------------------------------------------------- paths

def slashed(text) -> str:
    """A relative path with forward slashes whatever system wrote it, so a project moved between Windows and
    a Mac still finds what it names."""
    return "/".join(p for p in re.split(r"[\\/]+", str(text or "")) if p)


def joined(base, rel) -> Path:
    """A relative path Trace wrote, joined back to its folder with Path, a part at a time."""
    return Path(base).joinpath(*[p for p in slashed(rel).split("/") if p not in ("", ".")])


def rel_name(base, path) -> str:
    """A path as a line names it, from `base` with forward slashes when it stands under it, else its name."""
    try:
        return Path(path).resolve().relative_to(Path(base).resolve()).as_posix()
    except (ValueError, OSError):
        return Path(path).name


def from_folder(folder, target) -> str:
    """Where a file stands from the project's folder, forward slashes, `..` where it stands beside it, or
    empty on another drive."""
    try:
        return slashed(PureWindowsPath(os.path.relpath(Path(target), Path(folder))).as_posix()
                       if os.sep == "\\" else os.path.relpath(Path(target), Path(folder)))
    except ValueError:
        return ""


def located(folder, held: dict) -> Path:
    """A manuscript or a list where it stands: its path as kept when it is there, else its path from the
    project's folder, so a project moved with its files still finds them."""
    first = Path(str(held.get("document") or held.get("path") or ""))
    if first.is_file() or not held.get("relative"):
        return first
    near = joined(folder, held["relative"])
    return near if near.is_file() else first


# ------------------------------------------------------------------- the files

def project_file(folder) -> Path:
    return Path(folder) / PROJECT_FILE


def lock_path(folder) -> Path:
    return Path(folder) / LOCK_NAME


def state_path(folder, doc: str) -> Path:
    return Path(folder) / f"{doc}{STATE_SUFFIX}"


def log_path(folder, doc: str) -> Path:
    return Path(folder) / f"{doc}{LOG_SUFFIX}"


def pdf_folder(folder) -> Path:
    return Path(folder) / PDF_DIR


def good_doc(doc) -> str:
    """A document's name as the files take it, letters, digits, dashes and underscores alone, or empty."""
    text = str(doc or "")
    return text if re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_-]{0,80}", text) and text != PROJECT_FILE[:-5] else ""


def read_json(path: Path) -> dict:
    try:
        data = json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}
    return data if isinstance(data, dict) else {}


def dumps(data) -> str:
    return json.dumps(data, indent=2, ensure_ascii=False) + "\n"


def is_legacy(folder) -> bool:
    """Sift's Check references folder of 14 October, read in place as a Trace project."""
    return Path(folder).name == LEGACY_DIR


def is_project(folder) -> bool:
    folder = Path(folder)
    return project_file(folder).is_file() or (is_legacy(folder) and folder.is_dir())


def read_project(folder) -> dict:
    return read_json(project_file(folder))


def own_name(folder) -> str:
    """A project's own name: the one its file holds, for Sift's step the Sift project's folder's, else its
    folder's."""
    folder = Path(folder)
    given = str(read_project(folder).get("name") or "").strip()
    if given:
        return given
    return folder.parent.name if is_legacy(folder) else folder.name


def to_open(folder) -> Path:
    """The project a folder chosen in Open project folder opens: a Trace project's folder, or Sift's
    `reference_check/` of 14 October, chosen itself or by the Sift project's folder that holds it. Any
    other is refused in one line. Writes nothing."""
    folder = Path(folder)
    if is_project(folder):
        return folder
    if (folder / LEGACY_DIR).is_dir():
        return folder / LEGACY_DIR
    raise TraceError(_w("NOT_A_PROJECT"))


def make(folder, name: str) -> None:
    """A new project: its folder when it is new and its own file with its name."""
    folder = Path(folder)
    folder.mkdir(exist_ok=True)
    write_atomic(project_file(folder), dumps({"name": " ".join(str(name).split()), "made": now_iso(),
                                                   "made_by": "Idiograph"}))


def docs(folder) -> list[dict]:
    """The manuscripts of a project, each `doc`, the name its files take, `name`, the file's, and `path`,
    as it now stands, in the order they were added."""
    out = []
    base = Path(folder)
    if not base.is_dir():
        return out
    for path in sorted(base.glob(f"*{STATE_SUFFIX}")):
        doc = good_doc(path.name[:-len(STATE_SUFFIX)])
        data = read_json(path)
        if doc and data.get("document"):
            out.append({"doc": doc, "name": str(data.get("name") or Path(data["document"]).name),
                        "path": str(located(base, data)), "added": str(data.get("added") or ""),
                        "counts": data.get("counts") if isinstance(data.get("counts"), dict) else None})
    return sorted(out, key=lambda d: (d["added"], d["doc"]))


def doc_entry(folder, doc) -> dict:
    """One manuscript of the project, refused in one line when the project holds none of that name."""
    name = good_doc(doc)
    for d in docs(folder):
        if d["doc"] == name:
            return d
    raise TraceError(_w("NO_DOC"))


def ascii_word(text) -> str:
    folded = unicodedata.normalize("NFKD", str(text or "")).encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z0-9]+", "", folded.lower())


def same_file(a, b) -> bool:
    try:
        return Path(a).resolve() == Path(b).resolve()
    except OSError:
        return str(a) == str(b)


def add(folder, path) -> dict:
    """A file added to the project by its path: a reference list, `set_list`, or a manuscript, read once to
    be sure Trace can read it and finds its references, in its own list or the project's, and never
    written. The same manuscript added again is the one there. Answers `doc` or `list`."""
    target = Path(path).expanduser()
    suffix = target.suffix.lower()
    if suffix in LIST_KINDS:
        return {"list": set_list(folder, target)}
    if KINDS.get(suffix) is None:
        raise TraceError(_w("NOT_KIND"))
    if not target.is_file():
        raise TraceError(_w("NOT_THERE"))
    target = target.resolve()
    analysis = analyse(target, listed(folder))
    if not analysis["listed"]:
        raise TraceError(_w("NO_REF_LIST"))
    with locks.held(lock_path(folder)):
        for d in docs(folder):
            if same_file(d["path"], target):
                return {"doc": d["doc"]}
        stem = ascii_word(target.stem)[:40] or "document"
        taken = {d["doc"] for d in docs(folder)}
        doc, n = stem, 2
        while (doc in taken or not good_doc(doc) or state_path(folder, doc).exists()
               or log_path(folder, doc).exists()):
            doc, n = f"{stem}-{n}", n + 1
        data = {"document": str(target), "relative": from_folder(folder, target), "name": target.name,
                "added": now_iso(), "claims": []}
        write_atomic(state_path(folder, doc), dumps(data))
        write_state(folder, doc, analysis)
    return {"doc": doc_entry(folder, doc)["doc"]}


# ------------------------------------------------------------- the document read

HEADING_MD = re.compile(r"^(#{1,6})\s+(.*?)\s*#*\s*$")
SETEXT = re.compile(r"^\s{0,3}(=+|-+)\s*$")
FENCE = re.compile(r"^\s{0,3}(```|~~~)")
LIST_ITEM = re.compile(r"^\s{0,3}(?:[-*+]|\d{1,4}[.)])\s+")
COMMENT = re.compile(r"<!--.*?-->", re.S)


def md_inline(text: str) -> str:
    """A Markdown line's words as they read: images and footnote marks out, a link's words kept, an
    address in angle brackets kept, emphasis, code marks, tags and escapes taken away."""
    s = re.sub(r"!\[[^\]]*\]\([^)]*\)", "", text)
    s = re.sub(r"\[\^[^\]]+\]", "", s)
    s = re.sub(r"\[([^\]]+)\]\((?:[^()]|\([^)]*\))*\)", r"\1", s)
    s = re.sub(r"<(https?://[^>\s]+)>", r"\1", s)
    s = re.sub(r"</?[A-Za-z][A-Za-z0-9-]*(?:\s[^<>]*)?/?>", "", s)
    s = s.replace("**", "").replace("__", "").replace("`", "")
    s = re.sub(r"(?<![\w*])\*(?=\S)(.+?)(?<=\S)\*(?![\w*])", r"\1", s)
    s = re.sub(r"(?<![\w_])_(?=\S)(.+?)(?<=\S)_(?![\w_])", r"\1", s)
    s = re.sub(r"\\([\\`*_{}\[\]()#+\-.!>])", r"\1", s)
    return s


def md_blocks(text: str) -> list[dict]:
    """A Markdown document as headings and paragraphs, each paragraph with its lines: front matter,
    comments and code passed over, a list item a paragraph of its own, a quote's mark taken away."""
    text = COMMENT.sub("", text.replace("\r\n", "\n").replace("\r", "\n"))
    lines = text.split("\n")
    if lines and lines[0].strip() == "---":
        for i in range(1, len(lines)):
            if lines[i].strip() in ("---", "..."):
                lines = lines[i + 1:]
                break
    out: list[dict] = []
    para: list[str] = []
    fenced = False

    def close():
        # the paragraph's words read whole, so emphasis that runs over a line's end is taken away too, and
        # its lines kept as written for the reference list, each entry read as a whole once it is found
        lines_kept = [x.strip() for x in para if x.strip()]
        if lines_kept:
            out.append({"kind": "para", "text": " ".join(md_inline(" ".join(lines_kept)).split()), "lines": lines_kept,
                        "md": True})
        para.clear()

    for i, raw in enumerate(lines):
        if FENCE.match(raw):
            close()
            fenced = not fenced
            continue
        if fenced:
            continue
        line = re.sub(r"^\s{0,3}>\s?", "", raw)
        m = HEADING_MD.match(line)
        if m:
            close()
            out.append({"kind": "heading", "level": len(m.group(1)), "text": md_inline(m.group(2)).strip()})
            continue
        nxt = lines[i + 1] if i + 1 < len(lines) else ""
        if line.strip() and len(para) == 0 and SETEXT.match(nxt) and not LIST_ITEM.match(line) and not FENCE.match(nxt):
            out.append({"kind": "heading", "level": 1 if nxt.strip().startswith("=") else 2,
                        "text": md_inline(line).strip()})
            lines[i + 1] = ""
            continue
        if not line.strip():
            close()
            continue
        if LIST_ITEM.match(line):
            close()
            line = LIST_ITEM.sub("", line, count=1)
        para.append(line)
    close()
    return [b for b in out if b["kind"] == "para" or b["text"]]


def word_blocks(data: bytes, name: str) -> list[dict]:
    out = []
    for level, text in textfiles.docx_paragraphs(data, name):
        words = " ".join(text.split())
        if not words:
            continue
        if level:
            out.append({"kind": "heading", "level": level, "text": words})
        else:
            lines = [" ".join(x.split()) for x in text.split("\n") if x.strip()]
            out.append({"kind": "para", "text": words, "lines": lines})
    return out


def read_bytes(path, limit: int = DOC_MAX) -> bytes:
    target = Path(path)
    try:
        if target.stat().st_size > limit:
            raise TraceError(i18n.t("trace_server.read_bytes.file_over_32_mb"))
        return target.read_bytes()
    except FileNotFoundError:
        raise TraceError(_w("NOT_THERE")) from None
    except OSError:
        raise TraceError(i18n.t("trace_server.read_bytes.file_not_read")) from None


def blocks_of(path) -> list[dict]:
    """A document's headings and paragraphs, read and never written."""
    target = Path(path)
    kind = KINDS.get(target.suffix.lower())
    if kind is None:
        raise TraceError(_w("NOT_KIND"))
    data = read_bytes(target)
    if kind == "word":
        try:
            return word_blocks(data, target.name)
        except textfiles.Unreadable:
            raise TraceError(i18n.t("trace_server.read_docx.word_file_not_read")) from None
    return md_blocks(textfiles.decode(data))


# ---------------------------------------------------------------- the reference list

REF_HEAD = re.compile(r"^(?:[0-9IVXivx]+[.)]?\s+)?(references?|reference list|bibliography|works cited|literature cited|"
                      r"cited works)\s*:?$", re.I)
YEARS_ONE = r"(?:\d{4}[a-z]?|n\.\s?d\.(?:-[a-z])?|in press(?:-[a-z])?)"
YEAR_PAREN = re.compile(r"\(\s*(?P<y>\d{4}|n\.\s?d\.|in press)(?:-?(?P<s>[a-z]))?(?:\s*[,/][^()]*)?\)", re.I)
ENTRY_START = re.compile(r"^(?:(?:(?:van|von|de|der|den|du|da|di|del|della|le|la|ten|ter)\s+)*[A-ZÀ-Þ][^\s,()]*(?:[ '’-][A-Za-zÀ-ɏ][^\s,()]*){0,3},\s+(?:[A-ZÀ-Þ][a-z]?\.)"
                         r"|[A-Z][^.()]{1,150}\.\s+\((?:\d{4}|n\.\s?d\.|in press))")
INITIALS = re.compile(r"^(?:[A-ZÀ-Þ][a-z]?\.[\s-]*)+$")
DOI_IN = re.compile(r"(?:https?://(?:dx\.)?doi\.org/|\bdoi:\s*)?(10\.\d{4,9}/[^\s\"<>]+)", re.I)


def ref_section(blocks: list[dict]) -> tuple[int, int] | None:
    """Where the reference list stands, the first block after its heading and the block that ends it,
    the last heading named References or Bibliography, or a paragraph that says no more than that, to
    the next heading as high as it."""
    at = None
    for i, b in enumerate(blocks):
        if REF_HEAD.match(b["text"].strip()) and (b["kind"] == "heading" or len(b["text"]) < 40):
            at = i
    if at is None:
        return None
    level = blocks[at].get("level", 99) if blocks[at]["kind"] == "heading" else 99
    end = len(blocks)
    for j in range(at + 1, len(blocks)):
        if blocks[j]["kind"] == "heading" and blocks[j]["level"] <= level:
            end = j
            break
    return at, end


def entries_of(lines: list[str]) -> list[str]:
    """A paragraph of the reference list as its entries: each line that starts as an entry does, after
    one that ends as one does, an entry of its own, and any other line the rest of the one before, so a
    list one to a line and a wrapped entry both read right."""
    out: list[str] = []
    for line in lines:
        line = line.strip()
        if not line:
            continue
        ends = bool(out) and (out[-1].endswith((".", ")")) or re.search(r"\S+/\S+$", out[-1]) is not None)
        if out and not (ends and ENTRY_START.match(line)):
            out[-1] = f"{out[-1]} {line}"
        else:
            out.append(line)
    return out


def surnames(authors: str) -> list[str]:
    """The authors' surnames, or a group's name, in order, from the part of an entry before its year."""
    text = re.sub(r"\((?:Eds?|Trans|Comp|Dir)\.?[^)]*\)", "", authors).strip()
    if not re.search(r"(?:^|[\s,])[A-Z\u00C0-\u00DE][a-z]?\.", text):
        # a group's name, with no initials in it, whole, its "and" kept
        return [" ".join(text.split()).rstrip(".")] if text else []
    text = re.sub(r"\.\s?\.\s?\.|…", ",", text)
    text = re.sub(r"(?:,\s*)?(?:&|\band\b)\s*", ", ", text)
    parts = [p.strip() for p in text.split(",")]
    initials = lambda p: bool(INITIALS.match(p)) or bool(re.fullmatch(r"[A-Z\u00C0-\u00DE]", p))
    names = [p.strip(".") for p in parts if p and not initials(p) and p.strip(".") not in ("Jr", "Sr", "II", "III")]
    return [re.sub(r"\s+", " ", n) for n in names]


def parse_reference(text: str) -> dict:
    """One entry of the reference list: its words, the surnames, the year, a letter after it, the
    title as near as the entry gives it and the DOI."""
    m = YEAR_PAREN.search(text)
    names = surnames(text[:m.start()].strip().rstrip(",")) if m else []
    year = ""
    if m:
        y = m.group("y").lower().replace(" ", "")
        year = {"n.d.": "n.d.", "inpress": "in press"}.get(y, y)
    after = text[m.end():].lstrip(" .") if m else ""
    title = re.split(r"(?<=[.?!])\s+(?=[A-Z0-9(])", after, maxsplit=1)[0].strip() if after else ""
    doi = ""
    d = DOI_IN.search(text)
    if d:
        doi = pdftext.norm_doi(d.group(1).rstrip(".,;)]"))
    return {"text": text, "names": names, "year": year, "suffix": (m.group("s") or "").lower() if m else "",
            "title": title, "doi": doi, "zotero": ""}


def fold(name) -> str:
    """A name as two are matched by, its letters alone, accents and case set aside."""
    folded = unicodedata.normalize("NFKD", str(name or "")).encode("ascii", "ignore").decode().lower()
    return re.sub(r"[^a-z]", "", folded)


def keyed(refs: list[dict]) -> list[dict]:
    """Each reference's key, the first surname, the year and its letter, `-2` and up for a second alike."""
    seen: dict[str, int] = {}
    for r in refs:
        base = (ascii_word(r["names"][0])[:24] if r["names"] else "ref") + ascii_word(r["year"] or "nd") + r["suffix"]
        seen[base] = seen.get(base, 0) + 1
        r["key"] = base if seen[base] == 1 else f"{base}-{seen[base]}"
    return refs


# ------------------------------------------------------------ a reference list alone

LIST_HEADS = {
    "text": ("reference", "references", "reference text", "full reference", "citation", "full citation",
             "formatted citation", "bibliography", "apa", "apa reference", "entry"),
    "authors": ("author", "authors", "author(s)", "creator", "creators"),
    "year": ("publication year", "year", "pub year", "publication date", "date", "issued"),
    "title": ("title", "article title", "document title", "item title"),
    "journal": ("publication title", "journal", "journal title", "source title", "source", "container title",
                "publication", "book title", "publisher"),
    "doi": ("doi",),
    "key": ("key", "item key", "zotero key"),
}
LATEX_MARKS = {"`": "\u0300", "'": "\u0301", "^": "\u0302", '"': "\u0308", "~": "\u0303", "=": "\u0304",
               ".": "\u0307", "u": "\u0306", "v": "\u030C", "H": "\u030B", "c": "\u0327", "d": "\u0323",
               "b": "\u0331", "k": "\u0328"}
LATEX_LETTERS = {"ss": "ß", "o": "ø", "O": "Ø", "ae": "æ", "AE": "Æ", "oe": "œ", "OE": "Œ", "aa": "å", "AA": "Å",
                 "l": "ł", "L": "Ł", "i": "ı"}


def year_in(text) -> str:
    m = re.search(r"\b(1[5-9]\d{2}|20\d{2})\b", str(text or ""))
    if m:
        return m.group(1)
    return "in press" if re.search(r"in press", str(text or ""), re.I) else ""


def name_of(person: str) -> str:
    """A surname from a name as a reference manager writes it: before its comma, Arden, Pia, else a group's
    name whole."""
    person = " ".join(str(person or "").split()).strip(" .;")
    if "," in person:
        return person.split(",", 1)[0].strip()
    return person


def persons(authors: str) -> list[str]:
    """The authors of a column as a reference manager gives them, each whole, parted at semicolons, else at
    and or an ampersand."""
    text = str(authors or "").strip()
    if not text:
        return []
    parts = text.split(";") if ";" in text else re.split(r",?\s+(?:and|&)\s+|\s*&\s*", text)
    return [p for p in (" ".join(x.split()).strip(" ;") for x in parts) if p]


def made_text(people: list[str], year: str, title: str, journal: str) -> str:
    """A reference's words for the table when a list gives its parts alone."""
    who = "; ".join(people)
    out = f"{who} ({year or 'n.d.'})."
    if title:
        out += f" {title.rstrip('.')}."
    if journal:
        out += f" {journal.rstrip('.')}."
    return out.strip()


def entry_of(parts: dict) -> dict | None:
    """One reference from a list's parts: its words where the list gives them whole, read as an entry of a
    reference list is, else made from its authors, year and title, its DOI and Zotero item from their own
    columns."""
    text = " ".join(str(parts.get("text") or "").split())
    people = [p for p in (parts.get("people") or []) if p]
    if text:
        ref = parse_reference(text)
        if not ref["names"] and people:
            ref["names"] = [name_of(p) for p in people]
        if not ref["year"]:
            ref["year"] = year_in(parts.get("year")) or ref["year"]
        if not ref["title"]:
            ref["title"] = str(parts.get("title") or "").strip()
    else:
        title = " ".join(str(parts.get("title") or "").split())
        if not people and not title:
            return None
        year = year_in(parts.get("year")) or "n.d."
        ref = {"text": made_text(people, year, title, " ".join(str(parts.get("journal") or "").split())),
               "names": [name_of(p) for p in people], "year": year, "suffix": "", "title": title, "doi": "",
               "zotero": ""}
    doi = DOI_IN.search(str(parts.get("doi") or ""))
    if doi:
        ref["doi"] = pdftext.norm_doi(doi.group(1).rstrip(".,;)]"))
    key = str(parts.get("key") or "").strip()
    ref["zotero"] = key if re.fullmatch(r"[A-Z0-9]{8}", key) else ""
    return ref


def csv_refs(text: str, tabbed: bool) -> list[dict]:
    """A CSV's references: its columns found by their headings, Reference or Author, Year and Title among
    them, as Zotero, EndNote or Mendeley name them, else each row's first cell when it reads as an entry."""
    first = text.split("\n", 1)[0]
    delim = "\t" if tabbed or "\t" in first else (";" if first.count(";") > first.count(",") else ",")
    rows = [row for row in csv.reader(io.StringIO(text, newline=""), delimiter=delim) if any(c.strip() for c in row)]
    if not rows:
        return []
    head = [" ".join(h.replace("\ufeff", "").split()).lower() for h in rows[0]]
    at = {}
    for part, names in LIST_HEADS.items():
        for n in names:
            if n in head:
                at[part] = head.index(n)
                break
    out = []
    if "text" in at or "authors" in at or "title" in at:
        cell = lambda row, part: row[at[part]].strip() if part in at and at[part] < len(row) else ""
        for row in rows[1:]:
            people = persons(cell(row, "authors"))
            ref = entry_of({"text": cell(row, "text"), "people": people, "year": cell(row, "year"),
                            "title": cell(row, "title"), "journal": cell(row, "journal"), "doi": cell(row, "doi"),
                            "key": cell(row, "key")})
            if ref:
                out.append(ref)
        return out
    for row in rows:
        cellv = next((c.strip() for c in row if c.strip()), "")
        if YEAR_PAREN.search(cellv):
            out.append(parse_reference(" ".join(cellv.split())))
    return out


RIS_LINE = re.compile(r"^([A-Z][A-Z0-9])  -(?: (.*))?$")


def ris_refs(text: str) -> list[dict]:
    """An RIS file's references, Zotero's export among them: its authors, AU and A1, the year, PY, Y1 or
    DA, the title, TI or T1, the journal or book, the DOI, DO, or one in its address."""
    out, cur, last = [], None, None
    for raw in text.splitlines():
        m = RIS_LINE.match(raw.rstrip())
        if not m:
            if cur is not None and last and raw.strip():
                cur[last][-1] = f"{cur[last][-1]} {raw.strip()}"
            continue
        tag, value = m.group(1), (m.group(2) or "").strip()
        if tag == "TY":
            cur, last = {}, None
        elif tag == "ER":
            if cur is not None:
                out.append(cur)
            cur, last = None, None
        elif cur is not None:
            cur.setdefault(tag, []).append(value)
            last = tag
    refs = []
    for e in out:
        one = lambda *tags: next((v for t in tags for v in e.get(t, []) if v), "")
        people = e.get("AU", []) + e.get("A1", [])
        ref = entry_of({"people": people, "year": one("PY", "Y1", "DA"), "title": one("TI", "T1", "CT"),
                        "journal": one("T2", "JO", "JF", "JA", "BT", "PB"), "doi": one("DO", "UR", "L3"), "key": ""})
        if ref:
            refs.append(ref)
    return refs


def delatex(text: str) -> str:
    """BibTeX's words as they read: its accents made letters, its escapes and braces taken away."""
    s = str(text or "")
    s = re.sub(r"\{?\\([`'^\"~=.uvHcdbk])\s*\{?\s*([A-Za-z])\}?\}?",
               lambda m: unicodedata.normalize("NFC", m.group(2) + LATEX_MARKS[m.group(1)]), s)
    s = re.sub(r"\{?\\(ss|ae|AE|oe|OE|aa|AA|o|O|l|L|i)\b\}?", lambda m: LATEX_LETTERS[m.group(1)], s)
    s = re.sub(r"\\([&%$#_{}])", r"\1", s)
    s = s.replace("---", "–").replace("--", "–").replace("~", " ")
    s = re.sub(r"\\[A-Za-z]+\s*", "", s)
    return " ".join(s.replace("{", "").replace("}", "").split())


def bib_fields(rest: str) -> dict:
    """An entry's fields, each name and its value in braces, in quotes or bare."""
    fields, i, n = {}, 0, len(rest)
    name_at = re.compile(r"[\s,]*([A-Za-z][\w:-]*)\s*=\s*")
    while i < n:
        m = name_at.match(rest, i)
        if not m:
            break
        name, i = m.group(1).lower(), m.end()
        if i < n and rest[i] in "{\"":
            close, depth, j = rest[i], 0, i
            while j < n:
                ch = rest[j]
                if ch == "{":
                    depth += 1
                elif ch == "}":
                    depth -= 1
                    if close == "{" and depth == 0:
                        break
                elif ch == '"' and close == '"' and j > i and depth == 0:
                    break
                j += 1
            fields[name], i = rest[i + 1:j], j + 1
        else:
            m2 = re.compile(r"[^,]*").match(rest, i)
            fields[name], i = m2.group(0).strip(), m2.end()
    return fields


def bib_people(value: str) -> list[str]:
    """BibTeX's authors parted at and outside braces, each as Surname, Given: a group's name in braces whole,
    and a name written Given Surname turned, its particle kept with the surname."""
    parts, depth, word = [], 0, ""
    for token in re.split(r"(\s+and\s+|[{}])", value):
        if token == "{":
            depth += 1
        elif token == "}":
            depth -= 1
        if depth == 0 and re.fullmatch(r"\s+and\s+", token or ""):
            parts.append(word)
            word = ""
        else:
            word += token or ""
    parts.append(word)
    out = []
    for p in parts:
        p = p.strip()
        if not p:
            continue
        if p.startswith("{") and p.endswith("}") and p.count("{") == 1:
            out.append(delatex(p))
            continue
        flat = delatex(p)
        if "," in flat:
            out.append(flat)
            continue
        words = flat.split()
        at = next((k for k in range(1, len(words)) if words[k][:1].islower()), len(words) - 1)
        out.append(f"{' '.join(words[at:])}, {' '.join(words[:at])}".strip(" ,"))
    return out


def bib_refs(text: str) -> list[dict]:
    """A BibTeX file's references, Zotero's and Better BibTeX's exports among them."""
    refs, i, n = [], 0, len(text)
    while True:
        at = text.find("@", i)
        if at < 0:
            break
        m = re.compile(r"@\s*([A-Za-z]+)\s*([{(])").match(text, at)
        if not m:
            i = at + 1
            continue
        kind, opener = m.group(1).lower(), m.group(2)
        j, depth = m.end(), 1
        while j < n and depth:
            ch = text[j]
            if ch == "{":
                depth += 1
            elif ch == "}" or (opener == "(" and ch == ")" and depth == 1):
                depth -= 1
            j += 1
        body, i = text[m.end():j - 1], j
        if kind in ("comment", "string", "preamble"):
            continue
        _key, _, rest = body.partition(",")
        f = bib_fields(rest)
        people = bib_people(f.get("author") or f.get("editor") or "")
        ref = entry_of({"people": people, "year": f.get("year") or f.get("date") or "",
                        "title": delatex(f.get("title") or ""),
                        "journal": delatex(f.get("journal") or f.get("journaltitle") or f.get("booktitle")
                                           or f.get("publisher") or f.get("school") or f.get("institution") or ""),
                        "doi": f.get("doi") or f.get("url") or "", "key": ""})
        if ref:
            refs.append(ref)
    return refs


def title_order(title: str) -> str:
    return re.sub(r"^(?:a|an|the)\s+", "", re.sub(r"[^a-z0-9 ]", "", str(title or "").lower()))


def lettered(refs: list[dict]) -> list[dict]:
    """The letters APA gives the works of the same authors in the same year, a, b and on in the order of
    their titles, for a list a reference manager wrote with none."""
    groups: dict[tuple, list[dict]] = {}
    for r in refs:
        if r["suffix"] or not r["names"] or not r["year"]:
            continue
        groups.setdefault((tuple(fold(n) for n in r["names"]), r["year"]), []).append(r)
    for same in groups.values():
        if len(same) > 1:
            for k, r in enumerate(sorted(same, key=lambda x: title_order(x["title"]))[:26]):
                r["suffix"] = "abcdefghijklmnopqrstuvwxyz"[k]
    return refs


def read_list(path) -> list[dict]:
    """A reference list alone, CSV, RIS or BibTeX, read and never written, each reference keyed as an
    entry of a manuscript's list is."""
    target = Path(path)
    kind = LIST_KINDS.get(target.suffix.lower())
    if kind is None:
        raise TraceError(_w("NOT_KIND"))
    text = textfiles.decode(read_bytes(target)).replace("\r\n", "\n").replace("\r", "\n")
    refs = csv_refs(text, target.suffix.lower() == ".tsv") if kind == "csv" else ris_refs(text) if kind == "ris" else bib_refs(text)
    return keyed(lettered(refs))


def list_of(folder) -> dict | None:
    """The project's reference list as kept, its path where it now stands, its name and the day it was
    added, or None."""
    held = read_project(folder).get("list")
    if not isinstance(held, dict) or not held.get("path"):
        return None
    return {"path": str(located(folder, held)), "name": str(held.get("name") or Path(str(held["path"])).name),
            "added": str(held.get("added") or "")}


def listed(folder) -> list[dict] | None:
    """The project's reference list read afresh, or None with none or one no longer there."""
    held = list_of(folder)
    if held is None:
        return None
    try:
        return read_list(held["path"])
    except TraceError:
        return None


def set_list(folder, path) -> dict:
    """A reference list for the project, read once to be sure it holds references and never written, kept
    in its own file in place of one before."""
    target = Path(path).expanduser()
    if not target.is_file():
        raise TraceError(_w("NOT_THERE"))
    target = target.resolve()
    if not read_list(target):
        raise TraceError(_w("NO_LIST_REFS"))
    with locks.held(lock_path(folder)):
        data = read_project(folder) or {"name": own_name(folder)}
        data["list"] = {"path": str(target), "relative": from_folder(folder, target), "name": target.name,
                        "added": now_iso()}
        write_atomic(project_file(folder), dumps(data))
    return list_of(folder)


# ------------------------------------------------------------------- the citations

YEARS = rf"{YEARS_ONE}(?:\s*,\s*{YEARS_ONE})*"
ITEM = re.compile(rf"^(?P<names>.+?),\s*(?P<years>{YEARS})(?P<rest>(?:\s*,\s*.*)?)$", re.I | re.S)
LEAD = re.compile(r"^(?:e\.g\.,?|i\.e\.,?|see also|see|cf\.|for example,?|for a review,? see|for reviews,? see|"
                  r"reviewed in|as in|also|but see|compare|and)\s+", re.I)
NAME_WORD = (r"(?:[A-ZÀ-Þ][\w'’\-À-ɏ]*|(?:van|von|de|der|den|du|da|di|del|della|le|la|ten|ter)(?=\s))")
NAMES = rf"{NAME_WORD}(?:\s+{NAME_WORD})*"
NARRATIVE = re.compile(rf"(?P<names>{NAMES}(?:\s+et\s+al\.|(?:,\s+{NAMES})*,?\s+(?:and|&)\s+{NAMES})?)(?:['’]s?)?"
                       rf"(?:\s*\[(?P<alias>[A-Z][A-Za-z&.]{{1,15}})\])?\s+\((?P<years>{YEARS})(?P<rest>(?:\s*,\s*[^()]*)?)\)")
# a group's abbreviation alone in a bracket, after the group's name in the sentence, British Beekeepers
# Union (BBU, 2018), as APA writes a group's first narrative citation
ABBR = re.compile(r"^[A-Z][A-Z&]{1,9}$")
BEFORE = re.compile(rf"((?:{NAME_WORD}\s+){{0,7}}{NAME_WORD})\s*$")
PAGE = re.compile(r"\b(pp?\.\s*[\dxivlc]+(?:\s*[–-]\s*[\dxivlc]+)?|paras?\.\s*\d+(?:\s*[–-]\s*\d+)?|"
                  r"(?:chap(?:ter)?|ch)\.?\s*\d+|section\s+[\d.]+|table\s+\d+|figure\s+\d+)", re.I)
# a word that opens a sentence before a name, never a name of its own
OPENERS = {"in", "as", "however", "the", "this", "these", "that", "according", "following", "while", "both",
           "unlike", "like", "per", "by", "for", "since", "when", "although", "thus", "here", "recently",
           "similarly", "indeed", "moreover", "furthermore", "notably", "earlier", "later", "building", "drawing",
           "after", "before", "where", "whereas", "yet", "but", "so", "and", "or", "also", "then", "on", "with",
           "from", "to", "of", "at", "see", "we", "i", "our", "my", "their", "his", "her", "its", "a", "an",
           "using", "under", "within", "across", "between", "among", "because", "if", "once", "until",
           "even", "only", "still", "first", "second", "third", "finally", "lastly", "next"}
ABBREV = {"al", "e.g", "i.e", "p", "pp", "cf", "vs", "fig", "figs", "no", "nos", "vol", "vols", "ed", "eds", "dr", "mr",
          "mrs", "ms", "st", "approx", "ch", "chap", "para", "paras", "trans", "rev", "n.d", "et", "c", "ca", "viz"}
# A sentence that leans on the one before it: one that opens by pointing back, This, These, It, Such, or
# carries it on, However, Moreover, For example, so the claim it makes of its reference is the two together
LEANS = re.compile(r"^[\"'“‘(\[]*(?:this|these|that|those|it|its|they|their|them|such|both|each|neither|either|"
                   r"another|here|he|she|his|her|however|moreover|furthermore|also|additionally|similarly|likewise|"
                   r"thus|hence|therefore|consequently|accordingly|yet|but|and|still|indeed|instead|again|otherwise|"
                   r"then|nevertheless|nonetheless|conversely|in addition|in turn|in particular|in contrast|"
                   r"by contrast|for example|for instance|as a result|even so|taken together|together|"
                   r"on the other hand|at the same time|to this end|in this way|the latter|the former|the same)\b", re.I)
CLOSES = re.compile(r"[\s)\].,;:!?\"'”’]*")


def years_of(text: str) -> list[tuple[str, str]]:
    out = []
    for y in re.split(r"\s*,\s*", text.strip()):
        m = re.match(r"^(\d{4}|n\.\s?d\.|in press)(?:-?([a-z]))?$", y.strip(), re.I)
        if m:
            year = m.group(1).lower().replace(" ", "")
            out.append(({"n.d.": "n.d.", "inpress": "in press"}.get(year, year), (m.group(2) or "").lower()))
    return out


def names_of(text: str) -> tuple[list[str], bool, str]:
    """The names a citation gives, whether it says et al., and a group's abbreviation in square
    brackets, World Health Organization [WHO], which a later citation may give alone."""
    s = " ".join(text.split())
    alias = ""
    m = re.search(r"\s*\[([A-Z][A-Za-z0-9&.\- ]{0,20})\]\s*$", s)
    if m:
        alias, s = m.group(1).strip(), s[:m.start()].strip()
    etal = bool(re.search(r"\bet\s+al\.?$", s))
    s = re.sub(r",?\s*\bet\s+al\.?$", "", s).strip()
    parts = [p.strip() for p in re.split(r"\s*,\s*(?:&\s*|and\s+)?|\s+(?:&|and)\s+", s) if p and p.strip()]
    return parts, etal, alias


def plausible(names: list[str]) -> bool:
    """Whether a bracket's words before its year are names: each opens with a capital or a name's
    particle, none holds a digit, and none runs past six words."""
    if not names:
        return False
    for n in names:
        if re.search(r"\d", n) or len(n.split()) > 6:
            return False
        if not (n[0].isupper() or re.match(r"^(?:van|von|de|der|den|du|da|di|del|della|le|la|ten|ter)\s", n)):
            return False
    return True


def page_of(rest: str) -> str:
    m = PAGE.search(rest or "")
    return " ".join(m.group(1).split()) if m else ""


def cited_as(names: list[str], etal: bool, years: list[tuple[str, str]], page: str = "") -> str:
    """A citation as APA writes it in a bracket, Smith et al., 2020."""
    if etal:
        who = f"{names[0]} et al."
    elif len(names) == 2:
        who = f"{names[0]} & {names[1]}"
    elif len(names) > 2:
        who = f"{', '.join(names[:-1])}, & {names[-1]}"
    else:
        who = names[0] if names else ""
    return f"{who}, {', '.join(y + s for y, s in years)}" + (f", {page}" if page else "")


def short_of(ref: dict) -> str:
    """A reference as a citation names it, Quint et al., 2022, for the table and the filters."""
    n = ref.get("names") or []
    if not n:
        return f"{(ref.get('text') or '')[:40]}"
    who = f"{n[0]} et al." if len(n) > 2 else f"{n[0]} & {n[1]}" if len(n) == 2 else n[0]
    return f"{who}, {ref.get('year') or 'n.d.'}{ref.get('suffix') or ''}"


def brackets(text: str) -> list[tuple[int, int]]:
    """Each bracket's inside in a paragraph, its start and end, the outermost of nested ones."""
    out, depth, start = [], 0, 0
    for i, ch in enumerate(text):
        if ch == "(":
            if depth == 0:
                start = i + 1
            depth += 1
        elif ch == ")" and depth:
            depth -= 1
            if depth == 0:
                out.append((start, i))
    return out


def sentences(text: str) -> list[tuple[int, int]]:
    """A paragraph's sentences as their start and end, a stop inside a bracket, after an abbreviation
    or after an initial never ending one."""
    spans, start, depth, i, n = [], 0, 0, 0, len(text)
    while i < n:
        ch = text[i]
        if ch in "([":
            depth += 1
        elif ch in ")]":
            depth = max(0, depth - 1)
        elif ch in ".!?" and depth == 0:
            j = i + 1
            while j < n and text[j] in "\"'”’)]":
                j += 1
            if j >= n or text[j].isspace():
                k = j
                while k < n and text[k].isspace():
                    k += 1
                if k >= n or text[k].isupper() or text[k].isdigit() or text[k] in "\"'“‘([":
                    word = re.search(r"([A-Za-z.]+)$", text[start:i])
                    w = word.group(1) if word else ""
                    if not (ch == "." and (w.lower().rstrip(".") in ABBREV or re.fullmatch(r"[A-Z]", w))):
                        spans.append((start, j))
                        start = k
                        i = k
                        continue
        i += 1
    if text[start:].strip():
        spans.append((start, n))
    return spans


def citations_in(text: str) -> list[dict]:
    """Every citation in a paragraph in order: `at`, where it stands, `end`, where its bracket closes,
    `names`, `etal`, `alias`, `years`, `page` and `narrative`, the author and year forms APA writes."""
    out: list[dict] = []
    for a, b in brackets(text):
        inside = text[a:b]
        for k, part in enumerate(re.split(r"\s*;\s*", inside)):
            for piece in re.split(r",?\s+as cited in\s+", part):
                item = piece.strip()
                while LEAD.match(item):
                    item = LEAD.sub("", item, count=1).strip()
                m = ITEM.match(item)
                if not m:
                    continue
                names, etal, alias = names_of(m.group("names"))
                years = years_of(m.group("years"))
                if not plausible(names) or not years:
                    continue
                before = BEFORE.search(text[:max(0, a - 1)]) if k == 0 and len(names) == 1 and ABBR.match(names[0]) else None
                out.append({"at": a + inside.find(piece) if piece in inside else a, "end": b + 1, "names": names,
                            "etal": etal, "alias": alias, "years": years, "page": page_of(m.group("rest")),
                            "narrative": False, "named": before.group(1) if before else ""})
    for m in NARRATIVE.finditer(text):
        names, etal, alias = names_of(m.group("names"))
        years = years_of(m.group("years"))
        if names and years:
            out.append({"at": m.start(), "end": m.end(), "names": names, "etal": etal, "alias": m.group("alias") or alias,
                        "years": years, "page": page_of(m.group("rest")), "narrative": True, "named": ""})
    return sorted(out, key=lambda c: c["at"])


def leans(sentence: str) -> bool:
    """Whether a sentence opens by pointing back to the one before it."""
    return bool(LEANS.match(sentence.strip()))


# ---------------------------------------------------------------------- matching

def match(cite: dict, year: str, suffix: str, refs: list[dict], aliases: dict) -> dict | None:
    """The reference a citation of one year names: the year and its letter the same and the first
    author's surname, a two-author citation's second too and et al. three or more, a group by its name
    or its abbreviation. A narrative citation's opening words that are no name, In Smith (2020), are let
    go one at a time until a reference answers. None when no reference answers or two answer alike."""
    names = list(cite["names"])
    tries = [names]
    if cite["narrative"]:
        first = names[0].split()
        for k in range(1, len(first)):
            tries.append([" ".join(first[k:])] + names[1:])
        if len(names) > 1:
            tries.append(names[1:])
    for given in tries:
        if not given:
            continue
        lead = fold(aliases.get(given[0], given[0]))
        found = [r for r in refs if r["year"] == year and r["suffix"] == suffix and r["names"]
                 and fold(r["names"][0]) == lead]
        if not found:
            continue
        if cite["etal"]:
            best = [r for r in found if len(r["names"]) >= 3] or found
        elif len(given) == 2:
            second = fold(given[1])
            best = ([r for r in found if len(r["names"]) == 2 and fold(r["names"][1]) == second]
                    or [r for r in found if second in [fold(x) for x in r["names"][1:]]])
        elif len(given) > 2:
            best = [r for r in found if [fold(x) for x in r["names"][:len(given)]] == [fold(x) for x in given]] or found
        else:
            best = [r for r in found if len(r["names"]) == 1] or found
        if len(best) == 1:
            return best[0]
        if best:
            return None
    return None


def clean_names(cite: dict) -> list[str]:
    """A narrative citation's names with the words that open its sentence let go, for its row when no
    reference answers it."""
    names = list(cite["names"])
    if cite["narrative"] and names:
        words = names[0].split()
        while len(words) > 1 and words[0].lower() in OPENERS:
            words = words[1:]
        names[0] = " ".join(words)
        if len(names) > 1 and names[0].lower() in OPENERS:
            names = names[1:]
    return names


def claim_hash(sentence: str) -> str:
    """A claim's sentence as its key holds it, its letters and digits alone, so a change of spacing keeps
    his judgement and a change of words asks for a new one."""
    flat = re.sub(r"[^a-z0-9]", "", unicodedata.normalize("NFKD", sentence).encode("ascii", "ignore").decode().lower())
    return hashlib.sha1(flat.encode("utf-8")).hexdigest()[:8]


def claims_of(cites: list[dict]) -> list[dict]:
    """The citing sentences once each, in order, each with its section, the sentence before it where it
    leans on it, and every form it cites the reference in, so a sentence that cites it twice is one claim."""
    out: dict[str, dict] = {}
    for c in cites:
        held = out.setdefault(c["sentence"], {"section": c["section"], "sentence": c["sentence"], "before": "",
                                              "as": [], "at": c["at"]})
        if c["as"] not in held["as"]:
            held["as"].append(c["as"])
        if c["before"] and not held["before"]:
            held["before"] = c["before"]
    return list(out.values())


def enrich(own: list[dict], listed_refs: list[dict]) -> None:
    """A manuscript's own references given the DOI and the Zotero item of the same reference in the
    project's list, by its first surname, year and letter, where its own entry has none."""
    by = {}
    for r in listed_refs:
        by.setdefault((fold(r["names"][0]) if r["names"] else "", r["year"], r["suffix"]), []).append(r)
    for r in own:
        same = by.get((fold(r["names"][0]) if r["names"] else "", r["year"], r["suffix"])) or []
        if len(same) == 1:
            if not r.get("doi") and same[0].get("doi"):
                r["doi"] = same[0]["doi"]
            if not r.get("zotero") and same[0].get("zotero"):
                r["zotero"] = same[0]["zotero"]


def analyse(path, listed_refs: list[dict] | None = None) -> dict:
    """A manuscript read: `references`, its own reference list in order, or with none the project's,
    each with its key, words, surnames, year and letter, title, DOI, `cites`, each citation with its
    sentence, section and form, and `claims`, its citing sentences once each, then `missing`, each citation
    no reference answers, by its form, `claims`, every claim in the manuscript's order, each reference's or
    a missing citation's, `sections`, the headings in order, `listed`, whether there are references to
    match, and `source`, document or list."""
    blocks = blocks_of(path)
    span = ref_section(blocks)
    refs: list[dict] = []
    if span:
        for b in blocks[span[0] + 1:span[1]]:
            if b["kind"] != "para":
                continue
            for entry in entries_of(b["lines"]):
                entry = " ".join(md_inline(entry).split()) if b.get("md") else entry
                if YEAR_PAREN.search(entry) or re.search(r"\b(?:1[5-9]|20)\d{2}[a-z]?\b", entry):
                    refs.append(parse_reference(entry))
    source = "document" if refs else ""
    if refs and listed_refs:
        enrich(refs, listed_refs)
    elif not refs and listed_refs:
        refs = [dict(r) for r in listed_refs]
        source = "list"
    keyed(refs)
    for r in refs:
        r["cites"] = []
    body = [(i, b) for i, b in enumerate(blocks) if source != "document" or not span or not (span[0] <= i < span[1])]
    aliases: dict[str, str] = {}
    missing: dict[str, dict] = {}
    sections: list[str] = []
    heading = NO_HEADING
    for i, b in body:
        if b["kind"] == "heading":
            heading = b["text"]
            continue
        cites = citations_in(b["text"])
        if not cites:
            continue
        if heading not in sections:
            sections.append(heading)
        spans = sentences(b["text"])
        for c in cites:
            if c["alias"]:
                aliases[c["alias"]] = clean_names(c)[0]
            if c["named"] and c["names"][0] not in aliases:
                # the group's name before its abbreviation, its opening words let go until a group answers
                words = c["named"].split()
                for k in range(len(words)):
                    if any(r["names"] and fold(r["names"][0]) == fold(" ".join(words[k:])) for r in refs):
                        aliases[c["names"][0]] = " ".join(words[k:])
                        break
            s = next((k for k, (x, y) in enumerate(spans) if x <= c["at"] < y), None)
            x, y = spans[s] if s is not None else (0, len(b["text"]))
            said = " ".join(b["text"][x:y].split())
            # the sentence before, where the citation closes a sentence that leans on it
            before = ""
            if s and leans(said) and CLOSES.fullmatch(b["text"][min(c["end"], y):y] or ""):
                before = " ".join(b["text"][spans[s - 1][0]:spans[s - 1][1]].split())
            names = clean_names(c)
            for year, suffix in c["years"]:
                one = {"section": heading, "sentence": said, "before": before,
                       "as": cited_as(names, c["etal"], [(year, suffix)], c["page"]), "page": c["page"], "at": [i, c["at"]]}
                ref = match(c, year, suffix, refs, aliases)
                if ref is not None:
                    ref["cites"].append(one)
                    continue
                if c["narrative"] and not all(re.search(r"[a-z]", n) and not re.search(r"\d", n) for n in names):
                    # words in capitals or with a digit before a year in a bracket, COVID-19 (2020), that no
                    # reference answers, are no citation
                    continue
                form = cited_as(names, c["etal"], [(year, suffix)])
                key = "cite:" + ascii_word(form)
                held = missing.setdefault(key, {"key": key, "as": form, "cites": []})
                held["cites"].append(one)
    claims: list[dict] = []
    for r in refs:
        r["count"] = len(r["cites"])
        r["claims"] = claims_of(r["cites"])
        for c in r["claims"]:
            c["ref"] = r["key"]
            c["key"] = f"{r['key']}~{claim_hash(c['sentence'])}"
            claims.append(c)
    miss = list(missing.values())
    for m in miss:
        m["count"] = len(m["cites"])
        m["claims"] = claims_of(m["cites"])
        for c in m["claims"]:
            c["ref"] = ""
            c["missing"] = m["as"]
            c["key"] = f"{m['key']}~{claim_hash(c['sentence'])}"
            claims.append(c)
    claims.sort(key=lambda c: (c["at"][0], c["at"][1]))
    return {"references": refs, "missing": miss, "claims": claims, "sections": sections, "listed": bool(refs),
            "source": source}


# ------------------------------------------------------------------------ the PDFs

def alnum(text) -> str:
    return re.sub(r"[^a-z0-9]", "", unicodedata.normalize("NFKC", str(text or "")).lower())


FIRST_PAGES: dict[tuple, str] = {}
SCREENINGS_READ: dict[tuple, list] = {}


def first_page(path: Path) -> str:
    """A PDF's first page's text, read once for each size and time it has."""
    try:
        st = path.stat()
        key = (str(path), st.st_size, st.st_mtime_ns)
        if key not in FIRST_PAGES:
            FIRST_PAGES[key] = pdftext.first_page_text(path.read_bytes()) if st.st_size <= PDF_MAX else ""
        return FIRST_PAGES[key]
    except OSError:
        return ""


def screening_hits(folder: Path) -> list[dict]:
    """A screening's records as the PDF lookup takes them, each its PDF, Zotero item, DOI and title, read
    once for each size and time its CSV has."""
    csv_file = Path(folder) / screenings.CSV_NAME
    try:
        st = csv_file.stat()
    except OSError:
        return []
    key = (str(csv_file), st.st_size, st.st_mtime_ns)
    if key not in SCREENINGS_READ:
        try:
            sc = screenings.load(folder)
        except (ScreeningError, OSError):
            return []
        base = folder.parent.parent if folder.parent.name == screenings.RUNS_DIR else folder
        SCREENINGS_READ[key] = [{"rec": rec, "zotero": sc.cell(rec, screenings.ZOTERO_COLUMN).strip(),
                                 "doi": pdftext.norm_doi(sc.cell(rec, "doi")), "title": pdftext.norm_title(sc.cell(rec, "title")),
                                 "base": str(base)} for rec in sc.ids]
    out = []
    for h in SCREENINGS_READ[key]:
        out.append(dict(h, pdf=screenings.pdf_path(folder, h["rec"])))
    return out


def legacy_screenings(folder) -> list[Path]:
    """For Sift's step of 14 October, the screenings of the Sift project that holds it, its own and each
    run's, newest run first."""
    folder = Path(folder)
    if not is_legacy(folder):
        return []
    return screenings.of_review(folder.parent)


def pdf_index(folder, screenings=()) -> dict:
    """What finds a reference's PDF: the PDFs in the project's `pdfs/`, and each record's PDF and Zotero item
    in the screenings given, by its DOI and by its title."""
    files = []
    base = pdf_folder(folder)
    if base.is_dir():
        files = sorted(p for p in base.iterdir() if p.is_file() and p.suffix.lower() == ".pdf" and not p.name.startswith("."))
    by_doi: dict[str, dict] = {}
    by_title: dict[str, dict] = {}
    seen = set()
    for screening in list(legacy_screenings(folder)) + [Path(s) for s in screenings]:
        try:
            mark = Path(screening).resolve()
        except OSError:
            continue
        if mark in seen:
            continue
        seen.add(mark)
        for hit in screening_hits(Path(screening)):
            for held, key in ((by_doi, hit["doi"]), (by_title, hit["title"])):
                if key and len(key) > 6:
                    was = held.get(key)
                    if was is None or (not was["pdf"] and hit["pdf"]) or (not was["zotero"] and hit["zotero"] and bool(was["pdf"]) == bool(hit["pdf"])):
                        held[key] = hit
    return {"files": files, "doi": by_doi, "title": by_title}


def pdf_for(folder, ref: dict, index: dict) -> dict:
    """A reference's PDF and Zotero item: `path`, `from`, `folder` for one in the project's pdfs/, by its key
    or its DOI in the file's name or on its first page, or `screening` for a record's, `name`, where it
    stands with forward slashes, and `zotero`, the item the list or Sift's export gave it."""
    record = None
    if ref.get("doi"):
        record = index["doi"].get(ref["doi"])
    if record is None and ref.get("title"):
        record = index["title"].get(pdftext.norm_title(ref["title"]))
    out = {"path": None, "from": "", "name": "", "zotero": ref.get("zotero") or (record or {}).get("zotero", "")}
    doi = alnum(ref.get("doi"))
    hit = next((p for p in index["files"] if p.stem.lower() == str(ref.get("key", "")).lower()), None)
    if hit is None and doi:
        hit = (next((p for p in index["files"] if doi in alnum(p.stem)), None)
               or next((p for p in index["files"] if doi in alnum(first_page(p))), None))
    if hit is not None:
        return dict(out, path=hit, name=rel_name(folder, hit), **{"from": "folder"})
    if record and record.get("pdf"):
        return dict(out, path=record["pdf"], name=rel_name(record["base"], record["pdf"]), **{"from": "screening"})
    return out


def known_refs(folder, doc=None) -> list[dict]:
    """The references a PDF may be added for: the manuscript's, or with none the project's list."""
    if doc:
        entry = doc_entry(folder, doc)
        return analyse(entry["path"], listed(folder))["references"]
    return listed(folder) or []


def save_pdf(folder, doc, ref_key, data: bytes) -> dict:
    """A PDF he adds for a reference, kept as `pdfs/<key>.pdf` through a temporary file, never over a file
    there, and only when it is a PDF."""
    keys = {r["key"] for r in known_refs(folder, doc)}
    if ref_key not in keys:
        raise TraceError(_w("NO_REF"))
    if not pdftext.is_pdf(data):
        raise TraceError(_w("NOT_PDF"))
    with locks.held(lock_path(folder)):
        base = pdf_folder(folder)
        base.mkdir(parents=True, exist_ok=True)
        target = base / f"{ref_key}.pdf"
        if target.exists():
            raise TraceError(_w("PDF_THERE"))
        tmp = base / f".{ref_key}.pdf.tmp"
        tmp.write_bytes(data)
        tmp.replace(target)
    return {"saved": True}


def pdf_path(folder, doc, ref, screenings=()) -> Path:
    """A reference's PDF, found as the table finds it, refused in one line when it has none."""
    r = next((x for x in known_refs(folder, doc) if x["key"] == ref), None)
    if r is None:
        raise TraceError(_w("NO_REF"))
    found = pdf_for(folder, r, pdf_index(folder, screenings))["path"]
    if found is None:
        raise TraceError(_w("NO_PDF"))
    return Path(found)


# ------------------------------------------------------------------------ the log

def read_lines(folder, doc) -> list[dict]:
    path = log_path(folder, doc)
    if not path.is_file():
        return []
    out = []
    for line in path.read_text(encoding="utf-8").splitlines():
        try:
            entry = json.loads(line) if line.strip() else None
        except ValueError:
            continue
        if isinstance(entry, dict) and entry.get("act"):
            out.append(entry)
    return out


def append(folder, doc, entry: dict) -> None:
    """One line added to the end of the log, flushed to the disk, nothing before it touched."""
    path = log_path(folder, doc)
    with open(path, "ab") as fh:
        if fh.tell() > 0:
            with open(path, "rb") as held:
                held.seek(-1, 2)
                if held.read(1) != b"\n":
                    fh.write(b"\n")
        fh.write((json.dumps(entry, ensure_ascii=False) + "\n").encode("utf-8"))
        fh.flush()
        os.fsync(fh.fileno())


UNDOABLE = ("judge", "note")


def undoable(entry: dict) -> bool:
    return entry.get("act") in UNDOABLE and bool(entry.get("claim"))


def undo_target(lines: list[dict]) -> dict | None:
    """The newest judgement or note not yet undone, which Undo takes back."""
    undone = {e.get("undoes") for e in lines if e.get("act") == "undo"}
    for entry in reversed(lines):
        if undoable(entry) and entry.get("n") not in undone:
            return entry
    return None


BLANK = {"judged": "", "set": "", "note": ""}


def states(lines: list[dict]) -> dict:
    """Each claim's judgement, the day he gave it and his note, and each reference's newest passages, from
    the log, his acts undone passed over. Sift's Checked lines of 14 October are history alone, and its
    pointer is read as passages."""
    undone = {e.get("undoes") for e in lines if e.get("act") == "undo"}
    claims: dict[str, dict] = {}
    found: dict[str, dict] = {}
    for e in lines:
        if e.get("n") in undone:
            continue
        if undoable(e):
            st = claims.setdefault(str(e["claim"]), dict(BLANK))
            if e["act"] == "judge":
                st["judged"] = e.get("judged") if e.get("judged") in JUDGEMENTS else ""
                st["set"] = str(e.get("at") or "")[:10] if st["judged"] else ""
            else:
                st["note"] = str(e.get("note") or "")
        elif e.get("act") in ("passages", "pointer") and e.get("ref"):
            held = e.get("passages") if e.get("act") == "passages" else e.get("pointer")
            found[str(e["ref"])] = held if isinstance(held, dict) else None
    return {"claims": claims, "passages": found}


def claim_state(held: dict, key: str) -> dict:
    return dict(held["claims"].get(key) or BLANK)


def passage_for(passages: dict | None, claim: dict) -> dict | None:
    """The passage a reference's passages hold for one claim, by its key, or for Sift's pointer by its
    sentence."""
    if not isinstance(passages, dict):
        return None
    for c in passages.get("claims") or []:
        if c.get("claim") == claim["key"] or (not c.get("claim") and c.get("said") == claim["sentence"]):
            return c
    return None


def judge_words(entry: dict) -> str:
    """What a judgement's line says, in plain words: the researcher's, and with the AI's passages shown,
    what they found for this claim."""
    out = f"{RESEARCHER} judged it {JUDGEMENTS.get(entry.get('judged'), 'nothing')}"
    seen = entry.get("passages_shown")
    if isinstance(seen, dict):
        what = ("a passage found" if seen.get("found") else "its passage not in the PDF" if seen.get("unverified")
                else "no passage found")
        out += f", with the AI's passages shown, {seen.get('model') or 'a model'}, {what}"
    return out


def check_words(entry: dict) -> str:
    """A Checked line of Sift's step of 14 October in words, as its history lists it."""
    word = "checked" if entry.get("checked") == "Y" else "not checked"
    return f"The screener set the reference {word} in Sift"


def undo_said(lines: list[dict]) -> dict | None:
    target = undo_target(lines)
    if target is None:
        return None
    return {"claim": target.get("claim"), "ref": target.get("ref"), "what": target["act"], "n": target.get("n")}


# ----------------------------------------------------------------------- the view

def ref_rows(folder, refs: list[dict], index: dict) -> dict:
    return {r["key"]: pdf_for(folder, r, index) for r in refs}


def ref_cells(r: dict, pdf: dict) -> dict:
    """What a row says of its reference."""
    return {"ref": r["key"], "reference": r["text"], "short": short_of(r), "names": r["names"],
            "year": r["year"] + r["suffix"], "doi": r["doi"], "title": r["title"], "pdf": pdf["path"] is not None,
            "pdf_from": pdf["from"], "pdf_name": pdf["name"], "zotero": pdf["zotero"]}


def rows(folder, doc, analysis: dict | None = None, screenings=()) -> dict:
    """A manuscript's rows as the screen draws them, in its order: each claim, its sentence, the sentence
    before where it leans on it, its section, the forms it cites in, its reference with its PDF and Zotero
    item, his judgement, the day and his note, the passage the AI found for it, and how many of its
    reference's claims he has judged, then a row for each citation no reference answers within that order,
    and a row for each reference never cited at the end."""
    entry = doc_entry(folder, doc)
    got = analysis if analysis is not None else analyse(entry["path"], listed(folder))
    lines = read_lines(folder, doc)
    held = states(lines)
    pdfs = ref_rows(folder, got["references"], pdf_index(folder, screenings))
    by = {r["key"]: r for r in got["references"]}
    tally: dict[str, list[int]] = {}
    for c in got["claims"]:
        if c["ref"]:
            t = tally.setdefault(c["ref"], [0, 0])
            t[0] += 1
            t[1] += 1 if claim_state(held, c["key"])["judged"] else 0
    out = []
    for c in got["claims"]:
        st = claim_state(held, c["key"])
        row = {"key": c["key"], "sentence": c["sentence"], "before": c["before"], "section": c["section"], "as": c["as"],
               "judged": st["judged"], "set": st["set"], "note": st["note"]}
        if c["ref"]:
            r = by[c["ref"]]
            found = held["passages"].get(r["key"])
            row.update(ref_cells(r, pdfs[r["key"]]), kind="claim", passage=passage_for(found, c),
                       passages={k: found.get(k) for k in ("model", "asked", "found", "of")} if found else None,
                       ref_claims=tally[r["key"]][0], ref_judged=tally[r["key"]][1])
        else:
            row.update(kind="missing", ref="", reference="", short=c["missing"], names=[], year="", doi="", title="",
                       pdf=False, pdf_from="", pdf_name="", zotero="", passage=None, passages=None, ref_claims=0,
                       ref_judged=0)
        out.append(row)
    for r in got["references"]:
        if r["count"]:
            continue
        out.append(dict(ref_cells(r, pdfs[r["key"]]), key=r["key"], kind="uncited", sentence="", before="", section="",
                        **{"as": []}, judged="", set="", note="", passage=None, passages=None, ref_claims=0, ref_judged=0))
    return {"doc": entry["doc"], "name": entry["name"], "path": entry["path"], "rows": out, "sections": got["sections"],
            "listed": got["listed"], "source": got["source"], "undo": undo_said(lines)}


def list_rows(folder, screenings=()) -> dict:
    """The project's reference list alone, before any manuscript: a row for each reference with its PDF and
    Zotero item, and no claim."""
    refs = listed(folder) or []
    pdfs = ref_rows(folder, refs, pdf_index(folder, screenings))
    out = [dict(ref_cells(r, pdfs[r["key"]]), key=r["key"], kind="uncited", sentence="", before="", section="",
                **{"as": []}, judged="", set="", note="", passage=None, passages=None, ref_claims=0, ref_judged=0)
           for r in refs]
    return {"doc": "", "name": "", "path": "", "rows": out, "sections": [], "listed": bool(refs), "source": "list",
            "undo": None}


def counts(view: dict) -> dict:
    claims = [r for r in view["rows"] if r["kind"] == "claim"]
    refs = {r["ref"]: r for r in view["rows"] if r["kind"] in ("claim", "uncited")}
    return {"claims": len(claims), "judged": sum(1 for r in claims if r["judged"]),
            "supports": sum(1 for r in claims if r["judged"] == SUPPORTS),
            "question": sum(1 for r in claims if r["judged"] == QUESTION),
            "not_supported": sum(1 for r in claims if r["judged"] == NOT_SUPPORTED),
            "not_judged": sum(1 for r in claims if not r["judged"]),
            "no_reference": sum(1 for r in view["rows"] if r["kind"] == "missing"),
            "never_cited": sum(1 for r in view["rows"] if r["kind"] == "uncited"),
            "references": len(refs), "pdf": sum(1 for r in refs.values() if r["pdf"])}


def write_state(folder, doc, analysis: dict | None = None) -> None:
    """`<doc>.json` written afresh from the log and the manuscript as it now reads, when it changed: the
    manuscript's path and name, each claim in its order with its reference, section, sentence, the
    sentence before where it leans on it, his judgement in words, the day and his note, a claim he judged
    that the manuscript no longer holds kept at the end, each citation no reference answers, each
    reference never cited, the AI's passages by reference with their model, and the counts the home
    screen's card reads."""
    path = state_path(folder, doc)
    data = read_json(path)
    if not data.get("document"):
        raise TraceError(_w("NO_DOC"))
    got = analysis if analysis is not None else analyse(located(folder, data), listed(folder))
    held = states(read_lines(folder, doc))
    claims, keys = [], set()
    for c in got["claims"]:
        keys.add(c["key"])
        if not c["ref"]:
            continue
        st = claim_state(held, c["key"])
        one = {"key": c["key"], "reference": c["ref"], "section": c["section"], "claim": c["sentence"]}
        if c["before"]:
            one["before"] = c["before"]
        one.update(judged=JUDGEMENTS.get(st["judged"], ""), set=st["set"], note=st["note"])
        claims.append(one)
    for key, st in held["claims"].items():
        if key not in keys and (st["judged"] or st["note"]):
            claims.append({"key": key, "reference": key.split("~", 1)[0], "in_document": False,
                           "judged": JUDGEMENTS.get(st["judged"], ""), "set": st["set"], "note": st["note"]})
    judged = sum(1 for c in claims if c.get("judged") and c.get("in_document") is not False)
    fresh = {k: v for k, v in data.items() if k not in ("references", "no_reference")}
    fresh.update(claims=claims,
                 no_reference=[{"cited_as": c["missing"], "claim": c["sentence"]} for c in got["claims"] if not c["ref"]],
                 never_cited=[r["key"] for r in got["references"] if not r["count"]],
                 passages={k: v for k, v in held["passages"].items() if v},
                 counts={"claims": sum(1 for c in got["claims"] if c["ref"]), "judged": judged})
    text = dumps(fresh)
    try:
        if path.read_text(encoding="utf-8") == text:
            return
    except OSError:
        pass
    write_atomic(path, text)


def refresh(folder, doc, analysis: dict | None = None) -> None:
    """The readable file brought up to the manuscript as it now reads, under the project's lock, as the
    screen reads it."""
    with locks.held(lock_path(folder)):
        write_state(folder, doc, analysis)


def next_n(lines: list[dict]) -> int:
    return max([int(e.get("n") or 0) for e in lines] + [0]) + 1


def answer_of(folder, doc, claim: str, ref: str) -> dict:
    """What an act answers: the claim's judgement, the day and his note, its reference's passages, and what
    Undo would take back."""
    lines = read_lines(folder, doc)
    held = states(lines)
    return {"claim": claim, "ref": ref, "state": claim_state(held, claim) if claim else None,
            "passages": held["passages"].get(ref) if ref else None, "undo": undo_said(lines)}


def act(folder, doc, claim, kind: str, value, tool: str = TOOL, ai_on: bool = False) -> dict:
    """One act of his on a claim, Y, Q or N, `judge`, or his note, `note`, a line of the log under the
    project's lock and the readable file written afresh, answering the claim as it now stands and what Undo
    would take back. Only `judge` sets a judgement, always as the researcher's, its line saying, with the
    app's AI switch on and passages on its reference, that they were shown and what they found."""
    entry = doc_entry(folder, doc)
    analysis = analyse(entry["path"], listed(folder))
    c = next((x for x in analysis["claims"] if x["key"] == str(claim or "")), None)
    if c is None:
        raise TraceError(_w("NO_CLAIM"))
    if not c["ref"]:
        raise TraceError(_w("NOTHING_TO_JUDGE"))
    with locks.held(lock_path(folder)):
        lines = read_lines(folder, entry["doc"])
        line = {"n": next_n(lines), "at": now_iso(), "act": kind, "claim": c["key"], "ref": c["ref"],
                "tool": str(tool or TOOL), "by": "researcher"}
        held = states(lines)
        was = claim_state(held, c["key"])
        if kind == "judge":
            value = str(value or "").strip().upper()
            if value not in JUDGEMENTS:
                raise TraceError(_w("JUDGE_VALUES"))
            line["judged"] = value
            line["was"] = {"judged": was["judged"], "set": was["set"]}
            found = held["passages"].get(c["ref"])
            if ai_on and isinstance(found, dict):
                p = passage_for(found, c) or {}
                line["passages_shown"] = {"model": found.get("model"), "found": bool(p.get("passage")),
                                          "unverified": bool(p.get("unverified"))}
            line["words"] = judge_words(line)
        elif kind == "note":
            line["note"] = str(value or "").replace("\r\n", "\n").strip()
            line["was"] = {"note": was["note"]}
        else:
            raise TraceError(i18n.t("trace_server.act.judge_or_note"))
        append(folder, entry["doc"], line)
        write_state(folder, entry["doc"], analysis)
        return answer_of(folder, entry["doc"], c["key"], c["ref"])


def undo(folder, doc, tool: str = TOOL) -> dict:
    """Undo: one more line in the log, taking back his newest judgement or note not yet undone. Nothing in
    the log is removed."""
    entry = doc_entry(folder, doc)
    analysis = analyse(entry["path"], listed(folder))
    with locks.held(lock_path(folder)):
        lines = read_lines(folder, entry["doc"])
        target = undo_target(lines)
        if target is None:
            return {"claim": None, "ref": None, "state": None, "undone": None, "undo": None}
        append(folder, entry["doc"], {"n": next_n(lines), "at": now_iso(), "act": "undo", "undoes": target.get("n"),
                                      "claim": target.get("claim"), "ref": target.get("ref"), "tool": str(tool or TOOL),
                                      "by": "researcher"})
        write_state(folder, entry["doc"], analysis)
        return dict(answer_of(folder, entry["doc"], target.get("claim"), target.get("ref")),
                    undone={"claim": target.get("claim"), "what": target["act"], "n": target.get("n")})


# ------------------------------------------------------------------- the AI's passages

PASSAGES_PROMPT = """You help a researcher check the references of a document he wrote. You see one reference, the claims his document makes of it, numbered, each a sentence that cites it, some with the sentence before it that the claim leans on, and the text of the source's PDF page by page. For each claim, find the passage of the source that supports what the claim says of the source.

Copy each passage word for word from the PDF's text, a sentence or two, never a summary and never your own words, and give the page it is on. When the source holds nothing that supports a claim, say so. He reads the source himself and judges every claim. Your answer only shows him where to look."""
PASSAGES_SHAPE = "\n".join([
    "Answer with strict JSON and nothing else, in this shape:",
    '{"claims": [{"claim": 1, "found": true, "page": 3, "passage": "the words, copied exactly"}]}',
    "One entry for each claim. found is false, page null and passage empty when the source holds nothing that supports it.",
])
PASSAGES_TOKENS = 2000
# the most of a PDF's text one call sends, the pages that share most words with the claims chosen in their
# order when the whole would run past it
PDF_CHARS = 120000
PASSAGE_MIN = 20
NOT_FOUND = "The model gave no passage for this claim."
FAILED = "The model gave a passage Trace could not find in the PDF, so it is not shown."


def page_choice(pages: list[str], said: list[str], budget: int = PDF_CHARS) -> list[int]:
    """The pages a call sends: every one while the whole fits, else those that share most words with the
    claims, kept in their order."""
    if sum(len(p) for p in pages) <= budget:
        return list(range(len(pages)))
    want = {w for s in said for w in re.findall(r"[a-z]{4,}", s.lower())}
    scored = sorted(range(len(pages)), key=lambda i: -len(want & set(re.findall(r"[a-z]{4,}", pages[i].lower()))))
    chosen, used = [], 0
    for i in scored:
        if used + len(pages[i]) > budget and chosen:
            continue
        chosen.append(i)
        used += len(pages[i])
    return sorted(chosen)


def passages_message(ref: dict, pages: list[str], chosen: list[int]) -> str:
    """The call's message: the reference, its claims numbered, each with its section and the sentence before
    it where it leans on it, and the pages chosen, each under its number."""
    lines = [f"Reference: {ref['text']}", "", "Claims the document makes of it:"]
    for k, c in enumerate(ref["claims"], 1):
        lead = f"{c['before']} " if c.get("before") else ""
        lines.append(f"{k}. ({c['section']}) {lead}{c['sentence']}")
    lines += ["", "The source's text, page by page:"]
    for i in chosen:
        lines += [f"[Page {i + 1}]", pages[i] or "(no text on this page)"]
    return "\n".join(lines)


def letters(text: str) -> tuple[str, list[int]]:
    """A text's letters and digits alone, folded, and where each stands in the text, so a passage is
    found whatever its case, spacing, hyphens and punctuation, and given back in the text's own words."""
    out, at = [], []
    for i, ch in enumerate(text):
        for c in unicodedata.normalize("NFKC", ch).casefold():
            if c.isalnum():
                out.append(c)
                at.append(i)
    return "".join(out), at


def locate(passage: str, pages: list[str]) -> tuple[int, str] | None:
    """Where a passage stands in the PDF's text, its page counted from 1 and its words as that page
    holds them, each piece of one parted by an ellipsis found in order on one page, or None when it is
    not there or too short to be told."""
    pieces = [p for p in re.split(r"\s*(?:\.\.\.|…)\s*", str(passage or "")) if letters(p)[0]]
    if not pieces or sum(len(letters(p)[0]) for p in pieces) < PASSAGE_MIN:
        return None
    for n, text in enumerate(pages, 1):
        flat, at = letters(text)
        start, shown = 0, []
        for p in pieces:
            want = letters(p)[0]
            k = flat.find(want, start)
            if k < 0:
                break
            a, b = at[k], at[k + len(want) - 1] + 1
            shown.append(" ".join(text[a:b].split()))
            start = k + len(want)
        else:
            return n, " … ".join(shown)
    return None


def read_answer(text: str, n: int, pages: list[str], truncated: bool = False) -> dict:
    """The answer read strictly: for each claim, `found`, and a passage kept only when it is in the PDF's
    text, in the PDF's own words with the page it stands on, `unverified` where the model gave one that is
    not there."""
    try:
        data = json.loads(ai_mod.strip_fences(text))
    except (ValueError, TypeError):
        return {"error": ai_mod.TOO_LONG if truncated else NOT_JSON}
    claims = data.get("claims") if isinstance(data, dict) else None
    if not isinstance(claims, list):
        return {"error": _w("NO_PASSAGES")}
    out: dict[int, dict] = {}
    for c in claims:
        if not isinstance(c, dict):
            continue
        try:
            k = int(c.get("claim", c.get("sentence")))
        except (TypeError, ValueError):
            continue
        if not 1 <= k <= n or k in out:
            continue
        passage = str(c.get("passage") or "").strip()
        if c.get("found") is not True or not passage:
            out[k] = {"n": k, "found": False}
            continue
        hit = locate(passage, pages)
        out[k] = {"n": k, "found": True, "page": hit[0], "passage": hit[1]} if hit else \
            {"n": k, "found": True, "unverified": True}
    return {"claims": [out.get(k, {"n": k, "found": False}) for k in range(1, n + 1)]}


def find_passages(folder, doc, ref, route: dict, transport=None, tool: str = TOOL, screenings=()) -> dict:
    """The AI's passages for one reference's claims, asked of the app's AI with the claims and the PDF's
    text, each passage kept only once it is found in that text, written to the log as the AI's, its model
    named, never setting a judgement, or one error line with nothing written."""
    entry = doc_entry(folder, doc)
    analysis = analyse(entry["path"], listed(folder))
    r = next((x for x in analysis["references"] if x["key"] == ref), None)
    if r is None:
        raise TraceError(_w("NOTHING_TO_JUDGE") if str(ref or "").startswith("cite:") else _w("NO_REF"))
    if not r["claims"]:
        return {"error": _w("NO_CITES")}
    found = pdf_for(folder, r, pdf_index(folder, screenings))["path"]
    if found is None:
        return {"error": _w("NO_PDF")}
    pages = pdftext.pages_text(Path(found).read_bytes())
    if not any(p.strip() for p in pages):
        return {"error": _w("PDF_UNREAD")}
    refused = ai_mod.route_ready(route)
    if refused:
        return refused
    said = [f"{c['before']} {c['sentence']}".strip() for c in r["claims"]]
    chosen = page_choice(pages, said)
    provider = route.get("provider") if route.get("provider") in ai_mod.PROVIDERS else ai_mod.ANTHROPIC
    answer = ai_mod.complete(f"{PASSAGES_PROMPT}\n\n{PASSAGES_SHAPE}", passages_message(r, pages, chosen), provider,
                             route.get("model"), route.get("key"),
                             route.get("local_url"), transport, None,
                             None if provider == ai_mod.ANTHROPIC and ai_mod.thinks(route.get("model")) else PASSAGES_TOKENS,
                             route.get("address"), route.get("deployment"))
    if "error" in answer:
        return answer
    got = read_answer(answer["text"], len(said), pages, bool(answer.get("truncated")))
    if "error" in got:
        return got
    for c in got["claims"]:
        claim = r["claims"][c["n"] - 1]
        c["claim"] = claim["key"]
        c["said"] = claim["sentence"]
    held = {"model": ai_mod.route_model(route), "asked": now_iso(), "claims": got["claims"],
            "found": sum(1 for c in got["claims"] if c.get("passage")), "of": len(got["claims"]),
            "unverified": sum(1 for c in got["claims"] if c.get("unverified"))}
    with locks.held(lock_path(folder)):
        lines = read_lines(folder, entry["doc"])
        append(folder, entry["doc"], {"n": next_n(lines), "at": now_iso(), "act": "passages", "ref": ref,
                                      "tool": str(tool or TOOL), "by": "ai", "passages": held})
        write_state(folder, entry["doc"], analysis)
        return answer_of(folder, entry["doc"], "", ref)


def plan(folder, doc, ids=None, screenings=()) -> dict:
    """The references AI find passages for the rows shown would ask about, before any call: those with a
    PDF, a claim and no passages yet, among the claims `ids` names when the screen names its rows, one call
    each."""
    view = rows(folder, doc, screenings=screenings)
    shown = {str(i) for i in ids} if isinstance(ids, list) else None
    keys: list[str] = []
    for r in view["rows"]:
        if (r["kind"] == "claim" and r["pdf"] and not r["passages"] and (shown is None or r["key"] in shown)
                and r["ref"] not in keys):
            keys.append(r["ref"])
    return {"ids": keys, "calls": len(keys)}


# ------------------------------------------------------------------- read views

def history(folder, doc) -> list[dict]:
    """Every line of a manuscript's log, oldest first, each judgement with its words, and Sift's Checked lines
    of 14 October with theirs, for the command line."""
    doc_entry(folder, doc)
    out = []
    for e in read_lines(folder, doc):
        line = dict(e)
        if e.get("act") == "judge":
            line["words"] = judge_words(e)
        elif e.get("act") == "check":
            line["words"] = check_words(e)
        out.append(line)
    return out


def stands(folder) -> str:
    """A project's card's one line: its newest manuscript and how many of its claims he has judged, from the
    readable file alone, or its reference list alone, or nothing yet."""
    entries = docs(folder)
    if entries:
        d = entries[-1]
        c = d.get("counts") or {}
        n, j = int(c.get("claims") or 0), int(c.get("judged") or 0)
        if len(entries) > 1:
            return i18n.t("trace_server.stands.judged_more", name=d["name"], more=len(entries) - 1, judged=j, n=n)
        return i18n.t("trace_server.stands.judged", name=d["name"], judged=j, n=n)
    held = list_of(folder)
    if held:
        return i18n.t("trace_server.stands.no_manuscript", name=held["name"])
    return i18n.t("trace_server.stands.no_document")
