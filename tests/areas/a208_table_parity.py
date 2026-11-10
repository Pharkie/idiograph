"""Area 208: the Table view does everything the canvas does, way 1 (20 October 2026).

Adam, 20 October about 00:25: the table self-sufficient, everything done one way or another with keys, the
mouse, drags or buttons, so that anything done on the canvas can be done in the table and the other way
round. At about 01:00 he chose way 1: the canvas's own keys, palette and menus work on the table's rows,
nothing new to learn. The selection is the board's, so the canvas shows what the table selected. G puts a
label over the rows selected, its title open, and with nothing selected makes a new empty PET at the end;
New group inside on a PET's, a sub-theme's or a GET's menu makes an empty one inside it, a GET's
sub-theme a row of the GET table, and a Cases panel row let go on the GET table goes under the GET it lands on. Statements dragged
together come in together, a drop on a title strip merges into it, Backspace takes a statement back to Not
placed, X bins it and the table's own Binned list puts it back, and S stacks under the one that reads
first. Each is one step of the board's undo. An agent makes an empty label with `make` and no members, as
G and New group inside do, with a dry run.

The checks pin behaviour, on an invented board about keeping bees: in node, the page's own code with the
server's reorder route answering, and the API through the command line and MCP on a scratch copy of the
demo. No string, colour or pixel is pinned.
"""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys

from . import support
from .support import TOOL, check, skip
import idiograph_routes

# a board about keeping bees: PET g1 holding sub-PET g2 and two statements of its own, PET g3 beside it with
# three, and two statements in no PET
CARDS = {
    "Initial:3:0": (40, 120, "Smoke calming the hive"),
    "Initial:5:0": (270, 120, "Stung through the glove"),
    "Initial:7:0": (60, 300, "The hum changing before a swarm"),
    "Initial:9:0": (290, 300, "Counting frames of brood"),
    "Initial:11:0": (40, 520, "Honey on the kitchen floor"),
    "Initial:13:0": (700, 80, "A neighbour asking for a jar"),
    "Initial:15:0": (700, 220, "Telling people it is safe"),
    "Initial:17:0": (700, 360, "Bees on the washing line"),
    "Initial:19:0": (40, 900, "The suit hanging in the shed"),
    "Initial:21:0": (300, 900, "A queen marked in blue"),
}
GROUPS = [
    {"id": "g1", "label": "Learning the hive's moods", "members": ["Initial:3:0", "Initial:5:0", "g2"], "x": 20, "y": 60},
    {"id": "g2", "label": "Reading the colony", "members": ["Initial:7:0", "Initial:9:0"], "x": 40, "y": 260},
    {"id": "g3", "label": "Bees and the neighbours", "members": ["Initial:13:0", "Initial:15:0", "Initial:17:0"], "x": 700, "y": 40},
]

ROUTE = r"""
import json, sys
sys.path.insert(0, sys.argv[1])
import boot
boot.setup()
import idiograph_routes
print(json.dumps(idiograph_routes.api_board_order(json.loads(sys.stdin.read()))))
"""


def test_table_parity(scratch):
    print("\n208. The Table view does what the canvas does: the selection shared, G on rows and with none, New group "
          "inside, ungroup, merge, back to Not placed, several rows dragged, the bin, stacks, each one step of undo, "
          "and an empty label through the API, 20 October, with New group inside on GETs, a GET's sub-theme a row of the GET "
          "table and a Cases panel row dropped on it (tableparity2)")
    _api(scratch)
    node = shutil.which("node")
    if not node:
        skip("208: the table in node", "node is not installed")
        return
    board = {"id": "v1", "name": "Board 1", "note": "", "created": "2026-10-20T09:00:00+01:00",
             "updated": "2026-10-20T09:00:00+01:00", "discarded": [], "picks": {}, "notes": [],
             "cards": {k: {"x": x, "y": y, "text": t} for k, (x, y, t) in CARDS.items()},
             "groups": support.plain(json.loads(json.dumps(GROUPS)))}
    route = scratch / "table-parity-route-208.py"
    route.write_text(ROUTE, encoding="utf-8")
    js = support.text("apps/idiograph/static/themes.js")
    script = scratch / "table-parity-208.js"
    script.write_text(support.i18n_js() + STUBS + js + SCENARIO, encoding="utf-8")
    env = dict(os.environ, TP_PY=sys.executable, TP_ROUTE=str(route), TP_TOOL=str(TOOL), TP_BOARD=json.dumps(board))
    run = subprocess.run([node, str(script)], capture_output=True, text=True, encoding="utf-8", timeout=180, env=env)
    if run.returncode != 0:
        check("208: the table runs in node", False, (run.stderr or run.stdout).strip()[:900])
        return
    o = support.plain(json.loads(run.stdout))

    s = o["select"]
    check("208: in node, a click on a row selects it alone, Cmd adds one, Shift adds the run between, and the selection "
          "is the board's: the canvas's cards show selected, and Esc's clear empties it",
          s["one"] == ["Initial:3:0"] and s["cmd"] == ["Initial:3:0", "Initial:13:0"]
          and s["run"] == ["Initial:13:0", "Initial:15:0", "Initial:17:0"] and s["canvas"] == s["run"]
          and s["label"] == ["g3"] and s["cleared"] == 0, json.dumps(s))

    g = o["group"]
    check("208: in node, G on two statements of a PET puts a sub-PET over them inside it, its title box open in the "
          "table, the title typed kept, the letters following, one step of undo, Made a theme",
          g["open"] and g["parent"] == "g1" and g["members"] == ["Initial:3:0", "Initial:5:0"] and g["label"] == "Calm hands"
          and g["steps"] == 1 and g["what"] == "Made a theme" and g["codes"] == ["A", "A1", "A2", "B"], json.dumps(g))
    check("208: in node, undo of it takes the sub-PET away and puts the statements back in the PET",
          g["undone"] == {"gone": True, "back": True}, json.dumps(g["undone"]))

    e = o["empty"]
    check("208: in node, G with nothing selected makes a new empty PET, last in the table, its title box open, one step "
          "of undo, and undo takes it away",
          e["empty"] and e["top"] and e["last"] and e["label"] == "Swarm season" and e["steps"] == 1 and e["undone"],
          json.dumps(e))
    n = o["inside"]
    check("208: in node, New group inside is on a PET's menu and a sub-PET's, and makes an empty label inside it, last "
          "there, one step of undo",
          n["menu"] and n["parent"] == "g2" and n["empty"] and n["last"] and n["steps"] == 1 and n["undone"], json.dumps(n))

    u = o["ungroup"]
    check("208: in node, Delete this label on a sub-PET keeps what it held, in the PET in its place, one step of undo",
          u["gone"] and u["held"] and u["steps"] == 1 and u["undone"], json.dumps(u))
    m = o["merge"]
    check("208: in node, a PET dropped on another's title strip goes inside it with all it holds, one step of undo, "
          "and statements dropped there join it at its end",
          m["nested"] == "g3" and m["kept"] and m["steps"] == 1 and m["undone"] and m["joined"] == "g3" and m["end"],
          json.dumps(m))
    b = o["back"]
    check("208: in node, Backspace on a statement takes it out of its PET to Not placed, one step of undo, and on a "
          "statement already there leaves it",
          b["loose"] and b["steps"] == 1 and b["undone"] and b["again"] == 1, json.dumps(b))
    d = o["drag"]
    check("208: in node, two statements dragged together from one PET into another come in together at the place let "
          "go, in the order they read, saved, one step of undo, and undo puts both back",
          d["order"] == ["Initial:13:0", "Initial:3:0", "Initial:5:0", "Initial:15:0", "Initial:17:0"] and d["saved"]
          and d["steps"] == 1 and d["undone"], json.dumps(d))
    x = o["bin"]
    check("208: in node, X bins the statements selected, the table lists them under Binned with Put back, and Put back "
          "brings one to Not placed, each one step of undo",
          x["binned"] and x["listed"] and x["back"] and x["steps"] == 2 and x["undone"], json.dumps(x))
    w = o["words"]
    check("208: in node, a Shift, Cmd or right click and a double-click on a row select none of its words, while a "
          "plain click and a press in a title box keep the browser's own",
          w["shift"] and w["cmd"] and w["right"] and w["twice"] and not w["plain"] and not w["box"], json.dumps(w))
    t = o["gets"]
    check("208: in node, New group inside is on a GET's menu and a GET sub-theme's, makes an empty sub-theme inside the "
          "GET, its title box open in the table, one step of undo, and the GET table shows it as a row under its GET",
          t["menu"] and t["subMenu"] and t["open"] and t["parent"] == "G1" and t["empty"]
          and t["label"] == "Stings in the first summer" and t["steps"] == 1 and t["row"] and t["flat"], json.dumps(t))
    check("208: in node, a card dropped on the sub-theme's title strip in the GET table goes inside it, its row saying so, "
          "and undo of the two steps puts the GET back as it was",
          t["filled"] and t["undone"], json.dumps(t))
    q = o["pull"]
    check("208: in node, a Cases panel row let go on a GET in the table brings its card in under that GET, selected, one "
          "step of undo, Brought a card in, and undo takes it away",
          q["joined"] and q["steps"] == 1 and q["what"] == "Brought a card in" and q["selected"] and q["undone"], json.dumps(q))
    check("208: in node, a row whose card is there already moves it, into Not placed over that list, out of the bin onto a "
          "GET, each one step, and let go where it is already changes nothing",
          q["loose"] and q["unbinned"] and q["same"], json.dumps(q))
    k = o["stack"]
    check("208: in node, S on three statements stacks two under the one that reads first in the table, one step of "
          "undo, the stack's rows shown under its top when opened, and undo unstacks them",
          k["top"] == "Initial:13:0" and k["under"] == ["Initial:15:0", "Initial:17:0"] and k["steps"] == 1
          and k["shown"] and k["undone"], json.dumps(k))


def _api(scratch):
    """`make` with no members through the command line, dry run first, and through MCP."""
    import cli
    import mcp_server
    import server as server_mod
    import themes

    pristine = support.DEMO_PRISTINE
    root = scratch / "table-parity-root"
    shutil.rmtree(root, ignore_errors=True)
    for name in ("Juno", "Rowan", "Mabel"):
        (root / name / "Working").mkdir(parents=True)
        shutil.copy2(pristine / f"{name} - EN & ES.xlsx", root / name / f"{name} - EN & ES.xlsx")
        for side in (pristine / "Working").glob(f"{name} - *"):
            shutil.copy2(side, root / name / "Working" / side.name)
    case = root / "Rowan"
    (root / server_mod.PROJECT_FILE).write_text(json.dumps({
        "name": "Dogs, a scratch project", "agents": {"allowed": True, "at": "2026-10-20T09:00:00+01:00"}}), encoding="utf-8")
    config_file = scratch / "table-parity-config.json"
    config_file.write_text(json.dumps({"root": str(root), "interviewer": "Adam"}), encoding="utf-8")
    themes_file = themes.themes_path(case / "Rowan - EN & ES.xlsx")
    kept = (server_mod.CONFIG_PATH, server_mod.ROOT_OVERRIDE, server_mod.STATE_MEMORY)
    try:
        def answer(*args):
            code, out, err = cli.run(["--root", str(root), "--config", str(config_file), *args, "--json"])
            return code, (support.plain(json.loads(out)) if out.strip() else {}), err

        start = json.loads(themes_file.read_text(encoding="utf-8"))
        sub = next(g["id"] for g in start["boards"][0]["groups"]
                   if any(g["id"] in o["members"] for o in start["boards"][0]["groups"]))
        spec = scratch / "table-parity-ops.json"
        spec.write_text(json.dumps({"operations": [
            {"op": "make", "title": "Walks at the edges of the day", "inside": None},
            {"op": "make", "title": "Watching the road", "inside": sub, "members": []}]}), encoding="utf-8")
        raw = themes_file.read_bytes()
        code, dry, err = answer("board", "apply", "Rowan", "v1", "--ops", str(spec), "--note", "Two empty labels",
                                "--tool", "Claude Code", "--dry-run")
        check("208: make with no members has a dry run that writes nothing and says it makes empty labels",
              code == 0 and dry.get("dry_run") is True and themes_file.read_bytes() == raw
              and dry.get("said", "").count("empty label") == 2, err or json.dumps(dry)[:300])
        code, done, err = answer("board", "apply", "Rowan", "v1", "--ops", str(spec), "--note", "Two empty labels",
                                 "--tool", "Claude Code")
        after = next(b for b in json.loads(themes_file.read_text(encoding="utf-8"))["boards"] if b["id"] == "v1")
        by_title = {g["label"]: g for g in after["groups"]}
        parents = {m: g["id"] for g in after["groups"] for m in g["members"]}
        pet, inner = by_title.get("Walks at the edges of the day"), by_title.get("Watching the road")
        check("208: applied, an empty PET at the top of the board and an empty group inside the sub-PET, saved",
              code == 0 and pet and inner and not pet["members"] and not inner["members"]
              and pet["id"] not in parents and parents.get(inner["id"]) == sub, err or json.dumps(after["groups"])[-400:])

        srv = mcp_server.Server(str(root), config=str(config_file))
        srv.receive(json.dumps({"jsonrpc": "2.0", "id": 1, "method": "initialize",
                                "params": {"protocolVersion": "2025-06-18", "clientInfo": {"name": "claude-code"}}}))
        res = srv.receive(json.dumps({"jsonrpc": "2.0", "id": 2, "method": "tools/call", "params": {
            "name": "board_apply", "arguments": {"case": "Rowan", "board": "v1", "request": "One more empty PET",
                                                 "dry_run": True, "operations": [{"op": "make", "title": "Late hives"}]}}}))["result"]
        check("208: through MCP board_apply's dry run makes an empty label too",
              not res["isError"] and "empty label" in json.dumps(support.plain(res["structuredContent"])), json.dumps(res)[:300])

        # New group inside on a GET: gets apply's make with no members inside a GET, a dry run first
        import gets as gets_mod
        server_mod.ROOT_OVERRIDE = str(root)
        server_mod.STATE_MEMORY = {"recent": []}
        books = [{"case": n, "workbook": str(root / n / f"{n} - EN & ES.xlsx")} for n in ("Juno", "Rowan", "Mabel")]
        data_g, _, _, _ = gets_mod.assemble(root, books, themes.now_iso())
        gets_mod.write(root, gets_mod._file(data_g, themes.now_iso()))
        shown = idiograph_routes.api_gets({"workbook": books[0]["workbook"]})
        keys = [c["key"] for c in shown["cards"]]
        body = dict(shown["version"], cards={c["key"]: {"x": c["x"], "y": c["y"], "text": c.get("text") or ""} for c in shown["cards"]},
                    groups=[{"id": "G1", "label": "Walks with a dog", "members": keys[:2], "x": 0, "y": 0}],
                    discarded=list(shown["discarded"]), picks={}, notes=[])
        took = idiograph_routes.api_gets_save({"workbook": books[0]["workbook"], "version": body})
        gfile = gets_mod.gets_path(root)
        gspec = scratch / "table-parity-gets-ops.json"
        gspec.write_text(json.dumps({"operations": [{"op": "make", "title": "At the edges of the day", "inside": "G1"}]}),
                         encoding="utf-8")
        held = gfile.read_bytes()
        code, gdry, err = answer("gets", "apply", "b1", "--ops", str(gspec), "--note", "A sub-theme to fill", "--dry-run")
        check("208: gets apply's make with no members inside a GET has a dry run that writes nothing and says it makes an "
              "empty label",
              took.get("saved") and code == 0 and gfile.read_bytes() == held and "empty label" in gdry.get("said", ""),
              err or json.dumps(gdry)[:300])
        code, _, err = answer("gets", "apply", "b1", "--ops", str(gspec), "--note", "A sub-theme to fill", "--tool", "Claude Code")
        gb = gets_mod.load(root)["boards"][0]
        made = next((g for g in gb["groups"] if g["label"] == "At the edges of the day"), None)
        g1 = next((g for g in gb["groups"] if g["id"] == "G1"), {"members": []})
        check("208: applied, the GET holds an empty sub-theme beside the cards it held, saved",
              code == 0 and made and not made["members"] and made["id"] in g1["members"]
              and all(k in g1["members"] for k in keys[:2]), err or json.dumps(gb["groups"])[:400])
    finally:
        server_mod.CONFIG_PATH, server_mod.ROOT_OVERRIDE, server_mod.STATE_MEMORY = kept


STUBS = r"""
// the page as the table meets it: any element asked for is made on the way, the canvas never booted
const { execFileSync } = require('child_process');
const ELS = {};
class El {
  constructor(id) {
    this.id = id; this.cls = new Set(); this.attrs = {}; this.hidden = false; this._html = ''; this.textContent = '';
    this.dataset = {}; this.value = ''; this.scrollTop = 0; this.offsetWidth = 0; this.offsetHeight = 0;
    const self = this;
    this.style = { setProperty: () => {} };
    this.classList = { add: (...n) => n.forEach((x) => self.cls.add(x)), remove: (...n) => n.forEach((x) => self.cls.delete(x)),
      contains: (n) => self.cls.has(n),
      toggle: (n, on) => { if (on === undefined) on = !self.cls.has(n); if (on) self.cls.add(n); else self.cls.delete(n); return on; } };
  }
  set innerHTML(v) { this._html = v; }
  get innerHTML() { return this._html; }
  setAttribute(k, v) { this.attrs[k] = String(v); }
  getAttribute(k) { return this.attrs[k]; }
  removeAttribute(k) { delete this.attrs[k]; }
  getBoundingClientRect() { return { left: 0, top: 0, width: 0, height: 0, right: 0, bottom: 0 }; }
  querySelector() { return null; }
  querySelectorAll() { return []; }
  addEventListener() {}
  contains() { return false; }
  closest() { return null; }
  focus() {}
  pause() {}
  setSelectionRange() {}
}
const $ = (id) => (id === 'th-stage' ? null : (ELS[id] = ELS[id] || new El(id)));
const esc = (s) => String(s).replace(/[&<>]/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;' }[c]));
const escAttr = (s) => esc(s).replace(/"/g, '&quot;');
const SAID = [];
const say = (t) => SAID.push(t);
const MOD = (e) => !!(e.metaKey || e.ctrlKey);
const REDO_Y = () => false;
const RESTART_LINE = 'Restart';
const needsRestart = () => false;
const cheerOn = () => false;
const confetti = () => {};
const fileOf = (p) => String(p).split('/').pop();
const STORE = new Map();
globalThis.localStorage = { getItem: (k) => (STORE.has(k) ? STORE.get(k) : null), setItem: (k, v) => STORE.set(k, String(v)),
  removeItem: (k) => STORE.delete(k) };
globalThis.window = { innerWidth: 1280, innerHeight: 800, matchMedia: () => ({ matches: true }), open: () => null };
let FRAMES = [];
globalThis.requestAnimationFrame = (fn) => { FRAMES.push(fn); return FRAMES.length; };
globalThis.cancelAnimationFrame = () => {};
globalThis.setTimeout = () => 0;
globalThis.clearTimeout = () => {};
globalThis.getComputedStyle = () => ({ getPropertyValue: () => '' });
globalThis.document = { activeElement: null };
const api = async (path, body) => {
  if (path !== '/api/board-order') throw new Error(`no ${path} here`);
  const out = execFileSync(process.env.TP_PY, [process.env.TP_ROUTE, process.env.TP_TOOL], { input: JSON.stringify(body), encoding: 'utf8' });
  return JSON.parse(out);
};
"""

SCENARIO = r"""
;(async () => {
  const out = {};
  const settle = async () => { for (let i = 0; i < 40 && TH.busy; i += 1) await new Promise((r) => setImmediate(r)); await new Promise((r) => setImmediate(r)); };
  const fresh = () => {
    const b = JSON.parse(process.env.TP_BOARD);
    const cards = {};
    for (const [k, c] of Object.entries(b.cards)) cards[k] = Object.assign({ sheet: 'Initial', row: Number(k.split(':')[1]), line: 0, time: '00:10' }, c);
    TH.v = { cards, groups: b.groups, discarded: [], picks: {}, ai: { discarded: {} }, review: null, stickies: [], revise: null, stacks: {} };
    TH.meta = { id: b.id, name: b.name, note: '', created: b.created, updated: b.updated };
    TH.path = 'Hive/Hive - EN.xlsx';
    TH.live = true; TH.busy = false; TH.mode = 'pets'; TH.undo = []; TH.redo = []; TH.removed = new Set();
    TH.sel = { cards: new Set(), groups: new Set(), stickies: new Set() };
    // the canvas's own cards, so its selection can be seen
    TH.els = { cards: {}, labels: {}, frames: {}, stickies: {}, under: {} };
    for (const k of Object.keys(cards)) TH.els.cards[k] = new El(k);
    TH.project = { pet_labels: 'letters' }; TH.sheets = ['Initial']; TH.quotes = {};
    TH.dirty = false; TH.saveTimer = null; TH.chain = null; TH.face = 'table'; TH.opened = new Set(); TH.stackable = true;
    TH.tedit = null; TH.tanchor = null; TH.panelOpen = false;
    TH.z = Object.keys(cards);
    thRender();
  };
  thMeasure = function () {
    TH.sizes = {};
    for (const k of Object.keys(TH.v.cards)) TH.sizes[k] = { w: 200, h: 80 };
    for (const g of TH.v.groups) TH.sizes[g.id] = { w: 140, h: 30 };
  };
  thRender = function () { thMeasure(); thPlace(); };
  thMapMoved = () => {};
  const parentOf = (k) => thParents(TH.v)[k];
  const sel = () => [...TH.sel.cards];
  const codes = () => {
    const list = [];
    const walk = (n) => { list.push(n.code); for (const it of n.items) if (it.kind === 'label') walk(it.node); };
    thTableTree(TH.v, TH.layout, true, TH.sheets).pets.forEach(walk);
    return list;
  };
  const snapOf = () => JSON.stringify(thBody(TH.v, TH.meta).groups.map((g) => [g.id, g.members]));
  const typeTitle = (text) => { $('tb-title-box').value = text; thTableTitleDone(true); };

  // ── the selection, shared with the canvas
  fresh();
  thTableSelect('Initial:3:0', 'statement');
  const one = sel();
  thTableSelect('Initial:13:0', 'statement', { mod: true });
  const cmd = sel();
  thTableSelect('Initial:17:0', 'statement', { shift: true });
  const run = sel().sort();
  const canvas = Object.entries(TH.els.cards).filter(([, el]) => el.classList.contains('sel')).map(([k]) => k).sort();
  thTableSelect('g3', 'label');
  const label = [...TH.sel.groups];
  thClearSel();
  out.select = { one, cmd, run, canvas, label, cleared: TH.sel.cards.size + TH.sel.groups.size };

  // the mouse's press on a row: a Shift, Cmd or right click and a double-click select no words, a plain click
  // and a press in a title box keep the browser's own
  const heard = {};
  $('th-table').addEventListener = (kind, fn) => { (heard[kind] = heard[kind] || []).push(fn); };
  thTableBoot();
  const press = (e, inBox = false) => {
    let stopped = false;
    const target = { closest: (q) => (q === '[data-trow]' ? {} : (q === 'input, textarea' && inBox ? {} : null)) };
    const ev = Object.assign({ target, button: 0, detail: 1, shiftKey: false, metaKey: false, ctrlKey: false,
      preventDefault: () => { stopped = true; } }, e);
    for (const fn of heard.mousedown || []) fn(ev);
    return stopped;
  };
  out.words = { shift: press({ shiftKey: true }), cmd: press({ metaKey: true }), right: press({ button: 2 }),
    twice: press({ detail: 2 }), plain: press({}), box: press({ shiftKey: true }, true) };

  // ── G over two statements of a PET
  fresh();
  thTableSelect('Initial:3:0', 'statement');
  thTableSelect('Initial:5:0', 'statement', { mod: true });
  thGroupKey();
  const made = TH.tedit && TH.tedit.id;
  const open = !!(TH.tedit && TH.tedit.fresh);
  typeTitle('Calm hands');
  out.group = { open, parent: parentOf(made), members: thGroup(TH.v, made).members.slice(), label: thGroup(TH.v, made).label,
    steps: TH.undo.length, what: TH.undo[0] && TH.undo[0].what, codes: codes() };
  thUndo(true);
  out.group.undone = { gone: !thIsGroup(TH.v, made), back: parentOf('Initial:3:0') === 'g1' && parentOf('Initial:5:0') === 'g1' };

  // ── G with nothing selected: a new empty PET at the end
  fresh();
  thGroupKey();
  const pet = TH.tedit && TH.tedit.id;
  typeTitle('Swarm season');
  const tops = thTableTree(TH.v, TH.layout, true, TH.sheets).pets.map((n) => n.id);
  out.empty = { empty: thGroup(TH.v, pet).members.length === 0, top: parentOf(pet) === undefined, last: tops[tops.length - 1] === pet,
    label: thGroup(TH.v, pet).label, steps: TH.undo.length };
  thUndo(true);
  out.empty.undone = !thIsGroup(TH.v, pet);

  // ── New group inside, from a sub-PET's menu
  fresh();
  const menu = thMenuItems(TH.v, { kind: 'group', id: 'g1' }).some((m) => m.act === 'inside')
    && thMenuItems(TH.v, { kind: 'group', id: 'g2' }).some((m) => m.act === 'inside');
  const inner = thNewEmpty('g2');
  typeTitle('Queen cells');
  const under = thTableSiblings(TH.v, TH.layout, 'g2');
  out.inside = { menu, parent: parentOf(inner), empty: thGroup(TH.v, inner).members.length === 0, last: under[under.length - 1] === inner,
    steps: TH.undo.length };
  thUndo(true);
  out.inside.undone = !thIsGroup(TH.v, inner) && thGroup(TH.v, 'g2').members.length === 2;

  // ── ungroup: Delete this label keeps what it held
  fresh();
  let was = snapOf();
  thDeleteLabels(['g2']);
  out.ungroup = { gone: !thIsGroup(TH.v, 'g2'), held: parentOf('Initial:7:0') === 'g1' && parentOf('Initial:9:0') === 'g1', steps: TH.undo.length };
  thUndo(true);
  out.ungroup.undone = snapOf() === was;

  // ── merge: a PET dropped on another's title strip, then statements on it
  fresh();
  was = snapOf();
  thTableMerge(['g1'], 'label', 'g3');
  out.merge = { nested: parentOf('g1') || null, kept: parentOf('g2') === 'g1' && parentOf('Initial:3:0') === 'g1', steps: TH.undo.length };
  thUndo(true);
  out.merge.undone = snapOf() === was;
  thTableMerge(['Initial:19:0'], 'statement', 'g3');
  await settle();
  const g3 = thTableSiblings(TH.v, TH.layout, 'g3');
  out.merge.joined = parentOf('Initial:19:0') || null;
  out.merge.end = g3[g3.length - 1] === 'Initial:19:0';

  // ── Backspace: back to Not placed
  fresh();
  was = snapOf();
  thTableSelect('Initial:5:0', 'statement');
  thDeleteKey();
  out.back = { loose: parentOf('Initial:5:0') === undefined, steps: TH.undo.length };
  thTableSelect('Initial:5:0', 'statement');
  thDeleteKey();
  out.back.again = TH.undo.length;
  thUndo(true);
  out.back.undone = snapOf() === was;

  // ── two statements dragged together from g1 into g3, after its first
  fresh();
  was = snapOf();
  thTablePut(['Initial:3:0', 'Initial:5:0'], 'statement', 'g1', 'g3', 1);
  await settle();
  out.drag = { order: thTableSiblings(TH.v, TH.layout, 'g3'), steps: TH.undo.length,
    saved: thBody(TH.v, TH.meta).groups.find((g) => g.id === 'g3').members.includes('Initial:5:0') };
  thUndo(true);
  out.drag.undone = parentOf('Initial:3:0') === 'g1' && parentOf('Initial:5:0') === 'g1';

  // ── the bin, and Put back from the table's list
  fresh();
  thTableSelect('Initial:11:0', 'statement');
  thTableSelect('Initial:13:0', 'statement', { mod: true });
  thDiscardKey();
  const binned = TH.v.discarded.includes('Initial:11:0') && TH.v.discarded.includes('Initial:13:0');
  const html = thTableBin(TH.v);
  const listed = html.includes('data-trestore="Initial:11:0"') && html.includes('data-trestore="Initial:13:0"');
  thPutBack('Initial:13:0');
  out.bin = { binned, listed, back: !TH.v.discarded.includes('Initial:13:0') && parentOf('Initial:13:0') === undefined
    && thOnCanvas(TH.v, 'Initial:13:0'), steps: TH.undo.length };
  thUndo(true);
  thUndo(true);
  out.bin.undone = TH.v.discarded.length === 0 && parentOf('Initial:13:0') === 'g3';

  // ── S: three statements stack under the one that reads first
  fresh();
  thTableSelect('Initial:17:0', 'statement');
  thTableSelect('Initial:13:0', 'statement', { mod: true });
  thTableSelect('Initial:15:0', 'statement', { mod: true });
  thTableStackKey();
  const top = Object.keys(TH.v.stacks || {})[0] || null;
  const underTop = top ? thStackOf(TH.v, top).slice().sort() : [];
  thStackShow(top);
  const shown = thTableFlat(TH.v).filter((r) => r.kind === 'under').map((r) => r.id).sort().join() === underTop.join();
  out.stack = { top, under: underTop, steps: TH.undo.length, shown };
  thUndo(true);
  out.stack.undone = thStackOf(TH.v, 'Initial:13:0').length === 0 && parentOf('Initial:15:0') === 'g3' && parentOf('Initial:17:0') === 'g3';

  // ── GETs: New group inside on a GET, its sub-theme a row of the table, and a Cases panel row dropped on it
  const ENTRY = (name, pets) => ({ case: name, who: name, in: true, complete: true, lines: {},
    pets: pets.map(([id, title]) => ({ id, title, parent: null, statements: [], subs: [] })) });
  const getsFresh = () => {
    fresh();
    TH.mode = 'gets';
    TH.gets = { cases: [ENTRY('Wren', [['g1', 'Calm at the hive'], ['g2', 'The smell of smoke']]), ENTRY('Ash', [['g1', 'Stings remembered']])],
      minimum: 2, total: 2, settings: { one_per_pet: true } };
    const card = (entry, id, x, y) => Object.assign(gtCardFrom(entry, 'pet', id), { x, y });
    TH.v.cards = { 'Wren/g1': card(TH.gets.cases[0], 'g1', 40, 120), 'Ash/g1': card(TH.gets.cases[1], 'g1', 270, 120) };
    TH.v.groups = [{ id: 'G1', label: 'Living with stings', members: ['Wren/g1', 'Ash/g1'], x: 20, y: 60 }];
    TH.v.rows = {};
    TH.els.cards = { 'Wren/g1': new El('a'), 'Ash/g1': new El('b') };
    TH.z = Object.keys(TH.v.cards);
    TH.layout = {};
    thRender();
  };
  getsFresh();
  const acts = (id) => gtMenuItems(TH.v, { kind: 'group', id }, thMenuItems(TH.v, { kind: 'group', id }, false)).map((m) => m.act);
  const getMenu = acts('G1').includes('inside');
  const sid = thNewEmpty('G1');
  const sopen = !!(TH.tedit && TH.tedit.fresh && TH.tedit.id === sid);
  typeTitle('Stings in the first summer');
  const face = gtTableFace(TH.v);
  out.gets = { menu: getMenu, open: sopen, parent: parentOf(sid), empty: thGroup(TH.v, sid).members.length === 0,
    label: thGroup(TH.v, sid).label, steps: TH.undo.length,
    row: face.includes(`data-trow="${sid}" data-tkind="label" data-tparent="G1"`),
    flat: thTableFlat(TH.v).some((r) => r.id === sid && r.kind === 'label'), subMenu: acts(sid).includes('inside') };
  thTableMerge(['Ash/g1'], 'statement', sid);
  await settle();
  out.gets.filled = parentOf('Ash/g1') === sid && TH.undo.length === 2
    && gtTableFace(TH.v).includes(`in ${thGroup(TH.v, sid).label}`);
  thUndo(true);
  thUndo(true);
  out.gets.undone = !thIsGroup(TH.v, sid) && parentOf('Ash/g1') === 'G1';

  getsFresh();
  const brought = gtCardFrom(TH.gets.cases[0], 'pet', 'g2');
  gtPullTableDrop(brought, { gid: 'G1', el: new El('sec') });
  out.pull = { joined: parentOf('Wren/g2') === 'G1', steps: TH.undo.length, what: TH.undo[0] && TH.undo[0].what,
    selected: TH.sel.cards.has('Wren/g2') };
  thUndo(true);
  out.pull.undone = !TH.v.cards['Wren/g2'];
  getsFresh();
  gtPullTableDrop(gtCardFrom(TH.gets.cases[0], 'pet', 'g1'), { gid: null, el: new El('rest') });
  out.pull.loose = parentOf('Wren/g1') === undefined && TH.undo.length === 1 && TH.undo[0].what === 'Moved a card from the Participants panel';
  getsFresh();
  thDiscard(TH.v, ['Ash/g1']);
  gtPullTableDrop(gtCardFrom(TH.gets.cases[1], 'pet', 'g1'), { gid: 'G1', el: new El('sec') });
  out.pull.unbinned = !TH.v.discarded.includes('Ash/g1') && parentOf('Ash/g1') === 'G1' && TH.undo.length === 1;
  gtPullTableDrop(gtCardFrom(TH.gets.cases[1], 'pet', 'g1'), { gid: 'G1', el: new El('sec') });
  out.pull.same = TH.undo.length === 1;

  process.stdout.write(JSON.stringify(out));
})().catch((e) => { console.error(e.stack); process.exit(1); });
"""
