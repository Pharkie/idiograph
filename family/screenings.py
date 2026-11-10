"""Sift's screenings, read and never written (22 October 2026, the family codebase's second build, from
Sift's `sift.py` and `sift_search.py`). A screening is a folder holding `screening.csv`, one row a record
by its `rec_id`, its PDFs in `pdfs/<rec_id>.pdf` beside it, and a review keeps a screening of its own
and one in each run folder under `runs/`. Sift reads and writes its screenings through `sift.py`, which
takes the reading here, and Trace finds a reference's PDF and Zotero item in them through here alone.

`reviews_in` reads Sift's list of its projects from a state file, so Trace's own app finds the PDFs in
the screenings of Sift's projects as it did while it ran inside Idiograph (Adam's call, 22 October), and
never writes that file.

The standard library and the family's `errors.py` only, and nothing here writes.
"""
from __future__ import annotations

import csv
import io
import json
import re
from pathlib import Path

from errors import ScreeningError

CSV_NAME = "screening.csv"
PDF_DIR = "pdfs"
RUNS_DIR = "runs"
REQUIRED = ("rec_id", "title", "abstract")
# the key of the record's item in Zotero, which Sift's sync writes (see `sift_zotero.py`)
ZOTERO_COLUMN = "zotero_key"
# Sift's list of its projects in its state file, each `{"folder", "opened"}` and a name he gave
REVIEWS_KEY = "sift_reviews"


# ----------------------------------------------------------------- the CSV

class Screening:
    """The CSV as it stands: its header, its rows as lists in the header's order, how its lines end
    and whether it opens with a byte order mark, so a rewrite keeps all three."""

    def __init__(self, folder: Path, header: list[str], rows: list[list[str]], newline: str, bom: bool):
        self.folder = Path(folder)
        self.header = header
        self.rows = rows
        self.newline = newline
        self.bom = bom
        self.col = {name: i for i, name in enumerate(header)}
        self.ids = [row[self.col["rec_id"]].strip() for row in rows]
        self.at = {rec: i for i, rec in enumerate(self.ids)}

    def cell(self, rec: str, name: str) -> str:
        i = self.col.get(name)
        row = self.rows[self.at[rec]]
        return row[i] if i is not None and i < len(row) else ""

    def record(self, rec: str) -> dict:
        return {name: self.cell(rec, name) for name in self.header}


def csv_path(folder) -> Path:
    return Path(folder) / CSV_NAME


def is_screening(folder) -> bool:
    try:
        return csv_path(folder).is_file()
    except OSError:
        return False


def load(folder) -> Screening:
    """The screening in `folder`, refused in one line, a ScreeningError, when it has no CSV, the CSV lacks
    a required column, or a record has no rec_id or shares one."""
    path = csv_path(folder)
    if not path.is_file():
        raise ScreeningError(f"There is no {CSV_NAME} in that folder.")
    raw = path.read_bytes()
    try:
        text = raw.decode("utf-8-sig")
    except UnicodeDecodeError:
        raise ScreeningError(f"{CSV_NAME} is not UTF-8, so Sift cannot read it.") from None
    rows = [row for row in csv.reader(io.StringIO(text, newline="")) if row]
    if not rows:
        raise ScreeningError(f"{CSV_NAME} is empty.")
    header = [h.strip() for h in rows[0]]
    missing = [c for c in REQUIRED if c not in header]
    if missing:
        raise ScreeningError(f"{CSV_NAME} needs the columns {', '.join(missing)}, so it was not opened.")
    width = len(header)
    body = [row + [""] * (width - len(row)) for row in rows[1:]]
    sc = Screening(folder, header, body, "\r\n" if "\r\n" in text else "\n", raw.startswith(b"\xef\xbb\xbf"))
    seen: set[str] = set()
    for n, rec in enumerate(sc.ids, 2):
        if not rec:
            raise ScreeningError(f"Line {n} of {CSV_NAME} has no rec_id, so it was not opened.")
        if rec in seen:
            raise ScreeningError(f"{rec} is in {CSV_NAME} twice, so it was not opened.")
        seen.add(rec)
    return sc


def pdf_path(folder, rec_id) -> Path | None:
    """A record's PDF, `pdfs/<rec_id>.pdf` beside the CSV, and nothing that resolves anywhere else."""
    rec = str(rec_id or "")
    if not rec or rec != rec.strip() or rec.startswith(".") or any(c in rec for c in "/\\\x00:"):
        return None
    base = (Path(folder) / PDF_DIR).resolve()
    for name in (f"{rec}.pdf", f"{rec}.PDF"):
        p = (base / name).resolve()
        if p.parent == base and p.is_file():
            return p
    return None


# ------------------------------------------------------------------ the runs

def runs_path(folder) -> Path:
    return Path(folder) / RUNS_DIR


# a run folder's name, its day and, for a later run that day, its number: 2026-10-09, then 2026-10-09-2
RUN_NAME = re.compile(r"(\d{4}-\d{2}-\d{2})(?:-([2-9]|[1-9]\d{1,3}))?")


def run_parts(name) -> tuple[str, int]:
    """A run folder's day and its number that day, the first for a day's own name. A folder of another
    name stands as a day of its own, its first run."""
    m = RUN_NAME.fullmatch(str(name or ""))
    return (m.group(1), int(m.group(2) or 1)) if m else (str(name or ""), 1)


def run_dirs(folder) -> list[Path]:
    """Every run folder under `runs/`, newest first, in the order they were made: by day, and within a
    day by its number."""
    base = runs_path(folder)
    if not base.is_dir():
        return []
    return sorted((p for p in base.iterdir() if p.is_dir() and not p.name.startswith(".")), key=lambda p: run_parts(p.name),
                  reverse=True)


def of_review(folder) -> list[Path]:
    """A review's screenings, its own and each run's, newest run first. Only reads."""
    folder = Path(folder)
    out = [folder] if is_screening(folder) else []
    try:
        out += [run for run in run_dirs(folder) if is_screening(run)]
    except OSError:
        pass
    return out


# ------------------------------------------------------------ Sift's projects

def reviews_in(state_file: Path, base: Path) -> list[Path]:
    """The folders of Sift's projects, newest first, from Sift's own state file, each relative one taken
    from `base`, the folder Sift's paths start from, and none when the file is not there or cannot be
    read. Only reads, and never writes the file."""
    try:
        held = json.loads(Path(state_file).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return []
    rows = held.get(REVIEWS_KEY) if isinstance(held, dict) else None
    out = []
    for e in rows if isinstance(rows, list) else []:
        if isinstance(e, dict) and isinstance(e.get("folder"), str) and e["folder"].strip():
            p = Path(e["folder"].strip()).expanduser()
            out.append(p if p.is_absolute() else Path(base) / p)
    return out
