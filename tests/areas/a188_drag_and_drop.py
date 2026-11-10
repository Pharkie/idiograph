"""Area 188: a drag on the PETs and GETs boards smooth in WebKit, and a drop that merges only on a title strip
(18 October 2026).

Adam, about 17:35, in the Mac window: dragging even a few statements juddered and stuck. WebKit, the
window's engine, was poor on every build back to 14 October and Chromium smooth on all of them, so the
cause was WebKit's way with the board, not one commit: the lean's rotate transition begun afresh on every
move of every card dragged, every pointer move doing the whole step where Chromium hands the page one a
frame, and the board's map written whole each frame of a drag. Now a drag takes one step a frame, what is
dragged leans with no transition of its own, and the map moves only the marks that
moved and reads no layout until the drop.

Adam, about 18:20, from a drawing: with three levels of grouping a drag kept offering to merge when he only
meant to move or reorder inside a sub-PET. Now a drop in a theme's body moves, a line showing where it comes
in that theme's order, and a drop merges only on a theme's title strip, which reads "Merge into" and its
title while the drag is over it, at every level of nesting. Undo is as it was.

Adam, 19 October about 13:35, on the shots: a statement let go in ANOTHER PET's body went back into its own.
Now statements move into the innermost PET, sub-PET or group the pointer is in, at the line shown. A PET or
a sub-PET dragged still only moves there.

Adam, 31 October, by dialog after the drag audit (design A, area 312): no PET or sub-PET moves out of the way
while a drag lasts, the one under the pointer is outlined, and a sub-PET let go in a PET's body goes in, keeping
its level. The hot spot kept where a strip stood is gone.

The checks here pin behaviour, in node on an invented board about learning to swim as an adult: how often
the step and the map run, what a drop does to what holds what and to the order, and that undo puts it back.
No timing is pinned.
"""
from __future__ import annotations

import json
import shutil
import subprocess

from . import support
from .support import check, skip


def test_drag_and_drop(scratch):
    print("\n188. A drag smooth in WebKit, one step and one map a frame, and a drop that merges only on a title strip, "
          "18 October")
    js = support.text("apps/idiograph/static/themes.js")
    app = support.text("family/static/shell.js", "apps/idiograph/static/distil.js")
    # the minimap's setting and its pixel rounding, which the board's map shares with the transcript's, from app.js
    at = app.index("function minimapMode(")
    lifted = "\n".join([app[at:app.index("\n}", at) + 2]]
                       + [ln for ln in app.splitlines() if ln.startswith(("const MINIMAP_AWAKE = ", "const mmPx = "))])
    node = shutil.which("node")
    if not node:
        skip("188: the drag and the drop in node", "node is not installed")
        return
    script = scratch / "drag-and-drop-188.js"
    script.write_text(support.i18n_js() + STUBS + lifted + "\n" + js + SCENARIO, encoding="utf-8")
    run = subprocess.run([node, str(script)], capture_output=True, text=True, encoding="utf-8", timeout=120)
    if run.returncode != 0:
        check("188: the drag and the drop run in node", False, run.stderr.strip()[:600])
        return
    o = json.loads(run.stdout)

    q = o["queue"]
    check("188: in node, any number of pointer moves in one frame take one step of the drag, the latest, and the next "
          "frame takes the next",
          q["asked"] == 1 and q["before"] == [] and q["first"] == [40] and q["second"] == [40, 70], str(q))
    check("188: in node, letting go runs the move still waiting for its frame before the drop, once, and Alt takes it "
          "first too",
          q["up"] == [40, 70, 90, "end"] and q["upLeft"] == 0 and q["alt"] == [110] and q["stale"] == [], str(q))

    t = o["trail"]
    check("188: in node, what comes along with a label trails it, eased out, past half the way in about 50 ms and nine "
          "tenths in about 150, caught up at last, and at once with reduced motion",
          40 < t["at48"] < 80 and t["at144"] >= 90 and t["caught"] and t["calm"] == [100, -50], str(t))

    m = o["map"]
    check("188: in node, the map is drawn whole when the drag begins and then moves only the marks that moved, the "
          "card dragged and the frames of its sub-PET and its PET reaching out to it, reading no layout while the drag lasts",
          m["first"]["whole"] and m["step"] == {"whole": False, "writes": 3, "reads": 0, "fit": True}
          and m["still"] == {"whole": False, "writes": 0, "reads": 0}, str(m))
    check("188: in node, after the drop the map is drawn whole again and fitted to the board as it now stands",
          m["drop"]["whole"] and m["drop"]["reads"] > 0 and m["drop"]["refit"], str(m["drop"]))
    check("188: in node, with no sidebar open the map reads no place of its own to see whether one covers it",
          m["covered"] == {"rects": 0, "covered": False}, str(m["covered"]))

    d = o["drop"]
    body = lambda g: {"group": g, "frame": True, "body": True}
    check("188: in node, a statement dropped in its own sub-PET's body only moves: it stays in the sub-PET and comes "
          "in its order where it was let go, the line in the gap before the statement it now comes before",
          d["own"]["hit"] == body("S1") and d["own"]["home"] == "S1" and d["own"]["parent"] == "S1"
          and d["own"]["order"] == ["s:3:0", "s:1:0", "s:2:0"] and d["own"]["line"] == d["own"]["lineWanted"]
          and d["own"]["merge"] is False, str(d["own"]))
    shown = {"line": True, "tint": True, "leaving": True, "lit": True}
    check("188: in node, a statement let go in another sub-PET's body, or a group of the third level inside it, moves "
          "into the innermost one the pointer is in (19 October), the line inside it in its tint, the statement shown "
          "leaving its own, and that one lit, its frame outlined and its title tinted (31 October, design A)",
          d["sibling"] == {"hit": body("S2"), "home": "S2", "parent": "S2", "shown": shown}
          and d["deep"] == {"hit": body("G"), "home": "G", "parent": "G", "shown": shown}, str([d["sibling"], d["deep"]]))
    check("188: in node, one let go on the open canvas stays where it stood in the tree, one in no PET let go in a "
          "sub-PET's body comes into it, and with Alt held a body takes nothing, the statement coming out onto the canvas",
          d["canvas"]["hit"] is None and d["canvas"]["parent"] == "S1" and d["loose"] == {"hit": body("S1"), "parent": "S1"}
          and d["altBody"] == {"hit": None, "home": "", "parent": True, "left": ["s:2:0"]},
          str([d["canvas"], d["loose"], d["altBody"]]))
    check("188: in node, a sub-PET dropped in its sibling's body stays a sub-PET of its own PET, keeping its level "
          "(31 October, design A), its PET's own statements making room",
          d["sub"] == {"hit": body("P"), "home": "P", "parent": "P", "nested": False}, str(d["sub"]))
    check("188: in node, a drop on a title strip merges: a statement joins that sub-PET, a sub-PET nests in its "
          "sibling, at every level, the strip reading Merge into and the title",
          d["strip"]["hit"] == {"group": "S2", "onLabel": True} and d["strip"]["parent"] == "S2"
          and d["strip"]["shown"] == {"hidden": False, "title": "Kicking from the hip", "lit": True}
          and d["nest"] == {"parent": "S2", "depth": 2} and d["deepStrip"]["parent"] == "G", str([d["strip"], d["nest"]]))
    check("188: in node, the hot spot where a title strip stood is gone (31 October, design A): the strip holds still "
          "while the drag lasts, and a point with no strip under it goes by the body there",
          d["fled"] == {"hit": body("S2"), "still": True}, str(d["fled"]))
    check("188: in node, the strip says nothing over the theme that holds all that is dragged already, nor with Alt "
          "held over it, where the drop takes it out",
          d["ownStrip"] == {"merge": False, "hidden": True} and d["altOwn"] == {"home": "", "left": ["s:2:0"]}, str(d["ownStrip"]))
    check("188: in node, each drop is put back whole by the board as the drag began, what holds what and every place",
          d["undo"] == {"own": True, "sibling": True, "deep": True, "canvas": True, "strip": True, "nest": True}, str(d["undo"]))

    g = o["gets"]
    check("188: in node, on the GETs board the same: a PET's card dropped in a GET's body or on its strip joins that GET",
          g == {"body": "G1", "strip": "G2"}, str(g))


STUBS = r"""
// the page as the drag and the map meet it: elements that count what is written to them and what is read
const ELS = {};
let READS = 0; let RECTS = 0; let WRITES = 0; let WHOLE = 0;
class El {
  constructor(id) {
    this.id = id; this.cls = new Set(); this.attrs = {}; this.hidden = false; this._html = ''; this.textContent = '';
    this.dataset = {}; this.children = []; this.rect = { left: 0, top: 0, width: 0, height: 0, right: 0, bottom: 0 };
    const self = this;
    this.style = { props: {}, setProperty: (k, v) => { self.style.props[k] = v; } };
    Object.defineProperty(this.style, 'cssText', { set(v) { WRITES += 1; self.style._css = v; }, get() { return self.style._css; } });
    this.classList = { add: (...n) => n.forEach((x) => self.cls.add(x)), remove: (...n) => n.forEach((x) => self.cls.delete(x)),
      contains: (n) => self.cls.has(n),
      toggle: (n, on) => { if (on === undefined) on = !self.cls.has(n); if (on) self.cls.add(n); else self.cls.delete(n); return on; } };
  }
  set innerHTML(v) {
    this._html = v;
    if (this.id === 'th-map-items') { WHOLE += 1; this.children = (v.match(/<i /g) || []).map(() => new El('mark')); }
  }
  get innerHTML() { return this._html; }
  get lastElementChild() { if (!this._last) this._last = new El('last'); return this._last; }
  setAttribute(k, v) { this.attrs[k] = String(v); }
  getAttribute(k) { return this.attrs[k]; }
  getBoundingClientRect() { RECTS += 1; return this.rect; }
  querySelector() { return ELS.bar; }
  contains() { return true; }
  closest(sel) { return (this.near || {})[sel] || null; }
}
const $ = (id) => ELS[id] || null;
const esc = (s) => String(s).replace(/[&<>]/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;' }[c]));
const escAttr = (s) => esc(s).replace(/"/g, '&quot;');
const say = () => {};
globalThis.localStorage = { getItem: () => null, setItem: () => {} };
globalThis.window = { innerWidth: 1280, innerHeight: 800, matchMedia: () => ({ matches: false }) };
let FRAMES = []; let FID = 0;
globalThis.requestAnimationFrame = (fn) => { FID += 1; FRAMES.push({ fn, id: FID }); return FID; };
globalThis.cancelAnimationFrame = (id) => { FRAMES = FRAMES.filter((f) => f.id !== id); };
const frame = () => { const due = FRAMES; FRAMES = []; due.forEach((f) => f.fn(0)); return due.length; };
globalThis.setTimeout = () => 0;
globalThis.clearTimeout = () => {};
let UNDER = null;
globalThis.document = { elementFromPoint: () => UNDER };
"""

SCENARIO = r"""
const out = {};
const keep = (x) => JSON.parse(JSON.stringify(x));
for (const id of ['th-map', 'th-map-items', 'th-map-view', 'th-map-btn', 'themes', 'th-world', 'th-zoom-level', 'th-discard', 'th-merge', 'th-insert'])
  ELS[id] = new El(id);
ELS.bar = Object.assign(new El('bar'), { offsetWidth: 300 });
ELS['th-stage'] = new El('th-stage');
Object.defineProperty(ELS['th-stage'], 'clientWidth', { get() { READS += 1; return 1000; } });
Object.defineProperty(ELS['th-stage'], 'clientHeight', { get() { READS += 1; return 600; } });
ELS['th-map-area'] = new El('th-map-area');
Object.defineProperty(ELS['th-map-area'], 'clientWidth', { get() { READS += 1; return 290; } });
Object.defineProperty(ELS['th-map-area'], 'clientHeight', { get() { READS += 1; return 150; } });
thCorners = () => {};

// ── the drag's steps: many moves a frame make one step, the latest; letting go and Alt take the waiting one first
{
  const calls = [];
  thDragMove = (e) => calls.push(e.clientX);
  thDragEnd = () => calls.push('end');
  const d = { next: null, step: 0, moving: new Set(), alt: false };
  TH.drag = d; TH.press = null; TH.pan = null;
  for (const x of [10, 20, 30, 40]) thPointerMove({ clientX: x, clientY: 0 });
  const q = { asked: FRAMES.length, before: calls.slice() };
  frame(); q.first = calls.slice();
  thPointerMove({ clientX: 60, clientY: 0 }); thPointerMove({ clientX: 70, clientY: 0 });
  frame(); q.second = calls.slice();
  thPointerMove({ clientX: 90, clientY: 0 });
  thPointerUp({ pointerId: 1, clientX: 90, clientY: 0 });
  q.up = calls.slice(); q.upLeft = FRAMES.length;
  // Alt pressed with a move waiting: the move runs first, and what is left in the frame does nothing more
  calls.length = 0;
  const e = { next: null, step: 0, moving: new Set(), alt: false };
  TH.drag = e;
  thPointerMove({ clientX: 110, clientY: 0, altKey: false });
  thDragAlt(false);
  q.alt = calls.slice();
  calls.length = 0; frame(); q.stale = calls.slice();
  TH.drag = null;
  out.queue = q;
}

// ── what came along with a label trails it by about 140 ms, eased each frame, and at once with reduced motion
{
  const d = { dx: 100, dy: -50, trail: { x: 0, y: 0, t: 0, raf: 0 } };
  const xs = [];
  let t = 1000;
  thTrail(d, t);
  for (let i = 0; i < 12; i += 1) { t += 16; thTrail(d, t); xs.push(Math.round(d.trail.x)); }
  const calm = { dx: 100, dy: -50, trail: { x: 0, y: 0, t: 0, raf: 0 } };
  const was = window.matchMedia;
  window.matchMedia = () => ({ matches: true });
  thTrail(calm, 2000);
  window.matchMedia = was;
  out.trail = { at48: xs[2], at144: xs[8], caught: thTrail(d, t + 400) === false && d.trail.x === 100 && d.trail.y === -50,
    calm: [calm.trail.x, calm.trail.y] };
}

// an invented board: a PET with two sub-PETs, the first holding three statements, the second two and a group of the
// third level, and a card in no PET
const card = (x, y) => ({ x, y, text: 'Counting the lengths', time: '00:10' });
const board = () => {
  const v = { cards: { 's:1:0': card(0, 0), 's:2:0': card(210, 0), 's:3:0': card(420, 0), 't:1:0': card(0, 300), 't:2:0': card(210, 300),
    'u:1:0': card(0, 500), 'u:2:0': card(210, 500), 'k:1:0': card(1400, 0) }, groups: [], discarded: [], picks: {}, stickies: [] };
  const g = (members, label, id) => { const made = thMakeGroup(v, members, label); thGroup(v, made).id = id;
    for (const o of v.groups) o.members = o.members.map((m) => (m === made ? id : m)); return id; };
  g(['u:1:0', 'u:2:0'], 'The deep end', 'G');
  g(['s:1:0', 's:2:0', 's:3:0'], 'Floating at last', 'S1');
  g(['t:1:0', 't:2:0', 'G'], 'Kicking from the hip', 'S2');
  g(['S1', 'S2'], 'Water that holds her', 'P');
  return v;
};
const size = (id) => (thIsGroup(TH.v, id) ? { w: 160, h: 30 } : { w: 200, h: 80 });
const sizes = (v) => { const s = {}; for (const id of [...Object.keys(v.cards), ...v.groups.map((x) => x.id)]) s[id] = thIsGroup(v, id) ? { w: 160, h: 30 } : { w: 200, h: 80 }; return s; };

// ── the map: whole at the start, then only what moved, no layout read in the drag, whole and refitted after the drop
{
  const v = board();
  TH.v = v; TH.sizes = sizes(v); TH.live = true; TH.mode = 'pets'; TH.view = { x: 0, y: 0, z: 1 };
  TH.config = { minimap: 'on' }; TH.mapHand = ''; TH.mapMode = 'on';
  TH.layout = thLayout(v, thSize, null);
  TH.drag = null; TH.map = null; TH.mapStale = true; FRAMES = [];
  const look = () => ({ whole: WHOLE, writes: WRITES, reads: READS });
  const since = (a) => { const b = look(); return { whole: b.whole > a.whole, writes: b.writes - a.writes, reads: b.reads - a.reads }; };
  let a = look(); thMapSchedule(); frame(); const first = since(a);
  // a drag begins: the first frame of it, then a move of one card of a PET's sub-PET
  TH.drag = { moving: new Set(['k:1:0']), seen: null, alt: false };
  const fit = keep(TH.map);
  const seen = keep(v); seen.cards['s:3:0'].x = 2400;
  TH.drag.seen = seen; TH.layout = thLayout(seen, thSize, null);
  a = look(); thMapMoved(); frame(); const step = since(a);
  step.fit = JSON.stringify(TH.map) === JSON.stringify(fit);
  a = look(); thMapMoved(); frame(); const still = since(a); delete still.fit;
  // the drop
  v.cards['s:3:0'].x = 2400; TH.drag = null; TH.layout = thLayout(v, thSize, null);
  a = look(); thMapMoved(); frame(); const drop = since(a);
  drop.refit = JSON.stringify(TH.map) !== JSON.stringify(fit);
  RECTS = 0; const covered = thMapCovered();
  out.map = { first, step: { whole: step.whole, writes: step.writes, reads: step.reads, fit: step.fit },
    still: { whole: still.whole, writes: still.writes, reads: still.reads }, drop, covered: { rects: RECTS, covered } };
}

// ── the drop: a drag as the page runs it, the pointer over a point of the board, and the drop as thDragEnd makes it
const strip = (gid) => { const el = new El('label'); el.dataset.group = gid; el.near = { '.th-label': el }; return el; };
const body = () => { const el = new El('body'); el.near = {}; return el; };
const drag = (v, cards, groups, alt = false) => {
  TH.v = v; TH.sizes = sizes(v); TH.layout = thLayout(v, thSize, null);
  TH.els = { labels: {}, frames: {}, cards: {}, stickies: {} };
  for (const x of v.groups) { TH.els.labels[x.id] = new El('l'); TH.els.frames[x.id] = new El('f'); }
  const moving = thMoving(v, new Set(cards), new Set(groups));
  const starts = {};
  for (const it of moving) { const o = thIsGroup(v, it) ? thGroup(v, it) : v.cards[it]; starts[it] = { x: o.x, y: o.y }; }
  const parents = thParents(v);
  const nest = [...moving].some((it) => thIsGroup(v, it) && !moving.has(parents[it]));
  const only = moving.size > 0 && [...moving].every((it) => !!v.cards[it]);
  const d = { moving, starts, nest, cards: only, frames: thBodiesFor(v, moving, TH.layout), dx: 0, dy: 0, alt,
    before: thSnap(v, new Set()), was: thLabelBoxes(TH.layout), from: thSpots(v),
    slides: new Map(), seen: null, raf: 0, hitNow: null, next: null, step: 0, home: null, layout: null };
  TH.drag = d; TH.hoverAt = null;
  return d;
};
// the pointer at `pt` on the board, by default the middle of the first statement dragged as it now stands
const over = (d, dx, dy, under, pt) => {
  d.dx = dx; d.dy = dy; UNDER = under;
  const first = [...d.moving].find((it) => TH.v.cards[it]);
  const at = pt || (first && d.cards ? { x: d.starts[first].x + 100 + dx, y: d.starts[first].y + 40 + dy } : { x: 0, y: 0 });
  const hit = thTargetAt(at.x, at.y);
  thWay(d, hit);
  thHover(hit); thMergeShow(hit); thInsertShow(d);
  return hit;
};
const letGo = (d, hit) => {
  thPreview(TH.v, thSize, d, thWayHome(TH.v, d.moving, d.nest, hit, d.alt));
  const res = thDrop(TH.v, d.moving, hit && !hit.frame ? hit.group : null, hit && hit.frame ? hit.group : null, d.alt);
  thSettle(TH.v, thSize, d.moving, d.was, [], TH_PASSES, true);
  TH.drag = null;
  return res;
};
const same = (v, before) => { const now = keep(thSnap(v, new Set())); return JSON.stringify(now) === JSON.stringify(keep(before)); };
const drop = {};
TH.view = { x: 0, y: 0, z: 1 };
{
  // within its own sub-PET: s:3:0 let go before s:1:0 on their row, so it now reads first
  const v = board();
  const d = drag(v, ['s:3:0'], []);
  const hit = over(d, -630, 0, body(), { x: -12, y: 40 });
  const lay = d.layout;
  const s1 = thSolid(v, thSize, lay, 's:1:0');
  const line = thInsertAt(v, lay, d.moving, d.home, 3);
  const lineWanted = { x: s1.x - TH_MARGIN / 2 - 1.5, y: s1.y, w: 3, h: s1.h, along: false };
  const merge = !ELS['th-merge'].hidden;
  letGo(d, hit);
  drop.own = { hit, home: d.home, parent: thParents(v)['s:3:0'], order: thThemeOrder(v, 'S1', thLayout(v, thSize, null)), line, lineWanted, merge };
  thPut(v, d.before);
  drop.undo = { own: same(v, d.before) };
}
{
  // into the sibling sub-PET's body, into the group of the third level inside it, and out on the open canvas
  for (const [name, dx, dy] of [['sibling', 0, 300], ['deep', 0, 500], ['canvas', 1700, 0]]) {
    const v = board();
    const d = drag(v, ['s:2:0'], []);
    const hit = over(d, dx, dy, body());
    const line = thInsertAt(v, d.layout, d.moving, d.home, 3);
    const el = ELS['th-insert'];
    const f = d.home ? d.layout[d.home].frame : null;
    const inside = !!(line && f && line.x >= f.x && line.x + line.w <= f.x + f.w && line.y >= f.y && line.y + line.h <= f.y + f.h);
    const tint = d.home ? thTintClass(thTints(v)[d.home]) : '';
    const shown = { line: !el.hidden && inside, tint: !!tint && String(el.className || '').includes(tint), leaving: thLeavers(v, d.moving).has('s:2:0') && !!d.out,
      lit: Object.values(TH.els.labels).some((x) => x.cls.has('target')) };
    letGo(d, hit);
    drop[name] = { hit, home: d.home, parent: thParents(v)['s:2:0'], shown };
    thPut(v, d.before);
    drop.undo[name] = same(v, d.before) && thParents(v)['s:2:0'] === 'S1';
  }
  // a statement in no PET let go in a sub-PET's body comes into it
  const v = board();
  const d = drag(v, ['k:1:0'], []);
  const hit = over(d, -1400, 0, body());
  letGo(d, hit);
  drop.loose = { hit, parent: thParents(v)['k:1:0'] };
  // with Alt held a statement in another sub-PET's body comes out of its own, onto the canvas, as before
  const w = board();
  const e = drag(w, ['s:2:0'], [], true);
  const h2 = over(e, 0, 300, body());
  const res = letGo(e, h2);
  drop.altBody = { hit: h2, home: e.home, parent: thParents(w)['s:2:0'] === undefined, left: res.left };
}
{
  // a sub-PET over its sibling's body
  const v = board();
  const d = drag(v, [], ['S1']);
  const hit = over(d, 0, 300, body());
  letGo(d, hit);
  drop.sub = { hit, home: d.home, parent: thParents(v).S1, nested: thParents(v).S1 === 'S2' };
}
{
  // on the sibling's title strip: Merge into and its title, and the drop joins
  const v = board();
  const d = drag(v, ['s:2:0'], []);
  const hit = over(d, 0, 260, strip('S2'));
  const m = ELS['th-merge'];
  const shown = { hidden: m.hidden, title: m.lastElementChild.textContent, lit: TH.els.labels.S2.cls.has('target') };
  letGo(d, hit);
  drop.strip = { hit, parent: thParents(v)['s:2:0'], shown };
  thPut(v, d.before);
  drop.undo.strip = same(v, d.before) && thParents(v)['s:2:0'] === 'S1';
  // a sub-PET on its sibling's strip nests there, two levels down
  const w = board();
  const e = drag(w, [], ['S1']);
  const h2 = over(e, 0, 260, strip('S2'));
  letGo(e, h2);
  drop.nest = { parent: thParents(w).S1, depth: thAncestors(w, 'S1').length };
  thPut(w, e.before);
  drop.undo.nest = same(w, e.before) && thParents(w).S1 === 'P';
  // a statement on the strip of the group of the third level joins it
  const x = board();
  const f = drag(x, ['s:1:0'], []);
  const h3 = over(f, 0, 460, strip('G'));
  letGo(f, h3);
  drop.deepStrip = { parent: thParents(x)['s:1:0'] };
}
{
  // no hot spot where a strip stood (31 October, design A): titles hold still, so a point where one stood with no
  // label under the pointer goes by the body there, and the strip itself never moves while the drag lasts
  const v = board();
  const d = drag(v, ['s:2:0'], []);
  const b = d.was.S2;
  d.dx = 0; d.dy = 260; UNDER = body();
  drop.fled = { hit: thTargetAt(b.x + b.w / 2, b.y + b.h / 2) };
  over(d, 0, 260, body(), { x: b.x + b.w / 2, y: b.y + b.h / 2 });
  drop.fled.still = d.layout.S2.label.x === b.x && d.layout.S2.label.y === b.y;
  TH.drag = null;
}
{
  // its own sub-PET's strip: nothing to merge, and with Alt held there the drop takes it out
  const v = board();
  const d = drag(v, ['s:2:0'], []);
  const hit = over(d, 0, -40, strip('S1'));
  drop.ownStrip = { merge: thMergeInto(v, d.moving, 'S1'), hidden: ELS['th-merge'].hidden };
  TH.drag = null;
  const w = board();
  const e = drag(w, ['s:2:0'], [], true);
  const h2 = over(e, 0, -40, strip('S1'));
  const res = letGo(e, h2);
  drop.altOwn = { home: e.home, left: res.left };
}
out.drop = drop;

// ── the GETs board: the same rule, a PET's card on a GET
{
  TH.mode = 'gets';
  const v = { cards: { 'Ada/pet/g1': card(0, 0), 'Bo/pet/g2': card(0, 300), 'Bo/pet/g3': card(800, 0) }, groups: [], discarded: [], picks: {}, stickies: [] };
  const one = thMakeGroup(v, ['Ada/pet/g1'], 'Water that holds her');
  thGroup(v, one).id = 'G1';
  const two = thMakeGroup(v, ['Bo/pet/g2'], 'The deep end');
  thGroup(v, two).id = 'G2';
  const before = keep(v);
  const d = drag(v, ['Bo/pet/g3'], []);
  const onStrip = over(d, -800, 260, strip('G2'));
  letGo(d, onStrip);
  const stripParent = thParents(v)['Bo/pet/g3'];
  const w = keep(before);
  const e = drag(w, ['Bo/pet/g3'], []);
  const inBody = over(e, -800, 0, body());
  letGo(e, inBody);
  out.gets = { body: thParents(w)['Bo/pet/g3'], strip: stripParent };
  TH.mode = 'pets';
}
console.log(JSON.stringify(out));
"""
