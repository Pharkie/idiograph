"""Area 427: a newer shipped demo is told, never put in place unasked (demostamp, 18 November 2026, Adam: a demo is
never replaced without the researcher's knowledge, "a bar underneath the card on the home screen for any demo that's
changed since they last downloaded it", and Reset demo easy to find).

A demo's version is a hash of the files Reset demo puts back (`make_demo.stamp`), so it changes whenever a shipped
demo's files do. The installed demo keeps the stamp it was last put right from in `.demo-stamp` in its own folder.
Home's library answer (`demo_updates`) names each demo whose installed copy is older, with whether it was worked in, and
changes nothing; Get the update is Reset demo (`api_reset_demo`), which ends by writing the stamp.

What is checked, on a scratch copy of the shipped demo and an installed copy of it: the stamp is the same twice and
changes with one shipped byte or the project file; an installed demo with no stamp and an old Juno workbook is named as
newer and as worked in, and is untouched by asking, any number of times, byte for byte with its modified time; one with no
stamp that is as it ships is stamped and named by none; Reset demo replaces it, writes the stamp, and then none is named;
an up-to-date demo is named by none and left alone; a stamp of an older shipped demo is named again; a user's own
project beside it and a file beside the demo are untouched throughout; a demo not worked in is named with `changed`
false, which is what lets Get the update skip its question; where the demo worked on is the shipped folder none is named
and nothing is written; and Reset demo is in a demo's card menu and the demo's band menu."""
from __future__ import annotations

import hashlib
import shutil
from pathlib import Path

from .support import check


def snapshot(root: Path) -> dict:
    """Every file under a folder by its bytes and modified time."""
    return {p.relative_to(root).as_posix(): (hashlib.sha256(p.read_bytes()).hexdigest(), p.stat().st_mtime_ns)
            for p in sorted(root.rglob("*")) if p.is_file()}


def test_demo_stamp(scratch: Path):
    print("\n427. A newer shipped demo is told on Home and put in place only by Get the update (demostamp)")
    import idiograph_routes as routes
    import make_demo
    import server as server_mod

    base = scratch / "a427"
    shutil.rmtree(base, ignore_errors=True)
    shipped = base / "shipped"
    shutil.copytree(make_demo.DEMO, shipped, ignore=shutil.ignore_patterns("*.m4a", "source", "_Archive", "*.lock",
                                                                           "Juno", "Rowan", "Mabel", "Hollis", "Nell", "Arlo",
                                                                           "Dev", "Ffion", "Glen", "Kemi", "Ros", "Toby"))
    # a staged bundle holds each case's files too, as the pristine copy has them, and the first run's seed_demo copies them
    for root in (shipped, shipped / "ta", shipped / "lipa", shipped / "rta"):
        for name in make_demo.cases_of(root / "pristine"):
            for src in (root / "pristine").rglob(f"{name} - EN & ES*"):
                target = root / name / src.relative_to(root / "pristine")
                if "Working" in src.parts:
                    target = root / name / "Working" / src.name
                else:
                    target = root / name / src.name
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(src, target)
    live = base / "live"
    # as the app's first run and start fill it: what is missing copied, the cases from the pristine copy
    kept = (server_mod.SHIPPED_DEMO, server_mod.DEMO_DIR)
    server_mod.SHIPPED_DEMO, server_mod.DEMO_DIR = shipped, live
    try:
        server_mod.seed_demo(shipped, live)
        routes.fill_demo()
    finally:
        server_mod.SHIPPED_DEMO, server_mod.DEMO_DIR = kept
    juno = live / "Juno" / "Juno - EN & ES.xlsx"
    shipped_juno = shipped / "pristine" / "Juno - EN & ES.xlsx"
    stamp_file = live / make_demo.STAMP_FILE

    one = make_demo.stamp(shipped / "pristine")
    check("427: the stamp is worked out from the shipped files, the same twice",
          bool(one) and one == make_demo.stamp(shipped / "pristine"), one)
    probe = base / "probe"
    shutil.copytree(shipped, probe)
    with open(probe / "pristine" / "Juno - EN & ES.xlsx", "ab") as fh:
        fh.write(b"x")
    check("427: and changes with one shipped byte", make_demo.stamp(probe / "pristine") != one, "")
    probe_project = base / "probe2"
    shutil.copytree(shipped, probe_project)
    held_project = probe_project / server_mod.PROJECT_FILE
    held_project.write_text(held_project.read_text(encoding="utf-8") + " ", encoding="utf-8")
    check("427: the project file's change counts too", make_demo.stamp(probe_project / "pristine") != one, "")
    probe_noise = base / "probe3"
    shutil.copytree(shipped, probe_noise)
    for junk in ("Thumbs.db", "._Juno - EN & ES.xlsx", ".DS_Store", "notes.txt~"):
        (probe_noise / "pristine" / junk).write_bytes(b"junk")
    check("427: Thumbs.db, ._ files, .DS_Store and editor files are passed over", make_demo.stamp(probe_noise / "pristine") == one, "")
    probe_crlf = base / "probe4"
    shutil.copytree(shipped, probe_crlf)
    for f in (probe_crlf / "pristine").rglob("*.json"):
        f.write_bytes(f.read_bytes().replace(b"\r\n", b"\n").replace(b"\n", b"\r\n"))
    pj = probe_crlf / server_mod.PROJECT_FILE
    pj.write_bytes(pj.read_bytes().replace(b"\r\n", b"\n").replace(b"\n", b"\r\n"))
    check("427: a JSON file with Windows line endings reads as the same stamp", make_demo.stamp(probe_crlf / "pristine") == one, "")

    own = base / "own-project"
    (own / "P1 - Ann").mkdir(parents=True)
    (own / "P1 - Ann" / "note.txt").write_text("the researcher's own project", encoding="utf-8")
    beside = base / "beside.txt"
    beside.write_text("a file beside the demo", encoding="utf-8")

    def outside() -> dict:
        return snapshot(own) | {"beside": (hashlib.sha256(beside.read_bytes()).hexdigest(), beside.stat().st_mtime_ns)}

    kept_outside = outside()
    server_mod.SHIPPED_DEMO, server_mod.DEMO_DIR = shipped, live
    try:
        # a first run's copy, as it ships and with no stamp: stamped, and no bar
        check("427: a first run's copy, as it ships, is named by none and stamped, every demo's",
              routes.demo_updates() == {} and make_demo.installed_stamp(live) == one
              and all((live / d / make_demo.STAMP_FILE).is_file() for d in ("ta", "lipa", "rta")), "")
        stamp_file.unlink()

        # an install from before: no stamp, an old Juno workbook worked in
        juno.write_bytes(b"an old Juno workbook")
        before = snapshot(live)
        found = routes.demo_updates()
        routes.demo_updates()
        check("427: an installed demo with no stamp and an old Juno workbook is named as newer and as worked in",
              list(found) == ["demo"] and found["demo"] == {"stamp": one, "changed": True}, str(found))
        check("427: asking changes nothing in it, byte for byte with its modified time", snapshot(live) == before, "")

        # Get the update is Reset demo
        routes.api_reset_demo({})
        check("427: Get the update, Reset demo, puts the shipped Juno in place and writes the stamp",
              juno.read_bytes() == shipped_juno.read_bytes() and make_demo.installed_stamp(live) == one, "")
        after = snapshot(live)
        check("427: then no demo is named, and asking changes nothing", routes.demo_updates() == {} and snapshot(live) == after, "")
        check("427: a user's own project and a file beside the demo are untouched", outside() == kept_outside, "")

        # a newer shipped demo over an installed one nobody touched: named, and not as worked in (the baseline is the
        # installed demo's own, so a changed shipped file is no work of the researcher's)
        mabel_ship = shipped / "pristine" / "Mabel - EN & ES.xlsx"
        mabel_ship.write_bytes(mabel_ship.read_bytes() + b"x")
        new_one = make_demo.stamp(shipped / "pristine")
        found = routes.demo_updates()
        check("427: a shipped file changed over an untouched installed demo is named as newer and not worked in",
              found == {"demo": {"stamp": new_one, "changed": False}}, str(found))
        # the bar's Get the update sends asked: false; with the demo untouched it goes through
        # (a demo worked in since is refused first, below)
        juno.write_bytes(b"worked on")
        found = routes.demo_updates()
        check("427: and as worked in once the researcher has changed the demo", found.get("demo", {}).get("changed") is True, str(found))
        refused = routes.api_reset_demo({"asked": False})
        check("427: a reset sent as not asked is refused whole when the demo was worked in since, nothing replaced",
              refused.get("changed") is True and refused.get("reset") is False and juno.read_bytes() == b"worked on", str(refused))
        routes.api_reset_demo({})
        check("427: Reset demo asked ends the bar, the shipped Juno in place and the new stamp held",
              routes.demo_updates() == {} and juno.read_bytes() == shipped_juno.read_bytes()
              and make_demo.installed_stamp(live) == new_one, "")
        mabel_ship.write_bytes(mabel_ship.read_bytes() + b"y")
        routes.api_reset_demo({"asked": False})
        check("427: a reset sent as not asked goes through when the demo is as it was put right",
              routes.demo_updates() == {} and make_demo.installed_stamp(live) == make_demo.stamp(shipped / "pristine"), "")
        # a stamp file with no baseline, as before the baselines, counts as worked in
        stamp_file.write_text("an older shipped demo\n", encoding="utf-8")
        found = routes.demo_updates()
        check("427: an install with a stamp and no baseline counts as worked in, so it is asked",
              found.get("demo", {}).get("changed") is True, str(found))

        # where the demo worked on is the shipped folder, as from the repo
        server_mod.DEMO_DIR = shipped
        kept_shipped = snapshot(shipped)
        check("427: where the demo worked on is the shipped folder none is named and nothing is written",
              routes.demo_updates() == {} and snapshot(shipped) == kept_shipped, "")
    finally:
        server_mod.SHIPPED_DEMO, server_mod.DEMO_DIR = kept

    # Reset demo is where it can be found: in a demo's card menu and the band's menu, and on the demo's page
    import subprocess
    script = base / "menu-427.js"
    js = (Path(routes.__file__).parent / "static" / "distil.js").read_text(encoding="utf-8")
    start = js.index("function homeMenuItems(")
    script.write_text(js[start:js.index("\n}\n", start) + 3] + "\nconst r = homeMenuItems({ demo: true }, {});"
                      "\nconst o = homeMenuItems({ id: 'x' }, { window: true });"
                      "\nconsole.log(JSON.stringify([r, o.includes('reset')]));\n", encoding="utf-8")
    ran = subprocess.run(["node", str(script)], capture_output=True, text=True, encoding="utf-8", timeout=60)
    check("427: Reset demo is in a demo's menu, under Project settings, and in no project's",
          ran.stdout.strip() == '[["settings","reset"],false]', ran.stdout + ran.stderr)
