"""What the two checks of the window share, `drive_mac.py` and `drive_windows.py`: the invented world
they open the window on, the stub on this machine that hears the window, and the steps the page is
taken through. The standard library only.

The world is the demo as a build stages it, copied in as a project of its own so its cases open from
the project's rows, a settings file that names no project, no corpus and no reference, and an
invented Sift screening and Trace document on dogs at home. Nothing here reaches anything but this
machine.
"""
from __future__ import annotations

import csv
import json
import os
import shutil
import socket
import socketserver
import threading
import time
import urllib.parse
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

# the window's port and the stub's, or a builder's own leased pair through IDIOGRAPH_DRIVE_PORT and
# IDIOGRAPH_DRIVE_STUB, so two drives on one Mac never meet (28 October)
PORT = int(os.environ.get("IDIOGRAPH_DRIVE_PORT") or 8795)
STUB = int(os.environ.get("IDIOGRAPH_DRIVE_STUB") or 8797)

RECORDS = [
    ("R001", "Morning walks and the shape of the day", "Twelve owners kept diaries of their first year with a puppy.", "Hale, P.", "2021", "include"),
    ("R002", "Shared sofas: negotiating space with a large dog", "An interview study of nine households.", "Brisk, T.", "2019", ""),
    ("R003", "Barking at the post: a sound survey", "A count of barking episodes across forty streets.", "Quill, D.", "2018", "exclude"),
    ("R004", "The old dog's last winter", "Seven carers of dogs over twelve described adjusting walks.", "Fennel, R.", "2023", "maybe"),
]
MANUSCRIPT = """# Dog routines: a review protocol

## Background

Owners often describe the walk as the spine of the day (Hale, 2021). Space in the home is negotiated
as much as it is shared (Brisk, 2019), and ageing together brings its own changes (Fennel, 2023).

## References

Brisk, T. (2019). Shared sofas. Home and Habit, 4(2), 10-22.

Fennel, R. (2023). The old dog's last winter. Journal of Invented Companions, 9(1), 1-14.

Hale, P. (2021). Morning walks and the shape of the day. Journal of Invented Companions, 7(3), 33-48.
"""


class _NoLookupServer(ThreadingHTTPServer):
    """A server bound as the standard library binds it, without its lookup of this computer's own name
    (`socket.getfqdn`), which held every server half a minute on the hosted Mac (train 173, family/server.py)."""

    def server_bind(self):
        socketserver.TCPServer.server_bind(self)
        self.server_name, self.server_port = self.server_address[:2]


def listening(port: int) -> bool:
    with socket.socket() as s:
        s.settimeout(0.3)
        return s.connect_ex(("127.0.0.1", port)) == 0


def wait_closed(port: int, seconds: float) -> float:
    """Seconds until nothing listens on `port`, or -1 when something still does after `seconds`."""
    t0 = time.time()
    while listening(port):
        if time.time() - t0 > seconds:
            return -1.0
        time.sleep(0.1)
    return round(time.time() - t0, 2)


def make_world(out: Path, stage: Path, shipped: Path) -> dict:
    world = out / "world"
    shutil.rmtree(world, ignore_errors=True)
    project = world / "project"
    shutil.copytree(stage, project)
    shutil.rmtree(project / "pristine", ignore_errors=True)
    cfg = json.loads(shipped.read_text(encoding="utf-8"))
    cfg.update(projects=[], corpus="", gravity_reference="", corpus_exclude=[], ai_suggest=False)
    (world / "config.json").write_text(json.dumps(cfg, indent=2), encoding="utf-8")
    review = world / "sift-review"
    review.mkdir(parents=True)
    with open(review / "screening.csv", "w", encoding="utf-8", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["rec_id", "title", "abstract", "authors", "year", "decision"])
        w.writerows(RECORDS)
    (world / "trace-docs").mkdir()
    (world / "trace-docs" / "Dog routines protocol.md").write_text(MANUSCRIPT, encoding="utf-8")
    (world / "trace-project").mkdir()
    (world / "drop-me.csv").write_text("rec_id,title,abstract\nD001,A dropped record,Invented.\n", encoding="utf-8")
    return {"world": world, "project": project, "config": world / "config.json",
            "review": str(review), "trace": str(world / "trace-project"),
            "doc": str(world / "trace-docs" / "Dog routines protocol.md")}


def app_env(base: dict, w: dict, **more) -> dict:
    """The window's environment for a check: the check's port, never quitting by itself, the world as
    its root and settings, and Claude Desktop's settings file a scratch one."""
    env = dict(base, IDIOGRAPH_PORT=str(PORT), IDIOGRAPH_STAY_OPEN="1",
               IDIOGRAPH_ARGS=f"--root {w['project']} --config {w['config']}",
               IDIOGRAPH_CLAUDE_DESKTOP_CONFIG=str(w["world"] / "claude_desktop_config.json"))
    env.update({k: str(v) for k, v in more.items()})
    return env


# ── the stub on this machine ────────────────────────────────────────────────────────────────────

class Stub:
    """What the window says to this machine on STUB: a report a page posts, an order a page asks for
    (drive_mac.py), and a visit to /outside, which a link opened in the default browser makes."""

    def __init__(self, port: int = STUB):
        self.reports: list = []
        self.orders: dict = {}
        self.visits: list = []
        # one the stub's handler takes again inside it, for `done`
        self.lock = threading.RLock()
        stub = self

        class Handler(BaseHTTPRequestHandler):
            def log_message(self, *a):
                pass

            def _head(self, code=200, kind="text/plain"):
                self.send_response(code)
                self.send_header("Access-Control-Allow-Origin", "*")
                self.send_header("Content-Type", kind)
                self.end_headers()

            def do_POST(self):
                n = int(self.headers.get("Content-Length") or 0)
                raw = self.rfile.read(n) or b"{}"
                try:
                    said = dict(json.loads(raw), at=time.time())
                except ValueError:
                    said = {"raw": raw[:500].decode("utf-8", "replace"), "at": time.time()}
                with stub.lock:
                    stub.reports.append(said)
                    # a step answered is handed no more (see `order`)
                    if said.get("event") == "done":
                        stub.done(str(said.get("label") or ""), str(said.get("id") or ""))
                self._head(204)

            def do_GET(self):
                url = urllib.parse.urlsplit(self.path)
                if url.path == "/order":
                    label = urllib.parse.parse_qs(url.query).get("label", [""])[0]
                    with stub.lock:
                        queue = stub.orders.get(label) or []
                        js = queue[0] if queue else ""
                    self._head(200)
                    self.wfile.write(js.encode("utf-8"))
                    return
                with stub.lock:
                    stub.visits.append({"path": self.path, "agent": self.headers.get("User-Agent", "")[:120], "at": time.time()})
                self._head(200, "text/html")
                self.wfile.write(b"<!doctype html><title>Outside</title><p>A page outside Idiograph, on this machine.</p>")

        self.server = _NoLookupServer(("127.0.0.1", port), Handler)
        threading.Thread(target=self.server.serve_forever, daemon=True).start()

    def order(self, label: str, js: str) -> None:
        """A step for the window `label`, `<id>` then a newline then its body, handed to each ask of the
        page's until its answer comes (`done`), so a step whose hand-over or answer the web view lost is
        handed again, and the page answers it again without running it twice (drivefix, 3 November)."""
        with self.lock:
            self.orders.setdefault(label, []).append(js)

    def done(self, label: str, key: str) -> None:
        """The step `key` taken off `label`'s list, answered or given up."""
        with self.lock:
            queue = self.orders.get(label) or []
            queue[:] = [js for js in queue if js.split("\n", 1)[0] != key]

    def find(self, pred, after: float = 0.0):
        with self.lock:
            return [r for r in self.reports if r.get("at", 0) >= after and pred(r)]

    def wait(self, pred, seconds: float, after: float = 0.0):
        t0 = time.time()
        while time.time() - t0 < seconds:
            hit = self.find(pred, after)
            if hit:
                return hit[-1]
            time.sleep(0.2)
        return None

    def close(self) -> None:
        self.server.shutdown()
        self.server.server_close()


# ── the steps the page is taken through, each an async function's body that returns its answer ──

HEAD = """var wait = function (ms) { return new Promise(function (r) { setTimeout(r, ms); }); };
var row = function (name) { return Array.prototype.slice.call(document.querySelectorAll('li.pcard')).find(function (li) { return li.offsetParent && li.textContent.indexOf(name) >= 0; }); };
var size = function () { return [innerWidth, innerHeight]; };
"""


def setup_js(w: dict) -> str:
    world = json.dumps({"review": w["review"], "trace": w["trace"], "doc": w["doc"]})
    return HEAD + f"var w = {world};" + """
function post(path, body) { return fetch(path, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body) }).then(function (r) { return r.json(); }); }
var sift = await post('/api/sift-review', { op: 'open', folder: w.review, name: 'Dog routines' });
var made = await post('/api/trace-project', { op: 'new', folder: w.trace, name: 'Dog routines protocol' });
if (!made.project) made = await post('/api/trace-project', { op: 'open', folder: w.trace });
var folder = made.project && made.project.folder;
var added = await post('/api/trace', { op: 'add', folder: folder, path: w.doc });
return { sift: !!sift.review, trace: folder, added: added.error || 'ok' };"""


def world_js(w: dict) -> str:
    """The world's folders as the page's steps find them, set in each window before its steps."""
    return "window.__driveWorld = " + json.dumps({"review": w["review"], "trace": w["trace"]}) + "; return true;"


PAGE_WAIT = HEAD + """var t0 = Date.now();
while (Date.now() - t0 < 40000) {
  if (document.readyState === 'complete' && document.querySelector('li.pcard')) return { ok: true, href: location.href, size: size(), dpr: devicePixelRatio, shim: !!window.__idiographWindow };
  await wait(200);
}
return { ok: false, href: location.href };"""

THEME = "theme(%s); await new Promise(function (r) { setTimeout(r, 800); }); return document.documentElement.dataset.theme;"

STEPS = {
    "home": "hide('settings'); await loadLibrary(); await wait(1500); return size();",
    "statements": "hide('settings'); await loadLibrary(); await wait(1000); row('Rowan').querySelector('[data-act=\"statements\"]').click(); await wait(3500); return size();",
    "pets": "hide('settings'); await loadLibrary(); await wait(1000); row('Rowan').querySelector('[data-act=\"pets\"]').click(); await wait(4500); return size();",
    "gets": "hide('settings'); await loadLibrary(); await wait(1000); row('Rowan').querySelector('[data-act=\"pets\"]').click(); await wait(4500); document.getElementById('th-step-gets').click(); await wait(4500); return size();",
    "settings": "await loadLibrary(); await wait(800); openSettings(); await wait(1500); return size();",
}
# Idiograph's own screens: Sift and Trace have been apps of their own since 20 October, with windows of
# their own, so Idiograph's page has neither siftOpen nor trOpen (drivefix, 3 November)
SCREENS = ("statements", "pets", "gets", "settings")


def step_js(name: str) -> str:
    return HEAD + STEPS[name]


# the print views, each opened in a window of its own from the screen it belongs to
PRINT_VIEWS = {
    "pets_print": STEPS["pets"].replace("return size();", "await thPrint(); await wait(2500); return true;"),
    "gets_print": STEPS["gets"].replace("return size();", "gtPrintOpen('table'); await gtPrintGo(); await wait(2500); return true;"),
    "canvas_print": STEPS["pets"].replace("return size();", "await thCanvasPrint({ notes: false }); await wait(2500); return true;"),
}

PRINT = "setTimeout(function () { window.print(); }, 300); return { shim: !!window.__idiographWindow, title: document.title };"

# every print view a Mac's window prints to PDF (drive_mac.py --pdfs, 28 October): the table of PETs, the
# GET table, the audit trail, the full set and the PETs canvas
PDF_VIEWS = {
    "pets_table": STEPS["pets"].replace("return size();", "await thPrint(); await wait(2500); return true;"),
    "gets_table": STEPS["gets"].replace("return size();", "gtPrintOpen('table'); await gtPrintGo(); await wait(2500); return true;"),
    "gets_trail": STEPS["gets"].replace("return size();", "gtPrintOpen('trail'); await gtPrintGo(); await wait(2500); return true;"),
    "gets_full": STEPS["gets"].replace("return size();", "gtPrintOpen('all'); await gtPrintGo(); await wait(2500); return true;"),
    "pets_canvas": STEPS["pets"].replace("return size();", "await thCanvasPrint({ notes: false }); await wait(2500); return true;"),
}

# a print asked of the window as Tauri's own print asked it before 28 October, the page's paper left out
PRINT_PLAIN = ("await window.__TAURI_INTERNALS__.invoke('print', { href: location.href, title: document.title }); "
               "return true;")

# a save in Idiograph's own window: Share a copy of the project, the whole of it, its card opened as Home's
# project menu opens it, Share… pressed, the save panel asked for with the file's name (idiographSavePath),
# and the server writing the file where the panel answers. The press is not awaited, since the panel waits
# for its answer
SHARE = HEAD + """hide('settings'); await loadLibrary(); await wait(1000);
var listed = (await api('/api/projects', { op: 'read' })).projects || [];
var p = listed.find(function (one) { return one && one.id && !one.demo; });
if (!p) return { error: 'no project of its own', projects: listed.length };
await sendProject(p.id, p.name); await wait(800);
var card = document.getElementById('share-card');
document.getElementById('sc-go').click();
return { card: !card.hidden, name: sentName(p.name) };"""

# what the card says after Share…, and whether it is still open, then it shut
SHARE_SAID = """var card = document.getElementById('share-card'), said = document.getElementById('sc-said');
return { open: !card.hidden, said: said.hidden ? '' : said.textContent };"""
SHARE_CLOSE = "if (!document.getElementById('share-card').hidden) scShut(); return true;"

OUTSIDE = """var a = document.createElement('a');
a.href = 'http://127.0.0.1:%d/outside'; a.target = '_blank'; a.textContent = 'outside';
document.body.appendChild(a); a.click(); a.remove();
var b = document.createElement('a');
b.href = 'http://127.0.0.1:%d/outside-in-place'; b.textContent = 'outside in place';
document.body.appendChild(b); b.click(); b.remove();
return location.href;""" % (STUB, STUB)

CASE = HEAD + """hide('settings'); await loadLibrary(); await wait(1000);
row(%s).querySelector('[data-act="statements"]').click(); await wait(3500);
return { case: (typeof S !== 'undefined' && S.data && S.data.name) || '', size: size() };"""

RESTART = "serverOp('restart'); return true;"
QUIT = "serverOp('quit'); return true;"
STARTED = "var r = await fetch('/api/server'); var j = await r.json(); return j.started;"
