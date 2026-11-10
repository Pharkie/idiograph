"""Area 185: what polish 8 and the sixth Tauri build left (18 October).

The board's map after Fit all, where the view's box ran past the map on every side and washed the whole
of it with no edge: the board and the view fitted together so the box stands whole inside the map, and
the box drawn as the transcript's minimap draws its own. A sticky note there already whose words grow
over a card moves clear as he types, as a new one does. What's new's line at the foot leaves the home
screen room, so Add transcripts at 360 scrolls clear above it. Every board here is invented, on keeping
bees.
"""
from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path

from . import support
from .support import check, skip


def test_polish_nine(scratch):
    print("\n185. Polish after polish 8 and the sixth Tauri build, 18 October: the board's map after Fit all drawing "
          "the view's box whole, and a sticky note there already moving clear as its words grow")
    read = lambda path: Path(path).read_text(encoding="utf-8")
    app, themes_js = support.text("family/static/shell.js", "apps/idiograph/static/distil.js"), support.text("apps/idiograph/static/themes.js")
    node = shutil.which("node")
    if not node:
        skip("185: the board's map and a sticky note in node", "node is not on this machine")
        return

    def whole(src, name):
        """A function of a script whole, or "" when there is none."""
        if f"function {name}(" not in src:
            return ""
        at = src.index(f"function {name}(")
        return src[at:src.index("\n}", at) + 2]

    line = lambda src, start: start + src.split(start, 1)[1].split("\n", 1)[0] if start in src else ""

    def run_node(name, code):
        script = scratch / name
        script.write_text(support.i18n_js() + code, encoding="utf-8")
        done = subprocess.run([node, str(script)], capture_output=True, text=True, encoding="utf-8", timeout=120)
        try:
            return json.loads(done.stdout) if done.returncode == 0 and done.stdout.strip() else {}, done
        except ValueError:
            return {}, done

    # ── 1. the board's map after Fit all: the board and the view fitted together, the box whole and clear
    code = MAP_STUBS + "\n".join([whole(app, "minimapMode"), line(app, "const MINIMAP_AWAKE = "),
                                  line(app, "const mmPx = ")]) + "\n" + themes_js + MAP_SCENARIO
    o, done = run_node("map-185.js", code)
    fa = o.get("fitAll", {})
    check("185: in node, after Fit all on a board of 2,400 by 1,000 the box that ran past the map on every side "
          "stands whole inside it, 6 pixels in from its top and its foot, centred across, the board inside the box as "
          "the canvas shows it, and the box shows the marks drawn again for that fit",
          fa.get("wasPast") == [True, True, True, True] and fa.get("inside") is True and fa.get("pad") == [6, 6]
          and fa.get("centred") == 0 and fa.get("boardInBox") is True and fa.get("redrawn") is True
          and fa.get("smaller") is True, json.dumps(fa)[:400])
    pan = o.get("pan", {})
    check("185: in node, a view inside the board keeps the board's own fit, a pan there leaving the marks as they "
          "were written, a view past one edge alone keeps it too and is cut by the map, and a pan of a view holding "
          "the whole board carries the marks with it inside a box that stands still",
          pan.get("inside") == {"same": True, "kept": True} and pan.get("edge") == {"same": True, "cut": True}
          and pan.get("whole") == {"boxStill": True, "moved": True}, json.dumps(pan)[:400])
    dr = o.get("drag", {})
    check("185: in node, a drag on the box of a view holding the whole board keeps the fit it started at, the "
          "place under the pointer kept under it, and as it ends the fit comes back round the view",
          dr.get("held") is True and dr.get("under") == dr.get("underWanted") and dr.get("asked") is True
          and dr.get("back") is True, json.dumps(dr)[:400])

    # ── 2. a sticky note there already moves clear as its words grow
    o, done = run_node("sticky-185.js", STICKY_STUBS + themes_js + STICKY_SCENARIO)
    s = o.get("sticky", {})
    check("185: in node, a note there already 50 pixels over a card stays while its words fit, and as they grow "
          "over the card it moves clear of it as he types, alone, the card where it stood, its words still open",
          s.get("short") == {"y": 100, "moved": False} and s.get("grown", {}).get("clear") is True
          and s.get("grown", {}).get("moved") is True and s.get("grown", {}).get("card") == [0, 200]
          and s.get("grown", {}).get("open") is True, json.dumps(s)[:400])
    check("185: in node, words typed and taken back after the note moved still make one step of undo, Edited a "
          "sticky note, and a note opened and closed untouched makes none",
          s.get("kept") == ["Edited a sticky note"] and s.get("untouched") == [], json.dumps(s)[:300])


MAP_STUBS = r"""
const ELS = {};
class El {
  constructor(id) {
    this.id = id; this.cls = new Set(); this.attrs = {}; this.hidden = false; this.writes = 0; this.html = '';
    this.captured = []; this.rect = { left: 0, top: 0, width: 0, height: 0, right: 0, bottom: 0 };
    const self = this;
    this.style = { props: {}, setProperty: (k, v) => { self.style.props[k] = v; } };
    this.classList = { add: (...n) => n.forEach((x) => self.cls.add(x)), remove: (...n) => n.forEach((x) => self.cls.delete(x)),
      contains: (n) => self.cls.has(n),
      toggle: (n, on) => { if (on === undefined) on = !self.cls.has(n); if (on) self.cls.add(n); else self.cls.delete(n); return on; } };
  }
  get innerHTML() { return this.html; }
  set innerHTML(v) { this.writes += 1; this.html = v; }
  setAttribute(k, v) { this.attrs[k] = String(v); }
  setPointerCapture(p) { this.captured.push(p); }
  releasePointerCapture() {}
  getBoundingClientRect() { return this.rect; }
  querySelector() { return null; }
}
const $ = (id) => ELS[id] || null;
const esc = (s) => String(s).replace(/[&<>]/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;' }[c]));
const escAttr = (s) => esc(s).replace(/"/g, '&quot;');
const say = () => {};
globalThis.localStorage = { getItem: () => null, setItem: () => {} };
globalThis.window = { innerWidth: 1280, innerHeight: 800, matchMedia: () => ({ matches: false }) };
let FRAMES = [];
globalThis.requestAnimationFrame = (fn) => { FRAMES.push(fn); return FRAMES.length; };
globalThis.cancelAnimationFrame = () => {};
const flush = () => { let n = 0; while (FRAMES.length && n < 50) { const due = FRAMES; FRAMES = []; due.forEach((f) => f(0)); n += 1; } };
globalThis.setTimeout = () => 0;
globalThis.clearTimeout = () => {};
"""

MAP_SCENARIO = r"""
// the canvas 1200 by 700, the map's area 290 by 150 at 900, 500
for (const id of ['th-map', 'th-map-items', 'th-map-view', 'th-map-btn', 'themes', 'th-world', 'th-zoom-level']) ELS[id] = new El(id);
ELS['th-stage'] = Object.assign(new El('th-stage'), { clientWidth: 1200, clientHeight: 700 });
ELS['th-map-area'] = Object.assign(new El('th-map-area'), { clientWidth: 290, clientHeight: 150 });
ELS['th-map-area'].rect = { left: 900, top: 500, width: 290, height: 150, right: 1190, bottom: 650 };
thCorners = () => {};
const r2 = (v) => Math.round(v * 100) / 100;
const out = {};
// an invented board of hives, cards spread over 2,400 by 1,000
const card = (x, y) => ({ text: 'Smoke before opening the hive', time: '00:10', x, y });
const v = { cards: {}, groups: [], discarded: [], picks: {}, stickies: [], ai: { discarded: {} } };
for (let i = 0; i < 12; i += 1) v.cards[`h:${i}:0`] = card((i % 4) * 733, Math.floor(i / 4) * 460);
TH.v = v; TH.layout = thLayout(v, thSize, null); TH.live = true; TH.mode = 'pets'; TH.config = { minimap: 'on' };
const items = ELS['th-map-items'];
const board = () => thMapFit(thMapItems(v, TH.layout, thSize, null).all, 290, 150);
const fitAll = () => { const u = thUnion(thMapItems(v, TH.layout, thSize, null).all); const z = Math.min(1, (1200 - 112) / u.w, (700 - 112) / u.h);
  TH.view = { x: 600 - (u.x + u.w / 2) * z, y: 350 - (u.y + u.h / 2) * z, z }; };

// ── Fit all: the box on the board's own fit ran past every side, and now stands whole inside
fitAll();
const was = thMapBox(board(), thMapSeen(TH.view, 1200, 700));
thMapSchedule(); flush();
const box = TH.mapBox;
const u = thUnion(thMapItems(v, TH.layout, thSize, null).all);
const b0 = thMapToMap(TH.map, u.x, u.y); const b1 = thMapToMap(TH.map, u.x + u.w, u.y + u.h);
out.fitAll = { wasPast: [was.x < 0, was.y < 0, was.x + was.w > 290, was.y + was.h > 150],
  inside: box.x >= 0 && box.y >= 0 && box.x + box.w <= 290 && box.y + box.h <= 150,
  pad: [r2(box.y), r2(150 - box.y - box.h)], centred: r2(box.x - (290 - box.x - box.w)),
  boardInBox: b0.x > box.x && b0.y > box.y && b1.x < box.x + box.w && b1.y < box.y + box.h,
  redrawn: items.writes >= 1 && thMapSame(TH.mapDrawn, TH.map), smaller: TH.map.k < board().k };

// ── a view inside the board: the board's fit, a pan leaving the marks; a view past one edge: cut there
const p = {};
TH.view = { x: -800, y: -300, z: 1 }; thMapViewed(); flush();
let writes = items.writes;
TH.view = { x: -820, y: -310, z: 1 }; thMapViewed(); flush();
p.inside = { same: TH.map === TH.mapBoard, kept: items.writes === writes };
TH.view = { x: 300, y: -300, z: 1 }; thMapViewed(); flush();
p.edge = { same: TH.map === TH.mapBoard, cut: TH.mapBox.x < 0 && TH.mapBox.y > 0 };
// a view holding the whole board panned: the box stands still in the middle, the marks follow
TH.view = { x: 400, y: 200, z: 0.25 }; thMapViewed(); flush();
const still = Object.assign({}, TH.mapBox); writes = items.writes; const html = items.html;
TH.view = { x: 430, y: 210, z: 0.25 }; thMapViewed(); flush();
p.whole = { boxStill: r2(TH.mapBox.x) === r2(still.x) && r2(TH.mapBox.y) === r2(still.y), moved: items.writes === writes + 1 && items.html !== html };
out.pan = p;

// ── a drag on that box: the fit held, the place under the pointer kept, and asked for again at its end
const d = {};
const ev = (mx, my) => ({ button: 0, clientX: 900 + mx, clientY: 500 + my, pointerId: 7, preventDefault() {} });
const held = TH.map;
const bx = TH.mapBox.x + TH.mapBox.w / 2; const by = TH.mapBox.y + TH.mapBox.h / 2;
thMapDown(ev(bx, by)); thMapMove(ev(bx + 20, by + 9)); flush();
d.held = TH.map === held;
const at = thMapToBoard(TH.map, bx + 20, by + 9);
const seen = thMapSeen(TH.view, 1200, 700);
const grab = thMapToBoard(held, bx, by); const top = thMapSeen({ x: 430, y: 210, z: 0.25 }, 1200, 700);
d.under = [r2(at.x - seen.x), r2(at.y - seen.y)]; d.underWanted = [r2(grab.x - top.x), r2(grab.y - top.y)];
FRAMES = [];
thMapUp(ev(bx + 20, by + 9)); d.asked = FRAMES.length > 0; flush();
d.back = TH.map !== held && Math.abs(TH.mapBox.x - still.x) < 0.5 && Math.abs(TH.mapBox.y - still.y) < 0.5;
out.drag = d;
console.log(JSON.stringify(out));
"""

STICKY_STUBS = r"""
const $ = () => null; const esc = (s) => String(s); const escAttr = esc; const say = () => {};
globalThis.window = { innerWidth: 1280, innerHeight: 800, matchMedia: () => ({ matches: false }) };
globalThis.localStorage = { getItem: () => null, setItem: () => {} };
const HEARD = {};
globalThis.document = { createElement: () => ({ value: '', rows: 1, spellcheck: false, placeholder: '', setAttribute() {},
  addEventListener: (k, fn) => { HEARD[k] = fn; }, focus() {}, setSelectionRange() {} }), activeElement: null };
"""

STICKY_SCENARIO = r"""
const out = {};
const STEPS = [];
thMeasure = () => {}; thPlace = () => {}; thRender = () => {}; thTitleDone = () => {}; thNoteDone = () => {};
thDone = (before, what) => { STEPS.push(what); };
const card = (x, y) => ({ text: 'Smoke before opening the hive', time: '00:10', x, y });
const v = { cards: { 'h:1:0': card(0, 200), 'h:2:0': card(400, 0) }, groups: [], discarded: [], picks: {},
  stickies: [{ id: 'n1', text: 'Queen seen?', colour: 'yellow', x: 0, y: 100 }], ai: { discarded: {} } };
TH.v = v; TH.live = true; TH.busy = false; TH.layout = thLayout(v, thSize, null);
TH.sizes = { 'h:1:0': { w: 200, h: 80 }, 'h:2:0': { w: 200, h: 80 }, n1: { w: 120, h: 47 } };
const words = { textContent: '' };
TH.els = { stickies: { n1: { querySelector: () => words, classList: { add() {}, remove() {} }, insertBefore() {} } } };
const n = v.stickies[0];
const s = {};
// opened, a word added that still fits: it stays where it stands
thStickyEditOpen('n1');
TH.stickyEdit.box.value = 'Queen seen? Yes'; HEARD.input();
s.short = { y: n.y, moved: !!TH.stickyEdit.moved };
// the words grow it to 140 tall, over the card 50 pixels under its foot: it moves clear as he types
TH.sizes.n1 = { w: 160, h: 140 };
TH.stickyEdit.box.value = 'Queen seen? Yes, on the third frame, marked blue, and the brood looks even across both sides';
HEARD.input();
const clear = !thMeets({ x: n.x, y: n.y, w: 160, h: 140 }, { x: v.cards['h:1:0'].x, y: v.cards['h:1:0'].y, w: 200, h: 80 });
s.grown = { clear, moved: !!TH.stickyEdit.moved, card: [v.cards['h:1:0'].x, v.cards['h:1:0'].y], open: !!TH.stickyEdit };
// the words taken back to what they were and kept: the move is one step of undo all the same
TH.stickyEdit.box.value = 'Queen seen?';
thStickyEditDone(true);
s.kept = STEPS.slice();
// opened and closed untouched: nothing
STEPS.length = 0;
thStickyEditOpen('n1'); thStickyEditDone(true);
s.untouched = STEPS.slice();
out.sticky = s;
console.log(JSON.stringify(out));
"""
