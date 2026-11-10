#!/usr/bin/env python3
"""Clear a draft annotation past a redline, keeping an archived copy of the workbook first.

Built for a case where Adam had redlined the Initial sheet as far as row 47 and the rest
of the sheet, plus the whole of 2d, was Claude's draft, none of it usable. This clears columns C,
E and F past the boundary so the case can be worked again from the app with a clean slate. The
transcript column is never touched.

    .venv/bin/python Tools/idiograph/wipe_draft.py \\
        --workbook "<case>/P8 Wren - EN & ES.xlsx" \\
        --sheet Initial --after-row 47 --all-sheets-except Initial --dry-run

Drop `--dry-run` to write. The workbook is archived to `_Archive/<stem> (pre-wipe <date>).xlsx`
beside itself before anything is cleared, and the run refuses outright when Excel holds the file
open. It is a command-line tool on purpose: the app never wipes anything.
"""
from __future__ import annotations

import argparse
import datetime as dt
import shutil
import sys
from pathlib import Path

# the family's folders on the path first (boot.py), under `python -I` too
sys.path.insert(0, str(Path(__file__).resolve().parent))
import boot  # noqa: E402

boot.setup()

import openpyxl

from workbook import WorkbookError, detect_columns, guard_lock, plain_text, _atomic_save

CLEAR = ("es", "en", "kq")


def plan(path: Path, sheet: str, after_row: int, other_sheets: list[str]) -> list[dict]:
    wb = openpyxl.load_workbook(path, rich_text=True)
    if sheet not in wb.sheetnames:
        raise WorkbookError(f"No sheet called {sheet} in {path.name}. Sheets: {', '.join(wb.sheetnames)}")
    rows = []
    for ws in wb.worksheets:
        whole = ws.title in other_sheets
        if ws.title != sheet and not whole:
            continue
        start = 2 if whole else after_row + 1
        cols = detect_columns(ws)
        for r in range(start, ws.max_row + 1):
            filled = {role: plain_text(ws.cell(r, cols[role]).value).strip()
                      for role in CLEAR if role in cols}
            filled = {k: v for k, v in filled.items() if v}
            if filled:
                rows.append({"sheet": ws.title, "row": r, "cells": filled})
    wb.close()
    return rows


def archive(path: Path) -> Path:
    folder = path.parent / "_Archive"
    folder.mkdir(parents=True, exist_ok=True)
    stamp = dt.date.today().strftime("%d%b%y")
    out = folder / f"{path.stem} (pre-wipe {stamp}).xlsx"
    n = 2
    while out.exists():
        out = folder / f"{path.stem} (pre-wipe {stamp}-{n}).xlsx"
        n += 1
    shutil.copy2(path, out)
    return out


def wipe(path: Path, sheet: str, after_row: int, other_sheets: list[str]) -> int:
    wb = openpyxl.load_workbook(path, rich_text=True)
    cleared = 0
    for ws in wb.worksheets:
        whole = ws.title in other_sheets
        if ws.title != sheet and not whole:
            continue
        start = 2 if whole else after_row + 1
        cols = detect_columns(ws)
        for r in range(start, ws.max_row + 1):
            for role in CLEAR:
                if role in cols and ws.cell(r, cols[role]).value is not None:
                    ws.cell(r, cols[role]).value = None
                    cleared += 1
    _atomic_save(wb, path)
    wb.close()
    return cleared


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--workbook", required=True)
    ap.add_argument("--sheet", required=True, help="the sheet holding the redline boundary")
    ap.add_argument("--after-row", type=int, required=True, help="last row to keep on that sheet")
    ap.add_argument("--all-sheets-except", default=None,
                    help="also clear every row of every other sheet, naming the one to spare")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    path = Path(args.workbook).expanduser().resolve()
    if not path.exists():
        raise SystemExit(f"No such workbook: {path}")
    try:
        guard_lock(path)
    except WorkbookError as exc:
        raise SystemExit(str(exc))

    others: list[str] = []
    if args.all_sheets_except:
        book = openpyxl.load_workbook(path, read_only=True)
        others = [s for s in book.sheetnames if s != args.all_sheets_except]
        book.close()

    rows = plan(path, args.sheet, args.after_row, others)
    print(f"{path.name}")
    print(f"  keeping {args.sheet} rows 2 to {args.after_row}")
    if others:
        print(f"  clearing every row of: {', '.join(others)}")
    print(f"  {len(rows)} rows carry something to clear\n")
    print(f"  {'sheet':<12} {'row':>5}  {'C':>4} {'E':>4} {'F':>4}  first statement")
    print("  " + "-" * 76)
    for row in rows[:400]:
        mark = lambda k: "yes" if k in row["cells"] else "."
        sample = (row["cells"].get("es") or row["cells"].get("en") or row["cells"].get("kq") or "")
        sample = sample.replace("\n", " ")[:38]
        print(f"  {row['sheet']:<12} {row['row']:>5}  {mark('es'):>4} {mark('en'):>4} {mark('kq'):>4}  {sample}")
    if len(rows) > 400:
        print(f"  ... and {len(rows) - 400} more")

    if args.dry_run:
        print("\n  Dry run. Nothing was written.")
        return
    if not rows:
        print("\n  Nothing to clear.")
        return
    copy = archive(path)
    print(f"\n  Archived to {copy}")
    cleared = wipe(path, args.sheet, args.after_row, others)
    print(f"  Cleared {cleared} cells in {path.name}")


if __name__ == "__main__":
    main()
