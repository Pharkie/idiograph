from __future__ import annotations

import os
import re
from pathlib import Path

import make_app

from . import support
from .support import check, skip


def test_launcher(scratch):
    print("\n32. The Mac launcher: the bundle, its script, its icon and the Desktop shortcut")
    if os.name == "nt":
        # bash, symlinks and the Mac's own tools, none of them on Windows (14 October)
        return skip("32: the Mac launcher", "a Mac's bundle, checked on a Mac")
    import plistlib
    import struct
    import subprocess
    import zlib

    bundle = support.source("Idiograph.app")
    plist_path = bundle / "Contents" / "Info.plist"
    script_path = bundle / "Contents" / "MacOS" / "Idiograph"
    icns_path = bundle / "Contents" / "Resources" / "Idiograph.icns"
    files = [p for p in bundle.rglob("*") if p.is_file()]
    check("the bundle holds its three files and nothing else",
          all(p.is_file() for p in (plist_path, script_path, icns_path)) and len(files) == 3,
          ", ".join(sorted(p.relative_to(bundle).as_posix() for p in files)))
    info = plistlib.loads(plist_path.read_bytes()) if plist_path.is_file() else {}
    want = {"CFBundleName": "Idiograph", "CFBundleIdentifier": "uk.co.adamknowles.idiograph",
            "CFBundleExecutable": "Idiograph", "CFBundleIconFile": "Idiograph",
            "LSMinimumSystemVersion": "12.0", "CFBundleVersion": "1.0",
            "CFBundleShortVersionString": "1.0"}
    check("the plist names the app, its executable, its icon and its versions",
          all(info.get(k) == v for k, v in want.items()) and info.get("LSUIElement") is False
          and info == make_app.INFO, f"{len(info)} keys")
    check("the launcher in the bundle is executable and is the one make_app.py writes",
          script_path.is_file() and os.access(script_path, os.X_OK)
          and script_path.read_text(encoding="utf-8") == make_app.LAUNCHER,
          "a stale bundle is rebuilt with make_app.py")
    check("the icon is an icns", icns_path.is_file() and icns_path.read_bytes()[:4] == b"icns")

    script = make_app.LAUNCHER
    syntax = subprocess.run(["/bin/bash", "-n", "-c", script], capture_output=True, text=True, encoding="utf-8")
    check("the launcher is valid bash for the bash macOS ships", syntax.returncode == 0,
          syntax.stderr.strip())

    # The same lines, run from a copy of the bundle reached through a symlink, in a tool folder
    # renamed and with a space in its path, prove the resolution rather than only its spelling.
    fake_trace = scratch / "launcher trace.log"
    head = script.split('\nTRACE=', 1)[1].split('LOGDIR=', 1)[0]
    head = head.replace('"/tmp/idiograph-launch.log"', '"' + str(fake_trace) + '"', 1)
    probe = ('TRACE=' + head
             + 'echo "$ROOT"\necho "$PORT"\necho "${#EXTRA[@]}"\necho "$SERVER"\n')
    fake_root = scratch / "launcher root" / "Repo Copy"
    macos = fake_root / "Tools" / "renamed tool" / "Idiograph.app" / "Contents" / "MacOS"
    macos.mkdir(parents=True, exist_ok=True)
    fake_script = macos / "Idiograph"
    fake_script.write_text("#!/bin/bash\n" + probe, encoding="utf-8")
    fake_script.chmod(0o755)
    desk = scratch / "launcher desk"
    desk.mkdir(exist_ok=True)
    link = desk / "Idiograph.app"
    if link.is_symlink():
        link.unlink()
    link.symlink_to(macos.parent.parent)
    env = {k: v for k, v in os.environ.items() if not k.startswith("IDIOGRAPH_")}
    plain = subprocess.run([str(link / "Contents" / "MacOS" / "Idiograph")], capture_output=True,
                           text=True, encoding="utf-8", env=env)
    over = subprocess.run([str(link / "Contents" / "MacOS" / "Idiograph")], capture_output=True,
                          text=True, encoding="utf-8",
                          env={**env, "IDIOGRAPH_PORT": "8770",
                               "IDIOGRAPH_ARGS": "--no-browser --root /tmp/scratch-root"})
    got = plain.stdout.splitlines()
    check("through a Desktop symlink the root is the real folder two above the tool",
          got[:1] == [str(fake_root.resolve())] and got[3:4] == ["Tools/renamed tool/server.py"],
          " | ".join(got) or plain.stderr.strip())
    check("with no overrides the port is 8765 and there are no extra arguments",
          got[1:3] == ["8765", "0"], " | ".join(got[1:3]))
    check("IDIOGRAPH_PORT and IDIOGRAPH_ARGS reach the launcher",
          over.stdout.splitlines()[1:3] == ["8770", "3"], " | ".join(over.stdout.splitlines()))

    check("a start runs detached, and its log and pid file sit outside iCloud Drive",
          'PYTHONUNBUFFERED=1 nohup "$PY" "$SERVER"' in script
          and '>> "$LOG" 2>&1 < /dev/null &' in script
          and 'LOGDIR="$HOME/Library/Logs/Idiograph"' in script
          and 'LOG="$LOGDIR/idiograph.log"' in script
          and 'PIDFILE="$LOGDIR/idiograph-$PORT.pid"' in script
          and 'deadline=$((SECONDS + 10))' in script
          and '$(tail -n 12 "$LOG")' in script)
    check("every exit leaves its outcome or its reason, with dates and no paths",
          'TRACE="/tmp/idiograph-launch.log"' in script
          and "echo \"$(/bin/date '+%Y-%m-%d %H:%M:%S') port $PORT: $1\" >> \"$TRACE\"" in script
          and """trap 'rc=$?; [ -n "$TRACED" ] || trace "ended with no outcome, exit $rc"' EXIT"""
          in script
          and not re.search(r"\|\|\s*exit 1\s*$", script, re.M)
          and all(re.search(r"\btrace\b", chunk) for chunk in script.split("exit 1")[:-1]
                  if chunk.rstrip().endswith((";", "\n", "}")))
          and not [line for line in script.splitlines()
                   if line.strip().startswith("trace ")
                   and re.search(r"\$(ROOT|TOOL|LOG|PY|0|ICON|SERVER|EXTRA)\b", line)])
    written = fake_trace.read_text(encoding="utf-8") if fake_trace.exists() else ""
    check("the trap writes a line for an exit nothing else explained",
          written.count("ended with no outcome, exit 0") == 2
          and "port 8770: ended with no outcome" in written, written.strip().replace("\n", " | "))
    check("a second double-click offers Stop, Restart and Open, with Open the default",
          'set question to "Idiograph is running."' in script
          and 'set choices to {"Stop", "Restart", "Open"}' in script
          and script.count('with title "Idiograph" buttons choices default button "Open"') == 2
          and 'open "$URL"' in script and 'notify "Idiograph stopped."' in script
          and "stop_server; then\n      start_server restarted" in script)
    kills = [line.strip() for line in script.splitlines()
             if re.search(r"\bkill\b", line) and not line.strip().startswith("#")]
    check("Stop signals only what listens on the port, and only when it is the server",
          'lsof -nP -iTCP:"$PORT" -sTCP:LISTEN -t' in script
          and "grep -q 'server\\.py' || return 1" in script
          and all(k.startswith('for pid in $(listeners); do kill -"$sig" "$pid"')
                  or k.startswith('kill -0 "$child"') for k in kills)
          and "pkill" not in script and "killall" not in script,
          f"{len(kills)} kill lines")

    rgba = make_app.draw_icon(64)
    png = make_app.png_bytes(64, rgba)
    ihdr = png[8:33]
    width, height, depth, colour = struct.unpack(">IIBB", ihdr[8:18])
    idat_len = struct.unpack(">I", png[33:37])[0]
    raw = zlib.decompress(png[41:41 + idat_len])
    check("the PNG writer writes a valid header for a 64 px render",
          png[:8] == b"\x89PNG\r\n\x1a\n" and ihdr[4:8] == b"IHDR"
          and (width, height, depth, colour) == (64, 64, 8, 6)
          and struct.unpack(">I", ihdr[21:25])[0] == zlib.crc32(ihdr[4:21]) & 0xFFFFFFFF
          and png.endswith(b"IEND\xaeB`\x82"),
          f"{width}x{height}, depth {depth}, colour type {colour}")
    check("the image data is one filter byte and 64 RGBA pixels a row",
          len(rgba) == 64 * 64 * 4 and len(raw) == 64 * (1 + 64 * 4)
          and all(raw[r * 257] == 0 for r in range(64)))

    real = scratch / "launcher desktop real"
    real.mkdir(exist_ok=True)
    blocker = real / "Idiograph.app"
    blocker.mkdir(exist_ok=True)
    (blocker / "keep.txt").write_text("not a symlink", encoding="utf-8")
    try:
        make_app.link_desktop(bundle, real)
        refused = False
    except FileExistsError:
        refused = True
    check("the Desktop step refuses anything that is not a symlink, and leaves it alone",
          refused and blocker.is_dir() and not blocker.is_symlink()
          and (blocker / "keep.txt").read_text(encoding="utf-8") == "not a symlink")
    links = scratch / "launcher desktop links"
    links.mkdir(exist_ok=True)
    first = make_app.link_desktop(bundle, links)
    stale = links / "Idiograph.app"
    stale.unlink()
    stale.symlink_to(scratch)
    second = make_app.link_desktop(bundle, links)
    check("it makes the symlink, and replaces an old symlink of that name",
          first == second and second.is_symlink()
          and Path(os.readlink(second)) == bundle.resolve())
