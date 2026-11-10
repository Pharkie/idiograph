from __future__ import annotations

import inspect
import json
import re
import shutil
from pathlib import Path

import openpyxl

import rounds as rounds_mod
import workbook as wb_mod
from workbook import WorkbookError

from . import support
from .support import cell_signature, check, json_strings, line_of_js, skip
import idiograph_routes


def test_add_transcripts(scratch):
    print("\n108. Add transcripts: transcripts added to a project that stands, a new pseudonym a new case at its next "
          "number, a case's own a further interview at the end of its workbooks, the refusals and the put-back")
    import base64
    import subprocess
    import zipfile
    import convert
    import server as server_mod
    import themes as themes_mod

    b64 = lambda data: base64.b64encode(data if isinstance(data, bytes) else data.encode("utf-8")).decode("ascii")
    flat = lambda text: " ".join(str(text).split())

    # ── A. every word invented: Kit asks about an allotment, and each participant's label is a made-up
    # full name, which must never reach a workbook
    vtt = ("WEBVTT\n\n00:00:01.000 --> 00:00:04.000\n<v Kit Sample>What did the plot look like in March?</v>\n\n"
           "00:00:05.000 --> 00:00:09.000\n<v Noor Invented>Mostly mud and a broken shed.</v>\n\n"
           "00:00:10.000 --> 00:00:12.000\n<v Kit Sample>And now?</v>\n\n"
           "00:00:13.000 --> 00:00:16.000\n<v Noor Invented>Beans up the fence, and a new roof.</v>\n")
    srt = ("1\n00:00:02,000 --> 00:00:05,000\nKit: A week later, what changed?\n\n"
           "2\n00:00:06,000 --> 00:00:09,000\nNoor: The slugs found the lettuce first.\n\n"
           "3\n00:00:10,000 --> 00:00:11,000\nKit: All of it?\n\n"
           "4\n00:00:12,000 --> 00:00:15,000\nNoor: All but one row by the path.\n")
    txt = ("Kit: [00:00:03] Who else works the plots?\nPip Invented: [00:00:08] An old couple and a school.\n"
           "Kit: [00:00:40] Do you talk to them?\nPip Invented: [00:00:44] Over the water butt, mostly.\n")
    csv_text = ("Speaker,Start,Text\nKit,0:04,When do you go down?\nOla Invented,0:09,Before work while it is quiet.\n"
                "Kit,0:15,Every day?\nOla Invented,0:19,Most days in summer.\n")
    originals = {"Initial.vtt": vtt.encode("utf-8"), "Day 2.srt": srt.encode("utf-8"),
                 "plot notes.txt": txt.encode("utf-8"), "talk.csv": csv_text.encode("utf-8")}

    base = scratch / "add-transcripts-108"
    shutil.rmtree(base, ignore_errors=True)
    folder = base / "Allotment study"
    folder.mkdir(parents=True)
    held_dir = base / "originals"
    held_dir.mkdir()
    for name, data in originals.items():
        (held_dir / name).write_bytes(data)
    marks = {p.name: (p.read_bytes(), p.stat().st_mtime_ns) for p in held_dir.iterdir()}
    cfg_file = scratch / "add-transcripts-108-config.json"
    cfg_file.write_text(json.dumps({"projects": [], "interviewer": "Bea"}), encoding="utf-8")
    live_config = server_mod.CONFIG_PATH.read_bytes() if server_mod.CONFIG_PATH.exists() else None
    kept = (server_mod.CONFIG_PATH, server_mod.ROOT_OVERRIDE, server_mod.STATE_PATH, server_mod.STATE_MEMORY,
            wb_mod.add_from_source, convert.add_sheets)

    def tree(at: Path) -> dict:
        # each path with slashes on any system, and a lock file never read, since Windows refuses a
        # read of a file another holds locked (14 October)
        return {p.relative_to(at).as_posix(): (p.read_bytes() if p.is_file() and p.suffix != ".lock" else None)
                for p in sorted(at.rglob("*"))}

    def files_for(*rows):
        return [{"name": n, "data": b64(originals[n]), "pseudonym": who, "interview": convert.interview_of(n),
                 "interviewer": asks, **more} for n, who, asks, more in rows]

    def refusal(body: dict) -> str:
        before, settings = tree(base), cfg_file.read_bytes()
        try:
            idiograph_routes.api_add_transcripts(body)
            return "added"
        except (WorkbookError, server_mod.OutsideRoot) as exc:
            return str(exc) if tree(base) == before and cfg_file.read_bytes() == settings else "written: " + str(exc)

    def sheet_marks(path: Path, names=None) -> dict:
        """Every cell of the sheets named, its value, runs, font, fill, border, alignment, protection and
        format, and each sheet's widths, heights, panes, zoom and size."""
        wb = openpyxl.load_workbook(path, rich_text=True)
        out = {}
        for ws in wb.worksheets:
            if names is not None and ws.title not in names:
                continue
            cells = {c.coordinate: (cell_signature(c), repr(c.font), repr(c.fill), repr(c.border), repr(c.alignment),
                                    repr(c.protection), c.number_format) for row in ws.iter_rows() for c in row}
            out[ws.title] = (cells, {k: v.width for k, v in ws.column_dimensions.items()},
                             {k: v.height for k, v in ws.row_dimensions.items()}, ws.freeze_panes,
                             ws.sheet_view.zoomScale, ws.max_row, ws.max_column)
        wb.close()
        return out

    def add(root_id, *rows):
        return {"op": "add", "root": root_id, "files": files_for(*rows)}

    try:
        server_mod.CONFIG_PATH, server_mod.ROOT_OVERRIDE = cfg_file, None
        server_mod.STATE_PATH, server_mod.STATE_MEMORY = scratch / "add-transcripts-108-state.json", {"recent": []}
        made = idiograph_routes.api_new_project({"op": "make", "folder": str(folder), "name": "Allotments",
                                           "research_question": "How do people experience keeping an allotment?",
                                           "files": files_for(("Initial.vtt", "Hazel", "Kit Sample", {}),
                                                              ("plot notes.txt", "Rook", "Kit", {}))})
        root_id = made["project"]["id"]
        hazel = folder / "P1 - Hazel"
        book = hazel / "P1 Hazel - EN & ES.xlsx"
        raw = hazel / "Source" / "P1 Hazel - transcript.xlsx"
        # ── B. his work in Hazel's case, invented: two statements through the route the page saves by, and
        # a PETs board grouping them
        turns = [r for r in idiograph_routes.api_open({"path": str(book)})["sheets"][0]["rows"] if r["name"] == "Hazel"]
        for r, words in zip(turns, ("Facing a plot that is all mud", "Putting a roof back on the shed")):
            idiograph_routes.api_commit({"path": str(book), "sheet": "Initial", "row": r["row"], "es": words, "en": "",
                                   "kq": r["text"][:12]})
        shown = idiograph_routes.api_themes({"workbook": str(book)})
        keys = [c["key"] for c in shown["cards"]]
        idiograph_routes.api_themes_save({"workbook": str(book), "version": {
            **shown["version"], "cards": {c["key"]: {"x": c["x"], "y": c["y"], "text": c["text"]} for c in shown["cards"]},
            "groups": [{"id": "g1", "label": "Making the plot over", "members": keys, "x": 0, "y": -40}], "discarded": []}})
        board, sidecar = themes_mod.themes_path(book), rounds_mod.progress_path(book)
        work = idiograph_routes.api_themes({"workbook": str(book)})
        check("108: the case has work in it before the Add, two statements and a board of one PET",
              len(keys) == 2 and [g["label"] for g in work["groups"]] == ["Making the plot over"]
              and board.is_file() and sidecar.is_file(), str(keys))
        held_board, held_sidecar = board.read_bytes(), sidecar.read_bytes()
        before_book, before_raw = book.read_bytes(), raw.read_bytes()
        book_marks, raw_marks = sheet_marks(book), sheet_marks(raw)
        project_bytes = (folder / server_mod.PROJECT_FILE).read_bytes()
        before_tree = tree(folder)

        # ── C. the card asks the project, then Add writes a new case and a further interview of Hazel's
        card = idiograph_routes.api_add_transcripts({"op": "project", "root": root_id})
        check("108, 9 October: the card asks the project for its name, its next free number and its cases by label, and no "
              "two-part setting",
              card == {"id": root_id, "name": "Allotments", "next": 3,
                       "cases": [{"label": "P1 - Hazel", "pseudonym": "Hazel"}, {"label": "P2 - Rook", "pseudonym": "Rook"}]},
              str(card))
        settings = cfg_file.read_bytes()
        added = idiograph_routes.api_add_transcripts(add(root_id, ("Day 2.srt", "Hazel", "Kit", {"number": 7, "second": "Never"}),
                                                   ("talk.csv", "Linnet", "Kit", {"second": "Never"})))
        check("108: Add answers the project, the new case and the case joined, each by label",
              added["added"] is True and added["cases"] == ["P3 - Linnet"] and added["joined"] == ["P1 - Hazel"]
              and added["project"]["name"] == "Allotments", str({k: v for k, v in added.items() if k != "project"}))
        after_tree = tree(folder)
        archive = [n for n in after_tree if n.startswith("P1 - Hazel/_Archive/") and n.endswith(".xlsx")]
        new = set(after_tree) - set(before_tree)
        changed = {n for n in before_tree if n in after_tree and before_tree[n] != after_tree[n]}
        want_new = {"P1 - Hazel/Source/Day 2", "P1 - Hazel/Source/Day 2/P1-Day 2.srt", "P1 - Hazel/_Archive", *archive,
                    "P3 - Linnet", "P3 - Linnet/Source", "P3 - Linnet/Source/Interview",
                    "P3 - Linnet/Source/Interview/P3-Interview.csv", "P3 - Linnet/Source/P3 Linnet - transcript.xlsx",
                    "P3 - Linnet/P3 Linnet - EN & ES.xlsx"}
        check("108: Add writes the copy, the archive copy and the new case, changes the two workbooks, and nothing else",
              new == want_new and changed == {"P1 - Hazel/P1 Hazel - EN & ES.xlsx", "P1 - Hazel/Source/P1 Hazel - transcript.xlsx"}
              and len(archive) == 1 and not set(before_tree) - set(after_tree),
              str(sorted(new ^ want_new)) + str(sorted(changed)))
        check("108: the workbook went to the participant's _Archive first, byte for byte as it was, under a backup's name",
              after_tree[archive[0]] == before_book
              and re.fullmatch(r"P1 - Hazel/_Archive/P1 Hazel - EN & ES \(pre-add \d{8}-\d{4}\)\.xlsx", archive[0]) is not None
              and idiograph_routes.BACKUP_STEM.search(Path(archive[0]).stem) is not None, archive[0] if archive else "none")
        check("108: the copy is the file as dropped, byte for byte, and the originals are untouched where they lie",
              (hazel / "Source" / "Day 2" / "P1-Day 2.srt").read_bytes() == originals["Day 2.srt"]
              and {p.name: (p.read_bytes(), p.stat().st_mtime_ns) for p in held_dir.iterdir()} == marks)
        opened_books = [openpyxl.load_workbook(p) for p in (book, raw)]
        check("108: the further interview is a sheet at the end of the raw source and of the annotated workbook",
              [b.sheetnames for b in opened_books] == [["Initial", "Day 2"], ["Initial", "Day 2"]]
              and wb_mod.is_raw_source(wb_mod.detect_columns(opened_books[1]["Day 2"]))
              and [c.value for c in opened_books[0]["Day 2"][1]] == wb_mod.HEADER,
              str([b.sheetnames for b in opened_books]))
        names_in = {opened_books[0]["Day 2"].cell(r, 1).value for r in range(2, opened_books[0]["Day 2"].max_row + 1)}
        fills = [c.fill.fill_type for b in opened_books for ws in b.worksheets for row in ws.iter_rows() for c in row
                 if c.fill.fill_type]
        for b in opened_books:
            b.close()
        check("108: its turns are under Settings' name and the pseudonym, no label from the file reaches it, and no cell "
              "carries a fill", names_in == {"Bea", "Hazel"} and not fills, str(names_in))
        check("108: every sheet already there is the same cell for cell and style for style, with its widths, heights, "
              "panes and zoom, in the annotated workbook and the raw source alike",
              sheet_marks(book, {"Initial"}) == book_marks and sheet_marks(raw, {"Initial"}) == raw_marks
              and list(book_marks) == ["Initial"])
        fresh = base / "fresh" / "P1 Hazel - EN & ES.xlsx"
        fresh.parent.mkdir()
        wb_mod.create_from_source(raw, fresh)
        check("108: the new sheet is the one create_from_source makes from the raw source's sheet, cell for cell",
              sheet_marks(book, {"Day 2"}) == sheet_marks(fresh, {"Day 2"}) and "Day 2" in sheet_marks(fresh))
        check("108: the PETs board and the progress file are byte for byte as they were, and so are the project file "
              "and the settings", board.read_bytes() == held_board and sidecar.read_bytes() == held_sidecar
              and (folder / server_mod.PROJECT_FILE).read_bytes() == project_bytes and cfg_file.read_bytes() == settings)

        # ── D. the new interview and the new case taken as any other
        opened = idiograph_routes.api_open({"path": str(book)})
        sheets = {s["name"]: s for s in opened["sheets"]}
        day2 = sheets.get("Day 2", {"rows": []})["rows"]
        stops = [r for r in day2 if rounds_mod.is_stop(r, "Bea")]
        check("108: Experiential statements opens the case with the new interview, its first turn as said, its stops the "
              "participant's turns, and the statements written before still there",
              list(sheets) == ["Initial", "Day 2"] and day2 and day2[0]["text"] == "A week later, what changed?"
              and day2[0]["name"] == "Bea" and {r["name"] for r in stops} == {"Hazel"} and len(stops) == 2
              and [r["es"] for r in sheets["Initial"]["rows"] if r["es"]] == ["Facing a plot that is all mud",
                                                                               "Putting a roof back on the shed"],
              str([(r["name"], r["text"][:20]) for r in day2[:2]]))
        cards = themes_mod.read_cards(book)
        state = idiograph_routes.api_themes({"workbook": str(book)})
        check("108: PETs reads the new sheet with the others, the statements keep their keys, and the board its PET",
              cards["sheets"] == ["Initial", "Day 2"] and [c["key"] for c in cards["cards"]] == keys
              and [g["label"] for g in state["groups"]] == ["Making the plot over"]
              and board.read_bytes() == held_board, str(cards["sheets"]))
        listed = idiograph_routes.api_cases({})["projects"][0]
        linnet = folder / "P3 - Linnet" / "P3 Linnet - EN & ES.xlsx"
        lin_open = idiograph_routes.api_open({"path": str(linnet)})
        rows_of = {c["case"]: c for c in listed["participants"]}
        check("108: the new case stands at the project's next number as Make writes one, and the home screen has all three",
              [c["case"] for c in listed["participants"]] == ["P1 - Hazel", "P2 - Rook", "P3 - Linnet"]
              and [s["name"] for s in lin_open["sheets"]] == ["Interview"]
              and {r["name"] for s in lin_open["sheets"] for r in s["rows"]} == {"Bea", "Linnet"}
              and rows_of["P1 - Hazel"]["sheets"] == ["Initial", "Day 2"], str(list(rows_of)))

        # ── E. the refusals, each one line, each writing nothing
        lock = hazel / ("~$" + book.name)
        lock.write_bytes(b"")
        said = {"open": refusal(add(root_id, ("plot notes.txt", "Hazel", "Kit", {"interview": "T3"})))}
        lock.unlink()
        lock = raw.parent / ("~$" + raw.name)
        lock.write_bytes(b"")
        said["raw open"] = refusal(add(root_id, ("plot notes.txt", "Hazel", "Kit", {"interview": "T3"})))
        lock.unlink()
        said["there"] = refusal(add(root_id, ("Day 2.srt", "Hazel", "Kit", {})))
        said["there, other capitals"] = refusal(add(root_id, ("plot notes.txt", "Hazel", "Kit", {"interview": "initial"})))
        said["twice"] = refusal(add(root_id, ("plot notes.txt", "Hazel", "Kit", {"interview": "T3"}),
                                    ("talk.csv", "Hazel", "Kit", {"interview": "t3"})))
        said["lower"] = refusal(add(root_id, ("talk.csv", "wisp", "Kit", {})))
        said["two words"] = refusal(add(root_id, ("talk.csv", "Wisp Tree", "Kit", {})))
        said["interviewer"] = refusal(add(root_id, ("talk.csv", "Bea", "Kit", {})))
        said["unreadable"] = refusal({"op": "add", "root": root_id, "files": [
            {"name": "noise.docx", "data": b64(b"PK\x03\x04 nothing"), "pseudonym": "Hazel", "interview": "T3"}]})
        said["none"] = refusal({"op": "add", "root": root_id, "files": []})
        said["number taken"] = refusal(add(root_id, ("talk.csv", "Wisp", "Kit", {"number": 2})))
        (folder / "P9 - Hazel").mkdir()
        said["two cases"] = refusal(add(root_id, ("talk.csv", "Hazel", "Kit", {"interview": "T3"})))
        (folder / "P9 - Hazel").rmdir()
        (folder / "Plum").mkdir()
        said["plain folder"] = refusal(add(root_id, ("talk.csv", "Plum", "Kit", {})))
        (folder / "Plum").rmdir()
        said["demo"] = refusal(add("demo", ("talk.csv", "Wisp", "Kit", {})))
        said["no project"] = refusal(add(str(base / "elsewhere"), ("talk.csv", "Wisp", "Kit", {})))
        said["op"] = refusal({"op": "remake", "root": root_id})
        cfg_file.write_text(json.dumps({"projects": json.loads(settings)["projects"] + [{"root": str(base / "gone")}],
                                        "interviewer": "Bea"}), encoding="utf-8")
        said["gone"] = refusal(add(str(base / "gone"), ("talk.csv", "Wisp", "Kit", {})))
        said["gone, asked"] = refusal({"op": "project", "root": str(base / "gone")})
        cfg_file.write_bytes(settings)
        want = {
            "open": "P1 Hazel - EN & ES.xlsx is open in Excel. Close it in Excel first, then try again.",
            "raw open": "P1 Hazel - transcript.xlsx is open in Excel. Close it in Excel first, then try again.",
            "there": "P1 - Hazel has an interview named Day 2 already.",
            "there, other capitals": "P1 - Hazel has an interview named initial already.",
            "twice": "Hazel has two interviews named t3.",
            "lower": "Make the pseudonym for talk.csv one capitalised word.",
            "two words": "Make the pseudonym for talk.csv one capitalised word.",
            "interviewer": "Bea is the interviewer's name in Settings, so it cannot be a pseudonym.",
            "unreadable": "Idiograph could not read any passages from noise.docx.",
            "none": "Drop a transcript first.",
            "number taken": "There is a P2 folder there already.",
            "two cases": "P1 - Hazel and P9 - Hazel share the pseudonym Hazel.",
            "plain folder": "Plum is a participant there already.",
            "demo": "The demo's project is fixed.",
            "no project": "That folder is not a project's root.",
            "op": "The op is project or add.",
            "gone": "That folder is not there, so nothing was added.",
            "gone, asked": "That folder is not there, so nothing was added.",
        }
        check("108: every refusal is one line naming what to fix, checked before anything is written, and writes nothing",
              said == want, str({k: v for k, v in said.items() if want.get(k) != v}))

        # ── F. a failure on the way puts back what that Add changed, and nothing else
        rook = folder / "P2 - Rook"
        calls = []

        def late(source, sheets, out):
            calls.append(list(sheets))
            kept[4](source, sheets, out)
            raise OSError("the disk is full")

        before_fail = tree(base)
        stamps = {p: p.stat().st_mtime_ns for p in (book, raw)}
        wb_mod.add_from_source = late
        said_late = refusal(add(root_id, ("talk.csv", "Wisp", "Kit", {}), ("plot notes.txt", "Hazel", "Kit", {"interview": "T3"})))
        wb_mod.add_from_source = kept[4]
        check("108: a write that fails once the workbook has its new sheet puts the workbook and the raw source back from "
              "their copies, takes away the new case, the copy and the archive copy, and says one line",
              said_late == idiograph_routes.NOT_ADDED == "Idiograph could not add the transcripts, so nothing was added."
              and calls == [["T3"]] and tree(base) == before_fail and {p: p.stat().st_mtime_ns for p in (book, raw)} == stamps,
              said_late)

        def early(sheets, out):
            raise OSError("the disk is full")

        convert.add_sheets = early
        had_working = (rook / "Working").exists()
        said_early = refusal(add(root_id, ("talk.csv", "Rook", "Kit", {"interview": "T3"})))
        convert.add_sheets = kept[5]
        check("108: one that fails at the raw source leaves a case with no Working folder without one, its lock taken away",
              said_early == idiograph_routes.NOT_ADDED and had_working is False and not (rook / "Working").exists(), said_early)

        # ── G. the two-part folders his own cases carry (9 October): New project and Add make `P<n> - Pseudonym`
        # whatever a page from before sends, and a case whose folder already carries a second part is joined, its
        # folder's name kept as it is
        parts = base / "Allotments in two parts"
        parts.mkdir()
        thorn, birch, willow = "Th" + "orn", "Bi" + "rch", "Wi" + "llow"
        two = idiograph_routes.api_new_project({"op": "make", "folder": str(parts), "name": "Allotments in two parts",
                                          "second_part": True, "files": files_for(("Initial.vtt", "Hazel", "Kit Sample",
                                                                                   {"second": thorn}))})
        two_id = two["project"]["id"]
        made_plain = (parts / "P1 - Hazel").is_dir()
        # his own name for the folder, a second part after the pseudonym, as a GRAVITY case carries one
        (parts / "P1 - Hazel").rename(parts / ("P1 - Hazel" + "-" + thorn))
        card_two = idiograph_routes.api_add_transcripts({"op": "project", "root": two_id})
        added_two = idiograph_routes.api_add_transcripts(add(two_id, ("Day 2.srt", "Hazel", "Kit", {"second": willow}),
                                                       ("talk.csv", "Linnet", "Kit", {"second": birch})))
        hazel2, linnet2 = parts / ("P1 - Hazel" + "-" + thorn), parts / "P2 - Linnet"
        written = []
        for path in sorted(parts.rglob("*")):
            if path.is_file() and path.suffix == ".xlsx":
                with zipfile.ZipFile(path) as z:
                    written += [(f"{path.name}:{m}", z.read(m)) for m in z.namelist()]
            elif path.is_file():
                written.append((path.name, path.read_bytes()))
        inner = ["/".join(p.relative_to(parts).parts[1:]) for p in parts.rglob("*")]
        joined_book = openpyxl.load_workbook(hazel2 / "P1 Hazel - EN & ES.xlsx")
        joined_sheets = joined_book.sheetnames
        joined_book.close()
        holders = [n for n, data in written if any(w.encode() in data for w in (thorn, birch, willow))]
        shown_two = list(json_strings(card_two, ())) + list(json_strings(added_two, ()))
        check("108, 9 October: a new case is `P<n> - Pseudonym` whatever second part a page from before sends, and a case "
              "whose folder carries one is joined, its folder's name kept and the part written nowhere else",
              made_plain and "second_part" not in card_two and not (parts / "P1 - Hazel").exists()
              and (hazel2 / "Source" / "Day 2" / "P1-Day 2.srt").is_file() and (linnet2 / "P2 Linnet - EN & ES.xlsx").is_file()
              and joined_sheets == ["Initial", "Day 2"]
              and not holders and not any(w in n for n in inner for w in (thorn, birch, willow))
              and sorted(p.name for p in parts.iterdir() if p.is_dir()) == sorted([hazel2.name, "P2 - Linnet"]), str(holders[:3]))
        check("108: and never on a screen: the card's answer and Add's carry the labels alone",
              card_two["cases"] == [{"label": "P1 - Hazel", "pseudonym": "Hazel"}]
              and added_two["cases"] == ["P2 - Linnet"] and added_two["joined"] == ["P1 - Hazel"]
              and not any(w in s for s in shown_two for w in (thorn, birch, willow)), str(added_two["cases"]))
        check("108: with the setting off, a row's second part is never asked or written",
              not any("Never" in p.name for p in folder.rglob("*")))
        fns = (idiograph_routes.standing_cases, idiograph_routes.own_books, idiograph_routes.join_case, idiograph_routes.add_interviews,
               idiograph_routes.unadd, idiograph_routes.add_root, idiograph_routes.add_transcripts, idiograph_routes.api_add_transcripts,
               wb_mod.add_from_source, convert.add_sheets)
        check("108: nothing in Add prints, so no log carries a name, and nothing in it reaches an AI",
              not any("print(" in inspect.getsource(f) for f in fns)
              and not any(w in inspect.getsource(f) for f in fns for w in ("ai_mod", "themes_ai", "sift_ai", "ai_suggest")))
    finally:
        (server_mod.CONFIG_PATH, server_mod.ROOT_OVERRIDE, server_mod.STATE_PATH, server_mod.STATE_MEMORY,
         wb_mod.add_from_source, convert.add_sheets) = kept
    check("108: the live config.json is exactly as it was",
          (server_mod.CONFIG_PATH.read_bytes() if server_mod.CONFIG_PATH.exists() else None) == live_config)
    check("108: the route sits after /api/new-project in the table and takes a POST alone, since it writes",
          server_mod.ROUTES.get("/api/add-transcripts") is idiograph_routes.api_add_transcripts
          and "/api/add-transcripts" in server_mod.POST_ONLY
          and list(server_mod.ROUTES).index("/api/add-transcripts") == list(server_mod.ROUTES).index("/api/new-project") + 1)

    # ── H. the page: Add transcripts on each project's section, the card with the project fixed, the rows
    page = support.page_text()
    js = support.text("family/static/shell.js", "apps/idiograph/static/distil.js")
    fn = lambda name: js.split(f"function {name}(", 1)[1].split("\n}", 1)[0] if f"function {name}(" in js else ""
    whole = lambda name: f"function {name}(" + fn(name) + "\n}"
    check("108, 9 October: each project's page ends in a quiet Add transcripts, none on the demo's or on a folder that is gone",
          '<button type="button" class="quiet proj-transcripts" id="hp-transcripts">Add transcripts</button>' in page
          and "$('hp-transcripts').hidden = s.there === false;" in fn("drawPage")
          and "$('hp-transcripts').onclick = () => openAddTranscripts(s.id);" in fn("drawPage")
          and "$('hp-transcripts').hidden = true;" in fn("drawDemoPage") and "proj-more" not in page)
    card_html = page.split('<div class="overlay" id="newproject" hidden>', 1)[1].split("\n</div>\n", 1)[0]
    check("108, 9 October: Add sends the rows to its own route, a row that joins a case with no number, and no row a second part",
          "if (add) await api('/api/add-transcripts', { op: 'add', root: add.id, files, skip });" in fn("npMake")
          and "second" not in fn("npMake") + fn("npFilesSent") and "number: joins ? null" in fn("npFilesSent")
          and "const files = npFilesSent();" in fn("npMake")
          and "op: 'make'" in fn("npMake"))
    np_code = js.split("/* New project (item 204)", 1)[1].split("/* ───", 1)[0]
    add_code = "\n".join(whole(n) for n in ("npMode", "openAddTranscripts", "npJoinsDraw", "npMake"))
    check("108: no AI anywhere in it, the code and the card alike",
          "openAddTranscripts" in np_code and not re.search(r"\bai\b|AI|sparkle|data-ai", add_code + card_html))
    node = shutil.which("node")
    if not node:
        skip("108: the numbers in node", "node is not installed")
    else:
        script = scratch / "add-transcripts-108.js"
        script.write_text(
            line_of_js(js, "const NP = ") + "\n" + whole("npNumbers") + "\n"
            "NP.next = 3;\n"
            "NP.add = { id: 'x', name: 'Allotments', cases: new Map([['Hazel', 'P1 - Hazel'], ['Rook', 'P2 - Rook']]) };\n"
            "const mk = (p, n = '') => ({ pseudonym: p, number: n });\n"
            "NP.rows = [mk('Hazel', '1'), mk('Linnet'), mk('Rook'), mk('Wisp'), mk('Hazel')];\n"
            "const adding = npNumbers();\n"
            "NP.add = null;\n"
            "NP.next = 1;\n"
            "NP.rows = [mk('Hazel'), mk('Linnet')];\n"
            "const making = npNumbers();\n"
            "console.log(JSON.stringify({ adding, making }));\n", encoding="utf-8")
        run = subprocess.run([node, str(script)], capture_output=True, text=True, encoding="utf-8")
        if run.returncode != 0:
            check("108: the numbers run in node", False, run.stderr.strip()[:400])
        else:
            o = json.loads(run.stdout)
            check("108: in node, a case there takes no number, and each new one the next free from the project's own",
                  o["adding"] == {"Linnet": 3, "Wisp": 4} and o["making"] == {"Hazel": 1, "Linnet": 2}, run.stdout.strip())

    # ── I. the words: the manual, the internals, and the voice of all that is new
    internals = support.source("docs/internals.md").read_text(encoding="utf-8")
    row = flat(internals.split("| `/api/add-transcripts` |", 1)[1].split("\n", 1)[0]) if "| `/api/add-transcripts` |" in internals else ""
