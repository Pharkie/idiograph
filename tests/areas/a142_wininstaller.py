from __future__ import annotations

import inspect
import io
import os
import shutil
import sys
from pathlib import Path

from . import support
from .support import TOOL, check, skip


def test_wininstaller(scratch):
    print("\n142. The Windows app, 14 October: its launcher with every Windows call stood in for, the folders it "
          "writes in, the build's spec and Inno Setup script as text, a dry run, the workflow that builds the "
          "installer and the words")
    import contextlib as ctx
    import ctypes
    import importlib.util
    import struct
    import subprocess
    import app_folders
    import mcp_server
    import server as server_mod

    def load(name):
        spec = importlib.util.spec_from_file_location(f"idiograph_142_{name}", support.source("packaging") / f"{name}.py")
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        return mod

    read = lambda path: Path(path).read_text(encoding="utf-8")
    w = load("windows_launcher")
    mac = load("mac_launcher")
    build = load("build_windows")
    build_mac = load("build_mac")
    launch_src, build_src = read(support.source("packaging/windows_launcher.py")), read(support.source("packaging/build_windows.py"))
    folders_src = read(support.source("family/app_folders.py"))
    workflow_path = support.source(".github/workflows/windows-installer.yml")
    workflow = read(workflow_path) if workflow_path.exists() else ""
    base = scratch / "wininstaller"
    shutil.rmtree(base, ignore_errors=True)
    home = base / "Kim Example"

    # ── A. one helper decides the folders, for both platforms
    win = app_folders.folders("win32", home)
    given = app_folders.folders("win32", home, {"APPDATA": str(base / "roam"), "LOCALAPPDATA": str(base / "local"),
                                                "TEMP": str(base / "temp")})
    macs = app_folders.folders("darwin", home)
    check("142: on Windows the data in AppData, Roaming, the logs in AppData, Local, and the launch line in the temporary folder",
          win == {"data": home / "AppData" / "Roaming" / "Idiograph", "logs": home / "AppData" / "Local" / "Idiograph" / "Logs",
                  "trace": home / "AppData" / "Local" / "Temp" / "idiograph-launch.log"}
          and given == {"data": base / "roam" / "Idiograph", "logs": base / "local" / "Idiograph" / "Logs",
                        "trace": base / "temp" / "idiograph-launch.log"}, str(win))
    check("142: on a Mac the folders are as before, Application Support, Logs and /tmp",
          macs == {"data": home / "Library" / "Application Support" / "Idiograph", "logs": home / "Library" / "Logs" / "Idiograph",
                   "trace": Path("/tmp/idiograph-launch.log")})
    paths_win, paths_mac = server_mod.app_paths(True, home, "win32"), server_mod.app_paths(True, home, "darwin")
    check("142: the server, the Mac launcher and the Windows launcher all take their folders from app_folders, with no copy of their own",
          paths_win["data"] == win["data"] and paths_win["logs"] == win["logs"] and paths_mac["logs"] == macs["logs"]
          and mac.logs_dir(home) == macs["logs"] and mac.TRACE == app_folders.folders("darwin")["trace"]
          and w.places(home) == win and "app_folders.folders(" in inspect.getsource(server_mod.app_paths)
          and "AppData" not in inspect.getsource(server_mod) and "AppData" not in launch_src
          and '"Library"' not in read(support.source("packaging/mac_launcher.py")) and folders_src.count("def folders(") == 1
          and "app_folders" in build_mac.MODULES and "import app_folders" in read(support.source("packaging/mac_launcher.py")))

    # ── B. the launcher, every Windows call stood in for
    class Clock:
        def __init__(self):
            self.t = 1000.0

        def monotonic(self):
            return self.t

        def sleep(self, seconds):
            self.t += seconds

    exe = r"C:\Users\Kim Example\AppData\Local\Programs\Idiograph\Idiograph.exe"
    ours_line = subprocess.list2cmdline([exe, "--serve", "--port", "8765"])
    other_line = r'"C:\Program Files\Kettle Lamp\kettle.exe" --listen 8765'
    held: dict[int, set[int]] = {}
    commands: dict[int, str] = {}
    calls: dict[str, list] = {k: [] for k in ("popen", "ask", "alert", "notify", "open", "quit", "end")}
    answers: list[str] = []
    quit_closes = [True]

    class Child:
        def __init__(self, pid):
            self.pid = pid

        def poll(self):
            return None

    def popen(cmd, **kw):
        calls["popen"].append((list(cmd), kw))
        pid = 5000 + len(calls["popen"])
        port = int(w.port_of(list(cmd)))
        held[port] = {pid}
        commands[pid] = subprocess.list2cmdline([exe, *cmd[cmd.index("--serve"):]])
        return Child(pid)

    def quit_server(port, timeout=15):
        calls["quit"].append(port)
        if quit_closes[0]:
            held.pop(port, None)
        return True

    def end(pid):
        calls["end"].append(pid)
        for port in list(held):
            held[port].discard(pid)
            if not held[port]:
                held.pop(port)

    stand_ins = {
        "listening": lambda first, last: {p: set(v) for p, v in held.items() if first <= p <= last},
        "command_of": lambda pid: commands.get(pid, ""),
        "POPEN": popen,
        "ask": lambda: (calls["ask"].append(1), answers.pop(0) if answers else "")[1],
        "alert": lambda message: calls["alert"].append(message),
        "notify": lambda message: calls["notify"].append(message),
        "open_page": lambda url: calls["open"].append(url),
        "ask_quit": quit_server,
        "terminate": end,
        "places": lambda home_=None, env=None: app_folders.folders("win32", home),
        "time": Clock(),
    }
    real = {name: getattr(w, name) for name in stand_ins}
    kept_env = {k: os.environ.pop(k) for k in ("IDIOGRAPH_PORT", "IDIOGRAPH_ARGS") if k in os.environ}
    logs = win["logs"]
    trace_file = base / "launch.log"
    # the launch line of a run with no trace of its own, Setup's stop, in the stand-in temporary folder
    win["trace"].parent.mkdir(parents=True, exist_ok=True)
    real_tcp = w.tcp_table

    def reset(table=None, cmds=None, said=()):
        held.clear()
        held.update(table or {})
        commands.clear()
        commands.update(cmds or {})
        for v in calls.values():
            v.clear()
        answers[:] = list(said)
        quit_closes[0] = True
        trace_file.unlink(missing_ok=True)
        win["trace"].unlink(missing_ok=True)

    traced = lambda: trace_file.read_text(encoding="utf-8") if trace_file.exists() else ""
    try:
        for name, value in stand_ins.items():
            setattr(w, name, value)
        reset()
        code = w.launch(None, [], w.Trace(trace_file))
        cmd, kw = calls["popen"][0] if calls["popen"] else ([], {})
        pid_file = logs / "idiograph-8765.pid"
        how = (kw.get("creationflags") == w.DETACHED and "startupinfo" in kw) if os.name == "nt" else kw.get("start_new_session") is True
        check("142: a double-click with nothing on the port starts the server with no window, its output in the log, and asks nothing",
              code == 0 and cmd[-3:] == ["--serve", "--port", "8765"] and how and kw.get("cwd") == str(logs)
              and kw.get("stdin") is subprocess.DEVNULL and kw.get("stderr") is subprocess.STDOUT and kw.get("close_fds") is True
              and kw.get("env", {}).get("PYTHONUNBUFFERED") == "1" and (logs / "idiograph.log").is_file()
              and pid_file.read_text(encoding="utf-8") == "5001\n" and not calls["ask"] and not calls["alert"]
              and "port 8765: started, pid 5001" in traced(), traced())
        check("142: the server runs as this executable with --serve, the Python with this file from source, and the window flags are Windows's",
              w.server_command(8789, ["--no-browser"]) == [sys.executable, str(support.source("packaging/windows_launcher.py").resolve()),
                                                           "--serve", "--port", "8789", "--no-browser"]
              and w.DETACHED == 0x08000200 and w.STARTF_FORCEOFFFEEDBACK == 0x80
              and 'return [sys.executable, SERVE, "--port", str(port), *extra]' in launch_src)

        seen = {}
        for choice in ("Open", "Stop", "Restart", ""):
            reset({8765: {77}}, {77: ours_line}, [choice])
            # each call kept with its command alone, never its environment, which a check's detail would print
            seen[choice] = (w.launch(None, [], w.Trace(trace_file)),
                            {k: [c[0] for c in v] if k == "popen" else list(v) for k, v in calls.items()}, traced(),
                            sorted(held.get(8765, ())))
        o, s, r, d = seen["Open"], seen["Stop"], seen["Restart"], seen[""]
        check("142: a double-click while it runs asks once, and Open, the default, opens the page at its port",
              o[0] == 0 and o[1]["ask"] == [1] and o[1]["open"] == ["http://127.0.0.1:8765/"] and not o[1]["popen"]
              and not o[1]["quit"] and "running, opened the browser" in o[2]
              and w.QUESTION == mac.QUESTION == "Idiograph is running." and w.CHOICES == mac.CHOICES == ("Stop", "Restart", "Open")
              and w.DEFAULT == "Open", str(o[1]))
        check("142: Stop asks the server to quit, as Settings does, ends nothing it need not, and says it stopped",
              s[0] == 0 and s[1]["quit"] == [8765] and not s[1]["end"] and s[1]["notify"] == ["Idiograph stopped."]
              and not s[1]["popen"] and "running, stopped" in s[2] and s[3] == [], str(s[1]))
        check("142: Restart stops it the same way and starts it again on the same port",
              r[0] == 0 and r[1]["quit"] == [8765] and len(r[1]["popen"]) == 1 and r[1]["popen"][0][-2:] == ["--port", "8765"]
              and "restarted, pid 5001" in r[2] and r[3] == [5001], str(r[1]))
        check("142: a dialog closed does nothing and says so in the launch line",
              d[0] == 0 and not any(d[1][k] for k in ("quit", "end", "popen", "open")) and "running, dialog dismissed" in d[2])
        reset({8765: {77}}, {77: ours_line}, ["Stop"])
        quit_closes[0] = False
        stubborn = (w.launch(None, [], w.Trace(trace_file)), list(calls["quit"]), list(calls["end"]))
        check("142: a server that has not quit five seconds after it was asked is ended, its own process alone",
              stubborn == (0, [8765], [77]), str(stubborn))

        # the port: another program's, the app's own further on, and every port held
        reset({8765: {91}}, {91: other_line})
        moved = (w.launch(None, [], w.Trace(trace_file)), calls["popen"][0][0][-2:] if calls["popen"] else [], traced())
        picks = {"ours": w.choose_port(8765, {8765: {91}, 8767: {77}}),
                 "full": w.choose_port(8765, {p: {91} for p in range(8765, 8765 + w.SPAN + 1)})}
        commands.update({91: other_line, 77: ours_line})
        picks["ours"] = w.choose_port(8765, {8765: {91}, 8767: {77}})
        reset({p: {91} for p in range(8765, 8765 + w.SPAN + 1)}, {91: other_line})
        full = (w.launch(None, [], w.Trace(trace_file)), list(calls["alert"]), list(calls["popen"]))
        check("142: port 8765 first, the next free one past another program, the app's own wherever it runs, and none when all are held",
              moved[0] == 0 and moved[1] == ["--port", "8768"] and "another program is listening, so port 8768" in moved[2]
              and picks["ours"] == (8767, True) and full[0] == 1 and not full[2]
              and full[1] == ["Other programs are listening on ports 8765 to 8785, so Idiograph cannot start."], str(picks))

        # Stop and Restart refuse a port that is not this app's server, and send it nothing
        refusals = []
        for table, cmds in (({8766: {91}}, {91: other_line}),
                            ({8766: {77, 91}}, {77: ours_line, 91: other_line}),
                            ({8766: {92}}, {92: r'"C:\Kites\.venv\Scripts\python.exe" C:\Kites\server.py --port 8766'})):
            reset(table, cmds)
            refusals.append((w.stop_server(8766, logs / "idiograph-8766.pid"), list(calls["quit"]), list(calls["end"])))
        check("142: Stop and Restart refuse a port another program holds, alone or beside the app's, and ask and end nothing there",
              refusals == [(False, [], [])] * 3, str(refusals))
        check("142: the app's own server is Idiograph.exe with --serve, by its file name in any case, and nothing else",
              w.is_ours(ours_line) and w.is_ours(r"C:\Apps\IDIOGRAPH.EXE --serve --port 8770")
              and not w.is_ours(subprocess.list2cmdline([exe, "--port", "8765"]))
              and not w.is_ours(r'"C:\Kites\.venv\Scripts\python.exe" C:\Kites\server.py --port 8765')
              and not w.is_ours(r"python.exe C:\Kites\packaging\windows_launcher.py --serve --port 8765")
              and not w.is_ours(r'"C:\Apps\Idiograph-console.exe" --serve') and not w.is_ours("") and not w.is_ours(other_line))
        words = [[exe, "--serve", "--root", "C:\\Study Notes\\"], ["x", 'say "hi"', "back\\\\", "", "a b\\\"c"],
                 ["Idiograph.exe", "--config", "C:\\a\\b c\\config.json"]]
        check("142: a Windows command line is split as the C runtime splits it, quotes and backslashes and all",
              all(w.argv_of(subprocess.list2cmdline(ws)) == ws for ws in words)
              and w.argv_of('"C:\\a b\\x.exe" one "two three"') == ["C:\\a b\\x.exe", "one", "two three"])

        # Setup's stop: every server of the app in the span, no other program, and always 0 for Setup
        reset({8765: {77}, 8766: {91}, 8770: {78}}, {77: ours_line, 78: ours_line.replace("8765", "8770"), 91: other_line})
        stopped = (w.main(["stop"]), sorted(calls["quit"]), sorted(held), win["trace"].read_text(encoding="utf-8"))
        check("142: Idiograph.exe stop, which Setup and the uninstaller run, stops every server of the app and leaves the rest",
              stopped[0] == 0 and stopped[1] == [8765, 8770] and stopped[2] == [8766]
              and "stopped for Setup" in stopped[3] and not calls["ask"], str(stopped[:3]))
        reset()
        nothing = (w.main(["stop"]), win["trace"].read_text(encoding="utf-8"))
        check("142: with nothing of Idiograph's running, stop says so in the launch line and still answers 0",
              nothing[0] == 0 and "nothing of Idiograph's running for Setup to stop" in nothing[1])

        # Restart from Settings: the server started anew as its own process, and this one ends
        reset()
        w.respawn([exe, "--serve", "--port", "8789", "--no-browser"], {"IDIOGRAPH_RESTARTED": "1"})
        spawned = calls["popen"][0] if calls["popen"] else ([], {})
        check("142: Restart in the Windows app starts the server again as its own process, to the same log, its pid in the pid file",
              spawned[0] == [exe, "--serve", "--port", "8789", "--no-browser"] and spawned[1].get("env") == {"IDIOGRAPH_RESTARTED": "1"}
              and spawned[1].get("cwd") == str(logs) and (logs / "idiograph-8789.pid").read_text(encoding="utf-8") == "5001\n"
              and w.port_of(["x", "--port=8790"]) == "8790" and w.port_of(["x"]) is None)

        # the dialog: Windows's own task dialog, and Open where it cannot be shown
        real_dialog = real["ask"]
        kept_task = w.task_dialog
        outcomes = []
        for stand in (lambda *a: "Restart", lambda *a: "", lambda *a: None,
                      lambda *a: (_ for _ in ()).throw(AttributeError("no TaskDialogIndirect"))):
            w.task_dialog = stand
            outcomes.append(real_dialog())
        w.task_dialog = kept_task
        wide = ctypes.sizeof(ctypes.c_void_p) == 8
        check("142: the dialog's choice comes back as pressed, a dismissal as nothing, and Open where no dialog can be shown",
              outcomes == ["Restart", "", "Open", "Open"], str(outcomes))
        check("142: the task dialog's structures are the header's, packed, 160 bytes on 64-bit Windows, and version 6 of the controls is asked for",
              (not wide or (ctypes.sizeof(w.TASKDIALOGCONFIG) == 160 and ctypes.sizeof(w.TASKDIALOG_BUTTON) == 12
                            and ctypes.sizeof(w.ACTCTXW) == 56 and w.TASKDIALOGCONFIG.pButtons.offset == 64
                            and w.TASKDIALOGCONFIG.nDefaultButton.offset == 72 and w.TASKDIALOGCONFIG.cxWidth.offset == 156))
              and 'name="Microsoft.Windows.Common-Controls" version="6.0.0.0"' in w.MANIFEST
              and 'publicKeyToken="6595b64144ccf1df"' in w.MANIFEST and "TDF_ALLOW_DIALOG_CANCELLATION" in launch_src
              and "config.nDefaultButton = FIRST_BUTTON + choices.index(default)" in launch_src)

        # the listening table, read from iphlpapi's own rows
        v4 = struct.pack("<I", 2) + struct.pack("<II", 2, 0x0100007F) + (8765).to_bytes(2, "big") + b"\0\0" + struct.pack("<III", 0, 0, 77)
        v4 += struct.pack("<II", 2, 0) + (445).to_bytes(2, "big") + b"\0\0" + struct.pack("<III", 0, 0, 4)
        v6 = struct.pack("<I", 1) + bytes(16) + struct.pack("<I", 0) + (8766).to_bytes(2, "big") + b"\0\0" + bytes(16) \
            + struct.pack("<IIII", 0, 0, 2, 91)
        w.tcp_table = lambda family: v4 if family == w.AF_INET else v6
        table = real["listening"](8765, 8785)
        check("142: the listening table comes from GetExtendedTcpTable's rows, IPv4 and IPv6, each port read in network order",
              w.parse_table(v4, w.AF_INET) == [(8765, 77), (445, 4)] and w.parse_table(v6, w.AF_INET6) == [(8766, 91)]
              and w.parse_table(b"", w.AF_INET) == [] and table == {8765: {77}, 8766: {91}}
              and all(word not in launch_src for word in ("netstat", "taskkill", "wmic", "powershell", "pkill", "killall")), str(table))
    finally:
        for name, value in real.items():
            setattr(w, name, value)
        w.tcp_table = real_tcp
        os.environ.update(kept_env)

    # what goes to cli, mcp and the server, and the one launch at a time
    routed = []
    kept_fns = {n: getattr(w, n) for n in ("command_line", "mcp_server", "serve", "launch")}
    try:
        w.command_line = lambda args: routed.append(("cli", args)) or 0
        w.mcp_server = lambda args: routed.append(("mcp", args)) or 0
        w.serve = lambda port, extra: routed.append(("serve", port, extra)) or 0
        w.launch = lambda port, extra, trace: routed.append(("launch", port, extra)) or 0
        w.places = lambda home_=None, env=None: app_folders.folders("win32", home)
        for argv in (["cli", "cases", "--json"], ["mcp", "--demo"], ["--serve", "--port", "8789", "--no-browser"], ["--port=8790"]):
            w.main(argv)
    finally:
        for n, f in kept_fns.items():
            setattr(w, n, f)
        w.places = real["places"]
    check("142: cli and mcp go to the command line and the MCP server, --serve to the server, the rest to a launch, one at a time",
          routed == [("cli", ["cli", "cases", "--json"][1:]), ("mcp", ["--demo"]), ("serve", "8789", ["--no-browser"]),
                     ("launch", "8790", [])]
          and "with one_launch():" in inspect.getsource(w.main) and "msvcrt.LK_LOCK" in launch_src, str(routed))
    entry_win = mcp_server.server_command(frozen=True, executable=exe, system="win32")
    entry_mac = mcp_server.server_command(frozen=True, executable="/Applications/Idiograph.app/Contents/MacOS/Idiograph",
                                          system="darwin")
    check("142: Add Idiograph to Claude Desktop names the console twin in the Windows app and the app itself on a Mac",
          entry_win == [r"C:\Users\Kim Example\AppData\Local\Programs\Idiograph\Idiograph-console.exe", "mcp"]
          and entry_mac == ["/Applications/Idiograph.app/Contents/MacOS/Idiograph", "mcp"]
          and app_folders.CONSOLE_EXE == "Idiograph-console.exe" and app_folders.WINDOWED_EXE == "Idiograph.exe")

    # the server: Restart works through the launcher's SPAWN, Quit names the Start menu
    kept_server = (server_mod.SPAWN, server_mod.EXEC, server_mod.RELAUNCH, server_mod.FROZEN)
    spawns, execs = [], []
    try:
        # a Windows run with no way to start the server anew, which since 14 October none is (see 144)
        server_mod.SPAWN = None
        blocked = (server_mod.restart_blocked("win32"), server_mod.restart_blocked("darwin"))
        server_mod.SPAWN = lambda command, env: spawns.append((list(command), dict(env)))
        server_mod.EXEC = lambda path, argv, env: execs.append(argv)
        server_mod.RELAUNCH = [exe, "--serve", "--port", "8789"]
        unblocked = server_mod.restart_blocked("win32")
        with ctx.redirect_stdout(io.StringIO()):
            server_mod.finish("restart", 8789)
    finally:
        server_mod.SPAWN, server_mod.EXEC, server_mod.RELAUNCH, server_mod.FROZEN = kept_server
    check("142: Restart with no way to start anew on Windows says it cannot, and in the Windows app the launcher's SPAWN "
          "starts the server anew",
          blocked == (server_mod.named(server_mod.WINDOWS_LINE), None) and unblocked is None and not execs
          and spawns and spawns[0][0] == [exe, "--serve", "--port", "8789"] and spawns[0][1].get(server_mod.RESTARTED) == "1"
          and "server.SPAWN = respawn" in inspect.getsource(w.serve) and server_mod.SPAWN is kept_server[0])

    # ── C. the build: its pins, the icon, the recording, the spec and the Inno Setup script
    check("142: the build takes build_mac's pins but certifi, its modules and its stage, and freezes the Windows launcher",
          build.PINS == tuple(p for p in build_mac.PINS if not p.startswith("certifi")) and len(build.PINS) == 4
          and build.MODULES == build_mac.MODULES and build.ENTRY == support.source("packaging/windows_launcher.py")
          and "build_mac.stage_recordings(build_mac.stage_cases(stage))" in build_src and ".venv" not in build_src.split('"""', 2)[2]
          and "demo = stage_cases(stage)" in inspect.getsource(build_mac.stage_demo))
    ico = build.ico_bytes((16, 32, 256))
    count = struct.unpack("<HHH", ico[:6])
    entries = [struct.unpack("<BBBBHHII", ico[6 + 16 * i:22 + 16 * i]) for i in range(3)]
    check("142: the icon is an .ico of make_app's drawing, each size a PNG, 256 written as 0",
          count == (0, 1, 3) and [e[0] for e in entries] == [16, 32, 0] and all(e[4:6] == (1, 32) for e in entries)
          and all(ico[e[7]:e[7] + 8] == b"\x89PNG\r\n\x1a\n" and e[7] + e[6] <= len(ico) for e in entries)
          and entries[0][7] == 6 + 16 * 3, str(entries))
    # the demo's recordings (recvoices, 12 November 2026): committed in packaging/recording, each under a name that
    # carries the hash of the transcript it was made from, staged by build_mac's own `stage_recordings`, which area 16
    # checks, and nothing spoken here
    ignored_tool = read(support.source(".gitignore")).splitlines()
    check("142: the Windows build stages the demo's recordings through the Mac build's own step, speaks nothing, and the "
          "recordings and their licence are the folder's committed files",
          "packaging/recording/*" in ignored_tool and "!packaging/recording/*-Initial-*.m4a" in ignored_tool
          and "!packaging/recording/LICENSE-audio.md" in ignored_tool
          and not hasattr(build, "speak") and "--speak" not in build_src and "make_demo" not in build_src)
    stage, frozen, dist = base / "stage", base / "frozen" / "Idiograph", base / "dist"
    # the installer is Tauri's NSIS one since 17 October (the third Tauri build, area 173), its settings in
    # tauri.conf.json and its own steps in hooks.nsh, where Inno Setup's script stood
    import json as json_
    conf = json_.loads(read(support.source("packaging/tauri/src-tauri/tauri.conf.json")))
    nsis = conf["bundle"]["windows"]["nsis"]
    hooks = read(support.source("packaging/tauri/src-tauri/windows/hooks.nsh"))
    check("142, updated 17 October (173): Setup installs for the current user with no administrator prompt, Tauri's "
          "NSIS installer for the one user, in its own folder under LocalAppData",
          nsis["installMode"] == "currentUser" and "nsis" in conf["bundle"]["targets"]
          and '["nsis"]' in build_src and "Inno Setup 6" not in build_src and "ISCC" not in build_src
          and "admin" not in json_.dumps(conf).lower())
    check("142, updated 17 October (173): it makes a Start menu entry, a desktop shortcut only when ticked on its last "
          "page, and an uninstaller in Settings, Apps, the version the server's, set as it builds",
          conf["productName"] == "Idiograph" and conf["bundle"]["publisher"] == "Adam Knowles"
          and build.window.overrides(server_mod.VERSION)["version"] == server_mod.VERSION == conf["version"]
          and build.version_info("0.9.0") == "0.9.0.0" and build.app_version() == server_mod.VERSION
          and "startMenuFolder" not in nsis)
    check("142, updated 17 October (173): the Inno Setup install of 0.9.0 goes first, quietly, by its own uninstaller, "
          "found by its id for ever, and its going waited for, and nothing of the user's data folder is touched",
          f"{{{build.APP_ID}}}_is1" in hooks and "/VERYSILENT /SUPPRESSMSGBOXES /NORESTART" in hooks
          and "!macro NSIS_HOOK_PREINSTALL" in hooks and "${ExitDo}" in hooks
          and "APPDATA" not in hooks.split("!define IDIOGRAPH_INNO_KEY", 1)[1] and "RMDir" not in hooks and "Delete " not in hooks)
    check("142, updated 17 October (173): Setup and the uninstaller stop a running Idiograph first, through the "
          "console twin's own stop, with no window",
          "!macro NSIS_HOOK_PREUNINSTALL" in hooks and hooks.count("!insertmacro IDIOGRAPH_STOP") == 2
          and """nsExec::Exec '"$INSTDIR\\server\\Idiograph-console.exe" stop'""" in hooks)
    check("142, updated 17 October (173): unsigned, Tauri signs nothing, and signed it signs the window and the "
          "installer with the same thumbprint signtool signs the server with",
          "bundle" not in build.window.overrides("0.9.1") and build.window.overrides("0.9.1", windows_sign="ABC123")["bundle"]
          == {"windows": {"certificateThumbprint": "ABC123", "digestAlgorithm": "sha256", "timestampUrl": "http://timestamp.digicert.com"}})
    kept_tool = build.find_signtool
    try:
        build.find_signtool = lambda: None
        try:
            build.signing("ABC123")
            no_tool = ""
        except SystemExit as exc:
            no_tool = str(exc)
        build.find_signtool = lambda: r"C:\Kits\signtool.exe"
        with_tool = build.signing("ABC123")
    finally:
        build.find_signtool = kept_tool
    unsigned = build.signing(None)
    check("142: signing is one place, a certificate's thumbprint through signtool, and without one the build says unsigned in one line",
          unsigned[0] is None and "SmartScreen" in unsigned[1] and "More info, Run anyway" in unsigned[1] and "\n" not in unsigned[1]
          and "signtool" in no_tool and with_tool[0].startswith('"C:\\Kits\\signtool.exe" sign /sha1 ABC123 /fd sha256 /tr ')
          and with_tool[0].endswith("/td sha256 $f") and build_src.count("SIGNTOOL = ") == 1)
    (base / "spec").mkdir(parents=True, exist_ok=True)
    spec_text = build.write_spec(base / "spec", stage).read_text(encoding="utf-8")
    check("142: PyInstaller makes one folder with two executables, Idiograph windowed and Idiograph-console, the Mac app's data and the .ico",
          "name='Idiograph', console=False" in spec_text and "name='Idiograph-console', console=True" in spec_text
          and "coll = COLLECT(windowed, console, a.binaries, a.datas, name='Idiograph'" in spec_text
          and spec_text.count("Idiograph.ico") == 2 and "'app_folders'" in spec_text and "'static')" in spec_text
          and "'demo')" in spec_text and "config.json" in spec_text and "'tkinter'" in spec_text
          and "check_frozen(frozen, app)" in build_src and '"cli", "--help"' in build_src)

    # 22 October 2026: Windows Defender took 0.9.3 for Trojan:Win32/Bearfoos.x!ml. Each executable now
    # carries a version resource, PyInstaller's bootloader is compiled on the machine that builds, and
    # Defender scans what the build made. The version files are read back as PyInstaller reads them, by
    # eval, here with stand-ins for its classes that keep what they are given
    def resource_of(text):
        def keep(kind):
            return lambda *a, **k: {"kind": kind, "args": a, **k}
        names_ = {n: keep(n) for n in ("VSVersionInfo", "FixedFileInfo", "StringFileInfo", "StringTable",
                                       "VarFileInfo", "VarStruct")}
        names_["StringStruct"] = lambda key, value: (key, value)
        info = eval(text, {"__builtins__": {}}, names_)
        return info["ffi"], dict(info["kids"][0]["args"][0][0]["args"][1])
    conf_bundle = conf["bundle"]
    sift_base = base / "spec-sift"
    sift_base.mkdir(parents=True, exist_ok=True)
    sift_spec = build.write_spec(sift_base, stage, "sift", "1.2.3").read_text(encoding="utf-8")
    files = {kind: base / "spec" / f"Idiograph{tail}-version.txt" for kind, tail in (("windowed", ""), ("console", "-console"))}
    ffi, strings = resource_of(read(files["console"])) if files["console"].is_file() else ({}, {})
    _, windowed_strings = resource_of(read(files["windowed"])) if files["windowed"].is_file() else ({}, {})
    _, sift_strings = resource_of(read(sift_base / "Sift-version.txt")) if (sift_base / "Sift-version.txt").is_file() else ({}, {})
    four = build.version_info(server_mod.VERSION)
    check("142, 22 October 2026: both executables carry a full Windows version resource, the publisher and copyright "
          "tauri.conf.json gives the window, the app's name and version, and each file's own name",
          f"version={str(files['windowed'])!r}" in spec_text and f"version={str(files['console'])!r}" in spec_text
          and strings.get("CompanyName") == conf_bundle["publisher"] == build.PUBLISHER
          and strings.get("LegalCopyright") == conf_bundle["copyright"]
          and strings.get("ProductName") == strings.get("FileDescription") == "Idiograph"
          and strings.get("FileVersion") == strings.get("ProductVersion") == four
          and ffi.get("filevers") == ffi.get("prodvers") == tuple(int(n) for n in four.split("."))
          and strings.get("OriginalFilename") == "Idiograph-console.exe" and strings.get("InternalName") == "Idiograph-console"
          and windowed_strings.get("OriginalFilename") == "Idiograph.exe" and windowed_strings.get("InternalName") == "Idiograph"
          and sift_strings.get("ProductName") == "Sift" and sift_strings.get("FileVersion") == "1.2.3.0"
          and sift_strings.get("OriginalFilename") == "Sift.exe" and "Sift-console-version.txt" in sift_spec,
          str(strings))
    hooks_company = [ln for ln in hooks.splitlines() if ln.startswith("VIAddVersionKey")]
    check("142, 22 October 2026: the installer names the same publisher in its own version resource, which Tauri's "
          "NSIS script leaves without a company",
          hooks_company == [f'VIAddVersionKey "CompanyName" "{conf_bundle["publisher"]}"'], str(hooks_company))
    install = [str(c) for c in build.bootloader_install(Path("py.exe"))]
    check("142, 22 October 2026: PyInstaller is built from its source at the pin, its bootloader compiled on the machine "
          "that builds, no wheel taken from pip's cache, and the build stops when pip said nothing of compiling it",
          build.pyinstaller_pin() in build_mac.PINS and install[-1] == build.pyinstaller_pin()
          and "--no-binary" in install and install[install.index("--no-binary") + 1] == "pyinstaller"
          and "--no-cache-dir" in install and "--verbose" in install
          and build.BOOTLOADER_ENV == {"PYINSTALLER_COMPILE_BOOTLOADER": "1"}
          and "install_bootloader(py)" in inspect.getsource(build.build_venv)
          and "BOOTLOADER_SAID not in said" in inspect.getsource(build.install_bootloader), str(install))

    # Defender's scan, MpCmdRun stood in for: a clean report, a finding, a scan that could not run, none, off
    class Done:
        def __init__(self, code, out=""):
            self.returncode, self.stdout, self.stderr = code, out, ""
    shipped = base / "scan"
    (shipped / "Idiograph").mkdir(parents=True, exist_ok=True)
    (shipped / "Idiograph-Setup.exe").write_bytes(b"MZ")
    paths_ = [shipped / "Idiograph", shipped / "Idiograph-Setup.exe", shipped / "never-built.exe"]
    report = ("Scan starting...\nScan finished.\nScanning found 1 threats.\n"
              "<===========================LIST OF DETECTED THREATS==========================>\n"
              "----------------------------- Threat information ------------------------------\n"
              "Threat                  : Trojan:Win32/Madeup.x!ml\nResources               : 1 total\n"
              f"    file                : {shipped / 'Idiograph-Setup.exe'}\n")

    def scan_with(answers, **kw):
        asked, out = [], io.StringIO()
        def runner(cmd, **_k):
            asked.append(cmd)
            return answers(cmd)
        with ctx.redirect_stdout(out):
            code = build.defender_scan(paths_, runner=runner, **kw)
        return code, asked, out.getvalue()
    clean = scan_with(lambda c: Done(0, "Scan finished."), tool="MpCmdRun.exe", on=True)
    flagged = scan_with(lambda c: Done(2, report) if c[-2].endswith("Setup.exe") else Done(0), tool="MpCmdRun.exe", on=True)
    broken = scan_with(lambda c: Done(0) if c[1] == "-SignatureUpdate" else Done(-2147024894), tool="MpCmdRun.exe", on=True)
    missing = scan_with(lambda c: Done(0), tool="", on=True)
    off = scan_with(lambda c: Done(0), tool="MpCmdRun.exe", on=False)
    scans = [c for c in clean[1] if "-Scan" in c]
    check("142, 22 October 2026: Defender scans the frozen folder and the installer with nothing removed, and a finding "
          "fails the run with the file and the detection's name",
          clean[0] == 0 and clean[1][0] == ["MpCmdRun.exe", "-SignatureUpdate"] and len(scans) == 2
          and all(c[1:4] == ["-Scan", "-ScanType", "3"] and c[-1] == "-DisableRemediation" for c in scans)
          and "never-built.exe" in clean[2] and "!ml" in clean[2]
          and flagged[0] == 1 and f"::error file={shipped / 'Idiograph-Setup.exe'}::Windows Defender detected "
          "Trojan:Win32/Madeup.x!ml" in flagged[2]
          and build.scanned(Path("b"), Path("d"), "sift") == [Path("b/pyinstaller-dist/Sift"), Path("b/target/release/Sift.exe"),
                                                              Path("d/Sift-Setup.exe")], flagged[2][-400:])
    check("142, 22 October 2026: with Defender missing, off or unable to scan, the run says so and carries on",
          broken[0] == 0 and "could not scan" in broken[2] and missing[0] == 0 and missing[1] == []
          and "not on this machine" in missing[2] and off[0] == 0 and off[1] == [] and "is off" in off[2],
          broken[2][-300:])

    # a dry run here: the scripts written, every step said, nothing installed or run
    out = base / "dry"
    said = io.StringIO()
    before = sorted(p.name for p in TOOL.iterdir())
    with ctx.redirect_stdout(said):
        dry = build.main(["--dry-run", "--out", str(out)])
    said = said.getvalue()
    staged = out / "build" / "stage"
    check("142, updated 17 October (173): a dry run writes the stage, the spec and Tauri's settings into its folder, "
          "says each step and runs none",
          dry == 0 and json_.loads((out / "build" / "tauri-config.json").read_text(encoding="utf-8")) == {"version": server_mod.VERSION}
          and (out / "build" / "Idiograph-windows.spec").is_file() and (staged / "Idiograph.ico").is_file()
          and all((staged / "demo" / build_mac.recording_path(n)).is_file() == bool(build_mac.committed_recording(n))
                  for n in build_mac.DEMO_CASES)
          and build_mac.stage_recordings(base / "dry-again") in said
          and (staged / "demo" / "Rowan" / "Rowan - EN & ES.xlsx").is_file() and not (out / "build" / "venv").exists()
          and all(w_ in said for w_ in ("Would make", "Would run PyInstaller", "Would run Tauri", "NSIS installer", "Unsigned"))
          and sorted(p.name for p in TOOL.iterdir()) == before, said[-300:])
    if sys.platform != "win32":
        try:
            build.main(["--out", str(base / "nowhere")])
            elsewhere = ""
        except SystemExit as exc:
            elsewhere = str(exc)
        check("142: off Windows a build without --dry-run stops in one line and builds nothing",
              "built on Windows" in elsewhere and "--dry-run" in elsewhere and not (base / "nowhere" / "build" / "venv").exists())
    else:
        skip("142: off Windows a build without --dry-run stops in one line", "this is Windows")

    # ── D. the workflow that builds it
    jobs = workflow.split("\njobs:\n", 1)[1] if "\njobs:\n" in workflow else ""
    windows = jobs.split("\n  mac-app:\n", 1)[0]
    installer = windows.split("# the installer", 1)[1] if "# the installer" in windows else ""
    release = jobs.split("\n  release:\n", 1)[1].split("\n  macos:\n", 1)[0] if "\n  release:\n" in jobs else ""
    gated = [ln for ln in installer.splitlines() if ln.strip().startswith("- ")]
    mac_job = jobs.split("\n  mac-app:\n", 1)[1].split("\n  release:\n", 1)[0] if "\n  mac-app:\n" in jobs else ""
    check("142, updated 20 October (229): the installers are built by hand and on a version tag, never on a push to "
          "main, the Windows one after the suite on the same machine, on the Python the app carries, by Tauri's bundler",
          '\n    tags: ["v*", "idiograph-v*", "sift-v*", "trace-v*"]\n' in workflow and "\n      installer:\n" in workflow
          and "default: true" in workflow
          and "INSTALLER: ${{ github.ref_type == 'tag' || (github.event_name == 'workflow_dispatch' && inputs.installer) }}"
          in windows and windows.index("python tests/test_idiograph.py") < windows.index("python packaging/build_windows.py")
          and len(gated) == 6 and all(ln.strip() == "- if: env.INSTALLER == 'true'" for ln in gated)
          and 'python-version: "3.13"' in installer and "@tauri-apps/cli@$env:TAURI_CLI_VERSION" in installer
          and 'TAURI_CLI_VERSION: "2.12.1"' in workflow, str(gated))
    check("142, updated 20 October (229): it needs no Inno Setup, and uploads the app's Setup as the run's artifact",
          "innosetup" not in workflow and "ISCC" not in workflow
          and "uses: actions/upload-artifact@v4" in installer and "path: dist/${{ env.APP_NAME }}-Setup.exe" in installer
          and "if-no-files-found: error" in installer)
    check("173, updated 9 November (relfix): the Mac app is built on a tag or by hand when asked, for Apple Silicon "
          "alone from python.org's Python, its disk image and update file the run's artifact",
          "if: github.ref_type == 'tag' || (github.event_name == 'workflow_dispatch' && inputs.mac_app)" in mac_job
          and "rustup target add aarch64-apple-darwin\n" in mac_job and "x86_64-apple-darwin" not in mac_job
          and "-macos11.pkg" in mac_job
          and "python3 packaging/build_mac.py --unsigned --app ${{ env.APP }}" in mac_job
          and "dist/${{ env.APP_NAME }}.dmg" in mac_job
          and "dist/${{ env.APP_NAME }}.app.tar.gz" in mac_job and "\n      mac_app:\n" in workflow)
    check("142, updated 20 October (229) and 9 November (linux57): on a tag a small Linux job puts the tagged app's three files on a draft "
          "release with the run's own token, and nothing else may write",
          "if: github.ref_type == 'tag'" in release and "needs: [windows, mac-app, linux-app]" in release
          and "runs-on: ubuntu-latest" in release
          and '"$APP_NAME-Setup.exe" "$APP_NAME.dmg" "$APP_NAME.app.tar.gz"' in release
          and "contents: write" in release and "--draft" in release and "GH_TOKEN: ${{ github.token }}" in release
          and "\npermissions:\n  contents: read\n" in workflow and workflow.count("contents: write") == 1
          and "secrets." not in workflow and "matrix" not in workflow)

