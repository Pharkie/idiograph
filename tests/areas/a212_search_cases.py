from __future__ import annotations

import hashlib
import json
import shutil
import unicodedata

from .support import DEMO_SHEET, check, demo_copy, demo_sheet
from . import support
import idiograph_cli


def test_search_cases(scratch):
    print("\n212. Search across cases for agents, 20 October: the app's Search as the command line's search and the MCP "
          "tool search, over a project, a case or one of its boards, narrowed by kind, a page at a time with a cursor, each "
          "hit with its case, place, speaker, a snippet with its words marked and the tool that opens it, read-only")
    import app_search
    import cli
    import mcp_server
    import server as server_mod
    import themes as themes_mod
    import workbook as wb_mod

    # ── an invented project: two potters, each case a copy of the demo's invented interview
    base = scratch / "search-212"
    shutil.rmtree(base, ignore_errors=True)
    root = base / "Kiln study"
    books = {name: demo_copy(root, name, f"{name} - EN & ES.xlsx") for name in ("Hollis", "Quill")}
    project_file = root / server_mod.PROJECT_FILE
    allowed = {"name": "Kiln study", "research_question": "How do potters experience the night of a firing?",
               "agents": {"allowed": True, "at": "2026-10-20T10:00:00+01:00"}}
    project_file.write_text(json.dumps(allowed), encoding="utf-8")
    config = base / "config.json"
    config.write_text(json.dumps({"root": str(root), "interviewer": "Researcher", "corpus": "", "gravity_reference": "",
                                  "corpus_exclude": []}), encoding="utf-8")
    sheet, her, _him = demo_sheet(books["Hollis"])
    empty = [r["row"] for r in sheet["rows"] if r["name"] == her and not r["es"].strip()]
    wb_mod.save_turn(books["Hollis"], DEMO_SHEET, empty[0], "Lying wakeful before the first firing",
                     "Wakeful, the kiln on her mind", "")
    wb_mod.save_turn(books["Quill"], DEMO_SHEET, empty[1], "Wakeful nights at the kiln", "", "")
    cards = themes_mod.read_cards(books["Hollis"])["cards"]
    planted = next(c["key"] for c in cards if c["text"].startswith("Lying wakeful"))
    one = themes_mod.blank_version(cards)
    one.update(id="v1", name="Board 1", groups=[
        {"id": "g1", "label": "Wakeful before the kiln", "members": [planted], "x": 0, "y": 0}])
    two = themes_mod.blank_version(cards)
    two.update(id="v2", name="Board 2", groups=[
        {"id": "g1", "label": "Nights kept wakeful", "members": [], "x": 0, "y": 0},
        {"id": "g2", "label": "The firing itself", "members": [planted], "x": 3000, "y": 0}])
    themes_mod.write(books["Hollis"], {"schema": 2, "case": "Hollis", "workbook": books["Hollis"].name, "current": "v1",
                                       "chosen": "v1", "boards": [one, two]})

    def files() -> dict:
        return {str(p): hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(root.rglob("*")) if p.is_file()}

    def answer(*args):
        code, out, err = cli.run(["--root", str(root), "--config", str(config), "search", *args, "--json"])
        return code, (support.plain(json.loads(out)) if out.strip() else {}), err

    def every(*args, limit=2) -> list[dict]:
        """Every hit of a search, page by page through its cursor."""
        out, more, pages = [], None, 0
        while pages < 100:
            code, got, _err = answer(*args, "--limit", str(limit), *(["--more", more] if more else []))
            if code:
                break
            out += got["results"]
            more, pages = got.get("more"), pages + 1
            if not more:
                break
        return out

    before = files()
    kept = (server_mod.CONFIG_PATH, server_mod.ROOT_OVERRIDE, server_mod.STATE_MEMORY)
    try:
        # ── A. across the cases: hits in both, each naming its case, place, speaker and the tool that opens it
        code, got, err = answer("wakeful")
        kinds = {(r["case"], r["kind"]) for r in got.get("results", [])}
        check("212: one search finds the words in both cases, the statements, the exploratory note and the PETs, with "
              "the count by case",
              code == 0 and {("Hollis", "statement"), ("Quill", "statement"), ("Hollis", "enote"), ("Hollis", "pet")} <= kinds
              and {c["case"]: c["count"] for c in got["cases"]}.get("Quill") == 1 and got["total"] == len(got["results"]),
              err or str(kinds))
        stated = next((r for r in got.get("results", []) if r["kind"] == "statement" and r["case"] == "Hollis"), {})
        check("212: a statement's hit gives its sheet, row, time, speaker, short id and key, where the Current board "
              "places it, and turn_show to open its passage",
              stated.get("sheet") == DEMO_SHEET and stated.get("row") == empty[0] and stated.get("speaker") == her
              and stated.get("key") == planted and stated.get("id", "").startswith("S")
              and stated.get("placed", {}).get("board") == "v1" and stated["placed"].get("label") == "g1"
              and stated["placed"].get("export_label")
              and stated.get("open", {}).get("tool") == "turn_show"
              and stated["open"]["arguments"] == {"case": "Hollis", "sheet": DEMO_SHEET, "row": empty[0]}
              and stated["open"]["command"] == f"idiograph turn show Hollis {DEMO_SHEET} {empty[0]}", str(stated))
        pet = next((r for r in got.get("results", []) if r["kind"] == "pet"), {})
        check("212: a PET's hit names its board and label and opens with board_show",
              pet.get("board") in ("v1", "v2") and pet.get("label") == "g1"
              and pet.get("open", {}).get("tool") == "board_show", str(pet))
        check("212: every snippet marks each word found between two asterisks, its case as written",
              all("**" in r["snippet"] and "wakeful" in r["snippet"].lower() for r in got.get("results", []))
              and app_search.marked("Wakeful, then WAKEFUL", ["wakeful"]) == "**Wakeful**, then **WAKEFUL**"
              and app_search.marked(unicodedata.normalize("NFD", "A café at dawn"), ["cafe"]).count("**") == 2
              and app_search.marked("sleepless", ["sleep", "less"]) == "**sleepless**", str([r["snippet"] for r in got.get("results", [])]))

        # ── B. the scope and the kinds
        _c, in_case, _e = answer("wakeful", "--case", "Quill")
        _c, on_two, _e = answer("wakeful", "--case", "Hollis", "--board", "Board 2")
        _c, in_hollis, _e = answer("wakeful", "--case", "Hollis")
        pets = lambda a: sorted(r["board"] for r in a.get("results", []) if r["kind"] == "pet")
        two_stated = next((r for r in on_two.get("results", []) if r["kind"] == "statement"), {})
        check("212: a case alone, and one of its boards alone, the statement placed as that board places it",
              {r["case"] for r in in_case.get("results", [])} == {"Quill"} and pets(in_hollis) == ["v1", "v2"]
              and pets(on_two) == ["v2"] and two_stated.get("placed", {}).get("label") == "g2" and on_two["scope"] == "board",
              str((pets(in_hollis), pets(on_two), two_stated.get("placed"))))
        _c, only, _e = answer("wakeful", "--kinds", "statements")
        _c, notes, _e = answer("wakeful", "--kinds", "notes,pets")
        check("212: kinds narrow the hits, by the agent's groups, the counts by kind still every kind",
              {r["kind"] for r in only.get("results", [])} == {"statement"} and only["total"] == 2
              and only["counts"].get("pet") == 2
              and {r["kind"] for r in notes.get("results", [])} == {"enote", "pet"}, str((only.get("counts"), notes.get("total"))))
        _c, phrase, _e = answer('"wakeful nights"')
        _c, reversed_, _e = answer('"nights wakeful"')
        check("212: a phrase in quotation marks finds its words together and in their order alone",
              [r["case"] for r in phrase.get("results", [])] == ["Quill"] and phrase["phrase"] is True
              and reversed_.get("total") == 0, str((phrase.get("total"), reversed_.get("total"))))

        # ── C. the cursor
        code, first, _e = answer("wakeful", "--limit", "2")
        paged = every("wakeful", limit=2)
        check("212: a page holds limit hits and more is the cursor to the next, the pages together every hit once, the last "
              "with no more",
              code == 0 and len(first["results"]) == 2 and first["more"] == "2" and first["total"] == got["total"]
              and [(r["case"], r["kind"], r["where"]) for r in paged]
              == [(r["case"], r["kind"], r["where"]) for r in got["results"]] and got["more"] is None, str(len(paged)))

        # ── D. the same hits as the app's Search for the same words
        server_mod.ROOT_OVERRIDE = str(root)
        server_mod.STATE_MEMORY = {"recent": []}
        app = server_mod.api_search({"q": "wakeful", "scope": "project", "root": str(root)})
        app_case = server_mod.api_search({"q": "wakeful", "scope": "case", "path": str(books["Hollis"])})
        server_mod.CONFIG_PATH, server_mod.ROOT_OVERRIDE, server_mod.STATE_MEMORY = kept
        plain = lambda rows: [(r["kind"], r["case"], r["where"], r.get("text", r.get("snippet", "")).replace("**", ""))
                              for r in rows]
        check("212: the hits are the app's Search's for the same words, project and case alike, in its order",
              plain(app["results"]) == plain(got["results"]) and plain(app_case["results"]) == plain(in_hollis["results"])
              and app["counts"] == {**{k: 0 for k in app["counts"]}, **got["counts"]},
              str((len(app["results"]), len(got["results"]))))

        # ── E. the MCP tool: the command line's answer
        srv = mcp_server.Server(root=str(root), config=str(config))
        told = srv.call(mcp_server.BY_NAME["search"], {"words": "wakeful", "kinds": ["statements"], "limit": 1})
        nxt = srv.call(mcp_server.BY_NAME["search"], {"words": "wakeful", "kinds": ["statements"], "limit": 1,
                                                      "more": support.plain(told["structuredContent"]).get("more") or ""})
        tool = mcp_server.BY_NAME["search"]
        check("212: the MCP tool search answers as the command line does, a page and its cursor, and only reads",
              not told["isError"] and [r["key"] for r in support.plain(told["structuredContent"])["results"] + support.plain(nxt["structuredContent"])["results"]]
              == [r["key"] for r in only["results"]] and support.plain(nxt["structuredContent"])["more"] is None
              and tool["annotations"]["readOnlyHint"] is True and "dry_run" not in tool["inputSchema"]["properties"]
              and "search" in mcp_server.CORE and len(mcp_server.CORE) <= mcp_server.CORE_LIMIT, str(told)[:300])

        # ── F. the refusals
        code_words, _o, err_words = cli.run(["--root", str(root), "--config", str(config), "search", '""'])
        code_board, _o, err_board = cli.run(["--root", str(root), "--config", str(config), "search", "kiln", "--board", "v1"])
        code_kind, _o, err_kind = cli.run(["--root", str(root), "--config", str(config), "search", "kiln", "--kinds", "pots"])
        code_more, _o, err_more = cli.run(["--root", str(root), "--config", str(config), "search", "kiln", "--more", "x"])
        code_limit, _o, _e = cli.run(["--root", str(root), "--config", str(config), "search", "kiln", "--limit", "0"])
        check("212: no words, a board with no case, a kind there is none of, a cursor no search gave and a page of none "
              "are each refused in one line",
              (code_words, code_board, code_kind, code_more, code_limit) == (1, 1, 1, 1, 1)
              and cli.NO_WORDS in err_words and idiograph_cli.BOARD_NEEDS_CASE in err_board and "No kind called pots" in err_kind
              and "not a cursor" in err_more, err_words + err_board + err_kind + err_more)
        project_file.write_text(json.dumps(dict(allowed, agents={"allowed": False})), encoding="utf-8")
        shut_code, _o, shut_err = cli.run(["--root", str(root), "--config", str(config), "search", "wakeful"])
        shut_tool = srv.call(mcp_server.BY_NAME["search"], {"words": "wakeful"})
        outside = base / "Elsewhere"
        outside.mkdir()
        out_code, _o, _out_err = cli.run(["--root", str(outside), "--config", str(config), "search", "wakeful"])
        project_file.write_text(json.dumps(allowed), encoding="utf-8")
        check("212: with the agents tick off, or on a folder that is no project of his, the search is refused and reads nothing",
              shut_code == 1 and idiograph_cli.PRIVATE in shut_err and shut_tool["isError"] and out_code == 1, shut_err)
        check("212: every search only read: no file of the project changed", files() == before)

        # ── G. a Sift screening by its folder, its records found and opened with sift_show
        screen = base / "Glaze review"
        screen.mkdir()
        (screen / "screening.csv").write_text("rec_id,title,authors,year,abstract\nR001,Wakeful glazers,Okafor,2020,"
                                              "Potters described wakeful nights.\nR002,Clay bodies,Ng,2021,Nothing of it.\n",
                                              encoding="utf-8")
        code, sifted, err = cli.run(["--app", "sift", "search", "wakeful", "--folder", str(screen), "--json", "--config", str(config)])
        sifted = support.plain(json.loads(sifted)) if sifted.strip() else {}
        not_ours = cli.run(["--config", str(config), "search", "wakeful", "--folder", str(screen), "--json"])
        check("212: with folder a Sift screening's records are searched by Sift's search, each hit opening with sift_show, "
              "and Idiograph's refuses the folder by name since the cutover",
              code == 0 and sifted["scope"] == "sift" and [r["rec_id"] for r in sifted["results"]] == ["R001", "R001"]
              and all(r["open"]["tool"] == "sift_show" for r in sifted["results"]) and not_ours[0] == 1
              and support.plain(json.loads(not_ours[1]))["error"].startswith("That folder is Sift's, not Idiograph's."), err or str(sifted)[:300])
    finally:
        server_mod.CONFIG_PATH, server_mod.ROOT_OVERRIDE, server_mod.STATE_MEMORY = kept
