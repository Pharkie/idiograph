from __future__ import annotations

import json
import re
import shutil
from pathlib import Path

from . import support
from .support import check, skip


def test_minimap_corner(scratch):
    print("\n169. The minimap as a card in the corner, 17 October, Adam's word that the strip down the column's full "
          "height took too much of the screen for a quick look, and since 17 October, later, his drawing of that evening: "
          "one card of one size at the transcript column's bottom right, the transcript as one narrow column of blocks "
          "scaled to fit like a measuring jug, the interviewer's marks, the done track, the box, the time at its right, "
          "Auto, On and Off, the same acts, a tip, the wheel, a map button and m, giving way over the passage being "
          "worked on, closing to its button at 1100px and below, and one bottom edge with Back to where I was. Since the test review "
          "of 18 October the card's markup, look, contrast, sizes and the blocks' layout are review shots, and the keys, the "
          "button, the presses, the drag, the wheel, the tip, the done track, giving way and Auto, On and Off stay")
    import subprocess

    read = lambda path: Path(path).read_text(encoding="utf-8")
    app = support.text("family/static/shell.js", "apps/idiograph/static/distil.js")
    themes_js, sift_js = support.text("apps/idiograph/static/themes.js"), support.text("apps/sift/static/sift.js")

    def whole(name):
        """A function of app.js whole, a one-line one included, or "" when there is none."""
        if f"function {name}(" not in app:
            return ""
        at = app.index(f"function {name}(")
        if app[max(0, at - 6):at] == "async ":
            at -= 6
        first = app[at:app.index("\n", at)]
        if first.rstrip().endswith("}") and first.count("{") == first.count("}"):
            return first
        return app[at:app.index("\n}", at) + 2]

    const = lambda name: next((ln for ln in app.splitlines() if ln.startswith(f"const {name} = ")), "")
    node = shutil.which("node")

    # ── A. m and the button
    keys = re.findall(r"else if \((?:e\.)?key === '(\w)' && !\$\('work'\)\.hidden[^)]*\) \{([^}]*)\}", app)
    check("169: M shows or hides the card on the statements screen, outside a field as every letter key is, the one M "
          "there, PETs and GETs taking theirs for the board's own map since 18 October (area 179) and Sift's own on its "
          "own screen",
          ("m", " e.preventDefault(); minimapToggle(); ") in keys and [k for k, _ in keys].count("m") == 1
          and app.count("key === 'm'") == 1 and themes_js.count("e.key === 'm'") == 1
          and "if (e.key === 'm' || e.key === 'M') { e.preventDefault(); thMapToggle(); return; }" in themes_js
          and "minimapToggle" not in themes_js and "'m'" in sift_js,
          str(keys))
    check("169: the button and m go through one show and hide, the View choice through its own, and the card's wheel is "
          "not passive so it can scroll the column",
          "$('minimap-btn').addEventListener('click', () => minimapToggle());" in app
          and "else if (e.target.name === 'view-minimap' && e.target.checked) minimapChoose(e.target.value);" in app
          and "$('minimap').addEventListener('wheel', minimapWheel, { passive: false });" in app
          and "$('minimap-area').addEventListener('pointerleave', () => minimapTip(null));" in app
          and "return setView('minimap', mode);" in whole("minimapChoose"))

    # ── C. in node: the plan, the time, the ties to the column, the box, the acts, giving way, Auto, On and Off
    if not node:
        skip("169: the card in node", "node is not installed")
    else:
        names = ["minimapMode", "minimapLayout", "minimapPlan", "minimapGrain", "minimapTimes", "minimapAnchors", "minimapToMap", "minimapToCol",
                 "minimapHtml", "minimapView", "drawMinimap", "drawMinimapView", "minimapOver", "minimapNarrow",
                 "minimapWanted", "minimapShown", "minimapYield", "minimapBand", "minimapButtonBand", "minimapWake", "minimapRest", "minimapLeave", "minimapScrolled",
                 "minimapPoint", "minimapRowAt", "minimapTo", "minimapDown", "minimapMove", "minimapUp", "minimapHover",
                 "minimapTip", "minimapWheel", "minimapToggle", "minimapChoose", "columnsOf", "largerPassage", "drawView",
                 "drawViewMenu", "setView",
                 # the columns shown and the stacking since 18 October (186), which drawView and Settings read
                 "columnsHiddenOf", "stackSplitOf", "columnsLayout"]
        consts = ["MINIMAP_MODES", "MINIMAP_ROOM", "MINIMAP_LEAST", "MINIMAP_GAP", "MINIMAP_MARK", "MINIMAP_FINE", "MINIMAP_AT", "MINIMAP_BOX",
                  "MINIMAP_APART", "MINIMAP_AWAKE", "MINIMAP_NARROW", "MINIMAP_CLEAR", "mmPx", "minimapWords",
                  "COLUMNS", "isColumns", "viewConfig", "HIDEABLE_COLUMNS", "STACK_SPLIT", "STACK_RANGE", "colsTicked"]
        view_choice = app[app.index("const viewChoice = "):app.index("\n});", app.index("const viewChoice = ")) + 4]
        source = "\n".join([const(c) for c in consts] + [view_choice, "let minimapSleep = 0;"] + [whole(n) for n in names])
        script = scratch / "minimap-169.js"
        script.write_text(r"""
const els = {};
// what the card gives way to: the current passage's parts, a field in focus, and the card, its button and its wrapper
let CUR_EL = null; let CURRENT = null; const FOCUSED = [];
const document = { activeElement: null, body: {}, elementsFromPoint: () => [] };
const box4 = (left, top, right, bottom) => ({ left, top, right, bottom, width: right - left, height: bottom - top });
const cls = () => ({ on: new Set(), toggle(c, v) { if (v === undefined) v = !this.on.has(c); if (v) this.on.add(c); else this.on.delete(c); return v; },
  add(c) { this.on.add(c); }, remove(c) { this.on.delete(c); }, contains(c) { return this.on.has(c); } });
const mk = (id) => ({ id, checked: false, hidden: false, value: '', innerHTML: '', style: {}, classList: cls(), attrs: {},
  offsetHeight: 0, offsetWidth: 0, captured: [],
  setAttribute(k, v) { this.attrs[k] = String(v); }, setPointerCapture(p) { this.captured.push(p); },
  getBoundingClientRect: () => box4(933, 447, 1058, 737) });
const $ = (id) => els[id] || (els[id] = mk(id));
let NARROW = false; let REDUCED = false;
const window = { innerWidth: 1280, matchMedia: (q) => ({ matches: q.includes('max-width') ? NARROW : REDUCED }) };
const esc = (s) => String(s).replace(/[&<>"]/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]));
let SCHEDULED = 0; const scheduleMinimap = () => { SCHEDULED += 1; };
// the timers kept by hand, so Auto's two seconds pass when the script says
let TIMERS = []; let TID = 0;
const setTimeout = (fn, ms) => { TID += 1; TIMERS.push({ fn, ms, id: TID }); return TID; };
const clearTimeout = (id) => { TIMERS = TIMERS.filter((t) => t.id !== id); };
const pass = () => { const due = TIMERS; TIMERS = []; due.forEach((t) => t.fn()); return due.map((t) => t.ms); };
const sent = []; const api = async (path, body) => { sent.push(body); return { config: Object.assign({}, S.data.config, body) }; };
const say = () => {}; const RESTART_LINE = 'Restart the server to finish this update.'; const needsRestart = () => false;
const current = () => CURRENT; const centreCurrent = () => {}; const placeNotes = () => {};
const placeCard = () => {}; const drawColumns = () => {}; const cellsAgain = () => {};
const NOTES_PLACE_COLUMNS = { right: ['transcript', 'notes', 'statements'], left: ['notes', 'transcript', 'statements'], under: ['transcript', 'statements', 'notes'] };
const ROOMS = [];
els['transcript-rows'] = Object.assign(mk('transcript-rows'), { querySelector: () => CUR_EL });
// the column's wrapper, 900 wide and 400 tall, at its bottom right the card, 135 by 300, and its button, 32 square,
// 4 to its right on its bottom edge, the two 171 wide
els['minimap-btn'] = Object.assign(mk('minimap-btn'), { offsetWidth: 32, getBoundingClientRect: () => box4(1057, 710, 1089, 742) });
els['minimap-card'] = Object.assign(mk('minimap-card'), { getBoundingClientRect: () => box4(918, 442, 1053, 742) });
const WRAP = { clientWidth: 900, clientHeight: 400, classList: cls(), style: { setProperty: (k, v) => ROOMS.push([k, v]) } };
els.minimap = Object.assign(mk('minimap'), { parentElement: WRAP, offsetWidth: 171,
  getBoundingClientRect: () => box4(918, 442, 1089, 742) });
const lastOf = (key) => ROOMS.filter(([k]) => k === key).pop();
// twelve invented passages, the interviewer's and hers by turns, hers of 40 to 200 words, the last with no timecode
const SECONDS = [0, 10, 60, 200, 400, 590, 610, 700, 900, 1190, 1500, null];
const WORDS = [8, 40, 8, 120, 8, 10, 8, 200, 8, 60, 8, 90];
const S = { data: null, libConfig: null, mm: null, mmDrag: null,
  flat: SECONDS.map((s, i) => ({ i, name: i % 2 ? (i === 9 ? 'Wren <&>' : 'Wren') : 'Hale', time: s === null ? '' : `00:${String(Math.floor(s / 60)).padStart(2, '0')}:${String(s % 60).padStart(2, '0')}`,
    seconds: s, text: Array.from({ length: WORDS[i] }, () => 'bee').join(' ') })) };
const SPANS = [[26, 40], [66, 140], [206, 40], [246, 300], [546, 40], [586, 60], [646, 40], [686, 460], [1146, 40],
  [1186, 160], [1346, 40], [1386, 220]];
const DONE = [0, 2, 0, 1, 0, 0, 0, 2, 0, 0, 0, 0];
let READS = 0;
const rect = (top, height) => ({ top, height, bottom: top + height });
const COL = Object.assign(mk('transcript'), { scrollTop: 0, scrollHeight: 1928, clientHeight: 400, scrolled: [], by: [],
  getBoundingClientRect() { READS += 1; return rect(100, 400); },
  querySelectorAll(sel) {
    const on = (top) => 100 - this.scrollTop + top;
    if (sel === '.turn') return SPANS.map(([top, h], i) => ({ dataset: Object.assign({ i: String(i) }, DONE[i] ? { done: String(DONE[i]) } : {}),
      classList: { contains: (c) => (c === 'aside' ? i % 2 === 0 : false) },
      getBoundingClientRect: () => rect(on(top), h) }));
    return [];
  },
  scrollTo(o) { this.scrolled.push(o); }, scrollBy(o) { this.by.push(o); }, contains: (el) => FOCUSED.includes(el) });
els.transcript = COL;
""" + source + r"""
const r2 = (v) => Math.round(v * 100) / 100;
const out = {};
(async () => {
  out.modes = [undefined, true, false, 'on', 'off', 'auto', 'sometimes'].map((v) => minimapMode(v === undefined ? {} : { minimap: v }));
  out.modeNone = minimapMode(null);
  out.words = [minimapWords('one two  three\nfour'), minimapWords(''), minimapWords(null)];

  // the plan: six blocks of hers, each her words' share of 280 less the gaps, the interviewer's marks between them
  const layout = minimapLayout(COL);
  out.layout = layout.rows.map((r) => [r.top, r.height, r.hers, r.done, r.words, r.seconds]);
  const plan = minimapPlan(layout, MINIMAP_ROOM);
  const gaps = (6 - 1 + 1) * MINIMAP_GAP;
  out.plan = { k: r2(plan.k * 1000) / 1000, kWanted: r2((280 - gaps) / 520 * 1000) / 1000, blocks: plan.blocks.map((b) => [r2(b.top), r2(b.height), b.rows]),
    marks: plan.marks.map(r2), end: r2(plan.blocks[5].top + plan.blocks[5].height),
    spans: plan.spans.map((s) => [r2(s.top), r2(s.bottom)]), done: plan.done.map((d) => [r2(d.top), r2(d.bottom)]) };
  // a passage that would come out under 4.5 pixels joins the smaller of its neighbours, and the scale grows for the gap
  const tiny = { rows: [{ hers: true, words: 100 }, { hers: false, words: 5 }, { hers: true, words: 2 }, { hers: false, words: 5 },
    { hers: true, words: 30 }, { hers: false, words: 5 }, { hers: true, words: 100 }].map((r, i) => Object.assign({ i, top: i * 50, height: 40, done: 0, seconds: null }, r)), height: 400 };
  const joined = minimapPlan(tiny, MINIMAP_ROOM);
  out.joined = { blocks: joined.blocks.map((b) => b.rows), marks: joined.marks.length, least: r2(Math.min(...joined.blocks.map((b) => b.height))),
    inside: r2(joined.spans[3].top) === r2(joined.spans[4].top), end: r2(joined.blocks[joined.blocks.length - 1].top + joined.blocks[joined.blocks.length - 1].height) };
  out.none = [minimapPlan({ rows: [{ hers: false, words: 3, top: 0, height: 10 }], height: 10 }, MINIMAP_ROOM), minimapPlan(layout, { width: 62, height: 0 })];
  // the time: every five minutes under half an hour, its marks between the timecodes either side
  out.times = plan.times.map((t) => [r2(t.y), t.label, t.short]);

  // the ties to the column: a place in the column read in the map and back, an interviewer's turn a point
  plan.anchors = minimapAnchors(layout, plan);
  out.ties = { head: minimapToMap(plan, 0), foot: r2(minimapToMap(plan, 1928)), rowTop: minimapToMap(plan, 246.5) > plan.spans[3].top && minimapToMap(plan, 246.5) < plan.spans[3].top + 1,
    mid: r2(minimapToMap(plan, 246 + 150)), wanted: r2((plan.spans[3].top + plan.spans[3].bottom) / 2),
    back: Math.round(minimapToCol(plan, minimapToMap(plan, 800))), ask: Math.round(minimapToCol(plan, plan.spans[2].top)) };
  // the box: its place for the view's head to its place for its foot, never under 6 pixels, a short one centred
  out.views = [[0, 400], [800, 400], [1928, 0], [700, 2]].map(([t, h]) => { const v = minimapView(plan, t, h); return [r2(v.top), r2(v.height)]; });
  out.html = minimapHtml(plan);

  // On: the card wanted and drawn, its button pressed, the box over the part in view
  $('work').hidden = false; $('work').classList.add('minimap-on'); $('work').classList.add('minimap-always');
  const way = () => ({ yield: $('minimap').classList.contains('yield'), gone: $('minimap').classList.contains('gone'),
    shut: $('minimap').classList.contains('shut'), pressed: $('minimap-btn').attrs['aria-pressed'] });
  drawMinimap();
  out.drawn = Object.assign(way(), { same: $('minimap-map').innerHTML === out.html, views: $('minimap-views').innerHTML,
    room: lastOf('--mm-room'), lift: WRAP.classList.contains('mm-lift') });
  COL.scrollTop = 800; drawMinimapView(); out.followed = $('minimap-views').innerHTML; COL.scrollTop = 0; drawMinimapView();

  // giving way: clear words leave the card be, the notes under the card take its map and leave the button's chip, words
  // under the chip take the card whole, a field in focus counts, never while the pointer is on it or a press is under way
  const words = (...rects) => { CUR_EL = { querySelectorAll: () => rects.map((r) => ({ getBoundingClientRect: () => r })) }; };
  words(box4(100, 300, 600, 500)); minimapYield(); out.clear = Object.assign(way(), { room: lastOf('--mm-room') });
  words(box4(950, 600, 1040, 690)); minimapYield(); out.underCard = Object.assign(way(), { room: lastOf('--mm-room') });
  words(box4(1000, 700, 1088, 740)); minimapYield(); out.underChip = Object.assign(way(), { room: lastOf('--mm-room') });
  NARROW = true; minimapYield(); out.stacked = way(); NARROW = false;
  words(); const field = { tagName: 'TEXTAREA', getBoundingClientRect: () => box4(980, 600, 1040, 640) };
  FOCUSED.push(field); document.activeElement = field; minimapYield(); out.focused = way();
  FOCUSED.length = 0; document.activeElement = null; minimapYield(); out.cleared = way();
  S.mmOver = true; words(box4(950, 600, 1040, 690)); minimapYield(); out.over = way(); S.mmOver = false;
  S.mmDrag = { grab: 0 }; minimapYield(); out.dragging = way(); S.mmDrag = null; minimapYield(); out.left = way();
  // an opening of his: over what stands in the corner as he opens it, through a scroll on the card, ended by the pointer
  // leaving, a scroll by his hand, the corner clear and then reached, or a field in focus under it
  const peekWay = () => Object.assign(way(), { peek: $('work').classList.contains('minimap-peek') });
  const open = () => { $('work').classList.add('minimap-peek'); S.mmHeld = true; };
  open(); minimapYield(); out.peek = peekWay();
  minimapYield(); out.peekStill = peekWay();
  S.mmOver = true; minimapYield(); minimapLeave(); out.peekLeft = Object.assign(peekWay(), { held: S.mmHeld });
  open(); words(); minimapYield(); out.peekClear = Object.assign(peekWay(), { held: S.mmHeld });
  words(box4(950, 600, 1040, 690)); minimapYield(); out.peekReached = peekWay();
  open(); minimapYield(); FOCUSED.push(field); document.activeElement = field; minimapYield(); out.peekField = peekWay();
  FOCUSED.length = 0; document.activeElement = null;
  open(); minimapYield(); S.mmOver = true; minimapScrolled(); out.scrollOnCard = peekWay(); S.mmOver = false;
  minimapScrolled(); out.scrollByHand = peekWay();
  NARROW = true; open(); words(); minimapYield(); SCHEDULED = 0; words(box4(950, 600, 1040, 690)); minimapYield();
  out.narrowReached = Object.assign(peekWay(), { scheduled: SCHEDULED, wanted: minimapWanted() });
  NARROW = false; words(); minimapYield();
  // Back to where I was beside the card where the column has the room, and where it has not, while the way back shows, in
  // a strip at the column's head, the column's words kept in place as the strip comes and goes
  const strip = () => ({ room: lastOf('--mm-room'), on: WRAP.classList.contains('mm-lift'), top: COL.scrollTop });
  // the words never move as the strip comes and goes
  COL.scrollTop = 500; WRAP.clientWidth = 312; minimapYield(); out.narrowHere = strip();
  WRAP.classList.add('away'); minimapYield(); out.lifted = strip();
  minimapYield(); out.liftedAgain = strip();
  WRAP.clientWidth = 900; minimapYield(); out.unlifted = strip();
  WRAP.clientWidth = 312; minimapYield(); WRAP.classList.remove('away'); minimapYield(); out.backHome = strip();
  WRAP.clientWidth = 900; COL.scrollTop = 0; minimapYield();

  // the acts: a press off the box glides the place pressed to the column's middle, a wander leaves it, a drag scrolls at
  // once, letting go ends it, a press on the box takes it from the first move, and a closed card moves nothing
  const ev = (x, m, extra = {}) => Object.assign({ button: 0, clientX: 933 + 17 + x, clientY: 447 + 5 + m, pointerId: 7,
    pointerType: 'mouse', prevented: false, preventDefault() { this.prevented = true; } }, extra);
  S.mm = Object.assign(minimapPlan(minimapLayout(COL), MINIMAP_ROOM), {}); S.mm.anchors = minimapAnchors(minimapLayout(COL), S.mm);
  COL.scrolled.length = 0;
  const down = ev(30, 200); minimapDown(down);
  out.click = { scrolled: COL.scrolled.slice(), wanted: Math.round(minimapToCol(S.mm, 200) - 200), prevented: down.prevented,
    captured: $('minimap-area').captured.slice(), dragging: $('minimap-area').classList.contains('dragging'),
    grab: S.mmDrag.grab, moved: S.mmDrag.moved };
  COL.scrolled.length = 0; minimapMove(ev(31, 202)); out.wander = COL.scrolled.slice();
  minimapMove(ev(30, 240)); out.dragged = [COL.scrolled.slice(), Math.round(minimapToCol(S.mm, 240) - 200)];
  minimapUp(); out.up = { drag: S.mmDrag, dragging: $('minimap-area').classList.contains('dragging') };
  COL.scrollTop = 800; COL.scrolled.length = 0;
  const v = minimapView(S.mm, 800, 400);
  minimapDown(ev(30, v.top + v.height / 2)); out.onBox = { scrolled: COL.scrolled.slice(), grab: Math.round(S.mmDrag.grab),
    wanted: Math.round(minimapToCol(S.mm, v.top + v.height / 2) - 800) };
  const grabbed = S.mmDrag.grab;
  minimapMove(ev(30, v.top + v.height / 2 + 20)); out.boxMoved = [COL.scrolled.slice(), Math.max(0, Math.round(minimapToCol(S.mm, v.top + v.height / 2 + 20) - grabbed))];
  minimapUp(); COL.scrollTop = 0;
  COL.scrolled.length = 0; REDUCED = true; minimapDown(ev(30, 200)); out.still = COL.scrolled.slice(); minimapUp(); REDUCED = false;
  COL.scrolled.length = 0; minimapDown(ev(30, 200, { button: 2 })); out.right = { scrolled: COL.scrolled.slice(), drag: S.mmDrag };
  const kept = S.mm; S.mm = null; minimapDown(ev(30, 200)); out.closedPress = COL.scrolled.length; S.mm = kept;
  // the tip: a passage's speaker and timecode, escaped, the interviewer's at his mark, none off the column or for a touch
  Object.defineProperty($('minimap-tip'), 'offsetWidth', { get() { return 90; } });
  Object.defineProperty($('minimap-tip'), 'offsetHeight', { get() { return 20; } });
  const tipNow = () => ({ hidden: $('minimap-tip').hidden, html: $('minimap-tip').innerHTML, left: $('minimap-tip').style.left, top: $('minimap-tip').style.top });
  const midOf = (n) => (S.mm.spans[n].top + S.mm.spans[n].bottom) / 2;
  minimapMove(ev(30, midOf(3))); out.tip = tipNow();
  minimapMove(ev(30, midOf(9))); out.tipEscaped = tipNow().html;
  minimapMove(ev(10, S.mm.spans[2].top)); out.tipAsk = tipNow().html;
  minimapMove(ev(30, midOf(11))); out.tipNoTime = tipNow().html;
  minimapMove(ev(80, midOf(3))); out.tipOff = tipNow().hidden;
  minimapMove(ev(30, midOf(3))); minimapMove(ev(30, midOf(3), { pointerType: 'touch' })); out.tipTouch = tipNow().hidden;
  minimapMove(ev(30, midOf(3))); minimapDown(ev(30, 200)); out.tipPress = tipNow().hidden; minimapUp();
  const wheel = (deltaY, deltaMode, ctrlKey = false) => { const e = { deltaY, deltaMode, ctrlKey, prevented: false, preventDefault() { this.prevented = true; } };
    COL.by.length = 0; minimapWheel(e); return [COL.by.length ? COL.by[0].top : null, e.prevented]; };
  out.wheel = [wheel(120, 0), wheel(3, 1), wheel(1, 2), wheel(-40, 0, true)];

  // Auto: asleep the card is not wanted and reads nothing, a scroll wakes it, two seconds let it sleep, never under his
  // hand or in a drag, the time starting again as the pointer leaves, and a move to another passage wakes it
  CUR_EL = null; TIMERS = [];
  $('work').classList.remove('minimap-always'); S.mmAwake = false;
  let reads = READS; drawMinimap(); out.asleep = Object.assign(way(), { mm: S.mm, reads: READS - reads, wanted: minimapWanted() });
  SCHEDULED = 0; minimapScrolled(); out.woken = { awake: S.mmAwake, scheduled: SCHEDULED, timers: TIMERS.map((t) => t.ms) };
  drawMinimap(); out.awakeDrawn = Object.assign(way(), { drawn: !!S.mm });
  minimapScrolled(); out.oneTimer = TIMERS.length;
  S.mmOver = true; out.handPass = pass(); out.held = S.mmAwake;
  minimapLeave(); out.leftTimers = TIMERS.map((t) => t.ms); pass(); out.slept = S.mmAwake;
  drawMinimap(); out.sleptDrawn = way();
  S.mmDrag = { grab: 0 }; minimapScrolled(); pass(); out.dragHeld = S.mmAwake; S.mmDrag = null; minimapUp(); pass();
  CURRENT = S.flat[3]; S.mmAwake = false; drawMinimap(); out.moved = { awake: S.mmAwake, shut: $('minimap').classList.contains('shut') };
  pass(); drawMinimap();
  // the button and m: hidden it shows until the next passage, held over the corner, shown it hides until then, a scroll
  // waking Auto leaving it hidden, and the next passage clearing both
  minimapToggle(); drawMinimap(); out.shownByHim = Object.assign(peekWay(), { held: S.mmHeld, hush: S.mmHush });
  minimapToggle(); drawMinimap(); out.hiddenByHim = Object.assign(peekWay(), { hush: S.mmHush });
  minimapScrolled(); drawMinimap(); out.hushKept = way().shut;
  CURRENT = S.flat[5]; drawMinimap(); out.nextPassage = { peek: $('work').classList.contains('minimap-peek'), hush: S.mmHush, held: S.mmHeld, awake: S.mmAwake };
  pass(); CURRENT = null; drawMinimap();
  // where the sheet and the fields stack nothing but his press shows it, in Auto or On
  NARROW = true; S.mmAwake = true; $('work').classList.add('minimap-always'); out.narrow = minimapWanted();
  minimapToggle(); out.narrowPressed = minimapWanted(); $('work').classList.remove('minimap-peek'); S.mmHeld = false;
  NARROW = false; $('work').classList.remove('minimap-always'); S.mmAwake = false;

  // the choice: Auto on a new install, On, Off with nothing in the corner and the button and m doing nothing, each sent
  // alone, View and Settings in step, any opening or hiding of his gone with it
  S.data = { config: {} }; S.libConfig = { minimap: 'auto' }; drawView();
  const state = () => ({ on: $('work').classList.contains('minimap-on'), always: $('work').classList.contains('minimap-always'),
    menu: MINIMAP_MODES.filter((m) => $(`view-minimap-${m}`).checked), cfg: S.data.config.minimap === undefined ? null : S.data.config.minimap });
  out.fresh = state();
  $('work').classList.add('minimap-peek'); S.mmHush = true;
  sent.length = 0; await minimapChoose('on'); out.chosenOn = Object.assign(state(), { peek: $('work').classList.contains('minimap-peek'), hush: S.mmHush, lib: S.libConfig.minimap });
  await minimapChoose('off'); out.chosenOff = Object.assign(state(), { wanted: minimapWanted() });
  minimapYield(); out.offCard = { off: $('minimap').classList.contains('off'), room: lastOf('--mm-room') };
  minimapToggle(); out.offToggle = $('work').classList.contains('minimap-peek');
  TIMERS = []; await minimapChoose('auto'); out.chosenAuto = Object.assign(state(), { awake: S.mmAwake, timers: TIMERS.map((t) => t.ms) });
  out.sent = sent.slice();
  for (const m of MINIMAP_MODES) $(`set-minimap-${m}`).checked = minimapMode(S.data.config) === m;
  // the columns shown under Show since 18 October (186), where the columns' order stood
  $('set-show-statements').checked = true; $('set-show-notes').checked = true;
  $('set-larger').checked = largerPassage(S.data.config);
  out.settings = viewChoice();
  $('set-minimap-auto').checked = false; $('set-minimap-on').checked = true;
  out.settingsMoved = viewChoice().minimap;
  S.data.config.minimap = true; drawView(); out.oldTrue = state();
  S.data.config.minimap = false; drawView(); out.oldFalse = state();
  console.log(JSON.stringify(out));
})().catch((err) => { console.error(String(err && err.stack || err)); process.exit(1); });
""", encoding="utf-8")
        run = subprocess.run([node, str(script)], capture_output=True, text=True, encoding="utf-8", timeout=60)
        out = json.loads(run.stdout) if run.returncode == 0 and run.stdout.strip() else {}
        if not out:
            check("169: the card's functions run in node", False, run.stderr.strip()[:400])
        else:
            check("169, 17 October, later: in node, the choice reads Auto when absent, from the old tick's true and from "
                  "anything it does not know, Off from the old false, and a passage's words are counted, never under one",
                  out["modes"] == ["auto", "auto", "off", "on", "off", "auto", "auto"] and out["modeNone"] == "auto"
                  and out["words"] == [4, 1, 1], f"{out['modes']} {out['words']}")
            p = out["plan"]
            check("169, 17 October, later: in node, the done track runs from a passage done to the last done after it, a "
                  "skipped one counting, across the interviewer's turns between, and stops at one not done",
                  p["done"] == [[p["spans"][1][0], p["spans"][3][1]], [p["spans"][7][0], p["spans"][7][1]]], str(p["done"]))
            j = out["joined"]
            labels = [t[1] for t in out["times"] if t[1]]
            t = out["ties"]
            check("169, 17 October, later: in node, a place in the column reads as a place in the map and back, the "
                  "column's head the map's, its foot the map's foot, a passage's top its block's, its middle its middle, "
                  "and an interviewer's point as his turn's first place in the column",
                  t["head"] == 0 and t["foot"] == 280 and t["rowTop"] and abs(t["mid"] - t["wanted"]) < 0.02
                  and t["back"] == 800 and t["ask"] == 206, str(t))
            html = out["html"]
            check("169, 17 October, later: in node, the card gives way to its button where the passage's notes would "
                  "stand under it, and the button goes too where words would stand under it, at every width, where at "
                  "1100px and below the button stayed over the last line of his passage, and for a field in focus, comes "
                  "back once they are clear, holds while the pointer is on it or a press is under way, and Back to where I was "
                  "keeps the card and the button's width, the button's alone or none",
                  out["clear"] == {"yield": False, "gone": False, "shut": False, "pressed": "true", "room": ["--mm-room", "193px"]}
                  and out["underCard"] == {"yield": True, "gone": False, "shut": True, "pressed": "false", "room": ["--mm-room", "54px"]}
                  and out["underChip"] == {"yield": True, "gone": True, "shut": True, "pressed": "false", "room": ["--mm-room", ""]}
                  and out["stacked"] == {"yield": False, "gone": True, "shut": True, "pressed": "false"}
                  and out["focused"] == {"yield": True, "gone": False, "shut": True, "pressed": "false"}
                  and out["cleared"] == {"yield": False, "gone": False, "shut": False, "pressed": "true"}
                  and out["over"] == out["cleared"] and out["dragging"] == out["cleared"]
                  and out["left"] == {"yield": True, "gone": False, "shut": True, "pressed": "false"},
                  str({k: out[k] for k in ("clear", "underCard", "underChip", "stacked", "focused", "left")}))
            check("169, 17 October, later: in node, an opening of his shows over what stands in the corner as he opens it "
                  "and through a scroll on the card, and ends once his pointer leaves the card or his hand scrolls the "
                  "words, once what he works on reaches the corner after it stood clear, or at once for a field in focus "
                  "under it, then giving way as at any time and at 1100px and below closing to its button, where it never "
                  "gave way there and covered the notes he was writing",
                  out["peek"] == {"yield": False, "gone": False, "shut": False, "pressed": "true", "peek": True}
                  and out["peekStill"] == out["peek"]
                  and out["peekLeft"] == {"yield": True, "gone": False, "shut": True, "pressed": "false", "peek": False, "held": False}
                  and out["peekClear"] == {"yield": False, "gone": False, "shut": False, "pressed": "true", "peek": True, "held": False}
                  and out["peekReached"] == {"yield": True, "gone": False, "shut": True, "pressed": "false", "peek": False}
                  and out["peekField"] == {"yield": True, "gone": False, "shut": True, "pressed": "false", "peek": False}
                  and out["scrollOnCard"] == out["peek"]
                  and out["scrollByHand"] == {"yield": True, "gone": False, "shut": True, "pressed": "false", "peek": False}
                  and out["narrowReached"] == {"yield": True, "gone": False, "shut": True, "pressed": "false", "peek": False,
                                               "scheduled": 1, "wanted": False},
                  str({k: out[k] for k in ("peek", "peekLeft", "peekClear", "peekReached", "peekField", "scrollByHand", "narrowReached")}))
            check("169: in node, a press off the box glides the column to bring the place pressed to its middle and keeps "
                  "the pointer, a wander of a pixel or two leaves the glide alone, a drag scrolls at once, and letting go "
                  "ends it",
                  out["click"]["scrolled"] == [{"top": out["click"]["wanted"], "behavior": "smooth"}] and out["click"]["prevented"]
                  and out["click"]["captured"] == [7] and out["click"]["dragging"] and out["click"]["grab"] == 200
                  and out["click"]["moved"] is False and out["wander"] == []
                  and out["dragged"][0] == [{"top": out["dragged"][1], "behavior": "auto"}]
                  and out["up"] == {"drag": None, "dragging": False}, str(out["click"]))
            check("169: in node, a press on the box moves nothing until the pointer does, then takes the box with it, under "
                  "reduced motion a click jumps, a right press does nothing, and a closed card moves nothing",
                  out["onBox"]["scrolled"] == [] and out["onBox"]["grab"] == out["onBox"]["wanted"]
                  and out["boxMoved"][0] == [{"top": out["boxMoved"][1], "behavior": "auto"}]
                  and out["still"] == [{"top": out["click"]["wanted"], "behavior": "auto"}]
                  and out["right"] == {"scrolled": [], "drag": None} and out["closedPress"] == 0, str(out["onBox"]))
            check("169: in node, the tip gives the passage's speaker and timecode as the margin has them, escaped, the "
                  "interviewer's at his mark, the name alone where a passage has no timecode, centred above the pointer, and "
                  "it goes off the column, for a touch and on a press",
                  out["tip"]["hidden"] is False and out["tip"]["html"] == 'Wren <span class="mono">00:03:20</span>'
                  and out["tip"]["top"].endswith("px") and out["tipEscaped"] == 'Wren &lt;&amp;&gt; <span class="mono">00:19:50</span>'
                  and out["tipAsk"] == 'Hale <span class="mono">00:01:00</span>' and out["tipNoTime"] == "Wren"
                  and out["tipOff"] is True and out["tipTouch"] is True and out["tipPress"] is True, str(out["tip"]))
            check("169: in node, the wheel over the card scrolls the column by its pixels, by 16 a line and by the column's "
                  "height a page, and a pinch is left to the browser",
                  out["wheel"] == [[120, True], [48, True], [400, True], [None, False]], str(out["wheel"]))
            check("169, 17 October, later: in node, in Auto the card asleep is not wanted, reads nothing and fades to its "
                  "button, a scroll wakes it with one timer of two seconds, which never lets it sleep under his hand or in a "
                  "drag and starts again as the pointer leaves, and a move to another passage wakes it",
                  out["asleep"] == {"yield": False, "gone": False, "shut": True, "pressed": "false", "mm": None, "reads": 0, "wanted": False}
                  and out["woken"] == {"awake": True, "scheduled": 1, "timers": [2000]}
                  and out["awakeDrawn"] == {"yield": False, "gone": False, "shut": False, "pressed": "true", "drawn": True}
                  and out["oneTimer"] == 1 and out["handPass"] == [2000] and out["held"] is True
                  and out["leftTimers"] == [2000] and out["slept"] is False
                  and out["sleptDrawn"]["shut"] is True and out["dragHeld"] is True
                  and out["moved"] == {"awake": True, "shut": False}, str({k: out[k] for k in ("asleep", "woken", "handPass", "moved")}))
            check("169, 17 October, later: in node, the button and m show the card until the next passage, held over the "
                  "corner until the corner stands clear, or hide it until then, a scroll in Auto leaving it hidden, and the next passage clears both, "
                  "where the sheet and the fields stack only his press shows it",
                  out["shownByHim"] == {"yield": False, "gone": False, "shut": False, "pressed": "true", "peek": True, "held": False, "hush": False}
                  and out["hiddenByHim"] == {"yield": False, "gone": False, "shut": True, "pressed": "false", "peek": False, "hush": True}
                  and out["hushKept"] is True
                  and out["nextPassage"] == {"peek": False, "hush": False, "held": False, "awake": True}
                  and out["narrow"] is False and out["narrowPressed"] is True,
                  str({k: out[k] for k in ("shownByHim", "hiddenByHim", "nextPassage")}))
            check("169, 17 October, later: in node, Auto on a new install and for the old tick's true, Off for its false, "
                  "each choice drawn at once in View and sent alone, an opening or hiding of his gone with it, Off with "
                  "nothing in the corner and the button and m doing nothing, Auto shown at once and left to sleep, and "
                  "Settings in step, its choice moved what Save sends",
                  out["fresh"] == {"on": True, "always": False, "menu": ["auto"], "cfg": None}
                  and out["chosenOn"] == {"on": True, "always": True, "menu": ["on"], "cfg": "on", "peek": False, "hush": False, "lib": "on"}
                  and out["chosenOff"] == {"on": False, "always": False, "menu": ["off"], "cfg": "off", "wanted": False}
                  and out["offCard"] == {"off": True, "room": ["--mm-room", ""]} and out["offToggle"] is False
                  and out["chosenAuto"] == {"on": True, "always": False, "menu": ["auto"], "cfg": "auto", "awake": True, "timers": [2000]}
                  and out["sent"] == [{"minimap": "on"}, {"minimap": "off"}, {"minimap": "auto"}]
                  and out["settings"] == {"columns_hidden": [], "columns_stacked": False, "larger_passage": True, "minimap": "auto", "status_bar": False}
                  and out["settingsMoved"] == "on"
                  and out["oldTrue"]["menu"] == ["auto"] and out["oldTrue"]["on"] is True
                  and out["oldFalse"] == {"on": False, "always": False, "menu": ["off"], "cfg": False},
                  str({k: out[k] for k in ("fresh", "chosenOn", "chosenOff", "chosenAuto", "settings")}))
