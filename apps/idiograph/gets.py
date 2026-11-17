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
                 "discarded": [], "picks": {}, "notes": [], "rows": {}, "history_head": {...}}]}

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

import board_history
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


def load(root: Path, move: bool = True, cited: bool = True) -> dict | None:
    """The GETs file as it sits on disk, or None when there is none yet. One that is there and
    cannot be read is refused, so nothing is ever written over a file that can be recovered.

    Each board is told where its History's chunks are, and a file whose boards still hold their History inside it
    is moved over on this first open when its lock is free and the file is this install's to write (historybuild,
    see `board_history`). With `cited` False each statement keeps its time and its timepoint's label as the file
    keeps them, for a read of the cases' marks alone (`copies_untouched`), which never reads either (lgetsfast)."""
    path = gets_path(root)
    if not path.exists():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        raise WorkbookError(i18n.t("server.could_read_nothing_written", name=path.name))
    if not isinstance(data, dict):
        raise WorkbookError(i18n.t("server.gets_file_nothing_written", name=path.name))
    board_history.place(path, data)
    if move and board_history.embedded(data):
        # the move asks Working together's one writer as a write does: the project's GETs owner at the root, and
        # for a participant's LPETs in their Working folder that participant's writer (review 6)
        guard = None
        if FILE_AT.get() is None:
            guard = (lambda: WRITE_GUARD(Path(root))) if WRITE_GUARD is not None else None
        elif path.parent.name == "Working":
            guard = lambda: themes.guard_of(path)  # noqa: E731
        data = board_history.move_on_open(path, data, lambda d: write_at(path, d),
                                          lambda: board_history.place(path, json.loads(path.read_text(encoding="utf-8"))),
                                          guard=guard)
    if not cited:
        # a case's lines that are not a mapping refused as the reads below refuse them
        for rec in (data.get("cases") or {}).values() if isinstance(data.get("cases"), dict) else []:
            if isinstance(rec, dict):
                (rec.get("lines") or {}).values()
        return data
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
    return write_at(path, data)


def write_at(path: Path, data: dict) -> Path:
    """The file at `path` written as `write` writes it, each board's History to its chunks first (`board_history`)."""
    path = Path(path)
    kept, finish = board_history.out_of(path, data) if isinstance(data, dict) else (data, lambda: None)
    tmp = path.with_name(path.name + ".tmp")
    if isinstance(kept, dict) and themes.plain_json(kept):
        # data that JSON gives back as it is (`themes.plain_json`) copied only where `retime` writes, each line,
        # and written by `json.dumps`, the text the copy through JSON and `render` give, in a fraction of the time
        # (lgetsfast, 16 November 2026)
        text = json.dumps(retime(lines_copied(kept), KEPT_AS), ensure_ascii=False, indent=1)
    else:
        text = themes.render(retime(json.loads(json.dumps(kept)), KEPT_AS) if isinstance(kept, dict) else kept)
    tmp.write_text(text + "\n", encoding="utf-8", newline="\n")
    os.replace(tmp, path)
    note_written(path)
    finish()
    return path


def lines_copied(data: dict) -> dict:
    """The file's data with each case's lines copied, line by line, and everything else shared: what `retime` may
    write to, so it can retime the copy and leave the data given as it was."""
    out = dict(data)
    cases = out.get("cases")
    if isinstance(cases, dict):
        out["cases"] = {case: dict(rec, lines={k: dict(v) if isinstance(v, dict) else v for k, v in rec["lines"].items()})
                        if isinstance(rec, dict) and isinstance(rec.get("lines"), dict) else rec
                        for case, rec in cases.items()}
    return out


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
    the group id, line key or note number, and for a second card of a PET the number after it. A
    statement's second card on an LPETs board (drawsbuild, 17 November 2026) is `<case>/es/<line>/2`,
    its line read without the number, since a line's key, `<sheet>:<row>:<place>`, never holds a slash."""
    case, _, rest = str(key).partition("/")
    head, _, tail = rest.partition("/")
    if head == "es":
        line, _, copy = tail.partition("/")
        return {"case": case, "kind": head, "ident": line, "copy": copy or None}
    if head == "pn":
        return {"case": case, "kind": head, "ident": tail, "copy": None}
    return {"case": case, "kind": "group", "ident": head, "copy": tail or None}


def base_key(key: str) -> str:
    """The key of a card's first card, which a second one, `/2`, extends: a PET's, a sub-theme's or a statement's."""
    k = split_key(key)
    if k["kind"] == "pn" or not k["copy"]:
        return str(key)
    return card_of(k["case"], k["kind"], k["ident"])


def with_copy(key: str, to: str) -> str:
    """`to`, a first card's new key, with the number of `key`'s copy after it, so a second card follows its first."""
    copy = split_key(key)["copy"]
    return f"{to}/{copy}" if copy else to


def cards_of_key(cards, key: str) -> list[str]:
    """A card's key and its second cards' among `cards`, the keys of one PET, sub-theme or statement on a board."""
    return [k for k in cards if k == key or (base_key(k) == key and k != key)]


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


def normal(board: dict, data: dict, hide: bool = True) -> dict:
    """A GETs board as the file holds it, whatever the page sent: the PETs screen's rules, a card
    in one group at most among them, then a PET's or a sub-theme's card keeps no words while its
    case still has it, a statement and a participant note keep theirs, and `rows` holds the GET
    table's rows (see `rows_of`). Read with `hide`, his reasons no LPET draws on a PET leave out each one an LPET
    now draws on (see `why_undrawn`); a writer, or a hash of the board as the file keeps it, reads with `hide`
    false, so the file keeps every reason (drawswordfix2)."""
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
    # his reason no LPET draws on a PET is hidden while one does, and kept in the file (drawswordfix2)
    if hide and kept.get(themes.WHY):
        said = why_undrawn(kept, data)
        if said:
            kept[themes.WHY] = said
        else:
            kept.pop(themes.WHY, None)
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
            if k["copy"]:
                item["copy"] = k["copy"]
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
            "why": kept.get(themes.WHY) or {},
            "stickies": kept.get("notes") or [], "rows": kept["rows"], "history": themes.history_list(shown),
            "history_away": themes.history_away(shown), "sheets": [], "quotes": {},
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
    held_was = normal(was, data, hide=False)
    for key in ("ai",) + themes.FROM_BEFORE:
        if key not in version and held_was.get(key):
            kept[key] = held_was[key]
    # his reasons a PET is drawn on by no LPET are the file's, written by their own operation alone (drawsword), so a
    # save keeps them for each card still on the board, whatever the page sent, one whose PET an LPET now draws on
    # too, hidden on every read, so an undo of the move shows it again (drawswordfix2)
    kept.pop(themes.WHY, None)
    said = themes.why_kept(held_was.get(themes.WHY), kept["cards"])
    if said:
        kept[themes.WHY] = said
    # a board an agent made is marked edited by his first save that changes it
    if kept.get("made"):
        kept["made"] = themes.edited_mark(kept["made"], kept, when, kept.get("changed"))
    made = None
    if revision == "auto" and disk is not None:
        made = themes.auto_revision(was, at=when)
    themes.carry_history(was, kept)
    boards[at] = kept
    data["boards"] = boards
    data["current"] = bid
    write(root, _file(data, when))
    out = {"saved": True, "updated": when, "version": themes.summary(kept)}
    # on LPETs his reasons as a read shows them, one hidden where this save has an LPET draw on its PET
    if in_lpets():
        out["why"] = why_undrawn(kept, data)
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
        copy = json.loads(json.dumps(normal(target, data, hide=False)))
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


def followed(state: dict, data: dict) -> dict:
    """A copy of a revision's state with its statement cards following their words to the participant's copy as it
    is now, as a PETs revision's do when it is shown or restored (`themes.follow`, `themes.brought_up`, historyfix2):
    a card stays while its key still holds its words, and otherwise takes an unclaimed line of theirs with its words,
    the nearest first, its GETs' members, the bin and the rest with it. A trim, a passage written or a rekey moves
    the GETs revisions' keys with the board when their History is here; one made while it was not leaves them as
    they were, and they follow here. The table's ticked quotes are no part of a revision (`themes.STATE_KEYS` holds no
    `rows`, and Restore leaves the table as it stands): they live on the board alone, which those followers always
    move, so none is followed here (historyfix3, review 4). Nothing is written."""
    out = json.loads(json.dumps(state))
    cards = out.get("cards") if isinstance(out.get("cards"), dict) else {}
    for case, rec in ((data or {}).get("cases") or {}).items():
        lines = rec.get("lines") if isinstance(rec, dict) and isinstance(rec.get("lines"), dict) else {}
        if not lines:
            continue
        held = {split_key(k)["ident"]: c for k, c in cards.items()
                if split_key(k)["kind"] == "es" and split_key(k)["case"] == case and isinstance(c, dict)}
        if all(isinstance(lines.get(i), dict) and themes.words(lines[i].get("text")) == themes.words(c.get("text"))
               for i, c in held.items()):
            # every card's key still holds its words: nothing to follow
            continue
        live = []
        for ident, line in lines.items():
            if not isinstance(line, dict):
                continue
            sheet, row, n = themes.split_card_key(ident)
            if row is None or n is None:
                continue
            live.append({"key": ident, "sheet": sheet, "row": row, "line": n, "text": str(line.get("text") or "")})
        pseudo = {"cards": {i: {"x": 0, "y": 0, "text": str(c.get("text") or "")} for i, c in held.items()}}
        keymap: dict = {}
        themes.follow(pseudo, live, None, keys=keymap)
        cmap = {k: v for k, v in keymap.items() if k != v and k in held}
        if cmap:
            board_remapped(out, case, cmap, {})
    return out


def view_state(board: dict, data: dict) -> dict:
    kept = normal(board, data)
    return {"cards": cards_shown(kept, data), "groups": kept["groups"], "discarded": kept["discarded"],
            "picks": {}, "discard_reasons": (kept.get("ai") or {}).get("discarded") or {},
            "why": kept.get(themes.WHY) or {}, "stickies": kept.get("notes") or []}


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
    themes.revision_checked(revision, body.get("hash"))
    if op == "view":
        return dict(view_state(followed(revision["state"], data), data), op=op, revision=themes.revision_summary(revision),
                    board=themes.summary(normal(board, data), board))
    if op == "revision":
        made = themes.add_revision(board, name=str(body.get("name") or "")[:200], at=when)
        extra = {"revision": themes.revision_summary(made)}
    else:
        made = themes.add_revision(board, name=themes.revision_name("before_restoring", when_at=revision["at"]),
                                   at=when)
        restored = json.loads(json.dumps(themes.state_of(themes.normalise(followed(revision["state"], data)))))
        for key in ("notes", "ai", "quoted", "cut", themes.WHY):
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
                for each in cards_of_key(board.get("cards") or {}, card_of(case, "es", key)):
                    card = board["cards"][each]
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


def held_of(root: Path, workbook: Path, books: list[dict] | None = None,
            move: bool = True, cited: bool = True) -> tuple[dict | None, list[dict]]:
    """The file in scope as it sits on disk, and each case of it that is the participant's at `workbook`, as a
    survey's entry: on GETs and LGETs the one case whose copy names the workbook, and on LPETs each of the
    participant's timepoints that is in, from `books`, with its timepoint and the label it is cited with. None and
    none with no file. With `move` False the file is read without moving its boards' History out of it (see `load`),
    as every dry run and every read alone reads it, so they write nothing (timefix, 16 November 2026)."""
    if not gets_path(root).exists():
        return None, []
    data = load(root, move=move, cited=cited)
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
        data, entries = held_of(root, workbook, books, move=False, cited=False)
    except WorkbookError:
        return {}
    held = (data or {}).get("cases") or {}
    return {e["case"]: bool(at_timepoint(e, untouched, Path(workbook), held[e["case"]])) for e in entries}


def quotes_carried(lines: dict, key: str, old: str, new: str, carried: dict | None = None) -> dict[str, list[str]]:
    """A statement's own quote rewritten in its place, `old` to `new`, carried to a copy's lines (cardsync, 13 November
    2026): every line of the copy on the statement's row keeps the row's quotes by place (see `row_places`), and each
    whose place held the old quote, its words as `themes.quote_words` reads them, takes the new as the workbook holds
    it. A line holding another quote there, a change waiting, keeps it. `carried` is the quotes the write's other
    statements have carried already, by line, which this one builds on. Answers each line that changes by its key
    with its quotes after. Nothing is written."""
    sheet, row, place = themes.split_card_key(key)
    if row is None or place is None:
        return {}
    out = {}
    for lkey, line in lines.items():
        if not isinstance(line, dict) or line.get("sheet") != sheet or line.get("row") != row:
            continue
        was = [str(q or "") for q in (carried or {}).get(lkey, line.get("quotes") or [])]
        places = was + [""] * (place + 1 - len(was))
        if themes.quote_words(places[place]) != themes.quote_words(old) or places[place] == new:
            continue
        places[place] = str(new or "")
        while places and not places[-1]:
            places.pop()
        if places != was:
            out[lkey] = places
    return out


def _starts(text: str, part: str) -> list[int]:
    """Every place `part` begins in `text`, overlapping ones too."""
    out, at = [], text.find(part) if part else -1
    while at >= 0:
        out.append(at)
        at = text.find(part, at + 1)
    return out


def bold_followed(old: str, new: str, spans) -> tuple[list[list[int]], int, int]:
    """A key quote's bold carried to the quote worded anew (quotefollow, 13 November 2026, Adam: "keep it where the
    words survive"). His bold is kept as character positions against the quote as the copy holds it, so a requote
    leaves each span on the wrong words. Each span moves to the same words in `new`: the words exactly as they were
    first, and failing that the same letters and figures, case and punctuation set aside, the nearest place to where
    they stood and clear of the span before. A span whose words are gone from `new` is dropped, never put on other
    words. Answers the spans after, the number that moved to another place and the number dropped."""
    old, new = str(old or ""), str(new or "")
    held = spans_kept(spans)
    if old == new:
        return held, 0, 0
    # the letters and figures of the new quote, lower-cased, each with its place
    flat = [(ch.casefold(), i) for i, ch in enumerate(new) if ch.isalnum()]
    flat_text = "".join(ch for ch, _ in flat)
    out: list[list[int]] = []
    moved = dropped = 0
    for a, b in held:
        words = old[a:b]
        found = None
        if words.strip():
            marks = [m for m in _starts(new, words) if not out or m >= out[-1][1]]
            if marks:
                at = min(marks, key=lambda m: (abs(m - a), m))
                found = [at, at + len(words)]
            else:
                bare = "".join(ch.casefold() for ch in words if ch.isalnum())
                marks = [m for m in _starts(flat_text, bare) if not out or flat[m][1] >= out[-1][1]] if bare else []
                if marks:
                    before = sum(1 for ch in old[:a] if ch.isalnum())
                    at = min(marks, key=lambda m: (abs(m - before), m))
                    found = [flat[at][1], flat[at + len(bare) - 1][1] + 1]
        if found is None:
            dropped += 1
            continue
        if found != [a, b]:
            moved += 1
        out.append(found)
    return spans_kept(out), moved, dropped


def bold_changes(data: dict, case: str, places: dict[str, tuple[str, str]]) -> list[dict]:
    """The key quotes whose bold a requote of a copy's quotes moves (quotefollow, 13 November 2026): `places` holds, by
    the quote's key, `<sheet>:<row>:<place>`, the quote as the copy held it and as it will hold it. Every board of the
    file that ticked such a quote for `case` as a row's key quote, with bold in it, is one answer: its `board` id and
    name, the LPET (`gid`, `lpet` its title), `case`, the quote's `key`, the spans `after`, and how many `moved` and
    were `dropped`. A passage of the transcript is never marked by a requote. Nothing is written."""
    out = []
    for board in boards_of(data):
        rows = board.get("rows") if isinstance(board.get("rows"), dict) else {}
        titles = {str(g.get("id")): str(g.get("label") or "") for g in board.get("groups") or [] if isinstance(g, dict)}
        for gid, cases in rows.items():
            row = cases.get(case) if isinstance(cases, dict) else None
            if not isinstance(row, dict) or not row.get("bold"):
                continue
            key = " ".join(str(row.get("quote") or "").split())
            if key not in places:
                continue
            after, moved, dropped = bold_followed(places[key][0], places[key][1], row["bold"])
            if after != spans_kept(row["bold"]):
                out.append({"board": str(board.get("id")), "name": str(board.get("name") or FIRST_NAME), "gid": str(gid),
                            "lpet": titles.get(str(gid), ""), "case": case, "key": key, "after": after,
                            "moved": moved, "dropped": dropped})
    return out


def bold_set(data: dict, changes: list[dict]) -> None:
    """The bold `bold_changes` found, written to the boards' rows, a row left with none keeping no bold."""
    for c in changes:
        for board in boards_of(data):
            if str(board.get("id")) != c["board"]:
                continue
            row = ((board.get("rows") or {}).get(c["gid"]) or {}).get(c["case"])
            if not isinstance(row, dict):
                continue
            if c["after"]:
                row["bold"] = c["after"]
            else:
                row.pop("bold", None)


def bold_report(changes: list[dict], entries: list[dict]) -> list[dict]:
    """What `bold_changes` found as a report: each key quote's cell by the participant's case, its timepoint's label
    where the copy is by timepoint, the LPET, its board and the quote's key, with how many spans moved and were
    dropped, never a word of the quote."""
    cite = {e["case"]: e.get("cite") or "" for e in entries}
    return [{"case": c["case"], "timepoint": cite.get(c["case"]) or None, "board": c["board"], "board_name": c["name"],
             "lpet": c["gid"], "title": c["lpet"], "key": c["key"], "moved": c["moved"], "dropped": c["dropped"]}
            for c in changes]


def bold_places(lines: dict, requoted: dict[str, list[str]]) -> dict[str, tuple[str, str]]:
    """What a copy's quotes at each place were and will be, for `requoted` (each line's key with its quotes after): by
    the quote's key, the first line of the row to change it."""
    out: dict[str, tuple[str, str]] = {}
    for lkey, after in requoted.items():
        line = lines.get(lkey) or {}
        held = [str(q or "") for q in line.get("quotes") or []]
        for i in range(max(len(held), len(after))):
            was = held[i] if i < len(held) else ""
            now = str(after[i] or "") if i < len(after) else ""
            if was != now:
                out.setdefault(f"{line.get('sheet')}:{line.get('row')}:{i}", (was, now))
    return out


def statements_followed(root: Path, workbook: Path, words: dict, before: dict, books: list[dict] | None = None,
                        dry: bool = False, changed: dict | None = None, history: str = "",
                        said: dict | None = None, quotes: dict | None = None) -> dict:
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

    `quotes`, each statement by its key with its own quote before and after, carries a quote rewritten in its place
    the same way (cardsync, 13 November 2026: a requote had reached the copies' wording alone, so the LPETs and the
    key quotes Trajectories reads from them kept the old quote): every line of the copy on its row takes the new
    quote at its place where it held the old (see `quotes_carried`), and a board with a card of the statement is
    kept and marked as one that took words is.

    Answers nothing when nothing took words or a quote and no board kept a line, else `cases`, the cases that took
    either, `words` and `quotes`, the statements' keys that took each, `boards`, each board with a card of one, its
    id, name and the cards' keys, `versions`, every board as the board menu lists it after the write, for the page's
    next save, and `histories`, each board that kept a line with its revisions as the History tab lists them."""
    data, entries = held_of(root, workbook, books, move=not dry)
    if data is None or not entries:
        return {}
    held = data["cases"]
    took: dict[str, list[str]] = {}
    # each line of a copy that takes a quote, with its quotes after, and the statements whose quote it is
    requoted: dict[str, dict[str, list[str]]] = {}
    quoted: dict[str, list[str]] = {}
    for e in entries:
        lines = held[e["case"]].get("lines") if isinstance(held[e["case"]].get("lines"), dict) else {}
        for key, (old, new) in words.items():
            line = lines.get(key)
            if (isinstance(line, dict) and themes.words(old) != themes.words(new)
                    and themes.words(line.get("text")) == themes.words(old)):
                took.setdefault(e["case"], []).append(key)
        for key, (old, new) in (quotes or {}).items():
            carried = quotes_carried(lines, key, old, new, requoted.get(e["case"]))
            if carried:
                requoted.setdefault(e["case"], {}).update(carried)
                quoted.setdefault(e["case"], []).append(key)
    # the statements whose card a board keeps marked for the write: those that took words, and those that took a quote
    marks = {case: list(dict.fromkeys(took.get(case, []) + quoted.get(case, [])))
             for case in held if case in took or case in quoted}
    # his bold in a key quote, moved to the same words in the quote worded anew (quotefollow, 13 November 2026)
    bold = [c for case, carried in requoted.items()
            for c in bold_changes(data, case, bold_places(held[case].get("lines") or {}, carried))]
    boards = []
    for board in boards_of(data):
        cards = board.get("cards") if isinstance(board.get("cards"), dict) else {}
        keys = [each for case, keys in marks.items() for key in keys
                for each in cards_of_key(cards, card_of(case, "es", key)) if isinstance(cards.get(each), dict)]
        if keys or any(c["board"] == str(board.get("id")) for c in bold):
            boards.append({"board": str(board.get("id")), "name": str(board.get("name") or FIRST_NAME), "keys": keys})
    out = {"cases": [c for c in held if c in marks], "boards": boards,
           "words": list(dict.fromkeys(k for keys in took.values() for k in keys)),
           "quotes": list(dict.fromkeys(k for keys in quoted.values() for k in keys))}
    if bold:
        out["bold"] = bold_report(bold, entries)
    if dry:
        return out if marks else {}
    when = themes.now_iso()
    # his own edit's line on each board that shows the statement, the board as it stood before the words
    noted = noted_on(data, entries, said or {}, when)
    marked = {b["board"] for b in boards} if changed else set()
    for board in boards_of(data):
        if str(board.get("id")) in marked:
            themes.kept_revision(board, name=history, at=when)
    for case, keys in took.items():
        rec = held[case]
        for key in keys:
            rec["lines"][key]["text"] = " ".join(str(words[key][1]).split())
            for board in boards_of(data):
                for each in cards_of_key(board.get("cards") or {}, card_of(case, "es", key)):
                    card = board["cards"][each]
                    if isinstance(card, dict) and "text" in card:
                        card["text"] = rec["lines"][key]["text"]
        rec["hash"] = snap_hash(rec)
    for case, carried in requoted.items():
        rec = held[case]
        for lkey, places in carried.items():
            rec["lines"][lkey]["quotes"] = places
        # a statement whose own quote it took takes the span the quote now has, as a fresh read gives it, so a
        # quote reworded to take in the passages beside its own, or no longer, never marks it changed (spanfollow)
        for key in quoted.get(case) or []:
            spans_followed(rec, Path(workbook), key, (quotes or {}).get(key, ("", ""))[1])
        rec["hash"] = snap_hash(rec)
    bold_set(data, bold)
    # a copy with nothing else waiting keeps its files' new times (see `untouched`), read afresh to be sure
    kept = kept_in(held, entries, before)
    for board in boards_of(data):
        if str(board.get("id")) in marked:
            board["updated"] = when
            board["changed"] = dict(changed, at=when)
            board["changed"]["hash"] = themes.state_hash(themes.made_state(normal(board, data, hide=False)))
    if not marks and not kept and not noted:
        return {}
    data["updated"] = when
    write(root, data)
    if not marks and not noted:
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
                themes.kept_revision(board, name=line, at=when)
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


# ------------------------------------------------------- copies brought in line (cardsync)
# (13 November 2026, from the GRAVITY session: a write that went astray left thirty statements' cards and a
# participant's LPETs on the old wording and the old quotes, the workbook holding the new, and nothing brought them
# back.) `copies_refreshed` reads every copy a file keeps of a participant against the workbook, statement by
# statement, and brings back each that differs, its dry run naming the keys alone.

def workbook_lines(workbook: Path) -> dict[str, dict]:
    """Every statement of a participant's workbook at every timepoint, by its key, `Initial:12:0`, with its words and
    its row's quotes by place, as a copy keeps them (see `snapshot` and `row_places`). Read alone."""
    workbook = Path(workbook)
    out: dict[str, dict] = {}
    for n in sorted({1} | set(themes.placed_sheets(workbook).values())):
        with themes.scoped(n):
            read = themes.read_cards(workbook)
        for c in read["cards"]:
            row = (read["quotes"].get(themes.row_key(c["sheet"], c["row"])) or {}).get("quotes") or []
            out[c["key"]] = {"text": c["text"], "quotes": row_places(row)}
    return out


def copies_refreshed(root: Path, workbook: Path, truth: dict, books: list[dict] | None = None, dry: bool = False,
                     changed: dict | None = None, history: str = "") -> dict:
    """The copy the file in scope keeps of a participant brought in line with their workbook (cardsync, 13 November
    2026): the project's GETs, inside `lgets` its LGETs, or inside `lpets` the participant's LPETs, each of their
    timepoints in it from `books`. `truth` is the workbook's statements by key (see `workbook_lines`). Each line of the
    copy whose words read otherwise takes the workbook's, each whose quotes do takes the row's quotes as the workbook
    holds them, and each board's card of a statement takes its words, whether or not a change waits to be taken: the
    copy keeps no wording of his own, so the workbook wins, as an edit's words reach a copy (see
    `statements_followed`). A line or a card whose statement is no longer in the workbook is listed under `missing`
    and left as it is. Each board with a card that changes keeps the board as it stood first in its History, under
    `history`, and with `changed`, an agent's mark, is stamped and marked changed in a conversation. A copy that then
    reads as its files do keeps their times, so it is not marked Changed since it came in (see `kept_in`). The file is
    written once, and with `dry` not at all.

    Answers nothing when the file has no copy of the participant, else `statements`, the keys whose words change,
    `quotes`, those whose quotes change, `missing`, those no longer in the workbook, and `boards`, each board with a
    card that changes or is missing, its id, name, `cards` and `missing`, card keys alone, never the words."""
    data, entries = held_of(root, workbook, books, move=not dry)
    if data is None or not entries:
        return {}
    held = data["cases"]
    mine = {e["case"] for e in entries}
    statements, quotes, missing = [], [], []
    fix: dict[str, dict[str, dict]] = {}
    for e in entries:
        lines = held[e["case"]].get("lines") if isinstance(held[e["case"]].get("lines"), dict) else {}
        for key, line in lines.items():
            if not isinstance(line, dict):
                continue
            now = truth.get(key)
            if now is None:
                missing.append(key)
                continue
            if themes.words(line.get("text")) != themes.words(now["text"]):
                statements.append(key)
                fix.setdefault(e["case"], {}).setdefault(key, {})["text"] = now["text"]
            if [str(q or "") for q in line.get("quotes") or []] != now["quotes"]:
                quotes.append(key)
                fix.setdefault(e["case"], {}).setdefault(key, {})["quotes"] = list(now["quotes"])
    boards = []
    for board in boards_of(data):
        cards = board.get("cards") if isinstance(board.get("cards"), dict) else {}
        took, gone = [], []
        for ck, card in cards.items():
            k = split_key(ck)
            if k["kind"] != "es" or k["case"] not in mine or not isinstance(card, dict) or "text" not in card:
                continue
            now = truth.get(k["ident"])
            if now is None:
                gone.append(ck)
            elif themes.words(card.get("text")) != themes.words(now["text"]):
                took.append(ck)
        if took or gone:
            boards.append({"board": str(board.get("id")), "name": str(board.get("name") or FIRST_NAME),
                           "cards": took, "missing": gone})
    # his bold in a key quote, moved to the same words in the quote the copy takes (quotefollow, 13 November 2026)
    bold = []
    for case, lines in fix.items():
        carried = {key: took["quotes"] for key, took in lines.items() if "quotes" in took}
        bold += bold_changes(data, case, bold_places(held[case].get("lines") or {}, carried))
    out = {"statements": statements, "quotes": quotes, "missing": missing, "boards": boards}
    if bold:
        out["bold"] = bold_report(bold, entries)
    if dry or not (fix or any(b["cards"] for b in boards)):
        return out
    when = themes.now_iso()
    by_id = {b["board"]: b for b in boards if b["cards"]}
    touched = set(by_id) | {c["board"] for c in bold}
    for board in boards_of(data):
        said = by_id.get(str(board.get("id")))
        if str(board.get("id")) not in touched:
            continue
        themes.kept_revision(board, name=history, at=when)
        for ck in (said or {}).get("cards") or []:
            board["cards"][ck]["text"] = truth[split_key(ck)["ident"]]["text"]
    for case, lines in fix.items():
        rec = held[case]
        for key, took in lines.items():
            rec["lines"][key].update(took)
        rec["hash"] = snap_hash(rec)
    bold_set(data, bold)
    # a copy that now reads as its files do keeps their times, never marked Changed since it came in for this
    kept_in(held, entries, {case: True for case in fix})
    for board in boards_of(data):
        if str(board.get("id")) in touched:
            board["updated"] = when
            if changed:
                board["changed"] = dict(changed, at=when)
                board["changed"]["hash"] = themes.state_hash(themes.made_state(normal(board, data, hide=False)))
    data["updated"] = when
    write(root, data)
    return out


# ------------------------------------------------------- keys that follow the rows (lpetkeys)
# (13 November 2026, Adam by dialog, from the Ayahuasca IPA project: a passage split into two rows by `turn assign`
# moved the PETs boards' keys with the rows and left a participant's LPETs on the old row numbers, one row off from
# the split down, and the removed statements' copies stayed on the LPETs.) A copy keeps a statement by its key,
# `<sheet>:<row>:<line>`, in four places: the copy's `lines`, each PET's `statements` and `picks` in the copy, each
# board's cards `<case>/es/<key>` with every place a board names a card, and the table's rows, a ticked quote by its
# key and a passage of the transcript by its turn, `<sheet>:<row>`. `copy_remapped` and `board_remapped` move all of
# them by one map, so every change below moves them the same way: `rows_moved` with the rows, `passage_followed`
# with a passage's statements, `copies_rekeyed` to repair keys a row op left behind, and `copies_pruned` to take off
# copies whose statement is no longer in the workbook.

# how much of a removed statement's words a statement must hold to be the one it was merged into
MERGED = 0.6
# the copies a trim cut, kept in the file until the trim is undone, as a PETs board keeps its cut cards
ROWS_CUT = "rows_cut"


def copy_remapped(rec: dict, cmap: dict, qmap: dict, merged=()) -> list[str]:
    """A case's copy with its statements' keys moved by `cmap`, each key to its new key or None for a statement
    gone, and its quotes' keys by `qmap` the same way: its lines, each with its sheet and row, the statement it is
    stacked under, and each PET's statements and picks, a key that meets another once. A key of `merged` was
    merged into the one it maps to: its line goes, the line it joined standing, and the PETs that held it hold
    that one. Changed in place, and answers the lines' keys that moved or went."""
    lines = rec.get("lines") if isinstance(rec.get("lines"), dict) else {}
    out, said = {}, []
    # a line merged away comes last, so the line it joined keeps its place, and takes it only where the copy
    # held no line of that statement
    for key, line in sorted(lines.items(), key=lambda kv: kv[0] in merged):
        to = cmap.get(key, key)
        if to != key:
            said.append(key)
        if to is None or to in out or not isinstance(line, dict):
            continue
        line = dict(line)
        if to != key:
            sheet, row, _ = themes.split_card_key(to)
            line["sheet"], line["row"] = sheet, row
        if line.get("stacked"):
            top = cmap.get(line["stacked"], line["stacked"])
            if top is None or top == to:
                line.pop("stacked", None)
            else:
                line["stacked"] = top
        out[to] = line
    rec["lines"] = {k: out[k] for k in sorted(out, key=themes._order)}

    def moved(keys, by):
        kept = []
        for k in keys or []:
            to = by.get(k, k)
            if to is not None and to not in kept:
                kept.append(to)
        return kept

    for pet in rec.get("pets") or []:
        if isinstance(pet, dict):
            pet["statements"] = moved(pet.get("statements"), cmap)
            pet["picks"] = moved(pet.get("picks"), qmap)
    return said


def board_remapped(board: dict, case: str, cmap: dict, qmap: dict, turns=None, merged=()) -> list[str]:
    """A board, or a revision's state, with the statement cards of `case` moved by `cmap` (see `copy_remapped`)
    everywhere it names them: its cards, its groups' members, the bin, the stacks, Not the same, the AI's reasons
    and the picks, a card that meets another once, a card of `merged` giving way to the card of the statement it
    joined. The table's rows of the case move with them, a ticked quote by `qmap` and a passage's turn by `turns`,
    a row key to its new row key or None, a quote or a passage gone leaving the row its note. Changed in place,
    and answers the cards' keys that moved or went."""
    def card(k):
        if not isinstance(k, str):
            return k
        s = split_key(k)
        if s["kind"] != "es" or s["case"] != case or s["ident"] not in cmap:
            return k
        to = cmap[s["ident"]]
        return None if to is None else with_copy(k, card_of(case, "es", to))

    def keys(seq):
        out = []
        for k in seq or []:
            to = card(k)
            if to is not None and to not in out:
                out.append(to)
        return out

    said = []
    cards = board.get("cards")
    if isinstance(cards, dict):
        out = {}
        late = {card_of(case, "es", k) for k in merged}
        for k, c in sorted(cards.items(), key=lambda kc: base_key(kc[0]) in late):
            to = card(k)
            if to != k:
                said.append(k)
            if to is not None and to not in out:
                out[to] = c
        board["cards"] = {k: out[k] for k in sorted(out, key=lambda k: list(cards).index(k) if k in cards else len(cards))}
    for g in board.get("groups") or []:
        if isinstance(g, dict):
            g["members"] = keys(g.get("members"))
    if isinstance(board.get("discarded"), list):
        board["discarded"] = keys(board["discarded"])
    if isinstance(board.get("stacks"), dict):
        stacks = {}
        for top, under in board["stacks"].items():
            to = card(top)
            if to is not None:
                stacks.setdefault(to, [])
                stacks[to] += [k for k in keys(under) if k != to and k not in stacks[to]]
        board["stacks"] = {t: ks for t, ks in stacks.items() if ks}
    if isinstance(board.get("not_same"), list):
        board["not_same"] = [[card(a), card(b)] for a, b in board["not_same"]
                             if card(a) is not None and card(b) is not None and card(a) != card(b)]
    if isinstance((board.get("ai") or {}).get("discarded"), dict):
        board["ai"]["discarded"] = {card(k): why for k, why in board["ai"]["discarded"].items() if card(k) is not None}
    # and his reason a card is drawn on by no LPET goes with its card (drawsword)
    if isinstance(board.get(themes.WHY), dict):
        board[themes.WHY] = {card(k): why for k, why in board[themes.WHY].items() if card(k) is not None}
    if isinstance(board.get("picks"), dict):
        board["picks"] = {g: keys(chosen) for g, chosen in board["picks"].items()}
    rows = board.get("rows") if isinstance(board.get("rows"), dict) else {}
    for cases in rows.values():
        row = cases.get(case) if isinstance(cases, dict) else None
        if not isinstance(row, dict):
            continue
        if row.get("quote") in qmap:
            to = qmap[row["quote"]]
            if to is None:
                row.pop("quote", None)
                row.pop("bold", None)
            else:
                row["quote"] = to
        passage = row.get("passage") if isinstance(row.get("passage"), dict) else None
        if passage and turns is not None and passage.get("turn"):
            to = turns(str(passage["turn"]))
            if to is None:
                row.pop("passage", None)
                row.pop("bold", None)
            elif to != passage["turn"]:
                passage["turn"] = to
    return said


def case_keys(data: dict, case: str, history: bool = True) -> tuple[set, set]:
    """Every statement key and every quote key the file holds of a case, on its copy, its boards and, with `history`, their
    revisions, so one map moves them all."""
    rec = (data.get("cases") or {}).get(case) or {}
    statements = set(rec.get("lines") or {})
    quotes = set()
    for pet in rec.get("pets") or []:
        statements |= set((pet or {}).get("statements") or [])
        quotes |= set((pet or {}).get("picks") or [])
    for board in boards_of(data):
        # a History not all here gives none, so a follower still moves the copy and the boards (review 2, 5)
        for state in [board] + ([r.get("state") for r in themes.history_known(board) if isinstance(r, dict)]
                                if history else []):
            if not isinstance(state, dict):
                continue
            for k in state.get("cards") or {}:
                s = split_key(k)
                if s["kind"] == "es" and s["case"] == case:
                    statements.add(s["ident"])
        for cases in (board.get("rows") or {}).values():
            row = (cases or {}).get(case) if isinstance(cases, dict) else None
            if isinstance(row, dict) and row.get("quote"):
                quotes.add(str(row["quote"]))
    return statements, quotes


def remap_case(data: dict, case: str, cmap: dict, qmap: dict, turns=None, merged=(), history: bool = True) -> dict:
    """One case's keys moved by `cmap` and `qmap` across the file: its copy, every board and, with `history`,
    every revision of each, its hash following. Answers the copy's lines and each board's cards that moved or
    went, the boards by id."""
    rec = data["cases"][case]
    lines = copy_remapped(rec, cmap, qmap, merged)
    boards = {}
    for board in boards_of(data):
        said = board_remapped(board, case, cmap, qmap, turns, merged)
        if said:
            boards[str(board.get("id"))] = said
        # a board whose History is not all here is remapped alone, its revisions brought up to date when restored
        for revision in (board_history.attached(board) or []) if history else []:
            if isinstance(revision, dict) and isinstance(revision.get("state"), dict):
                board_remapped(revision["state"], case, cmap, qmap, turns, merged)
    rec["hash"] = snap_hash(rec)
    return {"lines": lines, "boards": boards}


def rows_moved(root: Path, workbook: Path, mapper, books: list[dict] | None = None, cut: str | None = None,
               back: str | None = None, before: dict | None = None) -> list[str]:
    """The copy the file in scope keeps of a participant moved with rows their workbook has just moved (lpetkeys,
    13 November 2026), as a PETs board moves (see `themes.rekey`): the project's GETs, inside `lgets` its LGETs, or
    inside `lpets` the participant's LPETs, each of their timepoints from `books`. `mapper` takes a row key,
    `Initial:12`, to the row it moves to, or None for a row cut, as the progress file was moved. Every key of the
    copy moves with its row, the copy's lines, its PETs' statements and picks, every board's cards and the table's
    quotes and passages, and every revision in each board's History, rows merged into one keeping their lines
    after the first row's (see `themes._row_map`). A trim's cut rows, `cut` its id, go aside in the file under
    `rows_cut`, and come back when the trim is undone, `back`. A copy that stood as its files did, `before` (see
    `copies_untouched`), keeps their new times when it reads as they now do. Written once, only when a key moved.
    Answers the keys that moved, the copy's and the cards'."""
    data, entries = held_of(root, workbook, books)
    if data is None or not entries:
        return []
    held = data["cases"]
    was = json.dumps(data, sort_keys=True, ensure_ascii=False)
    aside = [r for r in data.get(ROWS_CUT) or [] if isinstance(r, dict)]
    said: list[str] = []
    for e in entries:
        case = e["case"]
        statements, quotes = case_keys(data, case)
        cmap = {k: v for k, v in themes._row_map(statements, mapper).items() if v != k}
        qmap = {k: v for k, v in themes._row_map(quotes, mapper).items() if v != k}
        if cut and any(v is None for v in cmap.values()):
            aside.append(cut_aside(data, case, {k for k, v in cmap.items() if v is None}, cut))
        if cmap or qmap:
            done = remap_case(data, case, cmap, qmap, turns=mapper)
            said += done["lines"] + [k for keys in done["boards"].values() for k in keys]
        if back:
            for record in [r for r in aside if r.get("trim") == back and r.get("case") == case]:
                put_back_cut(data, record)
                aside.remove(record)
    if aside:
        data[ROWS_CUT] = aside
    else:
        data.pop(ROWS_CUT, None)
    if json.dumps(data, sort_keys=True, ensure_ascii=False) == was:
        return []
    kept_in(held, entries, before or {})
    data["updated"] = themes.now_iso()
    write(root, data)
    return list(dict.fromkeys(said))


def cut_aside(data: dict, case: str, gone: set, trim: str) -> dict:
    """What a trim cuts of a case's copy, kept to put back: the lines, the PETs that held them, and each board's
    cards of them with the groups and the bin that held them."""
    rec = data["cases"][case]
    record = {"trim": str(trim), "case": case,
              "lines": {k: v for k, v in (rec.get("lines") or {}).items() if k in gone},
              "pets": {p["id"]: [k for k in p.get("statements") or [] if k in gone]
                       for p in rec.get("pets") or [] if isinstance(p, dict) and set(p.get("statements") or []) & gone},
              "boards": {}}
    firsts = {card_of(case, "es", k) for k in gone}
    for board in boards_of(data):
        keys = {k for k in board.get("cards") or {} if base_key(k) in firsts}
        cards = {k: c for k, c in (board.get("cards") or {}).items() if k in keys}
        if cards:
            record["boards"][str(board.get("id"))] = {
                "cards": cards, "discarded": [k for k in board.get("discarded") or [] if k in keys],
                "members": {g["id"]: [m for m in g.get("members") or [] if m in keys]
                            for g in board.get("groups") or [] if set(g.get("members") or []) & keys}}
    return record


def put_back_cut(data: dict, record: dict) -> None:
    """A trim's cut copies put back as it is undone (see `cut_aside`), into the PETs, groups and bins still
    there, a key held again since left as it stands."""
    rec = data["cases"].get(record.get("case"))
    if not isinstance(rec, dict):
        return
    lines = rec.setdefault("lines", {})
    for k, line in (record.get("lines") or {}).items():
        lines.setdefault(k, line)
    rec["lines"] = {k: lines[k] for k in sorted(lines, key=themes._order)}
    pets = {p["id"]: p for p in rec.get("pets") or [] if isinstance(p, dict)}
    for pid, keys in (record.get("pets") or {}).items():
        if pid in pets:
            pets[pid]["statements"] = list(dict.fromkeys(list(pets[pid].get("statements") or []) + keys))
    for board in boards_of(data):
        kept = (record.get("boards") or {}).get(str(board.get("id")))
        if not kept:
            continue
        cards = board.setdefault("cards", {})
        for k, c in kept["cards"].items():
            cards.setdefault(k, c)
        groups = {g["id"]: g for g in board.get("groups") or [] if isinstance(g, dict)}
        for gid, keys in (kept.get("members") or {}).items():
            if gid in groups:
                groups[gid]["members"] = list(dict.fromkeys(list(groups[gid].get("members") or []) + keys))
        board["discarded"] = list(dict.fromkeys(list(board.get("discarded") or []) + kept.get("discarded", [])))
    rec["hash"] = snap_hash(rec)


def merged_into(old: list[str], new: list[str], lines: dict, i: int) -> int | None:
    """The statement a removed one was merged into by a write, `lines` each old statement's new place (see
    `themes.passage_lines`): a new statement that another old one became, reworded, holding MERGED or more of the
    removed one's words, the most first. None when no statement holds them, a statement removed outright."""
    import difflib
    said = themes.words(old[i]).lower() if i < len(old) else ""
    if not said:
        return None
    became = {j: k for k, j in lines.items() if j is not None}
    best = None
    for j, text in enumerate(new):
        if j not in became:
            continue
        now = themes.words(text).lower()
        if themes.words(old[became[j]]).lower() == now:
            continue
        found = difflib.SequenceMatcher(None, said, now, autojunk=False).get_matching_blocks()
        share = sum(b.size for b in found) / len(said)
        if share >= MERGED and (best is None or share > best[0]):
            best = (share, j)
    return best[1] if best else None


def passage_map(sheet: str, row: int, old: list[str], new: list[str], lines: dict) -> tuple[dict, set]:
    """A passage's statements' keys as a write leaves them (see `passage_followed`): each statement that moves to
    its new key, a removed one to None, or to the statement it was merged into (see `merged_into`), those merged
    named apart."""
    cmap, merged = {}, set()
    for i in range(len(old)):
        key, j = themes.card_key(sheet, row, i), lines.get(i)
        if j is None:
            into = merged_into(old, new, lines, i)
            cmap[key] = None if into is None else themes.card_key(sheet, row, into)
            if into is not None:
                merged.add(key)
        elif j != i:
            cmap[key] = themes.card_key(sheet, row, j)
    return cmap, merged


def passage_followed(root: Path, workbook: Path, sheet: str, row: int, old: list[str], new: list[str], lines: dict,
                     books: list[dict] | None = None, dry: bool = False) -> dict:
    """A write of one passage's statements carried to the copy the file in scope keeps of the participant
    (lpetdrop, 13 November 2026, Adam by dialog: as the boards do): `old` and `new` the passage's statements
    before and after, `lines` each old statement's new place or None (see `themes.passage_lines`). A statement
    removed goes from the copy, its PETs and every board, an LPET's card of it with it; one merged into another
    follows it, the merged statement then standing once wherever either stood, never twice under one LPET; and
    every other statement of the passage that moves takes its new key, its quote with it. The copy keeps its
    words, so a change of wording shows as ever. Written once with the board's History as it was, and with `dry`
    not at all. Answers `removed`, `merged` and `moved`, the statements' keys, and `boards`, each board's cards
    that changed by its id, nothing when the file has no copy of the participant or nothing moved."""
    cmap, merged = passage_map(sheet, row, old, new, lines)
    if not cmap:
        return {}
    data, entries = held_of(root, workbook, books, move=not dry)
    if data is None or not entries:
        return {}
    out = {"removed": [], "merged": [], "moved": [], "boards": {}}
    for e in entries:
        case = e["case"]
        statements, quotes = case_keys(data, case)
        hit = {k: v for k, v in cmap.items() if k in statements}
        qhit = {k: v for k, v in cmap.items() if k in quotes}
        if not hit and not qhit:
            continue
        done = remap_case(data, case, hit, qhit, merged=merged & set(hit))
        for k, v in hit.items():
            (out["merged"] if k in merged else out["removed"] if v is None else out["moved"]).append(k)
        for bid, keys in done["boards"].items():
            out["boards"].setdefault(bid, []).extend(keys)
    if not (out["removed"] or out["merged"] or out["moved"] or out["boards"]):
        return {}
    if not dry:
        when = themes.now_iso()
        for board in boards_of(data):
            if str(board.get("id")) in out["boards"]:
                board["updated"] = when
        data["updated"] = when
        write(root, data)
    return out


# ------------------------------------------------------- a sheet's timecodes shifted reach the copies (timeshift)

def times_followed(root: Path, workbook: Path, sheet: str, moved: dict, times: dict,
                   books: list[dict] | None = None, dry: bool = False, plan: bool = False):
    """A sheet's timecodes shifted (see `workbook.shift_times`) carried to the copy the file in scope keeps of the
    participant (timeshift, 16 November 2026), so no card or quote shows the old time and the shift alone never marks
    the participant changed since they came in. `moved` is each shifted row's seconds before and after, by its row,
    and `times` every timed row of the sheet by its seconds before. A line of the sheet on a shifted row takes the
    row's new seconds when it held the row's old ones; a line holding another time, a change not yet taken, keeps
    it, so the participant still shows changed. Each end of a quote's span (quotespan) follows the row it belongs to,
    whether or not the line's own row was shifted (timefix): a quote may take in the same speaker's passages before
    its own row and after it, so its start is found at or before the line's row and its end at or after, each the
    nearest timed row holding that end's seconds, and takes that row's new seconds where that row moved. So the copy
    after a shift is what a fresh read of the workbook gives. The copy's hash follows only where it stood for the
    copy as it was. Written once, with `dry` not at all, the file read without its History moved (see `held_of`).
    Answers `lines`, how many lines took a new time, and `cases`, the cases of the file that did, nothing when none
    did; with `plan` it writes nothing and answers that and the file's data as it would be written, None for none,
    for the caller to write once the workbook is saved (timefix)."""
    data, entries = held_of(root, workbook, books, move=not dry)
    if data is None or not entries or not moved:
        return ({}, None) if plan else {}
    held = data["cases"]
    form = KEPT_AS
    out = {"lines": 0, "cases": []}
    order = sorted(times)
    # the rows of `moved` that had no timecode and take their first, by their new seconds (spanfix)
    first = {r: after for r, (before, after) in moved.items() if before is None and after is not None}
    spread_held: dict = {}

    def spread_rows(key: str, line: dict) -> list:
        """The rows the quote of a line takes in, from the first to the last, as a fresh read places it, the sheet
        read as it stands, the rows with no time as yet."""
        place = themes.split_card_key(key)[2]
        said = [str(q or "") for q in line.get("quotes") or []]
        if place is None or place >= len(said) or not said[place]:
            return []
        at = (line["row"], tuple(said))
        if at not in spread_held:
            try:
                spread_held[at] = themes.row_spread(workbook, sheet, line["row"], said, form)
            except Exception:  # noqa: BLE001  a sheet that cannot be read leaves the end as it was
                spread_held[at] = {}
        return list((spread_held[at].get(key) or {}).get("rows") or [])

    def end_of(seconds, row: int, back: bool):
        """A span's end as the shift leaves it: the nearest timed row holding `seconds`, at or before the line's
        own row for its start (`back`) and at or after it for its end, that row's new seconds where it moved."""
        if seconds is None:
            return None
        rows = reversed([r for r in order if r <= row]) if back else (r for r in order if r >= row)
        at = next((r for r in rows if times[r] == seconds), None)
        return moved[at][1] if at in moved else seconds

    for e in entries:
        rec = held.get(e["case"])
        lines = rec.get("lines") if isinstance(rec, dict) and isinstance(rec.get("lines"), dict) else {}
        whole = rec.get("hash") == snap_hash(rec) if isinstance(rec, dict) else False
        n = 0
        for key, line in lines.items():
            if not isinstance(line, dict) or line.get("sheet") != sheet or not isinstance(line.get("row"), int):
                continue
            row = line["row"]
            took = False
            if row in moved and line.get("seconds") == moved[row][0]:
                line["seconds"] = moved[row][1]
                took = True
            span = line.get("span")
            if isinstance(span, list) and len(span) == 2:
                new = [end_of(span[0], row, True), end_of(span[1], row, False)]
                if None in span and first:
                    # an end with no time belongs to a row that has none; one of those rows given its first timecode
                    # gives it to the end that is its row's, found as a fresh read finds it (spanfix, 16 November 2026)
                    rows = spread_rows(key, line)
                    for i, at in ((0, rows[0] if rows else None), (1, rows[-1] if rows else None)):
                        if span[i] is None and at in first:
                            new[i] = first[at]
                if new != span:
                    line["span"] = new
                    took = True
            if took:
                retimed(line, form, rec.get("cite") or "")
                n += 1
        if n:
            if whole:
                rec["hash"] = snap_hash(rec)
            out["lines"] += n
            out["cases"].append(e["case"])
    if not out["lines"]:
        return ({}, None) if plan else {}
    data["updated"] = themes.now_iso()
    if plan:
        return out, data
    if not dry:
        write(root, data)
    return out


# ------------------------------------------------------- statements added reach the copies (copiesadd)
# (16 November 2026, from the session that runs Adam's longitudinal study: a statement added with `turn write` or on
# the statements screen never reached the participant's LPETs, so a Trajectories cell could not tick its quote, and
# `copies refresh` brought in line only the statements a copy already held.) A copy holds every statement of its
# participant at its timepoint, placed or not, as it came in (see `snapshot`), so a statement added since joins it,
# in no PET and on no board, unplaced until the researcher places it, as lpetkeys made a removed one leave.

def passage_added(sheet: str, row: int, new: list[str], lines: dict) -> list[str]:
    """The keys of a passage's statements a write adds, `new` its statements after and `lines` each old statement's
    new place (see `themes.passage_lines`): each new statement no old one became."""
    became = {j for j in (lines or {}).values() if j is not None}
    return [themes.card_key(sheet, int(row), j) for j, text in enumerate(new or [])
            if j not in became and themes.words(text)]


def holds_sheet(entry: dict, workbook: Path, sheets: set) -> bool:
    """Whether a case of the file in scope is at a timepoint that holds one of `sheets`: on LGETs every timepoint of
    the participant, else the entry's own, T1 for a project of one."""
    if in_lgets():
        return True
    placed, here = themes.placed_sheets(workbook), int(entry.get("timepoint") or 1)
    return any(placed.get(s, 1) == here for s in sheets)


def row_lines(workbook: Path, sheet: str, row: int, cite: str = "") -> dict[str, dict]:
    """The statements of one passage as a copy keeps them (see `snapshot`), read from that row alone (copiesadd, 16
    November 2026), so a save that adds a statement never reads the whole workbook: each by its key with its sheet,
    row, time (cited with `cite` on the LPETs), seconds, words, the row's quotes by place and its exploratory notes,
    in no PET and not in the bin. A quote taking in the same speaker's passages beside its own carries its `span` and
    its time from the first passage to the last, as a fresh read gives them (spanfollow, 16 November 2026: it kept
    its own passage's time until the participant's changes were taken, so they read changed), the rest of the sheet
    read only for such a quote (see `themes.row_spread`). None for a row with no statement."""
    workbook = Path(workbook)
    form = timecodes_for(workbook)
    # read once for every file of copies a save reaches, while the workbook stands as it was read
    try:
        info = workbook.stat()
        held_key = (str(workbook.resolve()), info.st_mtime_ns, info.st_size, str(sheet), int(row), form)
    except OSError:
        held_key = None
    # .get, never a test then an index, as another project's save may empty it between the two (copiesfix)
    got = ROWS_HELD.get(held_key) if held_key is not None else None
    if got is not None:
        values, cols, width = got
    else:
        from workbook import row_cells
        values, cols, width = row_cells(workbook, sheet, row)
        if held_key is not None:
            ROWS_HELD.clear()
            ROWS_HELD[held_key] = (values, cols, width)
    if cols is None:
        return {}
    entries = themes.split_entries(values[cols["es"] - 1])
    places = list(themes.quote_entries(values[cols["kq"] - 1])) if "kq" in cols else []
    while places and not places[-1]:
        places.pop()
    notes = themes.split_entries(values[cols["en"] - 1]) if entries and "en" in cols else []
    seconds = themes.ts_seconds(values[cols["ts"] - 1])
    own = str(values[cols["transcript"] - 1] or "")
    spread = {}
    if any(themes.quote_spreads(q, own) for q in places[:len(entries)] if q):
        spread_key = held_key + (tuple(places),) if held_key is not None else None
        spread = SPREAD_HELD.get(spread_key) if spread_key is not None else None
        if spread is None:
            spread = themes.row_spread(workbook, sheet, int(row), places[:len(entries)], form)
            if spread_key is not None:
                SPREAD_HELD.clear()
                SPREAD_HELD[spread_key] = spread
    out = {}
    for i, text in enumerate(entries):
        key = themes.card_key(sheet, int(row), i)
        took = spread.get(key)
        time = took["time"] if took else timecode(seconds, form)
        if cite:
            time = f"{cite}, {time}" if time else cite
        out[key] = {"sheet": sheet, "row": int(row), "time": time, "seconds": seconds,
                    **({"span": list(took["span"])} if took else {}), "text": text, "quotes": list(places),
                    "notes": list(notes), "pet": None, "discarded": False}
    return out


def spans_followed(rec: dict, workbook: Path, key: str, quote: str) -> bool:
    """A copy's line of the statement at `key` given the span and time its quote, `quote` as the workbook now holds
    it, has in a fresh read (see `row_lines`), once a write has carried the quote to it (spanfollow, 16 November
    2026). A line holding another quote at its place, a change not yet taken, is left as it is. Answers whether
    the line changed. Reads the workbook as it stands, so it is called once the write is saved."""
    lines = rec.get("lines") if isinstance(rec.get("lines"), dict) else {}
    line = lines.get(key)
    sheet, row, place = themes.split_card_key(key)
    if not isinstance(line, dict) or row is None or place is None:
        return False
    held = [str(q or "") for q in line.get("quotes") or []]
    if themes.quote_words(held[place] if place < len(held) else "") != themes.quote_words(quote):
        return False
    fresh = row_lines(Path(workbook), sheet, row).get(key)
    if fresh is None:
        return False
    had = line.get("span")
    if fresh.get("span") == had:
        return False
    if fresh.get("span"):
        # placed after the seconds, where a fresh read puts it
        kept = dict(line)
        line.clear()
        for k, v in kept.items():
            if k != "span":
                line[k] = v
            if k == "seconds":
                line["span"] = list(fresh["span"])
        line.setdefault("span", list(fresh["span"]))
    else:
        line.pop("span", None)
    retimed(line, KEPT_AS, rec.get("cite") or "")
    return True


# the last row `row_lines` read, by the workbook's path, time and size, the sheet, the row and the timecodes
ROWS_HELD: dict = {}
# and the spans of the last row whose quotes take in the passages beside it, by the same and the row's quotes
SPREAD_HELD: dict = {}


def workbook_keys(workbook: Path, row_now: dict | None = None) -> set[str]:
    """Every statement's key a participant's workbook holds at every timepoint (see `workbook_lines`), read once for
    every file of copies a save reaches while the workbook stands as it was read (copiesfix, 16 November 2026).
    `row_now`, by one passage's sheet and row, is the keys that passage holds once a write not yet made, or just
    made, stands, which take the place of the row's as read."""
    workbook = Path(workbook)
    try:
        info = workbook.stat()
        held_key = (str(workbook.resolve()), info.st_mtime_ns, info.st_size)
    except OSError:
        held_key = None
    got = KEYS_HELD.get(held_key) if held_key is not None else None
    if got is None:
        got = frozenset(workbook_lines(workbook))
        if held_key is not None:
            KEYS_HELD.clear()
            KEYS_HELD[held_key] = got
    out = set(got)
    for (sheet, row), keys in (row_now or {}).items():
        out = {k for k in out if themes.split_card_key(k)[:2] != (sheet, row)} | set(keys)
    return out


# the last workbook `workbook_keys` read, by its path, time and size
KEYS_HELD: dict = {}


def copies_added(root: Path, workbook: Path, books: list[dict] | None = None, keys=None, dry: bool = False,
                 also=None, moved: dict | None = None, holds=None, row_now: dict | None = None) -> list[dict]:
    """The statements of a participant's workbook that the copy the file in scope keeps of them lacks, added to it
    (copiesadd, 16 November 2026): the project's GETs, inside `lgets` its LGETs, or inside `lpets` the participant's
    LPETs, each of their timepoints from `books`. Each joins the copy in no PET, not in the bin and stacked under
    none, so it stands unplaced, its quote one a Trajectories cell can tick; no board's card is made. The copy's other
    lines on its row take its quote in its own place alone, any other quote they hold kept as it is.

    `keys`, a write's new statements (see `passage_added`), keeps to those, each read from its row alone (see
    `row_lines`); `moved`, the write's statements moving with them (see `passage_map`), says which keys the copy
    holds once they have moved, for the dry run. With no `keys` every statement the copy lacks is added, `copies
    refresh`'s catching up, read afresh (see `fresh_of`). On the LGETs `also`, when given, is the keys the LPETs took
    or would take, so a timepoint whose LPETs hold no copy adds none. With `dry` nothing is written, and a write's
    keys are counted without a read, since the workbook is not yet written. The copy's hash follows, so the addition
    alone never marks the participant Changed since they came in. Written once, only when one was added.

    A copy holding a line at a key the workbook no longer holds, one an old row op left behind, takes nothing, on a
    write and on `copies refresh`, dry or not (copiesfix, 16 November 2026): its lines may stand at keys a run of
    statements has shifted from, so a statement it seems to lack may be one it holds at another key, and an added
    line would then be moved again by the `copies rekey` that puts it right. `holds` is the keys the workbook holds,
    else read (see `workbook_keys`) with `row_now`, the written passage's keys once the write stands, in place of
    its row's.

    Answers each case of the file that takes a statement, `case` (a timepoint on LPETs, else the participant) and
    `keys`, and each that takes none for that, `case` and `rekey`, its keys the workbook no longer holds, keys
    alone, never the words."""
    data, entries = held_of(root, workbook, books, move=not dry)
    if data is None or not entries:
        return []
    held = data["cases"]
    wanted = None if keys is None else [str(k) for k in keys]
    if wanted is not None and not wanted:
        return []
    lgets_on = in_lgets()
    out, adds, requotes = [], {}, {}
    there = [set(holds)] if holds is not None else []

    def behind(after: set) -> list[str]:
        """The copy's keys the workbook no longer holds, read once for every case."""
        if not there:
            there.append(workbook_keys(Path(workbook), row_now))
        return sorted((k for k in after if k not in there[0]), key=themes._order)

    for e in entries:
        rec = held[e["case"]]
        lines = rec.get("lines") if isinstance(rec.get("lines"), dict) else {}
        if wanted is not None:
            after = ({(moved or {}).get(k, k) for k in lines} - {None}) if dry else set(lines)
            mine = [k for k in wanted if k not in after and holds_sheet(e, Path(workbook), {themes.split_card_key(k)[0]})]
            if lgets_on and also is not None:
                mine = [k for k in mine if k in set(also)]
            if not mine:
                continue
            # a copy an old row op left behind takes nothing until `copies rekey` puts it right (copiesfix)
            left = behind(after)
            if left:
                out.append({"case": e["case"], "keys": [], "rekey": left})
                continue
            if dry:
                out.append({"case": e["case"], "keys": mine})
                continue
            if lgets_on:
                fresh = fresh_of(e)["lines"]
            else:
                fresh = {}
                for sheet, row in sorted({themes.split_card_key(k)[:2] for k in mine}):
                    fresh.update(row_lines(Path(workbook), sheet, row, e.get("cite") or ""))
        else:
            fresh = fresh_of(e)["lines"]
        new = {}
        for k, line in fresh.items():
            if k in lines or not isinstance(line, dict):
                continue
            if wanted is not None and k not in wanted:
                continue
            if wanted is not None and lgets_on and also is not None and k not in set(also):
                continue
            line = dict(line, pet=None, discarded=False)
            line.pop("stacked", None)
            new[k] = line
        if dry and lgets_on:
            for k in also or ():
                if k not in lines and k not in new:
                    new[str(k)] = None
        if not new:
            continue
        if wanted is None:
            left = behind(set(lines))
            if left:
                out.append({"case": e["case"], "keys": [], "rekey": left})
                continue
        out.append({"case": e["case"], "keys": sorted(new, key=themes._order)})
        adds[e["case"]] = new
        # each line already on an added statement's row takes its quote in its place, as every line of a row keeps the
        # row's quotes by place (see `row_places`), and nothing else, so a quote change the copy holds back stays
        for k, line in new.items():
            if not isinstance(line, dict):
                continue
            sheet, row, at = themes.split_card_key(k)
            quote = (line.get("quotes") or [])[at] if at is not None and at < len(line.get("quotes") or []) else ""
            for other, held_line in lines.items():
                if not isinstance(held_line, dict) or themes.split_card_key(other)[:2] != (sheet, row):
                    continue
                places = list(requotes.get(e["case"], {}).get(other, held_line.get("quotes") or []))
                if at < len(places) and places[at] == quote:
                    continue
                if not quote and at >= len(places):
                    continue
                places += [""] * (at + 1 - len(places))
                places[at] = quote
                while places and not places[-1]:
                    places.pop()
                requotes.setdefault(e["case"], {})[other] = places
    if dry or not adds:
        return out
    for case, new in adds.items():
        rec = held[case]
        lines = rec.get("lines") if isinstance(rec.get("lines"), dict) else {}
        for k, places in (requotes.get(case) or {}).items():
            lines[k]["quotes"] = places
        lines.update(new)
        rec["lines"] = {k: lines[k] for k in sorted(lines, key=themes._order)}
        rec["hash"] = snap_hash(rec)
    data["updated"] = themes.now_iso()
    write(root, data)
    return out


def truth_words(truth: dict) -> dict[str, list[str]]:
    """The workbook's statements' keys by their words, `truth` as `workbook_lines` reads it."""
    out: dict[str, list[str]] = {}
    for k, v in truth.items():
        out.setdefault(themes.words(v.get("text")), []).append(k)
    return out


def nearest(key: str, found: list[str]) -> str:
    """Of keys on a statement's sheet, the nearest to `key`: its own row first and the nearest line, then the
    nearest row."""
    sheet, row, line = themes.split_card_key(key)
    same = [x for x in found if themes.split_card_key(x)[1] == row]
    if same:
        return min(same, key=lambda x: (abs(themes.split_card_key(x)[2] - (line or 0)), x))
    return min(found, key=lambda x: (abs(themes.split_card_key(x)[1] - (row or 0)), themes._order(x)))


def lpets_of(data: dict, board: dict | None, case: str, key: str) -> list[dict]:
    """The top groups of `board`, LPETs or GETs, that hold a statement of `case` by its key, its own card or the
    PET's card that holds it, each by id and title."""
    if board is None:
        return []
    rec = (data.get("cases") or {}).get(case) or {}
    groups = [g for g in board.get("groups") or [] if isinstance(g, dict)]
    by_id = {g["id"]: g for g in groups}
    parents = themes.parents_of(groups)
    pets = {p["id"] for p in rec.get("pets") or [] if isinstance(p, dict) and key in pet_lines(rec, p["id"])}

    def holds(m: str) -> bool:
        # the statement's own card, or a card of a PET holding it, a second card of one (`/2`) among them
        s = split_key(m)
        return s["case"] == case and ((s["kind"] == "es" and s["ident"] == key) or (s["kind"] == "group" and s["ident"] in pets))

    out = []
    for g in groups:
        if g["id"] in parents:
            continue
        seen, todo, hit = set(), [g["id"]], False
        while todo and not hit:
            at = todo.pop()
            if at in seen or at not in by_id:
                continue
            seen.add(at)
            for m in by_id[at].get("members") or []:
                if holds(m):
                    hit = True
                    break
                todo.append(m)
        if hit:
            out.append({"id": g["id"], "title": g.get("label") or ""})
    return out


# ------------------------------------------------- what draws on a PET, a sub-theme or a statement (drawsword)
#
# Adam, 17 November 2026: an LPET is his interpretation, and the cards under it record what it draws on at each
# timepoint, its audit trail. The forward trace reads it the other way: for a PET, a sub-theme or a statement of a
# timepoint, which LPETs of the participant's board draw on it. An LPET draws on an item `whole` when the item's own
# card is under it, `through` a larger one when the card of a PET or sub-theme holding it is (`via`), and `part` when
# the card of something inside it is.

HOW_ORDER = ("whole", "through", "part")


def drawn_on(data: dict, board: dict | None, case: str) -> dict:
    """For the timepoint `case`, T1, of a participant's LPETs file: each PET and sub-theme of its copy by id, and each
    statement by its key, with the top LPETs of `board` that draw on it, in canvas order, each `{"id", "title",
    "how", "via"}`, `via` the larger card's PET or sub-theme by id and title when `how` is `through`. Only those
    drawn on are named. Only reads."""
    if board is None:
        return {"pets": {}, "statements": {}}
    return drawn_in(data, normal(board, data), case)


def drawn_in(data: dict, kept: dict, case: str) -> dict:
    """`drawn_on` over a board already normalised, `kept`, which `normal` itself asks of the board it makes."""
    out = {"pets": {}, "statements": {}}
    rec = (data.get("cases") or {}).get(case) or {}
    pets = {p["id"]: p for p in rec.get("pets") or [] if isinstance(p, dict) and p.get("id")}
    lines = rec.get("lines") or {}
    by_id = {g["id"]: g for g in kept["groups"]}
    parents = themes.parents_of(kept["groups"])
    # each PET's line of PETs and sub-themes above it, nearest first
    above = {}
    for pid, p in pets.items():
        chain, at, seen = [], p.get("parent"), {pid}
        while at in pets and at not in seen:
            chain.append(at)
            seen.add(at)
            at = pets[at].get("parent")
        above[pid] = chain
    # each statement's PET, its top's where it is stacked
    owner = {}
    for pid, p in pets.items():
        for k in p.get("statements") or []:
            owner.setdefault(k, pid)
    for k, line in lines.items():
        top = line.get("stacked") if isinstance(line, dict) else None
        if k not in owner and top in owner:
            owner[k] = owner[top]

    def mark(kind: str, key: str, g: dict, how: str, via: str | None = None) -> None:
        held = out[kind].setdefault(key, [])
        found = next((x for x in held if x["id"] == g["id"]), None)
        entry = {"id": g["id"], "title": str(g.get("label") or ""), "how": how}
        if via is not None:
            entry["via"] = {"id": via, "title": str(pets[via].get("title") or "")}
        if found is None:
            held.append(entry)
        elif HOW_ORDER.index(how) < HOW_ORDER.index(found["how"]):
            held[held.index(found)] = entry

    tops = themes.canvas_order([g["id"] for g in kept["groups"] if g["id"] not in parents], by_id)
    for gid in tops:
        g = by_id[gid]
        for key in themes.cards_under(by_id, gid):
            k = split_key(key)
            if k["case"] != case:
                continue
            if k["kind"] == "group" and k["ident"] in pets:
                pid = k["ident"]
                mark("pets", pid, g, "whole")
                for up in above[pid]:
                    mark("pets", up, g, "part")
                # everything inside it, its sub-themes at any depth and their statements
                inside = [x for x, chain in above.items() if pid in chain]
                for x in inside:
                    mark("pets", x, g, "through", pid)
                for s in pet_lines({"pets": list(pets.values())}, pid):
                    mark("statements", s, g, "through", pid)
                for s, top in ((s, line.get("stacked")) for s, line in lines.items() if isinstance(line, dict)):
                    if top and owner.get(s) and (owner[s] == pid or pid in above.get(owner[s], [])):
                        mark("statements", s, g, "through", pid)
            elif k["kind"] == "es" and k["ident"] in lines:
                s = k["ident"]
                mark("statements", s, g, "whole")
                for t, line in lines.items():
                    if isinstance(line, dict) and line.get("stacked") == s:
                        mark("statements", t, g, "whole")
                pid = owner.get(s)
                for up in ([pid] + above[pid]) if pid in pets else []:
                    mark("pets", up, g, "part")
    return out


def why_undrawn(kept: dict, data: dict) -> dict[str, str]:
    """His reasons kept on a normalised board, `kept`, for the PETs and sub-theme no LPET draws on: a reason for "no
    LPET draws on it" is untrue while one does, so every read hides it while its PET is drawn on, wholly, through a
    larger card or in part, and the file keeps it, so it shows again when none does, after any undo of the change
    or a later move (drawswordfix2, 17 November 2026)."""
    held = kept.get(themes.WHY) if isinstance(kept.get(themes.WHY), dict) else {}
    if not held:
        return {}
    drawn: dict = {}
    out = {}
    for key, why in held.items():
        k = split_key(key)
        if k["kind"] == "group":
            if k["case"] not in drawn:
                drawn[k["case"]] = drawn_in(data, kept, k["case"])["pets"]
            if drawn[k["case"]].get(k["ident"]):
                continue
        out[key] = why
    return out


def drawn_on_why(data: dict, board: dict | None, case: str) -> dict[str, str]:
    """His reasons a PET or sub-theme of the timepoint `case` is drawn on by no LPET, by its id."""
    held = (normal(board, data).get(themes.WHY) or {}) if board is not None else {}
    out = {}
    for key, why in held.items():
        k = split_key(key)
        if k["case"] == case and k["kind"] == "group" and not k["copy"]:
            out[k["ident"]] = why
    return out


def copies_rekeyed(root: Path, workbook: Path, truth: dict, books: list[dict] | None = None, at: str | None = None,
                   sheet: str | None = None, from_row: int | None = None, shift: int | None = None, dry: bool = False,
                   changed: dict | None = None, history: str = "") -> dict:
    """The copy the file in scope keeps of a participant re-pointed at its statements where a row op left its keys
    behind (lpetkeys, 13 November 2026): the project's GETs, inside `lgets` its LGETs, or inside `lpets` the
    participant's LPETs, each of their timepoints in it from `books`, or the one `at` names, `T1`. `truth` is the
    workbook's statements by key (see `workbook_lines`).

    By the statement's own words, the default: each line of the copy whose key the workbook no longer holds takes
    the key where its words now stand on its sheet, not held by another line of the copy, its own row first, then
    the nearest row. A line whose words stand nowhere cannot be matched and is listed, for `copies_pruned`. A key
    the workbook still holds is never moved this way, so a statement reworded keeps its place.

    By an offset, with `from_row` and `shift`, where the words cannot tell (a refresh that took the workbook's words
    at keys already one row off): every key of the timepoint `at` on `sheet`, or its one sheet, from row
    `from_row` down moves by `shift` rows, its words or not, refused whole when one would land on a key of the
    copy that stays.

    Every place the file names a moved key follows (see `remap_case`), the revisions too. Each board whose cards
    move keeps itself first in its History under `history` and with `changed`, an agent's mark, is marked changed.
    Written once, and with `dry` not at all. Answers `moves`, each statement moved, its timepoint, `from`, `to`,
    whether the workbook's words there are the copy's, `matched`, and the LPETs that hold it on the board the
    table reads, and `unmatched`, each line it cannot place, with its LPETs, never the words."""
    data, entries = held_of(root, workbook, books, move=not dry)
    if data is None or not entries:
        return {}
    if at is not None:
        entries = [e for e in entries if e["case"] == at]
        if not entries:
            return {}
    held = data["cases"]
    words_at = {k: themes.words(v.get("text")) for k, v in truth.items()}
    where = truth_words(truth)
    board, _ = source_board(data)
    moves, unmatched, maps = [], [], {}
    for e in entries:
        case = e["case"]
        lines = held[case].get("lines") if isinstance(held[case].get("lines"), dict) else {}
        statements, quotes = case_keys(data, case)
        cmap: dict[str, str] = {}
        turns, merged = None, set()
        if from_row is not None:
            sheets = sorted({themes.split_card_key(k)[0] for k in statements | quotes})
            on = sheet if sheet is not None else (sheets[0] if len(sheets) == 1 else None)
            if on is None:
                raise WorkbookError(i18n.t("server.copies_rekey_which_sheet", case=case, sheets=", ".join(sheets)))
            for k in statements | quotes:
                s, r, n = themes.split_card_key(k)
                if s == on and r is not None and n is not None and r >= from_row:
                    cmap[k] = themes.card_key(s, r + shift, n)
            stays = (statements | quotes) - set(cmap)
            clash = sorted({v for v in cmap.values() if v in stays}, key=themes._order)
            if clash:
                raise WorkbookError(i18n.t("server.copies_rekey_clash", case=case, keys=", ".join(clash)))

            def turns(t, on=on):
                s, _, r = str(t).rpartition(":")
                return themes.row_key(s, int(r) + shift) if s == on and r.isdigit() and int(r) >= from_row else t
        else:
            claimed = {k for k in lines if k in truth}
            for k in sorted((k for k in lines if k not in truth), key=themes._order):
                said = themes.words((lines[k] or {}).get("text"))
                s = themes.split_card_key(k)[0]
                found = [x for x in where.get(said, []) if themes.split_card_key(x)[0] == s and x not in claimed] if said else []
                # a line of the copy at that key already reads the same, as a refresh leaves a statement removed
                # before it in its passage: the two are one statement, and this one joins it
                same = [x for x in where.get(said, []) if themes.split_card_key(x)[0] == s and x in lines
                        and themes.words((lines[x] or {}).get("text")) == said] if said and not found else []
                if not found and not same:
                    unmatched.append({"timepoint": case, "key": k, "lpets": lpets_of(data, board, case, k)})
                    continue
                to = nearest(k, found or same)
                cmap[k] = to
                claimed.add(to)
                if not found:
                    merged.add(k)
        cmap = {k: v for k, v in cmap.items() if v != k}
        if not cmap:
            continue
        # a statement's own quote is its row's at its place, so a pick or a ticked quote goes where it goes
        qmap = {k: v for k, v in cmap.items() if k in quotes}
        maps[case] = (cmap, qmap, turns, merged)
        for k in sorted(cmap, key=themes._order):
            if k not in statements:
                continue
            line = lines.get(k)
            moves.append({"timepoint": case, "from": k, "to": cmap[k], "joins": k in merged,
                          "matched": line is not None and words_at.get(cmap[k]) == themes.words(line.get("text")),
                          "lpets": lpets_of(data, board, case, k)})
    out = {"moves": moves, "unmatched": unmatched, "boards": []}
    if not maps:
        return out if unmatched else {}
    when = themes.now_iso()
    touched: dict[str, list[str]] = {}
    for case, (cmap, qmap, turns, merged) in maps.items():
        before = {str(b.get("id")): json.loads(json.dumps(themes.board_state(b))) for b in boards_of(data)}
        done = remap_case(data, case, cmap, qmap, turns=turns, merged=merged)
        for bid, keys in done["boards"].items():
            touched.setdefault(bid, []).extend(keys)
            if not dry and bid in before:
                b = next(x for x in boards_of(data) if str(x.get("id")) == bid)
                if not any(r.get("name") == history and r.get("at") == when for r in themes.history_known(b)):
                    themes.kept_revision(b, name=history, at=when, state=before[bid])
    out["boards"] = [{"board": bid, "name": next(str(b.get("name") or FIRST_NAME) for b in boards_of(data)
                                                 if str(b.get("id")) == bid), "cards": keys}
                     for bid, keys in touched.items()]
    if dry:
        return out
    for board in boards_of(data):
        if str(board.get("id")) in touched:
            board["updated"] = when
            if changed:
                board["changed"] = dict(changed, at=when)
                board["changed"]["hash"] = themes.state_hash(themes.made_state(normal(board, data, hide=False)))
    data["updated"] = when
    write(root, data)
    return out


def evidence(data: dict, board: dict | None, cases: list[str]) -> dict[tuple[str, str], int]:
    """How many statements each top group of `board`, an LPET or a GET, holds of each case in `cases`, its own
    statement cards and its PETs' statements, by (group id, case), a statement the copy no longer holds left out."""
    if board is None:
        return {}
    out = {}
    held = data.get("cases") or {}
    for g in table(data, board, cases):
        for row in g["rows"]:
            lines = (held.get(row["case"]) or {}).get("lines") or {}
            n = sum(1 for it in row["items"] if it["kind"] == "es" and it["line"] in lines)
            n += sum(len([k for k in it.get("lines") or [] if k in lines]) for it in row["items"]
                     if it["kind"] in ("pet", "sub") and not it["gone"])
            out[(g["id"], row["case"])] = n
    return out


def copies_pruned(root: Path, workbook: Path, truth: dict, books: list[dict] | None = None, dry: bool = False,
                  changed: dict | None = None, history: str = "") -> dict:
    """The copies the file in scope keeps of a participant's statements that are no longer in their workbook
    taken off (lpetkeys, 13 November 2026): the project's GETs, inside `lgets` its LGETs, or inside `lpets` the
    participant's LPETs, each of their timepoints from `books`. `truth` is the workbook's statements by key (see
    `workbook_lines`). A line of the copy whose key the workbook does not hold and whose words stand nowhere on its
    sheet goes, from the copy, its PETs and every board, with its picks and a ticked quote on it; one whose words
    stand at another key is left and listed under `elsewhere`, for `copies_rekeyed` first. Each board whose cards
    go keeps itself first in its History under `history`, and with `changed` is marked changed. Written once, and
    with `dry` not at all.

    Answers `pruned`, each statement taken off, its timepoint, key and the LPETs that held it on the board the
    table reads, `elsewhere`, those left, `boards`, each board's cards taken off, and `emptied`, each LPET (or GET)
    of that board left with no statement at a timepoint that had one, by id, title and timepoint, so a statement
    can be put in its place before the write. Never a statement's words."""
    data, entries = held_of(root, workbook, books, move=not dry)
    if data is None or not entries:
        return {}
    held = data["cases"]
    where = truth_words(truth)
    board, _ = source_board(data)
    pruned, elsewhere, maps = [], [], {}
    for e in entries:
        case = e["case"]
        lines = held[case].get("lines") if isinstance(held[case].get("lines"), dict) else {}
        statements, quotes = case_keys(data, case, history=False)
        gone = set()
        for k in sorted((k for k in statements if k not in truth), key=themes._order):
            said = themes.words((lines.get(k) or {}).get("text"))
            s = themes.split_card_key(k)[0]
            if said and any(themes.split_card_key(x)[0] == s for x in where.get(said, [])):
                elsewhere.append({"timepoint": case, "key": k, "lpets": lpets_of(data, board, case, k)})
                continue
            gone.add(k)
            pruned.append({"timepoint": case, "key": k, "lpets": lpets_of(data, board, case, k)})
        if gone:
            maps[case] = ({k: None for k in gone}, {q: None for q in quotes if q in gone})
    out = {"pruned": pruned, "elsewhere": elsewhere, "boards": [], "emptied": []}
    if not maps:
        return out if elsewhere else {}
    cases = [e["case"] for e in entries]
    was = evidence(data, board, cases)
    when = themes.now_iso()
    touched: dict[str, list[str]] = {}
    for case, (cmap, qmap) in maps.items():
        before = {str(b.get("id")): json.loads(json.dumps(themes.board_state(b))) for b in boards_of(data)}
        done = remap_case(data, case, cmap, qmap, history=False)
        for bid, keys in done["boards"].items():
            touched.setdefault(bid, []).extend(keys)
            if not dry:
                b = next(x for x in boards_of(data) if str(x.get("id")) == bid)
                if not any(r.get("name") == history and r.get("at") == when for r in themes.history_known(b)):
                    themes.kept_revision(b, name=history, at=when, state=before[bid])
    now = evidence(data, board, cases)
    titles = {g["id"]: g.get("label") or "" for g in (board or {}).get("groups") or [] if isinstance(g, dict)}
    out["emptied"] = [{"board": str(board.get("id")), "board_name": str(board.get("name") or FIRST_NAME),
                       "lpet": gid, "title": titles.get(gid, ""), "timepoint": case}
                      for (gid, case), n in was.items() if n and not now.get((gid, case))]
    out["boards"] = [{"board": bid, "name": next(str(b.get("name") or FIRST_NAME) for b in boards_of(data)
                                                 if str(b.get("id")) == bid), "cards": keys}
                     for bid, keys in touched.items()]
    if dry:
        return out
    for b in boards_of(data):
        if str(b.get("id")) in touched:
            b["updated"] = when
            if changed:
                b["changed"] = dict(changed, at=when)
                b["changed"]["hash"] = themes.state_hash(themes.made_state(normal(b, data, hide=False)))
    data["updated"] = when
    write(root, data)
    return out


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
    # a statement's second card follows its first (drawsbuild), so the words are followed once, by the first's key
    seconds = [key for key in cards if split_key(key)["case"] == case and split_key(key)["kind"] == "es"
               and split_key(key)["copy"]]
    cards = {key: c for key, c in cards.items() if key not in seconds}
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
    out = {key: card_of(case, "es", ident) for key, ident in to.items() if ident != mine[key]}
    for key in seconds:
        first = base_key(key)
        if first in out:
            out[key] = with_copy(key, out[first])
    return out


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


def take(root: Path, books: list[dict], case: str, dry_run: bool = False) -> dict:
    """Take the changes of a case that changed since it came in: each GET board keeps a revision
    first, each card of its PETs keeps its place by id, then by title, a statement's card by its
    line, then by its words, a top-level PET with no card and a sub-theme new to the case come in
    unplaced in the nearest free spot, and a card whose PET has gone from the case stays where it
    is, its title kept on it, marked "No longer in" its PETs. A sub-theme the copy held already and
    the board never did, on a board made before sub-themes came in as cards, stays off it (Add every
    sub-theme brings it). Nothing is moved or binned by itself.

    Each board keeps its own structure (takedry, 16 November 2026): its labels (on LPETs the LPETs), their titles
    and places, which cards sit under which label and in what order, the bin, the picks, the rows (on LPETs the key
    quotes, his bold and the states Trajectories shows) and the notes. Only the copy's contents follow the source, a
    card following its PET or its statement to a new key, a card grown taller making room below it, a new PET's card
    coming into the pile and a card whose source has gone keeping its title (see `structure_kept`); a take that would
    change anything else is refused whole, nothing written. With `dry_run` the same take runs in memory alone and
    nothing is written, and the answer is its `counts` (see `take_into`), keys and counts and never a word. The
    take answers the same `counts`, so it writes exactly what its dry run said."""
    when = themes.now_iso()
    data, cases, _disk, _taken = assemble(root, books, when)
    entry = next((e for e in cases if e["case"] == case), None)
    old = (data.get("cases") or {}).get(case)
    if entry is None or old is None:
        raise WorkbookError(i18n.t("server.participant_gets_yet_nothing_came"))
    if entry["status"] == "in":
        raise WorkbookError(i18n.t("server.nothing_changed_s_pets_since", who_case=who(case)))
    fresh = entry["fresh"] if entry["fresh"] is not None else fresh_of(entry)
    counts = take_into(data, case, old, fresh, entry["workbook"], when)
    if dry_run:
        return {"dry_run": True, "op": "take", "taken": case, "counts": counts}
    write(root, _file(data, when))
    current = data.get("current")
    return dict(answer(data, survey(books, data), data, board=current), op="take", taken=case, counts=counts)


def take_into(data: dict, case: str, old: dict, fresh: dict, workbook: Path, when: str) -> dict:
    """A case's changes taken into `data` in memory (see `take`), and what the take changed, keys and counts and
    never a word: `copy`, what changed in the case's copy (`copy_counts`), and `boards`, for each board what it does
    there (`board_effects`). Refused whole when a board would not keep its own structure."""
    pairs = matched(old.get("pets") or [], fresh["pets"])
    # what comes in: every top-level PET with no card, as before, and a sub-theme new to the case
    new = {p["id"] for p in fresh["pets"]} - set(pairs.values())
    comers = tops(case, fresh) + [e for e in subs_of(case, fresh) if split_key(e[0])["ident"] in new]
    titles = {p["id"]: p["title"] for p in old.get("pets") or []}
    name = who(case)
    # the cards' words for the estimates of the layout, this case's from its new copy
    seen = dict(data, cases=dict(data.get("cases") or {}, **{case: {"pets": fresh["pets"], "lines": fresh["lines"]}}))
    before = dict(data, cases=dict(data.get("cases") or {}))
    source = source_board(data)[0] if in_lpets() else None
    # each ticked quote of the case follows its words as its statement's card does (takefix)
    qmap = quotes_followed(case, old, fresh)
    done = []
    for board in boards_of(data):
        was_board = json.loads(json.dumps(board))
        themes.add_revision(board, name=themes.revision_name("before_changes", who=name), at=when)
        # each card's height as it stood, for the room a card that grows makes below it (see `make_room_below`)
        was = {k: card_height(k, c.get("text")) for k, c in named(board, data)["cards"].items()}
        # a statement's card follows its words, whatever a write moved or removed in its passage
        rename = lines_followed(case, board.get("cards") or {}, old.get("lines") or {}, fresh["lines"])
        titled = set()
        for key in list(board.get("cards") or {}):
            k = split_key(key)
            if k["case"] != case:
                continue
            if k["kind"] == "group":
                to = pairs.get(k["ident"])
                if to is None:
                    if not board["cards"][key].get("text"):
                        titled.add(key)
                    board["cards"][key]["text"] = board["cards"][key].get("text") or titles.get(k["ident"], themes.UNTITLED)
                elif to != k["ident"]:
                    fresh_key = card_of(case, "group", to) + (f"/{k['copy']}" if k["copy"] else "")
                    if fresh_key not in board["cards"]:
                        rename[key] = fresh_key
        keys_followed(board, case, rename, qmap)
        back = {to: key for key, to in rename.items()}
        pushed = carried(board, make_room_below(board, seen, {back.get(k, k): k for k in board.get("cards") or {}}, was))
        lay_in(board, comers, seen)
        # in a thematic analysis project a new extract of a code on the board comes in where it stands (codes)
        if ta_now():
            codes_mod().gather(board, seen)
        board["updated"] = when
        done.append((was_board, board, rename, titled, pushed))
    data["cases"][case] = record(fresh, workbook, when)
    boards = []
    for was_board, board, rename, titled, pushed in done:
        effects = board_effects(case, was_board, board, before, data, old, fresh, pairs, rename)
        differs = {} if ta_now() else structure_changes(was_board, board, case, rename, qmap, effects, titled, pushed)
        if differs:
            raise WorkbookError(i18n.t("server.take_would_change_board", who_case=name, board=str(was_board.get("id")),
                                       what=differs_said(differs)))
        boards.append(dict({"board": str(board.get("id")), "name": str(board.get("name") or "")},
                           **({"trajectories": True} if source is not None and source.get("id") == board.get("id") else {}),
                           **effects))
    return {"copy": copy_counts(case, old, fresh, pairs), "boards": boards}


def counted(keys: dict) -> dict:
    """Each list of keys beside its count, `n_<name>`."""
    out = {}
    for k, v in keys.items():
        if isinstance(v, (list, dict)):
            out["n_" + k] = len(v)
        out[k] = v
    return out


def copy_counts(case: str, old: dict, fresh: dict, pairs: dict[str, str]) -> dict:
    """What a take changes in a case's copy, by key: PETs `pets_added`, `pets_renamed` (a new title or the same
    title on a new id) and `pets_removed`, `<case>/<id>`; statements `statements_added`, `statements_changed` (its
    words or its quotes), `statements_moved` (to another PET, out of one or into one, set aside or back) and
    `statements_removed`, `<case>/es/<line>`; `marked`, its PETs marked complete since, and `source`, the copy now
    from another board. Each list with its count beside it. A PET matched by title keeps its statements' place."""
    olds = {p["id"]: p for p in old.get("pets") or []}
    news = {p["id"]: p for p in fresh.get("pets") or []}
    taken = set(pairs.values())
    old_lines = old.get("lines") or {}
    new_lines = fresh.get("lines") or {}

    def place(line: dict, mapped: bool) -> tuple:
        if line.get("discarded"):
            return ("aside",)
        pid = line.get("pet")
        if pid and mapped:
            pid = pairs.get(pid, f"\x00{pid}")
        return ("pet", pid) if pid else ("none",)

    added = [card_of(case, "group", p["id"]) for p in fresh.get("pets") or [] if p["id"] not in taken]
    removed = [card_of(case, "group", p["id"]) for p in old.get("pets") or [] if p["id"] not in pairs]
    renamed = [card_of(case, "group", b) for a, b in pairs.items() if olds[a]["title"] != news[b]["title"] or a != b]
    s_added = [card_of(case, "es", k) for k in new_lines if k not in old_lines]
    s_removed = [card_of(case, "es", k) for k in old_lines if k not in new_lines]
    s_changed, s_moved = [], []
    for k, line in new_lines.items():
        was = old_lines.get(k)
        if not isinstance(was, dict) or not isinstance(line, dict):
            continue
        if themes.words(was.get("text")) != themes.words(line.get("text")) or list(was.get("quotes") or []) != list(line.get("quotes") or []):
            s_changed.append(card_of(case, "es", k))
        if place(was, True) != place(line, False):
            s_moved.append(card_of(case, "es", k))
    return dict(counted({"pets_added": added, "pets_renamed": renamed, "pets_removed": removed,
                         "statements_added": s_added, "statements_changed": s_changed, "statements_moved": s_moved,
                         "statements_removed": s_removed}),
                marked=bool(fresh.get("complete")) and not old.get("complete"),
                source=fresh.get("board") != old.get("board"))


def pet_view(rec: dict, pid: str) -> tuple | None:
    """What a PET's card shows from its case's copy, to tell whether a take changes it: its title, description,
    note, statements at any depth and picks. None for a PET the copy does not hold."""
    pet = next((p for p in rec.get("pets") or [] if p.get("id") == pid), None)
    if pet is None:
        return None
    return (pet.get("title"), themes.description_of(pet), pet.get("note") or "", sorted(pet_lines(rec, pid)),
            list(pet.get("picks") or []))


def line_view(rec: dict, ident: str, pairs: dict | None = None) -> tuple | None:
    """What a statement's card shows from its case's copy: its words, quotes and where it stands, its PET by the id
    the take gives it with `pairs`. None for a statement the copy does not hold."""
    line = (rec.get("lines") or {}).get(ident)
    if not isinstance(line, dict):
        return None
    pid = line.get("pet")
    if pid and pairs is not None:
        pid = pairs.get(pid, f"\x00{pid}")
    return (themes.words(line.get("text")), list(line.get("quotes") or []), pid, bool(line.get("discarded")))


def cells_of(data: dict, board: dict, case: str) -> dict[str, tuple]:
    """Each label's row for a case on a board as its table shows it, by `<label>/<case>`: the key quote's key and
    words, whether he ticked it and his bold in it. On LPETs these are the cells Trajectories shows."""
    out = {}
    for g in table(data, json.loads(json.dumps(board)), [case]):
        for row in g["rows"]:
            q = row.get("quote") or {}
            # the cell as it reads, its key aside, so a ticked quote that follows its words to a new place reads the same
            out[f"{g['id']}/{row['case']}"] = (q.get("text"), bool(row.get("chosen")), row.get("bold") or [])
    return out


def board_effects(case: str, was: dict, board: dict, before: dict, after: dict, old: dict, fresh: dict,
                  pairs: dict[str, str], rename: dict[str, str]) -> dict:
    """What a take does on one board, by key, each list with its count: `labels_changed`, the top-level labels (on
    LPETs the LPETs) holding a card it changes; `cards_changed`, the case's cards it changes, its PET's or its
    statement's words, statements, picks or place in the copy, or its key; `cards_lost`, cards whose PET or statement
    is no longer in the copy, left where they stand; `cards_renamed`, each card's old key to its new; `cards_added`,
    cards new to the board, in the pile; `cards_moved`, cards moved straight down to make room below a card grown
    taller, `labels_moved` and `notes_moved`, the labels (with all they hold) and sticky notes moved straight down
    the same way; and `cells_changed`, the rows whose key quote or bold the table (on LPETs Trajectories) shows
    differently, `<label>/<case>`. `cards_renamed` is a list of pairs, a card's old key and its new. The keys stay plain in an agent's answer (`cli.PLAIN`): never words. `was` and `before` are the board and
    the file before, `board` and `after` after."""
    cards_was = was.get("cards") or {}
    cards_now = board.get("cards") or {}
    from_key = {rename.get(k, k): k for k in cards_was}
    added = sorted(k for k in cards_now if k not in from_key)
    moved = sorted(k for k, o in from_key.items() if k in cards_now
                   and (cards_now[k].get("x"), cards_now[k].get("y")) != (cards_was[o].get("x"), cards_was[o].get("y")))
    changed, lost = [], []
    for key in cards_now:
        k = split_key(key)
        if k["case"] != case or key not in from_key or k["kind"] not in ("group", "es"):
            continue
        o = split_key(from_key[key])
        if k["kind"] == "group":
            then, now = pet_view(old, o["ident"]), pet_view(fresh, k["ident"])
            if then is not None and now is None:
                lost.append(key)
            if then is not None and now is not None:
                # a PET's statements by the keys the take gives them, so a PET matched by title is compared fairly
                then = then[:3] + (sorted(rename_line(case, x, rename) for x in then[3]),) + then[4:]
        else:
            then, now = line_view(old, o["ident"], pairs), line_view(fresh, k["ident"])
            if then is not None and now is None:
                lost.append(key)
        if key != from_key[key] or key in lost or (now is not None and then != now):
            changed.append(key)
    by_id = {g["id"]: g for g in board.get("groups") or [] if isinstance(g, dict) and g.get("id")}
    parents = themes.parents_of(list(by_id.values()))
    hit = set(changed)
    labels = [gid for gid in themes.canvas_order([g for g in by_id if g not in parents], by_id)
              if hit & set(themes.cards_under(by_id, gid))]
    cells_was, cells_now = cells_of(before, was, case), cells_of(after, board, case)
    cells = sorted(k for k in set(cells_was) | set(cells_now) if cells_was.get(k) != cells_now.get(k))
    spot = lambda x: (x.get("x"), x.get("y"))  # noqa: E731
    labels_was = {g.get("id"): g for g in was.get("groups") or [] if isinstance(g, dict)}
    notes_was = {n.get("id"): n for n in was.get("notes") or [] if isinstance(n, dict)}
    labels_moved = sorted(str(g["id"]) for g in board.get("groups") or [] if isinstance(g, dict)
                          and g.get("id") in labels_was and spot(g) != spot(labels_was[g["id"]]))
    notes_moved = sorted(str(n["id"]) for n in board.get("notes") or [] if isinstance(n, dict)
                         and n.get("id") in notes_was and spot(n) != spot(notes_was[n["id"]]))
    return counted({"labels_changed": labels, "cards_changed": sorted(changed), "cards_lost": sorted(lost),
                    "cards_added": added, "cards_moved": moved, "labels_moved": labels_moved, "notes_moved": notes_moved,
                    "cells_changed": cells,
                    "cards_renamed": [[k, v] for k, v in sorted(rename.items()) if k in cards_was]})


def rename_line(case: str, ident: str, rename: dict[str, str]) -> str:
    """A statement's line key as the take gives its card, the key itself when its card does not move."""
    key = card_of(case, "es", ident)
    return split_key(rename.get(key, key))["ident"]


def quotes_followed(case: str, old: dict, fresh: dict) -> dict[str, str]:
    """Where each quote of a case's copy goes when its changes are taken (takefix, 16 November 2026), by its key,
    `<sheet>:<row>:<place>`: a statement's own quote stands at its line's place, so one whose words moved to another
    line, as `lines_followed` finds them, moves with it, and only when the quote's words there are the same. A
    quote whose key still holds its words stays, and one whose words are nowhere stays too. Answers each that
    moves."""
    old_lines, new_lines = old.get("lines") or {}, fresh.get("lines") or {}
    follow = {split_key(k)["ident"]: split_key(v)["ident"] for k, v in
              lines_followed(case, {card_of(case, "es", k): {} for k in old_lines}, old_lines, new_lines).items()}
    out = {}
    for ident, to in follow.items():
        was = quote_at(old, ident)
        if was is None or (quote_at(fresh, ident) or {}).get("text") == was["text"]:
            continue
        if (quote_at(fresh, to) or {}).get("text") == was["text"]:
            out[ident] = to
    return out


def keys_followed(board: dict, case: str, rename: dict[str, str], qmap: dict[str, str]) -> None:
    """A board's keys of a case moved where a take gives them new ones (takefix, 16 November 2026), everywhere the
    board names them, as `board_remapped` moves a case's keys: its cards by `rename`, its labels' members, the bin,
    the stacks, Not the same, the AI's reasons and the picks, and the rows' ticked quotes of the case by `qmap`, his
    bold kept with each. So a card that follows its PET or its statement keeps its stack, its pick and its key quote.
    In place."""
    m = lambda k: rename.get(k, k) if isinstance(k, str) else k  # noqa: E731
    if rename:
        board["cards"] = {m(k): c for k, c in (board.get("cards") or {}).items()}
        for g in board.get("groups") or []:
            if isinstance(g, dict):
                g["members"] = [m(x) for x in g.get("members") or []]
        if isinstance(board.get("discarded"), list):
            board["discarded"] = [m(k) for k in board["discarded"]]
        if isinstance(board.get("stacks"), dict):
            board["stacks"] = {m(t): [m(k) for k in under or []] for t, under in board["stacks"].items()}
        if isinstance(board.get("not_same"), list):
            board["not_same"] = [[m(a), m(b)] for a, b in board["not_same"]]
        if isinstance((board.get("ai") or {}).get("discarded"), dict):
            board["ai"]["discarded"] = {m(k): why for k, why in board["ai"]["discarded"].items()}
        if isinstance(board.get(themes.WHY), dict):
            board[themes.WHY] = {m(k): why for k, why in board[themes.WHY].items()}
        if isinstance(board.get("picks"), dict):
            board["picks"] = {g: [m(k) for k in chosen or []] for g, chosen in board["picks"].items()}
    for cases in (board.get("rows") or {}).values() if isinstance(board.get("rows"), dict) else ():
        row = cases.get(case) if isinstance(cases, dict) else None
        if isinstance(row, dict) and row.get("quote") in qmap:
            row["quote"] = qmap[row["quote"]]


def carried(board: dict, moved: list[str]) -> set[str]:
    """The labels and sticky notes `make_room_below` moved on a board, each label with the labels and the notes it
    holds, as `themes.push_clear` shifts them."""
    by_id = {g["id"]: g for g in board.get("groups") or [] if isinstance(g, dict) and g.get("id")}
    out: set[str] = set()
    for item in moved or []:
        labels, _cards, notes = themes._block(by_id, board, item)
        out |= set(labels) | set(notes)
    return out


def structure_changes(was: dict, board: dict, case: str, rename: dict[str, str], qmap: dict[str, str], effects: dict,
                      titled=(), pushed=()) -> dict[str, list[str]]:
    """What a take changed of a board's own structure (see `take`), by kind and key, never a word, empty when it
    kept it: the board as it was with the take's new keys followed through it (`keys_followed`) set against the
    board now. `labels`, a label's title, description, domain, note, members in order or place, a label in `pushed`
    (moved down to make room, see `carried`) allowed its new place; `bin`; `picks`; `key_quotes`, a row's key quote,
    bold, state or note, `<label>/<case>`; `notes`, a sticky note, one in `pushed` allowed its new place; `stacks`;
    `board`, its name or note; and `cards`, a card gone, come in other than into the pile, or changed other than in
    place for a card moved down to make room, or in words for a card whose PET has gone, given its title, `titled`."""
    want = json.loads(json.dumps(was))
    keys_followed(want, case, rename, qmap)
    out: dict[str, list[str]] = {}

    def add(kind: str, key) -> None:
        if str(key) not in out.setdefault(kind, []):
            out[kind].append(str(key))

    def placed(x: dict, free: bool) -> dict:
        return {k: v for k, v in x.items() if not (free and k in ("x", "y"))}

    for kind, field in (("labels", "groups"), ("notes", "notes")):
        then = [x for x in want.get(field) or [] if isinstance(x, dict)]
        now = [x for x in board.get(field) or [] if isinstance(x, dict)]
        by_id = {x.get("id"): x for x in now}
        for i in {x.get("id") for x in then} ^ set(by_id):
            add(kind, i)
        for x in then:
            y = by_id.get(x.get("id"))
            if y is not None and placed(x, x.get("id") in pushed) != placed(y, x.get("id") in pushed):
                add(kind, x.get("id"))
        if not out.get(kind) and [x.get("id") for x in then] != [x.get("id") for x in now]:
            add(kind, "order")
    if (want.get("discarded") or []) != (board.get("discarded") or []):
        for k in sorted(set(want.get("discarded") or []) ^ set(board.get("discarded") or [])) or ["order"]:
            add("bin", k)
    for kind, field in (("picks", "picks"), ("stacks", "stacks")):
        a, b = want.get(field) or {}, board.get(field) or {}
        for k in sorted(set(a) | set(b)):
            if a.get(k) != b.get(k):
                add(kind, k)
    ra, rb = want.get("rows") or {}, board.get("rows") or {}
    for gid in sorted(set(ra) | set(rb)):
        ca, cb = ra.get(gid) or {}, rb.get(gid) or {}
        for c in sorted(set(ca) | set(cb)):
            if ca.get(c) != cb.get(c):
                add("key_quotes", f"{gid}/{c}")
    for f in ("name", "note"):
        if want.get(f) != board.get(f):
            add("board", f)
    cards_was, cards_now = want.get("cards") or {}, board.get("cards") or {}
    for k in sorted(set(cards_now) ^ (set(cards_was) | set(effects["cards_added"]))):
        add("cards", k)
    moved = set(effects["cards_moved"])
    back = {rename.get(k, k): k for k in was.get("cards") or {}}
    for k, c in cards_was.items():
        if k not in cards_now:
            continue
        then, now = placed(c, k in moved), placed(cards_now[k], k in moved)
        if back.get(k, k) in titled and not then.get("text"):
            now.pop("text", None)
        if then != now:
            add("cards", k)
    return {k: v for k, v in out.items() if v}


def structure_kept(was: dict, board: dict, case: str, rename: dict[str, str], qmap: dict[str, str], effects: dict,
                   titled=(), pushed=()) -> bool:
    """Whether a take kept a board's own structure (see `structure_changes`)."""
    return not structure_changes(was, board, case, rename, qmap, effects, titled, pushed)


# the kinds a refused take names, in the order its line says them, each its own line of the catalogue
TAKE_KINDS = {"labels": lambda: i18n.t("server.take_kind_labels"), "cards": lambda: i18n.t("server.take_kind_cards"),
              "bin": lambda: i18n.t("server.take_kind_bin"), "picks": lambda: i18n.t("server.take_kind_picks"),
              "stacks": lambda: i18n.t("server.take_kind_stacks"),
              "key_quotes": lambda: i18n.t("server.take_kind_key_quotes"),
              "notes": lambda: i18n.t("server.take_kind_notes"), "board": lambda: i18n.t("server.take_kind_board")}


def differs_said(differs: dict[str, list[str]], most: int = 12) -> str:
    """What a refused take would have changed, by kind and key and never a word, in a line: `labels G1, G2; cards
    T1/g4`, the first `most` of each and how many more."""
    parts = []
    for kind, said in TAKE_KINDS.items():
        keys = differs.get(kind) or []
        if keys:
            more = i18n.t("server.take_and_more", n=len(keys) - most) if len(keys) > most else ""
            parts.append(said() + " " + ", ".join(keys[:most]) + more)
    return "; ".join(parts)


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


def shown_twice(board: dict, data: dict) -> list[dict]:
    """The statement cards on a GETs, LPETs or LGETs board whose statement the board shows a second time, inside a
    PET's or a sub-theme's card of the same case (an LPET's on LGETs), its own or a PET's over it, which carries
    its sub-themes, a second card of that PET among them (lpetsaside, 17 November 2026, found on a participant's
    LPETs where an agent brought in statements their PETs' cards held already). Cards set aside are passed over,
    as the canvas shows neither. Each by its key: `card`, `case`, `also`, the cards that hold it too, and `label`,
    the label it stands in, or None for one in none. Keys alone, never a word."""
    held = data.get("cases") or {}
    cards = board.get("cards") or {}
    aside = set(board.get("discarded") or [])
    parents = themes.parents_of(board.get("groups") or [])
    groups = {}
    for key in cards:
        k = split_key(key)
        if k["kind"] == "group" and key not in aside:
            groups.setdefault((k["case"], k["ident"]), []).append(key)
    out = []
    for key in cards:
        k = split_key(key)
        rec = held.get(k["case"])
        if k["kind"] != "es" or key in aside or not isinstance(rec, dict):
            continue
        pets = {p.get("id"): p for p in rec.get("pets") or [] if isinstance(p, dict)}
        # each label's owner, from its own `parent` or from the `subs` of the one that lists it, so a sub-theme's
        # card counts whichever of the two the copy carries (asidefix, 17 November 2026)
        owner = {s: pid for pid, pet in pets.items() for s in pet.get("subs") or [] if s in pets}
        chain = []
        holders = [p for p, pet in pets.items() if k["ident"] in (pet.get("statements") or [])]
        # a statement stacked under another on the PETs board stands in the label its top does, and no label's
        # `statements` lists it: its line names that label (asidefix, 17 November 2026, a participant's T1 9:1)
        line = (rec.get("lines") or {}).get(k["ident"])
        if isinstance(line, dict) and line.get("pet") in pets and not line.get("discarded") and line["pet"] not in holders:
            holders.append(line["pet"])
        for pid in holders:
            while pid is not None and pid not in chain:
                chain.append(pid)
                pid = (pets.get(pid) or {}).get("parent") or owner.get(pid)
        also = sorted(c for pid in chain for c in groups.get((k["case"], pid), []))
        if also:
            out.append({"card": key, "case": k["case"], "also": also, "label": parents.get(key)})
    return sorted(out, key=lambda x: x["card"])


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
    else the one it starts with, and on a participant's LPETs the one he ticked alone, none standing in until he
    ticks one (Adam's ruling of 17 November 2026, drawswordfix), and his note for the row. `counted` says whether anything of the
    case's counts there, a participant note never. Reads the file alone, and writes nothing."""
    kept = normal(board, data)
    shown = named(kept, data)
    drawn = themes.layout_boxes(shown, card_height)
    by_id = {g["id"]: g for g in kept["groups"]}
    parents = themes.parents_of(kept["groups"])
    held = data.get("cases") or {}
    cases = sorted(inside, key=case_order)
    lpets_now = in_lpets()
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
                         "quote": chosen or (None if lpets_now else first_quote(items, rec)), "chosen": chosen is not None,
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
    themes.drop_history(board)
    kept = normal(board, data, hide=False)
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
# quote he ticked is its key quote, none until he ticks one (Adam's ruling of 17 November 2026, drawswordfix: the
# first no longer stands in), and `bold` his bold in it. Run
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


def quote_bold(said, bold) -> list[tuple[str, bool]]:
    """A key quote's words as the LPET table's print view and PDF set them, without the marks the workbook keeps
    round them, in runs, each with whether his bold is on it (lpetmarks, 12 November 2026): his spans are kept
    against the quote as the row keeps it, so each is moved past the marks it lost (`quote_cut`), as Trajectories
    shows it. A quote with no bold is one run."""
    text, cut = quote_cut(said)
    marked = [False] * len(text)
    for a, b in spans_kept(bold):
        for i in range(max(0, a - cut), min(len(text), b - cut)):
            marked[i] = True
    runs: list[list] = []
    for ch, on in zip(text, marked):
        if runs and runs[-1][1] == on:
            runs[-1][0] += ch
        else:
            runs.append([ch, on])
    return [(t, on) for t, on in runs]


def book_turns(book):
    """A participant's transcript turns at a timepoint by its key, T2, as `passage_found` reads them: the workbook
    read once while it is unchanged. A workbook that cannot be read has none, so a passage kept from it falls back."""
    def turns(at: str) -> list[dict]:
        try:
            return [t for t in themes.transcript_turns(Path(book)) if f"T{t['at']}" == at]
        except (WorkbookError, OSError):
            return []
    return turns


def passage_cells(data: dict, board: dict | None, turns, bare: bool = True) -> dict:
    """The key quotes the LPET table shows that were taken from the transcript on Trajectories (lpetgaps,
    12 November 2026), by LPET and then timepoint: `{"quote": {"key", "text", "time", "sheet"}, "bold"}`, the quote
    as `lpet_rows` gives it with the time Trajectories gives it, read where Trajectories keeps it, the row's
    `passage`. A passage whose words are gone is left out, and the row shows its first quote as before. With
    `bare` the words come without the marks the workbook keeps round them and his bold is moved to match, as the
    page draws them, else both as the row keeps them, for `quote_bold` to move. Reads alone."""
    if board is None:
        return {}
    out: dict = {}
    for gid, cases in normal(board, data)["rows"].items():
        for case, stored in cases.items():
            found = passage_found(stored.get("passage"), turns) if stored.get("passage") else None
            if not found:
                continue
            cite = cite_of(data, found["at"])
            text, bold = found["text"], stored.get("bold") or []
            if bare:
                text, cut = quote_cut(text)
                bold = [[max(0, a - cut), min(len(text), b - cut)] for a, b in bold]
            out.setdefault(gid, {})[case] = {
                "quote": {"key": "", "text": text, "sheet": "", "time": f"{cite}, {found['time']}" if found["time"] else cite},
                "bold": [s for s in bold if s[0] < s[1]]}
    return out


def lpet_domains(data: dict, board: dict | None) -> list[str]:
    """Each LPET's domain on `board` as it keeps it, "" for none, in the order the LPET table reads them, the order
    `lpet_rows` gives its rows (lpetmarks): read without the table's cells, so every participant's can be read
    cheaply for the domains' colours (`trajectories.domain_colours`)."""
    if board is None:
        return []
    kept = normal(board, data)
    by_id = {g["id"]: g for g in kept["groups"]}
    parents = themes.parents_of(kept["groups"])
    tops = themes.canvas_order([g["id"] for g in kept["groups"] if g["id"] not in parents], by_id)
    return [str(by_id[gid].get(themes.DOMAIN) or "") for gid in tops]


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
    round them, none clearing it, refused on a cell with no key quote), `domain` (`lpet`, `domain`, several
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
    if kind == "why":
        return why_op(data, board, tp(), labels, op, name)
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
    # bold, on the quote he ticked, none standing in since 17 November 2026 (drawswordfix)
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


def why_op(data: dict, board: dict, key: str, labels: dict, op: dict, name: str) -> list[str]:
    """`why`: his reason a PET or a sub-theme of the timepoint `key` is drawn on by no LPET (drawsword, 17 November
    2026), `pet` by its id at that timepoint, g3, or its title, `why` the words, "" taking it off, kept on the card in
    Unplaced. Refused, nothing changed, for a PET the timepoint's copy has not got, and, but for "", which is always
    taken (drawswordfix), one whose card is not on the board, one an LPET draws on, wholly, through a larger card or
    in part, and a board other than the one LGETs take, the one `board drawn-on` reads. Answers its line, the PET by
    its id and title, never his words."""
    rec = (data.get("cases") or {}).get(key) or {}
    pets = [p for p in rec.get("pets") or [] if isinstance(p, dict) and p.get("id")]
    given = " ".join(str(op.get("pet") or "").split())
    at = tp_names(labels, key)[0]
    pet = next((p for p in pets if p["id"] == given), None) or next(
        (p for p in pets if " ".join(str(p.get("title") or "").split()).lower() == given.lower()), None)
    if pet is None or not given:
        raise WorkbookError(i18n.t("server.lpets_why_no_pet", name=name, pet=given or "none", timepoint=at))
    card = card_of(key, "group", pet["id"])
    text = str(op.get("why") if op.get("why") is not None else "").replace("\r\n", "\n").replace("\r", "\n").strip()
    # "" takes a reason off wherever it is, drawn on or not (drawswordfix)
    if text:
        source = source_board(data)[0]
        if source is not None and str(source.get("id")) != str(board.get("id")):
            raise WorkbookError(i18n.t("server.lpets_why_not_source", name=name,
                                       source=str(source.get("name") or source.get("id"))))
        if card not in (board.get("cards") or {}):
            raise WorkbookError(i18n.t("server.lpets_why_not_on_board", name=name, pet=pet["title"], timepoint=at))
        drawing = drawn_on(data, board, key)["pets"].get(pet["id"]) or []
        lpets = ", ".join(f"'{d['title']}'" for d in drawing)
        if len(drawing) > 1:
            raise WorkbookError(i18n.t("server.lpets_why_drawn_on_many", pet=pet["title"], timepoint=at, lpets=lpets))
        if drawing:
            raise WorkbookError(i18n.t("server.lpets_why_drawn_on", pet=pet["title"], timepoint=at, lpets=lpets))
    if len(text) > themes.WHY_MOST:
        raise WorkbookError(i18n.t("server.lpets_why_long", most=themes.WHY_MOST))
    held = board.get(themes.WHY) if isinstance(board.get(themes.WHY), dict) else {}
    if text == (held.get(card) or ""):
        return []
    if text:
        held[card] = text
    else:
        held.pop(card, None)
    if held:
        board[themes.WHY] = held
    else:
        board.pop(themes.WHY, None)
    return [f"{name}'s PET {pet['id']} '{pet['title']}' at {at}: reason no LPET draws on it "
            + ("set." if text else "taken off.")]


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
