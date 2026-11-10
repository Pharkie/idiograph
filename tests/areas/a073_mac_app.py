from __future__ import annotations

import inspect
import json
import re
import shutil
import sys
from pathlib import Path

import make_app
import workbook as wb_mod
from workbook import WorkbookError

from . import support
from .support import DEMO_SHEET, STUDY_FOLDERS, TOOL, check, skip
import idiograph_routes


def test_mac_app(scratch):
    print("\n73. The Mac app: where its files live, the demo copied and reset from the bundle, no root and "
          "Choose folder, the launcher, the build script and the words")
    import hashlib
    import importlib.util
    import subprocess
    import server as server_mod

    def load(name):
        spec = importlib.util.spec_from_file_location(f"idiograph_{name}", support.source("packaging") / f"{name}.py")
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        return mod

    def tree(folder):
        return {p.relative_to(folder).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
                for p in sorted(Path(folder).rglob("*")) if p.is_file()}

    src = inspect.getsource(server_mod)
    js = support.text("family/static/shell.js", "apps/idiograph/static/distil.js")
    fn = lambda text, name: text.split(f"function {name}(", 1)[1].split("\n}", 1)[0] if f"function {name}(" in text else ""

    # ── 1. one function decides where the files go, and run from the repo nothing moves
    home = scratch / "mac-home"
    repo = server_mod.app_paths(False, home, "darwin")
    frozen = server_mod.app_paths(True, home, "darwin")
    app_support = home / "Library" / "Application Support" / "Idiograph"
    check("73: run from the repo, the settings, the recent list, the key file and the demo are beside the app as before",
          repo["config"] == support.source("config.json") and repo["state"] == support.source("state.json")
          and repo["env"] == support.source(".env") and repo["demo"] == support.source("demo") == repo["shipped_demo"]
          and repo["base"] == server_mod.source_base(TOOL) and repo["data"] == TOOL
          and not server_mod.FROZEN and server_mod.PATHS == server_mod.app_paths(False)
          and server_mod.REPO_ROOT == server_mod.source_base(TOOL) and server_mod.ENV_PATH == support.source(".env")
          and server_mod.DEMO_DIR == support.source("demo") == server_mod.SHIPPED_DEMO, str(repo["config"].parent.name))
    check("73: run from the Mac app, every file it writes is under Application Support, the logs under Logs either way",
          frozen["config"] == app_support / "config.json" and frozen["state"] == app_support / "state.json"
          and frozen["env"] == app_support / ".env" and frozen["demo"] == app_support / "demo" and frozen["base"] == app_support
          and frozen["shipped_demo"] == support.source("demo") and frozen["logs"] == home / "Library" / "Logs" / "Idiograph"
          and repo["logs"] == frozen["logs"]
          and all(not str(v).startswith(str(TOOL)) for k, v in frozen.items() if k != "shipped_demo"))
    check("73: the module takes every one of those paths from app_paths, and frozen is the bundle's own flag",
          'FROZEN = bool(getattr(sys, "frozen", False))' in src and "PATHS = app_paths()" in src
          and all(line in src for line in ('REPO_ROOT = PATHS["base"]', 'CONFIG_PATH = PATHS["config"]',
                                           'STATE_PATH = PATHS["state"]', 'DEMO_DIR = PATHS["demo"]',
                                           'SHIPPED_DEMO = PATHS["shipped_demo"]', 'ENV_PATH = PATHS["env"]'))
          and 'HERE / "config.json"' not in src.split("def app_paths(", 1)[0])

    # ── 2. the first run copies the shipped settings and the demo, and Reset restores from the bundle
    bundle = scratch / "mac-bundle"
    shutil.rmtree(bundle, ignore_errors=True)
    shutil.copytree(support.source("demo"), bundle / "demo",
                    ignore=shutil.ignore_patterns("*.themes.json", "_Archive", "*.m4a", "Working"))
    shutil.copytree(support.source("demo/pristine/Working"), bundle / "demo" / "pristine" / "Working")
    recording = bundle / "demo" / "Juno" / "Source" / "Initial" / "Source" / "Juno-Initial.m4a"
    recording.parent.mkdir(parents=True, exist_ok=True)
    recording.write_bytes(b"not really audio, a stand-in for the recording the build ships")
    (bundle / "config.json").write_text(json.dumps(server_mod.shipped_config(), indent=2), encoding="utf-8")
    shipped = tree(bundle)
    repo_demo = tree(support.source("demo"))
    shutil.rmtree(home, ignore_errors=True)
    paths = dict(frozen, shipped_demo=bundle / "demo")
    first = server_mod.first_run(paths)
    copied_config = json.loads((app_support / "config.json").read_text(encoding="utf-8")) if (app_support / "config.json").exists() else {}
    work = app_support / "demo" / "Juno" / "Juno - EN & ES.xlsx"
    check("73: the first run makes the folder, copies the shipped settings with no project, and the demo with its recording",
          app_support / "config.json" in first and copied_config.get("projects") == [] and "root" not in copied_config
          and copied_config.get("interviewer") == server_mod.defaults()["interviewer"]
          and work.is_file() and (app_support / "demo" / "pristine" / "Juno - EN & ES.xlsx").is_file()
          and (app_support / "demo" / recording.relative_to(bundle / "demo")).read_bytes() == recording.read_bytes()
          and (app_support / "demo" / "idiograph-project.json").is_file(), f"{len(first)} files")
    work.write_bytes(work.read_bytes() + b"")
    marker = app_support / "demo" / "Juno" / "Working" / "worked.txt"
    marker.parent.mkdir(parents=True, exist_ok=True)
    marker.write_text("a demo worked on", encoding="utf-8")
    (app_support / "config.json").write_text(json.dumps({"root": "", "interviewer": "Quill"}), encoding="utf-8")
    again = server_mod.first_run(paths)
    check("73: a later run copies nothing over what is there, settings and demo alike",
          again == [] and json.loads((app_support / "config.json").read_text(encoding="utf-8"))["interviewer"] == "Quill"
          and marker.is_file(), str(again))
    check("73: run from the repo the first run copies nothing and writes nothing",
          server_mod.first_run(repo) == [] and tree(support.source("demo")) == repo_demo)
    check("73: main readies the folder before the config fallback it always had",
          "start_up(args)" in inspect.getsource(server_mod.main)
          and "first_run(PATHS, CONFIG_PATH)\n" in inspect.getsource(server_mod.start_up)
          and "    if not CONFIG_PATH.exists():\n        save_json(CONFIG_PATH, shipped_config())"
          in inspect.getsource(server_mod.start_up).split("first_run(PATHS, CONFIG_PATH)\n", 1)[-1])

    kept = (server_mod.DEMO_DIR, server_mod.DEMO_CASE, server_mod.DEMO_WORKBOOK, server_mod.SHIPPED_DEMO)
    import make_demo
    made = (make_demo.CASE, make_demo.WORKBOOK, make_demo.PRISTINE)
    try:
        server_mod.DEMO_DIR, server_mod.SHIPPED_DEMO = app_support / "demo", bundle / "demo"
        server_mod.DEMO_CASE = server_mod.DEMO_DIR / "Juno"
        server_mod.DEMO_WORKBOOK = server_mod.DEMO_CASE / "Juno - EN & ES.xlsx"
        wb_mod.save_turn(server_mod.DEMO_WORKBOOK, DEMO_SHEET, 3, "A statement written in the app", None, None)
        held = app_support / "demo" / "Juno" / "Working" / "Juno - EN & ES.themes.json"
        held.write_text("{}", encoding="utf-8")
        copy = app_support / "demo" / recording.relative_to(bundle / "demo")
        copy.unlink()
        answer = idiograph_routes.api_reset_demo({})
        pristine = bundle / "demo" / "pristine"
        check("73: Reset demo restores the workbook and its sidecar from the bundle's copy, and the recording with them",
              answer.get("reset") is True
              and server_mod.DEMO_WORKBOOK.read_bytes() == (pristine / "Juno - EN & ES.xlsx").read_bytes()
              and (app_support / "demo" / "Juno" / "Working" / "Juno - EN & ES.progress.json").read_bytes()
              == (pristine / "Working" / "Juno - EN & ES.progress.json").read_bytes()
              and held.read_bytes() == (pristine / "Working" / "Juno - EN & ES.themes.json").read_bytes()
              and copy.read_bytes() == recording.read_bytes())
        copy.unlink()
        building = idiograph_routes.ensure_demo_recording()
        check("73: a recording gone missing comes back from the bundle, and nothing is spoken or built",
              building is False and copy.is_file() and not idiograph_routes._demo_building)
        check("73: neither touched the bundle, the repo's demo or make_demo's own paths",
              tree(bundle) == shipped and tree(support.source("demo")) == repo_demo
              and (make_demo.CASE, make_demo.WORKBOOK, make_demo.PRISTINE) == made
              and "make_demo.reset_all(shipped / \"pristine\", live)" in inspect.getsource(idiograph_routes.api_reset_demo))
    finally:
        server_mod.DEMO_DIR, server_mod.DEMO_CASE, server_mod.DEMO_WORKBOOK, server_mod.SHIPPED_DEMO = kept

    # ── 3. the shipped config, and no project at all
    check("73: the shipped config is the defaults with no project, and no run defaults to a study's folder",
          server_mod.shipped_config() == dict(server_mod.defaults(), projects=[])
          and server_mod.defaults()["projects"] == [] and "root" not in server_mod.defaults()
          and not any(w in src for w in STUDY_FOLDERS))
    saved = (server_mod.CONFIG_PATH, server_mod.ROOT_OVERRIDE, server_mod.STATE_MEMORY, server_mod.PLATFORM,
             server_mod.PICK_FOLDER)
    cfg_file = scratch / "mac-config.json"
    cfg_file.write_text(json.dumps(dict(server_mod.shipped_config(), interviewer="Quill")), encoding="utf-8")
    try:
        server_mod.CONFIG_PATH, server_mod.ROOT_OVERRIDE, server_mod.STATE_MEMORY = cfg_file, None, {"recent": []}
        server_mod.PLATFORM = "darwin"
        cases = idiograph_routes.api_cases({})
        stray = server_mod.REPO_ROOT / "idiograph-project.json"
        before = stray.exists()
        try:
            idiograph_routes.api_project({"name": "A project with nowhere to live"})
            refused = False
        except WorkbookError:
            refused = True
        check("73: with no project the case list is empty, says so through an empty root, and offers the dialog on a Mac",
              cases["cases"] == [] and cases["root"] == "" and cases["choose"] is True and cases["recent"] == []
              and cases["projects"] == [] and cases["participants"] == [] and cases["demo"]
              and cases["project"]["root"] == "" and cases["project"]["name"] == "",
              f"root {cases['root']!r}")
        check("73: with no project nothing but the demo is reachable, and the app's own folder is never taken for a root",
              server_mod.within_root(server_mod.DEMO_WORKBOOK) and not server_mod.within_root(support.source("config.json"))
              and not server_mod.within_root(TOOL.parent.parent / "x.xlsx")
              and idiograph_routes.project_root() is None and idiograph_routes.day_workbooks(server_mod.config()) == []
              and refused and stray.exists() == before)
        server_mod.PLATFORM = "linux"
        check("73: off a Mac the case list says there is no dialog", idiograph_routes.api_cases({})["choose"] is False)

        # ── 4. the picker route, which a page from before the projects asks
        held = cfg_file.read_bytes()
        try:
            idiograph_routes.api_choose_root({})
            off = None
        except WorkbookError as exc:
            off = str(exc)
        check("73: off a Mac the picker route refuses in one line, naming the typed path, and writes nothing",
              off == "The folder dialog is on a Mac only. Type the folder's path." and cfg_file.read_bytes() == held)
        server_mod.PLATFORM = "darwin"
        asked = []
        server_mod.PICK_FOLDER = lambda: asked.append(1)
        cancelled = idiograph_routes.api_choose_root({})
        check("73: a cancelled dialog changes nothing", cancelled == {"chosen": False} and asked == [1]
              and cfg_file.read_bytes() == held)
        chosen = scratch / "mac-cases"
        chosen.mkdir(exist_ok=True)
        server_mod.PICK_FOLDER = lambda: chosen
        picked = idiograph_routes.api_choose_root({})
        stored = json.loads(cfg_file.read_text(encoding="utf-8"))
        check("73: a folder chosen is added as a project, every other setting as it was, and the case list reads it",
              picked == {"chosen": True, "root": str(chosen.resolve())}
              and stored["projects"] == [{"root": str(chosen.resolve())}] and "root" not in stored
              and stored["interviewer"] == "Quill" and idiograph_routes.api_cases({})["root"] == str(chosen.resolve()),
              str(picked))
        other = scratch / "mac-other"
        case_dir = other / "P9 - {}-{}".format("Nobody", "Second")
        case_dir.mkdir(parents=True, exist_ok=True)
        server_mod.PICK_FOLDER = lambda: case_dir
        idiograph_routes.api_choose_root({})
        stored = json.loads(cfg_file.read_text(encoding="utf-8"))
        check("73: a case folder in the folder chosen is written as a glob on its pseudonym",
              stored["projects"][-1]["root"].endswith("P9 - Nobody*") and "Second" not in cfg_file.read_text(encoding="utf-8")
              and server_mod.resolve_path(stored["projects"][-1]["root"]) == case_dir.resolve(),
              stored["projects"][-1]["root"].rsplit("/", 1)[-1])
        server_mod.PICK_FOLDER = lambda: scratch / "mac-nowhere"
        check("73: a folder that is not there changes nothing", idiograph_routes.api_choose_root({}) == {"chosen": False})
    finally:
        (server_mod.CONFIG_PATH, server_mod.ROOT_OVERRIDE, server_mod.STATE_MEMORY, server_mod.PLATFORM,
         server_mod.PICK_FOLDER) = saved
    check("73: the route is in the table, after the project, and takes a POST alone, since it opens a dialog",
          server_mod.ROUTES.get("/api/choose-root") is idiograph_routes.api_choose_root
          and "/api/choose-root" in server_mod.POST_ONLY and "/api/projects" in server_mod.POST_ONLY
          and list(server_mod.ROUTES).index("/api/choose-root") == list(server_mod.ROUTES).index("/api/project") + 1
          and list(server_mod.ROUTES).index("/api/projects") == list(server_mod.ROUTES).index("/api/choose-root") + 1)

    # ── 5. the page: the line and Add project with no project, and Add project under Projects
    draw = fn(js, "openFolderPress")
    add_home = fn(js, "addFromHome")
    choose = fn(js, "addProject")
    check("73: Open project folder asks the server, with the dialog or the typed path, and a cancel adds nothing",
          "api('/api/projects', { op: 'add', path })\n      : await picking((chosen) => api('/api/projects', { op: 'add', path: chosen }), btn, PICK_SAYS.project)" in choose
          and "return data && data.added ? data : null;" in choose
          and "const data = await addProject(path, $('add-project-home'));" in add_home and "if (!data) return;" in add_home)
    node = shutil.which("node")
    if not node:
        skip("72: Open project folder in node", "node is not installed")
    else:
        script = scratch / "mac-no-root.js"
        script.write_text(
            "const S = {};\n"
            "const els = {};\n"
            "const el = (id) => (els[id] = els[id] || { id, hidden: false, value: '', onclick: null, onkeydown: null, focus() {} });\n"
            "const $ = (id) => el(id);\n"
            "const asked = [];\n"
            "const kept = [];\n"
            "async function addProject(path) { asked.push(path === undefined ? 'dialog' : path);\n"
            "  return path === '/tmp/Cases' ? { added: true, project: { id: 'cases' } } : null; }\n"
            "function homeKeep(id) { kept.push(id); }\n"
            "function loadLibrary() { return Promise.resolve(); }\n"
            "function say() {}\n"
            "function openFolderPress(" + draw + "\n}\n"
            "async function addFromHome(" + add_home + "\n}\n"
            "const at = async (choose) => { S.chooseRoot = choose; $('add-home-typed').hidden = true; openFolderPress(); await null;\n"
            "  const field = !$('add-home-typed').hidden; await addFromHome('/tmp/Cases');\n"
            "  return [field, asked.splice(0), kept.splice(0)]; };\n"
            "(async () => { console.log(JSON.stringify({ mac: await at(true), other: await at(false) })); })();\n",
            encoding="utf-8")
        run = subprocess.run([node, str(script)], capture_output=True, text=True, encoding="utf-8")
        if run.returncode != 0:
            check("73: Open project folder runs in node", False, run.stderr.strip()[:400])
        else:
            o = json.loads(run.stdout)
            check("73: in node, on a Mac Open project folder opens the dialog, and a folder added opens on its page",
                  o["mac"] == [False, ["dialog", "/tmp/Cases"], ["cases"]], str(o["mac"]))
            check("73: in node, off a Mac Open project folder shows the field for the folder's path, and Add sends it",
                  o["other"] == [True, ["/tmp/Cases"], ["cases"]], str(o["other"]))

    # ── 6. the launcher inside the bundle
    launcher = load("mac_launcher")
    launch_src = support.source("packaging/mac_launcher.py").read_text(encoding="utf-8")
    check("73: the launcher splits its own arguments from the server's, and drops the Finder's -psn_",
          launcher.split_args(["--port", "8789", "--no-browser", "-psn_0_123"]) == (False, "8789", ["--no-browser"])
          and launcher.split_args(["--serve", "--port=8790", "--root", "x"]) == (True, "8790", ["--root", "x"])
          and launcher.split_args([]) == (False, None, []))
    app_server = "/Applications/Idiograph.app/Contents/MacOS/Idiograph --serve --port 8765"
    check("73: a server is the app's own only when it is the bundle's executable run with --serve",
          launcher.is_ours(app_server)
          and launcher.is_ours("/Users/a b/Apps/Idiograph.app/Contents/MacOS/Idiograph --serve --port 8766 --no-browser")
          and not launcher.is_ours("/x/.venv/bin/python3 Tools/idiograph/server.py --port 8765")
          and not launcher.is_ours("/Applications/Idiograph.app/Contents/MacOS/Idiograph")
          and not launcher.is_ours("/usr/bin/python3 -m http.server 8765"))
    commands = {1: "/x/.venv/bin/python3 Tools/idiograph/server.py --port 8765", 2: app_server, 3: "nginx"}
    real_command = launcher.command_of
    try:
        launcher.command_of = lambda pid: commands.get(pid, "")
        picks = {
            "free": launcher.choose_port(8765, {}),
            "repo": launcher.choose_port(8765, {8765: {1}}),
            "ours": launcher.choose_port(8765, {8765: {1}, 8766: {3}, 8767: {2}}),
            "full": launcher.choose_port(8765, {p: {3} for p in range(8765, 8765 + launcher.SPAN + 1)}),
        }
    finally:
        launcher.command_of = real_command
    # past another program the next free port that is none of the family's three, Sift's 8766 and Trace's 8767
    # left to them since the three-app split (20 October)
    check("73: port 8765 first, the next free one past another program, and the app's own server wherever it runs",
          picks == {"free": (8765, False), "repo": (8768, False), "ours": (8767, True), "full": (None, False)},
          str(picks))
    start = inspect.getsource(launcher.start_server)
    check("73: a start runs detached, logs in ~/Library/Logs/Idiograph and keeps its pid there, waiting ten seconds",
          launcher.logs_dir(home) == frozen["logs"] and "start_new_session=True" in start
          and 'logs / "idiograph.log"' in start and 'logs / f"idiograph-{port}.pid"' in start
          and "time.monotonic() + 10" in start and 'PYINSTALLER_RESET_ENVIRONMENT="1"' in start
          and "splitlines(True)[-12:]" in start
          and launcher.server_command(8789, ["--no-browser"])
          == [sys.executable, str(support.source("packaging/mac_launcher.py").resolve()), "--serve", "--port", "8789", "--no-browser"])
    stop = inspect.getsource(launcher.stop_server)
    check("73: Stop signals only what listens on the port, and only the app's own server, TERM then KILL",
          "for sig in (15, 9):" in stop and "if is_ours(command_of(pid)):" in stop
          and "pkill" not in launch_src and "killall" not in launch_src
          and '"-iTCP:{first}-{last}", "-sTCP:LISTEN"' in launch_src)
    check("73: every launch leaves its date and its outcome in /tmp, with no path",
          launcher.TRACE == Path("/tmp/idiograph-launch.log") and '"launched", final=False' in launch_src
          and 'f"ended with no outcome, exit {code}"' in launch_src
          and not [ln for ln in launch_src.splitlines() if "trace.line(" in ln and re.search(r"\{(log|logs|pidfile)\}", ln)])
    serve = inspect.getsource(launcher.serve)
    check("73: the server runs in the bundle with certifi's certificates, and reads its options as from the repo",
          'os.environ.setdefault("SSL_CERT_FILE", certifi.where())' in serve and "server.main()" in serve
          and "--serve" not in str(launcher.split_args(["--serve", "--port", "1"])[2]))

    # ── 7. the build script names its pieces, and its outputs are gitignored
    build = load("build_mac")
    build_src = support.source("packaging/build_mac.py").read_text(encoding="utf-8")
    local = {p.stem for p in support.code_files("*.py")}
    imported = set(re.findall(r"^\s*import (\w+)", src, flags=re.M)) | set(re.findall(r"^\s*from (\w+) import", src, flags=re.M))
    check("73: the build freezes the launcher with every module the server imports, and ships the page, the guidance and the licences",
          build.ENTRY == support.source("packaging/mac_launcher.py") and (imported & local) <= set(build.MODULES)
          and set(build.MODULES) <= local and all(Path(found).exists() for app in ("idiograph", "sift", "trace")
                                                  for found, _folder in build.data_files(app))
          and {"guidance.md", "pet_guidance.md", "themes_guidance.md", "NOTICE.md"}
          <= {Path(found).name for found, _folder in build.data_files("idiograph")}
          and not {"guidance.md", "pet_guidance.md"} & {Path(found).name for found, _folder in build.data_files("sift")},
          ", ".join(sorted((imported & local) - set(build.MODULES))) or f"{len(build.MODULES)} modules")
    check("73, updated 9 November (relfix): the build venv is its own, with PyInstaller, openpyxl, certifi and "
          "cryptography pinned, made from a Python that runs as arm64, a python.org one when there is one",
          [p.split("==")[0] for p in build.PINS] == ["pyinstaller", "openpyxl", "et_xmlfile", "certifi", "cryptography"]
          and all("==" in p for p in build.PINS) and 'venv = build / "venv"' in build_src
          and build.FRAMEWORKS == Path("/Library/Frameworks/Python.framework/Versions")
          and build.runs_arm64("macosx-11.0-arm64") and build.runs_arm64("macosx-10.13-universal2")
          and not build.runs_arm64("macosx-10.13-x86_64") and ".venv" not in build_src.split('"""', 2)[2])
    check("73, 9 November (relfix): the Mac app is for Apple Silicon alone, built on an Apple Silicon Mac and refused "
          "on an Intel one",
          build.ARCH == "arm64" and build.apple_silicon("arm64") and not build.apple_silicon("x86_64")
          and "universal=False" in build_src and not hasattr(build, "both_archs"))
    (scratch / "mac-spec").mkdir(exist_ok=True)
    spec_text = build.write_spec(scratch / "mac-spec", scratch / "mac-stage", "0.9.0").read_text(encoding="utf-8")
    check("73, updated 9 November (relfix): the spec is one folder, windowed, arm64, with the static page, the "
          "demo and the config as data, the server the window runs, with no app of PyInstaller's own around it",
          "target_arch='arm64'" in spec_text and "console=False" in spec_text and "argv_emulation=False" in spec_text
          and "'static')" in spec_text and "'demo')" in spec_text and "config.json" in spec_text
          and "COLLECT(" in spec_text and "BUNDLE(" not in spec_text and "codesign_identity=None" in spec_text
          and "'certifi'" in spec_text)
    window_conf = json.loads(support.source("packaging/tauri/src-tauri/tauri.conf.json").read_text(encoding="utf-8"))
    window_src = support.source("packaging/tauri/bundle.py").read_text(encoding="utf-8")
    window_mod = build.window
    check("73, updated 17 October (173): the window's Info.plist is Tauri's, its identity the repo launcher's, its "
          "version the server's, set as it builds, and its floor the old app's, so the Dock treats them alike",
          window_conf["identifier"] == make_app.INFO["CFBundleIdentifier"]
          and window_conf["bundle"]["macOS"]["minimumSystemVersion"] == make_app.INFO["LSMinimumSystemVersion"] == "12.0"
          and window_mod.overrides("0.9.0")["version"] == "0.9.0" and "version = args.version or app_version(py, app)" in build_src
          and "--version, --whats-new, --update-key and --update-url are for the test app alone." in build_src)
    check("73, updated 18 October (175): the app is Tauri's bundler's and the image dmgbuild's, pinned, the app and a "
          "link to /Applications laid out in the image itself, so no Finder window is scripted on the screen",
          'window.bundle(frozen, build, version, ["app"]' in build_src and 'CI="true"' in window_src
          and "window.disk_image(app" in build_src and '"dmgbuild==1.6.7"' in build_src
          and "create-dmg" not in build_src and "hdiutil" not in build_src and "osascript" not in window_src)
    real = (build.developer_id, build.notary_ready)
    try:
        build.developer_id = lambda: None
        build.notary_ready = lambda: (_ for _ in ()).throw(AssertionError("asked notarytool with no identity"))
        none = build.signing(False)
        build.developer_id = lambda: "Developer ID Application: Someone (ABC123)"
        build.notary_ready = lambda: False
        no_profile = build.signing(False)
        build.notary_ready = lambda: True
        both = build.signing(False)
        asked_off = build.signing(True)
    finally:
        build.developer_id, build.notary_ready = real
    check("73: it signs and notarises only with an identity and the notarytool profile, and else says unsigned in one line",
          none[0] is None and none[1].startswith("Unsigned: no Developer ID Application identity")
          and no_profile[0] is None and build.NOTARY_PROFILE in no_profile[1]
          and both[0] == "Developer ID Application: Someone (ABC123)" and asked_off[0] is None
          and all("\n" not in line for _, line in (none, no_profile, both, asked_off)))
    check("73, updated 17 October (173): the only keychain command is find-identity, stapling follows notarising, "
          "and an identity signs the server's every binary through PyInstaller and the app through Tauri",
          '["security", "find-identity", "-v", "-p", "codesigning"]' in build_src
          and "find-generic-password" not in build_src and "find-generic-password" not in launch_src
          and build_src.index('"notarytool", "submit"') < build_src.index('"stapler", "staple"')
          and "codesign_identity={identity!r}" in build_src
          and build.signing_env("Developer ID Application: Someone (ABC123)") == {"APPLE_SIGNING_IDENTITY": "Developer ID Application: Someone (ABC123)"}
          and build.signing_env(None) == {})
    ignored = [line.strip() for line in support.source(".gitignore").read_text(encoding="utf-8").splitlines()]
    check("73: build/ and dist/ are gitignored, and the script builds there unless told otherwise",
          "build/" in ignored and "dist/" in ignored and "else TOOL" in inspect.getsource(build.main)
          and 'build, dist = out / "build", out / "dist"' in build_src)
    check("73: the shipped stage carries the demo as Reset leaves it, its recording, and a config with no root",
          'shutil.copyfile(src / "pristine" / f"{stem}.xlsx", into / name / f"{stem}.xlsx")' in build_src
          and 'shutil.copyfile(src / "pristine" / kept, into / kept)' in build_src and "(DEMO_GETS, DEMO_CODES)" in build_src
          and "shipped_config()" in build_src and 'raise SystemExit("The shipped config names a project, and it must not.")' in build_src
          and "make_demo.RECORDING = Path(sys.argv[2])" in build_src and '"*.themes.json", "_Archive"' in build_src)
