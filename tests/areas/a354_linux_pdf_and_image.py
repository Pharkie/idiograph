"""Area 354: Export as PDF and Save as an image on Linux (linux4, 9 November 2026, build 4 of the Linux plan). Until
typst5 the Linux window, which has no print-to-file or picture of its own, asked the server (`/api/page-file`) to make
the file with a browser on the computer, headless. Since typst5 (9 November 2026, Adam: Typst for every PDF and
picture, no fallback) every computer is the same: the page asks the server, which makes the file with Typst, so on
Linux no browser is looked for and none is needed. Here, with a faked platform: the table of PETs and the canvas made
on "linux" as on any computer, no browser looked for on the path, the server's way for Linux gone with its route, and
window.js giving no system a way of its own. What only a real Linux run proves (the typesetter beside the frozen
server in the .deb and the AppImage, a file written from the window there) is not here. Nothing here uses a
participant's words."""
from __future__ import annotations

import json
import shutil
import subprocess
import sys
from pathlib import Path

from . import support
from .support import check, skip

HARNESS = r"""
const fs = require('fs');
const src = fs.readFileSync(process.argv[2], 'utf8');
function load(os, bridge) {
  const win = { __IDIOGRAPH_OS__: os, location: { href: 'http://127.0.0.1:8800/' }, document: { title: '' },
    addEventListener: () => {}, print: () => {}, btoa: (s) => Buffer.from(s, 'latin1').toString('base64'),
    open: () => ({}) };
  if (bridge) win.__TAURI_INTERNALS__ = { invoke: () => Promise.resolve(null) };
  new Function('window', src)(win);
  return win;
}
const out = {};
for (const os of ['other', 'linux', 'macos', 'windows']) {
  const w = load(os, true);
  out[os] = [typeof w.idiographByServer, typeof w.idiographSavePdf, typeof w.idiographSavePng];
}
console.log(JSON.stringify(out));
"""


def test_linux_pdf_and_image(scratch: Path):
    print("\n354. Export as PDF and Save as an image on Linux: the same as on every computer since typst5, the server "
          "making the file with Typst and no browser looked for")
    import canvas_out
    import idiograph_routes as routes
    import server as server_mod
    import typeset

    if not typeset.available():
        skip("354: the exports on a faked Linux", "typst-py is not installed")
        return
    pristine = support.DEMO_SHIPPED
    root = scratch / "a354"
    shutil.rmtree(root, ignore_errors=True)
    (root / "Juno" / "Working").mkdir(parents=True)
    shutil.copy2(pristine / "Juno - EN & ES.xlsx", root / "Juno" / "Juno - EN & ES.xlsx")
    for side in (pristine / "Working").glob("Juno - *"):
        shutil.copy2(side, root / "Juno" / "Working" / side.name)
    book = root / "Juno" / "Juno - EN & ES.xlsx"
    looked: list = []
    real = (sys.platform, shutil.which, server_mod.ROOT_OVERRIDE, server_mod.STATE_MEMORY)
    try:
        sys.platform = "linux"
        shutil.which = lambda name, *a, **k: (looked.append(name), None)[1]
        server_mod.ROOT_OVERRIDE, server_mod.STATE_MEMORY = str(root), {"recent": []}
        table = routes.api_themes_export({"workbook": str(book), "op": "pdf"})
        picture = routes.api_themes_export({"workbook": str(book), "op": "canvas", "kind": "png"})
    finally:
        sys.platform, shutil.which, server_mod.ROOT_OVERRIDE, server_mod.STATE_MEMORY = real
    browsers = [n for n in looked if any(b in n for b in ("chrom", "brave", "edge"))]
    check("354: on Linux Export as PDF and Save as an image are the server's, made with Typst, no browser looked for",
          (root / "Juno" / table["name"]).read_bytes()[:5] == b"%PDF-"
          and canvas_out.png_size((root / "Juno" / picture["name"]).read_bytes())[0] > 0 and not browsers,
          json.dumps([table.get("name"), picture.get("name"), looked]))
    check("354: the Linux window's own way, /api/page-file, is gone with the browser it reached",
          "/api/page-file" not in routes.ROUTES and "/api/page-file" not in server_mod.WINDOW_ONLY
          and "/api/page-file" not in server_mod.POST_ONLY)

    # window.js gives no system a way of its own to save a PDF or a picture
    node = shutil.which("node")
    if not node:
        skip("354: window.js under node", "node is not on this machine")
        return
    harness = scratch / "linux-pdf-354.js"
    harness.write_text(HARNESS, encoding="utf-8")
    out = subprocess.run([node, str(harness), str(support.TOOL / "packaging" / "tauri" / "window.js")],
                         capture_output=True, text=True, encoding="utf-8", timeout=60)
    try:
        got = json.loads(out.stdout.strip().splitlines()[-1])
    except (ValueError, IndexError):
        got = {}
    none = ["undefined", "undefined", "undefined"]
    check("354: window.js offers no system a PDF or a picture of its own, Linux, the Mac and Windows alike",
          got == {"other": none, "linux": none, "macos": none, "windows": none}, json.dumps(got) + out.stderr[-200:])
