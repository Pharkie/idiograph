"""Area 239: the boards' toolbar, Auto-arrange's ways, Align and Spread, and 25 participant colours (Adam, 21
October 2026, the toolbar drawings, "Build as drawn").

The palette docked by default under the research question as a toolbar, each tool with its icon and its word,
pulled off by its grip to float and docked again, its place kept on this computer; Auto-arrange's button
repeating the last of Grid, Column and Row; Align's six and Spread's two on the toolbar and under Align in a
selection's right-click menu; and the participants' colours grown from eight to 25, a new participant given
the next free one and a colour another participant has never choosable. Each canvas act has its operation for
an agent, through `board apply`, `gets apply` and `gets colour`.

The checks hold behaviour: each Align and Spread result's places, in the page's code and the server's alike,
Column's order down a PET with its sub-theme kept whole, the colour a new participant gets, a taken colour
refused in the app and through the command line, the toolbar's docked or floating place kept in the settings
and drawn so after a reload, and the operations' dry runs writing nothing. Words, layout and colour go to Adam
as review shots. The fixtures are invented: an allotment study's holders and a board about learning to swim.
"""
from __future__ import annotations

import json
import shutil
import subprocess

from .a201_status_bar_and_palette import STUBS
from . import support
from .support import case_palette_problems, check, demo_copy, refusal_of, skip
import idiograph_routes

BOXES = [("a", 100, 0, 200, 80), ("b", 40, 120, 200, 60), ("c", 300, 240, 160, 80), ("d", 600, 60, 200, 100)]
# where each box goes, its top-left corner, by way: the edge or centre of the outermost, the others along the
# line moved on only as far as keeps the margin of 10 clear, and Spread's even gaps between the first and last
WANT = {
    "left": {"a": [40, 0], "b": [40, 200], "c": [40, 270], "d": [40, 90]},
    "centre": {"a": [320, 0], "b": [320, 200], "c": [340, 270], "d": [320, 90]},
    "right": {"a": [600, 0], "b": [600, 200], "c": [640, 270], "d": [600, 90]},
    "top": {"a": [250, 0], "b": [40, 0], "c": [460, 0], "d": [630, 0]},
    "middle": {"a": [250, 120], "b": [40, 130], "c": [460, 120], "d": [630, 110]},
    "bottom": {"a": [250, 240], "b": [40, 260], "c": [460, 240], "d": [630, 220]},
    "across": {"a": [250, 0], "b": [40, 120], "c": [460, 240], "d": [630, 60]},
    "down": {"a": [100, 0], "b": [40, 200], "c": [300, 270], "d": [600, 90]},
}


def test_toolbar(scratch):
    print("\n239. The boards' toolbar docked under the research question, Auto-arrange's Grid, Column and Row, Align "
          "and Spread, and 25 participant colours (Adam, 21 October)")
    import cli
    import gets as gets_mod
    import server as server_mod
    import themes as themes_mod

    # ── A. Align and Spread's places, the server's
    plans = {how: themes_mod.align_plan({i: (x, y, w, h) for i, x, y, w, h in BOXES}, how)
             for how in themes_mod.ALIGN_WAYS + themes_mod.SPREAD_WAYS}
    got = {how: {i: list(p) for i, p in plan.items()} for how, plan in plans.items()}
    for how in WANT:
        check(f"239: Align and Spread, {how}: each card to its place, the others along the line moved on only as far as "
              "keeps the margin, so nothing overlaps", got[how] == WANT[how], f"{got[how]}")

    def apart(how):
        sizes = {i: (w, h) for i, _x, _y, w, h in BOXES}
        boxes = [(p[0], p[1], *sizes[i]) for i, p in plans[how].items()]
        return not any(themes_mod.clash(a, b) for n, a in enumerate(boxes) for b in boxes[n + 1:])
    check("239: no Align or Spread leaves two cards overlapping", all(apart(how) for how in WANT))

    # ── B. Column on a PET: one card above another in the order they read, the sub-theme kept whole as a block
    card = lambda x, y, t="A length of the pool without stopping": {"x": x, "y": y, "text": t}
    v = {"cards": {"S:1:0": card(0, 100), "S:2:0": card(220, 100), "S:3:0": card(0, 200), "S:4:0": card(220, 200),
                   "S:6:0": card(40, 470), "S:7:0": card(40, 570), "S:9:0": card(600, 100)},
         "groups": [{"id": "g1", "label": "Trusting the water", "members": ["S:1:0", "S:2:0", "S:3:0", "S:4:0", "g2"], "x": 0, "y": 50},
                    {"id": "g2", "label": "The deep end", "members": ["S:6:0", "S:7:0"], "x": 40, "y": 430}],
         "discarded": [], "picks": {}}
    before = themes_mod.order_of(themes_mod.normalise(json.loads(json.dumps(v))), "g1")
    col = themes_mod.arrange(v, "g1", "column")
    drawn = themes_mod.layout_boxes(col)
    own = ["S:1:0", "S:2:0", "S:3:0", "S:4:0"]
    tops = [col["cards"][k]["y"] for k in own]
    frame = drawn["frames"]["g2"]
    inner = [drawn["cards"][k] for k in ("S:6:0", "S:7:0")]
    check("239: Column keeps the order the PET read in, each card one above another at one left edge, and the "
          "sub-theme a block in its place, its cards inside its frame below the cards before it",
          themes_mod.order_of(col, "g1") == before and len({col["cards"][k]["x"] for k in own}) == 1
          and tops == sorted(tops) and len(set(tops)) == 4 and frame[1] > tops[-1]
          and all(frame[0] <= b[0] and b[1] + b[3] <= frame[1] + frame[3] for b in inner)
          and inner[0][1] < inner[1][1] and col["cards"]["S:9:0"] == v["cards"]["S:9:0"], f"{before} {tops} {frame}")
    row = themes_mod.arrange(v, "g1", "row")
    lefts = [row["cards"][k]["x"] for k in own]
    check("239: Row puts them side by side in the order they read, at one top",
          themes_mod.order_of(row, "g1") == before and lefts == sorted(lefts) and len({row["cards"][k]["y"] for k in own}) == 1, str(lefts))
    check("239: a way Auto-arrange does not have is refused",
          refusal_of(lambda: themes_mod.arrange(v, "g1", "spiral")).startswith("Auto-arrange's ways are"))

    # ── C. in node: the page's Align and Spread places the same as the server's, Column's order, and the toolbar's place
    node = shutil.which("node")
    if not node:
        skip("239: the toolbar in node", "node is not installed")
    else:
        js = support.text("apps/idiograph/static/themes.js")
        scenario = r"""
const out = {};
const boxes = %s;
out.plans = {};
for (const how of TH_ALIGN_WAYS.concat(TH_SPREAD_WAYS)) {
  const p = thAlignPlan(boxes.map(([id, x, y, w, h]) => ({ id, x, y, w, h })), how);
  out.plans[how] = Object.fromEntries(Object.entries(p).map(([id, b]) => [id, [b.x, b.y]]));
}
// Column on the swimming board, by the page's own arrange
const c = (x, y) => ({ x, y, text: 'A length of the pool without stopping' });
const v = { cards: { 'S:1:0': c(0, 100), 'S:2:0': c(220, 100), 'S:3:0': c(0, 200), 'S:4:0': c(220, 200), 'S:6:0': c(40, 470), 'S:7:0': c(40, 570) },
  groups: [{ id: 'g1', label: 'Trusting the water', members: ['S:1:0', 'S:2:0', 'S:3:0', 'S:4:0', 'g2'], x: 0, y: 50 },
    { id: 'g2', label: 'The deep end', members: ['S:6:0', 'S:7:0'], x: 40, y: 430 }], discarded: [], stacks: {} };
const size = (id) => (v.cards[id] ? { w: 200, h: 80 } : { w: 180, h: 32 });
const order = () => thThemeOrder(v, 'g1', thLayout(v, size, null));
out.before = order();
out.arranged = thArrange(v, 'g1', size, 'column');
out.after = order();
out.xs = ['S:1:0', 'S:2:0', 'S:3:0', 'S:4:0'].map((k) => v.cards[k].x);
out.ys = ['S:1:0', 'S:2:0', 'S:3:0', 'S:4:0', 'S:6:0', 'S:7:0'].map((k) => v.cards[k].y);
// the toolbar's place: docked under the question by default, floating where the settings put it
class Box {
  constructor(id) { this.id = id; this.kids = []; this.parentElement = null; this.cls = new Set(); this.attrs = {};
    const self = this; this.style = { setProperty: () => {} }; this.hidden = false; this.offsetWidth = 140; this.offsetHeight = 300;
    this.clientWidth = 1000; this.clientHeight = 600;
    this.classList = { add: (...n) => n.forEach((x) => self.cls.add(x)), remove: (...n) => n.forEach((x) => self.cls.delete(x)),
      contains: (n) => self.cls.has(n), toggle: (n, on) => { if (on === undefined) on = !self.cls.has(n); if (on) self.cls.add(n); else self.cls.delete(n); return on; } }; }
  appendChild(k) { if (k.parentElement) k.parentElement.kids = k.parentElement.kids.filter((x) => x !== k); this.kids.push(k); k.parentElement = this; }
  setAttribute(k, val) { this.attrs[k] = String(val); }
  querySelector() { return null; }
}
for (const id of ['th-palette', 'th-stage', 'th-dock']) ELS[id] = new Box(id);
ELS['th-stage'].appendChild(ELS['th-palette']);
TH.config = {};
thPalettePlace();
const pal = ELS['th-palette'];
out.fresh = { in: pal.parentElement.id, docked: pal.cls.has('docked') };
TH.config = { palette_docked: false, palette_place: { edge: 'right', y: 0.5 } };
thPalettePlace();
out.floating = { in: pal.parentElement.id, docked: pal.cls.has('docked'), right: pal.cls.has('right'), rightPx: pal.style.right };
TH.config = { palette_docked: true, palette_place: { edge: 'right', y: 0.5 } };
thPalettePlace();
out.again = { in: pal.parentElement.id, docked: pal.cls.has('docked'), left: pal.style.left, top: pal.style.top };
out.docks = [thPaletteDocks(120, 100), thPaletteDocks(90, 100), thPaletteDocks(200, 100)];
console.log(JSON.stringify(out));
""" % json.dumps([list(b) for b in BOXES])
        script = scratch / "toolbar-239.js"
        script.write_text(support.i18n_js() + STUBS + js + scenario, encoding="utf-8")
        run = subprocess.run([node, str(script)], capture_output=True, text=True, encoding="utf-8", timeout=120)
        if run.returncode != 0:
            check("239: the toolbar runs in node", False, run.stderr.strip()[:600])
        else:
            o = json.loads(run.stdout)
            check("239: in node, the page's Align and Spread put each card where the server's do, all eight ways",
                  all(o["plans"][how] == WANT[how] for how in WANT), str({h: o["plans"][h] for h in WANT if o["plans"][h] != WANT[h]}))
            check("239: in node, the page's Column keeps the order the PET read in, one card above another at one left "
                  "edge, the sub-theme's cards below them, inside it one above the other",
                  o["arranged"] is True and o["after"] == o["before"] and len(set(o["xs"])) == 1
                  and o["ys"] == sorted(o["ys"]) and len(set(o["ys"])) == 6, str({k: o[k] for k in ("after", "xs", "ys")}))
            check("239: in node, with nothing kept the toolbar stands docked under the question, and the settings' "
                  "floating place puts it on the canvas against its edge, and docked again it leaves the canvas",
                  o["fresh"] == {"in": "th-dock", "docked": True}
                  and o["floating"] == {"in": "th-stage", "docked": False, "right": True, "rightPx": "16px"}
                  and o["again"] == {"in": "th-dock", "docked": True, "left": "", "top": ""}, str({k: o[k] for k in ("fresh", "floating", "again")}))
            check("239: in node, a drag of the floating toolbar docks when let go over the slot at the canvas's top, or "
                  "above it, and floats anywhere lower", o["docks"] == [True, True, False], str(o["docks"]))

    # ── D. the toolbar's place and Auto-arrange's way kept in the settings across a restart
    cfg = scratch / "toolbar-config.json"
    cfg.write_text(json.dumps({"projects": [], "interviewer": "Adam"}), encoding="utf-8")
    kept = (server_mod.CONFIG_PATH, server_mod.ROOT_OVERRIDE, server_mod.STATE_MEMORY)
    try:
        server_mod.CONFIG_PATH, server_mod.ROOT_OVERRIDE = cfg, None
        server_mod.STATE_MEMORY = {"recent": []}
        fresh = server_mod.merge_config({})
        server_mod.api_settings({"palette_docked": False, "palette_place": {"edge": "left", "y": 0.4}})
        server_mod.api_settings({"arrange_way": "column"})
        saved = json.loads(cfg.read_text(encoding="utf-8"))
        back = server_mod.merge_config(saved)
        odd = server_mod.merge_config({"palette_docked": "no", "arrange_way": "spiral"})
        check("239: on a new install the toolbar is docked and Auto-arrange is a grid; pulled off, its floating place and "
              "Column are kept in the settings file and read back so after a restart, and anything else reads as new",
              fresh["palette_docked"] is True and fresh["arrange_way"] == "grid"
              and saved.get("palette_docked") is False and back["palette_docked"] is False
              and back["palette_place"] == {"edge": "left", "y": 0.4} and back["arrange_way"] == "column"
              and odd["palette_docked"] is True and odd["arrange_way"] == "grid",
              str({k: saved.get(k) for k in ("palette_docked", "palette_place", "arrange_way")}))
    finally:
        server_mod.CONFIG_PATH, server_mod.ROOT_OVERRIDE, server_mod.STATE_MEMORY = kept

    # ── E. the participants' colours: 25, a new participant the next free, a taken colour refused
    problems = case_palette_problems(support.text("apps/idiograph/static/themes.css"),
                                     support.text("family/static/tokens.css"))
    check("239: the 25 colours in light and dark: neighbours in the picker's order and its grid of five stay apart as "
          "seen and under protanopia, deuteranopia and tritanopia, the eight as apart as before, every badge's letter "
          "readable on them, and none a red or near a judgement's colour", not problems, "; ".join(problems[:8]))
    names = ("Bea", "Cal", "Dot", "Eli", "Fen", "Gus", "Hal", "Isla", "Ivo", "Jem")
    many = gets_mod.looks(list(names), None)
    chose = gets_mod.looks(list(names), {"colours": {"Bea": 9, "Cal": 12}})
    check("239: the palette holds 25 colours, the eight first, and each participant past eight takes the next of them, "
          "never coming round to Blue while one is free",
          gets_mod.COLOURS == 25 and gets_mod.COLOUR_NAMES[:8] == ("Blue", "Olive", "Plum", "Brown", "Indigo", "Teal", "Purple", "Slate")
          and [many[n]["colour"] for n in names] == list(range(10)), str([many[n]["colour"] for n in names]))
    check("239: a participant whose own colour another has chosen gets the next free one after it, the others keeping "
          "theirs, and Default names the colour each would have",
          [chose[n]["colour"] for n in names] == [9, 12, 2, 3, 4, 5, 6, 7, 8, 10]
          and chose["Jem"]["chosen"] is False and chose["Bea"]["default"] == 0 and chose["Cal"]["default"] == 1,
          str([(n, chose[n]["colour"], chose[n]["default"]) for n in names]))

    root = scratch / "toolbar-239-root" / "Allotment study"
    shutil.rmtree(root.parent, ignore_errors=True)
    books = {name: demo_copy(root, name, f"{name} - EN & ES.xlsx") for name in ("Isla", "Ivo", "Tam")}
    (root / "idiograph-project.json").write_text(json.dumps({"name": "Allotments", "research_question": "What is it like?",
                                                             "agents": {"allowed": True, "at": "2026-10-21T10:00:00+01:00"}}),
                                                 encoding="utf-8")
    saved = (server_mod.ROOT_OVERRIDE, server_mod.STATE_PATH, server_mod.STATE_MEMORY)
    server_mod.ROOT_OVERRIDE = str(root)
    server_mod.STATE_MEMORY = {"recent": []}
    any_book = str(books["Isla"])
    gfile = gets_mod.gets_path(root)
    try:
        idiograph_routes.api_gets_cases({"workbook": any_book, "op": "colour", "case": "Tam", "colour": 20})
        first = gfile.read_bytes()
        taken = refusal_of(lambda: idiograph_routes.api_gets_cases({"workbook": any_book, "op": "colour", "case": "Ivo", "colour": 20}))
        own = refusal_of(lambda: idiograph_routes.api_gets_cases({"workbook": any_book, "op": "colour", "case": "Ivo", "colour": 0}))
        check("239: in the app, More colours' 21st is kept, and a colour another participant has, his choice or theirs by "
              "default, is refused with nothing written",
              json.loads(first)["colours"] == {"Tam": 20} and taken == gets_mod.TAKEN_COLOUR and own == gets_mod.TAKEN_COLOUR
              and gfile.read_bytes() == first, f"{taken} {own}")
        cfg_file = scratch / "toolbar-239-cli.json"
        cfg_file.write_text(json.dumps({"root": str(root), "interviewer": "Adam"}), encoding="utf-8")
        go = lambda *a: cli.run(["--root", str(root), "--config", str(cfg_file), "gets", "colour", *a])
        refused = go("Ivo", "Ocean", "--note", "Ocean for Ivo")
        dry = go("Ivo", "Fig", "--dry-run")
        after_dry = gfile.read_bytes()
        done = go("Ivo", "Fig", "--note", "Fig for Ivo", "--tool", "Claude Code")
        held = json.loads(gfile.read_text(encoding="utf-8"))["colours"]
        check("239: through the command line a taken colour is refused, a dry run writes nothing, and a free one by its "
              "name is kept as the picker keeps it",
              refused[0] != 0 and "Tam's colour" in refused[1] + refused[2] and dry[0] == 0 and "Dry run" in dry[1]
              and after_dry == first and done[0] == 0 and held == {"Tam": 20, "Ivo": 24}, f"{refused} {dry} {done} {held}")

        # ── F. the board's operations: arrange with a way, align and spread, dry run first
        cards = themes_mod.read_cards(books["Isla"])["cards"]
        keys = [c["key"] for c in cards]
        board = themes_mod.blank_version(cards)
        board.update(id="v1", name="Board 1", groups=[
            {"id": "g1", "label": "Digging before work", "members": keys[0:4], "x": 0, "y": 0}])
        themes_mod.write(books["Isla"], {"schema": 2, "case": "Isla", "workbook": books["Isla"].name, "current": "v1",
                                         "boards": [board]})
        stored = themes_mod.load(books["Isla"])
        ops = scratch / "toolbar-239-ops.json"
        ops.write_text(json.dumps({"operations": [{"op": "arrange", "label": "g1", "way": "column"},
                                                  {"op": "align", "items": ["S1", "S2"], "to": "right"}]}), encoding="utf-8")
        run = lambda *a: cli.run(["--root", str(root), "--config", str(cfg_file), "board", "apply", "Isla", "v1", "--ops", str(ops), *a])
        dry = run("--dry-run")
        unchanged = themes_mod.load(books["Isla"]) == stored
        made = run("--note", "Tidy the digging", "--tool", "Claude Code")
        now = themes_mod.current_version(themes_mod.load(books["Isla"]))
        xs = [now["cards"][k]["x"] for k in keys[0:4]]
        rights = {now["cards"][k]["x"] for k in keys[0:2]}
        bad = scratch / "toolbar-239-bad.json"
        bad.write_text(json.dumps({"operations": [{"op": "align", "items": ["S1", "S2"], "to": "sideways"},
                                                  {"op": "spread", "items": ["S1", "S2"], "to": "across"}]}), encoding="utf-8")
        before_bad = themes_mod.load(books["Isla"])
        wrong = cli.run(["--root", str(root), "--config", str(cfg_file), "board", "apply", "Isla", "v1", "--ops", str(bad), "--note", "x"])
        check("239: board apply arranges a label's cards a way and aligns cards, its dry run writing nothing, the change "
              "one step in History; a way Align has not and a Spread of two are refused whole",
              dry[0] == 0 and "Dry run" in dry[1] and "as a column" in dry[1] and unchanged
              and made[0] == 0 and len(set(xs)) == 1 and len(rights) == 1 and "aligned" in made[1].lower()
              and wrong[0] != 0 and themes_mod.load(books["Isla"]) == before_bad and "sideways" in wrong[1] + wrong[2]
              and "3 or more" in wrong[1] + wrong[2], f"{dry} {made} {wrong} {xs}")
    finally:
        server_mod.ROOT_OVERRIDE, server_mod.STATE_PATH, server_mod.STATE_MEMORY = saved
