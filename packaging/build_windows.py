#!/usr/bin/env python3
"""Build the Windows app, Idiograph in its own window with its own Python, and Idiograph-Setup.exe to
install it.

    py packaging\\build_windows.py                    from the app's folder, into build\\ and dist\\ beside it
    py packaging\\build_windows.py --out <folder>     into <folder>\\build and <folder>\\dist
    py packaging\\build_windows.py --sign-sha1 <thumbprint>   signed with that certificate (see SIGNTOOL)
    py packaging\\build_windows.py --test-app --out <folder>  a check's build, Idiograph Test
    python3 packaging/build_windows.py --dry-run      on any machine: the files written, every step said, none run
    python3 packaging/build_windows.py --list --app sift   on any machine: what Sift's build would ship

The counterpart of `build_mac.py`, whose pins, modules, data files and stage it takes, so the two
apps carry the same code and the same demo. GitHub's Windows machine runs it from
`.github/workflows/windows-installer.yml`, with Rust and Node.js for Tauri's bundler, and `build/` and
`dist/` are gitignored. The steps:

1. A build venv, `build\\venv`, made with the Python running this script or the one `--python`
   names, 3.11 or later, with build_mac's PINS but certifi, since Python on Windows checks HTTPS
   against Windows's own certificates. Never the repo's own `.venv`. PyInstaller comes from its source
   at the pinned version, its bootloader compiled on this machine by the MSVC GitHub's Windows machine
   has (`install_bootloader`), since 22 October 2026, when Windows Defender took 0.9.3 for
   Trojan:Win32/Bearfoos.x!ml on Curt's machine. A machine-learning guess of that kind often falls on
   the prebuilt bootloader every PyInstaller app shares, malware's included, and one built here has
   bytes of its own.
2. The stage, `build\\stage`: for Idiograph, the demo's three cases as Reset demo leaves them, through build_mac's
   `stage_cases`, and their recordings through its `stage_recordings`, each committed in `packaging/recording`
   under a name that carries the hash of the transcript it was made from, the licence beside each (recvoices, 12
   November 2026). A build takes a case's only when that hash is its transcript's, since another's timecodes would
   land on the wrong words, and else ships that case without it and says so in one line, its player then staying
   quiet. Sift's and Trace's builds carry no demo. `config.json`
   from `server.shipped_config(app)`, which names no project, and the icon as `Idiograph.ico`, drawn by
   make_app's `draw_icon`, the Mac icon's drawing, at each size Windows asks, up to 32 from the
   mark drawn for 16 pixels.
3. PyInstaller, one folder, from `packaging/windows_launcher.py`, with the Mac app's data: the server
   the window runs beside it, two executables, `Idiograph.exe`, windowed, which runs the server, and
   its console twin `Idiograph-console.exe`, for the command line, the MCP server and `stop`, since a
   windowed program cannot print to the terminal that ran it. A run of the twin's `cli --help`
   proves the frozen app finds every module. Since 22 October 2026 each executable carries a full
   Windows version resource (`version_resource`), the publisher and copyright tauri.conf.json gives
   the window and the installer, the app's name and version and the file's own name, where it had
   none, which scanners count against a program. Then the typesetter, `idiograph-typeset.exe`, built by cargo
   and put beside them, signed with them when signing, and run on a one-line page with the fonts the folder
   carries (typst1, 9 November 2026, `packaging/typeset_helper.py`).
4. Signing, in one place, SIGNTOOL: with `--sign-sha1`, the thumbprint of a code-signing
   certificate in this machine's store, signtool from the Windows SDK signs both executables, and
   Tauri the window and the installer with the same certificate. Without it the build says in one
   line that it is unsigned, and SmartScreen asks once before the installer runs.
5. `dist\\Idiograph-Setup.exe`, Tauri's NSIS installer (`packaging/tauri/bundle.py`, 17 October, the
   third Tauri build, in place of Inno Setup's): the window with the server beside it as `server\\`,
   installed for the current user alone, in `%LOCALAPPDATA%\\Idiograph`, with no administrator prompt,
   a Start menu entry, a desktop shortcut when ticked on its last page, an uninstaller in Settings,
   Apps, and the version the server carries. A newer version installs over the old, and the version
   Inno Setup installed is removed first (`packaging/tauri/src-tauri/windows/hooks.nsh`). Every
   setting and case stays, since they live in `%APPDATA%\\Idiograph`, never the install folder.
   Setup and the uninstaller stop a running Idiograph first, `Idiograph-console.exe stop`.
6. `--scan`, a step of its own after the build (22 October 2026): Windows Defender, where the machine
   has it on, scans the frozen folder, the window and the installer with its signatures brought up to
   date, and a finding stops the run with the file and the detection's name. A detection that is a
   cloud machine-learning guess, `!ml` at its end, may never show in a scan like this one.

`--app sift` or `--app trace` (20 October, the three-app split's build 6) builds that app in place of
Idiograph: `Sift.exe` and `Sift-console.exe`, by whose names the frozen server knows it is Sift, its own
icon, and `dist\\Sift-Setup.exe`, which installs Sift in `%LOCALAPPDATA%\\Sift` under its own name, bundle
id and update address (`packaging/tauri/bundle.py`), beside Idiograph and never over it.
"""
from __future__ import annotations

import argparse
import glob
import hashlib
import json
import os
import re
import shutil
import struct
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
TOOL = HERE.parent
sys.path.insert(0, str(TOOL))
sys.path.insert(0, str(HERE))
import boot  # noqa: E402  the family's folders on the path (boot.py)
boot.setup()

import app_folders  # noqa: E402  the two executables' names
import app_identity  # noqa: E402  which of the three apps a build is
import build_mac  # noqa: E402  the pins, the modules, the data files and the stage the Mac app has
import make_app  # noqa: E402  the icon's drawing
from build_mac import window  # noqa: E402  Tauri's bundler run on the window, packaging/tauri/bundle.py
import typeset_helper  # noqa: E402  the typesetter beside the frozen server, packaging/typeset_helper.py

NAME = "Idiograph"
ENTRY = HERE / "windows_launcher.py"
WINDOWED = Path(app_folders.WINDOWED_EXE).stem
CONSOLE = Path(app_folders.CONSOLE_EXE).stem
# build_mac's pins, certifi left out: the Windows app checks HTTPS against Windows's own certificates
PINS = tuple(p for p in build_mac.PINS if not p.startswith("certifi=="))
MODULES = build_mac.MODULES
# the installer's name as it ships, and the id Inno Setup's installer had, up to 0.9.0, the same on
# every version, by which Tauri's installer finds that install and removes it first (hooks.nsh)
SETUP = "Idiograph-Setup"
APP_ID = "C7E7DA37-1EC0-4980-B693-28D0962DA65C"
PUBLISHER = "Adam Knowles"
# tauri.conf.json, whose publisher and copyright the window and the installer carry, and the server's
# two executables with them (`version_resource`)
TAURI_CONF = HERE / "tauri" / "src-tauri" / "tauri.conf.json"
# PyInstaller built from its source, its bootloader compiled on the machine that builds, never the
# prebuilt one in the wheel every PyInstaller app shares (`install_bootloader`)
BOOTLOADER_ENV = {"PYINSTALLER_COMPILE_BOOTLOADER": "1"}
# what PyInstaller's build says as it compiles the bootloader, by which the build knows it did
BOOTLOADER_SAID = "compile the bootloader"
# Windows Defender's command line, in its own updated platform folder or where Windows put it first
DEFENDER_PLATFORM = r"%ProgramData%\Microsoft\Windows Defender\Platform"
DEFENDER_FIRST = r"%ProgramFiles%\Windows Defender\MpCmdRun.exe"
# the sizes Windows draws the icon at, from the taskbar's to the large tiles'
ICO_SIZES = (16, 24, 32, 48, 64, 128, 256)
# Signing, the one place: signtool's command, `$f` the file, for a certificate by its thumbprint.
# It needs a code-signing certificate from a certificate authority, or Azure Trusted Signing, in the
# store of the machine that builds, and on GitHub's machine a secret to bring it there. Tauri signs
# the window and the installer with the same thumbprint (`window.overrides`)
SIGNTOOL = ("{signtool} sign /sha1 {sha1} /fd sha256 /tr http://timestamp.digicert.com /td sha256 $f")


def names(app: str = app_identity.DEFAULT) -> dict:
    """The names a build of `app` makes: the frozen folder's, the two executables' and the installer's,
    `Idiograph`, `Idiograph.exe`, `Idiograph-console.exe` and `Idiograph-Setup` for Idiograph, `Sift`,
    `Sift.exe`, `Sift-console.exe` and `Sift-Setup` for Sift."""
    name = app_identity.APPS[app_identity.check(app)]["name"]
    return {"name": name, "windowed": app_folders.windowed_exe(app), "console": app_folders.console_exe(app),
            "setup": f"{name}-Setup"}


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


def pyinstaller_pin() -> str:
    """PyInstaller's pin, from build_mac's PINS, the one version both apps freeze with."""
    found = [p for p in PINS if p.lower().startswith("pyinstaller==")]
    if len(found) != 1:
        raise SystemExit("build_mac.PINS names no one PyInstaller version.")
    return found[0]


def bootloader_install(py: Path) -> list:
    """pip's command for PyInstaller from its source at the pin, never a wheel, its own or one pip kept,
    said in full so the bootloader's compiling shows in the log. Run with BOOTLOADER_ENV."""
    return [py, "-m", "pip", "install", "--disable-pip-version-check", "--no-cache-dir", "--verbose",
            "--no-binary", "pyinstaller", pyinstaller_pin()]


def install_bootloader(py: Path) -> None:
    """PyInstaller from its source with its bootloader compiled here, and the build stopped when pip
    said nothing of compiling it, so a wheel found elsewhere never slips in. The bootloaders' hashes
    go in the log."""
    say(f"Building {pyinstaller_pin()} from its source, its bootloader compiled on this machine")
    done = subprocess.run([str(c) for c in bootloader_install(py)], env={**os.environ, **BOOTLOADER_ENV},
                          capture_output=True, text=True, encoding="utf-8", errors="replace")
    said = done.stdout + done.stderr
    if done.returncode != 0 or BOOTLOADER_SAID not in said:
        raise SystemExit(f"PyInstaller's bootloader was not compiled here:\n{said[-4000:]}")
    where = subprocess.run([str(py), "-X", "utf8", "-c", "import PyInstaller, os; print(os.path.dirname(PyInstaller.__file__))"],
                           capture_output=True, text=True, encoding="utf-8", check=True).stdout.strip()
    for exe in sorted(Path(where, "bootloader").glob("Windows-64bit-*/run*.exe")):
        say(f"  {exe.parent.name}/{exe.name} sha256 {hashlib.sha256(exe.read_bytes()).hexdigest()}")


def build_venv(build: Path, python: Path) -> Path:
    """The build venv with PINS in it, PyInstaller from its source, made afresh when the Python behind
    it has changed or it was made before its bootloader was compiled here."""
    venv = build / "venv"
    marker = venv / "made-with.txt"
    want = f"{python}\n" + "\n".join(PINS) + "\nbootloader compiled here\n"
    py = venv / "Scripts" / "python.exe"
    if not (marker.is_file() and marker.read_text(encoding="utf-8") == want and py.is_file()):
        shutil.rmtree(venv, ignore_errors=True)
        say(f"Making the build venv with {python}")
        run([python, "-m", "venv", venv])
        run([py, "-m", "pip", "install", "--disable-pip-version-check", "-q", *(p for p in PINS if p != pyinstaller_pin())])
        install_bootloader(py)
        marker.write_text(want, encoding="utf-8")
    return py


# ── 2. the stage ──────────────────────────────────────────────────────────────────────────────

def ico_bytes(sizes=ICO_SIZES, app: str = app_identity.DEFAULT) -> bytes:
    """The icon of `app` as a Windows .ico: make_app's drawing at each size, each image a PNG, which
    Windows has read in an icon since Vista. A header, an entry of 16 bytes for each image, then the
    images."""
    images = [make_app.png_bytes(s, make_app.draw_icon(s, app)) for s in sizes]
    head = struct.pack("<HHH", 0, 1, len(images))
    offset = 6 + 16 * len(images)
    entries, data = b"", b""
    for size, png in zip(sizes, images):
        # a width or height of 256 is written as 0
        entries += struct.pack("<BBBBHHII", size % 256, size % 256, 0, 0, 1, 32, len(png), offset + len(data))
        data += png
    return head + entries + data


def stage_config(stage: Path, py: Path, app: str = app_identity.DEFAULT) -> Path | None:
    """config.json as the app ships it, through build_mac's own, or None when this Python cannot
    import the server, as in a dry run with no openpyxl."""
    try:
        return build_mac.stage_config(stage, py, app)
    except subprocess.CalledProcessError:
        return None


def app_version(app: str = app_identity.DEFAULT) -> str:
    """The app's version, its entry in versions.json, so a dry run needs nothing installed."""
    return app_identity.version(app)


# ── 3. PyInstaller ────────────────────────────────────────────────────────────────────────────

def publisher() -> dict:
    """The publisher and the copyright tauri.conf.json gives the window and the installer."""
    bundle = json.loads(TAURI_CONF.read_text(encoding="utf-8"))["bundle"]
    return {"company": bundle["publisher"], "copyright": bundle["copyright"]}


def version_resource(exe: str, product: str, version: str) -> str:
    """The Windows version resource of the executable `exe`, as PyInstaller's `version=` file holds it,
    a VSVersionInfo in its text form: the publisher and copyright the window carries, `product` as the
    product and the file's description, the version in Windows's four numbers, and the file's own
    name. US English in Unicode, as Windows reads it first."""
    who, four = publisher(), version_info(version)
    numbers = tuple(int(n) for n in four.split("."))
    strings = {"CompanyName": who["company"], "FileDescription": product, "FileVersion": four,
               "InternalName": Path(exe).stem, "LegalCopyright": who["copyright"], "OriginalFilename": exe,
               "ProductName": product, "ProductVersion": four}
    table = ",\n".join(f"        StringStruct({k!r}, {v!r})" for k, v in strings.items())
    return f"""# -*- coding: utf-8 -*-
# Written by build_windows.py on every build. Change that script, never this file.
VSVersionInfo(
  ffi=FixedFileInfo(filevers={numbers!r}, prodvers={numbers!r}, mask=0x3f, flags=0x0, OS=0x40004,
                    fileType=0x1, subtype=0x0, date=(0, 0)),
  kids=[
    StringFileInfo([StringTable('040904B0', [
{table}])]),
    VarFileInfo([VarStruct('Translation', [1033, 1200])])
  ]
)
"""


def write_spec(build: Path, stage: Path, app: str = app_identity.DEFAULT, version: str | None = None,
               product: str | None = None) -> Path:
    """The spec: one Analysis of the launcher, two executables from it, one folder, each named for
    `app`, each with its version resource, `product` and `version` the app's own unless a test build
    names others. Its data are the Mac app's, the static page, the demo, the config, the guidance,
    the licences, the template and what an agent reads."""
    named = names(app)
    version, product = version or app_version(app), product or named["name"]
    resources = {}
    for kind in ("windowed", "console"):
        resources[kind] = build / f"{Path(named[kind]).stem}-version.txt"
        resources[kind].write_text(version_resource(named[kind], product, version), encoding="utf-8")
    # the folders, the data and the modules the Mac build takes, from its folder lists (build_mac.bundle_inputs)
    pathex, datas, modules = build_mac.bundle_inputs(stage, app)
    icon = str(stage / f"{named['name']}.ico")
    spec = f'''# Written by build_windows.py on every build. Change that script, never this file.
a = Analysis([{str(ENTRY)!r}], pathex={pathex!r},
             datas={datas!r},
             hiddenimports={modules!r}, excludes={build_mac.EXCLUDES!r}, noarchive=False)
pyz = PYZ(a.pure)
windowed = EXE(pyz, a.scripts, [], exclude_binaries=True, name={Path(named["windowed"]).stem!r}, console=False,
               icon={icon!r}, version={str(resources["windowed"])!r}, upx=False)
console = EXE(pyz, a.scripts, [], exclude_binaries=True, name={Path(named["console"]).stem!r}, console=True,
              icon={icon!r}, version={str(resources["console"])!r}, upx=False)
coll = COLLECT(windowed, console, a.binaries, a.datas, name={named["name"]!r}, upx=False)
'''
    path = build / f"{named['name']}-windows.spec"
    path.write_text(spec, encoding="utf-8")
    return path


def pyinstaller(py: Path, build: Path, spec: Path, app: str = app_identity.DEFAULT) -> Path:
    say("Freezing the app with PyInstaller")
    out = build / "pyinstaller-dist"
    run([py, "-m", "PyInstaller", "--noconfirm", "--clean", "--log-level", "WARN",
         "--distpath", out, "--workpath", build / "pyinstaller", spec])
    return out / names(app)["name"]


def check_frozen(frozen: Path, app: str = app_identity.DEFAULT) -> None:
    """The console twin's `cli --help`, which imports the command line and through it the server
    and every module it needs, so a module the freeze left out stops the build here."""
    done = subprocess.run([str(frozen / names(app)["console"]), "cli", "--help"], capture_output=True,
                          text=True, encoding="utf-8", errors="replace", timeout=120)
    if done.returncode != 0:
        raise SystemExit(f"The frozen app did not start:\n{(done.stdout + done.stderr)[-2000:]}")
    say("The frozen app starts: its command line answered --help")


# ── 4. signing ────────────────────────────────────────────────────────────────────────────────

def find_signtool() -> str | None:
    """signtool from the newest Windows SDK, or on the PATH."""
    found = sorted(glob.glob(os.path.expandvars(r"%ProgramFiles(x86)%\Windows Kits\10\bin\*\x64\signtool.exe")))
    return found[-1] if found else shutil.which("signtool")


def signing(sha1: str | None) -> tuple[str | None, str]:
    """signtool's command for a certificate's thumbprint, or None, and the one line that says which."""
    if not sha1:
        return None, ("Unsigned: no --sign-sha1, so Windows SmartScreen says it protected the PC, and "
                      "More info, Run anyway opens the installer, once.")
    tool = find_signtool()
    if not tool:
        raise SystemExit("--sign-sha1 needs signtool, from the Windows SDK.")
    return SIGNTOOL.format(signtool=f'"{tool}"', sha1=sha1), f"Signed with the certificate {sha1}."


def sign_files(command: str, files: list[Path]) -> None:
    for path in files:
        subprocess.run(command.replace("$f", f'"{path}"'), check=True, shell=False)


# ── 5. the installer ──────────────────────────────────────────────────────────────────────────

def version_info(version: str) -> str:
    """The version as Windows's file version wants it, four numbers."""
    numbers = [int(n) for n in re.findall(r"\d+", version)][:4]
    return ".".join(str(n) for n in numbers + [0] * (4 - len(numbers)))


def installer_of(made: Path, version: str) -> Path:
    """The installer Tauri's bundler made for this version, `<name>_<version>_x64-setup.exe` under `nsis`,
    never another version's left beside it by an earlier build or a cache: the fourth Tauri build's second
    run on GitHub took a 0.9.2 installer its cache had kept for the 0.9.1 it had just built (18 October)."""
    found = sorted(p for p in (made / "nsis").glob("*-setup.exe") if f"_{version}_" in p.name)
    if not found:
        raise SystemExit(f"Tauri's bundler made no installer for {version} in {made / 'nsis'}.")
    return found[-1]


# ── 6. Windows Defender's scan ────────────────────────────────────────────────────────────────

def find_defender() -> str | None:
    """MpCmdRun.exe from Defender's newest platform folder, or where Windows put it first, or None."""
    platforms = sorted(glob.glob(os.path.join(os.path.expandvars(DEFENDER_PLATFORM), "*", "MpCmdRun.exe")))
    first = os.path.expandvars(DEFENDER_FIRST)
    return platforms[-1] if platforms else (first if os.path.isfile(first) else None)


def defender_on() -> bool:
    """Whether Defender's antivirus runs on this machine, as Get-MpComputerStatus says."""
    try:
        done = subprocess.run(["powershell", "-NoProfile", "-Command", "(Get-MpComputerStatus).AntivirusEnabled"],
                              capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=120)
    except (OSError, subprocess.TimeoutExpired):
        return False
    return done.stdout.strip().lower() == "true"


def scanned(build: Path, dist: Path, app: str = app_identity.DEFAULT) -> list[Path]:
    """What a build of `app` ships: the frozen folder, the window Tauri built and the installer."""
    named = names(app)
    return [build / "pyinstaller-dist" / named["name"], build / "target" / "release" / f"{named['name']}.exe",
            dist / f"{named['setup']}.exe"]


def detections(said: str) -> list[tuple[str, str]]:
    """The threats in MpCmdRun's report, each its detection's name and the file it was found in."""
    found, threat = [], None
    for line in said.splitlines():
        key, _, value = line.partition(":")
        key, value = key.strip().lower(), value.strip()
        if key == "threat":
            threat = value
        elif key == "file" and threat:
            found.append((threat, value))
    return found


def defender_scan(paths: list[Path], tool: str | None = None, on: bool | None = None, runner=subprocess.run) -> int:
    """Each of `paths` scanned by Defender with nothing removed, its signatures updated first, the
    report printed, and 1 when it found anything, each finding said as a GitHub error with its file
    and its name. Missing or off, it says so and answers 0, as does a scan that could not run."""
    tool = tool if tool is not None else find_defender()
    if not tool:
        say("Windows Defender is not on this machine, so nothing was scanned.")
        return 0
    if not (defender_on() if on is None else on):
        say("Windows Defender is off on this machine, so nothing was scanned.")
        return 0
    updated = runner([tool, "-SignatureUpdate"], capture_output=True, text=True, encoding="utf-8", errors="replace")
    say("Defender's signatures brought up to date." if updated.returncode == 0
        else f"Defender's signatures could not be updated ({updated.returncode}), so it scans with those it has.")
    say("A cloud machine-learning detection, one ending !ml, may not show in a scan here.")
    found = []
    for path in paths:
        if not path.exists():
            say(f"Not scanned, not built: {path}")
            continue
        done = runner([tool, "-Scan", "-ScanType", "3", "-File", str(path), "-DisableRemediation"],
                      capture_output=True, text=True, encoding="utf-8", errors="replace")
        said = (done.stdout or "") + (done.stderr or "")
        print(said.strip(), flush=True)
        hits = detections(said)
        if done.returncode == 2 or hits:
            found += hits or [("a detection MpCmdRun did not name", str(path))]
        elif done.returncode != 0:
            say(f"Defender could not scan {path} ({done.returncode}).")
        else:
            say(f"Defender found nothing in {path}")
    for threat, where in found:
        say(f"::error file={where}::Windows Defender detected {threat} in {where}")
    return 1 if found else 0


def size_mb(path: Path) -> float:
    if path.is_file():
        return path.stat().st_size / 1e6
    return sum(p.stat().st_size for p in path.rglob("*") if p.is_file()) / 1e6


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Build the Windows app and Idiograph-Setup.exe, or Sift's or Trace's.")
    ap.add_argument("--app", default=app_identity.DEFAULT, choices=list(app_identity.APPS),
                    help="the app to build, idiograph by default, sift or trace")
    ap.add_argument("--out", help="the folder build/ and dist/ go in, the app's own folder by default")
    ap.add_argument("--python", help="the Python 3.11 or later to build with, the one running this by default")
    ap.add_argument("--sign-sha1", help="the thumbprint of the code-signing certificate to sign with")
    ap.add_argument("--test-app", action="store_true", help="the test app, Idiograph Test, for a check")
    ap.add_argument("--dry-run", action="store_true", help="write the spec and Tauri's settings, say every step, run none")
    ap.add_argument("--scan", action="store_true", help="after a build, scan what it made with Windows Defender")
    # a check's own release, for the test app alone (18 October, the fourth Tauri build), as build_mac.py has
    ap.add_argument("--version", help="the test app's version, in place of its own in versions.json")
    ap.add_argument("--whats-new", help="the test app's notes, in place of docs/whats-new.md")
    ap.add_argument("--update-key", help="a file holding the public half of a check's throwaway update key")
    ap.add_argument("--update-url", help="the address of a check's update manifest, on this machine")
    ap.add_argument("--list", action="store_true", help="print what the build would ship, each file and where it comes from, and build nothing")
    args = ap.parse_args(argv)
    if args.list:
        return build_mac.print_list(args.app, windows=True)
    if (args.version or args.whats_new or args.update_key or args.update_url) and not args.test_app:
        raise SystemExit("--version, --whats-new, --update-key and --update-url are for the test app alone.")
    if bool(args.update_key) != bool(args.update_url):
        raise SystemExit("--update-key and --update-url go together.")
    if sys.platform != "win32" and not (args.dry_run or args.scan):
        raise SystemExit("The Windows app is built on Windows, as GitHub's Windows machine builds it. "
                         "--dry-run says every step here.")

    app, named = args.app, names(args.app)
    out = Path(args.out).expanduser().resolve() if args.out else TOOL
    build, dist = out / "build", out / "dist"
    if args.scan:
        return defender_scan(scanned(build, dist, app))
    stage = build / "stage"
    stage.mkdir(parents=True, exist_ok=True)
    dist.mkdir(parents=True, exist_ok=True)
    frozen = build / "pyinstaller-dist" / named["name"]
    version = args.version or app_version(app)
    update = window.test_update(Path(args.update_key).read_text(encoding="utf-8"), args.update_url) if args.update_key else None
    conf = window.overrides(version, args.test_app, None, update, app)
    product = conf.get("productName", NAME)
    setup = dist / (f"{product}-Setup.exe" if args.test_app else f"{named['setup']}.exe")

    if args.dry_run:
        say(f"Dry run, on {sys.platform}: nothing is installed, frozen, signed or bundled.")
        say(f"1. Would make {build / 'venv'} with {args.python or sys.executable}, pip install "
            f"{' '.join(p for p in PINS if p != pyinstaller_pin())}, and build {pyinstaller_pin()} from its "
            f"source with {' '.join(f'{k}={v}' for k, v in BOOTLOADER_ENV.items())}, its bootloader compiled here")
        py = Path(sys.executable)
    else:
        py = build_venv(build, choose_python(args.python))

    # Idiograph's demo alone, since the sixth build (23 October 2026) no other app's build carries it
    staged = (build_mac.stage_recordings(build_mac.stage_cases(stage)) if build_mac.ships_demo(app)
              else "none, the demo being Idiograph's,")
    config = stage_config(stage, py, app)
    (stage / f"{named['name']}.ico").write_bytes(ico_bytes(app=app))
    spec = write_spec(build, stage, app, version, product)
    sign, line = signing(None if args.dry_run else args.sign_sha1)
    settings = build / "tauri-config.json"
    settings.write_text(json.dumps(window.overrides(version, args.test_app, args.sign_sha1 if sign else None, update, app), indent=2) + "\n",
                        encoding="utf-8")
    say(f"2. Staged the demo {staged}, "
        f"{'config.json' if config else 'no config.json, since this Python cannot import the server,'} and {named['name']}.ico")
    if args.dry_run:
        say(f"3. Would run PyInstaller on {spec.name}: {named['windowed']}, windowed, and "
            f"{named['console']}, each with its version resource, {product} {version_info(version)}, "
            f"in {frozen}, then {named['console']} cli --help")
        say(f"   Would build {typeset_helper.exe_name(True)} with "
            f"{' '.join(typeset_helper.build_command(build / 'typeset-target'))}, put it in {frozen} beside "
            f"{named['console']}, sign it with them and typeset a line with the fonts there")
        say(f"4. {line}")
        say(f"5. Would run Tauri {window.TAURI_CLI}'s bundler for the NSIS installer with {settings.name}, "
            f"for {setup}, version {version}, installing {product} in %LOCALAPPDATA%\\{product} "
            f"as {conf.get('identifier', 'uk.co.adamknowles.idiograph')}")
        say(f"Wrote {spec} and {settings}")
        return 0

    frozen = pyinstaller(py, build, spec, app)
    check_frozen(frozen, app)
    # the typesetter beside the server (typst1, 9 November 2026), signed with them and run on a line
    helper = typeset_helper.place(typeset_helper.build(build), frozen)
    if sign:
        sign_files(sign, [frozen / named["windowed"], frozen / named["console"], helper])
    typeset_helper.check(helper, typeset_helper.fonts_in(frozen))
    say(f"The typesetter is beside the server, {size_mb(helper):.1f} MB, and typeset a line")
    made = window.bundle(frozen, build, version, ["nsis"], test=args.test_app,
                         windows_sign=args.sign_sha1 if sign else None, update=update,
                         whats_new=Path(args.whats_new).resolve() if args.whats_new else None, app=app)
    setup.unlink(missing_ok=True)
    shutil.copyfile(installer_of(made, version), setup)
    say(f"Built {frozen}, version {version}, {size_mb(frozen):.0f} MB")
    say(f"Built {setup}, {size_mb(setup):.0f} MB")
    say(line)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
