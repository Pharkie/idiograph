"""Working together's owners and versions (wtowners, 8 November 2026, the spec's build 2 of the design Adam chose that
evening about 19:10: arrivals and waiting under the project's question, option A, and all the spec's defaults).

**One writer per participant.** The lead's roster (team.py) names who works on each participant, `owners` by the
participant's folder from the project's root, and on the GETs board, `gets_owner`, the lead where it names nobody.
Only that member's installs write the participant's files. `guard` is the one check, run where every write to a
participant's files takes the case's lock (`workbook.case_held`, the app's writes through `routes.writing` and the
command line's alike, so an agent is refused as the app is), and where the GETs file is written (`gets.write`). An
export, which reads a participant and writes a file of its own beside, is not refused. While Working together is off
nothing is refused and nothing here reads more than team.json.

**Versions.** A participant's version is its workbook, its PETs files and its progress file, its recordings too when
Send the recordings too is ticked, each with its SHA-256, zipped, inside the message when it fits one and otherwise
as a sealed blob (above `INLINE_MOST`), with `n`, the owner's count for it, one higher each time. The GETs board's
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
import hashlib
import io
import json
import os
import re
import threading
import time
import zipfile
from datetime import datetime, timezone
from pathlib import Path, PurePosixPath
from typing import Callable

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
    for key in ("sent", "held", "arrivals"):
        data[key] = data.get(key) if isinstance(data.get(key), dict) else {}
    data["copied"] = list(data.get("copied") or [])
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


def participant_files(case: Path, workbook: Path, recordings: bool) -> list[tuple[Path, str]]:
    """A participant's files as a version carries them, each with its path from the participant's folder: the
    workbook, the PETs files and the progress file in Working, and the recordings when they go."""
    out = []
    try:
        out.append((workbook, workbook.relative_to(case).as_posix()))
    except ValueError:
        return []
    working = case / "Working"
    if working.is_dir():
        for p in sorted(working.iterdir()):
            if not p.is_file() or not p.name.startswith(workbook.stem):
                continue
            if p.name.endswith(pack_mod.PROGRESS_TAIL) or pack_mod.PETS_FILE.search(p.name):
                out.append((p, f"Working/{p.name}"))
    if recordings:
        for p in sorted(case.rglob("*")):
            rel = PurePosixPath(p.relative_to(case).as_posix())
            if p.is_file() and not p.is_symlink() and pack_mod.kind_in_case(rel) == "audio" \
                    and not any(part.startswith(".") for part in rel.parts):
                out.append((p, str(rel)))
    return out


def gets_files(root: Path) -> list[tuple[Path, str]]:
    return [(Path(root) / name, name) for name in pack_mod.GETS_FILES if (Path(root) / name).is_file()]


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
        return len(path.parts) == 2 and path.parts[0] == "Working" and bool(pack_mod.PETS_FILE.search(path.name))
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
        out.append({"what": p["folder"], "files": participant_files(case, Path(p["workbook"]).resolve(),
                                                                       data.get("recordings") is True),
                    "lock": case / "Working" / locks.NAME, "own": own})
    if gets_owner(roster) == me or every:
        files = gets_files(root)
        if files:
            out.append({"what": GETS, "files": files, "lock": locks.root_lock(root), "own": gets_owner(roster) == me})
    return out


def waiting(root: Path, data: dict, state: dict) -> list[dict]:
    """What of this member's has changed since it last went, each item of `mine` with its prints."""
    out = []
    for item in mine(root, data):
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


def send_one(root: Path, data: dict, dev: dict, way, item: dict, n: int) -> None:
    """One version, of a participant or of the GETs board, sealed and sent: its files read under their lock."""
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
    if len(packed) <= INLINE_MOST:
        body["zip"] = base64.b64encode(packed).decode("ascii")
    else:
        blob = os.urandom(16).hex()
        way.put_blob(team, blob, team_mod.aead_seal(key, packed, blob.encode("ascii")))
        body["blob"] = blob
    kind = "gets_version" if item["what"] == GETS else "version"
    way.send(team, team_mod.seal_envelope(team, epoch, key, dev, str(data.get("member") or ""),
                                          team_mod.next_seq(team), kind, body))


def push(root: Path, now: bool = False, dry_run: bool = False) -> dict:
    """What has waited a minute since its last save sent, or with `now` all that waits, and to a computer new on the
    roster everything this member works on. Answers `{"sent", "waiting", "offline"}`."""
    data = team_on(root)
    if data is None:
        return {"sent": [], "waiting": 0, "offline": False}
    roster = data["roster"]
    if alone(roster):
        return {"sent": [], "waiting": 0, "offline": False}
    dev = team_mod.device() or {}
    _gone, kept_back = flush(root, data)
    state = load_state(root)
    others = sorted(d["id"] for m in team_mod.roster_members(roster) for d in m.get("devices") or []
                    if isinstance(d, dict) and d.get("id") and d.get("id") != dev.get("id"))
    fresh = [d for d in others if d not in state["copied"]]
    if fresh:
        # the first full copy: everything of his goes again, at once, for the computer that has none of it, and
        # from the lead every participant, which a computer with none of that participant takes as its first copy
        lead = str(data.get("member") or "") == str(roster.get("lead") or "")
        items = [dict(item, print=prints(item["files"], {})) for item in mine(root, data, every=lead)]
        now = True
    else:
        items = waiting(root, data, state)
    due = [item for item in items if now or newest(item["files"]) <= time.time() - WAIT]
    if dry_run:
        return {"sent": [], "due": [item["what"] for item in due], "waiting": len(items), "offline": False,
                "dry_run": True}
    sent, offline = [], False
    try:
        way = team_mod.transport_for(data, dev)
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
            send_one(root, data, dev, way, item, n)
        except WorkbookError:
            continue
        except Exception:
            offline = True
            break
        if item.get("own", True):
            state["sent"][what] = {"n": n, "print": item["print"], "at": now_iso()}
        sent.append(what)
    if not offline and len(sent) == len(due):
        state["copied"] = others
    offline = offline or kept_back
    state["failed"] = now_iso() if offline else ""
    save_state(root, state)
    left = sum(1 for item in items if item.get("own", True) and item["what"] not in sent) + len(read_out(root))
    return {"sent": sent, "waiting": left, "offline": offline}


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


def flush(root: Path, data: dict | None = None) -> tuple[int, bool]:
    """What `post` kept, sent in order until the transport refuses one. Answers how many went and whether the
    transport could not be reached."""
    data = data or team_on(root)
    if data is None:
        return 0, False
    with locks.held(Path(root) / team_mod.LOG_DIR / OUT_LOCK):
        held = read_out(root)
        if not held:
            return 0, False
        team = str(data.get("team") or "")
        gone, offline = 0, False
        try:
            way = team_mod.transport_for(data, team_mod.device() or {})
            for item in held:
                way.send(team, base64.b64decode(item["sealed"]))
                gone += 1
        except Exception:
            offline = True
        write_out(root, held[gone:])
    return gone, offline


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
    _gone, offline = flush(root, data)
    return {"sent": not offline}


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


def version_bytes(data: dict, way, body: dict) -> bytes:
    if body.get("blob"):
        blob = str(body["blob"])
        if not re.fullmatch(r"[0-9a-f]{32}", blob):
            raise team_mod.TeamError(i18n.t("team.refused.tampered"), "tampered")
        team = str(data.get("team") or "")
        sealed = way.get_blob(team, blob)
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


def place(files: dict[str, bytes], base: Path) -> None:
    """Each file written beside its place under a new name, then renamed into place, and left out of the files the
    app noted as its own writes, so the screens see a change made elsewhere."""
    for rel, content in files.items():
        target = base / Path(*PurePosixPath(rel).parts)
        target.parent.mkdir(parents=True, exist_ok=True)
        tmp = target.with_name(f".{target.name}{INCOMING}")
        tmp.write_bytes(content)
        os.replace(tmp, target)
        wb_mod.WRITTEN.pop(str(target.resolve()), None)


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
    if not names or any((n_ not in pack_mod.GETS_FILES) if gets else not allowed_in_case(n_) for n_ in names):
        return "bad_file"
    files = unzipped(version_bytes(data, way, body), listed)
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
    try:
        way = team_mod.transport_for(data, dev)
        key = way_key(way)
        came = way.fetch(team, int(state["cursors"].get(key) or 0))
    except Exception:
        return {"applied": [], "offline": True}
    applied, taken = [], []
    for seq, sender, raw in came:
        state["cursors"][key] = max(int(state["cursors"].get(key) or 0), int(seq))
        if sender and sender == dev.get("id"):
            continue
        try:
            inner = team_mod.open_envelope(raw, data["roster"], team_mod.project_keys(team))
        except team_mod.TeamError as exc:
            team_mod.note_dropped(root, exc.code, str(sender or ""))
            continue
        if inner.get("device") == dev.get("id"):
            continue
        kind = inner.get("kind")
        if kind in EPOCH_NOW and epoch_of(raw) < int((data["roster"] or {}).get("epoch") or 1):
            team_mod.note_dropped(root, "old_epoch", str(sender or ""))
            continue
        try:
            if kind == "roster":
                body = inner.get("body") or {}
                if isinstance(body.get("n"), int) and body["n"] <= int((data["roster"] or {}).get("n") or 0):
                    # one this computer had already, in the welcome or by the way it came first
                    continue
                team_mod.take_roster(root, body)
                data = team_on(root) or data
                continue
            if kind in ("version", "gets_version"):
                came_of = take_version(root, data, way, inner, state)
                if came_of == "applied":
                    applied.append(GETS if kind == "gets_version" else str(inner["body"]["participant"]))
                elif came_of not in ("same", "older"):
                    team_mod.note_dropped(root, came_of, str(inner.get("device") or ""))
                data = team_on(root) or data
                continue
            if kind in TAKEN_HERE:
                took = TAKEN_HERE[kind](root, data, dev, inner)
                if took:
                    taken.append(took)
                data = team_on(root) or data
                continue
            handler = HANDLERS.get(str(kind))
            if handler is not None:
                handler(root, data, inner)
        except team_mod.TeamError as exc:
            team_mod.note_dropped(root, exc.code, str(inner.get("device") or ""))
        except WorkbookError as exc:
            team_mod.note_dropped(root, getattr(exc, "code", "") or "busy", str(inner.get("device") or ""))
        except Exception:
            team_mod.note_dropped(root, "could_not_read", str(inner.get("device") or ""))
    save_state(root, state)
    seen = getattr(way, "seen", None)
    if came and callable(seen):
        # the shared folder's mark of what this computer has read, so a message all have read is deleted
        try:
            seen(team, int(state["cursors"].get(key) or 0))
        except Exception:
            pass
    return {"applied": applied, "taken": taken, "offline": False}


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


def sync(root: Path, now: bool = False, dry_run: bool = False) -> dict:
    """One look: what came taken in, then what waits sent. One run at a time for the project."""
    if team_on(root) is None:
        return {"applied": [], "sent": [], "waiting": 0, "offline": False}
    if dry_run:
        return dict(push(root, now=now, dry_run=True), applied=[])
    with _RUN, run_lock(root):
        took = pull(root)
        gave = push(root, now=now)
    return {"applied": took["applied"], "taken": took.get("taken") or [], "sent": gave["sent"],
            "waiting": gave["waiting"], "offline": took["offline"] or gave["offline"]}


# ------------------------------------------------------------------ what the project's page and the agents read

def status(root: Path) -> dict | None:
    """Working together on the project's page: None while it is off. On, `tags` by participant label, each
    `{"owner": name}` for a participant another member works on and `{"review": name}` for one of this member's out
    for review, `arrivals` today, newest first, each `{"name", "participant", "at"}`, `waiting`, how many of his
    have changed since they went, and `offline`, whether the last try to send found no connection."""
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
    count = 0 if alone(roster) else len(waiting(root, data, state)) + held_out
    return {"tags": tags, "arrivals": arrivals, "waiting": count, "offline": bool(state.get("failed")) and count > 0}


# ------------------------------------------------------------------ the server's own looks

def looks(roots: Callable[[], list]) -> None:
    """The server's thread: every EVERY seconds, and when a transport says something came, a look at each project
    worked on together."""
    wake = threading.Event()
    stops: dict = {}
    while not _THREAD.get("stop"):
        for root in list(roots() or []):
            root = Path(root)
            if not root.is_dir() or team_on(root) is None:
                continue
            key = str(root)
            # tried again each look until a route listens, a relay project made since among the reasons (relaywire)
            if stops.get(key) is None:
                data = team_on(root)
                try:
                    way = team_mod.transport_for(data, team_mod.device() or {})
                    stops[key] = way.listen(str(data.get("team") or ""), wake.set)
                except Exception:
                    stops[key] = None
            try:
                sync(root)
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
    _THREAD["stop"] = True
    for root in list(roots() or []):
        try:
            if Path(root).is_dir() and team_on(Path(root)) is not None:
                with _RUN, run_lock(Path(root)):
                    push(Path(root), now=True)
        except Exception:
            pass
