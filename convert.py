#!/usr/bin/env python3
"""A transcript in the shape a recorder or a service gave it, read into turns for the import card.

Each reader is a pure function from the file's text, or from a table's rows, to turns, each turn
`(name, seconds or None, text)`. The card shows the first of them, and Make writes them as a raw
source, the three columns `create_from_source` reads, beside the file in the case's `Source/`.

    VTT and SRT   cues by their start times, the speaker from a `<v Name>` tag or a leading
                  `Name:`, the cues of one speaker in a row merged into one turn at the first
                  cue's time, and every cue its own row under `Speaker` when nobody is named
    plain text    a turn starts at a line opening with `Name:`, the lines after it carry it on,
                  and a time at its head, `[00:01:23]`, `00:01:23` or `1:23`, is the turn's time
    CSV, Excel    three columns mapped to Name, Timestamp and Transcript, guessed from the
                  headers, the times Excel times, `HH:MM:SS`, `MM:SS` or seconds
    Word          a `.docx` opened with zipfile and the standard library's XML parser, a
                  paragraph a line, then read as plain text is, so a label and a time at a
                  paragraph's head start a turn, as the file saved as plain text always read.
                  A body that is mostly a table of two columns or more is read a row a turn,
                  the transcript in one column and the exploratory notes beside it (`read_docx_table`)

Text is UTF-8 with or without a byte order mark, falling back to Windows-1252, and a Word file's
words are read as the family's `textfiles.py` reads them, which Trace shares. The standard library,
openpyxl and that module only, and nothing here writes but `write_sheets` and `add_sheets`.
"""
from __future__ import annotations

import csv
import datetime as dt
import html
import io
import os
import re
from pathlib import Path

import openpyxl

import i18n
import shared_strings  # noqa: F401  keeps a line feed a line feed on Windows, before any save
# the readers Trace shares, the family's since 22 October 2026 (family/textfiles.py), kept by these names here
from textfiles import (DOCX_MAX, HEADING_NAME, Unreadable, _FALLBACK, _NOT_WORDS, _W, _docx_body,  # noqa: F401
                       _level, _outline, _paragraphs, _style_level, _styles, _words_of, decode, docx_paragraphs,
                       docx_text, unreadable)

FORMATS = (".vtt", ".srt", ".txt", ".csv", ".xlsx", ".docx")
SPEAKER = "Speaker"            # the name a turn takes when the file names nobody
SHEET = "Transcript"           # the one sheet of a raw source made here
CONVERTED = " (converted)"     # the suffix an Excel file's raw source carries, so it never meets its own name
PREVIEW = 8                    # the turns the card shows


# ------------------------------------------------------------------ text

def _lines(text: str) -> list[str]:
    return text.replace("\r\n", "\n").replace("\r", "\n").split("\n")


def _squash(text: str) -> str:
    return " ".join(str(text).split())


# ------------------------------------------------------------------ times

CLOCK = r"(?:\d{1,2}:)?\d{1,3}:\d{2}(?:[.,]\d{1,3})?"
_CLOCK = re.compile(r"(?:(\d{1,2}):)?(\d{1,3}):(\d{2})(?:[.,]\d{1,3})?")
_NUMBER = re.compile(r"\d+(?:\.\d+)?")


def clock_seconds(text) -> int | None:
    """`HH:MM:SS`, `MM:SS` or `H:MM:SS.mmm`, in brackets or not, as whole seconds. A two-part clock
    may carry the hours in its minutes, `75:10`. Anything else is None."""
    m = _CLOCK.fullmatch(str(text).strip().strip("[]()"))
    if not m:
        return None
    hours, minutes, seconds = int(m.group(1) or 0), int(m.group(2)), int(m.group(3))
    if seconds >= 60 or (m.group(1) is not None and minutes >= 60):
        return None
    return hours * 3600 + minutes * 60 + seconds


def seconds_of(value) -> int | None:
    """A cell's time as whole seconds: an Excel time, date-time or duration, a number of seconds,
    or text a clock or a number. A blank or anything else is None."""
    if value is None or isinstance(value, bool):
        return None
    if isinstance(value, dt.datetime):
        return value.hour * 3600 + value.minute * 60 + value.second
    if isinstance(value, dt.time):
        return value.hour * 3600 + value.minute * 60 + value.second
    if isinstance(value, dt.timedelta):
        return max(0, int(value.total_seconds()))
    if isinstance(value, (int, float)):
        return int(value) if value >= 0 else None
    text = str(value).strip()
    if _NUMBER.fullmatch(text):
        return int(float(text))
    return clock_seconds(text)


# A table's Time column read by its format (Adam, 20 October: "auto detect, or manually set if
# necessary, or manually override the format"). Found from what the column holds, and set by hand on
# the card, which then reads each time strictly in that format, so a time it cannot read is named and
# never silently dropped. Frames are counted at the frame rate given, 25 a second unless he says.
# Each format is named by an example of it, never by letters (Adam, 20 October), and a time with a
# fraction of a second and one without read each other, since the fraction is dropped either way.
TIME_FORMATS = {"hms": "1:02:03", "ms": "02:03", "fraction": "1:02:03.5", "seconds": "62.5 seconds",
                "frames": "1:02:03:12, frames"}
_ONE_CLOCK = {"hms": "fraction", "fraction": "hms"}
EXCEL_TIME = "excel"                # a cell Excel holds as a time, read whatever the format chosen
TIME_NAMES = dict(TIME_FORMATS, excel="Excel time")
FRAME_RATE = 25
_FRAMES = re.compile(r"(\d{1,2}):(\d{2}):(\d{2})[:;](\d{1,3})")
_HMS = re.compile(r"(\d{1,3}):(\d{2}):(\d{2})([.,]\d+)?")
_MS = re.compile(r"(\d{1,4}):(\d{2})(?:[.,]\d+)?")
_SECONDS = re.compile(r"\d+(?:[.,]\d+)?")


def _bare(value) -> str:
    return str(value).strip().strip("[]()").strip()


def time_kind(value) -> str | None:
    """The format one cell's time is written in: hms, fraction, ms, seconds, frames or excel, or None for a
    blank or anything no format reads. Brackets round it and a fraction after a full stop or a comma,
    as SRT and VTT write them, are taken in."""
    if value is None or isinstance(value, bool):
        return None
    if isinstance(value, (dt.datetime, dt.time, dt.timedelta)):
        return EXCEL_TIME
    if isinstance(value, (int, float)):
        return "seconds" if value >= 0 else None
    text = _bare(value)
    m = _FRAMES.fullmatch(text)
    if m:
        return "frames" if int(m.group(2)) < 60 and int(m.group(3)) < 60 else None
    m = _HMS.fullmatch(text)
    if m:
        if int(m.group(2)) >= 60 or int(m.group(3)) >= 60:
            return None
        return "fraction" if m.group(4) else "hms"
    m = _MS.fullmatch(text)
    if m:
        return "ms" if int(m.group(2)) < 60 else None
    return "seconds" if _SECONDS.fullmatch(text) else None


def time_found(values) -> str | None:
    """The format a column's times are written in, the one most of them take, a column of three-part
    and two-part times taken as three-part, or None for a column with no time in it."""
    kinds = [k for k in (time_kind(v) for v in values) if k]
    if not kinds:
        return None
    if "ms" in kinds and ("hms" in kinds or "fraction" in kinds):
        kinds = [k for k in kinds if k != "ms"]
    return max(dict.fromkeys(kinds), key=kinds.count)


def frame_rate(value) -> int:
    """The frames a second a frame count is read at, a whole number from 1 to 120, 25 when none is given."""
    try:
        rate = int(float(str(value).replace(",", ".")))
    except (TypeError, ValueError):
        return FRAME_RATE
    return rate if 1 <= rate <= 120 else FRAME_RATE


def time_seconds(value, fmt: str = "", fps: int = FRAME_RATE) -> int | None:
    """A cell's time as whole seconds, by the format chosen, or with none by its own. A time in
    another format than the one chosen is None, so is a frame count at or past the frame rate. An
    Excel time is read whatever the format."""
    kind = time_kind(value)
    if kind is None or (fmt in TIME_FORMATS and kind not in (fmt, _ONE_CLOCK.get(fmt), EXCEL_TIME)):
        return None
    if kind == EXCEL_TIME:
        return seconds_of(value)
    if isinstance(value, (int, float)):
        return int(value)
    text = _bare(value)
    if kind == "seconds":
        return int(float(text.replace(",", ".")))
    if kind == "frames":
        h, m, s, f = (int(g) for g in _FRAMES.fullmatch(text).groups())
        return h * 3600 + m * 60 + s if f < frame_rate(fps) else None
    parts = [int(p) for p in re.split(r"[.,]", text)[0].split(":")]
    if kind in ("hms", "fraction"):
        return parts[0] * 3600 + parts[1] * 60 + parts[2]
    return parts[0] * 60 + parts[1]


def timing_of(given) -> dict:
    """The card's or an agent's choice of how a Time column is read, `{"format", "fps"}`, the format
    "" for the one found."""
    given = given if isinstance(given, dict) else {}
    fmt = str(given.get("format") or "").strip().lower()
    return {"format": fmt if fmt in TIME_FORMATS else "", "fps": frame_rate(given.get("fps"))}


# --------------------------------------------------------------- speakers

# A speaker label is a name of up to four words, each opening on a capital or a digit, with the
# small words of a surname allowed between them. The words a document's head uses for its fields
# never are, nor the transcriber's bracketed marks.
NAME = r"[^\W\d_][\w'’.\-]*(?:[ \t]+[\w'’.\-]+){0,3}"
PARTICLES = {"de", "da", "di", "del", "della", "dos", "das", "du", "van", "von", "der", "den", "la", "le",
             "al", "el", "bin", "ibn", "y", "e"}
NOT_NAMES = {"date", "time", "duration", "location", "place", "title", "subject", "note", "notes",
             "transcript", "transcription", "recording", "interview", "participants", "attendees",
             "present", "file", "audio", "source", "language", "re", "ps", "http", "https", "www",
             "inaudible", "laughter", "laughs", "crosstalk", "pause", "silence", "music", "noise",
             "unclear", "background", "summary", "keywords", "speakers", "meeting", "started", "ended"}
_LABELS = [
    # [00:01:23] Name: words, or 00:01:23 - Name: words
    re.compile(rf"^\s*[\[(]?(?P<time>{CLOCK})[\])]?\s*[-–|]?\s*(?P<name>{NAME})\s*:(?:\s+|$)(?P<text>.*)$"),
    # Name (00:01:23): words, or Name [00:01:23] on a line of its own
    re.compile(rf"^\s*(?P<name>{NAME})\s*[\[(](?P<time>{CLOCK})[\])]\s*:?(?:\s+|$)(?P<text>.*)$"),
    # [Name] 00:01:23 words, as a saved meeting transcript has it
    re.compile(rf"^\s*\[(?P<name>{NAME})\]\s+(?P<time>{CLOCK})\s*:?(?:\s+|$)(?P<text>.*)$"),
    # Name: words, or Name: [00:01:23] words
    re.compile(rf"^\s*(?P<name>{NAME})\s*:(?:\s+|$)(?:[\[(]?(?P<time>{CLOCK})[\])]?(?:\s+|$))?(?P<text>.*)$"),
    # Name   0:03 on a line of its own, as a Word transcript saved as text has it
    re.compile(rf"^\s*(?P<name>{NAME})[ \t]+(?P<time>{CLOCK})\s*$"),
]


def good_name(name: str) -> bool:
    words = name.split()
    if not words or len(words) > 4 or len(name) > 40 or name.lower().rstrip(".") in NOT_NAMES:
        return False
    return all(w[0].isupper() or w[0].isdigit() or w in PARTICLES for w in words) and words[0][0].isupper()


def label_of(line: str):
    """A line that opens a turn, as `(name, seconds or None, the words after it)`, or None."""
    for pattern in _LABELS:
        m = pattern.match(line)
        if m and good_name(m.group("name").strip()):
            time = m.group("time")
            return (_squash(m.group("name")), (clock_seconds(time) if time else None),
                    (m.groupdict().get("text") or "").strip())
    return None


def _named(labels, twice: bool = True) -> set[str]:
    """The names that open lines. In plain text only those that open at least two, or one with a
    time beside the name, which a line of reported speech never has, and a file where none does
    takes every name. A cue is a unit of its own, so a subtitle file takes every name."""
    counts: dict[str, int] = {}
    timed: set[str] = set()
    for found in labels:
        if found:
            counts[found[0]] = counts.get(found[0], 0) + 1
            if found[1] is not None:
                timed.add(found[0])
    again = {n for n, c in counts.items() if c >= 2} | timed
    return (again if twice else set()) or set(counts)


_LEAD = re.compile(rf"^\s*[\[(]?(?P<time>{CLOCK})[\])]?(?:\s+|$)")


def _lead_time(text: str) -> tuple[int | None, str]:
    """A time at the head of a paragraph with no speaker, and the words after it."""
    m = _LEAD.match(text)
    if not m:
        return None, text
    return clock_seconds(m.group("time")), text[m.end():].strip()


# ------------------------------------------------------------- VTT and SRT

_TAG = re.compile(r"<[^>]*>")
_ASS = re.compile(r"\{\\[^}]*\}")
_VOICE = re.compile(r"<v(?:\.[^\s>]*)?(?:\s+([^>]*))?>")
_TIMING = re.compile(rf"^\s*(?P<start>{CLOCK})\s*-->\s*(?P<end>{CLOCK})")


def _clean(text: str) -> str:
    return _squash(html.unescape(_ASS.sub("", _TAG.sub("", text))))


def read_cues(text: str) -> list[tuple[str | None, int, str]]:
    """Every cue as `(speaker or None, start seconds, words)`, a cue with several voices as several.

    Blocks are cut at blank lines. The header, `NOTE`, `STYLE` and `REGION` blocks and anything
    with no timing line are passed over. A cue's identifier, its end time and its settings are
    dropped, and so are its inline tags.
    """
    cues = []
    for block in re.split(r"\n[ \t]*\n", "\n".join(_lines(text))):
        lines = [ln for ln in block.split("\n") if ln.strip()]
        if not lines or lines[0].lstrip("﻿").startswith(("WEBVTT", "NOTE", "STYLE", "REGION")):
            continue
        at = next((i for i, ln in enumerate(lines) if _TIMING.match(ln)), None)
        if at is None:
            continue
        start = clock_seconds(_TIMING.match(lines[at]).group("start"))
        body = "\n".join(lines[at + 1:])
        voices = list(_VOICE.finditer(body))
        parts = []
        if voices:
            if body[:voices[0].start()].strip():
                parts.append((None, body[:voices[0].start()]))
            for i, v in enumerate(voices):
                end = voices[i + 1].start() if i + 1 < len(voices) else len(body)
                parts.append((_squash(v.group(1) or "") or None, body[v.end():end]))
        else:
            parts.append((None, body))
        for voice, words in parts:
            cues.append((voice, start, words))
    return cues


def read_vtt(text: str) -> list[tuple[str, int | None, str]]:
    """A WebVTT file as turns: Teams names its speakers in `<v Name>`, Zoom with a leading
    `Name:`, and the cues of one speaker in a row become one turn at the first cue's time."""
    raw = read_cues(text)
    # a cue named by its tag is taken as named. One without a tag is looked at line by line, and
    # a line opening with a speaker label starts a piece of that name
    lines = [(voice, start, ln) for voice, start, words in raw for ln in words.split("\n")]
    names = _named((label_of(_clean(ln)) for voice, _, ln in lines if voice is None), twice=False)
    pieces: list[list] = []
    for voice, start, words in raw:
        if voice is not None:
            pieces.append([voice, start, _clean(words)])
            continue
        current = [None, start, ""]
        pieces.append(current)
        for ln in words.split("\n"):
            found = label_of(_clean(ln))
            if found and found[0] in names:
                current = [found[0], start, found[2]]
                pieces.append(current)
            else:
                current[2] = _squash(f"{current[2]} {_clean(ln)}")
    pieces = [p for p in pieces if p[2]]
    if not any(p[0] for p in pieces):
        return [(SPEAKER, start, words) for _, start, words in pieces]
    turns: list[list] = []
    for name, start, words in pieces:
        if name is None:
            name = turns[-1][0] if turns else SPEAKER
        if turns and turns[-1][0] == name:
            turns[-1][2] = f"{turns[-1][2]} {words}"
        else:
            turns.append([name, start, words])
    return [tuple(t) for t in turns]


read_srt = read_vtt                      # the same blocks, a comma before the milliseconds


# -------------------------------------------------------------- plain text

def read_plain(text: str) -> list[tuple[str, int | None, str]]:
    """Plain text as turns. A line opening with a speaker label starts a turn, with the time at its
    head when there is one, and every line after it carries the turn on. Lines before the first
    label are a turn of their own under `Speaker`, so nothing in the file is lost. A file with no
    label at all is one turn a paragraph, each with the time at its head when there is one."""
    if text.lstrip("﻿ \t\r\n").startswith("WEBVTT"):
        return read_vtt(text)
    lines = _lines(text)
    head = [ln for ln in lines if ln.strip()][:3]
    if len(head) >= 2 and head[0].strip().isdigit() and _TIMING.match(head[1]):
        return read_srt(text)
    found = [label_of(ln) for ln in lines]
    names = _named(found)
    if not names:
        paragraphs = [_squash(p) for p in re.split(r"\n[ \t]*\n", "\n".join(lines)) if p.strip()]
        if len(paragraphs) == 1:
            paragraphs = [_squash(ln) for ln in lines if ln.strip()]
        rows = [(SPEAKER,) + _lead_time(p) for p in paragraphs]
        return [(name, seconds, words) for name, seconds, words in rows if words]
    turns: list[list] = []
    for line, label in zip(lines, found):
        if label and label[0] in names:
            turns.append([label[0], label[1], label[2]])
        elif line.strip():
            if not turns:
                turns.append([SPEAKER, None, ""])
            turns[-1][2] = _squash(f"{turns[-1][2]} {line}")
    return [tuple(t) for t in turns if t[2]]


# ------------------------------------------------------------------ Word

# A Word table of transcript and notes, as the IPA book lays one out (Smith, Flowers and Larkin 2022,
# pp. 79-85) and a tester's Figure 1 shows (19 October): the transcript in one column, the exploratory
# notes beside it at the level of the words they are about, a new row at each change of speaker, and
# in the book's three-column layout the experiential statements in a third.
# The notes are also found under the words an analyst gives them elsewhere, Thoughts, Memo or Memos,
# Reflections and Reflexive notes (20 October), the card's guess alone, which he can change.
NOTE_STEMS = ("note", "comment", "explor", "thought", "memo", "reflect", "reflexi")
STATEMENT_STEMS = ("statement", "experien", "emergent theme")
ORDINALS = ("first", "second", "third", "fourth", "fifth", "sixth", "seventh", "eighth")


_WRAPS = (_W + "sdt", _W + "sdtContent", _W + "customXml", _W + "smartTag")
RAW_NOTES = "Notes"                    # a raw source's column of exploratory notes from a Word table
RAW_STATEMENTS = "Statements"          # and of experiential statements (workbook.RAW_EXTRAS reads both)
RAW_INTERVIEWER = "Interviewer notes"  # and of notes on the interviewer's turns, workbook.NOTE_HEADER
# and of quotes, a line a quote, which `create_from_source` pairs with the statements by order (ayabuild12, 9
# November 2026). Never "Quote" or "Quotes", which `workbook.ROLE_TESTS` reads as an annotated workbook's column.
RAW_QUOTES = "Quote lines"
QUOTE_KEYS = ("quote", "quotes", "key quote", "key quotes", "kq")
# what a column may bring beside the words: exploratory notes, experiential statements and quotes
EXTRAS = ("en", "es", "kq")


def _children(el, tags):
    """An element's own children of the tags given, in order, a content control's taken as its own."""
    for child in el:
        if child.tag in tags:
            yield child
        elif child.tag in _WRAPS:
            yield from _children(child, tags)


def _rows_of(tbl) -> list[list[list[str]]]:
    """A table's rows, each a list of its grid's columns, each the lines of that cell. A cell
    spanning several columns is its first's, and the rest are empty."""
    rows = []
    for tr in _children(tbl, (_W + "tr",)):
        cells: list[list[str]] = []
        for tc in _children(tr, (_W + "tc",)):
            pr = tc.find(_W + "tcPr")
            span = pr.find(_W + "gridSpan") if pr is not None else None
            try:
                span = max(1, min(20, int(span.get(_W + "val")))) if span is not None else 1
            except (TypeError, ValueError):
                span = 1
            paragraphs: list[str] = []
            _paragraphs(tc, paragraphs)
            cells.append([ln for p in paragraphs for ln in p.split("\n")])
            cells.extend([] for _ in range(span - 1))
        rows.append(cells)
    return rows


def _has_words(line: str) -> bool:
    """A line with a letter or a digit in it, so a dot or a dash kept to hold a note's level is none."""
    return any(ch.isalnum() for ch in line)


def _head_role(key: str) -> str | None:
    """What a Word table's heading names: the transcript, the exploratory notes, the experiential
    statements, the speaker or the time, or None."""
    if not key:
        return None
    if key in HEADERS["text"] or "transcript" in key:
        return "text"
    if key == "es" or any(s in key for s in STATEMENT_STEMS):
        return "es"
    if key in QUOTE_KEYS or key.endswith((" quotes", " quote")):
        return "kq"
    if key == "en" or any(s in key for s in NOTE_STEMS):
        return "en"
    if key in HEADERS["name"]:
        return "name"
    if key in HEADERS["ts"]:
        return "ts"
    return None


def _cell_text(lines) -> str:
    return _squash(" ".join(lines))


def read_docx_table(root, mapping=None, timing=None) -> dict | None:
    """A Word file whose body is mostly a table of two columns or more, read a row a turn: the
    transcript column's words, a `Name:` and a time at the head of a row as plain text reads them,
    a row with no name carrying on the speaker before it, and beside each turn the lines of its
    notes cell, and of its statements cell when a heading names one. Columns are found by a heading
    row when there is one, Transcript, Notes, Exploratory notes, Comments, Experiential statements
    and the like, and else by what they hold: the transcript the column whose rows open with a name
    or whose lines run longest, the notes the fullest of the rest. A row is never split, and a row
    with notes and no transcript adds its notes to the turn before it. A separate Speaker or Time
    column is found by its heading, or by holding a few names or mostly times. `mapping` is the
    card's choice of a role a column (see `choose`), which takes the place of the guess, and `timing`
    how its Time column is read (see `timing_of`). Answers
    `turns`, `notes`, a `{"en", "es"}` of lines joined by line breaks for each turn, `left`, a line
    for each column and for the words outside the table that are left out, and the table's
    `headers`, `mapping`, `roles` and `said` as `read_data` answers a spreadsheet's, or None for a
    body that is no such table and no mapping given, which is read as paragraphs as before."""
    body = root.find(_W + "body")
    if body is None:
        return None
    tables, outside = [], 0
    for block in _children(body, (_W + "tbl", _W + "p")):
        if block.tag == _W + "tbl":
            tables.append(_rows_of(block))
        else:
            words: list[str] = []
            _paragraphs([block], words)
            outside += len(_squash(" ".join(words)))
    wide = [t for t in tables if t and max(len(r) for r in t) >= 2]
    if not wide:
        return None
    width = max(len(r) for r in wide[0])
    kept = [t for t in wide if max(len(r) for r in t) == width]
    size = lambda t: sum(len(_cell_text(c)) for r in t for c in r)
    outside += sum(size(t) for t in tables if not any(t is k for k in kept))
    inside = sum(size(t) for t in kept)
    if not inside or inside < outside:
        return None
    rows = [r + [[] for _ in range(width - len(r))] for t in kept for r in t]
    keys = [_header_key(_cell_text(c)) for c in rows[0]]
    roles = [_head_role(k) for k in keys]
    header = any(r in ("text", "en", "es") for r in roles) and all(len(k) <= 60 for k in keys)
    heads = [_cell_text(c) for c in rows[0]] if header else [""] * width
    if header:
        rows = [r for r in rows[1:] if [_header_key(_cell_text(c)) for c in r] != keys]
    guess: dict = {role: None for role in ROLES}
    for i, role in enumerate(roles if header else []):
        if role and guess[role] is None:
            guess[role] = i
    firsts = lambda i: [next((ln for ln in r[i] if ln.strip()), "") for r in rows]
    taken = lambda: {v for v in guess.values() if v is not None}
    if guess["ts"] is None:
        timed = [i for i in range(width) if i not in taken() and not heads[i] and _timed([v for v in firsts(i) if v.strip()])]
        if timed:
            guess["ts"] = timed[0]
    if guess["text"] is None:
        free = [i for i in range(width) if i not in taken()]
        if not free:
            return None

        def score(i):
            lines = [ln for r in rows for ln in r[i] if ln.strip()]
            labelled = sum(1 for ln in firsts(i) if ln and label_of(ln))
            return (labelled, sum(len(ln) for ln in lines) / max(1, len(lines)), -i)
        guess["text"] = max(free, key=score)
    if guess["name"] is None:
        named = [i for i in range(width) if i not in taken() and not heads[i] and _names([_cell_text(r[i]) for r in rows])]
        if named:
            guess["name"] = named[0]
    if guess["en"] is None:
        free = [i for i in range(width) if i not in taken() and not heads[i]]
        fullness = {i: sum(len(_cell_text(r[i])) for r in rows) for i in free}
        if free and max(fullness.values()):
            guess["en"] = max(free, key=lambda i: (fullness[i], -i))
    shown = [heads[i] or f"Column {i + 1}" for i in range(width)]
    cols, chosen, said = choose(guess, mapping, width)
    timing = timing_of(timing)
    time_was = time_found([_cell_text(r[cols["ts"]]) for r in rows]) if cols["ts"] is not None else None
    bad: list[dict] = []
    turns: list[tuple] = []
    notes: list[dict] = []
    if cols["text"] is not None:
        t = cols["text"]
        found = [label_of(ln) if ln else None for ln in firsts(t)]
        names = _named(found)
        last = SPEAKER
        for row, label in zip(rows, found):
            lines = [ln.strip() for ln in row[t] if ln.strip()]
            extra = {role: [_squash(ln) for ln in row[cols[role]] if _has_words(ln)] if cols[role] is not None else []
                     for role in EXTRAS}
            words = ""
            if lines:
                if label and label[0] in names:
                    who, seconds, head = label
                else:
                    who = last
                    seconds, head = _lead_time(lines[0])
                if cols["name"] is not None and _cell_text(row[cols["name"]]):
                    who = _cell_text(row[cols["name"]])
                given = _cell_text(row[cols["ts"]]) if cols["ts"] is not None else ""
                if given:
                    at = time_seconds(given, timing["format"], timing["fps"])
                    if at is None:
                        bad.append({"passage": len(turns) + 1, "time": given})
                    else:
                        seconds = at
                words = _squash(" ".join([head] + lines[1:]))
            if not words:
                if notes:
                    for role in EXTRAS:
                        notes[-1][role] += extra[role]
                continue
            last = who
            turns.append((who, seconds, words))
            notes.append(extra)
    if not turns and mapping is None:
        return None
    left = left_out(shown, [bool(h) for h in heads], chosen, [any(_cell_text(r[i]) for r in rows) for i in range(width)])
    if outside:
        left.append(i18n.t("server.words_outside_table_left_out"))
    return {"turns": turns, "notes": [{role: "\n".join(lines) for role, lines in n.items()} for n in notes],
            "left": left, "headers": shown, "mapping": cols, "roles": chosen, "said": said,
            "time_found": time_was, "timing": timing, "bad_times": bad}


# The roles a column of a table can take on the import card (Adam, 19 October: "column matching" for
# Word tables and spreadsheets alike), each column of a Word table, an Excel file or a CSV given one
# at its head, or left out.
# Since 9 November 2026 (ayabuild12, the Ayahuasca plan's build 1) a column may be the quotes, a line a quote,
# each paired with the statement on the same line of the row's statements cell.
ROLES = ("name", "ts", "text", "en", "es", "kq")
ROLE_NAMES = {"name": "Speaker", "ts": "Time", "text": "Transcript", "en": "Exploratory notes",
              "es": "Experiential statements", "kq": "Quote"}
NO_TRANSCRIPT = i18n.t("server.choose_column_holds_transcript")


def _timed(values) -> bool:
    """Whether most of a column's entries are times, so it is the passages' times."""
    return bool(values) and sum(time_kind(v) is not None for v in values) >= 0.6 * len(values)


def _names(values) -> bool:
    """Whether a column holds speakers' names: a few, each one a name as a label takes one."""
    values = [str(v).strip() for v in values if v is not None and str(v).strip()]
    return bool(values) and len(set(values)) <= 12 and all(good_name(v) for v in values)


def choose(guess: dict, given, width: int) -> tuple[dict, list, str | None]:
    """The columns a table is read by: the guess, or what the card chose. `given` is a list of one
    role a column, "" for one left out, as the card sends it, or a `{role: index}` as a page or an
    agent from before 19 October sends it, whose roles not named keep the guess. Answers the role to
    column, the role of each column, and the one line that holds Make back, two columns given one
    role or none the transcript, else None. Two columns given one role are read by the first."""
    said = None
    if isinstance(given, (list, tuple)):
        roles = [str(r) if str(r) in ROLES else "" for r in list(given)[:width]]
        roles += [""] * (width - len(roles))
        cols = {role: None for role in ROLES}
        for role in ROLES:
            at = [i for i, r in enumerate(roles) if r == role]
            if at:
                cols[role] = at[0]
            if len(at) > 1 and said is None:
                said = i18n.t("server.two_columns_set_choose_one", role=ROLE_NAMES[role])
    else:
        cols = {role: guess.get(role) for role in ROLES}
        if isinstance(given, dict):
            fixed = {}
            for role in ROLES:
                if role in given:
                    try:
                        index = int(given[role])
                    except (TypeError, ValueError):
                        index = -1
                    fixed[role] = index if 0 <= index < width else None
            for role in ROLES:
                if role not in fixed and cols[role] in fixed.values():
                    cols[role] = None
            cols.update(fixed)
        roles = [""] * width
        for role in ROLES:
            if cols[role] is not None and not roles[cols[role]]:
                roles[cols[role]] = role
    if cols["text"] is None and said is None:
        said = NO_TRANSCRIPT
    return cols, roles, said


def left_out(heads, named, roles, filled) -> list[str]:
    """A line for each column with something in it that no role takes, by its heading when it has one."""
    left = []
    for i, head in enumerate(heads):
        if roles[i] or not filled[i]:
            continue
        place = ORDINALS[i] if i < len(ORDINALS) else f"number {i + 1}"
        left.append(i18n.t("server.column_headed_left_out", head=head) if named[i] else i18n.t("server.column_left_out", place=place))
    return left


def _come(n: int, what: str) -> str:
    return f"{n} passage{'' if n == 1 else 's'} {'comes' if n == 1 else 'come'} in with {'its' if n == 1 else 'their'} {what}"


def brings(read: dict) -> str:
    """What a Word table brings beside its transcript, in a line for the import card: the passages
    that come in with exploratory notes and with experiential statements, and what is left out.
    Empty for any other file."""
    notes = read.get("notes") or []
    en = sum(1 for n in notes if n.get("en"))
    es = sum(1 for n in notes if n.get("es"))
    kq = sum(1 for n in notes if n.get("kq"))
    said = [f"{_come(n, what)}." for n, what in ((en, "exploratory notes"), (es, "experiential statements"),
                                                 (kq, "quotes")) if n]
    return " ".join(said + list(read.get("left") or []))

# ---------------------------------------------------------- CSV and Excel

HEADERS = {
    "name": ("name", "speaker", "speaker name", "speakers", "who", "person", "voice", "participant", "role",
             "speaker label", "talker"),
    "ts": ("timestamp", "time", "timecode", "time code", "start", "start time", "starttime", "begin",
           "time stamp", "in", "offset", "seconds", "start (s)", "start time (s)"),
    "text": ("transcript", "text", "words", "utterance", "content", "transcription", "speech", "dialogue",
             "line", "sentence", "caption", "said", "what was said", "body", "message"),
}
STEMS = {"name": ("speaker", "name"), "ts": ("start", "timestamp", "timecode", "time"),
         "text": ("transcript", "text", "utterance", "content")}


def _header_key(value) -> str:
    return _squash(str(value or "")).lower().strip(" :#")


def is_header(row) -> bool:
    """Whether a table's first row names its columns: a known heading anywhere in it, or else no
    cell in it a time or a number."""
    cells = [c for c in row if c is not None and str(c).strip()]
    if not cells:
        return False
    if any(_header_key(c) in words for c in cells for words in HEADERS.values()):
        return True
    return not any(isinstance(c, (int, float, dt.time, dt.datetime, dt.timedelta)) or seconds_of(c) is not None
                   for c in cells)


def delimiter_of(text: str) -> str:
    """Comma, semicolon, tab or bar: the one that splits the first lines into the same number of
    columns most often, two at least, and the comma when none does."""
    sample = "\n".join(_lines(text)[:60])
    best, score = ",", (0.0, 0)
    for d in (",", ";", "\t", "|"):
        counts = [len(r) for r in csv.reader(io.StringIO(sample), delimiter=d) if any(c.strip() for c in r)]
        mode = max(set(counts), key=counts.count) if counts else 0
        if mode >= 2 and (counts.count(mode) / len(counts), mode) > score:
            best, score = d, (counts.count(mode) / len(counts), mode)
    return best


def table_of_csv(text: str) -> tuple[list[str], list[list]]:
    """A CSV's headings and rows. A row longer than the first has its extra cells joined back into
    its last, which is where words with the delimiter in them and no quotes round them spill from."""
    d = delimiter_of(text)
    rows = [r for r in csv.reader(io.StringIO("\n".join(_lines(text))), delimiter=d) if any(c.strip() for c in r)]
    if rows:
        width = len(rows[0])
        rows = [r[:width - 1] + [d.join(r[width - 1:])] if len(r) > width else r for r in rows]
    return _with_headers(rows)


def table_of_xlsx(path, name=None, sheet=None, info: dict | None = None) -> tuple[list[str], list[list]]:
    """An Excel file's first sheet with anything in it, as headings and rows, or with `sheet` the sheet of that
    name (ayabuild12, 9 November 2026), refused in one line when the file has none. `path` is the file or its
    contents in a file object, and `name` the file's name for the line a failure says. `info`, when given, is
    given `sheets`, every sheet's name in the file's order, for the card's Sheet chooser, and `sheet`, the one
    read."""
    try:
        book = openpyxl.load_workbook(path, read_only=True, data_only=True)
    except Exception as exc:                     # a damaged or protected file says one line
        raise unreadable(name or path) from exc
    try:
        if info is not None:
            info.update(sheets=list(book.sheetnames), sheet=None)
        sheets = book.worksheets
        wanted = " ".join(str(sheet or "").split())
        if wanted:
            sheets = ([ws for ws in book.worksheets if ws.title == wanted]
                      or [ws for ws in book.worksheets if ws.title.lower() == wanted.lower()])
            if not sheets:
                raise Unreadable(i18n.t("server.no_sheet_named", sheet=wanted, name=Path(str(name or "")).name))
        for ws in sheets:
            rows = [list(r) for r in ws.iter_rows(values_only=True)
                    if any(c is not None and str(c).strip() for c in r)]
            if rows:
                if info is not None:
                    info["sheet"] = ws.title
                return _with_headers(rows)
    finally:
        book.close()
    return [], []


def _with_headers(rows: list[list]) -> tuple[list[str], list[list]]:
    if not rows:
        return [], []
    width = max(len(r) for r in rows)
    rows = [list(r) + [None] * (width - len(r)) for r in rows]
    if is_header(rows[0]):
        heads = [_squash(str(c)) if c is not None else "" for c in rows[0]]
        rows = rows[1:]
    else:
        heads = [""] * width
    heads = [h or f"Column {i + 1}" for i, h in enumerate(heads)]
    return heads, rows


def guess_columns(headers: list[str], rows: list[list]) -> dict:
    """Which column is the Name, the Timestamp, the Transcript, the Exploratory notes and the
    Experiential statements, as indices or None: by the headings first, the notes and statements by
    the words a Word table's headings take, then the exact words before the words they contain, and
    then by what the columns hold, the times, the longest words and the fewest names, and in a table
    with no headings the fullest column left as the notes."""
    keys = [_header_key(h) for h in headers]
    found: dict = {"name": None, "ts": None, "text": None, "en": None, "es": None, "kq": None}
    taken: set[int] = set()
    for i, k in enumerate(keys):
        role = _head_role(k)
        if role in EXTRAS and found[role] is None and not any(k in HEADERS[r] for r in HEADERS):
            found[role] = i
            taken.add(i)
    for role in ("text", "ts", "name"):
        exact = [i for i, k in enumerate(keys) if k in HEADERS[role] and i not in taken]
        stem = [i for i, k in enumerate(keys) for s in STEMS[role]
                if s in k and i not in taken and not (role == "ts" and "end" in k.split())]
        pick = (exact or stem or [None])[0]
        if pick is not None:
            found[role] = pick
            taken.add(pick)
    sample = rows[:200]
    column = lambda i: [r[i] for r in sample if i < len(r) and r[i] is not None and str(r[i]).strip()]
    free = [i for i in range(len(headers)) if i not in taken]
    if found["ts"] is None:
        timed = [i for i in free if column(i) and sum(time_kind(v) is not None for v in column(i)) >= 0.6 * len(column(i))]
        if timed:
            found["ts"] = timed[0]
            free.remove(timed[0])
    if found["text"] is None and free:
        found["text"] = max(free, key=lambda i: sum(len(str(v)) for v in column(i)) / max(1, len(column(i))))
        free.remove(found["text"])
    if found["name"] is None:
        named = [i for i in free if column(i) and len({str(v).strip() for v in column(i)}) <= 12
                 and all(len(str(v)) <= 40 for v in column(i))]
        if named:
            found["name"] = min(named, key=lambda i: len({str(v).strip() for v in column(i)}))
            free.remove(found["name"])
    if found["en"] is None:
        wordy = [i for i in free if _GIVEN.fullmatch(headers[i]) and column(i) and not _timed(column(i))
                 and not all(isinstance(v, (int, float)) for v in column(i))]
        if wordy:
            found["en"] = max(wordy, key=lambda i: (sum(len(str(v)) for v in column(i)), -i))
    return found


_GIVEN = re.compile(r"Column \d+")     # the heading `_with_headers` gives a column with none


def read_table(rows: list[list], mapping: dict) -> list[tuple[str, int | None, str]]:
    """The mapped columns as turns. A row with no name carries the name above it, and a table
    with no name column is all `Speaker`. A row with no words is passed over."""
    return table_turns(rows, mapping)[0]


def table_turns(rows: list[list], mapping: dict, timing=None, bad: list | None = None) -> tuple[list[tuple], list[dict]]:
    """The mapped columns as turns, as `read_table` reads them, and beside each its notes and its
    statements from the columns mapped to `en` and `es`, and its quotes from `kq`, a `{"en", "es", "kq"}` of
    lines joined by line breaks, as a Word table's come in. A row with notes and no words adds them to the turn before.
    The times are read as `timing` says (see `timing_of`), and each one that cannot be is put in
    `bad`, by its passage's number and the time as written, its passage landing with no time."""
    timing = timing_of(timing)
    n, t, x = mapping.get("name"), mapping.get("ts"), mapping.get("text")
    cell = lambda row, i: row[i] if i is not None and i < len(row) else None
    lines = lambda v: [_squash(ln) for ln in str(v).splitlines() if _has_words(ln)] if v is not None else []
    turns, notes, last = [], [], SPEAKER
    for row in rows:
        extra = {role: lines(cell(row, mapping.get(role))) for role in EXTRAS}
        words = cell(row, x)
        words = _squash(words) if words is not None else ""
        if not words:
            if notes:
                for role in EXTRAS:
                    notes[-1][role] += extra[role]
            continue
        name = _squash(cell(row, n)) if cell(row, n) is not None else ""
        last = name or last
        given = cell(row, t)
        seconds = time_seconds(given, timing["format"], timing["fps"]) if given is not None else None
        if seconds is None and given is not None and str(given).strip() and bad is not None:
            bad.append({"passage": len(turns) + 1, "time": _squash(str(given))})
        turns.append((last if n is not None else SPEAKER, seconds, words))
        notes.append(extra)
    return turns, [{role: "\n".join(v) for role, v in held.items()} for held in notes]


# ----------------------------------------------------------- the whole file

def kind_of(path) -> str:
    return Path(path).suffix.lower().lstrip(".")


def read_file(path, mapping: dict | None = None, timing=None, sheet=None) -> dict:
    """A transcript file read for the card: its kind, its turns, and for a table its headings, the
    mapping used and the role of each column, the one given or else the one guessed (see `choose`). Raises Unreadable with the card's line
    when no turn comes out of it, but for a table with headings, whose mapping can still be
    changed, which comes back with no turns."""
    path = Path(path)
    if kind_of(path) not in {f.lstrip(".") for f in FORMATS}:
        raise unreadable(path)
    return read_data(path.name, path.read_bytes(), mapping, timing, sheet)


def read_data(name: str, data: bytes, mapping: dict | None = None, timing=None, sheet=None) -> dict:
    """A transcript read from its contents, as `read_file` reads one from the disk. New project's
    files arrive this way, since a browser's drop gives no path. `name` is the file's name, whose
    extension says the kind. A table answers too `time_found`, the format its Time column's times
    are written in, `timing`, how they were read, and `bad_times`, each one that could not be. An Excel file is
    read at its first sheet with anything in it, or at `sheet` by its name, and answers too `sheets`, every
    sheet's name, and `sheet`, the one read."""
    kind = kind_of(name)
    if kind not in {f.lstrip(".") for f in FORMATS}:
        raise unreadable(name)
    if kind in ("csv", "xlsx"):
        if kind == "csv":
            text = decode(data)
            if "\x00" in text:
                raise unreadable(name)
            headers, rows = table_of_csv(text)
        else:
            info: dict = {}
            headers, rows = table_of_xlsx(io.BytesIO(data), name, sheet, info)
        if not headers or not rows:
            raise unreadable(name)
        cols, roles, said = choose(guess_columns(headers, rows), mapping, len(headers))
        bad: list[dict] = []
        turns, notes = table_turns(rows, cols, timing, bad) if cols["text"] is not None else ([], [])
        found = (time_found([r[cols["ts"]] for r in rows if cols["ts"] < len(r)])
                 if cols["ts"] is not None else None)
        filled = [any(i < len(r) and r[i] is not None and str(r[i]).strip() for r in rows) for i in range(len(headers))]
        left = left_out(headers, [not _GIVEN.fullmatch(h) for h in headers], roles, filled)
        out = {"kind": kind, "turns": turns, "headers": headers, "mapping": cols, "roles": roles,
               "notes": notes if any(v for held in notes for v in held.values()) else None,
               "left": left, "said": said, "time_found": found, "timing": timing_of(timing), "bad_times": bad}
        if kind == "xlsx":
            out.update(sheets=info.get("sheets") or [], sheet=info.get("sheet"))
        return out
    if kind == "docx":
        # a table of transcript and notes comes in whole (19 October), anything else a paragraph a line
        root, _ = _docx_body(data, name)
        table = read_docx_table(root, mapping, timing)
        if table:
            return dict(table, kind=kind)
        paragraphs: list[str] = []
        _paragraphs(root, paragraphs)
        text = "\n".join(paragraphs)
    else:
        text = decode(data)
    if "\x00" in text:
        raise unreadable(name)
    turns = read_vtt(text) if kind in ("vtt", "srt") else read_plain(text)
    if not turns:
        raise unreadable(name)
    return {"kind": kind, "turns": turns, "headers": None, "mapping": None}


def speakers(turns) -> list[dict]:
    """Each speaker in the order they first speak, with their turns and their question marks."""
    out: dict[str, dict] = {}
    for name, _, words in turns:
        s = out.setdefault(name, {"name": name, "turns": 0, "questions": 0})
        s["turns"] += 1
        s["questions"] += words.count("?")
    return list(out.values())


def _same(a: str, b: str) -> bool:
    a, b = a.strip().lower(), b.strip().lower()
    return bool(a and b) and (a == b or a.split()[0] == b or b.split()[0] == a)


def guess_interviewer(turns, setting: str = "") -> str | None:
    """The interviewer among the speakers: the one Settings names, by the whole name or the first,
    or else the speaker with the most question marks, and nobody when nobody asks anything or
    only one speaker is named."""
    found = speakers(turns)
    for s in found:
        if setting and _same(s["name"], setting):
            return s["name"]
    real = [s for s in found if s["name"] != SPEAKER]
    if len(real) < 2:
        return None
    best = max(real, key=lambda s: s["questions"])          # the first to speak wins a tie
    return best["name"] if best["questions"] else None


def written_as(turns, setting: str) -> dict:
    """For each speaker, the name their turns are written under when chosen as the interviewer:
    Settings' interviewer, so the app reads them as context, or None when they already carry it,
    or when another speaker does, whose turns would then be mixed with theirs."""
    setting = (setting or "").strip()
    names = [s["name"] for s in speakers(turns)]
    out = {}
    for name in names:
        clash = any(o != name and o.strip().lower() == setting.lower() for o in names)
        out[name] = None if (not setting or clash or name.strip().lower() == setting.lower()) else setting
    return out


def as_interviewer(turns, chosen: str, setting: str) -> list[tuple]:
    """The turns with the chosen interviewer's written under Settings' name, as `written_as` says."""
    to = written_as(turns, setting).get(chosen) if chosen else None
    if not to:
        return list(turns)
    return [(to if name == chosen else name, seconds, words) for name, seconds, words in turns]


INTERVIEWER = "Interviewer"     # the interviewer's name in a new case when Settings gives none


# Each speaker's role (Adam, 20 October: "more than two names in the speaker column"): the
# interviewer, a participant, or another speaker. One transcript is always one case (his ruling of
# that morning). Two participants, a couple interviewed together, are one case with one set of PETs,
# each passage keeping its speaker's name. Another speaker, someone heard off camera, stays in the
# case, the turns skipped when moving from passage to passage as the interviewer's are, and still
# open to a note or a statement.
SPEAKER_ROLES = {"interviewer": "Interviewer", "participant": "Participant", "other": "Other speaker"}
ROLE_WORDS = {"interviewer": "interviewer", "participant": "participant", "other": "other",
              "other speaker": "other", "context": "other"}
CONTEXT = "Other speaker"       # the heading of the column marking another speaker's turn, and its mark
TWO_INTERVIEWERS = i18n.t("server.two_speakers_set_interviewer_choose")
NO_PARTICIPANT = i18n.t("server.set_one_speaker_participant")


def role_word(value) -> str | None:
    """A speaker's role as the card's key or its words, Interviewer, Participant or Other speaker, or None."""
    return ROLE_WORDS.get(" ".join(str(value or "").split()).lower())


def speaker_roles(turns, given=None, setting: str = "", interviewer=None) -> dict[str, str]:
    """Each speaker's role, in the order they first speak: the guess, the interviewer as
    `guess_interviewer` finds him and every other speaker a participant, with `interviewer`, the one
    chosen as a page from before 20 October sends it, in his place, and then whatever `given`, a
    `{name: role}`, sets. A name `given` holds that no turn carries is passed over."""
    names = [s["name"] for s in speakers(turns)]
    who = guess_interviewer(turns, setting) if interviewer is None else (interviewer if interviewer in names else None)
    roles = {name: ("interviewer" if name == who else "participant") for name in names}
    if isinstance(given, dict):
        for name, role in given.items():
            word = role_word(role)
            if name in roles and word:
                roles[name] = word
    return roles


def roles_said(roles: dict[str, str]) -> str | None:
    """The one line that holds Make back over the speakers' roles, two interviewers or no participant, else None."""
    if sum(r == "interviewer" for r in roles.values()) > 1:
        return TWO_INTERVIEWERS
    if roles and not any(r == "participant" for r in roles.values()):
        return NO_PARTICIPANT
    return None


def the_interviewer(roles: dict[str, str]) -> str:
    return next((n for n, r in roles.items() if r == "interviewer"), "")


def case_turns(turns, roles: dict[str, str], setting: str):
    """The case's turns and a mark a turn: the interviewer's under Settings' name as `as_interviewer`
    writes them, every participant's under their own name, and every other speaker's under theirs,
    each marked True, so the app skips them when moving from passage to passage."""
    chosen = the_interviewer(roles)
    out = as_interviewer(turns, chosen, setting) if chosen else list(turns)
    return out, [roles.get(name) == "other" for name, _s, _w in turns]


def as_case(turns, chosen: str, setting: str, pseudonym: str) -> list[tuple]:
    """One interview's turns as a new case holds them: the chosen interviewer's under Settings'
    name, so the app reads them as context, and every other speaker's under the participant's
    pseudonym, so no name from the recording's labels reaches the workbook."""
    to = (setting or "").strip() or INTERVIEWER
    return [(to if chosen and name == chosen else pseudonym, seconds, words) for name, seconds, words in turns]


def as_new_case(turns, roles: dict[str, str], setting: str, pseudonym: str) -> tuple[list[tuple], list[bool]]:
    """One interview's turns as New project writes them when each speaker has a role, as the import
    card gives them (20 October): the interviewer's under Settings' name, every participant's under
    the pseudonym, and another speaker's under Other speaker, Other speaker 2 for a second, each
    marked, so no name from the recording's labels reaches the workbook. Answers the turns and a mark
    a turn (see `case_turns`)."""
    to = (setting or "").strip() or INTERVIEWER
    others = [n for n, r in roles.items() if r == "other"]
    named = {n: (CONTEXT if i == 0 else f"{CONTEXT} {i + 1}") for i, n in enumerate(others)}
    out = [(to if roles.get(name) == "interviewer" else named.get(name, pseudonym), seconds, words)
           for name, seconds, words in turns]
    return out, [roles.get(name) == "other" for name, _s, _w in turns]


# An interview's name guessed from its file's name, for New project: one of a few fixed words, or a
# fixed word and a number, so a file named after a person never lends the guess a name.
_GUESSES = (
    (re.compile(r"(?<![a-z])initial(?![a-z])", re.I), lambda m: "Initial"),
    (re.compile(r"(?<![a-z])additional(?![a-z])", re.I), lambda m: "Additional"),
    (re.compile(r"(?<![a-z])follow[ _-]?up(?![a-z])", re.I), lambda m: "Follow-up"),
    (re.compile(r"(?<![a-z0-9])2d(?![a-z0-9])", re.I), lambda m: "2d"),
    (re.compile(r"(?<![a-z0-9])t([1-9])(?![0-9])", re.I), lambda m: f"T{m.group(1)}"),
    (re.compile(r"(?<![a-z])(time|day|part|session|interview)[ _-]*([1-9])(?![0-9])", re.I),
     lambda m: f"{m.group(1).capitalize()} {m.group(2)}"),
)
INTERVIEW = "Interview"         # the guess when the file's name gives none


def interview_of(name) -> str:
    """The interview a file holds, guessed from its name: Initial, Additional, Follow-up, 2d, T1,
    Day 2 and the like, else Interview."""
    stem = Path(str(name or "")).stem
    for pattern, word in _GUESSES:
        m = pattern.search(stem)
        if m:
            return word(m)
    return INTERVIEW


# --------------------------------------------------------------- the files

def output_for(path) -> Path:
    """The raw source a transcript file is made into, beside it: `<file name>.xlsx`, and for an
    Excel file `<file name> (converted).xlsx`."""
    path = Path(path)
    if path.suffix.lower() == ".xlsx":
        return path.with_name(f"{path.stem}{CONVERTED}.xlsx")
    return path.with_name(f"{path.stem}.xlsx")


def offered(path) -> bool:
    """Whether a file is one to offer: a transcript format, not one the app wrote, and with no
    workbook of its name beside it yet."""
    path = Path(path)
    if path.suffix.lower() not in FORMATS or path.name.startswith(("~$", ".")):
        return False
    if path.suffix.lower() == ".xlsx" and path.stem.endswith(CONVERTED):
        return False
    return not output_for(path).exists()


_ILLEGAL = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f]")


def _put(ws, row: int, col: int, value) -> None:
    """A cell written as text, never taken for a formula however it opens."""
    cell = ws.cell(row, col, value)
    if isinstance(value, str) and value.startswith("="):
        cell.data_type = "s"


def write_source(turns, out, notes=None, interviewer: str = "", made: str = "", context=None) -> Path:
    """The turns as a raw source workbook, `Name | Timestamp | Transcript` on one sheet, the times
    as Excel times, with a Word table's notes beside them (see `_fill`). Refuses a name already
    taken, and writes through a temporary file. `made`, for a workbook an agent made, says who made
    it for which request, in the file's own description (see `cli.cmd_import`). `context`, a mark a
    turn, puts Context beside each turn kept as context (see `case_turns`)."""
    return write_sheets([(SHEET, turns, notes, interviewer, context)], out, made)


def write_sheets(sheets, out, made: str = "") -> Path:
    """Several interviews as one raw source workbook, a sheet each named by its interview in the
    order given, each `Name | Timestamp | Transcript` as `write_source` writes one, so a case of
    several interviews is the one workbook of several sheets a GRAVITY case is. Each is `(title,
    turns)`, or `(title, turns, notes, interviewer)` for a Word table's notes (see `_fill`). Refuses
    a name already taken, and writes through a temporary file."""
    out = Path(out)
    if out.exists():
        raise FileExistsError(out.name)
    book = openpyxl.Workbook()
    book.remove(book.active)
    if made:
        book.properties.description = made
    for title, *rest in sheets:
        _fill(book.create_sheet(str(title)), *rest)
    tmp = out.with_name(f".{out.stem}.idiograph.tmp.xlsx")
    try:
        book.save(tmp)
        if out.exists():
            raise FileExistsError(out.name)
        os.replace(tmp, out)
    finally:
        book.close()
        if tmp.exists():
            tmp.unlink()
    return out


def _fill(ws, turns, notes=None, interviewer: str = "", context=None) -> None:
    """One interview's turns on a sheet of a raw source, `Name | Timestamp | Transcript`, the times as
    Excel times, an hour of 24 or more as text. A Word table's `notes`, one `{"en", "es", "kq"}` a turn,
    add the columns that hold any: Notes, Statements and Quote lines, and Interviewer notes for the notes on the
    turns written under `interviewer`, the name Settings gives him, since the statements screen keeps
    his notes there. `context`, a mark a turn, adds a Context column with Context beside each turn
    kept as context. `create_from_source` takes each into its place in the annotated workbook."""
    ws.append(["Name", "Timestamp", "Transcript"])
    who = str(interviewer or "").strip().lower()
    places = {}
    notes = list(notes or [])
    marks = list(context or [])
    for r, (name, seconds, words) in enumerate(turns, start=2):
        _put(ws, r, 1, _ILLEGAL.sub("", str(name)))
        if seconds is not None:
            h, m, s = seconds // 3600, (seconds % 3600) // 60, seconds % 60
            cell = ws.cell(r, 2, dt.time(h, m, s) if h < 24 else f"{h}:{m:02d}:{s:02d}")
            cell.number_format = "h:mm:ss"
        _put(ws, r, 3, _ILLEGAL.sub("", str(words)))
        held = notes[r - 2] if r - 2 < len(notes) and isinstance(notes[r - 2], dict) else {}
        mine = bool(who) and str(name).strip().lower() == who
        for head, text in ((RAW_INTERVIEWER if mine else RAW_NOTES, held.get("en")), (RAW_STATEMENTS, held.get("es")),
                           (RAW_QUOTES, held.get("kq"))):
            if text:
                if head not in places:
                    places[head] = 4 + len(places)
                    ws.cell(1, places[head], head)
                    ws.column_dimensions[chr(ord("A") + places[head] - 1)].width = 52.0
                _put(ws, r, places[head], _ILLEGAL.sub("", str(text)))
        if r - 2 < len(marks) and marks[r - 2]:
            if CONTEXT not in places:
                places[CONTEXT] = 4 + len(places)
                ws.cell(1, places[CONTEXT], CONTEXT)
                ws.column_dimensions[chr(ord("A") + places[CONTEXT] - 1)].width = 12.0
            ws.cell(r, places[CONTEXT], CONTEXT)
    for col, width in (("A", 16.0), ("B", 12.0), ("C", 80.0)):
        ws.column_dimensions[col].width = width


def add_sheets(sheets, out) -> Path:
    """Further interviews added to a raw source that stands, a sheet each at the end as `write_sheets`
    writes one, every sheet already there as it was. Refuses a sheet name taken already, whatever its
    capitals, as Excel does, and writes through a temporary file, its strings shared as Excel writes
    them (see `shared_strings`)."""
    from shared_strings import convert as shared

    out = Path(out)
    book = openpyxl.load_workbook(out, rich_text=True)
    tmp = out.with_name(f".{out.stem}.idiograph.tmp.xlsx")
    try:
        taken = {name.lower() for name in book.sheetnames}
        for title, *rest in sheets:
            if str(title).lower() in taken:
                raise FileExistsError(str(title))
            _fill(book.create_sheet(str(title)), *rest)
            taken.add(str(title).lower())
        book.save(tmp)
        shared(tmp)
        os.replace(tmp, out)
    finally:
        book.close()
        if tmp.exists():
            tmp.unlink()
    return out
