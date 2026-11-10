from __future__ import annotations

import inspect
import json
import os
import re
import shutil

import rounds as rounds_mod
import workbook as wb_mod
from workbook import WorkbookError

from . import support
from .support import DEMO_QUESTION, check, skip
import idiograph_routes
import idiograph_cli


def test_agent_cli(scratch):
    print("\n79. Agent access: the command line, one writer at a time, the page noticing, the privacy tick and "
          "the guide")
    import subprocess
    import threading
    import time
    import cli
    import gets as gets_mod
    import locks
    import server as server_mod
    import themes as themes_mod
    import themes_ai

    js = support.text("apps/idiograph/static/themes.js")
    app = support.text("family/static/shell.js", "apps/idiograph/static/distil.js")
    page = support.page_text()
    fn = lambda src, name: src.split(f"function {name}(", 1)[1].split("\n}", 1)[0] if f"function {name}(" in src else ""
    pristine = support.DEMO_PRISTINE
    folder = re.compile(r"P\d - [A-Z][a-z]+-[A-Z][a-z]+")

    def make_root(at: Path, names=("Juno", "Rowan", "Mabel"), folders=None) -> Path:
        """Invented cases from the demo's pristine copy, each with its sidecars, and a project file."""
        shutil.rmtree(at, ignore_errors=True)
        for name in names:
            case = at / (folders or {}).get(name, name)
            (case / "Working").mkdir(parents=True)
            shutil.copy2(pristine / f"{name} - EN & ES.xlsx", case / f"{name} - EN & ES.xlsx")
            for side in (pristine / "Working").glob(f"{name} - *"):
                shutil.copy2(side, case / "Working" / side.name)
        (at / "idiograph-project.json").write_text(json.dumps({"name": "Dogs, a scratch project",
                                                               "research_question": DEMO_QUESTION}), encoding="utf-8")
        return at

    def files(at: Path) -> dict:
        return {p.relative_to(at).as_posix(): p.read_bytes() for p in sorted(at.rglob("*")) if p.is_file() and p.name != locks.NAME}

    root = make_root(scratch / "agent-cli-root")
    config_file = scratch / "agent-cli-config.json"
    config_file.write_text(json.dumps({"root": str(root), "interviewer": "Adam"}), encoding="utf-8")
    juno, rowan = root / "Juno" / "Juno - EN & ES.xlsx", root / "Rowan" / "Rowan - EN & ES.xlsx"

    def run(*args, at: Path | None = None) -> tuple[int, str, str]:
        return cli.run(["--root", str(at or root), "--config", str(config_file), *args])

    def answer(*args, at: Path | None = None):
        code, out, err = run(*args, "--json", at=at)
        return code, support.plain(json.loads(out)) if out.strip() else {}

    def spec(name: str, value) -> str:
        path = scratch / f"agent-cli-{name}.json"
        path.write_text(json.dumps(value), encoding="utf-8")
        return str(path)

    kept = (server_mod.CONFIG_PATH, server_mod.ROOT_OVERRIDE, server_mod.STATE_MEMORY, server_mod.DEMO_DIR,
            server_mod.SHIPPED_DEMO, server_mod.DEMO_CASE, server_mod.DEMO_WORKBOOK, server_mod.DEMO_PROJECT, locks.WAIT)
    live_config = server_mod.CONFIG_PATH.read_bytes() if server_mod.CONFIG_PATH.exists() else None
    try:
        server_mod.CONFIG_PATH = config_file
        server_mod.ROOT_OVERRIDE = str(root)
        server_mod.STATE_MEMORY = {"recent": []}

        # \u2500\u2500 A. the privacy tick: refused without it, the tick in the project file, the demo always open
        before = files(root)
        code, out, err = run("cases")
        check("79: a project without the tick is refused in one line saying where to tick it, and nothing is written",
              code == 1 and err.strip() == idiograph_cli.PRIVATE and not out and files(root) == before
              and "Project settings" in idiograph_cli.PRIVATE and "Allow AI agents to read this project" in idiograph_cli.PRIVATE)
        code, data = answer("cases")
        check("79: with --json the refusal is JSON too", code == 1 and data.get("error") == idiograph_cli.PRIVATE)
        ticked = idiograph_routes.api_project({"path": str(juno), "agents": True})["project"]
        held = json.loads((root / server_mod.PROJECT_FILE).read_text(encoding="utf-8"))
        check("79: Settings' tick lands in the project file as agents, allowed with the time, the name and question kept",
              held["agents"]["allowed"] is True and held["agents"]["at"] and held["name"] == "Dogs, a scratch project"
              and ticked["agents"]["allowed"] is True and ticked["agents"]["at"] == held["agents"]["at"]
              and idiograph_routes.read_project(root)["agents"]["allowed"] is True)
        idiograph_routes.api_project({"path": str(juno), "agents": False})
        refused_again = run("cases")[0] == 1
        idiograph_routes.api_project({"path": str(juno), "agents": True})
        check("79: untick it and the command line refuses again, tick it and it answers",
              refused_again and run("cases")[0] == 0)
        check("79: off by default, read as off from a file without the key, and on for the demo",
              idiograph_routes.agents_of({}) == {"allowed": False, "at": None}
              and idiograph_routes.agents_of({"agents": {"allowed": "yes"}})["allowed"] is False
              and idiograph_routes.agents_of({}, demo=True)["allowed"] is True
              and idiograph_routes.read_project(server_mod.DEMO_DIR)["agents"]["allowed"] is True)

        # the demo, through --demo, on a scratch copy that make_demo.fill fills as a server start does
        demo = scratch / "agent-cli-demo"
        shipped = scratch / "agent-cli-shipped"
        shutil.rmtree(demo, ignore_errors=True)
        shutil.rmtree(shipped, ignore_errors=True)
        shutil.copytree(pristine, shipped / "pristine")
        for name in ("Juno", "Rowan", "Mabel"):
            (demo / name).mkdir(parents=True)
            shutil.copy2(pristine / f"{name} - EN & ES.xlsx", demo / name / f"{name} - EN & ES.xlsx")
        shutil.copyfile(support.source("demo") / server_mod.PROJECT_FILE, demo / server_mod.PROJECT_FILE)
        server_mod.DEMO_DIR, server_mod.SHIPPED_DEMO = demo, shipped
        server_mod.DEMO_CASE = demo / "Juno"
        server_mod.DEMO_WORKBOOK = server_mod.DEMO_CASE / "Juno - EN & ES.xlsx"
        server_mod.DEMO_PROJECT = demo / server_mod.PROJECT_FILE
        code, demo_out, err = cli.run(["--demo", "--config", str(config_file), "cases"])
        code_json, demo_json = cli.run(["--demo", "--config", str(config_file), "cases", "--json"])[:2]
        demo_json = support.plain(json.loads(demo_json))
        check("79: the demo answers with no tick, its three cases by name, its sidecars filled as a server start fills them",
              code == 0 and code_json == 0 and "Living with a dog (the demo)" in demo_out
              and [c["case"] for c in demo_json["cases"]] == ["Juno", "Mabel", "Rowan"] and demo_json["project"]["demo"]
              and themes_mod.themes_path(demo / "Rowan" / "Rowan - EN & ES.xlsx").exists(), err or demo_out[:120])
        code, valid, err = cli.run(["--demo", "--config", str(config_file), "validate", "--json"])
        valid = support.plain(json.loads(valid))
        check("79: the schemas in docs/schemas read the demo's every file as valid",
              code == 0 and valid["valid"] and valid["problems"] == [] and len(valid["files"]) == 6
              and sorted(p.name for p in support.source("docs/schemas").glob("*.schema.json"))
              == ["gets.schema.json", "progress.schema.json", "project.schema.json", "themes.schema.json"], str(valid)[:300])
        made = {"rounds": {}}
        rounds_mod.record_work(made, 2, 1000.0)
        made_problems: list = []
        cli.conform(made, cli.schema_of("progress"), "progress", cli.schema_of("progress").get("$defs") or {}, made_problems)
        check("79: a progress file as rounds.py writes it, its last round kept as text like the rounds' own keys, reads as valid",
              made_problems == [] and made["last_commit_round"] == "2", str(made_problems))

        # \u2500\u2500 B. cases, statements and the boards, in text and in JSON
        code, text, _ = run("cases")
        _, data = answer("cases")
        rowan_row = next(c for c in data["cases"] if c["case"] == "Rowan")
        check("79: cases names the project, its question and the minimum, never a cap, then each case with its workbook, phases and boards",
              code == 0 and "Dogs, a scratch project" in text and DEMO_QUESTION in text and "PETs" not in text.split("\n\n", 1)[0]
              and "Rowan: Rowan - EN & ES.xlsx" in text and "Boards: Board 1 (v1, the Current board, on the canvas)" in text
              and data["project"]["ai_board_most_pets"] == 5 and data["project"]["gets_minimum"] == 3 and data["project"]["smith_band"]
              and rowan_row["workbook"] == "Rowan - EN & ES.xlsx" and rowan_row["statements_complete"]
              and rowan_row["pets_complete"]["board"] == "v1" and rowan_row["current"] == "Board 1"
              and rowan_row["boards"] == [{"id": "v1", "name": "Board 1", "current": True, "canvas": True}])
        read = themes_mod.read_cards(rowan)
        code, text, _ = run("statements", "Rowan")
        _, data = answer("statements", "Rowan")
        rows = data["statements"]
        binned = next(r for r in rows if any(b["where"] == idiograph_cli.BIN for b in r["boards"]))
        check("79: statements gives every statement its short id in sheet and transcript order, with its key, its turn, quotes and notes",
              code == 0 and [r["id"] for r in rows] == [f"S{i}" for i in range(1, len(read["cards"]) + 1)]
              and [r["key"] for r in rows] == [c["key"] for c in read["cards"]]
              and rows[0]["turn"].startswith("Yeah. Erm.") and rows[0]["quotes"][0]["key"] == "Initial:3:0"
              and rows[0]["notes"] and "S1 Initial:3:0  Slipping between is and was" in text
              and "  Turn: Yeah. Erm." in text and "  Quote Initial:3:0:" in text)
        check("79: and where each board places it, the labels over it, Not placed or the bin",
              rows[1]["boards"][0]["where"] == "Company in a lonely year, and a world closing in"
              and rows[0]["boards"][0]["where"] == idiograph_cli.NOT_PLACED and binned["key"] == "Initial:7:1"
              and "      Board 1: Set aside" in text)
        code, text, _ = run("board", "list", "Rowan")
        check("79: board list names each board with its marks and counts",
              code == 0 and "v1  Board 1 (the Current board, on the canvas): 5 PETs, 43 placed, 2 not placed, 1 set aside" in text)
        by_id, by_name = run("board", "show", "Rowan", "v1"), run("board", "show", "Rowan", "board 1")
        _, shown = answer("board", "show", "Rowan")
        check("79: board show is the board as a tree, by its id or its name alike, the Current board with none named",
              by_id == by_name and by_id[0] == 0 and "g1 Living on her timetable, in the dark at both ends (1 sub-theme \u00b7 7 statements)" in by_id[1]
              and "   g6 Still listening for other dogs (4 statements)" in by_id[1]
              and "   Picked Initial:9:0: \"this is all right, this is ours\"" in by_id[1]
              and "\nNot placed (2)\n" in by_id[1] and "\nSet aside (1)\n" in by_id[1]
              and shown["id"] == "v1" and shown["themes"][0]["statements"][0]["id"] == "S7"
              and shown["discarded"][0]["key"] == "Initial:7:1")

        # \u2500\u2500 C. a new board from a plain structure, the dry run first, then for real
        keys = {c["key"]: f"S{i}" for i, c in enumerate(read["cards"], start=1)}
        plan = {"pets": [
            {"title": "Mornings and nights arranged round her fear", "note": "The timetable as he lived it.",
             "members": ["S7", "S9", "Initial:9:1", "S11"], "picks": ["Initial:9:0"],
             "subs": [{"title": "The watch that has not stopped", "members": ["S12", "S13"]}]},
            {"title": "A lonely year she filled", "members": ["S2", "S3", "S4", "S5", "S6"]},
            {"title": "A flat that could not hold her", "members": ["S20", "S21", "S22"]}],
            "not_placed": {"S1": "Tense more than an experience, for him to weigh", "S8": ""}}
        source = spec("plan", plan)
        before = files(root)
        code, text, _ = run("board", "new", "Rowan", "--from", source, "--dry-run")
        check("79: board new with --dry-run says what it would make and writes nothing, his request not yet needed",
              code == 0 and text.startswith("Dry run, nothing was written. It would make Board 2 on Rowan, from Board 1: 3 PETs, 14 statements placed")
              and files(root) == before)
        code, _, err = run("board", "new", "Rowan", "--from", source)
        check("79: a write with no request in his words is refused, and nothing is written",
              code == 1 and err.strip() == idiograph_cli.NO_REQUEST and files(root) == before)
        board1 = json.loads(themes_mod.themes_path(rowan).read_text(encoding="utf-8"))["boards"][0]
        code, text, _ = run("board", "new", "Rowan", "--from", source, "--note", "Make a board of three PETs",
                            "--tool", "Claude Code")
        stored = json.loads(themes_mod.themes_path(rowan).read_text(encoding="utf-8"))
        made = stored["boards"][-1]
        parents = themes_mod.parents_of(made["groups"])
        check("79: it lands as the next board, Board 2, through propose (184), made current, every other board as it was",
              code == 0 and made["name"] == "Board 2" and stored["current"] == made["id"] and stored["chosen"] == "v1"
              and stored["boards"][0] == board1
              and text.startswith("Made Board 2 on Rowan, from Board 1: 3 PETs, 14 statements placed, 32 left in Not placed, 1 of them with a reason."))
        check("79: made says an agent made it, with the tool, his request and the time, and the note says it in words",
              made["made"]["by"] == "agent" and made["made"]["tool"] == "Claude Code"
              and made["made"]["request"] == "Make a board of three PETs" and made["made"]["at"]
              and made["note"].startswith("Made by Claude Code in a conversation on ")
              and "for the request 'Make a board of three PETs'. 3 PETs, 14 placed, 32 not placed." in made["note"])
        g = {x["label"]: x for x in made["groups"]}
        check("79: titles, notes, members by short id or key, sub-themes and picks land where the structure put them",
              g["Mornings and nights arranged round her fear"]["note"] == "The timetable as he lived it."
              and g["The watch that has not stopped"]["id"] in g["Mornings and nights arranged round her fear"]["members"]
              and "Initial:9:1" in g["Mornings and nights arranged round her fear"]["members"]
              and made["picks"] == {g["Mornings and nights arranged round her fear"]["id"]: ["Initial:9:0"]}
              and made["quoted"] == {"Initial:9:0": "\"this is all right, this is ours\""})
        check("79: nothing goes in the bin, and a statement left out sits in Not placed with its reason under ai",
              made["discarded"] == [] and "Initial:3:0" not in parents and "Initial:7:1" not in parents
              and made["ai"] == {"discarded": {"Initial:3:0": "Tense more than an experience, for him to weigh"}})
        layout = themes_mod.layout_boxes(themes_mod.normalise(made))
        tops = [x["id"] for x in made["groups"] if x["id"] not in parents]
        boxes = [layout["frames"][t] for t in tops] + [layout["cards"][k] for k in layout["cards"] if k not in parents]
        check("79: it is laid out by lay_out, nothing over anything else",
              not [1 for i, a in enumerate(boxes) for b in boxes[i + 1:] if themes_mod.clash(a, b)])

        # \u2500\u2500 D. validation: every problem one line, and nothing written
        before = files(root)
        bad = {"pets": [{"title": "A", "members": ["S999", "S7"], "picks": ["Initial:13:0"]},
                        {"title": "", "members": ["S7", "S30"]},
                        {"title": "C", "members": ["S40"], "subs": [{"title": "D", "members": ["S41"], "subs": []}]}],
               "discarded": ["S5"]}
        code, _, err = run("board", "new", "Rowan", "--from", spec("bad", bad), "--note", "x")
        lines = err.strip().splitlines()
        check("79: an unknown id, a statement twice, a missing title, a sub in a sub and the bin each refused in a line, a pick outside its label dropped (area 196)",
              code == 1 and idiograph_cli.NEVER_BIN in lines and "S999 in 'A' is not a statement of this participant." in lines
              and "S7 Initial:7:0 is placed twice, in 'A' and in PET 2." in lines and "PET 2 has no title." in lines
              and not any("Initial:13:0" in line for line in lines)
              and "'D' is a sub-theme, and a sub-theme holds statements and groups, not sub-themes." in lines
              and files(root) == before, err)

        # \u2500\u2500 E. a change through the operations AI revise uses, a revision kept first
        ai_board = made["id"]
        lonely = g["A lonely year she filled"]["id"]
        mornings = g["Mornings and nights arranged round her fear"]["id"]
        ops = {"request": "Give the tense and the joke a PET, and move the sock into the timetable",
               "operations": [{"op": "retitle", "label": lonely, "title": "A lonely year she filled, and a world that shrank"},
                              {"op": "make", "ref": "new1", "title": "Is and was, and the joke that was not one",
                               "inside": None, "members": ["S1", "Initial:7:1"]},
                              {"op": "move", "items": ["S46"], "to": mornings},
                              {"op": "move", "items": ["S30"], "to": None, "reason": "It answers no part of the question"}]}
        change = spec("ops", ops)
        before = files(root)
        code, text, _ = run("board", "apply", "Rowan", ai_board, "--ops", change, "--dry-run")
        check("79: board apply with --dry-run says what it would do in plain words and writes nothing",
              code == 0 and text.startswith("Dry run, nothing was written. On Board 2 it would have: retitled 'A lonely year she filled'")
              and files(root) == before)
        code, text, _ = run("board", "apply", "Rowan", "Board 2", "--ops", change, "--tool", "Claude Code")
        stored = json.loads(themes_mod.themes_path(rowan).read_text(encoding="utf-8"))
        after = stored["boards"][-1]
        rev = after["history"][-1]
        ga = {x["label"]: x for x in after["groups"]}
        check("79: the board as it stood is kept first as a revision named Before: and his request, marked as the agent's",
              code == 0 and rev["name"] == themes_ai.revision_name(ops["request"]) and rev["auto"] is False
              and rev["state"]["groups"] == made["groups"] and rev["made"]["by"] == "agent"
              and after["changed"]["request"] == ops["request"] and after["changed"]["tool"] == "Claude Code"
              and 'is kept first in its History, as "Before: Give the tense' in text)
        check("79: the change lands: retitled, a new PET of short ids and keys, a statement moved, one sent out with its reason",
              "A lonely year she filled, and a world that shrank" in ga
              and sorted(ga["Is and was, and the joke that was not one"]["members"]) == ["Initial:3:0", "Initial:7:1"]
              and "Initial:39:1" in ga["Mornings and nights arranged round her fear"]["members"]
              and after["ai"]["discarded"].get("Initial:33:2" if keys.get("Initial:33:2") == "S30" else read["cards"][29]["key"])
              == "It answers no part of the question"
              and "Initial:3:0" not in after["ai"]["discarded"] and after["discarded"] == [])
        normal = themes_mod.normalise(after)
        layout = themes_mod.layout_boxes(normal)
        parents = themes_mod.parents_of(normal["groups"])
        tops = [x["id"] for x in normal["groups"] if x["id"] not in parents]
        boxes = [layout["frames"][t] for t in tops] + [layout["cards"][k] for k in layout["cards"] if k not in parents]
        clashes = [1 for i, a in enumerate(boxes) for b in boxes[i + 1:] if themes_mod.clash(a, b)]
        untouched = g["A flat that could not hold her"]
        check("79: what the change did not touch keeps its place, and nothing overlaps after it lands",
              not clashes and ga["A flat that could not hold her"]["x"] == untouched["x"]
              and ga["A flat that could not hold her"]["y"] == untouched["y"], f"{len(clashes)} clashes")
        before = files(root)
        refusals = spec("refusals", {"request": "x", "operations": [
            {"op": "retitle", "label": lonely, "title": "Fine"},
            {"op": "move", "items": ["S2"], "to": "g99"},
            {"op": "delete", "items": ["S3"]},
            {"op": "make", "title": "", "inside": None, "members": ["S4"]}]})
        code, _, err = run("board", "apply", "Rowan", ai_board, "--ops", refusals)
        lines = err.strip().splitlines()
        check("79: one operation that cannot stand refuses the whole change, a line for each, and nothing is written",
              code == 1 and "Operation 4 makes a label with no title." in lines
              and f"Operation 3: {idiograph_cli.NO_DELETE}" in lines and lines[-1] == "Nothing was written." and files(root) == before, err)
        code, _, err = run("board", "apply", "Rowan", ai_board, "--ops", spec("label", {"request": "x", "operations": [
            {"op": "move", "items": ["S2"], "to": "g99"}]}))
        code_bin, _, err_bin = run("board", "apply", "Rowan", "v1", "--ops", spec("bin", {"request": "x", "operations": [
            {"op": "move", "items": ["Initial:7:1"], "to": "g1"}]}))
        check("79: no operation reaches the bin: a statement in it is not on the board for any operation",
              code == 1 and "Operation 1 named a label not on the board." in err
              and code_bin == 1 and "Operation 1 named a statement not on the board." in err_bin and files(root) == before)

        # \u2500\u2500 F. compare, on two invented boards of Juno's with figures worked by hand
        k = [c["key"] for c in themes_mod.read_cards(juno)["cards"]]
        one = {"pets": [{"title": "Ex", "members": k[0:3]}, {"title": "Why", "members": k[3:5]}]}
        two = {"pets": [{"title": "Pe", "members": k[0:2]}, {"title": "Queue", "members": k[2:5]}]}
        run("board", "new", "Juno", "--from", spec("one", one), "--note", "first")
        run("board", "new", "Juno", "--from", spec("two", two), "--note", "second")
        code, text, _ = run("board", "compare", "Juno", "Board 1", "Board 2")
        _, data = answer("board", "compare", "Juno", "Board 1", "Board 2")
        went = {(w["from_name"], w["to_name"]): {p["title"]: [(x["title"], x["count"]) for x in p["went"]] for p in w["pets"]}
                for w in data["where"]}
        check("79: compare gives each pair of boards the share of statement pairs placed alike, 149 of 153 here",
              code == 0 and len(k) == 18 and data["pairs"][0]["pairs"] == 153 and data["pairs"][0]["alike"] == 149
              and "Board 1 and Board 2: 149 of 153 statement pairs placed alike, 97%" in text)
        check("79: and for each board where every other board's PETs went on it",
              went[("Board 1", "Board 2")] == {"Ex": [("Pe", 2), ("Queue", 1)], "Why": [("Queue", 2)]}
              and went[("Board 2", "Board 1")] == {"Pe": [("Ex", 2)], "Queue": [("Why", 2), ("Ex", 1)]}
              and "Where Board 1's PETs went on Board 2" in text and "    2 to Pe" in text)

        # \u2500\u2500 G. a turn written as /api/commit writes one, behind Excel's lock and the backup
        turn = {"statements": ["A walk she knows better than anyone"], "notes": ["Routine owned by the dog."],
                "quotes": ["there are mornings where I genuinely think she is walking me"], "request": "Code turn 15"}
        source = spec("turn", turn)
        book_before = juno.read_bytes()
        side_before = rounds_mod.progress_path(juno).read_bytes()
        code, text, _ = run("turn", "write", "Juno", "Initial", "15", "--from", source, "--dry-run")
        check("79: turn write with --dry-run says what it would write and writes nothing",
              code == 0 and text.startswith("Dry run, nothing was written. It would write the statements")
              and juno.read_bytes() == book_before and not (root / "Juno" / "_Archive").exists())
        lock = wb_mod.lock_file(juno)
        lock.write_text("", encoding="utf-8")
        try:
            code, _, err = run("turn", "write", "Juno", "Initial", "15", "--from", source)
        finally:
            lock.unlink()
        check("79: a turn write is refused while Excel has the workbook open, before any backup, and nothing is written",
              code == 1 and "is open in Excel" in err and juno.read_bytes() == book_before
              and not (root / "Juno" / "_Archive").exists() and rounds_mod.progress_path(juno).read_bytes() == side_before)
        code, _, err = run("turn", "write", "Juno", "Initial", "14", "--from", spec("loose", dict(turn, quotes=["walking the dog"])))
        check("79: an interviewer's turn and a quote not in the turn's words are refused, a line each",
              code == 1 and "That turn is the interviewer's" in err and "is not in the turn's words as they stand." in err
              and juno.read_bytes() == book_before)
        code, text, _ = run("turn", "write", "Juno", "Initial", "15", "--from", source, "--tool", "Claude Code")
        case = wb_mod.read_case(juno)
        row = next(r for s in case["sheets"] for r in s["rows"] if r["row"] == 15)
        progress = json.loads(rounds_mod.progress_path(juno).read_text(encoding="utf-8"))
        edit = progress["edits"][-1]
        backups = sorted((root / "Juno" / "_Archive").glob("Juno - EN & ES (pre-agent *).xlsx"))
        check("79: it writes the three fields, the quote in inverted commas as q writes one, after the trim-style backup",
              code == 0 and row["es"] == turn["statements"][0] and row["en"] == turn["notes"][0]
              and row["kq"] == '"there are mornings where I genuinely think she is walking me"'
              and len(backups) == 1 and backups[0].read_bytes() == book_before and backups[0].name in text)
        check("79: the progress file's edits record the write as the agent's, the row decided and his place left alone",
              edit["by"] == "agent" and edit["tool"] == "Claude Code" and edit["request"] == "Code turn 15"
              and edit["sheet"] == "Initial" and edit["row"] == 15 and edit["before"]["es"] == []
              and edit["after"]["es"] == turn["statements"] and progress["rows"]["Initial:15"] == rounds_mod.HAS_CONTENT
              and progress["last"] == support.plain(json.loads(side_before))["last"])
        code, text, _ = run("turn", "show", "Juno", "Initial", "14-15")
        check("79: turn show gives a run of turns, the interviewer's marked, with what each holds",
              code == 0 and "Initial, row 14, 03:51, Adam (the interviewer)" in text
              and "  Statement: A walk she knows better than anyone" in text)

        # \u2500\u2500 H. one writer at a time, across the server and the command line
        check("79: the lock is flock on Working/.idiograph.lock in the case and .idiograph.lock at the root",
              wb_mod.case_lock(rowan) == root / "Rowan" / "Working" / ".idiograph.lock"
              and locks.root_lock(root) == root / ".idiograph.lock" and locks.WAIT == 10.0
              and "fcntl.flock(fh.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)" in inspect.getsource(locks)
              and "msvcrt.locking" in inspect.getsource(locks))
        locks.WAIT = 0.1
        before = files(root)
        with wb_mod.case_held(rowan):
            code, _, err = run("board", "new", "Rowan", "--from", spec("plan", plan), "--note", "x")
        check("79: a write that cannot have the lock says so and writes nothing", code == 1 and err.strip() == locks.BUSY
              and files(root) == before)
        locks.WAIT = 10.0
        order = []

        def hold(seconds: float):
            with wb_mod.case_held(rowan):
                order.append(("held", time.monotonic()))
                time.sleep(seconds)
                order.append(("let go", time.monotonic()))

        opened = idiograph_routes.api_themes({"workbook": str(rowan), "board": "v1"})
        body = dict(opened["version"], cards={c["key"]: {"x": c["x"], "y": c["y"], "text": c["text"]} for c in opened["cards"]},
                    groups=opened["groups"], discarded=opened["discarded"], picks=opened["picks"])
        holder = threading.Thread(target=hold, args=(0.2,))
        holder.start()
        while not order:
            time.sleep(0.01)
        idiograph_routes.api_themes_save({"workbook": str(rowan), "version": body})
        saved_at = time.monotonic()
        holder.join()
        holder = threading.Thread(target=hold, args=(0.2,))
        holder.start()
        while len(order) < 3:
            time.sleep(0.01)
        code, _, _ = run("board", "apply", "Rowan", "v1", "--ops", spec("small", {"request": "Retitle", "operations": [
            {"op": "retitle", "label": "g5", "title": "Keeping her good name and her bowl"}]}))
        applied_at = time.monotonic()
        holder.join()
        check("79: the server's write waits for the lock a command holds, and a command waits for one the server holds",
              saved_at >= order[1][1] and applied_at >= order[3][1] and code == 0
              and "with writing(path, boards=True):" in inspect.getsource(idiograph_routes.api_themes_save)
              and "with writing(root=root):" in inspect.getsource(idiograph_routes.api_gets_ops)
              and "wb_mod.case_held(" in inspect.getsource(idiograph_routes.writing) and "locks.root(" in inspect.getsource(idiograph_routes.writing))

        # \u2500\u2500 I. a page that last saw a board before an agent changed it never saves over the change
        stale = dict(body, id=ai_board, updated=made["updated"], groups=made["groups"],
                     cards={k2: dict(v) for k2, v in made["cards"].items()})
        refused = None
        try:
            idiograph_routes.api_themes_save({"workbook": str(rowan), "version": stale})
        except WorkbookError as exc:
            refused = str(exc)
        held = themes_mod.find_version(json.loads(themes_mod.themes_path(rowan).read_text(encoding="utf-8")), ai_board)
        check("79: the stale save is refused with its line, the canvas kept in History, the agent's change standing",
              refused == themes_mod.OUTSIDE and held["history"][-1]["name"] == themes_mod.CANVAS_KEPT
              and held["groups"] == after["groups"] and refused.startswith("This board changed in a conversation"))
        fresh = dict(stale, updated=held["updated"], v=themes_mod.board_version(held), groups=held["groups"])
        saved = idiograph_routes.api_themes_save({"workbook": str(rowan), "version": fresh})
        kept_made = {k: v for k, v in themes_mod.find_version(themes_mod.load(rowan), ai_board)["made"].items() if k != "edited"}
        check("79: a page that has shown the change saves as ever, and the board keeps made and changed",
              saved.get("saved") is True and themes_mod.find_version(themes_mod.load(rowan), ai_board)["changed"] == after["changed"]
              and kept_made == made["made"])

        # \u2500\u2500 J. the GETs, once the project has a file
        code, _, err = run("gets", "show")
        no_file = code == 1 and "no GETs file yet" in err
        books = idiograph_routes.gets_books(root)
        when = themes_mod.now_iso()
        gdata, _c, _d, _t = gets_mod.assemble(root, books, when)
        gets_mod.write(root, gets_mod._file(gdata, when))
        code, text, _ = run("gets", "show")
        check("79: gets show waits for the GETs file, then shows the board with the cards in no GET",
              no_file and code == 0 and "GETs, Board 1 (b1). A GET needs 3 of the 3 participants." in text
              and "   PET Mabel: " in text and "[Rowan/g1]" in text)
        gops = spec("gops", {"request": "Group the two timetables", "operations": [
            {"op": "make", "ref": "t", "title": "Days given their shape by the dog", "inside": None,
             "members": ["Mabel/g1", "Rowan/g1"]}]})
        code, text, _ = run("gets", "apply", "b1", "--ops", gops, "--tool", "Claude Code")
        held = gets_mod.load(root)
        gboard = held["boards"][0]
        check("79: gets apply takes the same operations over its cards, a GET numbered as the screen numbers one, a revision first",
              code == 0 and [x["id"] for x in gboard["groups"]] == ["G1"] and gboard["groups"][0]["members"] == ["Mabel/g1", "Rowan/g1"]
              and gboard["history"][-1]["name"] == "Before: Group the two timetables" and gboard["changed"]["by"] == "agent"
              and "Made 'Days given their shape by the dog'." in text)

        # \u2500\u2500 K. /api/stamp, what the page asks
        before = files(root)
        stamp = idiograph_routes.api_stamp({"workbook": str(rowan)})
        gstamp = idiograph_routes.api_stamp({"workbook": str(rowan), "gets": True})
        jstamp = idiograph_routes.api_stamp({"workbook": str(juno)})
        names = {b["name"]: b for b in stamp["boards"]}
        check("79: /api/stamp reads each board's updated with made and changed, the GETs file's too, and writes nothing",
              stamp["file"] == "themes" and names["Board 2"]["made"]["by"] == "agent" and "changed" in names["Board 2"]
              and "made" not in names["Board 1"] and stamp["chosen"] == "v1" and gstamp["file"] == "gets"
              and gstamp["boards"][0]["changed"]["tool"] == "Claude Code" and files(root) == before
              and server_mod.ROUTES.get("/api/stamp") is idiograph_routes.api_stamp)
        check("79: and the turns an agent wrote, with the last, for Experiential statements",
              jstamp["turns"]["count"] == 1 and jstamp["turns"]["last"]["row"] == 15 and stamp["turns"]["count"] == 0)

        # \u2500\u2500 L. the guide: AGENTS.md at the case root, never over his own
        written = idiograph_routes.api_agents_guide({"path": str(juno)})
        guide = (root / "AGENTS.md").read_text(encoding="utf-8")
        again = idiograph_routes.api_agents_guide({"path": str(juno)})
        updated = idiograph_routes.api_agents_guide({"path": str(juno), "update": True})
        check("79: Write a guide writes AGENTS.md from docs/agents.md with the project filled in where the guide marks it",
              written["written"] and guide.startswith(idiograph_routes.AGENTS_MARK) and "<!-- project -->" not in guide
              and "This project is Dogs, a scratch project. Its research question: " + DEMO_QUESTION in guide
              and "A GET needs 3 of the 3 participants" in guide and "new board holds" not in guide
              and guide.split("\n\n", 1)[1].split("## This project", 1)[0]
              == support.source("docs/agents.md").read_text(encoding="utf-8").split("## This project", 1)[0])
        check("79: a second press offers to update the one it wrote, and updates it on the word",
              again == {"written": False, "ours": True, "said": idiograph_routes.AGENTS_OURS}
              and updated["written"] and updated["updated"])
        (root / "AGENTS.md").write_text("# My own notes for agents\n", encoding="utf-8")
        mine = None
        try:
            idiograph_routes.api_agents_guide({"path": str(juno), "update": True})
        except WorkbookError as exc:
            mine = str(exc)
        demo_refused = None
        try:
            idiograph_routes.api_agents_guide({"path": str(server_mod.DEMO_WORKBOOK)})
        except WorkbookError as exc:
            demo_refused = str(exc)
        check("79: never over a file he wrote, and never for the demo",
              mine == "AGENTS.md in the project folder is your own, so it was left as it is."
              and (root / "AGENTS.md").read_text(encoding="utf-8") == "# My own notes for agents\n"
              and demo_refused and not (demo / "AGENTS.md").exists()
              and server_mod.ROUTES.get("/api/agents-guide") is idiograph_routes.api_agents_guide)

        # \u2500\u2500 M. validate: the files as written, then each problem one plain line
        code, text, _ = run("validate")
        broken = json.loads(themes_mod.themes_path(rowan).read_text(encoding="utf-8"))
        del broken["boards"][0]["groups"][0]["label"]
        broken["boards"][0]["cards"]["Initial:3:0"]["x"] = "left"
        themes_mod.themes_path(rowan).write_text(json.dumps(broken), encoding="utf-8")
        side = json.loads(rounds_mod.progress_path(juno).read_text(encoding="utf-8"))
        side["rows"]["Initial:3"] = "done"
        rounds_mod.progress_path(juno).write_text(json.dumps(side), encoding="utf-8")
        code_bad, bad_text, _ = run("validate")
        check("79: validate reads every file of the project against its schema, the agent's writes among them",
              code == 0 and text.startswith("Every file of the project reads as its schema says:") and "the GETs file" in text)
        check("79: and a problem is one plain line naming the case, the file and the place",
              code_bad == 0 and "Rowan, the themes file: themes.boards[0].groups[0].label is missing." in bad_text
              and "Rowan, the themes file: themes.boards[0].cards[\"Initial:3:0\"].x should be a number, not text." in bad_text
              and "Juno, the progress file: progress.rows[\"Initial:3\"] should be one of \"has-content\", \"reviewed-empty\", not \"done\"." in bad_text,
              bad_text[:400])

        # \u2500\u2500 N. a case folder's second part never reaches any output
        second = "P9 - {}-{}".format("Alder", "Beta")
        other = make_root(scratch / "agent-cli-folders", names=("Juno",), folders={"Juno": second})
        (other / server_mod.PROJECT_FILE).write_text(json.dumps({"name": "Folders", "agents": {"allowed": True, "at": "x"}}),
                                                     encoding="utf-8")
        said = []
        for args in (("cases",), ("cases", "--json"), ("statements", "P9"), ("board", "show", "Alder", "nothing"),
                     ("validate",), ("turn", "show", "P9 - Alder", "Initial", "999")):
            said.append("".join(run(*args, at=other)[1:]))
        check("79: no output or error carries a case folder's second part, the case by its pseudonym alone",
              not [s for s in said if folder.search(s) or "Alder-" in s] and "P9 - Alder: Juno - EN & ES.xlsx" in said[0],
              said[0][:200])
    finally:
        (server_mod.CONFIG_PATH, server_mod.ROOT_OVERRIDE, server_mod.STATE_MEMORY, server_mod.DEMO_DIR,
         server_mod.SHIPPED_DEMO, server_mod.DEMO_CASE, server_mod.DEMO_WORKBOOK, server_mod.DEMO_PROJECT, locks.WAIT) = kept
    check("79: the live settings file is exactly as it was",
          (server_mod.CONFIG_PATH.read_bytes() if server_mod.CONFIG_PATH.exists() else None) == live_config)

    check("79: the PETs and GETs screens ask the stamp on a focus and every few seconds, GETs every thirty (20 October, "
          "two windows in step), never over a save of their own",
          "window.addEventListener('focus', () => thStampTick());" in fn(js, "thOutsideBoot")
          and "}, 4 * 1000);" in fn(js, "thOutsideBoot") and "Date.now() - (TH.stampLast || 0) < 30 * 1000" in fn(js, "thOutsideBoot")
          and "thOutsideBoot();" in fn(js, "themesBoot")
          and "TH.busy || TH.chain || TH.saveTimer || TH.dirty" in fn(js, "thStampTick")
          and "api('/api/stamp', { workbook: path, gets: mode === 'gets' })" in fn(js, "thStampTick")
          and "TH.known[TH.meta.id] = data.updated;" in fn(js, "thSaveOnce") and "thKnow(TH.boards);" in fn(js, "thLoad"))
    # Show it and Update (20 October) run thOutsideTake
    show = fn(js, "thOutsideTake")
    check("79: Show it puts the page's own work first through the autosave, then loads, and never before",
          "await thOutsideTake(o);" in fn(js, "thOutsideShow")
          and show.index("await thFlush();") < show.index("api('/api/themes', { workbook: TH.path, board: o.board })")
          and "thLoad(data, { fit: !o.changed });" in show and 'id="th-outside-show" tabindex="-1">Show it</button>' in page
          and "if (refusedAs(err, 'board_changed_outside')) thStampTick(true);" in fn(js, "thSaveOnce"))
    check("79: Experiential statements does the same for a turn an agent wrote, Show it saving the turn first",
          "api('/api/stamp', { workbook: path })" in fn(app, "esStampTick")
          and fn(app, "esOutsideShow").index("await commit(current(), false);") < fn(app, "esOutsideShow").index("api('/api/open'")
          and "startCase(data, { land: { sheet: last.sheet, row: last.row } });" in fn(app, "esOutsideShow")
          and "setInterval(esStampTick, ES_STEP_EVERY);" in app and "if (!inPlace) esStampStart();" in fn(app, "startCase"))
    check("79: Project settings carries the tick and Write a guide for AI agents, the tick saved with Save, per project",
          '<input type="checkbox" id="set-agents"> Allow AI agents to read this project</label>' in page
          and 'id="agents-guide">Write a guide for AI agents</button>' in page
          and "out.push({ ...projectBody(p), agents: $('set-agents').checked });" in fn(app, "projectSaves")
          and "api('/api/agents-guide', update ? { ...projectBody(), update: true } : projectBody())" in fn(app, "agentsGuide")
          and "$('set-agents').disabled = !p.agents || !!p.demo;" in fn(app, "drawAgents")
          and "drawAgents(p);" in fn(app, "drawProjectPane"))
    node = shutil.which("node")
    if node:
        script = scratch / "agent-cli-stamp.js"
        script.write_text(support.i18n_js() + js + r"""
const known = { v1: 't1', v2: 't2' };
const out = {
  none: thStampSeen({ boards: [{ id: 'v1', name: 'Board 1', updated: 't1' }, { id: 'v2', name: 'Board 2', updated: 't2' }] }, known, 'v1'),
  added: thStampSeen({ boards: [{ id: 'v1', name: 'Board 1', updated: 't1' }, { id: 'v5', name: 'AI board 5', updated: 't9', made: { by: 'agent' } }] }, known, 'v1'),
  changed: thStampSeen({ boards: [{ id: 'v1', name: 'Board 1', updated: 't3', changed: { by: 'agent' } }, { id: 'v5', name: 'AI board 5', updated: 't9', made: { by: 'agent' } }] }, known, 'v1'),
  elsewhere: thStampSeen({ boards: [{ id: 'v1', name: 'Board 1', updated: 't1' }, { id: 'v3', name: 'Board 3', updated: 't4' }] }, known, 'v1'),
  other: thStampSeen({ boards: [{ id: 'v1', name: 'Board 1', updated: 't1' }, { id: 'v2', name: 'Board 2', updated: 't7', changed: { by: 'agent' } }] }, known, 'v1'),
};
console.log(JSON.stringify(out));
""", encoding="utf-8")
        ran = subprocess.run([node, str(script)], capture_output=True, text=True, encoding="utf-8")
        seen = support.plain(json.loads(ran.stdout)) if ran.returncode == 0 else {}
        check("79: in node, the corner line: a board added in a conversation, the board on the canvas changed, outside the app "
              "(another window until 20 October, when a window of the app came to load its change by itself), none",
              seen.get("none") is None and seen.get("added") == {"board": "v5", "updated": "t9", "changed": False,
                                                                 "line": "AI board 5 added in a conversation."}
              and seen.get("changed", {}).get("line") == "This board changed in a conversation." and seen["changed"]["changed"]
              and seen.get("elsewhere", {}).get("line") == "Board 3 added outside Idiograph." and seen.get("other") is None,
              ran.stderr.strip()[:300] or str(seen)[:300])
    else:
        skip("79: the corner line in node", "no node on this machine")

    # \u2500\u2500 P. the guide, the skill, the wrapper, the bundle and the words
    import app_identity
    guide = support.source("docs/agents.md").read_text(encoding="utf-8")
    skill = support.source("skills/idiograph/SKILL.md").read_text(encoding="utf-8")
    check("79: the skill carries the same guide for Claude Code and Claude Desktop, under its name and description",
          skill.startswith("---\nname: idiograph\ndescription: ") and skill.split("\n---\n\n", 1)[1] == guide)
    wrapper = support.source("idiograph").read_text(encoding="utf-8")
    build_src = support.source("packaging/build_mac.py").read_text(encoding="utf-8")
    launch_src = support.source("packaging/mac_launcher.py").read_text(encoding="utf-8")
    check("79: the wrapper runs the root venv's python on cli.py, the bundle takes cli first, and ships the guide and the schemas",
          os.access(support.source("idiograph"), os.X_OK) and '.venv/bin/python3' in wrapper and 'cli.py" "$@"' in wrapper
          and "cli.py" in support.source("idiograph.bat").read_text(encoding="utf-8")
          and '"cli", "locks",' in build_src and {"docs/agents.md", "docs/schemas"} <= set(app_identity.files("idiograph"))
          and 'if given[:1] == ["cli"]:' in launch_src and "return cli.main(args)" in launch_src)
