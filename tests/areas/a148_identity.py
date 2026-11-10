from __future__ import annotations

import sys
from pathlib import Path

import make_app

from . import support
from .support import check


def test_identity(scratch):
    print("\n148. Idiograph's identity, 15 October: direction C, Bracket, the orange dot between square brackets, "
          "each part's mark in the same stroke and its own colour, Trace's raised into its citation, the lockup, "
          "the favicon and the app icon, the crux and the amber at 4.5 to 1 as words, the dark crux clear of the amber. "
          "Since the test review of 18 October the marks, colours, contrasts and places are review shots, and what "
          "the server serves and the builds draw stays")
    import http.server
    import struct
    import threading
    import urllib.request
    import zlib
    import server as server_mod

    read = lambda path: Path(path).read_text(encoding="utf-8")
    marks, favicon = support.text("family/static/marks.svg"), support.text("apps/idiograph/static/favicon.svg")

    # ── E. the favicon, served
    check("148: the server serves the 32 pixel PNG at /favicon.png, and the Mac build ships make_app, which draws it",
          server_mod.FAVICON_PATH == "/favicon.png" and server_mod.FAVICON_SIZE == 32
          and "make_app" in load_module(support.source("packaging/build_mac.py")).MODULES)
    httpd = http.server.ThreadingHTTPServer(("127.0.0.1", 0), server_mod.Handler)
    threading.Thread(target=httpd.serve_forever, kwargs={"poll_interval": 0.05}, daemon=True).start()
    got = {}
    try:
        for path in ("/favicon.png", "/favicon.svg", "/marks.svg"):
            with urllib.request.urlopen(f"http://127.0.0.1:{httpd.server_address[1]}{path}", timeout=10) as r:
                got[path] = (r.status, r.headers.get("Content-Type", ""), r.read())
    finally:
        httpd.shutdown()
        httpd.server_close()
    png = got.get("/favicon.png", (0, "", b""))
    check("148: over HTTP /favicon.png is a 32 pixel PNG of the app's icon, and /favicon.svg and /marks.svg are SVG",
          png[0] == 200 and png[1] == "image/png" and png[2] == make_app.png_bytes(32, make_app.draw_icon(32))
          and struct.unpack(">II", png[2][16:24]) == (32, 32)
          and got["/favicon.svg"][:2] == (200, "image/svg+xml") and got["/favicon.svg"][2].decode("utf-8") == favicon
          and got["/marks.svg"][:2] == (200, "image/svg+xml") and got["/marks.svg"][2].decode("utf-8") == marks,
          str({k: v[:2] for k, v in got.items()}))

    # ── F. the app icon, drawn at each size
    drawn, failed = {}, []
    for size in (1024, 128, 32, 16):
        try:
            drawn[size] = make_app.draw_icon(size)
            png = make_app.png_bytes(size, drawn[size])
            raw = zlib.decompress(png[41:41 + struct.unpack(">I", png[33:37])[0]])
            if len(drawn[size]) != size * size * 4 or len(raw) != size * (1 + size * 4):
                failed.append(str(size))
        except Exception as exc:  # noqa: BLE001
            failed.append(f"{size}: {exc}")
    check("148: draw_icon draws C's mark at 1024, 128, 32 and 16 without an error, each a whole PNG", not failed, ", ".join(failed))


def load_module(path: Path):
    """A module from its file, by its stem, imported once."""
    import importlib.util
    name = f"_loaded_{path.stem}"
    if name in sys.modules:
        return sys.modules[name]
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod
