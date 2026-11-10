from __future__ import annotations

import json
import os
import re
import shutil
import sys
from pathlib import Path

import make_app

from . import support
from .support import TOOL, check, skip, suite_text


def test_distclone(scratch):
    print("\n141. A downloaded copy, 14 October: the run scripts, the command line, the bundle's launcher and the MCP "
          "entry find the app's folder and its .venv in the repo and in a copy alike, a copy's first run sets itself "
          "up or says plainly why not, the app starts with no config.json, and nothing ships this machine's settings")
    import socket
    import subprocess
    import time
    import urllib.request
    import mcp_server
    import server as server_mod

    flat = lambda text: " ".join(str(text).split())
    read = lambda path: Path(path).read_text(encoding="utf-8")
    real = lambda text: str(Path(str(text).strip()).resolve())
    shells = os.name != "nt" and Path("/bin/bash").exists()
    run_sh, run_command, run_bat = read(support.source("run.sh")), read(support.source("run.command")), read(support.source("run.bat"))
    wrapper, wrapper_bat = read(support.source("idiograph")), read(support.source("idiograph.bat"))
    build_src = read(support.source("packaging/build_mac.py"))
    # the suite's workflow, merged with the Windows installer's on 14 October (see 142)
    workflow_path = support.source(".github/workflows/windows-installer.yml")
    workflow = read(workflow_path) if workflow_path.exists() else ""
    pinned = re.search(r'"(openpyxl==[0-9.]+)"', build_src)
    pin = pinned.group(1) if pinned else "openpyxl, pinned nowhere"

    # ── A. two invented trees: a repo copy with the app two folders below its root, its .venv at the
    # root, and a downloaded copy, the app's folder alone under Downloads. Each venv's python is a stub,
    # a small shell script that runs no python: it says where it ran, with what and as which script
    base = scratch / "distclone"
    shutil.rmtree(base, ignore_errors=True)
    repo_root = base / "A Repo Copy"
    repo_tool = repo_root / "Tools" / "idiograph"
    copy_tool = base / "Downloads" / "idiograph-main"
    inside = ("bin", "python3")

    def stub(path: Path, version: str = "3.12", pip: int = 0, venv: bool = True, missing: bool = False) -> Path:
        """A stand-in for a python that never runs one. It answers the run scripts' two questions
        about its version with `version`, makes a venv of its own copies for `-m venv`, unless
        `venv` is False, whose pip ends with `pip`, and for anything else prints its folder, its
        arguments and the script that started it. `missing` answers as a program that is not
        there, as the Mac's python3 does before its developer tools are installed."""
        old = 0 if tuple(int(n) for n in version.split(".")) >= (3, 11) else 1
        made = ('mkdir -p "$3/bin" && cp "$0" "$3/bin/python3" && chmod +x "$3/bin/python3"; exit 0'
                if venv else "exit 1")
        body = ("#!/bin/sh\n# a stand-in for a python, written by the suite: it never runs one\nexit 127\n" if missing else
                "#!/bin/sh\n# a stand-in for a python, written by the suite: it never runs one\n"
                'case "$1" in\n'
                f'  -c) case "$2" in *print*) echo "{version}"; exit 0 ;; *) exit {old} ;; esac ;;\n'
                f'  -m) case "$2" in venv) {made} ;; pip) echo "pip ran"; exit {pip} ;; esac ;;\n'
                "esac\n"
                'echo "ran in $(pwd -P) with $* as ${IDIOGRAPH_START:-none}"\n')
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(body, encoding="utf-8")
        path.chmod(0o755)
        return path

    for tool in (repo_tool, copy_tool):
        tool.mkdir(parents=True)
        for name in ("run.sh", "run.command", "idiograph"):
            shutil.copyfile(TOOL / name, tool / name)
            (tool / name).chmod(0o755)
    stub(repo_root.joinpath(".venv", *inside))
    stub(copy_tool.joinpath(".venv", *inside))
    clean_env = {k: v for k, v in os.environ.items() if not k.startswith("IDIOGRAPH_")}

    def sh(*args, path: str | None = None, cwd: Path = base):
        env = dict(clean_env, PATH=path) if path is not None else clean_env
        done = subprocess.run(["/bin/bash", *[str(a) for a in args]], capture_output=True, text=True, encoding="utf-8", env=env,
                              cwd=str(cwd), timeout=60)
        return done.returncode, done.stdout + done.stderr

    def ran(out: str) -> tuple[str, str, str]:
        """The stub's line: the folder it ran in, its arguments and the script that started it."""
        m = re.search(r"^ran in (.*) with (.*) as (\S+)$", out, re.M)
        return (real(m.group(1)), m.group(2), m.group(3)) if m else ("", "", "")

    if shells:
        code, out = sh(repo_tool / "run.sh", "--port", "1")
        check("141: in the repo, run.sh runs the root's .venv on Tools/idiograph/server.py from the root, as it always has",
              code == 0 and ran(out) == (real(repo_root), "Tools/idiograph/server.py --port 1", "run.sh"), flat(out)[-200:])
        code, out = sh(repo_tool / "run.command")
        check("141: run.command hands over to run.sh, and the server is told it was run.command",
              code == 0 and ran(out) == (real(repo_root), "Tools/idiograph/server.py", "run.command"), flat(out)[-200:])
        code, out = sh(copy_tool / "run.sh", "--port", "1")
        check("141: in a downloaded copy, run.sh runs the .venv beside it on server.py from the app's folder",
              code == 0 and ran(out) == (real(copy_tool), "server.py --port 1", "run.sh"), flat(out)[-200:])
        stub(repo_tool.joinpath(".venv", *inside))
        code, out = sh(repo_tool / "run.command")
        check("141: a .venv beside the app comes first, before the one two folders up",
              code == 0 and ran(out) == (real(repo_tool), "server.py", "run.command"), flat(out)[-200:])
        shutil.rmtree(repo_tool / ".venv")
        code, out = sh(repo_tool / "idiograph", "cases")
        code2, out2 = sh(copy_tool / "idiograph", "cases", "--json")
        check("141: the command line runs the root's .venv in the repo and the one beside it in a copy, on cli.py by its full path",
              code == 0 and ran(out)[1] == f"{repo_tool / 'cli.py'} cases"
              and code2 == 0 and ran(out2)[1] == f"{copy_tool / 'cli.py'} cases --json", flat(out + out2)[-200:])

        # the bundle's launcher, its lines from the trace to the log run alone, in both trees
        script = make_app.LAUNCHER
        head = script.split("\nTRACE=", 1)[1].split("LOGDIR=", 1)[0]
        head = head.replace('"/tmp/idiograph-launch.log"', '"' + str(base / "launch trace.log") + '"', 1)
        probe = "#!/bin/bash\nTRACE=" + head + 'echo "$ROOT"\necho "$SERVER"\necho "$PY"\n'
        answers = {}
        for tool in (repo_tool, copy_tool):
            macos = tool / "Idiograph.app" / "Contents" / "MacOS"
            macos.mkdir(parents=True)
            (macos / "Idiograph").write_text(probe, encoding="utf-8")
            (macos / "Idiograph").chmod(0o755)
            answers[tool] = subprocess.run([str(macos / "Idiograph")], capture_output=True, text=True, encoding="utf-8", env=clean_env,
                                           timeout=30).stdout.splitlines()
        got_repo, got_copy = answers[repo_tool], answers[copy_tool]
        check("141: the bundle's launcher starts the server from the repo root on its .venv, and from a copy's own folder on the one beside it",
              got_repo[:2] == [real(repo_root), "Tools/idiograph/server.py"]
              and real(got_repo[2] if len(got_repo) > 2 else "") == real(repo_root.joinpath(".venv", *inside))
              and got_copy[:2] == [real(copy_tool), "server.py"]
              and real(got_copy[2] if len(got_copy) > 2 else "") == real(copy_tool.joinpath(".venv", *inside)),
              " | ".join(got_repo + got_copy))
    else:
        skip("141: the run scripts, the command line and the bundle's launcher in both trees", "no bash on this system")

    # ── B. the first run of a downloaded copy, its python a stub on a PATH of stubs. The scripts' own
    # list of places to look on a Mac is swapped for a place that is not there, so no real python is found
    places = ('for CANDIDATE in python3 python /Library/Frameworks/Python.framework/Versions/3.*/bin/python3 \\\n'
              '    /opt/homebrew/bin/python3 /usr/local/bin/python3; do')
    check("141: the first run looks for python3, then python, then a python.org install and Homebrew's",
          places in run_sh and "sys.version_info >= (3, 11)" in run_sh)
    fresh = base / "Setup" / "idiograph-main"
    stubs = base / "stub-bin"

    def fresh_copy():
        shutil.rmtree(fresh, ignore_errors=True)
        fresh.mkdir(parents=True)
        (fresh / "run.sh").write_text(run_sh.replace(places, 'for CANDIDATE in python3 python "$HERE/no-such-python"; do'),
                                      encoding="utf-8")
        shutil.copyfile(support.source("run.command"), fresh / "run.command")

    def pythons(python3: dict, python: dict | None = None):
        shutil.rmtree(stubs, ignore_errors=True)
        stub(stubs / "python3", **python3)
        stub(stubs / "python", **(python or {"missing": True}))
        return f"{stubs}{os.pathsep}/usr/bin{os.pathsep}/bin"

    left = lambda: sorted(p.name for p in fresh.iterdir() if p.name.startswith(".venv"))
    if shells:
        fresh_copy()
        code, out = sh(fresh / "run.sh", path=pythons({"missing": True}))
        check("141: with no python the first run says so in plain words, names python.org and makes nothing",
              code == 1 and "Idiograph needs Python 3.11 or later, and there is none on this computer." in out
              and "Install it from https://www.python.org/downloads/ and open Idiograph again." in out and left() == [],
              flat(out)[-200:])
        code, out = sh(fresh / "run.sh", path=pythons({"version": "3.9"}, {"version": "3.10"}))
        check("141: with one too old it names the version found and python.org, and makes nothing",
              code == 1 and "Idiograph needs Python 3.11 or later, and the one on this computer is 3.10." in out
              and "python.org" in out and left() == [], flat(out)[-200:])
        code, out = sh(fresh / "run.sh", path=pythons({"pip": 1}))
        check("141: an install that fails says so in one line and leaves no .venv and no half-made setup",
              code == 1 and "Setting up Idiograph, once. It takes a minute." in out
              and "Idiograph could not set itself up, so nothing was kept. Check the internet connection and open it again." in out
              and left() == [], flat(out)[-200:])
        code, out = sh(fresh / "run.sh", path=pythons({"venv": False}))
        check("141: so does a venv that cannot be made", code == 1 and "could not set itself up" in out and left() == [],
              flat(out)[-200:])
        # what a stopped setup and a broken folder leave, neither taken for a good .venv
        stub(fresh.joinpath(".venv-setup", *inside), version="3.9")
        (fresh / ".venv").mkdir()
        code, out = sh(fresh / "run.command", "--port", "2", path=pythons({"missing": True}, {"version": "3.13"}))
        check("141: python stands in for python3, the setup clears what a stopped one left, and the server starts on the new .venv",
              code == 0 and "Setting up Idiograph, once." in out and "pip ran" in out
              and ran(out) == (real(fresh), "server.py --port 2", "run.command")
              and left() == [".venv"] and fresh.joinpath(".venv", *inside).is_file(), flat(out)[-300:])
        code, out = sh(fresh / "run.command", path=pythons({"missing": True}))
        check("141: a second run starts at once, with no setup and no python looked for",
              code == 0 and "Setting up" not in out and ran(out) == (real(fresh), "server.py", "run.command"),
              flat(out)[-200:])
    else:
        skip("141: the first run's setup and its refusals", "no bash on this system")
    check("141: the setup is made as .venv-setup and takes the name .venv only once openpyxl is in it, at build_mac.py's pin",
          f'OPENPYXL="{pin}"' in run_sh and '"$FOUND" -m venv "$SETUP"' in run_sh
          and '-m pip install --disable-pip-version-check -q "$OPENPYXL"' in run_sh
          and 'rm -rf "$HERE/.venv" && mv "$SETUP" "$HERE/.venv"' in run_sh
          and run_command.rstrip().endswith('exec /bin/bash "$(dirname "$0")/run.sh" "$@"'))

    # ── C. Windows, read rather than run: run.bat and idiograph.bat
    code_lines = [ln for ln in run_bat.splitlines() if ln.strip() and not ln.lstrip().upper().startswith(("REM", "@ECHO"))]
    unquoted = [ln for ln in code_lines if re.search(r"[()]", re.sub(r'"[^"]*"', "", ln))]
    order = [run_bat.find(s) for s in ('if exist "%HERE%.venv\\Scripts\\python.exe" goto beside',
                                       'if exist "%HERE%..\\..\\.venv\\Scripts\\python.exe" goto repo', ":setup",
                                       '\npy -3 -c "import sys; sys.exit(0 if sys.version_info >= (3, 11) else 1)"',
                                       '\npython -c "import sys; sys.exit(0 if sys.version_info >= (3, 11) else 1)"', ":make")]
    check("141: run.bat looks beside itself, then two folders up, then sets up with py -3 first and python after, 3.11 or later",
          all(i >= 0 for i in order) and order == sorted(order), str(order))
    check("141, updated 18 October (180): run.bat sets up as .venv-setup, renames it only after pip, which installs "
          "et_xmlfile beside openpyxl, and a failure removes it and says so in one line",
          '%PY% -m venv "%HERE%.venv-setup" || goto failed' in run_bat
          and f'-m pip install --disable-pip-version-check -q "%OPENPYXL%" "%ET_XMLFILE%" "%CRYPTOGRAPHY%" || goto failed' in run_bat
          and f'set "OPENPYXL={pin}"' in run_bat and 'ren "%HERE%.venv-setup" .venv || goto failed' in run_bat
          and ':failed\nif exist "%HERE%.venv-setup" rmdir /s /q "%HERE%.venv-setup"' in run_bat
          and "Idiograph could not set itself up, so nothing was kept." in run_bat
          and 'set "IDIOGRAPH_START=run.bat"' in run_bat)
    check("141: run.bat is plain ASCII with no bracket outside quotes, so a folder name with one cannot break it",
          run_bat.isascii() and wrapper_bat.isascii() and not unquoted, " | ".join(unquoted[:3]))
    beside_bat = wrapper_bat.find('if exist "%HERE%.venv\\Scripts\\python.exe" set "PY=%HERE%.venv\\Scripts\\python.exe"')
    check("141: idiograph.bat and idiograph take the .venv beside them over the one two folders up, then any python",
          0 <= wrapper_bat.find('if exist "%HERE%..\\..\\.venv\\Scripts\\python.exe"') < beside_bat
          and '"%PY%" "%HERE%cli.py" %*' in wrapper_bat
          and 'PY="$HERE/.venv/bin/python3"\n[ -x "$PY" ] || PY="$HERE/../../.venv/bin/python3"\n[ -x "$PY" ] || PY="python3"'
          in wrapper)
    attributes = read(support.source(".gitattributes")) if support.source(".gitattributes").exists() else ""
    check("141: .gitattributes gives the batch files CRLF and the scripts LF, in a checkout and in GitHub's zip",
          all(line in attributes.splitlines() for line in ("*.bat text eol=crlf", "*.sh text eol=lf", "*.command text eol=lf",
                                                           "/idiograph text eol=lf",
                                                           "/Idiograph.app/Contents/MacOS/Idiograph text eol=lf")))

    # ── D. the MCP entry and where relative paths start, in both trees
    win_tool = base / "Windows Copy" / "idiograph-main"
    win_tool.joinpath(".venv", "Scripts").mkdir(parents=True)
    win_tool.joinpath(".venv", "Scripts", "python.exe").write_text("a stand-in, never run\n", encoding="utf-8")
    check("141: the MCP entry runs the .venv beside the app first, then the repo root's, by its own path, and Scripts on Windows",
          mcp_server.venv_python(copy_tool, "darwin") == copy_tool.joinpath(".venv", *inside)
          and mcp_server.venv_python(repo_tool, "darwin") == repo_root.joinpath(".venv", *inside)
          and mcp_server.venv_python(win_tool, "win32") == win_tool / ".venv" / "Scripts" / "python.exe"
          and mcp_server.venv_python(win_tool, "darwin") is None
          and (os.name == "nt" or mcp_server.server_command(frozen=False, here=copy_tool)
               == [str(copy_tool.joinpath(".venv", *inside)), str(copy_tool / "mcp_server.py")]))
    clone_tool = base / "Tools" / "idiograph"
    (clone_tool / ".git").mkdir(parents=True)
    set_up = base / "Elsewhere" / "Tools" / "idiograph"
    (set_up / ".venv").mkdir(parents=True)
    check("141: relative paths start at the repo root in the repo, and inside the copy for a copy, a clone or a set-up copy",
          server_mod.source_base(repo_tool) == repo_root and server_mod.source_base(copy_tool) == copy_tool
          and server_mod.source_base(clone_tool) == clone_tool and server_mod.source_base(set_up) == set_up
          and server_mod.app_paths(False)["base"] == server_mod.source_base(TOOL) == server_mod.REPO_ROOT)
    home = base / "home"
    win = server_mod.app_paths(True, home, "win32")
    check("141, 142: the frozen Windows app keeps its files in AppData, Roaming, Idiograph and its logs in AppData, Local, a Mac's as before",
          win["data"] == home / "AppData" / "Roaming" / "Idiograph" == win["config"].parent
          and win["logs"] == home / "AppData" / "Local" / "Idiograph" / "Logs" and win["base"] == win["data"]
          and server_mod.app_paths(True, home, "darwin")["data"] == home / "Library" / "Application Support" / "Idiograph")
    # an invented case folder with its second name, put together here so no such name sits in the source
    folder = "P4 - Tamsin" + "-" + "Holloway"
    check("141: a path on the screen is scrubbed at Windows's backslashes as at slashes, and a path typed in quotes is taken without them",
          server_mod.display_path(f"Study\\{folder}\\P4 Tamsin - EN & ES.xlsx")
          == "Study\\P4 - Tamsin\\P4 Tamsin - EN & ES.xlsx"
          and server_mod.display_path(f"Study/{folder}/x.xlsx") == "Study/P4 - Tamsin/x.xlsx"
          and server_mod.abs_path('"' + str(base) + '"') == base and server_mod.abs_path(" '" + str(base) + "' ") == base
          and server_mod.abs_path(str(base)) == base)

    # ── E. no settings of this machine shipped, and the app starting with none
    ignored = read(support.source(".gitignore")).splitlines()
    check("141: config.json, the first run's .venv and its setup folder are gitignored at the app's top",
          all(line in ignored for line in ("/config.json", "/.venv/", "/.venv-setup/")))
    source = suite_text()
    reads_own = re.findall(r'\(TOOL / "config\.json"\)\.read_\w+|open\(TOOL / "config\.json"|load_json\(TOOL / "config\.json"', source)
    check("141: no check reads the tool folder's own config.json, and the suite's settings file is a scratch one",
          not reads_own and server_mod.CONFIG_PATH != support.source("config.json")
          and str(server_mod.CONFIG_PATH).startswith(str(scratch)), f"{len(reads_own)} reads, {server_mod.CONFIG_PATH.name}")
    own = support.source("config.json")
    # its date and size, never its contents
    stamp = lambda: (own.stat().st_mtime_ns, own.stat().st_size) if own.exists() else None
    before = stamp()
    copy = base / "Fresh" / "idiograph-main"
    shutil.copytree(TOOL, copy, ignore=shutil.ignore_patterns(
        "config.json", "state.json", ".env", "__pycache__", "build", "dist", ".venv", ".venv-setup", "tests", ".github",
        "packaging", "feedback-worker", "Idiograph.app", "*.m4a", "_Archive", "*.lock"))
    with socket.socket() as probe:
        probe.bind(("127.0.0.1", 0))
        free = probe.getsockname()[1]
    child = subprocess.Popen([sys.executable, str(copy / "server.py"), "--port", str(free), "--no-browser"], cwd=str(copy),
                             stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                             env=support.faulty_env(dict(clean_env, PYTHONUNBUFFERED="1")))
    watch = support.ChildWatch(child, free)
    answer, said = None, ""
    try:
        until = time.monotonic() + 30
        while time.monotonic() < until and answer is None:
            try:
                with urllib.request.urlopen(f"http://127.0.0.1:{free}/api/cases", timeout=5) as reply:
                    answer = json.loads(reply.read().decode("utf-8"))
                watch.answered()
            except OSError:
                time.sleep(0.25)
        if answer is None:
            watch.ran_out("the 30 s loop ran out")
    finally:
        child.terminate()
        try:
            said = child.communicate(timeout=15)[0].decode("utf-8", "replace")
        except subprocess.TimeoutExpired:
            child.kill()
            said = child.communicate()[0].decode("utf-8", "replace")
    written = json.loads(read(copy / "config.json")) if (copy / "config.json").exists() else {}
    shipped = json.loads(json.dumps(server_mod.shipped_config()))
    demo = (answer or {}).get("demo") or {}
    started = (answer is not None and written == shipped and written.get("projects") == [] and "root" not in written
               and (answer or {}).get("projects") == [] and "No project folder chosen yet." in said)
    check("141: a copy with no config.json starts, writes the defaults with no project, and asks for a folder",
          started, flat(said)[-200:] if started else watch.says(said))
    check("141: and its paths start inside the copy, the demo's workbook at demo/Juno",
          Path(str(demo.get("path") or "")).as_posix() == "demo/Juno/Juno - EN & ES.xlsx", str(demo.get("path")))
    check("141: the tool folder's own config.json is as it was",
          stamp() == before)

    # ── F. the workflow: the suite on Windows on every pull request and before every installer, the
    # installer's own steps checked in 142, and on a Mac and on Linux on every pull request (21 October,
    # for the public copy). A push to main runs nothing since 23 October, so a release runs once
    jobs = workflow.split("\njobs:\n", 1)[1] if "\njobs:\n" in workflow else ""
    # the Windows job alone, the Mac app's own job after it since 17 October (the third Tauri build, 173)
    windows = jobs.split("\n  mac-app:\n", 1)[0].split("\n  release:\n", 1)[0]
    suite = windows.split("# the installer", 1)[0]
    after_mac = jobs.split("\n  macos:\n", 1)[1] if "\n  macos:\n" in jobs else ""
    mac, linux = after_mac.split("\n  linux:\n", 1) if "\n  linux:\n" in after_mac else (after_mac, "")
    check("141, 142, updated 23 October: the workflow runs the suite with Python 3.11 on Windows, a Mac and Linux on every pull request, and on Windows and a Mac by hand, never on a push to main or another branch",
          'on:\n  push:\n    tags: [' in workflow and "branches:" not in workflow and "\n  workflow_dispatch:\n" in workflow
          and "\n  pull_request:\n" in workflow
          and "runs-on: windows-latest" in windows and "if:" not in suite
          and "runs-on: macos-latest" in mac
          and "if: github.event_name == 'pull_request' || (github.event_name == 'workflow_dispatch' && inputs.macos)" in mac
          and "runs-on: ubuntu-latest" in linux and "if: github.event_name == 'pull_request'\n" in linux
          and suite.count('python-version: "3.11"') == 1 == mac.count('python-version: "3.11"') == linux.count('python-version: "3.11"')
          and windows.count("timeout-minutes:") == 1 == mac.count("timeout-minutes:") == linux.count("timeout-minutes:")
          and workflow.count("cache: pip") == 6 and "matrix" not in workflow and "secrets" not in workflow
          and workflow.count(f"python -m pip install --disable-pip-version-check {pin}") == 3
          and workflow.count("python tests/test_idiograph.py") == 3 and "git config --global core.autocrlf false" in suite
          and not support.source(".github/workflows/tests.yml").exists())
