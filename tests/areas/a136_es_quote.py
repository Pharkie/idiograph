from __future__ import annotations

import json
import shutil

from . import support
from .support import check, skip


def test_es_quote(scratch):
    print("\n136. q and the pair in hand, 14 October, and since 16 October one key for a key quote: q fills the key "
          "quote of the pair being worked on while it is empty and else adds a pair under the last, never writing over "
          "a quote, the line at the foot the same either way, Cmd + Z taking it back in one step and Cmd + Shift + Z "
          "putting it back, and nothing held past the depth of the stack, since q replaces none. Since the test review of "
          "18 October q's fill, add, undo and redo on the screen are area 153's and the save again area 152's, and q "
          "again from a new pair, a quote changed by clearing it and the stack's depth stay")
    import subprocess
    app = support.text("family/static/shell.js", "apps/idiograph/static/distil.js")
    quote_js = support.text("family/static/quote.js")
    fn = lambda src, name: src.split(f"function {name}(", 1)[1].split("\n}", 1)[0] if f"function {name}(" in src else ""
    whole = lambda src, name: ("async " if f"async function {name}(" in src else "") + f"function {name}(" + fn(src, name) + "\n}"
    line = lambda src, start: start + src.split(start, 1)[1].split("\n", 1)[0] if start in src else ""
    node = shutil.which("node")

    # ── B. in node: the real commitQuote, quotePut, statementPut, undoPush and undoStep over a stand-in for the pairs
    if not node:
        skip("136: q in node", "no node on this machine")
    else:
        harness = r"""
let MAC = true;
let pairSeq = 0;
const PROMPT_FALLBACK = 'A prompt';
const S = { prompt: '', pairFocus: null, dirty: false, pending: [], undoStack: [], redoStack: [],
  data: { path: 'hive.xlsx' }, undoBusy: false, note: null, quoting: false };
const escAttr = (s) => String(s).replace(/"/g, '&quot;');
const said = [];
const commits = [];
const grow = () => {}; const growPairs = () => {}; const growField = () => {};
const drawWordCount = () => {};
const runNudges = () => {};
const drawAct = () => {};
const paintTurn = () => {};
const markKeyQuotes = () => {};
const TEXT = 'The bees woke me before the alarm and I went out in my socks to hear them, the hum was the whole morning';
const ROW = { key: 'Initial:9', i: 9, stop: true, pos: 3, runs: [{ text: TEXT }], pairs: [] };
let NOW = ROW;
const current = () => NOW;
const rowByKey = (key) => (key === ROW.key ? ROW : undefined);
const selectionInTurn = () => null;
const selectionElsewhere = () => null;
const anyOverlayOpen = () => false;
const keepNote = () => {};
const selBarHide = () => {};
const takeSelection = () => false;
const clearPending = () => { S.pending = []; };
const goTo = async () => {};
const keepBeforeUndo = async () => true;
const say = (t) => { said.push(t); };
const fakeEl = (tag, attrs, text) => ({ tag, attrs, textContent: text, value: '', placeholder: '',
  setAttribute(k, v) { this.attrs[k] = String(v); }, getAttribute(k) { return k in this.attrs ? this.attrs[k] : null; },
  focus() {} });
const box = { list: [] };
function parse(html) {
  const starts = [...html.matchAll(/<div class="pair" data-pid="([^"]+)">/g)];
  return starts.map((m, i) => {
    const chunk = html.slice(m.index, i + 1 < starts.length ? starts[i + 1].index : html.length);
    const kids = {};
    for (const t of chunk.matchAll(/<(\w+)\b([^>]*)>([^<]*)/g)) {
      const attrs = {};
      for (const a of t[2].matchAll(/([\w-]+)="([^"]*)"/g)) attrs[a[1]] = a[2];
      const el = fakeEl(t[1], attrs, t[3]);
      for (const c of (attrs.class || '').split(/\s+/)) if (c && !kids['.' + c]) kids['.' + c] = el;
    }
    const pair = { dataset: { pid: m[1] }, chunk, querySelector: (sel) => kids[sel] || null,
      remove() { const at = box.list.indexOf(pair); if (at >= 0) box.list.splice(at, 1); },
      insertAdjacentHTML(where, h) { box.list.splice(box.list.indexOf(pair) + (where === 'beforebegin' ? 0 : 1), 0, ...parse(h)); } };
    return pair;
  });
}
Object.defineProperty(box, 'innerHTML', { set(h) { box.list = parse(h); } });
box.querySelectorAll = (sel) => (sel === '.pair' ? [...box.list] : []);
box.querySelector = (sel) => {
  const m = sel.match(/^\.pair\[data-pid="([^"]+)"\]$/);
  return m ? box.list.find((p) => p.dataset.pid === m[1]) || null : null;
};
box.insertAdjacentHTML = (where, h) => { if (where === 'beforeend') box.list.push(...parse(h)); };
const work = { hidden: false };
const $ = (id) => (id === 'pairs' ? box : id === 'work' ? work : null);
const commit = async (row) => {
  row.pairs = pairsNow().map((p) => ({ ...p }));
  S.pending = [];
  commits.push(row.pairs.map((p) => p.kq));
};
"""
        pieces = [harness, quote_js, support.quote_span_js(), "const keyName = " + app.split("const keyName = ", 1)[1].split(";\n", 1)[0] + ";\n" + line(app, "const PAIR_QUOTE_HINT = "), line(app, "const GRAMM_OFF = "),
                  line(app, "const UNDO_DEPTH = "), line(app, "const pairEls = "), line(app, "const pairOf = "),
                  line(app, "const pairsNow = "), line(app, "const pairEmpty = "), line(app, "const workingPlace = "),
                  line(app, "const pendingQuote = ")] + [whole(app, n) for n in (
                      "rowPairs", "pairHtml", "pairsDrawn", "drawPairs", "insertPair", "workingPair", "pairsChanged",
                      "turnPlainText", "quotePut", "commitQuote", "statementPut", "undoPush", "undoStep")]
        scenario = r"""
(async () => {
const kqs = () => box.list.map((p) => p.querySelector('.pair-kq').value);
const ess = () => box.list.map((p) => p.querySelector('.pair-es').value);
const pick = (words) => { const s = TEXT.indexOf(words); S.pending = [{ start: s, end: s + words.length }]; };
const on = (k) => { S.pairFocus = box.list[k].dataset.pid; };
const last = () => said[said.length - 1];
const top = () => S.undoStack[S.undoStack.length - 1];
const out = {};
drawPairs([{ es: 'Waking with the hive', kq: '' }, { es: 'The hum fills the morning', kq: '"the hum was the whole morning"' }]);
on(0); pick('The bees woke me before the alarm'); await commitQuote();
out.fill = { kqs: kqs(), ess: ess(), n: box.list.length, said: last(), undos: S.undoStack.length };
on(1); pick('I went out in my socks'); await commitQuote();
out.add = { kqs: kqs(), ess: ess(), n: box.list.length, said: last(), what: top().what };
pick('to hear them'); await commitQuote();
out.again = { kqs: kqs(), n: box.list.length, said: last(), undos: S.undoStack.length };
await undoStep(true);
out.undo1 = { kqs: kqs(), n: box.list.length, said: last(), pending: S.pending.length };
await undoStep(true);
out.undo2 = { kqs: kqs(), n: box.list.length, said: last() };
await undoStep(false);
out.redo1 = { kqs: kqs(), n: box.list.length, said: last() };
await undoStep(false);
out.redo2 = { kqs: kqs(), said: last(), redos: S.redoStack.length };
ROW.pairs = pairsNow().map((p) => ({ ...p }));
await undoStep(true);
out.saved = { kqs: kqs(), commits: commits.slice() };
await undoStep(false);
out.savedRedo = { kqs: kqs(), commits: commits.slice() };
// a quote is changed by clearing it, then q, which fills the field cleared
box.list[0].querySelector('.pair-kq').value = '';
on(0); pick('the hum was the whole morning'); await commitQuote();
out.cleared = { kqs: kqs(), n: box.list.length, said: last(), what: top().what };
const quotes = () => S.undoStack.filter((e) => e.what === 'the quote' || e.what === 'the new pair').length;
for (let k = 0; k < 70; k += 1) undoPush({ key: ROW.key, what: 'the pair', undo() {}, redo() {} });
out.depth = { len: S.undoStack.length, kept: quotes(), depth: UNDO_DEPTH };
NOW = { key: 'Initial:11' };
for (let k = 0; k < 70; k += 1) undoPush({ key: 'Initial:11', what: 'the pair', undo() {}, redo() {} });
out.away = { len: S.undoStack.length, kept: quotes() };
NOW = ROW;
S.undoStack.length = 0;
S.redoStack.length = 0;
drawPairs([{ es: 'Socks on the wet grass', kq: '(no quote)' }]);
on(0); pick('I went out in my socks'); await commitQuote();
out.noQuote = { said: last(), what: top().what, old: top().old, kqs: kqs() };
await undoStep(true);
out.noQuoteBack = { kqs: kqs(), said: last() };
console.log(JSON.stringify(out));
})().catch((err) => { console.error(String(err && err.stack || err)); process.exit(1); });
"""
        script = scratch / "es-quote-136.js"
        script.write_text(support.i18n_js() + "\n".join(pieces + [scenario]), encoding="utf-8")
        run = subprocess.run([node, str(script)], capture_output=True, text=True, encoding="utf-8")
        if run.returncode != 0:
            check("136: q runs in node", False, run.stderr.strip()[:300])
        else:
            out = json.loads(run.stdout)
            bees, socks, hear, hum = ('"The bees woke me before the alarm"', '"I went out in my socks"', '"to hear them"',
                                      '"the hum was the whole morning"')
            added = "Quote added, verbatim."
            check("136, 153: in node, q again from the new pair, which now holds a quote, adds another",
                  out["again"] == {"kqs": [bees, hum, socks, hear], "n": 4, "said": added, "undos": 3},
                  str(out["again"]))
            check("136, 153: in node, a quote cleared by hand and then q is the new quote in its place, which is how a "
                  "quote is changed since 16 October",
                  out["cleared"] == {"kqs": [hum, hum, socks, hear], "n": 4, "said": added, "what": "the quote"},
                  str(out["cleared"]))
            check("136, 153: in node, past the depth of the stack the oldest entries go, the quotes among them, nothing "
                  "held",
                  out["depth"] == {"len": 60, "kept": 0, "depth": 60}, str(out["depth"]))
            check("136: in node, on another turn the depth trims them from the oldest like any entry",
                  out["away"] == {"len": 60, "kept": 0}, str(out["away"]))
