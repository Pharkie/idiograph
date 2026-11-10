"""Area 195: Print in the Mac app's windows (19 October 2026). On a Mac a window the page opens, a
print view or a table, shares its opener's web view setup, so its Print reached the app as the window
behind it, and the panel opened out of sight (Adam, 18 October 18:26). Each window now names its own
address with Print, a window opened on about:blank and written in gets the same Print from the page
that opened it, window.js sets its Print again when Tauri's own script has run after it and set its
own, which the window refuses, and a browser and Windows keep their own print.
"""
from __future__ import annotations

import json
import shutil
import subprocess

from . import support
from .support import check, skip

HARNESS = r"""
const fs = require('fs');
const src = fs.readFileSync(process.argv[2], 'utf8');
function load(os, bridge, href, title) {
  const t = { invoked: [], opened: [], printed: 0 };
  const win = {
    __IDIOGRAPH_OS__: os,
    location: { href: href },
    document: { title: title || '' },
    addEventListener: () => {},
    print: () => { t.printed += 1; },
    btoa: (s) => Buffer.from(s, 'latin1').toString('base64'),
  };
  win.open = (url, target) => {
    t.opened.push([url, target]);
    // a window of the app's, its address its own, and its own print, which does nothing on a Mac
    return { location: { href: url === '' ? 'about:blank' : url }, document: { title: '' }, print: () => { t.printed += 1; } };
  };
  if (bridge) win.__TAURI_INTERNALS__ = { invoke: (cmd, args) => { t.invoked.push([cmd, args]); return Promise.resolve(null); } };
  t.baseOpen = win.open;
  t.basePrint = win.print;
  new Function('window', src)(win);
  t.win = win;
  return t;
}
const out = {};
const table = 'http://127.0.0.1:8800/themes/print?workbook=x&board=b1&auto=0';
// a Mac: the page's own Print names its address and title
const mac = load('macos', true, 'http://127.0.0.1:8800/', 'Dog walks');
mac.win.print();
// a table opened from it, on its address, and the canvas's print, on about:blank then written in
const tab = mac.win.open(table, '_blank');
tab.document.title = 'Pip - Board 1 - PETs';
tab.print();
const blank = mac.win.open('about:blank', '_blank');
blank.location.href = 'http://127.0.0.1:8800/';
blank.document.title = 'Pip - Board 1 - PETs canvas';
blank.print();
out.mac = { invoked: mac.invoked, native: mac.printed, opened: mac.opened };
// Tauri's own script run after this one, as a Mac runs every window's scripts in each, sets its print,
// which the window refuses, and the next run of this file sets the page's Print again
const again = load('macos', true, 'http://127.0.0.1:8800/themes/print?board=b1', 'Pip - Board 1 - PETs');
again.win.print = () => { again.invoked.push(['plugin:webview|print']); };
new Function('window', src)(again.win);
again.win.print();
out.again = again.invoked;
// Windows and a browser: print and open as they were
const w = load('windows', true, 'http://127.0.0.1:8800/');
out.windows = { print: w.win.print === w.basePrint, open: w.win.open === w.baseOpen };
const b = load('macos', false, 'http://127.0.0.1:8800/');
out.browser = { print: b.win.print === b.basePrint, open: b.win.open === b.baseOpen };
console.log(JSON.stringify(out));
"""


def test_mac_print(scratch):
    print("\n195. Print in the Mac app's windows (19 October): a print view's or a table's Print opens the print panel on "
          "its own window, and a browser and Windows print as they did")
    node = shutil.which("node")
    if not node:
        skip("195: window.js under node", "node is not on this machine")
        return
    harness = scratch / "mac-print-195.js"
    harness.write_text(HARNESS, encoding="utf-8")
    run = subprocess.run([node, str(harness), str(support.source("packaging/tauri/window.js"))],
                         capture_output=True, text=True, encoding="utf-8")
    try:
        got = json.loads(run.stdout.strip().splitlines()[-1])
    except (ValueError, IndexError):
        got = {}
    table = "http://127.0.0.1:8800/themes/print?workbook=x&board=b1&auto=0"
    mac = got.get("mac") or {}
    check("195: on a Mac the page's Print, a table's opened from it and the canvas's written into about:blank each ask "
          "the window for its print panel with that window's own address and title, the canvas's with its opener's "
          "address and its own title, and the web view's own print is never called",
          mac.get("invoked") == [["print", {"href": "http://127.0.0.1:8800/", "title": "Dog walks"}],
                                 ["print", {"href": table, "title": "Pip - Board 1 - PETs"}],
                                 ["print", {"href": "http://127.0.0.1:8800/", "title": "Pip - Board 1 - PETs canvas"}]]
          and mac.get("native") == 0
          and mac.get("opened") == [[table, "_blank"], ["about:blank", "_blank"]],
          run.stderr[-300:] or str(mac))
    check("195: run again after Tauri's own script has set its print, which the window refuses, the page's Print is "
          "this file's again", got.get("again") == [["print", {"href": "http://127.0.0.1:8800/themes/print?board=b1", "title": "Pip - Board 1 - PETs"}]],
          str(got.get("again")))
    check("195: on Windows, whose web view prints by itself, and in a browser, with no window's bridge, print and "
          "window.open are the page's own", got.get("windows") == {"print": True, "open": True}
          and got.get("browser") == {"print": True, "open": True}, f"{got.get('windows')} {got.get('browser')}")
