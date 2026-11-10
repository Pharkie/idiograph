from __future__ import annotations

import inspect
import io
import json
import re
import shutil
from pathlib import Path

import openpyxl

import rounds as rounds_mod
import workbook as wb_mod
from workbook import WorkbookError

from . import support
from .support import check, json_strings, line_of_js, skip
import idiograph_routes


def test_new_project(scratch):
    print("\n102. New project (204): a folder he picks, transcripts dropped onto the card in six formats, a case "
          "for each pseudonym with its named interviews, the refusals, the two-part setting and the cases opening")
    import base64
    import datetime as dt
    import subprocess
    import zipfile
    import convert
    import server as server_mod

    b64 = lambda data: base64.b64encode(data if isinstance(data, bytes) else data.encode("utf-8")).decode("ascii")
    flat = lambda text: " ".join(str(text).split())

    # ── A. the six formats, every word invented: Sam asks, and each participant's label is a made-up
    # full name, which must never reach a workbook
    vtt = ("WEBVTT\n\n00:00:01.000 --> 00:00:04.000\n<v Sam Okafor>How did the first week with the hens go?</v>\n\n"
           "00:00:05.000 --> 00:00:09.000\n<v Rhea Example>Slowly. They hid in the coop.</v>\n\n"
           "00:00:10.000 --> 00:00:12.000\n<v Sam Okafor>And you?</v>\n\n"
           "00:00:13.000 --> 00:00:16.000\n<v Rhea Example>I checked on them every hour.</v>\n")
    srt = ("1\n00:00:02,000 --> 00:00:04,000\nSam: Two days on, how are they?\n\n"
           "2\n00:00:05,000 --> 00:00:08,000\nRhea: Bolder. One followed me in.\n\n"
           "3\n00:00:09,000 --> 00:00:10,000\nSam: Into the house?\n\n"
           "4\n00:00:11,000 --> 00:00:13,000\nRhea: Into the kitchen, yes.\n")
    txt = ("Sam: [00:00:03] What is the morning like now?\nTobi Example: [00:00:07] Eggs first, then tea.\n"
           "Sam: [00:01:02] Why that order?\nTobi Example: [00:01:05] The hens are louder than the kettle.\n")
    csv_text = ("Speaker,Start,Text\nSam,0:03,Where do they sleep?\nLin Example,0:08,On the high perch.\n"
                "Sam,0:15,All of them?\nLin Example,0:19,All but the smallest.\n")
    book = openpyxl.Workbook()
    book.active.append(["Who", "When", "What was said"])
    for row in (["Sam", dt.time(0, 0, 4), "Do they have names?"], ["Oda Example", dt.time(0, 0, 9), "Two of them do."],
                ["Sam", dt.time(0, 0, 20), "Which two?"], ["Oda Example", dt.time(0, 0, 25), "The loud ones."]):
        book.active.append(row)
    sheet_bytes = io.BytesIO()
    book.save(sheet_bytes)
    book.close()
    w = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
    para = lambda text, extra="": (f'<w:p><w:pPr><w:tabs><w:tab w:val="left" w:pos="720"/></w:tabs></w:pPr>{extra}'
                                   f'<w:r><w:t xml:space="preserve">{text}</w:t></w:r></w:p>')
    body = (para("Sam: [00:00:05] What did the winter change?")
            + para("Ivo Example: [00:00:11] The light.", '<w:del w:id="1"><w:r><w:delText>struck words</w:delText></w:r></w:del>')
            + '<w:p><w:r><w:t>Less of it,</w:t><w:br/><w:t>and fewer eggs.</w:t></w:r></w:p>'
            + para("Sam: [00:00:30] And for you?") + para("Ivo Example: [00:00:34] A quieter house."))
    document = f'<?xml version="1.0" encoding="UTF-8"?><w:document xmlns:w="{w}"><w:body>{body}<w:sectPr/></w:body></w:document>'
    docx_bytes = io.BytesIO()
    with zipfile.ZipFile(docx_bytes, "w") as z:
        z.writestr("[Content_Types].xml", '<?xml version="1.0"?><Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types"/>')
        z.writestr("word/document.xml", document)
    originals = {"Initial.vtt": vtt.encode("utf-8"), "follow up.srt": srt.encode("utf-8"),
                 "walk notes.txt": txt.encode("utf-8"), "table.csv": csv_text.encode("utf-8"),
                 "sheet.xlsx": sheet_bytes.getvalue(), "talk T2.docx": docx_bytes.getvalue()}
    T = lambda turns: [tuple(t) for t in turns]
    word = convert.read_data("talk T2.docx", originals["talk T2.docx"])
    check("102: a Word file is read with zipfile and the XML parser, a paragraph a line as plain text reads, a line break "
          "carrying the turn on, and a tab stop or a tracked deletion never taken for words",
          word["kind"] == "docx" and T(word["turns"]) == [
              ("Sam", 5, "What did the winter change?"), ("Ivo Example", 11, "The light. Less of it, and fewer eggs."),
              ("Sam", 30, "And for you?"), ("Ivo Example", 34, "A quieter house.")], str(word["turns"]))
    lines = []
    for name, data in (("noise.docx", b"PK\x03\x04 not a zip"), ("empty.docx", docx_bytes.getvalue()[:40]),
                       ("letter.pdf", b"%PDF-1.4")):
        try:
            convert.read_data(name, data)
            lines.append(None)
        except convert.Unreadable as exc:
            lines.append(str(exc))
    entity = io.BytesIO()
    with zipfile.ZipFile(entity, "w") as z:
        z.writestr("word/document.xml", '<?xml version="1.0"?><!DOCTYPE d [<!ENTITY a "aaaa">]><d>&a;</d>')
    try:
        convert.read_data("entity.docx", entity.getvalue())
        lines.append(None)
    except convert.Unreadable as exc:
        lines.append(str(exc))
    check("102: a file that is no Word document, a format it does not read and a body declaring entities each say one line",
          lines == [f"Idiograph could not read any passages from {n}." for n in ("noise.docx", "empty.docx", "letter.pdf", "entity.docx")],
          str(lines))
    every = {name: convert.read_data(name, data) for name, data in originals.items()}
    check("102: the six formats read from their contents alone, as the page sends them, each with four turns",
          {n: r["kind"] for n, r in every.items()} == {"Initial.vtt": "vtt", "follow up.srt": "srt", "walk notes.txt": "txt",
                                                       "table.csv": "csv", "sheet.xlsx": "xlsx", "talk T2.docx": "docx"}
          and all(len(r["turns"]) == 4 for r in every.values()) and ".docx" in convert.FORMATS,
          str({n: len(r["turns"]) for n, r in every.items()}))
    guesses = {n: convert.interview_of(n) for n in ("Initial.vtt", "follow up.srt", "talk T2.docx", "P3_day-2.txt",
                                                     "Interview 2.csv", "x 2d.xlsx", "Rhea Example.vtt", "walk notes.txt")}
    check("102: the interview's name is guessed from fixed words in the file's name, and a person's name lends it nothing",
          guesses == {"Initial.vtt": "Initial", "follow up.srt": "Follow-up", "talk T2.docx": "T2", "P3_day-2.txt": "Day 2",
                      "Interview 2.csv": "Interview 2", "x 2d.xlsx": "2d", "Rhea Example.vtt": "Interview",
                      "walk notes.txt": "Interview"}, str(guesses))
    check("102: a new case's turns: the interviewer's under Settings' name, every other speaker's under the pseudonym",
          [t[0] for t in convert.as_case(every["Initial.vtt"]["turns"], "Sam Okafor", "Quill", "Wren")] == ["Quill", "Wren", "Quill", "Wren"]
          and {t[0] for t in convert.as_case(every["Initial.vtt"]["turns"], "", "Quill", "Wren")} == {"Wren"}
          and convert.as_case([("Sam", 1, "Hi?")], "Sam", "", "Wren")[0][0] == convert.INTERVIEWER == "Interviewer")

    # ── B. Make, in scratch settings, from a folder chosen in a stand-in for the dialog
    base = scratch / "new-project-102"
    shutil.rmtree(base, ignore_errors=True)
    folder = base / "Hens study"
    folder.mkdir(parents=True)
    held_dir = base / "originals"
    held_dir.mkdir()
    for name, data in originals.items():
        (held_dir / name).write_bytes(data)
    marks = {p.name: (p.read_bytes(), p.stat().st_mtime_ns) for p in held_dir.iterdir()}
    cfg_file = scratch / "new-project-102-config.json"
    cfg_file.write_text(json.dumps({"projects": [], "interviewer": "Quill"}), encoding="utf-8")
    live_config = server_mod.CONFIG_PATH.read_bytes() if server_mod.CONFIG_PATH.exists() else None
    kept = (server_mod.CONFIG_PATH, server_mod.ROOT_OVERRIDE, server_mod.STATE_PATH, server_mod.STATE_MEMORY,
            server_mod.PLATFORM, server_mod.PICK_FOLDER, idiograph_routes.add_project, wb_mod.create_from_source)

    def tree(at: Path) -> dict:
        # each path with slashes on any system, and a lock file never read, since Windows refuses a
        # read of a file another holds locked (14 October)
        return {p.relative_to(at).as_posix(): (p.read_bytes() if p.is_file() and p.suffix != ".lock" else None)
                for p in sorted(at.rglob("*"))}

    def files_for(*rows):
        return [{"name": n, "data": b64(originals[n]), "pseudonym": who, "interview": convert.interview_of(n),
                 "interviewer": asks, **more} for n, who, asks, more in rows]

    six = [("Initial.vtt", "Wren", "Sam Okafor", {}), ("follow up.srt", "Wren", "Sam", {}), ("walk notes.txt", "Ash", "Sam", {}),
           ("table.csv", "Fern", "Sam", {}), ("sheet.xlsx", "Moss", "Sam", {}), ("talk T2.docx", "Reed", "Sam", {})]

    def refusal(at: Path, body: dict) -> str:
        before, settings = tree(at), cfg_file.read_bytes()
        try:
            idiograph_routes.api_new_project(body)
            return "made"
        except WorkbookError as exc:
            return str(exc) if tree(at) == before and cfg_file.read_bytes() == settings else "written: " + str(exc)

    try:
        server_mod.CONFIG_PATH, server_mod.ROOT_OVERRIDE = cfg_file, None
        server_mod.STATE_PATH, server_mod.STATE_MEMORY = scratch / "new-project-102-state.json", {"recent": []}
        server_mod.PLATFORM = "darwin"
        asked = []
        server_mod.PICK_FOLDER = lambda prompt=None: (asked.append(prompt), folder)[1]
        chosen = idiograph_routes.api_new_project({"op": "folder"})
        check("102: Choose opens the Mac's folder dialog with its own prompt, and answers the folder, its next number and its name",
              asked == [idiograph_routes.NEW_PROMPT] == ["Choose the folder for the new project."]
              and chosen == {"chosen": True, "folder": str(folder.resolve()), "next": 1, "name": "Hens study",
                             "research_question": ""}
              and not (folder / server_mod.PROJECT_FILE).exists(), str(chosen))
        server_mod.PICK_FOLDER = lambda prompt=None: None
        server_mod.PLATFORM = "linux"
        try:
            idiograph_routes.api_new_project({"op": "folder"})
            off = None
        except WorkbookError as exc:
            off = str(exc)
        check("102: a cancelled dialog answers nothing chosen, and off a Mac the folder is typed",
              (server_mod.PLATFORM == "linux") and off == server_mod.NO_DIALOG
              and idiograph_routes.api_new_project({"op": "folder", "path": str(folder)})["folder"] == str(folder.resolve()))
        server_mod.PLATFORM = "darwin"
        check("102: and on a Mac the dialog's Cancel adds and writes nothing", idiograph_routes.api_new_project({"op": "folder"}) == {"chosen": False})
        read = idiograph_routes.api_new_project({"op": "read", "name": "Initial.vtt", "data": b64(originals["Initial.vtt"])})
        check("102: read answers a dropped file as the import card's read does, with its interview's name guessed",
              read["count"] == 4 and read["interviewer"] == "Sam Okafor" and read["interview"] == "Initial"
              and [s["name"] for s in read["speakers"]] == ["Sam Okafor", "Rhea Example"] and read["said"] is None
              and read["kind"] == "vtt" and read["file"] == "Initial.vtt" and "pseudonym" not in read, str(read)[:200])
        table = idiograph_routes.api_new_project({"op": "read", "name": "table.csv", "data": b64(originals["table.csv"]),
                                            "columns": {"name": "", "ts": 1, "text": 2}})
        bad = idiograph_routes.api_new_project({"op": "read", "name": "noise.docx", "data": b64(b"PK\x03\x04 nothing")})
        check("102: a table's columns read as chosen, and a file that cannot be read says its one line",
              table["columns"] == ["Speaker", "Start", "Text"] and {t["name"] for t in table["turns"]} == {"Speaker"}
              and bad["said"] == "Idiograph could not read any passages from noise.docx." and bad["count"] == 0)

        made = idiograph_routes.api_new_project({"op": "make", "folder": str(folder), "name": "Keeping hens",
                                           "research_question": "How do people experience keeping hens at home?",
                                           "files": files_for(*six)})
        labels = ["P1 - Wren", "P2 - Ash", "P3 - Fern", "P4 - Moss", "P5 - Reed"]
        check("102: Make answers every project with the one made and its cases by label, numbered from 1 in the order they come",
              made["made"] is True and made["cases"] == labels and made["project"]["name"] == "Keeping hens"
              and [p["name"] for p in made["projects"]] == ["Keeping hens"], str(made.get("cases")))
        wren = folder / "P1 - Wren"
        expected = {".idiograph.lock", server_mod.PROJECT_FILE}
        for label, n, who, interviews in (("P1 - Wren", 1, "Wren", [("Initial", ".vtt"), ("Follow-up", ".srt")]),
                                          ("P2 - Ash", 2, "Ash", [("Interview", ".txt")]),
                                          ("P3 - Fern", 3, "Fern", [("Interview", ".csv")]),
                                          ("P4 - Moss", 4, "Moss", [("Interview", ".xlsx")]),
                                          ("P5 - Reed", 5, "Reed", [("T2", ".docx")])):
            expected |= {label, f"{label}/Source", f"{label}/P{n} {who} - EN & ES.xlsx", f"{label}/Source/P{n} {who} - transcript.xlsx"}
            for interview, ext in interviews:
                expected |= {f"{label}/Source/{interview}", f"{label}/Source/{interview}/P{n}-{interview}{ext}"}
        check("102: each case is a folder P<n> - Pseudonym, the copies in Source/<interview>/, the raw source and the "
              "annotated workbook, and nothing else is written",
              set(tree(folder)) == expected, str(sorted(set(tree(folder)) ^ expected)))
        copies = {"Initial.vtt": wren / "Source" / "Initial" / "P1-Initial.vtt",
                  "follow up.srt": wren / "Source" / "Follow-up" / "P1-Follow-up.srt",
                  "talk T2.docx": folder / "P5 - Reed" / "Source" / "T2" / "P5-T2.docx"}
        check("102: each copy is the file as dropped, byte for byte, and the originals are untouched where they lie",
              all(p.read_bytes() == originals[n] for n, p in copies.items())
              and {p.name: (p.read_bytes(), p.stat().st_mtime_ns) for p in held_dir.iterdir()} == marks)
        raw = openpyxl.load_workbook(wren / "Source" / "P1 Wren - transcript.xlsx")
        annotated = openpyxl.load_workbook(wren / "P1 Wren - EN & ES.xlsx")
        check("102: two files under one pseudonym are one case of two named interviews, a sheet each, raw and annotated",
              raw.sheetnames == ["Initial", "Follow-up"] and annotated.sheetnames == ["Initial", "Follow-up"]
              and all(wb_mod.is_raw_source(wb_mod.detect_columns(ws)) for ws in raw.worksheets)
              and [c.value for c in annotated["Initial"][1]] == wb_mod.HEADER, str(annotated.sheetnames))
        raw.close()
        annotated.close()
        names, cells = set(), []
        for label in labels:
            n, who = label.split(" - ")
            for path in (folder / label / f"{n} {who} - EN & ES.xlsx", folder / label / "Source" / f"{n} {who} - transcript.xlsx"):
                wb = openpyxl.load_workbook(path)
                for ws in wb.worksheets:
                    names |= {ws.cell(r, 1).value for r in range(2, ws.max_row + 1)}
                    cells += [str(c.value) for row in ws.iter_rows() for c in row if c.value is not None]
                    cells += [str(c.fill.fill_type) for row in ws.iter_rows() for c in row if c.fill.fill_type]
                wb.close()
        leaked = [c for c in cells if any(n in c for n in ("Rhea", "Tobi", "Lin Example", "Oda", "Ivo", "Okafor", "Example"))]
        check("102: the interviewer's turns are under Settings' name and every participant's under the pseudonym, so no label "
              "from a recording reaches a workbook, and no cell carries a fill",
              names == {"Quill", "Wren", "Ash", "Fern", "Moss", "Reed"} and not leaked
              and not any(c in ("solid", "gray125", "darkGray") for c in cells), str(sorted(n for n in names if n))[:200])
        stored = json.loads(cfg_file.read_text(encoding="utf-8"))
        held = json.loads((folder / server_mod.PROJECT_FILE).read_text(encoding="utf-8"))
        check("102: the folder is added once, through add_project, and its project file has the name and the question",
              len([p for p in stored["projects"] if server_mod.same_folder(server_mod.configured(p["root"]), folder)]) == 1
              and len(stored["projects"]) == 1 and stored["interviewer"] == "Quill"
              and held["name"] == "Keeping hens" and held["research_question"] == "How do people experience keeping hens at home?"
              and "updated" in held, str(stored["projects"]))
        listed = idiograph_routes.api_cases({})
        section = listed["projects"][0]
        check("102: the project stands among the home screen's sections, a row for each case",
              section["project"]["name"] == "Keeping hens" and [c["case"] for c in section["participants"]] == labels
              and all(c["path"] and c["path"].endswith("EN & ES.xlsx") for c in section["participants"]),
              str([c["case"] for c in section["participants"]]))
        opened = []
        for card in section["participants"]:
            case = idiograph_routes.api_open({"path": card["path"]})
            stops = [r for s in case["sheets"] for r in s["rows"] if rounds_mod.is_stop(r, "Quill")]
            opened.append((card["case"], [s["name"] for s in case["sheets"]], {r["name"] for r in stops}, len(stops)))
        check("102: each case opens on Experiential statements, its stops the participant's turns under the pseudonym",
              opened == [("P1 - Wren", ["Initial", "Follow-up"], {"Wren"}, 4), ("P2 - Ash", ["Interview"], {"Ash"}, 2),
                         ("P3 - Fern", ["Interview"], {"Fern"}, 2), ("P4 - Moss", ["Interview"], {"Moss"}, 2),
                         ("P5 - Reed", ["T2"], {"Reed"}, 2)], str(opened))

        # ── C. the refusals, each one line, each writing nothing
        other = base / "Hens two"
        other.mkdir()
        one = lambda *rows, **more: dict({"op": "make", "folder": str(other), "name": "Hens two", "files": files_for(*rows)}, **more)
        said = {
            "none": refusal(other, {"op": "make", "folder": str(other), "files": []}),
            "nameless": refusal(other, one(("walk notes.txt", "", "Sam", {}))),
            "lower": refusal(other, one(("walk notes.txt", "ash", "Sam", {}))),
            "two words": refusal(other, one(("walk notes.txt", "Ash Tree", "Sam", {}))),
            "interviewer": refusal(other, one(("walk notes.txt", "Quill", "Sam", {}))),
            "no interview": refusal(other, one(("walk notes.txt", "Ash", "Sam", {"interview": " "}))),
            "bad interview": refusal(other, one(("walk notes.txt", "Ash", "Sam", {"interview": "a/b"}))),
            "same interview": refusal(other, one(("Initial.vtt", "Wren", "Sam Okafor", {}),
                                                 ("follow up.srt", "Wren", "Sam", {"interview": "initial"}))),
            "one number": refusal(other, one(("walk notes.txt", "Ash", "Sam", {"number": 3}), ("table.csv", "Fern", "Sam", {"number": 3}))),
            "two numbers": refusal(other, one(("Initial.vtt", "Wren", "Sam Okafor", {"number": 1}),
                                              ("follow up.srt", "Wren", "Sam", {"number": 2}))),
            "bad number": refusal(other, one(("walk notes.txt", "Ash", "Sam", {"number": "x"}))),
            "unreadable": refusal(other, dict(one(("walk notes.txt", "Ash", "Sam", {})),
                                              files=[{"name": "noise.docx", "data": b64(b"PK\x03\x04 nothing"), "pseudonym": "Ash",
                                                      "interview": "Interview"}])),
            "pdf": refusal(other, dict(one(("walk notes.txt", "Ash", "Sam", {})),
                                       files=[{"name": "letter.pdf", "data": b64(b"%PDF-1.4"), "pseudonym": "Ash", "interview": "Interview"}])),
            "a project": refusal(folder, dict(one(("walk notes.txt", "Ash", "Sam", {})), folder=str(folder))),
            "nowhere": refusal(other, dict(one(("walk notes.txt", "Ash", "Sam", {})), folder=str(base / "none"))),
            # a page from before 9 October sends the two-part setting and a second part, both passed over, so
            # the refusal is the one the rest of the row earns
            "no second": refusal(other, one(("walk notes.txt", "", "Sam", {}), second_part=True)),
            "lower second": refusal(other, one(("walk notes.txt", "Ash", "Sam", {"second": "low", "interview": " "}), second_part=True)),
            "two seconds": refusal(other, one(("Initial.vtt", "Wren", "Sam Okafor", {"second": "Al" + "der", "number": 1}),
                                              ("follow up.srt", "Wren", "Sam", {"second": "Be" + "ech", "number": 2}), second_part=True)),
            "op": refusal(other, {"op": "remake"}),
        }
        (other / "P1 - Wren").mkdir()
        (other / "P2 - Owl").mkdir()
        (other / "P6 - Ash").mkdir()
        said["folder there"] = refusal(other, one(("Initial.vtt", "Wren", "Sam Okafor", {"number": 1})))
        said["number taken"] = refusal(other, one(("table.csv", "Fern", "Sam", {"number": 2})))
        said["case there"] = refusal(other, one(("walk notes.txt", "Ash", "Sam", {})))
        server_mod.ROOT_OVERRIDE = str(folder)
        said["one run"] = refusal(other, one(("walk notes.txt", "Ash", "Sam", {})))
        server_mod.ROOT_OVERRIDE = None
        want = {
            "none": "Drop a transcript first.",
            "nameless": "Give walk notes.txt a pseudonym.",
            "lower": "Make the pseudonym for walk notes.txt one capitalised word.",
            "two words": "Make the pseudonym for walk notes.txt one capitalised word.",
            "interviewer": "Quill is the interviewer's name in Settings, so it cannot be a pseudonym.",
            "no interview": "Give walk notes.txt an interview name.",
            "bad interview": "Make the interview name for walk notes.txt 31 characters or fewer, with none of \\ / : * ? [ ].",
            "same interview": "Wren has two interviews named initial.",
            "one number": "P3 is given to both Ash and Fern.",
            "two numbers": "Wren's interviews carry two numbers, P1 and P2.",
            "bad number": "Make the number for walk notes.txt a whole number from 1.",
            "unreadable": "Idiograph could not read any passages from noise.docx.",
            "pdf": "Idiograph could not read any passages from letter.pdf.",
            "a project": "That folder is Keeping hens, a project already.",
            "nowhere": "That folder is not there, so nothing was added.",
            "no second": "Give walk notes.txt a pseudonym.",
            "lower second": "Give walk notes.txt an interview name.",
            "two seconds": "Wren's interviews carry two numbers, P1 and P2.",
            "op": "The op is folder, read or make.",
            "folder there": "P1 - Wren is there already.",
            "number taken": "There is a P2 folder there already.",
            "case there": "Ash is a participant there already.",
            "one run": idiograph_routes.ONE_RUN,
        }
        check("102, 9 October: every refusal is one line naming what to fix, and writes nothing, in the folder or the "
              "settings, and a second part asks for nothing",
              said == want and "second part" not in " ".join(said.values()), str({k: v for k, v in said.items() if want.get(k) != v}))
        check("102: the next free number skips every P<n> folder there", idiograph_routes.next_number(other) == 7
              and idiograph_routes.api_new_project({"op": "folder", "path": str(other)})["next"] == 7)

        # ── D. a failure on the way takes away what that Make wrote, and nothing else
        third = base / "Hens three"
        third.mkdir()
        (third / "notes.md").write_text("His own file.", encoding="utf-8")
        calls = []

        def flaky(source, out, made=""):
            calls.append(Path(out).name)
            if len(calls) == 2:
                raise OSError("the disk is full")
            return kept[7](source, out, made=made)

        wb_mod.create_from_source = flaky
        said_fail = refusal(third, {"op": "make", "folder": str(third), "files": files_for(*six[:3])})
        wb_mod.create_from_source = kept[7]
        check("102: a write that fails half way takes away the case it had made and the lock it brought, and says one line",
              said_fail == idiograph_routes.NOT_MADE == "Idiograph could not write the participants' folders, so nothing was made."
              and calls == ["P1 Wren - EN & ES.xlsx", "P2 Ash - EN & ES.xlsx"]
              and sorted(p.name for p in third.iterdir()) == ["notes.md"], said_fail)
        (third / server_mod.PROJECT_FILE).write_text(json.dumps({"name": "Old hens", "note": "kept"}), encoding="utf-8")
        before_file = (third / server_mod.PROJECT_FILE).read_bytes()

        def late(path):
            raise WorkbookError("Added elsewhere in the meantime.")

        idiograph_routes.add_project = late
        said_late = refusal(third, {"op": "make", "folder": str(third), "name": "New hens", "files": files_for(*six[:2])})
        idiograph_routes.add_project = kept[6]
        check("102: one refused at the last step puts the project file back as it was and takes the cases away",
              said_late == "Added elsewhere in the meantime." and (third / server_mod.PROJECT_FILE).read_bytes() == before_file
              and sorted(p.name for p in third.iterdir()) == ["idiograph-project.json", "notes.md"], said_late)

        # ── E. Adam's two-part form is gone (9 October): a page from before that sends the setting and a second part
        # gets `P<n> - Pseudonym` all the same, the second part nowhere
        parts = base / "Hens in two parts"
        parts.mkdir()
        alder, beech = "Al" + "der", "Be" + "ech"
        two = idiograph_routes.api_new_project({"op": "make", "folder": str(parts), "name": "Hens in two parts", "second_part": True,
                                          "files": files_for(("Initial.vtt", "Wren", "Sam Okafor", {"second": alder}),
                                                             ("follow up.srt", "Wren", "Sam", {"second": alder}),
                                                             ("walk notes.txt", "Ash", "Sam", {"second": beech}))})
        wren2, ash2 = parts / "P1 - Wren", parts / "P2 - Ash"
        written = []
        for path in sorted(parts.rglob("*")):
            if path.is_file() and path.suffix == ".xlsx":
                with zipfile.ZipFile(path) as z:
                    written += [(f"{path.name}:{m}", z.read(m)) for m in z.namelist()]
            elif path.is_file():
                written.append((path.name, path.read_bytes()))
        names_written = ["/".join(p.relative_to(parts).parts[1:]) for p in parts.rglob("*")]
        holders = [n for n, data in written if alder.encode() in data or beech.encode() in data]
        project_two = json.loads((parts / server_mod.PROJECT_FILE).read_text(encoding="utf-8"))
        shown = list(json_strings(idiograph_routes.api_cases({}), ("path", "suggested", "id", "root")))
        check("102, 9 October: the setting and the second part a page from before sends are passed over, each folder "
              "`P<n> - Pseudonym`",
              wren2.is_dir() and ash2.is_dir() and (wren2 / "P1 Wren - EN & ES.xlsx").is_file()
              and (wren2 / "Source" / "P1 Wren - transcript.xlsx").is_file() and (wren2 / "Source" / "Initial" / "P1-Initial.vtt").is_file()
              and not holders and not any(alder in n or beech in n for n in names_written)
              and sorted(p.name for p in parts.iterdir() if p.is_dir()) == ["P1 - Wren", "P2 - Ash"]
              and "second_part" not in project_two and "second_part" not in idiograph_routes.read_project(parts),
              str(holders[:3]))
        check("102: and never on a screen: Make's answer and the home screen carry the label alone",
              two["cases"] == ["P1 - Wren", "P2 - Ash"] and not any(alder in s or beech in s for s in json_strings(two, ("path",)))
              and not any(alder in s or beech in s for s in shown)
              and alder.encode() not in cfg_file.read_bytes(), str(two["cases"]))
        check("102: nothing in New project prints, so no log carries a name",
              not any("print(" in inspect.getsource(f) for f in (idiograph_routes.make_project, idiograph_routes.new_cases,
                                                                 idiograph_routes.write_case, idiograph_routes.api_new_project)))
    finally:
        (server_mod.CONFIG_PATH, server_mod.ROOT_OVERRIDE, server_mod.STATE_PATH, server_mod.STATE_MEMORY,
         server_mod.PLATFORM, server_mod.PICK_FOLDER, idiograph_routes.add_project, wb_mod.create_from_source) = kept
    check("102: the live config.json is exactly as it was",
          (server_mod.CONFIG_PATH.read_bytes() if server_mod.CONFIG_PATH.exists() else None) == live_config)
    check("102: the route is in the table after /api/projects, and takes a POST alone, since it opens a dialog and writes",
          server_mod.ROUTES.get("/api/new-project") is idiograph_routes.api_new_project and "/api/new-project" in server_mod.POST_ONLY
          and list(server_mod.ROUTES).index("/api/new-project") == list(server_mod.ROUTES).index("/api/projects") + 1)

    # ── F. the page: New project under the sections, its card, its rows
    page = support.page_text()
    js = support.text("family/static/shell.js", "apps/idiograph/static/distil.js")
    fn = lambda name: js.split(f"function {name}(", 1)[1].split("\n}", 1)[0] if f"function {name}(" in js else ""
    whole = lambda name: f"function {name}(" + fn(name) + "\n}"
    card = page.split('<div class="overlay" id="newproject" hidden>', 1)[1].split("\n</div>\n", 1)[0] \
        if 'id="newproject"' in page else ""
    check("102: the page sends each file's contents, reads them through the route, and never fills a pseudonym",
          "readAsDataURL(file)" in fn("npBase64") and "op: 'read', name: row.file, data: row.data, columns" in fn("npRead")
          and "pseudonym" not in fn("npRead") and "pseudonym" not in fn("npAdd").split("pseudonym: '',", 1)[1]
          and "op: 'make'" in fn("npMake") and "closeNewProject();" in fn("npMake") and "loadLibrary()" in fn("npMake")
          and "needsRestart(err) ? RESTART_LINE : err.message" in fn("npMake"))
    np_code = js.split("/* New project (item 204)", 1)[1].split("/* ───", 1)[0] if "/* New project (item 204)" in js else ""
    check("102: no AI anywhere in it, on the page or the server",
          np_code and not re.search(r"\bai\b|AI|sparkle|data-ai", np_code)
          and not any(w in inspect.getsource(f) for f in (idiograph_routes.make_project, idiograph_routes.new_cases, idiograph_routes.api_new_project)
                      for w in ("ai_mod", "themes_ai", "sift_ai")))
    node = shutil.which("node")
    if not node:
        skip("102: the rows and the numbers in node", "node is not installed")
    else:
        pieces = [line_of_js(js, "const esc = "), line_of_js(js, "const escAttr = "), line_of_js(js, "const turnsWord = "),
                  line_of_js(js, "const importBrings = "), line_of_js(js, "const IMPORT_ROLES = "),
                  line_of_js(js, "const importRole = "), line_of_js(js, "const SPEAKER_ROLES = "), whole("speakerChoosersHtml"),
                  whole("importMapHtml"), whole("importPreviewHtml"), line_of_js(js, "const NP = "), line_of_js(js, "const NP_PREVIEW = "), whole("npNamesHtml"), whole("npRowHtml"), whole("npNumbers")]
        script = scratch / "new-project-102.js"
        script.write_text(support.i18n_js() +
            "const second = { checked: false };\n"
            "const $ = (id) => (id === 'np-second' ? second : null);\n"
            "const NP_CROSS = 'x';\n" + "\n".join(pieces) + "\n"
            "const read = " + json.dumps(read) + ";\n"
            "const row = { key: 1, file: 'Rhea Example.vtt', read, said: '', pseudonym: '', second: '', interview: 'Interview',\n"
            "  roles: { 'Sam Okafor': 'interviewer' }, number: '' };\n"
            "const html = npRowHtml(row);\n"
            "second.checked = true;\n"
            "const withSecond = npRowHtml(row);\n"
            "const bare = npRowHtml({ key: 2, file: 'x.vtt', read: null, said: '', pseudonym: '', second: '', interview: '', roles: {}, number: '' });\n"
            "NP.next = 4;\n"
            "const mk = (p, n = '') => ({ pseudonym: p, number: n });\n"
            "NP.rows = [mk('Wren'), mk('Ash'), mk('Wren'), mk('')];\n"
            "const auto = npNumbers();\n"
            "NP.rows = [mk('Wren'), mk('Ash', '9'), mk('Wren'), mk('Oak')];\n"
            "const typed = npNumbers();\n"
            "NP.rows = [mk('Wren'), mk('Ash', '4')];\n"
            "const around = npNumbers();\n"
            "console.log(JSON.stringify({ html, withSecond, bare, auto, typed, around }));\n", encoding="utf-8")
        run = subprocess.run([node, str(script)], capture_output=True, text=True, encoding="utf-8")
        if run.returncode != 0:
            check("102: the rows draw in node", False, run.stderr.strip()[:400])
        else:
            o = json.loads(run.stdout)
            pseud = o["html"].split('data-np="pseudonym"', 1)[1].split(">", 1)[0] if 'data-np="pseudonym"' in o["html"] else "missing"
            check("102: in node, a row shows its file, its turns, each speaker's role preset, and an empty pseudonym whatever the "
                  "labels and the file's name say",
                  "Rhea Example.vtt" in o["html"] and "4 passages" in o["html"]
                  and 'data-speaker="Sam Okafor" data-np="speaker-Sam Okafor"><option value="interviewer" selected' in o["html"]
                  and 'value=""' in pseud and "Rhea" not in pseud and 'value="Interview"' in o["html"]
                  and "Second part" not in o["html"] and o["withSecond"] == o["html"], pseud)
            check("102: in node, the numbers go in order from the folder's next free one, a case keeps one, and a typed one holds",
                  o["auto"] == {"Wren": 4, "Ash": 5} and o["typed"] == {"Ash": 9, "Wren": 4, "Oak": 5}
                  and o["around"] == {"Ash": 4, "Wren": 5}, str(o["auto"]) + str(o["typed"]) + str(o["around"]))

    # ── G. the words: the manual, the README and the internals, and the voice of all that is new
    manual = support.source("docs/manual.md").read_text(encoding="utf-8")
    projects = manual.split("\n## Projects\n", 1)[1].split("\n## ", 1)[0]
    para = flat(projects.split("**New project.**", 1)[1].split("\n\n", 1)[0]) if "**New project.**" in projects else ""
