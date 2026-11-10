from __future__ import annotations

import json
import re
import shutil

import openpyxl

import workbook as wb_mod

from . import support
from .support import DEMO_QUESTION, DEMO_SHEET, check, skip
import idiograph_cli


def test_quotes_safe(scratch):
    print("\n96. Quote writes lose nothing: a pick keeps its quote through inverted commas gained or lost, a turn "
          "write keeps the turn's lone quotes and can write one, and one rule for how many picks a label takes")
    import subprocess
    import cli
    import locks
    import mcp_server
    import server as server_mod
    import themes as themes_mod
    import themes_ai

    th_js = support.text("apps/idiograph/static/themes.js")
    fn = lambda src, name: src.split(f"function {name}(", 1)[1].split("\n}", 1)[0] if f"function {name}(" in src else ""
    node = shutil.which("node")

    # ── A. the matching, on an invented board of one statement and its pick
    def board(held: str) -> dict:
        return {"id": "v1", "name": "Board 1", "cards": {"S:3:0": {"x": 0, "y": 0, "text": "An invented statement"}},
                "groups": [{"id": "g1", "label": "An invented label", "members": ["S:3:0"], "x": 0, "y": 0}],
                "discarded": [], "picks": {"g1": ["S:3:0"]}, "quoted": {"S:3:0": held}}

    card = [{"key": "S:3:0", "sheet": "S", "row": 3, "line": 0, "text": "An invented statement"}]

    def row(*texts) -> dict:
        return {"S:3": {"sheet": "S", "row": 3, "seconds": None, "time": "",
                        "quotes": [{"key": f"S:3:{i}", "text": t} for i, t in enumerate(texts) if t]}}

    bare = "the words she said"
    marks = ['"the words she said"', "'the words she said'", "“the words she said”",
             "‘the words she said’", " “ the  words she said ” "]
    gained = [themes_mod.follow(board(bare), card, row(m)) for m in marks]
    check("96: a pick on a bare quote is kept when the quote gains inverted commas, straight or curly, single or double",
          all(v["picks"] == {"g1": ["S:3:0"]} for v in gained), str([v["picks"] for v in gained]))
    check("96: and the words kept for it take the quote as it reads now, inverted commas and all",
          [v["quoted"]["S:3:0"] for v in gained] == marks, str([v.get("quoted") for v in gained]))
    lost = [themes_mod.follow(board(m), card, row(bare)) for m in marks]
    check("96: a pick on a quote in inverted commas is kept when it loses them, its words taken bare",
          all(v["picks"] == {"g1": ["S:3:0"]} and v["quoted"]["S:3:0"] == bare for v in lost),
          str([v["picks"] for v in lost]))
    gone_moves, moved_moves = {}, {}
    reworded = themes_mod.follow(board(bare), card, row('"the words he said"'), gone_moves)
    moved = themes_mod.follow(board(bare), card, row('"other words"', "“the words she said”"), moved_moves)
    check("96: a real change of words still drops the pick, and words moved along the row still move it",
          reworded["picks"] == {} and gone_moves == {("g1", "S:3:0"): None}
          and moved["picks"] == {"g1": ["S:3:1"]} and moved_moves == {("g1", "S:3:0"): "S:3:1"},
          f"{reworded['picks']} {moved['picks']}")
    check("96: only the inverted commas round the whole quote are set aside, and the spacing inside them",
          themes_mod.quote_words(" “ two  words ” ") == "two words" and themes_mod.quote_words("'\"nested\"'") == "nested"
          and themes_mod.quote_words('"one side') == '"one side' and themes_mod.quote_words("it's hers") == "it's hers"
          and themes_mod.quote_words('"') == '"' and themes_mod.words('"kept"') == '"kept"')

    # ── B. an invented case: Juno's pristine copy, two turns given statements and quotes by hand
    pristine = support.DEMO_PRISTINE
    root = scratch / "quotesafe-root"
    shutil.rmtree(root, ignore_errors=True)
    (root / "Juno" / "Working").mkdir(parents=True)
    book = root / "Juno" / "Juno - EN & ES.xlsx"
    shutil.copy2(pristine / "Juno - EN & ES.xlsx", book)
    for side in (pristine / "Working").glob("Juno - *"):
        shutil.copy2(side, root / "Juno" / "Working" / side.name)
    (root / server_mod.PROJECT_FILE).write_text(json.dumps({
        "name": "Dogs, a quotes project", "research_question": DEMO_QUESTION,
        "agents": {"allowed": True, "at": "2026-10-07T12:00:00+01:00"}}), encoding="utf-8")
    config_file = scratch / "quotesafe-config.json"
    config_file.write_text(json.dumps({"root": str(root), "interviewer": "Adam"}), encoding="utf-8")
    texts = {r["row"]: r["text"] for r in wb_mod.read_case(book)["sheets"][0]["rows"]}
    piece = lambda r, a, b: " ".join(texts[r].split()[a:b]).strip(" ,.")
    qa, qb, lone, other = piece(15, 0, 5), piece(15, 6, 10), piece(15, 12, 16), piece(15, 17, 21)
    t19 = [piece(19, 0, 4), piece(19, 5, 9), piece(19, 10, 14)]
    first, second = "An invented first", "An invented second"
    k15, k19 = f"{DEMO_SHEET}:15:0", [f"{DEMO_SHEET}:19:{i}" for i in range(3)]
    wb = openpyxl.load_workbook(book, rich_text=True)
    ws = wb[DEMO_SHEET]
    cols = wb_mod.detect_columns(ws)
    # a bare quote for the first statement, none for the second, and a bare lone quote after them
    ws.cell(15, cols["es"]).value = f"{first}\n\n{second}"
    ws.cell(15, cols["kq"]).value = f"{qa}\n\n(no quote)\n\n{lone}"
    ws.cell(19, cols["es"]).value = "Invented one\n\nInvented two\n\nInvented three"
    ws.cell(19, cols["kq"]).value = "\n\n".join(t19)
    wb.save(book)
    wb.close()

    def cells(r: int) -> tuple:
        held = openpyxl.load_workbook(book, read_only=True)
        try:
            got = next(held[DEMO_SHEET].iter_rows(min_row=r, max_row=r, values_only=True))
            return got[cols["es"] - 1], got[cols["kq"] - 1]
        finally:
            held.close()

    def run(*args) -> tuple[int, str, str]:
        return cli.run(["--root", str(root), "--config", str(config_file), *args])

    def answer(*args) -> tuple[int, dict, str]:
        code, out, err = run(*args, "--json")
        return code, (support.plain(json.loads(out)) if out.strip() else {}), err

    def spec(name: str, value) -> str:
        path = scratch / f"quotesafe-{name}.json"
        path.write_text(json.dumps(value), encoding="utf-8")
        return str(path)

    def write(name: str, value, *more) -> tuple[int, dict, str]:
        return answer("turn", "write", "Juno", DEMO_SHEET, "15", "--from", spec(name, value), "--note", name, *more)

    kept = (server_mod.CONFIG_PATH, server_mod.ROOT_OVERRIDE, server_mod.STATE_MEMORY, locks.WAIT)
    try:
        server_mod.CONFIG_PATH = config_file
        server_mod.ROOT_OVERRIDE = str(root)
        server_mod.STATE_MEMORY = {"recent": []}
        code, _, err = run("board", "new", "Juno", "--from", spec("board", {"pets": [
            {"title": "An invented walk", "members": [k15, f"{DEMO_SHEET}:15:1"], "picks": [k15]},
            {"title": "Three invented quotes", "members": k19, "picks": k19}]}), "--note", "An invented board")
        made = themes_mod.current_version(themes_mod.load(book))
        walk = next((g["id"] for g in made["groups"] if g["label"] == "An invented walk"), None)
        three = next((g["id"] for g in made["groups"] if g["label"] == "Three invented quotes"), None)
        check("96: board new keeps every pick it is given, three on one label, and the bare quote's words beside them",
              code == 0 and made["picks"].get(walk) == [k15] and made["picks"].get(three) == k19
              and (made.get("quoted") or {}).get(k15) == qa, err.strip()[:200])

        # ── C. a write that wraps the quote keeps the pick and the lone quote
        wrap = {"pairs": [{"statement": first, "quote": qa}, {"statement": second, "quote": ""}]}
        before = book.read_bytes()
        code, dry, err = write("wrap", wrap, "--dry-run")
        _, text, _ = run("turn", "write", "Juno", DEMO_SHEET, "15", "--from", spec("wrap", wrap), "--note", "wrap",
                         "--dry-run")
        check("96: the dry run of a write that wraps a quote lists the lone quote it keeps and no pick moved or dropped",
              code == 0 and dry.get("lone_kept") == [lone] and dry.get("picks") == [] and book.read_bytes() == before
              and f'It would keep the turn\'s 1 lone quote, with no statement of its own, as it stands: "{lone}".' in text
              and "the pick" not in text, text)
        code, text, err = run("turn", "write", "Juno", DEMO_SHEET, "15", "--from", spec("wrap", wrap),
                              "--note", "Wrap the quote", "--tool", "Claude Code")
        shown = themes_mod.state(book, "Juno")
        check("96: the write puts the named quote in inverted commas and keeps the lone quote in its place, as it stands",
              code == 0 and cells(15) == (f"{first}\n\n{second}", f'"{qa}"\n\n(no quote)\n\n{lone}')
              and "It kept the turn's 1 lone quote" in text, f"{cells(15)} {err.strip()[:200]}")
        check("96: the pick on the bare quote is still there as the app reads the case, and the lone quote with it",
              shown["picks"].get(walk) == [k15]
              and [q["text"] for q in shown["quotes"][f"{DEMO_SHEET}:15"]["quotes"]] == [f'"{qa}"', lone],
              str(shown["picks"]))
        stored = themes_mod.current_version(themes_mod.load(book))
        themes_mod.save(book, stored, "Juno")
        saved = themes_mod.current_version(themes_mod.load(book))
        check("96: the server's save keeps the pick and writes the quoted words afresh, inverted commas and all",
              stored["quoted"][k15] == qa and saved["picks"].get(walk) == [k15] and saved["quoted"][k15] == f'"{qa}"'
              and saved["picks"].get(three) == k19, str(saved.get("quoted")))

        # ── D. a lone quote written, moved, and kept by every write that does not name it
        code, data, err = write("add", {"pairs": wrap["pairs"] + [{"statement": "", "quote": qb}]})
        check("96: a pair with a quote and no statement writes a lone quote, after the one the turn kept",
              code == 0 and cells(15)[1] == f'"{qa}"\n\n(no quote)\n\n{lone}\n\n"{qb}"'
              and data.get("lone_written") == [f'"{qb}"'] and data.get("lone_kept") == [lone], err.strip()[:200])
        code, data, err = write("move", {"pairs": [{"statement": first, "quote": qa}, {"statement": second, "quote": lone}]},
                                "--dry-run")
        check("96: a lone quote's words given to a statement move it there, and the lone quote it does not name stays",
              code == 0 and data.get("after", {}).get("kq") == [f'"{qa}"', f'"{lone}"', f'"{qb}"']
              and data.get("lone_kept") == [f'"{qb}"'], str(data.get("after")))
        code, data, err = write("alone", {"statements": [f"{first} reworded", second]})
        check("96: statements alone on a turn with a lone quote keep the quotes in their places and the lone ones after",
              code == 0 and cells(15) == (f"{first} reworded\n\n{second}", f'"{qa}"\n\n(no quote)\n\n{lone}\n\n"{qb}"')
              and data.get("lone_kept") == [lone, f'"{qb}"'], f"{cells(15)} {err.strip()[:200]}")
        before = book.read_bytes()
        code, _, err = run("turn", "write", "Juno", DEMO_SHEET, "15", "--from", spec("fewer", {"statements": ["Only one"]}),
                           "--note", "Fewer")
        check("96: and statements alone that would leave a quote unpaired are refused, nothing written",
              code == 1 and "unpaired" in err and book.read_bytes() == before, err.strip()[:200])
        code, data, err = write("notes", {"notes": ["An invented note"]})
        check("96: a write of notes alone leaves the key quotes cell as it was, lone quotes and all",
              code == 0 and cells(15)[1] == f'"{qa}"\n\n(no quote)\n\n{lone}\n\n"{qb}"', err.strip()[:200])
        check("96: pairs_given reads a pair with a quote and no statement as a lone quote, where it was refused",
              idiograph_cli.pairs_given([{"statement": "", "quote": "x"}, {"statement": "s", "quote": ""}, {}]) == (["s"], [""], ["x"])
              and idiograph_cli.lone_after(['"a"', "b", "c"], ['"n"'], ["b", "n"]) == ['"a"', '"n"', "c"])

        # ── E. a real change of words, and a new order, said by the dry run
        reword = {"pairs": [{"statement": f"{first} reworded", "quote": other}, {"statement": second, "quote": ""}]}
        code, data, _ = write("reword", reword, "--dry-run")
        _, text, _ = run("turn", "write", "Juno", DEMO_SHEET, "15", "--from", spec("reword", reword), "--note", "reword",
                         "--dry-run")
        check("96: a real change of words: the dry run says the pick would be dropped, and nothing is written",
              code == 0 and [(m["key"], m["to"], m["label"], m["name"]) for m in data.get("picks") or []]
              == [(k15, None, walk, made["name"])]
              and f"On {made['name']}, the pick {k15} on 'An invented walk' would be dropped" in text
              and cells(15)[1] == f'"{qa}"\n\n(no quote)\n\n{lone}\n\n"{qb}"', text)
        swap = {"pairs": [{"statement": second, "quote": ""}, {"statement": f"{first} reworded", "quote": qa}]}
        code, data, _ = write("swap", swap, "--dry-run")
        _, text, _ = run("turn", "write", "Juno", DEMO_SHEET, "15", "--from", spec("swap", swap), "--note", "swap",
                         "--dry-run")
        check("96: pairs in a new order: the dry run says the pick would move with its words",
              code == 0 and [(m["key"], m["to"]) for m in data.get("picks") or []] == [(k15, f"{DEMO_SHEET}:15:1")]
              and f"would move to {DEMO_SHEET}:15:1, where its words now are." in text, text)

        # ── F. the MCP tool takes a lone quote too
        mcp = mcp_server.Server(str(root), config=str(config_file))
        mcp.receive(json.dumps({"jsonrpc": "2.0", "id": 1, "method": "initialize",
                                "params": {"protocolVersion": "2025-06-18", "capabilities": {},
                                           "clientInfo": {"name": "claude-ai", "version": "0.1.0"}}}))
        listed = mcp.receive(json.dumps({"jsonrpc": "2.0", "id": 2, "method": "tools/list"}))
        tool = next(t for t in listed["result"]["tools"] if t["name"] == "turn_write")
        items = tool["inputSchema"]["properties"]["pairs"]["items"]
        written = mcp.receive(json.dumps({"jsonrpc": "2.0", "id": 3, "method": "tools/call", "params": {
            "name": "turn_write", "arguments": {"case": "Juno", "sheet": DEMO_SHEET, "row": 15, "request": "A lone quote",
                                                "pairs": [{"statement": f"{first} reworded", "quote": qa},
                                                          {"statement": second, "quote": ""},
                                                          {"statement": "", "quote": other}]}}}))
        check("96: the MCP tool takes a lone quote as a pair with an empty statement, the turn's own kept in their places",
              "required" not in items and "lone quote" in tool["description"] and written["result"]["isError"] is False
              and cells(15)[1] == f'"{qa}"\n\n(no quote)\n\n{lone}\n\n"{qb}"\n\n"{other}"', str(written)[:300])

        # ── F2. a lone quote goes only when a write names it under remove
        before = book.read_bytes()
        code, _, err = run("turn", "write", "Juno", DEMO_SHEET, "15", "--from", spec("nolone", {"remove": [first]}),
                           "--note", "No such lone quote")
        check("96: remove naming words that are no lone quote of the turn is refused, nothing written",
              code == 1 and "is not a lone quote of this turn" in err and book.read_bytes() == before, err.strip()[:200])
        code, data, err = write("remove", {"remove": [f'"{qb}"']}, "--dry-run")
        check("96: the dry run of a removal lists the lone quote it would remove and the ones it keeps, writing nothing",
              code == 0 and data.get("lone_removed") == [f'"{qb}"'] and data.get("lone_kept") == [lone, f'"{other}"']
              and book.read_bytes() == before, str(data)[:300])
        code, data, err = write("remove", {"remove": [qb]})
        check("96: a removal alone takes out the named lone quote, its inverted commas set aside, the rest as they stood",
              code == 0 and cells(15)[1] == f'"{qa}"\n\n(no quote)\n\n{lone}\n\n"{other}"'
              and data.get("lone_removed") == [f'"{qb}"'], f"{cells(15)} {err.strip()[:200]}")
        gone = mcp.receive(json.dumps({"jsonrpc": "2.0", "id": 4, "method": "tools/call", "params": {
            "name": "turn_write", "arguments": {"case": "Juno", "sheet": DEMO_SHEET, "row": 15, "request": "Remove it",
                                                "remove": [other]}}}))
        check("96: the MCP tool takes remove too, and says so",
              "remove" in tool["inputSchema"]["properties"] and "remove" in tool["description"]
              and gone["result"]["isError"] is False and cells(15)[1] == f'"{qa}"\n\n(no quote)\n\n{lone}', str(gone)[:300])

        # ── G. how many picks a label takes: one rule, the command line and the app agreeing
        apply = spec("three", {"request": "Three quotes carry it", "operations": [
            {"op": "pick", "label": three, "quotes": [k19[2], k19[0], k19[1]]}]})
        code, data, err = answer("board", "apply", "Juno", made["id"], "--ops", apply)
        after = themes_mod.state(book, "Juno")
        check("96: board apply's pick keeps all three quotes it names, in its order, and the app reads the three",
              code == 0 and (data.get("applied") or [{}])[0].get("quotes") == [k19[2], k19[0], k19[1]]
              and after["picks"].get(three) == [k19[2], k19[0], k19[1]] and after["picks"].get(walk) == [k15],
              f"{data.get('applied')} {err.strip()[:200]}")
        start = themes_ai.revise_start(themes_mod.read_cards(book), themes_mod.current_version(themes_mod.load(book)))
        ops = [{"op": "pick", "label": three, "quotes": k19}]
        by_ai = themes_ai.revise_ops(start, ops)[0]["picks"].get(three)
        by_hand = themes_ai.revise_ops(dict(start, pick_max=None), ops)[0]["picks"].get(three)
        check("96: an AI answer's pick is still held to two, and the command line's to none",
              by_ai == k19[:2] and by_hand == k19 and themes_ai.PICKS_MAX == 2, f"{by_ai} {by_hand}")
        many = themes_mod.normalise(dict(made, picks={three: k19}))
        toggle = fn(th_js, "thTogglePick")
        check("96: the file keeps three on read, and the PETs screen's tick holds no number either",
              many["picks"].get(three) == k19 and toggle and not re.search(r"length\s*[<>]=?\s*\d|PICKS|slice\(0,", toggle),
              toggle[:200])
        if node:
            script = scratch / "quotesafe-ticks.js"
            script.write_text(support.i18n_js() + th_js + r"""
const card = (row) => ({ sheet: 'S', row, line: 0, x: 0, y: 0, text: `${row}`, seconds: 0, time: '' });
const v = { cards: { 'S:3:0': card(3), 'S:5:0': card(5), 'S:7:0': card(7) }, groups: [], discarded: [], picks: {} };
const g = thMakeGroup(v, ['S:3:0', 'S:5:0', 'S:7:0'], 'Three');
['S:3:0', 'S:5:0', 'S:7:0'].forEach((k) => thTogglePick(v, g, k));
thPrunePicks(v);
console.log(JSON.stringify(v.picks[g]));
""", encoding="utf-8")
            ran = subprocess.run([node, str(script)], capture_output=True, text=True, encoding="utf-8")
            check("96: in node, three ticks on one label keep three, as the command line now does",
                  ran.returncode == 0 and support.plain(json.loads(ran.stdout or "null")) == ["S:3:0", "S:5:0", "S:7:0"],
                  (ran.stdout or ran.stderr).strip()[:200])
        else:
            skip("96: three ticks in node", "no node on this machine")
    finally:
        server_mod.CONFIG_PATH, server_mod.ROOT_OVERRIDE, server_mod.STATE_MEMORY, locks.WAIT = kept
