#!/usr/bin/env python3
"""Adam's own Mac copy of Idiograph, built on this Mac each day from main and swapped into /Applications,
using no GitHub Actions minutes (macdaily, 9 November 2026, Adam, 9 November about 13:20 by dialog: a GitHub
release once a week, on Mondays, and his own copy built here each day).

    python3 packaging/mac_daily.py              # build main's HEAD, check it, swap it in when the app is closed
    python3 packaging/mac_daily.py --dry-run    # build and check, never swap
    python3 packaging/mac_daily.py --ref <sha>  # another commit of the repository than main's HEAD

The steps, each said in one line:

1. A clean export of the commit, `git archive` of `--ref` (main by default) into `.verify/macdaily/src-<sha>`,
   never the working tree, so what is built is what main holds and nothing uncommitted reaches the app.
2. The build, as the workflow's mac-app job makes it: the export's own `packaging/build_mac.py --unsigned`,
   the same pins, the frozen server, Tauri's bundle at the pinned CLI, arm64 alone, signed ad hoc as the
   job's and Adam's installed copy are, with `--build <sha>` so the app carries `build.json` naming the
   commit, which About shows after the version ("Version 0.9.23, build e45b1af") and a note from Send
   feedback carries. The version is main's own, versions.json's, the week's release's number. The build
   folder, `.verify/macdaily/build`, is kept from day to day, so its venv, Juno's recording and cargo's
   work are made once. It runs through `~/.claude/bin/heavy idiograph build`, the shared Mac's queue.
3. The checks: the app, its server and its typesetter arm64 alone, the bundle's version versions.json's, `codesign
   --verify --deep --strict`, the server's `cli --help`, the typesetter beside the server typesetting a one-line
   page with the fonts the app carries (typst1, 9 November 2026), and the server started from inside the app in a home
   folder of its own (`--serve --no-browser` on a free port), asked for `/api/server`, which must answer as
   Idiograph with the version and the build, then asked to quit.
4. The swap, unless `--dry-run`: the checked app copied to `.verify/macdaily/ready-<sha>`, so the next day's
   build cannot change it while it waits, and handed to `~/.claude/bin/idiograph-swap-watch` as
   idiograph-release hands it a release, which swaps it in once his copy has not run for 12 seconds, at once
   when it is closed, the old copy kept in `.verify/app-before-daily-<date>` (`-2` and on for a second that
   day). Run it in the background: the watch's one line, `SWAP: DONE ...`, is the outcome. A copy of the
   same commit already in /Applications is left as it is unless `--force`.

The updater needs nothing. A daily copy keeps main's version, and Tauri's updater offers a release only when
its version is greater than the running one, so a daily copy of 0.9.24 made before 0.9.24's release is never
offered 0.9.23 (no downgrade), and once 0.9.24 is out it is not offered 0.9.24 either (equal, no loop): the
next day's build replaces it. Nothing is pushed, tagged or released.
"""
from __future__ import annotations

import argparse
import json
import os
import plistlib
import shutil
import subprocess
import sys
import tempfile
import time
from datetime import date
from pathlib import Path

HERE = Path(__file__).resolve().parent
TOOL = HERE.parent
sys.path.insert(0, str(TOOL))
sys.path.insert(0, str(HERE))
import boot  # noqa: E402  the family's folders on the path (boot.py)
boot.setup()

import build_linux  # noqa: E402  the smoke's parts: a free port, a home of its own, /api/server
import typeset_helper  # noqa: E402  the typesetter beside the server and its one-line page

APP = "idiograph"
NAME = "Idiograph"
INSTALLED = Path("/Applications") / f"{NAME}.app"
BIN = Path.home() / ".claude" / "bin"
HEAVY = BIN / "heavy"
SWAP = BIN / "idiograph-swap-watch"
# how long the server inside the app may take to answer, and to end once asked to quit
START_WAIT = 90
QUIT_WAIT = 30


def say(line: str) -> None:
    print(line, flush=True)


def git(repo: Path, *args: str) -> str:
    return subprocess.run(["git", "-C", str(repo), *args], check=True, capture_output=True, text=True,
                          encoding="utf-8").stdout.strip()


def commit_of(repo: Path, ref: str) -> tuple[str, str]:
    """The commit `ref` names, in full and as the seven-letter short sha the app shows."""
    full = git(repo, "rev-parse", "--verify", f"{ref}^{{commit}}")
    return full, full[:7]


def export(repo: Path, full: str, work: Path) -> Path:
    """The commit's tree, and nothing else, in `work/src-<sha>`, made afresh. Earlier days' exports go."""
    for old in work.glob("src-*"):
        shutil.rmtree(old, ignore_errors=True)
    src = work / f"src-{full[:7]}"
    src.mkdir(parents=True)
    archive = subprocess.Popen(["git", "-C", str(repo), "archive", "--format=tar", full], stdout=subprocess.PIPE)
    subprocess.run(["tar", "-x", "-C", str(src)], stdin=archive.stdout, check=True)
    archive.stdout.close()
    if archive.wait() != 0:
        raise SystemExit(f"git archive of {full[:7]} failed.")
    return src


def build_command(src: Path, work: Path, short: str, python: str, heavy: Path | None = HEAVY) -> list[str]:
    """The export's own build_mac.py as the workflow's mac-app job runs it, unsigned, with the commit named,
    into the kept build folder, through the shared Mac's queue when `heavy` is there."""
    cmd = [python, str(src / "packaging" / "build_mac.py"), "--unsigned", "--app", APP, "--build", short,
           "--out", str(work)]
    return ([str(heavy), "idiograph", "build", *cmd]) if heavy and heavy.is_file() else cmd


def backup_dir(repo: Path, day: date | None = None) -> Path:
    """Where the copy the swap replaces is kept: `.verify/app-before-daily-<date>`, `-2` and on when that one is
    already there, since the watch moves the old app into the folder and a second move would nest it."""
    base = repo / ".verify" / f"app-before-daily-{(day or date.today()).isoformat()}"
    path, n = base, 2
    while path.exists():
        path, n = base.with_name(f"{base.name}-{n}"), n + 1
    return path


def server_of(app: Path) -> Path:
    """The frozen server inside the app, as tauri.macos.conf.json lays it."""
    return app / "Contents" / "Resources" / "server" / NAME


def typesetter_of(app: Path) -> Path:
    """The typesetter inside the app, beside the frozen server (typst1, 9 November 2026)."""
    return server_of(app).parent / typeset_helper.NAME


def build_in(app: Path) -> str:
    """The commit an installed copy was built from, from its `build.json`, or empty for a release."""
    for path in (app / "Contents" / "Resources" / "server" / "_internal" / "build.json",
                 app / "Contents" / "Resources" / "server" / "build.json"):
        try:
            return str(json.loads(path.read_text(encoding="utf-8")).get("build") or "")
        except (OSError, ValueError, AttributeError):
            continue
    return ""


def archs(path: Path) -> str:
    return subprocess.run(["lipo", "-archs", str(path)], capture_output=True, text=True, encoding="utf-8",
                          errors="replace").stdout.strip()


def check(app: Path, version: str, short: str) -> None:
    """The built app as it must be before it may replace his copy. Anything wrong stops here."""
    if not typesetter_of(app).is_file():
        raise SystemExit(f"The app has no typesetter beside its server, {typeset_helper.NAME}.")
    for part in (app / "Contents" / "MacOS" / NAME, server_of(app), typesetter_of(app)):
        got = archs(part)
        if got != "arm64":
            raise SystemExit(f"{part.relative_to(app.parent)} is for {got or 'no architecture'}, not arm64 alone.")
    with open(app / "Contents" / "Info.plist", "rb") as fh:
        shown = plistlib.load(fh).get("CFBundleShortVersionString")
    if shown != version:
        raise SystemExit(f"The app says version {shown}, and versions.json {version}.")
    if build_in(app) != short:
        raise SystemExit(f"The app carries build {build_in(app) or 'none'}, not {short}.")
    done = subprocess.run(["codesign", "--verify", "--deep", "--strict", str(app)], capture_output=True, text=True,
                          encoding="utf-8", errors="replace")
    if done.returncode != 0:
        raise SystemExit(f"codesign refuses the app:\n{done.stderr.strip()}")
    done = subprocess.run([str(server_of(app)), "cli", "--help"], capture_output=True, text=True, encoding="utf-8",
                          errors="replace", timeout=120)
    if done.returncode != 0:
        raise SystemExit(f"The app's command line did not answer --help:\n{(done.stdout + done.stderr)[-2000:]}")
    made = typeset_helper.check(typesetter_of(app), typeset_helper.fonts_in(server_of(app).parent))
    say(f"Checked: arm64, version {shown}, build {short}, codesign verifies, cli --help answers, "
        f"the typesetter typeset a line with the app's fonts ({made} bytes of PDF)")
    serve(app, version, short)


def serve(app: Path, version: str, short: str) -> None:
    """The server inside the app started as the window starts it, minus the window, in a home folder of its own,
    so nothing of his settings is read or written: `/api/server` must answer as Idiograph with this version and
    build, then it is asked to quit and must end."""
    port = build_linux.free_port()
    with tempfile.TemporaryDirectory(prefix="idiograph-daily-") as tmp:
        home = Path(tmp) / "home"
        home.mkdir()
        env = build_linux.smoke_environment(home)
        env["IDIOGRAPH_STAY_OPEN"] = "1"
        log = Path(tmp) / "server.log"
        with open(log, "w", encoding="utf-8") as sink:
            proc = subprocess.Popen([str(server_of(app)), "--serve", "--port", str(port), "--no-browser"], env=env,
                                    stdin=subprocess.DEVNULL, stdout=sink, stderr=subprocess.STDOUT)
            try:
                state, end = None, time.monotonic() + START_WAIT
                while time.monotonic() < end and proc.poll() is None and state is None:
                    state = build_linux.fetch_state(port)
                    if state is None:
                        time.sleep(0.5)
                tail = "\n" + "".join(log.read_text(encoding="utf-8", errors="replace").splitlines(True)[-20:])
                if state is None:
                    raise SystemExit(f"The app's server did not answer /api/server within {START_WAIT} seconds.{tail}")
                got = (state.get("app"), state.get("version"), state.get("build"))
                if got != (APP, version, short):
                    raise SystemExit(f"The app's server answered as {got}, not {(APP, version, short)}.{tail}")
                if build_linux.fetch_state(port, {"op": "quit"}) is None:
                    raise SystemExit(f"The app's server did not take the quit.{tail}")
                proc.wait(timeout=QUIT_WAIT)
                say(f"Served: /api/server answered as {APP} {version} build {short}, and it quit")
            finally:
                if proc.poll() is None:
                    proc.kill()
                    proc.wait()


def size_mb(path: Path) -> float:
    return sum(p.lstat().st_size for p in path.rglob("*") if p.is_file() and not p.is_symlink()) / 1e6


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Build Adam's own Mac copy from main on this Mac, check it and swap it in.")
    ap.add_argument("--dry-run", action="store_true", help="build and check, never swap")
    ap.add_argument("--ref", default="main", help="the commit to build, main's HEAD by default")
    ap.add_argument("--repo", default=str(TOOL), help="the repository to export from, this script's own by default")
    ap.add_argument("--work", help="where the export, the kept build folder and the ready copy go, .verify/macdaily")
    ap.add_argument("--force", action="store_true", help="build and swap even when /Applications has this commit")
    args = ap.parse_args(argv)
    if sys.platform != "darwin":
        raise SystemExit("The Mac copy is built on a Mac.")
    repo = Path(args.repo).expanduser().resolve()
    work = Path(args.work).expanduser().resolve() if args.work else repo / ".verify" / "macdaily"
    work.mkdir(parents=True, exist_ok=True)
    full, short = commit_of(repo, args.ref)
    if not args.dry_run and not args.force and build_in(INSTALLED) == short:
        say(f"DAILY: SAME {short}, already in /Applications, nothing built")
        return 0
    began = time.monotonic()
    src = export(repo, full, work)
    version = json.loads((src / "versions.json").read_text(encoding="utf-8"))[APP]
    say(f"Building {NAME} {version} build {short} from a clean export of {args.ref}")
    done = subprocess.run(build_command(src, work, short, sys.executable), cwd=src)
    if done.returncode != 0:
        say(f"DAILY: FAILED the build of {short}, exit {done.returncode}")
        return 1
    app = work / "dist" / f"{NAME}.app"
    try:
        check(app, version, short)
    except SystemExit as exc:
        say(str(exc))
        say(f"DAILY: FAILED the checks of {short}")
        return 1
    minutes = (time.monotonic() - began) / 60
    say(f"DAILY: BUILT {NAME} {version} build {short} in {minutes:.1f} minutes, {size_mb(app):.0f} MB")
    if args.dry_run:
        say(f"Dry run: {app} stays where it is, and /Applications is not touched")
        return 0
    ready = work / f"ready-{short}"
    for old in work.glob("ready-*"):
        shutil.rmtree(old, ignore_errors=True)
    ready.mkdir(parents=True)
    subprocess.run(["ditto", str(app), str(ready / f"{NAME}.app")], check=True)
    keep = backup_dir(repo)
    say(f"Swapping into /Applications once {NAME} has been closed for 12 seconds, the old copy to {keep}")
    os.execv(str(SWAP), [str(SWAP), str(ready / f"{NAME}.app"), str(keep)])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
