"""The second build's steps of the Windows check (17 October, later), which `drive_windows.py` runs: the menu
bar of each window, About, the menus' items on the page, the zoom, the title, Choose, a real drop from
another program, the canvas print view's print, the window's size and place and its page kept across a
quit, the page's settings across a change of port, Exit from the menu, and the notice when the server ends
without a word. Windows's own parts are driven through user32 from PowerShell, a menu opened as Alt and its
letter opens it, through WM_SYSCOMMAND, so the web view's own handling of keys never stands between.
"""
from __future__ import annotations

import json
import time
from pathlib import Path

# the app's top-level windows that carry a menu bar, by title, and with an order: `open <title part>
# <letter>` opens that window's menu by its letter, `rect <title part>` says its rectangle, `move <title
# part> x y w h` moves it, `close <title part>` closes it as its close button does, `popup` says whether a
# menu stands open
MENUS = r"""
Add-Type -TypeDefinition @'
using System; using System.Text; using System.Runtime.InteropServices; using System.Collections.Generic;
public static class Bar {
  [StructLayout(LayoutKind.Sequential)] public struct R { public int L, T, Rt, B; }
  public delegate bool EnumProc(IntPtr h, IntPtr l);
  [DllImport("user32.dll")] static extern bool EnumWindows(EnumProc f, IntPtr l);
  [DllImport("user32.dll")] static extern bool IsWindowVisible(IntPtr h);
  [DllImport("user32.dll")] static extern uint GetWindowThreadProcessId(IntPtr h, out uint pid);
  [DllImport("user32.dll", CharSet = CharSet.Unicode)] static extern int GetWindowText(IntPtr h, StringBuilder s, int n);
  [DllImport("user32.dll", CharSet = CharSet.Unicode)] static extern int GetClassName(IntPtr h, StringBuilder s, int n);
  [DllImport("user32.dll")] static extern IntPtr GetMenu(IntPtr h);
  [DllImport("user32.dll")] static extern int GetMenuItemCount(IntPtr m);
  [DllImport("user32.dll", CharSet = CharSet.Unicode)] static extern int GetMenuString(IntPtr m, uint id, StringBuilder s, int n, uint flags);
  [DllImport("user32.dll")] static extern bool GetWindowRect(IntPtr h, out R r);
  [DllImport("user32.dll")] static extern bool SetForegroundWindow(IntPtr h);
  [DllImport("user32.dll")] static extern bool PostMessage(IntPtr h, uint m, IntPtr w, IntPtr l);
  [DllImport("user32.dll")] static extern bool SetWindowPos(IntPtr h, IntPtr after, int x, int y, int cx, int cy, uint flags);
  public static List<IntPtr> Mine(int[] pids, string part) {
    var set = new HashSet<int>(pids); var found = new List<IntPtr>();
    EnumWindows((h, l) => {
      uint pid; GetWindowThreadProcessId(h, out pid);
      if (set.Contains((int)pid) && IsWindowVisible(h) && GetMenu(h) != IntPtr.Zero) {
        var sb = new StringBuilder(256); GetWindowText(h, sb, 256);
        if (part == "*" || sb.ToString().Contains(part)) found.Add(h);
      }
      return true; }, IntPtr.Zero);
    return found;
  }
  public static string Title(IntPtr h) { var sb = new StringBuilder(256); GetWindowText(h, sb, 256); return sb.ToString(); }
  public static string Run(int[] pids, string op, string part, string[] more) {
    if (op == "dialog") {
      var said = "none";
      var set = new HashSet<int>(pids);
      EnumWindows((h, l) => {
        uint pid; GetWindowThreadProcessId(h, out pid); var c = new StringBuilder(64); GetClassName(h, c, 64);
        if (set.Contains((int)pid) && c.ToString() == "#32770" && IsWindowVisible(h)) { said = Title(h); if (part == "close") PostMessage(h, 0x0010, IntPtr.Zero, IntPtr.Zero); }
        return true; }, IntPtr.Zero);
      return said;
    }
    if (op == "popup") {
      var open = new List<string>();
      EnumWindows((h, l) => { var c = new StringBuilder(64); GetClassName(h, c, 64); if (c.ToString() == "#32768" && IsWindowVisible(h)) open.Add("menu"); return true; }, IntPtr.Zero);
      return open.Count.ToString();
    }
    var hits = Mine(pids, part);
    if (hits.Count == 0) return "none";
    var w = hits[0];
    if (op == "titles") { var all = new List<string>(); foreach (var h in hits) all.Add(Title(h)); return string.Join(" | ", all); }
    if (op == "bar") {
      var m = GetMenu(w); var n = GetMenuItemCount(m); var names = new List<string>();
      for (uint i = 0; i < n; i++) { var sb = new StringBuilder(64); GetMenuString(m, i, sb, 64, 0x400); names.Add(sb.ToString()); }
      return string.Join(" | ", names);
    }
    if (op == "rect") { R r; GetWindowRect(w, out r); return r.L + " " + r.T + " " + (r.Rt - r.L) + " " + (r.B - r.T) + " " + Title(w); }
    if (op == "move") { SetWindowPos(w, IntPtr.Zero, int.Parse(more[0]), int.Parse(more[1]), int.Parse(more[2]), int.Parse(more[3]), 0x0004); R r; GetWindowRect(w, out r); return r.L + " " + r.T + " " + (r.Rt - r.L) + " " + (r.B - r.T); }
    if (op == "close") { PostMessage(w, 0x0010, IntPtr.Zero, IntPtr.Zero); return "closed " + Title(w); }
    if (op == "open") { SetForegroundWindow(w); System.Threading.Thread.Sleep(300); PostMessage(w, 0x0112, (IntPtr)0xF100, (IntPtr)(int)more[0][0]); return "opened " + Title(w); }
    return "op?";
  }
}
'@
$ids = [int[]]@(Get-Process -Name $args[0] -ErrorAction SilentlyContinue | ForEach-Object { $_.Id })
$more = @(); if ($args.Count -gt 3) { $more = $args[3..($args.Count - 1)] }
[Bar]::Run($ids, $args[1], $args[2], [string[]]$more)
"""

# keys pressed into whatever has the keyboard, a menu standing open among them
PRESS = r"""
Add-Type -AssemblyName System.Windows.Forms
Start-Sleep -Milliseconds 300
[System.Windows.Forms.SendKeys]::SendWait($args[0])
"ok"
"""

# a file dragged from a form of this machine's own onto the window, the drop decided by the drag's own
# answers rather than the mouse button: it waits until the page has said it takes a copy, then drops, so
# a dragleave can only mean the page or the web view refused it (17 October, the second build)
DRAGGER2 = r"""
Add-Type -ReferencedAssemblies System.Windows.Forms, System.Drawing -TypeDefinition @'
using System; using System.Drawing; using System.Threading; using System.Windows.Forms;
using System.Collections.Specialized; using System.Runtime.InteropServices; using System.Collections.Generic;
public static class Dragger2 {
  [DllImport("user32.dll")] static extern bool SetCursorPos(int x, int y);
  [DllImport("user32.dll")] static extern void mouse_event(uint f, int x, int y, uint d, UIntPtr e);
  public static string Run(string file, int tx, int ty) {
    var form = new Form { Text = "drag source", StartPosition = FormStartPosition.Manual,
      Location = new Point(10, 10), Size = new Size(160, 100), TopMost = true };
    var label = new Label { Text = "drag", Dock = DockStyle.Fill };
    form.Controls.Add(label);
    var seen = new List<string>(); string result = "no drag"; int copies = 0; bool over = false;
    label.GiveFeedback += (s, e) => { seen.Add(e.Effect.ToString()); if ((e.Effect & DragDropEffects.Copy) != 0) copies++; };
    label.QueryContinueDrag += (s, e) => {
      if (e.EscapePressed) { e.Action = DragAction.Cancel; return; }
      e.Action = (over && copies >= 3) ? DragAction.Drop : DragAction.Continue;
    };
    label.MouseDown += (s, e) => {
      var data = new DataObject(); var files = new StringCollection(); files.Add(file); data.SetFileDropList(files);
      new Thread(() => {
        Thread.Sleep(300);
        for (int i = 1; i <= 60; i++) { SetCursorPos(60 + (tx - 60) * i / 60, 60 + (ty - 60) * i / 60); Thread.Sleep(25); }
        over = true;
        for (int i = 0; i < 80; i++) { SetCursorPos(tx + (i % 3), ty + (i % 2)); Thread.Sleep(60); }
        mouse_event(0x0004, 0, 0, 0, UIntPtr.Zero);
      }).Start();
      result = form.DoDragDrop(data, DragDropEffects.Copy).ToString();
      form.Close();
    };
    form.Shown += (s, e) => new Thread(() => {
      Thread.Sleep(600); SetCursorPos(60, 60); Thread.Sleep(150);
      mouse_event(0x0002, 0, 0, 0, UIntPtr.Zero); Thread.Sleep(150); SetCursorPos(66, 66);
    }).Start();
    var timer = new System.Windows.Forms.Timer { Interval = 25000 };
    timer.Tick += (s, e) => { result = result == "no drag" ? "timed out" : result; form.Close(); };
    timer.Start();
    Application.Run(form);
    var counts = new Dictionary<string, int>();
    foreach (var k in seen) { counts[k] = counts.ContainsKey(k) ? counts[k] + 1 : 1; }
    var parts = new List<string>(); foreach (var kv in counts) parts.Add(kv.Key + "=" + kv.Value);
    return result + " | feedback " + string.Join(",", parts);
  }
}
'@
[Dragger2]::Run($args[0], [int]$args[1], [int]$args[2])
"""

# every element taller than the window, for the page that scrolls when it should not
OVERFLOW = """var H = innerHeight, se = document.scrollingElement, past = [];
document.querySelectorAll('body *').forEach(function (el) {
  var cs = getComputedStyle(el); if (cs.display === 'none' || cs.position === 'fixed') return;
  var r = el.getBoundingClientRect(), up = el.parentElement && el.parentElement.getBoundingClientRect();
  if (r.bottom > H + 1 && r.height > 0 && !(up && up.bottom > H + 1)) past.push(el.tagName.toLowerCase() + (el.id ? '#' + el.id : '') + ' ' + Math.round(r.bottom));
});
var top = Array.prototype.slice.call(document.body.children).filter(function (el) { return getComputedStyle(el).display !== 'none'; }).map(function (el) {
  var r = el.getBoundingClientRect(); return el.tagName.toLowerCase() + (el.id ? '#' + el.id : '') + ' ' + getComputedStyle(el).position + ' ' + Math.round(r.top) + '+' + Math.round(r.height); });
return { scroll: se.scrollHeight, inner: H, width: [se.scrollWidth, innerWidth, se.clientWidth], past: past.slice(0, 6), top: top };"""

MENU_LETTERS = (("file", "f"), ("edit", "e"), ("view", "v"), ("help", "h"))


def ps(dw, script: str, *args: str, timeout: float = 90) -> str:
    return dw.powershell(script, *args, out=dw.OUT[0], timeout=timeout)


def bar(dw, name: str, op: str, part: str = "*", *more: str) -> str:
    return ps(dw, MENUS, name, op, part, *more)


def menus(dw, name: str, shots: Path) -> dict:
    """Each menu of the main window opened by its letter, as Alt and the letter opens it, its picture
    taken from the screen, then put away; Open Recent's list under File; and whether Alt and F typed
    while the page has the keyboard opens File too."""
    said = {"bar": bar(dw, name, "bar"), "titles": bar(dw, name, "titles")}
    for word, letter in MENU_LETTERS:
        said[word] = bar(dw, name, "open", "*", letter)
        time.sleep(1.2)
        said[f"{word}_open"] = bar(dw, name, "popup")
        dw.desktop(shots / f"win-menu-{word}.png", dw.OUT[0])
        if word == "file":
            ps(dw, PRESS, "r")
            time.sleep(1.0)
            dw.desktop(shots / "win-menu-file-recent.png", dw.OUT[0])
            said["recent_open"] = bar(dw, name, "popup")
        ps(dw, PRESS, "{ESC}{ESC}{ESC}")
        time.sleep(0.6)
    return said


def clear_dialogs(dw, name: str) -> list:
    """A dialog of the app's own left open by an earlier step closed, as its close button closes it, since
    one standing open keeps the menu bar shut (the third Windows run of the second build)."""
    closed = []
    for _ in range(4):
        said = bar(dw, name, "dialog", "close")
        if said == "none":
            break
        closed.append(said)
        time.sleep(1)
    return closed


def by_menu(dw, name: str, letter: str, item: str, wait: float = 1.5) -> str:
    """A menu's item chosen by the menu's letter and the item's, as a keyboard chooses it."""
    opened = bar(dw, name, "open", "*", letter)
    time.sleep(0.8)
    ps(dw, PRESS, item)
    time.sleep(wait)
    return opened


def steps(dw, win, page, w: dict, name: str, shots: Path, attempt, ev) -> None:
    """The second build's steps in the first run, on the main window and its page."""
    attempt("two_dialogs_left", lambda: clear_dialogs(dw, name), 60)
    attempt("two_menus", lambda: menus(dw, name, shots), 240)

    def about():
        said = {"opened": by_menu(dw, name, "h", "a", 2.0)}
        dw.desktop(shots / "win-about.png", dw.OUT[0])
        said["dialog"] = bar(dw, name, "dialog", "close")
        return said
    attempt("two_about", about, 90)

    def acts():
        said = {}
        dw.cdp_ev(page, dw.dc.step_js("home"), 60)
        by_menu(dw, name, "f", "s")
        said["settings"] = dw.cdp_ev(page, "return !document.getElementById('settings').hidden;", 10)
        dw.desktop(shots / "win-menu-settings.png", dw.OUT[0])
        dw.cdp_ev(page, "hide('settings'); return true;", 10)
        by_menu(dw, name, "h", "k")
        said["shortcuts"] = dw.cdp_ev(page, "return !document.getElementById('help').hidden;", 10)
        dw.cdp_ev(page, "hide('help'); return true;", 10)
        before = dw.cdp_ev(page, "return [innerWidth, devicePixelRatio];", 10)
        by_menu(dw, name, "v", "i")
        said["zoom_in_menu"] = [before, dw.cdp_ev(page, "return [innerWidth, devicePixelRatio];", 10)]
        page.keyboard.press("Control+Minus")
        time.sleep(1)
        page.keyboard.press("Control+Minus")
        time.sleep(1)
        said["zoom_out_keys"] = dw.cdp_ev(page, "return [innerWidth, devicePixelRatio];", 10)
        page.keyboard.press("Control+0")
        time.sleep(1)
        said["zoom_actual_keys"] = dw.cdp_ev(page, "return [innerWidth, devicePixelRatio];", 10)
        dw.cdp_ev(page, "window.__marker = 'before reload'; return true;", 10)
        by_menu(dw, name, "v", "r", 4.0)
        try:
            said["reloaded"] = dw.cdp_ev(page, "return window.__marker || 'gone';", 20)
        except Exception as exc:  # noqa: BLE001  the page object may go with the reload
            said["reloaded"] = f"page went: {type(exc).__name__}"
        return said
    attempt("two_menu_acts", acts, 240)

    def edit_by_menu():
        live = win.main()
        said = {"field": dw.cdp_ev(live, dw.EDIT_FIELD, 20)}
        live.click("#drive-edit")
        live.keyboard.type("Wren")
        by_menu(dw, name, "e", "a", 0.8)
        by_menu(dw, name, "e", "c", 0.8)
        live.keyboard.press("End")
        by_menu(dw, name, "e", "p", 0.8)
        said["copy_paste"] = dw.cdp_ev(live, dw.EDIT_VALUE, 10)
        by_menu(dw, name, "e", "u", 0.8)
        said["undo"] = dw.cdp_ev(live, dw.EDIT_VALUE, 10)
        by_menu(dw, name, "e", "r", 0.8)
        said["redo"] = dw.cdp_ev(live, dw.EDIT_VALUE, 10)
        dw.cdp_ev(live, dw.EDIT_DONE, 10)
        return said
    attempt("two_edit_by_menu", edit_by_menu, 180)

    def board_undo():
        live = win.main()
        said = {"pets": dw.cdp_ev(live, dw.dc.step_js("pets"), 120)}
        said["spy"] = dw.cdp_ev(live, "window.__undos = []; window.__thWas = thUndo; thUndo = function (b) { window.__undos.push(b); }; if (document.activeElement && document.activeElement.blur) document.activeElement.blur(); return typeof thUndo;", 10)
        by_menu(dw, name, "e", "u", 1.0)
        by_menu(dw, name, "e", "r", 1.0)
        said["undos"] = dw.cdp_ev(live, "var u = window.__undos; thUndo = window.__thWas; return u;", 10)
        dw.cdp_ev(live, dw.dc.step_js("home"), 60)
        return said
    attempt("two_board_undo", board_undo, 240)

    def titles():
        live = win.main()
        said = {"home": bar(dw, name, "titles")}
        dw.cdp_ev(live, dw.dc.CASE % json.dumps("Rowan"), 60)
        time.sleep(1.5)
        said["case"] = bar(dw, name, "titles")
        said["page"] = dw.cdp_ev(live, "return document.title;", 10)
        dw.cdp_ev(live, dw.dc.step_js("home"), 60)
        return said
    attempt("two_titles", titles, 180)

    def choose():
        live = win.main()
        said = {"card": dw.cdp_ev(live, "openNewProject(); return { choose: !document.getElementById('np-choose').hidden, typed: document.getElementById('np-folder').readOnly };", 20)}
        dw.cdp_ev(live, "setTimeout(function () { document.getElementById('np-choose').click(); }, 200); return true;", 10)
        time.sleep(3)
        dw.desktop(shots / "win-choose-dialog.png", dw.OUT[0])
        said["dialog"] = ps(dw, dw.WINDOWS, name, "list")
        ps(dw, PRESS, "{ESC}")
        time.sleep(1)
        said["dialog_left"] = bar(dw, name, "dialog", "close")
        time.sleep(1)
        said["after"] = dw.cdp_ev(live, "var r = { folder: document.getElementById('np-folder').value }; hide('newproject'); return r;", 10)
        return said
    attempt("two_choose", choose, 120)

    def overflow():
        live = win.main()
        said = {}
        # Idiograph's own screens (Sift is an app of its own since 20 October), the PETs board's taken last
        for step in ("statements", "gets", "settings", "pets"):
            dw.cdp_ev(live, dw.dc.step_js(step), 90)
            said[step] = dw.cdp_ev(live, OVERFLOW, 20)
        live.screenshot(path=str(shots / "win-pets-scrollbars.png"))
        dw.cdp_ev(live, "hide('settings'); return true;", 10)
        dw.cdp_ev(live, dw.dc.step_js("home"), 60)
        return said
    attempt("two_overflow", overflow, 300)

    def drop():
        live = win.main()
        dw.cdp_ev(live, dw.dc.step_js("home"), 60)
        dw.cdp_ev(live, dw.DROP_ARM, 10)
        card = dw.cdp_ev(live, dw.DROP_CARD, 10)
        rect = bar(dw, name, "rect").split()
        left, top, width, height = (int(n) for n in rect[:4])
        tx, ty = left + width // 2, top + height // 2
        dragged = ps(dw, DRAGGER2, str(w["world"] / "drop-me.csv"), str(tx), str(ty), timeout=60)
        time.sleep(1)
        dw.desktop(shots / "win-drop-2.png", dw.OUT[0])
        return {"card": card, "dragger": dragged, "page": dw.cdp_ev(live, dw.DROP_READ, 10)}
    attempt("two_drop", drop, 180)

    def canvas_print():
        live = win.main()
        # the view's window kept by the page that opens it, which a late connection does not list, so its
        # print is asked of it from there
        keep = "var was = window.open; window.open = function () { var w = was.apply(window, arguments); window.__cp = w; return w; }; window.__openWas = was;"
        said = {"step": dw.cdp_ev(live, keep + dw.dc.HEAD + dw.dc.PRINT_VIEWS["canvas_print"], 120)}
        said["title"] = dw.cdp_ev(live, "window.open = window.__openWas; return window.__cp && window.__cp.document ? window.__cp.document.title : null;", 10)
        if not said["title"]:
            return dict(said, opened=False, windows=ps(dw, dw.WINDOWS, name, "list"))
        time.sleep(1.5)
        dw.desktop(shots / "win-canvas_print.png", dw.OUT[0])
        said["print"] = dw.cdp_ev(live, "setTimeout(function () { window.__cp.print(); }, 300); return true;", 20)
        time.sleep(4)
        said["panel"] = dw.desktop(shots / "win-canvas_print-panel.png", dw.OUT[0])
        said["closed"] = ps(dw, dw.CLOSE_TITLE, said["title"])
        return said
    attempt("two_canvas_print", canvas_print, 240)

    # a setting of the page's own, which a window on another port must start with (the third run)
    attempt("two_keep_setting", lambda: dw.cdp_ev(win.main(), "localStorage.setItem('idiograph-shut', '[\"trace\"]'); return localStorage.getItem('idiograph-shut');", 10), 30)


def before_last_close(dw, win, name: str, shots: Path, ev) -> dict:
    """The second run, before its last window closes: a case open, the window moved and sized, so the
    third run can show both kept."""
    live = win.main()
    said = {"case": dw.cdp_ev(live, dw.dc.CASE % json.dumps("Rowan"), 60)}
    time.sleep(1.5)
    said["moved"] = bar(dw, name, "move", "*", "140", "90", "1180", "760")
    time.sleep(1)
    said["rect"] = bar(dw, name, "rect")
    return said


def third_run(dw, exe: Path, env: dict, pw, out: Path, name: str, shots: Path, attempt, ev, port: int) -> None:
    """The third run, on another port: the window where it was and on the case it closed on, the page's
    setting kept across the port, Exit from File, and then a fourth start whose server is ended from
    outside, so the window says so."""
    def reopen():
        other = dw.Window(exe, dict(env, IDIOGRAPH_PORT=str(port)), pw, out, "3", port=port)
        said = {"page": dw.cdp_ev(other.page, dw.dc.PAGE_WAIT, 60) if other.page else "no page"}
        time.sleep(3)
        said["rect"] = bar(dw, name, "rect")
        said["titles"] = bar(dw, name, "titles")
        live = other.page
        said["screen"] = dw.cdp_ev(live, "return { work: !document.getElementById('work').hidden, title: document.title, port: location.port };", 10)
        said["kept_setting"] = dw.cdp_ev(live, "return localStorage.getItem('idiograph-shut');", 10)
        dw.desktop(shots / "win-reopened.png", out)
        live.screenshot(path=str(shots / "win-reopened-page.png"))
        other.disconnect()
        t = time.time()
        said["exit_menu"] = by_menu(dw, name, "f", "x", 1.0)
        said["server_gone_s"] = dw.dc.wait_closed(port, 45)
        try:
            said["exit"] = other.proc.wait(timeout=45)
        except Exception:  # noqa: BLE001
            said["exit"] = "still running"
        said["seconds"] = round(time.time() - t, 2)
        return said
    attempt("three_reopen", reopen, 300)

    def ended():
        other = dw.Window(exe, env, pw, out, "4")
        page = other.page
        said = {"page": bool(page)}
        import subprocess
        said["killed"] = subprocess.run(["taskkill", "/F", "/IM", "Idiograph.exe"], capture_output=True, text=True).stdout.strip()[-200:]
        # the notice comes once the window has waited a few seconds for the server's last word, so it is
        # waited for, where four seconds missed it once (the third build's fourth Windows run). Since the
        # fifth build (18 October) it is the page's alone, in Adam's words, and no system notice stands
        # over it, where the fourth build showed both
        t = time.time()
        shown = None
        while time.time() - t < 25 and not shown:
            try:
                shown = dw.cdp_ev(page, "return document.getElementById('server-gone').hidden ? null : "
                                        "{ head: document.getElementById('server-gone-head').textContent, "
                                        "line: document.getElementById('server-gone-line').textContent };", 5)
            except Exception:  # noqa: BLE001  not there yet
                shown = None
            if not shown:
                time.sleep(1)
        said["notice_s"] = round(time.time() - t, 1)
        said["page_notice"] = shown
        # longer than the window waits for the page's word before its own notice would say it
        time.sleep(6)
        said["dialog"] = bar(dw, name, "dialog")
        said["windows"] = ps(dw, dw.WINDOWS, name, "list")
        dw.desktop(shots / "win-server-ended.png", out)
        other.disconnect()
        # closed as the notice says, by its close button, and the app ends with its last window
        said["closed"] = ps(dw, dw.WINDOWS, name, "close")
        try:
            said["exit"] = other.proc.wait(timeout=30)
        except Exception:  # noqa: BLE001
            said["exit"] = "still running"
            said["dialog_left"] = bar(dw, name, "dialog", "close")
        return said
    attempt("four_server_ended", ended, 200)

    # a start that fails, since the fifth build said in plain words where its dialog showed the log's last
    # lines: the server handed an argument it does not take, so it ends before it answers. Since the sixth
    # build (18 October) every other window is minimised first and the dialog taken by its own frame alone,
    # where the fifth build's picture showed the machine's console behind it (drive_failed_start.py, which
    # the workflow runs on the build before the fifth too, for the Before)
    def failed_start():
        bad = dict(env, IDIOGRAPH_ARGS="--no-such-switch")
        import drive_failed_start
        said = drive_failed_start.failed_start(exe, bad, out, shots / "win-failed-start.png", out / "window-5.log")
        said["dialog_left"] = bar(dw, name, "dialog", "close")
        return said
    attempt("five_failed_start", failed_start, 150)
