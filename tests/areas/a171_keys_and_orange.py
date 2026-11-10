from __future__ import annotations

import json
import shutil
import subprocess

from . import support
from .support import check, skip


def test_keys_and_orange(scratch):
    print("\n171. Keys in capitals, as keyboards and the Mac's and Windows' menus print them, the last of the orange "
          "out of its places, a drag kept off the title bar, a theme's title clear of the cards round it, and area "
          "55's label sizes measured again. Since the test review of 18 October the keys' capitals, the orange and the "
          "labels' sizes are review shots, and the board making room for a theme's title stays")
    themes_js = support.text("apps/idiograph/static/themes.js")
    node = shutil.which("node")

    # ── D. a theme's title clear of the cards round it
    if not node:
        skip("171: the room made in node", "node is not on this machine")
    else:
        script = scratch / "room-171.js"
        script.write_text(support.i18n_js() + themes_js + r"""
const tall = {};
const size = (item) => (item.startsWith('g') ? { w: 300, h: tall[item] || 30 } : { w: 200, h: 80 });
const card = (x, y) => ({ x, y, text: 't' });
const keep = (x) => JSON.parse(JSON.stringify(x));
const out = {};
{
  // a card clear of a theme's title until a mark takes the title onto a second line, a pick
  const v = { cards: { 'a:1:0': card(0, 200), 'a:2:0': card(210, 200), 'c:1:0': card(0, 60), 'c:2:0': card(700, 700) },
    groups: [], discarded: [], picks: {} };
  const G = thMakeGroup(v, ['a:1:0', 'a:2:0'], 'A title one mark from a second line');
  out.before = thClashes(v, size).length;
  const was = thLabelBoxes(thLayout(v, size, null));
  thTogglePick(v, G, 'a:1:0');
  tall[G] = 53;
  out.grown = thClashes(v, size).length;
  out.settled = thSettle(v, size, [], was, [G]);
  out.after = [thClashes(v, size).length, keep(v.cards['a:1:0']), thParents(v)['c:1:0'] === undefined];
}
{
  // a hand's or another computer's board: a card on a theme's title, made room for, and two cards on each other on the
  // canvas, made room for as a drop there makes it since 31 October (agentoverlap, area 309): the one that reads first
  // stays
  const v = { cards: { 'a:1:0': card(0, 200), 'a:2:0': card(210, 200), 'c:1:0': card(40, 150), 'd:1:0': card(700, 0),
    'd:2:0': card(760, 30) }, groups: [], discarded: [], picks: {} };
  const G = thMakeGroup(v, ['a:1:0', 'a:2:0'], 'G');
  tall[G] = 30;
  const members = keep([v.cards['a:1:0'], v.cards['a:2:0']]);
  out.clashes = thClashes(v, size).map((p) => p.join(' '));
  out.made = thMakeRoom(v, size);
  out.room = [thClashes(v, size).map((p) => p.join(' ')), JSON.stringify(keep([v.cards['a:1:0'], v.cards['a:2:0']])) === JSON.stringify(members),
    thParents(v)['c:1:0'] === undefined, keep(thGroup(v, G).members), keep(v.cards['d:1:0'])];
  out.again = thMakeRoom(v, size);
}
console.log(JSON.stringify(out));
""", encoding="utf-8")
        run = subprocess.run([node, str(script)], capture_output=True, text=True, encoding="utf-8", timeout=60)
        o = json.loads(run.stdout.strip().splitlines()[-1]) if run.returncode == 0 and run.stdout.strip() else {}
        check("171: in node, a label a pick takes onto a second line grows up onto the card above it, and the settle a "
              "pick now runs sends the card clear, the theme and its cards where they were, the card in no PET still",
              o.get("before") == 0 and o.get("grown", 0) > 0 and o.get("settled") is True
              and o.get("after") == [0, {"x": 0, "y": 200, "text": "t"}, True], (run.stdout + run.stderr)[:400])
        check("171: in node, a board with a card on a theme's title makes room, the card off the title, the theme's own "
              "cards and members as they were, the card never joining it, two cards on each other made room for, the one "
              "that reads first where it was (since 31 October, area 309), and a second pass finds nothing to move",
              o.get("clashes") == ["g1 c:1:0", "d:1:0 d:2:0"] and o.get("made") is True
              and o.get("room") == [[], True, True, ["a:1:0", "a:2:0"], {"x": 700, "y": 0, "text": "t"}]
              and o.get("again") is False,
              (run.stdout + run.stderr)[:400])

