from __future__ import annotations

import ast
import contextlib
import inspect
import io
import json
import os
import sys
from pathlib import Path

from . import support
from .support import TOOL, check, slashed, suite_files

# each file scanned once for both scans, its finds kept with whether a newline alone is their reason (sped up
# 18 October, testreview3, and 2 November, testspeed: once a file, not once a scan)
_SCANNED: dict[str, list[tuple[int, str, bool]]] = {}


def leaning(path: Path, newline: bool = False) -> list[tuple[int, str]]:
    """Each call in a Python file that leans on the system's code page, by line: a file opened, read
    or written as text with no encoding named, a binary mode aside, or a program's output read as
    text with none. With `newline`, each file written as text with no newline named as well, since
    Windows then turns every line end into two characters. A call handing on `**kw` is its caller's
    to decide (14 October)."""
    key = str(Path(path).resolve())
    if key not in _SCANNED:
        _SCANNED[key] = _scan(Path(path))
    return [(n, why) for n, why, newline_only in _SCANNED[key] if newline or not newline_only]


def _scan(path: Path) -> list[tuple[int, str, bool]]:
    """Every find of `leaning` in one file, each with whether it is a write with no newline alone."""
    programs = ("run", "Popen", "check_output", "call", "check_call")
    value = lambda node: node.value if isinstance(node, ast.Constant) else None
    out = []
    for node in ast.walk(ast.parse(path.read_text(encoding="utf-8"))):
        if not isinstance(node, ast.Call):
            continue
        f = node.func
        name = f.id if isinstance(f, ast.Name) else (f.attr if isinstance(f, ast.Attribute) else "")
        owner = f.value.id if isinstance(f, ast.Attribute) and isinstance(f.value, ast.Name) else ""
        given = {k.arg: k.value for k in node.keywords}
        if None in given:
            continue
        named = "encoding" in given
        mode, why = None, None
        if name == "open" and owner not in ("os", "webbrowser", "zipfile", "tarfile"):
            at = 1 if isinstance(f, ast.Name) else 0
            held = node.args[at] if len(node.args) > at else given.get("mode")
            mode = "r" if held is None else value(held)
            if isinstance(mode, str) and "b" not in mode and not named and len(node.args) < at + 3:
                why = "opened as text"
        elif name == "fdopen" and owner == "os":
            held = node.args[1] if len(node.args) > 1 else given.get("mode")
            mode = "r" if held is None else value(held)
            if isinstance(mode, str) and "b" not in mode and not named:
                why = "opened as text"
        elif name == "read_text" and isinstance(f, ast.Attribute) and not node.args and not named:
            why = "read as text"
        elif name == "write_text" and isinstance(f, ast.Attribute):
            mode = "w"
            if len(node.args) < 2 and not named:
                why = "written as text"
        elif name in programs and value(given.get("text", given.get("universal_newlines"))) is True and not named:
            why = "a program's output read as text"
        if why:
            out.append((node.lineno, why, False))
        elif isinstance(mode, str) and "b" not in mode and any(c in mode for c in "wax+") and "newline" not in given:
            out.append((node.lineno, "written with no newline", True))
    return out


def test_windows_text(scratch):
    print("\n144. Windows, 14 October: nothing read or written in the system's code page, every file the app writes "
          "the same on any system, a path on the screen with either system's separators, Restart starting the "
          "server anew where a program cannot run again in one process, and the suite's own readings")
    import ntpath
    import posixpath
    import subprocess
    import app_folders
    import cli
    import make_demo
    import mcp_server
    import server as server_mod

    app_files = support.code_files("*.py") + sorted(support.source("packaging").glob("*.py"))

    # ── A. the scan, tried first on a made-up file holding each kind of call
    sample = scratch / "leaning-sample.py"
    sample.write_text(
        "import subprocess\nfrom pathlib import Path\n"
        "a = open('notes.txt')\n"
        "b = open('notes.bin', 'rb')\n"
        "c = Path('notes.txt').read_text()\n"
        "Path('notes.txt').write_text('kept', encoding='utf-8')\n"
        "subprocess.run(['node', 'check.js'], capture_output=True, text=True)\n"
        "subprocess.run(['node', 'check.js'], capture_output=True)\n"
        "open('notes.txt', 'w', encoding='utf-8', newline='\\n')\n"
        "subprocess.run(['node', 'check.js'], capture_output=True, text=True, encoding='utf-8')\n",
        encoding="utf-8")
    found, found_nl = leaning(sample), leaning(sample, newline=True)
    check("144: the scan finds a text open, a read and a program's output read with no encoding, a write with no newline, "
          "and passes a binary open, a named encoding and bytes",
          [n for n, _ in found] == [3, 5, 7] and sorted(n for n, _ in found_nl) == [3, 5, 6, 7], f"{found} {found_nl}")

    # ── B. the app's source, and the suite's
    offenders = [f"{p.name}:{n} {why}" for p in app_files for n, why in leaning(p)]
    check("144: every file the app's Python opens, reads or writes as text names its encoding, a binary mode aside, and "
          "so does every program's output it reads",
          not offenders and len(app_files) > 30, str(offenders[:6]))
    unsaid = [f"{p.name}:{n} {why}" for p in support.code_files("*.py") for n, why in leaning(p, newline=True)]
    check("144: every file the app writes names its newline too, so a case's files come out byte for byte the same "
          "on Windows as on a Mac",
          not unsaid, str(unsaid[:6]))
    suite_said = [f"{p.name}:{n} {why}" for p in suite_files() for n, why in leaning(p)]
    check("144: the suite reads node's output, every other program's and every file as UTF-8, never in the system's "
          "code page",
          not suite_said, str(suite_said[:6]))

    # ── C. a run under a code page that is not UTF-8: Windows's own there, a Latin one here where the system has it
    words = "Hold \u2325 \u2192 Mornings \u00b7 first \u2026 Revue \u00c9mue \u2013 done"
    # every word of the child's program in ASCII escapes, so nothing of it rides on how the code page reads
    # its arguments
    snippet = ("import json, locale, sys\n"
               f"sys.path.insert(0, {ascii(str(TOOL))})\n"
               "import boot\nboot.setup()\nimport app_folders, server\n"
               "from pathlib import Path\n"
               f"words, at = {ascii(words)}, Path({ascii(str(scratch / 'locale-144.json'))})\n"
               "server.save_json(at, {'w': words})\n"
               "back = server.load_json(at, {}).get('w') == words\n"
               "app_folders.utf8_streams()\n"
               "print(json.dumps({'code page': locale.getencoding(), 'back': back, 'lf': b'\\r' not in at.read_bytes()}))\n"
               "print(words)\n")
    env = {k: v for k, v in os.environ.items() if k not in ("PYTHONIOENCODING", "PYTHONUTF8", "LC_ALL", "LC_CTYPE", "LANG")}
    if os.name != "nt":
        env.update(LC_ALL="en_US.ISO8859-1", LANG="en_US.ISO8859-1")
    ran = subprocess.run([sys.executable, "-c", snippet], capture_output=True, env=env, timeout=60)
    lines = ran.stdout.decode("utf-8", errors="replace").splitlines()
    facts = json.loads(lines[0]) if lines and lines[0].startswith("{") else {}
    check("144: under a code page that is not UTF-8 the app's JSON reads back what it wrote, its lines ending in LF, "
          "and its output to a pipe is UTF-8",
          ran.returncode == 0 and facts.get("back") is True and facts.get("lf") is True and lines[1:] == [words],
          f"{facts} {ran.stderr.decode('utf-8', errors='replace')[-200:]}")

    class Stream:
        def __init__(self, tty):
            self.tty, self.asked = tty, None

        def isatty(self):
            return self.tty

        def reconfigure(self, **how):
            self.asked = how

    pipe, console = Stream(False), Stream(True)
    held = sys.stdout, sys.stderr
    sys.stdout, sys.stderr = pipe, console
    try:
        app_folders.utf8_streams()
    finally:
        sys.stdout, sys.stderr = held
    import cli
    cli_main = inspect.getsource(cli.script)
    check("144: a pipe or a file gets UTF-8 and a console keeps its own, in the command line, the MCP server and the server",
          pipe.asked == {"encoding": "utf-8", "errors": "replace"} and console.asked is None
          and "app_folders.utf8_streams()" in cli_main and "app_folders.utf8_streams()" in inspect.getsource(mcp_server.main)
          and "app_folders.utf8_streams()" in inspect.getsource(server_mod.main))

    # ── D. a path on the screen, in either system's separators
    folder = "P3 - Wren" + "-" + "Example"
    win = ntpath.join("C:\\Users\\Kim Example", "Studies", folder, "Working", "Wren - All Experiential Statements.csv")
    mac = posixpath.join("/Users/kim", "Studies", folder, "Working", "Wren - All Experiential Statements.csv")
    check("144: a path on the screen shows the case folder by its pseudonym at Windows's backslashes as at a Mac's "
          "slashes, each separator as the system wrote it",
          server_mod.display_path(win) == "C:\\Users\\Kim Example\\Studies\\P3 - Wren\\Working\\Wren - All Experiential Statements.csv"
          and server_mod.display_path(mac) == "/Users/kim/Studies/P3 - Wren/Working/Wren - All Experiential Statements.csv"
          and slashed(server_mod.display_path(win)).endswith("/P3 - Wren/Working/Wren - All Experiential Statements.csv"))

    # ── E. Restart where a program cannot run again in one process
    kept = (server_mod.POPEN, server_mod.SPAWN, server_mod.EXEC, server_mod.RELAUNCH, server_mod.FROZEN, server_mod.ARGV,
            dict(server_mod.PATHS), os.fstat)
    popens, execs = [], []
    real_fstat = os.fstat

    def no_stdin(fd):
        if fd == 0:
            raise OSError(9, "Bad file descriptor")
        return real_fstat(fd)

    try:
        server_mod.POPEN = lambda command, **how: popens.append((list(command), how))
        server_mod.EXEC = lambda path, argv, env: execs.append(argv)
        server_mod.SPAWN = server_mod.spawn_again
        server_mod.RELAUNCH, server_mod.FROZEN = None, False
        server_mod.ARGV = [str(support.source("server.py")), "--port", "8796", "--no-browser"]
        logs = scratch / "windows-text-logs"
        logs.mkdir(exist_ok=True)
        server_mod.PATHS["logs"] = logs
        pid_file = logs / "idiograph-8796.pid"
        pid_file.write_text(f"{os.getpid()}\n", encoding="utf-8")
        said = io.StringIO()
        with contextlib.redirect_stdout(said):
            server_mod.finish("restart", 8796)
        blocked = server_mod.restart_blocked("win32")
        os.fstat = no_stdin
        try:
            server_mod.spawn_again(["idiograph", "--serve"], {"X": "1"})
        finally:
            os.fstat = real_fstat
    finally:
        (server_mod.POPEN, server_mod.SPAWN, server_mod.EXEC, server_mod.RELAUNCH, server_mod.FROZEN,
         server_mod.ARGV) = kept[:6]
        server_mod.PATHS.clear()
        server_mod.PATHS.update(kept[6])
        os.fstat = kept[7]
    first = popens[0] if popens else ([], {})
    check("144: on Windows a restart starts the same program anew as a process of its own, on this one's window and "
          "output, and this one then ends with no exec, so Restart no longer refuses there",
          first[0] == [sys.executable, str(support.source("server.py")), "--port", "8796", "--no-browser"]
          and first[1].get("env", {}).get(server_mod.RESTARTED) == "1" and first[1].get("close_fds") is True
          and all(first[1].get(n) in (fd, subprocess.DEVNULL) for n, fd in (("stdin", 0), ("stdout", 1), ("stderr", 2)))
          and not execs and "Restarting." in said.getvalue() and "Idiograph is closed." not in said.getvalue()
          and blocked is None,
          # the command's last words and the streams alone, never the environment, which may hold a key
          str([first[0][2:], {n: first[1].get(n) for n in ("stdin", "stdout", "stderr", "close_fds")}]))
    check("144: a stream the server lacks, as a program with no window lacks one, is none for the new one too",
          len(popens) == 2 and popens[1][1].get("stdin") == subprocess.DEVNULL and popens[1][1].get("stdout") == 1)
    check("144: Windows is given its own way by default and a Mac and Linux keep exec, the Windows app's launcher still "
          "setting its own",
          (kept[1] is server_mod.spawn_again) == (sys.platform == "win32")
          and "server.SPAWN = respawn" in support.source("packaging/windows_launcher.py").read_text(encoding="utf-8"))

    # ── F. the rest that a Mac can pin: the demo's zip, notes.sh and the workflow
    notes_sh = support.source("feedback-worker/notes.sh").read_text(encoding="utf-8")
    workflow = support.source(".github/workflows/windows-installer.yml").read_text(encoding="utf-8")
    check("144: the demo's rebuilt zip says every part was made on Unix, so its bytes are the same whichever system builds it",
          "info.create_system = 3" in inspect.getsource(make_demo.pin))
    check("144: notes.sh takes a path that starts at a drive letter or a backslash as whole, as Git's sh on Windows gives one",
          "/*|[A-Za-z]:*|\\\\*) ;;" in notes_sh)
    check("144: the workflow leaves Windows's code page as a tester's machine has it, no PYTHONUTF8 to hide a reading in it",
          "PYTHONUTF8" not in workflow)
