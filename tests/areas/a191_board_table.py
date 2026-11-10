"""Area 191: the PETs and GETs boards as two views, Canvas and Table, the table editable (19 October 2026).

Adam, 18 October about 18:00, in the window app, from a drawing: no export window. Each board's bar has
Canvas and Table, two views of one board, always in step, the choice kept for each board across a restart.
The table is the book's table of PETs, live, and editable: a grip on every row to reorder it, the letters
following, the canvas moving its cards to match, a title renamed in place, and a statement moved into another
PET or sub-PET, each the board's own change, saved as the canvas saves, on the same undo. A reorder goes
through the server's `themes.reorder`, the one an agent's `order` op runs, so the two clients set an order
the same way.

The checks pin behaviour, on an invented board about learning to swim as an adult: in node, the page's own
code with the server's route answering each reorder, the order, the letters and the places saved after a
reorder, a rename and a move, undo after each, a change on the canvas reaching the table, the view kept, and
Export's table printing at once where its window stood. No string, colour or pixel is pinned.
"""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys

from . import support
from .support import TOOL, check, skip
import idiograph_routes

# a board about learning to swim: PET g1 holding sub-PETs g2 and g3 and a statement of its own, g3 holding
# a group g4, PETs g5 and g6 beside it, and two statements in no PET
CARDS = {
    "Initial:3:0": (40, 120, "Floating once the teacher let go"),
    "Initial:5:0": (270, 120, "The water holding me, not her"),
    "Initial:7:0": (40, 360, "Trusting the water more than my arms"),
    "Initial:9:0": (60, 520, "Hating the deep end for years"),
    "Initial:11:0": (290, 520, "Swallowing water and laughing"),
    "Initial:13:0": (40, 720, "Kicking and going nowhere"),
    "Initial:15:0": (700, 80, "Counting strokes to stay calm"),
    "Initial:17:0": (930, 80, "Breathing out under the water"),
    "Initial:19:0": (700, 220, "Being the oldest in the class"),
    "Initial:21:0": (1300, 80, "Wanting to give up in week two"),
    "Initial:23:0": (1300, 220, "A length without stopping"),
    "Initial:25:0": (700, 900, "The smell of chlorine on the bus"),
    "Initial:27:0": (930, 900, "Goggles fogging and not minding"),
}
GROUPS = [
    {"id": "g1", "label": "Learning to trust the water", "members": ["g2", "g3", "Initial:13:0"], "x": 20, "y": 20},
    {"id": "g2", "label": "Held, then let go", "members": ["Initial:3:0", "Initial:5:0"], "x": 40, "y": 80},
    {"id": "g3", "label": "Breath and panic", "members": ["Initial:7:0", "g4"], "x": 40, "y": 320},
    {"id": "g4", "label": "Water in the mouth", "members": ["Initial:9:0", "Initial:11:0"], "x": 60, "y": 480},
    {"id": "g5", "label": "Doing it in front of others", "members": ["Initial:15:0", "Initial:17:0", "Initial:19:0"], "x": 700, "y": 40},
    {"id": "g6", "label": "Telling people I can swim", "members": ["Initial:21:0", "Initial:23:0"], "x": 1300, "y": 40},
]

# the server's route, run for each reorder the page asks, so node meets the real answer
ROUTE = r"""
import json, sys
sys.path.insert(0, sys.argv[1])
import boot
boot.setup()
import idiograph_routes
print(json.dumps(idiograph_routes.api_board_order(json.loads(sys.stdin.read()))))
"""


def test_board_table(scratch):
    print("\n191. Canvas and Table, two views of one board: a reorder, a rename and a move in the table, each saved and "
          "undone, a change on the canvas in the table, the view kept, and Export's table printed at once, 19 October")
    import server as server_mod
    import themes

    board = {"id": "v1", "name": "Board 1", "note": "", "created": "2026-10-19T10:00:00+01:00",
             "updated": "2026-10-19T10:00:00+01:00", "discarded": [], "picks": {}, "notes": [],
             "cards": {k: {"x": x, "y": y, "text": t} for k, (x, y, t) in CARDS.items()},
             "groups": json.loads(json.dumps(GROUPS))}
    tall = {k: 80 for k in CARDS}

    # ── the route alone: the table's reorder is the agents' order, nothing written
    asked = {"version": board, "under": "g1", "items": ["g3", "g2"], "heights": tall}
    got = idiograph_routes.api_board_order(json.loads(json.dumps(asked)))
    agent, info = themes.reorder(json.loads(json.dumps(board)), "g1", ["g3", "g2"], height=lambda k, _t: tall[k])
    landed = json.loads(json.dumps(board))
    for k, at in got["cards"].items():
        landed["cards"][k].update(at)
    for g in landed["groups"]:
        g.update(got["groups"][g["id"]])
    check("191: the route sets the order under a label as an agent's order op sets it, the same places for every card "
          "and label, and the board then reads in the new order",
          {k: (c["x"], c["y"]) for k, c in agent["cards"].items()} == {k: (a["x"], a["y"]) for k, a in got["cards"].items()}
          and themes.order_of(themes.normalise(landed), "g1") == ["g3", "g2", "Initial:13:0"] == got["order"]
          and info["order"] == got["order"], json.dumps(got)[:400])
    top = idiograph_routes.api_board_order(json.loads(json.dumps(dict(asked, under=None, items=["g6", "g1", "g5"]))))
    check("191: under none it sets the PETs' order, and a label the board no longer holds is refused",
          top["order"] == ["g6", "g1", "g5"] and _refused(server_mod, dict(asked, under="g9")), str(top["order"]))

    node = shutil.which("node")
    if not node:
        skip("191: the table in node", "node is not installed")
        return
    route = scratch / "board-table-route-191.py"
    route.write_text(ROUTE, encoding="utf-8")
    js = support.text("apps/idiograph/static/themes.js")
    script = scratch / "board-table-191.js"
    script.write_text(support.i18n_js() + STUBS + js + SCENARIO, encoding="utf-8")
    env = dict(os.environ, BT_PY=sys.executable, BT_ROUTE=str(route), BT_TOOL=str(TOOL), BT_BOARD=json.dumps(board))
    run = subprocess.run([node, str(script)], capture_output=True, text=True, encoding="utf-8", timeout=180, env=env)
    if run.returncode != 0:
        check("191: the table runs in node", False, (run.stderr or run.stdout).strip()[:900])
        return
    o = json.loads(run.stdout)

    first = o["first"]
    check("191: in node, the table sets out the PETs in canvas order, lettered A, A1, A1.1, each label's statements "
          "and labels in the order the canvas reads them, then the statements in no PET",
          first["codes"] == ["A", "A1", "A2", "A2.1", "B", "C"] and first["loose"] == ["Initial:25:0", "Initial:27:0"]
          and first["under"]["g1"] == ["g2", "g3", "Initial:13:0"], str(first))

    r = o["reorder"]
    check("191: in node, a sub-PET dragged above the one before it in the table takes its letter, A2 becoming A1, the "
          "canvas reads the new order, one request to the route with the board as the page holds it",
          r["codes"]["g3"] == "A1" and r["codes"]["g2"] == "A2" and r["canvas"] == ["g3", "g2", "Initial:13:0"]
          and r["asked"] == {"path": "/api/board-order", "under": "g1", "items": ["g3", "g2", "Initial:13:0"]}, str(r))
    check("191: in node, the places the reorder came back with are the board's saved places, a save on its way and one "
          "step of undo",
          r["saved"] and r["dirty"] and r["steps"] == 1 and r["moved"] > 0, str(r))
    check("191: in node, undo puts the reorder back, the order, the letters and every place",
          r["undone"] == {"codes": True, "places": True}, str(r["undone"]))
    k = o["keys"]
    check("191: in node, Alt with the arrow down on a PET's grip moves it one place down among the PETs, and back up",
          k["down"] == ["g5", "g1", "g6"] and k["up"] == ["g1", "g5", "g6"], str(k))

    n = o["rename"]
    check("191: in node, a title renamed in the table is the board's title, saved, one step of undo, and undo gives the "
          "old one back",
          n["label"] == "Swimming with others watching" and n["saved"] == n["label"] and n["dirty"] and n["steps"] == 1
          and n["undone"] == "Doing it in front of others", str(n))

    m = o["move"]
    check("191: in node, a statement dragged from one PET into another goes into it at the place it was let go, leaves "
          "the one it was in, is saved, and is one step of undo",
          m["parent"] == "g5" and m["at"] == 1 and m["left"] and m["saved"] and m["steps"] == 1, str(m))
    check("191: in node, undo takes the moved statement back into its own PET at its own place",
          m["undone"] == {"parent": "g6", "place": True}, str(m["undone"]))
    check("191: in node, one in no PET dragged into a sub-PET joins it",
          m["loose"] == "g4", str(m["loose"]))

    c = o["canvas"]
    check("191: in node, a change made on the canvas reaches the table on its next frame, with no refresh",
          c["before"] is False and c["after"] is True, str(c))

    f = o["face"]
    check("191: in node, the view is kept for each board: Table chosen on one board comes back after a restart, another "
          "board opens on the canvas, and Canvas chosen again is kept too",
          f == {"kept": "table", "other": "canvas", "back": "canvas"}, str(f))
    p = o["print"]
    check("191: in node, Export's table is printed at once, the print view opening with its dialog, where its window "
          "stood for reading",
          p["auto"] == "1" and p["board"] == "v1", str(p))


def _refused(server_mod, body) -> bool:
    from workbook import WorkbookError
    try:
        idiograph_routes.api_board_order(json.loads(json.dumps(body)))
    except WorkbookError:
        return True
    return False


STUBS = r"""
// the page as the table meets it: any element asked for is made on the way, and the canvas itself is never booted
const { execFileSync } = require('child_process');
const ELS = {};
class El {
  constructor(id) {
    this.id = id; this.cls = new Set(); this.attrs = {}; this.hidden = false; this._html = ''; this.textContent = '';
    this.dataset = {}; this.children = []; this.value = ''; this.scrollTop = 0; this.offsetWidth = 0; this.offsetHeight = 0;
    const self = this;
    this.style = { setProperty: () => {} };
    this.classList = { add: (...n) => n.forEach((x) => self.cls.add(x)), remove: (...n) => n.forEach((x) => self.cls.delete(x)),
      contains: (n) => self.cls.has(n),
      toggle: (n, on) => { if (on === undefined) on = !self.cls.has(n); if (on) self.cls.add(n); else self.cls.delete(n); return on; } };
  }
  set innerHTML(v) { this._html = v; }
  get innerHTML() { return this._html; }
  setAttribute(k, v) { this.attrs[k] = String(v); }
  getAttribute(k) { return this.attrs[k]; }
  removeAttribute(k) { delete this.attrs[k]; }
  getBoundingClientRect() { return { left: 0, top: 0, width: 0, height: 0, right: 0, bottom: 0 }; }
  querySelector() { return null; }
  querySelectorAll() { return []; }
  addEventListener() {}
  contains() { return false; }
  closest() { return null; }
  focus() {}
  setSelectionRange() {}
}
const $ = (id) => (id === 'th-stage' ? null : (ELS[id] = ELS[id] || new El(id)));
const esc = (s) => String(s).replace(/[&<>]/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;' }[c]));
const escAttr = (s) => esc(s).replace(/"/g, '&quot;');
const SAID = [];
const say = (t) => SAID.push(t);
const MOD = (e) => !!(e.metaKey || e.ctrlKey);
const REDO_Y = () => false;
const RESTART_LINE = 'Restart';
const needsRestart = () => false;
const cheerOn = () => false;
const confetti = () => {};
const fileOf = (p) => String(p).split('/').pop();
// what the browser keeps, which a restart of the page finds again
const STORE = new Map();
globalThis.localStorage = { getItem: (k) => (STORE.has(k) ? STORE.get(k) : null), setItem: (k, v) => STORE.set(k, String(v)),
  removeItem: (k) => STORE.delete(k) };
const OPENED = [];
globalThis.window = { innerWidth: 1280, innerHeight: 800, matchMedia: () => ({ matches: true }),
  open: (url) => { OPENED.push(url); return { close() {}, location: {} }; } };
let FRAMES = [];
globalThis.requestAnimationFrame = (fn) => { FRAMES.push(fn); return FRAMES.length; };
globalThis.cancelAnimationFrame = () => {};
const frame = () => { const due = FRAMES; FRAMES = []; due.forEach((fn) => fn(0)); return due.length; };
globalThis.setTimeout = () => 0;
globalThis.clearTimeout = () => {};
globalThis.getComputedStyle = () => ({ getPropertyValue: () => '' });
globalThis.document = { activeElement: null };
// each reorder the page asks goes to the server's own route, run in Python
const ASKED = [];
const api = async (path, body) => {
  ASKED.push({ path, under: body.under, items: body.items });
  if (path !== '/api/board-order') throw new Error(`no ${path} here`);
  const out = execFileSync(process.env.BT_PY, [process.env.BT_ROUTE, process.env.BT_TOOL], { input: JSON.stringify(body), encoding: 'utf8' });
  return JSON.parse(out);
};
"""

SCENARIO = r"""
;(async () => {
  const out = {};
  const sheet = (k) => ({ sheet: 'Initial', row: Number(k.split(':')[1]), line: 0, time: '00:10', seconds: 10 });
  const fresh = () => {
    const b = JSON.parse(process.env.BT_BOARD);
    const cards = {};
    for (const [k, c] of Object.entries(b.cards)) cards[k] = Object.assign(sheet(k), c);
    TH.v = { cards, groups: b.groups, discarded: [], picks: {}, ai: { discarded: {} }, review: null, stickies: [], revise: null };
    TH.meta = { id: b.id, name: b.name, note: '', created: b.created, updated: b.updated };
    TH.path = 'Wren/Wren - EN & ES.xlsx';
    TH.live = true; TH.busy = false; TH.mode = 'pets'; TH.undo = []; TH.redo = []; TH.removed = new Set();
    TH.sel = { cards: new Set(), groups: new Set(), stickies: new Set() };
    TH.els = { cards: {}, labels: {}, frames: {}, stickies: {} };
    TH.project = { pet_labels: 'letters' }; TH.sheets = ['Initial']; TH.quotes = {};
    TH.dirty = false; TH.saveTimer = null; TH.chain = null;
    TH.z = Object.keys(cards);
    thRender();
  };
  // the canvas drawn as the page draws it, its cards and labels at the sizes it measures
  thMeasure = function () {
    TH.sizes = {};
    for (const k of Object.keys(TH.v.cards)) TH.sizes[k] = { w: 200, h: 80 };
    for (const g of TH.v.groups) TH.sizes[g.id] = { w: 140, h: 30 };
  };
  thRender = function () { thMeasure(); thPlace(); };
  // the minimap is not this area's
  thMapMoved = () => {};
  const codes = () => {
    const tree = thTableTree(TH.v, TH.layout, true, TH.sheets);
    const all = {};
    const walk = (n) => { all[n.id] = n.code; for (const it of n.items) if (it.kind === 'label') walk(it.node); };
    tree.pets.forEach(walk);
    return { all, tree };
  };
  const places = () => JSON.stringify(Object.entries(TH.v.cards).map(([k, c]) => [k, c.x, c.y]));
  const parentOf = (k) => thParents(TH.v)[k];

  fresh();
  const one = codes();
  const list = [];
  const walk = (n) => { list.push(n.code); for (const it of n.items) if (it.kind === 'label') walk(it.node); };
  one.tree.pets.forEach(walk);
  out.first = { codes: list, loose: one.tree.loose, under: { g1: thTableSiblings(TH.v, TH.layout, 'g1') } };

  // a reorder: A2 dragged above A1
  const was = places();
  ASKED.length = 0;
  thTablePut('g3', 'label', 'g1', 'g1', 0);
  await new Promise((r) => setImmediate(r));
  for (let i = 0; i < 20 && TH.busy; i += 1) await new Promise((r) => setImmediate(r));
  const now = codes();
  const body = thBody(TH.v, TH.meta);
  out.reorder = { codes: now.all, canvas: thThemeOrder(TH.v, 'g1', TH.layout), asked: ASKED[0] || null,
    saved: Object.entries(body.cards).every(([k, c]) => c.x === TH.v.cards[k].x && c.y === TH.v.cards[k].y) && places() !== was,
    dirty: TH.dirty, steps: TH.undo.length, moved: Object.keys(body.cards).filter((k) => JSON.stringify(JSON.parse(was).find((e) => e[0] === k)) !== JSON.stringify([k, body.cards[k].x, body.cards[k].y])).length };
  thUndo(true);
  out.reorder.undone = { codes: codes().all.g2 === 'A1' && codes().all.g3 === 'A2', places: places() === was };

  // Alt with an arrow, on a PET's grip
  const keyOn = async (id, key) => {
    const row = { dataset: { trow: id, tparent: '' } };
    const target = { closest: (sel) => (sel.includes('data-trow') ? row : sel === '.tb-grip' ? {} : null) };
    thTableKey({ altKey: true, key, target, preventDefault() {} });
    for (let i = 0; i < 20 && TH.busy; i += 1) await new Promise((r) => setImmediate(r));
    await new Promise((r) => setImmediate(r));
  };
  TH.face = 'table';
  fresh();
  await keyOn('g1', 'ArrowDown');
  out.keys = { down: thTableSiblings(TH.v, TH.layout, null) };
  await keyOn('g1', 'ArrowUp');
  out.keys.up = thTableSiblings(TH.v, TH.layout, null);

  // a rename in place
  fresh();
  thTableTitleOpen('g5');
  $('tb-title-box').value = 'Swimming with others watching';
  thTableTitleDone(true);
  out.rename = { label: thGroup(TH.v, 'g5').label, saved: thBody(TH.v, TH.meta).groups.find((g) => g.id === 'g5').label,
    dirty: TH.dirty, steps: TH.undo.length };
  thUndo(true);
  out.rename.undone = thGroup(TH.v, 'g5').label;

  // a statement moved from g6 into g5, before its second statement
  fresh();
  const home = thTableSiblings(TH.v, TH.layout, 'g6');
  thTablePut('Initial:21:0', 'statement', 'g6', 'g5', 1);
  for (let i = 0; i < 20 && TH.busy; i += 1) await new Promise((r) => setImmediate(r));
  await new Promise((r) => setImmediate(r));
  out.move = { parent: parentOf('Initial:21:0'), at: thTableSiblings(TH.v, TH.layout, 'g5').indexOf('Initial:21:0'),
    left: !thGroup(TH.v, 'g6').members.includes('Initial:21:0'),
    saved: thBody(TH.v, TH.meta).groups.find((g) => g.id === 'g5').members.includes('Initial:21:0'), steps: TH.undo.length };
  thUndo(true);
  out.move.undone = { parent: parentOf('Initial:21:0'), place: JSON.stringify(thTableSiblings(TH.v, TH.layout, 'g6')) === JSON.stringify(home) };
  thTablePut('Initial:25:0', 'statement', '', 'g4', 0);
  for (let i = 0; i < 20 && TH.busy; i += 1) await new Promise((r) => setImmediate(r));
  await new Promise((r) => setImmediate(r));
  out.move.loose = parentOf('Initial:25:0') || null;

  // a change on the canvas, a title renamed there, reaches the table on its next frame
  fresh();
  TH.face = 'table';
  frame();
  thTableDraw();
  const before = $('th-table').innerHTML.includes('A dive I nearly took');
  const prior = thSnap(TH.v, TH.removed);
  thGroup(TH.v, 'g6').label = 'A dive I nearly took';
  thDone(prior, 'Renamed a label', { settle: [], labels: ['g6'] });
  frame();
  out.canvas = { before, after: $('th-table').innerHTML.includes('A dive I nearly took') };

  // the view kept by board, across a restart
  fresh();
  TH.face = 'canvas';
  thFace('table');
  TH.face = 'canvas';
  thFaceRestore();
  const kept = TH.face;
  TH.meta = Object.assign({}, TH.meta, { id: 'v2' });
  thFaceRestore();
  const other = TH.face;
  TH.meta = Object.assign({}, TH.meta, { id: 'v1' });
  thFaceRestore();
  thFace('canvas');
  TH.face = 'table';
  thFaceRestore();
  out.face = { kept, other, back: TH.face };

  // Export's table, printed at once
  fresh();
  TH.printable = true;
  OPENED.length = 0;
  await thPrint();
  const url = new URL(OPENED[0] || '/none', 'http://127.0.0.1');
  out.print = { auto: url.searchParams.get('auto'), board: url.searchParams.get('board') };

  process.stdout.write(JSON.stringify(out));
})().catch((e) => { console.error(e.stack); process.exit(1); });
"""
