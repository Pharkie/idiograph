from __future__ import annotations

import inspect
import json
import re
import shutil
import sys
from pathlib import Path

import openpyxl

import rounds as rounds_mod
import workbook as wb_mod
from workbook import WorkbookError

from . import support
from .support import TOOL, check, same_workbook, skip, suite_text
import idiograph_routes


def test_demo_cases(scratch):
    print("\n74. The demo as a finished project: Juno, Rowan and Mabel built from their sources, annotated, their PETs "
          "marked complete, the GETs across them marked complete, the Demo rows, Reset demo for all three, the guard, "
          "the switcher and the Mac app")
    import hashlib
    import importlib.util
    import subprocess
    import make_demo
    import server as server_mod
    import themes as themes_mod

    def tree(folder):
        return {p.relative_to(folder).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
                for p in sorted(Path(folder).rglob("*")) if p.is_file()}

    demo = support.source("demo")
    pristine = demo / "pristine"
    repo_demo = tree(demo)
    # every case of the demo is built from its sources since 26 October, Juno's too, and each has its
    # recording since 12 November (recvoices)
    written = make_demo.CASES
    book_of = lambda folder, name: Path(folder) / f"{name} - EN & ES.xlsx"

    # ── 1. the two interviews: real speech on Juno's topic, one sheet, the interviewer as Juno's is
    juno_rows = make_demo.read_turns()
    interviewer = {r["Name"].strip() for r in juno_rows} - {make_demo.PARTICIPANT}
    readme = support.source("README.md").read_text(encoding="utf-8")
    manual = support.source("docs/manual.md").read_text(encoding="utf-8")
    internals = support.source("docs/internals.md").read_text(encoding="utf-8")
    denied = {m.group(1) for src in (readme, manual, internals, suite_text())
              for m in re.finditer(r"P\d+\s*-?\s*([A-Z][a-z]{2,})", src)} - {"Pseudonym", "Nobody"}
    sources = {}
    for name in written:
        csv_path, notes_path = make_demo.written_sources(name)
        rows = make_demo.read_turns(csv_path)
        notes = make_demo.read_annotations(notes_path)
        sources[name] = (rows, notes)
        text = " ".join(r["Transcript"] for r in rows)
        check(f"74: {name}'s interview is on Juno's topic, with hesitations, in nobody's words",
              "dog" in text and re.search(r"\b(Erm|Well)\.", text) and len(text.split()) > 1500
              and not [n for n in denied if re.search(rf"\b{n}\b", text)], f"{len(text.split())} words")
        board = notes["board"]

    # ── 2. built from source, byte for byte, into pristine and the live case folders, the GETs with them
    rebuilt = scratch / "demo-cases-rebuilt"
    shutil.rmtree(rebuilt, ignore_errors=True)
    built = make_demo.build_all(rebuilt)
    shipped_gets = pristine / make_demo.GETS_FILE
    check("74: make_demo rebuilds the GETs file across the three from source, byte for byte",
          shipped_gets.is_file() and built["gets"]["file"].read_bytes() == shipped_gets.read_bytes(),
          f"{built['gets']['gets']} GETs, {built['gets']['set_aside']} set aside, {built['gets']['rows']} quotes ticked")
    for name in written:
        parts = {"workbook": book_of(pristine, name),
                 "progress": pristine / "Working" / f"{name} - EN & ES.progress.json",
                 "themes": pristine / "Working" / f"{name} - EN & ES.themes.json"}
        # the workbook as the same parts and trees, since another Python's XML writer spells them
        # differently, and the two files of JSON byte for byte (14 October)
        check(f"74: make_demo rebuilds {name}'s workbook, progress file and board from source, the same on any Python",
              same_workbook(built[name]["workbook"], parts["workbook"])
              and all(built[name][k].read_bytes() == parts[k].read_bytes() for k in ("progress", "themes")),
              ", ".join(f"{k} {hashlib.sha256(parts[k].read_bytes()).hexdigest()[:8]}" for k in parts))
        live = book_of(demo / name, name)
        check(f"74: {name}'s live case folder holds the workbook as it ships, in the shape Juno's takes",
              live.is_file() and live.read_bytes() == parts["workbook"].read_bytes(), live.parent.name)

    # ── 2b. a quote of pieces (esredo2, 12 November 2026): each piece found in order in the turn, or running on into
    # her next turn as the turn screen allows (quotespan), written in its statement's own row, and a quote out of
    # order or not in her words refused with nothing built
    def mabel_with(quote):
        folder = scratch / "demo-quote-pieces"
        shutil.rmtree(folder, ignore_errors=True)
        (folder / "source").mkdir(parents=True)
        csv_path, notes_path = make_demo.written_sources("Mabel")
        shutil.copyfile(csv_path, folder / "source" / csv_path.name)
        notes = json.loads(notes_path.read_text(encoding="utf-8"))
        notes["turns"][0]["kq"][0] = quote
        (folder / "source" / notes_path.name).write_text(json.dumps(notes, ensure_ascii=False), encoding="utf-8")
        try:
            return make_demo.build_written("Mabel", folder / "built", folder)["workbook"], ""
        except make_demo.DemoError as exc:
            return None, str(exc)

    across = "That's the nearest I can get to it. … And I'm a tidy person, or I was."
    book, said = mabel_with(across)
    mabel_rows = wb_mod.read_case(book)["sheets"][0]["rows"] if book else []
    first = next((i for i, r in enumerate(mabel_rows) if r["name"] == "Mabel"), 0)
    check("74: a quote whose second piece is in her next turn is written whole in its statement's own row, "
          "and found across the two",
          book and mabel_rows[first]["pairs"][0]["kq"] == f'"{across}"'
          and mabel_rows[first + 2]["pairs"][0]["kq"] == f'"{sources["Mabel"][1]["turns"][1]["kq"][0]}"'
          and [k for k, _s, _e in wb_mod.quote_turns(mabel_rows, first, f'"{across}"', sorted(interviewer)[0])]
          == [first, first + 2], said)
    _, swapped = mabel_with("That's the nearest I can get to it. … It's like having the lights on.")
    _, unsaid = mabel_with("It's like having the LIGHTS on.")
    check("74: a quote with its pieces out of order, or in words she did not say, refuses the build",
          "its pieces in order" in swapped and "not word for word as said" in unsaid, f"{swapped} | {unsaid}")

    # ── 3. annotated as Adam annotates: every turn decided, the register, quotes verbatim, no fills
    for name in written:
        book = book_of(pristine, name)
        rows, notes = sources[name]
        case = wb_mod.read_case(book)
        sheet = case["sheets"][0]
        theirs = [r for r in sheet["rows"] if r["name"] == name]
        progress = rounds_mod.load_progress(book)
        made = rounds_mod.build_rounds(case["sheets"], 10, sorted(interviewer)[0])
        summary = rounds_mod.summary(case["sheets"], progress, made, sorted(interviewer)[0], 2)
        states = summary["states"]
        check(f"74: {name}'s workbook passes the reader, one sheet, Initial, with Adam's six columns",
              [s["name"] for s in case["sheets"]] == ["Initial"] and len(sheet["rows"]) == len(rows)
              and {"name", "ts", "es", "transcript", "en", "kq"} <= set(sheet["columns"]))
        check(f"74: every one of {name}'s turns is decided, with content or reviewed and left empty",
              len(states) == len(theirs) and rounds_mod.HAS_CONTENT in set(states.values())
              and set(states.values()) <= {rounds_mod.HAS_CONTENT, rounds_mod.REVIEWED_EMPTY}
              and summary["turnsDone"] == summary["turnsTotal"] == len(theirs),
              f"{list(states.values()).count(rounds_mod.REVIEWED_EMPTY)} reviewed and empty of {len(theirs)}")
        statements = [line for r in theirs for line in r["es"].splitlines() if line.strip()]
        # each statement with its own quote since 12 November 2026 (esredo2): the annotations' quote i is statement
        # i's, saved paired, its pieces found in order in the turn and joined with an ellipsis as the turn screen
        # joins them
        at = {r["row"]: i for i, r in enumerate(sheet["rows"])}
        pairs = [(r, p) for r in theirs for p in r["pairs"]]
        given = [(s, f'"{q}"') for item in notes["turns"] for s, q in zip(item.get("es") or [], item.get("kq") or [])]
        check(f"74: {name}'s statements each hold their own key quote, as the annotations pair them, none to pair",
              len(pairs) == len(statements) > 0 and not any(r["unpaired"] for r in theirs)
              and [(p["es"], p["kq"]) for _r, p in pairs] == given, f"{len(pairs)} statements")
        pieced = [p for _r, p in pairs if "…" in p["kq"]]
        check(f"74: {name}'s key quotes are verbatim from their turns, in inverted commas, piece by piece in order, "
              "each turn with content holding a note",
              pieced and all(p["kq"].startswith('"') and p["kq"].endswith('"')
                             and {k for k, _s, _e in wb_mod.quote_turns(sheet["rows"], at[r["row"]], p["kq"],
                                                                        sorted(interviewer)[0])} == {at[r["row"]]}
                             for r, p in pairs)
              and all(r["en"].strip() for r in theirs
                      if progress["rows"].get(rounds_mod.row_key("Initial", r["row"])) == rounds_mod.HAS_CONTENT),
              f"{len(pieced)} of {len(pairs)} quotes in pieces")
        runs = [x for r in theirs for x in r["runs"] if x["crux"]]
        book_open = openpyxl.load_workbook(book, rich_text=True)
        fills = [c for row in book_open[book_open.sheetnames[0]].iter_rows() for c in row
                 if c.fill is not None and c.fill.fill_type]
        book_open.close()
        check(f"74: {name}'s highlights are real orange runs, and no cell carries a fill", runs and not fills,
              f"{len(runs)} runs")
        check(f"74: {name}'s rounds are closed, each with its minutes and day, and Statements complete is marked",
              summary["roundsDone"] == [r["number"] for r in made] and len(made) >= 2
              and all(progress["rounds"][str(r["number"])]["completed"] for r in made)
              and sum(d["rounds"] for d in progress["days"].values()) == len(made)
              and rounds_mod.complete_of(book) and summary["complete"] == rounds_mod.complete_of(book)
              and progress["last"] == {"sheet": "Initial", "row": theirs[-1]["row"]})

        # ── 4. the board: Board 1, the Current board, PETs complete, every state the GETs panel shows
        data = themes_mod.load(book)
        boards = themes_mod.boards_of(data)
        board = boards[0] if boards else {}
        groups = board.get("groups") or []
        inside = {m for g in groups for m in g["members"]}
        pets = [g for g in groups if g["id"] not in inside]
        subs = [g for g in groups if g["id"] in inside]
        placed = {k for g in groups for k in g["members"] if k in board.get("cards", {})}
        gone = set(board.get("discarded") or [])
        unplaced = set(board.get("cards", {})) - placed - gone
        check(f"74: {name}'s themes file has one board, Board 1, the Current board and marked PETs complete",
              len(boards) == 1 and board["name"] == "Board 1" and data.get("chosen") == board["id"]
              and themes_mod.complete_of(data) == {"at": data["complete"]["at"], "board": board["id"], "name": "Board 1"}
              and data.get("case") == name and themes_mod.chosen_name(book) == "Board 1")
        # three PETs each since 12 November 2026 (esredo2), as the annotations title them, no note on a label
        check(f"74: {name}'s board has the annotations' three PETs, sub-themes in some, each PET with a key quote "
              "picked, and every PET and sub-theme with a description",
              [g["label"] for g in pets] == [p["title"] for p in notes["board"]["pets"]] and len(pets) == 3 and subs
              and all(themes_mod.description_of(g) for g in groups)
              and all(board["picks"].get(g["id"]) for g in pets) and set(board.get("quoted") or {}) == {
                  k for chosen in board["picks"].values() for k in chosen},
              f"{len(pets)} PETs, {len(subs)} sub-themes")
        check(f"74: {name}'s board places every statement but those the annotations leave unplaced or discard",
              len(unplaced) == len(notes["board"].get("unplaced") or [])
              and len(gone) == len(notes["board"].get("discarded") or [])
              and len(placed) + len(unplaced) + len(gone) == len(statements)
              and set(board["cards"]) == {c["key"] for c in themes_mod.read_cards(book)["cards"]},
              f"{len(placed)} placed, {len(unplaced)} unplaced, {len(gone)} discarded")
        shown = themes_mod.state(book, name)
        check(f"74: {name}'s board opens on the canvas as it was saved, nothing new, changed or missing",
              shown["saved"] and shown["chosen"] == "v1" and not [c for c in shown["cards"]
                                                                 if c.get("new") or c.get("changed") or c.get("missing")])

    # ── 5. the GETs across the three, finished: five GETs, each with its description, every
    # participant in from a board marked complete, the board current and marked complete, every card
    # placed or set aside, every row of the GET table with its quote ticked
    import gets as gets_mod
    held = json.loads(shipped_gets.read_text(encoding="utf-8"))
    board = gets_mod.boards_of(held)[0] if gets_mod.boards_of(held) else {}
    tops = [g for g in board.get("groups") or [] if g["id"] not in {m for x in board["groups"] for m in x["members"]}]
    check("74: the GETs file holds one board, Board 1, the Current board, GETs marked complete on it",
          len(gets_mod.boards_of(held)) == 1 and board.get("name") == "Board 1" and held.get("chosen") == board.get("id")
          and (held.get("complete") or {}).get("board") == board.get("id"))
    check("74: every participant is in from their PETs marked complete, unchanged",
          sorted(held.get("cases") or {}) == sorted(make_demo.CASES)
          and all(r["state"] == "in" and r["complete"] and r["name"] == "Board 1" for r in held["cases"].values()))
    placed = {m for g in board["groups"] for m in g["members"]}
    check("74: five GETs, each with a description, each drawing on all three participants",
          len(tops) == 5 and all(themes_mod.description_of(g) for g in tops)
          and all({gets_mod.split_key(m)["case"] for m in g["members"]} == set(make_demo.CASES) for g in tops),
          str([len(g["members"]) for g in tops]))
    check("74: every PET and sub-PET card is under a GET or set aside, none left not placed",
          set(board["cards"]) == placed | set(board["discarded"]) and not placed & set(board["discarded"]),
          f"{len(placed)} placed, {len(board['discarded'])} set aside")
    rows = gets_mod.rows_of(board)
    check("74: every participant's row of every GET has its quote ticked",
          all(set(rows.get(g["id"]) or {}) == set(make_demo.CASES) and all(r["quote"] for r in rows[g["id"]].values())
              for g in tops))

    # ── 6. Juno is finished too, her CSV and recording where they were
    juno_side = json.loads((pristine / "Working" / "Juno - EN & ES.progress.json").read_text(encoding="utf-8"))
    check("74: Juno ships finished, her board and her mark in her pristine copy, her CSV and recording where they were",
          (pristine / "Working" / "Juno - EN & ES.themes.json").exists() and "complete" in juno_side
          and len(juno_rows) == 79 and make_demo.recording() == demo / "Juno" / "Source" / "Initial" / "Source" / "Juno-Initial.m4a"
          and make_demo.CASES == ("Juno", "Rowan", "Mabel") and idiograph_routes.DEMO_CASES == make_demo.CASES
          and idiograph_routes.demo_title(server_mod.DEMO_WORKBOOK) == idiograph_routes.DEMO_TITLE
          and idiograph_routes.demo_workbooks()[0] == server_mod.DEMO_WORKBOOK)

    # ── 7. Reset demo puts all three back and the GETs file, and takes its exports away
    work = scratch / "demo-cases-reset"
    shutil.rmtree(work, ignore_errors=True)
    shutil.copytree(pristine, work / "pristine")
    filled = make_demo.fill(work / "pristine", work)
    check("74: fill copies each case's workbook, progress file and board, and the GETs file, where they are missing",
          len(filled) == 10 and all(p.is_file() for p in filled)
          and all(themes_mod.themes_path(book_of(work / n, n)).is_file() for n in make_demo.CASES)
          and (work / make_demo.GETS_FILE).read_bytes() == shipped_gets.read_bytes(), f"{len(filled)} files")
    rowan = book_of(work / "Rowan", "Rowan")
    wb_mod.save_turn(rowan, "Initial", 3, "A statement written on camera", None, None)
    check("74: and a second fill finds nothing missing and replaces nothing",
          make_demo.fill(work / "pristine", work) == []
          and rowan.read_bytes() != book_of(work / "pristine", "Rowan").read_bytes())
    mabel = book_of(work / "Mabel", "Mabel")
    rounds_mod.set_complete(mabel, False)
    themes_mod.write(mabel, {"schema": 2, "boards": []})
    juno_board = themes_mod.themes_path(book_of(work / "Juno", "Juno"))
    juno_board.write_text("{}", encoding="utf-8")
    (work / "idiograph-gets.json").write_text("{}", encoding="utf-8")
    (work / "Working").mkdir()
    (work / "Working" / "GETs table.pdf").write_bytes(b"an export")
    make_demo.reset_all(work / "pristine", work)
    restored = all(book_of(work / n, n).read_bytes() == book_of(work / "pristine", n).read_bytes()
                   and rounds_mod.progress_path(book_of(work / n, n)).read_bytes()
                   == (work / "pristine" / "Working" / f"{n} - EN & ES.progress.json").read_bytes()
                   for n in make_demo.CASES)
    boards_back = all(themes_mod.themes_path(book_of(work / n, n)).read_bytes()
                      == (work / "pristine" / "Working" / f"{n} - EN & ES.themes.json").read_bytes() for n in written)
    check("74: Reset demo puts all three cases back as they ship, their boards with them",
          restored and boards_back and juno_board.read_bytes() != b"{}")
    check("74: and puts the demo's GETs file back as it ships, and removes the exports' Working folder",
          (work / "idiograph-gets.json").read_bytes() == shipped_gets.read_bytes() and not (work / "Working").exists())
    lock = wb_mod.lock_file(mabel)
    lock.write_text("x", encoding="utf-8")
    wb_mod.save_turn(rowan, "Initial", 3, "Written again", None, None)
    try:
        make_demo.reset_all(work / "pristine", work)
        refused = False
    except WorkbookError:
        refused = True
    finally:
        lock.unlink()
    check("74: a workbook open in Excel refuses the whole reset before anything is written",
          refused and rowan.read_bytes() != book_of(work / "pristine", "Rowan").read_bytes())

    # ── 8. the server: every demo case a demo case, the rows, the switcher, the guard, the route
    kept = (server_mod.DEMO_DIR, server_mod.DEMO_CASE, server_mod.DEMO_WORKBOOK, server_mod.SHIPPED_DEMO,
            server_mod.DEMO_PROJECT, server_mod.ROOT_OVERRIDE, server_mod.STATE_MEMORY)
    root = scratch / "demo-cases-root"
    root.mkdir(exist_ok=True)
    shipped = scratch / "demo-cases-shipped"
    shutil.rmtree(shipped, ignore_errors=True)
    shutil.copytree(pristine, shipped / "pristine")
    shutil.copyfile(server_mod.DEMO_PROJECT, work / "idiograph-project.json")
    try:
        server_mod.DEMO_DIR, server_mod.SHIPPED_DEMO = work, shipped
        server_mod.DEMO_CASE = work / "Juno"
        server_mod.DEMO_WORKBOOK = server_mod.DEMO_CASE / "Juno - EN & ES.xlsx"
        server_mod.DEMO_PROJECT = work / "idiograph-project.json"
        server_mod.ROOT_OVERRIDE, server_mod.STATE_MEMORY = str(root), {"recent": []}
        rowan, mabel = book_of(work / "Rowan", "Rowan"), book_of(work / "Mabel", "Mabel")
        cases = idiograph_routes.api_cases({})
        rows = cases.get("demos") or []
        check("74: the case list sends the Demo rows, Juno, Rowan and Mabel, and Juno's alone as demo",
              [r["case"] for r in rows] == ["Juno", "Rowan", "Mabel"] and all(r["demo"] for r in rows)
              and [r["name"] for r in rows] == ["Juno, living with a dog", "Rowan, living with a dog", "Mabel, living with a dog"]
              and cases["demo"]["case"] == "Juno", str([r["name"] for r in rows]))
        check("74: every demo row carries its marks and its Current board, the demo being finished",
              all(r["complete"] and r["pets_complete"] and r["board"] == "Board 1" for r in rows))
        check("74: every demo case is a demo case to the server, through the root guard and is_demo",
              all(server_mod.is_demo(b) and server_mod.within_root(b) and idiograph_routes.case_path(str(b)) == b
                  for b in (rowan, mabel))
              and not server_mod.within_root(work.parent / "demo-cases-rebuilt" / "Rowan" / rowan.name))
        refused = []
        for b in (rowan, mabel):
            try:
                idiograph_routes.api_project({"path": str(b), "name": "Another name"})
                refused.append(False)
            except WorkbookError:
                refused.append(True)
        opened = idiograph_routes.case_payload(rowan)
        check("74: a project save from a demo case is refused, and each opens on the demo's own project",
              refused == [True, True] and json.loads(server_mod.DEMO_PROJECT.read_text(encoding="utf-8"))["name"] == "Living with a dog"
              and opened["demo"] and opened["name"] == "Rowan, living with a dog"
              and opened["project"]["name"] == "Living with a dog" and opened["project"]["demo"])
        idiograph_routes.remember(rowan)
        server_mod.STATE_MEMORY = {"recent": [{"path": server_mod.rel_path(mabel), "name": mabel.stem,
                                               "case": "Mabel", "opened": 1}]}
        check("74: the recent list leaves the demo cases out, on the way in and on the way out",
              idiograph_routes.recent_entries([]) == [] and idiograph_routes.api_cases({})["recent"] == [])
        switcher = idiograph_routes.api_themes_cases({"workbook": str(mabel)})["cases"]
        check("74: the PETs switcher on any demo case lists the three, the one open the current one",
              [c["case"] for c in switcher] == ["Juno", "Mabel", "Rowan"]
              and [c["current"] for c in switcher] == [False, True, False]
              and [c["chosen"] for c in switcher] == [True, True, True], str([c["case"] for c in switcher]))
        heard = idiograph_routes.api_audio({"path": str(rowan), "sheet": "Initial"})
        stand_in = shipped / "Rowan" / "Source" / "Initial" / "Source" / "Rowan-Initial.m4a"
        stand_in.parent.mkdir(parents=True)
        stand_in.write_bytes(b"a stand-in for Rowan's recording")
        played = idiograph_routes.api_audio({"path": str(rowan), "sheet": "Initial"})
        check("74, updated 13 November 2026 (recdemand): Rowan's recording, missing from the demo the app works on, is "
              "never copied from the shipped copy, which carries none, and with no manifest naming it his player "
              "stays quiet, nothing built or fetched",
              heard["found"] is False and not heard.get("building") and not heard.get("download")
              and played["found"] is False and not make_demo.recording("Rowan", work).exists(), heard.get("note", ""))
        wb_mod.save_turn(rowan, "Initial", 3, "A statement written on camera", None, None)
        (work / "idiograph-gets.json").write_text("{}", encoding="utf-8")
        answer = idiograph_routes.api_reset_demo({})
        check("74: the Reset demo route resets all three from the shipped copy and the GETs file with them",
              answer["reset"] and rowan.read_bytes() == book_of(shipped / "pristine", "Rowan").read_bytes()
              and (work / "idiograph-gets.json").read_bytes() == (shipped / "pristine" / make_demo.GETS_FILE).read_bytes()
              and themes_mod.themes_path(mabel).read_bytes()
              == (shipped / "pristine" / "Working" / "Mabel - EN & ES.themes.json").read_bytes())
    finally:
        (server_mod.DEMO_DIR, server_mod.DEMO_CASE, server_mod.DEMO_WORKBOOK, server_mod.SHIPPED_DEMO,
         server_mod.DEMO_PROJECT, server_mod.ROOT_OVERRIDE, server_mod.STATE_MEMORY) = kept
    main_src = inspect.getsource(server_mod.main)
    check("74: a normal start fills in what a clone lacks, and a run with --root leaves the demo alone",
          "start_up(args)" in main_src
          and "for start in start_hooks():\n        start(bool(args.root))" in inspect.getsource(server_mod.start_up)
          and server_mod.STARTS == [("idiograph", idiograph_routes.start)]
          and "if not one_root:\n        fill_demo()" in inspect.getsource(idiograph_routes.start)
          and "(srv.SHIPPED_DEMO, srv.DEMO_DIR)" in inspect.getsource(idiograph_routes.fill_demo)
          and 'make_demo.fill(shipped / "pristine", live)' in inspect.getsource(idiograph_routes.fill_demo))

    # ── 8. the page: the rows, the place for the GETs head row, Reset demo once under them
    js = support.text("family/static/shell.js", "apps/idiograph/static/distil.js")
    fn = lambda name: js.split(f"function {name}(", 1)[1].split("\n}", 1)[0] if f"function {name}(" in js else ""
    node = shutil.which("node")
    if not node:
        skip("74: the Demo rows in node", "node is not installed")
    else:
        script = scratch / "demo-rows.js"
        script.write_text(
            "function demoRows(" + fn("demoRows") + "\n}\n"
            "const a = { path: 'a' }, b = { path: 'b' }, c = { path: 'c' };\n"
            "console.log(JSON.stringify([demoRows({ demos: [a, b, c], demo: a }).length, demoRows({ demo: a }).length,\n"
            "  demoRows({}).length, demoRows({ demos: [], demo: null }).length, demoRows({ demos: [a, {}, null] }).length]));\n",
            encoding="utf-8")
        run = subprocess.run([node, str(script)], capture_output=True, text=True, encoding="utf-8")
        check("74: in node, three rows from this server, Juno's alone from an older one, none from one before the demo",
              run.returncode == 0 and json.loads(run.stdout or "[]") == [3, 1, 0, 0, 1], (run.stdout or run.stderr).strip()[:200])

    # ── 9. the Mac app stages the three and ships the template
    spec = importlib.util.spec_from_file_location("idiograph_build_mac_74", support.source("packaging/build_mac.py"))
    build = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(build)
    stage = scratch / "demo-cases-stage" / "stage"
    shutil.rmtree(stage.parent, ignore_errors=True)
    stage.mkdir(parents=True)
    staged = build.stage_demo(stage)
    files = tree(staged)
    want = [f"{n}/{n} - EN & ES.xlsx" for n in make_demo.CASES] + [
        f"{n}/Working/{n} - EN & ES.progress.json" for n in make_demo.CASES] + [
        f"{n}/Working/{n} - EN & ES.themes.json" for n in written] + [
        f"pristine/Working/{n} - EN & ES.themes.json" for n in written] + [
        make_demo.GETS_FILE, f"pristine/{make_demo.GETS_FILE}"]
    check("74, updated 13 November 2026 (recdemand): the build stages the three cases from pristine, their boards and "
          "the GETs with them, and the manifest of their recordings in place of the recordings",
          all(w in files for w in want) and files[make_demo.GETS_FILE] == files[f"pristine/{make_demo.GETS_FILE}"]
          and files.get("recordings.json") == hashlib.sha256(make_demo.MANIFEST.read_bytes()).hexdigest()
          and not [f for f in files if f.endswith(".m4a") or f.endswith("LICENSE-audio.md")]
          and all(files[f"{n}/{n} - EN & ES.xlsx"] == files[f"pristine/{n} - EN & ES.xlsx"] for n in make_demo.CASES)
          and build.DEMO_CASES == make_demo.CASES, f"{len(files)} files staged")
    spec_text = build.write_spec(scratch / "demo-cases-stage", stage, "0.9.0").read_text(encoding="utf-8")
    check("74: the bundle's data carries the transcript template, under template/",
          "Transcript template.xlsx" in spec_text and "'template')" in spec_text
          and (TOOL / build.TEMPLATE).is_file())

    # ── 10. the words
    ignored = support.source(".gitignore").read_text(encoding="utf-8").splitlines()
    check("74: the pristine boards are let in beside the pristine progress files, and the live ones kept out",
          "!demo/pristine/Working/*.themes.json" in ignored and "*.themes.json" in ignored
          and ignored.index("*.themes.json") < ignored.index("!demo/pristine/Working/*.themes.json"))
    check("74: the live GETs file is kept out and the pristine one, at the pristine copy's root, is not",
          "demo/idiograph-gets.json" in ignored and not any(
              line.strip() in ("idiograph-gets.json", "*.json", "demo/pristine/") for line in ignored))
    check("74: nothing in this area wrote into the repo's demo", tree(demo) == repo_demo)
