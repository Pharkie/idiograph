#!/usr/bin/env python3
"""Build `template/Transcript template.xlsx`, the shape of a transcript the app reads as it is.

Three columns, Name, Timestamp and Transcript, one turn per row, the times as Excel times, and three
invented rows from the demo's world to show the shape. A transcript typed by hand, or pasted in
from elsewhere, goes into a copy of it in the case's `Source/` folder.

    .venv/bin/python Tools/idiograph/make_template.py

The rows are here, in the open, so what ships can be read without opening Excel.
"""
from __future__ import annotations

import datetime as dt
import sys
from pathlib import Path

import openpyxl
from openpyxl.styles import Alignment, Font

# the family's folders on the path first (boot.py), under `python -I` too
sys.path.insert(0, str(Path(__file__).resolve().parent))
import boot  # noqa: E402

boot.setup()
TEMPLATE = boot.resource("template/Transcript template.xlsx")
SHEET = "Transcript"
HEADER = ["Name", "Timestamp", "Transcript"]
ROWS = [
    ("Interviewer", dt.time(0, 0, 4), "How did the first week with the dog go?"),
    ("Juno", dt.time(0, 0, 9), "Slower than I thought. She slept most of the day, and I kept "
                               "checking she was still breathing."),
    ("Interviewer", dt.time(0, 0, 31), "What was that like, the checking?"),
]
WIDTHS = {"A": 16.0, "B": 12.0, "C": 80.0}


def build(out: Path = TEMPLATE) -> Path:
    out.parent.mkdir(parents=True, exist_ok=True)
    book = openpyxl.Workbook()
    ws = book.active
    ws.title = SHEET
    ws.append(HEADER)
    for cell in ws[1]:
        cell.font = Font(name="Calibri", size=11, bold=True)
    for name, time, words in ROWS:
        ws.append([name, time, words])
        ws.cell(ws.max_row, 2).number_format = "h:mm:ss"
    for row in ws.iter_rows(min_row=2):
        for cell in row:
            cell.alignment = Alignment(wrap_text=True, vertical="top")
    for col, width in WIDTHS.items():
        ws.column_dimensions[col].width = width
    ws.freeze_panes = "A2"
    book.save(out)
    book.close()
    return out


if __name__ == "__main__":
    print(build())
