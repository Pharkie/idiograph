from __future__ import annotations

import json
import shutil

from . import support
from .support import check, skip


def test_canvas_print(scratch):
    print("\n94. The canvas in print: Canvas under Export on PETs and Canvas in the GETs print card, the canvas copied "
          "from the screen onto one landscape page under a title, light, fitted to the paper, every statement whole (210)")
    import subprocess

    js = support.text("apps/idiograph/static/themes.js")
    fn = lambda src, name: src.split(f"function {name}(", 1)[1].split("\n}", 1)[0] if f"function {name}(" in src else ""
    block = js.split("/* ── the canvas in print ── */", 1)[1].split("/* ── the cases ── */", 1)[0] \
        if "/* ── the canvas in print ── */" in js else ""

    # ── A. the entries, on PETs and on GETs
    clicker = js.split("$('th-xmenu').addEventListener('click', (e) => {", 1)[1].split("});", 1)[0]
    check("94: a press on Canvas runs the canvas print, the other entries as they were",
          "if (op.dataset.xop === 'canvas') { thCanvasPrint(); return; }" in clicker
          and clicker.index("xop === 'print'") < clicker.index("xop === 'canvas'") < clicker.index("thExport(op.dataset.xop === 'word');"))
    goer = fn(js, "gtPrintGo")
    check("94: Canvas takes away Full or Selected, and Print sends it to the canvas print with the participant notes tick, "
          "before the server's print view is asked for",
          "$('gt-print-detail').hidden = p.what === 'canvas' && !p.gid;" in fn(js, "gtPrintDraw")
          and "if (p.what === 'canvas' && !p.gid) { thCanvasPrint({ notes }); return; }" in goer
          and goer.index("thCanvasPrint({ notes })") < goer.index("if (!TH.getsPrint)"))

    # ── B. taken from the canvas on screen, every statement whole, saved first, in a tab of its own
    printer = fn(js, "thCanvasMade")
    # the canvas's Save as PDF and Save as an image (exportA) send the page made here to the server to be saved,
    # and nothing else in the canvas's print asks it
    drawn = block.replace(fn(js, "thCanvasOut"), "")
    check("94: the page carries the app's own rules, read from the page's sheets, never a second drawing of the board",
          "for (const sheet of document.styleSheets)" in fn(js, "thCanvasRules") and "rules: thCanvasRules()" in printer
          and "thCanvasMade(notes)" in fn(js, "thCanvasPrint") and "fetch(" not in drawn and "api(" not in drawn)

    # ── C. in node: the box, the title, the copy laid out whole, the page and the press
    node = shutil.which("node")
    if not node:
        skip("94: the canvas print in node", "no node on this machine")
    else:
        script = scratch / "canvas-print.js"
        script.write_text(support.i18n_js() + js + r"""
const esc = (s) => String(s).replace(/[&<>]/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;' }[c]));
const said = [];
function say(m) { said.push(m); }
// A small stand-in for the page: elements in a tree, by class, tag and data, with places and sizes.
// Off the page nothing has a size, as in a browser, and a card is its four lines tall on screen and
// its whole height only under th-whole.
class El {
  constructor(tag, cls = '', o = {}) {
    this.tag = tag;
    this.cls = new Set(String(cls).split(' ').filter(Boolean));
    this.hidden = !!o.hidden;
    this.dataset = Object.assign({}, o.data || {});
    this.attrs = Object.assign({}, o.attrs || {});
    this.props = Object.assign({}, o.props || {});
    this.size = o.size || null;
    this.kids = [];
    this.up = null;
    const self = this;
    this.style = { left: '', top: '', width: '', height: '', cssText: '', removeProperty(p) { delete self.props[p]; } };
    if (o.at) { this.style.left = `${o.at.x}px`; this.style.top = `${o.at.y}px`; }
    this.classList = { contains: (c) => self.cls.has(c), remove: (...cs) => cs.forEach((c) => self.cls.delete(c)) };
  }
  set className(v) { this.cls = new Set(String(v).split(' ').filter(Boolean)); }
  get className() { return [...this.cls].join(' '); }
  setAttribute(k, v) { this.attrs[k] = String(v); }
  removeAttribute(k) { delete this.attrs[k]; }
  add(...kids) { for (const k of kids) this.appendChild(k); return this; }
  appendChild(k) { if (k.up) k.remove(); k.up = this; this.kids.push(k); return k; }
  remove() { if (this.up) { this.up.kids.splice(this.up.kids.indexOf(this), 1); this.up = null; } }
  get firstElementChild() { return this.kids[0] || null; }
  matches(sel) {
    return sel.split(',').map((s) => s.trim()).some((s) => s === '*' || (s.startsWith('.') ? this.cls.has(s.slice(1)) : this.tag === s));
  }
  all() { const out = []; const walk = (e) => { for (const k of e.kids) { out.push(k); walk(k); } }; walk(this); return out; }
  querySelectorAll(sel) { return this.all().filter((e) => e.matches(sel)); }
  cloneNode(deep) {
    const c = new El(this.tag, this.className, { hidden: this.hidden, data: this.dataset, attrs: this.attrs, props: this.props, size: this.size });
    for (const k of ['left', 'top', 'width', 'height']) c.style[k] = this.style[k];
    if (deep) for (const k of this.kids) c.appendChild(k.cloneNode(true));
    return c;
  }
  get connected() { let e = this; while (e.up) e = e.up; return e === document.body; }
  get offsetWidth() { return this.connected && this.size ? this.size.w : 0; }
  get offsetHeight() {
    if (!this.connected || !this.size) return 0;
    for (let e = this.up; e; e = e.up) if (e.cls.has('th-whole')) return this.size.whole || this.size.h;
    return this.size.h;
  }
  get innerHTML() {
    return JSON.stringify(this.all().map((e) => ({ tag: e.tag, cls: [...e.cls].sort(), hidden: e.hidden, data: e.dataset,
      tip: 'title' in e.attrs, id: 'id' in e.attrs, moved: Object.keys(e.props).length > 0,
      left: e.style.left, top: e.style.top, width: e.style.width, height: e.style.height })));
  }
}
const hosts = [];
globalThis.document = { body: new El('body'), createElement: (tag) => new El(tag),
  styleSheets: [{ cssRules: [{ cssText: '.th-card { width: 200px; }' }] }, { get cssRules() { throw new Error('closed'); } }] };
const bodyAdd = document.body.appendChild.bind(document.body);
document.body.appendChild = (k) => { hosts.push({ cls: k.className, css: k.style.cssText, hidden: k.attrs['aria-hidden'] }); return bodyAdd(k); };

// an invented board: Morning walks holds a sub-theme, Rain, with a group inside it, Puddles, and a
// note, Nights in is a block of four, Food sits just under Morning walks, two cards stand free under
// Nights in, and on GETs a participant note stands apart. Four statements run past four lines.
const LONG = new Set(['c1', 'c6', 'c8', 'c13']);
const SIZE = { g1: { w: 180, h: 30 }, g2: { w: 150, h: 26 }, g3: { w: 130, h: 26 }, g4: { w: 170, h: 30 }, g5: { w: 120, h: 30 },
  n1: { w: 120, h: 47 }, p1: { w: 200, h: 84, whole: 204 } };
const v = { cards: {}, groups: [], discarded: ['c15'], picks: {},
  stickies: [{ id: 'n1', text: 'ask about the rain', colour: 'yellow', x: 100, y: 900, in: 'g1' }] };
const column = { g1: ['c1', 'c2', 'c4', 'c6', 'c7', 'c5', 'c3'], g4: ['c8', 'c9', 'c10', 'c11'] };
for (let i = 1; i <= 15; i += 1) {
  const key = `c${i}`;
  SIZE[key] = LONG.has(key) ? { w: 200, h: 84, whole: 164 } : { w: 200, h: 62 };
  v.cards[key] = { key, text: LONG.has(key) ? `A long invented statement, ${key}, ${'on and on '.repeat(24)}` : `An invented statement, ${key}`,
    sheet: 'Initial', time: '01:00', x: 100, y: 100 };
}
column.g1.forEach((k, i) => Object.assign(v.cards[k], { x: 100, y: 100 + i * 110 }));
column.g4.forEach((k, i) => Object.assign(v.cards[k], { x: 1100, y: 100 + i * 110 }));
v.cards.p1 = { key: 'p1', kind: 'pn', text: `An invented participant note, ${'more and more '.repeat(20)}`, x: 1700, y: 100 };
v.groups = [
  { id: 'g1', label: 'Morning walks', members: ['c1', 'c2', 'g2', 'c3'], x: 0, y: 0 },
  { id: 'g2', label: 'Rain', members: ['c4', 'g3', 'c5'], x: 0, y: 0 },
  { id: 'g3', label: 'Puddles', members: ['c6', 'c7'], x: 0, y: 0 },
  { id: 'g4', label: 'Nights in', members: ['c8', 'c9', 'c10', 'c11'], x: 0, y: 0 },
  { id: 'g5', label: 'Food', members: ['c12'], x: 0, y: 0 }];
TH.sizes = Object.fromEntries(Object.entries(SIZE).map(([k, s]) => [k, { w: s.w, h: s.h }]));
TH.badges = { g1: 22, g2: 20, g3: 20, g4: 22, g5: 20 };
// Morning walks where the grid laid it until boardgrid (12 November 2026) set a label's sub-themes in rows across
// it: its first two cards side by side, Rain under them, its cards and Puddles one under another, then its last card
// and its note
for (const [k, x, y] of [['c1', 72, 100], ['c2', 282, 100], ['c3', 72, 548], ['c4', 86, 240], ['c5', 86, 464], ['c6', 100, 358], ['c7', 310, 358]]) {
  Object.assign(v.cards[k], { x, y });
}
Object.assign(v.stickies[0], { x: 282, y: 548 });
thArrange(v, 'g4', thSize);
let lay = thLayout(v, thSize, null);
const f1 = lay.g1.frame;
const f4 = lay.g4.frame;
Object.assign(v.cards.c12, { x: f1.x + TH_FRAME_X, y: f1.y + f1.h + 12 + TH_FRAME_Y + TH_GAP + SIZE.g5.h });
Object.assign(v.cards.c13, { x: f4.x, y: f4.y + f4.h + 12 });
Object.assign(v.cards.c14, { x: f4.x + 220, y: f4.y + f4.h + 12 });
TH.v = v;
TH.layout = thLayout(v, thSize, null);

// the canvas's world drawn from the board as thPlace draws it at rest, with a selection, a drop
// target, a note's controls, the tips, a drag's translate and the Merge on it
function worldOf(b, note) {
  const world = new El('div', 'th-world', { attrs: { id: 'th-world' } });
  const frames = new El('div', 'th-frames');
  const cards = new El('div', 'th-cards');
  const notes = new El('div', 'th-stickies');
  const labels = new El('div', 'th-labels');
  world.add(frames, cards, notes, labels, new El('div', 'th-merge', { attrs: { id: 'th-merge' }, hidden: true }));
  const layout = thLayout(b, thSize, null);
  for (const [key, c] of Object.entries(b.cards)) {
    if (b.discarded.includes(key) || (key === 'p1' && !note)) continue;
    const el = new El('div', `th-card${thParents(b)[key] !== undefined ? ' in' : ''}${key === 'c2' ? ' sel' : ''}${key === 'p1' ? ' gt-card gt-pn' : ''}`,
      { data: { key }, attrs: { title: c.text }, at: c, size: SIZE[key], props: key === 'c3' ? { translate: '4px 4px' } : {} });
    el.add(new El('p', 'th-text'), new El('div', 'th-foot'));
    cards.add(el);
  }
  for (const n of thStickies(b)) {
    notes.add(new El('div', 'th-sticky sticky-yellow alone', { data: { sticky: n.id }, attrs: { title: 'A sticky note' }, at: n, size: SIZE[n.id] })
      .add(new El('p', 'th-sticky-text'), new El('button', 'th-sticky-del'), new El('span', 'th-strip')));
  }
  for (const g of b.groups) {
    const f = layout[g.id].frame;
    frames.add(new El('div', 'th-frame hue-0', { data: { frame: g.id }, at: f, size: { w: f.w, h: f.h } }).add(new El('span', 'th-badge')));
    Object.assign(frames.kids[frames.kids.length - 1].style, { width: `${f.w}px`, height: `${f.h}px` });
    labels.add(new El('div', `th-label hue-0${g.id === 'g4' ? ' target' : ''}`, { data: { group: g.id }, attrs: { title: 'A label' }, at: g, size: SIZE[g.id] })
      .add(new El('span', 'th-words').add(new El('span', 'th-title')), new El('button', 'th-arr'), new El('button', 'th-del')));
  }
  // a frame with nothing in it to frame, hidden on screen
  frames.add(new El('div', 'th-frame hue-2', { hidden: true, at: { x: 9000, y: 9000 }, size: { w: 10, h: 10 } }));
  return world;
}
let world = worldOf(v, false);
document.body.appendChild(world);
hosts.length = 0;
const caseName = { textContent: 'P9 - Wren' };
const $ = (id) => (id === 'th-world' ? world : id === 'th-case' ? caseName : null);
const opened = [];
const tabs = [];
globalThis.window = { open: (url, name) => { opened.push([url, name]); const t = { shut: false, html: '', close() { t.shut = true; },
  document: { open() {}, write(h) { t.html += h; }, close() {} } }; tabs.push(t); return t; } };
const order = [];
let stays = false;
let saves = 0;
thTitleDone = () => order.push('title');
thNoteDone = () => order.push('note');
gtRowNoteDone = () => order.push('row');
thFlush = async () => { order.push(`flush, ${opened.length} open`); TH.dirty = stays; };
thSoon = () => { saves += 1; };
thSave = () => { saves += 1; };
const state = () => JSON.stringify({ v: TH.v, sizes: TH.sizes, layout: TH.layout, badges: TH.badges, world: world.innerHTML });
const out = {};
out.screen = { clashes: thClashes(v, thSize), heights: Object.fromEntries([...LONG].map((k) => [k, world.querySelectorAll('.th-card')
  .find((e) => e.dataset.key === k).offsetHeight])) };
out.box = [thCanvasBox([{ x: 10, y: 20, w: 100, h: 50 }, { x: -30.5, y: 200, w: 40, h: 10.2 }]), thCanvasBox([], 24),
  thCanvasBox([{ x: 0, y: 0, w: 0, h: 0 }]), thCanvasBox([{ x: 0, y: 0, w: 10, h: 10 }], 0)];
out.title = [thCanvasTitle('P9 - Wren', 'Board 2'), thCanvasTitle('  Hens,  a scratch project ', 'Board 1'), thCanvasTitle('Juno', ''),
  thCanvasTitle('P12-Ash', 'Second <go>')];

// the copy, against the same layout run on its own, and against the screen
const before = state();
const made = thCanvasCopy(true);
const copied = JSON.parse(made.html);
const whole = Object.fromEntries(Object.entries(SIZE).filter(([, s]) => s.whole).map(([k, s]) => [k, { w: s.w, h: s.whole }]));
delete whole.p1;
const again = thSnap(TH.v);
const laid = thCanvasWhole(again, whole, thSize);
const spot = (e) => ({ x: parseFloat(e.left), y: parseFloat(e.top) });
const cardsIn = copied.filter((e) => e.cls.includes('th-card'));
const at = Object.fromEntries(cardsIn.map((e) => [e.data.key, spot(e)]));
const parents = thParents(TH.v);
const holds = (gid, item) => item === gid || thAncestors(TH.v, item, parents).includes(gid)
  || (thSticky(TH.v, item) && (thSticky(TH.v, item).in === gid || thAncestors(TH.v, thSticky(TH.v, item).in, parents).includes(gid)));
const boxes = copied.filter((e) => !e.hidden && ['th-card', 'th-label', 'th-sticky', 'th-frame'].some((c) => e.cls.includes(c))).map((e) => {
  const id = e.data.key || e.data.group || e.data.sticky || e.data.frame;
  const s = e.cls.includes('th-frame') ? { w: parseFloat(e.width), h: parseFloat(e.height) } : laid.size(id);
  return { id, kind: e.cls.includes('th-frame') ? 'frame' : 'item', x: parseFloat(e.left), y: parseFloat(e.top), w: s.w, h: s.h };
});
const cross = (a, b) => a.x < b.x + b.w && b.x < a.x + a.w && a.y < b.y + b.h && b.y < a.y + a.h;
const overlaps = [];
for (let i = 0; i < boxes.length; i += 1) {
  for (let j = i + 1; j < boxes.length; j += 1) {
    const [a, b] = [boxes[i], boxes[j]];
    if (!cross(a, b)) continue;
    if (a.kind === 'frame' && b.kind === 'frame' && (holds(a.id, b.id) || holds(b.id, a.id))) continue;
    if (a.kind === 'frame' && b.kind === 'item' && holds(a.id, b.id)) continue;
    if (b.kind === 'frame' && a.kind === 'item' && holds(b.id, a.id)) continue;
    overlaps.push(`${a.id} ${b.id}`);
  }
}
const columns = {};
for (const [key, c] of Object.entries(v.cards)) {
  if (!at[key]) continue;
  const col = `${parents[key]} ${c.x}`;
  (columns[col] = columns[col] || []).push(key);
}
const sameColumnOrder = Object.values(columns).every((keys) => {
  const was = keys.slice().sort((a, b) => v.cards[a].y - v.cards[b].y).join();
  const now = keys.slice().sort((a, b) => at[a].y - at[b].y).join();
  return was === now;
});
const frameOf = (id) => copied.find((e) => e.data.frame === id);
const tops = (b, f) => ['g1', 'g4', 'g5'].sort((p, q) => f(p).y - f(q).y || f(p).x - f(q).x);
out.copy = {
  box: made.box, overlaps, clashes: thClashes(again, laid.size), sameColumnOrder,
  sameLayout: cardsIn.every((e) => at[e.data.key].x === again.cards[e.data.key].x && at[e.data.key].y === again.cards[e.data.key].y)
    && ['g1', 'g2', 'g3', 'g4', 'g5'].every((g) => frameOf(g).top === `${laid.layout[g].frame.y}px` && frameOf(g).height === `${laid.layout[g].frame.h}px`),
  columnsKept: Object.keys(at).every((k) => at[k].x === v.cards[k].x),
  noneUp: Object.keys(at).every((k) => at[k].y >= v.cards[k].y),
  nesting: JSON.stringify(thParents(again)) === JSON.stringify(parents),
  topOrder: tops(again, (g) => laid.layout[g].frame).join() === tops(v, (g) => TH.layout[g].frame).join(),
  down: { c10: at.c10.y - v.cards.c10.y, c11: at.c11.y - v.cards.c11.y, c9: at.c9.y - v.cards.c9.y, c5: at.c5.y - v.cards.c5.y,
    c12: at.c12.y - v.cards.c12.y, c13: at.c13.y - v.cards.c13.y },
  grew: Object.fromEntries(['g1', 'g2', 'g3', 'g4', 'g5'].map((g) => [g, laid.layout[g].frame.h - TH.layout[g].frame.h])),
  measured: hosts.slice(), bodyAfter: document.body.kids.length,
  stripped: copied.filter((e) => e.tag === 'button' || e.tag === 'textarea' || e.cls.some((c) => ['sel', 'target', 'alone', 'th-merge', 'th-strip',
    'th-del', 'th-arr', 'th-sticky-del'].includes(c)) || e.tip || e.id || e.moved).length,
  counts: ['th-frame', 'th-card', 'th-label', 'th-sticky', 'th-text'].map((c) => copied.filter((e) => e.cls.includes(c)).length),
  hiddenFrame: copied.filter((e) => e.cls.includes('th-frame') && e.hidden).length,
};
out.copy.unchanged = state() === before;
out.live = { sel: world.innerHTML.includes('"sel"'), del: world.querySelectorAll('button').length, tips: world.innerHTML.includes('"tip":true') };
out.page = thCanvasPage({ html: '<div class="th-cards"></div>', box: { x: -40, y: 10, w: 1200, h: 800 }, rules: thCanvasRules(),
  heading: 'P9 Wren · <Board 2>', title: 'P9 Wren - Board 2 - PETs canvas' });
(async () => {
  TH.live = true; TH.meta = { id: 'b2', name: 'Board 2' }; TH.mode = 'pets'; TH.busy = false;
  TH.dirty = true; TH.saveTimer = 1;
  const was = state();
  await thCanvasPrint();
  out.saved = { order: order.slice(), opened: opened.slice(), shut: tabs[0].shut, title: (tabs[0].html.match(/<title>(.*?)<\/title>/) || [])[1],
    heading: (tabs[0].html.match(/<h1 class="cp-title">(.*?)<\/h1>/) || [])[1], said: said.slice(),
    whole: tabs[0].html.includes('<div class="th-world th-whole" style="left: '), unchanged: state() === was, saves };
  order.length = 0; stays = true; TH.dirty = true;
  await thCanvasPrint();
  out.failed = { order: order.slice(), shut: tabs[1].shut, written: tabs[1].html.length, said: said.slice() };
  stays = false; TH.dirty = false; TH.saveTimer = null; TH.chain = null; order.length = 0;
  TH.mode = 'gets'; caseName.textContent = 'Hens, a scratch project';
  document.body.kids.splice(0);
  world = worldOf(v, true);
  document.body.appendChild(world);
  const gets = thCanvasCopy(false);
  const notes = thCanvasCopy(true);
  out.gets = { pn: gets.html.includes('gt-pn'), w: [gets.box.w, notes.box.w], h: [gets.box.h, notes.box.h] };
  await thCanvasPrint({ notes: false });
  out.getsPrint = { order: order.slice(), pn: tabs[2].html.includes('gt-pn'), title: (tabs[2].html.match(/<title>(.*?)<\/title>/) || [])[1] };
  await thCanvasPrint({ notes: true });
  out.getsNotes = tabs[3].html.includes('gt-pn');
  out.unchangedAll = state() === JSON.stringify(Object.assign(JSON.parse(was), { world: world.innerHTML })) && saves === 0;
  TH.v = { cards: {}, groups: [], discarded: [], stickies: [] };
  world = new El('div', 'th-world');
  world.add(new El('div', 'th-frame', { hidden: true, at: { x: 0, y: 0 }, size: { w: 10, h: 10 } }));
  document.body.appendChild(world);
  const count = opened.length;
  await thCanvasPrint();
  out.empty = { opened: opened.length - count, said: said[said.length - 1] };
  console.log(JSON.stringify(out));
})();
""", encoding="utf-8")
        run = subprocess.run([node, str(script)], capture_output=True, text=True, encoding="utf-8")
        if run.returncode != 0:
            check("94: the canvas print runs in node", False, run.stderr.strip()[:300])
        else:
            out = json.loads(run.stdout)
            import themes_print
            check("94: in node, the title names the case by its pseudonym as the print view does, on GETs the project, then the board",
                  out["title"] == ["P9 Wren · Board 2", "Hens, a scratch project · Board 1", "Juno", "P12 Ash · Second <go>"]
                  and [themes_print.case_title(c) for c in ("P9 - Wren", "Juno", "P12-Ash")]
                  == [out["title"][0].split(" · ")[0], out["title"][2], out["title"][3].split(" · ")[0]], str(out["title"]))
            cp = out["copy"]
            check("94: in node, the copy carries the frames, the cards, the labels and the note, the hidden frame kept hidden, and "
                  "leaves the selection, the drop target, the controls, the Merge, the tips, the ids and a drag's translate behind",
                  cp["counts"] == [6, 14, 5, 1, 14] and cp["hiddenFrame"] == 1 and cp["stripped"] == 0, str(cp["counts"]))
            check("94: in node, each card is measured whole under th-whole off screen, out of sight, and the host is gone again",
                  len(cp["measured"]) == 1 and cp["measured"][0]["cls"] == "th-whole" and cp["measured"][0]["hidden"] == "true"
                  and "visibility: hidden;" in cp["measured"][0]["css"] and "left: -100000px;" in cp["measured"][0]["css"]
                  and cp["bodyAfter"] == 1, str(cp["measured"]))
            check("94: in node, the copy stands where the canvas's own layout puts the board with every statement whole, and the box "
                  "round it takes their whole heights",
                  cp["sameLayout"] is True and cp["box"]["h"] > 0
                  and all(cp["grew"][g] >= 80 for g in ("g1", "g2", "g3", "g4")) and cp["grew"]["g5"] == 0, str(cp["grew"]))
            check("94: in node, no box overlaps another in the copy, a frame meeting only what it holds or what holds it, and no "
                  "neighbours come inside the margin",
                  cp["overlaps"] == [] and cp["clashes"] == [], ", ".join(cp["overlaps"][:4]) + str(cp["clashes"][:2]))
            down = cp["down"]
            check("94: in node, what lies below a longer card moves down and nothing moves up or sideways: the card under it, the "
                  "card under its group, the PET under its PET and the cards under Nights in, while a card beside it stays",
                  down["c10"] >= 80 and down["c5"] >= 160 and down["c12"] >= 150 and down["c13"] >= 70 and down["c11"] == 0 and down["c9"] == 0
                  and cp["columnsKept"] is True and cp["noneUp"] is True, str(down))
            check("94: in node, the copy keeps the screen's columns, its nesting and its order, down each column and among the PETs",
                  cp["sameColumnOrder"] is True and cp["nesting"] is True and cp["topOrder"] is True)
            check("94: in node, the canvas's own state is unchanged by the copy and by every print: its board, its sizes, its layout, "
                  "its elements, and no save asked for",
                  cp["unchanged"] is True and out["saved"]["unchanged"] is True and out["unchangedAll"] is True and out["saved"]["saves"] == 0
                  and out["live"] == {"sel": True, "del": 11, "tips": True}, str(out["live"]))
            saved, failed = out["saved"], out["failed"]
            check("94: in node, a press with a save to go opens the tab first, saves, then writes the page into it, unclamped, its "
                  "title the case and the board",
                  saved["opened"] == [["about:blank", "_blank"]] and saved["order"] == ["title", "note", "flush, 1 open"]
                  and saved["shut"] is False and saved["title"] == "P9 Wren - Board 2 - PETs canvas"
                  and saved["heading"] == "P9 Wren · Board 2" and saved["said"] == [] and saved["whole"] is True, str(saved)[:200])
            check("94: in node, a save that fails shuts the tab with the print view's line and writes nothing, and a canvas with "
                  "nothing on it says so and opens no tab",
                  failed["shut"] is True and failed["written"] == 0
                  and failed["said"] == ["The canvas is not saved yet, so nothing was printed."]
                  and out["empty"] == {"opened": 0, "said": "There is nothing on the canvas to print."}, str(failed))
            check("94: in node, on GETs the title is the project's and the board's, participant notes only with the tick, whole with "
                  "it and left out of the box without it, and the row note put away first",
                  out["getsPrint"]["order"] == ["title", "note", "row"] and out["getsPrint"]["pn"] is False
                  and out["getsPrint"]["title"] == "Hens, a scratch project - Board 2 - GETs canvas" and out["getsNotes"] is True
                  and out["gets"]["pn"] is False and out["gets"]["w"][0] < out["gets"]["w"][1], str(out["gets"]))
