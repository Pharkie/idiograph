#!/usr/bin/env python3
"""Export every statement in a case to CSV, in the format of the reference file.

the reference All Experiential Statements CSV of the finished case:
a UTF-8 BOM, then `Interview,Timestamp,Experiential statement,Proposed PET (blank for you)`,
one row per statement, timestamps as HH:MM:SS. A last column, `Quote` (`Key quote` until 22 October
2026), after the reference's four, holds the statement's own quote, the one at its place in the
quotes cell, without the
marks the workbook keeps round it, as the print view and the PET draft take it, and nothing for a
statement with none or a place holding "(no quote)".

The PET column is empty unless a themes file is named: then each statement carries the labels over
its card in that board, top-most first and joined with ` / `, `Binned` for a card in the bin,
and nothing for a card left unplaced. The header keeps its name either way.

With a themes file the rows go theme by theme in canvas order: each theme's statements in the
order the canvas reads them, top to bottom and left to right along a row, a sub-theme's where its
frame's top sits, then the statements left unplaced and last the discarded, both in transcript
order. Without one, every row keeps its transcript order.

In a project of two or more timepoints (21 October) `timepoints` names them, each `(n, label)`, and
the CSV holds every one of them named, timepoint by timepoint, a last column, `Timepoint`, its label,
and each timepoint's PET column from that timepoint's own board. A project of one names none, and its
CSV is the one it always was, byte for byte.

The interviewer notes go to a file of their own beside the CSV, and only when asked for, so the CSV
stays statements alone in the reference format. `export_notes` writes them in transcript order,
sheet by sheet, each note under its timecode, and writes nothing for a case with none.
"""
from __future__ import annotations

import csv
import datetime as dt
from pathlib import Path

import openpyxl

import formats
import i18n
import themes as themes_mod
from workbook import detect_columns, guard_lock, hhmmss, quote_entries, split_entries, ts_seconds

def header() -> list[str]:
    """The CSV's heading row, in the run's language (the text layer, 28 October 2026)."""
    return [i18n.t("exports.csv_interview"), i18n.t("exports.csv_timestamp"), i18n.t("exports.csv_statement"),
            i18n.t("exports.csv_proposed_pet"), i18n.t("exports.csv_quote")]


def output_path(workbook: Path) -> Path:
    workbook = Path(workbook)
    stem = workbook.stem.replace(" - EN & ES", "").strip()
    # named in the words of the project's method, a thematic analysis project's "All Codes" (tagaps)
    return workbook.parent / "Working" / i18n.t("exports.csv_name", stem=stem)




def export(workbook: Path, out: Path | None = None, themes=None, guard: bool = True,
           timepoints: list | None = None, dry_run: bool = False) -> dict:
    """Write the CSV. `themes` is the themes file and a board id in it, None for the current one,
    and fills the PET column. `guard` refuses a workbook Excel has open, as Settings always has. The
    Themes screen's export passes False: the workbook is only read, never written. `timepoints`, in
    a project of two or more, the timepoints whose statements it holds, each `(n, label)`, and then
    the PET column of each from that timepoint's current board, or from `themes`' board id at one.
    `dry_run` (26 October, parity4) reads and refuses as the export does and writes nothing, its answer
    the file it would write and the statements it would hold."""
    workbook = Path(workbook)
    if guard:
        guard_lock(workbook)
    out = Path(out) if out else output_path(workbook)
    if not dry_run:
        out.parent.mkdir(parents=True, exist_ok=True)
    if timepoints:
        return export_timepoints(workbook, out, themes, list(timepoints), dry_run=dry_run)
    pet, placed = themes_mod.pet_table(*themes, read=themes_mod.read_cards(workbook)) if themes else ({}, [])
    rows = ordered(statement_rows(workbook), pet, placed)
    if dry_run:
        return {"path": str(out), "statements": len(rows)}
    with open(out, "w", encoding="utf-8-sig", newline="") as fh:
        writer = csv.writer(fh)
        writer.writerow(header())
        writer.writerows(rows)
    return {"path": str(out), "statements": len(rows)}


def export_timepoints(workbook: Path, out: Path, themes, timepoints: list, dry_run: bool = False) -> dict:
    """The CSV of a project of two or more timepoints: each timepoint's statements in turn, ordered and
    labelled from that timepoint's board, its label in the last column."""
    placed_at = themes_mod.placed_sheets(workbook)
    every = statement_rows(workbook)
    rows = []
    for n, label in timepoints:
        with themes_mod.scoped(n):
            held = themes_mod.themes_path(workbook)
            board = themes if themes and len(timepoints) == 1 else ((held, None) if held.exists() else None)
            pet, placed = themes_mod.pet_table(*board, read=themes_mod.read_cards(workbook)) if board else ({}, [])
        mine = [(key, row) for key, row in every if placed_at.get(row[0], 1) == n]
        rows += [row + [label] for row in ordered(mine, pet, placed)]
    if dry_run:
        return {"path": str(out), "statements": len(rows)}
    with open(out, "w", encoding="utf-8-sig", newline="") as fh:
        writer = csv.writer(fh)
        writer.writerow(header() + [i18n.t("exports.csv_timepoint")])
        writer.writerows(rows)
    return {"path": str(out), "statements": len(rows)}


def statement_rows(workbook: Path) -> list:
    """Every statement of the workbook in transcript order, each `(key, row)`, its PET cell empty."""
    wb = openpyxl.load_workbook(workbook, data_only=True)
    rows = []
    for ws in wb.worksheets:
        cols = detect_columns(ws)
        if "es" not in cols or "ts" not in cols:
            continue
        for r in range(2, ws.max_row + 1):
            stamp = hhmmss(ts_seconds(ws.cell(r, cols["ts"]).value))
            # each statement's own quote, the one at its place, "(no quote)" read as none
            said = quote_entries(ws.cell(r, cols["kq"]).value) if "kq" in cols else []
            for i, text in enumerate(split_entries(ws.cell(r, cols["es"]).value)):
                key = themes_mod.card_key(ws.title, r, i)
                quote = themes_mod.bare(said[i]) if i < len(said) else ""
                rows.append((key, [ws.title, stamp, text, "", quote]))
    wb.close()
    return rows


def ordered(rows: list, pet: dict, placed: list) -> list:
    """The rows with their PET cells filled from `pet`, theme by theme in canvas order when a board
    places them, else in transcript order."""
    rows = [(key, row[:3] + [pet.get(key, "")] + row[4:]) for key, row in rows]
    if placed:
        rank = {key: i for i, key in enumerate(placed)}
        order = {key: i for i, (key, _) in enumerate(rows)}
        rows.sort(key=lambda item: (0, rank[item[0]]) if item[0] in rank
                  else (2 if pet.get(item[0]) == themes_mod.DISCARDED else 1, order[item[0]]))
    return [row for _, row in rows]


def notes_path(workbook: Path) -> Path:
    workbook = Path(workbook)
    stem = workbook.stem.replace(" - EN & ES", "").strip()
    return workbook.parent / "Working" / f"{stem} - Interviewer notes.md"


def export_notes(workbook: Path, case: str, out: Path | None = None, today: dt.date | None = None,
                 dry_run: bool = False) -> dict:
    """Write the interviewer notes to `<case>/Working/<stem> - Interviewer notes.md`.

    A heading with the case name, one line with the date, then the notes in transcript order,
    sheet by sheet, each under its timecode as HH:MM:SS with one blank line between notes. A sheet
    name stands as a heading only when the workbook has more than one sheet. A case with no notes
    writes no file, and the answer says so with a path of None. The workbook is only read. `dry_run`
    answers the same and writes nothing.
    """
    workbook = Path(workbook)
    wb = openpyxl.load_workbook(workbook, data_only=True)
    sheets = []
    try:
        for ws in wb.worksheets:
            cols = detect_columns(ws)
            if not {"name", "ts", "transcript"} <= set(cols):
                continue
            notes = []
            if "note" in cols:
                for r in range(2, ws.max_row + 1):
                    lines = split_entries(ws.cell(r, cols["note"]).value)
                    if lines:
                        notes.append((hhmmss(ts_seconds(ws.cell(r, cols["ts"]).value)), lines))
            sheets.append((ws.title, notes))
    finally:
        wb.close()
    count = sum(len(notes) for _, notes in sheets)
    if not count:
        return {"path": None, "notes": 0}
    day = today or dt.date.today()
    text = [i18n.t("exports.notes_title", case=case), "",
            i18n.t("exports.notes_exported", date=formats.date_words(day)), ""]
    for title, notes in sheets:
        if not notes:
            continue
        if len(sheets) > 1:
            text += [f"## {title}", ""]
        for stamp, lines in notes:
            text += [stamp, *lines, ""]
    out = Path(out) if out else notes_path(workbook)
    if dry_run:
        return {"path": str(out), "notes": count}
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text("\n".join(text), encoding="utf-8", newline="\n")
    return {"path": str(out), "notes": count}


if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        raise SystemExit(__doc__)
    result = export(Path(sys.argv[1]))
    print(f"{result['statements']} statements written to {result['path']}")


def __getattr__(name: str):
    """The CSV's headings as the checks name them, in the run's language when asked for."""
    if name == "HEADER":
        return header()
    if name == "TIMEPOINT_HEADER":
        return i18n.t("exports.csv_timepoint")
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
