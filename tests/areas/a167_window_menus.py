from __future__ import annotations

import http.client
import io
import json
import os
import re
import shutil
import subprocess
import threading
from http.server import ThreadingHTTPServer
from pathlib import Path

from . import support
from .support import STUDY_PSEUDONYMS, check, skip


def js_function(src: str, name: str) -> str:
    """A top-level function of a page script, from its `function` line to the brace that closes it."""
    m = re.search(rf"^(?:async )?function {name}\(", src, re.M)
    if not m:
        return ""
    end = src.find("\n}\n", m.start())
    return src[m.start():end + 3] if end > 0 else ""


def js_const(src: str, name: str) -> str:
    """A top-level const of a page script, to the line that ends it."""
    m = re.search(rf"^const {name} = ", src, re.M)
    if not m:
        return ""
    end = src.find(";\n", m.start())
    return src[m.start():end + 2]


def test_window_menus(scratch):
    print("\n167. Idiograph in a window of its own, the second build (17 October): the menus, each system's own, "
          "the window's size, place and page kept across a quit, the page's settings following the app and not "
          "the port, spelling, Choose through the system's own dialog, every window titled by its page, nothing of "
          "the browser's own on paper, thin scrollbars, the log in local time, a notice when the server ends "
          "without a word, and a browser's page as it was")
    import server as server_mod

    tauri = support.source("packaging/tauri")
    src = tauri / "src-tauri"
    read = lambda path: Path(path).read_text(encoding="utf-8")
    main_rs, menu_rs, keep_rs = read(src / "src" / "main.rs"), read(src / "src" / "menu.rs"), read(src / "src" / "keep.rs")
    cargo, conf = read(src / "Cargo.toml"), json.loads(read(src / "tauri.conf.json"))
    window_js, app_js = read(tauri / "window.js"), support.text("family/static/shell.js", "apps/idiograph/static/distil.js")
    themes_js, trace_js, style = read(support.source("apps/idiograph/static/themes.js")), read(support.source("apps/trace/static/trace.js")), support.text("family/static/style.css", "apps/idiograph/static/distil.css")
    manual = read(support.source("docs/manual.md"))
    index = support.every_page()

    # ── A. the server: whether the window started it, quitting by itself, the manual, the print views' paper
    saved = {k: os.environ.get(k) for k in (server_mod.WINDOW, server_mod.STAY_OPEN, server_mod.MANUAL_FILE)}
    try:
        for k in saved:
            os.environ.pop(k, None)
        plain = server_mod.server_state().get("window")
        tick_off = server_mod.quit_on({"quit_when_closed": False})
        os.environ[server_mod.WINDOW] = "1"
        own = server_mod.server_state().get("window")
        own_tick_off = server_mod.quit_on({"quit_when_closed": False})
        os.environ[server_mod.STAY_OPEN] = "1"
        held_open = server_mod.quit_on({"quit_when_closed": True})
    finally:
        for k, v in saved.items():
            if v is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = v
    check("167: the server says whether the window started it, from IDIOGRAPH_WINDOW, which the window sets and "
          "a Restart carries over, and a browser's server says it did not",
          plain is False and own is True and server_mod.WINDOW == "IDIOGRAPH_WINDOW"
          and '.env("IDIOGRAPH_WINDOW", "1")' in main_rs, f"{plain} {own}")
    check("167: a server the window started quits by itself a few minutes after the window's beat stops, whatever "
          "General's tick says, and a run with STAY_OPEN never does", tick_off is False and own_tick_off is True
          and held_open is False)

    code, page = server_mod.manual_page()
    names = re.findall(r"^## (.+)$", manual, re.M)
    check("167: /manual is the manual as one page, its sections listed at its head and each a heading the list leads to",
          code == 200 and all(f">{n}</a>" in page for n in names) and len(names) >= 5, f"{code} {len(names)} sections")
    check("167: the manual's lines keep code, bold and italics, a link off the machine as a link, and a link to a "
          "file beside it as its words alone",
          server_mod.manual_inline("See `x < y`, **bold**, *slant*, [the README](../README.md) and [a site](https://example.org/a).")
          == 'See <code>x &lt; y</code>, <strong>bold</strong>, <em>slant</em>, the README and <a href="https://example.org/a">a site</a>.')
    gone = scratch / "no-manual.md"
    os.environ[server_mod.MANUAL_FILE] = str(gone)
    try:
        code_gone, page_gone = server_mod.manual_page()
    finally:
        if saved[server_mod.MANUAL_FILE] is None:
            os.environ.pop(server_mod.MANUAL_FILE, None)
        else:
            os.environ[server_mod.MANUAL_FILE] = saved[server_mod.MANUAL_FILE]
    check("167: the manual is read from the file the window names in IDIOGRAPH_MANUAL, the one its bundle carries, "
          "and a copy without one says so in one line",
          code_gone == 404 and server_mod.named(server_mod.NO_MANUAL) in page_gone and server_mod.MANUAL_FILE == "IDIOGRAPH_MANUAL"
          and '.env("IDIOGRAPH_MANUAL", manual_file())' in main_rs
          and conf["bundle"]["resources"].get("../../../docs/manual.md") == "docs/manual.md"
          and server_mod.named(server_mod.NO_MANUAL) == "The manual is not in this copy of Idiograph.")

    httpd = ThreadingHTTPServer(("127.0.0.1", 0), server_mod.Handler)
    port = httpd.server_address[1]
    threading.Thread(target=httpd.serve_forever, kwargs={"poll_interval": 0.05}, daemon=True).start()
    try:
        def get(path):
            conn = http.client.HTTPConnection("127.0.0.1", port, timeout=20)
            conn.request("GET", path, headers={"Host": f"127.0.0.1:{port}"})
            res = conn.getresponse()
            body = res.read().decode("utf-8", errors="replace")
            conn.close()
            return res.status, body
        manual_status, manual_page = get("/manual")
        state_status, state = get("/api/server")
    finally:
        httpd.shutdown()
        httpd.server_close()
    check("167: /manual is served with the beat, its paper keeping out the browser's own headers and footers, and "
          "/api/server answers a browser's page with window false",
          manual_status == 200 and server_mod.BEAT_TAG in manual_page and manual_page.count(server_mod.PRINT_MARGINS) == 1
          and state_status == 200 and json.loads(state).get("window") is False, f"{manual_status} {state_status}")
    view = "<html><head><title>t</title></head><body><p>x</p></body></html>"
    once = server_mod.own_margins(view)
    check("167: every print view the server serves, PETs and GETs, has an empty box at the head and the foot of its "
          "page's margin, once, which keeps the date, the title, the page's address and the page count off paper, "
          "and so do the canvas print and any print of the page itself",
          once.count(server_mod.PRINT_MARGINS) == 1 and server_mod.own_margins(once) == once
          and once.index(server_mod.PRINT_MARGINS) < once.index("</head>"))

    class Gone(io.RawIOBase):
        def write(self, b):
            raise ConnectionAbortedError(10053, "An established connection was aborted")
    fake = server_mod.Handler.__new__(server_mod.Handler)
    fake.wfile = Gone()
    fake.request_version = "HTTP/1.1"
    fake.requestline = "GET / HTTP/1.1"
    fake.command = "GET"
    fake.close_connection = False
    try:
        fake._send(200, b"x", "text/plain")
        quiet = fake.close_connection is True
    except Exception as exc:  # noqa: BLE001
        quiet = f"{type(exc).__name__}: {exc}"
    check("167: an answer whose page let its request go, as on Windows when a Restart ends the server under it, ends "
          "quietly with no traceback in the log", quiet is True, str(quiet))

    node = shutil.which("node")
    if node:
        page_bits = "\n".join([support.i18n_js(), js_const(app_js, "PICK_SAYS"), js_function(app_js, "windowPicks"),
                               "let PICKING = false;", js_function(app_js, "picking"), js_function(app_js, "windowRecent"),
                               js_function(app_js, "recentNames"),
                               # each app's own projects for Open Recent from its own part since the fifth build
                               # (23 October 2026), registered with the family as the page registers them
                               js_function(app_js, "sectionsOf"), js_function(app_js, "distilRecent"),
                               js_const(support.text("apps/sift/static/sift_settings.js"), "siftRecent"),
                               js_const(support.text("apps/trace/static/trace.js"), "trRecent"),
                               "const FAMILY_APPS = {};", support.distil_hooks(app_js), js_function(app_js, "distilTitle"),
                               "FAMILY_APPS.sift = { recent: siftRecent }; FAMILY_APPS.trace = { recent: trRecent };",
                               js_const(app_js, "titleShown"), js_const(app_js, "titleText"), js_const(app_js, "titled"), js_const(app_js, "caseShown"),
                               js_function(app_js, "pageTitle"), js_function(app_js, "drawServerOps")])
        harness = scratch / "page-167.js"
        harness.write_text(r"""
const bits = require('fs').readFileSync(process.argv[2], 'utf8');
function world(withWindow, app) {
  const els = {};
  const el = (id, extra) => (els[id] = Object.assign({ id, hidden: false, textContent: '', disabled: false, closest: () => els[id + '-row'] }, extra || {}));
  ['work', 'themes', 'sift', 'sift-search', 'trace', 'library', 'home-project', 'rail-case', 'th-case', 'sf-name', 'sfs-name',
   'tr-name', 'hp-name', 'server-restart', 'server-quit', 'server-old', 'close-sub', 'set-quit-closed', 'set-quit-closed-row'].forEach((id) => el(id));
  const calls = [];
  const window = withWindow ? {
    idiographPick: (says, files) => { calls.push(['pick', says, files]); return Promise.resolve(window.__answer); },
    idiographRecent: (list, feedback) => { calls.push(['recent', list, feedback]); },
  } : {};
  const document = { body: { classList: { add() {}, remove() {} } } };
  // the page's app, Idiograph unless named (the split's third build)
  const names = { idiograph: 'Idiograph', sift: 'Sift', trace: 'Trace' };
  const env = { $: (id) => els[id], window, document, calls, els, APP: app || 'idiograph', APP_NAME: names[app || 'idiograph'],
    demoRows: (d) => (d.demos || []), DEMO_ID: 'demo', FEEDBACK: { on: true }, TH: { mode: 'pets', project: { name: 'Dog routines' } },
    SERVER: { info: null, old: false }, S: { data: null } };
  const fn = new Function(...Object.keys(env), bits + '\nreturn { picking, windowPicks, windowRecent, pageTitle, drawServerOps, PICK_SAYS };');
  return Object.assign(env, fn(...Object.values(env)));
}
(async () => {
  const out = {};
  const tab = world(false);
  const asked = [];
  out.tab = { picks: tab.windowPicks(), answer: await tab.picking((p) => { asked.push(p === undefined ? 'none' : p); return { chosen: true }; }, null, 'x') , asked };
  const win = world(true);
  win.window.__answer = '/home/wren/Dog walks';
  const sent = [];
  out.window = { picks: win.windowPicks(), answer: await win.picking((p) => { sent.push(p); return { chosen: true, folder: p }; }, null, win.PICK_SAYS.newProject) };
  win.window.__answer = null;
  out.cancel = await win.picking((p) => { sent.push(p); return { chosen: true }; }, null, win.PICK_SAYS.project, true);
  out.sent = sent; out.calls = win.calls.filter((c) => c[0] === 'pick');
  // Open Recent: each app's own projects, Idiograph's with the demo last, each with what opens it, and none for a folder gone
  const home = { reviews: [{ name: 'Dog sift', folder: '/s', there: true }, { name: 'Gone', folder: '/g', there: false }],
    traces: [{ name: 'Dog trace', folder: '/t', there: true }], demos: [{ path: 'x' }], demo_project: { name: 'Demo' } };
  home.projects = [{ id: 'p1', project: { name: 'Walks' }, there: true }];
  win.windowRecent(home);
  out.recent = win.calls.filter((c) => c[0] === 'recent');
  out.byApp = ['sift', 'trace'].map((app) => { const w = world(true, app); w.windowRecent(Object.assign({}, home, { demos: [], projects: [] }));
    return w.calls.filter((c) => c[0] === 'recent').map((c) => c[1]); });
  tab.windowRecent({ reviews: [] });
  out.tabRecent = tab.calls.length;
  // the title, from the bar of the screen in front
  const t = world(false);
  const only = (id) => { ['work', 'themes', 'sift', 'sift-search', 'trace', 'library'].forEach((s) => { t.els[s].hidden = s !== id; }); };
  out.titles = {};
  only('work'); t.els['rail-case'].textContent = 'Rowan'; out.titles.work = t.pageTitle();
  only('themes'); t.els['th-case'].textContent = 'Rowan'; out.titles.pets = t.pageTitle();
  t.TH.mode = 'gets'; out.titles.gets = t.pageTitle();
  only('sift'); t.els['sf-name'].textContent = 'Dog sift'; out.titles.sift = t.pageTitle();
  only('trace'); t.els['tr-name'].textContent = 'Dog trace'; out.titles.trace = t.pageTitle();
  only('library'); t.els['home-project'].hidden = true; out.titles.home = t.pageTitle();
  t.els['home-project'].hidden = false; t.els['hp-name'].textContent = 'Walks'; out.titles.project = t.pageTitle();
  // Closing and its tick hidden in the window alone
  const d = world(false);
  d.SERVER.info = { window: true }; d.drawServerOps(); const inWindow = [d.els['close-sub'].hidden, d.els['set-quit-closed-row'].hidden];
  d.SERVER.info = { window: false }; d.drawServerOps(); const inTab = [d.els['close-sub'].hidden, d.els['set-quit-closed-row'].hidden];
  out.closing = { inWindow, inTab };
  console.log(JSON.stringify(out));
})();
""", encoding="utf-8")
        bits_file = scratch / "page-167-bits.js"
        bits_file.write_text(page_bits, encoding="utf-8")
        run = subprocess.run([node, str(harness), str(bits_file)], capture_output=True, text=True, encoding="utf-8")
        try:
            got = json.loads(run.stdout.strip().splitlines()[-1])
        except (ValueError, IndexError):
            got = {}
        check("167: in a browser, with no window, Choose asks the server's own dialog as before, with no path",
              got.get("tab") == {"picks": False, "answer": {"chosen": True}, "asked": ["none"]}, run.stderr[-400:] or str(got.get("tab")))
        check("167: in the window, Choose asks the window's dialog with its words, sends the folder chosen as if typed, "
              "and a dialog cancelled sends nothing",
              (got.get("window") or {}).get("answer") == {"chosen": True, "folder": "/home/wren/Dog walks"}
              and got.get("cancel") == {"chosen": False} and got.get("sent") == ["/home/wren/Dog walks"]
              and got.get("calls") == [["pick", "Choose the folder for the new project.", False],
                                       ["pick", "Choose the folder that holds your participants.", True]], str(got.get("calls")))
        check("167, 20 October: the home screen hands the window its own app's projects for Open Recent, Idiograph's with "
              "the demo last, Sift's and Trace's on their own pages, with what opens each, none whose folder is gone, and "
              "whether Send feedback is there, and a browser's page hands nothing",
              got.get("recent") == [["recent", [{"part": "distil", "name": "Walks", "id": "p1"},
                                                {"part": "distil", "name": "Demo", "id": "demo", "demo": True}], True]]
              and got.get("byApp") == [[[{"part": "sift", "name": "Dog sift", "folder": "/s"}]],
                                       [[{"part": "trace", "name": "Dog trace", "folder": "/t"}]]]
              and got.get("tabRecent") == 0
              and "recent: (...a) => distilRecent(...a)," in app_js and "recent: siftRecent" in support.text("apps/sift/static/sift_settings.js")
              and "recent: trRecent" in support.text("apps/trace/static/trace.js"), str(got.get("recent"))[:400] + str(got.get("byApp")))
    else:
        skip("167: the page's window parts under node", "node is not on this machine")
    check("167: Ctrl+Y redoes off a Mac, on the statements screen and on a board, as Windows "
          "names Redo and the window's Edit menu presses it",
          "const REDO_Y = (e) => !MAC && e.ctrlKey && !e.shiftKey && !e.altKey && (e.key === 'y' || e.key === 'Y');" in app_js
          and "|| REDO_Y(e)) {\n    const backwards = !e.shiftKey && !REDO_Y(e);" in app_js
          and themes_js.count("REDO_Y(e)") == 2)

    # ── C. window.js under node: the settings kept, the place, closing, the menu's acts, the zoom keys
    if node:
        harness = scratch / "window-167.js"
        harness.write_text(r"""
const src = require('fs').readFileSync(process.argv[2], 'utf8');
class Storage {
  constructor() { this._m = new Map(); }
  get length() { return this._m.size; }
  key(i) { return [...this._m.keys()][i] || null; }
  getItem(k) { return this._m.has(String(k)) ? this._m.get(String(k)) : null; }
  setItem(k, v) { this._m.set(String(k), String(v)); }
  removeItem(k) { this._m.delete(String(k)); }
  clear() { this._m.clear(); }
}
class Ev { constructor(type, o) { this.type = type; Object.assign(this, o || {}); this.defaultPrevented = false; } preventDefault() { if (this.cancelable) this.defaultPrevented = true; } stopPropagation() {} }
function load(os, seed, pre) {
  const t = { invoked: [], on: {}, clicked: [] };
  const local = new Storage(), session = new Storage();
  (pre || []).forEach(([k, v]) => local.setItem(k, v));
  const target = () => ({ dispatchEvent: (e) => { for (const f of t.on[e.type] || []) f(e); return !e.defaultPrevented; } });
  const field = target();
  const button = (id) => ({ id, disabled: false, offsetParent: {}, closest: () => null, click() { t.clicked.push(id); } });
  const win = {
    __IDIOGRAPH_OS__: os, __IDIOGRAPH_SEED__: seed, Storage, localStorage: local, sessionStorage: session,
    Event: Ev, KeyboardEvent: Ev, PageTransitionEvent: Ev, location: { reload() { t.reloaded = true; } },
    addEventListener: (n, f) => { (t.on[n] = t.on[n] || []).push(f); },
    dispatchEvent: (e) => { for (const f of t.on[e.type] || []) f(e); return !e.defaultPrevented; },
    btoa: (s) => Buffer.from(s, 'latin1').toString('base64'),
    __TAURI_INTERNALS__: { invoke: (cmd, args) => { t.invoked.push([cmd, args]); return Promise.resolve(t.answers && cmd in t.answers ? t.answers[cmd] : null); } },
  };
  const document = { activeElement: field, body: field, getElementById: (id) => (t.buttons || []).includes(id) ? button(id) : null };
  global.Event = Ev; global.KeyboardEvent = Ev; global.PageTransitionEvent = Ev; global.document = document;
  new Function('window', 'document', src)(win, document);
  Object.assign(t, { win, local, session, field });
  return t;
}
const tick = () => new Promise((r) => setTimeout(r, 30));
(async () => {
  const out = {};
  // seeded once in a window: the app's settings in, a stale one of the app's out, another site's left, the place in
  const a = load('macos', { local: { 'idiograph-shut': '["sift"]', 'idiograph-theme': 'dark' }, session: { 'idiograph-home': 'p1' } },
    [['idiograph-theme', 'light'], ['idiograph-old', 'x'], ['elsewhere', 'y']]);
  out.seeded = { local: Object.fromEntries(a.local._m), session: a.session.getItem('idiograph-home'), keep: a.invoked.filter((c) => c[0] === 'keep').length };
  a.local.setItem('idiograph-guide', 'open'); a.local.setItem('other', '1'); a.local.removeItem('idiograph-shut'); a.session.setItem('idiograph-return', 'r');
  out.mirrored = a.invoked.filter((c) => c[0] === 'keep').map((c) => c[1]);
  // nothing kept yet: the port's own settings handed over
  const first = load('windows', { local: null, session: {} }, [['idiograph-theme', 'dark'], ['elsewhere', 'z']]);
  out.adopted = first.invoked.filter((c) => c[0] === 'keep').map((c) => c[1]);
  // closing a clean page: told it is going, its place handed over
  const c = load('macos', { local: {} }, []);
  c.on.pagehide = [() => { c.session.setItem('idiograph-return', '{"screen":"work"}'); }];
  c.win.__idiographClosing();
  await tick();
  out.clean = c.invoked.filter((x) => x[0] === 'closing').map((x) => x[1]);
  // a page with typed words a save keeps: saved, then closed with no question
  const d = load('macos', { local: {} }, []);
  let dirty = true;
  d.on.beforeunload = [(e) => { if (dirty) e.preventDefault(); }];
  d.win.savePending = () => { dirty = false; return Promise.resolve(true); };
  d.win.__idiographClosing(); await tick();
  out.saved = d.invoked.filter((x) => x[0] === 'closing').map((x) => x[1].step);
  // typed words that will not save: the window asks, and kept open when he says Cancel
  const e = load('windows', { local: {} }, []);
  e.on.beforeunload = [(ev) => ev.preventDefault()];
  e.win.savePending = () => Promise.resolve(false);
  e.answers = { closing: false };
  e.win.__idiographClosing(); await tick();
  out.unsaved = e.invoked.filter((x) => x[0] === 'closing').map((x) => x[1].step);
  // the menu's acts: Settings and Shortcuts press the bar's own buttons, Undo the page's own key first
  const m = load('macos', { local: {} }, []);
  m.buttons = ['th-settings', 'th-help'];
  m.win.__idiographMenu('settings'); m.win.__idiographMenu('shortcuts');
  m.field.dispatchEvent = (ev) => { if (ev.shiftKey) ev.preventDefault(); return true; };
  m.win.__idiographMenu('undo'); m.win.__idiographMenu('redo');
  out.menu = { clicked: m.clicked, edit: m.invoked.filter((x) => x[0] === 'edit').map((x) => x[1]), unknown: m.win.__idiographMenu('nothing') };
  // the zoom keys, Cmd on a Mac and Ctrl elsewhere
  const z = load('macos', { local: {} }, []);
  const key = (o) => { const ev = new Ev('keydown', Object.assign({ cancelable: true }, o)); for (const f of z.on.keydown) f(ev); return ev.defaultPrevented; };
  out.zoomKeys = [key({ metaKey: true, key: '=' }), key({ metaKey: true, key: '+' }), key({ metaKey: true, key: '-' }), key({ metaKey: true, key: '0' }),
    key({ ctrlKey: true, key: '=' }), key({ key: '=' })];
  out.zooms = z.invoked.filter((x) => x[0] === 'zoom').map((x) => x[1].by);
  const w = load('windows', { local: {} }, []);
  const wkey = (o) => { const ev = new Ev('keydown', Object.assign({ cancelable: true }, o)); for (const f of w.on.keydown) f(ev); return ev.defaultPrevented; };
  out.winZoom = [wkey({ ctrlKey: true, key: '-' }), wkey({ metaKey: true, key: '-' })];
  // Choose and Open Recent hand over to the window
  const p = load('windows', { local: {} }, []);
  p.answers = { pick: 'C:\\Users\\Wren\\Dog walks' };
  out.pick = await p.win.idiographPick('Choose the folder for the new project.', false);
  p.win.idiographRecent([{ part: 'distil', name: 'Walks', id: 'p1' }], true);
  out.pickCalls = p.invoked.filter((x) => x[0] === 'pick' || x[0] === 'recent').map((x) => x[1]);
  console.log(JSON.stringify(out));
  process.exit(0);
})();
""", encoding="utf-8")
        run = subprocess.run([node, str(harness), str(tauri / "window.js")], capture_output=True, text=True, encoding="utf-8")
        try:
            got = json.loads(run.stdout.strip().splitlines()[-1])
        except (ValueError, IndexError):
            got = {}
        check("167: a window lays the app's kept settings into the page's storage once, before the page reads any, "
              "takes out one of the app's the app no longer keeps, leaves another site's alone, and lays the place "
              "it opens on", got.get("seeded") == {"local": {"idiograph-theme": "dark", "elsewhere": "y", "idiograph-shut": '["sift"]'},
                                                    "session": "p1", "keep": 0}, run.stderr[-400:] or str(got.get("seeded")))
        check("167: every change the page makes to a setting of its own goes to the window to keep, and nothing else",
              got.get("mirrored") == [{"key": "idiograph-guide", "value": "open"}, {"key": "idiograph-shut", "value": None}],
              str(got.get("mirrored")))
        check("167: with nothing kept yet, the window takes the settings this port's storage holds, the page's own alone",
              got.get("adopted") == [{"all": {"idiograph-theme": "dark"}}], str(got.get("adopted")))
        check("167: closing a window tells its page it is going as a browser does, so it keeps its place, and hands "
              "the place to the window",
              got.get("clean") == [{"step": "begun"}, {"step": "done", "place": {"idiograph-return": '{"screen":"work"}'}}],
              str(got.get("clean")))
        check("167: what is typed and not saved is saved first, as any move saves it, and the window closes with no "
              "question; when it will not save the window asks, and Cancel keeps it open",
              got.get("saved") == ["begun", "done"] and got.get("unsaved") == ["begun", "unsaved", "kept"],
              f"{got.get('saved')} {got.get('unsaved')}")
        check("167: Settings and Keyboard Shortcuts press the buttons of the bar in view, and the Mac's Undo and Redo "
              "ask the page's own key first, leaving the field's own undo where the page leaves it",
              got.get("menu") == {"clicked": ["th-settings", "th-help"], "edit": [{"action": "undo"}], "unknown": False},
              str(got.get("menu")))
        check("167: Cmd with =, +, - and 0 on a Mac, Ctrl elsewhere, zoom the window, and nothing else does",
              got.get("zoomKeys") == [True, True, True, True, False, False] and got.get("zooms") == [1, 1, -1, 0]
              and got.get("winZoom") == [True, False], f"{got.get('zoomKeys')} {got.get('zooms')} {got.get('winZoom')}")
        check("167: Choose asks the window's dialog for its path and Open Recent hands the list over",
              got.get("pick") == "C:\\Users\\Wren\\Dog walks"
              and got.get("pickCalls") == [{"prompt": "Choose the folder for the new project.", "files": False},
                                           {"list": [{"part": "distil", "name": "Walks", "id": "p1"}], "feedback": True}],
              str(got.get("pickCalls")))
    else:
        skip("167: window.js under node", "node is not on this machine")
    ids = re.findall(r"'((?:btn|lib|th|sf|sfs|tr)-(?:settings|help|feedback))'", window_js)
    check("167: every bar button the menu presses is one the page has", ids and all(f'id="{i}"' in index or f"'{i}'" in app_js
                                                                                 or f"$('{i}')" in support.text("apps/sift/static/sift_search.js") + trace_js
                                                                                 for i in ids), str(ids))
    check("167: the window keeps the page's own keys, idiograph-, and the two places the page keeps in its session, "
          "the Restart's and the home screen's", "pub const PREFIX: &str = \"idiograph-\";" in keep_rs
          and "var PREFIX = 'idiograph-';" in window_js
          and 'pub const PLACES: [&str; 2] = ["idiograph-return", "idiograph-home"];' in keep_rs
          and "var PLACES = ['idiograph-return', 'idiograph-home'];" in window_js
          and "const RETURN_KEY = 'idiograph-return';" in app_js and "const HOME_KEY = 'idiograph-home';" in app_js)

    # ── D. the window: the menus, the state kept, the log, the notice, the save panel's kinds
    ids_made = set(re.findall(r'item\(app, "([a-z-]+)"', menu_rs))
    handled_ids = set(re.findall(r'"([a-z-]+)"', main_rs.split("fn menu_event(", 1)[1].split("\n}\n", 1)[0]))
    check("167: every menu item of the window's own does something", ids_made <= handled_ids, str(sorted(ids_made - handled_ids)))
    check("167: the main window's size, place, maximised and full screen are kept across a quit by the window-state "
          "plugin, never whether it was shown, and the window opens on the place its page last closed on",
          'tauri-plugin-window-state = "=2.5.0"' in cargo and ".with_filter(|label| label == MAIN)" in main_rs
          and "StateFlags::SIZE | StateFlags::POSITION | StateFlags::MAXIMIZED | StateFlags::FULLSCREEN" in main_rs
          and "VISIBLE" not in main_rs.split("fn window_state_flags", 1)[1].split("}\n", 1)[0]
          and "app_window(app, port, Some(MAIN), place)" in main_rs)
    check("167: the bundle's version is the server's own", conf["version"] == server_mod.VERSION)
    check("167: the checks' world for the window stays invented", not any(re.search(rf"\b{n}\b", window_js + menu_rs)
                                                                         for n in STUDY_PSEUDONYMS))
