"""Two faults "siftapp" found in Sift on 23 October 2026, mended the same day. A drop refused because
another writer held a run's screening lock had already taken away that run's screening log, so a run
and a drop now take the run's lock, and the lock of the run it follows, before they remove or write
anything in its folder. And Sift's and Trace's first start copied Idiograph's demo participants into
their own data folder, which they have no use for. A frozen Sift still did, since the server's start ran
every app's start hook, Idiograph's filling its demo wherever the running app's demo folder was, so a run
now starts only the hooks of the apps it serves (starthook, the same day)."""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import os
import shutil
from pathlib import Path

from . import support
from .support import check, refusal_of


def test_sift_fixes(scratch):
    print("\n256. A run or a drop refused BUSY leaves its run folder as it was, and Sift's and Trace's first starts "
          "leave Idiograph's demo where it is")
    import locks
    import server as server_mod
    import sift
    import sift_search as ss

    base = scratch / "sift-fixes-256"
    shutil.rmtree(base, ignore_errors=True)
    base.mkdir(parents=True)
    sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()
    shas = lambda folder: {p.relative_to(folder).as_posix(): sha(p) for p in sorted(Path(folder).rglob("*")) if p.is_file()}

    # ── 1. an invented review of kite flying, its records with no DOI, so nothing is asked of OpenAlex
    kept_clock, kept_env, kept_runner = ss.CLOCK, os.environ.pop(ss.STUB_ENV, None), ss.RUNNER
    ss.CLOCK = lambda: dt.date(2031, 5, 6)
    # no key in the keychain, so nothing asks the real `security` tool
    ss.RUNNER = lambda argv, **_: ss.Done(44, "\n")
    ctx = lambda: ss.Context(base={s: "http://127.0.0.1:9/" for s in ss.ENDPOINTS}, pause=lambda s: None)
    ris = lambda *titles: "".join(f"TY  - JOUR\nTI  - {t}\nPY  - 2020\nAB  - An invented abstract on kites.\nER  - \n\n"
                                  for t in titles).encode("utf-8")
    try:
        review = base / "kite review"
        review.mkdir()
        ss.save(review, {"databases": ["psycinfo"], "blocks": [{"name": "Kites", "terms": ["kite*"]}]})
        ss.register(review)
        d1, d2, d3 = "2031-05-01", "2031-05-02", "2031-05-03"
        ss.take_export(review, "psycinfo", ris("Kites over the downs", "Line and wind"), "p.ris", day=d1, ctx=ctx())
        f1 = review / "runs" / d1
        sift.decide(f1, "R001", "ta", "include")
        # a later run that follows the first, its screening carried from the drop, its log the carry's
        ss.run(review, day=d2, ctx=ctx(), follows=d1)
        ss.take_export(review, "psycinfo", ris("Kites over the downs", "A box kite in March"), "p.ris", day=d2, ctx=ctx())
        f2 = review / "runs" / d2
        check("256: the later run holds the carry's screening log and is not begun, so a drop may write it afresh",
              (f2 / sift.LOG_NAME).is_file() and ss.begun(f2) == "", ss.begun(f2))

        before2, before1 = shas(f2), shas(f1)
        again = ris("Kites over the downs", "A box kite in March", "Tails and bridles")
        with locks.held(sift.lock_path(f2)):
            own = refusal_of(lambda: ss.take_export(review, "psycinfo", again, "p.ris", day=d2, ctx=ctx(), wait=0.2))
        check("256: a drop refused BUSY while another writer holds the run's screening lock leaves every file of the "
              "run folder byte for byte as it was, its screening log among them",
              own == locks.BUSY and shas(f2) == before2 and shas(f1) == before1, own[:80])
        with locks.held(sift.lock_path(f1)):
            followed = refusal_of(lambda: ss.take_export(review, "psycinfo", again, "p.ris", day=d2, ctx=ctx(), wait=0.2))
        check("256: and one refused BUSY on the lock of the run it follows does the same",
              followed == locks.BUSY and shas(f2) == before2 and shas(f1) == before1, followed[:80])

        took = ss.take_export(review, "psycinfo", again, "p.ris", day=d2, ctx=ctx())
        sc2 = sift.load(f2)
        check("256: a drop that goes ahead writes the run afresh as before, every earlier record and its decision carried, the new "
              "records numbered on, the earlier run's folder untouched",
              took["taken"]["records"] == 3 and sc2.ids == ["R001", "R002", "R003", "R004"] and ss.begun(f2) == ""
              and any(e.get("act") == "carry" and e.get("rec_id") == "R001" for e in sift.read_lines(f2))
              and shas(f1) == before1
              and sorted(p.name for p in f2.iterdir() if p.is_file()) == sorted(
                  [sift.CSV_NAME, sift.LOG_NAME, sift.SEARCHES_NAME, sift.LOCK_NAME, "psycinfo.ris", "raw_psycinfo.json",
                   "run.json"]), str(sorted(p.name for p in f2.iterdir())))

        # a run of a day whose drop began it, refused BUSY, leaves that run's folder as it was too
        ss.take_export(review, "psycinfo", ris("Flying at dusk"), "p.ris", day=d3, ctx=ctx())
        f3 = review / "runs" / d3
        before3 = shas(f3)
        with locks.held(sift.lock_path(f3)):
            ran = refusal_of(lambda: ss.run(review, day=d3, ctx=ctx(), wait=0.2))
        check("256: a run refused BUSY on its run's screening lock removes nothing there",
              ran == locks.BUSY and shas(f3) == before3, ran[:80])
    finally:
        ss.CLOCK, ss.RUNNER = kept_clock, kept_runner
        if kept_env is not None:
            os.environ[ss.STUB_ENV] = kept_env

    # ── 2. Sift's and Trace's first start on a Mac whose Idiograph has its demo in its own data folder
    home = base / "mac-home"
    # the bundle's own demo and settings, as the build ships them, made here from the repo's invented demo
    bundle = base / "bundle"
    shutil.copytree(support.source("demo"), bundle / "demo")
    (bundle / "config.json").write_text(json.dumps(server_mod.shipped_config(), indent=2), encoding="utf-8")
    idio = server_mod.app_paths(True, home, "darwin", app="idiograph")
    idio["data"].mkdir(parents=True)
    server_mod.seed_demo(bundle / "demo", idio["demo"])
    (idio["config"]).write_text(json.dumps({"projects": [], "sound": False, "sift_email": "kites@example.org"}),
                                encoding="utf-8")
    (idio["state"]).write_text(json.dumps({"recent": [], "sift_reviews": [{"folder": str(review), "opened": 1}],
                                           "trace_projects": []}), encoding="utf-8")
    idio_before = shas(idio["data"])
    held = server_mod.app_held()
    kept_state = (server_mod.STATE_PATH, server_mod.STATE_MEMORY)
    got = {}
    try:
        for app in ("sift", "trace"):
            own = server_mod.app_paths(True, home, "darwin", app=app)
            server_mod.STATE_PATH, server_mod.STATE_MEMORY = own["state"], None
            copied = server_mod.first_run(dict(own, shipped_demo=bundle / "demo"), own["config"])
            sources = {"config": idio["config"], "state": idio["state"], "env": idio["env"], "base": idio["data"]}
            made = server_mod.first_start_copy(app, own["config"], sources, own_env=own["env"], own_base=own["data"])
            got[app] = (made, copied, sorted(p.relative_to(own["data"]).as_posix() for p in own["data"].rglob("*")))
    finally:
        server_mod.app_back(held)
        server_mod.STATE_PATH, server_mod.STATE_MEMORY = kept_state
    for app, name in (("sift", "Sift"), ("trace", "Trace")):
        made, copied, files = got[app]
        check(f"256: {name}'s first start copies its settings and recent list from Idiograph's, and no demo and no "
              f"participant into its own folder",
              made and files == ["config.json", "state.json"] and all("demo" not in str(p) for p in copied), str(files))
    check("256: and Idiograph's data folder, its demo among it, is byte for byte as it was",
          shas(idio["data"]) == idio_before and (idio["demo"] / "Juno").is_dir(), str(len(idio_before)))

    # ── 3. the real start path, `start_up` as `main` runs it in a frozen app, on a Mac with nothing yet:
    # Idiograph's first start, then Sift's and Trace's, each with every app's module registered as a
    # frozen build has them
    import workbook as wb_mod
    home3 = base / "mac-home-start"
    real_paths = server_mod.app_paths
    # each app's own bundle, as its build ships it since the sixth build (23 October 2026): its own settings, and
    # the demo Idiograph's alone
    bundles = {}
    for app in ("idiograph", "sift", "trace"):
        bundles[app] = base / f"bundle-{app}"
        bundles[app].mkdir(exist_ok=True)
        (bundles[app] / "config.json").write_text(json.dumps(server_mod.shipped_config(app), indent=2), encoding="utf-8")
    shutil.copytree(bundle / "demo", bundles["idiograph"] / "demo", dirs_exist_ok=True)
    frozen = lambda bundle=True, home=None, system=None, app=None: dict(
        real_paths(True, home3, "darwin", app=app), shipped_demo=bundles[app or server_mod.APP or "idiograph"] / "demo")
    held = server_mod.app_held()
    kept_run = (server_mod.ROOT_OVERRIDE, server_mod.STATE_MEMORY)
    kept_written = (dict(wb_mod.WRITTEN), wb_mod.WRITTEN_HOOK)
    folders, idio_after, own_files = {}, None, {}
    # Idiograph's start hook runs here in this process: Working together's looks left out, as in area 219, so no
    # thread of them goes on looking at later areas' team projects (winfix, 9 November 2026)
    import team_sync
    kept_looks = team_sync.start
    team_sync.start = lambda roots: None
    try:
        server_mod.app_paths = frozen
        server_mod.ROOT_OVERRIDE, server_mod.STATE_MEMORY = None, None
        for app in ("idiograph", "sift", "trace"):
            # a run of another app first, so `use_app` takes this one's folders afresh
            server_mod.APP = None
            server_mod.start_up(argparse.Namespace(app=app, config=None, root=None))
            folders[app] = server_mod.PATHS["data"]
            if app == "idiograph":
                idio_after = shas(folders[app])
            own_files[app] = sorted(p.relative_to(folders[app]).as_posix() for p in folders[app].rglob("*"))
    finally:
        team_sync.start = kept_looks
        server_mod.app_paths = real_paths
        server_mod.app_back(held)
        server_mod.ROOT_OVERRIDE, server_mod.STATE_MEMORY = kept_run
        wb_mod.WRITTEN.clear()
        wb_mod.WRITTEN.update(kept_written[0])
        wb_mod.WRITTEN_HOOK = kept_written[1]
    idio_data = folders["idiograph"]
    check("256: Idiograph's own start, through the start the server runs, still seeds its demo in its data folder, "
          "each demo participant's workbook there",
          all((idio_data / "demo" / name / f"{name} - EN & ES.xlsx").is_file() for name in ("Juno", "Mabel", "Rowan")),
          str(own_files["idiograph"][:6]))
    for app, name in (("sift", "Sift"), ("trace", "Trace")):
        check(f"256: {name}'s start, through the start the server runs, with Idiograph's modules registered, leaves no "
              f"demo and no participant folder in its data folder, only its settings and recent list",
              folders[app] != idio_data and own_files[app] == ["config.json", "state.json"], str(own_files[app]))
    check("256: and Sift's and Trace's starts leave Idiograph's data folder byte for byte as its own start left it",
          shas(idio_data) == idio_after, str(len(idio_after or {})))
    check("256: a run starts the start hooks of the apps it serves alone: Sift's and Trace's none of Idiograph's, "
          "Idiograph's its own",
          server_mod.start_hooks("sift") == [] and server_mod.start_hooks("trace") == []
          and len(server_mod.start_hooks("idiograph")) == 1, str(server_mod.STARTS))

    # ── 4. the settings hooks keyed by app (the sixth build, 23 October 2026): Idiograph's defaults out of the
    # family's, Sift's its own, each server running the hooks of the apps it serves alone
    idio_keys = set(server_mod.defaults("idiograph")) - set(server_mod.DEFAULTS)
    sift_keys = {"databases", "sift_email", "zotero"}
    first = {app: json.loads((folders[app] / "config.json").read_text(encoding="utf-8")) for app in folders}
    check("256: after each app's first start its settings file holds the family's settings and its own alone, "
          "Idiograph's interviewer, corpus and nudges in Idiograph's, Sift's databases in Sift's",
          {"interviewer", "corpus", "nudges"} <= idio_keys <= set(first["idiograph"])
          and not sift_keys & set(first["idiograph"]) and not idio_keys & (set(first["sift"]) | set(first["trace"]))
          and sift_keys <= set(first["sift"]) and not sift_keys & set(first["trace"])
          and all(first[a].get("status_bar") is True for a in first), str({a: sorted(c)[:6] for a, c in first.items()}))
    saves = {}
    kept_cfg = server_mod.CONFIG_PATH
    sent = {"interviewer": "Wren", "nudges": {"length": False}, "status_bar": False, "databases": [],
            "zotero": {"library": "user", "group_id": ""}, "ai_suggest": True, "minimap": "on"}
    try:
        for app in ("idiograph", "sift", "trace"):
            server_mod.CONFIG_PATH = base / f"save-{app}.json"
            server_mod.CONFIG_PATH.write_text("{}\n", encoding="utf-8")
            with support.as_app(app):
                answered = server_mod.api_settings(dict(sent))
            saves[app] = (json.loads(server_mod.CONFIG_PATH.read_text(encoding="utf-8")), answered)
    finally:
        server_mod.CONFIG_PATH = kept_cfg
    check("256: a Sift or Trace save writes no setting of Idiograph's, its sent ones and its defaults alike, and Trace's "
          "none of Sift's, Idiograph's none of Sift's",
          not idio_keys & set(saves["sift"][0]) and not idio_keys & set(saves["trace"][0])
          and sift_keys <= set(saves["sift"][0]) and not sift_keys & set(saves["trace"][0])
          and not sift_keys & set(saves["idiograph"][0]) and saves["idiograph"][0].get("interviewer") == "Wren"
          and saves["idiograph"][0]["nudges"]["length"] is False and saves["idiograph"][0].get("minimap") == "on",
          str({a: sorted(set(s[0]) & (idio_keys | sift_keys)) for a, s in saves.items()}))
    check("256: General's keys save in every app, the status bar and the AI switch among them",
          all(s[0].get("status_bar") is False and s[0].get("ai_suggest") is True for s in saves.values()),
          str({a: s[0].get("status_bar") for a, s in saves.items()}))
    check("256: the AI state an app's page draws by carries no limit in any app since New AI board went (aiout)",
          not any("cap" in saves[a][1]["ai"] for a in ("idiograph", "sift", "trace")))
    kinds = ("SETTINGS_READ", "SETTINGS_SAVE", "AI_CHOICE", "QUESTION", "SCOPES", "HOLDS", "STARTS")
    owners = {kind: {owner for owner, _hook in getattr(server_mod, kind)} for kind in kinds}
    ran = {app: {kind for kind in kinds if server_mod.hooks(getattr(server_mod, kind), app)} for app in ("idiograph", "sift", "trace")}
    check("256: each server runs the settings, AI, question, scope, quit and start hooks of the apps it serves alone, "
          "Sift's its holds, Trace's none, Idiograph's its own, with no hold since its demo's recordings are copied, "
          "never made (recvoices, 12 November 2026)",
          all(owners[kind] <= {"idiograph", "sift", "trace"} for kind in kinds) and ran["trace"] == set()
          and ran["sift"] == {"HOLDS"} and ran["idiograph"] == set(kinds) - {"HOLDS"} and owners["HOLDS"] == {"sift"}
          and all(owner == "idiograph" for kind in kinds if kind != "HOLDS" for owner in owners[kind]), str(ran))
    # qdpx's held copies let go as a process ends, a hook Idiograph takes as it first holds one, never on import
    probe = ("import atexit, base64, json, sys\nseen = []\nreal = atexit.register\n"
             "atexit.register = lambda f, *a, **k: (seen.append(getattr(f, '__name__', '')), real(f, *a, **k))[1]\n"
             "sys.path.insert(0, sys.argv[1])\nimport boot\nboot.setup()\nimport server, idiograph_routes as r\n"
             "on_import = list(seen)\nfor n in range(2):\n"
             "    r.qdpx_let_go(r.qdpx_hold({'name': 'p.qdpx', 'data': base64.b64encode(b'PK').decode()}))\n"
             "print(json.dumps([on_import, seen]))\n")
    import subprocess
    import sys
    done = subprocess.run([sys.executable, "-I", "-c", probe, str(support.TOOL)], capture_output=True, encoding="utf-8",
                          timeout=120, env=dict(os.environ, IDIOGRAPH_STAY_OPEN="1"))
    taken = json.loads(done.stdout.strip().splitlines()[-1]) if done.returncode == 0 and done.stdout.strip() else [[], []]
    check("256: qdpx's hook at the process's end is Idiograph's alone, taken once as it first holds a copy, never as "
          "any app's server imports its modules",
          "qdpx_let_all_go" not in taken[0] and taken[1].count("qdpx_let_all_go") == 1, done.stderr[-300:] or str(taken))
    # ── 5. the top's options before Sift's command read as after it (land6, 23 October 2026): `sift --config x
    # search ...` took `search` for the folder and refused its words
    import cli as cli_mod
    read = lambda given: vars(cli_mod.args_for(given, "sift"))
    before, after = read(["--config", "c.json", "search", "kites", "--folder", "F"]), read(["search", "kites", "--folder", "F", "--config", "c.json"])
    plan = read(["--config", "c.json", "--json", "search", "strings", "R"])
    check("256: Sift's options before its command read as after it, its Search and a review's search strings alike",
          before == after and before["words"] == ["kites"] and before["config"] == "c.json"
          and (plan["act"], plan["rec_id"], plan["config"], plan["json"]) == ("strings", "R", "c.json", True), str((before, plan)))
    # ── 6. each app's page holds its own parts alone since the cutover, so a family script that reads an element
    # by its id finds it on every app's page, or passes over it where it is absent, Idiograph's Home projects and
    # PETs model on Sift's and Trace's pages (land6, 23 October 2026: Sift's and Trace's boot stopped at
    # Idiograph's PETs model select, before their Home loaded)
    import re
    ids_in = lambda t: set(re.findall(r'id="([a-z0-9-]+)"', t)) | set(re.findall(r"\.id = '([a-z0-9-]+)'", t))
    family_js = {n: support.text(f"family/static/{n}") for n in ("shell.js", "search.js", "table.js", "quote.js", "beat.js")}
    # read only where that app's screen stands: the statements' and the PETs bars' bands, for Search's place
    on_its_screen = {"band", "th-band", "tj-band", "cd-band", "sf-band", "sfs-band"}

    def guarded(script: str, wanted: str) -> bool:
        lines = script.splitlines()
        el = re.escape(f"$('{wanted}')")
        for n, line in enumerate(lines):
            if f"$('{wanted}')" not in line:
                continue
            held = re.search(rf"if \({el}\)|if \(\w+ && {el}\)|{el} \?|!{el} \|\||{el} &&", line) \
                or (n and lines[n - 1].strip() == f"if ($('{wanted}')) {{")
            named = re.match(rf"\s*const (\w+) = {el};$", line)
            if not held and not (named and n + 1 < len(lines) and f"if (!{named.group(1)}) return;" in lines[n + 1]):
                return False
        return True

    absent = {}
    for app, own in (("idiograph", ("idiograph.html", "distil.js", "themes.js", "trajectories.js")),
                     ("sift", ("sift.html", "sift.js", "sift_search.js", "sift_settings.js")), ("trace", ("trace.html", "trace.js"))):
        found = ids_in(support.text("family/static/page.html", *(f"apps/{app}/static/{n}" for n in own))
                       + "".join(family_js.values()))
        for name, script in family_js.items():
            for wanted in sorted(set(re.findall(r"\$\('([a-z0-9-]+)'\)", script)) - found - on_its_screen):
                if not guarded(script, wanted):
                    absent.setdefault(f"{name} {wanted}", []).append(app)
    check("256: every element a family script reads by its id is on every app's page, or passed over where it is absent",
          not absent, str(absent))
