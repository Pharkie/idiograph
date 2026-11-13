"""A project sent to someone else's Idiograph as one file, and opened there as a copy (Adam's ruling of
20 October 2026, topic 10, from a tester's wish for a student and a supervisor).

Send writes `<Project name>.idiograph`, a zip of the whole project folder as it is, every workbook,
the project file, the boards, the GETs, Source, the recordings and History, with a list of what it
holds, and changes nothing in the project. Open a sent project unpacks it into a new folder beside
the others in the folder he chooses, never over one: a folder already there gives the copy the name
with "copy" after it. A returned board taken back in, turn-taking and live co-editing are for later
or left out. The server, the command line and the MCP server all call here.

A chosen send (23 October, Adam: a tester makes PETs for one of his participants, blinded, to compare
with his own) takes some participants and leaves kinds out (`choose`): the participants' workbooks,
their Source and progress files always go, the PETs (boards and their history, LPETs, PET drafts, PET
tables in Word or PDF), the GETs (the GETs, LGETs and Trajectories files, GETs tables at the root) and
the recordings each go or stay by choice, recordings staying unless asked for. `_Archive` copies never
go in a chosen send. Each participant's folder in the file is named by its label alone, never with a
second part its folder on disk carries, and the project file loses `names`, Rename's kept names, which
the renamed folders make moot. The file's format is the same, so an Idiograph from before opens it.
Since Adam's design E of 23 October the PETs and the recordings can be chosen participant by
participant, a whole send can leave the recordings alone out (`whole_less_audio`), and `inventory`
answers what Share a copy's card draws: each participant's PETs and recordings, and their weight.
A send of the current board alone (`current_boards`, Adam, 23 October) takes any plan and sends each
board file with the board it is going with, that board's drafts and tables only, and no History.

The file is a zip, `idiograph-sent.json` at its head and every file of the project under `project/`.
`format` is the shape this Idiograph writes, and a file of a higher format, from a newer Idiograph that
may hold what this one cannot read, is refused in plain words. Standard library and `locks` only.

A copy coming back (26 October, Adam's ruling of 23 October: "conceptually it's the same project"). The
list at the head carries the project's own id, `uid`, which the project file takes at its first send,
`statements`, a print of every statement sent, by participant and key, and, from a copy, `copy_of`, the
project it was opened from. A copy opened keeps them in its own project file, so a file sent back from
it names the project it came from and the statements as they read when they were sent. Since 8 November
`boards` is the places print of each board sent, by participant, so a board sent back untouched is told
as the sender's own. `sent_boards`
reads a sent file's boards for `idiograph_routes.boards_in`, which adds them to that project."""
from __future__ import annotations

import hashlib
import json
import os
import re
import shutil
import uuid
import zipfile
from datetime import datetime
from pathlib import Path, PurePosixPath

import formats
import i18n
from locks import NAME as LOCK_NAME

SUFFIX = ".idiograph"
FORMAT = 1
MANIFEST = "idiograph-sent.json"
TOP = "project/"
KIND = "idiograph-project"
# what is never sent: the file lock a writer holds while it writes, the Mac's folder settings, the
# owner file Excel keeps beside a workbook it has open, the holds file of before approvals were removed with its
# lock, and the record of agents' changes and their restore points (agent_changes.py), none of them the project's
# own, and the project's own History (project_history.py), whose
# lines name participants a partial send leaves out and whose requests are his to an agent, and Working together's
# team file and its folder (team.py's log, review.py's drafts and threads), which are this install's place in a team, never a copy's
LEFT_OUT = (LOCK_NAME, ".DS_Store", "idiograph-holds.json", ".idiograph-holds.lock", "idiograph-history.json",
            "idiograph-agent-changes.jsonl", ".idiograph-restore",
            "team.json", ".idiograph-team",
            # the project's list of real names (namesui, 8 November 2026, `names.FILE`), never in a copy he shares
            "idiograph-names.json")
# the copies kept in a participant's _Archive before Review and replace put the pseudonyms in, which hold the real
# names and so never go in a send either (`idiograph_routes.PSEUDO_ARCHIVE`)
REAL_NAMES_KEPT = "(pre-names "
# a name neither a file nor a folder may carry on a Mac or on Windows
NOT_IN_NAME = re.compile(r'[\\/:*?"<>|\x00-\x1f]')


class PackError(Exception):
    """A send or an open that cannot go ahead, in one plain line, with nothing written."""


def sent_name(name: str) -> str:
    """The file's name, the project's name with `.idiograph` after it, any character a file's name
    may not hold taken out."""
    clean = " ".join(NOT_IN_NAME.sub(" ", str(name or "")).split()).strip(". ") or "Project"
    return clean + SUFFIX


def left_out(rel: PurePosixPath) -> bool:
    return any(part in LEFT_OUT or part.startswith("~$") or REAL_NAMES_KEPT in part for part in rel.parts)


def project_files(root: Path, skip: Path | None = None) -> list[tuple[Path, str]]:
    """Every file of the project, each with its path from the root, in a steady order. A link is
    never followed, and what `LEFT_OUT` names is not the project's. `skip` is the file being written."""
    root = Path(root)
    out = []
    for folder, dirs, names in os.walk(root, followlinks=False):
        dirs.sort()
        here = Path(folder)
        dirs[:] = [d for d in dirs if not (here / d).is_symlink()]
        for name in sorted(names):
            path = here / name
            if path.is_symlink() or not path.is_file():
                continue
            if skip is not None and path.resolve() == skip:
                continue
            rel = PurePosixPath(path.relative_to(root).as_posix())
            if left_out(rel):
                continue
            out.append((path, str(rel)))
    return out


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with open(path, "rb") as fh:
        for block in iter(lambda: fh.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def size_said(n: int) -> str:
    """A size as a line says it, 820 KB or 3.2 MB."""
    if n < 1000 * 1000:
        return f"{max(1, round(n / 1000)) if n else 0} KB"
    if n < 1000 * 1000 * 1000:
        return f"{n / 1e6:.1f} MB"
    return f"{n / 1e9:.1f} GB"


def plan_send(root: Path, name: str) -> dict:
    """What Send would write, and nothing written: the file's name, its files and their weight."""
    files = project_files(root)
    total = sum(p.stat().st_size for p, _ in files)
    return {"name": sent_name(name), "files": len(files), "bytes": total, "size": size_said(total)}


def send(root: Path, name: str, dest: Path, version: str = "", chosen: dict | None = None,
         origin: dict | None = None) -> dict:
    """The project at `root` written to `dest` as one file, through a file beside it renamed into
    place, so a failure leaves nothing half written. Nothing in the project is changed. `chosen` is
    what `choose` answered for a chosen send, its files under their names in the file, the project
    file among them as bytes, and None sends every file as it is. `origin` is what the list at the
    head says of where the file comes from (`ORIGIN_KEYS`), the project's id among it."""
    root, dest = Path(root), Path(dest)
    if not root.is_dir():
        raise PackError(i18n.t("server.project_s_folder_nothing_sent"))
    tmp = dest.with_name(f".{dest.name}.sending")
    if chosen is None:
        files = project_files(root, skip=dest.resolve())
    else:
        skip = dest.resolve()
        files = [(src, rel) for src, rel in chosen["files"] if isinstance(src, bytes) or src.resolve() != skip]
    listed = []
    for src, rel in files:
        if isinstance(src, bytes):
            listed.append({"path": rel, "bytes": len(src), "sha256": hashlib.sha256(src).hexdigest()})
        else:
            listed.append({"path": rel, "bytes": src.stat().st_size, "sha256": sha256(src)})
    head = {"kind": KIND, "format": FORMAT, "name": str(name or ""), "folder": root.name,
            "sent": datetime.now().astimezone().isoformat(timespec="seconds"), "version": str(version or ""),
            "files": listed}
    for key in ORIGIN_KEYS:
        if (origin or {}).get(key):
            head[key] = origin[key]
    if chosen is not None:
        # what was chosen, so a reader knows the copy is not the whole project. An Idiograph from
        # before reads past a key it does not know
        head["chosen"] = {"participants": list(chosen["participants"]), "left_out": list(chosen["kinds_out"])}
        if chosen.get("per"):
            # the PETs and recordings chosen participant by participant
            head["chosen"]["each"] = {k: list(v) for k, v in chosen["each"].items()}
        if chosen.get("whole"):
            head["chosen"]["whole"] = True
        if chosen.get("board_choice") == "current":
            # each board file with the board it was going with alone
            head["chosen"]["boards"] = "current"
    try:
        with zipfile.ZipFile(tmp, "w", compression=zipfile.ZIP_DEFLATED, allowZip64=True) as zf:
            zf.writestr(MANIFEST, json.dumps(head, ensure_ascii=False, indent=1))
            for src, rel in files:
                if isinstance(src, bytes):
                    zf.writestr(TOP + rel, src)
                else:
                    zf.write(src, TOP + rel)
        os.replace(tmp, dest)
    except BaseException:
        try:
            tmp.unlink()
        except OSError:
            pass
        raise
    total = sum(f["bytes"] for f in listed)
    return {"sent": True, "file": str(dest), "name": dest.name, "files": len(listed), "bytes": total,
            "size": size_said(total)}


# ------------------------------------------------------------ a chosen send

# The kinds a chosen send takes or leaves, each by its word. The workbooks and the progress files always
# go. Recordings, working notes and Source stay out of a chosen send unless asked for (OPT_IN).
KINDS = ("pets", "gets", "audio", "notes", "source")
OPT_IN = ("audio", "notes", "source")
# the kinds a chosen send's answer gives for each participant, the PETs and recordings chosen one by one
EACH_KINDS = ("pets", "audio", "notes", "source")
KIND_WORDS = {"pets": "pets", "pet": "pets", "gets": "gets", "get": "gets", "audio": "audio",
              "recordings": "audio", "recording": "audio", "notes": "notes", "note": "notes",
              "source": "source", "sources": "source"}
# what each kind, and each other reason a file stays out, is called in a line
LEFT_SAID = {"pets": "PETs (boards and their history, LPETs, PET drafts, PET tables)",
             "gets": "GETs (the GETs, LGETs and Trajectories files and their tables)",
             "audio": "recordings", "notes": "working notes (any file of a participant's not Idiograph's own)",
             "source": "Source (raw sources and transcription exports)", "archive": "_Archive copies",
             "participants": "participants not chosen", "other": "files of no participant chosen",
             "history": "History (the progress file goes without its edits, trims, assignments and imports, "
                        "its statements' completion kept)",
             "boards": "PET drafts and tables of other boards, or of no board that can be told"}
LEFT_ORDER = ("pets", "gets", "audio", "notes", "source", "boards", "history", "archive", "participants", "other")
# what a progress file keeps in a send that leaves the PETs out: what the statements screen works by, no
# History, whose records carry requests, notes and tool names that may name a board or a PET (23 October)
PROGRESS_KEEP = ("version", "rows", "rounds", "days", "last", "last_commit_at", "last_commit_round", "complete",
                 "complete_timepoints", "timepoints", "flags")


def progress_without_history(path: Path) -> bytes:
    """A progress file's JSON with only `PROGRESS_KEEP`'s keys, every other key, the History among them,
    left out, so the copy's History starts fresh. A file that cannot be read goes as an empty one."""
    try:
        data = json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        data = {}
    data = data if isinstance(data, dict) else {}
    kept = {k: data[k] for k in PROGRESS_KEEP if k in data}
    return (json.dumps(kept, ensure_ascii=False, indent=2) + "\n").encode("utf-8")
AUDIO_EXT = {".m4a", ".m4b", ".mp3", ".wav", ".aac", ".aif", ".aiff", ".flac", ".ogg", ".opus", ".wma",
             ".mp4", ".m4v", ".mov", ".webm", ".avi", ".mkv"}
GETS_FILES = ("idiograph-gets.json", "idiograph-lgets.json", "idiograph-trajectories.json")
PETS_FILE = re.compile(r"\.(?:themes(?:-t\d+)?|lpets)\.json$", re.IGNORECASE)
PET_DRAFT = re.compile(r" - PET draft \(.*\)\.md$", re.IGNORECASE)
PROGRESS_TAIL = ".progress.json"
# the app's own backups beside a workbook, `(pre-trim)` or `(complete 30Sep26)` (routes.BACKUP_STEM)
BACKUP_STEM = re.compile(r"\((?:pre-|complete)[^()]*\)\s*$", re.IGNORECASE)
TABLES = {".docx", ".doc", ".pdf"}
ARCHIVE = "_Archive"


def kinds_of(words) -> set:
    """The kinds a list names, each word one of `KIND_WORDS` or several joined by commas, refused in
    one line for a word that names none."""
    out = set()
    for word in words or ():
        for part in str(word).split(","):
            part = part.strip().lower()
            if not part:
                continue
            if part not in KIND_WORDS:
                raise PackError(i18n.t("server.kind_send_takes_leaves_kinds", part=part))
            out.add(KIND_WORDS[part])
    return out


def kind_in_case(rel: PurePosixPath) -> str | None:
    """What a file inside a participant's folder is in a chosen send, by its path from that folder:
    None for the workbook and the progress file, which always go, `pets` for a themes or LPETs file,
    a PET draft or a PET table, `audio`, `source` for anything in Source, `archive`, and `notes` for
    every other file, Idiograph's or not, in Working or elsewhere in the folder (23 October, a blinding
    leak: a grouping draft and a statements CSV in Working went with a blinded send)."""
    parts, name, suffix = rel.parts, rel.name, rel.suffix.lower()
    if ARCHIVE in parts:
        return "archive"
    if suffix in AUDIO_EXT:
        return "audio"
    if len(parts) > 1 and parts[0] == "Source":
        return "source"
    if len(parts) == 2 and parts[0] == "Working":
        if name.endswith(PROGRESS_TAIL):
            return None
        if PETS_FILE.search(name) or PET_DRAFT.search(name):
            return "pets"
        return "notes"
    if len(parts) == 1:
        if suffix == ".xlsx" and not name.startswith(("~$", ".")) and not BACKUP_STEM.search(rel.stem):
            return None
        if suffix in TABLES:
            return "pets"
    return "notes"


def gets_cases(root: Path) -> set:
    """Every participant the GETs, LGETs and Trajectories files hold, by label."""
    out = set()
    for name in GETS_FILES:
        try:
            data = json.loads((Path(root) / name).read_text(encoding="utf-8"))
        except (OSError, ValueError):
            continue
        if not isinstance(data, dict):
            continue
        for key in ("cases", "study", "placed"):
            if isinstance(data.get(key), dict):
                out |= {str(k) for k in data[key]}
    return out


def clean_name(text: str) -> str:
    return " ".join(NOT_IN_NAME.sub(" ", str(text or "")).split()).strip(". ")


def as_renamed(name, old_name: str, last: str) -> str:
    """A file's name as a chosen send names it, the folder's whole name in it taken by the label."""
    name = str(name or "")
    return name.replace(old_name, last) if old_name and old_name != last else name


def workbook_named(path: Path, renamed) -> bytes | None:
    """A themes, LPETs, GETs or LGETs file's JSON with each `workbook` key naming the workbook as the
    send names it (26 October), or None when none changes. `renamed(case, name)` answers a workbook's
    name in the file, `case` None for a themes or LPETs file's own `workbook`, else a GETs file's
    participant by label."""
    try:
        data = json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    if not isinstance(data, dict):
        return None
    hit = False
    if isinstance(data.get("workbook"), str):
        now = renamed(None, data["workbook"])
        hit = now != data["workbook"]
        data["workbook"] = now
    for label, held in (data.get("cases") or {}).items() if isinstance(data.get("cases"), dict) else ():
        if isinstance(held, dict) and isinstance(held.get("workbook"), str):
            now = renamed(label, held["workbook"])
            hit = hit or now != held["workbook"]
            held["workbook"] = now
    return (json.dumps(data, ensure_ascii=False, indent=1) + "\n").encode("utf-8") if hit else None


CODES_FILE = "idiograph-codes.json"


def codes_for(root: Path, sent: list[dict], path: Path) -> bytes:
    """A thematic analysis project's code list as a send of some of its participants carries it: the codes their
    workbooks use, each with its id, name and description, and none of the list's History or undo."""
    import codes as codes_mod
    data = codes_mod.load(Path(root)) or {"codes": []}
    people = []
    for p in sent:
        folder = Path(root) / p["folder"]
        for book in sorted(folder.glob("*.xlsx")) if folder.is_dir() else []:
            if not book.name.startswith(("~$", ".")):
                try:
                    people.append({"case": p["label"], "who": p["label"], "workbook": book, "rows": codes_mod.rows_of(book)})
                except Exception:  # noqa: BLE001  a workbook that cannot be read uses no code
                    continue
    used = {x["code"] for x in codes_mod.extracts_of(people)}
    kept = {"schema": codes_mod.SCHEMA, "created": data.get("created"), "updated": data.get("updated"),
            "codes": [c for c in data["codes"] if codes_mod.norm(c["name"]) in used], "history": []}
    return (json.dumps(kept, ensure_ascii=False, indent=2) + "\n").encode("utf-8")


def choose(root: Path, project_file: str, participants: list[dict], named: bool, out: set, asked: set,
           skip: Path | None = None) -> dict:
    """A chosen send's files and what stays out, nothing written. `participants` is every participant
    of the project, each `{"folder", "label", "send"}`, its folder a path from the root. `named` says
    some were chosen, so a file of no chosen participant stays out. `out` is the kinds left out, `asked`
    the kinds asked for by name. A participant carrying its own `out` takes that in place of `out` for
    the files in its folder, so the PETs and the recordings can go for one and stay for another (Adam's
    design E of 23 October). GETs whose participants do not all go stay out with a line, or are
    refused when asked for by name. Answers `files`, each `(source, name in the file)`, the source a
    path or the project file's bytes, `left`, each reason's files by their names on disk, `kinds_out`,
    `participants`, the labels sent, `each`, every label sent with the kinds of `EACH_KINDS` going for
    it, `per`, whether any participant carried its own, and `notes`, plain lines."""
    root = Path(root)
    out = set(out)
    notes = []
    sent = [p for p in participants if p["send"]]
    labels = [p["label"] for p in sent]
    # each participant's folder renamed in the file by its label alone, with the kinds it leaves out
    renames, taken, outs, by_label = {}, {}, {}, {}
    for p in sent:
        old = PurePosixPath(p["folder"])
        if not old.parts:
            # a project whose root is the participant's own folder, which the file names already
            renames[()] = ((), "", "")
            outs[()] = p.get("out")
            continue
        last = clean_name(p["label"]) or old.name
        new = PurePosixPath(last) if str(old.parent) == "." else old.parent / last
        if str(new).lower() in taken:
            raise PackError(i18n.t("server.would_share_folder_nothing_sent", label=p['label'], other=taken[str(new).lower()]))
        taken[str(new).lower()] = p["label"]
        renames[old.parts] = (new.parts, old.name, last)
        outs[old.parts] = p.get("out")
        if old.name != last:
            by_label[p["label"]] = (old.name, last)
    others = [PurePosixPath(p["folder"]).parts for p in participants if not p["send"]]
    if "gets" not in out and any((root / n).is_file() for n in GETS_FILES):
        missing = sorted(gets_cases(root) - set(labels))
        if missing:
            said = formats.list_words(missing)
            if "gets" in asked:
                raise PackError(i18n.t("server.gets_hold_who_would_sent", said=said))
            out.add("gets")
            notes.append(i18n.t("server.gets_stay_out_since_they", said=said))
    files, left = [], {}

    def under(parts: tuple, prefix: tuple) -> bool:
        return len(parts) > len(prefix) and parts[:len(prefix)] == prefix

    for path, rel in project_files(root, skip=skip):
        parts = PurePosixPath(rel).parts
        suffix = PurePosixPath(rel).suffix.lower()
        if rel == project_file:
            try:
                data = json.loads(path.read_text(encoding="utf-8"))
            except (OSError, ValueError):
                data = None
            if isinstance(data, dict) and "names" in data:
                data.pop("names")
                files.append(((json.dumps(data, ensure_ascii=False, indent=2) + "\n").encode("utf-8"), rel))
            else:
                files.append((path, rel))
            continue
        case = next((k for k in renames if under(parts, k)), None)
        reason = None
        if case is not None:
            inner = PurePosixPath(*parts[len(case):])
            kind = kind_in_case(inner)
            case_out = out if outs.get(case) is None else set(outs[case])
            if kind == "archive" or kind in case_out:
                reason = kind
            else:
                new_parts, old_name, last = renames[case]
                # a file's name carrying the folder's whole name takes the label in its place too
                tail = [as_renamed(part, old_name, last) for part in inner.parts]
                named_as = str(PurePosixPath(*new_parts, *tail))
                if PETS_FILE.search(inner.name) and old_name and old_name != last:
                    # the themes or LPETs file's `workbook` naming the workbook as it is sent (26 October)
                    held = workbook_named(path, lambda _, name: as_renamed(name, old_name, last))
                    if held is not None:
                        files.append((held, named_as))
                        continue
                if "pets" in case_out and inner.name.endswith(PROGRESS_TAIL):
                    # with the PETs out, the progress file goes without its History, whose requests may
                    # name a board or a PET
                    files.append((progress_without_history(path), named_as))
                    left.setdefault("history", []).append(rel)
                    continue
                files.append((path, named_as))
                continue
        elif any(under(parts, k) for k in others):
            reason = "participants"
        elif ARCHIVE in parts:
            reason = "archive"
        elif len(parts) == 1 and parts[0] == CODES_FILE:
            # a thematic analysis project's code list goes with them, holding the codes they use alone (codes)
            files.append((codes_for(root, sent, path), rel))
            continue
        elif len(parts) == 1 and (parts[0] in GETS_FILES or suffix in TABLES) and "gets" in out:
            # a table at the root is the GETs' own
            reason = "gets"
        elif suffix in AUDIO_EXT and "audio" in out:
            reason = "audio"
        elif named and not (len(parts) == 1 and (parts[0] in GETS_FILES or suffix in TABLES)):
            reason = "other"
        if reason:
            left.setdefault(reason, []).append(rel)
        elif len(parts) == 1 and parts[0] in GETS_FILES and by_label:
            # the GETs files' participants' workbooks named as they are sent (26 October)
            held = workbook_named(path, lambda label, name: as_renamed(name, *by_label.get(label, ("", ""))))
            files.append((held if held is not None else path, rel))
        else:
            files.append((path, rel))
    each = {}
    for p in sent:
        case_out = out if p.get("out") is None else set(p["out"])
        each[p["label"]] = [k for k in EACH_KINDS if k not in case_out]
    # each participant's folder by its name in the file, with its label
    cases = {"/".join(renames[PurePosixPath(p["folder"]).parts][0]): p["label"] for p in sent}
    return {"files": files, "left": {k: left[k] for k in LEFT_ORDER if k in left},
            "kinds_out": [k for k in KINDS if k in out], "participants": labels, "each": each,
            "per": any(p.get("out") is not None for p in sent), "notes": notes, "cases": cases}


def whole_less_audio(root: Path, participants: list[dict], skip: Path | None = None, audio: bool = False) -> dict:
    """The whole project as a plain send writes it, every folder by its own name, the project file, the
    GETs, working notes, Source, `_Archive` and History all as they are, with only the recordings left
    out, wherever they sit, unless `audio` keeps them too (Adam's design E of 23 October: Whole project,
    its one choice the recordings). `participants` is every participant, each `{"folder", "label"}`.
    Answers as `choose` does, `whole` saying so."""
    files, left = [], []
    for path, rel in project_files(Path(root), skip=skip):
        if not audio and PurePosixPath(rel).suffix.lower() in AUDIO_EXT:
            left.append(rel)
        else:
            files.append((path, rel))
    return {"files": files, "left": {"audio": left} if left else {}, "kinds_out": [] if audio else ["audio"],
            "participants": [p["label"] for p in participants], "each": {}, "per": False, "notes": [],
            "whole": True, "cases": {p["folder"]: p["label"] for p in participants}}


# ------------------------------------------------------------ the current board alone

# `boards` in a send (Adam, 23 October, sending a participant to a second analyst: "just include the
# current board, whichever number that is"): `all`, every board as it stands, or `current`, each board
# file with the board it is going with alone
BOARDS = ("all", "current")
BOARD_FILES = ("idiograph-gets.json", "idiograph-lgets.json")
TIMEPOINT_IN = re.compile(r"\.themes-(t\d+)\.json$", re.IGNORECASE)
NAME_UNSAFE = str.maketrans({c: "-" for c in '/\\:*?"<>|'})


def boards_held(data) -> list[dict]:
    """A board file's boards, under `boards` or, from schema 1, `versions`."""
    if not isinstance(data, dict):
        return []
    key = "boards" if isinstance(data.get("boards"), list) else "versions"
    return [b for b in data.get(key) or [] if isinstance(b, dict)]


def board_going(data) -> dict | None:
    """The board a file is going with: the Current board (`chosen`), else the board on the canvas
    (`current`), else its first, or None for a file with none."""
    boards = boards_held(data)
    ids = [str(b.get("id")) for b in boards]
    for key in ("chosen", "current"):
        if data.get(key) not in (None, "") and str(data[key]) in ids:
            return boards[ids.index(str(data[key]))]
    return boards[0] if boards else None


def current_board_only(data: dict) -> tuple[dict, dict | None, int]:
    """A board file with the board it is going with alone, its own id and name kept, marked current, and
    the Current board too when the file marked one. The board's restore points (`history`) stay behind,
    and a complete mark goes only when it names that board. Answers the file, the board and how many
    boards the file held."""
    boards = boards_held(data)
    board = board_going(data)
    if board is None:
        return data, None, 0
    key = "boards" if isinstance(data.get("boards"), list) else "versions"
    out = dict(data)
    out[key] = [{k: v for k, v in board.items() if k != "history"}]
    out["current"] = board.get("id")
    if out.get("chosen") not in (None, ""):
        out["chosen"] = board.get("id")
    held = out.get("complete")
    if isinstance(held, dict) and str(held.get("board") or "") != str(board.get("id")):
        out["complete"] = None
    return out, board, len(boards)


def board_safe(name) -> str:
    """A board's name as an export puts it in a file's name (`themes.draft_path`, `themes_word.stem`)."""
    return " ".join(str(name or "Board 1").translate(NAME_UNSAFE).split()) or "Board 1"


def tied_to(stem: str, names: set) -> bool:
    """Whether a PET draft's or a table's name, less its extension, names one of the boards `names`:
    "(Board 3)", or "(Board 3, 6 Oct 14.20)" with the date an export puts in when the name was taken."""
    return any(stem.endswith(f"({safe})") or re.search(re.escape(f"({safe}, ") + r"[^()]*\)$", stem)
               for safe in names)


def current_boards(plan: dict, root: Path) -> dict:
    """A send's plan with the current board alone (`BOARDS`' `current`): each themes, LPETs, GETs and
    LGETs file with the board it is going with alone (`current_board_only`), a PET draft or a PET or GETs
    table kept only when its name ties it to that board, every progress file without its History, whose
    requests name the other boards, and `_Archive`'s old copies left behind. `plan["cases"]` names each
    participant's folder in the file by its label. Adds `boards`, each board file's board that goes."""
    root = Path(root)
    cases = plan.get("cases") or {}
    left = {k: list(v) for k, v in plan["left"].items()}
    files, rest, going, names = [], [], [], {}

    def on_disk(src, rel):
        # what stays out is named by its path on disk, as `choose` names it
        if isinstance(src, Path):
            try:
                return src.relative_to(root).as_posix()
            except ValueError:
                pass
        return rel

    for src, rel in plan["files"]:
        parts = PurePosixPath(rel).parts
        name = parts[-1]
        if ARCHIVE in parts:
            left.setdefault("archive", []).append(on_disk(src, rel))
            continue
        in_case = len(parts) >= 2 and parts[-2] == "Working"
        if (in_case and PETS_FILE.search(name)) or (len(parts) == 1 and name in BOARD_FILES):
            try:
                data = json.loads(src.decode("utf-8") if isinstance(src, bytes) else src.read_text(encoding="utf-8"))
            except (OSError, ValueError):
                data = None
            if boards_held(data):
                data, board, held = current_board_only(data)
                where = "/".join(parts[:-2]) if in_case else None
                names.setdefault(where, set()).add(board_safe(board.get("name")))
                tp = TIMEPOINT_IN.search(name)
                if in_case:
                    kind = "LPETs" if name.lower().endswith(".lpets.json") else "PETs"
                else:
                    kind = "LGETs" if name == "idiograph-lgets.json" else "GETs"
                going.append({"participant": cases.get(where) if in_case else None, "kind": kind,
                              "timepoint": tp.group(1).lower() if tp else "", "board": str(board.get("name") or ""),
                              "id": board.get("id"), "of": held})
                files.append(((json.dumps(data, ensure_ascii=False, indent=1) + "\n").encode("utf-8"), rel))
                continue
        rest.append((src, rel))
    for src, rel in rest:
        path = PurePosixPath(rel)
        parts = path.parts
        working = len(parts) >= 2 and parts[-2] == "Working"
        if working and path.name.endswith(PROGRESS_TAIL):
            if not isinstance(src, bytes):
                left.setdefault("history", []).append(on_disk(src, rel))
                src = progress_without_history(src)
            files.append((src, rel))
            continue
        draft = working and PET_DRAFT.search(path.name)
        table = path.suffix.lower() in TABLES and ("/".join(parts[:-1]) in cases or len(parts) == 1)
        if draft or table:
            ties = set(names.get("/".join(parts[:-2] if draft else parts[:-1]), set()))
            if len(parts) == 1:
                # a table at the root is the GETs' own, or a participant's whose folder is the root
                ties |= names.get(None, set())
            if not tied_to(path.stem, ties):
                left.setdefault("boards", []).append(on_disk(src, rel))
                continue
        files.append((src, rel))
    return dict(plan, files=files, left={k: left[k] for k in LEFT_ORDER if k in left}, boards=going,
                board_choice="current")


def boards_said(path: Path) -> dict | None:
    """A board file's count of boards and the one it is going with, for `inventory`, or None."""
    try:
        data = json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    board = board_going(data)
    if board is None:
        return None
    return {"boards": len(boards_held(data)), "current": str(board.get("name") or ""), "id": board.get("id")}


def has_boards(path: Path) -> bool:
    """Whether a themes or LPETs file holds a board, so one with none is no PETs."""
    try:
        data = json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return False
    return isinstance(data, dict) and any(isinstance(data.get(k), list) and data[k] for k in ("boards", "versions"))


def inventory(root: Path, participants: list[dict]) -> dict:
    """What Share a copy's card needs to draw itself, nothing written and no file read but the themes
    files: each participant of `participants` (`{"folder", "label"}`) with whether it has PETs (a board,
    a PET draft or a PET table) and recordings, and their weight, then the whole project's recordings
    and weight and whether it has GETs. A recording in `_Archive` is no participant's, since a chosen
    send never sends one, and counts in the whole project's, which a whole send less audio leaves out."""
    root = Path(root)
    cases = [(PurePosixPath(p["folder"]).parts, p) for p in participants]
    rows = {p["label"]: {"label": p["label"], "pets": False, "audio": False, "audio_bytes": 0, "boards": []}
            for _, p in cases}
    total = audio = 0
    gets = False
    gets_boards = []
    for path, rel in project_files(root):
        parts = PurePosixPath(rel).parts
        size = path.stat().st_size
        total += size
        if PurePosixPath(rel).suffix.lower() in AUDIO_EXT:
            audio += size
        if len(parts) == 1 and parts[0] in GETS_FILES:
            gets = True
            said = boards_said(path) if parts[0] in BOARD_FILES else None
            if said:
                gets_boards.append(dict(said, kind="LGETs" if parts[0] == "idiograph-lgets.json" else "GETs"))
        # the deepest participant folder holding the file, a project whose root is one participant's
        # folder holding every file
        hits = [(k, p) for k, p in cases if len(parts) > len(k) and parts[:len(k)] == k]
        if not hits:
            continue
        case, p = max(hits, key=lambda h: len(h[0]))
        row = rows[p["label"]]
        inner = PurePosixPath(*parts[len(case):])
        kind = kind_in_case(inner)
        if kind == "audio":
            row["audio"] = True
            row["audio_bytes"] += size
        elif kind == "pets":
            said = boards_said(path) if inner.suffix.lower() == ".json" and ARCHIVE not in parts else None
            if said:
                # each board file's count of boards and the one a send with the current board alone takes
                tp = TIMEPOINT_IN.search(inner.name)
                row["boards"].append(dict(said, kind="LPETs" if inner.name.lower().endswith(".lpets.json") else "PETs",
                                          timepoint=tp.group(1).lower() if tp else ""))
            if not row["pets"]:
                row["pets"] = has_boards(path) if inner.suffix.lower() == ".json" else True
    for row in rows.values():
        row["audio_size"] = size_said(row["audio_bytes"])
    return {"participants": list(rows.values()), "gets": gets, "gets_boards": gets_boards,
            "audio": audio > 0, "audio_bytes": audio,
            "audio_size": size_said(audio), "bytes": total, "size": size_said(total),
            "bytes_less_audio": total - audio, "size_less_audio": size_said(total - audio)}


def plan_chosen(name: str, chosen: dict) -> dict:
    """What a chosen send would write, and nothing written: as `plan_send`, with every file by its
    name in the file and what stays out."""
    total = sum(len(src) if isinstance(src, bytes) else src.stat().st_size for src, _ in chosen["files"])
    return {"name": sent_name(name), "files": len(chosen["files"]), "bytes": total, "size": size_said(total),
            "listed": [rel for _, rel in chosen["files"]], "left": chosen["left"],
            "kinds_out": chosen["kinds_out"], "participants": chosen["participants"], "each": chosen.get("each", {}),
            "whole": bool(chosen.get("whole")), "notes": chosen["notes"],
            "board_choice": chosen.get("board_choice", "all"), "boards": chosen.get("boards", [])}


def safe_rel(text: str) -> PurePosixPath | None:
    """A path inside the file as a path under the copy's folder, or None for one that would reach out
    of it: absolute, with a drive, or climbing with `..`."""
    rel = PurePosixPath(str(text or ""))
    if not str(rel) or rel.is_absolute() or ".." in rel.parts or "\\" in str(text) or re.match(r"^[A-Za-z]:", str(text)):
        return None
    return rel


# what the list at the head says of where a file comes from: the project's own id, the print of each
# statement sent, by participant and key, and the project a copy was opened from (26 October), and the
# sender's own name, Settings' Your name, when it is set, so a copy coming back names whose it is (copyback,
# 6 November 2026), and the places print of each board sent, by participant, so a board coming back as it was
# sent is told as the sender's own (copyback2, 8 November 2026)
ORIGIN_KEYS = ("uid", "statements", "copy_of", "from", "boards")
UID_KEY = "uid"
# what a copy keeps of the project it was opened from, in its project file's `copy_of`
COPY_KEYS = ("uid", "name", "sent", "version")


def new_uid() -> str:
    """A project's own id, written once into its project file and never changed after."""
    return uuid.uuid4().hex[:16]


def statement_print(text) -> str:
    """A statement's words as a short print, its spacing set aside, so a statement edited since it was
    sent is told from one as it was without its words travelling twice."""
    return hashlib.sha256(" ".join(str(text or "").split()).encode("utf-8")).hexdigest()[:12]


def read_sent(file: Path) -> dict:
    """What a sent file holds, its list read and checked, refused in one line when it is no sent
    project, from a newer Idiograph, or not whole: `name`, `folder`, `files` and their weight."""
    file = Path(file)
    if not file.is_file():
        raise PackError(i18n.t("server.file"))
    try:
        with zipfile.ZipFile(file) as zf:
            try:
                head = json.loads(zf.read(MANIFEST).decode("utf-8"))
            except KeyError:
                raise PackError(i18n.t("server.file_project_sent_from_idiograph")) from None
            names = set(zf.namelist())
    except (zipfile.BadZipFile, OSError, ValueError, UnicodeDecodeError):
        raise PackError(i18n.t("server.file_project_sent_from_idiograph")) from None
    if not isinstance(head, dict) or head.get("kind") != KIND:
        raise PackError(i18n.t("server.file_project_sent_from_idiograph"))
    try:
        fmt = int(head.get("format"))
    except (TypeError, ValueError):
        raise PackError(i18n.t("server.file_project_sent_from_idiograph")) from None
    if fmt > FORMAT:
        raise PackError(i18n.t("server.project_sent_from_newer_idiograph"))
    listed = head.get("files")
    if not isinstance(listed, list):
        raise PackError(i18n.t("server.file_project_sent_from_idiograph"))
    for entry in listed:
        rel = safe_rel(entry.get("path") if isinstance(entry, dict) else "")
        if rel is None or TOP + str(rel) not in names:
            raise PackError(i18n.t("server.file_did_arrive_whole_nothing"))
    total = sum(int(e.get("bytes") or 0) for e in listed)
    folder = " ".join(NOT_IN_NAME.sub(" ", str(head.get("folder") or "")).split()).strip(". ")
    out = {"name": str(head.get("name") or "").strip() or folder or "Project", "folder": folder or "Project",
           "files": len(listed), "bytes": total, "size": size_said(total), "format": fmt, "listed": listed,
           "sent": str(head.get("sent") or ""), "version": str(head.get("version") or ""),
           "uid": str(head.get("uid") or ""), "from": " ".join(str(head.get("from") or "").split())[:120]}
    out["statements"] = head["statements"] if isinstance(head.get("statements"), dict) else {}
    out["copy_of"] = head["copy_of"] if isinstance(head.get("copy_of"), dict) else {}
    out["boards"] = head["boards"] if isinstance(head.get("boards"), dict) else {}
    return out


# ------------------------------------------------------------ a copy coming back

THEMES_IN = re.compile(r"^(?P<stem>.+)\.themes(?:-t(?P<n>\d+))?\.json$")


def sent_json(file: Path, rel: str) -> dict | None:
    """One JSON file the sent file holds, by its path in the project, or None when it holds none or
    one that cannot be read."""
    try:
        with zipfile.ZipFile(file) as zf:
            data = json.loads(zf.read(TOP + rel).decode("utf-8"))
    except (KeyError, OSError, ValueError, UnicodeDecodeError, zipfile.BadZipFile):
        return None
    return data if isinstance(data, dict) else None


def sent_codes(file: Path) -> list[dict]:
    """The codes a sent file's code list holds, at its root, each `{"name", "description"}`, none when it has no list
    or one that cannot be read (codes, 2 November 2026)."""
    with zipfile.ZipFile(file) as zf:
        try:
            data = json.loads(zf.read(TOP + CODES_FILE).decode("utf-8"))
        except (KeyError, ValueError, UnicodeDecodeError):
            return []
    return [{"name": str(c.get("name") or ""), "description": str(c.get("description") or "")}
            for c in (data.get("codes") if isinstance(data, dict) and isinstance(data.get("codes"), list) else [])
            if isinstance(c, dict) and str(c.get("name") or "").strip()]


def sent_boards(file: Path) -> list[dict]:
    """Every PETs file the sent file holds, in a participant's `Working/`, never in `_Archive`: each
    `{"folder", "stem", "timepoint", "data"}`, the participant's folder by its path in the file, the
    workbook's stem, the timepoint, 1 for T1's file, and the file read. LPETs are not PETs boards. A
    file that cannot be read is passed over."""
    out = []
    with zipfile.ZipFile(file) as zf:
        for name in sorted(zf.namelist()):
            if not name.startswith(TOP):
                continue
            parts = PurePosixPath(name[len(TOP):]).parts
            if len(parts) < 2 or parts[-2] != "Working" or ARCHIVE in parts:
                continue
            m = THEMES_IN.match(parts[-1])
            if not m:
                continue
            try:
                data = json.loads(zf.read(name).decode("utf-8"))
            except (ValueError, UnicodeDecodeError):
                continue
            if not isinstance(data, dict):
                continue
            out.append({"folder": "/".join(parts[:-2]), "stem": m.group("stem"),
                        "timepoint": int(m.group("n") or 1), "data": data})
    return out


def copy_folder(into: Path, folder: str) -> Path:
    """The new folder the copy goes in: its own name in `into`, or with "copy" after it when that is
    taken, then "copy 2" and up. Never one already there."""
    into = Path(into)
    first = into / folder
    if not first.exists():
        return first
    n = 1
    while True:
        tried = into / (f"{folder} copy" if n == 1 else f"{folder} copy {n}")
        if not tried.exists():
            return tried
        n += 1


def plan_open(file: Path, into: Path) -> dict:
    """What opening a sent file would write, and nothing written: the new folder and what goes in it."""
    held = read_sent(file)
    into = Path(into)
    if not into.is_dir():
        raise PackError(i18n.t("server.folder_nothing_opened"))
    dest = copy_folder(into, held["folder"])
    return dict({k: v for k, v in held.items() if k != "listed"}, folder=str(dest), folder_name=dest.name)


def unpack(file: Path, dest: Path) -> dict:
    """The sent file unpacked into `dest`, a folder not yet there, through a folder beside it renamed
    into place once every file is out and matches its list, so a failure leaves nothing."""
    held = read_sent(file)
    dest = Path(dest)
    if dest.exists():
        raise PackError(i18n.t("server.folder_already_nothing_opened"))
    tmp = dest.with_name(f".{dest.name}.opening")
    shutil.rmtree(tmp, ignore_errors=True)
    try:
        tmp.mkdir(parents=True)
        with zipfile.ZipFile(file) as zf:
            for entry in held["listed"]:
                rel = safe_rel(entry["path"])
                target = tmp.joinpath(*rel.parts)
                target.parent.mkdir(parents=True, exist_ok=True)
                digest = hashlib.sha256()
                with zf.open(TOP + str(rel)) as src, open(target, "wb") as out:
                    for block in iter(lambda: src.read(1 << 20), b""):
                        digest.update(block)
                        out.write(block)
                if digest.hexdigest() != entry.get("sha256"):
                    raise PackError(i18n.t("server.file_did_arrive_whole_nothing"))
        os.replace(tmp, dest)
    except BaseException:
        shutil.rmtree(tmp, ignore_errors=True)
        raise
    return {"opened": True, "folder": str(dest), "folder_name": dest.name, "name": held["name"],
            "files": held["files"], "bytes": held["bytes"], "size": held["size"]}


def __getattr__(name: str) -> str:
    """The refusals other modules and the checks name as this module's, each read in the run's language when
    asked for (the text layer, 28 October 2026)."""
    said = {
        "NOT_SENT": lambda: i18n.t("server.file_project_sent_from_idiograph"),
        "NEWER": lambda: i18n.t("server.project_sent_from_newer_idiograph"),
        "BROKEN": lambda: i18n.t("server.file_did_arrive_whole_nothing"),
    }
    if name in said:
        return said[name]()
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
