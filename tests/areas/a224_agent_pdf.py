from __future__ import annotations

import json
import re
import shutil

from . import support
from .support import DEMO_QUESTION, check, skip
import idiograph_routes
import idiograph_find


def test_agent_pdf(scratch):
    print("\n224. A board's PDF for agents, a PETs board's and a GETs board's, with every tick the print views offer, "
          "beside the workbook as on 19 October or where --out names, and search by word forms, "
          "sleep finding slept, a phrase in quotation marks matched as typed (20 October)")
    import app_search
    import cli
    import gets as gets_mod
    import mcp_server
    import print_pdf
    import server as server_mod
    import themes as themes_mod

    # the fixture: the demo's three invented cases in a project of their own, agents allowed, Rowan's board
    # with a note of its own, and a GETs board of two GETs made through the command line
    pristine = support.DEMO_PRISTINE
    root = scratch / "a224-root"
    shutil.rmtree(root, ignore_errors=True)
    for name in ("Rowan", "Juno", "Mabel"):
        (root / name / "Working").mkdir(parents=True)
        shutil.copy2(pristine / f"{name} - EN & ES.xlsx", root / name / f"{name} - EN & ES.xlsx")
        for side in (pristine / "Working").glob(f"{name} - *"):
            shutil.copy2(side, root / name / "Working" / side.name)
    book = root / "Rowan" / "Rowan - EN & ES.xlsx"
    held = json.loads(themes_mod.themes_path(book).read_text(encoding="utf-8"))
    held["boards"][0]["note"] = "Walks at both ends of the day, read again after the second interview"
    themes_mod.themes_path(book).write_text(json.dumps(held, ensure_ascii=False), encoding="utf-8")
    (root / server_mod.PROJECT_FILE).write_text(json.dumps({
        "name": "Dogs, a printing project", "research_question": DEMO_QUESTION,
        "agents": {"allowed": True, "at": "2026-10-20T21:00:00+01:00"}}), encoding="utf-8")
    cfg = scratch / "a224-config.json"
    cfg.write_text(json.dumps({"projects": [{"root": str(root)}], "interviewer": "Adam", "corpus": "",
                               "gravity_reference": "", "corpus_exclude": []}), encoding="utf-8")
    out = scratch / "a224-out"
    shutil.rmtree(out, ignore_errors=True)
    out.mkdir()

    def run(*args):
        return cli.run(["--root", str(root), "--config", str(cfg), *args])

    def answer(*args):
        code, said, err = run(*args, "--json")
        return code, (support.plain(json.loads(said)) if said.strip() else {}), err

    def files(at):
        # the case's lock file aside, which every command that reads a case takes
        return {p.relative_to(at).as_posix(): p.read_bytes() for p in sorted(at.rglob("*"))
                if p.is_file() and not p.name.startswith(".")}

    # each PDF typeset by Typst and its words kept, squashed of their spaces and folded (typst5, 9 November 2026)
    sq = support.squashed
    printed: list[str] = []
    kept = (server_mod.CONFIG_PATH, server_mod.ROOT_OVERRIDE, server_mod.STATE_MEMORY)
    real_typeset, print_pdf.typeset_pdf = support.typeset_words(printed)
    try:
        case_files = files(root / "Rowan")

        # ── A. a PETs board: every tick off, then each on alone
        code, plain, err = answer("board", "export", "Rowan", "--pdf", "--out", str(out))
        base = printed[-1]
        board, version = __import__("themes_word").board_of(book)
        np_head = f"Not placed ({len(board['unplaced'])})"
        # the bin's heading says Set aside since 20 October (sidebar), the flag --binned still answering
        dc_head = f"{__import__('themes').BINNED_HEADING} ({len(board['discarded'])})"
        check("224: board export --pdf --out a folder writes the print view's page there, named as the print view "
              "names it, every tick off: no board note, no Not placed, no bin, the board named and letters for labels",
              code == 0 and plain["file"] == "Rowan - Board 1 - PETs.pdf" and (out / plain["file"]).read_bytes()[:5] == b"%PDF-"
              and plain["path"] == str(out.resolve() / plain["file"])
              and sq("Walks at both ends") not in base and sq(np_head) not in base and sq(dc_head) not in base
              and sq("Board 1") in base and plain["board_note"] is False, err or json.dumps(plain)[:300])
        ticks = {"--board-note": "Walks at both ends of the day", "--not-placed": np_head, "--binned": dc_head}
        on = {}
        for flag, words in ticks.items():
            c, _, e = answer("board", "export", "Rowan", "--pdf", "--out", str(out), flag)
            on[flag] = (c, sq(words) in printed[-1])
        check("224: --board-note, --not-placed and --binned each put their part in the PDF's text",
              all(c == 0 and found for c, found in on.values()), str(on))
        c1, sent, _ = answer("board", "export", "Rowan", "--pdf", "--out", str(out), "--for-sending")
        c2, numbered, _ = answer("board", "export", "Rowan", "--pdf", "--out", str(out), "--labels", "numbers")
        check("224: --for-sending names the PDF by the case alone with no board on its page, and --labels numbers "
              "labels the PETs PET 1 in place of A",
              c1 == c2 == 0 and sent["file"] == "Rowan.pdf" and sq("Board 1") not in printed[-2]
              and sq("PET 1") in printed[-1] and sq("PET 1") not in base, json.dumps(sent)[:200])
        check("224: none of it wrote into the participant's folder, which --out did not name",
              files(root / "Rowan") == case_files and len(list(out.glob("*.pdf"))) == 6)

        # a file named, the dry run, and the refusals
        named = out / "for supervision.pdf"
        c3, as_named, _ = answer("board", "export", "Rowan", "--pdf", "--out", str(named))
        before, count = files(out), len(printed)
        c4, dry, _ = answer("board", "export", "Rowan", "--pdf", "--out", str(named), "--dry-run", "--board-note")
        c5, dry_new, _ = answer("board", "export", "Rowan", "--pdf", "--out", str(out / "never.pdf"), "--dry-run")
        check("224: --out a file ending .pdf writes that name, and a dry run prints and writes nothing, saying the "
              "name it would take, dated when the name is taken",
              c3 == c4 == c5 == 0 and as_named["file"] == "for supervision.pdf" and named.is_file()
              and dry["dry_run"] is True and dry["dated"] is True and dry["file"].startswith("for supervision (")
              and dry_new["file"] == "never.pdf" and not (out / "never.pdf").exists()
              and files(out) == before and len(printed) == count, json.dumps(dry)[:300])
        c7, s7, e7 = run("board", "export", "Rowan", "--pdf", "--out", str(scratch / "a224-nowhere" / "x.pdf"))
        c8, s8, e8 = run("board", "export", "Rowan", "--word", "--out", str(out))
        check("224: with a folder not there, or --out with --word, nothing is written and it says why",
              c7 != 0 and "not there" in s7 + e7 and c8 != 0 and "--pdf" in s8 + e8
              and files(root / "Rowan") == case_files and len(printed) == count, s7 + e7 + s8 + e8)
        c9, beside, _ = answer("board", "export", "Rowan", "--pdf", "--board-note")
        check("224: with no --out the PDF goes beside the workbook, as on 19 October, its ticks still taken",
              c9 == 0 and beside["file"] == "Rowan - Board 1 - PETs.pdf" and (root / "Rowan" / beside["file"]).is_file()
              and "beside the workbook" in beside["said"] and sq("Walks at both ends") in printed[-1],
              json.dumps(beside)[:300])
        (root / "Rowan" / beside["file"]).unlink()

        # ── B. a GETs board, made first through the command line
        books = sorted(idiograph_routes.gets_books(root), key=lambda b: gets_mod.case_order(b["case"]))
        data_g, _, _, _ = gets_mod.assemble(root, books, themes_mod.now_iso())
        gets_mod.write(root, gets_mod._file(data_g, themes_mod.now_iso()))
        cards_g = list(data_g["boards"][0]["cards"])
        rowan = [k for k in cards_g if k.startswith("Rowan/")]
        mabel = [k for k in cards_g if k.startswith("Mabel/")]
        ops = scratch / "a224-gops.json"
        ops.write_text(json.dumps({"operations": [
            {"op": "make", "ref": "a", "title": "Walks at the edges of the day", "inside": None,
             "members": [rowan[0], mabel[0]]},
            {"op": "make", "ref": "b", "title": "Letting a dog go", "inside": None, "members": [rowan[1], mabel[1]]}]}),
            encoding="utf-8")
        code, _, err = answer("gets", "apply", "b1", "--ops", str(ops), "--note", "Two GETs")
        gets_before = gets_mod.gets_path(root).read_bytes()
        gout = scratch / "a224-gets"
        shutil.rmtree(gout, ignore_errors=True)
        gout.mkdir()
        g1, table, e1 = answer("gets", "export", "--pdf", "--out", str(gout))
        t_text = printed[-1]
        g2, trail, _ = answer("gets", "export", "--out", str(gout), "--what", "trail")
        r_text = printed[-1]
        g3, full, _ = answer("gets", "export", "--out", str(gout), "--what", "all", "--selected", "--notes")
        a_text = printed[-1]
        check("224: gets export writes the GET table by default, every item and no participant notes, the trail with "
              "--what trail, and the full set with --what all, --selected keeping the key quotes alone and --notes "
              "bringing the participant notes in, each named as the print view names it",
              code == g1 == g2 == g3 == 0 and table["file"] == "Dogs, a printing project - Board 1 - GET table.pdf"
              and sq("Walks at the edges of the day") in t_text and sq("participant notes") not in t_text
              and trail["file"].endswith("Audit trail.pdf") and sq("Transcript passage") in r_text
              and full["file"].endswith("GETs.pdf") and sq("Contents") in a_text
              and (table["detail"], full["detail"], full["notes"]) == ("full", "selected", True),
              e1 or json.dumps([table, trail, full])[:400])
        gid = next(t["id"] for t in answer("gets", "show")[1]["themes"] if t["label"] == "Letting a dog go")
        g4, one, _ = answer("gets", "export", "--out", str(gout), "--get", gid, "--for-sending")
        o_text = printed[-1]
        check("224: --get prints that GET's trail alone, and --for-sending leaves the board's name off the page and "
              "the file's name",
              g4 == 0 and one["what"] == "trail" and one["file"] == f"Dogs, a printing project - Audit trail - {gid}.pdf"
              and sq("Letting a dog go") in o_text and sq("Walks at the edges of the day") not in o_text
              and sq("Board 1") not in o_text, json.dumps(one)[:300])
        before, count = files(gout), len(printed)
        g5, gdry, _ = answer("gets", "export", "--out", str(gout), "--dry-run")
        g7, s7, e7 = run("gets", "export", "--out", str(gout), "--get", "G99")
        check("224: a GETs dry run prints and writes nothing, with a GET not on the board nothing is written, and "
              "the GETs file is only read",
              g5 == 0 and gdry["dry_run"] is True and gdry["dated"] is True and files(gout) == before
              and len(printed) == count and g7 != 0
              and gets_mod.gets_path(root).read_bytes() == gets_before, s7 + e7)
        g6, at_root, e6 = answer("gets", "export")
        check("224: with no --out a GETs board's PDF goes at the project's root, beside the GETs file",
              g6 == 0 and (root / at_root.get("file", "none")).is_file()
              and gets_mod.gets_path(root).parent.resolve() == root.resolve(), e6 or json.dumps(at_root)[:300])
        (root / at_root["file"]).unlink()

        # the same through MCP, gets_export and board_export's new arguments
        srv = mcp_server.Server(str(root), config=str(cfg))
        srv.receive(json.dumps({"jsonrpc": "2.0", "id": 1, "method": "initialize",
                                "params": {"protocolVersion": "2025-06-18", "clientInfo": {"name": "claude-code"}}}))
        call = lambda name, args: srv.receive(json.dumps({"jsonrpc": "2.0", "id": 2, "method": "tools/call",
                                                          "params": {"name": name, "arguments": args}}))["result"]
        m1 = call("gets_export", {"out": str(gout), "what": "all", "notes": True})
        m1_text = printed[-1]
        m2 = call("board_export", {"case": "Rowan", "format": "pdf", "out": str(out), "board_note": True})
        m2_text = printed[-1]
        m3 = call("board_export", {"case": "Rowan", "format": "pdf"})
        tool = mcp_server.BY_NAME["gets_export"]
        check("224: through MCP gets_export and board_export's out and board_note do as the command line does, "
              "a PDF with no out beside the workbook, gets_export marked as writing a file and taking dry_run",
              not m1["isError"] and support.plain(m1["structuredContent"]).get("notes") is True and not m2["isError"]
              and sq("Walks at both ends of the day") in m2_text and not m3["isError"]
              and (root / "Rowan" / support.plain(m3["structuredContent"])["file"]).is_file()
              and tool["annotations"]["readOnlyHint"] is False and "dry_run" in tool["inputSchema"]["properties"]
              and "request" not in tool["inputSchema"]["properties"], json.dumps([m1, m3])[:400])
    finally:
        print_pdf.typeset_pdf = real_typeset
        server_mod.CONFIG_PATH, server_mod.ROOT_OVERRIDE, server_mod.STATE_MEMORY = kept

    # ── C. search by word forms, the app's finder and the agents' search alike
    forms = {w: set(app_search.term(w).forms) for w in ("sleep", "walk", "walked", "slept", "tried", "running", "man")}
    check("224: the word forms: sleep gives sleeps, sleeping and slept, walk walked and walking, walked walk, "
          "slept sleep, tried try, running run, man men",
          {"sleeps", "sleeping", "slept"} <= forms["sleep"] and {"walked", "walking", "walks"} <= forms["walk"]
          and {"walk", "walking"} <= forms["walked"] and "sleep" in forms["slept"] and "try" in forms["tried"]
          and {"run", "ran"} <= forms["running"] and "men" in forms["man"], str(forms))
    words = app_search.words_of("man")
    check("224: a form found only as a whole word, so man finds men and never moment, the word typed still anywhere",
          app_search.matches("two men walked", words) and not app_search.matches("a moment", words)
          and app_search.matches("a human", words), "")
    _, quoted, phrase = app_search.query('"sleep"')
    check("224: a phrase in quotation marks has no other form",
          phrase == "sleep" and all(not w.forms for w in quoted) and app_search.term("sleep", widen=False).forms == ())
    kept = (server_mod.CONFIG_PATH, server_mod.ROOT_OVERRIDE, server_mod.STATE_MEMORY)
    try:
        code, found, err = answer("search", "sleep", "--kinds", "passages", "--limit", "200")
        texts = [r["snippet"] for r in found.get("results", [])]
        code2, walked, _ = answer("search", "walked", "--kinds", "passages", "--limit", "200")
        wtexts = [r["snippet"] for r in walked.get("results", [])]
        code3, exact, _ = answer("search", '"sleep"', "--kinds", "passages", "--limit", "200")
        etexts = [r["snippet"] for r in exact.get("results", [])]
        check("224: search for sleep finds the passage that says slept, marked, walked finds walk and walking, and "
              "\"sleep\" in quotation marks finds only sleep as typed",
              code == code2 == code3 == 0 and any("**slept**" in t for t in texts)
              and any("**walking**" in t for t in wtexts) and any("**walk**" in t.lower() for t in wtexts)
              and etexts and all("sleep" in t.lower() for t in etexts) and not any("**slept**" in t for t in etexts)
              and len(etexts) < len(texts), err or str(texts)[:300])
        cases = [{"case": b["case"], "workbook": b["workbook"], "path": ""} for b in
                 sorted(idiograph_routes.gets_books(root), key=lambda b: gets_mod.case_order(b["case"]))]
        app = idiograph_find.search("sleep", "project", cases, {"name": "Dogs"}, None)
        app_exact = idiograph_find.search('"sleep"', "project", cases, {"name": "Dogs"}, None)
        check("224: the app's Search finds the same forms, gives them to the page to mark, and takes a quoted phrase "
              "as typed",
              any("slept" in r["text"] for r in app["results"]) and "slept" in app["forms"]
              and not any("slept" in r["text"] and "sleep" not in r["text"].lower().replace("slept", "")
                          for r in app_exact["results"]) and app_exact["forms"] == []
              and app_exact["total"] < app["total"], str(app["forms"])[:200])
    finally:
        server_mod.CONFIG_PATH, server_mod.ROOT_OVERRIDE, server_mod.STATE_MEMORY = kept
