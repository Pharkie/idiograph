#!/usr/bin/env python3
"""A start that fails, its dialog taken from the screen by its own frame alone (18 October 2026, the sixth
Tauri build), on GitHub's Windows machine. `drive_windows_two.py` takes the fifth build's dialog with it,
and `.github/workflows/tauri.yml` the build before the fifth's, installed from that run's own installer, so
the screenshot check sees the two side by side, the log's last lines and the plain words that took their
place.

    python packaging/tauri/drive_failed_start.py --setup <an Idiograph-Setup.exe> --out <folder>
    python packaging/tauri/drive_failed_start.py --exe <an installed window's .exe> --out <folder>

Every window on the screen is minimised first, since the fifth build's picture showed the machine's own
console behind the dialog. The window is started with a switch its server does not take, so the server
ends before it answers and the window says so. The dialog's words are read, its frame alone taken from the
screen, and it is closed as its close button closes it. Every result goes in `results.json`, and nothing
reaches anything but this machine.
"""
from __future__ import annotations

import argparse
import ctypes
import json
import os
import subprocess
import sys
import time
from pathlib import Path

RESULTS: dict = {}

# every window on the screen minimised, as the taskbar's corner does it
MINIMISE = r"""
(New-Object -ComObject Shell.Application).MinimizeAll()
"minimised"
"""

# a part of the screen, x y w h, saved as a PNG
PART = r"""
param([string]$path, [int]$x, [int]$y, [int]$w, [int]$h)
Add-Type -AssemblyName System.Drawing
$bmp = New-Object System.Drawing.Bitmap $w, $h
$g = [System.Drawing.Graphics]::FromImage($bmp)
$g.CopyFromScreen($x, $y, 0, 0, (New-Object System.Drawing.Size $w, $h))
$bmp.Save($path, [System.Drawing.Imaging.ImageFormat]::Png)
"$w by $h at $x,$y"
"""


def powershell(script: str, *args: str, out: Path, timeout: float = 60) -> str:
    path = out / f"ps-{abs(hash(script)) % 100000}.ps1"
    path.write_text(script, encoding="utf-8")
    done = subprocess.run(["powershell.exe", "-NoProfile", "-STA", "-ExecutionPolicy", "Bypass", "-File", str(path), *args],
                          capture_output=True, text=True, timeout=timeout)
    return (done.stdout + done.stderr).strip()[-800:]


def user32():
    from ctypes import wintypes
    u = ctypes.WinDLL("user32", use_last_error=True)
    proc = ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)
    u.EnumWindows.argtypes = [proc, wintypes.LPARAM]
    u.EnumChildWindows.argtypes = [wintypes.HWND, proc, wintypes.LPARAM]
    u.GetWindowTextW.argtypes = [wintypes.HWND, wintypes.LPWSTR, ctypes.c_int]
    u.GetClassNameW.argtypes = [wintypes.HWND, wintypes.LPWSTR, ctypes.c_int]
    u.IsWindowVisible.argtypes = [wintypes.HWND]
    u.GetWindowThreadProcessId.argtypes = [wintypes.HWND, ctypes.POINTER(wintypes.DWORD)]
    u.PostMessageW.argtypes = [wintypes.HWND, wintypes.UINT, wintypes.WPARAM, wintypes.LPARAM]
    return u, proc


def text_of(u, hwnd) -> str:
    buf = ctypes.create_unicode_buffer(1024)
    u.GetWindowTextW(hwnd, buf, 1024)
    return buf.value


def dialogs(u, proc, pid: int) -> list:
    """The visible dialogs, Windows's own class #32770, of one process."""
    from ctypes import wintypes
    found = []

    def each(hwnd, _):
        owner = wintypes.DWORD()
        u.GetWindowThreadProcessId(hwnd, ctypes.byref(owner))
        name = ctypes.create_unicode_buffer(64)
        u.GetClassNameW(hwnd, name, 64)
        if owner.value == pid and name.value == "#32770" and u.IsWindowVisible(hwnd):
            found.append(hwnd)
        return True
    u.EnumWindows(proc(each), 0)
    return found


def words(u, proc, hwnd) -> list[str]:
    """The dialog's title, then the words of each of its visible parts, the message and the button."""
    found = [text_of(u, hwnd)]

    def each(child, _):
        if u.IsWindowVisible(child) and text_of(u, child).strip():
            found.append(text_of(u, child).strip())
        return True
    u.EnumChildWindows(hwnd, proc(each), 0)
    return found


def frame(hwnd) -> tuple[int, int, int, int]:
    """The window's frame as the screen draws it, its shadow left out (DWMWA_EXTENDED_FRAME_BOUNDS)."""
    from ctypes import wintypes
    r = wintypes.RECT()
    ctypes.WinDLL("dwmapi").DwmGetWindowAttribute(wintypes.HWND(hwnd), 9, ctypes.byref(r), ctypes.sizeof(r))
    return r.left, r.top, r.right - r.left, r.bottom - r.top


def failed_start(exe: Path, env: dict, out: Path, png: Path, log: Path) -> dict:
    """`exe` started with `env`, whose IDIOGRAPH_ARGS the server does not take, every other window
    minimised first, and the dialog that says the start failed read and taken by its frame alone."""
    u, proc = user32()
    said = {"minimised": powershell(MINIMISE, out=out)}
    time.sleep(1.5)
    with open(log, "w", encoding="utf-8") as held:
        child = subprocess.Popen([str(exe)], env=env, stdout=held, stderr=subprocess.STDOUT)
        t = time.time()
        shown = []
        while time.time() - t < 60 and not shown and child.poll() is None:
            shown = dialogs(u, proc, child.pid)
            if not shown:
                time.sleep(0.5)
        said["dialog_s"] = round(time.time() - t, 1)
        if shown:
            time.sleep(1)
            hwnd = shown[0]
            said["words"] = words(u, proc, hwnd)
            said["frame"] = frame(hwnd)
            x, y, w, h = said["frame"]
            said["shot"] = powershell(PART, str(png), str(x), str(y), str(w), str(h), out=out)
            u.PostMessageW(hwnd, 0x0010, 0, 0)  # WM_CLOSE, as its close button sends it
        else:
            said["words"] = "no dialog"
        try:
            said["exit"] = child.wait(timeout=30)
        except subprocess.TimeoutExpired:
            subprocess.run(["taskkill", "/F", "/T", "/PID", str(child.pid)], capture_output=True)
            said["exit"] = "still running, ended"
    said["output"] = log.read_text(encoding="utf-8", errors="replace")[-700:]
    return said


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--setup", help="an installer, run quietly first, whose app is then started")
    ap.add_argument("--exe", help="an installed window's .exe")
    ap.add_argument("--title", default="Idiograph", help="the app's name, its folder's and its .exe's")
    ap.add_argument("--shot", default="win-failed-start-before.png")
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    out = Path(a.out).resolve()
    out.mkdir(parents=True, exist_ok=True)
    results = out / "results.json"

    def note(key, value):
        RESULTS[key] = value
        print(f"{key}: {json.dumps(value, default=str)[:1500]}", flush=True)
        results.write_text(json.dumps(RESULTS, indent=2, default=str), encoding="utf-8")

    exe = Path(a.exe).resolve() if a.exe else Path(os.environ["LOCALAPPDATA"]) / a.title / f"{a.title}.exe"
    if a.setup:
        # by its whole path, since Tauri's installer reads a word of its command line starting /P as its
        # passive switch (the fifth build's first run)
        done = subprocess.run([str(Path(a.setup).resolve()), "/S"], capture_output=True, timeout=300)
        time.sleep(3)
        note("installed", {"exit": done.returncode, "exe": exe.is_file()})
    if not exe.is_file():
        note("stopped", f"no {exe}")
        return 1
    env = dict(os.environ, IDIOGRAPH_ARGS="--no-such-switch")
    note("failed_start", failed_start(exe, env, out, out / a.shot, out / "failed-start.log"))
    return 0


if __name__ == "__main__":
    sys.exit(main())
