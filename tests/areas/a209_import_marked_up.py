from __future__ import annotations

import base64
import json
import shutil
import subprocess

import openpyxl

from . import support
from .support import check, line_of_js, skip
import idiograph_routes

# An invented interview on learning to sail, Sam asking, Nell answering, and Tobi, her brother, heard
# from the boat beside her. Every word made up.
ROWS = [
    ["Sam", "00:00:04", "What was the first day on the water like?", "", ""],
    ["Nell", "00:00:12", "Cold. I held the rope so hard my hands went white.", "grip as fear held in the body",
     "Holding on as a way of staying safe\n\nFeeling the cold as the sea's first word"],
    ["Tobi", "00:00:30", "She would not let go of it all morning.", "", ""],
    ["Sam", "00:01:02", "And later in the week?", "", ""],
    ["Nell", "00:01:15", "I let the boat lean. I stopped fighting it.", "leaning with, not against",
     "Trusting the boat to carry her"],
]
STATEMENTS_ONLY = ("Speaker,Time,Transcript,Experiential statements\n"
                   "Sam,00:00:04,What was the first day on the water like?,\n"
                   'Nell,00:00:12,"Cold. I held the rope so hard my hands went white.","Holding on as a way of staying safe\n'
                   'Feeling the cold as the sea\'s first word"\n'
                   "Sam,00:01:02,And later in the week?,\n"
                   "Nell,00:01:15,I let the boat lean. I stopped fighting it.,Trusting the boat to carry her\n")


def cells(path) -> dict:
    book = openpyxl.load_workbook(path)
    try:
        return {ws.title: [list(r) for r in ws.iter_rows(values_only=True)] for ws in book.worksheets}
    finally:
        book.close()


def test_import_marked_up(scratch):
    print("\n209. Work done elsewhere comes in marked up to any degree: statements straight to PETs, each speaker "
          "Interviewer, Participant or Other speaker in one case, every time format read or named, and the "
          "recording copied in with an offset playback adds, through the card and the API (20 October)")
    import cli
    import convert
    import rounds as rounds_mod
    import server as server_mod
    import workbook as wb_mod

    root = scratch / "a209"
    shutil.rmtree(root, ignore_errors=True)
    case = root / "P4 - Nell"
    source = case / "Source"
    source.mkdir(parents=True)
    (root / server_mod.PROJECT_FILE).write_text(json.dumps({
        "name": "Sailing, an import project", "agents": {"allowed": True, "at": "2026-10-20T09:00:00+01:00"}}), encoding="utf-8")
    (source / "statements.csv").write_text(STATEMENTS_ONLY, encoding="utf-8")
    book = openpyxl.Workbook()
    ws = book.active
    ws.append(["Speaker", "Time", "Transcript", "Exploratory notes", "Experiential statements"])
    for row in ROWS:
        ws.append(row)
    book.save(source / "all three.xlsx")
    (source / "boat.wav").write_bytes(b"RIFF\x24\x00\x00\x00WAVEfmt " + bytes(28))
    config = scratch / "a209-config.json"
    config.write_text(json.dumps({"root": str(root), "interviewer": "Sam"}), encoding="utf-8")
    kept = (server_mod.CONFIG_PATH, server_mod.ROOT_OVERRIDE, server_mod.STATE_MEMORY, server_mod.STATE_PATH)
    try:
        server_mod.ROOT_OVERRIDE, server_mod.STATE_MEMORY = str(root), {"recent": []}
        server_mod.STATE_PATH = scratch / "a209-state.json"
        server_mod.CONFIG_PATH = config

        def card(name, **body):
            return idiograph_routes.api_import(dict(body, path=str(source / name)))

        def files():
            return {p.relative_to(root).as_posix(): p.read_bytes() for p in sorted(root.rglob("*")) if p.is_file()}

        # ── A. statements in, straight to PETs, a transcript with statements only
        made = card("statements.csv", op="make")
        raw = server_mod.abs_path(made["source"]["path"])
        out = server_mod.abs_path(idiograph_routes.api_create({"path": str(raw)})["path"])
        read = wb_mod.read_case(out)
        rows = read["sheets"][0]["rows"]
        check("209: a transcript with statements and no notes lands with every statement on its passage, two in one "
              "cell split as the app splits them",
              [r["es"] for r in rows] == ["", "Holding on as a way of staying safe\nFeeling the cold as the sea's first word",
                                          "", "Trusting the boat to carry her"]
              and all(r["en"] == "" for r in rows), str([r["es"] for r in rows]))
        progress = rounds_mod.load_progress(out)
        summary = idiograph_routes.case_payload(out)["progress"]
        code, said, _ = cli.run(["--root", str(root), "--config", str(config), "statements", "P4 - Nell", "--json"])
        listed = support.plain(json.loads(said)) if code == 0 else {}
        check("209: so the case opens ready for PETs, its passages decided and its three statements there to place",
              summary["states"].get(f"{convert.SHEET}:3") == rounds_mod.HAS_CONTENT and progress is not None
              and code == 0 and len(listed.get("statements") or []) == 3, said[:300])
        # a second case for the next fixture, so each lands in its own workbook
        case2 = root / "P5 - Ada"
        (case2 / "Source").mkdir(parents=True)
        shutil.copy2(source / "all three.xlsx", case2 / "Source" / "all three.xlsx")
        shutil.copy2(source / "boat.wav", case2 / "Source" / "boat.wav")
        source2 = case2 / "Source"

        def card2(**body):
            return idiograph_routes.api_import(dict(body, path=str(source2 / "all three.xlsx")))

        # ── B. three speakers, their roles guessed then set, and all three marked up
        seen = card2(op="read")
        check("209: the card lists every speaker with a role, the interviewer guessed and every other speaker a Participant",
              [s["name"] for s in seen["speakers"]] == ["Sam", "Nell", "Tobi"]
              and seen["speaker_roles"] == {"Sam": "interviewer", "Nell": "participant", "Tobi": "participant"}
              and seen["case"] == "P5 - Ada" and not seen["said"], str(seen.get("speaker_roles")))
        two = card2(op="read", speakers={"Sam": "interviewer", "Nell": "interviewer", "Tobi": "participant"})
        none = card2(op="read", speakers={"Sam": "interviewer", "Nell": "other", "Tobi": "other"})
        check("209: two interviewers or no participant hold Make back in one line",
              two["said"] == convert.TWO_INTERVIEWERS and none["said"] == convert.NO_PARTICIPANT)
        before = sorted(p.name for p in root.iterdir() if p.is_dir())
        card2(op="make", speakers={"Sam": "Interviewer", "Nell": "Participant", "Tobi": "Other speaker"},
              audio=server_mod.rel_path(source2 / "boat.wav"), offset="-1.5")
        raw2 = source2 / "all three (converted).xlsx"
        out2 = server_mod.abs_path(idiograph_routes.api_create({"path": str(raw2)})["path"])
        sheet = wb_mod.read_case(out2)["sheets"][0]
        rows = sheet["rows"]
        stops = [r["name"] for r in rows if rounds_mod.is_stop(r, "Sam")]
        check("209: one transcript makes one case: Make writes no other case folder, the other speaker's turn stays "
              "in the case, marked, and is no stop",
              sorted(p.name for p in root.iterdir() if p.is_dir()) == before
              and [r["context"] for r in rows] == [False, False, True, False, False] and stops == ["Nell", "Nell"]
              and wb_mod.CONTEXT_HEADER in cells(out2)[convert.SHEET][0], str([(r["name"], r["context"]) for r in rows]))
        check("209: all three marked up land, each passage's notes and statements in their places, the other speaker's "
              "turn still open to them",
              rows[1]["en"] == "grip as fear held in the body"
              and rows[1]["es"] == "Holding on as a way of staying safe\nFeeling the cold as the sea's first word"
              and rows[4]["es"] == "Trusting the boat to carry her" and rows[2]["name"] == "Tobi", str(rows[1]))
        couple = card2(op="read", speakers={"Sam": "interviewer", "Nell": "participant", "Tobi": "participant"})
        turns, marks = convert.case_turns([("Sam", 1, "a?"), ("Nell", 2, "b"), ("Tobi", 3, "c")],
                                          {"Sam": "interviewer", "Nell": "participant", "Tobi": "participant"}, "Sam")
        check("209: two participants, a couple interviewed together, are one case, each passage under its speaker's name",
              (not couple["said"] or couple["said"].endswith("is already there.")) and couple["speaker_roles"]["Tobi"] == "participant"
              and turns == [("Sam", 1, "a?"), ("Nell", 2, "b"), ("Tobi", 3, "c")] and marks == [False, False, False])

        # ── C. the recording copied in, the offset beside it, read afresh as after a restart
        held = case2 / "Source" / convert.SHEET / "Source"
        check("209: the recording is copied where the player finds the sheet's, its offset beside it",
              (held / "Ada.wav").read_bytes() == (source2 / "boat.wav").read_bytes()
              and json.loads((held / "offset.json").read_text(encoding="utf-8")) == {"offset": -1.5})
        heard = idiograph_routes.api_audio({"path": str(out2), "sheet": convert.SHEET})
        check("209: the player's answer carries the offset, read from the case's file, so it holds across a restart",
              heard["found"] is True and heard["offset"] == -1.5, str(heard))
        before = files()
        dry = idiograph_routes.api_audio_offset({"path": str(out2), "sheet": convert.SHEET, "offset": "+2", "dry_run": True})
        check("209: the offset op's dry run answers the old and the new and writes nothing",
              dry["was"] == -1.5 and dry["offset"] == 2.0 and files() == before, str(dry))
        idiograph_routes.api_audio_offset({"path": str(out2), "sheet": convert.SHEET, "offset": "2,5"})
        check("209: the offset op keeps the new offset beside the recording",
              idiograph_routes.api_audio({"path": str(out2), "sheet": convert.SHEET})["offset"] == 2.5)
        for bad, word in (("soon", "words"), ("90000", "more than a day")):
            try:
                idiograph_routes.api_audio_offset({"path": str(out2), "sheet": convert.SHEET, "offset": bad})
                refused = ""
            except server_mod.WorkbookError as exc:
                refused = str(exc)
            check(f"209: an offset in {word} is refused in one line", refused == idiograph_routes.NOT_AN_OFFSET, refused)
        try:
            idiograph_routes.api_audio_offset({"path": str(out), "sheet": convert.SHEET, "offset": 1})
            refused = ""
        except server_mod.WorkbookError as exc:
            refused = str(exc)
        check("209: a sheet with no recording takes no offset", refused == f"No recording found for {convert.SHEET}.", refused)

        # ── D. every time format read, and one that cannot be named
        reads = {t: convert.time_seconds(t) for t in ("01:02:03", "1:02:03", "02:03", "2:03", "[00:01:02]", "(1:02)",
                                                       "00:01:02,500", "00:01:02.5", "62", "62.5", "62,5")}
        check("209: HH:MM:SS, H:MM:SS, MM:SS, M:SS, in brackets or not, with a full stop or a comma fraction, and seconds read",
              reads == {"01:02:03": 3723, "1:02:03": 3723, "02:03": 123, "2:03": 123, "[00:01:02]": 62, "(1:02)": 62,
                        "00:01:02,500": 62, "00:01:02.5": 62, "62": 62, "62.5": 62, "62,5": 62}, str(reads))
        check("209: frames at the frame rate given, 25 a second unless he says, a frame past it unread",
              convert.time_seconds("00:01:02:12") == 62 and convert.time_seconds("00:01:02:27") is None
              and convert.time_seconds("00:01:02:27", fps=30) == 62 and convert.time_found(["00:00:01:02", "00:00:03:04"]) == "frames")
        check("209: the format found is the one most times take, three-part and two-part HH:MM:SS",
              convert.time_found(["01:02", "03:04"]) == "ms" and convert.time_found(["1:01:02", "59:10"]) == "hms"
              and convert.time_found(["12", "13.5"]) == "seconds" and convert.time_found(["", None]) is None)
        check("209: a format set by hand reads only that format, a time with a fraction and one without reading each other",
              convert.time_seconds("01:02:03", "ms") is None and convert.time_seconds("02:03", "hms") is None
              and convert.time_seconds("75:10", "ms") == 4510 and convert.time_seconds("62", "seconds") == 62
              and convert.time_seconds("00:01:02,500", "hms") == 62 and convert.time_seconds("00:01:02", "fraction") == 62
              and convert.time_found(["00:01:02,500", "00:01:03,000", "00:01:04"]) == "fraction")
        odd = source / "odd times.csv"
        odd.write_text("Speaker,Time,Transcript\nSam,00:00:04,Ready?\nNell,0:0x:12,Yes.\nSam,00:01:02,Go on.\n", encoding="utf-8")
        found = card("odd times.csv", op="read")
        hand = card("odd times.csv", op="read", times={"format": "ms"})
        check("209: the card shows the format found, a time it cannot read named by its passage and in the preview, "
              "never dropped",
              found["time_found"] == "hms" and found["time_found_name"] == convert.TIME_FORMATS["hms"]
              and found["bad_times"] == [{"passage": 2, "time": "0:0x:12"}] and found["turns"][1]["bad"] == "0:0x:12"
              and found["turns"][1]["time"] == "" and found["count"] == 3, str(found.get("bad_times")))
        check("209: set by hand, MM:SS on HH:MM:SS times names each it cannot read",
              hand["timing"]["format"] == "ms" and [b["passage"] for b in hand["bad_times"]] == [1, 2, 3], str(hand.get("bad_times")))

        # ── E. the API: the import op's dry run answers what the card shows, and the offset op
        run = lambda *argv: cli.run(["--root", str(root), "--config", str(config), *argv])
        (case2 / "Source" / "odd times.csv").write_text(odd.read_text(encoding="utf-8"), encoding="utf-8")
        before = files()
        code, out_text, err = run("import", "P5 - Ada/Source/odd times.csv", "--dry-run", "--json",
                                  "--speakers", "Sam=Interviewer, Nell=Other speaker", "--time-format", "HH:MM:SS",
                                  "--audio", "P5 - Ada/Source/boat.wav", "--offset", "0.5")
        dry = support.plain(json.loads(out_text)) if code == 0 else {}
        check("209: the import op's dry run answers the speakers and their roles, the time format found and set, the "
              "times it cannot read, the one case it makes and the recording with its offset, writing nothing",
              code == 0 and files() == before and [(s["name"], s["role"]) for s in dry["speakers"]] == [("Sam", "Interviewer"), ("Nell", "Other speaker")]
              and dry["said"] == convert.NO_PARTICIPANT and dry["time_found"] == convert.TIME_FORMATS["hms"]
              and dry["time_format"] == convert.TIME_FORMATS["hms"]
              and dry["times_unread"] == [{"passage": 2, "time": "0:0x:12"}] and dry["cases"] == ["P5 - Ada"]
              and dry["audio"] == "P5 - Ada/Source/boat.wav" and dry["audio_offset"] == 0.5, (out_text or err)[:400])
        code, _, err = run("import", "P5 - Ada/Source/odd times.csv", "--dry-run", "--speakers", "Sam=Captain")
        code2, _, err2 = run("import", "P5 - Ada/Source/odd times.csv", "--dry-run", "--time-format", "fortnights")
        check("209: a speaker's role or a time format that is not one is refused in one line",
              code == 1 and "Captain is not a speaker's role." in err and code2 == 1 and "fortnights is not a time format." in err2,
              err + err2)
        code, out_text, err = run("import", "P5 - Ada/Source/odd times.csv", "--note", "Bring in the odd times",
                                  "--speakers", "Sam=Interviewer,Nell=Participant", "--json")
        check("209: the import op's apply writes the raw source as the card's Make does",
              code == 0 and (source2 / "odd times.xlsx").is_file(), (out_text or err)[:300])
        before = files()
        code, out_text, err = run("offset", "P5 - Ada", convert.SHEET, "-3", "--dry-run", "--json")
        code2, out2_text, _ = run("offset", "P5 - Ada", convert.SHEET, "-3", "--json")
        check("209: the offset op's dry run writes nothing, its apply keeps the new offset",
              code == 0 and support.plain(json.loads(out_text))["dry_run"] is True and support.plain(json.loads(out_text))["was"] == 2.5
              and code2 == 0 and idiograph_routes.api_audio({"path": str(out2), "sheet": convert.SHEET})["offset"] == -3.0,
              (out_text or err)[:300])

        # ── G. New project's rows take each speaker's role as the import card does (20 October)
        three = base64.b64encode(("Speaker,Time,Transcript\nSam,00:00:04,Ready?\nNell,00:00:09,Yes.\n"
                                  "Tobi,00:00:15,She was.\nNell,00:00:20,I was.\n").encode("utf-8")).decode("ascii")
        guessed = idiograph_routes.api_new_project({"op": "read", "name": "boat.csv", "data": three})
        two = idiograph_routes.api_new_project({"op": "read", "name": "boat.csv", "data": three,
                                          "speakers": {"Sam": "interviewer", "Nell": "interviewer", "Tobi": "other"}})
        check("209: New project's read answers each speaker's role, and two interviewers in one line",
              guessed["speaker_roles"] == {"Sam": "interviewer", "Nell": "participant", "Tobi": "participant"}
              and not guessed["said"] and two["said"] == convert.TWO_INTERVIEWERS, str(guessed.get("speaker_roles")))
        made = idiograph_routes.new_cases(scratch / "np-root", {"files": [{
            "name": "boat.csv", "data": three, "pseudonym": "Wren", "interview": "Interview",
            "speakers": {"Sam": "Interviewer", "Nell": "Participant", "Tobi": "Other speaker"}}]}, "Adam")
        sheet = idiograph_routes.case_sheet(made[0]["interviews"][0], "Adam", "Wren")
        check("209: New project writes the interviewer under Settings' name, the participant under the pseudonym, and "
              "another speaker under Other speaker, marked",
              [t[0] for t in sheet[1]] == ["Adam", "Wren", convert.CONTEXT, "Wren"] and sheet[4] == [False, False, True, False],
              str(sheet[1]))
        try:
            idiograph_routes.new_cases(scratch / "np-root", {"files": [{
                "name": "boat.csv", "data": three, "pseudonym": "Wren", "interview": "Interview",
                "speakers": {"Sam": "Other speaker", "Nell": "Other speaker", "Tobi": "Interviewer"}}]}, "Adam")
            refused = ""
        except server_mod.WorkbookError as exc:
            refused = str(exc)
        check("209: New project refuses a file with no participant in one line", refused == f"boat.csv: {convert.NO_PARTICIPANT}", refused)
    finally:
        server_mod.CONFIG_PATH, server_mod.ROOT_OVERRIDE, server_mod.STATE_MEMORY, server_mod.STATE_PATH = kept

    # ── F. the page: the offset added to playback's position, the playhead's taken off, and a step past another speaker
    node = shutil.which("node")
    if not node:
        skip("209: the player in node", "node is not installed")
        return
    app = support.text("family/static/shell.js", "apps/idiograph/static/distil.js")
    fn = lambda name: f"function {name}(" + app.split(f"function {name}(", 1)[1].split("\n}", 1)[0] + "\n}"
    script = scratch / "a209-player.js"
    script.write_text(
        "const player = { src: 'x', readyState: 1, currentTime: 0, getAttribute: () => 'x', addEventListener() {} };\n"
        "const $ = (id) => (id === 'player' ? player : {});\n"
        "const S = { audioOffset: -1.5, seekAt: null, cueAt: 0, flat: [], stops: [] };\n"
        "let marked = null;\nconst markTurnAt = (t) => { marked = t; };\nconst drawPlayer = () => {};\n"
        + line_of_js(app, "const heardAt = ") + "\n" + fn("cueAudio") + "\n" + fn("stepTo") + "\n"
        "cueAudio(10);\nconst cued = { at: player.currentTime, marked };\n"
        "S.audioOffset = 2; cueAudio(0.5);\nconst late = player.currentTime;\n"
        "const heard = heardAt(12.5);\n"
        "S.flat = [{ other: false }, { other: true }, { other: true }, { other: false }]; S.stops = [0, 1, 2, 3];\n"
        "console.log(JSON.stringify({ cued, late, heard, on: stepTo(0, 1), back: stepTo(3, -1), end: stepTo(3, 1) }));\n",
        encoding="utf-8")
    ran = subprocess.run([node, str(script)], capture_output=True, text=True, encoding="utf-8")
    if ran.returncode != 0:
        check("209: the player runs in node", False, ran.stderr.strip()[:400])
        return
    o = support.plain(json.loads(ran.stdout))
    check("209: playback adds the offset to a passage's time code, minus too, and the playhead takes it off",
          o["cued"] == {"at": 8.5, "marked": 10} and o["late"] == 2.5 and o["heard"] == 10.5, ran.stdout)
    check("209: a step from passage to passage passes another speaker's turns, either way",
          o["on"] == 3 and o["back"] == 0 and o["end"] == 4, ran.stdout)
