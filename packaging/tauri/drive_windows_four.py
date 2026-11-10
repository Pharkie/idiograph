"""The fourth build's steps of the Windows check (18 October 2026), which `drive_windows.py` runs after the
third build's: what the third build's screenshots found. Sift's page whole below the menu bar, taken again
with the world the page needs set first, since the third build's picture showed a PETs board left there
when Sift did not open; a file dragged from another program onto the New project card, taken again with
the check's listener hearing the drop without taking it (drive_windows.py's DROP_ARM), since it had
swallowed the drop and the card stood empty; and a second window on a screen of 1366 by 768, where the second build's stepped 196 pixels down
with its foot under the taskbar. Windows's own parts are read through user32 from PowerShell, as the
earlier builds' steps read them.
"""
from __future__ import annotations

import json
import re
import time
from pathlib import Path

# the primary screen's size and the part of it the taskbar leaves, and with a size the screen set to it
SCREEN = r"""
Add-Type -AssemblyName System.Windows.Forms
if ($args.Count -ge 2) { Set-DisplayResolution -Width ([int]$args[0]) -Height ([int]$args[1]) -Force -ErrorAction SilentlyContinue; Start-Sleep -Seconds 3 }
$s = [System.Windows.Forms.Screen]::PrimaryScreen
"$($s.Bounds.Width) $($s.Bounds.Height) $($s.WorkingArea.X) $($s.WorkingArea.Y) $($s.WorkingArea.Width) $($s.WorkingArea.Height)"
"""

# every visible window of the app's own with its rectangle, `left top width height title` a line
RECTS = r"""
Add-Type -TypeDefinition @'
using System; using System.Text; using System.Runtime.InteropServices; using System.Collections.Generic;
public static class Rects4 {
  [StructLayout(LayoutKind.Sequential)] public struct R { public int L, T, Rt, B; }
  public delegate bool EnumProc(IntPtr h, IntPtr l);
  [DllImport("user32.dll")] static extern bool EnumWindows(EnumProc f, IntPtr l);
  [DllImport("user32.dll")] static extern bool IsWindowVisible(IntPtr h);
  [DllImport("user32.dll")] static extern uint GetWindowThreadProcessId(IntPtr h, out uint pid);
  [DllImport("user32.dll", CharSet = CharSet.Unicode)] static extern int GetWindowText(IntPtr h, StringBuilder s, int n);
  [DllImport("dwmapi.dll")] static extern int DwmGetWindowAttribute(IntPtr h, int a, out R r, int size);
  public static string Run(int[] pids) {
    var set = new HashSet<int>(pids); var found = new List<string>();
    EnumWindows((h, l) => { uint pid; GetWindowThreadProcessId(h, out pid);
      var sb = new StringBuilder(256); GetWindowText(h, sb, 256);
      if (set.Contains((int)pid) && IsWindowVisible(h) && sb.Length > 0 && !sb.ToString().EndsWith("-siw")) {
        R r; DwmGetWindowAttribute(h, 9, out r, Marshal.SizeOf(typeof(R)));
        found.Add(r.L + " " + r.T + " " + (r.Rt - r.L) + " " + (r.B - r.T) + " " + sb.ToString()); }
      return true; }, IntPtr.Zero);
    return string.Join("\n", found);
  }
}
'@
$ids = [int[]]@(Get-Process -Name $args[0] -ErrorAction SilentlyContinue | ForEach-Object { $_.Id })
[Rects4]::Run($ids)
"""

# the visible window with exactly this title brought in front of the others, put on top and let go again,
# so nothing else is asked of it (the sixth build)
FRONT = r"""
Add-Type -TypeDefinition @'
using System; using System.Text; using System.Runtime.InteropServices;
public static class Front6 {
  public delegate bool EnumProc(IntPtr h, IntPtr l);
  [DllImport("user32.dll")] static extern bool EnumWindows(EnumProc f, IntPtr l);
  [DllImport("user32.dll")] static extern bool IsWindowVisible(IntPtr h);
  [DllImport("user32.dll", CharSet = CharSet.Unicode)] static extern int GetWindowText(IntPtr h, StringBuilder s, int n);
  [DllImport("user32.dll")] static extern bool SetWindowPos(IntPtr h, IntPtr after, int x, int y, int cx, int cy, uint flags);
  [DllImport("user32.dll")] static extern bool SetForegroundWindow(IntPtr h);
  public static string Run(string title) {
    var hit = IntPtr.Zero;
    EnumWindows((h, l) => { var sb = new StringBuilder(256); GetWindowText(h, sb, 256);
      if (IsWindowVisible(h) && sb.ToString() == title) { hit = h; return false; } return true; }, IntPtr.Zero);
    if (hit == IntPtr.Zero) return "none";
    // SWP_NOMOVE | SWP_NOSIZE | SWP_SHOWWINDOW, on top and then not, so it stays in front
    SetWindowPos(hit, (IntPtr)(-1), 0, 0, 0, 0, 0x0043);
    SetWindowPos(hit, (IntPtr)(-2), 0, 0, 0, 0, 0x0043);
    SetForegroundWindow(hit);
    return "front " + title;
  }
}
'@
[Front6]::Run($args[0])
"""

# two pictures of the screen side by side, each with its caption above it: what the picture shows, so the
# pair reads as one (the sixth build's second window, each of the two in front in turn)
PAIR = r"""
param([string]$left, [string]$right, [string]$out, [string]$leftSaid, [string]$rightSaid)
Add-Type -AssemblyName System.Drawing
$a = [System.Drawing.Image]::FromFile($left)
$b = [System.Drawing.Image]::FromFile($right)
$band = 44
$gap = 24
$bmp = New-Object System.Drawing.Bitmap ($a.Width + $gap + $b.Width), ($band + [Math]::Max($a.Height, $b.Height))
$g = [System.Drawing.Graphics]::FromImage($bmp)
$g.Clear([System.Drawing.Color]::White)
$g.TextRenderingHint = [System.Drawing.Text.TextRenderingHint]::AntiAliasGridFit
$font = New-Object System.Drawing.Font("Segoe UI", 22, [System.Drawing.FontStyle]::Bold, [System.Drawing.GraphicsUnit]::Pixel)
$ink = New-Object System.Drawing.SolidBrush ([System.Drawing.Color]::FromArgb(255, 31, 27, 22))
$g.DrawString($leftSaid, $font, $ink, 4, 8)
$g.DrawString($rightSaid, $font, $ink, ($a.Width + $gap + 4), 8)
$g.DrawImage($a, 0, $band, $a.Width, $a.Height)
$g.DrawImage($b, ($a.Width + $gap), $band, $b.Width, $b.Height)
$bmp.Save($out, [System.Drawing.Imaging.ImageFormat]::Png)
"$($bmp.Width) by $($bmp.Height), band $band, gap $gap, left $($a.Width)"
"""

DROP_CARD_ROWS = ("return { rows: (typeof NP !== 'undefined' && NP.rows) ? NP.rows.map(function (r) { return r.file + (r.said ? ': ' + r.said : ''); }) : null, "
                  "shown: Array.prototype.map.call(document.querySelectorAll('#np-rows .np-row'), function (li) { return li.textContent.trim().slice(0, 80); }), "
                  "drops: window.__drops, enter: window.__enter, over: window.__over, leave: window.__leave };")


def screen(dw, *size: int) -> list[int]:
    """The primary screen's width and height and its work area, read from the line of six numbers the
    script says, whatever else setting the screen printed (the fourth build's first run read none)."""
    said = dw.powershell(SCREEN, *[str(n) for n in size], out=dw.OUT[0], timeout=90)
    lines = re.findall(r"^(-?\d+) (-?\d+) (-?\d+) (-?\d+) (-?\d+) (-?\d+)\s*$", said, re.M)
    return [int(n) for n in lines[-1]] if lines else []


def rects(dw, name: str) -> list[dict]:
    lines = dw.powershell(RECTS, name, out=dw.OUT[0], timeout=90).splitlines()
    found = []
    for line in lines:
        parts = line.split(" ", 4)
        if len(parts) == 5 and all(p.lstrip("-").isdigit() for p in parts[:4]):
            found.append({"left": int(parts[0]), "top": int(parts[1]), "width": int(parts[2]), "height": int(parts[3]), "title": parts[4]})
    return found


def inside(rect: dict, area: list[int]) -> bool:
    """Whether a window stands whole in the screen's work area, a pixel or two of its frame's shadow aside."""
    ax, ay, aw, ah = area[2:6]
    return (rect["left"] >= ax - 2 and rect["top"] >= ay - 2 and rect["left"] + rect["width"] <= ax + aw + 2
            and rect["top"] + rect["height"] <= ay + ah + 2)


def steps(dw, win, w: dict, name: str, shots: Path, attempt) -> None:
    """The fourth build's steps, on the first run's windows, after the third build's."""
    two, three = dw.build2, dw.build3

    def pets_whole():
        live = win.main()
        # the world the page's steps need, which a reload of the page had taken (the third build's picture)
        dw.cdp_ev(live, dw.dc.world_js(w), 10)
        # the PETs board whole below the menu bar (it was Sift's page, an app of its own since 20 October)
        said = {"step": dw.cdp_ev(live, dw.dc.step_js("pets"), 90)}
        said["screen"] = dw.cdp_ev(live, "return { board: !!document.querySelector('#th-step-gets'), title: document.title };", 10)
        said["fits"] = three.page_and_client(dw, live, name, live.title() or "Idiograph")
        dw.desktop(shots / "win-pets-whole.png", dw.OUT[0])
        dw.cdp_ev(live, dw.dc.step_js("home"), 60)
        return said
    attempt("four_pets_whole", pets_whole, 180)

    def real_drop():
        live = win.main()
        dw.cdp_ev(live, dw.dc.step_js("home"), 60)
        dw.cdp_ev(live, dw.DROP_ARM, 10)
        card = dw.cdp_ev(live, dw.DROP_CARD, 10)
        rect = two.bar(dw, name, "rect").split()
        left, top, width, height = (int(n) for n in rect[:4])
        dragged = two.ps(dw, two.DRAGGER2, str(w["world"] / "drop-me.csv"), str(left + width // 2), str(top + height // 2), timeout=60)
        time.sleep(2.5)
        said = {"card": card, "dragger": dragged, "page": dw.cdp_ev(live, DROP_CARD_ROWS, 10)}
        dw.desktop(shots / "win-real-drop.png", dw.OUT[0])
        dw.cdp_ev(live, "hide('newproject'); return true;", 10)
        return said
    attempt("four_real_drop", real_drop, 180)

    def second_window_small():
        said = {"screen_before": screen(dw)}
        # read again without setting it when the setting's own words left no line of numbers (the fifth
        # build's first run, whose screen did change)
        said["screen"] = screen(dw, 1366, 768) or screen(dw)
        live = win.main()
        dw.cdp_ev(live, "window.__driveTag = 'main'; return true;", 10)
        dw.cdp_ev(live, dw.dc.step_js("home"), 60)
        said["before"] = rects(dw, name)
        live.keyboard.press("Control+N")
        time.sleep(4)
        # the second window on a case of its own, so the two tell apart by their titles, and closed by its own
        # title alone, where the first run's closed both windows of one title and the app with them
        own = f"http://127.0.0.1:{dw.dc.PORT}/"
        second = win.fresh(lambda p: p.url.split("#")[0] == own and p.evaluate("window.__driveTag || ''") == "", 20)
        if second is not None:
            dw.cdp_ev(second, dw.dc.world_js(w).replace("return true;", "window.__driveTag = 'second'; return true;"), 20)
            said["second_case"] = dw.cdp_ev(second, dw.dc.CASE % json.dumps("Mabel"), 60)
            time.sleep(1.5)
        said["after"] = rects(dw, name)
        area = said["screen"]
        said["whole"] = {r["title"]: inside(r, area) for r in said["after"]} if len(area) == 6 else "no screen read"
        dw.desktop(shots / "win-second-window-1366.png", dw.OUT[0])
        mabel = next((r["title"] for r in said["after"] if r["title"].startswith("Mabel")), "")
        # the first window brought in front too and taken again, so each of the two shows whole in a picture
        # of its own, and the pair side by side, where the fifth build's one picture showed the second over
        # nearly all of the first (the sixth build, 18 October, the screenshot check)
        first = next((r["title"] for r in said["after"] if not r["title"].startswith("Mabel")), "")
        if first:
            said["first_in_front"] = dw.powershell(FRONT, first, out=dw.OUT[0])
            time.sleep(1.5)
            said["after_first_in_front"] = rects(dw, name)
            dw.desktop(shots / "win-second-window-1366-first.png", dw.OUT[0])
            said["pair"] = dw.powershell(PAIR, str(shots / "win-second-window-1366.png"),
                                         str(shots / "win-second-window-1366-first.png"),
                                         str(shots / "win-second-window-1366-both.png"),
                                         "The second window, in front", "The first window, brought in front", out=dw.OUT[0])
        if mabel:
            said["closed"] = dw.powershell(dw.CLOSE_TITLE, mabel, out=dw.OUT[0])
            time.sleep(2)
        said["screen_after"] = screen(dw, 1920, 1080)
        return said
    attempt("four_second_window_1366", second_window_small, 240)


def notice_words(dw, name: str) -> str:
    """The words of the notice standing open, its title and every line, for the crash notice's step."""
    return dw.build3.read(dw, name, "dialog")

