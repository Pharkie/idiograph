#!/usr/bin/env python3
"""A project, or some of its participants, written as a REFI-QDA 1.5 project (.qdpx), for NVivo, ATLAS.ti,
MAXQDA and QualCoder to open (qdpxout, 8 November 2026, the landscape's "Worth taking" first). It mirrors
`qdpx.py`, the reader, so an export brought back in by Idiograph's own import gives the same statements,
quotes and PETs.

A .qdpx is a zip of `project.qde`, XML in the namespace `urn:QDA-XML:project:1.0` as the standard's
Project.xsd sets it out, and `Sources/`, each file named by a new GUID. The mapping:

    a participant's interview (a sheet)   a text source, `Sources/<guid>.txt`, a passage a paragraph,
                                          "[00:01:23] Name: words", the words with their spaces made single,
                                          so the reader's own split (`qdpx.passages`) finds the same passages
                                          with the same speakers and times. With the recordings asked for, a
                                          sheet with a recording is an audio source holding that text as its
                                          transcript, a sync point at each passage, the recording in Sources
    an experiential statement (IPA)       a code named by its words, applied to each piece of its quote, each
                                          piece a selection, and a statement with no quote, or one whose quote is
                                          not in the transcript, to its whole passage
    a code (thematic analysis)            a code, once for the project, its description from the code list,
                                          applied to each of its extracts
    a quote waiting for a statement       a selection with no code, which the reader makes a blank statement
    an exploratory note, an interviewer   a note, linked to a selection of its passage
    note
    a PET, a sub-PET (IPA)                a code that cannot be coded, under the participant's code, in the
                                          board's order, its description its own, each PET also a set of the
                                          statements under it, which the reader's PET draft takes
    Not placed, Set aside                 a code of each name under the participant's, holding those statements
    a theme, a sub-theme (TA)             a code that cannot be coded holding its codes, and each theme a set
    a GET                                 a set of the PETs and statements under it, its note a member note
    a participant                         a case holding its sources, and a code holding its PETs (IPA)
    a label's note                        a note linked to its code

The boards are each participant's PETs board as the GETs take it (`gets.source_board`: the board marked
complete, else the Current board, else the one last open), at each timepoint in a project of two or
more. Nothing here writes a project's file. The standard library and the app's own readers alone.
"""
from __future__ import annotations

import os
import re
import tempfile
import uuid
import zipfile
from datetime import datetime, timezone
from pathlib import Path
from xml.etree import ElementTree as ET

import audio as audio_mod
import convert as convert_mod
import gets as gets_mod
import i18n
import qdpx as qdpx_mod
import themes as themes_mod
import workbook as wb_mod
from workbook import WorkbookError

NS = "urn:QDA-XML:project:1.0"
SUFFIX = ".qdpx"
# the most one file inside a package may weigh, as the standard sets it (8.5 Limitations)
MEDIA_MOST = 2 ** 31 - 1


def guid() -> str:
    return str(uuid.uuid4())


def squash_map(text: str) -> tuple[str, list[int]]:
    """A passage's words with each run of spaces one space and none at either end, as `convert._squash`
    makes them, and where each character of the passage stands in that, so a quote found in the passage
    is placed in the words written."""
    out: list[str] = []
    at: list[int] = []
    for ch in str(text or ""):
        if ch.isspace():
            if out and out[-1] != " ":
                out.append(" ")
            at.append(max(len(out) - 1, 0))
        else:
            out.append(ch)
            at.append(len(out) - 1)
    while out and out[-1] == " ":
        out.pop()
    return "".join(out), at


def speaker_name(name: str) -> str:
    """A speaker's name as a passage's label carries it, one the reader takes as a name (`convert.label_of`):
    the name itself, else its words opening on capitals, else "Speaker"."""
    text = " ".join(str(name or "").split())
    if not text:
        return convert_mod.SPEAKER
    for tried in (text, " ".join(w[:1].upper() + w[1:] for w in text.split()[:4])[:40]):
        if re.fullmatch(convert_mod.NAME, tried) and convert_mod.good_name(tried):
            return tried
    return convert_mod.SPEAKER


# ------------------------------------------------------------------ a sheet as a source

class Source:
    """One interview as the package holds it: its text, where each passage's words begin, its selections,
    and its recording when there is one."""

    def __init__(self, name: str, rows: list[dict], counts: dict):
        self.guid, self.text_guid, self.name = guid(), guid(), name
        self.rows = rows
        self.selections: list[dict] = []
        self.coded: dict[tuple[int, int], dict] = {}
        self.media: dict | None = None
        self.offset = 0.0
        parts, self.places, self.starts, self.seconds = [], {}, {}, {}
        at, last = 0, None
        for i, row in enumerate(rows):
            words, where = squash_map(row.get("text") or "")
            if not words:
                continue
            seconds = row.get("seconds")
            if seconds is None:
                counts["untimed"] += 1
                seconds = last if last is not None else 0
            last = seconds
            said = speaker_name(row.get("name"))
            if said != " ".join(str(row.get("name") or "").split()):
                counts["renamed"] += 1
            head = f"[{wb_mod.hhmmss(seconds)}] {said}: "
            line = head + words
            self.starts[i], self.places[i], self.seconds[i] = at, (at + len(head), where, len(words)), seconds
            parts.append(line)
            at += len(line) + 2
        self.text = "\n\n".join(parts) + ("\n" if parts else "")

    def span(self, i: int, start: int | None = None, end: int | None = None) -> tuple[int, int] | None:
        """Where a passage's words, or a piece of them by its place in the passage, stand in the text."""
        if i not in self.places:
            return None
        body, where, length = self.places[i]
        if start is None:
            return body, body + length
        if not where or end <= start:
            return None
        a, b = where[min(start, len(where) - 1)], where[min(end, len(where)) - 1] + 1
        return (body + a, body + min(b, length)) if b > a else None

    def code(self, span: tuple[int, int], code: str, name: str) -> None:
        """A code on a piece of the text, its selection named by its whole quote, as ATLAS.ti names a quotation
        by its words, so Idiograph's own import keeps two quotes of one code on one passage apart. Two codes on
        the same piece of the same quote are one selection with two codings. A statement with no quote is coded
        on its whole passage, its selection named `qdpx.WHOLE`, which Idiograph's import reads as no quote."""
        sel = self.coded.get((span, name))
        if sel is None:
            sel = {"guid": guid(), "start": span[0], "end": span[1], "codes": [], "notes": [], "name": name}
            self.coded[(span, name)] = sel
            self.selections.append(sel)
        if code not in sel["codes"]:
            sel["codes"].append(code)

    def loose(self, span: tuple[int, int]) -> None:
        self.selections.append({"guid": guid(), "start": span[0], "end": span[1], "codes": [], "notes": []})

    def noted(self, span: tuple[int, int], notes: list[str]) -> None:
        self.selections.append({"guid": guid(), "start": span[0], "end": span[1], "codes": [], "notes": notes})


def sheet_source(label: str, sheet: dict, plan: dict, code_of, interviewer: str) -> Source:
    """One sheet as a source: each passage's text, its statements' quotes coded, its loose quotes, its notes.
    `code_of(sheet, row, line, statement)` is the code a statement takes, None for none."""
    counts = plan["counts"]
    rows = sheet["rows"]
    src = Source(f"{label} - {sheet['name']}", rows, counts)
    for i, row in enumerate(rows):
        own = src.span(i)
        statements = [p for p in row.get("pairs") or []]
        if own is None:
            counts["no_words"] += sum(1 for p in statements if p.get("es"))
            continue
        line = 0
        for pair in statements:
            es, kq = str(pair.get("es") or ""), str(pair.get("kq") or "")
            found = wb_mod.quote_turns(rows, i, kq, interviewer) if kq else []
            spans = [src.span(k, s, e) for k, s, e in found]
            spans = [s for s in spans if s]
            if es:
                code = code_of(sheet["name"], row["row"], line, es)
                line += 1
                if code is None:
                    continue
                if not kq:
                    counts["no_quote"] += 1
                elif not spans:
                    counts["quote_missing"] += 1
                if len({k for k, _s, _e in found}) > 1:
                    counts["across"] += 1
                name = qdpx_mod.ELLIPSIS.join(src.text[a:b] for a, b in spans) if spans else qdpx_mod.WHOLE
                for span in spans or [own]:
                    src.code(span, code, name)
                counts["quotes"] += 1 if spans else 0
            elif spans:
                # a quote waiting for its statement, each piece a selection of its own
                for span in spans:
                    src.loose(span)
                counts["loose"] += 1
        notes = []
        for kind, field in (("exploratory", "en"), ("interviewer", "note")):
            for entry in str(row.get(field) or "").split("\n"):
                entry = entry.strip()
                if entry:
                    named = (i18n.t("exports.qdpx_note_exploratory") if kind == "exploratory"
                             else i18n.t("exports.qdpx_note_interviewer"))
                    note = {"guid": guid(), "name": named, "text": entry}
                    plan["notes"].append(note)
                    notes.append(note["guid"])
                    counts["notes" if kind == "exploratory" else "interviewer_notes"] += 1
        if notes:
            src.noted(own, notes)
    return src


# ------------------------------------------------------------------ the boards

def node(name: str, codable: bool, description: str = "", notes=None) -> dict:
    return {"guid": guid(), "name": " ".join(str(name or "").split()) or themes_mod.UNTITLED, "codable": codable,
            "description": description, "notes": list(notes or []), "children": []}


def label_note(plan: dict, group: dict) -> list[str]:
    """A label's note as a note of the package, its guid in a list, or none."""
    text = str(group.get("note") or "").strip()
    if not text:
        return []
    note = {"guid": guid(), "name": i18n.t("exports.qdpx_note_label"), "text": text}
    plan["notes"].append(note)
    plan["counts"]["label_notes"] += 1
    return [note["guid"]]


def statement_keys(case: dict) -> dict[str, dict]:
    """Every statement of a workbook by its card's key, `<sheet>:<row>:<line>`, as `themes.read_cards` keys them."""
    out = {}
    for sheet in case["sheets"]:
        for row in sheet["rows"]:
            line = 0
            for pair in row.get("pairs") or []:
                if pair.get("es"):
                    out[themes_mod.card_key(sheet["name"], row["row"], line)] = {"text": pair["es"]}
                    line += 1
    return out


def pets_tree(plan: dict, book: Path, statements: dict[str, dict], timepoint: int | None) -> tuple[list[dict], list[dict], dict]:
    """A participant's PETs at a timepoint as codes: each PET a node in the board's order, its sub-PETs and
    statements inside in the order the canvas reads them, the stacked after their top, then Not placed and
    Set aside. Answers the nodes, each PET's set, `{"name", "description", "codes"}`, and each PET's and
    sub-PET's code by its id on the board."""
    counts = plan["counts"]
    with themes_mod.scoped(timepoint):
        read = themes_mod.read_cards(book)
        data = themes_mod.load(book)
        board = gets_mod.source_board(data)[0] if data else None
    live = [c["key"] for c in read["cards"] if c["key"] in statements]
    if board is None:
        loose = node(i18n.t("exports.not_placed"), False)
        loose["children"] = [statements[k]["node"] for k in live if not statements[k].get("used")]
        for k in live:
            statements[k]["used"] = True
        return ([loose] if loose["children"] else []), [], {}
    version = themes_mod.follow(board, read["cards"], read["quotes"])
    by_id = {g["id"]: g for g in version["groups"]}
    parents = themes_mod.parents_of(version["groups"])
    drawn = themes_mod.layout_boxes(version)
    stacks = version.get("stacks") or {}
    ids: dict[str, str] = {}

    def take(key: str, into: dict, members: list[str]) -> None:
        for k in [key] + list(stacks.get(key) or []):
            st = statements.get(k)
            if st and not st.get("used"):
                st["used"] = True
                into["children"].append(st["node"])
                members.append(st["node"]["guid"])

    def group_node(gid: str, members: list[str], seen: frozenset) -> dict:
        g = by_id[gid]
        out = node(g["label"], False, themes_mod.description_of(g), label_note(plan, g))
        ids[gid] = out["guid"]
        for m in themes_mod.theme_order(version, gid, drawn):
            if m in by_id:
                if m not in seen:
                    out["children"].append(group_node(m, members, seen | {m}))
                    counts["sub_pets"] += 1
            else:
                take(m, out, members)
        return out

    nodes, sets = [], []
    for gid in themes_mod.canvas_order([g["id"] for g in version["groups"] if g["id"] not in parents], by_id):
        members: list[str] = []
        nodes.append(group_node(gid, members, frozenset({gid})))
        counts["pets"] += 1
        sets.append({"guid": guid(), "name": by_id[gid]["label"], "description": themes_mod.description_of(by_id[gid]),
                     "codes": members})
    aside = node(i18n.t("exports.qdpx_set_aside"), False)
    for key in version.get("discarded") or []:
        take(key, aside, [])
    loose = node(i18n.t("exports.not_placed"), False)
    for key in live:
        take(key, loose, [])
    nodes += [n for n in (loose, aside) if n["children"]]
    counts["sticky_notes"] += len(version.get("notes") or [])
    return nodes, sets, ids


def gets_sets(plan: dict, root: Path, pets: dict, statements: dict, chosen: set) -> list[dict]:
    """The GETs board on the canvas, each GET a set of the PETs and statements under it at any depth, in the
    board's order, only the participants exported. `pets` is each participant's PET codes by id and
    `statements` each one's statement codes by key."""
    counts = plan["counts"]
    data = gets_mod.load(root)
    boards = gets_mod.boards_of(data)
    if not boards:
        return []
    board = next((b for b in boards if b.get("id") == data.get("current")), boards[0])
    kept = gets_mod.normal(board, data)
    by_id = {g["id"]: g for g in kept["groups"]}
    parents = themes_mod.parents_of(kept["groups"])
    out = []

    def under(gid: str, seen: frozenset, into: list[str]) -> None:
        for m in by_id[gid]["members"]:
            if m in by_id:
                if m not in seen:
                    under(m, seen | {m}, into)
                continue
            k = gets_mod.split_key(m)
            if k["case"] not in chosen:
                continue
            code = (pets.get(k["case"], {}).get(k["ident"]) if k["kind"] == "group"
                    else (statements.get(k["case"], {}).get(k["ident"]) or {}).get("node", {}).get("guid")
                    if k["kind"] == "es" else None)
            if k["kind"] == "pn":
                counts["participant_notes"] += 1
            elif code and code not in into:
                into.append(code)

    for gid in themes_mod.canvas_order([g["id"] for g in kept["groups"] if g["id"] not in parents], by_id):
        members: list[str] = []
        under(gid, frozenset({gid}), members)
        g = by_id[gid]
        # a GET's note travels as its set's member note, which the standard's Set holds (qdpxround)
        out.append({"guid": guid(), "name": g["label"], "description": themes_mod.description_of(g), "codes": members,
                    "notes": label_note(plan, g)})
        counts["gets"] += 1
    return out


def themes_tree(plan: dict, root: Path, codes: dict[str, dict], row_code: dict) -> list[dict]:
    """A thematic analysis project's Themes board as codes: each theme a node holding its sub-themes and its
    codes, a code in the first theme that holds one of its extracts, then the codes in no theme. Each theme is
    a set of its codes too. `codes` is each code by its name as the code list compares names, `row_code`
    each extract's code by its participant and its card's key."""
    counts = plan["counts"]
    data = gets_mod.load(root)
    boards = gets_mod.boards_of(data)
    nodes: list[dict] = []
    if boards:
        board = next((b for b in boards if b.get("id") == data.get("current")), boards[0])
        kept = gets_mod.normal(board, data)
        by_id = {g["id"]: g for g in kept["groups"]}
        parents = themes_mod.parents_of(kept["groups"])

        def theme(gid: str, seen: frozenset, members: list[str]) -> dict:
            g = by_id[gid]
            out = node(g["label"], False, themes_mod.description_of(g), label_note(plan, g))
            for m in g["members"]:
                if m in by_id:
                    if m not in seen:
                        out["children"].append(theme(m, seen | {m}, members))
                    continue
                k = gets_mod.split_key(m)
                name = row_code.get((k["case"], k["ident"])) if k["kind"] == "es" else None
                code = codes.get(name) if name else None
                if code and not code.get("used"):
                    code["used"] = True
                    out["children"].append(code["node"])
                    members.append(code["node"]["guid"])
            return out

        for gid in themes_mod.canvas_order([g["id"] for g in kept["groups"] if g["id"] not in parents], by_id):
            members: list[str] = []
            nodes.append(theme(gid, frozenset({gid}), members))
            counts["themes"] += 1
            plan["sets"].append({"guid": guid(), "name": by_id[gid]["label"],
                                 "description": themes_mod.description_of(by_id[gid]), "codes": members})
    nodes += [c["node"] for c in codes.values() if not c.get("used")]
    return nodes


# ------------------------------------------------------------------ the plan

def fresh_counts() -> dict:
    keys = ("statements", "quotes", "no_quote", "quote_missing", "across", "loose", "notes", "interviewer_notes",
            "label_notes", "pets", "sub_pets", "gets", "themes", "codes", "sources", "recordings", "recordings_left",
            "untimed", "renamed", "no_words", "sticky_notes", "participant_notes")
    return {k: 0 for k in keys}


def plan(root: Path, name: str, method: str, question: str, people: list[dict], timepoints: list[dict],
         recordings: bool = False, codebook: dict | None = None, version: str = "") -> dict:
    """The package for `people`, each `{"label", "book"}` and with `portrait` the participant's pen portrait, their
    case's description (pbiobuild), its workbook read here (`workbook.read_case`, a
    workbook open in Excel refused), as plain records the writer takes: the codes as a tree, the sources,
    notes, sets and cases, and `counts`. `timepoints` the project's, `codebook` a thematic analysis project's
    code list (`codes.load`), `recordings` whether each sheet's recording goes in."""
    root = Path(root)
    out = {"name": name, "method": method, "question": question, "user": guid(), "codes": [], "sources": [],
           "notes": [], "sets": [], "cases": [], "counts": fresh_counts(), "origin": f"Idiograph {version}".strip()}
    counts = out["counts"]
    interviewer = wb_mod.interviewer_name()
    longitudinal = len(timepoints or []) > 1
    ta = method == "ta"
    import codes as codes_mod
    codes: dict[str, dict] = {}
    if ta:
        for c in (codebook or {}).get("codes") or []:
            codes[codes_mod.norm(c["name"])] = {"node": node(c["name"], True, c.get("description") or "")}
    row_code: dict = {}
    pets_by: dict[str, dict] = {}
    statements_by: dict[str, dict] = {}
    for person in people:
        label, book = person["label"], Path(person["book"])
        case = wb_mod.read_case(book)
        statements = statement_keys(case)
        statements_by[label] = statements
        if not ta:
            for key, st in statements.items():
                st["node"] = node(st["text"], True)
        counts["statements"] += len(statements)

        def code_of(sheet, row, line, es, statements=statements, label=label):
            key = themes_mod.card_key(sheet, row, line)
            if ta:
                n = codes_mod.norm(es)
                if n not in codes:
                    codes[n] = {"node": node(codes_mod.words(es), True)}
                row_code[(label, key)] = n
                return codes[n]["node"]["guid"]
            st = statements.get(key)
            return st["node"]["guid"] if st else None

        sources = []
        for sheet in case["sheets"]:
            src = sheet_source(label, sheet, out, code_of, interviewer)
            if not src.text:
                continue
            if recordings:
                found = audio_mod.for_sheet(book, sheet["name"])
                if found is not None:
                    if found.stat().st_size > MEDIA_MOST:
                        counts["recordings_left"] += 1
                    else:
                        src.media = {"path": found, "guid": guid(), "ext": found.suffix.lower()}
                        src.offset = audio_mod.offset_for(book, sheet["name"])
                        counts["recordings"] += 1
            sources.append(src)
        out["sources"] += sources
        counts["sources"] += len(sources)
        out["cases"].append({"guid": guid(), "name": label, "sources": [s.guid for s in sources],
                             "description": str(person.get("portrait") or "")})
        if ta:
            continue
        who = node(label, False)
        pets_by[label] = {}
        for n in ([tp["n"] if isinstance(tp, dict) and "n" in tp else i + 1 for i, tp in enumerate(timepoints)]
                  if longitudinal else [None]):
            nodes, sets, ids = pets_tree(out, book, statements, n)
            if n is None or n == 1:
                pets_by[label] = ids
            if longitudinal:
                tp = timepoints[n - 1]
                held = node(str(tp.get("label") or f"T{n}"), False)
                held["children"] = nodes
                nodes = [held] if nodes else []
            who["children"] += nodes
            out["sets"] += sets
        # a statement no board names, on a sheet no timepoint reads, still a code under its participant
        rest = [st["node"] for st in statements.values() if not st.get("used")]
        if rest:
            loose = node(i18n.t("exports.not_placed"), False)
            loose["children"] = rest
            who["children"].append(loose)
        out["codes"].append(who)
    if ta:
        out["codes"] = themes_tree(out, root, codes, row_code)
        counts["statements"] = sum(1 for _ in row_code)
        counts["codes"] = len(codes)
    elif not longitudinal:
        out["sets"] += gets_sets(out, root, pets_by, statements_by, {p["label"] for p in people})
    return out


# ------------------------------------------------------------------ the writing

def tag(name: str) -> str:
    return f"{{{NS}}}{name}"


def sub(parent, element: str, **attrs) -> ET.Element:
    return ET.SubElement(parent, tag(element), {k: str(v) for k, v in attrs.items() if v is not None})


def text_of(parent, name: str, words: str) -> None:
    if words:
        sub(parent, name).text = words


def code_el(parent, c: dict) -> None:
    el = sub(parent, "Code", guid=c["guid"], name=c["name"], isCodable="true" if c["codable"] else "false")
    text_of(el, "Description", c.get("description") or "")
    for n in c.get("notes") or []:
        sub(el, "NoteRef", targetGUID=n)
    for child in c["children"]:
        code_el(el, child)


def selection_el(parent, element: str, sel: dict, user: str, when: str, points: dict | None = None) -> None:
    if points is None:
        el = sub(parent, element, guid=sel["guid"], name=sel.get("name"), startPosition=sel["start"],
                 endPosition=sel["end"], creatingUser=user, creationDateTime=when)
    else:
        el = sub(parent, element, guid=sel["guid"], name=sel.get("name"), fromSyncPoint=points[sel["start"]],
                 toSyncPoint=points[sel["end"]], creatingUser=user, creationDateTime=when)
    for code in sel["codes"]:
        coding = sub(el, "Coding", guid=guid(), creatingUser=user, creationDateTime=when)
        sub(coding, "CodeRef", targetGUID=code)
    for n in sel["notes"]:
        sub(el, "NoteRef", targetGUID=n)


def sync_points(src: Source) -> tuple[list[tuple[int, int, str]], dict[int, str]]:
    """A recording's sync points: one where each passage starts at its time, the recording's offset added, and
    one at each end of a selection at its passage's time, so the reader times each passage by the point
    where it starts. Each `(position, milliseconds, guid)`, and each position's guid."""
    def ms(seconds) -> int:
        return max(0, int(round((float(seconds or 0) + src.offset) * 1000)))

    marks: dict[int, int] = {}
    order = sorted(src.starts.items(), key=lambda kv: kv[1])
    for i, at in order:
        marks[at] = ms(src.seconds[i])
    for sel in src.selections:
        for at in (sel["start"], sel["end"]):
            if at not in marks:
                held = [i for i, s in order if s <= at]
                marks[at] = ms(src.seconds[held[-1]]) if held else 0
    points = sorted((at, t, guid()) for at, t in marks.items())
    return points, {at: g for at, _t, g in points}


def qde(p: dict) -> bytes:
    """project.qde, in the order Project.xsd asks: Users, CodeBook, Cases, Sources, Notes, Sets, Description."""
    ET.register_namespace("", NS)
    when = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    project = ET.Element(tag("Project"), {"name": p["name"] or "Idiograph", "origin": p["origin"],
                                          "creatingUserGUID": p["user"], "creationDateTime": when})
    users = sub(project, "Users")
    sub(users, "User", guid=p["user"], name="Idiograph")
    if p["codes"]:
        book = sub(project, "CodeBook")
        held = sub(book, "Codes")
        for c in p["codes"]:
            code_el(held, c)
    if p["cases"]:
        cases = sub(project, "Cases")
        for c in p["cases"]:
            case = sub(cases, "Case", guid=c["guid"], name=c["name"])
            # the participant's pen portrait (pbiobuild), first, as Project.xsd's CaseType asks
            text_of(case, "Description", c.get("description") or "")
            for s in c["sources"]:
                sub(case, "SourceRef", targetGUID=s)
    if p["sources"]:
        sources = sub(project, "Sources")
        for src in p["sources"]:
            path = f"internal://{src.text_guid}.txt"
            if src.media:
                el = sub(sources, "AudioSource", guid=src.guid, name=src.name,
                         path=f"internal://{src.media['guid']}{src.media['ext']}", creatingUser=p["user"],
                         creationDateTime=when)
                script = sub(el, "Transcript", guid=guid(), name=src.name, plainTextPath=path,
                             creatingUser=p["user"], creationDateTime=when)
                points, at = sync_points(src)
                for position, ms, g in points:
                    sub(script, "SyncPoint", guid=g, timeStamp=ms, position=position)
                for sel in src.selections:
                    selection_el(script, "TranscriptSelection", sel, p["user"], when, at)
            else:
                el = sub(sources, "TextSource", guid=src.guid, name=src.name, plainTextPath=path,
                         creatingUser=p["user"], creationDateTime=when)
                for sel in src.selections:
                    selection_el(el, "PlainTextSelection", sel, p["user"], when)
    if p["notes"]:
        notes = sub(project, "Notes")
        for n in p["notes"]:
            note = sub(notes, "Note", guid=n["guid"], name=n["name"], creatingUser=p["user"], creationDateTime=when)
            sub(note, "PlainTextContent").text = n["text"]
    sets = [s for s in p["sets"] if s["codes"]]
    if sets:
        held = sub(project, "Sets")
        for s in sets:
            el = sub(held, "Set", guid=s["guid"], name=s["name"])
            text_of(el, "Description", s.get("description") or "")
            for c in s["codes"]:
                sub(el, "MemberCode", targetGUID=c)
            for n in s.get("notes") or []:
                sub(el, "MemberNote", targetGUID=n)
    text_of(project, "Description", p.get("question") or "")
    return ET.tostring(project, encoding="utf-8", xml_declaration=True)


def write(p: dict, dest: Path) -> int:
    """The package written to `dest`, a new file, through a temporary file beside it, so a failure leaves
    nothing there. Answers its size in bytes."""
    dest = Path(dest)
    fd, tmp = tempfile.mkstemp(prefix=".qdpx-", suffix=".tmp", dir=str(dest.parent))
    os.close(fd)
    tmp = Path(tmp)
    try:
        with zipfile.ZipFile(tmp, "w", zipfile.ZIP_DEFLATED) as z:
            z.writestr("project.qde", qde(p))
            for src in p["sources"]:
                z.writestr(f"Sources/{src.text_guid}.txt", src.text.encode("utf-8"))
                if src.media:
                    z.write(src.media["path"], f"Sources/{src.media['guid']}{src.media['ext']}",
                            compress_type=zipfile.ZIP_STORED)
        if dest.exists():
            raise WorkbookError(i18n.t("server.qdpx_out_there", name=dest.name))
        os.replace(tmp, dest)
        return dest.stat().st_size
    finally:
        tmp.unlink(missing_ok=True)


def target(to, name: str) -> Path:
    """Where an export writes: in a folder given, the project's name with .qdpx, and a file named without
    .qdpx given it."""
    path = Path(str(to or "")).expanduser()
    if path.is_dir():
        return (path / f"{file_name(name)}").resolve()
    if path.suffix.lower() != SUFFIX:
        path = path.with_name(path.name + SUFFIX)
    return path.resolve()


def file_name(name: str) -> str:
    """The file's name, the project's name with .qdpx, any character a file name cannot hold left out."""
    clean = re.sub(r'[\\/:*?"<>|\x00-\x1f]', "", " ".join(str(name or "").split())).strip(". ") or "Idiograph"
    return clean + SUFFIX
