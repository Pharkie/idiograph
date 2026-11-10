"""Area 179: the minimap on the PETs and GETs boards (18 October, Adam's yes of 17 October).

Miro's and tldraw's way: a card above the zoom bar at the canvas's bottom right, the bar's width and
160 pixels high, the board fitted to every card on it, each card a small rectangle in its PET's tint,
on GETs in its participant's colour, every frame an outline, and the view a box in a solid line of the
ink with the rest dimmed, a light wash of the ink until area 185. A
click glides the view there, a drag on the box pans, the wheel reaches the canvas, and it is drawn at
most once a frame. The transcript's Auto, On and Off rule it, its button on the zoom bar and M show or
hide it, and below 768 pixels of window it goes. Every board here is invented, on learning to swim.
"""
from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path

from . import support
from .support import check, skip


def test_board_map(scratch):
    print("\n179. The minimap on the PETs and GETs boards, 18 October, Adam's yes of 17 October: a card over the zoom "
          "bar, the board fitted to every card in its tints or its participants' colours, the frames as outlines, the "
          "view a light wash, a click gliding there, a drag panning, the wheel reaching the canvas, once a frame, the "
          "transcript's Auto, On and Off, its button and M, and gone below 768 pixels. Since the test review of 18 "
          "October its place, size, colours and the fit's measurements are review shots, and what a click, a drag, the "
          "button, M and the setting do stays")
    read = lambda path: Path(path).read_text(encoding="utf-8")
    js, app = support.text("apps/idiograph/static/themes.js"), support.text("family/static/shell.js", "apps/idiograph/static/distil.js")

    def whole(src, name):
        """A function of a script whole, or "" when there is none."""
        if f"function {name}(" not in src:
            return ""
        at = src.index(f"function {name}(")
        return src[at:src.index("\n}", at) + 2]

    const = lambda src, name: next((ln for ln in src.splitlines() if ln.startswith(f"const {name} = ")), "")

    # ── B. the key and the button
    keydown = whole(js, "thKeyDown")
    boot = whole(js, "themesBoot")
    check("179: M on a board shows or hides the map as its button does, outside a field and with no modifier as H is, "
          "and its button leaves the focus on the canvas",
          "if (e.key === 'm' || e.key === 'M') { e.preventDefault(); thMapToggle(); return; }" in keydown
          and keydown.index("thHand(!TH.hand); return; }") < keydown.index("thMapToggle();") < keydown.index("if (TH.busy) return;")
          and keydown.index("if (MOD(e) || e.altKey || e.ctrlKey) return;") < keydown.index("thMapToggle();")
          and "$('th-map-btn').addEventListener('pointerdown', (e) => e.preventDefault());" in boot
          and "$('th-map-btn').onclick = () => thMapToggle();" in boot)
    # ── D. in node: the marks, the fit, the box, the frames, Auto, On and Off, the button and M, the glide and the drag
    node = shutil.which("node")
    if not node:
        skip("179: the board's map in node", "node is not installed")
    else:
        lifted = "\n".join([whole(app, "minimapMode"), const(app, "MINIMAP_AWAKE"), const(app, "mmPx")])
        script = scratch / "board-map-179.js"
        script.write_text(support.i18n_js() + STUBS + lifted + "\n" + js + SCENARIO, encoding="utf-8")
        run = subprocess.run([node, str(script)], capture_output=True, text=True, encoding="utf-8", timeout=120)
        if run.returncode != 0:
            check("179: the board's map runs in node", False, run.stderr.strip()[:600])
        else:
            o = json.loads(run.stdout)
            node_checks(o)


def node_checks(o: dict) -> None:
    items = o["items"]
    check("179: in node, the map lists every frame in its tint, a sub-theme's a step lighter, each sticky note on its "
          "paper, an unknown paper the first, and every card on the canvas, a discarded one left out, a card in a PET in "
          "its theme's own tint however deep it sits, one in none plain and one no longer in its workbook marked",
          items["frames"] == ["tm-frame hue-0", "tm-frame hue-2 step-1", "tm-frame hue-2"]
          and items["stickies"] == ["tm-sticky sticky-pink", "tm-sticky sticky-yellow"]
          and items["cards"] == {"a:1:0": "tm-card in hue-0", "a:2:0": "tm-card in hue-0", "a:3:0": "tm-card in hue-2",
                                 "a:4:0": "tm-card in hue-2", "a:5:0": "tm-card missing"}
          and items["all"] == 10 and items["gets"] == ["tm-card tm-case case-3", "tm-card tm-case case-6"], str(items))
    s = o["states"]
    check("179: in node, with Off nothing shows, the canvas loses the map's button, the corners measured again, and the "
          "button, M and a pan do nothing",
          s["off"] == {"shut": True, "off": True, "corners": 1, "hand": "", "awake": False, "pressed": "false"}, str(s["off"]))
    check("179: in node, with On the map shows, its button pressed, the marks and the box drawn, the button or M hides it "
          "until pressed again, and a new setting forgets what they said",
          s["on"] == {"shut": False, "off": False, "corners": 2, "pressed": "true", "marks": 10, "view": True}
          and s["onHidden"] == {"shut": True, "hand": "hide", "pressed": "false"} and s["onShown"] == {"shut": False, "hand": ""}
          and s["onChanged"]["hand"] == "", str([s["on"], s["onHidden"], s["onShown"]]))
    check("179: in node, a new Auto shows the map at once and lets it sleep two seconds later, a pan or a zoom wakes it "
          "again for two seconds, never sleeping under his pointer, its time starting again as the pointer leaves",
          s["autoChosen"] == {"shut": False, "awake": True} and s["autoTimers"] == [2000] and s["autoSlept"] == {"shut": True, "awake": False}
          and s["panned"] == {"shut": False, "awake": True} and s["over"] == {"timers": 0, "awake": True}
          and s["left"] == {"timers": [2000], "shut": True}, str([s["autoChosen"], s["autoTimers"], s["panned"], s["over"], s["left"]]))
    check("179: in node, in Auto the button or M shows a sleeping map until pressed again, through its two seconds, and "
          "while it shows hides it at once until the next pan or zoom",
          s["shown"] == {"shut": False, "hand": "show", "afterTime": False}
          and s["hidden"] == {"shut": True, "hand": "", "awake": False} and s["nextPan"] == {"shut": False, "awake": True}, str(s))
    check("179: in node, a sidebar open over the map gives it way, its button not pressed, and one hidden or beside the "
          "canvas leaves it be",
          s["covered"] == {"shut": True, "pressed": "false"} and s["uncovered"] is False and s["beside"] is False,
          str([s["covered"], s["uncovered"], s["beside"]]))
    check("179: in node, nothing shows and nothing is read before a board is on the canvas, at 767 pixels and below, "
          "or with nothing on the board to draw, and the button and M do nothing at the narrow width",
          s["notLive"] == {"shut": True, "reads": 0} and s["narrow"] == {"shut": True, "reads": 0, "hand": ""}
          and s["empty"] == {"shut": True, "marks": 0}, str([s["notLive"], s["narrow"], s["empty"]]))
    f = o["frames"]
    check("179: in node, any number of pans, zooms and moves in a frame draw the map once, a pan alone moving the box and "
          "leaving the marks, a move or a change of the card's size drawing the marks again, a drag drawn as it shows, "
          "and on GETs every card in its participant's colour",
          f["asked"] == 1 and f["kept"] and f["redrawn"] and f["resized"] and f["dragShown"] and f["gets"] == ["case-3", "case-6"]
          and f["width"] == "300px" and f["placeAsks"] == 1, str(f))
    a = o["acts"]
    check("179: in node, a click off the box glides the place pressed to the canvas's middle in about a quarter of a "
          "second, at once under reduced motion, a wander of a pixel or two leaves the glide alone, and a press of "
          "another button does nothing",
          a["click"]["captured"] == [3] and a["click"]["dragging"] and a["click"]["midway"] and a["click"]["landed"] == a["click"]["wanted"]
          and a["click"]["frames"] >= 3 and a["still"] == a["stillWanted"] and a["wander"] == a["wanderWanted"]
          and a["right"] == {"drag": None, "moved": False}, str(a["click"]))
    check("179: in node, a drag on the box pans the canvas at once, the place under the pointer kept under it, a drag "
          "after a click carries on from the place clicked, letting go ends it and starts Auto's time again, and any other "
          "move of the view ends a glide where it stands",
          a["box"] == a["boxWanted"] and a["carried"] == a["carriedWanted"] and a["up"] == {"drag": None, "dragging": False, "timers": [2000]}
          and a["stopped"] == a["stoppedWanted"], str([a["box"], a["boxWanted"], a["stopped"], a["stoppedWanted"]]))


STUBS = r"""
const ELS = {};
let NARROW = false; let REDUCED = false;
class El {
  constructor(id) {
    this.id = id; this.cls = new Set(); this.attrs = {}; this.hidden = false; this.innerHTML = ''; this.textContent = '';
    this.captured = []; this.released = []; this.rect = { left: 0, top: 0, width: 0, height: 0, right: 0, bottom: 0 };
    const self = this;
    this.style = { props: {}, setProperty: (k, v) => { self.style.props[k] = v; } };
    this.classList = { add: (...n) => n.forEach((x) => self.cls.add(x)), remove: (...n) => n.forEach((x) => self.cls.delete(x)),
      contains: (n) => self.cls.has(n),
      toggle: (n, on) => { if (on === undefined) on = !self.cls.has(n); if (on) self.cls.add(n); else self.cls.delete(n); return on; } };
  }
  setAttribute(k, v) { this.attrs[k] = String(v); }
  getAttribute(k) { return this.attrs[k]; }
  setPointerCapture(p) { this.captured.push(p); }
  releasePointerCapture(p) { this.released.push(p); }
  getBoundingClientRect() { return this.rect; }
  querySelector() { return ELS.bar; }
}
const $ = (id) => ELS[id] || null;
const esc = (s) => String(s).replace(/[&<>]/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;' }[c]));
const escAttr = (s) => esc(s).replace(/"/g, '&quot;');
const say = () => {};
globalThis.localStorage = { getItem: () => null, setItem: () => {} };
globalThis.window = { innerWidth: 1280, innerHeight: 800,
  matchMedia: (q) => ({ matches: q.includes('max-width') ? NARROW : q.includes('reduced-motion') ? REDUCED : false }) };
let FRAMES = []; let FID = 0;
globalThis.requestAnimationFrame = (fn) => { FID += 1; FRAMES.push({ fn, id: FID }); return FID; };
globalThis.cancelAnimationFrame = (id) => { FRAMES = FRAMES.filter((f) => f.id !== id); };
let NOW = 0;
const flush = (step = 16) => { let n = 0; while (FRAMES.length && n < 200) { const due = FRAMES; FRAMES = []; NOW += step; due.forEach((f) => f.fn(NOW)); n += 1; } return n; };
const frame = (step = 16) => { const due = FRAMES; FRAMES = []; NOW += step; due.forEach((f) => f.fn(NOW)); return due.length; };
let TIMERS = []; let TID = 0;
globalThis.setTimeout = (fn, ms) => { TID += 1; TIMERS.push({ fn, ms, id: TID }); return TID; };
globalThis.clearTimeout = (id) => { TIMERS = TIMERS.filter((t) => t.id !== id); };
const pass = () => { const due = TIMERS; TIMERS = []; due.forEach((t) => t.fn()); return due.map((t) => t.ms); };
"""

SCENARIO = r"""
// the elements the map reads: the canvas 1000 by 600 at the window's left, the zoom bar 300 wide, the map's area 290 by
// 150 at 700, 400, its reads of its size counted
for (const id of ['th-map', 'th-map-items', 'th-map-view', 'th-map-btn', 'themes', 'th-world', 'th-zoom-level']) ELS[id] = new El(id);
ELS.bar = Object.assign(new El('bar'), { offsetWidth: 300 });
ELS['th-stage'] = Object.assign(new El('th-stage'), { clientWidth: 1000, clientHeight: 600 });
let AREA_W = 290; let READS = 0;
ELS['th-map-area'] = new El('th-map-area');
Object.defineProperty(ELS['th-map-area'], 'clientWidth', { get() { READS += 1; return AREA_W; } });
Object.defineProperty(ELS['th-map-area'], 'clientHeight', { get() { READS += 1; return 150; } });
ELS['th-map-area'].rect = { left: 700, top: 400, width: 290, height: 150, right: 990, bottom: 550 };
let CORNERS = 0;
thCorners = () => { CORNERS += 1; };
const out = {};
const r2 = (v) => Math.round(v * 100) / 100;

// ── an invented board: a PET of two, a PET holding a sub-theme of one and a card, a card in none no longer in its
// workbook, a discarded one, and two sticky notes, one on a paper the app does not know
const card = (x, y, extra) => Object.assign({ text: 'Counting the lengths', time: '00:10', x, y }, extra || {});
const v = { cards: { 'a:1:0': card(0, 0), 'a:2:0': card(220, 0), 'a:3:0': card(0, 300), 'a:4:0': card(600, 0),
  'a:5:0': card(900, 600, { missing: true }), 'a:6:0': card(1400, 0) }, groups: [], discarded: ['a:6:0'], picks: {},
  stickies: [{ id: 'n1', text: 'Look again', colour: 'pink', x: 700, y: 400 }, { id: 'n2', text: 'Cold', colour: 'mauve', x: 0, y: 700 }],
  ai: { discarded: {} } };
const g1 = thMakeGroup(v, ['a:1:0', 'a:2:0'], 'Floating at last');
const g2 = thMakeGroup(v, ['a:3:0'], 'The deep end');
const g3 = thMakeGroup(v, [g2, 'a:4:0'], 'Water that holds her');
const size = (id) => (thIsGroup(v, id) ? { w: 140, h: 30 } : thIsSticky(v, id) ? { w: 160, h: 47 } : { w: 200, h: 80 });
const layout = thLayout(v, size, null);
const items = thMapItems(v, layout, size, null);
const keyed = Object.fromEntries(Object.entries(v.cards).filter(([k]) => !v.discarded.includes(k)).map(([k], i) => [k, items.cards[i].cls]));
const getsItems = thMapItems({ cards: { x: card(0, 0, { case: 'Ada' }), y: card(300, 0, { case: 'Bo' }) }, groups: [], discarded: [], stickies: null },
  {}, () => ({ w: 200, h: 80 }), (c) => (c.case === 'Ada' ? 3 : 6));
out.items = { frames: items.frames.map((f) => f.cls), stickies: items.stickies.map((n) => n.cls), cards: keyed, all: items.all.length,
  gets: getsItems.cards.map((c) => c.cls), ids: [g1, g2, g3] };

// ── the fit, the round trip and the marks
const fit = thMapFit(items.all, 290, 150);
const u = thUnion(items.all);
const a0 = thMapToMap(fit, u.x, u.y); const a1 = thMapToMap(fit, u.x + u.w, u.y + u.h);
const small = thMapFit([{ x: 10, y: 10, w: 200, h: 80 }], 290, 150);
const sa = thMapToMap(small, 10, 10);
const back = thMapToBoard(fit, thMapToMap(fit, 123.4, -56.7).x, thMapToMap(fit, 123.4, -56.7).y);
out.fit = { k: fit.k, inside: a0.x >= 5.99 && a0.y >= 5.99 && a1.x <= 284.01 && a1.y <= 144.01,
  centred: [r2(a0.x - (290 - a1.x)), r2(a0.y - (150 - a1.y))],
  fills: Math.abs(a1.x - a0.x - 278) < 0.01 || Math.abs(a1.y - a0.y - 138) < 0.01,
  small: [r2(small.k), Math.abs(sa.x - 6) < 0.01 && Math.abs(sa.y + 40 * small.k - 75) < 0.01],
  back: [r2(back.x), r2(back.y)], none: [thMapFit([], 290, 150), thMapFit(items.all, 10, 150), thMapFit(items.all, 290, 0)] };
const html = thMapHtml(items, fit);
const tiny = thMapHtml({ all: [{ x: u.x, y: u.y, w: 1, h: 1, cls: 'tm-card' }] }, fit);
out.html = { marks: (html.match(/<i /g) || []).length, first: html.slice(0, 60), least: (tiny.match(/width:[^;]+;height:[^"]+/) || [''])[0] };

// ── the view's box
const seenOf = (view) => thMapSeen(view, 1000, 600);
const mid = thMapBox(fit, seenOf({ x: -300, y: -100, z: 1 }));
const mA = thMapToMap(fit, 300, 100);
const tinySeen = { x: 300, y: 100, w: 20, h: 12 };
const near = thMapBox(fit, tinySeen);
const tA = thMapToMap(fit, 300, 100);
const whole = thMapBox(fit, { x: u.x - 2000, y: u.y - 2000, w: u.w + 4000, h: u.h + 4000 });
const edge = thMapBox(fit, { x: u.x - 500, y: u.y, w: 1000, h: 600 });
out.box = { middle: [r2(mid.x), r2(mid.y), r2(mid.w), r2(mid.h)], middleWanted: [r2(mA.x), r2(mA.y), r2(1000 * fit.k), r2(600 * fit.k)],
  whole: [whole.x < 0, whole.y < 0, whole.x + whole.w > 290, whole.y + whole.h > 150],
  tiny: [r2(near.x), r2(near.y), r2(near.w), r2(near.h)],
  tinyWanted: [r2(tA.x - (6 - 20 * fit.k) / 2), r2(tA.y - (6 - 12 * fit.k) / 2), 6, 6],
  off: thMapBox(fit, seenOf({ x: 900000, y: 0, z: 1 })), edge: [r2(edge.x), r2(edge.w)], edgeWanted: r2(1000 * fit.k) };

// ── the states: Off, On, a new setting, Auto, the button and M, before a board, the narrow window, an empty board
const sizes = {}; for (const id of [...Object.keys(v.cards), ...v.groups.map((g) => g.id), 'n1', 'n2']) sizes[id] = size(id);
TH.sizes = sizes; TH.v = v; TH.layout = layout; TH.live = true; TH.view = { x: -300, y: -100, z: 1 }; TH.mode = 'pets';
const map = ELS['th-map'];
const look = () => ({ shut: map.cls.has('shut'), off: ELS['th-stage'].cls.has('th-map-off'), corners: CORNERS,
  hand: TH.mapHand, awake: !!TH.mapAwake, pressed: ELS['th-map-btn'].attrs['aria-pressed'] });
const pick = (o, keys) => Object.fromEntries(keys.map((k) => [k, o[k]]));
const marks = () => (ELS['th-map-items'].innerHTML.match(/<i /g) || []).length;
const s = {};
TH.config = { minimap: 'off' };
thMapDraw(); thMapToggle(); thMapViewed(); flush();
s.off = pick(look(), ['shut', 'off', 'corners', 'hand', 'awake', 'pressed']);
TH.config = { minimap: 'on' };
thMapSchedule(); flush();
s.on = Object.assign(pick(look(), ['shut', 'off', 'corners', 'pressed']), { marks: marks(), view: !ELS['th-map-view'].hidden && ELS['th-map-view'].style.left !== undefined });
thMapToggle(); flush(); s.onHidden = pick(look(), ['shut', 'hand', 'pressed']);
thMapToggle(); flush(); s.onShown = pick(look(), ['shut', 'hand']);
thMapToggle(); TH.config = { minimap: 'auto' }; TIMERS = []; thMapSchedule(); flush();
s.onChanged = look(); s.autoChosen = pick(look(), ['shut', 'awake']);
s.autoTimers = TIMERS.map((t) => t.ms); pass(); flush(); s.autoSlept = pick(look(), ['shut', 'awake']);
thMapViewed(); flush(); s.panned = pick(look(), ['shut', 'awake']);
TIMERS = []; TH.mapOver = true; thMapViewed(); s.over = { timers: TIMERS.length, awake: !!TH.mapAwake };
thMapLeave(); s.left = { timers: TIMERS.map((t) => t.ms) }; pass(); flush(); s.left.shut = map.cls.has('shut');
thMapToggle(); flush(); pass(); flush(); s.shown = Object.assign(pick(look(), ['shut', 'hand']), { afterTime: map.cls.has('shut') });
thMapToggle(); flush(); s.hidden = pick(look(), ['shut', 'hand', 'awake']);
thMapViewed(); flush(); s.nextPan = pick(look(), ['shut', 'awake']);
TH.config = { minimap: 'on' }; thMapSchedule(); flush();
TH.live = false; READS = 0; thMapSchedule(); flush(); s.notLive = { shut: map.cls.has('shut'), reads: READS }; TH.live = true;
NARROW = true; READS = 0; thMapToggle(); thMapSchedule(); flush(); s.narrow = { shut: map.cls.has('shut'), reads: READS, hand: TH.mapHand }; NARROW = false;
// a sidebar over the map gives it way, and one hidden or beside the canvas leaves it be
ELS['th-map'].rect = { left: 700, top: 400, width: 300, height: 160, right: 1000, bottom: 560 };
ELS['th-side'] = Object.assign(new El('th-side'), { rect: { left: 640, top: 0, width: 360, height: 520, right: 1000, bottom: 520 } });
thMapSchedule(); flush(); s.covered = { shut: map.cls.has('shut'), pressed: ELS['th-map-btn'].attrs['aria-pressed'] };
ELS['th-side'].hidden = true; thMapSchedule(); flush(); s.uncovered = map.cls.has('shut');
ELS['th-side'].hidden = false; ELS['th-side'].rect = { left: 1000, top: 0, width: 360, height: 900, right: 1360, bottom: 900 };
thMapSchedule(); flush(); s.beside = map.cls.has('shut'); delete ELS['th-side'];
TH.v = { cards: {}, groups: [], discarded: [], stickies: [] }; TH.layout = {}; thMapMoved(); flush();
s.empty = { shut: map.cls.has('shut'), marks: marks() };
TH.v = v; TH.layout = layout; thMapMoved(); flush();
out.states = s;

// ── the frames: one draw for many asks, a pan alone keeping the marks, a move, a new size, a drag as it shows, GETs
const f = {};
flush();
for (let i = 0; i < 5; i += 1) thMapViewed();
for (let i = 0; i < 3; i += 1) thMapMoved();
f.asked = FRAMES.length; flush();
ELS['th-map-items'].innerHTML = 'KEPT'; thMapViewed(); flush(); f.kept = ELS['th-map-items'].innerHTML === 'KEPT';
thMapMoved(); flush(); f.redrawn = ELS['th-map-items'].innerHTML !== 'KEPT';
ELS['th-map-items'].innerHTML = 'KEPT'; AREA_W = 250; thMapViewed(); flush(); f.resized = ELS['th-map-items'].innerHTML !== 'KEPT' && TH.map.w === 250; AREA_W = 290;
const seen = JSON.parse(JSON.stringify(v)); seen.cards['a:4:0'].x = 5000;
const kBefore = TH.map.k;
TH.drag = { seen }; thMapMoved(); flush(); f.dragShown = TH.map.k < kBefore; TH.drag = null;
TH.mode = 'gets'; TH.gets = { cases: [{ case: 'Ada', colour: 3 }, { case: 'Bo', colour: 6 }] };
TH.v = { cards: { x: card(0, 0, { case: 'Ada' }), y: card(300, 0, { case: 'Bo' }) }, groups: [], discarded: [], stickies: [] }; TH.layout = {};
thMapMoved(); flush(); f.gets = [...ELS['th-map-items'].innerHTML.matchAll(/tm-case (case-\d)/g)].map((m) => m[1]);
TH.mode = 'pets'; TH.v = v; TH.layout = layout; thMapMoved(); flush();
flush(); thMapPlace(); f.width = ELS['th-stage'].style.props['--th-map-w']; f.placeAsks = FRAMES.length; flush();
out.frames = f;

// ── the acts: a click off the box glides there, at once under reduced motion, a wander, another button, a drag on the
// box, a drag after a click, letting go, and a glide ended by another move
const acts = {};
const ev = (mx, my, extra = {}) => Object.assign({ button: 0, clientX: 700 + mx, clientY: 400 + my, pointerId: 3, preventDefault() {} }, extra);
const middleOf = () => ({ x: (500 - TH.view.x) / TH.view.z, y: (300 - TH.view.y) / TH.view.z });
TH.config = { minimap: 'on' }; TH.view = { x: -300, y: -100, z: 1 }; thMapSchedule(); flush();
const target = thMapToBoard(TH.map, 20, 120);
const box = TH.mapBox;
thMapDown(ev(20, 120));
const steps = []; let n = 0;
while (FRAMES.length && n < 60) { frame(40); steps.push(middleOf()); n += 1; }
const landed = middleOf();
acts.click = { captured: ELS['th-map-area'].captured.slice(), dragging: ELS['th-map-area'].cls.has('dragging'),
  midway: steps.length > 2 && Math.abs(steps[1].x - target.x) > 1 && Math.abs(steps[1].x - target.x) < Math.abs(300 + 500 - target.x),
  landed: [r2(landed.x), r2(landed.y)], wanted: [r2(target.x), r2(target.y)], frames: steps.length };
thMapUp(ev(20, 120)); flush();
REDUCED = true; TH.view = { x: -300, y: -100, z: 1 }; thMapSchedule(); flush();
const t2 = thMapToBoard(TH.map, 40, 30); thMapDown(ev(40, 30)); acts.still = [r2(middleOf().x), r2(middleOf().y)]; acts.stillWanted = [r2(t2.x), r2(t2.y)];
thMapUp(ev(40, 30)); REDUCED = false; flush();
TH.view = { x: -300, y: -100, z: 1 }; thMapSchedule(); flush();
const t3 = thMapToBoard(TH.map, 285, 5);
thMapDown(ev(285, 5)); thMapMove(ev(286, 7)); flush(); acts.wander = [r2(middleOf().x), r2(middleOf().y)]; acts.wanderWanted = [r2(t3.x), r2(t3.y)];
thMapMove(ev(260, 40)); const t4 = thMapToBoard(TH.map, 260, 40); acts.carried = [r2(middleOf().x), r2(middleOf().y)]; acts.carriedWanted = [r2(t4.x), r2(t4.y)];
thMapUp(ev(260, 40)); flush();
TH.mapDrag = null; thMapDown(ev(30, 30, { button: 2 })); acts.right = { drag: TH.mapDrag, moved: false };
TH.view = { x: -300, y: -100, z: 1 }; thMapSchedule(); flush();
const b = TH.mapBox; const bx = b.x + b.w / 2; const by = b.y + b.h / 2;
const under = thMapToBoard(TH.map, bx, by);
const off = { x: under.x - (0 - TH.view.x) / TH.view.z, y: under.y - (0 - TH.view.y) / TH.view.z };
thMapDown(ev(bx, by)); const glides = FRAMES.length; thMapMove(ev(bx + 12, by + 7));
const under2 = thMapToBoard(TH.map, bx + 12, by + 7);
acts.box = [r2(-TH.view.x / TH.view.z), r2(-TH.view.y / TH.view.z), glides];
acts.boxWanted = [r2(under2.x - off.x), r2(under2.y - off.y), 0];
TH.config = { minimap: 'auto' }; TH.mapMode = 'auto'; TH.mapAwake = true; TIMERS = [];
thMapUp(ev(bx + 12, by + 7)); acts.up = { drag: TH.mapDrag, dragging: ELS['th-map-area'].cls.has('dragging'), timers: TIMERS.map((t) => t.ms) };
TH.config = { minimap: 'on' }; thMapSchedule(); flush();
TH.view = { x: -300, y: -100, z: 1 };
thMapGlide(2000, 1000); frame(40); frame(40); TH.view.x = -777; const kept = TH.view.y; frame(40); frame(40); flush();
acts.stopped = [TH.view.x, r2(TH.view.y), FRAMES.length]; acts.stoppedWanted = [-777, r2(kept), 0];
out.acts = acts;
console.log(JSON.stringify(out));
"""
