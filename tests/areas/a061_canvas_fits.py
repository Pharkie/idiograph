from __future__ import annotations

import json
import shutil

from . import support
from .support import check, skip


def test_canvas_fits(scratch):
    print("\n61. The PETs canvas fitted closer: a note sized to its words (148), its colour in one click (149), "
          "Merge and one nest rule from every side (150, gone on 18 October for the title strip, area 188), and the count "
          "as a badge on the frame (151)")
    import subprocess

    js = support.text("apps/idiograph/static/themes.js")
    fn = lambda src, name: src.split(f"function {name}(", 1)[1].split("\n}", 1)[0]

    # ── B. 149, the colour in one click
    check("149: one click on a paper recolours the note, one step of undo, and the press never starts a drag or a lasso",
          "if (paper) { thStickyRecolour(paper.closest('.th-sticky').dataset.sticky, paper.dataset.colour); return; }" in js
          and "if (e.target.closest('.th-del, .th-arr, .th-more, .th-sticky-del, .th-strip, .th-stackn, .th-restack, .gt-unfold')) return;" in fn(js, "thPointerDown")
          and "thDone(before, t('themes.step.recoloured_sticky'));" in fn(js, "thStickyRecolour"))

    # ── C. 150, Merge and the one rule from every side went on 18 October: a drop merges only on a theme's title
    # strip, which says "Merge into" and the title, and a drop in a body only moves (area 188)


    # ── E. the model in node
    node = shutil.which("node")
    if node:
        script = scratch / "canvas-fits-model.js"
        script.write_text(support.i18n_js() + """
globalThis.$ = () => null;
globalThis.esc = (s) => String(s).replace(/[&<>]/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;' }[c]));
globalThis.escAttr = (s) => esc(s).replace(/"/g, '&quot;');
globalThis.say = () => {};
""" + js + r"""
const keep = (x) => JSON.parse(JSON.stringify(x));
const card = (x, y) => ({ x, y, text: 'A', time: '00:01' });
const out = {};
// two PETs side by side, and a third holding a sub-theme at its own bottom-left corner
const v = { cards: { 'a:1:0': card(0, 0), 'a:2:0': card(220, 0), 'a:3:0': card(0, 100), 'a:4:0': card(1000, 0),
  'a:5:0': card(1000, 100), 'a:6:0': card(2000, 100), 'a:7:0': card(2220, 0) }, groups: [], discarded: [], picks: {}, stickies: [] };
const one = thMakeGroup(v, ['a:1:0', 'a:2:0', 'a:3:0'], 'Theme 1');
const two = thMakeGroup(v, ['a:4:0', 'a:5:0'], 'Theme 2');
const size = (item) => (item.startsWith('g') ? { w: 120, h: 30 } : item.startsWith('n') ? { w: 80, h: 47 } : { w: 200, h: 80 });
let lay = thLayout(v, size, null);
const f = lay[one].frame;
const m = TH_MARGIN;
const three = thMakeGroup(v, ['a:6:0'], 'Inner');
const four = thMakeGroup(v, [three, 'a:7:0'], 'Outer');
lay = thLayout(v, size, null);
out.badges = [thBadgeText(v, one), thBadgeText(v, four), thBadgeText(v, three)];
// a PET whose one statement is discarded holds none, and its badge says 0
v.cards['a:8:0'] = card(3000, 0);
const zero = thMakeGroup(v, ['a:8:0'], 'Zero');
v.discarded.push('a:8:0');
out.zero = thBadgeText(v, zero);
const spots = thBadgeSpots(v, lay, { [one]: 20, [three]: 20, [four]: 20, [two]: 20 });
const s3 = lay[three].frame.x + spots[three];
const s4 = lay[four].frame.x + spots[four];
out.spots = [spots[one], spots[two], spots[three], s4 >= s3 + 20 + 4, lay[four].frame.y + lay[four].frame.h - (lay[three].frame.y + lay[three].frame.h)];
// the spacing reads the measured size: a note 80px wide beside a card leaves the margin, one taken as 160 would not
const w = { cards: { 'b:1:0': card(0, 0) }, groups: [], discarded: [], picks: {}, stickies: [{ id: 'n1', text: 'Yeah this needs a look', colour: 'yellow', x: -90, y: 0 }] };
const small = (item) => (item.startsWith('n') ? { w: 80, h: 47 } : { w: 200, h: 80 });
const wide = (item) => (item.startsWith('n') ? { w: 160, h: 140 } : { w: 200, h: 80 });
out.measured = [thClashes(w, small).length, thClashes(w, wide).length];
out.strip = thStripHtml({ id: 'n1', colour: 'green' });
console.log(JSON.stringify(out));
""", encoding="utf-8")
        run = subprocess.run([node, str(script)], capture_output=True, text=True, encoding="utf-8")
        if run.returncode != 0:
            check("151: the canvas's model runs in node", False, run.stderr.strip()[:300])
        else:
            out = json.loads(run.stdout)
            check("151: in node, the badge counts the statements at any depth, and 0 for a PET with none",
                  out["badges"] == ["3", "2", "1"] and out["zero"] == "0", f"{out['badges']} {out['zero']}")
            check("148: in node, the spacing takes the note's measured size, a small slip clear where a 160px square would clash",
                  out["measured"] == [0, 1], str(out["measured"]))
    else:
        skip("148 to 151: the canvas's model in node", "no node on this machine")
