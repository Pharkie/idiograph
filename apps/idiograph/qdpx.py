#!/usr/bin/env python3
"""A REFI-QDA project (.qdpx), as ATLAS.ti, NVivo and MAXQDA export one, read and mapped into IPA's
terms for an import (21 October 2026, the plan in the coordinator's qdpxplan, with Adam's rulings).

A .qdpx is a zip of `project.qde`, an XML file in the namespace `urn:QDA-XML:project:1.0`, and a
`Sources/` folder of the files it names `internal://<name>`. This module only reads: the package is
opened in memory, a name in it that climbs out of it (`../`, a leading `/`, a drive) is never read,
each part is capped in size, and an XML document type, which could carry entities, is refused.

    read_package(path)       the project as plain records: sources, their selections, codes, code
                             groups, notes, cases, users, and what is there but left out
    passages(text)           a source's plain text split as `convert.read_plain` splits it, each
                             passage with where its words sit in the text
    map_source(src, pkg, …)  one source as a participant's transcript: the turns, an exploratory
                             note a turn, the statements and quotes a turn, and the counts

The element names follow the open-source QualCoder's reader and writer (`refi.py`, read 21 October
2026), since the XSD and the specification sit behind a file viewer that could not be read as a page.
`MemberCode` in a `Set` rests on that documentation alone (QualCoder reads `MemberSource`).

Positions in a selection are counted as characters of the source's plain text, a character a Python
string's character, line endings as the file has them. The standard library alone.
"""
from __future__ import annotations

import re
import zipfile
from pathlib import Path
from xml.etree import ElementTree

import convert as convert_mod
import i18n

QDE = "project.qde"
QDE_MAX = 64 * 1024 * 1024          # the most project.qde may unpack to
TEXT_MAX = 32 * 1024 * 1024         # and one source's plain text
MEDIA_MAX = 4 * 1024 * 1024 * 1024  # and one recording
ENTRIES_MAX = 20000                 # the most files a package may hold
ELLIPSIS = " … "                    # between the pieces of a quote, as the app builds one (static/quote.js)
# the name Idiograph's own export gives a selection of a whole passage that stands for a statement with no
# quote (qdpx_out.py, 8 November 2026), read back as a statement with none from a project Idiograph wrote
WHOLE = "Whole passage"


# a package by the programme its `origin` names, for the lines and the PET draft's board
PACKAGES = (("atlas", "ATLAS.ti"), ("nvivo", "NVivo"), ("maxqda", "MAXQDA"), ("qualcoder", "QualCoder"), ("idiograph", "Idiograph"))

CODES = ("statements", "notes", "leave")
COMMENTS = ("notes", "statements")
LOOSE = ("blank", "leave")
MEMOS = ("source", "leave")
RECORDINGS = ("copy", "leave")


class Unreadable(Exception):
    """A package that cannot be read, with the one line that says so."""


# ------------------------------------------------------------------ the zip

def safe_name(name: str) -> bool:
    """A name in the zip that stays inside it: no `..`, no leading slash or backslash, no drive."""
    text = str(name or "")
    if not text or text.startswith(("/", "\\")) or "\\" in text or re.match(r"^[A-Za-z]:", text):
        return False
    return ".." not in text.split("/")


class Package:
    """An open .qdpx, its safe names by their lower case, read part by part under the caps."""

    def __init__(self, path: Path):
        self.path = Path(path)
        try:
            self.zip = zipfile.ZipFile(self.path)
        except (zipfile.BadZipFile, OSError, ValueError):
            raise Unreadable(i18n.t("server.file_refi_qda_project_idiograph")) from None
        infos = self.zip.infolist()
        if len(infos) > ENTRIES_MAX:
            self.zip.close()
            raise Unreadable(i18n.t("server.file_refi_qda_project_idiograph"))
        self.names: dict[str, zipfile.ZipInfo] = {}
        self.unsafe: list[str] = []
        for info in infos:
            if info.is_dir():
                continue
            if safe_name(info.filename):
                self.names.setdefault(info.filename.lower(), info)
            else:
                self.unsafe.append(info.filename)

    def close(self) -> None:
        self.zip.close()

    def info(self, name: str) -> zipfile.ZipInfo | None:
        return self.names.get(str(name).lower()) if safe_name(name) else None

    def read(self, name: str, most: int) -> bytes | None:
        """A part's bytes, or None when it is not there, is unsafe, or unpacks past `most`."""
        info = self.info(name)
        if info is None or info.file_size > most:
            return None
        with self.zip.open(info) as fh:
            data = fh.read(most + 1)
        return None if len(data) > most else data

    def source_part(self, ref: str) -> str | None:
        """The zip's name for an `internal://` reference, in `Sources/` (or `sources/`), else None."""
        text = str(ref or "")
        if not text.lower().startswith("internal://"):
            return None
        tail = text[len("internal://"):].lstrip("/")
        for folder in ("Sources/", "sources/"):
            if self.info(folder + tail) is not None:
                return folder + tail
        return None


def local(tag) -> str:
    """An element's name without its namespace."""
    return str(tag).rsplit("}", 1)[-1]


def kids(el, name: str) -> list:
    return [c for c in list(el) if local(c.tag) == name]


def kid(el, name: str):
    if el is None:
        return None
    found = kids(el, name)
    return found[0] if found else None


def within(el, outer: str, inner: str) -> list:
    """The `inner` elements of `el`'s child `outer`, none when it has no such child."""
    holder = kid(el, outer)
    return [] if holder is None else kids(holder, inner)


def words_of(el) -> str:
    """An element's own text, or none."""
    return "" if el is None else "".join(el.itertext()).strip()


def parse_qde(data: bytes):
    """project.qde parsed, refused when it carries a document type, so no entity is ever expanded."""
    head = data[:4096 * 16].lower()
    if b"<!doctype" in head or b"<!entity" in data.lower():
        raise Unreadable(i18n.t("server.project_s_project_qde_carries"))
    try:
        return ElementTree.fromstring(data)
    except ElementTree.ParseError:
        raise Unreadable(i18n.t("server.file_refi_qda_project_idiograph")) from None


def package_name(origin: str) -> str:
    """The programme a project came from, by its `origin`, ATLAS.ti, NVivo or MAXQDA, else its own words."""
    low = str(origin or "").lower()
    for stem, name in PACKAGES:
        if stem in low:
            return name
    return " ".join(str(origin or "").split())[:40] or "another programme"


def number(value, default: int | None = None) -> int | None:
    try:
        return int(str(value).strip())
    except (TypeError, ValueError):
        return default


# ------------------------------------------------------------------ reading

def selection_of(el, sync: dict | None = None) -> dict | None:
    """A selection as a record: where it starts and ends, its codes with who coded each, its comment
    (its own `Description`), the notes it points to, and who made it. A transcript's selection is
    placed by its sync points' positions. None for one that cannot be placed."""
    if local(el.tag) == "TranscriptSelection":
        start = (sync or {}).get(el.get("fromSyncPoint"))
        end = (sync or {}).get(el.get("toSyncPoint"))
        start, end = (start or {}).get("position"), (end or {}).get("position")
    else:
        start, end = number(el.get("startPosition")), number(el.get("endPosition"))
    if start is None or end is None or end <= start or start < 0:
        return None
    codes = []
    for coding in kids(el, "Coding"):
        for ref in kids(coding, "CodeRef"):
            if ref.get("targetGUID"):
                codes.append({"code": ref.get("targetGUID"), "user": coding.get("creatingUser") or el.get("creatingUser") or ""})
    return {"guid": el.get("guid") or "", "start": start, "end": end, "codes": codes,
            "comment": words_of(kid(el, "Description")),
            "notes": [r.get("targetGUID") for r in kids(el, "NoteRef") if r.get("targetGUID")],
            "user": el.get("creatingUser") or "", "name": el.get("name") or ""}


def text_at(pkg: Package, el) -> tuple[str | None, str]:
    """A source's plain text, from its `plainTextPath` in the package or its own `PlainTextContent`,
    with the reason when there is none."""
    ref = el.get("plainTextPath") or ""
    part = pkg.source_part(ref)
    if part:
        data = pkg.read(part, TEXT_MAX)
        if data is None:
            return None, "too large"
        return convert_mod.decode(data), ""
    inline = kid(el, "PlainTextContent")
    if inline is not None and words_of(inline):
        return "".join(inline.itertext()), ""
    return None, "its text is not in the package" if ref else "it has no text"


def media_of(pkg: Package, el) -> dict | None:
    """A recording's file: `internal://` in the package, else `relative://` or `absolute://`, by name."""
    ref = str(el.get("path") or "")
    if not ref:
        return None
    part = pkg.source_part(ref)
    if part:
        return {"part": part, "name": Path(part).name, "size": pkg.info(part).file_size}
    kind, _, tail = ref.partition("://")
    return {"part": None, "name": Path(tail.replace("\\", "/")).name, "where": kind or "path", "ref": tail}


def read_package(path) -> dict:
    """A .qdpx read into plain records. Raises Unreadable with the card's line for a file that is no
    project. Every source keeps its place in the file, numbered from 1."""
    pkg = Package(path)
    try:
        data = pkg.read(QDE, QDE_MAX)
        if data is None:
            found = next((n for n in pkg.names if n.endswith(".qde") and "/" not in n), None)
            if found is None:
                raise Unreadable(i18n.t("server.project_s_project_qde_too") if pkg.info(QDE) is not None else i18n.t("server.file_holds_project_qde_refi"))
            data = pkg.read(found, QDE_MAX)
            if data is None:
                raise Unreadable(i18n.t("server.project_s_project_qde_too"))
        root = parse_qde(data)
        if local(root.tag) != "Project":
            raise Unreadable(i18n.t("server.file_refi_qda_project_idiograph"))
        out = read_root(pkg, root)
        out["unsafe"] = list(pkg.unsafe)
        return out
    finally:
        pkg.close()


def read_root(pkg: Package, root) -> dict:
    users = {u.get("guid"): u.get("name") or "" for u in within(root, "Users", "User")}
    codes: dict[str, dict] = {}

    def walk(el, parent: str | None) -> None:
        for c in kids(el, "Code"):
            guid = c.get("guid") or ""
            codes[guid] = {"guid": guid, "name": " ".join(str(c.get("name") or "").split()), "parent": parent,
                           "codable": str(c.get("isCodable") or "true").lower() != "false",
                           "described": bool(words_of(kid(c, "Description"))),
                           "description": " ".join(words_of(kid(c, "Description")).split()),
                           "notes": [r.get("targetGUID") for r in kids(c, "NoteRef") if r.get("targetGUID")],
                           "children": []}
            if parent in codes:
                codes[parent]["children"].append(guid)
            walk(c, guid)

    book = kid(root, "CodeBook")
    held = kid(book, "Codes")
    if held is not None:
        walk(held, None)
    elif book is not None:
        walk(book, None)
    notes = {}
    for n in within(root, "Notes", "Note"):
        text, _ = text_at(pkg, n)
        text = text if text is not None else words_of(kid(n, "Description"))
        notes[n.get("guid") or ""] = {"name": n.get("name") or "", "text": (text or "").strip()}
    sets = []
    for s in within(root, "Sets", "Set"):
        sets.append({"name": " ".join(str(s.get("name") or "").split()),
                     "codes": [m.get("targetGUID") for m in kids(s, "MemberCode") if m.get("targetGUID") in codes],
                     "sources": [m.get("targetGUID") for m in kids(s, "MemberSource") if m.get("targetGUID")],
                     "description": " ".join(words_of(kid(s, "Description")).split()),
                     "notes": [m.get("targetGUID") for m in kids(s, "MemberNote") if m.get("targetGUID")]})
    cases = []
    for c in within(root, "Cases", "Case"):
        cases.append({"name": c.get("name") or "", "sources": [r.get("targetGUID") for r in kids(c, "SourceRef")],
                      "values": len(kids(c, "VariableValue"))})
    sources = []
    holder = kid(root, "Sources")
    for el in ([] if holder is None else list(holder)):
        sources.append(read_source(pkg, el, len(sources) + 1))
    # Idiograph names each source `<participant> - <interview>` and its case by the participant (qdpx_out.py), so
    # an interview comes back under its own name, which no guess from the words of a name could give (qdpxround)
    if str(root.get("origin") or "").startswith("Idiograph"):
        by_guid = {s["guid"]: s for s in sources}
        for c in cases:
            for g in c["sources"]:
                src = by_guid.get(g)
                if src is not None and src["name"].startswith(f"{c['name']} - "):
                    src["interview"] = src["name"][len(c["name"]) + 3:].strip()
    variables = len(within(root, "Variables", "Variable"))
    referenced = ({g for s in sources for g in s["memos"]} | {g for s in sources for sel in s["selections"] for g in sel["notes"]}
                  | {g for c in codes.values() for g in c["notes"]} | {g for s in sets for g in s["notes"]})
    return {"origin": root.get("origin") or "", "package": package_name(root.get("origin") or ""),
            "name": root.get("name") or "", "users": users, "codes": codes, "sets": sets, "notes": notes,
            "cases": cases, "sources": sources, "variables": variables,
            "values": sum(c["values"] for c in cases),
            "links": len(list(kid(root, "Links") if kid(root, "Links") is not None else [])),
            "graphs": len(list(kid(root, "Graphs") if kid(root, "Graphs") is not None else [])),
            "free_memos": [g for g in notes if g not in referenced]}


KINDS = {"TextSource": "text", "AudioSource": "audio", "VideoSource": "video", "PDFSource": "pdf",
         "PictureSource": "picture"}


def read_source(pkg: Package, el, n: int) -> dict:
    """One source: its kind, its plain text (a transcript's for a recording), its selections, its sync
    points by position, its recording, and the notes it points to itself, its memos."""
    kind = KINDS.get(local(el.tag), local(el.tag))
    src = {"n": n, "guid": el.get("guid") or "", "name": " ".join(str(el.get("name") or f"Source {n}").split()),
           "kind": kind, "text": None, "missing": "", "selections": [], "sync": [], "media": None,
           "memos": [r.get("targetGUID") for r in kids(el, "NoteRef") if r.get("targetGUID")],
           "lost": 0}
    if kind == "text":
        src["text"], src["missing"] = text_at(pkg, el)
        for s in kids(el, "PlainTextSelection"):
            sel = selection_of(s)
            if sel is None:
                src["lost"] += 1
            else:
                src["selections"].append(sel)
    elif kind in ("audio", "video"):
        src["media"] = media_of(pkg, el)
        script = kid(el, "Transcript")
        if script is None:
            src["missing"] = "it has no transcript"
        else:
            src["text"], src["missing"] = text_at(pkg, script)
            points = {}
            for p in kids(script, "SyncPoint"):
                at, ms = number(p.get("position")), number(p.get("timeStamp"))
                if at is not None and ms is not None:
                    points[p.get("guid")] = {"position": at, "ms": ms}
            src["sync"] = sorted((p["position"], p["ms"]) for p in points.values())
            for s in list(script):
                if local(s.tag) in ("TranscriptSelection", "PlainTextSelection"):
                    sel = selection_of(s, points)
                    if sel is None:
                        src["lost"] += 1
                    else:
                        src["selections"].append(sel)
        # a selection of the recording itself, by its times, has no words to quote
        src["lost"] += len(kids(el, "AudioSelection")) + len(kids(el, "VideoSelection"))
    return src


# ------------------------------------------------------------------ passages

_LINE = re.compile(r"[^\r\n]*(?:\r\n|\n|\r)?")


def lines_at(text: str) -> list[tuple[int, str]]:
    """Each line of the text with where it starts, its line ending left off."""
    out, at = [], 0
    for m in _LINE.finditer(text):
        if m.end() == m.start():
            break
        line = m.group(0).rstrip("\r\n")
        out.append((m.start(), line))
        at = m.end()
    if at < len(text) or not out:
        out.append((at, text[at:]))
    return out


def passages(text: str) -> list[dict]:
    """The text split as `convert.read_plain` splits plain text, a `Name:` line starting a passage
    and the lines after it carrying it on, else a paragraph a passage (a line a passage when the
    whole is one paragraph), each `{"name", "seconds", "words", "start", "body", "end"}`: `body`
    where its words begin in the text, after the label or the time, and `end` where its last line ends."""
    lines = lines_at(text)
    found = [convert_mod.label_of(line) for _, line in lines]
    names = convert_mod._named(found)
    out: list[dict] = []
    if names:
        for (at, line), label in zip(lines, found):
            if label and label[0] in names:
                words = label[2]
                body = at + (line.rfind(words) if words else len(line))
                out.append({"name": label[0], "seconds": label[1], "start": at, "body": body, "end": at + len(line)})
            elif line.strip():
                if not out:
                    out.append({"name": convert_mod.SPEAKER, "seconds": None, "start": at, "body": at, "end": at + len(line)})
                else:
                    out[-1]["end"] = at + len(line)
    else:
        blocks: list[list[tuple[int, str]]] = [[]]
        for at, line in lines:
            if line.strip():
                blocks[-1].append((at, line))
            elif blocks[-1]:
                blocks.append([])
        blocks = [b for b in blocks if b]
        if len(blocks) == 1:
            blocks = [[one] for one in blocks[0]]
        for block in blocks:
            at, end = block[0][0], block[-1][0] + len(block[-1][1])
            raw = text[at:end]
            seconds, rest = convert_mod._lead_time(convert_mod._squash(raw))
            body = at + (len(raw) - len(raw.lstrip()))
            if seconds is not None:
                m = convert_mod._LEAD.match(raw)
                body = at + (m.end() if m else 0)
            out.append({"name": convert_mod.SPEAKER, "seconds": seconds, "start": at, "body": body, "end": end})
    for p in out:
        p["words"] = convert_mod._squash(text[p["body"]:p["end"]])
    return [p for p in out if p["words"]]


def merge_pieces(pieces: list[tuple[int, int]], text: str) -> list[tuple[int, int]]:
    """Pieces in transcript order, those that overlap or have nothing but space between them made
    one, as `mergePieces` in static/quote.js makes them."""
    out: list[list[int]] = []
    for start, end in sorted((max(0, s), min(len(text), e)) for s, e in pieces):
        if end <= start:
            continue
        if out and (start <= out[-1][1] or not text[out[-1][1]:start].strip()):
            out[-1][1] = max(out[-1][1], end)
        else:
            out.append([start, end])
    return [(s, e) for s, e in out]


def assemble_quote(pieces: list[tuple[int, int]], text: str) -> str:
    """One quote of its pieces, joined with an ellipsis, in inverted commas, as the app builds one."""
    parts = [" ".join(text[s:e].split()) for s, e in merge_pieces(pieces, text)]
    parts = [p for p in parts if p]
    return f'"{ELLIPSIS.join(parts)}"' if parts else ""


def ms_at(sync: list[tuple[int, int]], at: int) -> int | None:
    """The milliseconds of the sync point nearest before a place in the text, or None."""
    best = None
    for position, ms in sync:
        if position <= at:
            best = ms
        else:
            break
    return best


def time_at(sync: list[tuple[int, int]], at: int) -> int | None:
    """A passage's time in seconds from the sync point nearest before where it starts, or None."""
    best = ms_at(sync, at)
    return None if best is None else max(0, int(best) // 1000)


OFFSET_MOST = 24 * 3600  # as audio.OFFSET_MOST


def offset_of(found: list[dict], sync: list[tuple[int, int]]) -> float | None:
    """The recording's offset when a transcript's own times and its sync points differ by the same seconds at
    every passage that has both, to a hundredth: the transcript's times are then kept and the difference
    becomes the offset, so a passage plays where it did and shows the time it had (qdpxround, 9 November 2026).
    None when no passage has both or they disagree."""
    diffs = []
    for p in found:
        if p["seconds"] is None:
            continue
        ms = ms_at(sync, p["start"])
        if ms is None:
            return None
        diffs.append(ms / 1000 - p["seconds"])
    if not diffs or max(diffs) - min(diffs) > 0.011 or abs(diffs[0]) > OFFSET_MOST:
        return None
    return round(sum(diffs) / len(diffs), 2) + 0.0


# ------------------------------------------------------------------ mapping

def one_line(text) -> str:
    return " ".join(str(text or "").split())


def map_source(src: dict, pkg: dict, codes: str = "statements", comments: str = "notes", loose: str = "blank",
               user: str = "", roles: dict | None = None) -> dict:
    """One text source, or a recording's transcript, as a participant's transcript under the choices:
    `turns`, `(name, seconds, words)` as the raw source takes them, `notes`, one `{"en"}` a turn with
    its exploratory notes a line each, `pairs`, a turn's index to its `[{"es", "kq"}]`, and `counts`.

    A selection lands on the passage where it starts, its words cut at that passage's end, and is
    counted as cut. Its comment is an exploratory note there, or with `comments` of `statements` a
    statement whose quote it is. Each of its codes, with `codes` of `statements`, is a statement
    named by the code on that passage, one a code a passage, its quote the code's quotations there
    as pieces in transcript order (Adam's ruling 2). With `notes` the code's name is a note there
    once. A selection with neither, with `loose` of `blank`, is a blank statement, its quote set and
    its words empty (ruling 3). `user`, a user's name or id, keeps that coder's work alone. Codes and
    statements on the interviewer's or another speaker's passages, by `roles`, are left out and
    counted, their comments kept as notes."""
    text = src["text"] or ""
    found = passages(text)
    sync = src.get("sync") or []
    offset = offset_of(found, sync) if sync else None
    turns = []
    for p in found:
        if offset is not None:
            ms = ms_at(sync, p["start"])
            seconds = p["seconds"] if p["seconds"] is not None or ms is None else max(0, int(round(ms / 1000 - offset)))
        else:
            seconds = time_at(sync, p["start"]) if sync else None
        turns.append((p["name"], seconds if seconds is not None else p["seconds"], p["words"]))
    roles = roles or {}
    names = pkg["codes"]
    counts = {"comments": 0, "coded": 0, "statements": 0, "comment_statements": 0, "code_notes": 0, "blank": 0, "loose_left": 0,
              "cut": 0, "outside": 0, "not_participant": 0, "codes_left": set(), "codes_used": set(), "users": set(),
              "other_users": 0}
    notes: list[list[str]] = [[] for _ in found]
    by_code: dict[tuple[int, str, str], list[tuple[int, int]]] = {}
    said: dict[int, list[tuple[int, str, list]]] = {}
    want = one_line(user).lower()
    who = lambda guid: pkg["users"].get(guid, guid) or ""
    # a project Idiograph wrote marks a statement with no quote by a selection of its whole passage
    own = ours(pkg)

    def mine(guid: str) -> bool:
        return not want or want in (str(guid).lower(), who(guid).lower())

    # in a project Idiograph wrote, the selections stand in the order of each passage's statements, which a
    # statement with no quote, coded on its whole passage, would lose if they were put in order by place (qdpxround)
    seq = {id(sel): n for n, sel in enumerate(src["selections"])}
    first_seq: dict[tuple, int] = {}
    for sel in sorted(src["selections"], key=lambda s: (s["start"], s["end"])):
        at = seq[id(sel)]
        place = next((i for i, p in enumerate(found) if p["start"] <= sel["start"] < max(p["end"], p["start"] + 1)), None)
        if place is None:
            # between passages, in a blank line: the next passage that starts after it
            place = next((i for i, p in enumerate(found) if p["start"] >= sel["start"] and p["start"] < sel["end"]), None)
        if place is None:
            counts["outside"] += 1
            continue
        p = found[place]
        start, end = max(sel["start"], p["body"]), min(sel["end"], p["end"])
        if sel["end"] > p["end"] and text[p["end"]:sel["end"]].strip():
            counts["cut"] += 1
        piece = (start, end) if end > start and text[start:end].strip() else None
        participant = roles.get(p["name"], "participant") == "participant"
        kept_codes = [c for c in sel["codes"] if mine(c["user"]) and c["code"] in names]
        counts["other_users"] += len([c for c in sel["codes"] if not mine(c["user"])])
        for c in sel["codes"]:
            counts["users"].add(who(c["user"]))
        if sel["user"]:
            counts["users"].add(who(sel["user"]))
        comment_mine = mine(sel["user"]) if sel["user"] else True
        texts = [sel["comment"]] if sel["comment"] else []
        texts += [pkg["notes"][g]["text"] for g in sel["notes"] if g in pkg["notes"] and pkg["notes"][g]["text"]]
        texts = [one_line(t) for t in texts if one_line(t)] if comment_mine else []
        for t in texts:
            counts["comments"] += 1
            if comments == "statements" and participant and piece:
                said.setdefault(place, []).append((at if own else piece[0], t, [piece]))
                counts["statements"] += 1
                counts["comment_statements"] += 1
            else:
                notes[place].append(t)
        for c in kept_codes:
            counts["coded"] += 1
            name = names[c["code"]]["name"]
            if codes == "leave":
                counts["codes_left"].add(c["code"])
            elif not participant:
                counts["not_participant"] += 1
            elif codes == "notes":
                if name not in notes[place]:
                    notes[place].append(name)
                    counts["code_notes"] += 1
                counts["codes_used"].add(c["code"])
            elif piece:
                # in a project Idiograph wrote, a selection's name is its quote's, so two quotes of one code on one
                # passage stay two statements, as a thematic analysis project's code on two extracts there is
                held = (sel.get("name") or "") if own else ""
                by_code.setdefault((place, c["code"], held), []).append(None if held == WHOLE else piece)
                first_seq[(place, c["code"], held)] = min(first_seq.get((place, c["code"], held), at), at)
                counts["codes_used"].add(c["code"])
        if not sel["codes"] and not texts and comment_mine:
            if loose == "blank" and participant and piece:
                said.setdefault(place, []).append((at if own else piece[0], "", [piece]))
                counts["blank"] += 1
            else:
                counts["loose_left"] += 1
    for (place, code, held), pieces in by_code.items():
        pieces = [one for one in pieces if one]
        first = min(s for s, _ in pieces) if pieces else found[place]["start"]
        if own:
            first = first_seq[(place, code, held)]
        said.setdefault(place, []).append((first, names[code]["name"], pieces))
        counts["statements"] += 1
    pairs = {}
    keys: dict[int, list[str]] = {}
    for place, items in said.items():
        items.sort(key=lambda x: x[0])
        pairs[place] = [{"es": es, "kq": assemble_quote(pieces, text)} for _, es, pieces in items]
        keys[place] = [es for _, es, _ in items]
    counts["codes_left"] = len(counts["codes_left"])
    counts["codes_used"] = sorted(counts["codes_used"])
    counts["users"] = sorted(u for u in counts["users"] if u)
    return {"turns": turns, "notes": [{"en": "\n".join(n)} if n else {} for n in notes], "pairs": pairs,
            "counts": counts, "passages": found, "offset": offset or 0.0}


def codable_under(pkg: dict, guid: str, through: bool = True) -> list[str]:
    """The codes that can be coded under a code, at any depth, in the codebook's order, the code itself left out.
    With `through` false the walk stops at a code that cannot be coded, so a sub-group's codes stay its own."""
    codes, out = pkg["codes"], []

    def walk(g: str) -> None:
        for x in codes[g]["children"]:
            if codes[x]["codable"]:
                out.append(x)
                walk(x)
            elif through:
                walk(x)
    walk(guid)
    return out


def note_text(pkg: dict, code: dict) -> str:
    """A code's notes as one note, each the words the package holds for it."""
    said = [pkg["notes"][g]["text"] for g in code.get("notes") or [] if g in pkg["notes"] and pkg["notes"][g]["text"]]
    return "\n\n".join(said)


def code_tree(pkg: dict, guid: str) -> dict:
    """A code that cannot be coded as a PET or a theme: its name, description and note, `codes` the codes under
    it that are its own, and `groups` each code under it that cannot be coded and holds some, nested the same way.
    `code` is its guid."""
    codes = pkg["codes"]
    c = codes[guid]
    subs = [code_tree(pkg, x) for x in c["children"] if not codes[x]["codable"] and codable_under(pkg, x)]
    return {"code": guid, "name": c["name"], "description": c.get("description") or "", "note": note_text(pkg, c),
            "codes": codable_under(pkg, guid, through=False), "groups": subs}


def set_tree(pkg: dict, one: dict) -> dict:
    """A set as a PET or a theme with what it holds. When a code of the set's name that cannot be coded holds
    exactly the set's codes, as Idiograph writes a PET and its set (qdpx_out.py), the code's tree is the set's, so
    its sub-PETs, their order and its note come back (qdpxround, 9 November 2026). Else the set's codes, flat."""
    codes = pkg["codes"]
    want = {g for g in one["codes"] if codes[g]["codable"]}
    holder = next((g for g, c in codes.items() if c["name"] == one["name"] and not c["codable"]
                   and set(codable_under(pkg, g)) == want), None)
    if holder is None:
        return {"code": None, "name": one["name"], "description": one.get("description") or "", "note": "",
                "codes": [g for g in one["codes"] if codes[g]["codable"]], "groups": []}
    tree = code_tree(pkg, holder)
    tree["description"] = one.get("description") or tree["description"]
    return tree


def code_groups(pkg: dict) -> list[dict]:
    """The code groups a PET draft takes, each `{"name", "codes", "description", "tree"}`: the project's sets
    that hold codes that can be coded, each with its own description, and with none, each parent code with the
    codes under it, itself among them. `tree` is the group as `set_tree` reads it, its sub-groups nested."""
    codes = pkg["codes"]
    groups = [{"name": s["name"], "codes": s["codes"], "description": s.get("description") or "", "tree": set_tree(pkg, s)}
              for s in pkg["sets"] if s["name"] and any(codes[g]["codable"] for g in s["codes"])]
    if groups:
        return groups
    out = []
    for c in codes.values():
        if c["children"] and c["parent"] is None:
            under, stack = [], [c["guid"]]
            while stack:
                g = stack.pop(0)
                under.append(g)
                stack += codes[g]["children"]
            out.append({"name": c["name"], "codes": under, "description": "",
                        "tree": {"code": None, "name": c["name"], "description": "", "note": "", "codes": under,
                                 "groups": []}})
    return out


def upper_groups(pkg: dict) -> list[dict]:
    """The sets that hold codes that cannot be coded, as Idiograph writes each GET, a set of PETs (qdpx_out.py):
    each `{"name", "description", "note", "codes"}`, its codes those that cannot be coded, in its order, its note
    the set's member notes as one."""
    codes = pkg["codes"]
    out = []
    for s in pkg["sets"]:
        held = [g for g in s["codes"] if not codes[g]["codable"]]
        if s["name"] and held:
            out.append({"name": s["name"], "description": s.get("description") or "", "codes": held,
                        "note": note_text(pkg, s)})
    return out


def ours(pkg: dict) -> bool:
    """Whether Idiograph wrote the package, by its `origin`."""
    return str(pkg.get("origin") or "").startswith("Idiograph")


def set_aside(pkg: dict) -> set[str]:
    """In a package Idiograph wrote, the codes in each participant's Set aside code (qdpx_out.py), its name in the
    language of the run or in English, so those statements go back to the bin. None from another programme."""
    if not ours(pkg):
        return set()
    names = {i18n.t("exports.qdpx_set_aside"), i18n.t("exports.qdpx_set_aside", lang="en")}
    out: set[str] = set()
    for g, c in pkg["codes"].items():
        if not c["codable"] and c["parent"] is not None and c["name"] in names:
            out.update(codable_under(pkg, g))
    return out


def copy_media(path, part: str, target: Path) -> bool:
    """A recording copied out of the package to `target`, a new file, in chunks, never past the cap.
    False, with nothing left at `target`, when it is not there or is too large."""
    pkg = Package(path)
    try:
        info = pkg.info(part)
        if info is None or info.file_size > MEDIA_MAX:
            return False
        done = 0
        with pkg.zip.open(info) as fh, open(target, "xb") as out:
            while True:
                chunk = fh.read(1024 * 1024)
                if not chunk:
                    break
                done += len(chunk)
                if done > MEDIA_MAX:
                    break
                out.write(chunk)
        if done > MEDIA_MAX:
            Path(target).unlink(missing_ok=True)
            return False
        return True
    finally:
        pkg.close()


def __getattr__(name: str) -> str:
    """The refusals other modules and the checks name as this module's, each read in the run's language when
    asked for (the text layer, 28 October 2026)."""
    said = {
        "NOT_A_PACKAGE": lambda: i18n.t("server.file_refi_qda_project_idiograph"),
        "DOCTYPE": lambda: i18n.t("server.project_s_project_qde_carries"),
    }
    if name in said:
        return said[name]()
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
