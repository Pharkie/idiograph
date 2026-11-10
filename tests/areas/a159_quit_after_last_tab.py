from __future__ import annotations

import contextlib
import io
import json
import os
import shutil
import sys
from pathlib import Path

from . import support
from .support import check, skip


def test_quit_after_last_tab(scratch):
    print("\n159. Quitting after the last tab, 16 October, Adam's word on a tester who closed the tab and found the app "
          "still running: every page beats, every request counts as use, and with nothing running the server quits by "
          "Quit's own path a few minutes after its last tab closes, a tick at the end of Settings, General, on by "
          "default, and never in the suite's own servers")
    import http.client
    import socket
    import subprocess
    import threading
    import time
    from http.server import ThreadingHTTPServer
    import server as server_mod
    import sift_routes

    read = lambda path: Path(path).read_text(encoding="utf-8")
    page, app, design_page = support.page_text(), support.text("family/static/shell.js", "apps/idiograph/static/distil.js"), support.page_text("family/static/design.html")
    node = shutil.which("node")
    fn = lambda src, name: src.split(f"function {name}(", 1)[1].split("\n}", 1)[0] if f"function {name}(" in src else ""
    stay = server_mod.STAY_OPEN

    @contextlib.contextmanager
    def free_to_quit():
        """The suite's own STAY_OPEN set aside for a check of the watcher itself, and put back after."""
        held = os.environ.pop(stay, None)
        try:
            yield
        finally:
            if held is not None:
                os.environ[stay] = held

    # ── A. the key: on by default and when absent, saved and read back
    check("159: quit_when_closed is on in the server's defaults and the Mac app's shipped settings, a settings file "
          "without it reads on, and one with it off keeps it off",
          server_mod.defaults().get("quit_when_closed") is True and server_mod.shipped_config()["quit_when_closed"] is True
          and server_mod.merge_config({"interviewer": "Wren"})["quit_when_closed"] is True
          and server_mod.merge_config({"quit_when_closed": False})["quit_when_closed"] is False)
    kept_config = server_mod.CONFIG_PATH
    server_mod.CONFIG_PATH = scratch / "quit-159-config.json"
    try:
        server_mod.CONFIG_PATH.write_text(json.dumps({"interviewer": "Wren", "round_minutes": 12}), encoding="utf-8")
        before = server_mod.config()
        off = server_mod.api_settings({"quit_when_closed": False})["config"]
        off_disk = json.loads(server_mod.CONFIG_PATH.read_text(encoding="utf-8"))
        kept = server_mod.api_settings({"interviewer": "Wren", "sound": True})["config"]
        back_off = server_mod.config()
        on = server_mod.api_settings({"quit_when_closed": 1})["config"]
        on_disk = json.loads(server_mod.CONFIG_PATH.read_text(encoding="utf-8"))
        with free_to_quit():
            reads = (server_mod.quit_on({}), server_mod.quit_on({"quit_when_closed": False}), server_mod.quit_on())
        held_open = (server_mod.quit_on({}), server_mod.quit_on())
    finally:
        server_mod.CONFIG_PATH = kept_config
    check("159: Save writes it and keeps every other key, a save without it leaves it as it was, the file reads back the "
          "same, and the watcher reads it from the file, on unless it says false",
          before["quit_when_closed"] is True and off["quit_when_closed"] is False and off_disk["quit_when_closed"] is False
          and off_disk["round_minutes"] == 12 and kept["quit_when_closed"] is False and back_off["quit_when_closed"] is False
          and on["quit_when_closed"] is True and on_disk["quit_when_closed"] is True and on_disk["sound"] is True
          and reads == (True, False, True), f"{off_disk.get('quit_when_closed')} {kept.get('quit_when_closed')} {reads}")
    check("159: the suite runs with STAY_OPEN set, so no server it starts quits by itself, whatever the tick",
          os.environ.get(stay) == "1" and held_open == (False, False) and server_mod.watch_idle(object()) is None)

    # ── B. the beat reaching the server, and every request a sign of use
    httpd = ThreadingHTTPServer(("127.0.0.1", 0), server_mod.Handler)
    port = httpd.server_address[1]
    serving = threading.Thread(target=httpd.serve_forever, kwargs={"poll_interval": 0.05}, daemon=True)
    serving.start()

    def ask(method, path, body=None, origin=None, kind="application/json", at=None):
        conn = http.client.HTTPConnection("127.0.0.1", at or port, timeout=20)
        headers = {"Host": f"127.0.0.1:{at or port}"}
        if body is not None:
            headers["Content-Type"] = kind
        if origin:
            headers["Origin"] = origin
        conn.request(method, path, body if isinstance(body, (str, type(None))) else json.dumps(body), headers)
        res = conn.getresponse()
        raw = res.read()
        conn.close()
        try:
            return res.status, json.loads(raw or b"{}")
        except ValueError:
            return res.status, raw.decode("utf-8", errors="replace")

    def settled(seconds=10):
        """The server's count of requests in hand and its last sign of use, read under its own lock once
        the count is back to none. A request's answer reaches the page before the server's thread lets
        the request go and takes its closing sign of use, so a read straight after the answer could come
        first on a busy machine and find the request still counted, or a stamp about to move (17 October)."""
        until = time.monotonic() + seconds
        while True:
            with server_mod._life:
                held, seen = server_mod.LIFE["requests"], server_mod.LIFE["seen"]
            if not held or time.monotonic() >= until:
                return held, seen
            time.sleep(0.005)

    try:
        own = f"http://127.0.0.1:{port}"
        mark = time.monotonic()
        time.sleep(0.02)
        beat = ask("POST", "/api/beat", {}, origin=own)
        after_beat = settled()[1]
        time.sleep(0.02)
        # the last word as `navigator.sendBeacon` sends it, a text body
        gone = ask("POST", "/api/beat", '{"gone":true}', origin=own, kind="text/plain;charset=UTF-8")
        after_gone = settled()[1]
        time.sleep(0.02)
        other = ask("GET", "/api/server")
        after_other = settled()[1]
        time.sleep(0.02)
        foreign = ask("POST", "/api/beat", {}, origin="https://example.com")
        after_foreign = settled()[1]
        printed = ask("GET", "/themes/print?workbook=nowhere.xlsx")
        in_hand = settled()[0]
        check("159: a page's beat and its last word reach the server, each answered and each a sign of use, and so is any "
              "other request, while one from a page served elsewhere is refused and counts for nothing",
              beat == (200, {"heard": True}) and gone == (200, {"heard": True}) and other[0] == 200
              and mark < after_beat < after_gone < after_other and foreign[0] == 403 and after_foreign == after_other
              and in_hand == 0 and server_mod.ROUTES[server_mod.BEAT_PATH] is server_mod.api_beat
              and server_mod.BEAT_PATH == "/api/beat" and server_mod.BEAT_PATH not in server_mod.POST_ONLY,
              f"{beat} {gone} {foreign[0]}")
        check("159: the print views carry the beat once, as the page and the design page do, so an open print tab keeps "
              "the app open",
              isinstance(printed[1], str) and printed[1].count(server_mod.BEAT_TAG) == 1
              and server_mod.beating(server_mod.beating("<body>x</body>")) == "<body>x" + server_mod.BEAT_TAG + "</body>"
              and page.count(server_mod.BEAT_TAG) == 1 and design_page.count(server_mod.BEAT_TAG) == 1)
    finally:
        httpd.shutdown()
        httpd.server_close()

    # ── C. the watcher on a server of its own: what holds it, then the quit by Quit's path
    # sped up 18 October (testreview3): the wait and each hold shorter, the hold still twice the wait
    wait, hold = 0.3, 0.6
    kept_life = dict(server_mod.LIFE)
    kept_state = dict(server_mod.SERVER_STATE)
    kept_logs = dict(server_mod.PATHS)
    server_mod.CONFIG_PATH = scratch / "quit-159-watch.json"
    server_mod.CONFIG_PATH.write_text(json.dumps({"interviewer": "Wren"}), encoding="utf-8")
    httpd = ThreadingHTTPServer(("127.0.0.1", 0), server_mod.Handler)
    port = httpd.server_address[1]
    serving = threading.Thread(target=httpd.serve_forever, kwargs={"poll_interval": 0.05}, daemon=True)
    stop = threading.Event()
    outcome = {}
    phases = {}
    said = io.StringIO()

    def slow(_body):
        time.sleep(hold)
        return {"slow": True}

    def standing():
        return serving.is_alive() and server_mod.SERVER_STATE["op"] is None and not server_mod.LIFE["closing"]

    try:
        with free_to_quit(), contextlib.redirect_stdout(said):
            serving.start()
            server_mod.used()
            watcher = threading.Thread(target=lambda: outcome.update(quit=server_mod.idle_quit(
                httpd, wait=wait, look=0.05, stop=stop)), daemon=True)
            watcher.start()
            own = f"http://127.0.0.1:{port}"
            until = time.monotonic() + hold * 1.5
            while time.monotonic() < until:
                ask("POST", "/api/beat", {}, origin=own)
                time.sleep(0.1)
            phases["beats"] = standing()
            until = time.monotonic() + hold * 1.5
            while time.monotonic() < until:
                ask("GET", "/api/server")
                time.sleep(0.1)
            phases["requests"] = standing()
            # a request in hand longer than the wait, as an AI request or a save is
            server_mod.ROUTES["/api/slow-159"] = slow
            phases["in hand"] = ask("POST", "/api/slow-159", {}, origin=own) == (200, {"slow": True}) and standing()
            server_mod.ROUTES.pop("/api/slow-159", None)
            # Sift's work holds Sift's server alone, its holds keyed by app (the sixth build, 23 October 2026)
            with support.as_app("sift"):
                sift_routes.SEARCH_RUNS["quit-159"] = {"running": True}
                time.sleep(hold)
                phases["search run"] = standing()
                sift_routes.SEARCH_RUNS["quit-159"]["running"] = False
                sift_routes.ZOTERO_SYNCS["quit-159"] = {"running": True}
                time.sleep(hold)
                phases["Zotero sync"] = standing()
            phases["not Idiograph's"] = server_mod.holding() == ""
            sift_routes.ZOTERO_SYNCS["quit-159"]["running"] = False
            server_mod._lock.acquire()
            try:
                time.sleep(hold)
                phases["write"] = standing()
            finally:
                server_mod._lock.release()
            server_mod.CONFIG_PATH.write_text(json.dumps({"interviewer": "Wren", "quit_when_closed": False}), encoding="utf-8")
            time.sleep(hold * 1.5)
            phases["tick off"] = standing()
            server_mod.CONFIG_PATH.write_text(json.dumps({"interviewer": "Wren", "quit_when_closed": True}), encoding="utf-8")
            freed = time.monotonic()
            serving.join(10)
            watcher.join(5)
            took = time.monotonic() - freed
            quit_state = (dict(server_mod.SERVER_STATE), server_mod.LIFE["closing"], serving.is_alive(), outcome.get("quit"))
            # what `main` does once the serving has stopped, as for Quit
            httpd.socket.close()
            logs = scratch / "quit-159-logs"
            logs.mkdir(exist_ok=True)
            server_mod.PATHS["logs"] = logs
            (logs / f"idiograph-{port}.pid").write_text(f"{os.getpid()}\n", encoding="utf-8")
            server_mod.finish(server_mod.SERVER_STATE["op"], port)
            pid_gone = not (logs / f"idiograph-{port}.pid").exists()
            let_go = server_mod._lock.acquire(timeout=1)
            if let_go:
                server_mod._lock.release()
            # a request that comes once the quit is decided, on a server still listening
            late = ThreadingHTTPServer(("127.0.0.1", 0), server_mod.Handler)
            late_port = late.server_address[1]
            threading.Thread(target=late.serve_forever, kwargs={"poll_interval": 0.05}, daemon=True).start()
            try:
                closing = ask("POST", "/api/beat", {}, origin=f"http://127.0.0.1:{late_port}", at=late_port)
            finally:
                late.shutdown()
                late.server_close()
    finally:
        stop.set()
        server_mod.ROUTES.pop("/api/slow-159", None)
        sift_routes.SEARCH_RUNS.pop("quit-159", None)
        sift_routes.ZOTERO_SYNCS.pop("quit-159", None)
        server_mod.CONFIG_PATH = kept_config
        server_mod.PATHS.clear()
        server_mod.PATHS.update(kept_logs)
        server_mod.SERVER_STATE.clear()
        server_mod.SERVER_STATE.update(kept_state)
        server_mod.LIFE.update(kept_life, requests=0, closing=False)
        if serving.is_alive():
            httpd.shutdown()
        try:
            httpd.server_close()
        except OSError:
            pass
    check("159: beats, other requests, a request in hand, a search run, a Zotero sync, a write and the tick off each hold "
          "it past the wait, and Sift's work holds no other app's server", all(phases.values()) and len(phases) == 8, str(phases))
    check("159: then with no sign and nothing running it quits once the wait has passed again, by Quit's path: the serving "
          "stopped, finish clearing the pid file, the lock let go, and its two lines said",
          quit_state == ({"op": "quit"}, True, False, True) and took >= wait * 0.8 and pid_gone and let_go
          and server_mod.named(server_mod.QUIT_LINE) in said.getvalue() and "Idiograph is closed." in said.getvalue()
          and said.getvalue().index(server_mod.named(server_mod.QUIT_LINE)) < said.getvalue().index("Idiograph is closed."),
          f"{quit_state} {took:.2f}s")
    check("159: a request that comes once the quit is decided is told the app is closed, so no write starts after it",
          closing == (503, {"error": "Idiograph is closed."}) and server_mod.named(server_mod.CLOSED_LINE) == "Idiograph is closed.")

    # ── C2. the window gone without Quit (31 October, quitcrash: 0.9.14 crashed as Adam quit it and its
    # server ran on): a server the window started quits at the watcher's next look once its parent has
    # changed, a write in hand still holding it, and never for its parent unchanged or a run not the window's
    class Stub:
        """What the watcher stops, the serving, counted."""
        def __init__(self):
            self.stopped = 0

        def shutdown(self):
            self.stopped += 1

    def watched(parent: int, window: bool, held: float = 0.0, run_for: float = 0.6) -> tuple[bool, float, int]:
        """The watcher run with a wait of an hour on a stub, its parent noted as `parent`: whether it quit, how
        soon, and how often it stopped the serving, a write held for `held` seconds first."""
        stub, kept_parent, kept_window = Stub(), server_mod.PARENT, os.environ.get(server_mod.WINDOW)
        kept_life_, kept_state_ = dict(server_mod.LIFE), dict(server_mod.SERVER_STATE)
        server_mod.PARENT = parent
        if window:
            os.environ[server_mod.WINDOW] = "1"
        else:
            os.environ.pop(server_mod.WINDOW, None)
        done = {}
        try:
            with free_to_quit(), contextlib.redirect_stdout(io.StringIO()):
                server_mod.used()
                if held:
                    server_mod._lock.acquire()
                halt = threading.Event()
                begun = time.monotonic()
                watcher = threading.Thread(target=lambda: done.update(quit=server_mod.idle_quit(
                    stub, wait=3600, look=0.05, stop=halt)), daemon=True)
                watcher.start()
                if held:
                    time.sleep(held)
                    server_mod._lock.release()
                    held = 0.0
                watcher.join(run_for)
                took = time.monotonic() - begun
                halt.set()
                watcher.join(2)
        finally:
            if held:
                server_mod._lock.release()
            server_mod.PARENT = kept_parent
            if kept_window is None:
                os.environ.pop(server_mod.WINDOW, None)
            else:
                os.environ[server_mod.WINDOW] = kept_window
            server_mod.SERVER_STATE.clear()
            server_mod.SERVER_STATE.update(kept_state_)
            server_mod.LIFE.update(kept_life_, requests=0, closing=False)
        return bool(done.get("quit")), took, stub.stopped

    gone_quit, gone_took, gone_stops = watched(os.getppid() + 1, True)
    held_quit, held_took, _ = watched(os.getppid() + 1, True, held=0.4, run_for=1.5)
    same_quit, _, same_stops = watched(os.getppid(), True)
    plain_quit, _, plain_stops = watched(os.getppid() + 1, False)
    # Windows hands an orphan to no one and starts a Restart anew from the old server, so it never asks there
    mac = sys.platform != "win32"
    check("159: a server the window started quits at the watcher's next look once the window has gone without Quit, "
          "its parent changed, not after the wait, a write in hand holding it until done, and never while its parent is "
          "the same or for a server the window did not start",
          server_mod.PARENT == os.getppid() and gone_quit == mac and (gone_took < 0.5 and gone_stops == 1 or not mac)
          and held_quit == mac and (0.35 <= held_took < 1.2 or not mac)
          and not same_quit and same_stops == 0 and not plain_quit and plain_stops == 0,
          f"gone {gone_quit} {gone_took:.2f}s held {held_quit} {held_took:.2f}s same {same_quit} plain {plain_quit}")

    # ── D. two real servers: one quits a second after its beats stop, one with STAY_OPEN never does
    root = scratch / "quit-159-root"
    root.mkdir(exist_ok=True)
    cfg = scratch / "quit-159-child.json"
    cfg.write_text(json.dumps({"interviewer": "Wren"}), encoding="utf-8")
    ports = []
    for _ in range(2):
        with socket.socket() as probe:
            probe.bind(("127.0.0.1", 0))
            ports.append(probe.getsockname()[1])
    base = {k: v for k, v in os.environ.items() if k != stay}
    base.update(PYTHONUNBUFFERED="1", IDIOGRAPH_START="run.sh", **{server_mod.QUIT_AFTER_ENV: "1.0"})
    base = support.faulty_env(base)
    kids = [subprocess.Popen([sys.executable, str(support.source("server.py")), "--port", str(p), "--no-browser", "--root", str(root),
                              "--config", str(cfg)], stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                             env=dict(base, **({stay: "1"} if i else {}))) for i, p in enumerate(ports)]
    # what a failure says of each server (cidiag, 7 November 2026): a wait that runs out aborts that server
    watches = [support.ChildWatch(kid, p) for kid, p in zip(kids, ports)]
    watch_at = dict(zip(ports, watches))

    def ready(at, seconds=20):
        until = time.monotonic() + seconds
        while time.monotonic() < until:
            try:
                if ask("GET", "/api/server", at=at)[0] == 200:
                    watch_at[at].answered()
                    return True
            except OSError:
                pass
            time.sleep(0.2)
        watch_at[at].ran_out(f"ready's {seconds} s ran out")
        return False

    def closed_port(at, seconds=10):
        until = time.monotonic() + seconds
        while True:
            with socket.socket() as probe:
                if probe.connect_ex(("127.0.0.1", at)) != 0:
                    return True
            if time.monotonic() >= until:
                watch_at[at].ran_out(f"closed_port's {seconds} s ran out")
                return False
            time.sleep(0.2)

    def ended(kid, seconds=20):
        try:
            return kid.wait(seconds)
        except subprocess.TimeoutExpired:
            watches[kids.index(kid)].ran_out(f"ended's {seconds} s ran out")
            return None

    real = {}
    errors = []
    try:
        real["ready"] = ready(ports[0]) and ready(ports[1])
        until = time.monotonic() + 1.8
        while time.monotonic() < until:
            ask("POST", "/api/beat", {}, origin=f"http://127.0.0.1:{ports[0]}", at=ports[0])
            time.sleep(0.3)
        real["beaten"] = kids[0].poll() is None
        last = time.monotonic()
        real["code"] = ended(kids[0])
        real["after"] = time.monotonic() - last
        real["port"] = closed_port(ports[0])
        real["stays"] = kids[1].poll() is None
        real["quit"] = ask("POST", "/api/server", {"op": "quit"}, origin=f"http://127.0.0.1:{ports[1]}", at=ports[1])[0]
        real["stay_code"] = ended(kids[1])
    except (OSError, http.client.HTTPException, ValueError) as err:
        # a connect that times out, or a read that fails: both servers are asked for their threads, the check
        # then says what it saw instead of the area ending on a bare traceback (cidiag, 7 November 2026)
        errors.append(f"{type(err).__name__}: {err}")
        for watch in watches:
            watch.ran_out(f"a call failed ({errors[-1]})")
    finally:
        for kid in kids:
            if kid.poll() is None:
                kid.kill()
                kid.wait(10)
    outs = [kid.stdout.read().decode("utf-8", errors="replace") for kid in kids]
    for kid in kids:
        kid.stdout.close()
    held_up = (real.get("ready") and real.get("beaten") and real.get("code") == 0 and 0.8 <= real.get("after", 0) < 15
               and real.get("port") and server_mod.named(server_mod.QUIT_LINE) in outs[0] and "Idiograph is closed." in outs[0]
               and real.get("stays") and real.get("quit") == 200 and real.get("stay_code") == 0
               and server_mod.named(server_mod.QUIT_LINE) not in outs[1] and "Idiograph is closed." in outs[1])
    check("159: a real server held open by its beats quits by itself once they stop, its port closed and its two lines in "
          "its output, and one with STAY_OPEN set is still running long after the wait, until Quit",
          held_up, str(real) if held_up else f"{real}, call that failed: {errors or 'none'}\n" + "\n".join(
              f"server {i + 1} ({'quits by itself' if i == 0 else 'STAY_OPEN'}), port {ports[i]}: {watches[i].says(outs[i])}"
              for i in range(len(kids))))

    # ── E. the beat in the page, run under node with its times shortened
    if node:
        script = scratch / "quit-159-beat.js"
        script.write_text(r"""
const fs = require('fs');
const src = fs.readFileSync(process.argv[2], 'utf8')
  .replace('const EVERY = 30 * 1000;', 'const EVERY = 150;')
  .replace('const AGAIN = 2 * 1000;', 'const AGAIN = 20;')
  .replace('const WAIT = 40 * 1000;', 'const WAIT = 200;');
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
function load(hook) {
  const t = { calls: [], beacons: [], on: {}, won: {}, every: [], cleared: 0, up: true };
  const ctx = {
    window: { addEventListener: (n, f) => { t.won[n] = f; } },
    document: { visibilityState: 'visible', addEventListener: (n, f) => { t.on[n] = f; } },
    navigator: { sendBeacon: (url, body) => { t.beacons.push([url, body]); return true; } },
    fetch: (url, o) => {
      t.calls.push([url, o.method, o.body, o.headers['Content-Type']]);
      return t.up ? Promise.resolve({ status: 200 }) : Promise.reject(new TypeError('Failed to fetch'));
    },
    setInterval: (f, ms) => { t.every.push(ms); return setInterval(f, ms); },
    clearInterval: (id) => { if (id !== null) t.cleared += 1; clearInterval(id); },
    setTimeout, Date,
  };
  if (hook) ctx.window.idiographClosed = hook;
  new Function(...Object.keys(ctx), src)(...Object.values(ctx));
  t.ctx = ctx;
  return t;
}
(async () => {
  const out = {};
  const a = load(null);
  await sleep(15);
  out.first = a.calls.slice();
  out.every = a.every.slice();
  a.on.visibilitychange();
  await sleep(15);
  out.visible = a.calls.length;
  a.ctx.document.visibilityState = 'hidden';
  a.on.visibilitychange();
  await sleep(15);
  out.hidden = a.calls.length;
  await sleep(165);
  out.ticked = a.calls.length;
  a.won.pagehide();
  out.beacons = a.beacons.slice();
  a.won.pageshow({ persisted: true });
  await sleep(15);
  out.shown = a.calls.length;
  let closedSaid = 0;
  const b = load(() => { closedSaid += 1; return true; });
  await sleep(15);
  b.up = false;
  await sleep(500);
  out.closedSaid = closedSaid;
  out.bCleared = b.cleared;
  out.bTries = b.calls.length;
  const tries = b.calls.length;
  await sleep(200);
  out.bQuiet = b.calls.length === tries;
  b.won.pagehide();
  out.bBeacons = b.beacons.length;
  let heldSaid = 0;
  const c = load(() => { heldSaid += 1; return false; });
  await sleep(15);
  c.up = false;
  await sleep(500);
  c.up = true;
  const cAt = c.calls.length;
  await sleep(175);
  out.heldSaid = heldSaid;
  out.cGoesOn = c.calls.length > cAt && c.cleared === 0;
  let falseSaid = 0;
  const d = load(() => { falseSaid += 1; return true; });
  await sleep(15);
  d.up = false;
  await sleep(165);
  d.up = true;
  await sleep(250);
  out.falseSaid = falseSaid;
  const e = load(null);
  await sleep(15);
  e.ctx.window.idiographQuiet();
  const eAt = e.calls.length;
  await sleep(175);
  e.won.pagehide();
  out.eQuiet = e.calls.length === eAt && e.beacons.length === 0 && e.cleared === 1;
  console.log(JSON.stringify(out));
  process.exit(0);
})();
""", encoding="utf-8")
        run = subprocess.run([node, str(script), str(support.source("family/static/beat.js"))], capture_output=True, text=True, encoding="utf-8")
        try:
            got = json.loads(run.stdout.strip().splitlines()[-1])
        except (ValueError, IndexError):
            got = {}
        check("159: the page beats at once with a POST to /api/beat and every thirty seconds after, again on coming back "
              "into view or from the browser's cache and never on going hidden, and says its last word on pagehide",
              [c[:2] + c[3:] for c in got.get("first") or []] == [["/api/beat", "POST", "application/json"]]
              and set(json.loads(got["first"][0][2])) == {"page", "at"} and got.get("every") == [150, 3000]
              and got.get("visible") == 2 and got.get("hidden") == 2 and got.get("ticked") == 3
              and [b[0] for b in got.get("beacons") or []] == ["/api/beat"]
              and json.loads(got["beacons"][0][1]) == {"gone": True, "page": json.loads(got["first"][0][2])["page"]}
              and got.get("shown") == 4,
              run.stderr[-300:] or str(got))
        check("159: a server with no answer for the wait is said closed once through the page's hook and the beat goes quiet, "
              "a hook that holds keeps it beating, a server back within the wait is never taken for a close, and "
              "idiographQuiet ends it with no last word",
              got.get("closedSaid") == 1 and got.get("bCleared") == 1 and got.get("bTries", 0) >= 5 and got.get("bQuiet")
              and got.get("bBeacons") == 0 and got.get("heldSaid", 0) >= 1 and got.get("cGoesOn") and got.get("falseSaid") == 0
              and got.get("eQuiet"), str(got))
    else:
        skip("159: the beat under node", "node is not on this machine")

    # ── F. the page: the tick filled and saved
    check("159: Settings ticks it unless the settings say false, and Save sends it with the rest",
          "$('set-quit-closed').checked = c.quit_when_closed !== false;" in fn(app, "openSettings")
          and "quit_when_closed: $('set-quit-closed').checked," in fn(app, "saveSettings"))
