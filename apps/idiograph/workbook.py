#!/usr/bin/env python3
"""Reading and writing the annotation workbooks, with Excel fidelity as the hard constraint.

Every write goes through the same path: refuse if Excel holds the file open, load with
`rich_text=True`, touch only the annotation cells, save to a temp file in the same directory,
convert the inline strings Excel dislikes into a shared-strings part, then `os.replace` over the
original. Column widths, fonts, alignment, freeze panes, zoom and every untouched cell survive
unchanged, which `tests/test_idiograph.py` checks cell by cell against an untouched copy.

The orange crux colour is theme 9, tint 0, the same value `gravity_build_annotated_xlsx.py` uses.
Do not approximate it with an RGB.
"""
from __future__ import annotations

import contextlib
import contextvars
import copy
import datetime as dt
import hashlib
import json
import math
import os
import re
import shutil
from pathlib import Path

import openpyxl
from openpyxl.cell.rich_text import CellRichText, TextBlock
from openpyxl.cell.text import InlineFont
from openpyxl.styles import Alignment, Font
from openpyxl.styles.cell_style import StyleArray
from openpyxl.styles.colors import Color
from openpyxl.utils import get_column_letter

import shared_strings  # noqa: F401  keeps a line feed a line feed on Windows, before any save
# the family's one error, by the name every module here has always caught it by (family/errors.py)
import i18n
import locks
from errors import WorkbookError  # noqa: F401

HEADER = ["Name", "Timestamp", "Experiential statements", "Transcript", "Exploratory notes", "Quote"]
# The quotes column was headed Key quotes until 22 October 2026, and Quote since (Adam's ruling). A
# workbook with either heading reads and writes the same, found by ROLE_TESTS, and the app never
# renames the heading of a workbook already there by itself. Since 23 October one op renames it on his
# word, `quote_heading`, through the API (the command line's quote-heading, MCP's quote_heading).
WIDTHS = {"A": 11.0, "B": 12.0, "C": 42.0, "D": 60.0, "E": 52.0, "F": 32.5}
# The analyst's notes on his own interventions. Never part of a new workbook: the column is added to
# a sheet the first time a note is written on it, in the first empty header cell after the last
# used one, which is G in the six columns above, and found by its header on every read after that.
NOTE_HEADER = "Interviewer notes"
NOTE_WIDTH = 42.0
# A raw source made from a Word table of transcript and notes carries them in columns of these
# headings, which no annotation role's test takes, so the source stays raw, and `create_from_source`
# puts each in its place (convert.RAW_NOTES and RAW_STATEMENTS, 19 October).
# Since 9 November 2026 (ayabuild12) a source's quotes come in a column of their own too, a line a quote, each
# paired with the statement on the same line by order (convert.RAW_QUOTES).
RAW_EXTRAS = {"notes": "en", "statements": "es", "quote lines": "kq"}
# Another speaker's turn, someone heard beside the interviewer and the participant (20 October),
# carries these words in a column of this heading, in the raw source and the annotated workbook alike
# (convert.CONTEXT). The app skips it when moving from passage to passage, and it can still be coded.
CONTEXT_HEADER = "Other speaker"
FONT = Font(name="Calibri", size=11)
HFONT = Font(name="Calibri", size=11, bold=True)
ALIGN = Alignment(wrap_text=True, vertical="top")
CRUX_THEME = 9
ORANGE = InlineFont(rFont="Calibri", sz=11, color=Color(theme=CRUX_THEME, tint=0.0))
PLAIN = InlineFont(rFont="Calibri", sz=11, color=Color(theme=1, tint=0.0))

ENTRY_SPLIT = re.compile(r"\n\s*\n")
ENTRY_JOIN = "\n\n"




# ---------------------------------------------------------------- lock guard

def lock_file(path: Path) -> Path:
    path = Path(path)
    return path.with_name("~$" + path.name)


def guard_lock(path: Path) -> None:
    lock = lock_file(path)
    if lock.exists():
        raise WorkbookError(i18n.t("server.open_excel_close_excel_first_2", name=Path(path).name))


# ------------------------------------------------------------ cell contents

def split_entries(value) -> list[str]:
    """A cell holds one or more statements, notes or quotes, separated by a blank line.

    Same convention as `ipa_annotation_audit.py`. Extra blank lines are tolerated.
    """
    if value is None:
        return []
    return [p.strip() for p in ENTRY_SPLIT.split(str(value)) if p.strip()]


def join_entries(entries) -> str | None:
    kept = [e.strip() for e in entries if e and e.strip()]
    return ENTRY_JOIN.join(kept) if kept else None


def field_to_lines(value) -> str:
    """Cell text for a textarea: one entry per line."""
    return "\n".join(split_entries(value))


def lines_to_field(text: str) -> str | None:
    """Textarea text back to a cell: one entry per line, blank lines ignored."""
    return join_entries((text or "").splitlines())


# A statement and its key quote are a pair, by place: the first quote in the key quotes cell is the
# first statement's, the second the second's. Once a turn has a quote, its cell holds one entry
# per statement, this mark for a statement with none, which every reader takes as empty, keeping
# its place. A turn with no quote at all keeps its cell empty.
NO_QUOTE = "(no quote)"


def no_quote(text) -> bool:
    """An entry that stands for no quote, spacing and case aside, as Excel may hold it too."""
    return " ".join(str(text or "").split()).lower() == NO_QUOTE


def quote_entries(value) -> list[str]:
    """The key quotes cell by place: every entry, "(no quote)" read as an empty one."""
    return ["" if no_quote(e) else e for e in split_entries(value)]


def one_entry(text) -> str:
    """A statement or a quote as one entry of its cell: stripped, with no blank line inside."""
    return ENTRY_SPLIT.sub("\n", str(text or "").strip())


def pair_entries(statements, quotes) -> list[dict]:
    """The pairs of a turn, by order: the first quote with the first statement. A statement past
    the last quote has an empty one, and a quote past the last statement is a pair of its own with
    an empty statement. A place past the statements with no quote in it is no pair."""
    statements, quotes = list(statements or []), list(quotes or [])
    out = [{"es": s, "kq": quotes[i] if i < len(quotes) else ""} for i, s in enumerate(statements)]
    out += [{"es": "", "kq": q} for q in quotes[len(statements):] if q]
    return out


def pairs_of(es_value, kq_value) -> list[dict]:
    """A turn's pairs from its two cells."""
    return pair_entries(split_entries(es_value), quote_entries(kq_value))


def unpaired(es_value, kq_value) -> bool:
    """A turn whose quotes are not one a statement: at least one quote, and a count of entries in
    its key quotes cell that differs from its statements'. Such a turn pairs by order on screen
    and is listed as Quotes to pair until it is saved paired."""
    places = quote_entries(kq_value)
    return any(places) and len(places) != len(split_entries(es_value))


def passage_version(es_value, en_value, kq_value) -> str:
    """What a passage's three cells hold, as a short hash a save carries back, so a save over a
    passage changed since the page or an agent read it can be refused (18 October). The entries are
    hashed, never the spacing, so a cell Excel spelled otherwise reads the same."""
    held = [split_entries(es_value), split_entries(en_value), quote_entries(kq_value)]
    return hashlib.sha1(json.dumps(held, ensure_ascii=False).encode("utf-8")).hexdigest()[:12]


# ------------------------------------------------- a quote across her passages

# One quote may run on from its statement's passage into the same speaker's passages next to it (quotespan,
# Adam, 30 October 2026: "Adjacent passages may combine into one block quote with a timecode range"). It is
# still one quote, kept in its statement's own row as the words alone, the pieces in transcript order joined
# with an ellipsis as pieces of one passage always were, so an older Idiograph shows the same words. Nothing
# else is stored: which passages a quote takes in is found from its words each time it is read, as where a
# quote stands in its one passage always was (`quote_reach`), so a passage corrected, trimmed or replaced
# under a piece is followed as a quote of one passage is. Two passages are adjacent when they are the same
# speaker's, on the same sheet, with nothing but the interviewer's turns between, so no participant passage,
# hers or another speaker's, is ever skipped. The page holds the same rule in family/static/quote.js.
QUOTE_CUT = re.compile(r"\s*(?:…|\.\.\.|\[[^\]]*\])\s*")
DOUBLE_MARKS = "\"“”"
SINGLE_MARKS = "'‘’"
# the two timecodes of a quote that takes in more than one passage, "25:51–26:50", as the thesis writes them
RANGE_DASH = "–"


def quote_pieces(quote) -> list[str]:
    """A quote's pieces as the page finds them (`quoteSpans` in quote.js): the inverted commas round the whole
    set aside, cut at an ellipsis, three dots or a clarifying insert in square brackets, a piece with no letter
    or digit dropped."""
    body = str(quote or "").strip()
    if not body or no_quote(body):
        return []
    if body[0] in DOUBLE_MARKS or body[-1] in DOUBLE_MARKS:
        body = body.lstrip(DOUBLE_MARKS).rstrip(DOUBLE_MARKS)
    elif len(body) > 1 and body[0] in SINGLE_MARKS and body[-1] in SINGLE_MARKS:
        body = body[1:-1]
    return [p.strip() for p in QUOTE_CUT.split(body) if any(ch.isalnum() for ch in p)]


def _fold(ch: str) -> str:
    if ch in "‘’":
        return "'"
    if ch in "“”":
        return '"'
    low = ch.lower()
    return low if len(low) == 1 else ch


def _flat(text) -> tuple[str, list[int]]:
    """A passage with each run of spaces one space and every character folded, and where each character of
    that stands in the passage itself."""
    flat, at = [], []
    for i, ch in enumerate(str(text or "")):
        if ch.isspace():
            if flat and flat[-1] == " ":
                continue
            flat.append(" ")
        else:
            flat.append(_fold(ch))
        at.append(i)
    return "".join(flat), at


def quote_reach(quote, texts, home: int = 0) -> list[tuple[int, int, int]]:
    """Where a quote stands among a speaker's adjacent passages, `texts` in transcript order and `home` the
    place of its statement's own passage among them: one (passage, start, end) a piece, or [] when its words
    are not there. Each piece is found after the one before, in the same passage or the next, so the passages
    a quote takes in run unbroken, each holding at least one piece, and its own passage always among them. Its
    own passage is tried alone first, as a quote of one passage was always found, then running on into the
    passages after it, then starting in those before. The spaces, the case and the curly marks are set aside as
    the page sets them aside."""
    pieces = quote_pieces(quote)
    texts = list(texts or [])
    if not pieces or not 0 <= home < len(texts):
        return []
    wants = ["".join(_fold(c) for c in " ".join(p.split())) for p in pieces]
    flats: dict[int, tuple[str, list[int]]] = {}
    failed: set = set()

    def flat(t: int) -> tuple[str, list[int]]:
        if t not in flats:
            flats[t] = _flat(texts[t])
        return flats[t]

    def find(i: int, t: int, start: int):
        if i == len(wants):
            return [] if t >= home else None
        if (i, t, start) in failed:
            return None
        for turn, frm in ((t, start), (t + 1, 0)):
            # a new passage only once this one holds a piece, and never past the texts
            if (turn != t and i == 0) or turn >= len(texts):
                continue
            words, at = flat(turn)
            k = words.find(wants[i], frm)
            if k < 0:
                continue
            rest = find(i + 1, turn, k + len(wants[i]))
            if rest is not None:
                return [(turn, at[k], at[k + len(wants[i]) - 1] + 1)] + rest
        failed.add((i, t, start))
        return None

    # each passage before her own holds a piece at least, so a quote of n pieces starts no further back than n - 1
    for first in range(home, max(-1, home - len(pieces)), -1):
        found = find(0, first, 0)
        if found:
            return found
    return []


def interviewer_name() -> str:
    """The interviewer's name as Settings holds it, the speaker whose turns are context, or empty with no
    settings to read."""
    try:
        import server as srv
        return str(srv.config().get("interviewer") or "").strip()
    except Exception:  # noqa: BLE001  a read with no server set up has no interviewer
        return ""


def speakers_run(rows: list[dict], i: int, interviewer: str, most: int) -> tuple[list[int], int]:
    """The passages a quote of `rows[i]` may take in, as indexes into `rows`, a sheet's rows in order each with
    its `name` and, for another speaker's turn the workbook marks, `context`, and the place of `i` among them:
    the same speaker's passages either side, up to `most` each way, adjacent with nothing but the interviewer's
    turns, or rows with no speaker, between."""
    who = _norm(interviewer)
    me = _norm(rows[i].get("name"))
    if not me or me == who or rows[i].get("context"):
        return [i], 0
    before, after = [], []
    for step, into in ((-1, before), (1, after)):
        k = i + step
        while 0 <= k < len(rows) and len(into) < most:
            name = _norm(rows[k].get("name"))
            if name and name != who:
                if name != me or rows[k].get("context"):
                    break
                into.append(k)
            k += step
    return before[::-1] + [i] + after, len(before)


def quote_turns(rows: list[dict], i: int, quote, interviewer: str | None = None) -> list[tuple[int, int, int]]:
    """Where the quote of the statement on `rows[i]` stands: one (row index, start, end) a piece, in its own
    passage and the same speaker's adjacent ones (see `quote_reach`), [] when its words are not there.
    `interviewer` is read from Settings when not given, and only when the quote is not in its own passage."""
    pieces = quote_pieces(quote)
    if not pieces:
        return []
    own = quote_reach(quote, [rows[i].get("text") or ""], 0)
    if own or len(pieces) < 2:
        return [(i, s, e) for _, s, e in own]
    run, home = speakers_run(rows, i, interviewer_name() if interviewer is None else interviewer, len(pieces) - 1)
    return [(run[t], s, e) for t, s, e in quote_reach(quote, [rows[k].get("text") or "" for k in run], home)]


def time_span(first: int | None, last: int | None, form: str | None = None) -> str:
    """The timecode of a quote that takes in more than one passage, from the first passage's to the last's,
    "25:51–26:50", one time where the two read the same or one is missing."""
    times = [t for t in (timecode(first, form), timecode(last, form)) if t]
    if len(times) == 2 and times[0] == times[1]:
        times = times[:1]
    return RANGE_DASH.join(times)




class StaleTurn(WorkbookError):
    """A save over a passage that has changed since it was read. It carries the passage as it now
    reads, for the page to show beside what was typed."""

    def __init__(self, now: dict):
        super().__init__(i18n.t("server.passage_changed_since_page_loaded"))
        self.now = now


def pairs_to_cells(pairs) -> tuple[str | None, str | None]:
    """Pairs back to the two cells. The statements go in order. Once any quote is there the key
    quotes cell holds one entry a statement, "(no quote)" for one with none, and a quote whose
    statement is empty is kept after them, so nothing written is lost and no other pair moves. With
    no quote at all the key quotes cell is empty."""
    kept, loose = [], []
    for pair in pairs or []:
        if isinstance(pair, dict):
            statement, quote = pair.get("es"), pair.get("kq")
        else:
            statement, quote = pair
        statement, quote = one_entry(statement), one_entry(quote)
        if no_quote(quote):
            quote = ""
        if statement:
            kept.append((statement, quote))
        elif quote:
            loose.append(quote)
    es = join_entries([s for s, _ in kept])
    if not loose and not any(q for _, q in kept):
        return es, None
    return es, ENTRY_JOIN.join([q or NO_QUOTE for _, q in kept] + loose)


# ------------------------------------------------------------------- columns

ROLE_TESTS = {
    "name": lambda h: h in ("name", "speaker"),
    "ts": lambda h: h in ("timestamp", "time", "timecode"),
    "es": lambda h: "experien" in h and "state" in h,
    "transcript": lambda h: h in ("transcript", "text") or h.startswith("transcript"),
    "en": lambda h: "explor" in h,
    "kq": lambda h: "key quote" in h or h in ("quote", "quotes"),
    "note": lambda h: "interviewer note" in h,
    "ctx": lambda h: h == "other speaker",
}


def header_row(ws) -> list:
    """The first row's values. Works on a read-only worksheet as well as a normal one."""
    try:
        return list(next(ws.iter_rows(min_row=1, max_row=1, values_only=True)))
    except StopIteration:
        return []


def detect_columns(ws) -> dict[str, int]:
    """Map role to 1-based column by reading the header row, so other layouts can be added later."""
    found: dict[str, int] = {}
    for c, raw in enumerate(header_row(ws)[:12], start=1):
        if raw is None:
            continue
        h = str(raw).strip().lower()
        for role, test in ROLE_TESTS.items():
            if role not in found and test(h):
                found[role] = c
                break
    return found


def is_raw_source(cols: dict[str, int]) -> bool:
    """A raw transcript workbook: speaker, timestamp and transcript, with no annotation columns."""
    return {"name", "ts", "transcript"} <= set(cols) and not ({"es", "en", "kq"} & set(cols))


# --------------------------------------------------------------- timestamps

def ts_seconds(value) -> int | None:
    if isinstance(value, dt.time):
        return value.hour * 3600 + value.minute * 60 + value.second
    if isinstance(value, dt.datetime):
        return value.hour * 3600 + value.minute * 60 + value.second
    if isinstance(value, (int, float)):           # Excel serial fraction of a day
        return int(round(float(value) * 86400))
    if isinstance(value, str):
        parts = value.strip().split(":")
        try:
            nums = [int(p) for p in parts]
        except ValueError:
            return None
        if len(nums) == 3:
            return nums[0] * 3600 + nums[1] * 60 + nums[2]
        if len(nums) == 2:
            return nums[0] * 60 + nums[1]
    return None


# How a project writes its timecodes (Adam, 28 October), each named by itself at an hour and a quarter:
# 75:12, the hours folded into the minutes, 1:15:12, the hours once past the hour, and 01:15:12, the hours
# always. Kept as `timecodes` in the project file, a project with none reading 1:15:12. Every timecode the
# app shows follows it: the transcript, the player, the boards, print, Word and the command line's turn
# lines. The statements CSV, the notes export, the workbook's own cell, QDPX and --json keep their own.
TIMECODES = ("75:12", "1:15:12", "01:15:12")
TIMECODES_DEFAULT = "1:15:12"


def timecodes_of(value) -> str:
    """A project file's `timecodes` as one of the three, 1:15:12 for anything else or none."""
    return value if value in TIMECODES else TIMECODES_DEFAULT


def timecode(seconds: int | None, form: str | None = TIMECODES_DEFAULT) -> str:
    """`seconds` written the way `form` says, one of TIMECODES, an empty string for no time. The minutes
    and the seconds always take two digits, 00:05 at five seconds, and past ten hours the hours take as
    many as they need."""
    if seconds is None:
        return ""
    t = max(0, int(seconds))
    form = timecodes_of(form)
    if form == "75:12":
        return f"{t // 60:02d}:{t % 60:02d}"
    rest = f"{(t % 3600) // 60:02d}:{t % 60:02d}"
    if form == "01:15:12":
        return f"{t // 3600:02d}:{rest}"
    return f"{t // 3600}:{rest}" if t >= 3600 else rest


def timecodes_at(root) -> str:
    """The timecodes of the project at `root`, its project file's `timecodes`, 1:15:12 with no file."""
    try:
        import server as srv
        data = json.loads((Path(root) / srv.PROJECT_FILE).read_text(encoding="utf-8"))
    except (ImportError, OSError, ValueError, TypeError):
        return TIMECODES_DEFAULT
    return timecodes_of(data.get("timecodes") if isinstance(data, dict) else None)


def timecodes_for(path) -> str:
    """The timecodes of the project a workbook belongs to (see `server.project_of`), 1:15:12 for a path
    under no project."""
    try:
        import server as srv
        root = srv.project_of(Path(path))
    except Exception:  # noqa: BLE001  a read with no server set up reads the default
        return TIMECODES_DEFAULT
    return timecodes_at(root) if root is not None else TIMECODES_DEFAULT


def hhmmss(seconds: int | None) -> str:
    """The export convention, matching the reference CSV."""
    if seconds is None:
        return ""
    return f"{seconds // 3600:02d}:{(seconds % 3600) // 60:02d}:{seconds % 60:02d}"


TIMECODE = re.compile(r"(\d{1,4}):(\d{2})(?::(\d{2}))?")


def parse_timecode(value) -> int | None:
    """A timecode typed into the turn editor, `MM:SS` or `H:MM:SS`, as seconds.

    `MM:SS` may carry the hours flattened into the minutes, which is how a project kept at 75:12 prefills
    the box past the hour, so `75:10` reads as an hour and a quarter. Anything else is None.
    """
    if value is None:
        return None
    m = TIMECODE.fullmatch(str(value).strip())
    if not m:
        return None
    if m.group(3) is None:
        minutes, seconds = int(m.group(1)), int(m.group(2))
        return None if seconds >= 60 else minutes * 60 + seconds
    hours, minutes, seconds = int(m.group(1)), int(m.group(2)), int(m.group(3))
    if minutes >= 60 or seconds >= 60:
        return None
    return hours * 3600 + minutes * 60 + seconds


def timecode_like(template, seconds: int):
    """`seconds` in the representation `template` holds, so a new timecode sits among its
    neighbours the way they were written: a `datetime.time`, a datetime, a fraction of a day, or a
    string of the same shape. `ts_seconds` reads every one of them back."""
    seconds = max(0, int(seconds))
    hours, minutes, secs = seconds // 3600, (seconds % 3600) // 60, seconds % 60
    if isinstance(template, dt.datetime):
        return template.replace(hour=min(hours, 23), minute=minutes, second=secs, microsecond=0)
    if isinstance(template, (int, float)) and not isinstance(template, bool):
        return seconds / 86400
    if isinstance(template, str):
        parts = template.strip().split(":")
        if len(parts) == 2:
            return f"{seconds // 60:02d}:{secs:02d}"
        if len(parts) == 3:
            return f"{hours:0{max(1, len(parts[0]))}d}:{minutes:02d}:{secs:02d}"
    return dt.time(min(hours, 23), minutes, secs)


def _write_timecode(ws, cols: dict[str, int], row: int, seconds: int, template=None) -> None:
    """Write a timecode into one row, in the form that row, or failing that its neighbours, uses."""
    cell = ws.cell(row, cols["ts"])
    if template is None:
        for r in (row, row - 1, row + 1):
            if 2 <= r <= ws.max_row and ws.cell(r, cols["ts"]).value is not None:
                template = ws.cell(r, cols["ts"]).value
                break
    cell.value = timecode_like(template, seconds)


# --------------------------------------------------------------- rich text

def font_key(font: InlineFont | None):
    if font is None:
        return None
    c = font.color
    return (
        getattr(c, "theme", None) if c is not None else None,
        getattr(c, "tint", None) if c is not None else None,
        getattr(c, "rgb", None) if c is not None and c.type == "rgb" else None,
        font.rFont, font.sz, font.b, font.i, font.u, font.strike,
    )


def is_crux_font(font: InlineFont | None) -> bool:
    if font is None or font.color is None:
        return False
    return getattr(font.color, "theme", None) == CRUX_THEME


def cell_runs(value) -> list[dict]:
    """A transcript cell as a list of {text, crux} runs, in order."""
    if value is None:
        return []
    if not isinstance(value, CellRichText):
        return [{"text": str(value), "crux": False}]
    runs = []
    for block in value:
        if isinstance(block, TextBlock):
            runs.append({"text": block.text, "crux": is_crux_font(block.font)})
        else:
            runs.append({"text": str(block), "crux": False})
    return _coalesce_display(runs)


def _coalesce_display(runs: list[dict]) -> list[dict]:
    out: list[dict] = []
    for r in runs:
        if not r["text"]:
            continue
        if out and out[-1]["crux"] == r["crux"]:
            out[-1]["text"] += r["text"]
        else:
            out.append(dict(r))
    return out


def plain_text(value) -> str:
    if value is None:
        return ""
    if isinstance(value, CellRichText):
        return "".join(b.text if isinstance(b, TextBlock) else str(b) for b in value)
    return str(value)


def _char_fonts(value) -> tuple[str, list[InlineFont | None]]:
    """Explode a cell into its characters and the font carried by each, so a span can be re-fonted
    without disturbing any other run."""
    text = plain_text(value)
    fonts: list[InlineFont | None] = []
    if isinstance(value, CellRichText):
        for block in value:
            if isinstance(block, TextBlock):
                fonts.extend([block.font] * len(block.text))
            else:
                fonts.extend([None] * len(str(block)))
    else:
        fonts = [None] * len(text)
    return text, fonts


def _is_unremarkable(font: InlineFont | None) -> bool:
    """A run carrying no formatting worth keeping: the default body text of the cell."""
    if font is None:
        return True
    if font.b or font.i or font.u or font.strike:
        return False
    c = font.color
    return c is None or getattr(c, "theme", None) == 1


def _rebuild(text: str, fonts: list[InlineFont | None]):
    """Characters and fonts back into a cell value. A cell left with nothing but body text goes
    back to a plain string, which is what an untouched transcript cell looks like."""
    if all(_is_unremarkable(f) for f in fonts):
        return text
    blocks: list = []
    start = 0
    for i in range(1, len(text) + 1):
        if i == len(text) or font_key(fonts[i]) != font_key(fonts[start]):
            chunk, font = text[start:i], fonts[start]
            blocks.append(TextBlock(font, chunk) if font is not None else chunk)
            start = i
    return CellRichText(*blocks)


def apply_crux(value, start: int, end: int, remove: bool):
    """Mark or unmark [start, end) of a transcript cell. Returns the new cell value."""
    text, fonts = _char_fonts(value)
    if not 0 <= start < end <= len(text):
        raise WorkbookError(i18n.t("server.selection_inside_passage_select_phrase"))
    if remove:
        # Take the font of whatever sits next to the mark, so clearing it folds the span back into
        # the run it was carved out of rather than leaving a separate block behind.
        before = fonts[start - 1] if start > 0 and not is_crux_font(fonts[start - 1]) else None
        after = fonts[end] if end < len(fonts) and not is_crux_font(fonts[end]) else None
        if before is not None:
            replacement = before
        elif after is not None:
            replacement = after
        elif (start > 0 and not is_crux_font(fonts[start - 1])) or (end < len(fonts) and not is_crux_font(fonts[end])):
            replacement = None                      # the neighbour is plain text with no run of its own
        else:
            replacement = PLAIN
        for i in range(start, end):
            fonts[i] = replacement
    else:
        for i in range(start, end):
            fonts[i] = ORANGE
    return _rebuild(text, fonts)


def crux_marks(value) -> list[tuple[str, InlineFont | None]]:
    """Every orange stretch of a cell, with the font it carries. Adjacent orange runs read as one,
    the way `cell_runs` reports them."""
    text, fonts = _char_fonts(value)
    marks: list[tuple[str, InlineFont | None]] = []
    i = 0
    while i < len(text):
        if not is_crux_font(fonts[i]):
            i += 1
            continue
        j = i
        while j < len(text) and is_crux_font(fonts[j]):
            j += 1
        marks.append((text[i:j], fonts[i]))
        i = j
    return marks


def rekey_crux(old_value, new_text: str) -> tuple[object, list[str]]:
    """Carry a cell's orange runs onto rewritten text, by phrase.

    A mark whose phrase still occurs keeps its highlight at the first occurrence in the new text,
    in the font it already carried, so a run written by the build script and one written by `h`
    both come through as they were. A mark whose phrase has gone is dropped and named, so the
    interface can say which. Everything between the marks is the cell's body text: the text has
    been rewritten, so there is no character-by-character run to keep it on.

    Nothing about the cell itself is decided here. The caller keeps the cell, its style and its
    fill, and takes back only the value.
    """
    fonts: list[InlineFont | None] = [None] * len(new_text)
    dropped: list[str] = []
    for phrase, font in crux_marks(old_value):
        at = new_text.find(phrase)
        if at < 0:
            dropped.append(phrase)
            continue
        for i in range(at, at + len(phrase)):
            fonts[i] = font or ORANGE
    return _rebuild(new_text, fonts), dropped


def crux_span_at(value, start: int, end: int) -> tuple[int, int] | None:
    """The full orange run covering the selection, or None when the selection is not all orange."""
    text, fonts = _char_fonts(value)
    if not 0 <= start < end <= len(text):
        return None
    if not all(is_crux_font(f) for f in fonts[start:end]):
        return None
    a, b = start, end
    while a > 0 and is_crux_font(fonts[a - 1]):
        a -= 1
    while b < len(fonts) and is_crux_font(fonts[b]):
        b += 1
    return a, b


# ------------------------------------------------------------------ reading

def read_case(path: Path, form: str | None = None) -> dict:
    """The whole workbook as the interface needs it: sheets, rows, runs, existing annotations, each
    row's timecode written as `form` says, by default as its project's timecodes say (see `timecode`)."""
    path = Path(path)
    form = form or timecodes_for(path)
    guard_lock(path)
    wb = openpyxl.load_workbook(path, rich_text=True)
    sheets = []
    for ws in wb.worksheets:
        cols = detect_columns(ws)
        if not {"name", "ts", "transcript"} <= set(cols):
            continue
        rows = []
        for r in range(2, ws.max_row + 1):
            name = ws.cell(r, cols["name"]).value
            tval = ws.cell(r, cols["ts"]).value
            dval = ws.cell(r, cols["transcript"]).value
            if name is None and tval is None and dval is None:
                continue
            es_value = ws.cell(r, cols["es"]).value if "es" in cols else None
            kq_value = ws.cell(r, cols["kq"]).value if "kq" in cols else None
            rows.append({
                "sheet": ws.title,
                "row": r,
                "name": (str(name).strip() if name is not None else ""),
                "seconds": ts_seconds(tval),
                "time": timecode(ts_seconds(tval), form),
                "runs": cell_runs(dval),
                "text": plain_text(dval),
                "es": field_to_lines(es_value),
                "en": field_to_lines(ws.cell(r, cols["en"]).value) if "en" in cols else "",
                # the quotes themselves, "(no quote)" left out, and the pairs by place beside them
                "kq": "\n".join(q for q in quote_entries(kq_value) if q),
                "pairs": pairs_of(es_value, kq_value),
                "unpaired": unpaired(es_value, kq_value),
                # what the three cells hold now, which a save carries back (see `passage_version`)
                "v": passage_version(es_value, ws.cell(r, cols["en"]).value if "en" in cols else None, kq_value),
                # a sheet with no Interviewer notes column reads every note as empty
                "note": field_to_lines(ws.cell(r, cols["note"]).value) if "note" in cols else "",
                # another speaker's turn, skipped when moving from passage to passage (20 October)
                "context": bool("ctx" in cols and str(ws.cell(r, cols["ctx"]).value or "").strip()),
            })
        sheets.append({"name": ws.title, "columns": cols, "rows": rows})
    wb.close()
    return {"path": str(path), "name": path.stem, "sheets": sheets}


# ------------------------------------------------------------------ writing

# The files this process last wrote, each by its path with its modification time after the write (20
# October): the server asks it to tell a change from another of its own windows, which an open board takes
# by itself, from a change made outside the app, by an AI agent's command line or by hand on the file,
# which a board says with Changes made elsewhere. The command line runs in a process of its own, so what it
# writes is never noted here. The server keeps the list in the app's own state across a restart, through
# WRITTEN_HOOK, called after each note, and `still_written` when it starts.
WRITTEN: dict[str, int] = {}
WRITTEN_HOOK = None
# the most files the list keeps, the oldest noted dropped first
WRITTEN_MOST = 500


def note_written(path) -> None:
    try:
        key = str(Path(path).resolve())
        when = Path(path).stat().st_mtime_ns
    except OSError:
        return
    WRITTEN.pop(key, None)
    WRITTEN[key] = when
    while len(WRITTEN) > WRITTEN_MOST:
        WRITTEN.pop(next(iter(WRITTEN)))
    if WRITTEN_HOOK is not None:
        try:
            WRITTEN_HOOK(dict(WRITTEN))
        except Exception:
            pass


def still_written(saved) -> dict[str, int]:
    """Of a list kept from an earlier run, the files that still stand as that run last wrote them. A file
    changed since, or gone, is left out, so a change made while the app was closed is still one from outside."""
    out: dict[str, int] = {}
    if not isinstance(saved, dict):
        return out
    for key, when in saved.items():
        if not isinstance(key, str) or not isinstance(when, int) or isinstance(when, bool):
            continue
        try:
            if Path(key).stat().st_mtime_ns == when:
                out[key] = when
        except OSError:
            continue
    return out


def written_here(path) -> bool:
    """True when the file stands as this process last wrote it, False when it has changed since or this
    process never wrote it."""
    try:
        return WRITTEN.get(str(Path(path).resolve())) == Path(path).stat().st_mtime_ns
    except OSError:
        return False


def _atomic_save(wb, path: Path) -> None:
    boards_pass_check(path)
    tmp = path.with_name(f".{path.stem}.idiograph.tmp.xlsx")
    try:
        wb.save(tmp)
        from shared_strings import convert
        convert(tmp)
        os.replace(tmp, path)
        note_written(path)
    finally:
        if tmp.exists():
            tmp.unlink()


def save_turn(path: Path, sheet: str, row: int, es: str, en: str, kq: str, pairs=None,
              was: str | None = None) -> dict:
    """Write the three annotation cells of one row. Nothing else in the workbook is touched.

    With `pairs`, each a statement and its key quote, the statements and the quotes are written
    from them as `pairs_to_cells` sets them out, and `es` and `kq` are not read. The answer then
    carries the turn's pairs as they now read and whether its quotes are still to pair, and the
    passage's version after the save, `v`.

    `was` is the version the writer last read (see `passage_version`). When the cells hold another
    now and the save would change any of them, it raises `StaleTurn` with nothing written, so a
    second window or an agent never writes over words it has not seen. A save that changes nothing
    is answered as ever."""
    path = Path(path)
    guard_lock(path)
    wb = openpyxl.load_workbook(path, rich_text=True)
    if sheet not in wb.sheetnames:
        wb.close()
        raise WorkbookError(i18n.t("server.sheet_called", sheet=sheet, name=path.name))
    ws = wb[sheet]
    cols = detect_columns(ws)
    cells = {"en": lines_to_field(en) if en is not None else None}
    if pairs is not None:
        cells["es"], cells["kq"] = pairs_to_cells(pairs)
        given = ("es", "en", "kq") if en is not None else ("es", "kq")
    else:
        cells["es"] = lines_to_field(es) if es is not None else None
        cells["kq"] = lines_to_field(kq) if kq is not None else None
        given = [role for role, text in (("es", es), ("en", en), ("kq", kq)) if text is not None]
    held = lambda role: ws.cell(row, cols[role]).value if role in cols else None
    written, todo = {}, {}
    for role in ("es", "en", "kq"):
        if role not in cols or role not in given:
            continue
        cell = ws.cell(row, cols[role])
        value = cells[role]
        written[role] = value or ""
        # A cell whose entries are the same is left exactly as it is, spacing and all, so
        # revisiting a turn and moving on writes nothing at all. "(no quote)" reads the same
        # however Excel spelled it.
        same = (quote_entries(cell.value) == quote_entries(value) if role == "kq"
                else split_entries(cell.value) == split_entries(value))
        if not same:
            todo[role] = value
    if todo and was is not None and passage_version(held("es"), held("en"), held("kq")) != str(was):
        now = turn_now(held("es"), held("en"), held("kq"))
        wb.close()
        raise StaleTurn(dict(now, sheet=sheet, row=row))
    # the statements as they read before, when the save changes them, for the boards' History (histreplace)
    es_was = split_entries(held("es")) if "es" in todo else None
    for role, value in todo.items():
        ws.cell(row, cols[role]).value = value
    changed = bool(todo)
    if changed:
        _atomic_save(wb, path)
    es_now, en_now, kq_now = held("es"), held("en"), held("kq")
    wb.close()
    out = {"row": row, "sheet": sheet, "written": written, "changed": changed,
           "pairs": pairs_of(es_now, kq_now), "unpaired": unpaired(es_now, kq_now),
           "v": passage_version(es_now, en_now, kq_now)}
    if es_was is not None:
        out["statements"] = {"before": es_was, "after": split_entries(es_now)}
    return out


def turn_now(es_value, en_value, kq_value) -> dict:
    """A passage's three cells as the turn screen reads them, with its version."""
    return {"es": field_to_lines(es_value), "en": field_to_lines(en_value),
            "kq": "\n".join(q for q in quote_entries(kq_value) if q),
            "pairs": pairs_of(es_value, kq_value), "unpaired": unpaired(es_value, kq_value),
            "v": passage_version(es_value, en_value, kq_value)}


def save_crux(path: Path, sheet: str, row: int, start: int, end: int, selection: str,
              op: str | None = None) -> dict:
    """Mark the selection orange, clear the mark, or toggle between the two.

    Three calls, one path. `op="add"` marks exactly the selection, so a selection that overlaps an
    orange run or spans it ends as one longer run. `op="remove"` clears exactly the selection, so a
    selection inside a run shortens it at either end and splits it into two runs when it sits in
    the middle. With no `op` the call toggles the way it always did: a selection that is orange all
    through clears the whole run it belongs to, anything else is marked.

    The storage is the same in all three: the orange is a font run on the characters, theme 9, and
    what is cleared takes the font of whatever it sat next to. No cell ever gains a fill.
    """
    if op not in (None, "add", "remove"):
        raise WorkbookError(i18n.t("server.highlight_added_removed_nothing_else"))
    path = Path(path)
    guard_lock(path)
    wb = openpyxl.load_workbook(path, rich_text=True)
    if sheet not in wb.sheetnames:
        wb.close()
        raise WorkbookError(i18n.t("server.sheet_called", sheet=sheet, name=path.name))
    ws = wb[sheet]
    cols = detect_columns(ws)
    cell = ws.cell(row, cols["transcript"])
    text = plain_text(cell.value)
    if selection is not None and text[start:end] != selection:
        found = text.find(selection) if selection else -1
        if found < 0:
            wb.close()
            raise WorkbookError(i18n.t("server.selection_does_match_passage_s"))
        start, end = found, found + len(selection)
    if op is None:
        span = crux_span_at(cell.value, start, end)
        removing = span is not None
        if removing:
            start, end = span
    else:
        removing = op == "remove"
    cell.value = apply_crux(cell.value, start, end, remove=removing)
    _atomic_save(wb, path)
    result = {"row": row, "sheet": sheet, "removed": removing,
              "op": "remove" if removing else "add", "runs": cell_runs(cell.value)}
    wb.close()
    return result


def rewrite_transcript(cell, new: str) -> list[str]:
    """Write new text into one transcript cell, the one cell write a correction and a replace share.

    The highlights are found again by phrase (`rekey_crux`), and only the value changes, so the cell
    keeps its font, its alignment and its number format and never gains a fill. Answers with the
    phrases of the highlights dropped, the ones whose words have gone.
    """
    value, dropped = rekey_crux(cell.value, new)
    cell.value = value
    return dropped


def edit_turn(path: Path, sheet: str, row: int, text: str, typed: str | None = None, dry: bool = False,
              form: str | None = None) -> dict:
    """Rewrite one row's transcript text, keeping the cell and re-keying its highlights.

    The transcript is a transcript and carries slips. This writes the corrected text into the same
    cell, which keeps its font, its alignment and its number format, and never gains a fill. The
    orange runs are found again by phrase, so a highlight whose words survive the correction comes
    back at its new position and one whose words have gone is dropped and named in the answer.

    `typed` is a timecode, optional, `MM:SS` or `H:MM:SS`, and one that differs from the cell's is
    written into the timestamp cell in the representation that cell already holds. One that cannot
    be read is refused before anything is written. Nothing else is touched: the statements, the
    notes, the key quotes and the speaker are left exactly as they were, and a text and a timecode
    that have not changed write nothing. With `dry` everything is read and checked as for a write, and
    nothing is saved, so an agent's dry run answers what the write would (26 October). The answer's
    times are written as `form` says, by default as the project's timecodes say.
    """
    path = Path(path)
    form = form or timecodes_for(path)
    guard_lock(path)
    new = "" if text is None else str(text)
    if not new.strip():
        raise WorkbookError(i18n.t("server.passage_cannot_left_text_cancel"))
    wanted = None
    if typed is not None and str(typed).strip():
        wanted = parse_timecode(typed)
        if wanted is None:
            raise WorkbookError(i18n.t("server.not_a_timecode", timecode=str(typed).strip()))
    wb = openpyxl.load_workbook(path, rich_text=True)
    try:
        if sheet not in wb.sheetnames:
            raise WorkbookError(i18n.t("server.sheet_called", sheet=sheet, name=path.name))
        ws = wb[sheet]
        cols = detect_columns(ws)
        if "transcript" not in cols:
            raise WorkbookError(i18n.t("server.transcript_column", sheet=sheet))
        row = int(row)
        if row < 2:
            raise WorkbookError(i18n.t("server.header_row_never_edited"))
        cell = ws.cell(row, cols["transcript"])
        old = plain_text(cell.value)
        dropped: list[str] = []
        text_changed = new != old
        if text_changed:
            dropped = rewrite_transcript(cell, new)
        old_seconds = ts_seconds(ws.cell(row, cols["ts"]).value) if "ts" in cols else None
        time_changed = wanted is not None and "ts" in cols and wanted != old_seconds
        if time_changed:
            _write_timecode(ws, cols, row, wanted)
        changed = text_changed or time_changed
        if changed and not dry:
            _atomic_save(wb, path)
        seconds = ts_seconds(ws.cell(row, cols["ts"]).value) if "ts" in cols else None
        return {"sheet": sheet, "row": row, "old": old, "changed": changed,
                "text": plain_text(cell.value), "runs": cell_runs(cell.value), "dropped": dropped,
                "text_changed": text_changed, "time_changed": time_changed,
                "old_time": timecode(old_seconds, form), "seconds": seconds, "time": timecode(seconds, form)}
    finally:
        wb.close()


# ------------------------------------------------------------ find and replace



def _wordy(ch: str) -> bool:
    """A letter or a digit, which a whole word may not run into."""
    return ch.isalnum()


def find_spans(text, find, word: bool = True, case: bool = False) -> list[tuple[int, int]]:
    """Every occurrence of `find` in `text`, as (start, end), left to right and never overlapping.

    The match is literal, never a pattern. With `case` off a capital and a small letter match each
    other. With `word` on an occurrence may not run into a letter or a digit at an end that is a
    letter or a digit itself, so "so" never matches inside "also" or "sofa" and does match "so,"
    and "So", and "so " still matches before the next word. `findSpans` in static/app.js keeps the
    same rules, so the count on the page and the replace here never disagree.
    """
    text = "" if text is None else str(text)
    find = "" if find is None else str(find)
    if not find or not text:
        return []
    pattern = re.compile(re.escape(find), 0 if case else re.IGNORECASE)
    spans: list[tuple[int, int]] = []
    pos = 0
    while pos <= len(text):
        m = pattern.search(text, pos)
        if not m:
            break
        start, end = m.span()
        if word and ((start > 0 and _wordy(text[start]) and _wordy(text[start - 1]))
                     or (end < len(text) and _wordy(text[end - 1]) and _wordy(text[end]))):
            pos = start + 1
            continue
        spans.append((start, end))
        pos = end
    return spans


def keep_case(found: str, replace: str) -> str:
    """Replace with in the case of what it replaces, for a find with Match case off: a word found
    in capitals is replaced in capitals, one found with a capital first letter gets a capital first
    letter, and one found in small letters is written as typed (item 139)."""
    letters = [c for c in found if c.isalpha()]
    if not letters or not replace:
        return replace
    if len(letters) > 1 and all(c.isupper() for c in letters):
        return replace.upper()
    if letters[0].isupper():
        return replace[0].upper() + replace[1:]
    return replace


def _splice(text: str, spans, replace: str, keep: bool = False) -> str:
    """The text with every span in it replaced, the spans in order and never overlapping. With
    `keep` each replacement takes the case of what it replaces (see `keep_case`)."""
    out, at = [], 0
    for start, end in spans:
        out.append(text[at:start])
        out.append(keep_case(text[start:end], replace) if keep else replace)
        at = end
    out.append(text[at:])
    return "".join(out)


FONT_FIELDS = ("rFont", "charset", "family", "b", "i", "strike", "outline", "shadow", "condense",
               "extend", "sz", "u", "vertAlign", "scheme")


def font_wire(font: InlineFont | None) -> dict | None:
    """A run's font as plain values, for a JSON record to carry and `font_from` to rebuild."""
    if font is None:
        return None
    out = {k: getattr(font, k) for k in FONT_FIELDS if getattr(font, k, None) is not None}
    c = font.color
    if c is not None:
        if c.type == "rgb":
            out["rgb"] = c.rgb
        elif getattr(c, "theme", None) is not None:
            out["theme"] = c.theme
        if getattr(c, "tint", None) is not None:
            out["tint"] = c.tint
    return out


def font_from(wire: dict | None) -> InlineFont:
    """The font `font_wire` wrote down, or the crux orange when there is none."""
    if not wire:
        return ORANGE
    kw = {k: wire[k] for k in FONT_FIELDS if k in wire}
    if "rgb" in wire:
        color = Color(rgb=wire["rgb"], tint=wire.get("tint", 0.0))
    elif "theme" in wire:
        color = Color(theme=wire["theme"], tint=wire.get("tint", 0.0))
    else:
        color = None
    return InlineFont(color=color, **kw)


def _crux_spans(value) -> list[tuple[int, int, InlineFont | None]]:
    """Where a cell's orange runs sit, as (start, end, font) in its plain text."""
    text, fonts = _char_fonts(value)
    spans, i = [], 0
    while i < len(text):
        if not is_crux_font(fonts[i]):
            i += 1
            continue
        j = i
        while j < len(text) and is_crux_font(fonts[j]):
            j += 1
        spans.append((i, j, fonts[i]))
        i = j
    return spans


def _transcript_sheets(wb):
    """The sheets the turn screen reads, the ones `read_case` keeps, with their columns."""
    for ws in wb.worksheets:
        cols = detect_columns(ws)
        if {"name", "ts", "transcript"} <= set(cols):
            yield ws, cols


# The cells a find and replace reaches on each row (Adam, 24 October 2026, "Everything follows"): the
# transcript, then the experiential statements, the quotes, the exploratory notes and the interviewer's
# notes, each by its role in `detect_columns`, so the words found change wherever the row holds them.
REPLACE_ROLES = ("transcript", "es", "kq", "en", "note")
# what the dry run and the command line call each column, by its role
ROLE_NAMES = {"transcript": "transcript", "es": "statements", "kq": "quotes", "en": "exploratory notes",
              "note": "interviewer notes"}


def replace_pairs(find=None, replace=None, pairs=None) -> list[tuple[str, str]]:
    """The finds and their replacements a replace runs, in order: `pairs` when given, else the one
    `find` and `replace`. An empty find is refused, a line break in either is refused, and a pair whose
    replacement reads as its find is left out, since it changes nothing."""
    given = [(find, replace)] if pairs is None else list(pairs)
    out = []
    for item in given:
        f, r = (item[0], item[1]) if isinstance(item, (list, tuple)) and len(item) == 2 else (None, None)
        f = "" if f is None else str(f)
        r = "" if r is None else str(r)
        if not f:
            raise WorkbookError(i18n.t("server.type_words_find_first"))
        if any(ch in f + r for ch in "\r\n"):
            raise WorkbookError(i18n.t("server.find_replace_one_line_each"))
        if f != r:
            out.append((f, r))
    return out


def _replaced(text: str, pairs, word: bool, case: bool) -> tuple[str, int]:
    """One piece of text with every pair run over it in order, each on what the one before left, and
    how many occurrences changed. An occurrence that already reads as its replacement is left and not
    counted."""
    count = 0
    for find, replace in pairs:
        spans = [(s, e) for s, e in find_spans(text, find, word, case)
                 if text[s:e] != (replace if case else keep_case(text[s:e], replace))]
        if spans:
            text = _splice(text, spans, replace, keep=not case)
            count += len(spans)
    return text, count


def _replaced_entries(value, role: str, pairs, word: bool, case: bool) -> tuple[str | None, int]:
    """An annotation cell with the pairs run over each of its entries, a statement, a quote or a note
    at a time, never across the blank line between two. A quotes cell's "(no quote)" keeps its place
    untouched, and an entry the replace would leave empty is left as it was, so every entry keeps its
    place and a statement keeps its card. Answers the cell's new text, or None when nothing changed, and
    the count."""
    entries = split_entries(plain_text(value) if value is not None else None)
    out, count = [], 0
    for entry in entries:
        if role == "kq" and no_quote(entry):
            out.append(entry)
            continue
        new, n = _replaced(entry, pairs, word, case)
        if n and new.strip():
            out.append(new)
            count += n
        else:
            out.append(entry)
    if not count:
        return None, 0
    return ENTRY_JOIN.join(out), count


def replace_words(path: Path, find: str | None = None, replace: str | None = None, word: bool = True,
                  case: bool = False, only: dict | None = None, pairs=None, dry: bool = False,
                  form: str | None = None) -> dict:
    """Replace `find` with `replace`, or each of `pairs` in turn, wherever a row holds the words: its
    transcript, its experiential statements, its quotes, its exploratory notes and the interviewer's
    notes (Adam, 24 October 2026, "Everything follows"), every row of every sheet, or in the transcript
    the one occurrence `only` names. `find_spans` matches in every cell alike.

    `only` is {"sheet", "row", "ordinal", "text"}: the occurrence's 0-based place among that row's
    transcript matches, counted again here by the same rules, and the row's text as the page holds it.
    A place that is no longer there, or a row that reads differently, is refused with nothing written.
    Only the transcript changes then, since the occurrence is the transcript's.

    A transcript cell is written through `rewrite_transcript`, its highlights kept by phrase. An
    annotation cell is written a statement, a quote or a note at a time (see `_replaced_entries`), as
    plain text, no cell ever gaining a fill. The header row is never touched. An empty find is refused,
    and a replace equal to the find does nothing. The workbook is loaded once and saved once, and with
    `dry` it is never saved. Each row changed comes back with its old and its new transcript, its runs,
    the highlights dropped and where each sat, the occurrences replaced in it, `columns`, the count in
    each column by role, `cells`, each annotation cell changed with its old and its new text, and its
    timecode, `time`, written as `form` says, by default as the project's timecodes say.
    """
    path = Path(path)
    guard_lock(path)
    form = form or timecodes_for(path)
    pairs = replace_pairs(find, replace, pairs)
    if not pairs:
        return {"rows": [], "counts": {}, "replaced": 0, "changed": False}
    if only is not None and len(pairs) != 1:
        raise WorkbookError(i18n.t("server.one_occurrence_replaced_one_find"))
    if only is not None and int(only["row"]) < 2:
        raise WorkbookError(i18n.t("server.header_row_never_edited"))
    wb = openpyxl.load_workbook(path, rich_text=True)
    try:
        sheets = list(_transcript_sheets(wb))
        if only is not None and only["sheet"] not in [ws.title for ws, _ in sheets]:
            raise WorkbookError(i18n.t("server.sheet_called", sheet=only['sheet'], name=path.name))
        rows: list[dict] = []
        counts: dict[str, int] = {}
        for ws, cols in sheets:
            if only is not None and ws.title != only["sheet"]:
                continue
            numbers = [int(only["row"])] if only is not None else range(2, ws.max_row + 1)
            for r in numbers:
                cell = ws.cell(r, cols["transcript"])
                old = plain_text(cell.value)
                columns: dict[str, int] = {}
                text, dropped, marks = old, [], []
                if only is not None:
                    f, rep = pairs[0]
                    spans = find_spans(old, f, word, case)
                    place = int(only.get("ordinal") or 0)
                    expect = only.get("text")
                    if (expect is not None and str(expect) != old) or not 0 <= place < len(spans):
                        raise WorkbookError(i18n.t("server.occurrence_longer_where_nothing_written"))
                    s, e = spans[place]
                    if old[s:e] != (rep if case else keep_case(old[s:e], rep)):
                        text, columns["transcript"] = _splice(old, [(s, e)], rep, keep=not case), 1
                else:
                    text, n = _replaced(old, pairs, word, case)
                    if n:
                        columns["transcript"] = n
                cells: dict[str, dict] = {}
                if only is None:
                    for role in REPLACE_ROLES[1:]:
                        if role not in cols:
                            continue
                        held = ws.cell(r, cols[role]).value
                        new, n = _replaced_entries(held, role, pairs, word, case)
                        if n:
                            cells[role] = {"old": plain_text(held), "new": new}
                            columns[role] = n
                if not columns:
                    continue
                if "transcript" in columns:
                    marks = _crux_spans(cell.value)
                    if dry:
                        _value, dropped = rekey_crux(cell.value, text)
                    else:
                        dropped = rewrite_transcript(cell, text)
                if not dry:
                    for role, change in cells.items():
                        ws.cell(r, cols[role]).value = change["new"]
                seconds = ts_seconds(ws.cell(r, cols["ts"]).value)
                n = sum(columns.values())
                changed = {"sheet": ws.title, "row": r, "old": old, "text": text if dry else plain_text(cell.value),
                           "runs": cell_runs(cell.value), "dropped": dropped, "count": n,
                           "columns": columns, "cells": cells, "time": timecode(seconds, form)}
                if dropped:
                    # where each dropped highlight sat in the old text, and its font, for an undo
                    changed["crux"] = [[s, e, font_wire(f)] for s, e, f in marks if old[s:e] in dropped]
                rows.append(changed)
                counts[ws.title] = counts.get(ws.title, 0) + n
        if rows and not dry:
            _atomic_save(wb, path)
        return {"rows": rows, "counts": counts, "replaced": sum(counts.values()), "changed": bool(rows) and not dry}
    finally:
        wb.close()


def names_in_book(path: Path, fix, dry: bool = False) -> dict:
    """The project's list of names run over a workbook already in (namesui, 8 November 2026): every row of every
    sheet the turn screen reads, its speaker's name, its transcript, then each statement, quote, exploratory note
    and interviewer's note one entry at a time, in that order, so a check and a replace meet each find in the same
    place. `fix(text, role, sheet, row)` answers the text as it is to be, the finds left as written by the caller's
    skips. A transcript is written through `rewrite_transcript`, its highlights kept by phrase, an annotation cell
    entry by entry, an entry the change would leave empty left as it was. With `dry` nothing is saved and an open
    workbook is not refused. Answers each row changed as `replace_words` answers one, with `cells`, the old and the
    new text of each annotation cell, which the boards and the GETs follow (`idiograph_routes.follow_replace`)."""
    path = Path(path)
    if not dry:
        guard_lock(path)
    wb = openpyxl.load_workbook(path, rich_text=True)
    try:
        rows: list[dict] = []
        for ws, cols in _transcript_sheets(wb):
            for r in range(2, ws.max_row + 1):
                columns: dict[str, int] = {}
                cells: dict[str, dict] = {}
                name_cell = ws.cell(r, cols["name"])
                name_was = name_cell.value if isinstance(name_cell.value, str) else None
                name_new = fix(name_was, "speaker", ws.title, r) if name_was and name_was.strip() else name_was
                if name_new != name_was:
                    columns["name"] = 1
                cell = ws.cell(r, cols["transcript"])
                old = plain_text(cell.value)
                text = fix(old, "transcript", ws.title, r) if old else old
                if text != old:
                    columns["transcript"] = 1
                for role in REPLACE_ROLES[1:]:
                    if role not in cols:
                        continue
                    held = ws.cell(r, cols[role]).value
                    entries = split_entries(plain_text(held) if held is not None else None)
                    out, changed = [], False
                    for entry in entries:
                        new = entry if role == "kq" and no_quote(entry) else fix(entry, role, ws.title, r)
                        if new != entry and new.strip():
                            out.append(new)
                            changed = True
                        else:
                            out.append(entry)
                    if changed:
                        cells[role] = {"old": plain_text(held), "new": ENTRY_JOIN.join(out)}
                        columns[role] = 1
                if not columns:
                    continue
                if not dry:
                    if "name" in columns:
                        name_cell.value = name_new
                    if "transcript" in columns:
                        rewrite_transcript(cell, text)
                    for role, change in cells.items():
                        ws.cell(r, cols[role]).value = change["new"]
                rows.append({"sheet": ws.title, "row": r, "old": old, "text": text, "columns": columns, "cells": cells,
                             "dropped": [], "count": len(columns)})
        if rows and not dry:
            _atomic_save(wb, path)
        return {"rows": rows, "changed": bool(rows) and not dry}
    finally:
        wb.close()


def put_back(path: Path, records: list[dict], to: str) -> list[dict]:
    """Write each edit record's text back into its row: `old` for an undo, `new` for a redo, the
    transcript and every annotation cell the record names under `cells` alike.

    Every row is read first, and nothing is written unless each cell still holds the other text of its
    record, so a passage changed since is refused whole. A transcript goes through `rewrite_transcript`,
    which finds the highlights again by phrase, and an undo then puts a highlight the replace dropped
    back on the characters it covered, from the record's `crux`. One load, one save. Each row comes
    back as `replace_words` answers it, with the annotation cells it wrote, by role.
    """
    if to not in ("old", "new"):
        raise WorkbookError(i18n.t("server.replace_undone_redone_nothing_else"))
    other = "new" if to == "old" else "old"
    path = Path(path)
    guard_lock(path)
    wb = openpyxl.load_workbook(path, rich_text=True)
    try:
        plan = []
        for record in records:
            sheet, row = record["sheet"], int(record["row"])
            if sheet not in wb.sheetnames:
                raise WorkbookError(i18n.t("server.sheet_called", sheet=sheet, name=path.name))
            ws = wb[sheet]
            cols = detect_columns(ws)
            if "transcript" not in cols or row < 2:
                raise WorkbookError(i18n.t("server.passage_replace_changed_reads_differently"))
            cell = ws.cell(row, cols["transcript"])
            if plain_text(cell.value) != record[other]:
                raise WorkbookError(i18n.t("server.passage_replace_changed_reads_differently"))
            for role, change in (record.get("cells") or {}).items():
                if (role not in cols
                        or split_entries(plain_text(ws.cell(row, cols[role]).value)) != split_entries(change[other])):
                    raise WorkbookError(i18n.t("server.passage_replace_changed_reads_differently"))
            plan.append((record, ws, cols, cell))
        rows = []
        for record, ws, cols, cell in plan:
            target = record[to]
            dropped = rewrite_transcript(cell, target) if target != plain_text(cell.value) else []
            if to == "old" and record.get("crux"):
                text, fonts = _char_fonts(cell.value)
                for start, end, *font in record["crux"]:
                    start, end = int(start), int(end)
                    if 0 <= start < end <= len(text) and not all(is_crux_font(f) for f in fonts[start:end]):
                        fonts[start:end] = [font_from(font[0] if font else None)] * (end - start)
                cell.value = _rebuild(text, fonts)
            cells = {}
            for role, change in (record.get("cells") or {}).items():
                ws.cell(int(record["row"]), cols[role]).value = change[to] or None
                cells[role] = {"old": change[other], "new": change[to]}
            rows.append({"sheet": ws.title, "row": int(record["row"]), "text": plain_text(cell.value),
                         "runs": cell_runs(cell.value), "dropped": dropped, "cells": cells})
        if rows:
            _atomic_save(wb, path)
        return rows
    finally:
        wb.close()


def passage_cells(path: Path, places) -> dict[tuple[str, int], dict]:
    """What the turn screen holds of each row `places` names, (sheet, row), as `read_case` gives it:
    the statements, the notes, the quotes, the pairs, whether its quotes are still to pair, its version
    and the interviewer's note, for the page to take in after a replace or its undo. Read-only."""
    wanted = {(str(s), int(r)) for s, r in places}
    out: dict[tuple[str, int], dict] = {}
    if not wanted:
        return out
    wb = openpyxl.load_workbook(path, rich_text=True)
    try:
        for ws in wb.worksheets:
            if ws.title not in {s for s, _ in wanted}:
                continue
            cols = detect_columns(ws)
            for sheet, r in sorted(wanted):
                if sheet != ws.title:
                    continue
                held = lambda role: ws.cell(r, cols[role]).value if role in cols else None
                out[(sheet, r)] = dict(turn_now(held("es"), held("en"), held("kq")),
                                       note=field_to_lines(held("note")) if "note" in cols else "")
    finally:
        wb.close()
    return out




def _note_column(ws) -> int:
    """Add the Interviewer notes heading to a sheet that has none, and say where it went.

    The heading goes in the first empty header cell after the last used one, in the header font,
    and the column takes its width. Nothing else on the sheet changes and no cell gains a fill.
    """
    used = [c for c, v in enumerate(header_row(ws), start=1) if v is not None and str(v).strip()]
    col = (max(used) if used else 0) + 1
    if col > 12:
        raise WorkbookError(i18n.t("server.room_column_first_twelve_columns", note_header=NOTE_HEADER, title=ws.title))
    head = ws.cell(1, col)
    head.value, head.font, head.alignment = NOTE_HEADER, HFONT, ALIGN
    ws.column_dimensions[get_column_letter(col)].width = NOTE_WIDTH
    return col


def save_interviewer_note(path: Path, sheet: str, row: int, text: str, interviewer: str, dry: bool = False) -> dict:
    """Write the analyst's note on one of his own turns into the Interviewer notes column.

    The row's speaker must be the interviewer. The column is added the first time a note is
    written on the sheet and found by its header after that. A cell whose text is the same is left
    exactly as it is, an empty text clears the cell, and the cell written takes the body font and
    alignment the three fields' cells carry. Nothing else in the workbook is touched, and nothing in
    the progress file, so an interviewer's turn stays context and never a stop. The answer carries the
    note it held, `old`, and with `dry` nothing is saved (26 October, an agent's dry run).
    """
    path = Path(path)
    guard_lock(path)
    wb = openpyxl.load_workbook(path, rich_text=True)
    try:
        if sheet not in wb.sheetnames:
            raise WorkbookError(i18n.t("server.sheet_called", sheet=sheet, name=path.name))
        ws = wb[sheet]
        cols = detect_columns(ws)
        if "name" not in cols:
            raise WorkbookError(i18n.t("server.speaker_column", sheet=sheet))
        row = int(row)
        if row < 2:
            raise WorkbookError(i18n.t("server.header_row_never_edited"))
        speaker = _norm(ws.cell(row, cols["name"]).value) if row <= ws.max_row else ""
        if not speaker or speaker != _norm(interviewer):
            raise WorkbookError(i18n.t("server.interviewer_notes_belong_interviewer_s"))
        value = lines_to_field(text)
        changed = False
        old = field_to_lines(ws.cell(row, cols["note"]).value) if "note" in cols else ""
        if "note" in cols:
            cell = ws.cell(row, cols["note"])
            if split_entries(cell.value) != split_entries(value):
                cell.value = value
                cell.font, cell.alignment = FONT, ALIGN
                changed = True
        elif value is not None:
            # an empty note on a sheet with no column has nothing to clear, and adds no column
            cell = ws.cell(row, _note_column(ws))
            cell.value = value
            cell.font, cell.alignment = FONT, ALIGN
            changed = True
        if changed and not dry:
            _atomic_save(wb, path)
        return {"row": row, "sheet": sheet, "text": field_to_lines(value), "changed": changed, "old": old}
    finally:
        wb.close()


QUOTE_HEADER = HEADER[-1]


def quote_heading(path: Path, dry_run: bool = False) -> list[dict]:
    """The quotes column's heading renamed from Key quotes to Quote on every annotation sheet, the one
    op that renames it (Adam's ruling of 23 October 2026, for a workbook made before 22 October).

    An annotation sheet is one the turn screen reads, with a quotes column. A heading reading Key
    quotes, or Key quote, takes the word Quote and keeps its font, fill, border and alignment. No other
    cell is touched. A sheet headed Quote already, one whose quotes column is headed some other way, and
    one with no quotes column are left as they are and said so. Answers each sheet with `sheet`,
    `column`, `was`, `now` and `change`, one of rename, already, other or none. With `dry_run`, or with
    nothing to rename, nothing is written. The caller holds the case's lock."""
    path = Path(path)
    guard_lock(path)
    wb = openpyxl.load_workbook(path, rich_text=True)
    try:
        out = []
        for ws, cols in _transcript_sheets(wb):
            if "kq" not in cols:
                out.append({"sheet": ws.title, "column": None, "was": None, "now": None, "change": "none"})
                continue
            cell = ws.cell(1, cols["kq"])
            was = plain_text(cell.value)
            said = " ".join(was.split())
            if said == QUOTE_HEADER:
                change = "already"
            elif "key quote" in said.lower():
                change = "rename"
            else:
                change = "other"
            if change == "rename":
                cell.value = QUOTE_HEADER
            out.append({"sheet": ws.title, "column": get_column_letter(cols["kq"]), "was": was,
                        "now": QUOTE_HEADER if change == "rename" else was, "change": change})
        if not dry_run and any(s["change"] == "rename" for s in out):
            _atomic_save(wb, path)
        return out
    finally:
        wb.close()




def edit_statement(path: Path, sheet: str, row: int, line: int, text: str, old: str | None = None) -> dict:
    """Replace one line of one row's experiential statements cell, the PETs screen's one write.

    The cell is split into its lines and joined again the way the turn screen's save does, so every
    other line stays as it was, and the cell keeps its font, its alignment and its number format and
    never gains a fill. The text is kept to one line, and an empty one is refused. With `old`, a
    line that no longer reads so is refused, so an undo never writes over a line changed since.
    Behind the same lock guard as `save_turn`, so a workbook Excel has open is refused, and nothing
    else in the workbook is touched. A text that is the same writes nothing.
    """
    path = Path(path)
    guard_lock(path)
    new = " ".join(str(text or "").split())
    if not new:
        raise WorkbookError(i18n.t("server.statement_cannot_left_empty_esc"))
    wb = openpyxl.load_workbook(path, rich_text=True)
    try:
        if sheet not in wb.sheetnames:
            raise WorkbookError(i18n.t("server.sheet_called", sheet=sheet, name=path.name))
        ws = wb[sheet]
        cols = detect_columns(ws)
        if "es" not in cols:
            raise WorkbookError(i18n.t("server.experiential_statements_column", sheet=sheet))
        row, line = int(row), int(line)
        if row < 2:
            raise WorkbookError(i18n.t("server.header_row_never_edited"))
        cell = ws.cell(row, cols["es"])
        entries = split_entries(plain_text(cell.value) if isinstance(cell.value, CellRichText) else cell.value)
        if not 0 <= line < len(entries):
            raise WorkbookError(i18n.t("server.statement_longer_workbook_nothing_written"))
        was = entries[line]
        if old is not None and " ".join(was.split()) != " ".join(str(old).split()):
            raise WorkbookError(i18n.t("server.statement_reads_differently_workbook_now"))
        changed = was != new
        if changed:
            entries[line] = new
            cell.value = join_entries(entries)
            _atomic_save(wb, path)
        return {"sheet": sheet, "row": row, "line": line, "old": was, "text": new, "changed": changed}
    finally:
        wb.close()


# ------------------------------------------------- create from a raw source

def source_pairs(es_text, kq_text) -> tuple[str | None, str | None]:
    """A raw source's statements and quotes, a line each, as the two cells the workbook keeps: paired by order,
    the first quote the first statement's (ayabuild12, 9 November 2026), "(no quote)" for a statement past the
    last quote once any quote is there, and a quote past the last statement kept after them, so the turn is
    listed under Quotes to pair. Nothing is lost."""
    lines = lambda text: [ln.strip() for ln in str(text or "").splitlines() if ln.strip()]
    return pairs_to_cells(pair_entries(lines(es_text), lines(kq_text)))


def quote_census(passages) -> dict:
    """What an import's quotes come to, counts only (ayabuild12): `passages`, each `(words, statements, quotes)`
    with the statements and the quotes a list of lines in the file's order. `paired` statements with a quote,
    `unpaired` quotes past the last statement, which wait under Quotes to pair, `no_quote` statements past the
    last quote, and `unmarked` quotes not word for word in their passage, kept as the statement's quote but not
    marked in the words."""
    out = {"paired": 0, "unpaired": 0, "no_quote": 0, "unmarked": 0}
    for words, statements, quotes in passages:
        statements, quotes = [s for s in statements if s.strip()], [q for q in quotes if q.strip()]
        out["paired"] += min(len(statements), len(quotes))
        out["unpaired"] += max(0, len(quotes) - len(statements))
        if quotes:
            out["no_quote"] += max(0, len(statements) - len(quotes))
        out["unmarked"] += sum(1 for q in quotes if not quote_reach(q, [words or ""], 0))
    return out


def create_from_source(source: Path, out: Path, made: str = "") -> Path:
    """Build an annotated workbook from a raw `Name | Timestamp | Transcript` source.

    The annotation columns are inserted in Adam's order, with the reference workbook's headers, widths and
    formatting. The source is opened read-only and never written to. `made`, for a workbook an
    agent made, says who made it for which request, in the file's own description.
    """
    source, out = Path(source), Path(out)
    if "Source" in out.parts:
        raise WorkbookError(i18n.t("server.refusing_write_into_source_folder"))
    if out.exists():
        raise WorkbookError(i18n.t("server.already_exists_open_instead_rename", name=out.name))
    guard_lock(out)
    src = openpyxl.load_workbook(source, rich_text=True)
    wb = openpyxl.Workbook()
    blank = wb.active                      # the empty sheet a new workbook starts with
    if blank is not None:
        wb.remove(blank)
    for ws_src in src.worksheets:
        cols = detect_columns(ws_src)
        if not {"name", "ts", "transcript"} <= set(cols):
            continue
        _annotated_sheet(wb, ws_src, cols)
    src.close()
    if not wb.sheetnames:
        raise WorkbookError(i18n.t("server.transcript_sheets_found", name=source.name))
    if made:
        wb.properties.description = made
    _atomic_save(wb, out)
    wb.close()
    return out


def _annotated_sheet(wb, ws_src, cols: dict[str, int]):
    """One sheet of an annotated workbook made from a raw source's sheet of the same name, at the end
    of `wb`: the six headers, the speaker, the time and the words, the reference workbook's widths,
    fonts and wrapping, the panes frozen at C2 and the zoom at 160."""
    ws = wb.create_sheet(ws_src.title)
    for col, h in zip("ABCDEF", HEADER):
        c = ws[f"{col}1"]
        c.value, c.font, c.alignment = h, HFONT, ALIGN
    # a Word table's notes, which a raw source made from one carries beside the words (19 October),
    # each written as the statements screen writes it, a line an entry
    extras = {role: c for c, raw in enumerate(header_row(ws_src)[:12], start=1) if raw is not None
              for head, role in RAW_EXTRAS.items() if str(raw).strip().lower() == head}
    if "note" in cols:
        extras["note"] = cols["note"]
    places = {"es": 3, "en": 5, "note": 7, "kq": 6}
    marked = []
    for r in range(2, ws_src.max_row + 1):
        ws.cell(r, 1, ws_src.cell(r, cols["name"]).value)
        tsc = ws.cell(r, 2, ws_src.cell(r, cols["ts"]).value)
        tsc.number_format = ws_src.cell(r, cols["ts"]).number_format
        ws.cell(r, 4, ws_src.cell(r, cols["transcript"]).value)
        held = {role: ws_src.cell(r, c).value for role, c in extras.items()}
        held = {role: (plain_text(v) if isinstance(v, CellRichText) else str(v)) if v is not None else None
                for role, v in held.items()}
        if "kq" in held:
            # each quote line with the statement on the same line, as the statements screen pairs them: a quote
            # past the last statement waits under Quotes to pair, a statement past the last quote has none
            held["es"], held["kq"] = source_pairs(held.get("es"), held["kq"])
        for role in extras:
            value = held[role]
            value = (value if role in ("es", "kq") and "kq" in held else lines_to_field(value)) if value is not None else None
            if value is not None:
                if role == "note" and ws.cell(1, 7).value is None:
                    head = ws.cell(1, 7)
                    head.value, head.font, head.alignment = NOTE_HEADER, HFONT, ALIGN
                    ws.column_dimensions["G"].width = NOTE_WIDTH
                cell = ws.cell(r, places[role], value)
                cell.font, cell.alignment = FONT, ALIGN
        if "ctx" in cols and str(ws_src.cell(r, cols["ctx"]).value or "").strip():
            marked.append(r)
        for col in range(1, 7):
            cell = ws.cell(r, col)
            cell.font, cell.alignment = FONT, ALIGN
    if marked:
        # the context marks after every other column, Interviewer notes included, once those are placed
        at = 8 if ws.cell(1, 7).value is not None else 7
        head = ws.cell(1, at)
        head.value, head.font, head.alignment = CONTEXT_HEADER, HFONT, ALIGN
        ws.column_dimensions[get_column_letter(at)].width = 12.0
        for r in marked:
            cell = ws.cell(r, at, CONTEXT_HEADER)
            cell.font, cell.alignment = FONT, ALIGN
    for col, w in WIDTHS.items():
        ws.column_dimensions[col].width = w
    ws.freeze_panes = "C2"
    ws.sheet_view.zoomScale = 160
    return ws


def add_from_source(source: Path, sheets, out: Path) -> Path:
    """Sheets of a raw source added to an annotated workbook that stands, a further interview each,
    at the end and made as `create_from_source` makes one, with nothing already there changed: every
    sheet, cell, style, width and pane stays as it was. Refused when Excel has the workbook open,
    when a sheet of that name is there already, and when the source has no such transcript sheet.
    The source is opened read-only and never written to."""
    source, out = Path(source), Path(out)
    guard_lock(out)
    src = openpyxl.load_workbook(source, rich_text=True)
    try:
        wb = openpyxl.load_workbook(out, rich_text=True)
        try:
            taken = {name.lower() for name in wb.sheetnames}
            for title in sheets:
                title = str(title)
                if title.lower() in taken:
                    raise WorkbookError(i18n.t("server.sheet_named_already", name=out.name, title=title))
                ws_src = src[title] if title in src.sheetnames else None
                cols = detect_columns(ws_src) if ws_src is not None else {}
                if not {"name", "ts", "transcript"} <= set(cols):
                    raise WorkbookError(i18n.t("server.transcript_sheet_named", name=source.name, title=title))
                _annotated_sheet(wb, ws_src, cols)
                taken.add(title.lower())
            _atomic_save(wb, out)
        finally:
            wb.close()
    finally:
        src.close()
    return out


# ------------------------------------------------------ trimming the ends

def _shift_row_heights(ws, first: int, count: int, inserted: bool = False) -> None:
    """Move custom row heights with their rows after a delete, or after an insert.

    `delete_rows` and `insert_rows` carry the cells and their styles, and leave `row_dimensions`
    where they were, so a row height would end up on a different row than the one it was set for.
    After a delete the heights below the gap move up by `count` and the deleted rows' heights go.
    After an insert every height from `first` down moves down by `count`, and the new rows start
    with none, for the caller to set.
    """
    dims = ws.row_dimensions
    kept = {}
    for index in sorted(dims):
        if inserted:
            kept[index + count if index >= first else index] = dims[index]
        elif index < first:
            kept[index] = dims[index]
        elif index >= first + count:
            kept[index - count] = dims[index]
    for index in list(dims):
        del dims[index]
    for index, dim in kept.items():
        dim.index = index
        dims[index] = dim


def archive_copy(path: Path, label: str) -> Path:
    """Copy the workbook to `_Archive/<stem> (<label> <date-time>).xlsx` before any row moves.

    Two operations inside the same minute each keep a copy of their own, because an undo restores
    from the one it was given and must never find another operation's copy in its place.
    """
    path = Path(path)
    archive = case_folder(path) / "_Archive"
    archive.mkdir(parents=True, exist_ok=True)
    stamp = dt.datetime.now().strftime("%Y%m%d-%H%M")
    backup = archive / f"{path.stem} ({label} {stamp}).xlsx"
    n = 2
    while backup.exists():
        backup = archive / f"{path.stem} ({label} {stamp}-{n}).xlsx"
        n += 1
    shutil.copy2(path, backup)
    return backup


def trim_preview(path: Path, sheet: str, row: int, direction: str, form: str | None = None) -> dict:
    """The rows a trim would take, without touching anything, its times as `form` says, by default as
    the project's timecodes say."""
    path = Path(path)
    form = form or timecodes_for(path)
    wb = openpyxl.load_workbook(path, rich_text=True)
    try:
        if sheet not in wb.sheetnames:
            raise WorkbookError(i18n.t("server.sheet_called", sheet=sheet, name=path.name))
        ws = wb[sheet]
        cols = detect_columns(ws)
        row = int(row)
        if row < 2:
            raise WorkbookError(i18n.t("server.header_row_never_cut"))
        first, last = (2, row) if direction == "before" else (row, ws.max_row)
        if first > last:
            raise WorkbookError(i18n.t("server.nothing_cut_side_passage"))
        times, marked = [], 0
        for r in range(first, last + 1):
            seconds = ts_seconds(ws.cell(r, cols["ts"]).value) if "ts" in cols else None
            if seconds is not None:
                times.append(seconds)
            annotated = any(split_entries(ws.cell(r, cols[role]).value) for role in ("es", "en", "kq") if role in cols)
            crux = any(x["crux"] for x in cell_runs(ws.cell(r, cols["transcript"]).value))
            if annotated or crux:
                marked += 1
        boundary = ws.cell(row, cols["ts"]).value if "ts" in cols else None
        head = plain_text(ws.cell(row, cols["transcript"]).value)[:60]
        return {"sheet": sheet, "direction": direction, "row": row, "first": first, "last": last,
                "count": last - first + 1, "marked": marked,
                "from": timecode(min(times), form) if times else "", "to": timecode(max(times), form) if times else "",
                "timecode": timecode(ts_seconds(boundary), form), "head": head,
                "left": ws.max_row - (last - first + 1) - 1}
    finally:
        wb.close()


def trim_rows(path: Path, sheet: str, row: int, direction: str, dry: bool = False) -> dict:
    """Cut the consent talk off the front, or the goodbyes off the back.

    The workbook is copied into `_Archive` before a single row goes, because the rows themselves
    are the only record of what was there. The header row is never cut, and the transcript column
    keeps its rich text and its orange runs on every surviving row. That copy is also what
    `restore_trim` puts the rows back from. With `dry` it answers the plan, the rows it would cut, and
    writes nothing, no backup either (26 October, an agent's dry run).
    """
    path = Path(path)
    if direction not in ("before", "after"):
        raise WorkbookError(i18n.t("server.trim_runs_before_passage_after"))
    guard_lock(path)
    plan = trim_preview(path, sheet, row, direction)
    if dry:
        return dict(plan, removed=0, backup=None)

    backup = archive_copy(path, "pre-trim")

    wb = openpyxl.load_workbook(path, rich_text=True)
    ws = wb[sheet]
    count = plan["last"] - plan["first"] + 1
    ws.delete_rows(plan["first"], count)
    _shift_row_heights(ws, plan["first"], count)
    _atomic_save(wb, path)
    wb.close()
    return dict(plan, removed=count, backup=backup)


def _text_at(ws, cols: dict[str, int], r: int) -> str:
    """The plain text of one row's transcript cell, and nothing for the header or past the last
    row, which is read without making a cell there, so a check never grows the sheet it reads."""
    if r < 2 or r > ws.max_row:
        return ""
    return plain_text(ws.cell(r, cols["transcript"]).value)


def restore_trim(path: Path, sheet: str, first: int, count: int, backup: Path) -> dict:
    """Undo a trim: the rows it cut come back from its backup, at the place they were cut from.

    `first` and `count` are the rows the trim took. Rows open at `first` and take rows `first` to
    `first + count - 1` of the backup cell for cell, value, rich text and style, with their heights,
    the way `restore_rows` puts an assignment back. The rows that survived the cut move down and
    are not otherwise touched, so a statement, a key quote or a note written on them since stays
    where it was written. The header row is never touched and no cell gains a fill.

    The rows either side of the gap must read as the rows either side of the cut read in the
    backup. A sheet that reads differently there has been changed some other way, and it is
    refused rather than written over.
    """
    path, backup = Path(path), Path(backup)
    guard_lock(path)
    first, count = int(first), int(count)
    if first < 2:
        raise WorkbookError(i18n.t("server.header_row_never_restored_over"))
    if count < 1:
        raise WorkbookError(i18n.t("server.trim_cut_rows_nothing_put"))
    if not backup.exists():
        raise WorkbookError(i18n.t("server.backup_undo_needs_gone_from", name=backup.name))
    if backup.resolve().parent != (case_folder(path) / "_Archive").resolve():
        raise WorkbookError(i18n.t("server.backup_does_belong_participant"))
    wb = openpyxl.load_workbook(path, rich_text=True)
    bk = openpyxl.load_workbook(backup, rich_text=True)
    try:
        ws, cols = _transcript_sheet(wb, sheet, path)
        if sheet not in bk.sheetnames:
            raise WorkbookError(i18n.t("server.backup_sheet_called", sheet=sheet))
        bws = bk[sheet]
        if first + count - 1 > bws.max_row:
            raise WorkbookError(i18n.t("server.backup_does_hold_rows_trim"))
        # the row above the gap is the row above the cut, and the row below it the row below
        for now, was in ((first - 1, first - 1), (first, first + count)):
            if _text_at(ws, cols, now) != _text_at(bws, cols, was):
                raise WorkbookError(i18n.t("server.rows_beside_cut_have_changed"))
        ws.insert_rows(first, count)
        _shift_row_heights(ws, first, count, inserted=True)
        width = max(ws.max_column, bws.max_column)
        for r in range(first, first + count):
            for c in range(1, width + 1):
                _copy_cell(bws.cell(r, c), ws.cell(r, c))
            height = bws.row_dimensions[r].height if r in bws.row_dimensions else None
            if height is not None:
                ws.row_dimensions[r].height = height
        _atomic_save(wb, path)
    finally:
        wb.close()
        bk.close()
    return {"sheet": sheet, "first": first, "last": first + count - 1, "count": count, "restored": count}


# ------------------------------------------------ assigning words to a speaker
#
# A participant turn sometimes carries words the interviewer said, and the other way about. The
# operation takes words out of one turn and makes them a turn of the speaker they belong to, or
# gives a whole turn to another speaker. Where the speaker it lands on already holds the turn
# before or after, the two become one, so the sheet never reads the same name twice running.
#
# Every assignment is one of three shapes on the sheet: rows inserted beside the turn, rows merged
# into a neighbour and deleted, or nothing moving at all but a name or the text of two rows. The
# workbook is archived first, the way the trim archives it, and that copy is what an undo restores
# the touched rows from.

SECONDS_PER_WORD = 0.4          # the estimate for a cut in the last turn of a sheet
ROLES = ("es", "en", "kq")


def _norm(name) -> str:
    return str(name or "").strip().lower()


def sheet_speakers(ws, cols: dict[str, int]) -> list[str]:
    """The distinct Name values of a sheet, in the order they first appear. No limit on how many."""
    seen, out = set(), []
    for r in range(2, ws.max_row + 1):
        name = str(ws.cell(r, cols["name"]).value or "").strip()
        if name and name.lower() not in seen:
            seen.add(name.lower())
            out.append(name)
    return out


def _speaker_sheets(wb):
    """The sheets of a workbook that hold a transcript, a Name, a Timestamp and a Transcript column,
    each with its columns."""
    for ws in wb.worksheets:
        cols = detect_columns(ws)
        if {"name", "ts", "transcript"} <= set(cols):
            yield ws, cols


def speaker_rows(path: Path, name: str, interviewer: str = "") -> dict[str, int]:
    """How many rows of each transcript sheet carry `name` in the Name column, case and spacing set
    aside, a sheet with none left out, and never a row of the interviewer's. Only reads, so Rename
    can say what it will change before it changes anything (16 October)."""
    who, asked = _norm(interviewer), _norm(name)
    if not asked or asked == who:
        return {}
    wb = openpyxl.load_workbook(path, read_only=True)
    out = {}
    try:
        for ws, cols in _speaker_sheets(wb):
            n = sum(1 for values in ws.iter_rows(min_row=2, min_col=cols["name"], max_col=cols["name"], values_only=True)
                    if values and _norm(values[0]) == asked)
            if n:
                out[ws.title] = n
    finally:
        wb.close()
    return out


def rename_speaker(path: Path, old: str, new: str, interviewer: str = "") -> dict[str, int]:
    """Rename's write (16 October): every Name cell that reads `old`, case and spacing set aside, on
    every transcript sheet, set to `new`, the interviewer's rows never touched and every other cell,
    style and font kept, never a fill. Written through the one path every write takes, and nothing
    written when no row carries the name. The answer is the rows changed on each sheet."""
    path = Path(path)
    guard_lock(path)
    who, asked = _norm(interviewer), _norm(old)
    if not asked or asked == who:
        return {}
    wb = openpyxl.load_workbook(path, rich_text=True)
    out = {}
    try:
        for ws, cols in _speaker_sheets(wb):
            n = 0
            for r in range(2, ws.max_row + 1):
                cell = ws.cell(r, cols["name"])
                if cell.value is not None and _norm(cell.value) == asked:
                    cell.value = new
                    n += 1
            if n:
                out[ws.title] = n
        if out:
            _atomic_save(wb, path)
    finally:
        wb.close()
    return out


def snap_words(text: str, start: int, end: int) -> tuple[int, int]:
    """A selection widened to whole words, never half of one, with the spaces at its edges left
    outside it. Words are what whitespace separates, so punctuation travels with its word."""
    if not 0 <= start < end <= len(text):
        raise WorkbookError(i18n.t("server.selection_inside_passage_select_words"))
    while start < end and text[start].isspace():
        start += 1
    while end > start and text[end - 1].isspace():
        end -= 1
    if start >= end:
        raise WorkbookError(i18n.t("server.words_selection_assign"))
    while start > 0 and not text[start - 1].isspace():
        start -= 1
    while end < len(text) and not text[end].isspace():
        end += 1
    return start, end


def _transcript_sheet(wb, sheet: str, path: Path):
    if sheet not in wb.sheetnames:
        raise WorkbookError(i18n.t("server.sheet_called", sheet=sheet, name=Path(path).name))
    ws = wb[sheet]
    cols = detect_columns(ws)
    if not {"name", "transcript"} <= set(cols):
        raise WorkbookError(i18n.t("server.name_transcript_columns", sheet=sheet))
    return ws, cols


def _blank(ws, cols: dict[str, int], r: int) -> bool:
    return all(ws.cell(r, cols[k]).value is None for k in ("name", "ts", "transcript") if k in cols)


def _facts(ws, cols: dict[str, int], r: int) -> dict:
    """One row as the plan needs it: the speaker, the time, every character and its font, the
    annotation entries and the custom height if it has one."""
    text, fonts = _char_fonts(ws.cell(r, cols["transcript"]).value)
    raw = ws.cell(r, cols["name"]).value
    ts_raw = ws.cell(r, cols["ts"]).value if "ts" in cols else None
    dim = ws.row_dimensions[r] if r in ws.row_dimensions else None
    return {"row": r, "raw_name": raw, "name": str(raw).strip() if raw is not None else "",
            "ts_raw": ts_raw, "seconds": ts_seconds(ts_raw), "text": text, "fonts": fonts,
            "entries": {role: split_entries(ws.cell(r, cols[role]).value) for role in ROLES if role in cols},
            "height": dim.height if dim is not None else None}


def _join_runs(parts) -> tuple[str, list]:
    """Texts joined with a single space in sheet order, every character keeping its font.

    The joining space takes the font of the text before it, or after it, whichever is not orange,
    so a merge never stretches a highlight across the join. Spaces at the join are trimmed first,
    so the two texts meet at exactly one.
    """
    text, fonts = "", []
    for piece, pfonts in parts:
        if not piece.strip():
            continue
        if text:
            keep = len(text.rstrip())
            text, fonts = text[:keep], fonts[:keep]
            lead = len(piece) - len(piece.lstrip())
            piece, pfonts = piece[lead:], pfonts[lead:]
            before, after = fonts[-1], pfonts[0]
            joint = before if not is_crux_font(before) else (after if not is_crux_font(after) else None)
            text += " "
            fonts.append(joint)
        text += piece
        fonts = fonts + list(pfonts)
    return text, fonts


def merged_quotes(parts) -> list[str]:
    """The key quotes of rows merged into one, each row's quote kept with its own statement: a
    row's quotes up to its statements' count take their places, "(no quote)" where it has none, and
    a quote past its row's statements goes after them all. With no quote anywhere, none."""
    placed, loose = [], []
    for p in parts:
        statements = p["entries"].get("es", [])
        places = ["" if no_quote(q) else q for q in p["entries"].get("kq", [])]
        placed += places[:len(statements)] + [""] * max(0, len(statements) - len(places))
        loose += [q for q in places[len(statements):] if q]
    if not loose and not any(placed):
        return []
    return [q or NO_QUOTE for q in placed] + loose


def _line_unit(ws) -> float:
    """The height of one line on a sheet whose rows carry custom heights: the smallest one set."""
    heights = [d.height for d in ws.row_dimensions.values() if d.height]
    return max(12.0, min(heights)) if heights else 15.0


def _share_height(src: dict, length: int, unit: float) -> float | None:
    """A new row's height, the source row's lines shared out by the characters it takes. None on a
    sheet that sets no heights, so a sheet Excel sizes for itself stays that way."""
    if src["height"] is None:
        return None
    lines = max(1, round(src["height"] / unit))
    return float(max(1, math.ceil(lines * length / max(1, len(src["text"])))) * unit)


def _sum_heights(*heights) -> float | None:
    """A merged row's height: the rows' heights added, and only when every one of them had one."""
    if any(h is None for h in heights):
        return None
    return float(sum(heights))


def _estimator(ws, cols: dict[str, int], src: dict):
    """The timecode of a cut inside a turn, from where the cut falls in it.

    The seconds from this turn's timecode to the next turn's, whoever speaks it, are shared out by
    character offset and rounded to the second, never before this turn and never past the next.
    The last turn of a sheet has no next one, so it is taken to run 0.4 seconds a word.
    """
    t0 = src["seconds"]
    if t0 is None:
        return lambda offset: None
    t1 = None
    if src["row"] + 1 <= ws.max_row and "ts" in cols:
        t1 = ts_seconds(ws.cell(src["row"] + 1, cols["ts"]).value)
    if t1 is None or t1 < t0:
        t1 = t0 + math.ceil(SECONDS_PER_WORD * len(src["text"].split()))
    size = max(1, len(src["text"]))
    return lambda offset: min(t1, max(t0, t0 + round((t1 - t0) * offset / size)))


def _plan_assign(ws, cols: dict[str, int], row: int, to: str, start=None, end=None) -> dict:
    """What an assignment does to the sheet, worked out before anything is written.

    The answer names the block of rows it touches (`first`, how many rows it held before and how
    many after), the one insert or delete that moves the rows below it (`shift`), and every row
    of the block as it will be written. Nothing here writes.
    """
    row = int(row)
    if row < 2:
        raise WorkbookError(i18n.t("server.header_row_never_assigned"))
    if row > ws.max_row or _blank(ws, cols, row):
        raise WorkbookError(i18n.t("server.passage_row"))
    wanted = str(to or "").strip()
    if not wanted:
        raise WorkbookError(i18n.t("server.say_who_words_go"))
    # a name already on the sheet is taken as it is spelled there, whatever the case typed
    to = next((s for s in sheet_speakers(ws, cols) if s.lower() == wanted.lower()), wanted)
    src = _facts(ws, cols, row)
    if _norm(src["name"]) == _norm(to):
        raise WorkbookError(i18n.t("server.passage_already_s", name=src['name']))
    text, fonts = src["text"], src["fonts"]
    if not text.strip():
        raise WorkbookError(i18n.t("server.passage_words_assign"))
    whole = start is None and end is None
    if not whole:
        if start is None or end is None:
            raise WorkbookError(i18n.t("server.selection_needs_start_end"))
        start, end = snap_words(text, int(start), int(end))
        # a selection over every word of the turn is the whole turn
        whole = not text[:start].strip() and not text[end:].strip()
    prev = _facts(ws, cols, row - 1) if row - 1 >= 2 and not _blank(ws, cols, row - 1) else None
    nxt = _facts(ws, cols, row + 1) if row + 1 <= ws.max_row and not _blank(ws, cols, row + 1) else None
    joins_prev = prev is not None and _norm(prev["name"]) == _norm(to)
    joins_next = nxt is not None and _norm(nxt["name"]) == _norm(to)
    est = _estimator(ws, cols, src)
    unit = _line_unit(ws)
    plan = {"sheet": ws.title, "row": row, "from": src["name"], "to": to, "whole": whole,
            "start": None if whole else start, "end": None if whole else end,
            "template": src["ts_raw"] if src["ts_raw"] is not None else (nxt["ts_raw"] if nxt else None),
            "src": src, "prev": prev, "next": nxt}

    if whole:
        parts = ([prev] if joins_prev else []) + [src] + ([nxt] if joins_next else [])
        spec: dict = {"row": parts[0]["row"]}
        if not joins_prev:
            spec["name"] = to
        if len(parts) > 1:
            spec["value"] = _join_runs([(p["text"], p["fonts"]) for p in parts])
            spec["entries"] = {role: [e for p in parts for e in p["entries"].get(role, [])]
                               for role in ROLES if role in cols}
            if "kq" in spec["entries"]:
                spec["entries"]["kq"] = merged_quotes(parts)
            spec["height"] = _sum_heights(*(p["height"] for p in parts))
        if joins_prev:
            shift = {"at": row, "count": 2 if joins_next else 1, "inserted": False, "into": row - 1}
        elif joins_next:
            shift = {"at": row + 1, "count": 1, "inserted": False, "into": row}
        else:
            shift = None
        plan.update(kind="merge" if len(parts) > 1 else "assign", rows=[spec], shift=shift,
                    block={"first": parts[0]["row"], "before": len(parts), "after": 1},
                    merges=[p for p in parts if p is not src], holder=parts[0]["row"])
        return plan

    # the cut falls at the snapped edges, and the spaces there are trimmed, never invented
    pre_end = start
    while pre_end > 0 and text[pre_end - 1].isspace():
        pre_end -= 1
    post_start = end
    while post_start < len(text) and text[post_start].isspace():
        post_start += 1
    pre = (text[:pre_end], fonts[:pre_end])
    mid = (text[start:end], fonts[start:end])
    post = (text[post_start:], fonts[post_start:])
    has_pre, has_post = bool(pre[0].strip()), bool(post[0].strip())

    if has_pre and has_post:
        # three rows: the original speaker either side, the words between them
        rows = [{"row": row, "value": pre},
                {"row": row + 1, "style_from": row, "name": to, "ts": est(start), "value": mid,
                 "height": _share_height(src, len(mid[0]), unit)},
                {"row": row + 2, "style_from": row, "name": src["raw_name"], "ts": est(post_start),
                 "value": post, "height": _share_height(src, len(post[0]), unit)}]
        plan.update(kind="assign", rows=rows, merges=[], holder=row,
                    shift={"at": row + 1, "count": 2, "inserted": True, "into": None},
                    block={"first": row, "before": 1, "after": 3})
    elif has_pre:
        # the words end the turn: they stand after it, or open the next turn when that is theirs
        if joins_next:
            rows = [{"row": row, "value": pre},
                    {"row": row + 1, "ts": est(start), "value": _join_runs([mid, (nxt["text"], nxt["fonts"])]),
                     "height": _sum_heights(nxt["height"], _share_height(src, len(mid[0]), unit))}]
            plan.update(kind="merge", rows=rows, merges=[nxt], holder=row, shift=None,
                        block={"first": row, "before": 2, "after": 2})
        else:
            rows = [{"row": row, "value": pre},
                    {"row": row + 1, "style_from": row, "name": to, "ts": est(start), "value": mid,
                     "height": _share_height(src, len(mid[0]), unit)}]
            plan.update(kind="assign", rows=rows, merges=[], holder=row,
                        shift={"at": row + 1, "count": 1, "inserted": True, "into": None},
                        block={"first": row, "before": 1, "after": 2})
    else:
        # the words start the turn: they stand before it, keeping its timecode, or close the turn
        # before when that is theirs. The rest keeps the speaker, the annotations and the flag.
        if joins_prev:
            rows = [{"row": row - 1, "value": _join_runs([(prev["text"], prev["fonts"]), mid]),
                     "height": _sum_heights(prev["height"], _share_height(src, len(mid[0]), unit))},
                    {"row": row, "ts": est(post_start), "value": post}]
            plan.update(kind="merge", rows=rows, merges=[prev], holder=row, shift=None,
                        block={"first": row - 1, "before": 2, "after": 2})
        else:
            rows = [{"row": row, "style_from": row + 1, "name": to, "ts": src["seconds"], "value": mid,
                     "height": _share_height(src, len(mid[0]), unit)},
                    {"row": row + 1, "ts": est(post_start), "value": post}]
            plan.update(kind="assign", rows=rows, merges=[], holder=row + 1,
                        shift={"at": row, "count": 1, "inserted": True, "into": None},
                        block={"first": row, "before": 1, "after": 2})
    return plan


def _copy_row_style(ws, src_row: int, dst_row: int) -> None:
    """Every cell of a new row takes the style of the cell above or below it that it was cut from,
    the way create_from_source styles the rows it writes. The fill is the one thing never copied."""
    for c in range(1, ws.max_column + 1):
        s, d = ws.cell(src_row, c), ws.cell(dst_row, c)
        if not s.has_style:
            continue
        d.font = copy.copy(s.font)
        d.alignment = copy.copy(s.alignment)
        d.border = copy.copy(s.border)
        d.protection = copy.copy(s.protection)
        d.number_format = s.number_format


def _apply_plan(ws, cols: dict[str, int], plan: dict) -> None:
    shift = plan["shift"]
    if shift:
        if shift["inserted"]:
            ws.insert_rows(shift["at"], shift["count"])
        else:
            ws.delete_rows(shift["at"], shift["count"])
        _shift_row_heights(ws, shift["at"], shift["count"], inserted=shift["inserted"])
    for spec in plan["rows"]:
        r = spec["row"]
        if spec.get("style_from"):
            _copy_row_style(ws, spec["style_from"], r)
        if spec.get("name") is not None:
            ws.cell(r, cols["name"]).value = spec["name"]
        if spec.get("ts") is not None and "ts" in cols:
            _write_timecode(ws, cols, r, spec["ts"], plan["template"])
        if spec.get("value") is not None:
            ws.cell(r, cols["transcript"]).value = _rebuild(*spec["value"])
        for role, entries in (spec.get("entries") or {}).items():
            cell = ws.cell(r, cols[role])
            # a cell whose entries come out the same is left exactly as it was, spacing and all
            if split_entries(cell.value) != entries:
                cell.value = join_entries(entries)
        if spec.get("height") is not None:
            ws.row_dimensions[r].height = spec["height"]


def _block_texts(ws, cols: dict[str, int], first: int, count: int) -> list[str]:
    return [plain_text(ws.cell(r, cols["transcript"]).value) for r in range(first, first + count)]


def assign_preview(path: Path, sheet: str, row: int, to: str, start=None, end=None, form: str | None = None) -> dict:
    """What an assignment would merge and carry, without touching anything. The confirm card for a
    whole turn is drawn from this, its times as `form` says, by default as the project's timecodes say."""
    path = Path(path)
    form = form or timecodes_for(path)
    wb = openpyxl.load_workbook(path, rich_text=True)
    try:
        ws, cols = _transcript_sheet(wb, sheet, path)
        plan = _plan_assign(ws, cols, row, to, start, end)
    finally:
        wb.close()
    first, before = plan["block"]["first"], plan["block"]["before"]
    parts = [p for p in (plan["prev"], plan["src"], plan["next"]) if p and first <= p["row"] < first + before]
    counts = {role: sum(len([e for e in p["entries"].get(role, []) if not (role == "kq" and no_quote(e))])
                        for p in parts) for role in ROLES}
    return {"sheet": sheet, "row": plan["row"], "kind": plan["kind"], "whole": plan["whole"],
            "from": plan["from"], "to": plan["to"], "time": timecode(plan["src"]["seconds"], form),
            "merges": [{"row": p["row"], "name": p["name"], "time": timecode(p["seconds"], form)} for p in plan["merges"]],
            "rows": [p["row"] for p in parts], "counts": counts, "block": plan["block"]}


def assign_rows(path: Path, sheet: str, row: int, to: str, start=None, end=None) -> dict:
    """Assign the words `[start, end)` of one turn, or the whole turn, to the speaker `to`.

    The selection is widened to whole words. A cut inside a turn makes a row of the new speaker,
    with the original speaker's rows either side where there are words either side, and the new
    row takes a timecode estimated from where the cut falls. The statements, key quotes, notes and
    flag stay with the first row that keeps the original speaker. A row landing beside a turn of the
    same speaker merges with it: the texts join with one space in sheet order, every run and every
    annotation is kept, and the first row's timecode stands.

    Rows are inserted or deleted in place. The header row is never touched, widths, freeze panes
    and zoom are kept, custom row heights move with their rows, and no cell gains a fill. The
    workbook is copied into `_Archive` before a row moves, and that copy is what `restore_rows`
    puts the block back from.
    """
    path = Path(path)
    guard_lock(path)
    wb = openpyxl.load_workbook(path, rich_text=True)
    try:
        ws, cols = _transcript_sheet(wb, sheet, path)
        plan = _plan_assign(ws, cols, row, to, start, end)
        block = plan["block"]
        before_texts = _block_texts(ws, cols, block["first"], block["before"])
        backup = archive_copy(path, "pre-assign")
        _apply_plan(ws, cols, plan)
        after_texts = _block_texts(ws, cols, block["first"], block["after"])
        _atomic_save(wb, path)
    finally:
        wb.close()
    return {"sheet": sheet, "row": plan["row"], "kind": plan["kind"], "whole": plan["whole"],
            "start": plan["start"], "end": plan["end"], "from": plan["from"], "to": plan["to"],
            "block": dict(block, sheet=sheet), "shift": plan["shift"], "holder": plan["holder"],
            "merged": len(plan["merges"]), "before": before_texts, "after": after_texts,
            "backup": backup}


def _copy_cell(src, dst) -> None:
    """A cell put back from another workbook: its value, its rich text run for run, its style."""
    value = src.value
    dst.value = copy.deepcopy(value) if isinstance(value, CellRichText) else value
    if not src.has_style:
        dst._style = StyleArray()
        return
    dst.font = copy.copy(src.font)
    dst.fill = copy.copy(src.fill)
    dst.border = copy.copy(src.border)
    dst.alignment = copy.copy(src.alignment)
    dst.protection = copy.copy(src.protection)
    dst.number_format = src.number_format


def restore_rows(path: Path, sheet: str, first: int, before: int, after: int, backup: Path,
                 target: int, expect: list[str] | None = None) -> dict:
    """Undo an assignment: the rows it made go, and the rows it replaced come back from its backup.

    `first`, `before` and `after` are the block the assignment answered with. The rows
    `[first, first + after)` are replaced by rows `[first, first + before)` of the backup, cell for
    cell, value, rich text and style, and their heights with them. Anything written into the
    block since the assignment, a statement, a key quote or a note that the backup does not hold,
    is appended to row `target`, the turn the assignment was made on, so nothing is dropped.

    `expect` is the text of the block as the assignment left it. A block that reads differently
    now has been changed some other way, and it is refused rather than overwritten.
    """
    path, backup = Path(path), Path(backup)
    guard_lock(path)
    first, before, after, target = int(first), int(before), int(after), int(target)
    if first < 2:
        raise WorkbookError(i18n.t("server.header_row_never_restored_over"))
    if not backup.exists():
        raise WorkbookError(i18n.t("server.backup_undo_needs_gone_from", name=backup.name))
    if backup.resolve().parent != (case_folder(path) / "_Archive").resolve():
        raise WorkbookError(i18n.t("server.backup_does_belong_participant"))
    wb = openpyxl.load_workbook(path, rich_text=True)
    bk = openpyxl.load_workbook(backup, rich_text=True)
    try:
        ws, cols = _transcript_sheet(wb, sheet, path)
        if sheet not in bk.sheetnames:
            raise WorkbookError(i18n.t("server.backup_sheet_called", sheet=sheet))
        bws = bk[sheet]
        if expect is not None and _block_texts(ws, cols, first, after) != list(expect):
            raise WorkbookError(i18n.t("server.those_rows_have_changed_since"))
        # what the block holds now that the backup does not: written since, and kept
        was = {role: [e for r in range(first, first + before) for e in split_entries(bws.cell(r, cols[role]).value)]
               for role in ROLES if role in cols}
        extras: dict[str, list[str]] = {role: [] for role in was}
        for r in range(first, first + after):
            for role in was:
                for entry in split_entries(ws.cell(r, cols[role]).value):
                    if entry in was[role]:
                        was[role].remove(entry)
                    elif not (role == "kq" and no_quote(entry)):
                        # "(no quote)" holds a place the merge gave it, and is never a quote written since
                        extras[role].append(entry)
        if after > before:
            ws.delete_rows(first + before, after - before)
            _shift_row_heights(ws, first + before, after - before)
        elif before > after:
            ws.insert_rows(first + after, before - after)
            _shift_row_heights(ws, first + after, before - after, inserted=True)
        width = max(ws.max_column, bws.max_column)
        for r in range(first, first + before):
            for c in range(1, width + 1):
                _copy_cell(bws.cell(r, c), ws.cell(r, c))
            height = bws.row_dimensions[r].height if r in bws.row_dimensions else None
            if height is not None:
                ws.row_dimensions[r].height = height
            elif r in ws.row_dimensions:
                ws.row_dimensions[r].height = None
        appended = 0
        for role, lines in extras.items():
            if lines:
                cell = ws.cell(target, cols[role])
                cell.value = join_entries(split_entries(cell.value) + lines)
                appended += len(lines)
        _atomic_save(wb, path)
        texts = _block_texts(ws, cols, first, before)
    finally:
        wb.close()
        bk.close()
    return {"sheet": sheet, "first": first, "before": before, "after": after, "restored": before,
            "appended": appended, "texts": texts, "target": target}


def case_folder(path: Path) -> Path:
    """The case folder a workbook belongs to: its own folder, or the parent of a Source folder."""
    path = Path(path)
    return path.parent.parent if path.parent.name == "Source" else path.parent


def case_lock(workbook: Path) -> Path:
    """The lock of a case's files, in its `Working/` folder beside the progress file, for its
    workbook and for a raw source in its `Source/` alike (the family codebase's fourth build, 22 October
    2026, from locks.py, whose lock it is, the case's folder being Idiograph's)."""
    return case_folder(Path(workbook)) / "Working" / locks.NAME


# Working together's one writer (wtowners, 8 November 2026): set by team_sync when the routes load, a call that
# refuses a write to a participant this install does not own, before the case's lock is taken
WRITE_GUARD = None
# a block that writes a participant's boards and nothing else (ownboards, 9 November 2026): a reviewer's own boards of
# a participant someone else works on are kept apart in his copy (themes.OWN_FILE), so the block passes the case's
# lock, and a save of the workbook or the progress file inside it is still refused (`boards_pass_check`)
BOARDS_ONLY: contextvars.ContextVar = contextvars.ContextVar("idiograph_boards_only", default=False)


def boards_pass_check(path: Path) -> None:
    """Inside a boards-only block, the one writer's refusal for a write of anything but the boards."""
    if WRITE_GUARD is not None and BOARDS_ONLY.get():
        WRITE_GUARD(Path(path))


@contextlib.contextmanager
def _boards_block(held):
    token = BOARDS_ONLY.set(True)
    try:
        with held:
            yield
    finally:
        BOARDS_ONLY.reset(token)


def case_held(workbook: Path, wait: float | None = None, export: bool = False, boards: bool = False):
    """The lock of a case's files, held for the block (`locks.held`): the one place every write to a participant's
    files passes, the app's and the command line's, so `WRITE_GUARD` refuses here a write to a participant another
    member of the team works on. An export, which reads the participant and writes a file of its own beside, passes
    `export` and is not refused. A board op passes `boards`: the boards' own writer (`themes.write`) then keeps a
    reviewer's own boards apart and refuses a change to the owner's, and the block is `BOARDS_ONLY`."""
    if WRITE_GUARD is not None and not export and not boards and not BOARDS_ONLY.get():
        WRITE_GUARD(Path(workbook))
    held = locks.held(case_lock(workbook), wait)
    return _boards_block(held) if boards else held


def suggested_output(source: Path) -> Path:
    """`P<n> <Pseudonym> - EN & ES.xlsx` in the case folder, read off the folder name."""
    folder = case_folder(source)
    m = re.match(r"(P\d+)\s*-\s*([^-]+)", folder.name)
    if m:
        stem = f"{m.group(1)} {m.group(2).strip().split('-')[0].strip()}"
    else:
        stem = re.sub(r"\s*v\d+\s*$", "", Path(source).stem).replace(" - ", " ")
    return folder / f"{stem} - EN & ES.xlsx"


def __getattr__(name: str) -> str:
    """The refusals other modules and the checks name as this module's, each read in the run's language when
    asked for (the text layer, 28 October 2026)."""
    said = {
        "STALE_LINE": lambda: i18n.t("server.passage_changed_since_page_loaded"),
        "EMPTY_FIND": lambda: i18n.t("server.type_words_find_first"),
        "FIND_MOVED": lambda: i18n.t("server.occurrence_longer_where_nothing_written"),
        "REPLACE_MOVED": lambda: i18n.t("server.passage_replace_changed_reads_differently"),
        "NOT_INTERVIEWER": lambda: i18n.t("server.interviewer_notes_belong_interviewer_s"),
        "EMPTY_STATEMENT": lambda: i18n.t("server.statement_cannot_left_empty_esc"),
        "NO_STATEMENT": lambda: i18n.t("server.statement_longer_workbook_nothing_written"),
        "STATEMENT_MOVED": lambda: i18n.t("server.statement_reads_differently_workbook_now"),
    }
    if name in said:
        return said[name]()
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
