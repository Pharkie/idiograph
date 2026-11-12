#!/usr/bin/env python3
"""The Trajectories board (21 October, timepoints part 3, Adam's model after Farr and Nizza 2019): after the
LGETs, the project's own trajectories, each participant placed in one, with a note on why.

The trajectories are never fixed by the app. He makes and names them on the board itself, as a GET's title is
named: his own study's are Positive, Mixed and No impact, and another study's are its own.

Layout F (Adam, 10 November 2026, from his Freeform page after revD): each trajectory a band down the screen
with its colour, one of PALETTE, its icon, one of ICONS, and its sentence, `description`, then its
participants in his order, `order`, any not named there after them in case order. Each participant keeps
their own label, `title` ("The late starter"), their tags, free words whose colour is kept once for the
project in `tags`, a place in the participants' palette, so a tag reads the same on everyone, their picture,
a file in `trajectories/pictures/` in the project folder or one of the app's set, `set:peep07`, with none the
initial on their colour, and `hidden`, the ids of the LPETs this screen leaves out, every LPET shown until he
hides one. Under them each LPET is a row: its title and its domain, then at each timepoint its key quote over
its state. The domain is the LPET's own, on the participant's LPETs board, and its colour comes from `tags`
too, each domain its own when commas separate several. The state, the key quote, its words without the marks the
workbook keeps round them, and his bold in it are the LPET table's row on that board (`gets.row_op`), the key
quote the LPET's own, another statement's of that interview or a passage of any of the participant's transcripts
(trajchoose, 11 November 2026), and this module hands those operations, LPET_OPS, to the caller's `lpet_op`.

The file is `idiograph-trajectories.json` at the project's root, written only once a change is made:

    {"schema": 1, "created": "...", "updated": "...", "note": "Icons by ...",
     "columns": [{"id": "c1", "title": "Positive", "description": "The plot gave them a place.",
                  "colour": "good", "icon": "rising", "order": ["P2 - Ash", "P1 - Wren"]},
                 {"id": "c2", "title": "Mixed"}],
     "placed": {"P1 - Wren": {"column": "c1", "note": "Asks the neighbours by midsummer",
                              "title": "The late starter", "tags": ["Town", "First plot"],
                              "picture": "Wren.png", "hidden": ["G2"]}},
     "tags": {"Town": 3, "First plot": 7, "Practical": 1},
     "history": [{"when": "...", "changes": ["Positive added."], "note": "", "tool": ""}]}

The board's own `note` (trajnote, 10 November 2026) is his free text for the whole screen, shown under its
title while the status bar's Notes is on, and kept here beside the trajectories.

A participant goes by their label, `P1 - Wren`, the GETs' case. What is kept on a participant stays when
they are taken out of every trajectory, and a trajectory taken away puts its participants back among those
not placed, each keeping theirs. Every change, from the board or from an agent, goes through `apply`, its
operations checked first and all refused when one is wrong, and with `dry_run` nothing is written. A picture
is written into the project folder only with the change, and the one it replaces goes to the pictures'
`_Archive`, never deleted. Standard library, the themes module and the GETs module's palette.
"""
from __future__ import annotations

import base64
import json
import os
import re
import struct
import zlib
from pathlib import Path

import i18n
import themes
from workbook import WorkbookError

FILE = "idiograph-trajectories.json"
SCHEMA = 1
TITLE_MAX = 60
NOTE_MAX = 2000
HISTORY_MAX = 200
DESCRIPTION_MAX = 400
LABEL_MAX = 60
TAG_MAX = 40
TAGS_MAX = 12
# a trajectory's colours, drawn from the app's own tokens, each with its dark-mode value in tokens.css: the name
# the file keeps and the name the picker and an agent use
PALETTE = {"good": "Green", "amber": "Amber", "danger": "Red", "excerpt": "Blue", "sift": "Plum", "trace": "Teal",
           "accent": "Taupe", "crux": "Orange"}
ICONS = ("rising", "mixed", "falling", "level")
# the participants' palette, gets.COLOUR_NAMES, a tag's colour a place in it
TAG_NAMES = ("Blue", "Olive", "Plum", "Brown", "Indigo", "Teal", "Purple", "Slate",
             "Moss", "Spruce", "Violet", "Aubergine", "Pine", "Denim", "Khaki", "Mulberry", "Fern", "Periwinkle", "Umber",
             "Grape", "Ocean", "Amethyst", "Jade", "Navy", "Fig")
# the app's own set of pictures (peeps, 12 November 2026): forty Open Peeps drawn in ink, static/faces/peep01.svg
# to peep40.svg, made by packaging/make_peeps.py
FACES = tuple(f"peep{n:02d}" for n in range(1, 41))
# The drawn set before it, face01 to face24 (eight heads of hair, each plain, with glasses, and with a beard or
# earrings), which projects hold still: each is read as its nearest in the set now, the same hair and, where the
# set has them, the same glasses or beard. Nothing a project holds is rewritten by a read, and one of them chosen
# again is kept as its new name.
FACES_BEFORE = {
    "face01": "peep02", "face02": "peep27", "face03": "peep01", "face04": "peep38", "face05": "peep03",
    "face06": "peep32", "face07": "peep39", "face08": "peep12", "face09": "peep19", "face10": "peep33",
    "face11": "peep15", "face12": "peep07", "face13": "peep37", "face14": "peep21", "face15": "peep13",
    "face16": "peep18", "face17": "peep09", "face18": "peep22", "face19": "peep01", "face20": "peep23",
    "face21": "peep36", "face22": "peep14", "face23": "peep13", "face24": "peep26",
}
PICTURES = ("trajectories", "pictures")
PICTURE_SIZE = 256
PICTURE_SIDE_MAX = 2000
PICTURE_MAX = 12 * 1024 * 1024
KEPT_MAX = {"jpg": 400 * 1024, "svg": 200 * 1024}
# the operations kept in this file, then those on a participant's LPETs board, which the caller runs
OPS = ("add", "rename", "move", "remove", "place", "note", "describe", "colour", "icon", "title", "tags",
       "tag_colour", "picture", "order", "hide", "show", "note_board")
LPET_OPS = ("state", "quote", "bold", "domain", "states_from_notes")


def path_of(root: Path) -> Path:
    return Path(root) / FILE


def pictures_of(root: Path) -> Path:
    return Path(root).joinpath(*PICTURES)


def fresh(when: str) -> dict:
    return {"schema": SCHEMA, "created": when, "updated": when, "columns": [], "placed": {}, "tags": {}, "history": []}


def load(root: Path) -> dict | None:
    """The file as it sits on disk, or None when there is none yet. One that is there and cannot be
    read is refused, so nothing is ever written over a file that can be recovered."""
    path = path_of(root)
    if not path.exists():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        raise WorkbookError(i18n.t("server.could_read_nothing_written", name=path.name))
    if not isinstance(data, dict):
        raise WorkbookError(i18n.t("server.trajectories_file_nothing_written", name=path.name))
    return normal(data)


def normal(data: dict) -> dict:
    """The file's trajectories and placings as the board reads them, anything it cannot read left out."""
    columns, seen = [], set()
    for c in data.get("columns") if isinstance(data.get("columns"), list) else []:
        if isinstance(c, dict) and str(c.get("id") or "") and str(c["id"]) not in seen:
            seen.add(str(c["id"]))
            col = {"id": str(c["id"]), "title": words(c.get("title"))}
            if words(c.get("description")):
                col["description"] = words(c.get("description"))[:DESCRIPTION_MAX]
            if c.get("colour") in PALETTE:
                col["colour"] = c["colour"]
            if c.get("icon") in ICONS:
                col["icon"] = c["icon"]
            order = [str(x) for x in c.get("order") or [] if isinstance(x, str)] if isinstance(c.get("order"), list) else []
            if order:
                col["order"] = list(dict.fromkeys(order))
            columns.append(col)
    placed = {}
    for case, at in (data.get("placed") if isinstance(data.get("placed"), dict) else {}).items():
        if not isinstance(at, dict):
            continue
        column = str(at.get("column") or "") or None
        held = {"column": column if column in seen else None, "note": str(at.get("note") or "")}
        if words(at.get("title")):
            held["title"] = words(at.get("title"))[:LABEL_MAX]
        if tags_kept(at.get("tags")):
            held["tags"] = tags_kept(at.get("tags"))
        if picture_kept(at.get("picture")):
            held["picture"] = picture_kept(at.get("picture"))
        hidden = [str(x) for x in at.get("hidden") or [] if isinstance(x, str)] if isinstance(at.get("hidden"), list) else []
        if hidden:
            held["hidden"] = list(dict.fromkeys(hidden))
        placed[str(case)] = held
    colours = {}
    for word, n in (data.get("tags") if isinstance(data.get("tags"), dict) else {}).items():
        if words(word) and isinstance(n, int) and not isinstance(n, bool) and 0 <= n < len(TAG_NAMES):
            colours[words(word)[:TAG_MAX]] = n
    history = [h for h in data.get("history") or [] if isinstance(h, dict)] if isinstance(data.get("history"), list) else []
    out = dict(data, columns=columns, placed=placed, tags=colours, history=history)
    note = data.get("note").strip()[:NOTE_MAX] if isinstance(data.get("note"), str) else ""
    if note:
        out["note"] = note
    else:
        out.pop("note", None)
    return out


def tags_kept(given) -> list[str]:
    """A participant's tags as the file keeps them: each a few words on one line, once each in any case, in his
    order."""
    out, seen = [], set()
    for t in given if isinstance(given, list) else []:
        word = words(t)[:TAG_MAX]
        if word and word.lower() not in seen:
            seen.add(word.lower())
            out.append(word)
    return out[:TAGS_MAX]


def face_of(name) -> str:
    """One of the set by its name, `peep07`, one from the set before as its nearest now, or "" when it is
    neither."""
    name = str(name or "").strip().lower()
    return name if name in FACES else FACES_BEFORE.get(name, "")


def picture_kept(given) -> str:
    """A picture's name as the file keeps it: one of the set, `set:peep07`, one of the set before, `set:face07`,
    kept as it is, or a file's name in the project's pictures folder, never a path."""
    name = str(given or "").strip()
    if name.startswith("set:"):
        return name if name[4:] in FACES or name[4:] in FACES_BEFORE else ""
    return name if re.fullmatch(r"[A-Za-z0-9][\w .-]{0,118}\.(png|jpg|svg)", name) else ""


def write(root: Path, data: dict) -> Path:
    """Written to a temporary file beside it and moved over the old one, as the GETs file is."""
    path = path_of(root)
    tmp = path.with_name(path.name + ".tmp")
    tmp.write_text(themes.render(data) + "\n", encoding="utf-8", newline="\n")
    os.replace(tmp, path)
    return path


def who(case: str) -> str:
    """The pseudonym alone, `P1 - Wren` is Wren."""
    text = str(case or "")
    return re.sub(r"^P\d+\s*-\s*", "", text).strip() or text


def case_order(case: str) -> list:
    return [int(t) if t.isdigit() else t.lower() for t in re.split(r"(\d+)", str(case or ""))]


def words(text) -> str:
    return " ".join(str(text or "").split())


def domains_of(text) -> list[str]:
    """An LPET's domains: its one `domain` string read with commas between domains, "Relationships,
    Psychological" two, each trimmed, an empty one or a repeat left out (trajfix, 11 November 2026)."""
    out: list[str] = []
    for part in str(text or "").split(","):
        word = words(part)[:TAG_MAX]
        if word and word.lower() not in (w.lower() for w in out):
            out.append(word)
    return out


def find_column(data: dict, name) -> dict | None:
    """A column by its id, `c1`, or its title, any case."""
    name = words(name)
    for c in data["columns"]:
        if c["id"] == name:
            return c
    for c in data["columns"]:
        if c["title"].lower() == name.lower():
            return c
    return None


def find_case(cases: list[str], name) -> str | None:
    """A participant by their label, `P1 - Wren`, or their pseudonym, `Wren`, any case."""
    name = words(name)
    for c in cases:
        if c == name or c.lower() == name.lower():
            return c
    for c in cases:
        if who(c).lower() == name.lower():
            return c
    return None


def find_lpet(lpets: list[dict], name) -> dict | None:
    """One of a participant's LPETs by its id, `G1`, or its title, any case."""
    name = words(name)
    for l in lpets:
        if l["id"] == name:
            return l
    for l in lpets:
        if words(l["title"]).lower() == name.lower():
            return l
    return None


def next_id(data: dict) -> str:
    taken = [int(c["id"][1:]) for c in data["columns"] if re.match(r"^c\d+$", c["id"])]
    return f"c{max(taken, default=0) + 1}"


def checked_title(data: dict, title, but: str | None = None) -> str:
    title = words(title)
    if not title:
        raise WorkbookError(i18n.t("server.trajectory_needs_title_nothing_changed"))
    if len(title) > TITLE_MAX:
        raise WorkbookError(i18n.t("server.make_title_characters_fewer_nothing", title_max=TITLE_MAX))
    if any(c["title"].lower() == title.lower() and c["id"] != but for c in data["columns"]):
        raise WorkbookError(i18n.t("server.trajectory_twice", name=title))
    return title


def palette_of(said) -> str | None:
    """A trajectory's colour by the name the file keeps, `good`, or the picker's, `Green`, any case, None for
    none. Anything else is refused."""
    name = words(said).lower()
    if name in ("", "none", "null", "default"):
        return None
    for key, plain in PALETTE.items():
        if name in (key, plain.lower()):
            return key
    raise WorkbookError(i18n.t("server.trajectory_colour_not_one", colour=words(said),
                               listed=", ".join(PALETTE.values())))


def tag_colour_of(said) -> int:
    """A tag's colour by its name in the participants' palette, `Brown`, or its place there from 0."""
    if isinstance(said, int) and not isinstance(said, bool) and 0 <= said < len(TAG_NAMES):
        return said
    name = words(said).lower()
    for n, plain in enumerate(TAG_NAMES):
        if name == plain.lower() or name == str(n):
            return n
    raise WorkbookError(i18n.t("server.trajectory_tag_colour_not_one", colour=words(said)))


def colour_for(data: dict, word: str) -> int:
    """The colour a tag or a domain has across the project, a new word given the first of the participants'
    palette no other word has, round again once all are taken."""
    for held, n in data["tags"].items():
        if held.lower() == word.lower():
            return n
    used = list(data["tags"].values())
    n = min(range(len(TAG_NAMES)), key=lambda i: (used.count(i), i))
    data["tags"][word] = n
    return n


def domain_colours(data: dict | None, walked, more=()) -> dict[str, int]:
    """Each domain's colour by its word in lower case, as the board draws it and the LPETs screen draws it too
    (lpetmarks, 12 November 2026): the project's own, kept in `tags`, and a domain no op has coloured yet, one of two
    set before they were read apart, the colour the next op would give it, worked out on a copy in the board's order,
    `walked`, each participant's LPETs' domains as they keep them, participants in case order and LPETs in the LPET
    table's, then `more`, so opening writes nothing and the two screens agree."""
    unsaid = {"tags": dict((data or {}).get("tags") or {})}
    out: dict[str, int] = {}
    for text in list(walked) + list(more):
        for word in domains_of(text):
            out[word.lower()] = colour_for(unsaid, word)
    return out


def order_of(data: dict, col: dict, cases: list[str]) -> list[str]:
    """A trajectory's participants in his order, those he has not ordered after them in case order."""
    mine = [c for c in cases if (data["placed"].get(c) or {}).get("column") == col["id"]]
    held = [c for c in col.get("order") or [] if c in mine]
    return held + sorted((c for c in mine if c not in held), key=case_order)


def at_of(op: dict, n: int, limit: int) -> int:
    at = op.get("at")
    if at is None:
        return limit
    try:
        return max(0, min(limit, int(at)))
    except (TypeError, ValueError):
        raise WorkbookError(i18n.t("server.operation_gives_place_which_number", n=n, at=at))


def apply(data: dict, cases: list[str], ops, lpets: dict | None = None, lpet_op=None,
          files: dict | None = None, read_file=None, set_person=None) -> list[str]:
    """Each operation run on `data` in order, in place, answering a line for each change. Refused as a
    whole, with `data` to be thrown away, when one is wrong:

    - `add`, `title`, and `at`, its place among the trajectories from 0, at the end without it
    - `rename`, `column` by its id or title, `title`
    - `move`, `column`, `at`
    - `remove`, `column`, its participants back among those not placed, what is kept on each kept
    - `describe`, `column`, `description`, its sentence, an empty one clearing it
    - `colour`, `column`, `colour`, one of PALETTE by either name, none clearing it
    - `icon`, `column`, `icon`, one of ICONS, none clearing it
    - `place`, `participant` by label or pseudonym, `column`, or none to take them out of every trajectory, and
      `at`, their place in it from 0, at the end without it
    - `order`, `participant`, `at`, their place in their trajectory
    - `note`, `participant`, `note`, his words on why, an empty one clearing it
    - `note_board`, `note`, his note for the whole screen, an empty one clearing it
    - `title`, `participant`, `title`, their own label, an empty one clearing it
    - `tags`, `participant`, `tags`, a list of words, all of their tags, an empty list clearing them
    - `tag_colour`, `tag`, `colour`, by its name in the participants' palette, for every participant
    - `picture`, `participant`, and `set`, one of FACES (one of FACES_BEFORE kept as its nearest), or `from`, an
      image file's path, or `data`, a data URL
      as the page sends one, or none of them to take the picture off
    - `hide` and `show`, `participant`, `lpet`, by its id or its title, on this screen alone
    - `state`, `quote`, `bold`, `domain` and `states_from_notes`, run on the participant's LPETs board by
      `lpet_op(case, op, n)`, which answers its lines: the board their LPETs come into LGETs from, or the one
      `board` names by its id or name (lpetmarks, 12 November 2026, for the LPETs screen's own board)

    `lpets` is each participant's LPETs, `[{"id", "title"}]`, for `hide` and `show`. A picture's bytes go into
    `files`, by the name they are kept under, `None` for one taken off, for `change` to write. `read_file` reads
    `from`, so a test or a hold can stand in for the disk.

    With `set_person` (pbiobuild, 11 November 2026) the label and the picture are the participant's own, kept in
    the project file for every screen (`participants.py`): `title` and `picture` are names for that set's change,
    `set_person(case, given)` running it and answering its lines, and this file keeps neither. Since demobuild (12
    November 2026) `tags` and `tag_colour` are names too, for their values in the project's Tags category and that
    value's colour (`demographics.py`)."""
    if not isinstance(ops, list):
        raise WorkbookError(i18n.t("server.trajectories_operations_list_nothing_changed"))
    lpets = lpets or {}
    files = {} if files is None else files
    said = []
    for n, op in enumerate(ops, start=1):
        kind = str((op or {}).get("op") or "") if isinstance(op, dict) else ""
        if kind not in OPS and kind not in LPET_OPS:
            raise WorkbookError(i18n.t("server.trajectory_not_an_op", n=n, op=kind or "empty"))

        def column(key="column") -> dict:
            found = find_column(data, op.get(key))
            if found is None:
                raise WorkbookError(i18n.t("server.trajectory_not_on_board", name=words(op.get(key)) or "with no name"))
            return found

        def participant() -> str:
            case = find_case(cases, op.get("participant"))
            if case is None:
                raise WorkbookError(i18n.t("server.trajectory_not_a_participant", name=words(op.get("participant")) or "Nobody"))
            return case

        if kind == "add":
            title = checked_title(data, op.get("title"))
            data["columns"].insert(at_of(op, n, len(data["columns"])), {"id": next_id(data), "title": title})
            said.append(f"{title} added.")
        elif kind == "rename":
            c = column()
            title = checked_title(data, op.get("title"), but=c["id"])
            if title != c["title"]:
                said.append(f"{c['title']} renamed {title}.")
                c["title"] = title
        elif kind == "move":
            c = column()
            data["columns"].remove(c)
            at = at_of(op, n, len(data["columns"]))
            data["columns"].insert(at, c)
            said.append(f"{c['title']} moved to place {at + 1}.")
        elif kind == "remove":
            c = column()
            data["columns"].remove(c)
            back = sorted((k for k, v in data["placed"].items() if v["column"] == c["id"]), key=case_order)
            for k in back:
                data["placed"][k]["column"] = None
            said.append(f"{c['title']} taken away" + (f", {', '.join(who(k) for k in back)} not placed." if back else "."))
        elif kind == "describe":
            c = column()
            text = words(op.get("description"))
            if len(text) > DESCRIPTION_MAX:
                raise WorkbookError(i18n.t("server.trajectory_sentence_long", most=DESCRIPTION_MAX))
            if text != (c.get("description") or ""):
                if text:
                    c["description"] = text
                else:
                    c.pop("description", None)
                said.append(f"{c['title']}'s sentence " + ("changed." if text else "cleared."))
        elif kind == "colour":
            c = column()
            colour = palette_of(op.get("colour"))
            if colour != c.get("colour"):
                if colour:
                    c["colour"] = colour
                else:
                    c.pop("colour", None)
                said.append(f"{c['title']} is {PALETTE[colour]} now." if colour else f"{c['title']} has no colour now.")
        elif kind == "icon":
            c = column()
            icon = words(op.get("icon")).lower()
            icon = None if icon in ("", "none", "null") else icon
            if icon is not None and icon not in ICONS:
                raise WorkbookError(i18n.t("server.trajectory_icon_not_one", icon=words(op.get("icon")), listed=", ".join(ICONS)))
            if icon != c.get("icon"):
                if icon:
                    c["icon"] = icon
                else:
                    c.pop("icon", None)
                said.append(f"{c['title']}'s icon is {icon} now." if icon else f"{c['title']} has no icon now.")
        elif kind == "note_board":
            note = str(op.get("note") or "").strip()
            if len(note) > NOTE_MAX:
                raise WorkbookError(i18n.t("server.make_note_characters_fewer_nothing", note_max=NOTE_MAX))
            if note != (data.get("note") or ""):
                if note:
                    data["note"] = note
                else:
                    data.pop("note", None)
                said.append("The board's note " + ("changed." if note else "cleared."))
        elif kind == "tag_colour" and set_person is not None:
            # a tag is a word of the participants' Tags category since demobuild: its colour is that value's
            said += set_person("", {"tag_colour": {"tag": op.get("tag"), "colour": op.get("colour")}})
        elif kind == "tag_colour":
            word = words(op.get("tag"))
            held = next((w for w in data["tags"] if w.lower() == word.lower()), None)
            if held is None:
                raise WorkbookError(i18n.t("server.trajectory_no_such_tag", tag=word or "with no words"))
            colour = tag_colour_of(op.get("colour"))
            if data["tags"][held] != colour:
                data["tags"][held] = colour
                said.append(f"{held} is {TAG_NAMES[colour]} now, wherever it is used.")
        elif kind in LPET_OPS:
            if lpet_op is None:
                raise WorkbookError(i18n.t("server.trajectory_not_an_op", n=n, op=kind))
            if kind == "states_from_notes" and op.get("participant") in (None, ""):
                for case in sorted(cases, key=case_order):
                    said += lpet_op(case, op, n)
                continue
            case = participant()
            lines = lpet_op(case, op, n)
            said += lines
            # each of an LPET's domains its own colour across the project, as a tag has
            for word in domains_of(op.get("domain")) if kind == "domain" else []:
                colour_for(data, word)
        else:
            case = participant()
            held = data["placed"].setdefault(case, {"column": None, "note": ""})
            name = who(case)
            if kind in ("place", "order"):
                if kind == "order":
                    to = find_column(data, held.get("column")) if held.get("column") else None
                    if to is None:
                        raise WorkbookError(i18n.t("server.trajectory_order_not_placed", name=name))
                else:
                    to = column() if op.get("column") not in (None, "") else None
                was = held["column"]
                for c in data["columns"]:
                    if c.get("order") and case in c["order"]:
                        c["order"] = [x for x in c["order"] if x != case] or None
                        if c["order"] is None:
                            c.pop("order")
                if to is None:
                    held["column"] = None
                    if was:
                        said.append(f"{name} not placed.")
                else:
                    others = [x for x in order_of(data, to, cases) if x != case]
                    at = at_of(op, n, len(others))
                    held["column"] = to["id"]
                    to["order"] = others[:at] + [case] + others[at:]
                    if was != to["id"]:
                        said.append(f"{name} placed in {to['title']}.")
                    elif op.get("at") is not None:
                        said.append(f"{name} moved to place {at + 1} in {to['title']}.")
            elif kind == "note":
                note = str(op.get("note") or "").strip()
                if len(note) > NOTE_MAX:
                    raise WorkbookError(i18n.t("server.make_note_characters_fewer_nothing", note_max=NOTE_MAX))
                if note != held["note"]:
                    held["note"] = note
                    said.append(f"The note on {name} " + ("changed." if note else "cleared."))
            elif kind == "title" and set_person is not None:
                said += set_person(case, {"label": op.get("title") if op.get("title") is not None else ""})
            elif kind == "tags" and set_person is not None:
                # their tags are their values in the Tags category since demobuild (12 November 2026)
                given = op.get("tags")
                if not isinstance(given, list) or any(not isinstance(t, str) for t in given):
                    raise WorkbookError(i18n.t("server.trajectory_tags_list"))
                said += set_person(case, {"values": {"Tags": given}})
            elif kind == "picture" and set_person is not None:
                given = ({"picture": f"set:{words(op.get('set')).lower()}"} if op.get("set") not in (None, "")
                         else {"data": op.get("data")} if op.get("data") not in (None, "")
                         else {"from": op.get("from")} if op.get("from") not in (None, "") else {"picture": ""})
                said += set_person(case, given)
            elif kind == "title":
                title = words(op.get("title"))
                if len(title) > LABEL_MAX:
                    raise WorkbookError(i18n.t("server.trajectory_label_long", most=LABEL_MAX))
                if title != (held.get("title") or ""):
                    if title:
                        held["title"] = title
                    else:
                        held.pop("title", None)
                    said.append(f"{name}'s label is {title} now." if title else f"{name}'s label cleared.")
            elif kind == "tags":
                given = op.get("tags")
                if not isinstance(given, list) or any(not isinstance(t, str) for t in given):
                    raise WorkbookError(i18n.t("server.trajectory_tags_list"))
                if any(len(words(t)) > TAG_MAX for t in given):
                    raise WorkbookError(i18n.t("server.trajectory_tag_long", most=TAG_MAX))
                tags = tags_kept(given)
                if len(tags) < len([t for t in given if words(t)]) and len(tags) == TAGS_MAX:
                    raise WorkbookError(i18n.t("server.trajectory_tags_many", most=TAGS_MAX))
                # a word another participant has keeps its spelling, so Town is one tag with one colour
                tags = [next((w for w in data["tags"] if w.lower() == t.lower()), t) for t in tags]
                if tags != (held.get("tags") or []):
                    if tags:
                        held["tags"] = tags
                    else:
                        held.pop("tags", None)
                    for t in tags:
                        colour_for(data, t)
                    said.append(f"{name}'s tags are {', '.join(tags)} now." if tags else f"{name}'s tags cleared.")
            elif kind == "picture":
                was = held.get("picture") or ""
                if op.get("set") not in (None, ""):
                    face = face_of(words(op.get("set")))
                    if not face:
                        raise WorkbookError(i18n.t("server.trajectory_no_such_face", face=words(op.get("set")),
                                                   first=FACES[0], last=FACES[-1]))
                    now = f"set:{face}"
                elif op.get("from") not in (None, "") or op.get("data") not in (None, ""):
                    if op.get("data") not in (None, ""):
                        raw = data_url(op.get("data"))
                    else:
                        raw = (read_file or read_picture)(str(op.get("from")))
                    body, ext = picture_bytes(raw)
                    now = own_name(name, ext, was)
                    files[now] = body
                else:
                    now = ""
                if now != was or now in files:
                    if was and not was.startswith("set:"):
                        files.setdefault(was, None)
                    if now:
                        held["picture"] = now
                    else:
                        held.pop("picture", None)
                    said.append(f"{name}'s picture changed." if now else f"{name}'s picture taken off.")
            else:
                found = find_lpet(lpets.get(case) or [], op.get("lpet"))
                if found is None:
                    raise WorkbookError(i18n.t("server.trajectory_no_such_lpet", name=name,
                                               lpet=words(op.get("lpet")) or "with no name"))
                hidden = list(held.get("hidden") or [])
                if kind == "hide" and found["id"] not in hidden:
                    held["hidden"] = hidden + [found["id"]]
                    said.append(f"{name}'s LPET '{found['title']}' hidden on Trajectories.")
                elif kind == "show" and found["id"] in hidden:
                    hidden.remove(found["id"])
                    if hidden:
                        held["hidden"] = hidden
                    else:
                        held.pop("hidden", None)
                    said.append(f"{name}'s LPET '{found['title']}' shown on Trajectories.")
            if not any(held.get(k) for k in ("column", "note", "title", "tags", "picture", "hidden")):
                data["placed"].pop(case, None)
    return said


# ------------------------------------------------------------------ the pictures

def own_name(name: str, ext: str, was: str) -> str:
    """The name a participant's own picture is kept under, their pseudonym, and a number after it when the
    picture it replaces has that name, so the old one can go to the archive first."""
    stem = re.sub(r"[^\w .-]", "", name).strip(" .") or "picture"
    first = f"{stem}.{ext}"
    return first if first != was else f"{stem}-2.{ext}"


def read_picture(path: str) -> bytes:
    file = Path(path).expanduser()
    try:
        if not file.is_file():
            raise OSError
        if file.stat().st_size > PICTURE_MAX:
            raise WorkbookError(i18n.t("server.trajectory_picture_large"))
        return file.read_bytes()
    except OSError:
        raise WorkbookError(i18n.t("server.trajectory_picture_not_there", path=path))


def data_url(text) -> bytes:
    found = re.fullmatch(r"data:image/[\w.+-]+;base64,([A-Za-z0-9+/=\s]+)", str(text or ""))
    if not found:
        raise WorkbookError(i18n.t("server.trajectory_picture_kind"))
    try:
        raw = base64.b64decode(found.group(1), validate=False)
    except ValueError:
        raise WorkbookError(i18n.t("server.trajectory_picture_kind"))
    if len(raw) > PICTURE_MAX:
        raise WorkbookError(i18n.t("server.trajectory_picture_large"))
    return raw


def picture_bytes(raw: bytes) -> tuple[bytes, str]:
    """A picture as it is kept: a PNG cut to a square at its middle and scaled to PICTURE_SIZE, or a small JPEG
    or SVG kept as it came. The window's Change picture... sends a PNG it has scaled already."""
    if raw[:8] == b"\x89PNG\r\n\x1a\n":
        try:
            w, h, rgba = png_read(raw)
        except (ValueError, zlib.error, struct.error, IndexError):
            raise WorkbookError(i18n.t("server.trajectory_picture_kind"))
        return png_write(*square(w, h, rgba, PICTURE_SIZE)), "png"
    if raw[:3] == b"\xff\xd8\xff":
        if len(raw) > KEPT_MAX["jpg"]:
            raise WorkbookError(i18n.t("server.trajectory_picture_jpeg_large"))
        return raw, "jpg"
    head = raw[:600].decode("utf-8", "ignore").lower()
    if "<svg" in head:
        if len(raw) > KEPT_MAX["svg"] or "<script" in raw.decode("utf-8", "ignore").lower():
            raise WorkbookError(i18n.t("server.trajectory_picture_kind"))
        return raw, "svg"
    raise WorkbookError(i18n.t("server.trajectory_picture_kind"))


def png_read(raw: bytes) -> tuple[int, int, bytearray]:
    """A PNG of 8 bits a channel, not interlaced, as its width, height and RGBA bytes."""
    at, idat, palette, trns = 8, bytearray(), None, None
    w = h = depth = kind = interlace = None
    while at < len(raw):
        size, tag = struct.unpack(">I4s", raw[at:at + 8])
        body = raw[at + 8:at + 8 + size]
        at += 12 + size
        if tag == b"IHDR":
            w, h, depth, kind, _c, _f, interlace = struct.unpack(">IIBBBBB", body)
        elif tag == b"PLTE":
            palette = body
        elif tag == b"tRNS":
            trns = body
        elif tag == b"IDAT":
            idat += body
        elif tag == b"IEND":
            break
    if not w or not h or depth != 8 or interlace or kind not in (0, 2, 3, 4, 6) or max(w, h) > PICTURE_SIDE_MAX:
        if w and h and max(w, h) > PICTURE_SIDE_MAX:
            raise WorkbookError(i18n.t("server.trajectory_picture_wide", most=PICTURE_SIDE_MAX))
        raise ValueError("unread")
    channels = {0: 1, 2: 3, 3: 1, 4: 2, 6: 4}[kind]
    stride = w * channels
    data = zlib.decompress(bytes(idat))
    out = bytearray(stride * h)
    prev = bytearray(stride)
    pos = 0
    for y in range(h):
        f = data[pos]
        line = bytearray(data[pos + 1:pos + 1 + stride])
        pos += 1 + stride
        if f == 1:
            for i in range(channels, stride):
                line[i] = (line[i] + line[i - channels]) & 255
        elif f == 2:
            for i in range(stride):
                line[i] = (line[i] + prev[i]) & 255
        elif f == 3:
            for i in range(stride):
                left = line[i - channels] if i >= channels else 0
                line[i] = (line[i] + ((left + prev[i]) >> 1)) & 255
        elif f == 4:
            for i in range(stride):
                a = line[i - channels] if i >= channels else 0
                b = prev[i]
                c = prev[i - channels] if i >= channels else 0
                p = a + b - c
                pa, pb, pc = abs(p - a), abs(p - b), abs(p - c)
                line[i] = (line[i] + (a if pa <= pb and pa <= pc else b if pb <= pc else c)) & 255
        out[y * stride:(y + 1) * stride] = line
        prev = line
    rgba = bytearray(w * h * 4)
    for i in range(w * h):
        if kind == 6:
            rgba[i * 4:i * 4 + 4] = out[i * 4:i * 4 + 4]
        elif kind == 2:
            rgba[i * 4:i * 4 + 4] = out[i * 3:i * 3 + 3] + b"\xff"
        elif kind == 0:
            g = out[i]
            rgba[i * 4:i * 4 + 4] = bytes((g, g, g, 255))
        elif kind == 4:
            g = out[i * 2]
            rgba[i * 4:i * 4 + 4] = bytes((g, g, g, out[i * 2 + 1]))
        else:
            n = out[i]
            if palette is None or n * 3 + 3 > len(palette):
                raise ValueError("palette")
            alpha = trns[n] if trns and n < len(trns) else 255
            rgba[i * 4:i * 4 + 4] = palette[n * 3:n * 3 + 3] + bytes((alpha,))
    return w, h, rgba


def square(w: int, h: int, rgba: bytearray, size: int) -> tuple[int, int, bytearray]:
    """The picture's middle square, each pixel of the result the average of the pixels it covers, no larger
    than it came."""
    side = min(w, h)
    x0, y0 = (w - side) // 2, (h - side) // 2
    to = min(size, side)
    out = bytearray(to * to * 4)
    for ty in range(to):
        sy0, sy1 = y0 + ty * side // to, y0 + max((ty + 1) * side // to, ty * side // to + 1)
        for tx in range(to):
            sx0, sx1 = x0 + tx * side // to, x0 + max((tx + 1) * side // to, tx * side // to + 1)
            sums = [0, 0, 0, 0]
            for sy in range(sy0, sy1):
                base = (sy * w) * 4
                for sx in range(sx0, sx1):
                    i = base + sx * 4
                    sums[0] += rgba[i]
                    sums[1] += rgba[i + 1]
                    sums[2] += rgba[i + 2]
                    sums[3] += rgba[i + 3]
            count = (sy1 - sy0) * (sx1 - sx0)
            j = (ty * to + tx) * 4
            out[j:j + 4] = bytes(s // count for s in sums)
    return to, to, out


def png_write(w: int, h: int, rgba: bytearray) -> bytes:
    def chunk(tag: bytes, body: bytes) -> bytes:
        return struct.pack(">I", len(body)) + tag + body + struct.pack(">I", zlib.crc32(tag + body) & 0xffffffff)
    lines = b"".join(b"\x00" + bytes(rgba[y * w * 4:(y + 1) * w * 4]) for y in range(h))
    return (b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", w, h, 8, 6, 0, 0, 0))
            + chunk(b"IDAT", zlib.compress(lines, 9)) + chunk(b"IEND", b""))


def picture_files(root: Path, files: dict, when: str, folder: Path | None = None) -> None:
    """The pictures a change made, written into the project's pictures folder, Trajectories' own or with `folder`
    another (the participants' own, `participants.pictures_of`), and each one it replaced or took off moved to the
    folder's `_Archive` with the time in its name, never deleted."""
    folder = pictures_of(root) if folder is None else Path(folder)
    stamp = re.sub(r"[^0-9]", "", str(when))[:14] or "0"
    for name, body in files.items():
        if body is not None:
            continue
        old = folder / name
        if old.is_file():
            keep = folder / "_Archive"
            keep.mkdir(parents=True, exist_ok=True)
            os.replace(old, keep / f"{Path(name).stem} {stamp}{Path(name).suffix}")
    for name, body in files.items():
        if body is None:
            continue
        folder.mkdir(parents=True, exist_ok=True)
        old = folder / name
        if old.is_file():
            keep = folder / "_Archive"
            keep.mkdir(parents=True, exist_ok=True)
            os.replace(old, keep / f"{Path(name).stem} {stamp}{Path(name).suffix}")
        tmp = folder / (name + ".tmp")
        tmp.write_bytes(body)
        os.replace(tmp, old)


# ------------------------------------------------------------------ the board

def board(data: dict | None, people: list[dict]) -> dict:
    """The board as the screen draws it and an agent reads it: each trajectory with its participants in his
    order, those not placed, and each participant's card, `case`, `who`, `colour`, `lpets` (their LPETs'
    titles), `column`, `note`, `title`, `tags` (each `{"word", "colour"}`), `picture` and `hidden`, and the
    board's own `note`. `people` is
    each participant of the project with their colour and LPETs, and `rows`, each LPET with its cells, to which
    the board adds `shown` and `domains`, each of its domains as `{"word", "colour"}` (`domains_of`)."""
    data = normal(data) if data else {"columns": [], "placed": {}, "tags": {}, "history": [], "updated": None}
    placed = data.get("placed") or {}
    colours = {w.lower(): n for w, n in (data.get("tags") or {}).items()}
    people = sorted(people, key=lambda x: case_order(x["case"]))
    # each domain's colour, one no op has coloured yet worked out in the board's order (`domain_colours`)
    hues = domain_colours(data, [r.get("domain") for p in people for r in p.get("rows") or []])
    cards = []
    for p in people:
        held = placed.get(p["case"]) or {}
        hidden = set(held.get("hidden") or [])
        rows = [dict(r, shown=r["id"] not in hidden,
                     domains=[{"word": w, "colour": hues[w.lower()]} for w in domains_of(r.get("domain"))])
                for r in p.get("rows") or []]
        # the label and the picture the participant's own (pbiobuild), as the caller reads them, else this file's
        own = p.get("person") if isinstance(p.get("person"), dict) else None
        cards.append(dict({k: v for k, v in p.items() if k != "person"}, who=who(p["case"]), column=held.get("column"),
                          note=held.get("note") or "",
                          title=(own.get("label") or "") if own is not None else held.get("title") or "",
                          tags=[{"word": t, "colour": colours.get(t.lower(), 0)} for t in held.get("tags") or []],
                          picture=(own.get("picture") or "") if own is not None else held.get("picture") or "",
                          hidden=sorted(hidden), rows=rows))
    cases = [x["case"] for x in cards]
    return {"columns": [dict({k: v for k, v in c.items() if k != "order"}, participants=order_of(data, c, cases))
                        for c in data["columns"]],
            "unplaced": [x["case"] for x in cards if not x["column"]], "note": data.get("note") or "",
            "participants": cards, "tags": dict(data.get("tags") or {}), "updated": data.get("updated"),
            "palette": dict(PALETTE), "icons": list(ICONS), "faces": list(FACES),
            "history": list(data.get("history") or [])[-20:]}


def change(root: Path, cases: list[str], ops, when: str, dry_run: bool = False, note: str = "",
           tool: str = "", lpets: dict | None = None, lpet_op=None, commit=None, set_person=None) -> dict:
    """The operations applied to the project's board and written, with a History line, unless `dry_run`
    or nothing changed. `lpet_op` runs an operation on a participant's LPETs board in memory, and `commit`
    writes those boards, called only once every operation has passed. Answers `changes`, a line each,
    `dry_run`, and the file's state after, `data`."""
    held = load(root)
    data = json.loads(json.dumps(held)) if held else fresh(when)
    data.setdefault("tags", {})
    files: dict = {}
    said = apply(data, cases, ops, lpets=lpets, lpet_op=lpet_op, files=files, set_person=set_person)
    if said and not dry_run:
        if commit is not None:
            commit()
        if files:
            picture_files(root, files, when)
        data["updated"] = when
        data["history"] = (data.get("history") or []) + [
            dict({"when": when, "changes": said}, **({"note": note} if note else {}), **({"tool": tool} if tool else {}))]
        data["history"] = data["history"][-HISTORY_MAX:]
        write(root, data)
    return {"changes": said, "dry_run": bool(dry_run), "data": data}
