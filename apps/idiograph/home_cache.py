"""Home's read cache kept across a restart (homecache, 16 November 2026).

Home's case list keeps what it read of each workbook, progress file and themes file in memory, each against the
marks of the files it came from (`idiograph_routes.read_book`, `turns_of`, `themes_head`, `boards_count`), so a second
visit opens nothing that has not changed. A restart forgot all of it, and the first visit read every workbook again,
0.6 to 0.8 s on Adam's projects and 1 to 2 s at their scale on a busy Mac (perfreview, 13 November 2026). Now those
tables are written to one file beside the app's own state, never inside a project folder or iCloud, read at the
server's start and written again in the background after Home has its list.

Every entry keeps the same marks the memory does, each file's modification time, size and inode, and is used only
while they are what the files have now, so a change to a project's files makes its entry stale and it is read again.
The whole file is also kept against a stamp of the app's version, the file's own format and the code that made the
entries (`stamp`), and one from another app version or other code is dropped whole. A file that cannot be read or
parsed, or any entry not in the shape its table keeps, is ignored, never trusted: the table reads its files as it
always did. Writing it is best effort, a temporary file then a rename, and a failure says nothing and changes nothing.
"""
from __future__ import annotations

import json
import os
import sys
import threading
from pathlib import Path

NAME = "home-cache.json"
FORMAT = 1
# the modules whose code made the entries: one changed, from source or by an update, and the file is dropped whole
CODE = ("idiograph_routes", "rounds", "themes", "workbook", "home_cache")


def code_mark() -> list:
    """Each module's file mark in `CODE`, or None where it has no file of its own (a frozen app's, which the
    version and build stand for)."""
    out = []
    for name in CODE:
        mod = sys.modules.get(name)
        where = getattr(mod, "__file__", None) if mod else None
        try:
            st = os.stat(where) if where else None
        except OSError:
            st = None
        out.append([name, [st.st_mtime_ns, st.st_size] if st else None])
    return out


def stamp(version: str, build: str) -> dict:
    """What the whole file is kept against: its format, the app's version and build, and the code's marks."""
    return {"format": FORMAT, "version": str(version or ""), "build": str(build or ""), "code": code_mark()}


def as_tuple(value):
    """A mark as JSON hands it back, every list a tuple again, as the memory keeps it and compares it."""
    if isinstance(value, list):
        return tuple(as_tuple(v) for v in value)
    return value


def _mark(value) -> bool:
    """A file mark as `file_mark` makes it: three whole numbers, or None for a file that was not there."""
    return value is None or (isinstance(value, tuple) and len(value) == 3 and all(type(v) is int for v in value))


def _strs(value) -> bool:
    return isinstance(value, list) and all(isinstance(v, str) for v in value)


def _book(mark, value):
    """A `read_book` entry, its rows as tuples again, or None for one not in its shape."""
    if not _mark(mark) or mark is None or not isinstance(value, dict):
        return None
    if value.get("kind") not in ("raw", "annotated") or not _strs(value.get("sheets")) or not _strs(value.get("names")):
        return None
    turns = value.get("turns")
    if not isinstance(turns, dict):
        return None
    rows = {}
    for sheet, got in turns.items():
        if not isinstance(got, list):
            return None
        kept = []
        for row in got:
            if not (isinstance(row, list) and len(row) == 3 and type(row[0]) is int and isinstance(row[1], str)
                    and type(row[2]) is bool):
                return None
            kept.append((row[0], row[1], row[2]))
        rows[sheet] = kept
    return {"kind": value["kind"], "sheets": list(value["sheets"]), "names": list(value["names"]), "turns": rows}


def _counts(value) -> bool:
    return (isinstance(value, dict) and set(value) == {"done", "total"}
            and all(type(value[k]) is int and value[k] >= 0 for k in ("done", "total")))


def _turns(mark, value):
    """A `turns_of` entry, (counts, timepoints), or None for one not in its shape. Its mark is the workbook's, the
    progress file's, the interviewer's name and the project's timepoints."""
    if not (isinstance(mark, tuple) and len(mark) == 4 and _mark(mark[0]) and mark[0] is not None and _mark(mark[1])
            and isinstance(mark[2], str) and isinstance(mark[3], tuple)):
        return None
    if not (isinstance(value, list) and len(value) == 2 and _counts(value[0])):
        return None
    tps = value[1]
    if tps is not None and not (isinstance(tps, list) and all(isinstance(t, dict) and _strs(t.get("sheets"))
                                                             for t in tps)):
        return None
    return value[0], tps


def _head(mark, value):
    """A `themes_head` entry, (the Current board's name, the PETs mark), or None for one not in its shape."""
    if not _mark(mark) or mark is None or not (isinstance(value, list) and len(value) == 2):
        return None
    name, pets = value
    if name is not None and not isinstance(name, str):
        return None
    if pets is not None and not (isinstance(pets, dict) and all(isinstance(pets.get(k), str) for k in ("at", "board", "name"))):
        return None
    return name, pets


def _count(mark, value):
    """A `boards_count` entry, the number of boards, or None for one not in its shape."""
    if not _mark(mark) or mark is None or type(value) is not int or value < 0:
        return None
    return value


SHAPES = {"books": _book, "turns": _turns, "heads": _head, "boards": _count}


def entries(tables: dict) -> dict:
    """The tables as the file holds them: each entry its key, its mark and what it keeps."""
    out = {}
    for name, table in tables.items():
        # a copy first, as another request may add to the table while it is read
        rows = []
        for key, held in list(dict(table).items()):
            if name == "turns":
                rows.append([key, held[0], [held[1], held[2]]])
            else:
                rows.append([key, held[0], held[1]])
        out[name] = rows
    return out


def load(path: Path, want: dict, tables: dict) -> int:
    """The file's entries put into `tables` where each has none of its own yet, the number taken. Nothing is taken
    from a file that cannot be read or parsed, or whose stamp is not `want`, and an entry not in its table's shape
    is passed over. Marks are not checked here: each table checks its own on every read, as it always has."""
    try:
        data = json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, ValueError, UnicodeDecodeError):
        return 0
    if not isinstance(data, dict) or data.get("stamp") != want or not isinstance(data.get("tables"), dict):
        return 0
    taken = 0
    for name, shape in SHAPES.items():
        table, rows = tables.get(name), data["tables"].get(name)
        if table is None or not isinstance(rows, list):
            continue
        for row in rows:
            if not (isinstance(row, list) and len(row) == 3 and isinstance(row[0], str)):
                continue
            mark = as_tuple(row[1])
            value = shape(mark, row[2])
            if value is None or row[0] in table:
                continue
            table[row[0]] = (mark, *value) if name == "turns" else (mark, value)
            taken += 1
    return taken


def save(path: Path, want: dict, tables: dict, current) -> bool:
    """The tables written to the file, each entry only while `current(table, key, mark)` says its mark is still what
    the files have, so one for a file changed or gone is left out. A temporary file beside it, then a rename, so a
    reader never meets it half written. False when it could not be written, with nothing else changed."""
    rows = entries(tables)
    kept = {name: [r for r in got if current(name, r[0], r[1])] for name, got in rows.items()}
    path = Path(path)
    tmp = path.with_name(f"{path.name}.{os.getpid()}.{threading.get_ident()}.tmp")
    try:
        tmp.write_text(json.dumps({"stamp": want, "tables": kept}, ensure_ascii=False, separators=(",", ":")),
                       encoding="utf-8", newline="\n")
        os.replace(tmp, path)
    except (OSError, TypeError, ValueError):
        try:
            tmp.unlink()
        except OSError:
            pass
        return False
    return True


def signature(tables: dict) -> int:
    """What the tables hold, keys and marks, so a write after a visit that read nothing new is left out."""
    return hash(tuple(sorted((name, key, repr(held[0])) for name, table in tables.items()
                             for key, held in list(dict(table).items()))))
