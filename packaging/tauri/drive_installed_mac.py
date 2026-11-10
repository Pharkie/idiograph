#!/usr/bin/env python3
"""The Mac app as a tester gets it, checked on GitHub's Mac (17 October 2026, the third Tauri build), run by
`.github/workflows/tauri.yml`'s mac job on a push whose message holds [mac].

    python packaging/tauri/drive_installed_mac.py --dmg <Idiograph.dmg> --out <folder>

1. The disk image opened as a double-click opens it, its window taken from the screen with a heading
   saying what it shows and what to check, in the light and then the dark, this machine's appearance
   turned to dark and back for it (GitHub's machine, wiped after the run). Since the fourth build (18
   October) the image is dmgbuild's, laid out: Idiograph at the left, an arrow, Applications at the right.
2. The app copied to Applications as a drag copies it, the image put away, and the app opened from
   there as the Dock opens it, its first window taken from the screen.
3. `Idiograph mcp` and `Idiograph cli` from the bundle, as Claude Desktop and an agent run them: the
   server's own path inside the bundle, which Add Idiograph to Claude Desktop writes, and the app's own
   executable, which hands over to it, as an entry written for 0.9.0 still runs it.
4. The bundle itself: its version, its architectures, its signature, its size and the server's links.
5. Quit, as Settings' Quit asks it, and the app and its server gone.

This machine is GitHub's, wiped after the run, so the real app is installed in Applications here and
nowhere else. Every result goes in `results.json` beside the shots.
"""
from __future__ import annotations

import argparse
import json
import plistlib
import socket
import subprocess
import sys
import time
import traceback
import urllib.request
from pathlib import Path

HERE = Path(__file__).resolve().parent
RESULTS: dict = {}
SAVED: list = []
APP = Path("/Applications/Idiograph.app")


def note(key: str, value) -> None:
    RESULTS[key] = value
    print(f"{key}: {json.dumps(value, default=str)[:1500]}", flush=True)
    if SAVED:
        SAVED[0].write_text(json.dumps(RESULTS, indent=2, default=str), encoding="utf-8")


def attempt(name: str, fn) -> None:
    try:
        note(name, fn())
    except Exception:  # noqa: BLE001  one failed step never stops the rest
        note(name, {"error": traceback.format_exc()[-1500:]})


def sh(*cmd, timeout: float = 120, **kw) -> subprocess.CompletedProcess:
    return subprocess.run([str(c) for c in cmd], capture_output=True, text=True, timeout=timeout, **kw)


WINDOW_JXA = """ObjC.import('CoreGraphics');
var list = ObjC.deepUnwrap(ObjC.castRefToObject($.CGWindowListCopyWindowInfo(1, 0)));
var best = null;
list.forEach(function (w) {
  if (w.kCGWindowOwnerName === %s && w.kCGWindowLayer === 0 && (!best || w.kCGWindowBounds.Width * w.kCGWindowBounds.Height > best[1])) best = [w.kCGWindowNumber, w.kCGWindowBounds.Width * w.kCGWindowBounds.Height];
});
best ? String(best[0]) : '';"""


def shot(out: Path, name: str, head: str, check: str, owner: str = "") -> str:
    """The installed app's own window taken by its number alone (`screencapture -o -l`, with the sound), never the
    screen or another app's window, then a heading baked in above it by heading.js. `owner` is the app's process name."""
    if not owner:
        return "not taken: that window is not this app's own"
    number = sh("osascript", "-l", "JavaScript", "-e", WINDOW_JXA % json.dumps(owner)).stdout.strip()
    if not number.isdigit():
        return f"no window of {owner} to capture"
    raw = out / "shots" / f"raw-{name}"
    taken = sh("screencapture", "-o", "-l", number, raw)
    if taken.returncode != 0 or not raw.is_file():
        return f"no window capture: {(taken.stdout + taken.stderr).strip()[:300]}"
    baked = sh("osascript", "-l", "JavaScript", HERE / "heading.js", raw, out / "shots" / name, head, check)
    raw.unlink(missing_ok=True)
    return (baked.stdout + baked.stderr).strip()


def listening(port: int) -> bool:
    with socket.socket() as s:
        s.settimeout(0.3)
        return s.connect_ex(("127.0.0.1", port)) == 0


def wait_for(fn, seconds: float, every: float = 0.5):
    t0 = time.time()
    while time.time() - t0 < seconds:
        try:
            got = fn()
            if got:
                return got
        except Exception:  # noqa: BLE001
            pass
        time.sleep(every)
    return None


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dmg", required=True)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    out = Path(a.out).resolve()
    (out / "shots").mkdir(parents=True, exist_ok=True)
    SAVED.append(out / "results.json")
    dmg = Path(a.dmg).resolve()
    volume: list = []

    def image():
        attached = sh("hdiutil", "attach", dmg, "-readonly", "-plist")
        mount = next((e.get("mount-point") for e in plistlib.loads(attached.stdout.encode()).get("system-entities", [])
                      if e.get("mount-point")), None)
        volume.append(mount)
        said = {"mount": mount, "holds": sorted(p.name for p in Path(mount).iterdir()) if mount else [],
                "applications_link": Path(mount, "Applications").is_symlink() if mount else None,
                "size_mb": round(dmg.stat().st_size / 1e6, 1)}
        said["layout"] = Path(mount, ".DS_Store").is_file() if mount else None
        said["background"] = sorted(p.name for p in Path(mount, ".background").iterdir()) if mount and Path(mount, ".background").is_dir() else []
        sh("open", mount)
        time.sleep(4)
        said["shot"] = shot(out, "mac-dmg-window.png", "The disk image's window, on a Mac, light",
                            "Idiograph left, an arrow, Applications right, no toolbar or sidebar, both names readable")
        dark = 'tell application "System Events" to tell appearance preferences to set dark mode to {}'
        said["dark"] = sh("osascript", "-e", dark.format("true")).returncode
        time.sleep(3)
        said["shot_dark"] = shot(out, "mac-dmg-window-dark.png", "The disk image's window, on a Mac, dark",
                                 "the same window in the dark, both names readable on the background")
        said["light_again"] = sh("osascript", "-e", dark.format("false")).returncode
        time.sleep(2)
        return said
    attempt("image", image)

    def install():
        mount = volume[0]
        sh("osascript", "-e", 'tell application "Finder" to close every window')
        copied = sh("ditto", Path(mount) / "Idiograph.app", APP)
        sh("hdiutil", "detach", mount, "-quiet")
        info = plistlib.loads((APP / "Contents" / "Info.plist").read_bytes())
        server = APP / "Contents" / "Resources" / "server"
        links = [str(p.relative_to(server)) for p in server.rglob("*") if p.is_symlink()]
        return {"copied": copied.returncode, "version": info.get("CFBundleShortVersionString"),
                "identifier": info.get("CFBundleIdentifier"), "minimum": info.get("LSMinimumSystemVersion"),
                "archs": sh("lipo", "-archs", APP / "Contents" / "MacOS" / "Idiograph").stdout.strip(),
                "server_archs": sh("lipo", "-archs", server / "Idiograph").stdout.strip(),
                "signature": [ln for ln in sh("codesign", "-dv", APP).stderr.splitlines() if ln.startswith(("Signature", "Identifier", "Format"))],
                "verify": sh("codesign", "--verify", "--deep", "--strict", APP).returncode,
                "size_mb": round(sum(p.lstat().st_size for p in APP.rglob("*") if p.is_file() and not p.is_symlink()) / 1e6, 1),
                "server_links": links, "manual": (APP / "Contents" / "Resources" / "docs" / "manual.md").is_file()}
    attempt("install", install)

    def first_window():
        t = time.time()
        sh("open", "-a", APP)
        said = {"server": bool(wait_for(lambda: listening(8765), 90)), "server_s": round(time.time() - t, 1)}
        time.sleep(8)
        said["windows"] = sh("osascript", "-e", 'tell application "System Events" to get name of every window of process "Idiograph"').stdout.strip()
        said["shot"] = shot(out, "mac-installed-first-window.png", "The installed app's first window, on a Mac",
                            "Idiograph in its own window and the home screen in it", "Idiograph")
        return said
    attempt("first_window", first_window)

    def mcp():
        msgs = "\n".join(json.dumps(m) for m in (
            {"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {"protocolVersion": "2025-06-18", "capabilities": {}, "clientInfo": {"name": "check", "version": "0"}}},
            {"jsonrpc": "2.0", "method": "notifications/initialized"},
            {"jsonrpc": "2.0", "id": 2, "method": "tools/list"})) + "\n"
        said = {}
        for label, exe in (("server_path", APP / "Contents" / "Resources" / "server" / "Idiograph"),
                           ("app_path", APP / "Contents" / "MacOS" / "Idiograph")):
            done = sh(exe, "mcp", input=msgs, timeout=60)
            lines = [json.loads(x) for x in done.stdout.splitlines() if x.strip().startswith("{")]
            said[label] = {"exit": done.returncode, "answers": len(lines),
                           "tools": next((len(m["result"].get("tools", [])) for m in lines if m.get("id") == 2 and "result" in m), None)}
        cli = sh(APP / "Contents" / "MacOS" / "Idiograph", "cli", "--help", timeout=60)
        said["cli_help"] = {"exit": cli.returncode, "first": cli.stdout.strip().splitlines()[:1]}
        return said
    attempt("mcp_and_cli", mcp)

    def quit_():
        req = urllib.request.Request("http://127.0.0.1:8765/api/server", data=b'{"op":"quit"}', method="POST",
                                     headers={"Host": "127.0.0.1:8765", "Content-Type": "application/json"})
        try:
            answer = urllib.request.build_opener(urllib.request.ProxyHandler({})).open(req, timeout=10).read().decode()[:200]
        except OSError as exc:
            answer = str(exc)
        gone = wait_for(lambda: not listening(8765) and not sh("pgrep", "-f", str(APP)).stdout.strip(), 40)
        return {"answer": answer, "gone": bool(gone), "left": sh("pgrep", "-fl", str(APP)).stdout.strip()[:300]}
    attempt("quit", quit_)
    return 0


if __name__ == "__main__":
    sys.exit(main())
