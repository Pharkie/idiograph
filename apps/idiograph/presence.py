"""Another computer with the same project folder open (sharedopen, 20 November 2026, Adam's ruling that day).

A project folder kept on a shared or synced drive (Dropbox, OneDrive, Google Drive, iCloud) and opened on two
computers at once loses work: Idiograph's locks hold on one computer only, so whoever saves last overwrites the
other, or the sync app makes a copy such as "Mabel 2.xlsx". Working together avoids it, since each person keeps a
copy of their own, but nothing told someone who had simply put the project on a shared drive.

**The presence file.** While a page is in front of a project, the server keeps `.idiograph-open/<id>.json` inside the
project's folder: this install's id, the computer's plain name as Working together shows it (`team.computer_name`),
the app and the time. It is written whole through a temporary file renamed into place, about once a minute with the
page's beat (`sync`, called from `server.api_beat` and the idle watcher), by a worker thread of its own that the beat only hands the places to, so a stalled shared folder never holds a beat's answer, and taken away when the page leaves the
project or the server stops (`server.finish`, which waits at most two seconds for the worker). The id is one random one for each install, kept in `presence-id.json`
beside the app's settings, with a mark of this computer's hardware added to the key written in the file, so a settings folder cloned onto another Mac by Migration Assistant still names it (Working together's device exists only once it is on, so it cannot serve). No failure to
write or to read it ever stops anything: each is answered as if it were not there.

**Another computer's.** `others` is the names of the computers whose file in the folder carries another id and a time
less than FRESH seconds old (five minutes, since sync apps are slow). The id and the time are read from the file's
own words, never its name or its modified time, so a conflict copy a sync app made of it counts once for its owner,
and this install's own id is never another computer. The project's page shows one line while there are any, and
`project show` answers them as `open_elsewhere` for an agent.

**What it is not.** A dot-named folder at the project's root: no participant (`participants`, `team_folders` and the
case list skip dot-names), never in Share a copy (`project_pack.LEFT_OUT`), never in Working together (the team's
walks skip dot-names), not read by the restore points (they skip dot-folders) and not a writer for Remove to the
Trash (`trash.busy` skips dot-folders, and the folder goes to the Trash with the rest). A demo's folder is never
written."""
from __future__ import annotations

import hashlib
import json
import os
import secrets
import threading
import time
import uuid
from pathlib import Path

import app_identity
import locks
import server as srv

DIR = ".idiograph-open"
ID_FILE = "presence-id.json"
# a file older than this is taken as gone: a sync app can be minutes behind
FRESH = 5 * 60
# a project's file is rewritten when it is this old, the page's beat being thirty seconds
EVERY = 55
# the most files read in the folder, and the most one may hold
MOST = 40
SIZE = 4096

_LOCK = threading.RLock()
# each project folder written for, by its path, and when (monotonic)
HELD: dict = {}
_ID: list = [None, None]
# each other computer's file as last looked at, by project and key: its time and when that time last changed
LAST: dict = {}


def id_path() -> Path:
    return Path(srv.CONFIG_PATH).parent / ID_FILE


def install_id() -> str:
    """This install's id, made once and kept beside the settings; a random one for this run when it cannot be kept."""
    path = id_path()
    with _LOCK:
        if _ID[0] == str(path) and _ID[1]:
            return _ID[1]
        got = ""
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            got = str(data.get("id") or "") if isinstance(data, dict) else ""
        except (OSError, ValueError):
            got = ""
        if not got:
            got = secrets.token_hex(8)
            try:
                path.parent.mkdir(parents=True, exist_ok=True)
                tmp = locks.new_tmp(path)
                tmp.write_text(json.dumps({"id": got}) + "\n", encoding="utf-8", newline="\n")
                os.replace(tmp, path)
            except OSError:
                pass
        _ID[0], _ID[1] = str(path), got
        return got


def hardware() -> str:
    """A short mark of this computer's hardware (its network address), so a settings folder cloned onto another Mac by
    Migration Assistant or a restore, id file and all, still gives that Mac a key of its own."""
    try:
        node = uuid.getnode()
        if (node >> 40) & 1:        # getnode's random stand-in when it finds no address: a new one each run, so no mark
            return ""
        return hashlib.sha256(str(node).encode()).hexdigest()[:8]
    except Exception:
        return ""


def key_of(ident: str) -> str:
    """The id a file carries: the install's id and this hardware's mark."""
    if not ident:
        return ""
    mark = hardware()
    return f"{ident}.{mark}" if mark else ident


def current() -> str:
    """The key this install writes and compares: the id as the server holds it (made if need be), the same one in
    both. Where this process holds none, as the command line, the one on disk, never made."""
    try:
        path = str(id_path())
        if _ID[0] == path and _ID[1]:
            return key_of(_ID[1])
    except Exception:
        pass
    return key_of(known_id())


def known_id() -> str:
    """This install's id if it has one, read and never made, so a read by the command line writes nothing."""
    try:
        data = json.loads(id_path().read_text(encoding="utf-8"))
        return str(data.get("id") or "") if isinstance(data, dict) else ""
    except (OSError, ValueError):
        return ""


def computer() -> str:
    import team
    try:
        return team.computer_name()
    except Exception:           # a name is never worth a failure
        return ""


def write(root, ident: str = "", name: str = "", now: float | None = None) -> bool:
    """This install's file in the project's folder, whole through a temporary file renamed into place. False when it
    could not be written, which is never an error."""
    try:
        ident = ident or key_of(install_id())
        folder = Path(root) / DIR
        folder.mkdir(exist_ok=True)
        target = folder / f"{ident}.json"
        tmp = locks.new_tmp(target)
        body = {"id": ident, "name": name or computer(), "app": getattr(srv, "APP", ""), "time": now or time.time()}
        tmp.write_text(json.dumps(body, ensure_ascii=False) + "\n", encoding="utf-8", newline="\n")
        os.replace(tmp, target)
        return True
    except Exception:
        return False


def remove(root, ident: str = "") -> None:
    """This install's file taken away, and the folder when it holds nothing else. Silent."""
    try:
        ident = ident or key_of(install_id())
        folder = Path(root) / DIR
        (folder / f"{ident}.json").unlink(missing_ok=True)
        try:
            folder.rmdir()
        except OSError:
            pass
    except Exception:
        pass


def others(root, ident: str = "", now: float | None = None) -> list[str]:
    """The names of the other computers whose file in the project's folder is fresh, each once, in a steady order.
    Reads only; nothing in the folder is changed."""
    out: list = []
    if len(LAST) > 400:
        LAST.clear()
    try:
        ident = ident or current()
        now = time.time() if now is None else now
        folder = Path(root) / DIR
        if folder.is_symlink() or not folder.is_dir():
            return []
        seen = set()
        for i, entry in enumerate(sorted(os.scandir(folder), key=lambda e: e.name)):
            if i >= MOST:
                break
            try:
                if not entry.name.endswith(".json") or entry.is_symlink() or entry.stat().st_size > SIZE:
                    continue
                data = json.loads(Path(entry.path).read_text(encoding="utf-8"))
                when = float(data["time"])
                who = str(data["id"])
            except (OSError, ValueError, KeyError, TypeError):
                continue
            if who == ident or who in seen:
                continue
            # fresh by the file's own time, or, for a computer whose clock is far off, because its time has changed
            # since this install last looked, within the last five minutes (a file seen once, with an old time, waits
            # for its next write)
            mark = (str(root), who)
            before = LAST.get(mark)
            mono = time.monotonic()
            if before is None:
                LAST[mark] = (when, None)
            elif before[0] != when:
                LAST[mark] = (when, mono)
            moved = LAST[mark][1]
            if abs(now - when) >= FRESH and not (moved is not None and mono - moved < FRESH):
                continue
            seen.add(who)
            name = " ".join(str(data.get("name") or "").split())[:80]
            out.append(name or "")
    except Exception:
        return []
    return sorted(out)


def roots_of(shown) -> dict:
    """The projects the pages in front now are on, by path: Idiograph's own, never a demo's."""
    want: dict = {}
    for at in shown or []:
        try:
            root = srv.project_named(at)
            if srv.is_demo_root(root) or not Path(root).is_dir():
                continue
            want[str(root)] = root
        except Exception:
            continue
    return want


def _work(shown) -> None:
    """The files as the pages in front now (`shown`, the projects they name, or None for the server stopping) need
    them. Runs on the worker thread, never a request's."""
    try:
        t = time.monotonic()
        want = roots_of(shown)
        with _LOCK:
            for key, root in want.items():
                if t - HELD.get(key, -1e9) >= EVERY:
                    write(root)
                    HELD[key] = t
            for key in [k for k in HELD if k not in want]:
                remove(key)
                HELD.pop(key, None)
    except Exception:
        pass


# what the pages in front want, handed to the worker; the worker wakes on it, and is idle when it has caught up
_WANT: list = [[]]
_WAKE = threading.Event()
_IDLE = threading.Event()
_IDLE.set()
_START = threading.Lock()
_WORKER: list = [None]


def _run() -> None:
    while True:
        _WAKE.wait()
        _WAKE.clear()
        shown = _WANT[0]
        _work(shown)
        if not _WAKE.is_set():
            _IDLE.set()


def sync(shown, wait: float = 0.0) -> None:
    """Hand the worker the places the pages in front now name, or None for the server stopping, and answer at once:
    a stalled shared folder (iCloud, OneDrive, a network share) holds the worker and never a beat's answer or a Quit.
    `wait`, seconds, waits that long for the worker to catch up (`finish` waits two, a check a few). Silent."""
    try:
        if getattr(srv, "APP", "") != app_identity.DEFAULT:
            return
        with _START:
            if _WORKER[0] is None or not _WORKER[0].is_alive():
                _WORKER[0] = threading.Thread(target=_run, daemon=True, name="presence")
                _WORKER[0].start()
            _WANT[0] = shown
            _IDLE.clear()
            _WAKE.set()
        if shown is None and not wait:
            wait = 2.0
        if wait:
            _IDLE.wait(wait)
    except Exception:
        pass
