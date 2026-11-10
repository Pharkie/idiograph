from __future__ import annotations

import base64
import json
import shutil
from pathlib import Path

from workbook import WorkbookError

from .support import check
from . import support
import idiograph_routes

# Every word invented: Kit asks newcomers to an allotment about their first year on it, before the season,
# at midsummer and after the harvest. Wren is interviewed at T1 and T2 and not at T3.
T1_TEXT = ("Kit: [00:00:03] What did you expect of the plot?\nWren: [00:00:08] Tidy rows, like the seed packets.\n"
           "Kit: [00:00:40] And the shed?\nWren: [00:35:55] I had not looked inside it yet.\n")
T2_TEXT = ("Kit: [00:00:02] How is it now?\nWren: [00:00:06] I ask the neighbours before I read the packet.\n"
           "Kit: [00:00:30] Why them?\nWren: [00:12:33] They know this soil.\n")
COMPOST_TEXT = ("Kit: [00:00:03] What did you expect of the heap?\nWren: [00:00:08] That it would smell.\n")
THREE = [{"label": "T1", "description": "Before the season"}, {"label": "T2", "description": "Midsummer"},
         {"label": "T3", "description": "After the harvest"}]


def test_timepoint_boards(scratch):
    print("\n235. Timepoints part 2 (21 October): a PETs canvas per timepoint reading its own sheets alone, the LPETs "
          "canvas made from the participant's timepoint PETs and saved, a timepoint not interviewed shown so, quotes "
          "cited with the timepoint, the command line's --timepoint and --lpets, and a project of one timepoint "
          "unchanged byte for byte")
    import cli
    import gets as gets_mod
    import mcp_server
    import rounds as rounds_mod
    import server as server_mod
    import themes
    import workbook as wb_mod

    b64 = lambda text: base64.b64encode(text.encode("utf-8")).decode("ascii")
    base = scratch / "a235"
    shutil.rmtree(base, ignore_errors=True)
    base.mkdir(parents=True)
    cfg_file = scratch / "a235-config.json"
    cfg_file.write_text(json.dumps({"projects": [], "interviewer": "Kit", "corpus": "", "gravity_reference": "",
                                    "corpus_exclude": []}), encoding="utf-8")
    kept = (server_mod.CONFIG_PATH, server_mod.ROOT_OVERRIDE, server_mod.STATE_PATH, server_mod.STATE_MEMORY)

    def tree(at: Path) -> dict:
        return {p.relative_to(at).as_posix(): (p.read_bytes() if p.is_file() and p.suffix != ".lock" else None)
                for p in sorted(at.rglob("*"))}

    def row(name, text, who, interview, **more):
        return dict({"name": name, "data": b64(text), "pseudonym": who, "interview": interview,
                     "speakers": {"Kit": "interviewer", who: "participant"}}, **more)

    def said_rows(book: Path, sheet: str) -> list[int]:
        import openpyxl
        wb = openpyxl.load_workbook(book, read_only=True)
        try:
            ws = wb[sheet]
            return [r for r, values in enumerate(ws.iter_rows(min_row=2, max_col=1, values_only=True), start=2)
                    if str(values[0] or "").strip() == "Wren"]
        finally:
            wb.close()

    def state(book: Path, **more) -> dict:
        return call("/api/themes", dict({"workbook": str(book)}, **more))

    def call(route: str, body: dict) -> dict:
        # through the dispatch's own scope, as a request from the page comes in
        with idiograph_routes.route_scope(route, body):
            return server_mod.ROUTES[route](body)

    def refused(route: str, body: dict) -> str:
        try:
            call(route, body)
        except WorkbookError as exc:
            return str(exc)
        return "answered"

    try:
        server_mod.CONFIG_PATH, server_mod.ROOT_OVERRIDE = cfg_file, None
        server_mod.STATE_PATH, server_mod.STATE_MEMORY = scratch / "a235-state.json", {"recent": []}

        # ── A. a project of one timepoint: the PETs canvas reads, opens and saves exactly as before
        compost = base / "Compost study"
        compost.mkdir()
        idiograph_routes.api_new_project({"op": "make", "folder": str(compost), "name": "Compost study",
                                    "research_question": "How do people take to keeping compost?",
                                    "files": [row("first.txt", COMPOST_TEXT, "Wren", "Interview")]})
        cbook = compost / "P1 - Wren" / "P1 Wren - EN & ES.xlsx"
        sheet0 = idiograph_routes.read_sheets(cbook)[1][0]
        crow = said_rows(cbook, sheet0)
        wb_mod.save_turn(cbook, sheet0, crow[0], "Expecting a smell", "", "")
        plain = state(cbook)
        with_one = state(cbook, timepoint=1)
        check("235: a project of one timepoint answers its PETs canvas as before: no timepoint, no timepoints, and "
              "naming T1 is the same canvas",
              "timepoint" not in plain and "timepoints" not in plain and [c["key"] for c in plain["cards"]]
              == [c["key"] for c in with_one["cards"]] == [themes.card_key(sheet0, crow[0], 0)], str(sorted(plain)))
        check("235: and a later timepoint there is refused",
              "no timepoint 2" in refused("/api/themes", {"workbook": str(cbook), "timepoint": 2}),
              refused("/api/themes", {"workbook": str(cbook), "timepoint": 2}))
        v = dict(plain["version"], cards={c["key"]: {"x": 0, "y": 0, "text": c["text"]} for c in plain["cards"]},
                 groups=[{"id": "g1", "label": "Smell", "members": [plain["cards"][0]["key"]], "x": 0, "y": -40}],
                 discarded=[], picks={})
        call("/api/themes-save", {"workbook": str(cbook), "version": v})
        held = themes.themes_path(cbook)
        files = sorted(p.name for p in held.parent.iterdir())
        check("235: its save writes the one themes file it always did, and no LPETs or timepoint file",
              held.name == "P1 Wren - EN & ES.themes.json" and held.exists()
              and not any("themes-t" in f or "lpets" in f for f in files), str(files))
        before = tree(compost)
        state(cbook)
        cli.run(["--root", str(compost), "--config", str(cfg_file), "board", "show", "Wren", "--json"])
        check("235: reading it again, on screen and by the command line, changes no byte", tree(compost) == before)
        check("235: LPETs are refused in a project of one timepoint",
              refused("/api/gets", {"workbook": str(cbook), "lpets": True}) == idiograph_routes.LPETS_ONE)

        # ── B. a project of three timepoints: Wren at T1 and T2, not at T3
        garden = base / "Allotment year"
        garden.mkdir()
        made = idiograph_routes.api_new_project({"op": "make", "folder": str(garden), "name": "Allotment year",
                                           "research_question": "How do newcomers make sense of a first year on a plot?",
                                           "files": [row("before.txt", T1_TEXT, "Wren", "Before")]})
        root_id = made["project"]["id"]
        idiograph_routes.api_project({"root": root_id, "timepoints": THREE})
        idiograph_routes.api_project({"root": root_id, "agents": True})
        idiograph_routes.api_add_transcripts({"op": "add", "root": root_id, "files": [
            row("midsummer.txt", T2_TEXT, "Wren", "Midsummer", timepoint=2)]})
        book = garden / "P1 - Wren" / "P1 Wren - EN & ES.xlsx"
        r1, r2 = said_rows(book, "Before"), said_rows(book, "Midsummer")
        wb_mod.save_turn(book, "Before", r1[0], "Expecting order\nTrusting the packet", "", "")
        wb_mod.save_turn(book, "Before", r1[1], "Not yet inside the shed", "", "I had not looked inside it yet.")
        wb_mod.save_turn(book, "Midsummer", r2[0], "Asking the neighbours first", "", "")
        wb_mod.save_turn(book, "Midsummer", r2[1], "The soil is known by others", "", "They know this soil.")
        t1 = state(book)
        t2 = state(book, timepoint=2)
        t2_label = state(book, timepoint="T2")
        sheets_of = lambda answer: {c["sheet"] for c in answer["cards"]}
        check("235: T1's canvas reads the T1 sheet's statements alone, and says it is at T1 among three",
              sheets_of(t1) == {"Before"} and len(t1["cards"]) == 3 and t1["timepoint"] == 1
              and [t["label"] for t in t1["timepoints"]] == ["T1", "T2", "T3"]
              and [t["state"] for t in t1["timepoints"]] == ["progress", "progress", "none"], str(sheets_of(t1)))
        check("235: T2's canvas, by its number or its label, reads the T2 sheet's statements alone",
              sheets_of(t2) == {"Midsummer"} and len(t2["cards"]) == 2 and t2["timepoint"] == 2
              and [c["key"] for c in t2_label["cards"]] == [c["key"] for c in t2["cards"]], str(sheets_of(t2)))

        # T2's board saved: its own file, T1's untouched
        k2 = [c["key"] for c in t2["cards"]]
        v2 = dict(t2["version"], cards={k: {"x": 0, "y": 40 * i} for i, k in enumerate(k2)},
                  groups=[{"id": "g1", "label": "Learning from neighbours", "members": k2, "x": 0, "y": -40}],
                  discarded=[], picks={})
        call("/api/themes-save", {"workbook": str(book), "timepoint": 2, "version": v2})
        t2_file = themes.themes_path(book, 2)
        t1_file = themes.themes_path(book)
        check("235: T2's board is saved in its own file beside T1's, no T1 file written by it",
              t2_file.name == "P1 Wren - EN & ES.themes-t2.json" and t2_file.exists() and not t1_file.exists(),
              str(sorted(p.name for p in t2_file.parent.iterdir())))
        k1 = [c["key"] for c in t1["cards"]]
        v1 = dict(t1["version"], cards={k: {"x": 0, "y": 40 * i} for i, k in enumerate(k1)},
                  groups=[{"id": "g1", "label": "Order expected", "members": k1[:2], "x": 0, "y": -40},
                          {"id": "g2", "label": "A shed unopened", "members": k1[2:], "x": 300, "y": -40}],
                  discarded=[], picks={})
        call("/api/themes-save", {"workbook": str(book), "version": v1})
        call("/api/themes-versions", {"workbook": str(book), "timepoint": 2, "op": "choose", "id": t2["version"]["id"]})
        held2 = json.loads(t2_file.read_text(encoding="utf-8"))
        held1 = json.loads(t1_file.read_text(encoding="utf-8"))
        check("235: each timepoint keeps its own boards and Current board: T1's PETs in T1's file, T2's in T2's",
              [g["label"] for g in held1["boards"][0]["groups"]] == ["Order expected", "A shed unopened"]
              and [g["label"] for g in held2["boards"][0]["groups"]] == ["Learning from neighbours"]
              and held2.get("chosen") == t2["version"]["id"] and "chosen" not in held1, str(held2.get("chosen")))
        again = state(book, timepoint=2)
        check("235: T2's canvas opens again on its own PETs",
              [g["label"] for g in again["groups"]] == ["Learning from neighbours"], str(again["groups"]))

        # ── C. the LPETs canvas: the participant's timepoint PETs as cards, T3 not interviewed
        lp = call("/api/gets", {"workbook": str(book), "lpets": True})
        cases = {c["case"]: c for c in lp["cases"]}
        kinds = sorted((c["case"], c["who"], c["text"]) for c in lp["cards"] if c["kind"] == "pet")
        check("235: the LPETs canvas opens on the participant, each timepoint a case of it, T3 not interviewed",
              lp["lpets"] is True and lp["participant"] == "P1 - Wren" and sorted(cases) == ["T1", "T2", "T3"]
              and cases["T3"]["missing"] and cases["T3"]["said"] == gets_mod.NOT_INTERVIEWED
              and not cases["T1"]["missing"], str({k: (c["status"], c["said"]) for k, c in cases.items()}))
        check("235: its cards are the timepoint PETs, named by the timepoint's label",
              kinds == [("T1", "T1", "A shed unopened"), ("T1", "T1", "Order expected"),
                        ("T2", "T2", "Learning from neighbours")], str(kinds))
        cited = cases["T1"]["lines"][themes.card_key("Before", r1[1], 0)]["time"]
        check("235: a statement's time is cited with its timepoint, T1, 35:55", cited == "T1, 35:55", cited)
        check("235: opening the LPETs writes nothing", not gets_mod.lpets_path(book).exists())
        pet = {c["text"]: c["key"] for c in lp["cards"] if c["kind"] == "pet"}
        lv = dict(lp["version"], cards={c["key"]: {"x": c["x"], "y": c["y"]} for c in lp["cards"]},
                  groups=[{"id": "G1", "label": "From order to neighbours",
                           "members": [pet["Order expected"], pet["Learning from neighbours"]], "x": 0, "y": -60}],
                  discarded=[], picks={}, notes=[])
        call("/api/gets-save", {"workbook": str(book), "lpets": True, "version": lv})
        lfile = gets_mod.lpets_path(book)
        saved = json.loads(lfile.read_text(encoding="utf-8"))
        board = saved["boards"][0]
        check("235: an LPET made of a T1 PET and a T2 PET is saved in the participant's LPETs file",
              lfile.name == "P1 Wren - EN & ES.lpets.json" and sorted(saved["cases"]) == ["T1", "T2", "T3"]
              and board["groups"][0]["label"] == "From order to neighbours"
              and sorted(board["groups"][0]["members"]) == sorted([pet["Order expected"], pet["Learning from neighbours"]]),
              str(sorted(saved)))
        check("235: and the project's GETs file is not written by it",
              not (garden / gets_mod.FILE).exists(), str(sorted(p.name for p in garden.iterdir())))
        back = call("/api/gets", {"workbook": str(book), "lpets": True})
        check("235: the LPETs canvas opens again on its LPET",
              [g["label"] for g in back["groups"]] == ["From order to neighbours"], str(back["groups"]))
        project_gets = call("/api/gets", {"workbook": str(book)})
        # since part 3 the project's board in a project of timepoints is its LGETs, each card an LPET (area 237)
        check("235: the project's board takes the participant's LPETs, never T1's PETs alone",
              sorted(c["text"] for c in project_gets["cards"] if c["kind"] == "pet") == ["From order to neighbours"],
              str([c["text"] for c in project_gets["cards"]]))

        # ── D. the API: the command line and the MCP server name a timepoint or the LPETs
        def run(*args):
            code, out, err = cli.run(["--root", str(garden), "--config", str(cfg_file), *args, "--json"])
            return code, (support.plain(json.loads(out)) if out.strip() else {}), err

        code, shown, err = run("board", "show", "Wren", "--timepoint", "2")
        check("235: board show --timepoint 2 reads T2's board and T2's statements alone",
              code == 0 and [t["label"] for t in shown.get("themes") or []] == ["Learning from neighbours"], err or str(shown)[:300])
        code, shown1, err = run("board", "show", "Wren")
        check("235: board show without it reads T1's",
              code == 0 and sorted(t["label"] for t in shown1.get("themes") or []) == ["A shed unopened", "Order expected"],
              err or str(shown1)[:300])
        ops = scratch / "a235-ops.json"
        ops.write_text(json.dumps({"operations": [{"op": "retitle", "label": "g1", "title": "Neighbours as teachers"}]}),
                       encoding="utf-8")
        before2 = t2_file.read_bytes()
        code, dry, err = run("board", "apply", "Wren", t2["version"]["id"], "--ops", str(ops), "--timepoint", "T2",
                             "--dry-run", "--note", "Rename the PET")
        check("235: a dry run at T2 writes nothing", code == 0 and t2_file.read_bytes() == before2, err)
        code, done, err = run("board", "apply", "Wren", t2["version"]["id"], "--ops", str(ops), "--timepoint", "T2",
                              "--note", "Rename the PET")
        labels2 = [g["label"] for g in json.loads(t2_file.read_text(encoding="utf-8"))["boards"][0]["groups"]]
        labels1 = [g["label"] for g in json.loads(t1_file.read_text(encoding="utf-8"))["boards"][0]["groups"]]
        check("235: board apply --timepoint T2 changes T2's board and leaves T1's",
              code == 0 and labels2 == ["Neighbours as teachers"] and labels1 == ["Order expected", "A shed unopened"],
              err or str(labels2))
        code, _, err = run("board", "show", "Wren", "--timepoint", "4")
        check("235: a timepoint the project has not got is refused", code == 1 and "no timepoint 4" in err.lower() + str(_),
              err)
        code, lshow, err = run("gets", "show", "--lpets", "Wren")
        check("235: gets show --lpets Wren reads Wren's LPETs board",
              code == 0 and "From order to neighbours" in json.dumps(lshow), err or str(lshow)[:300])
        tools = {t["name"]: t for t in mcp_server.TOOLS}
        check("235: the MCP server's board and gets tools take the timepoint and the LPETs",
              "timepoint" in json.dumps(tools.get("board_show", {})) and "lpets" in json.dumps(tools.get("gets_show", {})),
              str(sorted(tools))[:300])
    finally:
        server_mod.CONFIG_PATH, server_mod.ROOT_OVERRIDE, server_mod.STATE_PATH, server_mod.STATE_MEMORY = kept
