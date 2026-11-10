"""Area 181: the minimap's box made visible (18 October, Adam's word of 11:50 on the corner card's shot).

The box showing which part of the transcript is on screen had become a faint wash of the ink with no
edge, which he could not see, where the ink outline before it showed at once where he was. Four looks
were drawn for him, and at 12:55 he chose two of them combined: A's solid ink line 2 pixels, near white
in dark, with D's dimming of the column outside the view, the card's paper over it at 35 per cent in
light and a little less in dark, at 25, `--dim` in tokens.css, the other three looks gone. The look is
measured from the tokens in both themes. The box is never under 12 pixels tall, three hours is drawn
finer than an hour, as his drawing of 17 October has it, and a card he opens by a press over the
transcript's words stands on a band where they fade out, as at 360 pixels. Every interview here is
invented, a beekeeper's.
"""
from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path

from . import support
from .support import check, skip


def test_minimap_box(scratch):
    print("\n181. The minimap's box made visible, 18 October, Adam's word that the wash with no edge could not be seen: "
          "his choice of A's solid ink line with D's dimming of the rest, a little less in dark, measured from the tokens, "
          "the box never under 12 pixels, three hours drawn finer than an hour, and a card opened by a press over the "
          "words standing on a band where they fade out. Since the test review of 18 October the look, its contrast, "
          "the box's least height and the blocks' grain are review shots, and the band that never fades a field he is "
          "writing in stays")
    app = support.text("family/static/shell.js", "apps/idiograph/static/distil.js")
    node = shutil.which("node")

    def whole(name):
        """A function of app.js whole, or "" when there is none."""
        if f"function {name}(" not in app:
            return ""
        at = app.index(f"function {name}(")
        return app[at:app.index("\n}", at) + 2]

    # ── a card opened by a press over the words stands on a band where they fade out, never over a field he is
    # writing in
    if not node:
        skip("181: the band in node", "node is not installed")
    else:
        script = scratch / "minimap-181-band.js"
        script.write_text(r"""
const box4 = (left, top, right, bottom) => ({ left, top, right, bottom, width: right - left, height: bottom - top });
const els = {};
const $ = (id) => els[id];
const document = { activeElement: null, body: {} };
let WORDS = [];
const asked = [];
const FOCUSED = [];
// 360 wide: the column from 173 to 728 down the window, the card 135 by 300 at its bottom right
els['transcript-rows'] = { querySelector: (sel) => { asked.push(sel); return { querySelectorAll: (s) => { asked.push(s); return WORDS.map((r) => ({ getBoundingClientRect: () => r })); } }; } };
els.transcript = { scrollTop: 500, getBoundingClientRect: () => box4(16, 173, 344, 728), contains: (el) => FOCUSED.includes(el) };
els['minimap-card'] = { getBoundingClientRect: () => box4(159, 422, 294, 722) };
const S = { mm: { rows: [[0, 600], [600, 120], [720, 160], [880, 300], [1180, 200], [1380, 400]].map(([top, height], i) => ({ i, top, height })) } };
""" + whole("minimapOver") + "\n" + whole("minimapBand") + r"""
const out = {};
WORDS = [box4(72, 430, 328, 470)]; out.crossing = minimapBand(); out.asked = asked.filter((s) => s.startsWith('.turn['));
out.parts = [...new Set(asked.filter((s) => !s.startsWith('.turn[')))];
WORDS = [box4(72, 300, 150, 340)]; out.clear = minimapBand();
WORDS = [box4(72, 430, 328, 470)];
const field = { tagName: 'TEXTAREA', getBoundingClientRect: () => box4(30, 380, 300, 420) };
FOCUSED.push(field); document.activeElement = field; out.writingLow = minimapBand();
const high = { tagName: 'TEXTAREA', getBoundingClientRect: () => box4(30, 200, 300, 260) };
FOCUSED.length = 0; FOCUSED.push(high); document.activeElement = high; out.writingHigh = minimapBand();
FOCUSED.length = 0; document.activeElement = { tagName: 'BUTTON', getBoundingClientRect: () => box4(298, 690, 330, 722) }; out.button = minimapBand();
document.activeElement = null; S.mm = null; out.none = minimapBand();
console.log(JSON.stringify(out));
""", encoding="utf-8")
        run = subprocess.run([node, str(script)], capture_output=True, text=True, encoding="utf-8", timeout=60)
        got = json.loads(run.stdout) if run.returncode == 0 and run.stdout.strip() else {}
        check("181: in node, at 360 the band runs from the column's foot to 12 pixels above the card, 318 pixels, where "
              "the words of a passage level with the card stand under it, only the passages level with it read, their "
              "words, a box open for correction and a quote being built, none where the words are clear of the card, none "
              "while a field he is writing in would reach into the band, so it never fades, one higher up or the map "
              "button in focus leaving it, and none with no map drawn",
              got.get("crossing") == "318px" and got.get("asked") == ['.turn[data-i="2"]', '.turn[data-i="3"]']
              and got.get("parts") == [".turn-text, .turn-edit, .quote-preview"] and got.get("clear") == ""
              and got.get("writingLow") == "" and got.get("writingHigh") == "318px" and got.get("button") == "318px"
              and got.get("none") == "", run.stdout.strip()[:300] or run.stderr.strip()[:300])
