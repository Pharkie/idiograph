"""Area 309: an agent's change to a PETs board leaves no card over another, and the page taking it lays the board out
by the canvas's own rules (agentoverlap, 31 October 2026).

Adam, 31 October, on 0.9.15, quotes on cards Full: an agent changed the board while he had it open, he took the change,
"then the card that is updated overlaps with an existing card ... As soon as I drag it, it snaps to the right place".
An agent's `turn write` rewording a statement gave its card the longer words on every board and made no room, so the
card stood taller over the one under it, and the page's room for the quotes, made below each card's foot, ran the quote
under that card too. The page made room on an open only for a pair with a PET or a sub-PET in it, never for two cards.
Now the page makes room for every pair once it has measured a board, on an open, on taking a change and on a reload,
two cards as a drag's drop makes it (the one that reads first stays, the other pushed clear), and the server settles
what each agent's change touched by the same rule with its own sizes, after `board apply`, `turn write`, Find and
replace and an edit on the canvas carried to the other boards.

What is checked: on an invented participant, Wren, learning to sail a dinghy at forty, a board made by `board new` and
each sub-PET arranged in a column by `board apply`, then on a fresh copy each change an agent makes through the command
line: a statement moved into a sub-PET, an order inside one, a stack, a stack taken apart again, Put all on the board
and a statement reworded longer with a long quote by `turn write`. Each board the server saves has no two neighbours
nearer than the margin by its own sizes, and the reworded card's neighbour below has moved down under it in the same
order. Then in node on themes.js's own `thLoad` and `thOutsideTake`, at quotes Off, Short and Full, the page open on the
board before the change takes the change as Take does: nothing overlaps in the view or where the file keeps it, and the
page moves nothing of the agent's board. A board saved with a reworded card over the one under it, as before the fix,
opens clean at each setting, the reworded card where it stood and the one under it below it, with nothing written.
"""
from __future__ import annotations

import json
import shutil
from pathlib import Path

import openpyxl

from . import support
from .support import check as said_check, skip


def check(name, ok, detail=""):
    said_check(name, ok, json.dumps(detail, default=str)[:900])


TALK = [
    ("The first time the boat tipped I was sure I would drown, and then I was standing up in the water, waist deep, "
     "laughing at myself.", ["Sure she would drown", "Laughing at herself in the shallows"], ['"I was sure I would drown"', ""]),
    ("Nobody at the club was my age. They were all teenagers who had sailed since they could walk, and they looked at "
     "me like I was lost.", ["The only adult at the club", "Looked at as if she were lost"],
     ['"They were all teenagers who had sailed since they could walk, and they looked at me like I was lost."', ""]),
    ("Learning the knots at the kitchen table, over and over, until my husband said I was tying them in my sleep.",
     ["Knots at the kitchen table", "Tying them in her sleep"], ["", ""]),
    ("The wind does what it wants. You can't argue with it, you can only listen, and I had never listened to anything "
     "like that before.", ["Listening to the wind", "Nothing to argue with"], ['"you can only listen"', ""]),
    ("When I took her out alone the first time, the harbour went quiet in my head. Just the sail and the water and my "
     "hand on the tiller.", ["Out alone, the harbour quiet", "Her hand on the tiller"], ["", ""]),
    ("I told nobody at work. It felt like a secret I was keeping for myself.", ["A secret kept from work"], [""]),
    ("Capsizing on purpose in the drills, again and again, until falling in stopped being frightening.",
     ["Capsizing on purpose until it stopped frightening"], [""]),
    ("Now on a Saturday I'm the one showing the new ones how to right the boat.", ["Showing the new ones"], [""]),
]
# the statement reworded, S3 at the head of its sub-PET's column, its card from one line to four, with a long quote
LONG = ("The only adult at the club among teenagers who had sailed since they could walk, and she the one who looked "
        "lost to all of them")
LONG_QUOTE = '"Nobody at the club was my age. They were all teenagers who had sailed since they could walk."'

STUBS = """
const SAVED = [];
let AFTER = null;
globalThis.$ = () => null;
globalThis.esc = (s) => String(s);
globalThis.escAttr = (s) => String(s);
globalThis.say = () => {};
globalThis.MOD = (e) => !!(e && e.metaKey);
// the board the change left, as /api/themes reads it, and every other call the page makes counted, a save among them
globalThis.api = async (path) => { if (path === '/api/themes' && AFTER) return JSON.parse(JSON.stringify(AFTER)); SAVED.push(path); return {}; };
"""

HARNESS = r"""
const noop = () => {};
// what thLoad and Take call beyond the board, quiet here
thViewDrop = () => false; thStaleHide = noop; thClearSel = noop; thPanelDrop = noop; thViewDraw = noop;
thDrawBoard = noop; thNote = noop; thFaceRestore = noop; thSaveLine = noop; thReplyDrop = noop; thView = noop;
thVmenu = noop; thViewEnd = noop; thFlush = async () => {}; thFit = noop; thLand = noop; thDrawSel = noop;
thPanelFollow = noop; thEase = noop; thSoon = noop; thMapMoved = noop; thLinksDraw = noop; thTableSoon = noop;
thUnderPlace = noop; thTitleDone = noop; thNoteDone = noop;
thPlace = (drag) => { if (!drag) thRoomFollow(); TH.layout = thLayout(TH.v, thSize, null); };
let WAY = 'off';
let SIZES = {};
// the drawing: each card and label at the size the page measures, a card showing its quote taller by it, Short three
// lines at most and Full the whole quote, and the room for the quotes made as the page makes it (thStacksRoom)
thRender = () => {
  TH.els = { cards: {}, labels: {}, frames: {}, stickies: {}, rails: {}, under: {} };
  TH.sizes = {}; TH.qfull = {}; TH.qextra = {}; TH.baseH = {};
  for (const key of Object.keys(TH.v.cards)) {
    if (!thOnCanvas(TH.v, key)) continue;
    TH.els.cards[key] = {};
    const s = SIZES.cards[key];
    TH.sizes[key] = { w: s[0], h: s[1] };
    const q = WAY === 'off' ? null : thCardQuote(TH.v, key);
    if (!q) continue;
    const lines = Math.ceil(q.text.length / 28);
    const extra = 6 + 19 * (WAY === 'short' ? Math.min(3, lines) : lines);
    TH.qfull[key] = s[1] + extra; TH.qextra[key] = extra; TH.sizes[key] = { w: s[0], h: s[1] + extra };
  }
  for (const g of TH.v.groups) { TH.els.labels[g.id] = {}; const s = SIZES.labels[g.id]; TH.sizes[g.id] = { w: s[0], h: s[1] }; }
  thStacksRoom();
  TH.layout = thLayout(TH.v, thSize, null);
};
const copy = (o) => JSON.parse(JSON.stringify(o));
const pairs = (v, size) => thClashes(v, size).map((p) => p.join(' '));
const file = () => { const s = thUnshifted(TH.v); return Object.assign({}, TH.v, { cards: s.cards, groups: s.groups }); };
const spots = (v) => Object.fromEntries(Object.entries(v.cards).filter(([k]) => thOnCanvas(v, k)).map(([k, c]) => [k, [Math.round(c.x), Math.round(c.y)]]));
const moved = (a, b) => Object.keys(b).filter((k) => JSON.stringify(a[k]) !== JSON.stringify(b[k])).sort();
const said = (agent) => {
  const f = file();
  return { view: pairs(TH.v, thSize), file: pairs(f, thBaseSize), moved: moved(spots(agent), spots(f)),
           saved: SAVED.length, dirty: !!TH.dirty, at: spots(f) };
};
const asBoard = (d) => ({ cards: Object.fromEntries(d.cards.map((c) => [c.key, c])), groups: d.groups,
                          discarded: d.discarded, stacks: d.stacks || {}, stickies: d.stickies || [] });
const open = (d) => {
  TH.mode = 'pets'; TH.live = true; TH.path = 'Wren - EN & ES.xlsx'; TH.v = null; TH.meta = null; TH.undo = []; TH.redo = [];
  TH.stacks = {}; TH.undoBoard = null; TH.opened = new Set(); TH.shifts = []; TH.roomShown = null; TH.dirty = false;
  SAVED.length = 0;
  thLoad(copy(d), { fit: true });
};
(async () => {
  const out = {};
  for (const [name, c] of Object.entries(CASES)) {
    out[name] = {};
    for (const way of ['off', 'short', 'full']) {
      WAY = way;
      if (c.before) {
        // the page open on the board before the change, then Take, as the line's Show does
        SIZES = c.sizesBefore;
        open(c.before);
        const shown = pairs(TH.v, thSize);
        SIZES = c.sizesAfter;
        AFTER = c.after;
        await thOutsideTake({ board: c.after.version.id, changed: true, updated: 'later', cases: [] });
        out[name][way] = Object.assign(said(asBoard(c.after)), { before: shown });
      } else {
        // a board saved as it was before the fix, opened
        SIZES = c.sizesAfter;
        AFTER = null;
        open(c.after);
        out[name][way] = said(asBoard(c.after));
      }
    }
  }
  console.log(JSON.stringify(out));
})().catch((e) => { console.log(JSON.stringify({ error: String(e && e.stack || e) })); });
"""


def make_workbook(root: Path, folder: str, speaker: str) -> Path:
    """Wren's annotated workbook, the statements and quotes of each passage as the app writes them."""
    import workbook as wb_mod
    case = root / folder
    (case / "Source").mkdir(parents=True)
    raw = openpyxl.Workbook()
    first = raw.active
    first.title = "Initial"
    first.append(["Name", "Timestamp", "Transcript"])
    for n, (said, _es, _kq) in enumerate(TALK):
        first.append(["Interviewer", f"00:{n:02d}:04", "And then?"])
        first.append([speaker, f"00:{n:02d}:30", said])
    source = case / "Source" / f"{folder} - interview.xlsx"
    raw.save(source)
    book = wb_mod.create_from_source(source, case / f"{folder} - EN & ES.xlsx")
    wb = openpyxl.load_workbook(book, rich_text=True)
    ws = wb.worksheets[0]
    cols = wb_mod.detect_columns(ws)
    for n, (_said, es, kq) in enumerate(TALK):
        ws.cell(3 + 2 * n, cols["es"]).value = "\n\n".join(es)
        if any(kq):
            ws.cell(3 + 2 * n, cols["kq"]).value = "\n\n".join(q or "(no quote)" for q in kq)
    wb.save(book)
    return book


def near(board: dict, gap: float) -> list:
    """Each pair of neighbours on a saved board nearer than `gap` by the server's own sizes: in the same label, or on
    the canvas, a label by its frame, a statement waiting in Not placed off the canvas."""
    import themes
    v = themes.normalise(board)
    drawn = themes.layout_boxes(v)
    boxes = themes._solid_boxes(v, drawn)
    parents = themes.parents_of(v["groups"])
    waiting = set(themes.waiting_keys(v))
    ids = {g["id"] for g in v["groups"]}
    places: dict = {}
    for item, box in boxes.items():
        if item in waiting:
            continue
        home = parents.get(item)
        places.setdefault(home if home in ids else None, []).append((item, box))
    out = []
    for items in places.values():
        for i in range(len(items)):
            for j in range(i + 1, len(items)):
                if themes.clash(items[i][1], items[j][1], gap):
                    out.append(f"{items[i][0]} {items[j][0]}")
    return out


def sizes(board: dict) -> dict:
    """Each card's and label's size as the page measures it: the server's estimate, a pixel over the page's."""
    import themes
    drawn = themes.layout_boxes(themes.normalise(board))
    return {"cards": {k: [b[2], b[3] - 1] for k, b in drawn["cards"].items()},
            "labels": {g: [b[2], b[3] - 1] for g, b in drawn["labels"].items()}}


def test_agent_board_room(scratch: Path):
    print("\n309. An agent's change to a PETs board leaves no card over another, and the page taking it, or opening a "
          "board saved with one, lays it out by the canvas's rules at quotes Off, Short and Full (31 October)")
    import cli
    import server as server_mod
    import themes

    base = scratch / "agent-room-309"
    shutil.rmtree(base, ignore_errors=True)
    start = base / "start" / "Dinghy"
    start.mkdir(parents=True)
    (start / server_mod.PROJECT_FILE).write_text(json.dumps({
        "name": "Dinghy", "research_question": "How do adults experience learning to sail?",
        "agents": {"allowed": True, "at": "2026-10-31T09:00:00+00:00"}}), encoding="utf-8")
    book = make_workbook(start, "P1 - Wren", "Wren")
    config_file = base / "config-309.json"
    config_file.write_text(json.dumps({"projects": [], "interviewer": "Interviewer", "corpus": "",
                                       "gravity_reference": "", "corpus_exclude": []}), encoding="utf-8")
    plan = base / "plan.json"
    plan.write_text(json.dumps({
        "pets": [{"title": "Afraid of the water, then not", "members": ["S1", "S12"],
                  "subs": [{"title": "Out of place at the club", "members": ["S3", "S4", "S11"]},
                           {"title": "The wind as a teacher", "members": ["S7", "S8"]}]},
                 {"title": "A skill she made her own", "members": ["S5", "S6", "S13"],
                  "subs": [{"title": "Alone on the water", "members": ["S9", "S10"]}]}],
        "not_placed": {"S2": "A moment of the first day, apart from the rest"}}), encoding="utf-8")

    def run(root, *args):
        return cli.run(["--config", str(config_file), "--root", str(root), *args])

    def board_of(root) -> dict:
        data = json.loads((root / "P1 - Wren" / "Working" / f"{book.stem}.themes.json").read_text(encoding="utf-8"))
        return themes.current_version(data)

    def apply(root, ops, note):
        spec = root.parent / "ops.json"
        spec.write_text(json.dumps({"operations": ops}), encoding="utf-8")
        return run(root, "board", "apply", "Wren", "Board 1", "--ops", str(spec), "--note", note, "--tool", "Claude Code")

    made = run(start, "board", "new", "Wren", "--from", str(plan), "--note", "His first board", "--tool", "Claude Code")
    first = board_of(start) if made[0] == 0 else {}
    subs = {g["label"]: g["id"] for g in first.get("groups") or []}
    club = subs.get("Out of place at the club")
    arranged = apply(start, [{"op": "arrange", "label": subs.get(t), "way": "column"} for t in
                             ("Out of place at the club", "The wind as a teacher", "Alone on the water")],
                     "Each sub-PET in a column") if club else (1, "", "no board")
    if made[0] != 0 or arranged[0] != 0:
        check("309: the invented board made and its sub-PETs arranged in columns by the agents' ops", False,
              {"made": made, "arranged": arranged})
        return
    sids = {sid: k for k, sid in themes.short_ids(themes.read_cards(book)["cards"]).items()}
    kept = board_of(start)

    def turn_ops(root):
        spec = root.parent / "turn.json"
        spec.write_text(json.dumps({"pairs": [
            {"key": "Initial:5:0", "statement": LONG, "quote": LONG_QUOTE},
            {"key": "Initial:5:1", "statement": TALK[1][1][1], "quote": ""}]}), encoding="utf-8")
        return run(root, "turn", "write", "Wren", "Initial", "5", "--from", str(spec), "--note", "Say S3 more fully",
                   "--tool", "Claude Code")

    changes = {
        "move": lambda r: apply(r, [{"op": "move", "items": ["S13"], "to": club}], "Put S13 in with the club"),
        "order": lambda r: apply(r, [{"op": "order", "under": club, "items": ["S11", "S4", "S3"]}], "Reverse the club"),
        "stack": lambda r: apply(r, [{"op": "stack", "items": ["S4"], "under": "S3"}], "S4 under S3"),
        "unstack": lambda r: apply(r, [{"op": "stack", "items": ["S4", "S11"], "under": "S3"},
                                       {"op": "unstack", "items": ["S11"]}], "Stack and take one out"),
        "put_all_on": lambda r: apply(r, [{"op": "put_all_on"}], "Everything on the board"),
        "reword": turn_ops,
    }
    cases, server_said = {}, {}
    before_state = themes.state(book, "Wren")
    for name, change in changes.items():
        root = base / name / "Dinghy"
        shutil.rmtree(root.parent, ignore_errors=True)
        shutil.copytree(start, root)
        here = root / "P1 - Wren" / book.name
        done = change(root)
        board = board_of(root)
        after_state = themes.state(here, "Wren")
        server_said[name] = {"code": done[0], "said": (done[1] + done[2])[-300:], "near": near(board, themes.MARGIN - 2),
                             "over": near(board, -0.5), "board": board}
        cases[name] = {"before": before_state, "after": after_state, "sizesBefore": sizes(kept), "sizesAfter": sizes(board)}

    for name, s in server_said.items():
        check(f"309: {name}, the agent's change goes through and the board it saves has no card over another and none "
              "over a frame, every two neighbours a margin apart by the server's own sizes",
              s["code"] == 0 and not s["over"] and not s["near"], {k: s[k] for k in ("code", "said", "near", "over")})

    # the reword: the card stands taller and the card under it moved down under it, the sub-PET's order kept
    reworded = server_said["reword"]["board"]
    s3, s4 = sids["S3"], sids["S4"]
    grown = themes.card_height(reworded["cards"][s3]["text"]) - themes.card_height(kept["cards"][s3]["text"])
    order_then = themes.theme_order(themes.normalise(kept), club)
    order_now = themes.theme_order(themes.normalise(reworded), club)
    check("309: turn write rewording S3 longer gives its card the words on the board, the card under it moved down by as "
          "much as it grew, S3 where it stood, and the sub-PET reads in the same order",
          grown >= 40 and reworded["cards"][s3]["text"] == LONG
          and (reworded["cards"][s3]["x"], reworded["cards"][s3]["y"]) == (kept["cards"][s3]["x"], kept["cards"][s3]["y"])
          and reworded["cards"][s4]["y"] - kept["cards"][s4]["y"] >= grown and order_now == order_then,
          {"grown": grown, "s3": [kept["cards"][s3], reworded["cards"][s3]], "s4": [kept["cards"][s4]["y"], reworded["cards"][s4]["y"]],
           "order": [order_then, order_now]})

    # a board saved with the reworded card over the one under it, as the server left it before: the words taken, the
    # places as they were
    overlap = json.loads(json.dumps(cases["reword"]["after"]))
    held = {c["key"]: c for c in cases["reword"]["before"]["cards"]}
    for c in overlap["cards"]:
        c["x"], c["y"] = held[c["key"]]["x"], held[c["key"]]["y"]
    groups = {g["id"]: g for g in cases["reword"]["before"]["groups"]}
    for g in overlap["groups"]:
        g["x"], g["y"] = groups[g["id"]]["x"], groups[g["id"]]["y"]
    cases["saved_overlap"] = {"after": overlap, "sizesAfter": cases["reword"]["sizesAfter"]}

    if not shutil.which("node"):
        skip("309: the page taking each change, under node", "node is not on this machine")
        return
    script = (support.i18n_js() + STUBS + support.text("apps/idiograph/static/themes.js")
              + f"\nconst CASES = {json.dumps(cases, default=str)};\n" + HARNESS)
    ran = support.run_node(script, base, "agent-room-309.js", timeout=180)
    try:
        o = json.loads(ran.stdout.strip().splitlines()[-1])
    except (ValueError, IndexError):
        o = {}
    if not o or o.get("error"):
        check("309: the page's own code runs in node over the agent's boards", False, (ran.stdout + ran.stderr)[-900:])
        return
    for name in changes:
        for way in ("off", "short", "full"):
            r = o[name][way]
            check(f"309: {name}, quotes {way}, the page open on the board takes the agent's change and nothing overlaps, "
                  "in the view or where the file keeps it, the page moving nothing of the agent's board and writing nothing",
                  not r["view"] and not r["file"] and not r["moved"] and not r["saved"] and not r["dirty"]
                  and not r["before"], {k: r[k] for k in ("view", "file", "moved", "saved", "dirty", "before")})
    for way in ("off", "short", "full"):
        r = o["saved_overlap"][way]
        held_s3 = [held[s3]["x"], held[s3]["y"]]
        check(f"309: a board saved with a reworded card over the one under it opens clean at quotes {way}: nothing "
              "overlaps in the view or the file, the reworded card where it stood and the one under it below it, the "
              "order kept, and nothing written",
              not r["view"] and not r["file"] and r["at"][s3] == held_s3 and s4 in r["moved"] and s3 not in r["moved"]
              and r["at"][s4][1] > held[s4]["y"] and not r["saved"] and not r["dirty"],
              {k: r[k] for k in ("view", "file", "moved", "saved", "dirty")} | {"s3": [held_s3, r["at"][s3]], "s4": r["at"][s4]})
