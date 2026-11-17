#!/usr/bin/env python3
"""Build the reflexive thematic analysis demo: "Working from home", six invented participants interviewed for a
reflexive thematic analysis, as a finished thematic analysis project of the app's own model (rtabuild, 17 November
2026).

Adam, 14 November 2026: the thematic analysis demo codes the IPA demo's own interviews, and an IPA interview can only
be specifically IPA if an interview made for reflexive thematic analysis would differ, so a fourth demo has
interviews made for it: an open question about a pattern across a broader group, one shorter guide put to everyone,
and themes as patterns of shared meaning round a central organising concept. Its researcher, Leah Marsh, its six
participants, their words and the analysis are invented (rtawrite, approved by Adam on 16 November 2026), and each
interview is recorded in Gemini's voices (rtavoices). It lives inside the demo's folder, as the thematic analysis and
longitudinal demos do:

    demo/rta/idiograph-project.json            the project: its name, question and method, the researcher's
                                               reflexivity statement (Project settings' Reflexivity, settingsbuild),
                                               the participants' own labels, pictures, pen portraits and values, and
                                               its demographics
    demo/rta/source/<Name> - interview.csv     each interview, Name, Timestamp and Transcript, the timestamps the
                                               recording's own
    demo/rta/source/<Name> - coding.json       each passage's extracts with their codes and its note, and the times
                                               of the work, in the thematic analysis demo's shape
    demo/rta/source/Themes.json                the code list and the Themes board, each theme with its definition
                                               and note, the board itself with no note
    demo/rta/<Name>/<Name> - EN & ES.xlsx      the workbook, built from those
    demo/rta/pristine/                         the copy Reset demo restores from, the code list and the Themes
                                               board's file with it
    packaging/recording/<Name>-Initial-<hash>.m4a   the recordings, gitignored, assets of the release
                                               demo-recordings-1

Everything goes through the functions `make_demo.ship_ta` builds the thematic analysis demo with: each workbook
through `create_from_source`, every turn coded through the turn screen's own save, the rounds closed and coding
complete, the code list as the Code list screen writes it, and the Themes board laid out as that demo's is, saved
through the board's own save and made Current. The clock is held at times of its own, so the same sources build the
same files.

    .venv/bin/python apps/idiograph/make_demo_rta.py [--force]
    .venv/bin/python apps/idiograph/make_demo_rta.py --audio <rtavoices folder>

`--audio` takes the recordings again, from a folder holding `csv/<Name>.csv` and `join/<Name>.m4a` as rtavoices
writes them: each CSV's timestamps into the demo's interview (its words must be the demo's, turn for turn), each
recording into packaging/recording named by the interview as then written, the manifest written again, and the
demo built again, since the timecodes moved. Run it again after any recast of the voices.
"""
from __future__ import annotations

import argparse
import json
import os
import shutil
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
import boot  # noqa: E402

boot.setup()

import audio as audio_mod  # noqa: E402
import make_demo as md  # noqa: E402
import rounds as rounds_mod  # noqa: E402
import workbook as wb_mod  # noqa: E402

DemoError = md.DemoError

# the demo's folder inside the demo's, and its participants in the order the study took them
FOLDER = "rta"
CASES = ("Kemi", "Toby", "Ros", "Glen", "Dev", "Ffion")
SHEET = md.SHEET
EN_ES = md.EN_ES
PROJECT_FILE = md.PROJECT_FILE
THEMES = md.TA_THEMES
ROOT_FILES = (md.GETS_FILE, md.CODES_FILE)
# the room each row of the Themes board keeps under a code's card: its six participants' marks take a second line
# where the thematic analysis demo's three take one, so a row keeps more than `make_demo.TA_ROOM`, or the page pushes
# a card that would overlap the next row out of its column
ROOM = md.TA_ROOM + 28


# ------------------------------------------------------------------ the sources

def rta_dir(demo: Path | None = None) -> Path:
    """The reflexive thematic analysis demo's folder, inside the demo's."""
    return (Path(demo) if demo is not None else md.DEMO) / FOLDER


def interview(name: str, demo: Path | None = None) -> Path:
    """A participant's interview, its CSV among the demo's sources."""
    return rta_dir(demo) / "source" / f"{name} - interview.csv"


def coding_file(name: str, demo: Path | None = None) -> Path:
    return rta_dir(demo) / "source" / f"{name} - coding.json"


def read_plan(demo: Path | None = None) -> dict:
    return md.read_plan(rta_dir(demo) / "source" / THEMES)


# ------------------------------------------------------------------ the recordings

def recording(name: str, demo: Path | None = None) -> Path:
    """Where a participant's recording sits in the demo, where the player finds it."""
    return rta_dir(demo) / name / "Source" / SHEET / "Source" / f"{name}-{SHEET}.m4a"


def committed(name: str, demo: Path | None = None, folder: Path | None = None) -> Path:
    """The recording made for the interview as it stands, in packaging/recording unless `folder` says, there or
    not."""
    return Path(folder or md.RECORDINGS) / audio_mod.demo_recording_name(name, SHEET, interview(name, demo))


def recording_names(demo: Path | None = None) -> list[str]:
    """The names of the six recordings for the interviews as they stand."""
    return [committed(name, demo).name for name in CASES]


def place_recording(name: str, demo: Path | None = None, folder: Path | None = None) -> Path | None:
    """A recording made for the interview as it stands copied into its place, as `make_demo.place_recording` does,
    or None when there is none."""
    source = committed(name, demo, folder)
    if not source.is_file():
        return None
    target = recording(name, demo)
    target.parent.mkdir(parents=True, exist_ok=True)
    tmp = target.with_name(f".{target.stem}.copying{target.suffix}")
    shutil.copyfile(source, tmp)
    os.replace(tmp, target)
    return target


def m4a_seconds(path: Path) -> float:
    return md.clip_seconds(path)


def take_audio(voices: Path, demo: Path | None = None, folder: Path | None = None) -> list[dict]:
    """The recordings taken from rtavoices' folder: each `csv/<Name>.csv`'s timestamps written into the demo's
    interview, its words checked against the demo's turn for turn first, then `join/<Name>.m4a` copied into `folder`,
    packaging/recording unless a caller gives another, named by the interview as then written, and an older recording
    of the same participant taken away. Nothing is written unless all six are there and match. Answers each one's
    name, length, size and how many timecodes moved."""
    voices = Path(voices)
    taken = []
    for name in CASES:
        given, ours = voices / "csv" / f"{name}.csv", interview(name, demo)
        audio = voices / "join" / f"{name}.m4a"
        if not given.is_file() or not audio.is_file():
            raise DemoError(f"{voices} has no {given.name} or no {audio.name}, so no recording was taken.")
        new = md.read_turns(given)
        old = md.read_turns(ours) if ours.is_file() else None
        if old is not None and [(r["Name"], r["Transcript"]) for r in new] != [(r["Name"], r["Transcript"]) for r in old]:
            raise DemoError(f"{given.name}'s words are not the demo's interview turn for turn, so no recording was taken.")
        taken.append((name, new, old, audio))
    out = []
    for name, new, old, audio in taken:
        moved = sum(1 for a, b in zip(new, old or []) if a["Timestamp"] != b["Timestamp"]) if old else len(new)
        md.write_turns(new, interview(name, demo))
        target = committed(name, demo, folder)
        target.parent.mkdir(parents=True, exist_ok=True)
        tmp = target.with_name(f".{target.stem}.copying{target.suffix}")
        shutil.copyfile(audio, tmp)
        os.replace(tmp, target)
        for older in target.parent.glob(f"{name}-{SHEET}-*.m4a"):
            if older != target:
                older.unlink()
        out.append({"name": name, "seconds": m4a_seconds(target), "bytes": target.stat().st_size, "path": target,
                    "moved": moved, "turns": len(new)})
    return out


# ------------------------------------------------------------------ the participants

def build_case(name: str, into: Path, demo: Path | None = None) -> dict:
    """One participant built into `<into>/<name>/`, a folder that must not be there yet, as `make_demo.build_ta_case`
    builds the thematic analysis demo's: the workbook from the interview, every turn decided with its extracts, codes
    and notes, and the rounds closed and coding complete in its progress file. The coding closes one round a time
    given, so where the interview makes fewer rounds than it gives the last of them closes, and where more, the last
    time closes the rest a minute apart. Answers the two files' paths and the counts."""
    rows = md.read_turns(interview(name, demo))
    coding = md.read_annotations(coding_file(name, demo))
    folder = Path(into) / name
    if folder.exists():
        raise DemoError(f"{folder} is there already, so nothing was built into it.")
    folder.mkdir(parents=True)
    workbook = folder / f"{name}{EN_ES}"
    with tempfile.TemporaryDirectory(prefix="demo-rta-source-") as tmp:
        source = md.written_source(rows, Path(tmp) / f"{name} - interview.xlsx")
        wb_mod.create_from_source(source, workbook)
    progress = md.code_turns(workbook, name, coding)
    case = wb_mod.read_case(workbook)
    who = sorted({row["name"] for sheet in case["sheets"] for row in sheet["rows"]} - {name})[0]
    made = len(rounds_mod.build_rounds(case["sheets"], md.ROUND_MINUTES, who))
    coding = dict(coding, work=dict(coding["work"], rounds=fit_rounds(coding["work"]["rounds"], made)))
    md.record_work(workbook, name, coding, progress)
    md.pin(workbook, coding["built"])
    extracts = [x for t in coding["turns"] for x in t.get("extracts") or []]
    return {"workbook": workbook, "progress": rounds_mod.progress_path(workbook), "extracts": len(extracts),
            "codings": sum(len(x["codes"]) for x in extracts)}


def fit_rounds(given: list[dict], made: int) -> list[dict]:
    """The rounds the coding closes fitted to the `made` the interview makes: the first ones as given and the last
    given closing the rest, or the given ones cut to `made` with the last kept last."""
    if made <= 0 or not given:
        return []
    if len(given) >= made:
        return list(given[:made - 1]) + [given[-1]]
    import datetime as dt
    last = given[-1]
    out = list(given)
    for n in range(1, made - len(given) + 1):
        at = dt.datetime.fromisoformat(last["completed"]) + dt.timedelta(minutes=n)
        out.append({"seconds": last["seconds"], "completed": at.isoformat()})
    return out


def books(root: Path) -> list[dict]:
    """The study as the Themes board finds it in a folder holding the six participants."""
    return md.ta_books(root, CASES)


# ------------------------------------------------------------------ the whole demo

def build_all(into: Path, demo: Path | None = None) -> dict:
    """The whole demo built into `into`, a folder that must not be there yet: its project file, the six
    participants, and the code list and the Themes board at its root, the board with no note: the reflexivity
    statement is the project file's own since settingsbuild (17 November 2026)."""
    into = Path(into)
    if into.exists():
        raise DemoError(f"{into} is there already, so nothing was built into it.")
    into.mkdir(parents=True)
    plan = read_plan(demo)
    shutil.copyfile(rta_dir(demo) / PROJECT_FILE, into / PROJECT_FILE)
    project = json.loads((into / PROJECT_FILE).read_text(encoding="utf-8"))
    if project.get("method") != "ta" or sorted(project.get("participants") or {}) != sorted(CASES):
        raise DemoError(f"The project file is not a thematic analysis project of {', '.join(CASES)}.")
    built = {name: build_case(name, into, demo) for name in CASES}
    built["codes"] = md.build_ta_codes(into, plan, CASES)
    built["themes"] = md.build_ta_themes(into, plan, CASES, room=ROOM)
    return built


def shipped_files(folder: Path, name: str) -> list[Path]:
    """A participant's workbook and its progress file, which is all a thematic analysis participant has."""
    book = Path(folder) / name / f"{name}{EN_ES}"
    return [book, rounds_mod.progress_path(book)]


def ship_rta(force: bool = False, demo: Path | None = None, verbose: bool = True) -> dict:
    """The demo built and put where it ships: each participant's workbook in `demo/rta/pristine/` and its progress
    file in `pristine/Working/`, the code list and the Themes board's file in `pristine/`, and the same in the live
    demo, each participant in its folder and the two files at its root. Live workbooks already there are replaced
    only with `force`, and one open in Excel refuses the whole build."""
    rta = rta_dir(demo)
    lives = {name: rta / name / f"{name}{EN_ES}" for name in CASES}
    there = [live.name for live in lives.values() if live.exists()]
    if there and not force:
        raise DemoError(f"The reflexive thematic analysis demo's {there[0]} is already there. Pass --force to build it "
                        f"again.")
    for live in lives.values():
        wb_mod.guard_lock(live)
    pristine = rta / "pristine"
    with tempfile.TemporaryDirectory(prefix="demo-rta-built-") as tmp:
        built = build_all(Path(tmp) / FOLDER, demo)
        if pristine.exists():
            shutil.rmtree(pristine)
        (pristine / "Working").mkdir(parents=True)
        for name, live in lives.items():
            (live.parent / "Working").mkdir(parents=True, exist_ok=True)
            for f in shipped_files(Path(tmp) / FOLDER, name):
                into = "" if f.suffix == ".xlsx" else "Working"
                shutil.copyfile(f, pristine / into / f.name)
                shutil.copyfile(f, live.parent / into / f.name)
        for f in ROOT_FILES:
            shutil.copyfile(Path(tmp) / FOLDER / f, pristine / f)
            shutil.copyfile(Path(tmp) / FOLDER / f, rta / f)
    if verbose:
        for name in CASES:
            b = built[name]
            print(f"  {name}: {b['extracts']} extracts, {b['codings']} codes on them")
        t = built["themes"]
        print(f"  Themes: {len(built['codes']['codes'])} codes, {t['placed']} in {t['themes']} themes and "
              f"{t['subthemes']} subthemes, {t['not_placed']} unplaced")
    return built


def main() -> int:
    ap = argparse.ArgumentParser(description="Build the reflexive thematic analysis demo.")
    ap.add_argument("--force", action="store_true", help="replace workbooks that are already there")
    ap.add_argument("--audio", type=Path, metavar="VOICES",
                    help="take the recordings and their timecodes from rtavoices' folder (csv/, join/), then build")
    ap.add_argument("--audio-only", action="store_true", help="put each recording made in place in the demo")
    a = ap.parse_args()
    try:
        if a.audio_only:
            for name in CASES:
                placed = place_recording(name)
                print(f"  {name}: {placed.name + ' in place' if placed else 'no recording made for it'}")
            return 0
        if a.audio:
            print("Taking the recordings.")
            for made in take_audio(a.audio):
                print(f"  {made['name']}: {md.hhmmss(made['seconds'])}, {made['bytes'] / 1e6:.2f} MB, "
                      f"{made['path'].name}, {made['moved']} of {made['turns']} timecodes moved")
            md.write_manifest()
            a.force = True
        print("Building the reflexive thematic analysis demo.")
        ship_rta(force=a.force)
    except (DemoError, wb_mod.WorkbookError) as exc:
        print(str(exc), file=sys.stderr)
        return 1
    print("Done.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
