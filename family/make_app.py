#!/usr/bin/env python3
"""Build Idiograph.app, the Mac launcher, at the root of the app's folder.

    python3 family/make_app.py            # from the app's folder, build or rebuild the bundle in place
    python3 family/make_app.py --desktop  # and put a symlink to it on the Desktop

The bundle is three files: the Info.plist, the launcher script (LAUNCHER below, which is the only
place to change it) and the icon. The launcher starts the server in the background and keeps its
log and pid file in ~/Library/Logs/Idiograph, because a script launched from Finder may not write
a file in iCloud Drive that it did not make. The icon is drawn here at 1024 px with the standard library,
scaled by sips into an iconset, its sizes up to 32 drawn from the 16 px drawing, and packed by
iconutil, so no image lives in the repo but the icns. The server draws the page's 32 px favicon from
the same drawing.
Standard library only, so it runs on any Python 3 on the Mac.
"""
from __future__ import annotations

import argparse
import math
import os
import plistlib
import shutil
import struct
import subprocess
import sys
import tempfile
import zlib
from pathlib import Path

# run as a tool, `python3 family/make_app.py`, the root goes on the path first, for boot
if __name__ == "__main__":
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import boot  # noqa: E402

boot.setup()
APP_NAME = "Idiograph.app"
BUNDLE = boot.ROOT / APP_NAME

INFO = {
    "CFBundleName": "Idiograph",
    "CFBundleDisplayName": "Idiograph",
    "CFBundleIdentifier": "uk.co.adamknowles.idiograph",
    "CFBundleExecutable": "Idiograph",
    "CFBundleIconFile": "Idiograph",
    "CFBundlePackageType": "APPL",
    "CFBundleInfoDictionaryVersion": "6.0",
    "CFBundleVersion": "1.0",
    "CFBundleShortVersionString": "1.0",
    "LSMinimumSystemVersion": "12.0",
    "LSUIElement": False,
}

# The executable inside the bundle. Bash 3.2, the one macOS ships, so no mapfile and every array
# expansion guarded for `set -u`.
LAUNCHER = r"""#!/bin/bash
# Idiograph, the launcher inside Idiograph.app. make_app.py writes this file, so change it there.
#
# Double-click with nothing on the port: the server starts in the background and opens the browser
# itself. Double-click while it runs: a dialog offers Stop, Restart and Open. Stop and Restart only
# ever signal the process that listens on the port, and only when that process is Idiograph's
# server.
#
# macOS lets a script launched from Finder read or change a file in iCloud Drive only when the
# script made that file. The server is not held to that, it runs as its own process, but this
# script is, so its log and pid file live in ~/Library/Logs/Idiograph, outside iCloud Drive.
#
# IDIOGRAPH_PORT (default 8765) and IDIOGRAPH_ARGS (extra server arguments, split on spaces,
# default none) are for testing, so a trial run never touches the port in daily use.
#
# Each launch writes a line to /tmp/idiograph-launch.log before anything else, so a launch that
# dies early still leaves its date there, and a second line with the outcome or the reason it
# stopped. The trap writes that second line for an exit nothing else explained.
echo "$(/bin/date '+%Y-%m-%d %H:%M:%S') port ${IDIOGRAPH_PORT:-8765}: launched" >> /tmp/idiograph-launch.log 2>/dev/null
TRACE="/tmp/idiograph-launch.log"
PORT="${IDIOGRAPH_PORT:-8765}"
TRACED=""
trace() {
  TRACED=1
  echo "$(/bin/date '+%Y-%m-%d %H:%M:%S') port $PORT: $1" >> "$TRACE" 2>/dev/null
}
trap 'rc=$?; [ -n "$TRACED" ] || trace "ended with no outcome, exit $rc"' EXIT
set -u
PATH="/usr/bin:/bin:/usr/sbin:/sbin:${PATH:-}"

# The Desktop shortcut is a symlink to the bundle, so resolve the script and then its folder with
# cd -P before counting upwards. Contents/MacOS sits three folders below the tool folder, so a
# renamed folder changes nothing here. The Python environment is the .venv beside the tool's own
# files, as the first run of a downloaded copy makes it, and the server starts from the tool folder.
# Else it is the one at the repo root, two folders above the tool folder, and the server starts
# from there, as it always has.
SELF="$0"
while [ -L "$SELF" ]; do
  LINK="$(readlink "$SELF")"
  case "$LINK" in
    /*) SELF="$LINK" ;;
    *) SELF="$(dirname "$SELF")/$LINK" ;;
  esac
done
MACOS="$(cd -P "$(dirname "$SELF")" && pwd)" &&
  CONTENTS="$(cd -P "$MACOS/.." && pwd)" &&
  TOOL="$(cd -P "$CONTENTS/../.." && pwd)" || {
  trace "not started, cannot find the bundle's folders"
  exit 1
}
if [ -x "$TOOL/.venv/bin/python3" ]; then
  ROOT="$TOOL"
  SERVER="server.py"
else
  ROOT="$(cd -P "$TOOL/../.." && pwd)" || {
    trace "not started, cannot find the bundle's folders"
    exit 1
  }
  SERVER="${TOOL#"$ROOT"/}/server.py"
fi

read -r -a EXTRA <<< "${IDIOGRAPH_ARGS:-}"
PY="$ROOT/.venv/bin/python3"
LOGDIR="$HOME/Library/Logs/Idiograph"
LOG="$LOGDIR/idiograph.log"
PIDFILE="$LOGDIR/idiograph-$PORT.pid"
ICON="$CONTENTS/Resources/Idiograph.icns"
URL="http://127.0.0.1:$PORT/"

# A dialog with one OK button, echoed to stderr for a run from a terminal.
alert() {
  echo "Idiograph: $1" >&2
  osascript -e 'on run argv' -e 'activate' \
    -e 'display dialog (item 1 of argv) with title "Idiograph" buttons {"OK"} default button "OK" with icon caution' \
    -e 'end run' "$1" >/dev/null 2>&1
}

notify() {
  echo "Idiograph: $1" >&2
  osascript -e 'on run argv' -e 'display notification (item 1 of argv) with title "Idiograph"' \
    -e 'end run' "$1" >/dev/null 2>&1
}

# The running dialog. Prints the button pressed, or nothing when the dialog is dismissed. The icon
# sits in iCloud Drive, so when it cannot be read the dialog shows the plain note icon.
ask() {
  osascript - "$ICON" 2>/dev/null <<'OSA'
on run argv
  activate
  set question to "Idiograph is running."
  set choices to {"Stop", "Restart", "Open"}
  try
    set reply to display dialog question with title "Idiograph" buttons choices default button "Open" with icon ((POSIX file (item 1 of argv)) as alias)
  on error number n
    if n is -128 then return ""
    set reply to display dialog question with title "Idiograph" buttons choices default button "Open" with icon note
  end try
  return button returned of reply
end run
OSA
}

# The PIDs listening on the port, one a line, or nothing.
listeners() {
  lsof -nP -iTCP:"$PORT" -sTCP:LISTEN -t 2>/dev/null
}

# True when every listener is Idiograph's server, so Stop never signals another program.
ours() {
  local pid
  for pid in $(listeners); do
    ps -p "$pid" -o command= 2>/dev/null | grep -q 'server\.py' || return 1
  done
  return 0
}

wait_closed() {
  local deadline=$((SECONDS + 5))
  while [ -n "$(listeners)" ]; do
    [ "$SECONDS" -ge "$deadline" ] && return 1
    sleep 0.2
  done
  return 0
}

# A background server ignores Control-C, so TERM, and KILL only for whatever still listens five
# seconds later. Every workbook save is a temporary file renamed into place, so neither can leave
# half a workbook.
stop_server() {
  local sig pid
  for sig in TERM KILL; do
    for pid in $(listeners); do kill -"$sig" "$pid" 2>/dev/null; done
    if wait_closed; then
      rm -f "$PIDFILE"
      return 0
    fi
  done
  return 1
}

# $1 is the outcome word for the trace, started or restarted.
start_server() {
  local child pid deadline
  if [ ! -x "$PY" ]; then
    trace "not $1, no .venv/bin/python3"
    alert "Idiograph has no Python environment yet.

Double-click run.command beside Idiograph.app once, which sets one up, and then open Idiograph.app again."
    exit 1
  fi
  if ! mkdir -p "$LOGDIR" || ! : >> "$LOG"; then
    trace "not $1, cannot write the log"
    alert "Idiograph cannot write its log at $LOG."
    exit 1
  fi
  cd "$ROOT" || {
    trace "not $1, cannot enter the folder it starts from"
    exit 1
  }
  printf '\n=== %s, starting on port %s\n' "$(date '+%Y-%m-%d %H:%M:%S')" "$PORT" >> "$LOG"
  PYTHONUNBUFFERED=1 nohup "$PY" "$SERVER" --port "$PORT" ${EXTRA[@]+"${EXTRA[@]}"} \
    >> "$LOG" 2>&1 < /dev/null &
  child=$!
  echo "$child" > "$PIDFILE"
  deadline=$((SECONDS + 10))
  while [ "$SECONDS" -lt "$deadline" ]; do
    pid="$(listeners | head -n 1)"
    if [ -n "$pid" ]; then
      echo "$pid" > "$PIDFILE"
      trace "$1, pid $pid"
      return 0
    fi
    kill -0 "$child" 2>/dev/null || break
    sleep 0.25
  done
  kill -0 "$child" 2>/dev/null || rm -f "$PIDFILE"
  trace "not $1, nothing listening after ten seconds"
  alert "Idiograph did not start on port $PORT. The last lines of $LOG:

$(tail -n 12 "$LOG")"
  exit 1
}

case "$PORT" in
  ''|*[!0-9]*) trace "not a port number"; alert "IDIOGRAPH_PORT is not a port number: $PORT"; exit 1 ;;
esac

if [ -z "$(listeners)" ]; then
  start_server started
  exit 0
fi

if ! ours; then
  trace "another program is listening"
  alert "Another program is listening on port $PORT, so Idiograph cannot start there."
  exit 1
fi

CHOICE="$(ask)"
case "$CHOICE" in
  Open)
    trace "running, opened the browser"
    open "$URL"
    ;;
  Stop)
    if stop_server; then
      trace "running, stopped"
      notify "Idiograph stopped."
    else
      trace "running, did not stop"
      alert "Idiograph did not stop. Something still listens on port $PORT."
      exit 1
    fi
    ;;
  Restart)
    if stop_server; then
      start_server restarted
    else
      trace "running, did not stop, so not restarted"
      alert "Idiograph did not stop, so it did not restart. Something still listens on port $PORT."
      exit 1
    fi
    ;;
  *)
    trace "running, dialog dismissed"
    ;;
esac
exit 0
"""

# ── The icon ────────────────────────────────────────────────────────────────────────────────────
# Idiograph's mark (15 October), the participant's experience, an orange dot, held between the two
# square brackets where the researcher's hand enters a quotation, in the colours of the design
# board's light tile: the paper, the ink and the crux orange.
PAPER = (0xF6, 0xF1, 0xE8)
CRUX = (0xC2, 0x5E, 0x0B)
INK = (0x1F, 0x1B, 0x16)

# Rounded rectangles on a 1024 grid, painted in order: (left, top, right, bottom), corner radius,
# colour. The tile follows the Mac icon grid (824 square, 100 in from each side), and the mark is
# drawn on its 24 grid at 26 to the unit from 200 in, each bracket a stroke of two units as three
# rectangles with square corners, overlapping at the corners so no seam shows, and the dot a
# rectangle whose radius is half its side.
SHAPES = [
    ((100, 100, 924, 924), 185, PAPER),
    ((291, 265, 343, 759), 0, INK),
    ((291, 265, 447, 317), 0, INK),
    ((291, 707, 447, 759), 0, INK),
    ((681, 265, 733, 759), 0, INK),
    ((577, 265, 733, 317), 0, INK),
    ((577, 707, 733, 759), 0, INK),
    ((441.8, 441.8, 582.2, 582.2), 70.2, CRUX),
]

# The mark drawn for 16 pixels, which every size up to 32 takes, since the 1024 drawing scaled that
# far down blurs: the tile to the edge, every edge on a whole pixel, two-pixel strokes, the feet
# three pixels long and the dot four across. Given on the 16 grid and painted at 64 to the unit.
SHAPES_16 = [(tuple(v * 64 for v in box), radius * 64, rgb) for box, radius, rgb in [
    ((0, 0, 16, 16), 3.5, PAPER),
    ((3, 3, 5, 13), 0, INK),
    ((3, 3, 6, 5), 0, INK),
    ((3, 11, 6, 13), 0, INK),
    ((11, 3, 13, 13), 0, INK),
    ((10, 3, 13, 5), 0, INK),
    ((10, 11, 13, 13), 0, INK),
    ((6, 6, 10, 10), 2, CRUX),
]]
SMALL = 32

# Sift's and Trace's icons (20 October, the three-app split's build 6, drawing 4 of the plan): the same
# paper tile, the mark in ink and one point in the crux orange. Sift's mark is a sieve, its two halves
# with a gap between, an ink record held above and the orange record falling through. Trace's is a
# page's corner, a small bracket inside it and the orange citation beside the bracket. Each is drawn as
# Idiograph's is, the 24 grid at 26 to the unit from 200 in, every stroke two units with square ends.
SIFT_SHAPES = [
    ((100, 100, 924, 924), 185, PAPER),
    ((265, 304, 317, 629), 0, INK),
    ((265, 577, 473, 629), 0, INK),
    ((551, 577, 759, 629), 0, INK),
    ((707, 304, 759, 629), 0, INK),
    ((369, 447, 452.2, 530.2), 0, INK),
    ((470.4, 688.8, 553.6, 772), 0, CRUX),
]
SIFT_SHAPES_16 = [(tuple(v * 64 for v in box), radius * 64, rgb) for box, radius, rgb in [
    ((0, 0, 16, 16), 3.5, PAPER),
    ((3, 4, 5, 11), 0, INK),
    ((3, 9, 7, 11), 0, INK),
    ((9, 9, 13, 11), 0, INK),
    ((11, 4, 13, 11), 0, INK),
    ((6, 6, 8, 8), 0, INK),
    ((7, 12, 9, 14), 0, CRUX),
]]
TRACE_SHAPES = [
    ((100, 100, 924, 924), 185, PAPER),
    ((252, 707, 759, 759), 0, INK),
    ((707, 278, 759, 759), 0, INK),
    ((655, 278, 759, 330), 0, INK),
    ((434, 278, 538, 330), 0, INK),
    ((434, 278, 486, 564), 0, INK),
    ((434, 512, 538, 564), 0, INK),
    ((549.7, 374.2, 643.3, 467.8), 0, CRUX),
]
TRACE_SHAPES_16 = [(tuple(v * 64 for v in box), radius * 64, rgb) for box, radius, rgb in [
    ((0, 0, 16, 16), 3.5, PAPER),
    ((2, 12, 14, 14), 0, INK),
    ((12, 2, 14, 14), 0, INK),
    ((11, 2, 14, 4), 0, INK),
    ((5, 2, 8, 4), 0, INK),
    ((5, 2, 7, 10), 0, INK),
    ((5, 8, 8, 10), 0, INK),
    ((9, 5, 11, 7), 0, CRUX),
]]
# each app's drawing, the large and the one for 16 pixels
DRAWINGS = {"idiograph": (SHAPES, SHAPES_16), "sift": (SIFT_SHAPES, SIFT_SHAPES_16),
            "trace": (TRACE_SHAPES, TRACE_SHAPES_16)}


def _over(buf: bytearray, i: int, rgb: tuple[int, int, int], a: float) -> None:
    """Composite one colour at coverage `a` over the straight-alpha pixel at byte offset `i`."""
    da = buf[i + 3] / 255
    oa = a + da * (1 - a)
    for k in range(3):
        buf[i + k] = round((rgb[k] * a + buf[i + k] * da * (1 - a)) / oa)
    buf[i + 3] = round(oa * 255)


def _paint(buf: bytearray, size: int, box, radius: float, rgb) -> None:
    """Paint one rounded rectangle, given on the 1024 grid, onto a `size` square RGBA buffer.

    Coverage is a distance test from each pixel centre to the rounded edge, with a one-pixel soft
    edge. For a fixed row the distance only grows away from the centre, so the fully covered pixels
    form one span, which is filled as a slice, and only the pixels either side of it are tested.
    """
    s = size / 1024
    x0, y0, x1, y1 = (v * s for v in box)
    cx, cy, hx, hy = (x0 + x1) / 2, (y0 + y1) / 2, (x1 - x0) / 2, (y1 - y0) / 2
    r = min(radius * s, hx, hy)
    solid = bytes((*rgb, 255))
    lo, hi = max(0, math.floor(x0) - 1), min(size, math.ceil(x1) + 1)

    def cover(px: int, qy: float) -> float:
        qx = abs(px + 0.5 - cx) - hx + r
        d = math.hypot(qx, qy) - r if qx > 0 and qy > 0 else max(qx, qy) - r
        return min(1.0, max(0.0, 0.5 - d))

    for py in range(max(0, math.floor(y0) - 1), min(size, math.ceil(y1) + 1)):
        qy = abs(py + 0.5 - cy) - hy + r
        base = py * size * 4
        left = lo
        while left < hi and cover(left, qy) < 1:
            left += 1
        right = hi
        while right > left and cover(right - 1, qy) < 1:
            right -= 1
        for px in [*range(lo, left), *range(right, hi)]:
            a = cover(px, qy)
            if a > 0:
                _over(buf, base + 4 * px, rgb, a)
        if right > left:
            buf[base + 4 * left:base + 4 * right] = solid * (right - left)


def draw_icon(size: int = 1024, app: str = "idiograph") -> bytearray:
    """The icon of `app`, Idiograph's by default, Sift's or Trace's, as straight-alpha RGBA bytes,
    `size` pixels square, transparent outside the tile, from the 16 pixel drawing up to 32 pixels and
    the 1024 drawing above."""
    large, small = DRAWINGS[app]
    buf = bytearray(size * size * 4)
    for box, radius, rgb in small if size <= SMALL else large:
        _paint(buf, size, box, radius, rgb)
    return buf


def png_bytes(size: int, rgba: bytes) -> bytes:
    """A PNG of a square RGBA image, written by hand: signature, IHDR, one IDAT, IEND."""
    stride = size * 4
    raw = b"".join(b"\x00" + bytes(rgba[y * stride:(y + 1) * stride]) for y in range(size))

    def chunk(tag: bytes, data: bytes) -> bytes:
        return (struct.pack(">I", len(data)) + tag + data
                + struct.pack(">I", zlib.crc32(tag + data) & 0xFFFFFFFF))

    header = struct.pack(">IIBBBBB", size, size, 8, 6, 0, 0, 0)
    return (b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", header)
            + chunk(b"IDAT", zlib.compress(raw, 9)) + chunk(b"IEND", b""))


# The names iconutil expects in an iconset, and the pixel size of each.
ICONSET = [
    ("icon_16x16.png", 16), ("icon_16x16@2x.png", 32),
    ("icon_32x32.png", 32), ("icon_32x32@2x.png", 64),
    ("icon_128x128.png", 128), ("icon_128x128@2x.png", 256),
    ("icon_256x256.png", 256), ("icon_256x256@2x.png", 512),
    ("icon_512x512.png", 512), ("icon_512x512@2x.png", 1024),
]


def build_icns(dest: Path, app: str = "idiograph") -> None:
    """Draw the 1024 master, scale the iconset's larger sizes from it with sips, draw the sizes up to
    32 from the 16 pixel drawing, and pack it with iconutil.

    Everything but the icns stays in a temporary folder, so the PNGs never reach the repo.
    """
    with tempfile.TemporaryDirectory(prefix="idiograph-icon-") as tmp:
        master = Path(tmp) / "Idiograph-1024.png"
        master.write_bytes(png_bytes(1024, draw_icon(1024, app)))
        iconset = Path(tmp) / "Idiograph.iconset"
        iconset.mkdir()
        for name, px in ICONSET:
            out = iconset / name
            if px == 1024:
                shutil.copyfile(master, out)
            elif px <= SMALL:
                out.write_bytes(png_bytes(px, draw_icon(px, app)))
            else:
                subprocess.run(["sips", "-z", str(px), str(px), str(master), "--out", str(out)],
                               check=True, capture_output=True)
        subprocess.run(["iconutil", "-c", "icns", str(iconset), "-o", str(dest)],
                       check=True, capture_output=True)


# ── The bundle ──────────────────────────────────────────────────────────────────────────────────
BUNDLE_FILES = ("Contents/Info.plist", "Contents/MacOS/Idiograph", "Contents/Resources/Idiograph.icns")


def build_app(bundle: Path = BUNDLE) -> Path:
    """Write the bundle, or rewrite it in place, and drop anything an older build left inside it."""
    contents = bundle / "Contents"
    (contents / "MacOS").mkdir(parents=True, exist_ok=True)
    (contents / "Resources").mkdir(parents=True, exist_ok=True)
    (contents / "Info.plist").write_bytes(plistlib.dumps(INFO, fmt=plistlib.FMT_XML))
    script = contents / "MacOS" / "Idiograph"
    script.write_text(LAUNCHER, encoding="utf-8", newline="\n")
    script.chmod(0o755)
    build_icns(contents / "Resources" / "Idiograph.icns")

    keep = {bundle / f for f in BUNDLE_FILES}
    keep_dirs = {contents, contents / "MacOS", contents / "Resources"}
    for path in sorted(bundle.rglob("*"), reverse=True):
        if path.is_symlink() or path.is_file():
            if path not in keep:
                path.unlink()
        elif path.is_dir() and path not in keep_dirs and not any(path.iterdir()):
            path.rmdir()
    # A fresh date on the bundle is what tells Finder and the Dock to look at the icon again.
    os.utime(bundle)
    return bundle


def link_desktop(bundle: Path = BUNDLE, desktop: Path | None = None) -> Path:
    """Put `Idiograph.app` on the Desktop as a symlink to the bundle.

    An existing symlink of that name is replaced. Anything else of that name is left alone and
    FileExistsError is raised, because it might be a real app or a folder with work in it.
    """
    desktop = desktop if desktop is not None else Path.home() / "Desktop"
    link = desktop / APP_NAME
    if link.is_symlink():
        link.unlink()
    elif link.exists():
        raise FileExistsError(f"{link} exists and is not a symlink, so it was left as it is.")
    link.symlink_to(bundle.resolve())
    return link


def main() -> int:
    ap = argparse.ArgumentParser(description="Build Idiograph.app, the Mac launcher.")
    ap.add_argument("--desktop", action="store_true",
                    help="also put a symlink to the bundle on the Desktop")
    args = ap.parse_args()
    bundle = build_app()
    print(f"Built {bundle}")
    if args.desktop:
        try:
            print(f"Desktop shortcut: {link_desktop(bundle)}")
        except FileExistsError as exc:
            print(exc, file=sys.stderr)
            return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
