from __future__ import annotations

import json
import shutil
from pathlib import Path

import openpyxl

import rounds as rounds_mod
import workbook as wb_mod
from workbook import WorkbookError

from . import support
from .support import cell_signature, check, skip
import idiograph_routes


def test_rename_and_go_to_passage(scratch):
    print("\n156. Rename a participant, a statement card's passage and the way back, the faint done bar for a "
          "skipped passage alone, and Sift's PRISMA flow from the active run alone, 16 October, Adam's word on a "
          "tester's feedback")
    import base64
    import subprocess
    import gets as gets_mod
    import server as server_mod
    import sift
    import themes as themes_mod

    read = lambda path: Path(path).read_text(encoding="utf-8")
    app, themes_js = support.text("family/static/shell.js", "apps/idiograph/static/distil.js"), support.text("apps/idiograph/static/themes.js")
    fn = lambda src, name: src.split(f"function {name}(", 1)[1].split("\n}", 1)[0] if f"function {name}(" in src else ""
    whole = lambda src, name: ("async " if f"async function {name}(" in src else "") + f"function {name}(" + fn(src, name) + "\n}"
    line = lambda src, start: start + src.split(start, 1)[1].split("\n", 1)[0] if start in src else ""
    node = shutil.which("node")
    b64 = lambda text: base64.b64encode(text.encode("utf-8")).decode("ascii")

    # ── A. an invented project: two gardeners, Kit the interviewer, every word made up
    vtt = ("WEBVTT\n\n00:00:01.000 --> 00:00:04.000\n<v Kit>What comes up first in spring?</v>\n\n"
           "00:00:05.000 --> 00:00:09.000\n<v Ada>The broad beans, always the beans first.</v>\n\n"
           "00:00:10.000 --> 00:00:12.000\n<v Kit>And after them?</v>\n\n"
           "00:00:13.000 --> 00:00:16.000\n<v Ada>The weeds, and me on my knees in the wet.</v>\n\n"
           "00:00:17.000 --> 00:00:19.000\n<v Kit>Do you mind it?</v>\n\n"
           "00:00:20.000 --> 00:00:24.000\n<v Ada>No, the knees are the price of the beans.</v>\n")
    txt = ("Kit: [00:00:03] When do you water?\nBea: [00:00:08] At dusk, when the slugs come out too.\n"
           "Kit: [00:00:40] Is that a good time?\nBea: [00:00:44] For the slugs it is.\n")
    base = scratch / "rename-156"
    shutil.rmtree(base, ignore_errors=True)
    root = base / "Garden study"
    root.mkdir(parents=True)
    cfg_file = base / "config.json"
    cfg_file.write_text(json.dumps({"projects": [], "interviewer": "Kit"}), encoding="utf-8")
    kept = (server_mod.CONFIG_PATH, server_mod.ROOT_OVERRIDE, server_mod.STATE_PATH, server_mod.STATE_MEMORY)

    def tree(at: Path) -> dict:
        return {p.relative_to(at).as_posix(): (p.read_bytes() if p.is_file() and p.suffix != ".lock" else None)
                for p in sorted(at.rglob("*"))}

    def refusal(body: dict) -> str:
        before, settings, held = tree(base), cfg_file.read_bytes(), json.dumps(server_mod.STATE_MEMORY)
        try:
            idiograph_routes.api_rename(body)
            return "renamed"
        except (WorkbookError, server_mod.OutsideRoot) as exc:
            same = tree(base) == before and cfg_file.read_bytes() == settings and json.dumps(server_mod.STATE_MEMORY) == held
            return str(exc) if same else "written: " + str(exc)

    def names_in(path: Path) -> dict:
        """Each transcript sheet's Name cells, row by row."""
        wb = openpyxl.load_workbook(path)
        out = {}
        for ws in wb.worksheets:
            cols = wb_mod.detect_columns(ws)
            if {"name", "ts", "transcript"} <= set(cols):
                out[ws.title] = [ws.cell(r, cols["name"]).value for r in range(2, ws.max_row + 1)]
        wb.close()
        return out

    def cells_but_names(path: Path) -> dict:
        """Every cell but the Name column's, its value, runs, font, fill and format, and each Name cell's style."""
        wb = openpyxl.load_workbook(path, rich_text=True)
        out = {}
        for ws in wb.worksheets:
            cols = wb_mod.detect_columns(ws)
            name_col = cols.get("name")
            out[ws.title] = {c.coordinate: (cell_signature(c) if c.column != name_col or c.row == 1 else None,
                                            repr(c.font), repr(c.fill), c.number_format)
                             for row in ws.iter_rows() for c in row}
        wb.close()
        return out

    try:
        server_mod.CONFIG_PATH, server_mod.ROOT_OVERRIDE = cfg_file, None
        server_mod.STATE_PATH, server_mod.STATE_MEMORY = base / "state.json", {"recent": []}
        made = idiograph_routes.api_new_project({"op": "make", "folder": str(root), "name": "Gardens",
                                           "research_question": "How do people experience keeping a garden?",
                                           "files": [{"name": "Initial.vtt", "data": b64(vtt), "pseudonym": "Ada",
                                                      "interview": "Initial", "interviewer": "Kit"},
                                                     {"name": "notes.txt", "data": b64(txt), "pseudonym": "Bea",
                                                      "interview": "Initial", "interviewer": "Kit"}]})
        rid = made["project"]["id"]
        ada = root / "P1 - Ada"
        book, raw = ada / "P1 Ada - EN & ES.xlsx", ada / "Source" / "P1 Ada - transcript.xlsx"
        turns = [r for r in idiograph_routes.api_open({"path": str(book)})["sheets"][0]["rows"] if r["name"] == "Ada"]
        idiograph_routes.api_commit({"path": str(book), "sheet": "Initial", "row": turns[0]["row"], "es": "Beans as the first sign",
                               "en": "", "kq": "The broad beans"})
        idiograph_routes.api_commit({"path": str(book), "sheet": "Initial", "row": turns[1]["row"], "es": "Kneeling as the work",
                               "en": "", "kq": "on my knees"})
        shown = idiograph_routes.api_themes({"workbook": str(book)})
        keys = [c["key"] for c in shown["cards"]]
        idiograph_routes.api_themes_save({"workbook": str(book), "version": {
            **shown["version"], "cards": {c["key"]: {"x": c["x"], "y": c["y"], "text": c["text"]} for c in shown["cards"]},
            "groups": [{"id": "g1", "label": "The garden asks for the body", "members": keys, "x": 0, "y": -40}], "discarded": []}})
        gshown = idiograph_routes.api_gets({"workbook": str(book)})
        idiograph_routes.api_gets_save({"workbook": str(book), "version": dict(
            gshown["version"], cards={c["key"]: {"x": c["x"], "y": c["y"], "text": c.get("text", "")} for c in gshown["cards"]},
            groups=[{"id": "G1", "label": "Tending", "members": ["P1 - Ada/g1"], "x": 0, "y": -60}],
            discarded=[], picks={}, notes=[])})
        idiograph_routes.api_order({"root": rid, "order": ["P2 - Bea", "P1 - Ada"]})
        gfile, pfile = root / gets_mod.FILE, root / server_mod.PROJECT_FILE
        board = themes_mod.themes_path(book)
        before_names = {p: names_in(p) for p in (book, raw)}
        before_cells = {p: cells_but_names(p) for p in (book, raw)}
        before_bytes = {p: p.read_bytes() for p in (book, raw, board, gfile, pfile)}
        check("156: the invented case has work in it before a rename, two statements, a board, the GETs and his order",
              len(keys) == 2 and board.is_file() and gfile.is_file() and "P1 - Ada/g1" in gfile.read_text(encoding="utf-8")
              and json.loads(pfile.read_text(encoding="utf-8"))["order"] == ["P2 - Bea", "P1 - Ada"]
              and before_names[book]["Initial"].count("Ada") == 3 and before_names[book]["Initial"].count("Kit") == 3,
              str(before_names[book]))

        # ── B. what will change, said first and nothing written
        before = tree(base)
        plan = idiograph_routes.api_rename({"op": "plan", "root": rid, "case": "P1 - Ada", "name": "Cora", "folder": False})
        ticked = idiograph_routes.api_rename({"op": "plan", "root": rid, "case": "P1 - Ada", "name": "Cora", "folder": True})
        bare = idiograph_routes.api_rename({"op": "plan", "root": rid, "case": "P1 - Ada", "name": "", "folder": True})
        check("156: the plan lists a line for each thing it writes, the two workbooks, the case's PETs boards, the "
              "project's GETs, the project's order and note, and the recent list, and writes nothing",
              tree(base) == before and len(plan["lines"]) == 6 and plan["label"] == "P1 - Cora" and plan["case"] == "P1 - Ada",
              str(plan["lines"]))
        check("156: with the folder ticked the plan adds a line for the folder and for each workbook named after the "
              "participant, the same with no name yet, and none with the folder kept",
              len(ticked["folder_lines"]) == 3 and len(ticked["lines"]) == 6 and ticked["folder"] is True
              and len(bare["folder_lines"]) == 3 and plan["folder_lines"] == [], str([ticked["folder_lines"], ticked["lines"]]))

        # ── C. the refusals, each one line, nothing changed
        said = {what: refusal({"op": "rename", "root": rid, "case": "P1 - Ada", "name": name, "folder": True})
                for what, name in (("empty", "  "), ("same", "Ada"), ("word", "cora"), ("two", "Cora Lee"),
                                   ("taken", "Bea"), ("interviewer", "Kit"))}
        check("156: an empty, unchanged, uncapitalised, two-word, taken or interviewer's name is refused, nothing changed",
              len(said) == 6 and all(v and v != "renamed" and not v.startswith("written: ") for v in said.values()), str(said))
        lock = wb_mod.lock_file(raw)
        lock.write_bytes(b"")
        locked = refusal({"op": "rename", "root": rid, "case": "P1 - Ada", "name": "Cora", "folder": False})
        lock.unlink()
        demo_said = refusal({"op": "rename", "root": "demo", "case": "Juno", "name": "Cora", "folder": False})
        check("156: a workbook Excel has open, its ~$ file beside it, is refused with the statements screen's line, and "
              "the demo's names are fixed, nothing changed",
              locked not in ("", "renamed") and not locked.startswith("written: ")
              and demo_said == idiograph_routes.DEMO_NAMES, f"{locked} | {demo_said}")

        # ── D. renamed with the folder kept
        done = idiograph_routes.api_rename({"op": "rename", "root": rid, "case": "P1 - Ada", "name": "Cora", "folder": False})
        after_names = {p: names_in(p) for p in (book, raw)}
        check("156: the list shown first is what changed, and the answer names the case afresh",
              done["lines"] == plan["lines"] and done["case"] == "P1 - Cora" and done["old"] == "P1 - Ada"
              and done["folder_lines"] == [], str(done)[:300])
        check("156: every Name cell of every sheet that read Ada reads Cora, in the workbook and the raw source, and "
              "the interviewer's stay Kit",
              all(after_names[p][s] == ["Cora" if v == "Ada" else v for v in before_names[p][s]]
                  for p in (book, raw) for s in before_names[p])
              and after_names[book]["Initial"].count("Kit") == 3, str(after_names[book]))
        check("156: no other cell, style or fill moved, and the renamed cells keep their own style, never a fill",
              all(cells_but_names(p) == before_cells[p] for p in (book, raw)))
        tdata = json.loads(board.read_text(encoding="utf-8"))
        gdata = json.loads(gfile.read_text(encoding="utf-8"))
        pdata = json.loads(pfile.read_text(encoding="utf-8"))
        old_board = json.loads(before_bytes[board].decode("utf-8"))
        check("156: the themes file names the case P1 - Cora and its boards are as they were",
              tdata["case"] == "P1 - Cora" and tdata["boards"] == old_board["boards"] and tdata["workbook"] == book.name)
        check("156: the GETs file keys the case by its new label everywhere, its study, its copy and its cards, and "
              "names the old one nowhere",
              "P1 - Cora" in gdata["study"] and "P1 - Cora" in gdata["cases"]
              and "P1 - Cora/g1" in json.dumps(gdata["boards"]) and "P1 - Ada" not in json.dumps(gdata), str(list(gdata["cases"])))
        check("156: the project's file keeps his order under the new label and the new name by the folder's",
              pdata["order"] == ["P2 - Bea", "P1 - Cora"] and pdata["names"] == {"P1 - Ada": "Cora"}
              and pdata["name"] == "Gardens", str(pdata))
        copies = sorted(p.name for p in (ada / "_Archive").iterdir())
        held = {p.name: p.read_bytes() for p in (ada / "_Archive").iterdir()}
        root_copies = {p.name: p.read_bytes() for p in (root / "_Archive").iterdir()}
        check("156: a copy of every file it wrote went into _Archive first, the case's for its own and the project's for "
              "the GETs file and the project file, as the app's backups are named, each holding the file as it was",
              ada.is_dir() and book.is_file() and raw.is_file() and len(copies) == 3
              and all("(pre-rename " in n for n in copies)
              and sorted(held.values()) == sorted([before_bytes[book], before_bytes[raw], before_bytes[board]])
              and sorted(root_copies.values()) == sorted([before_bytes[gfile], before_bytes[pfile]])
              and all(n.startswith(("idiograph-gets (pre-rename ", "idiograph-project (pre-rename ")) for n in root_copies),
              str(copies + list(root_copies)))
        rows = [c for c in idiograph_routes.api_cases({})["projects"][0]["participants"]]
        opened = idiograph_routes.api_open({"path": str(book)})
        check("156: the row, the PETs board, the GETs, the statements screen's bar and the recent list show the new "
              "name with no restart, the folder kept",
              [c["case"] for c in rows] == ["P2 - Bea", "P1 - Cora"] and all(c["folder"] is True for c in rows)
              and idiograph_routes.api_themes({"workbook": str(book)})["case"] == "P1 - Cora"
              and "P1 - Cora" in [c["case"] for c in idiograph_routes.api_gets({"workbook": str(book)})["cases"]]
              and opened["name"] == "P1 Cora - EN & ES"
              and server_mod.STATE_MEMORY["recent"][0]["case"] == "P1 - Cora"
              and [c["label"] for c in idiograph_routes.standing_cases(root)["Cora"]] == ["P1 - Cora"],
              str([c["case"] for c in rows]))

        # ── E. renamed again with the folder ticked: the folder and the files named after the participant move
        ticked = idiograph_routes.api_rename({"op": "plan", "root": rid, "case": "P1 - Cora", "name": "Dara", "folder": True})
        moved = idiograph_routes.api_rename({"op": "rename", "root": rid, "case": "P1 - Cora", "name": "Dara", "folder": True})
        dara = root / "P1 - Dara"
        nbook, nraw = dara / "P1 Dara - EN & ES.xlsx", dara / "Source" / "P1 Dara - transcript.xlsx"
        check("156: ticked, the folder and each file named after the participant take the new name, the sidecars with "
              "their workbook, and the list shown first is what changed",
              not ada.exists() and dara.is_dir() and nbook.is_file() and nraw.is_file()
              and themes_mod.themes_path(nbook).is_file() and rounds_mod.progress_path(nbook).is_file()
              and moved["lines"] == ticked["lines"] and moved["folder_lines"] == ticked["folder_lines"],
              str([ticked["folder_lines"], ticked["lines"]]))
        gdata = json.loads(gfile.read_text(encoding="utf-8"))
        pdata = json.loads(pfile.read_text(encoding="utf-8"))
        tdata = json.loads(themes_mod.themes_path(nbook).read_text(encoding="utf-8"))
        check("156: the names entry goes with the folder, and the themes file and the GETs copy name the workbook as it is now",
              "names" not in pdata and pdata["order"] == ["P2 - Bea", "P1 - Dara"]
              and tdata["case"] == "P1 - Dara" and tdata["workbook"] == nbook.name
              and gdata["cases"]["P1 - Dara"]["workbook"] == nbook.name and "P1 - Cora" not in json.dumps(gdata)
              and names_in(nbook)["Initial"].count("Dara") == 3 and names_in(nraw)["Initial"].count("Dara") == 3)
        check("156: the earlier backups moved with the folder, every one kept, and the recent list points at the file "
              "where it is now",
              len(list((dara / "_Archive").iterdir())) >= 3
              and server_mod.abs_path(server_mod.STATE_MEMORY["recent"][0]["path"]).resolve() == nbook.resolve()
              and server_mod.STATE_MEMORY["recent"][0]["case"] == "P1 - Dara"
              and [c["case"] for c in idiograph_routes.api_cases({})["projects"][0]["participants"]] == ["P2 - Bea", "P1 - Dara"])
        gone = refusal({"op": "rename", "root": rid, "case": "P1 - Ada", "name": "Eve", "folder": False})
        check("156: a row's old label once renamed names no case, and is refused in one line",
              gone == idiograph_routes.NO_CASE, gone)
        # a folder with a second part after the pseudonym, kept: the project file keys the new name by the
        # folder's label, and the second part is written nowhere
        two_part = root / "P3 - {}-{}".format("Fen", "Example")
        shutil.copytree(root / "P2 - Bea", two_part)
        kept_two = idiograph_routes.api_rename({"op": "rename", "root": rid, "case": "P3 - Fen", "name": "Gale", "folder": False})
        pdata = json.loads(pfile.read_text(encoding="utf-8"))
        check("156: a folder with a second part keeps it in its name alone, the project file keying the new name by its "
              "label and the second part written nowhere",
              two_part.is_dir() and kept_two["case"] == "P3 - Gale" and pdata["names"] == {"P3 - Fen": "Gale"}
              and "Example" not in pfile.read_text(encoding="utf-8") + gfile.read_text(encoding="utf-8")
              and "P3 - Gale" in [c["case"] for c in idiograph_routes.api_cases({})["projects"][0]["participants"]],
              str(pdata.get("names")))

        # ── F. a statement's passage, checked by the server before anything changes
        opened = idiograph_routes.api_open({"path": str(nbook), "passage": {"sheet": "Initial", "row": turns[0]["row"]}})
        recent = json.dumps(server_mod.STATE_MEMORY)
        missing = None
        try:
            idiograph_routes.api_open({"path": str(nbook), "passage": {"sheet": "Initial", "row": 2}})
        except WorkbookError as exc:
            missing = str(exc)
        check("156: Experiential statements opens at a statement's passage while it is one of the participant's, and "
              "refuses one that is not, the interviewer's or gone, in one line with the recent list as it was",
              opened["path"] == server_mod.rel_path(nbook) and missing == idiograph_routes.NO_PASSAGE
              and json.dumps(server_mod.STATE_MEMORY) == recent, str(missing))
        check("156: the routes are in the table, Rename takes a POST alone",
              server_mod.ROUTES.get("/api/rename") is idiograph_routes.api_rename and "/api/rename" in server_mod.POST_ONLY)

        # ── F2. each state's list is exactly what its Rename writes (16 October later, after the screenshot check):
        # two invented projects alike, no order of their rows, one renamed with the folder kept and one ticked, every
        # file compared before and after
        pond_vtt = ("WEBVTT\n\n00:00:01.000 --> 00:00:03.000\n<v Kit>What do you watch for at the pond?</v>\n\n"
                    "00:00:04.000 --> 00:00:08.000\n<v Wren>The newts, once the water warms.</v>\n\n"
                    "00:00:09.000 --> 00:00:11.000\n<v Kit>And then?</v>\n\n"
                    "00:00:12.000 --> 00:00:15.000\n<v Wren>The heron, who comes for them.</v>\n")

        def pond(where: Path) -> tuple:
            where.mkdir(parents=True)
            got = idiograph_routes.api_new_project({"op": "make", "folder": str(where), "name": "Ponds",
                                              "research_question": "How do people experience tending a pond?",
                                              "files": [{"name": "Initial.vtt", "data": b64(pond_vtt), "pseudonym": "Wren",
                                                         "interview": "Initial", "interviewer": "Kit"}]})
            folder = where / "P1 - Wren"
            wb = folder / "P1 Wren - EN & ES.xlsx"
            said_rows = [r for r in idiograph_routes.api_open({"path": str(wb)})["sheets"][0]["rows"] if r["name"] == "Wren"]
            idiograph_routes.api_commit({"path": str(wb), "sheet": "Initial", "row": said_rows[0]["row"],
                                   "es": "Newts as the sign of warm water", "en": "", "kq": "once the water warms"})
            pets = idiograph_routes.api_themes({"workbook": str(wb)})
            idiograph_routes.api_themes_save({"workbook": str(wb), "version": {
                **pets["version"], "cards": {c["key"]: {"x": c["x"], "y": c["y"], "text": c["text"]} for c in pets["cards"]},
                "groups": [{"id": "g1", "label": "Watching the water", "members": [c["key"] for c in pets["cards"]],
                            "x": 0, "y": -40}], "discarded": []}})
            seen = idiograph_routes.api_gets({"workbook": str(wb)})
            idiograph_routes.api_gets_save({"workbook": str(wb), "version": dict(
                seen["version"], cards={c["key"]: {"x": c["x"], "y": c["y"], "text": c.get("text", "")} for c in seen["cards"]},
                groups=[], discarded=[], picks={}, notes=[])})
            return got["project"]["id"], folder

        def what_changed(where: Path, folder: Path, rid: str, ticked: bool) -> dict:
            answer, inner = idiograph_routes.rename_plan(where, folder, "Lark", ticked, server_mod.config())
            held = {p: p.read_bytes() for p in where.rglob("*")
                    if p.is_file() and "_Archive" not in p.parts and not p.name.endswith(".lock")}
            recent = json.dumps(server_mod.STATE_MEMORY)
            done = idiograph_routes.api_rename({"op": "rename", "root": rid, "case": "P1 - Wren", "name": "Lark", "folder": ticked})
            moves, target = dict(inner["moves"]), inner["target"]

            def now(p: Path) -> Path:
                p = moves.get(p, p)
                return target / p.relative_to(folder) if target is not None and folder in p.parents else p
            changed = {p for p, was in held.items() if not now(p).is_file() or now(p).read_bytes() != was}
            kinds = {"book": set(inner["books"]), "boards": {themes_mod.themes_path(b) for b in inner["themes"]},
                     "gets": {where / gets_mod.FILE}, "project": {where / server_mod.PROJECT_FILE}}
            listed = {"book": sum(1 for x in answer["lines"] if "'s name on " in x),
                      "boards": sum(1 for x in answer["lines"] if "PETs boards" in x),
                      "gets": sum(1 for x in answer["lines"] if x == "The project's GETs"),
                      "project": sum(1 for x in answer["lines"] if x.startswith("The project's") and x != "The project's GETs"),
                      "recent": sum(1 for x in answer["lines"] if x == "Idiograph's own list of recent participants")}
            return {"answer": answer, "done": done, "changed": changed, "kinds": kinds, "listed": listed,
                    "recent": json.dumps(server_mod.STATE_MEMORY) != recent, "moves": inner["moves"], "target": target,
                    "moved": all(not a.exists() and now(a).is_file() for a, _b in inner["moves"])}

        kept_pond, ticked_pond = base / "Pond kept", base / "Pond ticked"
        kept_id, kept_case = pond(kept_pond)
        tick_id, tick_case = pond(ticked_pond)
        states = {"kept": what_changed(kept_pond, kept_case, kept_id, False),
                  "ticked": what_changed(ticked_pond, tick_case, tick_id, True)}
        wrong = []
        for state, got in states.items():
            for kind in ("book", "boards", "gets", "project"):
                written = got["changed"] & got["kinds"][kind]
                if len(written) != got["listed"][kind]:
                    wrong.append(f"{state} {kind}: {len(written)} written, {got['listed'][kind]} listed")
            if got["changed"] - set().union(*got["kinds"].values()):
                wrong.append(f"{state} wrote what no line says")
            if got["recent"] != bool(got["listed"]["recent"]):
                wrong.append(f"{state} recent")
            if got["done"]["lines"] != got["answer"]["lines"] or got["done"]["folder_lines"] != got["answer"]["folder_lines"]:
                wrong.append(f"{state} answered other lines")
        check("156, 16 October later: in both states each line of the list stands for a file its Rename writes and each "
              "file it writes has its line, the workbooks, the PETs boards, the GETs, the project's file and the recent "
              "list, compared byte for byte before and after", not wrong, "; ".join(wrong))
        kept_lines, tick_lines = states["kept"]["answer"]["lines"], states["ticked"]["answer"]["lines"]
        dropped = [x for x in kept_lines if x not in tick_lines]
        check("156, 16 October later: ticking drops no line that still changes, the one line it drops the project's note "
              "of the new name, which a kept folder needs and a moved folder never writes, the project's file left as it "
              "was",
              len(dropped) == 1
              and (kept_pond / server_mod.PROJECT_FILE) in states["kept"]["changed"]
              and (ticked_pond / server_mod.PROJECT_FILE) not in states["ticked"]["changed"]
              and not [x for x in tick_lines if x not in kept_lines], str([kept_lines, tick_lines]))
        check("156, 16 October later: ticked, the folder and each workbook listed moved, its progress and PETs boards with "
              "it, the list's folder lines one for the folder and one for each workbook",
              states["ticked"]["moved"] and states["ticked"]["target"] == ticked_pond / "P1 - Lark"
              and len(states["ticked"]["answer"]["folder_lines"]) == 3
              and len(states["ticked"]["moves"]) == 4 and states["kept"]["answer"]["folder_lines"] == [],
              str(states["ticked"]["answer"]["folder_lines"]))
    finally:
        server_mod.CONFIG_PATH, server_mod.ROOT_OVERRIDE, server_mod.STATE_PATH, server_mod.STATE_MEMORY = kept

    if not node:
        skip("156: the canvas's passage in node", "no node on this machine")
    else:
        harness = r"""
const TH = { mode: 'pets', live: true, busy: false, dirty: false, path: 'garden/P1 Dara - EN & ES.xlsx', label: 'P1 - Dara',
  back: 'BACK', to: 'cases', meta: { id: 'v2' }, view: { x: 40, y: -12, z: 0.8 }, lastPick: { kind: 'card', id: 'Initial:5:0' },
  sel: { cards: new Set(['Initial:5:0']), groups: new Set(['g1']), stickies: new Set() }, v: null, ask: 0, viewing: null };
const said = [];
const calls = [];
const say = (t) => said.push(t);
const $ = (id) => ({ hidden: false, textContent: '', style: {} });
const noop = () => {};
const thTitleDone = noop, thNoteDone = noop, thVmenu = noop, thViewEnd = noop, thPile = noop, thXmenu = noop,
  thCasemenu = noop, thSideShut = noop, thAiCard = noop, thExported = noop, thMade = noop, thMenuClose = noop;
const thFlush = async () => {};
const gtSplit = (key) => { const [kase, kind, ident] = key.split('/'); return { kase, kind, ident }; };
const GETS_CASES = [{ case: 'P2 - Bea', path: 'garden/P2 Bea - EN & ES.xlsx' }];
const gtCase = (name) => GETS_CASES.find((c) => c.case === name) || null;
let OPENED = null;
const openPassage = (book, at, how) => { OPENED = { book, at, to: how.to }; how.leave(); return true; };
const navGo = (again, open) => open();
const themesOpen = (path, opts) => { calls.push(['pets', path, opts.board, opts.to, opts.back, opts.restore.view.z]); };
const getsOpen = (path, opts) => { calls.push(['gets', path, opts.board, opts.to]); };
const thLocked = () => false;
const thParents = () => ({});
const thUnit = () => 'PET';
const thIsGroup = (v, id) => v.groups.some((g) => g.id === id);
const thStickies = () => [];
const thIsSticky = () => false;
const thTopOf = () => null, thStackItems = () => [], thGroupItems = () => [], thUnderShown = () => false, thWaits = () => false, thAlignIds = () => [];
const thSetOf = (item) => item.kind === 'card' ? TH.sel.cards : TH.sel.groups;
const thSelected = (item) => thSetOf(item).has(item.id);
const thDrawSel = () => calls.push(['sel', [...TH.sel.cards], [...TH.sel.groups]]);
const thPanelFollow = () => calls.push(['panel']);
const thView = () => calls.push(['view', TH.view.x, TH.view.y, TH.view.z]);
// a phone's canvas, 360 wide, for the card the way back keeps in view (16 October later)
const thStage = () => ({ clientWidth: 360, clientHeight: 600 });
const thSize = () => ({ w: 200, h: 60 });
"""
        pieces = [harness, line(themes_js, "const TH_NO_PASSAGE = ")] + [whole(themes_js, n) for n in (
            "thIsStatement", "thLineOf", "thToPassage", "thBackFromPassage", "thMenuItems")]
        scenario = r"""
(async () => {
const out = {};
TH.v = { cards: { 'Initial:5:0': { key: 'Initial:5:0', text: 'Kneeling as the work' } }, groups: [{ id: 'g1', label: 'L', members: [] }],
  discarded: [] };
out.lines = [thLineOf('Initial:12:0'), thLineOf('2d:3:1'), thLineOf('Sheet:with:colon:7:2'), thLineOf('bad')];
out.menu = thMenuItems(TH.v, { kind: 'card', id: 'Initial:5:0' }).map((i) => i.label);
out.labelMenu = thMenuItems(TH.v, { kind: 'group', id: 'g1' }).map((i) => i.label);
await thToPassage('Initial:5:0');
out.opened = OPENED;
out.live = TH.live;
// the way back, from Experiential statements's bar
const back = calls.length;
TH.live = true;
TH.view = { x: 0, y: 0, z: 1 };
TH.sel = { cards: new Set(), groups: new Set(), stickies: new Set() };
out.again = null;
// the board it reopens, with what the open hands thBackFromPassage
const restoreArgs = [];
const realOpen = themesOpen;
out.call = calls[back - 1] || null;
thBackFromPassage({ view: { x: 40, y: -12, z: 0.8 }, pick: { kind: 'card', id: 'Initial:5:0' },
  sel: { cards: ['Initial:5:0', 'Initial:9:9'], groups: ['g1', 'gone'], stickies: [] } });
out.restored = { view: TH.view, cards: [...TH.sel.cards], groups: [...TH.sel.groups], pick: TH.lastPick };
// the window narrowed while the passage was open: the card it came from, now off the canvas, back in its middle at
// the same zoom, a card still in view left where it is, and a card gone leaving the view as it was
TH.v = { cards: { 'Initial:5:0': { key: 'Initial:5:0', x: 1000, y: 200 } }, groups: [], discarded: [] };
thBackFromPassage({ view: { x: 0, y: 0, z: 0.5 }, from: 'Initial:5:0', sel: {} });
out.narrowed = { ...TH.view };
thBackFromPassage({ view: { x: 0, y: 0, z: 0.5 }, from: 'Initial:9:9', sel: {} });
out.goneFrom = { ...TH.view };
TH.v.cards['Initial:5:0'].x = 100;
thBackFromPassage({ view: { x: 0, y: 0, z: 0.5 }, from: 'Initial:5:0', sel: {} });
out.inView = { ...TH.view };
// on GETs: a statement card goes to its case's workbook, a PET card is no statement
TH.mode = 'gets';
TH.live = true;
TH.v = { cards: { 'P2 - Bea/es/Initial:4:0': { key: 'P2 - Bea/es/Initial:4:0', kind: 'es', case: 'P2 - Bea' },
                  'P2 - Bea/g1': { key: 'P2 - Bea/g1', kind: 'pet', case: 'P2 - Bea' } }, groups: [], discarded: [] };
out.getsMenu = thMenuItems(TH.v, { kind: 'card', id: 'P2 - Bea/es/Initial:4:0' }).map((i) => i.label);
out.petMenu = thMenuItems(TH.v, { kind: 'card', id: 'P2 - Bea/g1' }).map((i) => i.label);
OPENED = null;
await thToPassage('P2 - Bea/g1');
out.petOpened = OPENED;
await thToPassage('P2 - Bea/es/Initial:4:0');
out.getsOpened = OPENED;
console.log(JSON.stringify(out));
})().catch((err) => { console.error(String(err && err.stack || err)); process.exit(1); });
"""
        script = scratch / "rename-156.js"
        script.write_text(support.i18n_js() + "\n".join(pieces + [scenario]), encoding="utf-8")
        run = subprocess.run([node, str(script)], capture_output=True, text=True, encoding="utf-8")
        if run.returncode != 0:
            check("156: the canvas's passage runs in node", False, run.stderr.strip()[:300])
        else:
            out = json.loads(run.stdout)
            check("156: in node, a statement's key splits into its sheet, row and line from the right, and a key that is "
                  "none gives none",
                  out["lines"] == [{"sheet": "Initial", "row": 12, "line": 0}, {"sheet": "2d", "row": 3, "line": 1},
                                   {"sheet": "Sheet:with:colon", "row": 7, "line": 2}, None], str(out["lines"]))
            check("156: in node, a statement card's menu has Go to the passage after Inspect, a label's has none, and on "
                  "GETs a statement card's has it and a PET card's not",
                  out["menu"][:2] == ["Inspect", "Go to the passage"] and "Go to the passage" not in out["labelMenu"]
                  and "Rename" in out["labelMenu"] and out["getsMenu"][:2] == ["Inspect", "Go to the passage"]
                  and "Go to the passage" not in out["petMenu"], str([out["menu"], out["getsMenu"], out["petMenu"]]))
            check("156: in node, the passage opens on the case's workbook at the statement's sheet, row and line, the "
                  "board put away, and on GETs the statement's case's own workbook, a PET card opening none",
                  out["opened"] == {"book": "garden/P1 Dara - EN & ES.xlsx", "at": {"sheet": "Initial", "row": 5, "line": 0},
                                    "to": "pets"} and out["live"] is False and out["petOpened"] is None
                  and out["getsOpened"] == {"book": "garden/P2 Bea - EN & ES.xlsx", "at": {"sheet": "Initial", "row": 4, "line": 0},
                                            "to": "gets"}, str([out["opened"], out["getsOpened"]]))
            check("156: in node, the way back puts the canvas where it was and selects what was selected and is still there",
                  out["restored"] == {"view": {"x": 40, "y": -12, "z": 0.8}, "cards": ["Initial:5:0"], "groups": ["g1"],
                                      "pick": {"kind": "card", "id": "Initial:5:0"}}, str(out["restored"]))

    if not node:
        skip("156: the menu's path, the way back's word and the renamed row in node", "no node on this machine")
    else:
        menu_harness = r"""
const TH = { mode: 'pets', live: true, busy: false, dirty: false, path: 'garden/P1 Dara - EN & ES.xlsx', label: 'P1 - Dara',
  back: 'BACK', to: 'cases', meta: { id: 'v2' }, view: { x: 40, y: -12, z: 0.8 }, lastPick: null,
  sel: { cards: new Set(), groups: new Set(), stickies: new Set() }, v: null, ask: 0, viewing: null, boards: [], menu: null };
const said = [];
const say = (t) => said.push(t);
const els = {};
const $ = (id) => (els[id] = els[id] || { hidden: false, textContent: '', style: {} });
const noop = () => {};
const thTitleDone = noop, thNoteDone = noop, thVmenu = noop, thViewEnd = noop, thPile = noop, thXmenu = noop,
  thCasemenu = noop, thSideShut = noop, thAiCard = noop, thExported = noop, thMade = noop, thPanelFollow = noop;
const thFlush = async () => {};
const gtSplit = (key) => { const [kase, kind, ident] = key.split('/'); return { kase, kind, ident }; };
const GETS_CASES = [{ case: 'P2 - Bea', path: 'garden/P2 Bea - EN & ES.xlsx' }];
const gtCase = (name) => GETS_CASES.find((c) => c.case === name) || null;
let OPENED = null;
const openPassage = (book, at, how) => { OPENED = { book, at, to: how.to }; how.leave(); return true; };
const navGo = (again, open) => open();
const themesOpen = noop, getsOpen = noop;
const thLocked = () => false;
const thParents = () => ({});
const thUnit = () => 'PET';
const thIsGroup = (v, id) => v.groups.some((g) => g.id === id);
const thIsSticky = () => false;
const thOnCanvas = (v, key) => !!v.cards[key] && !v.discarded.includes(key);
const thTopOf = () => null, thStackItems = () => [], thGroupItems = () => [], thUnderShown = () => false, thWaits = () => false, thAlignIds = () => [];
const thCopyTargets = () => [];
const thSetOf = (item) => (item.kind === 'card' ? TH.sel.cards : TH.sel.groups);
const thSelected = (item) => thSetOf(item).has(item.id);
const thSelectOnly = (item) => { TH.sel.cards = new Set(item.kind === 'card' ? [item.id] : []); };
const esc = (s) => String(s);
const TH_TICK_ICON = '';
const window = { innerWidth: 1280, innerHeight: 800 };
let POP = null;
const document = { body: { appendChild: (el) => { POP = el; } }, createElement: () => ({
  className: '', innerHTML: '', style: {}, offsetWidth: 160, offsetHeight: 120, handlers: {}, removed: false,
  setAttribute() {}, addEventListener(type, f) { this.handlers[type] = f; }, remove() { this.removed = true; } }) };
"""
        menu_pieces = [menu_harness, line(themes_js, "const TH_NO_PASSAGE = "), line(themes_js, "const TH_TAKES = "), line(themes_js, "const TH_OUTS = "),
                       line(themes_js, "const thLeaveLabel = ")] + [whole(themes_js, n) for n in (
            "thIsStatement", "thLineOf", "thToPassage", "thMenuItems", "gtUnfoldPet", "gtUnfoldable", "gtMenuItems", "thMenuOpen", "thMenuClose", "thMenuDo")]
        menu_scenario = r"""
(async () => {
const out = {};
// a right-click's menu on a card, then a click on the entry of that label as the menu's own listener takes it
async function choose(id, label) {
  OPENED = null;
  POP = null;
  TH.live = true;
  thMenuOpen({ kind: 'card', id }, 100, 100);
  if (!POP) return { menu: null };
  const labels = [...POP.innerHTML.matchAll(/data-cmenu="(\d+)"[^>]*>(?:<span[^>]*><\/span>)?<span>([^<]*)<\/span>/g)]
    .map((m) => [Number(m[1]), m[2]]);
  const hit = labels.find((l) => l[1] === label);
  const target = { closest: (sel) => (sel === '[data-cmenu]' && hit ? { dataset: { cmenu: String(hit[0]) }, disabled: false } : null) };
  POP.handlers.click({ target });
  await new Promise((r) => setTimeout(r, 0));
  return { menu: labels.map((l) => l[1]), opened: OPENED, shut: POP.removed && TH.menu === null, live: TH.live,
    selected: [...TH.sel.cards] };
}
TH.v = { cards: { 'Initial:5:0': { key: 'Initial:5:0', text: 'Kneeling as the work' } }, groups: [], discarded: [] };
out.pets = await choose('Initial:5:0', 'Go to the passage');
TH.mode = 'gets';
TH.menu = null;
TH.v = { cards: { 'P2 - Bea/es/Initial:4:0': { key: 'P2 - Bea/es/Initial:4:0', kind: 'es', case: 'P2 - Bea' },
                  'P2 - Bea/g1': { key: 'P2 - Bea/g1', kind: 'pet', case: 'P2 - Bea' } }, groups: [], discarded: [] };
out.gets = await choose('P2 - Bea/es/Initial:4:0', 'Go to the passage');
TH.menu = null;
out.pet = await choose('P2 - Bea/g1', 'Go to the passage');
console.log(JSON.stringify(out));
})().catch((err) => { console.error(String(err && err.stack || err)); process.exit(1); });
"""
        script = scratch / "rename-156-menu.js"
        script.write_text(support.i18n_js() + "\n".join(menu_pieces + [menu_scenario]), encoding="utf-8")
        run = subprocess.run([node, str(script)], capture_output=True, text=True, encoding="utf-8")
        if run.returncode != 0:
            check("156: the menu's path runs in node", False, run.stderr.strip()[:300])
        else:
            out = json.loads(run.stdout)
            check("156, 16 October later: in node, a right-click on a PETs statement card and a click on Go to the passage "
                  "in the menu it draws shuts the menu, puts the board away and opens the statement's passage, as the "
                  "double-click does",
                  out["pets"]["menu"][:2] == ["Inspect", "Go to the passage"] and out["pets"]["shut"] is True
                  and out["pets"]["live"] is False and out["pets"]["selected"] == ["Initial:5:0"]
                  and out["pets"]["opened"] == {"book": "garden/P1 Dara - EN & ES.xlsx",
                                                "at": {"sheet": "Initial", "row": 5, "line": 0}, "to": "pets"},
                  str(out["pets"]))
            check("156, 16 October later: in node, the same on a GETs statement card opens its own case's passage, and a "
                  "PET card's menu has no Go to the passage and opens nothing",
                  out["gets"]["opened"] == {"book": "garden/P2 Bea - EN & ES.xlsx",
                                            "at": {"sheet": "Initial", "row": 4, "line": 0}, "to": "gets"}
                  and out["gets"]["shut"] is True and "Go to the passage" not in out["pet"]["menu"]
                  and out["pet"]["opened"] is None, str([out["gets"], out["pet"]]))

    # ── I. the faint done bar, for a passage he skipped alone, the counts as they were
    if not node:
        skip("156: the done bars in node", "no node on this machine")
    else:
        bars = "\n".join([line(app, "const DONE_LEVEL = "), whole(app, "doneLevels"), r"""
const rows = [{ i: 0, stop: true, key: 'a' }, { i: 1, stop: false }, { i: 2, stop: true, key: 'b' }, { i: 3, stop: false },
  { i: 4, stop: true, key: 'c' }, { i: 5, stop: false }, { i: 6, stop: true, key: 'd' }];
const states = { a: 'passed', b: 'passed', c: 'reviewed-empty', d: 'has-content' };
const level = doneLevels(rows, states);
console.log(rows.map((r) => level.get(r.i)).join(''));
"""])
        script = scratch / "rename-156-bars.js"
        script.write_text(support.i18n_js() + bars, encoding="utf-8")
        run = subprocess.run([node, str(script)], capture_output=True, text=True, encoding="utf-8")
        levels = run.stdout.strip()
        check("156: in node, a passage jumped over carries no bar, one he skipped the faint one, one with a statement "
              "the full one, and the interviewer's between take the fainter of the two",
              levels == "0000112", levels)
    passed_rows = [{"sheet": "Initial", "row": r, "name": "Ada", "es": "x" if r == 4 else ""} for r in (2, 3, 4)]
    progress = {"rows": {"Initial:4": "has-content"}, "last": {"sheet": "Initial", "row": 4}}
    states = rounds_mod.row_states([{"name": "Initial", "rows": passed_rows}], progress, "kit")
    check("156: the server's states and the counts are as they were, a passage jumped over still passed and decided",
          states == {"Initial:2": "passed", "Initial:3": "passed", "Initial:4": "has-content"}
          and sum(1 for v in states.values() if v in rounds_mod.DECIDED) == 3, str(states))

    # ── J. the PRISMA flow from the active run alone, across two invented runs
    review = base / "review"
    first, second = review / "runs" / "2026-10-01", review / "runs" / "2026-10-08"
    for f in (first, second):
        f.mkdir(parents=True)
    head = "rec_id,title,abstract,sources,doi\n"
    (first / "screening.csv").write_text(head + "R001,Bees at dawn,An invented abstract,PsycInfo,\n"
                                         "R002,Hives in the city,Another,OpenAlex,\nR003,A swarm in May,A third,PsycInfo,\n",
                                         encoding="utf-8")
    log_rows = ("date,source,interface,query,hits,records_saved,note\n"
                "2026-10-01,PsycInfo,,,9,9,\n2026-10-01,OpenAlex,,,8,8,\n")
    (first / "log.csv").write_text(log_rows, encoding="utf-8")
    (first / "run.json").write_text(json.dumps({"date": "2026-10-01", "version": 1, "draft": True}), encoding="utf-8")
    (second / "screening.csv").write_text(head + "R001,Bees at dawn,An invented abstract,PsycInfo,\n"
                                          "R002,Hives in the city,Another,OpenAlex; PsycInfo,\n"
                                          "R003,A swarm in May,A third,PsycInfo,\n"
                                          "R004,Honey and grief,A fourth,PsycInfo,\nR005,Calm keepers,A fifth,OpenAlex,\n"
                                          "R006,From a reference list,A sixth,citation chasing,\n", encoding="utf-8")
    (second / "log.csv").write_text(log_rows + "2026-10-08,PsycInfo,,,3,3,\n2026-10-08,OpenAlex,,,2,2,\n", encoding="utf-8")
    (second / "run.json").write_text(json.dumps({"date": "2026-10-08", "version": 2, "draft": False,
                                                 "follows": {"date": "2026-10-01", "carried": 3, "new": 3, "again": 1},
                                                 "carried": {"log": 1, "searches": 2}}), encoding="utf-8")
    sift.append(second, {"n": 1, "at": "2026-10-08T10:00:00+01:00", "act": "follow", "run": "2026-10-01",
                         "records": ["R001", "R002", "R003"], "new": ["R004", "R005", "R006"], "again": ["R002"], "tool": "Sift"})
    sift.decide(second, "R001", "ta", "exclude", reason="E1")
    sift.decide(second, "R004", "ta", "exclude", reason="E2")
    sift.decide(second, "R002", "ta", "include")
    c = sift.counts(sift.load(second))
    flow = sift.refresh_prisma(second)
    on_disk = (second / sift.PRISMA_NAME).read_text(encoding="utf-8")
    check("156: the flow counts the active run's own searches alone, by database, and its duplicates, the earlier "
          "run's rows at the head of its log.csv out of it",
          c["flow"]["search"]["saved"] == 5 and c["flow"]["search"]["sources"] == {
              "PsycInfo": {"hits": 3, "saved": 3}, "OpenAlex": {"hits": 2, "saved": 2}}
          and c["flow"]["duplicates"] == 2 and c["flow"]["databases"] == 3
          and 'db["Records identified<br/>from databases<br/>(n = 5)<br/>PsycInfo (n = 3)<br/>OpenAlex (n = 2)"]' in flow
          and 'dup["Duplicate records<br/>removed (n = 2)"]' in flow and "(n = 17)" not in flow and "(n = 22)" not in flow,
          flow[:400])
    check("156: every box onward counts the run's own records, those only the earlier run found out of it, the "
          "records from other methods kept, while the screen's counts and the export keep every record",
          c["flow"]["records"] == 4 and c["flow"]["stages"]["ta"]["records"] == 4
          and c["flow"]["stages"]["ta"]["exclude"] == 1 and c["flow"]["stages"]["ta"]["include"] == 1
          and 'screened["Records screened<br/>(n = 4)' in flow and 'excluded["Records excluded<br/>(n = 1)<br/>E2 (n = 1)"]' in flow
          and c["stages"]["ta"]["records"] == 6 and c["stages"]["ta"]["exclude"] == 2
          and ["title and abstract", "records", 6] in sift.count_rows(c)
          and 'other["Records identified<br/>from other methods<br/>(n = 1)' in flow, flow[:600])
    check("156: prisma.md beside the CSV holds the same flow, and the earlier run's own flow is its own search",
          on_disk == sift.prisma_markdown(flow)
          and 'db["Records identified<br/>from databases<br/>(n = 17)<br/>PsycInfo (n = 9)<br/>OpenAlex (n = 8)"]'
          in sift.prisma_source(sift.counts(sift.load(first))))
    alone = base / "alone"
    alone.mkdir()
    (alone / "screening.csv").write_text(head + "R001,Bees at dawn,An invented abstract,PsycInfo,\n", encoding="utf-8")
    (alone / "log.csv").write_text(log_rows + "2026-10-08,PsycInfo,,,3,3,\n", encoding="utf-8")
    lone = sift.counts(sift.load(alone))
    lone_flow = sift.prisma_source(lone)
    check("156: a screening of no run whose log.csv holds two searches has no active run, its first box says so in one "
          "line and no sum and no duplicates are drawn",
          lone["flow"]["search"]["active"] is False and lone["flow"]["duplicates"] is None
          and 'db["Records identified<br/>from databases<br/>No active run to count"]' in lone_flow
          and "dup[" not in lone_flow and sift.NO_ACTIVE == "No active run to count", lone_flow[:300])

