# SPDX-License-Identifier: AGPL-3.0-or-later
"""The shared-folder route for Working together (wtfolder, 9 November 2026, the spec's section 6): the transport
that passes a project's sealed envelopes through a folder the team already shares, such as OneDrive, Dropbox or a
network drive, with no server of Idiograph's in between.

It has the shape every transport has (transport.py):

    send(project_id, sealed) -> int                      this install's number for the envelope
    fetch(project_id, after) -> [(n, device, sealed)]    every envelope after n, in order
    listen(project_id, on_new) -> stop                   on_new() whenever something may have come

and what the relay's has besides: `seen`, `put_blob`, `get_blob`.

**The layout.** Inside the chosen folder, `Idiograph <the first 8 letters of the project id>/`:

    devices/<device id>/messages/<seq>.sealed     one envelope, the same bytes the relay carries
    devices/<device id>/blobs/<blob>.sealed       a sealed blob
    devices/<device id>/seen.json                 {sender device: the highest unbroken seq this device has read}
    invites/<invite id>/<time>-<random>.join      an invite's mailbox, each answer a file of its own

A device writes only in its own folder, and in an invite's under a name nobody else can take, always through a
temporary name beginning with a dot renamed into place, so a reader never takes a file half written and a sync
service never meets two writers on one file, which is what makes OneDrive keep a conflicted copy. `<seq>` is the
device's own counter from 1. A reader takes only names of the form `<digits>.sealed` in a folder named by a device
id, each sender's in order, and stops at a gap or at a file that will not open yet (a placeholder still syncing),
trying it again next time.

**The numbers.** There is no server to number messages across devices, so each install numbers them itself, in the
order it first read them, and keeps that order in `team-folder/<project>.json` beside its device file. `fetch`'s
`after` and `send`'s answer are those numbers, so they rise as the relay's do.

**Dropping.** `seen(project_id, n)` writes this device's `seen.json`, and each device deletes its own messages once
every other device on the roster has seen them. A device with no `seen.json` yet holds everything.

**Watching.** `listen` lists the folders on starting, every 15 seconds after, and at once when the computer wakes
from sleep (the wall clock jumping ahead of the monotonic one), with no file-watching library. It calls `on_new` when
something new has come.

**A missing folder.** When no folder is chosen, or the one chosen is not there (a drive not connected, a sync app
not signed in), every call is refused through `refuse(code, folder)`: `no_folder`, `folder_missing`. A file that
will not open is counted (`unopened`), so the page can say to keep the folder on this computer. Only the standard
library.
"""
from __future__ import annotations

import json
import os
import re
import secrets
import threading
import time
from pathlib import Path
from typing import Callable

INVITE_PREFIX = "invite/"
POLL = 15.0
# a wall clock ahead of the monotonic one by more than this, between two looks, means the computer slept
WOKE_AFTER = 5.0
MAX_BLOB = 200 * 1024 * 1024
SEALED = re.compile(r"^(\d{1,12})\.sealed$")
JOIN = re.compile(r"^\d{1,20}-[0-9a-f]{8,32}\.join$")
DEVICE = re.compile(r"^[0-9a-f]{32}$")
BLOB = re.compile(r"^[A-Za-z0-9_-]{16,64}$")
INVITE = re.compile(r"^[0-9a-f]{16,64}$")
# a temporary file of this device's older than this is left from a write that never finished, and removed
STALE_TMP = 600
# this install's numbering, there but not readable, is read again this many times, this many seconds apart
READ_TRIES = 5
READ_PAUSE = 0.1
# the files that would not open at the last look, by the shared folder's path, for the page's line
UNOPENED: dict = {}


class FolderError(Exception):
    """A call the folder could not take: `code` is `no_folder`, `folder_missing`, `invite_not_here`,
    `blob_not_here` or `too_large`."""

    def __init__(self, code: str, folder: str = ""):
        super().__init__(f"folder {code}: {folder}")
        self.code = code
        self.folder = folder


def _default_refuse(code: str, folder: str):
    raise FolderError(code, folder)


def team_folder_name(project_id: str) -> str:
    return f"Idiograph {str(project_id)[:8]}"


def write_new(target: Path, data: bytes) -> None:
    """`data` at `target` through a temporary name beginning with a dot in the same folder, renamed into place."""
    target.parent.mkdir(parents=True, exist_ok=True)
    tmp = target.with_name(f".{target.name}.{secrets.token_hex(4)}.tmp")
    with open(tmp, "wb") as out:
        out.write(data)
        out.flush()
        try:
            os.fsync(out.fileno())
        except OSError:
            pass
    os.replace(tmp, target)


def complete(data: bytes) -> bool:
    """Whether the bytes of a file look whole: something there, and an envelope (JSON) that parses. A sync service
    can show a file before all of it has come."""
    if not data:
        return False
    if data[:1] == b"{":
        try:
            json.loads(data.decode("utf-8"))
        except (UnicodeDecodeError, ValueError):
            return False
    return True


class FolderTransport:
    """One device's way through the shared folder `folder`. `device` is this install's device id, `state` the folder
    this install keeps its own numbering in (beside its device file, never in the shared folder), `peers` the other
    devices on the roster, whose `seen.json` decide what is dropped, `refuse(code, folder)` raises the refusal
    the caller wants (FolderError by default), and `team` this install's project id, where an invite it makes has
    its mailbox."""

    def __init__(self, device: str, folder, state, peers: list[str] | None = None,
                 refuse: Callable[[str, str], None] | None = None, team: str = ""):
        if not DEVICE.match(str(device or "")):
            raise ValueError("a device id is 32 hex")
        self.device = str(device)
        self.folder = str(folder or "").strip()
        self.state_dir = Path(state)
        self.peers = [p for p in (peers or []) if p != self.device]
        self._refuse = refuse or _default_refuse
        self.team = str(team or "")
        self._lock = threading.RLock()

    # where things are ------------------------------------------------------------------------------

    def shared(self) -> Path:
        """The chosen folder, refused when none is chosen or it is not there. Never made here: a folder that is
        missing means a drive or a sync app not connected, and making it would hide that."""
        if not self.folder:
            self._refuse("no_folder", "")
            raise FolderError("no_folder")
        root = Path(self.folder).expanduser()
        if not root.is_dir():
            self._refuse("folder_missing", self.folder)
            raise FolderError("folder_missing", self.folder)
        return root

    def base(self, project_id: str) -> Path:
        return self.shared() / team_folder_name(project_id)

    def own(self, project_id: str) -> Path:
        return self.base(project_id) / "devices" / self.device

    @staticmethod
    def _invite(project_id: str) -> str | None:
        if not str(project_id).startswith(INVITE_PREFIX):
            return None
        inv = str(project_id)[len(INVITE_PREFIX):]
        if not INVITE.match(inv):
            raise ValueError("an invite id is hex")
        return inv

    def invite_box(self, inv: str, make_in: str | None = None) -> Path | None:
        """An invite's mailbox: found in whichever project folder holds it (the joiner does not know the project's id
        before joining), or, with `make_in`, the place in that project's folder for a new one."""
        root = self.shared()
        for team_dir in sorted(root.glob("Idiograph *")):
            box = team_dir / "invites" / inv
            if box.is_dir():
                return box
        if make_in:
            return root / team_folder_name(make_in) / "invites" / inv
        return None

    # this install's own numbering ------------------------------------------------------------------

    def _state_path(self, project_id: str) -> Path:
        return self.state_dir / "team-folder" / f"{str(project_id)[:32]}.json"

    def _load(self, project_id: str) -> dict:
        held = {}
        for attempt in range(READ_TRIES):
            try:
                held = json.loads(self._state_path(project_id).read_text(encoding="utf-8"))
                break
            except FileNotFoundError:
                break
            except (OSError, ValueError):
                # there but not readable: never numbered afresh, which would number new messages below the reader's
                # mark and so pass them over (teamflake, 9 November 2026), but tried again and then refused
                if attempt + 1 == READ_TRIES:
                    raise OSError(f"could not read {self._state_path(project_id).name}") from None
                time.sleep(READ_PAUSE)
        if not isinstance(held, dict):
            held = {}
        held.setdefault("next", 0)
        held.setdefault("sent", 0)
        held.setdefault("index", {})
        held.setdefault("high", {})
        return held

    def _keep(self, project_id: str, held: dict) -> None:
        write_new(self._state_path(project_id), json.dumps(held, separators=(",", ":")).encode("utf-8"))

    @staticmethod
    def _number(held: dict, sender: str, seq: int) -> int:
        held["next"] = int(held["next"]) + 1
        held["index"][f"{sender}/{seq}"] = held["next"]
        held["high"][sender] = max(int(held["high"].get(sender) or 0), seq)
        return held["next"]

    # the transport's shape -------------------------------------------------------------------------

    def send(self, project_id: str, sealed: bytes) -> int:
        """One sealed envelope into this device's own folder, as `<seq>.sealed`. Answers this install's number for
        it, the next after everything it has read."""
        inv = self._invite(project_id)
        data = bytes(sealed)
        with self._lock:
            if inv is not None:
                box = self.invite_box(inv, make_in=self.team or None)
                if box is None:
                    self._refuse("invite_not_here", self.folder)
                    raise FolderError("invite_not_here", self.folder)
                write_new(box / f"{time.time_ns()}-{secrets.token_hex(8)}.join", data)
                return len(self._invite_files(box))
            messages = self.own(project_id) / "messages"
            self._sweep(messages)
            held = self._load(project_id)
            mine = [int(m.group(1)) for m in (SEALED.match(p.name) for p in self._list(messages)) if m]
            seq = max([int(held["sent"])] + mine) + 1
            write_new(messages / f"{seq}.sealed", data)
            held["sent"] = seq
            self._scan(project_id, held)
            n = held["index"].get(f"{self.device}/{seq}") or self._number(held, self.device, seq)
            self._keep(project_id, held)
            return int(n)

    def fetch(self, project_id: str, after: int) -> list[tuple[int, str, bytes]]:
        """Every envelope numbered above `after`, oldest first, as (n, sender's device id, sealed). New files are
        numbered as they are first read, each sender's in its own order. An invite's mailbox not in the folder is
        refused as `invite_not_here`: it may not have synced to this computer yet."""
        inv = self._invite(project_id)
        if inv is not None:
            box = self.invite_box(inv)
            if box is None:
                self._refuse("invite_not_here", self.folder)
                raise FolderError("invite_not_here", self.folder)
            out = []
            for k, path in enumerate(self._invite_files(box), 1):
                if k <= after:
                    continue
                data = self._read(path)
                if data is None:
                    break
                out.append((k, "", data))
            return out
        with self._lock:
            held = self._load(project_id)
            self._scan(project_id, held)
            self._keep(project_id, held)
            out = []
            for key, n in sorted(held["index"].items(), key=lambda kv: kv[1]):
                if n <= after:
                    continue
                sender, seq = key.split("/")
                data = self._read(self.base(project_id) / "devices" / sender / "messages" / f"{seq}.sealed")
                if data is not None:
                    out.append((int(n), sender, data))
            return out

    def listen(self, project_id: str, on_new: Callable[[], None]) -> Callable[[], None]:
        """Looks on starting, every POLL seconds and on waking, calling on_new() when the folder's files have
        changed since the last look. Answers a stop, which returns once the thread is done."""
        watch = _Watch(self, project_id, on_new)
        watch.start()
        return watch.stop

    # what all have read ----------------------------------------------------------------------------

    def seen(self, project_id: str, n: int) -> int:
        """This device has read everything numbered up to `n`: its `seen.json` written with each sender's highest
        unbroken seq, then its own messages that every other device on the roster has seen deleted. Answers how
        many that dropped."""
        with self._lock:
            held = self._load(project_id)
            per: dict = {}
            for key, k in held["index"].items():
                sender, seq = key.split("/")
                per.setdefault(sender, []).append((int(seq), int(k)))
            own = self.own(project_id)
            mark = self.read_seen(own / "seen.json")
            was = dict(mark)
            for sender, items in per.items():
                if sender == self.device:
                    continue
                top = int(mark.get(sender) or 0)
                for seq, k in sorted(items):
                    if seq <= top:
                        continue
                    if k > n or (top and seq > top + 1):
                        break
                    top = seq
                if top:
                    mark[sender] = top
            if mark != was or not (own / "seen.json").is_file():
                write_new(own / "seen.json", json.dumps(mark, sort_keys=True).encode("utf-8"))
            return self.drop(project_id)

    def drop(self, project_id: str) -> int:
        """This device's own messages that every other device on the roster has seen, deleted. None while it is
        alone on the roster, or while any of them has not written its `seen.json`."""
        if not self.peers:
            return 0
        devices = self.base(project_id) / "devices"
        upto = min(int(self.read_seen(devices / p / "seen.json").get(self.device) or 0) for p in self.peers)
        dropped = 0
        for path in self._list(self.own(project_id) / "messages"):
            m = SEALED.match(path.name)
            if m and int(m.group(1)) <= upto:
                try:
                    path.unlink()
                    dropped += 1
                except OSError:
                    pass
        return dropped

    @staticmethod
    def read_seen(path: Path) -> dict:
        try:
            got = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            return {}
        return {str(k): int(v) for k, v in got.items() if DEVICE.match(str(k)) and isinstance(v, int)} \
            if isinstance(got, dict) else {}

    # blobs ------------------------------------------------------------------------------------------

    def put_blob(self, project_id: str, blob: str, sealed) -> int:
        """A sealed blob, bytes or the path of a file holding them, into this device's blobs folder. Answers its
        size."""
        if not BLOB.match(str(blob)):
            raise ValueError("a blob's name is 16 to 64 letters, digits, - and _")
        data = Path(sealed).read_bytes() if isinstance(sealed, (str, Path)) else bytes(sealed)
        if len(data) > MAX_BLOB:
            raise FolderError("too_large", self.folder)
        write_new(self.own(project_id) / "blobs" / f"{blob}.sealed", data)
        return len(data)

    def get_blob(self, project_id: str, blob: str) -> bytes:
        """A sealed blob, from whichever device's folder holds it."""
        if not BLOB.match(str(blob)):
            raise ValueError("a blob's name is 16 to 64 letters, digits, - and _")
        devices = self.base(project_id) / "devices"
        for sender in self._device_dirs(devices):
            data = self._read(sender / "blobs" / f"{blob}.sealed", whole=False)
            if data is not None:
                return data
        raise FolderError("blob_not_here", self.folder)

    # reading the folder ----------------------------------------------------------------------------

    @staticmethod
    def _list(folder: Path) -> list[Path]:
        try:
            return list(folder.iterdir())
        except OSError:
            return []

    def _device_dirs(self, devices: Path) -> list[Path]:
        return sorted(p for p in self._list(devices) if DEVICE.match(p.name) and p.is_dir())

    def _invite_files(self, box: Path) -> list[Path]:
        return sorted((p for p in self._list(box) if JOIN.match(p.name)),
                      key=lambda p: (int(p.name.split("-", 1)[0]), p.name))

    def _read(self, path: Path, whole: bool = True) -> bytes | None:
        try:
            data = path.read_bytes()
        except OSError:
            return None
        if whole and not complete(data):
            return None
        return data

    def _scan(self, project_id: str, held: dict) -> None:
        """Number every message come since the last look, each sender's in seq order from the one after the highest
        numbered, stopping at a gap or a file that will not open yet. Forgets the numbers of files gone."""
        devices = self.base(project_id) / "devices"
        unopened = 0
        present = set()
        for sender_dir in self._device_dirs(devices):
            sender = sender_dir.name
            seqs = sorted(int(m.group(1)) for m in (SEALED.match(p.name) for p in self._list(sender_dir / "messages"))
                          if m)
            present.update(f"{sender}/{s}" for s in seqs)
            high = int(held["high"].get(sender) or 0)
            for seq in seqs:
                if seq <= high:
                    continue
                if high and seq != high + 1:
                    break  # a gap: the one before has not come yet
                if self._read(sender_dir / "messages" / f"{seq}.sealed") is None:
                    unopened += 1
                    break
                self._number(held, sender, seq)
                high = seq
        held["index"] = {k: v for k, v in held["index"].items() if k in present}
        UNOPENED[str(Path(self.folder).expanduser())] = unopened

    def _sweep(self, folder: Path) -> None:
        """This device's own temporary files left by a write that never finished."""
        now = time.time()
        for p in self._list(folder):
            if p.name.startswith(".") and p.name.endswith(".tmp"):
                try:
                    if now - p.stat().st_mtime > STALE_TMP:
                        p.unlink()
                except OSError:
                    pass

    def signature(self, project_id: str) -> tuple:
        """What `listen` compares between looks: every message and answer file's name and size."""
        inv = self._invite(project_id)
        if inv is not None:
            box = self.invite_box(inv)
            return tuple((p.name, _size(p)) for p in self._invite_files(box)) if box else ()
        devices = self.base(project_id) / "devices"
        out = []
        for sender_dir in self._device_dirs(devices):
            for p in sorted(self._list(sender_dir / "messages")):
                if SEALED.match(p.name):
                    out.append((sender_dir.name, p.name, _size(p)))
        return tuple(out)


def _size(path: Path) -> int:
    try:
        return path.stat().st_size
    except OSError:
        return -1


class _Watch(threading.Thread):
    """`listen`'s thread: a look on starting, every POLL seconds, and at once on waking."""

    TICK = 1.0

    def __init__(self, way: FolderTransport, project_id: str, on_new: Callable[[], None]):
        super().__init__(daemon=True, name=f"folder-watch-{str(project_id)[:8]}")
        self.way, self.project_id, self.on_new = way, project_id, on_new
        self._halt = threading.Event()
        self.looks = 0
        self.wakes = 0

    def stop(self) -> None:
        self._halt.set()
        if threading.current_thread() is not self:
            self.join(timeout=5)

    def _look(self, last):
        self.looks += 1
        try:
            now = self.way.signature(self.project_id)
        except Exception:
            return last  # a folder missing for now: look again next time
        if now != last:
            try:
                self.on_new()
            except Exception:
                pass  # a listener's fault is its own
        return now

    def run(self) -> None:
        last = self._look(None)
        due = time.monotonic() + POLL
        wall, mono = time.time(), time.monotonic()
        while not self._halt.wait(min(self.TICK, POLL)):
            w, m = time.time(), time.monotonic()
            woke = (w - wall) - (m - mono) > WOKE_AFTER
            wall, mono = w, m
            if woke:
                self.wakes += 1
            if woke or m >= due:
                last = self._look(last)
                due = time.monotonic() + POLL
