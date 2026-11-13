#!/usr/bin/env python3
"""Build the longitudinal IPA demo: "First year on an allotment", three invented participants interviewed at three
timepoints, as a finished longitudinal project of the app's own model (lipabuild, 13 November 2026).

Adam, 12 November 2026: a third demo beside the IPA and thematic analysis demos, grown from the allotment study of
the website's clip (`packaging/motion/clips/make_lipa.py`), its analysis to the standard of the IPA demo, which he
read and approved that day (lipawrite). Hollis, Nell and Arlo are each interviewed before the season (T1), at
midsummer (T2) and after the harvest (T3), each interview recorded in Gemini's voices (lipavoices). Nobody in it is
real. It lives inside the demo's folder, as the thematic analysis demo does:

    demo/lipa/idiograph-project.json            the project: its name, question, timepoints, the participants' own
                                                labels, pictures, pen portraits and values, and its demographics
    demo/lipa/source/<Name> - T1.csv            each interview, Name, Timestamp and Transcript, nine of them
    demo/lipa/source/analysis.json              the analysis: statements, notes and key quotes on every turn, each
                                                timepoint's PETs board, each participant's LPETs with their rows,
                                                the LGETs and the Trajectories board
    demo/lipa/<Name>/<Name> - EN & ES.xlsx      the workbook, a sheet a timepoint (T1, T2, T3), built from those
    demo/lipa/<Name>/Working/                   its progress file, a PETs file a timepoint and its LPETs file
    demo/lipa/idiograph-lgets.json              the LGETs, and idiograph-trajectories.json the Trajectories board
    demo/lipa/pristine/                         the copy Reset demo restores from
    packaging/recording/<Name>-T1-<hash>.m4a    the recordings, gitignored, assets of the release demo-recordings-1

Everything goes through the functions the app itself calls, as `make_demo` builds the other two: each participant's
workbook through `create_from_source` from a raw source of three sheets, the T2 and T3 sheets placed at their
timepoints in the progress file (`rounds.tag_sheets`), every turn decided through the turn screen's own save, each
timepoint's Statements complete, its PETs board laid out, arranged as a grid (`themes.arrange_board`, so it reads
top left to bottom right and fits a screen, as Auto-arrange leaves one), made Current and marked complete inside
`themes.scoped`, the LPETs inside `gets.lpets` from the PETs and sub-PETs each LPET holds, a card no LPET holds set
aside, each row's state, key quote and bold through `gets.row_op`, the LGETs inside `gets.lgets` the same way, and
the Trajectories board through `trajectories.apply`. The clock is held at times of its own, so the same sources
build the same files.

    .venv/bin/python apps/idiograph/make_demo.py --lipa [--force]
    .venv/bin/python apps/idiograph/make_demo_lipa.py --recordings <clips folder>

`--recordings` joins each interview's clips, one WAV a turn in `<clips>/<Name> - T1/NNN.wav` (lipavoices kept them
in `.verify/keep/lipa-voices-12Nov26/`), writes each turn's Timestamp in the CSV from their lengths and the half
second between them, encodes the join as the other demos' are (HE-AAC at 24 kbps) into packaging/recording, named by
the CSV's hash, and writes the manifest again. Then build the demo again, since the timecodes moved.
"""
from __future__ import annotations

import argparse
import contextlib
import datetime as dt
import json
import os
import shutil
import sys
import tempfile
import wave
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
import boot  # noqa: E402

boot.setup()

import openpyxl  # noqa: E402

import audio as audio_mod  # noqa: E402
import gets as gets_mod  # noqa: E402
import make_demo as md  # noqa: E402
import rounds as rounds_mod  # noqa: E402
import themes as themes_mod  # noqa: E402
import trajectories as traj_mod  # noqa: E402
import workbook as wb_mod  # noqa: E402

DemoError = md.DemoError

# the demo's folder inside the demo's, its participants in the order the study takes them, and its timepoints,
# each a sheet of the participant's workbook named by its label
FOLDER = "lipa"
CASES = ("Hollis", "Nell", "Arlo")
TIMEPOINTS = ("T1", "T2", "T3")
ANALYSIS = "analysis.json"
PROJECT_FILE = md.PROJECT_FILE
EN_ES = md.EN_ES
LGETS_FILE = gets_mod.LGETS_FILE
TRAJ_FILE = traj_mod.path_of(Path(".")).name
# the files at the demo's root the pristine copy holds, beside its participants
ROOT_FILES = (LGETS_FILE, TRAJ_FILE)
ROUND_MINUTES = md.ROUND_MINUTES

# When each part of the work was done: each interview's statements in the week after it (T1 in March, T2 in July,
# T3 in November 2026), its PETs board the day after, each participant's LPETs after their T3 board, then the LGETs
# and the Trajectories board. Held so the same sources build the same files.
TP_DAYS = {"T1": "2026-03-16", "T2": "2026-07-13", "T3": "2026-11-02"}


def at(day: str, hour: int, minute: int = 0) -> str:
    return f"{day}T{hour:02d}:{minute:02d}:00+00:00"


def day_after(day: str, n: int) -> str:
    return (dt.date.fromisoformat(day) + dt.timedelta(days=n)).isoformat()


def times(name: str, tp: str) -> dict:
    """The times a participant's timepoint was worked on: its rounds closing on `work`, Statements complete, and
    its PETs board made, made Current and marked complete."""
    k = CASES.index(name)
    work = day_after(TP_DAYS[tp], 2 * k)
    board = day_after(work, 1)
    return {"work": work, "complete": at(work, 17, 30), "made": at(board, 10), "chosen": at(board, 12),
            "pets_complete": at(board, 12, 30)}


LPETS_DAY = "2026-11-09"
LGETS_AT = at("2026-11-10", 11)
TRAJ_AT = at("2026-11-11", 15)
BUILT = at("2026-11-11", 17, 30)


# ------------------------------------------------------------------ the sources

def lipa_dir(demo: Path | None = None) -> Path:
    """The longitudinal demo's folder, inside the demo's."""
    return (Path(demo) if demo is not None else md.DEMO) / FOLDER


def interview(name: str, tp: str, demo: Path | None = None) -> Path:
    """A participant's interview at a timepoint, its CSV among the demo's sources."""
    return lipa_dir(demo) / "source" / f"{name} - {tp}.csv"


def read_analysis(demo: Path | None = None) -> dict:
    path = lipa_dir(demo) / "source" / ANALYSIS
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        raise DemoError(f"{path.name} could not be read: {exc}")
    if not isinstance(data, dict) or not isinstance(data.get("cases"), dict):
        raise DemoError(f"{path.name} has no participants in it.")
    return data


def raw_source(name: str, out: Path, demo: Path | None = None) -> Path:
    """The participant's three interviews as a raw source workbook, a sheet a timepoint named by its label, as
    New project and Add transcripts write one, each speaker as the CSV names them and the times as times."""
    book = openpyxl.Workbook()
    book.remove(book.active)
    for tp in TIMEPOINTS:
        ws = book.create_sheet(tp)
        ws.append(["Name", "Timestamp", "Transcript"])
        for r, row in enumerate(md.read_turns(interview(name, tp, demo)), start=2):
            ws.cell(r, 1, row["Name"].strip())
            cell = ws.cell(r, 2, md.as_time(row["Timestamp"]))
            cell.number_format = "h:mm:ss"
            ws.cell(r, 3, row["Transcript"])
    book.save(out)
    book.close()
    return out


# ------------------------------------------------------------------ the recordings

def recording(name: str, tp: str, demo: Path | None = None) -> Path:
    """Where a participant's recording at a timepoint sits in the demo, where the player finds it."""
    return lipa_dir(demo) / name / "Source" / tp / "Source" / f"{name}-{tp}.m4a"


def committed(name: str, tp: str, demo: Path | None = None, folder: Path | None = None) -> Path:
    """The recording made for the interview as it stands, in packaging/recording unless `folder` says, there or
    not."""
    return Path(folder or md.RECORDINGS) / audio_mod.demo_recording_name(name, tp, interview(name, tp, demo))


def interviews() -> list[tuple[str, str]]:
    return [(name, tp) for name in CASES for tp in TIMEPOINTS]


def recording_names(demo: Path | None = None) -> list[str]:
    """The names of the nine recordings for the interviews as they stand."""
    return [committed(name, tp, demo).name for name, tp in interviews()]


def build_recording(name: str, tp: str, clips: list[Path], folder: Path | None = None,
                    demo: Path | None = None) -> dict:
    """One interview's turn clips measured, each turn's Timestamp written from them and the half second between,
    joined and encoded as the other demos' recordings are, into the recording named by the CSV as then written.
    An older recording of the same interview is taken away. Answers the turns, length, size and path."""
    path = interview(name, tp, demo)
    rows = md.read_turns(path)
    if len(clips) != len(rows):
        raise DemoError(f"{name} {tp} has {len(rows)} turns and there are {len(clips)} clips.")
    shape = None
    for clip in clips:
        with wave.open(str(clip), "rb") as fh:
            got = (fh.getnchannels(), fh.getsampwidth(), fh.getframerate())
        if shape is not None and got != shape:
            raise DemoError(f"{clip.name} of {name} {tp} is not of the same rate and shape as the first.")
        shape = got
    starts, now = [], 0.0
    for clip in clips:
        starts.append(now)
        now += md.clip_seconds(clip) + md.GAP_SECONDS
    moved = [i for i, row in enumerate(rows) if row["Timestamp"] != md.hhmmss(starts[i])]
    for row, start in zip(rows, starts):
        row["Timestamp"] = md.hhmmss(start)
    if moved:
        md.write_turns(rows, path)
    target = committed(name, tp, demo, folder)
    with tempfile.TemporaryDirectory(prefix="demo-lipa-audio-") as tmp:
        joined = Path(tmp) / "joined.wav"
        md.join_clips(clips, md.GAP_SECONDS, joined)
        length = md.clip_seconds(joined)
        md.to_m4a(joined, target)
    for old in target.parent.glob(f"{name}-{tp}-*.m4a"):
        if old != target:
            old.unlink()
    return {"turns": len(rows), "seconds": length, "bytes": target.stat().st_size, "path": target, "moved": len(moved)}


def build_recordings(clips: Path, demo: Path | None = None) -> list[dict]:
    """All nine from a folder of clips, `<clips>/<Name> - T1/NNN.wav`, then the manifest written again."""
    out = []
    for name, tp in interviews():
        folder = Path(clips) / f"{name} - {tp}"
        wavs = sorted(folder.glob("[0-9][0-9][0-9].wav"))
        made = build_recording(name, tp, wavs, demo=demo)
        print(f"  {name} {tp}: {md.hhmmss(made['seconds'])}, {made['bytes'] / 1e6:.2f} MB, {made['path'].name}, "
              f"{made['moved']} of {made['turns']} timecodes moved")
        out.append(made)
    md.write_manifest()
    return out


def place_recording(name: str, tp: str, demo: Path | None = None, folder: Path | None = None) -> Path | None:
    """A recording made for the interview as it stands copied into its place, as `make_demo.place_recording` does,
    or None when there is none."""
    source = committed(name, tp, demo, folder)
    if not source.is_file():
        return None
    target = recording(name, tp, demo)
    target.parent.mkdir(parents=True, exist_ok=True)
    tmp = target.with_name(f".{target.stem}.copying{target.suffix}")
    shutil.copyfile(source, tmp)
    os.replace(tmp, target)
    return target


# ------------------------------------------------------------------ a participant

def annotate(workbook: Path, name: str, plan: dict) -> dict:
    """Every participant turn of each timepoint's sheet decided through the turn screen's own save, its statements
    with their key quotes, its note, as `make_demo.annotate` does a sheet. Answers the progress file, not written."""
    case = wb_mod.read_case(workbook)
    every = [row for sheet in case["sheets"] for row in sheet["rows"]]
    sheet_of = {id(row): sheet["name"] for sheet in case["sheets"] for row in sheet["rows"]}
    others = sorted({row["name"] for row in every} - {name})
    interviewer = others[0] if others else ""
    progress = rounds_mod.load_progress(workbook)
    last = None
    for tp in TIMEPOINTS:
        places = [i for i, row in enumerate(every) if row["name"] == name and sheet_of[id(row)] == tp]
        given = plan["timepoints"][tp]["turns"]
        if len(places) != len(given):
            raise DemoError(f"{name} has {len(places)} turns at {tp} and the analysis gives {len(given)}.")
        for place, item in zip(places, given):
            row = every[place]
            if not row["text"].startswith(str(item.get("at") or "\0")):
                raise DemoError(f"{name}'s turn at {tp} row {row['row']} does not start with {item.get('at')!r}.")
            key = rounds_mod.row_key(tp, row["row"])
            if item.get("empty"):
                progress["rows"][key] = rounds_mod.REVIEWED_EMPTY
                continue
            statements, quotes = list(item.get("es") or []), list(item.get("kq") or [])
            if len(quotes) > len(statements):
                raise DemoError(f"{name}'s turn at {tp} row {row['row']} has a key quote with no statement of its own.")
            pairs = [{"es": s, "kq": md.quote_of(every, place, quotes[k], name, interviewer) if k < len(quotes) and quotes[k] else ""}
                     for k, s in enumerate(statements)]
            wb_mod.save_turn(workbook, tp, row["row"], None, item.get("en", ""), None, pairs=pairs)
            progress["rows"][key] = rounds_mod.HAS_CONTENT
            last = {"sheet": tp, "row": row["row"]}
    progress["last"] = last
    return progress


def record_work(workbook: Path, name: str, progress: dict) -> dict:
    """The rounds closed, each on the day its timepoint was worked on, an hour after the one before, and each
    timepoint's Statements complete, T1's as `complete` and the later ones in `complete_timepoints`, written as the
    app writes the file."""
    case = wb_mod.read_case(workbook)
    who = sorted({row["name"] for sheet in case["sheets"] for row in sheet["rows"]} - {name})[0]
    made = rounds_mod.build_rounds(case["sheets"], ROUND_MINUTES, who)
    placed = rounds_mod.sheet_timepoints(progress)
    count: dict[str, int] = {}
    for rnd in made:
        sheets = [s for s in (rnd.get("sheets") or [rnd.get("sheet")]) if s] if isinstance(rnd, dict) else []
        tp = TIMEPOINTS[max([placed.get(str(s), 1) for s in sheets] or [1]) - 1]
        n = count[tp] = count.get(tp, 0) + 1
        day = times(name, tp)["work"]
        closed = at(day, 9 + n)
        progress["rounds"][str(rnd["number"])] = {"seconds": 1500 + 60 * (rnd["number"] % 7), "completed": closed}
        progress["days"].setdefault(day, {"rounds": 0})["rounds"] += 1
    states = rounds_mod.row_states(case["sheets"], progress, who)
    if not all(rounds_mod.round_done(rnd, states) for rnd in made):
        raise DemoError(f"Not every turn of {name}'s is decided, so the rounds cannot close.")
    progress["complete"] = {"at": times(name, "T1")["complete"]}
    progress[rounds_mod.TP_COMPLETE] = {str(n): {"at": times(name, tp)["complete"]}
                                        for n, tp in enumerate(TIMEPOINTS, start=1) if n > 1}
    rounds_mod.save_progress(workbook, progress)
    return progress


def square(board: dict, height=None) -> dict:
    """The board's places as Auto-arrange to a grid leaves them, its PETs in rows across, each label's cards in a
    compact grid in the order they read (boardgrid, Adam 12 November 2026: a board read whole, never a long
    column), everything else the board holds kept."""
    laid = themes_mod.arrange_board(board, "grid", height)
    out = dict(board)
    out["cards"] = {k: dict(board["cards"].get(k) or {}, **{f: c[f] for f in ("x", "y") if f in c})
                    for k, c in laid["cards"].items()}
    spots = {g["id"]: g for g in laid["groups"]}
    out["groups"] = [dict(g, **{f: spots[g["id"]][f] for f in ("x", "y") if g["id"] in spots and f in spots[g["id"]]})
                     for g in board["groups"]]
    return out


def make_board(workbook: Path, name: str, tp: str, plan: dict) -> dict:
    """A timepoint's PETs board, as `make_demo.make_board` makes the IPA demo's, then arranged as a grid, inside
    that timepoint's scope: every statement of the timepoint named once, each theme's description and picked
    key quote, saved, made Current and marked complete."""
    import themes_ai

    when = times(name, tp)
    with themes_mod.scoped(TIMEPOINTS.index(tp) + 1):
        read = themes_mod.read_cards(workbook)
        keys: dict[str, str] = {}
        for card in read["cards"]:
            if card["text"] in keys:
                raise DemoError(f"Two of {name}'s statements at {tp} read {card['text']!r}.")
            keys[card["text"]] = card["key"]
        named: list[str] = []

        def key(text: str) -> str:
            if text not in keys:
                raise DemoError(f"No statement of {name}'s at {tp} reads {text!r}.")
            named.append(keys[text])
            return keys[text]

        groups = []
        for pet in plan["pets"]:
            own = [key(t) for t in pet.get("statements") or []]
            subs = [{"label": s["title"], "description": s.get("description") or "",
                     "members": [key(t) for t in s["statements"]]} for s in pet.get("subs") or []]
            groups.append({"label": pet["title"], "description": pet.get("description") or "", "members": own,
                           "groups": subs})
        unplaced = [key(t) for t in plan.get("unplaced") or []]
        if len(named) != len(set(named)) or set(named) != set(keys.values()):
            raise DemoError(f"Every statement of {name}'s at {tp} is named once on the board, and some are not.")
        pile = themes_mod.blank_version(read["cards"], when["made"])["cards"]
        cards = [dict(c, x=pile[c["key"]]["x"], y=pile[c["key"]]["y"]) for c in read["cards"]]
        laid = themes_ai.lay_out(groups, cards, [])
        by_label = {g["label"]: g for g in laid["groups"]}
        if len(by_label) != len(laid["groups"]):
            raise DemoError(f"Two of {name}'s themes at {tp} share a title.")
        by_id = {g["id"]: g for g in laid["groups"]}
        picks = {}
        for pet in plan["pets"]:
            for theme in [pet] + list(pet.get("subs") or []):
                if theme.get("note"):
                    by_label[theme["title"]]["note"] = theme["note"]
                if theme.get("description"):
                    by_label[theme["title"]][themes_mod.DESCRIPTION] = theme["description"]
            gid = by_label[pet["title"]]["id"]
            rows = {themes_mod.row_key(*themes_mod.split_card_key(k)[:2]) for k in themes_mod.cards_under(by_id, gid)}
            chosen = []
            for words in pet.get("picks") or []:
                found = [q["key"] for r in sorted(rows) for q in (read["quotes"].get(r) or {}).get("quotes", [])
                         if q["text"].strip('"') == words]
                if len(found) != 1:
                    raise DemoError(f"The pick {words!r} is not one key quote under {pet['title']!r}.")
                chosen.append(found[0])
            if chosen:
                picks[gid] = chosen
        board = dict(laid, id=themes_mod.FIRST_VERSION, name=themes_mod.FIRST_NAME, note="",
                     created=when["made"], updated=when["made"], picks=picks)
        board = square(board)
        with md.clock(when["made"]):
            themes_mod.save(workbook, board, name)
        with md.clock(when["chosen"]):
            themes_mod.version_op(workbook, "choose", {"id": themes_mod.FIRST_VERSION}, name)
        with md.clock(when["pets_complete"]):
            themes_mod.version_op(workbook, "complete", {}, name)
    return {"statements": len(keys), "pets": len(plan["pets"]),
            "subs": sum(len(p.get("subs") or []) for p in plan["pets"]), "unplaced": len(unplaced)}


def build_case(name: str, into: Path, plan: dict, demo: Path | None = None) -> dict:
    """One participant built into `<into>/<name>/`, a folder that must not be there yet: the workbook of three
    sheets, T2's and T3's placed at their timepoints, every turn decided, the rounds closed and each timepoint's
    Statements complete, and a PETs board a timepoint. Answers the workbook and the counts by timepoint."""
    folder = Path(into) / name
    if folder.exists():
        raise DemoError(f"{folder} is there already, so nothing was built into it.")
    folder.mkdir(parents=True)
    workbook = folder / f"{name}{EN_ES}"
    with tempfile.TemporaryDirectory(prefix="demo-lipa-source-") as tmp:
        raw = raw_source(name, Path(tmp) / f"{name} - interviews.xlsx", demo)
        wb_mod.create_from_source(raw, workbook)
    for n, tp in enumerate(TIMEPOINTS, start=1):
        if n > 1:
            rounds_mod.tag_sheets(workbook, [tp], n)
    progress = annotate(workbook, name, plan)
    record_work(workbook, name, progress)
    counts = {tp: make_board(workbook, name, tp, plan["timepoints"][tp]["board"]) for tp in TIMEPOINTS}
    return {"workbook": workbook, "counts": counts}


# ------------------------------------------------------------------ LPETs, LGETs and Trajectories

def labels_of(project: dict) -> dict:
    """Each timepoint's key, `T1`, to its label and its description, as `gets.row_op` takes them."""
    return {f"T{n}": [t["label"], t.get("description") or ""] for n, t in enumerate(project["timepoints"], start=1)}


def lpets_books(workbook: Path, project: dict) -> list[dict]:
    """The participant's timepoints as the LPETs canvas takes them in (`idiograph_routes.lpets_books`)."""
    return [{"case": f"T{n}", "workbook": Path(workbook), "timepoint": n, "cite": t["label"], "missing": False,
             "pets_complete": None} for n, t in enumerate(project["timepoints"], start=1)]


def utime_all(paths, when: str) -> None:
    stamp = int(dt.datetime.fromisoformat(when).timestamp()) * 1_000_000_000
    for path in paths:
        if Path(path).exists():
            os.utime(path, ns=(stamp, stamp))


def case_files(workbook: Path) -> list[Path]:
    folder = Path(workbook).parent / "Working"
    return [Path(workbook)] + sorted(folder.glob(f"{Path(workbook).stem}.*"))


def build_lpets(root: Path, name: str, plan: dict, project: dict) -> dict:
    """A participant's LPETs board, inside `gets.lpets`: each timepoint taken in from its board marked complete,
    each LPET made of the PETs and sub-PETs its cards name, with its description and domain, every card no LPET
    holds set aside, laid out and arranged as a grid, then each LPET's row at each timepoint: its state, its key
    quote ticked and the words in bold, through `gets.row_op` as Trajectories and the LPET table set them. Saved,
    made Current and marked complete. Answers the counts."""
    import themes_ai

    workbook = Path(root) / name / f"{name}{EN_ES}"
    labels = labels_of(project)
    names = {k: v[0] for k, v in labels.items()}
    books = lpets_books(workbook, project)
    inside = [b["case"] for b in books]
    k = CASES.index(name)
    made, chosen, complete = at(LPETS_DAY, 10 + 2 * k), at(LPETS_DAY, 11 + 2 * k), at(LPETS_DAY, 11 + 2 * k, 30)
    utime_all(case_files(workbook), made)
    with gets_mod.lpets(workbook, names):
        with md.clock(made):
            data, _cases, _disk, _taken = gets_mod.assemble(root, books, themes_mod.now_iso())
        ids: dict[tuple[str, str, str], str] = {}
        for tp, rec in data["cases"].items():
            if rec.get("state") != "in" or not rec.get("complete"):
                raise DemoError(f"{name}'s PETs at {tp} are not in from a board marked complete.")
            for pet in rec["pets"]:
                kind = "PET" if pet.get("parent") is None else "sub-PET"
                ids[(tp, kind, pet["title"])] = gets_mod.card_of(tp, "group", pet["id"])
        named: list[str] = []

        def card(c: dict) -> str:
            found = ids.get((c["timepoint"], c["kind"], c["title"]))
            if not found:
                raise DemoError(f"{name} has no {c['kind']} at {c['timepoint']} called {c['title']!r}.")
            named.append(found)
            return found

        lpets = plan["lpets"]["lpets"]
        groups = [{"label": l["title"], "description": l.get("description") or "",
                   "members": [card(c) for c in l["cards"]], "groups": []} for l in lpets]
        if len(named) != len(set(named)):
            raise DemoError(f"A card of {name}'s is in two LPETs.")
        aside = [key for key in ids.values() if key not in named]
        pile = data["boards"][0]["cards"]
        said = {gets_mod.card_of(tp, "group", pet["id"]): gets_mod.layout_text(pet["title"], themes_mod.description_of(pet))
                for tp, rec in data["cases"].items() for pet in rec["pets"]}
        cards = [{"key": key, "text": said[key], "x": pile[key]["x"], "y": pile[key]["y"]} for key in pile]
        laid = themes_ai.gets_ids(themes_ai.lay_out(groups, cards, aside, size=gets_mod.card_height))
        by_label = {g["label"]: g for g in laid["groups"]}
        if len(by_label) != len(laid["groups"]):
            raise DemoError(f"Two of {name}'s LPETs share a title.")
        for l in lpets:
            g = by_label[l["title"]]
            if l.get("description"):
                g[themes_mod.DESCRIPTION] = l["description"]
            if l.get("domain"):
                g[themes_mod.DOMAIN] = l["domain"]
        version = dict(laid, id=gets_mod.FIRST_BOARD, name=gets_mod.FIRST_NAME, note="", picks={}, rows={})
        version = square(version, gets_mod.card_height)
        quotes = gets_mod.interview_quotes(data, inside)
        ticked = 0
        for l in lpets:
            gid = by_label[l["title"]]["id"]
            for tp, row in (l.get("rows") or {}).items():
                if row.get("state"):
                    gets_mod.row_op(data, version, inside, labels, {"op": "state", "lpet": gid, "timepoint": tp,
                                                                   "state": row["state"]}, name)
                if row.get("quote"):
                    words = " ".join(row["quote"].split())
                    found = [q["key"] for q in quotes.get(tp) or [] if " ".join(q["text"].split()) == words]
                    if len(found) != 1:
                        raise DemoError(f"The key quote {row['quote'][:40]!r}... of {name}'s {l['title']!r} at {tp} "
                                        f"is not one quote of that interview.")
                    gets_mod.row_op(data, version, inside, labels, {"op": "quote", "lpet": gid, "timepoint": tp,
                                                                   "quote": found[0]}, name)
                    ticked += 1
                    spans = []
                    for words_bold, span in zip(row.get("bold") or [], row.get("bold_spans") or []):
                        start = row["quote"].find(words_bold)
                        if start < 0:
                            raise DemoError(f"The bold {words_bold!r} is not in {name}'s key quote at {tp}.")
                        spans.append([start, start + len(words_bold)])
                    if spans:
                        cell = next(r for r in gets_mod.lpet_rows(data, version, inside) if r["id"] == gid)["cells"][tp]
                        text = cell["quote"]["text"]
                        for (a, b), w in zip(spans, row["bold"]):
                            if text[a:b] != w:
                                raise DemoError(f"The bold {w!r} of {name}'s {l['title']!r} at {tp} does not fall "
                                                f"where the key quote has it.")
                        gets_mod.row_op(data, version, inside, labels, {"op": "bold", "lpet": gid, "timepoint": tp,
                                                                       "spans": spans}, name)
        version["created"] = version["updated"] = made
        with md.clock(made):
            gets_mod.save(root, books, version)
        with md.clock(chosen):
            gets_mod.version_op(root, books, "choose", {"id": gets_mod.FIRST_BOARD})
        with md.clock(complete):
            gets_mod.version_op(root, books, "complete", {})
    return {"lpets": len(lpets), "cards": len(named), "set_aside": len(aside), "quotes": ticked}


def build_lgets(root: Path, plan: dict, project: dict) -> dict:
    """The LGETs across the three, inside `gets.lgets`, as `make_demo.build_gets` makes the IPA demo's GETs: every
    participant taken in from their LPETs board marked complete, each LGET of the LPETs it names, its description,
    laid out and arranged as a grid, the quote of each row of the LGET table ticked, then saved, made Current and
    marked complete. Answers the file and the counts."""
    import themes_ai

    root = Path(root)
    names = {k: v[0] for k, v in labels_of(project).items()}
    books = [{"case": name, "workbook": root / name / f"{name}{EN_ES}", "pets_complete": True} for name in CASES]
    for b in books:
        utime_all(case_files(b["workbook"]), LGETS_AT)
    lg = plan["lgets"]
    with gets_mod.lgets(root, names):
        with md.clock(LGETS_AT):
            data, _cases, _disk, _taken = gets_mod.assemble(root, books, themes_mod.now_iso())
        ids: dict[tuple[str, str], str] = {}
        for case, rec in data["cases"].items():
            if rec.get("state") != "in" or not rec.get("complete"):
                raise DemoError(f"{case}'s LPETs are not in from a board marked complete.")
            for pet in rec["pets"]:
                if pet.get("parent") is None:
                    ids[(case, pet["title"])] = gets_mod.card_of(case, "group", pet["id"])
        named: list[str] = []

        def key(m: dict) -> str:
            found = ids.get((m["case"], m["lpet"]))
            if not found:
                raise DemoError(f"{m['case']} has no LPET called {m['lpet']!r}.")
            named.append(found)
            return found

        groups = [{"label": g["title"], "description": g.get("description") or "",
                   "members": [key(m) for m in g["members"]], "groups": []} for g in lg["lgets"]]
        aside = [key(m) for m in lg.get("set_aside") or []]
        if len(named) != len(set(named)) or set(named) != set(ids.values()):
            raise DemoError("Every LPET is named once on the LGETs board, and some are not.")
        pile = data["boards"][0]["cards"]
        said = {gets_mod.card_of(case, "group", pet["id"]): gets_mod.layout_text(pet["title"], themes_mod.description_of(pet))
                for case, rec in data["cases"].items() for pet in rec["pets"]}
        cards = [{"key": k, "text": said[k], "x": pile[k]["x"], "y": pile[k]["y"]} for k in pile]
        laid = themes_ai.gets_ids(themes_ai.lay_out(groups, cards, aside, size=gets_mod.card_height))
        by_label = {g["label"]: g for g in laid["groups"]}
        for g in lg["lgets"]:
            if g.get("description"):
                by_label[g["title"]][themes_mod.DESCRIPTION] = g["description"]
            if g.get("note"):
                by_label[g["title"]]["note"] = g["note"]
        version = dict(laid, id=gets_mod.FIRST_BOARD, name=gets_mod.FIRST_NAME, note="", picks={}, rows={})
        version = square(version, gets_mod.card_height)
        targets = {t["id"]: t for t in gets_mod.row_targets(data, version, list(CASES))}
        for g in lg["lgets"]:
            gid = by_label[g["title"]]["id"]
            for case, q in (g.get("quotes") or {}).items():
                words = " ".join(q["quote"].split())
                found = [x["key"] for x in (targets.get(f"{gid}/{case}") or {}).get("quotes", [])
                         if " ".join(x["text"].strip('"').split()) == words]
                if len(found) != 1:
                    raise DemoError(f"The quote {q['quote'][:40]!r}... is not one of {case}'s under {g['title']!r}.")
                version["rows"].setdefault(gid, {})[case] = {"quote": found[0], "note": ""}
        with md.clock(LGETS_AT):
            gets_mod.save(root, books, version)
            gets_mod.version_op(root, books, "choose", {"id": gets_mod.FIRST_BOARD})
            gets_mod.version_op(root, books, "complete", {})
    return {"file": root / LGETS_FILE, "lgets": len(lg["lgets"]), "cards": len(named), "set_aside": len(aside),
            "rows": sum(len(r) for r in version["rows"].values())}


def build_trajectories(root: Path, plan: dict) -> dict:
    """The Trajectories board: each trajectory with its description, colour and icon, each participant placed in
    the order given with the note on why, and the board's note, through `trajectories.apply`. The participants'
    labels and pictures are their own, in the project file. Answers the file and the counts."""
    t = plan["trajectories"]
    ops = []
    for col in t["columns"]:
        ops += [{"op": "add", "title": col["title"]},
                {"op": "describe", "column": col["title"], "description": col.get("description") or ""},
                {"op": "colour", "column": col["title"], "colour": col["colour"]},
                {"op": "icon", "column": col["title"], "icon": col["icon"]}]
        ops += [{"op": "place", "participant": who, "column": col["title"]} for who in col.get("order") or []]
    for who, placed in (t.get("placed") or {}).items():
        if placed.get("note"):
            ops.append({"op": "note", "participant": who, "note": placed["note"]})
    if t.get("note"):
        ops.append({"op": "note_board", "note": t["note"]})
    data = traj_mod.fresh(TRAJ_AT)
    data.setdefault("tags", {})
    said = traj_mod.apply(data, list(CASES), ops)
    data["updated"] = TRAJ_AT
    traj_mod.write(Path(root), data)
    return {"file": traj_mod.path_of(Path(root)), "trajectories": len(t["columns"]),
            "placed": sum(len(c.get("order") or []) for c in t["columns"]), "changes": len(said)}


# ------------------------------------------------------------------ the whole demo

def build_all(into: Path, demo: Path | None = None) -> dict:
    """The whole longitudinal demo built into `into`, a folder that must not be there yet: its project file, the
    three participants, each one's LPETs, then the LGETs and the Trajectories board at its root."""
    into = Path(into)
    if into.exists():
        raise DemoError(f"{into} is there already, so nothing was built into it.")
    into.mkdir(parents=True)
    plan = read_analysis(demo)
    shutil.copyfile(lipa_dir(demo) / PROJECT_FILE, into / PROJECT_FILE)
    project = json.loads((into / PROJECT_FILE).read_text(encoding="utf-8"))
    if [t["label"] for t in project.get("timepoints") or []] != list(TIMEPOINTS):
        raise DemoError(f"The project's timepoints are not {', '.join(TIMEPOINTS)}.")
    built = {name: build_case(name, into, plan["cases"][name], demo) for name in CASES}
    for name in CASES:
        built[name]["lpets"] = build_lpets(into, name, plan["cases"][name], project)
    built["lgets"] = build_lgets(into, plan, project)
    built["trajectories"] = build_trajectories(into, plan)
    for name in CASES:
        md.pin(built[name]["workbook"], BUILT)
    return built


def shipped_files(folder: Path, name: str) -> list[Path]:
    """A participant's workbook and every file of theirs in `Working/`: the progress file, a PETs file a
    timepoint and the LPETs file."""
    return case_files(Path(folder) / name / f"{name}{EN_ES}")


def ship_lipa(force: bool = False, demo: Path | None = None, verbose: bool = True) -> dict:
    """The longitudinal demo built and put where it ships: each participant's workbook in `demo/lipa/pristine/` and
    their files in `pristine/Working/`, the LGETs and Trajectories files in `pristine/`, and the same in the live
    demo, each participant in its folder and the two files at its root. Live workbooks already there are replaced
    only with `force`, and one open in Excel refuses the whole build."""
    lipa = lipa_dir(demo)
    lives = {name: lipa / name / f"{name}{EN_ES}" for name in CASES}
    there = [live.name for live in lives.values() if live.exists()]
    if there and not force:
        raise DemoError(f"The longitudinal demo's {there[0]} is already there. Pass --force to build it again.")
    for live in lives.values():
        wb_mod.guard_lock(live)
    pristine = lipa / "pristine"
    with tempfile.TemporaryDirectory(prefix="demo-lipa-built-") as tmp:
        built = build_all(Path(tmp) / FOLDER, demo)
        if pristine.exists():
            shutil.rmtree(pristine)
        (pristine / "Working").mkdir(parents=True)
        for name, live in lives.items():
            work = live.parent / "Working"
            if work.is_dir():
                for old in work.glob(f"{live.stem}.*"):
                    old.unlink()
            work.mkdir(parents=True, exist_ok=True)
            for f in shipped_files(Path(tmp) / FOLDER, name):
                into = "" if f.suffix == ".xlsx" else "Working"
                shutil.copyfile(f, pristine / into / f.name)
                shutil.copyfile(f, live.parent / into / f.name)
        for f in ROOT_FILES:
            shutil.copyfile(Path(tmp) / FOLDER / f, pristine / f)
            shutil.copyfile(Path(tmp) / FOLDER / f, lipa / f)
    if verbose:
        for name in CASES:
            c = built[name]["counts"]
            line = ", ".join(f"{tp} {c[tp]['statements']} statements in {c[tp]['pets']} PETs" for tp in TIMEPOINTS)
            lp = built[name]["lpets"]
            print(f"  {name}: {line}; {lp['lpets']} LPETs of {lp['cards']} cards, {lp['set_aside']} set aside, "
                  f"{lp['quotes']} key quotes ticked")
        g = built["lgets"]
        print(f"  LGETs: {g['lgets']} of {g['cards']} LPETs, {g['rows']} quotes ticked")
        t = built["trajectories"]
        print(f"  Trajectories: {t['trajectories']}, {t['placed']} participants placed")
    return built


def main() -> int:
    ap = argparse.ArgumentParser(description="Build the longitudinal IPA demo.")
    ap.add_argument("--force", action="store_true", help="replace workbooks that are already there")
    ap.add_argument("--recordings", type=Path, metavar="CLIPS",
                    help="join each interview's clips from this folder into its recording, writing its timecodes")
    ap.add_argument("--audio-only", action="store_true", help="put each recording made in place in the demo")
    a = ap.parse_args()
    try:
        if a.recordings:
            build_recordings(a.recordings)
            return 0
        if a.audio_only:
            for name, tp in interviews():
                placed = place_recording(name, tp)
                print(f"  {name} {tp}: {placed.name + ' in place' if placed else 'no recording made for it'}")
            return 0
        print("Building the longitudinal demo.")
        ship_lipa(force=a.force)
    except (DemoError, wb_mod.WorkbookError) as exc:
        print(str(exc), file=sys.stderr)
        return 1
    print("Done.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
