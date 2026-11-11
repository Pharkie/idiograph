#!/usr/bin/env python3
"""GETs: the cross-case step after the PETs, every case's PETs grouped into group experiential
themes on a canvas, the PETs canvas one layer up.

The study is every case of the project with an annotated workbook. Each case comes in as a copy,
the snapshot, of the board its PETs were marked complete on, else its Current board, else the
board last open: every PET and sub-theme with its title, note, parent, sub-themes, statements and
picks, and every statement of the case with its sheet, timecode, words, quotes and exploratory
notes. Nothing here writes a workbook or a themes file, and opening writes nothing: the file takes
every case not yet in on his first act.

The file is `idiograph-gets.json` at the case root, beside `idiograph-project.json`:

    {"schema": 1, "created": "...", "updated": "...", "current": "b1", "chosen": "b1", "complete": null,
     "settings": {"minimum": null, "one_per_pet": true},
     "study": {"P2 - Rowan": {"in": true}, "P1 - Pilot": {"in": false, "reason": "a pilot"}},
     "colours": {"P1 - Pilot": 4},
     "cases": {"P2 - Rowan": {"workbook": "P2 Rowan - EN & ES.xlsx", "board": "v3", "name": "Board 3",
                 "complete": true, "came": "...", "seen": {"workbook": 0, "themes": 0},
                 "hash": "<state hash>", "state": "in",
                 "pets": [{"id": "g1", "title": "...", "note": "...", "parent": null, "subs": ["g2"],
                           "statements": ["Initial:12:0"], "picks": ["Initial:12:0"]}],
                 "lines": {"Initial:12:0": {"sheet": "Initial", "row": 12, "time": "02:10", "seconds": 130,
                           "text": "...", "quotes": ["..."], "notes": ["..."], "pet": "g1", "discarded": false}}}},
     "boards": [{"id": "b1", "name": "Board 1", "note": "", "created": "...", "updated": "...",
                 "cards": {"P2 - Rowan/g1": {"x": 0, "y": 0},
                           "P2 - Rowan/es/Initial:12:0": {"x": 0, "y": 0, "text": "..."},
                           "P2 - Rowan/pn/1": {"x": 0, "y": 0, "text": "..."}},
                 "groups": [{"id": "G1", "label": "...", "members": ["P2 - Rowan/g1"], "x": 0, "y": -40}],
                 "discarded": [], "picks": {}, "notes": [], "rows": {}, "history": [...]}]}

Cases go by the pseudonym in each themes file's `case`. A card's key names its case and kind: a
PET or a sub-theme by its group id, a sub-theme's groups at any depth riding inside its card with
no card of their own though the copy keeps them, a second card of one under another GET with `/2` after it, `es`
a statement and `pn` a participant note, his words on what he knows of the participant beyond the
transcript. `settings` holds the study's own, since the demo's project file refuses a save:
`minimum`, null for Smith's (2011a) band, and `one_per_pet`, on by default. `state` is `in` for a
case that came in from a board and `none` for one with no PETs yet. `colours` holds the colour he
chose for a case in the Cases panel, by its label, a place in the cases' palette, and is missing
until he chooses one, a case with none taking its place in case order round the palette.

`hash` is the snapshot's hash as `themes.state_hash` makes one. `seen` (20 October) holds each of
the case's two files' modification times in nanoseconds as the snapshot read them, null for a themes
file not there yet. On each open a case whose workbook and themes file both stand as `seen` has them
is unchanged without a read, and any other is snapshotted again and compared, so a difference marks
it changed, and the copy stands until Take the changes. A case that came in before `seen` was kept
goes by `came`, to the whole second, as it always has. Standard library and the themes module alone.
"""
from __future__ import annotations

import contextlib
import contextvars
import json
import math
import os
import re
from datetime import datetime
from pathlib import Path

import formats
import i18n
import themes
from workbook import (WorkbookError, no_quote, note_written, time_span, timecode, timecodes_at, timecodes_for,
                      written_here)

FILE = "idiograph-gets.json"
SCHEMA = 1
FIRST_BOARD = "b1"
FIRST_NAME = themes.FIRST_NAME
OPS = themes.OPS
BOARD_OPS = ("revision", "view", "restore", "subs")
SETTINGS = {"minimum": None, "one_per_pet": True}
# a GETs card carries its kind and its case over its words, "PET · Rowan", a line the PETs
# screen's cards do not have, so every estimate of its height takes that line on
KICKER_H = 18
# the cases' palette, `--th-case0` to `--th-case24` in themes.css, the eight of 16 October first and More
# colours' seventeen after them (21 October), named as the picker names them
COLOUR_NAMES = ("Blue", "Olive", "Plum", "Brown", "Indigo", "Teal", "Purple", "Slate",
                "Moss", "Spruce", "Violet", "Aubergine", "Pine", "Denim", "Khaki", "Mulberry", "Fern", "Periwinkle", "Umber",
                "Grape", "Ocean", "Amethyst", "Jade", "Navy", "Fig")
COLOURS = len(COLOUR_NAMES)


# LPETs (21 October, timepoints part 2, Farr and Nizza 2019): a participant's longitudinal PETs, made from
# their PETs at each timepoint as GETs are made from every participant's PETs, so this module runs them too.
# Inside `lpets` the file is that participant's, `<case>/Working/<stem>.lpets.json`, and each "case" is a
# timepoint, `T1`, `T2`, named on the cards by its label (see `who`), each book carrying its `timepoint`,
# whose PETs file and sheets its snapshot reads (see `themes.scoped`), its `cite`, the label a quote's time
# is cited with, "T1, 35:55", and `missing` for a timepoint the participant was not interviewed at.
FILE_AT: contextvars.ContextVar = contextvars.ContextVar("idiograph_lpets_file", default=None)
NAMES: contextvars.ContextVar = contextvars.ContextVar("idiograph_lpets_names", default=None)
LPETS_TAIL = ".lpets.json"


def lpets_path(workbook: Path) -> Path:
    """A participant's LPETs file, beside their PETs files in `Working/`."""
    workbook = Path(workbook)
    return workbook.parent / "Working" / f"{workbook.stem}{LPETS_TAIL}"


@contextlib.contextmanager
def lpets(workbook: Path, names: dict):
    """What runs inside works on the participant's LPETs, `names` each timepoint's label by its key."""
    at, named, up = FILE_AT.set(lpets_path(workbook)), NAMES.set(dict(names)), LGETS.set(None)
    try:
        yield
    finally:
        FILE_AT.reset(at)
        NAMES.reset(named)
        LGETS.reset(up)


def in_lpets() -> bool:
    return NAMES.get() is not None


# LGETs (21 October, timepoints part 3): in a project of two or more timepoints the project's board across its
# participants is made from each participant's LPETs, as GETs are made from their PETs, so this module runs it
# too, and there are no GETs at a single timepoint (Adam's answer of 20 October). Inside `lgets` the file is
# `idiograph-lgets.json` at the project's root, beside the GETs file, which stays as it was for a project that
# goes back to one timepoint. Each case is a participant, its copy read from their LPETs file (see
# `lpets_snapshot`): each LPET and sub-LPET a "PET" of the copy, every statement under its timepoint PETs a
# line, cited with its timepoint, `at` the timepoint by its place and `cite` its label then.
LGETS_FILE = "idiograph-lgets.json"
LGETS: contextvars.ContextVar = contextvars.ContextVar("idiograph_lgets_names", default=None)


@contextlib.contextmanager
def lgets(root: Path, names: dict):
    """What runs inside works on the project's LGETs, `names` each timepoint's label by its key, `T1`."""
    at, up, named = FILE_AT.set(Path(root) / LGETS_FILE), LGETS.set(dict(names)), NAMES.set(None)
    try:
        yield
    finally:
        FILE_AT.reset(at)
        LGETS.reset(up)
        NAMES.reset(named)


def in_lgets() -> bool:
    return LGETS.get() is not None


def lpets_snapshot(workbook: Path) -> dict:
    """A participant as LGETs take them in, read afresh from their LPETs file: the board their LPETs were
    marked complete on, else its Current board, else the board last open, each LPET with its sub-LPETs and
    the statements under the timepoint PETs in it, and every statement of their LPETs' copies, cited with its
    timepoint. A participant with no LPETs file has no LPETs. Nothing is written."""
    workbook = Path(workbook)
    seen = seen_of(workbook)
    names = LGETS.get() or {}
    with lpets(workbook, names):
        data = load(workbook) or {}
    board, complete = source_board(data)
    held = data.get("cases") if isinstance(data.get("cases"), dict) else {}
    lines = {}
    for tkey, rec in held.items():
        if not isinstance(rec, dict):
            continue
        for key, line in (rec.get("lines") or {}).items():
            if isinstance(line, dict):
                lines[key] = dict(line, at=tkey, cite=rec.get("cite") or names.get(tkey) or tkey, pet=None,
                                  discarded=False)
    pets = []
    if board is not None:
        groups = [g for g in board.get("groups") or [] if isinstance(g, dict) and g.get("id")]
        by_id = {g["id"]: g for g in groups}
        owners = themes.parents_of(groups)
        thrown = set(board.get("discarded") or [])

        def under_card(member: str) -> list[str]:
            k = split_key(member)
            if k["kind"] == "es":
                return [k["ident"]] if k["ident"] in lines else []
            if k["kind"] != "group":
                return []
            pets_of = {q["id"]: q for q in ((held.get(k["case"]) or {}).get("pets") or []) if isinstance(q, dict)}
            return [x for x in under(k["ident"], pets_of) if x in lines] if k["ident"] in pets_of else []

        def walk(gid: str, been: frozenset) -> None:
            g = by_id[gid]
            members = [m for m in g.get("members") or [] if m not in thrown]
            mine = []
            for m in members:
                if m in by_id:
                    continue
                for key in under_card(m):
                    if key not in mine:
                        mine.append(key)
                    if lines[key]["pet"] is None:
                        lines[key]["pet"] = gid
            pets.append(dict({"id": gid, "title": str(g.get("label") or ""), "note": str(g.get("note") or ""),
                              "parent": owners.get(gid), "subs": [m for m in members if m in by_id], "statements": mine,
                              "picks": []}, **described(g)))
            for m in members:
                if m in by_id and m not in been:
                    walk(m, been | {m})

        for gid in themes.canvas_order([g["id"] for g in groups if g["id"] not in owners], by_id):
            walk(gid, frozenset({gid}))
        for member in thrown:
            for key in under_card(member):
                lines[key]["discarded"] = lines[key]["pet"] is None
    return {"board": board["id"] if board else None, "name": board.get("name") if board else None,
            "complete": bool(complete and board), "pets": pets, "lines": lines, "seen": seen}


# ------------------------------------------------------------------ the file

def gets_path(root: Path) -> Path:
    """The GETs file at the project's root, or inside `lpets` the participant's LPETs file."""
    held = FILE_AT.get()
    return held if held is not None else Path(root) / FILE


def load(root: Path) -> dict | None:
    """The GETs file as it sits on disk, or None when there is none yet. One that is there and
    cannot be read is refused, so nothing is ever written over a file that can be recovered."""
    path = gets_path(root)
    if not path.exists():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        raise WorkbookError(i18n.t("server.could_read_nothing_written", name=path.name))
    if not isinstance(data, dict):
        raise WorkbookError(i18n.t("server.gets_file_nothing_written", name=path.name))
    if in_lgets() and isinstance(data.get("cases"), dict):
        # on LGETs each statement cited by its timepoint's label as it is now
        for rec in data["cases"].values():
            for line in ((rec.get("lines") if isinstance(rec, dict) else None) or {}).values():
                label = LGETS.get().get(line.get("at")) if isinstance(line, dict) else None
                if label and line.get("cite") and line["cite"] != label:
                    bare = uncited(line.get("time"), line["cite"])
                    line.update(time=f"{label}, {bare}" if bare else label, cite=label)
    named = NAMES.get()
    if in_lpets() and named and isinstance(data.get("cases"), dict):
        # each timepoint cited by its label as it is now, whatever it was when its PETs came in
        for case, rec in data["cases"].items():
            if isinstance(rec, dict) and rec.get("cite") and named.get(case) and rec["cite"] != named[case]:
                recite(rec, named[case])
    # every time read as the project writes its timecodes, the file keeping its own (see `KEPT_AS`)
    retime(data, timecodes_for(root) if in_lpets() else timecodes_at(root))
    return data


# The file keeps every statement's time one way, 1:15:12, whatever the project's timecodes, so a project
# that changes them changes nothing in its files and no case reads as changed since it came in. `load`
# gives each time as the project writes it (28 October, Adam: timecodes are the project's).
KEPT_AS = "1:15:12"


def retime(data: dict | None, form: str) -> dict | None:
    """Every line's time in the file's data rewritten from its seconds as `form` says, a time cited with
    its timepoint, "T1, 35:55", keeping its timepoint, and a line with no seconds left as it is. In place."""
    cases = (data or {}).get("cases") if isinstance(data, dict) else None
    for rec in (cases or {}).values() if isinstance(cases, dict) else []:
        if isinstance(rec, dict):
            for line in (rec.get("lines") or {}).values():
                retimed(line, form, rec.get("cite") or "")
    return data


def retimed(line, form: str, cite: str = "") -> None:
    """One line's time rewritten from its seconds as `form` says, its timepoint kept (see `retime`)."""
    if not isinstance(line, dict) or line.get("seconds") is None:
        return
    had, cite = str(line.get("time") or ""), line.get("cite") or cite
    head = cite if cite and (had == cite or had.startswith(cite + ", ")) else ""
    try:
        bare = timecode(int(line["seconds"]), form)
        # a statement whose quote takes in the passages next to its own is placed by its range (quotespan)
        span = line.get("span")
        if isinstance(span, list) and len(span) == 2:
            bare = time_span(*(None if t is None else int(t) for t in span), form) or bare
    except (TypeError, ValueError):
        return
    line["time"] = f"{head}, {bare}" if head else bare


# Working together's one writer of the GETs board (wtowners, 8 November 2026): set by team_sync when the routes
# load, a call that refuses the GETs file's write on an install whose member does not work on the GETs board
WRITE_GUARD = None


def write(root: Path, data: dict) -> Path:
    """Written to a temporary file beside it and moved over the old one, as the themes file is, every
    time kept as the file keeps them (see `KEPT_AS`) and the data given left as it was."""
    path = gets_path(root)
    if WRITE_GUARD is not None and FILE_AT.get() is None:
        WRITE_GUARD(Path(root))
    tmp = path.with_name(path.name + ".tmp")
    kept = retime(json.loads(json.dumps(data)), KEPT_AS) if isinstance(data, dict) else data
    tmp.write_text(themes.render(kept) + "\n", encoding="utf-8", newline="\n")
    os.replace(tmp, path)
    note_written(path)
    return path


def changed_outside(entry: dict, rec: dict | None) -> bool:
    with themes.scoped(entry.get("timepoint")):
        return _changed_outside(entry, rec)


def _changed_outside(entry: dict, rec: dict | None) -> bool:
    """Whether a case changed since it came in was changed outside the app (20 October): its workbook or
    its themes file written since then by anything but this process, an AI agent's command line or a hand
    on the file. A change from another window of the app is the app's own, which the GETs take by
    themselves."""
    workbook = Path(entry["workbook"])
    for name, path in case_files(workbook):
        if path.exists() and written_since(rec, name, path) and not written_here(path):
            return True
    return False


def case_files(workbook: Path) -> tuple:
    """A case's two files by the names `seen` keeps them under, its workbook and its themes file, on LGETs
    its LPETs file in the themes file's place."""
    if in_lgets():
        return (("workbook", Path(workbook)), ("themes", lpets_path(Path(workbook))))
    return (("workbook", Path(workbook)), ("themes", themes.themes_path(Path(workbook))))


def seen_of(workbook: Path) -> dict:
    """Each of a case's two files as it stands now, its modification time in nanoseconds, or None for one
    not there, the themes file of a case with no board yet."""
    out = {}
    for name, path in case_files(workbook):
        try:
            out[name] = path.stat().st_mtime_ns
        except OSError:
            out[name] = None
    return out


def written_since(rec: dict | None, name: str, path: Path) -> bool:
    """Whether one of a case's files was written since the case came in. A case kept with `seen` compares
    the file's time with the one its snapshot read, to the nanosecond, so a write in the very second it came
    in shows and a file untouched since never does (20 October: the arrival kept to the whole second had
    read a workbook written in that second as changed, and could miss a change made in it). A case kept
    before `seen` goes by `came` as it always has, a file written in its second or later counting as
    written since. A file not there was not written since, unless `seen` saw it there."""
    rec = rec if isinstance(rec, dict) else {}
    seen = rec.get("seen") if isinstance(rec.get("seen"), dict) else None
    try:
        info = path.stat()
    except OSError:
        info = None
    if seen is not None and name in seen:
        was = seen[name]
        if was is not None and (isinstance(was, bool) or not isinstance(was, int)):
            return True
        return (info.st_mtime_ns if info is not None else None) != was
    if info is None:
        return False
    at = stamp(rec.get("came"))
    return at is None or info.st_mtime >= at


def fresh_file(when: str) -> dict:
    return {"schema": SCHEMA, "created": when, "updated": when, "current": FIRST_BOARD, "complete": None,
            "settings": dict(SETTINGS), "study": {}, "cases": {}, "boards": []}


def boards_of(data: dict | None) -> list[dict]:
    return themes.boards_of(data)


def ta_now() -> bool:
    """Whether the run is in a thematic analysis project, whose board keeps each code one card (codes)."""
    return i18n.method_now() == "ta"


def codes_mod():
    import codes
    return codes


# ---------------------------------------------------------------- the cases

def who(case: str) -> str:
    """The pseudonym alone, for a card's kicker: `P2 - Rowan` is Rowan, and `Juno` stays Juno."""
    text = str(case or "")
    named = NAMES.get()
    if named and text in named:
        return named[text]
    return re.sub(r"^P\d+\s*-\s*", "", text).strip() or text


def case_order(case: str) -> list:
    """Case order, the numbers in a name read as numbers, so P2 comes before P10."""
    return [int(t) if t.isdigit() else t.lower() for t in re.split(r"(\d+)", str(case or ""))]


def card_of(case: str, kind: str, ident) -> str:
    """A card's key: `<case>/g1` for a PET or a sub-theme, `<case>/es/<line>` and `<case>/pn/<n>`."""
    return f"{case}/{ident}" if kind == "group" else f"{case}/{kind}/{ident}"


def split_key(key: str) -> dict:
    """What a card's key names: its case, its kind, `group` for a PET or a sub-theme, `es` or `pn`,
    the group id, line key or note number, and for a second card of a PET the number after it."""
    case, _, rest = str(key).partition("/")
    head, _, tail = rest.partition("/")
    if head in ("es", "pn"):
        return {"case": case, "kind": head, "ident": tail, "copy": None}
    return {"case": case, "kind": "group", "ident": head, "copy": tail or None}


def source_board(data: dict | None) -> tuple[dict | None, bool]:
    """The board a case comes in from, and whether its PETs were marked complete on it: the board
    the mark names while the file holds it, else the Current board, else the board last open."""
    done = themes.complete_of(data)
    if done:
        board = themes.find_version(data, done["board"])
        if board is not None:
            return board, True
    chosen = themes.chosen_of(data)
    if chosen:
        return themes.find_version(data, chosen), False
    return themes.current_version(data), False


def at_timepoint(entry: dict, fn, *args):
    """`fn` run at the timepoint a survey's entry is for, T1 or a project of one with none."""
    with themes.scoped(entry.get("timepoint")):
        return fn(*args)


def fresh_of(entry: dict) -> dict:
    """An entry's snapshot as it reads now, its quotes' times cited with the timepoint on LPETs."""
    snap = at_timepoint(entry, snapshot, entry["workbook"])
    cite = entry.get("cite")
    if cite:
        recite(snap, cite)
    return snap


def uncited(time: str, cite: str) -> str:
    """A quote's time without the timepoint it is cited with, "35:55" of "T1, 35:55"."""
    time = str(time or "")
    if not cite:
        return time
    if time == cite:
        return ""
    return time[len(cite) + 2:] if time.startswith(cite + ", ") else time


def recite(rec: dict, cite: str) -> dict:
    """A timepoint's copy on LPETs cited with `cite`, its label now, every quote's time "T1, 35:55". A
    timepoint is known by its place, so a label renamed in Settings changes only how it is cited."""
    was = rec.get("cite") or ""
    for line in (rec.get("lines") or {}).values():
        if isinstance(line, dict):
            bare = uncited(line.get("time"), was)
            line["time"] = f"{cite}, {bare}" if bare else cite
    rec["cite"] = cite
    return rec


def snapshot(workbook: Path) -> dict:
    """What a case comes in with, read afresh from its workbook and its themes file: the board's
    id and name, whether its PETs were marked complete there, its PETs and sub-themes in the order
    the canvas reads them, and every statement of the case, placed, unplaced or discarded, with its
    sheet, timecode, words, quotes and exploratory notes, one stacked under another with `stacked`,
    its top, and its top's PET. Every sheet is pooled, the sheet named
    on each line. A case with no themes file, or one with no board, has no PETs and every statement
    unplaced. Nothing is written."""
    workbook = Path(workbook)
    if in_lgets():
        return lpets_snapshot(workbook)
    # the two files' times before a word is read, so a write while it reads shows as one since
    seen = seen_of(workbook)
    data = themes.load(workbook)
    board, complete = source_board(data)
    read = themes.read_cards(workbook, explore=True)
    shown = themes.follow(board, read["cards"], read["quotes"]) if board is not None else None
    owners = themes.parents_of(shown["groups"]) if shown else {}
    thrown = set(shown["discarded"]) if shown else set()
    # a statement stacked under another goes where its top goes, its PET or the bin, and names its top
    tops = {k: t for t, keys in ((shown or {}).get("stacks") or {}).items() for k in keys}
    lines = {}
    for c in read["cards"]:
        row = themes.row_key(c["sheet"], c["row"])
        at = tops.get(c["key"], c["key"])
        lines[c["key"]] = {"sheet": c["sheet"], "row": c["row"], "time": c["time"], "seconds": c["seconds"],
                           **({"span": c["span"]} if c.get("span") else {}), "text": c["text"],
                           "quotes": row_places((read["quotes"].get(row) or {}).get("quotes") or []),
                           "notes": list(read["explored"].get(row) or []),
                           "pet": owners.get(at), "discarded": at in thrown}
        if c["key"] in tops:
            lines[c["key"]]["stacked"] = tops[c["key"]]
    pets = []
    if shown:
        drawn = themes.layout_boxes(shown)
        by_id = {g["id"]: g for g in shown["groups"]}

        def walk(gid: str, seen: frozenset) -> None:
            g = by_id[gid]
            members = themes.theme_order(shown, gid, drawn)
            pets.append(dict({"id": gid, "title": g["label"], "note": str(g.get("note") or ""),
                              "parent": owners.get(gid), "subs": [m for m in members if m in by_id],
                              "statements": [m for m in members if m not in by_id and m in lines],
                              "picks": list(shown["picks"].get(gid) or [])}, **described(g)))
            for m in members:
                if m in by_id and m not in seen:
                    walk(m, seen | {m})

        for gid in themes.canvas_order([g["id"] for g in shown["groups"] if g["id"] not in owners], by_id):
            walk(gid, frozenset({gid}))
    return {"board": shown["id"] if shown else None, "name": shown["name"] if shown else None,
            "complete": bool(complete and shown), "pets": pets, "lines": lines, "seen": seen}


SNAP_KEYS = ("board", "name", "complete", "pets", "lines")


def snap_hash(snap: dict) -> str:
    """The snapshot's hash, as the history hashes a revision."""
    held = {k: snap.get(k) for k in SNAP_KEYS}
    cite = snap.get("cite")
    if cite or any(isinstance(v, dict) and v.get("cite") for v in (held.get("lines") or {}).values()):
        # on LPETs and LGETs the hash leaves out the label a time is cited with, so a renamed timepoint is
        # unchanged: the copy's own on LPETs, each line's on LGETs
        def bare(v: dict) -> dict:
            out = dict(v, time=uncited(v.get("time"), v.get("cite") or cite))
            out.pop("cite", None)
            return out
        held["lines"] = {k: bare(v) if isinstance(v, dict) else v for k, v in (held.get("lines") or {}).items()}
    # and every time as the file keeps it, so the project's timecodes never change a case (see `KEPT_AS`)
    held["lines"] = {k: kept_time(v) for k, v in (held.get("lines") or {}).items()}
    return themes.state_hash(held)


def kept_time(v):
    """A line with its time as the file keeps it, a copy (see `snap_hash`)."""
    if not isinstance(v, dict):
        return v
    out = dict(v)
    retimed(out, KEPT_AS)
    return out


def record(snap: dict, workbook: Path, when: str) -> dict:
    """A case as the file holds it once it is in."""
    return {"workbook": Path(workbook).name, "board": snap["board"], "name": snap["name"],
            "complete": snap["complete"], "came": when, "seen": dict(snap.get("seen") or seen_of(workbook)),
            "hash": snap_hash(snap), "state": "in" if snap["board"] else "none", "pets": snap["pets"],
            "lines": snap["lines"], **({"cite": snap["cite"]} if snap.get("cite") else {})}


def stamp(iso: str) -> float | None:
    try:
        return datetime.fromisoformat(str(iso)).timestamp()
    except (TypeError, ValueError):
        return None


def untouched(workbook: Path, rec: dict | None) -> bool:
    """True when neither the workbook nor its themes file was written since the case came in, so it
    is unchanged without a read. A workbook not there is read, and refused there."""
    if not Path(workbook).exists():
        return False
    return not any(written_since(rec, name, path) for name, path in case_files(workbook))


def changes(old: dict, new: dict) -> dict:
    """What changed in a case since it came in: PETs added, gone and retitled, statements moved
    from one PET to another, placed, not placed or discarded, and its PETs marked complete since."""
    olds = {p["id"]: p for p in old.get("pets") or []}
    news = {p["id"]: p for p in new.get("pets") or []}
    pairs = matched(old.get("pets") or [], new.get("pets") or [])
    taken = set(pairs.values())
    added = [p["title"] for p in new.get("pets") or [] if p["id"] not in taken]
    gone = [p["title"] for p in old.get("pets") or [] if p["id"] not in pairs]
    retitled = [[olds[a]["title"], news[b]["title"]] for a, b in pairs.items() if olds[a]["title"] != news[b]["title"]]
    titles = {**{p["id"]: p["title"] for p in old.get("pets") or []}, **{p["id"]: p["title"] for p in new.get("pets") or []}}

    def where(line: dict | None) -> str:
        if not line:
            return ""
        if line.get("discarded"):
            return themes.DISCARDED
        return titles.get(line.get("pet"), "") if line.get("pet") else themes.NOT_PLACED

    moved = []
    for key, line in (new.get("lines") or {}).items():
        was = (old.get("lines") or {}).get(key)
        if was is None or (was.get("pet"), bool(was.get("discarded"))) == (line.get("pet"), bool(line.get("discarded"))):
            continue
        moved.append({"text": line["text"], "from": where(was), "to": where(line)})
    marked = bool(new.get("complete")) and not old.get("complete")
    return {"added": added, "gone": gone, "retitled": retitled, "moved": moved, "marked": marked,
            "board": new.get("name") if new.get("board") != old.get("board") else None}


def matched(old: list[dict], new: list[dict]) -> dict[str, str]:
    """Each old PET's id to the new one that takes its place: the same id, then the same title,
    and an old one matched by neither is gone."""
    news = {p["id"]: p for p in new}
    out, claimed = {}, set()
    for p in old:
        if p["id"] in news:
            out[p["id"]] = p["id"]
            claimed.add(p["id"])
    for p in old:
        if p["id"] in out:
            continue
        same = next((q["id"] for q in new if q["id"] not in claimed
                     and themes.words(q["title"]).lower() == themes.words(p["title"]).lower()), None)
        if same:
            out[p["id"]] = same
            claimed.add(same)
    return out


def survey(books: list[dict], data: dict, light: bool = False) -> list[dict]:
    """Each case of the study as it stands now, in case order: the copy the file holds, the
    snapshot it would come in with when it is not in yet or has changed, and its status, `pending`
    not yet in, `in`, `changed` or `unread` when its themes file cannot be read. `light`, for the
    autosave, reads only the cases not yet in, since a save answers with no case."""
    held = data.get("cases") if isinstance(data.get("cases"), dict) else {}
    out = []
    for book in sorted(books, key=lambda b: case_order(b["case"])):
        case, workbook = book["case"], Path(book["workbook"])
        rec = held.get(case) if isinstance(held.get(case), dict) else None
        entry = {"case": case, "workbook": workbook, "held": rec, "fresh": None, "status": "in", "said": ""}
        # on LPETs a timepoint is read at its own PETs file and sheets, and one not interviewed says so
        if book.get("timepoint"):
            entry.update(timepoint=book["timepoint"], cite=book.get("cite") or "", missing=bool(book.get("missing")))
            if entry["missing"]:
                entry["said"] = i18n.t("exports.not_interviewed")
        if rec is not None and (light or at_timepoint(entry, untouched, workbook, rec)):
            out.append(entry)
            continue
        try:
            entry["fresh"] = fresh_of(entry)
        except (WorkbookError, OSError) as exc:
            entry.update(status="unread", said=str(exc))
            out.append(entry)
            continue
        if rec is None:
            entry["status"] = "pending"
        elif snap_hash(entry["fresh"]) != rec.get("hash"):
            entry["status"] = "changed"
        out.append(entry)
    return out


# --------------------------------------------------------------- the study

def settings_of(data: dict | None) -> dict:
    """The study's own settings: `minimum`, null for Smith's band, and `one_per_pet`. The limit New AI
    board kept here before 11 November 2026, `cap`, is read as nothing."""
    held = (data or {}).get("settings") if isinstance((data or {}).get("settings"), dict) else {}
    minimum = held.get("minimum")
    try:
        minimum = max(1, int(minimum)) if minimum is not None else None
    except (TypeError, ValueError):
        minimum = None
    return {"minimum": minimum, "one_per_pet": held.get("one_per_pet") is not False}


def study_of(data: dict | None, cases) -> dict:
    """Each case's place in the study: in unless Settings took it out, with the reason he gave."""
    held = (data or {}).get("study") if isinstance((data or {}).get("study"), dict) else {}
    out = {}
    for case in cases:
        mark = held.get(case) if isinstance(held.get(case), dict) else {}
        out[case] = {"in": mark.get("in") is not False, "reason": str(mark.get("reason") or "").strip()}
    return out


def band(n: int) -> int:
    """Smith's (2011a) band for a study of `n`: every participant for three or fewer, three for
    four to eight, and half, rounded up, beyond eight."""
    n = max(0, int(n))
    if n <= 3:
        return n
    if n <= 8:
        return 3
    return math.ceil(n / 2)


def minimum_of(settings: dict, n: int) -> tuple[int, bool]:
    """The minimum a GET needs and whether it is Smith's band, his to change."""
    if settings.get("minimum") is None:
        return band(n), True
    return int(settings["minimum"]), False


def count(board: dict, gid: str, inside: set[str]) -> int:
    """The cases with a PET, a sub-theme or a statement of theirs anywhere under a group, of the
    cases in the study. A participant note never counts."""
    by_id = {g["id"]: g for g in board.get("groups") or []}
    thrown = set(board.get("discarded") or [])
    found = set()
    for key in themes.cards_under(by_id, gid):
        if key in thrown or key not in (board.get("cards") or {}):
            continue
        k = split_key(key)
        if k["kind"] != "pn" and k["case"] in inside:
            found.add(k["case"])
    return len(found)


# ---------------------------------------------------------------- a board

def described(item: dict) -> dict:
    """A PET's or a GET's description as a copy or a card carries it, `{"description": ...}`, or nothing
    for none, so a copy of a case with no descriptions reads and writes as it did (21 October)."""
    said = themes.description_of(item)
    return {themes.DESCRIPTION: said} if said else {}


# a PET's description on its card, after its title in the words the layout is estimated from (21 October): the
# page's .gt-desc, 13px in the serif, 1.3 apart, two lines at most, 2px under the title
DESC_MARK = "\x1f"
DESC_PX, DESC_LINE, DESC_TOP = 13.0, 13.0 * 1.3, 2


def layout_text(title, description="") -> str:
    """A card's words for the estimate of its height: a PET's title, and its description after DESC_MARK."""
    said = themes.description_of({themes.DESCRIPTION: description})
    return f"{title or ''}{DESC_MARK}{said}" if said else str(title or "")


def card_height(_key, text) -> int:
    """A GETs card's height as the page draws it, a little over: its kicker over a PETs card, and a PET's
    description under its title, two lines at most, when its words carry one (see `layout_text`)."""
    words, _, said = str(text or "").partition(DESC_MARK)
    height = themes.card_height(words) + KICKER_H
    if said.strip():
        lines, _ = themes.wrap([themes.text_width(w, DESC_PX) for w in said.split()], themes.text_width(" ", DESC_PX),
                               themes.CARD_TEXT_W)
        height += DESC_TOP + math.ceil(min(2, lines) * DESC_LINE)
    return height


def pile(entries: list[tuple[str, str]]) -> dict[str, dict]:
    """A round pile in the middle of the canvas, in an order seeded from the keys."""
    texts = dict(entries)
    order = themes.seeded(texts)
    spots = themes.pack_round([(themes.CARD_W, card_height(k, texts[k])) for k in order], themes.MARGIN)
    return {k: {"x": x, "y": y} for k, (x, y) in zip(order, spots)}


def depths(rec: dict) -> dict[str, int]:
    """How deep each PET of a case's copy sits, by its id: 0 for a PET, 1 for a sub-theme, and 2
    or more for a group, which rides inside its sub-theme's card and has none of its own."""
    pets = {p["id"]: p for p in rec.get("pets") or []}
    out = {}
    for pid in pets:
        depth, seen, at = 0, {pid}, pets[pid].get("parent")
        while at is not None and at in pets and at not in seen:
            seen.add(at)
            depth += 1
            at = pets[at].get("parent")
        out[pid] = depth
    return out


def tops(case: str, rec: dict) -> list[tuple[str, str]]:
    """A case's top-level PETs as cards, by key and title."""
    return [(card_of(case, "group", p["id"]), p["title"]) for p in rec.get("pets") or [] if p.get("parent") is None]


def cards_of(case: str, rec: dict, only=None) -> list[tuple[str, str]]:
    """A case's cards as a board gets them by itself, by key and title: one for every PET and one
    for every sub-theme, each a card of its own (item 193), a sub-theme's groups at any depth riding
    inside its card. `only`, a set of ids, keeps those alone."""
    deep = depths(rec)
    return [(card_of(case, "group", p["id"]), p["title"]) for p in rec.get("pets") or []
            if deep.get(p["id"], 0) <= 1 and (only is None or p["id"] in only)]


def subs_of(case: str, rec: dict) -> list[tuple[str, str]]:
    """A case's sub-themes as cards, by key and title, their groups riding inside them."""
    deep = depths(rec)
    return [(card_of(case, "group", p["id"]), p["title"]) for p in rec.get("pets") or [] if deep.get(p["id"], 0) == 1]


def blank_board(data: dict, bid: str, name: str, when: str) -> dict:
    """A board with every card back in the pile: each PET and each sub-theme of each case in the
    study, a card of its own in no group."""
    study = study_of(data, (data.get("cases") or {}).keys())
    entries = [e for case, rec in sorted((data.get("cases") or {}).items(), key=lambda x: case_order(x[0]))
               if study[case]["in"] for e in cards_of(case, rec)]
    spots = pile(entries)
    return {"id": bid, "name": name, "note": "", "created": when, "updated": when,
            "cards": {k: dict(spots[k]) for k, _ in entries}, "groups": [], "discarded": [], "picks": {}, "rows": {}}


# Arrange by participant (Adam, 19 October, way 2 of the drawings), the page's GT_BY_ numbers: between one
# card of a row and the next, that much more before each PET after the first, between one participant's row
# and the next, and between what stays and the first row
BY_GAP, BY_PET, BY_ROW, BY_BELOW = 14, 14, 40, 60


def by_participant(board: dict, data: dict, order: list[str], height=None) -> list[str]:
    """Arrange by participant, as the GETs screen's board menu and its right click on empty canvas do
    it: every PET and sub-theme card in no GET and not in the bin goes in a row for its participant,
    the rows in `order`, the Cases panel's, each PET in the case's PET order with its sub-themes beside
    it after it, each PET after the first a little further off, a second card of a PET after its first,
    and a sub-theme whose PET is in a GET or in the bin at the row's end. The rows go below everything that stays, at its left edge: every GET with all it holds, a
    statement's card, a participant note and a sticky note, none of which moves. The board is changed
    in place, and the answer is the cards moved in the order they now read, none when every PET and
    sub-theme is in a GET or in the bin. `height` is as `themes.layout_boxes` takes it."""
    tall = height or card_height
    parents = themes.parents_of(board.get("groups") or [])
    gone = themes.off_canvas(board)
    cards = board.get("cards") or {}
    moving = [k for k in cards if k not in gone and k not in parents and kind_of(k, data) in ("pet", "sub")]
    if not moving:
        return []
    going = set(moving)
    drawn = themes.layout_boxes(board, tall)
    stays = [drawn["frames"][g["id"]] for g in board.get("groups") or [] if g["id"] not in parents and g["id"] in drawn["frames"]]
    stays += [box for k, box in drawn["cards"].items() if k not in going and k not in parents]
    stays += [box for n in board.get("notes") or [] if isinstance(n, dict) and not n.get("in")
              for box in [drawn["notes"].get(n.get("id"))] if box]
    if stays:
        x0 = min(b[0] for b in stays)
        y = max(b[1] + b[3] for b in stays) + BY_BELOW
    else:
        x0 = min(cards[k].get("x", 0) for k in moving)
        y = min(cards[k].get("y", 0) for k in moving)
    by_case: dict[str, list[str]] = {}
    for k in moving:
        by_case.setdefault(split_key(k)["case"], []).append(k)
    names = [n for n in order if n in by_case] + sorted((n for n in by_case if n not in order), key=case_order)
    out = []
    for name in names:
        pets = ((data.get("cases") or {}).get(name) or {}).get("pets") or []
        at = {p["id"]: i for i, p in enumerate(pets)}
        by_id = {p["id"]: p for p in pets}

        def top_of(pid):
            seen = set()
            while pid in by_id and by_id[pid].get("parent") is not None and pid not in seen:
                seen.add(pid)
                pid = by_id[pid]["parent"]
            return pid

        place = lambda pid: at.get(pid, len(pets))  # noqa: E731
        groups: dict[str, list[str]] = {}
        for k in by_case[name]:
            groups.setdefault(top_of(split_key(k)["ident"]), []).append(k)
        # each PET with its own sub-themes in the case's PET order, and after them the sub-themes whose PET is
        # in a GET or in the bin, so a row never starts with a sub-theme or puts one after a PET not its own
        headed = {t for t, keys in groups.items() if any(split_key(k)["ident"] == t for k in keys)}
        x, row = x0, 0
        for i, top in enumerate(sorted(groups, key=lambda t: (t not in headed, place(t), str(t)))):
            if i:
                x += BY_PET

            def rank(k, top=top):
                s = split_key(k)
                return (0 if s["ident"] == top else 1, place(s["ident"]), int(s["copy"]) if str(s["copy"] or "").isdigit() else (1 if s["copy"] else 0), k)

            for k in sorted(groups[top], key=rank):
                h = tall(k, cards[k].get("text"))
                cards[k]["x"], cards[k]["y"] = round(x), round(y)
                x += themes.CARD_W + BY_GAP
                row = max(row, h)
                out.append(k)
        y += row + BY_ROW
    return out


def has_card(board: dict, key: str) -> bool:
    """A card of this PET or sub-theme is on the board, the first or a second one."""
    return any(k == key or k.startswith(key + "/") for k in board.get("cards") or {})


def lay_in(board: dict, entries: list[tuple[str, str]], data: dict) -> None:
    """Cards new to a board in the nearest free spot to the middle, clear of everything there. A
    PET's card on the board keeps no words, so its title comes from its case's copy in `data`, and
    the card is taken as tall as the page draws it (item 196)."""
    entries = [(k, t) for k, t in entries if not has_card(board, k)]
    if not entries:
        return
    texts = dict(entries)
    shown = dict(named(board, data), picks=board.get("picks") or {})
    spots = themes.place_new([k for k, _ in entries], texts, shown, card_height)
    for k, _ in entries:
        board.setdefault("cards", {})[k] = dict(spots[k])


def statement_line(data: dict, key: str) -> dict | None:
    """The statement a card's key names in its case's copy, `<case>/es/<line>`, as the Participants panel lists
    it: on LPETs a timepoint's, on GETs and LGETs a participant's. None for a key of another kind or a statement
    the copy does not hold."""
    k = split_key(key)
    if k["kind"] != "es":
        return None
    rec = (data.get("cases") or {}).get(k["case"])
    line = (rec.get("lines") or {}).get(k["ident"]) if isinstance(rec, dict) and isinstance(rec.get("lines"), dict) else None
    return line if isinstance(line, dict) else None


def bring_in(board: dict, data: dict, keys: list[str]) -> list[str]:
    """Statements brought onto a board from the Participants panel, each alone, never its PET's other statements,
    the card a row dragged onto the canvas makes (lpetadd, 11 November 2026, `gtCardFrom` and `gtPullDrop` on the
    page): its words from its case's copy, which `normal` keeps on a statement's card as it keeps the page's, in no
    label, in the nearest free spot to the middle, as a case's cards come in (`lay_in`). A key on the board already
    or naming no statement of a copy is passed over. The board is changed in place, and the answer is the keys
    brought in."""
    entries = []
    for key in keys:
        line = statement_line(data, key)
        if line is not None and key not in (board.get("cards") or {}) and key not in dict(entries):
            entries.append((key, str(line.get("text") or "")))
    lay_in(board, entries, data)
    for key, text in entries:
        board["cards"][key]["text"] = text
    return [k for k, _ in entries]


def take_in(data: dict, cases: list[dict], when: str) -> list[str]:
    """Every case not yet in comes in: its snapshot into the file, its place in the study, and a
    card for each of its PETs and sub-themes into the pile of every board. The cases taken, by
    name."""
    held = data.setdefault("cases", {})
    study = data.setdefault("study", {})
    taken = []
    for entry in cases:
        if entry["status"] != "pending" or entry["fresh"] is None:
            continue
        case = entry["case"]
        held[case] = record(entry["fresh"], entry["workbook"], when)
        study.setdefault(case, {"in": True})
        for board in boards_of(data):
            lay_in(board, cards_of(case, held[case]), data)
        taken.append(case)
    # in a thematic analysis project a new participant's extracts of a code on a board come in where it stands
    if taken and ta_now():
        for board in boards_of(data):
            codes_mod().gather(board, data)
    return taken


def normal(board: dict, data: dict) -> dict:
    """A GETs board as the file holds it, whatever the page sent: the PETs screen's rules, a card
    in one group at most among them, then a PET's or a sub-theme's card keeps no words while its
    case still has it, a statement and a participant note keep theirs, and `rows` holds the GET
    table's rows (see `rows_of`)."""
    kept = themes.normalise(board)
    held = data.get("cases") or {}
    for key, card in kept["cards"].items():
        k = split_key(key)
        if k["kind"] == "group":
            ids = {p["id"] for p in (held.get(k["case"]) or {}).get("pets") or []}
            if k["ident"] in ids or not card.get("text"):
                card.pop("text", None)
        card.pop("live", None)
    kept["rows"] = rows_of(dict(board, groups=kept["groups"]))
    return kept


def rows_of(board: dict) -> dict:
    """The GET table's rows as the file keeps them, by GET and then by case: the quote he
    ticked, by its key, `<sheet>:<row>:<place>`, and his note for the row. A row with neither is
    left out, and so is a GET no longer on the board, so a new GET that takes a gone one's id
    starts with none."""
    held = board.get("rows") if isinstance(board.get("rows"), dict) else {}
    ids = {str(g.get("id")) for g in board.get("groups") or [] if isinstance(g, dict)}
    out: dict = {}
    for gid, cases in held.items():
        if str(gid) not in ids or not isinstance(cases, dict):
            continue
        for case, row in cases.items():
            if not isinstance(row, dict):
                continue
            quote = " ".join(str(row.get("quote") or "").split())
            note = str(row.get("note") or "").replace("\r\n", "\n").replace("\r", "\n").strip()
            # a key quote taken from the transcript on Trajectories (trajchoose, 11 November 2026), in place of a tick
            passage = None if quote else passage_kept(row.get("passage"))
            if quote or note or passage:
                kept = {"quote": quote, "note": note[:4000]}
                if passage:
                    kept["passage"] = passage
                # his bold in the key quote (trajbuild2, 10 November 2026), kept with the quote it marks
                bold = spans_kept(row.get("bold")) if quote or passage else []
                if bold:
                    kept["bold"] = bold
                out.setdefault(str(gid), {})[str(case)] = kept
    return out


# the longest passage of the transcript a row keeps as its key quote
PASSAGE_MAX = 20000


def passage_kept(given) -> dict | None:
    """A key quote taken from the transcript as a row keeps it (trajchoose, 11 November 2026): the interview by its
    timepoint's key, `at`, `T3`, the turn, `turn`, `<sheet>:<row>`, the place of its words in the turn's words by
    character, `start` and `end`, and the words, `text`, so a turn whose words change since is noticed. None for
    anything else."""
    if not isinstance(given, dict):
        return None
    at, turn, text = str(given.get("at") or ""), str(given.get("turn") or ""), str(given.get("text") or "")
    start, end = given.get("start"), given.get("end")
    sheet, _, row = turn.rpartition(":")
    whole = all(isinstance(x, int) and not isinstance(x, bool) for x in (start, end))
    if (not re.fullmatch(r"T\d+", at) or not sheet or not row.isdigit() or not whole or not 0 <= start < end
            or end - start != len(text) or not text.strip() or len(text) > PASSAGE_MAX):
        return None
    return {"at": at, "turn": turn, "start": start, "end": end, "text": text}


def spans_kept(given) -> list[list[int]]:
    """Bold in a key quote as the row keeps it: spans of the quote's words, `[start, end]` by character, in
    order, each once, those that touch or overlap made one. The transcript is never marked."""
    spans = []
    for s in given if isinstance(given, list) else []:
        if (isinstance(s, (list, tuple)) and len(s) == 2 and all(isinstance(x, int) and not isinstance(x, bool) for x in s)
                and 0 <= s[0] < s[1] <= 20000):
            spans.append([s[0], s[1]])
    out: list[list[int]] = []
    for s in sorted(spans):
        if out and s[0] <= out[-1][1]:
            out[-1][1] = max(out[-1][1], s[1])
        else:
            out.append(s)
    return out[:200]


def assemble(root: Path, books: list[dict], when: str, light: bool = False) -> tuple[dict, list[dict], dict | None, list[str]]:
    """The file as the first act would leave it, in memory: every case not yet in taken in, and a
    first board when there is none. The file on disk, or None, each case's survey and the cases
    taken in."""
    disk = load(root)
    data = json.loads(json.dumps(disk)) if disk else fresh_file(when)
    for key, value in fresh_file(when).items():
        data.setdefault(key, value)
    cases = survey(books, data, light)
    taken = take_in(data, cases, when)
    if not boards_of(data):
        data["boards"] = [blank_board(data, FIRST_BOARD, FIRST_NAME, when)]
        data["current"] = FIRST_BOARD
    return data, cases, disk, taken


# --------------------------------------------------------------- the state

def kind_of(key: str, data: dict) -> str:
    k = split_key(key)
    if k["kind"] != "group":
        return k["kind"]
    pets = {p["id"]: p for p in ((data.get("cases") or {}).get(k["case"]) or {}).get("pets") or []}
    p = pets.get(k["ident"])
    return "sub" if p is not None and p.get("parent") is not None else "pet"


def cards_shown(board: dict, data: dict) -> list[dict]:
    """The board's cards as the page draws them, each named from its case's copy: its kind and
    case, the words, a PET's statements counted at any depth, a statement's timecode and sheet, and
    the marks, `open` for a case whose PETs are not complete and `gone` for a card no longer in its
    case's copy."""
    held = data.get("cases") or {}
    out = []
    for key, c in (board.get("cards") or {}).items():
        k = split_key(key)
        rec = held.get(k["case"]) or {}
        pets = {p["id"]: p for p in rec.get("pets") or []}
        lines = rec.get("lines") or {}
        # a participant note is his own words, not the case's PETs, so it never carries their mark
        item = {"key": key, "case": k["case"], "who": who(k["case"]), "x": c.get("x", 0), "y": c.get("y", 0),
                "text": c.get("text") or "", "time": "", "sheet": "", "seconds": None,
                "open": bool(rec) and not rec.get("complete") and rec.get("state") == "in" and k["kind"] != "pn",
                "gone": False}
        if k["kind"] == "group":
            p = pets.get(k["ident"])
            if p is None:
                item.update(kind="pet", gone=True, text=item["text"] or themes.UNTITLED)
            else:
                item.update(kind="pet" if p.get("parent") is None else "sub", text=p["title"], pet=p["id"],
                            statements=len(under(p["id"], pets)), **described(p))
            if k["copy"]:
                item["copy"] = k["copy"]
        elif k["kind"] == "es":
            line = lines.get(k["ident"])
            item["kind"] = "es"
            if line is None:
                item["gone"] = True
            else:
                item.update(text=line["text"], time=line.get("time") or "", sheet=line.get("sheet") or "",
                            seconds=line.get("seconds"), pet=line.get("pet"))
        else:
            item["kind"] = "pn"
        out.append(item)
    return out


def under(gid: str, pets: dict) -> list[str]:
    """Every statement under a PET of a case's copy, at any depth."""
    out, stack, seen = [], [gid], set()
    while stack:
        at = stack.pop()
        if at in seen or at not in pets:
            continue
        seen.add(at)
        out.extend(pets[at].get("statements") or [])
        stack.extend(pets[at].get("subs") or [])
    return out


# ------------------------------------------------------- the cases' colours

def colours_of(data: dict | None) -> dict[str, int]:
    """His colours by case, from the file's `colours`, each a place in the cases' palette from 0 to 24,
    anything else left out."""
    held = (data or {}).get("colours")
    out: dict[str, int] = {}
    if isinstance(held, dict):
        for case, n in held.items():
            if isinstance(n, int) and not isinstance(n, bool) and 0 <= n < COLOURS:
                out[str(case)] = n
    return out


def badges(pairs: list[tuple[str, str]]) -> dict[str, str]:
    """A badge for each case, by its pseudonym: the initial, two letters where two cases share one, the
    initial and the next letter, and where those are shared too the initial and the case's place among
    them, "J1", "J2"."""
    first = lambda name: next((ch for ch in str(name) if ch.isalnum()), "?").upper()
    groups: dict[str, list[tuple[str, str]]] = {}
    for case, name in pairs:
        groups.setdefault(first(name), []).append((case, name))
    out: dict[str, str] = {}
    for initial, members in groups.items():
        if len(members) == 1:
            out[members[0][0]] = initial
            continue
        def two(name: str) -> str:
            letters = [ch for ch in str(name) if ch.isalnum()]
            return initial + (letters[1].lower() if len(letters) > 1 else "")
        pair = [two(name) for _, name in members]
        for k, (case, _name) in enumerate(members):
            same = [i for i, p in enumerate(pair) if p == pair[k]]
            out[case] = pair[k] if len(same) == 1 else f"{initial}{same.index(k) + 1}"
    return out


def looks(cases, data: dict | None) -> dict[str, dict]:
    """Each case's look on the GETs board (16 October): `colour`, his choice or else `default`, the
    case's place in case order round the palette, `chosen` whether it is his, and `badge`."""
    order = sorted(dict.fromkeys(str(c) for c in cases), key=case_order)
    chosen = {c: n for c, n in colours_of(data).items() if c in order}
    marks = badges([(c, who(c)) for c in order])
    given = defaults_of(order, chosen)
    out = {}
    for c in order:
        own = given[c] if c not in chosen else defaults_of(order, {k: n for k, n in chosen.items() if k != c})[c]
        out[c] = {"colour": chosen.get(c, given[c]), "default": own, "chosen": c in chosen, "badge": marks[c]}
    return out


def defaults_of(order: list[str], chosen: dict[str, int]) -> dict[str, int]:
    """Each case's colour where he has chosen none (21 October): in case order, its own place in the
    palette while no one has it, else the next colour free in the picker's order after it, round to the
    first, skipping the colours his choices took and those the cases before it were given, so a new
    participant gets the next free colour of the 25. Past 25 cases they go round again. A choice of his
    is its case's own and given to none other."""
    taken = set(chosen.values())
    out = {}
    for i, c in enumerate(order):
        if c in chosen:
            out[c] = chosen[c]
            continue
        start = i % COLOURS
        free = [n for n in list(range(start, COLOURS)) + list(range(0, start)) if n not in taken]
        out[c] = free[0] if free else start
        taken.add(out[c])
    return out


def colour_op(root: Path, books: list[dict], case: str, colour) -> dict:
    """A case's colour set from its row in the Cases panel and kept in the file at once, a place in the
    palette, or null for Default, which takes his choice away. An act, so every case not yet in comes
    in first, as Settings' save does. A case the project does not have, or a colour the palette does
    not hold, is refused with nothing written."""
    when = themes.now_iso()
    data, cases, _disk, _taken = assemble(root, books, when)
    if case not in {e["case"] for e in cases}:
        raise WorkbookError(i18n.t("server.participant_project_their_colour_changed"))
    held = colours_of(data)
    if colour is None:
        held.pop(case, None)
    elif isinstance(colour, int) and not isinstance(colour, bool) and 0 <= colour < COLOURS:
        # a colour another participant has, his choice or theirs by default, is not his to take (21 October)
        now = looks([e["case"] for e in cases], data)
        if any(other != case and look["colour"] == colour for other, look in now.items()):
            raise WorkbookError(i18n.t("server.colour_another_participant_s_nothing"))
        held[case] = colour
    else:
        raise WorkbookError(i18n.t("server.one_participants_colours_nothing_changed"))
    data["colours"] = held
    write(root, _file(data, when))
    return dict(answer(data, cases, data, board=data.get("current")), op="colour", case=case)


def panel(entry: dict, data: dict, study: dict, look: dict | None = None) -> dict:
    """One case of the Cases panel: the copy the file holds, or the one it would come in with, its
    PETs and statements, its place in the study, what changed since it came in, and its colour and
    badge."""
    case = entry["case"]
    rec = (data.get("cases") or {}).get(case)
    shown = rec or entry["fresh"] or {}
    look = look or {"colour": 0, "default": 0, "chosen": False, "badge": who(case)[:1].upper()}
    # `workbook` and `board` are where Open beside finds the case's board, the one its copy came from
    out = {"case": case, "who": who(case), "status": entry["status"], "said": entry["said"],
           "colour": look["colour"], "default": look["default"], "chosen": look["chosen"], "badge": look["badge"],
           "in": study.get(case, {"in": True})["in"], "reason": study.get(case, {"reason": ""})["reason"],
           "none": not shown.get("board"), "complete": bool(shown.get("complete")),
           "board_name": shown.get("name") or "", "pets": shown.get("pets") or [], "lines": shown.get("lines") or {},
           "changes": None, "workbook": str(entry["workbook"]), "board": shown.get("board") or ""}
    if entry.get("timepoint"):
        out.update(timepoint=entry["timepoint"], missing=bool(entry.get("missing")))
    if entry["status"] == "changed" and entry["fresh"] is not None and rec is not None:
        out["changes"] = changes(rec, entry["fresh"])
    return out


def state(root: Path, books: list[dict], board: str | None = None) -> dict:
    """Everything the GETs screen draws, read afresh, and nothing written: each case not yet in
    shown as it would come in, its PETs and sub-themes in the pile. `board` shows that board in
    place of the one last open."""
    when = themes.now_iso()
    data, cases, disk, _taken = assemble(root, books, when)
    return answer(data, cases, disk, board)


def on_disk(disk: dict | None, board: dict | None) -> dict:
    """The board as the file on disk holds it, its version's source (see `themes.board_version`), or
    an empty one when the file does not hold it yet, which has no version. A case taken in on the way
    lays cards into the boards in memory, so the board in memory is never the version's source."""
    found = themes.find_version(disk, str((board or {}).get("id") or "")) if disk else None
    return found if isinstance(found, dict) else {}


def answer(data: dict, cases: list[dict], disk: dict | None, board: str | None = None) -> dict:
    boards = boards_of(data)
    shown = (themes.find_version(data, board) if board else None) or themes.current_version(data)
    kept = normal(shown, data)
    # in a thematic analysis project each code is one card, its lead, with its counts (codes)
    folded = None
    if ta_now():
        kept, folded = codes_mod().fold(kept, data)
    study = study_of(data, [e["case"] for e in cases] + list((data.get("cases") or {}).keys()))
    inside = {c for c, s in study.items() if s["in"] and c in {e["case"] for e in cases}}
    settings = settings_of(data)
    minimum, is_band = minimum_of(settings, len(inside))
    look = looks([e["case"] for e in cases], data)
    return {"gets": True, "schema": SCHEMA, "current": kept["id"], "chosen": themes.chosen_of(data),
            "complete": themes.complete_of(data), "versions": [themes.summary(b, on_disk(disk, b)) for b in boards],
            "version": themes.summary(kept, on_disk(disk, shown)), "saved": disk is not None,
            "cards": cards_shown(kept, data), "groups": kept["groups"], "discarded": kept["discarded"],
            "picks": {}, "discard_reasons": (kept.get("ai") or {}).get("discarded") or {},
            "stickies": kept.get("notes") or [], "rows": kept["rows"], "history": themes.history_list(shown),
            "sheets": [], "quotes": {},
            "cases": [panel(e, data, study, look.get(e["case"])) for e in cases], "study": study,
            "colours": colours_of(data),
            "settings": settings, "minimum": minimum, "band": is_band, "total": len(inside),
            "smith": band(len(inside)), **({"codes": folded} if folded is not None else {})}


# ------------------------------------------------------------- the acts

def _file(data: dict, when: str) -> dict:
    """The file in the order it is written, the top first and the boards last."""
    out = {"schema": SCHEMA, "created": str(data.get("created") or when), "updated": when,
           "current": data.get("current") or FIRST_BOARD}
    chosen = themes.chosen_of(data)
    if chosen:
        out["chosen"] = chosen
    out["complete"] = data.get("complete") if themes.complete_of(data) else None
    out["settings"] = settings_of(data)
    out["study"] = data.get("study") or {}
    if colours_of(data):
        out["colours"] = colours_of(data)
    else:
        data.pop("colours", None)
    out["cases"] = data.get("cases") or {}
    out["boards"] = boards_of(data)
    for key, value in data.items():
        out.setdefault(key, value)
    return out


def save(root: Path, books: list[dict], version: dict, revision=None) -> dict:
    """The board on the canvas written into the file, every case not yet in taken in on the way,
    the first act on the screen being what writes the file. A board the file does not hold is
    refused, and with no file yet only the first is taken. `revision` of `auto` keeps the board as
    the file held it in its history first, at the time of this save, as the PETs screen's save does
    (see `themes.save`). A page whose `v`
    is not the board's now is refused with `themes.StaleBoard` and nothing written."""
    if not isinstance(version, dict):
        raise WorkbookError(i18n.t("server.board_canvas_nothing_written"))
    when = themes.now_iso()
    data, cases, disk, taken = assemble(root, books, when, light=True)
    boards = boards_of(data)
    bid = str(version.get("id") or FIRST_BOARD)
    at = next((i for i, b in enumerate(boards) if str(b.get("id")) == bid), None)
    if at is None:
        raise WorkbookError(i18n.t("server.board_longer_gets_file_nothing"))
    was = boards[at]
    # the version the page last read, the board's `v`: a save over a board the file holds in
    # another version now, from an agent's gets apply or take or from another window, is refused with
    # nothing written (19 October). With no file yet there is nothing to save over.
    if on_disk(disk, was):
        themes.refuse_stale(on_disk(disk, was), version.get("v"), themes.STALE_PAGE)
    kept = normal(version, data)
    # in a thematic analysis project the page sends each code's lead alone, its rows laid back beside it (codes)
    if ta_now():
        kept = codes_mod().unfold(kept, data, was)
    # a GET sent with no key for a field keeps the file's, its description or an LPET's domain (see `themes.fields_kept`)
    kept = themes.fields_kept(kept, version.get("groups"), was.get("groups"))
    # a case that came in with this save, after the page last drew the board, lands in its pile too
    for case in taken:
        lay_in(kept, cards_of(case, data["cases"][case]), data)
    kept.update(id=bid, created=str(was.get("created") or when), updated=when,
                name=str(was.get("name") or FIRST_NAME), note=str(was.get("note") or ""))
    # what an AI agent did to the board is the file's, as on the PETs screen, and so is what New AI
    # board made it from
    for key in themes.AGENT_KEYS:
        kept.pop(key, None)
        mark = themes.made_mark(was.get(key)) if key == "made" else themes.agent_mark(was.get(key))
        if mark:
            kept[key] = mark
    if "notes" not in version and was.get("notes"):
        kept["notes"] = themes.notes_of(was, {g["id"] for g in kept["groups"]}, set(kept["cards"]))
    # the page sends the rows of the GET table with the board, and a page from before them sends
    # none, which keeps the rows the file holds
    if "rows" not in version and was.get("rows"):
        kept["rows"] = rows_of(dict(was, groups=kept["groups"]))
    # a page from before the reasons sends no `ai`, and the page sends no `review` or `revise`, what the
    # app's own AI left with a board before 11 November 2026, so the file's stay as they are
    held_was = normal(was, data)
    for key in ("ai",) + themes.FROM_BEFORE:
        if key not in version and held_was.get(key):
            kept[key] = held_was[key]
    # a board an agent made is marked edited by his first save that changes it
    if kept.get("made"):
        kept["made"] = themes.edited_mark(kept["made"], kept, when, kept.get("changed"))
    held = {"history": themes.history_of(was)}
    made = None
    if revision == "auto" and disk is not None:
        made = themes.add_revision(held, auto=True, at=when, state=themes.board_state(was))
    if held["history"]:
        kept["history"] = held["history"]
    boards[at] = kept
    data["boards"] = boards
    data["current"] = bid
    write(root, _file(data, when))
    out = {"saved": True, "updated": when, "version": themes.summary(kept)}
    if made:
        out.update(revision=themes.revision_summary(made), history=themes.history_list(kept))
    return out


def _next_board(boards: list[dict]) -> str:
    n = 0
    for b in boards:
        digits = str(b.get("id") or "")[1:]
        if str(b.get("id") or "").startswith("b") and digits.isdigit():
            n = max(n, int(digits))
    return f"b{max(n, len(boards)) + 1}"


def waiting(data: dict, cases: list[dict]) -> list[str]:
    """The cases of the study that keep GETs from being marked complete, each with why: not in
    from its marked board, changed since it came in, or not read."""
    study = study_of(data, [e["case"] for e in cases])
    out = []
    for e in cases:
        if not study[e["case"]]["in"]:
            continue
        rec = (data.get("cases") or {}).get(e["case"]) or {}
        name = who(e["case"])
        if e["status"] == "unread":
            out.append(i18n.t("server.waiting_unread", name=name))
        elif e["status"] == "changed":
            out.append(i18n.t("server.waiting_changed", name=name))
        elif rec.get("state") == "none":
            out.append(i18n.t("server.waiting_no_pets", name=name))
        elif not rec.get("complete"):
            out.append(i18n.t("server.waiting_not_complete", name=name))
    return out


def said_list(names: list[str]) -> str:
    """Names joined as the run's language joins a list (formats.list_words, Python's tList)."""
    return formats.list_words(names)


def version_op(root: Path, books: list[dict], op: str, body: dict, dry_run: bool = False) -> dict:
    """One change to the boards, as the PETs screen's ops make one, and the screen's state after:
    `new`, every card back in the pile, `duplicate`, `rename`, `note`, `switch`, `delete`, never the
    last, `choose`, the Current board or none, `complete`, GETs marked complete, refused while any
    case of the study is not in from its marked board unchanged, and `reopen`. Every op is an act,
    so every case not yet in comes in first. With `dry_run` (26 October, for the agents' gets ops)
    every check is made and nothing is written: the answer is the op, the board on the canvas after
    it and each board by its id and name."""
    if op not in OPS:
        raise WorkbookError(themes.NOT_A_BOARD_OP, code="unknown_op")
    body = body if isinstance(body, dict) else {}
    when = themes.now_iso()
    data, cases, _disk, _taken = assemble(root, books, when)
    boards = boards_of(data)
    ids = [str(b.get("id")) for b in boards]
    current = str(data.get("current")) if str(data.get("current")) in ids else ids[0]
    vid = str(body.get("id") or current)
    target = next((b for b in boards if str(b.get("id")) == vid), None)
    clearing = op == "choose" and body.get("id") in (None, "")
    if target is None and op not in ("new", "complete", "reopen") and not clearing:
        raise WorkbookError(i18n.t("server.board_gone_gets_changed"))
    if op == "complete":
        if themes.complete_of(data) is None:
            stop = waiting(data, cases)
            if stop:
                raise WorkbookError(i18n.t("server.gets_were_marked_complete_waiting", waiting=said_list(stop)))
            mark = themes.chosen_of(data) or current
            board = themes.find_version(data, mark)
            data["complete"] = {"at": when, "board": mark, "name": str(board.get("name") or FIRST_NAME)}
    elif op == "reopen":
        data["complete"] = None
    elif op == "new":
        name = " ".join(str(body.get("name") or "").split())
        fresh = blank_board(data, _next_board(boards), themes.board_name(boards, name), when)
        boards.append(fresh)
        current = fresh["id"]
    elif op == "duplicate":
        copy = json.loads(json.dumps(normal(target, data)))
        for key in themes.FROM_BEFORE:
            copy.pop(key, None)
        for key in themes.AGENT_KEYS:
            copy.pop(key, None)
        name = " ".join(str(body.get("name") or "").split())
        copy.update(id=_next_board(boards), name=themes._free_name(boards, name or f"{copy['name']} copy"),
                    note="", created=when, updated=when)
        boards.insert(boards.index(target) + 1, copy)
        current = copy["id"]
    elif op == "rename":
        name = " ".join(str(body.get("name") or "").split())
        if not name:
            raise WorkbookError(i18n.t("server.board_needs_name_nothing_changed"))
        if any(str(b.get("name") or "").strip().lower() == name.lower() and b is not target for b in boards):
            raise WorkbookError(i18n.t("server.another_board_called_already_nothing", name=name))
        target.update(name=name, updated=when)
    elif op == "note":
        target.update(note=str(body.get("note") or "").strip(), updated=when)
    elif op == "switch":
        current = vid
    elif op == "choose":
        if clearing:
            data.pop("chosen", None)
        else:
            data["chosen"] = vid
    elif op == "delete":
        if len(boards) == 1:
            raise WorkbookError(i18n.t("server.last_board_cannot_deleted_nothing"))
        at = boards.index(target)
        boards.remove(target)
        if current == vid:
            current = str(boards[max(0, at - 1)].get("id"))
        if str(data.get("chosen")) == vid:
            data.pop("chosen", None)
            if len(boards) == 1:
                data["chosen"] = str(boards[0].get("id"))
    data["boards"] = boards
    data["current"] = current
    if dry_run:
        return {"op": op, "dry_run": True, "current": current, "complete": data.get("complete"),
                "boards": [{"id": str(b.get("id")), "name": str(b.get("name") or FIRST_NAME)} for b in boards]}
    write(root, _file(data, when))
    return dict(answer(data, cases, data), op=op)


def view_state(board: dict, data: dict) -> dict:
    kept = normal(board, data)
    return {"cards": cards_shown(kept, data), "groups": kept["groups"], "discarded": kept["discarded"],
            "picks": {}, "discard_reasons": (kept.get("ai") or {}).get("discarded") or {},
            "stickies": kept.get("notes") or []}


def subs_missing(data: dict, board: dict) -> list[tuple[str, str]]:
    """Every sub-theme of every case in the study with no card on the board, a second card or one
    in the bin counting as a card, by key and title, in case order."""
    study = study_of(data, (data.get("cases") or {}).keys())
    return [(k, t) for case, rec in sorted((data.get("cases") or {}).items(), key=lambda x: case_order(x[0]))
            if study[case]["in"] for k, t in subs_of(case, rec) if not has_card(board, k)]


def add_subs(board: dict, data: dict) -> list[dict]:
    """Add every sub-theme: a card for each sub-theme `subs_missing` finds, in the nearest free spot
    clear of every card, label, frame and sticky note there (`lay_in`), as the page draws them, on
    a copy of the board. The board itself is left as it was, so the page lands the cards as one step
    of undo and the autosave writes them. Refused with one line when there is none to add."""
    entries = subs_missing(data, board)
    if not entries:
        raise WorkbookError(i18n.t("server.every_sub_theme_card_board"))
    work = json.loads(json.dumps(board))
    lay_in(work, entries, data)
    return cards_shown({"cards": {k: work["cards"][k] for k, _ in entries}}, data)


def board_op(root: Path, books: list[dict], op: str, body: dict, dry_run: bool = False) -> dict:
    """A board's history: `revision` keeps one by hand, `view` answers with one as the canvas draws
    it and writes nothing, and `restore` keeps the board as it stands first, then makes the
    revision's state the board's. `subs`, Add every sub-theme, answers with `added`, a card for each
    sub-theme of the study the board has none of, placed by `add_subs`, and writes nothing. With
    `dry_run` (26 October) every check is made and nothing is written."""
    if op not in BOARD_OPS:
        raise WorkbookError(themes.NOT_A_BOARD_OP, code="unknown_op")
    body = body if isinstance(body, dict) else {}
    when = themes.now_iso()
    data, cases, _disk, _taken = assemble(root, books, when)
    boards = boards_of(data)
    ids = [str(b.get("id")) for b in boards]
    current = str(data.get("current")) if str(data.get("current")) in ids else ids[0]
    bid = str(body.get("id") or current)
    board = next((b for b in boards if str(b.get("id")) == bid), None)
    if board is None:
        raise WorkbookError(i18n.t("server.board_gone_gets_changed"))
    if op == "subs":
        return {"op": op, "board": bid, "added": add_subs(board, data)}
    rid = str(body.get("revision") or "")
    revision = next((r for r in themes.history_of(board) if str(r["id"]) == rid), None) if rid else None
    if op in ("view", "restore") and revision is None:
        raise WorkbookError(themes.LOST)
    if op == "view":
        return dict(view_state(revision["state"], data), op=op, revision=themes.revision_summary(revision),
                    board=themes.summary(normal(board, data), board))
    if op == "revision":
        made = themes.add_revision(board, name=str(body.get("name") or "")[:200], at=when)
        extra = {"revision": themes.revision_summary(made)}
    else:
        made = themes.add_revision(board, name=themes.revision_name("before_restoring", when_at=revision["at"]),
                                   at=when)
        restored = json.loads(json.dumps(themes.state_of(themes.normalise(revision["state"]))))
        for key in ("notes", "ai", "quoted", "cut"):
            board.pop(key, None)
        board.update({key: restored[key] for key in themes.STATE_KEYS if key in restored}, updated=when)
        extra = {"revision": themes.revision_summary(made), "restored": themes.revision_summary(revision)}
    if dry_run:
        return dict(op=op, dry_run=True, board=bid, name=str(board.get("name") or FIRST_NAME), **extra)
    write(root, _file(data, when))
    return dict(answer(data, cases, data, board=bid), op=op, **extra)


def words_replaced(root: Path, workbook: Path, rows: dict, before: dict, books: list[dict] | None = None) -> list[str]:
    """A find and replace carried to the copy the file in scope keeps of the participant (24 October 2026,
    "Everything follows"): the project's GETs, inside `lgets` its LGETs, or inside `lpets` the participant's LPETs,
    each of their timepoints in it, from `books` (histreplace, 30 October 2026: a replace had reached the GETs
    alone, leaving the LPETs' and the LGETs' copies behind). `rows` is each row the replace changed, by (sheet,
    row), with `es`, `kq` and `en`, its statements, its quotes by place and its exploratory notes, each a pair of
    lists, the entries before and after. Each of the copy's statements whose words were the old ones takes the
    new, with its quotes and its notes, and so does each board's card of it, and the copy's hash follows. A copy
    that stood as its files did before the replace, `before` (see `copies_untouched`), is read afresh, and when
    that read is the copy as it now stands it keeps the files' new times, so the replace alone never marks the
    participant Changed since it came in. A copy changed already keeps its mark, to be taken as ever. A project
    with no such file, or a participant not in it, has nothing to carry. Answers the keys that took words, and
    writes only when one did."""
    data, entries = held_of(root, workbook, books)
    if data is None or not entries:
        return []
    held = data["cases"]

    def swap(values, old, new):
        out = list(values or [])
        for i, value in enumerate(out):
            if i < len(old) and i < len(new) and value == old[i] and old[i] != new[i]:
                out[i] = new[i]
        return out

    took: dict[str, list[str]] = {}
    for e in entries:
        lines = held[e["case"]].get("lines") if isinstance(held[e["case"]].get("lines"), dict) else {}
        for key, line in lines.items():
            sheet, row, at = themes.split_card_key(key)
            change = rows.get((sheet, row)) if isinstance(line, dict) else None
            if not change or at is None:
                continue
            was = json.dumps(line, sort_keys=True, ensure_ascii=False)
            old, new = change.get("es") or ([], [])
            if at < len(old) and at < len(new) and line.get("text") == old[at]:
                line["text"] = new[at]
            if change.get("kq"):
                line["quotes"] = swap(line.get("quotes"), *change["kq"])
            if change.get("en"):
                line["notes"] = swap(line.get("notes"), *change["en"])
            if json.dumps(line, sort_keys=True, ensure_ascii=False) != was:
                took.setdefault(e["case"], []).append(key)
    if not took:
        return []
    for case, keys in took.items():
        rec = held[case]
        for board in boards_of(data):
            for key in keys:
                card = (board.get("cards") or {}).get(card_of(case, "es", key))
                if isinstance(card, dict) and "text" in card:
                    card["text"] = rec["lines"][key]["text"]
        rec["hash"] = snap_hash(rec)
    kept_in(held, entries, before)
    data["updated"] = themes.now_iso()
    write(root, data)
    return [key for keys in took.values() for key in keys]


def kept_in(held: dict, entries: list[dict], before: dict) -> list[str]:
    """After a write that the copies followed, each case of `entries` that stood as its files did before it,
    `before` (see `copies_untouched`), read afresh, and when that read is its copy as it now stands, its files'
    new times kept, so it is not read again on each open. Answers the cases kept so."""
    kept = []
    for e in entries:
        rec = held[e["case"]]
        if not before.get(e["case"]):
            continue
        try:
            fresh = fresh_of(e)
        except (WorkbookError, OSError):
            continue
        if snap_hash(fresh) == snap_hash(rec) and (rec.get("seen") != fresh["seen"] or rec.get("hash") != snap_hash(rec)):
            rec["seen"] = dict(fresh["seen"])
            rec["hash"] = snap_hash(rec)
            kept.append(e["case"])
    return kept


def held_of(root: Path, workbook: Path, books: list[dict] | None = None) -> tuple[dict | None, list[dict]]:
    """The file in scope as it sits on disk, and each case of it that is the participant's at `workbook`, as a
    survey's entry: on GETs and LGETs the one case whose copy names the workbook, and on LPETs each of the
    participant's timepoints that is in, from `books`, with its timepoint and the label it is cited with. None and
    none with no file."""
    if not gets_path(root).exists():
        return None, []
    data = load(root)
    held = data.get("cases") if isinstance(data.get("cases"), dict) else {}
    name = Path(workbook).name
    if books is None:
        entries = [{"case": c, "workbook": Path(workbook)} for c, rec in held.items()
                   if isinstance(rec, dict) and rec.get("workbook") == name]
    else:
        entries = [dict({"case": b["case"], "workbook": Path(workbook)},
                        **({"timepoint": b["timepoint"], "cite": b.get("cite") or ""} if b.get("timepoint") else {}))
                   for b in books if isinstance(held.get(b["case"]), dict) and Path(b["workbook"]).name == name]
    return data, entries


def copies_untouched(root: Path, workbook: Path, books: list[dict] | None = None) -> dict[str, bool]:
    """Before a write to a participant's statements (30 October 2026, getsedit): each case of the file in scope that
    is theirs, and whether its copy stands as its files do now (see `untouched`), so `statements_followed` reads
    afresh only a copy the write alone can have changed. Nothing with no file, or one that cannot be read."""
    try:
        data, entries = held_of(root, workbook, books)
    except WorkbookError:
        return {}
    held = (data or {}).get("cases") or {}
    return {e["case"]: bool(at_timepoint(e, untouched, Path(workbook), held[e["case"]])) for e in entries}


def statements_followed(root: Path, workbook: Path, words: dict, before: dict, books: list[dict] | None = None,
                        dry: bool = False, changed: dict | None = None, history: str = "",
                        said: dict | None = None) -> dict:
    """A participant's statements reworded in their workbook carried to the copy the file in scope keeps of them,
    the project's GETs, inside `lgets` its LGETs or inside `lpets` the participant's LPETs (30 October 2026,
    getsedit, Adam: "Edit there too", a statement edited from a GETs board as on PETs, the GETs' copy taking the
    words). `words` holds each statement by its key, `Initial:12:0`, with its words before and after. Each line of
    the participant's copy that held the old words takes the new, and so does each board's card of it, and the
    copy's hash follows, so the words alone never mark the participant Changed since they came in. One that stood
    as its files did before the write, `before` (see `copies_untouched`), is read afresh, and when that read is the
    copy as it now stands it keeps the files' new times, so it is not read again on each open (see `kept_in`). A
    change waiting already keeps its mark, to be taken as ever. With `changed`, an agent's mark, each board with a
    card that took words keeps the board as it stood first in its History, under `history`, and is stamped and
    marked changed in a conversation, so an open GETs screen says so. With `said`, his own edit's History line by
    the statement's key (see `themes.edit_line`), every board with a card of it keeps itself first under that line,
    whether or not its copy took the words (histreplace, 30 October 2026). With `dry` nothing is written.

    Answers nothing when nothing took words and no board kept a line, else `cases`, the cases that took words,
    `boards`, each board with a card that did, its id, name and the cards' keys, `versions`, every board as the
    board menu lists it after the write, for the page's next save, and `histories`, each board that kept a line
    with its revisions as the History tab lists them."""
    data, entries = held_of(root, workbook, books)
    if data is None or not entries:
        return {}
    held = data["cases"]
    took: dict[str, list[str]] = {}
    for e in entries:
        lines = held[e["case"]].get("lines") if isinstance(held[e["case"]].get("lines"), dict) else {}
        for key, (old, new) in words.items():
            line = lines.get(key)
            if (isinstance(line, dict) and themes.words(old) != themes.words(new)
                    and themes.words(line.get("text")) == themes.words(old)):
                took.setdefault(e["case"], []).append(key)
    boards = []
    for board in boards_of(data):
        cards = board.get("cards") if isinstance(board.get("cards"), dict) else {}
        keys = [card_of(case, "es", key) for case, keys in took.items() for key in keys
                if isinstance(cards.get(card_of(case, "es", key)), dict)]
        if keys:
            boards.append({"board": str(board.get("id")), "name": str(board.get("name") or FIRST_NAME), "keys": keys})
    out = {"cases": [c for c in held if c in took], "boards": boards}
    if dry:
        return out if took else {}
    when = themes.now_iso()
    # his own edit's line on each board that shows the statement, the board as it stood before the words
    noted = noted_on(data, entries, said or {}, when)
    marked = {b["board"] for b in boards} if changed else set()
    for board in boards_of(data):
        if str(board.get("id")) in marked:
            themes.add_revision(board, name=history, at=when)
    for case, keys in took.items():
        rec = held[case]
        for key in keys:
            rec["lines"][key]["text"] = " ".join(str(words[key][1]).split())
            for board in boards_of(data):
                card = (board.get("cards") or {}).get(card_of(case, "es", key))
                if isinstance(card, dict) and "text" in card:
                    card["text"] = rec["lines"][key]["text"]
        rec["hash"] = snap_hash(rec)
    # a copy with nothing else waiting keeps its files' new times (see `untouched`), read afresh to be sure
    kept = kept_in(held, entries, before)
    for board in boards_of(data):
        if str(board.get("id")) in marked:
            board["updated"] = when
            board["changed"] = dict(changed, at=when)
            board["changed"]["hash"] = themes.state_hash(themes.made_state(normal(board, data)))
    if not took and not kept and not noted:
        return {}
    data["updated"] = when
    write(root, data)
    if not took and not noted:
        return {}
    disk = load(root)
    return dict(out, versions=[themes.summary(b, on_disk(disk, b)) for b in boards_of(disk)],
                histories={str(b.get("id")): themes.history_list(b) for b in boards_of(disk) if str(b.get("id")) in noted})


def noted_on(data: dict, entries: list[dict], said: dict, when: str) -> list[str]:
    """His own edit of a participant's statements kept in the History of each board of the file with a card of one
    (histreplace, Adam, 30 October 2026, "Add a History line"): `said` holds each statement's History line by its
    key (see `themes.edit_line`), and each board keeps itself as it stood under it, one revision a statement, its
    version unchanged by it. The boards that kept a line, by id."""
    out = []
    for board in boards_of(data):
        cards = board.get("cards") if isinstance(board.get("cards"), dict) else {}
        for key, line in said.items():
            if any(isinstance(cards.get(card_of(e["case"], "es", key)), dict) for e in entries):
                themes.add_revision(board, name=line, at=when)
                if str(board.get("id")) not in out:
                    out.append(str(board.get("id")))
    return out


def statements_noted(root: Path, workbook: Path, said: dict, books: list[dict] | None = None) -> dict:
    """A participant's statements he reworded on the statements screen kept in the History of each board of the
    file in scope with a card of one (histreplace, 30 October 2026, see `noted_on`): the project's GETs, inside
    `lgets` its LGETs or inside `lpets` the participant's LPETs, each of their timepoints in it from `books`. The
    copy and its cards keep their words, so the participant shows Changed since it came in, as ever. Answers
    nothing when no board kept a line, else `boards`, those that did by id, and `histories`, each one's revisions as
    the History tab lists them. Writes only when one did."""
    if not said:
        return {}
    data, entries = held_of(root, workbook, books)
    if data is None or not entries:
        return {}
    when = themes.now_iso()
    noted = noted_on(data, entries, said, when)
    if not noted:
        return {}
    data["updated"] = when
    write(root, data)
    return {"boards": noted, "histories": {str(b.get("id")): themes.history_list(b) for b in boards_of(data)
                                           if str(b.get("id")) in noted}}


def lines_followed(case: str, cards: dict, old_lines: dict, fresh_lines: dict) -> dict[str, str]:
    """Where each statement card of a case goes when its changes are taken, by its words, as a PETs
    board's cards follow theirs (see `themes.follow`): a card whose line still holds the words it came
    in with stays, one whose words now stand on another line, as when a write removed a statement
    before it in its passage (20 October), moves to that line, its own row first and the nearest
    line, then the nearest row of its sheet, and one whose words are nowhere keeps its line while no
    other card has taken it, else goes past every line of its row, so it reads as no longer in. The
    card's words are the copy's it came in with, else its own. Answers each card that moves, its key
    and the key it moves to."""
    said = lambda ident, key: themes.words((old_lines.get(ident) or {}).get("text") or (cards.get(key) or {}).get("text"))
    mine = {key: split_key(key)["ident"] for key in cards
            if split_key(key)["case"] == case and split_key(key)["kind"] == "es"}
    live = {k: themes.words(line.get("text")) for k, line in fresh_lines.items()}
    to: dict[str, str] = {}
    for key, ident in mine.items():
        if ident in live and live[ident] == said(ident, key):
            to[key] = ident
    claimed = set(to.values())
    movers = sorted((k for k in mine if k not in to), key=lambda k: themes._order(mine[k]))
    for key in movers:
        ident, w = mine[key], said(mine[key], key)
        sheet, row, line = themes.split_card_key(ident)
        found = [x for x, lw in live.items() if w and lw == w and x not in claimed and themes.split_card_key(x)[0] == sheet]
        if not found:
            continue
        same = [x for x in found if themes.split_card_key(x)[1] == row]
        pick = (min(same, key=lambda x: (abs(themes.split_card_key(x)[2] - (line or 0)), x)) if same else
                min(found, key=lambda x: (abs(themes.split_card_key(x)[1] - (row or 0)), themes._order(x))))
        to[key] = pick
        claimed.add(pick)
    for key in movers:
        if key not in to and mine[key] not in claimed:
            to[key] = mine[key]
            claimed.add(mine[key])
    for key in movers:
        if key in to:
            continue
        sheet, row, _ = themes.split_card_key(mine[key])
        if row is None:
            continue
        taken = [themes.split_card_key(x) for x in set(live) | set(mine.values()) | claimed]
        last = max((ln for s, r, ln in taken if s == sheet and r == row and ln is not None), default=-1)
        to[key] = themes.card_key(sheet, row, last + 1)
        claimed.add(to[key])
    return {key: card_of(case, "es", ident) for key, ident in to.items() if ident != mine[key]}


def make_room_below(board: dict, data: dict, now: dict[str, str], was: dict[str, int]) -> list[str]:
    """Room below each card a take made taller, a PET's title a line longer or a description new under it
    (22 October): what it now meets below it moves straight down just far enough, and pushes on in turn
    (see `themes.push_clear`), so nothing overlaps and nothing placed by hand moves further than that.
    `now` maps each card's key before the take to its key after, `was` each card's height before, and
    `data` holds the case's new copy. The board is changed in place, and the answer is what moved."""
    shown = dict(named(board, data), picks=board.get("picks") or {})
    gone = themes.off_canvas(shown)
    grown = [key for old, key in now.items() if key not in gone and old in was
             and card_height(key, shown["cards"][key].get("text")) > was[old]]
    if not grown:
        return []
    moved = themes.push_clear(shown, grown, card_height)
    for key, c in shown["cards"].items():
        board["cards"][key]["x"], board["cards"][key]["y"] = c["x"], c["y"]
    return moved


def take(root: Path, books: list[dict], case: str) -> dict:
    """Take the changes of a case that changed since it came in: each GET board keeps a revision
    first, each card of its PETs keeps its place by id, then by title, a statement's card by its
    line, then by its words, a top-level PET with no card and a sub-theme new to the case come in
    unplaced in the nearest free spot, and a card whose PET has gone from the case stays where it
    is, its title kept on it, marked "No longer in" its PETs. A sub-theme the copy held already and
    the board never did, on a board made before sub-themes came in as cards, stays off it (Add every
    sub-theme brings it). Nothing is moved or binned by itself."""
    when = themes.now_iso()
    data, cases, _disk, _taken = assemble(root, books, when)
    entry = next((e for e in cases if e["case"] == case), None)
    old = (data.get("cases") or {}).get(case)
    if entry is None or old is None:
        raise WorkbookError(i18n.t("server.participant_gets_yet_nothing_came"))
    if entry["status"] == "in":
        raise WorkbookError(i18n.t("server.nothing_changed_s_pets_since", who_case=who(case)))
    fresh = entry["fresh"] if entry["fresh"] is not None else fresh_of(entry)
    pairs = matched(old.get("pets") or [], fresh["pets"])
    # what comes in: every top-level PET with no card, as before, and a sub-theme new to the case
    new = {p["id"] for p in fresh["pets"]} - set(pairs.values())
    comers = tops(case, fresh) + [e for e in subs_of(case, fresh) if split_key(e[0])["ident"] in new]
    titles = {p["id"]: p["title"] for p in old.get("pets") or []}
    name = who(case)
    # the cards' words for the estimates of the layout, this case's from its new copy
    seen = dict(data, cases=dict(data.get("cases") or {}, **{case: {"pets": fresh["pets"], "lines": fresh["lines"]}}))
    for board in boards_of(data):
        themes.add_revision(board, name=themes.revision_name("before_changes", who=name), at=when)
        # each card's height as it stood, for the room a card that grows makes below it (see `make_room_below`)
        was = {k: card_height(k, c.get("text")) for k, c in named(board, data)["cards"].items()}
        # a statement's card follows its words, whatever a write moved or removed in its passage
        rename = lines_followed(case, board.get("cards") or {}, old.get("lines") or {}, fresh["lines"])
        for key in list(board.get("cards") or {}):
            k = split_key(key)
            if k["case"] != case:
                continue
            if k["kind"] == "group":
                to = pairs.get(k["ident"])
                if to is None:
                    board["cards"][key]["text"] = board["cards"][key].get("text") or titles.get(k["ident"], themes.UNTITLED)
                elif to != k["ident"]:
                    fresh_key = card_of(case, "group", to) + (f"/{k['copy']}" if k["copy"] else "")
                    if fresh_key not in board["cards"]:
                        rename[key] = fresh_key
        if rename:
            board["cards"] = {rename.get(k, k): c for k, c in board["cards"].items()}
            for g in board.get("groups") or []:
                g["members"] = [rename.get(m, m) for m in g.get("members") or []]
            board["discarded"] = [rename.get(k, k) for k in board.get("discarded") or []]
        back = {to: key for key, to in rename.items()}
        make_room_below(board, seen, {back.get(k, k): k for k in board.get("cards") or {}}, was)
        lay_in(board, comers, seen)
        # in a thematic analysis project a new extract of a code on the board comes in where it stands (codes)
        if ta_now():
            codes_mod().gather(board, seen)
        board["updated"] = when
    data["cases"][case] = record(fresh, entry["workbook"], when)
    write(root, _file(data, when))
    current = data.get("current")
    return dict(answer(data, survey(books, data), data, board=current), op="take", taken=case)


def settings_op(root: Path, books: list[dict], body: dict, dry_run: bool = False, asker: dict | None = None) -> dict:
    """The study's own settings, kept in the file: `minimum`, a whole number or null for Smith's
    band, `one_per_pet`, and `study`, each case in
    or out with the reason he gave. An act, so every case not yet in comes in first. With `dry_run`
    (26 October, for the agents' gets settings) every check is made and nothing is written: the
    answer is the settings and each case's place in the study as they would be. A save that changes a
    setting is kept in the project's History (projhistory, 2 November 2026), `asker` asking, the caller
    holding the project's lock (see `project_history`)."""
    body = body if isinstance(body, dict) else {}
    when = themes.now_iso()
    data, cases, _disk, _taken = assemble(root, books, when)
    held = settings_of(data)
    was_settings = dict(held)
    was_study = study_of(data, sorted({e["case"] for e in cases}, key=case_order))
    if "minimum" in body:
        value = body.get("minimum")
        try:
            held["minimum"] = None if value in (None, "") else max(1, min(99, int(value)))
        except (TypeError, ValueError):
            raise WorkbookError(i18n.t("server.minimum_whole_number_nothing_changed"))
    if "one_per_pet" in body:
        held["one_per_pet"] = bool(body.get("one_per_pet"))
    data["settings"] = held
    sent = body.get("study") if isinstance(body.get("study"), dict) else {}
    study = data.setdefault("study", {})
    known = {e["case"] for e in cases}
    for case, mark in sent.items():
        if case not in known or not isinstance(mark, dict):
            continue
        if mark.get("in") is False:
            reason = " ".join(str(mark.get("reason") or "").split())
            if not reason:
                raise WorkbookError(i18n.t("server.say_line_why_out_study", who_case=who(case)))
            study[case] = {"in": False, "reason": reason[:200]}
        else:
            study[case] = {"in": True}
    if dry_run:
        return {"op": "settings", "dry_run": True, "settings": settings_of(data),
                "study": study_of(data, sorted(known, key=case_order))}
    write(root, _file(data, when))
    import project_history
    project_history.record(root, "gets settings",
                           settings_changes(was_settings, settings_of(data), was_study,
                                            study_of(data, sorted(was_study, key=case_order))), asker, when)
    return dict(answer(data, cases, data), op="settings")


def settings_changes(was: dict, now: dict, was_study: dict | None = None, now_study: dict | None = None) -> list[str]:
    """What a save of the study's settings changed, a line each, as the project's History keeps it."""
    out = []
    said = lambda m: "the usual number" if m is None else str(m)
    if was.get("minimum") != now.get("minimum"):
        out.append(f"Participants needed for a GET from {said(was.get('minimum'))} to {said(now.get('minimum'))}.")
    if was.get("one_per_pet") != now.get("one_per_pet"):
        on = lambda v: "on" if v else "off"
        out.append(f"One per PET from {on(was.get('one_per_pet'))} to {on(now.get('one_per_pet'))}.")
    for case, mark in (now_study or {}).items():
        old = (was_study or {}).get(case) or {"in": True, "reason": ""}
        if old["in"] != mark["in"] or (not mark["in"] and old["reason"] != mark["reason"]):
            out.append(f"{who(case)} back in the study." if mark["in"] else f"{who(case)} out of the study: {mark['reason']}.")
    return out


def settings_view(root: Path, books: list[dict]) -> dict:
    """What Settings shows under GETs, read from the GETs file alone and nothing written: the
    switch, the minimum and whether it is Smith's band, and each case of the study with its tick
    and the reason it is out."""
    try:
        data = load(root)
    except WorkbookError:
        data = None
    cases = sorted({b["case"] for b in books}, key=case_order)
    study = study_of(data, cases)
    settings = settings_of(data)
    inside = [c for c in cases if study[c]["in"]]
    minimum, is_band = minimum_of(settings, len(inside))
    return {"settings": settings, "minimum": minimum, "band": is_band, "total": len(inside),
            "smith": band(len(inside)),
            "study": [{"case": c, "who": who(c), "in": study[c]["in"], "reason": study[c]["reason"]} for c in cases]}


def summary_of(root: Path, books: list[dict]) -> dict:
    """The head row of All cases, read cheaply and never written: the cases in the study and those
    with their PETs marked complete, and GETs marked complete when they are. Reads the GETs file
    alone, for the cases Settings took out, and no workbook."""
    try:
        data = load(root)
    except WorkbookError:
        data = None
    study = study_of(data, [b["case"] for b in books])
    inside = [b for b in books if study[b["case"]]["in"]]
    return {"cases": len(inside), "complete": sum(1 for b in inside if b.get("pets_complete")),
            "done": themes.complete_of(data)}


# ---------------------------------------------------------- the GET table

# a participant with no PETs, so nothing under a GET, says it in this one line, with no mark beside
# the name, in the table and the trail alike (17 October, after the screenshot check)


def named(board: dict, data: dict) -> dict:
    """A board with words on every card, a PET's and a statement's read from its case's copy, for
    the estimates of its layout."""
    held = data.get("cases") or {}
    cards = {}
    for key, c in (board.get("cards") or {}).items():
        text = c.get("text") or ""
        if not text:
            k = split_key(key)
            rec = held.get(k["case"]) or {}
            if k["kind"] == "group":
                pet = next((p for p in rec.get("pets") or [] if p["id"] == k["ident"]), None)
                text = layout_text(pet["title"], pet.get(themes.DESCRIPTION)) if pet else ""
            elif k["kind"] == "es":
                text = ((rec.get("lines") or {}).get(k["ident"]) or {}).get("text") or ""
        cards[key] = dict(c, text=text)
    return dict(board, cards=cards, groups=board.get("groups") or [], discarded=board.get("discarded") or [],
                picks={}, notes=board.get("notes") or [])


def items_under(shown: dict, gid: str, drawn: dict) -> list[dict]:
    """The cards under a group in the order the canvas reads them, higher first, at any depth, a
    sub-theme's cards where its frame's top sits, each with the labels of the sub-themes between it
    and the group. A discarded card is left out."""
    by_id = {g["id"]: g for g in shown.get("groups") or []}
    thrown = set(shown.get("discarded") or [])
    out: list[dict] = []

    def walk(at: str, within: list[str], seen: frozenset) -> None:
        for m in themes.theme_order(shown, at, drawn):
            if m in by_id:
                if m not in seen:
                    walk(m, within + [by_id[m]["label"]], seen | {m})
            elif m in (shown.get("cards") or {}) and m not in thrown:
                out.append({"key": m, "within": within})

    walk(gid, [], frozenset({gid}))
    return out


def row_places(quotes: list[dict]) -> list[str]:
    """A row's quotes by place, as a case's copy keeps them on each of its statements: the
    words at each quote's place, and an empty place where the cell holds "(no quote)"."""
    places: list[str] = []
    for q in quotes:
        at = themes.split_card_key(q["key"])[2]
        if at is not None:
            places += [""] * (at + 1 - len(places))
            places[at] = q["text"]
    return places


def line_quotes(line: dict, own: str | None = None) -> list[dict]:
    """A row's quotes as a statement's copy keeps them, each with its key,
    `<sheet>:<row>:<place>`, an empty place or "(no quote)" left out. With `own`, the statement's
    key, its own quote alone, the one at its place."""
    place = themes.split_card_key(own)[2] if own else None
    return [{"key": f"{line.get('sheet')}:{line.get('row')}:{i}", "text": q, "sheet": line.get("sheet") or "",
             "row": line.get("row"), "time": line.get("time") or "", "seconds": line.get("seconds")}
            for i, q in enumerate(line.get("quotes") or [])
            if str(q or "").strip() and not no_quote(q) and (own is None or i == place)]


def quote_at(rec: dict, qkey) -> dict | None:
    """A quote of a case's copy by its key, with its sheet, row and timecode, or None when the
    copy no longer holds it."""
    sheet, row, _ = themes.split_card_key(str(qkey or ""))
    if row is None:
        return None
    for line in (rec.get("lines") or {}).values():
        if line.get("sheet") == sheet and line.get("row") == row:
            found = next((q for q in line_quotes(line) if q["key"] == str(qkey)), None)
            if found:
                return found
    return None


def pet_lines(rec: dict, pid: str) -> list[str]:
    """A PET's statements at any depth, its own first in the order its board reads them, then each
    sub-theme's."""
    pets = {p["id"]: p for p in rec.get("pets") or []}
    out: list[str] = []
    seen: set = set()

    def walk(at: str) -> None:
        if at in seen or at not in pets:
            return
        seen.add(at)
        out.extend(k for k in pets[at].get("statements") or [] if k not in out)
        for sub in pets[at].get("subs") or []:
            walk(sub)

    walk(pid)
    return out


def item_of(rec: dict, key: str, card: dict, within=()) -> dict:
    """One card under a GET as the table and the trail set it out: a PET or a sub-theme with its
    title, note, statements and picks, a statement with its sheet, timecode, its own quote and
    exploratory notes, or a participant note, his words."""
    k = split_key(key)
    base = {"key": key, "within": list(within), "gone": False}
    if k["kind"] == "pn":
        return dict(base, kind="pn", text=str(card.get("text") or ""))
    lines = rec.get("lines") or {}
    if k["kind"] == "es":
        line = lines.get(k["ident"])
        if line is None:
            return dict(base, kind="es", gone=True, text=str(card.get("text") or ""), sheet="", time="", seconds=None,
                        row=None, quotes=[], notes=[], line=k["ident"])
        return dict(base, kind="es", text=line["text"], sheet=line.get("sheet") or "", time=line.get("time") or "",
                    seconds=line.get("seconds"), row=line.get("row"), quotes=line_quotes(line, k["ident"]),
                    notes=list(line.get("notes") or []), line=k["ident"])
    pet = next((p for p in rec.get("pets") or [] if p["id"] == k["ident"]), None)
    if pet is None:
        return dict(base, kind="pet", gone=True, title=str(card.get("text") or themes.UNTITLED), note="", lines=[],
                    picks=[], statements=0)
    keys = pet_lines(rec, pet["id"])
    picks = [q for q in (quote_at(rec, p) for p in pet.get("picks") or []) if q]
    return dict(base, kind="pet" if pet.get("parent") is None else "sub", title=pet["title"], note=pet.get("note") or "",
                lines=keys, picks=picks, statements=len(keys), description=themes.description_of(pet))


def first_quote(items: list[dict], rec: dict) -> dict | None:
    """The quote a row starts with: the first pick of the participant's highest PET there, and
    failing a pick, the first statement there with a quote of its own, in the order the GET
    reads."""
    for it in items:
        if it["kind"] in ("pet", "sub") and it["picks"]:
            return it["picks"][0]
    lines = rec.get("lines") or {}
    for it in items:
        if it["kind"] == "es" and it["quotes"]:
            return it["quotes"][0]
        if it["kind"] in ("pet", "sub"):
            for key in it["lines"]:
                quotes = line_quotes(lines.get(key) or {}, key)
                if quotes:
                    return quotes[0]
    return None


def table(data: dict, board: dict, inside: list[str]) -> list[dict]:
    """The GET table of a board: each GET in canvas order with its note and its count, then a row
    for every case in the study in case order, its PETs, sub-themes, statements and participant
    notes under the GET in the order the canvas reads them, its quote, the one he ticked or
    else the one it starts with, and his note for the row. `counted` says whether anything of the
    case's counts there, a participant note never. Reads the file alone, and writes nothing."""
    kept = normal(board, data)
    shown = named(kept, data)
    drawn = themes.layout_boxes(shown, card_height)
    by_id = {g["id"]: g for g in kept["groups"]}
    parents = themes.parents_of(kept["groups"])
    held = data.get("cases") or {}
    cases = sorted(inside, key=case_order)
    out = []
    for gid in themes.canvas_order([g["id"] for g in kept["groups"] if g["id"] not in parents], by_id):
        under = items_under(shown, gid, drawn)
        rows = []
        for case in cases:
            rec = held.get(case) or {}
            items = [item_of(rec, it["key"], shown["cards"][it["key"]], it["within"])
                     for it in under if split_key(it["key"])["case"] == case]
            stored = (kept["rows"].get(gid) or {}).get(case) or {}
            chosen = quote_at(rec, stored.get("quote")) if stored.get("quote") else None
            rows.append({"case": case, "who": who(case), "items": items,
                         "counted": any(it["kind"] != "pn" for it in items),
                         "quote": chosen or first_quote(items, rec), "chosen": chosen is not None,
                         "note": stored.get("note") or "", "bold": stored.get("bold") or [] if chosen else [],
                         "open": rec.get("state") == "in" and not rec.get("complete"),
                         "none": rec.get("state") == "none"})
        g = by_id[gid]
        out.append({"id": gid, "label": g["label"], "note": str(g.get("note") or ""),
                    "description": themes.description_of(g),
                    "count": count(kept, gid, set(inside)), "rows": rows,
                    "subs": [by_id[m]["label"] for m in g["members"] if m in by_id]})
    return out


# ---------------------------------------------------------------- the AI's titles
#
# What a GET's suggested titles are sent, as plain dicts `themes_ai` reads: a board set out GET by
# GET, each card by its participant's pseudonym. A participant note, a sticky note and a row's note
# never go into it.


def propose(root: Path, books: list[dict], version: dict, note: str) -> dict:
    """A board laid out whole added to the GETs file, as `new` adds one: laid out by the server, under
    the next `Board N` name, with its note, no participant notes or sticky notes, and made current.
    Every other board stays as it was."""
    when = themes.now_iso()
    data, cases, _disk, _taken = assemble(root, books, when)
    boards = boards_of(data)
    bid = _next_board(boards)
    board = dict(version, id=bid, name=themes.board_name(boards), note=str(note or "").strip(), created=when,
                 updated=when)
    board.pop("notes", None)
    board.pop("history", None)
    kept = normal(board, data)
    kept.update(id=bid, name=board["name"], note=board["note"], created=when, updated=when)
    kept.pop("notes", None)
    boards.append(kept)
    data["boards"] = boards
    data["current"] = bid
    write(root, _file(data, when))
    return dict(answer(data, cases, data, board=bid), op="propose")


def ai_card(rec: dict, key: str, card: dict) -> dict | None:
    """One card of a GETs board as a title's prompt is sent it, or None for a participant note: a PET or
    a sub-theme with its title, note and statements, a statement with its sheet, timecode and words."""
    k = split_key(key)
    it = item_of(rec, key, card)
    if it["kind"] == "pn":
        return None
    lines = rec.get("lines") or {}
    out = {"key": key, "case": k["case"], "who": who(k["case"]), "kind": it["kind"], "gone": bool(it["gone"])}
    if it["kind"] in ("pet", "sub"):
        out.update(title=it.get("title") or "", note=it.get("note") or "",
                   statements=[{"key": card_of(k["case"], "es", lk), "sheet": lines[lk].get("sheet") or "",
                                "time": lines[lk].get("time") or "", "text": lines[lk]["text"]}
                               for lk in it.get("lines") or [] if lk in lines])
    else:
        out.update(text=it.get("text") or "", sheet=it.get("sheet") or "", time=it.get("time") or "")
    return out


def ai_outline(data: dict, board: dict, inside: list[str], minimum: int) -> dict:
    """A GETs board as the titles set it out: each GET in canvas order with its id, title, note and
    count, its cards in the order the canvas reads them, the participants with nothing under it, and
    its sub-themes under it. A participant note is never in it. Reads the file alone, and writes
    nothing."""
    kept = normal(board, data)
    shown = named(kept, data)
    drawn = themes.layout_boxes(shown, card_height)
    by_id = {g["id"]: g for g in kept["groups"]}
    parents = themes.parents_of(kept["groups"])
    thrown = set(kept["discarded"])
    held = data.get("cases") or {}
    cases = sorted(inside, key=case_order)

    def card(key: str) -> dict | None:
        return ai_card(held.get(split_key(key)["case"]) or {}, key, shown["cards"][key])

    def get(gid: str, seen: frozenset) -> dict:
        members = themes.theme_order(shown, gid, drawn)
        cards = [c for c in (card(m) for m in members if m not in by_id and m in shown["cards"] and m not in thrown) if c]
        subs = [get(m, seen | {m}) for m in members if m in by_id and m not in seen]
        there = {split_key(k)["case"] for k in themes.cards_under(by_id, gid)
                 if k in shown["cards"] and k not in thrown and split_key(k)["kind"] != "pn"}
        return {"id": gid, "label": by_id[gid]["label"], "note": str(by_id[gid].get("note") or ""),
                "count": count(kept, gid, set(inside)), "cards": cards, "themes": subs,
                "missing": [who(c) for c in cases if c not in there]}

    return {"name": kept["name"], "total": len(inside), "minimum": minimum, "study": [who(c) for c in cases],
            "themes": [get(g, frozenset({g}))
                       for g in themes.canvas_order([g["id"] for g in kept["groups"] if g["id"] not in parents], by_id)]}


def row_targets(data: dict, board: dict, inside: list[str]) -> list[dict]:
    """The rows of a board's GET table with the quotes each could take, a GET and a case each, in table
    order, which the demo's key quotes are picked from: its id, `G1/<case>`, the GET's id and title,
    the case's pseudonym, and the quotes of that case's items under the GET, each by its key,
    `<sheet>:<row>:<place>`, and its words, once each. A row with nothing that counts, or with no
    quotes, is left out."""
    held = data.get("cases") or {}
    out = []
    for g in table(data, board, inside):
        for row in g["rows"]:
            if not row["counted"]:
                continue
            lines = (held.get(row["case"]) or {}).get("lines") or {}
            quotes: list[dict] = []
            for it in row["items"]:
                found = it.get("quotes") or [] if it["kind"] == "es" else list(it.get("picks") or []) + [
                    q for lk in it.get("lines") or [] for q in line_quotes(lines.get(lk) or {}, lk)]
                for q in found:
                    if q["key"] not in {x["key"] for x in quotes} and str(q.get("text") or "").strip():
                        quotes.append({"key": q["key"], "text": " ".join(str(q["text"]).split())})
            if quotes:
                out.append({"id": f"{g['id']}/{row['case']}", "get": g["id"], "label": g["label"], "case": row["case"],
                            "who": row["who"], "quotes": quotes})
    return out


# ---------------------------------------------------------------- the LPET table's rows on Trajectories
#
# Trajectories (trajbuild2, 10 November 2026, layout F) shows each LPET as a row across the timepoints, and each
# cell is that LPET's row of the LPET table at that timepoint: his note on the row is the LPET's state there, the
# quote he ticked is its key quote, the first standing in until he ticks one, and `bold` his bold in it. Run
# inside `lpets`, on the board the participant's LPETs come into LGETs from (`source_board`), so the LPETs
# screen's Inspector, the LPET table and Trajectories show the same tick and the same note.
#
# A key quote comes from one of three places (trajchoose, 11 November 2026, Adam's ruling): the LPET's own
# statements' quotes at that timepoint, `lpet`, as the Inspector offers them, the participant's other quotes from
# that interview, `interview`, a statement in another LPET or in none, ticked by its key just the same, and a
# passage of the transcript, `transcript`, any of the participant's interviews, kept on the row as `passage`.
# Ticking one moves no statement and writes no workbook.
SOURCES = ("lpet", "interview", "transcript")


def row_choices(items: list[dict], rec: dict) -> list[dict]:
    """The quotes a row can take as its key quote, as the Inspector offers them: each PET's and sub-theme's picks,
    then its statements' quotes, and a statement's own, once each, each from the LPET, `source` `lpet`."""
    out: list[dict] = []
    lines = rec.get("lines") or {}
    for it in items:
        found = it.get("quotes") or [] if it["kind"] == "es" else list(it.get("picks") or []) if it["kind"] in ("pet", "sub") else []
        if it["kind"] in ("pet", "sub"):
            for key in it.get("lines") or []:
                found += line_quotes(lines.get(key) or {}, key)
        for q in found:
            if not any(x["key"] == q["key"] for x in out):
                out.append({"key": q["key"], "text": q["text"], "time": q.get("time") or "", "source": "lpet"})
    return out


def interview_quotes(data: dict, inside: list[str], bare: bool = True) -> dict:
    """Every statement's own quote in each timepoint's interview as the participant's LPETs file holds it, by the
    timepoint's key, each once in transcript order, `{"T1": [{"key", "text", "time"}]}`: the quotes a cell may take
    beyond its LPET's own, whether their statement sits in another LPET or in none (trajchoose, 11 November 2026).
    Without the marks the workbook keeps round them unless `bare` is false. Reads alone."""
    out = {}
    for tp in inside:
        rec = (data.get("cases") or {}).get(tp) or {}
        found, seen = [], set()
        for key, line in (rec.get("lines") or {}).items():
            for q in line_quotes(line, key) if isinstance(line, dict) else []:
                text = themes.bare(q["text"]) if bare else q["text"]
                if q["key"] not in seen and text.strip():
                    seen.add(q["key"])
                    found.append({"key": q["key"], "text": text, "time": q.get("time") or ""})
        out[tp] = found
    return out


def cite_of(data: dict, at: str) -> str:
    """The label a timepoint's quotes are cited with, T3, as its copy cites them, its label in scope failing that."""
    return str(((data.get("cases") or {}).get(at) or {}).get("cite") or (NAMES.get() or {}).get(at) or at)


def passage_found(kept: dict | None, turns) -> dict | None:
    """A passage a row keeps as the transcript has it now: its turn's words at its place, or where the same words
    stand in that turn since an edit moved them, with the turn's time. None when the turn or its words are gone,
    and the row's key quote then falls back as a lost one does. `turns` gives a timepoint's turns by its key."""
    if not kept or turns is None:
        return None
    turn = next((t for t in turns(kept["at"]) or [] if t["turn"] == kept["turn"]), None)
    if turn is None:
        return None
    words = str(turn.get("text") or "")
    start = kept["start"] if words[kept["start"]:kept["end"]] == kept["text"] else words.find(kept["text"])
    if start < 0:
        return None
    return {"at": kept["at"], "turn": kept["turn"], "start": start, "end": start + len(kept["text"]),
            "text": kept["text"], "time": turn.get("time") or ""}


def passage_from(given, labels: dict, inside: list[str], turns, name: str) -> dict:
    """A passage an operation names, checked against the transcript as it is now: `interview`, a timepoint by its
    key, number or label, `turn`, `<sheet>:<row>` as `turn show` gives it (or `sheet` and `row`), and `start` and
    `end`, places in the turn's words by character, the whole turn without them, widened to whole words with the
    spaces at its edges left out. Refused when it is not in the participant's transcript."""
    if not isinstance(given, dict):
        raise WorkbookError(i18n.t("server.trajectory_passage_shape"))
    at = timepoint_of(given.get("interview"), labels)
    if at is None or at not in inside:
        raise WorkbookError(i18n.t("server.trajectory_no_such_timepoint",
                                   timepoint=" ".join(str(given.get("interview") or "").split()) or "none"))
    said = tp_names(labels, at)[0]
    here = (turns(at) if turns is not None else None) or []
    if not here:
        raise WorkbookError(i18n.t("server.trajectory_no_transcript", name=name, timepoint=said))
    asked = str(given.get("turn") or "").strip()
    if not asked and given.get("sheet") not in (None, "") and given.get("row") not in (None, ""):
        asked = themes.row_key(str(given["sheet"]), given["row"])
    turn = next((t for t in here if t["turn"] == asked), None)
    if turn is None:
        raise WorkbookError(i18n.t("server.trajectory_no_such_turn", turn=asked or "none", name=name, timepoint=said))
    words = str(turn["text"])
    start = given.get("start", 0) if given.get("start") is not None else 0
    end = given.get("end", len(words)) if given.get("end") is not None else len(words)
    if not all(isinstance(x, int) and not isinstance(x, bool) for x in (start, end)) or not 0 <= start < end <= len(words):
        raise WorkbookError(i18n.t("server.trajectory_passage_span", most=len(words)))
    while start < end and words[start].isspace():
        start += 1
    while end > start and words[end - 1].isspace():
        end -= 1
    if start >= end:
        raise WorkbookError(i18n.t("server.trajectory_passage_span", most=len(words)))
    while start > 0 and not words[start - 1].isspace():
        start -= 1
    while end < len(words) and not words[end].isspace():
        end += 1
    if end - start > PASSAGE_MAX:
        raise WorkbookError(i18n.t("server.trajectory_passage_span", most=len(words)))
    return {"at": at, "turn": turn["turn"], "start": start, "end": end, "text": words[start:end]}


def quote_cut(said) -> tuple[str, int]:
    """A key quote's words as Trajectories shows them, without the marks the workbook keeps round them
    (`themes.bare`, as thBareQuote and canvas_out's `bare_quote`), and how many characters that took off its
    front (trajfix, 11 November 2026). His bold is kept against the quote as the copy holds it, marks and all,
    so it is moved by that many to show and back by as many to keep, and stays on the same words. The words
    always sit in the copy at the first place they match, unless a quote is nothing but marks."""
    raw = str(said or "")
    text = themes.bare(raw)
    return text, max(0, raw.find(text)) if text else 0


def lpet_rows(data: dict, board: dict | None, inside: list[str], bare: bool = True, turns=None) -> list[dict]:
    """Each LPET of the board in canvas order, its title, description and domain, and a cell for each timepoint
    in `inside`: its `state`, its key quote, `quote` (`{"key", "text", "time", "source"}` or None), whether he
    ticked it, `chosen`, his bold in it, and the LPET's own quotes it could take, `choices`. A quote's `source` is
    where it comes from (SOURCES): a ticked statement's quote outside the LPET is `interview`, and a passage of
    the transcript is `transcript` with an empty key, its interview `at` and `passage` (`{"at", "turn", "start",
    "end"}`), read through `turns`, which gives a timepoint's turns by its key, a passage whose words are gone
    falling back as a lost quote does. Each quote's words come without the marks the workbook keeps round them and
    his bold is measured against them (`quote_cut`), unless `bare` is false, which gives both as the row keeps
    them, for `row_op`. Reads alone."""
    if board is None:
        return []
    kept = normal(board, data)
    by_id = {g["id"]: g for g in kept["groups"]}
    out = []
    for g in table(data, board, inside):
        cells = {}
        for row in g["rows"]:
            rec = (data.get("cases") or {}).get(row["case"]) or {}
            q, chosen, bold = row.get("quote"), bool(row.get("chosen")), row.get("bold") or []
            choices = row_choices(row["items"], rec)
            stored = (kept["rows"].get(g["id"]) or {}).get(row["case"]) or {}
            found = passage_found(stored.get("passage"), turns) if stored.get("passage") else None
            if found:
                cite = cite_of(data, found["at"])
                q = {"key": "", "text": found["text"], "time": f"{cite}, {found['time']}" if found["time"] else cite,
                     "source": "transcript", "at": found["at"],
                     "passage": {k: found[k] for k in ("at", "turn", "start", "end")}}
                chosen, bold = True, stored.get("bold") or []
            elif q:
                own = not chosen or any(c["key"] == q["key"] for c in choices)
                q = {"key": q["key"], "text": q["text"], "time": q.get("time") or "", "source": "lpet" if own else "interview"}
            text, cut = quote_cut(q["text"]) if q and bare else (q["text"] if q else "", 0)
            bold = [[max(0, a - cut), min(len(text), b - cut)] for a, b in bold]
            if bare:
                choices = [dict(c, text=themes.bare(c["text"])) for c in choices]
            cells[row["case"]] = {"state": row.get("note") or "", "chosen": chosen,
                                  "quote": dict(q, text=text) if q else None,
                                  "bold": [s for s in bold if s[0] < s[1]], "choices": choices,
                                  "missing": rec.get("state") != "in"}
        out.append({"id": g["id"], "title": g["label"], "description": g.get("description") or "",
                    "domain": str((by_id.get(g["id"]) or {}).get(themes.DOMAIN) or ""), "cells": cells})
    return out


# the en and em dash a head may end with, by their code points
DASHES = chr(0x2013) + chr(0x2014)


def tp_names(labels: dict, key: str) -> list[str]:
    """A timepoint's names, its label first, then its description: `labels` gives each key its label, or a list
    of its label and its description."""
    held = labels.get(key)
    names = held if isinstance(held, (list, tuple)) else [held]
    return [" ".join(str(n).split()) for n in names if n and str(n).strip()] or [key]


def timepoint_of(given, labels: dict) -> str | None:
    """A timepoint by its key, T2, its number, 2, its label or its description, any case."""
    said = " ".join(str(given if given is not None else "").split()).lower()
    for key in labels:
        if said in [key.lower(), key[1:]] + [n.lower() for n in tp_names(labels, key)]:
            return key
    return None


def states_in_note(note: str, labels: dict) -> dict:
    """An LPET's note read as its states, a paragraph headed by each timepoint, "T1: Knew she should ...", by its
    key, its label or its description, the head's words left out. A note with no such heads has none."""
    named = {h.lower(): key for key in labels for h in [key] + tp_names(labels, key)}
    heads = sorted(named, key=len, reverse=True)
    if not heads:
        return {}
    pattern = re.compile(r"^\s*[*_]*(" + "|".join(re.escape(h) for h in heads) + r")\b[*_]*"
                         r"(?:\s*\([^)\n]*\)|[ \t]+[^:\n]{1,40}(?=:))?\s*[:.\-" + DASHES + r"]?\s*(.*)$", re.I)
    out: dict[str, list[str]] = {}
    at = None
    for line in str(note or "").replace("\r\n", "\n").split("\n"):
        found = pattern.match(line)
        if found and named.get(found.group(1).lower()):
            at = named[found.group(1).lower()]
            out.setdefault(at, [])
            if found.group(2).strip():
                out[at].append(found.group(2).strip())
        elif at is not None and line.strip():
            out[at].append(line.strip())
        elif at is not None and not line.strip() and out[at]:
            out[at].append("")
    return {k: "\n".join(v).strip() for k, v in out.items() if "\n".join(v).strip()}


def row_op(data: dict, board: dict, inside: list[str], labels: dict, op: dict, name: str, turns=None) -> list[str]:
    """One operation on the LPET table's rows or an LPET of `board`, in place, answering its lines, refused as a
    whole when it is wrong: `state` (`lpet`, `timepoint`, `state`), `quote` (`lpet`, `timepoint`, and `quote`, the
    key of a quote of the LPET's own or of another statement of that interview, or `passage`, a passage of any of
    the participant's interviews as `passage_from` reads one, or neither to take his tick off), `bold` (`lpet`,
    `timepoint`, `spans`, `[[start, end]]` of the key quote's words as `lpet_rows` gives them, without the marks
    round them, none clearing it, the quote standing in ticked with it), `domain` (`lpet`, `domain`, several
    separated by commas, "" taking it off) and `states_from_notes` (each LPET's note's paragraphs headed by a
    timepoint into its rows' notes where they hold none, the note left as it was). `name` is the participant's,
    for the lines, and `turns` gives a timepoint's turns of their transcript by its key. Nothing here moves a
    statement or writes a workbook."""
    kind = str(op.get("op") or "")
    # the quotes and his bold as the rows keep them, marks and all: spans come in against the words alone
    rows = {g["id"]: g for g in lpet_rows(data, board, inside, bare=False, turns=turns)}
    groups = {g["id"]: g for g in board.get("groups") or [] if isinstance(g, dict)}
    if not isinstance(board.get("rows"), dict):
        board["rows"] = {}
    held = board["rows"]

    def lpet() -> dict:
        given = " ".join(str(op.get("lpet") or op.get("label") or "").split())
        found = rows.get(given) or next((r for r in rows.values() if r["title"].lower() == given.lower()), None)
        if found is None:
            raise WorkbookError(i18n.t("server.trajectory_no_such_lpet", name=name, lpet=given or "with no name"))
        return found

    def tp() -> str:
        key = timepoint_of(op.get("timepoint"), labels)
        if key is None or key not in inside:
            raise WorkbookError(i18n.t("server.trajectory_no_such_timepoint", timepoint=" ".join(str(op.get("timepoint") or "").split()) or "none"))
        return key

    def row_set(gid: str, key: str, change: dict) -> None:
        row = {"quote": "", "note": ""}
        row.update((held.get(gid) or {}).get(key) or {})
        row.update(change)
        # a statement's quote ticked or a passage taken, never both
        if row.get("quote") or not row.get("passage"):
            row.pop("passage", None)
        if not row.get("quote") and not row.get("passage"):
            row.pop("bold", None)
        if not row.get("bold"):
            row.pop("bold", None)
        if row.get("quote") or row.get("note") or row.get("passage"):
            held.setdefault(gid, {})[key] = row
        else:
            (held.get(gid) or {}).pop(key, None)
            if gid in held and not held[gid]:
                held.pop(gid)

    if kind == "states_from_notes":
        said = []
        for gid, r in rows.items():
            found = states_in_note(str((groups.get(gid) or {}).get("note") or ""), labels)
            for key in inside:
                text = found.get(key)
                if not text:
                    continue
                now = r["cells"].get(key, {}).get("state") or ""
                if now == text:
                    continue
                if now:
                    said.append(f"{name}'s '{r['title']}' at {tp_names(labels, key)[0]} has a state already, kept.")
                    continue
                row_set(gid, key, {"note": text[:4000]})
                said.append(f"{name}'s '{r['title']}' at {tp_names(labels, key)[0]}: state from its note.")
        return said
    r = lpet()
    if kind == "domain":
        domain = " ".join(str(op.get("domain") or "").split())
        if len(domain) > 40:
            raise WorkbookError(i18n.t("server.trajectory_domain_long", most=40))
        g = groups.get(r["id"])
        if domain == str(g.get(themes.DOMAIN) or ""):
            return []
        if domain:
            g[themes.DOMAIN] = domain
        else:
            g.pop(themes.DOMAIN, None)
        return [f"{name}'s '{r['title']}' is {domain} now." if domain else f"{name}'s '{r['title']}' has no domain now."]
    key = tp()
    cell = r["cells"].get(key) or {}
    at = tp_names(labels, key)[0]
    stored = (held.get(r["id"]) or {}).get(key) or {}
    if kind == "state":
        text = str(op.get("state") or "").replace("\r\n", "\n").strip()
        if len(text) > 4000:
            raise WorkbookError(i18n.t("server.trajectory_state_long", most=4000))
        if text == (stored.get("note") or ""):
            return []
        row_set(r["id"], key, {"note": text})
        return [f"{name}'s '{r['title']}' at {at}: state " + ("changed." if text else "cleared.")]
    if kind == "quote":
        given = str(op.get("quote") or "").strip()
        if op.get("passage") not in (None, "", {}):
            if given:
                raise WorkbookError(i18n.t("server.trajectory_quote_or_passage"))
            # a passage of the transcript, from this interview or another of the participant's
            taken = passage_from(op.get("passage"), labels, inside, turns, name)
            if not stored.get("quote") and stored.get("passage") == taken:
                return []
            row_set(r["id"], key, {"quote": "", "passage": taken, "bold": []})
            where = ", ".join(w for w in (tp_names(labels, taken["at"])[0], passage_found(taken, turns)["time"]) if w)
            return [f"{name}'s '{r['title']}' at {at}: key quote ticked from the transcript, {where}."]
        # a statement's quote of that interview, the LPET's own or another's, a statement in another LPET or in none
        if given and quote_at((data.get("cases") or {}).get(key) or {}, given) is None:
            raise WorkbookError(i18n.t("server.trajectory_no_such_quote", quote=given, name=name, timepoint=at))
        if given == (stored.get("quote") or "") and not stored.get("passage"):
            return []
        row_set(r["id"], key, {"quote": given, "passage": None, "bold": []})
        return [f"{name}'s '{r['title']}' at {at}: " + ("key quote ticked." if given else "key quote's tick taken off.")]
    # bold, on the quote he ticked or the one standing in, which his bold ticks
    q = cell.get("quote")
    if q is None:
        raise WorkbookError(i18n.t("server.trajectory_bold_no_quote", lpet=r["title"], timepoint=at))
    # the spans are of the words as Trajectories shows them, kept moved back past the marks they lost
    text, cut = quote_cut(q["text"])
    given = op.get("spans") if op.get("spans") is not None else []
    whole = lambda s: (isinstance(s, (list, tuple)) and len(s) == 2
                       and all(isinstance(x, int) and not isinstance(x, bool) for x in s) and 0 <= s[0] < s[1] <= len(text))
    if not isinstance(given, list) or not all(whole(s) for s in given):
        raise WorkbookError(i18n.t("server.trajectory_bold_spans", most=len(text)))
    spans = spans_kept([[s[0] + cut, s[1] + cut] for s in given])
    # a passage he took keeps its place, and a statement's quote, his or the one standing in, is ticked with it
    passage = q.get("source") == "transcript" and bool(cell.get("chosen"))
    same = bool(stored.get("passage")) if passage else (stored.get("quote") or "") == q["key"]
    if spans == (stored.get("bold") or []) and same:
        return []
    if not spans and not stored.get("bold"):
        return []
    row_set(r["id"], key, {"bold": spans} if passage else {"quote": q["key"], "passage": None, "bold": spans})
    return [f"{name}'s '{r['title']}' at {at}: bold in its key quote " + ("changed." if spans else "taken off.")]


def __getattr__(name: str) -> str:
    """The refusals other modules and the checks name as this module's, each read in the run's language when
    asked for (the text layer, 28 October 2026)."""
    said = {
        "NOT_COMPLETE": lambda: i18n.t("exports.pets_not_complete"),
        "NO_PETS": lambda: i18n.t("exports.no_pets_yet"),
        "CHANGED": lambda: i18n.t("exports.changed_since"),
        "NOT_INTERVIEWED": lambda: i18n.t("exports.not_interviewed"),
        "NOTHING": lambda: i18n.t("exports.nothing_under_get"),
        "NOTHING_NO_PETS": lambda: i18n.t("exports.no_pets_nothing_under_get"),
        "NOT_FROM": lambda: i18n.t("exports.not_from_transcript"),
        "NOT_A_GETS_OP": lambda: i18n.t("server.something_gets_screen_does_nothing"),
        "NOT_IN": lambda: i18n.t("server.participant_gets_yet_nothing_came"),
        "GONE": lambda: i18n.t("server.board_longer_gets_file_nothing"),
        "NO_SUBS": lambda: i18n.t("server.every_sub_theme_card_board"),
        "NOT_A_CASE": lambda: i18n.t("server.participant_project_their_colour_changed"),
        "NOT_A_COLOUR": lambda: i18n.t("server.one_participants_colours_nothing_changed"),
        "TAKEN_COLOUR": lambda: i18n.t("server.colour_another_participant_s_nothing"),
    }
    if name in said:
        return said[name]()
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
