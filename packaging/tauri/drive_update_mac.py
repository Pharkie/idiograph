#!/usr/bin/env python3
"""Idiograph's updates proved end to end on a Mac (18 October 2026, the fourth Tauri build): a test app of
one version finding the next on a manifest on this machine, signed with a throwaway key, downloading
it, the ready line, Relaunch now, the new version opening with What's new, Later installing as the app
quits, and a tampered file refused. The standard library only.

    python3 packaging/tauri/drive_update_mac.py --old "<folder>/Idiograph Test.app" --release <folder>
        --stage <build/stage> --out <folder>

`--old` is the test app at the older version, built with the `drive` feature, the throwaway key's public
half and the manifest's address (`build_mac.py --test-app --drive --update-key --update-url`), and
`--release` the folder `update_proof.py release` made from the newer one. Each run takes a fresh copy of
the older app into `<out>/app`, which the update then replaces in place, so the build itself is never
touched, and starts it as `open -g -n -W` starts it, so it never takes the keyboard (drive_mac.py). The
pictures are each window's page as its web view draws it, a heading baked in above (heading.js), at 1280
and 360 wide, light and dark.
"""
from __future__ import annotations

import argparse
import json
import os
import plistlib
import shutil
import subprocess
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import drive_common as dc  # noqa: E402  beside this file
import drive_mac as dm  # noqa: E402
import update_proof  # noqa: E402

RESULTS: dict = {}
SIZES = (("1280", 1280, 800), ("360", 360, 760))
LOOKS = ("light", "dark")


def note(key: str, value) -> None:
    RESULTS[key] = value
    print(f"{key}: {json.dumps(value, default=str)[:900]}", flush=True)
    if OUT:
        (OUT[0] / "results.json").write_text(json.dumps(RESULTS, indent=2, default=str), encoding="utf-8")


OUT: list = []


def attempt(name: str, fn) -> None:
    try:
        note(name, fn())
    except Exception as exc:  # noqa: BLE001  one failed step never stops the rest
        note(name, {"error": f"{type(exc).__name__}: {exc}"})


def version_of(app: Path) -> str:
    with open(app / "Contents" / "Info.plist", "rb") as fh:
        return plistlib.load(fh).get("CFBundleShortVersionString", "")


def said_since(err: Path, start: str, after_size: int = 0) -> list[str]:
    """The window's own lines from its output file, since `after_size` bytes, that begin `start`: the
    relaunched app writes on where the first left off, after `open` has stopped reading."""
    try:
        text = err.read_bytes()[after_size:].decode("utf-8", "replace")
    except OSError:
        return []
    return [line for line in text.splitlines() if line.startswith(start)]


def wait_said(err: Path, start: str, seconds: float, after_size: int = 0):
    t0 = time.time()
    while time.time() - t0 < seconds:
        hit = said_since(err, start, after_size)
        if hit:
            return hit[-1]
        time.sleep(0.2)
    return None


class Run:
    """One run of a fresh copy of the older app, its orders file, its output and its pictures."""

    def __init__(self, name: str, old: Path, out: Path, env: dict, stub: dc.Stub):
        self.name, self.out, self.stub = name, out, stub
        self.app = out / "app" / old.name
        shutil.rmtree(self.app.parent, ignore_errors=True)
        self.app.parent.mkdir(parents=True)
        subprocess.run(["ditto", str(old), str(self.app)], check=True)
        self.orders = out / f"orders-{name}"
        self.log = out / f"app-{name}.log"
        self.env = dict(env, IDIOGRAPH_WINDOW_ORDERS=str(self.orders))
        self.t0 = time.time()
        self.proc = dm.App(self.app, self.env, self.log)
        self.err = self.log.with_suffix(".err")

    def loaded(self, seconds: float = 90, after: float | None = None):
        return dm.loaded(self.stub, self.t0 if after is None else after, seconds, label="main")

    def js(self, body: str, timeout: float = 60):
        return dm.run(self.stub, "main", body, timeout)

    def order(self, line: str) -> None:
        with open(self.orders, "a", encoding="utf-8") as fh:
            fh.write(line + "\n")

    def state(self) -> dict:
        got = self.js("return window.idiographUpdate ? await window.idiographUpdate('read') : null;", 20)
        return got if isinstance(got, dict) else {}

    def wait_state(self, want: tuple, seconds: float = 90) -> dict:
        t0 = time.time()
        now: dict = {}
        while time.time() - t0 < seconds:
            now = self.state()
            if now.get("state") in want:
                return now
            time.sleep(0.7)
        return now

    def frame(self, w: int, h: int) -> None:
        self.order(f"frame 60 60 {w} {h}")
        time.sleep(1.2)

    def snap(self, shots: Path, name: str, head: str, check: str) -> dict:
        """The page as its web view draws it, at each size and look, a heading baked into each. A check's
        window stands below every other, where WebKit runs no animation, so a card's fade and the foot
        line's rise stood at their first frame, unseen, and a theme's colours half changed, in the first
        run's pictures: every animation and transition is stilled for the pictures alone."""
        self.js("if (!document.getElementById('drive-still')) { var s = document.createElement('style'); s.id = 'drive-still'; "
                "s.textContent = '*, *::before, *::after { animation: none !important; transition: none !important; }'; "
                "document.head.appendChild(s); } return true;", 10)
        made = {}
        for look in LOOKS:
            self.js(dc.THEME % json.dumps(look), 20)
            for tag, w, h in SIZES:
                self.frame(w, h)
                raw = self.out / f"raw-{name}-{tag}-{look}.png"
                raw.unlink(missing_ok=True)
                size = self.err.stat().st_size if self.err.exists() else 0
                self.order(f"snappage main {raw}")
                wait_said(self.err, f"drive: snappage true {raw}", 15, size)
                final = shots / f"mac-{name}-{tag}-{look}.png"
                baked = subprocess.run(["osascript", "-l", "JavaScript", str(HERE / "heading.js"), str(raw), str(final),
                                        f"{head}, {tag} wide, {look}", check], capture_output=True, text=True)
                made[f"{tag}-{look}"] = (baked.stdout + baked.stderr).strip() if raw.exists() else "no picture"
                raw.unlink(missing_ok=True)
        self.js(dc.THEME % json.dumps("light"), 20)
        self.frame(1280, 800)
        return made

    def quit(self, seconds: float = 60) -> dict:
        """Quit as Settings' Quit asks it, the server and the app gone after."""
        t = time.time()
        self.js("setTimeout(function () { serverOp('quit'); }, 200); return true;", 10)
        gone = dc.wait_closed(dc.PORT, seconds)
        left = self.running(seconds)
        return {"server_gone_s": gone, "app_gone": not left, "seconds": round(time.time() - t, 1)}

    def running(self, seconds: float = 0) -> bool:
        """Whether the app from this run's copy still runs, waited for up to `seconds` to end."""
        t0 = time.time()
        while True:
            alive = subprocess.run(["pgrep", "-f", str(self.app / "Contents" / "MacOS")], capture_output=True, text=True).stdout.strip()
            if not alive or time.time() - t0 >= seconds:
                return bool(alive)
            time.sleep(0.5)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--old", required=True)
    ap.add_argument("--release", required=True)
    ap.add_argument("--stage", required=True)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    out = Path(a.out).resolve()
    OUT.append(out)
    shots = out / "shots"
    shots.mkdir(parents=True, exist_ok=True)
    old = Path(a.old).resolve()
    release_dir = Path(a.release).resolve()
    stage = Path(a.stage).resolve()
    w = dc.make_world(out, stage / "demo", stage / "config.json")
    home = out / "home"
    (home / "Downloads").mkdir(parents=True, exist_ok=True)
    (out / "drive.js").write_text(dm.DRIVE_JS, encoding="utf-8")
    base = dict(os.environ, HOME=str(home), IDIOGRAPH_WINDOW_DRIVE=str(out / "drive.js"), IDIOGRAPH_WINDOW_NO_OPEN="1")
    env = dc.app_env(base, w)
    stub = dc.Stub()
    manifest = update_proof.serve(release_dir)
    note("old_version", version_of(old))

    def manifest_is(which: str) -> str:
        shutil.copyfile(release_dir / f"latest-{which}.json", release_dir / "latest.json")
        return json.loads((release_dir / "latest.json").read_text(encoding="utf-8"))["version"]

    # ── the first run: asked once, Check, Download, the ready line, Settings' rows, Relaunch now, What's new
    def first():
        said = {"manifest": manifest_is("good")}
        run = Run("relaunch", old, out, env, stub)
        said["loaded"] = bool(run.loaded())
        run.js(dc.world_js(w), 20)
        said["asked"] = run.state()
        said["line_shown"] = run.js("return { shown: !$('update-line').hidden, said: $('update-said').textContent, "
                                    "more: $('update-more').textContent, yes: $('update-yes').textContent, no: $('update-no').textContent };")
        said["shots_ask"] = run.snap(shots, "update-ask-once", "The question asked once, at the head of the home screen",
                                     "Check for updates?, the line about what checking sends, Check and Don't check")
        run.js("$('update-yes').click(); return true;")
        said["available"] = run.wait_state(("available", "failed"))
        said["available_line"] = run.js("return $('update-said').textContent;")
        run.js("$('update-yes').click(); return true;")
        said["ready"] = run.wait_state(("ready", "failed"), 180)
        said["ready_line"] = run.js("return { said: $('update-said').textContent, yes: $('update-yes').textContent, no: $('update-no').textContent };")
        said["shots_ready"] = run.snap(shots, "update-ready", "The update ready, at the head of the home screen",
                                       f"Idiograph {said['manifest']} is ready. Relaunch to use it., Relaunch now and Later")
        run.js("openSettings(); showPane('general'); await new Promise(function (r) { setTimeout(r, 900); }); "
               "$('update-sub').scrollIntoView({ block: 'start' }); return true;")
        said["settings"] = run.js("return { running: $('update-running').textContent, check: $('set-update-check').checked, "
                                  "download: $('set-update-download').checked, checked: $('update-checked').textContent, "
                                  "state: $('update-state').textContent, relaunch: !$('update-relaunch').hidden };")
        said["shots_settings"] = run.snap(shots, "update-settings", "Settings, General: Updates",
                                          "the version with What's new, the two ticks, the line about what checking sends, Check now with the last check's time, Relaunch now")
        run.js("hide('settings'); return true;")
        size = run.err.stat().st_size
        t = time.time()
        run.js("$('update-yes').click(); return true;", 10)
        said["relaunching"] = wait_said(run.err, "Idiograph: relaunching", 30, size)
        said["installed_at_quit"] = wait_said(run.err, "Idiograph: installing update", 60, size)
        back = run.loaded(120, after=t + 0.5)
        said["back"] = bool(back)
        said["bundle_version"] = version_of(run.app)
        if back:
            time.sleep(1.5)
            said["after"] = run.state()
            said["foot"] = run.js("return { shown: !$('whatsnew-line').hidden, said: $('whatsnew-said').textContent };")
            said["shots_foot"] = run.snap(shots, "whats-new-line", "Once after an update, the line at the foot",
                                          f"Updated to Idiograph {said['manifest']}., What's new and Close, the page as it was before the relaunch")
            run.js("$('whatsnew-open').click(); await new Promise(function (r) { setTimeout(r, 700); }); return true;")
            said["sheet"] = run.js("return { open: !$('whatsnew').hidden, title: $('whatsnew-title').textContent, "
                                   "date: $('whatsnew-date').textContent, lines: Array.prototype.map.call($('whatsnew-notes').children, function (p) { return p.textContent; }) };")
            said["shots_sheet"] = run.snap(shots, "whats-new-sheet", "What's new, the version's notes",
                                           f"Idiograph {said['manifest']}, its date, a plain line for each part, Done")
            run.js("hide('whatsnew'); return true;")
            said["seen_after"] = run.state().get("updated")
            said["quit"] = run.quit()
        return said
    attempt("relaunch_run", first)

    # ── the second run: downloaded by itself, Later, and the update installed as the app quits
    def later():
        said = {"manifest": manifest_is("good")}
        run = Run("later", old, out, env, stub)
        said["loaded"] = bool(run.loaded())
        said["start"] = run.state()
        run.js("await window.idiographUpdate('set', { download: true }); return true;")
        run.js("await window.idiographUpdate('check'); return true;")
        said["ready"] = run.wait_state(("ready", "failed"), 180)
        run.js("$('update-no').click(); return true;")
        time.sleep(0.8)
        said["after_later"] = {"line_hidden": run.js("return $('update-line').hidden;"), "later": run.state().get("later")}
        size = run.err.stat().st_size
        said["quit"] = run.quit()
        said["installed_at_quit"] = wait_said(run.err, "Idiograph: installing update", 20, size)
        said["bundle_version"] = version_of(run.app)
        time.sleep(6)
        said["started_again"] = dc.listening(dc.PORT) or run.running()
        return said
    attempt("later_run", later)

    # ── the third run: a tampered file refused, and nothing put in place
    def tampered():
        said = {"manifest": manifest_is("tampered")}
        run = Run("tampered", old, out, env, stub)
        said["loaded"] = bool(run.loaded())
        run.js("await window.idiographUpdate('set', { download: false }); return true;")
        run.js("await window.idiographUpdate('check'); return true;")
        said["available"] = run.wait_state(("available", "failed"))
        run.js("await window.idiographUpdate('download'); return true;")
        said["failed"] = run.wait_state(("failed", "ready"), 120)
        run.js("openSettings(); showPane('general'); await new Promise(function (r) { setTimeout(r, 900); }); "
               "$('update-sub').scrollIntoView({ block: 'start' }); return true;")
        said["settings"] = run.js("return { failed: $('update-failed').textContent, shown: !$('update-failed').hidden };")
        said["shots_refused"] = run.snap(shots, "update-refused", "Settings, General: a tampered update refused",
                                         "the amber line, Idiograph could not confirm the update is genuine, so it was not installed.")
        run.js("hide('settings'); return true;")
        said["quit"] = run.quit()
        said["bundle_version"] = version_of(run.app)
        said["log"] = said_since(run.err, "Idiograph: the update did not download")
        return said
    attempt("tampered_run", tampered)

    manifest.shutdown()
    manifest.server_close()
    stub.close()
    note("ports_closed", {"server": not dc.listening(dc.PORT), "stub": not dc.listening(dc.STUB),
                          "manifest": not dc.listening(update_proof.PORT)})
    return 0


if __name__ == "__main__":
    sys.exit(main())
