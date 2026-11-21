"""Working together: the study's settings travel with the copy and keep in step (teamsettings, 20 November 2026,
Adam's ruling that day about 01:05 after teamflow's walk of the journey).

**What is the study's and what is each person's.** The study's settings are the project's name, its research
question, its method, its timepoints, its demographic categories, Rename's names for the participants (`names`) and
each participant's profile (picture, label, pen portrait and demographic values, `participants`). They travel. Every
other key of the project file is the person's own and is never sent nor written over: the reflexivity statement,
the interviewer's name, the archive tick, the privacy tick for agents, the order of the rows, the PET labels and
the timecodes of the exports, the guidance nudges and length, working in rounds, the participants table's layout,
and the file's own marks (`uid`, `copy_of`, `updated`). The list of names to replace is a file of its own and never
travels.

**How they travel.** A study's settings are kept as units, one for each key above and one for each field of each
participant's profile, so two people changing two participants' profiles never meet. The lead's computers send the
whole study, a `study` message with its count `n`, a minute after the project file last changed, at once to a
computer new on the list (the first full copy) and at once after a member's change came in. A member's computer
sends only what it changed since the study it last had from the lead, a `study_change` naming each unit's value
before and after. The lead's computer takes a member's unit when the lead's value is still the one the member
changed from, and keeps its own otherwise, then sends the whole study again: the lead's word wins on a conflict, as
the lead's list does. A computer taking the lead's study keeps a change of its own not sent yet where the lead
left that unit as it was, and otherwise takes the lead's. The first study taken keeps a unit of this computer's
where the lead holds none, so it goes to the lead as a change, the project file kept in `_Archive/` first. A
computer of the lead's other than the oldest on the list, with no study yet, asks for it and takes it before it
ever sends one, and a study numbered no higher than one sent or taken here is passed over. A member's change places
only the pictures of the units it set.

**Pictures** go inside the message that names them, only when their SHA-256 is not the one last sent, every one to
a computer new on the list. The pictures are small (a PNG of 256 pixels, a JPEG of 400 KB at most), and a message
above `team_sync.INLINE_MOST` goes as a sealed blob, as a version does. A picture another picture replaces is moved
to `pictures/_Archive/`, never deleted.

**Before this.** A computer on 0.9.32 or 0.9.33 drops these kinds as it drops any it does not know. A member that
has taken a version from the lead but never the study asks for it once a day (`study_ask`), and the lead's computer
answers with the whole study and every picture, so the settings start travelling once both ends have this version.

What this computer has sent and taken is kept in sync.json under `study`: `base`, the study as last sent or taken,
`sent` and `held`, the counts, `pics`, each picture's SHA-256 last sent or taken, `copied`, the computers given the
whole study, `force`, the whole study owed at once, `asked`, when this computer last asked, and `owed` and
`too_large`, the study held back by the route, which the status line says. A dry run sends
nothing and writes nothing (`team_sync.push` returns before this module is called)."""
from __future__ import annotations

import base64
import hashlib
import io
import json
import os
import re
import time
import zipfile
from datetime import datetime, timedelta, timezone
from pathlib import Path, PurePosixPath

import server as srv

KINDS = ("study", "study_change", "study_ask")
STATE_KEY = "study"
# the project file's keys that are the study's, beside each participant's profile
TOP = ("name", "research_question", "method", "timepoints", "demographics", "names")
PEOPLE = "participants"
SEP = "\t"
STUDY_FILE = "study.json"
PICTURES = "pictures/"
# a member asks for the study at most once in this many seconds
ASK_EVERY = 24 * 3600
NAME_MOST = 200
QUESTION_MOST = 10000
LABEL_MOST = 200
# the words a History line uses for each unit
SAID = {"name": "the name", "research_question": "the research question", "method": "the method",
        "timepoints": "the timepoints", "demographics": "the demographics", "names": "the participants' names",
        PEOPLE: "the participants' profiles"}


def _routes():
    import idiograph_routes as routes
    return routes


def _sync():
    import team_sync
    return team_sync


def words(text) -> str:
    return " ".join(str(text or "").split())


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


# ------------------------------------------------------------------ the study's units

def clean_unit(unit: str, value):
    """A unit's value as this computer keeps it, or None for none or one that will not read."""
    routes = _routes()
    if value is None:
        return None
    if unit == "name":
        out = words(value)[:NAME_MOST] if isinstance(value, str) else ""
        return out or None
    if unit == "research_question":
        out = str(value).strip() if isinstance(value, str) else ""
        return out[:QUESTION_MOST] or None
    if unit == "method":
        return value if isinstance(value, str) and value in routes.KINDS else None
    if unit == "timepoints":
        if not isinstance(value, list) or not value:
            return None
        try:
            tps = routes.clean_timepoints(value)
        except Exception:  # noqa: BLE001 - one that will not read is none
            return None
        return [{"label": tp["label"], "description": tp["description"]} for tp in tps]
    if unit == "demographics":
        import demographics as demo_mod
        if not isinstance(value, list):
            return None
        cats = [c for c in (demo_mod.cat_kept(raw) for raw in value) if c is not None][:demo_mod.CATS_MAX]
        return cats or None
    if unit == "names":
        if not isinstance(value, dict):
            return None
        out = {str(k): str(v).strip() for k, v in value.items() if isinstance(k, str) and k.strip()
               and isinstance(v, str) and routes.ONE_WORD.match(str(v).strip())}
        return out or None
    parts = unit.split(SEP)
    if len(parts) == 3 and parts[0] == PEOPLE:
        import participants as people_mod
        label, field = parts[1], parts[2]
        if not label.strip() or len(label) > LABEL_MOST or field not in people_mod.FIELDS:
            return None
        return people_mod.one({field: value}).get(field)
    return None


def unit_ok(unit) -> bool:
    if not isinstance(unit, str):
        return False
    if unit in TOP:
        return True
    parts = unit.split(SEP)
    import participants as people_mod
    return len(parts) == 3 and parts[0] == PEOPLE and bool(parts[1].strip()) and parts[2] in people_mod.FIELDS


def project_read(root: Path) -> dict | None:
    """The project file as it sits, None when it is not there or will not read (an iCloud file being fetched), so
    nothing is sent from a file not read and nothing is written over it."""
    try:
        data = json.loads((Path(root) / srv.PROJECT_FILE).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    return data if isinstance(data, dict) else None


def units_of(root: Path, project: dict) -> dict:
    """The study's settings in a project file, as units: the name as the project shows it, the method as it reads,
    and each other key and each field of each participant's profile that holds anything."""
    import participants as people_mod
    routes = _routes()
    out = {"name": clean_unit("name", project.get("name")) or srv.display_case(Path(root).name),
           "method": routes.method_of(project)}
    for key in TOP:
        if key in ("name", "method"):
            continue
        value = clean_unit(key, project.get(key))
        if value is not None:
            out[key] = value
    for label, held in people_mod.own_of(project).items():
        for field in people_mod.FIELDS:
            unit = SEP.join((PEOPLE, label, field))
            value = clean_unit(unit, held.get(field))
            if value is not None:
                out[unit] = value
    return out


def units_given(raw) -> dict:
    """Units as a message carries them, each checked, those that will not read left out."""
    out = {}
    for unit, value in (raw.items() if isinstance(raw, dict) else ()):
        if unit_ok(unit):
            kept = clean_unit(unit, value)
            if kept is not None:
                out[unit] = kept
    return out


def merged(base: dict, cur: dict, new: dict) -> dict:
    """The lead's study taken in: a unit changed here and not sent yet keeps its value where the lead left it as it
    was, and every other unit takes the lead's."""
    out = {}
    for unit in set(base) | set(cur) | set(new):
        b, c, n = base.get(unit), cur.get(unit), new.get(unit)
        value = c if c != b and n == b else n
        if value is not None:
            out[unit] = value
    return out


def holds_work(root: Path) -> bool:
    """Whether the project holds a participant, anything of any kind `list_cases` gives. A project that will not be
    read counts as one that does, so nothing is changed in it."""
    try:
        return bool(_routes().list_cases(Path(root)))
    except Exception:  # noqa: BLE001 - not read just now: kept as it is
        return True


def kept_as_is(root: Path, cur: dict, result: dict) -> dict:
    """The result of a member's change to the lead's study, with the method and the timepoints of a project with
    work in it put back as the project holds them: the method is fixed when a project is made, a thematic analysis
    or IPA project has no timepoints, and a longitudinal one keeps a list not shorter than its own (lowsW). A
    project with no participant takes the change whole. The lead's own study, taken by a member, is not held to
    this: the team's method is the lead's word."""
    if not holds_work(root):
        return result
    out = dict(result)
    if out.get("method") != cur.get("method"):
        out["method"] = cur.get("method")
    held = cur.get("timepoints")
    wanted = out.get("timepoints")
    if cur.get("method") != "lipa" or not isinstance(wanted, list) or not isinstance(held, list) \
            or len(wanted) < len(held):
        if held is None:
            out.pop("timepoints", None)
        else:
            out["timepoints"] = held
    return {u: v for u, v in out.items() if v is not None}


def written_over(root: Path, project: dict, cur: dict, result: dict) -> dict:
    """The project file with the units that changed set or taken off, every other key as it was."""
    data = dict(project)
    changed = [u for u in set(cur) | set(result) if cur.get(u) != result.get(u)]
    people = {k: dict(v) for k, v in (project.get(PEOPLE) or {}).items()
              if isinstance(k, str) and isinstance(v, dict)} if isinstance(project.get(PEOPLE), dict) else {}
    touched = False
    for unit in changed:
        value = result.get(unit)
        if unit in TOP:
            if value is None:
                data.pop(unit, None)
            else:
                data[unit] = value
            continue
        _p, label, field = unit.split(SEP)
        entry = people.setdefault(label, {})
        if value is None:
            entry.pop(field, None)
        else:
            entry[field] = value
        if field == "picture":
            entry.pop("from_traj", None)
        touched = True
    if touched:
        import participants as people_mod
        people = {k: v for k, v in people.items() if any(v.get(f) for f in people_mod.FIELDS)}
        if people:
            data[PEOPLE] = people
        else:
            data.pop(PEOPLE, None)
    data["updated"] = datetime.now().astimezone().isoformat(timespec="seconds")
    return data


def changed_said(cur: dict, result: dict) -> list[str]:
    """The study's settings that changed, in plain words, each once."""
    moved = {unit.split(SEP)[0] for unit in set(cur) | set(result) if cur.get(unit) != result.get(unit)}
    return [said for key, said in SAID.items() if key in moved]


def joined_said(items: list[str]) -> str:
    return items[0] if len(items) == 1 else ", ".join(items[:-1]) + " and " + items[-1]


# ------------------------------------------------------------------ pictures

def pictures_named(units: dict) -> set:
    """The pictures the study names that are files of the project's own, not one of the app's drawn sets."""
    return {v for u, v in units.items() if u.endswith(SEP + "picture") and isinstance(v, str)
            and not v.startswith("set:")}


def picture_ok(name: str, raw: bytes) -> bool:
    """A picture that came, kept only when its name is one a picture may have and its bytes are what its kind says,
    within the size the app keeps, an SVG with no script."""
    import trajectories as traj_mod
    if traj_mod.picture_kept(name) != name or name.startswith("set:"):
        return False
    ext = name.rsplit(".", 1)[-1].lower()
    if ext == "png":
        # read whole, as the app keeps one: a PNG it can read, no larger than the app's picture size
        if raw[:8] != b"\x89PNG\r\n\x1a\n" or len(raw) > traj_mod.PICTURE_MAX:
            return False
        try:
            w, h, _rgba = traj_mod.png_read(raw)
        except Exception:  # noqa: BLE001 - one that will not read is refused
            return False
        return 0 < w <= traj_mod.PICTURE_SIZE and 0 < h <= traj_mod.PICTURE_SIZE
    if ext == "jpg":
        return raw[:3] == b"\xff\xd8\xff" and len(raw) <= traj_mod.KEPT_MAX["jpg"]
    if ext == "svg":
        text = raw.decode("utf-8", "ignore").lower()
        return "<svg" in text[:600] and "<script" not in text and len(raw) <= traj_mod.KEPT_MAX["svg"]
    return False


def pictures_set(cur: dict, result: dict) -> set:
    """The pictures of the units a change set, those whose picture is not the one held before it, less any file
    another unit of the lead's names already, so a change naming another participant's picture never replaces it."""
    changed = {u for u, v in result.items() if u.endswith(SEP + "picture") and cur.get(u) != v}
    used = pictures_named({u: v for u, v in cur.items() if u not in changed})
    return pictures_named({u: result[u] for u in changed}) - used


def picture_files(root: Path, names: set) -> dict[str, bytes]:
    import participants as people_mod
    out = {}
    for name in sorted(names):
        path = people_mod.pictures_of(root) / name
        try:
            if path.is_file() and not path.is_symlink():
                out[name] = path.read_bytes()
        except OSError:
            continue
    return out


def place_pictures(root: Path, pictures: dict[str, bytes], wanted: set) -> list[str]:
    """The pictures that came and the study now names written into the project's pictures folder, one there with
    other bytes moved to its `_Archive` first. Answers the names written."""
    import participants as people_mod
    import trajectories as traj_mod
    folder = people_mod.pictures_of(root)
    out = []
    for name, raw in sorted(pictures.items()):
        if name not in wanted or not picture_ok(name, raw):
            continue
        path = folder / name
        try:
            if path.is_file() and hashlib.sha256(path.read_bytes()).digest() == hashlib.sha256(raw).digest():
                continue
        except OSError:
            pass
        traj_mod.picture_files(root, {name: raw}, now_iso(), folder=folder)
        out.append(name)
    return out


# ------------------------------------------------------------------ what this computer keeps

def kept(state: dict) -> dict:
    st = state.get(STATE_KEY)
    st = st if isinstance(st, dict) else {}
    st["pics"] = st.get("pics") if isinstance(st.get("pics"), dict) else {}
    st["copied"] = list(st.get("copied") or []) if isinstance(st.get("copied"), list) else []
    if not isinstance(st.get("base"), dict):
        st["base"] = None
    state[STATE_KEY] = st
    return st


ARCHIVE_LABEL = "pre-study"


def archive_copy(root: Path) -> None:
    """The project file copied to `_Archive/` beside it, `idiograph-project (pre-study <date-time>).json`, never over
    one there, before the first study taken writes over it."""
    import shutil
    path = Path(root) / srv.PROJECT_FILE
    if not path.is_file():
        return
    folder = Path(root) / "_Archive"
    folder.mkdir(parents=True, exist_ok=True)
    stem = path.name[:-len(".json")] if path.name.endswith(".json") else path.stem
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    target, n = folder / f"{stem} ({ARCHIVE_LABEL} {stamp}).json", 2
    while target.exists():
        target, n = folder / f"{stem} ({ARCHIVE_LABEL} {stamp}-{n}).json", n + 1
    shutil.copy2(path, target)


def first_lead_device(data: dict) -> str:
    """The lead's oldest computer on the list, the one that sends the whole study when no computer of the lead's
    has sent or taken one yet."""
    import team as team_mod
    ids = list(team_mod.lead_devices(data.get("roster") or {}))
    return ids[0] if ids else ""


def owed(state: dict) -> bool:
    """Whether the study's settings wait to go, held back by the route, for the status line's count."""
    st = state.get(STATE_KEY)
    return bool(isinstance(st, dict) and st.get("owed"))


def too_large(state: dict) -> bool:
    """Whether the study's settings with their pictures were too large for the route when last tried."""
    st = state.get(STATE_KEY)
    return bool(isinstance(st, dict) and st.get("too_large"))


def is_lead(data: dict, dev: dict) -> bool:
    import team as team_mod
    roster = data.get("roster") or {}
    return str(data.get("member") or "") == str(roster.get("lead") or "") \
        and dev.get("id") in team_mod.lead_devices(roster)


# ------------------------------------------------------------------ sending

def packed(files: dict[str, bytes]) -> tuple[bytes, list[dict]]:
    buf = io.BytesIO()
    listed = []
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as z:
        for name, raw in files.items():
            z.writestr(name, raw)
            listed.append({"name": name, "sha": hashlib.sha256(raw).hexdigest(), "size": len(raw)})
    return buf.getvalue(), listed


def send(data: dict, dev: dict, way, kind: str, body: dict, files: dict[str, bytes], files_held: bool) -> None:
    """One message of this module's, its files zipped inside it, or sealed as a blob of their own above what a
    message holds, as a version's are (`team_sync.send_one`)."""
    import i18n
    import team as team_mod
    ts = _sync()
    team = str(data.get("team") or "")
    epoch = int((data.get("roster") or {}).get("epoch") or 1)
    key = team_mod.project_key(team, epoch)
    if key is None:
        raise team_mod.TeamError(i18n.t("team.refused.no_key"), "no_key")
    zipped, listed = packed(files)
    body = dict(body, files=listed)
    blob = None
    if len(zipped) <= ts.INLINE_MOST:
        body["zip"] = base64.b64encode(zipped).decode("ascii")
    else:
        if files_held:
            raise ts.FilesHeld()
        if len(zipped) + 40 > ts.most_file(way):
            raise ts.TooLarge()
        blob = os.urandom(16).hex()
        try:
            way.put_blob(team, blob, team_mod.aead_seal(key, zipped, blob.encode("ascii")))
        except Exception as exc:  # noqa: BLE001 - marked, then raised as it came
            raise ts.on_file(exc)
        body["blob"] = blob
    ts.sent(way, team, team_mod.seal_envelope(team, epoch, key, dev, str(data.get("member") or ""),
                                              team_mod.next_seq(team), kind, body), blob)


def push(root: Path, data: dict, dev: dict, way, state: dict, others: list, now: bool = False,
         files_held: bool = False) -> dict:
    """The study's settings sent when they are due: from the lead's computer the whole study, from a member's what
    he changed, or a member's ask. Answers `{"sent": kind}`, or the refusal as `team_sync.push` keeps it,
    `{"held": word}`, `{"files_held": word}` or `{"offline": True}`, or `{}` for nothing to send."""
    ts = _sync()
    project = project_read(root)
    if project is None:
        return {}
    st = kept(state)
    cur = units_of(root, project)
    file = Path(root) / srv.PROJECT_FILE
    quiet = now or ts.newest([(file, srv.PROJECT_FILE)]) <= time.time() - ts.WAIT
    base = st["base"]
    lead_here = is_lead(data, dev)
    if lead_here and base is None and not st.get("held") and not st.get("sent") \
            and dev.get("id") != first_lead_device(data):
        # another computer of the lead's with no study yet (one joined from Home holds only the name and method)
        # asks the lead's other computers for theirs and takes it before it ever sends, so its empty study never
        # goes to the others as the lead's word (the review's finding 1)
        lead_here = False
    if lead_here:
        fresh = [d for d in others if d not in st["copied"]]
        force = st.get("force")
        if not (fresh or force or base is None or cur != base):
            return {}
        if not (fresh or force or quiet):
            return {}
        whole = bool(fresh) or force == "all"
        pics = picture_files(root, pictures_named(cur))
        shas = {name: hashlib.sha256(raw).hexdigest() for name, raw in pics.items()}
        going = {f"{PICTURES}{name}": raw for name, raw in pics.items() if whole or st["pics"].get(name) != shas[name]}
        n = max(int(st.get("sent") or 0), int(st.get("held") or 0)) + 1
        files = dict({STUDY_FILE: json.dumps(cur, ensure_ascii=False, sort_keys=True).encode("utf-8")}, **going)
        kind, body = "study", {"n": n}
    elif base is None:
        # nothing of the lead's study yet: asked for once a day, and only once a version of the lead's has come, so
        # a member joining now waits for the first copy (a lead on 0.9.32 or 0.9.33 drops the ask). The lead's other
        # computer asks at once
        asked = str(st.get("asked") or "")
        try:
            recent = datetime.now(timezone.utc) - datetime.fromisoformat(asked) < timedelta(seconds=ASK_EVERY)
        except ValueError:
            recent = False
        if (not state.get("held") and not is_lead(data, dev)) or recent:
            return {}
        kind, body, files = "study_ask", {}, {}
    else:
        changes = {u: [base.get(u), cur.get(u)] for u in sorted(set(base) | set(cur)) if base.get(u) != cur.get(u)}
        if not changes or not quiet:
            return {}
        named = pictures_named({u: cur[u] for u in changes if u in cur})
        files = {f"{PICTURES}{name}": raw for name, raw in picture_files(root, named).items()}
        kind, body = "study_change", {"base": int(st.get("held") or 0), "changes": changes}
    try:
        send(data, dev, way, kind, body, files, files_held)
    except ts.FilesHeld:
        # the route holds this project's files: the study waits with them, and the status line counts it
        st["owed"] = True
        return {"files_held": files_held if isinstance(files_held, str) and files_held else "files"}
    except ts.TooLarge:
        # too large for the route: said in the status line, and tried again at the next look
        st.update(owed=True, too_large=True)
        state["too_large_most"] = ts.most_file(way)
        return {}
    except Exception as exc:  # noqa: BLE001 - the route's refusal, or no connection
        word = ts.refused_word(exc)
        if word and word not in ("gone", "too_large") and getattr(exc, "on_file", False):
            state["files_hold"] = ts.hold_of(word, exc, data)
            return {"files_held": word}
        if word and word != "too_large":
            state["hold"] = ts.hold_of(word, exc, data)
            return {"held": word}
        return {"offline": True}
    st.pop("owed", None)
    st.pop("too_large", None)
    if kind == "study":
        st.update(base=cur, sent=body["n"], force=False)
        st["pics"].update(shas)
        if fresh:
            st["copied"] = sorted(set(st["copied"]) | set(others))
    elif kind == "study_ask":
        st["asked"] = now_iso()
    else:
        st["base"] = cur
    return {"sent": kind}


# ------------------------------------------------------------------ taking in

def opened(data: dict, way, inner: dict, body: dict) -> tuple[dict | None, dict[str, bytes]]:
    """A message's study and pictures, each file checked against its SHA-256."""
    import i18n
    import team as team_mod
    ts = _sync()
    listed = body.get("files") if isinstance(body.get("files"), list) else []
    names = [str((f or {}).get("name") or "") for f in listed]
    for name in names:
        rel = PurePosixPath(name)
        if name != STUDY_FILE and not (len(rel.parts) == 2 and name.startswith(PICTURES)
                                       and not rel.parts[1].startswith(".")):
            raise team_mod.TeamError(i18n.t("team.refused.tampered"), "bad_file")
    files = ts.unzipped(ts.version_bytes(data, way, body, inner), listed) if listed else {}
    study = None
    if STUDY_FILE in files:
        try:
            study = units_given(json.loads(files[STUDY_FILE].decode("utf-8")))
        except (ValueError, UnicodeDecodeError):
            raise team_mod.TeamError(i18n.t("team.refused.tampered"), "tampered") from None
    pictures = {name[len(PICTURES):]: raw for name, raw in files.items() if name.startswith(PICTURES)}
    return study, pictures


def take(root: Path, data: dict, dev: dict, way, inner: dict, state: dict) -> str:
    """One message of this module's taken in. Answers why one was dropped, or "" for taken or passed over."""
    import project_history as hist_mod
    import team as team_mod
    ts = _sync()
    roster = data.get("roster") or {}
    lead = str(roster.get("lead") or "")
    sender = str(inner.get("member") or "")
    kind = inner.get("kind")
    body = inner.get("body") if isinstance(inner.get("body"), dict) else {}
    st = kept(state)
    if kind == "study_ask":
        if is_lead(data, dev):
            st["force"] = "all"
        return ""
    if kind == "study_change":
        # a member's change, taken by the lead's computers alone. The lead's other computer sends whole studies
        if not is_lead(data, dev) or sender == lead or team_mod.member_of(roster, sender) is None:
            return ""
        changes = body.get("changes") if isinstance(body.get("changes"), dict) else {}
        _study, pictures = opened(data, way, inner, body)
        with _routes().writing(root=root):
            project = project_read(root)
            if project is None:
                raise ts.Later("busy")
            cur = units_of(root, project)
            result = dict(cur)
            for unit, pair in changes.items():
                if not unit_ok(unit) or not isinstance(pair, list) or len(pair) != 2:
                    continue
                old, new = clean_unit(unit, pair[0]), clean_unit(unit, pair[1])
                if pair[1] is not None and new is None:
                    continue
                if cur.get(unit) == old and old != new:
                    if new is None:
                        result.pop(unit, None)
                    else:
                        result[unit] = new
            if not result.get("name"):
                result["name"] = cur.get("name")
            result = kept_as_is(root, cur, result)
            said = changed_said(cur, result)
            if said:
                # only the pictures of the units this change set, so a member's change never replaces another
                place_pictures(root, pictures, pictures_set(cur, result))
                srv.save_json(Path(root) / srv.PROJECT_FILE, written_over(root, project, cur, result))
                who = ts.member_name(roster, sender) or sender
                hist_mod.record(root, "team take", [f"{who}'s change to the study's settings came in: "
                                                    f"{joined_said(said)}."], {"by": "app"})
        # the whole study goes again, so a change kept back here reaches the member as the lead has it
        st["force"] = st.get("force") or True
        return ""
    if kind != "study":
        return ""
    if sender != lead:
        return "not_owner"
    n = body.get("n")
    if not isinstance(n, int) or isinstance(n, bool) or n < 1:
        return "tampered"
    # a study numbered no higher than one this computer has sent or taken is passed over, so the lead's two
    # computers never take back an older or an equal study of the other's
    if n <= max(int(st.get("held") or 0), int(st.get("sent") or 0)):
        return ""
    new, pictures = opened(data, way, inner, body)
    if new is None:
        return "tampered"
    with _routes().writing(root=root):
        project = project_read(root)
        if project is None and (Path(root) / srv.PROJECT_FILE).exists():
            raise ts.Later("busy")
        project = project or {}
        cur = units_of(root, project)
        # the first study taken keeps a unit of this computer's where the lead holds none (a team from 0.9.33, or a
        # join from a project with work in it), so it goes to the lead as a change, and takes the lead's for every
        # other, the project file kept in _Archive first; after it a change here not sent yet is kept where the
        # lead left its unit as it was
        first = st["base"] is None
        result = merged({} if first else st["base"], cur, new)
        if not result.get("name"):
            result["name"] = cur.get("name")
        said = changed_said(cur, result)
        if said and first:
            archive_copy(root)
        written = place_pictures(root, pictures, pictures_named(result))
        if said:
            srv.save_json(Path(root) / srv.PROJECT_FILE, written_over(root, project, cur, result))
            who = ts.member_name(roster, sender) or sender
            hist_mod.record(root, "team take", [f"{who}'s settings for the study came in: {joined_said(said)}."],
                            {"by": "app"})
    st["base"], st["held"] = new, n
    for name in written:
        st["pics"][name] = hashlib.sha256(pictures[name]).hexdigest()
    return ""

