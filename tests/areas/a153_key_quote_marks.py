from __future__ import annotations

import json
import re
import shutil
from pathlib import Path

import openpyxl

import workbook as wb_mod

from . import support
from .support import DEMO_SHEET, DEMO_WORKBOOK, check, skip


def test_key_quote_marks(scratch):
    print("\n153. Key quotes as the marks in the text, 16 October, Adam's decisions on a tester's feedback: Highlight "
          "gone and the highlights in a workbook kept and never drawn, every key quote marked piece by piece in its "
          "passage and linked to its statement both ways, a done bar on every passage decided, one key q that fills "
          "an empty key quote or adds a pair, from another passage too, the note kept first, the rounds line and "
          "the morning's views fixes. Since the test review of 18 October the card's foot, the marks' and bars' styles, "
          "the tooltips and the words are review shots, and q, the marks' places and links, the done levels and the "
          "highlight kept byte for byte stay")
    import subprocess
    import zipfile
    read = lambda path: Path(path).read_text(encoding="utf-8")
    app, quote_js = support.text("family/static/shell.js", "apps/idiograph/static/distil.js"), support.text("family/static/quote.js")
    fn = lambda src, name: src.split(f"function {name}(", 1)[1].split("\n}", 1)[0] if f"function {name}(" in src else ""
    whole = lambda src, name: ("async " if f"async function {name}(" in src else "") + f"function {name}(" + fn(src, name) + "\n}"
    line = lambda src, start: start + src.split(start, 1)[1].split("\n", 1)[0] if start in src else ""
    node = shutil.which("node")

    # ── A. Highlight gone: no key but q for a key quote
    keydown = support.keydown_text(app)
    letters = re.findall(r"else if \((?:e\.)?key === '([a-z])'", keydown)
    check("153: neither h nor s does anything on the statements screen now, and q is the one key for a key quote",
          "h" not in letters and "s" not in letters and letters.count("q") == 1
          and "    else if (key === 'q' && !$('work').hidden) { e.preventDefault(); commitQuote(); }" in keydown
          and "$('sel-quote').onclick = () => commitQuote();" in app and "$('btn-quote')" not in app
          and "markCrux" not in app and "statementFromSelection" not in app, str(letters))

    # ── B. a workbook's highlight survives a save byte for byte in its rich text
    book = scratch / "key-quote-marks-153" / "book.xlsx"
    book.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(DEMO_WORKBOOK, book)

    def items(path):
        with zipfile.ZipFile(path) as z:
            xml = z.read("xl/sharedStrings.xml").decode("utf-8")
        return re.findall(r"<si>.*?</si>", xml, flags=re.S)

    wb = openpyxl.load_workbook(book, rich_text=True)
    ws = wb[DEMO_SHEET]
    cols = wb_mod.detect_columns(ws)
    lit = []
    for r in range(2, ws.max_row + 1):
        runs = wb_mod.cell_runs(ws.cell(r, cols["transcript"]).value)
        if any(x["crux"] for x in runs):
            lit.append((r, runs))
    wb.close()
    if not lit:
        check("153: the demo workbook carries a highlight to keep", False)
    else:
        row, runs = lit[0]
        phrase = next(x["text"] for x in runs if x["crux"])
        probe = phrase[:12]
        before = [s for s in items(book) if probe in s and "<r>" in s]
        made = wb_mod.save_turn(book, DEMO_SHEET, row, None, "A note on the hum", None,
                                pairs=[{"es": "Waking to the bees", "kq": f'"{phrase}"'}])
        after = [s for s in items(book) if probe in s and "<r>" in s]
        wb = openpyxl.load_workbook(book, rich_text=True)
        again = wb_mod.cell_runs(wb[DEMO_SHEET].cell(row, cols["transcript"]).value)
        wb.close()
        check("153: a save of the statements on a passage with a highlight writes its pairs and leaves the highlight's "
              "rich text byte for byte as it was",
              made["changed"] and len(before) == 1 and before == after and again == runs, f"{len(before)} {len(after)}")

    # ── C. in node: where a key quote stands, the marks drawn, the links both ways
    if not node:
        skip("153: the key quote marks in node", "no node on this machine")
    else:
        marks = r"""
const S = { pairsRow: null, kqHover: null, kqFocus: null, at: 0, editing: null, timeEdit: null, note: null, pairFocus: null };
const FOCUSED = [];
const NOTES_KEPT = [];
const GONE = [];
const fakePair = (pid) => ({ dataset: { pid }, querySelector: (sel) => (sel === '.pair-es' ? { focus() { FOCUSED.push(pid); } } : null) });
let PAIRS = [fakePair('p1'), fakePair('p2'), fakePair('p3')];
const pairEls = () => PAIRS;
const pairsNow = () => LIVE;
let LIVE = [];
const keepNote = () => { NOTES_KEPT.push(1); S.note = null; };
const pairIntoView = () => {};
const goTo = (k) => { GONE.push(k); S.at = k; return Promise.resolve(); };
const current = () => ({ key: 'Initial:' + S.at });
const BOX = { marks: [] };
const $ = (id) => (id === 'turn-text' ? { querySelectorAll: () => BOX.marks } : null);
const fakeMark = (kq) => ({ dataset: { kq }, cls: new Set(), classList: { toggle(c, on) { if (on) this.owner.cls.add(c); else this.owner.cls.delete(c); } } });
"""
        pieces = [marks, quote_js, support.quote_span_js(), line(app, "const esc = "), line(app, "const escAttr = ")] + [
            whole(app, n) for n in ("rowPairs", "livePairs", "kqLayer", "kqTitle", "markedHtml", "lightMarks",
                                    "toStatement", "doneLevels")] + [
            "const DONE_LEVEL = " + app.split("const DONE_LEVEL = ", 1)[1].split("\n", 1)[0] if "const DONE_LEVEL = " in app else ""]
        scenario = r"""
(async () => {
const T = 'The bees woke me before the alarm, and I went out in my socks to hear them.\n  The hum was the whole morning, it’s mine.';
const out = {};
const cut = (spans) => spans.map((s) => T.slice(s.start, s.end));
out.pieces = cut(quoteSpans('"The bees woke me … the whole morning"', T));
out.curly = cut(quoteSpans('“to hear them. The hum”', T));
out.apostrophe = cut(quoteSpans('"it\'s mine"', T));
out.dots = cut(quoteSpans('"I went out ... to hear them"', T));
out.single = cut(quoteSpans('‘the alarm’', T));
out.gone = quoteSpans('"the bees woke me after the alarm"', T);
out.order = quoteSpans('"the whole morning … The bees"', T);
out.noQuote = quoteSpans('(no quote)', T);
out.empty = quoteSpans('', T);

// the marks, each pair's by place, a piece of a quote put together marked on its own, and two pairs on the
// same words naming both
const ROW = { key: 'Initial:4', stop: true, runs: [{ text: T.slice(0, 33), crux: true }, { text: T.slice(33) }],
  pairs: [{ es: 'Woken early', kq: '"The bees woke me … the whole morning"' }, { es: 'Out in socks', kq: '"I went out in my socks"' },
    { es: 'Socks again', kq: '"in my socks"' }, { es: 'Gone', kq: '"a phrase that is not there"' }] };
const layer = kqLayer(ROW);
out.layer = layer.map((s) => [T.slice(s.start, s.end), s.kq, s.cls]);
const html = markedHtml(ROW.runs, layer);
out.spans = [...html.matchAll(/<span class="([^"]+)"( data-kq="([^"]*)"(?: data-es-colour(?:-b)?="\d")* title="([^"]*)")?>([^<]*)<\/span>/g)].map((m) => [m[1], m[3] || '', m[4] || '', m[5]]);
out.crux = html.includes('crux');
// the passage being worked on is marked from the fields as they stand
LIVE = [{ es: '', kq: '"to hear them"' }];
S.pairsRow = 'Initial:4';
out.live = kqLayer(ROW).map((s) => [T.slice(s.start, s.end), s.kq]);
S.pairsRow = null;
out.saved = kqLayer(ROW).length;
out.aside = kqLayer({ key: 'Initial:5', stop: false, runs: [{ text: T }], pairs: [{ es: 'x', kq: '"The bees"' }] }).length;
out.title = [kqTitle([1]), kqTitle([0, 2]), kqTitle([0, 1, 3])];

// a key quote under the pointer or holding the caret lights its marks, the pointer's first
BOX.marks = ['0', '1', '1 2', '2'].map((k) => { const m = fakeMark(k); m.classList.owner = m; return m; });
const lit = () => BOX.marks.map((m) => (m.cls.has('lit') ? 1 : 0)).join('');
S.kqFocus = 'p2'; lightMarks(); out.focusLit = lit();
S.kqHover = 'p3'; lightMarks(); out.hoverLit = lit();
S.kqHover = null; S.kqFocus = null; lightMarks(); out.noneLit = lit();

// a click on a mark brings its statement forward: here at once, elsewhere after the move, a note kept first
S.at = 3;
await toStatement({ pos: 3, key: 'Initial:3' }, 1);
out.here = { focused: FOCUSED.slice(), gone: GONE.slice(), pairFocus: S.pairFocus };
FOCUSED.length = 0;
S.note = { key: 'Initial:2' };
await toStatement({ pos: 5, key: 'Initial:5' }, 2);
out.there = { focused: FOCUSED.slice(), gone: GONE.slice(), notes: NOTES_KEPT.length, note: S.note, pairFocus: S.pairFocus };

// the done levels: a passage with a statement 2, one skipped 1, undecided or passed 0 (16 October), and the
// interviewer's between two of hers at the fainter of the two
const rows = [
  { i: 0, stop: false }, { i: 1, stop: true, key: 'a' }, { i: 2, stop: false }, { i: 3, stop: false },
  { i: 4, stop: true, key: 'b' }, { i: 5, stop: false }, { i: 6, stop: true, key: 'c' }, { i: 7, stop: false },
  { i: 8, stop: true, key: 'd' }, { i: 9, stop: false }, { i: 10, stop: true, key: 'e' }, { i: 11, stop: false },
  { i: 12, stop: true, key: 'f' }, { i: 13, stop: false }];
const states = { a: 'has-content', b: 'has-content', c: 'reviewed-empty', d: 'unvisited', e: 'passed', f: 'has-content' };
const levels = doneLevels(rows, states);
out.levels = rows.map((r) => levels.get(r.i)).join('');
console.log(JSON.stringify(out));
})().catch((err) => { console.error(String(err && err.stack || err)); process.exit(1); });
"""
        script = scratch / "key-quote-marks-153.js"
        script.write_text(support.i18n_js() + "\n".join(pieces + [scenario]), encoding="utf-8")
        run = subprocess.run([node, str(script)], capture_output=True, text=True, encoding="utf-8")
        if run.returncode != 0:
            check("153: the key quote marks run in node", False, run.stderr.strip()[:300])
        else:
            out = json.loads(run.stdout)
            check("153: in node, a quote put together with an ellipsis is found piece by piece in order, curly and "
                  "straight inverted commas and apostrophes matching, case and runs of spaces set aside, three dots as "
                  "an ellipsis and single inverted commas round a quote set aside too",
                  out["pieces"] == ["The bees woke me", "the whole morning"]
                  and out["curly"] == ["to hear them.\n  The hum"] and out["apostrophe"] == ["it’s mine"]
                  and out["dots"] == ["I went out", "to hear them"] and out["single"] == ["the alarm"],
                  str([out["pieces"], out["curly"], out["apostrophe"], out["dots"], out["single"]]))
            check("153: in node, a quote the passage no longer holds finds nothing at all, nor do pieces out of order, "
                  "\"(no quote)\" or an empty quote",
                  out["gone"] == [] and out["order"] == [] and out["noQuote"] == [] and out["empty"] == [],
                  str([out["gone"], out["order"]]))
            check("153: in node, every pair's key quote is laid over its passage by place, each piece of a quote put "
                  "together on its own, and a quote that no longer matches lays nothing",
                  out["layer"] == [["The bees woke me", 0, "kq"], ["the whole morning", 0, "kq"],
                                   ["I went out in my socks", 1, "kq"], ["in my socks", 2, "kq"]], str(out["layer"]))
            spans = out["spans"]
            check("153: in node, the marks carry the places of their pairs and a tooltip naming the statement, both where "
                  "two pairs hold the same words, and no highlight class whatever the runs say",
                  ["kq", "0", "Experiential statement 1", "The bees woke me"] in spans
                  and ["kq", "0", "Experiential statement 1", "the whole morning"] in spans
                  and ["kq", "1", "Experiential statement 2", "I went out "] in spans and len(spans) == 4
                  and ["kq", "1 2", "Experiential statements 2 and 3", "in my socks"] in spans
                  and not out["crux"], str(spans))
            check("153: in node, the passage being worked on is marked from the fields as they stand, every other one "
                  "from its pairs as saved, and an interviewer's passage takes none",
                  out["live"] == [["to hear them", 0]] and out["saved"] == 4 and out["aside"] == 0,
                  str([out["live"], out["saved"], out["aside"]]))
            check("153: in node, a click on a mark in the passage being worked on puts the caret in its pair's statement "
                  "with no move, and in another passage moves there first, an open note kept",
                  out["here"] == {"focused": ["p2"], "gone": [], "pairFocus": "p2"}
                  and out["there"] == {"focused": ["p3"], "gone": [5], "notes": 1, "note": None, "pairFocus": "p3"},
                  str([out["here"], out["there"]]))
            check("153, 156: in node, the done levels: 2 for a statement, 1 for one he skipped, 0 undecided and 0 for "
                  "one only passed since 16 October, and the interviewer's passages between two of hers at the fainter "
                  "of the two, none before the first or after the last",
                  out["levels"] == "02222110000020", out["levels"])

    # ── D. a click on a key quote's mark
    click = app.split("$('transcript').addEventListener('click', (e) => {", 1)[1].split("\n  });", 1)[0]
    check("153: a plain click on a key quote's mark goes to toStatement with its first pair, the second click of a "
          "double-click left to the editor",
          "const quoted = e.detail >= 2 ? null : e.target.closest('.turn-text .kq');" in click
          and "if (quoted && row.stop && quoted.dataset.kq !== undefined) { toStatement(row, Number(String(quoted.dataset.kq).split(' ')[0])); return; }"
          in click and click.index("if (pressMoved(e) || selectionLive()) return;") < click.index("const quoted")
          # and a piece of the quote of her passage next to this one goes to that passage's statement (quotespan)
          and "if (S.flat[i] && S.flat[i].stop) { toStatement(S.flat[i], n); return; }" in click)

    # ── E. in node: one key q
    if not node:
        skip("153: q in node", "no node on this machine")
    else:
        harness = r"""
let MAC = true;
let pairSeq = 0;
let FOCUSED = null;
let LIVE = null;
let ELSEWHERE = null;
let OVERLAY = false;
let NOTES_KEPT = 0;
const GONE = [];
const PROMPT_FALLBACK = 'A prompt';
const S = { prompt: '', pairFocus: null, dirty: false, pending: [], undoStack: [], redoStack: [],
  data: { path: 'hive.xlsx' }, undoBusy: false, note: null, quoting: false, pairsRow: null, at: 0 };
const escAttr = (s) => String(s).replace(/"/g, '&quot;');
const said = [];
const commits = [];
const grow = () => {}; const growPairs = () => {}; const growField = () => {};
const drawWordCount = () => {};
const runNudges = () => {};
const drawAct = () => {};
const paintTurn = () => {};
const markKeyQuotes = () => {};
const TEXT = 'The bees woke me before the alarm, and I went out in my socks to hear them, the hum was the whole morning';
const NEXT = 'I sat on the step with a cup going cold and watched them go out one by one';
const ROWS = [{ key: 'Initial:3', i: 3, stop: true, pos: 0, runs: [{ text: TEXT }], pairs: [] },
  { key: 'Initial:5', i: 5, stop: true, pos: 1, runs: [{ text: NEXT }], pairs: [{ es: 'Watching them leave', kq: '' }] }];
const current = () => ROWS[S.at];
const rowByKey = (key) => ROWS.find((r) => r.key === key);
const selectionInTurn = () => LIVE;
const selectionElsewhere = () => ELSEWHERE;
const takeSelection = (add) => { if (!LIVE) return false; if (add) S.pending.push(LIVE); else S.pending = [LIVE]; return true; };
const clearPending = () => { S.pending = []; };
const anyOverlayOpen = () => OVERLAY;
const keepNote = () => { NOTES_KEPT += 1; S.note = null; return Promise.resolve(true); };
const selBarHide = () => {};
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
// a move as goTo makes one: the fields saved on the way, the next passage's pairs drawn, the pieces cleared
const goTo = async (k) => {
  GONE.push(k);
  if (S.dirty) { await commit(current()); S.dirty = false; }
  S.at = k;
  S.pending = [];
  S.pairFocus = null;
  drawPairs(rowPairs(current()));
  S.pairsRow = current().key;
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
const at = (text, words) => { const s = text.indexOf(words); return { start: s, end: s + words.length }; };
const select = (words) => { LIVE = { ...at(TEXT, words), text: words }; ELSEWHERE = null; S.pending = []; };
const on = (k) => { S.pairFocus = box.list[k].dataset.pid; };
const caret = () => box.list.findIndex((p) => p.querySelector('.pair-es') === FOCUSED);
const last = () => said[said.length - 1];
const top = () => S.undoStack[S.undoStack.length - 1];
const fresh = (list) => { S.at = 0; S.undoStack.length = 0; S.redoStack.length = 0; FOCUSED = null; LIVE = null;
  ELSEWHERE = null; S.pending = []; S.note = null; GONE.length = 0; S.dirty = false; drawPairs(list); S.pairsRow = ROWS[0].key; };
const out = {};

// the pair in hand has a statement and no key quote: the selection fills its key quote, no pair added
fresh([{ es: 'Woken before the alarm', kq: '' }]);
on(0); select('The bees woke me'); await commitQuote();
out.fill = { kqs: kqs(), ess: ess(), n: box.list.length, caret: caret(), said: last(), undos: S.undoStack.length,
  what: top().what, old: top().old };
// now it has one, so the next selection makes a pair of its own under the last, the caret in its statement
LIVE = null; select('I went out in my socks'); await commitQuote();
out.add = { kqs: kqs(), ess: ess(), n: box.list.length, caret: caret(), said: last(), undos: S.undoStack.length,
  what: top().what, place: top().place };
// a statement written in the new pair since stays through Cmd + Z, its key quote emptied, in one step
box.list[1].querySelector('.pair-es').value = 'Out in socks to listen';
await undoStep(true);
out.addUndo = { kqs: kqs(), ess: ess(), n: box.list.length, said: last(), pending: S.pending.length };
await undoStep(false);
out.addRedo = { kqs: kqs(), ess: ess(), n: box.list.length };
// and the fill goes back in one step to the empty key quote, its statement as it was
await undoStep(true);
await undoStep(true);
out.fillUndo = { kqs: kqs(), ess: ess(), n: box.list.length };

// "(no quote)" holds no quote, so q fills it, and Cmd + Z puts it back as it read
fresh([{ es: 'The hum', kq: '(no quote)' }]);
on(0); select('the hum was the whole morning'); await commitQuote();
out.noQuote = { kqs: kqs(), n: box.list.length };
await undoStep(true);
out.noQuoteBack = kqs();

// a quote is changed by clearing it first: q never writes over one, the old quote stays where it is
fresh([{ es: 'Woken', kq: '"The bees woke me"' }]);
on(0); select('before the alarm'); await commitQuote();
out.never = { kqs: kqs(), n: box.list.length, caret: caret() };

// nothing selected anywhere: the line, no pair, no entry
fresh([{ es: 'Woken', kq: '' }]);
on(0); await commitQuote();
out.none = { kqs: kqs(), n: box.list.length, said: last(), undos: S.undoStack.length };

// words selected in another of her passages: the move goes there first, the passage left saved on the way,
// then the words fill that passage's empty key quote with the caret in its statement
fresh([{ es: 'Woken', kq: '"The bees woke me"' }]);
S.dirty = true;
ELSEWHERE = { row: ROWS[1], ...at(NEXT, 'a cup going cold'), text: 'a cup going cold' };
commits.length = 0;
await commitQuote();
out.elsewhere = { at: S.at, gone: GONE.slice(), kqs: kqs(), ess: ess(), caret: caret(), key: top().key,
  saved: commits.slice(), said: last() };
await undoStep(true);
out.elsewhereUndo = { at: S.at, kqs: kqs() };

// a card the move raised stands in front, so the words wait as the candidate and nothing is written
ROWS[1].pairs = [{ es: 'Watching them leave', kq: '' }];
fresh([{ es: 'Woken', kq: '' }]);
OVERLAY = true;
ELSEWHERE = { row: ROWS[1], ...at(NEXT, 'one by one'), text: 'one by one' };
await commitQuote();
out.card = { at: S.at, kqs: kqs(), pending: S.pending.length, undos: S.undoStack.length };
OVERLAY = false;

// an interviewer note open is kept first, as the button keeps it, and the pair in hand takes the quote
fresh([{ es: '', kq: '' }]);
S.note = { key: 'Initial:2' };
on(0); select('to hear them'); await commitQuote();
out.note = { kept: NOTES_KEPT, open: S.note, kqs: kqs(), caret: caret() };
// a selection in an interviewer passage is no selection for q, as it always was: the line, and the note stays
NOTES_KEPT = 0;
fresh([{ es: '', kq: '' }]);
S.note = { key: 'Initial:2' };
await commitQuote();
out.noteStays = { kept: NOTES_KEPT, open: !!S.note, kqs: kqs(), said: last() };

out.target = [quoteTarget([{ es: '', kq: '' }], 0), quoteTarget([{ es: 'A', kq: '' }], 0),
  quoteTarget([{ es: 'A', kq: '"x"' }, { es: '', kq: '' }], 0), quoteTarget([{ es: '', kq: '' }, { es: 'B', kq: '"y"' }], 7),
  quoteTarget([{ es: 'C', kq: '(no quote)' }], 0), quoteTarget([], 0)];
console.log(JSON.stringify(out));
})().catch((err) => { console.error(String(err && err.stack || err)); process.exit(1); });
"""
        script = scratch / "key-quote-q-153.js"
        script.write_text(support.i18n_js() + "\n".join(pieces + [scenario]), encoding="utf-8")
        run = subprocess.run([node, str(script)], capture_output=True, text=True, encoding="utf-8")
        if run.returncode != 0:
            check("153: q runs in node", False, run.stderr.strip()[:300])
        else:
            out = json.loads(run.stdout)
            woke, socks, hum = '"The bees woke me"', '"I went out in my socks"', '"the hum was the whole morning"'
            added = "Quote added, verbatim."
            check("153: in node, q fills the empty key quote of the pair in hand though it has a statement, adds no pair, "
                  "puts the caret in its statement and pushes one entry",
                  out["fill"] == {"kqs": [woke], "ess": ["Woken before the alarm"], "n": 1, "caret": 0, "said": added,
                                  "undos": 1, "what": "the quote", "old": ""}, str(out["fill"]))
            check("153: in node, q on a pair that holds a quote adds a pair under the last with the selection as its key "
                  "quote, the caret in the new statement, one more entry",
                  out["add"] == {"kqs": [woke, socks], "ess": ["Woken before the alarm", ""], "n": 2, "caret": 1,
                                 "said": added, "undos": 2, "what": "the new pair", "place": 1}, str(out["add"]))
            typed = "Out in socks to listen"
            check("153: in node, Cmd + Z takes q back in one step and keeps a statement typed since, and Cmd + Shift + Z "
                  "puts the quote back beside it",
                  out["addUndo"] == {"kqs": [woke, ""], "ess": ["Woken before the alarm", typed], "n": 2,
                                     "said": "The quote is out, and the pieces are still selected.", "pending": 1}
                  and out["addRedo"] == {"kqs": [woke, socks], "ess": ["Woken before the alarm", typed], "n": 2},
                  str([out["addUndo"], out["addRedo"]]))
            check("153: in node, the fill undone leaves the key quote empty and the statement as it was",
                  out["fillUndo"] == {"kqs": ["", ""], "ess": ["Woken before the alarm", typed], "n": 2},
                  str(out["fillUndo"]))
            check("153: in node, \"(no quote)\" is no quote, so q fills it, and Cmd + Z puts it back as it read",
                  out["noQuote"] == {"kqs": [hum], "n": 1} and out["noQuoteBack"] == ["(no quote)"],
                  str([out["noQuote"], out["noQuoteBack"]]))
            check("153: in node, q never writes over a quote, a new pair takes the words",
                  out["never"] == {"kqs": [woke, '"before the alarm"'], "n": 2, "caret": 1}, str(out["never"]))
            check("153: in node, with nothing selected q says to select first and makes no pair and no entry",
                  out["none"] == {"kqs": [""], "n": 1, "said": "Select the words inside the passage first, then press Q.",
                                  "undos": 0}, str(out["none"]))
            check("153: in node, words selected in another of her passages move there first, the passage left saved on "
                  "the way, and fill that passage's empty key quote, the caret in its statement, the entry its own",
                  out["elsewhere"] == {"at": 1, "gone": [1], "kqs": ['"a cup going cold"'], "ess": ["Watching them leave"],
                                       "caret": 0, "key": "Initial:5", "saved": [[["Woken", woke]]], "said": added}
                  and out["elsewhereUndo"] == {"at": 1, "kqs": [""]}, str([out["elsewhere"], out["elsewhereUndo"]]))
            check("153: in node, a card the move raised leaves the words as the candidate and writes nothing",
                  out["card"] == {"at": 1, "kqs": [""], "pending": 1, "undos": 0}, str(out["card"]))
            check("153: in node, q with an interviewer note open keeps the note first and fills the pair in hand, where "
                  "until 16 October the key filled the hidden pair with the note still open",
                  out["note"] == {"kept": 1, "open": None, "kqs": ['"to hear them"'], "caret": 0}, str(out["note"]))
            check("153: in node, a selection in an interviewer passage, no selection for q, leaves the note open and says "
                  "the line",
                  out["noteStays"] == {"kept": 0, "open": True, "kqs": [""],
                                       "said": "Select the words inside the passage first, then press Q."},
                  str(out["noteStays"]))
            check("153: in node, quoteTarget fills the empty key quote in hand whatever its statement, \"(no quote)\" "
                  "empty, and else names the place under the last",
                  out["target"] == [{"place": 0, "added": False, "old": ""}, {"place": 0, "added": False, "old": ""},
                                    {"place": 2, "added": True, "old": ""}, {"place": 2, "added": True, "old": ""},
                                    {"place": 0, "added": False, "old": "(no quote)"},
                                    {"place": 0, "added": True, "old": ""}], str(out["target"]))
