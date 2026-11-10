"""Area 234: Adam's clear calls on Home and Settings of 20 October 2026 (homebatch). Back from a project's
page is Home and Forward goes in again, the Mac window taking a mouse's back and forward buttons and View's
Home reaching the page; Celebrations a switch for each screen, a settings file from before read as all
three as it was; Text size, the window's zoom set from Settings and kept; and the statement length a
project's own number, 15 by default and kept in the project file only when it is not, the length nudge at
that length, the command line and the MCP server reading and setting it with a dry run. Every fixture is
invented, a project on keeping bees."""
from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path

import cli
import mcp_server
import nudges
import server as server_mod

from . import support
from .support import check, skip
import idiograph_routes


def whole(src: str, head: str) -> str:
    at = src.index(head)
    return src[at:src.index("\n}\n", at) + 3]


def test_home_batch(scratch: Path):
    print("\n234. Home, Back and Forward, Celebrations per screen, text size, the statement length")
    js = support.text("family/static/shell.js", "apps/idiograph/static/distil.js")
    window_js = support.source("packaging/tauri/window.js").read_text(encoding="utf-8")
    node = shutil.which("node")

    base = scratch / "homebatch-234"
    shutil.rmtree(base, ignore_errors=True)
    root = base / "Keeping bees"
    (root / "P1 - Wren").mkdir(parents=True)
    project_file = root / server_mod.PROJECT_FILE
    project_file.write_text(json.dumps({"name": "Keeping bees", "research_question": "How do beekeepers live "
                                        "through a cold spring?", "agents": {"allowed": True, "at": "2026-10-21T00:00:00+01:00"}}),
                            encoding="utf-8")
    book = root / "P1 - Wren" / "P1 Wren - EN & ES.xlsx"
    book.write_bytes(b"PK\x03\x04 a workbook stands in here")
    config_file = base / "config-234.json"
    config_file.write_text(json.dumps({"projects": [], "interviewer": "Sam", "corpus": "", "gravity_reference": "",
                                       "corpus_exclude": []}), encoding="utf-8")
    live = server_mod.CONFIG_PATH.read_bytes() if server_mod.CONFIG_PATH.exists() else None
    kept = server_mod.CONFIG_PATH, server_mod.ROOT_OVERRIDE, server_mod.STATE_MEMORY
    long_line = "Smoke drifting over the frames before the first inspection of a cold and quiet spring morning out"
    try:
        server_mod.CONFIG_PATH = config_file
        server_mod.ROOT_OVERRIDE = str(root)
        server_mod.STATE_MEMORY = {}

        # ── A. the statement length, the project's own number
        before = project_file.read_bytes()
        read = idiograph_routes.api_project({})["project"]
        dry = idiograph_routes.api_project({"statement_words": 22, "dry_run": True})
        check("234: a project with no statement length reads 15, and a dry run says what would change and writes nothing",
              read["statement_words"] == 15 and dry["project"]["statement_words"] == 22 and dry["dry_run"] is True
              and dry["changes"] == ["Statement length from 15 to 22 words."] and project_file.read_bytes() == before,
              json.dumps(dry)[:300])
        idiograph_routes.api_project({"statement_words": 22})
        held = json.loads(project_file.read_text(encoding="utf-8"))
        check("234: the length is saved in the project file, every other key kept",
              held.get("statement_words") == 22 and held.get("name") == "Keeping bees" and held.get("agents", {}).get("allowed") is True
              and idiograph_routes.read_project(root)["statement_words"] == 22, str(held))
        at_22 = idiograph_routes.api_nudges({"text": long_line, "path": str(book)})
        at_15 = idiograph_routes.api_nudges({"text": long_line})
        flags = lambda answer: [f["note"] for line in answer["lines"] for f in line["flags"] if f["check"] == "length"]
        check("234: the length nudge speaks at the project's length, and at 15 without a workbook",
              flags(at_22) == [] and at_22["statement_words"] == 22 and flags(at_15) and flags(at_15)[0].startswith("over 15 words")
              and nudges.words(long_line) == 17, f"{flags(at_22)} {flags(at_15)}")
        at_10 = nudges.check_field("Smoke over the frames before the first look of spring", high=8)
        check("234: the nudges take any length, saying it", at_10 and at_10[0]["flags"][0]["note"].startswith("over 8 words"),
              str(at_10))
        refused = []
        for bad in (3, 61, "many", True, 12.5):
            try:
                idiograph_routes.api_project({"statement_words": bad})
                refused.append(False)
            except server_mod.WorkbookError:
                refused.append(True)
        check("234: a length that is not a whole number from 5 to 60 is refused, and the file stays at 22",
              all(refused) and json.loads(project_file.read_text(encoding="utf-8"))["statement_words"] == 22, str(refused))
        try:
            idiograph_routes.write_statement_words(server_mod.DEMO_DIR, 20)
            demo_refused = False
        except server_mod.WorkbookError:
            demo_refused = True
        check("234: the demo's length is fixed", demo_refused)
        idiograph_routes.api_project({"statement_words": 15})
        check("234: back at 15 the key leaves the project file", "statement_words" not in json.loads(project_file.read_text(encoding="utf-8")))
        project_file.write_text(json.dumps({"name": "Keeping bees", "statement_words": "lots"}), encoding="utf-8")
        check("234: a project file holding something else reads 15", idiograph_routes.read_project(root)["statement_words"] == 15)
        project_file.write_text(json.dumps({"name": "Keeping bees", "agents": {"allowed": True, "at": "2026-10-21T00:00:00+01:00"}}),
                                encoding="utf-8")

        # the command line and the MCP server, the API's two other clients
        def run(*args):
            return cli.run(["--config", str(config_file), "--root", str(root), *args])

        code_r, said_r, _ = run("length")
        code_d, said_d, _ = run("length", "28", "--dry-run")
        after_dry = json.loads(project_file.read_text(encoding="utf-8"))
        code_n, said_n, err_n = run("length", "28")
        code_s, said_s, _ = run("length", "28", "--note", "a tester's statements run long, make it 28")
        check("234: the command line reads the length, a dry run writes nothing, a set without his words is refused, "
              "and with them it is saved",
              code_r == 0 and "past 15 words" in said_r and code_d == 0 and "Dry run" in said_d and "statement_words" not in after_dry
              and code_n != 0 and code_s == 0 and json.loads(project_file.read_text(encoding="utf-8")).get("statement_words") == 28,
              f"{said_r} | {said_d} | {err_n} | {said_s}")
        mcp = mcp_server.Server(root=str(root), config=str(config_file))
        names = {t["name"] for t in mcp.tools}
        res = mcp.call(mcp.by_name["statement_length"], {})
        res2 = mcp.call(mcp.by_name["statement_length_set"], {"words": 20, "request": "make it 20", "dry_run": True})
        check("234: the MCP server lists statement_length and statement_length_set, and the dry run writes nothing",
              {"statement_length", "statement_length_set"} <= names and not res["isError"] and not res2["isError"]
              and json.loads(project_file.read_text(encoding="utf-8")).get("statement_words") == 28,
              json.dumps([res["content"], res2["content"]])[:300])

        # ── B. Celebrations, a switch for each screen
        merged_off = server_mod.merge_config({"celebrations": False})["celebration_screens"]
        merged_none = server_mod.merge_config({})["celebration_screens"]
        check("234: a settings file from before the three reads as all three, as its one switch said",
              merged_off == {"statements": False, "pets": False, "gets": False}
              and merged_none == {"statements": True, "pets": True, "gets": True}, f"{merged_off} {merged_none}")
        server_mod.api_settings({"celebration_screens": {"pets": False}, "celebrations": True})
        one = json.loads(config_file.read_text(encoding="utf-8"))
        server_mod.api_settings({"celebration_screens": {"statements": False, "pets": False, "gets": False}})
        two = json.loads(config_file.read_text(encoding="utf-8"))
        server_mod.api_settings({"celebrations": True})
        three = json.loads(config_file.read_text(encoding="utf-8"))
        server_mod.api_settings({"interviewer": "Sam"})
        four = json.loads(config_file.read_text(encoding="utf-8"))
        check("234: each screen's switch is saved on its own, the old key on while any is, and the one switch of a page "
              "from before sets all three",
              one["celebration_screens"] == {"statements": True, "pets": False, "gets": True} and one["celebrations"] is True
              and two["celebrations"] is False and three["celebration_screens"] == {"statements": True, "pets": True, "gets": True}
              and four["celebration_screens"] == three["celebration_screens"], json.dumps([one.get("celebration_screens"),
                                                                                         two.get("celebrations")]))
        check("234: Sift and Trace copy the three on their first start, with Celebrations",
              "celebration_screens" in server_mod.app_identity.SHARED_SETTINGS)
    finally:
        server_mod.CONFIG_PATH, server_mod.ROOT_OVERRIDE, server_mod.STATE_MEMORY = kept
    check("234: the live settings file is exactly as it was",
          (server_mod.CONFIG_PATH.read_bytes() if server_mod.CONFIG_PATH.exists() else None) == live)

    if not node:
        skip("234: the page's parts and the window's under node", "node is not on this machine")
        return

    # ── C. the page under node: each screen's switch, the text size's rows, and Back and Forward from a project
    nav = js[js.index("const NAV_KIND = "):js.index("function navHeld()")]
    pieces = [line_of(js, "const CHEER_SCREENS = "), whole(js, "function cheerScreen()"), whole(js, "function cheerOnFor("),
              line_of(js, "const TEXT_SIZES = "), line_of(js, "const textSizeOf = "), nav,
              whole(js, "function navHeld()"), whole(js, "function navHere()"), line_of(js, "const navSame = "),
              whole(js, "async function navGo("), whole(js, "function navBackNow()"), whole(js, "async function navWayBack()"),
              whole(js, "function navSteps("), whole(js, "function navPop("), whole(js, "async function navBack("),
              whole(js, "async function navForward("), whole(js, "function openPage("), whole(js, "function openPageNow("),
              whole(js, "function closePage()"),
              # the family's celebrations ask Idiograph's part which screen is in front (the fifth build, 23 October 2026)
              "const FAMILY_APPS = {};", support.distil_hooks(js)]
    page = base / "page-234.js"
    page.write_text(r"""
const els = {};
const mk = (hidden) => ({ hidden, focus() {}, querySelectorAll: () => [] });
const $ = (id) => els[id] || (els[id] = mk(true));
const S = { home: '', data: null };
els.library = mk(false); els['home-pick'] = mk(false); els['home-project'] = mk(true); els.work = mk(true); els.themes = mk(true);
const homeKeep = (id) => { S.home = String(id || ''); };
const drawHome = () => { els['home-pick'].hidden = !!S.home; els['home-project'].hidden = !S.home; };
const window = { scrollTo() {} };
const document = {};
const toLibraryNow = async () => true; const themesLeave = async () => true;
const pops = [];
const history = { list: [null], at: 0,
  get state() { return this.list[this.at]; },
  pushState(s) { this.list = this.list.slice(0, this.at + 1); this.list.push(s); this.at += 1; },
  go(n) { this.at = Math.max(0, Math.min(this.list.length - 1, this.at + n)); pops.push(this.state); },
  back() { this.go(-1); }, forward() { this.go(1); } };
""" + "\n".join(pieces) + r"""
const settle = async () => { while (pops.length) { navPop({ state: pops.shift() }); await NAV.chain; } };
(async () => {
  const out = {};
  out.cheer = [cheerOnFor({ celebrations: false }, 'pets'), cheerOnFor({}, 'gets'),
    cheerOnFor({ celebrations: true, celebration_screens: { statements: true, pets: false, gets: true } }, 'pets'),
    cheerOnFor({ celebration_screens: { statements: true, pets: false, gets: true } }, 'gets'), cheerScreen()];
  out.sizes = [0.9, 1, 1.25, 1.1, 0.67, 2].map(textSizeOf);
  await openPage('p1');
  out.opened = { home: S.home, entries: history.list.length, screen: navHere().screen };
  history.back(); await settle();
  out.back = { home: S.home, pick: !els['home-pick'].hidden, screen: navHere().screen };
  history.forward(); await settle();
  out.forward = { home: S.home, project: !els['home-project'].hidden, entries: history.list.length };
  out.arrow = navBackNow(); await settle();
  out.arrowed = { home: S.home, screen: navHere().screen };
  console.log(JSON.stringify(out));
})();
""", encoding="utf-8")
    ran = subprocess.run([node, str(page)], capture_output=True, text=True, encoding="utf-8", timeout=60)
    try:
        got = json.loads(ran.stdout.strip().splitlines()[-1])
    except (ValueError, IndexError):
        got = {}
    check("234: each screen reads its own Celebrations switch, a file from before its one switch",
          got.get("cheer") == [False, True, False, True, "statements"], ran.stderr[-400:] or str(got.get("cheer")))
    check("234: Text size's row is Small at 90%, Medium at the actual size and Large at 125%, none between them "
          "(zoomshow, 30 October 2026: the heading then says the size)",
          got.get("sizes") == ["small", "medium", "large", "", "", ""], str(got.get("sizes")))
    check("234: a project's page opened from Home is an entry of its own, Back is Home, and Forward opens it again "
          "with no entry more, the page's arrow being Back",
          got.get("opened") == {"home": "p1", "entries": 2, "screen": "project"}
          and got.get("back") == {"home": "", "pick": True, "screen": "home"}
          and got.get("forward") == {"home": "p1", "project": True, "entries": 2}
          and got.get("arrowed") == {"home": "", "screen": "home"} and got.get("arrow") is True,
          ran.stderr[-400:] or json.dumps(got))

    # ── D. the window under node: the text size, View's Home and a mouse's back and forward buttons on a Mac
    harness = base / "window-234.js"
    harness.write_text(r"""
const src = require('fs').readFileSync(process.argv[2], 'utf8');
function load(os) {
  const t = { invoked: [], on: {}, nav: [], homed: 0, told: [] };
  class Ev { constructor(type, o) { this.type = type; Object.assign(this, o || {}); this.defaultPrevented = false; }
    preventDefault() { this.defaultPrevented = true; } stopPropagation() {} }
  const win = {
    __IDIOGRAPH_OS__: os, __IDIOGRAPH_SEED__: {}, Event: Ev, KeyboardEvent: Ev,
    CustomEvent: class { constructor(type, o) { this.type = type; this.detail = o.detail; } },
    addEventListener: (n, f) => { (t.on[n] = t.on[n] || []).push(f); },
    dispatchEvent: (e) => { if (e.type === 'idiograph-zoom') t.told.push(e.detail); return true; },
    history: { back: () => t.nav.push('back'), forward: () => t.nav.push('forward') },
    idiographHome: () => { t.homed += 1; },
    __TAURI_INTERNALS__: { invoke: (cmd, args) => { t.invoked.push([cmd, args]); return Promise.resolve(cmd === 'zoom' ? (args.to || 1) : null); } },
  };
  const document = { activeElement: null, body: null, getElementById: () => null };
  global.Event = Ev; global.KeyboardEvent = Ev; global.document = document;
  new Function('window', 'document', src)(win, document);
  Object.assign(t, { win, Ev });
  return t;
}
(async () => {
  const out = {};
  const m = load('macos');
  out.set = await m.win.idiographTextSize(1.25);
  out.read = await m.win.idiographTextSize();
  out.zooms = m.invoked.filter((x) => x[0] === 'zoom').map((x) => x[1]);
  out.told = m.told;
  m.win.__idiographMenu('home');
  out.homed = m.homed;
  const click = (t, button) => { const ev = new t.Ev('mouseup', { button }); for (const f of t.on.mouseup || []) f(ev); return ev.defaultPrevented; };
  out.mac = [click(m, 3), click(m, 4), click(m, 0)];
  out.macNav = m.nav;
  const w = load('windows');
  out.win = [click(w, 3), click(w, 4)];
  out.winNav = w.nav;
  console.log(JSON.stringify(out));
  process.exit(0);
})();
""", encoding="utf-8")
    ran = subprocess.run([node, str(harness), str(support.source("packaging/tauri/window.js"))],
                         capture_output=True, text=True, encoding="utf-8", timeout=60)
    try:
        got = json.loads(ran.stdout.strip().splitlines()[-1])
    except (ValueError, IndexError):
        got = {}
    check("234: Settings' Text size asks the window for its zoom by step and reads it back, each told to the page",
          got.get("set") == 1.25 and got.get("read") == 1 and got.get("zooms") == [{"to": 1.25}, {}]
          and got.get("told") == [1.25, 1], ran.stderr[-400:] or json.dumps(got))
    check("234: View's Home reaches the page's Home", got.get("homed") == 1, json.dumps(got))
    check("234: on a Mac a mouse's back and forward buttons are Back and Forward, and Windows's web view keeps its own",
          got.get("mac") == [True, True, False] and got.get("macNav") == ["back", "forward"]
          and got.get("win") == [False, False] and got.get("winNav") == [], json.dumps(got))
    check("234: the window's zoom set by step is kept by the window for the next run (keep.rs, its test)",
          "pub fn set_zoom(&self, to: f64) -> f64" in support.source("packaging/tauri/src-tauri/src/keep.rs").read_text(encoding="utf-8")
          and "fn sets_a_text_size_kept_for_the_next_run()" in support.source("packaging/tauri/src-tauri/src/keep.rs").read_text(encoding="utf-8"))


def line_of(js: str, start: str) -> str:
    at = js.index(start)
    return js[at:js.index("\n", at) + 1]
