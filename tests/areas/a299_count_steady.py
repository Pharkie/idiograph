"""Area 299: the statements screen's count held steady as you move (countdrift, 30 October 2026).

On Experiential statements the status bar's count, "122 statements", changed as he moved between passages (122, then
120, then 124) while the workbook held the same statements. A move drew the new passage's pairs into the fields
before it named that passage as the one the fields hold, so the count drawn with the pairs took the new passage twice,
once from the fields and once as saved, and the passage just left not at all, and nothing counted again until the
next keystroke. The passage the fields hold is named first now, in `drawTurn` and in `findFieldsAgain`. The count
takes every row of the workbook, an interviewer's included, as the board's cards and the agents' `statements` do, and
the passage being worked on as its fields hold it, a statement typed and not yet saved counted as it goes in, as a
word count counts what is typed.

What is checked: in node on distil.js's own `drawTurn`, `goTo`, `commit`, the pairs' functions and the fields' own
input listener, over the demo's Juno as `/api/load` reads her (the demo's invented interviews, on living with a dog),
the count at the open the same as the board's cards and the statements the workbook holds, the same after a step onto
every passage forward and back and after a jump, a statement typed adding one at once and still one after the save on
the move, a pair removed and a statement emptied each taking one, and the count after each the cards the workbook
would hold. A statement written on one of the interviewer's turns is counted from the open. The route is stubbed with
the server's own cleaning of the pairs. Only the statements added are new words, invented on the same dog."""
from __future__ import annotations

import json
import shutil

from . import support
from .support import check, skip


def whole(src: str, head: str) -> str:
    at = src.index(head)
    return src[at:src.index("\n}\n", at) + 3]


def line_of(js: str, start: str) -> str:
    at = js.index(start)
    return js[at:js.index("\n", at) + 1]


def statement(js: str, start: str) -> str:
    at = js.index(start)
    return js[at:js.index(";\n", at) + 2]


def listener(js: str, head: str) -> str:
    at = js.index(head)
    return js[at:js.index("\n  });\n", at) + 7]


HARNESS = r"""
const noop = () => {};
// what drawTurn, goTo and commit call beyond the pairs and the count, quiet here
for (const name of ['keepNote', 'closeEditor', 'closeTimeEdit', 'closeRowMenu', 'selBarHide', 'hideStale', 'markCurrent',
  'findSheetDrawn', 'resetAI', 'loadAudio', 'markListening', 'growNotes', 'drawAct', 'drawRoundBar', 'drawRoundMarks',
  'clockRound', 'drawClock', 'clockTitle', 'centreCurrent', 'focusEntry', 'loadExamples', 'growPairs', 'drawWordCount',
  'runNudges', 'markKeyQuotes', 'undoPush', 'say', 'flashCount', 'closeLeftRounds', 'awayReset', 'clearPending',
  'drawProgress', 'drawToPair', 'afterCommit', 'showStale', 'growField', 'pairCount', 'repaintRow', 'pairsFoldDraw',
  'requestAnimationFrame']) globalThis[name] = noop;
const findOpen = () => false;
// no quote being built across her passages, nor any quote running on into the next (quotespan, area 301)
const pendingRows = () => [];
const kqFarKeys = () => [];
const roundsHere = () => false;
const placeholderLine = () => '';
const sheetPlace = () => ({ on: 0, of: 0, title: '' });
const roundPlace = () => ({ on: 0, of: 0, title: '' });
const awayTally = () => ({});
const drawTranscript = (sheet) => { S.sheetDrawn = sheet; };
const setTimeout = noop;
const CARD_REACH = 'hold';
const REACH = {};
const PROMPT_FALLBACK = '';
const document = { fonts: { status: 'loaded' }, activeElement: null, body: {} };
const pairHtml = (id) => `<div class="pair" data-pid="${id}"></div>`;

// the fields' column: each pair a statement and a quote, in order, as the page holds them
const field = (cls) => ({ value: '', placeholder: '', id: '', classList: { contains: (c) => c === cls }, setAttribute: noop,
  focus: noop, closest: null });
const made = (html) => [...html.matchAll(/class="pair" data-pid="([^"]+)"/g)].map((m) => pairEl(m[1]));
function pairEl(pid) {
  const parts = { '.pair-es': field('pair-es'), '.pair-kq': field('pair-kq'), '.pair-num': { textContent: '' } };
  const el = {
    dataset: { pid },
    querySelector: (sel) => parts[sel] || null,
    remove: () => { const i = PAIRS.list.indexOf(el); if (i >= 0) PAIRS.list.splice(i, 1); },
    insertAdjacentHTML: (where, html) => { PAIRS.list.splice(PAIRS.list.indexOf(el), 0, ...made(html)); },
    get nextElementSibling() { return PAIRS.list[PAIRS.list.indexOf(el) + 1] || null; },
  };
  for (const f of [parts['.pair-es'], parts['.pair-kq']]) f.closest = (sel) => (sel === '.pair' ? el : null);
  return el;
}
const PAIRS = {
  list: [], heard: [],
  set innerHTML(html) { PAIRS.list = made(html); },
  querySelectorAll: (sel) => (sel === '.pair' ? PAIRS.list.slice() : []),
  querySelector: (sel) => { const m = sel.match(/data-pid="([^"]+)"/); return m ? PAIRS.list.find((p) => p.dataset.pid === m[1]) || null : null; },
  insertAdjacentHTML: (where, html) => { PAIRS.list.push(...made(html)); },
  addEventListener: (type, fn) => { if (type === 'input') PAIRS.heard.push(fn); },
};
const plainEl = () => ({ textContent: '', title: '', value: '', hidden: false, focus: noop,
  classList: { add: noop, remove: noop, toggle: noop, contains: () => false } });
const ELS = { pairs: PAIRS, 'es-count': plainEl(), en: plainEl(), saved: plainEl() };
const $ = (id) => ELS[id] || (ELS[id] = plainEl());

// the route: the pairs saved as the server cleans them, stripped and an empty pair dropped
const saved = [];
async function api(url, body) {
  saved.push(url);
  const pairs = body.pairs.map((p) => ({ es: p.es.trim(), kq: p.kq.trim() })).filter((p) => p.es || p.kq);
  return { pairs, v: `v${saved.length}`, progress: S.data.progress, unpaired: false };
}

const DATA = __DATA__;
const S = { data: { path: 'Juno - EN & ES.xlsx', rounds: [], progress: { states: {} }, config: {} },
  flat: [], stops: [], at: 0, pairsRow: null, dirty: false, lastInput: {}, pending: [], sheetDrawn: null };
// the rows as startCase reads /api/load's answer: every sheet's rows in order, a stop on each of the participant's
for (const sheet of DATA.sheets) for (const row of sheet.rows) S.flat.push(row);
S.flat.forEach((row, i) => { row.i = i; row.key = `${row.sheet}:${row.row}`; });
for (const row of S.flat) {
  row.stop = !!(row.name && row.name.trim().toLowerCase() !== 'adam');
  if (row.stop) { row.pos = S.stops.length; S.stops.push(row.i); }
}
""" + "\n__PIECES__\n" + r"""
const shown = () => { const m = ELS['es-count'].textContent.match(/\d+/); return m ? Number(m[0]) : null; };
// the statements the workbook would hold once each row is saved, as the board's cards count them
const inBook = () => S.flat.reduce((n, row) => n + rowPairs(row).filter((p) => p.es.trim()).length, 0);
// a keystroke into a pair's statement, heard by the fields' own listener
const type = (el, words) => { const f = el.querySelector('.pair-es'); f.value = words; for (const fn of PAIRS.heard) fn({ target: f }); };
const holding = (row) => row && rowPairs(row).filter((p) => p.es.trim()).length;

(async () => {
  const out = { at_open: null, book: null, forward: [], back: [], jump: null };
  drawTurn();
  out.at_open = shown();
  out.book = inBook();
  // a step onto every passage, then back to the first, by the move every button and key takes
  while (S.at < S.stops.length - 1) { await goTo(S.at + 1); out.forward.push(shown()); }
  while (S.at > 0) { await goTo(S.at - 1); out.back.push(shown()); }
  // a jump to a passage far off, as a click in the column makes, from one with statements to one with more
  const most = S.stops.reduce((best, i, k) => (holding(S.flat[i]) > holding(S.flat[S.stops[best]]) ? k : best), 0);
  await goTo(most);
  out.jump = shown();

  // a statement added to the passage being worked on, counted as it goes in and kept by the save on the move
  const before = shown();
  const added = addAnother();
  type(added, 'Waiting by the door for the lead before he has even stood up');
  out.typed = { before, now: shown() };
  await goTo(S.at + 1);
  out.added = { now: shown(), book: inBook(), saves: saved.length };
  const steps = [];
  for (let k = 0; k < 6; k += 1) { await goTo(k % 2 ? S.at + 1 : S.at - 1); steps.push(shown()); }
  out.added.steady = steps;

  // a pair removed, then a statement emptied, each on a passage of its own
  await goTo(most);
  const was = shown();
  removePair(PAIRS.list[0]);
  out.removed = { was, now: shown() };
  await goTo(S.at + 1);
  out.removed.after = shown();
  out.removed.book = inBook();
  await goTo(most);
  const had = shown();
  type(PAIRS.list[0], '   ');
  out.emptied = { had, now: shown() };
  await goTo(S.at - 1);
  out.emptied.after = shown();
  out.emptied.book = inBook();
  await goTo(most);
  out.emptied.back = shown();

  // the fields drawn again in place, as a replace across the passage does
  findFieldsAgain(current());
  out.again = { now: shown(), book: inBook() };
  console.log(JSON.stringify(out));
})().catch((e) => { console.log(JSON.stringify({ error: String(e && e.stack || e) })); });
"""


def test_count_steady(scratch):
    print("\n299. The statements screen's count steady as you move, one more for a statement added and one fewer "
          "for one removed or emptied")
    if not shutil.which("node"):
        skip("299: the count as you move, under node", "node is not on this machine")
        return
    import themes
    import workbook as wb_mod

    # the demo as it ships, every one of Juno's statements, never the suite's head start of six passages
    shipped = len(themes.read_cards(support.DEMO_SHIPPED / "Juno - EN & ES.xlsx")["cards"])
    book = scratch / "a299" / "Juno - EN & ES.xlsx"
    book.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(support.DEMO_SHIPPED / "Juno - EN & ES.xlsx", book)
    # and a statement on one of the interviewer's turns, as an agent's write can leave one, which the board's
    # cards count and so the status bar does
    asked = next(r for s in wb_mod.read_case(book)["sheets"] for r in s["rows"]
                 if r["name"] == "Adam" and r["text"].strip())
    wb_mod.save_turn(book, asked["sheet"], asked["row"], None, None, None,
                     pairs=[{"es": "Asking what the first walk of the day is like", "kq": ""}])
    data = wb_mod.read_case(book)
    cards = len(themes.read_cards(book)["cards"])
    js = support.text("apps/idiograph/static/distil.js")
    quote = support.text("family/static/quote.js")
    pieces = "\n".join([
        support.i18n_js(),
        line_of(quote, "const NO_QUOTE = "), line_of(quote, "const noQuote = "),
        whole(quote, "function pairsByOrder("), whole(quote, "function pairsToCells("),
        "let pairSeq = 0;",
        line_of(js, "const pairEls = "), line_of(js, "const pairOf = "), line_of(js, "const pairsNow = "),
        line_of(js, "const pairEmpty = "), line_of(js, "const current = "), line_of(js, "const kqSignature = "),
        statement(js, "const isEntryField = "),
        whole(js, "function rowPairs("), whole(js, "function drawPairs("), whole(js, "function insertPair("),
        whole(js, "function pairsDrawn("), whole(js, "function pairsChanged("), whole(js, "function livePairs("),
        whole(js, "function esCountDraw("), whole(js, "function addAnother("), whole(js, "function removePair("),
        whole(js, "function drawTurn("), whole(js, "function findFieldsAgain("), whole(js, "function goTo("),
        whole(js, "async function commit("),
        listener(js, "$('pairs').addEventListener('input', (e) => {"),
    ])
    script = HARNESS.replace("__DATA__", json.dumps(data)).replace("__PIECES__", pieces)
    ran = support.run_node(script, scratch, "a299-count.js")
    try:
        got = json.loads(ran.stdout.strip().splitlines()[-1])
    except (ValueError, IndexError):
        got = {}
    def detail(*keys):
        return ran.stderr[-600:] or json.dumps({k: got.get(k) for k in keys})[:700]

    n = got.get("at_open")
    check("299: at the open the status bar counts the statements the workbook holds, an interviewer's turn's among "
          "them, as the board's cards do",
          isinstance(n, int) and n == got.get("book") == cards == shipped + 1 > 20, f"{detail('at_open', 'book')} cards {cards}")
    forward, back = got.get("forward") or [], got.get("back") or []
    check("299: a step onto every passage and back again leaves the count where it was",
          len(forward) == len(back) > 2 and set(forward) == set(back) == {n} and got.get("jump") == n,
          detail("forward", "back", "jump"))
    typed, added = got.get("typed") or {}, got.get("added") or {}
    check("299: a statement typed into a new pair adds one as it goes in, and the save on the move keeps it one",
          typed.get("now") == typed.get("before", -9) + 1 == added.get("now") == added.get("book")
          and added.get("saves") == 1 and set(added.get("steady") or [0]) == {added.get("now")},
          detail("typed", "added"))
    removed = got.get("removed") or {}
    check("299: a pair removed takes one away, and the count stays so after the move",
          removed.get("now") == removed.get("was", -9) - 1 == removed.get("after") == removed.get("book"),
          detail("removed"))
    emptied = got.get("emptied") or {}
    check("299: a statement emptied takes one away, and the count stays so across the move and back",
          emptied.get("now") == emptied.get("had", -9) - 1 == emptied.get("after") == emptied.get("book")
          == emptied.get("back"), detail("emptied"))
    again = got.get("again") or {}
    check("299: the fields drawn again in place leave the count as it was",
          again.get("now") == again.get("book") == emptied.get("back"), detail("again", "emptied"))
