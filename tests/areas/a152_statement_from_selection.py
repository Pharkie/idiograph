from __future__ import annotations

import json
import shutil
from pathlib import Path

from . import support
from .support import check, skip


def test_statement_from_selection(scratch):
    print("\n152. New statement from the selection, 16 October, Adam's agreement from a tester's feedback, and the same "
          "afternoon its work in q and Quote (153): words selected in the passage fill the key quote of the pair in hand "
          "while it is empty or of a pair added under the last, the caret in its statement, the quote put together "
          "once, one step of undo, and no pair from no selection, the s key, the New statement button and their line "
          "gone. Since the test review of 18 October what q does on the screen is area 153's, and the quote made verbatim, "
          "an empty pair in the middle filled and the workbook saved again on undo and redo stay")
    import subprocess
    read = lambda path: Path(path).read_text(encoding="utf-8")
    app, quote_js = support.text("family/static/shell.js", "apps/idiograph/static/distil.js"), support.text("family/static/quote.js")
    fn = lambda src, name: src.split(f"function {name}(", 1)[1].split("\n}", 1)[0] if f"function {name}(" in src else ""
    whole = lambda src, name: ("async " if f"async function {name}(" in src else "") + f"function {name}(" + fn(src, name) + "\n}"
    line = lambda src, start: start + src.split(start, 1)[1].split("\n", 1)[0] if start in src else ""
    node = shutil.which("node")

    # ── C. in node: the real functions over a stand-in for the pairs
    if not node:
        skip("152: the one key in node", "no node on this machine")
    else:
        harness = r"""
let MAC = true;
let pairSeq = 0;
let FOCUSED = null;
let LIVE = null;
let NOTES_KEPT = 0;
const PROMPT_FALLBACK = 'A prompt';
const S = { prompt: '', pairFocus: null, dirty: false, pending: [], undoStack: [], redoStack: [],
  data: { path: 'kite.xlsx' }, undoBusy: false, note: null, quoting: false };
const escAttr = (s) => String(s).replace(/"/g, '&quot;');
const said = [];
const commits = [];
const grow = () => {}; const growPairs = () => {}; const growField = () => {};
const drawWordCount = () => {};
const runNudges = () => {};
const drawAct = () => {};
const paintTurn = () => {};
const markKeyQuotes = () => {};
const TEXT = 'The kite pulled at my wrists before I was ready, and the line sang in the wind, the whole hill went quiet';
const ROW = { key: 'Initial:7', i: 7, stop: true, pos: 2, runs: [{ text: TEXT }], pairs: [] };
const current = () => ROW;
const rowByKey = (key) => (key === ROW.key ? ROW : undefined);
// a live selection in the passage, as selectionInTurn finds one, taken as a fresh piece
const selectionInTurn = () => LIVE;
const selectionElsewhere = () => null;
const anyOverlayOpen = () => false;
const takeSelection = (add) => { if (!LIVE) return false; if (add) S.pending.push(LIVE); else S.pending = [LIVE]; return true; };
const clearPending = () => { S.pending = []; };
const keepNote = () => { NOTES_KEPT += 1; S.note = null; return Promise.resolve(true); };
const selBarHide = () => {};
const goTo = async () => {};
const keepBeforeUndo = async () => true;
const say = (t) => { said.push(t); };
const fakeEl = (tag, attrs, text) => ({ tag, attrs, textContent: text, value: '', placeholder: '',
  setAttribute(k, v) { this.attrs[k] = String(v); }, getAttribute(k) { return k in this.attrs ? this.attrs[k] : null; },
  focus() { FOCUSED = this; } });
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
  commits.push(row.pairs.map((p) => [p.es, p.kq]));
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
const at = (words) => { const s = TEXT.indexOf(words); return { start: s, end: s + words.length }; };
const select = (words) => { LIVE = { ...at(words), text: words }; S.pending = []; };
const on = (k) => { S.pairFocus = box.list[k].dataset.pid; };
const caret = () => box.list.findIndex((p) => p.querySelector('.pair-es') === FOCUSED);
const last = () => said[said.length - 1];
const top = () => S.undoStack[S.undoStack.length - 1];
const fresh = (list) => { S.undoStack.length = 0; S.redoStack.length = 0; FOCUSED = null; LIVE = null; S.pending = []; drawPairs(list); };
const out = {};

// an empty passage: the selection fills the one empty pair's key quote, and the caret goes to its statement
fresh([]);
on(0); select('the line sang in the wind'); await commitQuote();
out.fill = { kqs: kqs(), ess: ess(), n: box.list.length, caret: caret(), focus: S.pairFocus === box.list[0].dataset.pid,
  said: last(), undos: S.undoStack.length, what: top().what, pending: S.pending.length };
await undoStep(true);
out.fillUndo = { kqs: kqs(), n: box.list.length, said: last(), pending: S.pending.length };
await undoStep(false);
out.fillRedo = { kqs: kqs(), n: box.list.length, said: last() };

// the pair in hand now holds a quote, so the next selection makes a pair of its own under the last
LIVE = null; select('The kite pulled at my wrists'); await commitQuote();
out.add = { kqs: kqs(), ess: ess(), n: box.list.length, caret: caret(), focus: S.pairFocus === box.list[1].dataset.pid,
  said: last(), undos: S.undoStack.length, what: top().what };
await undoStep(true);
out.addUndo = { kqs: kqs(), n: box.list.length, said: last(), pending: S.pending.length };
await undoStep(false);
out.addRedo = { kqs: kqs(), ess: ess(), n: box.list.length, said: last() };

// a statement written in the new pair since stays through an undo, and only its quote goes
box.list[1].querySelector('.pair-es').value = 'Pulled before she was ready';
await undoStep(true);
out.typedUndo = { kqs: kqs(), ess: ess(), n: box.list.length, said: last() };
await undoStep(false);
out.typedRedo = { kqs: kqs(), ess: ess(), n: box.list.length, said: last() };

// the quote q makes is the one assembleQuote makes, the pieces held with Cmd among them
const two = [at('The kite pulled'), at('the whole hill went quiet')];
fresh([]);
on(0); S.pending = two.map((p) => ({ ...p })); await commitQuote();
const byQ = kqs()[0];
fresh([]);
on(0); select('and the line sang'); await commitQuote();
out.same = { byQ, assembled: assembleQuote(two, TEXT), one: kqs()[0] };

// a pair in hand with its statement and no quote takes the quote, no pair added, since 16 October, later
fresh([{ es: 'Holding on in the wind', kq: '' }]);
on(0); select('the line sang in the wind'); await commitQuote();
out.withStatement = { kqs: kqs(), ess: ess(), n: box.list.length, caret: caret() };

// "(no quote)" holds no quote, so the pair is filled, and undo puts it back as it read
fresh([{ es: '', kq: '(no quote)' }]);
on(0); select('the whole hill went quiet'); await commitQuote();
out.noQuote = { kqs: kqs(), n: box.list.length };
await undoStep(true);
out.noQuoteBack = { kqs: kqs(), n: box.list.length };

// the pair in hand in the middle is filled where it stands, and from a full pair the new one goes last
fresh([{ es: 'Before she was ready', kq: '"The kite pulled at my wrists"' }, { es: '', kq: '' }, { es: 'The hill', kq: '' }]);
on(1); select('the line sang in the wind'); await commitQuote();
out.middle = { kqs: kqs(), n: box.list.length, caret: caret() };
on(0); select('the whole hill went quiet'); await commitQuote();
out.under = { kqs: kqs(), n: box.list.length, caret: caret(), place: top().place };
await undoStep(true);
out.underUndo = { kqs: kqs(), n: box.list.length };

// no selection in the passage: the line, and no pair, no entry
fresh([{ es: 'Holding on in the wind', kq: '' }]);
on(0); await commitQuote();
out.none = { n: box.list.length, kqs: kqs(), said: last(), undos: S.undoStack.length, caret: caret() };

// a passage already saved with the new pair is saved again on undo without it, and on redo with it
fresh([{ es: 'Holding on in the wind', kq: '"the line sang in the wind"' }]);
on(0); select('the whole hill went quiet'); await commitQuote();
ROW.pairs = pairsNow().map((p) => ({ ...p }));
commits.length = 0;
await undoStep(true);
out.saved = { n: box.list.length, commits: commits.slice() };
await undoStep(false);
out.savedRedo = { n: box.list.length, commits: commits.slice() };

// an interviewer note open is kept first, so the pairs are back to write in
fresh([]);
S.note = { key: 'Initial:6' };
on(0); select('the whole hill went quiet'); await commitQuote();
out.note = { kept: NOTES_KEPT, open: S.note, kqs: kqs() };

out.target = [quoteTarget([{ es: '', kq: '' }], 0), quoteTarget([{ es: 'A', kq: '' }], 0),
  quoteTarget([{ es: '', kq: '"x"' }, { es: '', kq: '' }], 0), quoteTarget([{ es: '', kq: '' }, { es: 'B', kq: '' }], 7),
  quoteTarget([], 0)];
console.log(JSON.stringify(out));
})().catch((err) => { console.error(String(err && err.stack || err)); process.exit(1); });
"""
        script = scratch / "statement-from-selection-152.js"
        script.write_text(support.i18n_js() + "\n".join(pieces + [scenario]), encoding="utf-8")
        run = subprocess.run([node, str(script)], capture_output=True, text=True, encoding="utf-8")
        if run.returncode != 0:
            check("152: the one key runs in node", False, run.stderr.strip()[:300])
        else:
            out = json.loads(run.stdout)
            sang, kite, quiet = '"the line sang in the wind"', '"The kite pulled at my wrists"', '"the whole hill went quiet"'
            check("152, 153: in node, the quote q makes is exactly the one assembleQuote makes, pieces joined by an "
                  "ellipsis in transcript order",
                  out["same"]["byQ"] == out["same"]["assembled"] == '"The kite pulled … the whole hill went quiet"'
                  and out["same"]["one"] == '"and the line sang"', str(out["same"]))
            check("152: in node, an empty pair in hand in the middle is filled where it stands, and from a full pair the "
                  "new one goes under the last, as Add another puts it, and goes again on Cmd + Z",
                  out["middle"] == {"kqs": [kite, sang, ""], "n": 3, "caret": 1}
                  and out["under"] == {"kqs": [kite, sang, "", quiet], "n": 4, "caret": 3, "place": 3}
                  and out["underUndo"] == {"kqs": [kite, sang, ""], "n": 3},
                  str([out["middle"], out["under"], out["underUndo"]]))
            check("152: in node, a passage saved with the new pair is saved again on Cmd + Z without it and on Cmd + Shift "
                  "+ Z with it, so the workbook ends where the fields do",
                  out["saved"] == {"n": 1, "commits": [[["Holding on in the wind", sang]]]}
                  and out["savedRedo"] == {"n": 2, "commits": [[["Holding on in the wind", sang]],
                                                               [["Holding on in the wind", sang], ["", quiet]]]},
                  str([out["saved"], out["savedRedo"]]))
