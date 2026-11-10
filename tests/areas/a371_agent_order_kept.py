"""Area 371: an agent's `board apply` leaves every label it does not name in the order it read, and the page open on
the board when the agent writes changes nothing of that order (agentorder, 10 November 2026).

The Gravity session, 10 November: across one afternoon's revisions of a real board an agent's operations changed the
reading order of PETs, sub-PETs and statements they never named, and the PETs table and the PDF, which read order from
where things stand on the canvas, followed. A `move` of two loose statements into a sub-PET swapped two PETs, an `order`
of the PETs swapped two sub-PETs inside one of them, a `move` of one statement into a sub-PET swapped that sub-PET with
the one before it, and the statements in sub-PETs no operation named drifted. Two causes: the server laid out afresh,
as a round blob, the whole PET a statement went into from elsewhere (`themes.land`), and the room it and the page then
made moved things by the least distance, which can carry one past its neighbour's row. And the page, its type taller
than the server's sizes, made room on taking the change by sending a statement aside, an order his next act saved.

What is checked: on an invented participant, Hazel, keeping bees in a city garden, a board of three PETs with two
sub-PETs each and loose statements, and on a copy of the demo's Juno, each change through the command line: two loose
statements moved into a sub-PET, the PETs ordered, one statement moved into a sub-PET. Each place no operation named
reads as it did, the sub-PET moved into reads its own statements first and the newcomers after them in the order named,
the ordered PETs read as named, and nothing stands nearer than the margin. Then the page, in node on themes.js's own
`thLoad` and `thOutsideTake`, open on the board before each change and taking it, at the server's sizes and with its
cards forty pixels taller: the places the page keeps for the file read every PET, sub-PET and the PETs in the agent's
order, nothing overlaps, and at the server's sizes nothing moves. And the page's own save while the agent writes is
refused, its canvas kept in History, and the board reads as the agent left it.
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
    "The first hive came from a man at the allotment who was giving up, and I carried it home on the bus.",
    "I was stung on the second day and sat on the step and laughed, because I had been so afraid of it.",
    "The smoke calms them, or it tells them there is a fire and they eat the honey, nobody quite agrees.",
    "Opening the lid is like opening a letter from somebody who doesn't know you are reading it.",
    "In the winter there is nothing to do but listen with your ear to the side of the box.",
    "My neighbour complained about the swarm and then asked for a jar of honey.",
    "I learned the queen's marks from a book, and then I could never find her anyway.",
    "When the colony died in the spring I cleaned the frames alone and didn't tell anyone.",
    "The second year I knew what I was looking at, and that was worse in a way.",
    "Watching them come in heavy with pollen on a warm evening is the best hour of the week.",
    "My daughter wears the spare veil and calls them her cousins.",
    "I keep a notebook of every inspection, the weather and what they were like that day.",
    "Somebody at the association said I was too soft with them, and maybe I am.",
    "The first honey was dark and tasted of the lime trees on the avenue.",
    "I sell a few jars at the gate and leave a tin for the money.",
    "If I am honest I go out to them when the house is too loud.",
    "Losing a queen in July taught me more than the course did.",
    "The bees don't care about me at all, which is a relief.",
    "A swarm in the plum tree, low enough to shake into a box, the first one I caught.",
    "I talk to them, the old custom, I tell them when something happens in the family.",
    "My hands are steadier now than they were before the bees.",
    "There is a smell to a healthy hive, warm and a little like bread.",
    "I worry about the wasps in August more than anything else.",
    "Next year I want to try a second apiary out on the edge of town.",
]

STUBS = """
const SAVED = [];
let AFTER = null;
globalThis.$ = () => null;
globalThis.esc = (s) => String(s);
globalThis.escAttr = (s) => String(s);
globalThis.say = () => {};
globalThis.MOD = (e) => !!(e && e.metaKey);
globalThis.api = async (path) => { if (path === '/api/themes' && AFTER) return JSON.parse(JSON.stringify(AFTER)); SAVED.push(path); return {}; };
"""

HARNESS = r"""
const noop = () => {};
thViewDrop = () => false; thStaleHide = noop; thClearSel = noop; thPanelDrop = noop; thViewDraw = noop;
thDrawBoard = noop; thNote = noop; thFaceRestore = noop; thSaveLine = noop; thReplyDrop = noop; thView = noop;
thVmenu = noop; thViewEnd = noop; thFlush = async () => {}; thFit = noop; thLand = noop; thDrawSel = noop;
thPanelFollow = noop; thEase = noop; thSoon = noop; thMapMoved = noop; thLinksDraw = noop; thTableSoon = noop;
thUnderPlace = noop; thTitleDone = noop; thNoteDone = noop;
thPlace = (drag) => { if (!drag) thRoomFollow(); TH.layout = thLayout(TH.v, thSize, null); };
let SIZES = {};
// each card and label at the size the page measures, the quotes off
thRender = () => {
  TH.els = { cards: {}, labels: {}, frames: {}, stickies: {}, rails: {}, under: {} };
  TH.sizes = {}; TH.qfull = {}; TH.qextra = {}; TH.baseH = {};
  for (const key of Object.keys(TH.v.cards)) {
    if (!thOnCanvas(TH.v, key)) continue;
    TH.els.cards[key] = {};
    const s = SIZES.cards[key];
    TH.sizes[key] = { w: s[0], h: s[1] };
  }
  for (const g of TH.v.groups) { TH.els.labels[g.id] = {}; const s = SIZES.labels[g.id]; TH.sizes[g.id] = { w: s[0], h: s[1] }; }
  thStacksRoom();
  TH.layout = thLayout(TH.v, thSize, null);
};
const copy = (o) => JSON.parse(JSON.stringify(o));
// every place's reading order as the page reads it, the PETs and inside each label
const ordersOf = (v, size) => {
  const layout = thLayout(v, size, null);
  const parents = thParents(v);
  const out = { '': gtCanvasOrder(v.groups.filter((g) => parents[g.id] === undefined)) };
  for (const g of v.groups) out[g.id] = thThemeOrder(v, g.id, layout);
  return JSON.stringify(out);
};
const file =() => { const s = thUnshifted(TH.v); return Object.assign({}, TH.v, { cards: s.cards, groups: s.groups }); };
const spots = (v) => Object.fromEntries(Object.entries(v.cards).filter(([k]) => thOnCanvas(v, k)).map(([k, c]) => [k, [Math.round(c.x), Math.round(c.y)]]));
const asBoard = (d) => ({ cards: Object.fromEntries(d.cards.map((c) => [c.key, c])), groups: d.groups,
                          discarded: d.discarded, stacks: d.stacks || {}, stickies: d.stickies || [] });
const open = (d) => {
  TH.mode = 'pets'; TH.live = true; TH.path = 'Hazel - EN & ES.xlsx'; TH.v = null; TH.meta = null; TH.undo = []; TH.redo = [];
  TH.stacks = {}; TH.undoBoard = null; TH.opened = new Set(); TH.shifts = []; TH.roomShown = null; TH.dirty = false;
  SAVED.length = 0;
  thLoad(copy(d), { fit: true });
};
(async () => {
  const out = {};
  for (const [name, c] of Object.entries(CASES)) {
    out[name] = {};
    for (const [taller, sizes] of Object.entries(c.sizes)) {
      SIZES = sizes.before;
      open(c.before);
      SIZES = sizes.after;
      AFTER = c.after;
      await thOutsideTake({ board: c.after.version.id, changed: true, updated: 'later', cases: [] });
      const f = file();
      // the agent's board read at the page's sizes, as it reads before any room is made
      const agent = asBoard(c.after);
      const moved = Object.keys(spots(f)).filter((k) => JSON.stringify(spots(f)[k]) !== JSON.stringify(spots(agent)[k]));
      out[name][taller] = { want: ordersOf(agent, thBaseSize), got: ordersOf(f, thBaseSize), at: spots(f),
                            labels: Object.fromEntries(f.groups.map((g) => [g.id, [Math.round(g.x), Math.round(g.y)]])),
                            clash: thClashes(f, thBaseSize).map((p) => p.join(' ')), moved: moved.length,
                            saved: SAVED.length, dirty: !!TH.dirty };
    }
  }
  console.log(JSON.stringify(out));
})().catch((e) => { console.log(JSON.stringify({ error: String(e && e.stack || e) })); });
"""


def make_workbook(root: Path, folder: str, speaker: str) -> Path:
    """Hazel's annotated workbook, a statement to each of her turns, some long enough to take three lines."""
    import workbook as wb_mod
    case = root / folder
    (case / "Source").mkdir(parents=True)
    raw = openpyxl.Workbook()
    first = raw.active
    first.title = "Initial"
    first.append(["Name", "Timestamp", "Transcript"])
    for n, said in enumerate(TALK):
        first.append(["Interviewer", f"00:{n:02d}:04", "And then?"])
        first.append([speaker, f"00:{n:02d}:30", said])
    source = case / "Source" / f"{folder} - interview.xlsx"
    raw.save(source)
    book = wb_mod.create_from_source(source, case / f"{folder} - EN & ES.xlsx")
    wb = openpyxl.load_workbook(book, rich_text=True)
    ws = wb.worksheets[0]
    cols = wb_mod.detect_columns(ws)
    for n, said in enumerate(TALK):
        # statements of one line to four, by turns
        ws.cell(3 + 2 * n, cols["es"]).value = " ".join((said.rstrip(".") + " " + said).split()[:3 + 3 * (n % 5)])
    wb.save(book)
    return book


def orders(board: dict) -> dict:
    """Every place's reading order on a board, the PETs under "" and each label under its id."""
    import themes
    v = themes.normalise(board)
    drawn = themes.layout_boxes(v)
    out = {"": themes.order_of(v, None, drawn)}
    for g in v["groups"]:
        out[g["id"]] = themes.order_of(v, g["id"], drawn)
    return out


def near(board: dict, gap: float) -> list:
    """Each pair of neighbours on a saved board nearer than `gap` by the server's own sizes."""
    import themes
    v = themes.normalise(board)
    drawn = themes.layout_boxes(v)
    boxes = themes._solid_boxes(v, drawn)
    parents = themes.parents_of(v["groups"])
    waiting = set(themes.waiting_keys(v))
    ids = {g["id"] for g in v["groups"]}
    places: dict = {}
    for item, box in boxes.items():
        if item not in waiting:
            places.setdefault(parents.get(item) if parents.get(item) in ids else None, []).append((item, box))
    return [f"{a[0]} {b[0]}" for items in places.values() for i, a in enumerate(items) for b in items[i + 1:]
            if themes.clash(a[1], b[1], gap)]


def sizes(board: dict, taller: int) -> dict:
    """Each card's and label's size as the page measures it, a pixel under the server's, the cards `taller`."""
    import themes
    drawn = themes.layout_boxes(themes.normalise(board))
    return {"cards": {k: [b[2], b[3] - 1 + taller] for k, b in drawn["cards"].items()},
            "labels": {g: [b[2], b[3] - 1] for g, b in drawn["labels"].items()}}


def test_agent_order_kept(scratch: Path):
    print("\n371. An agent's board apply leaves every label it does not name in the order it read, and the page open "
          "on the board changes nothing of that order (agentorder, 10 November 2026)")
    import cli
    import server as server_mod
    import themes

    base = scratch / "agent-order-371"
    shutil.rmtree(base, ignore_errors=True)
    start = base / "start" / "Bees"
    start.mkdir(parents=True)
    (start / server_mod.PROJECT_FILE).write_text(json.dumps({
        "name": "Bees", "research_question": "How do people experience keeping bees in a city?",
        "agents": {"allowed": True, "at": "2026-11-10T09:00:00+00:00"}}), encoding="utf-8")
    book = make_workbook(start, "P1 - Hazel", "Hazel")
    config_file = base / "config-371.json"
    config_file.write_text(json.dumps({"projects": [], "interviewer": "Interviewer", "corpus": "",
                                       "gravity_reference": "", "corpus_exclude": []}), encoding="utf-8")
    plan = base / "plan.json"
    plan.write_text(json.dumps({"pets": [
        {"title": "Afraid, then not", "members": ["S1", "S2"],
         "subs": [{"title": "The first sting", "members": ["S3", "S4"]},
                  {"title": "Smoke and lids", "members": ["S5", "S6"]}]},
        {"title": "Learning by losing", "members": ["S7"],
         "subs": [{"title": "The dead colony", "members": ["S8", "S9", "S10"]},
                  {"title": "The lost queen", "members": ["S11"]}]},
        {"title": "A place of her own", "members": ["S12", "S13"],
         "subs": [{"title": "Out in the garden", "members": ["S14"]},
                  {"title": "Telling the bees", "members": ["S15", "S16"]}]}],
        "not_placed": {}}), encoding="utf-8")

    def run(root, *args):
        return cli.run(["--config", str(config_file), "--root", str(root), *args])

    def themes_file(root, folder):
        return next((root / folder / "Working").glob("* - EN & ES.themes.json"))

    def board_of(root, folder="P1 - Hazel") -> dict:
        return themes.current_version(json.loads(themes_file(root, folder).read_text(encoding="utf-8")))

    def apply(root, case, board, ops, note):
        spec = root.parent / "ops.json"
        spec.write_text(json.dumps({"operations": ops}), encoding="utf-8")
        return run(root, "board", "apply", case, board, "--ops", str(spec), "--note", note, "--tool", "Claude Code")

    made = run(start, "board", "new", "Hazel", "--from", str(plan), "--note", "Her first board", "--tool", "Claude Code")
    put = apply(start, "Hazel", "Board 1", [{"op": "put_all_on"}], "Everything on the board") if made[0] == 0 else made
    if made[0] != 0 or put[0] != 0:
        check("371: the invented board made, every statement on it", False, {"made": made, "put": put})
        return
    kept = themes.normalise(board_of(start))
    ids = {g["label"]: g["id"] for g in kept["groups"]}
    loose = [k for k, c in kept["cards"].items() if c.get("loose")]
    pets = [ids["Afraid, then not"], ids["Learning by losing"], ids["A place of her own"]]

    # each change, the place it names and the order that place should read in after it
    changes = {
        "two into a sub-PET": ([{"op": "move", "items": loose[:2], "to": ids["The lost queen"]}],
                               ids["The lost queen"], None),
        "the PETs ordered": ([{"op": "order", "under": None, "items": [pets[1], pets[0], pets[2]]}],
                             "", [pets[1], pets[0], pets[2]]),
        "one into a sub-PET": ([{"op": "move", "items": [loose[0]], "to": ids["Telling the bees"]}],
                               ids["Telling the bees"], None),
    }
    was = orders(kept)
    cases, boards = {}, {}
    for name, (ops, place, wanted) in changes.items():
        root = base / name.replace(" ", "-") / "Bees"
        shutil.rmtree(root.parent, ignore_errors=True)
        shutil.copytree(start, root)
        done = apply(root, "Hazel", "Board 1", ops, f"Agent: {name}")
        board = board_of(root)
        boards[name] = board
        now = orders(board)
        moved_in = [m for m in ops[0].get("items") or []] if ops[0]["op"] == "move" else []
        want = wanted or (was[place] + moved_in)
        drift = {p: [was[p], now.get(p)] for p in was if p != place and was[p] != now.get(p)}
        check(f"371: {name}, the agent's change goes through, the place it names reads "
              + ("as the order set it" if wanted else "its own statements first and the new ones after them, as named")
              + ", every other PET, sub-PET and the PETs read as they did, and nothing stands nearer than the margin",
              done[0] == 0 and now[place] == want and not drift and not near(board, themes.MARGIN - 2),
              {"code": done[0], "said": (done[1] + done[2])[-200:], "place": [want, now[place]], "drift": drift,
               "near": near(board, themes.MARGIN - 2)})
        here = root / "P1 - Hazel" / book.name
        cases[name] = {"before": themes.state(book, "Hazel"), "after": themes.state(here, "Hazel"),
                       "sizes": {str(t): {"before": sizes(kept, t), "after": sizes(board, t)} for t in (0, 40)}}

    # the demo's written participants: two statements moved from another PET into a sub-PET
    import make_demo
    for who in make_demo.WRITTEN:
        demo = base / "demo" / who / "Demo"
        (demo / who / "Working").mkdir(parents=True)
        (demo / server_mod.PROJECT_FILE).write_text(json.dumps({
            "name": "Demo", "research_question": "?", "agents": {"allowed": True, "at": "2026-11-10T09:00:00+00:00"}}),
            encoding="utf-8")
        shutil.copy2(support.DEMO_PRISTINE / f"{who} - EN & ES.xlsx", demo / who / f"{who} - EN & ES.xlsx")
        for side in (support.DEMO_PRISTINE / "Working").glob(f"{who} - *"):
            shutil.copy2(side, demo / who / "Working" / side.name)
        first = themes.normalise(board_of(demo, who))
        parents = themes.parents_of(first["groups"])
        tops = [g["id"] for g in first["groups"] if g["id"] not in parents]
        subs = [g["id"] for g in first["groups"] if g["id"] in parents]
        target = subs[-1] if subs else tops[-1]
        elsewhere = [k for k in first["cards"] if parents.get(k) in tops and parents.get(k) != parents.get(target)
                     and not (first.get("stacks") or {}).get(k) and k not in first.get("discarded", [])][:2]
        before_demo = orders(first)
        done = apply(demo, who, first["name"], [{"op": "move", "items": elsewhere, "to": target}],
                     "Agent: two into a sub-PET")
        after_demo = orders(board_of(demo, who))
        touched = {target} | {parents.get(k) for k in elsewhere}
        drift = {p: [before_demo[p], after_demo.get(p)] for p in before_demo
                 if p not in touched and before_demo[p] != after_demo.get(p)}
        left = {p: [m for m in after_demo.get(p, []) if m not in elsewhere] for p in touched}
        check(f"371: on the demo's {who}, two statements moved from another PET into a sub-PET, the PETs and every "
              "label the move did not touch read as they did, what stays in those it touched reads as it did, and the "
              "two read last in the sub-PET, as named",
              done[0] == 0 and len(elsewhere) == 2 and not drift
              and all(left[p] == [m for m in before_demo[p] if m not in elsewhere] for p in left)
              and after_demo[target][-2:] == elsewhere,
              {"code": done[0], "said": (done[1] + done[2])[-200:], "drift": drift, "target": after_demo.get(target)})

    # the page's own save while the agent writes: refused, its canvas kept, the board as the agent left it
    root = base / "stale" / "Bees"
    shutil.rmtree(root.parent, ignore_errors=True)
    shutil.copytree(start, root)
    here = root / "P1 - Hazel" / book.name
    page_had = board_of(root)
    apply(root, "Hazel", "Board 1", changes["two into a sub-PET"][0], "Agent: two into a sub-PET")
    agent = orders(board_of(root))
    sent = dict(page_had)
    for k in list(sent["cards"])[:3]:
        sent["cards"][k] = dict(sent["cards"][k], x=sent["cards"][k]["x"] + 400)
    refused = ""
    try:
        themes.save(here, sent, "Hazel")
    except Exception as exc:  # the refusal the page shows
        refused = getattr(exc, "code", "") or str(exc)
    history = themes.history_of(board_of(root))
    check("371: the page's own save, sent from the board as it was before the agent's change, is refused, its canvas "
          "kept in the board's History, and every place reads as the agent left it",
          refused == "board_changed_outside" and orders(board_of(root)) == agent
          and history and themes.revision_mark(history[-1])[0] == "canvas_kept", {"refused": refused})

    if not shutil.which("node"):
        skip("371: the page taking each change, under node", "node is not on this machine")
        return
    script = (support.i18n_js() + STUBS + support.text("apps/idiograph/static/themes.js")
              + f"\nconst CASES = {json.dumps(cases, default=str)};\n" + HARNESS)
    ran = support.run_node(script, base, "agent-order-371.js", timeout=240)
    try:
        o = json.loads(ran.stdout.strip().splitlines()[-1])
    except (ValueError, IndexError):
        o = {}
    if not o or o.get("error"):
        check("371: the page's own code runs in node over the agent's boards", False, (ran.stdout + ran.stderr)[-900:])
        return
    for name in changes:
        for taller in ("0", "40"):
            r = o[name][taller]
            # the places the page keeps, as his next act saves them, read as the PETs table and the PDF read them
            saved = json.loads(json.dumps(boards[name]))
            for k, (x, y) in r["at"].items():
                saved["cards"][k].update(x=x, y=y)
            for g in saved["groups"]:
                if g["id"] in r["labels"]:
                    g["x"], g["y"] = r["labels"][g["id"]]
            server_reads = orders(saved) == orders(boards[name])
            check(f"371: {name}, the page open on the board takes the change with its cards "
                  + ("at the server's sizes" if taller == "0" else "forty pixels taller than the server's")
                  + ": the places it keeps for the file read every PET, sub-PET and the PETs as the agent left them, "
                  "on the page and on the server, "
                  "nothing overlaps, nothing is saved by itself"
                  + (", and nothing moves" if taller == "0" else ""),
                  r["want"] == r["got"] and server_reads and not r["clash"] and not r["saved"] and not r["dirty"]
                  and (taller != "0" or not r["moved"]),
                  {k: r[k] for k in ("clash", "moved", "saved", "dirty")} | {"server_reads": server_reads}
                  | ({"want": r["want"], "got": r["got"]} if r["want"] != r["got"] else {}))
