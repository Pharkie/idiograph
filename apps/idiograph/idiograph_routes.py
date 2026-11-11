"""Idiograph's routes on the family's server (22 October 2026, the family codebase's fourth build, from
server.py): a project's participants and their workbooks, the statements screen, the PETs and GETs boards
and the Trajectories board, the timepoints, new projects, REFI-QDA, sending a project and opening a sent
one, renaming a participant, the exports and the print views, the recording, the demo, the examples, the
nudges and the AI's suggestions, each registered with the server by `register` at the foot of this file,
which the server's start imports this module for (`boot.load`). With them its settings and their defaults,
the research question an AI route asks, the timepoint a board's request runs at, its two scopes of Search,
its start, which fills the demo, and its paths outside /api/, the recording, the print views and Send.

One command, a tab opens at localhost, one participant turn at a time. The workbook stays the source of truth
and Excel can open it again at any point. Nothing leaves the machine but a turn sent to an AI model he chose
and a note he sends from Send feedback.

The server's names are read from it as each request comes, `srv.config()`, `srv.ROOT_OVERRIDE` and the rest,
so a check that stands in a dialog, a folder or a platform of its own is heard here too.
"""
from __future__ import annotations

import atexit
import base64
import binascii
import contextlib
import contextvars
import json
import os
import re
import shutil
import subprocess
import tempfile
import threading
import time
from datetime import datetime
from pathlib import Path, PurePosixPath
from urllib.parse import quote, urlencode

import openpyxl

import ai_suggest as ai_mod
import app_search
import audio as audio_mod
import boot
import canvas_out
import case_files
import codes as codes_mod
import convert as convert_mod
import corpus
import export as export_mod
import formats
import i18n
import gets as gets_mod
import gets_print
import gets_word
import idiograph_find
import locks
import names as names_mod
import nudges as nudges_mod
import print_pdf
import project_history as hist_mod
import participants as people_mod
import project_pack as pack_mod
import qdpx as qdpx_mod
import rounds as rounds_mod
import server as srv
import statement_prompts as prompts
import ta_ai
import team_board
import team_sync
import themes as themes_mod
import themes_ai
import themes_print
import themes_word
import trajectories as traj_mod
import trash as trash_mod
import workbook as wb_mod
from workbook import WorkbookError

# Working together's one writer per participant and per GETs board (wtowners, 8 November 2026), refused where the
# case's lock and the GETs file's write are, for the app and the command line alike (team_sync.guard)
team_sync.install_guards()
# and a reviewer's own boards of a participant someone else works on, kept apart in his copy (ownboards, 9 November
# 2026, team_board.own_file)
team_board.install()

# the lines of the Themes screen's Guidance tab, read afresh on every open of that screen
THEMES_GUIDANCE = boot.resource("themes_guidance.md")
# a thematic analysis project's own (tarail, 3 November 2026, Adam's "ta guidance reviewed and approved"): the Coding
# screen's rail, in the shape of guidance.md, and the Themes board's Guidance tab, in the shape of themes_guidance.md,
# both from Braun and Clarke's reflexive thematic analysis
TA_GUIDANCE = boot.resource("ta_guidance.md")
TA_THEMES_GUIDANCE = boot.resource("ta_themes_guidance.md")
SKIP_DIRS = {"Source", "_Archive", "Working", "_Process reports", "Photos"}

# The app's own backups and the coordinator's copies: a stem ending in a parenthesised note that
# starts `pre-` or `complete`, such as `(pre-trim)` or `(complete 30Sep26)`. They are never offered.
BACKUP_STEM = re.compile(r"\((?:pre-|complete)[^()]*\)\s*$", re.IGNORECASE)
DEMO_SHEET = "Initial"
DEMO_TITLE = "Juno, living with a dog"
# The demo's three cases, Juno first, each a folder of its name holding `<name> - EN & ES.xlsx`:
# Juno's to work on, with its recording, and Rowan's and Mabel's annotated, their PETs on a marked
# board, for the step across cases. Every one of them is a demo case, and the three make one
# project, Living with a dog, whose file is DEMO_PROJECT below.
DEMO_CASES = ("Juno", "Rowan", "Mabel")
DEMO_TOPIC = "living with a dog"

# the statements screen's three columns by name, in the book's order (Smith, Flowers and Larkin 2022,
# Box 5.4), its order on a new install
COLUMNS = ("statements", "transcript", "notes")
# the three places the exploratory notes could stand until 17 October, `notes_place`, each read as the
# order nearest the screen it drew: the notes right or left of the transcript with the statements' panel
# at the right, or under the statements in that panel
NOTES_PLACES = ("right", "left", "under")
NOTES_PLACE_COLUMNS = {
    "right": ("transcript", "notes", "statements"),
    "left": ("notes", "transcript", "statements"),
    "under": ("transcript", "statements", "notes"),
}


def statements_columns(value, notes_place=None) -> list[str] | None:
    """The three columns' order as config.json holds it, each name once. A value that is not the three
    names reads as the order nearest an old `notes_place`, and as the book's when that is no place, and
    is None when no `notes_place` is given at all, so a save sent anything else leaves the file as it was."""
    if isinstance(value, (list, tuple)) and len(value) == len(COLUMNS) \
            and all(isinstance(v, str) for v in value) and sorted(value) == sorted(COLUMNS):
        return list(value)
    if notes_place is None:
        return None
    return list(NOTES_PLACE_COLUMNS.get(notes_place, COLUMNS))


# the columns that can be hidden, the transcript always shown (18 October)
HIDEABLE_COLUMNS = ("statements", "notes")
# the divider between the statements and the notes stacked, the statements' share of the column, at half
# on a new install and never so far that a half is too short to hold a line
STACK_SPLIT = 0.5
STACK_SPLIT_RANGE = (0.2, 0.8)


def stack_top(value) -> str | None:
    """The column above in the stacked column (21 October), the statements or the notes. None for
    anything else, so a save sent it leaves the file as it was and a file holding it reads as the
    statements above."""
    return value if value in HIDEABLE_COLUMNS else None


def columns_hidden(value) -> list[str] | None:
    """The columns hidden as config.json holds them, the statements, the notes or both, each once and in
    the book's order, never the transcript. None for anything else, so a save sent it leaves the file as
    it was and a file holding it reads as none hidden."""
    if not isinstance(value, (list, tuple)) or not all(isinstance(v, str) for v in value) \
            or not set(value) <= set(HIDEABLE_COLUMNS):
        return None
    return [c for c in HIDEABLE_COLUMNS if c in value]


# the parts of a screen's widths, each a whole number of pixels, and how many screens are kept, the
# ones last set kept when a new one would pass it
COLUMN_WIDTH_KEYS = ("left", "right", "statements", "notes", "stack")
COLUMN_WIDTH_MOST = 20000
COLUMN_SCREENS_KEPT = 12


def column_screen(value) -> str | None:
    """A screen's key as `column_widths` holds it, its width in whole pixels as text, or None."""
    text = str(value).strip() if isinstance(value, (str, int)) and not isinstance(value, bool) else ""
    return text if text.isdigit() and 0 < int(text) <= COLUMN_WIDTH_MOST and len(text) <= 5 else None


def column_width_set(value) -> dict | None:
    """One screen's widths, each known part a whole number of pixels within reach, anything else left
    out. None when nothing is left."""
    if not isinstance(value, dict):
        return None
    out = {}
    for key in COLUMN_WIDTH_KEYS:
        v = value.get(key)
        if isinstance(v, bool) or not isinstance(v, (int, float)) or v != v:
            continue
        out[key] = int(round(min(COLUMN_WIDTH_MOST, max(0, float(v)))))
    return out or None


def column_widths(value) -> dict:
    """Every screen's widths as config.json holds them, anything that is not a screen's left out."""
    if not isinstance(value, dict):
        return {}
    out = {}
    for key, widths in value.items():
        screen, kept = column_screen(key), column_width_set(widths)
        if screen and kept:
            out[screen] = kept
    return dict(list(out.items())[-COLUMN_SCREENS_KEPT:])


def stack_split(value) -> float | None:
    """The divider's place as config.json holds it, a share between the two ends of the range, rounded to
    a thousandth. None for anything that is not a number."""
    if isinstance(value, bool) or not isinstance(value, (int, float)) or value != value:
        return None
    low, high = STACK_SPLIT_RANGE
    return round(min(high, max(low, float(value))), 3)
# the counts the boards' status bar can show, in the order it shows them
STATUS_COUNTS = ("pets", "placed", "stacked", "binned", "unplaced", "loose")


def status_counts(value) -> list[str] | None:
    """The status bar's counts as a list of known names, each once, in the bar's own order, None for
    anything that is not a list."""
    if not isinstance(value, list):
        return None
    return [name for name in STATUS_COUNTS if name in value]


def palette_place(value) -> dict | None:
    """The palette's place as config.json holds it, `{"edge": "left" or "right", "y": 0 to 1}`, its top
    as a share of the canvas's height, None for anything else, which is its place at the left."""
    if not isinstance(value, dict) or value.get("edge") not in ("left", "right"):
        return None
    y = value.get("y")
    if isinstance(y, bool) or not isinstance(y, (int, float)) or y != y:
        return None
    return {"edge": value["edge"], "y": round(min(1.0, max(0.0, float(y))), 4)}


# Auto-arrange's ways (21 October), the first the default: a grid as it has always been, one card above
# another, or all in a row, each in the order they read
ARRANGE_WAYS = ("grid", "column", "row")


def arrange_way(value) -> str:
    """One of Auto-arrange's ways, the grid for anything else."""
    return value if value in ARRANGE_WAYS else ARRANGE_WAYS[0]


# the minimap's three choices, the first the default
MINIMAP_MODES = ("auto", "on", "off")


def minimap_mode(value) -> str:
    """The minimap's choice as config.json holds it, the tick's old true read as auto and its old
    false as off, anything else as the default."""
    if value is False or value == "off":
        return "off"
    return value if value in MINIMAP_MODES else MINIMAP_MODES[0]


@contextlib.contextmanager
def writing(path: Path | None = None, root: Path | None = None, books=(), export: bool = False, boards: bool = False):
    """Every write the server makes, one at a time: its own lock, which its threads take turns
    through, and the file lock the command line takes too (see `locks.py`), so a write from a
    conversation and one from the page never interleave. `path` is a workbook, whose case's lock is
    taken, and `root` a case root, whose own lock is taken, with the cases of `books` after it.
    A folder that is not there takes no lock, and none is made to hold one. In a project worked on together a
    participant another member works on is refused here, at their case's lock (`team_sync.guard`), unless the
    block is an `export`, which reads them and writes a file of its own, or `boards`, a board op, which writes a
    reviewer's own boards apart from the owner's (ownboards, 9 November 2026, `themes.OWN_FILE`)."""
    with srv._lock, contextlib.ExitStack() as held:
        if root is not None and Path(root).is_dir():
            held.enter_context(locks.root(root))
        for book in ([path] if path is not None else []) + list(books):
            if wb_mod.case_folder(Path(book)).is_dir():
                held.enter_context(wb_mod.case_held(book, export=export, boards=boards))
        yield


def project_id(root: Path | None) -> str:
    """A project as the page names it back: its root as a project's `root` stores it, from the repo
    root and any case folder in it a glob on its pseudonym (see `root_setting`), or the demo's word."""
    if root is None:
        return ""
    if srv.same_folder(root, srv.demo_ta_dir()):
        return srv.DEMO_TA_ID
    return "demo" if srv.same_folder(root, srv.DEMO_DIR) else root_setting(Path(root))


def keep_written(written: dict) -> None:
    """The files this process last wrote, kept in the app's state as `written` after each save, so after a
    restart a board still tells the app's own change from one made outside it (20 October)."""
    with srv.STATE_LOCK:
        data = srv.state()
        if data.get("written") == written:
            return
        data["written"] = written
        srv.save_state(data)


def keep_written_on() -> None:
    """At the server's start: the list a run before kept, of the files still as it wrote them, and every
    note after kept in turn. The command line, which imports this module, never calls it."""
    wb_mod.WRITTEN.update(wb_mod.still_written(srv.state().get("written")))
    wb_mod.WRITTEN_HOOK = keep_written


# A case renamed with its folder kept (16 October, see Rename) keeps its new pseudonym in its
# project's file, `names`, by the folder's label, never its second part, and every label the server hands the page or
# writes into a file goes through `case_label`, which reads it, so every screen shows the new name.
NAMES_HELD: dict[str, tuple] = {}


def names_at(root: Path | None) -> dict[str, str]:
    """The new names Rename gave the cases whose folders it kept, `names` in the project file at this
    root, each a folder's label, `display_case` of its name, and its pseudonym, one capitalised word, kept until the file changes.
    None for no project, and the demo's has none."""
    if root is None:
        return {}
    file = Path(root) / srv.PROJECT_FILE
    mark = file_mark(file)
    if mark is None:
        return {}
    held = NAMES_HELD.get(str(file))
    if held and held[0] == mark:
        return held[1]
    raw = project_file(Path(root)).get("names")
    names = {str(k): str(v).strip() for k, v in (raw.items() if isinstance(raw, dict) else ())
             if isinstance(k, str) and isinstance(v, str) and ONE_WORD.match(str(v).strip())}
    NAMES_HELD[str(file)] = (mark, names)
    return names


def relabel(label: str, new: str) -> str:
    """A case label with its pseudonym, the part after `P<n> - ` or else the whole, taken by `new`."""
    m = re.match(r"^(P\d+ - )", str(label or ""))
    return (m.group(1) if m else "") + str(new)


def label_for(folder: Path, names: dict | None = None) -> str:
    """A case folder's label as every screen shows it: `display_case` of its name, with the pseudonym
    Rename gave it in place of the folder's own while it kept the folder. `names` is its project's,
    when the caller has them already."""
    folder = Path(folder)
    shown = srv.display_case(folder.name)
    if names is None:
        names = names_at(srv.project_of(folder))
    new = names.get(srv.display_case(folder.name))
    return relabel(shown, new) if new else shown


def case_label(path) -> str:
    """The case a workbook belongs to, by its label, `P1 - Ada`, as every screen shows it and every file
    the app writes names it, a rename with the folder kept among them (see `label_for`)."""
    return label_for(wb_mod.case_folder(Path(path)))


def shown_name(path: Path) -> str:
    """A workbook's name as its screen's bar shows it, its stem, with the pseudonym Rename gave its
    case in place of the folder's own where the file's name still carries it."""
    path = Path(path)
    folder = wb_mod.case_folder(path)
    own, now = gets_mod.who(srv.display_case(folder.name)), gets_mod.who(label_for(folder))
    if own == now:
        return path.stem
    return re.sub(rf"(?<![A-Za-z]){re.escape(own)}(?![A-Za-z])", now, path.stem)


def path_key(value) -> str:
    """One form of a path for comparing two, whichever form each was written in: from `REPO_ROOT` or
    whole, with backslashes or forward slashes, as `rel_path` wrote it then or writes it now. The
    recent list and the case list compare their paths by it, never as written (20 October)."""
    try:
        return str(srv.abs_path(str(value)).resolve())
    except (OSError, ValueError):
        return str(value)


def demo_workbooks(root: Path | None = None) -> list[Path]:
    """Every demo case's workbook, built on this machine or not, Juno's first and the same path as
    DEMO_WORKBOOK, or with `root` the thematic analysis demo's folder (see `srv.demo_ta_dir`) the same three
    there."""
    root = Path(root) if root is not None else srv.DEMO_DIR
    return [root / name / f"{name} - EN & ES.xlsx" for name in DEMO_CASES]


def demo_title(path: Path) -> str:
    """A demo case's name on the screen, its case and the demo's topic: `Rowan, living with a dog`."""
    return f"{wb_mod.case_folder(Path(path)).name}, {DEMO_TOPIC}"


def case_path(value: str) -> Path:
    """A workbook path from a request, refused unless a project's root contains it.

    Every API that reads or writes a workbook resolves its path here, so a server started with
    `--root` at a scratch folder can never reach a live case, whatever its recent list says. On
    21 September 2026 a test server did exactly that through the recent list and wrote one line
    into a live workbook.
    """
    p = srv.abs_path(value)
    if not value or not srv.within_root(p):
        raise srv.OutsideRoot(i18n.t("server.workbook_sits_outside_project_folder"))
    return p


# -------------------------------------------------------------- project

def project_root(path: Path | None = None) -> Path | None:
    """The folder whose project a request belongs to.

    With a path, the project that holds it (see `project_of`), the demo's folder for the demo. With
    none, the first project, which is the `--root` of a scratch run when there is one, or None
    while there is no project. No other folder ever is.
    """
    if path is not None:
        return srv.project_of(path)
    roots = srv.project_roots()
    return roots[0] if roots else None


def asked_root(body: dict, write: bool = False) -> Path | None:
    """The project a Settings request is for: the one `root` names by its id, else the one the
    workbook `path` belongs to, else the only project there is. A path under no project's root is
    refused, and so is a write that names no project while there are several."""
    if body.get("root"):
        return srv.project_named(body["root"])
    if body.get("path"):
        root = srv.project_of(srv.abs_path(body["path"]))
        if root is None:
            raise srv.OutsideRoot(i18n.t("server.workbook_sits_outside_project_folder"))
        return root
    roots = srv.project_roots()
    if write and len(roots) > 1:
        raise WorkbookError(i18n.t("server.say_which_project_nothing_saved"))
    return roots[0] if roots else None


def api_project_history(body: dict) -> dict:
    """The project's own History as Project history on Home shows it (historyui, 3 November 2026): the records
    newest first a page at a time, `limit` of them from `offset` on, `by` "app" or "agent" for those alone, and
    `total`, how many there are with that `by`, read as `project history` reads them (`hist_mod.newest`), each with
    the agent's words cleaned (`hist_mod.for_page`). It reads and writes nothing else. The demo keeps none, so it
    answers none."""
    root = asked_root(body)

    def whole(key):
        n = body.get(key)
        return n if isinstance(n, int) and not isinstance(n, bool) and n > 0 else None

    by = body.get("by") if body.get("by") in ("app", "agent") else ""
    if root is None or srv.is_demo_root(root):
        return {"history": [], "total": 0}
    held, total = hist_mod.newest(root, whole("limit"), whole("offset") or 0, by)
    return {"history": [hist_mod.for_page(h) for h in held], "total": total}


TEAM_WRITES = ("on", "off", "set", "choose", "invite", "admit", "join", "joined", "remove", "send", "lead", "take")
TEAM_READS = ("show", "answers")


def api_team(body: dict) -> dict:
    """Working together, Project settings' section and the agents' `team` ops (wtkeys, 8 November 2026, see team.py):
    `op` one of `show`, `on`, `off`, `set`, `choose` (the shared folder from the Mac's dialog), `invite`, `answers`, `admit`, `join`, `joined`, `remove`, `lead` and `take`. `show`
    answers the section as it stands, `{"on": false}` alone while it is off, and writes nothing. `on` takes `name`,
    `route` (relay or folder), `folder`, and for a team's own relay `relay_url`, and `on` and `set` take `code`, the
    lead's relay code, which makes the project on the relay and is kept nowhere (relaywire, 9 November 2026), `set` any of `route`, `folder`, `recordings`, `owners` ({participant:
    member}) and `gets_owner`, `invite` `own` for another computer of one's own, `answers` and `admit` an `invite` id,
    `admit` `match` true or false (They match, They differ), `join` `words` (the link or the twelve words),
    `name` and a team's own relay's `relay_url` when the link does not carry it, `joined` the `invite` id, `remove` a `member` by id or name or one `computer` by its id, `lead` (Make
    lead) a `member`, and `take` what has come for the list of people (wtdevices, 9 November 2026). Each write takes `dry_run`, which writes
    nothing and says what would change, and runs under the project's lock with a line in the project's History for
    each change. The demo's project takes none. `send` (wtowners), Send now: what came for the project taken in and
    what of his waits sent at once (`team_sync.sync`), answering `applied`, `sent`, `waiting` and `offline`, with no
    line in History, since what it sends is his work as it stands and what it takes in carries its own History."""
    import team as team_mod
    op = str(body.get("op") or "show")
    if op not in TEAM_WRITES + TEAM_READS:
        raise WorkbookError(i18n.t("team.refused.no_op"))
    root = asked_root(body, write=op in TEAM_WRITES)
    if root is None or srv.is_demo_root(root):
        if op == "show":
            return {"team": {"on": False, "demo": True}}
        raise WorkbookError(i18n.t("server.demo_s_project_fixed"))
    dry = body.get("dry_run") is True
    try:
        if op == "show":
            return {"team": team_mod.view(root, team_participants(root)), "your_name": researcher_name(),
                    "sync": team_sync.status(root)}
        if op == "answers":
            return team_mod.answers(root, str(body.get("invite") or ""))
        if op == "send":
            if not team_mod.is_on(root):
                raise team_mod.TeamError(i18n.t("team.refused.off"), "off")
            done = team_sync.sync(root, now=True, dry_run=dry)
            return dict(done, changes=[], dry_run=dry, team=team_mod.view(root, team_participants(root)),
                        sync=team_sync.status(root))
        # what has come is fetched before the lock, since a relay can be slow to answer (wtdevices)
        come = team_mod.come(root) if op == "take" else None
        with contextlib.nullcontext() if dry else writing(root=root):
            if op == "on":
                done = team_mod.turn_on(root, body.get("name") or researcher_name(), str(body.get("route") or "relay"),
                                        str(body.get("folder") or ""), dry_run=dry, code=body.get("code"),
                                        relay_url=str(body.get("relay_url") or ""))
            elif op == "off":
                done = team_mod.turn_off(root, dry_run=dry)
            elif op in ("set", "choose"):
                if op == "choose":
                    # Choose beside the shared folder: the Mac's folder dialog, a Cancel changing nothing
                    if srv.PLATFORM != "darwin":
                        raise WorkbookError(srv.NO_DIALOG)
                    picked = srv.PICK_FOLDER(i18n.t("team.page.folder"))
                    if picked is None:
                        return {"changes": [], "team": team_mod.view(root, team_participants(root))}
                    body = {"folder": str(picked)}
                done = team_mod.set_team(root, body, team_participants(root), dry_run=dry)
            elif op == "invite":
                done = team_mod.invite(root, own=body.get("own") is True, dry_run=dry)
            elif op == "admit":
                done = team_mod.admit(root, str(body.get("invite") or ""), body.get("match") is True, dry_run=dry)
            elif op == "join":
                done = team_mod.join(root, str(body.get("words") or ""), body.get("name") or researcher_name(),
                                     dry_run=dry, relay_url=str(body.get("relay_url") or ""))
            elif op == "joined":
                done = team_mod.joined(root, str(body.get("invite") or ""), dry_run=dry)
            elif op == "lead":
                done = team_mod.make_lead(root, str(body.get("member") or ""), team_participants(root), dry_run=dry)
            elif op == "take":
                done = team_mod.take(root, dry_run=dry, items=come)
            elif body.get("computer"):
                done = team_mod.remove_computer(root, str(body.get("computer") or ""), dry_run=dry)
            else:
                done = team_mod.remove(root, str(body.get("member") or ""), dry_run=dry)
            if not dry:
                hist_mod.record(root, f"team {op}", done.get("changes") or [], hist_mod.asker(body))
    except team_mod.TeamError as exc:
        raise WorkbookError(str(exc)) from None
    return dict(done, team=team_mod.view(root, team_participants(root)))


TEAM_BOARD_WRITES = ("send", "take", "answer")
TEAM_BOARD_READS = ("show",)


def api_team_board(body: dict) -> dict:
    """A reviewer's board sent straight in (wtboard, 9 November 2026, see team_board.py), the PETs screen's and the
    agents' `team board-send`, `team board-take`, `team board-answer` and `team boards`: `op` one of `show`, `send`,
    `take` and `answer`. `show` answers the boards sent and come in, and with a participant's `workbook` (or `case`)
    and `timepoint` whether his board of it can go and the boards of it waiting for an answer. It writes nothing.
    `send` takes the participant and `board`, its id or name, the one on the canvas when left out. `take` brings in
    what has come and answers `came` and `answers`, and with `workbook` the participant's boards as the PETs screen
    takes them (`state`) when one of them came. `answer` takes `ref`, or the `workbook` whose newest board waits,
    `accept` true (Add as next board) or false (Decline, nothing written to the participant) and an optional
    `reason`, and with `workbook` answers the screen's state afterwards. Each write
    takes `dry_run`, runs under the project's lock and adds its lines to the project's History. Off, `show` and
    `take` answer `{"on": false}` and write nothing. The demo's project takes none."""
    import team as team_mod
    import team_board as board_mod
    op = str(body.get("op") or "show")
    if op not in TEAM_BOARD_WRITES + TEAM_BOARD_READS:
        raise WorkbookError(i18n.t("team.refused.no_op"))
    book = case_path(body["workbook"]) if body.get("workbook") else None
    root = asked_root(dict(body, path=str(book)) if book is not None and not body.get("root") else body,
                      write=op in TEAM_BOARD_WRITES)
    if root is None or srv.is_demo_root(root):
        if op in ("show", "take"):
            return {"board": {"on": False}}
        raise WorkbookError(i18n.t("server.demo_s_project_fixed"))
    if book is None and body.get("case") and op in ("show", "send"):
        try:
            book = Path(board_mod.participant(root, str(body["case"]))["workbook"])
        except team_mod.TeamError as exc:
            raise WorkbookError(str(exc)) from None
    tp = body.get("timepoint")
    dry = body.get("dry_run") is True
    if op == "show" or (op == "take" and not team_mod.is_on(root)):
        return {"board": board_mod.view(root, book, tp)}
    try:
        with contextlib.nullcontext() if dry else writing(root=root):
            if op == "send":
                if book is None:
                    raise WorkbookError(i18n.t("team.refused.no_participant", who=""))
                done = board_mod.send(root, workbook=book, board=body.get("board"), timepoint=tp, dry_run=dry)
            elif op == "take":
                done = board_mod.take(root, dry_run=dry)
            else:
                done = board_mod.answer(root, str(body.get("ref") or ""), body.get("accept") is not False,
                                        str(body.get("reason") or ""), workbook=book, dry_run=dry)
            if not dry:
                hist_mod.record(root, f"team board-{op}", done.get("changes") or [], hist_mod.asker(body))
    except team_mod.TeamError as exc:
        raise WorkbookError(str(exc)) from None
    out = dict(done, board=board_mod.view(root, book, tp))
    if book is not None and not dry and (op == "answer" or any(
            c.get("path") and Path(srv.abs_path(c["path"])).resolve() == Path(book).resolve()
            for c in done.get("came") or [])):
        # the participant's boards as the PETs screen takes them, so a board come in or taken off shows at once
        with themes_mod.scoped(board_mod.timepoint_of(root, tp)):
            out["state"] = themes_mod.state(book, case_label(book))
    return out


def team_participants(root: Path) -> list[dict]:
    """The participants Who works on each lists, each `{"folder", "label"}`, by their folder from the root."""
    return [{"folder": p["folder"], "label": p["label"]} for p in participant_books(root)]


def project_file(root: Path) -> dict:
    """The project file at a root as it sits on disk, or an empty dict when it is missing or unreadable."""
    try:
        data = json.loads((Path(root) / srv.PROJECT_FILE).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}
    return data if isinstance(data, dict) else {}


def read_project(root: Path) -> dict:
    """The project at a root, as the page draws it.

    With no file the name is the root folder's own, shown by its pseudonym when it is a case
    folder, and the research question is empty. `root` is the path the Settings card shows, `id`
    the project as the page names it back (see `project_id`), and `demo` says the project is the
    demo's, which is fixed. With no project there is none of it. `agents` is whether AI agents may
    read the project through the command line, and since when, `{"allowed", "at"}`: off unless the
    file's `agents` says so, and always on for the demo. `pet_labels` is how the exports label its
    PETs, "letters", the book's A, A1, A1.1, unless the file says "numbers" (see `pet_labels_for`).
    `timecodes` is how every timecode of the project is written, 75:12, 1:15:12 or 01:15:12, 1:15:12
    unless the file says otherwise (see `workbook.timecode`).
    `method` (tadraw, 31 October 2026) is the project's method, "ipa" or "ta", chosen on New project and fixed
    after, a file with none IPA's (see `method_of`).
    A `second_part` key a file from before 9 October holds is passed over.
    """
    if root is None:
        return {"name": "", "research_question": "", "updated": None, "root": "", "id": "", "demo": False,
                "agents": {"allowed": False, "at": None}, "pet_labels": themes_mod.LETTERS,
                "timecodes": wb_mod.TIMECODES_DEFAULT, "method": i18n.BASE_METHOD}
    root = Path(root)
    data = project_file(root)
    demo = srv.is_demo_root(root)
    return {
        "name": str(data.get("name") or "").strip() or srv.display_case(root.name),
        "method": method_of(data),
        "research_question": str(data.get("research_question") or "").strip(),
        "updated": data.get("updated") or None,
        "root": srv.display_path(srv.rel_path(root)),
        "id": project_id(root),
        "demo": demo,
        "agents": agents_of(data, demo),
        "pet_labels": themes_mod.pet_labels_of(data.get("pet_labels")),
        "timecodes": wb_mod.timecodes_of(data.get("timecodes")),
        "timepoints": timepoints_of(data),
        "statement_words": statement_words_of(data),
        # opened from a shared copy (21 October): the copy's card and page carry a "copy" tag
        "copy": isinstance(data.get("copy_of"), dict),
    }


# ------------------------------------------------------------ the method

# A project's method (tadraw, 31 October 2026, Adam's choices of 28 October): IPA or thematic analysis, chosen on
# New project and fixed after, since the two hold different things. The project file's `method`, "ipa" or "ta",
# written as the project is made, a file with none an IPA project's.


def method_of(data: dict) -> str:
    """The project's method as its file holds it, "ipa" or "ta", IPA's for a file with none or with anything
    else."""
    return i18n.method_of((data or {}).get("method") if isinstance(data, dict) else None)


def method_asked(given) -> str:
    """A method as New project or `project new` gives it, "ipa" for none, or refused in one line naming the
    two."""
    text = str(given or "").strip().lower()
    if text and text not in i18n.METHODS:
        raise WorkbookError(i18n.t("method.refused_two"))
    return text or i18n.BASE_METHOD


def method_name(method: str) -> str:
    """A method's name as a line says it, "Interpretative phenomenological analysis" or "Thematic analysis"."""
    return i18n.t("method.name_ta") if i18n.method_of(method) == "ta" else i18n.t("method.name_ipa")


# ------------------------------------------------------------ the statement length

# The length nudge's number, a project's own (Adam's ruling of 20 October, after a tester's statements of
# 28 words): 15 by default, the book's band (see `nudges.HIGH`), kept in the project file as
# `statement_words` only when it is not 15, so a project at 15 carries nothing new.
WORDS_MIN, WORDS_MAX = 5, 60


def statement_words_of(data: dict) -> int:
    """The project's statement length, the words past which the length nudge speaks, 15 for a file with
    none or with anything but a whole number from WORDS_MIN to WORDS_MAX."""
    held = data.get("statement_words") if isinstance(data, dict) else None
    if isinstance(held, int) and not isinstance(held, bool) and WORDS_MIN <= held <= WORDS_MAX:
        return held
    return nudges_mod.HIGH


def clean_statement_words(given) -> int:
    """A statement length as a call gives it, a whole number from WORDS_MIN to WORDS_MAX, or refused in
    one line saying so."""
    if isinstance(given, str) and given.strip().isdigit():
        given = int(given.strip())
    if isinstance(given, float) and given.is_integer():
        given = int(given)
    if not isinstance(given, int) or isinstance(given, bool) or not WORDS_MIN <= given <= WORDS_MAX:
        raise WorkbookError(i18n.t("server.statement_length_whole_number_words", least=WORDS_MIN, most=WORDS_MAX))
    return given


def write_statement_words(root: Path, given, dry_run: bool = False, who: dict | None = None) -> dict:
    """The project's statement length saved in the project file at this root, every other key kept as it
    was, the key taken away at 15. The demo's is fixed. With `dry_run` nothing is written. Answers the
    project, as it is or would be, and `changes`, a line each. A change is kept in the project's History,
    `who` asking (see `project_history`), the caller holding the project's lock."""
    if root is None or not Path(root).is_dir():
        raise WorkbookError(i18n.t("server.project_folder_project_could_saved"))
    root = Path(root)
    if srv.is_demo_root(root):
        raise WorkbookError(i18n.t("server.demo_s_project_fixed"))
    wanted = clean_statement_words(given)
    data = project_file(root)
    was = statement_words_of(data)
    changes = [f"Statement length from {was} to {wanted} words."] if wanted != was else []
    if not dry_run and (changes or ("statement_words" in data and wanted == nudges_mod.HIGH)):
        if wanted == nudges_mod.HIGH:
            data.pop("statement_words", None)
        else:
            data["statement_words"] = wanted
        srv.save_json(root / srv.PROJECT_FILE, data)
        hist_mod.record(root, "length", changes, who)
    project = read_project(root)
    if dry_run:
        project = dict(project, statement_words=wanted)
    return {"project": project, "changes": changes, "dry_run": bool(dry_run)}


def statement_words_for(path: Path | None) -> int:
    """The statement length of the project a workbook belongs to, 15 for one under none."""
    root = project_root(Path(path)) if path else None
    return statement_words_of(project_file(root)) if root is not None else nudges_mod.HIGH


# ------------------------------------------------------------ timepoints

# A longitudinal study (Farr and Nizza 2019, Adam's ruling of 20 October): the project says how many
# timepoints its data was collected at, each with a label, T1 large where room is short, and a
# description, Before the season, beside it where there is room. `timepoints` in the project file, a
# list in order, is written only with two or more, so a project of one carries nothing new and the
# app is as it was. A timepoint is known by its place, never its label, and a participant's sheets
# are placed at one in the progress file beside the workbook (see `rounds.sheet_timepoints`).
TP_MAX = 10
TP_LABEL_MAX = 12
TP_DESCRIPTION_MAX = 60


def tp_label(n: int) -> str:
    """A timepoint's label when he has given none, T1, T2, T3."""
    return f"T{n}"


def timepoints_of(data: dict) -> list[dict]:
    """The project's timepoints as the page and the API read them, each `{"n", "label",
    "description"}`, always at least one, T1 with no description for a file with none."""
    held = data.get("timepoints") if isinstance(data, dict) else None
    held = held if isinstance(held, list) else []
    out = []
    for i, entry in enumerate(held[:TP_MAX], start=1):
        entry = entry if isinstance(entry, dict) else {}
        out.append({"n": i, "label": " ".join(str(entry.get("label") or "").split())[:TP_LABEL_MAX] or tp_label(i),
                    "description": " ".join(str(entry.get("description") or "").split())[:TP_DESCRIPTION_MAX]})
    return out or [{"n": 1, "label": tp_label(1), "description": ""}]


def longitudinal(timepoints) -> bool:
    """Whether a project's timepoints are two or more, the one test every longitudinal part takes."""
    return isinstance(timepoints, list) and len(timepoints) >= 2


def clean_timepoints(given) -> list[dict]:
    """Timepoints as a call gives them, a list of `{"label", "description"}` or of labels, or a
    number, checked: from 1 to TP_MAX, each label short and none twice, an empty label its place's,
    T2. Refused in one line naming what to fix."""
    if isinstance(given, int) and not isinstance(given, bool):
        given = [{} for _ in range(max(0, given))]
    if not isinstance(given, list):
        raise WorkbookError(i18n.t("server.timepoints_list_each_label_description"))
    if not 1 <= len(given) <= TP_MAX:
        raise WorkbookError(i18n.t("server.project_from_1_timepoints_nothing", most=TP_MAX))
    out, seen = [], {}
    for i, entry in enumerate(given, start=1):
        if isinstance(entry, str):
            entry = {"label": entry}
        if not isinstance(entry, dict):
            raise WorkbookError(i18n.t("server.timepoints_list_each_label_description"))
        label = " ".join(str(entry.get("label") or "").split()) or tp_label(i)
        description = " ".join(str(entry.get("description") or "").split())
        if len(label) > TP_LABEL_MAX:
            raise WorkbookError(i18n.t("server.make_label_timepoint_characters_fewer", i=i, most=TP_LABEL_MAX))
        if len(description) > TP_DESCRIPTION_MAX:
            raise WorkbookError(i18n.t("server.make_description_characters_fewer_nothing", label=label, most=TP_DESCRIPTION_MAX))
        if label.lower() in seen:
            raise WorkbookError(i18n.t("server.timepoints_both_labelled_nothing_saved", first=seen[label.lower()], i=i, label=label))
        seen[label.lower()] = i
        out.append({"n": i, "label": label, "description": description})
    return out


def timepoint_books(root: Path) -> list[tuple[str, Path]]:
    """Each participant's workbook at a root whose progress file may place sheets at a timepoint, by
    the participant's label: every annotated workbook, and the workbook a raw source becomes, whose
    progress file an Add may have written before it was made."""
    out = []
    for row in list_cases(root):
        if row.get("kind") == "annotated":
            out.append((row["case"], srv.abs_path(row["path"])))
        elif row.get("kind") == "raw" and row.get("suggested"):
            out.append((row["case"], srv.abs_path(row["suggested"])))
    return out


def timepoint_holders(root: Path, keep: int) -> dict[str, list[int]]:
    """The participants holding data at a timepoint after `keep`, by label, each with those
    timepoints: a sheet placed there, or its Statements complete mark. Only reads."""
    out: dict[str, set] = {}
    for case, book in timepoint_books(root):
        try:
            data = rounds_mod.read_raw(book)
        except (ValueError, OSError):
            continue
        held = set(rounds_mod.sheet_timepoints(data).values()) | set(rounds_mod.marked_timepoints(data))
        later = {n for n in held if n > keep}
        if later:
            out.setdefault(case, set()).update(later)
    return {case: sorted(ns) for case, ns in sorted(out.items(), key=lambda kv: gets_mod.case_order(kv[0]))}


def write_timepoints(root: Path, given, dry_run: bool = False, who: dict | None = None) -> dict:
    """The project's timepoints saved in the project file at this root, every other key kept as it
    was, the key taken away for one timepoint. Lowering the number is refused while a timepoint that
    would go holds data, naming the participants who hold it. With `dry_run` nothing is written.
    Answers the project, as it is or would be, and `changes`, a line each, kept in the project's History,
    `who` asking (see `project_history`), the caller holding the project's lock."""
    if root is None or not Path(root).is_dir():
        raise WorkbookError(i18n.t("server.project_folder_project_could_saved"))
    root = Path(root)
    wanted = clean_timepoints(given)
    data = project_file(root)
    # a thematic analysis project has no timepoints yet (tadraw, Adam's choice 2 of 28 October)
    if longitudinal(wanted) and method_of(data) == "ta":
        raise WorkbookError(i18n.t("method.refused_timepoints"))
    was = timepoints_of(data)
    if len(wanted) < len(was):
        holders = timepoint_holders(root, len(wanted))
        if holders:
            gone = sorted({n for ns in holders.values() for n in ns})
            named = formats.list_words(was[n - 1]["label"] if n <= len(was) else tp_label(n) for n in gone)
            who = formats.list_words(srv.display_case(c).split(" - ", 1)[-1] for c in holders)
            raise WorkbookError(i18n.t("server.timepoints_held", n=len(gone), named=named, who=who, was=len(was)))
    changes = []
    if len(wanted) != len(was):
        changes.append(f"Timepoints from {len(was)} to {len(wanted)}.")
    for tp in wanted:
        before = was[tp["n"] - 1] if tp["n"] <= len(was) else None
        said = f"{tp['label']}{', ' + tp['description'] if tp['description'] else ''}"
        if before is None:
            if longitudinal(wanted):
                changes.append(f"Timepoint {tp['n']} added, {said}.")
        elif (before["label"], before["description"]) != (tp["label"], tp["description"]) and longitudinal(wanted):
            changes.append(f"Timepoint {tp['n']} now {said}.")
    if not dry_run and changes:
        if longitudinal(wanted):
            data["timepoints"] = [{"label": tp["label"], "description": tp["description"]} for tp in wanted]
        else:
            data.pop("timepoints", None)
        srv.save_json(root / srv.PROJECT_FILE, data)
        hist_mod.record(root, "timepoints", changes, who)
    project = read_project(root)
    if dry_run:
        project = dict(project, timepoints=wanted)
    return {"project": project, "changes": changes, "dry_run": bool(dry_run)}


def project_timepoints(path: Path) -> list[dict]:
    """The timepoints of the project a workbook belongs to, one for a workbook under none."""
    root = srv.project_of(Path(path))
    return timepoints_of(project_file(root) if root is not None else {})


def timepoint_asked(value, timepoints: list[dict]) -> int:
    """The timepoint a call names, by its place or its label, 1 when it names none. Refused when the
    project has no such timepoint."""
    if value in (None, ""):
        return 1
    if isinstance(value, str) and not value.strip().isdigit():
        found = [tp["n"] for tp in timepoints if tp["label"].lower() == " ".join(value.split()).lower()]
        if not found:
            raise WorkbookError(i18n.t("server.timepoint_project", value=value.strip()))
        return found[0]
    try:
        n = int(value)
    except (TypeError, ValueError):
        raise WorkbookError(i18n.t("server.timepoint_number_1_2_3")) from None
    if not 1 <= n <= len(timepoints):
        many = len(timepoints)
        raise WorkbookError(i18n.t("server.no_such_timepoint", n=many, number=n))
    return n


def by_timepoint(sheets: list[str], progress: dict | None, states: dict, timepoints: list[dict]) -> list[dict]:
    """Each timepoint of a participant as a card and the statements screen show it: its label and
    description, its sheets in workbook order, the passages decided of the passages there, its
    Statements complete mark and `state`, `none` with no sheet (not interviewed), `complete` once
    marked, else `progress`. `states` is every participant passage's state by `sheet:row`."""
    placed = rounds_mod.sheet_timepoints(progress)
    out = []
    for tp in timepoints:
        mine = [s for s in sheets if placed.get(s, 1) == tp["n"]]
        keys = [k for k in states if rounds_mod.split_key(k)[0] in mine]
        done = sum(1 for k in keys if states[k] in rounds_mod.DECIDED)
        at = rounds_mod.complete_at_timepoint(progress, tp["n"]) if mine else None
        out.append(dict(tp, sheets=mine, done=done, total=len(keys), complete=at,
                        state="none" if not mine else "complete" if at else "progress"))
    return out


def timepoints_view(path: Path, sheets: list[str], progress: dict | None, states: dict) -> list[dict] | None:
    """A workbook's timepoints for its summary and its card, None in a project of one timepoint,
    which answers nothing new."""
    tps = project_timepoints(path)
    if not longitudinal(tps):
        return None
    return by_timepoint(sheets, progress, states, tps)


# ---- timepoints part 2 (21 October): a PETs canvas per timepoint and the LPETs canvas

# the routes a board's timepoint applies to, `timepoint` in the call naming it, and the GETs routes that
# take `lpets`, which puts them on the participant's LPETs (see `route_scope`)
THEMES_ROUTES = frozenset(("/api/themes", "/api/themes-save", "/api/themes-versions", "/api/themes-boards",
                           "/api/themes-cases", "/api/themes-export", "/api/themes-ai", "/api/edit-statement",
                           "/api/stamp", "/themes/print"))
GETS_ROUTES = frozenset(("/api/gets", "/api/gets-save", "/api/gets-ops", "/api/gets-boards", "/api/gets-cases",
                         "/api/gets-trail", "/api/gets-ai", "/api/stamp", "/gets/print"))
# the participant whose LPETs a request is on, which `gets_books` answers with their timepoints
LPETS_FOR: contextvars.ContextVar = contextvars.ContextVar("idiograph_lpets_for", default=None)


def board_timepoint(path: Path, value) -> int | None:
    """The timepoint a call's PETs board is at: its number in a project of two or more, 1 when the call
    names none, and None in a project of one timepoint, which reads and writes exactly as before. A
    timepoint the project does not have is refused."""
    tps = project_timepoints(path)
    n = timepoint_asked(value, tps)
    return n if longitudinal(tps) else None


def participant_timepoints(path: Path) -> list[dict]:
    """A participant's timepoints with where each stands (see `by_timepoint`), the project's alone with
    no sheets for a workbook that cannot be read."""
    tps = card_timepoints(path, srv.config().get("interviewer") or "")
    if tps:
        return tps
    return [dict(t, sheets=[], done=0, total=0, complete=None, state="none") for t in project_timepoints(path)]


def lpets_books(path: Path) -> list[dict]:
    """A participant's timepoints as the LPETs canvas takes them in, one "case" each, `T1`, `T2`, the
    participant's workbook read at that timepoint, a timepoint they were not interviewed at `missing`."""
    return [{"case": tp_label(t["n"]), "workbook": Path(path), "timepoint": t["n"], "cite": t["label"],
             "missing": t["state"] == "none", "pets_complete": None} for t in participant_timepoints(path)]


@contextlib.contextmanager
def lpets_scope(path: Path):
    """What runs inside works on the participant's LPETs: the file, the timepoints and their labels."""
    tps = project_timepoints(path)
    if not longitudinal(tps):
        raise WorkbookError(i18n.t("server.lpets_come_two_more_timepoints"))
    token = LPETS_FOR.set(Path(path))
    try:
        with gets_mod.lpets(path, {tp_label(t["n"]): t["label"] for t in tps}):
            yield
    finally:
        LPETS_FOR.reset(token)


# ---- timepoints part 3 (21 October): LGETs and the Trajectories board

# in a project of two or more timepoints the project's board across its participants is its LGETs, made from
# their LPETs, and every GETs route runs there (Adam's answer of 20 October: only LGETs, no GETs at a single
# timepoint). The GETs file stays as it was, for a project that goes back to one timepoint
LGETS_ROUTES = GETS_ROUTES | frozenset(("/api/gets-settings", "/api/gets-head"))
LGETS_FOR: contextvars.ContextVar = contextvars.ContextVar("idiograph_lgets_for", default=None)


def root_timepoints(root: Path | None) -> list[dict]:
    """The timepoints of the project at a root, one for none."""
    return timepoints_of(project_file(root) if root is not None else {})


@contextlib.contextmanager
def lgets_scope(root: Path):
    """What runs inside works on the project's LGETs, its timepoints' labels by their keys."""
    tps = root_timepoints(root)
    token = LGETS_FOR.set(Path(root))
    try:
        with gets_mod.lgets(root, {tp_label(t["n"]): t["label"] for t in tps}):
            yield
    finally:
        LGETS_FOR.reset(token)


@contextlib.contextmanager
def board_scope(root: Path | None):
    """The project's board across its participants: its LGETs in a project of two or more timepoints, and
    its GETs, exactly as before, in a project of one. Inside a participant's LPETs it changes nothing."""
    if root is None or LPETS_FOR.get() is not None or LGETS_FOR.get() is not None \
            or not longitudinal(root_timepoints(root)):
        yield
        return
    with lgets_scope(root):
        yield


def request_method(body) -> str | None:
    """The method of the project a request names (tagaps, 1 November 2026): the one its `workbook` or `path`
    belongs to, else the one `root` names, by its id or its folder, else the one `folder` sits in, else the only
    project there is, and None when it names none that is there."""
    if not isinstance(body, dict):
        return None
    try:
        value = body.get("workbook") or body.get("path")
        if value and isinstance(value, str):
            root = srv.project_of(srv.abs_path(value))
        elif body.get("root") and isinstance(body.get("root"), str):
            asked = srv.abs_path(body["root"]).resolve()
            root = next((Path(r) for r in [srv.DEMO_DIR, srv.demo_ta_dir()] + srv.project_roots() if Path(r).resolve() == asked), None)
            root = root or srv.project_named(body["root"])
        elif body.get("folder") and isinstance(body.get("folder"), str):
            root = srv.project_of(srv.abs_path(body["folder"]))
        else:
            roots = srv.project_roots()
            root = roots[0] if len(roots) == 1 else None
    except (WorkbookError, srv.OutsideRoot, OSError, ValueError, TypeError):
        return None
    return method_of(project_file(root)) if root is not None else None


@contextlib.contextmanager
def route_scope(route: str | None, body):
    """A request run in the words of its project's method (`request_method`, tagaps), and where it is on a board
    at a timepoint or a participant's LPETs, there (`place_scope`)."""
    with i18n.in_method(request_method(body)):
        with place_scope(route, body):
            yield


@contextlib.contextmanager
def place_scope(route: str | None, body):
    """A request on a board at a timepoint, or on a participant's LPETs, run there: `timepoint` on a
    PETs route sets the timepoint every reader and writer of the themes file goes by (`themes.scoped`),
    and `lpets` on a GETs route puts it on the participant's LPETs (`lpets_scope`). Any other request,
    and one naming neither, runs as it always did."""
    if not isinstance(body, dict) or route not in THEMES_ROUTES | LGETS_ROUTES:
        yield
        return
    value = body.get("workbook") or body.get("path")
    lpets = route in GETS_ROUTES and ticked(body.get("lpets"), False)
    # a GETs route in a project of two or more timepoints is on its LGETs (`board_scope`)
    if route in LGETS_ROUTES and not lpets and (route != "/api/stamp" or ticked(body.get("gets"), False)):
        try:
            root = gets_root(body) if route != "/gets/print" else gets_print_root(body)
        except (WorkbookError, srv.OutsideRoot, KeyError):
            root = None
        if root is not None and longitudinal(root_timepoints(root)):
            with board_scope(root):
                yield
            return
    tp = body.get("timepoint")
    if not value or (not lpets and tp in (None, "")):
        yield
        return
    path = case_path(value)
    if lpets:
        with lpets_scope(path):
            yield
        return
    with themes_mod.scoped(board_timepoint(path, tp)):
        yield


def order_of(data: dict) -> list[str]:
    """His order of the cases, `order` in the project file, each a case label, or none."""
    held = data.get("order") if isinstance(data.get("order"), list) else []
    return [str(label) for label in held if isinstance(label, str) and label.strip()]


def write_order(root: Path, labels) -> list[str]:
    """His order of the cases saved as `order` in the project file at this root, every other key
    kept as it was. The demo's order is fixed, and a root that is not a folder is refused."""
    if root is None or not Path(root).is_dir():
        raise WorkbookError(i18n.t("server.project_folder_order_could_saved"))
    if srv.is_demo_root(root):
        raise WorkbookError(i18n.t("server.demo_s_order_fixed"))
    if not isinstance(labels, list):
        raise WorkbookError(i18n.t("server.order_list_participants"))
    order: list[str] = []
    for label in labels:
        text = srv.display_case(" ".join(str(label or "").split()))
        if text and text not in order:
            order.append(text)
    data = project_file(Path(root))
    data["order"] = order
    srv.save_json(Path(root) / srv.PROJECT_FILE, data)
    return order


def agents_of(data: dict, demo: bool = False) -> dict:
    """The privacy tick, Allow AI agents to read this project, as the project file keeps it:
    `agents` `{"allowed": true, "at": "<iso>"}`, off with no such key, and on for the demo."""
    held = data.get("agents") if isinstance(data.get("agents"), dict) else {}
    if demo:
        return {"allowed": True, "at": None}
    return {"allowed": held.get("allowed") is True, "at": str(held.get("at") or "") or None}


def write_agents(root: Path, allowed: bool) -> dict:
    """The privacy tick saved in the project file at this root, with the time it was set, every
    other key kept as it was. The root has to be a folder already."""
    if root is None or not Path(root).is_dir():
        raise WorkbookError(i18n.t("server.project_folder_project_could_saved"))
    data = project_file(Path(root))
    data["agents"] = {"allowed": bool(allowed), "at": datetime.now().astimezone().isoformat(timespec="seconds")}
    srv.save_json(Path(root) / srv.PROJECT_FILE, data)
    return read_project(root)


def write_labels(root: Path, labels, dry_run: bool = False) -> dict:
    """How the exports label this project's PETs, `pet_labels` in the project file at this root,
    "letters" or "numbers", saved at once with every other key kept as it was. Anything else is
    refused, and so is a root that is not a folder. With `dry_run` nothing is written, and the
    answer is the project as it would be."""
    if root is None or not Path(root).is_dir():
        raise WorkbookError(i18n.t("server.project_folder_project_could_saved"))
    if labels not in themes_mod.PET_LABELS:
        raise WorkbookError(i18n.t("server.pet_labels_letters_numbers_nothing"))
    if dry_run:
        return dict(read_project(root), pet_labels=labels)
    data = project_file(Path(root))
    data["pet_labels"] = labels
    srv.save_json(Path(root) / srv.PROJECT_FILE, data)
    return read_project(root)


def write_timecodes(root: Path, form, dry_run: bool = False) -> dict:
    """How this project writes its timecodes, `timecodes` in the project file at this root, 75:12, 1:15:12
    or 01:15:12, saved at once with every other key kept as it was (28 October). Anything else is refused,
    and so is a root that is not a folder. With `dry_run` nothing is written, and the answer is the project
    as it would be."""
    if root is None or not Path(root).is_dir():
        raise WorkbookError(i18n.t("server.project_folder_project_could_saved"))
    if form not in wb_mod.TIMECODES:
        raise WorkbookError(i18n.t("server.timecodes_three_nothing"))
    if dry_run:
        return dict(read_project(root), timecodes=form)
    data = project_file(Path(root))
    data["timecodes"] = form
    srv.save_json(Path(root) / srv.PROJECT_FILE, data)
    return read_project(root)


def pet_labels_for(path: Path) -> str:
    """How the exports label the PETs of the case a workbook belongs to, its project's `pet_labels`,
    the one place the Word document, the print view and the PET draft take it from on the server."""
    return read_project(project_root(Path(path)))["pet_labels"]


def write_project(root: Path, name: str, question: str, dry_run: bool = False) -> dict:
    """Save the name and the question in the project file at this root, and nowhere else.

    The root has to be a folder already: nothing is created to hold the file. Any key the file
    carries beyond the three is kept as it was. With `dry_run` nothing is written, and the answer
    is the project as it would be.
    """
    if root is None or not Path(root).is_dir():
        raise WorkbookError(i18n.t("server.project_folder_project_could_saved"))
    root = Path(root)
    data = project_file(root)
    data.update(name=str(name or "").strip(), research_question=str(question or "").strip(),
                updated=datetime.now().astimezone().isoformat(timespec="seconds"))
    if dry_run:
        return dict(read_project(root), name=data["name"] or srv.display_case(root.name),
                    research_question=data["research_question"])
    srv.save_json(root / srv.PROJECT_FILE, data)
    return read_project(root)


def project_changes(before: dict, after: dict) -> list[str]:
    """What a save from Settings changes in the project, a line each, from the project as `read_project`
    reads it before and after: its name, its research question, how the exports label its PETs, how its
    timecodes are written and the privacy tick (26 October, for the agents' `project set`)."""
    out = []
    said = lambda text: f'"{text}"' if text else "none"
    if before["name"] != after["name"]:
        out.append(f"Name from {said(before['name'])} to {said(after['name'])}.")
    if before["research_question"] != after["research_question"]:
        out.append(f"Research question from {said(before['research_question'])} to {said(after['research_question'])}.")
    if before["pet_labels"] != after["pet_labels"]:
        out.append(f"PET labels from {before['pet_labels']} to {after['pet_labels']}.")
    if before.get("timecodes") != after.get("timecodes"):
        out.append(f"Timecodes from {before.get('timecodes')} to {after.get('timecodes')}.")
    if before["agents"]["allowed"] != after["agents"]["allowed"]:
        out.append("Allow AI agents to read this project " + ("ticked." if after["agents"]["allowed"] else "unticked."))
    return out


# ---------------------------------------------------------------- cases

def file_mark(path: Path) -> tuple | None:
    """A file's modification time and size, which a cached read is kept against, or None when the
    file is not there."""
    try:
        st = Path(path).stat()
    except OSError:
        return None
    return st.st_mtime_ns, st.st_size


# what the home screen has read, each kept against the marks of the files it came from, so a
# listing reads a workbook, a progress file or a themes file again only once it has changed
BOOKS: dict[str, tuple] = {}
TURNS: dict[str, tuple] = {}
BOARDS: dict[str, tuple] = {}
GETS_FILES: dict[str, tuple] = {}


def read_book(path: Path) -> dict | None:
    """A workbook as the case list and the cards read it, opened read-only once and kept until it
    changes: `kind`, `sheets`, its transcript sheets in workbook order, `names`, every sheet's
    name, and `turns`, each transcript sheet's rows as (row, speaker, whether it holds a
    statement), the rows `workbook.read_case` keeps. None for a file that cannot be opened.

    A sheet counts when it has a Name, a Timestamp and a Transcript column.
    """
    key = str(path)
    mark = file_mark(path)
    held = BOOKS.get(key)
    if mark is not None and held and held[0] == mark:
        return held[1]
    try:
        book = openpyxl.load_workbook(path, read_only=True)
    except Exception:
        return None
    kinds, sheets, turns = set(), [], {}
    try:
        names = list(book.sheetnames)
        for ws in book.worksheets:
            cols = wb_mod.detect_columns(ws)
            if not {"name", "ts", "transcript"} <= set(cols):
                continue
            sheets.append(ws.title)
            kinds.add("raw" if wb_mod.is_raw_source(cols) else "annotated")
            width = max(cols.values())
            rows = []
            for number, values in enumerate(ws.iter_rows(min_row=2, max_col=width, values_only=True), start=2):
                cell = lambda role: values[cols[role] - 1] if role in cols and cols[role] <= len(values) else None
                name, ts, text = cell("name"), cell("ts"), cell("transcript")
                if name is None and ts is None and text is None:
                    continue
                es = cell("es")
                rows.append((number, str(name).strip() if name is not None else "",
                             bool(wb_mod.field_to_lines(es).strip()) if es is not None else False))
            turns[ws.title] = rows
    except Exception:
        return None
    finally:
        book.close()
    out = {"kind": "raw" if kinds == {"raw"} else "annotated", "sheets": sheets, "names": names,
           "turns": turns}
    if mark is not None:
        BOOKS[key] = (mark, out)
    return out


def read_sheets(path: Path) -> tuple[str, list[str]] | None:
    """The kind of workbook and its transcript sheets, in workbook order, or None for neither.

    The case list and the cards both read a workbook through here, so they list the same sheets.
    """
    book = read_book(path)
    if not book or not book["sheets"]:
        return None
    return book["kind"], list(book["sheets"])


def turns_of(path: Path, interviewer: str) -> dict | None:
    """The turns decided of the turns there, `{"done", "total"}`, as the case's own screen counts
    them, from the workbook already read for its sheets and the progress file beside it, kept
    until either changes. None for a workbook that is not annotated."""
    book = read_book(path)
    if not book or book["kind"] != "annotated":
        return None
    who = str(interviewer or "").strip().lower()
    # the project's timepoints too, so a change in Settings is counted again
    tps_now = tuple((t["n"], t["label"], t["description"]) for t in project_timepoints(path))
    mark = (file_mark(path), file_mark(rounds_mod.progress_path(path)), who, tps_now)
    held = TURNS.get(str(path))
    if held and held[0] == mark:
        return dict(held[1])
    progress = rounds_mod.load_progress(path)
    sheets = [{"name": name, "rows": [{"sheet": name, "row": row, "name": speaker, "es": "x" if has else ""}
                                      for row, speaker, has in book["turns"].get(name, [])]}
              for name in book["sheets"]]
    states = rounds_mod.row_states(sheets, progress, who)
    out = {"done": sum(1 for v in states.values() if v in rounds_mod.DECIDED), "total": len(states)}
    # and in a project of two or more timepoints, each one's (see `timepoints_view`), kept with them
    tps = timepoints_view(path, list(book["sheets"]), progress, states)
    TURNS[str(path)] = (mark, out, tps)
    return dict(out)


def card_timepoints(path: Path, interviewer: str) -> list[dict] | None:
    """A participant's timepoints for their card, each with its sheets, its counts and its mark, None
    in a project of one timepoint or for a workbook that is not annotated. Read with the counts
    `turns_of` reads, and kept with them."""
    if turns_of(path, interviewer) is None:
        return None
    held = TURNS.get(str(path))
    tps = held[2] if held else None
    return [dict(t, sheets=list(t["sheets"])) for t in tps] if tps else None


def boards_count(path: Path) -> int:
    """How many boards a case's themes file holds, 0 with no file or one that cannot be read, kept
    until the file changes."""
    file = themes_mod.themes_path(path)
    mark = file_mark(file)
    if mark is None:
        return 0
    held = BOARDS.get(str(file))
    if held and held[0] == mark:
        return held[1]
    try:
        count = len(themes_mod.boards_of(themes_mod.load(path)))
    except (WorkbookError, OSError):
        count = 0
    BOARDS[str(file)] = (mark, count)
    return count


def gets_file(root: Path | None) -> dict | None:
    """A project's GETs file as it sits, None with none or one that cannot be read, kept until it
    changes. Only read."""
    if root is None:
        return None
    file = gets_mod.gets_path(root)
    mark = file_mark(file)
    if mark is None:
        return None
    # the project file's too, since its timecodes say how the times read (see `gets.load`)
    mark = (mark, file_mark(Path(root) / srv.PROJECT_FILE))
    held = GETS_FILES.get(str(file))
    if held and held[0] == mark:
        return held[1]
    try:
        data = gets_mod.load(root)
    except (WorkbookError, OSError):
        data = None
    GETS_FILES[str(file)] = (mark, data)
    return data


def pristine_copy(book: Path) -> bool:
    """Whether a workbook is a demo's pristine copy, the one Reset demo restores from: it sits in a
    folder named `pristine` beside a folder of its case's name, as `demo/pristine/Mabel - EN & ES.xlsx`
    sits beside `demo/Mabel/`. A copy of the demo folder added as a project holds one, and it is never
    a case of its own (20 October, Mabel twice on the GETs board)."""
    book = Path(book)
    if book.parent.name != "pristine":
        return False
    case = book.name.split(" - ", 1)[0].strip()
    return bool(case) and (book.parent.parent / case).is_dir()


def list_cases(root) -> list[dict]:
    """The annotated workbook of each case of a project and its raw source, nothing else but a
    transcript in another shape in a case's own `Source/`, which `convert.offered` passes. `root` is
    the project's root folder, and a settings dict stands for every project it names, in order.

    Anything under `_Archive`, `Working` and the like is left out, so is anything deeper than a
    case's own `Source/`, and so is a backup copy wherever it sits (BACKUP_STEM).
    """
    if isinstance(root, dict):
        return [row for each in srv.project_roots(root) for row in list_cases(each)]
    root = Path(root) if root is not None else None
    found: list[dict] = []
    if root is None or not root.exists():
        return found
    # the new names Rename kept in the project file, read once for every row
    names = names_at(root)
    # a folder inside with a project file of its own is that project's, never cases of this one: the thematic
    # analysis demo inside the IPA demo's folder, or inside a copy of it (demos, 3 November 2026)
    nested, files = [], []
    for p in root.rglob("*"):
        if p.name == srv.PROJECT_FILE and p.parent != root:
            nested.append(p.parent)
        elif p.suffix.lower() in convert_mod.FORMATS and p.is_file():
            files.append(p)
    for path in sorted(files):
        if path.name.startswith("~$") or path.name.startswith("."):
            continue
        if nested and any(srv.inside(path, folder) for folder in nested):
            continue
        if BACKUP_STEM.search(path.stem):
            continue
        folders = path.relative_to(root).parts[:-1]
        # A raw source worth offering sits in the case folder's own `Source/`. Anything deeper is a
        # per-session extract or a working copy of one, not a case to start from.
        in_source = bool(folders) and folders[-1] == "Source" and "Source" not in folders[:-1]
        if set(folders) & (SKIP_DIRS - {"Source"}):
            continue
        if "Source" in folders and not in_source:
            continue
        if pristine_copy(path):
            continue
        # a transcript in another shape, offered from the case's own `Source/` to be made into a
        # workbook, and an Excel file there with no three columns is one too
        read = read_sheets(path) if path.suffix.lower() == ".xlsx" else None
        if read is None:
            if in_source and convert_mod.offered(path):
                found.append(transcript_row(path))
            continue
        kind, sheets = read
        if in_source and kind != "raw":
            continue
        found.append({
            "path": srv.rel_path(path),
            "name": path.stem,
            "case": label_for(wb_mod.case_folder(path), names),
            "kind": kind,
            "sheets": sheets,
            "locked": wb_mod.lock_file(path).exists(),
            "suggested": srv.rel_path(wb_mod.suggested_output(path)) if kind == "raw" else None,
            "modified": int(path.stat().st_mtime),
            # the Current board's name, or None, read from the themes file's head (see
            # `themes.chosen_name`), for the row's small type
            "board": themes_mod.chosen_name(path) if kind == "annotated" else None,
            # the time the experiential statements phase was marked complete, or None, read from
            # the progress file beside the workbook, for the row's small type
            "complete": rounds_mod.complete_of(path) if kind == "annotated" else None,
            # and the PETs phase, `{"at", "board", "name"}` or None, read from the themes file
            "pets_complete": themes_mod.pets_complete_of(path) if kind == "annotated" else None,
        })
    return found


def transcript_row(path: Path) -> dict:
    """A transcript file's row in the case list, `kind` `transcript`, with `suggested` the raw
    source it is made into beside it. The file is not opened until its card asks."""
    return {"path": srv.rel_path(path), "name": path.name, "case": case_label(path),
            "kind": "transcript", "sheets": [], "locked": False,
            "suggested": srv.rel_path(convert_mod.output_for(path)), "modified": int(path.stat().st_mtime),
            "board": None, "complete": None, "pets_complete": None}


def demo_entry(workbook: Path | None = None) -> dict | None:
    """One demo case's row in the Demo section, Juno's unless `workbook` names another, or None
    when that case has not been built on this machine.

    Juno's row is also `demo` in the case list's answer, the one card a page from before the three
    cases draws. A payload with no `demo` in it is what an older server sends, and the page draws no
    section at all for that, so a static file that has reached the browser before the restart
    breaks nothing.
    """
    workbook = Path(workbook) if workbook is not None else srv.DEMO_WORKBOOK
    if not workbook.exists():
        return None
    book = read_book(workbook)
    sheets = list(book["names"]) if book else [DEMO_SHEET]
    # the demo's names are fixed, so its label is its folder's alone
    return {"path": srv.rel_path(workbook), "name": demo_title(workbook),
            "case": srv.display_case(wb_mod.case_folder(workbook).name),
            "kind": "annotated", "sheets": sheets, "demo": True, "suggested": None,
            "locked": wb_mod.lock_file(workbook).exists(),
            "modified": int(workbook.stat().st_mtime),
            "board": themes_mod.chosen_name(workbook),
            "complete": rounds_mod.complete_of(workbook),
            "pets_complete": themes_mod.pets_complete_of(workbook)}


def demo_entries(root: Path | None = None) -> list[dict]:
    """The Demo section's rows, Juno, Rowan and Mabel in that order, each case built on this machine, the IPA
    demo's or with `root` the thematic analysis demo's."""
    return [row for row in (demo_entry(book) for book in demo_workbooks(root)) if row]


def remember(path: Path, timepoint: int | None = None) -> None:
    # The demo is never one of the recent cases.
    if srv.is_demo(path):
        return
    # The newest first, always. Every entry is stored with its display label, so an older entry
    # that still carries a folder's second name loses it here, the next time anything is opened,
    # and the `screen` a build from before kept for the home screen goes with it.
    data = srv.state()
    entry = {"path": srv.rel_path(path), "name": Path(path).stem,
             "case": case_label(path), "opened": int(time.time())}
    same = [r for r in data.get("recent", []) if path_key(r.get("path", "")) == path_key(entry["path"])]
    # in a project of two or more timepoints, the timepoint whose PETs were opened last, which an open of
    # the statements screen keeps, for the tabs of the project's LGETs (getsB, 26 October)
    kept = timepoint or (same[0].get("timepoint") if same else None)
    if kept:
        entry["timepoint"] = int(kept)
    older = [dict({k: v for k, v in r.items() if k != "screen"}, case=srv.display_case(r.get("case", "")))
             for r in data.get("recent", []) if path_key(r.get("path", "")) != path_key(entry["path"])]
    data["recent"] = ([entry] + older)[:8]
    srv.save_state(data)


def last_opened(cases: list[dict]) -> dict | None:
    """Of a project's GETs or LGETs cases, each with its `workbook`, the participant opened last, from the
    recent list: `case` as the cases name it, `path`, the workbook he opened, and `timepoint`, the one whose
    PETs he opened last in a project of two or more, else None. None when no case of the project is in
    the list. The steps of the GETs opened from Home's card open this participant (Adam's option B, 26
    October). Writes nothing."""
    folders = {}
    for c in cases:
        if c.get("workbook"):
            folders.setdefault(str(wb_mod.case_folder(Path(c["workbook"])).resolve()), c)
    for r in srv.state().get("recent", []):
        path = srv.abs_path(r.get("path", ""))
        if not srv.within_root(path) or srv.is_demo(path) or not path.exists():
            continue
        hit = folders.get(str(wb_mod.case_folder(path).resolve()))
        if hit:
            return {"case": hit["case"], "path": srv.rel_path(path), "timepoint": r.get("timepoint")}
    return None


def case_payload(path: Path) -> dict:
    cfg = srv.config()
    case = wb_mod.read_case(path)
    rnds = rounds_mod.build_rounds(case["sheets"], cfg["round_minutes"], cfg["interviewer"])
    progress = rounds_mod.load_progress(path)
    summary = summary_of(path, case, progress, rnds, cfg)
    wire = [dict(r, rows=[{"sheet": s, "row": n} for s, n in r["rows"]],
                 stops=[{"sheet": s, "row": n} for s, n in r["stops"]]) for r in rnds]
    # every round carries `on_sheet`, its place on its sheet, and each sheet its count of rounds:
    # the numbers he sees are the sheet's, while `number` stays the case-wide key of the records
    counts = rounds_mod.sheet_counts(rnds)
    return {
        "path": srv.rel_path(path),
        # the workbook's name, with a renamed case's new pseudonym where the file still carries the old
        "name": demo_title(path) if srv.is_demo(path) else shown_name(path),
        # the case by its label, as PETs names it, so the window's title is the case's and not the
        # workbook's, "Rowan - Experiential statements" beside "Rowan - PETs" (17 October, the third
        # Tauri build)
        "case": case_label(path),
        # the header carries a small tag beside the name while this one is open, so any recording
        # of the interface says on its face that it is not a participant
        "demo": srv.is_demo(path),
        "sheets": [{"name": s["name"], "rows": s["rows"], "rounds": counts.get(s["name"], 0)}
                   for s in case["sheets"]],
        "rounds": wire,
        "progress": summary,
        "last": progress.get("last"),
        "config": cfg,
        # the band over the columns and the Project category in Settings. A page that finds no
        # `project` here is in front of a server from before it, and says so
        "project": read_project(project_root(path)),
        # the participant's picture, label and pen portrait, beside the name in the bar (pbiobuild)
        "person": person_for_book(path),
        # whether the bug in the bar shows: only when the build carries the collector's address
        "feedback": bool(srv.feedback_url(cfg)),
    }


def refresh_summary(path: Path, sheets: list | None = None) -> dict:
    """The summary the page redraws from. Beside the case's figures it carries every sheet's,
    `sheetRounds` with the rounds done, left and the minutes left on each, and `sheetsDone` and
    `sheetsLeft` for the case, so the round-done card counts the sheet it closed a round on.
    `sheets`, from a save that has just written the workbook (`workbook.outline_of`), spares reading it again."""
    cfg = srv.config()
    case = {"sheets": sheets} if sheets is not None else wb_mod.read_case(path)
    rnds = rounds_mod.build_rounds(case["sheets"], cfg["round_minutes"], cfg["interviewer"])
    progress = rounds_mod.load_progress(path)
    return summary_of(path, case, progress, rnds, cfg)


def summary_of(path: Path, case: dict, progress: dict, rnds: list, cfg: dict) -> dict:
    """A case's summary as the page draws its bar from, and in a project of two or more timepoints
    each timepoint's sheets, counts and Statements complete mark beside it, `timepoints` (see
    `timepoints_view`). A project of one timepoint answers exactly what it always did."""
    summary = rounds_mod.summary(case["sheets"], progress, rnds, cfg["interviewer"], cfg["daily_target"])
    tps = timepoints_view(path, [s["name"] for s in case["sheets"]], progress, summary["states"])
    if tps is not None:
        summary["timepoints"] = tps
    return summary


# -------------------------------------------------------------- handlers

def recent_entries(cases: list[dict]) -> list[dict]:
    """The recent list as the page draws it: newest first, exactly as `remember` stored it.

    Each entry carries its display label, whatever the file holds, and the sheets of its workbook,
    taken from the listing when the listing has it and read the same way when it does not.
    """
    listed = {path_key(c["path"]): c for c in cases}
    out = []
    for r in srv.state().get("recent", []):
        path = srv.abs_path(r.get("path", ""))
        if not srv.within_root(path) or srv.is_demo(path):
            continue
        key = path_key(r.get("path", ""))
        if key in listed:
            sheets = listed[key]["sheets"]
            complete = listed[key].get("complete")
            pets = listed[key].get("pets_complete")
        else:
            read = read_sheets(path) if path.exists() else None
            sheets = read[1] if read else []
            complete = rounds_mod.complete_of(path) if path.exists() else None
            pets = themes_mod.pets_complete_of(path) if path.exists() else None
        out.append(dict(r, case=srv.display_case(r.get("case", "")), sheets=sheets, complete=complete,
                        pets_complete=pets))
    # the Current board's name, as the listing has it, or read the same way
    return [dict(r, board=listed[path_key(r.get("path", ""))].get("board") if path_key(r.get("path", "")) in listed
                 else themes_mod.chosen_name(srv.abs_path(r.get("path", "")))) for r in out]


def card_of(case: str, rows: list[dict], cfg: dict, held: dict, recent: list[dict], demo: bool = False) -> dict:
    """One participant's card on the home screen, from the case list's rows of that case.

    The case's workbook is its annotated one, and of two the one opened last, else the newest, the
    other under Files. With one, the card carries what its two halves say: the turns decided of
    the turns there and the statements' mark, then the Current board's name, the number of boards,
    the PETs mark and whether the GETs file holds the case. With none, `start` is the newest raw
    source, else the newest transcript in another shape, which Start experiential statements takes.
    `files` is every row of the case, its workbook first. Only reads."""
    order = {path_key(r.get("path", "")): -i for i, r in enumerate(recent)}
    books = [r for r in rows if r.get("kind") == "annotated"]
    pick = max(books, key=lambda r: (path_key(r["path"]) in order, order.get(path_key(r["path"]), 0),
                                     r.get("modified") or 0),
               default=None)
    card = {"case": case, "demo": demo, "path": None, "name": None, "sheets": [], "locked": False,
            "turns": None, "complete": None, "board": None, "boards": 0, "pets_complete": None,
            "in_gets": False, "start": None,
            "files": ([pick] if pick else []) + [r for r in rows if r is not pick]}
    if pick is None:
        newest = lambda kind: max((r for r in rows if r.get("kind") == kind),
                                  key=lambda r: r.get("modified") or 0, default=None)
        card["start"] = newest("raw") or newest("transcript")
        return card
    path = srv.abs_path(pick["path"])
    card.update(path=pick["path"], name=pick["name"], sheets=pick.get("sheets") or [],
                locked=bool(pick.get("locked")), turns=turns_of(path, cfg.get("interviewer") or ""),
                complete=pick.get("complete"), board=pick.get("board"), boards=boards_count(path),
                pets_complete=pick.get("pets_complete"),
                in_gets=bool(held) and themes_case(path) in held)
    # in a project of two or more timepoints, each one with where it stands (see `by_timepoint`),
    # and nothing new in a project of one
    tps = card_timepoints(path, cfg.get("interviewer") or "")
    if tps is not None:
        card["timepoints"] = tps
    return card


def card_order(case: str, folder: bool) -> tuple:
    """Case order, P2 before P10, a folder with no P-number by its name after them, and a workbook
    sitting in the root itself after those."""
    numbered = folder and bool(re.match(r"^P\d+\b", case))
    return (0 if numbered else 1 if folder else 2, gets_mod.case_order(case))


def participants(root: Path | None, cases: list[dict], recent: list[dict], cfg: dict | None = None) -> list[dict]:
    """A project's rows on the home screen, one per case folder under its root and one per workbook
    sitting in the root itself, named by its stem, in his order (see `in_his_order`). Built from
    the case list, and only reads. A settings dict for `root` stands for the first project, as a
    page from before the projects had it."""
    if isinstance(root, dict):
        cfg, roots = root, srv.project_roots(root)
        root = roots[0] if roots else None
    cfg = srv.config() if cfg is None else cfg
    if root is None or not Path(root).exists():
        return []
    root = Path(root)
    groups: dict[str, dict] = {}
    names = names_at(root)
    for row in cases:
        try:
            parts = srv.abs_path(row["path"]).resolve().relative_to(root.resolve()).parts
        except (ValueError, OSError):
            continue
        folder = len(parts) > 1
        name = label_for(root / parts[0], names) if folder else Path(parts[0]).stem
        groups.setdefault(parts[0], {"case": name, "folder": folder, "rows": []})["rows"].append(row)
    data = gets_file(root)
    held = data.get("cases") if isinstance((data or {}).get("cases"), dict) else {}
    cards = [dict(card_of(g["case"], g["rows"], cfg, held, recent), folder=g["folder"])
             for g in sorted(groups.values(), key=lambda g: card_order(g["case"], g["folder"]))]
    with_people(root, cards)
    return in_his_order(cards, order_of(project_file(root)))


def with_people(root: Path, cards: list[dict]) -> list[dict]:
    """Each row's participant's picture, label and pen portrait (pbiobuild), `person`, with their colour on the
    GETs board for the initial where there is no picture."""
    people = people_view(root)
    colours = people_colours(root, [c["case"] for c in cards])
    for card in cards:
        card["person"] = person_of(root, people, card["case"], colours.get(card["case"]))
    return cards


def in_his_order(cards: list[dict], order: list[str]) -> list[dict]:
    """The rows in the order he dragged them into, `order` in the project file: the cases it names
    first, in its order, then every case it does not name in case order, as `cards` come. A label
    in `order` with no case is passed over, and with no `order` the rows keep case order."""
    rank: dict[str, int] = {}
    for at, label in enumerate(order):
        rank.setdefault(label, at)
    named = sorted((card for card in cards if card["case"] in rank), key=lambda card: rank[card["case"]])
    return named + [card for card in cards if card["case"] not in rank]


def demo_cards(rows: list[dict], root: Path | None = None) -> list[dict]:
    """The demo's rows, Juno, Rowan and Mabel, each from its one row, as a project's are drawn, and
    always in this order, which is fixed, the IPA demo's or with `root` the thematic analysis demo's."""
    at = Path(root) if root is not None else srv.DEMO_DIR
    data = gets_file(at)
    held = data.get("cases") if isinstance((data or {}).get("cases"), dict) else {}
    cfg = srv.config()
    return with_people(at, [card_of(row["case"], [row], cfg, held, [], demo=True) for row in rows])


def project_section(root: Path, recent: list[dict], cfg: dict, cases: list[dict] | None = None) -> dict:
    """One project's section of the home screen: `id`, the project as the page names it back,
    `project`, its name and research question for the head, `cases`, its case list, `participants`,
    its rows in his order, and `gets`, its GETs card, or None with no case. A root that is not there
    has no rows, and `there` says so. `cases` is its case list when the caller has it already."""
    if cases is None:
        cases = list_cases(root) if root.exists() else []
    section = {"id": project_id(root), "project": read_project(root), "there": root.is_dir(), "cases": cases,
               "participants": participants(root, cases, recent, cfg),
               "gets": gets_head(root, cases) if root.exists() else None}
    # Working together's tags and lines under the question (wtowners), only in a project where it is on
    team = team_sync.status(root) if root.is_dir() else None
    if team is not None:
        section["team"] = team
    return section


def api_cases(_: dict) -> dict:
    """The home screen. `projects` is a section for each project, in the order they were added (see
    `project_section`), and the demo's rows come after them. `cases`, `recent`, `participants`,
    `gets`, `root` and `project` stay for a page from before the projects, and are the first
    project's, `cases` and `recent` every project's."""
    cfg = srv.config()
    roots = srv.project_roots(cfg)
    # Trajectories' old labels and pictures moved into the participants' own sets the first time (pbiobuild)
    for root in roots:
        people_settled(root)
    listed = [(root, list_cases(root) if root.exists() else []) for root in roots]
    cases = [row for _root, rows in listed for row in rows]
    recent = recent_entries(cases)
    sections = [project_section(root, recent, cfg, rows) for root, rows in listed]
    first = sections[0] if sections else None
    demos = demo_entries()
    ta_root = srv.demo_ta_dir()
    demos_ta = demo_entries(ta_root)
    # `root` is empty while there is no project, and `choose` says the Mac's folder dialog is there.
    # `demos` is the Demo section's rows, the three cases, and `demo` stays Juno's alone, for a page
    # from before the three. `demo_project` is the demo's own, for its head. `one` says this run is
    # of one project, named by --root, which adds and removes none. Sift's and Trace's sections, `reviews`
    # and `traces`, went with the cutover (the sixth build, 23 October 2026): each is its own app's Home
    return {"projects": sections, "cases": cases, "recent": recent, "config": cfg, "demo": demo_entry(),
            "demos": demos, "participants": first["participants"] if first else [],
            "demo_participants": demo_cards(demos), "demo_project": read_project(srv.DEMO_DIR),
            # the Demo projects section's second (demos, 3 November 2026): the thematic analysis demo, its rows,
            # cards and project as the IPA demo's three keys above give its own
            "demos_ta": demos_ta, "demo_ta_participants": demo_cards(demos_ta, ta_root),
            "demo_ta_project": read_project(ta_root) if demos_ta else None,
            "root": srv.rel_path(roots[0]) if roots else "", "project": read_project(roots[0] if roots else None),
            "feedback": bool(srv.feedback_url(cfg)), "choose": srv.PLATFORM == "darwin", "one": bool(srv.ROOT_OVERRIDE),
            "version": srv.VERSION, "build": srv.BUILD, "gets": first["gets"] if first else None}


def day_workbooks(cfg: dict) -> list[Path]:
    """Every annotated workbook under every project's root with a progress file beside it, found
    from the progress files themselves, so no workbook is opened. A progress file sits in its case's
    `Working/`, and one under `_Archive` or another folder the case list leaves out, or beside a
    backup copy, or with no workbook of its stem beside its folder, is passed over. A workbook two
    roots share is counted once."""
    found: list[Path] = []
    seen: set[str] = set()
    for root in srv.project_roots(cfg):
        if not root.exists():
            continue
        for side in sorted(root.rglob("*.progress.json")):
            folders = side.relative_to(root).parts[:-1]
            if not folders or folders[-1] != "Working" or set(folders[:-1]) & SKIP_DIRS:
                continue
            stem = side.name[: -len(".progress.json")]
            workbook = side.parent.parent / f"{stem}.xlsx"
            if BACKUP_STEM.search(stem) or not workbook.is_file() or str(workbook.resolve()) in seen or pristine_copy(workbook):
                continue
            seen.add(str(workbook.resolve()))
            found.append(workbook)
    return found


def api_days(_: dict) -> dict:
    """The rounds closed on each day across every case of every project, for the squares in the
    home screen's head, with today's date and the daily target the line under them counts by. It only
    reads: each progress file as it sits, and nothing is written."""
    cfg = srv.config()
    try:
        target = max(1, int(cfg.get("daily_target") or 2))
    except (TypeError, ValueError):
        target = 2
    return {"days": rounds_mod.days_total(day_workbooks(cfg)), "today": rounds_mod.today(),
            "dailyTarget": target}


def api_project(body: dict) -> dict:
    """A project, read, or saved from Settings when the body carries a name or a question.

    The project is the one `root` names by its id, else the one the workbook `path` belongs to, else
    the only one, the `--root` of a scratch run included (see `asked_root`). A save lands in that
    project's root and nowhere else. The demo's project is fixed: asked with a demo path this reads
    the demo's own file, and a save for the demo is refused with nothing written. `agents`, true or
    false, saves the privacy tick with its time (see `write_agents`), alone or beside the name and
    the question, and `pet_labels`, "letters" or "numbers", how the exports label its PETs, at once
    (see `write_labels`), and `timecodes`, 75:12, 1:15:12 or 01:15:12, how every timecode of the
    project is written, at once (see `write_timecodes`). `timepoints`, a list of `{"label", "description"}` or a number, sets the
    project's timepoints, refused while a timepoint it would take away holds an interview, and with
    `dry_run` says what would change and writes nothing (see `write_timepoints`). `statement_words`, a
    whole number of words, sets the length past which the length nudge speaks, with `dry_run` likewise
    (see `write_statement_words`). The name, the question, the labels, the timecodes and the tick take `dry_run` too
    (26 October, for the agents' `project set`), and their save answers `changes`, a line each (see
    `project_changes`). `method` is fixed once the project is made (tadraw): one sent that is not the
    project's own is refused with nothing written, its own changing nothing.
    """
    writes = ("name" in body or "research_question" in body or "agents" in body or "pet_labels" in body
              or "timecodes" in body or "timepoints" in body or "statement_words" in body)
    root = asked_root(body, write=writes or "method" in body)
    if "method" in body and root is not None and method_asked(body.get("method")) != method_of(project_file(root)):
        raise WorkbookError(i18n.t("method.refused_fixed", method=method_name(method_of(project_file(root)))))
    if not writes:
        return {"project": read_project(root)}
    if srv.is_demo_root(root):
        raise WorkbookError(i18n.t("server.demo_s_project_fixed"))
    if "statement_words" in body:
        if body.get("dry_run") is True:
            return write_statement_words(root, body.get("statement_words"), dry_run=True)
        with writing(root=root):
            return write_statement_words(root, body.get("statement_words"), who=hist_mod.asker(body))
    if "timepoints" in body:
        if body.get("dry_run") is True:
            return write_timepoints(root, body.get("timepoints"), dry_run=True)
        with writing(root=root):
            return write_timepoints(root, body.get("timepoints"), who=hist_mod.asker(body))
    dry = body.get("dry_run") is True
    with contextlib.nullcontext() if dry else writing(root=root):
        before = read_project(root)
        project = before
        if "name" in body or "research_question" in body:
            made = write_project(root, body.get("name", ""), body.get("research_question", ""), dry_run=dry)
            project = dict(project, name=made["name"], research_question=made["research_question"])
        if "agents" in body:
            project = (dict(project, agents=agents_of({"agents": {"allowed": body.get("agents") is True}}))
                       if dry else write_agents(root, body.get("agents") is True))
        if "pet_labels" in body:
            project = dict(project, pet_labels=write_labels(root, body.get("pet_labels"), dry_run=dry)["pet_labels"])
        if "timecodes" in body:
            project = dict(project, timecodes=write_timecodes(root, body.get("timecodes"), dry_run=dry)["timecodes"])
        if not dry:
            project = read_project(root)
            # the project's History, under the same lock (projhistory, 2 November 2026)
            hist_mod.record(root, "project set", project_changes(before, project), hist_mod.asker(body))
    return {"project": project, "changes": project_changes(before, project), "dry_run": dry}


# Write a guide for AI agents, in Project settings: `docs/agents.md` copied to `AGENTS.md` at
# the case root, where an agent in a conversation finds it, with this project filled in where the
# guide marks the place. The first line of the copy says the app wrote it, and a file without that
# line is his own and never written over.
AGENTS_GUIDE = boot.resource("docs/agents.md")
AGENTS_FILE = "AGENTS.md"
AGENTS_MARK = ("<!-- Written by Idiograph from docs/agents.md. Settings, Project, Write a guide for AI agents "
               "writes it again. -->")
AGENTS_PLACE = re.compile(r"<!-- project -->.*?<!-- /project -->", re.S)


def agents_project(root: Path) -> str:
    """This project in the words the guide's place for it takes: its name, its research question,
    and the participants a GET needs."""
    project = read_project(root)
    try:
        held = gets_mod.load(root)
    except WorkbookError:
        held = None
    books = gets_books(root)
    study = gets_mod.study_of(held, [b["case"] for b in books])
    inside = sum(1 for b in books if study[b["case"]]["in"])
    minimum, band = gets_mod.minimum_of(gets_mod.settings_of(held), inside)
    question = project["research_question"] or "none is set yet, so ask him for it before any analysis"
    said = "Smith's band for a study of that size" if band else "set in Settings"
    return (f"This project is {project['name']}. Its research question: {question}\n\n"
            f"A GET needs {minimum} of the "
            f"{inside} participants in the study, {said}.")


def agents_guide(root: Path) -> str:
    """The guide as `AGENTS.md` holds it: the app's mark, then `docs/agents.md` with this project
    in the place it marks."""
    text = AGENTS_GUIDE.read_text(encoding="utf-8")
    return AGENTS_MARK + "\n\n" + AGENTS_PLACE.sub(lambda _m: agents_project(root), text, count=1)


def api_agents_guide(body: dict) -> dict:
    """Write a guide for AI agents: `AGENTS.md` at the case root, from `docs/agents.md` with the
    project filled in (see `agents_guide`). A file there that the app did not write is his own and
    is never written over. One it wrote is written again only with `update`, which the page asks
    for on a second press. The demo's guide is the one that ships, and nothing is written for it."""
    root = asked_root(body, write=True)
    if root is None or not Path(root).is_dir():
        raise WorkbookError(i18n.t("server.project_folder_chosen_yet_nowhere"))
    if srv.is_demo_root(root):
        raise WorkbookError(i18n.t("server.demo_s_guide_ships_app"))
    target = Path(root) / AGENTS_FILE
    there = target.exists()
    if there:
        try:
            held = target.read_text(encoding="utf-8")
        except (OSError, ValueError):
            held = ""
        if not held.startswith(AGENTS_MARK):
            raise WorkbookError(i18n.t("server.agents_md_project_folder_own"))
        if not ticked(body.get("update"), False):
            return {"written": False, "ours": True, "said": i18n.t("server.agents_md_from_earlier_press")}
    with writing(root=root):
        tmp = target.with_name(target.name + ".tmp")
        tmp.write_text(agents_guide(Path(root)), encoding="utf-8", newline="\n")
        os.replace(tmp, target)
    return {"written": True, "updated": there, "file": AGENTS_FILE,
            "said": i18n.t("server.agents_md_updated") if there else i18n.t("server.agents_md_wrote")}


def root_setting(folder: Path) -> str:
    """A chosen folder as a project's `root` stores it: from the repo root when it sits inside the
    repo, and with any case folder in it written as a glob on its pseudonym, so no second name
    reaches the file."""
    parts = Path(srv.rel_path(Path(folder))).parts
    return str(Path(*[(m.group(1) + "*") if (m := srv.CASE_FOLDER.match(p)) else p for p in parts]))


def projects_view() -> dict:
    """Settings' Projects: every project in the order they were added, as `read_project` draws
    each, `choose`, whether the Mac's folder dialog is there, and `one`, whether this run is of one
    project, which adds and removes none."""
    return {"projects": [read_project(root) for root in srv.project_roots()], "choose": srv.PLATFORM == "darwin",
            "one": bool(srv.ROOT_OVERRIDE)}


def project_folder(folder, cfg: dict) -> Path:
    """The folder a project would be added from, resolved, once nothing refuses it: a folder that is
    not there, one added already, one inside another project's root or holding one, one holding
    the app or its demo, and any folder in a run of one project. `cfg` is the saved settings, never
    the --root override. Add project and New project both ask it, and it writes nothing."""
    if srv.ROOT_OVERRIDE:
        raise WorkbookError(i18n.t("server.run_one_project_named_root"))
    text = str(folder or "").strip()
    if not text:
        raise WorkbookError(i18n.t("server.name_folder_first"))
    chosen = srv.abs_path(text)
    if not chosen.is_dir():
        raise WorkbookError(i18n.t("server.folder_nothing_added"))
    chosen = chosen.resolve()                       # the real folder, past any symlink, /var to /private/var
    if srv.inside(chosen, srv.DEMO_DIR) or srv.inside(srv.DEMO_DIR, chosen) or srv.inside(srv.HERE, chosen):
        raise WorkbookError(i18n.t("server.folder_holds_app_demo_cannot"))
    for root in srv.project_roots(cfg):
        name = read_project(root)["name"]
        if srv.same_folder(chosen, root):
            raise WorkbookError(i18n.t("server.folder_project_already", name=name))
        if srv.inside(chosen, root):
            raise WorkbookError(i18n.t("server.folder_inside_project_already", name=name))
        if srv.inside(root, chosen):
            raise WorkbookError(i18n.t("server.folder_holds_project_already", name=name))
    return chosen


def add_project(folder) -> dict:
    """A new project from a folder, after the others in config.json's `projects`, every other
    setting as it was, answered as `read_project` reads it. The one way a project is added, which
    Add project and New project both call. A typed path that is not absolute is taken from the repo
    root, as a stored root is read. Refused, with nothing written, as `project_folder` says. Nothing
    is written in the folder itself."""
    with srv._lock:
        cfg = srv.merge_config(srv.saved_config())          # saved settings, never the --root override
        chosen = project_folder(folder, cfg)
        # only the list written, every other setting left in the file as it stands
        srv.write_config_keys({"projects": list(cfg["projects"]) + [{"root": root_setting(chosen)}]})
    return {"added": True, "project": read_project(chosen)}


# the page asking, by its id, while an approved held action runs from it (`api_holds`)
ASKING_PAGE = contextvars.ContextVar("asking_page", default="")


def remove_project(value, trash: bool = False, page: str = "", dry_run: bool = False, by: str = "") -> dict:
    """Remove from Idiograph: the project `value` names by its id taken out of config.json's
    `projects`, every other setting as it was. Its folder and every file in it stay exactly as they
    are, unless `trash`, his tick on Remove's card (removetrash, 10 November 2026), which moves the folder to the
    system's Trash first, never deletes it, once `srv.trash_guard` refuses nothing, `page` the asking page, which
    may be in front of it. A move the system refuses keeps the project in the list. `dry_run` says what it would
    do and does nothing. Each removal is a line in the app's own record (`srv.record_removal`), `by` who asked.
    The demo stays, and a run of one project removes none."""
    if srv.ROOT_OVERRIDE:
        raise WorkbookError(i18n.t("server.run_one_project_named_root"))
    root = srv.project_named(value)
    if srv.is_demo_root(root):
        raise WorkbookError(i18n.t("server.demo_stays_nothing_removed"))
    name = read_project(root)["name"]
    where = ""
    if trash:
        folder = srv.trash_guard(root, name, lambda at: srv.same_folder(srv.project_named(at), root),
                                 page or ASKING_PAGE.get())
        if dry_run:
            return {"removed": False, "dry_run": True, "name": name, "trash": True, "folder": str(folder),
                    "where": trash_mod.where()}
        where = srv.trash_move(folder, name)
    elif dry_run:
        return {"removed": False, "dry_run": True, "name": name, "trash": False, "folder": str(root)}
    with srv._lock:
        cfg = srv.merge_config(srv.saved_config())
        srv.write_config_keys({"projects": [entry for entry in cfg["projects"]
                                        if not srv.same_folder(srv.configured(entry["root"]) or Path(entry["root"]), root)]})
    srv.record_removal(name, root, bool(trash), by)
    return {"removed": True, "name": name, "trash": bool(trash), "folder": str(root), "where": where}


def api_projects(body: dict) -> dict:
    """Settings' Projects, with `op` of `read`, the default, `add` or `remove`. `add` takes the
    folder typed as `path`, or with none the Mac's folder dialog, whose Cancel adds nothing. `remove`
    takes `root`, the project's id. Each answers with every project afterwards (see
    `projects_view`)."""
    op = str(body.get("op") or "read")
    if op == "read":
        return projects_view()
    if op == "add":
        if str(body.get("path") or "").strip():
            folder = body["path"]
        else:
            if srv.PLATFORM != "darwin":
                raise WorkbookError(srv.NO_DIALOG)
            folder = srv.PICK_FOLDER()
            if folder is None:
                return dict(projects_view(), added=False)
        added = add_project(folder)
        return dict(projects_view(), **added)
    if op == "remove":
        # with `trash`, his tick on Remove's card, the folder goes to the system's Trash first (removetrash)
        removed = remove_project(body.get("root"), trash=body.get("trash") is True, page=str(body.get("page") or ""),
                                 dry_run=body.get("dry_run") is True)
        return dict(projects_view(), **removed)
    if op == "reveal":
        # Show in Finder, or Show in Explorer, on a project card's menu on Home (21 October)
        return show_project_folder(body.get("root"))
    raise WorkbookError(i18n.t("server.op_read_add_remove_reveal"))


def show_folder(folder: Path) -> None:
    """The folder shown in the Finder on a Mac, or in Explorer on Windows, selected in the folder it sits in."""
    if srv.PLATFORM == "darwin":
        REVEAL(folder)
    elif srv.PLATFORM.startswith("linux"):
        srv.show_in_folder(folder)
    else:
        subprocess.run(f'explorer /select,"{folder}"', check=False, timeout=15,
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


SHOW_FOLDER = show_folder        # a name here so the suite can stand in for it


def show_project_folder(value) -> dict:
    """Show in Finder on a project card's menu: the project's folder, named by its id, shown in the
    Finder on a Mac or in Explorer on Windows. Nothing is written. The demo's folder, one that is not
    there, and any other machine are refused in one line."""
    if srv.PLATFORM not in ("darwin", "win32") and not srv.PLATFORM.startswith("linux"):
        raise WorkbookError(i18n.t("server.show_finder_mac_windows_only"))
    root = srv.project_named(value)
    if srv.is_demo_root(root):
        raise WorkbookError(i18n.t("server.demo_ships_idiograph_folder_shown"))
    if not Path(root).is_dir():
        raise WorkbookError(i18n.t("server.folder_more"))
    SHOW_FOLDER(Path(root))
    return {"revealed": True, "name": read_project(root)["name"]}


# ------------------------------------------------------- send a project, open a sent one

# Share a copy, on a project card's menu on Home, and Open a shared copy under the cards (Adam's ruling
# of 20 October, topic 10, their words and place his ruling of 21 October, Way A): the whole project as one file, `<Project name>.idiograph`, opened on another
# Idiograph as a copy in a folder of its own (see `project_pack.py`). A browser downloads the file
# from SEND_PATH. Idiograph's own window asks for the path in its save dialog and the server writes
# the file there through /api/send-project, so a project with recordings never passes through the
# page (21 October). The page opens one through /api/open-sent. The command line's `project send` and `project open-copy` call the same.
SEND_PATH = "/project/send"


def into_prompt(folder: str) -> str:
    """The folder dialog's line once the shared copy is read, naming the new folder made inside the one
    chosen (Adam's drawing of 21 October)."""
    folder = str(folder or "").strip()
    return i18n.t("server.choose_folder_put_copy_new", folder=folder) if folder else i18n.t("server.choose_folder_put_copy")
SENT_MAX = 4 * 1024 * 1024 * 1024        # the most a sent file the page hands over may weigh


def send_root(value) -> Path:
    """The project Send names by its id, never the demo's, and one whose folder is there."""
    root = srv.project_named(value)
    if srv.is_demo_root(root):
        raise WorkbookError(i18n.t("server.demo_ships_idiograph_sent"))
    if not Path(root).is_dir():
        raise WorkbookError(i18n.t("server.folder_nothing_sent"))
    return Path(root)


def send_participants(root: Path) -> list[dict]:
    """Every participant of the project a chosen send picks from, each `{"folder", "label"}`, its case
    folder as a path from the root and its label as every screen shows it, in the project's order."""
    root = Path(root).resolve()
    seen, out = set(), []
    for row in list_cases(root):
        folder = wb_mod.case_folder(srv.abs_path(row["path"])).resolve()
        try:
            rel = folder.relative_to(root).as_posix()
        except ValueError:
            continue
        rel = "" if rel == "." else rel
        if rel in seen:
            continue
        seen.add(rel)
        out.append({"folder": rel, "label": row["case"]})
    return out


def send_named(every: list[dict], want: str) -> dict:
    """The participant of `every` a name means, by label, then by pseudonym, refused in one line for a
    name that is no participant's or names two."""
    low = want.lower()
    hits = [p for p in every if p["label"].lower() == low]
    if not hits:
        hits = [p for p in every if gets_mod.who(p["label"]).lower() == low]
    if not hits:
        raise WorkbookError(i18n.t("server.participant_project_nothing_sent", want=want))
    if len(hits) > 1:
        raise WorkbookError(i18n.t("server.names_many_nothing_sent", want=want, names=formats.list_words(p['label'] for p in hits)))
    return hits[0]


def send_names(values) -> list[str]:
    """Names as a send is given them, a list or one, each with its spaces made single."""
    if isinstance(values, str):
        values = [values]
    return [" ".join(str(n).split()) for n in (values or []) if str(n).strip()]


def send_boards(value) -> str:
    """A send's `boards`, `all` (every board, as before) or `current` (each board file with the board it
    is going with alone), refused in one line for any other word."""
    word = str(value or "all").strip().lower()
    if word not in pack_mod.BOARDS:
        raise WorkbookError(i18n.t("server.choice_boards_say_current_all", word=word))
    return word


def send_chosen(root: Path, participants=None, leave_out=None, with_kinds=None, blind: bool = False,
                pets=None, audio=None, skip: Path | None = None, boards=None) -> dict | None:
    """A chosen send's plan (`project_pack.choose`), or None when nothing was chosen and the whole
    project goes as it is. `participants` names some by label or pseudonym, none naming every one.
    `leave_out` and `with_kinds` name kinds, pets, gets and audio, and `blind` leaves the PETs and the
    GETs out. Recordings stay out of a chosen send unless asked for. `pets` and `audio` name the
    participants whose PETs or recordings go, each of them sent, every other one's staying (Adam's
    design E of 23 October, the Choose participants rows). `leave_out` naming the recordings alone,
    no participant and nothing else chosen, is the whole project less its recordings
    (`project_pack.whole_less_audio`), the Whole project choice. Refused in one line for a name that
    is no participant's, a kind both asked for and left out, or a participant's PETs or recordings
    asked for with them left out for everyone or asked for everyone. `boards` `current` sends each
    themes, LPETs, GETs and LGETs file with the board it is going with alone, and the progress files
    without their History (`project_pack.current_boards`), with nothing else chosen the whole project so."""
    board_choice = send_boards(boards)
    plan = send_chosen_plan(root, participants, leave_out, with_kinds, blind, pets, audio, skip, board_choice)
    if plan is None or board_choice == "all":
        return plan
    plan = pack_mod.current_boards(plan, root)
    plan["left"] = {k: [srv.display_path(rel) for rel in v] for k, v in plan["left"].items()}
    return plan


def send_chosen_plan(root, participants, leave_out, with_kinds, blind, pets, audio, skip, board_choice):
    """`send_chosen`'s plan with every board, its `left` on disk names for a current board's to add to.
    A send of the current board alone with nothing else chosen is the whole project."""
    named = send_names(participants)
    pets_named, audio_named = send_names(pets), send_names(audio)
    try:
        given_out = pack_mod.kinds_of(leave_out)
        out = given_out | ({"pets", "gets"} if blind else set())
        asked = pack_mod.kinds_of(with_kinds)
    except pack_mod.PackError as exc:
        raise WorkbookError(str(exc)) from None
    if not (named or out or asked or blind or pets_named or audio_named):
        if board_choice == "all":
            return None
        return pack_mod.whole_less_audio(root, send_participants(root), skip=skip, audio=True)
    every = send_participants(root)
    if out == {"audio"} and not (named or asked or blind or pets_named or audio_named):
        plan = pack_mod.whole_less_audio(root, every, skip=skip)
        if board_choice == "all":
            plan["left"] = {k: [srv.display_path(rel) for rel in v] for k, v in plan["left"].items()}
        return plan
    both = [k for k in pack_mod.KINDS if k in out and k in asked]
    if both:
        raise WorkbookError(i18n.t("server.both_asked_left_out_nothing", name=both[0]))
    for kind, some, said in (("pets", pets_named, "PETs"), ("audio", audio_named, "recordings")):
        if some and kind in out:
            raise WorkbookError(i18n.t("server.left_out_everyone_asked_nothing", said=said, name=some[0]))
        if some and kind in asked:
            raise WorkbookError(i18n.t("server.asked_everyone_nothing_sent", said=said, name=some[0]))
    # recordings, working notes and Source stay out of a chosen send unless asked for
    out |= {k for k in pack_mod.OPT_IN if k not in asked}
    chosen = {send_named(every, want)["folder"] for want in named}
    each = {}
    for kind, some in (("pets", pets_named), ("audio", audio_named)):
        if not some:
            continue
        folders = set()
        for want in some:
            hit = send_named(every, want)
            if named and hit["folder"] not in chosen:
                raise WorkbookError(i18n.t("server.among_participants_sent_nothing_sent", label=hit['label']))
            folders.add(hit["folder"])
        each[kind] = folders
    people = []
    for p in every:
        row = dict(p, send=(not named) or p["folder"] in chosen)
        if each:
            # this participant's own kinds: the PETs going only for those `pets` names, the recordings
            # only for those `audio` names
            mine = set(out)
            if "pets" in each and p["folder"] not in each["pets"]:
                mine.add("pets")
            if "audio" in each and p["folder"] in each["audio"]:
                mine.discard("audio")
            row["out"] = mine
        people.append(row)
    try:
        plan = pack_mod.choose(root, srv.PROJECT_FILE, people, bool(named), out, asked, skip=skip)
    except pack_mod.PackError as exc:
        raise WorkbookError(str(exc)) from None
    # what stays out named as every screen names a path, each case folder by its label alone
    if board_choice == "all":
        plan["left"] = {k: [srv.display_path(rel) for rel in v] for k, v in plan["left"].items()}
    return plan


def send_list(root: Path) -> dict:
    """What Share a copy's card draws itself from, read only and cheap enough to call as the card opens
    (`project_pack.inventory`): the project's name, each participant by label with whether it has PETs
    and recordings and their weight, and the whole project's recordings, weight and GETs. Each
    participant carries its `name` as the card shows it, and `lgets` says the project has two or more
    timepoints, so the card says LGETs as the app does."""
    root = Path(root)
    got = pack_mod.inventory(root, send_participants(root))
    for row in got["participants"]:
        row["name"] = gets_mod.who(row["label"])
    return dict(got, name=read_project(root)["name"], lgets=longitudinal(timepoints_of(project_file(root))))


# Share a copy's card on Home (23 October, Adam's design E): Whole project, with one tick for the audio
# recordings, or Choose participants, a row for each with its own PETs and recordings ticks, the
# statements and notes always going and the GETs never. The page sends `card` as the ticks stand and
# `card_options` turns it into a send's options, so the window's save and a browser's download send alike.
def card_options(card) -> dict:
    """Share a copy's card as a send's options. `{"whole": true, "audio": ...}` is the plain send, the
    whole project as it is, answered `{}`, or with `audio` false the whole project less its recordings.
    Otherwise `participants` are the labels ticked, `pets` and `audio` those whose PETs or recordings are
    ticked: a chosen send of those participants, the GETs left out, the PETs left out when no one's are
    ticked. No participant ticked is refused in one line."""
    card = card if isinstance(card, dict) else {}
    # `boards`, current or all, the board files with the board each is going with alone or every board
    boards = {"boards": "current"} if send_boards(card.get("boards")) == "current" else {}
    if card.get("whole") is True:
        return dict({} if card.get("audio") is not False else {"leave_out": ["audio"]}, **boards)
    named = send_names(card.get("participants"))
    if not named:
        raise WorkbookError(i18n.t("server.nothing_sent_tick_participant_first"))
    pets, audio = send_names(card.get("pets")), send_names(card.get("audio"))
    return dict({"participants": named, "pets": pets or None, "audio": audio or None,
                 "leave_out": ["gets"] if pets else ["pets", "gets"]}, **boards)


def send_project(root: Path, dest: Path | None = None, dry_run: bool = False, participants=None,
                 leave_out=None, with_kinds=None, blind: bool = False, pets=None, audio=None, boards=None) -> dict:
    """The project at `root` written as one file to `dest`, under the writers' lock so no save lands
    half way through, or with `dry_run` what it would write. Nothing in the project changes, so the
    root's file lock is taken only when a writer has made it already, never made for a send. With
    participants named or kinds chosen it is a chosen send (see `send_chosen`), whose dry run lists
    every file it would write and what stays out."""
    name = read_project(root)["name"]
    options = dict(participants=participants, leave_out=leave_out, with_kinds=with_kinds, blind=blind,
                   pets=pets, audio=audio, boards=boards)
    if dry_run or dest is None:
        chosen = send_chosen(root, **options)
        made = {"uid_made": not project_file(root).get(pack_mod.UID_KEY)}
        if chosen is None:
            return dict(pack_mod.plan_send(root, name), dry_run=True, **made)
        return dict(pack_mod.plan_chosen(name, chosen), dry_run=True, chosen=True, **made)
    # the project's own id, written at its first send, so a copy coming back is known as its own (26 October)
    uid_made = False
    if not project_file(root).get(pack_mod.UID_KEY):
        with srv._lock, locks.root(root):
            uid_made = bool(project_uid(root, make=True))
    held = locks.root(root) if locks.root_lock(root).exists() else contextlib.nullcontext()
    with srv._lock, held:
        chosen = send_chosen(root, skip=Path(dest).resolve(), **options)
        labels = chosen["participants"] if chosen is not None else None
        try:
            done = pack_mod.send(root, name, Path(dest), srv.VERSION, chosen=chosen,
                                 origin=send_origin(root, labels))
        except pack_mod.PackError as exc:
            raise WorkbookError(str(exc)) from None
    done = dict(done, uid_made=uid_made)
    if chosen is not None:
        done = dict(done, chosen=True, listed=[rel for _, rel in chosen["files"]], left=chosen["left"],
                    kinds_out=chosen["kinds_out"], participants=chosen["participants"], notes=chosen["notes"],
                    each=chosen.get("each", {}), whole=bool(chosen.get("whole")),
                    board_choice=chosen.get("board_choice", "all"), boards=chosen.get("boards", []))
    return done


def copy_refused(dest: Path, cfg: dict) -> str | None:
    """Why a copy may not be made at `dest`, as Open project folder refuses a folder, or None."""
    if srv.ROOT_OVERRIDE:
        return i18n.t("server.run_one_project_named_root")
    if srv.inside(dest, srv.DEMO_DIR) or srv.inside(dest, srv.HERE):
        return i18n.t("server.folder_holds_app_demo_copy")
    for root in srv.project_roots(cfg):
        if srv.inside(dest, root):
            return i18n.t("server.folder_inside_project_already", name=read_project(root)['name'])
    return None


def whose(name) -> str:
    """Another analyst's name as a board's or a copy's name says whose it is, Curt's, or Jess' for a
    name ending in s."""
    name = " ".join(str(name or "").split())
    if not name:
        return ""
    return f"{name}'" if name.lower().endswith("s") else f"{name}'s"


def copy_named(name: str, from_name: str = "") -> str:
    """A copy's name: the shared project's own, or with `from_name` saying whose copy it is, "Night
    swimming, Curt's copy", so a copy coming back opened alongside the project it came from is told
    from it by name (Adam, 23 October)."""
    who = whose(from_name)
    return f"{name}, {who} copy" if who else name


def open_copy(file: Path, into: Path, dry_run: bool = False, from_name: str = "") -> dict:
    """A sent project unpacked into a new folder in `into`, its own name or with "copy" after it, then
    added as a project after the others and answered as `read_project` reads it. With `dry_run` what
    it would write, and nothing written. A failure after the unpacking takes the folder away again.
    `from_name` names whose copy it is in the project's name (`copy_named`). `returning` names the
    project of his a copy coming back belongs to, whose boards `boards_in` can add to it instead."""
    try:
        plan = pack_mod.plan_open(Path(file), Path(into))
    except pack_mod.PackError as exc:
        raise WorkbookError(str(exc)) from None
    dest = Path(plan["folder"]).resolve().parent / plan["folder_name"]
    with srv._lock:
        cfg = srv.merge_config(srv.saved_config())
        refused = copy_refused(dest, cfg)
    if refused:
        raise WorkbookError(refused)
    # a copy coming back is named from the project it was a copy of, never "a copy's copy"
    try:
        origin = returned_from(Path(file)).get("copy_of") or {}
    except WorkbookError:
        origin = {}
    shown = copy_named(str(origin.get("name") or "") if from_name and origin.get("name") else plan["name"], from_name)
    back = returning_to(Path(file), [Path(r) for r in srv.project_roots(cfg)])
    extra = {"returning": read_project(back)["name"]} if back is not None else {}
    if dry_run:
        return dict({k: v for k, v in plan.items() if k not in ("statements", "copy_of", "boards")}, folder=str(dest),
                    dry_run=True, name=shown, **extra)
    # a folder of its own, not there until the unpacking renames it into place, so no other writer
    # touches it, and `add_project` takes the settings' lock itself
    try:
        done = pack_mod.unpack(Path(file), dest)
    except pack_mod.PackError as exc:
        raise WorkbookError(str(exc)) from None
    try:
        mark_copy(dest, plan["name"], plan, shown)
        added = add_project(dest)
    except Exception:
        shutil.rmtree(dest, ignore_errors=True)
        raise
    return dict(done, project=added["project"], added=True, name=shown, **extra)


def mark_copy(dest: Path, name: str, held: dict | None = None, shown: str = "") -> None:
    """The copy's project file told it is a copy, `copy_of` with the shared project's name and when it
    was opened, every other key as it came, so its card and page carry a "copy" tag (21 October). It is
    the copy's own new folder, not yet a project, so no other writer is there. Since 26 October `copy_of`
    keeps, from `held`, the sent file as `project_pack.read_sent` reads it, the shared project's id, when
    it was sent, from which Idiograph, and the print of each statement sent, so a file sent back from
    the copy names the project it came from, and since 8 November the places print of each board sent. The id
    the project file came with is that project's, so the
    copy takes its own at its own first send. `shown` is the copy's name when it is not the project's."""
    held = held or {}
    data = project_file(dest)
    own = str(data.pop(pack_mod.UID_KEY, "") or "")
    copy_of = {"name": str(name or ""), "opened": datetime.now().astimezone().isoformat(timespec="seconds")}
    uid = str(held.get("uid") or "") or own
    if uid:
        copy_of["uid"] = uid
    for key in ("sent", "version"):
        if held.get(key):
            copy_of[key] = str(held[key])
    if held.get("statements"):
        copy_of["statements"] = held["statements"]
    if held.get("boards"):
        # each board as it was sent, by where it put its cards, so one sent back untouched is the sender's own
        copy_of["boards"] = held["boards"]
    data["copy_of"] = copy_of
    if shown and shown != name:
        data["name"] = shown
    srv.save_json(Path(dest) / srv.PROJECT_FILE, data)


# ------------------------------------------------- a shared copy coming back

# Adam's ruling of 23 October: a copy he sent, a second analyst's PETs made in it and sent back, is
# "conceptually the same project", so its boards are offered as additions to the participant's boards,
# never replacing any, each the next board, not current, named whose and when. `boards_in` is the one
# op, the command line's `project boards-in`, MCP's `project_boards_in` and /api/boards-in. Opening the
# copy as a project of its own beside his stays open_copy.

def project_uid(root: Path, make: bool = False) -> str:
    """The project's own id from its project file, and with `make` written there first when it has none,
    every other key kept. The caller holds the project's lock."""
    data = project_file(root)
    uid = str(data.get(pack_mod.UID_KEY) or "")
    if not uid and make:
        uid = pack_mod.new_uid()
        data[pack_mod.UID_KEY] = uid
        srv.save_json(Path(root) / srv.PROJECT_FILE, data)
    return uid


def participant_books(root: Path) -> list[dict]:
    """Every participant of the project with an annotated workbook, each `{"folder", "label", "workbook"}`,
    the folder from the root, as `send_participants` reads them."""
    root = Path(root).resolve()
    seen, out = set(), []
    for row in list_cases(root):
        if row.get("kind") != "annotated":
            continue
        book = srv.abs_path(row["path"])
        folder = wb_mod.case_folder(book).resolve()
        try:
            rel = folder.relative_to(root).as_posix()
        except ValueError:
            continue
        rel = "" if rel == "." else rel
        if rel in seen:
            continue
        seen.add(rel)
        out.append({"folder": rel, "label": row["case"], "workbook": Path(book)})
    return out


def live_statements(book: Path, timepoints: int) -> dict:
    """A participant's statements now, each key with its words, every timepoint's together, keys being
    their sheet's own. A workbook that cannot be read gives none."""
    out = {}
    for n in range(1, max(1, timepoints) + 1):
        try:
            with themes_mod.scoped(n):
                cards = themes_mod.read_cards(book)["cards"]
        except (WorkbookError, OSError, ValueError):
            return out
        out.update({c["key"]: themes_mod.words(c["text"]) for c in cards})
    return out


def sent_places(book: Path, timepoints: int) -> list[str]:
    """The places print of every PETs board a participant has, every timepoint's together, in the order the
    files hold them (`themes.places_print`). A board file that cannot be read gives none of its boards."""
    out = []
    for n in range(1, max(1, timepoints) + 1):
        try:
            with themes_mod.scoped(n):
                data = themes_mod.load(book) or {}
        except (WorkbookError, OSError, ValueError):
            continue
        for b in themes_mod.boards_of(data):
            mark = themes_mod.places_print(b)
            if mark not in out:
                out.append(mark)
    return out


def send_origin(root: Path, labels=None) -> dict:
    """What a sent file says of where it comes from (`project_pack.ORIGIN_KEYS`): the project's id, the
    print of each statement of the participants sent, `labels`, or every one for None, from a copy the
    project it was opened from (`project_pack.COPY_KEYS`), and the sender's name, Settings' Your name, when
    it is set (copyback, 6 November 2026), never the Interviewer's, who may be the other analyst's. Since
    8 November `boards`, the places print of every PETs board of each participant sent (`sent_places`), so a
    board coming back untouched is told as the sender's own as he sent it (copyback2)."""
    data = project_file(root)
    tps = len(timepoints_of(data))
    prints, places = {}, {}
    for p in participant_books(root):
        if labels is not None and p["label"] not in labels:
            continue
        said = live_statements(p["workbook"], tps)
        if said:
            prints[p["label"]] = {k: pack_mod.statement_print(t) for k, t in said.items()}
        held = sent_places(p["workbook"], tps)
        if held:
            places[p["label"]] = held
    out = {"uid": str(data.get(pack_mod.UID_KEY) or ""), "statements": prints, "boards": places,
           "from": " ".join(str(srv.config().get("your_name") or "").split())}
    held = data.get("copy_of")
    if isinstance(held, dict):
        out["copy_of"] = {k: str(held[k]) for k in pack_mod.COPY_KEYS if held.get(k)}
    return out


def returned_from(file: Path) -> dict:
    """What a sent file says of the project it came back to: the file as `read_sent` reads it, and
    `copy_of`, the project the copy it was sent from was opened from, with the print of each statement
    as it was sent to that copy, from the copy's project file in the file, else from the file's list."""
    try:
        held = pack_mod.read_sent(Path(file))
    except pack_mod.PackError as exc:
        raise WorkbookError(str(exc)) from None
    proj = pack_mod.sent_json(Path(file), srv.PROJECT_FILE) or {}
    copy_of = proj.get("copy_of") if isinstance(proj.get("copy_of"), dict) else None
    return dict(held, copy_of=copy_of or held.get("copy_of") or {})


def came_back_to(root: Path, back: dict, file_name: str) -> tuple[str | None, str]:
    """Why a copy coming back is not this project's, in one line, or None, with how it was matched:
    `id`, by the project's own id, or `name`, by the project's name alone for a file from an Idiograph
    before the ids, 0.9.5 and earlier, which never sent one."""
    project = read_project(root)["name"]
    mine = str(project_file(root).get(pack_mod.UID_KEY) or "")
    copy_of = back.get("copy_of") or {}
    origin = str(copy_of.get("uid") or "")
    away = i18n.t("server.open_shared_copy_opens_project")
    if not copy_of:
        if back.get("uid") and back["uid"] == mine:
            return (i18n.t("server.sent_copy_coming_back_nothing", file_name=file_name, project=project), "")
        return (f"{file_name} was not sent from a copy of {project}, so nothing was brought in. {away}", "")
    if origin:
        if origin == mine:
            return None, "id"
        other = str(copy_of.get("name") or "another project")
        what = f"another project called {other}" if other.lower() == project.lower() else other
        return (f"{file_name} was sent from a copy of {what}, not of {project}, so nothing was brought in. {away}", "")
    if " ".join(str(copy_of.get("name") or "").split()).lower() == project.lower():
        return None, "name"
    return (f"{file_name} was sent from a copy of {copy_of.get('name') or 'another project'}, not of {project}, "
            f"so nothing was brought in. {away}", "")


def returning_to(file: Path, roots: list[Path]) -> Path | None:
    """The one project of `roots` a copy coming back belongs to, by its id, else by its name alone, or
    None when it belongs to none of them or the file cannot be read."""
    try:
        back = returned_from(file)
    except WorkbookError:
        return None
    by = {"id": [], "name": []}
    for root in roots:
        if not Path(root).is_dir() or srv.is_demo_root(root):
            continue
        why, how = came_back_to(Path(root), back, Path(file).name)
        if why is None:
            by[how].append(Path(root))
    hits = by["id"] or by["name"]
    return hits[0] if len(hits) == 1 else None


def day_said(iso: str) -> str:
    """A day as a board's name says it, 30 Oct, today for a time that cannot be read."""
    try:
        when = datetime.fromisoformat(str(iso))
    except (TypeError, ValueError):
        when = datetime.now()
    return f"{when.day} {when:%b}"


def unmatched_reason(key: str, texts, linked: bool, sent: dict, who: str) -> tuple[str, str]:
    """Why a card of a board coming back does not read as the project's statement, and its kind. Linked
    to the project's statement by its key: `edited`, a statement edited in the project since the copy was
    sent, `own`, one the other analyst edited or merged in the copy, or for a file with no prints, from an
    Idiograph before them, `differs`. Placed in the copy's wording: `gone`, one no longer in the project,
    `own`, the other analyst's own added in the copy, or with no prints `missing`. `texts` is the card's
    words as the board keeps them and as the copy read them, and `sent` the print of each statement sent
    to the copy."""
    if sent:
        held = sent.get(key)
        if linked:
            if held and held in {pack_mod.statement_print(t) for t in texts if t}:
                return "edited", i18n.t("server.edited_project_since_copy_sent")
            return "own", i18n.t("server.own_statement_edited_merged_added", who=who)
        if held:
            return "gone", i18n.t("server.longer_project")
        return "own", i18n.t("server.own_statement_edited_merged_added", who=who)
    if linked:
        return "differs", i18n.t("server.reads_differently_project")
    return "missing", i18n.t("server.project")


def came_counts(said: dict) -> dict:
    """How a board's cards came in, from `board_coming`'s answer (copyback2, 8 November 2026): `statements`, every
    card, `as_sent`, those that read as the copy was sent, `reworded`, his statements reworded since, linked and
    in his wording now, `removed`, his statements removed since, placed in the copy's wording, and `own`, the other
    analyst's own, reworded, merged or added in the copy."""
    out = {"statements": said["statements"], "as_sent": said["matched"], "reworded": 0, "removed": 0, "own": 0}
    for s in said["not_matched"]:
        out["own" if s.get("kind") == "own" else "reworded" if s.get("wording") == "yours" else "removed"] += 1
    return out


def board_in_note(whose_said: str, day: str, counts: dict,
                  team: bool = False) -> str:
    """A board brought in's note (copyback2, 8 November 2026, Adam's wording 2): whose copy it came from and when
    it was sent, then how its statements came, "Curt's copy, sent 6 Nov: 63 statements as sent, 37 reworded
    since, 5 removed since." A clause whose count is 0 is left out, each count in its form. Every card keeps its
    place, so the note says only how each came. `team`, so a board a
    teammate sent says "Curt's board, sent 9 Nov: ..." (team_board.py, wtboard)."""
    parts = []
    if counts["as_sent"]:
        parts.append(i18n.t("server.board_in_note_as_sent", n=counts["as_sent"]))
    if counts["reworded"]:
        parts.append(i18n.t("server.board_in_note_reworded", n=counts["reworded"]))
    if counts["removed"]:
        parts.append(i18n.t("server.board_in_note_removed", n=counts["removed"]))
    if counts["own"]:
        parts.append(i18n.t("server.board_in_note_own", n=counts["own"], whose=whose_said))
    if not parts:
        return (i18n.t("team_board.note_head", whose=whose_said, day=day) if team
                else i18n.t("server.board_in_note_head", whose=whose_said, day=day))
    said = ", ".join(parts)
    return (i18n.t("team_board.note", whose=whose_said, day=day, list=said) if team
            else i18n.t("server.board_in_note", whose=whose_said, day=day, list=said))


def board_coming(board: dict, cards: list[dict], quotes: dict, sent: dict, who: str) -> tuple[dict, dict]:
    """A board of the copy as it would come in, and how each card was matched (copyback, Adam, 6 November
    2026: a board arrives whole). Every card keeps its place, in its PET, its stack, the bin or Not placed,
    as the board puts it, and is matched to the project's statements, `cards` as `read_cards` reads them:
    1. by its words: the statement at its key reads as the card, as the board keeps it or as the copy read
       it, else an unclaimed statement with the same words, on its own row first, then on its sheet, takes
       it, so a statement moved by a removal before it in its passage is found (`themes.follow`);
    2. by its key: else its key still holds a statement no other card took by its words, and the card is
       linked to it, showing the project's wording as it reads now, the copy's kept as the words the card
       was made with;
    3. else it is placed in the copy's wording, a statement no longer in the project: its key is gone, or
       holds a statement another card took by its words, so the card moves past every line of its row.
    With `sent`, the print of each statement as the copy was sent, a card whose key held no statement then
    is the other analyst's own, added in the copy, and takes a statement by its words alone. The board
    keeps its sticky notes and loses its review, its revise thread and an agent's marks, which were the
    copy's. `quotes` are the quotes as `read_cards` reads them, so the PETs' picks follow their words."""
    v = themes_mod.normalise(board)
    for key in themes_mod.AGENT_KEYS + ("review", "revise", themes_mod.ORIGIN):
        v.pop(key, None)
    raw = {c["key"]: str(c["text"]) for c in cards}
    live = {k: themes_mod.words(t) for k, t in raw.items()}
    # each card's words as the board keeps them and as the copy last read them, the copy's own wording
    texts, theirs = {}, {}
    for key, card in v["cards"].items():
        texts[key] = [themes_mod.words(card.get("text")), themes_mod.words(card.get("live"))]
        theirs[key] = str(card.get("live") or card.get("text") or "")
        if card.get("live") and live.get(key) == themes_mod.words(card["live"]):
            # the copy read the line as the project does now, so the card follows that reading
            card["text"] = card.pop("live")
    own = {k for k in v["cards"] if sent and k not in sent}
    moved = {}
    v = themes_mod.follow(v, cards, quotes, keys=moved, own=own)
    matched, by_key, out, kinds = 0, 0, [], {}
    for key in texts:
        to = moved.get(key, key)
        card = v["cards"].get(to)
        if card is None:
            continue
        if to in live and live[to] == themes_mod.words(card["text"]):
            matched += 1
            continue
        linked = to in live
        kind, reason = unmatched_reason(key, texts[key], linked, sent, who)
        kinds[kind] = kinds.get(kind, 0) + 1
        said = {"key": key, "to": to, "text": themes_mod.words(theirs[key]), "reason": reason, "kind": kind,
                "wording": "yours" if linked else "copy"}
        if linked:
            # the card shows the project's statement as it reads now, the copy's wording kept as its text
            by_key += 1
            card["text"], card["live"] = theirs[key], raw[to]
            said["now"] = live[to]
        else:
            card["text"] = theirs[key]
            card.pop("live", None)
        out.append(said)
    v = themes_mod.normalise(v, live=themes_mod.quote_keys(quotes))
    return v, {"statements": len(v["cards"]), "matched": matched, "by_key": by_key,
               "copy_words": len(out) - by_key, "kinds": kinds, "not_matched": out}


def sent_places_of(back: dict, label: str) -> set:
    """The places print of each board a participant had when the copy was sent, as the copy kept them, by
    the participant's label, none for a copy sent before 8 November 2026, which kept none (copyback2)."""
    held = ((back.get("copy_of") or {}).get("boards") or {}).get(label)
    return {str(x) for x in held} if isinstance(held, list) else set()


def his_places(sent: set, data: dict) -> set:
    """The places prints a board coming back is his own by (copyback2, after a tester's copy of 6 November 2026,
    where his own board, sent and sent back untouched, came in as the tester's once he had reworded it): every
    board he had when the copy was sent, `sent`, and every board of his now and every revision in their History,
    so a board as he sent it is found whatever he has done to his own since, in a copy that kept no prints too.
    A board brought in from a copy is the other analyst's, never his own."""
    out = set(sent)
    for b in themes_mod.boards_of(data):
        if themes_mod.origin_of(b.get(themes_mod.ORIGIN)):
            continue
        out.add(themes_mod.places_print(b))
        for r in themes_mod.history_of(b):
            if isinstance(r.get("state"), dict):
                out.add(themes_mod.places_print(r["state"]))
    return out


def said_board(b: dict) -> dict:
    """A board coming in as `boards_in` answers it, without the board itself, `came` saying how its cards came."""
    out = {k: b[k] for k in ("from", "name", "statements", "matched", "by_key", "copy_words", "kinds", "not_matched",
                             "as_sent") if k in b}
    out["came"] = came_counts(b)
    return out | ({"id": b["id"]} if b.get("id") else {})


def boards_chosen(boards) -> tuple[set, set]:
    """The boards of a copy coming back chosen, as `boards_in` takes them: each a name, that board of any
    participant, or `{"participant", "board", "timepoint"}`, that participant's board alone, at that timepoint
    alone when one is given, by its number or its label, as Open a shared copy's card ticks them (copyback, 6
    November 2026, the timepoint since copyback2, 8 November, where a board of the same name at another timepoint
    came in unticked). Answers the names and the choices, each `(participant, board, timepoint)`, lowercase, the
    timepoint "" for any."""
    names, pairs = set(), set()
    for b in ([boards] if isinstance(boards, (str, dict)) else boards or []):
        if isinstance(b, dict):
            who, name, at = (" ".join(str(b.get(k) or "").split()).lower() for k in ("participant", "board", "timepoint"))
            if who and name:
                pairs.add((who, name, at))
        elif str(b or "").strip():
            names.add(" ".join(str(b).split()).lower())
    return names, pairs


def timepoint_is(asked: str, n: int, tps: list) -> bool:
    """Whether a timepoint asked for, "" for any, its number, T2, or its label, is timepoint `n` of `tps`."""
    if not asked:
        return True
    said = {str(n), f"t{n}"}
    if 0 < n <= len(tps):
        said.add(" ".join(str(tps[n - 1].get("label") or "").split()).lower())
    return asked in said


def boards_in(root: Path, file: Path, from_name: str = "", participants=None, boards=None,
              dry_run: bool = False, request: str = "") -> dict:
    """A shared copy coming back: its PETs boards added to the boards of the same participants in the
    project at `root`, each the next board, not current, not on the canvas, named whose and when, "Curt's
    board, 30 Oct", or "Curt's Board 2, 30 Oct" when a participant has several in the copy, with a note and
    an `origin` saying where it came from and a revision in its History, "Brought in from <file>". Every
    card comes in where the copy's board puts it, matched by its words, then by its key (`board_coming`).
    A board the project holds already, the same in every card, is left. Nothing else is written: no
    statement, note, setting or other board. `participants` and `boards` choose some (`boards_chosen`).
    `from_name`, whose copy it is, is the name the file carries when it is not given, its sender's own
    (`from`, since 6 November 2026). A file not sent from a copy of this project, or a participant the
    project does not have, is refused in one line. With `dry_run` nothing is written."""
    root, file = Path(root), Path(file)
    if srv.is_demo_root(root):
        raise WorkbookError(i18n.t("server.demo_s_project_fixed"))
    back = returned_from(file)
    why, how = came_back_to(root, back, file.name)
    if why:
        raise WorkbookError(why)
    sender = " ".join(str(back.get("from") or "").split())
    who_name = " ".join(str(from_name or "").split()) or sender
    if not who_name and not dry_run:
        raise WorkbookError(i18n.t("server.say_whose_copy_each_board"))
    who = whose(who_name) or "The other analyst's"
    project = read_project(root)["name"]
    tps = timepoints_of(project_file(root))
    every = participant_books(root)
    found = {}
    for entry in pack_mod.sent_boards(file):
        if themes_mod.boards_of(themes_mod.migrate(entry["data"])):
            found.setdefault(entry["folder"], []).append(entry)
    named = send_names(participants)
    wanted_names, wanted_pairs = boards_chosen(boards)
    rows, strangers = [], []
    for folder, entries in found.items():
        label = srv.display_case(PurePosixPath(folder).name) if folder else back["name"]
        hit = next((p for p in every if p["label"].lower() == label.lower()), None) or next(
            (p for p in every if gets_mod.who(p["label"]).lower() == gets_mod.who(label).lower()), None)
        if named and not any(n.lower() in (label.lower(), gets_mod.who(label).lower()) for n in named):
            continue
        if hit is None:
            strangers.append(label)
            continue
        rows.append((label, hit, entries))
    for n in named:
        if not any(n.lower() in (lab.lower(), gets_mod.who(lab).lower()) for lab, _, _ in rows) and n not in strangers:
            raise WorkbookError(i18n.t("server.copy_holds_boards_nothing_brought", n=n))
    if strangers:
        raise WorkbookError(i18n.t("server.strangers_not_in_project", n=len(strangers), names=formats.list_words(strangers),
                                   project=project))
    # a thematic analysis project's codes the copy's list holds that the project's lacks come in too (codes)
    codes_back = []
    if read_project(root).get("method") == "ta":
        with writing(root=None if dry_run else root):
            codes_back = codes_mod.came_back(root, pack_mod.sent_codes(file), themes_mod.now_iso(), dry_run=dry_run,
                                             who=who_name)
    if not rows and codes_back:
        return {"file": file.name, "project": project, "matched_by": how, "sent": str(back.get("sent") or ""),
                "version": str(back.get("version") or ""), "who": who_name, "sender": sender, "participants": [],
                "codes": codes_back, "dry_run": bool(dry_run)}
    if not rows:
        raise WorkbookError(i18n.t("server.holds_boards_participant_nothing_brought", name=file.name, project=project))
    sent_day = day_said(back.get("sent") or "")
    prints = (back.get("copy_of") or {}).get("statements") or {}
    when = datetime.now().astimezone().isoformat(timespec="seconds")
    plans = []
    for label, p, entries in rows:
        book = p["workbook"]
        every_board = [(e, b) for e in entries for b in themes_mod.boards_of(themes_mod.migrate(e["data"]))]
        # the participant as the copy names it and as the project does, so a choice the card sends by the
        # project's label finds the boards the dry run listed by the pseudonym alone (copyback2)
        whom = {x.lower() for x in (label, gets_mod.who(label), p["label"], gets_mod.who(p["label"]))}

        def named(e, b) -> bool:
            name = " ".join(str(b.get("name") or "").split()).lower()
            return name in wanted_names or any(w in whom and n == name and timepoint_is(at, e["timepoint"], tps)
                                               for w, n, at in wanted_pairs)

        def wanted(e, b) -> bool:
            return (not wanted_names and not wanted_pairs) or named(e, b)
        held_all = [(e, b) for e, b in every_board if wanted(e, b)]
        # named by the copy's boards, every one, so a board chosen alone is called as it is among the rest
        several = len(every_board) > 1
        for entry in entries:
            n = entry["timepoint"]
            if n > len(tps):
                raise WorkbookError(i18n.t("server.s_boards_copy_t_which", label=label, n=n, project=project))
            with themes_mod.scoped(n):
                read = themes_mod.read_cards(book)
                data = themes_mod.load(book) or {}
            have = {themes_mod.state_hash(themes_mod.board_state(b)) for b in themes_mod.boards_of(data)}
            # and a board brought in from this copy before, by where it came from
            came = {(o.get("file"), o.get("board"), o.get("sent")) for o in
                    (themes_mod.origin_of(b.get(themes_mod.ORIGIN)) for b in themes_mod.boards_of(data)) if o}
            sent = prints.get(label) or {}
            mine = his_places(sent_places_of(back, label), data)
            row = {"case": p["label"], "timepoint": n, "timepoint_label": tps[n - 1]["label"] if len(tps) > 1 else "",
                   "boards": [], "already": [], "as_sent": [], "book": book, "data": data, "read": read}
            for b in [b for e, b in held_all if e is entry]:
                old = " ".join(str(b.get("name") or "").split()) or themes_mod.FIRST_NAME
                if (themes_mod.state_hash(themes_mod.board_state(b)) in have
                        or (file.name, old, " ".join(str(back.get("sent") or "").split()) or None) in came):
                    row["already"].append(old)
                    continue
                # his own board as he sent it, untouched in the copy, stays out unless asked for by its name
                own_board = themes_mod.places_print(b) in mine
                v, said = board_coming(b, read["cards"], read["quotes"], sent, who)
                name = f"{who} {old}, {sent_day}" if several else f"{who} board, {sent_day}"
                # the note (copyback2, 8 November 2026): whose copy and when it was sent, and how its statements
                # came, the file's name kept in the board's origin and its History's revision, then on the next
                # line the copy's own note as it was, the other analyst's work, never dropped
                own_note = str(b.get("note") or "").strip()
                v["note"] = board_in_note(who, sent_day, came_counts(said)) + (f"\n{own_note}" if own_note else "")
                v[themes_mod.ORIGIN] = {"file": file.name, "who": who_name or "", "board": old,
                                        "sent": str(back.get("sent") or ""), "at": when,
                                        "request": " ".join(str(request or "").split())}
                coming = {"from": old, "name": name, "board": v, **said}
                if own_board:
                    coming["as_sent"] = True
                (row["boards"] if not own_board or named(entry, b) else row["as_sent"]).append(coming)
            if row["boards"] or row["already"] or row["as_sent"]:
                plans.append(row)
    if not any(r["boards"] or r["already"] or r["as_sent"] for r in plans):
        raise WorkbookError(i18n.t("server.board_copy_one_asked_nothing"))
    for row in plans:
        # each name kept clear of the boards there and of the ones before it, the sender's own as sent last
        taken = list(themes_mod.boards_of(row["data"]))
        for b in row["boards"] + row["as_sent"]:
            b["name"] = themes_mod._free_name(taken, b["name"])
            taken.append({"name": b["name"]})
    if not dry_run:
        for row in plans:
            if not row["boards"]:
                continue
            book = row["book"]
            with wb_mod.case_held(book), themes_mod.scoped(row["timepoint"]):
                data = themes_mod.load(book) or {}
                versions = themes_mod.boards_of(data)
                if not versions:
                    # a participant with no board yet is given the first board an open offers, which stays on
                    # the canvas, so what comes in is never current
                    versions = [themes_mod.blank_version(row["read"]["cards"], when)]
                ids = [str(v.get("id")) for v in versions]
                current = str(data.get("current")) if str(data.get("current")) in ids else ids[0]
                for b in row["boards"]:
                    v = b["board"]
                    v.update(id=themes_mod._next_id(versions), name=themes_mod._free_name(versions, b["name"]),
                             created=when, updated=when)
                    v.pop("history", None)
                    themes_mod.add_revision(v, name=themes_mod.revision_name("brought_in", file=file.name), at=when)
                    versions.append(v)
                    b["id"], b["name"] = v["id"], v["name"]
                themes_mod.write(book, themes_mod._file(book, case_label(book), data, versions, current, when))
    out = []
    for row in plans:
        # `path`, the workbook as the page opens it, so Open a shared copy's card lands on the PETs board
        out.append({"case": row["case"], "timepoint": row["timepoint"], "timepoint_label": row["timepoint_label"],
                    "path": srv.rel_path(row["book"]), "already": row["already"],
                    "boards": [said_board(b) for b in row["boards"]], "as_sent": [said_board(b) for b in row["as_sent"]]})
    return {"file": file.name, "project": project, "matched_by": how, "sent": str(back.get("sent") or ""),
            "version": str(back.get("version") or ""), "who": who_name, "sender": sender, "participants": out,
            "codes": codes_back, "dry_run": bool(dry_run)}


def sent_upload(body: dict) -> Path | None:
    """A shared file a browser's file chooser read, `data`, its contents in base64, written to a folder of
    its own in the temporary folder under `name`, the file's own name, so a board brought in from it
    names the file as he chose it. None when the body holds no `data`. The caller takes the folder away."""
    raw = str(body.get("data") or "").strip()
    if not raw:
        return None
    if len(raw) * 3 // 4 > SENT_MAX:
        raise WorkbookError(i18n.t("server.file_too_large_open_here"))
    try:
        data = base64.b64decode(raw, validate=True)
    except (binascii.Error, ValueError):
        raise WorkbookError(pack_mod.BROKEN) from None
    name = PurePosixPath(str(body.get("name") or "").replace("\\", "/")).name.strip()
    if not name or name.startswith("."):
        name = "Shared copy" + pack_mod.SUFFIX
    if not name.lower().endswith(pack_mod.SUFFIX):
        name += pack_mod.SUFFIX
    file = Path(tempfile.mkdtemp(prefix="idiograph-sent-")) / name
    file.write_bytes(data)
    return file


def returning_said(file: Path) -> dict:
    """The project of his a shared copy coming back belongs to, `{"root", "name"}`, the root as the page
    names a project, or none, for Open a shared copy's card (Adam's option A, 26 October)."""
    back = returning_to(Path(file), [Path(r) for r in srv.project_roots()])
    if back is None:
        return {}
    return {"returning": {"root": project_id(back), "name": read_project(back)["name"]}}


def api_open_sent(body: dict) -> dict:
    """Open a shared copy on Home: the shared file as `file`, its path, from the window's own dialog, or
    as `data`, its contents in base64, and `name`, from a browser's file chooser, or with neither the
    Mac's file dialog, and the folder to put the copy in as `into`, or with none the Mac's folder dialog,
    asked only once the file is read. Either dialog cancelled opens nothing. `check` reads the file alone
    and answers, as well as its `name` and `folder`, `returning`, the project of his a copy coming back
    belongs to, so the page offers its boards to that project first (option A, 26 October), and from the
    Mac's file dialog the `file` chosen. `from_name`, whose copy it is, names a copy coming back opened
    as its own project. Answers with every project afterwards and `opened`, the copy's folder and its
    project."""
    if srv.ROOT_OVERRIDE:
        raise WorkbookError(i18n.t("server.run_one_project_named_root"))
    held = None
    try:
        held = sent_upload(body)
        if held is not None:
            file = held
        elif str(body.get("file") or "").strip():
            file = srv.abs_path(str(body["file"]).strip().strip('"'))
        else:
            if srv.PLATFORM != "darwin":
                raise WorkbookError(srv.NO_DIALOG)
            file = srv.PICK_FOLDER(i18n.t("server.choose_shared_copy"), files=True)
            if file is None:
                return dict(projects_view(), opened=False)
        try:
            sent = pack_mod.read_sent(file)
        except pack_mod.PackError as exc:
            raise WorkbookError(str(exc)) from None
        if body.get("check") is True:
            # the file read first, so one it refuses never asks for a folder, and a copy coming back to a
            # project of his said, so the page can offer its boards to that project
            said = {"checked": True, "name": sent["name"], "folder": sent["folder"], **returning_said(file)}
            if held is None and not str(body.get("file") or "").strip():
                said["file"] = str(file)
            return said
        if str(body.get("into") or "").strip():
            into = srv.abs_path(str(body["into"]).strip().strip('"'))
        else:
            if srv.PLATFORM != "darwin":
                raise WorkbookError(srv.NO_DIALOG)
            into = srv.PICK_FOLDER(into_prompt(sent["folder"]))
            if into is None:
                return dict(projects_view(), opened=False)
        done = open_copy(file, into, from_name=str(body.get("from_name") or ""))
    finally:
        if held is not None:
            shutil.rmtree(held.parent, ignore_errors=True)
    return dict(projects_view(), **done)


def api_send_project(body: dict) -> dict:
    """Share a copy in Idiograph's own window: the project `root` names, by its id, written by the server
    straight to `to`, the path he chose in the window's save dialog, so the file never passes through
    the page, however many recordings the project holds (21 October). The save dialog has asked
    already whether to replace a file there, so one there is written over, through a file beside it
    renamed into place. A browser keeps its download from SEND_PATH."""
    root = send_root(body.get("root"))
    to = str(body.get("to") or "").strip()
    if not to:
        raise WorkbookError(i18n.t("server.choose_where_save_then_send"))
    dest = srv.abs_path(to)
    if dest.suffix.lower() != pack_mod.SUFFIX:
        dest = dest.with_name(dest.name + pack_mod.SUFFIX)
    if not dest.parent.is_dir():
        raise WorkbookError(i18n.t("server.folder_parent_nothing_sent", parent=dest.parent))
    if dest.is_dir():
        raise WorkbookError(i18n.t("server.is_folder_nothing_sent", name=dest.name))
    # a chosen send, as the command line's options: `participants` a list of names, `leave_out` and
    # `with` lists of kinds, `blind` the PETs and GETs left out, and `dry_run` what it would write
    # `pets` and `audio` the participants whose PETs or recordings go, each one sent
    options = dict(participants=body.get("participants") or None, leave_out=body.get("leave_out") or None,
                   with_kinds=body.get("with") or None, blind=body.get("blind") is True,
                   pets=body.get("pets") or None, audio=body.get("audio") or None, boards=body.get("boards") or None)
    for key in ("participants", "leave_out", "with_kinds", "pets", "audio"):
        if isinstance(options[key], str):
            options[key] = [options[key]]
    # Share a copy's card: `card`, its choice as the card holds it (see `card_options`)
    if isinstance(body.get("card"), dict):
        options = dict(card_options(body["card"]))
    if body.get("dry_run") is True:
        return send_project(root, dest, dry_run=True, **options)
    done = send_project(root, dest, **options)
    answer = {"sent": True, "file": done["file"], "name": done["name"], "files": done["files"],
              "bytes": done["bytes"], "size": done["size"]}
    if done.get("chosen"):
        answer.update({k: done[k] for k in ("participants", "kinds_out", "left", "notes", "each", "whole",
                                            "board_choice", "boards")})
    return answer


def api_boards_in(body: dict) -> dict:
    """A shared copy coming back, its boards added to the project `root` names, by its id (see
    `boards_in`): `file`, the sent file's path, `from_name`, whose copy it is, else the name the file
    carries, `participants` and `boards` to choose some, a board a name or `{"participant", "board"}`, and
    `dry_run`. Open a shared copy's card (Adam's option A, 26 October) calls it with `dry_run` for what it
    shows and then for real with the boards ticked, and from a browser's file chooser sends the file as
    `data` and `name`, as /api/open-sent takes it."""
    root = send_root(body.get("root"))
    lists = {k: ([body[k]] if isinstance(body.get(k), str) else body.get(k)) or None for k in ("participants", "boards")}
    held = sent_upload(body)
    try:
        file = held or str(body.get("file") or "").strip()
        if not file:
            raise WorkbookError(i18n.t("server.choose_shared_copy_nothing_brought"))
        return boards_in(root, held or srv.abs_path(file.strip('"')), from_name=str(body.get("from_name") or ""),
                         dry_run=body.get("dry_run") is True, request=str(body.get("request") or ""), **lists)
    finally:
        if held is not None:
            shutil.rmtree(held.parent, ignore_errors=True)


def api_send_list(body: dict) -> dict:
    """What Share a copy's card draws itself from, the project `root` names, by its id (see `send_list`).
    It only reads."""
    return send_list(send_root(body.get("root")))


def api_choose_root(_: dict) -> dict:
    """Choose folder, as a page from before the projects asks it: the Mac's own dialog, its folder
    added as a project (see `add_project`). Off a Mac there is no such dialog, and a cancelled
    dialog changes nothing."""
    if srv.PLATFORM != "darwin":
        raise WorkbookError(srv.NO_DIALOG)
    chosen = srv.PICK_FOLDER()
    if chosen is None or not Path(chosen).is_dir():
        return {"chosen": False}
    added = add_project(chosen)
    return {"chosen": True, "root": added["project"]["root"]}


def api_order(body: dict) -> dict:
    """His order of a project's rows, from a drag or Alt and an arrow on a row's handle: `root`, the
    project's id, and `order`, its case labels top to bottom, saved in its project file and every
    other key kept (see `write_order`). The demo's is fixed."""
    root = srv.project_named(body.get("root"))
    with writing(root=root):
        order = write_order(root, body.get("order"))
    return {"order": order}


# ------------------------------------------------------------- new project

# New project, on the home screen: a folder he picks, which Idiograph then manages, and the
# transcripts dropped onto its card, each named by its participant's pseudonym and its interview's
# name. Make writes a case folder for each pseudonym, `P<n> - Pseudonym`, numbered from the folder's
# next free number, each file's copy in the case's `Source/<interview>/`, one raw source with a
# sheet an interview, the shape a GRAVITY case of several interviews has, and the annotated
# workbook built from it, then adds the folder as a project. A browser's drop gives no path, so the
# page sends each file's contents, and the original is never moved, changed or deleted.
NEW_MAX = 25 * 1024 * 1024                  # the most one transcript may weigh
# A pseudonym is one capitalised word, the shape CASE_FOLDER takes, and every case New project and
# Add transcripts make is `P<n> - Pseudonym`. A folder that already carries a second part after the
# pseudonym still opens and shows by its pseudonym alone, since `display_case` takes the part off.
ONE_WORD = re.compile(r"^[A-Z][a-z]+$")
NUMBERED = re.compile(r"^P(\d+)(?=[\s-]|$)")
# what neither a sheet's name nor a folder's may hold
NOT_IN_NAME = re.compile(r"[\\/:*?\[\]\x00-\x1f]")


def next_number(folder: Path) -> int:
    """The folder's next free participant number, one past the highest `P<n>` its folders carry."""
    try:
        taken = [int(m.group(1)) for p in Path(folder).iterdir() if p.is_dir() and (m := NUMBERED.match(p.name))]
    except OSError:
        taken = []
    return max(taken, default=0) + 1


def file_name(value) -> str:
    """A dropped file's own name, with any folder the page sent before it left out."""
    return re.split(r"[\\/]", str(value or "").strip())[-1] or "transcript"


def file_bytes(entry: dict, name: str) -> bytes:
    """A dropped file's contents, sent in base64, refused in one line when they did not arrive
    whole or weigh more than a transcript does."""
    try:
        data = base64.b64decode(str(entry.get("data") or ""), validate=True)
    except (binascii.Error, ValueError):
        raise WorkbookError(str(convert_mod.unreadable(name))) from None
    if len(data) > NEW_MAX:
        raise WorkbookError(i18n.t("server.too_large_transcript", name=name))
    return data


def interview_name(text) -> str | None:
    """An interview's name as both a sheet and a folder take it, its spaces closed up, or None:
    up to 31 characters, none of `\\ / : * ? [ ]`, no apostrophe or full stop at either end, and
    never History, which Excel keeps for itself."""
    name = " ".join(str(text or "").split())
    if (not name or len(name) > 31 or NOT_IN_NAME.search(name) or name[0] in "'." or name[-1] in "'."
            or name.lower() == "history"):
        return None
    return name


def turns_view(read: dict, setting: str, form: str | None = None) -> dict:
    """A transcript as its card shows it, the import card's and New project's alike: the first turns,
    the count, each speaker with their turns, the interviewer guessed, the name each speaker's turns
    go under as the interviewer, and for a table its headings, the role of each column, and the
    preview's columns, a column for each role chosen, each turn with its notes and statements, and
    for a table's Time column the format its times were found in, how they are read, and each one
    that cannot be, by its passage, a turn of the preview carrying its time as written in `bad`. Each
    turn's time is written as `form` says, the project's timecodes, a new project's by default."""
    turns = read["turns"]
    notes = read.get("notes") or []
    bad = list(read.get("bad_times") or [])
    unread = {b["passage"]: b["time"] for b in bad}
    held = lambda i, role: preview_words(notes[i].get(role) or "") if i < len(notes) and isinstance(notes[i], dict) else ""
    cols = read.get("mapping")
    # a Word table's speakers and times may come from the words' own `Name:` and time at a row's head
    found = {"name": any(n != convert_mod.SPEAKER for n, _s, _w in turns), "ts": any(s is not None for _n, s, _w in turns)}
    return {
        "turns": [dict({"name": n, "time": wb_mod.timecode(s, form), "text": preview_words(w), "en": held(i, "en"), "es": held(i, "es"),
                        "kq": held(i, "kq")},
                       **({"bad": unread[i + 1]} if i + 1 in unread else {}))
                  for i, (n, s, w) in enumerate(turns[:convert_mod.PREVIEW])],
        # the preview's columns, for a table one for each role chosen, in the order the workbook has them
        "shown": [r for r in convert_mod.ROLES if cols.get(r) is not None or found.get(r)] if cols else ["name", "ts", "text"],
        "roles": read.get("roles"),
        "count": len(turns),
        "speakers": [{"name": s["name"], "turns": s["turns"]} for s in convert_mod.speakers(turns)],
        "interviewer": convert_mod.guess_interviewer(turns, setting), "setting": setting,
        "as": convert_mod.written_as(turns, setting),
        "columns": read["headers"], "mapping": read["mapping"],
        # what a Word table of transcript and notes brings beside the words, and what it leaves out
        "brings": convert_mod.brings(read),
        # a Time column's format, found and chosen, and the times it cannot read (20 October)
        "time_found": read.get("time_found"),
        "time_found_name": convert_mod.TIME_NAMES.get(read.get("time_found") or "", ""),
        "timing": read.get("timing"),
        "time_formats": [[k, v] for k, v in convert_mod.TIME_FORMATS.items()],
        "bad_times": bad,
        # an Excel file's sheets, for the Sheet chooser, and the one read, none for its first (ayabuild12)
        "sheets": read.get("sheets") or [], "sheet": read.get("sheet"),
        # a Quote column's quotes as they will pair with the statements, counts only (ayabuild12)
        "quotes": quote_counts(read),
    }


def quote_counts(read: dict) -> dict | None:
    """A read's quotes as they will land, by `workbook.quote_census`: each passage's statements and quotes a line
    each, paired by order. None for a file with no quote column, or one with nothing in it."""
    notes = read.get("notes") or []
    if not any(isinstance(n, dict) and n.get("kq") for n in notes):
        return None
    lines = lambda text: [ln for ln in str(text or "").splitlines() if ln.strip()]
    return wb_mod.quote_census([(words, lines(n.get("es")), lines(n.get("kq")))
                                for (_n, _s, words), n in zip(read["turns"], notes) if isinstance(n, dict)])


def quote_lines(counts: dict | None) -> list[str]:
    """A census of quotes in the words an agent's answer gives it, a line, or none."""
    if not counts:
        return []
    parts = []
    if counts["paired"]:
        parts.append(i18n.t("server.quotes_paired", n=counts["paired"]))
    if counts["unpaired"]:
        parts.append(i18n.t("server.quotes_unpaired", n=counts["unpaired"]))
    if counts["no_quote"]:
        parts.append(i18n.t("server.quotes_no_quote", n=counts["no_quote"]))
    if counts["unmarked"]:
        parts.append(i18n.t("server.quotes_unmarked", n=counts["unmarked"]))
    return [formats.list_words(parts) + "."] if parts else []


def recording_name(case: str, timepoint: int, timepoints, source: Path) -> str:
    """The name a recording is copied in under (ayabuild12, 9 November 2026): the participant's pseudonym and
    the interview's timepoint, `Wren T2.m4a`, or `Wren.m4a` in a project of one timepoint, never the source's
    own name, which may carry a real one. `case` is the participant's label or pseudonym."""
    who = str(case or "").split(" - ", 1)[-1].strip() or "Recording"
    ext = Path(source).suffix.lower()
    return f"{who} T{int(timepoint or 1)}{ext}" if longitudinal(timepoints) else f"{who}{ext}"


def preview_words(text: str, most: int = 240) -> str:
    """A passage's words, or its notes with their line breaks, cut for the card's preview at the last
    whole word within `most` characters, never mid-word."""
    text = str(text or "")
    if len(text) <= most:
        return text
    cut = text[:most + 1]
    space = max(cut.rfind(" "), cut.rfind("\n"))
    return (cut[:space] if space > most // 2 else text[:most]).rstrip(" ,;:\n") + "…"


def read_entry(entry: dict) -> tuple[str, bytes, dict]:
    """A row of New project's or Add's files read: its name, its bytes and its turns, refused in one
    line naming the file when it cannot be read."""
    name = file_name(entry.get("name"))
    data = file_bytes(entry, name)
    columns = entry.get("columns") if isinstance(entry.get("columns"), (dict, list)) else None
    try:
        read = convert_mod.read_data(name, data, columns, sheet=entry.get("sheet") or None)
    except convert_mod.Unreadable as exc:
        raise WorkbookError(str(exc)) from None
    if read.get("said"):
        raise WorkbookError(i18n.t("server.named_said", name=name, said=read['said']))
    if not read["turns"]:
        raise WorkbookError(str(convert_mod.unreadable(name)))
    return name, data, read


def new_cases(root: Path, body: dict, as_name: str, standing: dict | None = None, reader=None,
              run: "names_mod.Run | None" = None) -> list[dict]:
    """Every case New project's files make, in the order each pseudonym first comes, once every file
    has been read and nothing refuses them, each folder `P<n> - Pseudonym`. Each refusal is one line
    naming what to fix: a file that cannot be read, a missing pseudonym or one that is not one
    capitalised word, an interview's name, a participant under two numbers or two under one, and a
    folder or a case already there. Writes nothing. `reader` reads a row, `read_entry` when none is
    given, and a REFI-QDA import gives its own (see `qdpx_import`), whose `data` may be a file's path.

    `standing` is the cases at the root an Add can join (see `standing_cases`), none for New project.
    A file under the pseudonym of one of them is a further interview of that case, `joins` true,
    which takes no number from its row (see `join_case`). A `second` or a `second_part` a page from
    before 9 October sends is passed over.

    `run` (namesrule, 8 November 2026) is the project's list of names applied as each file is read: its
    file name, its interview's name, each speaker's name, every passage and every note go through it, and a
    file with a name replaced is kept in Source as the replaced text (see `pseudo_read`). None takes the
    project's own list for a plain read, and a REFI-QDA import gives an empty one, since it has done this
    already (see `qdpx_import`)."""
    standing = standing or {}
    if run is None:
        run = pseudo_run(root, body)
    files = [f for f in (body.get("files") if isinstance(body.get("files"), list) else []) if isinstance(f, dict)]
    if not files:
        raise WorkbookError(i18n.t("server.drop_transcript_first"))
    # each file's timepoint, in a project of two or more, the sheets it makes placed there
    tps = timepoints_of(project_file(root))
    cases: dict[str, dict] = {}
    for entry in files:
        name, data, read = (reader or read_entry)(entry)
        who = str(entry.get("pseudonym") or "").strip()
        if not who:
            raise WorkbookError(i18n.t("server.give_pseudonym", name=name))
        asked_interview = entry.get("interview")
        if run:
            stem, dot, ext = name.rpartition(".")
            name = (run.text(stem, who, {"participant": who, "part": "file"}) + dot + ext) if dot and stem else name
            asked_interview = run.text(str(asked_interview or ""), who, {"participant": who, "part": "interview"})
        if not ONE_WORD.match(who):
            raise WorkbookError(i18n.t("server.make_pseudonym_one_capitalised_word", name=name))
        if who.lower() == as_name.lower():
            raise WorkbookError(i18n.t("server.interviewer_s_name_settings_cannot", who=who))
        joins = who in standing
        interview = interview_name(asked_interview)
        if not str(asked_interview or "").strip():
            raise WorkbookError(i18n.t("server.give_interview_name", name=name))
        if interview is None:
            raise WorkbookError(i18n.t("server.make_interview_name_31_characters", name=name))
        number = None if joins else entry.get("number")
        if number in (None, ""):
            number = None
        else:
            try:
                number = int(number)
            except (TypeError, ValueError):
                number = 0
            if not 1 <= number <= 9999:
                raise WorkbookError(i18n.t("server.make_number_whole_number_from", name=name))
        case = cases.setdefault(who, {"pseudonym": who, "number": number, "interviews": [], "joins": joins})
        if case["number"] is None:
            case["number"] = number
        elif number is not None and number != case["number"]:
            raise WorkbookError(i18n.t("server.s_interviews_carry_two_numbers", who=who, number=case['number'], number2=number))
        if any(i["interview"].lower() == interview.lower() for i in case["interviews"]):
            raise WorkbookError(i18n.t("server.two_interviews_named", who=who, interview=interview))
        speakers = {s["name"] for s in convert_mod.speakers(read["turns"])}
        chosen = str(entry.get("interviewer") or "")
        # each speaker's role, as the import card gives them (20 October), or from a page from
        # before, the interviewer alone and every other speaker a participant
        given = entry.get("speakers") if isinstance(entry.get("speakers"), dict) else None
        roles = convert_mod.speaker_roles(read["turns"], given, "", None if given else (chosen if chosen in speakers else ""))
        held = convert_mod.roles_said(roles)
        if held:
            raise WorkbookError(i18n.t("server.named_held", name=name, held=held))
        try:
            timepoint = timepoint_asked(entry.get("timepoint"), tps) if longitudinal(tps) else 1
        except WorkbookError as exc:
            raise WorkbookError(i18n.t("server.named_exc", name=name, exc=exc)) from None
        copy = None
        if run:
            read, roles, copy = pseudo_read(run, who, interview, read, roles)
        # a recording the entry names (audioop, 9 November 2026), checked now and copied in with the interview, named
        # by the pseudonym and the timepoint as an import's is
        recording = {}
        if str(entry.get("audio") or "").strip():
            try:
                audio = recording_checked(entry["audio"])
                seconds = audio_mod.offset_value(entry.get("offset") if entry.get("offset") not in (None, "") else 0)
                if seconds is None:
                    raise WorkbookError(i18n.t("server.give_offset_seconds_plus_minus"))
            except WorkbookError as exc:
                raise WorkbookError(i18n.t("server.named_exc", name=name, exc=exc)) from None
            recording = {"audio": audio, "audio_offset": seconds, "audio_name": recording_name(who, timepoint, tps, audio)}
        case["interviews"].append({"interview": interview, "name": name, "data": copy if copy is not None else data,
                                   "read": read,
                                   "interviewer": convert_mod.the_interviewer(roles), "roles": roles,
                                   "timepoint": timepoint, **recording,
                                   **({"copy_suffix": ".txt"} if copy is not None else {})})
    try:
        there = [p.name for p in root.iterdir() if p.is_dir()]
    except OSError:
        there = []
    taken = {int(m.group(1)) for p in there if (m := NUMBERED.match(p))}
    known = {srv.display_case(p).split(" - ", 1)[-1] for p in there}
    given = {c["number"] for c in cases.values() if c["number"] is not None}
    free = next_number(root)
    numbered: dict[int, str] = {}
    for case in cases.values():
        if case["joins"]:
            continue
        if case["number"] is None:
            while free in given or free in taken:
                free += 1
            case["number"] = free
            given.add(free)
        n, who = case["number"], case["pseudonym"]
        if n in numbered:
            raise WorkbookError(i18n.t("server.p_given_both", n=n, other=numbered[n], who=who))
        numbered[n] = who
        case["label"] = f"P{n} - {who}"
        case["folder"] = case["label"]
        if (root / case["folder"]).exists():
            raise WorkbookError(i18n.t("server.label_there_already", label=case['label']))
        if n in taken:
            raise WorkbookError(i18n.t("server.p_folder_already", n=n))
        if who in known:
            raise WorkbookError(i18n.t("server.participant_already", who=who))
    for case in cases.values():
        if case["joins"]:
            join_case(case, standing[case["pseudonym"]])
    return list(cases.values())


def case_sheet(each: dict, as_name: str, who: str) -> tuple:
    """One interview's sheet of a case's raw source: its title, its turns as `as_case` writes them,
    and a Word table's notes beside them, the interviewer's under the name Settings gives him when he
    was chosen, so they land where the statements screen keeps his notes (19 October)."""
    read = each["read"]
    setting = str(srv.config().get("interviewer") or "").strip() if each["interviewer"] else ""
    if each.get("roles"):
        turns, marks = convert_mod.as_new_case(read["turns"], each["roles"], as_name, who)
        return each["interview"], turns, read.get("notes"), setting, marks
    return (each["interview"], convert_mod.as_case(read["turns"], each["interviewer"], as_name, who),
            read.get("notes"), setting)


def write_case(root: Path, case: dict, as_name: str, made: list[Path], described: str = "") -> None:
    """One case written: its folder, each file's copy in `Source/<interview>/` as `P<n>-<interview>`,
    the raw source `Source/P<n> <Pseudonym> - transcript.xlsx` with a sheet an interview, the
    interviewer's turns under Settings' name and the participant's under the pseudonym, and the
    annotated workbook built from it as `/api/create` builds one. The folder goes into `made` the
    moment it stands, so a failure takes it away again. `described`, for an agent's Add, says who made
    the workbook for which request, in its own description, as an agent's import says it."""
    folder = root / case["folder"]
    folder.mkdir()
    made.append(folder)
    n, who = case["number"], case["pseudonym"]
    sheets = []
    for each in case["interviews"]:
        place = folder / "Source" / each["interview"]
        place.mkdir(parents=True)
        keep_transcript(place / f"P{n}-{each['interview']}{copy_suffix(each)}", each["data"])
        place_audio(folder, each.get("audio"), each.get("audio_offset", 0.0), made, each["interview"], each.get("audio_name"))
        sheets.append(case_sheet(each, as_name, who))
    raw = folder / "Source" / f"P{n} {who} - transcript.xlsx"
    convert_mod.write_sheets(sheets, raw)
    book = wb_mod.create_from_source(raw, wb_mod.suggested_output(raw), made=described)
    place_timepoints(book, case["interviews"])


def copy_suffix(each: dict) -> str:
    """The suffix of an interview's copy in Source: its file's own, or .txt for a copy written from the text
    with its names replaced."""
    return each.get("copy_suffix") or Path(each["name"]).suffix.lower()


def keep_transcript(target: Path, data) -> None:
    """A transcript's copy in its interview's Source folder, never over a file there: its bytes, or
    for a REFI-QDA project the file itself copied from its path."""
    if isinstance(data, Path):
        with open(data, "rb") as src, open(target, "xb") as fh:
            shutil.copyfileobj(src, fh, 1024 * 1024)
        return
    with open(target, "xb") as fh:
        fh.write(data)


def place_timepoints(book: Path, interviews: list[dict]) -> None:
    """Each interview's sheet placed at its timepoint in the progress file beside the workbook, those
    at T1 left as every sheet is, so a project of one timepoint writes nothing new."""
    for timepoint in sorted({each.get("timepoint", 1) for each in interviews} - {1}):
        rounds_mod.tag_sheets(book, [each["interview"] for each in interviews if each.get("timepoint", 1) == timepoint],
                              timepoint)


def unmake(root: Path, made: list[Path], project_was: bytes | None, lock_was: bool) -> None:
    """What a failed Make wrote taken away, and nothing else: the case folders it made, which held
    nothing before it, the project file put back as it was or taken away when it was not there, and
    the root's lock file when the Make brought it."""
    for folder in reversed(made):
        shutil.rmtree(folder, ignore_errors=True)
    target = root / srv.PROJECT_FILE
    with contextlib.suppress(OSError):
        if project_was is None:
            target.unlink(missing_ok=True)
        else:
            target.write_bytes(project_was)
    if not lock_was:
        with contextlib.suppress(OSError):
            (root / locks.NAME).unlink(missing_ok=True)


def make_project(body: dict) -> dict:
    """Make: every row checked first, then every case written, the project file given its name and
    its question, and the folder added as a project through `add_project`. A failure on the way takes
    away what this Make wrote and says one line. The answer is every project afterwards, the one made
    and its cases by label.

    `qdpx`, from the import card (21 October), is a project from ATLAS.ti, NVivo or MAXQDA the card
    holds, its `held` key and the choices `qdpx_import` takes, brought in once the project file is
    written, `files` then optional. Its refusals come before anything is written.

    With `dry_run` (26 October, for the agents' `project new`) every check is made and nothing is
    written: the answer is the folder, the name and question its project file would hold, and each case
    it would make, its label, its interviews and each speaker's role.

    `method` (tadraw, 31 October 2026), "ipa", the default, or "ta", is written in the project file as it is
    made and fixed after. A folder whose project file is there already keeps the method it holds, IPA's for
    none, taken when none is asked, and a different one asked is refused before anything is written."""
    root = project_folder(body.get("folder"), srv.merge_config(srv.saved_config()))
    there = (root / srv.PROJECT_FILE).exists()
    # none asked is IPA, or the method a project file there holds
    method = (method_of(project_file(root)) if there and not str(body.get("method") or "").strip()
              else method_asked(body.get("method")))
    if there and method != method_of(project_file(root)):
        raise WorkbookError(i18n.t("method.refused_fixed", method=method_name(method_of(project_file(root)))))
    as_name = str(srv.config().get("interviewer") or "").strip() or convert_mod.INTERVIEWER
    qdpx = body.get("qdpx") if isinstance(body.get("qdpx"), dict) else None
    q_path = qdpx_held(qdpx.get("held")) if qdpx else None
    run = pseudo_run(root, body)
    cases = new_cases(root, body, as_name, run=run) if body.get("files") or not qdpx else []
    if qdpx:
        held_back = qdpx_import(root, q_path, qdpx)["said"]
        if held_back:
            raise WorkbookError(held_back)
    if body.get("dry_run") is True:
        return {"dry_run": True, "folder": str(root),
                "name": str(body.get("name") or "").strip() or srv.display_case(root.name),
                "research_question": str(body.get("research_question") or "").strip(), "method": method,
                "cases": [{"label": c["label"], "interviews": [{"interview": i["interview"], "file": i["name"],
                                                                "speakers": i["roles"], "timepoint": i["timepoint"],
                                                                "passages": len(i["read"]["turns"]),
                                                                **({"sheet": i["read"]["sheet"]} if i["read"].get("sheet") else {}),
                                                                **({"quotes": quote_counts(i["read"])} if quote_counts(i["read"]) else {})}
                                                               for i in c["interviews"]]} for c in cases],
                **pseudo_answer(run, body)}
    made: list[Path] = []
    labels = [c["label"] for c in cases]
    target = root / srv.PROJECT_FILE
    project_was = target.read_bytes() if target.exists() else None
    lock_was = (root / locks.NAME).exists()
    try:
        with writing(root=root):
            for case in cases:
                write_case(root, case, as_name, made)
            data = project_file(root)
            data.update(name=str(body.get("name") or "").strip(),
                        research_question=str(body.get("research_question") or "").strip(),
                        updated=datetime.now().astimezone().isoformat(timespec="seconds"))
            if project_was is None:
                data["method"] = method
            srv.save_json(target, data)
        if qdpx:
            brought = qdpx_import(root, q_path, qdpx, make=True)
            made += [root / p["label"] for p in brought["participants"] if not p["joins"]]
            labels += brought["made"]
        added = add_project(root)
    except Exception as exc:
        unmake(root, made, project_was, lock_was)
        if isinstance(exc, WorkbookError):
            raise
        raise WorkbookError(i18n.t("server.idiograph_could_write_participants_folders")) from None
    if qdpx:
        qdpx_let_go(qdpx.get("held"))
    # a Real name typed on a row joins the project's list, in its folder (namesui)
    with writing(root=root):
        pseudo_keep(root, run)
    return dict(projects_view(), made=True, project=added["project"], cases=labels, **pseudo_answer(run, body))


def api_new_project(body: dict) -> dict:
    """New project, with `op` of `folder`, `read` or `make`. `folder` takes the folder typed as
    `path`, or with none the Mac's folder dialog, whose Cancel answers `chosen` false, and answers
    the folder as it will be added, its next free number, and the name and question its project file
    gives, refused as Add project refuses one. `read` takes a file's `name` and its `data` in base64,
    with `columns` for a table and `speakers`, a role a speaker's name, and answers it as the import
    card's read does, each speaker's role in `speaker_roles`, with `interview`, its name guessed from
    the file's. `make` takes `folder`, `name`, `research_question` and `files`, each `name`, `data`,
    `columns`, `speakers` (or `interviewer`, from a page from before 20 October), `pseudonym`,
    `interview` and `number`, and `dry_run`, which writes nothing (see `make_project`)."""
    op = str(body.get("op") or "")
    if op == "folder":
        if str(body.get("path") or "").strip():
            folder = body["path"]
        else:
            if srv.PLATFORM != "darwin":
                raise WorkbookError(srv.NO_DIALOG)
            folder = srv.PICK_FOLDER(i18n.t("server.choose_folder_new_project"))
            if folder is None:
                return {"chosen": False}
        chosen = project_folder(folder, srv.merge_config(srv.saved_config()))
        held = read_project(chosen)
        # a folder whose project file is there already keeps its method, which the card shows fixed (tadraw)
        return {"chosen": True, "folder": str(chosen), "next": next_number(chosen),
                "name": held["name"], "research_question": held["research_question"],
                **({"method": held["method"]} if (chosen / srv.PROJECT_FILE).exists() else {}),
                **({"timepoints": held["timepoints"]} if longitudinal(held["timepoints"]) else {})}
    if op == "read":
        name = file_name(body.get("name"))
        data = file_bytes(body, name)
        columns = body.get("columns") if isinstance(body.get("columns"), (dict, list)) else None
        setting = str(srv.config().get("interviewer") or "").strip()
        try:
            read = convert_mod.read_data(name, data, columns, sheet=body.get("sheet") or None)
            said = read.get("said") or (None if read["turns"] else str(convert_mod.unreadable(name)))
        except convert_mod.Unreadable as exc:
            read = {"kind": convert_mod.kind_of(name), "turns": [], "headers": None, "mapping": None}
            said = str(exc)
        # each speaker's role, the guess or as the row's choosers give them (20 October)
        given = body.get("speakers") if isinstance(body.get("speakers"), dict) else None
        roles = convert_mod.speaker_roles(read["turns"], given, setting)
        said = said or (convert_mod.roles_said(roles) if read["turns"] else None)
        return dict(turns_view(read, setting), kind=read["kind"], file=name, said=said, speaker_roles=roles,
                    interview=convert_mod.interview_of(name))
    if op == "make":
        return make_project(body)
    raise WorkbookError(i18n.t("server.op_folder_read_make"))


# Add transcripts, on each project's page: the New project card with the project fixed. A file under
# a new pseudonym makes a new case at the project's next free number, `P<n> - Pseudonym`, as Make
# does. A file under the pseudonym of a case already there is a further interview of it: its copy in
# `Source/<interview>/`, a sheet more at the end of the raw source, and the same sheet at the end of
# the annotated workbook, made as `create_from_source` makes one, once `archive_copy` has kept the
# workbook in the case's `_Archive/`. No sheet, cell or style already there changes, and a second
# part a case's folder already carries stays in its folder's name alone.
ADD_LABEL = "pre-add"
# a case folder an Add can join, `P<n> - Pseudonym`, with a second part or none
JOINABLE = re.compile(r"^P(\d+) - ([A-Z][a-z]+)(?:-[A-Z][a-z]+)?$")


def standing_cases(root: Path) -> dict[str, list[dict]]:
    """The cases at a project's root an Add can join, by pseudonym, each `{"path", "label",
    "number"}`, in number order. The label never carries a second part."""
    out: dict[str, list[dict]] = {}
    try:
        folders = sorted(p for p in Path(root).iterdir() if p.is_dir())
    except OSError:
        folders = []
    # a case renamed with its folder kept joins by its new pseudonym (16 October)
    names = names_at(root)
    for folder in folders:
        m = JOINABLE.match(folder.name)
        if m:
            who = names.get(srv.display_case(folder.name)) or m.group(2)
            out.setdefault(who, []).append({"path": folder, "label": f"P{m.group(1)} - {who}", "number": int(m.group(1))})
    for held in out.values():
        held.sort(key=lambda c: c["number"])
    return out


def own_books(folder: Path, kind: str) -> list[Path]:
    """A case's workbooks of one kind, `annotated` in its folder or `raw` in its own `Source/`, never
    a backup, a lock or a hidden file."""
    try:
        found = sorted(p for p in Path(folder).iterdir() if p.is_file() and p.suffix.lower() == ".xlsx")
    except OSError:
        return []
    return [p for p in found if not p.name.startswith(("~$", ".")) and not BACKUP_STEM.search(p.stem)
            and (read_sheets(p) or ("", []))[0] == kind]


def join_case(case: dict, held: list[dict]) -> None:
    """A case an Add joins, checked, and its folder, label, number, annotated workbook and raw source
    put on `case`, either workbook None when the case has none. Refused in one line when two cases
    share the pseudonym, when the case has two of either workbook, when Excel has either open, and
    when the case has an interview of that name already. Writes nothing."""
    if len(held) > 1:
        raise WorkbookError(i18n.t("server.share_pseudonym", names=formats.list_words(c['label'] for c in held), pseudonym=case['pseudonym']))
    folder, label = held[0]["path"], held[0]["label"]
    books, raws = own_books(folder, "annotated"), own_books(folder / "Source", "raw")
    book = next((b for b in books if any(wb_mod.suggested_output(r) == b for r in raws)), None)
    book = book or (books[0] if len(books) == 1 else None)
    if books and book is None:
        raise WorkbookError(i18n.t("server.more_than_one_annotated_workbook", label=label))
    raw = next((r for r in raws if book is not None and wb_mod.suggested_output(r) == book), None)
    raw = raw or (raws[0] if len(raws) == 1 else None)
    if raws and raw is None:
        raise WorkbookError(i18n.t("server.more_than_one_raw_source", label=label))
    names: set[str] = set()
    for path in (book, raw):
        if path is not None:
            wb_mod.guard_lock(path)
            names |= {str(n).lower() for n in (read_book(path) or {}).get("names") or []}
    with contextlib.suppress(OSError):
        names |= {p.name.lower() for p in (folder / "Source").iterdir() if p.is_dir()}
    for each in case["interviews"]:
        if each["interview"].lower() in names:
            raise WorkbookError(i18n.t("server.interview_named_already", label=label, interview=each['interview']))
    case.update(path=folder, label=label, number=held[0]["number"], book=book, raw=raw)


def add_interviews(case: dict, as_name: str, back: list) -> None:
    """A case's further interviews written: each file's copy in `Source/<interview>/` as
    `P<n>-<interview>`, a sheet each at the end of its raw source, or a raw source of them when the
    case had none, and the same sheets at the end of its annotated workbook, which `archive_copy`
    keeps in `_Archive/` first. Each step goes into `back` once it is taken, so a failure puts it
    back (see `unadd`)."""
    folder, n, who = case["path"], case["number"], case["pseudonym"]
    source = folder / "Source"
    sheets = []
    for each in case["interviews"]:
        place = source / each["interview"]
        top = place if source.exists() else source
        place.mkdir(parents=True)
        back.append(("folder", top))
        keep_transcript(place / f"P{n}-{each['interview']}{copy_suffix(each)}", each["data"])
        place_audio(folder, each.get("audio"), each.get("audio_offset", 0.0), [], each["interview"], each.get("audio_name"))
        sheets.append(case_sheet(each, as_name, who))
    raw = case["raw"]
    if raw is None:
        raw = source / f"P{n} {who} - transcript.xlsx"
        convert_mod.write_sheets(sheets, raw)
        back.append(("file", raw))
    else:
        back.append(("raw", raw, raw.read_bytes(), raw.stat()))
        convert_mod.add_sheets(sheets, raw)
    book = case["book"]
    if book is not None:
        archive = wb_mod.case_folder(book) / "_Archive"
        if not archive.exists():
            back.append(("archive", archive))
        back.append(("book", book, wb_mod.archive_copy(book, ADD_LABEL)))
        wb_mod.add_from_source(raw, [sheet[0] for sheet in sheets], book)
    # each at its timepoint, beside the workbook, or the one its raw source becomes
    if any(each.get("timepoint", 1) > 1 for each in case["interviews"]):
        target = book if book is not None else wb_mod.suggested_output(raw)
        back.append(progress_step(target))
        place_timepoints(target, case["interviews"])


def unadd(made: list[Path], back: list) -> None:
    """What a failed Add changed put back, the last step first: an annotated workbook from its copy
    in `_Archive/`, which then goes, a raw source from the bytes it had, and every file and folder
    the Add made taken away. Nothing else is touched."""
    for step in reversed(back):
        with contextlib.suppress(OSError):
            if step[0] == "book":
                book, backup = step[1], step[2]
                tmp = book.with_name(f".{book.stem}.idiograph.tmp.xlsx")
                shutil.copy2(backup, tmp)
                os.replace(tmp, book)
                if book.read_bytes() == backup.read_bytes():
                    backup.unlink()
            elif step[0] == "raw":
                raw, data, mark = step[1], step[2], step[3]
                tmp = raw.with_name(f".{raw.stem}.idiograph.tmp.xlsx")
                tmp.write_bytes(data)
                os.replace(tmp, raw)
                os.utime(raw, ns=(mark.st_atime_ns, mark.st_mtime_ns))
            elif step[0] == "file":
                step[1].unlink(missing_ok=True)
            elif step[0] == "progress":
                if step[2] is None:
                    step[1].unlink(missing_ok=True)
                else:
                    step[1].write_bytes(step[2])
            elif step[0] == "folder":
                shutil.rmtree(step[1], ignore_errors=True)
            elif step[0] == "archive":
                step[1].rmdir()
    for folder in reversed(made):
        shutil.rmtree(folder, ignore_errors=True)


def add_root(body: dict) -> Path:
    """The project an Add is for, named by its id, refused for the demo and for a folder gone."""
    root = srv.project_named(body.get("root"))
    if srv.is_demo_root(root):
        raise WorkbookError(i18n.t("server.demo_s_project_fixed"))
    if not root.is_dir():
        raise WorkbookError(i18n.t("server.folder_nothing_added"))
    return root


def add_plan(cases: list[dict]) -> list[dict]:
    """What an Add would write, case by case, as an agent's dry run answers it: each case's label, its
    pseudonym and number, whether it joins a case there, and each interview's name, file, timepoint, its
    passages and its speakers with their roles. Nothing of a participant's words."""
    return [{"label": c["label"], "pseudonym": c["pseudonym"], "number": c["number"], "joins": c["joins"],
             "interviews": [{"interview": i["interview"], "file": i["name"], "timepoint": i.get("timepoint", 1),
                             "passages": len(i["read"]["turns"]),
                             **({"sheet": i["read"]["sheet"]} if i["read"].get("sheet") else {}),
                             **({"quotes": quote_counts(i["read"])} if quote_counts(i["read"]) else {}),
                             **({"recording": i["audio_name"]} if i.get("audio") else {}),
                             "speakers": [{"name": sp["name"], "turns": sp["turns"],
                                           "role": convert_mod.SPEAKER_ROLES[(i.get("roles") or {}).get(sp["name"], "participant")]}
                                          for sp in convert_mod.speakers(i["read"]["turns"])]}
                            for i in c["interviews"]]} for c in cases]


def add_made(case: dict, tool: str, request: str) -> str:
    """Who made a case's workbook in a conversation, for which request and from which files, kept in the
    workbook's own description as an agent's import keeps it."""
    files = ", ".join(i["name"] for i in case["interviews"])
    day = datetime.now()
    return (f"Made by {tool} in a conversation on {day.day} {day.strftime('%B %Y')}, "
            f"for the request '{request}', from {files}.")


def add_record(book: Path, case: dict, tool: str, request: str) -> None:
    """An agent's Add kept in History, the participant's progress file's `imports`, as an import of a
    REFI-QDA project keeps its lines: when, the files, who for which request and the sheets it made."""
    progress = rounds_mod.load_progress(book)
    progress.setdefault("imports", []).append(marked(
        {"when": datetime.now().astimezone().isoformat(timespec="seconds"),
         "from": ", ".join(i["name"] for i in case["interviews"]), "add": True,
         "sheets": [i["interview"] for i in case["interviews"]],
         **quotes_held(case["interviews"]),
         **({"recordings": [i["audio_name"] for i in case["interviews"] if i.get("audio")]}
            if any(i.get("audio") for i in case["interviews"]) else {})}, tool, request))
    rounds_mod.save_progress(book, progress)


def quotes_held(interviews: list[dict]) -> dict:
    """The quotes an Add's interviews brought, counted across them for History, or nothing with none."""
    counts = [c for c in (quote_counts(i["read"]) for i in interviews) if c]
    return {"quotes": {k: sum(c[k] for c in counts) for k in counts[0]}} if counts else {}


def add_transcripts(body: dict) -> dict:
    """Add: every row checked first, then each new case written as Make writes one and each further
    interview added to its case. A failure on the way puts back what this Add changed and takes
    away what it made, the lock files it brought too, and says one line. The answer is the project,
    its new cases and the cases joined, by label.

    An agent's call (26 October, `project add-transcripts`) adds `dry_run`, which answers every row
    checked and what it would write (see `add_plan`) with nothing written, and `tool` and `request`,
    which each new workbook's description and each participant's History under `imports` carry.

    The project's list of names (namesrule, 8 November 2026) is applied to every file on its way in, and the
    answer's `names` says how many were replaced and left, by entry and where, never a name (see `pseudo_answer`).
    `skip` leaves finds as written, each an entry's number and its find's place, `3:1`."""
    root = add_root(body)
    as_name = str(srv.config().get("interviewer") or "").strip() or convert_mod.INTERVIEWER
    run = pseudo_run(root, body)
    cases = new_cases(root, body, as_name, standing=standing_cases(root), run=run)
    tool, request = agent_marks(body)
    if body.get("dry_run") is True:
        return {"added": False, "dry_run": True, "project": read_project(root), "plan": add_plan(cases),
                "cases": [c["label"] for c in cases if not c["joins"]],
                "joined": [c["label"] for c in cases if c["joins"]], **pseudo_answer(run, body)}
    books = [c["raw"] or c["path"] / "Source" / f"P{c['number']} {c['pseudonym']} - transcript.xlsx"
             for c in cases if c["joins"]]
    marks = [locks.root_lock(root)] + [wb_mod.case_lock(b) for b in books]
    were = [(p, p.exists(), p.parent.exists()) for p in marks]
    made: list[Path] = []
    back: list = []
    try:
        with writing(root=root, books=books):
            # in a project worked on together a participant a member adds is theirs to work on (landwt)
            ours = team_sync.adding(root, [c["folder"] for c in cases if not c["joins"]])
            try:
                for case in cases:
                    if case["joins"]:
                        if tool and case["book"] is not None:
                            back.append(progress_step(case["book"]))
                        add_interviews(case, as_name, back)
                        book = case["book"]
                    else:
                        write_case(root, case, as_name, made, add_made(case, tool, request) if tool else "")
                        book = wb_mod.suggested_output(root / case["folder"] / "Source" /
                                                       f"P{case['number']} {case['pseudonym']} - transcript.xlsx")
                    if tool and book is not None:
                        add_record(book, case, tool, request)
                # a Real name typed on a row joins the project's list, in its folder (namesui)
                pseudo_keep(root, run)
            except Exception:
                unadd(made, back)
                team_sync.unadding(root, ours)
                raise
    except Exception as exc:
        for lock, was, held in were:
            with contextlib.suppress(OSError):
                if not was:
                    lock.unlink(missing_ok=True)
                if not held:
                    lock.parent.rmdir()
        if isinstance(exc, WorkbookError):
            raise
        raise WorkbookError(i18n.t("server.idiograph_could_add_transcripts_nothing")) from None
    return {"added": True, "project": read_project(root), "cases": [c["label"] for c in cases if not c["joins"]],
            "joined": [c["label"] for c in cases if c["joins"]], **pseudo_answer(run, body)}


def api_add_transcripts(body: dict) -> dict:
    """Add transcripts, with `op` of `project` or `add`, each with `root`, the project's id. `project`
    answers what the card needs: the project's `name`, its `next` free number and its `cases`, each
    `label` and `pseudonym`, never a second part. `add` takes `files` as New project's `make` does, a
    file under a case's pseudonym joining that case with no number, and answers as `add_transcripts`
    does. A file is read through New project's `read`."""
    op = str(body.get("op") or "")
    if op == "project":
        root = add_root(body)
        held = read_project(root)
        cases = sorted((c for listed in standing_cases(root).values() for c in listed), key=lambda c: c["number"])
        # the project's timepoints, and each case's held, so a row of a participant there already
        # starts at the first timepoint they have no interview at
        long = longitudinal(held["timepoints"])
        return dict({"id": held["id"], "name": held["name"], "next": next_number(root),
                     "cases": [dict({"label": c["label"], "pseudonym": c["label"].split(" - ", 1)[1]},
                                    **({"held": sorted(timepoints_held(c["path"]))} if long else {})) for c in cases]},
                    **({"timepoints": held["timepoints"]} if long else {}))
    if op == "add":
        return add_transcripts(body)
    raise WorkbookError(i18n.t("server.op_project_add"))


# ---------------------------------------------------------- names replaced as a transcript comes in (8 November 2026)
# The project's list of real names and what each is written as (namesrule, the first of three builds, Adam's picks of
# 8 November). Since namesui (Adam, 8 November about 22:50) the list is one file in the project's folder,
# `idiograph-names.json`, moving with it, never in a workbook, History, the agent log, a shared copy or an export (see
# `family/names.py`). The transcripts already in are checked, then reviewed and replaced (`pseudo_replace`), the
# workbooks as they were kept in each participant's _Archive. Every road a transcript comes
# in by applies it: Add transcripts and New project's files (VTT, SRT, Word, CSV, Excel, text), a REFI-QDA project,
# and an import into a case. The app's own calls may ask for the finds (`names_preview`), with the words found. A
# call from the command line or the MCP server is told counts only, and cannot add a name.


def pseudo_list(root) -> list[dict]:
    """The project's list of names, from its folder's `idiograph-names.json` (namesui), none when it has none. A list
    namesrule kept in the app's own folder is moved there the first time (`names.load_at`)."""
    if root is None:
        return []
    root = Path(root)
    if srv.is_demo_root(root):
        return []
    return names_mod.load_at(root, project_file(root), root / srv.PROJECT_FILE)


def pseudo_run(root, body: dict) -> "names_mod.Run":
    """The project's list ready to apply, with the skips a call gives, refused in one line when one is no skip, and
    an entry for each Real name typed on the card's rows (namesui), which an agent cannot give, since an agent that
    types a real name has sent it to a model."""
    body = body or {}
    try:
        skip = names_mod.read_skip(body.get("skip"))
    except names_mod.NamesError as exc:
        raise WorkbookError(str(exc)) from None
    files = body.get("files") if isinstance(body.get("files"), list) else []
    if any(isinstance(f, dict) and str(f.get("real") or "").strip() for f in files) and agent_marks(body)[0]:
        raise WorkbookError(i18n.t("names.agent_adds"))
    try:
        entries = names_mod.with_real_names(pseudo_list(root), files)
    except names_mod.NamesError as exc:
        raise WorkbookError(str(exc)) from None
    return names_mod.Run(entries, skip)


def pseudo_keep(root, run: "names_mod.Run") -> None:
    """The entries a Real name made kept in the project's list, once an Add or a new project has been written."""
    if root is None or not run or srv.is_demo_root(Path(root)):
        return
    held = pseudo_list(root)
    if run.entries != held:
        names_mod.save_at(root, run.entries)


def pseudo_answer(run: "names_mod.Run", body: dict) -> dict:
    """What an answer says of the names: `names`, the counts by entry and place, a line, and for the app's own
    call (`names_preview`) every find with the words found. Nothing when the project has no list."""
    if not run:
        return {}
    counts = run.counts()
    out = dict(counts, said=names_mod.say(counts), lines=names_mod.lines(counts))
    if (body or {}).get("names_preview") is True:
        out["finds"] = run.preview()
    return {"names": out}


def pseudo_read(run: "names_mod.Run", who: str, interview: str, read: dict, roles: dict) -> tuple[dict, dict, bytes | None]:
    """A file's read with its names replaced: each distinct speaker's name once, every passage's words, every
    note. Answers the read, the roles under the speakers' new names, and the text to keep in Source in place of the
    file when a name was replaced in it (the original is not kept), else None."""
    def where(part: str, **more) -> dict:
        return dict({"participant": who, "interview": interview, "part": part}, **more)

    start = len(run.finds)
    rename: dict[str, str] = {}
    for i, (n, _s, _w) in enumerate(read["turns"]):
        if n not in rename:
            # the speaker's first passage, which the card's preview draws the name's find on (namesui)
            rename[n] = run.text(n, who, where("speaker", turn=i + 1))
    turns = [(rename[n], sec, run.text(w, who, where("words", turn=i + 1)))
             for i, (n, sec, w) in enumerate(read["turns"])]
    notes = read.get("notes")
    if notes:
        notes = [{k: (run.text(v, who, where("notes", turn=i + 1)) if isinstance(v, str) else v) for k, v in held.items()}
                 if isinstance(held, dict) else held for i, held in enumerate(notes)]
    changed = any(not f["skipped"] for f in run.finds[start:])
    read = dict(read, turns=turns, **({"notes": notes} if "notes" in read else {}))
    kept = names_mod.render(turns, notes).encode("utf-8") if changed else None
    return read, {rename.get(k, k): v for k, v in (roles or {}).items()}, kept


def pseudo_sources(rows) -> dict[int, str | None]:
    """Each source of a REFI-QDA import and the pseudonym it is given, none for a source not chosen yet."""
    out: dict[int, str | None] = {}
    for row in rows or []:
        try:
            out[int(row.get("source"))] = str(row.get("pseudonym") or "").strip() or None
        except (TypeError, ValueError):
            continue
    return out


def pseudo_package(run: "names_mod.Run", pkg: dict, who_of: dict) -> None:
    """A REFI-QDA package's names replaced where they are not a source's text: its codes and sets (a name every
    participant shares, so the entries for everyone alone), each source's name (as its participant's)."""
    for code in pkg["codes"].values():
        code["name"] = run.text(code["name"], None, {"part": "code"})
    for one in pkg["sets"]:
        one["name"] = run.text(one["name"], None, {"part": "code group"})
    for src in pkg["sources"]:
        src["name"] = run.text(src["name"], who_of.get(src["n"]), {"participant": who_of.get(src["n"]) or "", "part": "file"})


def pseudo_mapped(run: "names_mod.Run", who, src: dict, mapped: dict, roles: dict, pkg: dict) -> tuple[dict, dict]:
    """One source as mapped (`qdpx.map_source`) with its names replaced: speakers once each, passages, notes, the
    statements that comments made, and each quote with the passage's own skips. A statement named by a code
    already has the code's replaced name."""
    def where(part: str, **more) -> dict:
        return dict({"participant": who or "", "interview": src["name"], "part": part}, **more)

    coded = {c["name"] for c in pkg["codes"].values()}
    rename: dict[str, str] = {}
    for n, _s, _w in mapped["turns"]:
        if n not in rename:
            rename[n] = run.text(n, who, where("speaker"))
    turns, left = [], {}
    for i, (n, sec, w) in enumerate(mapped["turns"]):
        mark = len(run.finds)
        turns.append((rename[n], sec, run.text(w, who, where("words", turn=i + 1))))
        left[i] = run.left(mark)
    notes = [{k: run.text(v, who, where("notes", turn=i + 1)) for k, v in held.items()} if held else held
             for i, held in enumerate(mapped["notes"])]
    pairs = {i: [{**pair, "es": pair["es"] if pair["es"] in coded else run.text(pair["es"], who, where("statements", turn=i + 1)),
                  "kq": run.text(pair["kq"], who, where("quotes", turn=i + 1), mirror=left.get(i, set()))}
                 for pair in items] for i, items in mapped["pairs"].items()}
    return dict(mapped, turns=turns, notes=notes, pairs=pairs), {rename.get(k, k): v for k, v in roles.items()}


def pseudo_view(entries: list[dict], agent: bool) -> list[dict]:
    """The list as a call is shown it: the app's own, in full, an agent's by entry number, replacement and
    whom it is for, with how many spellings and never a real one."""
    if not agent:
        return [dict(e, entry=n + 1) for n, e in enumerate(entries)]
    return [{"entry": n + 1, "to": e["to"], "for": e["for"], "spellings": len(e["real"]), "case": e["case"]}
            for n, e in enumerate(entries)]


# what each column of a workbook already in is called among the finds, the same words an Add's finds use
PSEUDO_PARTS = {"speaker": "speaker", "transcript": "words", "es": "statements", "kq": "quotes", "en": "notes",
                "note": "notes"}
# the copies in Source read as text, a name replaced where it stands, the file's own form kept
PSEUDO_TEXT_COPIES = (".txt", ".vtt", ".srt", ".csv", ".md")
# the label of the copies kept in a participant's _Archive before the names are replaced, which a send leaves out
PSEUDO_ARCHIVE = "pre-names"


def pseudo_books(root: Path):
    """Every participant's annotated workbook in the project, in the one order a check and a replace both take,
    each with its participant's pseudonym and folder."""
    for folder in sorted(p for p in Path(root).iterdir() if p.is_dir()):
        if not JOINABLE.match(folder.name):
            continue
        who = label_for(folder).split(" - ", 1)[-1]
        for book in own_books(folder, "annotated"):
            yield who, folder, book


def pseudo_fixer(run: "names_mod.Run", who: str, left: dict | None = None):
    """The `fix` a workbook's rows are run through (`workbook.names_in_book`): each piece through the run as its
    participant's, by sheet, passage and part. `left` gathers, by sheet and row, what each row's finds left as
    written, for the raw source and Source's copies to leave the same."""
    def fix(text, role, sheet, row):
        mark = len(run.finds)
        out = run.text(text, who, {"participant": who, "interview": sheet, "part": PSEUDO_PARTS.get(role, role),
                                   "turn": row - 1, "row": row})
        if left is not None:
            left.setdefault((sheet, row), set()).update(run.left(mark))
        return out
    return fix


def pseudo_check(root: Path, entries: list[dict], skip=()) -> tuple["names_mod.Run", dict]:
    """Every transcript already in the project searched for the list's names: each passage's speaker and words,
    its statements, quotes, exploratory notes and interviewer's notes, nothing written. Answers the run, its finds
    by participant, sheet and passage, and each workbook a replace with `skip` would change."""
    run = names_mod.Run(entries, skip)
    changes: dict = {}
    for who, _folder, book in pseudo_books(root):
        mark = len(run.finds)
        wb_mod.names_in_book(book, pseudo_fixer(run, who), dry=True)
        if any(not f["skipped"] for f in run.finds[mark:]):
            changes[book] = True
    return run, changes


def pseudo_copies(run: "names_mod.Run", who: str, folder: Path, left: set, stamp: str) -> int:
    """A participant's copies in Source brought into line with their workbooks, with the same finds left as
    written (`left`, each entry and the words): a text copy has its names replaced where they stand, any other
    (a Word file, an Excel file) is read and kept as the replaced text, `.txt`, as an Add keeps one. The copy as it
    was goes to the participant's `_Archive` first, under the label a send leaves out. Answers how many changed."""
    source = folder / "Source"
    if not source.is_dir():
        return 0
    archive = folder / "_Archive"
    files = [p for p in sorted(source.iterdir()) if p.is_file() and p.suffix.lower() in PSEUDO_TEXT_COPIES]
    for sub in sorted(p for p in source.iterdir() if p.is_dir()):
        files += [p for p in sorted(sub.iterdir()) if p.is_file() and p.suffix.lower() in convert_mod.FORMATS + (".md",)]
    changed = 0
    where = {"participant": who, "part": "copy"}
    for path in files:
        if path.name.startswith(("~$", ".")):
            continue
        try:
            if path.suffix.lower() in PSEUDO_TEXT_COPIES:
                text = path.read_text(encoding="utf-8-sig")
                new = run.text(text, who, where, mirror=left)
                if new == text:
                    continue
                out = path
            else:
                read = convert_mod.read_data(path.name, path.read_bytes())
                turns = [(run.text(n, who, where, mirror=left), s, run.text(w, who, where, mirror=left))
                         for n, s, w in read["turns"]]
                notes = read.get("notes")
                if notes:
                    notes = [{k: run.text(v, who, where, mirror=left) if isinstance(v, str) else v for k, v in held.items()}
                             if isinstance(held, dict) else held for held in notes]
                if turns == [tuple(t) for t in read["turns"]] and notes == read.get("notes"):
                    continue
                new, out = names_mod.render(turns, notes), path.with_suffix(".txt")
        except (OSError, UnicodeDecodeError, convert_mod.Unreadable, ValueError):
            continue
        archive.mkdir(parents=True, exist_ok=True)
        kept = archive / f"{path.stem} ({PSEUDO_ARCHIVE} {stamp}){path.suffix}"
        n = 2
        while kept.exists():
            kept = archive / f"{path.stem} ({PSEUDO_ARCHIVE} {stamp}-{n}){path.suffix}"
            n += 1
        shutil.move(str(path), str(kept))
        out.write_text(new, encoding="utf-8", newline="\n")
        changed += 1
    return changed


def pseudo_replace(root: Path, entries: list[dict], skip, tool: str = "", request: str = "") -> dict:
    """Review and replace (namesui, Adam's pick of 8 November 2026): the list's names replaced in the transcripts
    already in, the finds `skip` names left as written. For each participant whose workbook holds one, the workbook
    and its raw source are kept first in the participant's `_Archive` (`workbook.archive_copy`, labelled
    "pre-names", which keeps the real names and which a send leaves out), then the workbook's rows are written,
    every board and every copy of the participant following the statements, quotes and notes as a find and replace
    makes them follow (`follow_replace`), the raw source and Source's copies brought into line with the same finds
    left. The project's History gets one record, counts only. Answers the run and the participants changed."""
    _planned, changes = pseudo_check(root, entries, skip)
    run = names_mod.Run(entries, skip)
    stamp = datetime.now().strftime("%Y%m%d-%H%M")
    done, failed = [], []
    for who, folder, book in pseudo_books(root):
        if book not in changes:
            # the run still meets every find in this workbook, so the finds after it keep their numbers
            wb_mod.names_in_book(book, pseudo_fixer(run, who), dry=True)
            continue
        left: dict = {}
        raws = [r for r in own_books(folder / "Source", "raw") if wb_mod.suggested_output(r) == book]
        with writing(book, root=root):
            before = copies_before(book)
            for each in [book] + raws:
                wb_mod.archive_copy(each, PSEUDO_ARCHIVE)
            rows = wb_mod.names_in_book(book, pseudo_fixer(run, who, left))["rows"]
            followed = follow_replace(book, rows, tool=tool, request=request, before=before)
            failed += followed["failed"]
            every = set().union(*left.values()) if left else set()
            for raw in raws:
                wb_mod.names_in_book(raw, lambda text, role, sheet, row: run.text(
                    text, who, {"part": "raw"}, mirror=left.get((sheet, row), every)))
            pseudo_copies(run, who, folder, every, stamp)
        done.append(label_for(folder))
    counts = run.counts()
    if done:
        with writing(root=root):
            hist_mod.record(root, "names replace", [i18n.t("names.history_line", replaced=counts["replaced"],
                                                           left=counts["left"],
                                                           participants=i18n.t("cli.n.participant", n=len(done)))],
                            {"by": "agent", "tool": tool, "request": request} if tool else None)
    return {"run": run, "participants": done, "failed": failed}


def pseudo_names_answer(run: "names_mod.Run", agent: bool, preview: bool) -> dict:
    """A check's or a replace's counts as an answer says them, and for the app's own call every find."""
    counts = run.counts()
    out = dict(counts, said=names_mod.say(counts), lines=names_mod.lines(counts))
    if preview and not agent:
        out["finds"] = run.preview()
    return out


def pseudo_segments(text: str, finds: list[dict]) -> list:
    """A piece of text as the card draws it with its finds: plain runs as strings, each find `{to, was, kept}`."""
    out, last = [], 0
    for f in sorted(finds, key=lambda f: f["at"]):
        if f["at"] < last:
            continue
        if f["at"] > last:
            out.append(text[last:f["at"]])
        out.append({"to": f["to"], "was": f["found"], "kept": f["skipped"]})
        last = f["at"] + len(f["found"])
    if last < len(text):
        out.append(text[last:])
    return out


def pseudo_preview(root, body: dict) -> dict:
    """What the list does to the files on Add transcripts' or New project's card before they are added, every
    file run through the list in the order and the way `new_cases` runs them, the Real names typed making their
    entries as they will: each file's finds, numbered as an Add will number them, so a skip ticked off here is the
    one the Add leaves, and its first passages as segments to draw, each replacement with what it was. A file that
    cannot be read yet has none. Nothing is written."""
    run = pseudo_run(root, body)
    out = []
    for entry in body.get("files") if isinstance(body.get("files"), list) else []:
        start = len(run.finds)
        try:
            if not isinstance(entry, dict) or not entry.get("data"):
                raise WorkbookError("")
            name, _data, read = read_entry(entry)
        except WorkbookError:
            out.append({"finds": [], "turns": []})
            continue
        who = str(entry.get("pseudonym") or "").strip()
        stem, dot, _ext = name.rpartition(".")
        if dot and stem:
            run.text(stem, who, {"participant": who, "part": "file"})
        interview = run.text(str(entry.get("interview") or ""), who, {"participant": who, "part": "interview"})
        given = entry.get("speakers") if isinstance(entry.get("speakers"), dict) else None
        roles = convert_mod.speaker_roles(read["turns"], given, "", None if given else "")
        pseudo_read(run, who, interview, read, roles)
        finds = run.finds[start:]
        first: dict = {}
        for i, (n, _s, _w) in enumerate(read["turns"]):
            first.setdefault(n, i + 1)
        shown = [{"text": pseudo_segments(w, [f for f in finds if f["where"].get("part") == "words"
                                               and f["where"].get("turn") == i + 1])}
                 for i, (_n, _s, w) in enumerate(read["turns"][:convert_mod.PREVIEW])]
        # each speaker by their name in the file, the passage their name was met at and what it becomes
        speakers = [{"name": n, "turn": at, "segments": pseudo_segments(n, [f for f in finds if f["where"].get("part") == "speaker"
                                                                           and f["where"].get("turn") == at])}
                    for n, at in first.items()]
        speaks = lambda turn: sum(1 for t in read["turns"] if t[0] == read["turns"][turn - 1][0])
        out.append({"finds": [dict(f, speaks=speaks(f["where"]["turn"])) if f["where"].get("part") == "speaker"
                              and f["where"].get("turn") else f for f in finds], "turns": shown, "speakers": speakers})
    counts = run.counts()
    return {"files": out, "entries": len(run.entries), "replaced": counts["replaced"], "left": counts["left"],
            "list": pseudo_view(run.entries, False)}


def api_names(body: dict) -> dict:
    """The project's list of names, `op` of `list`, `set`, `remove`, `check`, `replace`, `preview`, `read-key` or
    `key-file`, with `root`, the project's id. The list is the file `idiograph-names.json` in the project's folder
    (namesui). The app's own calls see the list in full. A call with a `tool` (the command line and the MCP server)
    is told counts and the entries' numbers only, never a real name, and cannot add one: `set`, `preview`,
    `read-key` and `key-file` are the app's alone, since an agent that types a real name has sent it to a model.

    `list` answers the entries. `set` takes `entries`, the whole list, each `{"real": [spellings], "to", "for", "case"}`
    (`for` a participant's pseudonym, none for everyone, `case` Match case), and keeps it, with `dry_run` writing
    nothing. `remove` takes `entries`, the numbers to take off. `check` searches the transcripts already in, counts
    only, and with `names_preview` the app's own call every find. `replace` replaces them, the finds `skip` names
    left as written, after a copy of each workbook changed is kept in its participant's `_Archive`
    (`pseudo_replace`), `dry_run` answering what `check` answers. `preview` takes Add's `files`, or New project's with
    its `folder`, and answers each file's finds (`pseudo_preview`). `read-key` takes a CSV or Excel key's `name` and
    `data` in base64 and answers the entries it holds, writing nothing, and `key-file` answers the list as a
    two-column CSV."""
    op = str(body.get("op") or "list")
    agent = bool(agent_marks(body)[0])
    if op == "preview":
        if agent:
            raise WorkbookError(i18n.t("names.agent_adds"))
        root = srv.project_named(body["root"]) if body.get("root") else None
        if root is None and str(body.get("folder") or "").strip():
            there = Path(str(body["folder"])).expanduser()
            root = there if there.is_dir() and (there / srv.PROJECT_FILE).is_file() else None
        return pseudo_preview(root, body)
    root = asked_root(body, write=op in ("set", "remove", "replace"))
    if root is None:
        raise WorkbookError(i18n.t("server.folder_nothing_added"))
    if srv.is_demo_root(root):
        raise WorkbookError(i18n.t("names.demo_fixed"))
    entries = pseudo_list(root)
    try:
        if op == "list":
            # the participants, by pseudonym, an entry can be for
            who = sorted({w for w, _f, _b in pseudo_books(root)})
            return {"entries": pseudo_view(entries, agent), "count": len(entries), "participants": who}
        if op == "check":
            run, changes = pseudo_check(root, entries)
            shown = body.get("names_preview") is True and not agent
            return dict({"names": pseudo_names_answer(run, agent, shown), "entries": len(entries),
                         "participants": len(changes)}, **({"list": pseudo_view(entries, False)} if shown else {}))
        if op == "replace":
            skip = names_mod.read_skip(body.get("skip"))
            if body.get("dry_run") is True:
                run, changes = pseudo_check(root, entries, skip)
                return {"names": pseudo_names_answer(run, agent, False), "dry_run": True, "replaced": False,
                        "participants": len(changes)}
            tool, request = agent_marks(body)
            done = pseudo_replace(root, entries, skip, tool, request)
            return {"names": pseudo_names_answer(done["run"], agent, False), "dry_run": False, "replaced": True,
                    "participants": len(done["participants"]), "failed": done["failed"]}
        if op == "remove":
            wanted = body.get("entries")
            wanted = wanted if isinstance(wanted, list) else [wanted]
            nums = set()
            for n in wanted:
                try:
                    nums.add(int(n))
                except (TypeError, ValueError):
                    raise WorkbookError(i18n.t("names.no_entry", n=n)) from None
            for n in sorted(nums):
                if not 1 <= n <= len(entries):
                    raise WorkbookError(i18n.t("names.no_entry", n=n))
            kept = [e for i, e in enumerate(entries) if i + 1 not in nums]
            dry = body.get("dry_run") is True
            if not dry:
                with writing(root=root):
                    names_mod.save_at(root, kept)
            return {"removed": len(nums), "dry_run": dry, "entries": pseudo_view(kept, agent), "count": len(kept)}
        if agent:
            raise WorkbookError(i18n.t("names.agent_adds"))
        if op == "set":
            fresh = names_mod.clean_entries(body.get("entries"))
            dry = body.get("dry_run") is True
            if not dry:
                with writing(root=root):
                    names_mod.save_at(root, fresh)
            return {"entries": pseudo_view(fresh, False), "count": len(fresh), "dry_run": dry}
        if op == "read-key":
            name = file_name(body.get("name"))
            return {"entries": pseudo_view(names_mod.read_key(name, file_bytes(body, name)), False)}
        if op == "key-file":
            return {"csv": names_mod.write_key(entries), "count": len(entries)}
    except names_mod.NamesError as exc:
        raise WorkbookError(str(exc)) from None
    raise WorkbookError(i18n.t("names.op"))


# ---------------------------------------------------------- REFI-QDA projects (21 October)

# A project from ATLAS.ti, NVivo or MAXQDA, exported as a REFI-QDA project (.qdpx), brought in as
# participants, each source one participant's transcript (see `qdpx.py`), through Add's own path: a
# copy of the .qdpx in `Source/<interview>/`, the raw source and the workbook, a further interview of
# a participant there already added to theirs. Then the statements and quotes the choices make, the
# memos to a text file in `Source/`, the recordings copied in for the player, and with `pets` a PETs
# board "From <package>" made of the code groups. The .qdpx is only read. A failure takes away what
# the import wrote and puts back what it changed. Adam's rulings of 21 October set the defaults.
QDPX_CHOICES = {"codes": (qdpx_mod.CODES, "statements"), "comments": (qdpx_mod.COMMENTS, "notes"),
                "loose": (qdpx_mod.LOOSE, "blank"), "memos": (qdpx_mod.MEMOS, "source"),
                "recordings": (qdpx_mod.RECORDINGS, "copy")}
QDPX_WORDS = {"notes": ("an exploratory note", "exploratory notes"), "statements": ("an experiential statement", "experiential statements")}


def qdpx_asks(body: dict) -> dict:
    """An import's choices as a call gives them, each refused in one line when it is not one offered,
    the default when left out: `codes`, `comments`, `loose`, `memos`, `recordings`, `pets`, `user`,
    `speakers` and `sources`, a list of `{"source", "pseudonym", "number", "timepoint", "interview"}`."""
    out = {}
    for key, (offered, default) in QDPX_CHOICES.items():
        value = " ".join(str(body.get(key) or "").split()).lower() or default
        if value not in offered:
            raise WorkbookError(i18n.t("server.choice_not", key=key, choices=formats.list_words(offered, "or"), given=body.get(key)))
        out[key] = value
    out["pets"] = body.get("pets") is True
    out["user"] = " ".join(str(body.get("user") or "").split())
    out["speakers"] = body.get("speakers") if isinstance(body.get("speakers"), dict) else None
    rows = body.get("sources")
    if rows is not None and not (isinstance(rows, list) and all(isinstance(r, dict) for r in rows)):
        raise WorkbookError(i18n.t("server.sources_shape"))
    out["sources"] = rows or []
    return out


def qdpx_view(src: dict, mapped: dict | None, roles: dict, as_name: str, form: str | None = None) -> dict:
    """A source as the card and an agent's dry run show it: its place, name and kind, its passages,
    speakers with their roles, coders, and the first passages as they will land, or why it is left out,
    their times as `form` says, the project's timecodes."""
    view = {"source": src["n"], "name": src["name"], "kind": src["kind"]}
    if mapped is None:
        return view
    # the interview's name an import guesses from the source's when none is given, which the card shows
    view["interview"] = src.get("interview") or convert_mod.interview_of(src["name"])
    turns = mapped["turns"]
    first = []
    for i, (name, seconds, words) in enumerate(turns[:convert_mod.PREVIEW]):
        one = {"speaker": as_name if roles.get(name) == "interviewer" else name, "time": wb_mod.timecode(seconds, form),
               "words": preview_words(words)}
        if mapped["notes"][i].get("en"):
            one["notes"] = mapped["notes"][i]["en"].split("\n")
        if mapped["pairs"].get(i):
            one["statements"] = [{"statement": p["es"], "quote": preview_words(p["kq"])} for p in mapped["pairs"][i]]
        first.append(one)
    return dict(view, count=len(turns), coders=mapped["counts"]["users"],
                speakers=[{"name": s["name"], "turns": s["turns"],
                           "role": convert_mod.SPEAKER_ROLES[roles.get(s["name"], "participant")]}
                          for s in convert_mod.speakers(turns)],
                recording=(src.get("media") or {}).get("name") or "", memos=len(src["memos"]), passages=first)


def qdpx_left(src: dict) -> str:
    """Why a source comes in as no participant, one plain line."""
    kinds = {"pdf": "a PDF document", "picture": "a picture"}
    if src["kind"] in kinds:
        return i18n.t("server.source_left_out_kind", name=src['name'], kind=kinds[src['kind']])
    if src["kind"] not in ("text", "audio", "video"):
        return i18n.t("server.kind_source_idiograph_does_read", name=src['name'])
    return i18n.t("server.source_left_out", name=src['name'], why=src['missing'] or 'it has no text')


def qdpx_rows(pkg: dict, rows: list[dict], tps: list[dict], readable: dict) -> list[dict]:
    """The sources chosen, each with its pseudonym, number, timepoint and interview, the interview
    guessed from the source's name when none is given, and a participant's second interview of
    that name given its timepoint's label or a number. Refused in one line for a source that is
    not there, that is left out, or that is named twice."""
    out, seen = [], set()
    names: dict[str, set] = {}
    for row in rows:
        n = row.get("source")
        try:
            n = int(n)
        except (TypeError, ValueError):
            raise WorkbookError(i18n.t("server.source_name_each_source_number", n=n)) from None
        if not 1 <= n <= len(pkg["sources"]):
            raise WorkbookError(i18n.t("server.source_project", n=n, count=len(pkg['sources'])))
        if n in seen:
            raise WorkbookError(i18n.t("server.source_named_twice", n=n))
        seen.add(n)
        if n not in readable:
            raise WorkbookError(i18n.t("server.source_why", n=n, why=qdpx_left(pkg['sources'][n - 1])))
        who = str(row.get("pseudonym") or "").strip()
        tp = timepoint_asked(row.get("timepoint"), tps) if longitudinal(tps) else 1
        given = str(row.get("interview") or "").strip()
        guess = pkg["sources"][n - 1].get("interview") or convert_mod.interview_of(pkg["sources"][n - 1]["name"])
        interview = given or guess
        taken = names.setdefault(who, set())
        if not given and interview.lower() in taken:
            label = interview_name(tps[tp - 1]["label"]) if longitudinal(tps) else None
            interview = label if label and label.lower() not in taken else interview
            k = 2
            while interview.lower() in taken:
                interview, k = f"{guess} {k}", k + 1
        taken.add(interview.lower())
        out.append({"source": n, "pseudonym": who, "number": row.get("number"), "timepoint": tp, "interview": interview})
    return out


def qdpx_counts(mapped: list[dict]) -> dict:
    """The counts of the sources chosen, summed."""
    total: dict = {}
    for m in mapped:
        for k, v in m["counts"].items():
            if isinstance(v, int):
                total[k] = total.get(k, 0) + v
            else:
                total[k] = sorted(set(total.get(k, [])) | set(v))
    return total


def plural_of(n: int, one: str) -> str:
    return f"{n} {one if n == 1 else one + 's'}"


def qdpx_lines(path: Path, pkg: dict, asks: dict, chosen: list[dict], mapped: list[dict], cases: int) -> list[str]:
    """What the import brings and what it leaves out, the plan's section 4: one line of what comes in
    and one of what does not, the lines each workbook's History keeps."""
    c = qdpx_counts(mapped) if mapped else {}
    srcs = [pkg["sources"][r["source"] - 1] for r in chosen]
    passages = sum(len(m["turns"]) for m in mapped)
    parts = [plural_of(cases, "participant"), plural_of(passages, "passage")]
    from_comments = c.get("comments", 0)
    if from_comments:
        parts.append(f"{plural_of(from_comments, 'comment')} as {QDPX_WORDS[asks['comments']][from_comments != 1]}")
    used = len(c.get("codes_used", []))
    if asks["codes"] == "statements" and used:
        made = c.get("statements", 0) - c.get("comment_statements", 0)
        parts.append(f"{plural_of(used, 'code')} as {plural_of(max(made, 0), 'experiential statement')}")
    elif asks["codes"] == "notes" and used:
        parts.append(f"{plural_of(used, 'code')} as {QDPX_WORDS['notes'][used != 1]}")
    if c.get("blank"):
        parts.append(f"{plural_of(c['blank'], 'quotation')} with no code or comment as {'a quote to pair' if c['blank'] == 1 else 'quotes to pair'}")
    memos = sum(len(s["memos"]) for s in srcs)
    if memos and asks["memos"] == "source":
        parts.append(f"{plural_of(memos, 'memo')} to Source")
    media = sum(1 for s in srcs if (s.get("media") or {}).get("part"))
    if media and asks["recordings"] == "copy":
        parts.append(f"{plural_of(media, 'recording')} copied to Source")
    lines = [f"From {path.name} ({pkg['package']}): " + ", ".join(parts) + "."]
    left = []
    codes_all = len([g for g, code in pkg["codes"].items() if code["codable"]])
    if asks["codes"] == "leave" and codes_all:
        left.append(f"{plural_of(codes_all, 'code')} left out")
    if c.get("not_participant"):
        left.append(f"{plural_of(c['not_participant'], 'coding')} on the interviewer's or another speaker's passages left out")
    if c.get("loose_left"):
        left.append(f"{plural_of(c['loose_left'], 'quotation')} with no code or comment left out")
    if c.get("other_users"):
        left.append(f"{plural_of(c['other_users'], 'coding')} by other coders left out")
    if c.get("cut"):
        left.append(f"{plural_of(c['cut'], 'quotation')} that {'crosses' if c['cut'] == 1 else 'cross'} passages cut")
    if c.get("outside"):
        left.append(f"{plural_of(c['outside'], 'quotation')} outside every passage left out")
    lost = sum(s["lost"] for s in srcs)
    if lost:
        left.append(f"{plural_of(lost, 'selection')} of a recording's times, or that could not be placed, left out")
    if memos and asks["memos"] == "leave":
        left.append(f"{plural_of(memos, 'memo')} left out")
    if media and asks["recordings"] == "leave":
        left.append(f"{plural_of(media, 'recording')} left out")
    away = sum(1 for s in srcs if s.get("media") and not s["media"].get("part"))
    if away:
        left.append(f"{plural_of(away, 'recording')} outside the package left out")
    for kind, word in (("pdf", "PDF document"), ("picture", "picture")):
        n = sum(1 for s in pkg["sources"] if s["kind"] == kind)
        if n:
            left.append(f"{plural_of(n, word)} left out")
    unread = sum(1 for s in pkg["sources"] if s["kind"] in ("text", "audio", "video") and s["text"] is None)
    if unread:
        left.append(f"{plural_of(unread, 'source')} with no text in the package left out")
    if pkg["variables"]:
        left.append(f"{plural_of(pkg['variables'], 'variable')} left out")
    if pkg["free_memos"]:
        left.append(f"{plural_of(len(pkg['free_memos']), 'free memo')} left out")
    # a PET's or a theme's description comes in on its label, and in thematic analysis a code's on the code list
    carried: set[str] = set()
    if asks["pets"] and asks["codes"] == "statements":
        def walk(tree: dict) -> None:
            if tree.get("code"):
                carried.add(tree["code"])
            for t in tree.get("groups") or []:
                walk(t)
        for g in qdpx_mod.code_groups(pkg):
            walk(g["tree"])
        if i18n.method_now() == "ta":
            carried |= {guid for guid, code in pkg["codes"].items() if code["codable"]}
    described = sum(1 for guid, code in pkg["codes"].items() if code["described"] and guid not in carried)
    if described:
        left.append(f"{plural_of(described, 'code description')} left out")
    if pkg["sets"] and not (asks["pets"] and asks["codes"] == "statements"):
        left.append(f"{plural_of(len(pkg['sets']), 'set')} left out")
    for key, word in (("links", "link"), ("graphs", "network")):
        if pkg[key]:
            left.append(f"{plural_of(pkg[key], word)} left out")
    if pkg["unsafe"]:
        left.append(f"{plural_of(len(pkg['unsafe']), 'file')} in the package with an unsafe name left out")
    if left:
        lines.append(left[0][0].upper() + left[0][1:] + "".join(f", {x}" for x in left[1:]) + ".")
    return lines


def put_pairs(book: Path, rows: dict, described: str = "") -> None:
    """Every statement and quote an import makes, each passage's pairs written as `save_turn` writes
    them (`workbook.pairs_to_cells`), in one save of the workbook, and with `described` the workbook's
    own description, for a workbook the import made."""
    if not rows and not described:
        return
    wb_mod.guard_lock(book)
    import openpyxl
    wb = openpyxl.load_workbook(book, rich_text=True)
    try:
        for (sheet, row), pairs in rows.items():
            ws = wb[sheet]
            cols = wb_mod.detect_columns(ws)
            es, kq = wb_mod.pairs_to_cells(pairs)
            ws.cell(row, cols["es"]).value = es
            if "kq" in cols:
                ws.cell(row, cols["kq"]).value = kq
        if described:
            wb.properties.description = described
        wb_mod._atomic_save(wb, book)
    finally:
        wb.close()


def qdpx_board(book: Path, made: list[dict], groups: list[dict], name: str, note: str, timepoint: int,
               aside: set | None = None, ids: dict | None = None) -> dict | None:
    """The PET draft (ruling 6): a board `name` on a participant's canvas at the timepoint, a PET a
    code group, holding the statements its codes made, laid out as a new board is and added through
    the boards' own op (`themes.version_op`, propose), the board on the canvas after. None when no
    group holds a statement of this participant. `made` is each statement with its sheet, row and code.
    A group's `tree` (`qdpx.set_tree`) gives its sub-PETs inside it, each label's description and note,
    and the statements of a code in `aside` go to the bin, as Idiograph's own export writes them
    (qdpxround, 9 November 2026). `ids`, when given, takes each PET's and sub-PET's code to its id on
    the board, for the GETs draft."""
    with themes_mod.scoped(board_timepoint(book, timepoint)):
        read = themes_mod.read_cards(book)
        keys = {}
        for card in read["cards"]:
            keys.setdefault((card["sheet"], card["row"], card["text"]), card["key"])
        by_code: dict[str, list[str]] = {}
        for one in made:
            key = keys.get((one["sheet"], one["row"], one["es"]))
            if key:
                by_code.setdefault(one["code"], []).append(key)
        seen: set[str] = set()

        def take(codes) -> list[str]:
            out = []
            for code in codes:
                for key in by_code.get(code, []):
                    if key not in seen:
                        seen.add(key)
                        out.append(key)
            return out

        def label(tree: dict, top: bool) -> dict | None:
            # a label with what it holds, its sub-labels the same way, one holding nothing left off, as lay_out leaves it
            members = take(tree["codes"])
            inner = [x for x in (label(t, False) for t in tree.get("groups") or []) if x]
            if not members and not inner:
                return None
            return {"label": themes_ai.clean_label(tree["name"]) or "Code group", "members": members, "groups": inner,
                    "description": tree.get("description") or "", "note": tree.get("note") or "",
                    "code": tree.get("code")}

        discarded = take(sorted(aside or ()))
        pets = []
        for group in groups:
            tree = group.get("tree") or {"name": group["name"], "codes": group["codes"], "groups": [],
                                         "description": group.get("description") or ""}
            pet = label(dict(tree, description=group.get("description") or tree.get("description") or ""), True)
            if pet:
                pets.append(pet)
        if not pets:
            return None
        version = themes_ai.lay_out(pets, read["cards"], discarded)
        # lay_out numbers the PETs g1 on and then each PET's sub-PETs in turn, and leaves off a label's
        # description and note, which each takes here by that same order
        order = list(pets)

        def nested(items: list[dict]) -> None:
            for item in items:
                order.append(item)
                nested(item["groups"])
        for pet in pets:
            nested(pet["groups"])
        by_id = {g["id"]: g for g in version["groups"]}
        for n, item in enumerate(order, start=1):
            g = by_id.get(f"g{n}")
            if g is None:
                continue
            if item["description"]:
                g[themes_mod.DESCRIPTION] = item["description"]
            if item["note"]:
                g["note"] = item["note"]
            if ids is not None and item.get("code"):
                ids[item["code"]] = g["id"]
        version.update(picks={}, quoted={})
        return themes_mod.version_op(book, themes_mod.PROPOSE, {"version": version, "note": note, "seed": False,
                                                               "name": name}, case_label(book))


def qdpx_import(root: Path, path: Path, body: dict, make: bool = False, made: str = "") -> dict:
    """A REFI-QDA project read for the card and an agent's dry run, or brought in with `make`. The
    one function the card, the command line (`idiograph qdpx`) and the MCP tool (`import_qdpx`) share.

    The answer carries the package, each source as `qdpx_view` shows it, the participants it would
    make or join, `lines`, what comes in and what is left out (see `qdpx_lines`), and `said`, the one
    line that holds the import back, else None. With `make` it writes as the comment above says and
    answers what it made, every refusal raised with nothing written. `made` says who made it for an
    agent's import, in each new workbook's description."""
    root, path = Path(root), Path(path)
    if path.suffix.lower() != ".qdpx" or not path.is_file():
        raise WorkbookError(i18n.t("server.file_refi_qda_project_name"))
    asks = qdpx_asks(body)
    try:
        pkg = qdpx_mod.read_package(path)
    except qdpx_mod.Unreadable as exc:
        raise WorkbookError(str(exc)) from None
    setting = str(srv.config().get("interviewer") or "").strip()
    as_name = setting or convert_mod.INTERVIEWER
    tps = timepoints_of(project_file(root))
    readable, views, roles_of = {}, [], {}
    # the project's list of names (namesrule): the package's code names, groups and sources' names now, each
    # source's passages, notes and quotes as it is mapped, the memos as they are written
    run = pseudo_run(root, body)
    who_of = pseudo_sources(asks["sources"])
    if run:
        pseudo_package(run, pkg, who_of)
    for src in pkg["sources"]:
        split = qdpx_mod.passages(src["text"]) if src["kind"] in ("text", "audio", "video") and src["text"] else []
        if not split:
            views.append(dict(qdpx_view(src, None, {}, as_name), left_out=qdpx_left(src)))
            continue
        first = [(p["name"], p["seconds"], p["words"]) for p in split]
        given = {k: v for k, v in (asks["speakers"] or {}).items() if k in {n for n, _s, _w in first}}
        roles = convert_mod.speaker_roles(first, given or None, setting)
        roles_of[src["n"]] = roles
        mapped = qdpx_mod.map_source(src, pkg, asks["codes"], asks["comments"], asks["loose"], asks["user"], roles)
        if run:
            mapped, roles = pseudo_mapped(run, who_of.get(src["n"]), src, mapped, roles, pkg)
            roles_of[src["n"]] = roles
        readable[src["n"]] = mapped
        views.append(qdpx_view(src, mapped, roles, as_name, wb_mod.timecodes_at(root)))
    chosen = qdpx_rows(pkg, asks["sources"], tps, readable)
    said = None if chosen else i18n.t("server.name_sources_bring_each_participant")
    for row in chosen:
        held = convert_mod.roles_said(roles_of[row["source"]])
        said = said or (f"Source {row['source']}: {held}" if held else None)
    entries = [{"name": f"{pkg['sources'][r['source'] - 1]['name']} (source {r['source']}) in {path.stem}.qdpx", "pseudonym": r["pseudonym"],
                "number": r["number"], "interview": r["interview"],
                "timepoint": tps[r["timepoint"] - 1]["label"] if longitudinal(tps) else None,
                "speakers": roles_of[r["source"]], "source": r["source"]} for r in chosen]

    def reader(entry: dict) -> tuple[str, Path, dict]:
        mapped = readable[entry["source"]]
        return entry["name"], path, {"kind": "qdpx", "turns": mapped["turns"], "headers": None, "mapping": None,
                                     "notes": mapped["notes"] if any(mapped["notes"]) else None}

    cases: list[dict] = []
    if chosen and not said:
        try:
            cases = new_cases(root, {"files": entries}, as_name, standing=standing_cases(root), reader=reader,
                              run=names_mod.Run([]))
        except WorkbookError as exc:
            said = str(exc)
        if run:
            # the package itself holds every source's names, so the copy kept in Source is the replaced text
            by_source = {e["name"]: e["source"] for e in entries}
            for case in cases:
                for each in case["interviews"]:
                    held = readable[by_source[each["name"]]]
                    each["data"], each["copy_suffix"] = names_mod.render(held["turns"], held["notes"]).encode("utf-8"), ".txt"
    # the lines of what comes in count the sources chosen, and with none chosen yet every source that can come in
    basis = chosen or [{"source": n, "pseudonym": str(n)} for n in readable]
    lines = qdpx_lines(path, pkg, asks, basis, [readable[r["source"]] for r in basis],
                       # a source with no pseudonym yet counted as a participant of its own, as the card shows it
                       len(cases) or len({r["pseudonym"] or f"#{r['source']}" for r in basis}))
    source_of = {e["name"]: e["source"] for e in entries}
    answer = {"file": path.name, "package": pkg["package"], "origin": pkg["origin"], "sources": views,
              "choices": {k: asks[k] for k in ("codes", "comments", "loose", "memos", "recordings", "pets", "user")},
              "participants": [{"label": c["label"], "joins": c["joins"],
                                "interviews": [{"interview": i["interview"], "source": source_of.get(i["name"], 0),
                                                "timepoint": i.get("timepoint", 1)} for i in c["interviews"]]}
                               for c in cases],
              "groups": [g["name"] for g in qdpx_mod.code_groups(pkg)] if asks["codes"] == "statements" else [],
              "lines": lines, "said": said, **pseudo_answer(run, body)}
    asks["names"] = run.entries
    if not make:
        return answer
    if said:
        raise WorkbookError(said)
    return dict(answer, made=qdpx_write(root, path, pkg, asks, cases, entries, readable, lines, made))


def qdpx_write(root: Path, path: Path, pkg: dict, asks: dict, cases: list[dict], entries: list[dict],
               readable: dict, lines: list[str], made_by: str) -> list[str]:
    """The import written, as Add writes its rows, then each participant's statements and quotes, its
    History line in its progress file, the memos, the recordings and the PET draft, all under the
    project's lock and each participant's. A failure puts back what it changed and takes away what
    it made, and says one line. Answers each participant's label."""
    as_name = str(srv.config().get("interviewer") or "").strip() or convert_mod.INTERVIEWER
    books = [c["raw"] or c["path"] / "Source" / f"P{c['number']} {c['pseudonym']} - transcript.xlsx"
             for c in cases if c["joins"]]
    marks = [locks.root_lock(root)] + [wb_mod.case_lock(b) for b in books]
    were = [(p, p.exists(), p.parent.exists()) for p in marks]
    made: list[Path] = []
    back: list = []
    done: list[dict] = []
    record = {"when": datetime.now().astimezone().isoformat(timespec="seconds"), "from": path.name,
              "package": pkg["package"], "lines": lines, **({"by": made_by} if made_by else {})}
    try:
        with writing(root=root, books=books):
            ours = team_sync.adding(root, [c["folder"] for c in cases if not c["joins"]])
            try:
                for case in cases:
                    if case["joins"]:
                        folder = case["path"]
                        raw = case["raw"] or folder / "Source" / f"P{case['number']} {case['pseudonym']} - transcript.xlsx"
                        book = case["book"]
                        if book is not None:
                            # the progress file as it was before the import, put back on a failure
                            back.append(progress_step(book))
                        add_interviews(case, as_name, back)
                        if book is None:
                            book = wb_mod.create_from_source(raw, wb_mod.suggested_output(raw))
                            back.append(("file", book))
                            place_timepoints(book, case["interviews"])
                    else:
                        write_case(root, case, as_name, made)
                        folder = root / case["folder"]
                        book = wb_mod.suggested_output(folder / "Source" / f"P{case['number']} {case['pseudonym']} - transcript.xlsx")
                    done.append(qdpx_case(path, pkg, asks, case, entries, readable, book, folder, back, record, made_by))
                if asks["pets"] and asks["codes"] == "statements" and done:
                    if i18n.method_now() == "ta":
                        qdpx_themes(root, path, pkg, done, back)
                    elif not longitudinal(timepoints_of(project_file(root))):
                        qdpx_gets(root, path, pkg, done, back)
            except Exception:
                unadd(made, back)
                team_sync.unadding(root, ours)
                raise
    except Exception as exc:
        for lock, was, held in were:
            with contextlib.suppress(OSError):
                if not was:
                    lock.unlink(missing_ok=True)
                if not held:
                    lock.parent.rmdir()
        if isinstance(exc, WorkbookError):
            raise
        raise WorkbookError(i18n.t("server.idiograph_could_bring_nothing_written", name=path.name)) from None
    return [c["label"] for c in cases]


def qdpx_case(path: Path, pkg: dict, asks: dict, case: dict, entries: list[dict], readable: dict, book: Path,
              folder: Path, back: list, record: dict, made_by: str) -> None:
    """One participant's part of an import once its sheets stand: the statements and quotes, the
    History line, the memos, the recordings and the PET draft, each step in `back` as it is taken."""
    rows: dict = {}
    statements: list[dict] = []
    by_name = {e["name"]: e for e in entries}
    memos: list[str] = []
    for each in case["interviews"]:
        entry = by_name[each["name"]]
        src, mapped = pkg["sources"][entry["source"] - 1], readable[entry["source"]]
        for i, pairs in mapped["pairs"].items():
            rows[(each["interview"], i + 2)] = pairs
        for i, items in qdpx_codes(pkg, mapped, asks).items():
            statements += [{"sheet": each["interview"], "row": i + 2, "es": es, "code": code,
                            "timepoint": each.get("timepoint", 1)} for es, code in items]
        if asks["memos"] == "source":
            for g in src["memos"]:
                note = pkg["notes"].get(g)
                if note and note["text"]:
                    kept = lambda t: names_mod.plain(t, asks.get("names") or [], case["pseudonym"])
                    head = f"{each['interview']}, {kept(note['name'])}" if note["name"] else each["interview"]
                    memos.append(f"{head}\n\n{kept(note['text'].strip())}\n")
        media = src.get("media") or {}
        if asks["recordings"] == "copy" and media.get("part"):
            place = folder / "Source" / each["interview"] / "Source"
            if not place.is_dir():
                place.mkdir(parents=True)
                back.append(("folder", place))
            # under the participant's pseudonym and timepoint, never the package's own name (ayabuild12)
            named = recording_name(case["pseudonym"], each.get("timepoint", 1), project_timepoints(book), Path(media["name"]))
            target = place / named
            if target.exists():
                raise WorkbookError(i18n.t("server.another_s_recordings_already_2", name=named, label=case['label']))
            if not qdpx_mod.copy_media(path, media["part"], target):
                raise WorkbookError(i18n.t("server.recording_too_large_copy", name=media['name'], name2=path.name))
            back.append(("file", target))
            # the difference between the transcript's own times and the recording's, its offset (qdpx.offset_of)
            audio_mod.write_offset(place, mapped.get("offset") or 0.0)
            back.append(("file", place / audio_mod.OFFSET_FILE))
    described = "" if case["joins"] else (made_by or f"Imported from {path.name} ({pkg['package']}) on "
                                                     f"{datetime.now().day} {datetime.now():%B %Y}.")
    put_pairs(book, rows, described)
    if not case["joins"]:
        back.append(progress_step(book))
    progress = rounds_mod.load_progress(book)
    progress.setdefault("imports", []).append(dict(record, sheets=[each["interview"] for each in case["interviews"]]))
    rounds_mod.save_progress(book, progress)
    if memos:
        who = case["pseudonym"]
        target, k = folder / "Source" / f"{who} - memos.txt", 2
        while target.exists():
            target, k = folder / "Source" / f"{who} - memos {k}.txt", k + 1
        with open(target, "x", encoding="utf-8", newline="\n") as fh:
            fh.write(f"Memos from {path.name} ({pkg['package']})\n\n" + "\n".join(memos))
        back.append(("file", target))
    ids: dict[str, str] = {}
    # a thematic analysis project's themes are the project's, one board for every participant (qdpx_themes)
    if asks["pets"] and asks["codes"] == "statements" and i18n.method_now() != "ta":
        groups = qdpx_mod.code_groups(pkg)
        aside = qdpx_mod.set_aside(pkg)
        when = datetime.now()
        for tp in sorted({s["timepoint"] for s in statements}):
            with themes_mod.scoped(board_timepoint(book, tp)):
                side = themes_mod.themes_path(book)
            back.append(("progress", side, side.read_bytes() if side.exists() else None))
            note = f"From {path.name} ({pkg['package']}), a PET a code group, brought in on {when.day} {when:%B %Y}."
            qdpx_board(book, [s for s in statements if s["timepoint"] == tp], groups, f"From {pkg['package']}", note, tp,
                       aside, ids if tp == 1 else None)
    return {"book": book, "statements": statements, "ids": ids}


def qdpx_gets(root: Path, path: Path, pkg: dict, done: list[dict], back: list) -> dict | None:
    """The GETs draft (qdpxround, 9 November 2026): a new board on the project's GETs canvas, each set of PETs in
    the package (`qdpx.upper_groups`, as Idiograph writes each GET) a GET holding the PETs and sub-PETs it names
    that this import brought in, laid out as a new board is and added through the GETs' own op
    (`gets.propose`), made current. None when no set names a PET brought in. `done` is each participant's
    workbook and its PETs' ids by their codes (`qdpx_case`)."""
    uppers = qdpx_mod.upper_groups(pkg)
    if not uppers:
        return None
    books = gets_books(root)
    when = themes_mod.now_iso()
    data, _cases, _disk, _taken = gets_mod.assemble(root, books, when)
    case_of = {str(Path(b["workbook"]).resolve()): b["case"] for b in books}
    keys: dict[str, str] = {}
    for one in done:
        case = case_of.get(str(Path(one["book"]).resolve()))
        rec = (data.get("cases") or {}).get(case) or {}
        known = {p["id"] for p in rec.get("pets") or []}
        for code, gid in one["ids"].items():
            if gid in known:
                keys[code] = gets_mod.card_of(case, "group", gid)
    groups = []
    for g in uppers:
        members = [keys[c] for c in g["codes"] if c in keys]
        if members:
            groups.append({"label": themes_ai.clean_label(g["name"]) or "Code group", "members": members, "groups": [],
                           "description": g["description"], "note": g["note"]})
    if not groups:
        return None
    pile = gets_mod.blank_board(data, "draft", "", when)["cards"]
    said = {gets_mod.card_of(case, "group", p["id"]): gets_mod.layout_text(p["title"], themes_mod.description_of(p))
            for case, rec in (data.get("cases") or {}).items() for p in rec.get("pets") or []}
    cards = [{"key": k, "text": said.get(k, ""), "x": c["x"], "y": c["y"]} for k, c in pile.items()]
    laid = themes_ai.gets_ids(themes_ai.lay_out(groups, cards, [], size=gets_mod.card_height))
    for g, item in zip(laid["groups"], groups):
        if item["description"]:
            g[themes_mod.DESCRIPTION] = item["description"]
        if item["note"]:
            g["note"] = item["note"]
    side = gets_mod.gets_path(root)
    back.append(("progress", side, side.read_bytes() if side.exists() else None))
    day = datetime.now()
    note = f"From {path.name} ({pkg['package']}), a GET a set of PETs, brought in on {day.day} {day:%B %Y}."
    return gets_mod.propose(root, books, dict(laid, picks={}, rows={}), note)


def qdpx_themes(root: Path, path: Path, pkg: dict, done: list[dict], back: list) -> dict | None:
    """A thematic analysis project's part of an import once every participant's rows stand (qdpxround, 9 November
    2026): each code's description from the package into the code list where the list has none, through the
    list's own op (`codes.change`, describe), and the Themes draft, a new board on the Themes canvas, each set of
    codes a theme holding the extracts of its codes this import brought in, its sub-themes inside it, each theme's
    description and note, added through the board's own op (`gets.propose`) and made current. `done` is each
    participant's workbook and its statements with their codes (`qdpx_case`)."""
    books = gets_books(root)
    when = themes_mod.now_iso()
    side = codes_mod.path_of(root)
    back.append(("progress", side, side.read_bytes() if side.exists() else None))
    gets_side = gets_mod.gets_path(root)
    back.append(("progress", gets_side, gets_side.read_bytes() if gets_side.exists() else None))
    listed = codes_mod.ensure(root, books, when, tool="qdpx")
    have = codes_mod.by_norm(listed)
    ops, seen = [], set()
    for c in pkg["codes"].values():
        held = have.get(codes_mod.norm(c["name"]))
        if c["codable"] and c.get("description") and held is not None and not held["description"] and held["id"] not in seen:
            seen.add(held["id"])
            ops.append({"op": "describe", "code": held["id"], "description": c["description"][:codes_mod.DESCRIPTION_MAX]})
    if ops:
        codes_mod.change(root, books, ops, when, note=f"From {path.name} ({pkg['package']})", tool="qdpx")
    groups_in = qdpx_mod.code_groups(pkg)
    if not groups_in:
        return None
    data, _cases, _disk, _taken = gets_mod.assemble(root, books, when)
    case_of = {str(Path(b["workbook"]).resolve()): b["case"] for b in books}
    by_code: dict[str, list[str]] = {}
    for one in done:
        case = case_of.get(str(Path(one["book"]).resolve()))
        lines = ((data.get("cases") or {}).get(case) or {}).get("lines") or {}
        read = themes_mod.read_cards(one["book"])
        keys = {}
        for card in read["cards"]:
            keys.setdefault((card["sheet"], card["row"], card["text"]), card["key"])
        for s in one["statements"]:
            key = keys.get((s["sheet"], s["row"], s["es"]))
            if key and key in lines:
                by_code.setdefault(s["code"], []).append(gets_mod.card_of(case, "es", key))
    seen_keys: set[str] = set()

    def take(codes) -> list[str]:
        out = []
        for code in codes:
            for key in by_code.get(code, []):
                if key not in seen_keys:
                    seen_keys.add(key)
                    out.append(key)
        return out

    def theme(tree: dict) -> dict | None:
        members = take(tree["codes"])
        inner = [x for x in (theme(t) for t in tree.get("groups") or []) if x]
        if not members and not inner:
            return None
        return {"label": themes_ai.clean_label(tree["name"]) or "Code group", "members": members, "groups": inner,
                "description": tree.get("description") or "", "note": tree.get("note") or ""}
    made = [x for x in (theme(dict(g["tree"], description=g["description"] or g["tree"].get("description") or ""))
                        for g in groups_in) if x]
    if not made:
        return None
    # a Themes board holds the extracts placed on it alone, so the cards are those the themes hold
    texts = {}
    for case, rec in (data.get("cases") or {}).items():
        for lk, line in (rec.get("lines") or {}).items():
            texts[gets_mod.card_of(case, "es", lk)] = line.get("text") or ""
    cards = [{"key": k, "text": texts.get(k, ""), "x": 0, "y": 0} for k in sorted(seen_keys, key=gets_mod.case_order)]
    laid = themes_ai.gets_ids(themes_ai.lay_out(made, cards, [], size=gets_mod.card_height))
    order = list(made)

    def nested(items: list[dict]) -> None:
        for item in items:
            order.append(item)
            nested(item["groups"])
    for item in made:
        nested(item["groups"])
    for g, item in zip(laid["groups"], order):
        if item["description"]:
            g[themes_mod.DESCRIPTION] = item["description"]
        if item["note"]:
            g["note"] = item["note"]
    # each code's extracts in one place, as the Themes canvas keeps a code one card
    codes_mod.gather(laid, data)
    day = datetime.now()
    note = f"From {path.name} ({pkg['package']}), a theme a set of codes, brought in on {day.day} {day:%B %Y}."
    return gets_mod.propose(root, books, dict(laid, picks={}, rows={}), note)


def qdpx_codes(pkg: dict, mapped: dict, asks: dict) -> dict[int, list[tuple[str, str]]]:
    """Each passage's statements that codes made, as `(statement, code)`, for the PET draft."""
    if asks["codes"] != "statements":
        return {}
    by_name: dict[str, list[str]] = {}
    for guid, code in pkg["codes"].items():
        by_name.setdefault(code["name"], []).append(guid)
    used = set(mapped["counts"]["codes_used"])
    out: dict[int, list[tuple[str, str]]] = {}
    for i, pairs in mapped["pairs"].items():
        for pair in pairs:
            guid = next((g for g in by_name.get(pair["es"], []) if g in used), None)
            if guid:
                out.setdefault(i, []).append((pair["es"], guid))
    return out


def api_qdpx(body: dict) -> dict:
    """A REFI-QDA project brought into a project: `op` of `read` or `make`, and the choices
    `qdpx_import` takes. An agent names `root`, the project's id, and `path`, the .qdpx under the
    project's folder. The import card on New project and Add transcripts sends the file itself
    once, its `name` and its `data` in base64, and then the key its first read answered as `held`,
    with `root` in Add, or `folder` in New project once one is chosen (see `qdpx_card_root`). The
    card's make is Add's; New project's goes through its own make with `qdpx` (see `make_project`)."""
    op = str(body.get("op") or "read")
    if op not in ("read", "make"):
        raise WorkbookError(i18n.t("server.op_read_make"))
    if body.get("held") or body.get("data") is not None:
        key = str(body.get("held") or "") or qdpx_hold(body)
        path = qdpx_held(key)
        if op == "make":
            if not body.get("root"):
                raise WorkbookError(i18n.t("server.name_project_add_participants"))
            answer = qdpx_import(add_root(body), path, body, make=True)
            qdpx_let_go(key)
            return answer
        return dict(qdpx_import(qdpx_card_root(body, path), path, body), held=key)
    root = add_root(body)
    path = srv.abs_path(str(body.get("path") or ""))
    if not srv.inside(path, root):
        raise WorkbookError(i18n.t("server.file_outside_project_s_folder"))
    return qdpx_import(root, path, body, make=op == "make")


# The import card's .qdpx (21 October): a drop gives the page no path, so the page sends the file
# once and the server keeps it in a folder of its own under the system's temporary folder, by a key
# the card sends back with each read and with Create project or Add. A copy is taken away once its
# participants are made, the oldest when more are held, and every one as the server ends. The
# file he dropped is never touched, and the copy kept in each participant's Source is made from this.
QDPX_CARD_MAX = 256 * 1024 * 1024        # the most a .qdpx dropped on the card may weigh
QDPX_HELD_MOST = 4
QDPX_HELD: dict[str, Path] = {}
# the hook that lets every held copy go as the process ends, once taken (see `qdpx_hold`)
QDPX_AT_EXIT: list = []
_qdpx_held_lock = threading.Lock()


def qdpx_hold(body: dict) -> str:
    """The card's .qdpx kept, from its `name` and its `data` in base64, answering its key. Refused in
    one line for a file whose name does not end .qdpx, one that did not arrive whole, or one too large."""
    name = file_name(body.get("name"))
    if not name.lower().endswith(".qdpx"):
        raise WorkbookError(i18n.t("server.file_refi_qda_project_name"))
    try:
        data = base64.b64decode(str(body.get("data") or ""), validate=True)
    except (binascii.Error, ValueError):
        raise WorkbookError(i18n.t("server.idiograph_could_read", name=name)) from None
    if not data:
        raise WorkbookError(i18n.t("server.idiograph_could_read", name=name))
    if len(data) > QDPX_CARD_MAX:
        raise WorkbookError(i18n.t("server.too_large_bring_from_card", name=name))
    folder = Path(tempfile.mkdtemp(prefix="idiograph-qdpx-"))
    with open(folder / name, "xb") as fh:
        fh.write(data)
    with _qdpx_held_lock:
        if not QDPX_AT_EXIT:
            # the held copies let go as the process ends, a hook taken as Idiograph first holds one, so another
            # app's process, which imports this module from source, takes none (the sixth build, 23 October 2026)
            atexit.register(qdpx_let_all_go)
            QDPX_AT_EXIT.append(qdpx_let_all_go)
        QDPX_HELD[folder.name] = folder / name
        while len(QDPX_HELD) > QDPX_HELD_MOST:
            oldest = next(iter(QDPX_HELD))
            shutil.rmtree(QDPX_HELD.pop(oldest).parent, ignore_errors=True)
    return folder.name


def qdpx_held(key) -> Path:
    """The card's .qdpx by its key, refused in one line when it is no longer held."""
    with _qdpx_held_lock:
        path = QDPX_HELD.get(str(key or ""))
    if path is None or not path.is_file():
        raise WorkbookError(i18n.t("server.project_s_file_longer_held"), code="file_not_held")
    return path


def qdpx_let_go(key) -> None:
    """The card's copy taken away, once its participants are made."""
    with _qdpx_held_lock:
        path = QDPX_HELD.pop(str(key or ""), None)
    if path is not None:
        shutil.rmtree(path.parent, ignore_errors=True)


def qdpx_let_all_go() -> None:
    for key in list(QDPX_HELD):
        qdpx_let_go(key)


def qdpx_card_root(body: dict, path: Path) -> Path:
    """The project a card's read is for: Add's by its id, New project's folder once one is chosen,
    else the held copy's own folder, a root of no participants and one timepoint."""
    if body.get("root"):
        return add_root(body)
    if str(body.get("folder") or "").strip():
        return project_folder(body["folder"], srv.merge_config(srv.saved_config()))
    return path.parent


# ---------------------------------------------------------- export as REFI-QDA (8 November)

# Export as REFI-QDA, on a project's menu beside Share a copy (qdpxout, 8 November 2026): the project, or the
# participants chosen, as a REFI-QDA project (.qdpx) for NVivo, ATLAS.ti, MAXQDA and QualCoder (see
# `qdpx_out.py`), the recordings in it when asked. The project is only read. Idiograph's own window asks for
# the path in its save dialog and the server writes the file there through /api/qdpx-export, and a browser
# downloads it from QDPX_PATH. The command line's `project export-qdpx` and the MCP tool call the same.
QDPX_PATH = "/project/qdpx"


def qdpx_people(root: Path, names=None) -> list[dict]:
    """The participants an export takes, each `{"label", "book"}` with its annotated workbook, every one with
    a workbook when none is named, else those named by label or pseudonym, in the project's order. A name
    that is no participant's, or one with no workbook yet, is refused in one line."""
    root = Path(root)
    every = []
    for row in list_cases(root):
        if row["kind"] != "annotated":
            continue
        book = srv.abs_path(row["path"])
        if any(p["label"] == row["case"] for p in every):
            continue
        every.append({"label": row["case"], "book": book})
    named = send_names(names)
    if not named:
        return every
    out = []
    for want in named:
        low = want.lower()
        hits = [p for p in every if p["label"].lower() == low] or [p for p in every if gets_mod.who(p["label"]).lower() == low]
        if len(hits) != 1:
            raise WorkbookError(i18n.t("server.qdpx_out_no_participant", want=want) if not hits else
                                i18n.t("server.qdpx_out_names_many", want=want, names=formats.list_words(p["label"] for p in hits)))
        if hits[0] not in out:
            out.append(hits[0])
    return out


def qdpx_export_lines(answer: dict, dry_run: bool) -> list[str]:
    """What an export holds and what it leaves out, one line each, as the command line and the card say them."""
    c = answer["counts"]
    ta = answer["method"] == "ta"
    parts = [i18n.t("cli.n.participant", n=len(answer["participants"])), i18n.t("server.qdpx_out_sources", n=c["sources"])]
    if ta:
        parts.append(i18n.t("server.qdpx_out_codes", n=c["codes"], extracts=c["statements"]))
        if c["themes"]:
            parts.append(i18n.t("server.qdpx_out_themes", n=c["themes"]))
    else:
        parts.append(i18n.t("server.qdpx_out_statements", n=c["statements"]))
        if c["pets"]:
            parts.append(i18n.t("server.qdpx_out_pets", n=c["pets"]))
        if c["gets"]:
            parts.append(i18n.t("server.qdpx_out_gets", n=c["gets"]))
    if c["notes"]:
        parts.append(i18n.t("server.qdpx_out_notes", n=c["notes"]))
    if c["recordings"]:
        parts.append(i18n.t("server.qdpx_out_recordings", n=c["recordings"]))
    listed = ", ".join(parts)
    head = (i18n.t("server.qdpx_out_would", file=answer["file"], list=listed) if dry_run
            else i18n.t("server.qdpx_out_wrote", file=answer["file"], list=listed))
    lines = [head]
    said = {"no_quote": lambda n: i18n.t("server.qdpx_out_left_no_quote", n=n),
            "quote_missing": lambda n: i18n.t("server.qdpx_out_left_quote_missing", n=n),
            "across": lambda n: i18n.t("server.qdpx_out_left_across", n=n),
            "no_words": lambda n: i18n.t("server.qdpx_out_left_no_words", n=n),
            "sticky_notes": lambda n: i18n.t("server.qdpx_out_left_sticky", n=n),
            "participant_notes": lambda n: i18n.t("server.qdpx_out_left_pn", n=n),
            "recordings_left": lambda n: i18n.t("server.qdpx_out_left_large", n=n)}
    left = [word(c[key]) for key, word in said.items() if c.get(key)]
    if left:
        lines.append(i18n.t("server.qdpx_out_left", list=formats.list_words(left, "and")))
    return lines


def qdpx_export(root: Path, dest: Path | None = None, participants=None, recordings: bool = False,
                dry_run: bool = False, replace: bool = False) -> dict:
    """The project at `root`, or the participants named, as a REFI-QDA project written to `dest`, or with
    `dry_run` what it would hold, nothing written. The one function the card, the command line and the MCP
    tool share. A file at `dest` is refused unless `replace`, which the window's save dialog has asked. The
    project's files are only read, under the writers' lock, so no save lands half way through."""
    import qdpx_out
    root = Path(root)
    info, data = read_project(root), project_file(root)
    if dest is not None and not dry_run:
        dest = Path(dest)
        if not dest.parent.is_dir():
            raise WorkbookError(i18n.t("server.qdpx_out_no_folder", parent=dest.parent))
        if dest.is_dir() or (dest.exists() and not replace):
            raise WorkbookError(i18n.t("server.qdpx_out_there", name=dest.name))
    held = locks.root(root) if locks.root_lock(root).exists() else contextlib.nullcontext()
    with srv._lock, held:
        people = qdpx_people(root, participants)
        if not people:
            raise WorkbookError(i18n.t("server.qdpx_out_nobody"))
        # each participant's pen portrait goes as their case's description (pbiobuild), their picture never
        sets = people_view(root)
        for person in people:
            person["portrait"] = people_mod.find(sets, person["label"]).get("portrait") or ""
        method = method_of(data)
        with i18n.in_method(method):
            plan = qdpx_out.plan(root, info["name"], method, info["research_question"], people, timepoints_of(data),
                                 recordings=recordings is True,
                                 codebook=codes_mod.load(root) if method == "ta" else None, version=srv.VERSION)
            name = dest.name if dest is not None else qdpx_out.file_name(info["name"])
            answer = {"file": name, "method": method, "participants": [p["label"] for p in people],
                      "counts": plan["counts"], "dry_run": bool(dry_run or dest is None)}
            if not answer["dry_run"]:
                if dest.exists() and replace:
                    dest.unlink()
                answer["bytes"] = qdpx_out.write(plan, dest)
                answer["path"] = str(dest)
            answer["lines"] = qdpx_export_lines(answer, answer["dry_run"])
    return answer


def api_qdpx_export(body: dict) -> dict:
    """Export as REFI-QDA in Idiograph's own window: the project `root` names written straight to `to`, the path
    he chose in the save dialog, which has asked already whether to replace a file there, with `participants`
    those ticked and `recordings` the recordings ticked. With `dry_run`, what it would hold."""
    root = srv.project_named(body.get("root"))
    if body.get("dry_run") is True:
        return qdpx_export(root, None, body.get("participants") or None, body.get("recordings") is True, dry_run=True)
    to = str(body.get("to") or "").strip()
    if not to:
        raise WorkbookError(i18n.t("server.qdpx_out_where"))
    dest = srv.abs_path(to)
    if dest.suffix.lower() != ".qdpx":
        dest = dest.with_name(dest.name + ".qdpx")
    return qdpx_export(root, dest, body.get("participants") or None, body.get("recordings") is True, replace=True)


def qdpx_download(handler, query: dict) -> None:
    """Export as REFI-QDA in a browser: the project `root` names, with `card` the card's choice as JSON, written
    to a scratch file first and served from it in pieces. A refusal answers in JSON."""
    try:
        root = srv.project_named(query.get("root"))
        try:
            card = json.loads(str(query.get("card") or "{}"))
        except ValueError:
            card = {}
        card = card if isinstance(card, dict) else {}
    except srv.OutsideRoot as exc:
        return handler._json({"error": str(exc)}, 403)
    except WorkbookError as exc:
        return handler._json({"error": str(exc)}, 409)
    import qdpx_out
    name = qdpx_out.file_name(read_project(root)["name"])
    folder = Path(tempfile.mkdtemp(prefix="idiograph-qdpx-"))
    made = folder / name
    try:
        qdpx_export(root, made, card.get("participants") or None, card.get("recordings") is True)
        size = made.stat().st_size
        handler.send_response(200)
        handler.send_header("Content-Type", "application/zip")
        handler.send_header("Content-Length", str(size))
        handler.send_header("Content-Disposition", "attachment; filename*=UTF-8''" + quote(name))
        handler.send_header("Cache-Control", "no-store")
        handler.end_headers()
        with open(made, "rb") as fh:
            for block in iter(lambda: fh.read(1 << 20), b""):
                handler.wfile.write(block)
    except (BrokenPipeError, ConnectionAbortedError, ConnectionResetError):
        handler.close_connection = True
    except WorkbookError as exc:
        return handler._json({"error": str(exc)}, 409)
    finally:
        shutil.rmtree(folder, ignore_errors=True)


# ---------------------------------------------------------- rename a participant

# Rename, in a case's menu on its project's page (16 October, Adam's word on a tester's feedback, since
# a pseudonym given once sometimes changes): the participant's new pseudonym in every file that carries
# it, the speaker's name in the Name column of every sheet of the case's workbooks, the case's name in
# its themes file and the GETs file, his order of the rows and the recent list, and with the folder
# ticked the case folder and the files in it named after the participant, their sidecars with them. A
# folder kept keeps the new name in the project file's `names` (see `label_for`). A copy of every file
# it writes goes to `_Archive/` first, the app's backup convention, the case's for its own files and
# the project's for the GETs file and the project file. The interviewer's passages, every backup and
# every export already written stay as they are. Since renamefix (11 November 2026) every file that names
# the participant, beside their workbooks and at the project's root, the LGETs, the Trajectories board and
# the list of names to replace among them, is named in one place, `case_files`, which this follows.
RENAME_LABEL = "pre-rename"
WORD = case_files.WORD
renamed = case_files.renamed
relabel_all = case_files.relabel_all
names_label = case_files.names_label


def rename_folder_of(root: Path, label: str) -> Path:
    """The case folder at a project's root that the row `label` names, refused in one line for the
    demo, for a row that is a workbook in the root itself, which has no folder, and for a label no
    folder has now."""
    if srv.is_demo_root(root):
        raise WorkbookError(i18n.t("server.demo_s_names_fixed"))
    names = names_at(root)
    try:
        held = sorted(Path(root).iterdir())
    except OSError:
        held = []
    for p in held:
        if p.is_dir() and not p.name.startswith(".") and label_for(p, names) == label:
            return p
    if any(p.is_file() and p.stem == label for p in held):
        raise WorkbookError(i18n.t("server.only_participant_folder_their_own"))
    raise WorkbookError(i18n.t("server.participant_project_now_nothing_changed"))


def case_books(folder: Path) -> list[Path]:
    """Every workbook of a case the app reads and Rename writes: its annotated workbooks and any raw
    source in its folder, then the raw sources in its own `Source/`, never a backup, a lock or a hidden
    file (see `own_books`)."""
    return own_books(folder, "annotated") + own_books(folder, "raw") + own_books(folder / "Source", "raw")


def passages_said(counts: dict) -> str:
    """The passages of each sheet a speaker's name stands on, '54 passages of the "Initial" sheet and 30
    of the "2d" sheet', each sheet named as the bar names it (17 October, later)."""
    items = list(counts.items())
    parts = [i18n.t("server.rename.passages_of_sheet", n=items[0][1], sheet=items[0][0])]
    parts += [i18n.t("server.rename.more_of_sheet", n=n, sheet=sheet) for sheet, n in items[1:]]
    return formats.list_words(parts)


def books_said(folder: Path) -> dict:
    """Each workbook of a case as the Rename card names it, in the researcher's words and never by a
    file the app keeps (16 October, after the screenshot check): the annotated workbook, the transcript
    in its folder and the transcript in Source, in `case_books`'s order, a file's name after its kind
    only where the case has two of that kind in one place."""
    said = {}
    for books, kind in ((own_books(folder, "annotated"), i18n.t("server.rename.annotated_workbook")),
                        (own_books(folder, "raw"), i18n.t("server.rename.transcript")),
                        (own_books(folder / "Source", "raw"), i18n.t("server.rename.transcript_in_source"))):
        for book in books:
            said[book] = i18n.t("server.rename.kind_named", kind=kind, file=book.name) if len(books) > 1 else kind
    return said


def first_up(text: str) -> str:
    """A line's first letter in capitals, the rest as it is."""
    return text[:1].upper() + text[1:]


def sidecars_said(book: Path, said: str) -> str:
    """The Rename card's line for a workbook named after the participant, `said` as `books_said` names it, taking
    the new name, and what it keeps as it does, its progress, its PETs boards and its LPETs, where it has them, every
    file named after it moving with it (`case_files.sidecars`), each a whole sentence in the catalogue since
    i18nleft4, 2 November 2026."""
    with_it = [what for what, there in ((i18n.t("server.rename.progress"), rounds_mod.progress_path(book).is_file()),
                                        (i18n.t("server.rename.pets_boards_kept"), bool(case_files.boards_files(book))),
                                        (i18n.t("server.rename.lpets_kept"), gets_mod.lpets_path(book).is_file()))
               if there]
    if with_it:
        return first_up(i18n.t("server.rename.book_takes_name_keeps", book=said, kept=formats.list_words(with_it)))
    return first_up(i18n.t("server.rename.book_takes_name", book=said))


def recent_in(folder: Path) -> list[dict]:
    """The entries of the recent list whose workbook sits in a case folder."""
    out = []
    for r in srv.state().get("recent", []):
        if srv.inside(srv.abs_path(r.get("path", "")), folder):
            out.append(r)
    return out


def rename_plan(root: Path, folder: Path, name, with_folder: bool, cfg: dict) -> tuple[dict, dict]:
    """What a rename of the case in `folder` to `name` will change, said before anything is, and the
    plan its act follows, both from the files as they stand and nothing written. `lines` says each
    thing it writes in the researcher's words, never by a file the app keeps (16 October): the
    participant's name on the passages of each sheet of each workbook, the case's PETs boards, each file
    at the project's root that names them (`case_files.PROJECT`: the GETs, the LGETs, the Trajectories
    board, the list of names to replace and the project's own file) and the recent list, and
    `folder_lines` the folder and each workbook it moves when the folder is ticked, which keeps its
    progress, PETs boards and LPETs, and their picture on the Trajectories board, the page showing them
    under the first. Each state says exactly what its act writes, so the project's note of the new
    name, which a kept folder needs, leaves the list as the tick takes the folder. A name that is not
    yet one capitalised word says each move by what it moves alone. A file it would write that is there
    and cannot be read is kept in `unread`, which refuses the rename (see `rename_refusal`)."""
    names = names_at(root)
    label = label_for(folder, names)
    old, own = gets_mod.who(label), gets_mod.who(srv.display_case(folder.name))
    new = " ".join(str(name or "").split())
    good = bool(ONE_WORD.match(new)) and new != old
    interviewer = str(cfg.get("interviewer") or "")
    plan = {"root": root, "folder": folder, "label": label, "old": old, "own": own, "new": new,
            "new_label": relabel(label, new) if good else "", "books": [], "themes": [], "sides": [],
            "carried": [], "recent": [], "moves": [], "target": None, "unread": None}
    lines, folder_lines = [], []
    said = books_said(folder)
    books = list(said)
    plan["all"] = books
    # each line one thing that changes in plain words, the participant's name on the passages of each
    # sheet, the workbook it is in said after it only where more than one carries the name (17 October,
    # after the screenshot check found "The annotated workbook, the participant's name on ..." hard to read)
    named = {book: wb_mod.speaker_rows(book, old, interviewer) for book in books}
    several = sum(1 for counts in named.values() if counts) > 1
    for book in books:
        counts = named[book]
        if counts:
            plan["books"].append(book)
            lines.append(i18n.t("server.rename.name_on_in", old=old, passages=passages_said(counts), book=said[book])
                         if several else i18n.t("server.rename.name_on", old=old, passages=passages_said(counts)))
    # the labels the case goes by in its files, its own and any other a PETs boards file of any timepoint
    # gives it, which the GETs file keys it by (see `themes_case`), and every file beside each workbook
    # that names the participant inside, read now (`case_files.side_files`)
    plan["was"] = [label]
    for book in books:
        for kind, path in case_files.side_files(book, with_folder):
            try:
                data = case_files.read_json(path)
            except case_files.Unreadable as exc:
                plan["unread"] = plan["unread"] or exc.path
                continue
            plan["sides"].append((kind, book, path, data))
            held = str(data.get("case") or "").strip() if kind == "boards" else ""
            if held and held not in plan["was"]:
                plan["was"].append(held)
    boards = [book for book in books if case_files.boards_files(book)]
    for book in boards:
        plan["themes"].append(book)
        lines.append(i18n.t("server.rename.pets_boards") if len(boards) == 1
                     else i18n.t("server.rename.pets_boards_of", book=said[book]))
    # each file at the project's root that may name the participant, read now
    roots = []
    for entry in case_files.PROJECT:
        path = entry.path(root)
        try:
            roots.append((entry, path, case_files.read_json(path)))
        except case_files.Unreadable as exc:
            plan["unread"] = plan["unread"] or exc.path
    # with the folder ticked, the folder and every workbook named after the participant, each with every
    # file named after it in `Working/`, and their own picture on the Trajectories board, and a folder whose
    # name carries no pseudonym is kept and the name goes into `names`
    olds = [x for x in dict.fromkeys([old, own]) if x]
    target = None
    if with_folder:
        m = re.match(r"^(P\d+\s*-\s*)([A-Z][a-z]+)(.*)$", folder.name)
        to = new if good else ""
        if m and m.group(2) in olds:
            target = folder.with_name(m.group(1) + (to or m.group(2)) + m.group(3))
        elif re.search(WORD.format("|".join(re.escape(x) for x in olds)), folder.name):
            target = folder.with_name(renamed(folder.name, olds, to or own))
        if target is not None:
            plan["target"] = target if good else None
            folder_lines.append(i18n.t("server.rename.folder_becomes", old=srv.display_case(folder.name),
                                       new=srv.display_case(target.name)) if good
                                else i18n.t("server.rename.folder_takes_name", old=srv.display_case(folder.name)))
        for book in books:
            if renamed(book.name, olds, "\u0000") == book.name:
                continue
            # one line for the workbook, its progress, its PETs boards and its LPETs going with it, said in
            # words and never by the file's new name (17 October, after the screenshot check)
            folder_lines.append(sidecars_said(book, said[book]))
            for item in [book] + case_files.sidecars(book):
                if item.is_file() and good and item not in dict(plan["moves"]):
                    plan["moves"].append((item, item.with_name(renamed(item.name, olds, new))))
        traj = next((data for entry, _path, data in roots if entry.file == traj_mod.FILE), None)
        picture = case_files.picture_move(root, traj, plan, olds, new if good else own)
        if picture is not None:
            folder_lines.append(i18n.t("server.rename.picture_takes_name"))
            if good:
                plan["moves"].append(picture)
        # their own picture, the participant's set's, in the project's pictures folder (pbiobuild)
        own_file = next((data for entry, _path, data in roots if entry.file == srv.PROJECT_FILE), None)
        picture = case_files.set_picture_move(root, own_file, plan, olds, new if good else own)
        if picture is not None:
            folder_lines.append(i18n.t("server.rename.set_picture_takes_name"))
            if good:
                plan["moves"].append(picture)
    # a kept folder notes the new name in the project's file, and a name noted there before goes once
    # the folder takes the new name or the new name is the folder's own (`case_files.project_line`)
    plan["kept_folder"] = not with_folder or target is None
    for entry, path, data in roots:
        line = entry.line(data, plan)
        if line:
            # the project's own file may say two things, his order and the participant's own set (pbiobuild)
            lines += line if isinstance(line, list) else [line]
            plan["carried"].append((entry, path, data))
    plan["recent"] = recent_in(folder)
    if plan["recent"]:
        lines.append(i18n.t("server.rename.recent"))
    answer = {"case": label, "old": old, "new": new if good else "", "label": plan["new_label"],
              "lines": lines, "folder_lines": folder_lines, "folder": bool(with_folder and target is not None)}
    return answer, plan


def rename_refusal(root: Path, folder: Path, plan: dict, cfg: dict) -> str | None:
    """The one line a rename is refused with, or None: a name not typed, the one it has, not one
    capitalised word, the interviewer's, or another case's in the project, a file it would carry the
    participant through that is there and cannot be read (renamefix), the folder or a file moving while
    Working together is on, since the team knows a participant by their folder (`case_files.KEPT`), a
    workbook of the case Excel has open, its `~$` file beside it, and a folder or a file the move would land
    on that is there."""
    new, old = plan["new"], plan["old"]
    if not new:
        return i18n.t("server.type_new_name_nothing_changed")
    if new == old:
        return i18n.t("server.name_now_nothing_changed")
    if not ONE_WORD.match(new):
        return i18n.t("server.make_new_name_one_capitalised")
    if new.lower() == str(cfg.get("interviewer") or "").strip().lower():
        return i18n.t("server.interviewer_s_name_settings_cannot", who=new)
    names = names_at(root)
    try:
        others = [p for p in Path(root).iterdir() if p != folder and not p.name.startswith(".")]
    except OSError:
        others = []
    taken = {gets_mod.who(label_for(p, names)).lower() if p.is_dir() else p.stem.lower() for p in others}
    if new.lower() in taken:
        return i18n.t("server.another_participant_s_name_project", new=new)
    if plan.get("unread") is not None:
        return i18n.t("server.not_renamed_unread", name=plan["unread"].name)
    if (plan["target"] is not None or plan["moves"]) and case_files.team_on(root):
        return i18n.t("server.rename.team_folder")
    for book in plan["all"]:
        if wb_mod.lock_file(book).exists():
            return i18n.t("server.open_excel_close_excel_first_2", name=book.name)
    if plan["target"] is not None and plan["target"].exists():
        return i18n.t("server.folder_named_already_nothing_changed", name=srv.display_case(plan['target'].name))
    for _item, moved in plan["moves"]:
        if moved.exists():
            return i18n.t("server.already_nothing_changed", name=moved.name)
    return None


def keep_copy(path: Path, archive: Path, stamp: str, made: list) -> None:
    """A copy of a file in `archive`, `<stem> (pre-rename <date-time>)<suffix>`, as `archive_copy`
    names a workbook's, never over one there, the folder made when it is not there yet."""
    if not archive.exists():
        archive.mkdir(parents=True)
        made.append(archive)
    stem, suffix = (path.stem, path.suffix) if path.suffix != ".json" else (path.name[:-len(".json")], ".json")
    copy, n = archive / f"{stem} ({RENAME_LABEL} {stamp}){suffix}", 2
    while copy.exists():
        copy, n = archive / f"{stem} ({RENAME_LABEL} {stamp}-{n}){suffix}", n + 1
    shutil.copy2(path, copy)
    made.append(copy)


def unrename(back: list, made: list) -> None:
    """What a failed rename changed put back, the last step first: each file moved moved back, each file
    written given its bytes again, with its mode where the step kept it (the list of names to replace is
    its owner's alone, `case_files.snapshot`), and every copy and folder it made taken away."""
    for step in reversed(back):
        with contextlib.suppress(OSError):
            if step[0] == "move":
                os.replace(step[2], step[1])
            elif step[0] == "folder":
                os.rename(step[2], step[1])
            elif step[0] == "bytes":
                tmp = step[1].with_name(f".{step[1].name}.idiograph.tmp")
                mode = step[3] if len(step) > 3 else 0o666
                with os.fdopen(os.open(tmp, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, mode), "wb") as fh:
                    fh.write(step[2])
                if len(step) > 3:
                    os.chmod(tmp, mode)
                os.replace(tmp, step[1])
            elif step[0] == "file":
                step[1].unlink()
    for item in reversed(made):
        with contextlib.suppress(OSError):
            if item.is_dir():
                item.rmdir()
            else:
                item.unlink()


def rename_case(root: Path, folder: Path, name, with_folder: bool, cfg: dict, who: dict | None = None) -> dict:
    """Rename made (see `rename_plan` for what it changes): refused in one line with nothing changed
    (see `rename_refusal`), else a copy of every file it writes into `_Archive/`, then the Name cells,
    each file beside a workbook that names the participant (`case_files.side_files`), each file at the
    root that does (`case_files.PROJECT`) and the files named after the participant, under the case's
    lock and the project's, then the
    folder under the project's alone, since Windows renames no folder with a file open in it, and the
    recent list last. A write that fails puts back everything before it and says one line. The answer
    is the plan as it was said, `lines` and `folder_lines`, and the case's new label."""
    interviewer = str(cfg.get("interviewer") or "")
    back: list = []
    made: list = []
    books = case_books(folder)
    stamp = datetime.now().strftime("%Y%m%d-%H%M")
    try:
        with writing(root=root, books=books[:1]):
            answer, plan = rename_plan(root, folder, name, with_folder, cfg)
            said = rename_refusal(root, folder, plan, cfg)
            if said:
                raise WorkbookError(said)
            label, new_label, new = plan["label"], plan["new_label"], plan["new"]
            moves = dict(plan["moves"])
            target = plan["target"]
            case_archive, root_archive = folder / "_Archive", root / "_Archive"
            # what each file beside a workbook and each at the root becomes, worked out whole before anything
            # is written (`case_files`), so a copy is kept of exactly the files that change
            sides, roots = [], []
            for kind, book, path, data in plan["sides"]:
                after = case_files.carry_side(kind, book, data, plan)
                if after != data:
                    sides.append((kind, book, path, after))
            for entry, path, data in plan["carried"]:
                after = entry.carry(data, plan)
                if after != data:
                    roots.append((entry, path, after))
            for path in dict.fromkeys(plan["books"] + [path for _kind, _book, path, _after in sides]):
                keep_copy(path, case_archive, stamp, made)
            for entry, path, _after in roots:
                if entry.archive and path.is_file():
                    keep_copy(path, root_archive, stamp, made)
            # the speaker's name in every sheet of each workbook that carries it
            for book in plan["books"]:
                back.append(("bytes", book, book.read_bytes()))
                wb_mod.rename_speaker(book, plan["old"], new, interviewer)
            # the case's name in each PETs boards file of every timepoint, the workbook's new name in them and
            # in the LPETs where it moves, and a trim's or an assignment's copy in the case's _Archive found
            # again in the folder it moves to
            for kind, book, path, after in sides:
                back.append(case_files.snapshot(path))
                case_files.write_side(kind, book, path, after)
            # each file at the root that names the participant: the GETs, the LGETs, the Trajectories board,
            # the list of names to replace and the project's own file
            for entry, path, after in roots:
                back.append(case_files.snapshot(path))
                entry.write(root, path, after)
            # the files named after the participant, each workbook with its sidecars
            for item, moved in plan["moves"]:
                os.replace(item, moved)
                back.append(("move", item, moved))
            # the project's History (projhistory, 2 November 2026), under the same lock, put back with the rest
            back.append(hist_mod.snapshot(root))
            hist_mod.record(root, "participant rename",
                            [f"{label} renamed {new_label}" + (", the folder too." if target is not None else ".")]
                            + [f"{line}." for line in answer["lines"] + answer["folder_lines"]], who)
        if target is not None:
            with srv._lock, locks.root(root):
                os.rename(folder, target)
                back.append(("folder", folder, target))
    except Exception as exc:
        unrename(back, made)
        if isinstance(exc, WorkbookError):
            raise
        named = getattr(exc, "filename", None) and Path(exc.filename).name
        raise WorkbookError(i18n.t("server.not_renamed", name=named) if named
                            else i18n.t("server.not_renamed_a_file")) from None
    # the recent list, the app's own, its entries in the case pointing at the files where they are now
    landed = target or folder
    was = Path(folder).resolve()
    moved_to = {str(Path(item).resolve()): Path(moved).resolve() for item, moved in moves.items()}
    with srv._lock:
        held = srv.state()
        for r in held.get("recent", []):
            path = srv.abs_path(r.get("path", "")).resolve()
            if path != was and was not in path.parents:
                continue
            path = moved_to.get(str(path), path)
            r["path"] = srv.rel_path(Path(landed) / path.relative_to(was))
            r["case"] = new_label
        srv.save_state(held)
        _gets_books.pop(str(Path(root).resolve()), None)
    return dict(answer, case=new_label, old=label, path=srv.rel_path(landed))


def api_rename(body: dict) -> dict:
    """Rename, from a case's menu on its project's page (16 October): `root`, the project's id,
    `case`, the row's label, `name`, the new pseudonym, and `folder`, whether the case folder and the
    files named after the participant take it too. `op` `plan` answers what will change and writes
    nothing, and `rename` changes it (see `rename_case`)."""
    root = srv.project_named(body.get("root"))
    folder = rename_folder_of(root, " ".join(str(body.get("case") or "").split()))
    with_folder = body.get("folder") in (True, "true")
    if str(body.get("op") or "plan") == "plan":
        with srv._lock:
            return rename_plan(root, folder, body.get("name"), with_folder, srv.config())[0]
    return rename_case(root, folder, body.get("name"), with_folder, srv.config(), who=hist_mod.asker(body))


def passage_in(payload: dict, at: dict) -> bool:
    """Whether a case's transcript still has a participant passage at `at`, its sheet and row."""
    who = str(payload["config"].get("interviewer") or "").strip().lower()
    try:
        row = int(at.get("row"))
    except (TypeError, ValueError):
        return False
    for sheet in payload["sheets"]:
        if sheet["name"] == str(at.get("sheet") or ""):
            return any(r["row"] == row and r["name"] and r["name"].strip().lower() != who for r in sheet["rows"])
    return False


def api_open(body: dict) -> dict:
    """A case opened on Experiential statements, put at the head of the recent list. With `passage`,
    a sheet and a row, from a statement card's double-click or Go to the passage on the PETs or GETs
    canvas (16 October), it opens only while the transcript still has a participant passage there,
    and otherwise says one line and changes nothing, the recent list included."""
    path = case_path(body["path"])
    payload = case_payload(path)
    at = body.get("passage")
    if isinstance(at, dict) and not passage_in(payload, at):
        raise WorkbookError(i18n.t("server.statement_s_passage_longer_transcript"))
    remember(path)
    return payload


def api_create(body: dict) -> dict:
    """The create card's Make: a raw source made into its annotated workbook, and in a project of two
    or more timepoints its sheets placed at `timepoint`, the import card's choice, T1 when left out."""
    source = case_path(body["path"])
    out = case_path(body["out"]) if body.get("out") else wb_mod.suggested_output(source)
    timepoint = timepoint_asked(body.get("timepoint"), project_timepoints(source))
    wb_mod.create_from_source(source, out)
    if timepoint > 1:
        rounds_mod.tag_sheets(out, read_sheets(out)[1], timepoint)
    payload = case_payload(out)
    remember(out)
    return payload


def api_import(body: dict) -> dict:
    """A transcript in another shape, read for its card or made into a raw source beside it.

    `op` `read` answers the first turns as they are read, each speaker with their turns and their
    role, the interviewer guessed, the name each speaker's turns are written under as the interviewer,
    for a Word table, a CSV or an Excel file its headings and the role of each column, the format its
    times were found in and each time that cannot be read, the recordings beside the file, and `said`, one line, when Make is held back (see `import_plan`).
    `columns` is the card's list of a role a column (see `convert.choose`), `speakers` a role a
    speaker's name, Interviewer, Participant or Other speaker, `times` how the Time column is read,
    `audio` a recording and `offset` its offset in seconds. `make` writes `<file name>.xlsx` beside
    the file, never over one there, copies the recording into the case, and answers the raw source as
    the case list has it, for the create card to take on. One transcript is always one case.
    """
    path = case_path(body["path"])
    if body.get("op") == "pick-audio":
        # Choose on the card's Recording row: the Mac's file dialog, whose Cancel chooses nothing
        if srv.PLATFORM != "darwin":
            raise WorkbookError(srv.NO_FILE_DIALOG)
        picked = srv.PICK_FOLDER(i18n.t("server.choose_recording"), files=True)
        return {"chosen": picked is not None, "path": str(picked) if picked else ""}
    setting = str(srv.config().get("interviewer") or "").strip()
    asks = import_asks(body)
    read, out, said = import_read(path, asks["columns"], body.get("op") == "make", asks["times"], asks["sheet"])
    plan = import_plan(path, read, asks, setting)
    said = said or plan["said"]
    if body.get("op") == "make":
        if said:
            raise WorkbookError(said)
        import_make(path, read, out, plan, setting)
        # a later interview of a participant with a workbook joins it at its timepoint, and the page
        # opens the workbook on the new sheet, where the create card would have made one
        joined = {"joined": srv.rel_path(plan["joins"]), "sheet": plan["sheet"]} if plan.get("joins") else {}
        return dict({"source": {"path": srv.rel_path(out), "name": out.stem, "case": case_label(out),
                                "kind": "raw", "sheets": [plan.get("sheet") or convert_mod.SHEET], "locked": False,
                                "suggested": srv.rel_path(wb_mod.suggested_output(out))},
                     "timepoint": plan.get("timepoint", 1)}, **joined)
    return dict(turns_view(read, setting, wb_mod.timecodes_for(path)), **plan_view(plan), kind=read["kind"], file=path.name, out=out.name,
                said=said, audio_found=audio_choices(path), timepoints=timepoints_for_card(path))


def timepoints_for_card(path: Path) -> list[dict]:
    """The project's timepoints for a card's Timepoint chooser, each with whether the participant a
    file belongs to has an interview there already, empty in a project of one timepoint."""
    tps = project_timepoints(path)
    if not longitudinal(tps):
        return []
    have = timepoints_held(wb_mod.case_folder(path))
    return [dict(tp, held=tp["n"] in have) for tp in tps]


def timepoints_held(folder: Path) -> set[int]:
    """The timepoints a participant's folder has an interview at, from their one annotated workbook,
    none with no workbook or two."""
    books = own_books(folder, "annotated")
    if len(books) != 1:
        return set()
    try:
        placed = rounds_mod.sheet_timepoints(rounds_mod.read_raw(books[0]))
    except (ValueError, OSError):
        placed = {}
    return {placed.get(s, 1) for s in (read_book(books[0]) or {}).get("sheets") or []}


def import_asks(body: dict) -> dict:
    """What a call asks of an import, the card's and an agent's alike, each in the shape the readers take."""
    pick = lambda key, kinds: body.get(key) if isinstance(body.get(key), kinds) else None
    return {"columns": pick("columns", (dict, list)), "speakers": pick("speakers", dict),
            "interviewer": body.get("interviewer") if "speakers" not in body and "interviewer" in body else None,
            "times": pick("times", dict),
            "audio": str(body.get("audio") or "").strip(), "offset": body.get("offset", 0),
            "timepoint": body.get("timepoint"), "sheet": str(body.get("sheet") or "").strip() or None}


def import_read(path: Path, columns=None, make: bool = False, timing=None, sheet=None) -> tuple[dict, Path, str | None]:
    """A transcript file read as the import card reads it, the card's and an agent's import alike
    (see `cli.cmd_import`): what was read, the raw source it is made into beside it, and the one line
    that holds Make back, no turn read, two columns given one role, none the transcript, or the raw
    source already there, else None. `columns` is a list of a role a column or a `{role: index}`
    (see `convert.choose`), and `timing` how a Time column is read (see `convert.timing_of`). A file
    that cannot be read is refused for a make and said for a read. `sheet` names an Excel file's sheet, its first
    with anything in it when none is named."""
    if not path.is_file() or path.suffix.lower() not in convert_mod.FORMATS:
        raise WorkbookError(i18n.t("server.file_transcript_idiograph_reads"))
    out = convert_mod.output_for(path)
    try:
        read = convert_mod.read_file(path, columns, timing, sheet)
    except convert_mod.Unreadable as exc:
        if make:
            raise WorkbookError(str(exc)) from exc
        read = {"kind": convert_mod.kind_of(path), "turns": [], "headers": None, "mapping": None, "said": str(exc)}
    said = read.get("said") or (None if read["turns"] else str(convert_mod.unreadable(path)))
    if out.exists():
        said = i18n.t("server.name_there_already", name=out.name)
    return read, out, said


# The rest of what an import takes (20 October): each speaker's role, the recording and its offset.
# One transcript is always one case (Adam's ruling), so Make makes no case but the file's own.


def import_plan(path: Path, read: dict, asks: dict, setting: str) -> dict:
    """What an import takes beyond its columns, the card's and an agent's alike, and the one line
    that holds Make back, else None: each speaker's role (see `convert.speaker_roles`), the recording
    and its offset. Writes nothing."""
    turns = read["turns"]
    roles = convert_mod.speaker_roles(turns, asks.get("speakers"), setting, asks.get("interviewer"))
    said = convert_mod.roles_said(roles) if turns else None
    audio, offset = None, audio_mod.offset_value(asks.get("offset") if asks.get("offset") not in (None, "") else 0)
    if asks.get("audio"):
        audio = srv.abs_path(asks["audio"])
        if audio.suffix.lower() not in audio_mod.CONTENT_TYPES:
            said = said or i18n.t("server.recording_one_idiograph_plays_plays")
        elif not audio.is_file():
            said = said or i18n.t("server.recording")
    if offset is None:
        said, offset = said or i18n.t("server.give_offset_seconds_plus_minus"), 0.0
    timepoint, joins, sheet = import_timepoint(path, asks.get("timepoint"))
    named = recording_name(case_label(path), timepoint, project_timepoints(path), audio) if audio else None
    return {"roles": roles, "audio": audio, "audio_name": named, "offset": offset, "said": said, "case": case_label(path),
            "timing": read.get("timing") or convert_mod.timing_of(None),
            "timepoint": timepoint, "joins": joins, "sheet": sheet}


def import_timepoint(path: Path, asked) -> tuple[int, Path | None, str]:
    """The timepoint an import is for, and in a project of two or more the participant's workbook it
    joins when they have one already, with the sheet it adds, named by the timepoint's label, T2, or
    T2 2 for a second part. One transcript is always one participant's. In a project of one
    timepoint nothing joins and the sheet is the raw source's own, as it always was. Refused for a
    timepoint the project has not got, and for a participant with two workbooks."""
    tps = project_timepoints(path)
    timepoint = timepoint_asked(asked, tps)
    if not longitudinal(tps):
        return 1, None, convert_mod.SHEET
    folder = wb_mod.case_folder(path)
    books = own_books(folder, "annotated")
    if not books:
        return timepoint, None, convert_mod.SHEET
    if len(books) > 1:
        raise WorkbookError(i18n.t("server.more_than_one_annotated_workbook", label=label_for(folder)))
    return timepoint, books[0], free_sheet(books[0], tps[timepoint - 1]["label"])


def free_sheet(book: Path, label: str) -> str:
    """A sheet name a workbook has not got, the timepoint's label, then with 2, 3 after it."""
    taken = {str(n).lower() for n in (read_book(book) or {}).get("names") or []}
    base = interview_name(label) or "Interview"
    name, k = base, 2
    while name.lower() in taken:
        name, k = f"{base[:28]} {k}", k + 1
    return name


def plan_view(plan: dict) -> dict:
    """The plan as the card and an agent's dry run show it: each speaker's role, the cases, the
    recording and its offset."""
    return {"speaker_roles": plan["roles"], "case": plan["case"],
            "audio": srv.rel_path(plan["audio"]) if plan["audio"] else "", "offset": plan["offset"],
            "audio_name": plan.get("audio_name") or "",
            "timepoint": plan.get("timepoint", 1), "joins": srv.rel_path(plan["joins"]) if plan.get("joins") else "",
            "sheet": plan.get("sheet") or convert_mod.SHEET}


def audio_choices(path: Path) -> list[dict]:
    """The recordings an import may take, those beside the transcript and anywhere in its case's
    Source folder, a few levels down, each by its path and its name from the case's folder."""
    folder = wb_mod.case_folder(path)
    found: dict[str, Path] = {}
    for place, depth in ((path.parent, 0), (folder / "Source", 3)):
        stack = [(place, 0)]
        while stack:
            at, level = stack.pop()
            try:
                entries = sorted(at.iterdir())
            except OSError:
                continue
            for entry in entries:
                if entry.name.startswith((".", "~$")):
                    continue
                if entry.is_dir() and level < depth and entry.name not in ("_Archive", "Working"):
                    stack.append((entry, level + 1))
                elif entry.is_file() and entry.suffix.lower() in audio_mod.CONTENT_TYPES:
                    found.setdefault(str(entry.resolve()), entry)
    out = []
    for entry in sorted(found.values(), key=lambda q: str(q).lower()):
        try:
            shown = entry.resolve().relative_to(folder.resolve()).as_posix()
        except ValueError:
            shown = entry.name
        out.append({"path": srv.rel_path(entry), "name": shown})
    return out


def place_audio(case_folder: Path, audio: Path | None, offset: float, made: list[Path],
                sheet: str = convert_mod.SHEET, name: str | None = None) -> None:
    """A recording copied into a case where `audio.for_sheet` finds the raw source's sheet's, its
    offset beside it, never over another file of its name. A recording already there is left as it is.
    `name` is the name it is copied in under, the participant's pseudonym and timepoint (see `recording_name`),
    never the source's own since 9 November 2026."""
    if audio is None:
        return
    folder = case_folder / "Source" / sheet / "Source"
    if not folder.is_dir():
        folder.mkdir(parents=True)
        made.append(folder)
    name = name or recording_name(label_for(case_folder), 1, [], audio)
    target = folder / name
    if not (target.exists() and target.resolve() == audio.resolve()):
        if target.exists():
            raise WorkbookError(i18n.t("server.another_s_recordings_already_2", name=name, label=label_for(case_folder)))
        shutil.copy2(audio, target)
        made.append(target)
    there = (folder / audio_mod.OFFSET_FILE).exists()
    audio_mod.write_offset(folder, offset)
    if not there:
        made.append(folder / audio_mod.OFFSET_FILE)


def import_make(path: Path, read: dict, out: Path, plan, setting: str, made: str = "") -> Path:
    """Make writes the raw source, never over a file there, the interviewer's turns under Settings'
    name and every other speaker's marked, under the case's lock, and the recording copied into the
    case with its offset (see `import_plan`). `made` says who made it for an agent's import. `plan`
    as a string is the interviewer chosen, as a caller from before 20 October gives it. A failure
    takes away what this Make wrote."""
    if isinstance(plan, str):
        plan = import_plan(path, read, {"interviewer": plan}, setting)
    written: list[Path] = []
    back: list = []
    chosen = convert_mod.the_interviewer(plan["roles"])
    book, sheet = plan.get("joins"), plan.get("sheet") or convert_mod.SHEET
    # the project's list of names, applied as an Add applies it (namesrule): the turns, notes and speakers
    run = pseudo_run(srv.project_of(path), {})
    if run:
        who = label_for(wb_mod.case_folder(path)).split(" - ", 1)[-1]
        read, roles, _copy = pseudo_read(run, who, sheet, read, plan["roles"])
        plan = dict(plan, roles=roles)
        chosen = convert_mod.the_interviewer(roles)
    with writing(path):
        try:
            turns, marks = convert_mod.case_turns(read["turns"], plan["roles"], setting)
            try:
                convert_mod.write_sheets([(sheet, turns, read.get("notes"), setting if chosen else "", marks)], out, made)
            except FileExistsError as exc:
                raise WorkbookError(i18n.t("server.name_there_already", name=out.name)) from exc
            written.append(out)
            place_audio(wb_mod.case_folder(path), plan["audio"], plan["offset"], written, sheet, plan.get("audio_name"))
            if book is not None:
                # a later interview of a participant who has a workbook (a longitudinal project):
                # its sheet at the end of that workbook, kept in _Archive first, at its timepoint
                archive = wb_mod.case_folder(book) / "_Archive"
                if not archive.exists():
                    back.append(("archive", archive))
                back.append(("book", book, wb_mod.archive_copy(book, ADD_LABEL)))
                back.append(progress_step(book))
                wb_mod.add_from_source(out, [sheet], book)
                rounds_mod.tag_sheets(book, [sheet], plan.get("timepoint", 1))
        except Exception:
            unadd([], back)
            for done in reversed(written):
                if done.is_dir():
                    shutil.rmtree(done, ignore_errors=True)
                else:
                    done.unlink(missing_ok=True)
            raise
    return out


def progress_step(book: Path) -> tuple:
    """A step `unadd` takes back: the progress file beside a workbook as it was, or none."""
    side = rounds_mod.progress_path(book)
    return ("progress", side, side.read_bytes() if side.exists() else None)


def set_audio_offset(path: Path, sheet: str, value, dry_run: bool = False) -> dict:
    """A sheet's recording given a new offset, which playback adds to every time code, kept beside the
    recording so it stays with the case. Refused for a sheet with no recording and for an offset that
    is no number of seconds. With `dry_run` nothing is written. Answers the offset it had and the new."""
    found = audio_mod.for_sheet(path, sheet)
    if found is None or not srv.within_root(found):
        raise WorkbookError(i18n.t("server.recording_found", sheet=sheet))
    seconds = audio_mod.offset_value(value)
    if seconds is None:
        raise WorkbookError(i18n.t("server.give_offset_seconds_plus_minus"))
    folder = audio_mod.source_folder(path, sheet)
    was = audio_mod.offset_in(folder)
    if not dry_run and seconds != was:
        with writing(path):
            audio_mod.write_offset(folder, seconds)
    return {"sheet": sheet, "recording": found.name, "was": was, "offset": seconds, "changed": seconds != was,
            "file": srv.rel_path(folder / audio_mod.OFFSET_FILE)}


def api_audio_offset(body: dict) -> dict:
    """The recording's offset on Experiential statements' player, `path` the workbook, `sheet` and
    `offset` in seconds (see `set_audio_offset`)."""
    path = case_path(body["path"])
    return set_audio_offset(path, str(body.get("sheet") or ""), body.get("offset"), body.get("dry_run") is True)


def recording_checked(value) -> Path:
    """A recording a call names, by its path, refused in one line when it is not a file Idiograph plays: not there,
    not .m4a, .mp3, .wav or .m4b, or empty. Read only, the file is never moved or changed."""
    audio = srv.abs_path(value)
    if audio.suffix.lower() not in audio_mod.CONTENT_TYPES:
        raise WorkbookError(i18n.t("server.recording_one_idiograph_plays_plays"))
    try:
        size = audio.stat().st_size if audio.is_file() else -1
    except OSError:
        size = -1
    if size < 0:
        raise WorkbookError(i18n.t("server.recording"))
    if size == 0:
        raise WorkbookError(i18n.t("server.recording_empty", name=audio.name))
    return audio


def attach_sheet(path: Path, timepoint: int, interview) -> str:
    """The sheet of a participant's workbook that is their interview at a timepoint, named by `interview` when they
    have two at it. Refused in one line when they have none there or two and none is named."""
    sheets = (read_book(path) or {}).get("sheets") or []
    try:
        placed = rounds_mod.sheet_timepoints(rounds_mod.read_raw(path))
    except (ValueError, OSError):
        placed = {}
    at = [s for s in sheets if placed.get(s, 1) == timepoint]
    label = case_label(path)
    wanted = " ".join(str(interview or "").split())
    if wanted:
        found = [s for s in at if s.lower() == wanted.lower()]
        if not found:
            raise WorkbookError(i18n.t("server.attach_no_interview_named", label=label, interview=wanted,
                                       list=formats.list_words(at) or "none"))
        return found[0]
    if not at:
        raise WorkbookError(i18n.t("server.attach_no_interview_at", label=label, n=timepoint))
    if len(at) > 1:
        raise WorkbookError(i18n.t("server.attach_two_interviews", label=label, n=timepoint, list=formats.list_words(at)))
    return at[0]


def attach_audio(path: Path, file, timepoint=None, interview=None, replace: bool = False, offset=0,
                 dry_run: bool = False, tool: str = "", request: str = "") -> dict:
    """A recording copied onto a participant's interview already in (audioop, 9 November 2026), as an import's
    `audio` copies one as a transcript comes in (`place_audio`): named by the participant's pseudonym and the
    interview's timepoint, `Wren T2.m4a`, or `Wren.m4a` in a project of one timepoint, never the source's own
    name, in the sheet's Source folder where the player finds it, its offset beside it. The interview is the
    participant's at `timepoint` (T1 when left out), `interview` naming it when they have two there. Refused for a
    file that is not a recording Idiograph plays, an interview that has one already unless `replace`, in which case
    the one there is kept in `_Archive`, and the source file is only read. Kept in History under `imports`. With
    `dry_run` nothing is written and the answer says the name the copy will have."""
    tps = project_timepoints(path)
    n = timepoint_asked(timepoint, tps)
    sheet = attach_sheet(path, n, interview)
    audio = recording_checked(file)
    seconds = audio_mod.offset_value(offset if offset not in (None, "") else 0)
    if seconds is None:
        raise WorkbookError(i18n.t("server.give_offset_seconds_plus_minus"))
    label = case_label(path)
    name = recording_name(label, n, tps, audio)
    folder = audio_mod.source_folder(path, sheet)
    held = audio_mod.for_sheet(path, sheet)
    if audio.resolve() == (folder / name).resolve():
        raise WorkbookError(i18n.t("server.attach_already_that", label=label, sheet=sheet, name=name))
    if held is not None and not replace:
        raise WorkbookError(i18n.t("server.attach_has_one", label=label, sheet=sheet, name=held.name))
    answer = {"case": label, "sheet": sheet, "timepoint": n, "recording": name, "offset": seconds,
              "writes": srv.rel_path(folder / name), "replaces": held.name if held is not None else None}
    if dry_run:
        return dict(answer, dry_run=True, attached=False)
    case_folder = wb_mod.case_folder(path)
    moved: tuple[Path, Path] | None = None
    made: list[Path] = []
    with writing(path):
        # read again under the lock, so a write between a dry run and this one is seen
        held = audio_mod.for_sheet(path, sheet)
        if held is not None and not replace:
            raise WorkbookError(i18n.t("server.attach_has_one", label=label, sheet=sheet, name=held.name))
        progress_was = progress_step(path)
        offset_was = (folder / audio_mod.OFFSET_FILE).read_bytes() if (folder / audio_mod.OFFSET_FILE).exists() else None
        try:
            if held is not None:
                archive = case_folder / "_Archive"
                archive.mkdir(exist_ok=True)
                stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
                keep = archive / f"{held.stem} before {stamp}{held.suffix}"
                k = 2
                while keep.exists():
                    keep = archive / f"{held.stem} before {stamp} {k}{held.suffix}"
                    k += 1
                shutil.move(str(held), str(keep))
                moved = (held, keep)
                answer["kept"] = srv.rel_path(keep)
            place_audio(case_folder, audio, seconds, made, sheet, name)
            progress = rounds_mod.load_progress(path)
            progress.setdefault("imports", []).append(marked(
                {"when": datetime.now().astimezone().isoformat(timespec="seconds"), "recording": name, "sheet": sheet,
                 "timepoint": n, "attach": True, "replaced": held.name if held is not None else None}, tool, request))
            rounds_mod.save_progress(path, progress)
        except Exception:
            for done in reversed(made):
                done.unlink(missing_ok=True)
            if offset_was is not None:
                (folder / audio_mod.OFFSET_FILE).write_bytes(offset_was)
            if moved is not None:
                shutil.move(str(moved[1]), str(moved[0]))
            unadd([], [progress_was])
            raise
    return dict(answer, attached=True)


def api_audio_attach(body: dict) -> dict:
    """A recording attached to a participant's interview already in, `path` the workbook, `file` the recording,
    `timepoint`, `interview`, `replace` and `offset` (see `attach_audio`), with `dry_run`, and the agent's `tool` and
    `request` for History."""
    path = case_path(body["path"])
    tool, request = agent_marks(body)
    return attach_audio(path, body.get("file"), body.get("timepoint"), body.get("interview"), body.get("replace") is True,
                        body.get("offset"), body.get("dry_run") is True, tool, request)


def rename_quote_heading(path: Path, dry_run: bool = False, tool: str = "", request: str = "") -> dict:
    """The quotes column's heading renamed from Key quotes to Quote on every annotation sheet of one
    workbook (`workbook.quote_heading`, Adam's ruling of 23 October 2026), under the case's lock as every
    write is, refused while the workbook is open in Excel. A copy of the workbook goes into `_Archive`
    first, and the progress file records each sheet renamed under `edits`, row 1, with `heading`, one
    batch id, the backup, and the tool and his request when an agent asked. With `dry_run`, or with no
    sheet to rename, nothing is written. Answers each sheet as `quote_heading` does."""
    path = Path(path)
    if dry_run:
        return {"sheets": wb_mod.quote_heading(path, dry_run=True), "changed": False, "dry_run": True,
                "backup": None}
    with writing(path):
        # read again under the lock, so a write between a dry run and this one is seen
        sheets = wb_mod.quote_heading(path, dry_run=True)
        renamed = [s for s in sheets if s["change"] == "rename"]
        if not renamed:
            return {"sheets": sheets, "changed": False, "dry_run": False, "backup": None}
        backup = wb_mod.archive_copy(path, "pre-heading")
        sheets = wb_mod.quote_heading(path)
        progress = rounds_mod.load_progress(path)
        batch = f"heading-{datetime.now().strftime('%Y%m%d%H%M%S')}"
        when = datetime.now().isoformat(timespec="seconds")
        for s in (s for s in sheets if s["change"] == "rename"):
            record = {"sheet": s["sheet"], "row": 1, "old": s["was"], "new": s["now"], "when": when,
                      "heading": True, "batch": batch, "backup": backup.name}
            if tool:
                record.update(by="agent", tool=tool)
            if request:
                record["request"] = request
            progress.setdefault("edits", []).append(record)
        rounds_mod.save_progress(path, progress)
    return {"sheets": sheets, "changed": True, "dry_run": False, "backup": backup.name, "batch": batch}


def api_quote_heading(body: dict) -> dict:
    """The quotes column's heading renamed to Quote on every annotation sheet of the workbook at `path`,
    with `dry_run`, and `tool` and `request` for an agent's write (see `rename_quote_heading`)."""
    path = case_path(body["path"])
    return rename_quote_heading(path, body.get("dry_run") is True, themes_ai.one_line(body.get("tool") or ""),
                                themes_ai.one_line(body.get("request") or ""))


def commit_pairs(body: dict) -> list[dict] | None:
    """The turn's pairs as the page sends them, each a statement and its quote, or None from a
    page that sends the two fields as text."""
    pairs = body.get("pairs")
    if pairs is None:
        return None
    if not isinstance(pairs, list) or not all(isinstance(p, dict) for p in pairs):
        raise WorkbookError(i18n.t("server.turn_s_pairs_list_each"))
    return [{"es": str(p.get("es") or ""), "kq": str(p.get("kq") or "")} for p in pairs]


def api_commit(body: dict) -> dict:
    """A passage's statements, notes and quotes saved. `v`, from a page that sends it, is the
    version of the passage the page last read, and a save over a passage another window or an agent
    has changed since is refused with nothing written, the progress file included. The answer then
    carries `stale`, the passage as it now reads, for the page to show beside what was typed.

    A statement the save rewords in its own place (see `themes.reworded`) leaves one line in the
    History of every board that holds a card of it, the case's boards at its sheet's timepoint and
    the boards of each copy across the participants, named for the participant and its words before
    and after (histreplace, 30 October 2026, see `themes.edit_line`). The cards and the copies keep
    their words, so a board shows the change as ever. The copies' lines are written under the
    project's lock once the case's is let go, and a copy that cannot have it keeps no line, the save
    standing."""
    path = case_path(body["path"])
    pairs = commit_pairs(body)
    was = body.get("v")
    said = {}
    with writing(path):
        try:
            result = wb_mod.save_turn(path, body["sheet"], int(body["row"]),
                                      body.get("es"), body.get("en"), body.get("kq"), pairs=pairs,
                                      was=None if was is None else str(was), outline=True)
        except wb_mod.StaleTurn as exc:
            return {"error": str(exc), "stale": exc.now, "status": 409}
        # the counts below come from the workbook as just saved, never a second read of it (savespeed)
        outline = result.pop("outline")
        moved = result.pop("statements", None)
        edits = themes_mod.reworded(moved["before"], moved["after"]) if moved else {}
        if edits:
            said = edit_lines(path, {themes_mod.card_key(result["sheet"], int(result["row"]), i): pair
                                     for i, pair in edits.items()})
            try:
                themes_mod.statements_noted(path, result["sheet"], int(result["row"]), edits,
                                            gets_mod.who(case_label(path)))
            except (WorkbookError, OSError):
                pass
        progress = rounds_mod.load_progress(path)
        key = rounds_mod.row_key(body["sheet"], int(body["row"]))
        has = (any(p["es"].strip() for p in pairs) if pairs is not None
               else bool((body.get("es") or "").strip()))
        progress["rows"][key] = rounds_mod.HAS_CONTENT if has else rounds_mod.REVIEWED_EMPTY
        progress["last"] = {"sheet": body["sheet"], "row": int(body["row"])}
        if body.get("round"):
            # `away` is the seconds the page was hidden or unfocused since the last save, counted
            # by the browser, so a window left open while he is elsewhere is not measured as work.
            rounds_mod.record_work(progress, int(body["round"]), time.time(),
                                   float(body.get("away") or 0))
        rounds_mod.save_progress(path, progress)
    root = project_root(path) if said else None
    if root is not None:
        try:
            with writing(root=root):
                statements_noted(path, said)
        except (WorkbookError, OSError):
            pass
    # in a thematic analysis project a name typed as New code joins the code list (codes, 2 November 2026)
    names = [p["es"] for p in result.get("pairs") or [] if str(p.get("es") or "").strip()]
    there = project_root(path) if names else None
    if there is not None and read_project(there).get("method") == "ta":
        try:
            with writing(root=there):
                result["codes_added"] = codes_mod.names_typed(there, names, themes_mod.now_iso())
                # the codes the save put on an extract become the codes used last, for the quick keys (quickkeysB)
                if moved:
                    result["recent"] = codes_mod.note_used(there, codes_mod.put_on(moved["before"], moved["after"]),
                                                           themes_mod.now_iso())
        except (WorkbookError, OSError):
            pass
    result["progress"] = refresh_summary(path, outline)
    result["state"] = progress["rows"][key]
    return result


def api_crux(body: dict) -> dict:
    """Add a highlight, remove one, or toggle the selection the way the first version did.

    `op` is optional. Without it the call behaves exactly as it always has, so a page in front of a
    server that has not been restarted keeps working. With `add` or `remove` it does that one thing
    to the characters the selection covers, which is what shortens a run rather than clearing it
    whole. The answer carries the op it performed, so the page can tell a server that read it from
    one that ignored it.
    """
    path = case_path(body["path"])
    with writing(path):
        return wb_mod.save_crux(path, body["sheet"], int(body["row"]),
                                int(body["start"]), int(body["end"]), body.get("text"),
                                op=body.get("op"))


def api_edit_turn(body: dict) -> dict:
    """Correct the text of one turn, in the transcript cell itself, and its timecode with it.

    The cell keeps its style and gains no fill, the highlights are found again by phrase, and the
    old and the new text both go into the sidecar under `edits`, so a case rebuilt from its raw
    source can be reconciled with what was corrected here. `timecode` is optional: a changed one is
    written in the representation the cell already holds and recorded beside the text, and one
    that cannot be read is refused with nothing written. The answer carries the row as the reader
    renders it, its timecode included, so the page redraws that one turn and nothing else.

    An agent's call (26 October, `turn edit`) adds `dry_run`, which answers the same with nothing
    written and the words and timecode the turn holds now, `old` and `old_time`, and `tool` and
    `request`, which its record in the sidecar carries, as an agent's `turn write` does.
    """
    path = case_path(body["path"])
    sheet, row = body["sheet"], int(body["row"])
    tool, request = agent_marks(body)
    if body.get("dry_run") is True:
        result = wb_mod.edit_turn(path, sheet, row, body.get("text"), body.get("timecode"), dry=True)
    else:
        with writing(path):
            result = wb_mod.edit_turn(path, sheet, row, body.get("text"), body.get("timecode"))
            if result["changed"]:
                progress = rounds_mod.load_progress(path)
                record = rounds_mod.record_edit(progress, sheet, row, result["old"], result["text"],
                                                result["old_time"], result["time"])
                marked(record, tool, request)
                rounds_mod.save_progress(path, progress)
    answer = {"sheet": sheet, "row": row, "changed": result["changed"], "text": result["text"],
              "runs": result["runs"], "dropped": result["dropped"],
              "seconds": result["seconds"], "time": result["time"]}
    if body.get("dry_run") is True:
        answer.update(dry_run=True, old=result["old"], old_time=result["old_time"])
    return answer


def agent_marks(body: dict) -> tuple[str, str]:
    """The agent's tool and his request a call from the command line or the MCP server carries, each one
    line, both empty for the page's own call."""
    return themes_ai.one_line(body.get("tool") or ""), themes_ai.one_line(body.get("request") or "")


def marked(record: dict, tool: str, request: str, prefix: str = "") -> dict:
    """A History record of an agent's write marked as its own, `by`, `tool` and `request`, as an agent's
    `turn write` marks its edit, with `prefix` for an undo's marks beside the write's. The page's own call
    gives no tool and leaves the record as it was."""
    if tool:
        record.update({f"{prefix}by": "agent", f"{prefix}tool": tool})
        if request:
            record[f"{prefix}request"] = request
    return record


def ticked(value, default: bool) -> bool:
    """A tick from a JSON body or a query string: true, false, or the default when it is absent."""
    if value is None:
        return default
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() in ("1", "true", "yes", "on")


def changed_rows(path: Path, rows: list[dict]) -> list[dict]:
    """The rows a replace or its undo wrote, as the reader renders them, for the page to redraw: the
    transcript's words and runs, the highlights dropped, and the passage's statements, notes, quotes,
    pairs, version and interviewer's note as `read_case` gives them, since a replace changes those too."""
    cells = wb_mod.passage_cells(path, [(r["sheet"], r["row"]) for r in rows])
    out = []
    for r in rows:
        item = {"sheet": r["sheet"], "row": r["row"], "text": r["text"], "runs": r["runs"], "dropped": r["dropped"]}
        item.update(cells.get((r["sheet"], int(r["row"]))) or {})
        out.append(item)
    return out


def replace_places(rows: list[dict]) -> list[dict]:
    """Where a replace changes, or would change, the words: a line for each column of each row, its
    sheet, row, timecode, the column by its role and how many occurrences, never the words."""
    return [{"sheet": r["sheet"], "row": r["row"], "time": r.get("time") or "", "column": role,
             "count": n} for r in rows for role, n in (r.get("columns") or {}).items()]


def words_by_row(rows: list[dict], back: bool = False) -> dict[str, dict]:
    """A replace's rows as the boards and the GETs follow them: each sheet's rows by number, each with
    its statements, its quotes by place and its exploratory notes, the entries before and after, the
    other way round for an undo, `back`."""
    out: dict[str, dict] = {}
    for r in rows:
        change = {}
        for role, cell in (r.get("cells") or {}).items():
            if role not in ("es", "kq", "en"):
                continue
            read = wb_mod.quote_entries if role == "kq" else wb_mod.split_entries
            old, new = read(cell["old"]), read(cell["new"])
            change[role] = (new, old) if back else (old, new)
        if change:
            out.setdefault(r["sheet"], {})[int(r["row"])] = change
    return out


def follow_replace(path: Path, rows: list[dict], back: bool = False, tool: str = "", request: str = "",
                   before: dict | None = None) -> dict:
    """Every copy of the words Idiograph keeps beside the workbook taken in step with a replace or its
    undo: each board of the case and every revision in its history (`themes.cards_reworded`), and each copy of
    the participant across the participants with its cards (`gets.words_replaced`), the GETs file's, and in a
    project of timepoints the participant's LPETs' and the LGETs' (histreplace, 30 October 2026: a replace had
    reached the GETs alone), in the order an edit reaches them (see `statement_copies`), `before` from
    `copies_before` read before the workbook was written. A file that cannot be read is named in `failed` and
    left as it is, the workbook's change standing. Answers the boards, and each copy's keys that took words by
    its kind, `gets`, `lpets` and `lgets`."""
    changes = words_by_row(rows, back)
    boards, failed = [], []
    copies = {kind: [] for kind in COPY_NAMES}
    if not changes:
        return {"boards": boards, **copies, "failed": failed}
    mark = {"by": "agent", "tool": tool, "request": request} if tool else None
    for sheet, by_row in changes.items():
        try:
            boards += themes_mod.cards_reworded(path, sheet, by_row, changed=mark)
        except (WorkbookError, OSError) as exc:
            failed.append(f"The boards could not be read, so their cards kept the words they had: {exc}")
    root, kinds = statement_copies(path)
    flat = {(sheet, row): change for sheet, by_row in changes.items() for row, change in by_row.items()}
    for kind in kinds:
        try:
            with copy_scope(kind, path, root):
                copies[kind] = gets_mod.words_replaced(root, path, flat, (before or {}).get(kind) or {},
                                                       lpets_books(path) if kind == "lpets" else None)
        except (WorkbookError, OSError) as exc:
            failed.append(f"The {COPY_NAMES[kind]} could not be read, so their copy kept the words it had: {exc}")
    return {"boards": boards, **copies, "failed": failed}


def replace_in_case(path: Path, find=None, replace=None, pairs=None, word: bool = True, case: bool = False,
                    only: dict | None = None, dry_run: bool = False, mask: bool = False, tool: str = "",
                    request: str = "", batch: str | None = None) -> dict:
    """Find and replace in one participant's workbook, the one replace the app and an agent share
    (`workbook.replace_words`): the transcript, the statements, the quotes, the exploratory notes and
    the interviewer's notes of every row of every sheet, or the one occurrence `only` names, with
    `pairs` a list of finds and their replacements run in turn. Under the case's lock the workbook is
    loaded once and saved once, every row changed goes into the progress file's `edits` under one batch
    id (`rounds.record_replace`), with `mask` the finds there read "[match]", an agent's `tool` and
    `request` beside them, and `batch` given when one replace spans several workbooks. Then every board
    and every copy of the participant, the GETs', and in a project of timepoints the LPETs' and the LGETs',
    take the new words (see `follow_replace`). With `dry_run` nothing is written, and the answer says
    where it would change. The answer carries the batch, the rows changed as the reader renders them, the
    count per sheet, the places, a line per column of each row, and the boards and each copy's keys that
    took the words, `gets`, `lpets` and `lgets`."""
    path = Path(path)
    if dry_run:
        result = wb_mod.replace_words(path, find, replace, word=word, case=case, only=only, pairs=pairs, dry=True)
        return {"batch": None, "dry_run": True, "rows": [], "counts": result["counts"],
                "replaced": result["replaced"], "places": replace_places(result["rows"])}
    root = project_root(path)
    with writing(path, root=root):
        before = copies_before(path)
        result = wb_mod.replace_words(path, find, replace, word=word, case=case, only=only, pairs=pairs)
        followed = {"boards": [], **{kind: [] for kind in COPY_NAMES}, "failed": []}
        if result["rows"]:
            progress = rounds_mod.load_progress(path)
            given = pairs if pairs is not None else None
            finds = [str(p[0]) for p in given] if given is not None else find
            puts = [str(p[1]) for p in given] if given is not None else replace
            batch = rounds_mod.record_replace(progress, result["rows"], finds, puts, batch=batch, mask=mask,
                                              tool=tool, request=request)
            rounds_mod.save_progress(path, progress)
            followed = follow_replace(path, result["rows"], tool=tool, request=request, before=before)
        else:
            batch = None
    return {"batch": batch, "rows": changed_rows(path, result["rows"]), "counts": result["counts"],
            "replaced": result["replaced"], "places": replace_places(result["rows"]), **followed}


def api_replace(body: dict) -> dict:
    """Find and replace, every row of every sheet, or one occurrence (see `replace_in_case`).

    `find` and `replace` are literal, or `pairs` a list of [find, replace], `word` (whole word, on
    unless false) and `case` (match case, off unless true) the two ticks, matched by
    `workbook.find_spans`. With `sheet`, `row` and `ordinal` it replaces the one occurrence at that
    0-based place among the row's transcript matches, counted again here, `text` being the row as the
    page holds it, and a place that has moved is refused with nothing written. `dry_run` answers the
    count and the places with nothing written, `mask` keeps the finds out of the progress file, and
    `tool` and `request` name an agent's write.
    """
    path = case_path(body["path"])
    find = "" if body.get("find") is None else str(body["find"])
    replace = "" if body.get("replace") is None else str(body["replace"])
    pairs = body.get("pairs") if isinstance(body.get("pairs"), list) else None
    only = None
    if body.get("sheet") is not None and body.get("row") is not None:
        only = {"sheet": str(body["sheet"]), "row": int(body["row"]),
                "ordinal": int(body.get("ordinal") or 0), "text": body.get("text")}
    return replace_in_case(path, find, replace, pairs=pairs, word=ticked(body.get("word"), True),
                           case=ticked(body.get("case"), False), only=only,
                           dry_run=ticked(body.get("dry_run"), False), mask=ticked(body.get("mask"), False),
                           tool=themes_ai.one_line(body.get("tool") or ""),
                           request=themes_ai.one_line(body.get("request") or ""))


def undo_in_case(path: Path, batch: str, redo: bool = False, dry_run: bool = False, tool: str = "",
                 request: str = "") -> dict:
    """Undo a find and replace, or with `redo` apply it again, by the batch id it answered with.

    Each of the batch's records has its old text written back, or its new text for a redo, the
    transcript and every statement, quote and note it changed, after every cell is checked to read as
    the other text, so a passage changed since is refused whole. A highlight the replace dropped comes
    back on its characters. The records are marked `undone`, or no longer, the workbook and the
    sidecar are each saved once, and every board and every copy of the participant, the GETs', the
    LPETs' and the LGETs', take the words back (see `follow_replace`). An agent's undo names its `tool` and his `request` on each record. With
    `dry_run` nothing is written. The answer is shaped as `/api/replace` answers."""
    path = Path(path)
    root = project_root(path)
    with writing(path, root=None if dry_run else root):
        progress = rounds_mod.load_progress(path)
        records = rounds_mod.replace_records(progress, batch)
        if not records:
            raise WorkbookError(i18n.t("server.record_replace_progress_file_cannot"))
        todo = [r for r in records if bool(r.get("undone")) == redo]
        if not todo:
            raise WorkbookError(i18n.t("server.replace_in_already") if redo
                                else i18n.t("server.replace_undone_already"))
        counts: dict[str, int] = {}
        for record in todo:
            counts[record["sheet"]] = counts.get(record["sheet"], 0) + int(record.get("count") or 1)
        places = [{"sheet": r["sheet"], "row": r["row"], "time": "", "column": role, "count": n}
                  for r in todo for role, n in (r.get("columns") or {"transcript": r.get("count") or 1}).items()]
        if dry_run:
            return {"batch": batch, "redo": redo, "dry_run": True, "rows": [], "counts": counts,
                    "replaced": sum(counts.values()), "places": places}
        before = copies_before(path)
        rows = wb_mod.put_back(path, todo, "new" if redo else "old")
        rounds_mod.mark_replace(todo, undone=not redo, tool=tool, request=request)
        rounds_mod.save_progress(path, progress)
        followed = follow_replace(path, rows, tool=tool, request=request, before=before)
    return {"batch": batch, "redo": redo, "rows": changed_rows(path, rows), "counts": counts,
            "replaced": sum(counts.values()), "places": places, **followed}


def api_replace_undo(body: dict) -> dict:
    """Undo a find and replace, or with `redo` apply it again, by its batch id (see `undo_in_case`)."""
    path = case_path(body["path"])
    return undo_in_case(path, str(body.get("batch") or ""), redo=ticked(body.get("redo"), False),
                        dry_run=ticked(body.get("dry_run"), False), tool=themes_ai.one_line(body.get("tool") or ""),
                        request=themes_ai.one_line(body.get("request") or ""))


def api_interviewer_note(body: dict) -> dict:
    """The analyst's note on one of his own turns, in the workbook's Interviewer notes column.

    The row must be the interviewer's, named in the settings, and the workbook is refused while
    Excel has it open. Nothing in the progress file changes, so an interviewer's turn stays context:
    never a stop, never counted, and the rounds, the row states and the passed turns are as they
    were. The answer carries the text as written and whether anything was. An agent's call (26 October,
    `turn interviewer-note`) adds `dry_run`, and `tool` and `request`, and its note alone goes into the
    progress file's `edits`, as History, the rows and the rounds as they were.
    """
    path = case_path(body["path"])
    tool, request = agent_marks(body)
    # an agent's dry run (26 October, `turn interviewer-note`): the same checks, nothing written
    if body.get("dry_run") is True:
        result = wb_mod.save_interviewer_note(path, body["sheet"], int(body["row"]), body.get("text") or "",
                                              srv.config()["interviewer"], dry=True)
        return {"sheet": result["sheet"], "row": result["row"], "text": result["text"],
                "changed": result["changed"], "old": result["old"], "dry_run": True}
    with writing(path):
        result = wb_mod.save_interviewer_note(path, body["sheet"], int(body["row"]),
                                              body.get("text") or "", srv.config()["interviewer"])
        if result["changed"] and tool:
            # an agent's note alone is kept in History, as an agent's turn write is, its row's state and
            # the rounds untouched, so his turn stays context
            progress = rounds_mod.load_progress(path)
            progress.setdefault("edits", []).append(marked(
                {"sheet": result["sheet"], "row": result["row"], "interviewer_note": True,
                 "when": datetime.now().isoformat(timespec="seconds"),
                 "before": {"note": result["old"]}, "after": {"note": result["text"]}}, tool, request))
            rounds_mod.save_progress(path, progress)
    return {"sheet": result["sheet"], "row": result["row"], "text": result["text"],
            "changed": result["changed"]}


def assign_line(preview: dict) -> str:
    """The one line on the confirm card for a whole turn: exactly what merges, which may be nothing."""
    me = f"{preview['from']} {preview['time']}".strip()
    to = preview["to"]
    merges = preview["merges"]
    if len(merges) == 2:
        a, b = merges
        return (i18n.t("server.become_one_passage_between_them", name=a['name'], time=a['time'], name2=b['name'], time2=b['time'], me=me, to=to))
    if len(merges) == 1:
        m = merges[0]
        return i18n.t("server.assigned_joins_one_passage", me=me, to=to, name=m['name'], time=m['time'])
    return i18n.t("server.becomes_s_passage_nothing_merges", me=me, to=to)


def carries_line(counts: dict, merging: bool) -> str:
    """What the merged turn carries across, or what the reassigned one keeps."""
    said = {"es": lambda n: i18n.t("server.count_statements", n=n), "kq": lambda n: i18n.t("server.count_quotes", n=n),
            "en": lambda n: i18n.t("server.count_notes", n=n)}
    parts = [said[k](counts[k]) for k in ("es", "kq", "en") if counts.get(k)]
    if not parts:
        return i18n.t("server.nothing_written_these_rows_yet")
    listed = formats.list_words(parts)
    return i18n.t("server.passage_carries", listed=listed) if merging else i18n.t("server.passage_keeps", listed=listed)


def themes_follow(path: Path, mapper, cut: str | None = None, back: str | None = None) -> dict:
    """Move the case's themes file with the rows the workbook has just moved, under the same lock
    and with the same row map as the progress file, so the two never disagree. A case with no
    themes file has nothing to move. A file that cannot be read is left as it is, and the answer
    carries one line saying so, under `themes`."""
    try:
        themes_mod.rekey(path, mapper, cut=cut, back=back)
    except (WorkbookError, OSError) as exc:
        return {"themes": str(exc) if isinstance(exc, WorkbookError) else
                i18n.t("server.themes_file_could_written_cards")}
    return {}


def api_rows(body: dict) -> dict:
    """Assign words to another speaker, preview a whole-turn assignment, or undo one.

    `op` is `assign` (sheet, row, to, and start and end for a selection, none for the whole turn),
    `preview` (what a whole-turn assignment would merge and carry, for the confirm card) or
    `restore` (an assignment put back from its own backup, by the id it answered with) or
    `untrim` (the rows a trim cut put back from its own backup, by the id `/api/trim` answered
    with). An assignment answers with the block it touched, so the page can hand it straight back
    to undo it, and with the turn to land on, which is where the turn he was on has moved to.

    The themes file moves with the rows in the same request as the progress file, after the
    workbook is written, and an untrim puts back the cards its trim kept aside. An answer carries
    `themes`, one line, when the themes file could not be read and was left as it is.

    An agent's call (26 October, `turn assign`, `turn assign-undo`, `turn trim-undo`) adds `dry_run`,
    which answers what the op would do with nothing written, an assignment's as `preview` answers, and
    `tool` and `request`, which the op's record in the progress file carries, an undo's as `undone_by`,
    `undone_tool` and `undone_request`.
    """
    op = body.get("op")
    path = case_path(body["path"])
    sheet = body.get("sheet") or ""
    current = body.get("current") or {}
    dry = body.get("dry_run") is True
    tool, request = agent_marks(body)

    if op == "preview" or (op == "assign" and dry):
        preview = wb_mod.assign_preview(path, sheet, int(body["row"]), body.get("to"),
                                        body.get("start"), body.get("end"))
        preview["line"] = assign_line(preview)
        preview["carries"] = carries_line(preview["counts"], bool(preview["merges"]))
        return dict(preview, dry_run=True) if op == "assign" else preview

    if op == "assign":
        with writing(path):
            result = wb_mod.assign_rows(path, sheet, int(body["row"]), body.get("to"),
                                        body.get("start"), body.get("end"))
            backup = srv.rel_path(result["backup"])
            progress = rounds_mod.load_progress(path)
            record = marked(rounds_mod.record_assignment(progress, result, backup), tool, request)
            # the turn the page was on, so an undo straight after lands back on it
            if current.get("sheet") == sheet and current.get("row"):
                record["current"] = int(current["row"])
            rounds_mod.save_progress(path, progress)
            shift = result["shift"]
            said = themes_follow(path, lambda key: rounds_mod.shift_key(
                key, sheet, shift["at"], shift["count"], shift["inserted"], shift.get("into"))) if shift else {}
        land = {"sheet": sheet, "row": result["holder"]}
        if current.get("sheet") == sheet and current.get("row") and int(current["row"]) != result["row"]:
            shift = result["shift"]
            moved = int(current["row"]) if not shift else rounds_mod.shifted_row(
                int(current["row"]), shift["at"], shift["count"], shift["inserted"], shift.get("into"))
            land = {"sheet": sheet, "row": moved if moved is not None else result["holder"]}
        elif current.get("sheet") and current.get("sheet") != sheet:
            land = {"sheet": current["sheet"], "row": int(current["row"])}
        return {"id": record["id"], "kind": result["kind"], "whole": result["whole"],
                "sheet": sheet, "row": result["row"], "start": result["start"], "end": result["end"],
                "from": result["from"], "to": result["to"], "merged": result["merged"],
                "block": dict(record["block"], sheet=sheet, backup=backup),
                "after": result["after"], "land": land, **said}

    if op == "restore":
        with writing(path):
            progress = rounds_mod.load_progress(path)
            record = rounds_mod.find_assignment(progress, body.get("id") or "")
            if record is None:
                raise WorkbookError(i18n.t("server.record_assignment_progress_file_cannot"))
            if record.get("undone"):
                raise WorkbookError(i18n.t("server.assignment_already_been_undone"))
            block = record["block"]
            backup = srv.abs_path(record["backup"])
            if not srv.within_root(backup):
                raise srv.OutsideRoot(i18n.t("server.backup_sits_outside_project_folder"))
            if dry:
                return {"id": record["id"], "sheet": record["sheet"], "row": record["row"], "kind": record["kind"],
                        "from": record.get("from"), "to": record.get("to"), "block": dict(block),
                        "backup": record["backup"], "dry_run": True}
            result = wb_mod.restore_rows(path, record["sheet"], block["first"], block["before"],
                                         block["after"], backup, record["row"], expect=record.get("after"))
            rounds_mod.undo_assignment(progress, record)
            marked(record, tool, request, "undone_")
            rounds_mod.save_progress(path, progress)
            said = themes_follow(path, lambda key: rounds_mod.restored_key(key, record))
        # the page stays on the turn it is on: one outside the block moves back with the rows, and
        # one inside it goes back to the turn it was on when the assignment was made
        first, before, after = int(block["first"]), int(block["before"]), int(block["after"])
        land = {"sheet": record["sheet"], "row": record.get("current") or record["row"]}
        if current.get("sheet") == record["sheet"] and current.get("row"):
            r = int(current["row"])
            if r < first:
                land["row"] = r
            elif r >= first + after:
                land["row"] = r - (after - before)
        elif current.get("sheet") and current.get("row"):
            land = {"sheet": current["sheet"], "row": int(current["row"])}
        return {"id": record["id"], "sheet": record["sheet"], "restored": result["restored"],
                "appended": result["appended"], "land": land, **said}

    if op == "untrim":
        with writing(path):
            progress = rounds_mod.load_progress(path)
            record = rounds_mod.find_trim(progress, body.get("id") or "")
            if record is None:
                raise WorkbookError(i18n.t("server.record_trim_progress_file_cannot"))
            if record.get("undone"):
                raise WorkbookError(i18n.t("server.trim_already_been_undone"))
            if not record.get("count") or not record.get("first"):
                raise WorkbookError(i18n.t("server.trim_recorded_before_trim_could"))
            trims = progress.get("trims", [])
            if any(t.get("id") and t.get("sheet") == record["sheet"] and not t.get("undone")
                   for t in trims[trims.index(record) + 1:]):
                raise WorkbookError(i18n.t("server.later_trim_sheet_undone_first"))
            backup = srv.abs_path(record["backup"])
            if not srv.within_root(backup):
                raise srv.OutsideRoot(i18n.t("server.backup_sits_outside_project_folder"))
            if dry:
                return {"id": record["id"], "sheet": record["sheet"], "direction": record.get("direction"),
                        "first": int(record["first"]), "last": int(record["first"]) + int(record["count"]) - 1,
                        "count": int(record["count"]), "timecode": record.get("timecode") or "",
                        "head": record.get("head") or "", "backup": record["backup"], "dry_run": True}
            result = wb_mod.restore_trim(path, record["sheet"], record["first"], record["count"], backup)
            rounds_mod.undo_trim(progress, record)
            marked(record, tool, request, "undone_")
            rounds_mod.save_progress(path, progress)
            first, count = int(record["first"]), int(record["count"])
            said = themes_follow(path, lambda key: rounds_mod.shift_key(key, record["sheet"], first, count, True),
                                 back=record["id"])
        # the page stays on the turn it is on, moved back down with the rows below the cut
        first, count = int(record["first"]), int(record["count"])
        land = {"sheet": record["sheet"], "row": first}
        if current.get("sheet") == record["sheet"] and current.get("row"):
            r = int(current["row"])
            land["row"] = r + count if r >= first else r
        elif current.get("sheet") and current.get("row"):
            land = {"sheet": current["sheet"], "row": int(current["row"])}
        return {"id": record["id"], "sheet": record["sheet"], "first": first, "last": first + count - 1,
                "restored": result["restored"], "land": land, **said}

    raise WorkbookError(i18n.t("server.rows_assigned_previewed_restored_untrimmed"), code="unknown_op")


def api_round_complete(body: dict) -> dict:
    """Record a round as completed, today, once.

    The page calls this on a save of a round's last turn, and for every round it finds done and
    unrecorded when a case opens and on every move, oldest first. A round the server does not find
    done is left unrecorded, so a page working from stale numbers cannot add to the tally. A round
    already recorded keeps its first date. `recorded` says whether this call was the one that
    recorded it.
    """
    cfg = srv.config()
    path = case_path(body["path"])
    number = int(body["round"])
    recorded = False
    with writing(path):
        case = wb_mod.read_case(path)
        rnds = rounds_mod.build_rounds(case["sheets"], cfg["round_minutes"], cfg["interviewer"])
        progress = rounds_mod.load_progress(path)
        states = rounds_mod.row_states(case["sheets"], progress, cfg["interviewer"])
        rnd = next((r for r in rnds if r["number"] == number), None)
        if rnd is not None and rounds_mod.round_done(rnd, states):
            recorded = not progress["rounds"].get(str(number), {}).get("completed")
            rounds_mod.complete_round(progress, number)
            if recorded:
                rounds_mod.save_progress(path, progress)
        summary = summary_of(path, case, progress, rnds, cfg)
    return {"progress": summary, "recorded": recorded}


COMPLETE_OPS = ("mark", "reopen")


def api_complete(body: dict) -> dict:
    """Mark the experiential statements phase of a case complete, or reopen it.

    `{"workbook": ..., "op": "mark" | "reopen"}`. The mark is `complete` in the progress file
    beside the workbook, and this writes that key and nothing else: not another byte of the
    progress file, and never the workbook. Marking a case already marked keeps its first time. The
    answer carries the mark and the summary, which carries it as `complete` too. In a project of two
    or more timepoints `timepoint`, its number or its label, marks that timepoint's statements alone,
    T1 when it is left out, and the summary's `timepoints` carries each one's mark. With `dry_run`
    (26 October, for the agents' `participant complete`) nothing is written: `complete` is the mark
    as it stands and `changed` whether the op would change it.
    """
    path = case_path(body.get("workbook") or body.get("path") or body["workbook"])
    op = str(body.get("op") or "")
    if op not in COMPLETE_OPS:
        raise WorkbookError(i18n.t("server.participant_marked_complete_reopened_nothing"))
    if not path.is_file():
        raise FileNotFoundError(path.name)
    timepoint = timepoint_asked(body.get("timepoint"), project_timepoints(path))
    if body.get("dry_run") is True:
        try:
            at = rounds_mod.complete_at_timepoint(rounds_mod.read_raw(path), timepoint)
        except (ValueError, OSError):
            raise WorkbookError(i18n.t("server.progress_file_beside_workbook_could"))
        return {"complete": at, "changed": (at is None) == (op == "mark"), "dry_run": True,
                "timepoint": timepoint}
    # the project's lock first, then the case's, as `writing` takes them, so the History line is under it too
    root = project_root(path)
    with writing(root=root, books=[path]) if root is not None else writing(path):
        try:
            was = rounds_mod.complete_at_timepoint(rounds_mod.read_raw(path), timepoint)
            at = rounds_mod.set_complete(path, op == "mark", timepoint)
        except (ValueError, OSError):
            raise WorkbookError(i18n.t("server.progress_file_beside_workbook_could"))
        if root is not None and (was is None) == (op == "mark"):
            # the project's History (projhistory, 2 November 2026): a mark that changes nothing writes none
            hist_mod.record(root, "participant complete", [complete_said(path, op, timepoint, was)],
                            hist_mod.asker(body))
    return {"complete": at, "progress": refresh_summary(path)}


def complete_said(path: Path, op: str, timepoint: int, was) -> str:
    """A mark or a reopen as the project's History says it: whose statements, at which timepoint in a project of
    two or more, and since when for a reopen."""
    case = srv.display_case(wb_mod.case_folder(Path(path)).name)
    tps = project_timepoints(path)
    at = f" at {tps[timepoint - 1]['label']}" if longitudinal(tps) and timepoint <= len(tps) else ""
    if op == "mark":
        return f"{case}'s statements{at} marked complete."
    try:
        at_time = datetime.fromisoformat(str(was))
        since = f"{at_time.day} {at_time:%B %Y} at {at_time:%H:%M}"
    except (TypeError, ValueError):
        since = str(was or "")
    return f"{case}'s statements{at} reopened, marked complete since {since}."


def api_trim(body: dict) -> dict:
    """Cut the consent talk off the front of a sheet, or the goodbyes off the back.

    The workbook is archived first, then the rows go, then the sidecar is moved onto the rows that
    survived and the trim is recorded in it, and the themes file moves with the rows the same way,
    each board keeping the cards of the rows cut under its `cut` list. The answer is that record,
    with an id the page hands back to `/api/rows` to undo it, and the turn to land on, which is
    where the turn the page was on (`current`) has moved to, or the nearest one left when it went
    with the cut. The page reloads the case in place, so the column and the round numbers are
    rebuilt. It carries `themes`, one line, when the themes file could not be read.

    An agent's call (26 October, `turn trim`) adds `dry_run`, which answers the rows the trim would cut,
    `first`, `last`, `count`, their times and `marked`, the rows among them with a statement, a note, a
    quote or a highlight, with nothing written, and `tool` and `request`, which the trim's record carries.
    """
    cfg = srv.config()
    path = case_path(body["path"])
    sheet, row = body["sheet"], int(body["row"])
    direction = body.get("direction")
    current = body.get("current") or {}
    tool, request = agent_marks(body)
    if body.get("dry_run") is True:
        return dict(wb_mod.trim_rows(path, sheet, row, direction, dry=True), dry_run=True)
    with writing(path):
        result = wb_mod.trim_rows(path, sheet, row, direction)
        progress = rounds_mod.load_progress(path)
        record = rounds_mod.rekey_after_trim(progress, sheet, direction, row, result["timecode"],
                                             result["head"], srv.rel_path(result["backup"]),
                                             last=result["last"])
        marked(record, tool, request)
        if progress.get("last") is None:
            # the turn he was on went with the cut, so he lands on the first one left
            case = wb_mod.read_case(path)
            rows = [r for s in case["sheets"] if s["name"] == sheet for r in s["rows"]
                    if rounds_mod.is_stop(r, cfg["interviewer"])]
            progress["last"] = {"sheet": sheet, "row": rows[0]["row"]} if rows else None
        record["sidecar"]["last_after"] = progress.get("last")
        rounds_mod.save_progress(path, progress)
        said = themes_follow(path, lambda key: rounds_mod.moved_key(key, sheet, direction, row),
                             cut=record["id"])
    land = None
    if current.get("sheet") and current.get("row"):
        land = {"sheet": current["sheet"], "row": int(current["row"])}
        if current["sheet"] == sheet:
            moved = rounds_mod.shifted_row(int(current["row"]), result["first"], result["removed"], False)
            # a turn that went with the cut lands on the nearest turn left: the first after a cut at
            # the front, the last before a cut at the back
            land["row"] = moved if moved is not None else result["first"]
    public = {k: v for k, v in record.items() if k != "sidecar"}
    return dict(public, removed=result["removed"], land=land,
                **{"from": result["from"], "to": result["to"]}, **said)


_demo_lock = threading.Lock()
_demo_building = False


def _build_demo_recording() -> None:
    """Speak the demo transcript into its recording. Minutes of work, so never on the request."""
    global _demo_building
    try:
        import make_demo
        make_demo.build_recording(write_csv=False, verbose=False)
    except Exception:
        import traceback
        traceback.print_exc()
    finally:
        with _demo_lock:
            _demo_building = False


def ensure_demo_recording() -> bool:
    """Start the demo recording if it is missing. True while a build is under way.

    The recording is not committed, so the first open of the demo on a machine that has never built
    it finds nothing to play. That is when this starts, in a thread of its own and well clear of
    the workbook lock, and the player says so until the file appears.
    """
    global _demo_building
    import shutil as _shutil
    with _demo_lock:
        if _demo_building:
            return True
        if audio_mod.for_sheet(srv.DEMO_WORKBOOK, DEMO_SHEET) is not None:
            return False
        # the Mac app ships the recording built, so a missing one comes back from the bundle's copy,
        # and nothing is ever spoken into the bundle
        if srv.DEMO_DIR != srv.SHIPPED_DEMO:
            srv.seed_demo()
            return False
        if not _shutil.which("say"):
            return False
        _demo_building = True
    threading.Thread(target=_build_demo_recording, daemon=True).start()
    return True


def fill_demo() -> list[Path]:
    """Each demo case's workbook, progress file and board copied from the shipped pristine copy where
    the demo the app works on is missing one (see `make_demo.fill`), the IPA demo's and the thematic analysis
    demo's. A file there is never replaced, and a fill that fails leaves the demo as it was and the server
    starting. Answers the files copied."""
    import make_demo
    copied = []
    for shipped, live in ((srv.SHIPPED_DEMO, srv.DEMO_DIR), (srv.SHIPPED_DEMO / srv.DEMO_TA_FOLDER, srv.demo_ta_dir())):
        try:
            copied += make_demo.fill(shipped / "pristine", live)
        except OSError:
            pass
    return copied


def api_reset_demo(body: dict) -> dict:
    """Put the three demo cases back the way they ship, each workbook, sidecar and board, and the
    demo's GETs file with them, and remove the GETs exports' `Working/`. `demo` of `ta` (demos, 3 November
    2026) resets the thematic analysis demo the same way, its code list with it, and with none it is the IPA
    demo, as before.

    The copy it restores from is the shipped one, inside the bundle in the Mac app, and a file of
    the demo gone missing comes back from there too. A workbook open in Excel refuses the reset
    before anything is written."""
    import make_demo
    live = srv.demo_dir_of((body or {}).get("demo"))
    shipped = srv.SHIPPED_DEMO / srv.DEMO_TA_FOLDER if live != srv.DEMO_DIR else srv.SHIPPED_DEMO
    books = demo_workbooks(live)
    with writing(root=live, books=books):
        try:
            make_demo.reset_all(shipped / "pristine", live)
        except make_demo.DemoError as exc:
            raise WorkbookError(str(exc))
        srv.seed_demo()
    return {"reset": True, "path": srv.rel_path(books[0]), "demo": project_id(live)}


def api_audio(body: dict) -> dict:
    """Whether this sheet has a recording, and the URL that streams it."""
    path = case_path(body["path"])
    sheet = body.get("sheet") or ""
    if not srv.within_root(path):
        return {"found": False, "note": i18n.t("server.workbook_sits_outside_project_folder")}
    found = audio_mod.for_sheet(path, sheet)
    # Juno's is the demo's one recording. Rowan and Mabel have none, and their player stays quiet
    # as it does for any workbook without one
    if found is None and srv.is_demo(path) and Path(path).resolve() == srv.DEMO_WORKBOOK.resolve() and ensure_demo_recording():
        return {"found": False, "building": True, "note": "Building the demo recording"}
    if found is None or not srv.within_root(found):
        return {"found": False, "note": i18n.t("server.recording_found", sheet=sheet)}
    # the offset playback adds to every time code, kept beside the recording (20 October)
    return {"found": True, "name": found.name, "offset": audio_mod.offset_for(path, sheet),
            "url": "/audio?" + urlencode({"path": srv.rel_path(path), "sheet": sheet})}


def api_export(body: dict) -> dict:
    """The statements CSV from Settings. A case with a themes file has the Proposed PET column
    filled from its current board, and one with none leaves the column empty, as it always did.

    With `notes` true, the tick in the Export pane, the interviewer notes go to a markdown file of
    their own beside the CSV, which itself stays statements alone. The answer names both files, and
    a case with no notes writes no file and says so with a `notes_path` of None.

    With `dry_run` (26 October, parity4, for `participant export`), the same checks and the same answer,
    the files it would write and what they would hold, and nothing written. The export changes nothing
    he made, so it keeps no History, from the page or an agent."""
    path = case_path(body["path"])
    held = themes_mod.themes_path(path)
    dry = body.get("dry_run") in (True, "true")
    # in a project of two or more timepoints every timepoint's statements, each with its label (21 October)
    tps = project_timepoints(path)
    every = [(t["n"], t["label"]) for t in tps] if longitudinal(tps) else None
    with writing(path, export=True):
        result = export_mod.export(path, themes=(held, None) if held.exists() else None, timepoints=every,
                                   dry_run=dry)
        if body.get("notes") in (True, "true"):
            case = case_label(path)
            notes = export_mod.export_notes(path, case, dry_run=dry)
            result["notes"] = notes["notes"]
            result["notes_path"] = srv.display_path(srv.rel_path(Path(notes["path"]))) if notes["path"] else None
    # a line on the screen, so the case folder shows by its pseudonym alone
    result["path"] = srv.display_path(srv.rel_path(Path(result["path"])))
    if dry:
        result["dry_run"] = True
    return result


def api_themes(body: dict) -> dict:
    """The Themes screen for one case: its cards read afresh from column C, merged with the board
    stored beside the progress file. The workbook is only read, so one Excel has open is read as it
    stands and nothing is said about it. Opening writes nothing in the case. `board`, from the case
    switcher, puts that board on the canvas in place of the one last open, and writes nothing there
    either."""
    path = case_path(body.get("workbook") or body.get("path") or body["workbook"])
    answer = themes_mod.state(path, case_label(path),
                              board=str(body.get("board") or "") or None)
    # opening the PETs screen goes to the head of the recent list as opening a case does. A board
    # shown beside the GETs canvas, `beside`, is not an opening, and the recent list is the only
    # thing written
    if not body.get("beside"):
        remember(path, themes_mod.timepoint_now() if longitudinal(project_timepoints(path)) else None)
    cfg = srv.config()
    # `platform` says whether Show in Finder can be offered after an export: on a Mac alone.
    # `project` is the band over the canvas, as /api/open carries it for the turn screen, and
    # `config` the settings Settings opens with over this screen
    # `print` is where the print view of a board is, which a server from before it does not send,
    # and `notes` says a save keeps a theme's note, which a server from before the notes would drop.
    # `guidance` is the board panel's Guidance tab, read from its file on every open, and a page in
    # front of a server from before it says to restart in the tab's place.
    # `word` says the export takes `op` of `word`, which a server from before it would answer with
    # the markdown draft and the CSV
    # in a project of two or more timepoints, the timepoint this canvas is at and the participant's
    # timepoints, which the bar's switch lists (21 October), and nothing new in a project of one
    if longitudinal(project_timepoints(path)):
        answer = dict(answer, timepoint=themes_mod.timepoint_now(), timepoints=participant_timepoints(path))
    return dict(answer, path=srv.rel_path(path), demo=srv.is_demo(path), ai=srv.ai_state(cfg), platform=srv.PLATFORM,
                project=read_project(project_root(path)), config=cfg, print=PRINT_PATH, notes=True,
                guidance=themes_guidance(), feedback=bool(srv.feedback_url(cfg)), word=True,
                person=person_for_book(path))


def api_themes_save(body: dict) -> dict:
    """Write the current board of the canvas into the themes file. The workbook is never touched.
    A board the file does not hold is refused. The field keeps its old name, `version`, and
    `revision` of `auto` is the page's timer asking for an automatic revision on the way. A page that
    last read the board in another version than the file holds now, and not because an agent changed
    it (see `themes.save`), is refused with 409, nothing written, and `stale` (19 October). With
    `keep`, Reload on the refusal's card, the canvas is kept in the board's History as
    `themes.RELOAD_KEPT` and the board itself is left as it is."""
    path = case_path(body.get("workbook") or body.get("path") or body["workbook"])
    with writing(path, boards=True):
        if body.get("keep"):
            held = themes_mod.load(path) or {}
            sent = body.get("version") if isinstance(body.get("version"), dict) else {}
            board = themes_mod.find_version(held, sent.get("id"))
            if board is None:
                raise WorkbookError(themes_mod.GONE)
            made = themes_mod.keep_before_reload(board, themes_mod.state_of(themes_mod.normalise(sent)),
                                                 themes_mod.now_iso())
            themes_mod.write(path, held)
            return {"kept": themes_mod.revision_summary(made)}
        try:
            return themes_mod.save(path, body.get("version"), case_label(path),
                                   revision=body.get("revision"))
        except themes_mod.StaleBoard as exc:
            return {"error": str(exc), "stale": exc.view(), "status": 409}


def api_board_order(body: dict) -> dict:
    """A reorder from the board's Table view (19 October, boardtable): the board as the page holds it,
    `version`, set in the order `items` gives under the label `under`, or with `under` null its PETs (its
    GETs with `gets`), through `themes.reorder`, the one an agent's `order` op in `board apply` runs, so
    the table and an agent set an order the same way. `heights` are the page's own measures of its cards
    by key, and a card it has none for takes the estimate. Nothing is written: the answer is where each
    card, label and sticky note now stands, which the page lands as one step of its undo and saves as the
    canvas saves, with `order`, `how` and `moved` as the dry run of the op says them."""
    version = body.get("version")
    if not isinstance(version, dict) or not isinstance(version.get("cards"), dict) or not isinstance(version.get("groups"), list):
        raise WorkbookError(i18n.t("server.board_did_arrive_whole_nothing"))
    gets = ticked(body.get("gets"), False)
    sent = body.get("heights") if isinstance(body.get("heights"), dict) else {}
    tall = {str(k): int(h) for k, h in sent.items() if isinstance(h, (int, float)) and not isinstance(h, bool) and 0 < h < 4000}
    guess = gets_mod.card_height if gets else (lambda _key, text: themes_mod.card_height(text))
    height = lambda key, text: tall.get(key) or guess(key, text)
    under = body.get("under")
    under = None if under in (None, "") else str(under)
    if under is not None and under not in {str(g.get("id")) for g in version["groups"] if isinstance(g, dict)}:
        raise WorkbookError(i18n.t("server.label_longer_board_nothing_moved"))
    items = [str(i) for i in body.get("items") or [] if isinstance(i, (str, int))]
    landed, info = themes_mod.reorder(version, under, items, height=height)
    return {"cards": {k: {"x": c["x"], "y": c["y"]} for k, c in landed["cards"].items()},
            "groups": {g["id"]: {"x": g["x"], "y": g["y"]} for g in landed["groups"]},
            "notes": {n["id"]: {"x": n.get("x", 0), "y": n.get("y", 0)} for n in landed.get("notes") or []
                      if isinstance(n, dict) and n.get("id")},
            "order": info["order"], "how": info["how"], "moved": info["moved"]}


def api_themes_versions(body: dict) -> dict:
    """The named boards of a case's themes, with `op` of `new`, `duplicate`, `rename`, `note`,
    `switch`, `delete` or `choose`, `id` for the board it acts on and `name` or `note` where they
    apply. `choose` marks the board `id` names as the Current board, and `id` of null clears the
    mark. `complete` marks the PETs complete on the Current board, refused while none is marked,
    and `reopen` takes that mark off. The route keeps the name it had when the boards were versions.
    The answer is the screen's state afterwards, as `/api/themes` gives it. The workbook is only read.
    With `dry_run` (26 October, for the agents' board ops) every check is made and nothing is written."""
    path = case_path(body.get("workbook") or body.get("path") or body["workbook"])
    op = str(body.get("op") or "")
    # a board laid out whole comes in only through the server's own callers, which lay it out themselves
    if op == themes_mod.PROPOSE:
        raise WorkbookError(themes_mod.NOT_A_BOARD_OP, code="unknown_op")
    with writing(path, boards=True):
        answer = themes_mod.version_op(path, op, body, case_label(path), dry_run=body.get("dry_run") is True)
    return dict(answer, path=srv.rel_path(path), demo=srv.is_demo(path))


def api_themes_boards(body: dict) -> dict:
    """A theme copied to another board, and each board's history, with `op` of `copy`,
    `revision`, `view` or `restore`, `id` for the board, `revision` for one of its revisions, and
    `group`, `to` and `name` where they apply. `view` writes nothing and answers with the revision
    as the canvas draws it. The others answer with the screen's state afterwards, as `/api/themes`
    gives it. The workbook is only read. With `dry_run` (26 October, for the agents' board history,
    revision, restore and copy) every check is made and nothing is written."""
    path = case_path(body.get("workbook") or body.get("path") or body["workbook"])
    op = str(body.get("op") or "")
    with writing(path, boards=True):
        answer = themes_mod.board_op(path, op, body, case_label(path), dry_run=body.get("dry_run") is True)
    return dict(answer, path=srv.rel_path(path), demo=srv.is_demo(path))


# a case's themes file, `<case>/Working/<stem>.themes.json`, as the switcher finds it
THEMES_SUFFIX = ".themes.json"


def themes_cases(path: Path) -> list[dict]:
    """The cases the PETs screen's switcher lists: every case of the project the workbook belongs
    to with a themes file, and this one whether it has one yet or not, by its pseudonym.

    A themes file counts when it sits in a case's `Working/` folder beside a workbook of its stem,
    outside `_Archive` and the like and never a backup copy. The demo is a project of its own and
    lists its three cases, Juno, Rowan and Mabel, each built here, with a themes file or not. Each
    entry carries the board it opens on, the Current board when it has one and else the board last
    open, and `table`, that board's print view with the dialog shut. A themes file that cannot be
    read leaves its case out. Nothing is written, and nothing is read but the themes files.
    """
    here = Path(path).resolve()
    root = project_root(path)
    books = []
    # the files of the timepoint in scope, `.themes-t2.json` at T2 (see `themes.scoped`)
    suffix = themes_mod.themes_path(Path("x.xlsx")).name[1:]
    if srv.is_demo(path):
        books = [book for book in demo_workbooks(srv.demo_root_of(path)) if book.is_file() and book.resolve() != here]
    else:
        for file in sorted(root.rglob("*" + suffix)):
            if file.name.startswith("."):
                continue
            book = file.parent.parent / (file.name[:-len(suffix)] + ".xlsx")
            try:
                folders = book.relative_to(root).parts[:-1]
            except ValueError:
                continue
            if file.parent.name != "Working" or set(folders) & SKIP_DIRS or BACKUP_STEM.search(book.stem) \
                    or pristine_copy(book):
                continue
            if book.is_file() and book.resolve() != here and srv.within_root(book):
                books.append(book)
    out = []
    for book in [Path(path)] + books:
        try:
            data = themes_mod.load(book)
        except WorkbookError:
            if book.resolve() != here:
                continue
            data = None
        chosen = themes_mod.chosen_of(data)
        shown = themes_mod.find_version(data, chosen) if chosen else themes_mod.current_version(data)
        board = str((shown or {}).get("id") or "")
        entry = {"path": srv.rel_path(book), "case": case_label(book),
                 "name": book.stem, "board": board,
                 "board_name": str((shown or {}).get("name") or themes_mod.FIRST_NAME),
                 "chosen": bool(chosen), "current": book.resolve() == here,
                 "table": PRINT_PATH + "?" + urlencode(dict({"workbook": srv.rel_path(book), "board": board, "auto": "0"},
                                                            **({"timepoint": themes_mod.timepoint_now()}
                                                               if themes_mod.SCOPE.get() else {})))}
        # an AI made that board, which the switcher says faintly after its name
        made = themes_mod.made_said(shown) if shown else None
        if made:
            entry["with_ai"] = made
        out.append(entry)
    out.sort(key=lambda c: (c["case"].lower(), c["name"].lower()))
    return out


def api_themes_cases(body: dict) -> dict:
    """The PETs screen's case switcher, for the workbook on the screen: the cases of its project
    with a themes file, each with the board it opens on and its table (see `themes_cases`). The
    switcher opens a case through `/api/themes` with that `board`, and its table in a tab of its
    own. Nothing is written."""
    path = case_path(body.get("workbook") or body.get("path") or body["workbook"])
    cases = themes_cases(path)
    # each with their picture, label and pen portrait (pbiobuild)
    root = project_root(path)
    return {"cases": with_people(root, cases) if root is not None else cases}


def api_participants(body: dict) -> dict:
    """The participant picker in the tab of the statements screen (20 October): every participant of the
    project the workbook belongs to with an annotated workbook, as GETs counts the study, in case order,
    each by its label with the workbook its statements open on, `current` the one on the screen, and the
    project's name. Nothing is written, and nothing is read but the case list and each themes file's head."""
    path = case_path(body.get("workbook") or body.get("path") or body["workbook"])
    root = project_root(path)
    here = path.resolve()
    books = sorted(gets_books(root) if root is not None else [], key=lambda b: gets_mod.case_order(b["case"]))
    out = [{"case": b["case"], "path": srv.rel_path(b["workbook"]), "current": b["workbook"].resolve() == here}
           for b in books]
    if not any(p["current"] for p in out):
        out.insert(0, {"case": case_label(path), "path": srv.rel_path(path), "current": True})
    # each with their picture, label and pen portrait (pbiobuild)
    if root is not None:
        with_people(root, out)
    return {"project": read_project(root).get("name") or "", "participants": out}


# ------------------------------------------------------------------ GETs

# the demo's own folders that hold no case: the copy Reset demo restores from, and the transcript
GETS_SKIP = ("pristine", "source")


def gets_root(body: dict) -> Path:
    """The project a GETs request is for: the one the workbook named belongs to, the demo's for a
    demo case, with no workbook the one `root` names by its id, and with neither the only project
    there is."""
    value = body.get("workbook") or body.get("path") or ""
    if value:
        return project_root(case_path(value))
    if body.get("root"):
        return srv.project_named(body["root"])
    roots = srv.project_roots()
    if not roots:
        raise WorkbookError(i18n.t("server.project_folder_chosen_yet_gets"))
    if len(roots) > 1:
        raise WorkbookError(i18n.t("server.say_which_project_s_gets"))
    return roots[0]


def themes_case(path: Path) -> str:
    """A case by the pseudonym its themes file names, read from the file's head, else its folder's."""
    try:
        with themes_mod.themes_path(path).open(encoding="utf-8") as fh:
            head = fh.read(2048)
        m = re.search(r'"case":\s*("(?:[^"\\]|\\.)*")', head)
        if m:
            case = json.loads(m.group(1)).strip()
            if case:
                return case
    except (OSError, ValueError):
        pass
    return case_label(path)


def gets_books(root: Path, rows: list[dict] | None = None) -> list[dict]:
    """The study: every case of a project with an annotated workbook, as the case list finds them,
    and for a case folder holding two the one with a themes file, then the newest. The demo's are
    the case folders in the demo, never its pristine copy. `rows` is the case list when the caller
    has it already."""
    if LPETS_FOR.get() is not None:
        return lpets_books(LPETS_FOR.get())
    demo = srv.is_demo_root(root)
    if rows is None:
        rows = list_cases(root)
    picked: dict[str, tuple] = {}
    for r in rows:
        if r.get("kind") != "annotated":
            continue
        path = srv.abs_path(r["path"])
        if demo:
            try:
                parts = path.resolve().relative_to(Path(root).resolve()).parts
            except ValueError:
                continue
            if not parts or parts[0] in GETS_SKIP:
                continue
        folder = str(wb_mod.case_folder(path).resolve())
        try:
            rank = (themes_mod.themes_path(path).exists(), path.stat().st_mtime)
        except OSError:
            continue
        if folder not in picked or rank > picked[folder][0]:
            picked[folder] = (rank, path, r)
    return [{"case": themes_case(path), "workbook": path, "pets_complete": r.get("pets_complete")}
            for _rank, path, r in picked.values()]


def gets_head(root: Path | None, rows: list[dict] | None = None) -> dict | None:
    """The head row of All cases for a project, or under the Demo card for the demo's: the cases of
    its study, those with their PETs marked complete, GETs marked complete when they are, and the
    workbook the screen opens through. None for a project with no case. Writes nothing."""
    if root is None:
        return None
    if LGETS_FOR.get() is None and longitudinal(root_timepoints(root)):
        # a project of two or more timepoints answers its LGETs (21 October)
        with board_scope(root):
            head = gets_head(root, rows)
        return dict(head, lgets=True) if head else head
    try:
        books = gets_books(root, rows)
    except OSError:
        return None
    if not books:
        return None
    first = sorted(books, key=lambda b: gets_mod.case_order(b["case"]))[0]
    # for the home screen's wide card: `held`, the cases of the study the GETs file holds, `board`,
    # the name of its Current board or None, and `boards`, how many boards it has
    data = gets_file(root)
    kept = data.get("cases") if isinstance((data or {}).get("cases"), dict) else {}
    study = gets_mod.study_of(data, [b["case"] for b in books])
    chosen = themes_mod.chosen_of(data)
    board = " ".join(str((themes_mod.find_version(data, chosen) or {}).get("name") or "").split()) if chosen else ""
    # `themes`, the group themes on the Current board, else on the board on the canvas, the groups no other
    # group holds, for the project's card on Home (the split's pages)
    shown = themes_mod.find_version(data, chosen or (data or {}).get("current")) or {}
    groups = [g for g in shown.get("groups") or [] if isinstance(g, dict)]
    inside = {m for g in groups for m in g.get("members") or []}
    tops = [g for g in groups if g.get("id") not in inside]
    return dict(gets_mod.summary_of(root, books), path=srv.rel_path(first["workbook"]),
                name=read_project(root)["name"],
                held=sum(1 for b in books if study[b["case"]]["in"] and b["case"] in kept),
                board=board or None, boards=len(gets_mod.boards_of(data)), themes=len(tops))


def gets_reply(root: Path, body: dict, answer: dict) -> dict:
    """A GETs answer with what the screen draws around the canvas: the project's name in the bar,
    the band, the demo tag, the settings for the cog, and `ai`, the switch and the PETs screen's model.
    `guidance` is the GETs sections of `pet_guidance.md` for the Guidance tab, a thematic analysis project's
    `ta_themes_guidance.md` (tarail), with `guidance_ta` to say so. Each case of the
    Cases panel carries `path`, its workbook as the screen names one, for Open beside, and `root`
    and `gets_print` say where the print view of the GETs is."""
    cfg = srv.config()
    project = read_project(root)
    # the participant opened last, whom the steps open on the project's GETs or LGETs from Home's card,
    # and none on a participant's LPETs, whose cases are their timepoints
    last = last_opened(answer.get("cases") or []) if LPETS_FOR.get() is None else None
    for case in answer.get("cases") or []:
        if case.get("workbook"):
            case["path"] = srv.rel_path(Path(case.pop("workbook")))
    ai = srv.ai_state(cfg, "gets")
    # on LPETs the participant is the canvas's own, by their label, with their timepoints (21 October), and their
    # picture, label and pen portrait for the bar (pbiobuild)
    if LPETS_FOR.get() is not None:
        who = LPETS_FOR.get()
        answer = dict(answer, lpets=True, participant=case_label(who), timepoints=participant_timepoints(who),
                      person=person_for_book(who))
    else:
        # each participant of the GETs' or the LGETs' Participants panel with their own set (pbiobuild)
        people = people_view(root)
        for case in answer.get("cases") or []:
            if isinstance(case, dict) and case.get("case"):
                case["person"] = person_of(root, people, case["case"])
    # and on LGETs the project's timepoints, which the cards cite (21 October)
    if LGETS_FOR.get() is not None:
        answer = dict(answer, lgets=True, timepoints=root_timepoints(root))
    return dict(answer, path=str(body.get("workbook") or body.get("path") or ""), demo=project["demo"],
                case=answer.get("participant") or project["name"], project=project, config=cfg, ai=ai,
                last_opened=last, platform=srv.PLATFORM, notes=True, feedback=bool(srv.feedback_url(cfg)),
                guidance=(themes_guidance(i18n.long_text(TA_THEMES_GUIDANCE)) if project.get("method") == "ta"
                          else themes_ai.gets_guidance_lines()), guidance_ta=project.get("method") == "ta",
                root=srv.rel_path(root), gets_print=GETS_PRINT_PATH)


def api_gets_head(body: dict) -> dict:
    """The GETs row of the project the workbook belongs to, as `/api/cases` carries the case root's,
    for the row under the Demo card. Writes nothing and reads no workbook it need not."""
    root = gets_root(body)
    return {"gets": gets_head(root)}


def api_gets(body: dict) -> dict:
    """The GETs screen of a project, read afresh: every case of the study, each one not yet in shown
    as it would come in. Opening writes nothing. `board` shows that board in place of the one last
    open. A thematic analysis project made before its code list has the list made first (codes), which
    gathers each code's cards on its boards."""
    root = gets_root(body)
    if i18n.method_now() == "ta" and not codes_mod.path_of(root).exists():
        codes_list(root)
    return gets_reply(root, body, gets_mod.state(root, gets_books(root), board=str(body.get("board") or "") or None))


# the autosave asks for the study every few hundred milliseconds of work, so it is held a moment
GETS_BOOKS_HELD = 10
_gets_books: dict = {}


def held_books(root: Path) -> list[dict]:
    """The study as `gets_books` finds it, held for a few seconds for the autosave."""
    if LPETS_FOR.get() is not None:
        return gets_books(root)
    key = str(Path(root).resolve())
    at, books = _gets_books.get(key, (0.0, None))
    if books is None or time.time() - at > GETS_BOOKS_HELD:
        books = gets_books(root)
        _gets_books[key] = (time.time(), books)
    return books


def api_gets_save(body: dict) -> dict:
    """The board on the GETs canvas written, every case not yet in taken in on the way. The
    workbooks and the themes files are only read. A page that last read the board in another version
    than the file holds now, after an agent's gets apply or take or another window's save, is refused
    with 409 and nothing written, and `stale`, the board's id and its version now, which Overwrite
    sends back (19 October). With `keep`, Reload on the refusal's card, the canvas is kept in the
    board's History as `themes.RELOAD_KEPT` and the board itself is left as it is."""
    root = gets_root(body)
    with writing(root=root):
        if body.get("keep"):
            held = gets_mod.load(root) or {}
            sent = body.get("version") if isinstance(body.get("version"), dict) else {}
            board = themes_mod.find_version(held, sent.get("id"))
            if board is None:
                raise WorkbookError(gets_mod.GONE)
            made = themes_mod.keep_before_reload(board, themes_mod.state_of(gets_mod.normal(sent, held)),
                                                 themes_mod.now_iso())
            gets_mod.write(root, held)
            return {"kept": themes_mod.revision_summary(made)}
        try:
            return gets_mod.save(root, held_books(root), body.get("version"), revision=body.get("revision"))
        except themes_mod.StaleBoard as exc:
            return {"error": str(exc), "stale": exc.view(), "status": 409}


def api_stamp(body: dict) -> dict:
    """What the page needs to notice a change made outside it, read and nothing written: the file's
    `updated`, the board on its canvas and the Current board, and each board by its id, name and
    `updated`, with what an AI agent did to it, `made` and `changed`. With `gets` it reads the GETs
    file of the workbook's project, and without it the case's themes file, with `turns`, how many
    turns an agent has written into the workbook and the last of them, from the progress file's
    `edits`, and `workbook`, the workbook's time and whether a window of this app wrote it last, which
    keeps two windows on one case in step. The PETs and GETs screens and Experiential statements ask it on a focus and every
    thirty seconds. `outside` says the file was last written outside the app, by an AI agent's command
    line or by hand, and not by a window of this one, whose change an open board takes by itself (20
    October), and on GETs `cases` lists each case whose PETs changed since they came in, with whether
    that change was made outside the app."""
    path = case_path(body.get("workbook") or body.get("path") or body["workbook"])

    def boards(data) -> list[dict]:
        out = []
        for b in themes_mod.boards_of(data):
            entry = {"id": str(b.get("id")), "name": str(b.get("name") or ""), "updated": str(b.get("updated") or "")}
            for key in themes_mod.AGENT_KEYS:
                mark = themes_mod.agent_mark(b.get(key))
                if mark:
                    entry[key] = mark
            out.append(entry)
        return out

    if ticked(body.get("gets"), False):
        root = project_root(path)
        data = gets_mod.load(root)
        held = (data or {}).get("cases") if isinstance((data or {}).get("cases"), dict) else {}
        cases = [{"case": e["case"], "outside": gets_mod.changed_outside(e, held.get(e["case"]))}
                 for e in gets_mod.survey(held_books(root), data or {}) if e["status"] == "changed"]
        return {"file": "gets", "updated": (data or {}).get("updated"), "current": (data or {}).get("current"),
                "chosen": themes_mod.chosen_of(data), "boards": boards(data),
                "outside": not wb_mod.written_here(gets_mod.gets_path(root)), "cases": cases}
    data = themes_mod.load(path)
    try:
        held = rounds_mod.read_raw(path) or {}
    except (ValueError, OSError):
        held = {}
    # a passage an agent wrote, never a heading the quote-heading op renamed (23 October)
    written = [e for e in held.get("edits") or [] if isinstance(e, dict) and e.get("by") == "agent"
               and not e.get("heading")]
    last = written[-1] if written else None
    # the workbook as it stands, so a window of this app writing a passage's statements or notes shows in
    # another window on the same case by itself (20 October, two windows in step): its time as text and
    # whether a window of this app wrote it last
    try:
        at = str(Path(path).stat().st_mtime_ns)
    except OSError:
        at = ""
    return {"file": "themes", "updated": (data or {}).get("updated"),
            "workbook": {"at": at, "here": wb_mod.written_here(path)},
            "outside": not wb_mod.written_here(themes_mod.themes_path(path)),
            "current": str((themes_mod.current_version(data) or {}).get("id") or "") or None,
            "chosen": themes_mod.chosen_of(data), "boards": boards(data),
            "turns": {"count": len(written),
                      "last": {"sheet": last.get("sheet"), "row": last.get("row"), "when": last.get("when"),
                               "tool": last.get("tool") or ""} if last else None}}


def api_gets_ops(body: dict) -> dict:
    """The GETs boards, with `op` of `new`, `duplicate`, `rename`, `note`, `switch`, `delete`,
    `choose`, `complete` or `reopen`, in the shape of the PETs board ops. `complete` marks GETs
    complete, refused while a case of the study is not in from its marked board unchanged. With
    `dry_run` (26 October, for the agents' gets ops) every check is made, nothing is written, and the
    answer is the op's own (see `gets.version_op`)."""
    root = gets_root(body)
    with writing(root=root):
        answer = gets_mod.version_op(root, gets_books(root), str(body.get("op") or ""), body,
                                     dry_run=body.get("dry_run") is True)
    return answer if answer.get("dry_run") else gets_reply(root, body, answer)


def api_gets_boards(body: dict) -> dict:
    """A GETs board's history, with `op` of `revision`, `view` or `restore`, in the shape of
    `/api/themes-boards`. `view` writes nothing, and with `dry_run` (26 October) no op does. With `op` of
    `pdf` (31 October 2026, Export as PDF) the print card's PDF is written where `gets export` puts it, made by
    Typst (typst5, 9 November 2026, see `gets_pdf_place`), and `canvas` writes the canvas's PDF or picture."""
    root = gets_root(body)
    if str(body.get("op") or "") == "pdf":
        return gets_pdf_place(root, body)
    if str(body.get("op") or "") == "canvas":
        return gets_canvas(root, body)
    if str(body.get("op") or "") == "word":
        return gets_word_write(root, body)
    with writing(root=root):
        answer = gets_mod.board_op(root, gets_books(root), str(body.get("op") or ""), body,
                                   dry_run=body.get("dry_run") is True)
    return answer if answer.get("dry_run") else gets_reply(root, body, answer)


def gets_pdf_place(root: Path, body: dict) -> dict:
    """Export as PDF of a GETs board (31 October 2026, pdfexport), written by the server through Typst (typst5, 9
    November 2026, Adam: Typst for every PDF, no fallback): the print card's choices, `what`, `detail`, `notes`,
    `get` and `sending`, at the project's root beside the GETs file, named as the agents' `gets export` names it,
    the date and time in the name when a file has it. `shown` names it from the project's root. With `dry_run`
    nothing is made or written. When Typst cannot make it the answer is its plain sentence and nothing is
    written."""
    data = gets_mod.load(root)
    boards = themes_mod.boards_of(data)
    asked = str(body.get("board") or "")
    board = next((b for b in boards if str(b.get("id")) == asked), None) if asked else None
    if board is None:
        raise WorkbookError(i18n.t("page_print.gets.board_gone"))
    books = gets_books(root)
    with writing(root=root):
        made = print_pdf.write_gets(root, books, read_project(root), board, what=str(body.get("what") or "table"),
                                    detail=str(body.get("detail") or "full"), notes=body.get("notes") in (True, 1, "1"),
                                    get=str(body.get("get") or "") or None, sending=export_sending(body),
                                    dry_run=body.get("dry_run") is True, descriptions=export_descriptions(body),
                                    researcher=researcher_name(), people=people_printed(root, body))
    out = {"pdf": made["name"], "shown": [made["name"]], "path": made["path"], "name": made["name"],
           "dated": made["dated"], "version": made["version"]}
    return dict(out, dry_run=True) if made.get("dry_run") else out


def gets_word_write(root: Path, body: dict) -> dict:
    """Microsoft Word on a thematic analysis project's theme table (taword, 1 November 2026): the board of themes as
    a Word document at the project's root, where its PDF goes, with the card's choices, `detail`, `notes`, `sending`
    and `descriptions`, its author Your name (see `gets_word`). An IPA project's is refused, its tables of PETs going
    to Word from each participant's board. `dry_run` names the file and writes nothing."""
    gets_word.refuse_unless_ta()
    data = gets_mod.load(root)
    asked = str(body.get("board") or "")
    board = next((b for b in themes_mod.boards_of(data) if str(b.get("id")) == asked), None) if asked else None
    if board is None:
        raise WorkbookError(i18n.t("page_print.gets.board_gone"))
    with writing(root=root):
        made = gets_word.write(root, gets_books(root), read_project(root), board, detail=str(body.get("detail") or "full"),
                               notes=body.get("notes") in (True, 1, "1"), sending=export_sending(body),
                               descriptions=export_descriptions(body), author=researcher_name(),
                               dry_run=body.get("dry_run") is True, people=people_printed(root, body))
    return {"word": made["name"], "shown": [made["name"]], "path": made["path"], "name": made["name"],
            "dated": made["dated"], "counts": made["counts"], "version": made["version"],
            **({"dry_run": True} if made.get("dry_run") else {})}


def api_gets_cases(body: dict) -> dict:
    """A case of the GETs, with `op` of `take` and `case`: Take the changes of a case changed since it
    came in, each board keeping a revision first. With `op` of `colour`, the case's colour on the GETs
    board, `colour` a place in the cases' palette or null for Default, kept in the GETs file at once."""
    root = gets_root(body)
    op = str(body.get("op") or "")
    if op not in ("take", "colour"):
        raise WorkbookError(gets_mod.NOT_A_GETS_OP, code="unknown_op")
    with writing(root=root):
        if op == "colour":
            answer = gets_mod.colour_op(root, gets_books(root), str(body.get("case") or ""), body.get("colour"))
        else:
            answer = gets_mod.take(root, gets_books(root), str(body.get("case") or ""))
    return gets_reply(root, body, answer)


def gets_audio(books: list[dict]):
    """A turn of the audit trail to the address of its sheet's recording, or None when its case has
    none, each sheet looked for once."""
    by_case = {b["case"]: Path(b["workbook"]) for b in books}
    found: dict = {}

    def link(cell: dict) -> str | None:
        book, sheet = by_case.get(cell.get("case")), str(cell.get("sheet") or "")
        if book is None or not sheet:
            return None
        key = (str(book), sheet)
        if key not in found:
            rec = audio_mod.for_sheet(book, sheet)
            found[key] = ("/audio?" + urlencode({"path": srv.rel_path(book), "sheet": sheet})
                          if rec is not None and rec.exists() and srv.within_root(rec) else None)
        return found[key]

    def offset(cell: dict) -> float:
        book, sheet = by_case.get(cell.get("case")), str(cell.get("sheet") or "")
        return audio_mod.offset_for(book, sheet) if book is not None and sheet else 0.0

    link.offset = offset
    return link


def search_cases(root: Path) -> list[dict]:
    """The cases a search of a project goes through, the study as the GETs screen finds it, held a few
    seconds as the autosave holds it, each by its label with its workbook, in his order of the cases on
    the project's page, the demo's fixed, and any case he has not placed after them in case order."""
    if srv.is_demo_root(root):
        order = list(DEMO_CASES)
    else:
        order = order_of(project_file(root))
    rows = [{"case": case_label(b["workbook"]), "workbook": Path(b["workbook"]), "path": srv.rel_path(Path(b["workbook"]))}
            for b in held_books(root)]
    return sorted(rows, key=lambda c: (0, order.index(c["case"]), []) if c["case"] in order
                  else (1, 0, gets_mod.case_order(c["case"])))


def search_distil(root: Path) -> dict:
    """A Distil project as Everything searches it, as This project does: its cases, its project, its GETs
    file and its PETs' labels, named as the home screen names it."""
    project = read_project(root)
    return {"id": project_id(root), "name": project.get("name") or Path(root).name, "cases": search_cases(root),
            "project": project, "gets_file": gets_mod.gets_path(root), "labels": project["pet_labels"]}


def api_gets_trail(body: dict) -> dict:
    """One GET's audit trail for the GETs screen, `get` on `board`, as HTML the page puts in its
    card, every case of the study a block, a turn with a recording carrying its address. The GETs
    file, the themes files and the workbooks are only read, and nothing is written."""
    root = gets_root(body)
    books = gets_books(root)
    with srv._lock:
        return gets_print.trail_view(root, books, str(body.get("board") or "") or None, str(body.get("get") or ""),
                                     audio=gets_audio(books))


# The print view of the GETs, a page the browser prints or saves as PDF, by GET.
GETS_PRINT_PATH = "/gets/print"


def gets_print_root(query: dict) -> Path:
    """The project a print of the GETs is for: the one `workbook` belongs to, or `root`, which must
    be a project's root or the demo's folder, and with neither the only project."""
    if query.get("workbook"):
        return gets_root(query)
    value = str(query.get("root") or "").strip()
    if not value:
        return gets_root({})
    asked = srv.abs_path(value).resolve()
    for allowed in [srv.DEMO_DIR, srv.demo_ta_dir()] + srv.project_roots():
        if asked == Path(allowed).resolve():
            return Path(allowed)
    raise srv.OutsideRoot(i18n.t("server.folder_project_folder_nothing_printed"))


def gets_print_page(query: dict) -> tuple[int, str]:
    """The print view of the GETs, `/gets/print?root=<path>&board=<id>&what=table|trail|all`, with
    `detail` of `full` or `selected`, `notes=1` to bring participant notes in, `get` for one GET's
    trail and `auto=0` to leave the print dialog shut. Rendered from the GETs file as the screen
    would show it, every case not yet in shown as it would come in, and nothing written anywhere.
    `sending`, 1 or 0, leaves the board's name off, as the PETs table's print view does. `participants`, 1 or 0,
    puts the participants table first or leaves it out, the settings deciding without it (pbioexport)."""
    try:
        root = gets_print_root(query)
        with srv._lock, route_scope(GETS_PRINT_PATH, query):
            books = gets_books(root)
            return 200, gets_print.page(root, books, read_project(root), str(query.get("board") or "") or None,
                                        what=str(query.get("what") or "table"), detail=str(query.get("detail") or "full"),
                                        notes=str(query.get("notes") or "") == "1", get=str(query.get("get") or "") or None,
                                        auto=str(query.get("auto") or "") != "0", audio=gets_audio(books),
                                        sending=export_sending(query), descriptions=export_descriptions(query),
                                        researcher=researcher_name(), people=people_printed(root, query))
    except srv.OutsideRoot as exc:
        return 403, themes_print.refusal(str(exc))
    except WorkbookError as exc:
        return 409, themes_print.refusal(str(exc))
    except FileNotFoundError as exc:
        return 404, themes_print.refusal(f"File not found: {exc}")


def api_gets_settings(body: dict) -> dict:
    """The study's own settings, under GETs in Project settings: read with `op` of `read`, the default, which
    writes nothing and reads no workbook, or saved with `op` of `save`, `minimum`, `one_per_pet` and
    `study`, each case in or out with a reason, the save with `dry_run` (26 October, for the agents'
    gets settings) checked and nothing written."""
    root = gets_root(body)
    books = gets_books(root)
    if str(body.get("op") or "read") == "save":
        with writing(root=root):
            answer = gets_mod.settings_op(root, books, body, dry_run=body.get("dry_run") is True,
                                          asker=hist_mod.asker(body))
        return answer if answer.get("dry_run") else gets_reply(root, body, answer)
    return dict(gets_mod.settings_view(root, books), project=read_project(root))


def traj_root(body: dict) -> Path:
    """The project a Trajectories request is for, as a GETs request finds it, refused in a project of one
    timepoint."""
    return traj_check(gets_root(body))


def traj_check(root: Path) -> Path:
    if not longitudinal(root_timepoints(root)):
        raise WorkbookError(i18n.t("server.trajectories_come_two_more_timepoints"))
    return root


def traj_people(root: Path) -> list[dict]:
    """Each participant of the project for their card on the Trajectories board: their label, their colour
    on the LGETs board, his choice or their place round the palette, the titles of their LPETs, from the
    board their LPETs come into LGETs from, each of those LPETs as a row across the timepoints (trajbuild2,
    10 November 2026, see `gets.lpet_rows`), every quote of each of their interviews, `quotes`, by the
    timepoint's key, which a cell may take beyond its LPET's own (trajchoose, 11 November 2026, see
    `gets.interview_quotes`), and their workbook. Their picture and label are their own, from the project file
    (pbiobuild, `people_view`). Only reads."""
    people = people_view(root)
    with board_scope(root):
        books = gets_books(root)
        data = gets_mod.load(root)
        look = gets_mod.looks([b["case"] for b in books], data)
        out = []
        for b in books:
            try:
                snap = gets_mod.lpets_snapshot(Path(b["workbook"]))
                titles = [p["title"] for p in snap["pets"] if p.get("parent") is None]
            except (WorkbookError, OSError):
                titles = []
            try:
                lp = traj_lpets(Path(b["workbook"]))
                rows, quotes = lp[2], gets_mod.interview_quotes(lp[0], lp[3]) if lp[0] else {}
            except (WorkbookError, OSError):
                rows, quotes = [], {}
            out.append({"case": b["case"], "colour": look[b["case"]]["colour"], "lpets": titles, "rows": rows,
                        "quotes": quotes, "path": srv.rel_path(Path(b["workbook"])),
                        "person": people_mod.find(people, b["case"])})
    return out


def traj_turns(book: Path):
    """A participant's transcript turns at a timepoint by its key, T2, for a key quote taken from the transcript
    (trajchoose, 11 November 2026), the workbook read once while it is unchanged (`themes.transcript_turns`). A
    workbook that cannot be read has none, so a passage kept from it falls back as a lost quote does."""
    def turns(at: str) -> list[dict]:
        try:
            return [t for t in themes_mod.transcript_turns(Path(book)) if tp_label(t["at"]) == at]
        except (WorkbookError, OSError):
            return []
    return turns


def traj_lpets(book: Path) -> tuple[dict | None, dict | None, list[dict], list[str], dict]:
    """A participant's LPETs file as Trajectories reads it: the file, the board their LPETs come into LGETs from,
    each LPET as a row across the timepoints, a passage of their transcript read where a row keeps one, the
    timepoints' keys and their labels. A participant with no LPETs file has no rows. Only reads."""
    tps = project_timepoints(book)
    inside = [tp_label(t["n"]) for t in tps]
    labels = {tp_label(t["n"]): [t["label"], t["description"]] for t in tps}
    with lpets_scope(book):
        data = gets_mod.load(book)
        if not data:
            return None, None, [], inside, labels
        board, _complete = gets_mod.source_board(data)
        return data, board, gets_mod.lpet_rows(data, board, inside, turns=traj_turns(book)), inside, labels


def traj_reply(root: Path, body: dict, data: dict | None, more: dict | None = None) -> dict:
    """The Trajectories board as the screen draws it, with the project for the bar."""
    cfg = srv.config()
    project = read_project(root)
    people = people_view(root)
    answer = traj_mod.board(data, traj_people(root))
    for c in answer["participants"]:
        c["picture_url"] = person_url(root, people_mod.find(people, c["case"]))
    return dict(answer, **(more or {}), project=project, demo=project["demo"],
                root=srv.rel_path(root), path=str(body.get("workbook") or body.get("path") or ""), config=cfg,
                platform=srv.PLATFORM, feedback=bool(srv.feedback_url(cfg)), timepoints=root_timepoints(root))


def api_trajectories(body: dict) -> dict:
    """The Trajectories board of a project of two or more timepoints (21 October): its columns, each
    participant's card and those not placed. Opening writes nothing."""
    root = traj_root(body)
    return traj_reply(root, body, traj_mod.load(root))


def api_trajectories_turns(body: dict) -> dict:
    """A participant's transcript at a timepoint for a key quote taken from it on Trajectories (trajchoose, 11
    November 2026): `participant`, by label or pseudonym, and `timepoint`, the cell's when none is named. Answers
    each of their turns with words, the interviewer's and another speaker's left out, its `turn`, `<sheet>:<row>`,
    time and words, and `interviews`, the timepoints they have a transcript at. Only reads. An agent reads the same
    turns with `turn show`, and the `quote` op takes the passage."""
    root = traj_root(body)
    books = gets_books(root)
    case = traj_mod.find_case([b["case"] for b in books], body.get("participant"))
    if case is None:
        raise WorkbookError(i18n.t("server.trajectory_not_a_participant",
                                   name=traj_mod.words(body.get("participant")) or "Nobody"))
    book = Path(next(b["workbook"] for b in books if b["case"] == case))
    tps = root_timepoints(root)
    labels = {tp_label(t["n"]): [t["label"], t["description"]] for t in tps}
    at = gets_mod.timepoint_of(body.get("timepoint"), labels) or tp_label(1)
    who = wb_mod._norm(srv.config().get("interviewer"))
    every = themes_mod.transcript_turns(book)
    held = {tp_label(t["at"]) for t in every}
    return {"participant": case, "timepoint": at, "interviews": [k for k in labels if k in held],
            "turns": [{"turn": t["turn"], "time": t["time"], "text": t["text"]} for t in every
                      if tp_label(t["at"]) == at and not t["context"] and not (who and wb_mod._norm(t["name"]) == who)]}


def api_trajectories_ops(body: dict) -> dict:
    """A change to the Trajectories board, `ops` a list of operations (see `trajectories.apply`): a column
    added, renamed, moved or taken away, a participant placed or taken out, their note. All or nothing, and
    with `dry_run` nothing is written. The board answers as it is, or would be, with `changes`."""
    root = traj_root(body)
    with writing(root=root):
        return traj_apply(root, body)


def traj_apply(root: Path, body: dict) -> dict:
    """The change itself, for the route and the command line alike, the caller holding the project's lock. An
    operation on an LPET's row or its domain is run on that participant's LPETs board in memory, and those
    boards are written only once every operation has passed (see `trajectories.change`)."""
    books = gets_books(root)
    cases = [b["case"] for b in books]
    by_case = {b["case"]: Path(b["workbook"]) for b in books}
    held: dict = {}
    when = themes_mod.now_iso()

    def opened(case: str):
        if case not in held:
            data, board, rows, inside, labels = traj_lpets(by_case[case])
            held[case] = {"data": data, "board": board, "inside": inside, "labels": labels, "rows": rows,
                          "was": json.dumps(board, sort_keys=True) if board else ""}
        return held[case]

    def lpet_op(case: str, op: dict, n: int) -> list[str]:
        at = opened(case)
        if at["board"] is None:
            if op.get("op") == "states_from_notes" and op.get("participant") in (None, ""):
                return []
            raise WorkbookError(i18n.t("server.trajectory_no_lpets", name=traj_mod.who(case)))
        with lpets_scope(by_case[case]):
            return gets_mod.row_op(at["data"], at["board"], at["inside"], at["labels"], op, traj_mod.who(case),
                                   turns=traj_turns(by_case[case]))

    def commit() -> None:
        for case, at in held.items():
            if at["board"] is None or json.dumps(at["board"], sort_keys=True) == at["was"]:
                continue
            at["board"]["updated"] = when
            with lpets_scope(by_case[case]):
                gets_mod.write(by_case[case], gets_mod._file(at["data"], when))

    # each participant's LPETs by id and title, for hide and show, read only when an operation names them
    ops = body.get("ops")
    wants = isinstance(ops, list) and any(isinstance(o, dict) and o.get("op") in ("hide", "show") for o in ops)
    lpets = {}
    if wants:
        for case in cases:
            lpets[case] = [{"id": r["id"], "title": r["title"]} for r in opened(case)["rows"]]
    # a participant's label and picture are their own set's, in the project file (pbiobuild): the board's title and
    # picture ops change that set, Trajectories' old labels and pictures moved into it first when it writes
    dry = ticked(body.get("dry_run"), False)
    wants_set = isinstance(ops, list) and any(isinstance(o, dict) and o.get("op") in ("title", "picture") for o in ops)
    held_set = person_change(root, dry=dry or not wants_set)

    def commit_all() -> None:
        commit()
        held_set.write(hist_mod.asker(body))

    done = traj_mod.change(root, cases, ops, when, dry_run=dry,
                           note=str(body.get("note") or ""), tool=str(body.get("tool") or ""),
                           lpets=lpets, lpet_op=lpet_op, commit=commit_all, set_person=held_set.apply)
    return traj_reply(root, body, done["data"], {"changes": done["changes"], "dry_run": done["dry_run"]})


def traj_picture_url(root: Path, picture: str) -> str:
    """Where the page reads a participant's picture: one of the set from the app's own files, his own from the
    project folder through `stream_traj_picture`, its time in the address so a new one is read afresh."""
    if not picture:
        return ""
    if picture.startswith("set:"):
        return f"/faces/{picture[4:]}.svg"
    file = traj_mod.pictures_of(root) / picture
    try:
        stamp = file.stat().st_mtime_ns
    except OSError:
        return ""
    return "/traj-picture?" + urlencode({"root": srv.rel_path(root), "name": picture, "v": stamp})


def stream_traj_picture(handler, query: dict) -> None:
    """A participant's own picture from the project's pictures folder, by its name alone, never a path."""
    try:
        root = srv.abs_path(query.get("root", ""))
    except Exception:
        return handler._send(400, b"Bad path", "text/plain; charset=utf-8")
    name = traj_mod.picture_kept(query.get("name", ""))
    if not query.get("root") or not srv.within_root(root) or not name or name.startswith("set:"):
        return handler._send(403, b"That picture is not a project's.", "text/plain; charset=utf-8")
    file = traj_mod.pictures_of(root) / name
    if not file.is_file() or not srv.within_root(file):
        return handler._send(404, b"No picture of that name.", "text/plain; charset=utf-8")
    kind = {"png": "image/png", "jpg": "image/jpeg", "svg": "image/svg+xml"}[name.rsplit(".", 1)[1]]
    handler.send_response(200)
    handler.send_header("Content-Type", kind)
    handler.send_header("Content-Length", str(file.stat().st_size))
    handler.send_header("Cache-Control", "no-store")
    # an SVG drawn as a picture runs nothing, and opened alone it may still run nothing
    handler.send_header("Content-Security-Policy", "default-src 'none'; style-src 'unsafe-inline'")
    handler.end_headers()
    handler.wfile.write(file.read_bytes())


# ------------------------------------------------------------------ each participant's own set (pbiobuild)

# Each participant's picture, label and pen portrait (pbiobuild, 11 November 2026, Adam's layout A), kept once for
# the project in its file under `participants` (see `participants.py`). Every screen that names a participant reads
# it through `person_of`: the project page's rows, the pickers, the bars over the statements screen, PETs and LPETs
# and the GETs' Participants panel, and Trajectories reads its picture and label from it. One route changes it,
# /api/participant, which the page's row, `participant set` and MCP's `participant_set` all run.


def people_view(root: Path | None) -> dict:
    """Every participant's set of the project at a root, by label, Trajectories' old labels and pictures merged in
    where the project file holds none (`participants.view`). Only reads."""
    if root is None:
        return {}
    return people_mod.view(root, project_file(Path(root)))


def person_url(root: Path, kept: dict) -> str:
    """Where the page reads a participant's picture: one of the set from the app's own files, his own from the
    project's `pictures/` through `stream_person_picture`, its time in the address so a new one is read afresh, and
    one Trajectories keeps still from its own folder."""
    picture = str(kept.get("picture") or "")
    if not picture or picture.startswith("set:") or kept.get("from_traj"):
        return traj_picture_url(root, picture)
    file = people_mod.pictures_of(root) / picture
    try:
        stamp = file.stat().st_mtime_ns
    except OSError:
        return ""
    return "/participant-picture?" + urlencode({"root": srv.rel_path(root), "name": picture, "v": stamp})


def person_of(root: Path | None, people: dict, case: str, colour: int | None = None) -> dict:
    """One participant's set as the screens draw it (`participants.shown`)."""
    kept = people_mod.find(people, case)
    return people_mod.shown(case, kept, person_url(root, kept) if root is not None else "", colour)


def person_for_book(path: Path) -> dict | None:
    """The set of the participant a workbook belongs to, for the bar over their screens, with their colour on the
    GETs board. None outside a project."""
    root = project_root(Path(path))
    if root is None:
        return None
    case = case_label(path)
    return person_of(root, people_view(root), case, people_colours(root, project_cases(root) + [case]).get(case))


def people_colours(root: Path, cases: list[str]) -> dict[str, int]:
    """Each participant's colour on the GETs board, his choice or their place round the palette among `cases`,
    the project's participants."""
    return {c: v["colour"] for c, v in gets_mod.looks(list(dict.fromkeys(cases)), gets_file(root)).items()}


def project_file_held(root: Path) -> dict:
    """The project file for a write: an empty one when there is none, refused when it is there and cannot be read,
    so nothing is written over a file that can be recovered."""
    file = Path(root) / srv.PROJECT_FILE
    if not file.exists():
        return {}
    try:
        data = json.loads(file.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        raise WorkbookError(i18n.t("server.could_read_nothing_written", name=file.name)) from None
    if not isinstance(data, dict):
        raise WorkbookError(i18n.t("server.could_read_nothing_written", name=file.name))
    return data


def people_settle(root: Path, who: dict | None = None) -> list[str]:
    """Trajectories' old labels and pictures moved into the participants' own sets for good, once, the caller
    holding the project's lock (`participants.settle`), with one History line. The demo is fixed and moves none."""
    if root is None or srv.is_demo_root(root) or not people_mod.unsettled(root):
        return []
    data = project_file_held(root)
    lines = people_mod.settle(root, data, Path(root) / srv.PROJECT_FILE, themes_mod.now_iso(), srv.save_json,
                              traj_mod.write)
    if lines:
        hist_mod.record(root, "participant set", lines, who)
    return lines


def people_settled(root: Path | None) -> None:
    """The project page's listing moves Trajectories' old labels and pictures over the first time
    (`people_settle`), under the project's lock. Busy or unwritable, it is left for the next, every screen reading
    them merged meanwhile."""
    if root is None or not Path(root).is_dir() or srv.is_demo_root(root) or not people_mod.unsettled(root):
        return
    with contextlib.suppress(WorkbookError, OSError):
        with writing(root=root):
            people_settle(root)


class person_change:
    """A change to the participants' sets of a project, made in memory by `apply` and written by `write`, once:
    the pictures, the project file with every other key kept, and one History record. With `dry` it reads the sets
    as every screen does and writes nothing. Otherwise Trajectories' old labels and pictures are moved over first
    (`people_settle`). The caller holds the project's lock."""

    def __init__(self, root: Path, dry: bool = False):
        self.root, self.dry = Path(root), dry
        self.files: dict = {}
        self.lines: list[str] = []
        self.settled: list[str] = []
        self.names = pseudo_list(root)
        if dry:
            self.project = {}
            self.people = {k: {f: v for f, v in kept.items() if f != "from_traj"}
                           for k, kept in people_view(root).items()}
            return
        if srv.is_demo_root(self.root):
            raise WorkbookError(i18n.t("server.demo_s_project_fixed"))
        self.settled = people_settle(self.root)
        self.project = project_file_held(self.root)
        self.people = people_mod.own_of(self.project)

    def apply(self, case: str, given: dict) -> list[str]:
        if srv.is_demo_root(self.root):
            raise WorkbookError(i18n.t("server.demo_s_project_fixed"))
        said = people_mod.apply(self.people, case, given, self.files, self.names)
        self.lines += said
        return said

    def write(self, who: dict | None = None) -> None:
        if self.dry or not self.lines:
            return
        when = themes_mod.now_iso()
        if self.files:
            traj_mod.picture_files(self.root, self.files, when, folder=people_mod.pictures_of(self.root))
        sets = people_mod.written(self.people)
        if sets:
            self.project[people_mod.KEY] = sets
        else:
            self.project.pop(people_mod.KEY, None)
        srv.save_json(self.root / srv.PROJECT_FILE, self.project)
        hist_mod.record(self.root, "participant set", self.lines, who)


def project_cases(root: Path) -> list[str]:
    """Every participant of a project by their label, as its page lists them, each once."""
    return list(dict.fromkeys(row["case"] for row in list_cases(root) if row.get("case")))


def participant_asked(body: dict) -> tuple[Path, str]:
    """The project and the participant a call names: `root`, the project's id, or `path`, a workbook of it, and
    `case`, the participant by their label or pseudonym, any case. Refused when they are not one of its."""
    root = asked_root(body, write=True)
    if root is None:
        raise WorkbookError(i18n.t("server.project_folder_project_could_saved"))
    named = body.get("case") or (case_label(case_path(body["path"])) if body.get("path") else "")
    case = traj_mod.find_case(project_cases(root), named)
    if case is None:
        raise WorkbookError(i18n.t("server.trajectory_not_a_participant", name=traj_mod.words(named) or "Nobody"))
    return root, case


def participant_answer(root: Path, case: str, people: dict | None = None) -> dict:
    """A participant's set as the route, `participant show` and MCP answer it."""
    people = people_view(root) if people is None else people
    return person_of(root, people, case, people_colours(root, project_cases(root) + [case]).get(case))


def api_participant(body: dict) -> dict:
    """A participant's picture, label and pen portrait (pbiobuild, 11 November 2026), read with `op` `show`, or
    changed with any of `label`, `portrait`, `picture` (`set:face07`, or "" to take it off), `data` (a picture as
    the page sends it, a data URL) or `from` (an image file's path, an agent's), each left out kept as it is and ""
    clearing it. The whole is refused, nothing written, for the demo, a participant not of the project, a label
    or a pen portrait over its limit or holding a name from the project's list of names to replace, or a picture
    that cannot be read. With `dry_run` nothing is written. Answers `person`, the set as it is or would be,
    `changes`, a line each, kept in the project's History, and `dry_run`."""
    given = {k: body.get(k) for k in ("label", "portrait", "picture", "data", "from") if body.get(k) is not None}
    show = str(body.get("op") or ("set" if given else "show")) == "show"
    if not show and srv.is_demo_root(asked_root(body, write=True)):
        raise WorkbookError(i18n.t("server.demo_s_project_fixed"))
    root, case = participant_asked(body)
    if show:
        return {"case": case, "person": participant_answer(root, case), "changes": [], "dry_run": False}
    if ticked(body.get("dry_run"), False):
        held = person_change(root, dry=True)
        lines = held.apply(case, given)
        person = participant_answer(root, case, held.people)
        # a picture not yet written has no address, so the dry run shows none for it
        return {"case": case, "person": dict(person, picture_url="") if held.files else person, "changes": lines,
                "dry_run": True}
    with writing(root=root):
        held = person_change(root)
        lines = held.apply(case, given)
        held.write(hist_mod.asker(body))
    return {"case": case, "person": participant_answer(root, case), "changes": held.settled + lines, "dry_run": False}


def stream_person_picture(handler, query: dict) -> None:
    """A participant's own picture from the project's `pictures/` folder, by its name alone, never a path."""
    try:
        root = srv.abs_path(query.get("root", ""))
    except Exception:
        return handler._send(400, b"Bad path", "text/plain; charset=utf-8")
    name = traj_mod.picture_kept(query.get("name", ""))
    if not query.get("root") or not srv.within_root(root) or not name or name.startswith("set:"):
        return handler._send(403, b"That picture is not a project's.", "text/plain; charset=utf-8")
    file = people_mod.pictures_of(root) / name
    if not file.is_file() or not srv.within_root(file):
        return handler._send(404, b"No picture of that name.", "text/plain; charset=utf-8")
    kind = {"png": "image/png", "jpg": "image/jpeg", "svg": "image/svg+xml"}[name.rsplit(".", 1)[1]]
    handler.send_response(200)
    handler.send_header("Content-Type", kind)
    handler.send_header("Content-Length", str(file.stat().st_size))
    handler.send_header("Cache-Control", "no-store")
    # an SVG drawn as a picture runs nothing, and opened alone it may still run nothing
    handler.send_header("Content-Security-Policy", "default-src 'none'; style-src 'unsafe-inline'")
    handler.end_headers()
    handler.wfile.write(file.read_bytes())


# ------------------------------------------------------------------ the code list (codes, 2 November 2026)

def codes_root(body: dict) -> Path:
    """The thematic analysis project a code list request is for, found as a GETs request finds its project, and
    refused in an IPA project, which has no code list."""
    root = gets_root(body)
    codes_mod.refuse_unless_ta(read_project(root).get("method"))
    return root


def codes_reply(root: Path, body: dict, view: dict, more: dict | None = None) -> dict:
    """The code list as the Code list screen draws it, with the project for the bar and each participant's colour
    and letter as the Themes board gives them."""
    project = read_project(root)
    cfg = srv.config()
    look = gets_mod.looks([p["case"] for p in view["participants"]], gets_mod.load(root))
    for p in view["participants"]:
        mine = look.get(p["case"]) or {}
        p.update(colour=mine.get("colour", 0), badge=mine.get("badge") or p["who"][:1].upper(),
                 path=srv.rel_path(Path(p["workbook"])))
    return dict(view, **(more or {}), project=project, demo=project["demo"], root=srv.rel_path(root),
                path=str(body.get("workbook") or body.get("path") or ""), config=cfg, platform=srv.PLATFORM,
                feedback=bool(srv.feedback_url(cfg)))


def codes_list(root: Path) -> dict:
    """The list as it reads now, made first on a project's first read, under the project's lock when it writes."""
    books = gets_books(root)
    with writing(root=root, books=[b["workbook"] for b in books]):
        data = codes_mod.ensure(root, books, themes_mod.now_iso())
    return codes_mod.listing(data, codes_mod.study_rows(books))


def api_codes(body: dict) -> dict:
    """A thematic analysis project's code list (see `codes.py`): every code with its description, its counts and
    its extracts by participant, `v` its version. A project made before the list has it made on this first read,
    each board gathering each code's cards in one place, a revision kept first."""
    root = codes_root(body)
    return codes_reply(root, body, codes_list(root))


def api_codes_ops(body: dict) -> dict:
    """A change to the code list, `ops` a list of operations (see `codes.apply`): a code new, renamed, described,
    merged into another or deleted, rename and merge reaching every workbook and every board. All or nothing,
    each file checked first, `v` the version the page read, and with `dry_run` nothing is written. Answers the
    list as it is, or would be, with `changes`."""
    root = codes_root(body)
    return codes_apply(root, body)


def codes_apply(root: Path, body: dict) -> dict:
    """The change itself, for the route and the command line alike."""
    books = gets_books(root)
    dry = ticked(body.get("dry_run"), False)
    with writing(root=root, books=[] if dry else [b["workbook"] for b in books]):
        try:
            done = codes_mod.change(root, books, body.get("ops"), themes_mod.now_iso(), dry_run=dry,
                                    note=themes_ai.one_line(body.get("note") or ""),
                                    tool=themes_ai.one_line(body.get("tool") or ""), seen=body.get("v"))
        except codes_mod.Stale as exc:
            return {"error": str(exc), "stale": True, "status": 409}
    view = done.pop("list")
    return codes_reply(root, body, view, done)


def api_codes_extract(body: dict) -> dict:
    """A code put on one extract of a passage, or taken off it (`op` of `add` or `remove`), as the Coding screen's
    Add a code and a chip's x do through the passage's save: `case`, `sheet`, `row`, `quote`, the extract's words,
    and `code`, a code of the list or a new name. With `dry_run` nothing is written."""
    root = codes_root(body)
    books = gets_books(root)
    dry = ticked(body.get("dry_run"), False)
    with writing(root=root, books=[] if dry else [b["workbook"] for b in books]):
        done = codes_mod.extract_change(root, books, body.get("op"), str(body.get("case") or ""),
                                        str(body.get("sheet") or ""), body.get("row") or 0, body.get("quote"),
                                        body.get("code"), themes_mod.now_iso(), dry_run=dry,
                                        note=themes_ai.one_line(body.get("note") or ""),
                                        tool=themes_ai.one_line(body.get("tool") or ""))
    return done


def api_codes_quick(body: dict) -> dict:
    """The Coding screen's quick keys for an agent (quickkeysB, 9 November 2026): words a passage holds made a new
    extract with a code at once, `op` of `last`, the code used last or with `n` of 2 to 5 that one of the codes used
    last, or `in-vivo`, a code named by the words (see `codes.quick`). `case`, `sheet`, `row` and `words`. With
    `dry_run` nothing is written."""
    root = codes_root(body)
    books = gets_books(root)
    dry = ticked(body.get("dry_run"), False)
    with writing(root=root, books=[] if dry else [b["workbook"] for b in books]):
        return codes_mod.quick(root, books, body.get("op"), str(body.get("case") or ""), str(body.get("sheet") or ""),
                               body.get("row") or 0, body.get("words"), themes_mod.now_iso(), n=body.get("n") or 1,
                               dry_run=dry, note=themes_ai.one_line(body.get("note") or ""),
                               tool=themes_ai.one_line(body.get("tool") or ""))


def api_codes_suggest(body: dict) -> dict:
    """Codes for one extract of a passage on the Coding screen (taaibuild, 3 November 2026, Adam's Coding A): the
    project's codes that fit, up to three with their counts, then up to two new names, from one call through the
    route the Experiential statements' suggestions take, with the project's research question and the Coding rail's
    lines about a code. The page sends the passage, `turn`, the interviewer's before it, `prior`, its `time`, the
    participant's `name`, the extract, `quote`, and the codes on it, `on`: the passage in question alone. Nothing is
    written, a code being taken by Add a code's own save. Refused, with nothing asked, while AI features or the
    Experiential statements' own switch is off, and in an IPA project, which has no code list."""
    cfg = srv.config()
    if not srv.ai_on(cfg, "statements"):
        return {"error": themes_ai.OFF}
    root = codes_root(body)
    route = srv.ai_route(cfg, {"path": body.get("workbook") or body.get("path")})
    on = [str(x) for x in body.get("on")[:50] if isinstance(x, str)] if isinstance(body.get("on"), list) else []
    started = time.monotonic()
    result = ta_ai.suggest_codes(str(body.get("turn") or "")[:20000], str(body.get("prior") or "")[:20000],
                                 str(body.get("name") or "")[:200], str(body.get("time") or "")[:40],
                                 str(body.get("quote") or "")[:4000], on, codes_list(root)["codes"],
                                 guidance_lines(i18n.long_text(TA_GUIDANCE)),
                                 read_project(root)["research_question"], route)
    if "error" not in result:
        result.update(model_name=route_name(route), seconds=round(time.monotonic() - started, 1))
    return result


def api_codes_undo(body: dict) -> dict:
    """The code list's last change undone, or with `redo` made again (see `codes.undo`): every file it wrote put
    back whole, refused with nothing written when one changed since."""
    root = codes_root(body)
    books = gets_books(root)
    dry = ticked(body.get("dry_run"), False)
    with writing(root=root, books=[] if dry else [b["workbook"] for b in books]):
        done = codes_mod.undo(root, books, themes_mod.now_iso(), redo=ticked(body.get("redo"), False), dry_run=dry,
                              tool=themes_ai.one_line(body.get("tool") or ""))
    view = done.pop("list")
    return codes_reply(root, body, view, done)


def api_gets_ai(body: dict) -> dict:
    """The GETs screen's AI help, three titles for a GET, `op` of `names`, as `/api/themes-ai` gives the
    PETs screen's, through the same route, `pets_route`, with the key and the project's research question,
    and refused while the switch in Settings is off. `group` names the GET, on the board `version` names,
    the one on the canvas when none is, read from the GETs file with every case not yet in as it would
    come in. Nothing is written. A thematic analysis project's Themes board asks nothing (aiout, 11
    November 2026: the board's AI review went, an agent of his own through MCP doing that work)."""
    if LPETS_FOR.get() is not None:
        raise WorkbookError(i18n.t("server.ai_s_help_lpets_yet"))
    if LGETS_FOR.get() is not None:
        raise WorkbookError(i18n.t("server.ai_s_help_lgets_yet"))
    cfg = srv.config()
    if not srv.ai_on(cfg, "gets"):
        return {"error": themes_ai.OFF}
    root = gets_root(body)
    project = read_project(root)
    if str(body.get("op") or "") != "names" or codes_mod.is_ta(project.get("method")):
        return {"error": i18n.t("server.something_ai_help_does_nothing"), "code": "unknown_op"}
    books = gets_books(root)
    question = project["research_question"]
    route = pets_route(cfg, {"research_question": question})
    started = time.monotonic()
    with srv._lock:
        data, cases, _disk, _taken = gets_mod.assemble(root, books, themes_mod.now_iso())
    vid = str(body.get("version") or "") or None
    source = themes_mod.find_version(data, vid) if vid else themes_mod.current_version(data)
    if source is None:
        raise WorkbookError(i18n.t("server.board_gone_gets_asked"))
    study_marks = gets_mod.study_of(data, [e["case"] for e in cases])
    inside = [e["case"] for e in cases if study_marks[e["case"]]["in"]]
    minimum, _band = gets_mod.minimum_of(gets_mod.settings_of(data), len(inside))
    board = gets_mod.ai_outline(data, source, inside, minimum)
    result = themes_ai.gets_names(themes_ai.gets_names_target(board, str(body.get("group") or "")), question, route)
    if "error" not in result:
        result.update(model_name=route_name(route), seconds=round(time.monotonic() - started, 1))
    return result


# each file of copies of a participant's statements by the name its boards go by
COPY_NAMES = {"gets": "GETs", "lpets": "LPETs", "lgets": "LGETs"}


@contextlib.contextmanager
def copy_scope(kind: str, path: Path, root: Path):
    """What runs inside works on one file of copies of a participant's statements (see `statement_copies`)."""
    if kind == "lpets":
        with lpets_scope(path):
            yield
    elif kind == "lgets":
        with lgets_scope(root):
            yield
    else:
        yield


def statement_copies(path: Path) -> tuple[Path | None, list[str]]:
    """The files across the participants that keep a copy of a participant's statements, in the order an edit
    reaches them (30 October 2026, getsedit): the project's GETs file, `gets`, and in a project of two or more
    timepoints the participant's LPETs, `lpets`, then the project's LGETs, `lgets`, which are made from the
    LPETs. The project's root with them, and none for a workbook in no project."""
    root = project_root(path)
    if root is None:
        return None, []
    return root, ["gets"] + (["lpets", "lgets"] if longitudinal(root_timepoints(root)) else [])


def copies_before(path: Path) -> dict:
    """Before a write to a participant's statements, each file of copies with each of their cases in it and
    whether its copy stands as its files do now (see `gets.copies_untouched`)."""
    root, kinds = statement_copies(path)
    out = {}
    for kind in kinds:
        try:
            with copy_scope(kind, path, root):
                out[kind] = gets_mod.copies_untouched(root, path, lpets_books(path) if kind == "lpets" else None)
        except (WorkbookError, OSError):
            out[kind] = {}
    return out


def follow_statements(path: Path, words: dict, before: dict, dry: bool = False, changed: dict | None = None,
                      history: str = "", said: dict | None = None) -> dict:
    """A participant's statements reworded in place, `words` each by its key with its words before and after,
    carried to every copy across the participants (getsedit, 30 October: an edit from a GETs, LGETs or LPETs
    board lands in the workbook and every copy follows): the GETs file's, and in a project of timepoints the
    participant's LPETs' and the LGETs', each through `gets.statements_followed`, `before` from `copies_before`,
    `said` his own edit's History line by each statement's key for every board with a card of it. Answers what
    each file took by its kind, and `failed`, a line for a file that could not be read, its copy left as it was
    and the workbook's change standing."""
    root, kinds = statement_copies(path)
    out, failed = {}, []
    for kind in kinds:
        try:
            with copy_scope(kind, path, root):
                done = gets_mod.statements_followed(root, path, words, before.get(kind) or {},
                                                    lpets_books(path) if kind == "lpets" else None,
                                                    dry=dry, changed=changed, history=history, said=said)
        except (WorkbookError, OSError) as exc:
            failed.append(f"The {COPY_NAMES[kind]} could not be read, so their copy kept the words it had: {exc}")
            continue
        if done:
            out[kind] = done
    if failed:
        out["failed"] = failed
    return out


def statements_noted(path: Path, said: dict) -> dict:
    """His statements reworded on the statements screen, `said` each one's History line by its key (see
    `themes.edit_line`), kept in the History of every board with a card of it across the participants, the GETs
    file's, and in a project of timepoints the participant's LPETs' and the LGETs', each through
    `gets.statements_noted`, the copies keeping their words (histreplace, 30 October 2026). Answers what each
    file's boards kept by its kind, and `failed`, a line for a file that could not be read."""
    root, kinds = statement_copies(path)
    out, failed = {}, []
    for kind in kinds:
        try:
            with copy_scope(kind, path, root):
                done = gets_mod.statements_noted(root, path, said, lpets_books(path) if kind == "lpets" else None)
        except (WorkbookError, OSError) as exc:
            failed.append(f"The {COPY_NAMES[kind]} could not be read, so their History has no line for it: {exc}")
            continue
        if done:
            out[kind] = done
    if failed:
        out["failed"] = failed
    return out


def edit_lines(path: Path, words: dict) -> dict:
    """Each statement's History line by its key, `words` holding its words before and after (see
    `themes.edit_line`), named for the participant at `path` by their pseudonym."""
    who = gets_mod.who(case_label(path))
    return {key: themes_mod.edit_line(who, old, new) for key, (old, new) in words.items()}


def api_edit_statement(body: dict) -> dict:
    """One statement edited in place on a board, the one case the boards write the workbook: `line`
    of `row` on `sheet` becomes `text`, every other line of the cell kept, behind the lock guard the
    turn screen's save uses. `old`, when the page sends it, is what the line read, and a line that
    reads otherwise now is refused. `check` asks whether this server has the route and writes
    nothing, and `copies` in its answer that it carries an edit to the GETs' copies, which a GETs,
    LGETs or LPETs board needs (30 October). The answer carries the new text, for the page to put on
    the card. Every other board of the case that held the old words takes the new ones (see
    `themes.statement_edited`), so none marks the card changed for an edit made on that screen, and
    so does every copy across the participants, under `copies` by file (see `follow_statements`),
    each with its boards' versions for a GETs board's next save. Every board that holds a card of the
    statement, the case's and each copy's, keeps itself first in its History under the edit's line (see
    `themes.edit_line`, histreplace, 30 October 2026), and `histories` in the answer, and in each copy's,
    gives each such board's revisions as the History tab lists them."""
    path = case_path(body.get("workbook") or body.get("path") or body["workbook"])
    if body.get("check"):
        return {"ready": True, "copies": True}
    with writing(path, root=project_root(path)):
        before = copies_before(path)
        out = wb_mod.edit_statement(path, str(body["sheet"]), int(body["row"]), int(body["line"]),
                                    body.get("text"), body.get("old"))
        if out.get("changed"):
            key = themes_mod.card_key(out["sheet"], out["row"], out["line"])
            said = edit_lines(path, {key: (out["old"], out["text"])})
            themes_mod.statement_edited(path, out["sheet"], out["row"], out["line"], out["old"], out["text"],
                                        said=said[key])
            # each board's version after it, so the page's next save carries the one this edit wrote
            # and is never refused as stale over its own edit (19 October)
            try:
                boards = themes_mod.boards_of(themes_mod.load(path))
                out["versions"] = [themes_mod.summary(b) for b in boards]
                out["histories"] = {str(b.get("id")): themes_mod.history_list(b) for b in boards
                                    if isinstance((b.get("cards") or {}).get(key), dict)}
            except WorkbookError:
                pass
            out["copies"] = follow_statements(path, {key: (out["old"], out["text"])}, before, said=said)
        return out


def pets_choice(cfg: dict) -> dict:
    """The PETs screen's own provider and model, in the fields `ai_route` takes from a body, or
    nothing when the PETs screen uses the Experiential statements ones. Both keys must be set: a
    provider with no model, or one this app does not know, is the statements' choice."""
    provider = cfg.get("pets_provider")
    model = str(cfg.get("pets_model") or "").strip()
    if provider not in ai_mod.PROVIDERS or not model:
        return {}
    return {"provider": provider, "local_model" if provider == ai_mod.LOCAL else "model": model}


def pets_route(cfg: dict, body: dict | None = None) -> dict:
    """The route the PETs screen's AI asks: its own provider and model when Settings sets them, and
    the Experiential statements route when not, with the key and the question as that route has
    them. The test bench never comes here."""
    return srv.ai_route(cfg, {**(body or {}), **pets_choice(cfg)})


def route_name(route: dict) -> str:
    return ai_mod.route_model(route)


def api_themes_ai(body: dict) -> dict:
    """The PETs screen's AI help, three titles for a PET or a sub-theme, `op` of `names`. It goes out
    through the PETs route, `pets_route`, the PETs screen's own provider and model when Settings sets
    them and a suggestion's when not, with the key and the project's research question, and is
    refused while the switch in Settings is off. Nothing is written.

    It takes the label by its id, `group`, on the board `version` names, the current one when none is,
    and builds the prompt from the workbook and the board: the theme with its statements in canvas
    order, each with every quote of its turn, the picks marked, its sub-themes, and the other labels.
    It answers with up to three `names`, and `said` when quotes went for room. A page from before it
    sends `statements`, `label`, `note` and `others` with no `group`, which builds the prompt it always
    did. New AI board, AI review and AI revise went on 11 November 2026 (aiout, Adam: an agent of his
    own through MCP does that work)."""
    cfg = srv.config()
    if not srv.ai_on(cfg, "pets"):
        return {"error": themes_ai.OFF}
    path = case_path(body.get("workbook") or body.get("path") or body["workbook"])
    if str(body.get("op") or "") != "names":
        return {"error": i18n.t("server.something_ai_help_does_nothing"), "code": "unknown_op"}
    route = pets_route(cfg, {"path": str(path)})
    started = time.monotonic()
    gid = str(body.get("group") or "")
    if not gid:
        # a page from before the whole theme went sends its statements as bare text
        statements = [str(t) for t in body.get("statements") or [] if str(t).strip()][:300]
        others = [str(t) for t in body.get("others") or [] if str(t).strip()][:100]
        result = themes_ai.names(statements, str(body.get("label") or ""), others,
                                 route["research_question"], route, note=str(body.get("note") or "")[:4000])
    else:
        vid = str(body.get("version") or "") or None
        with srv._lock:
            read = themes_mod.read_cards(path)
            data = themes_mod.load(path)
        source = themes_mod.pick_version(data, vid)
        if source is None:
            if vid and themes_mod.boards_of(data):
                raise WorkbookError(i18n.t("server.board_gone_themes_asked"))
            source = themes_mod.blank_version(read["cards"])
        # the theme as the workbook and the board hold it, built here, never from what the page sends
        result = themes_ai.pet_names(themes_ai.names_target(read, source, gid), route["research_question"], route)
    if "error" not in result:
        result.update(model_name=route_name(route), seconds=round(time.monotonic() - started, 1))
    return result


def case_relative(workbook: Path, target: Path) -> str:
    """A file in a case's folder as the Themes screen names it, `Working/<file>`: never the folder's
    own name, so the second part of a GRAVITY folder never reaches the line."""
    return Path(target).resolve().relative_to(Path(workbook).parent.resolve()).as_posix()


def reveal_in_finder(target: Path) -> None:
    subprocess.run(["open", "-R", str(target)], check=False, timeout=15,
                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


REVEAL = reveal_in_finder


def themes_reveal(path: Path, body: dict) -> dict:
    """Show a file the export wrote in the Finder. `file` is the case-relative path the export
    answered with, `Working/<file>`, or a Word document's own name at the case's root, and the
    board's markdown draft is the one when there is none. Anything else that resolves outside the
    case's own `Working/` folder or the case root, or that is not there, is refused, and so is any
    machine but a Mac."""
    if srv.PLATFORM != "darwin":
        raise WorkbookError(i18n.t("server.show_finder_mac_only"))
    working = (path.parent / "Working").resolve()
    named = str(body.get("file") or "").strip()
    if named:
        target = (path.parent / named).resolve()
    else:
        data = themes_mod.load(path)
        version = themes_mod.pick_version(data, str(body.get("version") or "") or None)
        target = themes_mod.draft_path(path, (version or {}).get("name") or themes_mod.FIRST_NAME).resolve()
    # a Word document or a PDF of the table sits beside the workbook, the files there Show in Finder opens on
    beside = target.parent == path.parent.resolve() and target.suffix.lower() in (".docx", ".pdf", ".png")
    try:
        if not beside:
            target.relative_to(working)
    except ValueError:
        raise srv.OutsideRoot(i18n.t("server.file_sits_outside_participant_s"))
    if not srv.within_root(target):
        raise srv.OutsideRoot(i18n.t("server.file_sits_outside_project_folder"))
    if not target.is_file():
        raise WorkbookError(i18n.t("server.file_more_export_again_write"))
    REVEAL(target)
    return {"revealed": case_relative(path, target)}


def api_themes_export(body: dict) -> dict:
    """A board's PET grouping draft in markdown, and the statements CSV with its Proposed PET
    column from the same board, both in the case's `Working/` folder. `version` names one, and
    the current one goes when it does not. The workbook is only read, so Excel's lock is no bar.
    `shown` names the two files the way the screen says them, `Working/<file>`.

    With `op` of `reveal`, nothing is written: the file named, the markdown draft when none is,
    is shown in the Finder, on a Mac alone. With `op` of `word`, the board is written as a Word
    document at the case's root, beside the workbook, never over a file there (see
    `themes_word.py`), and `word` and `shown` name it as the case holds it. Both label the PETs as
    the case's project labels them (see `pet_labels_for`), and `labels` says which way.

    With `dry_run` (26 October, for the agents' `board export --draft`) the board is read and the
    draft made in memory, and nothing is written: the answer names the two files, `markdown` and
    `csv`, as the case holds them, and `there`, those of them a write would put a new copy over."""
    path = case_path(body.get("workbook") or body.get("path") or body["workbook"])
    if str(body.get("op") or "") == "reveal":
        return themes_reveal(path, body)
    case = case_label(path)
    vid = str(body.get("version") or "") or None
    # the PETs labelled as the case's project labels them, the book's letters unless it says numbers
    labels = pet_labels_for(path)
    if str(body.get("op") or "") == "pdf":
        return themes_pdf_place(path, case, vid, labels, body)
    if str(body.get("op") or "") == "canvas":
        return themes_canvas(path, case, vid, body)
    if str(body.get("op") or "") == "word":
        unplaced, binned = export_includes(body)
        with writing(path, export=True):
            made = themes_word.write(path, case, vid, labels=labels, unplaced=unplaced, binned=binned,
                                     stacked=export_stacked(body), sending=export_sending(body),
                                     descriptions=export_descriptions(body), author=researcher_name(),
                                     who=portrait_printed(path, body))
        shown = case_relative(path, Path(made["path"]))
        return {"word": shown, "shown": [shown], "paths": [srv.display_path(srv.rel_path(Path(made["path"])))],
                "dated": made["dated"], "counts": made["counts"], "version": made["version"], "labels": labels}
    if body.get("dry_run") is True:
        _text, board = themes_mod.draft_markdown(path, case, vid, labels, export_stacked(body))
        files = [themes_mod.draft_path(path, board["name"]), export_mod.output_path(path)]
        shown = [case_relative(path, f) for f in files]
        return {"dry_run": True, "markdown": shown[0], "csv": shown[1], "shown": shown,
                "there": [x for x, f in zip(shown, files) if f.exists()],
                "version": themes_mod.summary(board), "labels": labels}
    with writing(path, export=True):
        draft = themes_mod.write_draft(path, case, vid, labels, stacked=export_stacked(body))
        tps = project_timepoints(path)
        # at a timepoint, that timepoint's statements alone, labelled from this board
        here = [(t["n"], t["label"]) for t in tps if t["n"] == themes_mod.timepoint_now()] if longitudinal(tps) else None
        csv_out = export_mod.export(path, themes=(themes_mod.themes_path(path), vid), guard=False, timepoints=here)
    # lines on the screen, so the case folder shows by its pseudonym alone
    shown = [srv.display_path(srv.rel_path(Path(p))) for p in (draft["path"], csv_out["path"])]
    return {"markdown": shown[0], "csv": shown[1], "paths": shown,
            "shown": [case_relative(path, Path(p)) for p in (draft["path"], csv_out["path"])],
            "statements": csv_out["statements"], "version": draft["version"], "labels": labels}


def themes_pdf_place(path: Path, case: str, vid, labels: str, body: dict) -> dict:
    """Export as PDF of the table of PETs (31 October 2026, pdfexport), written by the server through Typst (typst5, 9
    November 2026, Adam: Typst for every PDF, no fallback), the same file the agents' `board export --pdf` writes:
    beside the workbook as the Word document goes, named as the print view names it, the date and time in the name
    when a file has it, with the ticks as sent and the board's note left off, as Export has always left it. `shown`
    names it as the case holds it, for the line after. With `dry_run` nothing is made or written. When Typst cannot
    make it the answer is its plain sentence and nothing is written."""
    unplaced, binned = export_includes(body)
    held = read_project(project_root(path))
    with writing(path, export=True):
        made = print_pdf.write(path, case, vid, held["research_question"], labels=labels, unplaced=unplaced,
                               binned=binned, stacked=export_stacked(body), sending=export_sending(body),
                               dry_run=body.get("dry_run") is True, descriptions=export_descriptions(body),
                               project=held.get("name") or "", researcher=researcher_name(),
                               who=portrait_printed(path, body))
    shown = case_relative(path, Path(made["path"]))
    out = {"pdf": shown, "shown": [shown], "path": made["path"], "name": made["name"], "dated": made["dated"],
           "version": made["version"], "labels": labels}
    return dict(out, dry_run=True) if made.get("dry_run") else out


def canvas_written(made: dict, data: dict, body: dict, shown) -> dict:
    """The canvas's file made by Typst and written at the place named (typst5, 9 November 2026), `shown` naming it
    for the line after, with its size in bytes and a picture's in pixels. With `dry_run` nothing is made or written.
    When Typst cannot make it the answer is its plain sentence and nothing is written."""
    done = canvas_out.made(made, data, dry_run=body.get("dry_run") is True)
    out = dict(done, shown=[shown(done["path"])])
    return dict(out, dry_run=True) if body.get("dry_run") is True else out


def canvas_how(body: dict, gets: bool = False) -> dict:
    """What the canvas's file shows as the canvas shows it: `quotes`, Quotes on cards, off, short or full, as the
    settings hold it when the request says none, on GETs `notes`, Include participant notes, and on PETs the close
    pairs' lines while Close pairs is on in the settings."""
    cfg = srv.config()
    way = str(body.get("quotes") or canvas_out.quotes_of(cfg))
    how = {"quotes": way if way in canvas_out.QUOTES else "off", "notes": ticked(body.get("notes"), False)}
    if not gets:
        how["close"] = canvas_out.close_of(cfg)
    return how


def themes_canvas(path: Path, case: str, vid, body: dict) -> dict:
    """The canvas of a participant's board as a PDF or a PNG (`kind`), beside the workbook where the table's PDF
    goes, named as the table's with " canvas" after it, "P9 - Wren - Board 3 - PETs canvas.png", drawn by Typst
    from the board as its file keeps it (see `canvas_written`)."""
    kind = canvas_out.kind_of(body.get("kind"))
    _board, version = themes_word.board_of(path, vid)
    title = themes_print.title_of(case, version.get("name") or themes_mod.FIRST_NAME)
    made = canvas_out.place(path.parent, canvas_out.stem_of(title), kind)
    with writing(path, export=True):
        data = canvas_out.pets_data(path, case, str(version.get("id") or "") or None, **canvas_how(body))
        out = canvas_written(made, data, body, lambda p: case_relative(path, Path(p)))
    return dict(out, version=themes_mod.summary(version))


def gets_canvas(root: Path, body: dict) -> dict:
    """The canvas of a GETs board as a PDF or a PNG (`kind`), at the project's root where the GETs print card's PDF
    goes, "Study - Board 2 - GETs canvas.png", or a participant's LPETs (`lpets`) beside their workbook, drawn by
    Typst from the board as its file keeps it (see `canvas_written`)."""
    kind = canvas_out.kind_of(body.get("kind"))
    data = gets_mod.load(root)
    asked = str(body.get("board") or "")
    board = next((b for b in themes_mod.boards_of(data) if str(b.get("id")) == asked), None) if asked and data else None
    if board is None:
        raise WorkbookError(i18n.t("page_print.gets.board_gone"))
    name = str(board.get("name") or themes_mod.FIRST_NAME)
    value = body.get("workbook") or body.get("path")
    if value and ticked(body.get("lpets"), False):
        path = case_path(value)
        folder, title, heading = path.parent, f"{case_label(path)} - {name} - LPETs", case_label(path)
    else:
        project = read_project(root).get("name") or "GETs"
        folder, title, heading = Path(root), f"{project} - {name} - GETs", project
    made = canvas_out.place(folder, canvas_out.stem_of(title), kind)
    books = gets_books(root)
    with writing(root=root):
        drawn = canvas_out.gets_data(root, books, heading, str(board.get("id") or ""), **canvas_how(body, gets=True))
        out = canvas_written(made, drawn, body, lambda p: Path(p).name)
    return dict(out, version={"id": str(board.get("id") or ""), "name": name})


def export_includes(given: dict) -> tuple[bool, bool]:
    """Whether the PETs table's export, the print view or the Word document, puts Not placed and
    Discarded at its end: as the request says, `unplaced` and `binned` as 1 or 0 in a query or true
    or false in a body, and otherwise as his two ticks were last left in the settings, both off on a
    new install."""
    return export_tick(given, "unplaced", "export_not_placed"), export_tick(given, "binned", "export_binned")


def export_sending(given: dict) -> bool:
    """Whether an export is for sending, named by the case alone with no board on the page, as
    `sending` says, 1 or 0 in a query or true or false in a body, and otherwise as For sending was
    last left in the settings, off on a new install (Adam, 19 October)."""
    return export_tick(given, "sending", "export_for_sending")


def export_descriptions(given: dict) -> bool:
    """Whether an export of a board, the print view or the Word table, puts each label's description
    under its title, as `descriptions` says, 1 or 0 in a query or true or false in a body, and otherwise
    as Descriptions was last left in the settings, on on a new install (Adam, 21 October)."""
    value = given.get("descriptions")
    if value is None or value == "":
        return srv.config().get("export_descriptions") is not False
    return value in (True, 1, "1", "true")


def export_tick(given: dict, asked: str, key: str) -> bool:
    """One of the export's ticks, as the request gives it, else as the settings hold it."""
    value = given.get(asked)
    return bool(srv.config().get(key)) if value is None or value == "" else value in (True, 1, "1", "true")


def export_stacked(given: dict) -> bool:
    """Whether an export of the PETs, the print view, the Word document or the PET draft, puts the
    statements stacked under a top beneath it (19 October): as the request says, `stacked` as 1 or 0
    in a query or true or false in a body, and otherwise as his tick Include stacked statements was
    last left in the settings, off on a new install, so the top stands for its stack alone."""
    value = given.get("stacked")
    if value is None or value == "":
        return bool(srv.config().get("export_stacked"))
    return value in (True, 1, "1", "true")


def export_portrait(given: dict) -> bool:
    """Whether an export of the table of PETs, the print view, the PDF or the Word document, puts the participant's
    label and pen portrait under the head (pbioexport, 11 November 2026): as the request says, `portrait` as 1 or 0
    in a query or true or false in a body, and otherwise as Pen portrait under Export was last left, off on a new
    install."""
    return export_tick(given, "portrait", "export_portrait")


def export_participants(given: dict) -> bool:
    """Whether a print of the GETs, the GET table, the audit trail or the full set, its PDF and a theme table's Word
    document, opens with the participants table (pbioexport): as the request says, `participants` as 1 or 0 in a
    query or true or false in a body, and otherwise as Participants table on the print card was last left, off on
    a new install."""
    return export_tick(given, "participants", "export_participants")


def portrait_printed(path: Path, given: dict) -> dict | None:
    """What the table of PETs prints of its participant under the head (pbioexport): their label and pen portrait,
    never their picture (`participants.printed`), an empty set for a participant with neither, and None while Pen
    portrait is off (`export_portrait`)."""
    if not export_portrait(given):
        return None
    root = project_root(Path(path))
    return people_mod.printed(people_mod.find(people_view(root), case_label(path)))


def people_printed(root: Path, given: dict) -> dict | None:
    """Every participant's set for a print of the GETs' participants table (pbioexport), read as every screen reads
    them (`people_view`), and None while Participants table is off (`export_participants`)."""
    return people_view(Path(root)) if export_participants(given) else None


# The print view of a board, a page the browser prints or saves as PDF, by GET.
PRINT_PATH = "/themes/print"


def researcher_name() -> str:
    """The researcher the print views' foot names beside Confidential and Word's author field holds (Adam, 31
    October 2026): Settings' Your name, the name documents carry, and while it is empty the Interviewer's name,
    which also tells the interviewer's turns apart in a transcript, so may be a first name alone. Empty when
    the settings hold neither."""
    cfg = srv.config()
    return " ".join(str(cfg.get("your_name") or "").split()) or " ".join(str(cfg.get("interviewer") or "").split())


def themes_print_page(query: dict) -> tuple[int, str]:
    """The print view of a board, `/themes/print?workbook=<path>&board=<id>`, as HTML rendered from
    the board, the current one when `board` is empty. The workbook and the themes file are only
    read, and nothing is written anywhere. The case is named by its pseudonym. A workbook outside
    the case root is refused, and so is a board the file does not hold, each as a page of one line.
    `auto=0` leaves the print dialog shut, for a look at the page, and `note=1` puts the board's
    note under the head, which the page leaves out without it. `unplaced` and `binned`, 1 or 0, put
    Not placed and Discarded at its end or leave them out, and without them the page follows his two
    ticks as the settings hold them (see `export_includes`). `sending`, 1 or 0, leaves the board's
    name off the page and out of its title, which names the PDF, or keeps them, the settings deciding
    without it (see `export_sending`). `portrait`, 1 or 0, puts the participant's label and pen portrait under
    the head or leaves them out, the settings deciding without it (see `portrait_printed`)."""
    try:
        path = case_path(str(query.get("workbook") or ""))
        case = case_label(path)
        held = read_project(project_root(path))
        question = held["research_question"]
        unplaced, binned = export_includes(query)
        with srv._lock, route_scope(PRINT_PATH, query):
            return 200, themes_print.page(path, case, str(query.get("board") or "") or None, question,
                                          auto=str(query.get("auto") or "") != "0",
                                          note=str(query.get("note") or "") == "1", labels=pet_labels_for(path),
                                          unplaced=unplaced, binned=binned, stacked=export_stacked(query),
                                          sending=export_sending(query), descriptions=export_descriptions(query),
                                          project=held.get("name") or "", researcher=researcher_name(),
                                          who=portrait_printed(path, query))
    except srv.OutsideRoot as exc:
        return 403, themes_print.refusal(str(exc))
    except WorkbookError as exc:
        return 409, themes_print.refusal(str(exc))
    except FileNotFoundError as exc:
        return 404, themes_print.refusal(f"File not found: {exc}")


def examples(n: int, gravity_only: bool) -> list[dict]:
    """Statements for the rail and for the prompt's {examples}, from the one source both read.

    The corpus and the reference workbook named in config.json, and the demo's own statements
    when neither is on the machine.
    """
    cfg = srv.config()
    return corpus.sample(srv.configured(cfg.get("corpus")), srv.configured(cfg.get("gravity_reference")), n,
                         gravity_only, cfg.get("corpus_exclude") or (), srv.DEMO_EXAMPLES)


def api_examples(body: dict) -> dict:
    return {"examples": examples(3, bool(body.get("gravity_only")))}


def api_nudges(body: dict) -> dict:
    """The nudges on each statement in `text`, one a line, the length nudge at the statement length of
    the project the workbook `path` belongs to, 15 without one (see `statement_words_of`)."""
    cfg = srv.config()
    enabled = [k for k, v in cfg.get("nudges", {}).items() if v]
    try:
        high = statement_words_for(srv.abs_path(body["path"])) if body.get("path") else nudges_mod.HIGH
    except (srv.OutsideRoot, WorkbookError, OSError, ValueError):
        high = nudges_mod.HIGH
    return {"lines": nudges_mod.check_field(body.get("text", ""), enabled, high), "statement_words": high}


def rail_of(path: Path | None = None) -> dict:
    """One guidance file's rail as the statements screen's panel draws it: its lines, each line's examples, the
    framing under the list and the craft prompts for the field, `guidance.md`'s unless another file is named."""
    return {"lines": guidance_lines(path), "examples": guidance_examples(path), "framing": guidance_framing(path),
            "prompts": placeholder_prompts(path)}


def api_guidance(_: dict) -> dict:
    """The statements screen's rail, IPA's from `guidance.md`, and `ta`, a thematic analysis project's Coding rail
    from `ta_guidance.md` in the same shape (tarail), the page drawing the one of the project in front."""
    cfg = srv.config()
    return {**rail_of(),
            "ta": rail_of(i18n.long_text(TA_GUIDANCE)),
            "prompt_default": prompts.DEFAULT_PROMPT,
            "counts": corpus.counts(srv.configured(cfg.get("corpus")), srv.configured(cfg.get("gravity_reference")),
                                    cfg.get("corpus_exclude") or ())}


def guidance_sections(path: Path | None = None, keep_case: bool = False) -> dict[str, list[str]]:
    """The bulleted lines of a guidance file, in order, under the heading each one sits below:
    `guidance.md` unless another file is named, each heading lowercased unless `keep_case`.

    Two sections of `guidance.md` use it: the lines in the rail, which also ride in the prompt, and
    the craft prompts one of which becomes the placeholder in the statement field. The Themes
    screen's Guidance tab reads `themes_guidance.md` through it too, with its headings as written.

    Either bullet marker counts. The placeholders are written with `*` because a server started
    before that section existed swept the whole file for `- ` and would have shown all of them in
    the rail until it was restarted. An indented bullet belongs to the line above it, a rail line's
    examples (see `guidance_examples`), and is never a line of its own. A missing file has no sections.
    """
    path = path or i18n.long_text(boot.resource("guidance.md"))
    text = path.read_text(encoding="utf-8") if path.exists() else ""
    sections: dict[str, list[str]] = {}
    heading = ""
    for line in text.splitlines():
        bare = line.strip()
        if bare.startswith("#"):
            heading = bare.lstrip("#").strip()
            heading = heading if keep_case else heading.lower()
            sections.setdefault(heading, [])
        elif bare[:2] in ("- ", "* ") and not line[:1].isspace():
            sections.setdefault(heading, []).append(bare[2:].strip())
    return sections


EXAMPLE_SIDES = {"less this:": "less", "more this:": "more"}


def guidance_examples(path: Path | None = None) -> list[dict | None]:
    """Each rail line's two examples, in the order of `guidance_lines`, the panel's Less this and More
    this columns (Adam, 21 October). They are the indented bullets under a line in `guidance.md`, one
    starting `Less this:` and one `More this:`, `{"less", "more"}`, and a line without both has None,
    so the panel shows no arrow on it. Only the rail's own section is read, never the placeholders."""
    path = path or i18n.long_text(boot.resource("guidance.md"))
    text = path.read_text(encoding="utf-8") if path.exists() else ""
    rail = next((h for h, lines in guidance_sections(path).items() if "placeholder" not in h and lines), None)
    found: list[dict] = []
    heading = None
    for line in text.splitlines():
        bare = line.strip()
        if bare.startswith("#"):
            heading = bare.lstrip("#").strip().lower()
        elif heading != rail or bare[:2] not in ("- ", "* "):
            continue
        elif not line[:1].isspace():
            found.append({})
        elif found:
            body = bare[2:].strip()
            for opener, side in EXAMPLE_SIDES.items():
                if body.lower().startswith(opener):
                    found[-1][side] = body[len(opener):].strip()
    return [pair if pair.get("less") and pair.get("more") else None for pair in found]


def themes_guidance(path: Path | None = None) -> list[dict]:
    """The Themes screen's Guidance tab: each heading of `themes_guidance.md` with the lines under
    it, `{"heading", "lines"}`, in the file's order. It is read afresh on every open of the screen,
    so an edit shows on the next reload with no restart. The intro under the title carries no lines
    and so never shows, and a missing file is an empty list. A thematic analysis project's Themes board
    reads `ta_themes_guidance.md` through it (tarail)."""
    sections = guidance_sections(path or i18n.long_text(THEMES_GUIDANCE), keep_case=True)
    return [{"heading": heading, "lines": lines} for heading, lines in sections.items() if heading and lines]


def guidance_lines(path: Path | None = None) -> list[str]:
    """The rail's own lines: the bullets under the first heading, or every bullet in an older file."""
    sections = guidance_sections(path)
    for heading, lines in sections.items():
        if "placeholder" not in heading and lines:
            return lines
    return [line for lines in sections.values() for line in lines]


def guidance_framing(path: Path | None = None) -> str:
    """The plain paragraph under the rail's own heading in `guidance.md`, which the panel shows under
    the list (Adam's framing of 20 October: which rules test meaning, which are form). The rail's
    heading is the first one with lines that is not the placeholders'. Its prose lines join into one
    paragraph, and a file with none, or an older file with no such heading, gives an empty string."""
    path = path or i18n.long_text(boot.resource("guidance.md"))
    text = path.read_text(encoding="utf-8") if path.exists() else ""
    rail = next((h for h, lines in guidance_sections(path).items() if "placeholder" not in h and lines), None)
    if not rail:
        return ""
    heading, prose = None, []
    for line in text.splitlines():
        bare = line.strip()
        if bare.startswith("#"):
            heading = bare.lstrip("#").strip().lower()
        elif heading == rail and bare and bare[:2] not in ("- ", "* "):
            prose.append(bare)
    return " ".join(prose)


def placeholder_prompts(path: Path | None = None) -> list[str]:
    """The craft prompts the statement field shows one of, a fresh one on every turn."""
    for heading, lines in guidance_sections(path).items():
        if "placeholder" in heading:
            return lines
    return []


def run_suggestion(turn: str, prior: str, timecode: str, name: str, route: dict,
                   quotes: list[str] | None = None) -> dict:
    """Both passes through the route's provider, with the model named and the seconds counted.
    The quotes he took from the turn ride in both passes when there are any, and the answer
    counts them in `quotes`, so the page says so only when they went."""
    refused = ai_mod.route_ready(route)
    if refused:
        return refused
    register = [e["text"] for e in examples(6, True)]
    started = time.monotonic()
    result = prompts.suggest(turn, prior, timecode, name, guidance_lines(), register, route["key"],
                            template=route["template"], model=route["model"],
                            provider=route["provider"], local_url=route["local_url"],
                            research_question=route.get("research_question", ""), quotes=quotes,
                            address=route.get("address"), deployment=route.get("deployment"))
    if "error" not in result:
        local = ai_mod.is_local(route["provider"])
        result.update(provider=route["provider"],
                      model=route["model"] if local or ai_mod.is_openai(route["provider"])
                      else ai_mod.plain_model(route["model"]),
                      model_name=ai_mod.route_model(route),
                      seconds=round(time.monotonic() - started, 1))
        if quotes:
            result["quotes"] = len(quotes)
    return result


def api_suggest(body: dict) -> dict:
    """Concept tags and up to three candidate statements for one turn. Nothing is written anywhere.

    The key is read here, from `.env` or the keychain, only when Adam asks for a suggestion and
    only for Anthropic, and it goes no further than the request. An error comes back as one line.
    `quotes`, the turn's quotes as the field holds them, is read when it is a list of strings
    and ignored otherwise, so a page from before it is answered as it always was. Refused, with
    nothing asked, while AI features is off, as the PETs and GETs screens' help is.
    """
    cfg = srv.config()
    if not srv.ai_on(cfg, "statements"):
        return {"error": themes_ai.OFF}
    return run_suggestion(body.get("turn", ""), body.get("prior", ""), body.get("time", ""),
                          body.get("name", ""), srv.ai_route(cfg, {"path": body.get("path")}),
                          prompts.clean_quotes(body.get("quotes")))


def api_suggest_sample(body: dict) -> dict:
    """The test bench in settings. Asked with no turn, one turn of the demo case with the
    interviewer's turn before it, read from the demo transcript and never from a case root. Asked
    with `turn`, `prior`, `time` and `name`, the fields the button under the statement field sends,
    the same two-pass suggestion on them, with the provider, model, prompt and question the panel
    carries. A page from before that sends the one box as `text`. Nothing it says is written.
    """
    if "turn" in body:
        return run_suggestion(body.get("turn", ""), body.get("prior", ""), body.get("time", ""),
                              body.get("name", ""), srv.ai_route(srv.config(), body))
    if "text" not in body:
        return prompts.sample_turn(srv.SAMPLE_CSV)
    parts = prompts.split_sample(body.get("text", ""))
    return run_suggestion(parts["turn"], parts["prior"], "", parts["name"], srv.ai_route(srv.config(), body))


# ------------------------------------------- Add Idiograph to Claude Desktop

def holds_roots() -> list[Path]:
    """The projects whose waiting actions the app shows: its own list, a run's one project, and the demo."""
    roots = list(srv.project_roots())
    for extra in (srv.ROOT_OVERRIDE, srv.DEMO_DIR, srv.demo_ta_dir()):
        if extra and Path(extra).is_dir() and not any(srv.same_folder(Path(extra), r) for r in roots):
            roots.append(Path(extra))
    return roots


def api_holds(body: dict) -> dict:
    """The page's route for held actions (see `held_actions`), the asking page named while it runs, `page`, so an
    approved Remove with its folder to the Trash does not take the page approving it for another window
    (removetrash, 10 November 2026)."""
    token = ASKING_PAGE.set(str((body or {}).get("page") or "") if isinstance(body, dict) else "")
    try:
        return held_actions(body)
    finally:
        ASKING_PAGE.reset(token)


def held_actions(body: dict) -> dict:
    """An agent's action waiting for his yes in the app (holdsbuild, 27 October 2026, see holds.py), the page's own
    route, which no agent's op answers: `list` every action waiting in the app's projects, oldest first, `check`
    one as its card opens, its dry run again, `approve` it, run as the agent asked, and `decline` it, nothing
    written but History's line. Each names the project by its `root`, one of the app's, and the action by `id`.
    With `holds`, a list of `{root, id}`, in place of the one (holdbatchA, 1 November 2026, the card for several),
    `check` answers each as its card's row opens, and `approve` and `decline` answer each in the order given with
    its outcome (`holds.answer_all`), which the card sends one hold at a time to count them (holdsprog, 11 November
    2026). `counts` is Home's, how many wait in each project."""
    import cli
    import holds as holds_mod
    body = body if isinstance(body, dict) else {}
    op = body.get("op") or "list"
    roots = holds_roots()
    if op == "list":
        return {"holds": holds_mod.waiting(roots)}
    if op == "counts":
        # Home's cards (holdsprog, 11 November 2026): how many wait in each project, in one call, named as Home names
        # a project (`project_id`), from each project's holds file alone (`holds.counts`)
        return {"counts": [{"id": project_id(root), "root": str(root), "n": n} for root, n in holds_mod.counts(roots)]}
    if op not in ("check", "approve", "decline"):
        raise WorkbookError(i18n.t("server.op_list_check_approve_decline"))

    def root_of(given) -> Path:
        root = next((r for r in roots if given and srv.same_folder(Path(str(given)), r)), None)
        if root is None:
            raise WorkbookError(i18n.t("server.project_one_idiograph_s"))
        return root

    if "holds" in body:
        listed = body.get("holds")
        if not isinstance(listed, list) or not listed or not all(isinstance(x, dict) and x.get("id") for x in listed):
            raise WorkbookError(i18n.t("server.holds_list_ids"))
        items = [(root_of(x.get("root")), str(x["id"])) for x in listed]
        if op != "check":
            return holds_mod.answer_all(items, op)
        out = []
        for root, hid in items:
            try:
                out.append(dict(holds_mod.check(root, hid), root=str(root)))
            except cli.Refused:
                continue
        return {"checks": out}
    root = root_of(body.get("root"))
    try:
        return {"check": holds_mod.check, "approve": holds_mod.approve, "decline": holds_mod.decline}[op](
            root, str(body.get("id") or ""))
    except cli.Refused as exc:
        raise WorkbookError(" ".join(exc.lines)) from None


def api_team_review(body: dict) -> dict:
    """Working together's comments and review (wtreview, 8 November 2026): the page's route to review.py, whose ops
    the command line's `team` commands run too."""
    import review
    return review.api(body)


def api_mcp(body: dict) -> dict:
    """Add Idiograph to Claude Desktop, in Project settings. `show` answers the entry that runs
    `mcp_server.py` on the project in front of him, as Claude Desktop's settings file will hold it,
    the same entry for any other client, the one line for Claude Code and where Claude Desktop's
    file is. `add` writes the entry into that file (see `mcp_server.add_to_desktop`). The route takes
    a POST from the server's own page alone (see `Handler`)."""
    import mcp_server
    root = asked_root(body, write=True)
    if root is None or not Path(root).is_dir():
        raise WorkbookError(i18n.t("server.project_folder_chosen_yet_project"))
    # the thematic analysis demo as `--demo ta`, the IPA demo as `--demo` (demos)
    demo = ("ta" if srv.same_folder(root, srv.demo_ta_dir()) else True) if srv.is_demo_root(root) else False
    # a server reading another settings file hands the same file on, as a smoke server does
    own = srv.CONFIG_PATH if Path(srv.CONFIG_PATH).resolve() != Path(srv.PATHS["config"]).resolve() else None
    entry = mcp_server.desktop_entry(Path(root).resolve(), demo=demo, config=own)
    shown = mcp_server.setup(entry)
    if body.get("op") != "add":
        return shown
    with srv._lock:
        try:
            done = mcp_server.add_to_desktop(entry)
        except mcp_server.DesktopRefused as exc:
            raise WorkbookError(str(exc))
    return dict(shown, **done)


# ------------------------------------------------- what the family's server asks of Idiograph

# Idiograph's own settings and their defaults (the family codebase's fourth build, 22 October 2026, from
# the server's DEFAULTS), each block put before the family's setting it names (`srv.place_defaults`, as this
# module registers), so a settings file holds every key in the order it always has, and only Idiograph's
# (`srv.defaults`, the sixth build, 23 October 2026)
SETTINGS_DEFAULTS = (
    ("status_bar", {
        "interviewer": "Adam",
        # Work in rounds, under Distil, Experiential statements in Settings: a pace of transcript time
        # with a daily target and a streak, his habit and not a step of IPA, so off on a new install, and
        # a config without the key reads off (15 October). The rounds are cut and recorded all the same,
        # so the daily tally stays true for the day they are turned on
        "work_in_rounds": False,
        # The statements screen in the book's three columns (17 October, Adam's decision on a tester's "J-way",
        # Smith, Flowers and Larkin 2022, Box 5.4): experiential statements, the transcript and exploratory
        # notes side by side, in the book's order on a new install and in any of the six by his hand, from a
        # column's grip, Columns over the columns or Settings. A config from before, which has the notes'
        # place, `notes_place`, reads the order nearest the screen it drew (`statements_columns`), and the
        # old key leaves the file on its next save. Then the current passage drawn larger than the rest or
        # at their size, in the View menu and under Distil, Experiential statements in Settings (16 October)
        "statements_columns": ["statements", "transcript", "notes"],
        # Beside the order, the columns shown and how the statements and the notes stand (18 October,
        # Adam's drawing of four layouts and one menu): `columns_hidden` the columns he has hidden, the
        # statements, the notes or both, never the transcript, and hidden is never deleted, `columns_stacked`
        # the notes under the statements in one column beside the transcript, and `stack_split` the place of
        # the divider between them, the statements' share of that column. A config from before has none of
        # them and reads as the three columns side by side. Since 21 October a heading dropped on the other
        # column stacks the two either way up, `stack_top` the one above, the statements unless it says the
        # notes, and `stack_split` the upper half's share
        "columns_hidden": [],
        "columns_stacked": False,
        "stack_top": "statements",
        "stack_split": 0.5,
        # The columns' widths as their edges were dragged (20 October, Adam's way C from a tester's letterbox on a
        # wide screen): for each width of screen, its pixels as a key, the first column's distance from the
        # window's left, the last column's from its right, and the statements', the notes' and the stacked
        # column's widths, the transcript taking the rest. A screen with none opens as the columns always have
        "column_widths": {},
        "larger_passage": True,
        # The minimap at the bottom right of the statements screen's transcript, the whole sheet at a
        # glance with the part in view as a box (16 October, after a tester lost his place in a long
        # transcript), chosen in the same View menu and Settings' View: `auto`, shown as he scrolls or
        # moves and fading after, `on` or `off` (17 October, later, where it was a tick). Auto by default,
        # and a config without the key, or with the tick's old true, reads auto, its old false off
        "minimap": "auto",
        # The PETs table's two ticks, in Export on the PETs screen and on the print view (Adam, 18 October):
        # Include not placed and Include statements set aside, which put those two parts at the end
        # of the print view and the Word document. Off on a new install, so the export holds the PETs alone,
        # and his last choice kept
        "export_not_placed": False,
        "export_binned": False,
        # the third (19 October), Include stacked statements, which puts the statements stacked under a
        # top beneath it in the print view, the Word document and the PET draft. Off on a new install, so the
        # top stands for its stack alone
        "export_stacked": False,
        # For sending, beside them and on the GETs print card (Adam, 19 October): the PDF and the Word
        # document named by the case alone, "P1 - Ada.pdf", and no board's name or Current board on the
        # page, the foot kept. Off on a new install, his last choice kept
        "export_for_sending": False,
        # Descriptions, the first of them on the print view and in Export (Adam, 21 October): each PET's,
        # sub-PET's and GET's description under its title in the print view and the Word table. On on a new
        # install, his last choice kept
        "export_descriptions": True,
        # Pen portrait under Export and on the print view (pbioexport, 11 November 2026): the participant's label
        # and pen portrait under the head of the table of PETs, print view, PDF and Word. Off on a new install, his
        # last choice kept
        "export_portrait": False,
        # Participants table on the GETs print card (pbioexport): a first page listing each participant with their
        # label and pen portrait. Off on a new install, his last choice kept
        "export_participants": False,
    }),
    # The PETs and GETs boards' status bar along the foot (Adam, 19 October, A of the drawings), on by default and
    # turned off from View and from Settings, View, is General's, `status_bar`, the family's since the sixth build
    # (23 October 2026), and Idiograph's settings after it stand after it, as a file has always held them
    ("ai_suggest", {
        # `status_counts` the counts the status bar shows at its left, picked by a right click on it, in the
        # bar's own order, and `palette_place` where the palette of Sticky note, Group, Undo and Redo floats on
        # the canvas, the edge it settles against, left or right, and its top as a share of the canvas's
        # height, or nothing for its place at the left
        "status_counts": ["pets", "placed", "stacked", "binned", "unplaced", "loose"],
        # Quotes on cards (Adam, 19 October, way A of the drawings): each statement card on the PETs and
        # GETs boards shows its own quote under its statement, turned on and off from its button among the
        # status bar's view tools. Off on a new install, his last choice kept
        "card_quotes": False,
        # and with them on, each quote whole rather than cut at three lines (Adam, 30 October: "full quotes on
        # each card without having to click anything"), the button's third state. Off on a new install, kept
        "card_quotes_full": False,
        # Notes on cards (Adam, 20 October, from a tester's feedback): each statement card on the GETs board shows its
        # passage's exploratory notes, from its button beside Quotes. Off on a new install, his last choice kept
        "card_notes": False,
        # Compact on a thematic analysis project's Themes board (themesbuild, 2 November 2026): each code's card its
        # name alone. Off on a new install, his last choice kept
        "card_compact": False,
        # Quotes on the statements screen's status bar (Adam, 21 October): each statement's quote shown whole, or
        # with it off folded to one line, a quote opening alone from its label. On on a new install, his last
        # choice kept
        "es_quotes": True,
        # the Trajectories screen's status bar (trajbuild2, 10 November 2026): its key quotes off, short (three
        # lines) or full, Short on a new install, and Notes, each participant's note, off on a new install
        "traj_quotes": "short",
        "traj_notes": False,
        # Close pairs (Adam, 20 October, way B and way 1 of the drawings): a link line on the PETs board between
        # two statements in one group from one sheet within `close_gap` seconds of each other, turned on and off
        # from its button among the status bar's view tools, its gap from that button's menu. Off on a new
        # install, a minute, his last choice of both kept
        "close_pairs": False,
        "close_gap": 60,
        "palette_place": None,
        # The boards' toolbar (Adam, 21 October, the toolbar drawings): docked under the research question by
        # default, `palette_docked` false while he has pulled it off by its grip to float at `palette_place`,
        # and `arrange_way` the way Auto-arrange's button repeats, the last he chose from its menu
        "palette_docked": True,
        "arrange_way": "grid",
        # The statements screen's own toolbar (barsD, Adam, 6 November 2026), docked under the band by default and
        # floating at `es_palette_place` while he has pulled it off by its grip, as the boards' is
        "es_palette_docked": True,
        "es_palette_place": None,
        "round_minutes": 10,
        "daily_target": 2,
        # The examples rail's two pools. None by default, so a shared copy draws on the demo's own
        # statements: this install names its corpus, the sources to leave out of it and its reference
        # workbook in config.json. Case folders carry a second name that never belongs in the repo, so
        # a configured path is a glob on the pseudonym and is resolved on disk at read time.
        "corpus": "",
        "corpus_exclude": [],
        "gravity_reference": "",
        "nudges": {c: True for c in ("length", "lead", "quote", "semicolon", "emdash", "arrow", "readsas")},
    }),
    ("ai_provider", {
        # `ai_prompt` is the statements' whole system prompt, his to edit
        "ai_prompt": prompts.DEFAULT_PROMPT,
    }),
    ("celebrations", {
        # The PETs screen's own provider and model, chosen under PETs in settings. Empty is the
        # Experiential statements one, which is what a file from before the two keys gets.
        "pets_provider": "",
        "pets_model": "",
        # "Dangerously skip permissions" under Using your own AI agents (Adam, 26 and 27 October 2026): off on a new
        # install, so an agent's action that deletes a board, puts an old revision over one or replaces words
        # across every participant waits for his yes in the app (see holds.py), and on, it runs at once
        "skip_permissions": False,
    }),
)


# Idiograph's own defaults by name, which its settings read over
OWN_DEFAULTS = {key: value for _before, block in SETTINGS_DEFAULTS for key, value in block.items()}


def read_settings(cfg: dict, saved: dict) -> None:
    """Idiograph's own settings as the family's `merge_config` reads them from the file (the family codebase's
    fourth build, 22 October 2026, from it), each in place: the nudges over their defaults, the statements screen's columns, and the boards' quotes, notes, close pairs, toolbar and arrange
    way, each read as its default where the file holds something else. The status bar is General's, the
    family's (the sixth build, 23 October 2026)."""
    cfg["nudges"] = {**OWN_DEFAULTS["nudges"], **saved.get("nudges", {})}
    # the three columns' order, an old notes' place read as the order nearest it, which a save then writes
    # in its place, and anything else the book's
    cfg["statements_columns"] = statements_columns(saved.get("statements_columns"), saved.get("notes_place", ""))
    cfg.pop("notes_place", None)
    # the columns shown, how the statements and the notes stand and the divider between them, each read
    # as the three side by side where the file has none or holds something else
    cfg["columns_hidden"] = columns_hidden(saved.get("columns_hidden")) or []
    cfg["columns_stacked"] = saved.get("columns_stacked") is True
    cfg["stack_top"] = stack_top(saved.get("stack_top")) or "statements"
    split = stack_split(saved.get("stack_split"))
    cfg["stack_split"] = STACK_SPLIT if split is None else split
    cfg["column_widths"] = column_widths(saved.get("column_widths"))
    cfg["minimap"] = minimap_mode(cfg.get("minimap"))
    cfg["card_quotes"] = saved.get("card_quotes") is True
    cfg["card_quotes_full"] = saved.get("card_quotes_full") is True
    cfg["card_notes"] = saved.get("card_notes") is True
    cfg["card_compact"] = saved.get("card_compact") is True
    cfg["es_quotes"] = saved.get("es_quotes") is not False
    cfg["traj_quotes"] = saved.get("traj_quotes") if saved.get("traj_quotes") in ("off", "short", "full") else "short"
    cfg["traj_notes"] = saved.get("traj_notes") is True
    cfg["close_pairs"] = saved.get("close_pairs") is True
    cfg["close_gap"] = themes_mod.close_gap(saved.get("close_gap"))
    counts = status_counts(saved.get("status_counts"))
    cfg["status_counts"] = list(OWN_DEFAULTS["status_counts"]) if counts is None else counts
    cfg["palette_place"] = palette_place(saved.get("palette_place"))
    cfg["palette_docked"] = saved.get("palette_docked") is not False
    cfg["es_palette_place"] = palette_place(saved.get("es_palette_place"))
    cfg["es_palette_docked"] = saved.get("es_palette_docked") is not False
    cfg["arrange_way"] = arrange_way(saved.get("arrange_way"))
    cfg["skip_permissions"] = saved.get("skip_permissions") is True
    cfg["your_name"] = " ".join(str(saved.get("your_name") or "").split())


def save_settings(cfg: dict, body: dict) -> None:
    """Idiograph's own settings as a save sends them, into `cfg` before the family's `api_settings` writes it
    (the family codebase's fourth build, 22 October 2026, from it): the interviewer, the rounds and the
    statements' prompt, the PETs screen's own model, the nudges, the ticks of the statements screen, the
    exports and the boards, the close pairs' gap, the status bar's counts, the toolbar, the minimap and the
    columns, each only as the page sends it."""
    # Your name, the name documents carry, the print views' foot and Word's author (31 October 2026), one line
    if "your_name" in body:
        cfg["your_name"] = " ".join(str(body["your_name"] or "").split())[:120]
    for name in ("interviewer", "round_minutes", "daily_target", "ai_prompt"):
        if name in body:
            cfg[name] = body[name]
    # the PETs screen's own model goes as a pair, and anything short of a known provider with a
    # model is the Experiential statements one, both keys empty. A page from before sends neither
    if "pets_provider" in body or "pets_model" in body:
        own = str(body.get("pets_model") or "").strip()
        provider = body.get("pets_provider") if body.get("pets_provider") in ai_mod.PROVIDERS and own else ""
        cfg["pets_provider"], cfg["pets_model"] = provider, own if provider else ""
    if "nudges" in body:
        cfg["nudges"] = {**cfg.get("nudges", {}), **body["nudges"]}
    # Work in rounds and the larger current passage, saved as they stand, the View menu's one sent alone,
    # the PETs table's export's ticks, each sent alone from Export or the print view, and the boards' bars
    for name in ("work_in_rounds", "larger_passage", "export_not_placed", "export_binned", "export_stacked",
                 "export_for_sending", "export_descriptions", "export_portrait", "export_participants", "card_quotes",
                 "card_quotes_full", "card_notes", "card_compact", "es_quotes", "close_pairs", "traj_notes"):
        if name in body:
            cfg[name] = bool(body[name])
    if body.get("traj_quotes") in ("off", "short", "full"):
        cfg["traj_quotes"] = body["traj_quotes"]
    # the close pairs' gap, one of the menu's, anything else read as the minute
    if "close_gap" in body:
        cfg["close_gap"] = themes_mod.close_gap(body["close_gap"])
    # the status bar's counts and the palette's place, each sent alone as it changes, anything else left
    # as the file has it, and a place of null putting the palette back at the left
    counts = status_counts(body.get("status_counts"))
    if counts is not None:
        cfg["status_counts"] = counts
    if "palette_place" in body:
        cfg["palette_place"] = palette_place(body["palette_place"])
    # docked under the research question or floating, and Auto-arrange's way, each sent alone as it changes
    if "palette_docked" in body:
        cfg["palette_docked"] = body["palette_docked"] is not False
    # and the statements screen's toolbar, its place and whether it is docked, each as the boards' (barsD)
    if "es_palette_place" in body:
        cfg["es_palette_place"] = palette_place(body["es_palette_place"])
    if "es_palette_docked" in body:
        cfg["es_palette_docked"] = body["es_palette_docked"] is not False
    if "arrange_way" in body:
        cfg["arrange_way"] = arrange_way(body["arrange_way"])
    # Dangerously skip permissions, on only when the page sends it ticked
    if "skip_permissions" in body:
        cfg["skip_permissions"] = body["skip_permissions"] is True
    # the minimap's Auto, On or Off, and a page from before the choice sends its tick, true read as auto
    if "minimap" in body:
        cfg["minimap"] = minimap_mode(body["minimap"])
    # the three columns' order, the three names once each, anything else left as the file has it
    order = statements_columns(body.get("statements_columns"))
    if order:
        cfg["statements_columns"] = order
    # the columns hidden, the statements and notes side by side or stacked, and the divider's place, each
    # only as the page sends it and anything else left as the file has it (18 October)
    hidden = columns_hidden(body.get("columns_hidden"))
    if hidden is not None:
        cfg["columns_hidden"] = hidden
    if isinstance(body.get("columns_stacked"), bool):
        cfg["columns_stacked"] = body["columns_stacked"]
    if stack_top(body.get("stack_top")):
        cfg["stack_top"] = body["stack_top"]
    split = stack_split(body.get("stack_split"))
    if split is not None:
        cfg["stack_split"] = split
    # one screen's column widths at a time, `{"screen": "2560", "widths": {...}}`, and widths of null
    # putting that screen back as it opens, so two windows on two screens never write over each other's
    asked = body.get("column_widths")
    if isinstance(asked, dict) and column_screen(asked.get("screen")):
        screen = column_screen(asked.get("screen"))
        held = column_widths(cfg.get("column_widths"))
        held.pop(screen, None)
        kept = column_width_set(asked.get("widths"))
        if kept:
            held[screen] = kept
        cfg["column_widths"] = column_widths(held)


def research_question(body: dict) -> str:
    """The research question an AI route fills `{research_question}` with (the family's `ai_route`): the
    project's the case `path` names belongs to, the demo's own for the demo, and with no path the only
    project's."""
    where = srv.abs_path(body["path"]) if body.get("path") else None
    return read_project(project_root(where))["research_question"]


def search_rows() -> list[dict]:
    """Idiograph's projects as Everything searches them (the family's `api_search`), each as This project
    searches it, every project's in the order they were added and the demo's last."""
    roots = [r for r in srv.project_roots() if r.exists()] + ([srv.DEMO_DIR] if demo_workbooks() else [])
    roots += [srv.demo_ta_dir()] if any(book.is_file() for book in demo_workbooks(srv.demo_ta_dir())) else []
    return [search_distil(r) for r in roots]


def search_scope(body: dict, kinds: list) -> dict:
    """This case, the workbook `path` and its themes file, and This project, every case of the project `path`
    belongs to or `root` names by its id, its GETs, its cases' names and its research question, Idiograph's
    two scopes of the family's Search (`api_search`), with `cases` and `sheets` the filters ticked."""
    listed = lambda key: [str(v) for v in body.get(key) or [] if isinstance(v, str)] if isinstance(body.get(key), list) else []
    scope, q = str(body.get("scope") or ""), body.get("q") or ""
    path = case_path(body["path"]) if body.get("path") else None
    if scope == "case" and path is None:
        raise WorkbookError(app_search.NO_CASE)
    root = project_root(path) if path is not None else srv.project_named(body["root"]) if body.get("root") else None
    if root is None:
        raise WorkbookError(app_search.NO_PROJECT)
    project = read_project(root)
    if scope == "case":
        cases = [{"case": case_label(path), "workbook": path, "path": srv.rel_path(path)}]
    else:
        cases = search_cases(root)
    whole, match_case = app_search.options(body)
    found = idiograph_find.search(q, scope, cases, project,
                                  gets_mod.gets_path(root) if scope == "project" else None, project["pet_labels"],
                                  kinds=kinds, only_cases=listed("cases"), sheets=listed("sheets"), whole=whole,
                                  match_case=match_case)
    # the kinds' names in the words of the project's method, a thematic analysis project's Codes and Extracts, for
    # the card to name them by (taword, 1 November 2026)
    with i18n.in_method(project.get("method")):
        names = idiograph_find.names_now()
    return dict(found, names=names) if names else found


def stream_audio(handler, query: dict) -> None:
    """Serve the sheet's recording, with Range support so the player can seek.

    Chromium will not let anyone drag the scrubber on a file served in one piece, which is the
    whole reason for the 206 path below.
    """
    try:
        path = srv.abs_path(query.get("path", ""))
    except Exception:
        return handler._send(400, b"Bad path", "text/plain; charset=utf-8")
    if not query.get("path") or not srv.within_root(path):
        return handler._send(403, b"That path is outside the project folder.", "text/plain; charset=utf-8")
    found = audio_mod.for_sheet(path, query.get("sheet", ""))
    if found is None or not found.exists() or not srv.within_root(found):
        return handler._send(404, b"No recording for that sheet.", "text/plain; charset=utf-8")
    try:
        size = found.stat().st_size
    except OSError:
        return handler._send(404, b"That recording could not be read.", "text/plain; charset=utf-8")
    span = audio_mod.parse_range(handler.headers.get("Range"), size)
    start, end = span if span else (0, size - 1)
    length = end - start + 1
    handler.send_response(206 if span else 200)
    handler.send_header("Content-Type", audio_mod.content_type(found))
    handler.send_header("Accept-Ranges", "bytes")
    handler.send_header("Content-Length", str(length))
    if span:
        handler.send_header("Content-Range", f"bytes {start}-{end}/{size}")
    handler.send_header("Cache-Control", "no-store")
    handler.end_headers()
    try:
        for block in audio_mod.read_span(found, start, end):
            handler.wfile.write(block)
    except (BrokenPipeError, ConnectionResetError, OSError):
        pass                                   # the player seeked away, which is not an error

def send_zip(handler, query: dict) -> None:
    """Send: the project `root` names, by its id, as one file, written to a scratch file first and
    served from it in pieces, so a project with its recordings is never held whole in memory. A
    refusal answers in JSON, as the page's other requests do. With `card` it takes Share a copy's card's
    choice as `/api/send-project` does, written as JSON, so a browser shares as the window does."""
    try:
        root = send_root(query.get("root"))
        options = {}
        if query.get("card"):
            try:
                card = json.loads(str(query["card"]))
            except ValueError:
                raise WorkbookError(i18n.t("server.nothing_sent_card_s_choice")) from None
            options = card_options(card)
    except srv.OutsideRoot as exc:
        return handler._json({"error": str(exc)}, 403)
    except WorkbookError as exc:
        return handler._json({"error": str(exc)}, 409)
    name = pack_mod.sent_name(read_project(root)["name"])
    fd, made = tempfile.mkstemp(suffix=pack_mod.SUFFIX)
    os.close(fd)
    made = Path(made)
    try:
        made.unlink()
        send_project(root, made, **options)
        size = made.stat().st_size
        handler.send_response(200)
        handler.send_header("Content-Type", "application/zip")
        handler.send_header("Content-Length", str(size))
        handler.send_header("Content-Disposition", "attachment; filename*=UTF-8''" + quote(name))
        handler.send_header("Cache-Control", "no-store")
        handler.end_headers()
        with open(made, "rb") as fh:
            for block in iter(lambda: fh.read(1 << 20), b""):
                handler.wfile.write(block)
    except (BrokenPipeError, ConnectionAbortedError, ConnectionResetError):
        handler.close_connection = True
    except WorkbookError as exc:
        return handler._json({"error": str(exc)}, 409)
    finally:
        made.unlink(missing_ok=True)


def start(one_root: bool) -> None:
    """What Idiograph does as the family's server starts (`main`): a clone of the repo carries the demo cases'
    workbooks and none of their gitignored sidecars, which come from the pristine copy here, never over a file
    that is there, and a trial run with --root, `one_root`, leaves the demo as it finds it, as it leaves the
    recent list. Then the list a run before kept of the files still as it wrote them is taken up."""
    if not one_root:
        fill_demo()
    keep_written_on()
    # Working together's looks (wtowners): what came taken in and what waits sent, in each project it is on in
    team_sync.start(lambda: [Path(r) for r in srv.project_roots()])


def demo_holding() -> str:
    """What of Idiograph's holds a quit (the family's `holding`): the demo's recording being made."""
    return "the demo's recording" if _demo_building else ""


def print_view(query: dict) -> tuple[int, bytes, str]:
    """The print view of a board, `/themes/print` (see `themes_print_page`), as the family's server sends a page
    of its own, its margins and its beat in it."""
    code, page = themes_print_page(query)
    return code, srv.own_margins(srv.beating(page)).encode("utf-8"), "text/html; charset=utf-8"


def gets_print_view(query: dict) -> tuple[int, bytes, str]:
    """The print view of the GETs, `/gets/print` (see `gets_print_page`), as `print_view` sends a board's."""
    code, page = gets_print_page(query)
    return code, srv.own_margins(srv.beating(page)).encode("utf-8"), "text/html; charset=utf-8"


# The settings Idiograph keeps of its own, which another app's /api/settings leaves as its file has them
# (the split's second build, 20 October 2026, from the server's SETTINGS_BY_APP)
OWN_SETTINGS = ("interviewer", "round_minutes", "daily_target", "ai_prompt", "pets_provider", "pets_model",
                "nudges", "work_in_rounds", "larger_passage", "export_not_placed", "export_binned",
                "export_stacked", "export_for_sending", "export_descriptions", "export_portrait",
                "export_participants", "card_quotes", "card_quotes_full",
                "es_quotes", "close_pairs", "traj_quotes", "traj_notes",
                "close_gap", "status_counts", "palette_place", "palette_docked", "arrange_way", "minimap",
                "statements_columns", "columns_hidden", "columns_stacked", "stack_top", "stack_split",
                "skip_permissions")

# Idiograph's routes, each path's handler, as the server's table held them before the split
ROUTES = {
    "/api/cases": api_cases,
    "/api/days": api_days,
    "/api/open": api_open,
    "/api/create": api_create,
    "/api/import": api_import,
    "/api/commit": api_commit,
    "/api/crux": api_crux,
    "/api/edit-turn": api_edit_turn,
    "/api/replace": api_replace,
    "/api/replace-undo": api_replace_undo,
    "/api/interviewer-note": api_interviewer_note,
    "/api/trim": api_trim,
    "/api/rows": api_rows,
    "/api/audio": api_audio,
    "/api/audio-offset": api_audio_offset,
    "/api/audio-attach": api_audio_attach,
    "/api/quote-heading": api_quote_heading,
    "/api/reset-demo": api_reset_demo,
    "/api/round-complete": api_round_complete,
    "/api/complete": api_complete,
    "/api/export": api_export,
    "/api/themes": api_themes,
    "/api/themes-save": api_themes_save,
    "/api/board-order": api_board_order,
    "/api/themes-versions": api_themes_versions,
    "/api/themes-boards": api_themes_boards,
    "/api/themes-cases": api_themes_cases,
    "/api/participants": api_participants,
    "/api/themes-export": api_themes_export,
    "/api/themes-ai": api_themes_ai,
    "/api/edit-statement": api_edit_statement,
    "/api/gets": api_gets,
    "/api/gets-head": api_gets_head,
    "/api/gets-save": api_gets_save,
    "/api/gets-ops": api_gets_ops,
    "/api/gets-boards": api_gets_boards,
    "/api/gets-cases": api_gets_cases,
    "/api/gets-settings": api_gets_settings,
    "/api/gets-trail": api_gets_trail,
    "/api/gets-ai": api_gets_ai,
    "/api/trajectories": api_trajectories,
    "/api/trajectories-ops": api_trajectories_ops,
    "/api/trajectories-turns": api_trajectories_turns,
    "/api/participant": api_participant,
    "/api/codes": api_codes,
    "/api/codes-ops": api_codes_ops,
    "/api/codes-extract": api_codes_extract,
    "/api/codes-quick": api_codes_quick,
    "/api/codes-undo": api_codes_undo,
    "/api/codes-suggest": api_codes_suggest,
    "/api/stamp": api_stamp,
    "/api/agents-guide": api_agents_guide,
    "/api/examples": api_examples,
    "/api/nudges": api_nudges,
    "/api/project": api_project,
    "/api/choose-root": api_choose_root,
    "/api/projects": api_projects,
    "/api/new-project": api_new_project,
    "/api/add-transcripts": api_add_transcripts,
    "/api/names": api_names,
    "/api/qdpx": api_qdpx,
    "/api/order": api_order,
    "/api/open-sent": api_open_sent,
    "/api/send-project": api_send_project,
    "/api/send-list": api_send_list,
    "/api/qdpx-export": api_qdpx_export,
    "/api/boards-in": api_boards_in,
    "/api/rename": api_rename,
    "/api/guidance": api_guidance,
    "/api/suggest": api_suggest,
    "/api/haiku": api_suggest,                 # the name it had before, kept working
    "/api/suggest-sample": api_suggest_sample,
    "/api/mcp": api_mcp,
    "/api/holds": api_holds,
    "/api/project-history": api_project_history,
    "/api/team": api_team,
    "/api/team-board": api_team_board,
    # Working together's comments and review (wtreview, 8 November 2026, see review.py)
    "/api/team-review": api_team_review,
}

srv.register("idiograph", routes=ROUTES,
             # these open a dialog, write another program's settings or make a project, so they answer a POST
             # from the page and never a GET, and /api/mcp only from the server's own page
             post_only=("/api/choose-root", "/api/projects", "/api/new-project", "/api/add-transcripts", "/api/names", "/api/qdpx",
                        "/api/open-sent", "/api/send-project", "/api/qdpx-export", "/api/boards-in", "/api/order", "/api/rename",
                        "/api/participant",
                        "/api/mcp", "/api/quote-heading", "/api/holds", "/api/team",
                        "/api/team-board", "/api/team-review"),
             # an agent's action waiting for his yes is answered by the app alone, never an agent (holds.py)
             own_page=("/api/mcp", "/api/holds"),
             # what governs agents, from the app's own window alone, never a program on this machine (agentlock,
             # 2 November 2026): answering a held action, adding to Claude Desktop, writing AGENTS.md, Dangerously
             # skip permissions and a project's "Allow AI agents to read this project"
             # and the list of real names (namesrule, 8 November 2026), which only the window reads or sets over HTTP
             window_only={"/api/holds": None, "/api/mcp": None, "/api/agents-guide": None, "/api/names": None,
                          "/api/settings": "skip_permissions", "/api/project": "agents"},
             get_paths={PRINT_PATH: print_view, GETS_PRINT_PATH: gets_print_view},
             streams={"/audio": stream_audio, SEND_PATH: send_zip, QDPX_PATH: qdpx_download,
                      "/traj-picture": stream_traj_picture, "/participant-picture": stream_person_picture},
             search_scope={"case": search_scope, "project": search_scope}, search_rows=search_rows,
             defaults=SETTINGS_DEFAULTS,
             own_settings=OWN_SETTINGS,
             read_settings=read_settings, save_settings=save_settings, ai_choice=pets_choice,
             question=research_question, scope=route_scope, start=start, holding=demo_holding)


def __getattr__(name: str) -> str:
    """The refusals other modules and the checks name as this module's, each read in the run's language when
    asked for (the text layer, 28 October 2026)."""
    said = {
        "AGENTS_OURS": lambda: i18n.t("server.agents_md_from_earlier_press"),
        "NEW_PROMPT": lambda: i18n.t("server.choose_folder_new_project"),
        "QDPX_NAME_SOURCES": lambda: i18n.t("server.name_sources_bring_each_participant"),
        "LPETS_ONE": lambda: i18n.t("server.lpets_come_two_more_timepoints"),
        "LGETS_NO_AI": lambda: i18n.t("server.ai_s_help_lgets_yet"),
        "ONE_RUN": lambda: i18n.t("server.run_one_project_named_root"),
        "NOT_MADE": lambda: i18n.t("server.idiograph_could_write_participants_folders"),
        "NOT_ADDED": lambda: i18n.t("server.idiograph_could_add_transcripts_nothing"),
        "NOT_A_QDPX": lambda: i18n.t("server.file_refi_qda_project_name"),
        "QDPX_GONE": lambda: i18n.t("server.project_s_file_longer_held"),
        "DEMO_NAMES": lambda: i18n.t("server.demo_s_names_fixed"),
        "NO_CASE": lambda: i18n.t("server.participant_project_now_nothing_changed"),
        "NO_PASSAGE": lambda: i18n.t("server.statement_s_passage_longer_transcript"),
        "NOT_AN_OFFSET": lambda: i18n.t("server.give_offset_seconds_plus_minus"),
        "TRAJ_ONE": lambda: i18n.t("server.trajectories_come_two_more_timepoints"),
    }
    if name in said:
        return said[name]()
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
