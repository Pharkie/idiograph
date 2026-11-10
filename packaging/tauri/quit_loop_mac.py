#!/usr/bin/env python3
"""Quit asked of the window many times on a Mac, some of them while its board moves, and the crash
reports counted (31 October, quitcrash: 0.9.14 crashed as Adam quit it, the system's web view drawing a
frame for a page it had freed, and the server Quit was to stop afterwards ran on). Each run starts the
test app as `open -g -n -W` starts it, so it never takes the keyboard, on a home folder of its own and
the invented world `drive_common` makes, opens Rowan's PETs board from the project's row, sets the
board panning and every scrollable part of the page scrolling on each frame, then after a moment
chosen at random asks Quit as the menu's Quit asks it (the `drive` feature's order `item quit`), and
notes how long the server and the window took to end, whether the server was stopped before the app
ended, and anything left running. At the end every crash report the runs left in
~/Library/Logs/DiagnosticReports is counted, by the path of the process that crashed. A crash as rare
as Adam's may not show in fifty runs, so a count of none is no proof. The standard library only.

    python3 packaging/tauri/quit_loop_mac.py --app "<Idiograph Test.app>" --stage <build/stage> --out <folder> --runs 50

`--stage` is a folder holding `demo/` and `config.json` as a build stages them. IDIOGRAPH_DRIVE_PORT and
IDIOGRAPH_DRIVE_STUB give the run its own ports, as for the other drives.
"""
from __future__ import annotations

import argparse
import json
import random
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import drive_common as dc  # noqa: E402  beside this file
import drive_mac as dm  # noqa: E402  beside this file

# the board panned sideways on every frame as a wheel pans it, and every part of the page that scrolls
# scrolled back and forth, which the system's web view scrolls on its own side, until the page goes
MOVE = """var stage = typeof thStage === 'function' ? thStage() : null;
var parts = Array.prototype.slice.call(document.querySelectorAll('*')).filter(function (el) {
  var s = getComputedStyle(el);
  return el.scrollHeight > el.clientHeight + 20 && /(auto|scroll)/.test(s.overflowY) && el.offsetParent;
});
if (document.scrollingElement) parts.push(document.scrollingElement);
var dir = 1, n = 0;
window.__quitLoopMoving = true;
(function frame() {
  if (!window.__quitLoopMoving) return;
  n += 1;
  if (n % 45 === 0) dir = -dir;
  if (stage) {
    var r = stage.getBoundingClientRect();
    stage.dispatchEvent(new WheelEvent('wheel', { deltaX: 24 * dir, deltaY: 0, clientX: r.left + r.width / 2,
      clientY: r.top + r.height / 2, bubbles: true, cancelable: true }));
  }
  parts.forEach(function (el) { el.scrollTop += 18 * dir; });
  requestAnimationFrame(frame);
})();
return { board: !!stage && !!document.querySelector('.th-card, .th-label'), parts: parts.length };"""


def crash_reports(since: float, paths: list[str]) -> list[dict]:
    """The crash reports written since `since` for a process whose path is under one of `paths`."""
    found = []
    folder = Path.home() / "Library" / "Logs" / "DiagnosticReports"
    for report in sorted(folder.glob("*.ips")):
        try:
            if report.stat().st_mtime < since:
                continue
            head, _, body = report.read_text(encoding="utf-8", errors="replace").partition("\n")
            said = json.loads(body) if body.strip().startswith("{") else {}
        except (OSError, ValueError):
            continue
        path = said.get("procPath", "")
        if any(path.startswith(p) for p in paths):
            frames = said.get("threads", [{}])[said.get("faultingThread", 0)].get("frames", [])
            top = [f.get("symbol") for f in frames[:3] if f.get("symbol")]
            found.append({"file": report.name, "path": path, "exception": said.get("exception", {}).get("type"),
                          "top": top})
    return found


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--app", required=True)
    ap.add_argument("--stage", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--runs", type=int, default=50)
    ap.add_argument("--seed", type=int, default=31)
    a = ap.parse_args()
    out = Path(a.out).resolve()
    out.mkdir(parents=True, exist_ok=True)
    stage = Path(a.stage).resolve()
    bundle = Path(a.app).resolve()
    pick = random.Random(a.seed)
    w = dc.make_world(out, stage / "demo", stage / "config.json")
    (out / "drive.js").write_text(dm.DRIVE_JS, encoding="utf-8")
    orders = out / "orders"
    (out / "logs").mkdir(exist_ok=True)
    stub = dc.Stub()
    began = time.time()
    runs = []
    try:
        for n in range(1, a.runs + 1):
            home = out / "homes" / f"run-{n:03d}"
            home.mkdir(parents=True, exist_ok=True)
            env = dc.app_env({"HOME": str(home)}, w, IDIOGRAPH_WINDOW_DRIVE=out / "drive.js",
                             IDIOGRAPH_WINDOW_ORDERS=orders, IDIOGRAPH_WINDOW_NO_OPEN="1")
            orders.unlink(missing_ok=True)
            t = time.time()
            app = dm.App(bundle, env, out / "logs" / f"run-{n:03d}.log")
            said = {"run": n}
            said["loaded"] = bool(dm.loaded(stub, t, 60, label="main"))
            # a third of the runs quit on the home screen with nothing moving, the rest on a moving board
            moving = n % 3 != 0
            if said["loaded"] and moving:
                said["board"] = dm.run(stub, "main", dc.HEAD + dc.STEPS["pets"], timeout=30)
                said["moving"] = dm.run(stub, "main", MOVE, timeout=10)
            pause = round(pick.uniform(0.05, 1.5), 2)
            time.sleep(pause)
            said["pause_s"] = pause
            asked = time.time()
            orders.write_text("item quit\n", encoding="utf-8")
            said["server_gone_s"] = dc.wait_closed(dc.PORT, 45)
            ended = app.end(60)
            said["app_gone_s"] = round(time.time() - asked, 2)
            said.update(ended)
            said["stopped_line"] = app.said("Idiograph: the server stopped")
            runs.append(said)
            print(json.dumps(said)[:400], flush=True)
            (out / "runs.json").write_text(json.dumps(runs, indent=2), encoding="utf-8")
            time.sleep(1.0)
    finally:
        stub.close()
    time.sleep(5)
    crashes = crash_reports(began - 1, [str(bundle)])
    summary = {
        "runs": len(runs),
        "loaded": sum(1 for r in runs if r.get("loaded")),
        "moving": sum(1 for r in runs if isinstance(r.get("moving"), dict) and r["moving"].get("parts") is not None),
        "server_left_running": sum(1 for r in runs if r.get("left")),
        "server_not_gone": sum(1 for r in runs if r.get("server_gone_s", -1) < 0),
        "app_killed": sum(1 for r in runs if r.get("exit") == "killed"),
        "crash_reports": crashes,
    }
    (out / "summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(json.dumps(summary, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
