"""The third build's steps of the Windows check (17 October 2026), which `drive_windows.py` runs after the
second build's: what the second build's screenshots found, each read from the window itself rather than
judged from a picture. The page's height against the window's own client area below its menu bar, every
window's menu bar, the print views' among them, About's words, the folder dialog's title, Settings' word
for quitting and the statements screen's title by the case. Windows's own parts are read through
user32 from PowerShell, as the second build's steps read them.
"""
from __future__ import annotations

import json
import time
from pathlib import Path

# the app's top-level windows read through user32: `client <title part>` says a window's client area and
# whether it has a menu bar, `bars` every visible window of the app with whether it carries a menu bar, `dialog` a dialog's
# own title and words. A menu's own words cannot be read here, since muda draws its items itself, so the
# second build's pictures of each menu show them
READ = r"""
Add-Type -TypeDefinition @'
using System; using System.Text; using System.Runtime.InteropServices; using System.Collections.Generic;
public static class Read3 {
  [StructLayout(LayoutKind.Sequential)] public struct R { public int L, T, Rt, B; }
  public delegate bool EnumProc(IntPtr h, IntPtr l);
  [DllImport("user32.dll")] static extern bool EnumWindows(EnumProc f, IntPtr l);
  [DllImport("user32.dll")] static extern bool EnumChildWindows(IntPtr p, EnumProc f, IntPtr l);
  [DllImport("user32.dll")] static extern bool IsWindowVisible(IntPtr h);
  [DllImport("user32.dll")] static extern uint GetWindowThreadProcessId(IntPtr h, out uint pid);
  [DllImport("user32.dll", CharSet = CharSet.Unicode)] static extern int GetWindowText(IntPtr h, StringBuilder s, int n);
  [DllImport("user32.dll", CharSet = CharSet.Unicode)] static extern int GetClassName(IntPtr h, StringBuilder s, int n);
  [DllImport("user32.dll")] static extern IntPtr GetMenu(IntPtr h);
  [DllImport("user32.dll")] static extern bool GetClientRect(IntPtr h, out R r);
  [DllImport("user32.dll")] static extern uint GetDpiForWindow(IntPtr h);
  static string Text(IntPtr h) { var sb = new StringBuilder(512); GetWindowText(h, sb, 512); return sb.ToString(); }
  static string Kind(IntPtr h) { var sb = new StringBuilder(64); GetClassName(h, sb, 64); return sb.ToString(); }
  static List<IntPtr> Tops(int[] pids) {
    var set = new HashSet<int>(pids); var found = new List<IntPtr>();
    EnumWindows((h, l) => { uint pid; GetWindowThreadProcessId(h, out pid);
      if (set.Contains((int)pid) && IsWindowVisible(h) && Text(h).Length > 0 && !Text(h).EndsWith("-siw")) found.Add(h); return true; }, IntPtr.Zero);
    return found;
  }
  public static string Run(int[] pids, string op, string part) {
    var tops = Tops(pids);
    if (op == "bars") { var all = new List<string>(); foreach (var h in tops) all.Add(Text(h) + (GetMenu(h) != IntPtr.Zero ? " [menu bar]" : " [no menu bar]")); return string.Join(" | ", all); }
    if (op == "dialog") {
      var said = new List<string>();
      foreach (var h in tops) { if (Kind(h) != "#32770") continue; said.Add("title: " + Text(h));
        EnumChildWindows(h, (c, l) => { var t = Text(c); if (t.Length > 0) said.Add(t); return true; }, IntPtr.Zero); }
      return said.Count == 0 ? "none" : string.Join(" | ", said);
    }
    IntPtr w = IntPtr.Zero;
    foreach (var h in tops) if (part == "*" ? GetMenu(h) != IntPtr.Zero : Text(h).Contains(part)) { w = h; break; }
    if (w == IntPtr.Zero) return "none";
    if (op == "client") { R r; GetClientRect(w, out r); return (r.Rt - r.L) + " " + (r.B - r.T) + " " + GetDpiForWindow(w) + " " + (GetMenu(w) != IntPtr.Zero ? "menu" : "nomenu") + " " + Text(w); }
    return "op?";
  }
}
'@
$ids = [int[]]@(Get-Process -Name $args[0] -ErrorAction SilentlyContinue | ForEach-Object { $_.Id })
[Read3]::Run($ids, $args[1], $args[2])
"""


def read(dw, name: str, op: str, part: str = "*") -> str:
    return dw.powershell(READ, name, op, part, out=dw.OUT[0], timeout=90)


def page_and_client(dw, page, name: str, part: str) -> dict:
    """A window's page size against its client area, both in pixels, so a page cut by the menu bar shows
    as a page taller than the area that holds it."""
    inner = dw.cdp_ev(page, "return [innerWidth, innerHeight, devicePixelRatio, document.title];", 10)
    client = read(dw, name, "client", part).split(" ", 4)
    said = {"page": inner, "client": client}
    try:
        dpr = float(inner[2])
        said["fits"] = abs(round(inner[1] * dpr) - int(client[1])) <= 2 and abs(round(inner[0] * dpr) - int(client[0])) <= 2
    except (TypeError, ValueError, IndexError):
        said["fits"] = None
    return said


def steps(dw, win, name: str, shots: Path, attempt) -> None:
    """The third build's steps, on the first run's windows, after the second build's."""
    two = dw.build2

    def sizes():
        live = win.main()
        # the PETs board, a screen of Idiograph's own (Sift's page is an app of its own since 20 October)
        dw.cdp_ev(live, dw.dc.step_js("pets"), 90)
        said = {"main": page_and_client(dw, live, name, live.title() or "Idiograph")}
        dw.desktop(shots / "win-three-pets-whole.png", dw.OUT[0])
        dw.cdp_ev(live, dw.dc.step_js("home"), 60)
        return said
    attempt("three_page_fits", sizes, 180)

    def about():
        two.clear_dialogs(dw, name)
        two.by_menu(dw, name, "h", "a", 2.0)
        said = {"dialog": read(dw, name, "dialog")}
        dw.desktop(shots / "win-three-about.png", dw.OUT[0])
        two.clear_dialogs(dw, name)
        return said
    attempt("three_about", about, 90)

    def quit_word():
        live = win.main()
        return dw.cdp_ev(live, "await loadLibrary(); openSettings(); await new Promise(function (r) { setTimeout(r, 1200); });"
                               "var b = document.getElementById('server-quit'); var t = b.textContent; hide('settings');"
                               "return { word: t, shown: !b.hidden, os: window.__IDIOGRAPH_OS__ };", 30)
    attempt("three_quit_word", quit_word, 60)

    def title():
        live = win.main()
        dw.cdp_ev(live, dw.dc.CASE % json.dumps("Rowan"), 60)
        time.sleep(1.5)
        said = {"page": dw.cdp_ev(live, "return document.title;", 10), "windows": two.bar(dw, name, "titles")}
        dw.cdp_ev(live, dw.dc.step_js("home"), 60)
        return said
    attempt("three_title", title, 120)

    def choose_title():
        live = win.main()
        dw.cdp_ev(live, "openNewProject(); setTimeout(function () { document.getElementById('np-choose').click(); }, 200); return true;", 20)
        time.sleep(3)
        said = {"windows": dw.powershell(dw.WINDOWS, name, "list", out=dw.OUT[0])}
        dw.ps_press("{ESC}")
        time.sleep(1)
        two.clear_dialogs(dw, name)
        dw.cdp_ev(live, "hide('newproject'); return true;", 10)
        return said
    attempt("three_choose_title", choose_title, 90)

    def print_bars():
        """Each print view's window, and the manual's, with its menu bar, read once each is open."""
        live = win.main()
        said = {}
        for view in ("pets_print", "gets_print"):
            dw.cdp_ev(live, dw.dc.HEAD + dw.dc.PRINT_VIEWS[view], 120)
            time.sleep(2.5)
            said[view] = read(dw, name, "bars")
            title = next((t.rsplit(" [", 1)[0] for t in said[view].split(" | ") if "Board" in t), "")
            if title:
                said[f"{view}_client"] = read(dw, name, "client", title)
                dw.powershell(dw.CLOSE_TITLE, title, out=dw.OUT[0])
                time.sleep(1.5)
        two.by_menu(dw, name, "h", "m", 3.0)
        said["manual"] = read(dw, name, "bars")
        dw.desktop(shots / "win-three-manual.png", dw.OUT[0])
        manual = next((t.rsplit(" [", 1)[0] for t in said["manual"].split(" | ") if "anual" in t), "")
        if manual:
            dw.powershell(dw.CLOSE_TITLE, manual, out=dw.OUT[0])
        return said
    attempt("three_print_bars", print_bars, 300)
