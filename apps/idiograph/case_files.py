"""Every file that names a participant, and how a rename carries them through it (renamefix, 11 November 2026).

pbiodraw found on 11 November that a rename left the Trajectories board and the LGETs behind: both name a
participant by their label, `P1 - Wren`, and Rename carried the label through the GETs file alone. With the folder
ticked it also left the participant's LPETs and their PETs boards after T1 under the workbook's old name, where
nothing found them. So every file that names a participant is named here, in one place, and Rename
(`idiograph_routes.rename_plan` and `rename_case`, which the app's Rename, the command line's `participant rename`
and MCP's `participant_rename` all run) carries them through each, with its dry run and its History.

**Beside a workbook**, in its `Working/` folder, every file named after it, `<stem>.<anything>`, is its own
(`sidecars`): the progress file, the PETs boards of each timepoint, the LPETs and any file a later build keeps there.
They move with the workbook when the folder is ticked. Those that name the participant inside are carried
(`side_files`, `carry_side`): each PETs boards file's `case` and `workbook`, the LPETs file's `workbook` for each
timepoint, and the progress file's copies of a trim or an assignment, found again in the folder it moves to.

**At the project's root** each file that names a participant is in `PROJECT`, with its line in the Rename card and
the History and how it carries them: the GETs and the LGETs (every key and string that names the participant or a
card of theirs, and the workbook's new name), the Trajectories board (where they are placed, his order of each
trajectory and, with the folder ticked, their picture's file, named after them), the list of names to replace (an
entry for the participant, and the pseudonym it writes when it is theirs), and the project's own file (his order of
the participants, the note of a kept folder's new name, and the participant's own picture, label and pen portrait,
with their picture's file in `pictures/`, named after them, when the folder is ticked, pbiobuild). Every other file at a root that the code names is in
`KEPT`, with why a rename leaves it as it is. Area 156 reads every such name in the code and fails on one in
neither, so a new file cannot be missed.

A file that is there and cannot be read refuses the rename with nothing changed (`Unreadable`), and with Working
together on the folder keeps its name, since the team knows a participant by it. A copy of each file goes into
`_Archive/` first, as Rename's always have, except the list of names to replace, which the app copies nowhere, and
a write that fails puts back every file before it (`snapshot`).
"""
from __future__ import annotations

import copy
import json
import os
import re
from pathlib import Path
from typing import Callable, NamedTuple

import gets as gets_mod
import i18n
import names as names_mod
import participants as people_mod
import rounds as rounds_mod
import server as srv
import themes as themes_mod
import trajectories as traj_mod
from workbook import note_written

# a pseudonym as a whole word in a file's or a folder's name
WORD = r"(?<![A-Za-z]){}(?![A-Za-z])"


class Unreadable(Exception):
    """A file a rename would carry the participant through that is there and cannot be read."""

    def __init__(self, path: Path):
        super().__init__(Path(path).name)
        self.path = Path(path)


# ------------------------------------------------------------------ names and labels

def renamed(name: str, olds, new: str) -> str:
    """A file's or a folder's name with each pseudonym of `olds` in it as a whole word taken by `new`."""
    for old in olds:
        name = re.sub(WORD.format(re.escape(old)), new, name)
    return name


def relabel_all(value, old: str, new: str):
    """Every key and string in a file's JSON that names the case `old`, the label itself or a card's key
    under it, `old/...`, given the label `new`, everything else as it was."""
    def one(text):
        if text == old:
            return new
        return new + text[len(old):] if isinstance(text, str) and text.startswith(old + "/") else text
    if isinstance(value, dict):
        return {one(k): relabel_all(v, old, new) for k, v in value.items()}
    if isinstance(value, list):
        return [relabel_all(v, old, new) for v in value]
    return one(value) if isinstance(value, str) else value


def names_label(value, label: str) -> bool:
    """Whether a file's JSON names the case `label` anywhere, as a key, a string or a card's key."""
    if isinstance(value, dict):
        return any(names_label(k, label) or names_label(v, label) for k, v in value.items())
    if isinstance(value, list):
        return any(names_label(v, label) for v in value)
    return isinstance(value, str) and (value == label or value.startswith(label + "/"))


def order_of(data: dict | None) -> list[str]:
    held = (data or {}).get("order")
    return [str(x) for x in held if isinstance(x, str) and x.strip()] if isinstance(held, list) else []


# ------------------------------------------------------------------ reading and writing

def read_json(path: Path) -> dict | None:
    """A file as it sits, None when it is not there, `Unreadable` when it is there and is no JSON object."""
    path = Path(path)
    if not path.exists():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        raise Unreadable(path) from None
    if not isinstance(data, dict):
        raise Unreadable(path)
    return data


def write_board(path: Path, data: dict) -> None:
    """A boards file (PETs, LPETs, GETs, LGETs, Trajectories) written whole as the app writes them, beside it first."""
    tmp = path.with_name(path.name + ".tmp")
    tmp.write_text(themes_mod.render(data) + "\n", encoding="utf-8", newline="\n")
    os.replace(tmp, path)
    note_written(path)


def snapshot(path: Path) -> tuple:
    """A file as it stands, for a rename that may have to put it back: its bytes and its mode, or that it was not there."""
    path = Path(path)
    if path.is_file():
        return ("bytes", path, path.read_bytes(), path.stat().st_mode & 0o777)
    return ("file", path)


def team_on(root: Path) -> bool:
    """Whether Working together is on in the project, a team file that will not read taken as on."""
    import team as team_mod
    try:
        data = team_mod.read_team(Path(root))
    except Exception:
        return True
    return bool(data) and data.get("on") is True


# ------------------------------------------------------------------ beside each workbook

def sidecars(book: Path) -> list[Path]:
    """Every file beside a workbook in its `Working/` folder named after it, `<stem>.<anything>`, a file named after
    another file of its folder whose name runs longer left to that one. They move with the workbook."""
    book = Path(book)
    working = book.parent / "Working"
    if not working.is_dir():
        return []
    try:
        longer = [p.stem + "." for p in book.parent.iterdir()
                  if p.is_file() and p != book and p.stem.startswith(book.stem) and len(p.stem) > len(book.stem)]
        held = sorted(working.iterdir())
    except OSError:
        return []
    mine = book.stem + "."
    return [p for p in held if p.is_file() and p.name.startswith(mine) and not any(p.name.startswith(x) for x in longer)]


def boards_files(book: Path) -> list[Path]:
    """A workbook's PETs boards files, T1's then each later timepoint's, those there."""
    files = [themes_mod.themes_path(book, n) for n in [1] + themes_mod.timepoint_files(book)]
    return [p for p in files if p.is_file()]


def side_files(book: Path, with_progress: bool) -> list[tuple[str, Path]]:
    """The files beside a workbook that name the participant inside, each by its kind: `boards` for each PETs boards
    file, `lpets` for the LPETs file, and `progress` for the progress file, which names the case's folder in its
    copies of a trim or an assignment, read only when the folder moves."""
    out = [("boards", p) for p in boards_files(book)]
    lp = gets_mod.lpets_path(book)
    if lp.is_file():
        out.append(("lpets", lp))
    pr = rounds_mod.progress_path(book)
    if with_progress and pr.is_file():
        out.append(("progress", pr))
    return out


def carry_side(kind: str, book: Path, data: dict, plan: dict) -> dict:
    """A file beside a workbook with the participant carried through it, `data` left as it was."""
    out = copy.deepcopy(data)
    moves = {Path(a): Path(b) for a, b in plan["moves"]}
    moved = moves.get(Path(book))
    if kind == "boards":
        out["case"] = plan["new_label"]
        if moved is not None and out.get("workbook") == Path(book).name:
            out["workbook"] = moved.name
    elif kind == "lpets" and moved is not None:
        for rec in (out.get("cases") or {}).values() if isinstance(out.get("cases"), dict) else []:
            if isinstance(rec, dict) and rec.get("workbook") == Path(book).name:
                rec["workbook"] = moved.name
    elif kind == "progress" and plan["target"] is not None:
        # a trim's or an assignment's copy in the case's _Archive, found again in the folder it moves to
        was, now = srv.rel_path(plan["folder"]), srv.rel_path(plan["target"])
        for key in ("trims", "assignments"):
            for rec in out.get(key) or []:
                held = str(rec.get("backup") or "") if isinstance(rec, dict) else ""
                if held == was or held.startswith(was + "/") or held.startswith(was + "\\"):
                    rec["backup"] = now + held[len(was):]
    return out


def write_side(kind: str, book: Path, path: Path, data: dict) -> None:
    if kind == "progress":
        rounds_mod.save_progress(book, data)
    else:
        write_board(path, data)


# ------------------------------------------------------------------ at the project's root

class Carried(NamedTuple):
    """A file at the project's root that names a participant: its name, its path at a root, its line in the
    Rename card given the file as it is and the plan (None when the rename leaves it), the file with the participant
    carried through it, its write, and whether a copy goes into the root's `_Archive/` first."""
    file: str
    path: Callable[[Path], Path]
    line: Callable[[dict | None, dict], str | None]
    carry: Callable[[dict | None, dict], dict]
    write: Callable[[Path, Path, dict], None]
    archive: bool = True


def gets_line(said: Callable[[], str]):
    """The line for the GETs or the LGETs, `said` giving its words, when the file names the participant."""
    def line(data: dict | None, plan: dict) -> str | None:
        return said() if data is not None and any(names_label(data, x) for x in plan["was"]) else None
    return line


def gets_carry(data: dict | None, plan: dict) -> dict:
    """The GETs or the LGETs: every key and string that names the participant or a card of theirs given the new
    label, and their copy's workbook its new name where it moves."""
    out = copy.deepcopy(data or {})
    for was in plan["was"]:
        out = relabel_all(out, was, plan["new_label"])
    held = (out.get("cases") or {}).get(plan["new_label"]) if isinstance(out.get("cases"), dict) else None
    if isinstance(held, dict):
        for book, moved in plan["moves"]:
            if held.get("workbook") == Path(book).name:
                held["workbook"] = Path(moved).name
    return out


def gets_write(root: Path, path: Path, data: dict) -> None:
    """The GETs file through the GETs module's own write, which Working together's one writer guards, and the LGETs
    file through the same write at its own place."""
    token = gets_mod.FILE_AT.set(None if Path(path) == Path(root) / gets_mod.FILE else Path(path))
    try:
        gets_mod.write(root, data)
    finally:
        gets_mod.FILE_AT.reset(token)


def traj_line(data: dict | None, plan: dict) -> str | None:
    if data is None:
        return None
    placed = data.get("placed") if isinstance(data.get("placed"), dict) else {}
    ordered = [x for c in data.get("columns") or [] if isinstance(c, dict) for x in c.get("order") or []]
    return i18n.t("server.rename.trajectories") if any(x in placed or x in ordered for x in plan["was"]) else None


def traj_picture(data: dict | None, plan: dict) -> str:
    """The participant's own picture on the Trajectories board, a file's name, or "" for none or one of the set."""
    placed = (data or {}).get("placed") if isinstance((data or {}).get("placed"), dict) else {}
    for was in plan["was"]:
        name = traj_mod.picture_kept((placed.get(was) or {}).get("picture") if isinstance(placed.get(was), dict) else "")
        if name and not name.startswith("set:"):
            return name
    return ""


def traj_carry(data: dict | None, plan: dict) -> dict:
    """The Trajectories board: where the participant is placed, with everything kept on them, keyed by the new
    label, his order of each trajectory naming them by it, and their picture's file by its new name where it moves."""
    out = copy.deepcopy(data or {})
    new, was = plan["new_label"], plan["was"]
    placed = out.get("placed") if isinstance(out.get("placed"), dict) else None
    if placed is not None:
        mine = next((placed[x] for x in was if x in placed), None)
        kept = {k: v for k, v in placed.items() if k not in was}
        if mine is not None:
            kept[new] = mine
            moves = {Path(a).name: Path(b).name for a, b in plan["moves"]
                     if Path(a).parent == traj_mod.pictures_of(plan["root"])}
            if isinstance(mine, dict) and mine.get("picture") in moves:
                mine["picture"] = moves[mine["picture"]]
        out["placed"] = kept
    for col in out.get("columns") or []:
        if isinstance(col, dict) and isinstance(col.get("order"), list):
            col["order"] = list(dict.fromkeys(new if x in was else x for x in col["order"]))
    return out


def names_line(data: dict | None, plan: dict) -> str | None:
    old = plan["old"].casefold()
    for e in (data or {}).get("entries") or []:
        if isinstance(e, dict) and (str(e.get("for") or "").strip().casefold() == old or str(e.get("to") or "") == plan["old"]):
            return i18n.t("server.rename.names_list")
    return None


def names_carry(data: dict | None, plan: dict) -> dict:
    """The list of names to replace: an entry for the participant is theirs by the new pseudonym, and an entry that
    writes their pseudonym writes the new one, so a transcript of theirs added later has a real name replaced still,
    and by the name they have now."""
    out = copy.deepcopy(data or {})
    old = plan["old"].casefold()
    for e in out.get("entries") or []:
        if not isinstance(e, dict):
            continue
        if str(e.get("for") or "").strip().casefold() == old:
            e["for"] = plan["new"]
        if str(e.get("to") or "") == plan["old"]:
            e["to"] = plan["new"]
    return out


def names_write(root: Path, path: Path, data: dict) -> None:
    names_mod.save_at(root, [e for e in data.get("entries") or []])


def project_states(data: dict | None, plan: dict) -> tuple[bool, bool, bool, bool]:
    """What the rename writes in the project's own file: whether it is written, whether his order names the
    participant, whether the new name is noted there while the folder keeps its own, and whether a name noted
    there before goes."""
    in_order = any(x in order_of(data) for x in plan["was"])
    names = (data or {}).get("names") if isinstance((data or {}).get("names"), dict) else {}
    folder = srv.display_case(plan["folder"].name)
    noted = plan["kept_folder"] and plan["new"] != plan["own"]
    unnoted = not noted and folder in names
    return in_order or plan["kept_folder"] or folder in names, in_order, noted, unnoted


def set_of(data: dict | None, plan: dict) -> str | None:
    """The key the participant's own set, picture, label and pen portrait, is kept under in the project's file
    (pbiobuild, `participants.py`), or None when it keeps none for them."""
    held = (data or {}).get(people_mod.KEY)
    return next((x for x in plan["was"] if isinstance(held, dict) and x in held), None)


def project_line(data: dict | None, plan: dict) -> list[str] | None:
    """The lines for the project's own file: his order of the participants when it names them, the new name noted
    there while the folder keeps its own, or an earlier name noted there that goes, and the participant's own set
    when it keeps one."""
    on, in_order, noted, unnoted = project_states(data, plan)
    lines = []
    if not on:
        pass
    elif noted:
        lines.append(i18n.t("server.rename.project_order_noted") if in_order else i18n.t("server.rename.project_noted"))
    elif unnoted:
        lines.append(i18n.t("server.rename.project_order_unnoted") if in_order else i18n.t("server.rename.project_unnoted"))
    else:
        lines.append(i18n.t("server.rename.project_order"))
    if set_of(data, plan):
        lines.append(i18n.t("server.rename.project_set"))
    return lines or None


def set_picture_move(root: Path, data: dict | None, plan: dict, olds, new: str) -> tuple[Path, Path] | None:
    """The participant's own picture in the project's pictures folder (pbiobuild), named after them, and where it
    moves with the folder ticked, or None for none, one of the set, or one whose name does not carry the pseudonym."""
    key = set_of(data, plan)
    name = traj_mod.picture_kept(((data or {}).get(people_mod.KEY) or {}).get(key, {}).get("picture")) if key else ""
    if not name or name.startswith("set:"):
        return None
    path = people_mod.pictures_of(root) / name
    if not path.is_file() or renamed(name, olds, "\u0000") == name:
        return None
    return path, path.with_name(renamed(name, olds, new))


def project_carry(data: dict | None, plan: dict) -> dict:
    """The project's own file: his order naming the participant by the new label, the participant's own set kept
    by it with their picture's file by its new name where it moves, and the new name noted by the folder's label
    while the folder keeps its own name, a name noted there before gone once the folder takes it."""
    out = copy.deepcopy(data or {})
    if "order" in out:
        out["order"] = list(dict.fromkeys(plan["new_label"] if x in plan["was"] else x for x in order_of(out)))
    key = set_of(out, plan)
    if key is not None:
        sets = out[people_mod.KEY]
        mine = sets.pop(key)
        for x in plan["was"]:
            sets.pop(x, None)
        moves = {Path(a).name: Path(b).name for a, b in plan["moves"]
                 if Path(a).parent == people_mod.pictures_of(plan["root"])}
        if isinstance(mine, dict) and mine.get("picture") in moves:
            mine["picture"] = moves[mine["picture"]]
        sets[plan["new_label"]] = mine
    kept = dict(out.get("names") or {}) if isinstance(out.get("names"), dict) else {}
    folder = srv.display_case(plan["folder"].name)
    kept.pop(folder, None)
    if plan["target"] is None and plan["new"] != plan["own"]:
        kept[folder] = plan["new"]
    if kept:
        out["names"] = kept
    else:
        out.pop("names", None)
    return out


# Every file at a project's root that names a participant, in the order the Rename card lists them. A new one is
# added here, with its line in the catalogue (server.json, `server.rename.*`), and area 156 holds it.
PROJECT = (
    Carried(gets_mod.FILE, lambda root: Path(root) / gets_mod.FILE,
            gets_line(lambda: i18n.t("server.rename.project_gets")), gets_carry, gets_write),
    Carried(gets_mod.LGETS_FILE, lambda root: Path(root) / gets_mod.LGETS_FILE,
            gets_line(lambda: i18n.t("server.rename.project_lgets")), gets_carry, gets_write),
    Carried(traj_mod.FILE, traj_mod.path_of, traj_line, traj_carry, lambda root, path, data: traj_mod.write(root, data)),
    # the list of real names is copied nowhere, so it keeps no copy in _Archive either (`names.py`, the store)
    Carried(names_mod.FILE, names_mod.path_at, names_line, names_carry, names_write, archive=False),
    Carried(srv.PROJECT_FILE, lambda root: Path(root) / srv.PROJECT_FILE, project_line, project_carry,
            lambda root, path, data: srv.save_json(path, data)),
)

# Every other file at a project's root the code names, and why a rename leaves it as it is.
KEPT = {
    "idiograph-history.json": "what was done, kept as it was written, the rename adding its own record",
    "idiograph-codes.json": "a thematic analysis project's codes, kept by code and never by participant, a step of "
                            "its undo naming files by their place and refused whole once one of them has changed",
    "idiograph-holds.json": "an agent's request in its own words, a hold that names the participant reading as "
                            "changed on its card so that Approve runs nothing",
    "idiograph-sent.json": "the record inside a shared copy's own file, never at a project's root",
    "team.json": "Working together knows a participant by their folder, in its signed list and its folder "
                 "`.idiograph-team`, so the folder keeps its name while it is on and a label alone changes nothing there",
}


def picture_move(root: Path, data: dict | None, plan: dict, olds, new: str) -> tuple[Path, Path] | None:
    """The participant's own picture on the Trajectories board, named after them, and where it moves with the
    folder ticked, or None for none, one of the set, or one whose name does not carry the pseudonym."""
    name = traj_picture(data, plan)
    if not name:
        return None
    path = traj_mod.pictures_of(root) / name
    if not path.is_file() or renamed(name, olds, "\u0000") == name:
        return None
    return path, path.with_name(renamed(name, olds, new))
