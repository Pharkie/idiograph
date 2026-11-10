#!/usr/bin/env python3
"""The window's own part of Restart and Quit checked on a Mac with no page driven (17 October): the
test app started as `open -g -n -W` starts it, Restart then Quit asked of the server as the page asks
them, and the app's end timed, then a second start, and the last window closed. Nothing here needs the
page to draw, so it runs while someone works at the Mac. The standard library only.

    python3 packaging/tauri/quit_mac.py --app "<Idiograph Test.app>" --stage <build/stage> --out <folder>
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
import time
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import drive_common as dc  # noqa: E402  beside this file
import drive_mac as dm  # noqa: E402  beside this file


def server(op: str | None = None) -> dict:
    """/api/server as the page asks it: its state for a GET, Restart or Quit for a POST."""
    data = json.dumps({"op": op}).encode() if op else None
    req = urllib.request.Request(f"http://127.0.0.1:{dc.PORT}/api/server", data=data, method="POST" if op else "GET",
                                 headers={"Host": f"127.0.0.1:{dc.PORT}", "Content-Type": "application/json"})
    try:
        with urllib.request.build_opener(urllib.request.ProxyHandler({})).open(req, timeout=10) as res:
            return json.loads(res.read() or b"{}")
    except (OSError, ValueError) as exc:
        return {"error": str(exc)}


def start(bundle: Path, env: dict, err: Path) -> "dm.App":
    """A run of the window through drive_mac's App, as `open -g -n -W` starts it, its standard error in `err`. The
    App notes the window and its server as they come and stops whatever is left however this check ends, at its
    end, on an error or on a signal, since `open` starts the window under launchd and never as this check's child
    and IDIOGRAPH_STAY_OPEN keeps its server from quitting by itself (loose31, 31 October 2026: the one drive of the
    Mac window still outside the App drivemac gave drive_mac.py on 27 October)."""
    return dm.App(bundle, env, err.with_suffix(".log"))


def wait(fn, seconds: float):
    t0 = time.time()
    while time.time() - t0 < seconds:
        got = fn()
        if got:
            return round(time.time() - t0, 2)
        time.sleep(0.2)
    return None


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--app", required=True)
    ap.add_argument("--stage", required=True)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    out = Path(a.out).resolve()
    out.mkdir(parents=True, exist_ok=True)
    stage = Path(a.stage).resolve()
    w = dc.make_world(out, stage / "demo", stage / "config.json")
    home = out / "home"
    home.mkdir(exist_ok=True)
    closer = out / "close-these"
    env = {"HOME": str(home), "IDIOGRAPH_PORT": str(dc.PORT), "IDIOGRAPH_STAY_OPEN": "1",
           "IDIOGRAPH_ARGS": f"--root {w['project']} --config {w['config']}",
           "IDIOGRAPH_CLAUDE_DESKTOP_CONFIG": str(w["world"] / "claude_desktop_config.json"),
           "IDIOGRAPH_WINDOW_CLOSE": str(closer), "IDIOGRAPH_WINDOW_NO_OPEN": "1"}
    bundle = Path(a.app).resolve()
    said: dict = {}

    # Restart, then Quit: the window waits through the one and closes with the other
    app = start(bundle, env, out / "app-1.err")
    said["answered_s"] = wait(lambda: "started" in server(), 60)
    before = server().get("started")
    said["restart"] = server("restart")
    said["back_s"] = wait(lambda: (lambda s: s and s != before)(server().get("started")), 40)
    time.sleep(3)
    said["app_kept_through_restart"] = app.proc.poll() is None
    # a second start while it runs: it ends at once and starts no server
    second = start(bundle, env, out / "app-second.err")
    try:
        said["second_start_exit"] = second.proc.wait(timeout=30)
    except subprocess.TimeoutExpired:
        second.stop()
        said["second_start_exit"] = "still running"
    said["next_port_listening"] = dc.listening(dc.PORT + 1)
    said["quit"] = server("quit")
    said["server_gone_s"] = dc.wait_closed(dc.PORT, 30)
    t = time.time()
    try:
        said["app_exit"] = app.proc.wait(timeout=30)
        said["app_gone_after_quit_s"] = round(time.time() - t, 2)
    except subprocess.TimeoutExpired:
        said["app_exit"] = "still running"
        closer.write_text("main\n", encoding="utf-8")
        app.proc.wait(timeout=30)

    # the last window closed by its close button: the app ends, and the server with it
    app = start(bundle, env, out / "app-2.err")
    said["answered_again_s"] = wait(lambda: "started" in server(), 60)
    time.sleep(2)
    closer.write_text("main\n", encoding="utf-8")
    said["server_gone_after_close_s"] = dc.wait_closed(dc.PORT, 40)
    try:
        said["app_exit_after_close"] = app.proc.wait(timeout=40)
    except subprocess.TimeoutExpired:
        said["app_exit_after_close"] = "still running"
    said["brought_forward"] = [line for line in (out / "app-1.err").read_text(encoding="utf-8", errors="replace").splitlines()
                               if "brought forward" in line or "server stopped" in line]
    # whatever a run left, stopped and named, a server that outlived its window among them
    left = sorted({cmd for run in list(dm.STARTED) for cmd in run.stop()})
    if left:
        said["left"] = left
    said["port_closed_at_end"] = not dc.listening(dc.PORT)
    (out / "results.json").write_text(json.dumps(said, indent=2), encoding="utf-8")
    print(json.dumps(said, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
