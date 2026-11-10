from __future__ import annotations

import json
import shutil
import subprocess

from . import support
from .support import check, skip


def test_polish_eight(scratch):
    print("\n182. Polish after Adam's look at the night's builds, 18 October: the exploratory notes field about five "
          "lines tall and growing with a long note, the Columns picker, the selection toolbar and the Columns menu, the "
          "board map's pressed button, its view box cut at the map's edge and a small board fitted to the map, a new "
          "sticky note placed clear of every card, and Search named on the bars. Since the test review of 18 October the "
          "heights, widths and places are review shots, and the sticky note kept clear of the cards stays")
    themes_js = support.text("apps/idiograph/static/themes.js")
    node = shutil.which("node")

    def run_node(name, code):
        script = scratch / name
        script.write_text(support.i18n_js() + code, encoding="utf-8")
        done = subprocess.run([node, str(script)], capture_output=True, text=True, encoding="utf-8", timeout=120)
        try:
            return json.loads(done.stdout) if done.returncode == 0 and done.stdout.strip() else {}, done
        except ValueError:
            return {}, done

    # ── 4. a new sticky note placed clear of every card, with room for its words
    if not node:
        skip("182: a new sticky note in node", "node is not on this machine")
    else:
        code = r"""
const $ = () => null; const esc = (s) => String(s); const escAttr = esc; const say = () => {};
globalThis.window = { innerWidth: 1280, innerHeight: 800, matchMedia: () => ({ matches: false }) };
globalThis.localStorage = { getItem: () => null, setItem: () => {} };
""" + themes_js + r"""
const out = {};
const card = (x, y) => ({ text: 'Counting the lengths', time: '00:10', x, y });
// a card at the top left and one under it, 120 pixels down, and a note made between them, its words still empty
const v = { cards: { 'a:1:0': card(0, 0), 'a:2:0': card(0, 200) }, groups: [], discarded: [], picks: {}, stickies: [], ai: { discarded: {} } };
TH.v = v; TH.sizes = {};
const id = thStickyMake(v, 0, 100, null);
TH.sizes[id] = { w: 64, h: 47 };
out.room = thStickyRoom(id)(id);
out.other = thStickyRoom(id)('a:1:0');
out.before = thStickyOver(v, id);
// settled with its own size it stays, since the margin is clear above and below, and with its room it moves
const was = thLabelBoxes(thLayout(v, thSize, null));
const plain = JSON.parse(JSON.stringify(v));
thSettle(plain, thSize, [id], was, []);
out.plainStays = [plain.stickies[0].x, plain.stickies[0].y];
thSettle(v, thStickyRoom(id), [id], was, []);
const n = v.stickies[0];
const roomBox = { x: n.x, y: n.y, w: 160, h: 47 + 63 };
out.clear = Object.values(v.cards).every((c) => !thMeets(roomBox, { x: c.x, y: c.y, w: 200, h: 80 }));
out.cardsStill = [v.cards['a:1:0'].y, v.cards['a:2:0'].y];
// his words grow it past its room over a card: it lies over it, and settled again it is clear
n.x = 0; n.y = 100; TH.sizes[id] = { w: 160, h: 140 };
out.grown = thStickyOver(v, id);
thSettle(v, thStickyRoom(id), [id], was, []);
out.grownClear = !thStickyOver(v, id) && Object.values(v.cards).every((c) => !thMeets({ x: n.x, y: n.y, w: 160, h: 140 }, { x: c.x, y: c.y, w: 200, h: 80 }));
out.cardsStill2 = [v.cards['a:1:0'].y, v.cards['a:2:0'].y];
// a note inside a PET meets a card of the canvas outside it never, only what stands inside its PET
const g = thMakeGroup(v, ['a:1:0'], 'Floating at last');
n.in = g; n.x = 0; n.y = 220; TH.sizes[id] = { w: 160, h: 47 };
out.apart = thStickyOver(v, id);
out.gone = thStickyOver(v, 'n99');
console.log(JSON.stringify(out));
"""
        o, done = run_node("sticky-182.js", code)
        check("182: in node, a new note's room is 160 wide and three lines of 21 pixels taller, every other size its own, "
              "a note made between two cards lies over neither, its own size leaving it where it is made and its room "
              "moving it clear of both with the cards where they stood",
              o.get("room") == {"w": 160, "h": 110} and o.get("other") == {"w": 200, "h": 80} and o.get("before") is False
              and o.get("plainStays") == [0, 100] and o.get("clear") is True and o.get("cardsStill") == [0, 200],
              (done.stdout + done.stderr)[:400])
        check("182: in node, words grown past the room over a card make it lie over that card, settling again takes the "
              "note alone clear, and a note in a PET or one not there meets nothing outside",
              o.get("grown") is True and o.get("grownClear") is True and o.get("cardsStill2") == [0, 200]
              and o.get("apart") is False and o.get("gone") is False, (done.stdout + done.stderr)[:400])
