"""Area 312: dragging into and out of PETs and sub-PETs, design A (Adam, 31 October 2026, by dialog after the
drag audit, `dragaudit`).

The audit's 46 drags on the demo board found statements working and every sub-PET or PET aimed at another PET
failing by eye: the PET it was aimed at ran 340 to 500 px out of the way as the frame of the PET left stretched
after its member, "Merge into" came and went, and a sub-PET let go in another PET's body only moved. Design A:
no PET or sub-PET moves out of the way while a drag lasts, only what is inside the one under the pointer makes
room, and that one is outlined in its tint. Let go inside a PET or sub-PET and what is dragged goes in at the
insertion line keeping its level, a sub-PET into a PET. Let go on a title and it goes one level under, a PET
becoming a sub-PET. A card's middle still stacks, Alt joins nothing, and the hot spot kept where a title stood
is gone. The drop settles the rest, nothing overlapping, and Undo takes it back in one step.

The checks run themes.js's own drag, thDragStart, thDragMove and thDragEnd, in node, with the quotes on cards off
and at Full, on an invented board about learning to keep bees: two PETs side by side, each with two sub-PETs.
The pointer steers at a title where it shows, as a person does. No timing and no pixel is pinned.
"""
from __future__ import annotations

import json
import shutil
import subprocess

from . import support
from .support import check, skip
from .a205_card_quotes_and_by_participant import STUBS

SCENARIO = r"""
(() => {
// the page's elements as the drag meets them: a label knows itself as the label, and the stage is the window
class N extends El {
  constructor(id) { super(id); this.near = {}; this.parentNode = { appendChild: () => {} }; this.firstElementChild = null; this._last = null; }
  get lastElementChild() { if (!this._last) this._last = new N('last'); return this._last; }
  closest(sel) { return this.near[sel] || null; }
  contains() { return true; }
  getBoundingClientRect() { return { left: 0, top: 0, right: 1280, bottom: 800, width: 1280, height: 800, x: 0, y: 0 }; }
}
// reduced motion, so what makes room is there at once and nothing waits on a frame
window.matchMedia = () => ({ matches: true });
globalThis.performance = globalThis.performance || { now: () => 0 };
for (const id of ['th-stage', 'th-merge', 'th-insert']) ELS[id] = new N(id);
thPlayerDraw = () => {}; thPanelFollow = () => {}; thDrawSel = () => {}; thSoon = () => {}; thMomentum = () => {};
thCorners = () => {}; thMapPlace = () => {}; thDrawCounts = () => {}; thTip = () => {}; thSideArm = () => {};
thUnderPlace = () => {}; thLinksDraw = () => {}; thMapMoved = () => {}; thTableSoon = () => {}; thStatusDraw = () => {};
const card = (text, x, y) => ({ x, y, text, time: '3:15', sheet: 'Initial' });
const board = () => ({
  cards: {
    a1: card('Smoke before the lid comes off', 0, 100), a2: card('A veil that never quite fits', 210, 100),
    a3: card('Holding a frame up to the light', 0, 260), a4: card('Eggs like grains of rice', 210, 260),
    b1: card('Sitting by the hive after work', 500, 100), b2: card('The hum changes when rain comes', 710, 100),
    b3: card('Counting them out in the morning', 500, 260), b4: card('Talking to them when no one hears', 740, 260),
  },
  groups: [
    { id: 'G1', label: 'Smoke and patience', members: ['S1', 'S2'], x: 0, y: 0 },
    { id: 'S1', label: 'The first sting', members: ['a1', 'a2'], x: 0, y: 0 },
    { id: 'S2', label: 'Reading the frames', members: ['a3', 'a4'], x: 0, y: 0 },
    { id: 'G2', label: 'The hive as company', members: ['S3', 'S4', 'b4'], x: 0, y: 0 },
    { id: 'S3', label: 'A warm evening hum', members: ['b1', 'b2'], x: 0, y: 0 },
    { id: 'S4', label: 'Counting the bees out', members: ['b3'], x: 0, y: 0 },
  ],
  discarded: [], stacks: {} });
const KEYS = ['a1', 'a2', 'a3', 'a4', 'b1', 'b2', 'b3', 'b4'];
let quotes = false;
const measure = () => {
  TH.sizes = {};
  for (const k of KEYS) TH.sizes[k] = { w: 200, h: 80 };
  for (const g of ['G1', 'S1', 'S2', 'G2', 'S3', 'S4']) TH.sizes[g] = { w: 160, h: 26 };
  TH.qfull = {}; TH.qextra = {}; TH.baseH = {};
  // at Full each card shows its whole quote, a few lines more
  if (quotes) for (const k of KEYS) { TH.qfull[k] = 150; TH.qextra[k] = 70; TH.sizes[k] = { w: 200, h: 150 }; }
};
thRender = () => { measure(); thStacksRoom(); TH.layout = thLayout(TH.v, thSize, null); };
const open = () => {
  TH.v = board(); TH.opened = new Set(); TH.shifts = []; TH.roomShown = null; TH.removed = new Set(); TH.undo = []; TH.redo = [];
  TH.live = true; TH.mode = 'pets'; TH.view = { x: 0, y: 0, z: 1 }; TH.stackable = true; TH.z = [];
  TH.sel = { cards: new Set(), groups: new Set(), stickies: new Set() };
  TH.els = { cards: {}, under: {}, labels: {}, frames: {}, stickies: {}, rails: {} };
  for (const k of KEYS) TH.els.cards[k] = new N(k);
  for (const g of TH.v.groups) {
    const l = new N(`label ${g.id}`); l.dataset.group = g.id; l.near['.th-label'] = l;
    TH.els.labels[g.id] = l; TH.els.frames[g.id] = new N(`frame ${g.id}`);
  }
  thRender();
  thPlace();
};
// what the pointer is over: a label as it shows, never one carried, and otherwise a body or the canvas
const BODY = new N('body');
document.elementFromPoint = (x, y) => {
  const d = TH.drag;
  for (const g of TH.v.groups) {
    if (d && d.moving.has(g.id)) continue;
    const l = TH.layout[g.id] && TH.layout[g.id].label;
    if (l && x >= l.x && x <= l.x + l.w && y >= l.y && y <= l.y + l.h) return TH.els.labels[g.id];
  }
  return BODY;
};
const where = () => ({ groups: Object.fromEntries(TH.v.groups.map((g) => [g.id, [...g.members]])),
  cards: Object.fromEntries(KEYS.map((k) => [k, [Math.round(TH.v.cards[k].x), Math.round(TH.v.cards[k].y)]])), stacks: JSON.stringify(TH.v.stacks || {}) });
const label = (g) => { const l = TH.layout[g].label; return { x: l.x, y: l.y, w: l.w, h: l.h }; };
const frame = (g) => { const f = TH.layout[g].frame; return { x: f.x, y: f.y, w: f.w, h: f.h }; };
// what is outside the one under the pointer and stands still: every label not carried where it stood, and every
// statement not carried and not directly in the PET or sub-PET making room where it stood
const still = (d, labels0, cards0) => {
  const room = d.hitNow && d.hitNow.group && d.hitNow.group === d.home ? d.home : null;
  const parents = thParents(TH.v);
  const out = [];
  for (const g of TH.v.groups) {
    if (d.moving.has(g.id)) continue;
    const l = TH.layout[g.id].label;
    if (Math.round(l.x) !== Math.round(labels0[g.id].x) || Math.round(l.y) !== Math.round(labels0[g.id].y)) out.push(g.id);
  }
  for (const k of KEYS) {
    if (d.moving.has(k) || (room && parents[k] === room)) continue;
    if (TH.v.cards[k].x !== cards0[k][0] || TH.v.cards[k].y !== cards0[k][1]) out.push(k);
  }
  return out;
};
// one drag as the page runs it: picked up at `from`, the pointer steering 8 px a move at where `aim` says, read
// live, and let go there, with or without Alt; what showed on the way and what the drop did
const drag = (item, from, aim, opts = {}) => {
  open();
  const before = where();
  const labels0 = Object.fromEntries(TH.v.groups.map((g) => [g.id, label(g.id)]));
  const cards0 = before.cards;
  TH.press = { item, x0: from.x, y0: from.y, add: false, alt: !!opts.alt };
  thDragStart();
  const d = TH.drag;
  let x = from.x, y = from.y;
  const moved = new Set();
  let merges = 0, wasMerge = false;
  for (let i = 0; i < 400; i += 1) {
    const to = aim();
    const dist = Math.hypot(to.x - x, to.y - y);
    if (dist < 1) break;
    const k = Math.min(1, 8 / dist);
    x += (to.x - x) * k; y += (to.y - y) * k;
    thDragMove({ clientX: x, clientY: y, altKey: !!opts.alt });
    for (const m of still(d, labels0, cards0)) moved.add(m);
    const merge = !ELS['th-merge'].hidden;
    if (merge !== wasMerge) merges += 1;
    wasMerge = merge;
  }
  const target = opts.target;
  const shown = { hit: d.hitNow, merge: ELS['th-merge'].hidden ? null : ELS['th-merge'].lastElementChild.textContent,
    line: !ELS['th-insert'].hidden, lineTint: !ELS['th-insert'].hidden && target ? String(ELS['th-insert'].className).includes(thTintClass(thTints(TH.v)[target])) : false,
    outlined: target ? TH.els.frames[target].cls.has('target') && TH.els.labels[target].cls.has('target') : false,
    stackOn: TH.stackAt || null };
  thDragEnd({ clientX: x, clientY: y, altKey: !!opts.alt });
  const parents = thParents(TH.v);
  const after = { parent: Object.fromEntries([...(opts.watch || [])].map((id) => [id, parents[id] || null])),
    top: opts.stacked ? thTopOf(TH.v, opts.stacked) : undefined, steps: TH.undo.length, what: TH.undo.length ? TH.undo[TH.undo.length - 1].what : null,
    clashes: thClashes(TH.v, thSize).length, lit: Object.values(TH.els.frames).some((f) => f.cls.has('target')) };
  thUndo(true);
  const back = where();
  after.undone = JSON.stringify(back) === JSON.stringify(before) && TH.undo.length === 0 && TH.redo.length === 1;
  return { moved: [...moved].sort(), merges, shown, after };
};
// where to grab and where to aim, read from the board as it shows now
const onLabel = (g) => () => { const l = TH.layout[g].label; return { x: l.x + Math.min(40, l.w / 2), y: l.y + l.h / 2 }; };
const grabLabel = (g) => { const l = TH.layout[g].label; return { x: l.x + 20, y: l.y + l.h / 2 }; };
const out = {};
for (const q of [false, true]) {
  quotes = q;
  const r = {};
  open();
  r.start = { clashes: thClashes(TH.v, thSize).length, gap: frame('G2').x - (frame('G1').x + frame('G1').w) };
  // the audit's three worst: a sub-PET onto another PET's title, a PET onto a PET's title, a sub-PET let go in
  // another PET's body
  open(); r.subTitle = drag({ kind: 'group', id: 'S1' }, grabLabel('S1'), onLabel('G2'), { watch: ['S1'], target: 'G2' });
  open(); r.petTitle = drag({ kind: 'group', id: 'G1' }, grabLabel('G1'), onLabel('G2'), { watch: ['G1'], target: 'G2' });
  open();
  const into = () => { const f3 = frame('S3'), f4 = frame('S4'); return { x: f4.x + f4.w + 6, y: Math.round((f3.y + f3.h + f4.y) / 2) }; };
  r.subBody = drag({ kind: 'group', id: 'S1' }, grabLabel('S1'), into, { watch: ['S1'], target: 'G2' });
  // a sub-PET onto another PET's sub-PET's title nests there, a group of the third level
  open(); r.subSub = drag({ kind: 'group', id: 'S1' }, grabLabel('S1'), onLabel('S3'), { watch: ['S1'], target: 'S3' });
  // a statement into a sub-PET at the line, and onto a card's middle to stack, as before
  open();
  const between = () => { const b1 = TH.v.cards.b1, b2 = TH.v.cards.b2; return { x: Math.round((b1.x + 200 + b2.x) / 2), y: Math.round(b1.y + 20) }; };
  r.esSub = drag({ kind: 'card', id: 'a3' }, { x: TH.v.cards.a3.x + 100, y: TH.v.cards.a3.y + 10 }, between, { watch: ['a3'], target: 'S3' });
  open();
  const middle = () => { const c = TH.v.cards.b3; return { x: c.x + 100, y: c.y + thSize('b3').h / 2 }; };
  r.esStack = drag({ kind: 'card', id: 'a4' }, { x: TH.v.cards.a4.x + 100, y: TH.v.cards.a4.y + 10 }, middle, { watch: ['a4'], stacked: 'a4' });
  // Alt joins nothing: a statement with Alt held on another PET's title comes out of its own onto the canvas
  open(); r.altTitle = drag({ kind: 'card', id: 'a1' }, { x: TH.v.cards.a1.x + 100, y: TH.v.cards.a1.y + 10 }, onLabel('G2'), { watch: ['a1'], target: 'G2', alt: true });
  out[q ? 'full' : 'off'] = r;
}
console.log(JSON.stringify(out));
})();
"""


def test_drag_design_a(scratch):
    print("\n312. Dragging into and out of PETs and sub-PETs, design A (Adam, 31 October): nothing moves out of the way, "
          "the one under the pointer outlined, in at the line keeping its level, one level under on a title")
    node = shutil.which("node")
    if not node:
        skip("312: the drag in node", "node is not installed")
        return
    js = support.text("apps/idiograph/static/themes.js")
    script = scratch / "drag-design-a-312.js"
    script.write_text(support.i18n_js() + STUBS + js + SCENARIO, encoding="utf-8")
    run = subprocess.run([node, str(script)], capture_output=True, text=True, encoding="utf-8", timeout=120)
    if run.returncode != 0:
        check("312: the drag runs in node", False, run.stderr.strip()[:800])
        return
    o = json.loads(run.stdout)
    body = lambda g: {"group": g, "frame": True, "body": True}
    title = lambda g: {"group": g, "onLabel": True}
    for q in ("off", "full"):
        r = o[q]
        check(f"312: quotes {q}, the invented board opens with its two PETs side by side and nothing overlapping",
              r["start"]["clashes"] == 0 and r["start"]["gap"] > 0, json.dumps(r["start"]))
        s = r["subTitle"]
        check(f"312: quotes {q}, a sub-PET steered onto another PET's title by eye joins it: the title never moves, Merge "
              "into shows once and stays, that PET outlined, and the drop makes it that PET's sub-PET",
              s["moved"] == [] and s["merges"] == 1 and s["shown"]["hit"] == title("G2")
              and s["shown"]["merge"] == "The hive as company" and s["shown"]["outlined"]
              and s["after"]["parent"] == {"S1": "G2"}, json.dumps(s)[:900])
        p = r["petTitle"]
        check(f"312: quotes {q}, a PET steered onto another PET's title by eye becomes its sub-PET, the title never moving "
              "and Merge into showing once",
              p["moved"] == [] and p["merges"] == 1 and p["shown"]["hit"] == title("G2") and p["shown"]["outlined"]
              and p["after"]["parent"] == {"G1": "G2"}, json.dumps(p)[:900])
        b = r["subBody"]
        check(f"312: quotes {q}, a sub-PET let go in another PET's body goes in as its sub-PET: that PET outlined and holding "
              "still, the insertion line in its tint, no Merge, and nothing outside it moving",
              b["moved"] == [] and b["merges"] == 0 and b["shown"]["hit"] == body("G2") and b["shown"]["outlined"]
              and b["shown"]["line"] and b["shown"]["lineTint"] and b["after"]["parent"] == {"S1": "G2"}, json.dumps(b)[:900])
        n = r["subSub"]
        check(f"312: quotes {q}, a sub-PET onto another PET's sub-PET's title goes one level under it, the title never moving",
              n["moved"] == [] and n["shown"]["hit"] == title("S3") and n["after"]["parent"] == {"S1": "S3"}, json.dumps(n)[:900])
        e = r["esSub"]
        check(f"312: quotes {q}, a statement let go between two statements of another PET's sub-PET goes in there, as "
              "before: the line in its tint, the sub-PET outlined, and nothing else moving",
              e["moved"] == [] and e["shown"]["hit"] == body("S3") and e["shown"]["line"] and e["shown"]["lineTint"]
              and e["shown"]["outlined"] and e["after"]["parent"] == {"a3": "S3"}, json.dumps(e)[:900])
        k = r["esStack"]
        check(f"312: quotes {q}, a statement let go on the middle of a card stacks under it, as before, nothing moving",
              k["moved"] == [] and k["shown"]["hit"] == {"stack": "b3"} and k["shown"]["stackOn"] == "b3"
              and k["after"]["top"] == "b3" and k["after"]["what"] == "Stacked a card", json.dumps(k)[:900])
        a = r["altTitle"]
        check(f"312: quotes {q}, with Alt held a title takes nothing: no Merge, nothing lit, and the drop takes the statement "
              "out of its PET onto the canvas",
              a["moved"] == [] and a["merges"] == 0 and a["shown"]["hit"] is None and not a["shown"]["outlined"]
              and a["after"]["parent"] == {"a1": None}, json.dumps(a)[:900])
        drops = [r[c]["after"] for c in ("subTitle", "petTitle", "subBody", "subSub", "esSub", "esStack", "altTitle")]
        check(f"312: quotes {q}, each drop is one step of undo, settles with nothing overlapping and nothing left lit, and "
              "Undo puts the whole board back in that one step",
              all(x["steps"] == 1 and x["clashes"] == 0 and not x["lit"] and x["undone"] for x in drops),
              json.dumps(drops)[:900])
