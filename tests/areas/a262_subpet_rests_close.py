"""Area 262: a sub-PET dragged close to the ones above it rests there (26 October 2026, Adam: in a PET he could
not move the last sub-PET up any closer to the sub-PETs above it. As he moved it the line under the sub-PET above
showed, then the others moved up out of its way, so the box ended no closer).

While a drag made way, every neighbour that came inside the margin of what was dragged was sent clear by the least
distance, which for the sub-PET above one coming up from below is up, and the drop's settle did the same, so the
gap never closed and the whole PET grew upward. And the insertion line showed from the first move, though the
drop changed no order. Now a PET, a sub-PET or a group dragged in its own place that meets its neighbours only by
a little (the shortest shift clearing it of them all TH_NEAR or less) stops a margin from them and lands there,
nothing else moving, and the line shows only when the drop changes the order or brings something in.

The checks run the page's own board code in node, the drag's own move and drop, on an invented board about a wet
weekend on the hill, with the quotes on cards off and on, and read what the page would save.
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
thPlayerDraw = () => {}; thPanelFollow = () => {}; thDrawSel = () => {}; thEase = () => {}; thSoon = () => {};
thMomentum = () => {}; thCorners = () => {}; thMapPlace = () => {}; thDrawCounts = () => {}; thTip = () => {};
thLean = () => {}; thSideArm = () => {}; thMergeShow = () => {}; thHover = () => {}; thAck = () => {};
thPlace = () => { thRoomFollow(); };
ELS['th-insert'] = new El('th-insert');
ELS['th-stage'] = new El('th-stage');
globalThis.performance = globalThis.performance || { now: () => 0 };
const card = (text, y) => ({ x: 40, y, text, time: '2:10', sheet: 'Initial' });
const board = () => ({
  cards: { a1: card('Rain on the tent', 100), b1: card('Mud on the boots', 240), c1: card('Fog on the ridge', 380),
           c2: card('A cold summit', 480), z: card('The drive home', 900) },
  groups: [{ id: 'P', label: 'Weather on the hill', members: ['A', 'B', 'C'], x: 0, y: 0 },
           { id: 'A', label: 'Rain', members: ['a1'], x: 0, y: 0 },
           { id: 'B', label: 'Mud', members: ['b1'], x: 0, y: 0 },
           { id: 'C', label: 'Fog', members: ['c1', 'c2'], x: 0, y: 0 }],
  discarded: [], stacks: {} });
let quotes = false;
const measure = () => {
  TH.sizes = {};
  for (const k of ['a1', 'b1', 'c1', 'c2', 'z']) TH.sizes[k] = { w: 200, h: 80 };
  for (const g of ['P', 'A', 'B', 'C']) TH.sizes[g] = { w: 140, h: 26 };
  TH.qfull = {}; TH.qextra = {}; TH.baseH = {};
  if (quotes) for (const k of ['a1', 'b1', 'c1']) { TH.qfull[k] = 120; TH.qextra[k] = 40; TH.sizes[k] = { w: 200, h: 120 }; }
};
thRender = () => { measure(); thStacksRoom(); TH.layout = thLayout(TH.v, thSize, null); };
const open = () => {
  TH.v = board(); TH.opened = new Set(); TH.shifts = []; TH.roomShown = null; TH.removed = new Set(); TH.undo = []; TH.redo = [];
  TH.live = true; TH.mode = 'pets'; TH.view = { x: 0, y: 0, z: 1 }; TH.stackable = true;
  TH.sel = { cards: new Set(), groups: new Set(), stickies: new Set() };
  TH.els = { cards: {}, under: {}, labels: {}, frames: {}, stickies: {}, rails: {} };
  thRender();
  // the PET in a column, a margin between its sub-PETs, and the last taken 120 further down
  thArrange(TH.v, 'P', thSize, 'column');
  for (const m of ['C', 'c1', 'c2']) { const o = thIsGroup(TH.v, m) ? thGroup(TH.v, m) : TH.v.cards[m]; o.y += 120; }
  TH.shifts = []; TH.roomShown = null;
  thRender();
};
const frames = (v = TH.v) => { const l = thLayout(v, thSize, null); return Object.fromEntries(['A', 'B', 'C', 'P'].map((g) => [g, [Math.round(l[g].frame.y), Math.round(l[g].frame.y + l[g].frame.h)]])); };
const saved = () => { const s = thUnshifted(TH.v).cards; return Object.fromEntries(Object.entries(s).map(([k, c]) => [k, [Math.round(c.x), Math.round(c.y)]])); };
// the drag as the page starts it on C's label, each move as the pointer gives it, and the drop
const drag = () => {
  TH.press = { item: { kind: 'group', id: 'C' }, x0: 100, y0: 100, add: false, alt: false };
  thDragStart();
  return TH.drag;
};
// where each frame goes as the drag makes way, read from the board under the slides
const move = (d, dy) => { thDragMove({ clientX: 100, clientY: 100 + dy, altKey: false }); const f = frames(); return { gap: f.C[0] - f.B[1], line: !ELS['th-insert'].hidden, dy: d.dy, B: f.B }; };
const out = {};
for (const q of [false, true]) {
  quotes = q;
  open();
  const file0 = saved(); const f0 = frames(); const gap0 = f0.C[0] - f0.B[1];
  const d = drag();
  const steps = [];
  for (let dy = 0; dy >= -(gap0 + 15); dy -= 5) steps.push(move(d, dy));
  thDragEnd({ clientX: 100, clientY: 100 - (gap0 + 15), altKey: false });
  const file1 = saved(); const f1 = frames();
  out[q ? 'on' : 'off'] = { gap0, f0, f1, file0, file1, steps, undo: TH.undo.length };
  // pulled well over the sub-PET above, which holds still since 31 October (design A)
  open();
  const e = drag();
  const far = move(e, -(gap0 + 60));
  thDragCancel();
  out[q ? 'onFar' : 'offFar'] = { far, f0: frames() };
  // pulled past the sub-PET above to read before it, the line shows
  open();
  const g = drag();
  const past = move(g, -(gap0 + 330));
  thDragCancel();
  out[q ? 'onPast' : 'offPast'] = past;
}
console.log(JSON.stringify(out));
})();
"""


def test_subpet_rests_close(scratch):
    print("\n262. A sub-PET dragged close to the ones above it rests a margin from them and nothing else moves, and the "
          "insertion line shows only when the drop changes the order (26 October)")
    node = shutil.which("node")
    if not node:
        skip("262: the board in node", "node is not installed")
        return
    js = support.text("apps/idiograph/static/themes.js")
    script = scratch / "subpet-rests-close-262.js"
    script.write_text(support.i18n_js() + STUBS + js + SCENARIO, encoding="utf-8")
    run = subprocess.run([node, str(script)], capture_output=True, text=True, encoding="utf-8", timeout=120)
    if run.returncode != 0:
        check("262: the board runs in node", False, run.stderr.strip()[:800])
        return
    o = json.loads(run.stdout)
    margin = 10
    for q in ("off", "on"):
        r = o[q]
        moved = sorted(k for k in r["file0"] if r["file1"][k] != r["file0"][k])
        dy = r["file1"]["c1"][1] - r["file0"]["c1"][1]
        check(f"262: quotes {q}, the last sub-PET dragged up close to the one above and let go rests a margin below it, "
              "its own statements moving by one and the same shift and no other statement moving in the file",
              moved == ["c1", "c2"] and r["file1"]["c2"][1] - r["file0"]["c2"][1] == dy
              and r["f1"]["C"][0] - r["f1"]["B"][1] == margin and r["f1"]["A"] == r["f0"]["A"]
              and r["f1"]["B"] == r["f0"]["B"] and r["undo"] == 1, json.dumps(r)[:900])
        check(f"262: quotes {q}, while it is dragged close the sub-PETs above never move, it never goes nearer than the "
              "margin, and no insertion line shows, since the order does not change",
              all(s["B"] == r["f0"]["B"] for s in r["steps"]) and min(s["gap"] for s in r["steps"]) == margin
              and not any(s["line"] for s in r["steps"]), json.dumps(r["steps"])[:900])
        far = o[q + "Far"]
        # since 31 October (design A, area 312) no PET or sub-PET moves out of the way while a drag lasts
        check(f"262: quotes {q}, pulled well over the sub-PET above it, that one holds still, and Esc puts it back",
              far["far"]["B"] == r["f0"]["B"] and far["f0"] == r["f0"], json.dumps(far)[:600])
        check(f"262: quotes {q}, pulled past the sub-PETs above to read before them, the insertion line shows",
              o[q + "Past"]["line"] is True, json.dumps(o[q + "Past"])[:600])
