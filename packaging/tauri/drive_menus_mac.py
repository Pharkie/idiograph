#!/usr/bin/env python3
"""The second build's check of the window on a Mac (17 October, later), on a build with the `drive` feature:
the menus, each opened over the window and its picture taken, About, the menus' items on the page, the
zoom, the title, Choose, Open Recent, spelling, and across a quit the window's size and place, the page's
place and its settings on another port, Quit from the menu, and the notice when the server ends without a
word. The standard library only, with `drive_mac.py`'s own parts.

    python3 packaging/tauri/drive_menus_mac.py --app <Idiograph Test.app> --stage <build/stage> --out <folder>

The app starts as `open -g -n -W` starts it, so it never comes to the front, and its windows never take
the keyboard. A menu opened by a check stands over whatever is on the screen for three seconds. This
Mac takes no screen capture of a check's windows ("could not create image from window", both builds), so
the pictures are drawn by the app itself: a window, a menu or a panel by AppKit (`snap`), and a page by its
web view (`snappage`).
"""
from __future__ import annotations

import argparse
import json
import os
import signal
import subprocess
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import drive_common as dc  # noqa: E402  beside this file
import drive_mac as dm  # noqa: E402  beside this file

# the windows of a process as the window server lists them: number, layer, width and height
WINDOWS_JXA = """ObjC.import('CoreGraphics');
var list = ObjC.deepUnwrap(ObjC.castRefToObject($.CGWindowListCopyWindowInfo(1, 0)));
var out = [];
list.forEach(function (w) { if (w.kCGWindowOwnerPID === %d) out.push([w.kCGWindowNumber, w.kCGWindowLayer, Math.round(w.kCGWindowBounds.Width), Math.round(w.kCGWindowBounds.Height)]); });
JSON.stringify(out);"""

MENUS = ("Idiograph", "File", "File>Open Recent", "Edit", "Edit>Spelling and Grammar", "View", "Window", "Help")


def app_pid(bundle: Path) -> int | None:
    """The app's own process, by its executable's path as `ps` shows it."""
    exe = str(bundle / "Contents" / "MacOS" / bundle.stem)
    done = subprocess.run(["ps", "-axo", "pid=,command="], capture_output=True, text=True)
    pids = [int(line.split(None, 1)[0]) for line in done.stdout.splitlines()
            if line.strip() and line.split(None, 1)[1:] and line.split(None, 1)[1].startswith(exe)]
    return max(pids) if pids else None


def windows_of(pid: int) -> list:
    done = subprocess.run(["osascript", "-l", "JavaScript", "-e", WINDOWS_JXA % pid], capture_output=True, text=True, timeout=20)
    try:
        return json.loads(done.stdout.strip() or "[]")
    except ValueError:
        return []


FRAME_JXA = """ObjC.import('CoreGraphics');
var out = {win: null, item: null};
var list = ObjC.deepUnwrap(ObjC.castRefToObject($.CGWindowListCopyWindowInfo(1, 0)));
list.forEach(function (w) { if (w.kCGWindowOwnerPID === %d && w.kCGWindowLayer >= 101 && !out.win) out.win = [w.kCGWindowBounds.X, w.kCGWindowBounds.Y, w.kCGWindowBounds.Width, w.kCGWindowBounds.Height]; });
try {
  var se = Application('System Events');
  var m = se.processes.whose({unixId: %d})[0].menuBars[0].menuBarItems.byName('File').menus[0].menuItems.byName('Project History');
  out.item = [m.position()[0], m.position()[1], m.size()[0], m.size()[1]];
} catch (e) { out.error = String(e); }
JSON.stringify(out);"""


def item_frame(pid: int):
    """The open File menu's Project History item by its accessibility frame, and the menu window's own, both in
    screen points, so the item's place in a capture of the window alone is the difference (histmenu, 4 November)."""
    done = subprocess.run(["osascript", "-l", "JavaScript", "-e", FRAME_JXA % (pid, pid)], capture_output=True, text=True, timeout=30)
    try:
        return json.loads(done.stdout.strip())
    except ValueError:
        return {"error": done.stderr.strip()[:200]}


def order(path: Path, *lines: str) -> None:
    with path.open("a", encoding="utf-8") as fh:
        fh.write("\n".join(lines) + "\n")


def snap(app: dm.App, orders: Path, prefix: Path, after: float, seconds: float = 10) -> list:
    """Every visible window of the app's own drawn to a picture by AppKit, its lines said back."""
    order(orders, f"snap {prefix}")
    app.wait_said(f"drive: snap done {prefix}", seconds, after)
    return [line.split("drive: snap ", 1)[1] for line in app.said("drive: snap ", after) if str(prefix) in line and "done" not in line]


def snap_page(app: dm.App, orders: Path, label: str, path: Path, after: float, seconds: float = 10):
    """A window's page drawn to a picture by its web view."""
    order(orders, f"snappage {label} {path}")
    return app.wait_said("drive: snappage", seconds, after)


def menu_lines(app: dm.App, after: float) -> list:
    return [line.split("drive: menu ", 1)[1] for line in app.said("drive: menu ", after) if not line.startswith("drive: menu item")]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--app", required=True)
    ap.add_argument("--stage", required=True)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    out = Path(a.out).resolve()
    shots = out / "shots"
    shots.mkdir(parents=True, exist_ok=True)
    dm.SAVED.append(out / "results.json")
    note, attempt, run, loaded = dm.note, dm.attempt, dm.run, dm.loaded
    bundle = Path(a.app).resolve()
    stage = Path(a.stage).resolve()
    w = dc.make_world(out, stage / "demo", stage / "config.json")
    home = out / "home"
    (home / "Downloads").mkdir(parents=True, exist_ok=True)
    (out / "drive.js").write_text(dm.DRIVE_JS, encoding="utf-8")
    orders, closer = out / "orders", out / "close-these"
    chosen = w["world"] / "chosen-folder"
    chosen.mkdir(exist_ok=True)
    base = dict(os.environ, HOME=str(home), IDIOGRAPH_WINDOW_DRIVE=str(out / "drive.js"), IDIOGRAPH_WINDOW_SAVE_TO=str(home / "Downloads"),
                IDIOGRAPH_WINDOW_CLOSE=str(closer), IDIOGRAPH_WINDOW_NO_OPEN="1", IDIOGRAPH_WINDOW_ORDERS=str(orders),
                IDIOGRAPH_WINDOW_PICK=str(chosen), IDIOGRAPH_WINDOW_UNSAVED="close")
    env = dc.app_env(base, w)
    stub = dc.Stub()
    logs = home / "Library" / "Logs" / "Idiograph" / "idiograph.log"

    # ── the first run
    t0 = time.time()
    app = dm.App(bundle, env, out / "app-1.log")
    first = loaded(stub, t0, 60, label="main")
    note("page_loaded_s", round(first["at"] - t0, 2) if first else None)
    pid = app_pid(bundle)
    note("pid", pid)
    attempt("world", lambda: run(stub, "main", dc.world_js(w)))
    attempt("home", lambda: run(stub, "main", dc.step_js("home")))

    def menus():
        t = time.time()
        order(orders, "menus")
        app.wait_said("drive: menus done", 15, t)
        return menu_lines(app, t)
    attempt("menus", menus)

    def popups():
        said = {}
        for title in MENUS:
            t = time.time()
            order(orders, f"popup {title}")
            opened = app.wait_said(f"drive: popup open {title}", 15, t)
            time.sleep(0.8)
            menus_now = [x for x in windows_of(pid) if x[1] >= 101] if pid else []
            for _ in range(4):
                if menus_now:
                    break
                time.sleep(0.4)
                menus_now = [x for x in windows_of(pid) if x[1] >= 101] if pid else []
            prefix = shots / f"mac-menu-{title.replace('>', '-').replace(' ', '-').lower()}"
            # the open menu's own window alone, by its number, so no desktop shows (histmenu, 4 November)
            if title == "File":
                (shots / "file-grey-frame.json").write_text(json.dumps(item_frame(pid)), encoding="utf-8")
            for n, win in enumerate(menus_now):
                subprocess.run(["screencapture", "-o", "-l", str(win[0]), f"{prefix}-menu{n}.png"], capture_output=True, timeout=20)
            said[title] = {"opened": bool(opened), "windows": menus_now, "snap": snap(app, orders, prefix, t, 4)}
            app.wait_said(f"drive: popup closed {title}", 10, t)
            time.sleep(0.5)
        return said
    attempt("popups", popups)

    def about():
        t = time.time()
        order(orders, "about")
        # the item's title, then the page's own card (20 October), never the system's panel
        line = app.wait_said("drive: about item ", 10, t)
        said = {"line": line}
        time.sleep(0.8)
        said["card"] = run(stub, "main", "return !document.getElementById('about').hidden;")
        said["snap"] = snap(app, orders, shots / "mac-about", t)
        order(orders, "about-close")
        said["closed"] = app.wait_said("drive: about closed", 10, t)
        return said
    attempt("about", about)

    def acts():
        said = {}
        for item, check in (("settings", "return !document.getElementById('settings').hidden;"),
                            ("shortcuts", "return !document.getElementById('help').hidden;")):
            order(orders, f"item {item}")
            time.sleep(1.5)
            said[item] = run(stub, "main", check)
            run(stub, "main", "hide('settings'); hide('help'); return true;")
        size = "return [innerWidth, devicePixelRatio];"
        said["zoom_before"] = run(stub, "main", size)
        order(orders, "item zoom-in")
        time.sleep(2)
        said["zoom_in"] = run(stub, "main", size, timeout=120)
        said["zoom_in_snap"] = snap_page(app, orders, "main", shots / "mac-zoom-in.png", time.time())
        # Cmd and - as the page hears it, which window.js hands the window
        run(stub, "main", "var e = new KeyboardEvent('keydown', { key: '-', metaKey: true, bubbles: true, cancelable: true }); document.body.dispatchEvent(e); return e.defaultPrevented;")
        time.sleep(1.2)
        said["zoom_out_key"] = run(stub, "main", size)
        order(orders, "item zoom-actual")
        time.sleep(1.2)
        said["zoom_actual"] = run(stub, "main", size)
        return said
    attempt("menu_acts", acts)

    def more_items():
        said = {"closing_hidden": run(stub, "main", "openSettings('general'); var r = [document.getElementById('close-sub').hidden, document.getElementById('set-quit-closed').closest('.switches').hidden]; hide('settings'); return r;")}
        for item, look in (("new-window", "/"), ("manual", "/manual")):
            t = time.time()
            order(orders, f"item {item}")
            page = loaded(stub, t, 30, not_label="main")
            said[item] = page and {"label": page.get("label"), "href": page.get("href"), "title": page.get("title")}
            if page:
                time.sleep(1.5)
                if item == "manual":
                    said["manual_snap"] = snap_page(app, orders, page["label"], shots / "mac-manual.png", time.time())
                order(closer, page["label"])
                time.sleep(2)
        run(stub, "main", "window.__beforeReload = 'here'; return true;")
        t = time.time()
        order(orders, "item reload")
        said["reload"] = bool(loaded(stub, t, 30, label="main")) and run(stub, "main", "return window.__beforeReload || 'reloaded';")
        return said
    attempt("more_items", more_items)

    def undo_on_board():
        said = {"pets": run(stub, "main", dc.step_js("pets"), timeout=120)}
        said["spy"] = run(stub, "main", "window.__undos = []; var was = thUndo; thUndo = function (b) { window.__undos.push(b); }; window.__thWas = was; document.activeElement && document.activeElement.blur && document.activeElement.blur(); return typeof thUndo;")
        order(orders, "item undo", "item redo")
        time.sleep(2)
        said["undos"] = run(stub, "main", "var u = window.__undos; thUndo = window.__thWas; return u;")
        return said
    attempt("undo_on_board", undo_on_board)

    def titles():
        t = time.time()
        said = {"case": run(stub, "main", dc.CASE % json.dumps("Rowan"))}
        time.sleep(1.5)
        said["page"] = run(stub, "main", "return document.title;")
        said["window"] = app.said("drive: title main", t)[-1:]
        said["snap"] = snap(app, orders, shots / "mac-title-window", time.time())
        run(stub, "main", dc.step_js("home"))
        time.sleep(1.2)
        said["home"] = app.said("drive: title main", t)[-1:]
        return said
    attempt("titles", titles)

    def choose():
        t = time.time()
        said = {"card": run(stub, "main", "openNewProject(); return !document.getElementById('np-choose').hidden;")}
        run(stub, "main", "setTimeout(function () { document.getElementById('np-choose').click(); }, 100); return true;")
        line = app.wait_said("drive: sheet main ", 20, t)
        said["panel"] = line
        time.sleep(1.2)
        said["snap"] = snap(app, orders, shots / "mac-choose-panel", t)
        app.wait_said("drive: picked", 15, t)
        said["picked"] = app.said("drive: picked", t)
        said["folder"] = run(stub, "main", "var t0 = Date.now(); while (!document.getElementById('np-folder').value && Date.now() - t0 < 10000) await wait(250); var v = { folder: document.getElementById('np-folder').value, said: (document.getElementById('np-said') || {}).textContent || '' }; hide('newproject'); return v;")
        return said
    attempt("choose", choose)

    def recent():
        t = time.time()
        order(orders, "menus")
        app.wait_said("drive: menus done", 15, t)
        rows = [x for x in menu_lines(app, t) if x.startswith("/File/Open Recent |")]
        said = {"rows": rows}
        first_row = next((r for r in rows if "| recent" not in r and "| true |" in r), None)
        said["first"] = first_row
        t2 = time.time()
        order(orders, "item recent-0")
        page = loaded(stub, t2, 30, not_label="main")
        said["opened"] = page and {"label": page.get("label"), "title": page.get("title")}
        if page:
            time.sleep(2.5)
            said["screen"] = run(stub, page["label"], "return { title: document.title, sift: !!document.getElementById('sift') && !document.getElementById('sift').hidden, project: !document.getElementById('home-project').hidden };")
            said["snap"] = snap_page(app, orders, page["label"], shots / "mac-open-recent-window.png", time.time())
            order(closer, page["label"])
            time.sleep(2)
        return said
    attempt("open_recent", recent)

    def project_history():
        """File, Project History (histmenu, 4 November): greyed on the demo, on on a project of its own, and its item
        opens that project's History record, as Home's project menu does. The window's page says which as the window
        comes to the front, which a check's window never does, so each read follows a focus event the check sends.
        File, Project Settings... under it (settingsplit, 5 November) is greyed on Home alone, on on a demo too, whose
        sheet is read-only, and its item opens the project's own settings sheet."""
        def row(focus=True, item="Project History"):
            if focus:
                run(stub, "main", "window.dispatchEvent(new Event('focus')); return true;")
                time.sleep(1.0)
            t = time.time()
            order(orders, "menus")
            app.wait_said("drive: menus done", 15, t)
            line = next((x for x in menu_lines(app, t) if x.startswith(f"/File | {item} |")), None)
            return line and ("on" if line.split(" | ")[-2] == "true" else "grey")
        settings_item = "Project Settings\u2026"
        said = {"mine": run(stub, "main", dc.HEAD + "hide('settings'); hide('newproject'); await loadLibrary(); await wait(800); return S.home;")}
        run(stub, "main", dc.HEAD + "homeKeep(''); drawHome(); await wait(800); return S.home;")
        said["settings_home"] = row(item=settings_item)
        run(stub, "main", dc.HEAD + "openPage(DEMO_ID); await wait(2500); return S.home;")
        said["demo"] = row()
        said["settings_demo"] = row(False, settings_item)
        run(stub, "main", dc.HEAD + "openPage(%s); await wait(2500); return S.home;" % json.dumps(said["mine"]))
        said["project"] = row()
        said["settings_project"] = row(False, settings_item)
        # the File menu open with a project in front, the item on, its own window alone
        t = time.time()
        order(orders, "popup File")
        app.wait_said("drive: popup open File", 15, t)
        time.sleep(1.2)
        (shots / "file-on-frame.json").write_text(json.dumps(item_frame(pid)), encoding="utf-8")
        for n, win in enumerate(x for x in windows_of(pid) if x[1] >= 101):
            subprocess.run(["screencapture", "-o", "-l", str(win[0]), str(shots / f"mac-menu-file-on-menu{n}.png")], capture_output=True, timeout=20)
        app.wait_said("drive: popup closed File", 10, t)
        time.sleep(0.5)
        order(orders, "item project-history")
        time.sleep(2.5)
        said["sheet"] = run(stub, "main", "return { open: !document.getElementById('project-history').hidden, project: document.getElementById('ph-project').textContent };")
        said["snap"] = snap_page(app, orders, "main", shots / "mac-project-history.png", time.time())
        run(stub, "main", dc.THEME % "'light'")
        said["snap_light"] = snap_page(app, orders, "main", shots / "mac-project-history-light.png", time.time())
        run(stub, "main", dc.THEME % "'dark'")
        said["closed"] = run(stub, "main", "phShut(); return document.getElementById('project-history').hidden;")
        order(orders, "item project-settings")
        time.sleep(2.5)
        said["settings_sheet"] = run(stub, "main", "return { open: !document.getElementById('projset').hidden, project: document.getElementById('projset-kicker').textContent };")
        said["settings_snap"] = snap_page(app, orders, "main", shots / "mac-project-settings.png", time.time())
        said["settings_closed"] = run(stub, "main", "hide('projset'); return document.getElementById('projset').hidden;")
        return said
    attempt("project_history", project_history)

    def spelling():
        t = time.time()
        order(orders, "spellstate main")
        said = {"state": app.wait_said("drive: spellstate", 10, t)}
        said.update({"field": run(stub, "main", "var f = document.createElement('textarea'); f.id = 'drive-spell'; f.spellcheck = true; f.style.cssText = 'position:fixed;left:40px;top:120px;width:420px;height:90px;z-index:99999;font-size:20px'; document.body.appendChild(f); f.focus(); document.execCommand('insertText', false, 'Thsi sentense is mispeled on purpose. '); return f.value;")})
        time.sleep(2.5)
        said["snap"] = snap_page(app, orders, "main", shots / "mac-spelling.png", time.time())
        said["snap_window"] = snap(app, orders, shots / "mac-spelling-window", time.time())
        run(stub, "main", "var f = document.getElementById('drive-spell'); if (f) f.remove(); return true;")
        return said
    attempt("spelling", spelling)

    attempt("keep_setting", lambda: run(stub, "main", "localStorage.setItem('idiograph-shut', '[\"trace\"]'); return localStorage.getItem('idiograph-shut');"))

    def close_on_case():
        said = {"case": run(stub, "main", dc.CASE % json.dumps("Rowan"))}
        order(orders, "frame 160 120 1100 720")
        time.sleep(1.5)
        t = time.time()
        order(orders, "where")
        said["where"] = app.wait_said("drive: where", 10, t)
        order(closer, "main")
        said["server_gone_s"] = dc.wait_closed(dc.PORT, 40)
        said.update(app.end(40))
        return said
    attempt("close_on_case", close_on_case)
    attempt("window_state_file", lambda: sorted(p.name for p in (home / "Library" / "Application Support" / "uk.co.adamknowles.idiograph.test").glob("*")))
    attempt("window_json", lambda: json.loads((home / "Library" / "Application Support" / "uk.co.adamknowles.idiograph.test" / "window.json").read_text()))

    # ── the second run, on another port: where it was, the case it closed on, the setting, Quit from the menu
    port2 = dc.PORT + 1
    t3 = time.time()
    app2 = dm.App(bundle, dict(env, IDIOGRAPH_PORT=str(port2)), out / "app-2.log")
    second = loaded(stub, t3, 60, label="main")
    note("second_loaded", second and {"href": second.get("href"), "title": second.get("title")})

    def reopened():
        time.sleep(4)
        t = time.time()
        order(orders, "where")
        said = {"where": app2.wait_said("drive: where", 10, t)}
        said["screen"] = run(stub, "main", "return { work: !document.getElementById('work').hidden, title: document.title, port: location.port, kept: localStorage.getItem('idiograph-shut') };")
        said["snap_page"] = snap_page(app2, orders, "main", shots / "mac-reopened.png", time.time())
        said["snap_window"] = snap(app2, orders, shots / "mac-reopened-window", time.time())
        return said
    attempt("reopened", reopened)

    # Restart in Settings, then Quit in Settings: the window waits for the server through the Restart and
    # ends with it after the Quit (Quit from the menu was tried on the run before, mac2)
    def restart_then_quit():
        before = run(stub, "main", dc.STARTED)
        t = time.time()
        run(stub, "main", dc.RESTART, timeout=10)
        back = loaded(stub, t, 40, label="main")
        time.sleep(2)
        said = {"before": before, "after": run(stub, "main", dc.STARTED), "reloaded": bool(back),
                "app_running": app2.proc.poll() is None}
        t = time.time()
        run(stub, "main", dc.QUIT, timeout=10)
        said["server_gone_s"] = dc.wait_closed(port2, 40)
        said.update(app2.end(40))
        said["seconds"] = round(time.time() - t, 2)
        said["notice"] = app2.said("Idiograph: Idiograph stopped unexpectedly")
        return said
    attempt("restart_then_quit", restart_then_quit)

    # ── the third run: the server ended from outside, and the window says so
    t4 = time.time()
    app3 = dm.App(bundle, env, out / "app-3.log")
    note("third_loaded", bool(loaded(stub, t4, 60, label="main")))

    def ended():
        pid3 = app_pid(bundle)
        done = subprocess.run(["pgrep", "-f", f"Resources/server/Idiograph --serve --port {dc.PORT}"], capture_output=True, text=True)
        servers = [int(p) for p in done.stdout.split() if p.isdigit()]
        for p in servers:
            os.kill(p, signal.SIGKILL)
        time.sleep(4)
        found = windows_of(pid3) if pid3 else []
        said = {"servers": servers, "windows": found, "said": app3.said("Idiograph: Idiograph stopped unexpectedly")}
        said["snap"] = snap(app3, orders, shots / "mac-server-ended", time.time())
        if pid3:
            os.kill(pid3, signal.SIGTERM)
        said.update(app3.end(20))
        return said
    attempt("server_ended", ended)

    attempt("log", lambda: [line for line in logs.read_text(encoding="utf-8").splitlines() if line.startswith("===")][-4:])
    stub.close()
    note("ports_closed_at_end", [not dc.listening(dc.PORT), not dc.listening(port2)])
    return 0


if __name__ == "__main__":
    sys.exit(main())
