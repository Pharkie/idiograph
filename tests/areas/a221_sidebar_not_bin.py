from __future__ import annotations

import datetime as dt
import json
import shutil
import subprocess
import sys

import openpyxl

from . import support
from .support import check as said_check, skip


def check(name, ok, detail=""):
    said_check(name, ok, str(detail)[:600])

# An invented study of learning the cello as an adult, Tamsin the participant and Ivo asking, every word made
# up. Each row is (speaker, time, statements), a statement cell's entries split by a blank line.
ROWS = [
    ("Ivo", "00:01:00", None),
    ("Tamsin", "00:01:10", "Practising before work as a promise to herself"),
    ("Tamsin", "00:02:30", "The first scale that sounded like music"),
    ("Tamsin", "00:04:05", "Embarrassed by the sound in a quiet flat"),
    ("Tamsin", "00:06:40", "Her teacher's patience as permission to be slow"),
    ("Tamsin", "00:08:15", "The cello as company in the evenings"),
    ("Tamsin", "00:09:50", "Sore fingers taken as proof of work"),
]
HEAD = ["Name", "Timestamp", "Experiential statements", "Transcript", "Exploratory notes", "Key quotes"]


def made_book(path) -> None:
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Initial"
    ws.append(HEAD)
    for speaker, at, said in ROWS:
        ws.append([speaker, dt.time(*map(int, at.split(":"))), said, f"{speaker} says something about the cello.",
                   "Music as company." if said else None, None])
    wb.save(path)


def test_sidebar_not_bin(scratch):
    print("\n221. The boards' sidebar in place of the bin (Adam, 20 October, way A): an old board's binned cards open "
          "as Set aside and save back the same, a card in no PET waits in Not placed unless it lies loose on the "
          "canvas, Take out and Backspace send a card to Not placed and X to Set aside, both starts of a new board, "
          "Put all on the board, Select all, and the bin's old names still answering on the command line and MCP")
    import mcp_server
    import themes

    root = scratch / "sidebar-root"
    shutil.rmtree(root, ignore_errors=True)
    (root / "Tamsin" / "Working").mkdir(parents=True)
    book = root / "Tamsin" / "Tamsin - EN & ES.xlsx"
    made_book(book)
    (root / "idiograph-project.json").write_text(json.dumps({
        "name": "Cello, a sidebar project", "agents": {"allowed": True, "at": "2026-10-20T21:00:00+01:00"}}), encoding="utf-8")
    cfg = scratch / "sidebar-config.json"
    cfg.write_text(json.dumps({"root": str(root), "interviewer": "Ivo"}), encoding="utf-8")
    read = themes.read_cards(book)
    k = [c["key"] for c in read["cards"]]
    check("221: the invented workbook reads six statements", len(k) == 6, k)

    # ── A. an old board, as the file held it before 20 October: a binned card, two cards in no PET
    old = {"id": "v1", "name": "Board 1", "cards": {key: {"x": i * 210, "y": 0, "text": c["text"]}
                                                    for i, (key, c) in enumerate(zip(k, read["cards"]))},
           "groups": [{"id": "g1", "label": "Practice as a promise", "members": [k[0], k[1], k[3]], "x": 0, "y": -40}],
           "discarded": [k[2]], "picks": {}}
    themes.save(book, old, "Tamsin")
    st = themes.state(book, "Tamsin")
    check("221: an old board's binned card opens set aside, kept under `discarded`", st["discarded"] == [k[2]], st["discarded"])
    check("221: an old board's cards in no PET carry no `loose`, so they wait in the sidebar's Not placed",
          not any(c.get("loose") for c in st["cards"]), [c for c in st["cards"] if c.get("loose")])
    check("221: what waits is in no PET, not set aside, in interview order", themes.waiting_keys(themes.load(book)["boards"][0]) == [k[4], k[5]],
          themes.waiting_keys(themes.load(book)["boards"][0]))
    raw = json.loads(themes.themes_path(book).read_text(encoding="utf-8"))["boards"][0]
    themes.save(book, dict(raw), "Tamsin")
    again = json.loads(themes.themes_path(book).read_text(encoding="utf-8"))["boards"][0]
    check("221: an old board saved back holds the same set aside and no `loose`, as it read",
          again["discarded"] == [k[2]] and not any("loose" in c for c in again["cards"].values()), again["discarded"])

    # a card put loose on the canvas is kept, and one in a PET never carries `loose`
    loose = support.plain(json.loads(json.dumps(again)))
    loose["cards"][k[4]]["loose"] = True
    loose["cards"][k[0]]["loose"] = True
    themes.save(book, loose, "Tamsin")
    kept = json.loads(themes.themes_path(book).read_text(encoding="utf-8"))["boards"][0]
    st = themes.state(book, "Tamsin")
    check("221: a card loose on the canvas is kept loose, and the open sends it so",
          kept["cards"][k[4]].get("loose") is True and next(c for c in st["cards"] if c["key"] == k[4]).get("loose") is True,
          kept["cards"][k[4]])
    check("221: a card in a PET never carries `loose`", "loose" not in kept["cards"][k[0]], kept["cards"][k[0]])

    # ── B. both starts of a new board, through the board op the board menu sends
    made = themes.version_op(book, "new", {"start": "canvas"}, "Tamsin")
    canvas = themes.current_version(themes.load(book))
    check("221: New board, all on the canvas: every statement loose, no PET, nothing set aside",
          all(c.get("loose") for c in canvas["cards"].values()) and not canvas["groups"] and not canvas["discarded"], made["current"])
    themes.version_op(book, "new", {}, "Tamsin")
    empty = themes.current_version(themes.load(book))
    check("221: New board, empty: every statement waiting in the sidebar",
          themes.waiting_keys(empty) == k, themes.waiting_keys(empty))

    # ── C. the command line and MCP: set aside, put back, put all on the board, a new board's start, the old names
    def cli(*words):
        ran = subprocess.run([sys.executable, str(support.source("cli.py")), "--root", str(root), "--config", str(cfg), *words],
                             capture_output=True, text=True, encoding="utf-8", timeout=120)
        try:
            return support.plain(json.loads(ran.stdout)), ran
        except ValueError:
            return {}, ran

    def apply(ops, note="As he asked"):
        path = scratch / "sidebar-ops.json"
        path.write_text(json.dumps(ops), encoding="utf-8")
        return cli("board", "apply", "Tamsin", "v1", "--note", note, "--tool", "Claude Code", "--ops", str(path), "--json")

    themes.version_op(book, "switch", {"id": "v1"}, "Tamsin")
    out, ran = apply([{"op": "set_aside", "items": [k[5]]}])
    v1 = themes.find_version(themes.load(book), "v1")
    check("221: board apply's set_aside sets a statement aside", k[5] in v1["discarded"], (out, ran.stderr[:300]))
    out, ran = apply([{"op": "bin", "items": [k[3]]}, {"op": "discard", "items": [k[1]]}])
    v1 = themes.find_version(themes.load(book), "v1")
    check("221: the bin's old names, bin and discard, still answer, as set_aside",
          k[3] in v1["discarded"] and k[1] in v1["discarded"] and k[3] not in v1["groups"][0]["members"], (out, ran.stderr[:300]))
    out, ran = apply([{"op": "put_back", "items": [k[5]]}])
    v1 = themes.find_version(themes.load(book), "v1")
    check("221: put_back takes a statement out of Set aside to wait in Not placed",
          k[5] not in v1["discarded"] and k[5] in themes.waiting_keys(v1), (out, ran.stderr[:300]))
    out, ran = apply([{"op": "put_all_on"}])
    v1 = themes.find_version(themes.load(book), "v1")
    check("221: put_all_on puts every statement waiting on the canvas, loose", not themes.waiting_keys(v1)
          and v1["cards"][k[5]].get("loose") is True, (out, ran.stderr[:300]))
    shown, ran = cli("board", "show", "Tamsin", "v1", "--json")
    check("221: board show names Set aside and marks a loose statement",
          {s["key"] for s in shown.get("set_aside", [])} == set(v1["discarded"])
          and any(s.get("loose") for s in shown.get("unplaced", [])), ran.stderr[:300])
    out, ran = cli("board", "fresh", "Tamsin", "--start", "canvas", "--note", "A board to try", "--tool", "Claude Code", "--json")
    now = themes.current_version(themes.load(book))
    check("221: board fresh --start canvas makes a board with every statement on the canvas, put on the canvas",
          out.get("start") == "canvas" and all(c.get("loose") for c in now["cards"].values()), (out, ran.stderr[:300]))
    tools = {t["name"]: t for t in mcp_server.TOOLS}
    check("221: MCP has board_fresh", "board_fresh" in tools, sorted(tools)[:5])
    args = mcp_server.arguments(tools["board_fresh"], {"case": "Tamsin", "start": "canvas"}, {"root": str(root), "config": str(cfg)}, "test")
    check("221: MCP board_fresh passes its start", args.start == "canvas" and args.act == "fresh", vars(args))
    for name in ("set_aside", "binned"):
        args = mcp_server.arguments(tools["board_export"], {"case": "Tamsin", name: True}, {"root": str(root), "config": str(cfg)}, "test")
        check(f"221: MCP board_export takes {name} for the statements set aside", args.binned is True, vars(args))

    # ── D. the page's model in node: Take out, Backspace, X, the order, a drop, Put all on the board, Select all
    node = shutil.which("node")
    if not node:
        skip("221: the sidebar's model in node", "node is not installed")
        return
    js = support.text("apps/idiograph/static/themes.js")
    script = scratch / "sidebar-model.js"
    script.write_text(support.i18n_js() + """
globalThis.$ = (id) => (id === 'th-stage' ? { getBoundingClientRect: () => ({ left: 0, top: 0, width: 800, height: 600, right: 800, bottom: 600 }) } : null);
globalThis.esc = (s) => String(s);
globalThis.escAttr = (s) => String(s);
globalThis.say = () => {};
globalThis.MOD = (e) => !!(e && e.metaKey);
""" + js + r"""
const out = {};
thRender = () => {}; thEase = () => {}; thSoon = () => {}; thInspectorOpen = () => {}; thPanelFollow = () => {};
thSettle = () => false; thFlash = () => {}; thListDraw = () => {}; thSideFlash = () => {}; thDrawSel = () => {};

thToWorld = (x, y) => ({ x, y }); thTargetAt = () => null; thFit = () => {};
TH.mode = 'pets'; TH.live = true; TH.layout = {}; TH.sheets = ['Initial', 'Follow-up'];
const card = (key, extra = {}) => Object.assign({ key, sheet: key.split(':')[0], row: Number(key.split(':')[1]), line: Number(key.split(':')[2]), x: 0, y: 0, text: key }, extra);
const keys = ['Initial:2:0', 'Initial:3:0', 'Initial:4:0', 'Initial:5:0', 'Follow-up:2:0', 'Initial:9:0', 'Initial:7:0'];
const data = { cards: keys.map((k) => card(k, k === 'Initial:9:0' ? { missing: true } : k === 'Initial:7:0' ? { loose: true } : {})),
  groups: [{ id: 'g1', label: 'Practice', members: ['Initial:2:0', 'Initial:3:0'] }], discarded: ['Initial:4:0'], picks: {},
  stacks: { 'Follow-up:2:0': ['Initial:5:0'] }, not_same: [], stickies: [] };
const cards = {}; for (const c of data.cards) cards[c.key] = Object.assign({}, c);
const v = { cards, groups: data.groups, discarded: data.discarded.slice(), picks: {}, stacks: data.stacks, not_same: [], stickies: [], waits: true };
thWaitsRead(v);
TH.v = v;
TH.sel = { cards: new Set(), groups: new Set(), stickies: new Set() };
out.read = { waiting: thWaitingKeys(v, TH.sheets), loose: thOnCanvas(v, 'Initial:7:0'), aside: v.discarded };
// a stack waits as one row at its top, a statement missing from the workbook last
// Take out of PET and Backspace: back to Not placed
TH.sel.cards = new Set(['Initial:2:0']);
thDeleteKey();
out.backspace = { waiting: thWaiting(v, 'Initial:2:0'), onCanvas: thOnCanvas(v, 'Initial:2:0'), inPet: v.groups[0].members.includes('Initial:2:0') };
thMenuChoose = null;
out.takeOut = thLeaveThemes(['Initial:3:0']) && thWaiting(v, 'Initial:3:0');
// Backspace on a card loose on the canvas sends it back too
TH.sel.cards = new Set(['Initial:7:0']);
thDeleteKey();
out.looseBack = thWaiting(v, 'Initial:7:0');
// X sets aside
TH.sel.cards = new Set(['Initial:7:0']);
thPutOn(v, 'Initial:7:0', 10, 10);
TH.sel.cards = new Set(['Initial:7:0']);
thDiscardKey();
out.x = { aside: v.discarded.includes('Initial:7:0'), waiting: thWaiting(v, 'Initial:7:0'), onCanvas: thOnCanvas(v, 'Initial:7:0') };
out.order = thWaitingKeys(v, TH.sheets);
// rows dropped on the canvas lie there loose, and X's statement put back waits in Not placed
thSideDrop(['Initial:2:0', 'Initial:3:0'], 100, 100);
out.drop = { onCanvas: thOnCanvas(v, 'Initial:2:0') && thOnCanvas(v, 'Initial:3:0'), selected: [...TH.sel.cards] };
thSideBack('Initial:7:0');
out.putBack = thWaiting(v, 'Initial:7:0');
// Put all on the board: every statement waiting but the missing one
thSideAll();
out.all = { waiting: thWaitingKeys(v, TH.sheets), loose: ['Initial:7:0', 'Follow-up:2:0'].every((k) => thOnCanvas(v, k)) };
// Select all on the canvas: every statement on it
TH.face = 'canvas'; TH.sideLast = false;
thSelectAll();
out.selectAll = [...TH.sel.cards].sort();
out.onCanvas = Object.keys(v.cards).filter((k) => thOnCanvas(v, k)).sort();
// and in the sidebar's section pressed last
TH.ssel = new Set(); TH.sideLast = true; TH.casesOpen = true; TH.ssec = 'aside';
thSideSelectAll();
out.sideAll = [...TH.ssel];
// the save keeps loose for a card on the canvas in no PET, and none for one waiting
TH.stackable = true; TH.pairable = true;
const body = thBody(v, { id: 'v1', name: 'Board 1' });
out.body = { loose: body.cards['Initial:7:0'].loose === true, waitingMissing: body.cards['Initial:9:0'].loose === undefined, aside: body.discarded };
console.log(JSON.stringify(out));
""", encoding="utf-8")
    ran = subprocess.run([node, str(script)], capture_output=True, text=True, encoding="utf-8", timeout=60)
    try:
        o = support.plain(json.loads(ran.stdout.strip().splitlines()[-1]))
    except (ValueError, IndexError):
        o = {}
    said = (ran.stdout + ran.stderr)[:800]
    check("221: the page reads a card in no PET as waiting, a loose one as on the canvas, the bin's as set aside",
          o.get("read") == {"waiting": ["Follow-up:2:0", "Initial:9:0"], "loose": True, "aside": ["Initial:4:0"]}, said)
    check("221: Backspace sends a card in a PET to Not placed, off the canvas and out of its PET",
          o.get("backspace") == {"waiting": True, "onCanvas": False, "inPet": False}, said)
    check("221: Take out of PET sends a card to Not placed", o.get("takeOut") is True, said)
    check("221: Backspace sends a card loose on the canvas back to Not placed", o.get("looseBack") is True, said)
    check("221: X sets a card aside, off the canvas and out of Not placed",
          o.get("x") == {"aside": True, "waiting": False, "onCanvas": False}, said)
    check("221: Not placed reads in interview order, a stack at its top's time, one missing from the workbook last",
          o.get("order") == ["Initial:2:0", "Initial:3:0", "Follow-up:2:0", "Initial:9:0"], said)
    check("221: rows dropped on the canvas lie there, selected", (o.get("drop") or {}).get("onCanvas") is True
          and sorted((o.get("drop") or {}).get("selected") or []) == ["Initial:2:0", "Initial:3:0"], said)
    check("221: Put back from Set aside waits in Not placed", o.get("putBack") is True, said)
    check("221: Put all on the board puts every statement waiting on the canvas, the missing one left",
          o.get("all") == {"waiting": ["Initial:9:0"], "loose": True}, said)
    check("221: Select all selects every statement on the canvas", o.get("selectAll") == o.get("onCanvas") and o.get("selectAll"), said)
    check("221: Cmd + A in the sidebar selects the section pressed last", o.get("sideAll") == ["Initial:4:0"], said)
    check("221: the save sends loose for a card on the canvas in no PET and none for one waiting",
          (o.get("body") or {}).get("loose") is True and (o.get("body") or {}).get("waitingMissing") is True, said)
