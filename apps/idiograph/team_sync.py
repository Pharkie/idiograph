"""Working together's owners and versions (wtowners, 8 November 2026, the spec's build 2 of the design Adam chose that
evening about 19:10: arrivals and waiting under the project's question, option A, and all the spec's defaults).

**One writer per participant.** The lead's roster (team.py) names who works on each participant, `owners` by the
participant's folder from the project's root, and on the GETs board, `gets_owner`, the lead where it names nobody.
Only that member's installs write the participant's files. `guard` is the one check, run where every write to a
participant's files takes the case's lock (`workbook.case_held`, the app's writes through `routes.writing` and the
command line's alike, so an agent is refused as the app is), and where the GETs file is written (`gets.write`). An
export, which reads a participant and writes a file of its own beside, is not refused. While Working together is off
nothing is refused and nothing here reads more than team.json.

**Versions.** A participant's version is its workbook, its PETs files and its progress file, each with its SHA-256,
zipped, inside the message when it fits one and otherwise as a sealed blob (above `INLINE_MOST`), with `n`, the
owner's count for it, one higher each time.

**Recordings travel once** (relayopen, 18 November 2026, Adam's ruling that day). With Send the recordings too ticked,
each recording goes on its own, a `recording` message naming its participant, its path, its SHA-256 and the sealed
blob that holds it, and only when its SHA-256 is not the one last sent, never inside every version. A computer that
already has a file with that SHA-256 takes nothing and fetches nothing. A new computer's first full copy sends them
again, and the others, holding them already, fetch nothing.

**When the relay says no** (relayopen, relayfix). A refusal of a message (the day's 100 MB or its count of messages
used, as much of the project waiting as the relay keeps, the relay full) holds what waits until the cap can have
lifted (`hold`: the day's at 00:00 UTC, the others an hour on), and only small messages are tried meanwhile. A
refusal of a file (a recording, or a version too large for a message) holds files alone (`files_hold`), and the
versions that fit a message go on. The page and `team send` say why in one line, never as no connection, naming
the computers that have not fetched what the relay holds when it says so. One file over the route's limit (80 MB
on the relay, 200 MB in a shared folder) is never sent and is said as such until it changes or goes. A first full
copy that stops partway resumes where it stopped (`copying`), and what changes meanwhile still goes; the recordings
go to new computers on their own count (`rec_copied`, `rec_copying`). A message whose blob cannot be fetched just
now, or whose recording finds its participant's lock busy, stops the look there, so nothing after it is marked read
and the relay keeps the blob for the next look. The GETs board's
is the GETs, LGETs and Trajectories files, `gets_version`. A version goes a minute after the owner's last save
(`WAIT`, by the files' times, so a save from the app, the command line or an agent counts alike), at once on Send
now, and on quit. A new computer on the roster gets every participant this member works on, and the GETs board when
it is his, at once: the first full copy. With nobody else on the team nothing is sent and nothing waits.

**Taking one in.** A version is applied only when its `n` is higher than the one held, and only from the member who
works on that participant (another's, or one for a participant this member works on, is dropped and noted in the
team log). Each file is checked against its SHA-256, written beside its place under a new name and renamed into
place under the case's lock, and left out of the files the app noted as its own writes, so the screens' "changes
made elsewhere" picks it up as any outside change. A version whose files are the ones here already moves the count
on and says nothing. Each arrival is kept by participant, with whose it was and when, for the line under the
project's question.

What this install has sent and taken in is kept in `.idiograph-team/sync.json` at the project's root (left out of a
sent copy with the rest of that folder): the transport's number read up to, each participant's count sent and the
files' prints it went with, each count taken in, the arrivals, the computers given a full copy, and when the last
try to send found no connection. One run at a time, under `.idiograph-team/sync.lock`.

The kinds of later builds (comments, suggestions, boards, hand-over) are passed to `HANDLERS` by kind when a module
registers one, and otherwise passed over. A kind in `EPOCH_NOW` is taken only when it was sealed under the roster's
present epoch: one sealed under an older key is dropped and noted, as team.py drops others.

**Messages of other builds going out** (wtreview2, 9 November 2026). `post` seals a message at once under the present
epoch's key (team.py `seal_envelope`) and keeps it, sealed, in `.idiograph-team/out.json` until the transport has
taken it: sent at once when it can be, and otherwise by the next look, before any version, so a comment written with
no connection goes when there is one. Nothing in that file can be read without the project's key.
"""
from __future__ import annotations

import base64
import contextlib
import hashlib
import io
import json
import os
import re
import threading
import time
import zipfile
from datetime import datetime, timedelta, timezone
from pathlib import Path, PurePosixPath
from typing import Callable

import board_history
import i18n
import locks
import project_pack as pack_mod
import server as srv
import team as team_mod
import workbook as wb_mod
from workbook import WorkbookError

STATE_FILE = "sync.json"
LOCK_FILE = "sync.lock"
# seconds after the owner's last save before a version goes, and between looks while the app is open
WAIT = 60
EVERY = 15
# a version's zip above this goes as a sealed blob, the message's padded size (1 MB) holding its base64 below it
INLINE_MOST = 640 * 1024
# seconds between looks at the relay while its live socket is up and says nothing (it says "new N" when a message
# comes, and each reconnect looks at once), so an idle computer costs the relay a call in five minutes, not fifteen
# seconds (relayfix, the review's W2)
LIVE_EVERY = 300
# seconds the relay's "project full" and "relay full" hold what waits before the next try
HOLD_FULL = 3600
# the relay's refusals that hold what waits, by its one word, and the one that refuses a single file. The day's
# three (its bytes, its files' share, its count of messages) hold until 00:00 UTC
HELD = {"day": "day", "day files": "day_files", "day messages": "day_messages", "project full": "project_full",
        "relay full": "relay_full", "project files today": "project_files_today", "files today": "files_today",
        "nobody to send to": "nobody", "blocked": "blocked", "closed": "closed", "no project": "gone"}
TILL_MIDNIGHT = ("day", "day_files", "day_messages", "project_files_today", "files_today")
# seconds a hold lasts that is not the day's: Cloudflare's rate rule and nobody to send to a minute, anything else
# an hour
HOLD_BLOCKED = 60
# an envelope the relay takes outside the day's bytes (relay/src/worker.js, LIMITS.small): the only messages tried
# while what waits is held
SMALL = 24 * 1024
# the largest file a route that names none takes (the shared folder's and the loopback's)
MOST_FILE = 200 * 1024 * 1024
# days a message whose recording or file cannot be taken just now (its participant's lock busy, the shared folder
# still bringing the file) is tried again before it is given up and dropped
LATER_DAYS = 3
# seconds a participant's list of recordings is kept between looks when its folders have not changed
RECORDINGS_KEPT = 300
# a new name beside a file's place, written then renamed into place
INCOMING = ".incoming"
GETS = "gets"
# the handlers of later builds' kinds, each `handler(root, team_json, inner_message)`
HANDLERS: dict[str, Callable] = {}
# who has a participant out for review, `review_with(root) -> {participant folder: member id}`, set by review.py
REVIEW_WITH: Callable | None = None
# the kinds taken only when sealed under the roster's present epoch, each build adding its own (review.py)
EPOCH_NOW: set = set()
# what `post` keeps until the transport takes it: sealed envelopes, in the order they were sealed
OUT_FILE = "out.json"
OUT_LOCK = "out.lock"

_RUN = threading.Lock()
_THREAD: dict = {}


def _routes():
    import idiograph_routes as routes
    return routes


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def team_on(root: Path) -> dict | None:
    data = team_mod.read_team(root)
    return data if data and data.get("on") is True and data.get("roster") else None


def owner_of(data: dict, folder: str) -> str:
    """Who works on a participant, `team.owner_here`: the one the lead named, else who added it, else the lead."""
    return team_mod.owner_here(data, folder)


def gets_owner(roster: dict) -> str:
    return str(roster.get("gets_owner") or roster.get("lead") or "")


def member_name(roster: dict, member: str) -> str:
    return str((team_mod.member_of(roster, member) or {}).get("name") or "")


def pseudonym(label: str) -> str:
    """A participant's label as a line names them, `Juno` for `P1 - Juno`."""
    return re.sub(r"^P\d+\s*-\s*", "", str(label or "")) or str(label or "")


def label_of(root: Path, folder: str) -> str:
    try:
        return _routes().label_for(Path(root) / folder)
    except Exception:
        return Path(folder).name


def alone(roster: dict) -> bool:
    return len(team_mod.roster_members(roster)) <= 1


# ------------------------------------------------------------------ the one writer

def project_root_of(path: Path) -> Path | None:
    """The project a file or folder is in: the nearest folder at or above it holding a project file."""
    here = Path(path)
    for folder in [here] + list(here.parents)[:4]:
        if (folder / srv.PROJECT_FILE).is_file():
            return folder
    return None


def refusal(root: Path, folder: str, data: dict) -> WorkbookError:
    roster = data.get("roster") or {}
    who = member_name(roster, owner_of(data, folder))
    return WorkbookError(i18n.t("team.refused.not_yours", participant=pseudonym(label_of(root, folder)), name=who),
                         code="not_yours")


def guard(path: Path) -> None:
    """`workbook.WRITE_GUARD`: a write to a participant's files refused, before the case's lock, when the project is
    worked on together and another member works on that participant."""
    case = wb_mod.case_folder(Path(path)) if Path(path).suffix else Path(path)
    root = project_root_of(case)
    if root is None:
        return
    data = team_on(root)
    if data is None:
        return
    try:
        folder = case.resolve().relative_to(root.resolve()).as_posix()
    except ValueError:
        return
    folder = "" if folder == "." else folder
    if owner_of(data, folder) != str(data.get("member") or ""):
        raise refusal(root, folder, data)


def gets_guard(root: Path) -> None:
    """`gets.WRITE_GUARD`: the GETs file's write refused when another member works on the GETs board."""
    data = team_on(Path(root))
    if data is None:
        return
    roster = data["roster"]
    if gets_owner(roster) != str(data.get("member") or ""):
        raise WorkbookError(i18n.t("team.refused.not_yours_gets", name=member_name(roster, gets_owner(roster))),
                            code="not_yours")


def install_guards() -> None:
    import gets as gets_mod
    wb_mod.WRITE_GUARD = guard
    gets_mod.WRITE_GUARD = gets_guard


def adding(root: Path, folders: list) -> list:
    """New participants a member adds here, his to work on: kept in team.json's `added` until the lead's computer
    names them in the list, so the guard lets his writes through and his versions go (landwt, 9 November 2026).
    Nothing for the lead, who works on every participant nobody else is named for. Answers the folders noted."""
    data = team_on(Path(root))
    if data is None:
        return []
    roster = data["roster"]
    me = str(data.get("member") or "")
    if not me or me == str(roster.get("lead") or ""):
        return []
    added = dict(data.get("added") or {})
    named = roster.get("owners") or {}
    new = [str(f) for f in folders if f and str(f) not in named and str(f) not in added]
    if new:
        added.update({f: me for f in new})
        team_mod.write_team(Path(root), dict(data, added=added))
    return new


def unadding(root: Path, folders: list) -> None:
    """An Add that failed: the participants it noted as his taken out of `added` again."""
    data = team_mod.read_team(Path(root)) if folders else None
    if not data:
        return
    added = {k: v for k, v in (data.get("added") or {}).items() if k not in folders}
    if added != (data.get("added") or {}):
        team_mod.write_team(Path(root), dict(data, added=added))


def claimed(root: Path, data: dict, what: str, inner: dict, base: Path) -> dict:
    """A version of a participant this computer has nothing of, from a member, not the lead, who added it: noted as
    his in `added`, and on the lead's computer named his in the list, signed and sent. Answers team.json as it is
    then. A participant here already, or one the list names, is never taken this way."""
    roster = data["roster"]
    sender = str(inner.get("member") or "")
    if (not sender or sender == str(roster.get("lead") or "") or what in (roster.get("owners") or {})
            or what in (data.get("added") or {}) or base.exists() or team_mod.member_of(roster, sender) is None):
        return data
    data = dict(data, added=dict(data.get("added") or {}, **{what: sender}))
    team_mod.write_team(Path(root), data)
    dev = team_mod.device() or {}
    if str(data.get("member") or "") == str(roster.get("lead") or "") and dev.get("id") in team_mod.lead_devices(roster):
        pinned = team_mod.deep(roster)
        pinned["owners"] = dict(pinned.get("owners") or {}, **{what: sender})
        data = team_mod.signed_out(Path(root), data, dev, pinned)
    return data


# ------------------------------------------------------------------ what this install has sent and taken in

def state_path(root: Path) -> Path:
    return Path(root) / team_mod.LOG_DIR / STATE_FILE


def load_state(root: Path, strict: bool = True) -> dict:
    """sync.json as kept, empty when there is none. One there that will not read is refused as busy, so the look
    writes nothing (`locks.read_json`): taken as empty, the next save would start every count afresh, a full copy
    would go again numbered from one and the others would drop this member's changes as older (teamflake). The
    page's line, which writes nothing, reads it with `strict` off and shows it as empty."""
    try:
        data = locks.read_json(state_path(root))
    except WorkbookError:
        if strict:
            raise
        data = {}
    data = data if isinstance(data, dict) else {}
    for key in ("sent", "held", "arrivals", "recordings", "too_large", "hold", "files_hold", "list_refused", "copying", "rec_copying"):
        data[key] = data.get(key) if isinstance(data.get(key), dict) else {}
    data["copied"] = list(data.get("copied") or [])
    # the computers given every recording. A state from before relayopen has none, and its versions carried the
    # recordings, so the computers it gave a full copy have them already (the review's A5)
    data["rec_copied"] = list(data["rec_copied"]) if isinstance(data.get("rec_copied"), list) else list(data["copied"])
    data["cursors"] = data.get("cursors") if isinstance(data.get("cursors"), dict) else {}
    return data


def way_key(way) -> str:
    """The transport's own count's name: each route numbers its messages its own way, so a change of route starts
    a count of its own."""
    return type(way).__name__


def save_state(root: Path, data: dict) -> None:
    target = state_path(root)
    target.parent.mkdir(exist_ok=True)
    tmp = locks.new_tmp(target)
    tmp.write_text(json.dumps(data, indent=1, ensure_ascii=False) + "\n", encoding="utf-8", newline="\n")
    os.replace(tmp, target)


def run_lock(root: Path):
    return locks.held(Path(root) / team_mod.LOG_DIR / LOCK_FILE)


# ------------------------------------------------------------------ the files a version carries

def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with open(path, "rb") as fh:
        for block in iter(lambda: fh.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def participant_files(case: Path, workbook: Path, recordings: bool = False) -> list[tuple[Path, str]]:
    """A participant's files as a version carries them, each with its path from the participant's folder: the
    workbook, the PETs files and the progress file in Working, and each PETs file's History chunks its boards name.
    With `recordings`, the recordings too, as `recordings_of` finds them (a version no longer carries them: they
    travel once each, relayopen). `board_history.HistoryAway` while a chunk a board names is not on this computer, so
    a version never carries part of a History (review 4)."""
    out = []
    try:
        out.append((workbook, workbook.relative_to(case).as_posix()))
    except ValueError:
        return []
    working = case / "Working"
    if working.is_dir():
        for p in sorted(working.iterdir()):
            if not p.is_file() or not p.name.startswith(workbook.stem + "."):
                continue
            if p.name.endswith(pack_mod.PROGRESS_TAIL) or pack_mod.PETS_FILE.search(p.name):
                out.append((p, f"Working/{p.name}"))
                # and its boards' History, the chunks their heads name in the folder beside it (historybuild)
                if pack_mod.PETS_FILE.search(p.name):
                    out += [(c, f"Working/{c.parent.name}/{c.name}") for c in board_history.named_files(p)]
    if recordings:
        out += recordings_of(case)
    return out


_RECORDINGS: dict = {}


def folder_mark(case: Path) -> tuple:
    """The times of a participant's folder and of the folders in it, which change when a file is added or taken
    away in either, read without walking the whole tree."""
    marks = []
    try:
        marks.append(Path(case).stat().st_mtime_ns)
        for p in os.scandir(case):
            if p.is_dir(follow_symlinks=False) and not p.name.startswith("."):
                marks.append((p.name, p.stat(follow_symlinks=False).st_mtime_ns))
    except OSError:
        return ()
    return tuple(marks)


def recordings_of(case: Path) -> list[tuple[Path, str]]:
    """A participant's recordings, each with its path from the participant's folder, hidden names left out. The
    list is kept while the folder's mark stands, and walked again at least every RECORDINGS_KEPT seconds, so a look
    does not walk every participant's folder (the review's A13)."""
    key = str(case)
    mark = folder_mark(case)
    kept = _RECORDINGS.get(key)
    if kept and kept[0] == mark and time.monotonic() - kept[1] < RECORDINGS_KEPT:
        return list(kept[2])
    found = walked_recordings(case)
    _RECORDINGS[key] = (mark, time.monotonic(), found)
    return list(found)


def walked_recordings(case: Path) -> list[tuple[Path, str]]:
    out = []
    for p in sorted(Path(case).rglob("*")):
        rel = PurePosixPath(p.relative_to(case).as_posix())
        if p.is_file() and not p.is_symlink() and pack_mod.kind_in_case(rel) == "audio" \
                and not any(part.startswith(".") for part in rel.parts):
            out.append((p, str(rel)))
    return out


def gets_files(root: Path) -> list[tuple[Path, str]]:
    out = [(Path(root) / name, name) for name in pack_mod.GETS_FILES if (Path(root) / name).is_file()]
    # and the GETs' and LGETs' History, the chunks their boards name beside them (historybuild), away while one is not
    # on this computer (see `participant_files`)
    for path, _name in list(out):
        if board_history.folder_of(path).name in pack_mod.GETS_HISTORY:
            out += [(c, f"{c.parent.name}/{c.name}") for c in board_history.named_files(path)]
    return out


def allowed_in_case(rel: str) -> bool:
    """A file's path in a version a participant's folder may take: the workbook, the progress file, a PETs file in
    Working or a recording, never a path out of the folder or a hidden name."""
    path = PurePosixPath(rel)
    if path.is_absolute() or not path.parts or any(part in ("", ".", "..") or part.startswith(".")
                                                   for part in path.parts):
        return False
    kind = pack_mod.kind_in_case(path)
    if kind is None:
        return path.suffix.lower() == ".xlsx" or path.name.endswith(pack_mod.PROGRESS_TAIL)
    if kind == "pets":
        return (len(path.parts) == 2 and path.parts[0] == "Working" and bool(pack_mod.PETS_FILE.search(path.name))) \
            or pack_mod.history_chunk(path.parts)
    return kind == "audio"


def allowed_folder(root: Path, folder: str) -> Path | None:
    path = PurePosixPath(str(folder or ""))
    if path.is_absolute() or not path.parts or any(part in ("", ".", "..") or part.startswith(".")
                                                   or part in _routes().SKIP_DIRS for part in path.parts):
        return None
    case = (Path(root) / Path(*path.parts)).resolve()
    try:
        case.relative_to(Path(root).resolve())
    except ValueError:
        return None
    return case


def prints(files: list[tuple[Path, str]], before: dict) -> dict:
    """Each file's size, time and SHA-256 by its path in the version, the SHA-256 taken again only when the size or
    the time moved since `before`."""
    out = {}
    for path, rel in files:
        try:
            st = path.stat()
        except OSError:
            continue
        was = before.get(rel)
        if isinstance(was, list) and len(was) == 3 and was[0] == st.st_size and was[1] == st.st_mtime_ns:
            out[rel] = was
        else:
            out[rel] = [st.st_size, st.st_mtime_ns, sha256(path)]
    return out


def same_content(a: dict, b: dict) -> bool:
    return {k: v[2] for k, v in a.items()} == {k: v[2] for k, v in (b or {}).items() if isinstance(v, list)}


def newest(files: list[tuple[Path, str]]) -> float:
    times = []
    for path, _rel in files:
        try:
            times.append(path.stat().st_mtime)
        except OSError:
            pass
    return max(times, default=0.0)


def mine(root: Path, data: dict, every: bool = False) -> list[dict]:
    """What this member works on, each `{"what": folder or GETS, "files", "lock", "own"}`: his participants and the
    GETs board when it is his. With `every`, the lead's first full copy, every participant and the GETs board."""
    roster = data["roster"]
    me = str(data.get("member") or "")
    out = []
    for p in _routes().participant_books(root):
        own = owner_of(data, p["folder"]) == me
        if not p["folder"] or not (own or every):
            continue
        case = Path(root).resolve() / p["folder"]
        try:
            files = participant_files(case, Path(p["workbook"]).resolve())
        except board_history.HistoryAway:
            # a History not all here yet waits, never sent in part (review 4)
            continue
        recs = recordings_of(case) if data.get("recordings") is True else []
        out.append({"what": p["folder"], "files": files, "lock": case / "Working" / locks.NAME, "own": own,
                    "recordings": recs})
    if gets_owner(roster) == me or every:
        try:
            files = gets_files(root)
        except board_history.HistoryAway:
            files = []
        if files:
            out.append({"what": GETS, "files": files, "lock": locks.root_lock(root), "own": gets_owner(roster) == me})
    return out


def waiting(root: Path, data: dict, state: dict, items: list | None = None) -> list[dict]:
    """What of this member's has changed since it last went, each item of `mine` (or of `items`, `mine` already
    read) with its prints."""
    out = []
    for item in mine(root, data) if items is None else items:
        was = (state["sent"].get(item["what"]) or {}).get("print") or {}
        now = prints(item["files"], was)
        if not same_content(now, was):
            out.append(dict(item, print=now))
    return out


# ------------------------------------------------------------------ sending

def zipped(files: list[tuple[Path, str]]) -> tuple[bytes, list[dict]]:
    buf = io.BytesIO()
    listed = []
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as z:
        for path, rel in files:
            data = path.read_bytes()
            z.writestr(rel, data)
            listed.append({"name": rel, "sha": hashlib.sha256(data).hexdigest(), "size": len(data)})
    return buf.getvalue(), listed


class FilesHeld(Exception):
    """A version that needs a blob while the relay holds this project's files: it waits, and versions that fit a
    message go on."""


class TooLarge(Exception):
    """A file over what the route takes, found before it is read (the review's A6)."""
    code = "too_large"


def most_file(way) -> int:
    """The largest sealed file `way` takes: the relay's for this project, the shared folder's, else MOST_FILE."""
    most = getattr(way, "max_blob", None)
    return int(most) if isinstance(most, int) and most > 0 else MOST_FILE


def on_file(exc: Exception) -> Exception:
    """A refusal marked as the file's, not the message's, so it holds files alone."""
    try:
        exc.on_file = True
    except AttributeError:
        pass
    return exc


def send_one(root: Path, data: dict, dev: dict, way, item: dict, n: int, files_held: bool = False) -> None:
    """One version, of a participant or of the GETs board, sealed and sent: its files read under their lock. One
    that needs a blob while files are held raises FilesHeld, and a refusal of its blob is marked `on_file`."""
    team = str(data.get("team") or "")
    epoch = int((data.get("roster") or {}).get("epoch") or 1)
    key = team_mod.project_key(team, epoch)
    if key is None:
        raise team_mod.TeamError(i18n.t("team.refused.no_key"), "no_key")
    with srv._lock, locks.held(item["lock"]):
        packed, listed = zipped(item["files"])
    body = {"n": int(n), "files": listed}
    if item["what"] != GETS:
        body["participant"] = item["what"]
    blob = None
    if len(packed) <= INLINE_MOST:
        body["zip"] = base64.b64encode(packed).decode("ascii")
    else:
        if files_held:
            raise FilesHeld()
        blob = os.urandom(16).hex()
        try:
            way.put_blob(team, blob, team_mod.aead_seal(key, packed, blob.encode("ascii")))
        except Exception as exc:  # noqa: BLE001 - marked, then raised as it came
            raise on_file(exc)
        body["blob"] = blob
    kind = "gets_version" if item["what"] == GETS else "version"
    sent(way, team, team_mod.seal_envelope(team, epoch, key, dev, str(data.get("member") or ""),
                                           team_mod.next_seq(team), kind, body), blob)


def sent(way, team: str, sealed: bytes, blob: str | None) -> None:
    """A message to the team, naming the blob it carries to a route that frees a blob with its message (the relay)."""
    if blob and getattr(way, "names_blobs", False):
        way.send(team, sealed, blob=blob)
    else:
        way.send(team, sealed)


def send_recording(data: dict, dev: dict, way, what: str, rel: str, path: Path, sha: str) -> None:
    """One recording, sealed whole as a blob and named by a `recording` message with its participant, path and
    SHA-256, read under nothing: a recording is not written while the app works. Its size is checked against the
    route's limit before it is read, so a file too large is never read into memory."""
    team = str(data.get("team") or "")
    epoch = int((data.get("roster") or {}).get("epoch") or 1)
    key = team_mod.project_key(team, epoch)
    if key is None:
        raise team_mod.TeamError(i18n.t("team.refused.no_key"), "no_key")
    # the seal adds its nonce and tag, 40 bytes at most
    if Path(path).stat().st_size + 40 > most_file(way):
        raise TooLarge()
    raw = Path(path).read_bytes()
    if hashlib.sha256(raw).hexdigest() != sha:
        raise WorkbookError("changed while it was read")
    blob = os.urandom(16).hex()
    try:
        way.put_blob(team, blob, team_mod.aead_seal(key, raw, blob.encode("ascii")))
    except Exception as exc:  # noqa: BLE001 - marked, then raised as it came
        raise on_file(exc)
    body = {"participant": what, "name": rel, "sha": sha, "size": len(raw), "blob": blob}
    sent(way, team, team_mod.seal_envelope(team, epoch, key, dev, str(data.get("member") or ""),
                                           team_mod.next_seq(team), "recording", body), blob)


def refused_word(exc) -> str:
    """The relay's (or a shared folder's) refusal that is not a fault of the connection, as one word of HELD's or
    "too_large", or "" for anything else."""
    status, said = getattr(exc, "status", None), str(getattr(exc, "error", "") or "")
    if (status == 413 and said == "too large") or getattr(exc, "code", "") == "too_large":
        return "too_large"
    if status and status >= 400 and said in HELD:
        return HELD[said]
    return ""


def hold_until(word: str) -> str:
    """When a hold the relay asked for can have lifted: the next 00:00 UTC for the day's, a minute for Cloudflare's
    rate rule and for nobody to send to, an hour on else."""
    t = datetime.now(timezone.utc)
    if word in TILL_MIDNIGHT:
        lifted = datetime(t.year, t.month, t.day, tzinfo=timezone.utc) + timedelta(days=1)
    elif word in ("blocked", "nobody"):
        # "nobody to send to" a minute too: a look that falls between the list's write at They match and the relay
        # hearing of the new computer meets it just after someone joined (review2)
        lifted = t + timedelta(seconds=HOLD_BLOCKED)
    else:
        lifted = t + timedelta(seconds=HOLD_FULL)
    return lifted.isoformat(timespec="seconds")


def hold_of(word: str, exc=None, data: dict | None = None) -> dict:
    """A hold as sync.json keeps it: its word, when it can have lifted, and with "project full" the computers the
    relay said have not fetched what it holds."""
    out = {"word": word, "until": hold_until(word)}
    if word == "gone":
        out["project"] = str(team_mod.relay_note(data or {}).get("project") or "")
    behind = [str(d) for d in getattr(exc, "behind", None) or [] if isinstance(d, str)]
    if behind:
        out["behind"] = behind
    return out


def held_now(state: dict, key: str = "hold") -> str:
    """The hold in force, its word, or "" when there is none or it has lifted. `key` "files_hold" reads the hold of
    files alone."""
    hold = state.get(key) or {}
    try:
        if hold.get("word") and datetime.fromisoformat(str(hold.get("until"))) > datetime.now(timezone.utc):
            return str(hold["word"])
    except ValueError:
        pass
    return ""


def lift_gone(data: dict, state: dict) -> None:
    """The hold for a project the relay no longer has, let go once the team no longer sends through the relay or its
    list of people names another project there. It is kept in the state given and written by the look that goes on."""
    hold = state.get("hold") or {}
    if hold.get("word") != "gone":
        return
    here = str(team_mod.relay_note(data).get("project") or "")
    if hold.get("project") != here or str(data.get("route") or "relay") != "relay":
        state["hold"] = {}


def resend_list(root: Path, data: dict) -> None:
    """The lead's list of computers sent to the relay once more after the day it was refused for (`lists today`) has
    ended, so the computer it names is let in without another change to the list (the review's L3)."""
    refused = (load_state(root, strict=False).get("list_refused") or {})
    try:
        due = refused.get("word") == "lists today" and datetime.fromisoformat(str(refused.get("until"))) <= datetime.now(timezone.utc)
    except ValueError:
        due = False
    roster = data.get("roster") or {}
    if not due or str(data.get("member") or "") != str(roster.get("lead") or ""):
        return
    try:
        way = team_mod.transport_for(data, team_mod.device() or {})
        team_mod.tell_relay(data, way, roster, root=root)
    except Exception:  # noqa: BLE001 - tried again at the next look
        pass


def seed_recordings(state: dict, item: dict) -> None:
    """A participant's recordings as sent before relayopen, when its versions carried them: their SHA-256s, taken
    from the version last sent, so the first look of this copy does not send each recording again (the review's
    A5)."""
    what = item["what"]
    kept = state["recordings"].get(what)
    if isinstance(kept, dict) and "sent" in kept:
        return
    was = ((state["sent"].get(what) or {}).get("print") or {})
    sent_shas = {rel: v[2] for rel, v in was.items() if isinstance(v, list) and len(v) == 3
                 and pack_mod.kind_in_case(PurePosixPath(rel)) == "audio"}
    state["recordings"][what] = dict(kept or {}, sent=sent_shas)


def recordings_due(state: dict, item: dict, again: bool) -> list[tuple[Path, str, str]]:
    """The recordings of an item to send, each (path, its path in the folder, its SHA-256): those whose SHA-256 is
    not the one last sent, or with `again` every one (a new computer's first copy), less any too large to send."""
    if not item.get("recordings"):
        return []
    what = item["what"]
    before = (state["recordings"].get(what) or {}).get("print") or {}
    now = prints(item["recordings"], before)
    sent_shas = (state["recordings"].get(what) or {}).get("sent") or {}
    state["recordings"][what] = dict(state["recordings"].get(what) or {}, print=now)
    out = []
    for path, rel in item["recordings"]:
        sha = (now.get(rel) or [0, 0, ""])[2]
        if not sha or state["too_large"].get(f"{what}\t{rel}") == sha:
            continue
        if again or sent_shas.get(rel) != sha:
            out.append((path, rel, sha))
    return out


def prune_too_large(root: Path, state: dict, own: list[dict], recordings_on: bool) -> None:
    """A refusal of a file too large let go once the file is gone, or no longer sent (the tick taken off, the
    participant no longer here), so its line goes with it (the review's A12)."""
    listed = {f"{item['what']}\t{rel}" for item in own for _p, rel in item.get("recordings") or []} \
        if recordings_on else set()
    for key in list(state["too_large"]):
        if "\t" in key:
            keep = key in listed
        else:
            case = allowed_folder(root, key) if key != GETS else Path(root)
            keep = case is not None and case.is_dir()
        if not keep:
            state["too_large"].pop(key, None)
    if not state["too_large"]:
        state.pop("too_large_most", None)


def push(root: Path, now: bool = False, dry_run: bool = False, recordings: bool = True) -> dict:
    """What has waited a minute since its last save sent, or with `now` all that waits, and to a computer new on the
    roster everything this member works on. Recordings go after the versions, each once, and only this member's
    own participants' (the owner sends them, the lead never sends another's). While the relay holds what waits
    (`hold`) nothing but `post`'s small messages is tried, and while it holds this project's files (`files_hold`)
    the versions that fit a message go on. A dry run sends nothing and writes nothing. `recordings` False leaves
    them for the next look (on quit). Answers `{"sent", "waiting", "offline", "held"}`."""
    data = team_on(root)
    if data is None:
        return {"sent": [], "waiting": 0, "offline": False}
    roster = data["roster"]
    if alone(roster):
        return {"sent": [], "waiting": 0, "offline": False}
    dev = team_mod.device() or {}
    if not dry_run:
        resend_list(root, data)
    state = load_state(root)
    lift_gone(data, state)
    held = held_now(state)
    kept_back = False
    if not dry_run:
        # what other builds kept, first: only the small ones while the relay holds what waits (the review's A7)
        # nothing is sent to a relay that has no project: the outbox waits (the review's L1)
        _gone, kept_back, word, exc = flush(root, data, small_only=bool(held)) if held != "gone" else (0, False, "", None)
        if word and not held:
            held = word
            state["hold"] = hold_of(word, exc, data)
    me = str(data.get("member") or "")
    lead = me == str(roster.get("lead") or "")
    others = sorted(d["id"] for m in team_mod.roster_members(roster) for d in m.get("devices") or []
                    if isinstance(d, dict) and d.get("id") and d.get("id") != dev.get("id"))
    own = mine(root, data)
    fresh = [d for d in others if d not in state["copied"]]
    copying = state["copying"] if state["copying"].get("for") == others else {"for": others, "done": []}
    done = set(copying.get("done") or []) if fresh else set()
    if fresh:
        # the first full copy: everything of this member's goes again, at once, for the computer that has none of
        # it, and from the lead every participant, which a computer with none of that participant takes as its
        # first copy. One stopped partway (the relay's day used, no connection) goes on from where it stopped, and
        # what changed since it went, of what the copy has sent already, goes as ever (the review's A1)
        first = [dict(item, print=prints(item["files"], {}), first=True)
                 for item in (mine(root, data, every=True) if lead else own) if item["what"] not in done]
        items = first + [item for item in waiting(root, data, state, own) if item["what"] in done]
    else:
        first = []
        items = waiting(root, data, state, own)
    items = [item for item in items if state["too_large"].get(item["what"]) != print_key(item["print"])]
    first_left = {item["what"] for item in items if item.get("first")}
    due = [item for item in items if now or item.get("first") or newest(item["files"]) <= time.time() - WAIT]
    # the recordings of this member's own participants, each whose SHA-256 has not gone, every one for a computer
    # that has not had them all (the review's A5: owners send their own, the lead no one else's)
    rec_fresh = [d for d in others if d not in state["rec_copied"]]
    rec_copying = state["rec_copying"] if state["rec_copying"].get("for") == others else {"for": others, "done": {}}
    recs = []
    if recordings:
        for item in own:
            if not item.get("recordings"):
                continue
            seed_recordings(state, item)
            done_recs = set((rec_copying.get("done") or {}).get(item["what"]) or []) if rec_fresh else set()
            recs += [(item["what"], path, rel, sha) for path, rel, sha in recordings_due(state, item, bool(rec_fresh))
                     if rel not in done_recs and (now or rec_fresh or newest([(path, rel)]) <= time.time() - WAIT)]
    if dry_run:
        return {"sent": [], "due": [item["what"] for item in due], "waiting": len(items) + len(recs), "offline": False,
                "dry_run": True}
    prune_too_large(root, state, own, data.get("recordings") is True)
    sent_now, offline = [], False
    files_held = held_now(state, "files_hold")
    try:
        way = team_mod.transport_for(data, dev) if not held else None
    except team_mod.TeamError:
        way, offline = None, True
    for item in due if way is not None else []:
        what = item["what"]
        if item.get("own", True):
            n = max(int((state["sent"].get(what) or {}).get("n") or 0), int(state["held"].get(what) or 0)) + 1
        else:
            # another's participant in the lead's first copy keeps the count it came with, so theirs comes after
            n = max(1, int(state["held"].get(what) or 0))
        try:
            send_one(root, data, dev, way, item, n, files_held=bool(files_held))
        except (WorkbookError, FilesHeld):
            continue
        except Exception as exc:  # noqa: BLE001 - the route's refusal, or no connection
            word = refused_word(exc)
            if word == "too_large":
                state["too_large"][what] = print_key(item["print"])
                state["too_large_most"] = most_file(way)
                continue
            if word and word != "gone" and getattr(exc, "on_file", False):
                # its blob refused: files wait, the versions that fit a message go on
                files_held = word
                state["files_hold"] = hold_of(word, exc, data)
                continue
            if word:
                held = word
                state["hold"] = hold_of(word, exc, data)
            else:
                offline = True
            break
        if item.get("own", True):
            state["sent"][what] = {"n": n, "print": item["print"], "at": now_iso()}
        state["too_large"].pop(what, None)
        if item.get("first"):
            copying["done"] = sorted(set(copying.get("done") or []) | {what})
            first_left.discard(what)
        sent_now.append(what)
    # a participant whose version was due and did not go sends no recording this pass, so a recording never comes
    # before the version that makes its folder on another computer (the review's A9)
    unsent = {item["what"] for item in due} - set(sent_now)
    recs_left = len(recs)
    if way is not None and not offline and not held and not files_held:
        for what, path, rel, sha in recs:
            if what in unsent:
                continue
            try:
                send_recording(data, dev, way, what, rel, path, sha)
            except WorkbookError:
                continue
            except Exception as exc:  # noqa: BLE001 - the route's refusal, or no connection
                word = refused_word(exc)
                if word == "too_large":
                    state["too_large"][f"{what}\t{rel}"] = sha
                    state["too_large_most"] = most_file(way)
                    recs_left -= 1
                    continue
                if word and word != "gone" and getattr(exc, "on_file", False):
                    # a recording refused holds recordings and other files alone (the review's A2)
                    files_held = word
                    state["files_hold"] = hold_of(word, exc, data)
                elif word:
                    held = word
                    state["hold"] = hold_of(word, exc, data)
                else:
                    offline = True
                break
            kept = state["recordings"].setdefault(what, {})
            kept["sent"] = dict(kept.get("sent") or {}, **{rel: sha})
            state["too_large"].pop(f"{what}\t{rel}", None)
            if rec_fresh:
                rec_copying.setdefault("done", {})
                rec_copying["done"][what] = sorted(set(rec_copying["done"].get(what) or []) | {rel})
            recs_left -= 1
            # kept after each recording, so a stop during a long upload does not send it again (the review's A10)
            state["rec_copying"] = rec_copying if rec_fresh else {}
            save_state(root, state)
    if not held:
        state["hold"] = {}
    if not files_held:
        state["files_hold"] = {}
    if fresh:
        # the computers have every version once each first-copy item has gone, whatever the recordings
        if not offline and not held and not first_left:
            state["copied"], state["copying"] = others, {}
        else:
            state["copying"] = copying
    if rec_fresh and recordings:
        if not offline and not held and not files_held and recs_left == 0:
            state["rec_copied"], state["rec_copying"] = others, {}
        else:
            state["rec_copying"] = rec_copying
    offline = offline or kept_back
    state["failed"] = now_iso() if offline else ""
    save_state(root, state)
    left = (sum(1 for item in items if item.get("own", True) and item["what"] not in sent_now) + len(read_out(root))
            + recs_left)
    return {"sent": sent_now, "waiting": left, "offline": offline, "held": held or files_held}


def print_key(print_: dict) -> str:
    """A version's files' SHA-256s in one line, to know a refused one again until it changes."""
    return hashlib.sha256(json.dumps({k: v[2] for k, v in sorted((print_ or {}).items())}).encode("utf-8")).hexdigest()


# ------------------------------------------------------------------ other builds' messages, sealed and kept until sent

def out_path(root: Path) -> Path:
    return Path(root) / team_mod.LOG_DIR / OUT_FILE


def read_out(root: Path) -> list[dict]:
    # one there that will not read is refused as busy, never taken as empty and written over (teamflake)
    data = locks.read_json(out_path(root))
    held = data.get("out") if isinstance(data, dict) else None
    return [x for x in held or [] if isinstance(x, dict) and x.get("sealed")]


def write_out(root: Path, held: list[dict]) -> None:
    target = out_path(root)
    target.parent.mkdir(exist_ok=True)
    tmp = locks.new_tmp(target)
    tmp.write_text(json.dumps({"out": held}, indent=1) + "\n", encoding="utf-8", newline="\n")
    os.replace(tmp, target)


def flush(root: Path, data: dict | None = None, small_only: bool = False) -> tuple[int, bool, str, object]:
    """What `post` kept, sent in order until the transport refuses one, with `small_only` (while the relay holds
    what waits) only while the next is small enough to go outside the day's bytes. Answers how many went, whether
    the transport could not be reached, and the relay's word when it refused one, with the refusal (the review's
    A7: never taken for no connection, so nothing larger is tried again every look)."""
    data = data or team_on(root)
    if data is None:
        return 0, False, "", None
    with locks.held(Path(root) / team_mod.LOG_DIR / OUT_LOCK):
        held = read_out(root)
        if not held:
            return 0, False, "", None
        team = str(data.get("team") or "")
        gone, offline, word, refusal = 0, False, "", None
        try:
            way = team_mod.transport_for(data, team_mod.device() or {})
            for item in held:
                sealed = base64.b64decode(item["sealed"])
                if small_only and len(sealed) > SMALL:
                    break
                way.send(team, sealed)
                gone += 1
        except Exception as exc:  # noqa: BLE001 - the relay's refusal, or no connection
            word = refused_word(exc)
            if word in ("", "too_large"):
                word, offline = "", True
            else:
                refusal = exc
        if gone:
            write_out(root, held[gone:])
    return gone, offline, word, refusal


def post(root: Path, kind: str, body: dict) -> dict:
    """One message of a later build's kind to the team: sealed now under the present epoch, signed by this computer
    as its member, kept sealed until the transport takes it, and sent at once when it can be. Answers `{"sent"}`,
    False when it waits for a connection. Refused while Working together is off or this computer has no key."""
    data = team_on(root)
    if data is None:
        raise team_mod.TeamError(i18n.t("team.refused.off"), "off")
    dev = team_mod.device()
    if not dev:
        raise team_mod.TeamError(i18n.t("team.refused.no_device"), "no_device")
    team = str(data.get("team") or "")
    epoch = int((data.get("roster") or {}).get("epoch") or 1)
    key = team_mod.project_key(team, epoch)
    if key is None:
        raise team_mod.TeamError(i18n.t("team.refused.no_key"), "no_key")
    sealed = team_mod.seal_envelope(team, epoch, key, dev, str(data.get("member") or ""), team_mod.next_seq(team),
                                    kind, body)
    with locks.held(Path(root) / team_mod.LOG_DIR / OUT_LOCK):
        write_out(root, read_out(root) + [{"kind": kind, "sealed": base64.b64encode(sealed).decode("ascii")}])
    flush(root, data, small_only=bool(held_now(load_state(root, strict=False))))
    # sent when nothing is left kept, this message with the rest
    try:
        left = read_out(root)
    except WorkbookError:
        left = [None]
    return {"sent": not left}


# ------------------------------------------------------------------ taking in

def unzipped(raw: bytes, listed: list) -> dict[str, bytes]:
    """The files of a version by their path, each checked against its SHA-256. Refused as tampered otherwise."""
    out = {}
    try:
        with zipfile.ZipFile(io.BytesIO(raw)) as z:
            for f in listed:
                name = str((f or {}).get("name") or "")
                got = z.read(name)
                if hashlib.sha256(got).hexdigest() != str(f.get("sha") or ""):
                    raise team_mod.TeamError(i18n.t("team.refused.tampered"), "tampered")
                out[name] = got
    except (zipfile.BadZipFile, KeyError, ValueError, OSError):
        raise team_mod.TeamError(i18n.t("team.refused.tampered"), "tampered") from None
    return out


def version_bytes(data: dict, way, body: dict, inner: dict | None = None) -> bytes:
    if body.get("blob"):
        blob = str(body["blob"])
        if not re.fullmatch(r"[0-9a-f]{32}", blob):
            raise team_mod.TeamError(i18n.t("team.refused.tampered"), "tampered")
        team = str(data.get("team") or "")
        sealed = fetched_blob(way, team, blob, inner)
        for key in team_mod.project_keys(team).values():
            try:
                return team_mod.aead_open(key, sealed, blob.encode("ascii"))
            except team_mod.TeamError:
                continue
        raise team_mod.TeamError(i18n.t("team.refused.tampered"), "tampered")
    try:
        return base64.b64decode(str(body.get("zip") or ""), validate=True)
    except ValueError:
        raise team_mod.TeamError(i18n.t("team.refused.tampered"), "tampered") from None


class Later(Exception):
    """A blob that could not be fetched just now (no connection, the relay's fault): the look stops at its message
    and leaves it unread, so the relay keeps the blob for the next look. `stuck` when it will not come by trying
    again (the relay has given this computer the file as often as it gives one), which the page says."""

    def __init__(self, said: str = "", stuck: bool = False):
        super().__init__(said)
        self.stuck = stuck


def young(inner: dict) -> bool:
    """A message sent less than LATER_DAYS ago, or one whose time will not read, which is tried again before it is
    given up."""
    try:
        at = datetime.fromisoformat(str(inner.get("sent") or ""))
    except ValueError:
        return True
    if at.tzinfo is None:
        at = at.replace(tzinfo=timezone.utc)
    return datetime.now(timezone.utc) - at < timedelta(days=LATER_DAYS)


def fetched_blob(way, team: str, blob: str, inner: dict | None = None) -> bytes:
    """A sealed blob fetched. One the relay no longer has is dropped as gone. One the shared folder has not brought
    yet (its small message came first) is tried again later, until the message is LATER_DAYS old (the review's
    A4), and any other fault is tried again later."""
    try:
        return way.get_blob(team, blob)
    except team_mod.TeamError:
        raise
    except Exception as exc:  # noqa: BLE001 - the relay's refusal, no connection, a folder not there
        status = getattr(exc, "status", None)
        if getattr(exc, "code", "") == "blob_not_here" and young(inner or {}):
            raise Later(str(exc)) from None
        if status == 429 and getattr(exc, "error", "") == "fetched too often":
            # the relay gives this computer the file no more: the look waits there, and the page says why
            raise Later("fetched too often", stuck=True) from None
        if status == 404 or getattr(exc, "code", "") == "blob_not_here":
            raise team_mod.TeamError(i18n.t("team.refused.tampered"), "blob_gone") from None
        raise Later(str(exc)) from None


def take_recording(root: Path, data: dict, way, inner: dict) -> str:
    """A recording come on its own: from the member who works on its participant, or the lead, to a path a
    recording may take, fetched only when this computer has no file with its SHA-256 there, checked and put in
    place under the participant's lock. Answers "applied", "same" or why it was dropped."""
    roster = data["roster"]
    body = inner.get("body") if isinstance(inner.get("body"), dict) else {}
    what, rel, sha = str(body.get("participant") or ""), str(body.get("name") or ""), str(body.get("sha") or "")
    blob = str(body.get("blob") or "")
    base = allowed_folder(root, what)
    if base is None:
        return "bad_participant"
    if not allowed_in_case(rel) or pack_mod.kind_in_case(PurePosixPath(rel)) != "audio" \
            or not re.fullmatch(r"[0-9a-f]{64}", sha) or not re.fullmatch(r"[0-9a-f]{32}", blob):
        return "bad_file"
    sender = str(inner.get("member") or "")
    if sender not in (owner_of(data, what), str(roster.get("lead") or "")):
        return "not_owner"
    target = base / Path(*PurePosixPath(rel).parts)
    # this member's own recording is never written over here, but one this computer does not have yet (a second
    # computer of the member's, taking its first copy) is taken (the review's A3)
    if owner_of(data, what) == str(data.get("member") or "") and target.exists():
        return "own"
    try:
        if target.is_file() and sha256(target) == sha:
            return "same"
    except OSError:
        pass
    team = str(data.get("team") or "")
    sealed = fetched_blob(way, team, blob, inner)
    raw = None
    for key in team_mod.project_keys(team).values():
        try:
            raw = team_mod.aead_open(key, sealed, blob.encode("ascii"))
            break
        except team_mod.TeamError:
            continue
    if raw is None or hashlib.sha256(raw).hexdigest() != sha:
        return "tampered"
    (base / "Working").mkdir(parents=True, exist_ok=True)
    with srv._lock, locks.held(base / "Working" / locks.NAME):
        place({rel: raw}, base)
    return "applied"


def place(files: dict[str, bytes], base: Path) -> None:
    """Each file written beside its place under a new name, then renamed into place, and left out of the files the
    app noted as its own writes, so the screens see a change made elsewhere. A board file's History chunks that the
    file as it was here named and the file that came names no longer are put aside (`board_history.supersede`); any other chunk is left (review
    4: a chunk the sender could not list is never a reason to delete one here)."""
    boards = [rel for rel in files if pack_mod.PETS_FILE.search(PurePosixPath(rel).name)
              or PurePosixPath(rel).name in pack_mod.GETS_FILES]
    named_before = {}
    for rel in boards:
        target = base / Path(*PurePosixPath(rel).parts)
        try:
            held = json.loads(target.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            continue
        named_before[rel] = {n for b in board_history.boards_in(held)
                             for n in board_history.names_of(board_history.head_of(b))}
    # the History chunks first, so a board file never names one not yet in place
    for rel, content in sorted(files.items(), key=lambda item: ".history/" not in item[0]):
        target = base / Path(*PurePosixPath(rel).parts)
        target.parent.mkdir(parents=True, exist_ok=True)
        tmp = target.with_name(f".{target.name}{INCOMING}")
        tmp.write_bytes(content)
        os.replace(tmp, target)
        wb_mod.WRITTEN.pop(str(target.resolve()), None)
    for rel, was in named_before.items():
        try:
            came = json.loads(files[rel].decode("utf-8"))
        except (ValueError, UnicodeDecodeError):
            continue
        now = {n for b in board_history.boards_in(came) for n in board_history.names_of(board_history.head_of(b))}
        folder = board_history.folder_of(base / Path(*PurePosixPath(rel).parts))
        # put aside as a write here puts them, never taken away at once (historyfix2)
        board_history.supersede(folder, sorted(was - now))


def same_files(files: dict[str, bytes], base: Path) -> bool:
    for rel, content in files.items():
        target = base / Path(*PurePosixPath(rel).parts)
        try:
            if sha256(target) != hashlib.sha256(content).hexdigest():
                return False
        except OSError:
            return False
    return True


def take_version(root: Path, data: dict, way, inner: dict, state: dict) -> str:
    """A participant's or the GETs board's version, applied when it is newer and from the member who works on it.
    Answers what came of it: "applied", "same", "older" or why it was dropped."""
    roster = data["roster"]
    body = inner.get("body") if isinstance(inner.get("body"), dict) else {}
    n = body.get("n")
    if not isinstance(n, int) or isinstance(n, bool) or n < 1:
        return "tampered"
    gets = inner.get("kind") == "gets_version"
    if gets:
        what, owner, base = GETS, gets_owner(roster), Path(root)
    else:
        what = str(body.get("participant") or "")
        base = allowed_folder(root, what)
        if base is None:
            return "bad_participant"
        data = claimed(root, data, what, inner, base)
        roster = data["roster"]
        owner = owner_of(data, what)
    held_n = int(state["held"].get(what) or 0)
    there = (Path(root) / pack_mod.GETS_FILES[0]).exists() if gets else base.exists()
    # the lead's first full copy of a participant, or of the GETs board, this computer has nothing of yet
    first = inner.get("member") == roster.get("lead") and held_n == 0 and not there
    if not first and inner.get("member") != owner:
        return "not_owner"
    if not first and owner == str(data.get("member") or ""):
        return "own"
    if n <= held_n:
        return "older"
    listed = body.get("files") if isinstance(body.get("files"), list) else []
    names = [str((f or {}).get("name") or "") for f in listed]
    if not names or any((n_ not in pack_mod.GETS_FILES and not pack_mod.gets_chunk(PurePosixPath(n_).parts)) if gets
                        else not allowed_in_case(n_) for n_ in names):
        return "bad_file"
    files = unzipped(version_bytes(data, way, body, inner), listed)
    lock = locks.root_lock(root) if gets else base / "Working" / locks.NAME
    if not gets:
        (base / "Working").mkdir(parents=True, exist_ok=True)
    with srv._lock, locks.held(lock):
        if same_files(files, base):
            state["held"][what] = n
            return "same"
        place(files, base)
    state["held"][what] = n
    if owner == str(data.get("member") or ""):
        # his own participant's first copy: what came is what he holds, so nothing waits to go back
        prior = (state["sent"].get(what) or {})
        on_disk = [(base / Path(*PurePosixPath(rel).parts), rel) for rel in files]
        state["sent"][what] = {"n": max(n, int(prior.get("n") or 0)), "print": prints(on_disk, {}), "at": now_iso()}
    elif not first:
        state["arrivals"][what] = {"member": str(inner.get("member") or ""), "at": now_iso(), "n": n}
    return "applied"


def builds() -> None:
    """The later builds' modules imported, so their kinds have their handlers before anything is read."""
    try:
        import review  # noqa: F401, PLC0415, it registers its kinds and REVIEW_WITH as it is imported
    except ImportError:
        pass


def epoch_of(raw: bytes) -> int:
    """The epoch an envelope says it was sealed under, read from its open head, 0 when it says none."""
    try:
        env = json.loads(raw.decode("utf-8") if isinstance(raw, (bytes, bytearray)) else raw)
        return int(env.get("epoch") or 0) if isinstance(env, dict) else 0
    except (ValueError, TypeError, UnicodeDecodeError):
        return 0


def pull(root: Path) -> dict:
    """What came for this project since the last look, opened, checked and taken in, in the order it came. Answers
    `{"applied": [what, ...], "offline"}`."""
    data = team_on(root)
    if data is None:
        return {"applied": [], "offline": False}
    builds()
    dev = team_mod.device() or {}
    team = str(data.get("team") or "")
    state = load_state(root)
    lift_gone(data, state)
    if held_now(state) in ("blocked", "closed", "gone"):
        # Cloudflare stops calls before the relay: none is made until the hold can have lifted (the abuse plan's M6).
        # A project the relay no longer has is not asked for again either
        return {"applied": [], "offline": False}
    try:
        way = team_mod.transport_for(data, dev)
        key = way_key(way)
        came = way.fetch(team, int(state["cursors"].get(key) or 0))
    except Exception as exc:  # noqa: BLE001 - the relay's refusal, or no connection
        if refused_word(exc) == "gone":
            state["hold"] = hold_of("gone", exc, data)
            save_state(root, state)
            return {"applied": [], "offline": False}
        return {"applied": [], "offline": True}
    applied, taken, later, stuck = [], [], False, False
    was = int(state["cursors"].get(key) or 0)
    for seq, sender, raw in came:
        try:
            got = take_one(root, data, dev, way, team, state, sender, raw, applied, taken)
        except Later as exc:
            # its blob could not be fetched just now: this message and those after it wait for the next look
            later, stuck = True, exc.stuck
            state["stuck"] = now_iso() if exc.stuck else ""
            break
        if got is not None:
            data = got
        state["cursors"][key] = max(int(state["cursors"].get(key) or 0), int(seq))
    save_state(root, state)
    seen = getattr(way, "seen", None)
    if not later:
        state["stuck"] = ""
    if int(state["cursors"].get(key) or 0) > was and callable(seen):
        # the mark of what this computer has read, so a message all have read is deleted, and the blob it names
        try:
            seen(team, int(state["cursors"].get(key) or 0))
        except Exception:
            pass
    return {"applied": applied, "taken": taken, "offline": False, "later": later, "stuck": stuck}


def take_one(root: Path, data: dict, dev: dict, way, team: str, state: dict, sender: str, raw: bytes,
             applied: list, taken: list) -> dict | None:
    """One message come, opened, checked and taken in, or dropped and noted. Answers team.json when taking it in
    changed it, or None. Raises Later when its blob could not be fetched just now."""
    if sender and sender == dev.get("id"):
        return None
    try:
        inner = team_mod.open_envelope(raw, data["roster"], team_mod.project_keys(team))
    except team_mod.TeamError as exc:
        team_mod.note_dropped(root, exc.code, str(sender or ""))
        return None
    if inner.get("device") == dev.get("id"):
        return None
    kind = inner.get("kind")
    if kind in EPOCH_NOW and epoch_of(raw) < int((data["roster"] or {}).get("epoch") or 1):
        team_mod.note_dropped(root, "old_epoch", str(sender or ""))
        return None
    try:
        if kind == "roster":
            body = inner.get("body") or {}
            if isinstance(body.get("n"), int) and body["n"] <= int((data["roster"] or {}).get("n") or 0):
                # one this computer had already, in the welcome or by the way it came first
                return None
            team_mod.take_roster(root, body)
            return team_on(root) or data
        if kind in ("version", "gets_version"):
            came_of = take_version(root, data, way, inner, state)
            if came_of == "applied":
                applied.append(GETS if kind == "gets_version" else str(inner["body"]["participant"]))
            elif came_of not in ("same", "older"):
                team_mod.note_dropped(root, came_of, str(inner.get("device") or ""))
            return team_on(root) or data
        if kind == "recording":
            try:
                came_of = take_recording(root, data, way, inner)
            except WorkbookError:
                # the participant's lock busy (the app or an agent writing): a recording has no next version to heal
                # it, so it is tried again at the next look until the message is days old (the review's A4)
                if young(inner):
                    raise Later("busy") from None
                raise
            if came_of not in ("applied", "same", "own"):
                team_mod.note_dropped(root, came_of, str(inner.get("device") or ""))
            return None
        if kind in TAKEN_HERE:
            took = TAKEN_HERE[kind](root, data, dev, inner)
            if took:
                taken.append(took)
            return team_on(root) or data
        handler = HANDLERS.get(str(kind))
        if handler is not None:
            handler(root, data, inner)
    except Later:
        raise
    except team_mod.TeamError as exc:
        team_mod.note_dropped(root, exc.code, str(inner.get("device") or ""))
    except WorkbookError as exc:
        team_mod.note_dropped(root, getattr(exc, "code", "") or "busy", str(inner.get("device") or ""))
    except Exception:
        team_mod.note_dropped(root, "could_not_read", str(inner.get("device") or ""))
    return None


# ------------------------------------------------------------------ the other kinds this one loop takes in (landwt)

def take_devices(root: Path, data: dict, dev: dict, inner: dict) -> str:
    """A member's change to his own computers, on the lead's computer, as `team take` does: `team.apply_devices`
    under the project's lock, with its line in the project's History."""
    roster = data["roster"]
    if str(data.get("member") or "") != str(roster.get("lead") or "") or dev.get("id") not in team_mod.lead_devices(roster):
        return ""
    import project_history as hist_mod
    with _routes().writing(root=root):
        changes = team_mod.apply_devices(root, team_on(root) or data, dev, inner)
        if changes:
            hist_mod.record(root, "team take", changes, {"by": "app"})
    return "devices" if changes else ""


def take_board(root: Path, data: dict, dev: dict, inner: dict) -> str:
    """A board a teammate sent to this member, or an answer to one this member sent, as `team board-take` takes it:
    `team_board.came_in` or `answered` under the project's lock, the record and the project's History written."""
    import project_history as hist_mod
    import team_board as board_mod
    body = inner.get("body") if isinstance(inner.get("body"), dict) else {}
    if body.get("to") != str(data.get("member") or ""):
        return ""
    with _routes().writing(root=root):
        kept = board_mod.read_ledger(root)
        if inner.get("kind") == board_mod.KIND:
            one = board_mod.came_in(root, inner, data["roster"], kept)
        else:
            one = board_mod.answered(root, inner, data["roster"], kept)
        if not one:
            return ""
        board_mod.write_ledger(root, kept)
        hist_mod.record(root, "team board-take", [one["change"]], {"by": "app"})
    return "board"


# the kinds other builds read with their own ops, taken in here too so one loop reads every kind
TAKEN_HERE: dict[str, Callable] = {"devices": take_devices, "board": take_board, "answer": take_board}


def sync(root: Path, now: bool = False, dry_run: bool = False, pull_too: bool = True) -> dict:
    """One look: what came taken in, then what waits sent. One run at a time for the project. `pull_too` False
    sends what waits and asks the route for nothing (the looks while the relay's live socket is up)."""
    if team_on(root) is None:
        return {"applied": [], "sent": [], "waiting": 0, "offline": False}
    if dry_run:
        return dict(push(root, now=now, dry_run=True), applied=[])
    with _RUN, run_lock(root):
        took = pull(root) if pull_too else {"applied": [], "offline": False}
        gave = push(root, now=now)
    return {"applied": took["applied"], "taken": took.get("taken") or [], "sent": gave["sent"],
            "waiting": gave["waiting"], "offline": took["offline"] or gave["offline"], "later": took.get("later", False),
            "stuck": took.get("stuck", False)}


# ------------------------------------------------------------------ what the project's page and the agents read

def status(root: Path) -> dict | None:
    """Working together on the project's page: None while it is off. On, `tags` by participant label, each
    `{"owner": name}` for a participant another member works on and `{"review": name}` for one of this member's out
    for review, `arrivals` today, newest first, each `{"name", "participant", "at"}`, `waiting`, how many of theirs
    have changed since they went (recordings not yet sent among them), `offline`, whether the last try to send found
    no connection, `held`, the line saying why the relay holds what waits, and `too_large`, the line naming files too
    large for the route (relayopen)."""
    data = team_on(root)
    if data is None:
        return None
    roster = data["roster"]
    me = str(data.get("member") or "")
    state = load_state(root, strict=False)
    builds()
    tags = {}
    review = {}
    if REVIEW_WITH is not None:
        try:
            review = dict(REVIEW_WITH(root) or {})
        except Exception:
            review = {}
    for p in _routes().participant_books(root):
        owner = owner_of(data, p["folder"])
        if owner != me:
            tags[p["label"]] = {"owner": member_name(roster, owner)}
        elif review.get(p["folder"]):
            tags[p["label"]] = {"review": member_name(roster, str(review[p["folder"]]))}
    today = datetime.now().astimezone().date()
    arrivals = []
    for what, came in state["arrivals"].items():
        try:
            at = datetime.fromisoformat(str(came.get("at")))
        except (ValueError, TypeError):
            continue
        if at.astimezone().date() != today:
            continue
        arrivals.append({"name": member_name(roster, str(came.get("member") or "")),
                         "participant": "" if what == GETS else pseudonym(label_of(root, what)),
                         "gets": what == GETS, "at": at.isoformat()})
    arrivals.sort(key=lambda a: a["at"], reverse=True)
    try:
        held_out = len(read_out(root))
    except WorkbookError:
        held_out = 0
    count = 0
    if not alone(roster):
        own = mine(root, data)
        count = len(waiting(root, data, state, own)) + held_out
        for item in own:
            if item.get("recordings"):
                seed_recordings(state, item)
                count += len(recordings_due(state, item, False))
    lift_gone(data, state)
    held = i18n.t("team.held.gone") if held_now(state) == "gone" else ""
    if not held and count > 0:
        held = held_line(data, state)
    if not held and state.get("stuck"):
        held = i18n.t("team.held.fetched_too_often")
    if not held:
        held = list_refused_line(state)
    return {"tags": tags, "arrivals": arrivals, "waiting": count, "offline": bool(state.get("failed")) and count > 0,
            "held": held, "too_large": too_large_line(root, data, state)}


def behind_names(data: dict, state_hold: dict) -> str:
    """The computers the relay said have not fetched what it holds, by their names on the list of people, this one
    left out: "Kit's MacBook, Sam". "" when it named none this computer knows."""
    dev = team_mod.device() or {}
    names = []
    for m in team_mod.roster_members((data or {}).get("roster") or {}):
        for d in m.get("devices") or []:
            if isinstance(d, dict) and d.get("id") in (state_hold.get("behind") or []) and d.get("id") != dev.get("id"):
                computer = team_mod.one_line(d.get("name"))[:team_mod.NAME_MOST]
                person = str(m.get("name") or "")
                names.append(i18n.t("team.held.computer", name=person, computer=computer) if computer else person)
    return ", ".join(n for n in names if n)


def list_refused_line(state: dict) -> str:
    """The line for the relay's refusal of the list of computers (`list_refused`), "" while there is none. It is
    said whether or not changes wait, since the computer it names cannot send or read until the list is taken."""
    refused = state.get("list_refused") or {}
    if refused.get("word") == "too many removed":
        return i18n.t("team.held.list_removed")
    if refused.get("word") == "lists today":
        return i18n.t("team.held.list_today")
    return ""


def held_line(data: dict, state: dict) -> str:
    """Why what waits is held, in one plain line, or "" while nothing holds it (relayopen). A hold of everything is
    said before a hold of files alone, which it covers."""
    word = held_now(state)
    if word == "day":
        return i18n.t("team.held.day")
    if word == "day_messages":
        return i18n.t("team.held.day_messages")
    if word == "project_full":
        who = behind_names(data, state.get("hold") or {})
        return i18n.t("team.held.project_full_who", who=who) if who else i18n.t("team.held.project_full")
    if word == "relay_full":
        return i18n.t("team.held.relay_full")
    if word == "blocked":
        return i18n.t("team.held.blocked")
    if word == "closed":
        return i18n.t("team.held.closed")
    if word == "nobody":
        return i18n.t("team.held.nobody")
    word = held_now(state, "files_hold")
    if word in ("day", "day_files", "project_files_today"):
        return i18n.t("team.held.files_day")
    if word == "files_today":
        return i18n.t("team.held.files_relay_today")
    if word == "nobody":
        return i18n.t("team.held.nobody")
    if word == "blocked":
        return i18n.t("team.held.blocked")
    if word == "closed":
        return i18n.t("team.held.closed")
    if word == "project_full":
        who = behind_names(data, state.get("files_hold") or {})
        return i18n.t("team.held.files_project_full_who", who=who) if who else i18n.t("team.held.files_project_full")
    if word == "relay_full":
        return i18n.t("team.held.files_relay_full")
    return ""


def too_large_line(root: Path, data: dict, state: dict) -> str:
    """A participant's files or a recording too large for the route, named in one plain line with the route's own
    limit, or "" for none. A refusal kept for files since changed, gone or no longer sent is not said again."""
    most = int(state.get("too_large_most") or MOST_FILE) // (1024 * 1024)
    for what in sorted(state.get("too_large") or {}):
        folder = what.split("\t", 1)[0]
        participant = pseudonym(label_of(root, folder)) if folder != GETS else i18n.t("team.cli.gets_board")
        if (data.get("route") or "relay") == "folder":
            return i18n.t("team.held.too_large_folder", participant=participant, mb=most)
        return i18n.t("team.held.too_large", participant=participant, mb=most)
    return ""


# ------------------------------------------------------------------ the server's own looks

def live_now(stop) -> bool:
    """Whether a route's live socket is up: the relay's says so, and a route with none never is."""
    return bool(getattr(getattr(stop, "__self__", None), "connected", False))


def looks(roots: Callable[[], list]) -> None:
    """The server's thread: every EVERY seconds what waits is sent, and the route is asked what came. While the
    relay's live socket is up it is asked only when the socket says something came, when the last look left a
    message for later, and every LIVE_EVERY seconds besides, so a computer left open does not spend the relay's
    daily calls (the review's W2). A shared folder is looked at every time."""
    wake = threading.Event()
    stops: dict = {}
    woken: set = set()
    asked: dict = {}
    again: set = set()

    def told(key: str):
        def on_new():
            woken.add(key)
            wake.set()
        return on_new

    while not _THREAD.get("stop"):
        for root in list(roots() or []):
            root = Path(root)
            if not root.is_dir() or team_on(root) is None:
                continue
            key = str(root)
            # tried again each look until a route listens, a relay project made since among the reasons (relaywire)
            if held_now(load_state(root, strict=False)) == "gone":
                # a socket already listening is closed too, or it tries again every minute (the review's L2)
                if stops.get(key):
                    try:
                        stops[key]()
                    except Exception:
                        pass
                    stops[key] = None
            elif stops.get(key) is None:
                data = team_on(root)
                try:
                    way = team_mod.transport_for(data, team_mod.device() or {})
                    stops[key] = way.listen(str(data.get("team") or ""), told(key))
                except Exception:
                    stops[key] = None
            ask = (not live_now(stops.get(key)) or key in woken or key in again
                   or time.monotonic() - asked.get(key, 0.0) >= LIVE_EVERY)
            woken.discard(key)
            try:
                got = sync(root, pull_too=ask)
                if ask:
                    asked[key] = time.monotonic()
                    # a file the relay will give this computer no more is not asked for at every look: the
                    # LIVE_EVERY look is enough (review2's L1)
                    (again.add if got.get("later") and not got.get("stuck") else again.discard)(key)
            except Exception:
                pass
        wake.wait(EVERY)
        wake.clear()
    for stop in stops.values():
        if stop:
            try:
                stop()
            except Exception:
                pass


def start(roots: Callable[[], list]) -> None:
    """The looks started once, in the server alone, and what waits sent at once on quit."""
    if _THREAD.get("thread"):
        return
    thread = threading.Thread(target=looks, args=(roots,), daemon=True, name="team-sync")
    _THREAD["thread"] = thread
    thread.start()
    import atexit
    atexit.register(on_quit, roots)


def on_quit(roots: Callable[[], list]) -> None:
    """What waits sent at once, the recordings left for the next look, so quitting never sits uploading them (the
    review's A10)."""
    _THREAD["stop"] = True
    for root in list(roots() or []):
        try:
            if Path(root).is_dir() and team_on(Path(root)) is not None:
                with _RUN, run_lock(Path(root)):
                    push(Path(root), now=True, recordings=False)
        except Exception:
            pass
