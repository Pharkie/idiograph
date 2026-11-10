"""Area 202: a reorder closes the gap a taller sub-PET leaves, and the status bar's counts menu opens clear of
the bar (polish 11, 19 October 2026).

The shared `themes.reorder`, run by an agent's `order` op and by the Table view through the server's route,
set a taller sub-PET in a shorter one's place and left the shorter one's old height as a gap under the one
that moved up, the rows below pushed down past it. Now each row keeps the gap it had under the rows above it,
so what is below moves up where a shorter one took a taller one's place, and the layout is otherwise kept.
The status bar's right-click menu put its foot at the pointer, so a click in the bar's middle left it about
14 pixels over the bar. It now opens above the bar, clear of it, at any height on the bar.

The checks hold behaviour, on an invented board about learning to bake bread at home: the places a reorder
gives, through both callers, and where the menu stands, in node. No string, colour or pixel of the page is
pinned.
"""
from __future__ import annotations

import json
import re
import shutil
import subprocess

from . import support
from .support import check, skip
import idiograph_routes

# PET g1 holding a tall sub-PET g2 of three statements, a short one g3 of one under it, and a statement of its
# own at the foot, with PET g5 beside it
CARDS = {
    "Initial:3:0": (40, 120, "Burning the first loaf"),
    "Initial:5:0": (40, 240, "Reading the recipe three times"),
    "Initial:7:0": (40, 360, "Flour on every surface"),
    "Initial:9:0": (40, 560, "The smell of the oven at six"),
    "Initial:11:0": (40, 760, "Sharing a loaf with the neighbours"),
    "Initial:13:0": (700, 120, "A starter kept alive for a year"),
}
GROUPS = [
    {"id": "g1", "label": "Learning to bake at home", "members": ["g2", "g3", "Initial:11:0"], "x": 20, "y": 20},
    {"id": "g2", "label": "Getting it wrong", "members": ["Initial:3:0", "Initial:5:0", "Initial:7:0"], "x": 40, "y": 80},
    {"id": "g3", "label": "Mornings", "members": ["Initial:9:0"], "x": 40, "y": 520},
    {"id": "g5", "label": "Keeping something going", "members": ["Initial:13:0"], "x": 700, "y": 40},
]


def test_reorder_gap_and_status_menu(scratch):
    print("\n202. A reorder under a label closes the gap a taller sub-PET leaves, through an agent's order op and the "
          "Table view's route alike, and the status bar's counts menu opens above the bar (polish 11, 19 October)")
    import server as server_mod
    import themes

    board = {"id": "v1", "name": "Board 1", "note": "", "discarded": [], "picks": {}, "notes": [],
             "cards": {k: {"x": x, "y": y, "text": t} for k, (x, y, t) in CARDS.items()},
             "groups": json.loads(json.dumps(GROUPS))}
    tall = {k: 80 for k in CARDS}
    height = lambda k, _t: tall[k]
    first = themes.layout_boxes(themes.normalise(json.loads(json.dumps(board))), height)
    v, info = themes.reorder(json.loads(json.dumps(board)), "g1", ["g3", "g2"], height=height)
    after = themes.layout_boxes(v, height)
    f0, f1 = first["frames"], after["frames"]
    gap0 = f0["g3"][1] - (f0["g2"][1] + f0["g2"][3])
    gap1 = f1["g2"][1] - (f1["g3"][1] + f1["g3"][3])
    own0 = first["cards"]["Initial:11:0"][1] - (f0["g3"][1] + f0["g3"][3])
    own1 = after["cards"]["Initial:11:0"][1] - (f1["g2"][1] + f1["g2"][3])
    check("202: the short sub-PET set before the tall one takes its place at the top, the tall one stands under it with "
          "the gap the two had, no more, and the PET's own statement below keeps its gap too, so nothing is left empty",
          info["order"] == ["g3", "g2", "Initial:11:0"] and f1["g3"][1] == f0["g2"][1] and gap1 == gap0
          and own1 == own0 and f1["g1"][3] == f0["g1"][3], f"{f0} {f1} {gap0} {gap1} {own0} {own1}")
    check("202: the PET beside it and its statement do not move", f1["g5"] == f0["g5"]
          and after["cards"]["Initial:13:0"] == first["cards"]["Initial:13:0"], f"{f0['g5']} {f1['g5']}")
    back, _ = themes.reorder(json.loads(json.dumps(v)), "g1", ["g2", "g3"], height=height)
    check("202: set back in the first order, every card and label stands where it began",
          {k: (c["x"], c["y"]) for k, c in back["cards"].items()} == {k: (x, y) for k, (x, y, _t) in CARDS.items()}
          and themes.layout_boxes(back, height)["frames"] == f0,
          str({k: (c["x"], c["y"]) for k, c in back["cards"].items()}))
    got = idiograph_routes.api_board_order({"version": json.loads(json.dumps(board)), "under": "g1", "items": ["g3", "g2"],
                                      "heights": tall})
    check("202: the Table view's route lands every card and label where the agents' order op does",
          {k: (a["x"], a["y"]) for k, a in got["cards"].items()} == {k: (c["x"], c["y"]) for k, c in v["cards"].items()}
          and {k: (a["x"], a["y"]) for k, a in got["groups"].items()} == {g["id"]: (g["x"], g["y"]) for g in v["groups"]},
          json.dumps(got)[:400])

    # ── in node: where the counts menu stands for a right click high, in the middle and low on the bar
    node = shutil.which("node")
    if not node:
        skip("202: the status bar's menu in node", "node is not installed")
        return
    js = support.text("apps/idiograph/static/themes.js")
    parts = [re.search(r"\nfunction thStatusMenu\(open, x, y\) \{.*?\n\}\n", js, re.S),
             re.search(r"\nconst TH_SMENU_GAP = .*?\nfunction thStatusMenuSpot\(.*?\n\}\n", js, re.S)]
    if not all(parts):
        check("202: the status bar's menu code is found in themes.js", False, "")
        return
    script = scratch / "status-menu-202.js"
    script.write_text(MENU_STUBS + "".join(p.group(0) for p in parts) + MENU_SCENARIO, encoding="utf-8")
    run = subprocess.run([node, str(script)], capture_output=True, text=True, encoding="utf-8", timeout=60)
    if run.returncode != 0:
        check("202: the status bar's menu runs in node", False, run.stderr.strip()[:600])
        return
    o = json.loads(run.stdout)
    bar_top = 770
    check("202: in node, a right click anywhere on the bar, near its top, in its middle or near its foot, opens the "
          "menu with its foot above the bar's top, clear of the bar, at the same height each time",
          len({s["top"] for s in o["spots"]}) == 1 and all(s["top"] + 120 < bar_top for s in o["spots"]), str(o))
    check("202: in node, the menu's left is at the pointer and held inside the window near its right edge",
          o["spots"][0]["left"] == 300 and o["edge"]["left"] == 1280 - 180 - 8, str(o))


MENU_STUBS = r"""
const TH = {};
const menu = { hidden: true, offsetWidth: 180, offsetHeight: 120, style: {} };
const bar = { getBoundingClientRect: () => ({ top: 770, bottom: 800, left: 0, right: 1280 }) };
const $ = (id) => (id === 'th-smenu' ? menu : id === 'th-status' ? bar : null);
const thStatusMenuDraw = () => {};
globalThis.window = { innerWidth: 1280, innerHeight: 800 };
"""

MENU_SCENARIO = r"""
const spots = [];
for (const y of [772, 785, 798]) {
  thStatusMenu(true, 300, y);
  spots.push({ top: parseFloat(menu.style.top), left: parseFloat(menu.style.left) });
}
thStatusMenu(true, 1270, 785);
const edge = { left: parseFloat(menu.style.left) };
console.log(JSON.stringify({ spots, edge }));
"""
