"""A board's History kept beside its board file, in chunks, never inside it (historybuild, 16 November 2026, Adam's
rulings that day: chunks of about 256 KB per board, in a folder beside the board file, existing projects moved over on
first open, no backwards compatibility; historyfix the same day after a fresh-eyes review).

Until then each board carried every revision of itself under `history` inside its board file, so a participant's
PETs file ran to 6 to 13 MB, parsed whole on every 4-second poll and written whole on every drop. Now:

- Beside each board file, a folder with `.json` swapped for `.history` (`folder_of`): `Working/<stem>.themes.history/`,
  `.themes-t2.history/` and so on, `.lpets.history/`, `idiograph-gets.history/` and `idiograph-lgets.history/` at the
  root. Trajectories, codes and participants keep their own small capped histories inside their files.
- Each board's History is chunks, one revision a line as the board file wrote them, oldest first, a chunk taking no
  new revision once it holds CHUNK bytes. A revision stays in the chunk it was written to, so pruning, a rekey or a new
  revision changes only the chunks whose bytes change.
- A write's new revisions go into one chunk of their own, open, and no chunk already written is read, written again
  or put aside; the head's `open` says how many of its last chunks are. At FOLD open chunks the next write folds
  them, their lines copied byte for byte, onto the tail when it is here and they fit in CHUNK, else after it; a fold
  that cannot read an open chunk now writes one more open chunk instead (perfhist, 22 November 2026, where every
  revision wrote the last chunk anew, up to 256 KB a board, and put the old one aside for a week).
- A chunk is never written over: each is named by its board's uid, its number and the start of its bytes' SHA-256,
  `<uid>.<n>.<hash>.jsonl`, and a chunk whose bytes change is written under its new name. The board's head names
  every chunk its History is (`chunks`), so the board file says exactly which files hold its History, and a chunk read
  is checked against its name. A chunk iCloud has not brought yet, or an older copy of one, can never be read as the
  History: it is not the file the head names (review 1). And a write that stops part way leaves the files the board
  file names as they were: the new chunks go first, then the board file, and only then are the chunks it no longer
  names put aside in `superseded/` inside the History folder, read from there while a board file another Mac wrote
  still names one, brought back by the next write, and taken away a week later (`out_of`, `supersede`, historyfix2).
- `uid` is a random name each board is given with its first revision, so a board id the file reuses after a delete
  (`gets._next_board` takes the largest plus one) never meets the History of the board deleted.
- The board keeps `history_head` in its file (`HEAD`): its `uid`, `count`, `next` (the next revision's number), `last`
  (the last state's hash), `autos` (how many are automatic), `chunks`, each chunk's number and hash, and `open`, a
  hint for the writer alone (`open_of`). In memory a
  board read from a file also carries `at` in its head, the folder its chunks are in, written nowhere (`place`), so a
  board brought from another file brings its History with it, and `add`, revisions made since it was read and not
  yet written, which the writer puts in a chunk of their own without reading the others (`append`).
- A chunk the head names that is missing, or one that will not read or does not match its name, is `HistoryAway`:
  the History tab shows it as not here yet, and a History write that needs it is refused with nothing written. A chunk
  Optimize Mac Storage evicted (`SF_DATALESS`) is read, which brings it back from iCloud, given FETCH_SECONDS once
  for each fetch and no wait at all under a lock; one shown by a `.<name>.icloud` placeholder is asked for and is
  away until it comes (review 2). A read error never reads as an empty chunk.
- A follower that rewrites revisions after the workbook has changed (a trim's rekey, a passage written, the GETs'
  remaps) leaves a board whose History is away with its revisions as they were and moves the board itself: Restore
  follows a revision's keys and words to the workbook as it is (`themes.brought_up`), so nothing is half done. A
  find and replace no longer rewrites the revisions at all: a revision takes the words of today when it is restored or
  shown (lazy word-following, Adam, 16 November 2026).
- Every reader that walks History goes through here: `revisions` (read, never attached), `attach` (the History put
  on the board in memory to change it, written back by `out_of`), `attach_all` for a whole file. The suite's area 400
  greps for `.get("history")` and `["history"]` on boards anywhere else.

Moving a project over (`move_on_open`): a board file whose boards still hold `history` inside it is moved on its first
open under its lock (the case's in `Working/`, the project's at the root, both `<the file's folder>/.idiograph.lock`),
a copy of the whole file into the `_Archive` first, `<name> (pre-history-move <date-time>).json`; the chunks written,
read back and every revision checked (`census`: id, time, name, automatic, kind, slots and its state's SHA-256),
each board's version checked unchanged on what is to be written, and only then the board file written without them.
Anything that stops it leaves the file as it was and answers the data as read, which every reader here takes as it is.
A file still holding History inside it after a crash part way is moved again from what it holds: the History inside
the file wins, and the chunks a half-done move left, which no board file names, are swept once ORPHAN_SECONDS old,
a copy of each in the `_Archive` first.
"""
from __future__ import annotations

import contextlib
import contextvars
import glob
import hashlib
import json
import os
import re
import secrets
import shutil
import subprocess
import threading
import time
from datetime import datetime
from pathlib import Path

import i18n
import locks
from errors import WorkbookError

TAIL = ".history"
CHUNK = 256 * 1024
HEAD = "history_head"
AT = "at"
ADD = "add"
UID = re.compile(r"^[0-9a-f]{16}$")
HASH_LEN = 12
CHUNK_NAME = re.compile(r"^([0-9a-f]{16})\.(\d+)\.([0-9a-f]{12})\.jsonl$")
# a file iCloud Drive has evicted to the cloud, its data not on this Mac (sys/stat.h)
SF_DATALESS = 0x40000000
# how long a read waits for iCloud to bring an evicted chunk back before History reads as not here yet: once for each
# fetch, never again while that fetch goes on, and never under a lock (historyfix2)
FETCH_SECONDS = 20.0
# a fetch that failed (no connection) is remembered this long, every read meanwhile away at once, then tried again
FAILED_SECONDS = 60.0
# a chunk no board file names (a write or a move that stopped part way, or a head another Mac has not sent yet) is
# left this long before it is swept, a copy in the _Archive first
ORPHAN_SECONDS = 7 * 24 * 3600
# a chunk a write no longer names is put in this folder inside the History folder and left there SUPERSEDED_SECONDS
# from then, never taken away as it is superseded: a board file another Mac wrote before it saw the write may still
# name it and win in iCloud, and then it is read from here and brought back by the next write (historyfix2)
SUPERSEDED = "superseded"
SUPERSEDED_SECONDS = 7 * 24 * 3600
# a write's new revisions go into a chunk of their own, open, and once a board has FOLD open chunks the next write
# folds them into a chunk at CHUNK (perfhist, 22 November 2026); the head's OPEN says how many of its last chunks are
OPEN = "open"
FOLD = 16
# a History folder is swept at most once in this long by one process: what a sweep takes away is a week old
SWEEP_EVERY = 600.0
MOVE_LABEL = "pre-history-move"
# set for a dry run, which writes nothing, the move on first open among it (`move_on_open`)
HOLD: contextvars.ContextVar = contextvars.ContextVar("idiograph_history_hold", default=False)
# what a move checks on the data to be written, before the board file is (`move_on_open`, `out_of`)
CHECK: contextvars.ContextVar = contextvars.ContextVar("idiograph_history_check", default=None)
GONE_LABEL = "deleted board"
ORPHAN_LABEL = "unnamed"


class HistoryAway(WorkbookError):
    """A board's History not wholly on this computer yet: a chunk missing, evicted or unreadable."""

    code = "history_away"


def away() -> HistoryAway:
    return HistoryAway(i18n.t("server.history_away"))


# ------------------------------------------------------------------ places

def folder_of(path: Path) -> Path:
    """The History folder beside a board file: `.json` swapped for `.history`."""
    path = Path(path)
    name = path.name[:-len(".json")] if path.name.endswith(".json") else path.name
    return path.with_name(name + TAIL)


def file_of(folder: Path) -> Path:
    folder = Path(folder)
    return folder.with_name(folder.name[:-len(TAIL)] + ".json")


def archive_of(path: Path) -> Path:
    """The `_Archive` a board file's copies go to: its participant's for a file in `Working/`, the project's for one
    at the root."""
    path = Path(path)
    return (path.parent.parent if path.parent.name == "Working" else path.parent) / "_Archive"


def lock_of(path: Path) -> Path:
    """The lock a board file is written under: `Working/.idiograph.lock` for a participant's, the root's for the
    project's (`workbook.case_lock`, `locks.root_lock`)."""
    return Path(path).parent / locks.NAME


def new_uid() -> str:
    return secrets.token_hex(8)


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()[:HASH_LEN]


def chunk_name(uid: str, n: int, h: str) -> str:
    return f"{uid}.{int(n)}.{h}.jsonl"


def state_hash(state: dict) -> str:
    """A stable hash of a board's state (`themes.state_hash` is this one)."""
    text = json.dumps(state, sort_keys=True, ensure_ascii=False, separators=(",", ":"))
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def head_of(board) -> dict | None:
    """A board's head when it has a good one."""
    head = board.get(HEAD) if isinstance(board, dict) else None
    if isinstance(head, dict) and isinstance(head.get("uid"), str) and UID.match(head["uid"]):
        return head
    return None


def named(head: dict) -> list[tuple[int, str]]:
    """The chunks a head names, in order, each its number and hash. A head that names them in any other shape is
    away, never an empty History."""
    held = head.get("chunks")
    if not isinstance(held, list):
        raise away()
    out = []
    for item in held:
        if not (isinstance(item, (list, tuple)) and len(item) == 2 and isinstance(item[0], int)
                and isinstance(item[1], str) and re.fullmatch(r"[0-9a-f]{%d}" % HASH_LEN, item[1])):
            raise away()
        out.append((int(item[0]), item[1]))
    return out


def open_of(head: dict | None) -> int:
    """How many of a head's last chunks are open, not folded yet: a hint for the writer alone, read as 0 when it is
    no whole number, and never more than the chunks the head names. A wrong one only folds early or late."""
    if not isinstance(head, dict):
        return 0
    value = head.get(OPEN)
    held = head.get("chunks")
    if not isinstance(value, int) or isinstance(value, bool) or not isinstance(held, list):
        return 0
    return min(max(value, 0), len(held))


def names_of(head: dict | None) -> set[str]:
    """The chunk files a head names, by their names; none for a head that names them in no good shape."""
    if head is None:
        return set()
    try:
        return {chunk_name(head["uid"], n, h) for n, h in named(head)}
    except HistoryAway:
        return set()


def drop(board: dict) -> dict:
    """A board with no History, none inside and no head: a copy made or a board brought in starts its own."""
    board.pop("history", None)
    board.pop(HEAD, None)
    return board


def bare_head(head: dict) -> dict:
    return {k: v for k, v in head.items() if k not in (AT, ADD)}


def bare(board: dict) -> dict:
    """A board as its file holds it: no History inside, and its head without the folder it is read from or the
    revisions waiting to be written."""
    out = {k: v for k, v in board.items() if k != "history"}
    head = head_of(board)
    if head is not None:
        out[HEAD] = bare_head(head)
    elif HEAD in out:
        out.pop(HEAD)
    return out


def boards_in(data) -> list[dict]:
    return [b for b in (data or {}).get("boards") or [] if isinstance(b, dict)] if isinstance(data, dict) else []


def place(path: Path, data):
    """Each board of a file read from `path` told where its chunks are, in memory alone."""
    folder = str(folder_of(path))
    for board in boards_in(data):
        head = head_of(board)
        if head is not None:
            head[AT] = folder
    return data


def embedded(data) -> bool:
    """Whether a file's boards hold their History inside it, as before this build."""
    return any(isinstance(b.get("history"), list) for b in boards_in(data))


# ------------------------------------------------------------------ reading the chunks

_BYTES: dict = {}
_MEMO: dict = {}
# each chunk's revisions without their states, by its path and mark, for History's list alone (`light_head`)
_LIGHT: dict = {}
# when this process last swept each History folder (`finish` in `out_of`)
_SWEPT: dict = {}
_FETCHING: dict = {}
_ASKED: dict = {}


def reset() -> None:
    """Everything kept in memory forgotten, as after a restart (the suite's): the fetches and iCloud's asks among it."""
    _BYTES.clear()
    _MEMO.clear()
    _LIGHT.clear()
    _SWEPT.clear()
    _FETCHING.clear()
    _ASKED.clear()


def _mark(st) -> tuple:
    return (st.st_mtime_ns, st.st_size, getattr(st, "st_ino", 0))


def _ask_icloud(path: Path) -> None:
    """A chunk iCloud shows by a `.<name>.icloud` placeholder asked for, in the background; it reads once it comes."""
    for key, proc in list(_ASKED.items()):
        if proc.poll() is not None:
            _ASKED.pop(key, None)
    brctl = shutil.which("brctl")
    if brctl is None or str(path) in _ASKED:
        return
    with contextlib.suppress(OSError, ValueError):
        _ASKED[str(path)] = subprocess.Popen([brctl, "download", str(path)], stdout=subprocess.DEVNULL,
                                             stderr=subprocess.DEVNULL)


def _fetch(path: Path) -> bytes:
    """An evicted chunk read, which on macOS brings its data back from iCloud, in the background. A read waits for it
    while the fetch is younger than FETCH_SECONDS, and not at all under a lock (`locks.holding`), so a save never
    waits on the network; past that, or failed (no connection) within FAILED_SECONDS, it is away at once, and a later
    read finds the data once the fetch has brought it (review 2, 4)."""
    key = str(path)
    held = _FETCHING.get(key)
    now = time.monotonic()
    if held is not None and held["done"].is_set() and (held["error"] is not None or held["data"] is None) \
            and now - held["ended"] > FAILED_SECONDS:
        _FETCHING.pop(key, None)
        held = None
    if held is None:
        held = {"data": None, "error": None, "done": threading.Event(), "began": now, "ended": now}
        _FETCHING[key] = held

        def read() -> None:
            try:
                with open(path, "rb") as fh:
                    held["data"] = fh.read()
            except OSError as exc:
                held["error"] = exc
            finally:
                held["ended"] = time.monotonic()
                held["done"].set()
        threading.Thread(target=read, daemon=True, name="history-fetch").start()
    wait = 0.0 if locks.holding() else max(0.0, FETCH_SECONDS - (now - held["began"]))
    if not held["done"].wait(wait):
        raise away()
    if held["error"] is not None or held["data"] is None:
        raise away()
    _FETCHING.pop(key, None)
    return held["data"]


def dataless(path: Path) -> bool:
    """Whether a file is evicted to iCloud, its data not on this Mac (a stat, nothing read)."""
    try:
        return bool(getattr(os.stat(path), "st_flags", 0) & SF_DATALESS)
    except OSError:
        return False


def found(path: Path) -> Path | None:
    """Where a chunk is: in its History folder, or in that folder's `superseded/` (see SUPERSEDED), else None."""
    path = Path(path)
    if path.exists():
        return path
    aside = path.parent / SUPERSEDED / path.name
    return aside if aside.exists() else None


def read_chunk(path: Path, h: str | None = None) -> bytes:
    """A chunk's bytes, kept against its time, size and inode, and checked against the hash its name gives. Missing,
    unreadable or not matching is away; evicted is fetched (see `_fetch`)."""
    path = Path(path)
    try:
        st = os.stat(path)
    except FileNotFoundError:
        aside = path.parent / SUPERSEDED / path.name
        if path.parent.name != SUPERSEDED and aside.exists():
            # a write elsewhere superseded it while this board file still names it
            m = CHUNK_NAME.match(path.name)
            return read_chunk(aside, h or (m.group(3) if m else None))
        placeholder = path.with_name("." + path.name + ".icloud")
        if placeholder.exists():
            _ask_icloud(path)
        raise away() from None
    except OSError:
        raise away() from None
    mark = _mark(st)
    held = _BYTES.get(str(path))
    if held is not None and held[0] == mark:
        return held[1]
    if getattr(st, "st_flags", 0) & SF_DATALESS:
        data = _fetch(path)
        with contextlib.suppress(OSError):
            mark = _mark(os.stat(path))
    else:
        try:
            with open(path, "rb") as fh:
                data = fh.read()
        except OSError:
            raise away() from None
        if len(data) != mark[1]:
            raise away()
    m = CHUNK_NAME.match(path.name)
    want = h or (m.group(3) if m else None)
    if want and digest(data) != want:
        raise away()
    _BYTES[str(path)] = (mark, data)
    if len(_BYTES) > 4096:
        _BYTES.clear()
    return data


def parse(data: bytes) -> list[dict]:
    """A chunk's revisions. A line that will not read is away, never an empty chunk."""
    out = []
    try:
        for line in data.decode("utf-8").split("\n"):
            if line.strip():
                rev = json.loads(line)
                if not isinstance(rev, dict):
                    raise ValueError
                out.append(rev)
    except (UnicodeDecodeError, ValueError):
        raise away() from None
    return out


def where_of(board: dict, folder: Path | None = None) -> Path:
    head = head_of(board)
    if head is not None and head.get(AT):
        return Path(head[AT])
    if folder is not None:
        return Path(folder)
    raise away()


def read_head(folder: Path, head: dict) -> tuple[list[dict], dict[str, int], dict[int, bytes]]:
    """The revisions the chunks a head names hold, read afresh, the chunk each revision's id is in, and each chunk's
    bytes. Any chunk not here, or a count other than the head's, is away."""
    revs, where, raw = [], {}, {}
    for n, h in named(head):
        data = read_chunk(Path(folder) / chunk_name(head["uid"], n, h), h)
        raw[n] = data
        for rev in parse(data):
            revs.append(rev)
            where[str(rev.get("id"))] = n
    try:
        count = int(head.get("count") or 0)
    except (TypeError, ValueError):
        raise away() from None
    if len(revs) != count:
        raise away()
    return revs, where, raw


class Unread(dict):
    """The state of a revision read for History's list (`light`): a dict, so `isinstance(state, dict)` holds as for the
    revision it stands for, and empty, but any read of what is in it raises, so a caller of `memo` that comes to need a
    state fails at once and never reads a board as empty (perfhist2)."""
    __slots__ = ()

    def _unread(self, *_a, **_k):
        raise RuntimeError("board_history.memo: a revision's state is not read for History's list; use revisions()")

    __getitem__ = __iter__ = __len__ = __contains__ = __eq__ = __ne__ = __bool__ = _unread
    get = keys = values = items = copy = setdefault = pop = popitem = update = _unread
    __setitem__ = __delitem__ = clear = __or__ = __ior__ = __reduce__ = __reduce_ex__ = _unread
    __hash__ = None


# one key held underneath, so code that reads a dict's insides without its methods (json's encoder) raises too
UNREAD = Unread({"unread": True})


def light(rev: dict) -> dict:
    """A revision without its state's contents: `state` the `UNREAD` marker when it was a board's state, which raises
    on any read, and gone otherwise."""
    out = {k: v for k, v in rev.items() if k != "state"}
    if isinstance(rev.get("state"), dict):
        out["state"] = UNREAD
    return out


def light_head(folder: Path, head: dict) -> list[dict]:
    """The revisions the chunks a head names hold, each without its state (`light`), for History's list: each
    chunk read and checked against its name as `read_head` reads it, but parsed only when this process has not
    parsed those bytes before, and the count checked against the head's. Fresh copies, so a caller's changes never
    reach what is kept (perfhist: after a revision only its new chunk is parsed, where every chunk was)."""
    revs = []
    for n, h in named(head):
        path = Path(folder) / chunk_name(head["uid"], n, h)
        data = read_chunk(path, h)
        key = (h, len(data))
        held = _LIGHT.get(str(path))
        if held is None or held[0] != key:
            held = (key, [light(r) for r in parse(data)])
            if len(_LIGHT) > 4096:
                _LIGHT.clear()
            _LIGHT[str(path)] = held
        revs.extend(dict(r) for r in held[1])
    try:
        count = int(head.get("count") or 0)
    except (TypeError, ValueError):
        raise away() from None
    if len(revs) != count:
        raise away()
    return revs


def stored(board: dict, folder: Path | None = None) -> tuple[list[dict], dict[str, int]]:
    """A board's revisions as its chunks hold them, read afresh, and the chunk each revision's id is in."""
    head = head_of(board)
    if head is None:
        return [], {}
    revs, where, _raw = read_head(where_of(board, folder), head)
    return revs, where


def pending(board: dict) -> list[dict]:
    head = head_of(board)
    held = head.get(ADD) if head is not None else None
    return list(held) if isinstance(held, list) else []


def key_of(board: dict) -> tuple:
    """What a board's History is, for a cache: its folder, uid and the chunks it names, which are never written over."""
    head = head_of(board)
    if head is None:
        return ()
    return (str(where_of(board)), head["uid"], int(head.get("count") or 0), tuple(named(head)))


def revisions(board: dict) -> list[dict]:
    """A board's revisions, oldest first: the ones in memory when the board carries them (a file from before this
    build, or attached to change them), else read from its chunks with any made since it was read, a fresh list the
    caller may keep."""
    held = board.get("history") if isinstance(board, dict) else None
    if isinstance(held, list):
        return held
    if head_of(board) is None:
        return []
    return stored(board)[0] + pending(board)


def counted(board: dict) -> int | None:
    """How many revisions a board's head says it has, with those waiting, no chunk read; None for a board carrying its
    History in memory or with no head."""
    head = head_of(board)
    if head is None or isinstance(board.get("history"), list):
        return None
    try:
        return int(head.get("count") or 0) + len(pending(board))
    except (TypeError, ValueError):
        return None


def memo(board: dict, kind: str, fn):
    """`fn(revisions)` kept against the board's chunks as they stand, for what History shows of a board read
    lazily. A board carrying its History in memory, or revisions not yet written, is worked out afresh. Read from
    the chunks, `fn` is given the revisions without their states (`light_head`: `state` the `UNREAD` marker, which
    raises on any read, or missing), so it must never read a state's contents: History's list and `here`'s count,
    its only callers, read none."""
    if isinstance(board.get("history"), list) or head_of(board) is None or pending(board):
        return fn(revisions(board))
    key = (kind,) + key_of(board)
    held = _MEMO.get(key)
    if held is None:
        held = fn(light_head(where_of(board), head_of(board)))
        if len(_MEMO) > 512:
            _MEMO.clear()
        _MEMO[key] = held
    return held


def here(board: dict) -> bool:
    """Whether a board's History is all on this computer: every chunk its head names there and not evicted, and
    reading whole. A stat of each, the chunks read only when History has not been read as it stands (`memo`), and
    never a wait: an evicted chunk is away until a read has brought it back (review 2, 4)."""
    try:
        if not isinstance(board.get("history"), list) and head_of(board) is not None:
            head = head_of(board)
            at = where_of(board)
            for n, h in named(head):
                f = found(at / chunk_name(head["uid"], n, h))
                if f is None:
                    return False
                held = _BYTES.get(str(f))
                if dataless(f) and not (held is not None and held[0] == _mark(os.stat(f))):
                    return False
            key = key_of(board)
            if not any(k[1:] == key for k in _MEMO):
                memo(board, "count", len)
        return True
    except (HistoryAway, OSError):
        return False


def attach(board: dict) -> list[dict]:
    """A board's History put on it in memory, to change it: the writer then writes it back to its chunks. Away is
    raised, so a History write never starts from part of it."""
    held = board.get("history")
    if not isinstance(held, list):
        held = revisions(board)
        board["history"] = held
        head = head_of(board)
        if head is not None:
            head.pop(ADD, None)
    return held


def attached(board: dict) -> list[dict] | None:
    """`attach`, or None while the board's History is not all here: for a follower that moves the board itself
    whatever its History, its revisions brought up to date when restored (see the module's head)."""
    try:
        return attach(board)
    except HistoryAway:
        return None


def attach_all(data) -> dict:
    """Every board of a file with its History attached, for a reader that walks the whole file."""
    for board in boards_in(data):
        attach(board)
    return data


def number_of(rev: dict) -> int:
    rid = str(rev.get("id") or "")
    return int(rid[1:]) if rid[:1] == "r" and rid[1:].isdigit() else 0


def next_number(board: dict, history: list[dict]) -> int:
    """The next revision's number: past the largest the History holds, the revisions waiting and the head's own."""
    numbers = [number_of(r) for r in list(history) + pending(board)]
    head = head_of(board) or {}
    try:
        kept = int(head.get("next") or 1)
    except (TypeError, ValueError):
        kept = 1
    return max(max(numbers, default=0) + 1, kept)


def last_number(board: dict) -> int:
    """The number of a board's last revision, those in memory or waiting and the head's own counted, 0 for none; no
    chunk is read (histfollow, 21 November 2026)."""
    held = board.get("history") if isinstance(board.get("history"), list) else []
    return next_number(board, held) - 1


def last_hash(board: dict) -> str | None:
    """The hash of the board's last revision's state, from the revisions waiting or else the head, no chunk read."""
    adds = pending(board)
    if adds and isinstance(adds[-1].get("state"), dict):
        return state_hash(adds[-1]["state"])
    head = head_of(board)
    return str(head.get("last") or "") if head is not None else None


def can_append(board: dict) -> bool:
    """Whether a new revision can go on the end of a board's History without the rest of it in memory: the board
    read from its file with a head and its History not attached. A revision goes into a chunk of its own
    (`append_chunks`), so no chunk is read for it, and one of them away, the last among them, evicted, not come
    from iCloud yet or lost, loses nothing and is never written over: the head goes on naming it and the revision
    takes the next number after it, so History shows the board's History as not here yet while it is away and
    whole when it is back, where a last chunk away once refused every revision of the board for good (smallfix,
    22 November 2026)."""
    head = head_of(board)
    if head is None or isinstance(board.get("history"), list) or not head.get(AT):
        return False
    # a head naming its chunks in no good shape is away, as ever, and no chunk is looked for
    named(head)
    return True


def append(board: dict, rev: dict) -> None:
    """A revision put on the end of a board's History, written by `out_of` in a chunk of its own (see
    `can_append`, `append_chunks`)."""
    head = head_of(board)
    head.setdefault(ADD, []).append(rev)


# ------------------------------------------------------------------ writing the chunks

def line_of(rev: dict) -> str:
    return json.dumps(rev, ensure_ascii=False, separators=(",", ":"))


def _write_new(path: Path, data: bytes, made: list[Path]) -> None:
    """A chunk written under its own name, never over another: one already there with that name holds these bytes."""
    if path.exists():
        # named by its own hash, so one there evicted holds these bytes; one that reads otherwise is written over
        if dataless(path):
            return
        with contextlib.suppress(OSError):
            if path.read_bytes() == data:
                return
    tmp = locks.new_tmp(path)
    try:
        with open(tmp, "wb") as fh:
            fh.write(data)
        locks.replace(tmp, path)
    finally:
        with contextlib.suppress(OSError):
            tmp.unlink()
    _BYTES.pop(str(path), None)
    made.append(path)


def head_for(uid: str, history: list[dict], chunks: list[list], kept: dict | None, open_: int = 0) -> dict:
    good = [r for r in history if isinstance(r.get("state"), dict)]
    nxt = max([number_of(r) for r in history] + [0]) + 1
    if kept is not None:
        with contextlib.suppress(TypeError, ValueError):
            nxt = max(nxt, int(kept.get("next") or 1))
    return {"uid": uid, "count": len(history), "next": nxt,
            "last": state_hash(good[-1]["state"]) if good else "", "autos": sum(1 for r in history if r.get("auto")),
            "chunks": chunks, OPEN: max(0, min(int(open_), len(chunks)))}


def write_chunks(folder: Path, uid: str, history: list[dict], base: dict | None, made: list[Path] | None = None) -> dict:
    """A board's whole History written to its chunks: each revision stays in the chunk `base`, the head as the file
    holds it, has it in, a new one goes into the last chunk until it holds CHUNK bytes, and only a chunk whose bytes
    changed is written, under its new name. The head it now has. Nothing is taken away here (see `out_of`)."""
    folder = Path(folder)
    made = [] if made is None else made
    old_where, old_raw = {}, {}
    if base is not None and base.get("uid") == uid:
        try:
            _revs, old_where, old_raw = read_head(folder, base)
        except HistoryAway:
            # the History in memory is the whole of it: written afresh, the file's old head naming chunks gone
            old_where, old_raw = {}, {}
    chunks: dict[int, list[str]] = {}
    sizes: dict[int, int] = {}
    last = 0
    top = max(old_raw, default=1)
    for rev in history:
        line = line_of(rev)
        n = old_where.get(str(rev.get("id")))
        if n is None:
            n = max(top, last, 1)
            if sizes.get(n, 0) >= CHUNK or (n in old_raw and n not in sizes and len(old_raw[n]) >= CHUNK):
                n += 1
            top = n
        n = max(n, last)
        last = n
        chunks.setdefault(n, []).append(line)
        sizes[n] = sizes.get(n, 0) + len(line.encode("utf-8")) + 1
    listed = []
    lengths: dict[int, int] = {}
    if chunks:
        folder.mkdir(parents=True, exist_ok=True)
    for n in sorted(chunks):
        data = ("\n".join(chunks[n]) + "\n").encode("utf-8")
        h = digest(data)
        if old_raw.get(n) != data:
            _write_new(folder / chunk_name(uid, n, h), data, made)
        listed.append([n, h])
        lengths[n] = len(data)
    # the chunks still open: the last ones past the base's last folded one and under CHUNK bytes, so a full chunk is
    # never counted open, by its number or by a prune past AUTO_KEEP filling one after another, and a fold never
    # reads one; none when there was no base to read (a move, a board brought in, the base away) (perfhist2)
    still_open = 0
    if old_raw:
        was = named(base)
        k = open_of(base)
        tail_n = was[-k - 1][0] if k < len(was) else 0
        for n, _h in reversed(listed):
            if n <= tail_n or lengths[n] >= CHUNK:
                break
            still_open += 1
    return head_for(uid, history, listed, base, still_open)


def lines_in(data: bytes) -> list[bytes]:
    """A chunk's lines as its bytes hold them, each with its newline, the empty ones left out as `parse` leaves them."""
    return [piece + b"\n" for piece in data.split(b"\n") if piece.strip()]


def pack(lines: list[bytes], start: int) -> list[tuple[int, bytes]]:
    """Lines cut into chunks numbered from `start`, a chunk taking no new line once it holds CHUNK bytes."""
    out, data, n = [], b"", start
    for line in lines:
        if data and len(data) >= CHUNK:
            out.append((n, data))
            n, data = n + 1, b""
        data += line
    if data:
        out.append((n, data))
    return out


def held_in(path: Path, h: str, data: bytes) -> int:
    """How many revisions a chunk's bytes hold, parsed, or counted from History's list's cache of the same bytes."""
    kept = _LIGHT.get(str(path))
    if kept is not None and kept[0] == (h, len(data)):
        return len(kept[1])
    return len(parse(data))


def folded(folder: Path, uid: str, chunks: list[list], k: int, adds: list[bytes],
           past: bool = False) -> tuple[int, list] | None:
    """A fold (see `append_chunks`): where the chunks it replaces begin in `chunks`, and the chunks that take their
    place, each its number and bytes, the open ones' lines and the adds' copied byte for byte; None when an open
    chunk will not read now (away, evicted, other bytes), never a wait under a lock. With `past`, an open chunk that
    will not read is left where it is, the tail now, and only the open chunks after it are folded. The tail, the
    chunk before the open ones folded, is folded onto only when it is here, not evicted, reads, and it, the open ones
    and the adds fit in CHUNK; otherwise it stays as it is and the rest go after it. The lines packed are checked
    against the revisions the chunks read hold, parsed, and the adds."""
    folder = Path(folder)
    at = len(chunks) - k
    lines: list[bytes] = []
    want = 0
    stuck = False
    for i in range(at, len(chunks)):
        n, h = chunks[i]
        path = folder / chunk_name(uid, n, h)
        try:
            data = read_chunk(path, h)
            held = held_in(path, h, data)
        except HistoryAway:
            if not past:
                return None
            lines, want, at, stuck = [], 0, i + 1, True
            continue
        lines += lines_in(data)
        want += held
    lines += adds
    want += len(adds)
    tail = chunks[at - 1] if at > 0 else None
    start = (tail[0] + 1) if tail is not None else 1
    if tail is not None and not stuck:
        f = found(folder / chunk_name(uid, *tail))
        if f is not None and not dataless(f):
            with contextlib.suppress(OSError, HistoryAway):
                if os.stat(f).st_size + sum(len(x) for x in lines) <= CHUNK:
                    data = read_chunk(f, tail[1])
                    held = held_in(f, tail[1], data)
                    lines = lines_in(data) + lines
                    want += held
                    at, start = at - 1, tail[0]
    pieces = pack(lines, start)
    # every revision the folded chunks held and every add, once each: a line `lines_in` split otherwise than `parse`
    # reads it is away, and the rollback in `out_of` takes away what was made
    if sum(len(lines_in(d)) for _n, d in pieces) != want:
        raise away()
    return at, pieces


def append_chunks(folder: Path, head: dict, adds: list[dict], made: list[Path] | None = None) -> dict:
    """Revisions put on the end of a board's History, `head` the board file's own (perfhist, 22 November 2026). As
    a rule the write's revisions go into one new chunk of their own, open, and no chunk already written is read,
    written again or put aside. Once the head has FOLD open chunks, or the revisions alone come to CHUNK bytes, the
    write folds: the open chunks and its revisions packed onto the tail or after it (`folded`), the chunks folded
    put aside by `out_of` once the board file names the new ones. A fold that cannot read an open chunk now writes
    one more open chunk instead, and a later write folds; once the head has 2 * FOLD open chunks, one lost for good
    among them, the write folds the open chunks after it and leaves it where it is, so the files never pile up
    (perfhist2). The head it now has."""
    folder = Path(folder)
    made = [] if made is None else made
    uid = head["uid"]
    chunks = [list(c) for c in named(head)]
    k = open_of(head)
    lines = [(line_of(rev) + "\n").encode("utf-8") for rev in adds]
    fold = None
    if lines and (k >= FOLD or sum(len(x) for x in lines) >= CHUNK):
        fold = folded(folder, uid, chunks, k, lines)
        if fold is None and k >= 2 * FOLD:
            fold = folded(folder, uid, chunks, k, lines, past=True)
    if fold is not None:
        at, pieces, still_open = fold[0], fold[1], 0
    elif lines:
        at, pieces, still_open = len(chunks), [((chunks[-1][0] + 1) if chunks else 1, b"".join(lines))], k + 1
    else:
        at, pieces, still_open = len(chunks), [], k
    if pieces:
        folder.mkdir(parents=True, exist_ok=True)
    chunks = chunks[:at] + [[n, digest(data)] for n, data in pieces]
    for n, data in pieces:
        _write_new(folder / chunk_name(uid, n, digest(data)), data, made)
    count, autos, nxt = int(head.get("count") or 0), int(head.get("autos") or 0), int(head.get("next") or 1)
    for rev in adds:
        count += 1
        autos += 1 if rev.get("auto") else 0
        nxt = max(nxt, number_of(rev) + 1)
    good = [r for r in adds if isinstance(r.get("state"), dict)]
    return {"uid": uid, "count": count, "next": nxt,
            "last": state_hash(good[-1]["state"]) if good else str(head.get("last") or ""), "autos": autos,
            "chunks": chunks, OPEN: min(still_open, len(chunks))}


def chunk_files(folder: Path) -> dict[str, Path]:
    """Every chunk in a History folder by its name."""
    try:
        return {n: Path(folder) / n for n in os.listdir(folder) if CHUNK_NAME.match(n)}
    except OSError:
        return {}


def disk_state(path: Path) -> tuple[dict, bool]:
    """The file as it stands, read once for a write: each board's head by its id, with when the board was made (for a
    writer that lost a head), and whether its boards still hold their History inside it: "kept" when any revision is
    there to move, True when only an empty list is."""
    try:
        text = Path(path).read_text(encoding="utf-8")
        data = json.loads(text)
    except (OSError, ValueError):
        return {}, False
    heads = {str(b.get("id")): (head_of(b), str(b.get("created") or "")) for b in boards_in(data) if head_of(b)}
    if '"history":' not in text or not embedded(data):
        return heads, False
    # a file holding History is copied first and its revisions checked, one holding none just loses the key
    return heads, "kept" if any(b.get("history") for b in boards_in(data)) else True


def census_of(history: list[dict]) -> list[tuple]:
    """Each revision as a census lists it, never its words: id, time, name's hash, automatic, kind, slots' hash and
    its state's SHA-256."""
    out = []
    for r in history:
        state = r.get("state") if isinstance(r.get("state"), dict) else {}
        out.append((str(r.get("id")), str(r.get("at") or ""),
                    hashlib.sha256(str(r.get("name") or "").encode("utf-8")).hexdigest()[:16], bool(r.get("auto")),
                    str(r.get("kind") or ""), state_hash(r.get("slots") or {})[:16], state_hash(state)))
    return out


def stamp() -> str:
    return datetime.now().strftime("%Y%m%d-%H%M")


def keep_copy(path: Path) -> Path:
    """A copy of a board file in its `_Archive`, `<name> (pre-history-move <date-time>).json`."""
    path = Path(path)
    archive = archive_of(path)
    archive.mkdir(parents=True, exist_ok=True)
    stem, at = path.name[:-len(".json")] if path.name.endswith(".json") else path.stem, stamp()
    # one copy of the file as it is, however many times a move that fails is tried (review 2, 6)
    size = path.stat().st_size
    for kept in archive.glob(f"{glob.escape(stem)} ({MOVE_LABEL} *).json"):
        with contextlib.suppress(OSError):
            if kept.stat().st_size == size and kept.read_bytes() == path.read_bytes():
                return kept
    copy, n = archive / f"{stem} ({MOVE_LABEL} {at}).json", 2
    while copy.exists():
        copy, n = archive / f"{stem} ({MOVE_LABEL} {at}-{n}).json", n + 1
    shutil.copy2(path, copy)
    return copy


def archive_files(path: Path, files: list[Path], label: str) -> None:
    """Chunks copied into the board file's `_Archive`, `<name> history (<label> <date-time>)/`."""
    if not files:
        return
    folder = folder_of(path)
    stem = folder.name[:-len(TAIL)]
    archive = archive_of(path)
    at = stamp()
    target, n = archive / f"{stem} history ({label} {at})", 2
    while target.exists():
        target, n = archive / f"{stem} history ({label} {at}-{n})", n + 1
    target.mkdir(parents=True)
    for f in files:
        shutil.copy2(f, target / f.name)


def out_of(path: Path, data: dict) -> tuple[dict, callable]:
    """A board file's write, its History first. Every board carrying History in memory has it written to its chunks,
    one with revisions waiting has them written in a chunk of their own, or folded with the open ones at FOLD
    (`append_chunks`), and one with neither keeps the head the file has for
    it (a writer holding an older head never puts it back, review 5). A board from another file, its head's folder not
    this one's, brings its own History here under a new uid. Each head is brought up to date in place. Only new chunk
    files are written, so the files the board file names now stay as they are until it is written.

    The data to write to the board file, no History inside and no folder in a head, and what to run once it is
    written: which takes away the chunks it no longer names (those of a board deleted copied into the `_Archive`
    first), and sweeps chunks no board file names once ORPHAN_SECONDS old. Anything that stops it takes away the
    chunks it wrote, the board file not yet touched. A board file whose History was inside it on disk is copied into
    the `_Archive` first, and each board's chunks read back and checked against what was inside (the move), and a
    move's own check (`CHECK`) is run on the data to be written."""
    path = Path(path)
    folder = folder_of(path)
    on_disk, moving = disk_state(path)
    by_uid = {h["uid"]: h for h, _made in on_disk.values()}
    if moving == "kept":
        keep_copy(path)
    made: list[Path] = []
    written: list[tuple[dict, list[tuple]]] = []
    heads: list[dict] = []
    out_boards = []
    try:
        for board in boards_in(data):
            head = head_of(board)
            at = Path(head[AT]) if head is not None and head.get(AT) else None
            history = board.get("history") if isinstance(board.get("history"), list) else None
            if history is None and head is None:
                # a writer that built the board afresh without its head keeps the History of the same board, the
                # same id made at the same time, never a board that took a deleted one's id
                held = on_disk.get(str(board.get("id")))
                if held is not None and held[1] and held[1] == str(board.get("created") or ""):
                    head = dict(held[0], **{AT: str(folder)})
                    board[HEAD] = head
                    at = folder
            if head is not None and at is not None and at != folder:
                # brought from another file: its History comes with it, under a uid of this file's
                history = revisions(board) if history is None else history
                head = None
            if history is None:
                if head is None:
                    out_boards.append(bare(board))
                    continue
                adds = pending(board)
                base = by_uid.get(head["uid"])
                if adds:
                    new = append_chunks(folder, base if base is not None else head, adds, made)
                else:
                    # the file's own head for it, which names the chunks as they are on disk
                    new = dict(base if base is not None else bare_head(head))
                board[HEAD] = dict(new, **{AT: str(folder)})
                heads.append(board[HEAD])
                out_boards.append(bare(board))
                continue
            if not history and head is None:
                board.pop(HEAD, None)
                out_boards.append(bare(board))
                continue
            uid = head["uid"] if head is not None else new_uid()
            base = by_uid.get(uid)
            new = write_chunks(folder, uid, history, base, made)
            if head is not None:
                with contextlib.suppress(TypeError, ValueError):
                    new["next"] = max(new["next"], int(head.get("next") or 1))
            board[HEAD] = dict(new, **{AT: str(folder)})
            heads.append(board[HEAD])
            written.append((board[HEAD], census_of(history)))
            out_boards.append(bare(board))
        if moving:
            # every revision read back from its chunks and checked against the History the file held
            for head, want in written:
                for n, h in named(head):
                    _BYTES.pop(str(folder / chunk_name(head["uid"], n, h)), None)
                got = read_head(folder, head)[0]
                if census_of(got) != want:
                    raise WorkbookError(i18n.t("server.history_move_differs", name=path.name))
        out = dict(data)
        out["boards"] = out_boards
        check = CHECK.get()
        if check is not None:
            check(out)
    except BaseException:
        for f in made:
            with contextlib.suppress(OSError):
                f.unlink()
            _BYTES.pop(str(f), None)
        raise
    keep = set().union(*(names_of(h) for h in heads)) if heads else set()
    kept_uids = {h["uid"] for h in heads}
    was = set().union(*(names_of(h) for h in by_uid.values())) if by_uid else set()
    # a board deleted: its chunks, which the file named, copied into the _Archive before the file is written
    gone = sorted(folder / n for n in was - keep if CHUNK_NAME.match(n).group(1) not in kept_uids)
    archive_files(path, [f for f in gone if f.exists()], GONE_LABEL)
    # and the chunks a write superseded, which the file named and no longer does
    superseded = sorted(was - keep)
    # a chunk the file is to name that a write elsewhere put aside is brought back before the file names it
    for name in sorted(keep):
        restore(folder, name)

    def finish() -> None:
        supersede(folder, superseded)
        # at most once in SWEEP_EVERY a folder: what it takes away is a week old, and every chunk this file names is
        # brought back from superseded/ above before the write
        now = time.monotonic()
        last = _SWEPT.get(str(folder))
        if last is None or now - last > SWEEP_EVERY:
            _SWEPT[str(folder)] = now
            sweep(path, keep)
        with contextlib.suppress(OSError):
            if folder.is_dir() and not any(folder.iterdir()):
                folder.rmdir()
    return out, finish


def supersede(folder: Path, names) -> None:
    """Chunks a board file no longer names put aside in its History folder's `superseded/`, timed from now, never
    taken away as they are superseded (see SUPERSEDED, review 2, 3)."""
    folder = Path(folder)
    aside = folder / SUPERSEDED
    now = time.time()
    for name in names:
        f = folder / name
        if not f.exists():
            continue
        with contextlib.suppress(OSError):
            aside.mkdir(exist_ok=True)
            os.replace(f, aside / name)
            os.utime(aside / name, (now, now))
        _BYTES.pop(str(f), None)


def restore(folder: Path, name: str) -> bool:
    """A chunk a board file names brought back from `superseded/` when it is there and not beside the file; whether
    it is beside the file now."""
    folder = Path(folder)
    f = folder / name
    aside = folder / SUPERSEDED / name
    if f.exists():
        if aside.exists():
            # written again since it was put aside: the copy aside is the same bytes, its name its hash
            with contextlib.suppress(OSError):
                aside.unlink()
        return True
    if not aside.exists():
        return False
    with contextlib.suppress(OSError):
        os.replace(aside, f)
    _BYTES.pop(str(aside), None)
    return f.exists()


def sweep(path: Path, named_now: set[str]) -> list[Path]:
    """Chunks no board file names, left by a write or a move that stopped part way, taken away once ORPHAN_SECONDS
    old, a copy of each in the `_Archive` first. A younger one may be named by a board file another Mac has not
    sent yet, so it stays. And the chunks put aside as superseded, taken away without a copy SUPERSEDED_SECONDS
    after they were, one the file names again brought back."""
    folder = folder_of(path)
    now = time.time()
    old = []
    for name, f in chunk_files(folder).items():
        if name in named_now:
            continue
        with contextlib.suppress(OSError):
            if now - f.stat().st_mtime > ORPHAN_SECONDS:
                old.append(f)
    if old:
        with contextlib.suppress(OSError):
            archive_files(path, old, ORPHAN_LABEL)
            for f in old:
                with contextlib.suppress(OSError):
                    f.unlink()
    aside = folder / SUPERSEDED
    for name, f in chunk_files(aside).items():
        if name in named_now:
            restore(folder, name)
            continue
        with contextlib.suppress(OSError):
            if now - f.stat().st_mtime > SUPERSEDED_SECONDS:
                f.unlink()
                _BYTES.pop(str(f), None)
    with contextlib.suppress(OSError):
        if aside.is_dir() and not any(aside.iterdir()):
            aside.rmdir()
    return old


def snapshot(path: Path) -> dict:
    """A board file's History chunks as they stand, for an op that may have to put them back (`put_back`)."""
    folder = folder_of(path)
    return {"folder": str(folder), "files": {n: f.read_bytes() for n, f in chunk_files(folder).items()}}


def put_back(snap: dict) -> None:
    """The chunks `snapshot` kept put back byte for byte, and any made since taken away."""
    folder = Path(snap["folder"])
    for name, f in chunk_files(folder).items():
        if name not in snap["files"]:
            with contextlib.suppress(OSError):
                f.unlink()
            _BYTES.pop(str(f), None)
    if snap["files"]:
        folder.mkdir(parents=True, exist_ok=True)
    for name, data in snap["files"].items():
        target = folder / name
        if target.exists() and target.read_bytes() == data:
            continue
        _write_new(target, data, [])


def inline(data: dict) -> dict:
    """A board file's data with every board's History inside it and no head, as files held it before this build: a
    copy kept in an `_Archive` that an op may put back over the file (codes' undo, clear-formatting's), whole in
    itself, which the next open moves over again under new uids, so it never names a chunk taken away since.
    Refused while a board's History is not all here."""
    out = dict(data)
    out["boards"] = [dict({k: v for k, v in b.items() if k not in ("history", HEAD)}, history=revisions(b))
                     if isinstance(b, dict) else b for b in (data.get("boards") or [])]
    return out


def inline_copy(path: Path, copy: Path) -> Path:
    """`copy`, a copy of the board file at `path`, written with its History inside it (`inline`) when the file keeps
    its History beside it."""
    try:
        data = place(path, json.loads(Path(path).read_text(encoding="utf-8")))
    except (OSError, ValueError):
        return copy
    if any(head_of(b) is not None for b in boards_in(data)):
        from themes import render  # noqa: PLC0415 (themes imports this module)
        Path(copy).write_text(render(inline(data)) + "\n", encoding="utf-8", newline="\n")
    return copy


def keep_named(path: Path, copy: Path) -> Path:
    """`copy`, a copy of the board file at `path` an op may put back over it (codes' undo), given the chunks the file
    names, copied into the History folder beside the copy, so that putting it back never names a chunk taken away
    since (`bring_named`). Chunks are never written over, so a copy of one is the chunk."""
    try:
        files = named_files(path)
    except HistoryAway:
        files = []
    if files:
        target = folder_of(copy)
        target.mkdir(parents=True, exist_ok=True)
        for f in files:
            shutil.copy2(f, target / f.name)
    return copy


def bring_named(copy: Path, path: Path) -> None:
    """A board file put back from `copy` (see `keep_named`): each chunk it names that is no longer beside it brought
    back from the copy's folder."""
    try:
        data = json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return
    kept, folder = folder_of(copy), folder_of(path)
    for board in boards_in(data):
        for name in names_of(head_of(board)):
            if not restore(folder, name) and (kept / name).exists():
                folder.mkdir(parents=True, exist_ok=True)
                _write_new(folder / name, (kept / name).read_bytes(), [])


def named_files(path: Path, data: dict | None = None) -> list[Path]:
    """Every chunk a board file's heads name, from the file or from `data` as it holds it. One missing is away, so
    nothing that carries a board file's History carries part of it (Working together, review 4)."""
    path = Path(path)
    if data is None:
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            return []
    folder = folder_of(path)
    out = []
    for board in boards_in(data):
        for name in sorted(names_of(head_of(board))):
            f = folder / name
            if HOLD.get():
                f = found(f)
                if f is None:
                    raise away()
            elif not restore(folder, name):
                raise away()
            out.append(f)
    return out


# ------------------------------------------------------------------ moving a file over on its first open

def move_on_open(path: Path, data: dict, write, reread, guard=None) -> dict:
    """A board file whose boards hold their History inside it, moved over (see the module's head) when its lock is
    free and the file is this install's to write: `write(data)` the file's own writer, which goes through `out_of`,
    and `reread()` the file read again. Each board's version is checked unchanged on the data to be written, before
    the file is (review 3), and on the file read back after, the file's bytes put back when it is not. Anything that
    stops it leaves the file as it was and answers the data as read, History inside, which every reader here takes
    as it is, so a participant's boards always open."""
    from themes import board_version  # noqa: PLC0415 (themes imports this module)
    path = Path(path)
    if HOLD.get():
        return data
    if guard is not None:
        try:
            guard()
        except WorkbookError:
            return data
    try:
        with locks.held(lock_of(path), wait=0):
            fresh = reread()
            if not embedded(fresh):
                return fresh
            raw = path.read_bytes()
            before = {str(b.get("id")): board_version(b) for b in boards_in(fresh)}

            def same(out: dict) -> None:
                if {str(b.get("id")): board_version(b) for b in boards_in(out)} != before:
                    raise WorkbookError(i18n.t("server.history_move_differs", name=path.name))
            token = CHECK.set(same)
            try:
                write(fresh)
            finally:
                CHECK.reset(token)
            try:
                after = reread()
                same(after)
            except Exception:
                # the file put back as it was, its History inside; the chunks it named are swept in time
                tmp = locks.new_tmp(path)
                tmp.write_bytes(raw)
                locks.replace(tmp, path)
                raise
            return after
    except Exception:  # noqa: BLE001 (a move that cannot be made never stops the boards opening)
        return data


# ------------------------------------------------------------------ the census

def census(path: Path) -> dict:
    """Every revision of every board of a board file, from its chunks or from inside it: keys and hashes, never
    words. `boards` by id, each its revisions' census rows, and `total`."""
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    place(path, data)
    out = {}
    for board in boards_in(data):
        out[str(board.get("id"))] = census_of(revisions(board))
    return {"boards": out, "total": sum(len(v) for v in out.values())}
