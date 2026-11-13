"""Bold and font colours taken out of a whole project, the words left exactly as they were (clearformat, 13 November
2026, Adam's ruling: take all bold and font colours out, "the quotes that are selected pick out the most relevant
words").

Where the project keeps formatted text, and so what this clears:

- Each participant's workbook, on every sheet the statements screen reads (`workbook._transcript_sheets`), every row
  under the header, in the transcript, the experiential statements, the quotes, the exploratory notes and the
  Interviewer notes columns: a run's bold and colour in a cell of rich text, a highlight's orange among them, and the
  cell's own font's bold and colour. Black in any of its spellings (no colour, theme 1, FF000000, indexed 8 or 64, auto)
  is the body's ink, not a colour, and is left. Italics, underline, strike, the font's name and size, fills, borders,
  widths and the header row, the workbook's own styles, stay as they are. The speaker and timecode columns, a sheet the
  app does not read, and the raw transcripts in a participant's `Source/`, which the app only ever reads, are left.
- His bold in a key quote on an LPET table's row, `rows[<LPET>][<timepoint>]["bold"]` in a participant's
  `Working/<stem>.lpets.json` (the LPETs screen and the Trajectories board draw it from there), and the same key on any
  other board's rows: the GETs, LGETs and Trajectories files at the root and every other board file in a participant's
  `Working/`, a shared copy's own boards among them. A board's cards and every copy of the statements keep plain words,
  with no formatting to clear.

The plain text of every cell of every sheet is read before and after, in memory before the save and again from the
file written, and any difference refuses the whole op: every file written so far is put back as it was. A JSON file is
checked the same way, its every string the same before and after. A copy of each workbook and JSON file it changes
goes into the `_Archive` beside it first, `<stem> (pre-clear-formatting <date-time>)`, as Rename's and the trim's do,
and an agent's write keeps its run's restore point as every agent write does (`agent_changes.through`), so the run's
undo, or the one change's, puts it all back. The dry run writes nothing and answers counts alone, by participant and by
part, never a word."""
from __future__ import annotations

import copy
import json
import os
from pathlib import Path

import openpyxl
from openpyxl.cell.rich_text import CellRichText, TextBlock

import i18n
import locks
import workbook as wb_mod
from workbook import WorkbookError

LABEL = "pre-clear-formatting"
# the workbook's columns this clears, by `detect_columns`' role, and the part each is counted under
ROLES = {"transcript": "transcript", "kq": "quotes", "es": "statements", "en": "notes", "note": "interviewer_notes"}
# the parts the answer counts, in order: cells of the workbook, then rows of the boards
PARTS = ("transcript", "quotes", "statements", "notes", "interviewer_notes", "lpet_table", "copies")
# the board files at a project's root that can hold rows
ROOT_BOARDS = ("idiograph-gets.json", "idiograph-lgets.json", "idiograph-trajectories.json")
PROGRESS_TAIL = ".progress.json"
LPETS_TAIL = ".lpets.json"
# black, as a run or a cell can spell it: the body's ink, not a colour
BLACK_RGB = frozenset(("FF000000", "000000", "00000000"))
BLACK_INDEXED = frozenset((8, 64))


class Differs(WorkbookError):
    """The plain text of a cell, or a string of a board file, read otherwise after the clearing: nothing kept."""


def coloured(color) -> bool:
    """Whether a font's colour is a colour, not the body's black."""
    if color is None:
        return False
    # openpyxl answers only the attribute of the colour's own type, so it is read by its type
    kind = getattr(color, "type", None)
    if kind == "auto":
        return False
    if kind == "theme":
        return not (color.theme == 1 and not (color.tint or 0))
    if kind == "rgb":
        return str(color.rgb or "").upper() not in BLACK_RGB
    if kind == "indexed":
        return color.indexed not in BLACK_INDEXED
    return kind is not None


def marked(font) -> bool:
    """Whether a font carries bold or a colour."""
    return font is not None and (bool(font.b) or coloured(font.color))


def plain_font(font):
    """The font with its bold and its colour off, everything else kept. A run's font left with nothing set answers
    None, so the run is plain words."""
    out = copy.copy(font)
    out.b = None
    out.color = None
    return out


def empty_inline(font) -> bool:
    return all(getattr(font, k, None) in (None, False) for k in
               ("rFont", "charset", "family", "b", "i", "strike", "outline", "shadow", "condense", "extend", "color",
                "sz", "u", "vertAlign", "scheme"))


def cleared_value(value):
    """A cell's value with every run's bold and colour off, and whether any run had them. Runs left with no font
    become plain words, and a cell of plain words alone goes back to a plain string."""
    if not isinstance(value, CellRichText):
        return value, False
    hit = False
    blocks = []
    for block in value:
        if isinstance(block, TextBlock) and marked(block.font):
            hit = True
            font = plain_font(block.font)
            blocks.append(block.text if empty_inline(font) else TextBlock(font, block.text))
        else:
            blocks.append(block)
    if not hit:
        return value, False
    if all(not isinstance(b, TextBlock) for b in blocks):
        return "".join(str(b) for b in blocks), True
    return CellRichText(*blocks), True


def words_of(wb) -> dict:
    """Every cell's plain text, sheet by sheet, the words a clearing must leave as they were."""
    out = {}
    for ws in wb.worksheets:
        for row in ws.iter_rows():
            for c in row:
                if c.value is not None:
                    v = c.value
                    out[(ws.title, c.coordinate)] = wb_mod.plain_text(v) if isinstance(v, (CellRichText, str)) else repr(v)
    return out


def clear_book(wb) -> dict:
    """Bold and colours off in an open workbook, as the module's head says, answering the cells changed by part."""
    counts = {}
    for ws, cols in wb_mod._transcript_sheets(wb):
        for role, part in ROLES.items():
            col = cols.get(role)
            if not col:
                continue
            for r in range(2, ws.max_row + 1):
                cell = ws.cell(r, col)
                if cell.value is None:
                    continue
                value, hit = cleared_value(cell.value)
                if hit:
                    cell.value = value
                if marked(cell.font):
                    cell.font = plain_font(cell.font)
                    hit = True
                if hit:
                    counts[part] = counts.get(part, 0) + 1
    return counts


def book_plan(path: Path) -> dict:
    """What clearing a workbook would change, cells by part, nothing written."""
    path = Path(path)
    wb_mod.guard_lock(path)
    wb = openpyxl.load_workbook(path, rich_text=True)
    try:
        return clear_book(wb)
    finally:
        wb.close()


def clear_workbook(path: Path) -> dict:
    """A workbook's bold and colours cleared and saved by the app's own save, the plain text of every cell checked
    before the save and again from the file written. Refused, `Differs`, with the file as it was when any reads
    otherwise. The caller holds the case's lock and puts the file back on any later failure."""
    path = Path(path)
    wb_mod.guard_lock(path)
    old = path.read_bytes()
    wb = openpyxl.load_workbook(path, rich_text=True)
    try:
        before = words_of(wb)
        counts = clear_book(wb)
        if not counts:
            return counts
        if words_of(wb) != before:
            raise Differs(i18n.t("server.clear_formatting_words_differ", file=path.name))
        wb_mod._atomic_save(wb, path)
    finally:
        wb.close()
    again = openpyxl.load_workbook(path, rich_text=True)
    try:
        same = words_of(again) == before
    finally:
        again.close()
    if not same:
        locks.write_over(path, old)
        raise Differs(i18n.t("server.clear_formatting_words_differ", file=path.name))
    return counts


# ---------------------------------------------------------------- the boards

def bold_rows(node, found: list) -> list:
    """Every row of a board holding bold, `(row, key)`, the key the participant's or the timepoint's, wherever a
    `rows` map stands in the file, a board's own or one kept in its History."""
    if isinstance(node, dict):
        rows = node.get("rows")
        if isinstance(rows, dict):
            for cases in rows.values():
                if isinstance(cases, dict):
                    for key, row in cases.items():
                        if isinstance(row, dict) and isinstance(row.get("bold"), list) and row["bold"]:
                            found.append((row, str(key)))
        for v in node.values():
            bold_rows(v, found)
    elif isinstance(node, list):
        for v in node:
            bold_rows(v, found)
    return found


def strings_of(node, out: list) -> list:
    """Every string value of a file's data, in order: the words, which taking bold off never changes."""
    if isinstance(node, dict):
        for v in node.values():
            strings_of(v, out)
    elif isinstance(node, list):
        for v in node:
            strings_of(v, out)
    elif isinstance(node, str):
        out.append(node)
    return out


def board_files(root: Path, books: list[dict]) -> list[tuple[Path, str | None]]:
    """The board files that can hold rows: the root's, whose rows are by participant (None), and each participant's
    in `Working/` but their progress file, all theirs (their case)."""
    out = [(Path(root) / name, None) for name in ROOT_BOARDS if (Path(root) / name).is_file()]
    for b in books:
        book = Path(b["workbook"])
        working = book.parent / "Working"
        if not working.is_dir():
            continue
        for f in sorted(working.glob(f"{book.stem}.*json")):
            if f.is_file() and not f.name.endswith(PROGRESS_TAIL) and f.suffix == ".json":
                out.append((f, str(b["case"])))
    return out


def board_part(path: Path) -> str:
    return "lpet_table" if path.name.endswith(LPETS_TAIL) else "copies"


def board_plan(path: Path, owner: str | None, only: set | None) -> tuple[dict | None, dict]:
    """A board file's data with the bold taken off its rows, and the rows cleared by participant, `only` the
    participants to clear at a root file. None for a file with nothing to clear."""
    try:
        data = json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        raise WorkbookError(i18n.t("server.clear_formatting_unreadable", file=Path(path).name, exc=exc)) from None
    counts: dict = {}
    for row, key in bold_rows(data, []):
        who = owner if owner is not None else key
        if owner is None and only is not None and key not in only:
            continue
        row.pop("bold", None)
        counts[who] = counts.get(who, 0) + 1
    return (data if counts else None), counts


def write_board(path: Path, data: dict) -> None:
    """A board file written as the app writes it (`themes.render`), through a temporary file moved over it, its every
    string checked against the file as it was first."""
    import themes
    path = Path(path)
    before = strings_of(json.loads(path.read_text(encoding="utf-8")), [])
    text = themes.render(data) + "\n"
    if strings_of(json.loads(text), []) != before:
        raise Differs(i18n.t("server.clear_formatting_words_differ", file=path.name))
    tmp = path.with_name(path.name + ".tmp")
    tmp.write_text(text, encoding="utf-8", newline="\n")
    os.replace(tmp, path)
    wb_mod.note_written(path)


def archive_json(path: Path, folder: Path) -> Path:
    import codes as codes_mod
    return codes_mod.root_archive(folder, Path(path), LABEL)


# ---------------------------------------------------------------- the op

def plan(root: Path, books: list[dict], only: set | None = None) -> dict:
    """What the op would clear, nothing written: `by_participant`, each participant's counts by part, `totals` by
    part, `workbooks` and `boards` the files it would change by their names relative to the root, and `cells` and
    `rows` in all."""
    root = Path(root)
    by: dict = {}
    workbooks, boards = [], []
    for b in books:
        counts = book_plan(Path(b["workbook"]))
        if counts:
            by.setdefault(str(b["case"]), {}).update(counts)
            workbooks.append(Path(b["workbook"]))
    for path, owner in board_files(root, books):
        _data, counts = board_plan(path, owner, only)
        if counts:
            boards.append((path, owner))
            for who, n in counts.items():
                part = board_part(path)
                row = by.setdefault(who, {})
                row[part] = row.get(part, 0) + n
    return answer(root, by, workbooks, [p for p, _ in boards])


def answer(root: Path, by: dict, workbooks: list, boards: list) -> dict:
    def rel(p):
        try:
            return Path(p).resolve().relative_to(Path(root).resolve()).as_posix()
        except ValueError:
            return Path(p).name
    people = [{"case": who, **{part: counts.get(part, 0) for part in PARTS}} for who, counts in by.items()]
    totals = {part: sum(p[part] for p in people) for part in PARTS}
    return {"by_participant": people, "totals": totals,
            "cells": sum(totals[p] for p in PARTS[:5]), "rows": totals["lpet_table"] + totals["copies"],
            "workbooks": [rel(p) for p in workbooks], "boards": [rel(p) for p in boards]}


def clear(root: Path, books: list[dict], only: set | None = None) -> dict:
    """The op itself, under the locks the caller holds: each workbook and board file to change copied to its
    `_Archive` first, then cleared and checked. Any failure, a cell's words reading otherwise among them, puts back
    every file written so far, byte for byte, and raises. Answers as `plan`, with `archived`, the copies kept."""
    root = Path(root)
    written: list[tuple[Path, bytes, bool]] = []
    archived: list[Path] = []
    by: dict = {}
    workbooks, boards = [], []
    try:
        for b in books:
            book = Path(b["workbook"])
            if not book_plan(book):
                continue
            archived.append(wb_mod.archive_copy(book, LABEL))
            old = book.read_bytes()
            counts = clear_workbook(book)
            written.append((book, old, True))
            if counts:
                by.setdefault(str(b["case"]), {}).update(counts)
                workbooks.append(book)
        for path, owner in board_files(root, books):
            data, counts = board_plan(path, owner, only)
            if data is None:
                continue
            folder = root if owner is None else wb_mod.case_folder(path)
            archived.append(archive_json(path, folder))
            old = path.read_bytes()
            write_board(path, data)
            written.append((path, old, False))
            boards.append(path)
            for who, n in counts.items():
                part = board_part(path)
                row = by.setdefault(who, {})
                row[part] = row.get(part, 0) + n
    except BaseException:
        for path, old, is_book in reversed(written):
            try:
                if is_book:
                    locks.write_over(path, old)
                else:
                    tmp = path.with_name(path.name + ".tmp")
                    tmp.write_bytes(old)
                    os.replace(tmp, path)
            except OSError:
                pass
        # and the copies it kept, the files being as they were
        for copy_kept in archived:
            try:
                copy_kept.unlink()
            except OSError:
                pass
        raise
    out = answer(root, by, workbooks, boards)
    out["archived"] = [p.name for p in archived]
    return out
