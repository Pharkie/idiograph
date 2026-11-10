#!/usr/bin/env python3
"""The executable inside the Mac app, Idiograph.app as `build_mac.py` makes it.

It does what the repo's launcher script does (`LAUNCHER` in `make_app.py`), in Python, since the
app carries its own Python and has no repo beside it. A double-click with nothing on the port
starts the server in the background, and the server opens the browser itself. A double-click
while it runs offers Stop, Restart and Open, with Open the default. Either way this process then
ends, so the app leaves the Dock once the server is up, as the script does.

The server is this same executable run again with `--serve`, in a session of its own, its output
in `~/Library/Logs/Idiograph/idiograph.log` and its process number in `idiograph-<port>.pid`
beside it. Port 8765 first. When another program holds it, the next free port, and a server of
this app already listening on one of those ports is the one the dialog offers. Stop and Restart
only ever signal a process listening on that port, and only when it is this app's server.

    Idiograph [--port N] [--no-browser] [--root FOLDER] [--config FILE] [--verbose]
    Idiograph --serve [the same]       the server itself, in the foreground
    Idiograph cli <command>            the command line an AI agent works through, docs/agents.md
    Idiograph mcp [--project NAME | --root FOLDER]   the MCP server, the commands as tools for Claude Desktop

`IDIOGRAPH_PORT` and `IDIOGRAPH_ARGS` work as they do for the repo's launcher, for a trial run that
never touches the port in daily use. Every launch leaves a line with its date and its outcome in
`/tmp/idiograph-launch.log`, as the script does.
"""
from __future__ import annotations

import os
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

# run from the source the app's modules are a folder up, and frozen they are in the bundle
if not getattr(sys, "frozen", False):
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import boot  # noqa: E402  the family's folders on the path (boot.py), the bundle's own frozen

boot.setup()
import app_folders  # noqa: E402  the folders the app writes in, the Windows app's too
import app_identity  # noqa: E402  which of the three apps, by this launcher's own name

# the app this launcher is, by its own name, Idiograph's unless it is Sift's or Trace's, and its port,
# 8765 for Idiograph (see app_identity)
APP = app_identity.chosen([])
PORT = app_identity.APPS[APP]["port"]
# the ports tried after the first when another program holds it
SPAN = 20
SERVE = "--serve"
# the bundle's own executable, which every server of this app runs as
EXECUTABLE = f"/Contents/MacOS/{app_identity.APPS[APP]['name']}"
TRACE = app_folders.folders("darwin", app=APP)["trace"]
QUESTION = f"{app_identity.APPS[APP]['name']} is running."
CHOICES = ("Stop", "Restart", "Open")
URL = "http://127.0.0.1:{port}/"


def logs_dir(home: Path | None = None) -> Path:
    """`~/Library/Logs/Idiograph`, where the log and the pid file live, as for the repo's launcher,
    from `app_folders`, which decides it for the Windows app as well."""
    return app_folders.folders("darwin", home, app=APP)["logs"]


class Trace:
    """The two lines a launch leaves in /tmp: its date first, then its outcome or the reason it
    stopped. Dates and port numbers only, never a path."""

    def __init__(self, path: Path = TRACE):
        self.path = path
        self.done = False

    def line(self, port, words: str, final: bool = True) -> None:
        self.done = self.done or final
        stamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        try:
            with open(self.path, "a", encoding="utf-8") as fh:
                fh.write(f"{stamp} port {port}: {words}\n")
        except OSError:
            pass


def osascript(lines, *args: str, timeout: float = 600) -> str:
    """Run AppleScript, one `-e` a line, with `args` as `argv`. Answers what it printed, or ""."""
    cmd = ["osascript"]
    for line in lines:
        cmd += ["-e", line]
    try:
        run = subprocess.run(cmd + list(args), capture_output=True, text=True, encoding="utf-8", timeout=timeout)
    except (OSError, subprocess.TimeoutExpired):
        return ""
    return run.stdout.strip() if run.returncode == 0 else ""


def echo(message: str) -> None:
    """A line on stderr for a run from a terminal. Launched from the Finder there may be none."""
    if sys.stderr is not None:
        print(f"Idiograph: {message}", file=sys.stderr)


def alert(message: str) -> None:
    """A dialog with one OK button, echoed to stderr for a run from a terminal."""
    echo(message)
    osascript(("on run argv", "activate",
               'display dialog (item 1 of argv) with title "Idiograph" buttons {"OK"} '
               'default button "OK" with icon caution', "end run"), message)


def notify(message: str) -> None:
    echo(message)
    osascript(("on run argv", 'display notification (item 1 of argv) with title "Idiograph"', "end run"),
              message)


ASK = ("on run argv", "activate",
       f'set question to "{QUESTION}"',
       "set choices to {" + ", ".join(f'"{c}"' for c in CHOICES) + "}",
       "try",
       'set reply to display dialog question with title "Idiograph" buttons choices default button "Open" '
       "with icon ((POSIX file (item 1 of argv)) as alias)",
       "on error number n",
       'if n is -128 then return ""',
       'set reply to display dialog question with title "Idiograph" buttons choices default button "Open" '
       "with icon note",
       "end try",
       "return button returned of reply",
       "end run")


def icon() -> str:
    """The app's icon in its bundle, for the running dialog. Run from the source it is not there,
    and the dialog shows the plain note icon."""
    return str(Path(sys.executable).resolve().parent.parent / "Resources" / "Idiograph.icns")


def ask() -> str:
    """The running dialog: the button pressed, or "" when it is dismissed."""
    return osascript(ASK, icon())


def listening(first: int, last: int) -> dict[int, set[int]]:
    """The processes listening on each port from `first` to `last`, by port, from one lsof call."""
    try:
        out = subprocess.run(["lsof", "-nP", f"-iTCP:{first}-{last}", "-sTCP:LISTEN", "-Fpn"],
                             capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=15).stdout
    except (OSError, subprocess.TimeoutExpired):
        return {}
    table: dict[int, set[int]] = {}
    pid = None
    for line in out.splitlines():
        if line.startswith("p") and line[1:].isdigit():
            pid = int(line[1:])
        elif line.startswith("n") and pid is not None:
            tail = line.rsplit(":", 1)[-1]
            if tail.isdigit() and first <= int(tail) <= last:
                table.setdefault(int(tail), set()).add(pid)
    return table


def command_of(pid: int) -> str:
    try:
        return subprocess.run(["ps", "-p", str(pid), "-o", "command="], capture_output=True, text=True,
                              encoding="utf-8", errors="replace", timeout=10).stdout.strip()
    except (OSError, subprocess.TimeoutExpired):
        return ""


def is_ours(command: str) -> bool:
    """A server of this app: the bundle's executable run with --serve. A server run from the repo
    is another program to the app, so the two never stop each other."""
    head = command.split(f" {SERVE}", 1)[0]
    return f" {SERVE}" in f"{command} " and head.endswith(EXECUTABLE)


def ours(pids) -> bool:
    return bool(pids) and all(is_ours(command_of(pid)) for pid in pids)


def choose_port(port: int, table: dict[int, set[int]]) -> tuple[int | None, bool]:
    """The port to use and whether this app's server already runs there.

    A server of this app anywhere in the span is the one to offer, so a second double-click finds
    it wherever the first one put it. Else the first port nothing listens on. None when every port
    in the span is held by another program.
    """
    for p in sorted(table):
        if port <= p <= port + SPAN and ours(table[p]):
            return p, True
    # never another app of the family's port, so Idiograph on its own held port never takes Sift's
    for p in app_identity.fallback_ports(port, SPAN):
        if p not in table:
            return p, False
    return None, False


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
    """TERM, and KILL only for whatever still listens five seconds later. Every workbook save is a
    temporary file renamed into place, so neither can leave half a workbook."""
    for sig in (15, 9):
        for pid in listening(port, port).get(port, ()):
            if is_ours(command_of(pid)):
                try:
                    os.kill(pid, sig)
                except OSError:
                    pass
        if wait_closed(port):
            pidfile.unlink(missing_ok=True)
            return True
    return False


def start_server(port: int, extra: list[str], word: str, trace: Trace) -> bool:
    """Start the server in the background and wait up to ten seconds for it to listen. `word` is
    the outcome for the trace, started or restarted."""
    logs = logs_dir()
    log = logs / "idiograph.log"
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
        child = subprocess.Popen(server_command(port, extra), stdin=subprocess.DEVNULL, stdout=fh,
                                 stderr=subprocess.STDOUT, start_new_session=True, env=env)
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


def split_args(argv: list[str]) -> tuple[bool, str | None, list[str]]:
    """`--serve`, the port asked for, and every other argument, which goes to the server. The
    `-psn_` argument an older Finder adds is dropped."""
    serve, port, extra = False, None, []
    rest = [a for a in argv if not a.startswith("-psn_")]
    i = 0
    while i < len(rest):
        arg = rest[i]
        if arg == SERVE:
            serve = True
        elif arg == "--port" and i + 1 < len(rest):
            port = rest[i + 1]
            i += 1
        elif arg.startswith("--port="):
            port = arg.split("=", 1)[1]
        else:
            extra.append(arg)
        i += 1
    return serve, port, extra


def serve(port: str | None, extra: list[str]) -> int:
    """The server itself, in this process, with the arguments the launch handed on."""
    if not getattr(sys, "frozen", False):
        sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
    else:
        # the bundle's Python knows none of the Mac's certificates, so HTTPS, the AI calls and Send
        # feedback, is checked against the ones certifi carries in the bundle
        try:
            import certifi
            os.environ.setdefault("SSL_CERT_FILE", certifi.where())
        except ImportError:
            pass
    # the log takes the server's output line by line, as PYTHONUNBUFFERED gives the repo's server,
    # which a frozen Python does not read, so a Stop never loses the last lines
    for name, fd in (("stdout", 1), ("stderr", 2)):
        try:
            stream = getattr(sys, name)
            if stream is None:
                setattr(sys, name, open(fd, "w", encoding="utf-8", buffering=1, closefd=False))
            else:
                stream.reconfigure(line_buffering=True)
        except (OSError, ValueError, AttributeError):
            pass
    # the app's own entry by its name, Trace's trace_main and the others' server (app_identity.entry), so
    # the build follows the app's own code, then the family's server it runs
    import importlib
    importlib.import_module(app_identity.entry(APP))
    server = sys.modules["server"]
    sys.argv = [sys.argv[0], *(["--port", port] if port else []), *extra]
    # Restart in Settings runs this same server again in this process, so the pid file still names it
    server.RELAUNCH = relaunch_command(port, extra)
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
        subprocess.run(["open", URL.format(port=port)], check=False)
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


def command_line(args: list[str]) -> int:
    """The command line an AI agent works through (see `docs/agents.md`), this same executable with
    `cli` first: `Idiograph cli cases`. It runs here, in the foreground, and starts no server."""
    if not getattr(sys, "frozen", False):
        sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
    # a windowed app's Python may start with no streams, and the answer goes to the terminal
    for name, fd in (("stdout", 1), ("stderr", 2)):
        if getattr(sys, name) is None:
            try:
                setattr(sys, name, open(fd, "w", encoding="utf-8", closefd=False))
            except OSError:
                pass
    import cli
    return cli.main(args)


def mcp_server(args: list[str]) -> int:
    """The MCP server, this same executable with `mcp` first, as Claude Desktop runs it once Settings
    has added it (see `mcp_server.py`). It speaks on standard input and output, in the foreground,
    and starts no server of the page's own."""
    if not getattr(sys, "frozen", False):
        sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
    else:
        try:
            import certifi
            os.environ.setdefault("SSL_CERT_FILE", certifi.where())
        except ImportError:
            pass
    if getattr(sys, "stderr", None) is None:
        try:
            sys.stderr = open(2, "w", encoding="utf-8", closefd=False)
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
    serving, port, extra = split_args(given)
    if serving:
        return serve(port, extra)
    # launched from the Finder the path is short, and these are where lsof, ps and osascript live
    os.environ["PATH"] = "/usr/bin:/bin:/usr/sbin:/sbin:" + os.environ.get("PATH", "")
    trace = Trace()
    trace.line(port or os.environ.get("IDIOGRAPH_PORT") or PORT, "launched", final=False)
    code = 1
    try:
        code = launch(port, extra, trace)
    finally:
        if not trace.done:
            trace.line(port or PORT, f"ended with no outcome, exit {code}")
    return code


if __name__ == "__main__":
    raise SystemExit(main())
