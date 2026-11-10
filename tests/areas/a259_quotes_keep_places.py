"""Area 259: cards keep their places on the canvas with the quotes shown (23 October 2026, a tester: "The
shuffling of the cards on the canvas is broken if you have the quotes shown - they jump around a lot").

With Quotes on cards the board makes room for each quote as a view, and the file keeps every card where it
stands with the quotes off. Two things broke that. The room's sign held the quotes' shares in the order the
cards were drawn, and a card picked up is drawn last, so the first act after an open took the place it left
a card at, room and all, as the file's: the card showed lower by its quote's room and the drop's settle pushed
its neighbours down the board for good, and the next act pushed them back. And every settle (a drop, a label
retitled or described, the room made on an open) was weighed in the shown room, where the room's own moves
counted as frames that grew, so whole PETs were pushed about.

The checks run the page's own board code in node on an invented board about learning to sail, quotes on, and
read what the page would save: a card moved sideways moves alone, after a change of drawing order as a drag
makes; a label that grows moves in the file exactly what it moves with the quotes off; the quotes off and on
again leave the file and the shown places as they were; and a board saved by an agent shows with its quotes
and saves back untouched.
"""
from __future__ import annotations

import json
import shutil
import subprocess

from . import support
from .support import check, skip
from .a205_card_quotes_and_by_participant import STUBS

SCENARIO = r"""
(() => {
thPlayerDraw = () => {};
thPanelFollow = () => {};
thDrawSel = () => {};
thEase = () => {};
thSoon = () => {};
thMomentum = () => {};
thCorners = () => {};
thMapPlace = () => {};
thDrawCounts = () => {};
thPlace = () => { thRoomFollow(); };
const out = {};
const card = (text, x, y) => ({ x, y, text, time: '2:10', sheet: 'Initial' });
// a PET of two columns: a and b on the left, c and d on the right, a with a long quote; a second PET to the right
const board = () => ({
  cards: { a: card('Wind caught the sail', 0, 40), b: card('Hands on the sheet', 0, 150), c: card('A gust from nowhere', 220, 40),
           d: card('The boom swings over', 220, 150), e: card('Back on the jetty', 460, 40), f: card('Salt on the lips', 460, 150),
           h: card('Ropes coiled on the deck', 100, -120) },
  groups: [{ id: 'g1', label: 'Learning the wind', members: ['a', 'b', 'c', 'd'], x: 0, y: 0 },
           { id: 'g2', label: 'Coming ashore', members: ['e', 'f'], x: 460, y: 0 }],
  discarded: [], stacks: {} });
let quotes = true;
let order = ['a', 'c'];
let labelH = 26;
// what thRender does for the room: each card measured, its quote's share among it, in the order drawn
const measure = () => {
  TH.sizes = { a: { w: 200, h: 90 }, b: { w: 200, h: 90 }, c: { w: 200, h: 90 }, d: { w: 200, h: 90 }, e: { w: 200, h: 90 },
               f: { w: 200, h: 90 }, h: { w: 200, h: 90 }, g1: { w: 160, h: labelH }, g2: { w: 160, h: 26 } };
  TH.qfull = {}; TH.qextra = {}; TH.baseH = {};
  if (quotes) for (const k of order) { TH.qfull[k] = k === 'a' ? 150 : 120; TH.qextra[k] = k === 'a' ? 60 : 30; TH.sizes[k] = { w: 200, h: TH.qfull[k] }; }
};
thRender = () => { measure(); thStacksRoom(); TH.layout = thLayout(TH.v, thSize, null); };
const open = () => {
  TH.v = board(); TH.opened = new Set(); TH.shifts = []; TH.roomShown = null; TH.removed = new Set(); TH.undo = []; TH.redo = [];
  TH.live = true; TH.mode = 'pets';
  TH.els = { cards: {}, under: {}, labels: {}, frames: {}, stickies: {}, rails: {} };
  thRender();
};
const saved = () => { const s = thUnshifted(TH.v).cards; return Object.fromEntries(Object.entries(s).map(([k, c]) => [k, [Math.round(c.x), Math.round(c.y)]])); };
const shown = () => Object.fromEntries(Object.entries(TH.v.cards).map(([k, c]) => [k, [Math.round(c.x), Math.round(c.y)]]));

// ── a card moved sideways, after it was picked up and so drawn last
quotes = true; order = ['a', 'c']; open();
const file0 = saved();
const at0 = shown();
{
  const before = thSnap(TH.v, TH.removed); const was = thLabelBoxes(TH.layout);
  order = ['c', 'a'];
  TH.v.cards.b.x -= 20;
  thDone(before, 'Moved', { settle: ['b'], stay: true, was });
}
out.sideways = { file: saved(), was: file0, shownB: shown().b, shownWas: at0.b };

// ── a label that grows two lines, with the quotes on and with them off, from the same board
const grow = (on) => {
  quotes = on; order = ['a', 'c']; labelH = 26; open();
  const before = thSnap(TH.v, TH.removed); const was = thLabelBoxes(TH.layout);
  TH.v.groups[0].label = 'Learning the wind, and how it changes as the afternoon turns';
  labelH = 70;
  thDone(before, 'Renamed a label', { settle: [], labels: ['g1'], was });
  labelH = 26;
  return saved();
};
out.grow = { on: grow(true), off: grow(false) };

// ── the quotes off and on again
quotes = true; order = ['a', 'c']; open();
const kept = saved(); const seen = shown();
quotes = false; thRender();
const offFile = saved(); const offShown = shown();
quotes = true; thRender();
out.toggle = { kept, seen, offFile, offShown, againFile: saved(), againShown: shown() };

// ── a board as an agent saved it, shown with its quotes, saves back as it came
quotes = true; order = ['a', 'c']; open();
TH.meta = { id: 'v1', name: 'Board 1', created: '', updated: '' };
const body = thBody(TH.v, TH.meta);
out.agent = Object.fromEntries(Object.entries(body.cards).map(([k, c]) => [k, [c.x, c.y]]));
out.board = Object.fromEntries(Object.entries(board().cards).map(([k, c]) => [k, [c.x, c.y]]));
console.log(JSON.stringify(out));
})();
"""


def test_quotes_keep_places(scratch):
    print("\n259. Cards keep their places with the quotes shown: a move moves what it moves, a settle weighs the file "
          "as it is with the quotes off, and the quotes off and on rewrite nothing (23 October)")
    node = shutil.which("node")
    if not node:
        skip("259: the board in node", "node is not installed")
        return
    js = support.text("apps/idiograph/static/themes.js")
    script = scratch / "quotes-keep-places-259.js"
    script.write_text(support.i18n_js() + STUBS + js + SCENARIO, encoding="utf-8")
    run = subprocess.run([node, str(script)], capture_output=True, text=True, encoding="utf-8", timeout=120)
    if run.returncode != 0:
        check("259: the board runs in node", False, run.stderr.strip()[:800])
        return
    o = json.loads(run.stdout)
    s = o["sideways"]
    moved = sorted(k for k in s["was"] if s["file"][k] != s["was"][k])
    check("259: with the quotes on, a card under a quote moved sideways after being picked up (drawn last) moves "
          "alone in the file, by just the move, and shows where it was let go",
          moved == ["b"] and s["file"]["b"] == [s["was"]["b"][0] - 20, s["was"]["b"][1]]
          and s["shownB"] == [s["shownWas"][0] - 20, s["shownWas"][1]], json.dumps(s))
    g = o["grow"]
    check("259: a label that grows two lines with the quotes on moves in the file just what it moves with them off",
          g["on"] == g["off"] and g["on"]["h"] != [100, -120], json.dumps(g))
    t = o["toggle"]
    check("259: the quotes off and on again rewrite no place in the file, and the board shows again as it did",
          t["offFile"] == t["kept"] and t["againFile"] == t["kept"] and t["againShown"] == t["seen"]
          and t["offShown"] == t["kept"] and t["seen"] != t["kept"], json.dumps(t))
    check("259: a board as an agent saved it, shown with its quotes, saves back with every card where it came",
          o["agent"] == o["board"], json.dumps(o["agent"]))
