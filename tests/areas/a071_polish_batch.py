from __future__ import annotations

import inspect
import json
import shutil

from . import support
from .support import MAKE_WAY_CHECK, check, demo_copy, skip
import idiograph_routes


POLISH_DRAG = r"""
// a member card dragged far from its PET, past a card in no PET, without Alt and with it
const scene = () => {
  const v = board({ 'a:1:0': [0, 0], 'a:2:0': [210, 0], 'k:1:0': [700, 0], 'k:2:0': [700, 700] });
  const P = thMakeGroup(v, ['a:1:0', 'a:2:0'], 'Mornings');
  return { v, P };
};
{
  const { v, P } = scene();
  const was = keep(thSpots(v));
  const d = start(v, ['a:2:0']);
  const m = move(v, d, 900, 0, { x: 1210, y: 40 });
  const lay = thLayout(v, size, null);
  const made = keep(thSpots(v));
  out.far = { home: m.home, moved: m.moved, member: thParents(v)['a:2:0'] === P,
    clear: !thMeets(lay[P].frame, boxOf(v, 'k:1:0'), M), kMoved: !home(v, was, 'k:1:0'), landed: at(v, 'a:2:0') };
  thDrop(v, d.moving, null, null, false);
  thSettle(v, size, d.moving, d.was, [], TH_PASSES, true);
  const after = thLayout(v, size, null);
  out.far.drop = { member: thParents(v)['a:2:0'] === P, still: JSON.stringify(keep(thSpots(v)).cards) === JSON.stringify(made.cards),
    clashes: thClashes(v, size).length, landed: at(v, 'a:2:0'), clear: !thMeets(after[P].frame, boxOf(v, 'k:1:0'), M) };
}
{
  const { v, P } = scene();
  const was = keep(thSpots(v));
  const d = start(v, ['a:2:0']);
  d.alt = true;
  const m = move(v, d, 900, 0, { x: 1210, y: 40 });
  out.alt = { home: m.home, kStill: home(v, was, 'k:1:0') };
  const { left } = thDrop(v, d.moving, null, null, true);
  out.alt.left = left;
}
// into another PET's body: since 31 October (design A) it goes in, that PET's own cards making room, and nothing on
// the canvas moves
{
  const v = board({ 'a:1:0': [0, 0], 'a:2:0': [210, 0], 'k:1:0': [700, 0], 'q:1:0': [1200, 0] });
  const P = thMakeGroup(v, ['a:1:0', 'a:2:0'], 'Mornings');
  const Q = thMakeGroup(v, ['q:1:0'], 'Nights');
  const was = keep(thSpots(v));
  const d = start(v, ['a:2:0']);
  const m = move(v, d, 1000, 20, { x: 1260, y: 60 });
  out.join = { home: m.home === Q, kStill: home(v, was, 'k:1:0'), moved: m.moved };
}
console.log(JSON.stringify(out));
"""


def test_polish_batch(scratch):
    print("\n71. Polish: the Current board passes to the last board left (169), an edit carried to the other boards, "
          "the bars' names, the zoom bar clear of the bin, a far drag, the Current board on the case row, the round "
          "card once")
    import subprocess
    import server as server_mod
    import themes as themes_mod

    js = support.text("apps/idiograph/static/themes.js")
    app = support.text("family/static/shell.js", "apps/idiograph/static/distil.js")
    fn = lambda src, name: src.split(f"function {name}(", 1)[1].split("\n}", 1)[0] if f"function {name}(" in src else ""
    whole = lambda src, name: f"function {name}(" + fn(src, name) + "\n}"
    node = shutil.which("node")

    root = scratch / "polish-root"
    kept = (server_mod.ROOT_OVERRIDE, server_mod.STATE_PATH, server_mod.STATE_MEMORY)
    server_mod.ROOT_OVERRIDE = str(root)
    server_mod.STATE_PATH = scratch / "polish-state.json"
    server_mod.STATE_MEMORY = {"recent": []}
    try:
        # ── 1. the Current board passes to the last board left (169)
        work = demo_copy(root, "Juno", "Juno - EN & ES.xlsx")
        file = lambda: json.loads(themes_mod.themes_path(work).read_text(encoding="utf-8"))
        op = lambda name, **extra: idiograph_routes.api_themes_versions(dict({"workbook": str(work), "op": name}, **extra))
        op("new")
        lone = op("delete", id="v2")
        check("169: a file that never marked a board marks nothing when one board is left",
              lone["chosen"] is None and "chosen" not in file() and [v["id"] for v in lone["versions"]] == ["v1"])
        op("choose", id="v1")
        made = op("new")["current"]
        passed = op("delete", id="v1")
        check("169: the Current board deleted with one board left marks that one, in the answer and the file",
              passed["chosen"] == made and file()["chosen"] == made and passed["current"] == made
              and [v["name"] for v in passed["versions"]] == ["Board 2"], str(passed["chosen"]))
        op("new")
        middle = op("new")["versions"][1]["id"]
        op("choose", id=middle)
        gone = op("delete", id=middle)
        check("169: with two or more boards left the mark goes nowhere, and nothing is said",
              gone["chosen"] is None and "chosen" not in file() and len(gone["versions"]) == 2
              and set(gone) == set(passed))
        check("169: the page takes the mark from the delete's answer, so an old server's answer leaves it off",
              "thLoad(data);" in fn(js, "thDeleteGo") and "TH.chosen = data.chosen || null;" in fn(js, "thLoad")
              and "data[\"chosen\"] = str(versions[0].get(\"id\"))" in inspect.getsource(themes_mod.version_op))

        # ── 2. a statement edited in place is carried to the other boards that held its words
        edit_root = scratch / "polish-edit-root"
        work2 = demo_copy(edit_root, "Juno", "Juno - EN & ES.xlsx")
        server_mod.ROOT_OVERRIDE = str(edit_root)
        op2 = lambda name, **extra: idiograph_routes.api_themes_versions(dict({"workbook": str(work2), "op": name}, **extra))
        file2 = lambda: json.loads(themes_mod.themes_path(work2).read_text(encoding="utf-8"))
        opened = idiograph_routes.api_themes({"workbook": str(work2)})
        card = next(c for c in opened["cards"] if c["key"].endswith(":0"))
        key, was_text = card["key"], card["text"]
        sheet, row, line = key.split(":")
        op2("new")
        op2("new")
        idiograph_routes.api_themes_boards({"workbook": str(work2), "op": "revision", "id": "v1", "name": "before"})
        data = file2()
        data["boards"][2]["cards"][key]["text"] = "Words from an older reading"
        themes_mod.write(work2, data)
        op2("switch", id="v1")
        new_text = was_text + " again"
        idiograph_routes.api_edit_statement({"workbook": str(work2), "sheet": sheet, "row": int(row), "line": int(line),
                                       "text": new_text, "old": was_text})
        after = {b["id"]: b["cards"][key] for b in file2()["boards"]}
        rev = file2()["boards"][0]["history"][-1]["state"]["cards"][key]["text"]
        check("2: an edit in place gives the new words to every board whose card held the old ones",
              after["v1"]["text"] == new_text and after["v2"]["text"] == new_text and "live" not in after["v2"], str(after))
        check("2: a board whose card held other words keeps them, and its revisions keep theirs",
              after["v3"]["text"] == "Words from an older reading" and rev == was_text, str(after["v3"]))
        shown = lambda vid: next(c for c in op2("switch", id=vid)["cards"] if c["key"] == key)
        check("2: so the other board shows the card as it reads, and only the board that held other words marks it changed",
              not shown("v2").get("changed") and shown("v3").get("changed")
              and shown("v3").get("stored") == "Words from an older reading")
        op2("switch", id="v1")
        idiograph_routes.api_edit_statement({"workbook": str(work2), "sheet": sheet, "row": int(row), "line": int(line),
                                       "text": was_text, "old": new_text})
        undone = {b["id"]: b["cards"][key]["text"] for b in file2()["boards"]}
        check("2: undo through the same route gives the old words back to the same boards",
              undone == {"v1": was_text, "v2": was_text, "v3": "Words from an older reading"}, str(undone))
        bare = demo_copy(edit_root, "Bare", "Juno - EN & ES.xlsx")
        out = idiograph_routes.api_edit_statement({"workbook": str(bare), "sheet": sheet, "row": int(row), "line": int(line),
                                             "text": new_text, "old": was_text})
        check("2: a case with no themes file has its line written and no themes file made",
              out["changed"] and not themes_mod.themes_path(bare).exists())
        themes_mod.themes_path(bare).parent.mkdir(parents=True, exist_ok=True)
        themes_mod.themes_path(bare).write_text("{ not json", encoding="utf-8")
        out = idiograph_routes.api_edit_statement({"workbook": str(bare), "sheet": sheet, "row": int(row), "line": int(line),
                                             "text": was_text, "old": new_text})
        check("2: a themes file that cannot be read is left as it is, and the line is still written",
              out["changed"] and themes_mod.themes_path(bare).read_text(encoding="utf-8") == "{ not json"
              and themes_mod.statement_edited(bare, sheet, row, line, was_text, new_text) == 0)

        # ── 6. the Current board on the case list's row
        server_mod.ROOT_OVERRIDE = str(root)
        wren = root / "P8 - Wren" / "P8 Wren - EN & ES.xlsx"
        wren.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(work, wren)
        idiograph_routes.api_open({"path": str(work)})
        op("choose", id=gone["versions"][0]["id"])
        name = gone["versions"][0]["name"]
        cases = idiograph_routes.api_cases({})
        rows = {c["case"]: c.get("board") for c in cases["cases"]}
        check("6: a case whose themes file marks a Current board names it on its row, and one with no file names none",
              rows.get("Juno") == name and rows.get("P8 - Wren") is None and "board" in cases["demo"], str(rows))
        check("6: the recent list carries the same name, read the way the listing reads it",
              [(r["case"], r["board"]) for r in cases["recent"]] == [("Juno", name)],
              str([(r["case"], r.get("board")) for r in cases["recent"]]))
        op("choose", id=None)
        check("6: a file with no mark gives no name, and nothing is written by the listing",
              themes_mod.chosen_name(work) is None and idiograph_routes.api_cases({})["cases"][0].get("board") is None)
        head_only = themes_mod.themes_path(wren)
        head_only.parent.mkdir(parents=True, exist_ok=True)
        head_only.write_text('{\n "schema": 2,\n "current": "v1",\n "boards": [ not json at all', encoding="utf-8")
        parsed = []
        real_loads = themes_mod.json.loads
        themes_mod.json.loads = lambda *a, **k: parsed.append(1) or real_loads(*a, **k)
        try:
            unmarked = themes_mod.chosen_name(wren)
        finally:
            themes_mod.json.loads = real_loads
        head_only.write_text('{\n "current": "v1",\n "chosen": "v9",\n "boards": [{"id": "v1", "name": "Board 1"}]\n}',
                             encoding="utf-8")
        check("6: a file whose head carries no mark is never parsed, and a mark naming a board gone names none",
              unmarked is None and not parsed and themes_mod.chosen_name(wren) is None
              and themes_mod.chosen_name(root / "nowhere.xlsx") is None)
    finally:
        server_mod.ROOT_OVERRIDE, server_mod.STATE_PATH, server_mod.STATE_MEMORY = kept

    # ── 4. the zoom bar keeps clear of the bin
    if not node:
        skip("4, 5, 7: the page's parts in node", "node is not installed")
        return

    # ── 5. a far drag keeps the member, its frame stretching after it, and the drop sends clear what it reaches
    prelude = MAKE_WAY_CHECK.split("const out = {};", 1)[0]
    script = scratch / "polish-drag.js"
    script.write_text(support.i18n_js() + """
globalThis.$ = () => null;
globalThis.esc = (s) => String(s).replace(/[&<>]/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;' }[c]));
globalThis.escAttr = (s) => esc(s).replace(/"/g, '&quot;');
globalThis.say = () => {};
""" + js + prelude + "const out = {};\n" + POLISH_DRAG, encoding="utf-8")
    run = subprocess.run([node, str(script)], capture_output=True, text=True, encoding="utf-8")
    if run.returncode != 0:
        check("5: the far drag runs in node", False, run.stderr.strip()[:400])
    else:
        o = json.loads(run.stdout)
        # design A (31 October, area 312): the frame of the PET left stretches after its member and pushes nothing while
        # the drag lasts, and the drop settles what it reaches
        check("5: in node, a member dragged far without Alt stays a member, and the card under its stretched frame stays "
              "where it is while the drag lasts",
              o["far"]["home"] == "g1" and o["far"]["member"] and not o["far"]["kMoved"] and not o["far"]["clear"]
              and o["far"]["moved"] == [] and o["far"]["landed"] == [1110, 0], str(o["far"]))
        check("5: in node, the drop keeps it in its PET where it was let go, and sends that card clear of the frame",
              o["far"]["drop"] == {"member": True, "still": False, "clashes": 0, "landed": [1110, 0], "clear": True},
              str(o["far"]["drop"]))
        check("5: in node, with Alt the frame lets go, nothing makes way for it, and the drop takes the card out",
              o["alt"] == {"home": "", "kStill": True, "left": ["a:2:0"]}, str(o["alt"]))
        check("5: in node, a card dragged into another PET's body goes into it, that PET's own card making room and the "
              "card on the canvas still",
              o["join"]["home"] is True and o["join"]["kStill"] is True and o["join"]["moved"] == ["q:1:0"], str(o["join"]))

    # ── 7. the round card once per round close
    script = scratch / "polish-round-card.js"
    script.write_text(support.i18n_js() + 
        "const log = [];\n"
        "const S = { flat: [], stops: [], at: 0, data: null };\n"
        "for (const [i, round] of [1, 1, 1, 2, 2].entries()) { S.flat.push({ i, round }); S.stops.push(i); }\n"
        "const celebrate = (n) => log.push('card ' + n); const drawTurn = () => {}; const flashCount = () => log.push('flash');\n"
        "const say = (t) => log.push(t); const closeLeftRounds = () => log.push('close');\n"
        + "\n".join(ln for ln in app.splitlines() if ln.startswith(("function roundsOn(", "function roundsHere("))) + "\n"
        + whole(app, "afterCommit") + "\n"
        "const save = (at, recorded, complete) => { log.length = 0; S.at = at;\n"
        "  S.data = { config: { work_in_rounds: true }, progress: { roundsDone: [1], complete: complete || null, roundTurns: [{ number: 1, recorded }, { number: 2, recorded: false }] } };\n"
        "  afterCommit(S.flat[S.stops[at]]); return [log.slice(), S.at]; };\n"
        "console.log(JSON.stringify({ first: save(2, false), again: save(2, true), marked: save(2, true, '2026-10-05T09:00:00'),\n"
        "  middle: save(1, false) }));\n", encoding="utf-8")
    run = subprocess.run([node, str(script)], capture_output=True, text=True, encoding="utf-8")
    if run.returncode != 0:
        check("7: afterCommit runs in node", False, run.stderr.strip()[:400])
    else:
        o = json.loads(run.stdout)
        check("7: in node, the save that closes a round shows its card once",
              o["first"] == [["card 1"], 2] and o["middle"] == [["flash", "close"], 2], str(o))
        check("7: in node, a save on the last turn of a round already recorded moves on with no card, marked complete or not",
              o["again"] == [["flash", "close"], 3] and o["marked"] == [["flash", "close"], 3], str(o))
