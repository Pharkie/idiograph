"""Area 372: the gate's participants'-words scan (wordsfix, 10 November 2026). Before the repository went
public a check was found using a participant's spoken lines as its fixture, so `./verify` refuses a tree
holding eight words running from a participant's turn, a statement, a quote or a PET's title of any case
the local gate file reaches, RED with reason participant-words, naming the file and a count, never a word.

The fixtures are invented: a study of an evening pottery class with three made-up participants, Quill, Tamsin
and Odile, an interviewer called Hazel, a second study with one more, Ines, reached through
`words_sources`, and a made-up tree for the gate."""
from __future__ import annotations

import csv
import json
import os
import shutil
from pathlib import Path

import openpyxl

from .support import check
from .a271_loose_ends import load_gate

HEADER = ["Name", "Timestamp", "Experiential statements", "Transcript", "Exploratory notes", "Key quotes"]
# each line eight words or more, so each makes runs of its own
ROWAN = "The wheel kept pulling my bowl sideways until I laughed out loud at it"
STATEMENT = "Laughing at the clay when the wheel will not obey her hands"
QUOTE = "my thumbs finally found the centre and the whole lump went quiet"
ASKED = "Could you take me back to the first evening at the wheel please"
COMMON = "and then the kiln door opened and there they all were"
NOTE = "Quill seems to treat the failure as play rather than as a loss of face"
ARCHIVED = "an older copy of the interview that the archive keeps for safety only"
INES = "I don't mind the glaze running, it's the waiting overnight I can't bear"
TITLE = "Waiting through the night for the kiln as a small rehearsal of trust"


def book(path: Path, rows: list[list]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Interview"
    ws.append(HEADER)
    for row in rows:
        ws.append(row)
    wb.save(path)


def make_sources(academy: Path) -> list[Path]:
    main = academy / "Pottery" / "Main Data"
    book(main / "P1 - Quill" / "P1 Quill - EN & ES.xlsx", [
        ["Hazel", "00:00:05", None, ASKED, None, None],
        ["Quill", "00:00:20", STATEMENT, ROWAN + ", and " + QUOTE + ".", NOTE, f'"{QUOTE}"'],
        ["Quill", "00:01:10", None, COMMON, None, None],
    ])
    book(main / "P1 - Quill" / "_Archive" / "P1 Quill - EN & ES (old).xlsx", [["Quill", "00:00:20", None, ARCHIVED, None, None]])
    book(main / "P2 - Tamsin" / "P2 Tamsin - EN & ES.xlsx", [["Tamsin", "00:00:12", None, COMMON, None, None]])
    book(main / "P3 - Odile" / "Source" / "P3 Odile - transcript.xlsx", [["Odile", "00:00:09", None, COMMON, None, None]])
    ines = academy / "Glaze study" / "Ines"
    ines.mkdir(parents=True)
    with (ines / "Ines_T1_Transcript.csv").open("w", encoding="utf-8", newline="") as handle:
        out = csv.writer(handle)
        out.writerow(["Speaker", "Time", "Experiential statements", "Text", "Exploratory notes", "Key quotes"])
        out.writerow(["Hazel", "00:00:03", "", ASKED, "", ""])
        out.writerow(["Ines", "00:00:15", "", INES, "", ""])
    (ines / "Working").mkdir()
    board = {"schema": 2, "boards": [{"id": "v1", "name": "Board 1", "cards": {},
                                      "groups": [{"id": "g1", "label": TITLE, "members": []}]}]}
    (ines / "Working" / "Ines - EN & ES.themes.json").write_text(json.dumps(board), encoding="utf-8")
    return sorted(p for p in academy.rglob("*") if p.is_file())


def make_tree(tree: Path) -> dict[str, str]:
    files = {
        "tests/fixture.py": f'LINE = "{ROWAN}."\n',
        "docs/notes.md": f"# Notes\n\n{COMMON}. {NOTE}. {ARCHIVED}.\n",
        # the words with their case, apostrophes and punctuation changed are the same words
        "demo/data.json": json.dumps({"said": INES.upper().replace("'", "’").replace(",", " ;")},
                                     ensure_ascii=False),
        "static/board.js": f"const title = '{TITLE.lower()}';\n",
        "asked.md": f"{ASKED}?\n",
        "photo.png": f"{ROWAN}\0\n",
    }
    for rel, text in files.items():
        (tree / rel).parent.mkdir(parents=True, exist_ok=True)
        (tree / rel).write_text(text, encoding="utf-8")
    book(tree / "demo" / "sheet.xlsx", [["Someone", "00:00:01", STATEMENT, "Invented words alone.", None, None]])
    return files


def test_participant_words(scratch: Path):
    print("\n372. The gate's participants'-words scan: a participant's words in the tree RED, by file and count, "
          "the interviewer, notes, archives and common speech passed over, the runs cached as hashes, no data a skip")
    gate = load_gate()
    base = scratch / "a372"
    shutil.rmtree(base, ignore_errors=True)
    academy, tree, cache = base / "Academy", base / "tree", base / "cache"
    sources = make_sources(academy)
    before = {p: (p.read_bytes(), p.stat().st_mtime_ns) for p in sources}
    files = make_tree(tree)
    tracked = sorted(files) + ["demo/sheet.xlsx"]
    view = gate.View(root=tree, tracked=tracked, staged={}, changed=[])
    kept = (gate.ACADEMY, gate.MAIN_DATA, gate.LOCAL, gate.WORDS_CACHE_DIR, gate.words_in_file)
    try:
        gate.ACADEMY, gate.MAIN_DATA, gate.WORDS_CACHE_DIR = academy, academy / "Pottery" / "Main Data", cache
        gate.LOCAL = {"words_sources": ["Glaze study"], "interviewer": "Hazel"}

        ok, said, reason = gate.check_participant_words(view)
        check("372: the full gate refuses a tree holding a participant's words, RED with reason participant-words, "
              "naming each file and its count: a turn, a statement in a tracked workbook, a second study's turn "
              "with its case and apostrophes changed, and a PET's title from a board file",
              ok is False and reason == "participant-words"
              and "tests/fixture.py: 7 run(s)" in said and "demo/sheet.xlsx: 5 run(s)" in said
              and "demo/data.json: 6 run(s)" in said and "static/board.js: 6 run(s)" in said, said)
        check("372: the interviewer's turns, the exploratory notes, an _Archive's copy, words in three cases and a "
              "picture are passed over",
              "docs/notes.md" not in said and "asked.md" not in said and "photo.png" not in said, said)
        words = {w for line in (ROWAN, STATEMENT, INES, TITLE) for w in gate.words_of(line) if len(w) > 4}
        check("372: the gate's words name no word of what it found, nor the case",
              not any(w in said.lower() for w in words) and "quill" not in said.lower() and "ines" not in said.lower(),
              said)
        stored = b"".join(p.read_bytes() for p in cache.iterdir())
        check("372: the cache holds the runs as hashes and each file's count, never a word",
              sorted(p.name for p in cache.iterdir()) == [gate.WORDS_MEMO_NAME, gate.WORDS_CACHE_NAME]
              and not any(w.encode() in stored.lower() for w in words), str(len(stored)))
        check("372: the sources are read and left as they were",
              all(p.read_bytes() == data and p.stat().st_mtime_ns == when for p, (data, when) in before.items()))

        def refuse(*_args):
            raise AssertionError("a source read")
        gate.words_in_file = refuse
        ok2, said2, reason2 = gate.check_participant_words_cached(view)
        check("372: the fast gate's run with the sources unchanged reads no workbook and finds the same, from the cache",
              ok2 is False and reason2 == "participant-words" and said2.split("\n")[1:] == said.split("\n")[1:]
              and "cached" in said2, said2)
        os.utime(sources[0], ns=(before[sources[0]][1] + 10**9, before[sources[0]][1] + 10**9))
        ok3, said3, _ = gate.check_participant_words_cached(view)
        check("372: a source changed since, and the fast gate skips, saying the full gate reads them",
              ok3 is True and "the full gate reads them, skipped" in said3, said3)
        gate.words_in_file = kept[4]
        ok4, said4, _ = gate.check_participant_words(view)
        check("372: and the full gate reads them again", ok4 is False and "runs read from" in said4, said4)

        clean = {rel: text for rel, text in files.items()
                 if rel not in ("tests/fixture.py", "demo/data.json", "static/board.js")}
        ok5, said5, reason5 = gate.check_participant_words(gate.View(root=tree, tracked=sorted(clean), staged={},
                                                                     changed=[]))
        check("372: the tree without them passes", ok5 is True and reason5 is None and "clean" in said5, said5)

        gate.LOCAL = {"words_sources": ["Glaze study"]}
        ok6, said6, _ = gate.check_participant_words(view)
        check("372: with no interviewer named, Hazel's turns count as words too",
              ok6 is False and "asked.md: 6 run(s)" in said6, said6)

        gate.ACADEMY = gate.MAIN_DATA = None
        gate.LOCAL = {}
        ok7, said7, reason7 = gate.check_participant_words(view)
        check("372: with no case data reachable the scan skips and says so",
              ok7 is True and reason7 is None and "no case data reachable" in said7 and "skipped" in said7, said7)
        check("372: the fast gate and ./commit run the scan from the cache, the full gate reading the sources",
              ("participant words", gate.check_participant_words_cached) in gate.FAST_CHECKS)
    finally:
        gate.ACADEMY, gate.MAIN_DATA, gate.LOCAL, gate.WORDS_CACHE_DIR, gate.words_in_file = kept
