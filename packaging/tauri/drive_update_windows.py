#!/usr/bin/env python3
"""Idiograph's updates proved end to end on GitHub's Windows machine (18 October 2026, the fourth Tauri
build), run by `.github/workflows/tauri.yml`'s `update` job: the test app of one version, installed by its
own installer, finding the next on a manifest on this machine signed with a throwaway key, downloading
it, the ready line, Relaunch now, the installer running with its progress bar alone and starting the new
version, What's new, then a tampered file refused and Later's update installed as the app quits.

    python packaging/tauri/drive_update_windows.py --old-setup <the older test installer>
        --release <update_proof.py's folder> --stage <the staged demo> --shipped-config <its config.json>
        --out <folder>

The window is driven through WebView2's own debugging port, as drive_windows.py drives it, opened for
this run alone. The installer starts the new version as the signed-in user, from that user's own
settings and not this run's, so the port, and the setting that keeps the app from quitting by itself,
are put in the user's settings for this machine's run alone (HKCU\\Environment, a machine GitHub wipes
after the run), and the app is started with its port and its world on its command line, which the
updater hands on to the new version. Every result goes in `results.json` beside the pictures.
"""
from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import time
import traceback
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import drive_common as dc  # noqa: E402  beside this file
import drive_windows as dw  # noqa: E402
import update_proof  # noqa: E402

RESULTS: dict = {}
NAME = "Idiograph Test"


def note(key: str, value) -> None:
    RESULTS[key] = value
    print(f"{key}: {json.dumps(value, default=str)[:1500]}", flush=True)
    if dw.SAVED:
        dw.SAVED[0].write_text(json.dumps(RESULTS, indent=2, default=str), encoding="utf-8")


def attempt(name: str, fn, seconds: float = 300) -> None:
    try:
        note(name, dw.watched(name, seconds, fn))
    except Exception:  # noqa: BLE001  one failed step never stops the rest
        note(name, {"error": traceback.format_exc()[-1500:]})


def installed() -> Path:
    return Path(os.environ["LOCALAPPDATA"]) / NAME / f"{NAME}.exe"


def exe_version(exe: Path) -> str:
    done = subprocess.run(["powershell.exe", "-NoProfile", "-Command", f"(Get-Item '{exe}').VersionInfo.ProductVersion"],
                          capture_output=True, text=True, timeout=60)
    return done.stdout.strip()


def running() -> str:
    done = subprocess.run(["tasklist", "/fi", f"imagename eq {NAME}.exe", "/fo", "csv", "/nh"], capture_output=True, text=True)
    return done.stdout.strip() if NAME in done.stdout else ""


def setup_running() -> str:
    """The installer running, the updater's own copy, `<name>-<version>-installer.exe`, among them."""
    done = subprocess.run(["tasklist", "/fo", "csv", "/nh"], capture_output=True, text=True)
    return " | ".join(line.split(",")[0].strip('"') for line in done.stdout.splitlines()
                      if "setup" in line.lower() or "-installer" in line.lower())[:300]


def user_setting(name: str, value: str | None) -> str:
    """A setting of the signed-in user's own environment, which a program the installer starts as that
    user takes: set by setx, which tells every program, Explorer among them, that it changed, or with
    None taken away."""
    args = ["setx", name, value] if value is not None else ["reg", "delete", "HKCU\\Environment", "/v", name, "/f"]
    done = subprocess.run(args, capture_output=True, text=True)
    return (done.stdout + done.stderr).strip()[:200]


def install(setup: Path, *flags: str) -> dict:
    t = time.time()
    done = subprocess.run([str(setup), *flags], capture_output=True, text=True, timeout=600)
    return {"exit": done.returncode, "seconds": round(time.time() - t, 1), "version": exe_version(installed())}


def uninstall() -> dict:
    uninst = installed().parent / "uninstall.exe"
    if not uninst.exists():
        return {"uninstaller": False}
    done = subprocess.run([str(uninst), "/S"], capture_output=True, text=True, timeout=300)
    gone = dw.wait_for(lambda: not installed().exists(), 60)
    return {"exit": done.returncode, "gone": bool(gone)}


class App:
    """The installed app started with its port and its world on its command line, and the one
    Playwright connection to its page through WebView2's debugging port."""

    def __init__(self, pw, w: dict, out: Path, tag: str, env: dict):
        self.pw, self.out = pw, out
        self.log = open(out / f"update-{tag}.log", "w", encoding="utf-8")
        self.args = [str(installed()), "--port", str(dc.PORT), "--root", str(w["project"]), "--config", str(w["config"])]
        self.proc = subprocess.Popen(self.args, env=env, stdout=self.log, stderr=subprocess.STDOUT)
        self.page = connect(pw)

    def ev(self, body: str, timeout: float = 60):
        return dw.cdp_ev(self.page, body, timeout) if self.page else {"error": "no page"}


def connect(pw, seconds: float = 120):
    """The app's own page, found through a connection made once the port and the page are there."""
    own = f"http://127.0.0.1:{dc.PORT}/"
    if not dw.wait_for(lambda: dc.listening(dc.PORT) and dc.listening(dw.CDP), seconds):
        return None
    dw.wait_for(lambda: [t for t in dw.targets() if t.get("url", "").startswith(own)], 60)
    t0 = time.time()
    while time.time() - t0 < 60:
        try:
            browser = pw.chromium.connect_over_cdp(f"http://127.0.0.1:{dw.CDP}", timeout=30000)
            for page in [p for c in browser.contexts for p in c.pages if not p.is_closed()]:
                if page.url.split("#")[0] == own:
                    got = dw.cdp_ev(page, dc.PAGE_WAIT, 60)
                    if isinstance(got, dict) and got.get("ok"):
                        return page
        except Exception:  # noqa: BLE001  not there yet
            pass
        time.sleep(1.5)
    return None


def state(app: App) -> dict:
    got = app.ev("return window.idiographUpdate ? await window.idiographUpdate('read') : null;", 20)
    return got if isinstance(got, dict) else {}


def wait_state(app: App, want: tuple, seconds: float = 120) -> dict:
    t0 = time.time()
    now: dict = {}
    while time.time() - t0 < seconds:
        now = state(app)
        if now.get("state") in want:
            return now
        time.sleep(1)
    return now


def quit_app(app: App) -> dict:
    try:
        app.ev("setTimeout(function () { serverOp('quit'); }, 200); return true;", 10)
    except Exception as exc:  # noqa: BLE001  the page goes as the app quits
        print(f"quit: {exc}")
    gone = dc.wait_closed(dc.PORT, 40)
    left = dw.wait_for(lambda: not running(), 40)
    return {"server_gone_s": gone, "app_gone": bool(left)}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--old-setup", required=True)
    ap.add_argument("--release", required=True)
    ap.add_argument("--stage", required=True)
    ap.add_argument("--shipped-config", required=True)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    from playwright.sync_api import sync_playwright

    out = Path(a.out).resolve()
    shots = out / "shots"
    shots.mkdir(parents=True, exist_ok=True)
    dw.SAVED.append(out / "results.json")
    dw.OUT.append(out)
    old_setup = Path(a.old_setup).resolve()
    release_dir = Path(a.release).resolve()
    w = dc.make_world(out, Path(a.stage).resolve(), Path(a.shipped_config).resolve())
    debug = f"--remote-debugging-port={dw.CDP}"
    env = dict(os.environ, WEBVIEW2_ADDITIONAL_BROWSER_ARGUMENTS=debug, IDIOGRAPH_STAY_OPEN="1")
    note("user_settings", [user_setting("WEBVIEW2_ADDITIONAL_BROWSER_ARGUMENTS", debug), user_setting("IDIOGRAPH_STAY_OPEN", "1")])
    manifest = update_proof.serve(release_dir)
    pw = sync_playwright().start()

    def manifest_is(which: str) -> str:
        shutil.copyfile(release_dir / f"latest-{which}.json", release_dir / "latest.json")
        return json.loads((release_dir / "latest.json").read_text(encoding="utf-8"))["version"]

    note("install_old", install(old_setup, "/S"))

    # ── asked once, Check, Download, the ready line, Settings' rows, Relaunch now, What's new
    def relaunch():
        said = {"manifest": manifest_is("good")}
        app = App(pw, w, out, "1", env)
        said["page"] = bool(app.page)
        said["asked"] = state(app)
        app.page.screenshot(path=str(shots / "win-update-ask-once.png"))
        app.ev("$('update-yes').click(); return true;")
        said["available"] = wait_state(app, ("available", "failed"))
        # the line offering the newer version, and as it downloads, both pictured since the fifth build
        app.page.screenshot(path=str(shots / "win-update-available.png"))
        app.ev("$('update-yes').click(); return true;")
        said["downloading"] = wait_state(app, ("downloading", "ready", "failed"), 30)
        app.page.screenshot(path=str(shots / "win-update-downloading.png"))
        said["ready"] = wait_state(app, ("ready", "failed"), 240)
        said["ready_line"] = app.ev("return $('update-said').textContent;")
        app.page.screenshot(path=str(shots / "win-update-ready.png"))
        app.ev("openSettings(); showPane('general'); await new Promise(function (r) { setTimeout(r, 900); }); "
               "$('update-sub').scrollIntoView({ block: 'start' }); return true;")
        app.page.screenshot(path=str(shots / "win-update-settings.png"))
        app.ev("hide('settings'); return true;")
        t = time.time()
        try:
            app.ev("$('update-yes').click(); return true;", 10)
        except Exception as exc:  # noqa: BLE001  the page goes as the app ends
            said["click"] = str(exc)[:200]
        said["old_ended"] = bool(dw.wait_for(lambda: app.proc.poll() is not None, 60))
        time.sleep(2)
        said["installer"] = setup_running()
        said["installer_desktop"] = dw.desktop(shots / "win-update-installing.png", out)
        new = connect(pw, 240)
        said["back_s"] = round(time.time() - t, 1)
        said["version"] = exe_version(installed())
        said["running"] = running()
        if new is None:
            said["desktop"] = dw.desktop(shots / "win-update-after.png", out)
            return said
        time.sleep(2)
        app.page = new
        said["after"] = state(app)
        said["foot"] = app.ev("return { shown: !$('whatsnew-line').hidden, said: $('whatsnew-said').textContent };")
        said["desktop"] = dw.desktop(shots / "win-update-after.png", out)
        app.page.screenshot(path=str(shots / "win-whats-new-line.png"))
        app.ev("$('whatsnew-open').click(); await new Promise(function (r) { setTimeout(r, 800); }); return true;")
        said["sheet"] = app.ev("return { open: !$('whatsnew').hidden, title: $('whatsnew-title').textContent, "
                               "lines: Array.prototype.map.call($('whatsnew-notes').children, function (p) { return p.textContent; }) };")
        app.page.screenshot(path=str(shots / "win-whats-new-sheet.png"))
        app.ev("hide('whatsnew'); return true;")
        said["quit"] = quit_app(app)
        return said
    attempt("relaunch_run", relaunch, 900)

    # back to the older version for the next two runs: uninstalled, every setting kept, then installed
    note("back_to_old", {"uninstall": uninstall(), "install": install(old_setup, "/S")})

    # ── a tampered file refused, and nothing installed as the app quits
    def tampered():
        said = {"manifest": manifest_is("tampered")}
        app = App(pw, w, out, "2", env)
        said["page"] = bool(app.page)
        app.ev("await window.idiographUpdate('check'); return true;")
        said["available"] = wait_state(app, ("available", "failed"))
        app.ev("await window.idiographUpdate('download'); return true;")
        said["failed"] = wait_state(app, ("failed", "ready"), 240)
        app.ev("openSettings(); showPane('general'); await new Promise(function (r) { setTimeout(r, 900); }); "
               "$('update-sub').scrollIntoView({ block: 'start' }); return true;")
        app.page.screenshot(path=str(shots / "win-update-refused.png"))
        app.ev("hide('settings'); return true;")
        said["quit"] = quit_app(app)
        time.sleep(5)
        said["installer_after_quit"] = setup_running()
        said["version"] = exe_version(installed())
        return said
    attempt("tampered_run", tampered, 600)

    # ── downloaded by itself, Later, and the update installed as the app quits, nothing started after
    def later():
        said = {"manifest": manifest_is("good")}
        app = App(pw, w, out, "3", env)
        said["page"] = bool(app.page)
        app.ev("await window.idiographUpdate('set', { download: true }); return true;")
        app.ev("await window.idiographUpdate('check'); return true;")
        said["ready"] = wait_state(app, ("ready", "failed"), 240)
        app.ev("$('update-no').click(); return true;")
        time.sleep(1)
        said["line_hidden"] = app.ev("return $('update-line').hidden;")
        said["quit"] = quit_app(app)
        said["installing"] = dw.wait_for(setup_running, 30, 0.5) or ""
        said["installer_desktop"] = dw.desktop(shots / "win-update-at-quit.png", out)
        dw.wait_for(lambda: not setup_running(), 240)
        time.sleep(5)
        said["version"] = exe_version(installed())
        said["started_after"] = running() or dc.listening(dc.PORT)
        return said
    attempt("later_run", later, 900)

    pw.stop()
    manifest.shutdown()
    manifest.server_close()
    note("user_settings_gone", [user_setting("WEBVIEW2_ADDITIONAL_BROWSER_ARGUMENTS", None), user_setting("IDIOGRAPH_STAY_OPEN", None)])
    note("window_json", (Path(os.environ["APPDATA"]) / "uk.co.adamknowles.idiograph.test" / "window.json").read_text(encoding="utf-8")[-800:]
         if (Path(os.environ["APPDATA"]) / "uk.co.adamknowles.idiograph.test" / "window.json").exists() else None)
    return 0


if __name__ == "__main__":
    sys.exit(main())
