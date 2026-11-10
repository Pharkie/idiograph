"""Area 361: Adam's own Mac copy built on this Mac each day (macdaily, 9 November 2026). On any machine: the commit
a daily build carries, written into the stage by build_mac.py's `--build` and shipped, removed again by a build
without it, and read by `app_identity.build` (a bad or missing file read as none), the server answering the build in
`/api/server` and Home's answer, and a note from Send feedback carrying it after the version, within the collector's
40 characters, and mac_daily.py's clean export holding the commit's tree and nothing uncommitted, its build command the
export's own build_mac.py, unsigned, with the commit, through the shared Mac's queue, the folder that keeps the old
copy never one already there, and the commit read from an installed copy. The build itself, the checks of a real app
and the swap are the script's dry run's and Adam's Mac's."""
from __future__ import annotations

import importlib.util
import json
import shutil
import subprocess
from datetime import date
from pathlib import Path

from . import support
from .support import check, skip


def load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_mac_daily(scratch: Path):
    print("\n361. Adam's own Mac copy built here each day: the build it carries, the export, the command and the swap's folder")
    import app_identity
    import server as server_mod
    build_mac = load("idiograph_361_build_mac", support.source("packaging") / "build_mac.py")
    daily = load("idiograph_361_mac_daily", support.source("packaging") / "mac_daily.py")
    root = scratch / "mac_daily"
    shutil.rmtree(root, ignore_errors=True)
    root.mkdir(parents=True)

    # ── A. the build file, written, shipped, removed and read
    stage = root / "stage"
    stage.mkdir()
    made = build_mac.stage_build(stage, "e45b1af")
    shipped = [d for s, d in build_mac.bundle_inputs(stage)[1] if s.endswith(app_identity.BUILD_FILE)]
    check("361: --build writes build.json naming the commit, and the bundle ships it at its top",
          made is not None and json.loads(made.read_text(encoding="utf-8")) == {"build": "e45b1af"} and shipped == ["."],
          str(shipped))
    check("361: the app reads the commit from the file", app_identity.build(made) == "e45b1af")
    gone = build_mac.stage_build(stage, None)
    still = [s for s, _ in build_mac.bundle_inputs(stage)[1] if s.endswith(app_identity.BUILD_FILE)]
    check("361: a build without --build takes away the file an earlier one left, so a release carries none",
          gone is None and not (stage / app_identity.BUILD_FILE).exists() and not still, str(still))
    try:
        build_mac.stage_build(stage, "e45b1af; rm")
        refused = False
    except SystemExit:
        refused = True
    check("361: --build refuses anything but a short sha", refused and not (stage / app_identity.BUILD_FILE).exists())
    odd = root / "odd.json"
    reads = []
    for text in ('{"build": "../x"}', "not json", '["e45b1af"]', '{"build": ""}'):
        odd.write_text(text, encoding="utf-8")
        reads.append(app_identity.build(odd))
    reads.append(app_identity.build(root / "none.json"))
    check("361: a bad, empty or missing build file reads as no build, and a run from source has none",
          reads == [""] * 5 and app_identity.build() == "", str(reads))

    # ── B. the server says it, and a note carries it
    before = server_mod.BUILD
    try:
        server_mod.BUILD = ""
        plain = server_mod.feedback_payload("x", "", "home", "")["version"]
        server_mod.BUILD = "e45b1af"
        note = server_mod.feedback_payload("x", "", "home", "")["version"]
        state = server_mod.server_state()
    finally:
        server_mod.BUILD = before
    check("361: a note from a daily copy carries the build after the version, within the collector's 40 characters, "
          "and a release's the version alone",
          plain == server_mod.VERSION and note == f"{server_mod.VERSION} build e45b1af" and len(note) <= 40, note)
    check("361: /api/server answers the version and the build",
          state.get("version") == server_mod.VERSION and state.get("build") == "e45b1af", str(state.get("build")))
    home = support.text("apps/idiograph/idiograph_routes.py", "family/server.py")
    check("361: Home's answers carry the build for About",
          '"build": srv.BUILD' in home and '"build": BUILD' in home)

    # ── C. mac_daily.py: the export, the command, the old copy's folder, an installed copy's commit
    if not shutil.which("git"):
        skip("361: the clean export", "no git on this machine")
    else:
        repo = root / "repo"
        repo.mkdir()
        git = lambda *a: subprocess.run(["git", "-C", str(repo), *a], check=True, capture_output=True, text=True,
                                          encoding="utf-8")
        git("init", "-q")
        (repo / "versions.json").write_text('{"idiograph": "9.9.9"}\n', encoding="utf-8")
        (repo / "hive.txt").write_text("frames\n", encoding="utf-8")
        git("add", "-A")
        git("-c", "user.name=Beekeeper", "-c", "user.email=bees@example.org", "commit", "-q", "-m", "hives")
        (repo / "hive.txt").write_text("frames, changed and not committed\n", encoding="utf-8")
        (repo / "smoker.txt").write_text("untracked\n", encoding="utf-8")
        full, short = daily.commit_of(repo, "HEAD")
        work = root / "work"
        (work / "src-0000000").mkdir(parents=True)
        src = daily.export(repo, full, work)
        check("361: the export is the commit's tree alone, nothing uncommitted, and an earlier day's export goes",
              len(short) == 7 and full.startswith(short) and src.name == f"src-{short}"
              and (src / "hive.txt").read_text(encoding="utf-8") == "frames\n" and not (src / "smoker.txt").exists()
              and not (src / ".git").exists() and not (work / "src-0000000").exists(),
              str(sorted(p.name for p in src.iterdir())))
    heavy = root / "heavy"
    heavy.write_text("#!/bin/sh\n", encoding="utf-8")
    cmd = daily.build_command(Path("/x/src-e45b1af"), Path("/x"), "e45b1af", "/py", heavy=heavy)
    bare = daily.build_command(Path("/x/src-e45b1af"), Path("/x"), "e45b1af", "/py", heavy=root / "no-heavy")
    check("361: the build is the export's own build_mac.py, unsigned, naming the commit, through heavy's queue",
          cmd[:3] == [str(heavy), "idiograph", "build"]
          and cmd[3:] == ["/py", str(Path("/x/src-e45b1af") / "packaging" / "build_mac.py"), "--unsigned",
                          "--app", "idiograph", "--build", "e45b1af", "--out", str(Path("/x"))]
          and bare == cmd[3:], str(cmd))
    # the test app beside an earlier Idiograph.app in one --out: the bundle and binary are the test app's own
    macos = root / "macos"
    for n in ("Idiograph", "Idiograph Test"):
        (macos / f"{n}.app" / "Contents" / "MacOS").mkdir(parents=True)
    picked = build_mac.bundle_named(macos, "Idiograph Test")
    try:
        build_mac.bundle_named(macos, "Sift Test")
        missing = False
    except SystemExit:
        missing = True
    check("361: build_mac picks the app built now by its name, not the first .app in the folder, and its binary is named for the product",
          picked.name == "Idiograph Test.app" and missing
          and build_mac.executable_of(picked, "Idiograph Test") == picked / "Contents" / "MacOS" / "Idiograph Test"
          and build_mac.ARCH == "arm64", str(picked))
    day = date(2026, 11, 9)
    first = daily.backup_dir(root, day)
    first.mkdir(parents=True)
    second = daily.backup_dir(root, day)
    second.mkdir()
    third = daily.backup_dir(root, day)
    check("361: the old copy's folder is a new one each time, -2 and -3 on a second and third swap that day",
          (first.name, second.name, third.name) == ("app-before-daily-2026-11-09", "app-before-daily-2026-11-09-2",
                                                    "app-before-daily-2026-11-09-3") and first.parent == root / ".verify",
          str((first.name, second.name, third.name)))
    app = root / "Idiograph.app"
    inner = app / "Contents" / "Resources" / "server" / "_internal"
    inner.mkdir(parents=True)
    released = daily.build_in(app)
    (inner / "build.json").write_text('{"build": "e45b1af"}\n', encoding="utf-8")
    check("361: an installed copy's commit is read from its bundle, none for a release",
          released == "" and daily.build_in(app) == "e45b1af")
