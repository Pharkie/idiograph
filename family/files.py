"""Files the family's apps write, the same way in each (22 October 2026, the family codebase's second
build): a moment as the files record one, and a file written whole or not at all. Sift's screening and
Trace's projects both write through here, as Sift did alone before.

The standard library only.
"""
from __future__ import annotations

import os
import stat
import tempfile
from datetime import datetime
from pathlib import Path


def now_iso() -> str:
    """This moment as the files record one, to the second with the machine's offset: 2026-10-22T21:30:00+01:00."""
    return datetime.now().astimezone().isoformat(timespec="seconds")


def write_atomic(path: Path, text: str) -> None:
    """A file written whole or not at all: a temporary file beside it, then `os.replace`, with the
    old file's permissions, or read and write for him and read for others on a new file."""
    fd, tmp = tempfile.mkstemp(dir=str(path.parent), prefix=f".{path.name}.", suffix=".tmp")
    try:
        try:
            mode = stat.S_IMODE(path.stat().st_mode)
        except OSError:
            mode = 0o644
        os.chmod(tmp, mode)
        with os.fdopen(fd, "w", encoding="utf-8", newline="") as fh:
            fh.write(text)
            fh.flush()
            os.fsync(fh.fileno())
        os.replace(tmp, path)
    except BaseException:
        try:
            os.unlink(tmp)
        except OSError:
            pass
        raise
