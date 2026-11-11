#!/usr/bin/env python3
"""Build the bundled demo: a finished IPA project of three invented cases on sharing a home with a dog.

Nobody real is in it, so the whole interface can be screen-recorded without a participant's words
ever reaching the screen. It is a worked example as a project looks once it is done (Adam, 24
October): every participant's turns decided, with experiential statements, exploratory notes, key
quotes and highlights, their rounds closed and Statements complete, a PETs board with PETs,
sub-PETs, descriptions, notes and picked quotes marked complete, and a GETs board across the three
with descriptions and the GET table's quotes ticked, marked complete. The PET tables and the GET
table are the app's own, made from those boards. Juno's has a recording, Rowan's and Mabel's are
shorter written interviews. It lives beside the app rather than under the case root:

    demo/source/Juno - interview.csv          Juno's transcript, committed, Rowan's and Mabel's beside it
    demo/source/Juno - annotations.json       her statements, notes, quotes and her PET board, theirs beside it
    demo/source/GETs.json                     the GETs board across the three
    demo/Juno/Juno - EN & ES.xlsx             the annotated workbook, built from those two
    demo/Juno/Working/...progress.json        the sidecar, and the case's board beside it
    demo/Juno/Source/Initial/Source/          the recording, generated here and gitignored
    demo/idiograph-gets.json                  the GETs file, gitignored, put back from pristine
    demo/pristine/                            the copy Reset demo restores from, the GETs file with it

    .venv/bin/python apps/idiograph/make_demo.py
    .venv/bin/python apps/idiograph/make_demo.py --written --force

The thematic analysis demo (demos, 3 November 2026, Adam that evening) is the same three participants coded
in a thematic analysis project, `demo/ta/`, from the same interview CSVs: each passage's extracts with their codes
and notes in `demo/ta/source/<name> - coding.json`, the code list and the Themes board in `demo/ta/source/Themes.json`,
built through the same functions (`ship_ta`) into `demo/ta/pristine/` and the live cases beside it, the code list
and the Themes board's file at `demo/ta/`. `--written` builds both demos, `--ta` the thematic analysis one alone.

`--audio-only` rebuilds the recording and leaves the CSV, the workbooks and their sidecars alone, which
is what the server runs in a background thread the first time the demo is opened on a machine that
has never built it. `--written`, or `--workbook-only`, does the reverse: the three cases and the GETs,
with no recording, so it needs no `say`. `--force` replaces workbooks that are already there.

The recording is macOS `say`, one clip per turn, two voices. The clips are measured and the
timecodes in the CSV are written from the cumulative durations plus a short gap, so clicking a
timecode in the app lands on the words of that turn. Without `say` a plain run refuses to start:
the demo recording is the one thing here that no other tool on the machine can produce.

Everything goes through the functions the app itself calls, with the clock held at the times the
annotations files give, every part of each workbook's zip dated the same and the files the GETs read
dated alike while it reads them, so the same sources build the same files byte for byte.
"""
from __future__ import annotations

import argparse
import contextlib
import csv
import datetime as dt
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import wave
import zipfile
from pathlib import Path

# the family's folders on the path first (boot.py), under `python -I` too, the root two folders up
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
import boot  # noqa: E402

boot.setup()
HERE = boot.ROOT

import openpyxl

import rounds as rounds_mod
import themes as themes_mod
import workbook as wb_mod

DEMO = boot.resource("demo")
SOURCE_CSV = DEMO / "source" / "Juno - interview.csv"
CASE = DEMO / "Juno"
WORKBOOK = CASE / "Juno - EN & ES.xlsx"
PRISTINE = DEMO / "pristine"
SHEET = "Initial"
PARTICIPANT = "Juno"
RECORDING = CASE / "Source" / SHEET / "Source" / f"{PARTICIPANT}-{SHEET}.m4a"

# The two written cases, with no recording, and the three the demo holds, Juno first. Each case is a
# folder of its name holding `<name> - EN & ES.xlsx`, the name the app gives any annotated workbook.
WRITTEN = ("Rowan", "Mabel")
CASES = (PARTICIPANT,) + WRITTEN
EN_ES = " - EN & ES.xlsx"
# the rounds the cases' progress files record, the app's default length
ROUND_MINUTES = 10
# what GETs writes at the demo's root, its file and the folder its exports land in, and the GETs
# board's source beside the cases' own
GETS_FILE = "idiograph-gets.json"
GETS_WORKING = "Working"
GETS_SOURCE = "GETs.json"
# the thematic analysis demo's folder inside the demo's, its code list's file at its root, its sources' board
# and its project file
TA_FOLDER = "ta"
CODES_FILE = "idiograph-codes.json"
TA_THEMES = "Themes.json"
PROJECT_FILE = "idiograph-project.json"

# Two clear built-in voices, one for each speaker. Both ship with macOS, and `say -v '?'` lists
# them. Neither honours `-r`, so the pace is the voice's own, about 180 words a minute.
VOICE_INTERVIEWER = "Daniel"
VOICE_PARTICIPANT = "Flo (English (UK))"
RATE = 22050
GAP_SECONDS = 0.5

BRACKET = re.compile(r"\[[^\]]*\]")

class DemoError(Exception):
    """Something the person running this needs to read."""


# ------------------------------------------------------------------ the CSV

def interviewer() -> str:
    """The interviewer name from config.json, which is what the demo transcript is built with."""
    try:
        data = json.loads((HERE / "config.json").read_text(encoding="utf-8"))
        name = str(data.get("interviewer") or "").strip()
    except (ValueError, OSError):
        name = ""
    return name or "Adam"


def read_turns(path: Path = SOURCE_CSV) -> list[dict]:
    with Path(path).open(encoding="utf-8-sig", newline="") as fh:
        rows = list(csv.DictReader(fh))
    if not rows:
        raise DemoError(f"{Path(path).name} has no turns in it.")
    missing = {"Name", "Timestamp", "Transcript"} - set(rows[0])
    if missing:
        raise DemoError(f"{Path(path).name} is missing the column {sorted(missing)[0]}.")
    return rows


def write_turns(rows: list[dict], path: Path = SOURCE_CSV) -> None:
    with Path(path).open("w", encoding="utf-8", newline="") as fh:
        out = csv.writer(fh)
        out.writerow(["Name", "Timestamp", "Transcript"])
        for row in rows:
            out.writerow([row["Name"], row["Timestamp"], row["Transcript"]])


def hhmmss(seconds: float) -> str:
    s = int(round(seconds))
    return f"{s // 3600:02d}:{(s % 3600) // 60:02d}:{s % 60:02d}"


def as_time(value: str) -> dt.time:
    parts = [int(p) for p in str(value).strip().split(":")]
    while len(parts) < 3:
        parts.insert(0, 0)
    return dt.time(parts[0], parts[1], parts[2])


def spoken(text: str) -> str:
    """What the voice says: the turn without any transcriber's marks in square brackets."""
    return BRACKET.sub(" ", str(text)).replace("[[", " ").strip()


# ------------------------------------------------------------- the recording

def have(tool: str) -> bool:
    return shutil.which(tool) is not None


def say_clip(text: str, voice: str, out: Path) -> None:
    """One turn, spoken into a WAV. The text goes through a file, so no quoting can bite."""
    with tempfile.NamedTemporaryFile("w", suffix=".txt", encoding="utf-8", delete=False) as fh:
        fh.write(text or " ")
        script = Path(fh.name)
    try:
        subprocess.run(["say", "-v", voice, "-f", str(script),
                        "--data-format", f"LEI16@{RATE}", "-o", str(out)],
                       check=True, capture_output=True)
    except subprocess.CalledProcessError as exc:
        raise DemoError(f"say failed on {voice}: {exc.stderr.decode('utf-8', 'replace').strip()}")
    finally:
        script.unlink(missing_ok=True)


def clip_seconds(path: Path) -> float:
    """The length of a clip. `afinfo` when it is there, the WAV header itself when it is not."""
    if have("afinfo"):
        out = subprocess.run(["afinfo", str(path)], capture_output=True, text=True, encoding="utf-8",
                             errors="replace").stdout
        m = re.search(r"estimated duration:\s*([\d.]+)", out)
        if m:
            return float(m.group(1))
    if have("ffprobe"):
        out = subprocess.run(["ffprobe", "-v", "quiet", "-show_entries", "format=duration",
                              "-of", "csv=p=0", str(path)], capture_output=True, text=True, encoding="utf-8",
                             errors="replace").stdout
        try:
            return float(out.strip())
        except ValueError:
            pass
    with wave.open(str(path), "rb") as fh:
        return fh.getnframes() / float(fh.getframerate())


def join_clips(clips: list[Path], gap: float, out: Path) -> None:
    """Every clip in order with a half-second of silence between them, into one WAV."""
    with wave.open(str(clips[0]), "rb") as first:
        params = first.getparams()
    silence = b"\x00" * int(params.sampwidth * params.nchannels * params.framerate * gap)
    with wave.open(str(out), "wb") as dest:
        dest.setparams(params)
        for i, clip in enumerate(clips):
            if i:
                dest.writeframes(silence)
            with wave.open(str(clip), "rb") as src:
                dest.writeframes(src.readframes(src.getnframes()))


def to_m4a(source: Path, out: Path) -> None:
    out.parent.mkdir(parents=True, exist_ok=True)
    tmp = out.with_name(f".{out.stem}.building{out.suffix}")
    tmp.unlink(missing_ok=True)
    if have("afconvert"):
        cmd = ["afconvert", "-f", "m4af", "-d", "aac", "-b", "48000", str(source), str(tmp)]
    elif have("ffmpeg"):
        cmd = ["ffmpeg", "-v", "quiet", "-y", "-i", str(source), "-c:a", "aac", "-b:a", "48k", str(tmp)]
    else:
        raise DemoError("Neither afconvert nor ffmpeg is on this machine, so the clips cannot be "
                        "joined into one recording.")
    subprocess.run(cmd, check=True, capture_output=True)
    tmp.replace(out)


def build_recording(write_csv: bool = True, verbose: bool = True) -> dict:
    """Speak every turn, measure the clips, and join them into the one recording.

    With `write_csv` the timecodes in the source CSV are rewritten from the measured durations, so
    a timecode click in the app lands on the words of that turn. The server rebuilds the recording
    without it, because the committed CSV and the workbook already carry those timecodes and the
    voices produce the same lengths every time.
    """
    if not have("say"):
        raise DemoError("This machine has no `say`, so the demo recording cannot be built here. "
                        "The demo workbook and its transcript still work, without audio.")
    rows = read_turns()
    who = interviewer()
    with tempfile.TemporaryDirectory(prefix="demo-audio-") as tmp:
        scratch = Path(tmp)
        clips, at, starts = [], 0.0, []
        for i, row in enumerate(rows):
            clip = scratch / f"{i:03d}.wav"
            voice = VOICE_PARTICIPANT if row["Name"].strip() == PARTICIPANT else VOICE_INTERVIEWER
            say_clip(spoken(row["Transcript"]), voice, clip)
            clips.append(clip)
            starts.append(at)
            at += clip_seconds(clip) + GAP_SECONDS
            if verbose and (i + 1) % 20 == 0:
                print(f"  {i + 1} of {len(rows)} turns spoken")
        joined = scratch / "joined.wav"
        join_clips(clips, GAP_SECONDS, joined)
        length = clip_seconds(joined)
        to_m4a(joined, RECORDING)
    moved = [i for i, row in enumerate(rows) if row["Timestamp"] != hhmmss(starts[i])]
    if write_csv:
        for row, start in zip(rows, starts):
            row["Timestamp"] = hhmmss(start)
            if row["Name"].strip() != PARTICIPANT:
                row["Name"] = who
        write_turns(rows)
    result = {"turns": len(rows), "seconds": length, "bytes": RECORDING.stat().st_size,
              "path": RECORDING, "moved": len(moved)}
    if verbose:
        print(f"  recording: {hhmmss(length)}, {result['bytes'] / 1e6:.1f} MB, {RECORDING.name}")
        if not write_csv and moved:
            print(f"  note: {len(moved)} timecodes in the CSV no longer match the clips")
    return result


# --------------------------------------------------------------- the pristine copy

def reset(pristine: Path | None = None, workbook: Path | None = None) -> dict:
    """Put one demo case back the way it ships, Juno's unless `workbook` names another.

    The themes file goes too, and the board the case ships with comes back in its place, each case's
    marked board, or none for a case the pristine copy holds no board for.
    `pristine` and `workbook` default to the demo beside this file. The Mac app passes the
    pristine copy inside its bundle and the workbook it works on in Application Support.
    """
    pristine = Path(pristine) if pristine is not None else PRISTINE
    workbook = Path(workbook) if workbook is not None else WORKBOOK
    source = pristine / workbook.name
    if not source.exists():
        raise DemoError("The pristine copy of the demo is missing, so it cannot be reset.")
    wb_mod.guard_lock(workbook)
    workbook.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, workbook)
    sidecar = rounds_mod.progress_path(workbook)
    seed_file = pristine / "Working" / sidecar.name
    sidecar.parent.mkdir(parents=True, exist_ok=True)
    if seed_file.exists():
        shutil.copy2(seed_file, sidecar)
    elif sidecar.exists():
        sidecar.unlink()
    for held in sidecar.parent.glob("*.themes.json"):
        held.unlink()
    board = pristine / "Working" / themes_mod.themes_path(workbook).name
    if board.exists():
        shutil.copy2(board, sidecar.parent / board.name)
    return {"reset": True, "path": str(workbook)}


def reset_all(pristine: Path | None = None, demo: Path | None = None) -> dict:
    """Reset demo: every demo case put back the way it ships, Juno, Rowan and Mabel, the GETs file
    put back as it ships from the pristine copy, or taken away when that holds none, and the
    `Working/` the GETs exports land in taken away.

    A case is reset when the pristine copy holds its workbook. A workbook open in Excel refuses the
    whole reset before anything is written, so the three never end up half put back. `pristine`
    and `demo` default to the demo beside this file, and the Mac app passes the bundle's pristine
    copy and the demo it works on in Application Support.
    """
    pristine = Path(pristine) if pristine is not None else PRISTINE
    demo = Path(demo) if demo is not None else DEMO
    books = [demo / name / f"{name}{EN_ES}" for name in CASES if (pristine / f"{name}{EN_ES}").exists()]
    if not books:
        raise DemoError("The pristine copy of the demo is missing, so it cannot be reset.")
    for book in books:
        wb_mod.guard_lock(book)
    for book in books:
        reset(pristine, book)
    # the GETs file and, in the thematic analysis demo, the code list
    for name in (GETS_FILE, CODES_FILE):
        shipped = pristine / name
        if shipped.is_file():
            # a new copy, dated now, so nothing that read the file before the reset keeps that read
            shutil.copyfile(shipped, demo / name)
        else:
            (demo / name).unlink(missing_ok=True)
    exports = demo / GETS_WORKING
    if exports.is_dir() and not exports.is_symlink():
        shutil.rmtree(exports)
    return {"reset": True, "cases": [book.parent.name for book in books]}


def fill(pristine: Path | None = None, demo: Path | None = None) -> list[Path]:
    """Copy into each demo case whatever of it the pristine copy holds and the case is missing: its
    workbook, its progress file and its board, and the GETs file at the demo's root. A file already
    there is never replaced.

    The sidecars and the GETs file are gitignored, so a clone of the repo carries the cases'
    workbooks and none of their progress, boards or GETs. The server runs this as it starts, which gives a fresh clone the demo
    as it ships, and on a demo worked on it finds nothing missing and copies nothing. Answers the
    files copied.
    """
    pristine = Path(pristine) if pristine is not None else PRISTINE
    demo = Path(demo) if demo is not None else DEMO
    copied = []
    for name in CASES:
        book = demo / name / f"{name}{EN_ES}"
        side = rounds_mod.progress_path(book)
        pairs = [(pristine / book.name, book),
                 (pristine / "Working" / side.name, side),
                 (pristine / "Working" / themes_mod.themes_path(book).name, themes_mod.themes_path(book))]
        for source, target in pairs:
            if source.is_file() and not target.exists():
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(source, target)
                copied.append(target)
    # the GETs file and, in the thematic analysis demo, the code list
    for name in (GETS_FILE, CODES_FILE):
        target = demo / name
        if (pristine / name).is_file() and not target.exists():
            shutil.copy2(pristine / name, target)
            copied.append(target)
    return copied


# ------------------------------------------------------------ the written cases

def written_sources(name: str, demo: Path | None = None) -> tuple[Path, Path]:
    """A written case's two sources: its interview CSV and its annotations file."""
    folder = (Path(demo) if demo is not None else DEMO) / "source"
    return folder / f"{name} - interview.csv", folder / f"{name} - annotations.json"


def read_annotations(path: Path) -> dict:
    try:
        data = json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        raise DemoError(f"{Path(path).name} could not be read: {exc}")
    if not isinstance(data, dict) or not isinstance(data.get("turns"), list):
        raise DemoError(f"{Path(path).name} has no turns in it.")
    return data


def written_source(rows: list[dict], out: Path) -> Path:
    """The CSV as a three-column raw source workbook, which is what create_from_source reads, with
    each speaker named as the CSV names them, so the same CSV builds the same workbook whatever
    config.json says. The timestamps go in as times with the format a transcribed source carries, so
    the workbook the app builds from this is the same shape as one built from a real transcript."""
    book = openpyxl.Workbook()
    ws = book.active
    ws.title = SHEET
    ws.append(["Name", "Timestamp", "Transcript"])
    for r, row in enumerate(rows, start=2):
        ws.cell(r, 1, row["Name"].strip())
        cell = ws.cell(r, 2, as_time(row["Timestamp"]))
        cell.number_format = "h:mm:ss"
        ws.cell(r, 3, row["Transcript"])
    book.save(out)
    book.close()
    return out


@contextlib.contextmanager
def clock(at: str):
    """The themes module's clock held at `at`, so a board made here carries the times the
    annotations give and not the time it was built."""
    held = themes_mod.now_iso
    themes_mod.now_iso = lambda: at
    try:
        yield
    finally:
        themes_mod.now_iso = held


def annotate(workbook: Path, name: str, notes: dict) -> dict:
    """Every participant turn decided, through the turn screen's own saves: its statements, its
    exploratory note and its key quotes, each quote checked against the turn and put in inverted
    commas as the turn screen puts it, and its highlight, or the turn marked reviewed and empty.
    Answers the progress file as it then stands, not yet written."""
    case = wb_mod.read_case(workbook)
    turns = [row for sheet in case["sheets"] for row in sheet["rows"] if row["name"] == name]
    given = notes["turns"]
    if len(turns) != len(given):
        raise DemoError(f"{name} has {len(turns)} turns and the annotations give {len(given)}.")
    progress = rounds_mod.load_progress(workbook)
    for row, item in zip(turns, given):
        if not row["text"].startswith(str(item.get("at") or "\0")):
            raise DemoError(f"{name}'s turn at row {row['row']} does not start with {item.get('at')!r}.")
        key = rounds_mod.row_key(SHEET, row["row"])
        if item.get("empty"):
            progress["rows"][key] = rounds_mod.REVIEWED_EMPTY
            continue
        for quote in item.get("kq") or []:
            if quote not in row["text"]:
                raise DemoError(f"The key quote {quote!r} is not in {name}'s turn at row {row['row']}.")
        quotes = "\n".join(f'"{q}"' for q in item.get("kq") or [])
        wb_mod.save_turn(workbook, SHEET, row["row"], "\n".join(item["es"]), item.get("en", ""), quotes)
        progress["rows"][key] = rounds_mod.HAS_CONTENT
        phrase = item.get("crux")
        if phrase:
            at = row["text"].find(phrase)
            if at < 0:
                raise DemoError(f"The phrase {phrase!r} is not in {name}'s turn at row {row['row']}.")
            wb_mod.save_crux(workbook, SHEET, row["row"], at, at + len(phrase), phrase, op="add")
    progress["last"] = {"sheet": SHEET, "row": turns[-1]["row"]}
    return progress


def record_work(workbook: Path, name: str, notes: dict, progress: dict) -> dict:
    """The rounds closed, each with its minutes and when it closed, the days they closed on, and
    Statements complete, at the times the annotations give, written as the app writes the file."""
    case = wb_mod.read_case(workbook)
    speakers = {row["name"] for sheet in case["sheets"] for row in sheet["rows"]} - {name}
    who = sorted(speakers)[0] if speakers else ""
    made = rounds_mod.build_rounds(case["sheets"], ROUND_MINUTES, who)
    work = notes["work"]
    if len(made) != len(work["rounds"]):
        raise DemoError(f"{name}'s interview makes {len(made)} rounds and the annotations close {len(work['rounds'])}.")
    for rnd, closed in zip(made, work["rounds"]):
        progress["rounds"][str(rnd["number"])] = {"seconds": int(closed["seconds"]), "completed": closed["completed"]}
        day = progress["days"].setdefault(closed["completed"][:10], {"rounds": 0})
        day["rounds"] += 1
    states = rounds_mod.row_states(case["sheets"], progress, who)
    if not all(rounds_mod.round_done(rnd, states) for rnd in made):
        raise DemoError(f"Not every turn of {name}'s is decided, so the rounds cannot close.")
    progress["complete"] = {"at": work["complete"]}
    rounds_mod.save_progress(workbook, progress)
    return progress


def make_board(workbook: Path, name: str, notes: dict) -> dict:
    """The case's PETs on Board 1, laid out the way an agent's board make lays one out, each theme's
    description, note and picked key quote added, then saved, marked the Current board and marked complete,
    through the themes module's own save and board ops with its clock at the annotations' times.

    Every statement of the case is named once: under a PET or one of its sub-themes, left unplaced
    or discarded. A statement named twice, or one left out, is an error here."""
    import themes_ai

    plan = notes["board"]
    read = themes_mod.read_cards(workbook)
    keys: dict[str, str] = {}
    for card in read["cards"]:
        if card["text"] in keys:
            raise DemoError(f"Two of {name}'s statements read {card['text']!r}.")
        keys[card["text"]] = card["key"]

    named: list[str] = []

    def key(text: str) -> str:
        if text not in keys:
            raise DemoError(f"No statement of {name}'s reads {text!r}.")
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
    discarded = [key(t) for t in plan.get("discarded") or []]
    if len(named) != len(set(named)) or set(named) != set(keys.values()):
        raise DemoError(f"Every statement of {name}'s is named once on the board, and some are not.")

    pile = themes_mod.blank_version(read["cards"], plan["made"])["cards"]
    cards = [dict(c, x=pile[c["key"]]["x"], y=pile[c["key"]]["y"]) for c in read["cards"]]
    laid = themes_ai.lay_out(groups, cards, discarded)
    by_label = {g["label"]: g for g in laid["groups"]}
    if len(by_label) != len(laid["groups"]):
        raise DemoError(f"Two of {name}'s themes share a title.")
    by_id = {g["id"]: g for g in laid["groups"]}
    picks = {}
    for pet in plan["pets"]:
        themes = [pet] + list(pet.get("subs") or [])
        for theme in themes:
            if theme.get("note"):
                by_label[theme["title"]]["note"] = theme["note"]
            # the layout made room for the description under its title, and the board keeps it
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
                 created=plan["made"], updated=plan["made"], picks=picks)
    with clock(plan["made"]):
        themes_mod.save(workbook, board, name)
    with clock(plan["chosen"]):
        themes_mod.version_op(workbook, "choose", {"id": themes_mod.FIRST_VERSION}, name)
    with clock(plan["complete"]):
        themes_mod.version_op(workbook, "complete", {}, name)
    return {"statements": len(keys), "pets": len(plan["pets"]),
            "subs": sum(len(p.get("subs") or []) for p in plan["pets"]), "unplaced": len(unplaced),
            "discarded": len(discarded)}


# every part of the workbook's zip dated alike, and the document's own two times with it
CORE_TIMES = re.compile(r"(<dcterms:(?:created|modified)\b[^>]*>)([^<]*)(</dcterms:(?:created|modified)>)")


def pin(path: Path, at: str) -> Path:
    """The workbook with every part of its zip dated `at` and its created and modified times set to
    it, which is all that differs between two builds from the same sources."""
    stamp = dt.datetime.fromisoformat(at)
    when = (stamp.year, stamp.month, stamp.day, stamp.hour, stamp.minute, stamp.second)
    iso = stamp.strftime("%Y-%m-%dT%H:%M:%SZ")
    path = Path(path)
    with zipfile.ZipFile(path) as z:
        parts = [(info.filename, z.read(info.filename)) for info in z.infolist()]
    tmp = path.with_name(f".{path.stem}.pinned.xlsx")
    with zipfile.ZipFile(tmp, "w") as out:
        for name, data in parts:
            if name == "docProps/core.xml":
                data = CORE_TIMES.sub(lambda m: m.group(1) + iso + m.group(3), data.decode("utf-8")).encode("utf-8")
            info = zipfile.ZipInfo(name, date_time=when)
            info.compress_type = zipfile.ZIP_DEFLATED
            # every part said to be made on Unix, which is what zipfile says on a Mac and not on
            # Windows, so the zip comes out byte for byte the same whichever system builds it
            info.create_system = 3
            info.external_attr = 0o644 << 16
            out.writestr(info, data)
    os.replace(tmp, path)
    return path


def build_written(name: str, into: Path, demo: Path | None = None) -> dict:
    """One written case built from its two sources into `<into>/<name>/`, a folder that must not be
    there yet: the workbook through create_from_source, every turn decided, the rounds closed and
    Statements complete in its progress file, and its board in its themes file. Answers the paths
    of the three files and the board's counts."""
    csv_path, notes_path = written_sources(name, demo)
    rows = read_turns(csv_path)
    notes = read_annotations(notes_path)
    folder = Path(into) / name
    if folder.exists():
        raise DemoError(f"{folder} is there already, so nothing was built into it.")
    folder.mkdir(parents=True)
    workbook = folder / f"{name}{EN_ES}"
    with tempfile.TemporaryDirectory(prefix="demo-source-") as tmp:
        source = written_source(rows, Path(tmp) / f"{name} - interview.xlsx")
        wb_mod.create_from_source(source, workbook)
    progress = annotate(workbook, name, notes)
    record_work(workbook, name, notes, progress)
    counts = make_board(workbook, name, notes)
    pin(workbook, notes["built"])
    return dict(counts, workbook=workbook, progress=rounds_mod.progress_path(workbook),
                themes=themes_mod.themes_path(workbook))


def put(built: dict, live: Path, pristine: Path) -> None:
    """A built case's workbook into `pristine/` and its two sidecars into `pristine/Working/`, and the
    same three into the live case folder beside `live`, its workbook."""
    (pristine / "Working").mkdir(parents=True, exist_ok=True)
    rounds_mod.progress_path(live).parent.mkdir(parents=True, exist_ok=True)
    for part in ("workbook", "progress", "themes"):
        source = built[part]
        shutil.copyfile(source, (pristine if part == "workbook" else pristine / "Working") / source.name)
        shutil.copyfile(source, (live.parent if part == "workbook" else live.parent / "Working") / source.name)


def said(name: str, built: dict) -> str:
    return (f"  {name}: {built['statements']} statements, {built['pets']} PETs, {built['subs']} sub-PETs, "
            f"{built['unplaced']} unplaced, {built['discarded']} discarded")


def ship_written(name: str, force: bool = False, demo: Path | None = None, verbose: bool = True) -> dict:
    """Build one case and put it where it ships: the workbook in `pristine/` and its two
    sidecars in `pristine/Working/`, and the same three in the live case folder, `demo/<name>/`.
    A live workbook already there is replaced only with `force`. The GETs are left as they are,
    and `ship_all` builds them with the three cases."""
    demo = Path(demo) if demo is not None else DEMO
    live = demo / name / f"{name}{EN_ES}"
    if live.exists() and not force:
        raise DemoError(f"{live.name} is already there. Pass --force to build it again.")
    wb_mod.guard_lock(live)
    with tempfile.TemporaryDirectory(prefix="demo-written-") as tmp:
        built = build_written(name, Path(tmp), demo)
        put(built, live, demo / "pristine")
    if verbose:
        print(said(name, built))
    return {"workbook": live, "statements": built["statements"]}


# ------------------------------------------------------------------ the GETs

def gets_source(demo: Path | None = None) -> Path:
    return (Path(demo) if demo is not None else DEMO) / "source" / GETS_SOURCE


def read_gets(path: Path) -> dict:
    try:
        data = json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        raise DemoError(f"{Path(path).name} could not be read: {exc}")
    if not isinstance(data, dict) or not isinstance(data.get("gets"), list):
        raise DemoError(f"{Path(path).name} has no GETs in it.")
    return data


def gets_books(root: Path) -> list[dict]:
    """The study as the GETs screen finds it in a folder holding the three cases, each by the name
    its themes file gives it."""
    return [{"case": name, "workbook": Path(root) / name / f"{name}{EN_ES}", "pets_complete": True}
            for name in CASES]


def build_gets(root: Path, demo: Path | None = None) -> dict:
    """The GETs board across the three cases built into `root`, a folder holding them as
    `build_written` leaves them: every case taken in, each GET with its PETs and sub-PETs, its title,
    description and note, laid out as the server lays out a board made whole, the PET and sub-PET cards it
    leaves out set aside, the quote of each row of the GET table ticked, then saved through the GETs
    screen's own save, made the Current board and marked complete, with the clock at the times the
    source gives. Every PET and sub-PET of the three is named once, and a name that is not one of
    them, or a quote that is not under its GET, is an error. Answers the file and its counts."""
    import gets as gets_mod
    import themes_ai

    plan = read_gets(gets_source(demo))
    root = Path(root)
    books = gets_books(root)
    # each case's two files dated alike, so the file the GETs write holds the same times on every build
    at = int(dt.datetime.fromisoformat(plan["made"]).timestamp()) * 1_000_000_000
    for book in books:
        for path in (book["workbook"], themes_mod.themes_path(book["workbook"])):
            os.utime(path, ns=(at, at))
    with clock(plan["made"]):
        data, _cases, _disk, _taken = gets_mod.assemble(root, books, themes_mod.now_iso())
    ids: dict[tuple[str, str], str] = {}
    for case, rec in data["cases"].items():
        if rec.get("state") != "in" or not rec.get("complete"):
            raise DemoError(f"{case}'s PETs are not in from a board marked complete, so the GETs cannot be built.")
        deep = gets_mod.depths(rec)
        for pet in rec["pets"]:
            if deep.get(pet["id"], 0) <= 1:
                ids[(case, pet["title"])] = gets_mod.card_of(case, "group", pet["id"])
    named: list[str] = []

    def key(item: dict) -> str:
        found = ids.get((str(item.get("case")), str(item.get("pet"))))
        if not found:
            raise DemoError(f"{item.get('case')} has no PET or sub-PET called {item.get('pet')!r}.")
        named.append(found)
        return found

    groups = [{"label": g["title"], "description": g.get("description") or "",
               "members": [key(m) for m in g["members"]], "groups": []} for g in plan["gets"]]
    aside = [key(m) for m in plan.get("set_aside") or []]
    if len(named) != len(set(named)) or set(named) != set(ids.values()):
        raise DemoError("Every PET and sub-PET is named once on the GETs board, and some are not.")
    pile = data["boards"][0]["cards"]
    # each card measured as the page draws it, its title and under it its PET's description, as
    # `gets apply` measures one (idiograph_cli.cmd_gets_apply)
    said = {gets_mod.card_of(case, "group", pet["id"]): gets_mod.layout_text(pet["title"], themes_mod.description_of(pet))
            for case, rec in data["cases"].items() for pet in rec["pets"]}
    cards = [{"key": k, "text": said[k], "x": pile[k]["x"], "y": pile[k]["y"]} for k in pile]
    laid = themes_ai.gets_ids(themes_ai.lay_out(groups, cards, aside, size=gets_mod.card_height))
    by_label = {g["label"]: g for g in laid["groups"]}
    if len(by_label) != len(laid["groups"]):
        raise DemoError("Two GETs share a title.")
    for g in plan["gets"]:
        if g.get("note"):
            by_label[g["title"]]["note"] = g["note"]
        if g.get("description"):
            by_label[g["title"]][themes_mod.DESCRIPTION] = g["description"]
    version = dict(laid, id=gets_mod.FIRST_BOARD, name=gets_mod.FIRST_NAME, note="", picks={}, rows={})
    inside = [book["case"] for book in books]
    targets = {t["id"]: t for t in gets_mod.row_targets(data, version, inside)}
    for g in plan["gets"]:
        gid = by_label[g["title"]]["id"]
        for case, words in (g.get("quotes") or {}).items():
            found = [q["key"] for q in (targets.get(f"{gid}/{case}") or {}).get("quotes", [])
                     if q["text"].strip('"') == words]
            if len(found) != 1:
                raise DemoError(f"The quote {words!r} is not one of {case}'s under {g['title']!r}.")
            version["rows"].setdefault(gid, {})[case] = {"quote": found[0], "note": ""}
    with clock(plan["made"]):
        gets_mod.save(root, books, version)
    with clock(plan["chosen"]):
        gets_mod.version_op(root, books, "choose", {"id": gets_mod.FIRST_BOARD})
    with clock(plan["complete"]):
        gets_mod.version_op(root, books, "complete", {})
    return {"file": gets_mod.gets_path(root), "gets": len(plan["gets"]), "cards": len(named),
            "set_aside": len(aside), "rows": sum(len(r) for r in version["rows"].values())}


def build_all(into: Path, demo: Path | None = None) -> dict:
    """The whole finished demo built into `into`, a folder that must not be there yet: the three
    cases as `build_written` makes each, then the GETs across them at its root. Answers each case's
    files and counts, by name, and the GETs' under `gets`."""
    into = Path(into)
    if into.exists():
        raise DemoError(f"{into} is there already, so nothing was built into it.")
    into.mkdir(parents=True)
    built = {name: build_written(name, into, demo) for name in CASES}
    built["gets"] = build_gets(into, demo)
    return built


def ship_all(force: bool = False, demo: Path | None = None, verbose: bool = True) -> dict:
    """The finished demo built and put where it ships: each case's workbook in `pristine/` and its
    two sidecars in `pristine/Working/`, the GETs file in `pristine/`, and the same in the live
    demo, each case in its folder and the GETs file at the demo's root. Live workbooks already
    there are replaced only with `force`, and one open in Excel refuses the whole build."""
    demo = Path(demo) if demo is not None else DEMO
    lives = {name: demo / name / f"{name}{EN_ES}" for name in CASES}
    there = [live.name for live in lives.values() if live.exists()]
    if there and not force:
        raise DemoError(f"{there[0]} is already there. Pass --force to build it again.")
    for live in lives.values():
        wb_mod.guard_lock(live)
    pristine = demo / "pristine"
    with tempfile.TemporaryDirectory(prefix="demo-built-") as tmp:
        built = build_all(Path(tmp) / "demo", demo)
        for name, live in lives.items():
            put(built[name], live, pristine)
        shutil.copyfile(built["gets"]["file"], pristine / GETS_FILE)
        shutil.copyfile(built["gets"]["file"], demo / GETS_FILE)
    if verbose:
        for name in CASES:
            print(said(name, built[name]))
        g = built["gets"]
        print(f"  GETs: {g['gets']} GETs from {g['cards']} PETs and sub-PETs, {g['set_aside']} set aside, "
              f"{g['rows']} quotes ticked")
    return built


# ---------------------------------------------------------- the thematic analysis demo

def ta_dir(demo: Path | None = None) -> Path:
    """The thematic analysis demo's folder, inside the demo's."""
    return (Path(demo) if demo is not None else DEMO) / TA_FOLDER


def ta_sources(name: str, demo: Path | None = None) -> tuple[Path, Path]:
    """A participant's two sources in the thematic analysis demo: the interview CSV the IPA demo's case is built
    from, the same words, and the coding file among the thematic analysis demo's own sources."""
    demo = Path(demo) if demo is not None else DEMO
    return demo / "source" / f"{name} - interview.csv", ta_dir(demo) / "source" / f"{name} - coding.json"


def read_plan(path: Path) -> dict:
    """The thematic analysis demo's code list and Themes board as its source gives them."""
    try:
        data = json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        raise DemoError(f"{Path(path).name} could not be read: {exc}")
    if not isinstance(data, dict) or not isinstance(data.get("codes"), list) or not isinstance(data.get("themes"), list):
        raise DemoError(f"{Path(path).name} has no codes or themes in it.")
    return data


def code_turns(workbook: Path, name: str, coding: dict) -> dict:
    """Every participant turn decided, through the turn screen's own save: each extract the coding gives, checked
    against the turn and put in inverted commas, with each of its codes one of the passage's pairs, so two codes on
    one extract are two pairs with the same quote, as the Coding screen writes them (codes.py), and the passage's
    note, or the turn marked reviewed and empty. Answers the progress file, not yet written."""
    case = wb_mod.read_case(workbook)
    turns = [row for sheet in case["sheets"] for row in sheet["rows"] if row["name"] == name]
    given = coding["turns"]
    if len(turns) != len(given):
        raise DemoError(f"{name} has {len(turns)} turns and the coding gives {len(given)}.")
    progress = rounds_mod.load_progress(workbook)
    for row, item in zip(turns, given):
        if not row["text"].startswith(str(item.get("at") or "\0")):
            raise DemoError(f"{name}'s turn at row {row['row']} does not start with {item.get('at')!r}.")
        key = rounds_mod.row_key(SHEET, row["row"])
        if item.get("empty"):
            progress["rows"][key] = rounds_mod.REVIEWED_EMPTY
            continue
        pairs = []
        for extract in item.get("extracts") or []:
            words = extract["text"]
            if words not in row["text"]:
                raise DemoError(f"The extract {words!r} is not in {name}'s turn at row {row['row']}.")
            if not extract.get("codes"):
                raise DemoError(f"The extract {words!r} of {name}'s has no code.")
            pairs += [{"es": code, "kq": f'"{words}"'} for code in extract["codes"]]
        wb_mod.save_turn(workbook, SHEET, row["row"], None, item.get("note", ""), None, pairs=pairs)
        progress["rows"][key] = rounds_mod.HAS_CONTENT
    progress["last"] = {"sheet": SHEET, "row": turns[-1]["row"]}
    return progress


def build_ta_case(name: str, into: Path, demo: Path | None = None) -> dict:
    """One participant of the thematic analysis demo built into `<into>/<name>/`, a folder that must not be there
    yet: the workbook from the same CSV as the IPA demo's, every turn decided with its extracts, codes and notes,
    and the rounds closed and coding complete in its progress file. No themes file: a thematic analysis project
    has no board for each participant. Answers the two files' paths and the counts."""
    csv_path, coding_path = ta_sources(name, demo)
    rows = read_turns(csv_path)
    coding = read_annotations(coding_path)
    folder = Path(into) / name
    if folder.exists():
        raise DemoError(f"{folder} is there already, so nothing was built into it.")
    folder.mkdir(parents=True)
    workbook = folder / f"{name}{EN_ES}"
    with tempfile.TemporaryDirectory(prefix="demo-ta-source-") as tmp:
        source = written_source(rows, Path(tmp) / f"{name} - interview.xlsx")
        wb_mod.create_from_source(source, workbook)
    progress = code_turns(workbook, name, coding)
    record_work(workbook, name, coding, progress)
    pin(workbook, coding["built"])
    extracts = [x for t in coding["turns"] for x in t.get("extracts") or []]
    return {"workbook": workbook, "progress": rounds_mod.progress_path(workbook), "extracts": len(extracts),
            "codings": sum(len(x["codes"]) for x in extracts)}


def ta_books(root: Path) -> list[dict]:
    """The study as the Themes board finds it in a folder holding the three participants."""
    return [{"case": name, "workbook": Path(root) / name / f"{name}{EN_ES}", "pets_complete": None} for name in CASES]


def build_ta_codes(root: Path, plan: dict) -> dict:
    """The code list at `root`, each code of the plan with its description, in the plan's order, written as the
    Code list screen writes it, at the plan's time. Every code the participants' passages hold is in the plan, and
    every code in the plan is on some extract. Answers the list."""
    import codes as codes_mod

    data = codes_mod.fresh(plan["made"])
    for c in plan["codes"]:
        data["codes"].append({"id": codes_mod.next_id(data), "name": c["name"], "description": c["description"]})
    listed = {codes_mod.norm(c["name"]) for c in data["codes"]}
    if len(listed) != len(data["codes"]):
        raise DemoError("Two codes in the thematic analysis demo's list share a name.")
    held = {x["code"] for x in codes_mod.extracts_of(codes_mod.study_rows(ta_books(root)))}
    if held - listed:
        raise DemoError(f"A code on an extract is not in the list: {sorted(held - listed)[0]!r}.")
    if listed - held:
        raise DemoError(f"A code in the list is on no extract: {sorted(listed - held)[0]!r}.")
    codes_mod.write(root, data)
    return data


# The thematic analysis demo's Themes board laid out by hand, as a careful researcher would lay it (the coordinator,
# 3 November 2026: no card off-line): the themes side by side in one row, each its codes in two aligned columns under
# its label, a subtheme under its theme's codes in the same two columns, every gap the same, so the board ships tidy
TA_COLS = 2
TA_GAP = 2 * themes_mod.MARGIN
# the room the page keeps under a code card that stands for several extracts, which gets.card_height leaves out, so
# the page never pushes a row down to make it
TA_ROOM = 28
TA_THEME_GAP = 72


def ta_layout(themes: list[dict], groups: list[dict], texts: dict[str, str]) -> dict:
    """A board of `groups` (each theme's label, definition and lead cards, its subthemes inside) with every card
    placed on a grid: each top theme a column of its own, left to right in the plan's order, its codes two to a
    row under its label, then each subtheme's label and codes below them. The groups' ids are G1 on, the top themes
    first, then the subthemes, as a GETs board's are. Answers the board's cards, groups and set aside."""
    import gets as gets_mod

    body = TA_COLS * themes_mod.CARD_W + (TA_COLS - 1) * TA_GAP
    cards: dict[str, dict] = {}
    out: list[dict] = []
    ids = iter(f"G{n}" for n in range(1, 1000))
    tops = [(g, next(ids)) for g in groups]
    subs_of = {gid: [(s, next(ids)) for s in g["groups"]] for g, gid in tops}

    def grid(keys: list[str], x: float, y: float) -> float:
        for row in range(0, len(keys), TA_COLS):
            line = keys[row:row + TA_COLS]
            tall = 0
            for col, key in enumerate(line):
                cards[key] = {"x": round(x + col * (themes_mod.CARD_W + TA_GAP)), "y": round(y), "text": texts[key]}
                tall = max(tall, gets_mod.card_height(key, texts[key]) + TA_ROOM)
            y += tall + TA_GAP
        return y

    def label_h(g: dict, upper: bool, theme: dict) -> int:
        return themes_mod.label_size(g["label"], upper, int(bool(theme.get("note"))), g.get("description") or "", body)[1]

    x = 0.0
    for (g, gid), theme in zip(tops, themes):
        inner = subs_of[gid]
        y = label_h(g, bool(inner), theme) + themes_mod.LABEL_GAP
        y = grid(list(g["members"]), x + themes_mod.FRAME_X, y)
        held = []
        for (sub, sid), sub_theme in zip(inner, theme.get("subs") or []):
            y += themes_mod.FRAME_Y + label_h(sub, False, sub_theme) + themes_mod.LABEL_GAP
            y = grid(list(sub["members"]), x + themes_mod.FRAME_X, y) + themes_mod.FRAME_Y
            held.append({"id": sid, "label": sub["label"], "x": 0, "y": 0, "members": list(sub["members"])})
        out.append({"id": gid, "label": g["label"], "x": 0, "y": 0, "members": list(g["members"]) + [h["id"] for h in held]})
        out += held
        x += body + 2 * themes_mod.FRAME_X + TA_THEME_GAP
    return {"cards": cards, "groups": out, "discarded": []}


def build_ta_themes(root: Path, plan: dict) -> dict:
    """The Themes board across the three participants built into `root`: each theme and subtheme with its
    title, definition and note, each code's card under the theme the plan names, placed on a grid by `ta_layout`
    then saved through the Themes board's own save, which lays every extract of a code where its card
    stands (codes.unfold), and made the Current board, the clock at the plan's times. A code named under two
    themes, or one not in the list, is an error. Answers the file and its counts."""
    import codes as codes_mod
    import gets as gets_mod
    import i18n

    root = Path(root)
    books = ta_books(root)
    at = int(dt.datetime.fromisoformat(plan["made"]).timestamp()) * 1_000_000_000
    for book in books:
        os.utime(book["workbook"], ns=(at, at))
    with i18n.in_method("ta"):
        extracts = codes_mod.extracts_of(codes_mod.study_rows(books))
        by_code: dict[str, list[str]] = {}
        for x in extracts:
            by_code.setdefault(x["code"], []).append(gets_mod.card_of(x["case"], "es", x["key"]))
        names = {codes_mod.norm(c["name"]): c["name"] for c in plan["codes"]}
        leads: dict[str, str] = {}

        def lead(code_name: str) -> str:
            code = codes_mod.norm(code_name)
            if code not in names or code not in by_code:
                raise DemoError(f"The theme's code {code_name!r} is not in the list or on no extract.")
            if code in leads.values():
                raise DemoError(f"The code {code_name!r} is named under two themes.")
            key = min(by_code[code], key=codes_mod.key_order)
            leads[key] = code
            return key

        def group(theme: dict) -> dict:
            return {"label": theme["title"], "description": theme.get("definition") or "",
                    "members": [lead(c) for c in theme.get("codes") or []],
                    "groups": [group(sub) for sub in theme.get("subs") or []]}

        groups = [group(theme) for theme in plan["themes"]]
        with clock(plan["made"]):
            gets_mod.assemble(root, books, themes_mod.now_iso())
        laid = ta_layout(plan["themes"], groups, {k: names[code] for k, code in leads.items()})
        by_label = {g["label"]: g for g in laid["groups"]}
        if len(by_label) != len(laid["groups"]):
            raise DemoError("Two themes share a title.")

        def described(theme: dict) -> None:
            if theme.get("note"):
                by_label[theme["title"]]["note"] = theme["note"]
            if theme.get("definition"):
                by_label[theme["title"]][themes_mod.DESCRIPTION] = theme["definition"]
            for sub in theme.get("subs") or []:
                described(sub)

        for theme in plan["themes"]:
            described(theme)
        version = dict(laid, id=gets_mod.FIRST_BOARD, name=gets_mod.FIRST_NAME, note="", picks={}, rows={})
        with clock(plan["made"]):
            gets_mod.save(root, books, version)
        with clock(plan["chosen"]):
            gets_mod.version_op(root, books, "choose", {"id": gets_mod.FIRST_BOARD})
    return {"file": gets_mod.gets_path(root), "themes": len(plan["themes"]),
            "subthemes": sum(len(t.get("subs") or []) for t in plan["themes"]), "placed": len(leads),
            "not_placed": len(plan["codes"]) - len(leads)}


def build_ta_all(into: Path, demo: Path | None = None) -> dict:
    """The whole thematic analysis demo built into `into`, a folder that must not be there yet: its project file,
    the three participants, and the code list and the Themes board at its root. Answers each participant's files
    and counts, by name, the list under `codes` and the board's counts under `themes`."""
    into = Path(into)
    if into.exists():
        raise DemoError(f"{into} is there already, so nothing was built into it.")
    into.mkdir(parents=True)
    plan = read_plan(ta_dir(demo) / "source" / TA_THEMES)
    shutil.copyfile(ta_dir(demo) / PROJECT_FILE, into / PROJECT_FILE)
    built = {name: build_ta_case(name, into, demo) for name in CASES}
    built["codes"] = build_ta_codes(into, plan)
    built["themes"] = build_ta_themes(into, plan)
    return built


def ship_ta(force: bool = False, demo: Path | None = None, verbose: bool = True) -> dict:
    """The thematic analysis demo built and put where it ships: each participant's workbook in `demo/ta/pristine/`
    and its progress file in `pristine/Working/`, the code list and the Themes board's file in `pristine/`, and the
    same in the live demo, each participant in its folder and the two files at its root. Live workbooks already
    there are replaced only with `force`, and one open in Excel refuses the whole build."""
    ta = ta_dir(demo)
    lives = {name: ta / name / f"{name}{EN_ES}" for name in CASES}
    there = [live.name for live in lives.values() if live.exists()]
    if there and not force:
        raise DemoError(f"The thematic analysis demo's {there[0]} is already there. Pass --force to build it again.")
    for live in lives.values():
        wb_mod.guard_lock(live)
    pristine = ta / "pristine"
    with tempfile.TemporaryDirectory(prefix="demo-ta-built-") as tmp:
        built = build_ta_all(Path(tmp) / "ta", demo)
        (pristine / "Working").mkdir(parents=True, exist_ok=True)
        for name, live in lives.items():
            (live.parent / "Working").mkdir(parents=True, exist_ok=True)
            for source, folder in ((built[name]["workbook"], ""), (built[name]["progress"], "Working")):
                shutil.copyfile(source, pristine / folder / source.name)
                shutil.copyfile(source, live.parent / folder / source.name)
        for name in (GETS_FILE, CODES_FILE):
            shutil.copyfile(Path(tmp) / "ta" / name, pristine / name)
            shutil.copyfile(Path(tmp) / "ta" / name, ta / name)
    if verbose:
        for name in CASES:
            b = built[name]
            print(f"  {name}, thematic analysis: {b['extracts']} extracts, {b['codings']} codes on them")
        t = built["themes"]
        print(f"  Themes: {len(built['codes']['codes'])} codes, {t['placed']} in {t['themes']} themes and "
              f"{t['subthemes']} subthemes, {t['not_placed']} not placed")
    return built


# --------------------------------------------------------------------- main

def main() -> int:
    ap = argparse.ArgumentParser(description="Build the bundled demo, a finished IPA project, for the app.")
    ap.add_argument("--audio-only", action="store_true", help="rebuild only Juno's recording")
    ap.add_argument("--workbook-only", action="store_true",
                    help="build the three cases and the GETs with no recording, as --written does")
    ap.add_argument("--force", action="store_true", help="replace workbooks that are already there")
    ap.add_argument("--written", action="store_true",
                    help="build the three cases and the GETs, which needs no recording and no say, then the "
                         "thematic analysis demo")
    ap.add_argument("--ta", action="store_true", help="build the thematic analysis demo alone")
    args = ap.parse_args()
    if args.ta:
        try:
            print("Building the thematic analysis demo.")
            ship_ta(force=args.force)
        except (DemoError, wb_mod.WorkbookError) as exc:
            print(str(exc), file=sys.stderr)
            return 1
        print("Done.")
        return 0

    written = args.written or args.workbook_only
    if not written and not have("say"):
        print("This machine has no `say`, so the demo cannot be built here. It is macOS only.",
              file=sys.stderr)
        return 2
    try:
        if not written:
            print("Speaking the demo transcript.")
            build_recording(write_csv=not args.audio_only)
        if not args.audio_only:
            print("Building the demo.")
            ship_all(force=args.force)
            print("Building the thematic analysis demo.")
            ship_ta(force=args.force)
    except (DemoError, wb_mod.WorkbookError) as exc:
        print(str(exc), file=sys.stderr)
        return 1
    print("Done.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
