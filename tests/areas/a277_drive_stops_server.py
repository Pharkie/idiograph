"""Area 277: a drive of the Mac window stops the server it caused, however it ends (27 October 2026, drivemac).
`open` starts the window under launchd, never as the drive's child, and the window starts its server, so when a
window ended with no word of its own (a SIGTERM, before the window heard one) its server went on serving on 8795,
and with IDIOGRAPH_STAY_OPEN in a drive it never quit (macapp19 and macapp20, 23 October, each stopped it by hand).
`drive_mac.App` now notes the window and everything under it as they come, and `stop` ends what is left: at a
run's end, and through atexit and the drive's own signal handlers when the drive itself ends.

On a Mac alone, with a stand-in bundle in the scratch folder: a script that starts a long sleep under it, the
server's stand-in, and dies at a SIGTERM as the window did before it heard one."""
from __future__ import annotations

import os
import plistlib
import signal
import subprocess
import sys
import time
from pathlib import Path

from .support import check, skip

ROOT = Path(__file__).resolve().parents[2]

WINDOW = """#!/bin/bash
# the stand-in window: argv[0] its own path, as a real window's command line starts, then the server's
# stand-in under it, and a SIGTERM ends it at once, as one did the window before it heard one
if [ -z "$STANDIN_AGAIN" ]; then STANDIN_AGAIN=1 exec -a "$0" /bin/bash "$0" "$@"; fi
/bin/sleep "$IDIOGRAPH_STANDIN_SLEEP" &
echo "drive: stand-in started $!" >&2
wait
"""

DRIVE = """import sys, time
sys.path.insert(0, sys.argv[1])
import drive_mac as dm
from pathlib import Path
app = dm.App(Path(sys.argv[2]), {"IDIOGRAPH_STANDIN_SLEEP": sys.argv[3]}, Path(sys.argv[4]))
while not [c for c in app.mine.values() if c.startswith("/bin/sleep")]:
    time.sleep(0.2)
print("ready", flush=True)
time.sleep(600)
"""


def _bundle(scratch: Path, name: str) -> Path:
    bundle = scratch / f"{name}.app"
    macos = bundle / "Contents" / "MacOS"
    macos.mkdir(parents=True, exist_ok=True)
    (bundle / "Contents" / "Info.plist").write_bytes(plistlib.dumps({
        "CFBundleExecutable": name, "CFBundleIdentifier": f"uk.co.adamknowles.idiograph.check.{name.lower()}",
        "CFBundleName": name, "CFBundlePackageType": "APPL", "LSUIElement": True}))
    exe = macos / name
    exe.write_text(WINDOW, encoding="utf-8")
    exe.chmod(0o755)
    return bundle


def _running(word: str) -> list:
    done = subprocess.run(["pgrep", "-f", f"^/bin/sleep {word}$"], capture_output=True, text=True, encoding="utf-8")
    return [int(p) for p in done.stdout.split() if p.isdigit()]


def _gone(word: str, seconds: float = 10) -> bool:
    t0 = time.time()
    while _running(word) and time.time() - t0 < seconds:
        time.sleep(0.2)
    return not _running(word)


def test_drive_stops_server(scratch: Path):
    print("\n277. A drive of the Mac window stops the server it caused, however it ends: a window killed outside "
          "the drive, and the drive itself ended by a SIGTERM (27 October 2026)")
    if sys.platform != "darwin":
        skip("277: a drive stops its server", "the Mac window's drive runs on a Mac alone")
        return
    sys.path.insert(0, str(ROOT / "packaging" / "tauri"))
    import drive_mac as dm

    # one: the window killed from outside, its server left under launchd, and the run's end stops it
    word = str(70000 + os.getpid() % 9000)
    bundle = _bundle(scratch, "StandinOne")
    app = dm.App(bundle, {"IDIOGRAPH_STANDIN_SLEEP": word}, scratch / "one.log")
    t0 = time.time()
    while not _running(word) and time.time() - t0 < 20:
        time.sleep(0.2)
    server = _running(word)
    time.sleep(1)
    windows = [pid for pid, cmd in app.mine.items() if cmd.startswith(app.exe)]
    for pid in windows:
        os.kill(pid, signal.SIGKILL)
    time.sleep(1)
    orphaned = bool(_running(word))
    said = app.end(10)
    check("277: a window killed outside the drive leaves its server running, and the run's end stops it",
          bool(server) and bool(windows) and orphaned and _gone(word) and any("/bin/sleep" in c for c in said.get("left", [])),
          f"server {server}, windows {windows}, orphaned {orphaned}, {said}")
    for pid in _running(word):
        os.kill(pid, signal.SIGKILL)

    # two: the drive itself ended by a SIGTERM, its window and the window's server stopped as it goes
    word = str(80000 + os.getpid() % 9000)
    bundle = _bundle(scratch, "StandinTwo")
    script = scratch / "drive_standin.py"
    script.write_text(DRIVE, encoding="utf-8")
    drive = subprocess.Popen([sys.executable, "-I", str(script), str(ROOT / "packaging" / "tauri"), str(bundle), word,
                              str(scratch / "two.log")], stdout=subprocess.PIPE, text=True, encoding="utf-8")
    ready = drive.stdout.readline().strip() == "ready"
    server = _running(word)
    drive.send_signal(signal.SIGTERM)
    try:
        drive.wait(timeout=60)
    except subprocess.TimeoutExpired:
        drive.kill()
    exe = str(bundle / "Contents" / "MacOS")
    left = subprocess.run(["pgrep", "-f", exe], capture_output=True, text=True, encoding="utf-8").stdout.split()
    check("277: a drive ended by a SIGTERM stops its window and the window's server",
          ready and bool(server) and _gone(word) and not left, f"ready {ready}, server {server}, windows left {left}")
    for pid in _running(word) + [int(p) for p in left if p.isdigit()]:
        os.kill(pid, signal.SIGKILL)
