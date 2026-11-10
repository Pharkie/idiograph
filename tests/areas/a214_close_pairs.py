from __future__ import annotations

import datetime as dt
import json
import shutil
import subprocess

import openpyxl

from . import support
from .support import check, skip

# An invented interview about keeping bees, Wren the participant and Ivo asking, every word made up. Each
# row is (speaker, time, statements, key quote), a statement cell's entries split by a blank line.
INITIAL = [
    ("Ivo", "00:12:00", None, None),
    ("Wren", "00:12:04", "Feeling trusted when the bees stay calm on her hands", "they just sat there on my hands"),
    ("Wren", "00:12:10", "Taking the calm as a gift", None),
    ("Wren", "00:12:16", "The bees' calm read as a sign she is accepted", "okay, they have decided about me"),
    ("Wren", "00:13:10", "Moving slowly so as not to alarm them", None),
    ("Wren", "00:23:02", "Wanting to do right by the colony", None),
    ("Wren", "00:23:20", "Duty felt as a weight she chose", None),
    ("Wren", "00:23:41", "Worry for the colony through its first winter", None),
    ("Wren", "00:31:10", "Pride in the first jar of honey\n\nHoney as proof of care", None),
]
# a sheet with no times, read by its rows
FOLLOW_UP = [
    ("Wren", None, "Calm with the bees now feels earned", None),
    ("Wren", None, "Earning their trust over a season", None),
    ("Ivo", None, None, None),
    ("Ivo", None, None, None),
    ("Wren", None, "The hive as a second home", None),
]
HEAD = ["Name", "Timestamp", "Experiential statements", "Transcript", "Exploratory notes", "Key quotes"]


def made_book(path) -> None:
    wb = openpyxl.Workbook()
    for i, (title, rows) in enumerate((("Initial", INITIAL), ("Follow-up", FOLLOW_UP))):
        ws = wb.active if i == 0 else wb.create_sheet()
        ws.title = title
        ws.append(HEAD)
        for who, at, said, quote in rows:
            t = dt.time(*map(int, at.split(":"))) if at else None
            ws.append([who, t, said, f"{who} says something about the bees.", None, quote])
    wb.save(path)


def test_close_pairs(scratch):
    print("\n214. Close pairs on the PETs board: two statements in one group from one sheet within the gap, "
          "none for a stacked pair, the gap's setting kept across a restart, Not the same saved and kept, and "
          "the API's pairs and its two new operations (Adam, 20 October)")
    import cli
    import mcp_server
    import server as server_mod
    import themes

    root = scratch / "close-root"
    shutil.rmtree(root, ignore_errors=True)
    case = root / "Wren"
    (case / "Working").mkdir(parents=True)
    book = case / "Wren - EN & ES.xlsx"
    made_book(book)
    (root / server_mod.PROJECT_FILE).write_text(json.dumps({
        "name": "Bees, a close pairs project", "agents": {"allowed": True, "at": "2026-10-20T18:00:00+01:00"}}), encoding="utf-8")
    cfg = scratch / "close-config.json"
    cfg.write_text(json.dumps({"root": str(root), "interviewer": "Ivo"}), encoding="utf-8")
    read = themes.read_cards(book)
    keys = [c["key"] for c in read["cards"]]
    A, L, B, C, D, F, E, J, K = keys[:9]
    G, H, I = keys[9:12]
    sids = themes.short_ids(read["cards"])
    texts = {c["key"]: c["text"] for c in read["cards"]}
    check("214: the fixture reads as twelve statements, two of them one cell's, three on a sheet with no times",
          len(keys) == 12 and J.split(":")[:2] == K.split(":")[:2] and all(c["seconds"] is None for c in read["cards"][9:]),
          str(keys))

    def at(i):
        return {"x": (i % 3) * 210, "y": (i // 3) * 100}

    cards = {k: dict(at(i), text=texts[k]) for i, k in enumerate(keys)}
    board0 = {"id": "v1", "name": "Board 1", "cards": cards, "discarded": [], "picks": {}, "stacks": {A: [L]},
              "groups": [{"id": "g1", "label": "Being trusted by the hive", "members": [A, B, C, G, H, I], "x": 0, "y": -40},
                         {"id": "g2", "label": "Living alongside the colony", "members": ["g3", "g4"], "x": 0, "y": 600},
                         {"id": "g3", "label": "Duty to the colony", "members": [D, F], "x": 0, "y": 640},
                         {"id": "g4", "label": "Fearing for the colony", "members": [E], "x": 400, "y": 640},
                         {"id": "g5", "label": "Pride in the honey", "members": [J, K], "x": 0, "y": 900}]}
    themes.save(book, board0, "Wren")
    themes_file = themes.themes_path(book)

    def board() -> dict:
        return next(b for b in json.loads(themes_file.read_text(encoding="utf-8"))["boards"] if b["id"] == "v1")

    def found(gap):
        return {(tuple(p["items"]), p["gap"], p["unit"], p["same_row"], p["group"])
                for p in themes.close_pairs(board(), read["cards"], gap)}

    # ── A. found by sheet, group and gap, none for a stacked statement
    minute = found(60)
    check("214: within a minute, the pairs are two statements directly in one group from one sheet: 12 s, 54 s, "
          "18 s, one row apart on a sheet with no times, and two of one cell, the same passage",
          minute == {((A, B), 12, "s", False, "g1"), ((B, C), 54, "s", False, "g1"), ((D, F), 18, "s", False, "g3"),
                     ((G, H), 1, "rows", False, "g1"), ((J, K), 0, "s", True, "g5")}, str(sorted(minute)))
    check("214: two 66 s apart are no pair in a minute, two in two sub-themes of one PET none, a statement stacked "
          "under another in none, and two from two sheets none whatever their places",
          not any(set(p[0]) in ({A, C}, {D, E}, {F, E}) or L in p[0] or (A in p[0] and G in p[0]) for p in minute), "")
    check("214: the gap rules: in 30 s the 54 s pair goes and one row still counts, in two minutes the 66 s pair "
          "comes and four rows count",
          {p[0] for p in found(30)} == {(A, B), (D, F), (G, H), (J, K)}
          and {p[0] for p in found(120)} == {(A, B), (B, C), (A, C), (D, F), (G, H), (G, I), (H, I), (J, K)},
          str(sorted(found(120))))
    stacked = themes.stack_onto(themes.normalise(board()), [B], A)
    check("214: once one is stacked under the other the pair is gone, and so are the stacked one's other pairs",
          {tuple(p["items"]) for p in themes.close_pairs(stacked, read["cards"], 60)} == {(D, F), (G, H), (J, K)}, "")
    check("214: the words for a gap: seconds, rows and one passage",
          [themes.pair_words(p) for p in themes.close_pairs(board(), read["cards"], 60) if p["items"] == [A, B]] == ["12 s apart"]
          and themes.pair_words({"gap": 1, "unit": "rows"}) == "1 row apart"
          and themes.pair_words({"gap": 0, "unit": "s", "same_row": True}) == "Same passage", "")

    kept = (server_mod.CONFIG_PATH, server_mod.ROOT_OVERRIDE, server_mod.STATE_MEMORY)
    try:
        server_mod.CONFIG_PATH, server_mod.ROOT_OVERRIDE = cfg, str(root)
        server_mod.STATE_MEMORY = {"recent": []}

        # ── B. the switch and the gap, off and a minute on a new install, kept across a restart
        fresh = server_mod.merge_config({})
        check("214: Close pairs is off on a new install, its gap a minute", fresh["close_pairs"] is False
              and fresh["close_gap"] == 60, str({k: fresh.get(k) for k in ("close_pairs", "close_gap")}))
        server_mod.api_settings({"close_pairs": True})
        server_mod.api_settings({"close_gap": 120})
        saved = json.loads(cfg.read_text(encoding="utf-8"))
        again = server_mod.merge_config(saved)
        check("214: the switch and the gap, each sent alone, are kept in the settings and read back after a restart",
              saved.get("close_pairs") is True and saved.get("close_gap") == 120 and again["close_pairs"] is True
              and again["close_gap"] == 120, str(saved)[:300])
        server_mod.api_settings({"close_gap": 45})
        check("214: a gap the menu does not offer is read as the minute",
              json.loads(cfg.read_text(encoding="utf-8")).get("close_gap") == 60
              and server_mod.merge_config({"close_gap": "x"})["close_gap"] == 60, "")

        # ── C. the API's pairs: board show and its JSON, and --close for one look
        def run(*args):
            return cli.run(["--root", str(root), "--config", str(cfg), *args])

        def answer(*args):
            code, out, err = run(*args, "--json")
            return code, (support.plain(json.loads(out)) if out.strip() else {}), err

        def ops(*operations, request="Mark the pair that says different things") -> str:
            path = scratch / "close-ops.json"
            path.write_text(json.dumps({"request": request, "operations": list(operations)}), encoding="utf-8")
            return str(path)

        code, shown, err = answer("board", "show", "Wren", "v1")
        close = shown.get("close") or {}
        pairs = {tuple(p["items"]): p for p in close.get("pairs") or []}
        ab = pairs.get((sids[A], sids[B])) or {}
        check("214: board show --json gives the pairs within the setting's gap, each with its two ids and keys, its "
              "sheet, the gap and the group with its title, and none marked Not the same",
              code == 0 and close.get("within_s") == 60 and len(pairs) == 5
              and ab.get("keys") == [A, B] and ab.get("sheet") == "Initial" and ab.get("gap") == 12 and ab.get("unit") == "s"
              and ab.get("group") == "g1" and ab.get("label") == "Being trusted by the hive" and close.get("not_same") == [],
              (str(close) + err)[:400])
        tree_a = next(s for t in shown.get("themes", []) if t["id"] == "g1" for s in t["statements"] if s["key"] == A)
        tree_b = next(s for t in shown.get("themes", []) if t["id"] == "g1" for s in t["statements"] if s["key"] == B)
        check("214: in the tree each statement of a pair names its partner and the gap, one close to two naming both",
              [x["id"] for x in tree_a.get("close") or []] == [sids[B]]
              and sorted(x["id"] for x in tree_b.get("close") or []) == sorted([sids[A], sids[C]]), str(tree_b.get("close")))
        code, out, _ = run("board", "show", "Wren", "v1")
        check("214: board show in words says each pair under its statements and their count at the end",
              code == 0 and f"Close to {sids[B]}, 12 s apart" in out and f"Close to {sids[K]}, same passage" in out
              and "Close pairs: 5, within 1 minute in one group" in out, out[-400:])
        before = cfg.read_bytes()
        code, look, _ = answer("board", "show", "Wren", "v1", "--close", "30")
        check("214: --close looks within another gap for that one look and leaves the setting as it was",
              code == 0 and (look.get("close") or {}).get("within_s") == 30 and len((look.get("close") or {}).get("pairs") or []) == 4
              and cfg.read_bytes() == before, str(look.get("close"))[:200])
        code, _, err = run("board", "show", "Wren", "v1", "--close", "lots")
        check("214: a --close that is not whole seconds is refused", code != 0 and "--close" in err, err[:200])
        tool = next(x for x in mcp_server.TOOLS if x["name"] == "board_show")
        check("214: the MCP's board_show takes close, left out to follow the setting",
              mcp_server.arguments(tool, {"case": "Wren", "close": 30}, {"project": None}, "test").close == 30
              and mcp_server.arguments(tool, {"case": "Wren"}, {"project": None}, "test").close is None, "")

        # ── D. Not the same through the API: a dry run, the op, kept in the file, refused twice, shown again
        start = themes_file.read_bytes()
        code, dry, _ = answer("board", "apply", "Wren", "v1", "--ops", ops(
            {"op": "not_same", "items": [sids[B], sids[A]]}), "--dry-run")
        check("214: not_same's dry run says what it would do and writes nothing",
              code == 0 and dry.get("dry_run") is True and themes_file.read_bytes() == start
              and "Not the same" in dry.get("said", ""), str(dry)[:300])
        code, done, err = answer("board", "apply", "Wren", "v1", "--ops", ops(
            {"op": "not_same", "items": [sids[B], sids[A]]}), "--note", "Mark the pair that says different things",
            "--tool", "Claude Code")
        after = board()
        check("214: not_same keeps the pair with the board, its keys in transcript order, in one revision of its History",
              code == 0 and after.get("not_same") == [[A, B]] and len(after.get("history") or []) == 1
              and not (after["history"][0]["state"].get("not_same")), (str(done) + err)[:300])
        code, shown, _ = answer("board", "show", "Wren", "v1")
        close = shown.get("close") or {}
        code_t, words, _ = run("board", "show", "Wren", "v1")
        check("214: board show leaves the pair out and lists it as marked Not the same",
              (sids[A], sids[B]) not in {tuple(p["items"]) for p in close.get("pairs") or []}
              and close.get("not_same") == [{"items": [sids[A], sids[B]], "keys": [A, B]}]
              and "Close pairs: 4, within 1 minute in one group (1 marked Not the same)" in words, str(close)[:300])
        held = themes_file.read_bytes()
        code, said, err = answer("board", "apply", "Wren", "v1", "--ops", ops(
            {"op": "not_same", "items": [sids[A], sids[B]]}), "--note", "x", "--tool", "Claude Code")
        code2, said2, err2 = answer("board", "apply", "Wren", "v1", "--ops", ops(
            {"op": "not_same", "items": [sids[A]]}), "--note", "x", "--tool", "Claude Code")
        check("214: marking a pair twice, or one statement, is refused with nothing written",
              code != 0 and code2 != 0 and themes_file.read_bytes() == held
              and "already" in str(said.get("error") or "") + err and "two" in str(said2.get("error") or "") + err2,
              (err + err2)[:300])

        # ── E. saved and read back from the page: kept by a page before them, taken off by one that sends none
        state = themes.state(book, "Wren")
        check("214: the board as the page opens it carries its pairs marked Not the same", state.get("not_same") == [[A, B]], "")
        page = dict(themes.normalise(board()))
        page.pop("not_same")
        themes.save(book, page, "Wren")
        check("214: a save from a page before the close pairs keeps the file's", board().get("not_same") == [[A, B]], "")
        themes.save(book, dict(themes.normalise(board()), not_same=[]), "Wren")
        check("214: a save that sends none takes them off, so the pair is linked again",
              not board().get("not_same") and len(themes.close_pairs(board(), read["cards"], 60)) == 5, "")
        themes.save(book, dict(themes.normalise(board()), not_same=[[B, A], [A, B], [A, "gone"]]), "Wren")
        check("214: a save keeps each pair once, in transcript order, of statements the board holds",
              board().get("not_same") == [[A, B]], str(board().get("not_same")))
        code, _, err = answer("board", "apply", "Wren", "v1", "--ops", ops(
            {"op": "show_again", "items": [sids[A], sids[B]]}), "--note", "Show it again", "--tool", "Claude Code")
        check("214: show_again takes the mark off through the API, the pair linked again",
              code == 0 and not board().get("not_same") and len(themes.close_pairs(board(), read["cards"], 60)) == 5, err[:200])
        themes.save(book, dict(themes.normalise(board()), not_same=[[A, B]]), "Wren")
        shift = lambda rk: f"{rk.rpartition(':')[0]}:{int(rk.rpartition(':')[2]) + 1}" if rk.startswith("Initial:") else rk
        moved = themes._moved(board(), shift)
        a2, b2, l2 = (f"Initial:{int(k.split(':')[1]) + 1}:0" for k in (A, B, L))
        check("214: a pair marked Not the same, and a stack, move with their rows when rows move",
              moved.get("not_same") == [[a2, b2]] and moved.get("stacks") == {a2: [l2]}, str(moved.get("not_same")))
    finally:
        server_mod.CONFIG_PATH, server_mod.ROOT_OVERRIDE, server_mod.STATE_MEMORY = kept

    # ── F. the page's model in node: the same pairs, Stack under this one and Not the same each one step of undo
    node = shutil.which("node")
    if not node:
        skip("214: the close pairs' model in node", "node is not installed")
        return
    js = support.text("apps/idiograph/static/themes.js")
    v_cards = {c["key"]: dict(c, x=at(i)["x"], y=at(i)["y"]) for i, c in enumerate(read["cards"])}
    v = {"cards": v_cards, "groups": board0["groups"], "discarded": [], "picks": {}, "stickies": [],
         "stacks": {A: [L]}, "not_same": []}
    script = scratch / "close-model.js"
    script.write_text(support.i18n_js() + """
globalThis.$ = () => null;
globalThis.esc = (s) => String(s);
globalThis.escAttr = (s) => String(s);
globalThis.say = () => {};
""" + js + r"""
const v = """ + json.dumps(v) + r""";
const out = {};
TH.mode = 'pets'; TH.config = { close_pairs: true, close_gap: 60 }; TH.v = v; TH.live = true;
TH.stackable = true; TH.pairable = true; TH.layout = {};
const ids = (ps) => ps.map((p) => [p.a, p.b, p.gap, p.unit, p.same, p.group]);
out.minute = ids(thClosePairs(v));
TH.config.close_gap = 30;
out.half = ids(thClosePairs(v));
TH.config.close_gap = 45;
out.odd = thCloseGap();
TH.config.close_gap = 60;
// the canvas drawn nowhere: what an act draws stands still, and the undo is the page's own
thRender = () => {}; thEase = () => {}; thSoon = () => {}; thMomentum = () => {}; thAck = () => {};
thInspectorOpen = () => {}; thPanelFollow = () => {};
const pairs = thClosePairs(v);
const ab = pairs.find((p) => p.a === '""" + A + """' && p.b === '""" + B + r"""');
thPairStack(ab, ab.b);
out.stacked = { stacks: JSON.parse(JSON.stringify(v.stacks)), undo: TH.undo.length, pairs: ids(thClosePairs(v)) };
thUndo(true);
out.undone = { stacks: JSON.parse(JSON.stringify(v.stacks)), pairs: thClosePairs(v).length };
const bc = thClosePairs(v).find((p) => p.a === '""" + B + """' && p.b === '""" + C + r"""');
thPairApart(bc);
out.apart = { notSame: JSON.parse(JSON.stringify(v.not_same)), undo: TH.undo.length, pairs: thClosePairs(v).length,
  body: thBody(v, { id: 'v1', name: 'Board 1' }).not_same };
thUndo(true);
out.back = { notSame: JSON.parse(JSON.stringify(v.not_same)), pairs: thClosePairs(v).length };
thUndo(false);
thPairAgain(0);
out.again = { notSame: JSON.parse(JSON.stringify(v.not_same)), undo: TH.undo.length };
TH.mode = 'gets';
out.gets = thClosePairs(v).length + (thCloseOn() ? 1 : 0);
console.log(JSON.stringify(out));
""", encoding="utf-8")
    ran = subprocess.run([node, str(script)], capture_output=True, text=True, encoding="utf-8", timeout=60)
    try:
        o = support.plain(json.loads(ran.stdout.strip().splitlines()[-1]))
    except (ValueError, IndexError):
        o = {}
    want = sorted([[A, B, 12, "s", False, "g1"], [B, C, 54, "s", False, "g1"], [G, H, 1, "rows", False, "g1"],
                   [D, F, 18, "s", False, "g3"], [J, K, 0, "s", True, "g5"]])
    check("214: in node, the page finds the same pairs as board show, within the setting's gap, and a gap the menu "
          "does not offer is the minute",
          sorted(o.get("minute") or []) == want and len(o.get("half") or []) == 4 and o.get("odd") == 60,
          (ran.stdout + ran.stderr)[:500])
    s_ = o.get("stacked") or {}
    check("214: in node, Stack under this one stacks the other of the pair under the one chosen, its own stack with "
          "it, in one step of undo, the pair gone, and undo puts both back",
          s_.get("stacks") == {B: [A, L]} and s_.get("undo") == 1 and len(s_.get("pairs") or []) == 4
          and o.get("undone") == {"stacks": {A: [L]}, "pairs": 5}, json.dumps([s_, o.get("undone")])[:400])
    ap = o.get("apart") or {}
    check("214: in node, Not the same keeps the pair with the board, one step of undo, the line gone, and the save "
          "sends it; undo brings it back, redo and Show again take it off again",
          ap.get("notSame") == [[B, C]] and ap.get("undo") == 1 and ap.get("pairs") == 4 and ap.get("body") == [[B, C]]
          and o.get("back") == {"notSame": [], "pairs": 5} and (o.get("again") or {}).get("notSame") == []
          and (o.get("again") or {}).get("undo") == 2, json.dumps([ap, o.get("back"), o.get("again")])[:500])
    check("214: in node, the GETs board has no close pairs and no switch", o.get("gets") == 0, str(o.get("gets")))
