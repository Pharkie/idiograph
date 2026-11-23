"""What `gets` and `agent_changes` share about telling a changed file by its marks where the file clock is coarse
(seenmark, 23 November 2026): Windows's clock ticks about every 15.6 ms, so a file rewritten inside the tick it was last
read in keeps its time, and one rewritten to the same size its size too. Where that may be (`COARSE`) a file read within
`TICK_NS` of its own time is read for its contents too (`sha_of`), and a time and size that match are settled by those
contents. The suite sets `COARSE` in each module that uses it to check it on any system; the Mac and Linux, whose times
are fine, keep time and size alone. Standard library alone, so either module may import it."""
from __future__ import annotations

import hashlib
import os

COARSE = os.name == "nt"
TICK_NS = 2_000_000_000
CHUNK = 1024 * 1024


def sha_of(path) -> str | None:
    """A file's sha256, read a CHUNK at a time, or None when it cannot be read."""
    digest = hashlib.sha256()
    try:
        with open(path, "rb") as fh:
            for piece in iter(lambda: fh.read(CHUNK), b""):
                digest.update(piece)
    except OSError:
        return None
    return digest.hexdigest()
