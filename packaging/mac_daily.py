#!/usr/bin/env python3
"""Adam's own Mac copy of Idiograph, built each day from main and swapped into /Applications (macdaily,
9 November 2026, Adam, 9 November about 13:20 by dialog: a GitHub release once a week, on Mondays, and his own
copy each day). Since 16 November 2026 (macactions, Adam: "switch it") the build is GitHub Actions' by
default, free now the repository is public and kind to a Mac that is shared and loaded; the build on this Mac
is `--local`.

    python3 packaging/mac_daily.py              # Actions builds pushed main's Mac app, check it, swap it in
    python3 packaging/mac_daily.py --dry-run    # the same, never swap
    python3 packaging/mac_daily.py --local      # build on this Mac instead (Actions down), from `--ref`
    python3 packaging/mac_daily.py --ref <sha>  # --local alone: another commit than main's HEAD

The Actions way, before the checks: A. refuse unless local main is origin/main, since the build must be of
what is pushed. B. dispatch `.github/workflows/windows-installer.yml` by hand with `mac_app` true (and the
Windows installer off, the suite alone running beside it), print the run's URL, wait on the Mac job every 30
seconds and say every ending (failed, cancelled, timed out after 40 minutes). C. `gh run download` of the
artifact `Idiograph-Mac` into `.verify/macdaily/actions`, the app unpacked from its `.app.tar.gz` into
`.verify/macdaily/dist`, and any quarantine mark taken off it (a download by `gh` carries none, but the check
is made and the mark removed if it ever does). The workflow passes `--build <sha>` on a run by hand, so the app
carries build.json, which must be the commit asked for, on both ways. Every gh call names the origin repository,
and the run is checked (sha, branch main, by hand, made after the dispatch) before its artifact is taken.

The local way's steps, each said in one line:

1. A clean export of the commit, `git archive` of `--ref` (main by default) into `.verify/macdaily/src-<sha>`,
   never the working tree, so what is built is what main holds and nothing uncommitted reaches the app.
2. The build, as the workflow's mac-app job makes it: the export's own `packaging/build_mac.py --unsigned`,
   the same pins, the frozen server, Tauri's bundle at the pinned CLI, arm64 alone, signed ad hoc as the
   job's and Adam's installed copy are, with `--build <sha>` so the app carries `build.json` naming the
   commit, which About shows after the version ("Version 0.9.23, build e45b1af") and a note from Send
   feedback carries. The version is main's own, versions.json's, the week's release's number. The build
   folder, `.verify/macdaily/build`, is kept from day to day, so its venv and cargo's work are made once. It runs through `~/.claude/bin/heavy idiograph build`, the shared Mac's queue.
3. The checks (both ways): the app, its server and its typesetter arm64 alone, the bundle's version versions.json's, `codesign
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
import re
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
    carried = build_in(app)
    if carried and carried != short:
        raise SystemExit(f"The app carries build {carried}, not {short}.")
    if not carried:
        raise SystemExit(f"The app carries build none, not {short}.")
    done = subprocess.run(["codesign", "--verify", "--deep", "--strict", str(app)], capture_output=True, text=True,
                          encoding="utf-8", errors="replace")
    if done.returncode != 0:
        raise SystemExit(f"codesign refuses the app:\n{done.stderr.strip()}")
    done = subprocess.run([str(server_of(app)), "cli", "--help"], capture_output=True, text=True, encoding="utf-8",
                          errors="replace", timeout=120)
    if done.returncode != 0:
        raise SystemExit(f"The app's command line did not answer --help:\n{(done.stdout + done.stderr)[-2000:]}")
    made = typeset_helper.check(typesetter_of(app), typeset_helper.fonts_in(server_of(app).parent))
    say(f"Checked: arm64, version {shown}, build {carried}, codesign verifies, cli --help answers, "
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
                say(f"Served: /api/server answered as {APP} {version} build {state.get('build') or 'none'}, and it quit")
            finally:
                if proc.poll() is None:
                    proc.kill()
                    proc.wait()


# ── the Actions way (macactions, 16 November 2026)
WORKFLOW = "windows-installer.yml"
ARTIFACT = f"{NAME}-Mac"
JOB = "mac-app"
POLL = 30
TIMEOUT = 40 * 60


REPO = {"name": "Pharkie/idiograph", "dir": str(TOOL)}


def repo_name(repo: Path) -> str:
    """owner/name of the origin remote (the checkout also has a `history` remote), for every gh call's -R."""
    url = git(repo, "remote", "get-url", "origin")
    m = re.search(r"github\.com[:/]([^/]+/[^/]+?)(?:\.git)?/?$", url)
    if not m:
        raise SystemExit(f"origin ({url}) is not a GitHub repository.")
    return m.group(1)


def gh(*args: str, check: bool = True) -> subprocess.CompletedProcess:
    return subprocess.run(["gh", *args, "-R", REPO["name"]], check=check, capture_output=True, text=True,
                          encoding="utf-8", errors="replace", cwd=REPO["dir"])


def pushed_commit(repo: Path, ref: str) -> tuple[str, str]:
    """The commit of origin/main, which must also be local main's: the build is of what is pushed."""
    if ref != "main":
        raise SystemExit("Actions builds pushed main alone. Use --local for another commit.")
    fetched = subprocess.run(["git", "-C", str(repo), "fetch", "origin", "main", "--quiet"], capture_output=True,
                             text=True, encoding="utf-8", errors="replace")
    if fetched.returncode != 0:
        raise SystemExit(f"Could not fetch origin: {fetched.stderr.strip()}")
    local, short = commit_of(repo, "main")
    remote, _ = commit_of(repo, "origin/main")
    if local != remote:
        raise SystemExit(f"Local main ({local[:7]}) is not origin/main ({remote[:7]}), and the build must be of "
                         f"what is pushed. Push main, or use --local.")
    return local, short


def runs(full: str) -> list[dict]:
    done = gh("run", "list", "--workflow", WORKFLOW, "--event", "workflow_dispatch", "--commit", full,
              "--json", "databaseId,url", "--limit", "20", check=False)
    if done.returncode != 0:
        raise SystemExit(f"gh run list failed: {done.stderr.strip()}")
    try:
        return json.loads(done.stdout or "[]")
    except ValueError as exc:
        raise SystemExit(f"gh run list answered no JSON: {exc}")


def dispatch(full: str) -> tuple[str, str, str]:
    """Start the workflow by hand on main (mac_app on, the Windows installer off), and answer the new run's id,
    address and a time just before the call: the first run of that commit not there before the call."""
    before = {r["databaseId"] for r in runs(full)}
    began = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(time.time() - 60))
    sent = gh("workflow", "run", WORKFLOW, "--ref", "main", "-f", "mac_app=true", "-f", "installer=false", check=False)
    if sent.returncode != 0:
        raise SystemExit(f"Dispatch failed: {sent.stderr.strip()}")
    end = time.monotonic() + 120
    while time.monotonic() < end:
        time.sleep(5)
        for r in runs(full):
            if r["databaseId"] not in before:
                return str(r["databaseId"]), r["url"], began
    raise SystemExit("The dispatched run did not show up within two minutes.")


def verify_run(run_id: str, full: str, since: str) -> None:
    """The run is the one asked for: of main's full sha, on main, by hand, made after the dispatch."""
    done = gh("run", "view", run_id, "--json", "headSha,headBranch,event,createdAt", check=False)
    try:
        info = json.loads(done.stdout)
    except ValueError:
        raise SystemExit(f"gh run view of {run_id} failed: {done.stderr.strip()}")
    want = (full, "main", "workflow_dispatch")
    got = (info.get("headSha"), info.get("headBranch"), info.get("event"))
    if got != want or not str(info.get("createdAt", "")) >= since:
        raise SystemExit(f"Run {run_id} is not the dispatched one: {got}, created {info.get('createdAt')}, "
                         f"wanted {want} after {since}.")


def wait_for(run_id: str, poll: int = POLL, limit: int = TIMEOUT) -> None:
    """Wait for the run's Mac job, every `poll` seconds, up to `limit`. Returns on success, and says how it
    ended otherwise: failed, cancelled, skipped, or timed out."""
    end = time.monotonic() + limit
    last = ""
    while True:
        done = gh("run", "view", run_id, "--json", "status,conclusion,jobs", check=False)
        try:
            info = json.loads(done.stdout)
        except ValueError:
            info = None
        if info is not None:
            job = next((j for j in info.get("jobs", []) if j.get("name") == JOB), None)
            state = f"{job['status']}/{job.get('conclusion') or '-'}" if job else f"run {info['status']}, no {JOB} job yet"
            if state != last:
                say(f"  {time.strftime('%H:%M:%S')} {state}")
                last = state
            if job and job["status"] == "completed":
                if job["conclusion"] == "success":
                    return
                raise SystemExit(f"The Mac job ended {job['conclusion']}.")
            if info["status"] == "completed" and not job:
                raise SystemExit(f"The run ended {info.get('conclusion')} with no {JOB} job.")
        if time.monotonic() > end:
            raise SystemExit(f"Timed out after {limit // 60} minutes waiting for the Mac job.")
        time.sleep(poll)


def marks_on(app: Path) -> list[str]:
    """Quarantine and provenance marks anywhere in the app."""
    out = subprocess.run(["xattr", "-rl", str(app)], capture_output=True, text=True, encoding="utf-8",
                         errors="replace").stdout
    return sorted(set(re.findall(r"com\.apple\.(?:quarantine|provenance)", out)))


def gatekeeper(app: Path) -> str:
    done = subprocess.run(["spctl", "--assess", "--type", "execute", "-v", str(app)], capture_output=True, text=True,
                          encoding="utf-8", errors="replace")
    return (done.stdout + done.stderr).strip().replace(str(app), "<app>").replace("\n", " | ")


def fetch_from_actions(full: str, work: Path) -> Path:
    """Dispatch, wait, download and unpack: the app."""
    run_id, url, since = dispatch(full)
    say(f"Run {run_id}: {url}")
    verify_run(run_id, full, since)
    began = time.monotonic()
    wait_for(run_id)
    say(f"The Mac job succeeded after {(time.monotonic() - began) / 60:.1f} minutes")
    got = work / "actions"
    shutil.rmtree(got, ignore_errors=True)
    got.mkdir(parents=True)
    done = gh("run", "download", run_id, "-n", ARTIFACT, "-D", str(got), check=False)
    if done.returncode != 0:
        raise SystemExit(f"Download of {ARTIFACT} failed: {done.stderr.strip()}")
    tarball = got / f"{NAME}.app.tar.gz"
    if not tarball.is_file():
        raise SystemExit(f"{ARTIFACT} holds no {tarball.name}: {sorted(p.name for p in got.iterdir())}")
    say(f"Downloaded {ARTIFACT}: " + ", ".join(f"{p.name} {p.stat().st_size / 1e6:.1f} MB" for p in sorted(got.iterdir())))
    dist = work / "dist"
    dist.mkdir(exist_ok=True)
    app = dist / f"{NAME}.app"
    shutil.rmtree(app, ignore_errors=True)
    subprocess.run(["tar", "-xzf", str(tarball), "-C", str(dist)], check=True)
    if not app.is_dir():
        raise SystemExit(f"{tarball.name} did not unpack to {app.name}: {sorted(p.name for p in dist.iterdir())}")
    # quarantine is what would make Gatekeeper ask, and is taken off. provenance is macOS's own mark on every app
    # this Mac makes or opens (the local build and the installed copy carry it too, and it cannot be removed)
    if "com.apple.quarantine" in marks_on(app):
        say("The download carries com.apple.quarantine, taken off")
        subprocess.run(["xattr", "-dr", "com.apple.quarantine", str(app)], check=False)
    say(f"Extended attributes of the downloaded app: {', '.join(marks_on(app)) or 'none'} "
        f"(provenance is on the local build and /Applications too)")
    say(f"Gatekeeper on it: {gatekeeper(app)}")
    return app


def size_mb(path: Path) -> float:
    return sum(p.lstat().st_size for p in path.rglob("*") if p.is_file() and not p.is_symlink()) / 1e6


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Build Adam's own Mac copy from main on this Mac, check it and swap it in.")
    ap.add_argument("--dry-run", action="store_true", help="build and check, never swap")
    ap.add_argument("--local", action="store_true", help="build on this Mac, not on GitHub Actions")
    ap.add_argument("--ref", default="main", help="the commit to build, main's HEAD by default (--local for any other)")
    ap.add_argument("--repo", default=str(TOOL), help="the repository to export from, this script's own by default")
    ap.add_argument("--work", help="where the export, the kept build folder and the ready copy go, .verify/macdaily")
    ap.add_argument("--force", action="store_true", help="build and swap even when /Applications has this commit")
    args = ap.parse_args(argv)
    if sys.platform != "darwin":
        raise SystemExit("The Mac copy is built on a Mac.")
    repo = Path(args.repo).expanduser().resolve()
    work = Path(args.work).expanduser().resolve() if args.work else repo / ".verify" / "macdaily"
    work.mkdir(parents=True, exist_ok=True)
    if not args.local:
        REPO["dir"] = str(repo)
        try:
            REPO["name"] = repo_name(repo)
        except SystemExit as exc:
            say(str(exc))
            say("DAILY: REFUSED")
            return 1
    try:
        full, short = commit_of(repo, args.ref) if args.local else pushed_commit(repo, args.ref)
    except SystemExit as exc:
        say(str(exc))
        say("DAILY: REFUSED")
        return 1
    if not args.dry_run and not args.force and build_in(INSTALLED) == short:
        say(f"DAILY: SAME {short}, already in /Applications, nothing built")
        return 0
    began = time.monotonic()
    # the version is the commit's own, read from git, never from a working tree
    version = json.loads(git(repo, "show", f"{full}:versions.json"))[APP]
    if args.local:
        src = export(repo, full, work)
        say(f"Building {NAME} {version} build {short} from a clean export of {args.ref}")
        done = subprocess.run(build_command(src, work, short, sys.executable), cwd=src)
        if done.returncode != 0:
            say(f"DAILY: FAILED the build of {short}, exit {done.returncode}")
            return 1
        app = work / "dist" / f"{NAME}.app"
    else:
        say(f"Building {NAME} {version} build {short} on GitHub Actions")
        try:
            app = fetch_from_actions(full, work)
        except SystemExit as exc:
            say(str(exc))
            say(f"DAILY: FAILED the Actions build of {short}")
            return 1
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
