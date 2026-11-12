"""Area 305: another board comes on with its cards in view (boardview, 30 October 2026).

Adam, 30 October: going from one board to another, "it opens up in blank space and then I have to navigate to where
the cards are". Since 2 October a switch in the board menu, and a board deleted, kept the view of the board left, so
the next board's cards were in view only where the two stood in one place, as a duplicate does. An open fitted the
board, as it still does. Now another board comes on where its cards are (`thLand`): the view stays when it shows any
of that board's cards, so two boards laid out alike are still compared in one place, else the view that board was left
in while the participant has been open, else the board fitted as an open fits it, its used canvas in view, the origin
on an empty board. Fit all on a board too big to show whole even at the least zoom shows its top left, where its
middle could be blank.

What is checked: in node on themes.js's own `thLoad`, `thSwitch`, `thDeleteGo`, `thFit` and `thBackFromPassage`, over
the demo's Juno as `/api/themes` reads her (the demo's invented interview, on living with a dog), with the route and the
drawing stubbed: the open showing every card, a switch to a board whose cards stand far off showing its cards, a switch
back finding each board on the view it was left in, a switch to a board laid out as the one left keeping the view, an
empty board at the origin, a board deleted bringing the next on with its cards in view and no view kept for it, the way
back from a passage opening on the view it kept, and a board too wide for the least zoom fitted to its top left. The
other boards are Juno's own moved, emptied or spread out in the harness, no words of their own."""
from __future__ import annotations

import json
import shutil

from . import support
from .support import check as said_check, skip


def check(name, ok, detail=""):
    said_check(name, ok, json.dumps(detail, default=str)[:600])

HARNESS = r"""
const noop = () => {};
// what thLoad and the board menu call beyond the view, quiet here
thViewDrop = () => false; thStaleHide = noop; thKnow = noop; thClearSel = noop; thPanelDrop = noop; thViewDraw = noop;
thDrawBoard = noop; thNote = noop; thInFile = () => false; thFaceRestore = noop; thSaveLine = noop; thReplyDrop = noop;
thView = noop; thVmenu = noop; thTitleDone = noop; thNoteDone = noop; thViewEnd = noop; thFlush = async () => {};
thVsaid = noop; thDrawSel = noop; thPanelFollow = noop;
globalThis.hide = noop;
// the drawing: each card standing on the canvas drawn, each label's title where its label stands
thRender = () => {
  TH.els.cards = {};
  for (const key of Object.keys(TH.v.cards)) if (thOnCanvas(TH.v, key)) TH.els.cards[key] = {};
  TH.layout = {};
  for (const g of TH.v.groups) TH.layout[g.id] = { label: { x: g.x, y: g.y, w: 320, h: 64 } };
};

const ONE = __STATE__;
const copy = (o) => JSON.parse(JSON.stringify(o));
// Juno's own board, and four more made from it: moved far off, laid out as the moved one, emptied, spread wide
const board = (id, name, change) => { const d = copy(ONE); d.version = Object.assign({}, d.version, { id, name }); change(d); return d; };
const shift = (d) => {
  for (const c of d.cards) { c.x += 9000; c.y += 6000; }
  for (const g of d.groups) { g.x += 9000; g.y += 6000; }
  for (const n of d.stickies || []) { n.x += 9000; n.y += 6000; }
};
const B = {
  v1: board('v1', 'Board 1', () => {}),
  v2: board('v2', 'Board 2', shift),
  v3: board('v3', 'Board 2 copy', shift),
  v4: board('v4', 'Board 4', (d) => { d.groups = []; d.stickies = []; d.discarded = []; d.stacks = {}; for (const c of d.cards) delete c.loose; }),
  v5: board('v5', 'Board 5', (d) => {
    d.groups = []; d.stickies = []; d.discarded = []; d.stacks = {};
    d.cards.forEach((c, i) => { c.loose = true; c.x = i * 420 - 2000; c.y = (i % 4) * 150 - 3000; });
  }),
};
const metas = Object.values(B).map((d) => d.version);
for (const d of Object.values(B)) d.versions = metas;
// the board ops' route: the board switched to, and after a delete the first board with the one deleted gone
let deleted = null;
globalThis.api = async (url, body) => {
  if (body.op === 'switch') return B[body.id];
  if (body.op === 'delete') { deleted = body.id; return Object.assign(copy(B.v1), { versions: metas.filter((m) => m.id !== body.id) }); }
  throw new Error(`not stubbed: ${body.op}`);
};

const stage = thStage();
// how many of the board's cards stand with their middle on the stage, and the view
const inView = () => Object.keys(TH.els.cards).filter((key) => {
  const c = TH.v.cards[key]; const s = thSize(key);
  const x = TH.view.x + (c.x + s.w / 2) * TH.view.z; const y = TH.view.y + (c.y + s.h / 2) * TH.view.z;
  return x >= 0 && x <= stage.clientWidth && y >= 0 && y <= stage.clientHeight;
}).length;
const drawn = () => Object.keys(TH.els.cards).length;
const view = () => ({ x: Math.round(TH.view.x), y: Math.round(TH.view.y), z: +TH.view.z.toFixed(4) });
const said = () => ({ board: TH.meta.id, inView: inView(), drawn: drawn(), view: view() });

(async () => {
  const out = {};
  TH.mode = 'pets'; TH.live = true; TH.path = 'Juno - EN & ES.xlsx';
  // the open, as themesOpen loads a board
  thLoad(B.v1, { fit: true });
  out.open = said();
  // the board menu's switch to a board whose cards stand far off
  await thSwitch('v2');
  out.far = said();
  // a view of his own on it, at 100% with a card of it a third of the way in
  const k = Object.keys(TH.els.cards)[0];
  TH.view = { x: Math.round(stage.clientWidth / 3 - TH.v.cards[k].x), y: Math.round(stage.clientHeight / 3 - TH.v.cards[k].y), z: 1 };
  out.mine = view();
  out.mineShows = inView();
  // back to the first, then to the far one again: each on the view it was left in
  await thSwitch('v1');
  out.back1 = said();
  await thSwitch('v2');
  out.back2 = said();
  // a board laid out as the one on the canvas keeps the view, as since 2 October
  await thSwitch('v3');
  out.alike = said();
  // a board with nothing on the canvas, every statement waiting in Not placed
  await thSwitch('v4');
  out.empty = said();
  out.middle = { x: Math.round(stage.clientWidth / 2), y: Math.round(stage.clientHeight / 2), z: 1 };
  // Delete this board: the next comes on with its cards in view, and no view is kept for the one deleted
  TH.doomed = 'v4';
  await thDeleteGo();
  out.deleted = Object.assign(said(), { asked: deleted, kept: Object.keys(TH.views).sort() });
  // the way back from a passage opens on the view it kept
  thLoad(B.v1, { fit: true });
  const back = { x: out.open.view.x - 200, y: out.open.view.y - 100, z: 0.5 };
  thBackFromPassage({ view: back });
  out.restored = Object.assign(said(), { want: back });
  // a board too wide to show whole even at the least zoom: its top left in view
  const corner = () => {
    const first = TH.v.cards[Object.keys(TH.v.cards).sort((a, b) => TH.v.cards[a].x - TH.v.cards[b].x || TH.v.cards[a].y - TH.v.cards[b].y)[0]];
    const s = thSize(Object.keys(TH.v.cards)[0]);
    return { x: TH.view.x + (first.x + s.w / 2) * TH.view.z, y: TH.view.y + (first.y + s.h / 2) * TH.view.z, w: stage.clientWidth, h: stage.clientHeight };
  };
  await thSwitch('v5');
  out.wide = Object.assign(said(), { corner: corner() });
  // and Fit all there, from a view elsewhere, the same
  TH.view = { x: 0, y: 0, z: 1 };
  thFit();
  out.fitAll = Object.assign(said(), { corner: corner() });
  console.log(JSON.stringify(out));
})().catch((e) => { console.log(JSON.stringify({ error: String(e && e.stack || e) })); });
"""

STUBS = """
const STAGE = { clientWidth: 1180, clientHeight: 640, classList: { add() {}, remove() {}, toggle() {} },
  getBoundingClientRect: () => ({ left: 0, top: 0, width: 1180, height: 640, right: 1180, bottom: 640 }) };
globalThis.$ = (id) => (id === 'th-stage' ? STAGE : null);
globalThis.esc = (s) => String(s);
globalThis.escAttr = (s) => String(s);
globalThis.say = () => {};
globalThis.MOD = (e) => !!(e && e.metaKey);
"""


def test_board_view(scratch):
    print("\n305. Another board comes on with its cards in view: a switch to a board whose cards stand elsewhere, a "
          "switch back on the view it was left in, a board laid out alike keeping the view, an empty board at the "
          "origin, a delete, the way back from a passage, and a board too wide for the least zoom at its top left")
    if not shutil.which("node"):
        skip("305: another board's view, under node", "node is not on this machine")
        return
    import themes

    base = scratch / "a305"
    shutil.rmtree(base, ignore_errors=True)
    (base / "Working").mkdir(parents=True)
    book = base / "Juno - EN & ES.xlsx"
    shutil.copy2(support.DEMO_SHIPPED / "Juno - EN & ES.xlsx", book)
    shutil.copy2(support.DEMO_SHIPPED / "Working" / "Juno - EN & ES.themes.json", base / "Working" / "Juno - EN & ES.themes.json")
    state = themes.state(book, "Juno")
    script = (support.i18n_js() + STUBS + support.text("apps/idiograph/static/themes.js")
              + HARNESS.replace("__STATE__", json.dumps(state, default=str)))
    ran = support.run_node(script, base, "board-view-305.js", timeout=120)
    try:
        o = json.loads(ran.stdout.strip().splitlines()[-1])
    except (ValueError, IndexError):
        o = {}
    detail = (ran.stdout + ran.stderr)[-900:]
    if not o or o.get("error"):
        check("305: the page's own code runs in node over Juno's board", False, detail)
        return
    opened, far = o["open"], o["far"]
    check("305: an open fits the board, every card on the canvas in view",
          opened["drawn"] == len(state["cards"]) > 20 and opened["inView"] == opened["drawn"], opened)
    check("305: a switch to a board whose cards stand far off comes on with them in view, never the blank place the "
          "board left was shown at", far["board"] == "v2" and far["inView"] == far["drawn"] and far["view"] != opened["view"], far)
    check("305: a switch back finds each board on the view it was left in, the open's fit and his own at 100%",
          o["back1"]["board"] == "v1" and o["back1"]["view"] == opened["view"]
          and o["back2"]["board"] == "v2" and o["back2"]["view"] == o["mine"] and o["mineShows"] > 0, (o["back1"], o["back2"], o["mine"]))
    check("305: a switch to a board laid out as the one left keeps the view, so two such boards are compared in one place",
          o["alike"]["board"] == "v3" and o["alike"]["view"] == o["mine"] and o["alike"]["inView"] > 0, o["alike"])
    check("305: an empty board, every statement waiting in Not placed, opens at the origin in the middle at 100%",
          o["empty"]["board"] == "v4" and o["empty"]["drawn"] == 0 and o["empty"]["view"] == o["middle"], (o["empty"], o["middle"]))
    d = o["deleted"]
    check("305: Delete this board brings the next board on with its cards in view, and keeps no view for the one deleted",
          d["asked"] == "v4" and d["board"] == "v1" and d["inView"] > 0 and "v4" not in d["kept"], d)
    r = o["restored"]
    check("305: the way back from a passage opens on the view it kept", r["view"] == r["want"] and r["inView"] > 0, r)
    corner = lambda w: (w["view"]["z"] == 0.15 and 0 <= w["corner"]["x"] <= w["corner"]["w"]
                        and 0 <= w["corner"]["y"] <= w["corner"]["h"])
    check("305: a board too wide to show whole even at the least zoom comes on at the least zoom with its top left "
          "card in view, and Fit all there shows the same", o["wide"]["board"] == "v5" and corner(o["wide"])
          and corner(o["fitAll"]) and o["fitAll"]["view"] == o["wide"]["view"], (o["wide"], o["fitAll"]))
