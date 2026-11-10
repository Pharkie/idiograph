"""Area 264: the boards' status bar counts add up (Adam, 26 October 2026, wording C of countskofi's drawings).

Until now the bar said "3 PETs", "25 in PETs", "14 not placed", "2 set aside" and "5 stacked" with no total and no
unit, which left him unsure whether the statements stacked were among those in PETs (they were not). Now it says
the total first and where they are after it, "46 ES: 25 in PETs, 5 stacked, 2 set aside, 14 not placed", then the
PETs, and on GETs, LGETs and LPETs boards the unit is cards, "11 cards: 7 in GETs, 1 set aside, 3 not placed". The
parts are the statements or cards in their places, a stack's top once and the statements under it apart, so they
add to the total, and a total shows only where every place holding one is shown.

The checks run the page's own `thStatusDraw` in node on invented boards about learning to bake bread, with
sub-PETs, stacks under a top in a PET, in Not placed and set aside, statements set aside, waiting and loose on the
canvas, and read the bar it draws: the total equals its parts and the statements or cards the board holds, on
PETs, GETs and LPETs boards, and a count unticked takes the total away only while it holds something. Words,
layout and the widths, 1280 and 720, go to Adam as review shots, and area 269 sees in a browser that the bar
keeps the total and its parts at both.
"""
from __future__ import annotations

import json
import re
import shutil
import subprocess

from . import support
from .support import check, skip
from .a201_status_bar_and_palette import STUBS

SCENARIO = r"""
const out = {};
for (const id of ['th-status-counts', 'th-palette']) ELS[id] = new El(id);
ELS['th-stage'] = Object.assign(new El('th-stage'), { clientWidth: 1000, clientHeight: 600 });
ELS.bar = Object.assign(new El('bar'), { offsetHeight: 30 });
thCorners = () => {};
thMapPlace = () => {};
const box = ELS['th-status-counts'];
const card = (text, more) => Object.assign({ x: 0, y: 0, text }, more || {});
const real = (v, gets) => Object.values(v.cards).filter((c) => !c.missing && !(gets && c.kind === 'pn')).length;
const drawn = (v, gets) => {
  TH.v = v; TH.mode = gets ? 'gets' : 'pets';
  thStatusDraw();
  return { text: box.textContent, stats: [...box.innerHTML.matchAll(/data-stat="([a-z]+)"/g)].map((m) => m[1]), real: real(v, gets) };
};
TH.config = { status_bar: true };
TH.sel = { cards: new Set(), groups: new Set(), stickies: new Set() };

// a PETs board: two PETs, one with two sub-PETs, stacks under a top in a sub-PET, under one waiting and under
// one set aside, statements waiting in Not placed, one loose on the canvas and two set aside, one card missing
const pets = {
  waits: true,
  cards: {
    s1: card('The first loaf sank'), s2: card('It sank again'), s3: card('Flour on every surface'),
    s4: card('Proving overnight'), s5: card('Proving, the long wait'), s6: card('Kneading as a rest'),
    s7: card('My grandmother\'s tin'), s8: card('The tin, still dented'), s9: card('Burnt crust'),
    w1: card('Buying a scale', { wait: true }), w2: card('Weighing, not guessing', { wait: true }),
    w3: card('Weighing again', { wait: true }), l1: card('Sharing a loaf'),
    x1: card('A shop loaf'), x2: card('Shop bread, plain'), x3: card('Sourdough starter'),
    gone: card('A line no longer in the sheet', { missing: true }),
  },
  groups: [
    { id: 'P1', label: 'Failing in flour', members: ['S1', 'S2', 's3'] },
    { id: 'S1', label: 'Sinking loaves', members: ['s1'] },
    { id: 'S2', label: 'Waiting on the dough', members: ['s4', 's6'] },
    { id: 'P2', label: 'Bread as family', members: ['s7', 's9'] },
  ],
  discarded: ['x1', 'x3'],
  stacks: { s1: ['s2'], s4: ['s5'], s7: ['s8'], w2: ['w3'], x1: ['x2'] },
};
for (const k of ['w1', 'w2', 'w3']) pets.cards[k].wait = k !== 'w3';
out.pets = drawn(pets, false);

// a selection follows the PETs, "1 ES selected"
TH.sel.cards.add('s3');
out.picked = drawn(pets, false);
TH.sel.cards.clear();

// Stacked unticked while statements are stacked: no total, as no count holds them. Then a board with nothing
// stacked keeps its total with Stacked unticked, as the parts still reach it
TH.config = { status_bar: true, status_counts: ['pets', 'placed', 'unplaced', 'loose', 'binned'] };
out.unticked = drawn(pets, false);
const flat = JSON.parse(JSON.stringify(pets));
flat.stacks = {};
out.flat = drawn(flat, false);
TH.config = { status_bar: true };

// a GETs board: two GETs, one holding a PET card and a sub-PET card, a participant note never a card, cards not
// placed and one set aside
const gets = {
  cards: {
    'Ana/g1': card('Bread as patience', { kind: 'pet' }), 'Ana/g1.1': card('Waiting on the rise', { kind: 'sub' }),
    'Ben/g2': card('A kitchen of one\'s own', { kind: 'pet' }), 'Ben/g2.1': card('The oven door', { kind: 'sub' }),
    'Cal/g3': card('Bread as a gift', { kind: 'pet' }), 'Cal/g4': card('Learning from video', { kind: 'pet' }),
    'Cal/g4.1': card('Pausing the screen', { kind: 'sub' }), 'Ana/n1': card('Spoke of her mother', { kind: 'pn' }),
  },
  groups: [
    { id: 'G1', label: 'Patience in the dough', members: ['Ana/g1', 'Ana/g1.1', 'Ana/n1'] },
    { id: 'G2', label: 'A place to bake', members: ['G3', 'Ben/g2'] },
    { id: 'G3', label: 'The oven as a threshold', members: ['Ben/g2.1'] },
  ],
  discarded: ['Cal/g4.1'],
};
out.gets = drawn(gets, true);

// an LPETs board, the same cards across timepoints
TH.lpets = true;
out.lpets = drawn(JSON.parse(JSON.stringify(gets)), true);
TH.lpets = false;
console.log(JSON.stringify(out));
"""

SUM = re.compile(r"^(\d+) (ES|cards?): (.*?)(\d+ (?:PET|GET|LPET)s?)(.*)$")


def _parts(text: str):
    """the bar's text read back: the total, its unit, each part's number, the theme count and what follows"""
    m = SUM.match(text)
    if not m:
        return None
    nums = [int(x) for x in re.findall(r"(\d+) [a-z]", m.group(3))]
    return int(m.group(1)), m.group(2), nums, m.group(4), m.group(5)


def test_status_counts_add_up(scratch):
    print("\n264. The boards' status bar counts: the total first, its parts adding to it, on PETs, GETs and LPETs "
          "boards (Adam, 26 October, wording C)")
    node = shutil.which("node")
    if not node:
        skip("264: the status bar's counts in node", "node is not installed")
        return
    js = support.text("apps/idiograph/static/themes.js")
    script = scratch / "status-counts-264.js"
    script.write_text(support.i18n_js() + STUBS + js + SCENARIO, encoding="utf-8")
    run = subprocess.run([node, str(script)], capture_output=True, text=True, encoding="utf-8", timeout=120)
    if run.returncode != 0:
        check("264: the status bar's counts run in node", False, run.stderr.strip()[:600])
        return
    o = json.loads(run.stdout)

    p = _parts(o["pets"]["text"])
    check("264: on a PETs board with sub-PETs, stacks in a PET, in Not placed and set aside, statements waiting, "
          "loose and set aside, the bar says the statements' total first, its parts adding to it and to every "
          "statement the board holds, a missing one not among them, then the PETs at the top level",
          p is not None and p[1] == "ES" and p[0] == sum(p[2]) == o["pets"]["real"] == 16 and p[3] == "2 PETs"
          and p[2] == [6, 5, 2, 2, 1] and o["pets"]["stats"][:1] == ["sum"],
          str(o["pets"]))
    q = _parts(o["picked"]["text"])
    check("264: a statement selected is said after the PETs, the total unchanged",
          q is not None and q[0] == p[0] and q[4] == "1 ES selected", str(o["picked"]))
    check("264: Stacked unticked while statements are stacked, no total shows, as no count holds them, and with "
          "nothing stacked the total stays, the parts shown still reaching it",
          o["unticked"]["text"].startswith("ES: ") and "stacked" not in o["unticked"]["text"]
          and (_parts(o["flat"]["text"]) or (0, "", [-1]))[0] == sum(_parts(o["flat"]["text"])[2]) == 16,
          str({k: o[k] for k in ("unticked", "flat")}))
    for name, word in (("gets", "GETs"), ("lpets", "LPETs")):
        g = _parts(o[name]["text"])
        check(f"264: on a{'n' if name == 'lpets' else ''} {word} board the unit is cards, a PET's card and a sub-PET's "
              f"alike, the total first and its parts adding to it and to the cards the board holds, a participant "
              f"note never one, and no stacked count",
              g is not None and g[1] == "cards" and g[0] == sum(g[2]) == o[name]["real"] == 7 and g[2] == [4, 1, 2]
              and f" in {word}," in o[name]["text"] and g[3] == f"2 {word}" and "stacked" not in o[name]["text"],
              str(o[name]))
