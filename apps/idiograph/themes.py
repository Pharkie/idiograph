#!/usr/bin/env python3
"""Themes: the IPA step after the statements, grouping a case's experiential statements into
personal experiential themes on a canvas.

One card per experiential statement: every entry of column C, on every sheet, keyed by sheet, row
and line. The workbook is only ever read here, and read the way Excel leaves it, so a workbook
Excel has open is read like any other and nothing is said about it. Nothing in this module opens a
workbook for writing.

What he does with the cards lives in a themes file beside the progress file,
`<case>/Working/<stem>.themes.json`:

    {"schema": 2, "case": "P2 - Rowan", "workbook": "P2 Rowan - EN & ES.xlsx",
     "created": "...", "updated": "...", "current": "v1", "chosen": "v2",
     "complete": {"at": "...", "board": "v2", "name": "Board 2"},
     "boards": [{"id": "v1", "name": "Board 1", "note": "", "created": "...", "updated": "...",
                 "cards": {"Initial:12:0": {"x": 40, "y": -120, "text": "..."}},
                 "groups": [{"id": "g1", "label": "...", "members": ["Initial:12:0", "g2"],
                             "x": 40, "y": -160}],
                 "discarded": ["Initial:30:1"],
                 "stacks": {"Initial:12:0": ["Initial:13:0", "Initial:13:1"]},
                 "not_same": [["Initial:14:0", "Initial:15:0"]],
                 "picks": {"g1": ["Initial:12:0"]},
                 "notes": [{"id": "n1", "text": "merge with Mornings?", "colour": "yellow",
                            "x": 260, "y": -120, "in": "g1"}],
                 "quoted": {"Initial:12:0": "the words of the quote"},
                 "cut": [{"trim": "<trim id>", "cards": {...}, "members": {"g1": [...]},
                          "discarded": [...], "picks": {"g1": [...]}}],
                 "history": [{"id": "r1", "at": "...", "name": "", "auto": true,
                              "kind": "before_restoring", "slots": {"when": "12:04"},
                              "state": {"cards": {...}, "groups": [...], "discarded": [...],
                                        "picks": {...}, "quoted": {...}}}]}]}

`current` is the board on the canvas. `chosen` is the Current board, the one he is going with,
the one to send a supervisor, set and cleared only through the `choose` op, and through `delete`,
which gives it to the last board left when the Current board goes, never by a save, and a file
with none marked carries none. `complete` is the PETs phase marked complete, set by the
`complete` op on the Current board, naming that board and its name, and taken off by `reopen`. It
stays as it stands when that board is unmarked or deleted, and a file with no mark carries none.

`case` is the case by its pseudonym: a folder named `P<n> - Pseudonym-Secondname` is written as
`P<n> - Pseudonym`, so the cross-case step can name it and the second name never reaches the file.
A group's members are card keys or the ids of other groups, so a label over labels is the same
object one layer up. Membership is stored, never worked out from where a card sits. The screen
names a label by its layer (see `layer`): a PET at the top, a sub-theme inside a PET, and a group
inside a sub-theme, with groups inside groups as deep as he likes. A board from before the layers
had names reads the same way and keeps everything it holds. A group may
carry a `note`, his own words on why the theme exists, and a group with none carries none. A group may
carry a `description` too (Adam, 21 October), the longer line under its short title that shows as a
secondary heading on the board, in the Table view and on the printouts, a field of its own apart from
the note, and a group with none carries none. A board's
picks are the quotes ticked for a label, each keyed by sheet, row and its place among the row's
quotes, `Initial:12:0`, and only a quote of a row with a card under that label can be one. A
label takes as many as he picks, each once (see `picks_kept`).
`quoted` holds the words of every quote the picks name, written by the server on every save, so a
pick can follow its words when the quotes of its row move.

`stacks` are the statements stacked under a better one (Adam, 19 October): one point said several
ways close together in the transcript, kept under the statement that says it best, the top, which
stands for them in the PETs table and the exports. Each top names the statements stacked under it,
in their order. A stacked statement is in no group and not in the bin: it goes where its top goes,
into a PET, Not placed or the bin, and the exports leave it out unless asked (see `stacked_keys`).
A board with none carries none, so a file from before them reads and writes as it did.

`not_same` are the close pairs he has marked Not the same (Adam, 20 October): two statements in one
group from one passage of one sheet that say different things, so the board stops marking them as a
pair (see `close_pairs`). Each is the two keys in transcript order, and a board with none carries none.

`notes` are his sticky notes on the canvas, his own words to himself, "not sure about this". A note is
never a statement and never a member: it keeps its text, its colour, yellow, pink, green or blue, and
its place, and `in` names the group it sits in, a note in no group carrying none. It goes nowhere a
statement goes, the counts, the PET draft, the CSV, the print view, the outline or a prompt, and a
board with none carries none, so a file from before them reads and writes as it did.

The themes file moves with the rows. A trim, its undo, an assignment and its undo re-key every
board and every revision through `rekey`, with the row map the progress file is moved by. A card on
a row a trim cut goes under the board's `cut` list with the trim's id, where it sat and its picks,
and the trim's undo puts it all back.

The file holds named boards side by side, one of them current: a new one with every card back in
the pile, a copy of one under a new name, a rename, a note on why, a switch and a delete, which
never takes the last. A theme can be copied from one board to another. A board can be exported as
a markdown PET draft beside the progress file, and its labels fill the Proposed PET column of the
statements CSV. Schema 1 held them under `versions`, named Version 1 and AI proposal 1, and a file
of that shape is read as boards in memory and written as schema 2 on its next save.

Each board carries its history, the revisions of it kept as he works: one by hand when he asks,
one automatically every fifteen minutes of work when the board has changed since the last, one
before a restore and one before a theme is copied in. Every revision but the automatic ones is
kept, and the last 48 automatic ones. A revision holds the board's cards, groups, discards, picks
and the AI's reasons as the file holds them, written on one line of its own.

Every open reads column C afresh and merges it with the stored board, words before index: a stored
card whose key no longer carries its words takes the key of a live line with the same words, on
its row first and then anywhere on its sheet. Only then is a stored card whose line reads
differently marked changed, a stored card whose line has gone marked missing, and a new line given
a new card in the nearest free spot to the middle. A pick follows its words the same way, on its
row, else on a row with a card under its label, the inverted commas round a quote set aside, so a
quote put in them or taken out of them keeps its picks. Nothing overlaps, and every
card and label keeps its margin clear, a twentieth of a card's width: the first pile is packed in
rows inside a circle, the margin between cards, in an order seeded from the keys, so a case opens
the same way every time until he moves something.

Inside a theme, higher means a better example. The PET draft, the print view and the CSV list a
theme's statements in the order the canvas reads them, top to bottom and left to right along a row.
The CSV puts a sub-theme's where its frame's top sits among the cards, and the draft and the print
view set a sub-theme after its theme's own statements.
"""
from __future__ import annotations

import contextlib
import contextvars
import difflib
import functools
import hashlib
import json
import math
import os
import re
import unicodedata
from datetime import datetime
from pathlib import Path

import openpyxl

import formats
import i18n
from workbook import (WorkbookError, detect_columns, interviewer_name, note_written, quote_entries, quote_pieces,
                      quote_reach, quote_turns, split_entries, time_span, timecode, timecodes_for, ts_seconds)

SCHEMA = 2
# A board's id is the file's own and never shown. The first is `v1`, from the time the boards were
# versions, and ids stay as they were so a file read from schema 1 keeps them.
FIRST_VERSION = "v1"
FIRST_NAME = "Board 1"
BOARD = "Board"
UNTITLED = "Untitled"
# a binned card's word, in the CSV's Proposed PET column and where a GETs line stood, and the heading
# of the bin's part at the end of the print view, the Word document and the PET draft, in the words of
# its tick (Adam, 19 October, it read Discarded until then). The data keys stay `discarded`.
DISCARDED = "Set aside"
# The board's sidebar (Adam, 20 October, way A): a statement in no PET waits in the sidebar's Not placed,
# off the canvas, until he puts it on the board, where it lies `loose`, placed but in no PET yet. A card
# that carries `loose: true` is on the canvas, and one in no PET without it waits, so a board from before
# keeps everything it held in no PET waiting in the sidebar, and reads and writes as it did. What the
# bin held, `discarded`, is Set aside, the key kept. `start` of a new board: every statement waiting in
# the sidebar, or every statement on the canvas as a pile in the middle
LOOSE = "loose"
SET_ASIDE = "Set aside"
STARTS = ("empty", "canvas")
OPS = ("new", "duplicate", "rename", "note", "switch", "delete", "choose", "complete", "reopen")
# A board laid out whole by the server arrives as a board of its own, through the same op as the rest,
# so the file stays one shape: an agent's board make and a REFI-QDA import. The board menu never asks
# for it.
PROPOSE = "propose"
# What a board can do with its themes and its history, through `/api/themes-boards`: copy a theme
# to another board, keep a revision by hand, show one, and restore one.
BOARD_OPS = ("copy", "revision", "view", "restore")
AUTO_KEEP = 48       # the automatic revisions a board keeps, the oldest going past it
# What the app's own AI left with a board before 11 November 2026, when its AI boards, reviews and
# revisions went (aiout): `review`, a board's review rounds, and `revise`, its revise thread. Neither is
# read: each is carried as the file holds it, so a board that has one opens and saves as any other.
FROM_BEFORE = ("review", "revise")
REQUEST_TEXT = 2000  # the longest his request in an agent's mark runs
# What an AI agent in a conversation did to a board, through the command line: `made`, the board it
# made, and `changed`, the last change it made to a board, each `{"by": "agent", "tool", "request",
# "at"}`. The page never sends either, so a save keeps the file's. `made` keeps `hash`, the board's
# state hash when it was made, and `edited`, the time of his first save that changed it.
AGENT_KEYS = ("made", "changed")
# what a change made by a teammate's suggestion, accepted by its owner, keeps beside `by: "member"` (wtsuggest)
MEMBER_KEYS = ("member", "accepted_by", "suggestion")
# what the board menu says after the name of a board an agent made, once he has changed it
EDITED = "edited by you since"
# an agent's board from before `made`, read from its note: "Made by Claude Code in a conversation on ..."
AGENT_NOTE = re.compile(r"^Made by (?P<tool>.+?) in a conversation on \d")
# a save from a page that last saw a board before an agent changed it keeps the page's canvas as a
# revision of this name, and leaves the board as the agent left it
CANVAS_KEPT = ""  # set below, from REVISION_SAID
# A save carries the board's version, `v`, as the page last read it, and a write from the command
# line may carry it as the agent read it (19 October). `v` is a hash of the board as the file holds
# it, its history aside (see `board_version`), worked out on every read and never written, so two
# writes within one second, which share an `updated`, still differ. One over a board that holds another
# version now is refused with nothing written: STALE_PAGE is the page's line, STALE_WRITE an agent's.
STALE_WRITE = (i18n.t("server.board_changed_since_read_app"))


class StaleBoard(WorkbookError):
    """A save or a write over a board changed since it was read: `board` its id, `now` its version now."""

    def __init__(self, message: str, board: str, now: str):
        super().__init__(message)
        self.board = board
        self.now = now

    def view(self) -> dict:
        return {"board": self.board, "v": self.now}


def board_version(board: dict) -> str:
    """A board's version: a hash of it as the file holds it, its history and any `v` a page sent aside."""
    held = {k: value for k, value in board.items() if k not in ("history", "v", OWN)}
    return hashlib.sha1(json.dumps(held, sort_keys=True, ensure_ascii=False).encode("utf-8")).hexdigest()[:16]


def stale_since(board: dict | None, seen) -> bool:
    """Whether `seen`, a board's version as a page or an agent read it, is not the board's version
    now, `board` as the file holds it. A save or a write that carries none, a page from before
    versions among them, is never held up."""
    said = str(seen or "").strip()
    return bool(said) and isinstance(board, dict) and said != board_version(board)


# Reload on the refused save's card keeps the page's canvas in the board's History under this name
# first, so the work on it is one Restore away
RELOAD_KEPT = ""  # set below, from REVISION_SAID


def keep_before_reload(board: dict, state: dict, at: str) -> dict:
    """The page's canvas kept in a board's History as RELOAD_KEPT, the board itself left as it is."""
    return add_revision(board, name=revision_name("reload_kept"), at=at, state=state)


def refuse_stale(board: dict, seen, message: str) -> None:
    """StaleBoard raised when `seen` is not `board`'s version now (see `stale_since`)."""
    if stale_since(board, seen):
        raise StaleBoard(message, str(board.get("id") or ""), board_version(board))

# The canvas's own measures, estimated here the way the page draws them, for a layout made before
# the page has measured anything: the first pile, a new card's place, a board laid out whole and a copy.
# A card is 200px wide and as tall as its lines, four at most. The page measures the real ones, and
# each estimate here is a little over the page's and within a margin of it, so a frame laid out here
# holds the frame the page draws and a layout made here needs no shift there.
CARD_W = 200
CARD_H = 80          # a card's nominal height, for reading the canvas row by row
CARD_TEXT_W = 176    # the room for a card's words, inside its padding and its border
CARD_TEXT_PX = 14.5  # a card's statement in the serif
# The margin every card and every label always keeps clear round it, a twentieth of a card's width,
# 10px on a 200px card. One measure everywhere: the first pile, a drop, a nudge, a card put back, a
# new card, the AI's layout and an arrange. The page's TH_MARGIN is the same number.
MARGIN = CARD_W // 20
# A theme copied onto a board stands four margins clear of everything there, the space the AI's
# layout leaves beside its pile: the sizes here are estimates, and a label as the page draws it can
# run a little wider than its estimate, so the copy's frame and its neighbours' never meet.
COPY_GAP = 4 * MARGIN
ROW_BAND = CARD_H // 2   # reading a theme row by row: tops within half a card's height share a row
LABEL_GAP = 8        # between a label and the top of what it holds
LABEL_W = 340        # the widest a label runs before its title wraps
LABEL_CHROME = 73    # a label's padding, swatch, Auto-arrange and cross, with the gaps between them
LABEL_MARK = 20      # a mark on a label, its note's or its picks', with the gap before it
LABEL_PX = 17.5      # a label's title in the serif, and 21px on a label over labels
# A label's description (Adam, 21 October): a line of its own under the title, four fifths of the title's size,
# six lines at most on the board since 31 October (two before), the rest in its tooltip. A label with one runs
# as wide as what it holds, where that is wider than LABEL_W. The page's .th-desc and thLabelsWiden are the same.
DESCRIPTION = "description"
DOMAIN = "domain"
DESC_SCALE = 0.8
DESC_LEADING = 1.3
DESC_LINES = 6
DESC_GAP = 2
# An LPET's domains on its label on the LPETs screen (lpetmarks, 12 November 2026): a row of pills under its title
# and its description, each word at 11px in the sans inside its padding and border, as Trajectories draws them,
# wrapping as the words need. The page's .th-domains and .tf-pill are the same, each width here taken a tenth over.
PILL_H = 20
PILL_GAP = 4
PILL_PX = 11
PILL_PAD = 20
# Each character's width in the serif the page draws a title and a statement in, Iowan Old Style,
# at 17.5px, measured in the page. A character the table lacks is taken by its letter without its
# accent, and failing that as wide as the widest there. A count is in the code face, every character
# as wide as the next. Every width is taken 1% over, so a line here breaks no later than the page's.
_SERIF = dict(zip("abcdefghijklmnopqrstuvwxyz", (
    8.42, 9.73, 7.82, 9.84, 8.54, 5.45, 9.03, 10.25, 5.2, 4.79, 9.55, 5.11, 15.4,
    10.22, 9.64, 9.8, 9.77, 6.83, 7.75, 6.3, 10.29, 8.6, 13.56, 9.27, 8.5, 8.26)))
_SERIF.update(zip("ABCDEFGHIJKLMNOPQRSTUVWXYZ", (
    13.04, 10.89, 12.37, 13.66, 11.09, 10.24, 12.99, 13.89, 5.95, 5.81, 12.13, 10.01, 15.93,
    14.14, 14.03, 10.31, 14.03, 12.3, 9.47, 11.04, 13.77, 12.54, 18.15, 12.44, 11.54, 11.67)))
_SERIF.update(dict.fromkeys("0123456789#$", 9.73))
_SERIF.update({" ": 4.86, "!": 5.9, '"': 5.79, "'": 2.97, "(": 7.33, ")": 7.33, "[": 7.33, "]": 7.33,
               ",": 4.86, ".": 4.86, ":": 4.86, ";": 4.86, "-": 6.13, "/": 8.07, "?": 8.23, "*": 7.95,
               "&": 14.54, "%": 15.4, "+": 14.58, "=": 14.58, "’": 4.86, "‘": 4.86, "“": 8.3, "”": 8.3,
               "\u2013": 8.75, "\u2014": 17.5, "…": 17.5, "·": 4.86})
_SERIF_WIDEST = 18.15
_SLACK = 1.01
FRAME_X = 14         # a theme's frame, round its label and its members
FRAME_Y = 12
# A sticky note as the page draws it: 160px wide and square-ish, growing with its words, set in a
# handwriting face from the system. Its height is estimated the way a card's is, each width taken a
# fifth over the serif's, since the face is whichever the machine has, so the estimate stays over
# the page's.
NOTE_COLOURS = ("yellow", "pink", "green", "blue")
NOTE_W = 160
NOTE_TEXT_W = 136    # inside its padding
NOTE_PX = 16
NOTE_LINE = 21
NOTE_PAD = 26
NOTE_MIN_H = 140
NOTE_SLACK = 1.2
# the layers of a PETs board, a label's name by its depth: a PET at the top, a sub-theme inside a PET
# and a group at any depth below a sub-theme
LAYERS = ("PET", "sub-theme", "group")


# ------------------------------------------------------------------ the file

# The timepoint a request's boards are at (21 October, timepoints part 2). In a project of two or more
# timepoints each timepoint of a participant has its own PETs canvas, its boards in a file of their own,
# `<stem>.themes-t2.json` for T2, T1's the file it always was. `scoped(n)` sets it for one request or
# one command, and every reader and writer here goes by it: `themes_path` names that timepoint's file and
# `read_cards` reads that timepoint's sheets alone. With none set it is T1, so a project of one
# timepoint, and every project from before, reads and writes exactly as it did.
SCOPE: contextvars.ContextVar = contextvars.ContextVar("idiograph_timepoint", default=None)
TP_FILE = re.compile(r"\.themes-t(\d+)\.json$")


@contextlib.contextmanager
def scoped(n):
    """The boards of timepoint `n` for what runs inside, T1 for None or 1."""
    token = SCOPE.set(int(n) if n not in (None, "", 1, "1") else None)
    try:
        yield
    finally:
        SCOPE.reset(token)


def timepoint_now() -> int:
    """The timepoint the boards are read and written at, 1 unless `scoped` says later."""
    return SCOPE.get() or 1


def themes_path(workbook: Path, n: int | None = None) -> Path:
    """The themes file, beside the progress file in the case's `Working/` folder, the one of the
    timepoint in scope, or of `n`, a timepoint after T1 its own (see SCOPE)."""
    workbook = Path(workbook)
    n = int(n or timepoint_now())
    tail = ".themes.json" if n <= 1 else f".themes-t{n}.json"
    return workbook.parent / "Working" / f"{workbook.stem}{tail}"


def timepoint_files(workbook: Path) -> list[int]:
    """The timepoints after T1 a participant has a PETs file for, in order."""
    workbook = Path(workbook)
    folder = workbook.parent / "Working"
    out = []
    for file in folder.glob(f"{glob_escape(workbook.stem)}.themes-t*.json") if folder.is_dir() else []:
        m = TP_FILE.search(file.name)
        if m and file.name == f"{workbook.stem}.themes-t{m.group(1)}.json" and int(m.group(1)) >= 2:
            out.append(int(m.group(1)))
    return sorted(set(out))


def glob_escape(text: str) -> str:
    return re.sub(r"([*?\[])", r"[\1]", str(text))


def placed_sheets(workbook: Path) -> dict[str, int]:
    """Each sheet the participant's progress file places at T2 or later, by its name, none in a
    project of one timepoint (see `rounds.sheet_timepoints`). A file that cannot be read places none."""
    path = Path(workbook).parent / "Working" / f"{Path(workbook).stem}.progress.json"
    try:
        held = json.loads(path.read_text(encoding="utf-8")).get("timepoints")
    except (OSError, ValueError, AttributeError):
        return {}
    if not isinstance(held, dict):
        return {}
    return {str(k): v for k, v in held.items() if isinstance(v, int) and not isinstance(v, bool) and v >= 2}


def each_timepoint(fn):
    """A writer that carries a change to a participant's boards, run once for each PETs file they have:
    T1's, then each later timepoint's, when nothing set the timepoint, and for the one in scope when
    something did. Its answers are put together, a count added, a list joined, True when any was."""
    @functools.wraps(fn)
    def run(workbook, *args, **kwargs):
        if SCOPE.get() is not None:
            return fn(workbook, *args, **kwargs)
        out = fn(workbook, *args, **kwargs)
        for n in timepoint_files(workbook):
            with scoped(n):
                more = fn(workbook, *args, **kwargs)
            if isinstance(out, bool):
                out = out or bool(more)
            elif isinstance(out, (int, float)):
                out += more
            elif isinstance(out, list):
                out = out + list(more or [])
        return out
    return run


def at_sheet_timepoint(fn):
    """A writer that carries one passage's change to the boards, run on the boards of the timepoint the
    passage's sheet is at when nothing set the timepoint, its second argument the sheet."""
    @functools.wraps(fn)
    def run(workbook, sheet, *args, **kwargs):
        if SCOPE.get() is not None:
            return fn(workbook, sheet, *args, **kwargs)
        with scoped(placed_sheets(workbook).get(str(sheet), 1)):
            return fn(workbook, sheet, *args, **kwargs)
    return run


def now_iso() -> str:
    return datetime.now().astimezone().isoformat(timespec="seconds")


# A reviewer's own boards (ownboards, 9 November 2026, Working together). `OWN_FILE`, set by team_board when the routes
# load, names for a participant someone else works on the file this member's own boards of it are kept in at the
# timepoint in scope, apart from the owner's PETs file and never sent with it, and None for every other participant,
# a project worked on alone among them. There `load` gives the owner's boards then his own, each of his marked `OWN`
# in memory alone, and `write` puts his own in that file and refuses any change to the owner's (`write_own`).
OWN_FILE = None
OWN = "own"
# an own board's id starts with this, so it never meets an id of the owner's
OWN_ID = "o"


def own_file(workbook: Path) -> Path | None:
    return OWN_FILE(Path(workbook)) if OWN_FILE is not None else None


def load(workbook: Path) -> dict | None:
    """The themes file as it sits on disk, in the shape this build writes, or None when there is
    none yet. A schema 1 file is read as boards in memory and left on disk as it is.

    A file that is there and cannot be read is refused rather than started afresh, so a save can
    never write a fresh board over a file that can still be recovered by hand.

    For a participant someone else works on, the owner's boards and then this member's own (see `OWN_FILE`).
    """
    data = read_file(themes_path(workbook))
    mine = own_file(workbook)
    return data if mine is None else with_own(data, read_file(mine))


def with_own(data: dict | None, mine: dict | None) -> dict | None:
    """The owner's file with this member's own boards after the owner's, each marked `OWN`, and the board on his
    canvas his file's `current` when it names one of either. The owner's Current board and PETs mark stay his."""
    if data is None and mine is None:
        return None
    theirs = boards_of(data)
    ids = {str(b.get("id")) for b in theirs}
    own = [dict(b, **{OWN: True}) for b in boards_of(mine) if str(b.get("id")) not in ids]
    out = dict(data) if data is not None else {k: v for k, v in mine.items()
                                               if k not in ("boards", "chosen", "complete", "current")}
    out["boards"] = theirs + own
    current = str((mine or {}).get("current") or "")
    if current and current in ids | {str(b.get("id")) for b in own}:
        out["current"] = current
    return out


def read_file(path: Path) -> dict | None:
    """One themes file as `load` reads it."""
    if not path.exists():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        raise WorkbookError(i18n.t("server.could_read_canvas_left_nothing", name=path.name))
    if not isinstance(data, dict):
        raise WorkbookError(i18n.t("server.themes_file_nothing_written", name=path.name))
    return migrate(data)


# Schema 1 named its boards Version 1 and AI proposal 1, and a copy Version 1 copy. Those names
# become Board 1, AI board 1 and Board 1 copy. A name he gave one himself stays as he wrote it.
OLD_NAMES = ((re.compile(r"^Version (\d+)((?: copy(?: \d+)?)?)$"), r"Board \1\2"),
             (re.compile(r"^AI proposal (\d+)((?: copy(?: \d+)?)?)$"), r"AI board \1\2"))
# and the note an AI proposal wrote names the board it was made from the same way
OLD_FROM = ((re.compile(r" from Version (\d+)\b"), r" from Board \1"),
            (re.compile(r" from AI proposal (\d+)\b"), r" from AI board \1"))


def renamed(name: str) -> str:
    """A board's name from schema 1 as this build says it."""
    for pattern, new in OLD_NAMES:
        if pattern.match(name):
            return pattern.sub(new, name)
    return name


def migrate(data: dict) -> dict:
    """A themes file in the shape this build writes. Schema 1 kept the boards under `versions`:
    they move to `boards`, their names said the new way, and `schema` reads 2. Only the copy in
    memory changes, so opening a file never writes it, and the next save writes schema 2."""
    if not isinstance(data, dict) or "boards" in data or not isinstance(data.get("versions"), list):
        return data
    out = {}
    for key, value in data.items():
        if key != "versions":
            out[key] = value
            continue
        boards = []
        for board in value:
            if isinstance(board, dict):
                board = dict(board, name=renamed(str(board.get("name") or "")))
                note = str(board.get("note") or "")
                if note.startswith("Proposed by "):
                    for pattern, new in OLD_FROM:
                        note = pattern.sub(new, note, count=1)
                    board["note"] = note
            boards.append(board)
        out["boards"] = boards
    out["schema"] = SCHEMA
    return out


def boards_of(data: dict | None) -> list[dict]:
    """The boards a file holds, in their order."""
    return [b for b in (data or {}).get("boards") or [] if isinstance(b, dict)]


def render(value, depth: int = 0, rows: bool = False) -> str:
    """The file as JSON a person can read: indented a space a level, as `json.dumps` with `indent=1`
    writes it, except that each revision in a board's history is one line of its own, which keeps
    a long history from running to tens of thousands of lines."""
    inner = " " * (depth + 1)
    if isinstance(value, dict) and value:
        body = ",\n".join(f"{inner}{json.dumps(str(k), ensure_ascii=False)}: {render(v, depth + 1, k == 'history')}"
                          for k, v in value.items())
        return "{\n" + body + "\n" + " " * depth + "}"
    if isinstance(value, list) and value:
        body = ",\n".join(inner + (json.dumps(v, ensure_ascii=False, separators=(",", ":")) if rows
                                   else render(v, depth + 1)) for v in value)
        return "[\n" + body + "\n" + " " * depth + "]"
    return json.dumps(value, ensure_ascii=False)


def write(workbook: Path, data: dict) -> Path:
    mine = own_file(workbook)
    if mine is not None:
        return write_own(workbook, data, mine)
    path = themes_path(workbook)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + ".tmp")
    tmp.write_text(render(data) + "\n", encoding="utf-8", newline="\n")
    os.replace(tmp, path)
    note_written(path)
    return path


def unmarked(board: dict) -> dict:
    return {k: v for k, v in board.items() if k != OWN}


def write_own(workbook: Path, data: dict, mine: Path) -> Path:
    """A participant someone else works on, written on this member's install: his own boards, and the board on his
    canvas, into his own file, and the owner's file left as it is. A change to any of the owner's boards, a board of
    his taken off, or his Current board or PETs mark changed, is the one writer's refusal. An own board whose id is
    not yet one of `OWN_ID`'s takes the next, the canvas following it."""
    held = read_file(themes_path(workbook))
    theirs = {str(b.get("id")): unmarked(b) for b in boards_of(held)}
    boards = [unmarked(b) for b in boards_of(data)]
    kept = {str(b.get("id")): b for b in boards if str(b.get("id")) in theirs}

    def same(a, b) -> bool:
        return json.dumps(a, sort_keys=True, ensure_ascii=False) == json.dumps(b, sort_keys=True, ensure_ascii=False)

    def complete(d: dict | None):
        return (d or {}).get("complete") if complete_of(d) else None

    if set(kept) != set(theirs) or any(not same(kept[k], theirs[k]) for k in theirs) \
            or chosen_of(dict(data, boards=boards)) != chosen_of(held) or not same(complete(data), complete(held)):
        import workbook as wb_mod
        if wb_mod.WRITE_GUARD is not None:
            wb_mod.WRITE_GUARD(Path(workbook))
        raise WorkbookError(i18n.t("server.board_gone_themes_changed"), code="not_yours")
    # renamed in the caller's boards too, so an answer made from them names the id the file holds
    own_in = [b for b in boards_of(data) if str(b.get("id")) not in theirs]
    current = str(data.get("current") or "")
    taken = [str(b.get("id"))[len(OWN_ID):] for b in own_in if str(b.get("id")).startswith(OWN_ID)]
    n = max([int(x) for x in taken if x.isdigit()] + [0])
    for b in own_in:
        if not str(b.get("id")).startswith(OWN_ID):
            n += 1
            was, b["id"] = str(b.get("id")), f"{OWN_ID}{n}"
            current = b["id"] if current == was else current
    own = [unmarked(b) for b in own_in]
    before = read_file(mine) or {}
    out = {"schema": SCHEMA, "case": data.get("case") or before.get("case") or "", "workbook": Path(workbook).name,
           "created": str(before.get("created") or data.get("updated") or now_iso()),
           "updated": str(data.get("updated") or now_iso()), "current": current, "boards": own}
    mine.parent.mkdir(parents=True, exist_ok=True)
    tmp = mine.with_name(mine.name + ".tmp")
    tmp.write_text(render(out) + "\n", encoding="utf-8", newline="\n")
    os.replace(tmp, mine)
    note_written(mine)
    return mine


# ---------------------------------------------------------------- the cards

def card_key(sheet: str, row: int, line: int) -> str:
    """Sheet, row and line. Excel never lets a sheet name carry a colon, so the key splits cleanly."""
    return f"{sheet}:{row}:{line}"


def split_card_key(key: str) -> tuple[str, int | None, int | None]:
    head, _, line = str(key).rpartition(":")
    sheet, _, row = head.rpartition(":")
    try:
        return sheet, int(row), int(line)
    except ValueError:
        return sheet, None, None


def row_key(sheet: str, row: int) -> str:
    return f"{sheet}:{row}"


def read_cards(workbook: Path, explore: bool = False, turns: bool = False, form: str | None = None) -> dict:
    """Every experiential statement in the workbook, one card per entry of column C, in sheet order,
    and the quotes of every row that has any, keyed by sheet and row.

    Opened read-only and never guarded against Excel's lock file: the canvas only reads, so a
    workbook open in Excel is read as it was last saved. Only sheets with a speaker, a timestamp, a
    transcript and a statement column count, the sheets the turn screen draws. A quote is one entry
    of the quotes column as `quote_entries` gives it, keyed by sheet, row and its place there,
    which is its statement's key, and a place holding "(no quote)" carries no quote.

    With `explore`, the answer also carries `explored`, the exploratory notes of every row with a
    statement, keyed by sheet and row, for the GETs screen, which reads the case in the same pass.
    With `turns`, it carries `turns` too, the words of every row with a statement or a quote, keyed
    the same way, for the command line, which shows a statement with its turn.

    Each card's and each quote's `time` is written as `form` says, by default as the project's timecodes
    say (see `workbook.timecode`), and the answer's `timecodes` says which.
    """
    workbook = Path(workbook)
    form = form or timecodes_for(workbook)
    if not workbook.exists():
        raise FileNotFoundError(workbook.name)
    try:
        book = openpyxl.load_workbook(workbook, read_only=True, data_only=True)
    except Exception as exc:
        raise WorkbookError(i18n.t("server.could_read", name=workbook.name, exc=exc))
    sheets, cards, quotes, explored, words_of = [], [], {}, {}, {}
    # in a project of two or more timepoints the sheets of the timepoint in scope alone (see SCOPE)
    placed, here = placed_sheets(workbook), timepoint_now()
    try:
        for ws in book.worksheets:
            if (placed or here > 1) and placed.get(ws.title, 1) != here:
                continue
            cols = detect_columns(ws)
            if not {"name", "ts", "transcript", "es"} <= set(cols):
                continue
            sheets.append(ws.title)
            width = max(cols.values())
            # every turn of the sheet, for a quote that takes in the same speaker's passages next to its own
            spoken = []
            for r, values in enumerate(ws.iter_rows(min_row=2, max_col=width, values_only=True), start=2):
                values = tuple(values) + (None,) * (width - len(values))
                spoken.append({"name": str(values[cols["name"] - 1] or "").strip(), "row": r,
                               "text": str(values[cols["transcript"] - 1] or ""),
                               "seconds": ts_seconds(values[cols["ts"] - 1]),
                               "context": bool("ctx" in cols and str(values[cols["ctx"] - 1] or "").strip())})
                entries = split_entries(values[cols["es"] - 1])
                # "(no quote)" is read as empty and keeps its place, so quote i stays statement i's
                said = quote_entries(values[cols["kq"] - 1]) if "kq" in cols else []
                if not entries and not any(said):
                    continue
                if turns:
                    words_of[row_key(ws.title, r)] = str(values[cols["transcript"] - 1] or "").strip()
                seconds = ts_seconds(values[cols["ts"] - 1])
                if any(said):
                    quotes[row_key(ws.title, r)] = {
                        "sheet": ws.title, "row": r, "seconds": seconds, "time": timecode(seconds, form),
                        "quotes": [{"key": card_key(ws.title, r, i), "text": text}
                                   for i, text in enumerate(said) if text]}
                if explore and entries and "en" in cols:
                    thought = split_entries(values[cols["en"] - 1])
                    if thought:
                        explored[row_key(ws.title, r)] = thought
                for i, text in enumerate(entries):
                    cards.append({"key": card_key(ws.title, r, i), "sheet": ws.title, "row": r,
                                  "line": i, "text": text, "seconds": seconds, "time": timecode(seconds, form)})
            spread_quotes(ws.title, spoken, quotes, cards, form)
    finally:
        book.close()
    out = {"sheets": sheets, "cards": cards, "quotes": quotes, "timecodes": form}
    if explore:
        out["explored"] = explored
    if turns:
        out["turns"] = words_of
    return out


def spread_quotes(sheet: str, spoken: list[dict], quotes: dict, cards: list[dict], form: str) -> None:
    """Each quote of a sheet that takes in the same speaker's passages next to its own (quotespan, 30 October
    2026) carries where it stands, in place: under `time` its timecodes from the first passage it takes in to
    the last, "25:51–26:50", in the project's timecodes, under `span` those two in seconds and under `rows` the
    rows it takes in. Its statement's card takes the same `time`, `span` and `rows`, so every board, print,
    Word document and command that names where the statement is gives the range, and keeps its own `seconds`,
    its passage's, to play from. A quote in its own passage alone, or one whose words are no longer there, is
    left as it was. `spoken` is every row of the sheet in order, as `read_cards` reads it."""
    at = {t["row"]: i for i, t in enumerate(spoken)}
    who = None
    by_key = {}
    for key, held in quotes.items():
        if held["sheet"] != sheet or held["row"] not in at:
            continue
        i = at[held["row"]]
        for q in held["quotes"]:
            pieces = quote_pieces(q["text"])
            if len(pieces) < 2 or quote_reach(q["text"], [spoken[i]["text"]], 0):
                continue
            if who is None:
                who = interviewer_name()
            took = sorted({r for r, _, _ in quote_turns(spoken, i, q["text"], who)})
            if len(took) < 2:
                continue
            span = [spoken[took[0]]["seconds"], spoken[took[-1]]["seconds"]]
            by_key[q["key"]] = {"time": time_span(span[0], span[1], form), "span": span,
                                "rows": [spoken[k]["row"] for k in took]}
            q.update(by_key[q["key"]])
    if by_key:
        for c in cards:
            if c["key"] in by_key:
                c.update(by_key[c["key"]])


# The turns read for a key quote taken from the transcript on Trajectories (trajchoose, 11 November 2026), held
# while the workbook stands as it was read, so a board drawn again after each change opens it once
TURNS_HELD: dict = {}
TURNS_MOST = 24


def transcript_turns(workbook: Path, form: str | None = None) -> list[dict]:
    """Every turn of the workbook's transcript sheets that has words, in sheet order: its `turn`, `<sheet>:<row>`,
    its sheet and row, `at`, the timepoint its sheet is at by the participant's progress file (1 for T1, and in a
    project of one), the speaker's `name`, whether the workbook marks it another speaker's, `context`, its
    `seconds` and `time`, and its words as the transcript cell holds them. Opened read-only, as `read_cards`
    opens it, never against Excel's lock. A workbook not there has none."""
    workbook = Path(workbook)
    form = form or timecodes_for(workbook)
    try:
        stat = workbook.stat()
    except OSError:
        return []
    placed = placed_sheets(workbook)
    key = (str(workbook.resolve()), stat.st_mtime_ns, stat.st_size, form, tuple(sorted(placed.items())))
    if key in TURNS_HELD:
        return TURNS_HELD[key]
    try:
        book = openpyxl.load_workbook(workbook, read_only=True, data_only=True)
    except Exception as exc:
        raise WorkbookError(i18n.t("server.could_read", name=workbook.name, exc=exc))
    out = []
    try:
        for ws in book.worksheets:
            cols = detect_columns(ws)
            if not {"name", "ts", "transcript"} <= set(cols):
                continue
            width = max(cols.values())
            for r, values in enumerate(ws.iter_rows(min_row=2, max_col=width, values_only=True), start=2):
                values = tuple(values) + (None,) * (width - len(values))
                text = str(values[cols["transcript"] - 1] or "")
                if not text.strip():
                    continue
                seconds = ts_seconds(values[cols["ts"] - 1])
                out.append({"turn": row_key(ws.title, r), "sheet": ws.title, "row": r, "at": placed.get(ws.title, 1),
                            "name": str(values[cols["name"] - 1] or "").strip(),
                            "context": bool("ctx" in cols and str(values[cols["ctx"] - 1] or "").strip()),
                            "seconds": seconds, "time": timecode(seconds, form), "text": text})
    finally:
        book.close()
    for old in [k for k in TURNS_HELD if k[0] == key[0]] + list(TURNS_HELD)[:max(0, len(TURNS_HELD) - TURNS_MOST + 1)]:
        TURNS_HELD.pop(old, None)
    TURNS_HELD[key] = out
    return out


def quote_keys(quotes: dict) -> set[str]:
    return {q["key"] for row in (quotes or {}).values() for q in row.get("quotes") or []}


def own_quote(quotes: dict, key: str) -> dict | None:
    """A statement's own quote, the one at its place among its row's quotes, as
    `read_cards` reads them, or None when it has none. Its key is the statement's key."""
    sheet, row, _ = split_card_key(key)
    if row is None:
        return None
    return next((q for q in ((quotes or {}).get(row_key(sheet, row)) or {}).get("quotes") or []
                 if q["key"] == key), None)


# ------------------------------------------------------------- the geometry

def char_width(ch: str) -> float:
    """A character's width in the page's serif at 17.5px, a little over."""
    width = _SERIF.get(ch)
    if width is None:
        base = unicodedata.normalize("NFD", ch)[:1]
        width = _SERIF.get(base, _SERIF_WIDEST)
    return width * _SLACK


def text_width(text, px: float = LABEL_PX, spacing: float = 0) -> float:
    """Words set in the page's serif at `px`, with `spacing` between letters."""
    return sum(char_width(ch) * px / LABEL_PX + spacing for ch in str(text or ""))


def wrap(widths: list[float], space: float, room: float) -> tuple[int, float]:
    """The lines words of these widths take in `room`, broken at a space the way the page breaks
    them, a word wider than the room broken anywhere, and the width of all of them on one line."""
    lines, at = 1, 0.0
    for w in widths:
        need = (at + space + w) if at else w
        if at and need > room:
            lines, at, need = lines + 1, 0.0, w
        if need > room:
            lines += math.ceil(need / room) - 1
            need = need - (math.ceil(need / room) - 1) * room
        at = need
    whole = sum(widths) + space * max(0, len(widths) - 1)
    return lines, whole


def card_height(text) -> int:
    """A card's height: its statement in the serif at 14.5px, broken into lines across the card
    the way the page breaks it, four lines at most, with the padding and the timecode under them,
    a pixel over the page's."""
    words = [text_width(w, CARD_TEXT_PX) for w in str(text or "").split()] or [0.0]
    lines, _ = wrap(words, text_width(" ", CARD_TEXT_PX), CARD_TEXT_W)
    return 40 + 20 * max(1, min(4, lines))


def note_height(text) -> int:
    """A sticky note's height: its words in the handwriting face, each line he wrote broken across
    the note the way the page breaks it, with the padding round them, and never shorter than the
    square-ish note an empty one is."""
    lines = 0
    for para in str(text or "").split("\n"):
        words = [text_width(w, NOTE_PX) * NOTE_SLACK for w in para.split()] or [0.0]
        n, _ = wrap(words, text_width(" ", NOTE_PX) * NOTE_SLACK, NOTE_TEXT_W)
        lines += n
    return max(NOTE_MIN_H, NOTE_PAD + NOTE_LINE * max(1, lines))


def description_of(group) -> str:
    """A label's description, the longer line under its short title that he writes (Adam, 21 October):
    one line however it was typed, no limit on its length, and "" for none. It is his own field, apart
    from the label's note, and a label with none carries none, so a board from before reads and writes
    as it did."""
    return " ".join(str((group or {}).get(DESCRIPTION) or "").split()) if isinstance(group, dict) else ""


def layer(depth: int) -> str:
    """What a label is called at its depth, 0 at the top of the canvas: a PET, a sub-theme inside a
    PET, and a group at any depth below a sub-theme, a group inside a group a group too."""
    return LAYERS[max(0, min(int(depth), len(LAYERS) - 1))]


def depth_of(parents: dict, gid: str) -> int:
    """How many labels sit over a label, 0 for a PET, from `parents_of`."""
    depth, seen, at = 0, {gid}, parents.get(gid)
    while at is not None and at not in seen:
        seen.add(at)
        depth += 1
        at = parents.get(at)
    return depth


def count_text(statements: int, themes: int = 0, depth: int = 0) -> str:
    """What a label says after its title: `3 statements`, `2 sub-themes · 7 statements` on a PET
    over sub-themes, and `2 groups · 7 statements` on a sub-theme over groups. `depth` is the
    label's own, 0 for a PET."""
    said = f"{statements} {'statement' if statements == 1 else 'statements'}"
    if themes:
        inner = layer(depth + 1)
        said = f"{themes} {inner if themes == 1 else inner + 's'} · {said}"
    return said


def unit(board: dict, gid: str) -> str:
    """What the screen calls a label, in IPA's own words: a PET at the top of the canvas, a
    sub-theme inside a PET, and a group inside a sub-theme or deeper."""
    groups = board.get("groups") if isinstance(board.get("groups"), list) else []
    parents = {m: g.get("id") for g in groups if isinstance(g, dict) for m in g.get("members") or []}
    return layer(depth_of(parents, gid))


def label_size(text, upper: bool = False, marks: int = 0, description: str = "", body: float = 0,
               domain: str = "") -> tuple[int, int]:
    """A label's width and height, a little over the page's: its title in the serif, wrapping at
    the widest a label runs, with its note's mark and its picks' among `marks`. A label over labels
    is set larger, at 21px, its letters a touch apart. Its count is no part of it, since the page's
    label lost its count to a badge on its frame's corner on 3 October, and the estimate carried it
    on until 17 October, later, a line more for a title that filled its line. A `description` sits
    under the title at four fifths of its size, six lines at most, as the page shows it. A label with
    one runs as wide as `body`, the width of what it holds, where that is wider than LABEL_W, its title
    wrapping there too, so its frame is no wider for it (31 October). An LPET's `domain`, its domains between
    commas, adds their row of pills under the rest (lpetmarks)."""
    px, spacing, line, chrome = (21.0, 0.105, 26.88, 9) if upper else (LABEL_PX, 0, 22.4, 8)
    words = [text_width(w, px, spacing) for w in str(text or "").split()]
    space = text_width(" ", px)
    said = str(description or "").split()
    wide = max(LABEL_W, math.floor(body or 0)) if said else LABEL_W
    room = wide - LABEL_CHROME - LABEL_MARK * marks
    lines, whole = wrap(words or [0.0], space, room)
    width = min(wide, math.ceil(whole) + LABEL_CHROME + LABEL_MARK * marks) if lines == 1 else wide
    height = lines * line + chrome
    if said:
        small = px * DESC_SCALE
        more, long = wrap([text_width(w, small) for w in said], text_width(" ", small), room)
        height += DESC_GAP + min(DESC_LINES, more) * small * DESC_LEADING
        width = max(width, min(wide, math.ceil(long) + LABEL_CHROME + LABEL_MARK * marks)) if more == 1 else wide
    pills = [w for w in (" ".join(p.split()) for p in str(domain or "").split(",")) if w]
    if pills:
        rows, long = wrap([text_width(w, PILL_PX) * 1.1 + PILL_PAD for w in pills], PILL_GAP, room)
        height += PILL_GAP + rows * PILL_H + (rows - 1) * PILL_GAP
        width = max(width, min(wide, math.ceil(long) + LABEL_CHROME + LABEL_MARK * marks)) if rows == 1 else wide
    return width, math.ceil(height)


def union(boxes) -> tuple[float, float, float, float]:
    """The smallest box holding them all. A box is (x, y, w, h), its top-left corner and its size."""
    boxes = list(boxes)
    x = min(b[0] for b in boxes)
    y = min(b[1] for b in boxes)
    return x, y, max(b[0] + b[2] for b in boxes) - x, max(b[1] + b[3] for b in boxes) - y


def clash(a, b, gap: float = 0) -> bool:
    """Two boxes overlap, or come closer than `gap`."""
    return (a[0] < b[0] + b[2] + gap and b[0] < a[0] + a[2] + gap
            and a[1] < b[1] + b[3] + gap and b[1] < a[1] + a[3] + gap)


def pack_round(sizes, gap: float) -> list[tuple[int, int]]:
    """Places for boxes of these sizes, packed in rows inside a circle and in the order given, a
    `gap` between neighbours, the whole of it centred on the origin. Each row is as wide as the
    circle lets it be where the row runs furthest from the middle, and is centred. The circle starts
    at the boxes' own area and grows until every box has a place."""
    sizes = [(float(w), float(h)) for w, h in sizes]
    if not sizes:
        return []
    area = sum((w + gap) * (h + gap) for w, h in sizes)
    radius = max(math.sqrt(area / math.pi), max(w for w, _ in sizes) / 2 + gap)

    def half(top: float, bottom: float, r: float) -> float:
        far = max(abs(top), abs(bottom))
        return math.sqrt(r * r - far * far) if far < r else -1.0

    def rows(r: float):
        spots, i, y = [], 0, -r
        while i < len(sizes):
            if y > r:
                return None
            j, used, tall = i, 0.0, 0.0
            while j < len(sizes):
                w, h = sizes[j]
                need = used + (gap if j > i else 0) + w
                if need > 2 * half(y, y + max(tall, h), r):
                    break
                used, tall, j = need, max(tall, h), j + 1
            if j == i:
                y += 8
                continue
            x = -used / 2
            for k in range(i, j):
                spots.append((x, y))
                x += sizes[k][0] + gap
            y += tall + gap
            i = j
        return spots

    spots = rows(radius)
    while spots is None:
        radius *= 1.08
        spots = rows(radius)
    box = union((x, y, w, h) for (x, y), (w, h) in zip(spots, sizes))
    cx, cy = box[0] + box[2] / 2, box[1] + box[3] / 2
    # every place rounds the same way, half up, so two neighbours keep exactly the gap between them
    # rather than losing a pixel to rounding half to even
    return [(math.floor(x - cx + 0.5), math.floor(y - cy + 0.5)) for x, y in spots]


def free_offset(block, others, gap: float = MARGIN, limit: int = 3000) -> tuple[int, int]:
    """The shortest shift that leaves every box of `block` at least `gap` clear of every box of
    `others`, the block keeping its own arrangement: (0, 0) when it is clear already.

    Best first from where it landed: each shift tried that still meets something offers the four
    ways past the first box it meets, and the nearest of those is tried next. Past `limit` tries the
    block goes beside everything, to the right, which is always clear.
    """
    import heapq
    block = [tuple(b) for b in block]
    others = [tuple(o) for o in others]
    if not block or not others:
        return 0, 0

    def first(dx, dy):
        for b in block:
            moved = (b[0] + dx, b[1] + dy, b[2], b[3])
            for o in others:
                if clash(moved, o, gap):
                    return moved, o
        return None

    heap, seen = [(0, 0, 0)], {(0, 0)}
    while heap and limit > 0:
        limit -= 1
        _, dx, dy = heapq.heappop(heap)
        hit = first(dx, dy)
        if hit is None:
            return dx, dy
        b, o = hit
        for ndx, ndy in ((dx + o[0] + o[2] + gap - b[0], dy), (dx + o[0] - gap - b[2] - b[0], dy),
                         (dx, dy + o[1] + o[3] + gap - b[1]), (dx, dy + o[1] - gap - b[3] - b[1])):
            spot = (math.ceil(ndx) if ndx > dx else math.floor(ndx), math.ceil(ndy) if ndy > dy else math.floor(ndy))
            if spot not in seen:
                seen.add(spot)
                heapq.heappush(heap, (spot[0] ** 2 + spot[1] ** 2, spot[0], spot[1]))
    right = max(o[0] + o[2] for o in others)
    return math.ceil(right + gap - min(b[0] for b in block)), 0


def seeded(keys) -> list[str]:
    """The keys in an order seeded from the keys alone, so a case lays out the same way each time."""
    return sorted(keys, key=lambda k: hashlib.sha256(str(k).encode("utf-8")).hexdigest())


def pile(cards: list[dict]) -> dict[str, dict]:
    """Where each card lies when the canvas is first opened: a compact round pile in the middle,
    packed in rows inside a circle with the margin between cards, in an order seeded from the keys. The middle of the canvas is the origin, and a position is the card's
    top-left corner. No two cards overlap."""
    texts = {c["key"]: c.get("text") or "" for c in cards}
    order = seeded(texts)
    spots = pack_round([(CARD_W, card_height(texts[k])) for k in order], MARGIN)
    return {k: {"x": x, "y": y} for k, (x, y) in zip(order, spots)}


def layout_boxes(version: dict, height=None) -> dict:
    """Where the page draws a board's cards, labels and frames, their sizes estimated.

    The same rule as the page: a label sits above what it holds, its left edge on theirs, and a
    theme's frame runs round its label and its members, a sub-theme's frame counting as one of them.
    A label with nothing in it stays where it was put, and a label with a note or with picks
    carries their marks. Discarded cards are not drawn, nor are stacked ones, under their top. A sticky note stands where it was put, and
    one in a theme is part of what its frame runs round, as the page draws it. `height`, a card's
    key and words to its height, stands in for `card_height` on a canvas whose cards carry more,
    as the GETs screen's do.
    """
    gone = off_canvas(version)
    picks = version.get("picks") or {}
    tall = height or (lambda _key, text: card_height(text))
    cards = {k: (c["x"], c["y"], CARD_W, tall(k, c.get("text"))) for k, c in (version.get("cards") or {}).items()
             if k not in gone}
    groups = {g["id"]: g for g in version.get("groups") or []}
    notes, held = {}, {}
    for n in version.get("notes") or []:
        if isinstance(n, dict) and n.get("id"):
            notes[n["id"]] = (n.get("x", 0), n.get("y", 0), NOTE_W, note_height(n.get("text")))
            if n.get("in") in groups:
                held.setdefault(n["in"], []).append(notes[n["id"]])
    labels, frames, bodies = {}, {}, {}

    def visit(gid: str, seen: frozenset):
        if gid in frames:
            return frames[gid]
        if gid in seen:
            return None
        g = groups[gid]
        boxes, subs = [], 0
        for m in g["members"]:
            if m in groups:
                subs += 1
                inner = visit(m, seen | {gid})
                if inner:
                    boxes.append(inner)
            elif m in cards:
                boxes.append(cards[m])
        boxes.extend(held.get(gid, []))
        marks = bool(str(g.get("note") or "").strip()) + bool(picks.get(gid))
        body = union(boxes) if boxes else None
        w, h = label_size(g["label"], bool(subs), marks, description_of(g), body[2] if body else 0,
                          domain=str(g.get(DOMAIN) or ""))
        x, y = (body[0], body[1] - LABEL_GAP - h) if body else (g.get("x", 0), g.get("y", 0))
        labels[gid] = (x, y, w, h)
        bodies[gid] = body
        whole = union([labels[gid]] + ([body] if body else []))
        frames[gid] = (whole[0] - FRAME_X, whole[1] - FRAME_Y, whole[2] + 2 * FRAME_X, whole[3] + 2 * FRAME_Y)
        return frames[gid]

    for gid in groups:
        visit(gid, frozenset())
    return {"cards": cards, "labels": labels, "frames": frames, "bodies": bodies, "notes": notes}


def place_new(keys: list[str], texts: dict, version: dict, height=None) -> dict[str, dict]:
    """Places for cards a stored board has never seen: packed together as one small pile and set
    in the nearest free spot to the middle of the canvas, the margin clear of every card, label,
    frame and sticky note there, since a frame is solid to a card in no theme. `height` is as
    `layout_boxes` takes it."""
    if not keys:
        return {}
    tall = height or (lambda _key, text: card_height(text))
    order = seeded(keys)
    spots = pack_round([(CARD_W, tall(k, texts.get(k))) for k in order], MARGIN)
    block = [(x, y, CARD_W, tall(k, texts.get(k))) for k, (x, y) in zip(order, spots)]
    drawn = layout_boxes(version, height)
    dx, dy = free_offset(block, list(drawn["cards"].values()) + list(drawn["labels"].values())
                         + list(drawn["frames"].values()) + list(drawn["notes"].values()), MARGIN, limit=800)
    return {k: {"x": x + dx, "y": y + dy} for k, (x, y) in zip(order, spots)}


def blob(gid: str, by_id: dict, order, texts: dict, picks: dict | None = None, height=None, depth: int = 0) -> dict:
    """A theme laid out as a round blob, its frame's top-left corner at the origin: its own cards
    packed in rows that fill a circle, in the order `order(gid)` gives them, the margin between
    them, each sub-theme a blob of its own inside it at any depth, the margin clear of the theme's
    own cards, and its label at the top, its left edge on the left edge of what it holds, as the
    page sets it, with its note's mark and its picks' when it has them, `picks` being the board's.
    The answer is the frame's size, each card's place and each label's, from the frame's corner.
    `height` is as `layout_boxes` takes it, and `depth` is the depth the theme lands at, 0 for a PET,
    which its count names its labels by."""
    tall = height or (lambda _key, text: card_height(text))
    members = order(gid)
    own = [m for m in members if m not in by_id and m in texts]
    subs = [m for m in members if m in by_id]
    parts = []
    if own:
        spots = pack_round([(CARD_W, tall(k, texts[k])) for k in own], MARGIN)
        boxes = [(x, y, CARD_W, tall(k, texts[k])) for k, (x, y) in zip(own, spots)]
        box = union(boxes)
        parts.append({"w": box[2], "h": box[3], "labels": {},
                      "cards": {k: (b[0] - box[0], b[1] - box[1]) for k, b in zip(own, boxes)}})
    for sub in subs:
        parts.append(blob(sub, by_id, order, texts, picks, height, depth + 1))
    marks = bool(str(by_id[gid].get("note") or "").strip()) + bool((picks or {}).get(gid))
    spots, body = [], None
    if parts:
        spots = [(0, 0)] if len(parts) == 1 else pack_round([(p["w"], p["h"]) for p in parts], MARGIN)
        body = union((x, y, p["w"], p["h"]) for (x, y), p in zip(spots, parts))
    w, h = label_size(by_id[gid]["label"], bool(subs), marks, description_of(by_id[gid]), body[2] if body else 0,
                      domain=str(by_id[gid].get(DOMAIN) or ""))
    lx, ly, whole = 0, 0, (0, 0, w, h)
    if body:
        lx, ly = body[0], body[1] - LABEL_GAP - h
        whole = union([(lx, ly, w, h), body])
    ox, oy = whole[0] - FRAME_X, whole[1] - FRAME_Y
    cards, labels = {}, {gid: (lx - ox, ly - oy)}
    for (x, y), p in zip(spots, parts):
        for k, (cx, cy) in p["cards"].items():
            cards[k] = (x + cx - ox, y + cy - oy)
        for g, (gx, gy) in p["labels"].items():
            labels[g] = (x + gx - ox, y + gy - oy)
    return {"w": whole[2] + 2 * FRAME_X, "h": whole[3] + 2 * FRAME_Y, "cards": cards, "labels": labels}


# ----------------------------------------------------------------- a board

def blank_version(cards: list[dict], when: str | None = None, start: str = "empty") -> dict:
    """The first board of a case: no groups, nothing set aside, and every card waiting in the
    sidebar's Not placed, or with `start` of `canvas` every card on the canvas as a round pile in the
    middle, loose (see `LOOSE`). Either way each card has its place in the pile."""
    when = when or now_iso()
    spots = pile(cards)
    out = {c["key"]: dict(spots[c["key"]], text=c["text"]) for c in cards}
    if start == "canvas":
        for card in out.values():
            card[LOOSE] = True
    return {"id": FIRST_VERSION, "name": FIRST_NAME, "note": "", "created": when, "updated": when,
            "cards": out, "groups": [], "discarded": [], "picks": {}}


def waiting_keys(version: dict) -> list[str]:
    """The statements waiting in the sidebar's Not placed: in no PET, not set aside, not stacked and
    not loose on the canvas, in interview order."""
    parents = parents_of(version.get("groups") or [])
    gone = set(version.get("discarded") or []) | stacked_keys(version)
    return sorted((k for k, c in (version.get("cards") or {}).items()
                   if k not in parents and k not in gone and not c.get(LOOSE)), key=_order)


def put_all_on(version: dict, height=None) -> tuple[dict, list[str]]:
    """Every statement waiting in Not placed put on the canvas, loose, as one round pile in the
    nearest free spot to the middle (Adam, 20 October, "chuck all on the canvas"). The board and the
    keys put on. Nothing is written."""
    v = normalise(version)
    keys = waiting_keys(v)
    if keys:
        # the waiting cards are off the canvas, so their old places never stand in the way
        shown = dict(v, cards={k: c for k, c in v["cards"].items() if k not in keys})
        spots = place_new(keys, {k: v["cards"][k].get("text") or "" for k in keys}, shown, height)
        for k in keys:
            v["cards"][k].update(spots[k], **{LOOSE: True})
    return v, keys


def set_aside(version: dict, keys: list[str]) -> tuple[dict, list[str]]:
    """Statements set aside, as X does on the canvas: each leaves its PET, or the canvas, and a top
    takes its stack with it. The board and the keys set aside."""
    v = normalise(version)
    under = stacked_keys(v)
    done = []
    for k in keys:
        if k not in v["cards"] or k in v["discarded"] or k in under:
            continue
        for g in v["groups"]:
            if k in g["members"]:
                g["members"].remove(k)
        v["cards"][k].pop(LOOSE, None)
        v["discarded"].append(k)
        done.append(k)
    return normalise(v), done


def put_back(version: dict, keys: list[str]) -> tuple[dict, list[str]]:
    """Statements set aside put back, to wait in the sidebar's Not placed. The board and the keys put
    back."""
    v = normalise(version)
    done = [k for k in keys if k in v["discarded"]]
    v["discarded"] = [k for k in v["discarded"] if k not in done]
    for k in done:
        v["cards"][k].pop(LOOSE, None)
    return normalise(v), done


def _number(value, fallback: float = 0) -> int:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return int(fallback)
    return int(round(number)) if math.isfinite(number) else int(fallback)


def label_kept(group: dict, gid: str) -> dict:
    """A label as the file holds it, by its id, the one place that says what a label carries: its title,
    `Untitled` when it has none, its note stripped, its description on one line (see `description_of`), an
    LPET's domain, its members and its place. A field with nothing in it is left out, so a file from before it
    reads and writes as it did. Its members are read as they come, `normalise` checking them."""
    kept = {"id": gid, "label": str(group.get("label") or "").strip() or UNTITLED}
    note = str(group.get("note") or "").strip()
    if note:
        kept["note"] = note
    # its description, a line under its title (Adam, 21 October), kept apart from the note
    if description_of(group):
        kept[DESCRIPTION] = description_of(group)
    # an LPET's domain (trajbuild2, 10 November 2026), a word or two, shown as its pill on Trajectories
    domain = " ".join(str(group.get(DOMAIN) or "").split())[:40]
    if domain:
        kept[DOMAIN] = domain
    kept.update(members=[str(m) for m in group.get("members") or []],
                x=_number(group.get("x")), y=_number(group.get("y")))
    return kept


# What a change through the applier (`themes_ai.revise_ops`) says of a label: that it is there, its title, its note,
# its description and what it holds. The rest of the label is the board's, its domain and its place among it.
CHANGE_SAYS = ("id", "label", "note", DESCRIPTION, "members")
# What a page's save says of every label it sends, whatever the label holds: its id, title, members and place, and
# its note, which the page leaves out for none (`thLabelOut`). Any other field it sends no key for at all it never
# spoke of.
PAGE_SAYS = ("id", "label", "note", "members", "x", "y")


def label_landed(old: dict | None, said: dict, made: bool = False) -> dict:
    """A label a change landed, `said` as the applier left it, starting from the board's label of that id, `old`,
    whole: the change's title, note, description and members over everything else `old` carried, its domain among
    them, and its place. A label the change made, `made`, carries nothing of a label gone that had its id but the
    place, as before (domainkeep, 11 November 2026: a bring_in into one LPET took every LPET's domain off the board,
    since the landing built each label afresh from the fields the change speaks of)."""
    old = old or {}
    kept = {} if made else {k: v for k, v in old.items() if k not in CHANGE_SAYS}
    kept.update(id=said["id"], label=said.get("label") or UNTITLED)
    if str(said.get("note") or "").strip():
        kept["note"] = said["note"]
    if description_of(said):
        kept[DESCRIPTION] = description_of(said)
    kept.update(members=list(said.get("members") or []), x=old.get("x", 0), y=old.get("y", 0))
    return kept


def fields_kept(kept: dict, sent, held) -> dict:
    """A board a page saves, `kept` as `normalise` leaves it, each label keeping every field of the file's label of
    that id, `held` the file's labels, that the page sent no key for at all and does not always say (`PAGE_SAYS`):
    a description from a page loaded from an older copy of the app, which sent none (22 October, descloss), an
    LPET's domain, which no board screen edits, and any field a label comes to carry, so a page that does not know
    a field never takes it away (domainkeep, 11 November 2026). A key sent, "" among them, is the page's word, so a
    description he took off goes."""
    said = {str(g.get("id") or "").strip(): set(g) for g in sent or [] if isinstance(g, dict)}
    file = {}
    for g in held or []:
        gid = str(g.get("id") or "").strip() if isinstance(g, dict) else ""
        if gid and gid not in file:
            file[gid] = label_kept(g, gid)

    def put(g: dict) -> dict:
        back = {k: v for k, v in (file.get(g["id"]) or {}).items() if k not in PAGE_SAYS and k not in said.get(g["id"], ())}
        # in the order `label_kept` gives a label's fields
        return label_kept(dict(back, **g), g["id"]) if back else g

    return dict(kept, groups=[put(g) for g in kept["groups"]])


def normalise(version: dict, live: set[str] | None = None) -> dict:
    """A board as the file holds it, whatever the page sent, its history left out.

    Every card keeps a position and its text. A group keeps a label, `Untitled` when it has none,
    and members that exist: card keys still on the board and not discarded, and other groups. A
    member belongs to one group at most, the first that names it, and a group set inside itself, at
    any depth, loses the member that closes the loop. Discarded cards belong to no group.

    A group's `note` is kept stripped, and a group whose note is blank carries none, so a file from
    before the notes reads the same and writes the same.

    A group's `description` is kept the same way, on one line (see `description_of`).

    A group's picks keep only quotes of a row with a card under that group, at any depth, once each.
    With `live`, the quote keys the workbook holds now, a pick whose quote has gone is dropped too.

    `ai` is why a statement was left out, `{"discarded": {key: reason}}`, as an agent's board make
    gives it, or a New AI board gave it before 11 November 2026, kept for a card the board holds and a
    reason with words in it. A board with none carries no `ai` at all.

    `review` and `revise`, a board's AI review and revise thread from before 11 November 2026, are
    carried as the file holds them and never read (see `FROM_BEFORE`).

    `quoted` is the words of each quote the picks name, kept for the picks that stay. `cut` is the
    cards a trim cut, kept until the trim is undone (see `cut_of`). A board with neither carries
    neither, so a file from before them reads and writes as it did.

    `notes` are the board's sticky notes (see `notes_of`), and a board with none carries none.

    `stacks` are the statements stacked under a top (see `stacks_kept`), and a board with none
    carries none. A stacked statement leaves every group and the bin. `not_same` are the close pairs
    marked Not the same (see `not_same_kept`), and a board with none carries none.

    `made` and `changed` say what an AI agent in a conversation did to the board, the board it made
    and the last change it made (see `agent_mark`), and a board with neither carries neither.
    """
    version = version if isinstance(version, dict) else {}
    cards: dict[str, dict] = {}
    raw_cards = version.get("cards") if isinstance(version.get("cards"), dict) else {}
    for key, card in raw_cards.items():
        if not isinstance(card, dict):
            continue
        kept = {"x": _number(card.get("x")), "y": _number(card.get("y")),
                "text": str(card.get("text") or "")}
        # a card whose line has changed since the board was made keeps the text it was made with,
        # and the line as it reads now beside it, until he moves the card
        if card.get("live") is not None and str(card.get("live")) != kept["text"]:
            kept["live"] = str(card["live"])
        # a card he put on the canvas in no PET yet, `loose` (20 October), where one in no PET without it
        # waits in the sidebar's Not placed (see `LOOSE`)
        if card.get(LOOSE) is True:
            kept[LOOSE] = True
        cards[str(key)] = kept

    stacks, under = stacks_kept(version.get("stacks"), cards)
    discarded: list[str] = []
    for key in version.get("discarded") or []:
        key = str(key)
        if key in cards and key not in discarded and key not in under:
            discarded.append(key)
    # a stacked statement belongs to no group and is not in the bin: it goes where its top goes
    gone = set(discarded) | set(under)

    groups: list[dict] = []
    ids: set[str] = set()
    for group in version.get("groups") or []:
        if not isinstance(group, dict):
            continue
        gid = str(group.get("id") or "").strip()
        if not gid or gid in ids or gid in cards:
            continue
        ids.add(gid)
        groups.append(label_kept(group, gid))

    owner: dict[str, str] = {}
    for group in groups:
        kept = []
        for member in group["members"]:
            if member == group["id"] or member in owner:
                continue
            if member in ids or (member in cards and member not in gone):
                kept.append(member)
                owner[member] = group["id"]
        group["members"] = kept
    # `loose` is only for a card in no PET, not set aside and not stacked
    for key, card in cards.items():
        if card.get(LOOSE) and (key in owner or key in gone):
            card.pop(LOOSE)

    # a loop, a group inside a group inside itself, is broken where it closes
    for group in groups:
        child, at, path = group["id"], owner.get(group["id"]), [group["id"]]
        while at is not None:
            if at in path:
                parent = next(g for g in groups if g["id"] == owner[child])
                parent["members"].remove(child)
                owner.pop(child)
                break
            path.append(at)
            child, at = at, owner.get(at)

    picks: dict[str, list[str]] = {}
    raw_picks = version.get("picks") if isinstance(version.get("picks"), dict) else {}
    by_id = {g["id"]: g for g in groups}
    for gid, chosen in raw_picks.items():
        gid = str(gid)
        if gid not in by_id or not isinstance(chosen, list):
            continue
        # a statement stacked under one in the label counts as under it, so its quote stays picked
        rows = {row_key(*split_card_key(k)[:2]) for k in with_stacked(cards_under(by_id, gid), stacks) if k in cards}
        kept = []
        # as many as he picked, each once (see `picks_kept`), so a file's three are never cut on read
        for key in picks_kept(chosen):
            sheet, row, _ = split_card_key(key)
            if row is None or row_key(sheet, row) not in rows:
                continue
            if live is not None and key not in live:
                continue
            kept.append(key)
        if kept:
            picks[gid] = kept

    out = {"id": str(version.get("id") or FIRST_VERSION),
           "name": str(version.get("name") or FIRST_NAME),
           "note": str(version.get("note") or ""),
           "created": str(version.get("created") or now_iso()),
           "updated": str(version.get("updated") or now_iso()),
           "cards": cards, "groups": groups, "discarded": discarded, "picks": picks}
    if stacks:
        out["stacks"] = stacks
    apart = not_same_kept(version.get("not_same"), cards)
    if apart:
        out["not_same"] = apart
    notes = notes_of(version, {g["id"] for g in groups}, set(cards))
    if notes:
        out["notes"] = notes
    reasons = ai_reasons(version, cards)
    if reasons:
        out["ai"] = {"discarded": reasons}
    for key in FROM_BEFORE:
        if version.get(key):
            out[key] = version[key]
    for key in AGENT_KEYS:
        mark = made_mark(version.get(key)) if key == "made" else agent_mark(version.get(key))
        if mark:
            out[key] = mark
    held = version.get("quoted") if isinstance(version.get("quoted"), dict) else {}
    named = {k for chosen in picks.values() for k in chosen}
    quoted = {str(k): str(t) for k, t in held.items() if str(k) in named and isinstance(t, str) and t.strip()}
    if quoted:
        out["quoted"] = quoted
    cut = cut_of(version)
    if cut:
        out["cut"] = cut
    origin = origin_of(version.get(ORIGIN))
    if origin:
        out[ORIGIN] = origin
    return out


# A board brought in from a shared copy coming back (26 October, see `idiograph_routes.boards_in`) keeps
# where it came from: the file, whose copy, its name there, when the copy was sent and when it came in
ORIGIN = "origin"
# and since 9 November (wtboard) a board a teammate sent through Working together names its message, `team`, in
# place of a file
ORIGIN_FIELDS = ("file", "who", "board", "sent", "at", "request", "team")


def origin_of(raw) -> dict | None:
    """A board's `origin` as the file keeps it, its words alone, or None for none."""
    if not isinstance(raw, dict):
        return None
    kept = {k: " ".join(str(raw[k]).split()) for k in ORIGIN_FIELDS if isinstance(raw.get(k), str) and raw[k].strip()}
    return kept if kept.get("file") or kept.get("team") else None


def notes_of(version: dict, groups: set[str], cards=frozenset()) -> list[dict]:
    """A board's sticky notes as the file keeps them, in the order it holds them: each with an id of
    its own, its text stripped at the ends with its lines kept, its colour, yellow when it names
    none of the four, and its place. `in` stays only while it names a group of `groups`, so a note
    whose group has gone stands free. A note is never a member, so nothing that counts or lists a
    group's statements ever meets one."""
    out, seen = [], set()
    raw = version.get("notes") if isinstance(version, dict) and isinstance(version.get("notes"), list) else []
    for note in raw:
        if not isinstance(note, dict):
            continue
        nid = str(note.get("id") or "").strip()
        if not nid or nid in seen or nid in groups or nid in cards:
            continue
        seen.add(nid)
        colour = note.get("colour") if note.get("colour") in NOTE_COLOURS else NOTE_COLOURS[0]
        text = str(note.get("text") or "").replace("\r\n", "\n").replace("\r", "\n").strip()
        kept = {"id": nid, "text": text, "colour": colour, "x": _number(note.get("x")), "y": _number(note.get("y"))}
        where = str(note.get("in") or "")
        if where in groups:
            kept["in"] = where
        out.append(kept)
    return out


def cut_of(version: dict) -> list[dict]:
    """The cards a trim cut from a board, one record a trim: the trim's id, each card's place and
    words, the groups they sat in, the ones discarded, the picks on their rows with those picks'
    words, and the AI's reasons. A record stays in the numbering of the trim that made it, which is
    the numbering its undo puts the rows back in."""
    out = []
    for record in version.get("cut") if isinstance(version.get("cut"), list) else []:
        if not isinstance(record, dict):
            continue
        raw = record.get("cards") if isinstance(record.get("cards"), dict) else {}
        cards = {str(k): {"x": _number(c.get("x")), "y": _number(c.get("y")), "text": str(c.get("text") or "")}
                 for k, c in raw.items() if isinstance(c, dict)}

        def lists(field: str) -> dict:
            held = record.get(field) if isinstance(record.get(field), dict) else {}
            return {str(g): [str(k) for k in keys] for g, keys in held.items() if isinstance(keys, list) and keys}

        def texts(field: str) -> dict:
            held = record.get(field) if isinstance(record.get(field), dict) else {}
            return {str(k): str(t) for k, t in held.items() if isinstance(t, str) and t.strip()}

        kept = {"trim": str(record.get("trim") or ""), "cards": cards, "members": lists("members"),
                "discarded": [str(k) for k in record.get("discarded") or [] if str(k) in cards],
                "picks": lists("picks")}
        for field in ("quoted", "ai"):
            if texts(field):
                kept[field] = texts(field)
        if cards or kept["picks"]:
            out.append(kept)
    return out


def one_line(value, limit: int) -> str:
    return " ".join(str(value or "").split())[:limit].strip()


def agent_mark(raw) -> dict | None:
    """What an AI agent did, as a board keeps it: `{"by": "agent", "tool", "request", "at"}`, the
    tool it worked in, his request in his words and the time, or None for anything else."""
    if not isinstance(raw, dict) or raw.get("by") not in ("agent", "member") or not one_line(raw.get("at"), 40):
        return None
    out = {"by": raw["by"], "tool": one_line(raw.get("tool"), 80), "request": one_line(raw.get("request"), REQUEST_TEXT),
           "at": one_line(raw.get("at"), 40)}
    # a teammate's suggestion accepted (wtsuggest, 10 November 2026): who suggested it, who accepted it, and its id
    if raw["by"] == "member":
        out.update({k: one_line(raw.get(k), 80) for k in MEMBER_KEYS})
    # the board's state hash as the agent's change left it, so his next save is told from it
    if one_line(raw.get("hash"), 80):
        out["hash"] = one_line(raw.get("hash"), 80)
    return out


def made_mark(raw) -> dict | None:
    """Who made a board, as it keeps it: an agent's mark (see `agent_mark`), keeping `from` when it has
    one, `hash`, the board's state hash as it was made, and `edited`, the time his first save changed
    it. None for anything else, the mark a New AI board left before 11 November 2026 among them, so
    such a board is an ordinary one."""
    if not isinstance(raw, dict) or not one_line(raw.get("at"), 40) or raw.get("by") not in ("agent", "member"):
        return None
    out = agent_mark(raw)
    for key, limit in (("from", 160), ("hash", 80), ("edited", 40)):
        if one_line(raw.get(key), limit):
            out[key] = one_line(raw.get(key), limit)
    return out


def made_said(board: dict) -> dict | None:
    """What the board menu says of a board an agent made, `{"by", "said", "edited"}`: the tooltip's
    words, "Claude Code in a conversation, from Board 2", and whether he has changed it since. A board
    from before `made` is read from its note, and one no agent made, a duplicate among them, is None."""
    mark = made_mark(board.get("made")) if isinstance(board, dict) else None
    if mark:
        who = (mark.get("tool") or "" if mark["by"] == "member"
               else f"{mark.get('tool') or 'An agent'} in a conversation")
        said = who + (f", from {mark['from']}" if mark.get("from") else "")
        return {"by": mark["by"], "said": said, "edited": bool(mark.get("edited"))}
    note = str((board or {}).get("note") or "") if isinstance(board, dict) else ""
    found = AGENT_NOTE.match(note)
    if found:
        return {"by": "agent", "said": f"{found['tool']} in a conversation", "edited": False}
    return None


def made_state(board: dict) -> dict:
    """What `made`'s hash is taken over: the board's state as a revision holds it, with the GET
    table's rows on a GETs board, so a tick or a row's note is a change too."""
    state = state_of(board)
    if board.get("rows"):
        state["rows"] = board["rows"]
    return state


def stamp_made(made: dict | None, board: dict) -> dict | None:
    """A new board's `made` with the hash of the board as it was made."""
    if not made:
        return None
    return dict(made, hash=state_hash(made_state(board)))


def edited_mark(made: dict | None, board: dict, when: str, changed: dict | None = None) -> dict | None:
    """`made` after a save of `board`: his first save whose state differs from the one kept at the
    making marks it edited, at that time, and a save that changes nothing leaves it as it was. A
    board an agent changed since is told from the state the agent's change left, `changed`'s hash,
    so the agent's change is never called his."""
    if not made or made.get("edited") or not made.get("hash"):
        return made
    now = state_hash(made_state(board))
    if now == made["hash"] or (changed and now == changed.get("hash")):
        return made
    return dict(made, edited=when)


def iso_time(value) -> float | None:
    try:
        return datetime.fromisoformat(str(value)).timestamp()
    except (TypeError, ValueError):
        return None


def outside_since(board: dict, sent: dict) -> bool:
    """Whether an agent changed `board` after the page sending `sent` last saw it: the `updated` the
    page holds is not the board's, and the board's `changed` is later than it. A page that sends no
    `updated` is never held up, and nor is one whose last save is the board as the file holds it."""
    if not isinstance(board, dict) or not isinstance(sent, dict):
        return False
    mark = agent_mark(board.get("changed"))
    said = str(sent.get("updated") or "")
    seen, at = iso_time(said), iso_time(mark["at"]) if mark else None
    return at is not None and seen is not None and said != str(board.get("updated") or "") and seen < at


def keep_canvas(board: dict, state: dict, at: str | None = None) -> dict:
    """The page's canvas kept in a board's history when an agent changed the board under it, named
    CANVAS_KEPT. A second keep in a row takes the place of the first, so a page that goes on
    working before it shows the change keeps one revision, its latest."""
    history = history_of(board)
    if history and revision_mark(history[-1])[0] == "canvas_kept":
        history.pop()
        board["history"] = history
    return add_revision(board, name=revision_name("canvas_kept"), at=at, state=state)


def short_ids(cards: list[dict]) -> dict[str, str]:
    """Each statement's short id, `S1` on, in the order `read_cards` reads them, sheet by sheet and
    down each sheet in transcript order, worked out afresh on every read, so the same workbook
    always gives the same ids."""
    return {c["key"]: f"S{i}" for i, c in enumerate(cards, start=1)}


def ai_reasons(version: dict, cards: dict) -> dict[str, str]:
    """Why each statement was left out, by card key, for the cards the board holds: an agent's reason,
    or an AI proposal's from before 11 November 2026."""
    ai = version.get("ai") if isinstance(version.get("ai"), dict) else {}
    thrown = ai.get("discarded") if isinstance(ai.get("discarded"), dict) else {}
    out = {}
    for key, why in thrown.items():
        words = " ".join(str(why or "").split())
        if str(key) in cards and words:
            out[str(key)] = words
    return out


def cards_under(by_id: dict, gid: str) -> list[str]:
    """Every member of a group that is not itself a group, at any depth, in membership order."""
    out, seen, stack = [], set(), list(reversed(by_id[gid]["members"])) if gid in by_id else []
    while stack:
        item = stack.pop()
        if item in seen:
            continue
        seen.add(item)
        if item in by_id:
            stack.extend(reversed(by_id[item]["members"]))
        else:
            out.append(item)
    return out


def stacks_kept(raw, cards: dict) -> tuple[dict[str, list[str]], dict[str, str]]:
    """A board's stacks as the file keeps them, and each stacked statement's top: every top a card
    the board holds, each statement under it a card of the board, never the top itself, and under
    one top at most, the first that names it. A top stacked under another brings its own stack with
    it, so a stack is one level deep, the top over all the rest, and a stack named in a loop is cut
    where it closes. A top with nothing under it carries no stack."""
    stacks: dict[str, list[str]] = {}
    under: dict[str, str] = {}
    for top, keys in (raw.items() if isinstance(raw, dict) else ()):
        top = str(top)
        if top not in cards or not isinstance(keys, list):
            continue
        head = under.get(top, top)
        for key in keys:
            key = str(key)
            if key not in cards or key == head or key in under:
                continue
            brought = stacks.pop(key, [])
            stacks.setdefault(head, []).append(key)
            under[key] = head
            for k in brought:
                stacks[head].append(k)
                under[k] = head
    return {t: ks for t, ks in stacks.items() if ks}, under


def stacked_keys(version: dict) -> set[str]:
    """Every statement stacked under another on a board."""
    return {k for keys in (version.get("stacks") or {}).values() for k in keys}


def off_canvas(version: dict) -> set[str]:
    """The cards a board does not draw on its canvas: those in the bin and those stacked under a top."""
    return set(version.get("discarded") or []) | stacked_keys(version)


def top_of(version: dict, key: str) -> str | None:
    """The top a statement is stacked under, or None for one in no stack or on top of one."""
    return next((t for t, keys in (version.get("stacks") or {}).items() if key in keys), None)


def stack_onto(version: dict, items: list[str], top: str) -> dict:
    """A board with `items` stacked under `top`, as a drop on a card's middle does on the canvas: each
    leaves its label, the bin or another stack, and one that was a top brings its own stack with it,
    after it, so the stack stays one level deep. `top` keeps its place. Nothing is written."""
    v = json.loads(json.dumps(normalise(version)))
    stacks = v.get("stacks") or {}
    held = list(stacks.get(top) or [])
    for key in items:
        if key == top or key not in v["cards"]:
            continue
        brought = stacks.pop(key, [])
        for t in list(stacks):
            stacks[t] = [k for k in stacks[t] if k != key]
        for g in v["groups"]:
            g["members"] = [m for m in g["members"] if m != key]
        v["discarded"] = [k for k in v["discarded"] if k != key]
        held = [k for k in held if k not in (key, *brought)] + [key] + [k for k in brought if k != top]
    stacks[top] = held
    v["stacks"] = stacks
    return normalise(v)


def take_out(version: dict, items: list[str], height=None) -> dict:
    """A board with each of `items` taken out of its stack and put just below it: into the top's
    label, under the top, a margin below, and further down past anything there, never above the top,
    or into Not placed so when the top is in none, and into Not placed by the nearest free spot to
    the middle when the top is in the bin. Nothing is written."""
    v = json.loads(json.dumps(normalise(version)))
    for key in items:
        top = top_of(v, key)
        if top is None:
            continue
        v["stacks"][top] = [k for k in v["stacks"][top] if k != key]
        if not v["stacks"][top]:
            v["stacks"].pop(top)
        parents = parents_of(v["groups"])
        if top in v["discarded"]:
            spot = place_new([key], {key: v["cards"][key].get("text") or ""}, v, height)[key]
            v["cards"][key].update(spot)
            continue
        owner = parents.get(top)
        if owner is not None:
            g = next(x for x in v["groups"] if x["id"] == owner)
            g["members"].insert(g["members"].index(top) + 1, key)
        drawn = layout_boxes(dict(v, stacks=dict(v["stacks"], **{top: [key]})), height)
        tall = height or (lambda _key, text: card_height(text))
        t = drawn["cards"][top]
        holding = set()
        at = owner
        while at is not None and at not in holding:
            holding.add(at)
            at = parents.get(at)
        # what stands on the canvas, as the page's thBelowStack reads it: a statement waiting in Not placed is
        # off it, and its old place never stands in the way (31 October)
        waiting = set(waiting_keys(v))
        others = ([b for k, b in drawn["cards"].items() if k != key and k not in waiting] + list(drawn["notes"].values())
                  + [b for g, b in drawn["labels"].items()]
                  + [b for g, b in drawn["frames"].items() if g not in holding])
        v["cards"][key].update(**below(t, (CARD_W, tall(key, v["cards"][key].get("text"))), others))
    return normalise(v)


def below(top, size, others) -> dict:
    """Where a card taken out of a stack goes: under its top, `top` its box, at its left edge a margin
    below it, and moved further down past each box of `others` it would meet, never up and never
    aside, so it lands just below the stack and clear of everything."""
    x, y = top[0], top[1] + top[3] + MARGIN
    for _ in range(400):
        hit = next((o for o in others if clash((x, y, size[0], size[1]), o, MARGIN)), None)
        if hit is None:
            break
        y = hit[1] + hit[3] + MARGIN
    return {"x": round(x), "y": round(y)}


def make_top(version: dict, key: str) -> dict:
    """A board with `key` on top of the stack it is in, the top it replaces first under it, in the
    top's place: its label, its spot on the canvas, or the bin. Nothing is written."""
    v = json.loads(json.dumps(normalise(version)))
    top = top_of(v, key)
    if top is None:
        return v
    rest = [top] + [k for k in v["stacks"].pop(top) if k != key]
    v["stacks"][key] = rest
    for g in v["groups"]:
        g["members"] = [key if m == top else m for m in g["members"]]
    v["discarded"] = [key if k == top else k for k in v["discarded"]]
    v["cards"][key].update(x=v["cards"][top]["x"], y=v["cards"][top]["y"])
    return normalise(v)


def with_stacked(keys, stacks: dict) -> list[str]:
    """Keys with the statements stacked under each, after it, in the stack's order."""
    out = []
    for k in keys:
        out.append(k)
        out.extend(stacks.get(k) or [])
    return out


# ------------------------------------------------------------- close pairs

# Close pairs (Adam, 20 October, after supervision: statements from the same passage of the same sheet
# stack under the best one unless they say radically different things). Two statements directly in one
# group, or in one PET with no groups, from one sheet within the gap of each other, by their passages'
# times, are a close pair, which the board marks with a link line until they are stacked or he marks
# them Not the same. The gap is a setting, a minute on a new install.
CLOSE_GAPS = (15, 30, 60, 120, 300)
CLOSE_GAP = 60
CLOSE_MOST = 3600
# a sheet with no times counts its rows, each standing for half a minute, so a minute is two rows
ROW_SECONDS = 30


def close_gap(value, free: bool = False) -> int:
    """The gap in seconds: one of CLOSE_GAPS for the setting, else the minute, and with `free` any
    whole number of seconds from 1 to an hour, as an agent asks for one look."""
    if isinstance(value, bool):
        return CLOSE_GAP
    try:
        n = int(value)
    except (TypeError, ValueError):
        return CLOSE_GAP
    if free:
        return n if 1 <= n <= CLOSE_MOST else CLOSE_GAP
    return n if n in CLOSE_GAPS else CLOSE_GAP


def pair_of(a: str, b: str) -> list[str]:
    """Two keys in transcript order, sheet, row and line, the way a pair is kept and named."""
    return sorted([str(a), str(b)], key=_order)


def not_same_kept(raw, cards: dict) -> list[list[str]]:
    """The pairs marked Not the same as the file keeps them: two different keys of cards the board
    holds, in transcript order, each pair once, in the order he marked them."""
    out: list[list[str]] = []
    for item in raw if isinstance(raw, list) else []:
        if not isinstance(item, (list, tuple)) or len(item) != 2:
            continue
        a, b = (str(x) for x in item)
        if a == b or a not in cards or b not in cards:
            continue
        pair = pair_of(a, b)
        if pair not in out:
            out.append(pair)
    return out


def pair_words(pair: dict) -> str:
    """How far apart a close pair is, as the board says it: "12 s apart", "2 rows apart" on a sheet
    with no times, and "Same passage" for two statements of one row."""
    if pair.get("same_row"):
        return "Same passage"
    n = int(pair.get("gap") or 0)
    if pair.get("unit") == "rows":
        return "1 row apart" if n == 1 else f"{n} rows apart"
    return f"{n} s apart"


def close_pairs(version: dict, cards, gap: int = CLOSE_GAP) -> list[dict]:
    """A board's close pairs, those marked Not the same left out: each `{"items": [a, b], "sheet",
    "gap", "unit", "same_row", "group"}`, the two keys in transcript order, how far apart they are in
    seconds, or in rows (`unit` "rows") when either has no time, and the group both stand directly in.

    `cards` is the statements as `read_cards` gives them, or a dict of them by key, for each one's
    sheet, row and time. A statement stacked under another, in the bin or in no group is in no pair,
    so a pair already stacked is none. A statement close to two others is in a pair with each. The
    pairs run in the board's group order, then in transcript order. Nothing is written."""
    v = normalise(version)
    info = cards if isinstance(cards, dict) else {c["key"]: c for c in cards}
    apart = {tuple(p) for p in v.get("not_same") or []}
    groups = {g["id"] for g in v["groups"]}
    rows = max(1, int(gap) // ROW_SECONDS)
    out = []
    for g in v["groups"]:
        own = sorted((m for m in g["members"] if m not in groups and m in v["cards"] and m in info), key=_order)
        for i, a in enumerate(own):
            for b in own[i + 1:]:
                ca, cb = info[a], info[b]
                if str(ca.get("sheet")) != str(cb.get("sheet")) or (a, b) in apart:
                    continue
                sa, sb = ca.get("seconds"), cb.get("seconds")
                same_row = ca.get("row") == cb.get("row")
                if sa is not None and sb is not None:
                    d = abs(int(sa) - int(sb))
                    unit, near = "s", d <= gap
                else:
                    d = abs(int(ca.get("row") or 0) - int(cb.get("row") or 0))
                    unit, near = "rows", d <= rows
                if near:
                    out.append({"items": [a, b], "sheet": str(ca.get("sheet")), "gap": d, "unit": unit,
                                "same_row": same_row, "group": g["id"]})
    return out


def current_version(data: dict | None) -> dict | None:
    """The board the file names as current, or its first, or None for a file with none."""
    boards = boards_of(data)
    if not boards:
        return None
    return next((v for v in boards if v.get("id") == data.get("current")), boards[0])


def find_version(data: dict | None, vid) -> dict | None:
    return next((v for v in boards_of(data) if str(v.get("id")) == str(vid)), None)


def words(text) -> str:
    """A line's words as a card or a pick follows them: the whitespace collapsed, the case kept."""
    return " ".join(str(text or "").split())


# The inverted commas a quote may stand in, double or single, straight or curly. A pair round
# the whole quote is set aside when a pick is matched against it.
DOUBLE_MARKS = "\"\u201c\u201d\u201e"
SINGLE_MARKS = "'\u2018\u2019"


def quote_words(text) -> str:
    """A quote's words as a pick matches them: `words`, with the inverted commas round the whole
    quote set aside, double or single, straight or curly, and the spacing inside them. So a quote a
    write has put in inverted commas, or one he has taken them off, is still the same quote, and
    only a change of its words moves or drops a pick."""
    said = words(text)
    while len(said) >= 2 and any(said[0] in marks and said[-1] in marks for marks in (DOUBLE_MARKS, SINGLE_MARKS)):
        said = words(said[1:-1])
    return said


def picks_kept(keys, most: int | None = None) -> list[str]:
    """A label's picks as the app keeps them, the one rule for how many it takes: each quote once,
    in the order picked, and as many as he picks. The tick on the PETs screen, the file, `board new`
    and a pick operation from the command line keep every one. `most` is for an AI answer alone,
    the one quote its prompt asks for, or two when no single one carries the title (see
    `themes_ai.PICKS_MAX`), and a GETs pick, one quote for each case."""
    kept = list(dict.fromkeys(str(k) for k in keys or [] if str(k)))
    return kept[:most] if most else kept


def _order(key: str) -> tuple:
    sheet, row, line = split_card_key(key)
    return sheet, row if row is not None else -1, line if line is not None else -1


def follow(version: dict, cards: list[dict], quotes: dict | None = None, moves: dict | None = None,
           keys: dict | None = None, own=None) -> dict:
    """A board, or a revision's state, normalised, its keys following their words. Nothing is written.

    A stored card whose key still carries its stored text stays. One whose key no longer does takes
    the key of an unclaimed live line with the same words, `words` of each, on its own row first,
    the nearest line, and then anywhere on its sheet, the nearest row. One that finds none keeps its
    key while no other card has taken it, which marks it changed where a line reads differently there
    and missing where none does, and otherwise moves past every line of its row, which marks it
    missing. A key that moves moves everywhere the board names it: its cards, its groups' members,
    its discards and the AI's reasons. So a line inserted at the top of a cell
    leaves every card in its theme and its place.

    `own`, when given, is the keys of cards that were never a statement of the workbook's at their key,
    another analyst's own added in a copy coming back (copyback, 6 November 2026): such a card takes a
    line by its words alone, and where its key holds a line of the workbook's it moves past every line
    of its row. `keys`, when given, gains each stored card's key and the key it has now.

    Then the picks, with `quotes` the quotes as `read_cards` reads them and `quoted` the words
    each pick had when the board was last saved. Words are matched as `quote_words` gives them, the
    inverted commas round a quote set aside, so a quote a write has put in them reads the same. A
    pick whose quote reads the same stays. One whose quote reads differently, or has gone, takes the
    key of a quote with the same words on its own row, else on a row with a card under its label,
    the nearest first, and is dropped when there is none. A pick with no words kept, from a file
    before `quoted`, is left to the rule as it was. A pick that stays or moves keeps the words its
    quote has now under `quoted`.

    `moves`, when given, gains what became of each pick that held words, by its label and its key:
    the key it has now, its own when it stayed, or None when it was dropped.
    """
    v = normalise(version)
    stored = v["cards"]
    live = {c["key"]: c for c in cards}
    said = {k: words(c["text"]) for k, c in live.items()}
    by_words: dict[str, list[str]] = {}
    for k in live:
        by_words.setdefault(said[k], []).append(k)

    keymap: dict[str, str] = {}
    for k, card in stored.items():
        if k in live and said[k] == words(card["text"]):
            keymap[k] = k
    claimed = set(keymap.values())
    movers = sorted((k for k in stored if k not in keymap), key=_order)
    for k in movers:
        sheet, row, line = split_card_key(k)
        found = [x for x in by_words.get(words(stored[k]["text"]), [])
                 if x not in claimed and live[x]["sheet"] == sheet] if words(stored[k]["text"]) else []
        if not found:
            continue
        same = [x for x in found if live[x]["row"] == row]
        if same:
            to = min(same, key=lambda x: (abs(live[x]["line"] - (line or 0)), live[x]["line"]))
        else:
            to = min(found, key=lambda x: (abs(live[x]["row"] - (row or 0)), live[x]["row"], live[x]["line"]))
        keymap[k] = to
        claimed.add(to)
    strangers = set(own or ())
    for k in movers:
        if k not in keymap and k not in claimed and (k not in strangers or k not in live):
            keymap[k] = k
            claimed.add(k)
    for k in movers:
        if k in keymap:
            continue
        sheet, row, _ = split_card_key(k)
        if row is None:
            keymap[k] = k
            continue
        taken = [split_card_key(x) for x in set(live) | set(stored) | claimed]
        lines = [ln for s, r, ln in taken if s == sheet and r == row and ln is not None]
        keymap[k] = card_key(sheet, row, max(lines, default=-1) + 1)
        claimed.add(keymap[k])
    if keys is not None:
        keys.update(keymap)

    if any(keymap[k] != k for k in keymap):
        moved = {}
        for k, card in stored.items():
            card = dict(card)
            to = keymap[k]
            if to in live and said[to] == words(card["text"]):
                card.pop("live", None)
            moved[to] = card
        v["cards"] = moved
        for g in v["groups"]:
            g["members"] = [keymap.get(m, m) for m in g["members"]]
        v["discarded"] = [keymap.get(k, k) for k in v["discarded"]]
        if v.get("stacks"):
            v["stacks"] = {keymap.get(t, t): [keymap.get(k, k) for k in ks] for t, ks in v["stacks"].items()}
        if v.get("not_same"):
            v["not_same"] = [[keymap.get(a, a), keymap.get(b, b)] for a, b in v["not_same"]]
        if v.get("ai"):
            v["ai"] = {"discarded": {keymap.get(k, k): why for k, why in v["ai"]["discarded"].items()}}

    if quotes is not None and v["picks"]:
        held = v.get("quoted") or {}
        texts = {q["key"]: q["text"] for row in quotes.values() for q in row.get("quotes") or []}
        qsaid = {k: quote_words(t) for k, t in texts.items()}
        qby: dict[str, list[str]] = {}
        for k, w in qsaid.items():
            qby.setdefault(w, []).append(k)
        by_id = {g["id"]: g for g in v["groups"]}
        picks, quoted = {}, {}
        for gid, chosen in v["picks"].items():
            rows = {row_key(*split_card_key(k)[:2]) for k in with_stacked(cards_under(by_id, gid), v.get("stacks") or {})
                    if k in v["cards"]}
            stay = [k for k in chosen if k not in held or qsaid.get(k) == quote_words(held[k])]
            claimed = set(stay)
            kept = []
            for k in chosen:
                if k in stay:
                    kept.append(k)
                    if moves is not None and k in held:
                        moves[(gid, k)] = k
                    continue
                sheet, row, index = split_card_key(k)
                found = [x for x in qby.get(quote_words(held[k]), []) if x not in claimed]
                same = [x for x in found if split_card_key(x)[:2] == (sheet, row)]
                near = same or [x for x in found if row_key(*split_card_key(x)[:2]) in rows]
                if moves is not None:
                    moves[(gid, k)] = None
                if not near:
                    continue
                to = min(near, key=lambda x: (abs(split_card_key(x)[1] - (row or 0)),
                                              abs(split_card_key(x)[2] - (index or 0)), _order(x)))
                claimed.add(to)
                kept.append(to)
                quoted[to] = texts[to]
                if moves is not None:
                    moves[(gid, k)] = to
            # a pick that stayed keeps its quote's words as they read now, inverted commas and all
            for k in kept:
                if k not in quoted and k in held:
                    quoted[k] = texts.get(k, held[k])
            picks[gid] = kept
        v["picks"] = picks
        v["quoted"] = quoted
    return normalise(v)


def with_row(read: dict, sheet: str, row: int, statements, quotes) -> dict:
    """`read_cards`'s answer with one row's statements and quotes as a write would leave them,
    `quotes` by place as `quote_entries` reads the cell, an empty place carrying none. The row keeps
    its timecode, written as `read` writes its own. Nothing is read or written."""
    here = lambda c: c["sheet"] == sheet and c["row"] == row
    at = row_key(sheet, row)
    old = [c for c in read["cards"] if here(c)]
    held = (read.get("quotes") or {}).get(at) or {}
    seconds = old[0].get("seconds") if old else held.get("seconds")
    form = read.get("timecodes")
    first = next((i for i, c in enumerate(read["cards"]) if here(c)), None)
    cards = [c for c in read["cards"] if not here(c)]
    fresh = [{"key": card_key(sheet, row, i), "sheet": sheet, "row": row, "line": i, "text": text,
              "seconds": seconds, "time": timecode(seconds, form)} for i, text in enumerate(statements or [])]
    place = len(cards) if first is None else first
    cards[place:place] = fresh
    out = dict(read.get("quotes") or {})
    out.pop(at, None)
    said = [str(q or "") for q in quotes or []]
    if any(said):
        out[at] = {"sheet": sheet, "row": row, "seconds": seconds, "time": timecode(seconds, form),
                   "quotes": [{"key": card_key(sheet, row, i), "text": text} for i, text in enumerate(said) if text]}
    return dict(read, cards=cards, quotes=out)


def pick_moves(version: dict, now: dict, then: dict) -> list[dict]:
    """What a change to the workbook does to a board's picks, `now` and `then` being `read_cards`'s
    answers before and after it. The board is taken as a save would leave it now, its picks' words
    read afresh, and followed into `then` (see `follow`). Each pick that moves or is dropped is one
    entry: its label's id and title, its key, and `to`, the key it moves to, or None when it is
    dropped. A pick that stays, inverted commas gained or lost, is no entry. Nothing is written."""
    before = normalise(follow(version, now["cards"], now["quotes"]), quote_keys(now["quotes"]))
    texts = {q["key"]: q["text"] for row in now["quotes"].values() for q in row.get("quotes") or []}
    before["quoted"] = {k: texts[k] for chosen in before["picks"].values() for k in chosen if k in texts}
    moves: dict = {}
    after = normalise(follow(before, then["cards"], then["quotes"], moves), quote_keys(then["quotes"]))
    titles = {g["id"]: g["label"] for g in before["groups"]}
    out = []
    for gid, chosen in before["picks"].items():
        for k in chosen:
            to = moves.get((gid, k), k)
            if to is None or to not in (after["picks"].get(gid) or []):
                out.append({"label": gid, "title": titles.get(gid, ""), "key": k, "to": None})
            elif to != k:
                out.append({"label": gid, "title": titles.get(gid, ""), "key": k, "to": to})
    return out


def with_new(version: dict, cards: list[dict], height=None) -> dict:
    """A board, followed and normalised (see `follow`), with a card for every live line it has never
    seen, a statement written after the board was made (30 October), each in the nearest free spot to
    the middle of the canvas, the cards there already measured as the line reads now, and not loose, so
    it waits in the sidebar's Not placed. That is the card `merge` sends the page, which the canvas
    shows under Not placed and his next save keeps, so every board op takes the statement as one of the
    board's. `cards` is the statements as `read_cards` gives them, and `height` is as `layout_boxes`
    takes it. Nothing is written."""
    stored = version["cards"]
    live = {c["key"]: c for c in cards}
    fresh = [k for k in live if k not in stored]
    if not fresh:
        return version
    # the cards there already, as the page draws them: a changed line at its height as it reads now
    shown = dict(version, cards={k: dict(c, text=live[k]["text"]) if k in live else c for k, c in stored.items()})
    spots = place_new(fresh, {k: c["text"] for k, c in live.items()}, shown, height)
    return dict(version, cards={**stored, **{k: dict(spots[k], text=live[k]["text"]) for k in fresh}})


def merge(cards: list[dict], version: dict, quotes=None) -> dict:
    """The live cards and a stored board, or a revision of one, as the page draws them.

    The board's keys follow their words first (see `follow`), with `quotes` the quotes as
    `read_cards` reads them, or a set of the quote keys the workbook holds, which drops a pick whose
    quote has gone without following it. Then a stored card shows the line as it reads now. When
    that differs from the text the board was made with, the card is marked `changed` and carries the
    stored text as `stored`. A stored card whose line has gone is marked `missing` and shows the
    stored text in its place. A live line the board has never seen is a `new` card, in the nearest
    free spot to the middle of the canvas. `discard_reasons` is why a statement was left out, an
    agent's reason or an AI proposal's from before, for the pile.
    """
    if isinstance(quotes, dict):
        live = quote_keys(quotes)
    else:
        live, quotes = (set(quotes) if quotes is not None else None), None
    version = normalise(follow(version, cards, quotes), live)
    stored = version["cards"]
    live = {c["key"]: c for c in cards}
    # a line the board has never seen where `with_new` puts it, so the canvas and an agent's op agree
    spots = with_new(version, cards)["cards"]

    out = []
    for card in cards:
        key = card["key"]
        item = dict(card)
        if key in stored:
            item.update(x=stored[key]["x"], y=stored[key]["y"])
            if stored[key].get(LOOSE):
                item[LOOSE] = True
            if stored[key]["text"] != card["text"]:
                item.update(changed=True, stored=stored[key]["text"])
        else:
            item.update(x=spots[key]["x"], y=spots[key]["y"], new=True)
        out.append(item)
    for key, card in stored.items():
        if key in live:
            continue
        sheet, row, line = split_card_key(key)
        out.append({"key": key, "sheet": sheet, "row": row, "line": line, "text": card["text"],
                    "seconds": None, "time": "", "x": card["x"], "y": card["y"], "missing": True,
                    **({LOOSE: True} if card.get(LOOSE) else {})})
    # why a statement was left out, by card key: the board's `ai` under a name of its own, because `ai`
    # on the screen's answers is the bar's AI state. `stickies` is the board's sticky notes, under a name
    # of its own because `notes` on the screen's answers says a save keeps a theme's note, and a server
    # from before the sticky notes sends none. `stacks` is each top's stacked statements, and a server
    # from before them sends none. `not_same` is the close pairs marked Not the same, and a server from
    # before them sends none
    return {"cards": out, "groups": version["groups"], "discarded": version["discarded"],
            "picks": version["picks"], "discard_reasons": (version.get("ai") or {}).get("discarded") or {},
            "stickies": version.get("notes") or [],
            "stacks": version.get("stacks") or {}, "not_same": version.get("not_same") or []}


def summary(version: dict, raw: dict | None = None) -> dict:
    """A board as the board menu lists it, with `with_ai` when an agent made it (see `made_said`), and
    `v`, its version (see `board_version`), from `raw`, the board as the file holds it, when `version`
    is a normalised copy, and none when `raw` is empty, a board the file does not hold yet."""
    out = {k: version.get(k) for k in ("id", "name", "note", "created", "updated")}
    held = version if raw is None else raw
    if held:
        out["v"] = board_version(held)
    said = made_said(version)
    if said:
        out["with_ai"] = said
    # a reviewer's own board of a participant someone else works on (see `OWN_FILE`)
    if version.get(OWN) or (raw or {}).get(OWN):
        out[OWN] = True
    return out


# ------------------------------------------------------------- open, save

def state(workbook: Path, case: str, read: dict | None = None, board: str | None = None) -> dict:
    """Everything the Themes screen draws for one case, read afresh from the workbook and the file.

    Opening writes nothing: a case with no themes file yet is offered its first board, every card
    in the pile, and the file is written on his first move. `quotes` is the quotes of every row
    that has any, for the panel, `picks` the current board's picks with any whose quote has gone
    left out, and `history` the current board's revisions, newest first, without their states.
    The answer keeps the names the API had before boards, `versions`, `version` and `current`.
    `board` puts that board on the canvas in place of the current one, when the file holds it, and
    writes nothing, so another case opens on its Current board as it stands. `complete` is the PETs
    phase marked complete, or None. `sids` is each statement's short id, which the Inspector shows
    after its timecode and the command line names it by (see `short_ids`).
    """
    workbook = Path(workbook)
    read = read or read_cards(workbook)
    data = load(workbook)
    version = (find_version(data, board) if board else None) or current_version(data)
    saved = version is not None
    if version is None:
        version = blank_version(read["cards"])
    merged = merge(read["cards"], version, read["quotes"])
    versions = [summary(v) for v in boards_of(data)]
    return {"schema": SCHEMA, "case": case, "workbook": workbook.name, "sheets": read["sheets"],
            "current": version.get("id") or FIRST_VERSION, "chosen": chosen_of(data),
            "complete": complete_of(data), "versions": versions or [summary(version)],
            "version": summary(normalise(version), version), "saved": saved, "quotes": read["quotes"],
            "history": history_list(version), "sids": short_ids(read["cards"]), **merged}


def chosen_of(data: dict | None) -> str | None:
    """The Current board's id, the one he is going with, or None when the file marks none or names
    a board it no longer holds. Never the board on the canvas, which is `current`."""
    chosen = (data or {}).get("chosen")
    ids = {str(b.get("id")) for b in boards_of(data)}
    return str(chosen) if chosen not in (None, "") and str(chosen) in ids else None


def complete_of(data: dict | None) -> dict | None:
    """The PETs phase marked complete, `{"at", "board", "name"}`, or None when the file has no mark
    or one not in that shape. `name` is the board's name as the file holds it now while it holds
    the board, and the name it had when it was marked once it is gone, so the mark always names the
    board it was marked on."""
    held = (data or {}).get("complete")
    if not isinstance(held, dict) or not isinstance(held.get("at"), str) or not held["at"].strip():
        return None
    board = str(held.get("board") or "")
    live = find_version(data, board) if board else None
    name = str((live or {}).get("name") or held.get("name") or "")
    return {"at": held["at"], "board": board, "name": name}


def pets_complete_of(workbook: Path) -> dict | None:
    """The PETs mark of a case for a row of the case list, or None, and None for a themes file
    that cannot be read. Reads the one file beside the workbook and nothing else."""
    try:
        return complete_of(load(workbook))
    except (WorkbookError, OSError):
        return None


def chosen_name(workbook: Path) -> str | None:
    """The Current board's name for the case list's row, or None when the themes file marks none.

    Read-only and cheap: `chosen` is written before `boards`, so a file whose head carries no
    `chosen` is never parsed, and one that does is read for `chosen` and the boards' names alone. A
    case with no themes file, or one that cannot be read, gives None, and nothing is ever written.
    """
    try:
        text = themes_path(workbook).read_text(encoding="utf-8")
    except (OSError, ValueError):
        return None
    if '"chosen"' not in text.split('"boards"', 1)[0]:
        return None
    try:
        data = json.loads(text)
    except ValueError:
        return None
    if not isinstance(data, dict):
        return None
    vid = chosen_of(data)
    name = " ".join(str((find_version(data, vid) or {}).get("name") or "").split()) if vid else ""
    return name or None


def _file(workbook: Path, case: str, data: dict, versions: list[dict], current: str, when: str) -> dict:
    out = {"schema": SCHEMA, "case": case, "workbook": Path(workbook).name,
           "created": str(data.get("created") or when), "updated": when, "current": current}
    # the Current board sits beside `current`, and only while it names a board the file holds, so
    # a board deleted takes its mark with it
    chosen = chosen_of(dict(data, boards=versions))
    if chosen:
        out["chosen"] = chosen
    # the PETs marked complete comes after it, and stays as it stands whatever happens to the board
    # it names
    if complete_of(data):
        out["complete"] = data["complete"]
    out["boards"] = versions
    # anything a later stage adds at the top of the file survives a write from this one, and the
    # boards' old key never comes back
    for key, value in data.items():
        if key not in ("versions", "chosen"):
            out.setdefault(key, value)
    return out


def save(workbook: Path, version: dict, case: str, revision=None) -> dict:
    """Write one board into the themes file, as the current one, and nothing else anywhere.

    The other boards in the file are kept as they are, and so is this one's history. The file
    carries the case by its pseudonym, the workbook's file name, the schema, and when it was made
    and last written. A board the file does not hold is refused, so a page left open on a board
    deleted since can never put it back: with no file yet, only the first board, the one an open
    offers, is taken. A pick whose quote has gone from the workbook is dropped on the way in, and
    the board keeps the name and the note the file holds.

    `revision` of `auto` is the page's timer: the board as the file held it before this save goes
    into its history as an automatic revision, at the time of this save, when it differs from the
    board's last revision. The answer then carries the revision made and the history. Until 30
    October 2026 it took the time the board was last written, which a statement's edit and a
    revision kept since did not move, so it could list between revisions dated otherwise (histdate).

    A board with picks is read against the workbook: its keys follow their words (see `follow`),
    and `quoted` is written afresh, the words of every quote the picks name as the workbook reads
    now. The page never sends `quoted` or `cut`: the cut cards are the file's, kept as they are.

    Nor does it send `made` or `changed`, what an AI agent did to the board, which stay as the file
    holds them. A page whose `updated` is older than an agent's change to the board is refused with
    OUTSIDE, its canvas kept in the board's history as CANVAS_KEPT (see `keep_canvas`), so neither
    the agent's change nor his work is lost. A page whose `v` is not the board's for any other
    reason, another window's save among them, is refused with StaleBoard and nothing written, and
    Overwrite on the page sends the version the refusal names (19 October).
    """
    workbook = Path(workbook)
    if not isinstance(version, dict):
        raise WorkbookError(i18n.t("server.board_canvas_nothing_written"))
    sent = version
    data = load(workbook) or {}
    when = now_iso()
    versions = boards_of(data)
    at = next((i for i, v in enumerate(versions) if str(v.get("id")) == str(version.get("id") or FIRST_VERSION)), None)
    # the board as the file holds it: the picks' words and the cut cards are the file's, never the page's
    old = normalise(versions[at]) if at is not None else {}
    live, read = None, None
    if version.get("picks"):
        try:
            read = read_cards(workbook)
        except (WorkbookError, OSError):
            read = None
    if read is not None:
        live = quote_keys(read["quotes"])
        version = follow(dict(version, quoted=old.get("quoted") or {}, cut=[]), read["cards"], read["quotes"])
    kept = normalise(version, live)
    kept["updated"] = when
    kept.pop("quoted", None)
    kept.pop("cut", None)
    named = [k for chosen in kept["picks"].values() for k in chosen]
    if read is not None:
        texts = {q["key"]: q["text"] for row in read["quotes"].values() for q in row["quotes"]}
    else:
        texts = old.get("quoted") or {}
    quoted = {k: texts[k] for k in named if k in texts}
    if quoted:
        kept["quoted"] = quoted
    if old.get("cut"):
        kept["cut"] = old["cut"]
    made = None
    if at is None:
        if versions or kept["id"] != FIRST_VERSION:
            raise WorkbookError(i18n.t("server.board_longer_themes_file_nothing"))
        versions.append(kept)
    else:
        # the name and the note belong to the board ops, so a save from the canvas, perhaps sent
        # just before a rename landed, never puts back the ones it carried
        was = versions[at]
        # a page that last saw this board before an agent changed it never saves over the change:
        # its canvas goes into the board's history instead, and the save is refused with the line
        # the page shows beside its own corner line
        if outside_since(was, sent):
            keep_canvas(was, state_of(kept), at=when)
            write(workbook, _file(workbook, case, data, versions, str(data.get("current") or kept["id"]), when))
            raise WorkbookError(i18n.t("server.board_changed_conversation_canvas_saved"), code="board_changed_outside")
        # and one that last read the board before another window saved it, or before any other
        # change, is refused with nothing written, its canvas still on the page (19 October)
        refuse_stale(was, sent.get("v"), i18n.t("server.board_changed_since_page_loaded"))
        # a label sent with no key for a field keeps the file's, its description or its domain (see `fields_kept`)
        kept = fields_kept(kept, sent.get("groups"), was.get("groups"))
        kept.update(created=str(was.get("created") or kept["created"]),
                    name=str(was.get("name") or kept["name"]), note=str(was.get("note") or ""))
        # what an agent did to the board is the file's, and the page never sends it
        for key in AGENT_KEYS:
            kept.pop(key, None)
            mark = made_mark(was.get(key)) if key == "made" else agent_mark(was.get(key))
            if mark:
                kept[key] = mark
        # a page from before the reasons sends no `ai`, and the ones the file holds stay, and the page
        # sends no `review` or `revise`, what the app's own AI left with a board before 11 November 2026,
        # so the ones the file holds stay as they are
        for key in ("ai",) + FROM_BEFORE:
            if key not in sent and normalise(was).get(key):
                kept[key] = normalise(was)[key]
        # and a page from before the stacks sends no `stacks`, so the file's stay as they were
        if "stacks" not in sent and normalise(was).get("stacks"):
            kept = normalise(dict(kept, stacks=normalise(was)["stacks"]))
        # and one from before the close pairs sends no `not_same`, so the pairs he marked stay marked
        if "not_same" not in sent and normalise(was).get("not_same"):
            kept = normalise(dict(kept, not_same=normalise(was)["not_same"]))
        # and a page from before the sticky notes sends no `notes`, so the file's stay as they were,
        # each freed whose group the save took away
        if "notes" not in sent:
            held_notes = notes_of(normalise(was), {g["id"] for g in kept["groups"]}, set(kept["cards"]))
            if held_notes:
                kept["notes"] = held_notes
        # a board an agent made is marked edited by his first save that changes it
        if kept.get("made"):
            kept["made"] = edited_mark(kept["made"], kept, when, kept.get("changed"))
        held = {"history": history_of(was)}
        if revision == "auto":
            made = add_revision(held, auto=True, at=when, state=board_state(was))
        if held["history"]:
            kept["history"] = held["history"]
        versions[at] = kept
    write(workbook, _file(workbook, case, data, versions, kept["id"], when))
    out = {"saved": True, "updated": when, "version": summary(kept)}
    if made:
        out.update(revision=revision_summary(made), history=history_list(kept))
    return out


# ------------------------------------------------------------- the history

STATE_KEYS = ("cards", "groups", "discarded", "picks", "stacks", "not_same", "notes", "ai", "quoted", "cut")
# what a board holds only when it has some, which a revision and a change through the API carry the same way
STATE_OPTIONAL = ("stacks", "not_same", "notes", "ai", "quoted", "cut")


def state_of(kept: dict) -> dict:
    """A normalised board as a revision holds it: its cards, groups, discards and picks, and its
    sticky notes, the AI's reasons, the picks' words and the cut cards when it has them, so a
    revision's hash takes a note's words, its colour and its place."""
    out = {key: kept[key] for key in ("cards", "groups", "discarded", "picks")}
    for key in STATE_OPTIONAL:
        if kept.get(key):
            out[key] = kept[key]
    return out


def board_state(board: dict) -> dict:
    """What a revision holds of a board, as the file holds it (see `state_of`)."""
    return state_of(normalise(board))


def state_hash(state: dict) -> str:
    """A stable hash of a board's state, the same for the same state whatever order it was built in."""
    text = json.dumps(state, sort_keys=True, ensure_ascii=False, separators=(",", ":"))
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def places_print(board: dict) -> str:
    """A short print of where a board puts its cards, a board or a revision's state alike (copyback2, 8 November
    2026): each card by its key, each PET and sub-PET by its id, its title and its members in order, the stacks,
    the bin and the cards on the canvas in no PET. The board's name, its times, its notes, the cards' words and
    where anything sits on the canvas are left out, so a board sent and sent back untouched prints the same
    whatever its sender has reworded or moved on his own since."""
    v = normalise(board)
    held = {"cards": sorted(v["cards"]), "loose": sorted(k for k, c in v["cards"].items() if c.get(LOOSE)),
            "groups": [[g["id"], g["label"], list(g["members"])] for g in v["groups"]],
            "discarded": sorted(v["discarded"]), "stacks": {k: list(x) for k, x in (v.get("stacks") or {}).items()}}
    text = json.dumps(held, sort_keys=True, ensure_ascii=False, separators=(",", ":"))
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:16]


def history_of(board: dict) -> list[dict]:
    """A board's revisions, oldest first in the order they were made, each one with an id and a state.

    Each revision carries the time it was made. An automatic one kept before 30 October 2026 took the
    time its board was last written, which a statement's edit and a revision kept since did not move,
    so it could read earlier than the revision made before it (histdate). Such a one reads at that
    revision's time, the earliest it can have been made, so History lists in order on a board saved
    with the fault, with nothing written on open, and the board's next write keeps that time."""
    held = board.get("history") if isinstance(board, dict) else None
    out = [r for r in held or [] if isinstance(r, dict) and str(r.get("id") or "") and isinstance(r.get("state"), dict)]
    for before, revision in zip(out, out[1:]):
        then, at = iso_time(before.get("at")), iso_time(revision.get("at"))
        if revision.get("auto") and then is not None and at is not None and at < then:
            revision["at"] = before["at"]
    return out


def revision_summary(revision: dict) -> dict:
    """A revision for the History tab and the command line: its id, time, English name and whether it was automatic,
    and for one the app named, its kind and slots (see `revision_mark`), so the page says it in its own language."""
    out = {"id": str(revision["id"]), "at": str(revision.get("at") or ""),
           "name": str(revision.get("name") or ""), "auto": bool(revision.get("auto"))}
    kind, slots = revision_mark(revision)
    if kind:
        out.update(kind=kind, slots=slots)
    return out


# The revisions the app names itself (i18nleft2, 1 November 2026). Each carries a mark of what it is, `kind`, and
# the words that fill it, `slots`, and code finds one by its kind, never by its words. `name` keeps the English, as
# the file keeps the workbook's headings, for the command line, MCP and a reader from before marks. The page shows
# the name through the catalogue, `themes.revision.named.<kind>`, in the reader's language. A revision kept before
# marks carries only the English name, and `revision_mark` reads its kind and slots back from those words.
REVISION_SAID = {
    "canvas_kept": lambda **v: i18n.t("themes.revision.named.canvas_kept", v, lang="en", method="ipa"),
    "reload_kept": lambda **v: i18n.t("themes.revision.named.reload_kept", v, lang="en", method="ipa"),
    "before_restoring": lambda **v: i18n.t("themes.revision.named.before_restoring", v, lang="en", method="ipa"),
    "before_copy": lambda **v: i18n.t("themes.revision.named.before_copy", v, lang="en", method="ipa"),
    "before_copy_revision": lambda **v: i18n.t("themes.revision.named.before_copy_revision", v, lang="en",
                                               method="ipa"),
    "before_changes": lambda **v: i18n.t("themes.revision.named.before_changes", v, lang="en", method="ipa"),
    "statement_edited": lambda **v: i18n.t("themes.revision.named.statement_edited", v, lang="en", method="ipa"),
    "statement_edited_bare": lambda **v: i18n.t("themes.revision.named.statement_edited_bare", v, lang="en",
                                                method="ipa"),
    "brought_in": lambda **v: i18n.t("themes.revision.named.brought_in", v, lang="en", method="ipa"),
    # a board a teammate sent through Working together (wtboard, 9 November 2026)
    "team_board": lambda **v: i18n.t("themes.revision.named.team_board", v, lang="en", method="ipa"),
    # a thematic analysis project's code list (codes, 2 November 2026): a change to it, and the list made
    "codes_changed": lambda **v: i18n.t("themes.revision.named.codes_changed", v, lang="en", method="ipa"),
    "codes_listed": lambda **v: i18n.t("themes.revision.named.codes_listed", v, lang="en", method="ipa"),
    "codes_listed_moved": lambda **v: i18n.t("themes.revision.named.codes_listed_moved", v, lang="en", method="ipa"),
}
# what fills each kind's words
REVISION_SLOTS = {"canvas_kept": (), "reload_kept": (), "before_restoring": ("when",),
                  "before_copy": ("label", "board"), "before_copy_revision": ("label", "board", "when"),
                  "before_changes": ("who",), "statement_edited": ("who", "old", "new"),
                  "statement_edited_bare": ("old", "new"), "brought_in": ("file",), "team_board": ("who",), "codes_changed": ("what",),
                  "codes_listed": ("codes",), "codes_listed_moved": ("codes", "names")}
# the time a `when` names, as ISO, kept beside the slots (i18nleft3, 2 November 2026), so the page says it in the
# reader's language and formats (thWhen) where the English name keeps it as the History said it then
WHEN_AT = "when_at"


def slots_kept(kind: str, held: dict | None) -> dict:
    """The slots a revision of `kind` keeps from `held`: each of its words, and `when_at` beside a `when`."""
    held = held or {}
    out = {n: str(held.get(n, "")) for n in REVISION_SLOTS[kind]}
    if "when" in out and held.get(WHEN_AT):
        out[WHEN_AT] = str(held[WHEN_AT])
    return out


class RevisionName(str):
    """A revision's English name that knows its kind and slots, so it keeps its mark through the code that passes
    names along as text (a statement's edit line, from the route to every board's History)."""

    kind: str = ""
    slots: dict = {}


def revision_name(kind: str, **slots) -> RevisionName:
    """The English name of a revision the app names, carrying its kind and slots (see `REVISION_SAID`). A `when_at`
    gives a `when` its words, in English and its own formats, as the file keeps the name."""
    if "when" in REVISION_SLOTS[kind] and slots.get(WHEN_AT) and not slots.get("when"):
        slots["when"] = when_said(slots[WHEN_AT], lang="en")
    made = RevisionName(" ".join(REVISION_SAID[kind](**slots).split()))
    made.kind, made.slots = kind, slots_kept(kind, slots)
    return made


@functools.lru_cache(maxsize=1)
def _read_back() -> tuple:
    """Each kind's English as a pattern its slots are read back from, the most slots first, so a name is read as
    the kind that accounts for all of its words."""
    out = []
    for kind, names in sorted(REVISION_SLOTS.items(), key=lambda kv: -len(kv[1])):
        english = REVISION_SAID[kind](**{n: "\x00" + n + "\x00" for n in names})
        pattern = re.escape(english)
        for n in names:
            pattern = pattern.replace(re.escape("\x00" + n + "\x00"), f"(?P<{n}>.+?)")
        out.append((kind, re.compile("^" + pattern + "$", re.S)))
    return tuple(out)


def revision_mark(revision: dict) -> tuple[str, dict]:
    """A revision's kind and slots: its own mark, or for one kept before marks, read back from its English name. A
    revision named by hand or by an agent has none, ("", {})."""
    kind = str(revision.get("kind") or "")
    if kind in REVISION_SAID:
        held = revision.get("slots") if isinstance(revision.get("slots"), dict) else {}
        return kind, slots_kept(kind, held)
    name = str(revision.get("name") or "")
    if not name or revision.get("auto"):
        return "", {}
    for kind, pattern in _read_back():
        found = pattern.match(name)
        if found:
            return kind, {n: found.group(n) for n in REVISION_SLOTS[kind]}
    return "", {}


CANVAS_KEPT = revision_name("canvas_kept")
RELOAD_KEPT = revision_name("reload_kept")


def history_list(board: dict) -> list[dict]:
    """A board's revisions newest first, without their states, for the History tab."""
    return [revision_summary(r) for r in reversed(history_of(board))]


def add_revision(board: dict, name: str = "", auto: bool = False, at: str | None = None,
                 state: dict | None = None, kind: str = "", slots: dict | None = None) -> dict | None:
    """A revision of the board added to its history: its state now, or `state`, at `at` or now.

    An automatic one is made only when the state differs from the board's last revision, by a
    stable hash, and past AUTO_KEEP automatic ones the oldest of them goes. Every other revision,
    by hand or before a restore or a copy, is kept. One the app names keeps its `kind` and `slots`, given here or
    carried by a `revision_name`. The revision made, or None when none was.
    """
    history = history_of(board)
    state = board_state(board) if state is None else state
    if auto and history and state_hash(history[-1]["state"]) == state_hash(state):
        return None
    numbers = [int(str(r["id"])[1:]) for r in history if str(r["id"])[:1] == "r" and str(r["id"])[1:].isdigit()]
    made = {"id": f"r{max(numbers, default=0) + 1}", "at": at or now_iso(),
            "name": " ".join(str(name or "").split()), "auto": bool(auto),
            "state": json.loads(json.dumps(state))}
    # a revision the app names keeps its mark, given or carried by its name (see `revision_name`)
    kind = kind or getattr(name, "kind", "")
    if kind in REVISION_SAID:
        held = slots if slots is not None else getattr(name, "slots", {})
        made.update(kind=kind, slots=slots_kept(kind, held))
    history.append(made)
    autos = [r for r in history if r.get("auto")]
    if len(autos) > AUTO_KEEP:
        old = {id(r) for r in autos[:len(autos) - AUTO_KEEP]}
        history = [r for r in history if id(r) not in old]
    board["history"] = history
    return made


# A statement he edits, from any screen, leaves one line in the History of each board that holds a card of it
# (histreplace, Adam, 30 October 2026, by dialog: "Add a History line"), the board kept as it stood before the edit,
# named for the participant and the statement's words before and after. A long statement shows the words round the
# change, EDIT_AROUND words each side of it, with an ellipsis for the rest, and each side is cut at a word past
# EDIT_WORDS characters.
EDIT_WORDS = 60
EDIT_AROUND = 3


def edit_words(old: str, new: str, room: int = EDIT_WORDS) -> tuple[str, str]:
    """A statement's words before and after as its History line says them: whole when both fit in `room`, else
    the part that changed, with EDIT_AROUND words of what stayed on each side of it and an ellipsis for the rest,
    each cut at a word past `room` characters."""
    a, b = words(old).split(), words(new).split()
    if len(" ".join(a)) <= room and len(" ".join(b)) <= room:
        return " ".join(a), " ".join(b)
    lead = 0
    while lead < min(len(a), len(b)) and a[lead] == b[lead]:
        lead += 1
    tail = 0
    while tail < min(len(a), len(b)) - lead and a[-1 - tail] == b[-1 - tail]:
        tail += 1
    start = max(0, lead - EDIT_AROUND)

    def shown(said: list[str]) -> str:
        end = len(said) - max(0, tail - EDIT_AROUND)
        text = " ".join(said[start:end])
        cut = len(text) > room
        if cut:
            text = text[:room].rsplit(" ", 1)[0].rstrip(",.:;")
        return ("…" if start else "") + text + ("…" if cut or end < len(said) else "")

    return shown(a), shown(b)


def edit_line(who: str, old: str, new: str) -> str:
    """The History line a statement's edit leaves: `Juno's statement edited: "..." to "..."` (see `edit_words`)."""
    was, now = edit_words(old, new)
    who = words(who)
    return (revision_name("statement_edited", who=who, old=was, new=now) if who
            else revision_name("statement_edited_bare", old=was, new=now))


def when_said(at: str, now: datetime | None = None, lang: str | None = None) -> str:
    """A revision's time the way the History tab says it (thWhen): `12:04` today, `1 October 12:04` on
    another day this year, and the year after the month on a day of another year, in the formats in force and the
    run's language (i18nleft3), or in `lang`'s own alone for words a file keeps (`formats.chosen`)."""
    try:
        then = datetime.fromisoformat(str(at)).astimezone()
    except ValueError:
        return str(at)
    now = now or datetime.now().astimezone()
    clock = formats.clock_words(then, lang)
    if then.date() == now.date():
        return clock
    day = formats.date_words(then, lang=lang) if then.year != now.year else formats.day_words(then, lang)
    return i18n.t("themes.history.when", day=day, time=clock, lang=lang)


def copy_into(source: dict, gid: str, target: dict) -> tuple[dict, str]:
    """A theme of one board copied onto another, and the id it has there.

    A card exists once on a board, so nothing is duplicated: every card under the theme at any
    depth leaves whatever group holds it on the target and comes out of the bin there, and a group
    on the target that loses every member goes, and so does one above it left with none. The theme
    arrives as fresh groups, its label, its note, its description, its sub-themes in the same shape with theirs and
    its picks with their words, laid out as a round blob, its cards in the order they read on the source, and set in
    the nearest spot to the middle of the target's cards that is clear of every card, label,
    frame and sticky note there by four margins, or to the right of them all. A card the target
    has never held comes with its words. The theme's sticky notes stay behind, since a note is his
    own word to himself on that board, and the target's own stay as they were, a note whose group
    the copy empties standing free. A statement on top of a stack brings its stack, the same
    statements under it on the target, out of wherever the target held them.
    """
    src = normalise(source)
    tgt = normalise(target)
    by_id = {g["id"]: g for g in src["groups"]}
    tree, queue = [], [gid]
    while queue:
        at = queue.pop(0)
        if at in tree:
            continue
        tree.append(at)
        queue.extend(m for m in by_id[at]["members"] if m in by_id)
    keys = [k for k in cards_under(by_id, gid) if k in src["cards"]]
    # each top copied brings its stack, the statements under it leaving wherever the target holds them
    src_stacks = src.get("stacks") or {}
    under = {k: [x for x in src_stacks[k] if x in src["cards"]] for k in keys if src_stacks.get(k)}
    held = [x for xs in under.values() for x in xs]
    moved = set(keys) | set(held)

    had = {g["id"] for g in tgt["groups"] if g["members"]}
    # the copy's ids are fresh, past every id the target held before it, a group it empties included
    numbers = [int(g["id"][1:]) for g in tgt["groups"] if g["id"][:1] == "g" and g["id"][1:].isdigit()]
    for g in tgt["groups"]:
        g["members"] = [m for m in g["members"] if m not in moved]
    tgt["discarded"] = [k for k in tgt["discarded"] if k not in moved]
    while True:
        empty = {g["id"] for g in tgt["groups"] if g["id"] in had and not g["members"]}
        if not empty:
            break
        tgt["groups"] = [g for g in tgt["groups"] if g["id"] not in empty]
        for g in tgt["groups"]:
            g["members"] = [m for m in g["members"] if m not in empty]
        for e in empty:
            tgt["picks"].pop(e, None)
    for k in keys + held:
        if k not in tgt["cards"]:
            tgt["cards"][k] = dict(src["cards"][k])
    stacks = {t: [x for x in xs if x not in moved] for t, xs in (tgt.get("stacks") or {}).items()}
    for k, xs in under.items():
        # what the target stacked under the top, or under a statement now under it, stays under the top
        extra = stacks.pop(k, []) + [y for x in xs for y in stacks.pop(x, [])]
        stacks[k] = xs + [x for x in extra if x not in xs and x != k]
    tgt["stacks"] = {t: xs for t, xs in stacks.items() if xs}
    reasons = (tgt.get("ai") or {}).get("discarded") or {}
    for k in moved:
        reasons.pop(k, None)
    if tgt.get("ai") and not reasons:
        tgt.pop("ai")

    n = max(numbers, default=0)
    ids = {}
    for old in tree:
        n += 1
        ids[old] = f"g{n}"

    drawn_src = layout_boxes(src)
    texts = {k: tgt["cards"][k]["text"] for k in keys}
    shape = blob(gid, by_id, lambda g: theme_order(src, g, drawn_src), texts, src["picks"])
    # what stays where it is: every card of the target but the ones the copy takes
    drawn = layout_boxes(dict(tgt, cards={k: c for k, c in tgt["cards"].items() if k not in moved}))
    others = (list(drawn["cards"].values()) + list(drawn["labels"].values()) + list(drawn["frames"].values())
              + list(drawn["notes"].values()))
    middle = (0.0, 0.0)
    if drawn["cards"]:
        box = union(drawn["cards"].values())
        middle = (box[0] + box[2] / 2, box[1] + box[3] / 2)
    ox, oy = round(middle[0] - shape["w"] / 2), round(middle[1] - shape["h"] / 2)
    dx, dy = free_offset([(ox, oy, shape["w"], shape["h"])], others, COPY_GAP)
    ox, oy = ox + dx, oy + dy
    for k, (x, y) in shape["cards"].items():
        tgt["cards"][k].update(x=round(ox + x), y=round(oy + y))
    for old in tree:
        lx, ly = shape["labels"].get(old, (0, 0))
        # the label whole, its note and its description with it, under its new id where the copy lands
        fresh = dict(by_id[old], id=ids[old], members=[ids.get(m, m) for m in by_id[old]["members"] if m in ids or m in moved],
                     x=round(ox + lx), y=round(oy + ly))
        tgt["groups"].append(fresh)
        if src["picks"].get(old):
            tgt["picks"][ids[old]] = list(src["picks"][old])
            # the picks' words go with them, so they follow their quotes on the board copied to
            for k in src["picks"][old]:
                if k in (src.get("quoted") or {}):
                    tgt.setdefault("quoted", {})[k] = src["quoted"][k]
    return normalise(tgt), ids[gid]


def _tree(by_id: dict, gid: str) -> list:
    """A theme's shape, each label under it by its id with its members, to tell whether it changed."""
    out, stack, seen = [], [gid], set()
    while stack:
        at = stack.pop()
        if at in seen or at not in by_id:
            continue
        seen.add(at)
        out.append((at, tuple(by_id[at]["members"])))
        stack.extend(m for m in by_id[at]["members"] if m in by_id)
    return sorted(out)


def land(version: dict, revised: dict, height=None) -> dict:
    """A board with a change's labels and picks landed on it, `revised` holding `groups`, each label
    by its id with its title, its note and its members, and `picks`, as `themes_ai.revise_ops`
    leaves them, and `made`, the ids of the labels the change made, when it has any: a change that
    comes from the command line, where no canvas is open to land it. Each label keeps whatever else
    the board's label of its id carried, its domain among it (see `label_landed`).

    Everything the change did not touch keeps its place. A theme whose labels or members changed,
    and a theme new to the board, is laid out afresh as a round blob (see `blob`), its cards in the
    order they read, and set where its frame stood, or for a new one where most of its statements
    came from, or the nearest spot to that clear of everything else by four margins. A sticky note
    in such a theme goes with it, down the right of its cards inside its frame. A theme left where it
    stood whose retitled label now meets something is laid out afresh too. A statement the change
    took out of every theme goes to the nearest free spot to the middle, the margin clear of
    everything there. The bin is as it was. Nothing overlaps, and nothing is written. `height` is as
    `layout_boxes` takes it."""
    v = normalise(version)
    before = layout_boxes(v, height)
    old_by = {g["id"]: g for g in v["groups"]}
    old_parents = parents_of(v["groups"])
    # each label from the board's own, whole, the change's title, note, description and members over it
    made = {str(m) for m in revised.get("made") or []}
    groups = [label_landed(old_by.get(g["id"]), g, g["id"] in made) for g in revised.get("groups") or []]
    after = normalise(dict(v, groups=groups, picks=dict(revised.get("picks") or {})))
    by_id = {g["id"]: g for g in after["groups"]}
    parents = parents_of(after["groups"])
    gone = off_canvas(after)
    tops = [g["id"] for g in after["groups"] if g["id"] not in parents]
    old_tops = {g for g in old_by if g not in old_parents}
    touched = [t for t in tops if t not in old_tops or _tree(by_id, t) != _tree(old_by, t)]
    texts = {k: c.get("text") or "" for k, c in after["cards"].items()}
    drawn = layout_boxes(after, height)
    loose_before = {k for k in v["cards"] if k not in gone and k not in old_parents}
    loose = [k for k in after["cards"] if k not in gone and k not in parents]
    freed = [k for k in loose if k not in loose_before]

    def under(t: str) -> set:
        return {g for g, _ in _tree(by_id, t)}

    def obstacles(skip: set) -> dict:
        out = {}
        for t in tops:
            if t not in skip and t not in touched and t in drawn["frames"]:
                out[f"frame:{t}"] = drawn["frames"][t]
        for k in loose:
            if k not in freed:
                out[f"card:{k}"] = drawn["cards"][k]
        held = set().union(*(under(t) for t in touched)) if touched else set()
        for n in after.get("notes") or []:
            if n.get("in") not in held:
                out[f"note:{n['id']}"] = drawn["notes"][n["id"]]
        return out

    # a theme left where it stood whose frame now meets something, a label retitled longer, moves too
    for t in [t for t in tops if t not in touched]:
        others = obstacles({t})
        if t in drawn["frames"] and any(clash(drawn["frames"][t], box) for box in others.values()):
            touched.append(t)
    fixed = obstacles(set())
    boxes = [before["cards"][k] for k in before["cards"]]
    middle = (0.0, 0.0)
    if boxes:
        box = union(boxes)
        middle = (box[0] + box[2] / 2, box[1] + box[3] / 2)
    old_top = {}
    for t in old_tops:
        for k in cards_under(old_by, t):
            old_top[k] = t

    for t in touched:
        shape = blob(t, by_id, lambda g: theme_order(after, g, drawn), texts, after["picks"], height)
        held = under(t)
        notes = [n for n in after.get("notes") or [] if n.get("in") in held]
        tall_notes = sum(note_height(n.get("text")) for n in notes) + MARGIN * max(0, len(notes) - 1)
        w = shape["w"] + (MARGIN + NOTE_W if notes else 0)
        h = max(shape["h"], tall_notes + 2 * FRAME_Y)
        if t in before["frames"]:
            ox, oy = before["frames"][t][0], before["frames"][t][1]
        else:
            came = [old_top[k] for k in cards_under(by_id, t) if k in old_top and old_top[k] in before["frames"]]
            if came:
                frm = before["frames"][max(set(came), key=lambda x: (came.count(x), x))]
                ox, oy = frm[0], frm[1]
            else:
                ox, oy = middle[0] - w / 2, middle[1] - h / 2
        dx, dy = free_offset([(ox, oy, w, h)], list(fixed.values()), COPY_GAP)
        ox, oy = round(ox + dx), round(oy + dy)
        for k, (x, y) in shape["cards"].items():
            after["cards"][k].update(x=round(ox + x), y=round(oy + y))
        for g, (x, y) in shape["labels"].items():
            by_id[g].update(x=round(ox + x), y=round(oy + y))
        nx, ny = ox + shape["w"] - FRAME_X + MARGIN, oy + FRAME_Y
        for n in notes:
            n.update(x=round(nx), y=round(ny))
            ny += note_height(n.get("text")) + MARGIN
        fixed[f"frame:{t}"] = (ox, oy, w, h)

    if freed:
        stay = dict(after, cards={k: c for k, c in after["cards"].items() if k not in freed})
        spots = place_new(freed, texts, stay, height)
        for k in freed:
            after["cards"][k].update(x=spots[k]["x"], y=spots[k]["y"])
    return normalise(after)


def sync_labels(version: dict, height=None) -> dict:
    """Each label that holds something stored where the page draws it, above what it holds, as the
    page stores it on every layout, and the layout. `version` is normalised, and changed in place."""
    drawn = layout_boxes(version, height)
    for g in version["groups"]:
        if drawn["bodies"].get(g["id"]):
            x, y = drawn["labels"][g["id"]][:2]
            g["x"], g["y"] = round(x), round(y)
    return drawn


def _block(by_id: dict, version: dict, item: str) -> tuple[list, list, list]:
    """The labels, the cards and the sticky notes that move with `item`: a label with all it holds,
    a card alone, or a sticky note by its id."""
    notes = [n for n in version.get("notes") or [] if isinstance(n, dict) and n.get("id")]
    if item in by_id:
        labels = [g for g, _ in _tree(by_id, item)]
        return labels, cards_under(by_id, item), [n["id"] for n in notes if n.get("in") in labels]
    if item in (version.get("cards") or {}):
        return [], [item], []
    return [], [], [item]


def _shift(by_id: dict, version: dict, item: str, dx: float, dy: float) -> None:
    """`item` moved by (dx, dy) with all it holds, in place in `version`."""
    if not dx and not dy:
        return
    labels, cards, held = _block(by_id, version, item)
    for g in labels:
        by_id[g].update(x=round(by_id[g].get("x", 0) + dx), y=round(by_id[g].get("y", 0) + dy))
    for k in cards:
        c = version["cards"].get(k)
        if c is not None:
            c.update(x=round(c["x"] + dx), y=round(c["y"] + dy))
    for n in version.get("notes") or []:
        if isinstance(n, dict) and n.get("id") in held:
            n.update(x=round(n.get("x", 0) + dx), y=round(n.get("y", 0) + dy))


def land_kept(version: dict, revised: dict, height=None, strict: bool = False,
              statements_in: bool = False) -> dict | None:
    """A board with a change of what holds what landed on it the way the canvas lands one, keeping
    the layout: `revised` as `land` takes it.

    Whatever stays in the label it was in keeps its place, and so does a label with all it holds,
    its own arrangement whole. A label or a card taken up a level, to a label over the one it was
    in or to the top of the canvas, stays where it stands, as Remove from PET leaves it. A new label
    over things that all sat in one label wraps them where they stand, as `G` does. A label or a
    card put into a label elsewhere goes in under what that label holds, at its left, those that go
    into one label packed together. Then, level by level from the deepest, what moved goes to the
    nearest spot clear of its neighbours, and what stands beside a label that grew makes way for it
    by the least distance, so nothing overlaps. A statement in no PET or a sticky note in none that
    a frame now covers moves the same way. Nothing is written.

    With `strict`, a change that puts a statement into a label elsewhere, or a new label over things
    from more than one label, answers None, for `land` to lay out afresh. Without it, such a new
    label is laid out as a round blob (see `blob`) where most of what it holds came from. With
    `statements_in` as well, a statement put into a label elsewhere lands as a label does, under what
    that label holds, so it reads last there and its new neighbours keep their places, and only a new
    label over things from more than one label answers None (agentorder, 10 November 2026). `height`
    is as `layout_boxes` takes it."""
    v = normalise(version)
    old_by = {g["id"]: g for g in v["groups"]}
    old_parents = parents_of(v["groups"])
    # each label from the board's own, whole, the change's title, note, description and members over it
    made = {str(m) for m in revised.get("made") or []}
    groups = [label_landed(old_by.get(g["id"]), g, g["id"] in made) for g in revised.get("groups") or []]
    after = normalise(dict(v, groups=groups, picks=dict(revised.get("picks") or {})))
    by_id = {g["id"]: g for g in after["groups"]}
    parents = parents_of(after["groups"])
    gone = off_canvas(after)
    texts = {k: c.get("text") or "" for k, c in after["cards"].items()}

    def above(par: dict, x: str) -> list[str]:
        out, at = [], par.get(x)
        while at is not None and at not in out:
            out.append(at)
            at = par.get(at)
        return out

    def came_from(gid: str, seen: frozenset = frozenset()) -> set:
        """The labels, or None, that what a new label holds sat in before."""
        out = set()
        for m in by_id[gid]["members"]:
            if m in by_id and m not in old_by:
                if m not in seen:
                    out |= came_from(m, seen | {m})
            elif m in old_by or m in v["cards"]:
                out.add(old_parents.get(m))
        return out

    fresh = [g for g in by_id if g not in old_by and len(came_from(g)) > 1]
    if fresh and strict:
        return None
    # a fresh label inside another fresh one is laid out with it
    fresh = [g for g in fresh if not any(a in fresh for a in above(parents, g))]
    blobbed = {x for g in fresh for x, _ in _tree(by_id, g)} | {k for g in fresh for k in cards_under(by_id, g)}
    movers: list[str] = []
    into: dict[str, list[str]] = {}
    items = [g["id"] for g in after["groups"] if g["id"] in old_by] + [k for k in after["cards"] if k not in gone]
    for x in items:
        if x in blobbed:
            continue
        now, was = parents.get(x), old_parents.get(x)
        if now == was:
            continue
        movers.append(x)
        if now is None or now not in old_by or now in above(old_parents, x):
            continue
        if x not in by_id and strict and not statements_in:
            return None
        into.setdefault(now, []).append(x)
    movers += [g for g in by_id if g not in old_by and g not in blobbed] + fresh
    tall = height or (lambda _key, text: card_height(text))

    # a new label made empty (20 October), as G with nothing selected and New group inside make one: inside
    # a label it goes in under what that label holds, and at the top it stands below the whole board, so it
    # reads last
    empty = [g for g in by_id if g not in old_by and g not in blobbed and not by_id[g]["members"]]
    if empty:
        d = layout_boxes(after, height)
        tops = [f for g, f in d["frames"].items() if g not in parents and g not in empty]
        boxes = tops + [b for k, b in d["cards"].items() if k not in gone]
        foot = max((b[1] + b[3] for b in boxes), default=0)
        left = min((f[0] for f in tops), default=0)
        for g in empty:
            if parents.get(g) is not None:
                into.setdefault(parents[g], []).append(g)
            else:
                by_id[g].update(x=round(left), y=round(foot + 4 * MARGIN))
                foot += (d["frames"].get(g) or (0, 0, 0, 40))[3] + 4 * MARGIN

    # what goes into a label elsewhere, packed under what that label holds, the deepest first
    for target in sorted(into, key=lambda g: -depth_of(parents, g)):
        coming = into[target]
        d = layout_boxes(after, height)
        sizes = [(d["frames"][m][2], d["frames"][m][3]) if m in by_id else (CARD_W, tall(m, texts.get(m))) for m in coming]
        spots = pack_round(sizes, MARGIN)
        stay = [m for m in by_id[target]["members"] if m not in coming]
        boxes = [d["frames"][m] if m in by_id else d["cards"].get(m) for m in stay]
        boxes = [b for b in boxes if b]
        if boxes:
            body = union(boxes)
            ox, oy = body[0], body[1] + body[3] + MARGIN
        else:
            lab = d["labels"].get(target) or (by_id[target].get("x", 0), by_id[target].get("y", 0), 0, 0)
            ox, oy = lab[0], lab[1] + lab[3] + LABEL_GAP
        left = min(s[0] for s in spots)
        top = min(s[1] for s in spots)
        for m, (sx, sy) in zip(coming, spots):
            b = d["frames"][m] if m in by_id else d["cards"][m]
            _shift(by_id, after, m, ox + sx - left - b[0], oy + sy - top - b[1])

    # a new label over things from more than one label, laid out afresh where most of it came from
    if fresh:
        before = layout_boxes(v, height)
        drawn = layout_boxes(after, height)
        for g in fresh:
            shape = blob(g, by_id, lambda x: theme_order(after, x, drawn), texts, after["picks"], height,
                         depth_of(parents, g))
            homes = [old_parents.get(k) for k in cards_under(by_id, g)]
            homes = [h for h in homes if h in before["frames"]]
            if homes:
                frm = before["frames"][max(set(homes), key=lambda h: (homes.count(h), h))]
            else:
                firsts = [before["cards"][k] for k in cards_under(by_id, g) if k in before["cards"]]
                frm = firsts[0] if firsts else (0, 0, 0, 0)
            for k, (x, y) in shape["cards"].items():
                after["cards"][k].update(x=round(frm[0] + x), y=round(frm[1] + y))
            for lab, (x, y) in shape["labels"].items():
                by_id[lab].update(x=round(frm[0] + x), y=round(frm[1] + y))

    # then room made, level by level from the deepest, the PETs last
    moved = set(movers)
    sizes = {g: f[2:] for g, f in layout_boxes(v, height)["frames"].items()}

    def changed(gid: str, seen: frozenset = frozenset()) -> bool:
        if gid in moved or gid not in old_by:
            return True
        # a label retitled, or given a note's mark, grows or shrinks where it stands
        if sizes.get(gid) != d["frames"].get(gid, (0, 0, 0, 0))[2:]:
            return True
        if set(by_id[gid]["members"]) != set(old_by[gid]["members"]):
            return True
        return any(changed(m, seen | {m}) for m in by_id[gid]["members"] if m in by_id and m not in seen)

    levels = sorted(by_id, key=lambda g: -depth_of(parents, g)) + [None]
    for level in levels:
        for _ in range(3):
            d = sync_labels(after, height)
            if level is None:
                tops = [g for g in by_id if g not in parents]
                loose = [k for k in after["cards"] if k not in gone and k not in parents]
                free = [n["id"] for n in after.get("notes") or [] if isinstance(n, dict) and n.get("id")
                        and n.get("in") not in by_id]
                members, gap = tops + loose + free, COPY_GAP
            else:
                held = [n["id"] for n in after.get("notes") or [] if isinstance(n, dict) and n.get("in") == level]
                members, gap = list(by_id[level]["members"]) + held, MARGIN

            def box(m: str):
                if m in by_id:
                    return d["frames"].get(m)
                if m in d["cards"]:
                    return d["cards"][m]
                return d["notes"].get(m)

            # a statement in no PET or a free sticky note a frame now covers moves too
            if level is None:
                frames = [d["frames"][t] for t in tops if t in d["frames"]]
                covered = {m for m in loose + free if box(m) and any(clash(box(m), f) for f in frames)}
            else:
                covered = set()
            going = [m for m in members if (m in moved or m in covered) and box(m)]
            grown = [m for m in members if m in by_id and m not in moved and changed(m) and box(m)]
            pushed = False
            for m in going:
                others = [box(o) for o in members if o != m and box(o) and (o not in going or going.index(o) < going.index(m))]
                if any(clash(box(m), o) for o in others):
                    dx, dy = free_offset([box(m)], others, gap)
                    _shift(by_id, after, m, dx, dy)
                    d = sync_labels(after, height)
                    pushed = True
            # each neighbour a label that grew now meets moves out of its way by the least distance,
            # and in turn moves along what it then meets, as the canvas makes way
            queue, fixed = list(grown), set(going)
            while queue and len(fixed) < 4 * len(members) + 8:
                g = queue.pop(0)
                fixed.add(g)
                for o in members:
                    if o in fixed or not box(o) or not clash(box(g), box(o)):
                        continue
                    a, b = box(g), box(o)
                    ways = [(a[0] + a[2] + gap - b[0], 0), (a[0] - gap - b[0] - b[2], 0),
                            (0, a[1] + a[3] + gap - b[1]), (0, a[1] - gap - b[1] - b[3])]
                    dx, dy = min(ways, key=lambda w: abs(w[0]) + abs(w[1]))
                    _shift(by_id, after, o, dx, dy)
                    d = sync_labels(after, height)
                    pushed = True
                    if o not in queue:
                        queue.append(o)
            # anything still meeting another goes to the nearest free spot
            for m in members:
                if box(m) and any(o != m and box(o) and clash(box(m), box(o)) for o in members):
                    others = [box(o) for o in members if o != m and box(o)]
                    dx, dy = free_offset([box(m)], others, gap)
                    _shift(by_id, after, m, dx, dy)
                    d = sync_labels(after, height)
                    pushed = True
            if not pushed:
                break
    sync_labels(after, height)
    return normalise(after)


def order_of(version: dict, under: str | None, drawn: dict | None = None) -> list[str]:
    """The order the canvas, the PETs table and its exports read under a label, its statements and
    the labels inside it, or with `under` None the PETs. `version` is normalised."""
    by_id = {g["id"]: g for g in version["groups"]}
    if under is None:
        parents = parents_of(version["groups"])
        return canvas_order([g["id"] for g in version["groups"] if g["id"] not in parents], by_id)
    return theme_order(version, under, drawn)


def read_rows(spots: dict, band: float = ROW_BAND) -> list[list]:
    """The rows `read_order` reads ids in, each left to right, top row first."""
    rest = sorted(spots, key=lambda i: (spots[i][1], spots[i][0]))
    out = []
    while rest:
        top = spots[rest[0]][1]
        row = [i for i in rest if spots[i][1] - top < band]
        out.append(sorted(row, key=lambda i: (spots[i][0], spots[i][1])))
        rest = [i for i in rest if i not in row]
    return out


def reorder(version: dict, under: str | None, wanted: list[str], height=None) -> tuple[dict, dict]:
    """A board with what sits under one label, or with `under` None its PETs, set in the order
    `wanted` gives, those it leaves out after them in the order they read now. The canvas, the PETs
    table and its exports all read order from where things stand, so the order is set by moving them,
    and a drag afterwards works as before.

    Each one takes the place of the one that read at its turn before, a label with everything it
    holds, so the rows stay as they were and only the order changes. Where one is wider or taller
    than the one whose place it took, those after it along its row move right, and the rows below it
    move down, just far enough to stay clear, so nothing comes to overlap. A label that grows so and
    then meets a neighbour makes room the same way among its own neighbours, up to the PETs, and a
    statement in Not placed or a sticky note a PET now covers moves to the nearest free spot. Nothing
    is written.

    Answers the board and `info`: `before` and `order`, the order before and after, `moved`, those
    that moved, `how`, `kept` when each took another's place exactly and `room` when some moved along
    to make room, and `arranged`, each label above that made room among its neighbours, None for the
    PETs.

    A row under a shorter one than stood there before moves up, keeping the gap it had (19 October).
    Where moving up would change the order the rows read in, as among PETs of uneven heights, the
    rows keep their places as before and only move down."""
    try:
        return _reorder(version, under, wanted, height, close=True)
    except WorkbookError:
        return _reorder(version, under, wanted, height, close=False)


def _reorder(version: dict, under: str | None, wanted: list[str], height, close: bool) -> tuple[dict, dict]:
    """`reorder`, with `close` whether a row moves up into the room a shorter one above it leaves."""
    v = json.loads(json.dumps(normalise(version)))
    drawn = sync_labels(v, height)
    first = json.loads(json.dumps(v))
    gone = off_canvas(v)
    now = order_of(v, under, drawn)
    order = [m for m in wanted if m in now] + [m for m in now if m not in wanted]
    info = {"under": under, "before": now, "order": order, "moved": [], "how": "kept", "arranged": []}
    if order == now:
        return v, info

    def by_id() -> dict:
        return {g["id"]: g for g in v["groups"]}

    def notes() -> list[dict]:
        return [n for n in v.get("notes") or [] if isinstance(n, dict) and n.get("id")]

    def block(m: str) -> tuple[list, list, list]:
        """The labels, the cards and the sticky notes that move with `m`."""
        known = by_id()
        if m not in known:
            return [], [m], []
        labels = [g for g, _ in _tree(known, m)]
        return labels, cards_under(known, m), [n["id"] for n in notes() if n.get("in") in labels]

    def shift(m: str, dx: float, dy: float) -> None:
        if not dx and not dy:
            return
        labels, cards, held = block(m)
        known = by_id()
        for g in labels:
            known[g].update(x=round(known[g]["x"] + dx), y=round(known[g]["y"] + dy))
        for k in cards:
            if k in v["cards"]:
                v["cards"][k].update(x=round(v["cards"][k]["x"] + dx), y=round(v["cards"][k]["y"] + dy))
        for n in notes():
            if n["id"] in held:
                n.update(x=round(n.get("x", 0) + dx), y=round(n.get("y", 0) + dy))

    def box(d: dict, m: str):
        return d["frames"].get(m) if m in by_id() else d["cards"].get(m)

    def spot(d: dict, m: str, top: bool) -> tuple:
        """Where `m` reads from: a PET by its label, and inside a label a card by its corner and a
        label by its frame's."""
        if top:
            return d["labels"][m][0], d["labels"][m][1]
        b = box(d, m)
        return b[0], b[1]

    def hits(d: dict, m: str, parent: str | None) -> int:
        """How many of its neighbours, and of what stands beside them, `m` overlaps."""
        mine = box(d, m)
        if not mine:
            return 0
        others = [box(d, x) for x in order_of(v, parent, d) if x != m]
        if parent is None:
            parents = parents_of(v["groups"])
            others += [d["cards"][k] for k in v["cards"] if k not in parents and k not in gone and k in d["cards"]]
            others += [d["notes"][n["id"]] for n in notes() if n.get("in") not in by_id()]
        else:
            others += [d["notes"][n["id"]] for n in notes() if n.get("in") == parent]
        return sum(1 for o in others if o and clash(mine, o))

    def settle(parent: str | None, wanted_order: list[str]) -> bool:
        """`wanted_order` set in the places of the members of `parent` as they read now, the first
        in the first place, those along a row moved right and the rows below moved down just as far
        as keeps them clear. True when anything had to move along to make room."""
        d = sync_labels(v, height)
        top = parent is None
        reading = order_of(v, parent, d)
        spots = {m: spot(d, m, top) for m in reading}
        rows = read_rows(spots, CARD_H if top else ROW_BAND)
        place = {m: spots[s] for m, s in zip(wanted_order, reading)}
        gap = COPY_GAP if top else MARGIN
        placed, pushed, down = [], False, 0.0
        index = {s: i for i, s in enumerate(reading)}
        # the foot of the rows so far as they stood before and as they stand now, so each row keeps the
        # gap it had under the rows above it, moving up where a shorter one took a taller one's place
        # (19 October: a taller sub-PET moved down left a gap above the rows under it)
        was_foot = now_foot = None
        for row in rows:
            if close and was_foot is not None and placed:
                down = now_foot - was_foot
                pushed = pushed or abs(down) >= 1
            items = [wanted_order[index[s]] for s in row]
            spots_row, right = [], None
            for m in items:
                b = box(d, m)
                off = (b[0] - spots[m][0], b[1] - spots[m][1])
                x, y = place[m]
                bx = x + off[0]
                if right is not None and bx < right:
                    x, bx, pushed = x + right + gap - bx, right + gap, True
                spots_row.append((m, x, y, off, b))
                right = bx + b[2]
            need = 0.0
            for m, x, y, off, b in spots_row:
                mine = (x + off[0], y + off[1] + down, b[2], b[3])
                for o in placed:
                    if clash(mine, o) and o[1] < mine[1] + 1:
                        need = max(need, o[1] + o[3] + gap - mine[1])
            if need > 0:
                down, pushed = down + need, True
            for m, x, y, off, b in spots_row:
                now_spot = spot(d, m, top)
                shift(m, x - now_spot[0], y + down - now_spot[1])
                placed.append((x + off[0], y + off[1] + down, b[2], b[3]))
            olds = [box(d, s) for s in row if box(d, s)]
            foot = max((o[1] + o[3] for o in olds), default=None)
            if foot is not None:
                was_foot = foot if was_foot is None else max(was_foot, foot)
            now_foot = max(p[1] + p[3] for p in placed)
        if not top:
            # its own sticky notes kept clear of what it holds
            d = sync_labels(v, height)
            members = [box(d, m) for m in order_of(v, parent, d)]
            for n in notes():
                if n.get("in") != parent:
                    continue
                mine = d["notes"][n["id"]]
                if any(clash(mine, b) for b in members if b):
                    dx, dy = free_offset([mine], [b for b in members if b], MARGIN)
                    n.update(x=round(n.get("x", 0) + dx), y=round(n.get("y", 0) + dy))
                    pushed = True
        else:
            pushed = clear_top() or pushed
        return pushed

    def clear_top() -> bool:
        """A statement in no PET or a sticky note in none that a PET now covers, moved to the
        nearest free spot. True when one moved."""
        d = sync_labels(v, height)
        parents = parents_of(v["groups"])
        frames = [d["frames"][t] for t in order_of(v, None, d) if t in d["frames"]]
        covered = [k for k in v["cards"] if k not in parents and k not in gone and k in d["cards"]
                   and any(clash(d["cards"][k], f) for f in frames)]
        if covered:
            texts = {k: v["cards"][k].get("text") or "" for k in covered}
            spots = place_new(covered, texts, dict(v, cards={k: c for k, c in v["cards"].items() if k not in covered}), height)
            for k in covered:
                v["cards"][k].update(x=spots[k]["x"], y=spots[k]["y"])
        d = sync_labels(v, height)
        moved = bool(covered)
        for n in notes():
            if n.get("in") in by_id():
                continue
            mine = d["notes"][n["id"]]
            if any(clash(mine, f) for f in frames):
                others = frames + list(d["cards"].values()) + [b for k, b in d["notes"].items() if k != n["id"]]
                dx, dy = free_offset([mine], others, MARGIN)
                n.update(x=round(n.get("x", 0) + dx), y=round(n.get("y", 0) + dy))
                moved = True
        return moved

    if settle(under, order):
        info["how"] = "room"
    # a label that grew and now meets a neighbour makes room among them, up to the PETs
    child = under
    while child is not None:
        d = sync_labels(v, height)
        up = parents_of(v["groups"]).get(child)
        if hits(d, child, up) <= hits(drawn, child, up):
            break
        settle(up, order_of(v, up, d))
        info["arranged"].append(up)
        child = up
    final = sync_labels(v, height)
    if order_of(v, under, final) != order:
        raise WorkbookError(i18n.t("server.order_could_set_board_stands"))
    old = layout_boxes(first, height)
    info["moved"] = [m for m in order if (box(old, m) or (0, 0))[:2] != (box(final, m) or (0, 0))[:2]]
    return normalise(v), info


def order_kept(before: dict, after: dict, wanted: dict | None = None, named: list | None = None,
               height=None) -> dict:
    """The order each place on `after` should read in, by what `before` read: the PETs (None) and
    each label `before` had. What was there before reads as it did, in the places those of them read
    in now, and what came in keeps its place among them, but a statement or a label that came in from
    elsewhere, out of no label under this one, reads after the rest, in the order `named` gives
    (agentorder, 10 November 2026). `wanted` holds the order an `order` operation set for a place,
    which stands as set. Both boards are normalised."""
    wanted = wanted or {}
    named = [str(x) for x in named or []]
    old_by = {g["id"]: g for g in before["groups"]}
    old_parents = parents_of(before["groups"])
    stacked = {k: top for top, keys in (before.get("stacks") or {}).items() for k in keys or []}
    by_id = {g["id"]: g for g in after["groups"]}
    drawn_before, drawn_after = layout_boxes(before, height), layout_boxes(after, height)
    out = {}
    for place in [g for g in by_id if g in old_by] + [None]:
        now = order_of(after, place, drawn_after)
        if place in wanted:
            want = [m for m in wanted[place] if m in now]
            out[place] = want + [m for m in now if m not in want]
            continue
        was = [m for m in order_of(before, place, drawn_before) if m in now]

        def from_inside(m: str) -> bool:
            """Whether `m` came up from a label under this place, where it stands where it stood, or is
            a label new to the board, which reads where its making put it."""
            if m in by_id and m not in old_by:
                return True
            # a statement stacked before stood where its top did, so one taken out or made a top is from there
            at, seen = old_parents.get(stacked.get(m, m)), set()
            while at is not None and at not in seen:
                if at == place:
                    return True
                seen.add(at)
                at = old_parents.get(at)
            return place is None
        last = [m for m in now if m not in was and not from_inside(m)]
        last.sort(key=lambda m: named.index(m) if m in named else len(named))
        slots = iter(was)
        middle = [next(slots) if m in was else m for m in now if m not in last]
        out[place] = middle + last
    return out


def keep_order(before: dict, after: dict, wanted: dict | None = None, named: list | None = None,
               height=None) -> tuple[dict, list]:
    """`after` with every place reading in the order `order_kept` gives it, so a change leaves every
    label it does not name in the order it had (agentorder, 10 November 2026). The landing of a change
    and the room made for it move things by the least distance, which can carry a sub-PET past its
    neighbour's row or a PET up past another, and the canvas, the PETs table and its exports read order
    from where things stand. Each place that reads otherwise is set back by `reorder`, the deepest
    first and the PETs last, since a label set back can grow and move its neighbours, for a few rounds
    until all read as they should. Answers the board and the places set back."""
    before = normalise(before)
    v = normalise(after)
    fixed: list = []
    for _ in range(4):
        want = order_kept(before, v, wanted, named, height)
        parents = parents_of(v["groups"])
        drawn = layout_boxes(v, height)
        off = [p for p, w in want.items() if order_of(v, p, drawn) != w]
        if not off:
            break
        for place in sorted(off, key=lambda p: 0 if p is None else depth_of(parents, p) + 1, reverse=True):
            w = order_kept(before, v, wanted, named, height)[place]
            if order_of(v, place, layout_boxes(v, height)) == w:
                continue
            try:
                v, _info = reorder(v, place, w, height)
            except WorkbookError:
                continue
            if place not in fixed:
                fixed.append(place)
    return v, fixed


# ----------------------------------------------------------- the toolbar's tools (21 October)

# Auto-arrange's ways (Adam, 21 October, the toolbar drawings): a grid as it has always been, one card
# above another in the order they read down the PET, which carries its hierarchy, or all in a row
ARRANGE_WAYS = ("grid", "column", "row")
# Align's six and Spread's two, as the toolbar and a selection's right-click menu have them
ALIGN_WAYS = ("left", "centre", "right", "top", "middle", "bottom")
SPREAD_WAYS = ("across", "down")


def align_plan(boxes: dict, how: str, gap: float = MARGIN) -> dict:
    """Where each box goes, by its id, its top-left corner, for Align and Spread, as the page's
    thAlignPlan works it out, `boxes` each (x, y, w, h).

    Align moves each to the edge or the centre of the outermost of them, left, centre or right, top,
    middle or bottom, the others along the line keeping their order and moving along it only as far as
    keeps `gap` clear between them, so nothing comes to overlap. Spread keeps the first and the last
    where they stand, across by their left edges and down by their tops, and sets those between at even
    gaps, never under `gap`, the last moving on when they need more room."""
    ids = list(boxes)
    if len(ids) < 2:
        return {i: (boxes[i][0], boxes[i][1]) for i in ids}
    at = {i: [float(boxes[i][0]), float(boxes[i][1])] for i in ids}
    w = {i: boxes[i][2] for i in ids}
    h = {i: boxes[i][3] for i in ids}
    if how in ALIGN_WAYS:
        flat = how in ("left", "centre", "right")
        if how == "left":
            edge = min(at[i][0] for i in ids)
            for i in ids:
                at[i][0] = edge
        elif how == "right":
            edge = max(at[i][0] + w[i] for i in ids)
            for i in ids:
                at[i][0] = edge - w[i]
        elif how == "centre":
            mid = (min(at[i][0] for i in ids) + max(at[i][0] + w[i] for i in ids)) / 2
            for i in ids:
                at[i][0] = mid - w[i] / 2
        elif how == "top":
            edge = min(at[i][1] for i in ids)
            for i in ids:
                at[i][1] = edge
        elif how == "bottom":
            edge = max(at[i][1] + h[i] for i in ids)
            for i in ids:
                at[i][1] = edge - h[i]
        else:
            mid = (min(at[i][1] for i in ids) + max(at[i][1] + h[i] for i in ids)) / 2
            for i in ids:
                at[i][1] = mid - h[i] / 2
        # along the line in the order they stood, each moved on past any before it it would now meet
        axis = 1 if flat else 0
        size = h if flat else w
        placed = []
        for i in sorted(ids, key=lambda i: (boxes[i][1 if flat else 0], boxes[i][0 if flat else 1])):
            for _ in range(len(ids)):
                box = (at[i][0], at[i][1], w[i], h[i])
                hit = [p for p in placed if clash(box, (at[p][0], at[p][1], w[p], h[p]), gap)]
                if not hit:
                    break
                at[i][axis] = max(at[p][axis] + size[p] for p in hit) + gap
            placed.append(i)
    elif how in SPREAD_WAYS:
        axis = 0 if how == "across" else 1
        size = w if axis == 0 else h
        order = sorted(ids, key=lambda i: (at[i][axis], at[i][1 - axis]))
        first, last = order[0], order[-1]
        span = at[last][axis] + size[last] - at[first][axis]
        room = (span - sum(size[i] for i in order)) / (len(order) - 1)
        step = max(gap, room)
        pos = at[first][axis]
        for i in order:
            at[i][axis] = pos
            pos += size[i] + step
    return {i: (round(at[i][0]), round(at[i][1])) for i in ids}


def _solid_boxes(version: dict, drawn: dict) -> dict:
    """What each card, sticky note and label takes up on the canvas, a label its frame, or its label alone
    while it holds nothing."""
    out = dict(drawn["cards"])
    out.update(drawn["notes"])
    for gid, label in drawn["labels"].items():
        out[gid] = drawn["frames"][gid] if drawn["bodies"].get(gid) else label
    return out


def _neighbours_of(version: dict, item: str, drawn: dict) -> list:
    """What stands beside `item` where it is, in the same label or on the canvas, each a box."""
    by_id = {g["id"]: g for g in version["groups"]}
    parents = parents_of(version["groups"])
    notes = {n["id"]: n.get("in") for n in version.get("notes") or [] if isinstance(n, dict) and n.get("id")}
    home = notes.get(item) if item in notes else parents.get(item)
    home = home if home in by_id else None
    boxes = _solid_boxes(version, drawn)
    out = []
    for other, box in boxes.items():
        if other == item:
            continue
        there = notes.get(other) if other in notes else parents.get(other)
        there = there if there in by_id else None
        if there == home:
            out.append((other, box))
    return out


def _make_room(version: dict, moved: list[str], height=None) -> None:
    """What `moved` now meets beside it shifts clear by the least distance, a label with all it holds, and
    a label whose frame so grew makes room among its own neighbours in turn, up to the canvas, as the
    canvas settles after an act. In place."""
    by_id = {g["id"]: g for g in version["groups"]}
    parents = parents_of(version["groups"])
    todo = list(moved)
    seen = 0
    while todo and seen < 200:
        seen += 1
        item = todo.pop(0)
        drawn = sync_labels(version, height)
        mine = _solid_boxes(version, drawn).get(item)
        if not mine:
            continue
        for other, box in _neighbours_of(version, item, drawn):
            if other in moved or not clash(mine, box, MARGIN):
                continue
            rest = [b for o, b in _neighbours_of(version, other, drawn) if o != other]
            dx, dy = free_offset([box], rest, MARGIN)
            _shift(by_id, version, other, dx, dy)
            drawn = sync_labels(version, height)
            up = parents.get(other)
            if up is not None and up not in todo:
                todo.append(up)
        up = parents.get(item)
        if up is not None and up not in todo and up not in moved:
            todo.append(up)


def push_clear(version: dict, grown: list[str], height=None) -> list[str]:
    """Room made under what grew where it stands, as a GETs card does when a take brings it a description or a
    title a line longer (22 October). Each neighbour below it that it now meets, in the same label or on the
    canvas, moves straight down just far enough to keep the margin, a label with all it holds, and pushes what
    it then meets the same way, so a column keeps its order and its left edge. A label whose frame so grew
    pushes its own neighbours in turn, up to the canvas. What grew stays where it is, and nothing moves up or
    sideways. In place. Answers what moved, in the order it first moved."""
    by_id = {g["id"]: g for g in version.get("groups") or []}
    parents = parents_of(version.get("groups") or [])
    todo = list(dict.fromkeys(grown))
    moved: list[str] = []
    turns = 0
    while todo and turns < 500:
        turns += 1
        item = todo.pop(0)
        drawn = layout_boxes(version, height)
        mine = _solid_boxes(version, drawn).get(item)
        if mine:
            # nearest first, so the one just under it is pushed before what lies further down
            for other, box in sorted(_neighbours_of(version, item, drawn), key=lambda ob: (ob[1][1], ob[0])):
                if box[1] <= mine[1] or not clash(mine, box, MARGIN):
                    continue
                _shift(by_id, version, other, 0, math.ceil(mine[1] + mine[3] + MARGIN - box[1]))
                if other not in moved:
                    moved.append(other)
                if other not in todo:
                    todo.append(other)
        up = parents.get(item)
        if up is not None and up not in todo:
            todo.append(up)
    return moved


# How firmly each thing stands while a board settles after a change (agentoverlap, 31 October 2026), as the
# page's TH_FIRM: what the change touched leads, the one it reads first firmest, then a label whose frame grew
# as things inside it were pushed, then what a push moved, the earlier the firmer
FIRM_LEADS = 10 ** 6
FIRM_GREW = 10 ** 5
FIRM_PUSHED = 10 ** 4
SETTLE_PASSES = 40
# the server's sizes stand a pixel or so over the page's (see CARD_H), so a neighbour the page set a margin away
# reads a little nearer here, and only one nearer by more than this is pushed, a margin clear
SETTLE_SLACK = 2


def canvas_boxes(version: dict, height=None) -> tuple[dict, dict]:
    """What stands on a board's canvas, each card, sticky note and label by its box, a label by its frame or
    its label alone while it holds nothing, and where each stands, the id of the label it is in or None for
    the canvas. A statement waiting in Not placed, set aside or stacked under another is not on the canvas,
    as the page leaves it off (`thOnCanvas`)."""
    drawn = layout_boxes(version, height)
    groups = {g["id"] for g in version.get("groups") or []}
    parents = parents_of(version.get("groups") or [])
    notes = {n["id"]: n.get("in") for n in version.get("notes") or [] if isinstance(n, dict) and n.get("id")}
    waiting = set(waiting_keys(version))
    boxes, homes = {}, {}
    for item, box in _solid_boxes(version, drawn).items():
        if item in waiting:
            continue
        home = notes.get(item) if item in notes else parents.get(item)
        boxes[item] = tuple(box)
        homes[item] = home if home in groups else None
    return boxes, homes


def settle_change(before: dict, after: dict, height=None) -> list[str]:
    """A board a change left, made clear by the canvas's own rules for a drop (agentoverlap, 31 October 2026,
    Adam: a card an agent reworded stood over the card under it until he dragged it, and an unstack, an
    order of the PETs or a longer title could leave a frame over its neighbour). What the change touched,
    each card, sticky note and label whose box `after` moved, grew or brought onto the canvas since `before`,
    stays where it is and leads, the one that reads first firmest, so of two it touched the later makes way.
    Each neighbour, in the same label or on the canvas, that now stands nearer than the margin to one that
    leads, by more than the pixel or two the server's sizes run over the page's (SETTLE_SLACK), is pushed a
    margin clear of it by the least distance, a label with all it holds, and pushes on what it then
    meets in the next pass, the deepest labels first so a frame has followed what moved inside it before it
    is weighed, and a label whose frame so grew pushes its own neighbours, up to the canvas, as the page's
    `thSettle` does a drag's drop. Every label is then stored where the page draws it. Sizes are the server's
    estimates, the quotes on cards never among them, since the page makes their room as a view. In place in
    `after`. Answers what a push moved, in the order it first moved, and nothing when the change left
    everything clear."""
    was, _ = canvas_boxes(before, height)
    boxes, homes = canvas_boxes(after, height)
    touched = [i for i, box in boxes.items() if was.get(i) != box]
    if not touched:
        return []
    by_id = {g["id"]: g for g in after.get("groups") or []}
    parents = parents_of(after.get("groups") or [])
    firm = {i: FIRM_LEADS - n for n, i in enumerate(read_order({i: boxes[i][:2] for i in touched}))}

    def grew(item: str, box: tuple) -> bool:
        old = was.get(item)
        return (item in by_id and old is not None and (box[0] < old[0] - 0.5 or box[1] < old[1] - 0.5
                or box[0] + box[2] > old[0] + old[2] + 0.5 or box[1] + box[3] > old[1] + old[3] + 0.5))

    pushed: list[str] = []
    for turn in range(SETTLE_PASSES):
        shifted = False
        places = sorted(set(homes.values()), key=lambda h: -1 if h is None else -(depth_of(parents, h) + 1))
        for place in places:
            # a frame follows what a push inside it moved
            boxes, homes = canvas_boxes(after, height)
            items = [i for i in boxes if homes[i] == place]
            index = {i: n for n, i in enumerate(items)}
            level = {i: firm.get(i, FIRM_GREW if grew(i, boxes[i]) else -1) for i in items}
            standing = {i for i in items if level[i] >= 0}

            def over(o: str, n: str) -> bool:
                return o != n and level[o] >= 0 and (level[o] > level[n] or (level[o] == level[n] and index[o] < index[n]))

            for n in sorted(items, key=lambda i: (level[i], index[i])):
                if not any(o in standing and over(o, n) and clash(boxes[o], boxes[n], MARGIN - SETTLE_SLACK) for o in items):
                    continue
                dx, dy = free_offset([boxes[n]], [boxes[o] for o in items if over(o, n)], MARGIN)
                if not dx and not dy:
                    continue
                _shift(by_id, after, n, dx, dy)
                b = boxes[n]
                boxes[n] = (b[0] + dx, b[1] + dy, b[2], b[3])
                level[n] = firm[n] = FIRM_PUSHED - turn
                if n not in pushed:
                    pushed.append(n)
                shifted = True
        if not shifted:
            break
    if pushed:
        sync_labels(after, height)
    return pushed


def arrange(version: dict, gid: str, way: str = "grid", height=None) -> dict:
    """A theme's cards tidied under its label in the order they read now, as Auto-arrange does on the
    canvas: `grid`, rows about as wide as the square root of what it holds, `column`, one above another
    down the PET, or `row`, all side by side. Each sub-theme is arranged inside its own frame first, the
    same way, and set in the block as one piece where it read, and the theme's own sticky notes come at
    its end. The block keeps its top-left corner, so the label stays where it stands, and what its frame
    now meets makes room. Answers the board, normalised, nothing written. Refused for a label the board
    does not have, or one that holds nothing."""
    if way not in ARRANGE_WAYS:
        raise WorkbookError(i18n.t("server.auto_arrange_s_ways_nothing", ways=', '.join(ARRANGE_WAYS)))
    v = json.loads(json.dumps(normalise(version)))
    by_id = {g["id"]: g for g in v["groups"]}
    if gid not in by_id:
        raise WorkbookError(i18n.t("server.label_board_nothing_changed"))
    drawn = sync_labels(v, height)
    body = drawn["bodies"].get(gid)
    if not body:
        raise WorkbookError(i18n.t("server.nothing_under_arrange_nothing_changed", label=by_id[gid]['label']))
    picks = v.get("picks") or {}
    notes = [n for n in v.get("notes") or [] if isinstance(n, dict) and n.get("id")]

    def size(m, body=0):
        if m in by_id:
            subs = any(x in by_id for x in by_id[m]["members"])
            marks = bool(str(by_id[m].get("note") or "").strip()) + bool(picks.get(m))
            return label_size(by_id[m]["label"], subs, marks, description_of(by_id[m]), body,
                              domain=str(by_id[m].get(DOMAIN) or ""))
        if m in drawn["cards"]:
            return drawn["cards"][m][2], drawn["cards"][m][3]
        return drawn["notes"][m][2], drawn["notes"][m][3]

    def block(g, seen):
        own = [m for m in theme_order(v, g, drawn) if m in by_id or m in drawn["cards"]]
        held = read_order({n["id"]: (n.get("x", 0), n.get("y", 0)) for n in notes if n.get("in") == g})
        units = []
        for m in own + held:
            if m in seen:
                continue
            if m not in by_id:
                w, h = size(m)
                units.append({"id": m, "w": w, "h": h, "card": True, "note": m not in drawn["cards"]})
                continue
            inner = block(m, seen | {m})
            lw, lh = size(m, inner["w"])
            units.append({"id": m, "w": max(inner["w"], lw) + 2 * FRAME_X, "h": lh + LABEL_GAP + inner["h"] + 2 * FRAME_Y,
                          "inner": inner, "dx": FRAME_X, "dy": FRAME_Y + lh + LABEL_GAP, "card": False})
        if not units:
            return {"w": 0, "h": 0, "places": []}
        cols = 1 if way == "column" else len(units) if way == "row" else math.ceil(math.sqrt(len(units)))
        card = next((u["w"] for u in units if u["card"] and not u["note"]), CARD_W)
        width = math.inf if way == "row" else max(max(u["w"] for u in units), cols * card + (cols - 1) * MARGIN)
        places, x, y, tall, w = [], 0, 0, 0, 0
        for u in units:
            if x > 0 and x + u["w"] > width:
                y, x, tall = y + tall + MARGIN, 0, 0
            if u["card"]:
                places.append((u["id"], x, y, False))
            elif u["inner"]["places"]:
                places += [(i, x + u["dx"] + px, y + u["dy"] + py, lab) for i, px, py, lab in u["inner"]["places"]]
            else:
                places.append((u["id"], x + u["dx"], y + u["dy"] - LABEL_GAP - size(u["id"])[1], True))
            w, tall = max(w, x + u["w"]), max(tall, u["h"])
            x += u["w"] + MARGIN
        return {"w": w, "h": y + tall, "places": places}

    for item, px, py, lab in block(gid, {gid})["places"]:
        spot = (round(body[0] + px), round(body[1] + py))
        if lab:
            by_id[item].update(x=spot[0], y=spot[1])
        elif item in v["cards"]:
            v["cards"][item].update(x=spot[0], y=spot[1])
        else:
            for n in notes:
                if n["id"] == item:
                    n.update(x=spot[0], y=spot[1])
    _make_room(v, [gid], height)
    sync_labels(v, height)
    return normalise(v)


def align_items(version: dict, items: list[str], how: str, height=None) -> tuple[dict, list[str]]:
    """Cards, sticky notes and labels lined up or spread as Align and Spread do on the canvas (see
    `align_plan`), a label with all it holds, by its frame, then what they now meet beside them makes
    room. A label named with something inside it moves once, as itself. Answers the board, normalised,
    and those that moved. Nothing is written."""
    if how not in ALIGN_WAYS + SPREAD_WAYS:
        raise WorkbookError(i18n.t("server.one_align_s_spread_s"))
    v = json.loads(json.dumps(normalise(version)))
    by_id = {g["id"]: g for g in v["groups"]}
    parents = parents_of(v["groups"])
    drawn = sync_labels(v, height)
    solid = _solid_boxes(v, drawn)
    names = [i for i in dict.fromkeys(items) if i in solid]

    def above(i):
        at, out = parents.get(i), set()
        while at is not None and at not in out:
            out.add(at)
            at = parents.get(at)
        note = next((n.get("in") for n in v.get("notes") or [] if isinstance(n, dict) and n.get("id") == i), None)
        return out | ({note} if note else set())

    names = [i for i in names if not (above(i) & set(names))]
    need = 3 if how in SPREAD_WAYS else 2
    if len(names) < need:
        raise WorkbookError(i18n.t("server.spread_takes_cards", need=need) if how in SPREAD_WAYS
                            else i18n.t("server.align_takes_cards", need=need))
    plan = align_plan({i: solid[i] for i in names}, how)
    moved = []
    for i in names:
        dx, dy = plan[i][0] - solid[i][0], plan[i][1] - solid[i][1]
        if dx or dy:
            _shift(by_id, v, i, dx, dy)
            moved.append(i)
    if moved:
        # what was lined up moves on as one, its own arrangement kept, until it is clear of what stands
        # beside it, so the cards not named stay where they were, as the canvas settles it
        drawn = sync_labels(v, height)
        mine = _solid_boxes(v, drawn)
        inside = set()
        for i in names:
            if i in by_id:
                inside |= {g for g, _ in _tree(by_id, i)} | set(cards_under(by_id, i))
        others = [b for i in names for o, b in _neighbours_of(v, i, drawn) if o not in names and o not in inside]
        dx, dy = free_offset([mine[i] for i in names], others, MARGIN)
        for i in names:
            _shift(by_id, v, i, dx, dy)
        ups = list(dict.fromkeys(parents[i] for i in names if parents.get(i) is not None))
        if ups:
            _make_room(v, ups, height)
        sync_labels(v, height)
    return normalise(v), moved


def board_op(workbook: Path, op: str, body: dict, case: str, dry_run: bool = False) -> dict:
    """A theme copied to another board, and a board's history, and the screen's state afterwards.

    `id` names the board, the current one when it does not, and `revision` one of its revisions.
    `revision` keeps one by hand, with `name` when he gives one. `view` answers with a revision as
    the page draws it, merged with the workbook as it reads now, and writes nothing. `restore` keeps
    a revision of the board as it stands, named "Before restoring 12:04", then makes the revision's
    state the board's. `copy` copies the theme `group` of the board, or of its revision, to the
    board `to`, which first keeps a revision named "Before Mornings copied from Board 1" so the
    copy can be undone there. A revision's keys follow their words before it is shown, restored or
    copied from, so it lands on the keys the workbook holds now. The workbook is only read. The
    answer shows the board `id` names, the board on the canvas, unless a copy went to another.
    With `dry_run` (26 October, for the agents' board ops) every check is made and nothing is
    written: the answer is the op, the board and what it would keep, restore or copy.
    """
    workbook = Path(workbook)
    if op not in BOARD_OPS:
        raise WorkbookError(i18n.t("server.something_board_can_do_nothing"), code="unknown_op")
    body = body if isinstance(body, dict) else {}
    read = read_cards(workbook)
    data = load(workbook) or {}
    boards = boards_of(data) or [blank_version(read["cards"])]
    ids = [str(b.get("id")) for b in boards]
    current = str(data.get("current")) if str(data.get("current")) in ids else ids[0]
    bid = str(body.get("id") or current)
    board = next((b for b in boards if str(b.get("id")) == bid), None)
    if board is None:
        raise WorkbookError(i18n.t("server.board_gone_themes_changed"))
    rid = str(body.get("revision") or "")
    revision = next((r for r in history_of(board) if str(r["id"]) == rid), None) if rid else None
    if (rid or op in ("view", "restore")) and revision is None:
        raise WorkbookError(i18n.t("server.revision_longer_board_s_history"))
    when = now_iso()
    name = str(board.get("name") or FIRST_NAME)

    if op == "view":
        merged = merge(read["cards"], revision["state"], read["quotes"])
        return dict(merged, op=op, revision=revision_summary(revision), board=summary(normalise(board), board))

    if op == "revision":
        made = add_revision(board, name=str(body.get("name") or "")[:200], at=when)
        extra = {"revision": revision_summary(made)}
    elif op == "restore":
        made = add_revision(board, name=revision_name("before_restoring", when_at=revision["at"]), at=when)
        # the revision's keys follow their words first, so a restore lands on the keys the workbook
        # holds now
        restored = json.loads(json.dumps(state_of(follow(revision["state"], read["cards"], read["quotes"]))))
        for key in STATE_OPTIONAL:
            board.pop(key, None)
        board.update({key: restored[key] for key in STATE_KEYS if key in restored}, updated=when)
        extra = {"revision": revision_summary(made), "restored": revision_summary(revision)}
    else:
        to = str(body.get("to") or "")
        target = next((b for b in boards if str(b.get("id")) == to), None)
        if target is None:
            raise WorkbookError(i18n.t("server.board_gone_themes_copied"))
        gid = str(body.get("group") or "")
        if target is board and revision is None:
            raise WorkbookError(i18n.t("server.board_already_nothing_copied", unit=unit(board, gid)))
        source = follow(revision["state"] if revision else board, read["cards"], read["quotes"])
        group = next((g for g in source["groups"] if g["id"] == gid), None)
        if group is None:
            raise WorkbookError(i18n.t("server.label_longer_board_nothing_copied"))
        source_name = f"{name} at {when_said(revision['at'])}" if revision else name
        made = add_revision(target, name=(revision_name("before_copy_revision", label=group["label"], board=name,
                                                        when_at=revision["at"]) if revision
                                          else revision_name("before_copy", label=group["label"], board=name)),
                            at=when)
        copied, new_id = copy_into(source, gid, follow(target, read["cards"], read["quotes"]))
        for key in ("notes", "ai", "quoted", "cut"):
            target.pop(key, None)
        target.update({key: copied[key] for key in STATE_KEYS if key in copied}, updated=when)
        extra = {"revision": revision_summary(made),
                 "copied": {"label": group["label"], "group": new_id, "to": str(target.get("id")),
                            "to_name": str(target.get("name") or FIRST_NAME), "from": source_name}}
    if dry_run:
        return dict(op=op, dry_run=True, board=bid, name=name, **extra)
    write(workbook, _file(workbook, case, data, boards, current, when))
    # the answer shows the board acted on, the one on the canvas, a copy to another board aside. It
    # is the current one, unless the screen opened on another case's Current board and has saved
    # nothing yet
    shown = bid if op != "copy" or str(body.get("to") or "") == bid else None
    return dict(state(workbook, case, read, board=shown), op=op, **extra)


# ---------------------------------------------------------------- the rows
#
# A trim, its undo, an assignment and its undo move rows in the workbook. The progress file moves
# with them through `rounds.rekey_rows`, and the themes file moves through `rekey`, in the same
# request and with the same row map, so the two never disagree.

def _row_map(keys, mapper) -> dict:
    """Where each card or quote key lands when its row moves: `mapper` takes a row key, `Initial:12`,
    and gives the row it moves to, or None when the row was cut. A key keeps its line. Rows merged
    into one, which only an assignment does, keep the first row's lines and stand the others' after
    them in sheet order, the way the workbook appends their entries, so no two keys meet. A key
    that is not a card's or a quote's stays as it is."""
    out, landing = {}, {}
    for key in keys:
        sheet, row, line = split_card_key(key)
        if row is None or line is None:
            out[key] = key
            continue
        moved = mapper(row_key(sheet, row))
        if moved is None:
            out[key] = None
            continue
        landing.setdefault(str(moved), {}).setdefault(row, []).append((line, key))
    for moved, rows in landing.items():
        sheet, _, number = moved.rpartition(":")
        base = 0
        for i, row in enumerate(sorted(rows)):
            shift = 0 if i == 0 else base
            for line, key in sorted(rows[row]):
                out[key] = card_key(sheet, int(number), line + shift)
                base = max(base, line + shift + 1)
    return out


def _moved(board: dict, mapper, cut: str | None = None, back: str | None = None) -> dict:
    """A board, or a revision's state, normalised, with its rows moved by `mapper` (see `_row_map`).

    The cards and the picks move with their rows, and so does every place the board names a key:
    the groups' members, the discards, the AI's reasons and the picks' words. A review from before
    11 November 2026 stays as the file holds it.
    Cards on a row that was cut leave the board for a record under `cut` with the trim's id `cut`:
    each card, the groups it sat in, whether it was discarded, the picks on its row with their words
    and the AI's reasons. `back` is the id of a trim being undone: its record's cards come back
    under their keys, into the groups that are still there, discarded where they were, with their
    picks, and the record goes. Every other record stays as it is, in the numbering of its trim.
    """
    v = normalise(board)
    reasons = dict((v.get("ai") or {}).get("discarded") or {})
    quoted = dict(v.get("quoted") or {})
    cmap = _row_map(set(v["cards"]), mapper)
    qmap = _row_map({k for chosen in v["picks"].values() for k in chosen} | set(quoted), mapper)
    gone = {k for k, m in cmap.items() if m is None}
    qgone = {k for k, m in qmap.items() if m is None}
    records = list(v.get("cut") or [])
    if gone or qgone:
        record = {"trim": str(cut or ""),
                  "cards": {k: v["cards"][k] for k in sorted(gone, key=_order) if k in v["cards"]},
                  "members": {g["id"]: [m for m in g["members"] if m in gone] for g in v["groups"]},
                  "discarded": [k for k in v["discarded"] if k in gone],
                  "picks": {g: [k for k in chosen if k in qgone] for g, chosen in v["picks"].items()}}
        record["members"] = {g: keys for g, keys in record["members"].items() if keys}
        record["picks"] = {g: keys for g, keys in record["picks"].items() if keys}
        if any(k in qgone for k in quoted):
            record["quoted"] = {k: t for k, t in quoted.items() if k in qgone}
        if any(k in gone for k in reasons):
            record["ai"] = {k: why for k, why in reasons.items() if k in gone}
        if record["cards"] or record["picks"]:
            records.append(record)

    def card(key):
        return cmap.get(key, key)

    def quote(key):
        return qmap.get(key, key)

    cards = {card(k): c for k, c in v["cards"].items() if card(k) is not None}
    groups = [dict(g, members=[card(m) for m in g["members"] if card(m) is not None]) for g in v["groups"]]
    discarded = [card(k) for k in v["discarded"] if card(k) is not None]
    picks = {g: [quote(k) for k in chosen if quote(k) is not None] for g, chosen in v["picks"].items()}
    quoted = {quote(k): t for k, t in quoted.items() if quote(k) is not None}
    reasons = {card(k): why for k, why in reasons.items() if card(k) is not None}

    def put_back(into: list, keys: list) -> list:
        # each key goes back where transcript order puts it among the keys there, which is where
        # it stood before the cut whenever the list ran in transcript order
        out = list(into)
        for k in keys:
            if k in out:
                continue
            at = next((i for i, m in enumerate(out) if split_card_key(m)[1] is not None and _order(m) > _order(k)),
                      len(out))
            out.insert(at, k)
        return out

    if back:
        by_id = {g["id"]: g for g in groups}
        kept = []
        for record in records:
            if record["trim"] != back:
                kept.append(record)
                continue
            for k, c in record["cards"].items():
                cards.setdefault(k, dict(c))
            for g, keys in record["members"].items():
                if g in by_id:
                    by_id[g]["members"] = put_back(by_id[g]["members"], keys)
            discarded = put_back(discarded, record["discarded"])
            for g, keys in record["picks"].items():
                if g in by_id:
                    picks[g] = put_back(picks.get(g, []), keys)
            quoted.update(record.get("quoted") or {})
            for k, why in (record.get("ai") or {}).items():
                reasons.setdefault(k, why)
        records = kept

    out = dict(v, cards=cards, groups=groups, discarded=discarded, picks=picks)
    # a stack and a pair marked Not the same move with their rows too, and a statement cut leaves them
    if v.get("stacks"):
        out["stacks"] = {card(t): [card(k) for k in ks if card(k) is not None]
                         for t, ks in v["stacks"].items() if card(t) is not None}
    if v.get("not_same"):
        out["not_same"] = [[card(a), card(b)] for a, b in v["not_same"] if card(a) is not None and card(b) is not None]
    for key in ("ai", "quoted", "cut"):
        out.pop(key, None)
    if reasons:
        out["ai"] = {"discarded": reasons}
    if quoted:
        out["quoted"] = quoted
    if records:
        out["cut"] = records
    return normalise(out)


@each_timepoint
def rekey(workbook: Path, mapper, cut: str | None = None, back: str | None = None) -> bool:
    """Move every board of the themes file, and every revision in its history, with rows the
    workbook has just moved (see `_moved`). `mapper` is the row map the progress file was moved by,
    `rounds.shift_key` and its kin. `cut` is the id of a trim that cut rows, whose cards go under
    each board's `cut` list, and `back` the id of a trim undone, whose cards come back.

    Then the keys follow their words against the workbook as it reads now (see `follow`), the way
    the next open would, so a row merged into another, or put back from one, lands on the keys its
    words have there, and the file agrees with the workbook and the progress file from the moment
    it is written.

    A case with no themes file has nothing to move, and nothing is written. A file that cannot be
    read is refused and left as it is. True when the file was written, which is only when something
    in it moved.
    """
    workbook = Path(workbook)
    path = themes_path(workbook)
    if not path.exists():
        return False
    try:
        data = load(workbook)
    except WorkbookError:
        raise WorkbookError(i18n.t("server.could_read_cards_were_moved", name=path.name))
    try:
        read = read_cards(workbook)
    except (WorkbookError, OSError):
        read = None

    def moved(board: dict) -> dict:
        fields = _moved(board, mapper, cut, back)
        return follow(fields, read["cards"], read["quotes"]) if read is not None else fields

    before = json.dumps(data, sort_keys=True, ensure_ascii=False)
    content = STATE_KEYS
    for board in boards_of(data):
        fields = moved(board)
        rest = {k: value for k, value in board.items() if k not in content}
        history = rest.pop("history", None)
        board.clear()
        board.update(rest)
        board.update({k: value for k, value in fields.items() if k in content})
        if history is not None:
            board["history"] = history
        for revision in board.get("history") or []:
            if isinstance(revision, dict) and isinstance(revision.get("state"), dict):
                revision["state"] = state_of(moved(revision["state"]))
    if json.dumps(data, sort_keys=True, ensure_ascii=False) == before:
        return False
    data["updated"] = now_iso()
    write(workbook, data)
    return True


@at_sheet_timepoint
def statement_edited(workbook: Path, sheet: str, row: int, line: int, old: str, new: str, said: str = "") -> int:
    """A statement edited in place on the PETs screen, carried to the other boards of the case, the boards of
    the timepoint its sheet is at when nothing set one, as an edit from a GETs, LGETs or LPETs board sets none.

    The board on the canvas takes the new words from the page. Every board whose card for that
    line held the words it read before, `old`, takes `new` as well, so no board marks the card
    changed for an edit made on this screen. A board whose card held other words, from a change
    made in Experiential statements or in Excel since that board last saw the line, keeps them and
    keeps its changed mark, since that change is news there. With `said`, the edit's History line
    (see `edit_line`), every board that holds a card of the line keeps itself first as it stood, as a
    revision of that name, its version unchanged by it (histreplace, 30 October 2026). Revisions are
    otherwise left as they were. A case with no themes file, or one that cannot be read or written, is
    left alone. Answers how many boards took the words, and writes only when one did or kept a line.
    """
    if not themes_path(workbook).exists():
        return 0
    try:
        data = load(workbook)
    except WorkbookError:
        return 0
    key, was, now = card_key(sheet, int(row), int(line)), words(old), words(new)
    took = noted = 0
    when = now_iso()
    for board in boards_of(data):
        cards = board.get("cards")
        card = cards.get(key) if isinstance(cards, dict) else None
        if not isinstance(card, dict) or was == now:
            continue
        if said:
            add_revision(board, name=said, at=when)
            noted += 1
        if words(card.get("text")) != was:
            continue
        before = json.loads(json.dumps({k: v for k, v in board.items() if k != "history"}))
        card["text"] = now
        card.pop("live", None)
        # a card that takes longer words stands taller, and what it now meets makes way (31 October)
        settle_change(before, board)
        took += 1
    if took or noted:
        data["updated"] = when
        try:
            write(workbook, data)
        except OSError:
            return 0
    return took


@at_sheet_timepoint
def statements_noted(workbook: Path, sheet: str, row: int, edits: dict, who: str) -> list[dict]:
    """A passage's statements reworded on the statements screen, each kept in the History of every board of the
    case that holds a card of it, the boards of the timepoint its sheet is at (histreplace, Adam, 30 October 2026,
    "Add a History line"): `edits` holds each line reworded in place by its place, with its words before and
    after (see `reworded`), and each board keeps itself as it stood, one revision a statement named for it (see
    `edit_line`). The cards keep their words, so a board shows the change as ever, the card marked changed. A case
    with no themes file, or one that cannot be read or written, is left alone. Answers each board that kept a
    line, its id, name and the keys, and writes only when one did."""
    if not edits or not themes_path(workbook).exists():
        return []
    try:
        data = load(workbook)
    except WorkbookError:
        return []
    when = now_iso()
    out = []
    for board in boards_of(data):
        cards = board.get("cards") if isinstance(board.get("cards"), dict) else {}
        keys = []
        for i, (was, now) in sorted(edits.items()):
            key = card_key(sheet, int(row), int(i))
            if isinstance(cards.get(key), dict) and words(was) != words(now):
                add_revision(board, name=edit_line(who, was, now), at=when)
                keys.append(key)
        if keys:
            out.append({"board": str(board.get("id")), "name": str(board.get("name") or ""), "keys": keys})
    if out:
        data["updated"] = when
        try:
            write(workbook, data)
        except OSError:
            return []
    return out


def reworded(old: list[str], new: list[str]) -> dict[int, tuple[str, str]]:
    """The lines of a passage a write rewords, by place, each with its words before and after: a
    line whose words changed in its own place, neither its old words nor its new ones standing in
    another place of the passage, so a line moved or put in between is left to `follow`."""
    was = [words(x) for x in old]
    now = [words(x) for x in new]
    return {i: (old[i], new[i]) for i in range(min(len(was), len(now)))
            if was[i] and now[i] and was[i] != now[i] and was[i] not in now and now[i] not in was}


@at_sheet_timepoint
def statements_written(workbook: Path, sheet: str, row: int, old: list[str], new: list[str],
                       changed: dict | None = None) -> list[dict]:
    """A passage's statements written from outside the PETs screen, by the command line, carried to
    every board of the case, as `statement_edited` carries an edit made on the canvas: each card
    of a line reworded in place (see `reworded`) that held its words before takes the new ones, so
    no board keeps the old wording. Each board that took words is stamped `updated`, and with
    `changed`, an agent's mark, marked changed in a conversation, so an open PETs screen says so and
    its next save never puts the old words back. Revisions are left as they were. Answers each board
    that took words, its id, name and the keys, and writes only when one did."""
    lines = reworded(old, new)
    if not lines or not themes_path(workbook).exists():
        return []
    try:
        data = load(workbook)
    except WorkbookError:
        return []
    when = now_iso()
    out = []
    for board in boards_of(data):
        cards = board.get("cards") if isinstance(board.get("cards"), dict) else {}
        took = []
        for i, (was, now) in lines.items():
            key = card_key(sheet, int(row), i)
            card = cards.get(key)
            if isinstance(card, dict) and words(card.get("text")) == words(was):
                card["text"] = words(now)
                card.pop("live", None)
                took.append(key)
        if took:
            board["updated"] = when
            if changed:
                board["changed"] = dict(changed, at=when)
            out.append({"board": str(board.get("id")), "name": str(board.get("name") or ""), "keys": took})
    if out:
        data["updated"] = when
        write(workbook, data)
    return out


def words_followed(state: dict, sheet: str, rows: dict) -> list[str]:
    """One board, or a revision's state, taking the words a find and replace put in (24 October 2026,
    "Everything follows"): `rows` is each row of `sheet` the replace changed, by its number, with `es`
    and `kq`, its statements and its quotes by place, each a pair of lists, the entries before and
    after. A card of a statement whose words were the old ones takes the new, and so does a pick's
    quote under `quoted`. A card holding other words, a change the board has yet to see, keeps them.
    The state is changed in place. Answers the card keys that took words."""
    took = []
    cards = state.get("cards") if isinstance(state.get("cards"), dict) else {}
    quoted = state.get("quoted") if isinstance(state.get("quoted"), dict) else {}
    for row, change in rows.items():
        old, new = change.get("es") or ([], [])
        for i in range(min(len(old), len(new))):
            card = cards.get(card_key(sheet, int(row), i))
            if isinstance(card, dict) and words(old[i]) != words(new[i]) and words(card.get("text")) == words(old[i]):
                card["text"] = words(new[i])
                card.pop("live", None)
                took.append(card_key(sheet, int(row), i))
        old, new = change.get("kq") or ([], [])
        for i in range(min(len(old), len(new))):
            key = card_key(sheet, int(row), i)
            if key in quoted and old[i] != new[i] and words(quoted[key]) == words(old[i]):
                quoted[key] = new[i]
    return took


@at_sheet_timepoint
def cards_reworded(workbook: Path, sheet: str, rows: dict, changed: dict | None = None) -> list[dict]:
    """A find and replace carried to every board of the case and every revision in their histories,
    one sheet at a time (see `words_followed`), so no board keeps the words it replaced and none marks
    a card changed for it. An undo carries the old words back the same way, its rows' lists the other
    way round. Each board that took words is stamped `updated`, and with `changed`, an agent's mark,
    marked changed in a conversation, so an open PETs screen says so and its next save never puts the
    old words back. A case with no themes file has none, and one that cannot be read is left as it is.
    Answers each board that took words, its id, name and the keys, and writes only when something in the
    file changed."""
    if not rows or not themes_path(workbook).exists():
        return []
    data = load(workbook)
    before = json.dumps(data, sort_keys=True, ensure_ascii=False)
    when = now_iso()
    out = []
    for board in boards_of(data):
        was = json.loads(json.dumps({k: v for k, v in board.items() if k != "history"}))
        took = words_followed(board, sheet, rows)
        if took:
            # a card that takes longer words stands taller, and what it now meets makes way (31 October)
            settle_change(was, board)
        for revision in board.get("history") or []:
            if isinstance(revision, dict) and isinstance(revision.get("state"), dict):
                words_followed(revision["state"], sheet, rows)
        if took:
            board["updated"] = when
            if changed:
                board["changed"] = dict(changed, at=when)
            out.append({"board": str(board.get("id")), "name": str(board.get("name") or ""), "keys": took})
    if json.dumps(data, sort_keys=True, ensure_ascii=False) != before:
        data["updated"] = when
        write(workbook, data)
    return out


# ------------------------------------------------- a passage's lines moved
# (20 October, from the PhD session's write that left 22 of 72 statements out of one participant's
# passages.) A write that removes a statement before the last of its passage moves every later line
# up, and a board kept on the old keys then showed each card with its neighbour's words, the removed
# statement's card left stale. A write now moves every board with its lines, by the line each
# statement of the write was, and takes the cards of the removed ones off.

SIMILAR = 0.6   # how alike two wordings are, by difflib's ratio, to be taken for one statement reworded


def passage_lines(old: list[str], new: list[str], named: list | None = None) -> dict[int, int | None]:
    """Where each line of a passage goes when a write leaves `new` in place of `old`: each old line
    by its place, to its new place or None when it was removed.

    `named` gives each new line the old line it is, by place, None for one new to the passage, when
    the write said so with each pair's key, and then nothing is guessed. Otherwise a line with the
    same words is that line, the nearest first. The lines left are taken by place when as many are
    left on both sides, so a line reworded in its place keeps its card, and else each to the most
    alike in order, at least SIMILAR alike, and an old line with no match was removed."""
    if named is not None and any(n is not None for n in named):
        out = {int(i): j for j, i in enumerate(named) if i is not None}
        return {i: out.get(i) for i in range(len(old))}
    was, now = [words(x) for x in old], [words(x) for x in new]
    out: dict[int, int] = {}
    used: set[int] = set()
    for j, w in enumerate(now):
        same = [i for i in range(len(was)) if w and was[i] == w and i not in out]
        if same:
            i = min(same, key=lambda i: (abs(i - j), i))
            out[i] = j
            used.add(j)
    left = [i for i in range(len(was)) if i not in out]
    fresh = [j for j in range(len(now)) if j not in used]
    if len(left) == len(fresh):
        out.update(zip(left, fresh))
    elif left and fresh:
        like = [[difflib.SequenceMatcher(None, was[i], now[j]).ratio() for j in fresh] for i in left]
        best = [[0.0] * (len(fresh) + 1) for _ in range(len(left) + 1)]
        for a in range(1, len(left) + 1):
            for b in range(1, len(fresh) + 1):
                s = like[a - 1][b - 1]
                best[a][b] = max(best[a - 1][b], best[a][b - 1],
                                 best[a - 1][b - 1] + s if s >= SIMILAR else 0.0)
        a, b = len(left), len(fresh)
        while a and b:
            s = like[a - 1][b - 1]
            if s >= SIMILAR and best[a][b] == best[a - 1][b - 1] + s:
                out[left[a - 1]] = fresh[b - 1]
                a, b = a - 1, b - 1
            elif best[a][b] == best[a - 1][b]:
                a -= 1
            else:
                b -= 1
    return {i: out.get(i) for i in range(len(old))}


def drop_cards(version: dict, keys) -> dict:
    """A board with each card of `keys` taken off it, as Remove does for a card missing from the
    workbook. A stack stays whole: when a top goes, the first statement under it that stays takes
    its place as the top (see `make_top`), the rest still under it. Every place the board names a
    card gone loses it, its label's members, the bin, the stacks, Not the same and the AI's reasons.
    Its labels stay, emptied or not. Nothing is written."""
    v = json.loads(json.dumps(normalise(version)))
    gone = {str(k) for k in keys if str(k) in v["cards"]}
    if not gone:
        return v
    for k in sorted(gone, key=_order):
        rest = [x for x in (v.get("stacks") or {}).get(k) or [] if x not in gone]
        if rest:
            v = make_top(v, rest[0])
    v["cards"] = {k: c for k, c in v["cards"].items() if k not in gone}
    for g in v["groups"]:
        g["members"] = [m for m in g["members"] if m not in gone]
    v["discarded"] = [k for k in v["discarded"] if k not in gone]
    if v.get("stacks"):
        v["stacks"] = {t: [k for k in ks if k not in gone] for t, ks in v["stacks"].items() if t not in gone}
    if v.get("not_same"):
        v["not_same"] = [p for p in v["not_same"] if not set(p) & gone]
    if v.get("ai"):
        v["ai"] = {"discarded": {k: why for k, why in v["ai"]["discarded"].items() if k not in gone}}
    return normalise(v)


def keys_renamed(version: dict, cmap: dict, qmap: dict) -> dict:
    """A board with its card keys renamed by `cmap` and its quote keys by `qmap`, everywhere it names
    them, a quote mapped to None leaving the picks. A key in neither stays. Nothing is written."""
    v = json.loads(json.dumps(normalise(version)))
    card = lambda k: cmap.get(k, k)
    quote = lambda k: qmap.get(k, k)
    v["cards"] = {card(k): c for k, c in v["cards"].items()}
    for g in v["groups"]:
        g["members"] = [card(m) for m in g["members"]]
    v["discarded"] = [card(k) for k in v["discarded"]]
    if v.get("stacks"):
        v["stacks"] = {card(t): [card(k) for k in ks] for t, ks in v["stacks"].items()}
    if v.get("not_same"):
        v["not_same"] = [[card(a), card(b)] for a, b in v["not_same"]]
    if v.get("ai"):
        v["ai"] = {"discarded": {card(k): why for k, why in v["ai"]["discarded"].items()}}
    v["picks"] = {g: [quote(k) for k in chosen if quote(k) is not None] for g, chosen in v["picks"].items()}
    if v.get("quoted"):
        v["quoted"] = {quote(k): t for k, t in v["quoted"].items() if quote(k) is not None}
    return normalise(v)


def as_read(version: dict, read: dict) -> dict:
    """A board as a save would leave it against `read`, `read_cards`'s answer: its keys following
    their words, its picks' words read afresh. Nothing is written."""
    v = normalise(follow(version, read["cards"], read["quotes"]), quote_keys(read["quotes"]))
    texts = {q["key"]: q["text"] for r in read["quotes"].values() for q in r.get("quotes") or []}
    v["quoted"] = {k: texts[k] for chosen in v["picks"].values() for k in chosen if k in texts}
    return normalise(v)


def passage_moved(version: dict, sheet: str, row: int, old: list[str], new: list[str], lines: dict,
                  quote_lines: dict, now: dict, then: dict) -> tuple[dict, dict]:
    """One board, or a revision's state, moved with a passage's lines by a write: `lines` each old
    statement's new place or None (see `passage_lines`), `quote_lines` each old quote's place
    the same way, `now` and `then` `read_cards`'s answers before and after the write. The board is
    read as it reads now, its keys following their words, the cards of removed statements taken off
    (see `drop_cards`), every other card of the passage moved to its statement's new line, a card of
    a line reworded taking the new words when it held the old, and the board followed into `then`.

    Answers the board afterwards and what moved: `moved`, each card that changed key, `from`, `to`
    and its words, `removed`, each card taken off with its words, and `picks`, each pick moved or
    dropped, as `pick_moves` gives them. Nothing is written."""
    before = as_read(version, now)
    here = lambda k: split_card_key(k)[:2] == (sheet, row)
    grow = max(0, len(new) - len(old))
    cmap, gone = {}, []
    for k in before["cards"]:
        if not here(k):
            continue
        line = split_card_key(k)[2]
        if line < len(old):
            to = lines.get(line)
            if to is None:
                gone.append(k)
            elif to != line:
                cmap[k] = card_key(sheet, row, to)
        elif grow:
            # a card already missing past the passage's lines keeps clear of the lines the write adds
            cmap[k] = card_key(sheet, row, line + grow)
    qmap = {}
    for chosen in before["picks"].values():
        for k in chosen:
            if here(k):
                place = split_card_key(k)[2]
                to = quote_lines.get(place, place)
                if to != place:
                    qmap[k] = None if to is None else card_key(sheet, row, to)
    removed = [{"key": k, "text": before["cards"][k]["text"]} for k in sorted(gone, key=_order)]
    moved = [{"from": k, "to": cmap[k], "text": before["cards"][k]["text"]} for k in sorted(cmap, key=_order)
             if split_card_key(k)[2] < len(old)]
    v = keys_renamed(drop_cards(before, gone), cmap, qmap)
    reworded = []
    for i, j in sorted(lines.items()):
        if j is None or i >= len(old) or j >= len(new) or words(old[i]) == words(new[j]):
            continue
        c = v["cards"].get(card_key(sheet, row, j))
        if isinstance(c, dict) and words(c.get("text")) == words(old[i]):
            c["text"] = words(new[j])
            c.pop("live", None)
            reworded.append(card_key(sheet, row, j))
    moves: dict = {}
    after = normalise(follow(v, then["cards"], then["quotes"], moves), quote_keys(then["quotes"]))
    titles = {g["id"]: g["label"] for g in before["groups"]}
    picks = []
    for gid, chosen in before["picks"].items():
        for k in chosen:
            to = qmap.get(k, k)
            to = moves.get((gid, to), to) if to is not None else None
            if to is None or to not in (after["picks"].get(gid) or []):
                picks.append({"label": gid, "title": titles.get(gid, ""), "key": k, "to": None})
            elif to != k:
                picks.append({"label": gid, "title": titles.get(gid, ""), "key": k, "to": to})
    return after, {"moved": moved, "removed": removed, "picks": picks, "reworded": reworded}


@at_sheet_timepoint
def passage_written(workbook: Path, sheet: str, row: int, old: list[str], new: list[str], lines: dict,
                    quote_lines: dict, now: dict, then: dict, dry: bool = False, history: str = "",
                    changed: dict | None = None) -> list[dict]:
    """A write of one passage carried to every board of the case and every revision in their
    histories (see `passage_moved`), as a trim carries its rows (see `rekey`). Each board it changes
    keeps the board as it stood first in its History, under `history`, is stamped `updated`, and with
    `changed`, an agent's mark, is marked changed in a conversation, so an open PETs screen says so
    and its next save never puts the old keys back. With `dry` nothing is written.

    Answers each board it changes: its id and name, and the cards moved, the cards removed and the
    picks moved or dropped. A case with no themes file has none."""
    if not themes_path(workbook).exists():
        return []
    data = load(workbook)
    when = now_iso()
    out = []
    for board in boards_of(data):
        was = as_read(board, now)
        after, said = passage_moved(board, sheet, row, old, new, lines, quote_lines, now, then)
        # a card that takes longer words stands taller, and what it now meets makes way (31 October)
        settle_change(was, after)
        # the picks' words alone, a quote that gained inverted commas, are no change: the next save
        # reads them afresh
        plain = lambda v: {k: x for k, x in state_of(v).items() if k != "quoted"}
        if not (said["moved"] or said["removed"] or said["picks"] or said["reworded"]) and plain(after) == plain(was):
            continue
        out.append(dict(said, board=str(board.get("id")), name=str(board.get("name") or "")))
        if dry:
            continue
        for revision in board.get("history") or []:
            if isinstance(revision, dict) and isinstance(revision.get("state"), dict):
                revision["state"] = state_of(passage_moved(revision["state"], sheet, row, old, new, lines,
                                                           quote_lines, now, then)[0])
        add_revision(board, name=history, at=when)
        state = state_of(after)
        for key in STATE_OPTIONAL:
            board.pop(key, None)
        board.update({k: state[k] for k in STATE_KEYS if k in state}, updated=when)
        if changed:
            board["changed"] = dict(changed, at=when)
            board["changed"]["hash"] = state_hash(made_state(normalise(board)))
    if out and not dry:
        data["updated"] = when
        write(workbook, data)
    return out


# -------------------------------------------------------------- the boards

def _next_id(versions: list[dict]) -> str:
    # among a reviewer's own boards the next of his own (see `OWN_FILE`), which `write_own` gives one that has none
    if any(v.get(OWN) for v in versions):
        mine = [str(v.get("id") or "")[len(OWN_ID):] for v in versions if v.get(OWN)]
        return f"{OWN_ID}{max([int(x) for x in mine if x.isdigit()] + [0]) + 1}"
    n = 0
    for v in versions:
        digits = str(v.get("id") or "")[1:]
        if str(v.get("id") or "").startswith("v") and digits.isdigit():
            n = max(n, int(digits))
    return f"v{max(n, len(versions)) + 1}"


def _free_name(versions: list[dict], wanted: str) -> str:
    taken = {str(v.get("name") or "").strip().lower() for v in versions}
    if wanted.strip().lower() not in taken:
        return wanted
    n = 2
    while f"{wanted} {n}".lower() in taken:
        n += 1
    return f"{wanted} {n}"


def board_name(versions: list[dict], wanted: str = "") -> str:
    """A new board's name: the one he typed, kept clear of every other, or `Board N`, the next free
    number past the boards there are. An agent's board is named as his own are, and the board menu
    says after its name that an agent made it (see `made_said`)."""
    if wanted.strip():
        return _free_name(versions, wanted.strip())
    taken = {str(v.get("name") or "").strip().lower() for v in versions}
    n = len(versions) + 1
    while f"{BOARD} {n}".lower() in taken:
        n += 1
    return f"{BOARD} {n}"


def proposal_name(versions: list[dict]) -> str:
    """The name a board laid out whole takes, `Board N`, as every new board's is. A name from before,
    `AI board 3`, stays as it is."""
    return board_name(versions)


def version_op(workbook: Path, op: str, body: dict, case: str, dry_run: bool = False) -> dict:
    """One change to the boards in the file, and the screen's state afterwards. The ops keep the
    names they had when the boards were versions, and so does the route that carries them.

    `new` adds an empty board, every card waiting in the sidebar, or with `start` of `canvas` every
    card on the canvas as a pile in the middle (see `blank_version`), and makes it current. `duplicate`
    copies a board, the current one unless `id` names another, under a new name, its sticky notes
    with it, with its own empty note and no history, and makes the copy current. `rename` and `note` change one board's
    name or note. `switch` makes another board current and changes nothing else. `delete` takes one
    out, and is refused on the last: the board beside it becomes current when it was, and a board
    marked as the Current board takes the mark with it, unless one board is left, which takes the
    mark. A file that has only ever had one board marks nothing by itself. `choose` marks the board `id` names as the
    Current board, `chosen` at the top of the file, and `id` of None clears the mark. It never
    touches `current`, and a duplicate never carries the mark. Every op but `new` names a board the
    file holds, or is refused. A case with no file yet is given its first
    board before the op, the one an open offers.

    `complete` marks the PETs phase complete on the Current board, `complete` at the top of the
    file with the time, the board's id and its name, and is refused while no board is marked
    current. `reopen` takes the mark off. Neither names a board. Marking PETs already marked keeps
    the first time, and reopening with no mark writes nothing. Unmarking or deleting the board the
    mark names leaves the mark as it stands.

    `propose` is a board laid out whole: `version` laid out by the server, added at the end under the
    next `Board N` name, as New board names one, or under `name` kept clear of every other (a REFI-QDA
    import's "From ATLAS.ti", see `server.qdpx_board`), with `note`, with no sticky notes, and made
    current, its `made` taking the hash of the board as made. The board it was made from is left as
    it was, as every other board is. A board an AI agent made through the command line comes this
    way, with `made` saying so, and with `seed` false, so on a case with no file yet it is the
    file's first board, Board 1, with no empty board written before it, as its dry run names it. A
    duplicate never carries `made` or `changed`. With `dry_run` (26 October) every check is made and
    nothing is written.
    """
    workbook = Path(workbook)
    if op not in OPS and op != PROPOSE:
        raise WorkbookError(i18n.t("server.something_board_can_do_nothing"), code="unknown_op")
    body = body if isinstance(body, dict) else {}
    read = read_cards(workbook)
    data = load(workbook) or {}
    versions = boards_of(data)
    # a case with no file yet is given the board an open offers first, unless the board proposed is
    # to be its first
    if not versions and not (op == PROPOSE and body.get("seed") is False):
        versions = [blank_version(read["cards"])]
    ids = [str(v.get("id")) for v in versions]
    current = str(data.get("current")) if str(data.get("current")) in ids else (ids[0] if ids else "")
    vid = str(body.get("id") or current)
    target = next((v for v in versions if str(v.get("id")) == vid), None)
    # `choose` with no board named clears the mark, and so needs no board
    clearing = op == "choose" and body.get("id") in (None, "")
    if target is None and op not in ("new", PROPOSE, "complete", "reopen") and not clearing:
        raise WorkbookError(i18n.t("server.board_gone_themes_changed"))
    when = now_iso()

    # the PETs phase, the case's and no one board's: marked on the Current board, or the mark taken
    # off, and a mark already there, or none to take off, writes nothing
    if op in ("complete", "reopen"):
        held = complete_of(data)
        if op == "complete" and not held:
            chosen = chosen_of(dict(data, boards=versions))
            if not chosen:
                raise WorkbookError(i18n.t("server.board_marked_current_pets_were"))
            board = find_version({"boards": versions}, chosen)
            data["complete"] = {"at": when, "board": chosen, "name": str(board.get("name") or FIRST_NAME)}
        elif op == "reopen" and "complete" in data:
            data.pop("complete")
        else:
            return dict(state(workbook, case, read), op=op)

    if op == PROPOSE:
        made = normalise(body.get("version") if isinstance(body.get("version"), dict) else {})
        # a board laid out whole starts with no sticky notes, which are his alone
        made.pop("notes", None)
        made.update(id=_next_id(versions), name=board_name(versions, str(body.get("name") or "")),
                    note=str(body.get("note") or "").strip(), created=when, updated=when)
        # who made it, and the hash of the board as it was made, which his first change is told by
        if made.get("made"):
            made["made"] = stamp_made(made["made"], made)
        versions.append(made)
        current = made["id"]
    elif op == "new":
        start = "canvas" if str(body.get("start") or "") == "canvas" else "empty"
        fresh = blank_version(read["cards"], when, start)
        fresh["id"] = _next_id(versions)
        fresh["name"] = board_name(versions, str(body.get("name") or ""))
        versions.append(fresh)
        current = fresh["id"]
    elif op == "duplicate":
        copy = json.loads(json.dumps(normalise(target)))
        # a copy is his, made by his press, whatever an agent did to the board it was copied from, and
        # carries nothing the app's own AI left with the board before 11 November 2026
        for key in FROM_BEFORE:
            copy.pop(key, None)
        # and a copy of a board brought in from a shared copy is his, not the other analyst's
        copy.pop(ORIGIN, None)
        for key in AGENT_KEYS:
            copy.pop(key, None)
        name = str(body.get("name") or "").strip()
        # its own note, empty from the board menu, and from the command line the words that say who
        # made the copy for which request
        copy.update(id=_next_id(versions), name=_free_name(versions, name or f"{copy['name']} copy"),
                    note=str(body.get("note") or "").strip(), created=when, updated=when)
        versions.insert(versions.index(target) + 1, copy)
        current = copy["id"]
    elif op == "rename":
        name = " ".join(str(body.get("name") or "").split())
        if not name:
            raise WorkbookError(i18n.t("server.board_needs_name_nothing_changed"))
        if any(str(v.get("name") or "").strip().lower() == name.lower() and v is not target for v in versions):
            raise WorkbookError(i18n.t("server.another_board_called_already_nothing", name=name))
        target.update(name=name, updated=when)
    elif op == "note":
        target.update(note=str(body.get("note") or "").strip(), updated=when)
    elif op == "switch":
        current = vid
    elif op == "choose":
        # the Current board, the one he is going with, beside `current` and never in its place
        if clearing:
            data.pop("chosen", None)
        else:
            data["chosen"] = vid
    elif op == "delete":
        if len(versions) == 1:
            raise WorkbookError(i18n.t("server.last_board_cannot_deleted_nothing"))
        at = versions.index(target)
        versions.remove(target)
        if current == vid:
            current = str(versions[max(0, at - 1)].get("id"))
        if str(data.get("chosen")) == vid:
            data.pop("chosen", None)
            # the Current board deleted with one board left marks that one, the only one to go with
            if len(versions) == 1:
                data["chosen"] = str(versions[0].get("id"))

    if dry_run:
        return {"op": op, "dry_run": True, "current": current}
    write(workbook, _file(workbook, case, data, versions, current, when))
    return dict(state(workbook, case, read), op=op)


# ------------------------------------------------------------- the exports

# a board's name goes into a file name, so the characters a file name cannot carry go
UNSAFE = str.maketrans({c: "-" for c in '/\\:*?"<>|'})


def draft_stem(workbook: Path) -> str:
    """The stem the statements CSV uses: the workbook's, less its ` - EN & ES`."""
    return Path(workbook).stem.replace(" - EN & ES", "").strip()


def draft_path(workbook: Path, name: str) -> Path:
    safe = " ".join(str(name or FIRST_NAME).translate(UNSAFE).split()) or FIRST_NAME
    return Path(workbook).parent / "Working" / f"{draft_stem(workbook)} - PET draft ({safe}).md"


def pick_version(data: dict | None, vid=None) -> dict | None:
    """The board named, or the current one when none is. None when the file has no such board."""
    if vid:
        return find_version(data, vid)
    return current_version(data)


def parents_of(groups: list[dict]) -> dict[str, str]:
    return {m: g["id"] for g in groups for m in g["members"]}


def label_paths(version: dict) -> dict[str, str]:
    """What the Proposed PET column carries for each card: the labels over it, top-most first and
    joined with ` / `, `Binned` for a binned card, "Stacked under: <its top's words>" for a
    stacked one, and nothing for a card in no group."""
    version = normalise(version)
    by_id = {g["id"]: g for g in version["groups"]}
    parents = parents_of(version["groups"])
    out = {}
    for key in version["cards"]:
        chain, at = [], parents.get(key)
        while at is not None and at not in chain:
            chain.append(at)
            at = parents.get(at)
        if chain:
            out[key] = " / ".join(by_id[g]["label"] for g in reversed(chain))
    for key in version["discarded"]:
        out[key] = DISCARDED
    # a stacked statement names the statement it is stacked under, which stands for it
    for top, keys in (version.get("stacks") or {}).items():
        for key in keys:
            out[key] = i18n.t("exports.stacked_under_words", words=(version["cards"].get(top) or {}).get("text") or top)
    return out


def pet_column(themes_file: Path, vid=None, read: dict | None = None) -> dict[str, str]:
    """The Proposed PET column for the statements CSV, from a themes file and a board in it.

    No file is no column. A file that cannot be read is refused, and so is a board it lacks.
    """
    return pet_table(themes_file, vid, read)[0]


def pet_table(themes_file: Path, vid=None, read: dict | None = None) -> tuple[dict[str, str], list[str]]:
    """The Proposed PET column and the order the CSV lists the placed statements in, theme by theme
    in canvas order and each theme's as the canvas reads them. No file is no column and no order.
    With `read`, the workbook as `read_cards` reads it, the board's keys follow their words first,
    so a line inserted above a statement since the board was saved never moves its label."""
    themes_file = Path(themes_file)
    if not themes_file.exists():
        return {}, []
    try:
        data = json.loads(themes_file.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        raise WorkbookError(i18n.t("server.could_read_nothing_exported", name=themes_file.name))
    version = pick_version(migrate(data) if isinstance(data, dict) else None, vid)
    if version is None:
        if vid:
            raise WorkbookError(i18n.t("server.board_gone_themes_exported"))
        return {}, []
    if read is not None:
        version = follow(version, read["cards"], read["quotes"])
    return label_paths(version), placed_order(version)


def read_order(spots: dict, band: float = ROW_BAND) -> list:
    """Ids in the order the canvas reads them: top to bottom, and left to right along a row. `spots`
    gives each id its (x, y), and ids whose tops sit within `band` of the first in a row share it."""
    rest = sorted(spots, key=lambda i: (spots[i][1], spots[i][0]))
    out = []
    while rest:
        top = spots[rest[0]][1]
        row = [i for i in rest if spots[i][1] - top < band]
        out.extend(sorted(row, key=lambda i: (spots[i][0], spots[i][1])))
        rest = [i for i in rest if i not in row]
    return out


def canvas_order(ids: list[str], by_id: dict) -> list[str]:
    """Labels in the order the canvas reads: top to bottom, and left to right along a row. Labels
    whose tops sit within a card's height of the first in a row count as one row."""
    return read_order({g: (by_id[g]["x"], by_id[g]["y"]) for g in ids}, CARD_H)


def theme_order(version: dict, gid: str, drawn: dict | None = None) -> list[str]:
    """A theme's own members as the canvas reads them, top to bottom and left to right along a row,
    which is the order of how well each carries the theme: a card by its top-left corner and a
    sub-theme by its frame's, so a sub-theme takes its place among the cards where its frame's top
    sits. `version` is normalised, and `drawn` its layout when it is to hand."""
    drawn = drawn or layout_boxes(version)
    by_id = {g["id"]: g for g in version["groups"]}
    cards = version["cards"]
    spots = {}
    for m in by_id[gid]["members"] if gid in by_id else []:
        if m in by_id:
            frame = drawn["frames"].get(m)
            spots[m] = (frame[0], frame[1]) if frame else (by_id[m]["x"], by_id[m]["y"])
        elif m in cards:
            spots[m] = (cards[m]["x"], cards[m]["y"])
    return read_order(spots)


def placed_order(version: dict) -> list[str]:
    """Every statement placed in a theme, theme by theme in canvas order, and inside each theme as
    the canvas reads it, a sub-theme's statements at the place its frame's top sits, and the
    statements stacked under a top straight after it."""
    version = normalise(version)
    drawn = layout_boxes(version)
    by_id = {g["id"]: g for g in version["groups"]}
    parents = parents_of(version["groups"])
    out: list[str] = []

    def walk(gid: str, seen: frozenset) -> None:
        for m in theme_order(version, gid, drawn):
            if m in by_id:
                if m not in seen:
                    walk(m, seen | {m})
            elif m not in out:
                out.append(m)
                # the statements stacked under it come straight after it
                out.extend((version.get("stacks") or {}).get(m) or [])

    for gid in canvas_order([g["id"] for g in version["groups"] if g["id"] not in parents], by_id):
        walk(gid, frozenset({gid}))
    return out


def quoted(text: str) -> str:
    """A quote in inverted commas, once: one written by `q` carries them already."""
    text = str(text).strip()
    if len(text) >= 2 and text[0] in "\"\u201c" and text[-1] in "\"\u201d":
        return text
    return f'"{text}"'


# the marks a workbook may keep round a quote, double or single, taken off before a page's own
MARKS = ("\"\u201c\u201d", "'\u2018\u2019")


def bare(quote: str) -> str:
    """A quote's words without the quotation marks the workbook sometimes keeps round them, double
    or single, so they are never doubled. The print view, the Word document, the PET draft and the
    statements CSV all take a statement's own quote this way."""
    text = str(quote or "").strip()
    while len(text) >= 2 and any(text[0] in marks and text[-1] in marks for marks in MARKS):
        text = text[1:-1].strip()
    return text


def sub_letter(n: int) -> str:
    """The letter for a count, a for the first, z for the twenty-sixth, then aa: a sub-theme's
    after its PET's number, and in capitals a PET's own letter, A to Z and then AA."""
    out = ""
    while n > 0:
        n, r = divmod(n - 1, 26)
        out = chr(97 + r) + out
    return out


# The two ways a project labels its PETs, `pet_labels` in its project file. Letters are the book's,
# Smith, Flowers and Larkin's Box 5.6, and the default whenever the file says nothing else
LETTERS, NUMBERS = "letters", "numbers"
PET_LABELS = (LETTERS, NUMBERS)


def pet_labels_of(value) -> str:
    """A project's way of labelling its PETs from its file's `pet_labels`: "numbers" when it says
    so, else "letters", the book's way, for a missing key or anything else."""
    return NUMBERS if value == NUMBERS else LETTERS


def pet_numbers(themes: list[dict], labels: str = LETTERS) -> dict[str, str]:
    """The label each theme of an outline carries, by its id, each layer counted in the order the
    canvas reads it. With letters, the book's way and the default, "A" for the first PET, "Z" for
    the twenty-sixth and then "AA", "A1" for its first sub-theme, "A1.1" for that sub-theme's first
    group and "A1.1.1" for a group inside that group, and on the same way at any depth. With
    numbers, "PET 1", "PET 1a" for its first sub-theme, "1a.1" for that sub-theme's first group and
    "1a.1.1" for one inside that. The Word document, the print view and the PET draft all take
    their labels from here, so the three never disagree."""
    letters = pet_labels_of(labels) == LETTERS
    out: dict[str, str] = {}

    def walk(items: list[dict], stem: str, depth: int) -> None:
        for i, t in enumerate(items, 1):
            if letters:
                mark = inner = (sub_letter(i).upper() if depth == 0 else f"{stem}{i}" if depth == 1
                                else f"{stem}.{i}")
            elif depth == 0:
                mark, inner = f"PET {i}", str(i)
            elif depth == 1:
                inner = f"{stem}{sub_letter(i)}"
                mark = f"PET {inner}"
            else:
                mark = inner = f"{stem}.{i}"
            out[t["id"]] = mark
            walk(t.get("themes") or [], inner, depth + 1)

    walk(themes, "", 0)
    return out


def numbered(number: str, title: str) -> str:
    """A label's heading, its label and its title, a full stop after a PET's label and a
    sub-theme's, "A. Home life" and "A1. Mornings", or "PET 1. Home life" and "PET 1a. Mornings",
    and none after a group's, whose label carries a full stop already, "A1.1 Early light" or "1a.1
    Early light"."""
    return f"{number} {title}" if "." in str(number) else f"{number}. {title}"


def in_order(theme: dict) -> list[tuple[str, dict]]:
    """A theme of an outline as a page sets it out under its heading: its statements and its
    sub-themes or groups in the order the canvas reads them, each as `("statement", s)` or
    `("theme", sub)`. Its `order` places a label inside it among the cards where its frame's top
    sits, and anything the order leaves out follows it. The print view and the Word document both
    read a theme this way."""
    own = {s["key"]: s for s in theme.get("statements") or []}
    subs = {t["id"]: t for t in theme.get("themes") or []}
    order = [m for m in theme.get("order") or [] if m in own or m in subs]
    order += [m for m in [*own, *subs] if m not in order]
    return [("theme", subs[m]) if m in subs else ("statement", own[m]) for m in order]


def counted(title: str, n: int) -> str:
    """A heading with how many it holds, "Not placed (18)" and "Experiential statements set aside (3)", as the Word
    document, the print view and the PET draft head their lists at the end."""
    return i18n.t("exports.counted", title=title, n=n)


def where_said(item: dict) -> str:
    """Where a statement or a quote sits, "Initial, 18:52", the sheet and the timecode, and so for a
    line that has gone from the workbook."""
    where = ", ".join(p for p in (item.get("sheet"), item.get("time")) if p)
    if item.get("missing"):
        where = i18n.t("exports.where_gone", where=where) if where else i18n.t("exports.gone")
    return where


def said_line(s: dict) -> list[str]:
    """A statement as the PET draft lists it, the lines of one list item: its words and where it is,
    "- Statement (Initial, 12:04)", and when it has a quote of its own, the quote on the next line in
    single curly quotation marks, set in under the item and joined to it by a line break, never
    doubled when the workbook keeps marks round it, as the print view and the Word document set it."""
    out = [f"- {s['text']} ({where_said(s)})"]
    said = bare(s.get("quote"))
    if said:
        out = [out[0] + "\\", f"  \u2018{said}\u2019"]
    # the statements stacked under it, when the export asks for them, a list a step in under a line
    # of their own, "Stacked under it (3)", each with its reference and no quote
    if s.get("stacked"):
        out.append("  - " + counted(i18n.t("exports.stacked_under_it"), len(s["stacked"])))
        out.extend(f"    - {x['text']} ({where_said(x)})" for x in s["stacked"])
    return out


def draft_markdown(workbook: Path, case: str, vid=None, labels: str = LETTERS,
                   stacked: bool = False) -> tuple[str, dict]:
    """A board as a PET grouping draft in markdown, and the board it was made from.

    Its labels are the ones the print view and the Word document give, from `pet_numbers` with the
    project's `labels`, the book's letters unless it says numbers, in the same order, so the three
    never disagree. A title line, the case by its pseudonym and the board's name, then a list of
    every PET, its sub-themes and their groups in canvas order, "A. Home life (1 sub-theme · 7
    statements)", a sub-theme one step in, "A1. Mornings (1 group · 3 statements)", and a group one
    step further, "A1.1 Early light (2 statements)", a group inside a group a step further again.
    Then each PET under its label and title as a heading, "## A. Home life", its sub-themes as
    headings a level down, "### A1. Mornings", their groups a level further, "#### A1.1 Early
    light", and a group inside a group at "#####", where anything deeper
    stays, as the Word document's headings stop at Heading 5. Under a heading
    come its note as a plain paragraph when it has one, then its statements and the labels inside it
    as `in_order` reads them, the order the print view and the Word document take, a label taking its
    place among the cards where its frame's top sits. Each statement is a list item, its words and
    its reference, "(Initial, 12:04)", and its own quote on the next line in single curly
    quotation marks (see `said_line`), a statement with no quote of its own having no quote line.
    No picked quotes are listed, since every statement carries its own. Not placed and Discarded
    come at the end with their counts, "Not placed (18)", only when they hold anything, in
    transcript order, their statements set out the same way. The board's note stays out. The
    statements are read from the workbook as it reads now, through the outline the print view uses.
    A case with no file yet exports the board an open offers, everything not placed. A top stands
    for the statements stacked under it, which come under it only with `stacked`, the tick Include
    stacked statements.
    """
    workbook = Path(workbook)
    read = read_cards(workbook)
    data = load(workbook)
    version = pick_version(data, vid)
    if version is None:
        if vid and data:
            raise WorkbookError(i18n.t("server.board_gone_themes_exported"))
        version = blank_version(read["cards"])
    # the keys follow their words first, so the order the canvas reads names the keys the cards have
    version = follow(version, read["cards"], read["quotes"])
    board = stacks_shown(outline(read, version), stacked)
    numbers = pet_numbers(board["themes"], labels)
    # each label under its letter or number, as the print view and the Word document have them
    titled = lambda t: numbered(numbers[t["id"]], t["label"])
    out = [f"# {case}: PET grouping draft ({version['name']})", ""]

    def listed(items: list[dict], depth: int) -> None:
        for t in items:
            out.append(f"{'  ' * depth}- {titled(t)} ({t['count']})")
            listed(t["themes"], depth + 1)

    listed(board["themes"], 0)
    if board["themes"]:
        out.append("")

    def theme(t: dict, depth: int) -> None:
        # a heading a level down for each layer, stopping at the fifth as the Word document does
        out.extend([f"{'#' * min(5, depth + 1)} {titled(t)}", ""])
        if t.get("note"):
            out.extend([t["note"], ""])
        # its statements and the labels inside it as the print view and the Word document read them,
        # a run of statements one list
        run: list[str] = []
        for kind, item in in_order(t):
            if kind == "statement":
                run.extend(said_line(item))
                continue
            if run:
                out.extend(run + [""])
                run = []
            theme(item, depth + 1)
        if run:
            out.extend(run + [""])

    for t in board["themes"]:
        theme(t, 1)
    for title, items in ((i18n.t("exports.not_placed"), board["unplaced"]), (i18n.t("exports.set_aside_heading"), board["discarded"])):
        if items:
            out.extend([f"## {counted(title, len(items))}", ""] + [x for s in items for x in said_line(s)] + [""])
    return "\n".join(out).rstrip("\n") + "\n", version


def outline(read: dict, version: dict) -> dict:
    """A board as a document sets it out, for the titles' prompt and the print view.

    Its themes in canvas order, each with its own statements in the order the canvas reads them,
    higher first, the quotes picked to carry it in transcript order, its `note` and its `description`
    when it has them, and its sub-themes, at any depth, in the order their frames read among its cards. A theme's `order`
    gives its statements' keys and its sub-themes' ids in one list as the canvas reads them, so a
    sub-theme takes its place among the cards where its frame's top sits. Then the statements left
    unplaced and those discarded, both in transcript order, each with the reason it was left out when
    an agent gave one, or an AI proposal before. Each statement carries its key, sheet, timecode and words as
    the workbook reads now, whether its line has gone, and `quote`, its own quote, the one at
    its place among its row's quotes, empty when it has none or its line has gone. A top carries
    `stacked`, the statements stacked under it set out the same way, which are listed nowhere else. `read` is
    what `read_cards` gives, and nothing is written.
    """
    # the keys follow their words first, so the order the canvas reads names the keys the cards have
    version = follow(version, read["cards"], read["quotes"])
    drawn = layout_boxes(version)
    merged = merge(read["cards"], version, read["quotes"])
    cards = {c["key"]: c for c in merged["cards"]}
    sheets = {name: i for i, name in enumerate(read["sheets"])}
    order = lambda key: (sheets.get(cards[key]["sheet"], len(sheets)), cards[key]["row"] or 0,
                         cards[key]["line"] or 0)
    groups = merged["groups"]
    by_id = {g["id"]: g for g in groups}
    parents = parents_of(groups)
    quotes = {q["key"]: (row, q["text"]) for row in read["quotes"].values() for q in row["quotes"]}
    # a quote that takes in the passages next to its own is placed by its range (see `spread_quotes`)
    spans = {q["key"]: q["time"] for row in read["quotes"].values() for q in row["quotes"] if q.get("span")}
    stacks = merged.get("stacks") or {}
    stacked = stacked_keys(merged)
    reasons = merged.get("discard_reasons") or {}

    def statement(key: str, top: bool = True) -> dict:
        c = cards[key]
        gone = bool(c.get("missing"))
        out = {"key": key, "sheet": c["sheet"], "time": c.get("time") or "", "text": c["text"],
               "missing": gone, "quote": "" if gone or key not in quotes else quotes[key][1]}
        # the statements stacked under a top go with it, in their order, which an export shows only
        # when its tick asks for them
        if top and stacks.get(key):
            out["stacked"] = [statement(k, False) for k in stacks[key] if k in cards]
        return out

    def theme(gid: str, seen: frozenset) -> dict:
        items = [m for m in theme_order(version, gid, drawn) if m in cards or m in by_id]
        chosen = sorted((k for k in merged["picks"].get(gid, []) if k in quotes),
                        key=lambda k: (sheets.get(quotes[k][0]["sheet"], len(sheets)), quotes[k][0]["row"],
                                       split_card_key(k)[2]))
        subs = [theme(m, seen | {m}) for m in items if m in by_id and m not in seen]
        own = [statement(k) for k in items if k in cards and k not in by_id]
        under = len(own) + sum(s["under"] for s in subs)
        order = [m for m in items if (m in by_id and m not in seen) or (m in cards and m not in by_id)]
        out = {"id": gid, "label": by_id[gid]["label"], "statements": own, "order": order,
               "picks": [{"key": k, "text": quotes[k][1], "sheet": quotes[k][0]["sheet"],
                          "time": spans.get(k) or quotes[k][0].get("time") or ""} for k in chosen],
               "themes": subs, "under": under, "count": count_text(under, len(subs), len(seen) - 1)}
        if by_id[gid].get("note"):
            out["note"] = by_id[gid]["note"]
        if description_of(by_id[gid]):
            out[DESCRIPTION] = description_of(by_id[gid])
        return out

    gone = set(merged["discarded"])
    return {"name": version["name"], "note": version["note"], "sheets": list(read["sheets"]),
            "themes": [theme(g, frozenset({g}))
                       for g in canvas_order([g["id"] for g in groups if g["id"] not in parents], by_id)],
            "unplaced": [dict(statement(k), **({"reason": reasons[k]} if reasons.get(k) else {}))
                         for k in sorted((k for k in cards if k not in parents and k not in gone and k not in stacked),
                                         key=order)],
            "discarded": [dict(statement(k), reason=reasons.get(k, ""))
                          for k in sorted((k for k in gone if k in cards), key=order)]}


# the words an export heads a top's stack with, "Stacked under it (3)", where the tick asks for them,
# and the CSV's Proposed PET column for a stacked statement, "Stacked under: <its top's words>"


def stacks_shown(board: dict, stacked: bool) -> dict:
    """An outline (see `outline`) as an export sets it out: with `stacked` each top keeps the
    statements stacked under it, and without, the tick off as on a new install, the top stands for
    them alone and they are left out. Nothing is written."""
    if stacked:
        return board

    def plain(s: dict) -> dict:
        return {k: v for k, v in s.items() if k != "stacked"}

    def theme(t: dict) -> dict:
        return dict(t, statements=[plain(s) for s in t.get("statements") or []],
                    themes=[theme(x) for x in t.get("themes") or []])

    return dict(board, themes=[theme(t) for t in board.get("themes") or []],
                unplaced=[plain(s) for s in board.get("unplaced") or []],
                discarded=[plain(s) for s in board.get("discarded") or []])


def descriptions_shown(board: dict, shown: bool) -> dict:
    """An outline (see `outline`) as an export sets it out: with `shown`, the Descriptions tick on as on
    a new install, each label keeps its description under its title, and without it the titles stand
    alone, as before descriptions were (Adam, 21 October). Nothing is written."""
    if shown:
        return board

    def theme(t: dict) -> dict:
        return dict({k: v for k, v in t.items() if k != DESCRIPTION}, themes=[theme(x) for x in t.get("themes") or []])

    return dict(board, themes=[theme(t) for t in board.get("themes") or []])


def write_draft(workbook: Path, case: str, vid=None, labels: str = LETTERS, stacked: bool = False) -> dict:
    """Write the PET draft of a board into the case's `Working/` folder, its PETs labelled the
    project's way, `labels`, the statements stacked under a top beneath it only with `stacked`. The
    workbook is only read."""
    text, version = draft_markdown(workbook, case, vid, labels, stacked)
    path = draft_path(workbook, version["name"])
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + ".tmp")
    tmp.write_text(text, encoding="utf-8", newline="\n")
    os.replace(tmp, path)
    return {"path": str(path), "version": summary(version)}


def __getattr__(name: str) -> str:
    """The refusals other modules and the checks name as this module's, each read in the run's language when
    asked for (the text layer, 28 October 2026)."""
    said = {
        "BINNED_HEADING": lambda: i18n.t("exports.set_aside_heading"),
        "NOT_PLACED": lambda: i18n.t("exports.not_placed"),
        "STACKED_HEAD": lambda: i18n.t("exports.stacked_under_it"),
        "STACKED_UNDER": lambda: i18n.t("exports.stacked_under"),
        "STALE_PAGE": lambda: i18n.t("server.board_changed_since_page_loaded"),
        "NOT_A_BOARD_OP": lambda: i18n.t("server.something_board_can_do_nothing"),
        "LOST": lambda: i18n.t("server.revision_longer_board_s_history"),
        "OUTSIDE": lambda: i18n.t("server.board_changed_conversation_canvas_saved"),
        "GONE": lambda: i18n.t("server.board_longer_themes_file_nothing"),
        "NO_CURRENT": lambda: i18n.t("server.board_marked_current_pets_were"),
    }
    if name in said:
        return said[name]()
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
