"""Area 366: PETs boards and LPETs made from his own tables (ayabuild34, 9 November 2026, the Ayahuasca plan's builds
3 and 4, Adam, 9 November about 13:40).

A table of PETs, PET, Sub-theme, Experiential statements, Location and Quote, its titles carried down, made into a
board at a timepoint: each row matched to a statement by its words, then at 0.8 or more on the passage at its
Location, then on the passage its quote is in, the table's wording replacing the nearest statement there as an edit
with History, a row with nothing close added as a new statement with its quote or skipped, a statement two rows name
placed once. A table of LPETs made into a participant's LPETs board: each row an LPET with its title, description and
a note of a paragraph a timepoint, the PETs its cells quote proposed as members. Through the command line and MCP,
dry runs first. Every word is invented: three bell ringers, Quill, Fennel and Sorrel, at T1 to T3."""
from __future__ import annotations

import io
import json
import shutil

import openpyxl

from . import support
from .support import check

HEAD = "Speaker,Time,Transcript,Experiential statements,Quote\n"
# Quill at T1: seven passages, each with a statement and its quote
QUILL_T1 = (HEAD +
            "Ash,0:01,How did it start?,,\n"
            'Quill,0:05,"The first time I held the sally my arms shook and the rope pulled me up onto my toes.",'
            "Being lifted by the rope as a first fear,the rope pulled me up onto my toes\n"
            'Quill,0:30,"Nobody talks in the tower once the ringing starts, you just listen to the bell before yours.",'
            "Listening as the way into the band,you just listen to the bell before yours\n"
            'Quill,0:55,"I counted every stroke out loud for months, which drove my teacher mad, but it held me together.",'
            "Counting aloud as a private scaffold,it held me together\n"
            'Quill,1:20,"When we rang the full peal I cried in the stairwell afterwards, nobody saw.",'
            "Hidden tears after the first peal,I cried in the stairwell afterwards\n"
            'Quill,1:44,"The bells belong to the village more than to us, we only borrow them on Sundays.",'
            "Borrowing the village's bells,we only borrow them on Sundays\n"
            'Quill,2:10,"My hands are hard now, there are ridges where the rope runs, and I like touching them.",'
            "Calluses as proof of belonging,there are ridges where the rope runs\n"
            'Quill,2:40,"I was late once and the whole band waited, and then, well, they just smiled at me and we started.",'
            "Being waited for,I was late once and the whole band waited\n")
QUILL_T2 = (HEAD + "Ash,0:04,How is the tower now?,,\n"
            'Quill,0:08,"I ring the treble on Sundays and the rhythm just lives in my wrists.",'
            "Rhythm settling into the body,the rhythm just lives in my wrists\n"
            'Quill,0:30,"The captain asked me to teach a new ringer, which felt absurd and lovely.",'
            "Becoming the one who teaches,which felt absurd and lovely\n")
QUILL_T3 = (HEAD + "Ash,0:05,A year on?,,\n"
            'Quill,0:09,"I moved away and found a tower in the new town within a week, it was like finding family.",'
            "A tower as portable home,it was like finding family\n"
            'Quill,0:35,"Sometimes I miss the old bells more than the people, which shocks me.",'
            "Missing the bells over the people,I miss the old bells more than the people\n")
OTHER = (HEAD + "Ash,0:02,What brought you?,,\n"
         "{who},0:06,My grandfather rang here before the war.,Inheriting the tower,My grandfather rang here\n")

# his table of Quill's T1 PETs: three PETs with sub-themes, a reworded row a second off its passage, a row whose
# quote has an ellipsis and nothing close on its passage, and a statement given twice
PETS_T1 = [
    ["PET", "Sub-theme", "Experiential statements", "Location", "Quote"],
    ["The body learns the rope", "Fear in the arms", "Being lifted by the rope as a first fear", "0:05",
     "the rope pulled me up onto my toes"],
    [None, "Hands that remember", "Calluses as proof of belonging", "2:10", "there are ridges where the rope runs"],
    ["Joining the band", "Listening in", "Listening as the way into the band", "0:30", "you just listen to the bell before yours"],
    [None, None, "Counting out loud as a private scaffold", "0:56", "it held me together"],
    [None, "Being held by others", "Patience of the band as welcome", None,
     "I was late once … they just smiled at me"],
    ["Bells that are not ours", None, "Borrowing the village's bells", "1:44", "we only borrow them on Sundays"],
    [None, None, "Listening as the way into the band", "0:30", "you just listen to the bell before yours"],
]
PETS_T2 = ("PET,Sub-theme,Experiential statements,Location,Quote\n"
           "Ringing without thinking,,Rhythm settling into the body,0:08,the rhythm just lives in my wrists\n"
           "Passing it on,,Becoming the one who teaches,0:30,which felt absurd and lovely\n")
PETS_T3 = ("PET,Sub-theme,Experiential statements,Location,Quote\n"
           "Belonging that travels,,A tower as portable home,0:09,it was like finding family\n"
           "The bells themselves,,Missing the bells over the people,0:35,I miss the old bells more than the people\n")


def book_of(rows: list, sheet: str, cover: bool = True) -> bytes:
    wb = openpyxl.Workbook()
    first = wb.active
    if cover:
        first.title = "Notes"
        first.append(["Invented, for the check"])
        ws = wb.create_sheet(sheet)
    else:
        ws = first
        ws.title = sheet
    for r in rows:
        ws.append(r)
    out = io.BytesIO()
    wb.save(out)
    return out.getvalue()


LPETS = [
    ["LPET", "T1 - First year", "T2", "T3"],
    ["From fear to fluency\nThe body learning the rope until it needs no counting",
     'At first the rope lifts her.\n"the rope pulled me up onto my toes"', "Counting falls away.", "Hardly mentioned now."],
    ["The bells as kin\nBelonging to the bells more than the people", "A borrowed belonging.", "Not spoken of.",
     "Missing them most of all."],
]


def test_tables_of_pets(scratch):
    print("\n366. PETs boards and LPETs made from his own tables: each row matched to a statement, exact, fuzzy, "
          "rewritten, added, skipped or a duplicate, the board laid out as given, and LPETs with members proposed "
          "and a note a timepoint (ayabuild34, 9 November)")
    import cli
    import mcp_server
    import rounds as rounds_mod
    import server as server_mod
    import themes
    import workbook as wb_mod
    import idiograph_routes as routes

    base = scratch / "tables-366"
    shutil.rmtree(base, ignore_errors=True)
    folder = base / "Ringing"
    inputs = base / "inputs"
    folder.mkdir(parents=True)
    inputs.mkdir()
    cfg = base / "config.json"
    cfg.write_text(json.dumps({"projects": [], "interviewer": "Researcher"}), encoding="utf-8")
    kept = (server_mod.CONFIG_PATH, server_mod.ROOT_OVERRIDE, server_mod.STATE_PATH, server_mod.STATE_MEMORY)
    try:
        server_mod.CONFIG_PATH, server_mod.ROOT_OVERRIDE = cfg, None
        server_mod.STATE_PATH, server_mod.STATE_MEMORY = base / "state.json", {"recent": []}
        (folder / server_mod.PROJECT_FILE).write_text(json.dumps(
            {"name": "Learning to ring", "timepoints": [{"label": "T1", "description": "First year"},
                                                        {"label": "T2"}, {"label": "T3"}],
             "agents": {"allowed": True, "at": "2026-11-09T10:00:00+00:00"}}), encoding="utf-8")
        routes.add_project(folder)
        config = base / "agent-config.json"
        config.write_text(json.dumps({"root": str(folder), "interviewer": "Researcher"}), encoding="utf-8")

        def run(*argv):
            code_, out, err = cli.run(["--root", str(folder), "--config", str(config), "--json", *argv])
            return code_, (support.plain(json.loads(out)) if out.strip() and code_ == 0 else out), err

        def said(*argv):
            return cli.run(["--root", str(folder), "--config", str(config), *argv])

        def state():
            return sorted((p.relative_to(folder).as_posix(), p.stat().st_mtime_ns) for p in folder.rglob("*") if p.is_file())

        files = {"quill t1.csv": QUILL_T1, "quill t2.csv": QUILL_T2, "quill t3.csv": QUILL_T3,
                 "fennel.csv": OTHER.format(who="Fennel"), "sorrel.csv": OTHER.format(who="Sorrel"),
                 "t2 pets.csv": PETS_T2, "t3 pets.csv": PETS_T3}
        for name, text in files.items():
            (inputs / name).write_text(text, encoding="utf-8")
        (inputs / "quill pets.xlsx").write_bytes(book_of(PETS_T1, "T1 PETs"))
        (inputs / "quill lpets.xlsx").write_bytes(book_of(LPETS, "LPETs"))
        speakers = lambda who: {"Ash": "Interviewer", who: "Participant"}
        spec = base / "spec.json"
        spec.write_text(json.dumps(
            [{"file": str(inputs / f"quill t{n}.csv"), "pseudonym": "Quill", "interview": f"Ringing {n}",
              "timepoint": f"T{n}", "speakers": speakers("Quill")} for n in (1, 2, 3)]
            + [{"file": str(inputs / f"{w.lower()}.csv"), "pseudonym": w, "interview": "Tower", "timepoint": "T1",
                "speakers": speakers(w)} for w in ("Fennel", "Sorrel")]), encoding="utf-8")
        code_, _added, err = run("project", "add-transcripts", "--from", str(spec), "--note", "Bring in the ringers",
                                 "--tool", "Claude Code")
        check("366: the fixture's three ringers come in, Quill at T1 to T3", code_ == 0, err[:300])
        book = folder / "P1 - Quill" / "P1 Quill - EN & ES.xlsx"

        # ── A. the dry run of a table of PETs lists every row's match and writes nothing
        table = str(inputs / "quill pets.xlsx")
        before = state()
        code_, dry, err = run("board", "import", "Quill", "--timepoint", "T1", "--from", table, "--sheet", "T1 PETs",
                              "--name", "From Excel (Oct 2025)", "--unmatched", "add", "--dry-run")
        rows = {r["row"]: r for r in dry.get("rows", [])} if code_ == 0 else {}
        counts = dry.get("counts", {}) if code_ == 0 else {}
        check("366: the dry run counts 4 matched word for word, 1 fuzzy, 1 unmatched and 1 duplicate, and writes nothing",
              code_ == 0 and state() == before and counts.get("exact") == 4 and counts.get("fuzzy") == 1
              and counts.get("unmatched") == 1 and counts.get("added") == 1 and counts.get("duplicate") == 1
              and counts.get("rewritten") == 0 and dry.get("name") == "From Excel (Oct 2025)",
              err or json.dumps(counts))
        check("366: titles are carried down, the reworded row a second off its passage is fuzzy by its Location with its "
              "ratio, the ellipsis quote finds its passage, and the second naming of a statement is named a duplicate",
              rows and rows[3]["pet"] == "The body learns the rope" and rows[3]["sub"] == "Hands that remember"
              and rows[5]["how"] == "fuzzy" and rows[5]["by"] == "location" and rows[5]["ratio"] >= 0.8
              and rows[5]["was"] == "Counting aloud as a private scaffold" and rows[5]["pet"] == "Joining the band"
              and rows[6]["how"] == "added" and rows[6]["by"] == "quote" and rows[6]["time"] == "02:40"
              and rows[8]["how"] == "duplicate" and rows[8]["of"] == 4 and rows[2]["how"] == "exact",
              json.dumps({k: (v["how"], v["by"], v.get("of"), v["ratio"]) for k, v in rows.items()}))
        code_t, text, _e = said("board", "import", "Quill", "--timepoint", "T1", "--from", table, "--sheet", "T1 PETs",
                                "--dry-run")
        check("366: the dry run's lines say each row, and without --unmatched add the row with nothing close is skipped",
              code_t == 0 and "1 skipped" in text and "Row 5: Counting out loud as a private scaffold, close to "
              "Counting aloud as a private scaffold" in text and "Row 8: Listening as the way into the band is row 4's" in text
              and "word for word" in text and state() == before, text[:900])

        # ── B. applied: the passages written as edits with History, then the board as given
        code_, done, err = run("board", "import", "Quill", "--timepoint", "T1", "--from", table, "--sheet", "T1 PETs",
                               "--name", "From Excel (Oct 2025)", "--unmatched", "add",
                               "--note", "Bring in my October PETs", "--tool", "Claude Code")
        case = wb_mod.read_case(book) if code_ == 0 else {"sheets": []}
        t1 = next((s for s in case["sheets"] if s["rows"] and "sally" in json.dumps(s["rows"])), {"rows": []})
        by = {r["text"][:14]: r for r in t1["rows"]}
        counting, late = by.get("I counted ever", {}), by.get("I was late onc", {})
        check("366: the reworded statement takes the table's words in its own place, its quote kept",
              code_ == 0 and [(x["es"], themes.quote_words(x["kq"])) for x in counting.get("pairs") or []]
              == [("Counting out loud as a private scaffold", "it held me together")], err or str(counting.get("pairs")))
        check("366: the row with nothing close is a new statement on the passage its quote is in, with that quote",
              [p["es"] for p in late.get("pairs") or []] == ["Being waited for", "Patience of the band as welcome"]
              and "smiled at me" in (late.get("pairs") or [{}, {}])[1]["kq"], str(late.get("pairs")))
        edits = rounds_mod.load_progress(book).get("edits") or []
        check("366: each passage's edit is kept in History with his request and the tool",
              len(edits) == 2 and all(e["request"] == "Bring in my October PETs" and e["by"] == "agent"
                                      and e["tool"] == "Claude Code" for e in edits), json.dumps(edits)[:400])
        code_, shown, err = run("board", "show", "Quill", "From Excel (Oct 2025)", "--timepoint", "T1")
        tree = [(p["label"], [c["text"] for c in p.get("statements") or p.get("cards") or []],
                 [(s["label"], [c["text"] for c in s.get("statements") or s.get("cards") or []])
                  for s in p.get("subs") or p.get("themes") or []]) for p in shown.get("pets") or shown.get("themes") or []] \
            if code_ == 0 else []
        want = [("The body learns the rope", [], [("Fear in the arms", ["Being lifted by the rope as a first fear"]),
                                                  ("Hands that remember", ["Calluses as proof of belonging"])]),
                ("Joining the band", [], [("Listening in", ["Listening as the way into the band",
                                                            "Counting out loud as a private scaffold"]),
                                          ("Being held by others", ["Patience of the band as welcome"])]),
                ("Bells that are not ours", ["Borrowing the village's bells"], [])]
        check("366: the board is as the table gives it, the duplicate placed once, the rest in Not placed",
              tree == want and sorted(c["text"] for c in shown.get("not_placed") or shown.get("unplaced") or [])
              == ["Being waited for", "Hidden tears after the first peal"], json.dumps(tree)[:900] if tree else (err or json.dumps(shown)[:600]))
        data = themes.load(book)
        board = next((b for b in themes.boards_of(data) if b.get("name") == "From Excel (Oct 2025)"), {})
        check("366: the board's note and mark say who made it, for his request, from which table",
              (board.get("made") or {}).get("request") == "Bring in my October PETs"
              and (board.get("made") or {}).get("tool") == "Claude Code" and "quill pets.xlsx, sheet T1 PETs" in board.get("note", "")
              and "Bring in my October PETs" in board.get("note", "") and done.get("name") == "From Excel (Oct 2025)",
              json.dumps({k: board.get(k) for k in ("made", "note")})[:600])

        # ── C. MCP: both tools listed, a board_import dry run at T2 through it
        srv = mcp_server.Server(str(folder), config=str(config))
        srv.receive(json.dumps({"jsonrpc": "2.0", "id": 0, "method": "initialize",
                                "params": {"protocolVersion": "2025-06-18", "clientInfo": {"name": "claude-code"}}}))
        tools = {t["name"]: t for t in srv.receive(json.dumps({"jsonrpc": "2.0", "id": 1, "method": "tools/list"}))["result"]["tools"]}
        check("366: the MCP server has board_import with a timepoint and gets_import with lpets, both writing with a dry run",
              "timepoint" in tools["board_import"]["inputSchema"]["properties"]
              and "unmatched" in tools["board_import"]["inputSchema"]["properties"]
              and "lpets" in tools["gets_import"]["inputSchema"]["properties"]
              and "dry_run" in tools["gets_import"]["inputSchema"]["properties"])
        got = srv.receive(json.dumps({"jsonrpc": "2.0", "id": 2, "method": "tools/call", "params": {
            "name": "board_import", "arguments": {"case": "Quill", "timepoint": "T2", "file": str(inputs / "t2 pets.csv"),
                                                  "dry_run": True, "request": "My T2 PETs"}}}))["result"]
        check("366: an MCP dry run matches a CSV table at T2", not got.get("isError") and '"exact": 2' in json.dumps(got),
              json.dumps(got)[:400])
        for n, name in ((2, "t2 pets.csv"), (3, "t3 pets.csv")):
            code_, _x, err = run("board", "import", "Quill", "--timepoint", f"T{n}", "--from", str(inputs / name),
                                 "--note", f"My T{n} PETs", "--tool", "Claude Code")
            check(f"366: a CSV table of T{n}'s PETs made into a board", code_ == 0, err[:300])

        # ── D. LPETs from a table: the dry run, then the board with its notes and the member proposed
        lpets = str(inputs / "quill lpets.xlsx")
        before = state()
        code_, ldry, err = run("gets", "import", "--lpets", "Quill", "--from", lpets, "--sheet", "LPETs", "--dry-run")
        got_l = {x["title"]: x for x in ldry.get("lpets", [])} if code_ == 0 else {}
        fear, kin = got_l.get("From fear to fluency", {}), got_l.get("The bells as kin", {})
        check("366: the LPETs dry run lists each LPET, one PET proposed by a quote at T1 with why, one LPET named "
              "unmatched, and writes nothing",
              code_ == 0 and state() == before and [m["pet"] for m in fear.get("members", [])] == ["The body learns the rope"]
              and fear["members"][0]["by"] == "quote" and fear["members"][0]["timepoint"] == "T1"
              and fear["members"][0]["statement"] == "Being lifted by the rope as a first fear"
              and not kin.get("members") and ldry.get("unmatched") == ["The bells as kin"]
              and fear.get("description") == "The body learning the rope until it needs no counting",
              err or json.dumps(ldry)[:600])
        code_r, _r, err_r = run("gets", "import", "--from", lpets, "--dry-run")
        check("366: gets import without --lpets is refused", code_r != 0 and "--lpets" in (err_r + str(_r)), err_r[:200])
        code_, lmade, err = run("gets", "import", "--lpets", "Quill", "--from", lpets, "--sheet", "LPETs",
                                "--note", "Bring in my LPETs", "--tool", "Claude Code")
        code_s, lshow, err_s = run("gets", "show", "--lpets", "Quill", "From Excel")
        themes_l = {t["label"]: t for t in lshow.get("themes", [])} if code_s == 0 else {}
        a, b = themes_l.get("From fear to fluency", {}), themes_l.get("The bells as kin", {})
        check("366: the LPETs board From Excel holds both LPETs, the one PET proposed in the first, the second empty",
              code_ == 0 and code_s == 0 and [c["text"] for c in a.get("cards", [])] == ["The body learns the rope"]
              and b and not b.get("cards") and a.get("description") == "The body learning the rope until it needs no counting",
              (err or err_s) or json.dumps(lshow)[:700])
        check("366: each LPET's note holds a paragraph for each timepoint, headed T1, T2 and T3",
              a.get("note", "").split("\n\n") == ['T1: At first the rope lifts her.\n"the rope pulled me up onto my toes"',
                                                  "T2: Counting falls away.", "T3: Hardly mentioned now."]
              and b.get("note", "").startswith("T1: A borrowed belonging."), json.dumps(a.get("note")))

        # ── E. a table with no statements column is refused in one line, nothing written
        (inputs / "bad.csv").write_text("PET,Notes\nA theme,some words\n", encoding="utf-8")
        before = state()
        code_b, _b, err_b = run("board", "import", "Quill", "--from", str(inputs / "bad.csv"), "--note", "x")
        check("366: a table with no column of statements is refused, nothing written",
              code_b != 0 and "no column of experiential statements" in (err_b + str(_b)) and state() == before, err_b[:300])
        # ── F. the matcher alone: a statement worded further off is the passage's nearest, rewritten, and a row with
        # no passage at its Location or with its quote is skipped whatever --unmatched says
        import table_import
        turns = [{"sheet": "S", "row": 2, "name": "Researcher", "seconds": 1, "time": "00:01", "text": "And then?",
                  "statements": []},
                 {"sheet": "S", "row": 3, "name": "Wren", "seconds": 10, "time": "00:10",
                  "text": "The tenor bell frightened me for a whole winter.", "statements": ["Fear of the tenor bell"]}]
        far = table_import.match_pets(
            [{"row": 2, "pet": "P", "sub": "", "statement": "A winter of fearing the tenor", "at": 10, "location": "0:10",
              "quote": ""},
             {"row": 3, "pet": "P", "sub": "", "statement": "Bells in dreams", "at": 300, "location": "5:00",
              "quote": "I dream of bells"}], turns, "Researcher", add=True)
        check("366: a row worded further off rewrites the passage's nearest statement, and one with no passage is skipped",
              far[0]["how"] == "rewritten" and table_import.CLOSE <= far[0]["ratio"] < table_import.FUZZY
              and far[0]["key"] == "S:3:0" and far[1]["how"] == "skipped" and far[1]["why"] == "nowhere",
              json.dumps([(m["how"], m["ratio"], m["why"]) for m in far]))

        # ── G. a Location holding two times: every time read, the statement found at any of them, the dry run naming it
        seps = ["0:02 and 0:30", "0:02\n0:30", "0:02, 0:30", "0:02 / 0:30", "0:02 & 0:30", "0:02;0:30"]
        read = [table_import.ats_seconds(x) for x in seps]
        check("366: a Location with two times is read as both, whatever separates them, and one with none stays unread",
              all(x == [2, 30] for x in read) and table_import.ats_seconds("somewhere") == []
              and table_import.ats_seconds("0:05") == [5], json.dumps(read))
        (inputs / "two times.csv").write_text(
            "PET,Sub-theme,Experiential statements,Location,Quote\n"
            'Passing it on,,Becoming the one who teaches others,"0:02\n0:30",which felt absurd and lovely\n'
            "Passing it on,,Rhythm settling into the body now,0:08 & 0:02,\n", encoding="utf-8")
        before = state()
        code_, two, err = run("board", "import", "Quill", "--timepoint", "T2", "--from", str(inputs / "two times.csv"),
                              "--dry-run")
        rows = {r["row"]: r for r in two.get("rows", [])} if code_ == 0 else {}
        code_t, said_two, _e = said("board", "import", "Quill", "--timepoint", "T2", "--from",
                                    str(inputs / "two times.csv"), "--dry-run")
        check("366: a row whose second time finds its statement is fuzzy by its Location, the dry run naming that time",
              code_ == 0 and state() == before and rows[2]["how"] == "fuzzy" and rows[2]["by"] == "location"
              and rows[2]["time"] == "00:30" and rows[3]["how"] == "fuzzy" and rows[3]["time"] == "00:08"
              and "on Quill" not in said_two and "at 00:30" in said_two, err or json.dumps(rows)[:600])
        two_turns = [{"sheet": "S", "row": 2, "name": "Wren", "seconds": 359, "time": "05:59", "text": "x",
                      "statements": ["The tenor frightened me"]},
                     {"sheet": "S", "row": 3, "name": "Wren", "seconds": 1095, "time": "18:15", "text": "y",
                      "statements": ["Bells in my dreams"]}]
        got = table_import.match_pets([{"row": 2, "pet": "P", "sub": "", "statement": "The tenor frightened me",
                                        "at": 1095, "ats": [1095, 359], "location": "18:15 and 05:59", "quote": ""}],
                                      two_turns, "Researcher", add=False)
        check("366: an exact statement is found at the second of two times", got[0]["how"] == "exact"
              and got[0]["time"] == "05:59", json.dumps(got[0]))
    finally:
        (server_mod.CONFIG_PATH, server_mod.ROOT_OVERRIDE, server_mod.STATE_PATH, server_mod.STATE_MEMORY) = kept
