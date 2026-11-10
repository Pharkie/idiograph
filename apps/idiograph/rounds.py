#!/usr/bin/env python3
"""Rounds, row state, pace and the daily target.

A round is a fixed stretch of transcript time, default 10 minutes, cut at turn boundaries so a
turn is never split. A round never spans two sheets, so the last round of a sheet can be short.
Each round belongs to its sheet and carries its place there, `on_sheet`, which is the number the
page shows. Its `number` runs across the whole case, sheet by sheet in workbook order, and stays
the key of everything the progress file records about rounds, so nothing written before the rounds
belonged to a sheet changes meaning.

Progress lives in a sidecar JSON beside the workbook, in the case's `Working/` folder, and never
in the workbook itself. It holds per-row state, measured minutes per completed round, and the
daily tally that drives the target and the streak, with a record of every trim, every turn
corrected in place and every assignment of words to a speaker, and, once he marks it, the time the
experiential statements phase of the case was marked complete. A sidecar from before 3 October 2026
can also hold `flags`, the turns flagged for later while the app still had flags. Nothing reads
them now, and they are kept as they stand, moved with their rows like everything else that names
a row.

A turn he moves past without Next or Skip is `passed`: derived from the sidecar and the workbook
on every read, never written, because navigation writes nothing. It counts as decided exactly the
way `reviewed-empty` does.

Everything in it that names a row moves with that row when rows are inserted or deleted, through
one re-key: `rekey_rows`.
"""
from __future__ import annotations

import copy
import datetime as dt
import json
import os
import re
import uuid
from pathlib import Path

import i18n

UNVISITED = "unvisited"
REVIEWED_EMPTY = "reviewed-empty"
HAS_CONTENT = "has-content"
# derived, never stored: an unvisited turn that sits before the furthest decided turn on its sheet
PASSED = "passed"
# the states that count a turn as decided, for a round, the counts and the summary alike
DECIDED = (HAS_CONTENT, REVIEWED_EMPTY, PASSED)

# A gap longer than this is a break, not work, so it never counts toward the measured pace.
GAP_CAP_SECONDS = 300


def build_rounds(sheets: list[dict], round_minutes: int, interviewer: str) -> list[dict]:
    """Cut every sheet into rounds, number them across the case, and place each on its sheet.

    `number` is unique across the case and is what the progress file, the daily tally and
    `round-complete` are keyed by. `on_sheet` is the round's 1-based place on its own sheet, and
    `sheet_rounds` the count of rounds on that sheet, which is what the page shows.
    """
    size = max(1, int(round_minutes)) * 60
    out: list[dict] = []
    number = 0
    for sheet in sheets:
        first = len(out)
        buckets: dict[int, list[dict]] = {}
        order: list[int] = []
        last = 0
        for row in sheet["rows"]:
            seconds = row["seconds"]
            if seconds is None:
                seconds = last
            last = seconds
            key = seconds // size
            if key not in buckets:
                buckets[key] = []
                order.append(key)
            buckets[key].append(row)
        for key in sorted(order):
            rows = buckets[key]
            number += 1
            stops = [r for r in rows if is_stop(r, interviewer)]
            out.append({
                "number": number,
                "sheet": sheet["name"],
                "on_sheet": len(out) - first + 1,
                "from": rows[0]["seconds"],
                "to": rows[-1]["seconds"],
                "rows": [(r["sheet"], r["row"]) for r in rows],
                "stops": [(r["sheet"], r["row"]) for r in stops],
            })
        for rnd in out[first:]:
            rnd["sheet_rounds"] = len(out) - first
    return out


def sheet_counts(rounds: list[dict]) -> dict[str, int]:
    """Each sheet's count of rounds, in workbook order. A sheet with no rows has none and is absent."""
    counts: dict[str, int] = {}
    for rnd in rounds:
        counts[rnd["sheet"]] = counts.get(rnd["sheet"], 0) + 1
    return counts


def is_stop(row: dict, interviewer: str) -> bool:
    """The interviewer's turns are context, never a stop, and so is another speaker's, which the
    workbook marks (20 October), counted in no round's passages though it can be coded. Two
    participant turns are two stops."""
    return (bool(row["name"]) and row["name"].strip().lower() != interviewer.strip().lower()
            and not row.get("context"))


# ------------------------------------------------------------------ sidecar

def progress_path(workbook: Path) -> Path:
    workbook = Path(workbook)
    return workbook.parent / "Working" / f"{workbook.stem}.progress.json"


def load_progress(workbook: Path) -> dict:
    path = progress_path(workbook)
    if path.exists():
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (ValueError, OSError):
            data = {}
    else:
        data = {}
    data.setdefault("version", 1)
    data.setdefault("rows", {})
    data.setdefault("rounds", {})
    data.setdefault("days", {})
    data.setdefault("last", None)
    # Sidecars written before flagging and trimming existed have neither, so both are defaulted
    # here rather than anywhere that reads them.
    data.setdefault("flags", [])
    data.setdefault("trims", [])
    # a sidecar written before a turn could be corrected in place has no record of one
    data.setdefault("edits", [])
    # nor, before words could be assigned to another speaker, of an assignment
    data.setdefault("assignments", [])
    return data


def save_progress(workbook: Path, data: dict) -> None:
    import workbook as wb_mod
    wb_mod.boards_pass_check(workbook)
    path = progress_path(workbook)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(".tmp")
    tmp.write_text(json.dumps(data, indent=1, ensure_ascii=False), encoding="utf-8", newline="\n")
    os.replace(tmp, path)


def row_key(sheet: str, row: int) -> str:
    return f"{sheet}:{row}"


def split_key(key: str) -> tuple[str, int | None]:
    where, _, number = str(key).rpartition(":")
    try:
        return where, int(number)
    except ValueError:
        return where, None


# how far a turn has got, for the one place two rows' states have to become one
STATE_RANK = {UNVISITED: 0, REVIEWED_EMPTY: 1, HAS_CONTENT: 2}


def stronger(a: str | None, b: str | None) -> str | None:
    """The state of a merged row: the furthest either of its rows had got."""
    if a is None:
        return b
    if b is None:
        return a
    return a if STATE_RANK.get(a, 0) >= STATE_RANK.get(b, 0) else b


def row_states(sheets: list[dict], progress: dict, interviewer: str) -> dict[str, str]:
    """Every participant turn's state, sheet by sheet.

    Workbook content wins: a row with a statement in it is done however the sidecar reads. Then a
    turn the sidecar has as unvisited but that sits before the furthest decided turn on its sheet is
    `passed`, because moving past a blank turn is a decision not to code it. The furthest decided
    turn is the last stop, in sheet order, that is `has-content` or `reviewed-empty`, or the
    sidecar's `last` position when that is further. Each sheet is taken on its own, so a decision on
    one never passes a turn on another. Nothing here is written back.
    """
    states: dict[str, str] = {}
    last = progress.get("last") or {}
    for sheet in sheets:
        stops: list[tuple[int, str]] = []
        for row in sheet["rows"]:
            if not is_stop(row, interviewer):
                continue
            key = row_key(row["sheet"], row["row"])
            if row["es"].strip():
                states[key] = HAS_CONTENT
            else:
                states[key] = progress["rows"].get(key, UNVISITED)
                if states[key] == HAS_CONTENT:
                    states[key] = REVIEWED_EMPTY
                elif states[key] not in (REVIEWED_EMPTY, UNVISITED):
                    # a state this version does not know is read as never visited
                    states[key] = UNVISITED
            stops.append((int(row["row"]), key))
        furthest = max((r for r, k in stops if states[k] != UNVISITED), default=0)
        if last.get("sheet") == sheet["name"] and isinstance(last.get("row"), int):
            furthest = max(furthest, last["row"])
        for r, k in stops:
            if r < furthest and states[k] == UNVISITED:
                states[k] = PASSED
    return states


def round_done(rnd: dict, states: dict[str, str]) -> bool:
    """Every stop in the round is decided: saved, skipped, or passed on the way further."""
    keys = [row_key(s, r) for s, r in rnd["stops"]]
    if not keys:
        return True
    return all(states.get(k, UNVISITED) in DECIDED for k in keys)


def round_decided(rnd: dict, states: dict[str, str]) -> int:
    """How many of the round's stops are decided."""
    return sum(1 for s, r in rnd["stops"] if states.get(row_key(s, r), UNVISITED) in DECIDED)


def today() -> str:
    return dt.date.today().isoformat()


def record_work(progress: dict, number: int, now: float, away: float = 0) -> None:
    """Add the time since the last commit to this round's measured minutes.

    `away` is the seconds the page spent hidden or unfocused since the last save, counted by the
    browser and taken off the gap before the cap is tested, so a window left open while he does
    something else does not read as work. A gap that falls to zero or below adds nothing. A gap
    longer than GAP_CAP_SECONDS counts as a break and adds nothing either, so the pace estimate
    reflects work rather than the wall clock.
    """
    key = str(number)
    entry = progress["rounds"].setdefault(key, {"seconds": 0, "completed": None})
    last = progress.get("last_commit_at")
    last_round = progress.get("last_commit_round")
    if last and last_round == key:
        gap = (now - last) - max(0, away or 0)
        if 0 < gap <= GAP_CAP_SECONDS:
            entry["seconds"] = round(entry["seconds"] + gap)
    progress["last_commit_at"] = now
    progress["last_commit_round"] = key


def shifted_row(row: int, at: int, count: int | None, inserted: bool, into: int | None = None) -> int | None:
    """Where a row lands after rows are inserted or deleted on its sheet.

    Inserted: `count` new rows open at `at`, and every row from `at` down moves down by `count`.
    Deleted: rows `at` to `at + count - 1` go (`count` None runs to the end of the sheet), and every
    row below them moves up by `count`. A deleted row lands on `into` when it was merged into that
    row, and on None when it was cut.
    """
    if inserted:
        return row + count if row >= at else row
    if row < at:
        return row
    if count is None or row < at + count:
        return into
    return row - count


def shift_key(key: str, sheet: str, at: int, count: int | None, inserted: bool,
              into: int | None = None) -> str | None:
    """A sidecar row key moved the way `shifted_row` moves its row. Keys on other sheets stay."""
    where, number = split_key(key)
    if where != sheet or number is None:
        return key
    moved = shifted_row(number, at, count, inserted, into)
    return None if moved is None else row_key(sheet, moved)


def rekey_rows(progress: dict, sheet: str, at: int, count: int | None, inserted: bool,
               into: int | None = None) -> None:
    """Move everything in the sidecar that names a row: the row states, the flags, the edit
    records and the last turn saved.

    Rows merged into another (`into`) hand it their flag, and their state where it had got
    further. A row that was cut takes its state and its flag with it, and its edit records stay
    in the file marked `cut`, because they are the record of what was corrected. Round records are
    keyed by round number, not by row, so they stay as they are.
    """
    rows: dict[str, str] = {}
    for key, value in progress.get("rows", {}).items():
        moved = shift_key(key, sheet, at, count, inserted, into)
        if moved is not None:
            rows[moved] = stronger(rows.get(moved), value)
    progress["rows"] = rows
    flags: list[str] = []
    for key in progress.get("flags", []):
        moved = shift_key(key, sheet, at, count, inserted, into)
        if moved is not None and moved not in flags:
            flags.append(moved)
    progress["flags"] = flags
    for record in progress.get("edits", []):
        if record.get("sheet") != sheet or record.get("cut") or not isinstance(record.get("row"), int):
            continue
        moved = shifted_row(record["row"], at, count, inserted, into)
        if moved is None:
            record["cut"] = True
        else:
            record["row"] = moved
    last = progress.get("last")
    if last and last.get("sheet") == sheet:
        moved = shifted_row(int(last["row"]), at, count, inserted, into)
        progress["last"] = None if moved is None else {"sheet": sheet, "row": moved}


def moved_key(key: str, sheet: str, direction: str, row: int) -> str | None:
    """Where a row key lands after a trim, or None when that row was cut."""
    if direction == "before":
        return shift_key(key, sheet, 2, int(row) - 1, inserted=False)
    return shift_key(key, sheet, int(row), None, inserted=False)


def rekey_after_trim(progress: dict, sheet: str, direction: str, row: int,
                     timecode: str = "", head: str = "", backup: str = "",
                     last: int | None = None) -> dict:
    """Move the sidecar onto the rows that survived, and record what was cut.

    A cut at the front is rows 2 to `row` deleted, a cut at the back is `row` to the end, `last`
    being the last row the workbook cut. Round records stay as they are, and a cut at the front
    shifts every later row up, which can renumber the rounds themselves on the next open.

    The record carries an id, the rows cut (`first`, `last`, `count`), the backup and `undone`,
    which is what an undo needs, and what the sidecar said about the cut rows before they went,
    which is what lets `undo_trim` put the sidecar back exactly as it was. Assignment records are
    not moved: each stays in the numbering it was made in, which is what its own undo reads, and
    the undo stack takes a later trim back before it reaches an earlier assignment.
    """
    row = int(row)
    if direction == "before":
        first, last = 2, row
    else:
        first, last = row, (int(last) if last is not None else None)

    def cut(r) -> bool:
        return isinstance(r, int) and r >= first and (last is None or r <= last)

    snap = {
        "rows": {k: v for k, v in progress.get("rows", {}).items()
                 if split_key(k)[0] == sheet and cut(split_key(k)[1])},
        "flags": list(progress.get("flags", [])),
        "edits": {str(i): e["row"] for i, e in enumerate(progress.get("edits", []))
                  if e.get("sheet") == sheet and not e.get("cut") and cut(e.get("row"))},
        "last": copy.deepcopy(progress.get("last")),
    }
    if direction == "before":
        rekey_rows(progress, sheet, 2, row - 1, inserted=False)
    else:
        rekey_rows(progress, sheet, row, None, inserted=False)
    # where the last turn saved stands after the cut, which the server sets again when the cut took it
    snap["last_after"] = copy.deepcopy(progress.get("last"))
    record = {"id": uuid.uuid4().hex[:12],
              "sheet": sheet, "direction": direction, "row": row,
              "first": first, "last": last, "count": None if last is None else last - first + 1,
              "timecode": timecode, "head": head, "backup": backup,
              "when": dt.datetime.now().isoformat(timespec="seconds"), "undone": False,
              "sidecar": snap}
    progress.setdefault("trims", []).append(record)
    return record


def find_trim(progress: dict, record_id: str) -> dict | None:
    return next((r for r in progress.get("trims", []) if record_id and r.get("id") == record_id), None)


def undo_trim(progress: dict, record: dict) -> None:
    """Put the sidecar back the way it was before the trim `record`, and mark the record undone.

    The inverse of the trim's re-key: every row from the cut down moves down by the rows cut, and
    the cut rows take back their states, their flags, in the order the flags stood in, and their
    edit records, no longer marked cut. Anything recorded on a surviving row since the trim moves
    with that row and is kept. The last turn saved goes back to where it was before the cut when
    nothing has been saved since, and otherwise moves with its row.
    """
    sheet = record["sheet"]
    first, count = int(record["first"]), int(record["count"])
    snap = record.get("sidecar") or {}

    def was_cut(key) -> bool:
        where, number = split_key(key)
        return where == sheet and number is not None and first <= number < first + count

    untouched = progress.get("last") == snap.get("last_after")
    rekey_rows(progress, sheet, first, count, inserted=True)

    rows = progress.setdefault("rows", {})
    rows.update(snap.get("rows") or {})

    wanted = list(progress.get("flags", [])) + [k for k in snap.get("flags", []) if was_cut(k)]
    order = snap.get("flags") or []
    flags: list[str] = []
    for key in [k for k in order if k in wanted] + wanted:
        if key not in flags:
            flags.append(key)
    progress["flags"] = flags

    edits = progress.get("edits", [])
    for index, r in (snap.get("edits") or {}).items():
        i = int(index)
        if i < len(edits) and edits[i].get("sheet") == sheet and edits[i].get("cut"):
            edits[i].pop("cut", None)
            edits[i]["row"] = r

    if untouched:
        progress["last"] = copy.deepcopy(snap.get("last"))

    record["undone"] = True
    record["undone_when"] = dt.datetime.now().isoformat(timespec="seconds")


def record_edit(progress: dict, sheet: str, row: int, old: str, new: str,
                old_time: str | None = None, new_time: str | None = None) -> dict:
    """Write a correction to a turn into the sidecar, the way a trim is written into it.

    The workbook holds the corrected text, and a case rebuilt from its raw source brings the old
    text back, so the record is what reconciles the two later. Both texts are kept whole, and a
    timecode that was changed with them is kept beside them, the old one and the new.
    """
    record = {"sheet": sheet, "row": int(row), "old": old, "new": new,
              "when": dt.datetime.now().isoformat(timespec="seconds")}
    if old_time is not None and new_time is not None and old_time != new_time:
        record["old_time"] = old_time
        record["new_time"] = new_time
    progress.setdefault("edits", []).append(record)
    return record


MASKED = "[match]"


def new_batch() -> str:
    """A replace's batch id, twelve hex digits, which its undo names it by."""
    return uuid.uuid4().hex[:12]


def record_replace(progress: dict, rows: list[dict], find, replace, batch: str | None = None,
                   mask: bool = False, tool: str = "", request: str = "") -> str:
    """Write a find and replace into the sidecar: one edit record for every row it changed, the
    way `record_edit` writes a correction, all under one batch id, each carrying the words found,
    the words put in their place and how many times, so an undo finds them by the id and a case
    rebuilt from its raw source can be reconciled row by row. `old` and `new` are the transcript's,
    and `cells` each annotation cell the replace changed on the row, its statements, quotes, notes or
    interviewer's note, by role with its old and its new text (24 October 2026, "Everything follows").
    A row that lost a highlight carries where it sat, `crux`, for the undo to put back. `find` and
    `replace` are a list each for a replace of several pairs, and with `mask` both read "[match]", so a
    list of names that drove it is never written here. An agent's replace carries `by`, `tool` and his
    request. `batch` is given when one replace spans several workbooks, every participant's, so one id
    undoes it all. Answers with the batch id."""
    batch = batch or new_batch()
    if mask:
        find = replace = MASKED
    for row in rows:
        record = record_edit(progress, row["sheet"], row["row"], row["old"], row["text"])
        record.update({"batch": batch, "find": find, "replace": replace, "count": int(row.get("count") or 1)})
        if row.get("cells"):
            record["cells"] = {role: {"old": c["old"], "new": c["new"]} for role, c in row["cells"].items()}
        if row.get("columns"):
            record["columns"] = dict(row["columns"])
        if row.get("crux"):
            record["crux"] = row["crux"]
        if tool:
            record.update(by="agent", tool=tool)
        if request:
            record["request"] = request
    return batch


def replace_records(progress: dict, batch: str) -> list[dict]:
    """The edit records of one find and replace, in the order it wrote them. A record whose row a
    trim has cut is left out, since there is no row to write back into."""
    return [e for e in progress.get("edits", [])
            if batch and e.get("batch") == batch and not e.get("cut")]


def mark_replace(records: list[dict], undone: bool, tool: str = "", request: str = "") -> None:
    """A replace undone or redone: each of its records says so, and when, and for an agent's undo
    or redo its tool and his request."""
    now = dt.datetime.now().isoformat(timespec="seconds")
    word = "undone" if undone else "redone"
    for record in records:
        record["undone"] = undone
        record[f"{word}_when"] = now
        if tool:
            record[f"{word}_by"] = tool
        if request:
            record[f"{word}_request"] = request


# ─────────────────────────────────────────────────────────── assignments ──

def _block_snapshot(progress: dict, sheet: str, first: int, count: int) -> dict:
    """What the sidecar says about rows `first` to `first + count - 1`, for an undo to put back."""
    keys = {row_key(sheet, r) for r in range(first, first + count)}
    return {
        "rows": {k: v for k, v in progress.get("rows", {}).items() if k in keys},
        "flags": [k for k in progress.get("flags", []) if k in keys],
        "last": progress.get("last"),
        "edits": {str(i): e["row"] for i, e in enumerate(progress.get("edits", []))
                  if e.get("sheet") == sheet and not e.get("cut") and isinstance(e.get("row"), int)
                  and first <= e["row"] < first + count},
    }


def record_assignment(progress: dict, result: dict, backup: str) -> dict:
    """Move the sidecar with the rows an assignment moved, and record the assignment.

    The record holds the sheet and the row, the kind (`assign`, or `merge` when rows became one),
    the snapped offsets, the two speakers, the text of the block before and after, the backup and
    the time, so a case rebuilt from its raw source can be reconciled with it later. It also holds
    what the sidecar said about the block either side of the move, which is what lets an undo put
    the sidecar back exactly as it was.
    """
    sheet, block = result["sheet"], result["block"]
    first, before, after = int(block["first"]), int(block["before"]), int(block["after"])
    snap_before = _block_snapshot(progress, sheet, first, before)
    flags_before = list(progress.get("flags", []))
    shift = result.get("shift")
    if shift:
        rekey_rows(progress, sheet, shift["at"], shift["count"], shift["inserted"], shift.get("into"))
    record = {
        "id": uuid.uuid4().hex[:12],
        "sheet": sheet, "row": int(result["row"]), "kind": result["kind"],
        "whole": bool(result.get("whole")), "start": result.get("start"), "end": result.get("end"),
        "from": result.get("from"), "to": result.get("to"),
        "before": result.get("before", []), "after": result.get("after", []),
        "block": {"first": first, "before": before, "after": after},
        "shift": shift, "holder": result.get("holder"), "backup": backup,
        "when": dt.datetime.now().isoformat(timespec="seconds"), "undone": False,
        "sidecar": {"before": snap_before, "after": _block_snapshot(progress, sheet, first, after),
                    "flags": flags_before},
    }
    progress.setdefault("assignments", []).append(record)
    return record


def restored_key(key: str, record: dict) -> str | None:
    """Where a row key lands when the assignment `record` is undone, for the themes file, which
    moves with the rows the way `undo_assignment` moves the sidecar.

    A row above the block stays, and a row below it moves back by the rows the assignment added or
    took away. A row of the block that was there before the assignment is the row it was, and a row
    the assignment made lands on the turn it was made on, where the undo appends whatever was
    written into that row since. Keys on other sheets stay.
    """
    sheet = record["sheet"]
    where, number = split_key(key)
    if where != sheet or number is None:
        return key
    block = record["block"]
    first, before, after = int(block["first"]), int(block["before"]), int(block["after"])
    if number < first:
        return key
    if number >= first + after:
        return row_key(sheet, number - (after - before))
    return key if number - first < before else row_key(sheet, int(record["row"]))


def find_assignment(progress: dict, record_id: str) -> dict | None:
    return next((r for r in progress.get("assignments", []) if r.get("id") == record_id), None)


def undo_assignment(progress: dict, record: dict) -> None:
    """Put the sidecar back the way it was before `record`, and mark the record undone.

    Rows outside the block move back by the rows the assignment added or took away. Rows inside
    it take back what they held before. Anything recorded against the block since, a state or a
    flag its rows did not have straight after the assignment, lands on the turn it was made on,
    the way the annotations written since land there in the workbook.
    """
    sheet = record["sheet"]
    block = record["block"]
    first, before, after = int(block["first"]), int(block["before"]), int(block["after"])
    target = int(record["row"])
    snap = record.get("sidecar") or {}
    was = snap.get("before") or {"rows": {}, "flags": [], "last": None, "edits": {}}
    now = snap.get("after") or {"rows": {}, "flags": [], "last": None, "edits": {}}
    tkey = row_key(sheet, target)

    def back(r: int) -> int | None:
        if r < first:
            return r
        if r >= first + after:
            return r - (after - before)
        return None

    rows: dict[str, str] = {}
    later: list[str] = []
    for key, value in progress.get("rows", {}).items():
        where, number = split_key(key)
        if where != sheet or number is None:
            rows[key] = value
            continue
        r = back(number)
        if r is None:
            if now["rows"].get(key) != value:
                later.append(value)
            continue
        rows[row_key(sheet, r)] = value
    rows.update(was["rows"])
    for value in later:
        rows[tkey] = stronger(rows.get(tkey), value)
    progress["rows"] = rows

    wanted: list[str] = []
    for key in progress.get("flags", []):
        where, number = split_key(key)
        if where != sheet or number is None:
            wanted.append(key)
            continue
        r = back(number)
        if r is None:
            if key not in now["flags"]:
                wanted.append(tkey)
            continue
        wanted.append(row_key(sheet, r))
    wanted += was["flags"]
    order = snap.get("flags") or []
    flags: list[str] = []
    for key in [k for k in order if k in wanted] + wanted:
        if key not in flags:
            flags.append(key)
    progress["flags"] = flags

    last = progress.get("last")
    if last and last.get("sheet") == sheet:
        r = back(int(last["row"]))
        if r is None:
            progress["last"] = was["last"] if last == now["last"] else {"sheet": sheet, "row": target}
        else:
            progress["last"] = {"sheet": sheet, "row": r}

    for i, edit in enumerate(progress.get("edits", [])):
        if edit.get("sheet") != sheet or edit.get("cut") or not isinstance(edit.get("row"), int):
            continue
        k = str(i)
        if k in was["edits"] and now["edits"].get(k) == edit["row"]:
            edit["row"] = was["edits"][k]
            continue
        r = back(edit["row"])
        edit["row"] = target if r is None else r

    record["undone"] = True
    record["undone_when"] = dt.datetime.now().isoformat(timespec="seconds")


# ------------------------------------------------------- the phase complete

def complete_at(progress: dict | None) -> str | None:
    """When the experiential statements phase of the case was marked complete, or None.

    The mark is `complete`, `{"at": "<iso time>"}`, in the progress file, and absent until he marks
    it. A file written before the mark existed has none, so it reads as not complete, and anything
    that is not a time in that shape reads the same way.
    """
    held = (progress or {}).get("complete")
    at = held.get("at") if isinstance(held, dict) else None
    return at if isinstance(at, str) and at.strip() else None


def read_raw(workbook: Path) -> dict | None:
    """The progress file exactly as it sits on disk, with nothing defaulted into it, or None when
    there is none. A file that cannot be read raises, so nothing is ever written over it."""
    path = progress_path(workbook)
    if not path.exists():
        return None
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(i18n.t("server.progress_file_record"))
    return data


def complete_of(workbook: Path) -> str | None:
    """The mark of a case for a row of the case list: its time, or None, and None for a progress
    file that cannot be read. Reads the one small file beside the workbook and nothing else."""
    try:
        return complete_at(read_raw(workbook))
    except (ValueError, OSError):
        return None


def set_complete(workbook: Path, mark: bool, timepoint: int = 1) -> str | None:
    """Mark the phase complete, or reopen it, and write that and nothing else.

    The file is read as it sits, the one key is set or taken away, and it goes back in the shape
    `save_progress` writes, so every other byte of it stays as it was. Marking a case already
    marked keeps the time it was first marked. Returns the time of the mark, or None once reopened.
    `timepoint` 2 or later marks that timepoint's statements alone, in `complete_timepoints`, and
    1 is the `complete` key every file has always had (see `complete_at_timepoint`).
    """
    data = read_raw(workbook)
    if data is None:
        data = {}
    timepoint = int(timepoint or 1)
    if timepoint > 1:
        held = data.get(TP_COMPLETE) if isinstance(data.get(TP_COMPLETE), dict) else {}
        key = str(timepoint)
        if mark:
            if complete_at_timepoint(data, timepoint):
                return complete_at_timepoint(data, timepoint)
            held[key] = {"at": dt.datetime.now().isoformat(timespec="seconds")}
            data[TP_COMPLETE] = held
        elif key in held:
            del held[key]
            if held:
                data[TP_COMPLETE] = held
            else:
                data.pop(TP_COMPLETE, None)
        else:
            return None
        save_progress(workbook, data)
        return complete_at_timepoint(data, timepoint)
    if mark:
        if not complete_at(data):
            data["complete"] = {"at": dt.datetime.now().isoformat(timespec="seconds")}
    elif "complete" in data:
        del data["complete"]
    else:
        return None
    save_progress(workbook, data)
    return complete_at(data)


# ------------------------------------------------------------ timepoints

# A project of two or more timepoints (a longitudinal study, 20 October) keeps each sheet's timepoint
# here, `timepoints` `{"<sheet>": 2}`, a sheet not named at T1, so a file from before and a project
# of one timepoint carry nothing new. T1's Statements complete is `complete`, as it always was, and a
# later timepoint's is in `complete_timepoints`, `{"2": {"at": "<iso>"}}`.
TP_SHEETS = "timepoints"
TP_COMPLETE = "complete_timepoints"


def sheet_timepoints(progress: dict | None) -> dict[str, int]:
    """Each sheet the file places at T2 or later, by its name, anything else in the key passed over."""
    held = (progress or {}).get(TP_SHEETS)
    if not isinstance(held, dict):
        return {}
    out = {}
    for sheet, n in held.items():
        if isinstance(n, int) and not isinstance(n, bool) and n >= 2:
            out[str(sheet)] = n
    return out


def timepoint_of(progress: dict | None, sheet: str) -> int:
    """The timepoint a sheet belongs to, 1 unless the file says later."""
    return sheet_timepoints(progress).get(str(sheet), 1)


def complete_at_timepoint(progress: dict | None, timepoint: int) -> str | None:
    """When a timepoint's statements were marked complete, or None. T1's is `complete`."""
    if int(timepoint or 1) <= 1:
        return complete_at(progress)
    held = (progress or {}).get(TP_COMPLETE)
    entry = held.get(str(timepoint)) if isinstance(held, dict) else None
    at = entry.get("at") if isinstance(entry, dict) else None
    return at if isinstance(at, str) and at.strip() else None


def marked_timepoints(progress: dict | None) -> list[int]:
    """The timepoints after T1 a file holds a Statements complete mark for."""
    held = (progress or {}).get(TP_COMPLETE)
    out = []
    for key in (held if isinstance(held, dict) else {}):
        if str(key).isdigit() and int(key) >= 2 and complete_at_timepoint(progress, int(key)):
            out.append(int(key))
    return sorted(out)


def tag_sheets(workbook: Path, sheets, timepoint: int) -> None:
    """Sheets of a workbook placed at a timepoint, in the progress file beside it, and nothing else
    of the file changed. T1 is no tag, so placing a sheet at T1 takes its tag away, and a file that
    would gain nothing is never written, nor made."""
    timepoint = int(timepoint or 1)
    data = read_raw(workbook)
    had = data is not None
    data = data if had else {}
    held = data.get(TP_SHEETS) if isinstance(data.get(TP_SHEETS), dict) else {}
    was = dict(held)
    for sheet in sheets:
        if timepoint >= 2:
            held[str(sheet)] = timepoint
        else:
            held.pop(str(sheet), None)
    if held == was and (had or not held):
        return
    if held:
        data[TP_SHEETS] = held
    else:
        data.pop(TP_SHEETS, None)
    save_progress(workbook, data)


def complete_round(progress: dict, number: int) -> dict:
    key = str(number)
    entry = progress["rounds"].setdefault(key, {"seconds": 0, "completed": None})
    first_time = entry.get("completed") is None
    if first_time:
        entry["completed"] = dt.datetime.now().isoformat(timespec="seconds")
        day = progress["days"].setdefault(today(), {"rounds": 0})
        day["rounds"] = day.get("rounds", 0) + 1
    return entry


def pace_minutes(progress: dict) -> float | None:
    """Measured clock minutes per completed round. None until a round has been finished."""
    times = [r["seconds"] / 60 for r in progress["rounds"].values()
             if r.get("completed") and r.get("seconds", 0) > 30]
    if not times:
        return None
    return round(sum(times) / len(times), 1)


def streak(days: dict, target: int) -> int:
    """Consecutive days up to today on which the target was met. Today not yet met does not break
    the streak, it just has not been added to it."""
    count = 0
    day = dt.date.today()
    if days.get(day.isoformat(), {}).get("rounds", 0) < target:
        day -= dt.timedelta(days=1)
    while days.get(day.isoformat(), {}).get("rounds", 0) >= target:
        count += 1
        day -= dt.timedelta(days=1)
    return count


def today_work(progress: dict, rounds: list[dict]) -> tuple[int, int]:
    """The turns in the rounds closed today and the seconds measured on them, for the line a break
    shows. A round counts on the day it closed, as the daily tally counts it, so a round closed on
    open brings its turns and the seconds it carries, which may be none."""
    day = today()
    records = progress.get("rounds", {})
    turns = seconds = 0
    for rnd in rounds:
        entry = records.get(str(rnd["number"])) or {}
        if str(entry.get("completed") or "").startswith(day):
            turns += len(rnd["stops"])
            seconds += int(entry.get("seconds") or 0)
    return turns, seconds


DAY_KEY = re.compile(r"^\d{4}-\d{2}-\d{2}$")


def days_total(workbooks) -> dict[str, int]:
    """The rounds closed on each date, summed across the progress files of the workbooks given.

    Each file is read as it sits, with nothing defaulted into it and nothing written. A file that
    cannot be read adds nothing, and so does an entry that is not a date with a count of rounds.
    """
    total: dict[str, int] = {}
    for workbook in workbooks:
        try:
            data = read_raw(workbook) or {}
        except (ValueError, OSError):
            continue
        days = data.get("days")
        if not isinstance(days, dict):
            continue
        for date, entry in days.items():
            count = entry.get("rounds") if isinstance(entry, dict) else None
            if DAY_KEY.match(str(date)) and isinstance(count, int) and not isinstance(count, bool) and count > 0:
                total[date] = total.get(date, 0) + count
    return dict(sorted(total.items()))


def summary(sheets, progress, rounds, interviewer, daily_target) -> dict:
    """What the page draws its numbers from.

    `roundsDone` and the keys beside it are what every page has read since the first version, so a
    page loaded before this answer changed keeps working. `turnsDone` and `turnsTotal` are the case
    line, and `roundTurns` carries every round's decided and total stops with whether the sidecar
    has recorded it as completed, which is what the page back-fills a round from. `complete` is
    the time the phase was marked complete, or None, and a page from before the mark reads past it.

    `sheetRounds` is every sheet's figures, in workbook order, so the page picks the sheet in front
    of him: its rounds, the rounds done and left on it, and the minutes left on it at the measured
    pace. `sheetsDone` and `sheetsLeft` count the sheets with no round left and the sheets with
    one, and `minutesLeft` stays the whole case's. A page from before these reads past them.

    `todayTurns` and `todaySeconds` are the turns in the rounds closed today and the seconds
    measured on them, which the line a break shows sets beside `todayRounds`.
    """
    states = row_states(sheets, progress, interviewer)
    today_turns, today_seconds = today_work(progress, rounds)
    done = [r["number"] for r in rounds if round_done(r, states)]
    pace = pace_minutes(progress)
    left = len(rounds) - len(done)
    records = progress.get("rounds", {})
    finished = set(done)
    per_sheet = []
    for name, count in sheet_counts(rounds).items():
        done_here = sum(1 for r in rounds if r["sheet"] == name and r["number"] in finished)
        left_here = count - done_here
        per_sheet.append({"sheet": name, "rounds": count, "done": done_here, "left": left_here,
                          "minutesLeft": round(pace * left_here) if pace else None})
    return {
        "states": states,
        "roundsDone": done,
        "roundsTotal": len(rounds),
        "roundsLeft": left,
        "paceMinutes": pace,
        "minutesLeft": round(pace * left) if pace else None,
        "todayRounds": progress["days"].get(today(), {}).get("rounds", 0),
        "dailyTarget": daily_target,
        "streak": streak(progress["days"], daily_target),
        "turnsDone": sum(1 for v in states.values() if v in DECIDED),
        "turnsTotal": len(states),
        "roundTurns": [{"number": r["number"], "decided": round_decided(r, states),
                        "total": len(r["stops"]),
                        "recorded": bool(records.get(str(r["number"]), {}).get("completed"))}
                       for r in rounds],
        "complete": complete_at(progress),
        "sheetRounds": per_sheet,
        "sheetsDone": sum(1 for e in per_sheet if e["left"] == 0),
        "sheetsLeft": sum(1 for e in per_sheet if e["left"] > 0),
        "todayTurns": today_turns,
        "todaySeconds": today_seconds,
    }
