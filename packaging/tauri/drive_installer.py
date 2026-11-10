#!/usr/bin/env python3
"""The Windows installer as a tester gets it, checked on GitHub's Windows machine (17 October 2026, the third
Tauri build), run by `.github/workflows/tauri.yml`'s installer job.

    python packaging/tauri/drive_installer.py --inno <0.9.0's Idiograph-Setup.exe> --setup <Idiograph-Setup.exe> --out <folder>
    python packaging/tauri/drive_installer.py --older <a Setup> --newer <the next one's> --out <folder>

1. 0.9.0 installed by its own Inno Setup installer, quietly, as a tester had it, then its server started as
   its launcher starts it, so its data folder holds a settings file and the demo as a tester's would, and
   left running, as a tester who did not quit it leaves it. A note of the check's own goes in the data
   folder beside them.
2. The new installer run as a tester runs it, each page found by the heading it shows and taken from
   the screen with a heading saying what it shows and what to check: Welcome, the folder, the files in,
   and again with its details unfolded (the fifth build, 18 October), and again with the window widened
   until every line of the details shows whole, then put back as it was (the sixth build), Finish. Each
   page's Next pressed as its own button presses it. Open Idiograph left ticked, so Finish opens the app.
3. The installed app's first window taken from the screen.
4. What the install left: 0.9.0's uninstall entry, its folder and its Start menu entry gone, one Start
   menu entry, the new app's, the data folder as it was with the note among it, and both of the new
   app's processes, the window and the server. Then Setup run again for the same version, to the page
   that asks what to do, and ended there (the fifth build).
5. The app closed by its close button, then its uninstaller run as a tester runs it, its first page
   taken: the app's files gone, the data folder and the log as they were.

With `--older` and `--newer`, the update job's (the fifth build): the pages an older version's Setup and
a newer one's show where the other is installed, each in its plain words, each Setup ended there.

Every result goes in `results.json` beside the shots, and nothing reaches anything but this machine.
"""
from __future__ import annotations

import argparse
import ctypes
import json
import os
import subprocess
import sys
import time
import traceback
from pathlib import Path

RESULTS: dict = {}
SAVED: list = []
# 0.9.0's server, left running as a tester might leave it
RUNNING: list = []
INNO_KEY = r"Software\Microsoft\Windows\CurrentVersion\Uninstall\{C7E7DA37-1EC0-4980-B693-28D0962DA65C}_is1"
NSIS_KEY = r"Software\Microsoft\Windows\CurrentVersion\Uninstall\Idiograph"

# the screen taken with a heading above it: what the picture shows and what to check in it
SHOT = r"""
param([string]$path, [string]$head, [string]$check)
Add-Type -AssemblyName System.Windows.Forms, System.Drawing
$b = [System.Windows.Forms.Screen]::PrimaryScreen.Bounds
$band = 92
$bmp = New-Object System.Drawing.Bitmap $b.Width, ($b.Height + $band)
$g = [System.Drawing.Graphics]::FromImage($bmp)
$g.Clear([System.Drawing.Color]::FromArgb(255, 251, 247, 239))
$g.TextRenderingHint = [System.Drawing.Text.TextRenderingHint]::AntiAliasGridFit
$big = New-Object System.Drawing.Font("Segoe UI", 24, [System.Drawing.FontStyle]::Bold, [System.Drawing.GraphicsUnit]::Pixel)
$small = New-Object System.Drawing.Font("Segoe UI", 19, [System.Drawing.FontStyle]::Regular, [System.Drawing.GraphicsUnit]::Pixel)
$ink = New-Object System.Drawing.SolidBrush ([System.Drawing.Color]::FromArgb(255, 31, 27, 22))
$g.DrawString($head, $big, $ink, 20, 12)
$g.DrawString("Check: " + $check, $small, $ink, 20, 52)
$g.CopyFromScreen($b.Location, (New-Object System.Drawing.Point 0, $band), $b.Size)
$bmp.Save($path, [System.Drawing.Imaging.ImageFormat]::Png)
"$($b.Width)x$($b.Height)"
"""

# a part of the screen, x y w h, saved as a PNG: an installer's window by its own frame alone, for the
# screenshot check's crops (the sixth build)
PART = r"""
param([string]$path, [int]$x, [int]$y, [int]$w, [int]$h)
Add-Type -AssemblyName System.Drawing
$bmp = New-Object System.Drawing.Bitmap $w, $h
$g = [System.Drawing.Graphics]::FromImage($bmp)
$g.CopyFromScreen($x, $y, 0, 0, (New-Object System.Drawing.Size $w, $h))
$bmp.Save($path, [System.Drawing.Imaging.ImageFormat]::Png)
"$w by $h at $x,$y"
"""

# a shortcut's target, as Windows's own shell reads it
LINK = r"""
param([string]$path)
$s = (New-Object -ComObject WScript.Shell).CreateShortcut($path)
$s.TargetPath
"""


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


def powershell(script: str, *args: str, out: Path, timeout: float = 90) -> str:
    path = out / f"ps-{abs(hash(script)) % 100000}.ps1"
    path.write_text(script, encoding="utf-8")
    done = subprocess.run(["powershell.exe", "-NoProfile", "-STA", "-ExecutionPolicy", "Bypass", "-File", str(path), *args],
                          capture_output=True, text=True, timeout=timeout)
    return (done.stdout + done.stderr).strip()[-1500:]


def shot(out: Path, name: str, head: str, check: str) -> str:
    return powershell(SHOT, str(out / "shots" / name), head, check, out=out)


# ── user32, through ctypes ───────────────────────────────────────────────────────────────────────

def user32():
    from ctypes import wintypes
    u = ctypes.WinDLL("user32", use_last_error=True)
    u.EnumWindows.argtypes = [ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM), wintypes.LPARAM]
    u.EnumChildWindows.argtypes = [wintypes.HWND, ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM), wintypes.LPARAM]
    u.GetWindowTextW.argtypes = [wintypes.HWND, wintypes.LPWSTR, ctypes.c_int]
    u.GetClassNameW.argtypes = [wintypes.HWND, wintypes.LPWSTR, ctypes.c_int]
    u.IsWindowVisible.argtypes = [wintypes.HWND]
    u.GetDlgItem.argtypes = [wintypes.HWND, ctypes.c_int]
    u.GetDlgItem.restype = wintypes.HWND
    u.PostMessageW.argtypes = [wintypes.HWND, wintypes.UINT, wintypes.WPARAM, wintypes.LPARAM]
    u.SendMessageW.argtypes = [wintypes.HWND, wintypes.UINT, wintypes.WPARAM, wintypes.LPARAM]
    u.IsWindowEnabled.argtypes = [wintypes.HWND]
    u.SetForegroundWindow.argtypes = [wintypes.HWND]
    u.FindWindowExW.argtypes = [wintypes.HWND, wintypes.HWND, wintypes.LPCWSTR, wintypes.LPCWSTR]
    u.FindWindowExW.restype = wintypes.HWND
    # the parts of a window placed and measured, for the details list widened (the sixth build)
    u.GetParent.argtypes = [wintypes.HWND]
    u.GetParent.restype = wintypes.HWND
    u.GetWindowRect.argtypes = [wintypes.HWND, ctypes.POINTER(wintypes.RECT)]
    u.GetClientRect.argtypes = [wintypes.HWND, ctypes.POINTER(wintypes.RECT)]
    u.MapWindowPoints.argtypes = [wintypes.HWND, wintypes.HWND, ctypes.POINTER(wintypes.RECT), wintypes.UINT]
    u.SetWindowPos.argtypes = [wintypes.HWND, wintypes.HWND, ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_int, wintypes.UINT]
    u.RedrawWindow.argtypes = [wintypes.HWND, ctypes.c_void_p, ctypes.c_void_p, wintypes.UINT]
    u.SystemParametersInfoW.argtypes = [wintypes.UINT, wintypes.UINT, ctypes.c_void_p, wintypes.UINT]
    return u


U = None
PROC = None


def text_of(hwnd) -> str:
    buf = ctypes.create_unicode_buffer(512)
    U.GetWindowTextW(hwnd, buf, 512)
    return buf.value


def class_of(hwnd) -> str:
    buf = ctypes.create_unicode_buffer(128)
    U.GetClassNameW(hwnd, buf, 128)
    return buf.value


def tops(prefix: str) -> list:
    """Every visible top-level window whose title starts with `prefix`."""
    found = []

    def each(hwnd, _):
        if U.IsWindowVisible(hwnd) and text_of(hwnd).startswith(prefix):
            found.append(hwnd)
        return True
    U.EnumWindows(PROC(each), 0)
    return found


def words(hwnd) -> list[str]:
    """The words of a window's every visible control, a page's heading and its lines among them."""
    found = []

    def each(child, _):
        if U.IsWindowVisible(child) and text_of(child).strip():
            found.append(text_of(child).strip())
        return True
    U.EnumChildWindows(hwnd, PROC(each), 0)
    return found


def press(hwnd, control: int = 1) -> bool:
    """A dialog's button pressed as its click tells the dialog: 1 is NSIS's Next, Install, Finish and
    Uninstall. The dialog is told straight, WM_COMMAND with BN_CLICKED, since a click sent to the button
    of a dialog that is not in front was lost on the last page (the third build's second Windows run)."""
    button = U.GetDlgItem(hwnd, control)
    if not button or not U.IsWindowEnabled(button):
        return False
    U.SetForegroundWindow(hwnd)
    U.PostMessageW(hwnd, 0x0111, control, button)  # WM_COMMAND, BN_CLICKED in the high word, 0
    return True


def unfold_details(hwnd) -> bool:
    """The files page's Show details pressed, as its own click presses it: the page, the dialog inside
    the installer's window, told straight, as `press` tells the window, so the list of what Setup did
    shows (18 October, the fifth build, the fourth build's check having seen the page folded)."""
    inner = U.FindWindowExW(hwnd, None, "#32770", None)
    button = U.GetDlgItem(inner, 1027) if inner else None
    if not button or not U.IsWindowVisible(button):
        return False
    U.SetForegroundWindow(hwnd)
    U.PostMessageW(inner, 0x0111, 1027, button)  # WM_COMMAND, BN_CLICKED in the high word, 0
    # the list taken back to its first line, so what Setup did first is what shows
    time.sleep(1)
    listed = U.GetDlgItem(inner, 1016)
    if listed:
        U.SendMessageW(listed, 0x1013, 0, 0)  # LVM_ENSUREVISIBLE, the first item, wholly
    return True


def frame(hwnd) -> list[int]:
    """A window's frame as the screen draws it, its shadow left out (DWMWA_EXTENDED_FRAME_BOUNDS)."""
    from ctypes import wintypes
    r = wintypes.RECT()
    ctypes.WinDLL("dwmapi").DwmGetWindowAttribute(wintypes.HWND(hwnd), 9, ctypes.byref(r), ctypes.sizeof(r))
    return [r.left, r.top, r.right - r.left, r.bottom - r.top]


def dialog_shot(out: Path, name: str, hwnd) -> dict:
    """The installer's window alone taken from the screen, by its own frame, for the screenshot check's
    Before and After at one scale (the sixth build), beside the shot with its heading."""
    x, y, w, h = frame(hwnd)
    return {"frame": [x, y, w, h], "saved": powershell(PART, str(out / "shots" / name), str(x), str(y), str(w), str(h), out=out)}


def rect_in(hwnd, parent) -> list[int]:
    """A part's place and size in its parent's own area, x y w h."""
    from ctypes import wintypes
    r = wintypes.RECT()
    U.GetWindowRect(hwnd, ctypes.byref(r))
    U.MapWindowPoints(None, parent, ctypes.byref(r), 2)
    return [r.left, r.top, r.right - r.left, r.bottom - r.top]


def place(hwnd, x: int, y: int, w: int, h: int) -> None:
    U.SetWindowPos(hwnd, None, x, y, w, h, 0x0014)  # SWP_NOZORDER | SWP_NOACTIVATE


# what whole_details moved, so restore_details puts each part back
WIDENED: list = []


def stretched(rect: list[int], page: list[int], width: int, wider: int, taller: int) -> list[int]:
    """Where one part of the installer's window goes when the window is `wider` and `taller`, each rect x y
    w h in the window's own area `width` wide, `page` the page's: the page, and the place NSIS keeps for it,
    grow by both, and of the rest, the line, the buttons and the name at the foot under the page and the
    heading's band above it, what runs across most of the window is stretched, what stands with its middle
    in the right half moves right, and what is under the page moves down (the sixth build)."""
    x, y, w, h = rect
    if all(abs(a - b) <= 4 for a, b in zip(rect, page)):
        return [x, y, w + wider, h + taller]
    down = taller if y >= page[1] + page[3] - 2 else 0
    if w > width * 0.6:
        return [x, y + down, w + wider, h]
    return [x + wider if x + w / 2 > width / 2 else x, y + down, w, h]


def whole_details(hwnd) -> dict:
    """The details list made wide enough for its longest line, and taller, so every line shows whole where
    the fifth build's picture cut each at its right with dots (18 October, the sixth build, the screenshot
    check). NSIS lays its pages out once, so the window, its page, the list, the bar and the line above it
    are each made wider and the list taller, the buttons and the heading's mark moved right and the foot
    moved down by as much, within the screen's work area. `restore_details` puts every part back, so Finish
    stands as it was."""
    from ctypes import wintypes
    inner = U.FindWindowExW(hwnd, None, "#32770", None)
    listed = U.GetDlgItem(inner, 1016) if inner else None
    if not listed or not U.IsWindowVisible(listed):
        return {"list": False}
    U.SendMessageW(listed, 0x101E, 0, -1)  # LVM_SETCOLUMNWIDTH, LVSCW_AUTOSIZE: the longest line's width
    longest = U.SendMessageW(listed, 0x101D, 0, 0)  # LVM_GETCOLUMNWIDTH
    inside, outer, work = wintypes.RECT(), wintypes.RECT(), wintypes.RECT()
    U.GetClientRect(listed, ctypes.byref(inside))
    U.GetWindowRect(hwnd, ctypes.byref(outer))
    U.SystemParametersInfoW(0x0030, 0, ctypes.byref(work), 0)  # SPI_GETWORKAREA
    ww, wh = outer.right - outer.left, outer.bottom - outer.top
    dw = max(0, min(longest - inside.right + 8, (work.right - work.left) - ww - 16))
    dh = max(0, min(260, (work.bottom - work.top) - wh - 16))
    top_area = wintypes.RECT()
    U.GetClientRect(hwnd, ctypes.byref(top_area))
    cw = top_area.right
    page = rect_in(inner, hwnd)
    kids = []

    def each(child, _):
        if U.GetParent(child) == hwnd:
            kids.append(child)
        return True
    U.EnumChildWindows(hwnd, PROC(each), 0)
    WIDENED.clear()
    WIDENED.append((hwnd, None, [outer.left, outer.top, ww, wh]))
    x0 = max(work.left, min(outer.left, work.right - (ww + dw)))
    y0 = max(work.top, min(outer.top, work.bottom - (wh + dh)))
    U.SetWindowPos(hwnd, None, x0, y0, ww + dw, wh + dh, 0x0014)
    for kid in kids:
        was = rect_in(kid, hwnd)
        new = stretched(was, page, cw, dw, dh)
        if new != was:
            place(kid, *new)
            WIDENED.append((kid, hwnd, was))
    for part, taller in ((1016, True), (1004, False), (1006, False)):  # the list, the bar, the line above it
        kid = U.GetDlgItem(inner, part)
        if kid:
            x, y, w, h = rect_in(kid, inner)
            place(kid, x, y, w + dw, h + (dh if taller else 0))
            WIDENED.append((kid, inner, [x, y, w, h]))
    U.SendMessageW(listed, 0x101E, 0, -2)  # LVSCW_AUTOSIZE_USEHEADER: the column fills the list
    U.SendMessageW(listed, 0x1013, 0, 0)  # LVM_ENSUREVISIBLE, the first line
    U.RedrawWindow(hwnd, None, None, 0x0585)  # invalidate, erase, frame, every child, now
    shown = wintypes.RECT()
    U.GetClientRect(listed, ctypes.byref(shown))
    return {"longest": longest, "list_was": inside.right, "list_now": shown.right, "wider": dw, "taller": dh,
            "parts": len(WIDENED) - 1, "window": frame(hwnd)}


def restore_details() -> dict:
    """Every part whole_details moved put back, the window last, so the pages after stand as they were."""
    if not WIDENED:
        return {"restored": 0}
    hwnd, _, (x, y, w, h) = WIDENED[0]
    for kid, _, r in reversed(WIDENED[1:]):
        place(kid, *r)
    U.SetWindowPos(hwnd, None, x, y, w, h, 0x0014)
    inner = U.FindWindowExW(hwnd, None, "#32770", None)
    listed = U.GetDlgItem(inner, 1016) if inner else None
    if listed:
        U.SendMessageW(listed, 0x101E, 0, -2)
    U.RedrawWindow(hwnd, None, None, 0x0585)
    count = len(WIDENED)
    WIDENED.clear()
    return {"restored": count, "window": frame(hwnd)}


def end_setup(proc) -> int | str:
    """A Setup left on a page ended outright, as nothing past its pages has run, so nothing changes."""
    subprocess.run(["taskkill", "/F", "/T", "/PID", str(proc.pid)], capture_output=True, text=True)
    try:
        return proc.wait(timeout=30)
    except subprocess.TimeoutExpired:
        return "still running"


def page_after_welcome(setup: str, title: str, marker: str, name: str, head: str, check: str, out: Path) -> dict:
    """Setup run as a tester runs it, Next pressed on Welcome, and the page that follows, the one that
    says what is installed and asks what to do, taken from the screen with its words, then Setup ended
    there. Each of its lines in plain words since the fifth build (18 October, English.nsh). The Setup is
    named by its whole path, which on Windows has no forward slash: Tauri's installer reads any word of its
    command line that starts /P as its passive switch, so build/proof/... ran it with no pages at all (the
    fifth build's first run)."""
    proc = subprocess.Popen([str(Path(setup).resolve())])
    said = {}
    welcome = wait_for(lambda: shown(title, f"Welcome to {title}"), 90)
    said["welcome"] = bool(welcome)
    if welcome:
        time.sleep(1)
        press(welcome[0])
        page = wait_for(lambda: shown(title, marker), 60)
        said["words"] = page[1] if page else "never shown"
        if page:
            time.sleep(1.5)
            said["shot"] = shot(out, name, head, check)
            said["dialog_shot"] = dialog_shot(out, name.replace(".png", "-dialog.png"), page[0])
    if not welcome or said.get("words") == "never shown":
        said["windows"] = [text_of(h) for h in tops("")][:12]
    said["ended"] = end_setup(proc)
    return said


def wait_for(fn, seconds: float, every: float = 0.5):
    t0 = time.time()
    while time.time() - t0 < seconds:
        try:
            got = fn()
            if got:
                return got
        except Exception:  # noqa: BLE001  not there yet
            pass
        time.sleep(every)
    return None


def page_words(prefix: str) -> tuple:
    """The installer's window and its page's words, the page being the dialog inside it."""
    hits = tops(prefix)
    if not hits:
        return None, []
    return hits[0], words(hits[0])


def shown(prefix: str, marker: str):
    """The window and its words once a page that says `marker` stands in it with its first button
    enabled, or None until then."""
    win, said = page_words(prefix)
    if win and any(marker in t for t in said) and U.IsWindowEnabled(U.GetDlgItem(win, 1)):
        return win, said
    return None


# ── the registry and the folders ─────────────────────────────────────────────────────────────────

def reg(key: str, value: str = "") -> str | None:
    import winreg
    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, key) as k:
            return str(winreg.QueryValueEx(k, value)[0])
    except OSError:
        return None


def listing(folder: Path, depth: int = 1) -> list[str]:
    if not folder.exists():
        return ["(not there)"]
    return sorted(str(p.relative_to(folder)) for p in folder.glob("*" if depth == 1 else "**/*"))[:60]


def processes() -> list[str]:
    done = subprocess.run(["tasklist", "/fo", "csv", "/nh"], capture_output=True, text=True)
    return sorted(line.split(",")[0].strip('"') for line in done.stdout.splitlines() if "Idiograph" in line)


def listening(port: int) -> bool:
    import socket
    with socket.socket() as s:
        s.settimeout(0.3)
        return s.connect_ex(("127.0.0.1", port)) == 0


def other_versions(older: str, newer: str, title: str, out: Path) -> int:
    """`--older` and `--newer` (the fifth build, the update job's): with the newer version installed, the
    older one's Setup and the page saying a newer version is installed, then the older one put in quietly
    and the newer one's Setup and the page saying an older version is installed, each Setup ended on that
    page, so the installer's every page that asks what to do is seen in its plain words."""
    exe = Path(os.environ["LOCALAPPDATA"]) / title / f"{title}.exe"
    note("installed_first", {"exe": exe.is_file(), "processes": processes()})
    attempt("older_over_newer", lambda: page_after_welcome(
        older, f"{title} Setup", "Already installed", "win-install-older-over-newer.png",
        "The installer of an older version, run where a newer one is installed",
        "A newer version is installed. This Setup is older., Uninstall it first or Install over it (not possible with an older version), and Choose how to install", out))

    def put_older():
        done = subprocess.run([str(Path(older).resolve()), "/S"], capture_output=True, timeout=300)
        time.sleep(3)
        return {"exit": done.returncode, "version": reg(rf"Software\Microsoft\Windows\CurrentVersion\Uninstall\{title}", "DisplayVersion")}
    attempt("older_put_in", put_older)
    attempt("newer_over_older", lambda: page_after_welcome(
        newer, f"{title} Setup", "Already installed", "win-install-newer-over-older.png",
        "The installer of a newer version, run where an older one is installed",
        "An older version is installed, Uninstall it first or Install over it, and Choose how to install", out))
    return 0


def main() -> int:
    global U, PROC
    ap = argparse.ArgumentParser()
    ap.add_argument("--inno")
    ap.add_argument("--setup")
    ap.add_argument("--older", help="with --newer: the pages an older and a newer version's Setup show")
    ap.add_argument("--newer")
    ap.add_argument("--title", default="Idiograph Test")
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    from ctypes import wintypes
    U = user32()
    PROC = ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)
    out = Path(a.out).resolve()
    (out / "shots").mkdir(parents=True, exist_ok=True)
    SAVED.append(out / "results.json")
    if a.older and a.newer:
        return other_versions(a.older, a.newer, a.title, out)
    if not (a.inno and a.setup):
        ap.error("--inno and --setup, or --older and --newer")
    local, roaming = Path(os.environ["LOCALAPPDATA"]), Path(os.environ["APPDATA"])
    data, old_dir, new_dir = roaming / "Idiograph", local / "Programs" / "Idiograph", local / "Idiograph"
    menu = roaming / "Microsoft" / "Windows" / "Start Menu" / "Programs"

    # ── 1. 0.9.0, as a tester had it
    def old():
        done = subprocess.run([a.inno, "/VERYSILENT", "/SUPPRESSMSGBOXES", "/NORESTART"], capture_output=True, timeout=300)
        said = {"exit": done.returncode, "version": reg(INNO_KEY, "DisplayVersion"), "folder": listing(old_dir)}
        # its server started as its own launcher starts it, on 8765, and left running, as a tester who
        # did not quit it first leaves it, so the new installer has to stop it
        RUNNING.append(subprocess.Popen([str(old_dir / "Idiograph.exe"), "--serve", "--no-browser"]))
        said["served"] = bool(wait_for(lambda: listening(8765) and (data / "config.json").is_file(), 60))
        (data / "check-note.txt").write_text("A note of the check's own, kept across the upgrade.\n", encoding="utf-8")
        said["data"] = listing(data)
        said["start_menu"] = sorted(p.name for p in menu.glob("Idiograph*"))
        return said
    attempt("old_0_9_0", old)

    # ── 2. the new installer, page by page, each found by the heading it shows
    def install():
        said = {}
        setup = subprocess.Popen([a.setup])
        steps = (("Welcome to Idiograph Setup", "win-install-1-welcome.png", "Idiograph's installer: its first page, Welcome",
                  "Idiograph's mark at the left and in the title bar, words saying it installs for you alone with no administrator's password and no restart, Next, and no shield on any button"),
                 ("Choose Install Location", "win-install-2-folder.png", "Idiograph's installer: the folder it installs in",
                  "a folder in your own AppData, Local, Idiograph, and no administrator's shield on Install"),
                 ("Installation Complete", "win-install-3-installed.png", "Idiograph's installer: the files in",
                  "Completed, after it stopped 0.9.0 and removed it, every setting and case kept"),
                 ("Completing Idiograph Setup", "win-install-4-finish.png", "Idiograph's installer: its last page",
                  "Open Idiograph ticked, and a desktop shortcut left for you to choose"))
        for marker, name, head, check in steps:
            found = wait_for(lambda m=marker: shown("Idiograph Setup", m), 600 if "Complete" in marker else 90)
            key = name.split("-", 3)[-1].replace(".png", "")
            said[key] = found[1] if found else "never shown"
            if not found:
                said[f"{key}_windows"] = [text_of(h) for h in tops("")][:12]
                break
            time.sleep(1)
            said[f"shot_{key}"] = shot(out, name, head, check)
            # the files page's details unfolded too, what Setup did line by line (the fifth build)
            if marker == "Installation Complete":
                said["details_unfolded"] = unfold_details(found[0])
                time.sleep(1.5)
                said["shot_details"] = shot(out, "win-install-3b-details.png", "Idiograph's installer: the files in, its details unfolded",
                                            "each thing Setup did in order from the first, 0.9.0 stopped and removed, then the files")
                # and widened until every line shows whole, then put back (the sixth build)
                said["details_whole"] = whole_details(found[0])
                time.sleep(1.5)
                said["shot_details_whole"] = shot(out, "win-install-3c-details-whole.png",
                                                  "Idiograph's installer: the files in, its window widened to the longest line",
                                                  "every line of what Setup did whole, from the first")
                said["details_whole_dialog"] = dialog_shot(out, "win-install-3c-details-whole-dialog.png", found[0])
                said["details_back"] = restore_details()
                time.sleep(1)
            said[f"pressed_{key}"] = press(found[0])
        said["running_0_9_0_after"] = [p.poll() for p in RUNNING]
        try:
            said["setup_exit"] = setup.wait(timeout=120)
        except subprocess.TimeoutExpired:
            said["setup_exit"] = "still running"
        return said
    attempt("install", install)

    # ── 3. the installed app's first window
    def app_windows() -> list:
        return [h for h in tops("Idiograph") if not text_of(h).startswith("Idiograph Setup")]

    def first_window():
        said = {"by": "Finish, Open Idiograph ticked"}
        if not wait_for(lambda: app_windows() and listening(8765), 60):
            # as the Start menu's entry opens it, when the last page's Run did not
            said["by"] = "the Start menu's own target, Finish having opened nothing"
            subprocess.Popen([str(new_dir / "Idiograph.exe")])
        said["window"] = bool(wait_for(lambda: app_windows() and listening(8765), 90))
        said.update(old_server_ended=[p.poll() for p in RUNNING], next_port=listening(8766))
        time.sleep(10)
        said["titles"] = [text_of(h) for h in tops("")][:12]
        said["shot"] = shot(out, "win-installed-first-window.png", "The installed app's first window, on Windows",
                            "Idiograph in its own window, File, Edit, View and Help above the home screen")
        said["processes"] = processes()
        return said
    attempt("first_window", first_window)

    # ── 4. what the install left
    def left():
        links = sorted(p.name for p in menu.glob("Idiograph*"))
        return {"inno_entry": reg(INNO_KEY, "UninstallString"), "inno_folder": old_dir.exists(),
                "new_entry": {"version": reg(NSIS_KEY, "DisplayVersion"), "uninstall": reg(NSIS_KEY, "UninstallString")},
                "new_folder": listing(new_dir), "server_folder": (new_dir / "server" / "Idiograph-console.exe").is_file(),
                "start_menu": links,
                "start_menu_target": powershell(LINK, str(menu / "Idiograph.lnk"), out=out) if "Idiograph.lnk" in links else None,
                "data": listing(data), "note_kept": (data / "check-note.txt").is_file(),
                "config_kept": (data / "config.json").is_file()}
    attempt("left", left)

    # the MCP server and the command line from the install, as Claude Desktop and an agent run them
    def mcp():
        msgs = "\n".join(json.dumps(m) for m in (
            {"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {"protocolVersion": "2025-06-18", "capabilities": {}, "clientInfo": {"name": "check", "version": "0"}}},
            {"jsonrpc": "2.0", "method": "notifications/initialized"},
            {"jsonrpc": "2.0", "id": 2, "method": "tools/list"})) + "\n"
        done = subprocess.run([str(new_dir / "server" / "Idiograph-console.exe"), "mcp"], input=msgs, capture_output=True,
                              text=True, encoding="utf-8", timeout=60)
        lines = [json.loads(x) for x in done.stdout.splitlines() if x.strip().startswith("{")]
        tools = next((len(m["result"].get("tools", [])) for m in lines if m.get("id") == 2 and "result" in m), None)
        cli = subprocess.run([str(new_dir / "server" / "Idiograph-console.exe"), "cli", "--help"], capture_output=True,
                             text=True, encoding="utf-8", timeout=60)
        return {"mcp_answers": len(lines), "tools": tools, "cli_help": cli.returncode, "cli_first": cli.stdout.strip().splitlines()[:1]}
    attempt("mcp_and_cli", mcp)

    # ── 4b. Setup run again for the version installed: the page that asks what to do, then Setup ended
    # there, the app left as it was (the fifth build)
    attempt("same_again", lambda: dict(page_after_welcome(
        a.setup, "Idiograph Setup", "Already installed", "win-install-same-again.png",
        "Idiograph's installer run again for the version you have",
        "Already installed, the version, Install it again or Uninstall Idiograph, and Choose what to do, then click Next", out),
        still_running=processes()))

    # ── 5. the app closed by its close button, then the uninstaller
    def close_app():
        for hwnd in app_windows():
            U.PostMessageW(hwnd, 0x0010, 0, 0)  # WM_CLOSE
        gone = wait_for(lambda: not listening(8765) and not processes(), 60)
        return {"gone": bool(gone), "processes": processes()}
    attempt("close_app", close_app)

    def uninstall():
        said = {}
        subprocess.Popen([str(new_dir / "uninstall.exe")])
        found = wait_for(lambda: shown("Idiograph Uninstall", "Remove Idiograph from your computer"), 60)
        said["confirm"] = found[1] if found else "never shown"
        if found:
            time.sleep(1)
            said["words_confirm"] = words(found[0])
            said["shot_confirm"] = shot(out, "win-uninstall-1-confirm.png", "Idiograph's uninstaller: its first page",
                                        "Idiograph's mark at the top right, the line saying cases, transcripts and projects stay, and the tick, unticked, clearing only the window's size, zoom, appearance and folded sections")
            press(found[0])
            done = wait_for(lambda: shown("Idiograph Uninstall", "Uninstallation Complete"), 120)
            said["after"] = done[1] if done else "never shown"
            if done:
                time.sleep(1)
                said["shot_after"] = shot(out, "win-uninstall-2-done.png", "Idiograph's uninstaller: done",
                                          "Completed, the app's own files gone and nothing of yours touched")
                press(done[0])
        time.sleep(3)
        said["left"] = {"app": (new_dir / "Idiograph.exe").exists(), "server": (new_dir / "server").exists(),
                        "folder": listing(new_dir), "logs_kept": (new_dir / "Logs").is_dir(),
                        "logs": listing(new_dir / "Logs"), "data": listing(data), "note_kept": (data / "check-note.txt").is_file(),
                        "config_kept": (data / "config.json").is_file(),
                        "entry": reg(NSIS_KEY, "UninstallString"), "start_menu": sorted(p.name for p in menu.glob("Idiograph*"))}
        return said
    attempt("uninstall", uninstall)
    return 0


if __name__ == "__main__":
    sys.exit(main())
