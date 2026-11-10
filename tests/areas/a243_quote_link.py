"""Area 243: a click on a quote's shading opens its statement, and each quote folds on its own (Adam, 21 October
2026, from a tester, who takes the interviewer's turns out and sets several long quotes under one statement).

A plain click on words a quote shades in the passage puts the caret in that quote's statement and brings its
box into sight in the statements column, a box already in sight left where it is. A drag across the same words
still selects them for a new quote and opens nothing. A word two quotes share opens the first statement by
number. Each quote folds or opens on its own whatever Quotes on the status bar says, keeps that through any
other redraw of the screen, and a press on Quotes puts every quote back to the bar's state. A quote of several
pieces folds to one line holding them all. The two ways of hiding differ (Adam, later on 21 October): one quote
folded alone keeps its first line, while Quotes off hides every quote's words, no first line, its label's
toggle left so one can open alone.

The checks hold behaviour: where the caret goes, what scrolls, what is selected, what folds. The toggle's look
goes to Adam as review shots. The node fixture is invented, about a kite on a hill.
"""
from __future__ import annotations

import json
import re
import shutil
import subprocess
from pathlib import Path

from . import support
from .support import check, skip


def test_quote_link(scratch):
    print("\n243. Quote link: a click on a quote's shading opens its statement, and each quote folds on its own "
          "(Adam, 21 October)")
    node = shutil.which("node")
    if not node:
        skip("243: the click and the folds in node", "node is not installed")
        return
    app = support.text("family/static/shell.js", "apps/idiograph/static/distil.js")
    css = support.text("family/static/style.css", "apps/idiograph/static/distil.css")
    fn = lambda name: app.split(f"function {name}(", 1)[1].split("\n}", 1)[0] if f"function {name}(" in app else ""
    whole = lambda name: f"function {name}(" + fn(name) + "\n}"
    line = lambda start: start + app.split(start, 1)[1].split("\n", 1)[0] if start in app else ""
    listener = lambda start: (start + app.split(start, 1)[1].split("\n  });", 1)[0] + "\n  });") if start in app else ""

    harness = r"""
let MAC = true;
const setTimeout = (f) => f();
const S = { data: { config: { es_quotes: true } }, at: 2, flat: [], pairFocus: null, editing: false, timeEdit: null,
  note: null, selecting: false, wordsPress: false, dragWords: false };
const esc = (s) => String(s).replace(/[&<>]/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;' }[c]));
const escAttr = (s) => esc(s).replace(/"/g, '&quot;');
const log = [];
const classes = () => { const set = new Set(); return { add: (...c) => c.forEach((x) => set.add(x)),
  remove: (...c) => c.forEach((x) => set.delete(x)), contains: (c) => set.has(c),
  toggle(c, on) { if (on === undefined) on = !set.has(c); if (on) set.add(c); else set.delete(c); return on; } }; };
const document = { body: { tag: 'body' }, activeElement: null };
const getComputedStyle = (el) => ({ overflowY: el.overflowY || 'visible' });
// the column the boxes stand in: 600 tall from 150, scrolled by scrollTop
const pane = { overflowY: 'auto', scrollTop: 0, scrollHeight: 4000, clientHeight: 600, parentElement: document.body,
  getBoundingClientRect: () => ({ top: 150, bottom: 750, height: 600 }) };
const holder = { overflowY: 'visible', parentElement: pane };
const PAIRS = [];
function makePair(i, kq, top, height) {
  const kids = {
    '.pair-kq': { value: kq, focus() { document.activeElement = this; } },
    '.pair-kq-line': { textContent: '' },
    '.pair-qtoggle': { attrs: {}, title: '', setAttribute(k, v) { this.attrs[k] = String(v); } },
    '.pair-es': { id: `es-${i}`, focus() { document.activeElement = this; } },
  };
  const el = { dataset: { pid: `p${i}` }, classList: classes(), parentElement: holder, querySelector: (s) => kids[s] || null,
    getBoundingClientRect: () => ({ top: top - pane.scrollTop, bottom: top + height - pane.scrollTop, height }) };
  PAIRS.push(el);
  return el;
}
const pairEls = () => [...PAIRS];
const work = { classList: classes() };
const bar = { attrs: {}, setAttribute(k, v) { this.attrs[k] = String(v); } };
const transcript = { on: {}, addEventListener(type, f) { this.on[type] = f; } };
const rows = { on: {}, addEventListener(type, f) { this.on[type] = f; } };
const $ = (id) => ({ work, 'es-quotes-btn': bar, transcript, 'transcript-rows': rows, en: { focus() {} } }[id] || null);
const growPairs = () => {}; const growField = () => {}; const levelSoon = () => {};
const ROW = { key: 'Initial:7', i: 7, pos: 2, stop: true, seconds: 40, sheet: 'Initial', row: 7 };
S.flat[7] = ROW;
const current = () => ROW;
const keepNote = () => {};
const goTo = async (pos) => { log.push(['goTo', pos]); };
const cueAudio = (t) => log.push(['cue', t]);
const markTurn = () => {}; const noteable = () => false; const openNote = () => {};
const closeRowMenu = () => {}; const closeTimeEdit = () => {}; const openRowMenu = () => {};
const assignSelection = () => null; const playFrom = () => {}; const toRound = () => {};
const isEntryField = () => false;
let pressFocus = null;
let MOVED = false; let LIVE = false;
const pressMoved = () => MOVED;
const selectionLive = () => LIVE;
const snapDrag = () => log.push(['snap']);
const takeSelection = (add) => { log.push(['take', add]); return LIVE; };
const clearPending = () => log.push(['clear']);
const selBarShow = () => {};
"""
    pieces = [harness, line("const quotesFolded = "), line("const quoteShown = ")] + [whole(n) for n in (
        "pairsFoldDraw", "quotesDraw", "quoteOpen", "pairIntoView", "toStatement", "kqTitle", "markedHtml")] + [
        listener("$('transcript').addEventListener('click', (e) => {"),
        listener("$('transcript-rows').addEventListener('mouseup', (e) => {")]
    scenario = r"""
(async () => {
const out = {};
const target = (map) => ({ closest: (sel) => (sel in map ? map[sel] : null) });
const word = (kq) => target({ '.turn': { dataset: { i: '7' } }, '.turn-text .kq': { dataset: { kq } } });
const press = (e) => transcript.on.click({ detail: 1, metaKey: false, ctrlKey: false, shiftKey: false, altKey: false, ...e });
const up = (e) => rows.on.mouseup({ button: 0, detail: 1, metaKey: false, ctrlKey: false, shiftKey: false, altKey: false,
  target: target({}), ...e });
const quote = 'the line sang in the wind ... the whole hill went quiet';

// three statements, the third's box far down the column, out of sight
makePair(0, '"The kite pulled at my wrists"', 200, 260);
makePair(1, `"${quote}"`, 480, 300);
makePair(2, '"I was not ready"', 1400, 280);

// the words two quotes share are marked once, carrying both statements, the first by number first
const html = markedHtml([{ text: 'The kite pulled at my wrists' }], [{ start: 0, end: 8, kq: 2, cls: 'kq' }, { start: 4, end: 20, kq: 0, cls: 'kq' }]);
out.shared = (html.match(/data-kq="([^"]*)"/g) || []).map((m) => m.slice(9, -1));

// a plain click on the third quote's words: the caret in the third statement, its box scrolled into sight
press({ target: word('2') });
await Promise.resolve();
out.third = { focus: document.activeElement && document.activeElement.id, pairFocus: S.pairFocus,
  top: PAIRS[2].getBoundingClientRect().top, bottom: PAIRS[2].getBoundingClientRect().bottom, scroll: pane.scrollTop };

// a click on the first quote's words, whose box is in sight already, after scrolling back: nothing scrolls
pane.scrollTop = 0;
press({ target: word('0') });
out.first = { focus: document.activeElement && document.activeElement.id, scroll: pane.scrollTop };

// a word under two quotes opens the first by number
document.activeElement = null;
press({ target: word('1 2') });
out.both = document.activeElement && document.activeElement.id;

// a drag across shaded words opens nothing and the mouse up takes the words as a selection
document.activeElement = null; pane.scrollTop = 0; log.length = 0;
MOVED = true; LIVE = true; S.wordsPress = true;
press({ target: word('1') });
up({ target: word('1') });
out.drag = { focus: document.activeElement && document.activeElement.id, scroll: pane.scrollTop, log: log.map((l) => l.join(':')) };
MOVED = false; LIVE = false;

// Quotes on: every quote whole; one folded alone; the others stay whole; a redraw keeps it
const shown = () => PAIRS.map((el) => quoteShown(el));
const expanded = () => PAIRS.map((el) => el.querySelector('.pair-qtoggle').attrs['aria-expanded']);
quotesDraw();
out.onStart = shown();
quoteOpen(PAIRS[1], false);
out.onOneShut = { shown: shown(), expanded: expanded(), line: PAIRS[1].querySelector('.pair-kq-line').textContent };
quotesDraw();
out.onRedraw = shown();

// Quotes off by the bar: every quote folded, the one shut put back; one opened alone, its caret in it
S.data.config.es_quotes = false;
quotesDraw();
out.offStart = shown();
quoteOpen(PAIRS[2], true);
out.offOneOpen = { shown: shown(), expanded: expanded(), caret: document.activeElement === PAIRS[2].querySelector('.pair-kq') };
quotesDraw();
out.offRedraw = shown();
quoteOpen(PAIRS[2], false);
out.offRefold = shown();
quoteOpen(PAIRS[0], true);

// Quotes on again: every quote back to whole
S.data.config.es_quotes = true;
quotesDraw();
out.onAgain = { shown: shown(), own: PAIRS.map((el) => el.classList.contains('kq-open') || el.classList.contains('kq-shut')) };

console.log(JSON.stringify(out));
})().catch((e) => { console.log(JSON.stringify({ error: String(e && e.stack || e) })); });
"""
    js = scratch / "a243.js"
    js.write_text(support.i18n_js() + "\n".join(pieces) + "\n" + scenario, encoding="utf-8")
    run = subprocess.run([node, str(js)], capture_output=True, text=True, encoding="utf-8", timeout=60)
    try:
        out = json.loads(run.stdout.strip().splitlines()[-1])
    except (ValueError, IndexError):
        out = {"error": run.stdout + run.stderr}
    if out.get("error"):
        check("243: the node run", False, out["error"][:600])
        return

    third = out["third"]
    check("243: a plain click on a quote's shading puts the caret in its statement and scrolls its box, out of "
          "sight, into the statements column's view", third["focus"] == "es-2" and third["pairFocus"] == "p2"
          and third["scroll"] > 0 and third["top"] >= 150 and third["bottom"] <= 750, str(third))
    check("243: a click on shading whose statement's box is in sight already moves the caret and scrolls nothing",
          out["first"] == {"focus": "es-0", "scroll": 0}, str(out["first"]))
    check("243: words two quotes share are marked with both statements, the first by number first, and a click "
          "there opens the first", "0 2" in out["shared"] and out["both"] == "es-1", str((out["shared"], out["both"])))
    drag = out["drag"]
    check("243: a drag across shaded words opens no statement, scrolls nothing and takes the words selected",
          drag["focus"] is None and drag["scroll"] == 0 and "snap" in drag["log"] and "take:false" in drag["log"]
          and "clear" not in drag["log"], str(drag))
    check("243: with Quotes on, one quote folds alone, its toggle saying so, the others stay whole, and a redraw "
          "of the screen keeps it", out["onStart"] == [True, True, True]
          and out["onOneShut"]["shown"] == [True, False, True]
          and out["onOneShut"]["expanded"] == ["true", "false", "true"] and out["onRedraw"] == [True, False, True],
          str((out["onStart"], out["onOneShut"], out["onRedraw"])))
    check("243: a quote of several pieces folds to one line holding every piece and the ellipsis between them",
          out["onOneShut"]["line"] == '"the line sang in the wind ... the whole hill went quiet"', out["onOneShut"]["line"])
    check("243: Quotes off on the bar hides every quote, the one folded alone among them, and one opens alone with "
          "the caret in it, kept through a redraw and folded again alone",
          out["offStart"] == [False, False, False] and out["offOneOpen"]["shown"] == [False, False, True]
          and out["offOneOpen"]["expanded"] == ["false", "false", "true"] and out["offOneOpen"]["caret"] is True
          and out["offRedraw"] == [False, False, True] and out["offRefold"] == [False, False, False],
          str((out["offStart"], out["offOneOpen"], out["offRedraw"], out["offRefold"])))
    check("243: Quotes on again puts every quote back to whole, none keeping its own state",
          out["onAgain"]["shown"] == [True, True, True] and not any(out["onAgain"]["own"]), str(out["onAgain"]))

    # what the stylesheet shows of a set quote in each state, by its own cascade (Adam, later on 21 October: two
    # ways of hiding a quote). Folded alone under Quotes on, its first line stays. Quotes off hides its words
    # and its arrow entirely, no first line, only its label's toggle left, and one opened alone shows whole.
    shown_css = {}
    for name, folded, own in (("on", False, ""), ("on, folded alone", False, "kq-shut"),
                              ("off", True, ""), ("off, opened alone", True, "kq-open")):
        work = {"id": "work", "classes": {"quotes-folded"} if folded else set()}
        pair = {"classes": {"pair", "kq-filled"} | ({own} if own else set())}
        parts = ("pair-kq", "pair-kq-line", "pair-take", "pair-qtoggle", "pair-qlabel")
        shown_css[name] = sorted(part for part in parts
                                 if _display(css, [work, pair, {"classes": {"pair-body"}}], part) != "none")
    check("243: Quotes on shows a set quote whole with its toggle and arrow, and one folded alone keeps its first "
          "line in place of its words", shown_css["on"] == ["pair-kq", "pair-qtoggle", "pair-take"]
          and shown_css["on, folded alone"] == ["pair-kq-line", "pair-qtoggle", "pair-take"], str(shown_css))
    check("243: Quotes off hides a set quote's words, first line and arrow, leaving only its label's toggle, and "
          "one opened alone shows whole", shown_css["off"] == ["pair-qtoggle"]
          and shown_css["off, opened alone"] == ["pair-kq", "pair-qtoggle", "pair-take"], str(shown_css))


def _display(css: str, chain: list, part: str) -> str:
    """The display a stylesheet gives an element of class `part` inside `chain` (outermost first), by the
    cascade: the matching rule of highest specificity, the later on a tie. Only the selectors the quote's
    parts use: ids, classes, :not(.class), descendant and child."""
    text = re.sub(r"/\*.*?\*/", "", css, flags=re.S)
    target = {"classes": {part}}
    best = (None, (-1, -1), -1)
    for order, (sels, body) in enumerate(re.findall(r"([^{}]+)\{([^{}]*)\}", text)):
        m = re.search(r"(?:^|;)\s*display\s*:\s*([^;]+)", body)
        if not m:
            continue
        for sel in sels.split(","):
            parts = re.findall(r">|[^\s>]+", sel.strip())
            if not parts or not _compound(parts[-1], target) or not _ancestors(parts[:-1], chain):
                continue
            spec = (len(re.findall(r"#[\w-]+", sel)), len(re.findall(r"[.:][\w-]+", sel.replace(":not", ""))))
            if (spec, order) >= (best[1], best[2]):
                best = (m.group(1).strip(), spec, order)
    return best[0] or "block"


def _compound(sel: str, el: dict) -> bool:
    if sel.startswith("@") or re.search(r"::|:(?!not\()", sel):
        return False
    nots = re.findall(r":not\(\.([\w-]+)\)", sel)
    rest = re.sub(r":not\([^)]*\)", "", sel)
    if re.match(r"^[a-z*]", rest):
        return False
    ids = re.findall(r"#([\w-]+)", rest)
    classes = set(re.findall(r"\.([\w-]+)", rest))
    return (all(el.get("id") == i for i in ids) and classes <= el["classes"]
            and not any(c in el["classes"] for c in nots))


def _ancestors(parts: list, chain: list) -> bool:
    if not parts:
        return True
    child = parts[-1] == ">"
    sel = parts[-2] if child else parts[-1]
    rest = parts[:-2] if child else parts[:-1]
    places = [len(chain) - 1] if child else range(len(chain) - 1, -1, -1)
    return any(_compound(sel, chain[i]) and _ancestors(rest, chain[:i]) for i in places if i >= 0)
