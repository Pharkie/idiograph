#!/usr/bin/env python3
"""The window checked on a Mac (17 October 2026), on a build made with the `drive` feature, which no
shipped build has. The standard library only.

    python3 packaging/tauri/drive_mac.py --app <Idiograph.app> --stage <build/stage> --out <folder>

The app is the test app, uk.co.adamknowles.idiograph.test, and starts as `open -g -n -W` starts it, so
it never comes to the front, and its windows never take the keyboard (17 October). The Mac's web view
takes no driver, so the build runs a script of this file's in every window once its page has loaded,
which asks the stub here for its next step and says what came of it, says each window's and each
sheet's number for `screencapture`, and ends a sheet by itself four seconds after it opens. Every run
has HOME at `<out>/home`, so the logs and Downloads are the run's own. The results go in
`<out>/results.json` and the screenshots in `<out>/shots`.
"""
from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import threading
import time
import uuid
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import drive_common as dc  # noqa: E402  beside this file

DRIVE_JS = r"""(function () {
  var label = window.__driveLabel, stub = 'http://127.0.0.1:%d';
  // every ask of the stub given up after a few seconds: the Mac's web view now and then leaves one unanswered for
  // good, and the poll waiting on it stopped the page's steps for the rest of the run (drivefix, 3 November)
  function within(ms) { var c = new AbortController(); setTimeout(function () { c.abort(); }, ms); return c.signal; }
  function report(o) { return fetch(stub + '/report', { method: 'POST', signal: within(5000), body: JSON.stringify(Object.assign({ label: label, href: location.href }, o)) }).catch(function () {}); }
  report({ event: 'loaded', title: document.title, size: [innerWidth, innerHeight], shim: !!window.__idiographWindow });
  if (window.__drivePolling) return;
  window.__drivePolling = true;
  // the steps run, by their id, with their answers: the stub hands a step again until its answer reaches it,
  // and a step handed again is answered again, never run twice
  var ran = {};
  (async function poll() {
    for (;;) {
      try {
        var r = await fetch(stub + '/order?label=' + encodeURIComponent(label), { signal: within(5000) });
        var js = await r.text();
        if (js) {
          var id = js.split('\n', 1)[0], out;
          if (!ran[id]) {
            try { out = await (new Function('return (async function () {' + js.slice(id.length + 1) + '\n})();'))(); }
            // the error's own words first, which the Mac's web view leaves out of its stack
            catch (e) { out = { error: String(e) + (e && e.stack ? '\n' + e.stack : '') }; }
            ran[id] = { event: 'done', id: id, out: out === undefined ? null : out };
          }
          await report(ran[id]);
        }
      } catch (e) { }
      await new Promise(function (res) { setTimeout(res, 250); });
    }
  })();
})();""" % dc.STUB

# what the page says from Quit on, kept for a Quit that never ends the server
QUIT_HEARD = """window.__quitSaid = [];
var was = say;
say = function (line) { window.__quitSaid.push(String(line)); return was.apply(this, arguments); };
"""
QUIT_SAID = "return { said: window.__quitSaid || null, busy: !!(SERVER && SERVER.busy) };"

RESULTS: dict = {}
SAVED: list = []


def note(key: str, value) -> None:
    RESULTS[key] = value
    print(f"{key}: {json.dumps(value)[:600]}", flush=True)
    if SAVED:
        SAVED[0].write_text(json.dumps(RESULTS, indent=2), encoding="utf-8")


def processes() -> dict:
    """Every process on the machine, its pid to its parent's pid and its command line."""
    done = subprocess.run(["ps", "-axo", "pid=,ppid=,command="], capture_output=True, text=True, encoding="utf-8")
    found = {}
    for line in done.stdout.splitlines():
        parts = line.split(None, 2)
        if len(parts) == 3 and parts[0].isdigit() and parts[1].isdigit():
            found[int(parts[0])] = (int(parts[1]), parts[2])
    return found


# Every window a drive started, and the processes each is known to have caused, so a drive stops them
# however it ends: at its end, on an error, on a SIGTERM, a SIGHUP or a Ctrl+C (27 October, the loose
# end where the window's server outlived a drive on 8795). `open` starts the window under launchd,
# never as this process's child, and the window starts its server, so neither ends with the drive.
STARTED: list = []
_kept = threading.Lock()


def _stop_all() -> None:
    for app in list(STARTED):
        app.stop()


def _ended(sig, _frame) -> None:
    sys.exit(128 + sig)


def _guard() -> None:
    """The drive's own end stops its windows and their servers, once, on its first window."""
    if getattr(_guard, "done", False):
        return
    _guard.done = True
    import atexit
    import signal
    atexit.register(_stop_all)
    if threading.current_thread() is threading.main_thread():
        for sig in (signal.SIGTERM, signal.SIGHUP, signal.SIGINT):
            if signal.getsignal(sig) in (signal.SIG_DFL, signal.default_int_handler):
                signal.signal(sig, _ended)


class App:
    """One run of the window, started as `open -g -n -W` starts it, so it never comes to the front or
    takes the keyboard from whoever is at the machine (17 October), its standard error read from the
    file `open` writes it to, for the drive's words. The window's process is the one of its bundle's
    executable that came after it started and no other run has, and everything started under it, its
    server among them, is noted as it comes, so `stop` ends them all."""

    def __init__(self, bundle: Path, env: dict, log: Path):
        self.lines: list = []
        self.lock = threading.Lock()
        self.err = log.with_suffix(".err")
        self.err.write_text("", encoding="utf-8")
        self.started = time.time()
        self.exe = str(Path(bundle).resolve() / "Contents" / "MacOS") + "/"
        self.before = {pid for pid, (_, cmd) in processes().items() if cmd.startswith(self.exe)}
        self.mine: dict = {}
        self.stopped = False
        _guard()
        with _kept:
            STARTED.append(self)
        given = [f"{k}={v}" for k, v in env.items() if k in WINDOW_ENV or k.startswith("IDIOGRAPH_")]
        args = ["open", "-g", "-n", "-W", "--stdout", str(log), "--stderr", str(self.err)]
        for pair in given:
            args += ["--env", pair]
        self.proc = subprocess.Popen(args + [str(bundle)])
        threading.Thread(target=self._read, daemon=True).start()
        threading.Thread(target=self._watch, daemon=True).start()

    def note_processes(self) -> dict:
        """The window's processes and everything under them, noted with their command lines."""
        now = processes()
        with _kept:
            taken = set().union(*(other.mine for other in STARTED if other is not self))
            for pid, (_, cmd) in now.items():
                # a window that came since is the newest run's, so a second start's is never the first's
                if (cmd.startswith(self.exe) and STARTED[-1] is self and pid not in self.before
                        and pid not in taken and pid not in self.mine):
                    self.mine[pid] = cmd
            grew = True
            while grew:
                grew = False
                for pid, (parent, cmd) in now.items():
                    if parent in self.mine and pid not in self.mine:
                        self.mine[pid] = cmd
                        grew = True
        return now

    def _watch(self):
        while not self.stopped and self.proc.poll() is None:
            self.note_processes()
            time.sleep(0.5)
        self.note_processes()

    def stop(self, seconds: float = 20) -> list:
        """Every process this run caused that still runs, ended: the window by a SIGTERM, which ends it
        as Quit does, its server first, then whatever is left, its server among them, by a SIGTERM and
        after a few seconds a SIGKILL. A process is ended only while its command line is the one noted,
        so a pid taken again since is left alone. The command lines of those it had to end."""
        import signal
        if self.stopped:
            return []
        now = self.note_processes()
        self.stopped = True

        def alive() -> dict:
            here = processes()
            return {pid: cmd for pid, cmd in self.mine.items() if pid in here and here[pid][1] == cmd}

        left = alive()
        ended = sorted(set(left.values()))
        for pid, cmd in left.items():
            if cmd.startswith(self.exe) and now.get(pid, (0, ""))[0] not in self.mine:
                try:
                    os.kill(pid, signal.SIGTERM)
                except OSError:
                    pass
        # the wait lasts while a window still runs, as one stops its server before it goes, and two seconds
        # more for that server to finish, never the whole of it once no window is left to stop one (testspeed,
        # 2 November 2026: a window already killed held each stop its full 20 seconds)
        t0 = time.time()
        settle = None
        while time.time() - t0 < seconds:
            now = alive()
            if not now:
                break
            if not any(cmd.startswith(self.exe) for cmd in now.values()):
                settle = settle or time.time()
                if time.time() - settle >= 2:
                    break
            time.sleep(0.2)
        for sig in (signal.SIGTERM, signal.SIGKILL):
            for pid in alive():
                try:
                    os.kill(pid, sig)
                except OSError:
                    pass
            t1 = time.time()
            while alive() and time.time() - t1 < 5:
                time.sleep(0.2)
        if self.proc.poll() is None:
            self.proc.kill()
        return ended

    def _read(self):
        at = 0
        while True:
            try:
                text = self.err.read_text(encoding="utf-8", errors="replace")
            except OSError:
                text = ""
            if len(text) > at:
                fresh, at = text[at:], len(text)
                with self.lock:
                    self.lines += [(time.time(), line) for line in fresh.splitlines()]
            if self.proc.poll() is not None and len(text) == at:
                time.sleep(0.5)
                if len(self.err.read_text(encoding="utf-8", errors="replace")) == at:
                    return
            time.sleep(0.1)

    def said(self, start: str, after: float = 0.0) -> list:
        with self.lock:
            return [line for at, line in self.lines if at >= after and line.startswith(start)]

    def wait_said(self, start: str, seconds: float, after: float = 0.0):
        t0 = time.time()
        while time.time() - t0 < seconds:
            hit = self.said(start, after)
            if hit:
                return hit[-1]
            time.sleep(0.1)
        return None

    def number(self, label: str):
        hit = self.said(f"drive: window {label} ")
        return int(hit[-1].split()[-1]) if hit else None

    def end(self, seconds: float = 40) -> dict:
        """The run's end, waited for, and then whatever it left running stopped and named under `left`,
        a server that outlived its window among them."""
        try:
            code = self.proc.wait(timeout=seconds)
        except subprocess.TimeoutExpired:
            code = "killed"
        left = self.stop()
        return dict({"exit": code}, **({"left": left} if left else {}))


# what `open` hands the window besides every IDIOGRAPH_ variable: the run's own home folder
WINDOW_ENV = ("HOME",)


def shot(number, path: Path) -> str:
    if number is None:
        return "no window number"
    done = subprocess.run(["screencapture", "-o", f"-l{number}", str(path)], capture_output=True, text=True, encoding="utf-8")
    return "saved" if done.returncode == 0 and path.exists() else (done.stderr.strip() or f"exit {done.returncode}")


def run(stub: dc.Stub, label: str, body: str, timeout: float = 60):
    """One step in the window `label`: its answer, or an error when none came in time."""
    key = uuid.uuid4().hex[:12]
    t0 = time.time()
    stub.order(label, f"{key}\n{body}")
    got = stub.wait(lambda r: r.get("event") == "done" and r.get("id") == key, timeout, t0)
    # a step given up is handed no more, so a page opened later never runs it
    stub.done(label, key)
    return got.get("out") if got else {"error": f"no answer in {timeout} s"}


def loaded(stub: dc.Stub, after: float, seconds: float = 40, label: str | None = None, not_label: str | None = None):
    return stub.wait(lambda r: r.get("event") == "loaded" and (label is None or r.get("label") == label)
                     and (not_label is None or r.get("label") != not_label), seconds, after)


def sheet_shot(app: App, label: str, path: Path, after: float, seconds: float = 20) -> dict:
    """The sheet that opens on `label`'s window, its picture taken while it is open, and its answer."""
    line = app.wait_said(f"drive: sheet {label} ", seconds, after)
    if not line:
        return {"sheet": None}
    _, _, _, number, kind = line.split(" ", 4)
    time.sleep(1.2)
    said = {"sheet": kind, "shot": shot(int(number), path), "window_shot": shot(app.number(label), path.with_name(path.stem + "-window.png"))}
    said["answered"] = app.wait_said(f"drive: answered {label} {number}", 10, after)
    return said


def pdf_pages(path: Path) -> dict:
    """A PDF's page count and its pages' sizes in points, read from its own page objects, as the Mac's
    print writes them (uncompressed page dictionaries)."""
    data = path.read_bytes()
    import re
    boxes = re.findall(rb"/MediaBox\s*\[\s*([-\d.]+)\s+([-\d.]+)\s+([-\d.]+)\s+([-\d.]+)\s*\]", data)
    pages = len(re.findall(rb"/Type\s*/Page(?![s\w])", data))
    sizes = sorted({(round(float(x1) - float(x0)), round(float(y1) - float(y0))) for x0, y0, x1, y1 in boxes})
    return {"pages": pages, "sizes": sizes,
            "landscape": bool(sizes) and all(w > h for w, h in sizes),
            "a4": bool(sizes) and all(sorted((w, h)) == [595, 842] for w, h in sizes)}


def pdfs(app: "App", stub: dc.Stub, out: Path, close, logs: Path) -> int:
    """Each print view opened in its window and printed to PDF with no panel (IDIOGRAPH_WINDOW_PRINT_TO):
    first as the page's own Print asks, its @page size with it, then as Tauri's own print asked before 28
    October, the page's paper left out. Each PDF's orientation, paper and page count noted, then the run
    ends and leaves nothing running."""

    def printed(after: float, seconds: float = 40) -> dict:
        line = app.wait_said("drive: print to ", seconds, after)
        if not line:
            return {"pdf": None}
        path = Path(line.split("drive: print to ", 1)[1].strip())
        t0, last = time.time(), -1
        while time.time() - t0 < seconds:
            size = path.stat().st_size if path.exists() else -1
            if size > 0 and size == last:
                break
            last = size
            time.sleep(1.0)
        said = {"pdf": path.name, "info": app.said("drive: print info", after)[:1], "asked": [x for x in app.said("drive: print ", after) if " asked through " in x][:1]}
        if path.exists():
            said.update(pdf_pages(path))
        return said

    for view, body in dc.PDF_VIEWS.items():
        def one(view=view, body=body):
            t = time.time()
            said = {"step": run(stub, "main", dc.HEAD + body, timeout=90)}
            page = loaded(stub, t, 30, not_label="main")
            if not page:
                return dict(said, opened=False)
            label = page["label"]
            time.sleep(3)
            said.update(label=label, href=page.get("href", "").split("?")[0], title=page.get("title"))
            # a view that prints itself as it opens (the table of PETs) has printed once already
            said["on_open"] = [line for line in app.said("drive: print to ", t)]
            t = time.time()
            run(stub, label, dc.PRINT)
            said["page_print"] = printed(t)
            time.sleep(2)
            t = time.time()
            run(stub, label, dc.PRINT_PLAIN)
            said["plain_print"] = printed(t)
            close(label)
            time.sleep(1.5)
            return said
        attempt(view, one)
    attempt("main_print", lambda: (lambda t: (run(stub, "main", dc.PRINT), printed(t))[1])(time.time()))
    attempt("log", lambda: [line for line in logs.read_text(encoding="utf-8").splitlines() if line.startswith("===")][-4:])
    stub.close()
    note("left_at_end", [cmd for one in list(STARTED) for cmd in one.stop()])
    note("port_closed_at_end", not dc.listening(dc.PORT))
    return 0


def export(app: "App", stub: dc.Stub, out: Path, close, world: Path, case: str = "Rowan") -> int:
    """Export as PDF beside Print (31 October 2026, pdfexport): at the app's text size of 100% and of 125%, the
    table of PETs printed as its print view's own Print prints it, with no panel (IDIOGRAPH_WINDOW_PRINT_TO),
    and saved by the page's own Export as PDF, `thPdf`, beside the workbook. Each PDF's pages, paper and the
    width of its page noted, so Print's and Export's pages can be compared, and each zoom's, then the run ends
    and leaves nothing running."""
    made: dict = {}
    for zoom in (1.0, 1.25):
        def one(zoom=zoom):
            said = {"zoom": run(stub, "main", f"return await window.idiographTextSize({zoom});")}
            t = time.time()
            # the print view opens on its own Print, which prints it once to the folder
            run(stub, "main", dc.HEAD + dc.PDF_VIEWS["pets_table"].replace("row('Rowan')", f"row({json.dumps(case)})"), timeout=90)
            page = loaded(stub, t, 30, not_label="main")
            line = app.wait_said("drive: print to ", 40, t)
            if line:
                path = Path(line.split("drive: print to ", 1)[1].strip())
                for _ in range(40):
                    if path.exists() and path.stat().st_size > 0:
                        break
                    time.sleep(0.5)
                time.sleep(1.5)
                said["print"] = dict(pdf_pages(path), pdf=str(path)) if path.exists() else {"pdf": None}
            if page:
                close(page["label"])
                time.sleep(1.5)
            before = set(world.rglob("*.pdf"))
            said["export"] = run(stub, "main", dc.HEAD + "await thPdf(); await wait(4000); "
                                 "return TH.exported ? TH.exported.shown : null;", timeout=90)
            new = sorted(set(world.rglob("*.pdf")) - before)
            if new:
                kept = out / f"export-{zoom}.pdf"
                shutil.copyfile(new[0], kept)
                said["export_pdf"] = dict(pdf_pages(kept), pdf=str(kept), beside=new[0].parent.name)
            return said
        made[zoom] = one()
        note(f"export_{zoom}", made[zoom])
    attempt("export_zoom_back", lambda: run(stub, "main", "return await window.idiographTextSize(1);"))
    attempt("canvas", lambda: canvas_outputs(stub, out, world))
    stub.close()
    note("left_at_end", [cmd for one in list(STARTED) for cmd in one.stop()])
    note("port_closed_at_end", not dc.listening(dc.PORT))
    return 0


def canvas_outputs(stub: dc.Stub, out: Path, world: Path) -> dict:
    """The canvas's Save as PDF and Save as an image (1 November 2026, exportA): the board put on the canvas, then
    each made by the page's own `thCanvasOut`, which the server makes with Typst (typst5), beside the workbook.
    Each file's size noted, the PDF's pages and paper, and the PNG's pixels against the canvas page's own size."""
    said: dict = {"face": run(stub, "main", dc.HEAD + "thFace('canvas'); await wait(800); return TH.face;")}
    for kind, ending in (("pdf", ".pdf"), ("png", ".png")):
        before = set(world.rglob(f"*{ending}"))
        said[kind] = run(stub, "main", dc.HEAD + f"await thCanvasOut('{kind}'); await wait(3000); "
                         "return TH.exported ? TH.exported.shown : null;", timeout=120)
        new = sorted(set(world.rglob(f"*{ending}")) - before)
        if not new:
            said[f"{kind}_file"] = None
            continue
        kept = out / f"canvas{ending}"
        shutil.copyfile(new[0], kept)
        one = {"file": new[0].name, "bytes": kept.stat().st_size, "beside": new[0].parent.name, "kept": str(kept)}
        if kind == "pdf":
            one.update(pdf_pages(kept))
        else:
            head = kept.read_bytes()[:24]
            one["pixels"] = [int.from_bytes(head[16:20], "big"), int.from_bytes(head[20:24], "big")]
        said[f"{kind}_file"] = one
    said["page"] = run(stub, "main", dc.HEAD + "const c = thCanvasCopy(true); return c.box;")
    return said


def attempt(name: str, fn) -> None:
    try:
        note(name, fn())
    except Exception as exc:  # noqa: BLE001  one failed step never stops the rest
        note(name, {"error": f"{type(exc).__name__}: {exc}"})


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--app", required=True)
    ap.add_argument("--stage", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--pdfs", action="store_true", help="each print view printed to PDF from its window, then the run ends")
    ap.add_argument("--export", action="store_true", help="the table of PETs printed and saved by Export as PDF at 100%% and 125%%, then the run ends")
    ap.add_argument("--case", default="Rowan", help="the participant --export prints, Rowan by default")
    a = ap.parse_args()
    out = Path(a.out).resolve()
    shots = out / "shots"
    shots.mkdir(parents=True, exist_ok=True)
    SAVED.append(out / "results.json")
    bundle = Path(a.app).resolve()
    exe = bundle / "Contents" / "MacOS" / bundle.stem
    stage = Path(a.stage).resolve()
    w = dc.make_world(out, stage / "demo", stage / "config.json")
    home = out / "home"
    downloads = home / "Downloads"
    downloads.mkdir(parents=True, exist_ok=True)
    (out / "drive.js").write_text(DRIVE_JS, encoding="utf-8")
    closer = out / "close-these"
    base = dict(os.environ, HOME=str(home), IDIOGRAPH_WINDOW_DRIVE=str(out / "drive.js"), IDIOGRAPH_WINDOW_SAVE_TO=str(downloads),
                IDIOGRAPH_WINDOW_CLOSE=str(closer), IDIOGRAPH_WINDOW_NO_OPEN="1")
    if a.pdfs or a.export:
        (out / "pdfs").mkdir(exist_ok=True)
        base["IDIOGRAPH_WINDOW_PRINT_TO"] = str(out / "pdfs")
    env = dc.app_env(base, w)
    stub = dc.Stub()
    logs = home / "Library" / "Logs" / "Idiograph" / "idiograph.log"

    def close(*labels: str) -> None:
        closer.write_text("\n".join(labels) + "\n", encoding="utf-8")

    # ── the first run: every screen, print, the print views, downloads, two windows, a second start,
    # Restart, and the app ending with its last window
    t0 = time.time()
    app = App(bundle, env, out / "app-1.log")
    first = loaded(stub, t0, 60, label="main")
    note("page_loaded_s", round(first["at"] - t0, 2) if first else None)
    note("server_answered", app.wait_said("Idiograph: the server answered", 5))
    note("main_window", {"number": app.number("main"), "page": first})
    # the Edit menu's items, keys and actions, Cmd+C, Cmd+V, Cmd+X, Cmd+A, Cmd+Z and Cmd+Shift+Z among them
    note("edit_menu", app.said("drive: edit item"))
    attempt("world", lambda: run(stub, "main", dc.world_js(w)))
    if a.pdfs:
        return pdfs(app, stub, out, close, logs)
    if a.export:
        return export(app, stub, out, close, w["world"], a.case)
    for look in ("light", "dark"):
        attempt(f"theme_{look}", lambda look=look: run(stub, "main", dc.THEME % json.dumps(look)))
        for step in dc.SCREENS:
            attempt(f"{step}_{look}", lambda step=step: run(stub, "main", dc.step_js(step)))
            attempt(f"shot_{step}_{look}", lambda step=step, look=look: shot(app.number("main"), shots / f"mac-{step}-{look}.png"))
    attempt("theme_back", lambda: run(stub, "main", dc.THEME % json.dumps("light")))
    attempt("home", lambda: run(stub, "main", dc.step_js("home")))

    # print, from the page, as its own Print asks
    t1 = time.time()
    attempt("print", lambda: run(stub, "main", dc.PRINT))
    attempt("print_panel", lambda: sheet_shot(app, "main", shots / "mac-print-panel.png", t1))

    # each print view in a window of its own, which prints the same way, then closed
    for view, body in dc.PRINT_VIEWS.items():
        def one(view=view, body=body):
            t = time.time()
            said = {"step": run(stub, "main", dc.HEAD + body, timeout=90)}
            page = loaded(stub, t, 30, not_label="main")
            if not page:
                return dict(said, opened=False)
            label = page["label"]
            time.sleep(2)
            said.update(opened=True, label=label, href=page.get("href", "").split("?")[0], title=page.get("title"),
                        shim=page.get("shim"), shot=shot(app.number(label), shots / f"mac-{view}.png"))
            t = time.time()
            said["print"] = run(stub, label, dc.PRINT)
            said["panel"] = sheet_shot(app, label, shots / f"mac-{view}-panel.png", t)
            said["asked"] = app.said("drive: print", t)
            close(label)
            time.sleep(1.5)
            return said
        attempt(view, one)

    # a save: Share a copy of the whole project, the save panel with the file's name, answered, and the
    # file the server writes where it was put (the PRISMA map's downloads were Sift's, an app of its own
    # since 20 October)
    def download():
        before = set(p.name for p in downloads.iterdir())
        t = time.time()
        said = {"step": run(stub, "main", dc.SHARE)}
        said["panel"] = sheet_shot(app, "main", shots / "mac-save-panel.png", t)
        new = []
        for _ in range(60):
            new = sorted(n for n in set(p.name for p in downloads.iterdir()) - before if not n.startswith("."))
            if new and (downloads / new[0]).stat().st_size:
                break
            time.sleep(0.5)
        said["saved"] = new
        if new:
            said["head"] = (downloads / new[0]).read_bytes()[:2].decode("latin-1")
        said["card"] = run(stub, "main", dc.SHARE_SAID)
        run(stub, "main", dc.SHARE_CLOSE)
        return said
    attempt("download", download)

    # a link to another site: said, and with IDIOGRAPH_WINDOW_NO_OPEN never opened here
    t2 = time.time()
    def outside():
        said = {"page_still": run(stub, "main", dc.OUTSIDE)}
        # both links' lines, which the window's log can bring a moment after the page has answered
        for _ in range(50):
            if len(app.said("Idiograph: outside link", t2)) >= 2:
                break
            time.sleep(0.1)
        return dict(said, said=app.said("Idiograph: outside link", t2))
    attempt("outside", outside)

    # two windows, a case in each
    def two():
        t = time.time()
        said = {"new": run(stub, "main", "await window.__TAURI_INTERNALS__.invoke('new_window'); return true;")}
        page = loaded(stub, t, 30, not_label="main")
        if not page:
            return dict(said, opened=False)
        label = page["label"]
        run(stub, label, dc.world_js(w))
        said["main"] = run(stub, "main", dc.CASE % json.dumps("Rowan"))
        said["second"] = run(stub, label, dc.CASE % json.dumps("Mabel"))
        said["shots"] = [shot(app.number("main"), shots / "mac-two-windows-main.png"),
                         shot(app.number(label), shots / "mac-two-windows-second.png")]
        said["label"] = label
        return said
    attempt("two_windows", two)

    # a second start: it ends at once, starts no server, and the open window comes forward
    def second():
        t = time.time()
        other = App(bundle, env, out / "app-second.log")
        ended = other.end(30)
        time.sleep(1)
        return dict(ended, seconds=round(time.time() - t, 2), next_port_listening=dc.listening(dc.PORT + 1),
                    first_still_running=app.proc.poll() is None, brought=app.said("drive: brought forward", t))
    attempt("second_start", second)

    # Restart in Settings: the window stays and its page comes back on the server started again
    def restart():
        before = run(stub, "main", dc.STARTED)
        t = time.time()
        run(stub, "main", dc.RESTART)
        back = loaded(stub, t, 40, label="main")
        time.sleep(2)
        after = run(stub, "main", dc.STARTED)
        return {"before": before, "after": after, "reloaded": bool(back), "app_running": app.proc.poll() is None,
                "listening": dc.listening(dc.PORT)}
    attempt("restart", restart)

    # the last window closed: the app ends, and the server with it
    def last_window():
        two_label = (RESULTS.get("two_windows") or {}).get("label")
        if two_label:
            close(two_label)
            time.sleep(2)
        t = time.time()
        close("main")
        gone = dc.wait_closed(dc.PORT, 40)
        ended = app.end(40)
        return dict(ended, server_gone_s=gone, seconds=round(time.time() - t, 2),
                    stopped=app.said("Idiograph: the server stopped"))
    attempt("last_window", last_window)

    # ── the second run: a save that fails says so, then Quit in Settings ends the app
    missing = out / "no-such-folder"
    t3 = time.time()
    app2 = App(bundle, dict(env, IDIOGRAPH_WINDOW_SAVE_TO=str(missing)), out / "app-2.log")
    second_page = loaded(stub, t3, 60, label="main")
    note("second_run_loaded", bool(second_page))
    attempt("world_2", lambda: run(stub, "main", dc.world_js(w)))

    def failing():
        t = time.time()
        said = {"step": run(stub, "main", dc.SHARE)}
        said["panel"] = sheet_shot(app2, "main", shots / "mac-save-panel-again.png", t)
        # the card says the file was not sent, and stays open
        for _ in range(20):
            said["card"] = run(stub, "main", dc.SHARE_SAID)
            if (said["card"] or {}).get("said"):
                break
            time.sleep(0.5)
        said["shot"] = shot(app2.number("main"), shots / "mac-save-failed.png")
        said["folder_made"] = missing.exists()
        run(stub, "main", dc.SHARE_CLOSE)
        return said
    attempt("save_fails", failing)

    def quit_():
        t = time.time()
        run(stub, "main", QUIT_HEARD + dc.QUIT, timeout=10)
        gone = dc.wait_closed(dc.PORT, 40)
        # a Quit that never ended the server: what the page said, and whether it is still at it
        page = run(stub, "main", QUIT_SAID, timeout=10) if gone < 0 else None
        ended = app2.end(40)
        return dict(ended, server_gone_s=gone, seconds=round(time.time() - t, 2), **({"page": page} if page else {}))
    attempt("quit", quit_)

    # ── the command line and the MCP server from the bundle, as Claude Desktop runs them
    def mcp():
        msgs = "\n".join(json.dumps(m) for m in (
            {"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {"protocolVersion": "2025-06-18", "capabilities": {}, "clientInfo": {"name": "drive", "version": "0"}}},
            {"jsonrpc": "2.0", "method": "notifications/initialized"},
            {"jsonrpc": "2.0", "id": 2, "method": "tools/list"})) + "\n"
        said = {}
        for name, path in (("window", exe), ("server", bundle / "Contents" / "Resources" / "server" / "Idiograph")):
            done = subprocess.run([str(path), "mcp", "--root", str(w["project"]), "--config", str(w["config"])], input=msgs,
                                  capture_output=True, text=True, encoding="utf-8", timeout=60, env=dict(os.environ, HOME=str(home)))
            lines = [json.loads(x) for x in done.stdout.splitlines() if x.strip().startswith("{")]
            tools = next((len(m["result"].get("tools", [])) for m in lines if m.get("id") == 2 and "result" in m), None)
            said[name] = {"exit": done.returncode, "answers": len(lines), "tools": tools}
        cli = subprocess.run([str(exe), "cli", "cases", "--root", str(w["project"]), "--config", str(w["config"])],
                             capture_output=True, text=True, encoding="utf-8", timeout=60, env=dict(os.environ, HOME=str(home)))
        said["cli_cases"] = {"exit": cli.returncode, "out": cli.stdout.strip().splitlines()[:4], "err": cli.stderr.strip()[-400:]}
        return said
    attempt("mcp_and_cli", mcp)

    attempt("log", lambda: [line for line in logs.read_text(encoding="utf-8").splitlines() if line.startswith("===")][-4:])
    stub.close()
    note("port_closed_at_end", not dc.listening(dc.PORT))
    # whatever a run left running, stopped and named, so the next drive finds its port free
    note("left_at_end", [cmd for one in list(STARTED) for cmd in one.stop()])
    return 0


if __name__ == "__main__":
    sys.exit(main())
