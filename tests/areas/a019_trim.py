from __future__ import annotations

import shutil
from pathlib import Path

import openpyxl

import rounds as rounds_mod
import workbook as wb_mod
from workbook import WorkbookError

from .support import (
    DEMO_SHEET, add_second_sheet, check, compare_workbooks, demo_copy, orange_runs, sheet_signature,
)


def test_trim(scratch):
    print("\n19. Trimming the ends off a sheet")
    work = add_second_sheet(demo_copy(scratch, "trim", "Juno - EN & ES.xlsx"))
    case = work.parent
    keep = scratch / "trim" / "untouched.xlsx"
    shutil.copy2(work, keep)

    before_cells, before_fills, before_shape, before_heights = sheet_signature(keep, DEMO_SHEET)
    before_orange = orange_runs(keep, DEMO_SHEET)
    other_before = sheet_signature(keep, "2d")

    wb = openpyxl.load_workbook(keep)
    rows_before = wb[DEMO_SHEET].max_row
    wb.close()

    # a sidecar with something on every side of both cuts
    progress = rounds_mod.load_progress(work)
    progress["rows"] = {"Initial:3": "has-content", "Initial:9": "reviewed-empty",
                        "Initial:40": "has-content", "2d:5": "has-content"}
    progress["flags"] = ["Initial:3", "Initial:40", "2d:5"]
    progress["last"] = {"sheet": DEMO_SHEET, "row": 3}
    rounds_mod.save_progress(work, progress)

    plan = wb_mod.trim_preview(work, DEMO_SHEET, 7, "before")
    check("the preview counts the rows a front cut takes",
          plan["count"] == 6 and plan["first"] == 2 and plan["last"] == 7, str(plan["count"]))

    result = wb_mod.trim_rows(work, DEMO_SHEET, 7, "before")
    check("a front cut takes rows 2 to the boundary", result["removed"] == 6, str(result["removed"]))
    check("the backup was written into _Archive",
          Path(result["backup"]).exists() and Path(result["backup"]).parent.name == "_Archive",
          Path(result["backup"]).name)
    check("the backup is the workbook as it was",
          not compare_workbooks(keep, Path(result["backup"]), allowed=set())[0])

    after_cells, after_fills, after_shape, after_heights = sheet_signature(work, DEMO_SHEET)
    check("the header row is untouched", after_cells[0] == before_cells[0])
    check("the rows left are the ones after the cut, in order",
          after_cells[1:] == before_cells[7:], f"{len(after_cells) - 1} rows, was {rows_before - 1}")
    check("widths, freeze pane and zoom are unchanged", after_shape == before_shape, str(after_shape[1:]))
    check("no fill was added", after_fills == before_fills, str(after_fills))
    check("the other sheet is untouched", sheet_signature(work, "2d") == other_before)

    after_orange = orange_runs(work, DEMO_SHEET)
    survived = before_orange[len(before_orange) - len(after_orange):]
    check("every orange run on a surviving row survives, run for run",
          after_orange == survived and len(after_orange) > 0,
          f"{len(after_orange)} runs left of {len(before_orange)}")

    # the sidecar is moved by rounds.py, the way the endpoint moves it
    progress = rounds_mod.load_progress(work)
    rounds_mod.rekey_after_trim(progress, DEMO_SHEET, "before", 7, result["timecode"],
                                result["head"], str(result["backup"]))
    rounds_mod.save_progress(work, progress)
    progress = rounds_mod.load_progress(work)
    check("the sidecar rows moved up by the number cut",
          progress["rows"] == {"Initial:3": "reviewed-empty", "Initial:34": "has-content",
                               "2d:5": "has-content"},
          str(progress["rows"]))
    check("the flags moved with them", progress["flags"] == ["Initial:34", "2d:5"], str(progress["flags"]))
    check("a last pointer inside the cut is cleared for the server to reset",
          progress["last"] is None, str(progress["last"]))
    check("the trim is recorded for the audit",
          len(progress["trims"]) == 1 and progress["trims"][0]["direction"] == "before"
          and progress["trims"][0]["row"] == 7 and progress["trims"][0]["head"]
          and progress["trims"][0]["backup"],
          str({k: v for k, v in progress["trims"][0].items() if k in ("direction", "row", "timecode")}))

    # and the other end
    mid_cells = sheet_signature(work, DEMO_SHEET)[0]
    rows_now = len(mid_cells)
    progress["rows"] = {"Initial:3": "has-content", f"Initial:{rows_now}": "has-content"}
    progress["flags"] = ["Initial:3", f"Initial:{rows_now}"]
    progress["last"] = {"sheet": DEMO_SHEET, "row": rows_now}
    rounds_mod.save_progress(work, progress)

    tail = wb_mod.trim_rows(work, DEMO_SHEET, rows_now - 3, "after")
    check("a back cut takes the boundary and everything after it", tail["removed"] == 4, str(tail["removed"]))
    tail_cells = sheet_signature(work, DEMO_SHEET)[0]
    check("the rows left are the ones before the cut, in order",
          tail_cells == mid_cells[:rows_now - 4], f"{len(tail_cells)} rows")
    progress = rounds_mod.load_progress(work)
    rounds_mod.rekey_after_trim(progress, DEMO_SHEET, "after", rows_now - 3, tail["timecode"],
                                tail["head"], str(tail["backup"]))
    rounds_mod.save_progress(work, progress)
    progress = rounds_mod.load_progress(work)
    check("a back cut drops the cut rows and moves nothing",
          progress["rows"] == {"Initial:3": "has-content"} and progress["flags"] == ["Initial:3"],
          str(progress["rows"]))
    check("two trims are recorded", len(progress["trims"]) == 2)
    check("no row height is left past the last row",
          all(k <= len(tail_cells) for k in sheet_signature(work, DEMO_SHEET)[3]))

    # a small workbook of its own, because the demo carries no custom row heights and openpyxl
    # leaves those behind on a delete
    tall = case / "heights.xlsx"
    book = openpyxl.Workbook()
    ws = book.active
    ws.title = DEMO_SHEET
    for col, head in zip("ABCDEF", wb_mod.HEADER):
        ws[f"{col}1"] = head
    for r in range(2, 10):
        ws.cell(r, 1, "Him" if r % 2 else "Her")
        ws.cell(r, 2, f"00:0{r}:00")
        ws.cell(r, 4, f"row {r}")
        ws.row_dimensions[r].height = 10 + r
    book.save(tall)
    book.close()
    wb_mod.trim_rows(tall, DEMO_SHEET, 4, "before")
    heights = sheet_signature(tall, DEMO_SHEET)[3]
    check("custom row heights move up with the rows they belong to",
          heights == {2: 15.0, 3: 16.0, 4: 17.0, 5: 18.0, 6: 19.0}, str(heights))

    lock = wb_mod.lock_file(work)
    lock.write_bytes(b"pretend Excel lock")
    try:
        wb_mod.trim_rows(work, DEMO_SHEET, 5, "after")
        check("refuses to trim a workbook Excel has open", False, "it trimmed it")
    except WorkbookError as exc:
        check("refuses to trim a workbook Excel has open", "Close it in Excel first" in str(exc), str(exc))
    lock.unlink()
    try:
        wb_mod.trim_rows(work, DEMO_SHEET, 1, "before")
        check("the header row is never cut", False, "it cut it")
    except WorkbookError as exc:
        check("the header row is never cut", "header row" in str(exc), str(exc))
