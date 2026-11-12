#!/usr/bin/env python3
"""Build the Linux app's frozen server, the folder the window (Tauri's, a later build) carries as a resource
(linux2, 8 November 2026, build 2 of the Linux plan, `Idiograph_linux_plan_08Nov26.md`).

    python3 packaging/build_linux.py                    from the app's folder, into build/ beside it
    python3 packaging/build_linux.py --out <folder>     into <folder>/build
    python3 packaging/build_linux.py --smoke            after the build, start the frozen server headless
    python3 packaging/build_linux.py --window           then the window around it: dist/<Name>-x86_64.AppImage and dist/<Name>-amd64.deb
    python3 packaging/build_linux.py --window --test-app    a check's build, "<Name> Test", with no file type of its own
    python3 packaging/build_linux.py --dry-run          on any machine: the files written, every step said, none run
    python3 packaging/build_linux.py --list --app sift  on any machine: what Sift's build would ship

The counterpart of `build_windows.py`, taking `build_mac.py`'s pins, modules, data files and stage, so the
three systems carry the same code and the same demo. GitHub's `ubuntu-22.04` machine runs it from the
`linux-server` job of `.github/workflows/windows-installer.yml` (22.04's glibc 2.35 is the oldest the frozen
Python then runs on, as the plan asks). The steps:

1. A build venv, `build/venv`, with build_mac's PINS, made with the Python running this script or the one
   `--python` names, 3.11 or later. PyInstaller's own prebuilt Linux bootloader, since the Windows build's
   reason for compiling one (Defender's guess about a shared bootloader) does not apply.
2. The stage, `build/stage`: for Idiograph the demo's three cases through build_mac's `stage_cases`, and their
   recordings through its `stage_recordings`, each where one is committed for its transcript as it stands, with
   their licence beside it, and `config.json` from `server.shipped_config(app)`.
3. PyInstaller, one folder, from `packaging/linux_launcher.py`: a single executable named for the app
   (`Idiograph`, `Sift`, `Trace`), by whose name the frozen server knows which app it is, which is also
   what `app.rs`'s `server_exe` looks for on Linux. A run of its `cli --help` proves it finds every module.
   Then the typesetter, `idiograph-typeset`, built by cargo for this machine and put beside it, run on a one-line
   page with the fonts the folder carries (typst1, 9 November 2026, `packaging/typeset_helper.py`).
4. `--smoke` (a step of its own): the frozen server started with no display, in a home folder of its own,
   asked for `/api/server`, then asked to quit, and the run fails unless it answers as the app and ends.

The frozen folder is `build/pyinstaller-dist/<Name>/`.

5. `--window` (linux3, 8 November 2026, build 3 of the plan): Tauri's bundler (`packaging/tauri/bundle.py`) run
   on the window around that folder for `deb` and `appimage`, x86_64, on `ubuntu-22.04` with WebKitGTK 4.1 and
   the other packages Tauri needs (the workflow's apt line). Written to `dist/<Name>-x86_64.AppImage`, the
   download, and `dist/<Name>-amd64.deb`, which puts the window in `/usr/bin`, the server in
   `/usr/lib/<Name>/server`, a menu entry and, for Idiograph alone, the `.idiograph` type. `check_deb`
   unpacks the .deb and fails the build unless all of that is in it. The AppImage is then driven under xvfb
   by `packaging/tauri/drive_linux.py`. No update file, no signing and no upload yet (builds 5 and 7).
   On an ARM machine the files are `<Name>-aarch64.AppImage` and `<Name>-arm64.deb` (`linux_arch`, linuxfix).
"""
from __future__ import annotations

import argparse
import json
import re
import os
import platform
import shutil
import socket
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.request
from pathlib import Path

HERE = Path(__file__).resolve().parent
TOOL = HERE.parent
sys.path.insert(0, str(TOOL))
sys.path.insert(0, str(HERE))
import boot  # noqa: E402  the family's folders on the path (boot.py)
boot.setup()

import app_identity  # noqa: E402  which of the three apps a build is
import build_mac  # noqa: E402  the pins, the modules, the data files and the stage the Mac app has
from build_mac import window  # noqa: E402  Tauri's bundler run on the window, packaging/tauri/bundle.py
import typeset_helper  # noqa: E402  the typesetter beside the frozen server, packaging/typeset_helper.py

ENTRY = HERE / "linux_launcher.py"
# build_mac's pins as they are: certifi stays, since the frozen Python reads no system store the launcher
# could count on (mac_launcher.serve points SSL_CERT_FILE at it)
PINS = build_mac.PINS
# how long the smoke waits for the server to answer, and to end once asked to quit
START_WAIT = 90
QUIT_WAIT = 30


def name_of(app: str = app_identity.DEFAULT) -> str:
    """The frozen folder's and the executable's name, `Idiograph`, `Sift` or `Trace`."""
    return app_identity.APPS[app_identity.check(app)]["name"]


def say(line: str) -> None:
    print(line, flush=True)


def run(cmd, **kw) -> subprocess.CompletedProcess:
    return subprocess.run([str(c) for c in cmd], check=True, **kw)


# ── 1. the build venv ─────────────────────────────────────────────────────────────────────────

def choose_python(asked: str | None) -> Path:
    """The Python the build venv is made with: the one asked for, or the one running this script."""
    exe = Path(asked or sys.executable)
    facts = build_mac.python_facts(exe)
    if not facts or facts[0] < (3, 11):
        raise SystemExit(f"The app needs Python 3.11 or later to build, and {exe} is not.")
    return exe


def build_venv(build: Path, python: Path) -> Path:
    """The build venv with PINS in it, made afresh when the Python behind it has changed."""
    venv = build / "venv"
    marker = venv / "made-with.txt"
    want = f"{python}\n" + "\n".join(PINS) + "\n"
    py = venv / "bin" / "python"
    if not (marker.is_file() and marker.read_text(encoding="utf-8") == want and py.is_file()):
        shutil.rmtree(venv, ignore_errors=True)
        say(f"Making the build venv with {python}")
        run([python, "-m", "venv", venv])
        run([py, "-m", "pip", "install", "--disable-pip-version-check", "-q", *PINS])
        marker.write_text(want, encoding="utf-8")
    return py


# ── 2. the stage ──────────────────────────────────────────────────────────────────────────────

def stage_config(stage: Path, py: Path, app: str = app_identity.DEFAULT) -> Path | None:
    """config.json as the app ships it, or None when this Python cannot import the server, as in a dry
    run with no openpyxl."""
    try:
        return build_mac.stage_config(stage, py, app)
    except subprocess.CalledProcessError:
        return None


# ── 3. PyInstaller ────────────────────────────────────────────────────────────────────────────

def write_spec(build: Path, stage: Path, app: str = app_identity.DEFAULT) -> Path:
    """The spec: one Analysis of the launcher, one executable named for `app`, one folder. Its data are the
    Mac app's, the static page, the demo, the config, the guidance, the licences, the template and what an
    agent reads. The executable has a console: a Linux program writes to the terminal that ran it, so the
    command line and the MCP server need no twin as on Windows."""
    name = name_of(app)
    pathex, datas, modules = build_mac.bundle_inputs(stage, app)
    spec = f'''# Written by build_linux.py on every build. Change that script, never this file.
a = Analysis([{str(ENTRY)!r}], pathex={pathex!r},
             datas={datas!r},
             hiddenimports={[*modules, "mac_launcher"]!r}, excludes={build_mac.EXCLUDES!r}, noarchive=False)
pyz = PYZ(a.pure)
exe = EXE(pyz, a.scripts, [], exclude_binaries=True, name={name!r}, console=True, upx=False)
coll = COLLECT(exe, a.binaries, a.datas, name={name!r}, upx=False)
'''
    path = build / f"{name}-linux.spec"
    path.write_text(spec, encoding="utf-8")
    return path


def pyinstaller(py: Path, build: Path, spec: Path, app: str = app_identity.DEFAULT) -> Path:
    say("Freezing the app with PyInstaller")
    out = build / "pyinstaller-dist"
    run([py, "-m", "PyInstaller", "--noconfirm", "--clean", "--log-level", "WARN",
         "--distpath", out, "--workpath", build / "pyinstaller", spec])
    return out / name_of(app)


def check_frozen(frozen: Path, app: str = app_identity.DEFAULT) -> None:
    """`cli --help`, which imports the command line and through it the server and every module it needs,
    so a module the freeze left out stops the build here."""
    done = subprocess.run([str(frozen / name_of(app)), "cli", "--help"], capture_output=True,
                          text=True, encoding="utf-8", errors="replace", timeout=120)
    if done.returncode != 0:
        raise SystemExit(f"The frozen app did not start:\n{(done.stdout + done.stderr)[-2000:]}")
    say("The frozen app starts: its command line answered --help")


# ── 4. the smoke ──────────────────────────────────────────────────────────────────────────────

def free_port() -> int:
    """A port nothing holds on this machine's loopback."""
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


def smoke_environment(home: Path, base: dict | None = None) -> dict:
    """The environment the smoke's server runs in: a home folder of its own, every XDG folder left to
    default inside it, and no display, so nothing of the machine's own is read or written and nothing can
    open a window."""
    env = {k: v for k, v in (os.environ if base is None else base).items()
           if not k.startswith("XDG_") and k not in ("DISPLAY", "WAYLAND_DISPLAY", "BROWSER")}
    env.update(HOME=str(home), PYTHONUNBUFFERED="1", PYINSTALLER_RESET_ENVIRONMENT="1")
    return env


def smoke_command(frozen: Path, port: int, app: str = app_identity.DEFAULT) -> list:
    """The frozen server started as the window will start it, minus the window."""
    return [frozen / name_of(app), "--serve", "--port", str(port), "--no-browser"]


def fetch_state(port: int, post: dict | None = None, timeout: float = 3) -> dict | None:
    """`/api/server`, a GET, or a POST of `post` (the quit), as JSON, or None when nothing answers yet."""
    url = f"http://127.0.0.1:{port}/api/server"
    data = json.dumps(post).encode("utf-8") if post is not None else None
    req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"} if data else {})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as got:
            return json.loads(got.read().decode("utf-8"))
    except (OSError, ValueError, urllib.error.URLError):
        return None


def smoke(command: list, port: int, env: dict, app: str = app_identity.DEFAULT,
          start_wait: float = START_WAIT, quit_wait: float = QUIT_WAIT, log: Path | None = None) -> None:
    """Start `command`, wait for `/api/server` to answer as `app`, ask it to quit and wait for it to end.
    Anything else raises SystemExit with the server's last lines, and the process is always ended."""
    sink = open(log, "w", encoding="utf-8") if log else subprocess.DEVNULL
    proc = subprocess.Popen([str(c) for c in command], env=env, stdin=subprocess.DEVNULL, stdout=sink,
                            stderr=subprocess.STDOUT)

    def last() -> str:
        if not log:
            return ""
        try:
            return "\n" + "".join(log.read_text(encoding="utf-8", errors="replace").splitlines(True)[-20:])
        except OSError:
            return ""

    try:
        state, end = None, time.monotonic() + start_wait
        while time.monotonic() < end and proc.poll() is None:
            state = fetch_state(port)
            if state is not None:
                break
            time.sleep(0.5)
        if state is None:
            ended = f" (it ended with {proc.returncode})" if proc.poll() is not None else ""
            raise SystemExit(f"The frozen server did not answer /api/server within {start_wait:.0f} seconds{ended}.{last()}")
        if state.get("app") != app:
            raise SystemExit(f"The frozen server answered as {state.get('app')!r}, not {app!r}.{last()}")
        say(f"The frozen server serves: /api/server answered as {state['app']}, pid {state.get('pid')}")
        if fetch_state(port, {"op": "quit"}) is None:
            raise SystemExit(f"The frozen server did not take the quit.{last()}")
        try:
            proc.wait(timeout=quit_wait)
        except subprocess.TimeoutExpired:
            raise SystemExit(f"The frozen server did not end within {quit_wait:.0f} seconds of the quit.{last()}")
        say(f"The frozen server quit, exit {proc.returncode}")
    finally:
        if proc.poll() is None:
            proc.kill()
            proc.wait()
        if log:
            sink.close()


def smoke_frozen(frozen: Path, app: str = app_identity.DEFAULT) -> None:
    """The smoke of a built folder, in a temporary home, its log kept beside the folder."""
    port = free_port()
    with tempfile.TemporaryDirectory(prefix="idiograph-smoke-") as tmp:
        home = Path(tmp) / "home"
        home.mkdir()
        smoke(smoke_command(frozen, port, app), port, smoke_environment(home), app,
              log=frozen.parent / f"{name_of(app)}-smoke.log")


# ── 5. the window ─────────────────────────────────────────────────────────────────────────────

# what Tauri's AppImage bundler needs to run in a CI container: its tools are AppImages themselves, which
# are unpacked and run in place where a machine has no FUSE, and not stripped, whose old binutils stop on the
# newer libraries' relocations
BUNDLER_ENV = {"APPIMAGE_EXTRACT_AND_RUN": "1", "NO_STRIP": "true"}
# the library the window needs of the machine, which a .deb must depend on (an AppImage carries it)
WEBKIT_PACKAGE = "libwebkit2gtk-4.1"


def linux_arch(machine: str | None = None) -> tuple[str, str]:
    """The architecture a Linux build is for, as an AppImage's name and as a .deb's name have it: x86_64 and
    amd64, or aarch64 and arm64 on an ARM machine (linuxfix, 9 November 2026, after a build in an arm64 VM came out
    named for x86_64). `machine` is this Linux machine's own; off Linux, where a dry run says what the release's
    x86_64 machine builds, it is x86_64. release.py's names are x86_64's alone."""
    if machine is None:
        machine = platform.machine() if sys.platform.startswith("linux") else "x86_64"
    if machine.lower() in ("aarch64", "arm64", "armv8l"):
        return "aarch64", "arm64"
    return "x86_64", "amd64"


def window_names(app: str = app_identity.DEFAULT, test: bool = False, machine: str | None = None) -> dict:
    """The window's names for a build: the product's, which Tauri names the .deb's `lib/` folder and the
    bundles for, the executable's in `bin/`, and the two files `dist/` gets, named for the machine's
    architecture (`linux_arch`)."""
    name = name_of(app)
    conf = window.overrides(app_identity.version(app), test, None, None, app, True)
    product = conf.get("productName", name)
    image, deb = linux_arch(machine)
    return {"product": product, "main": conf.get("mainBinaryName", product), "name": name,
            "appimage": f"{name}-{image}.AppImage", "deb": f"{name}-{deb}.deb", "arch": image, "test": test, "app": app}


def deb_problems(tree: Path, depends: str, names: dict) -> list[str]:
    """What is missing or wrong in an unpacked .deb (`dpkg-deb -x`), as lines: the window in `usr/bin`, the
    frozen server in `usr/lib/<product>/server`, one desktop entry, the WebKitGTK package it depends on and,
    for Idiograph's own alone, the `.idiograph` type in the entry and as shared-mime-info's file, the type's icon
    in the hicolor theme and `%F` on the entry's Exec line (linuxfix). The other apps and the test app claim none."""
    out = []
    main, product, name = names["main"], names["product"], names["name"]
    if not (tree / "usr" / "bin" / main).is_file():
        out.append(f"usr/bin/{main} is not in the .deb")
    if not (tree / "usr" / "lib" / product / "server" / name).is_file():
        out.append(f"the frozen server, usr/lib/{product}/server/{name}, is not in the .deb")
    if not (tree / "usr" / "lib" / product / "server" / "_internal").is_dir():
        out.append(f"the frozen server's _internal folder is not in usr/lib/{product}/server")
    helper = tree / "usr" / "lib" / product / "server" / typeset_helper.NAME
    if not helper.is_file() or not os.access(helper, os.X_OK):
        out.append(f"the typesetter, usr/lib/{product}/server/{typeset_helper.NAME}, is not in the .deb or cannot run")
    desktops = sorted((tree / "usr" / "share" / "applications").glob("*.desktop"))
    if len(desktops) != 1:
        out.append(f"{len(desktops)} desktop entries in usr/share/applications, not one")
    text = desktops[0].read_text(encoding="utf-8", errors="replace") if desktops else ""
    # the entry's own icon, named for the app (Tauri writes `Icon=<executable's name>` and the picture under
    # usr/share/icons by that name), so Sift's and Trace's menu entries carry their marks, not Idiograph's
    icon_line = re.search(r"^Icon=(.*)$", text, re.M)
    icon = icon_line.group(1).strip() if icon_line else ""
    if desktops and not icon:
        out.append("the desktop entry has no Icon line")
    elif icon and not [p for p in (tree / "usr" / "share" / "icons").rglob("*") if p.is_file() and p.stem == icon]:
        out.append(f"no picture named {icon} under usr/share/icons for the desktop entry's Icon line")
    if WEBKIT_PACKAGE not in depends:
        out.append(f"the .deb does not depend on {WEBKIT_PACKAGE} (Depends: {depends})")
    claims = names["app"] == app_identity.DEFAULT and not names["test"]
    mime_file = tree / window.LINUX_MIME_DEST.lstrip("/")
    mime_line = re.search(r"^MimeType=(.*)$", text, re.M)
    in_entry = window.LINUX_MIME in (mime_line.group(1) if mime_line else "")
    # the entry's Exec line hands the app the files it is asked to open, %F, Idiograph's alone (linuxfix)
    exec_line = re.search(r"^Exec=(.*)$", text, re.M)
    takes_files = bool(exec_line) and exec_line.group(1).split()[-1:] == ["%F"]
    icons = [dest for dest in window.LINUX_MIME_ICONS if (tree / dest.lstrip("/")).is_file()]
    if claims:
        if not in_entry:
            out.append(f"the desktop entry's MimeType line lacks {window.LINUX_MIME}")
        if not mime_file.is_file():
            out.append(f"{window.LINUX_MIME_DEST} is not in the .deb, so a desktop has no name for a .idiograph file")
        if desktops and not takes_files:
            out.append("the desktop entry's Exec line does not end in %F, so a .idiograph file opened with it never reaches the app")
        if len(icons) != len(window.LINUX_MIME_ICONS):
            out.append(f"the .idiograph type's icon, {window.LINUX_MIME_ICON}, is not in every size under usr/share/icons/hicolor")
    elif in_entry or mime_file.exists() or takes_files or icons:
        out.append("this app claims the .idiograph type, which only Idiograph's own build does")
    return out


def check_deb(deb: Path, names: dict, work: Path) -> None:
    """Unpack the .deb with dpkg-deb and fail on anything `deb_problems` finds."""
    tree = work / "deb-tree"
    shutil.rmtree(tree, ignore_errors=True)
    run(["dpkg-deb", "-x", deb, tree])
    depends = subprocess.run(["dpkg-deb", "-f", str(deb), "Depends"], capture_output=True, text=True, encoding="utf-8",
                             errors="replace", check=True).stdout.strip()
    problems = deb_problems(tree, depends, names)
    if problems:
        raise SystemExit("The .deb is not right:\n  " + "\n  ".join(problems))
    say(f"The .deb holds the window, the server, one desktop entry and its dependency on {WEBKIT_PACKAGE}")


def build_window(frozen: Path, build: Path, dist: Path, app: str, test: bool) -> tuple[Path, Path]:
    """Tauri's bundler on the window around `frozen`, the AppImage and the .deb copied to `dist/` under
    their stable names, the .deb checked. Answers (appimage, deb)."""
    version = app_identity.version(app)
    names = window_names(app, test)
    made = window.bundle(frozen, build, version, ["deb", "appimage"], test=test, app=app, linux=True,
                         env={**os.environ, **BUNDLER_ENV})
    dist.mkdir(parents=True, exist_ok=True)
    out = []
    for kind in ("appimage", "deb"):
        target = dist / names[kind]
        target.unlink(missing_ok=True)
        shutil.copyfile(window.linux_bundle_of(made, kind, version), target)
        out.append(target)
    out[0].chmod(0o755)
    check_deb(out[1], names, build)
    return out[0], out[1]


def size_mb(path: Path) -> float:
    if path.is_file():
        return path.stat().st_size / 1e6
    return sum(p.lstat().st_size for p in path.rglob("*") if p.is_file() and not p.is_symlink()) / 1e6


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Build the Linux app's frozen server, Idiograph's, Sift's or Trace's.")
    ap.add_argument("--app", default=app_identity.DEFAULT, choices=list(app_identity.APPS),
                    help="the app to build, idiograph by default, sift or trace")
    ap.add_argument("--out", help="the folder build/ goes in, the app's own folder by default")
    ap.add_argument("--python", help="the Python 3.11 or later to build with, the one running this by default")
    ap.add_argument("--smoke", action="store_true", help="after the build, start the frozen server headless, ask /api/server, quit it")
    ap.add_argument("--smoke-only", action="store_true", help="only the smoke, on a folder an earlier build made")
    ap.add_argument("--window", action="store_true", help="after the build, the window around it: the AppImage and the .deb in dist/")
    ap.add_argument("--test-app", action="store_true", help="with --window, the test app, \"<Name> Test\", for a check")
    ap.add_argument("--dry-run", action="store_true", help="write the spec, say every step, run none")
    ap.add_argument("--list", action="store_true", help="print what the build would ship, each file and where it comes from, and build nothing")
    args = ap.parse_args(argv)
    if args.list:
        return build_mac.print_list(args.app, windows=True)
    if not sys.platform.startswith("linux") and not args.dry_run:
        raise SystemExit("The Linux server is frozen on Linux, as GitHub's ubuntu-22.04 machine does it. "
                         "--dry-run says every step here.")

    if args.test_app and not args.window:
        raise SystemExit("--test-app goes with --window.")
    app, name = args.app, name_of(args.app)
    out = Path(args.out).expanduser().resolve() if args.out else TOOL
    build, dist = out / "build", out / "dist"
    frozen = build / "pyinstaller-dist" / name
    if args.smoke_only:
        smoke_frozen(frozen, app)
        return 0
    stage = build / "stage"
    stage.mkdir(parents=True, exist_ok=True)

    if args.dry_run:
        say(f"Dry run, on {sys.platform}: nothing is installed, frozen or started.")
        say(f"1. Would make {build / 'venv'} with {args.python or sys.executable} and pip install {' '.join(PINS)}")
        py = Path(sys.executable)
    else:
        py = build_venv(build, choose_python(args.python))

    staged = (build_mac.stage_recordings(build_mac.stage_cases(stage)) if build_mac.ships_demo(app)
              else "none, the demo being Idiograph's,")
    config = stage_config(stage, py, app)
    spec = write_spec(build, stage, app)
    say(f"2. Staged the demo {staged}, "
        f"{'config.json' if config else 'no config.json, since this Python cannot import the server,'}")
    if args.dry_run:
        say(f"3. Would run PyInstaller on {spec.name}: {name}, one executable with a console, in {frozen}, "
            f"then {name} cli --help")
        say(f"   Would build {typeset_helper.NAME} with {' '.join(typeset_helper.build_command(build / 'typeset-target'))}, "
            f"put it in {frozen} beside {name} and typeset a line with the fonts there")
        say(f"4. Would start {name} --serve --port <free> --no-browser in a home folder of its own with no "
            f"display, ask /api/server, ask it to quit, and fail unless it answered as {app} and ended")
        if args.window:
            names = window_names(app, args.test_app)
            say(f"5. Would run Tauri {window.TAURI_CLI}'s bundler for deb and appimage ({names['product']}, "
                f"version {app_identity.version(app)}, {names['arch']}), write {dist / names['appimage']} and {dist / names['deb']}, "
                f"unpack the .deb and fail unless it holds usr/bin/{names['main']}, the server in usr/lib/{names['product']}/server, "
                f"one desktop entry and a dependency on {WEBKIT_PACKAGE}"
                + (", the .idiograph type in the entry and as a shared-mime-info file" if app == app_identity.DEFAULT and not args.test_app
                   else ", and no file type"))
        say(f"Wrote {spec}")
        return 0

    frozen = pyinstaller(py, build, spec, app)
    check_frozen(frozen, app)
    # the typesetter beside the server (typst1, 9 November 2026), run on a line with the fonts the folder carries
    helper = typeset_helper.place(typeset_helper.build(build), frozen)
    typeset_helper.check(helper, typeset_helper.fonts_in(frozen))
    say(f"The typesetter is beside the server, {size_mb(helper):.1f} MB, and typeset a line")
    say(f"Built {frozen}, version {app_identity.version(app)}, {size_mb(frozen):.0f} MB")
    if args.smoke:
        smoke_frozen(frozen, app)
    if args.window:
        appimage, deb = build_window(frozen, build, dist, app, args.test_app)
        say(f"Built {appimage}, {size_mb(appimage):.0f} MB, and {deb}, {size_mb(deb):.0f} MB")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
