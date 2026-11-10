"""Area 233: a PET card unfolds in place on the GETs board (Adam's ruling of 20 October 2026, topic 9, from a tester's
wish to see a PET's statements on GETs). The chevron on a PET's or a sub-theme's count, or Unfold in its menu,
shows under the card its sub-themes and each statement with its quote, its exploratory notes when Notes on cards
is on, and a stack under its top, and folds again. Nothing is placed: no card comes on the board, the board's data
stays byte for byte the same, nothing is saved and nothing is a step of undo. Which cards are unfolded is kept in
the browser with the board's view, by project and board, so a reload shows them unfolded. The room the taller
card takes is a view, given back when it folds, and Arrange and Fit all take its height.

The checks hold behaviour in node, on an invented project about keeping an allotment."""
from __future__ import annotations

import json
import shutil
import subprocess

from . import support
from .support import check, skip


def test_unfold(scratch):
    print("\n233. A PET card unfolds in place on GETs, nothing placed, kept across a reload (Adam, 20 October)")
    node = shutil.which("node")
    if not node:
        skip("233: unfolding in node", "node is not installed")
        return
    js = support.text("apps/idiograph/static/themes.js")
    script = scratch / "unfold-233.js"
    script.write_text(support.i18n_js() + STUBS + js + SCENARIO, encoding="utf-8")
    run = subprocess.run([node, str(script)], capture_output=True, text=True, encoding="utf-8", timeout=120)
    if run.returncode != 0:
        check("233: unfolding runs in node", False, run.stderr.strip()[:800])
        return
    o = json.loads(run.stdout)
    check("233: an unfolded PET card shows its own statements, then its sub-theme by its title with the statements under "
          "it, each with its own quote and timecode, a stacked statement under its top and never on its own, and a "
          "statement of another PET not at all",
          o["html"] == {"own": True, "sub": True, "subLine": True, "quote": True, "time": True, "stacked": True,
                        "stackOnce": True, "other": False, "notes": False}, str(o["html"]))
    check("233: with Notes on cards on, each statement shows its exploratory notes too, and a statement card, a "
          "participant note and a PET with nothing in it have no chevron and no Unfold",
          o["notes"] and o["able"] == {"pet": True, "sub": True, "es": False, "pn": False, "empty": False}, str(o["able"]))
    check("233: the menu of a PET card has Unfold after Inspect, and Fold once unfolded",
          o["menu"] == ["Unfold", "Fold"], str(o["menu"]))
    check("233: unfold and fold leave the board to save byte for byte the same, its cards the same keys, nothing saved, "
          "nothing marked to save and no step of undo",
          o["data"] == {"unfolded": True, "folded": True, "keys": True, "saved": 0, "dirty": False, "undo": 0}, str(o["data"]))
    check("233: which cards are unfolded is kept in the browser by project and board, read back after a reload, another "
          "board starting folded and a card no longer on the board left out, and none kept once all fold",
          o["kept"] == {"reload": ["Hale/g1"], "other": [], "gone": [], "empty": True}, str(o["kept"]))
    check("233: the unfolded part is measured as room the card takes, the card below moves down for it with the file "
          "keeping where it stood, Arrange and Fit all reading the whole height, and folded it all goes back",
          o["room"] == {"extra": 300, "below": 440, "kept": 140, "size": 390, "back": 140}, str(o["room"]))


STUBS = r"""
const ELS = {};
class El {
  constructor(id) {
    this.id = id; this.cls = new Set(); this.attrs = {}; this.hidden = false; this.innerHTML = ''; this.title = '';
    this.dataset = {}; this.offsetWidth = 200; this.offsetHeight = 90; this.found = [];
    const self = this;
    this.style = { setProperty: () => {} };
    this.classList = { add: (...n) => n.forEach((x) => self.cls.add(x)), remove: (...n) => n.forEach((x) => self.cls.delete(x)),
      contains: (n) => self.cls.has(n),
      toggle: (n, on) => { if (on === undefined) on = !self.cls.has(n); if (on) self.cls.add(n); else self.cls.delete(n); return on; } };
  }
  get textContent() { return String(this.innerHTML).replace(/<[^>]*>/g, ''); }
  set textContent(v) { this.innerHTML = String(v); }
  setAttribute(k, v) { this.attrs[k] = String(v); }
  getAttribute(k) { return this.attrs[k]; }
  getBoundingClientRect() { return { left: 0, top: 0, right: 200, bottom: 90, width: 200, height: 90 }; }
  querySelector() { return null; }
  querySelectorAll() { return this.found; }
}
const $ = (id) => ELS[id] || null;
const esc = (s) => String(s).replace(/[&<>]/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;' }[c]));
const escAttr = (s) => esc(s).replace(/"/g, '&quot;');
const say = () => {};
const SAVED = [];
const api = async (path, body) => { SAVED.push(body); return {}; };
const needsRestart = () => false;
const RESTART_LINE = 'Restart';
const PLAY_GLYPH = '>';
const PAUSE_GLYPH = '||';
const MAC = true;
const MOD = (e) => e.metaKey;
const STORE = new Map();
globalThis.localStorage = { getItem: (k) => (STORE.has(k) ? STORE.get(k) : null), setItem: (k, v) => { STORE.set(k, String(v)); },
  removeItem: (k) => { STORE.delete(k); } };
globalThis.window = { innerWidth: 1280, innerHeight: 800, matchMedia: () => ({ matches: false }) };
globalThis.requestAnimationFrame = () => 0;
globalThis.cancelAnimationFrame = () => {};
globalThis.setTimeout = () => 0;
globalThis.clearTimeout = () => {};
globalThis.document = { elementFromPoint: () => null, querySelectorAll: () => [] };
"""

SCENARIO = r"""
(async () => {
const out = {};
let renders = 0;
thRender = () => { renders += 1; };
thEase = () => {};
thSoon = () => {};
thPanelFollow = () => {};
thDrawSel = () => {};
gtCasesDraw = () => {};

TH.mode = 'gets';
TH.live = true;
TH.path = '/allotment/P1/P1.xlsx';
TH.meta = { id: 'b1', name: 'Board 1', created: 'x', updated: 'x', v: 'v1' };
TH.config = { card_notes: false };
TH.sheets = ['Initial'];
const line = (text, time, quote, extra = {}) => Object.assign({ text, sheet: 'Initial', row: Number(time.replace(':', '')), time,
  quotes: quote ? [quote] : [], notes: ['Soil as something to wait on'] }, extra);
TH.gets = { cases: [{ case: 'Hale', who: 'Hale', in: true,
  pets: [{ id: 'g1', parent: null, title: 'Waiting on the soil', statements: ['Initial:3:0', 'Initial:4:0', 'Initial:5:0'], subs: ['g2'] },
         { id: 'g2', parent: 'g1', title: 'First frost', statements: ['Initial:9:0'], subs: [] },
         { id: 'g3', parent: null, title: 'Other plots', statements: ['Initial:12:0'], subs: [] },
         { id: 'g4', parent: null, title: 'Nothing yet', statements: [], subs: [] }],
  lines: { 'Initial:3:0': line('Turning the beds in March', '3:10', '‘the ground tells you when’'),
           'Initial:4:0': line('Leaving it fallow a year', '4:02', ''),
           'Initial:5:0': line('A second year fallow', '5:20', '‘again, nothing’', { stacked: 'Initial:4:0' }),
           'Initial:9:0': line('Frost on the leeks', '9:45', '‘black by the morning’'),
           'Initial:12:0': line('The neighbour’s greenhouse', '12:00', '') } }] };
const card = (kind, x, y, text) => ({ kind, case: 'Hale', who: 'Hale', x, y, text, statements: 4 });
const v = { cards: { 'Hale/g1': card('pet', 0, 40, 'Waiting on the soil'), 'Hale/g2': card('sub', 220, 40, 'First frost'),
                     'Hale/g4': card('pet', 440, 40, 'Nothing yet'), 'Hale/es/Initial:12:0': card('es', 0, 140, 'The neighbour’s greenhouse'),
                     'Hale/pn/1': card('pn', 220, 140, 'A note') },
            groups: [], discarded: [], picks: {}, stickies: [] };
TH.v = v;
TH.removed = new Set();
TH.undo = []; TH.redo = [];

// ── what it shows
const html = gtUnfoldHtml('Hale/g1', v.cards['Hale/g1']);
const at = (s) => html.indexOf(s);
out.html = { own: at('Turning the beds in March') > 0 && at('Leaving it fallow a year') > 0,
  sub: at('First frost') > at('Leaving it fallow a year'), subLine: at('Frost on the leeks') > at('First frost'),
  quote: html.includes('‘the ground tells you when’') && html.includes('‘black by the morning’'),
  time: html.includes('3:10') && html.includes('9:45'),
  stacked: at('A second year fallow') > at('Leaving it fallow a year') && html.slice(at('Leaving it fallow a year'), at('A second year fallow')).includes('gt-ustack'),
  stackOnce: html.split('A second year fallow').length === 2,
  other: html.includes('greenhouse'), notes: html.includes('Soil as something to wait on') };
TH.config = { card_notes: true };
out.notes = gtUnfoldHtml('Hale/g1', v.cards['Hale/g1']).includes('Soil as something to wait on');
TH.config = { card_notes: false };
out.able = { pet: gtUnfoldable('Hale/g1', v.cards['Hale/g1']), sub: gtUnfoldable('Hale/g2', v.cards['Hale/g2']),
  es: gtUnfoldable('Hale/es/Initial:12:0', v.cards['Hale/es/Initial:12:0']), pn: gtUnfoldable('Hale/pn/1', v.cards['Hale/pn/1']),
  empty: gtUnfoldable('Hale/g4', v.cards['Hale/g4']) };
out.able.es = out.able.es || !!gtCardHtml(v, 'Hale/es/Initial:12:0', v.cards['Hale/es/Initial:12:0'], {}).includes('data-unfold');

// ── the menu
const label = () => gtMenuItems(v, { kind: 'card', id: 'Hale/g1' }, [{ label: 'Inspect', act: 'inspect' }, { label: 'Set aside', act: 'discard' }])[1].label;
out.menu = [label()];

// ── the data: unfold and fold change nothing the board saves
const body0 = JSON.stringify(thBody(v, TH.meta));
const keys0 = Object.keys(v.cards).join();
gtUnfold('Hale/g1');
const drawn = renders;
out.menu.push(label());
const unfoldedBody = JSON.stringify(thBody(v, TH.meta)) === body0;
const kept = STORE.get(GT_UNFOLD_KEY);
gtUnfold('Hale/g1');
out.data = { unfolded: unfoldedBody && drawn === 1, folded: JSON.stringify(thBody(v, TH.meta)) === body0,
  keys: Object.keys(v.cards).join() === keys0, saved: SAVED.length, dirty: !!TH.dirty, undo: TH.undo.length };

// ── kept across a reload, by board
STORE.set(GT_UNFOLD_KEY, kept);
gtUnfoldRead(v.cards);
const reload = [...TH.unfolded];
TH.meta = Object.assign({}, TH.meta, { id: 'b2' });
gtUnfoldRead(v.cards);
const other = [...TH.unfolded];
TH.meta = Object.assign({}, TH.meta, { id: 'b1' });
gtUnfoldRead({ 'Hale/g2': v.cards['Hale/g2'] });
out.kept = { reload, other, gone: [...TH.unfolded], empty: false };
// folding the last one takes the board's entry away
TH.unfolded = new Set(['Hale/g1']);
gtUnfold('Hale/g1');
out.kept.empty = !Object.keys(JSON.parse(STORE.get(GT_UNFOLD_KEY) || '{}')).length && kept.includes('Hale/g1');

// ── the room: measured from the unfolded part, a view the file never keeps
const r = { cards: { a: card('pet', 0, 40, 'A'), b: card('pet', 0, 140, 'B') }, groups: [], discarded: [], picks: {}, stickies: [] };
TH.v = r;
TH.opened = new Set(); TH.shifts = []; TH.roomShown = null;
const part = new El('part'); part.offsetHeight = 300;
const a = new El('a'); a.offsetHeight = 390; a.found = [part];
const b = new El('b'); b.found = [];
TH.els = { cards: { a, b }, under: {}, labels: {}, frames: {}, stickies: {}, rails: {} };
thMeasure();
const extra = TH.qextra.a;
thStacksRoom();
const below = r.cards.b.y;
const keptY = JSON.parse(JSON.stringify(thBody(r, TH.meta))).cards.b.y;
const size = thSize('a').h;
a.offsetHeight = 90; a.found = [];
thMeasure();
thStacksRoom();
out.room = { extra, below, kept: keptY, size, back: r.cards.b.y };
console.log(JSON.stringify(out));
})().catch((err) => { console.error(err && err.stack ? err.stack : String(err)); process.exit(1); });
"""
