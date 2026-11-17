"""Area 421: the reflexive thematic analysis demo, Working from home (rtabuild, 17 November 2026).

Adam, 14 and 16 November 2026: a fourth demo beside the IPA, thematic analysis and longitudinal ones, whose interviews
were made for reflexive thematic analysis, where the thematic analysis demo codes the IPA demo's: six invented
participants on one guide, an invented researcher, Leah Marsh, and the analysis he approved on 16 November.

Every check reads a scratch copy, never the repo's demo, whose gitignored files a run or a build leaves (lipafix, 13
November 2026). A: built twice from its sources into scratch, the same bytes both times, and the same as the pristine
copy it ships. B: a fresh clone's copy filled as the server's start fills it opens as the fourth demo: Home answers its
six participants in the study's order with their labels, pen portraits and pictures from the set no other demo uses,
a thematic analysis project named back as demo-rta, `--demo rta` on the command line and MCP. C: every extract's
words stand in its passage's transcript, the workbook's and the interview's, and every theme and subtheme of its
Themes board holds the approved codes, the two left unplaced unplaced, and the board has no note: the reflexivity
statement is the project's own, its Project settings' Reflexivity (settingsbuild, 17 November 2026).
D: Reset demo puts a changed copy back byte for byte, its code list and Themes board with it, and leaves the other
demos alone. E: the recordings list names six, one an interview, each in the manifest at the demos' release, and
where this computer holds them each recording's length, which the report says, runs past its interview's last
timecode. F: a build stages it whole with no recording, and its player offers its six as a download of their own. G (rtafix):
packaging/release.py refuses a version, a dry run too, while the demos' release lacks a file the manifest names or
holds one at another size or sha256, and the upload script passes over a recording there with the same bytes, refuses
one with other bytes and reads back by sha256, each with a gh of the check's own. Nothing here writes into the repo's demo or packaging/recording."""
from __future__ import annotations

import hashlib
import json
import shutil
from pathlib import Path

from . import support
from .support import check


def ck(name: str, condition, detail="") -> None:
    check(name, bool(condition), "" if condition else str(detail)[:600])


def sha(p) -> str:
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def snapshot(folder: Path) -> dict:
    """Every file under `folder` by its path, its size and its time, to tell a write into it."""
    out = {}
    for p in sorted(Path(folder).rglob("*")):
        if p.is_file():
            st = p.stat()
            out[p.relative_to(folder).as_posix()] = (st.st_size, st.st_mtime_ns)
    return out


def files_of(folder: Path) -> dict:
    return {p.relative_to(folder).as_posix(): p.read_bytes() for p in sorted(Path(folder).rglob("*")) if p.is_file()}


def as_cloned(folder: str, names: list[str]) -> list[str]:
    """What a copy of the repo's demo leaves out to stand as a fresh clone's (area 394's): the files the gitignore keeps
    out, which a run or a build makes beside the participants, every pristine copy kept whole."""
    if "pristine" in Path(folder).parts:
        return []
    made = {"Working", "Source", "_Archive", "pictures", "idiograph-gets.json", "idiograph-codes.json",
            "idiograph-lgets.json", "idiograph-trajectories.json"}
    return [n for n in names if n in made or n.endswith(".m4a")]


def test_rta_demo(scratch: Path):
    print("\n421. The reflexive thematic analysis demo (rtabuild)")
    import cli as family_cli
    import codes as codes_mod
    import demo_recordings as demo_rec
    import i18n
    import idiograph_routes as routes
    import make_demo
    import make_demo_rta as rta
    import mcp_server
    import server as server_mod

    shipped = support.source("demo")
    watched = {"demo": snapshot(shipped), "recording": snapshot(support.source("packaging/recording"))}
    src = shipped / rta.FOLDER
    names = [f"{c}{rta.EN_ES}" for c in rta.CASES]

    # ── A. the same bytes twice, and the same as it ships
    builds = []
    for n in (1, 2):
        into = scratch / f"a421-build-{n}"
        shutil.rmtree(into, ignore_errors=True)
        rta.build_all(into / rta.FOLDER, shipped)
        builds.append(into / rta.FOLDER)
    one, two = files_of(builds[0]), files_of(builds[1])
    ck("421: the demo builds from its sources the same bytes twice, every workbook, progress file, the code list and "
       "the Themes board",
       one and one == two and len([k for k in one if k.endswith(".xlsx")]) == 6,
       [k for k in one if one.get(k) != two.get(k)][:5])
    first = builds[0]
    pristine = src / "pristine"
    differ = [n for c, n in zip(rta.CASES, names) if not support.same_workbook(first / c / n, pristine / n)]
    differ += [f for f in rta.ROOT_FILES if sha(first / f) != sha(pristine / f)]
    differ += [p.name for c in rta.CASES for p in [first / c / "Working" / f"{c} - EN & ES.progress.json"]
               if sha(p) != sha(pristine / "Working" / p.name)]
    ck("421: and the same as the pristine copy it ships, every workbook part for part and every other file byte for "
       "byte", not differ, differ)

    # ── B. a fresh clone's copy filled as the server's start fills it, opened as the fourth demo
    fresh = scratch / "a421-clone"
    shutil.rmtree(fresh, ignore_errors=True)
    shutil.copytree(shipped, fresh, ignore=as_cloned)
    config = scratch / "a421-config.json"
    config.write_text(json.dumps({"projects": [], "corpus": "", "gravity_reference": "", "corpus_exclude": [],
                                  "interviewer": "Adam"}), encoding="utf-8")
    keys = ("DEMO_DIR", "SHIPPED_DEMO", "DEMO_CASE", "DEMO_WORKBOOK", "DEMO_PROJECT", "CONFIG_PATH", "STATE_MEMORY",
            "ROOT_OVERRIDE")
    kept = {k: getattr(server_mod, k) for k in keys}
    try:
        server_mod.DEMO_DIR = server_mod.SHIPPED_DEMO = fresh
        server_mod.DEMO_CASE = fresh / "Juno"
        server_mod.DEMO_WORKBOOK = server_mod.DEMO_CASE / "Juno - EN & ES.xlsx"
        server_mod.DEMO_PROJECT = fresh / server_mod.PROJECT_FILE
        server_mod.CONFIG_PATH, server_mod.STATE_MEMORY, server_mod.ROOT_OVERRIDE = config, {"recent": []}, None
        root = server_mod.demo_rta_dir()
        copied = {p.relative_to(root).as_posix() for p in routes.fill_demo() if root in p.parents}
        ck("421: on a fresh clone the server's start fills the demo from its pristine copy, each participant's progress "
           "file, its code list and its Themes board",
           {f"{c}/Working/{c} - EN & ES.progress.json" for c in rta.CASES} | set(rta.ROOT_FILES) <= copied,
           sorted(copied))
        home = routes.api_cases({})
        cards = home.get("demo_rta_participants") or []
        project = home.get("demo_rta_project") or {}
        people = json.loads((root / server_mod.PROJECT_FILE).read_text(encoding="utf-8"))["participants"]
        others = set()
        for folder in (fresh, fresh / "ta", fresh / "lipa"):
            held = json.loads((folder / server_mod.PROJECT_FILE).read_text(encoding="utf-8")).get("participants") or {}
            others |= {str(p.get("picture")) for p in held.values()}
        pictures = [str(people[c]["picture"]) for c in rta.CASES]
        ck("421: Home answers it as the fourth demo, a thematic analysis project, Working from home, its six in the "
           "study's order, each with their own label, pen portrait and a picture from the set no other demo uses",
           [c["case"] for c in cards] == list(rta.CASES) and [d["case"] for d in home.get("demos_rta") or []] == list(rta.CASES)
           and project.get("name") == "Working from home" and project.get("method") == "ta"
           and project.get("id") == "demo-rta" and project.get("demo") is True
           and project.get("research_question") == "How do people experience working from home since the pandemic?"
           and all(people[c]["label"] and len(people[c]["portrait"]) > 200 for c in rta.CASES)
           and all(p.startswith("set:peep") for p in pictures) and len(set(pictures)) == 6 and not set(pictures) & others,
           json.dumps({"cards": [c.get("case") for c in cards], "project": project}, default=str)[:400])
        books = routes.demo_workbooks(root)
        ck("421: it is named back as demo-rta and fixed as a demo is, each workbook inside it, and the command line and "
           "the MCP server name it `--demo rta` beside the others",
           routes.project_id(root) == "demo-rta" and server_mod.project_named("demo-rta") == root
           and server_mod.is_demo_root(root) and all(server_mod.demo_root_of(b) == root for b in books)
           and server_mod.demo_dir_of("rta") == root and server_mod.demo_dir_of("demo-rta") == root
           and family_cli.demo_words(["--demo", "rta", "cases"]) == ["--demo", "--demo-rta", "cases"]
           and family_cli.demo_asked(["--demo=rta"]) == "rta" and family_cli.demo_asked(["--demo", "lipa"]) == "lipa"
           and mcp_server.desktop_entry(root, demo="rta")["args"][-2:] == ["--demo", "rta"]
           and routes.demo_title(books[0]) == "Kemi, working from home")
        code, out, err = family_cli.run(["--demo", "rta", "--config", str(config), "cases", "--json"])
        said = support.plain(json.loads(out)) if code == 0 else {}
        ck("421: `--demo rta cases` reads the six as a thematic analysis project",
           code == 0 and said["project"]["method"] == "ta" and sorted(c["case"] for c in said["cases"]) == sorted(rta.CASES),
           (err or out)[:300])

        # ── C. every extract in its passage, every theme the approved codes
        plan = rta.read_plan(shipped)
        people_rows = codes_mod.study_rows(rta.books(root))
        extracts = codes_mod.extracts_of(people_rows)
        import workbook as wb_mod
        rows = {(c, r["row"]): r for c, b in zip(rta.CASES, books) for s in wb_mod.read_case(b)["sheets"] for r in s["rows"]}
        turns = {c: [r for r in shipped_turns(rta, c, shipped)] for c in rta.CASES}
        missing = []
        for x in extracts:
            row = rows.get((x["case"], x["row"])) or {}
            text = row.get("text") or ""
            said_csv = turns[x["case"]][x["row"] - 2] if 0 <= x["row"] - 2 < len(turns[x["case"]]) else {}
            words = str(x["quote"] or "").strip('"')
            if (not words or words not in text or said_csv.get("Transcript") != text or row.get("name") != x["case"]
                    or said_csv.get("Name") != x["case"]):
                missing.append(f"{x['case']} row {x['row']}")
        given = sum(len(e["codes"]) for c in rta.CASES for t in json.loads(rta.coding_file(c, shipped).read_text(
            encoding="utf-8"))["turns"] for e in t.get("extracts") or [])
        ck("421: every extract's words stand in its passage, in the workbook's transcript and the interview's, every "
           "code the approved coding gives on its extract",
           extracts and not missing and len(extracts) == given, f"{len(missing)} not found: {missing[:5]}")
        data = json.loads((root / make_demo.GETS_FILE).read_text(encoding="utf-8"))
        board = next(b for b in data["boards"] if b["id"] == data.get("chosen"))
        with i18n.in_method("ta"):
            line = codes_mod.line_codes(data)
        under = {}
        for g in board["groups"]:
            under[g["label"]] = {line[k] for k in g["members"] if k in line}
        want = {}
        for t in plan["themes"]:
            want[t["title"]] = {codes_mod.norm(c) for c in t["codes"]}
            for s in t.get("subs") or []:
                want[s["title"]] = {codes_mod.norm(c) for c in s["codes"]}
        placed = set().union(*want.values())
        on_board = {line[k] for k in board["cards"] if k in line}
        listed = routes.api_codes({"root": "demo-rta"})
        ck("421: every theme and subtheme of its Themes board holds the approved codes, under the approved titles with "
           "their definitions, the two codes left out unplaced, the Current board with no note, and the reflexivity "
           "statement the project's own Reflexivity (settingsbuild)",
           under == want and on_board == placed
           and {codes_mod.norm(c) for c in plan["not_placed"]} == {codes_mod.norm(c["name"]) for c in plan["codes"]} - placed
           and all(g.get("description") for g in board["groups"])
           and not board.get("note") and "reflexivity" not in plan
           and routes.read_project(root)["reflexivity"].startswith("I am ")
           and len(listed["codes"]) == len(plan["codes"]) == 24 and all(c.get("description") for c in listed["codes"]),
           json.dumps({k: sorted(v) for k, v in under.items()})[:400])

        # ── D. Reset demo puts it back byte for byte
        before_others = {f: files_of(fresh / f) for f in ("Juno", "ta", "lipa")}
        was = files_of(root)
        (root / make_demo.CODES_FILE).write_text("{}", encoding="utf-8")
        (root / make_demo.GETS_FILE).unlink()
        shutil.copyfile(books[1], books[0])
        (root / "Ros" / "Working" / "Ros - EN & ES.progress.json").unlink()
        answer = routes.api_reset_demo({"demo": "rta"})
        now = files_of(root)
        changed = sorted(k for k in set(was) | set(now) if was.get(k) != now.get(k))
        ck("421: Reset demo with demo rta puts a changed code list, a lost Themes board, an overwritten workbook and a lost "
           "progress file back byte for byte, and leaves the other demos alone",
           answer.get("demo") == "demo-rta" and not changed
           and {f: files_of(fresh / f) for f in ("Juno", "ta", "lipa")} == before_others, changed[:6])

        # ── E. the recordings: six, one an interview, in the manifest, each length past its last timecode
        manifest = json.loads(support.source("demo/recordings.json").read_text(encoding="utf-8"))
        entries = {r["file"]: r for r in manifest["recordings"]}
        made = rta.recording_names(shipped)
        _, listed_rec = routes.demo_interviews(routes.DEMO_RTA_RECORDINGS)
        ck("421: the recordings list names six, one each participant's interview named by its transcript's hash, each "
           "in the manifest with its size at the demos' release",
           len(made) == 6 and len(set(made)) == 6 and all(n in entries and entries[n]["size"] > 100_000 for n in made)
           and [r["name"] for r in listed_rec] == list(rta.CASES) and all(r["entry"] for r in listed_rec)
           and manifest["release"] == demo_rec.RELEASE, str(made))
        folder = support.source("packaging/recording")
        held = [n for n in made if (folder / n).is_file()]
        if len(held) == 6:
            lengths = {c: make_demo.clip_seconds(folder / n) for c, n in zip(rta.CASES, made)}
            last = {c: sum(int(x) * 60 ** i for i, x in enumerate(reversed(shipped_turns(rta, c, shipped)[-1]["Timestamp"].split(":"))))
                    for c in rta.CASES}
            print("  lengths " + ", ".join(f"{c} {make_demo.hhmmss(s)[3:]}" for c, s in lengths.items()))
            ck("421: each recording this computer holds matches its size and sha256 in the manifest and runs past its "
               "interview's last timecode, the interviews 7 to 10 minutes long",
               all(entries[n]["sha256"] == sha(folder / n) and entries[n]["size"] == (folder / n).stat().st_size for n in held)
               and all(last[c] < lengths[c] and 420 <= lengths[c] <= 600 for c in rta.CASES),
               json.dumps({c: [round(lengths[c]), last[c]] for c in rta.CASES}))
        else:
            support.skip("421: each recording's length", "this computer does not hold the six recordings in "
                         "packaging/recording (they are not committed)")

        # ── F. its player offers the six as a download of their own
        server_mod.DEMO_DIR = fresh
        server_mod.SHIPPED_DEMO = scratch / "a421-shipped"
        shutil.rmtree(server_mod.SHIPPED_DEMO, ignore_errors=True)
        shutil.copytree(fresh, server_mod.SHIPPED_DEMO)
        shutil.copyfile(support.source("demo/recordings.json"), server_mod.SHIPPED_DEMO / "recordings.json")
        offered = routes.api_audio({"path": str(books[3]), "sheet": "Initial"})
        whole = sum(entries[n]["size"] for n in made) + manifest["licence"]["size"]
        ck("421: with none on this computer a participant's player offers the six as a download of their own, its size "
           "theirs and the licence's, apart from the other demos'",
           offered["found"] is False and offered["download"]["demo"] == "rta" and offered["download"]["bytes"] == whole
           and routes.api_demo_recordings({"demo": "rta"})["bytes"] == whole
           and routes.api_demo_recordings({})["demo"] == "ipa", json.dumps(offered)[:300])
    finally:
        for k, v in kept.items():
            setattr(server_mod, k, v)

    build_mac = support.build_mac()
    stage = scratch / "a421-stage"
    shutil.rmtree(stage, ignore_errors=True)
    staged = build_mac.stage_cases(stage) / rta.FOLDER
    ck("421: a build stages it whole, each participant with its progress file, its code list and Themes board, its "
       "sources and project file, and no recording",
       all((staged / c / "Working" / f"{c} - EN & ES.progress.json").is_file() for c in rta.CASES)
       and all((staged / f).is_file() for f in rta.ROOT_FILES) and (staged / "source" / "Themes.json").is_file()
       and (staged / server_mod.PROJECT_FILE).is_file() and not list(staged.rglob("*.m4a")),
       sorted(p.name for p in staged.iterdir()) if staged.is_dir() else "no stage")

    # ── G. the release waits for the recordings, and their upload trusts no same-named asset (rtafix)
    release_and_upload(scratch)

    ck("421: nothing here wrote into the repo's demo or packaging/recording",
       snapshot(shipped) == watched["demo"] and snapshot(support.source("packaging/recording")) == watched["recording"])


# a gh of the check's own: its first argument a JSON file standing for the release's assets by name, each its size and
# digest, which `release view` lists and `release upload` adds to (refusing a name there already without --clobber), a
# release file that is not there a release GitHub cannot find, every call written down beside it
GH_STUB = """import hashlib, json, os, sys
state, args = sys.argv[1], sys.argv[2:]
open(state + '.log', 'a').write(json.dumps(args) + '\\n')
if not os.path.exists(state):
    sys.stderr.write('release not found\\n'); sys.exit(1)
assets = json.load(open(state))
if args[:2] == ['release', 'view']:
    print(json.dumps({'assets': [dict(name=n, **a) for n, a in assets.items()]})); sys.exit(0)
if args[:2] == ['release', 'upload']:
    files = [a for a in args[3:] if os.path.isfile(a)]
    for f in files:
        name = os.path.basename(f)
        if name in assets and '--clobber' not in args:
            sys.stderr.write('asset under the same name already exists: ' + name + '\\n'); sys.exit(1)
    for f in files:
        data = open(f, 'rb').read()
        assets[os.path.basename(f)] = {'size': len(data), 'digest': 'sha256:' + hashlib.sha256(data).hexdigest()}
    json.dump(assets, open(state, 'w')); sys.exit(0)
sys.stderr.write('not this check\\'s: ' + ' '.join(args) + '\\n'); sys.exit(1)
"""


def release_and_upload(scratch: Path) -> None:
    import contextlib
    import importlib.util
    import io
    import subprocess
    import sys

    import demo_recordings as demo_rec
    import make_demo_rta as rta
    sys.path.insert(0, str(support.source("packaging")))
    import release

    base = scratch / "a421-release"
    shutil.rmtree(base, ignore_errors=True)
    base.mkdir(parents=True)
    gh = base / "gh_stub.py"
    gh.write_text(GH_STUB, encoding="utf-8")
    manifest = json.loads(release.RECORDINGS.read_text(encoding="utf-8"))
    entries = list(manifest["recordings"]) + [manifest["licence"]]
    as_asset = lambda e: {"size": e["size"], "digest": f"sha256:{e['sha256']}"}
    rta_names = set(rta.recording_names())

    def state(name: str, assets: dict | None) -> Path:
        path = base / f"{name}.json"
        if assets is not None:
            path.write_text(json.dumps(assets), encoding="utf-8")
        return path

    def asked(path: Path) -> list[list[str]]:
        log = Path(f"{path}.log")
        return [json.loads(line) for line in log.read_text(encoding="utf-8").splitlines()] if log.exists() else []

    # a git of the check's own holding the tags the release reads its manifest from: v-none with no manifest,
    # v-same and the version's own tag with the checkout's, v-other with one recording more than the checkout names
    version = release.server_version("idiograph")
    tagged = base / "tagged"
    (tagged / "demo").mkdir(parents=True)
    git = lambda *a: subprocess.run(["git", "-C", str(tagged), "-c", "user.name=check", "-c", "user.email=check@invalid",
                                     "-c", "commit.gpgsign=false", "-c", "tag.gpgsign=false", *a],
                                    capture_output=True, text=True, encoding="utf-8", check=True)
    git("init", "-q")
    (tagged / "README").write_text("check\n", encoding="utf-8")
    git("add", "-A"); git("commit", "-q", "-m", "none"); git("tag", "v-none")
    (tagged / "demo" / "recordings.json").write_text(json.dumps(manifest), encoding="utf-8")
    git("add", "-A"); git("commit", "-q", "-m", "same"); git("tag", "v-same"); git("tag", f"v{version}")
    extra = {"file": "Extra-Initial-0123456789abcdef.m4a", "size": 5, "sha256": "a" * 64}
    (tagged / "demo" / "recordings.json").write_text(
        json.dumps({**manifest, "recordings": manifest["recordings"] + [extra]}), encoding="utf-8")
    git("add", "-A"); git("commit", "-q", "-m", "other"); git("tag", "v-other")

    def with_gh(path: Path, run):
        kept = release.GH, release.GIT
        release.GH, release.GIT = [sys.executable, str(gh), str(path)], ["git", "-C", str(tagged)]
        out, err = io.StringIO(), io.StringIO()
        try:
            with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
                done = run()
        except SystemExit as exc:
            done = f"refused: {exc}"
        finally:
            release.GH, release.GIT = kept
        return done, out.getvalue() + err.getvalue()

    full = {e["file"]: as_asset(e) for e in entries}
    present = state("present", full)
    missing = state("missing", {n: a for n, a in full.items() if n not in rta_names})
    one_rta = sorted(rta_names)[0]
    wrong = state("wrong", {**full, one_rta: {**full[one_rta], "digest": "sha256:" + "0" * 64},
                            manifest["licence"]["file"]: {**full[manifest["licence"]["file"]], "size": 1}})
    lost = state("lost", None)
    unsummed = state("unsummed", {**full, one_rta: {**full[one_rta], "digest": None}})
    said = {k: with_gh(p, lambda: release.recordings_released(t))[0] for k, p, t in
            (("present", present, "v-same"), ("missing", missing, "v-same"), ("wrong", wrong, "v-same"),
             ("lost", lost, "v-same"), ("other", state("other", full), "v-other"), ("none", state("none", full), "v-none"),
             ("unsummed", unsummed, "v-same"))}
    ck("421: the release goes ahead when the demos' release holds every recording and the licence the manifest names at "
       "its size and sha256, reading the release's assets alone",
       said["present"] is None and asked(present) == [["release", "view", manifest["release"], "--repo",
                                                        release.APP_REPO, "--json", "assets"]], said)
    ck("421: and is refused in one line naming the recordings the release lacks and saying to upload them first, or "
       "naming one there with another sha256 and the licence at another size, or saying GitHub did not list the release",
       str(said["missing"]).startswith("refused: The release demo-recordings-1 lacks")
       and all(n in said["missing"] for n in rta_names) and "Upload them first" in said["missing"]
       and "\n" not in said["missing"]
       and one_rta in said["wrong"] and manifest["licence"]["file"] in said["wrong"]
       and not any(n in said["wrong"] for n in rta_names - {one_rta})
       and "did not list the release" in str(said["lost"]), said)
    ck("421: the manifest is read as the tag being released holds it, not as the checkout does: a tag naming one "
       "recording more is refused naming that one alone, and a tag with no manifest is refused in one line",
       str(said["other"]).startswith("refused: The release demo-recordings-1 lacks") and extra["file"] in said["other"]
       and not any(e["file"] in said["other"] for e in entries)
       and str(said["none"]).startswith("refused: The tag v-none has no demo/recordings.json") and "\n" not in said["none"],
       said)
    ck("421: a recording GitHub gives no sha256 for, from an older gh, is refused saying so and to upgrade gh, never as "
       "other bytes",
       str(said["unsummed"]).startswith(f"refused: GitHub gave no checksum for {one_rta}")
       and "upgrade gh" in said["unsummed"] and "other bytes" not in said["unsummed"], said)

    runs = {}
    for k, argv in (("release", [f"v{version}"]), ("dry", [f"v{version}", "--dry-run"])):
        path = state(f"main-{k}", {n: a for n, a in full.items() if n not in rta_names})
        runs[k] = (with_gh(path, lambda: release.main(argv))[0], asked(path))
    sift = state("sift", None)
    sifted = with_gh(sift, lambda: release.recordings_released("v-same", "sift"))[0]
    ck("421: a release and its dry run with recordings missing on the demos' release are refused before anything is "
       "collected, signed or published, gh asked for the demos' release's assets alone, and Sift, with no demo, asks "
       "nothing",
       all(str(done).startswith("refused: The release demo-recordings-1 lacks") and calls == [calls[0]]
           and calls[0][:3] == ["release", "view", "demo-recordings-1"] for done, calls in runs.values())
       and sifted is None and asked(sift) == [], runs)

    # the upload script, on a scratch folder of six stand-in recordings and the licence, with its own manifest
    spec = importlib.util.spec_from_file_location("upload_rta_recordings_421",
                                                  support.source("packaging/upload_rta_recordings.py"))
    up = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(up)
    folder = base / "recording"
    folder.mkdir()
    rows = []
    for i, name in enumerate(rta.recording_names()):
        (folder / name).write_bytes(f"stand-in recording {i}\n".encode() * (i + 3))
        rows.append({"file": name, "size": (folder / name).stat().st_size, "sha256": sha(folder / name)})
    licence = folder / demo_rec.LICENCE
    licence.write_text("A stand-in licence for the demos' recordings.\n", encoding="utf-8")
    named_as = demo_rec.licence_asset(sha(licence))
    ours = {**manifest, "recordings": [e for e in manifest["recordings"] if e["file"] not in rta_names] + rows,
            "licence": {"file": named_as, "size": licence.stat().st_size, "sha256": sha(licence)}}
    ours_path = base / "recordings.json"
    ours_path.write_text(json.dumps(ours, indent=1), encoding="utf-8")
    kept = (up.FOLDER, up.MANIFEST)
    up.FOLDER, up.MANIFEST = folder, ours_path
    try:
        # the old licence the copies already out download, under its old name, never touched
        old_licence = {"size": 910, "digest": "sha256:" + "1" * 64}
        others = {e["file"]: as_asset(e) for e in manifest["recordings"] if e["file"] not in rta_names}
        quiet = state("up-quiet", others)
        dry = with_gh(quiet, lambda: up.main([]))
        fresh = state("up-fresh", {**others, demo_rec.LICENCE: old_licence, ours_path.name: {"size": 1, "digest": ""}})
        done = with_gh(fresh, lambda: up.main(["--yes"]))
        uploads = [a for a in asked(fresh) if a[:2] == ["release", "upload"]]
        clobbered = [Path(x).name for a in uploads if "--clobber" in a for x in a[3:] if Path(x).is_file()]
        after = json.loads(fresh.read_text(encoding="utf-8"))
        ck("421: the upload script without --yes asks GitHub nothing; with it the six and the licence, under its new "
           "name carrying its sha256's first 8, go up as new assets, the old LICENSE-audio.md untouched, the release's "
           "copy of the manifest the one asset replaced, each read back at its size and sha256",
           dry[0] == 0 and asked(quiet) == [] and done[0] == 0 and clobbered == [ours_path.name]
           and named_as != demo_rec.LICENCE and named_as.startswith("LICENSE-audio-")
           and release.unreleased(rows + [ours["licence"]], after) == []
           and after[demo_rec.LICENCE] == old_licence
           and after[ours_path.name]["digest"] == f"sha256:{sha(ours_path)}", (done, uploads))

        same = state("up-same", {**others, rows[0]["file"]: as_asset(rows[0]), named_as: as_asset(ours["licence"])})
        again = with_gh(same, lambda: up.main(["--yes"]))
        sent = [Path(x).name for a in asked(same) if a[:2] == ["release", "upload"] for x in a[3:] if Path(x).is_file()]
        clash = state("up-clash", {**others, rows[0]["file"]: {**as_asset(rows[0]), "digest": "sha256:" + "2" * 64}})
        refused = with_gh(clash, lambda: up.main(["--yes"]))
        lclash = state("up-lclash", {**others, named_as: {**as_asset(ours["licence"]), "digest": "sha256:" + "3" * 64}})
        licence_clash = with_gh(lclash, lambda: up.main(["--yes"]))
        nosum = state("up-nosum", {**others, rows[1]["file"]: {**as_asset(rows[1]), "digest": None}})
        no_sum = with_gh(nosum, lambda: up.main(["--yes"]))
        ck("421: a recording or the licence already on the release with the manifest's bytes is passed over, and one "
           "there with other bytes refuses the whole upload in one line naming it and saying what to do, nothing "
           "uploaded or replaced",
           again[0] == 0 and rows[0]["file"] not in sent and named_as not in sent
           and sorted(set(sent) - {ours_path.name}) == sorted(r["file"] for r in rows[1:])
           and refused[0] == 1 and rows[0]["file"] in refused[1] and "never replaced" in refused[1]
           and not [a for a in asked(clash) if a[:2] == ["release", "upload"]]
           and json.loads(clash.read_text(encoding="utf-8"))[rows[0]["file"]]["digest"] == "sha256:" + "2" * 64
           and licence_clash[0] == 1 and named_as in licence_clash[1]
           and not [a for a in asked(lclash) if a[:2] == ["release", "upload"]]
           and no_sum[0] == 1 and f"GitHub gave no checksum for {rows[1]['file']}" in no_sum[1]
           and "upgrade gh" in no_sum[1] and not [a for a in asked(nosum) if a[:2] == ["release", "upload"]],
           (again, sent, refused, licence_clash, no_sum))
    finally:
        up.FOLDER, up.MANIFEST = kept


def shipped_turns(rta, name: str, demo: Path) -> list[dict]:
    import make_demo
    return make_demo.read_turns(rta.interview(name, demo))
