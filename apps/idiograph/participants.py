#!/usr/bin/env python3
"""Each participant's picture, label and pen portrait (pbiobuild, 11 November 2026, Adam's layout A of pbiodraw's
proposal, by dialog about 18:10).

Every participant of every project, IPA and thematic analysis alike, has a set of their own beside the number and
pseudonym their folder gives them:

1. a **picture**, one of the app's drawn set, `set:peep07` (`trajectories.FACES`), his own file kept in `pictures/`
   at the project's root, or none, which shows the initial on the participant's colour. One of the set before,
   `set:face07`, is kept as it is and shown as its nearest now (`trajectories.FACES_BEFORE`),
2. a **label**, a few words, "Pepper's keeper", up to LABEL_MAX characters,
3. a **pen portrait**, one short paragraph of plain text, up to PORTRAIT_MAX characters, its line breaks folded
   into spaces.

The set is kept once for the project, in the project's own file, `idiograph-project.json`, under `participants`,
by the participant's label as his order (`order`) and Rename's names (`names`) are:

    "participants": {"P2 - Mabel": {"label": "Pepper's keeper", "portrait": "Widowed, 73, lives alone.",
                                    "picture": "set:peep07"},
                     "P1 - Juno": {"label": "The reluctant convert", "picture": "Juno.png"}}

The real name is never kept here. A save whose label or pen portrait holds a name from the project's list of names
to replace (`names.py`) is refused whole, nothing written, and the refusal names the list's entry by its number,
never the name.

Trajectories reads the picture and the label from here, and its editor's `title` and `picture` operations write
them here (`trajectories.apply`, `people`). A Trajectories file from before keeps them on each participant it
places, `placed[case]["title"]` and `["picture"]`, its pictures in `trajectories/pictures/`. Every read merges them
in where the project file holds none (`view`), so nothing is lost and nothing is written by a read. The first save
of a participant's set, from any road, and the project page's first listing move them over for good (`settle`):
both files copied to `_Archive/` first, `(pre-participants <date-time>)`, a picture's file copied into
`pictures/` and its original left where it is, then `title` and `picture` taken off `placed` in the same change,
so there is only ever one label. One History line says so.

Every change goes through `apply`, its fields checked first and the whole refused when one is wrong, and with a
dry run nothing is written. A picture is written into `pictures/` only with the change, and the one it replaces
goes to `pictures/_Archive/`, never deleted (`trajectories.picture_files`). Standard library, the names list's
finder and the Trajectories module's pictures.
"""
from __future__ import annotations

import copy
import json
import re
import shutil
from pathlib import Path

import i18n
import names as names_mod
import trajectories as traj_mod
from workbook import WorkbookError

KEY = "participants"
LABEL_MAX = traj_mod.LABEL_MAX
PORTRAIT_MAX = 800
PICTURES = ("pictures",)
FIELDS = ("label", "portrait", "picture")
ARCHIVE_LABEL = "pre-participants"


def pictures_of(root: Path) -> Path:
    return Path(root).joinpath(*PICTURES)


def words(text) -> str:
    return " ".join(str(text or "").split())


def one(raw) -> dict:
    """A participant's set as the file keeps it, anything it cannot read left out, empty fields left out."""
    raw = raw if isinstance(raw, dict) else {}
    out = {}
    label = words(raw.get("label"))[:LABEL_MAX]
    if label:
        out["label"] = label
    portrait = words(raw.get("portrait"))[:PORTRAIT_MAX]
    if portrait:
        out["portrait"] = portrait
    picture = traj_mod.picture_kept(raw.get("picture"))
    if picture:
        out["picture"] = picture
    return out


def own_of(project: dict | None) -> dict[str, dict]:
    """Every participant's set the project file holds, by label, those with nothing in them left out."""
    held = (project or {}).get(KEY) if isinstance(project, dict) else None
    out = {}
    for case, raw in (held.items() if isinstance(held, dict) else ()):
        kept = one(raw)
        if isinstance(case, str) and case.strip() and kept:
            out[case] = kept
    return out


def traj_raw(root: Path) -> dict | None:
    """The Trajectories file as it sits, None when there is none or it cannot be read (its own reader refuses it
    where it matters)."""
    path = traj_mod.path_of(root)
    if not path.exists():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    return data if isinstance(data, dict) else None


def traj_held(data: dict | None) -> dict[str, dict]:
    """The label and the picture a Trajectories file from before keeps on each participant it places."""
    placed = (data or {}).get("placed") if isinstance((data or {}).get("placed"), dict) else {}
    out = {}
    for case, at in placed.items():
        if not isinstance(at, dict):
            continue
        kept = {}
        if words(at.get("title")):
            kept["label"] = words(at.get("title"))[:LABEL_MAX]
        if traj_mod.picture_kept(at.get("picture")):
            kept["picture"] = traj_mod.picture_kept(at.get("picture"))
        if kept:
            out[str(case)] = kept
    return out


def unsettled(root: Path) -> bool:
    """Whether the project's Trajectories file still keeps a label or a picture on a participant."""
    return bool(traj_held(traj_raw(root)))


def view(root: Path | None, project: dict) -> dict[str, dict]:
    """Every participant's set as the screens and the agents read it, by label: the project file's own, and where
    it holds no label or no picture for a participant, the one a Trajectories file from before keeps, its picture
    marked `from_traj` so its address is the Trajectories folder's. Only reads."""
    out = {case: dict(kept) for case, kept in own_of(project).items()}
    if root is None:
        return out
    for case, kept in traj_held(traj_raw(root)).items():
        entry = out.setdefault(case, {})
        if "label" in kept and "label" not in entry:
            entry["label"] = kept["label"]
        if "picture" in kept and "picture" not in entry:
            entry["picture"] = kept["picture"]
            if not kept["picture"].startswith("set:"):
                entry["from_traj"] = True
    return out


def who(case: str) -> str:
    return traj_mod.who(case)


def find(people: dict[str, dict], case: str) -> dict:
    """A participant's set by their label, or failing that by their pseudonym, any case, empty for none."""
    if case in people:
        return people[case]
    name = who(case).lower()
    for key, kept in people.items():
        if who(key).lower() == name:
            return kept
    return {}


def key_of(people: dict[str, dict], case: str) -> str:
    """The key a participant's set is kept under: their label, or the key already kept for their pseudonym."""
    if case in people:
        return case
    name = who(case).lower()
    return next((k for k in people if who(k).lower() == name), case)


# ------------------------------------------------------------------ a change

def real_name_in(text: str, entries: list[dict]) -> int | None:
    """The number of the first entry of the project's list of names to replace whose name the text holds, from 1,
    whoever the entry is for, or None."""
    if not text or not entries:
        return None
    everyone = [dict(e, **{"for": None}) for e in entries if isinstance(e, dict) and e.get("real")]
    found = names_mod.find(text, everyone, None)
    if not found:
        return None
    hit = everyone[found[0]["entry"]]
    return next((n for n, e in enumerate(entries, start=1) if e is not None and e.get("real") == hit.get("real")), 1)


def apply(people: dict[str, dict], case: str, given: dict, files: dict, names: list[dict] | None = None,
          read_file=None) -> list[str]:
    """One participant's set changed in `people`, in place, answering a line for each change. `given` holds any of
    `label` and `portrait`, a string, "" clearing it, and for the picture one of `picture`, `set:peep07` or "" to
    take it off, `from`, an image file's path, or `data`, a data URL as the page sends one. A key left out keeps
    what is there. Refused as a whole, with `people` to be thrown away, when one is wrong: a label or a pen
    portrait over its limit or holding a name from the list of names to replace (`names`), a picture that is not
    one of the set or cannot be read. A picture's bytes go into `files` by the name they are kept under, `None`
    for one taken off, for `pictures.write` to write."""
    key = key_of(people, case)
    held = people.setdefault(key, {})
    name = who(case)
    said = []
    if "label" in given and given["label"] is not None:
        label = words(given["label"])
        if len(label) > LABEL_MAX:
            raise WorkbookError(i18n.t("server.trajectory_label_long", most=LABEL_MAX))
        entry = real_name_in(label, names or [])
        if entry:
            raise WorkbookError(i18n.t("server.participant_real_name_label", entry=entry))
        was = held.get("label") or ""
        if label != was:
            if label:
                held["label"] = label
            else:
                held.pop("label", None)
            said.append(f"{name}'s label from {was} to {label}." if was and label
                        else f"{name}'s label is {label} now." if label else f"{name}'s label cleared.")
    if "portrait" in given and given["portrait"] is not None:
        portrait = words(given["portrait"])
        if len(portrait) > PORTRAIT_MAX:
            raise WorkbookError(i18n.t("server.participant_portrait_long", most=PORTRAIT_MAX))
        entry = real_name_in(portrait, names or [])
        if entry:
            raise WorkbookError(i18n.t("server.participant_real_name_portrait", entry=entry))
        was = held.get("portrait") or ""
        if portrait != was:
            if portrait:
                held["portrait"] = portrait
            else:
                held.pop("portrait", None)
            said.append(f"{name}'s pen portrait " + ("changed." if was and portrait else "written." if portrait
                                                      else "cleared."))
    picked = [k for k in ("picture", "from", "data") if given.get(k) is not None]
    if picked:
        was = held.get("picture") or ""
        if given.get("data") not in (None, "") or given.get("from") not in (None, ""):
            raw = (traj_mod.data_url(given["data"]) if given.get("data") not in (None, "")
                   else (read_file or traj_mod.read_picture)(str(given["from"])))
            body, ext = traj_mod.picture_bytes(raw)
            now = traj_mod.own_name(name, ext, was)
            files[now] = body
        else:
            said_pic = words(given.get("picture"))
            if said_pic.lower() in ("", "none", "null"):
                now = ""
            else:
                face = traj_mod.face_of(said_pic[4:] if said_pic.lower().startswith("set:") else said_pic)
                if not face:
                    raise WorkbookError(i18n.t("server.trajectory_no_such_face", face=said_pic,
                                               first=traj_mod.FACES[0], last=traj_mod.FACES[-1]))
                now = f"set:{face}"
        if now != was or now in files:
            if was and not was.startswith("set:") and not held.get("from_traj"):
                files.setdefault(was, None)
            held.pop("from_traj", None)
            if now:
                held["picture"] = now
            else:
                held.pop("picture", None)
            said.append(f"{name}'s picture changed." if now else f"{name}'s picture taken off.")
    if not any(held.get(k) for k in FIELDS):
        people.pop(key, None)
    return said


def written(people: dict[str, dict]) -> dict[str, dict]:
    """The sets as the project file keeps them, those empty left out, in case order."""
    out = {}
    for case in sorted(people, key=traj_mod.case_order):
        kept = one(people[case])
        if kept:
            out[case] = kept
    return out


# ------------------------------------------------------------------ Trajectories' labels and pictures moved over

def archive_copy(path: Path, stamp: str) -> None:
    """A copy of a file in `_Archive/` beside it, `<stem> (pre-participants <date-time>).json`, never over one."""
    folder = Path(path).parent / "_Archive"
    folder.mkdir(parents=True, exist_ok=True)
    stem = Path(path).name[:-len(".json")] if Path(path).name.endswith(".json") else Path(path).stem
    target, n = folder / f"{stem} ({ARCHIVE_LABEL} {stamp}).json", 2
    while target.exists():
        target, n = folder / f"{stem} ({ARCHIVE_LABEL} {stamp}-{n}).json", n + 1
    shutil.copy2(path, target)


def settle(root: Path, project: dict, project_path: Path, when: str, save_json, write_traj) -> list[str]:
    """Trajectories' labels and pictures moved into the participants' own sets for good, the caller holding the
    project's lock: each where the project file holds none, a picture's file copied from `trajectories/pictures/`
    into `pictures/`, then both files copied to `_Archive/`, then `title` and `picture` taken off `placed`, the
    project file written first. Answers the History's line, none when there was nothing to move. `save_json` and
    `write_traj` are the writers the routes write those files with."""
    data = traj_raw(root)
    moving = traj_held(data)
    if not moving:
        return []
    stamp = re.sub(r"[^0-9T]", "", str(when))[:15].replace("T", "-") or "0"
    people = copy.deepcopy(own_of(project))
    for case, kept in moving.items():
        entry = people.setdefault(case, {})
        if "label" in kept and "label" not in entry:
            entry["label"] = kept["label"]
        if "picture" in kept and "picture" not in entry:
            name = kept["picture"]
            if not name.startswith("set:"):
                source = traj_mod.pictures_of(root) / name
                if not source.is_file():
                    continue
                folder = pictures_of(root)
                folder.mkdir(parents=True, exist_ok=True)
                target = folder / name
                n = 2
                while target.exists():
                    target = folder / f"{Path(name).stem}-{n}{Path(name).suffix}"
                    n += 1
                shutil.copy2(source, target)
                name = target.name
            entry["picture"] = name
    if project_path.exists():
        archive_copy(project_path, stamp)
    archive_copy(traj_mod.path_of(root), stamp)
    project[KEY] = written(people)
    save_json(project_path, project)
    for case, at in list((data.get("placed") or {}).items()):
        if isinstance(at, dict):
            at.pop("title", None)
            at.pop("picture", None)
    line = f"Labels and pictures of {len(moving)} participant{'s' if len(moving) != 1 else ''} moved from " \
           "Trajectories to the participants' own."
    data["updated"] = when
    data["history"] = ((data.get("history") if isinstance(data.get("history"), list) else [])
                       + [{"when": when, "changes": [line]}])[-traj_mod.HISTORY_MAX:]
    write_traj(root, data)
    return [line]


# ------------------------------------------------------------------ as the screens and the agents read it

def shown(case: str, kept: dict, url: str, colour: int | None) -> dict:
    """One participant's set as a screen draws it and an agent reads it: `case`, `who`, `label`, `portrait`,
    `picture` (`set:peep07`, his own file's name, or ""), `picture_url`, where the page reads it, and `colour`, their
    place in the participants' palette, for the initial on their colour where there is no picture."""
    return {"case": case, "who": who(case), "label": kept.get("label") or "", "portrait": kept.get("portrait") or "",
            "picture": kept.get("picture") or "", "picture_url": url, "colour": colour if colour is not None else 0}


# ------------------------------------------------------------------ in the exports (pbioexport)

# The exports carry a participant's label and pen portrait, never the picture, since a photo of a real participant
# identifies them (pbioexport, 11 November 2026, the Exports of pbiodraw's proposal, Adam's choice): the table of
# PETs, its print view, PDF and Word document, with Pen portrait under Export ticked, the two under the
# participant's heading, and the GET table, the audit trail and the full set, print view and PDF, and a thematic
# analysis project's theme table in Word too, with Participants table on the print card ticked, a first page
# listing each participant in order. A participant with neither adds nothing under their heading, and has a row
# with its cells empty in the table.
PRINTED = ("label", "portrait")


def printed(kept: dict | None) -> dict:
    """A participant's label and pen portrait as an export prints them, each left out when empty, the picture
    never."""
    kept = kept if isinstance(kept, dict) else {}
    return {k: words(kept.get(k)) for k in PRINTED if words(kept.get(k))}


def number_of(case: str, place: int) -> str:
    """A participant's number in the participants table: the one their folder gives them, P2 for `P2 - Mabel`, and
    for a folder with none their place in the order, from 1."""
    found = re.match(r"^(P\d+)\b", str(case or "").strip())
    return found.group(1) if found else str(place)


def table_rows(people: dict[str, dict], cases: list[str], name=who) -> list[dict]:
    """The participants table's rows, one for each of `cases` in their order: the number, the pseudonym as `name`
    gives it, the label and the pen portrait, "" where they have none."""
    out = []
    for place, case in enumerate(cases, start=1):
        kept = printed(find(people, case))
        out.append({"number": number_of(case, place), "pseudonym": name(case), "label": kept.get("label", ""),
                    "portrait": kept.get("portrait", "")})
    return out


def table_heads() -> list[str]:
    """The participants table's column heads, in the run's language."""
    return [i18n.t("page_print.people.number"), i18n.t("page_print.people.pseudonym"),
            i18n.t("page_print.people.label"), i18n.t("page_print.people.portrait")]
