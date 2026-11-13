#!/usr/bin/env python3
"""Build Idiograph.app, the Mac app in its own window with its own Python inside, its disk image and the
file its updater takes.

    python3 packaging/build_mac.py                  # from the app's folder, into build/ and dist/ beside it
    python3 packaging/build_mac.py --out <folder>   # into <folder>/build and <folder>/dist
    python3 packaging/build_mac.py --unsigned       # never sign, even with an identity
    python3 packaging/build_mac.py --test-app --out <folder>   # a check's build, Idiograph Test
    python3 packaging/build_mac.py --app sift       # Sift.app, Sift.dmg and Sift.app.tar.gz (Trace likewise)
    python3 packaging/build_mac.py --list --app sift   # what Sift's build would ship, building nothing
    python3 packaging/build_mac.py --unsigned --build <sha>   # a daily build, naming its commit (mac_daily.py)

`--list` (22 October, the family codebase) prints each file a build would ship and where it comes
from, and `--scripts` the page's own scripts, which GitHub's suite checks with node --check. The
modules and the page come from the folder lists (`code_folders`): the root, family/ and each app's
folder, the page's static/ folders merged into the bundle's one.

`--app` (20 October, the three-app split's build 6) builds Sift or Trace in place of Idiograph: the
server frozen under the app's own name, by which it knows which app it is, and the window with the
app's name, bundle id, icon, version from versions.json and update address (`packaging/tauri/bundle.py`).

One command from a clean checkout, on any Python 3 the Mac has, with Rust and Node.js installed for
Tauri's bundler. `build/` and `dist/` are gitignored, and nothing else in the checkout is written. The
steps:

The app is for Apple Silicon Macs alone (M1 or later), arm64 (Adam, 9 November 2026, relfix: cryptography
has had an Apple Silicon wheel alone since 49.0.0, so from 0.9.23 Intel Macs keep the copy they have).
It is built on an Apple Silicon Mac, and refused on an Intel one.

1. A build venv, `build/venv`, made with the newest python.org Python of 3.11 or later when one is
   installed, else the Python running this script, either of them one that runs as arm64.
   PyInstaller, openpyxl, certifi and cryptography go into it at the versions pinned in PINS, and
   dmgbuild, which makes the disk image, at those in DMG_PINS, never into the repo's own `.venv`.
2. The stage, `build/stage`: the demo as Reset demo leaves it, its three cases from
   `demo/pristine/`, Rowan's and Mabel's with their boards, and `demo/recordings.json`, the manifest the app
   downloads the demo's recordings by the first time one is played (recdemand, 13 November 2026: text in,
   recordings on demand), no recording and no `LICENSE-audio.md` staged, and `config.json` from
   `server.shipped_config()`, which names no project.
3. PyInstaller, one folder, from `packaging/mac_launcher.py`, which finds every module of the app
   from there, with the static page, the licences, the config and the app's own files of
   `app_identity.FILES` as its data, Idiograph's three guidance files, demo and transcript template among
   them, and nothing of another app's (the family codebase's sixth build, 23 October 2026): the server, which the window runs beside it, and the
   command line and the MCP server, which `Idiograph cli` and `Idiograph mcp` hand over to. Its
   `cli --help` proves it finds every module. Then the typesetter, `idiograph-typeset`, built by cargo from
   `packaging/tauri/typeset/` and put beside the server, signed as its binaries are, and run on a one-line page
   with the fonts the bundle carries (typst1, 9 November 2026, `packaging/typeset_helper.py`). typst-py, a
   run from source's engine, is never frozen in.
4. Tauri's bundler (`packaging/tauri/bundle.py`): the window around the server, `Idiograph.app`, then
   its disk image, made by dmgbuild (18 October, the fourth Tauri build), the app at the left and a
   link to /Applications at the right with an arrow between them, and `Idiograph.app.tar.gz`, the app
   as Tauri's updater takes it, all three into `dist/`, arm64 alone: the server frozen for ARCH and the
   window built for this Mac's own Rust target, aarch64-apple-darwin, and the build stopped if the app
   is for anything else.
5. Signing. With a Developer ID Application identity in the login keychain and the notarytool
   keychain profile NOTARY_PROFILE stored on this Mac, PyInstaller signs the server's every binary
   with it and Tauri the app, both with the hardened runtime, and the image is signed, notarised
   and its ticket stapled. Without both every part is signed ad hoc, said in one line, and macOS
   asks once before it opens the app. No credential is ever read here: `security find-identity`
   lists the identities and notarytool reads its own profile.
"""
from __future__ import annotations

import argparse
import json
import os
import platform
import plistlib
import re
import shutil
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
TOOL = HERE.parent
sys.path.insert(0, str(TOOL))
sys.path.insert(0, str(HERE / "tauri"))
sys.path.insert(0, str(HERE))
import boot  # noqa: E402  the family's folders on the path (boot.py)
boot.setup()

import app_identity  # noqa: E402  which of the three apps a build is
import audio as audio_mod  # noqa: E402  the kinds of file a recording is, the standard library alone
import bundle as window  # noqa: E402  Tauri's bundler run on the window, packaging/tauri/bundle.py
import typeset_helper  # noqa: E402  the typesetter beside the frozen server, packaging/typeset_helper.py

NAME = "Idiograph"
ENTRY = HERE / "mac_launcher.py"
# what the build venv holds, pinned so a release is the same build on any day. certifi carries the
# certificates HTTPS is checked against, since the bundle's Python has none of the Mac's. cryptography seals Working
# together's messages (wtkeys, 8 November 2026), its own wheel with OpenSSL inside
PINS = ("pyinstaller==6.22.3", "openpyxl==3.1.5", "et_xmlfile==2.0.0", "certifi==2026.7.22", "cryptography==50.0.2")
# what makes the disk image, laid out as the Finder shows it, on a Mac alone (packaging/tauri/bundle.py)
DMG_PINS = ("dmgbuild==1.6.7", "ds_store==1.3.3", "mac_alias==2.2.3")
FRAMEWORKS = Path("/Library/Frameworks/Python.framework/Versions")
# the one architecture the Mac app is for, Apple Silicon's (relfix, 9 November 2026)
ARCH = "arm64"
IDENTITY = "Developer ID Application"
# the profile `xcrun notarytool store-credentials idiograph-notary` makes, once, on the release Mac
NOTARY_PROFILE = "idiograph-notary"
# Every module an app runs, by its owner, named so a lazy import is never left out: the family's in every app's
# build and each app's in its own alone (the family codebase's sixth build, 23 October 2026), each app's entry,
# routes, command, tools and Search among its own
MODULES_BY_OWNER = {
    "family": ("server", "boot", "agent_log", "ai_suggest", "app_folders", "app_identity", "app_search", "make_app",
               "mcp_server", "cli", "locks", "errors", "files", "textfiles", "pdftext", "screenings", "i18n", "formats",
               "trash", "relay_transport", "folder_transport", "names", "typeset"),
    "idiograph": ("audio", "convert", "corpus", "demo_recordings", "export", "make_demo", "nudges", "rounds", "shared_strings", "themes",
                  "themes_ai", "themes_print", "themes_word", "workbook", "gets", "gets_print", "print_pdf", "project_pack",
                  "trajectories", "codes", "qdpx", "idiograph_main", "idiograph_routes", "idiograph_cli", "idiograph_mcp",
                  "idiograph_find", "statement_prompts", "team", "transport", "table_import"),
    "sift": ("sift", "sift_ai", "sift_oa", "sift_search", "sift_second", "sift_zotero", "sift_main", "sift_routes",
             "sift_cli", "sift_mcp", "sift_find", "sift_words"),
    "trace": ("trace_claims", "trace_main", "trace_routes", "trace_cli", "trace_mcp", "trace_find"),
}
# every module of every app, the family's first
MODULES = tuple(name for names in MODULES_BY_OWNER.values() for name in names)
# the third-party files the page loads from the app itself, never the web, each with its licence: Ko-fi's cup
# and the Quicksand face of its button on each Home (22 October), the family's, and an app's own in
# `app_identity.FILES`, Sift's Mermaid, which draws its PRISMA flow. They sit in a `static/vendor/` and ship with
# `static/`, and a build without its own stops before it starts
FAMILY_VENDORED = (Path("static") / "vendor" / "kofi" / "cup-border.png",
                   Path("static") / "vendor" / "quicksand" / "quicksand-latin-700-normal.woff2",
                   Path("static") / "vendor" / "quicksand" / "OFL-quicksand.txt")
# what no frozen server takes: typst-py is for a run from source alone, the frozen app typesetting with the
# typesetter beside it (typst1, 9 November 2026, family/typeset.py)
EXCLUDES = ["tkinter", "test", "typst"]
# the docs the window carries beside the server, its manual and its What's new (packaging/tauri/bundle.py), which
# PyInstaller never takes
WINDOW_DOCS = ("manual", "whats_new")
DEMO_WORKBOOK = "Juno - EN & ES.xlsx"
# The demo's recordings (recdemand, 13 November 2026, Adam: "Text in, recordings on demand"): no build stages
# one. The demo ships its text and `recordings.json`, the manifest the app downloads its recordings by the first
# time one is played, so the AI-made audio and its own licence stay out of every installer, the signed Windows
# one among them, and a stage holding a recording or that licence stops the build
DEMO_MANIFEST = "recordings.json"
AUDIO_LICENCE = "LICENSE-audio.md"
# the demo's three cases, each staged from the pristine copy with its sidecar and its board, and the
# GETs file across them, since the demo is a finished project (26 October)
DEMO_CASES = ("Juno", "Rowan", "Mabel")
DEMO_GETS = "idiograph-gets.json"
# the thematic analysis demo's folder inside the demo's, and its code list (demos, 3 November 2026)
DEMO_TA = "ta"
DEMO_CODES = "idiograph-codes.json"
# the longitudinal demo's folder, its three participants, and its LGETs and Trajectories files (lipabuild, 13 November
# 2026): each participant staged with every board file of theirs, a PETs file a timepoint and the LPETs file
DEMO_LIPA = "lipa"
DEMO_LIPA_CASES = ("Hollis", "Nell", "Arlo")
DEMO_ROOT_FILES = (DEMO_GETS, DEMO_CODES, "idiograph-lgets.json", "idiograph-trajectories.json")
# the transcript template, shipped so a tester has it in Idiograph, under `template/` in the bundle
TEMPLATE = Path("template") / "Transcript template.xlsx"


def say(line: str) -> None:
    print(line, flush=True)


# ── the folder lists ──────────────────────────────────────────────────────────────────────────
# (22 October 2026, the family codebase's first build) The family's code sits in folders, the root,
# family/ and each app's under apps/ (boot.py), and both builds take what they ship from these lists
# alone: each module of the app's from the one folder that has it, and the page from the static/ of each
# folder merged into the bundle's one static/, a name in two refused. Since the sixth build (23 October 2026)
# each app's build takes the family's folder, its own and the root, and ships nothing of another app's: no
# module, page part, script, style, data file or doc.

# The root's server.py, cli.py and mcp_server.py are the shims of the family's modules of those names (the
# fourth build, 22 October 2026, see boot.shim), which no build ships: the family's are the modules
ROOT_SHIMS = ("server", "cli", "mcp_server")


def code_folders(app: str = app_identity.DEFAULT) -> list[Path]:
    """The folders `app`'s build takes modules and the page from: the family's, the app's own and the root,
    in boot.setup's order, which PyInstaller looks for a module in, so `server` is family/server.py."""
    return [TOOL / "family", TOOL / "apps" / app_identity.check(app), TOOL]


def modules(app: str = app_identity.DEFAULT) -> tuple:
    """The modules `app`'s build ships, the family's and its own."""
    return MODULES_BY_OWNER["family"] + MODULES_BY_OWNER[app_identity.check(app)]


def vendored(app: str = app_identity.DEFAULT) -> tuple:
    """The third-party files `app`'s page loads, the family's and its own, by their paths under the bundle."""
    return FAMILY_VENDORED + tuple(Path(f) for f in app_identity.files(app) if f.startswith("static/"))


def module_files(app: str = app_identity.DEFAULT) -> dict[str, Path]:
    """Each module of the app's and its file, found in exactly one of `code_folders`. A module in none or
    in two stops the build before it starts."""
    found, wrong = {}, []
    for name in modules(app):
        hits = [folder / f"{name}.py" for folder in code_folders(app) if (folder / f"{name}.py").is_file()
                and not (folder == TOOL and name in ROOT_SHIMS)]
        if len(hits) == 1:
            found[name] = hits[0]
        else:
            wrong.append(f"{name} ({'in none of the folders' if not hits else 'in ' + ' and '.join(str(h.parent.relative_to(TOOL)) for h in hits)})")
    if wrong:
        raise SystemExit(f"The build needs each module in one folder, and {', '.join(wrong)}.")
    return found


def static_files(app: str = app_identity.DEFAULT) -> dict[str, Path]:
    """Every file of the page by its path under the bundle's static/, from the static/ of each of
    `code_folders`, merged. A path in two folders stops the build, since one would hide the other."""
    merged: dict[str, Path] = {}
    for folder in code_folders(app):
        base = folder / "static"
        for path in sorted(base.rglob("*")) if base.is_dir() else []:
            if path.is_file():
                rel = path.relative_to(base).as_posix()
                if rel in merged:
                    raise SystemExit(f"static/{rel} is in both {merged[rel].relative_to(TOOL)} and {path.relative_to(TOOL)}.")
                merged[rel] = path
    return merged


def stage_static(stage: Path, app: str = app_identity.DEFAULT) -> Path:
    """The page as the bundle carries it, `static_files` copied into the stage's static/."""
    target = stage / "static"
    shutil.rmtree(target, ignore_errors=True)
    for rel, path in static_files(app).items():
        (target / rel).parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(path, target / rel)
    return target


def data_files(app: str = app_identity.DEFAULT) -> list[tuple[Path, str]]:
    """The app's other files as (where it is, the bundle's folder for it), the family's and its own of
    `app_identity.files`, each found by boot as the code finds it, at the top or under its own folder: the
    licences and the versions, and Idiograph's guidance, its template under template/, its guide and schemas
    under docs/, Sift's and Trace's guides under docs/. The demo, staged, the page's vendored files, which ship
    with static/, and the docs the window carries are not among them."""
    window = {f"docs/{app_identity.APPS[app_identity.check(app)][key]}" for key in WINDOW_DOCS}
    datas = []
    for name in app_identity.files("family") + app_identity.files(app):
        if name == "demo" or name.startswith("static/") or name in window:
            continue
        found = boot.resource(name)
        folder = Path(name) if found.is_dir() else Path(name).parent
        datas.append((found, "." if str(folder) == "." else folder.as_posix()))
    return datas


def ships_demo(app: str = app_identity.DEFAULT) -> bool:
    """Whether `app`'s build carries the demo, Idiograph's alone (`app_identity.FILES`)."""
    return "demo" in app_identity.files(app)


def bundle_inputs(stage: Path, app: str = app_identity.DEFAULT) -> tuple[list[str], list[tuple[str, str]], list[str]]:
    """What PyInstaller is given, for the Mac build and the Windows one alike: the folders it finds
    modules in, the data as (source, bundle folder) with the page staged and merged, and the modules
    named so a lazy import is never left out. A vendored file the page loads and the build lacks
    stops it here."""
    page = static_files(app)
    missing = [str(item) for item in vendored(app) if Path(item).relative_to("static").as_posix() not in page]
    if missing:
        raise SystemExit(f"The build needs {', '.join(missing)}, which the page loads from the app.")
    module_files(app)
    datas = [(stage_static(stage, app), "static")] + ([(stage / "demo", "demo")] if ships_demo(app) else [])
    datas += [(stage / "config.json", ".")] + data_files(app)
    # a daily build's commit, written into the stage by `stage_build` and shipped at the bundle's top (macdaily)
    if (stage / app_identity.BUILD_FILE).is_file():
        datas.append((stage / app_identity.BUILD_FILE, "."))
    return [str(f) for f in code_folders(app)], [(str(s), d) for s, d in datas], list(modules(app))


def listing(app: str = app_identity.DEFAULT, windows: bool = False) -> list[tuple[str, str]]:
    """What a build of `app` ships, without building: (its path in the bundle, where it comes from),
    the modules as PYZ/<name>, the page, the data, Idiograph's demo as the stage lays it out, its text and the
    manifest of its recordings, never a recording, and the config. `windows` is the Windows build's, without
    certifi."""
    import tempfile
    rows = [(f"PYZ/{name}", str(path.relative_to(TOOL))) for name, path in module_files(app).items()]
    rows += [] if windows else [("PYZ/certifi", "the build venv's certifi")]
    rows += [(f"static/{rel}", str(path.relative_to(TOOL))) for rel, path in static_files(app).items()]
    for source, folder in data_files(app):
        files = sorted(p for p in source.rglob("*") if p.is_file()) if source.is_dir() else [source]
        for path in files:
            inside = path.relative_to(source).as_posix() if source.is_dir() else path.name
            dest = inside if folder == "." else f"{folder}/{inside}"
            rows.append((dest, str(path.relative_to(TOOL))))
    if ships_demo(app):
        with tempfile.TemporaryDirectory(prefix="idiograph-list-") as tmp:
            demo = stage_cases(Path(tmp))
            rows += [(f"demo/{p.relative_to(demo).as_posix()}", "the demo, staged from demo/")
                     for p in sorted(demo.rglob("*")) if p.is_file()]
    rows.append(("config.json", f"server.shipped_config({app_identity.check(app)!r})"))
    rows.append((typeset_helper.NAME, "packaging/tauri/typeset, built by cargo beside the frozen server (.exe on Windows)"))
    return sorted(rows)


def page_scripts(app: str = app_identity.DEFAULT) -> list[Path]:
    """The page's own scripts a build ships, the vendored ones left out, for CI's node --check."""
    return sorted(path for rel, path in static_files(app).items() if rel.endswith(".js") and "/" not in rel)


def run(cmd, **kw) -> subprocess.CompletedProcess:
    return subprocess.run([str(c) for c in cmd], check=True, **kw)


# ── 1. the build venv ─────────────────────────────────────────────────────────────────────────

def python_facts(exe: Path) -> tuple[tuple[int, int], str] | None:
    """The version and platform tag of a Python, or None when it does not run."""
    try:
        out = subprocess.run([str(exe), "-c", "import sys, sysconfig; "
                              "print(sys.version_info[0], sys.version_info[1], sysconfig.get_platform())"],
                             capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=30).stdout.split()
        return (int(out[0]), int(out[1])), out[2]
    except (OSError, subprocess.TimeoutExpired, ValueError, IndexError):
        return None


def runs_arm64(platform_tag: str) -> bool:
    """Whether a Python with this `sysconfig.get_platform()` runs as arm64: an arm64 one or a universal2 one."""
    return platform_tag.endswith(("-arm64", "-universal2"))


def choose_python(asked: str | None) -> Path:
    """The Python the build venv is made with: the newest python.org Python of 3.11 or later that runs as
    arm64, else the one asked for or the one running this script, refused unless it is 3.11 or later and
    runs as arm64."""
    if not asked:
        best = None
        for exe in FRAMEWORKS.glob("3.*/bin/python3.*"):
            if not re.fullmatch(r"python3\.\d+", exe.name):
                continue
            facts = python_facts(exe)
            if facts and facts[0] >= (3, 11) and runs_arm64(facts[1]) and (best is None or facts[0] > best[0]):
                best = (facts[0], exe)
        if best:
            return best[1]
    exe = Path(asked or sys.executable)
    facts = python_facts(exe)
    if not facts or facts[0] < (3, 11):
        raise SystemExit(f"The app needs Python 3.11 or later to build, and {exe} is not.")
    if not runs_arm64(facts[1]):
        raise SystemExit(f"The Mac app is for Apple Silicon, and {exe} is a Python for {facts[1]}.")
    return exe


def build_venv(build: Path, python: Path) -> Path:
    """The build venv with PINS in it, made afresh when the Python behind it has changed."""
    venv = build / "venv"
    marker = venv / "made-with.txt"
    want = f"{python}\n" + "\n".join(PINS + DMG_PINS) + "\n"
    if not (marker.is_file() and marker.read_text(encoding="utf-8") == want):
        shutil.rmtree(venv, ignore_errors=True)
        say(f"Making the build venv with {python}")
        run([python, "-m", "venv", venv])
        run([venv / "bin" / "python", "-m", "pip", "install", "--disable-pip-version-check", "-q", *PINS, *DMG_PINS])
        marker.write_text(want, encoding="utf-8")
    return venv / "bin" / "python"


# ── 2. the stage ──────────────────────────────────────────────────────────────────────────────

def stage_demo(stage: Path) -> Path:
    """The demo as Reset demo leaves it, its three cases and the manifest of their recordings. Nothing of a demo
    worked on here, no live themes file and no backup, ever reaches the stage: every case comes
    from the pristine copy, whose boards and GETs file are the ones the demo ships with."""
    demo = stage_cases(stage)
    say(f"Staged the demo {demo_line(demo)}")
    return demo


def demo_line(demo: Path) -> str:
    """The words a build says of the staged demo, every build's, the Mac's, Windows's and Linux's: its text, with its
    recordings to download the first time one is played. A stage holding a recording or the recordings' licence
    stops the build, since the AI-made audio never ships in an installer (recdemand, 13 November 2026)."""
    audio = sorted(p.relative_to(demo).as_posix() for p in demo.rglob("*")
                   if p.is_file() and (p.suffix.lower() in audio_mod.CONTENT_TYPES or p.name == AUDIO_LICENCE))
    if audio:
        raise SystemExit(f"The staged demo holds {audio[0]}, and no installer carries the demo's recordings.")
    if not (demo / DEMO_MANIFEST).is_file():
        return "with its text and no recordings, demo/recordings.json being missing"
    return "with its text, its recordings to download the first time one is played"


def stage_cases(stage: Path) -> Path:
    """The demos' cases in the stage as `stage_demo` lays them out, and the manifest of their recordings, the
    Windows and Linux builds' as the Mac's."""
    demo, source = stage / "demo", TOOL / "demo"
    shutil.rmtree(demo, ignore_errors=True)
    demo.mkdir(parents=True)
    leave = shutil.ignore_patterns(".*", "*.themes.json", "_Archive", "~$*")
    # the IPA demo at the stage's demo, and the thematic analysis demo in its folder inside it (demos, 3 November 2026),
    # and the longitudinal demo in its own (lipabuild, 13 November 2026)
    for into, src, cases in ((demo, source, DEMO_CASES), (demo / DEMO_TA, source / DEMO_TA, DEMO_CASES),
                             (demo / DEMO_LIPA, source / DEMO_LIPA, DEMO_LIPA_CASES)):
        if not (src / "pristine").is_dir():
            continue
        shutil.copytree(src / "pristine", into / "pristine", ignore=shutil.ignore_patterns(".*", "_Archive", "~$*"))
        shutil.copytree(src / "source", into / "source", ignore=leave)
        shutil.copyfile(src / "idiograph-project.json", into / "idiograph-project.json")
        for name in cases:
            stem = f"{name} - EN & ES"
            (into / name / "Working").mkdir(parents=True, exist_ok=True)
            shutil.copyfile(src / "pristine" / f"{stem}.xlsx", into / name / f"{stem}.xlsx")
            # its progress file and its boards, in the longitudinal demo a PETs file a timepoint and the LPETs file
            for side in sorted((src / "pristine" / "Working").glob(f"{stem}.*.json")):
                shutil.copyfile(side, into / name / "Working" / side.name)
        # the finished demo's GETs, at the demo's root as the GETs screen keeps them (26 October), the
        # thematic analysis demo's code list beside its own, and the longitudinal demo's LGETs and Trajectories
        for kept in DEMO_ROOT_FILES:
            if (src / "pristine" / kept).is_file():
                shutil.copyfile(src / "pristine" / kept, into / kept)
    # the manifest the app downloads the demo's recordings by (recdemand, 13 November 2026), at the demo's root
    if (source / DEMO_MANIFEST).is_file():
        shutil.copyfile(source / DEMO_MANIFEST, demo / DEMO_MANIFEST)
    return demo


def stage_config(stage: Path, py: Path, app: str = app_identity.DEFAULT) -> Path:
    """config.json as the app ships it, from `server.shipped_config(app)`: the app's defaults, no project."""
    out = run([py, "-c", "import sys, json; sys.path.insert(0, sys.argv[1]); import server; "
               "print(json.dumps(server.shipped_config(sys.argv[2]), indent=2, ensure_ascii=False))", TOOL,
               app_identity.check(app)], capture_output=True, text=True, encoding="utf-8").stdout
    data = json.loads(out)
    if data.get("root") or data.get("projects"):
        raise SystemExit("The shipped config names a project, and it must not.")
    path = stage / "config.json"
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return path


def stage_build(stage: Path, sha: str | None) -> Path | None:
    """`build.json` in the stage, naming the commit a daily build is made from (macdaily, 9 November 2026), which
    `app_identity.build` reads and About shows after the version. Without a commit any file an earlier build
    left is taken away, so a release never carries one."""
    path = stage / app_identity.BUILD_FILE
    path.unlink(missing_ok=True)
    if not sha:
        return None
    if not (sha.isalnum() and len(sha) <= 40):
        raise SystemExit(f"--build takes a commit's short sha, and {sha!r} is not one.")
    path.write_text(json.dumps({"build": sha}) + "\n", encoding="utf-8")
    return path


def app_version(py: Path | None = None, app: str = app_identity.DEFAULT) -> str:
    """The app's version, its entry in versions.json, the one the server reads too."""
    return app_identity.version(app)


def server_name(app: str = app_identity.DEFAULT) -> str:
    """The frozen server's name, the app's own, `Idiograph`, `Sift` or `Trace`, by which the server
    knows which app it is (`app_identity.from_executable`) and the window finds it."""
    return app_identity.APPS[app_identity.check(app)]["name"]


# ── 3. PyInstaller ────────────────────────────────────────────────────────────────────────────

def write_spec(build: Path, stage: Path, version: str, identity: str | None = None,
               app: str = app_identity.DEFAULT) -> Path:
    """The spec: one Analysis of the launcher, one folder, the server the window runs beside it (17
    October, the third Tauri build, where PyInstaller's own app around it went for Tauri's). With an
    identity PyInstaller signs every binary with it, and else ad hoc, as a Mac needs to run them. The
    server is named for `app`, `Sift` for Sift, the name by which it knows which app it is."""
    server = server_name(app)
    pathex, datas, modules = bundle_inputs(stage, app)
    spec = f'''# Written by build_mac.py on every build. Change that script, never this file. Version {version}.
a = Analysis([{str(ENTRY)!r}], pathex={pathex!r},
             datas={datas!r},
             hiddenimports={modules + ["certifi"]!r}, excludes={EXCLUDES!r}, noarchive=False)
pyz = PYZ(a.pure)
exe = EXE(pyz, a.scripts, [], exclude_binaries=True, name={server!r}, console=False,
          argv_emulation=False, target_arch={ARCH!r}, upx=False,
          codesign_identity={identity!r}, entitlements_file=None)
coll = COLLECT(exe, a.binaries, a.datas, name={server!r}, upx=False)
'''
    path = build / f"{server}.spec"
    path.write_text(spec, encoding="utf-8")
    return path


def pyinstaller(py: Path, build: Path, spec: Path, app: str = app_identity.DEFAULT) -> Path:
    say("Freezing the server with PyInstaller")
    out = build / "pyinstaller-dist"
    run([py, "-m", "PyInstaller", "--noconfirm", "--clean", "--log-level", "WARN",
         "--distpath", out, "--workpath", build / "pyinstaller", spec])
    return out / server_name(app)


def check_frozen(frozen: Path, app: str = app_identity.DEFAULT) -> None:
    """The frozen server's `cli --help`, which imports the command line and through it the server and
    every module it needs, so a module the freeze left out stops the build here, as on Windows."""
    done = subprocess.run([str(frozen / server_name(app)), "cli", "--help"], capture_output=True, text=True,
                          encoding="utf-8", errors="replace", timeout=120)
    if done.returncode != 0:
        raise SystemExit(f"The frozen server did not start:\n{(done.stdout + done.stderr)[-2000:]}")
    say("The frozen server starts: its command line answered --help")


def add_typesetter(build: Path, frozen: Path, identity: str | None = None) -> Path:
    """The typesetter built for this Mac, arm64, put beside the frozen server and signed as its binaries are, then
    run on a one-line page with the fonts the bundle carries (typst1, 9 November 2026)."""
    helper = typeset_helper.place(typeset_helper.build(build), frozen)
    typeset_helper.sign_mac(helper, identity)
    made = typeset_helper.check(helper, typeset_helper.fonts_in(frozen))
    say(f"The typesetter is beside the server, {size_mb(helper):.1f} MB, and typeset a line ({made} bytes of PDF)")
    return helper


# ── 4. signing ────────────────────────────────────────────────────────────────────────────────

def developer_id() -> str | None:
    """The first Developer ID Application identity `security find-identity` lists, or None."""
    try:
        out = subprocess.run(["security", "find-identity", "-v", "-p", "codesigning"],
                             capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=60).stdout
    except (OSError, subprocess.TimeoutExpired):
        return None
    m = re.search(rf'"({IDENTITY}: [^"]+)"', out)
    return m.group(1) if m else None


def notary_ready() -> bool:
    """Whether notarytool has the profile NOTARY_PROFILE. notarytool reads it from the keychain
    itself, and nothing of it reaches this script."""
    try:
        return subprocess.run(["xcrun", "notarytool", "history", "--keychain-profile", NOTARY_PROFILE],
                              capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=120).returncode == 0
    except (OSError, subprocess.TimeoutExpired):
        return False


def signing(unsigned: bool) -> tuple[str | None, str]:
    """The identity to sign with, or None, and the one line that says which."""
    if unsigned:
        return None, "Unsigned, as asked: macOS asks once before it opens the app."
    identity = developer_id()
    if not identity:
        return None, (f"Unsigned: no {IDENTITY} identity in the keychain, so macOS asks once before "
                      "it opens the app.")
    if not notary_ready():
        return None, (f"Unsigned: no notarytool profile {NOTARY_PROFILE} on this Mac, so macOS asks "
                      "once before it opens the app.")
    return identity, f"Signed with {identity}, notarised and stapled."


def signing_env(identity: str | None) -> dict:
    """What Tauri's bundler signs the app with: the identity, with the hardened runtime Tauri gives a
    signed app, or nothing, when tauri.conf.json's ad hoc signature stands."""
    return {"APPLE_SIGNING_IDENTITY": identity} if identity else {}


def notarise(dmg: Path, identity: str) -> None:
    run(["codesign", "--force", "--timestamp", "--sign", identity, dmg])
    say("Notarising, which waits on Apple")
    run(["xcrun", "notarytool", "submit", dmg, "--keychain-profile", NOTARY_PROFILE, "--wait"])
    run(["xcrun", "stapler", "staple", dmg])


# ── 4. the window, its disk image and its update file ──────────────────────────────────────────

def apple_silicon(machine: str | None = None) -> bool:
    """Whether this Mac is an Apple Silicon one, the only kind the app is built on and for."""
    return (machine or platform.machine()) == "arm64"


def place(made: Path, dist: Path, name: str) -> Path:
    """A bundle Tauri made, put in `dist/` under the name it ships with, its links kept."""
    target = dist / name
    if target.is_dir():
        shutil.rmtree(target)
    else:
        target.unlink(missing_ok=True)
    run(["ditto", made, target])
    return target


def bundle_named(macos: Path, product: str) -> Path:
    """The `.app` Tauri made for `product` in its `macos` folder. The folder keeps the bundles of every
    earlier build of the same `--out` (Idiograph.app beside Idiograph Test.app), so the one built now is
    found by its name, never as the first `.app` there (testappfix, 9 November 2026)."""
    found = macos / f"{product}.app"
    if not found.is_dir():
        raise SystemExit(f"Tauri made no {found.name} in {macos}.")
    return found


def executable_of(app_path: Path, product: str) -> Path:
    """The app's binary: named for the product, `Idiograph Test` in the test app."""
    return app_path / "Contents" / "MacOS" / product


def size_mb(path: Path) -> float:
    if path.is_file():
        return path.stat().st_size / 1e6
    return sum(p.lstat().st_size for p in path.rglob("*") if p.is_file() and not p.is_symlink()) / 1e6


def print_list(app: str, scripts: bool = False, windows: bool = False) -> int:
    """`--list`: each file a build of `app` ships, its path in the bundle and where it comes from, a tab
    between. `--scripts`: the page's own scripts, a path a line, from the app's folder."""
    if scripts:
        for path in page_scripts(app):
            print(path.relative_to(TOOL).as_posix())
        return 0
    for dest, source in listing(app, windows):
        print(f"{dest}\t{source}")
    return 0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Build Idiograph.app, or Sift.app or Trace.app, its disk image and its update file.")
    ap.add_argument("--app", default=app_identity.DEFAULT, choices=list(app_identity.APPS),
                    help="the app to build, idiograph by default, sift or trace")
    ap.add_argument("--out", help="the folder build/ and dist/ go in, the app's own folder by default")
    ap.add_argument("--python", help="the Python 3.11 or later to build with, a python.org one by default")
    ap.add_argument("--unsigned", action="store_true", help="never sign, even with an identity")
    ap.add_argument("--test-app", action="store_true", help="the test app, Idiograph Test, for a check")
    ap.add_argument("--drive", action="store_true", help="with the drive feature a check of the window needs, never shipped")
    ap.add_argument("--this-mac", action="store_true", help="kept for older commands: every build is Apple Silicon's alone")
    # a check's own release, for the test app alone (18 October, the fourth Tauri build): another version,
    # its notes, and a throwaway key's public half and a manifest's address on this machine
    ap.add_argument("--version", help="the test app's version, in place of its own in versions.json")
    ap.add_argument("--whats-new", help="the test app's notes, in place of docs/whats-new.md")
    ap.add_argument("--update-key", help="a file holding the public half of a check's throwaway update key")
    ap.add_argument("--update-url", help="the address of a check's update manifest, on this machine")
    ap.add_argument("--build", help="the commit a daily build is made from, its short sha, shown in About (mac_daily.py)")
    ap.add_argument("--list", action="store_true", help="print what the build would ship, each file and where it comes from, and build nothing")
    ap.add_argument("--scripts", action="store_true", help="print the page's own scripts the build ships, for node --check, and build nothing")
    args = ap.parse_args(argv)
    if args.list or args.scripts:
        return print_list(args.app, scripts=args.scripts)
    if sys.platform != "darwin":
        raise SystemExit("The Mac app is built on a Mac.")
    if not apple_silicon():
        raise SystemExit("The Mac app is for Apple Silicon Macs alone, and is built on one.")
    if (args.version or args.whats_new or args.update_key or args.update_url) and not args.test_app:
        raise SystemExit("--version, --whats-new, --update-key and --update-url are for the test app alone.")
    if bool(args.update_key) != bool(args.update_url):
        raise SystemExit("--update-key and --update-url go together.")

    app = args.app
    out = Path(args.out).expanduser().resolve() if args.out else TOOL
    build, dist = out / "build", out / "dist"
    stage = build / "stage"
    stage.mkdir(parents=True, exist_ok=True)
    dist.mkdir(parents=True, exist_ok=True)

    python = choose_python(args.python)
    py = build_venv(build, python)
    if ships_demo(app):
        stage_demo(stage)
    stage_config(stage, py, app)
    stage_build(stage, args.build)
    version = args.version or app_version(py, app)
    identity, line = signing(args.unsigned)
    frozen = pyinstaller(py, build, write_spec(build, stage, version, identity, app), app)
    check_frozen(frozen, app)
    add_typesetter(build, frozen, identity)

    env = dict(os.environ, **signing_env(identity))
    update = window.test_update(Path(args.update_key).read_text(encoding="utf-8"), args.update_url) if args.update_key else None
    made = window.bundle(frozen, build, version, ["app"], test=args.test_app, universal=False,
                         features=["drive"] if args.drive else [], env=env, update=update,
                         whats_new=Path(args.whats_new).resolve() if args.whats_new else None, app=app)
    product = window.overrides(version, args.test_app, app=app).get("productName", NAME)
    app_path = place(bundle_named(made / "macos", product), dist, f"{product}.app")
    dmg = window.disk_image(app_path, dist / f"{product}.dmg", py, product, build / "dmg")
    update = window.update_tarball(app_path, dist / f"{product}.app.tar.gz")
    if identity:
        notarise(dmg, identity)

    executable = executable_of(app_path, product)
    archs = subprocess.run(["lipo", "-archs", executable], capture_output=True, text=True, encoding="utf-8",
                           errors="replace").stdout.strip()
    with open(app_path / "Contents" / "Info.plist", "rb") as fh:
        shown = plistlib.load(fh).get("CFBundleShortVersionString")
    say(f"Built {app_path}, version {shown}, {archs or 'unknown architecture'}, {size_mb(app_path):.0f} MB")
    say(f"Built {dmg}, {size_mb(dmg):.0f} MB, and {update.name}, {size_mb(update):.0f} MB")
    if archs != ARCH:
        raise SystemExit(f"{app_path.name} is for {archs or 'no architecture'}, not {ARCH} alone.")
    say(line)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
