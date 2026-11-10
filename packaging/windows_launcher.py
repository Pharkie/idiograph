#!/usr/bin/env python3
"""The two executables of the Windows app, Idiograph.exe and Idiograph-console.exe, as
`build_windows.py` makes them.

The Windows counterpart of `mac_launcher.py`, the same behaviour in Windows terms. A double-click
on Idiograph, in the Start menu or on the desktop, with nothing on the port starts the server with no
console window, and the server opens the browser itself. A double-click while it runs offers Stop,
Restart and Open, with Open the default, in Windows's own task dialog, which needs nothing
downloaded. Either way this process then ends.

The server is Idiograph.exe run again with `--serve`, its output in
`%LOCALAPPDATA%\\Idiograph\\Logs\\idiograph.log` and its process number in `idiograph-<port>.pid`
beside it. Port 8765 first. When another program holds it, the next free port, and a server of
this app already listening on one of those ports is the one the dialog offers. Stop and Restart only
ever touch a process listening on that port, and only when it is this app's server, Idiograph.exe
run with --serve: Stop asks it to quit, as Quit in Settings does, and ends it only when it still
listens five seconds later.

    Idiograph [--port N] [--no-browser] [--root FOLDER] [--config FILE] [--verbose]
    Idiograph --serve [the same]       the server itself
    Idiograph stop                     every server of this app stopped, with no dialog, for Setup
    Idiograph-console cli <command>    the command line an AI agent works through, docs/agents.md
    Idiograph-console mcp [--project NAME | --root FOLDER]   the MCP server, for Claude Desktop

`cli` and `mcp` go through the console twin, since a windowed program cannot print to the terminal
that ran it. Both executables run this same file. `IDIOGRAPH_PORT` and `IDIOGRAPH_ARGS` work as they
do on the Mac, and every launch leaves a line with its date and its outcome in
`%TEMP%\\idiograph-launch.log`. The folders come from `app_folders`, which decides the Mac app's
too. Everything Windows's own is reached through ctypes, by a name the suite stands in for, so the
logic runs on any machine.
"""
from __future__ import annotations

import contextlib
import ctypes
import json
import os
import subprocess
import sys
import time
import urllib.request
from datetime import datetime
from pathlib import Path, PureWindowsPath

# run from the source the app's modules are a folder up, and frozen they are in the bundle
if not getattr(sys, "frozen", False):
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import boot  # noqa: E402  the family's folders on the path (boot.py), the bundle's own frozen

boot.setup()
import app_folders  # noqa: E402  the folders the app writes in, the Mac app's too
import app_identity  # noqa: E402  which of the three apps, by this launcher's own name

# the app this launcher is, by its own name, Idiograph's unless it is Sift's or Trace's, and its port,
# 8765 for Idiograph (see app_identity)
APP = app_identity.chosen([])
PORT = app_identity.APPS[APP]["port"]
# the ports tried after the first when another program holds it
SPAN = 20
SERVE = "--serve"
STOP = "stop"
# the windowed executable, which every server of this app runs as, Sift.exe for Sift (build 6 of the
# split, 20 October), so Sift's Setup stops Sift's servers and never Idiograph's
EXECUTABLE = app_folders.windowed_exe(APP)
TITLE = app_identity.APPS[APP]["name"]
QUESTION = f"{TITLE} is running."
CHOICES = ("Stop", "Restart", "Open")
DEFAULT = "Open"
URL = "http://127.0.0.1:{port}/"
LOG = "idiograph.log"
# a server starts with no console window and in a process group of its own, so it outlives the launch
CREATE_NEW_PROCESS_GROUP = 0x00000200
CREATE_NO_WINDOW = 0x08000000
DETACHED = CREATE_NEW_PROCESS_GROUP | CREATE_NO_WINDOW


def places(home: Path | None = None, env: dict | None = None) -> dict:
    """The data folder, the logs folder and the trace file on Windows, from `app_folders`."""
    return app_folders.folders("win32", home, env, app=APP)


def logs_dir() -> Path:
    return places()["logs"]


class Trace:
    """The two lines a launch leaves in %TEMP%: its date first, then its outcome or the reason it
    stopped. Dates and port numbers only, never a path."""

    def __init__(self, path: Path | None = None):
        self.path = Path(path) if path is not None else places()["trace"]
        self.done = False

    def line(self, port, words: str, final: bool = True) -> None:
        self.done = self.done or final
        stamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        try:
            with open(self.path, "a", encoding="utf-8") as fh:
                fh.write(f"{stamp} port {port}: {words}\n")
        except OSError:
            pass


def echo(message: str) -> None:
    """A line on stderr for a run from a terminal. The windowed executable has none."""
    if sys.stderr is not None:
        try:
            print(f"Idiograph: {message}", file=sys.stderr)
        except (OSError, ValueError):
            pass


# ── the dialogs, Windows's own ──────────────────────────────────────────────────────────────────

MB_OK = 0x0
MB_ICONWARNING = 0x30
MB_ICONINFORMATION = 0x40
MB_SETFOREGROUND = 0x10000


def message_box(message: str, flags: int) -> None:
    try:
        ctypes.WinDLL("user32").MessageBoxW(None, message, TITLE, MB_OK | MB_SETFOREGROUND | flags)
    except (OSError, AttributeError):
        pass


def alert(message: str) -> None:
    """A box with one OK button, echoed to stderr for a run from a terminal."""
    echo(message)
    message_box(message, MB_ICONWARNING)


def notify(message: str) -> None:
    echo(message)
    message_box(message, MB_ICONINFORMATION)


class TASKDIALOG_BUTTON(ctypes.Structure):
    _layout_ = "ms"
    _pack_ = 1
    _fields_ = [("nButtonID", ctypes.c_int), ("pszButtonText", ctypes.c_wchar_p)]


class TASKDIALOGCONFIG(ctypes.Structure):
    """commctrl.h's TASKDIALOGCONFIG, packed to one byte as the header packs it: 160 bytes on 64-bit
    Windows."""
    _layout_ = "ms"
    _pack_ = 1
    _fields_ = [("cbSize", ctypes.c_uint), ("hwndParent", ctypes.c_void_p), ("hInstance", ctypes.c_void_p),
                ("dwFlags", ctypes.c_int), ("dwCommonButtons", ctypes.c_int), ("pszWindowTitle", ctypes.c_wchar_p),
                ("pszMainIcon", ctypes.c_void_p), ("pszMainInstruction", ctypes.c_wchar_p),
                ("pszContent", ctypes.c_wchar_p), ("cButtons", ctypes.c_uint),
                ("pButtons", ctypes.POINTER(TASKDIALOG_BUTTON)), ("nDefaultButton", ctypes.c_int),
                ("cRadioButtons", ctypes.c_uint), ("pRadioButtons", ctypes.c_void_p),
                ("nDefaultRadioButton", ctypes.c_int), ("pszVerificationText", ctypes.c_wchar_p),
                ("pszExpandedInformation", ctypes.c_wchar_p), ("pszExpandedControlText", ctypes.c_wchar_p),
                ("pszCollapsedControlText", ctypes.c_wchar_p), ("pszFooterIcon", ctypes.c_void_p),
                ("pszFooter", ctypes.c_wchar_p), ("pfCallback", ctypes.c_void_p),
                ("lpCallbackData", ctypes.c_void_p), ("cxWidth", ctypes.c_uint)]


class ACTCTXW(ctypes.Structure):
    """winbase.h's ACTCTXW, 56 bytes on 64-bit Windows."""
    _fields_ = [("cbSize", ctypes.c_uint32), ("dwFlags", ctypes.c_uint32), ("lpSource", ctypes.c_wchar_p),
                ("wProcessorArchitecture", ctypes.c_ushort), ("wLangId", ctypes.c_ushort),
                ("lpAssemblyDirectory", ctypes.c_wchar_p), ("lpResourceName", ctypes.c_wchar_p),
                ("lpApplicationName", ctypes.c_wchar_p), ("hModule", ctypes.c_void_p)]


TDF_ALLOW_DIALOG_CANCELLATION = 0x0008
# the custom buttons' ids, the first choice's and up
FIRST_BUTTON = 100
# the task dialog lives in version 6 of the common controls, which a program asks for in its manifest.
# PyInstaller's own asks for it, and this one, activated around the dialog, makes sure of it
MANIFEST = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<assembly xmlns="urn:schemas-microsoft-com:asm.v1" manifestVersion="1.0">
  <dependency>
    <dependentAssembly>
      <assemblyIdentity type="win32" name="Microsoft.Windows.Common-Controls" version="6.0.0.0"
                        processorArchitecture="*" publicKeyToken="6595b64144ccf1df" language="*"/>
    </dependentAssembly>
  </dependency>
</assembly>
"""


@contextlib.contextmanager
def common_controls():
    """comctl32, version 6, with an activation context from MANIFEST around it, written beside the
    log. Without the context the version the program's own manifest asks for."""
    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
    cookie = ctypes.c_size_t(0)
    context = None
    try:
        manifest = logs_dir() / "common-controls.manifest"
        manifest.parent.mkdir(parents=True, exist_ok=True)
        if not manifest.is_file() or manifest.read_text(encoding="utf-8") != MANIFEST:
            manifest.write_text(MANIFEST, encoding="utf-8")
        act = ACTCTXW(cbSize=ctypes.sizeof(ACTCTXW), lpSource=str(manifest))
        kernel32.CreateActCtxW.restype = ctypes.c_void_p
        kernel32.CreateActCtxW.argtypes = (ctypes.POINTER(ACTCTXW),)
        kernel32.ActivateActCtx.argtypes = (ctypes.c_void_p, ctypes.POINTER(ctypes.c_size_t))
        kernel32.DeactivateActCtx.argtypes = (ctypes.c_ulong, ctypes.c_size_t)
        kernel32.ReleaseActCtx.argtypes = (ctypes.c_void_p,)
        handle = kernel32.CreateActCtxW(ctypes.byref(act))
        if handle and handle != ctypes.c_void_p(-1).value:
            if kernel32.ActivateActCtx(handle, ctypes.byref(cookie)):
                context = handle
            else:
                kernel32.ReleaseActCtx(handle)
    except (OSError, AttributeError, ValueError):
        context = None
    try:
        yield ctypes.WinDLL("comctl32")
    finally:
        if context:
            kernel32.DeactivateActCtx(0, cookie.value)
            kernel32.ReleaseActCtx(context)


def task_dialog(question: str, choices: tuple[str, ...], default: str) -> str | None:
    """Windows's task dialog with one button for each choice, `default` the one Enter presses. The
    choice pressed, "" when it is closed or Escape is pressed, and None when it cannot be shown."""
    buttons = (TASKDIALOG_BUTTON * len(choices))(*[TASKDIALOG_BUTTON(FIRST_BUTTON + i, c) for i, c in enumerate(choices)])
    config = TASKDIALOGCONFIG()
    config.cbSize = ctypes.sizeof(TASKDIALOGCONFIG)
    config.dwFlags = TDF_ALLOW_DIALOG_CANCELLATION
    config.pszWindowTitle = TITLE
    config.pszMainInstruction = question
    config.cButtons = len(choices)
    config.pButtons = ctypes.cast(buttons, ctypes.POINTER(TASKDIALOG_BUTTON))
    config.nDefaultButton = FIRST_BUTTON + choices.index(default)
    pressed = ctypes.c_int(0)
    try:
        # sharp on a screen scaled past 100 percent, where Windows would otherwise stretch the dialog
        ctypes.WinDLL("user32").SetProcessDpiAwarenessContext(ctypes.c_void_p(-4))
    except (OSError, AttributeError):
        pass
    with common_controls() as comctl:
        show = comctl.TaskDialogIndirect
        show.argtypes = (ctypes.POINTER(TASKDIALOGCONFIG), ctypes.POINTER(ctypes.c_int), ctypes.c_void_p, ctypes.c_void_p)
        show.restype = ctypes.c_long
        if show(ctypes.byref(config), ctypes.byref(pressed), None, None) != 0:
            return None
    at = pressed.value - FIRST_BUTTON
    return choices[at] if 0 <= at < len(choices) else ""


def ask() -> str:
    """The running dialog: the button pressed, or "" when it is dismissed. Where no dialog can be
    shown, Open, the default, so a double-click still reaches the page."""
    try:
        picked = task_dialog(QUESTION, CHOICES, DEFAULT)
    except (OSError, AttributeError, ValueError, TypeError):
        picked = None
    return DEFAULT if picked is None else picked


def open_page(url: str) -> None:
    """The page in the default browser."""
    os.startfile(url)  # noqa: S606  Windows's own way to open a link in the default browser


# ── the processes listening ─────────────────────────────────────────────────────────────────────

AF_INET, AF_INET6 = 2, 23
TCP_TABLE_OWNER_PID_LISTENER = 3
NO_ERROR, ERROR_INSUFFICIENT_BUFFER = 0, 122
# the bytes of a row of each table: the IPv4 row is six DWORDs, state, local address, local port,
# remote address, remote port and pid, and the IPv6 row the local address in 16 bytes, its scope,
# the local port, the remote address and its scope, the remote port, the state and the pid
ROW = {AF_INET: 24, AF_INET6: 56}
# where in a row the local port and the pid are
PORT_AT = {AF_INET: 8, AF_INET6: 20}
PID_AT = {AF_INET: 20, AF_INET6: 52}


def tcp_table(family: int) -> bytes:
    """The listening sockets of one address family with their process numbers, as iphlpapi's
    GetExtendedTcpTable gives them, which needs no program run and no words that change with the
    language Windows is in."""
    get = ctypes.WinDLL("iphlpapi").GetExtendedTcpTable
    get.argtypes = (ctypes.c_void_p, ctypes.POINTER(ctypes.c_ulong), ctypes.c_int, ctypes.c_ulong,
                    ctypes.c_int, ctypes.c_ulong)
    get.restype = ctypes.c_ulong
    size = ctypes.c_ulong(0)
    get(None, ctypes.byref(size), 0, family, TCP_TABLE_OWNER_PID_LISTENER, 0)
    for _ in range(4):
        buf = ctypes.create_string_buffer(max(size.value, 4))
        code = get(buf, ctypes.byref(size), 0, family, TCP_TABLE_OWNER_PID_LISTENER, 0)
        if code == NO_ERROR:
            return buf.raw[:size.value]
        if code != ERROR_INSUFFICIENT_BUFFER:
            break
    return b""


def parse_table(raw: bytes, family: int) -> list[tuple[int, int]]:
    """Each row's local port and pid. The table is its count, a DWORD, then the rows, and a port is
    in network order in the first two bytes of its DWORD."""
    if len(raw) < 4:
        return []
    size, rows = ROW[family], []
    for i in range(int.from_bytes(raw[:4], "little")):
        row = raw[4 + i * size:4 + (i + 1) * size]
        if len(row) < size:
            break
        port = int.from_bytes(row[PORT_AT[family]:PORT_AT[family] + 2], "big")
        rows.append((port, int.from_bytes(row[PID_AT[family]:PID_AT[family] + 4], "little")))
    return rows


def listening(first: int, last: int) -> dict[int, set[int]]:
    """The processes listening on each port from `first` to `last`, by port."""
    table: dict[int, set[int]] = {}
    for family in (AF_INET, AF_INET6):
        try:
            rows = parse_table(tcp_table(family), family)
        except (OSError, AttributeError, ValueError):
            rows = []
        for port, pid in rows:
            if first <= port <= last and pid:
                table.setdefault(port, set()).add(pid)
    return table


PROCESS_QUERY_LIMITED_INFORMATION = 0x1000
# NtQueryInformationProcess's class for a process's command line, Windows 8.1 and later
PROCESS_COMMAND_LINE = 60


def command_of(pid: int) -> str:
    """The command line a process was started with, or "" when it cannot be read."""
    kernel32, ntdll = ctypes.WinDLL("kernel32"), ctypes.WinDLL("ntdll")
    kernel32.OpenProcess.argtypes = (ctypes.c_ulong, ctypes.c_int, ctypes.c_ulong)
    kernel32.OpenProcess.restype = ctypes.c_void_p
    kernel32.CloseHandle.argtypes = (ctypes.c_void_p,)
    query = ntdll.NtQueryInformationProcess
    query.argtypes = (ctypes.c_void_p, ctypes.c_int, ctypes.c_void_p, ctypes.c_ulong, ctypes.POINTER(ctypes.c_ulong))
    query.restype = ctypes.c_long
    handle = kernel32.OpenProcess(PROCESS_QUERY_LIMITED_INFORMATION, 0, pid)
    if not handle:
        return ""
    try:
        need = ctypes.c_ulong(0)
        query(handle, PROCESS_COMMAND_LINE, None, 0, ctypes.byref(need))
        if not need.value:
            return ""
        buf = ctypes.create_string_buffer(need.value)
        if query(handle, PROCESS_COMMAND_LINE, buf, need.value, ctypes.byref(need)) != 0:
            return ""
        # a UNICODE_STRING: its length in bytes, then after the padding a pointer to the text, which
        # the call writes into the same buffer
        length = int.from_bytes(buf.raw[:2], "little")
        text = ctypes.c_void_p.from_buffer(buf, ctypes.sizeof(ctypes.c_void_p)).value
        return ctypes.wstring_at(text, length // 2) if text and length else ""
    finally:
        kernel32.CloseHandle(handle)


def argv_of(command: str) -> list[str]:
    """A Windows command line split as the C runtime splits it: the program to the next quote or
    space with no escapes, then each word, a run of backslashes before a quote halved and an odd one
    keeping the quote, a quote outside a word's quotes opening them, and two quotes inside them one."""
    words, i, n = [], 0, len(command)
    while i < n and command[i] in " \t":
        i += 1
    if i < n and command[i] == '"':
        end = command.find('"', i + 1)
        end = n if end < 0 else end
        words.append(command[i + 1:end])
        i = end + 1
    else:
        end = i
        while end < n and command[end] not in " \t":
            end += 1
        words.append(command[i:end])
        i = end
    while True:
        while i < n and command[i] in " \t":
            i += 1
        if i >= n:
            return words
        word, quoted = [], False
        while i < n and (quoted or command[i] not in " \t"):
            c = command[i]
            if c == "\\":
                j = i
                while j < n and command[j] == "\\":
                    j += 1
                if j < n and command[j] == '"':
                    word.append("\\" * ((j - i) // 2))
                    if (j - i) % 2:
                        word.append('"')
                        j += 1
                    i = j
                else:
                    word.append("\\" * (j - i))
                    i = j
            elif c == '"':
                if quoted and command[i + 1:i + 2] == '"':
                    word.append('"')
                    i += 2
                else:
                    quoted = not quoted
                    i += 1
            else:
                word.append(c)
                i += 1
        words.append("".join(word))


def is_ours(command: str) -> bool:
    """A server of this app: Idiograph.exe, by its file name, run with --serve. A server run from
    the source is python.exe, another program to the app, so the two never stop each other."""
    words = argv_of(command)
    return PureWindowsPath(words[0]).name.lower() == EXECUTABLE.lower() and SERVE in words[1:]


def ours(pids) -> bool:
    return bool(pids) and all(is_ours(command_of(pid)) for pid in pids)


def choose_port(port: int, table: dict[int, set[int]]) -> tuple[int | None, bool]:
    """The port to use and whether this app's server already runs there, as on the Mac: a server of
    this app anywhere in the span first, else the first port nothing listens on, else None."""
    for p in sorted(table):
        if port <= p <= port + SPAN and ours(table[p]):
            return p, True
    # never another app of the family's port, so Idiograph on its own held port never takes Sift's
    for p in app_identity.fallback_ports(port, SPAN):
        if p not in table:
            return p, False
    return None, False


# ── starting and stopping ───────────────────────────────────────────────────────────────────────

# how a server is started, and how a process is ended, names the suite stands in for
POPEN = subprocess.Popen


def terminate(pid: int) -> None:
    """The process ended, Windows's TerminateProcess, for a server that did not quit when asked."""
    os.kill(pid, 15)


def ask_quit(port: int, timeout: float = 15) -> bool:
    """Quit asked of the server on `port`, as Settings asks it, so it waits for any write in hand and
    clears its pid file before it ends. Asked only of a server this app's own."""
    request = urllib.request.Request(URL.format(port=port) + "api/server", data=json.dumps({"op": "quit"}).encode("utf-8"),
                                     headers={"Content-Type": "application/json"}, method="POST")
    # straight to this machine, never through a proxy Windows's settings may name
    direct = urllib.request.build_opener(urllib.request.ProxyHandler({}))
    try:
        with direct.open(request, timeout=timeout) as reply:
            return reply.status == 200
    except (OSError, ValueError):
        return False


STARTF_FORCEOFFFEEDBACK = 0x80


def detached() -> dict:
    """What Popen needs for a server that has no console window and outlives this process, and,
    since it never shows a window, no busy pointer while it starts."""
    if os.name == "nt":
        info = subprocess.STARTUPINFO()
        info.dwFlags |= STARTF_FORCEOFFFEEDBACK
        return {"creationflags": DETACHED, "startupinfo": info}
    return {"start_new_session": True}


@contextlib.contextmanager
def one_launch():
    """One launch at a time, so a second double-click while the first is still starting the server
    waits for it, then finds that server and offers the dialog, and never starts a second one on the
    same port. A lock on a file beside the log, which Windows lets go when the process ends."""
    held = None
    if os.name == "nt":
        try:
            import msvcrt
            logs_dir().mkdir(parents=True, exist_ok=True)
            held = open(logs_dir() / "launch.lock", "a+b")
            held.seek(0)
            # LK_LOCK tries once a second for ten seconds before it gives up
            msvcrt.locking(held.fileno(), msvcrt.LK_LOCK, 1)
        except OSError:
            pass
    try:
        yield
    finally:
        if held is not None:
            held.close()


def server_command(port: int, extra: list[str]) -> list[str]:
    """This executable again as the server. Run from the source, the Python running it with this file."""
    if getattr(sys, "frozen", False):
        return [sys.executable, SERVE, "--port", str(port), *extra]
    return [sys.executable, str(Path(__file__).resolve()), SERVE, "--port", str(port), *extra]


def wait_closed(port: int, seconds: float = 5) -> bool:
    deadline = time.monotonic() + seconds
    while listening(port, port).get(port):
        if time.monotonic() >= deadline:
            return False
        time.sleep(0.2)
    return True


def stop_server(port: int, pidfile: Path) -> bool:
    """Quit asked first, then whatever of this app still listens five seconds later ended. A port
    held by another program is refused at once, and nothing is asked of it or sent to it."""
    for step in (ask_quit, terminate):
        held = listening(port, port).get(port, set())
        mine = [pid for pid in sorted(held) if is_ours(command_of(pid))]
        if held and len(mine) < len(held):
            return False
        if mine:
            if step is ask_quit:
                ask_quit(port)
            else:
                for pid in mine:
                    try:
                        terminate(pid)
                    except OSError:
                        pass
        if wait_closed(port):
            pidfile.unlink(missing_ok=True)
            return True
    return False


def start_server(port: int, extra: list[str], word: str, trace: Trace) -> bool:
    """Start the server with no window and wait up to ten seconds for it to listen. `word` is the
    outcome for the trace, started or restarted."""
    logs = logs_dir()
    log = logs / LOG
    pidfile = logs / f"idiograph-{port}.pid"
    try:
        logs.mkdir(parents=True, exist_ok=True)
        fh = open(log, "a", encoding="utf-8")
    except OSError:
        trace.line(port, f"not {word}, cannot write the log")
        alert(f"Idiograph cannot write its log at {log}.")
        return False
    stamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    fh.write(f"\n=== {stamp}, starting on port {port}\n")
    fh.flush()
    env = dict(os.environ, PYTHONUNBUFFERED="1", PYINSTALLER_RESET_ENVIRONMENT="1")
    with fh:
        child = POPEN(server_command(port, extra), stdin=subprocess.DEVNULL, stdout=fh, stderr=subprocess.STDOUT,
                      env=env, cwd=str(logs), close_fds=True, **detached())
    pidfile.write_text(f"{child.pid}\n", encoding="utf-8")
    deadline = time.monotonic() + 10
    while time.monotonic() < deadline:
        pids = sorted(listening(port, port).get(port, ()))
        if pids:
            pidfile.write_text(f"{pids[0]}\n", encoding="utf-8")
            trace.line(port, f"{word}, pid {pids[0]}")
            return True
        if child.poll() is not None:
            break
        time.sleep(0.25)
    if child.poll() is not None:
        pidfile.unlink(missing_ok=True)
    trace.line(port, f"not {word}, nothing listening after ten seconds")
    try:
        last = "".join(log.read_text(encoding="utf-8", errors="replace").splitlines(True)[-12:])
    except OSError:
        last = ""
    alert(f"Idiograph did not start on port {port}. The last lines of {log}:\n\n{last}")
    return False


def respawn(command: list[str], env: dict, key: str | None = None) -> None:
    """Restart from Settings in the Windows app, `server.SPAWN`: the server started anew as a
    process of its own, its output to the same log and its number in the pid file, and this one
    then ends as `server.main` returns, since Windows cannot run a program again in one process.
    The window's `key`, when it handed one over, goes on the new one's standard input, a pipe, never
    in its environment (agentlock, 2 November 2026, `server.take_window_key`)."""
    logs = logs_dir()
    logs.mkdir(parents=True, exist_ok=True)
    with open(logs / LOG, "a", encoding="utf-8") as fh:
        child = POPEN(command, stdin=subprocess.PIPE if key else subprocess.DEVNULL, stdout=fh,
                      stderr=subprocess.STDOUT, env=env, cwd=str(logs), close_fds=True, **detached())
    if key and getattr(child, "stdin", None) is not None:
        child.stdin.write((key + "\n").encode("ascii"))
        child.stdin.close()
    port = port_of(command)
    if port:
        (logs / f"idiograph-{port}.pid").write_text(f"{child.pid}\n", encoding="utf-8")


def port_of(command: list[str]) -> str | None:
    """The port a server command names, `--port N` or `--port=N`."""
    for i, arg in enumerate(command):
        if arg == "--port" and i + 1 < len(command):
            return command[i + 1]
        if arg.startswith("--port="):
            return arg.split("=", 1)[1]
    return None


def split_args(argv: list[str]) -> tuple[bool, str | None, list[str]]:
    """`--serve`, the port asked for, and every other argument, which goes to the server."""
    serve, port, extra = False, None, []
    i = 0
    while i < len(argv):
        arg = argv[i]
        if arg == SERVE:
            serve = True
        elif arg == "--port" and i + 1 < len(argv):
            port = argv[i + 1]
            i += 1
        elif arg.startswith("--port="):
            port = arg.split("=", 1)[1]
        else:
            extra.append(arg)
        i += 1
    return serve, port, extra


def text_streams(utf8: bool) -> None:
    """Standard output and error made usable: a windowed program may start with none, and they are
    then opened on the handles it was given, line by line. With `utf8`, a stream that is not a
    console writes UTF-8, as the log and an agent reading through a pipe both expect."""
    for name, fd in (("stdout", 1), ("stderr", 2)):
        try:
            stream = getattr(sys, name)
            if stream is None:
                setattr(sys, name, open(fd, "w", encoding="utf-8", errors="replace", buffering=1, closefd=False))
            elif utf8 and not stream.isatty():
                stream.reconfigure(encoding="utf-8", errors="replace", line_buffering=True)
            else:
                stream.reconfigure(line_buffering=True)
        except (OSError, ValueError, AttributeError):
            pass


def serve(port: str | None, extra: list[str]) -> int:
    """The server itself, in this process, with the arguments the launch handed on. It checks HTTPS
    against Windows's own certificates, as Python on Windows does, so it needs no bundle of its own."""
    text_streams(utf8=True)
    # the app's own entry by its name, Trace's trace_main and the others' server (app_identity.entry), so
    # the build follows the app's own code, then the family's server it runs
    import importlib
    importlib.import_module(app_identity.entry(APP))
    server = sys.modules["server"]
    sys.argv = [sys.argv[0], *(["--port", port] if port else []), *extra]
    server.RELAUNCH = relaunch_command(port, extra)
    if os.name == "nt":
        server.SPAWN = respawn
    server.main()
    return 0


def relaunch_command(port: str | None, extra: list[str]) -> list[str]:
    """This executable run again as the server, with the arguments this launch handed on, for a
    restart from the page. Run from the source, the Python running it with this file."""
    head = [sys.executable] if getattr(sys, "frozen", False) else [sys.executable, str(Path(__file__).resolve())]
    return [*head, SERVE, *(["--port", str(port)] if port else []), *extra]


def launch(port_text: str | None, extra: list[str], trace: Trace) -> int:
    port_text = port_text or os.environ.get("IDIOGRAPH_PORT") or str(PORT)
    extra = extra + os.environ.get("IDIOGRAPH_ARGS", "").split()
    if not port_text.isdigit() or not 0 < int(port_text) < 65536 - SPAN:
        trace.line(port_text, "not a port number")
        alert(f"That is not a port number: {port_text}")
        return 1
    first = int(port_text)
    port, running = choose_port(first, listening(first, first + SPAN))
    if port is None:
        trace.line(first, "every port in the span is held by another program")
        alert(f"Other programs are listening on ports {first} to {first + SPAN}, so Idiograph cannot start.")
        return 1
    if not running:
        if port != first:
            trace.line(first, f"another program is listening, so port {port}", final=False)
        return 0 if start_server(port, extra, "started", trace) else 1
    pidfile = logs_dir() / f"idiograph-{port}.pid"
    choice = ask()
    if choice == "Open":
        trace.line(port, "running, opened the browser")
        open_page(URL.format(port=port))
    elif choice == "Stop":
        if not stop_server(port, pidfile):
            trace.line(port, "running, did not stop")
            alert(f"Idiograph did not stop. Something still listens on port {port}.")
            return 1
        trace.line(port, "running, stopped")
        notify("Idiograph stopped.")
    elif choice == "Restart":
        if not stop_server(port, pidfile):
            trace.line(port, "running, did not stop, so not restarted")
            alert(f"Idiograph did not stop, so it did not restart. Something still listens on port {port}.")
            return 1
        return 0 if start_server(port, extra, "restarted", trace) else 1
    else:
        trace.line(port, "running, dialog dismissed")
    return 0


def stop_all(trace: Trace) -> int:
    """Every server of this app in the span stopped, with no dialog: Setup runs this before it puts
    a newer version over the old one, and the uninstaller before it removes the app, so no file of
    theirs is in use. A port another program holds is left alone. Always 0, so Setup carries on."""
    given = os.environ.get("IDIOGRAPH_PORT") or ""
    first = int(given) if given.isdigit() and 0 < int(given) < 65536 - SPAN else PORT
    table = listening(first, first + SPAN)
    for port in sorted(table):
        if ours(table[port]):
            done = stop_server(port, logs_dir() / f"idiograph-{port}.pid")
            trace.line(port, "stopped for Setup" if done else "did not stop for Setup")
    if not trace.done:
        trace.line(first, "nothing of Idiograph's running for Setup to stop")
    return 0


def command_line(args: list[str]) -> int:
    """The command line an AI agent works through (see `docs/agents.md`), the console twin with
    `cli` first: `Idiograph-console cli cases`. It runs here, in the foreground, and starts no server."""
    text_streams(utf8=True)
    import cli
    return cli.main(args)


def mcp_server(args: list[str]) -> int:
    """The MCP server, the console twin with `mcp` first, as Claude Desktop runs it once Settings has
    added it (see `mcp_server.py`). It speaks on standard input and output, in the foreground, and
    starts no server of the page's own."""
    if getattr(sys, "stderr", None) is None:
        try:
            sys.stderr = open(2, "w", encoding="utf-8", errors="replace", closefd=False)
        except OSError:
            pass
    import mcp_server as mcp
    return mcp.main(args)


def main(argv: list[str] | None = None) -> int:
    given = sys.argv[1:] if argv is None else argv
    if given[:1] == ["cli"]:
        return command_line(given[1:])
    if given[:1] == ["mcp"]:
        return mcp_server(given[1:])
    if given[:1] == [STOP]:
        return stop_all(Trace())
    serving, port, extra = split_args(given)
    if serving:
        return serve(port, extra)
    trace = Trace()
    trace.line(port or os.environ.get("IDIOGRAPH_PORT") or PORT, "launched", final=False)
    code = 1
    try:
        with one_launch():
            code = launch(port, extra, trace)
    finally:
        if not trace.done:
            trace.line(port or PORT, f"ended with no outcome, exit {code}")
    return code


if __name__ == "__main__":
    raise SystemExit(main())
