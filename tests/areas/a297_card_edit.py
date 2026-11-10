"""Area 297: a double-click on a statement card edits its statement on the card (cardedit, 30 October 2026).

Adam, 30 October: a double-click on a PET's or a sub-PET's title opens it for renaming, but one on a statement card
took him to its passage on Experiential statements, so for consistency it should edit the statement. On the PETs
board a statement card's double-click now opens the card's editor, the one the Inspector's double-click opens:
the whole statement in a box where its words were, Enter or a click away keeping it through `/api/edit-statement`,
Esc leaving it, an empty one refused. Go to the passage in the card's menu still opens the passage. On the GETs board
a statement card's double-click went to the passage until getsedit (Adam, 30 October, later: "Edit there too"), and
now opens the same editor, a PET's card still its Inspector (area 298 holds the rest).

The checks run `thPointerUp` and the editor in node on themes.js's own code, the route stubbed. Every word
invented: a learner of the cello on her first year of lessons.
"""
from __future__ import annotations

import json
import shutil

from . import support
from .support import check as said_check, skip


def check(name, ok, detail=""):
    said_check(name, ok, str(detail)[:700])


LONG = ("Practising scales every morning before work until the bow stopped shaking in her hand, which took most of the "
        "winter and a good deal of patience with the neighbours, and with herself, as the notes came out thin at first")

STUBS = r"""
// just enough page for a card and its editor: elements with children, classes, handlers and the box's value
const ELS = {};
class El {
  constructor(tag, cls) {
    this.tagName = String(tag || 'div').toUpperCase(); this.cls = new Set(String(cls || '').split(' ').filter(Boolean));
    this.attrs = {}; this.hidden = false; this.innerHTML = ''; this.title = ''; this.value = ''; this.dataset = {};
    this.children = []; this.parentNode = null; this.handlers = {}; this.focused = false; this.selected = false;
    this.scrollHeight = 60; this.offsetWidth = 200; this.offsetHeight = 90;
    const self = this;
    this.style = { setProperty: () => {} };
    this.classList = { add: (...n) => n.forEach((x) => self.cls.add(x)), remove: (...n) => n.forEach((x) => self.cls.delete(x)),
      contains: (n) => self.cls.has(n),
      toggle: (n, on) => { if (on === undefined) on = !self.cls.has(n); if (on) self.cls.add(n); else self.cls.delete(n); return on; } };
  }
  set className(v) { this.cls = new Set(String(v).split(' ').filter(Boolean)); }
  get className() { return [...this.cls].join(' '); }
  setAttribute(k, v) { this.attrs[k] = String(v); }
  getAttribute(k) { return this.attrs[k]; }
  addEventListener(kind, fn) { (this.handlers[kind] = this.handlers[kind] || []).push(fn); }
  fire(kind, e = {}) { for (const fn of this.handlers[kind] || []) fn(Object.assign({ stopPropagation: () => {}, preventDefault: () => {} }, e)); }
  appendChild(n) { n.parentNode = this; this.children.push(n); return n; }
  insertBefore(n, ref) { n.parentNode = this; const i = this.children.indexOf(ref); this.children.splice(i < 0 ? this.children.length : i, 0, n); return n; }
  after(n) { const p = this.parentNode; n.parentNode = p; p.children.splice(p.children.indexOf(this) + 1, 0, n); }
  querySelector(sel) {
    const want = sel.startsWith('.') ? sel.slice(1) : null;
    for (const c of this.children) {
      if (want && c.cls.has(want)) return c;
      const deeper = c.querySelector(sel);
      if (deeper) return deeper;
    }
    return null;
  }
  querySelectorAll() { return []; }
  closest() { return null; }
  focus() { this.focused = true; }
  select() { this.selected = true; }
  get selectionStart() { return this.value.length; }
  setSelectionRange() {}
  getBoundingClientRect() { return { left: 0, top: 0, right: 200, bottom: 90, width: 200, height: 90 }; }
  releasePointerCapture() {}
  setPointerCapture() {}
}
const $ = (id) => ELS[id] || null;
const esc = (s) => String(s).replace(/[&<>]/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;' }[c]));
const escAttr = (s) => esc(s).replace(/"/g, '&quot;');
const SAID = [];
const say = (line) => { SAID.push(line); };
const CALLS = [];
const api = async (path, body) => {
  CALLS.push([path, body]);
  if (body && body.check) return { ready: true, copies: true };
  return { text: String(body.text).trim(), old: body.old, changed: true, versions: [] };
};
const needsRestart = () => false;
const RESTART_LINE = 'Restart';
const PLAY_GLYPH = '>';
const PAUSE_GLYPH = '||';
const MAC = true;
const MOD = (e) => e.metaKey;
globalThis.localStorage = { getItem: () => null, setItem: () => {} };
globalThis.window = { innerWidth: 1280, innerHeight: 800, matchMedia: () => ({ matches: false }) };
globalThis.requestAnimationFrame = () => 0;
globalThis.cancelAnimationFrame = () => {};
globalThis.document = { elementFromPoint: () => null, querySelectorAll: () => [], createElement: (tag) => new El(tag),
  activeElement: null, fonts: { ready: Promise.resolve() } };
"""

SCENARIO = r"""
(async () => {
const want = JSON.parse(process.env.CE_WANT);
const out = {};
const tick = () => new Promise((r) => setImmediate(r));
ELS['th-stage'] = new El('div', 'th-stage');
// what the double-click must not reach, and what it may, recorded
const went = [];
thToPassage = (key) => { went.push(['passage', key]); };
thTitleOpen = (id) => { went.push(['title', id]); };
gtCardOpen = (key) => { went.push(['inspector', key]); };
thKqOpen = (key) => { went.push(['quote', key]); };
thStickyEditOpen = (id) => { went.push(['sticky', id]); };
thRender = () => {}; thDrawSel = () => {}; thPanelFollow = () => {}; thPanelDraw = () => {}; thPlace = () => {};
thSoon = () => {}; thNoteDone = () => {}; thStickyEditDone = () => {}; thMenuClose = () => {};
thFileBoxes = () => ({});
thInFile = () => false;

// a card as the board draws it: its words, its quote when the quotes show, its foot
const card = (key, text, quote) => {
  const el = new El('div', 'th-card');
  el.dataset.key = key;
  const words = new El('p', 'th-text'); words.innerHTML = esc(text);
  el.appendChild(words);
  if (quote) el.appendChild(new El('blockquote', 'th-kq'));
  el.appendChild(new El('div', 'th-foot'));
  return el;
};
const v = {
  cards: {
    'Lessons:4:0': { x: 0, y: 40, text: want.long, time: '3:10', sheet: 'Lessons', row: 4, line: 0 },
    'Lessons:6:0': { x: 210, y: 40, text: 'The teacher moving her elbow an inch', time: '5:02', sheet: 'Lessons', row: 6, line: 0 },
    'Lessons:9:0': { x: 0, y: 200, text: 'Playing for no one in the kitchen', time: '9:40', sheet: 'Lessons', row: 9, line: 0 },
    'Lessons:9:1': { x: 0, y: 200, text: 'Playing alone at night', time: '9:40', sheet: 'Lessons', row: 9, line: 1 },
  },
  groups: [{ id: 'g1', label: 'The body learning first', members: ['Lessons:4:0', 'Lessons:6:0'], x: 0, y: 0 }],
  discarded: [], stacks: { 'Lessons:9:0': ['Lessons:9:1'] }, stickies: [],
};
TH.mode = 'pets'; TH.live = true; TH.busy = false; TH.path = '/study/P1 - Wren.xlsx'; TH.v = v; TH.removed = [];
TH.sel = { cards: new Set(), groups: new Set(), stickies: new Set() };
TH.undo = []; TH.redo = []; TH.opened = new Set(['Lessons:9:0']);
TH.els = { cards: { 'Lessons:4:0': card('Lessons:4:0', want.long, true), 'Lessons:6:0': card('Lessons:6:0', v.cards['Lessons:6:0'].text),
                    'Lessons:9:0': card('Lessons:9:0', v.cards['Lessons:9:0'].text) },
           under: { 'Lessons:9:1': card('Lessons:9:1', v.cards['Lessons:9:1'].text) }, labels: {}, frames: {}, stickies: {}, rails: {} };

// a click, then a second on the same thing, as the canvas hears them
const press = (item, kq = false) => {
  TH.press = { item, x0: 0, y0: 0, add: false, alt: false, kq };
  thPointerUp({ pointerId: 1, clientX: 0, clientY: 0 });
};
const twice = async (item, kq = false) => { TH.lastClick = null; press(item, kq); press(item, kq); await tick(); await tick(); };
const boxOf = (el) => el.children.find((c) => c.cls.has('th-card-edit')) || null;
const key = (e, k) => { e.fire('keydown', { key: k, isComposing: false }); };

// ── 1. a double-click on a long statement's card opens it whole on the card, never its passage
await twice({ kind: 'card', id: 'Lessons:4:0' });
const el1 = TH.els.cards['Lessons:4:0'];
const box1 = boxOf(el1);
out.open = {
  went: went.slice(), editing: TH.cardEdit ? TH.cardEdit.key : null, panel: TH.cardEdit ? TH.cardEdit.panel : null,
  whole: box1 ? box1.value === want.long : false, focused: !!(box1 && box1.focused && box1.selected),
  wordsHidden: el1.querySelector('.th-text').hidden, order: el1.children.map((c) => [...c.cls][0]),
  checked: CALLS.filter(([p, b]) => p === '/api/edit-statement' && b.check).length,
};
// ── 2. new words and Enter: written through the route the Inspector's edit takes, one step of undo
box1.value = 'Practising scales\nevery morning until the bow held still';
box1.fire('input');
key(box1, 'Enter');
await tick(); await tick();
const writes = () => CALLS.filter(([p, b]) => p === '/api/edit-statement' && !b.check).map(([, b]) => b);
out.saved = { writes: writes(), text: v.cards['Lessons:4:0'].text, undo: TH.undo.map((u) => [u.what, u.edit && u.edit.key]),
  closed: TH.cardEdit === null, went: went.slice() };

// ── 3. Esc leaves the words as they were and writes nothing
await twice({ kind: 'card', id: 'Lessons:6:0' });
const box2 = boxOf(TH.els.cards['Lessons:6:0']);
box2.value = 'Something else entirely';
key(box2, 'Escape');
await tick();
out.esc = { opened: !!box2, text: v.cards['Lessons:6:0'].text, writes: writes().length, closed: TH.cardEdit === null };

// ── 4. an empty statement refused, as the Inspector refuses it: Enter says so and the box stays open
await twice({ kind: 'card', id: 'Lessons:6:0' });
const box3 = TH.cardEdit && TH.cardEdit.box;
box3.value = '   ';
SAID.length = 0;
key(box3, 'Enter');
await tick();
out.empty = { said: SAID.slice(), open: !!TH.cardEdit, writes: writes().length, text: v.cards['Lessons:6:0'].text };
key(box3, 'Escape');

// ── 5. a stack's top and a card of a stack shown open open the same way
await twice({ kind: 'card', id: 'Lessons:9:0' });
out.top = TH.cardEdit ? TH.cardEdit.key : null;
key(TH.cardEdit.box, 'Escape');
await twice({ kind: 'card', id: 'Lessons:9:1' });
out.under = { key: TH.cardEdit ? TH.cardEdit.key : null, inCard: !!boxOf(TH.els.under['Lessons:9:1']) };
key(TH.cardEdit.box, 'Escape');

// ── 6. a double-click on the quote shows it whole and edits nothing
went.length = 0;
await twice({ kind: 'card', id: 'Lessons:4:0' }, true);
out.quote = { went: went.slice(), editing: !!TH.cardEdit };

// ── 7. a title's double-click is as it was, and Go to the passage in the card's menu still goes there
went.length = 0;
await twice({ kind: 'group', id: 'g1' });
TH.menu = { item: { kind: 'card', id: 'Lessons:6:0' } };
thMenuDo({ act: 'passage' });
out.title = went.slice();
out.menu = thMenuItems(v, { kind: 'card', id: 'Lessons:6:0' }).map((m) => m && m.label).filter(Boolean);

// ── 8. on the GETs board a statement card opens the same editor since getsedit, and another card its Inspector
went.length = 0;
TH.mode = 'gets';
const gv = { cards: { 'Ivo/es/Lessons:4:0': { x: 0, y: 0, kind: 'es', case: 'Ivo', text: 'A first open string' },
                      'Ivo/g1': { x: 210, y: 0, kind: 'pet', case: 'Ivo', text: 'Learning by ear' } },
             groups: [], discarded: [] };
TH.v = gv;
TH.gets = { cases: [{ case: 'Ivo', who: 'Ivo', path: '/study/P2 - Ivo.xlsx', lines: {} }] };
TH.els = { cards: { 'Ivo/es/Lessons:4:0': card('Ivo/es/Lessons:4:0', 'A first open string'), 'Ivo/g1': card('Ivo/g1', 'Learning by ear') },
           under: {}, labels: {}, frames: {}, stickies: {}, rails: {} };
await twice({ kind: 'card', id: 'Ivo/es/Lessons:4:0' });
const opened = TH.cardEdit ? TH.cardEdit.key : null;
if (TH.cardEdit) key(TH.cardEdit.box, 'Escape');
await twice({ kind: 'card', id: 'Ivo/g1' });
out.gets = { went: went.slice(), editing: opened };
console.log(JSON.stringify(out));
})().catch((err) => { console.error(err && err.stack || String(err)); process.exit(1); });
"""


def test_card_edit(scratch):
    print("\n297. A double-click on a statement card edits its statement on the card, as a title's opens the title, "
          "Enter saving through the route the Inspector's edit takes, Esc leaving it, an empty one refused, Go to the "
          "passage still in the card's menu, and the GETs board's statement cards opening the same editor "
          "(Adam, 30 October)")
    node = shutil.which("node")
    if not node:
        skip("297: the card's double-click in node", "node is not installed")
        return
    import os
    js = support.text("apps/idiograph/static/themes.js")
    env = dict(os.environ, CE_WANT=json.dumps({"long": LONG}))
    path = scratch / "card-edit-297.js"
    path.write_text(support.i18n_js() + STUBS + js + SCENARIO, encoding="utf-8")
    import subprocess
    run = subprocess.run([node, str(path)], capture_output=True, text=True, encoding="utf-8", timeout=120, env=env)
    if run.returncode != 0:
        check("297: the card's double-click runs in node", False, run.stderr.strip()[:800])
        return
    o = json.loads(run.stdout)
    op = o["open"]
    check("297: in node, a double-click on a statement card on the PETs board opens its editor on the card, not its "
          "passage, the whole of a long statement in the box, focused and selected, the words hidden and the quote "
          "still under the box",
          op["went"] == [] and op["editing"] == "Lessons:4:0" and op["panel"] is False and op["whole"] and op["focused"]
          and op["wordsHidden"] is True and op["order"] == ["th-text", "th-title-edit", "th-kq", "th-foot"]
          and op["checked"] == 1, op)
    sv = o["saved"]
    check("297: in node, Enter saves the new words through /api/edit-statement with the card's sheet, row and line and "
          "what it read, a line break made a space, the card takes them and undo holds one step",
          sv["writes"] == [{"workbook": "/study/P1 - Wren.xlsx", "sheet": "Lessons", "row": 4, "line": 0,
                            "text": "Practising scales every morning until the bow held still", "old": LONG}]
          and sv["text"] == "Practising scales every morning until the bow held still"
          and sv["undo"] == [["Edited a statement", "Lessons:4:0"]] and sv["closed"] and sv["went"] == [], sv)
    es = o["esc"]
    check("297: in node, Esc closes the box and leaves the words as they were, nothing written",
          es["opened"] and es["text"] == "The teacher moving her elbow an inch" and es["writes"] == 1 and es["closed"], es)
    em = o["empty"]
    check("297: in node, an empty statement is refused with the Inspector's line, the box left open and nothing written",
          len(em["said"]) == 1 and em["said"][0] and em["open"] and em["writes"] == 1
          and em["text"] == "The teacher moving her elbow an inch", em)
    check("297: in node, a stack's top and a card of a stack shown open open the editor on their own card",
          o["top"] == "Lessons:9:0" and o["under"] == {"key": "Lessons:9:1", "inCard": True}, [o["top"], o["under"]])
    check("297: in node, a double-click on a card's quote shows the quote whole on each click and opens no editor",
          o["quote"] == {"went": [["quote", "Lessons:4:0"], ["quote", "Lessons:4:0"]], "editing": False}, o["quote"])
    check("297: in node, a title's double-click still opens the title, and Go to the passage in the card's menu is "
          "there and still calls thToPassage",
          o["title"] == [["title", "g1"], ["passage", "Lessons:6:0"]] and "Go to the passage" in o["menu"],
          [o["title"], o["menu"]])
    check("297: in node, on the GETs board a statement card's double-click opens the same editor, never its passage, "
          "and a PET card's its Inspector",
          o["gets"] == {"went": [["inspector", "Ivo/g1"]], "editing": "Ivo/es/Lessons:4:0"}, o["gets"])
