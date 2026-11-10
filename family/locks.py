#!/usr/bin/env python3
"""One writer at a time, across processes: the server and the command line take the same file lock
around every write, so two writers never interleave.

A case's files, its themes file, its progress file and its workbook, go under the lock in its
`Working/.idiograph.lock` (the case's lock, whose place is Idiograph's, `workbook.case_lock`, since the family
codebase's fourth build, 22 October 2026), and the project's own files at the case root, the GETs file and
the project file, under `.idiograph.lock` at the root. The lock is `fcntl.flock` on that file, which
the system lets go when the process ends, however it ends, so a crash never leaves one held. On
Windows it is `msvcrt.locking` on the file's first byte. The lock file holds nothing and is never
read.

A write that cannot have the lock within WAIT seconds says so and writes nothing. The server's own
threads already take turns through its own lock, and this one is what keeps the command line and
the server apart.
"""
from __future__ import annotations

import contextlib
import json
import os
import secrets
import time
from pathlib import Path

import i18n
from errors import WorkbookError

try:
    import fcntl
except ImportError:          # Windows
    fcntl = None
    import msvcrt

NAME = ".idiograph.lock"
WAIT = 10.0                  # seconds a write waits for the lock before it gives up
STEP = 0.05
# a state file that is there but will not read whole is read again this many times, this many seconds apart
READ_TRIES = 5
READ_PAUSE = 0.1


def root_lock(root: Path) -> Path:
    """The lock of a project's own files at its case root, the GETs file and the project file."""
    return Path(root) / NAME


def _try(fh) -> bool:
    try:
        if fcntl is not None:
            fcntl.flock(fh.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        else:
            fh.seek(0)
            msvcrt.locking(fh.fileno(), msvcrt.LK_NBLCK, 1)
        return True
    except OSError:
        return False


def _release(fh) -> None:
    try:
        if fcntl is not None:
            fcntl.flock(fh.fileno(), fcntl.LOCK_UN)
        else:
            fh.seek(0)
            msvcrt.locking(fh.fileno(), msvcrt.LK_UNLCK, 1)
    except OSError:
        pass


@contextlib.contextmanager
def held(path: Path, wait: float | None = None):
    """The lock at `path` held for the block, its folder made when it is not there yet. Waits up to
    `wait` seconds, WAIT by default, and then refuses with BUSY, its code `busy`, having written nothing."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    fh = open(path, "a+b")
    limit = time.monotonic() + (WAIT if wait is None else wait)
    try:
        while not _try(fh):
            if time.monotonic() >= limit:
                raise WorkbookError(i18n.t("errors.another_write_these_files_under"), code="busy")
            time.sleep(STEP)
        try:
            yield path
        finally:
            _release(fh)
    finally:
        fh.close()


def root(folder: Path, wait: float | None = None):
    """The lock of a project's own files, held for the block."""
    return held(root_lock(folder), wait)


def is_held(path: Path) -> bool:
    """Whether another writer holds the lock at `path` now. Takes it and lets it go when free."""
    path = Path(path)
    if not path.exists():
        return False
    with open(path, "a+b") as fh:
        if _try(fh):
            _release(fh)
            return False
        return True


def replace(source: Path, target: Path, wait: float = 2.0) -> None:
    """`os.replace`, tried again for `wait` seconds when it is refused. On Windows a reader holding the target open
    for a moment refuses it, so a short wait lets the write through. Still refused after that, the error is raised
    as before (winsweep, 4 November 2026)."""
    until = time.time() + wait
    while True:
        try:
            os.replace(source, target)
            return
        except PermissionError:
            if time.time() > until:
                raise
            time.sleep(0.1)


def read_json(path: Path):
    """A file of the app's own state read as JSON: None when it is not there. One that is there but will not read
    or parse is read again a few times, a short pause between (a virus scanner or a sync app holding it a moment),
    and then refused as busy, never taken as not there: a reader that went on with nothing would write its counts,
    keys or waiting messages afresh over the ones kept (teamflake, 9 November 2026)."""
    path = Path(path)
    for attempt in range(READ_TRIES):
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except FileNotFoundError:
            return None
        except (OSError, ValueError):
            if attempt + 1 < READ_TRIES:
                time.sleep(READ_PAUSE)
    raise WorkbookError(i18n.t("errors.another_write_these_files_under"), code="busy")


def new_tmp(target: Path) -> Path:
    """A temporary name beside `target` that no other writer shares, so two threads or two processes writing one
    file never write into one temporary file and rename it into place half written."""
    target = Path(target)
    return target.with_name(f".{target.name}.{secrets.token_hex(4)}.tmp")


def __getattr__(name: str) -> str:
    """The refusals other modules and the checks name as this module's, each read in the run's language when
    asked for (the text layer, 28 October 2026)."""
    said = {
        "BUSY": lambda: i18n.t("errors.another_write_these_files_under"),
    }
    if name in said:
        return said[name]()
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
