"""Area 348: the Linux server's build and its CI job (linux2, 8 November 2026, build 2 of the Linux plan).
`packaging/build_linux.py` freezes the server with PyInstaller on Linux and starts it once headless. Here, on any
machine and a faked platform: its names, its refusal off Linux and its dry run, the spec it writes, the launcher's
three ways in, the smoke (a stand-in server that answers, answers as another app, never answers, and never ends),
the environment the smoke runs in, Tauri's Linux resource file, and the workflow's `linux-server` job (read as text,
since the suite has no YAML parser): when it runs, on which machine, that it is allowed to fail and that no release
waits for it. What only a real Linux run proves (PyInstaller's freeze, glibc 2.35, the frozen server answering) is
not here. All made-up folders. Nothing here uses a participant's words."""
from __future__ import annotations

import contextlib
import io
import json
import re
import sys
from pathlib import Path

from . import support
from .support import check

STUB = '''
import json, os, sys, threading
from http.server import BaseHTTPRequestHandler, HTTPServer
port, app, mode = int(sys.argv[1]), sys.argv[2], sys.argv[3]
if mode == "silent":
    import time
    time.sleep(60)
class H(BaseHTTPRequestHandler):
    def log_message(self, *a): pass
    def _send(self):
        body = json.dumps({"app": app, "pid": os.getpid()}).encode()
        self.send_response(200); self.send_header("Content-Length", str(len(body))); self.end_headers(); self.wfile.write(body)
    def do_GET(self): self._send()
    def do_POST(self):
        self.rfile.read(int(self.headers.get("Content-Length") or 0))
        self._send()
        if mode == "obey":
            threading.Thread(target=self.server.shutdown, daemon=True).start()
srv = HTTPServer(("127.0.0.1", port), H)
srv.serve_forever()
'''


def job_block(workflow: str, job: str) -> str:
    """The text of one job under `jobs:`, from its two-space key to the next job's."""
    found = re.search(rf"^  {re.escape(job)}:\n(.*?)(?=^  [A-Za-z0-9_-]+:\n|\Z)", workflow, re.S | re.M)
    return found.group(1) if found else ""


def test_linux_server_build(scratch: Path):
    print("\n348. The Linux server's build and its CI job: names, dry run, spec, smoke against a stand-in, the workflow (linux2)")
    import importlib.util

    def load(name):
        spec = importlib.util.spec_from_file_location(f"idiograph_348_{name}", support.source("packaging") / f"{name}.py")
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        return mod

    build_linux = load("build_linux")
    linux_launcher = load("linux_launcher")

    root = scratch / "linux_server"
    root.mkdir(parents=True, exist_ok=True)

    check("348: the frozen folder and its executable are the app's own name",
          [build_linux.name_of(a) for a in ("idiograph", "sift", "trace")] == ["Idiograph", "Sift", "Trace"])

    # the build refuses off Linux, and its dry run says every step on any machine
    real = sys.platform
    try:
        sys.platform = "darwin"
        try:
            build_linux.main(["--out", str(root / "refused")])
            refused = "built"
        except SystemExit as exc:
            refused = str(exc)
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            code = build_linux.main(["--dry-run", "--out", str(root / "dry")])
    finally:
        sys.platform = real
    said = out.getvalue()
    check("348: off Linux the build is refused and points at --dry-run", "frozen on Linux" in refused and "--dry-run" in refused, refused)
    check("348: the dry run answers 0 and says its four steps", code == 0 and all(f"\n{n}." in "\n" + said for n in "1234"), said[-300:])
    spec = (root / "dry" / "build" / "Idiograph-linux.spec").read_text(encoding="utf-8")
    check("348: the spec freezes the Linux launcher into one executable with a console, in one folder, named for the app",
          "linux_launcher.py" in spec and "name='Idiograph', console=True" in spec and spec.count("EXE(") == 1
          and "COLLECT(exe, a.binaries, a.datas, name='Idiograph'" in spec and "icon=" not in spec and "version=" not in spec, spec[-400:])
    check("348: the spec names the Mac launcher the launcher imports, so the freeze cannot leave it out",
          "'mac_launcher'" in spec and "'server'" in spec and "'cli'" in spec)
    with contextlib.redirect_stdout(io.StringIO()):
        build_linux.main(["--app", "sift", "--dry-run", "--out", str(root / "dry")])
    sift = (root / "dry" / "build" / "Sift-linux.spec").read_text(encoding="utf-8")
    check("348: Sift's spec is its own and carries no demo", "name='Sift', console=True" in sift and "'demo'" not in sift.split("datas=")[1].split("hiddenimports")[0])
    check("348: the build's pins are the Mac build's, PyInstaller among them", build_linux.PINS == build_linux.build_mac.PINS
          and any(p.startswith("pyinstaller==") for p in build_linux.PINS))

    # the launcher's three ways in
    calls = []
    base = linux_launcher.base
    real_fns = (base.command_line, base.mcp_server, base.serve)
    try:
        base.command_line = lambda a: calls.append(("cli", a)) or 0
        base.mcp_server = lambda a: calls.append(("mcp", a)) or 0
        base.serve = lambda port, extra: calls.append(("serve", port, extra)) or 0
        linux_launcher.main(["cli", "cases"])
        linux_launcher.main(["mcp", "--root", "/x"])
        linux_launcher.main(["--serve", "--port", "9000", "--no-browser"])
        linux_launcher.main([])
    finally:
        base.command_line, base.mcp_server, base.serve = real_fns
    check("348: the launcher hands cli, mcp and the server on, and a bare start serves too",
          calls == [("cli", ["cases"]), ("mcp", ["--root", "/x"]), ("serve", "9000", ["--no-browser"]), ("serve", None, [])], str(calls))

    # the smoke's command and environment
    cmd = build_linux.smoke_command(Path("/f/Idiograph"), 8123)
    check("348: the smoke starts the frozen server as the window will, headless", [str(c) for c in cmd]
          == [str(Path("/f/Idiograph") / "Idiograph"), "--serve", "--port", "8123", "--no-browser"], str(cmd))
    env = build_linux.smoke_environment(Path("/h"), {"PATH": "/bin", "DISPLAY": ":0", "WAYLAND_DISPLAY": "w", "BROWSER": "x",
                                                      "XDG_DATA_HOME": "/d", "HOME": "/real"})
    check("348: the smoke has a home of its own, no XDG folder of the machine's and no display",
          env["HOME"] == str(Path("/h")) and env["PATH"] == "/bin" and not any(k in env for k in ("DISPLAY", "WAYLAND_DISPLAY", "BROWSER", "XDG_DATA_HOME")), str(env))

    # the smoke against a stand-in server
    stub = root / "stub_server.py"
    stub.write_text(STUB, encoding="utf-8", newline="")

    def smoked(app, mode, **kw):
        port = build_linux.free_port()
        log = root / f"smoke-{mode}-{app}.log"
        try:
            with contextlib.redirect_stdout(io.StringIO()):
                build_linux.smoke([sys.executable, stub, port, app, mode], port, dict(__import__("os").environ), "idiograph", log=log, **kw)
            return "passed"
        except SystemExit as exc:
            return str(exc)

    got = smoked("idiograph", "obey", start_wait=20, quit_wait=10)
    check("348: a server that answers as the app and ends when asked passes the smoke", got == "passed", got)
    got = smoked("sift", "obey", start_wait=20, quit_wait=10)
    check("348: a server that answers as another app fails it", "answered as 'sift'" in got, got)
    got = smoked("idiograph", "silent", start_wait=1.5, quit_wait=1)
    check("348: a server that never answers fails it", "did not answer" in got, got)
    got = smoked("idiograph", "stay", start_wait=20, quit_wait=1.5)
    check("348: a server that takes the quit but does not end fails it, and is ended", "did not end" in got, got)

    # Tauri's Linux resource file puts the server where server_dir() looks
    conf = json.loads(support.source("packaging/tauri/src-tauri/tauri.linux.conf.json").read_text(encoding="utf-8"))
    win = json.loads(support.source("packaging/tauri/src-tauri/tauri.windows.conf.json").read_text(encoding="utf-8"))
    check("348: Tauri's Linux file carries the frozen server as server/, as Windows's does",
          conf["bundle"]["resources"] == win["bundle"]["resources"] == {"../../../build/tauri-server/": "server/"}, str(conf))
    main_rs = support.source("packaging/tauri/src-tauri/src/main.rs").read_text(encoding="utf-8")
    check("348: server_dir() asks for Tauri's resource folder on Linux", 'cfg!(target_os = "linux")' in main_rs.split("fn server_dir()")[1].split("fn ")[0]
          and "fn linux_server_candidates" in main_rs and "fn linux_finds_the_server_in_tauris_resource_folder" in main_rs)

    # the workflow's job
    workflow = support.source(".github/workflows/windows-installer.yml").read_text(encoding="utf-8")
    job = job_block(workflow, "linux-server")
    release = job_block(workflow, "release")
    check("348: the Linux job is on ubuntu-22.04, allowed to fail and time-limited", "runs-on: ubuntu-22.04" in job
          and "continue-on-error: true" in job and "timeout-minutes:" in job, job[:300])
    check("348, updated 9 November (linux57): it runs on a dispatch that asks for it alone, no longer on a tag, since "
          "the Linux window's job freezes the server and repeats the smoke, and on no pull request",
          "github.ref_type" not in job and "inputs.linux_server" in job and "pull_request" not in job.split("steps:")[0])
    check("348: the dispatch has its own input, off by default",
          re.search(r"linux_server:\n(?:        .*\n)*?        default: false", workflow) is not None)
    check("348: it builds the tagged app and runs the smoke", 'release.py --which "$BUILD_FOR"' in job
          and 'build_linux.py --app "$APP" --smoke' in job)
    check("348: no release waits for it", "linux-server" not in release.split("steps:")[0], release[:200])
