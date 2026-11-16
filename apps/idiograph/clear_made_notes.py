"""The notes an agent's boards carried about their own making, taken off (sidebarcopy, 16 November 2026, Adam: "archaeology
and unhelpful").

Until 16 November 2026 a board an agent made through `board new` carried a note, "Made by Claude Code in a conversation on
9 November 2026 at 22:21, for the request '...'. 3 PETs, 18 placed, 2 not placed.", and a copy it made through `board
duplicate` or `gets duplicate` one, "Duplicated from Board 1 by Claude Code in a conversation on ...", which the board's
head shows under its name. The record of agents' changes (By an agent) already keeps who, when and the request, and the
board keeps its own `made` mark, so nothing writes those notes now. This takes the ones already written off the boards:
the words of the making and its counts go, the agent's own note after them ("Its note: ...") stays as the board's note, and
a board with no `made` mark gets one from the note first, so the board menu still says an agent made it. A note that is not exactly
what an agent wrote, one he wrote or changed, even inside the agent's sentence, is left as it is and counted as `left`.

Every board file that can hold boards is read, the root's (the GETs, the LGETs, Trajectories) and each participant's in
`Working/`. A file to change is copied to the `_Archive` beside it first, `<name> (pre-clear-made-notes <date-time>)`, and
written as the app writes it (`themes.render`) through a temporary file; a failure puts every file written so far back byte
for byte and removes the copies. The dry run reads alone and answers counts by participant and the files by name, never a
word of a note."""
from __future__ import annotations

import json
import os
import re
from datetime import datetime
from pathlib import Path

import i18n
import workbook as wb_mod
from workbook import WorkbookError

import clear_format

LABEL = "pre-clear-made-notes"
# a board an agent made: the making, its request, its counts, and the agent's own note after them. The request is read
# non-greedily up to the first "'. " and the counts, and a request holding "'. " itself is left alone
MADE = re.compile(r"^Made by (?P<tool>.+?) in a conversation on (?P<when>.+?), for the request '(?P<request>.*?)'\. "
                  r"\d+ PETs?, \d+ placed, \d+ not placed\.(?: Its note: (?P<own>.*))?$", re.S)
# a copy an agent made, ending right after its request
COPY = re.compile(r"^Duplicated from .+? by .+? in a conversation on .+?, for the request '(?P<request>.*?)'\.$", re.S)
# a note that starts as one of the two but is not exactly what an agent wrote, which stays, counted as left
STARTS = re.compile(r"^(?:Made by .+? in a conversation on |Duplicated from .+? by .+? in a conversation on )", re.S)
PARTS = ("made", "copies", "left")
KINDS = ("made", "copies")


def exact(found, board: dict) -> bool:
    """Whether a note read by `MADE` is exactly what an agent wrote: where the board keeps its `made` mark, the tool,
    the request and the time it names are the mark's, so words he changed inside the agent's sentence do not match."""
    if "'. " in found["request"]:
        return False
    mark = board.get("made")
    if not isinstance(mark, dict) or not mark.get("at"):
        return True
    import cli
    import themes_ai
    return (themes_ai.one_line(mark.get("tool")) == " ".join(found["tool"].split())
            and themes_ai.one_line(mark.get("request")) == " ".join(found["request"].split())
            and cli.when_said(mark.get("at")) == found["when"])


def settle(board: dict, fallback_at: str = "") -> str | None:
    """What a board's note becomes, "made" or "copies" for the kind it was, and the board changed in place, "left" for a
    note that reads as an agent's but has been changed, left as it is, or None for a note of any other words."""
    note = str(board.get("note") or "").strip()
    found = MADE.match(note)
    if found and exact(found, board):
        own = (found["own"] or "").strip()
        if own:
            board["note"] = own
        else:
            board.pop("note", None)
        if not isinstance(board.get("made"), dict):
            at = str(board.get("created") or board.get("updated") or fallback_at or "").strip()
            board["made"] = {"by": "agent", "tool": " ".join(found["tool"].split())[:80],
                             "request": " ".join(found["request"].split())[:400],
                             "at": at or datetime.now().astimezone().isoformat(timespec="seconds")}
        return "made"
    copy = COPY.match(note)
    if copy and "'. " not in copy["request"]:
        board.pop("note", None)
        return "copies"
    return "left" if STARTS.match(note) else None


def file_plan(path: Path) -> tuple[dict | None, dict]:
    """A board file's data with its boards' making notes taken off, and the counts by kind, None for a file with none."""
    try:
        data = json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        raise WorkbookError(i18n.t("server.clear_formatting_unreadable", file=Path(path).name, exc=exc)) from None
    counts: dict = {}
    for board in (data.get("boards") or []) if isinstance(data, dict) else []:
        if isinstance(board, dict):
            kind = settle(board, str(data.get("updated") or ""))
            if kind:
                counts[kind] = counts.get(kind, 0) + 1
    return (data if any(counts.get(k) for k in KINDS) else None), counts


def write_file(path: Path, data: dict) -> None:
    """A board file written as the app writes it, through a temporary file moved over it."""
    import themes
    path = Path(path)
    tmp = path.with_name(path.name + ".tmp")
    try:
        tmp.write_text(themes.render(data) + "\n", encoding="utf-8", newline="\n")
        os.replace(tmp, path)
    finally:
        tmp.unlink(missing_ok=True)
    wb_mod.note_written(path)


def answer(root: Path, by: dict, files: list) -> dict:
    def rel(p):
        try:
            return Path(p).resolve().relative_to(Path(root).resolve()).as_posix()
        except ValueError:
            return Path(p).name
    people = [{"case": who, **{part: counts.get(part, 0) for part in PARTS}} for who, counts in by.items()]
    totals = {part: sum(p[part] for p in people) for part in PARTS}
    return {"by_participant": people, "totals": totals, "boards": sum(totals[k] for k in KINDS), "left": totals["left"],
            "files": [rel(p) for p in files]}


def plan(root: Path, books: list[dict]) -> dict:
    """What the op would take off, nothing written: counts by participant ("" for a file at the project's root) and by
    kind, `boards` in all and the files by name."""
    by: dict = {}
    files = []
    for path, owner in clear_format.board_files(Path(root), books):
        data, counts = file_plan(path)
        if data is not None:
            files.append(path)
        if counts:
            row = by.setdefault(owner or "", {})
            for kind, n in counts.items():
                row[kind] = row.get(kind, 0) + n
    return answer(root, by, files)


def clear(root: Path, books: list[dict]) -> dict:
    """The op itself, under the locks the caller holds: each file to change copied to its `_Archive` first, then written.
    Any failure puts back every file written so far, byte for byte, removes the copies and raises. Answers as `plan`, with
    `archived`, the copies kept."""
    import codes as codes_mod
    root = Path(root)
    written: list[tuple[Path, bytes]] = []
    archived: list[Path] = []
    by: dict = {}
    files = []
    try:
        for path, owner in clear_format.board_files(root, books):
            data, counts = file_plan(path)
            if data is None:
                if counts:
                    row = by.setdefault(owner or "", {})
                    for kind, n in counts.items():
                        row[kind] = row.get(kind, 0) + n
                continue
            folder = root if owner is None else wb_mod.case_folder(path)
            archived.append(codes_mod.root_archive(folder, Path(path), LABEL))
            old = path.read_bytes()
            write_file(path, data)
            written.append((path, old))
            files.append(path)
            row = by.setdefault(owner or "", {})
            for kind, n in counts.items():
                row[kind] = row.get(kind, 0) + n
    except BaseException:
        for path, old in reversed(written):
            tmp = path.with_name(path.name + ".tmp")
            try:
                tmp.write_bytes(old)
                os.replace(tmp, path)
                wb_mod.note_written(path)
            except OSError:
                pass
            finally:
                tmp.unlink(missing_ok=True)
        for kept in archived:
            try:
                kept.unlink()
            except OSError:
                pass
        raise
    out = answer(root, by, files)
    out["archived"] = [p.name for p in archived]
    return out
