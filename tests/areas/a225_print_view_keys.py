"""Area 225: the Mac app's print views keep their own keys, New Window opens on what the window in front
shows, and the corpus is read only from the path a config names (20 October 2026, the backlog).

On a Mac a window the page opens, a print view or a table, shares its opener's message handler, so what
it asked of the app came as the window behind it: Cmd + = and Cmd + minus zoomed the window behind, and
Cmd + S, which a print view takes for its save, reached nothing of its own. Each window now names its
own address and title with the zoom, as with Print, and in a Mac's print view Cmd + S opens that window's
print panel, where Save as PDF is. A window the page opened on about:blank and wrote in, the canvas's
print, loses the keys as it is written, and gets them back from its opener once its page is there, and as
it has its opener's address it is never taken for the app's page, so closing it no longer closes the
window behind it and the app (seen on the drive build of 20 October). File,
New Window hands the new window the place of the window it came from, as a restart's, and its address
after #open=, the form Open in a new window gives.

The checks hold behaviour, in node, on window.js with the window's bridge stubbed, and on corpus.py with
an invented corpus on bread baking.
"""
from __future__ import annotations

import json
import shutil
import subprocess

import corpus

from . import support
from .support import check, skip

HARNESS = r"""
const fs = require('fs');
const src = fs.readFileSync(process.argv[2], 'utf8');
function keyEvent(key, code, mods) {
  const e = { key, code, metaKey: !!mods.meta, ctrlKey: !!mods.ctrl, altKey: false, shiftKey: false, defaultPrevented: false,
    preventDefault() { this.defaultPrevented = true; }, stopPropagation() {} };
  return e;
}
function load(os, href, title, more) {
  const t = { invoked: [], listeners: [] };
  const url = new URL(href);
  const win = Object.assign({
    __IDIOGRAPH_OS__: os,
    location: { href, pathname: url.pathname },
    document: { title: title || '' },
    addEventListener: (type, fn) => { if (type === 'keydown') t.listeners.push(fn); },
    print: () => {},
    btoa: (s) => Buffer.from(s, 'latin1').toString('base64'),
    __TAURI_INTERNALS__: { invoke: (cmd, args) => { t.invoked.push([cmd, args]); return Promise.resolve(null); } },
  }, more || {});
  // a window opened on about:blank and then written in, the canvas's print, which takes its opener's address
  win.open = (u) => {
    const attrs = {};
    const body = { childNodes: [] };
    const tab = {
      closed: false, keys: [],
      location: { href: u || 'about:blank', pathname: u ? new URL(u, href).pathname : 'blank' },
      document: { title: '', readyState: 'complete', body, documentElement: {
        hasAttribute: (n) => n in attrs, setAttribute: (n, v) => { attrs[n] = v; } } },
      addEventListener: (type, fn) => { if (type === 'keydown') tab.keys.push(fn); },
      write(title) { body.childNodes.push({}); this.location.href = href; this.location.pathname = url.pathname; this.document.title = title; },
    };
    t.tab = tab;
    return tab;
  };
  new Function('window', src)(win);
  t.win = win;
  t.press = (key, code, mods) => { const e = keyEvent(key, code, mods); t.listeners.forEach((fn) => fn(e)); return e.defaultPrevented; };
  return t;
}
const wait = (ms) => new Promise((r) => setTimeout(r, ms));
(async () => {
  const out = {};
  const table = 'http://127.0.0.1:8800/themes/print?workbook=x&board=b1';
  const gets = 'http://127.0.0.1:8800/gets/print?root=r&board=g1';
  // a Mac's print view: the zoom of this window by its own address and title, and Cmd+S its print panel
  const view = load('macos', table, 'Ada - Board 1 - PETs');
  out.view = [view.press('=', 'Equal', { meta: true }), view.press('-', 'Minus', { meta: true }),
              view.press('0', 'Digit0', { meta: true }), view.press('s', 'KeyS', { meta: true })];
  out.viewAsked = view.invoked;
  const gview = load('macos', gets, 'Bread - GETs');
  gview.press('s', 'KeyS', { meta: true });
  out.getsAsked = gview.invoked;
  // the app's own page: its zoom as before, named by its own address, and Cmd+S left to the page
  const app = load('macos', 'http://127.0.0.1:8800/', 'Bread baking');
  out.app = [app.press('=', 'Equal', { meta: true }), app.press('s', 'KeyS', { meta: true })];
  out.appAsked = app.invoked;
  // Windows: Ctrl and the zoom keys named the same way, and Ctrl+S left as it was
  const w = load('windows', table, 'Ada - Board 1 - PETs');
  out.windows = [w.press('+', 'Equal', { ctrl: true }), w.press('s', 'KeyS', { ctrl: true })];
  out.windowsAsked = w.invoked;
  // the canvas's print: opened on about:blank, written in, then its keys given back from the opener
  const opener = load('macos', 'http://127.0.0.1:8800/', 'Bread baking');
  const tab = opener.win.open('about:blank', '_blank');
  await wait(300);
  out.beforeWritten = tab.keys.length;
  tab.write('Ada - Board 1 - PETs canvas');
  await wait(800);
  out.afterWritten = tab.keys.length;
  const ev = keyEvent('=', 'Equal', { meta: true });
  tab.keys.forEach((fn) => fn(ev));
  const sv = keyEvent('s', 'KeyS', { meta: true });
  tab.keys.forEach((fn) => fn(sv));
  out.canvasAsked = opener.invoked;
  out.canvasPrevented = [ev.defaultPrevented, sv.defaultPrevented];
  // a key another listener took already is not taken twice
  const taken = keyEvent('=', 'Equal', { meta: true });
  taken.defaultPrevented = true;
  const before = opener.invoked.length;
  tab.keys.forEach((fn) => fn(taken));
  out.takenTwice = opener.invoked.length - before;
  // a table opened on its own address has window.js of its own, and gets no second listener
  const served = load('macos', 'http://127.0.0.1:8800/', 'Bread baking');
  const st = served.win.open(table, '_blank');
  await wait(800);
  out.servedKeys = st.keys.length;
  // New Window from a board: the place it shows handed over as the new window's start and its #open= address
  const spot = { screen: 'pets', path: '/bread/P1 Ada - EN & ES.xlsx', board: 'v2', label: 'P1 - Ada', under: null };
  const board = load('macos', 'http://127.0.0.1:8800/', 'Bread baking', { spotNow: () => spot });
  board.press('n', 'KeyN', { meta: true });
  out.newWindow = board.invoked;
  // from the home screen, and from a print view: the home screen, as before
  const home = load('macos', 'http://127.0.0.1:8800/', 'Bread baking', { spotNow: () => null });
  home.win.__idiographNewWindow();
  out.newHome = home.invoked;
  const pv = load('windows', table, 'Ada - Board 1 - PETs');
  pv.press('n', 'KeyN', { ctrl: true });
  out.newFromView = pv.invoked;
  out.spot = spot;
  console.log(JSON.stringify(out));
})().catch((e) => { console.error(String(e && e.stack || e)); process.exit(1); });
"""


def test_print_view_keys(scratch):
    print("\n225. The Mac app's print views keep their own zoom and save, New Window opens on what the window in front "
          "shows, and the corpus is read only from the path a config names (20 October)")
    corpus_part(scratch)
    shell = support.source("packaging/tauri/src-tauri/src/main.rs").read_text(encoding="utf-8")
    zoom_cmd = shell.split("async fn zoom(", 1)[1].split("\n}\n", 1)[0] if "async fn zoom(" in shell else ""
    menu = shell.split("fn menu_event(", 1)[1].split("\n}\n", 1)[0] if "fn menu_event(" in shell else ""
    check("225: the app zooms the window whose page asked, found by its own address and title, and View's Zoom In, "
          "Zoom Out and Actual Size and File, New Window act on the window in front",
          "let target = asking(&window, href.as_deref(), title.as_deref());" in zoom_cmd and "zoom_on(&target, by);" in zoom_cmd
          and "Some(window) => zoom_on(&window, by)," in menu and "front(app, true)" in menu and "NEW_WINDOW_JS" in menu)
    own = shell.split("fn own_page(", 1)[1].split("\n}\n", 1)[0] if "fn own_page(" in shell else ""
    closes = shell.split("WindowEvent::CloseRequested", 1)[1].split("});", 1)[0] if "WindowEvent::CloseRequested" in shell else ""
    check("225: a window the page opened on about:blank and wrote in, which has its opener's address, is never taken "
          "for the app's own page, so closing the canvas's print closes it alone, never the window behind it",
          'if url.scheme() == "about"' in shell and "WRITTEN.lock().unwrap().push(label.clone());" in shell
          and "!WRITTEN.lock().unwrap().iter().any(|label| label == window.label())" in own
          and "if own_page(&webview) {" in closes)
    node = shutil.which("node")
    if not node:
        skip("225: window.js in node", "node is not on this machine")
        return
    harness = scratch / "print-view-keys-225.js"
    harness.write_text(HARNESS, encoding="utf-8")
    ran = subprocess.run([node, str(harness), str(support.source("packaging/tauri/window.js"))],
                         capture_output=True, text=True, encoding="utf-8", timeout=60)
    o = json.loads(ran.stdout.strip().splitlines()[-1]) if ran.returncode == 0 and ran.stdout.strip() else {}
    why = (ran.stderr or ran.stdout)[-400:]
    table = "http://127.0.0.1:8800/themes/print?workbook=x&board=b1"
    named = {"href": table, "title": "Ada - Board 1 - PETs"}
    check("225: in a Mac's print view Cmd + =, Cmd + minus and Cmd + 0 zoom that window, named by its own address and "
          "title, and Cmd + S opens its own print panel, each key taken there",
          o.get("view") == [True, True, True, True]
          and o.get("viewAsked") == [["zoom", dict(named, by=1)], ["zoom", dict(named, by=-1)], ["zoom", dict(named, by=0)],
                                     ["print", named]], why + str(o.get("viewAsked")))
    check("225: Cmd + S in the GETs' print view opens its own print panel too",
          o.get("getsAsked") == [["print", {"href": "http://127.0.0.1:8800/gets/print?root=r&board=g1", "title": "Bread - GETs"}]],
          str(o.get("getsAsked")))
    check("225: on the app's own page the zoom names that page and Cmd + S is left to the page, and on Windows the zoom "
          "is named the same way and Ctrl + S left as it was",
          o.get("app") == [True, False]
          and o.get("appAsked") == [["zoom", {"by": 1, "href": "http://127.0.0.1:8800/", "title": "Bread baking"}]]
          and o.get("windows") == [True, False] and o.get("windowsAsked") == [["zoom", dict(named, by=1)]],
          str([o.get("app"), o.get("appAsked"), o.get("windows"), o.get("windowsAsked")]))
    check("225: the canvas's print, opened on about:blank and written in, gets its keys once its page is there, its zoom "
          "and Cmd + S asked for it by its own title, never a key twice, and a table on its own address none from its opener",
          o.get("beforeWritten") == 0 and o.get("afterWritten") == 1
          and o.get("canvasAsked") == [["zoom", {"by": 1, "href": "http://127.0.0.1:8800/", "title": "Ada - Board 1 - PETs canvas"}],
                                       ["print", {"href": "http://127.0.0.1:8800/", "title": "Ada - Board 1 - PETs canvas"}]]
          and o.get("canvasPrevented") == [True, True] and o.get("takenTwice") == 0 and o.get("servedKeys") == 0,
          str([o.get("beforeWritten"), o.get("afterWritten"), o.get("canvasAsked"), o.get("takenTwice"), o.get("servedKeys")]))
    nw = (o.get("newWindow") or [[None, {}]])[0]
    args = nw[1] if len(nw) > 1 and isinstance(nw[1], dict) else {}
    place = args.get("place") or {}
    try:
        started = json.loads(place.get("idiograph-return") or "null") or {}
    except ValueError:
        started = {}
    spot = o.get("spot") or {}
    from urllib.parse import unquote
    hashed = args.get("hash") or ""
    check("225: New Window from a board hands the new window that board's place as its start, as a restart's, and the "
          "same place in its address after #open=",
          nw[0] == "new_window" and {k: v for k, v in started.items() if k != "at"} == spot and started.get("at")
          and hashed.startswith("#open=") and json.loads(unquote(hashed[len("#open="):]) or "null") == spot,
          str(o.get("newWindow"))[:300])
    check("225: New Window from the home screen, or from a print view, opens the home screen as before",
          o.get("newHome") == [["new_window", {"place": {}, "hash": ""}]]
          and o.get("newFromView") == [["new_window", {"place": {}, "hash": ""}]],
          str([o.get("newHome"), o.get("newFromView")]))


def corpus_part(scratch):
    """The corpus read from the path a config names, and nothing from an empty setting."""
    md = scratch / "bread-corpus-225.md"
    md.write_text("## Starter diaries (2)\n- The dough rose slowly overnight and I felt patient for once\n"
                  "- I watched the crust darken and worried it would burn\n\n## Oven notes (1)\n"
                  "- The kitchen smelt of warm flour and I relaxed\n", encoding="utf-8")
    corpus._cache.clear()
    items = corpus.load_corpus(md)
    left = corpus.load_corpus(md, ["Oven"])
    check("225: a config that names a corpus file reads its statements, each with its source, a source left out when "
          "the config says, and counts them",
          len(items) == 3 and {i["source"] for i in items} == {"Starter diaries", "Oven notes"} and len(left) == 2
          and corpus.counts(md, None)["corpus"] == 3, str(items)[:200])
    check("225: an empty corpus setting reads nothing and names no folder, so a new install draws on the demo alone",
          not corpus.is_file("") and corpus.load_corpus("") == [] and corpus.sample("", "", 3) == []
          and corpus.counts("", "") == {"corpus": 0, "gravity": 0})
