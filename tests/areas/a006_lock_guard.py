from __future__ import annotations

import workbook as wb_mod
from workbook import WorkbookError

from .support import DEMO_SHEET, check, demo_copy


def test_lock_guard(scratch):
    print("\n5. Lock guard")
    work = demo_copy(scratch, "lock", "Juno - EN & ES.xlsx")
    lock = wb_mod.lock_file(work)
    lock.write_bytes(b"pretend Excel lock")
    try:
        wb_mod.read_case(work)
        check("refuses to open a workbook Excel has open", False, "it opened it")
    except WorkbookError as exc:
        check("refuses to open a workbook Excel has open", "Close it in Excel first" in str(exc), str(exc))
    try:
        wb_mod.save_turn(work, DEMO_SHEET, 5, "x", "", "")
        check("refuses to save a workbook Excel has open", False, "it saved it")
    except WorkbookError as exc:
        check("refuses to save a workbook Excel has open", "Close it in Excel first" in str(exc), str(exc))
    lock.unlink()
    wb_mod.read_case(work)
    check("opens again once the lock file is gone", True)
