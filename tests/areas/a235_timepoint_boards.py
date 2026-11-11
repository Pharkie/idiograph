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
# Hazel, a second newcomer, interviewed before the season alone (lpetadd)
HAZEL_TEXT = ("Kit: [00:00:02] What did you expect of the plot?\nHazel: [00:00:07] I would water it by the moon.\n")
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

    def said_rows(book: Path, sheet: str, who: str = "Wren") -> list[int]:
        import openpyxl
        wb = openpyxl.load_workbook(book, read_only=True)
        try:
            ws = wb[sheet]
            return [r for r, values in enumerate(ws.iter_rows(min_row=2, max_col=1, values_only=True), start=2)
                    if str(values[0] or "").strip() == who]
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

        # ── E. a statement brought onto the LPETs board, into an LPET, as a row of the Participants panel dragged
        # there brings it (lpetadd, 11 November 2026): the op and the page's save leave the same board
        idiograph_routes.api_add_transcripts({"op": "add", "root": root_id, "files": [
            row("hazel.txt", HAZEL_TEXT, "Hazel", "Before", timepoint=1)]})
        hbook = next(garden.glob("*Hazel*/*Hazel*.xlsx"))
        hrow = said_rows(hbook, "Before", "Hazel")[0]
        wb_mod.save_turn(hbook, "Before", hrow, "Watering by the moon", "", "")
        soil, asking = themes.card_key("Midsummer", r2[1], 0), themes.card_key("Midsummer", r2[0], 0)
        skey, akey = f"T2/es/{soil}", f"T2/es/{asking}"
        order_key = f"T1/es/{themes.card_key('Before', r1[0], 0)}"

        def shape(board: dict) -> dict:
            """What holds what on a board, the cards' keys and a statement's words, never where they stand."""
            return {"cards": sorted(board["cards"]), "words": {k: c.get("text") for k, c in board["cards"].items() if "/es/" in k},
                    "groups": sorted((g["id"], g["label"], tuple(g["members"])) for g in board["groups"]),
                    "aside": sorted(board.get("discarded") or [])}

        def lboard() -> dict:
            held = json.loads(lfile.read_text(encoding="utf-8"))
            return next(b for b in held["boards"] if b["id"] == held["current"])

        # the page's drag: the row's card, its words from the timepoint's copy, let go in the LPET, sent with the save
        lp0 = call("/api/gets", {"workbook": str(book), "lpets": True})
        lpid = lp0["version"]["id"]
        g1 = next(g for g in lp0["groups"] if g["label"] == "From order to neighbours")
        line = {c["case"]: c for c in lp0["cases"]}["T2"]["lines"][soil]
        cards0 = {c["key"]: {"x": c["x"], "y": c["y"], "text": c["text"]} for c in lp0["cards"]}
        groups0 = [dict(g, members=list(g["members"])) for g in lp0["groups"]]
        call("/api/gets-save", {"workbook": str(book), "lpets": True, "version": dict(
            lp0["version"], cards=dict(cards0, **{skey: {"x": g1["x"] + 10, "y": g1["y"] + 300, "text": line["text"]}}),
            groups=[dict(g, members=g["members"] + ([skey] if g["id"] == g1["id"] else [])) for g in groups0],
            discarded=[], picks={}, notes=[])})
        dragged = shape(lboard())
        # and the board put back as it was, for the op to do the same
        back = call("/api/gets", {"workbook": str(book), "lpets": True})
        call("/api/gets-save", {"workbook": str(book), "lpets": True, "version": dict(
            back["version"], cards=cards0, groups=groups0, discarded=[], picks={}, notes=[])})
        check("235: the drag's save carded the T2 statement in the LPET, and the board is put back without it",
              skey in dragged["cards"] and skey not in lboard()["cards"], json.dumps(dragged)[:400])

        code, at_t2, err = run("statements", "Wren", "--timepoint", "T2")
        soil_id = next((r["id"] for r in at_t2.get("statements", []) if r["key"] == soil), "")
        bring = scratch / "a235-bring.json"
        bring.write_text(json.dumps({"operations": [{"op": "bring_in", "statement": soil_id, "timepoint": "T2",
                                                     "to": g1["id"]}]}), encoding="utf-8")
        before_bytes = lfile.read_bytes()
        code, dry, err = run("gets", "apply", lpid, "--lpets", "Wren", "--ops", str(bring), "--dry-run",
                             "--note", "Bring in the soil")
        check("235: bring_in's dry run names the statement it would card and where, and writes nothing",
              code == 0 and soil_id and lfile.read_bytes() == before_bytes and [b["key"] for b in dry.get("brought", [])] == [skey]
              and "T2's statement 'The soil is known by others' into 'From order to neighbours'" in dry.get("said", ""),
              err or json.dumps(dry)[:400])
        revisions = len(lboard().get("history") or [])
        code, done, err = run("gets", "apply", lpid, "--lpets", "Wren", "--ops", str(bring), "--note", "Bring in the soil",
                              "--tool", "Claude Code")
        after = lboard()
        check("235: gets apply --lpets brings the T2 statement in by its id into the LPET, alone, its PET's other "
              "statement left off, with History keeping the board first",
              code == 0 and skey in after["cards"] and akey not in after["cards"]
              and skey in next(g["members"] for g in after["groups"] if g["id"] == g1["id"])
              and after["cards"][skey].get("text") == "The soil is known by others"
              and len(after.get("history") or []) == revisions + 1
              and (after.get("history") or [{}])[0].get("name", "").endswith("Bring in the soil"),
              err or json.dumps(done)[:400])
        check("235: the board read back holds what the drag's save left: the same cards, words, LPETs and members",
              shape(after) == dragged, json.dumps({"op": shape(after), "drag": dragged})[:600])

        refuse = scratch / "a235-refuse.json"
        hazel_key = f"{hbook.parent.name}/es/{themes.card_key('Before', hrow, 0)}"
        refuse.write_text(json.dumps({"operations": [
            {"op": "bring_in", "statement": order_key},
            {"op": "bring_in", "statement": skey},
            {"op": "bring_in", "statement": f"T1/es/{themes.card_key('Before', r1[0], 1)}", "to": "G9"},
            {"op": "bring_in", "statement": "S1", "participant": "Hazel", "to": g1["id"]},
            {"op": "bring_in", "statement": hazel_key},
            {"op": "bring_in", "statement": "S9", "timepoint": "T2"},
            {"op": "bring_in", "statement": "S1"}]}), encoding="utf-8")
        before_bytes = lfile.read_bytes()
        code, said_out, err = run("gets", "apply", lpid, "--lpets", "Wren", "--ops", str(refuse), "--note", "Odd ones")
        err = err + json.dumps(said_out)
        check("235: bring_in refuses a statement on the board already, saying where, an unknown LPET, another "
              "participant's, one not at the timepoint and one with no timepoint, the whole change, nothing written",
              code == 1 and lfile.read_bytes() == before_bytes
              and "Operation 2 brings in 'The soil is known by others', which is on the board already, in 'From order to neighbours'" in err
              and "Operation 3 brings 'Trusting the packet' into G9, which is no LPET on this board" in err
              and "Operation 4 names a statement of Hazel's, and these are Wren's LPETs" in err
              and f"Operation 5 names {hazel_key}, which is not one of Wren's statements at any of their timepoints" in err
              and "Operation 6 names S9, which is not one of T2's statements" in err
              and "Operation 7 names S1 with no timepoint" in err and "Operation 1" not in err, err)

        # through MCP, by the card's key, onto the board in no LPET
        srv = mcp_server.Server(str(garden), config=str(cfg_file))
        srv.receive(json.dumps({"jsonrpc": "2.0", "id": 0, "method": "initialize",
                                "params": {"protocolVersion": "2025-06-18", "clientInfo": {"name": "claude-code"}}}))
        got = srv.receive(json.dumps({"jsonrpc": "2.0", "id": 2, "method": "tools/call", "params": {
            "name": "gets_apply", "arguments": {"lpets": "Wren", "board": lpid, "operations": [{"op": "bring_in", "statement": order_key}],
                                                "request": "Expecting order on the board"}}}))["result"]
        loose = lboard()
        check("235: MCP's gets_apply brings a T1 statement onto the LPETs board in no LPET, by its card's key",
              not got.get("isError") and order_key in loose["cards"]
              and not any(order_key in g["members"] for g in loose["groups"])
              and "T1's statement 'Expecting order' onto the board in no LPET" in json.dumps(got),
              json.dumps(got)[:400])

        _fields_kept(scratch, call, run, book, lfile, lboard, lpid,
                     {"asking": akey, "shed": f"T1/es/{themes.card_key('Before', r1[1], 0)}", "order": order_key, "soil": skey},
                     t2["version"]["id"])
    finally:
        server_mod.CONFIG_PATH, server_mod.ROOT_OVERRIDE, server_mod.STATE_PATH, server_mod.STATE_MEMORY = kept


# The page's own acts on the LPETs board as its scripts make them, each from the board as the page loads it (thLoad),
# the body each save sends kept in `out` by its name (domainkeep, 11 November 2026)
PAGE_ACTS = r"""
TH.mode = 'gets'; TH.lpets = true;
const load = () => {
  const cards = {};
  for (const c of DATA.cards) cards[c.key] = Object.assign({}, c);
  return { cards, groups: DATA.groups.map((g) => Object.assign({}, g, { members: g.members.slice() })),
    discarded: DATA.discarded.slice(), picks: {}, stickies: [], rows: JSON.parse(JSON.stringify(DATA.rows || {})), waits: false };
};
const out = {};
// a row of the Participants panel let go in an LPET, as gtPullDrop lets it go there
{ const v = load(); v.cards[ROW.key] = Object.assign({}, ROW); thJoin(v, [ROW.key], 'G2'); out.drag = thBody(v, META); }
// an LPET moved by its title strip
{ const v = load(); const g = thGroup(v, 'G1'); g.x += 40; g.y += 30; out.move = thBody(v, META); }
// retitled
{ const v = load(); thGroup(v, 'G1').label = 'Renamed on the page'; out.rename = thBody(v, META); }
// one LPET let go on the other's title strip, which takes it in
{ const v = load(); thJoin(v, ['G2'], 'G1'); out.merge = thBody(v, META); }
// an LPET deleted, and the step undone
{ const v = load(); const before = thSnap(v, new Set()); thDelete(v, 'G2'); out.deleted = thBody(v, META);
  thPut(v, before); out.undone = thBody(v, META); }
"""


def _fields_kept(scratch, call, run, book, lfile, lboard, lpid, keys, t2_id):
    """An LPET's domain, and every other field a label carries, kept on every path that writes a board
    (domainkeep, 11 November 2026). A data run's bring_in into an LPET took every LPET's domain off four boards,
    since `gets apply` landed its change through `themes.land`, which built each label afresh from the fields the
    change speaks of. Each path is driven on Wren's LPETs board with a domain on both LPETs, a note on one and a
    description on the other: the page's drag from the Participants panel, a move, a rename, a merge and undo, its
    scripts run in node and in a browser, an old page's save that sends no domain, and every `gets apply` op; then a
    GET on the LGETs board and a PET on a timepoint's board through their own applies."""
    import html as html_mod
    import subprocess
    import tempfile

    import themes

    n = [0]

    def ops_file(operations) -> str:
        n[0] += 1
        path = scratch / f"a235-keep-{n[0]}.json"
        path.write_text(json.dumps({"operations": list(operations)}), encoding="utf-8")
        return str(path)

    def apply(note, operations, board=lpid, lpets=True):
        return run("gets", "apply", board, *(["--lpets", "Wren"] if lpets else []), "--ops", ops_file(operations), "--note", note)

    def fields(b=None) -> dict:
        return {g["id"]: {k: v for k, v in g.items() if k not in ("members", "x", "y")} for g in (b or lboard())["groups"]}

    def members(gid: str) -> list:
        return next(g["members"] for g in lboard()["groups"] if g["id"] == gid)

    # a second LPET of the T1 PET left in none, described, and a note on the first, then a domain on each
    parents = themes.parents_of(lboard()["groups"])
    shed_pet = next(k for k in lboard()["cards"] if "/es/" not in k and k not in parents)
    code, done, err = apply("Two LPETs", [{"op": "make", "title": "A shed of her own", "members": [shed_pet], "ref": "S"},
                                          {"op": "describe", "label": "S", "description": "A room for tools"},
                                          {"op": "note", "label": "G1", "note": "Asked over the fence"}])
    def domains_on(**more):
        # each LPET's domain set as Trajectories sets it, so a path that takes them off is seen by itself
        given = dict({"G1": "Practical", "G2": "Family, Town"}, **more)
        call("/api/trajectories-ops", {"workbook": str(book), "ops": [
            {"op": "domain", "participant": "Wren", "lpet": gid, "domain": d} for gid, d in given.items()]})

    domains_on()
    want = {"G1": {"id": "G1", "label": "From order to neighbours", "note": "Asked over the fence", "domain": "Practical"},
            "G2": {"id": "G2", "label": "A shed of her own", "description": "A room for tools", "domain": "Family, Town"}}
    check("235 keep: two LPETs on Wren's board, a domain on each, a note on one and a description on the other",
          code == 0 and fields() == want, err + str(fields()))

    # ── the page's acts, its scripts in node and in a browser, each save read back from the file
    lp = call("/api/gets", {"workbook": str(book), "lpets": True})
    line = {c["case"]: c for c in lp["cases"]}["T2"]["lines"][keys["asking"].split("/es/", 1)[1]]
    b = lboard()
    head = ("const DATA = " + json.dumps({k: lp[k] for k in ("cards", "groups", "discarded", "rows")}) + ";\n"
            + "const META = " + json.dumps({"id": b["id"], "name": b.get("name"), "note": b.get("note") or "",
                                            "created": b.get("created"), "updated": b.get("updated"), "v": themes.board_version(b)}) + ";\n"
            + "const ROW = " + json.dumps({"key": keys["asking"], "case": "T2", "kind": "es", "text": line["text"], "x": 40, "y": 600}) + ";\n")
    themes_js = support.TOOL / "apps" / "idiograph" / "static" / "themes.js"
    node = shutil.which("node")
    in_node = None
    if node:
        ran = support.run_node(support.i18n_js() + themes_js.read_text(encoding="utf-8") + "\n" + head + PAGE_ACTS
                               + "\nconsole.log(JSON.stringify(out));\n", scratch, "a235-keep-page.js")
        in_node = json.loads(ran.stdout) if ran.returncode == 0 and ran.stdout.strip() else None
        if in_node is None:
            print(ran.stderr[:600])
    in_browser = None
    exe = support.browser()
    if exe is not None:
        with tempfile.TemporaryDirectory(prefix="idiograph-235-") as tmp:
            folder = Path(tmp)
            (folder / "words.js").write_text(support.i18n_js(), encoding="utf-8")
            (folder / "acts.js").write_text(head + PAGE_ACTS + "\ndocument.getElementById('out').textContent = JSON.stringify(out);\n",
                                            encoding="utf-8")
            (folder / "page.html").write_text('<!doctype html><html><head><meta charset="utf-8"></head><body><pre id="out"></pre>'
                                              f'<script src="words.js"></script><script src="{themes_js.as_uri()}"></script>'
                                              '<script src="acts.js"></script></body></html>', encoding="utf-8")
            cmd = [str(exe), "--headless", "--disable-gpu", "--no-first-run", "--no-default-browser-check", "--disable-extensions",
                   "--disable-background-networking", "--disable-component-update", "--disable-sync", "--disable-default-apps",
                   "--password-store=basic", "--use-mock-keychain", f"--user-data-dir={folder / 'profile'}",
                   "--allow-file-access-from-files", "--window-size=1280,800", "--virtual-time-budget=3000", "--dump-dom",
                   (folder / "page.html").as_uri()]
            try:
                dumped = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", timeout=120).stdout
            except (OSError, subprocess.TimeoutExpired) as exc:
                dumped = str(exc)
        got = dumped.split('<pre id="out">', 1)[1].split("</pre>", 1)[0] if '<pre id="out">' in dumped else ""
        in_browser = json.loads(html_mod.unescape(got)) if got.startswith("{") else None
    if node:
        check("235 keep: the page's acts on the LPETs board run in node: the panel's drag, a move, a rename, a merge, "
              "a delete and its undo", in_node is not None and sorted(in_node) == ["deleted", "drag", "merge", "move", "rename", "undone"],
              str(in_node)[:300])
    else:
        support.skip("235 keep: the page's acts in node", "no node on this machine")
    if exe is not None:
        check("235 keep: and in a browser the page's scripts send the same saves as in node",
              in_browser is not None and (in_node is None or in_browser == in_node), str(in_browser)[:300])
    else:
        support.skip("235 keep: the page's acts in a browser", "no Chrome, Chromium, Brave or Edge on this computer")
    bodies = in_node or in_browser
    if bodies:
        domains = lambda: {g: f.get("domain") for g, f in fields().items()}  # noqa: E731
        kept, dragged = {}, False
        for name in ("drag", "move", "rename", "merge", "deleted", "undone"):
            # each act's save in turn, as the page sends it from the board it last read
            call("/api/gets-save", {"workbook": str(book), "lpets": True,
                                    "version": dict(bodies[name], v=themes.board_version(lboard()))})
            kept[name] = domains()
            dragged = dragged or (name == "drag" and keys["asking"] in members("G2"))
        both = {"G1": "Practical", "G2": "Family, Town"}
        check("235 keep: the page's saves keep each LPET's domain: the statement dragged in from the panel, an LPET "
              "moved, retitled, let go on another's title, and deleted then undone, its domain back with it",
              dragged and all(kept[x] == both for x in ("drag", "move", "rename", "merge", "undone"))
              and kept["deleted"] == {"G1": "Practical"}, str(kept))
        old = dict(bodies["undone"], v=themes.board_version(lboard()),
                   groups=[dict({k: v for k, v in g.items() if k != "domain"}, label="Renamed on an old page" if g["id"] == "G1" else g["label"])
                           for g in bodies["undone"]["groups"]])
        call("/api/gets-save", {"workbook": str(book), "lpets": True, "version": old})
        check("235 keep: a save from a page that sends no domain keeps the file's, its rename taken",
              fields() == dict(want, G1=dict(want["G1"], label="Renamed on an old page")), str(fields()))

    # ── every gets apply op on the LPETs board: each label keeps every field the op did not change
    steps = [
        ("bring_in into an LPET", [{"op": "bring_in", "statement": keys["asking"], "to": "G2"}], {}),
        ("bring_in onto the board", [{"op": "bring_in", "statement": keys["shed"]}], {}),
        ("retitle", [{"op": "retitle", "label": "G1", "title": "Neighbours as teachers"}], {"G1": {"label": "Neighbours as teachers"}}),
        ("note and describe", [{"op": "note", "label": "G2", "note": "Forks under the sacks"},
                               {"op": "describe", "label": "G1", "description": "From packets to people"}],
         {"G2": {"note": "Forks under the sacks"}, "G1": {"description": "From packets to people"}}),
        ("move", [{"op": "move", "items": [keys["soil"]], "to": "G2"}], {}),
        ("make", [{"op": "make", "title": "Tools", "inside": "G2", "members": [keys["asking"]]}], {"G3": {"id": "G3", "label": "Tools"}}),
        ("merge", [{"op": "merge", "label": "G3", "into": "G2"}], {"G3": None}),
        ("make and apart", [{"op": "make", "title": "Loose ones", "members": [keys["order"], keys["shed"]], "ref": "L"},
                            {"op": "apart", "label": "L"}], {}),
        ("order", None, {}),
        ("arrange by participant", [{"op": "arrange", "by": "participant"}], {}),
        ("align", [{"op": "align", "items": ["G1", "G2"], "to": "top"}], {}),
    ]
    domains_on()
    lost = []
    for what, operations, changes in steps:
        if operations is None:
            operations = [{"op": "order", "under": "G2", "items": list(reversed(members("G2")))}]
        before = fields()
        code, done, err = apply(what, operations)
        expected = dict(before)
        for gid, change in changes.items():
            if change is None:
                expected.pop(gid, None)
            else:
                expected[gid] = dict(expected.get(gid) or {}, **change)
        if code != 0 or fields() != expected:
            lost.append(f"{what}: {code} {err[:200]} {fields()}")
    check("235 keep: gets apply --lpets keeps each LPET's domain, note and description through bring_in into an LPET and "
          "onto the board, retitle, note, describe, move, make, merge, apart, order, arrange and align, each op's own "
          "change taken", not lost and fields()["G1"].get("domain") == "Practical" and fields()["G2"].get("domain") == "Family, Town",
          "\n".join(lost) + str(fields()))

    # a GET a change makes may take the id of one it took away, and takes none of that one's domain
    code, _, err = apply("A spare", [{"op": "make", "title": "Spare", "members": []}])
    spare = next((g for g, f in fields().items() if f["label"] == "Spare"), "")
    domains_on(**{spare: "Weather"})
    had = fields()
    code, _, err = apply("Merge the spare, make a fresh one", [{"op": "merge", "label": spare, "into": "G1"},
                                                                {"op": "make", "title": "Fresh start", "members": []}])
    now = fields()
    check("235 keep: an LPET a change makes in the id of one it merged away carries none of that one's domain, the "
          "others keeping theirs", code == 0 and had.get(spare, {}).get("domain") == "Weather" and now["G1"].get("domain") == "Practical"
          and now.get(spare) == {"id": spare, "label": "Fresh start"} and now["G1"] == had["G1"] and now["G2"] == had["G2"],
          err + str(now))

    # ── a GET on the project's LGETs board and a PET on a timepoint's board, through their own applies
    lg = call("/api/gets", {"workbook": str(book)})
    lpet_card = next(c["key"] for c in lg["cards"] if c["kind"] == "pet")
    call("/api/gets-save", {"workbook": str(book), "version": dict(
        lg["version"], cards={c["key"]: {"x": c["x"], "y": c["y"]} for c in lg["cards"]}, discarded=[], picks={}, notes=[],
        groups=[{"id": "G1", "label": "Neighbours", "members": [lpet_card], "x": 0, "y": -60, "domain": "Town",
                 "description": "A GET described"}])})
    code, _, err = apply("Retitle a GET", [{"op": "retitle", "label": "G1", "title": "Neighbours first"},
                                           {"op": "make", "title": "Second", "members": []}], board=lg["version"]["id"], lpets=False)
    project = {g["id"]: g for g in call("/api/gets", {"workbook": str(book)})["groups"]}
    check("235 keep: on the LGETs board a GET keeps its domain and description through gets apply's retitle and make",
          code == 0 and project.get("G1", {}).get("domain") == "Town" and project["G1"].get("description") == "A GET described"
          and project["G1"]["label"] == "Neighbours first", err + str(project))
    st = call("/api/themes", {"workbook": str(book), "timepoint": 2})
    call("/api/themes-save", {"workbook": str(book), "timepoint": 2, "version": dict(
        st["version"], cards={c["key"]: {"x": c["x"], "y": c["y"], "text": c["text"]} for c in st["cards"]}, discarded=[], picks={},
        groups=[dict(g, domain="Town") for g in st["groups"]])})
    gid = st["groups"][0]["id"]
    code, _, err = run("board", "apply", "Wren", t2_id, "--timepoint", "T2", "--ops",
                       ops_file([{"op": "retitle", "label": gid, "title": "Neighbours, kept"}, {"op": "make", "title": "Another", "members": []}]),
                       "--note", "Retitle a PET")
    pets = {g["id"]: g for g in call("/api/themes", {"workbook": str(book), "timepoint": 2})["groups"]}
    check("235 keep: on a timepoint's PETs board a label keeps a field the applier never speaks of through board apply's "
          "retitle and make", code == 0 and pets.get(gid, {}).get("domain") == "Town" and pets[gid]["label"] == "Neighbours, kept",
          err + str(pets))
