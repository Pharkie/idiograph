"""Area 414: a trajectory's 22 icons and a delete undone from its notice (trajbuild, 17 November 2026, Adam's C and
D1 of the trajectory picker, and his ruling that the same function works the same on every screen).

What is checked, on a scratch copy of the longitudinal demo as a fresh clone has it, worked on as a project of its
own. A: every one of the server's icons (`trajectories.ICONS`, 22) set on a trajectory through the screen's route is
read back by the board, and the page draws and names every one of them and no other. B: every icon set by an agent's
`trajectories apply` on the command line, each spelt with a space where the name has an underscore, and by MCP's
`trajectories_apply`, is read back by `trajectories show`; its dry run writes nothing. C: a name that is no icon is
refused by the route, the command line and MCP alike, nothing written. D: a trajectory deleted by the bin, as the
page sends it, then the notice's Undo, which asks what the toolbar's Undo asks, puts the Trajectories file and every
other file of the project back byte for byte. E: a label deleted on a PETs board, by the board's own model run in
node, then its notice's Undo putting the board back from the step it kept: the board saved after the Undo is the
board saved before the delete, the file the same but for the board's save count and time of writing.

trajfix2 (17 November 2026, the review's findings): F: a second `remove` of a trajectory that is gone, by its id, is
refused with nothing written even where another trajectory is titled with that id. G, in node, Trajectories' own
script with the shared notice from shell.js: the notice's Undo undoes its delete and puts the focus on the restored
icon; after another change, a toolbar Undo or leaving the screen the notice is gone and a press of its button undoes
nothing; a title being typed when it is pressed is kept as its own step and the delete stays; two deletes at once send
one, a double-click's second click none; the popover takes the focus on a choice and gives it back to the icon. H, in
node, the boards' own script with the same notice: a label's delete undone from its notice comes back selected; after
another change, a toolbar Undo, a switch of board, or a title typed, a press undoes nothing; an untitled label is named
in the page's word; Ungroup shows no notice."""
from __future__ import annotations

import json
import os
import shutil
from pathlib import Path

from . import support
from .a394_lipa_demo import as_cloned
from .support import check as said_check

WHO = "Arlo"


def check(name, ok, detail=""):
    said_check(name, bool(ok), "" if ok else str(detail)[:700])


def test_trajectory_icons(scratch: Path):
    print("\n414. A trajectory's 22 icons through the route, the command line and MCP, a bad name refused, and a "
          "trajectory's and a PETs label's delete undone from its notice (trajbuild, 17 November)")
    import agent_log
    import cli
    import idiograph_routes as routes
    import mcp_server
    import server as server_mod
    import themes as themes_mod
    import trajectories as traj_mod
    from server import WorkbookError

    fresh = scratch / "icons-414-clone"
    shutil.rmtree(fresh, ignore_errors=True)
    shutil.copytree(support.source("demo"), fresh, ignore=as_cloned)
    kept = (server_mod.DEMO_DIR, server_mod.SHIPPED_DEMO, os.environ.get(agent_log.PLACE), server_mod.CONFIG_PATH,
            themes_mod.now_iso)
    cfg = scratch / "icons-414-config.json"
    cfg.write_text(json.dumps({"projects": [], "interviewer": "Interviewer", "corpus": "", "gravity_reference": "",
                               "corpus_exclude": []}), encoding="utf-8")
    try:
        server_mod.DEMO_DIR = server_mod.SHIPPED_DEMO = fresh
        os.environ[agent_log.PLACE] = str(scratch / "icons-414-agent-log.json")
        demo = server_mod.demo_lipa_dir()
        routes.fill_demo()
        root = scratch / "icons-414-allotment"
        shutil.rmtree(root, ignore_errors=True)
        shutil.copytree(demo, root, ignore=shutil.ignore_patterns("pristine", "source"))
        cfg.write_text(json.dumps({"projects": [{"root": str(root)}], "interviewer": "Interviewer", "corpus": "",
                                   "gravity_reference": "", "corpus_exclude": []}), encoding="utf-8")
        server_mod.CONFIG_PATH = cfg
        routes.api_project({"root": str(root), "agents": True})
        book = next(root.glob(f"{WHO}/{WHO} - *.xlsx"))
        tjfile = traj_mod.path_of(root)

        def call(route: str, body: dict) -> dict:
            with routes.route_scope(route, body):
                return server_mod.ROUTES[route](body)

        def refused(route: str, body: dict) -> str:
            try:
                call(route, body)
            except WorkbookError as exc:
                return str(exc)
            return "answered"

        def ops(*given, **more) -> dict:
            return call("/api/trajectories-ops", dict({"workbook": str(book), "ops": list(given), "step": True}, **more))

        def tree() -> dict:
            # every file of the project but the project's History, the archive copies and the locks
            return {p.relative_to(root).as_posix(): p.read_bytes() for p in sorted(root.rglob("*"))
                    if p.is_file() and "_Archive" not in p.parts and p.name != "idiograph-history.json"
                    and not p.name.endswith(".lock")}

        def differs(a: dict, b: dict) -> list:
            return sorted(k for k in set(a) | set(b) if a.get(k) != b.get(k))

        def agent(*args) -> tuple:
            return cli.run(["--root", str(root), "--config", str(cfg), "trajectories", *args])

        first = call("/api/trajectories", {"workbook": str(book)})
        column = first["columns"][0]["id"]

        def icon_now() -> str | None:
            board = call("/api/trajectories", {"workbook": str(book)})
            return next(c for c in board["columns"] if c["id"] == column).get("icon")

        # ── A. every icon through the screen's route, and the page's own list
        check("414: the server has 22 icons, each once, the first four as before", len(traj_mod.ICONS) == 22
              and len(set(traj_mod.ICONS)) == 22 and {"rising", "mixed", "falling", "level"} <= set(traj_mod.ICONS)
              and first.get("icons") == list(traj_mod.ICONS), first.get("icons"))
        read = {}
        for name in traj_mod.ICONS:
            ops({"op": "icon", "column": column, "icon": name})
            read[name] = icon_now()
        check("414: every icon set through the screen's route is the one the board reads back",
              all(read[k] == k for k in traj_mod.ICONS), {k: v for k, v in read.items() if v != k})
        ops({"op": "icon", "column": column, "icon": None})
        check("414: None takes the icon off", icon_now() is None, icon_now())
        script = support.i18n_js() + support.text("apps/idiograph/static/trajectories.js").split("// a trajectory's colour as its token", 1)[0] \
            + "\nconsole.log(JSON.stringify({ drawn: Object.keys(TJ_ICONS), named: Object.keys(TJ_ICON_SAID), " \
              "words: Object.keys(TJ_ICON_SAID).map((k) => TJ_ICON_SAID[k]()) }));\n"
        run = support.run_node(script, scratch, "icons-414.js") if shutil.which("node") else None
        if run is None:
            support.skip("414: the page's icons", "no node on this machine")
        else:
            page = json.loads(run.stdout or "{}") if run.returncode == 0 else {}
            check("414: the page draws and names every icon the server takes, in its order, each with words of its own",
                  page.get("drawn") == list(traj_mod.ICONS) and page.get("named") == list(traj_mod.ICONS)
                  and all(w and not w.startswith("trajectories.") for w in page.get("words", []))
                  and len(set(page.get("words", []))) == 22, [run.stderr[-300:], page])

        # ── B. every icon by an agent, the command line and MCP
        spec = scratch / "icons-414-spec.json"
        before = tree()
        spec.write_text(json.dumps([{"op": "icon", "column": column, "icon": "steps up"}]), encoding="utf-8")
        code, out, err = agent("apply", "--ops", str(spec), "--note", "Set the icon", "--tool", "Claude Code",
                               "--dry-run", "--json")
        check("414: an agent's dry run of an icon writes nothing", code == 0 and tree() == before, [code, err])
        by_cli = {}
        for name in traj_mod.ICONS:
            spec.write_text(json.dumps([{"op": "icon", "column": column, "icon": name.replace("_", " ")}]), encoding="utf-8")
            code, out, err = agent("apply", "--ops", str(spec), "--note", "Set the icon", "--tool", "Claude Code", "--json")
            shown = json.loads(agent("show", "--json")[1] or "{}")
            icon = next((c.get("icon") for c in shown.get("columns", []) if c.get("id") == column), "?")
            # the board's words come to an agent marked as data, the icon's name among them
            by_cli[name] = (code, icon.get("untrusted_text") if isinstance(icon, dict) else icon)
        check("414: every icon set by an agent on the command line, spelt with a space, is read back by "
              "trajectories show", all(v == (0, k) for k, v in by_cli.items()),
              {k: v for k, v in by_cli.items() if v != (0, k)})
        srv = mcp_server.Server(str(root), config=str(cfg))
        srv.receive(json.dumps({"jsonrpc": "2.0", "id": 0, "method": "initialize",
                                "params": {"protocolVersion": "2025-06-18", "clientInfo": {"name": "claude-code"}}}))

        def mcp(name, args, n):
            return srv.receive(json.dumps({"jsonrpc": "2.0", "id": n, "method": "tools/call",
                                           "params": {"name": name, "arguments": args}}))["result"]

        by_mcp = {}
        for n, name in enumerate(traj_mod.ICONS, start=1):
            got = mcp("trajectories_apply", {"operations": [{"op": "icon", "column": column, "icon": name}],
                                             "request": "Set the icon"}, n)
            by_mcp[name] = (bool(got.get("isError")), icon_now())
        check("414: every icon set through MCP's trajectories_apply is the one the board reads back",
              all(v == (False, k) for k, v in by_mcp.items()), {k: v for k, v in by_mcp.items() if v != (False, k)})

        # ── C. a name that is no icon, refused everywhere, nothing written
        before = tree()
        said = refused("/api/trajectories-ops", {"workbook": str(book), "step": True,
                                                 "ops": [{"op": "icon", "column": column, "icon": "sideways"}]})
        spec.write_text(json.dumps([{"op": "icon", "column": column, "icon": "sideways"}]), encoding="utf-8")
        code, out, err = agent("apply", "--ops", str(spec), "--note", "Set the icon", "--tool", "Claude Code", "--json")
        got = mcp("trajectories_apply", {"operations": [{"op": "icon", "column": column, "icon": "sideways"}],
                                         "request": "Set the icon"}, 99)
        check("414: a name that is no icon is refused by the route, the command line and MCP, nothing written",
              said != "answered" and code != 0 and got.get("isError") is True and tree() == before,
              [said, code, err[:200], json.dumps(got)[:200], differs(tree(), before)])

        # ── D. a trajectory deleted by its bin, then the notice's Undo
        board = call("/api/trajectories", {"workbook": str(book)})
        target = next((c for c in board["columns"] if c.get("participants")), board["columns"][0])
        start, tj0 = tree(), tjfile.read_bytes()
        gone = ops({"op": "remove", "column": target["id"]})
        check("414: the bin deletes the trajectory at once, one step, its participants unplaced",
              target["id"] not in [c["id"] for c in gone["columns"]] and gone.get("steps", {}).get("undo") is True
              and all(p in gone.get("unplaced", []) or p in [u.get("case") if isinstance(u, dict) else u
                                                             for u in gone.get("unplaced", [])]
                      for p in target.get("participants", [])) and tjfile.read_bytes() != tj0,
              [gone.get("steps"), target.get("participants"), gone.get("unplaced")])
        # the notice's Undo runs trajUndo(true), the toolbar's, which asks this route
        back = call("/api/trajectories-undo", {"workbook": str(book), "redo": False})
        check("414: its Undo puts the Trajectories file back byte for byte, and every other file of the project as it was",
              tjfile.read_bytes() == tj0 and tree() == start
              and target["id"] in [c["id"] for c in back["columns"]], differs(tree(), start))

        # ── F. a second remove of a trajectory gone never falls back to one titled with its id (trajfix2)
        ops({"op": "remove", "column": target["id"]})
        ops({"op": "add", "title": target["id"]})
        before = tree()
        said = refused("/api/trajectories-ops", {"workbook": str(book), "step": True,
                                                 "ops": [{"op": "remove", "column": target["id"]}]})
        titled = [c for c in call("/api/trajectories", {"workbook": str(book)})["columns"] if c["title"] == target["id"]]
        check("414: a second remove of a trajectory gone, by its id, is refused with nothing written, the trajectory "
              "titled with that id kept", said != "answered" and tree() == before and len(titled) == 1,
              [said, differs(tree(), before), titled])
        shouted = refused("/api/trajectories-ops", {"workbook": str(book), "step": True,
                                                    "ops": [{"op": "remove", "column": target["id"].upper()}]})
        check("414: the same id in capitals is an id too, refused with the trajectory titled with it kept (trajfix3)",
              shouted != "answered" and tree() == before, [shouted, differs(tree(), before)])
        call("/api/trajectories-undo", {"workbook": str(book), "redo": False})
        call("/api/trajectories-undo", {"workbook": str(book), "redo": False})

        # ── G and H. the delete's notice tied to its step, in node (trajfix2)
        if shutil.which("node"):
            notice_checks(scratch)
        else:
            support.skip("414: the delete's notice in node", "no node on this machine")

        # ── E. a label deleted on a PETs board, then its notice's Undo, by the board's own model
        if not shutil.which("node"):
            support.skip("414: a PETs label's delete undone", "no node on this machine")
            return
        pets = next((p for p in sorted(root.rglob("*.xlsx")) if "_Archive" not in p.parts
                     and (call("/api/themes", {"workbook": str(p)}).get("groups") or [])), None)
        check("414: the demo has a PETs board with a label", pets is not None, "")
        if pets is None:
            return
        themes_mod.now_iso = lambda: "2026-11-17T09:00:00"
        state = call("/api/themes", {"workbook": str(pets)})
        model = support.i18n_js() + support.text("apps/idiograph/static/themes.js") + r"""
const data = JSON.parse(require('fs').readFileSync(process.argv[2], 'utf8'));
TH.mode = 'pets';
TH.stackable = Object.prototype.hasOwnProperty.call(data, 'stacks');
TH.pairable = Array.isArray(data.not_same);
const cards = {};
for (const c of data.cards) cards[c.key] = Object.assign({}, c);
const v = { cards, groups: data.groups.map((g) => Object.assign({}, g, { members: g.members.slice() })),
  discarded: data.discarded.slice(), picks: JSON.parse(JSON.stringify(data.picks || {})),
  ai: { discarded: Object.assign({}, data.discard_reasons || {}) },
  stickies: Array.isArray(data.stickies) ? data.stickies.map((n) => Object.assign({}, n)) : null,
  stacks: data.stacks && typeof data.stacks === 'object' ? JSON.parse(JSON.stringify(data.stacks)) : {},
  not_same: Array.isArray(data.not_same) ? JSON.parse(JSON.stringify(data.not_same)) : [], waits: true };
thWaitsRead(v);
const meta = Object.assign({}, data.version);
const gid = v.groups[0].id;
const before = thBody(v, meta);
const snap = thSnap(v, new Set());
thDelete(v, gid);
const deleted = thBody(v, meta);
thPut(v, snap);
const undone = thBody(v, meta);
console.log(JSON.stringify({ gid, before, deleted, undone }));
"""
        given = scratch / "icons-414-board.json"
        given.write_text(json.dumps(state), encoding="utf-8")
        path = scratch / "icons-414-model.js"
        path.write_text(model, encoding="utf-8")
        import subprocess
        run = subprocess.run([shutil.which("node"), str(path), str(given)], capture_output=True, text=True,
                             encoding="utf-8", timeout=60)
        out = json.loads(run.stdout) if run.returncode == 0 else {}
        check("414: the board's model runs in node", run.returncode == 0, run.stderr[-400:])
        if not out:
            return
        board_path = themes_mod.themes_path(pets)

        def save(body, v):
            return call("/api/themes-save", {"workbook": str(pets), "version": dict(body, v=v)})

        def plain(raw: bytes) -> dict:
            # the file as JSON, each board's save count and the times of writing set aside
            data = json.loads(raw)
            for bd in data.get("boards", []):
                bd.pop("v", None)
                bd.pop("updated", None)
            data.pop("updated", None)
            return data

        first_save = save(out["before"], state["version"].get("v"))
        f0 = board_path.read_bytes()
        cut = save(out["deleted"], first_save["version"]["v"])
        f1 = board_path.read_bytes()
        held = next(bd for bd in json.loads(f1)["boards"] if bd["id"] == state["version"]["id"])
        groups_cut = [g["id"] for g in held["groups"]]
        check("414: a PETs label deleted is saved without it, what it held kept on the board",
              f1 != f0 and out["gid"] not in groups_cut and len(groups_cut) == len(out["before"]["groups"]) - 1
              and set(held["cards"]) == set(out["before"]["cards"]), [out["gid"], groups_cut])
        save(out["undone"], cut["version"]["v"])
        f2 = board_path.read_bytes()
        check("414: its notice's Undo puts the board back as it was: the file the same but for the board's save count "
              "and time of writing", plain(f2) == plain(f0) and out["undone"]["groups"] == out["before"]["groups"],
              [json.dumps(plain(f2))[:300], json.dumps(plain(f0))[:300]])
    finally:
        server_mod.DEMO_DIR, server_mod.SHIPPED_DEMO, server_mod.CONFIG_PATH = kept[0], kept[1], kept[3]
        themes_mod.now_iso = kept[4]
        if kept[2] is None:
            os.environ.pop(agent_log.PLACE, None)
        else:
            os.environ[agent_log.PLACE] = kept[2]


def whole(src: str, head: str) -> str:
    """One top-level function or statement of a script, from its head to its closing line."""
    at = src.index(head)
    end = src.index("\n}\n", at) + 3 if head.startswith(("function", "async function")) else src.index("\n", at) + 1
    return src[at:end]


def toast_pieces() -> str:
    """The line at the foot and its notice from shell.js, on a page that is not Linux's"""
    shell = support.text("family/static/shell.js")
    return "\n".join(["const LINUX = false;", "function toastClear() {}", "let toastTimer;", "let toastWords = '';",
                      whole(shell, "let toastUndo = "), whole(shell, "function say("), whole(shell, "function sayUndo("),
                      whole(shell, "function unsayUndo("), whole(shell, "function toastUndoPut("),
                      whole(shell, "let toastDue = "), whole(shell, "function unsay(")])


TOAST = r"""
// the line at the foot, as much of an element as the notice uses
class Toast {
  constructor() { this.hidden = true; this.kids = []; this.words = ''; this.style = {}; }
  set textContent(v) { for (const k of this.kids) k.isConnected = false; this.kids = []; this.words = String(v); }
  get textContent() { return this.words; }
  get firstChild() { return this.words ? { nodeValue: this.words } : null; }
  append(...n) { for (const k of n) if (k && typeof k === 'object') { k.isConnected = true; this.kids.push(k); } }
  querySelector(q) { return q === '.toast-undo' ? (this.kids.find((k) => k.isConnected) || null) : null; }
  getBoundingClientRect() { return { left: 0, right: 0, top: 0, bottom: 0 }; }
}
const TOAST_EL = new Toast();
const makeButton = () => {
  const b = { isConnected: false, style: {}, addEventListener() {}, focus() {}, setAttribute() {}, append() {},
    classList: { add() {}, remove() {}, toggle() {}, contains: () => false } };
  b.remove = () => { b.isConnected = false; };
  return b;
};
const undoButton = () => TOAST_EL.querySelector('.toast-undo');
const standing = () => !!undoButton() && !TOAST_EL.hidden;
"""

TRAJ_RUN = r"""
const FOCUSED = [];
const ELS = {};
const target = (q) => ({ q, focus() { FOCUSED.push(q); }, querySelector: (q2) => target(q2) });
class El {
  constructor(id) { this.id = id; this.hidden = false; this.value = ''; this.textContent = ''; this.style = {}; this.on = {};
    this.classList = { toggle() {}, add() {}, remove() {}, contains: () => false }; }
  addEventListener(kind, fn) { (this.on[kind] = this.on[kind] || []).push(fn); }
  querySelector(q) { return target(q); }
  querySelectorAll() { return []; }
  contains() { return true; }
  focus() {}
}
const $ = (id) => (id === 'toast' ? TOAST_EL : (ELS[id] = ELS[id] || new El(id)));
globalThis.document = { readyState: 'loading', addEventListener() {}, activeElement: null, createElement: () => makeButton() };
globalThis.CSS = { escape: (s) => s };
globalThis.window = { matchMedia: () => ({ matches: false }) };
globalThis.localStorage = { getItem: () => null, setItem() {} };
const esc = (s) => String(s).replace(/[&<>]/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;' }[c]));
const escAttr = (s) => esc(s).replace(/"/g, '&quot;');
const MOD = (e) => !!(e.metaKey || e.ctrlKey);
const REDO_Y = () => false;
const RESTART_LINE = 'Restart';
const needsRestart = () => false;
const pathProjectDraw = () => {};
const dsTabsDraw = () => {};
const dsTabsWatch = () => {};
const xmenuWire = () => {};
const loadLibrary = async () => {};
// the server: its trajectories, its steps, what it undid
let cols, steps, undone, calls;
const answer = () => ({ columns: JSON.parse(JSON.stringify(cols)), steps: { undo: steps.length > 0, redo: false },
  participants: [], unplaced: [], config: {} });
async function api(url, body) {
  calls.push({ url, ops: body.ops });
  await new Promise((r) => setImmediate(r));
  if (url === '/api/trajectories-ops') {
    const was = JSON.parse(JSON.stringify(cols));
    for (const op of body.ops) {
      const at = cols.findIndex((c) => c.id === op.column);
      if (at < 0) throw new Error('No such trajectory, nothing changed.');
      if (op.op === 'remove') cols.splice(at, 1);
      if (op.op === 'rename') cols[at].title = op.title;
    }
    steps.push({ was, ops: body.ops });
    return answer();
  }
  if (url === '/api/trajectories-undo') { const s = steps.pop(); cols = s.was; undone.push(s.ops); return answer(); }
  return answer();
}
__PIECES__
__TRAJ__
trajDraw = () => {};
const settle = async () => { for (let i = 0; i < 30; i += 1) await new Promise((r) => setImmediate(r)); };
const reset = () => {
  cols = [{ id: 'c1', title: 'Rising' }, { id: 'c2', title: 'Falling' }, { id: 'c3', title: 'Level' }];
  steps = []; undone = []; calls = []; FOCUSED.length = 0;
  Object.assign(TJ, { path: 'Bees/P1 - Wren/P1 Wren.xlsx', busy: false, picking: '', back: null });
  TJ.data = answer();
  $('traj').hidden = false;
  document.activeElement = null;
  TOAST_EL.hidden = false; TOAST_EL.textContent = ''; toastUndo = null; toastWords = '';
};
const titles = () => cols.map((c) => c.title);
(async () => {
  const out = {};
  // its own step
  reset();
  await trajDeleteNow('c1');
  const shown = standing() && TOAST_EL.textContent;
  undoButton().onclick();
  await settle();
  out.own = { shown, undone: undone.map((o) => o.map((x) => `${x.op} ${x.column}`)), titles: titles(),
    focus: FOCUSED[FOCUSED.length - 1], gone: !standing() };
  // another change first
  reset();
  await trajDeleteNow('c1');
  let press = undoButton().onclick;
  await trajOps([{ op: 'rename', column: 'c2', title: 'Down' }]);
  const withdrawn = !standing();
  press();
  await settle();
  out.another = { withdrawn, undone: undone.length, titles: titles() };
  // the toolbar's Undo first, a rename before the delete
  reset();
  await trajOps([{ op: 'rename', column: 'c2', title: 'Down' }]);
  await trajDeleteNow('c1');
  press = undoButton().onclick;
  await trajUndo(true);
  const withdrawnToolbar = !standing();
  press();
  await settle();
  out.toolbar = { withdrawn: withdrawnToolbar, undone: undone.length, titles: titles() };
  // leaving the screen
  reset();
  await trajDeleteNow('c1');
  press = undoButton().onclick;
  TJ.back = async () => {};
  await trajLeave();
  const withdrawnLeave = !standing();
  $('traj').hidden = false;
  press();
  await settle();
  out.leave = { withdrawn: withdrawnLeave, undone: undone.length };
  // a title being typed when the notice's Undo is pressed: the field keeps its words as it blurs, as the page's change does
  reset();
  await trajDeleteNow('c1');
  press = undoButton().onclick;
  document.activeElement = { tagName: 'INPUT', value: 'Typed', dataset: { col: 'c2' },
    blur() { document.activeElement = null; trajTitleDone(this); } };
  press();
  await settle();
  await new Promise((r) => setTimeout(r, 150));
  out.typing = { undone: undone.length, titles: titles(), renamed: calls.filter((c) => c.ops && c.ops[0].op === 'rename').length,
    said: TOAST_EL.hidden ? '' : TOAST_EL.textContent };
  // a change from another window read in: the notice is withdrawn, and a press of its Undo undoes nothing (trajfix3)
  reset();
  await trajDeleteNow('c1');
  press = undoButton().onclick;
  await trajReread(TJ.path);
  const withdrawnOther = !standing();
  press();
  await settle();
  out.other = { withdrawn: withdrawnOther, undone: undone.length };
  // an Undo with nothing to undo leaves the notice standing (trajfix3)
  reset();
  await trajDeleteNow('c1');
  TJ.steps.undo = false;
  const did = await trajUndo(true);
  out.idle = { did, standing: standing() };
  // two deletes at once, and the board's click handler: a double-click's second click and the popover
  reset();
  await Promise.all([trajDeleteNow('c1'), trajDeleteNow('c2')]);
  out.twice = calls.filter((c) => c.ops && c.ops[0].op === 'remove').length;
  let wired = '';
  try { trajWire(); } catch (err) { wired = String((err && err.stack) || err).slice(0, 300); }
  const clicks = (ELS['tj-main'] && ELS['tj-main'].on.click) || [];
  const click = async (attr, value, detail) => {
    const ev = { detail, target: { closest: (q) => (q === `[data-${attr}]` ? { dataset: { [attr.replace(/-(\w)/g, (m, c) => c.toUpperCase())]: value } } : null) } };
    for (const fn of clicks) fn(ev);
    await settle();
  };
  reset();
  await click('remove', 'c1', 2);
  const second = calls.length;
  await click('remove', 'c1', 1);
  out.click = { wired, handlers: clicks.length, second, first: calls.filter((c) => c.ops && c.ops[0].op === 'remove').length };
  reset();
  await click('swatch', 'c2', 1);
  const into = FOCUSED[FOCUSED.length - 1];
  await click('pick-done', '1', 1);
  out.pop = { open: into, back: FOCUSED[FOCUSED.length - 1] };
  process.stdout.write(JSON.stringify(out));
})().catch((e) => { console.error(e.stack); process.exit(1); });
"""

BOARD_RUN = r"""
;(async () => {
  const out = {};
  const b = JSON.parse(process.env.TP_BOARD);
  const fresh = () => {
    const cards = {};
    for (const [k, c] of Object.entries(b.cards)) cards[k] = Object.assign({ sheet: 'Initial', row: Number(k.split(':')[1]), line: 0, time: '00:10' }, c);
    TH.v = { cards, groups: JSON.parse(JSON.stringify(b.groups)), discarded: [], picks: {}, ai: { discarded: {} }, review: null,
      stickies: [], revise: null, stacks: {} };
    TH.meta = { id: b.id, name: b.name, note: '', created: b.created, updated: b.updated };
    TH.path = 'Hive/Hive - EN.xlsx';
    TH.live = true; TH.busy = false; TH.mode = 'pets'; TH.undo = []; TH.redo = []; TH.removed = new Set();
    TH.undoPath = TH.path; TH.undoBoard = b.id; TH.stacks = {}; TH.editing = null; TH.noting = null;
    TH.sel = { cards: new Set(), groups: new Set(), stickies: new Set() };
    TH.els = { cards: {}, labels: {}, frames: {}, stickies: {}, under: {} };
    for (const k of Object.keys(cards)) TH.els.cards[k] = new El(k);
    TH.project = { pet_labels: 'letters' }; TH.sheets = ['Initial']; TH.quotes = {};
    TH.dirty = false; TH.saveTimer = null; TH.chain = null; TH.face = 'table'; TH.opened = new Set(); TH.stackable = true;
    TH.tedit = null; TH.tanchor = null; TH.panelOpen = false;
    TH.z = Object.keys(cards);
    $('themes').hidden = false;
    TOAST_EL.hidden = false; TOAST_EL.textContent = ''; toastUndo = null; toastWords = '';
    thRender();
  };
  thMeasure = function () {
    TH.sizes = {};
    for (const k of Object.keys(TH.v.cards)) TH.sizes[k] = { w: 200, h: 80 };
    for (const g of TH.v.groups) TH.sizes[g.id] = { w: 140, h: 30 };
  };
  thRender = function () { thMeasure(); thPlace(); };
  thMapMoved = () => {};
  const snapOf = () => JSON.stringify(thBody(TH.v, TH.meta).groups.map((g) => [g.id, g.label, g.members]));
  const has = (id) => thIsGroup(TH.v, id);

  // its own step: the label back, selected
  fresh();
  const was = snapOf();
  thDeleteLabels(['g3']);
  const shown = standing() && TOAST_EL.textContent;
  undoButton().onclick();
  out.own = { shown, back: snapOf() === was, selected: [...TH.sel.groups], gone: !standing() };
  // another change first: Ungroup, which shows no notice of its own
  fresh();
  thDeleteLabels(['g3']);
  let press = undoButton().onclick;
  thDeleteLabels(['g2'], { ungroup: true });
  const withdrawn = !standing();
  const after = snapOf();
  press();
  out.another = { withdrawn, same: snapOf() === after, g3: has('g3'), g2: has('g2') };
  // Ungroup alone says nothing at the foot
  fresh();
  thDeleteLabels(['g2'], { ungroup: true });
  out.ungroup = { notice: standing(), gone: !has('g2') };
  // the toolbar's Undo first, another delete's step under it
  fresh();
  thDeleteLabels(['g1']);
  thDeleteLabels(['g3']);
  // the line put away by the step and said again shows its words a frame later
  for (const fn of FRAMES.splice(0)) fn();
  press = undoButton().onclick;
  thUndo(true);
  const withdrawnToolbar = !standing();
  press();
  out.toolbar = { withdrawn: withdrawnToolbar, g3: has('g3'), g1: has('g1') };
  // another board, its own step on top
  fresh();
  thDeleteLabels(['g3']);
  press = undoButton().onclick;
  const held = TH.undo;
  thUseStacks('v2');
  const withdrawnBoard = !standing();
  TH.undo.push(held[0]);
  const top = TH.undo.length;
  press();
  out.board = { withdrawn: withdrawnBoard, untouched: TH.undo.length === top && TH.redo.length === 0 };
  // a title being typed when the notice's Undo is pressed: kept as its own step, the delete left as it is
  fresh();
  thDeleteLabels(['g3']);
  press = undoButton().onclick;
  const g1 = thGroup(TH.v, 'g1');
  TH.editing = { id: 'g1', input: { value: 'Hive moods' }, was: g1.label, before: thSnap(TH.v, TH.removed),
    boxes: thLabelBoxes(TH.layout), desc: null, fresh: false };
  press();
  out.typing = { title: thGroup(TH.v, 'g1').label, g3: has('g3'), steps: TH.undo.length };
  // an untitled label, saved as the English word or as nothing, named in the page's word
  const words = [];
  for (const label of ['Untitled', '']) {
    fresh();
    thGroup(TH.v, 'g3').label = label;
    thDeleteLabels(['g3']);
    words.push(TOAST_EL.textContent);
  }
  out.untitled = { words, want: t('themes.deleted_label', { title: t('themes.untitled') }) };
  process.stdout.write(JSON.stringify(out));
})().catch((e) => { console.error(e.stack); process.exit(1); });
"""


def notice_checks(scratch: Path):
    """G and H: the delete's notice tied to its own step, on Trajectories and on a board, run in node"""
    import subprocess
    import sys

    from . import a208_table_parity as tp

    pieces = TOAST + toast_pieces()
    traj = support.cycle_js() + support.text("apps/idiograph/static/trajectories.js")
    script = support.i18n_js() + TRAJ_RUN.replace("__PIECES__", pieces).replace("__TRAJ__", traj)
    run = support.run_node(script, scratch, "notice-414-traj.js", timeout=60)
    got = json.loads(run.stdout) if run.returncode == 0 and run.stdout.strip() else {}
    check("414: Trajectories' notice runs in node", run.returncode == 0, run.stderr[-600:])
    if got:
        own = got["own"]
        check("414: the notice's Undo undoes its own delete, the trajectory back, the focus on its icon",
              own["shown"] and own["undone"] == [["remove c1"]] and own["titles"] == ["Rising", "Falling", "Level"]
              and own["focus"] == '[data-fkey="swatch-c1"]' and own["gone"], json.dumps(own))
        a = got["another"]
        check("414: after another change the notice is gone, and a press of its Undo undoes nothing",
              a["withdrawn"] and a["undone"] == 0 and a["titles"] == ["Down", "Level"], json.dumps(a))
        tb = got["toolbar"]
        check("414: a toolbar Undo withdraws the notice, and a press of its Undo then leaves the step before alone",
              tb["withdrawn"] and tb["undone"] == 1 and tb["titles"] == ["Rising", "Down", "Level"], json.dumps(tb))
        lv = got["leave"]
        check("414: leaving the screen withdraws the notice, and a press of its Undo undoes nothing",
              lv["withdrawn"] and lv["undone"] == 0, json.dumps(lv))
        ty = got["typing"]
        check("414: a title being typed when the notice's Undo is pressed is kept as its own step, never undone in the "
              "delete's place, and the delete stays", ty["undone"] == 0 and ty["renamed"] == 1
              and ty["titles"] == ["Typed", "Level"], json.dumps(ty))
        check("414: when its Undo is pressed after a change, the notice says the trajectory was not brought back",
              ty["said"].startswith("The trajectory was not brought back"), json.dumps(ty))
        ot = got["other"]
        check("414: a change read in from another window withdraws the notice, and a press of its Undo undoes nothing",
              ot["withdrawn"] and ot["undone"] == 0, json.dumps(ot))
        ide = got["idle"]
        check("414: an Undo that undoes nothing leaves the delete's notice standing", ide["did"] is False and ide["standing"],
              json.dumps(ide))
        check("414: two deletes at once send one", got["twice"] == 1, got["twice"])
        cl = got["click"]
        check("414: on the board, a double-click's second click on the bin deletes nothing, a single click one",
              not cl["wired"] and cl["handlers"] >= 1 and cl["second"] == 0 and cl["first"] == 1, json.dumps(cl))
        pop = got["pop"]
        check("414: the colour and icon popover takes the focus on a colour when opened and gives it back to the icon "
              "on Done", pop["open"] in (".tf-sw.on", ".tf-sw") and pop["back"] == '[data-fkey="swatch-c2"]',
              json.dumps(pop))

    board = {"id": "v1", "name": "Board 1", "note": "", "created": "2026-10-20T09:00:00+01:00",
             "updated": "2026-10-20T09:00:00+01:00", "discarded": [], "picks": {}, "notes": [],
             "cards": {k: {"x": x, "y": y, "text": w} for k, (x, y, w) in tp.CARDS.items()},
             "groups": support.plain(json.loads(json.dumps(tp.GROUPS)))}
    stubs = tp.STUBS.replace("const say = (t) => SAID.push(t);\n", "").replace("const sayUndo = (t) => SAID.push(t);\n", "")
    stubs = stubs.replace("const $ = (id) => (id === 'th-stage' ? null : (ELS[id] = ELS[id] || new El(id)));",
                          "const $ = (id) => (id === 'th-stage' ? null : id === 'toast' ? TOAST_EL : (ELS[id] = ELS[id] || new El(id)));")
    stubs = stubs.replace("globalThis.document = { activeElement: null };",
                          "globalThis.document = { activeElement: null, createElement: () => makeButton() };")
    js = support.text("apps/idiograph/static/themes.js")
    path = scratch / "notice-414-board.js"
    stubs += "El.prototype.appendChild = function () {};\n"
    path.write_text(support.i18n_js() + TOAST + stubs + toast_pieces() + "\n" + js + BOARD_RUN, encoding="utf-8")
    env = dict(os.environ, TP_PY=sys.executable, TP_BOARD=json.dumps(board))
    run = subprocess.run([shutil.which("node"), str(path)], capture_output=True, text=True, encoding="utf-8",
                         timeout=180, env=env)
    got = json.loads(run.stdout) if run.returncode == 0 and run.stdout.strip() else {}
    check("414: the board's notice runs in node", run.returncode == 0, run.stderr[-600:])
    if not got:
        return
    own = got["own"]
    check("414: a label's notice Undo puts the board back, the label selected, the notice gone",
          own["shown"] and own["back"] and own["selected"] == ["g3"] and own["gone"], json.dumps(own))
    a = got["another"]
    check("414: after another change on the board the notice is gone, and a press of its Undo undoes nothing",
          a["withdrawn"] and a["same"] and not a["g3"] and not a["g2"], json.dumps(a))
    check("414: Ungroup shows no Deleted notice", not got["ungroup"]["notice"] and got["ungroup"]["gone"],
          json.dumps(got["ungroup"]))
    tb = got["toolbar"]
    check("414: a toolbar Undo withdraws the board's notice, and a press of its Undo leaves the delete before alone",
          tb["withdrawn"] and tb["g3"] and not tb["g1"], json.dumps(tb))
    bd = got["board"]
    check("414: a switch of board withdraws the notice, and a press of its Undo touches the other board's steps not at "
          "all", bd["withdrawn"] and bd["untouched"], json.dumps(bd))
    ty = got["typing"]
    check("414: a label's title being typed when the notice's Undo is pressed is kept as its own step, and the delete "
          "stays", ty["title"] == "Hive moods" and not ty["g3"] and ty["steps"] == 2, json.dumps(ty))
    un = got["untitled"]
    check("414: an untitled label's notice names it in the page's word, saved as Untitled or as nothing",
          un["words"] == [un["want"], un["want"]] and "Untitled" in un["want"], json.dumps(un))
