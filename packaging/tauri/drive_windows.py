#!/usr/bin/env python3
"""The window checked on GitHub's Windows machine (17 October 2026), run by `.github/workflows/tauri.yml`
once the window is built and installed as the test app.

    python packaging/tauri/drive_windows.py --exe <installed exe> --stage <the staged demo>
        --shipped-config <the staged config.json> --out <folder>

The window is driven through WebView2's own debugging port, which this run alone opens, through
WEBVIEW2_ADDITIONAL_BROWSER_ARGUMENTS in the window's environment, never in a build that ships, and
Playwright's `connect_over_cdp`, one connection for each start of the app. What a page cannot show,
the print panel, the save panel, two windows side by side and a file dragged from another program, is
taken from the screen. Every step has a watchdog, since a call into a page that never answers cannot
be stopped from outside it, and a step that hangs ends the run with what it waited for. Every result
goes in `results.json` beside the screenshots, and nothing reaches any service but this machine's.
"""
from __future__ import annotations

import argparse
import csv
import json
import os
import subprocess
import sys
import threading
import time
import traceback
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import drive_common as dc  # noqa: E402  beside this file
import drive_windows_two as build2  # noqa: E402  the second build's steps, beside this file
import drive_windows_three as build3  # noqa: E402  the third build's steps, beside this file
import drive_windows_four as build4  # noqa: E402  the fourth build's steps, beside this file

CDP = 9222
RESULTS: dict = {}
SAVED: list = []
# the run's folder, for the second build's steps
OUT: list = []


def note(key: str, value) -> None:
    """A result kept, and results.json written afresh, so a run that stops keeps what it found."""
    RESULTS[key] = value
    print(f"{key}: {json.dumps(value, default=str)[:1500]}", flush=True)
    if SAVED:
        SAVED[0].write_text(json.dumps(RESULTS, indent=2, default=str), encoding="utf-8")


def watched(name: str, seconds: float, fn):
    """`fn` run with a watchdog: should it still be running after `seconds`, what it waited for is
    written to the results and the run ends there (17 October, the third run's 37 minutes on a page
    that never answered)."""
    def bite():
        note(f"hung_{name}", f"no answer after {seconds} s")
        os._exit(3)
    dog = threading.Timer(seconds, bite)
    dog.daemon = True
    dog.start()
    try:
        return fn()
    finally:
        dog.cancel()


def attempt(name: str, fn, seconds: float = 240) -> None:
    try:
        note(name, watched(name, seconds, fn))
    except Exception:  # noqa: BLE001  one failed step never stops the rest
        note(name, {"error": traceback.format_exc()[-1500:]})


# ── Windows's own, through PowerShell ────────────────────────────────────────────────────────────

DESKTOP = r"""
Add-Type -AssemblyName System.Windows.Forms, System.Drawing
$b = [System.Windows.Forms.Screen]::PrimaryScreen.Bounds
$bmp = New-Object System.Drawing.Bitmap $b.Width, $b.Height
$g = [System.Drawing.Graphics]::FromImage($bmp)
$g.CopyFromScreen($b.Location, [System.Drawing.Point]::Empty, $b.Size)
$bmp.Save($args[0], [System.Drawing.Imaging.ImageFormat]::Png)
"$($b.Width)x$($b.Height)"
"""

# every visible window of the app's processes, by title, and with "close" each sent WM_CLOSE, as its
# close button sends it. The single-instance plugin's own window, "<identifier>-siw", is left out
WINDOWS = r"""
Add-Type -TypeDefinition @'
using System; using System.Text; using System.Runtime.InteropServices; using System.Collections.Generic;
public static class Wins {
  public delegate bool EnumProc(IntPtr h, IntPtr l);
  [DllImport("user32.dll")] static extern bool EnumWindows(EnumProc f, IntPtr l);
  [DllImport("user32.dll")] static extern bool IsWindowVisible(IntPtr h);
  [DllImport("user32.dll")] static extern uint GetWindowThreadProcessId(IntPtr h, out uint pid);
  [DllImport("user32.dll", CharSet = CharSet.Unicode)] static extern int GetWindowText(IntPtr h, StringBuilder s, int n);
  [DllImport("user32.dll")] static extern bool PostMessage(IntPtr h, uint m, IntPtr w, IntPtr l);
  public static string Run(int[] pids, bool close) {
    var set = new HashSet<int>(pids); var found = new List<string>();
    EnumWindows((h, l) => {
      uint pid; GetWindowThreadProcessId(h, out pid);
      if (set.Contains((int)pid) && IsWindowVisible(h)) {
        var sb = new StringBuilder(256); GetWindowText(h, sb, 256);
        if (sb.Length > 0 && !sb.ToString().EndsWith("-siw")) { found.Add(sb.ToString()); if (close) PostMessage(h, 0x0010, IntPtr.Zero, IntPtr.Zero); }
      }
      return true; }, IntPtr.Zero);
    return found.Count + ": " + string.Join(" | ", found);
  }
}
'@
$ids = [int[]]@(Get-Process -Name $args[0] -ErrorAction SilentlyContinue | ForEach-Object { $_.Id })
[Wins]::Run($ids, $args[1] -eq 'close')
"""

# the visible window with exactly this title sent WM_CLOSE, as its close button sends it
CLOSE_TITLE = r"""
Add-Type -TypeDefinition @'
using System; using System.Text; using System.Runtime.InteropServices;
public static class Shut {
  public delegate bool EnumProc(IntPtr h, IntPtr l);
  [DllImport("user32.dll")] static extern bool EnumWindows(EnumProc f, IntPtr l);
  [DllImport("user32.dll")] static extern bool IsWindowVisible(IntPtr h);
  [DllImport("user32.dll", CharSet = CharSet.Unicode)] static extern int GetWindowText(IntPtr h, StringBuilder s, int n);
  [DllImport("user32.dll")] static extern bool PostMessage(IntPtr h, uint m, IntPtr w, IntPtr l);
  public static int Run(string title) {
    int n = 0;
    EnumWindows((h, l) => {
      var sb = new StringBuilder(256); GetWindowText(h, sb, 256);
      if (IsWindowVisible(h) && sb.ToString() == title) { PostMessage(h, 0x0010, IntPtr.Zero, IntPtr.Zero); n++; }
      return true; }, IntPtr.Zero);
    return n;
  }
}
'@
[Shut]::Run($args[0])
"""

# WebView2's processes with the arguments they were started with
WEBVIEWS = r"""
Get-CimInstance Win32_Process -Filter "name='msedgewebview2.exe'" | Select-Object -First 3 | ForEach-Object { $_.CommandLine.Substring(0, [Math]::Min(400, $_.CommandLine.Length)) }
"""

# a key pressed in the window whose title starts with the first argument, brought to the front first
KEYS = r"""
Add-Type -AssemblyName System.Windows.Forms
$shell = New-Object -ComObject WScript.Shell
$ok = $shell.AppActivate($args[0])
Start-Sleep -Milliseconds 400
[System.Windows.Forms.SendKeys]::SendWait($args[1])
"activated $ok"
"""

# the save panel's title as Windows shows it: Share a copy's line, which the window sets as the panel's title
# with its full stop taken off (`pick_title` in main.rs), read from the page so the check never pins the words
SHARE_TITLE = "return String(SHARE_LINE).trim().replace(/[.\\s]+$/, '');"

# a folder the user may not add a file to, so the panel takes a name in it and the server's write is refused,
# and the folder given back after
LOCK = r"""
icacls $args[0] /deny "$($env:USERNAME):(OI)(CI)(WD,AD)" | Out-Null
"locked"
"""
UNLOCK = r"""
icacls $args[0] /remove:d $env:USERNAME | Out-Null
"unlocked"
"""


def sendkeys_text(text: str) -> str:
    """`text` as SendKeys types it: each of its special characters in braces."""
    return "".join("{" + ch + "}" if ch in "{}[]()+^%~" else ch for ch in text)

# the check's ears on a drop, every drag event counted and each drop's files noted in the capture phase,
# nothing taken from the page, which takes the drop itself: until the fourth build this took the drop, so
# the New project card never had it and stood empty in the picture (18 October). A drop nothing on the page
# took is kept from opening the file in the window, once the page has had it
DROP_ARM = """window.__drops = []; window.__over = 0; window.__enter = 0; window.__leave = 0;
window.addEventListener('dragenter', function () { window.__enter += 1; }, true);
window.addEventListener('dragleave', function () { window.__leave += 1; }, true);
window.addEventListener('dragover', function () { window.__over += 1; }, true);
window.addEventListener('drop', function (e) {
  window.__drops.push({ files: Array.prototype.map.call(e.dataTransfer.files || [], function (f) { return f.name + ' ' + f.size; }), types: Array.prototype.slice.call(e.dataTransfer.types || []) });
}, true);
window.addEventListener('drop', function (e) { if (!e.defaultPrevented) e.preventDefault(); }, false);
return true;"""

DROP_READ = ("var rows = (typeof NP !== 'undefined' && NP.rows) ? NP.rows.length : -1; hide('newproject'); "
             "return { enter: window.__enter, over: window.__over, leave: window.__leave, drops: window.__drops, card_rows: rows };")
# the New Project card, which takes a file dropped anywhere on the window while it is open
DROP_CARD = "openNewProject(); return !document.getElementById('newproject').hidden;"

# Cut, Copy, Paste, Select All, Undo and Redo by their keys, in a text field of the check's own laid
# over the page and taken away after, so nothing of the app's is touched or saved
EDIT_FIELD = """var f = document.createElement('input');
f.id = 'drive-edit'; f.style.cssText = 'position:fixed;left:40px;top:40px;z-index:99999;width:300px;font-size:18px';
document.body.appendChild(f); f.focus();
return { focused: document.activeElement === f };"""
EDIT_VALUE = "var f = document.getElementById('drive-edit'); return { value: f.value, start: f.selectionStart, end: f.selectionEnd };"
EDIT_DONE = "var f = document.getElementById('drive-edit'); if (f) f.remove(); return true;"


def powershell(script: str, *args: str, out: Path, timeout: float = 90) -> str:
    path = out / f"ps-{abs(hash(script)) % 100000}.ps1"
    path.write_text(script, encoding="utf-8")
    done = subprocess.run(["powershell.exe", "-NoProfile", "-STA", "-ExecutionPolicy", "Bypass", "-File", str(path), *args],
                          capture_output=True, text=True, timeout=timeout)
    return (done.stdout + done.stderr).strip()[-1500:]


def desktop(path: Path, out: Path) -> str:
    return powershell(DESKTOP, str(path), out=out)


def ps_press(keys: str) -> str:
    """Keys pressed into whatever has the keyboard, a dialog standing open among them."""
    return powershell(build2.PRESS, keys, out=OUT[0])


def memory(name: str) -> dict:
    """Working sets in MB of the window, the server and WebView2's processes, from tasklist."""
    done = subprocess.run(["tasklist", "/fo", "csv", "/nh"], capture_output=True, text=True)
    sums: dict = {}
    for row in csv.reader(done.stdout.splitlines()):
        if len(row) >= 5 and row[0].lower() in (f"{name.lower()}.exe", "idiograph.exe", "msedgewebview2.exe"):
            kb = int("".join(ch for ch in row[4] if ch.isdigit()) or 0)
            sums.setdefault(row[0], [0, 0])
            sums[row[0]][0] += 1
            sums[row[0]][1] += kb // 1024
    return {k: {"processes": v[0], "mb": v[1]} for k, v in sums.items()}


def ev(page, body: str, timeout: float = 60):
    """One step's body run in `page` as an async function, its answer back, in the page's own world
    through a CDP session of its own (see `cdp_ev`), since from the second build a step may take a
    page found afresh after Reload, which Playwright's own evaluate ran without the page's scripts.
    A step that throws raises, as Playwright's evaluate did."""
    got = cdp_ev(page, body, timeout)
    if isinstance(got, dict) and set(got) == {"error"}:
        raise RuntimeError(got["error"])
    return got


def cdp_ev(page, body: str, timeout: float = 60):
    """One step's body run in `page`'s own world through a CDP session of its own, for a page Playwright
    attached to late, whose evaluate found none of the page's own functions (17 October, the first build)."""
    session = page.context.new_cdp_session(page)
    got = session.send("Runtime.evaluate", {"expression": "(async () => {\n" + body + "\n})()", "awaitPromise": True,
                                            "returnByValue": True, "timeout": int(timeout * 1000)})
    if got.get("exceptionDetails"):
        return {"error": str(got["exceptionDetails"])[:600]}
    return (got.get("result") or {}).get("value")


def targets() -> list:
    """WebView2's debugging targets as its own list gives them."""
    try:
        with urllib.request.urlopen(f"http://127.0.0.1:{CDP}/json/list", timeout=5) as res:
            return json.loads(res.read() or b"[]")
    except (OSError, ValueError):
        return []


def wait_for(fn, seconds: float, every: float = 0.25):
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


def server_started() -> str | None:
    """The server's own `started`, asked as its page asks it."""
    req = urllib.request.Request(f"http://127.0.0.1:{dc.PORT}/api/server", headers={"Host": f"127.0.0.1:{dc.PORT}"})
    try:
        with urllib.request.build_opener(urllib.request.ProxyHandler({})).open(req, timeout=5) as res:
            return json.loads(res.read()).get("started")
    except (OSError, ValueError):
        return None


class Window:
    """The installed window started with its debugging port open for this run alone, and the one
    Playwright connection to it. A window's page is found afresh by its address each time, since
    WebView2 may give a page a new target as it loads (17 October)."""

    def __init__(self, exe: Path, env: dict, pw, out: Path, tag: str, port: int = dc.PORT):
        self.t0 = time.time()
        self.port = port
        # the window's own words, which a windowed program writes only to the streams it is handed
        self.log = open(out / f"window-{tag}.log", "w", encoding="utf-8")
        self.proc = subprocess.Popen([str(exe)], env=env, stdout=self.log, stderr=subprocess.STDOUT)
        ready = wait_for(lambda: dc.listening(port) and dc.listening(CDP), 90)
        self.server_s = round(time.time() - self.t0, 2) if ready else None
        if not ready:
            note(f"no_debugging_port_{tag}", {"server": dc.listening(port), "windows": powershell(WINDOWS, exe.stem, "list", out=out),
                                              "webview": powershell(WEBVIEWS, out=out), "desktop": desktop(out / "shots" / f"win-no-port-{tag}.png", out)})
        own = f"http://127.0.0.1:{port}"
        listed = wait_for(lambda: [t for t in targets() if t.get("url", "").startswith(own)], 60)
        note(f"targets_{tag}", [(t.get("type"), t.get("url", "")[:60]) for t in targets()])
        self.pw = pw
        self.others: list = []
        self.browser = pw.chromium.connect_over_cdp(f"http://127.0.0.1:{CDP}", timeout=60000)
        # a connection made before the page has loaded may list it as about:blank and never learn
        # better, so a page not found is looked for again through a connection of its own (17 October,
        # the third build's second Windows run, whose window stood loaded while the check saw a blank page)
        self.page = self.find(lambda p: p.url.startswith(own), 30) or self.fresh(lambda p: p.url.startswith(own), 60)
        note(f"connected_{tag}", {"listed": bool(listed), "pages": self.pages()})

    def all_pages(self) -> list:
        return [p for c in self.browser.contexts for p in c.pages if not p.is_closed()]

    def pages(self) -> list:
        return [p.url[:70] for p in self.all_pages()]

    def find(self, pred, seconds: float = 30, besides=()):
        """The newest open page that `pred` holds for and that is none of `besides`."""
        def look():
            hit = [p for p in self.all_pages() if p not in besides and pred(p)]
            return hit[-1] if hit else None
        return wait_for(look, seconds)

    def fresh(self, pred, seconds: float = 30):
        """A page `pred` holds for, through a connection made now. WebView2 tells a connection of a
        window opened after it nothing, and gives a reloaded page a new target, so a page of another
        window, or one after a Restart, is found through a connection of its own (17 October)."""
        t0 = time.time()
        while time.time() - t0 < seconds:
            try:
                browser = self.pw.chromium.connect_over_cdp(f"http://127.0.0.1:{CDP}", timeout=30000)
            except Exception:  # noqa: BLE001  no window to reach, as after one closed the app with it
                time.sleep(1.5)
                continue
            for page in [p for c in browser.contexts for p in c.pages if not p.is_closed()]:
                try:
                    if pred(page):
                        self.others.append(browser)
                        return page
                except Exception:  # noqa: BLE001  a page going as it is asked
                    pass
            try:
                browser.close()
            except Exception:  # noqa: BLE001
                pass
            time.sleep(1.5)
        return None

    def main(self):
        """The main window's page as it is now, the one that holds the tag `main`."""
        own = f"http://127.0.0.1:{self.port}/"
        # a canvas print view, written into about:blank by the page, may report the page's own address
        return self.fresh(lambda p: p.url.split("#")[0] == own
                          and p.evaluate("document.querySelector('.cp-page') ? 'canvas' : (window.__driveTag || '')") in ("main", ""), 30)

    def disconnect(self) -> None:
        for browser in [self.browser, *self.others]:
            try:
                browser.close()
            except Exception:  # noqa: BLE001  the window may have gone
                pass
        self.log.flush()


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--exe", required=True)
    ap.add_argument("--stage", required=True)
    ap.add_argument("--shipped-config", required=True)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    from playwright.sync_api import sync_playwright

    out = Path(a.out).resolve()
    shots = out / "shots"
    shots.mkdir(parents=True, exist_ok=True)
    SAVED.append(out / "results.json")
    OUT.append(out)
    exe = Path(a.exe).resolve()
    name = exe.stem
    w = dc.make_world(out, Path(a.stage).resolve(), Path(a.shipped_config).resolve())
    note("exe", str(exe))
    downloads = Path(os.environ["USERPROFILE"]) / "Downloads"
    downloads.mkdir(exist_ok=True)
    stub = dc.Stub()
    # WebView2's debugging port, in this run's environment alone
    env = dc.app_env(dict(os.environ), w, WEBVIEW2_ADDITIONAL_BROWSER_ARGUMENTS=f"--remote-debugging-port={CDP}")
    pw = sync_playwright().start()

    # ── the first run: the screens, the print views, Share a copy and its failure, a link out, two windows, the edit keys,
    # a drop, a second start, Restart and Quit
    win = watched("start_1", 240, lambda: Window(exe, env, pw, out, "1"))
    page = win.page
    if page is None:
        desktop(shots / "win-no-page.png", out)
        note("stopped", "no page of the window's own reached through the debugging port")
        return 1
    note("start", {"server_and_port_s": win.server_s, "pages": win.pages()})
    attempt("page", lambda: ev(page, dc.PAGE_WAIT, 60), 90)
    # the page's own size, never one laid over it: the second build's checks set 1280 by 800 on a page
    # of 1280 by 780 below the menu bar, and every shot after showed its foot cut (17 October, the third
    # build), where the window now gives the page the size it asked for below the bar
    attempt("size_before", lambda: page.evaluate("[innerWidth, innerHeight, devicePixelRatio]"), 30)
    attempt("world", lambda: ev(page, dc.world_js(w).replace("return true;", "window.__driveTag = 'main'; return true;")), 60)
    for look in ("light", "dark"):
        attempt(f"theme_{look}", lambda look=look: ev(page, dc.THEME % json.dumps(look)), 60)
        for step in dc.SCREENS:
            attempt(f"{step}_{look}", lambda step=step: ev(page, dc.step_js(step)), 90)
            attempt(f"shot_{step}_{look}", lambda step=step, look=look: page.screenshot(path=str(shots / f"win-{step}-{look}.png")) and "saved", 60)
    attempt("theme_back", lambda: ev(page, dc.THEME % json.dumps("light")), 60)
    attempt("home", lambda: ev(page, dc.step_js("home")), 90)
    attempt("memory", lambda: memory(name), 60)

    # each print view in a window of its own, which prints the same way, its print panel taken from
    # the screen, then the window closed by its close button, with no call into its page after print
    # the canvas print view is the second build's two_canvas_print, which finds its window through the page
    # that opens it, where this one left it open unfound (17 October, the second build's fourth run)
    for view, body in ((v, b) for v, b in dc.PRINT_VIEWS.items() if v != "canvas_print"):
        def one(view=view, body=body):
            said = {"step": ev(page, dc.HEAD + body, 90)}
            look = (lambda p: "/themes/print" in p.url) if view == "pets_print" else \
                   (lambda p: "/gets/print" in p.url) if view == "gets_print" else \
                   (lambda p: p.url.startswith("about:blank"))
            view_page = win.fresh(look, 30)
            if view_page is None:
                return dict(said, opened=False, targets=[(t.get("type"), t.get("url", "")[:60]) for t in targets()],
                            windows=powershell(WINDOWS, name, "list", out=out))
            time.sleep(2.5)
            title = view_page.title()
            said.update(opened=True, url=view_page.url.split("?")[0], title=title,
                        size=view_page.evaluate("[innerWidth, innerHeight]"),
                        windows=powershell(WINDOWS, name, "list", out=out))
            view_page.screenshot(path=str(shots / f"win-{view}.png"))
            said["print"] = ev(view_page, dc.PRINT, 20)
            time.sleep(4)
            said["panel"] = desktop(shots / f"win-{view}-panel.png", out)
            said["closed"] = powershell(CLOSE_TITLE, title, out=out)
            time.sleep(2)
            said["after_close"] = powershell(WINDOWS, name, "list", out=out)
            return said
        attempt(view, one, 240)

    # a save: Share a copy of the whole project, Windows's own save panel with the file's name in it
    # (found by its title, the card's line), answered by Enter, and the file the server writes where the
    # panel put it, Downloads, its zip header checked (the PRISMA map's downloads were Sift's, an app of
    # its own since 20 October, as drive_mac.py's were until 3 November)
    def download():
        before = set(p.name for p in downloads.iterdir())
        said = {"step": ev(page, dc.SHARE, 60)}
        title = ev(page, SHARE_TITLE, 10)
        time.sleep(3)
        said["panel"] = desktop(shots / "win-save-panel.png", out)
        said["enter"] = powershell(KEYS, title, "{ENTER}", out=out)
        new = wait_for(lambda: sorted(n for n in set(p.name for p in downloads.iterdir()) - before
                                      if not n.startswith(".") and (downloads / n).stat().st_size), 30)
        said["saved"] = new
        if new:
            said["head"] = (downloads / new[0]).read_bytes()[:2].decode("latin-1")
        said["card"] = ev(page, dc.SHARE_SAID, 10)
        ev(page, dc.SHARE_CLOSE, 10)
        return said
    attempt("download", download, 180)

    # a save that fails: the panel told a name in a folder the user may not write to, which it takes, and
    # the server's write refused, the card kept open with its line that nothing was sent
    def save_fails():
        locked = out / "no-write-folder"
        locked.mkdir(exist_ok=True)
        said = {"lock": powershell(LOCK, str(locked), out=out)}
        try:
            said["step"] = ev(page, dc.SHARE, 60)
            title = ev(page, SHARE_TITLE, 10)
            time.sleep(3)
            said["panel"] = desktop(shots / "win-save-panel-again.png", out)
            target = locked / ((said["step"] or {}).get("name") or "Project.idiograph")
            said["typed"] = powershell(KEYS, title, sendkeys_text(str(target)) + "{ENTER}", out=out)
            said["card"] = wait_for(lambda: (lambda c: c if c and c.get("said") else None)(ev(page, dc.SHARE_SAID, 10)), 20)
            # the panel may itself refuse a folder it cannot write to, and stay open: said, then answered
            # with Escape so the run goes on
            said["panel_left"] = powershell(WINDOWS, name, "list", out=out)
            if title in said["panel_left"]:
                said["panel_refused"] = powershell(KEYS, title, "{ESC}", out=out)
            page.screenshot(path=str(shots / "win-save-failed.png"))
            said["file_made"] = sorted(p.name for p in locked.iterdir())
        finally:
            ev(page, dc.SHARE_CLOSE, 10)
            said["unlock"] = powershell(UNLOCK, str(locked), out=out)
        return said
    attempt("save_fails", save_fails, 180)

    # a link to another site opens in the default browser, which asks the stub on this machine
    def outside():
        t = time.time()
        said = {"page_still": ev(page, dc.OUTSIDE, 30)}
        said["visits"] = wait_for(lambda: (lambda v: v if len(v) >= 2 else None)([v["path"] for v in stub.visits if v["at"] >= t]), 45, 1) \
            or [v["path"] for v in stub.visits if v["at"] >= t]
        win.log.flush()
        said["window_said"] = [line.strip() for line in (out / "window-1.log").read_text(encoding="utf-8", errors="replace").splitlines()
                               if "outside link" in line]
        subprocess.run(["taskkill", "/IM", "msedge.exe", "/F"], capture_output=True)
        return said
    attempt("outside", outside, 120)

    # Cut, Copy, Paste, Select All, Undo and Redo by their keys in a text field
    def edit_keys():
        said = {"field": ev(page, EDIT_FIELD, 20)}
        kb = page.keyboard
        page.click("#drive-edit")
        kb.type("Wren Hollis")
        kb.press("Control+A")
        said["select_all"] = ev(page, EDIT_VALUE, 10)
        kb.press("Control+C")
        kb.press("End")
        kb.press("Control+V")
        said["copy_paste"] = ev(page, EDIT_VALUE, 10)
        kb.press("Control+Z")
        said["undo"] = ev(page, EDIT_VALUE, 10)
        kb.press("Control+Y")
        said["redo_ctrl_y"] = ev(page, EDIT_VALUE, 10)
        kb.press("Control+Z")
        kb.press("Control+Shift+Z")
        said["redo_ctrl_shift_z"] = ev(page, EDIT_VALUE, 10)
        kb.press("Control+A")
        kb.press("Control+X")
        said["cut"] = ev(page, EDIT_VALUE, 10)
        kb.press("Control+V")
        said["paste_back"] = ev(page, EDIT_VALUE, 10)
        ev(page, EDIT_DONE, 10)
        return said
    attempt("edit_keys", edit_keys, 120)

    # the second build's steps: the menus, About, the menus' items, the title, Choose, the page's height,
    # a drop decided by the drag's own answers, the canvas print view's print, a setting to keep
    build2.steps(sys.modules[__name__], win, page, w, name, shots, attempt, ev)
    # the page as it is now, since Reload from the View menu gave it a new target
    page = watched("page_again", 60, win.main) or page
    # the third build's steps: what the second build's screenshots found, read from the windows themselves
    build3.steps(sys.modules[__name__], win, name, shots, attempt)
    page = watched("page_again_3", 60, win.main) or page
    # the fourth build's steps: what the third build's screenshots found, Sift whole, a real drop the card
    # takes, and a second window on a screen of 1366 by 768
    build4.steps(sys.modules[__name__], win, w, name, shots, attempt)
    page = watched("page_again_4", 60, win.main) or page

    # a file dragged from another program onto the page is the second build's two_drop, which drops once the
    # page has said it takes a copy, where the first build's drag let go by the mouse ended as a dragleave

    # the page's own drop, through WebView2's own drag events with a real file's path: not a drag
    # from another program, which reaches the page but is let go as a dragleave on GitHub's machine
    def drop_cdp():
        ev(page, DROP_ARM, 10)
        ev(page, DROP_CARD, 10)
        cdp = page.context.new_cdp_session(page)
        data = {"items": [], "files": [str(w["world"] / "drop-me.csv")], "dragOperationsMask": 1}
        for kind in ("dragEnter", "dragOver", "drop"):
            cdp.send("Input.dispatchDragEvent", {"type": kind, "x": 640, "y": 400, "data": data})
            time.sleep(0.3)
        time.sleep(1)
        return ev(page, DROP_READ, 10)
    attempt("drop_cdp", drop_cdp, 60)

    # a second start: it ends at once, starts no server, and the open window comes forward
    def second_start():
        t = time.time()
        other = subprocess.run([str(exe)], env=env, capture_output=True, text=True, timeout=60)
        return {"exit": other.returncode, "seconds": round(time.time() - t, 2), "next_port_listening": dc.listening(dc.PORT + 1),
                "first_still_running": win.proc.poll() is None, "windows": powershell(WINDOWS, name, "list", out=out)}
    attempt("second_start", second_start, 120)

    # two windows by Ctrl+N, a case in each, the second found through a connection of its own
    def two():
        live = win.main() or page
        # the main page tagged again, since Reload took its tag and a fresh connection then took it for
        # the new window, so build 2's shots showed one page twice (17 October, the third build)
        cdp_ev(live, "window.__driveTag = 'main'; return true;", 10)
        live.keyboard.press("Control+N")
        own = f"http://127.0.0.1:{dc.PORT}/"
        second = win.fresh(lambda p: p.url.split("#")[0] == own and p.evaluate("window.__driveTag || ''") == "", 30)
        if second is None:
            return {"opened": False, "targets": [(t.get("type"), t.get("url", "")[:60]) for t in targets()],
                    "windows": powershell(WINDOWS, name, "list", out=out)}
        cdp_ev(second, dc.world_js(w).replace("return true;", "window.__driveTag = 'second'; return true;"), 20)
        said = {"page": cdp_ev(second, dc.PAGE_WAIT, 60)}
        said["main"] = ev(live, dc.CASE % json.dumps("Rowan"), 60)
        said["second"] = cdp_ev(second, dc.CASE % json.dumps("Mabel"), 60)
        time.sleep(1.5)
        said["titles"] = build2.bar(sys.modules[__name__], name, "titles")
        said["bars"] = build3.read(sys.modules[__name__], name, "bars")
        said["second_fits"] = build3.page_and_client(sys.modules[__name__], second, name, "Mabel")
        second.screenshot(path=str(shots / "win-two-windows-second.png"))
        live.screenshot(path=str(shots / "win-two-windows-main.png"))
        said["windows"] = powershell(WINDOWS, name, "list", out=out)
        said["desktop"] = desktop(shots / "win-two-windows-desktop.png", out)
        return said
    attempt("two_windows", two, 300)

    # Restart in Settings: Windows starts the server anew, and the window waits for it and stays. The
    # server is asked from here, never the page while it reloads
    def restart():
        build2.clear_dialogs(sys.modules[__name__], name)
        before = server_started()
        ev(page, dc.RESTART, 10)
        after = wait_for(lambda: (lambda s: s if s and s != before else None)(server_started()), 60, 1)
        note("restart_server", {"before": before, "after": after})
        time.sleep(3)
        said = {"before": before, "after": after, "window_running": win.proc.poll() is None,
                "windows": powershell(WINDOWS, name, "list", out=out), "listening": dc.listening(dc.PORT)}
        # each window's page back on its case, waited for by its title, and the screen taken, since the third
        # build's third run found the main window titled Idiograph after a Restart and its page unreached
        said["back"] = wait_for(lambda: (lambda t: t if t.count("Experiential statements") >= 2 else None)(
            powershell(WINDOWS, name, "list", out=out)), 60, 2) or powershell(WINDOWS, name, "list", out=out)
        said["desktop"] = desktop(shots / "win-after-restart.png", out)
        back = win.fresh(lambda p: p.url.split("#")[0] == f"http://127.0.0.1:{dc.PORT}/" and "Rowan" in p.title(), 30) or win.main()
        said["page"] = ev(back, "return { title: document.title, ready: document.readyState, quit: typeof serverOp };", 30) \
            if back is not None else "no page found"
        return said
    attempt("restart", restart, 240)



    # Quit in Settings: the server ends, then the window, then the app
    def quit_():
        t = time.time()
        live = win.fresh(lambda p: p.url.split("#")[0] == f"http://127.0.0.1:{dc.PORT}/" and "Rowan" in p.title(), 20) or win.main()
        try:
            ev(live, dc.QUIT.replace("serverOp('quit')", "setTimeout(function () { serverOp('quit'); }, 200)"), 10)
        except Exception as exc:  # noqa: BLE001  the page may go as the window closes
            print(f"quit: {exc}")
        gone = dc.wait_closed(dc.PORT, 20)
        how = "the page's Quit"
        if gone < 0:
            # the page's Quit could not be reached after the Restart, so Quit is asked of the server
            # as the page asks it, the window's part, closing with the server, the same
            how = "Quit asked of the server from here"
            req = urllib.request.Request(f"http://127.0.0.1:{dc.PORT}/api/server", data=b'{"op":"quit"}', method="POST",
                                         headers={"Host": f"127.0.0.1:{dc.PORT}", "Content-Type": "application/json"})
            try:
                urllib.request.build_opener(urllib.request.ProxyHandler({})).open(req, timeout=10).read()
            except OSError as exc:
                how += f", {exc}"
            gone = dc.wait_closed(dc.PORT, 40)
        try:
            code = win.proc.wait(timeout=40)
        except subprocess.TimeoutExpired:
            code = "still running"
        return {"how": how, "server_gone_s": gone, "exit": code, "seconds": round(time.time() - t, 2),
                "windows_after": powershell(WINDOWS, name, "list", out=out)}
    attempt("quit", quit_, 150)
    win.disconnect()

    # ── the second run: the main window's print, its panel from the screen, then the last window
    # closed by its close button, which ends the app and the server
    def print_and_last_window():
        other = Window(exe, env, pw, out, "2")
        live = other.page
        said = {"page": ev(live, dc.PAGE_WAIT, 60)}
        said["print"] = ev(live, dc.PRINT, 20)
        time.sleep(4)
        said["panel"] = desktop(shots / "win-print-panel.png", out)
        powershell(KEYS, "Print", "{ESC}", out=out)
        time.sleep(1.5)
        said["kept"] = build2.before_last_close(sys.modules[__name__], other, name, shots, ev)
        other.disconnect()
        t = time.time()
        said["closed"] = powershell(WINDOWS, name, "close", out=out)
        said["server_gone_s"] = dc.wait_closed(dc.PORT, 45)
        try:
            said["exit"] = other.proc.wait(timeout=45)
        except subprocess.TimeoutExpired:
            said["exit"] = "still running"
        said["seconds"] = round(time.time() - t, 2)
        return said
    attempt("print_and_last_window", print_and_last_window, 300)
    # the third and fourth runs: where the window was, on another port, Exit, and a server ended from outside
    build2.third_run(sys.modules[__name__], exe, env, pw, out, name, shots, attempt, ev, dc.PORT + 1)
    pw.stop()

    # the command line and the MCP server from the install, as Claude Desktop runs them
    def mcp():
        msgs = "\n".join(json.dumps(m) for m in (
            {"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {"protocolVersion": "2025-06-18", "capabilities": {}, "clientInfo": {"name": "drive", "version": "0"}}},
            {"jsonrpc": "2.0", "method": "notifications/initialized"},
            {"jsonrpc": "2.0", "id": 2, "method": "tools/list"})) + "\n"
        said = {}
        for label, path in (("window_exe", exe), ("console_twin", exe.parent / "server" / "Idiograph-console.exe")):
            done = subprocess.run([str(path), "mcp", "--root", str(w["project"]), "--config", str(w["config"])],
                                  input=msgs, capture_output=True, text=True, encoding="utf-8", timeout=60)
            lines = [json.loads(x) for x in done.stdout.splitlines() if x.strip().startswith("{")]
            tools = next((len(m["result"].get("tools", [])) for m in lines if m.get("id") == 2 and "result" in m), None)
            said[label] = {"exit": done.returncode, "answers": len(lines), "tools": tools}
        cli = subprocess.run([str(exe), "cli", "cases", "--root", str(w["project"]), "--config", str(w["config"])],
                             capture_output=True, text=True, encoding="utf-8", timeout=60)
        said["cli_cases"] = {"exit": cli.returncode, "out": cli.stdout.strip().splitlines()[:4], "err": cli.stderr.strip()[-400:]}
        return said
    attempt("mcp_and_cli", mcp, 180)

    logs = Path(os.environ["LOCALAPPDATA"]) / "Idiograph" / "Logs" / "idiograph.log"
    attempt("log", lambda: [line for line in logs.read_text(encoding="utf-8", errors="replace").splitlines() if line.startswith("===")][-6:], 30)
    # a Restart's ended server logged a ConnectionAbortedError traceback before the second build
    attempt("log_tracebacks", lambda: [line for line in logs.read_text(encoding="utf-8", errors="replace").splitlines()
                                       if "Traceback" in line or "ConnectionAbortedError" in line][-6:], 30)
    stub.close()
    note("port_closed_at_end", not dc.listening(dc.PORT))
    return 0


if __name__ == "__main__":
    sys.exit(main())
