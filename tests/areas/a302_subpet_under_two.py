"""Area 302: a sub-PET under two side by side rests a margin under the lower of them (30 October 2026, Adam: in a PET
with two sub-PETs side by side and a third below them, about 190 pixels stayed between the two and the third, and
dragging the third up kept that gap, so it would go no closer).

The history that made the board, all through agents' ops: one sub-PET moved out of the PET into another and back,
which put it in under what the PET held, then an order of the PET's statements and sub-PETs and orders inside two
sub-PETs. The agents' order sets the third in the row under the two, a margin under the lower. The fault was the
view's room: with the quotes shown on cards in both sub-PETs above, the page moved what stood below them down by the
first one's growth and then again by the second's, their sum, where it needs only the larger. So the third stood a
gap below them that the board does not hold, and every drop a margin from them in the view landed nearer than the
margin where the file keeps the board, so the drop sent the two up the board out of its way and the gap came back.
Now what stands below two or more that grew moves as far as the one that asks most, and keeps the gap the file gives
it under each.

The checks run the agents' path as `board apply` runs it, `themes.land_kept` for the moves and `themes.reorder` for
the orders, on an invented board about learning to swim as an adult, then hand the board it leaves to the page's own
board code in node, the drag's own move and drop, with the quotes on cards off and on, and read what the page would
save.
"""
from __future__ import annotations

import json
import shutil
import subprocess

from . import support
from .support import check, skip
from .a205_card_quotes_and_by_participant import STUBS

TEXTS = {
    "Initial:3:0": "Standing at the shallow end for an hour", "Initial:5:0": "The smell of chlorine on the bus home",
    "Initial:7:0": "Telling nobody at work", "Initial:9:0": "Swallowing half the pool",
    "Initial:9:1": "Coughing at the wall", "Initial:9:2": "Laughing it off", "Initial:11:0": "Going back the next week",
    "Initial:11:1": "Not telling her sister", "Initial:13:0": "Counting tiles on the bottom",
    "Initial:15:0": "Lessons on a Tuesday night", "Initial:15:1": "The teacher who never shouted",
    "Initial:17:0": "Kicking with a float", "Initial:19:0": "Lying back and the water holding her",
    "Initial:19:1": "Floating at last", "Initial:21:0": "Eyes on her from the gallery",
    "Initial:21:1": "Wanting the deep end empty", "Initial:23:0": "The lifeguard's chair",
}
# PET g2: three statements of its own over three sub-PETs side by side, g8 holding a stack of four under one card,
# PET g3 beside it, with a sub-PET of its own
SPOTS = {"Initial:3:0": (40, 100), "Initial:5:0": (40, 200), "Initial:7:0": (40, 300),
         "Initial:9:0": (40, 480), "Initial:13:0": (40, 580),
         "Initial:15:0": (300, 480), "Initial:15:1": (300, 580), "Initial:17:0": (300, 680),
         "Initial:19:0": (560, 480), "Initial:19:1": (560, 580),
         "Initial:21:0": (1100, 100), "Initial:21:1": (1100, 200), "Initial:23:0": (1100, 380)}
GROUPS = [
    {"id": "g2", "label": "Learning to swim at forty", "members": ["Initial:3:0", "Initial:5:0", "Initial:7:0", "g8", "g7", "g9"]},
    {"id": "g8", "label": "The first length", "members": ["Initial:9:0", "Initial:13:0"]},
    {"id": "g7", "label": "Lessons on a Tuesday", "members": ["Initial:15:0", "Initial:15:1", "Initial:17:0"]},
    {"id": "g9", "label": "Floating at last", "members": ["Initial:19:0", "Initial:19:1"]},
    {"id": "g3", "label": "Being watched", "members": ["Initial:21:0", "Initial:21:1", "g4"]},
    {"id": "g4", "label": "The lifeguard's chair", "members": ["Initial:23:0"]},
]
STACK = {"Initial:9:0": ["Initial:9:1", "Initial:9:2", "Initial:11:0", "Initial:11:1"]}

SCENARIO = r"""
(() => {
thPlayerDraw = () => {}; thPanelFollow = () => {}; thDrawSel = () => {}; thEase = () => {}; thSoon = () => {};
thMomentum = () => {}; thCorners = () => {}; thMapPlace = () => {}; thDrawCounts = () => {}; thTip = () => {};
thLean = () => {}; thSideArm = () => {}; thMergeShow = () => {}; thHover = () => {}; thAck = () => {};
// a drop's own placing makes the room again, as the page's thPlace does when no drag is under way
thPlace = (drag) => { if (!drag) thRoomFollow(); };
ELS['th-insert'] = new El('th-insert');
ELS['th-stage'] = new El('th-stage');
globalThis.performance = globalThis.performance || { now: () => 0 };
let quotes = false;
// every size as the server estimates it, so the page's layout here is the agents' layout, and with the quotes
// shown a card in each of the two sub-PETs above stands 60 taller
const measure = () => {
  TH.sizes = {};
  for (const [k, s] of Object.entries(SIZES)) TH.sizes[k] = { w: s[0], h: s[1] };
  TH.qfull = {}; TH.qextra = {}; TH.baseH = {};
  if (quotes) for (const k of ['Initial:9:0', 'Initial:15:0']) { TH.qfull[k] = TH.sizes[k].h + 60; TH.qextra[k] = 60; TH.sizes[k] = { w: TH.sizes[k].w, h: TH.qfull[k] }; }
};
thRender = () => { measure(); thStacksRoom(); TH.layout = thLayout(TH.v, thSize, null); };
const open = (board) => {
  TH.v = JSON.parse(JSON.stringify(board)); TH.opened = new Set(); TH.shifts = []; TH.roomShown = null; TH.removed = new Set();
  TH.undo = []; TH.redo = []; TH.live = true; TH.mode = 'pets'; TH.view = { x: 0, y: 0, z: 1 }; TH.stackable = true;
  TH.sel = { cards: new Set(), groups: new Set(), stickies: new Set() };
  TH.els = { cards: {}, under: {}, labels: {}, frames: {}, stickies: {}, rails: {} };
  thRender();
};
const IDS = ['g2', 'g8', 'g7', 'g9'];
const shown = () => Object.fromEntries(IDS.map((g) => { const f = TH.layout[g].frame; return [g, [Math.round(f.x), Math.round(f.y), Math.round(f.x + f.w), Math.round(f.y + f.h)]]; }));
const saved = () => { const s = thUnshifted(TH.v); return { cards: Object.fromEntries(Object.entries(s.cards).map(([k, c]) => [k, [Math.round(c.x), Math.round(c.y)]])), groups: Object.fromEntries(s.groups.map((g) => [g.id, [g.x, g.y]])) }; };
const filed = () => { const s = thUnshifted(TH.v); const l = thLayout(Object.assign({}, TH.v, { cards: s.cards, groups: s.groups }), thBaseSize, null);
  return Object.fromEntries(IDS.map((g) => [g, [Math.round(l[g].frame.y), Math.round(l[g].frame.y + l[g].frame.h)]])); };
// the drag as the page starts it on g9's title, each move as the pointer gives it, and the drop
const drag = (dx, dy, untilRest = false) => {
  TH.press = { item: { kind: 'group', id: 'g9' }, x0: 100, y0: 100, add: false, alt: false };
  thDragStart();
  const d = TH.drag;
  const n = Math.max(1, Math.ceil(Math.max(Math.abs(dx), Math.abs(dy)) / 5));
  let x = 100;
  let y = 100;
  let rest = 0;
  for (let i = 1; i <= n; i += 1) {
    x = 100 + Math.round((dx * i) / n);
    y = 100 + Math.round((dy * i) / n);
    thDragMove({ clientX: x, clientY: y, altKey: false });
    // a little way into the rest and let go there, as a hand stops when the box stops
    if (untilRest && d.free && Math.abs(d.free.dy - d.dy) > 0.5 && (rest += 1) >= 3) break;
  }
  thDragEnd({ clientX: x, clientY: y, altKey: false });
  thPlace();
  TH.layout = thLayout(TH.v, thSize, null);
};
const gapOf = (f) => f.g9[1] - Math.max(f.g8[3], f.g7[3]);
const out = {};
for (const q of [false, true]) {
  quotes = q;
  const r = {};
  // the board as the agents' ops left it, opened
  open(BOARD);
  r.open = shown(); r.openFile = filed(); r.openGap = gapOf(r.open);
  // moved under both and down, as his own moves on the canvas might leave it
  drag(360, 190);
  r.lowered = shown(); r.loweredGap = gapOf(r.lowered);
  const before = saved();
  const undo0 = TH.undo.length;
  // dragged up until it rests, and let go
  drag(0, -400, true);
  r.drop = shown(); r.dropFile = filed(); r.dropGap = gapOf(r.drop); r.undo = TH.undo.length - undo0;
  const after = saved();
  r.moved = Object.keys(after.cards).filter((k) => JSON.stringify(after.cards[k]) !== JSON.stringify(before.cards[k])).sort();
  r.g9dy = after.cards['Initial:19:0'][1] - before.cards['Initial:19:0'][1];
  r.g9own = after.cards['Initial:19:1'][1] - before.cards['Initial:19:1'][1];
  // and once more, as he tried again
  drag(0, -400, true);
  const again = saved();
  r.againMoved = Object.keys(again.cards).filter((k) => JSON.stringify(again.cards[k]) !== JSON.stringify(after.cards[k])).sort();
  r.again = shown();
  // the board as that drop saved it, opened afresh
  const kept = JSON.parse(JSON.stringify(TH.v));
  const s = thUnshifted(TH.v);
  kept.cards = s.cards; kept.groups = s.groups;
  open(kept);
  r.reopen = shown(); r.reopenFile = filed(); r.reopenGap = gapOf(r.reopen);
  r.saved = saved();
  out[q ? 'on' : 'off'] = r;
}
console.log(JSON.stringify(out));
})();
"""


def _agents_board():
    """The board the history leaves, through the agents' path: each move a change of what holds what landed as
    `board apply` lands one (`land_kept`, strict), then the orders (`reorder`)."""
    import themes

    board = {"id": "v1", "name": "Board 1", "note": "", "discarded": [], "picks": {}, "stacks": json.loads(json.dumps(STACK)),
             "cards": {k: {"x": SPOTS.get(k, (0, 0))[0], "y": SPOTS.get(k, (0, 0))[1], "text": t} for k, t in TEXTS.items()},
             "groups": [dict(g, members=list(g["members"]), x=0, y=0) for g in GROUPS]}
    v = themes.normalise(json.loads(json.dumps(board)))
    themes.sync_labels(v)

    def move(v, gid, frm, to):
        groups = json.loads(json.dumps(v["groups"]))
        for g in groups:
            if g["id"] == frm:
                g["members"] = [m for m in g["members"] if m != gid]
            if g["id"] == to:
                g["members"].append(gid)
        return themes.land_kept(v, {"groups": groups, "picks": v.get("picks") or {}}, strict=True)

    v = move(v, "g8", "g2", "g3")
    v = move(v, "g8", "g3", "g2")
    v, info = themes.reorder(v, "g2", ["Initial:3:0", "Initial:5:0", "Initial:7:0", "g8", "g7", "g9"])
    v, _ = themes.reorder(v, "g8", ["Initial:13:0", "Initial:9:0"])
    v, _ = themes.reorder(v, "g7", ["Initial:17:0", "Initial:15:0", "Initial:15:1"])
    return v, info


def test_subpet_under_two(scratch):
    print("\n302. A sub-PET under two side by side rests a margin under the lower of them, by the agents' order and by "
          "a drag with the quotes on cards off and on, the two above never pushed up (30 October)")
    import themes

    v, info = _agents_board()
    drawn = themes.layout_boxes(v)
    f = drawn["frames"]
    foot = max(f["g8"][1] + f["g8"][3], f["g7"][1] + f["g7"][3])
    check("302: through the agents' ops (out of the PET, back in, the PET's order and two orders inside), the third "
          "sub-PET stands in the row under the two side by side, a margin under the lower of them, the order set",
          info["order"][3:] == ["g8", "g7", "g9"] and f["g9"][1] - foot == themes.MARGIN
          and abs(f["g8"][1] - f["g7"][1]) < 1 and v["stacks"] == STACK, json.dumps({"f": f, "info": info})[:900])

    node = shutil.which("node")
    if not node:
        skip("302: the board in node", "node is not installed")
        return
    page = {"cards": {k: {"x": c["x"], "y": c["y"], "text": c["text"], "time": "1:00", "sheet": "Initial"}
                      for k, c in v["cards"].items()},
            "groups": [{"id": g["id"], "label": g["label"], "members": list(g["members"]), "x": g["x"], "y": g["y"]}
                       for g in v["groups"]],
            "discarded": [], "stacks": v["stacks"]}
    parents = themes.parents_of(v["groups"])
    sizes = {k: [themes.CARD_W, themes.card_height(c["text"])] for k, c in v["cards"].items()}
    for g in v["groups"]:
        sizes[g["id"]] = list(themes.label_size(g["label"], any(m in {x["id"] for x in v["groups"]} for m in g["members"])))
    js = support.text("apps/idiograph/static/themes.js")
    head = f"const BOARD = {json.dumps(page)};\nconst SIZES = {json.dumps(sizes)};\n"
    script = scratch / "subpet-under-two-302.js"
    script.write_text(support.i18n_js() + STUBS + js + head + SCENARIO, encoding="utf-8")
    run = subprocess.run([node, str(script)], capture_output=True, text=True, encoding="utf-8", timeout=120)
    if run.returncode != 0:
        check("302: the board runs in node", False, run.stderr.strip()[:800])
        return
    o = json.loads(run.stdout)
    margin = themes.MARGIN
    g9 = {k for k in TEXTS if parents.get(k) == "g9"}
    for q in ("off", "on"):
        r = o[q]
        check(f"302: quotes {q}, opened, the board shows the third sub-PET a margin under the lower of the two, as the "
              "file holds it, with no more room under them than the board has",
              r["openGap"] == margin and r["openFile"]["g9"][0] - max(r["openFile"]["g8"][1], r["openFile"]["g7"][1]) == margin,
              json.dumps({"open": r["open"], "file": r["openFile"]}))
        check(f"302: quotes {q}, moved under both and down and dragged up, it rests a margin under the lower of the two "
              "and the drop lands it there in the file, its own statements moving by one shift and nothing else moving",
              r["loweredGap"] > 150 and r["dropGap"] == margin and set(r["moved"]) == g9 and r["g9dy"] == r["g9own"] < 0
              and r["dropFile"]["g9"][0] - max(r["dropFile"]["g8"][1], r["dropFile"]["g7"][1]) == margin
              and r["drop"]["g8"] == r["lowered"]["g8"] and r["drop"]["g7"] == r["lowered"]["g7"] and r["undo"] == 1,
              json.dumps({k: r[k] for k in ("lowered", "drop", "dropFile", "moved", "g9dy", "undo")})[:900])
        check(f"302: quotes {q}, dragged up again, nothing moves, the two above never sent up the board",
              r["againMoved"] == [] and r["again"] == r["drop"], json.dumps({"again": r["again"], "moved": r["againMoved"]}))
        check(f"302: quotes {q}, the board as the drop saved it opens with the third a margin under the two, at the "
              "height the agents' order gave it, so the canvas and the agents' ops leave the same board",
              r["reopenGap"] == margin and r["reopenFile"]["g9"][0] == round(f["g9"][1])
              and r["saved"]["cards"]["Initial:19:0"][1] == v["cards"]["Initial:19:0"]["y"],
              json.dumps({"reopen": r["reopen"], "file": r["reopenFile"], "agents": f["g9"]}))
