from __future__ import annotations

import openpyxl
from openpyxl.cell.rich_text import CellRichText, TextBlock

import workbook as wb_mod

from .support import (
    DEMO_SHEET, DEMO_WORKBOOK, TOOL, check, compare_workbooks, count_rich, demo_copy, demo_sheet, skip,
)


def test_roundtrip(scratch):
    print("\n1. Round trip: a no-op save and a real save leave everything else untouched")
    check("the demo workbook is built from the demo's sources, which ship with the app, so the suite needs no live data",
          DEMO_WORKBOOK.exists() and (TOOL / "demo" / "source" / "Juno - interview.csv").is_file(), DEMO_WORKBOOK.name)
    if not DEMO_WORKBOOK.exists():
        return skip("round trip", "no demo workbook, so nothing else here can run either")
    keep = demo_copy(scratch, "roundtrip", "untouched.xlsx")
    work = demo_copy(scratch, "roundtrip", "Juno - EN & ES.xlsx")

    before_rich = count_rich(keep)

    # a turn that already carries a statement, written back unchanged
    initial, her, _ = demo_sheet(work)
    same = next(r for r in initial["rows"] if r["es"].strip())
    wb_mod.save_turn(work, same["sheet"], same["row"], same["es"], same["en"], same["kq"])
    problems, checked = compare_workbooks(keep, work, allowed=set())
    check("no-op save changes nothing", not problems, f"{checked} cells compared, {len(problems)} differences")
    if problems:
        for p in problems[:5]:
            print(f"        {p}")

    # a turn that had nothing, now given a statement, a note and a quote
    blank = next(r for r in initial["rows"] if not r["es"].strip() and r["name"] == her)
    wb_mod.save_turn(work, blank["sheet"], blank["row"],
                     "Test statement written by the suite", "Test note", "Test quote")
    allowed = {(DEMO_SHEET, blank["row"], c) for c in (3, 5, 6)}
    problems, checked = compare_workbooks(keep, work, allowed=allowed)
    check("one changed turn, nothing else moves", not problems,
          f"changed r{blank['row']} columns C, E, F, {checked} cells compared")
    for p in problems[:5]:
        print(f"        {p}")

    after = wb_mod.read_case(work)
    row = next(r for s in after["sheets"] for r in s["rows"] if r["row"] == blank["row"] and r["sheet"] == DEMO_SHEET)
    check("the statement reads back", row["es"] == "Test statement written by the suite", repr(row["es"]))
    check("rich text run count preserved", count_rich(work) == before_rich,
          f"{count_rich(work)} cells with orange runs, was {before_rich}")

    wb = openpyxl.load_workbook(work, rich_text=True)
    sample = next(ws.cell(r, 4).value for ws in wb.worksheets for r in range(2, ws.max_row + 1)
                  if isinstance(ws.cell(r, 4).value, CellRichText))
    themes = [getattr(b.font.color, "theme", None) for b in sample if isinstance(b, TextBlock)]
    wb.close()
    check("orange runs keep theme 9", 9 in themes, f"themes seen in one cell: {themes}")

    import zipfile
    with zipfile.ZipFile(work) as z:
        parts = z.namelist()
        inline = b'inlineStr' in z.read("xl/worksheets/sheet1.xml")
    check("saved as shared strings, the way Excel writes them",
          "xl/sharedStrings.xml" in parts and not inline,
          "no inline strings left for Excel to object to")
