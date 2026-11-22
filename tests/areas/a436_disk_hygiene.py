"""Area 436: the tooling cleans up after itself (diskhygiene, 20 November 2026).

Idiograph's runs once filled a Mac's disk: headless browsers left running with their profile folders, thousands of
temporary folders and lock files, and over 100 GB of builders' output in `.verify/`. This checks the three things that
stop it, each on made-up files in a scratch folder: `support.sweep_stale` takes this user's `idiograph-tests-*` and
`idiograph-motion-*` folders older than 6 hours and no younger one, none whose run is alive, and never an agents' lock;
`support.run_browser` ends a browser that outlasts its time with its helpers, and it and `chrome.mjs` kill only the helpers
listed while the browser lived and only while each is still the process listed (diskfix); and
`packaging/verify_prune.py` plans only build trees and big files in `wip-*` folders and all but the newest three
copies of the app, deleting nothing without `--commit`, and never a patch, a note, anything touched in the last 3 days or `keep`.
Every start of Chrome in the repo (the suite's `--headless` commands, chrome.mjs's `spawn(CHROME`) passes `--use-mock-keychain`
and `--password-store=basic` (mockkeychain, 22 November 2026), or macOS shows "Keychain Not Found" on the screen."""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path

from . import support
from .support import check, skip


def _old(path: Path, days: float):
    when = time.time() - days * 86400
    os.utime(path, (when, when))


def _alive(pid: int) -> bool:
    return support.pid_alive(pid)


# The node half: chrome.mjs's watchBelow and endListed on made-up children, never a real browser. It prints one line
# of JSON: the orphan's pid and what end() killed, then what each wrong listing of an unrelated sleep killed
NODE_BELOW = r"""
import { spawn } from 'node:child_process';
import { pathToFileURL } from 'node:url';
const { watchBelow, endListed, processes } = await import(pathToFileURL(process.argv[2]).href);
const exited = (p) => new Promise((ok) => (p.exitCode !== null || p.signalCode !== null) ? ok() : p.on('exit', ok));
const out = {};
// a helper listed while its browser lives, then handed to pid 1 when the browser ends
const b = spawn('sh', ['-c', 'sleep 77 >/dev/null 2>&1 & echo $!; sleep 1.2'], { stdio: ['ignore', 'pipe', 'ignore'] });
let said = ''; b.stdout.on('data', (d) => { said += d; });
const w = watchBelow(b);
await exited(b);
out.orphan = Number(said.trim());
out.killed = w.end();
// an unrelated sleep, and listings of it that no longer match: another start time, another parent, a browser ended
// before it was listed
const s = spawn('sleep', ['30'], { stdio: 'ignore' });
await new Promise((ok) => setTimeout(ok, 200));
out.sleep = s.pid;
out.wrongStart = endListed(new Map([[s.pid, { ppid: process.pid, start: 'Thu Jan 1 00:00:00 1970' }]]));
const real = processes().get(s.pid);
out.wrongParent = endListed(new Map([[s.pid, { ppid: real.ppid + 999999, start: real.start }]]));
const quick = spawn('sh', ['-c', 'exit 0'], { stdio: 'ignore' });
const wq = watchBelow(quick);
await exited(quick);
out.quick = wq.end();
out.aliveAfter = (() => { try { process.kill(s.pid, 0); return true; } catch { return false; } })();
out.control = endListed(new Map([[s.pid, real]]));
await exited(s);
console.log(JSON.stringify(out));
"""


def _helpers_listed_while_alive(root: Path):
    """diskfix (20 November 2026): helpers are listed while the browser lives and killed only while each is still the
    process listed, in Python (`support.run_browser`) and in node (`chrome.mjs`)."""
    # a helper listed while the browser lives and handed to pid 1 when it ends, holding the output open
    began = time.monotonic()
    done = support.run_browser(["sh", "-c", "sleep 77 & echo $!; sleep 1.2"], timeout=30)
    orphan = int(done.stdout.split()[0]) if done.stdout.split() else 0
    time.sleep(0.3)
    gone = bool(orphan) and not _alive(orphan)
    check("436: a helper listed while the browser lived is killed after the browser ends and leaves it to pid 1, "
          "and the run returns without waiting out its time",
          done.returncode == 0 and gone and time.monotonic() - began < 15, f"{done.returncode} {orphan} {gone}")
    if orphan and not gone:
        os.kill(orphan, 9)

    # an unrelated process whose number a listing names but that is not the process listed is never killed
    other = subprocess.Popen(["sleep", "30"])
    try:
        time.sleep(0.2)
        ppid, _, start = support.processes()[other.pid]
        spared = (support.end_listed({other.pid: (ppid, "Thu Jan 1 00:00:00 1970")}),
                  support.end_listed({other.pid: (ppid + 999999, start)}))
        quick = support.run_browser(["sh", "-c", "exit 0"], timeout=30)
        check("436: a process listed under another start time or another parent is left alive, and so is everything "
              "for a browser that ended before it was listed",
              spared == ([], []) and quick.returncode == 0 and _alive(other.pid) and other.poll() is None, str(spared))
        check("436: the same process, listed as it is, is killed (the guard's control)",
              support.end_listed({other.pid: (ppid, start)}) == [other.pid], "")
    finally:
        other.kill()
        other.wait()

    node = shutil.which("node")
    if not node:
        return skip("436: helpers listed while the browser lives, in node", "no node on this machine")
    script = root / "below.mjs"
    script.write_text(NODE_BELOW, encoding="utf-8")
    ran = subprocess.run([node, str(script), str(support.source("packaging/motion/chrome.mjs"))],
                         capture_output=True, text=True, encoding="utf-8", timeout=60)
    try:
        said = json.loads(ran.stdout.strip().splitlines()[-1])
    except (ValueError, IndexError):
        said = {}
    orphan = said.get("orphan") or 0
    time.sleep(0.3)
    check("436: in node, a helper listed while the browser lived is killed after the browser ends",
          bool(orphan) and said.get("killed") == [orphan] and not _alive(orphan), (ran.stderr or str(said))[-300:])
    if orphan and _alive(orphan):
        os.kill(orphan, 9)
    check("436: in node, an unrelated process under another start time, or for a browser that ended before it was "
          "listed, is left alive",
          said.get("wrongStart") == [] and said.get("wrongParent") == [] and said.get("quick") == []
          and said.get("aliveAfter") is True, str(said))
    check("436: in node, the same process, listed as it is, is killed (the guard's control)",
          bool(said.get("sleep")) and said.get("control") == [said.get("sleep")], str(said))


def _chrome_launches_lack_keychain_flag() -> tuple[int, list]:
    """Every start of Chrome in the repo, a `"--headless"` command in Python or the `spawn(CHROME` of the motion tools'
    chrome.mjs, with the lines it runs on, and those that do not carry --use-mock-keychain and --password-store=basic
    (a fresh profile without them makes macOS show "Keychain Not Found" on the screen at every run)."""
    seen, bad = 0, []
    for folder in ("tests", "packaging", "family", "apps"):
        for path in sorted(support.source(folder).rglob("*")):
            if path.suffix not in (".py", ".mjs") or any(p in ("node_modules", ".venv", "vendor") for p in path.parts):
                continue
            lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
            for i, line in enumerate(lines):
                if path.name == "a436_disk_hygiene.py":
                    continue
                if ('"--headless"' in line and path.suffix == ".py") or ("spawn(CHROME" in line and path.suffix == ".mjs"):
                    seen += 1
                    near = "\n".join(lines[i:i + 8])
                    mock = "--use-mock-keychain" in near or "KEYCHAIN_FLAGS" in near
                    store = "--password-store=basic" in near or "KEYCHAIN_FLAGS" in near
                    if not (mock and store):
                        bad.append(f"{path.name}:{i + 1}")
    return seen, bad


def test_disk_hygiene():
    print("\n436. The tooling removes its own temporary folders, locks and browsers, and .verify can be pruned (diskhygiene)")
    seen, bad = _chrome_launches_lack_keychain_flag()
    check("436: every start of Chrome in the repo passes --use-mock-keychain and --password-store=basic, so macOS never "
          "shows \"Keychain Not Found\"", seen >= 10 and not bad, f"{seen} launches, without: {bad}")
    with tempfile.TemporaryDirectory(prefix="idiograph-436-") as tmp:
        root = Path(tmp)

        # the sweep
        tdir = root / "tmpdir"
        tdir.mkdir()
        for name in ("idiograph-tests-old", "idiograph-tests-new", "idiograph-motion-old", "other-old"):
            (tdir / name).mkdir()
            (tdir / name / "x").write_text("x", encoding="utf-8")
        for name in ("idiograph-agents-aa.idiograph.lock", "idiograph-agents-bb.idiograph.lock", "idiograph-agents-keep.txt"):
            (tdir / name).write_text("", encoding="utf-8")
        for name in ("idiograph-tests-old", "idiograph-motion-old", "other-old", "idiograph-agents-aa.idiograph.lock",
                     "idiograph-agents-keep.txt"):
            _old(tdir / name, 0.5)
        (tdir / "idiograph-tests-live").mkdir()
        (tdir / "idiograph-tests-live" / ".pid").write_text(str(os.getpid()), encoding="utf-8")
        _old(tdir / "idiograph-tests-live", 0.5)
        gone = support.sweep_stale(tdir)
        check("436: the sweep takes the old idiograph-tests and idiograph-motion folders, not one whose run is alive",
              sorted(gone) == ["idiograph-motion-old", "idiograph-tests-old"], str(gone))
        left = sorted(p.name for p in tdir.iterdir())
        check("436: it leaves a younger run's folder, a live run's, another name and every agents' lock, old or not",
              left == ["idiograph-agents-aa.idiograph.lock", "idiograph-agents-bb.idiograph.lock", "idiograph-agents-keep.txt",
                       "idiograph-tests-live", "idiograph-tests-new", "other-old"],
              str(left))

        # a run's scratch folder goes with the run
        seen = {}
        try:
            with support.run_scratch("idiograph-436-run-") as scratch:
                seen["inside"] = Path(tempfile.gettempdir()).is_relative_to(scratch)
                seen["path"] = scratch
                (scratch / "tmp" / "idiograph-agents-zz.idiograph.lock").write_text("", encoding="utf-8")
                raise RuntimeError("a failing run")
        except RuntimeError:
            pass
        check("436: a suite run's scratch folder holds the temp folder for the run and is gone after a failed one",
              seen.get("inside") is True and not seen["path"].exists(), str(seen))

        # a browser that outlasts its time, with a helper, is ended whole
        marker = root / "helper.pid"
        code = ("import subprocess,sys,time\n"
                f"h=subprocess.Popen([sys.executable,'-c','import time;time.sleep(60)'])\n"
                f"open({str(marker)!r},'w').write(str(h.pid))\n"
                "time.sleep(60)\n")
        began = time.monotonic()
        timed_out = False
        try:
            support.run_browser([sys.executable, "-c", code], timeout=3)
        except subprocess.TimeoutExpired:
            timed_out = True
        helper = int(marker.read_text(encoding="utf-8")) if marker.exists() else 0
        time.sleep(0.5)
        alive = False
        if helper:
            alive = support.pid_alive(helper)
        check("436: a browser that outlasts its time raises the timeout and its helper process is ended with it",
              timed_out and helper and not alive and time.monotonic() - began < 30, f"{timed_out} {helper} {alive}")
        if helper and alive:
            support.kill_pid(helper)

        if os.name != "nt" and support.processes():
            _helpers_listed_while_alive(root)
        else:
            skip("436: helpers listed while the browser lives", "no ps on this machine")

        # the prune
        verify = root / "dot-verify"
        wip = verify / "wip-01Nov26" / "b1"
        (wip / "target" / "debug").mkdir(parents=True)
        (wip / "target" / "debug" / "bin").write_bytes(b"0" * 1000)
        (wip / "notes.md").write_text("notes", encoding="utf-8")
        # a folder of a builder's own that is only called build, a real build and a real browser profile
        (wip / "build").mkdir()
        (wip / "build" / "brief.md").write_text("a brief", encoding="utf-8")
        (wip / "app").mkdir()
        (wip / "app" / "package.json").write_text("{}", encoding="utf-8")
        (wip / "app" / "build").mkdir()
        (wip / "app" / "build" / "out.js").write_text("x", encoding="utf-8")
        (wip / "profile-shots").mkdir()
        (wip / "profile-shots" / "a.png").write_bytes(b"0" * 100)
        (wip / "profile-run").mkdir()
        (wip / "profile-run" / "Local State").write_text("{}", encoding="utf-8")
        (wip / "a.patch").write_bytes(b"0" * (21 * 1024 * 1024))
        (wip / "big.bin").write_bytes(b"0" * (21 * 1024 * 1024))
        (wip / "shot.png").write_bytes(b"0" * 1000)
        for path in [wip / "target" / "debug" / "bin", wip / "target" / "debug", wip / "target", wip / "notes.md",
                     wip / "build" / "brief.md", wip / "build", wip / "app" / "package.json", wip / "app" / "build" / "out.js",
                     wip / "app" / "build", wip / "app", wip / "profile-shots" / "a.png", wip / "profile-shots",
                     wip / "profile-run" / "Local State", wip / "profile-run",
                     wip / "a.patch", wip / "big.bin", wip / "shot.png"]:
            _old(path, 10)
        for i in range(5):
            copy = verify / f"app-before-v0.9.{i}"
            copy.mkdir(parents=True)
            (copy / "f").write_text("x", encoding="utf-8")
            _old(copy / "f", 10 + 5 - i)
            _old(copy, 10 + 5 - i)
        (verify / "keep").mkdir()
        (verify / "history.log").write_text("x", encoding="utf-8")
        _old(verify / "history.log", 30)
        sys.path.insert(0, str(support.source("packaging")))
        try:
            import verify_prune
            # everything here was made a moment ago, and a copy that keeps its old mtime is still new by its change
            # and birth times, so at the real time nothing is old enough; --days=-1 makes the cutoff a day ahead
            check("436: nothing touched in the last 3 days is planned, an old mtime on a fresh copy not hiding it",
                  verify_prune.plan(verify) == [], str(verify_prune.plan(verify))[:200])
            items = verify_prune.plan(verify, days=-1)
            names = sorted(p.relative_to(verify).as_posix() for _, p, _ in items)
            check("436: the prune plans the old build tree, the big file that is no patch and the two oldest app copies, "
                  "and a folder only called build or profile is no build tree, nothing else", names == ["app-before-v0.9.0", "app-before-v0.9.1", "wip-01Nov26/b1/app/build",
                                                "wip-01Nov26/b1/big.bin", "wip-01Nov26/b1/profile-run",
                                                "wip-01Nov26/b1/target"], str(names))
            before = sorted(p.relative_to(verify).as_posix() for p in verify.rglob("*"))
            verify_prune.main(["--verify-dir", str(verify), "--days=-1"])
            check("436: a dry run deletes nothing", before == sorted(p.relative_to(verify).as_posix() for p in verify.rglob("*")), "")
            verify_prune.main(["--verify-dir", str(verify), "--days=-1", "--commit"])
            after = sorted(p.relative_to(verify).as_posix() for p in verify.rglob("*"))
            check("436: --commit deletes what was planned, and the patch, note, picture, keep folder "
                  "and gate's log stay",
                  not any(n in after for n in ("wip-01Nov26/b1/target", "wip-01Nov26/b1/big.bin", "app-before-v0.9.0"))
                  and all(n in after for n in ("wip-01Nov26/b1/a.patch", "wip-01Nov26/b1/notes.md", "wip-01Nov26/b1/shot.png",
                                               "wip-01Nov26/b1/build/brief.md", "wip-01Nov26/b1/profile-shots/a.png",
                                               "keep", "history.log", "app-before-v0.9.2",
                                               "app-before-v0.9.4")), str(after))
        finally:
            sys.path.remove(str(support.source("packaging")))
