"""Area 315: a passage opened from a board names that board's step for the way back (loose01, 1 November 2026).

Found on 31 October by the i18ncodes build: Go to the passage on the LGETs board named its way back "gets", and a
timepoint's PETs named no timepoint, so the statements bar's LGETs step (or PETs step at T2) opened that board
afresh, from its start, where the step for the board he came from is the way back to it, his place on the canvas and
his selection kept, as Experiential statements from the bar does it. Now `thToPassage` names the step by its key, as
the bar's own steps do (TH_STEPS): pets with its timepoint, lpets, gets, lgets.

What is checked: in node, on themes.js's own `thToPassage` and distil.js's own `openPassage` and `esStep`, from a
card on each of PETs at T1, PETs at T2, a participant's LPETs, GETs and LGETs, with the route and the drawing stubbed:
the statements bar's step for that board takes the way back (the board reopened with what it kept), and another step
opens its own board afresh. Every word invented: an allotment's newcomers, Wren and Ash."""
from __future__ import annotations

import json
import shutil
import subprocess

from . import support
from .support import check, skip

HARNESS = r"""
const calls = [];
const noop = () => {};
const say = (line) => calls.push(['say', line]);
const unsay = noop, needsRestart = () => false;
const RESTART_LINE = 'Restart.', OPENING_LINE = 'Opening.';
const $ = (id) => ({ hidden: false, textContent: '', style: {}, pause: noop, scrollTop: 0 });
const thTitleDone = noop, thNoteDone = noop, thVmenu = noop, thViewEnd = noop, thPile = noop, thXmenu = noop,
  thCasemenu = noop, thSideShut = noop, thAiCard = noop, thExported = noop, thMade = noop, thMenuClose = noop;
const thFlush = async () => {};
const gtSplit = (key) => { const [kase, kind, ident] = key.split('/'); return { kase, kind, ident }; };
const GETS_CASES = [{ case: 'P2 - Ash', path: 'plots/P2 Ash/P2 Ash - EN & ES.xlsx' }];
const gtCase = (name) => GETS_CASES.find((c) => c.case === name) || null;
const navGo = (again, open) => open();
// the boards' opens as the way back calls them, what each was handed
const themesOpen = (path, opts) => calls.push(['open pets', path, opts.timepoint || null, !!opts.lpets, opts.board, !!opts.restore]);
const getsOpen = (path, opts) => calls.push(['open gets', path, !!opts.lpets, opts.board, !!opts.restore]);
// the statements screen as openPassage and esStep find it
const S = { data: null, backTo: null, dirty: false };
let TP = null;
const tpList = () => (TP ? [1, 2] : null);
const tpHere = () => (TP ? { n: TP } : null);
const api = async (route, body) => ({ path: body.path, config: { interviewer: 'Kit' },
  sheets: [{ name: body.passage.sheet, rows: [{ row: body.passage.row, name: 'Ash' }] }] });
const startCase = (data) => { S.data = { path: data.path, name: 'P2 - Ash' }; };
const current = () => null, pairEls = () => [], guideHolds = () => false, lightMarks = noop, passageStartInView = noop;
const requestAnimationFrame = noop;
// the bar's way back, as toLibrary takes it (distil.js)
const toLibrary = async () => { const to = S.backTo; S.backTo = null; calls.push(['way back']); await to.back(); };
const openThemes = (path, from, label, more) => calls.push(['fresh pets', (more || {}).timepoint || null]);
const esToGets = (more) => calls.push(['fresh gets', !!(more && more.lpets)]);
const esToTraj = () => calls.push(['fresh trajectories']);
"""

SCENARIO = r"""
const TH0 = { live: true, busy: false, dirty: false, label: 'P2 - Ash', back: 'HOME', to: 'cases', meta: { id: 'v3' },
  view: { x: 10, y: 20, z: 0.9 }, lastPick: null, ask: 0, face: 'canvas', viewing: null };
const pets = (key) => ({ cards: { [key]: { key, text: 'I asked next door' } }, groups: [], discarded: [] });
const gets = (key) => ({ cards: { [key]: { key, kind: 'es', case: 'P2 - Ash' } }, groups: [], discarded: [] });
var TH;
const boards = {
  pets1: { mode: 'pets', path: 'plots/P2 Ash/P2 Ash - EN & ES.xlsx', tp: null, lpets: false, lgets: false, key: 'T1:4:0', tpHere: 1 },
  pets2: { mode: 'pets', path: 'plots/P2 Ash/P2 Ash - EN & ES.xlsx', tp: 2, lpets: false, lgets: false, key: 'T2:3:0', tpHere: 2 },
  lpets: { mode: 'gets', path: 'plots/P2 Ash/P2 Ash - EN & ES.xlsx', tp: null, lpets: true, lgets: false, key: 'P2 - Ash/es/T2:3:0', tpHere: 2 },
  gets: { mode: 'gets', path: 'plots/P1 Wren/P1 Wren - EN & ES.xlsx', tp: null, lpets: false, lgets: false, key: 'P2 - Ash/es/T1:4:0', tpHere: 1 },
  lgets: { mode: 'gets', path: 'plots/P1 Wren/P1 Wren - EN & ES.xlsx', tp: null, lpets: false, lgets: true, key: 'P2 - Ash/es/T2:3:0', tpHere: 2 },
};
async function from(name, step) {
  const b = boards[name];
  TH = Object.assign({}, TH0, { mode: b.mode, path: b.path, tp: b.tp, lpets: b.lpets, lgets: b.lgets,
    sel: { cards: new Set([b.key]), groups: new Set(), stickies: new Set() },
    v: b.mode === 'gets' ? gets(b.key) : pets(b.key) });
  S.backTo = null;
  TP = b.tpHere;
  calls.splice(0);
  await thToPassage(b.key);
  const to = S.backTo ? [S.backTo.to, S.backTo.timepoint] : null;
  calls.splice(0);
  await esStep(step);
  await new Promise((r) => setTimeout(r, 0));
  return { to, did: calls.splice(0) };
}
(async () => {
  const out = {};
  for (const [name, step] of [['pets1', 'pets'], ['pets2', 'pets'], ['lpets', 'lpets'], ['gets', 'gets'], ['lgets', 'lgets']]) {
    out[name] = await from(name, step);
  }
  // another step than the board he came from opens its own board afresh
  out.lgetsToLpets = await from('lgets', 'lpets');
  out.pets2ToLgets = await from('pets2', 'lgets');
  console.log(JSON.stringify(out));
})().catch((e) => { console.error(String(e && e.stack || e)); process.exit(1); });
"""


def test_passage_way_back(scratch):
    print("\n315. The way back from a passage opened on a board (loose01, 1 November 2026): the statements bar's step for "
          "the board he left, LGETs and a timepoint's PETs as much as PETs, LPETs and GETs, reopens it as he left it")
    node = shutil.which("node")
    if not node:
        skip("315: the way back in node", "node is not on this machine")
        return
    tjs = support.text("apps/idiograph/static/themes.js")
    djs = support.text("apps/idiograph/static/distil.js")
    fn = lambda src, name: src.split(f"function {name}(", 1)[1].split("\n}", 1)[0] if f"function {name}(" in src else ""
    whole = lambda src, name: (("async " if f"async function {name}(" in src else "") + f"function {name}(" + fn(src, name) + "\n}")
    line = lambda src, start: start + src.split(start, 1)[1].split("\n", 1)[0] if start in src else ""
    pieces = [HARNESS, line(tjs, "const TH_NO_PASSAGE = "), line(djs, "const NO_PASSAGE_LINE = ")]
    pieces += [whole(tjs, n) for n in ("thIsStatement", "thLineOf", "thToPassage")]
    pieces += [whole(djs, n) for n in ("openPassage", "esStep")]
    script = scratch / "passage-way-back-315.js"
    script.write_text(support.i18n_js() + "\n".join(pieces + [SCENARIO]), encoding="utf-8")
    run = subprocess.run([node, str(script)], capture_output=True, text=True, encoding="utf-8", timeout=60)
    o = json.loads(run.stdout) if run.returncode == 0 and run.stdout.strip() else {}
    detail = (run.stdout + run.stderr)[:600]
    ash = "plots/P2 Ash/P2 Ash - EN & ES.xlsx"
    wren = "plots/P1 Wren/P1 Wren - EN & ES.xlsx"
    check("315: in node, from a card on PETs, at T1 and at T2, the statements bar's PETs step is the way back, the "
          "timepoint's PETs reopened with the board and place they kept",
          o.get("pets1") == {"to": ["pets", None], "did": [["way back"], ["open pets", ash, None, False, "v3", True]]}
          and o.get("pets2") == {"to": ["pets", 2], "did": [["way back"], ["open pets", ash, 2, False, "v3", True]]},
          str([o.get("pets1"), o.get("pets2")]) if o else detail)
    check("315: in node, from a card on a participant's LPETs and on the project's GETs, that step is the way back",
          o.get("lpets") == {"to": ["lpets", None], "did": [["way back"], ["open gets", ash, True, "v3", True]]}
          and o.get("gets") == {"to": ["gets", None], "did": [["way back"], ["open gets", wren, False, "v3", True]]},
          str([o.get("lpets"), o.get("gets")]) if o else detail)
    check("315: in node, from a card on the LGETs, the statements bar's LGETs step is the way back, the LGETs reopened "
          "with the board and place they kept, where it opened them afresh",
          o.get("lgets") == {"to": ["lgets", None], "did": [["way back"], ["open gets", wren, False, "v3", True]]},
          str(o.get("lgets")) if o else detail)
    check("315: in node, another step than the board he came from opens its own board afresh",
          o.get("lgetsToLpets") == {"to": ["lgets", None], "did": [["fresh gets", True]]}
          and o.get("pets2ToLgets") == {"to": ["pets", 2], "did": [["fresh gets", False]]},
          str([o.get("lgetsToLpets"), o.get("pets2ToLgets")]) if o else detail)
