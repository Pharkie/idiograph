"""Area 241: quote first on the statements screen (Adam, 21 October 2026, from a tester, who selects the words first
and then writes the statement).

The arrow beside each statement's quote, lit while words are selected in the passage, takes them as that
statement's quote, as Q and the selection's Quote do, and the save carries it to the workbook as Q's does. Each
statement's box stands level with its own quote once the quote is set, never before, stacked under the box
before it where two quotes stand close, and never moved by typing. Quotes on the status bar, off, folds each
quote to a line, and that is kept in the settings across a restart.

The checks hold behaviour: the quote the arrow sets and the save it makes, where a box goes and when, and the
setting kept. The bar's words and its look go to Adam as review shots. The node fixture is invented, about
flying a kite on a hill.
"""
from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path

from . import support
from .support import check, skip


def test_quote_first(scratch):
    print("\n241. Quote first: the arrow by a statement's quote, its box level with its quote, and Quotes folded "
          "on the status bar, kept (Adam, 21 October)")
    import server as server_mod

    # ── the setting: shown whole on a new install, folded kept across a restart
    cfg = scratch / "es-quotes-config.json"
    cfg.write_text(json.dumps({"projects": [], "interviewer": "Adam"}), encoding="utf-8")
    kept = (server_mod.CONFIG_PATH, server_mod.ROOT_OVERRIDE, server_mod.STATE_MEMORY)
    try:
        server_mod.CONFIG_PATH, server_mod.ROOT_OVERRIDE = cfg, None
        server_mod.STATE_MEMORY = {"recent": []}
        fresh = server_mod.merge_config({})
        server_mod.api_settings({"es_quotes": False})
        saved = json.loads(cfg.read_text(encoding="utf-8"))
        restarted = server_mod.merge_config(saved)
        server_mod.api_settings({"es_quotes": True})
        back = server_mod.merge_config(json.loads(cfg.read_text(encoding="utf-8")))
        check("241: Quotes shows each quote whole on a new install, off is kept in the settings file beside the "
              "interviewer and read back off after a restart, and on again read back on",
              fresh["es_quotes"] is True and saved.get("es_quotes") is False and saved.get("interviewer") == "Adam"
              and restarted["es_quotes"] is False and back["es_quotes"] is True,
              str({"fresh": fresh.get("es_quotes"), "saved": saved.get("es_quotes"), "back": back.get("es_quotes")}))
    finally:
        server_mod.CONFIG_PATH, server_mod.ROOT_OVERRIDE, server_mod.STATE_MEMORY = kept

    node = shutil.which("node")
    if not node:
        skip("241: the arrow and the boxes in node", "node is not installed")
        return
    read = lambda path: Path(path).read_text(encoding="utf-8")
    app, quote_js = support.text("family/static/shell.js", "apps/idiograph/static/distil.js"), support.text("family/static/quote.js")
    fn = lambda src, name: src.split(f"function {name}(", 1)[1].split("\n}", 1)[0] if f"function {name}(" in src else ""
    whole = lambda src, name: ("async " if f"async function {name}(" in src else "") + f"function {name}(" + fn(src, name) + "\n}"
    line = lambda src, start: start + src.split(start, 1)[1].split("\n", 1)[0] if start in src else ""

    harness = r"""
let MAC = true;
let pairSeq = 0;
let LIVE = null;
const PROMPT_FALLBACK = 'A prompt';
const S = { prompt: '', pairFocus: null, dirty: false, pending: [], undoStack: [], redoStack: [],
  data: { path: 'kite.xlsx', config: {} }, undoBusy: false, note: null, quoting: false };
const escAttr = (s) => String(s).replace(/"/g, '&quot;');
const said = [];
const commits = [];
const grow = () => {}; const growPairs = () => {}; const growField = () => {};
const drawWordCount = () => {}; const runNudges = () => {}; const drawAct = () => {};
const paintTurn = () => {}; const markKeyQuotes = () => {}; const footStuck = () => {};
const TEXT = 'The kite pulled at my wrists before I was ready, and the line sang in the wind, the whole hill went quiet';
const ROW = { key: 'Initial:7', i: 7, stop: true, pos: 2, runs: [{ text: TEXT }], pairs: [] };
const current = () => ROW;
const rowByKey = (key) => (key === ROW.key ? ROW : undefined);
const selectionInTurn = () => LIVE;
const selectionElsewhere = () => null;
const anyOverlayOpen = () => false;
const takeSelection = (add) => { if (!LIVE) return false; if (add) S.pending.push(LIVE); else S.pending = [LIVE]; return true; };
const clearPending = () => { S.pending = []; };
const keepNote = () => Promise.resolve(true);
const selBarHide = () => {};
const goTo = async () => {};
const say = (t) => { said.push(t); };
const undoPush = () => {};
const fakeEl = (tag, attrs) => ({ tag, attrs, value: '', placeholder: '', classList: { contains: () => false, toggle() {} },
  setAttribute(k, v) { this.attrs[k] = String(v); }, getAttribute(k) { return k in this.attrs ? this.attrs[k] : null; },
  focus() {} });
// the layout: the card's top at 100 lifted by --lift, each box 200 tall, 8 between, each later box dropped by --drop
const props = (o) => { o.vars = {}; o.style = { setProperty: (k, v) => { o.vars[k] = parseFloat(v); }, removeProperty: (k) => { delete o.vars[k]; } }; return o; };
const box = { list: [] };
function parse(html) {
  const starts = [...html.matchAll(/<div class="pair" data-pid="([^"]+)">/g)];
  return starts.map((m, i) => {
    const chunk = html.slice(m.index, i + 1 < starts.length ? starts[i + 1].index : html.length);
    const kids = {};
    for (const t of chunk.matchAll(/<(\w+)\b([^>]*)>/g)) {
      const attrs = {};
      for (const a of t[2].matchAll(/([\w-]+)="([^"]*)"/g)) attrs[a[1]] = a[2];
      for (const c of (attrs.class || '').split(/\s+/)) if (c && !kids['.' + c]) kids['.' + c] = fakeEl(t[1], attrs);
    }
    const pair = props({ dataset: { pid: m[1] }, querySelector: (sel) => kids[sel] || null,
      getBoundingClientRect() { return { top: topOf(box.list.indexOf(pair)) }; },
      // drawn on the page, as an IPA statement's box is (levelPairs passes over a pair drawn nowhere, taaibuild)
      getClientRects() { return [this.getBoundingClientRect()]; },
      remove() { const at = box.list.indexOf(pair); if (at >= 0) box.list.splice(at, 1); } });
    return pair;
  });
}
const card = props({ closest: (sel) => (sel === '.turn-es' ? cell : null) });
function topOf(k) {
  let top = 100 + (card.vars['--lift'] || 0);
  for (let j = 1; j <= k; j += 1) top += 200 + 8 + (box.list[j].vars['--drop'] || 0);
  return top;
}
Object.defineProperty(box, 'innerHTML', { set(h) { box.list = parse(h); } });
box.querySelectorAll = (sel) => (sel === '.pair' ? [...box.list] : []);
box.querySelector = (sel) => {
  const m = sel.match(/^\.pair\[data-pid="([^"]+)"\]$/);
  return m ? box.list.find((p) => p.dataset.pid === m[1]) || null : null;
};
box.insertAdjacentHTML = (where, h) => { if (where === 'beforeend') box.list.push(...parse(h)); };
// the passage's words beside the statements, and its quotes' marks, each at the top of its first line
let MARKS = [];
const words = { getBoundingClientRect: () => ({ left: 400, right: 900 }),
  querySelectorAll: () => MARKS.map(([kq, top]) => ({ dataset: { kq }, getClientRects: () => [{ top }] })) };
const holder = { querySelector: () => words, classList: { contains: () => false } };
const cell = { closest: () => holder, getClientRects: () => [1], getBoundingClientRect: () => ({ left: 40, right: 360 }),
  style: { removeProperty() {}, setProperty() {} } };
const work = { hidden: false };
const $ = (id) => (id === 'pairs' ? box : id === 'work' ? work : id === 'es-card' ? card : null);
const commit = async (row) => {
  row.pairs = pairsNow().map((p) => ({ ...p }));
  S.pending = [];
  commits.push(row.pairs.map((p) => [p.es, p.kq]));
};
"""
    pieces = [harness, quote_js, support.quote_span_js(),
              "const keyName = " + app.split("const keyName = ", 1)[1].split(";\n", 1)[0] + ";\n" + line(app, "const PAIR_QUOTE_HINT = "),
              line(app, "const GRAMM_OFF = "), line(app, "const pairEls = "), line(app, "const pairOf = "),
              line(app, "const pairsNow = "), line(app, "const pairEmpty = "), line(app, "const workingPlace = "),
              line(app, "const pendingQuote = "), line(app, "const CARD_REACH = "), line(app, "const REACH = ")] + [whole(app, n) for n in (
                  "rowPairs", "pairHtml", "pairsDrawn", "drawPairs", "insertPair", "workingPair", "pairsChanged",
                  "turnPlainText", "commitQuote", "pairTake", "levelPairs")]
    scenario = r"""
(async () => {
const kqs = () => box.list.map((p) => p.querySelector('.pair-kq').value);
const select = (w) => { const s = TEXT.indexOf(w); LIVE = { start: s, end: s + w.length, text: w }; S.pending = []; };
const tops = () => box.list.map((p) => p.getBoundingClientRect().top);
const out = {};

// two statements written first, no quotes: the arrow by the second takes the words as its quote, not the first's
drawPairs([{ es: 'Pulled before she was ready', kq: '' }, { es: 'The hill goes quiet', kq: '' }]);
select('the whole hill went quiet');
await pairTake(box.list[1]);
out.arrow = { kqs: kqs(), n: box.list.length, pending: S.pending.length };

// the same words by Q, the pair in hand being the second, make the same quote
const viaArrow = kqs()[1];
drawPairs([{ es: 'Pulled before she was ready', kq: '' }, { es: 'The hill goes quiet', kq: '' }]);
select('the whole hill went quiet');
S.pairFocus = box.list[1].dataset.pid;
await commitQuote();
out.sameAsQ = kqs()[1] === viaArrow;

// the arrow by a statement that has a quote never writes over it: the words go to a pair of their own, as Q's do
select('The kite pulled at my wrists');
await pairTake(box.list[1]);
out.over = { kqs: kqs(), n: box.list.length };

// with nothing selected the arrow does nothing and says so
LIVE = null; S.pending = [];
const before = kqs().join('|');
await pairTake(box.list[0]);
out.none = { same: kqs().join('|') === before, said: said[said.length - 1] };

// the save carries the arrow's quote to the workbook as Q's does
await commit(ROW);
out.saved = commits[commits.length - 1];

// the boxes: no quote set, a selection made, the first box stays at the passage's top
drawPairs([{ es: 'Pulled before she was ready', kq: '' }, { es: 'The hill goes quiet', kq: '' }]);
MARKS = [];
select('the whole hill went quiet');
levelPairs();
out.noQuote = tops();

// its quote set far down the passage, the box goes level with the quote's first line
MARKS = [['0', 520]];
levelPairs();
out.level = tops();

// a second quote close under the first: its box stacks under the first, never over it
MARKS = [['0', 520], ['1', 560]];
levelPairs();
out.stacked = tops();

// and a second quote further down: its box goes level with its own quote
MARKS = [['0', 520], ['1', 1100]];
levelPairs();
out.apart = tops();

// the statements stacked under the words (a phone's width): no box moves
const was = cell.getBoundingClientRect;
cell.getBoundingClientRect = () => ({ left: 400, right: 900 });
levelPairs();
out.under = tops();
cell.getBoundingClientRect = was;

console.log(JSON.stringify(out));
})().catch((e) => { console.log(JSON.stringify({ error: String(e && e.stack || e) })); });
"""
    js = scratch / "a241.js"
    js.write_text(support.i18n_js() + "\n".join(pieces) + "\n" + scenario, encoding="utf-8")
    run = subprocess.run([node, str(js)], capture_output=True, text=True, encoding="utf-8", timeout=60)
    try:
        out = json.loads(run.stdout.strip().splitlines()[-1])
    except (ValueError, IndexError):
        out = {"error": run.stdout + run.stderr}
    if out.get("error"):
        check("241: the node run", False, out["error"][:600])
        return
    quote = '"the whole hill went quiet"'
    check("241: the arrow by a statement takes the selected words as that statement's quote, verbatim, and the "
          "selection's pieces are let go", out["arrow"]["kqs"] == ["", quote] and out["arrow"]["n"] == 2
          and out["arrow"]["pending"] == 0, str(out["arrow"]))
    check("241: the arrow's quote is the one Q makes from the same words", out["sameAsQ"] is True, str(out))
    check("241: the arrow by a statement that has a quote never writes over it, the words going to a pair of their "
          "own under the last, as Q's do", out["over"]["n"] == 3 and out["over"]["kqs"][1] == quote
          and out["over"]["kqs"][2] == '"The kite pulled at my wrists"', str(out["over"]))
    check("241: with nothing selected the arrow changes nothing and says to select first",
          out["none"]["same"] is True and "Select" in (out["none"]["said"] or ""), str(out["none"]))
    check("241: the save carries the arrow's quote with its statement to the workbook, as Q's save does",
          out["saved"] == [["Pulled before she was ready", ""], ["The hill goes quiet", quote],
                           ["", '"The kite pulled at my wrists"']], str(out["saved"]))
    check("241: a statement with no quote set stays at the passage's top while words are only selected",
          out["noQuote"] == [100, 308], str(out["noQuote"]))
    check("241: once its quote is set the box goes level with the quote's first line",
          out["level"] == [520, 728], str(out["level"]))
    check("241: a second quote close under the first stacks its box under the first, in order, never over it",
          out["stacked"] == [520, 728], str(out["stacked"]))
    check("241: a second quote further down takes its box level with it", out["apart"] == [520, 1100], str(out["apart"]))
    check("241: with the statements stacked under the words no box moves", out["under"] == [100, 308], str(out["under"]))

    # typing never moves a box: the fields' keystrokes draw the counts and the marks, never the boxes' places
    body = app.split("$('pairs').addEventListener('input', (e) => {", 1)[1].split("\n  });", 1)[0]
    check("241: a keystroke in a statement or its quote never places the boxes again",
          "levelPairs" not in body and "levelSoon" not in body and "pairsDrawn" not in body, body[:300])
