from __future__ import annotations

import shutil

import workbook as wb_mod

from .support import REFERENCE_WORKBOOK, check, compare_workbooks, skip


def test_reference_roundtrip(scratch):
    print("\n29. The same round trip over the reference workbook, when it is on the machine")
    # Three sheets and 2,640 cells, against the demo's one sheet and 480. The comparison is what
    # this adds: the checks it shares with the demo round trip are not run twice.
    if not REFERENCE_WORKBOOK.exists():
        return skip("reference round trip", "no reference workbook under Main Data")
    keep = scratch / "reference-untouched.xlsx"
    work = scratch / "reference-work.xlsx"
    shutil.copy2(REFERENCE_WORKBOOK, keep)
    shutil.copy2(REFERENCE_WORKBOOK, work)

    case = wb_mod.read_case(work)
    sheets = [s["name"] for s in case["sheets"]]
    initial = next(s for s in case["sheets"] if s["name"] == "Initial")
    her = next(r["name"] for r in initial["rows"] if r["es"].strip())
    same = next(r for r in initial["rows"] if r["es"].strip())
    wb_mod.save_turn(work, same["sheet"], same["row"], same["es"], same["en"], same["kq"])
    problems, checked = compare_workbooks(keep, work, allowed=set())
    check("a no-op save over three sheets changes nothing", not problems,
          f"{checked} cells compared over {len(sheets)} sheets, {len(problems)} differences")
    for p in problems[:5]:
        print(f"        {p}")

    blank = next(r for r in initial["rows"] if not r["es"].strip() and r["name"] == her)
    wb_mod.save_turn(work, blank["sheet"], blank["row"],
                     "Test statement written by the suite", "Test note", "Test quote")
    allowed = {("Initial", blank["row"], c) for c in (3, 5, 6)}
    problems, checked = compare_workbooks(keep, work, allowed=allowed)
    check("one changed turn on three sheets, nothing else moves", not problems,
          f"{checked} cells compared, {len(problems)} differences")
    for p in problems[:5]:
        print(f"        {p}")
