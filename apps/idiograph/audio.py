#!/usr/bin/env python3
"""Finding and serving the recording a sheet was transcribed from.

Source recordings sit at `<case>/Source/<Sheet>/Source/*.m4a`, where `<Sheet>` is the sheet name
(`Initial`, `2d`). A folder can hold the mixed recording and the per-speaker tracks beside it, so
the choice is made in order: the file whose stem is exactly `P<n>-<Sheet>`, then the largest `.m4a`
whose name does not carry `-track-`, then nothing.

Chromium cannot seek a file the server hands over in one piece, so the server answers a Range
request with 206 and a Content-Range. `parse_range` is the whole of that arithmetic and is tested
on its own.
"""
from __future__ import annotations

import json
import os
import re
from pathlib import Path

CONTENT_TYPES = {".m4a": "audio/mp4", ".mp3": "audio/mpeg", ".wav": "audio/wav", ".m4b": "audio/mp4"}
CHUNK = 256 * 1024


def case_tag(workbook: Path) -> str:
    """The `P<n>` a recording is named with, read off the workbook or its case folder."""
    for name in (Path(workbook).stem, Path(workbook).parent.name):
        m = re.match(r"\s*(P\d+)", name)
        if m:
            return m.group(1)
    return ""


def source_folder(workbook: Path, sheet: str) -> Path:
    workbook = Path(workbook)
    case = workbook.parent.parent if workbook.parent.name == "Source" else workbook.parent
    return case / "Source" / str(sheet) / "Source"


def choose(folder: Path, sheet: str, tag: str = "") -> Path | None:
    """The recording for one sheet, by the rule in the module docstring."""
    folder = Path(folder)
    if not folder.is_dir():
        return None
    files = [p for p in sorted(folder.iterdir())
             if p.is_file() and p.suffix.lower() in CONTENT_TYPES and not p.name.startswith(".")]
    if not files:
        return None
    if tag:
        exact = [p for p in files if p.stem == f"{tag}-{sheet}"]
        if exact:
            return exact[0]
    mixed = [p for p in files if "-track-" not in p.name]
    if not mixed:
        return None
    return max(mixed, key=lambda p: (p.stat().st_size, p.name))


def for_sheet(workbook: Path, sheet: str) -> Path | None:
    return choose(source_folder(workbook, sheet), sheet, case_tag(workbook))


# The recording may be a slightly different version from the one the times were taken on (Adam,
# 20 October: "a plus or minus offset"), so a sheet's recording can carry an offset in seconds, which
# playback adds to every time code. It is kept beside the recording, `offset.json` in the sheet's
# Source folder, `{"offset": -1.5}`, a plain file any tool can read, so it stays with the case.
OFFSET_FILE = "offset.json"
OFFSET_MOST = 24 * 3600


def offset_value(value) -> float | None:
    """An offset as a call gives it, a number of seconds, plus or minus, with a full stop or a comma,
    rounded to a hundredth, or None for anything else or more than a day either way."""
    if isinstance(value, bool):
        return None
    try:
        seconds = float(str(value).strip().replace(",", ".").replace("+", "", 1)) if not isinstance(value, (int, float)) else float(value)
    except (TypeError, ValueError):
        return None
    if seconds != seconds or abs(seconds) > OFFSET_MOST:
        return None
    return round(seconds, 2) + 0.0


def offset_in(folder: Path) -> float:
    """The offset a sheet's recording folder holds, 0 when it holds none or one that cannot be read."""
    try:
        held = json.loads((Path(folder) / OFFSET_FILE).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return 0.0
    seconds = offset_value(held.get("offset")) if isinstance(held, dict) else None
    return seconds or 0.0


def offset_for(workbook: Path, sheet: str) -> float:
    return offset_in(source_folder(workbook, sheet))


def write_offset(folder: Path, seconds: float) -> Path:
    """The offset written beside a sheet's recording, through a temporary file."""
    folder = Path(folder)
    target = folder / OFFSET_FILE
    tmp = folder / f".{OFFSET_FILE}.tmp"
    tmp.write_text(json.dumps({"offset": seconds}) + "\n", encoding="utf-8", newline="\n")
    os.replace(tmp, target)
    return target


def offset_said(seconds: float) -> str:
    """An offset as the screens and the agents' answers say it, "+1.5 seconds", "-2 seconds", "none"."""
    if not seconds:
        return "none"
    text = f"{abs(seconds):.2f}".rstrip("0").rstrip(".")
    return f"{'+' if seconds > 0 else '-'}{text} second{'' if abs(seconds) == 1 else 's'}"


def content_type(path: Path) -> str:
    return CONTENT_TYPES.get(Path(path).suffix.lower(), "application/octet-stream")


def parse_range(header: str | None, size: int) -> tuple[int, int] | None:
    """`bytes=0-99`, `bytes=100-` and `bytes=-100` as an inclusive [start, end].

    None for a missing, malformed or unsatisfiable header, which the caller answers with the whole
    file, because a player that asked badly still plays from the start.
    """
    if not header or size <= 0:
        return None
    m = re.fullmatch(r"\s*bytes\s*=\s*(\d*)\s*-\s*(\d*)\s*", str(header))
    if not m:
        return None
    first, last = m.group(1), m.group(2)
    if not first and not last:
        return None
    if not first:                                  # the final N bytes
        length = int(last)
        if length <= 0:
            return None
        return max(0, size - length), size - 1
    start = int(first)
    if start >= size:
        return None
    end = int(last) if last else size - 1
    end = min(end, size - 1)
    if end < start:
        return None
    return start, end


def read_span(path: Path, start: int, end: int):
    """Yield the bytes of [start, end] in chunks, so a long recording never lands in memory."""
    remaining = end - start + 1
    with open(path, "rb") as fh:
        fh.seek(start)
        while remaining > 0:
            block = fh.read(min(CHUNK, remaining))
            if not block:
                return
            remaining -= len(block)
            yield block
