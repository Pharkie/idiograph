from __future__ import annotations

import hashlib
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

from . import support
from .support import TOOL, check
import idiograph_routes
import team_sync


def test_app_identity(scratch):
    print("\n219. One codebase choosing its app at start (20 October, the first build of the three-app split): "
          "--app picks Sift's or Trace's folders, files and port, a held port's fallback never takes another app's, "
          "Sift's and Trace's first start copies what they share from Idiograph's files once and only reads them, "
          "and every reader takes its version from versions.json. With no --app, Idiograph is as it was")
    import importlib.util

    import app_folders
    import app_identity
    import cli
    import mcp_server
    import server as server_mod

    base = scratch / "a219"
    shutil.rmtree(base, ignore_errors=True)
    base.mkdir(parents=True)

    def load(name, folder="packaging"):
        spec = importlib.util.spec_from_file_location(f"idiograph_219_{name}", TOOL / folder / f"{name}.py")
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        return mod

    def digest(*paths):
        return {str(p): hashlib.sha256(Path(p).read_bytes()).hexdigest() for p in paths}

    held = server_mod.app_held()
    # the starts below run Idiograph's start hook in this process: Working together's looks are left out, since a
    # thread of them left running would look at every later area's team projects as their settings file changes
    # under it, and send for them (winfix, 9 November 2026: area 343's ask went with four more on Windows)
    kept_looks = team_sync.start
    team_sync.start = lambda roots: None
    kept = (server_mod.ROOT_OVERRIDE, server_mod.STATE_MEMORY, server_mod.ARGV, list(sys.argv),
            server_mod.AppServer, os.environ.get(server_mod.STAY_OPEN))
    try:
        # ── the folders and files each app reads and writes
        home = base / "home"
        mac = {app: app_folders.folders("darwin", home, app=app) for app in app_identity.APPS}
        win = {app: app_folders.folders("win32", home, {"APPDATA": str(home / "Roaming"),
                                                        "LOCALAPPDATA": str(home / "Local"), "TEMP": str(home / "Temp")},
                                        app=app) for app in app_identity.APPS}
        check("each app keeps its own data and logs folders on a Mac and on Windows, Idiograph's where they were",
              mac["idiograph"] == app_folders.folders("darwin", home)
              and mac["sift"]["data"] == home / "Library" / "Application Support" / "Sift"
              and mac["trace"]["logs"] == home / "Library" / "Logs" / "Trace"
              and mac["sift"]["trace"].as_posix() == "/tmp/sift-launch.log"
              and win["sift"]["data"] == home / "Roaming" / "Sift" and win["trace"]["logs"] == home / "Local" / "Trace" / "Logs"
              and win["idiograph"]["data"] == home / "Roaming" / "Idiograph",
              str(mac["sift"]["data"]))
        frozen = {app: server_mod.app_paths(bundle=True, home=home, system="darwin", app=app) for app in app_identity.APPS}
        source = {app: server_mod.app_paths(bundle=False, home=home, system="darwin", app=app) for app in app_identity.APPS}
        check("app_paths takes the app: frozen each its own folder's config.json and state.json, from source "
              "config.sift.json and state.sift.json beside Idiograph's config.json, the key file beside the code shared",
              frozen["sift"]["config"] == mac["sift"]["data"] / "config.json"
              and frozen["trace"]["state"] == mac["trace"]["data"] / "state.json"
              and frozen["idiograph"]["config"] == mac["idiograph"]["data"] / "config.json"
              and source["idiograph"]["config"] == server_mod.HERE / "config.json"
              and source["idiograph"]["state"] == server_mod.HERE / "state.json"
              and source["sift"]["config"] == server_mod.HERE / "config.sift.json"
              and source["trace"]["state"] == server_mod.HERE / "state.trace.json"
              and source["sift"]["env"] == source["idiograph"]["env"] == server_mod.HERE / ".env",
              f"{source['sift']['config'].name}, {source['trace']['state'].name}")
        check("the frozen launcher's own name chooses the app, any other name Idiograph",
              app_identity.from_executable("/Applications/Sift.app/Contents/MacOS/Sift") == "sift"
              and app_identity.from_executable(r"C:\Users\x\AppData\Local\Trace\server\Trace-console.exe".replace("\\", "/")) == "trace"
              and app_identity.from_executable("/Applications/Idiograph Test.app/Contents/MacOS/Idiograph Test") == "idiograph"
              and app_identity.chosen([], frozen=True, executable="/x/Sift.app/Contents/MacOS/Sift") == "sift"
              and app_identity.chosen([], frozen=False, executable="/x/Sift.app/Contents/MacOS/Sift") == "idiograph"
              and app_identity.chosen(["--app", "trace"], frozen=True, executable="/x/Sift") == "trace"
              and app_identity.chosen(["--app=sift"]) == "sift")
        refused = False
        try:
            app_identity.check("distil")
        except app_identity.UnknownApp:
            refused = True
        code, _out, err = cli.run(["--app", "distil", "cases"])
        check("an app that is none of the three is refused, on the command line in one line", refused and code == 2
              and "no app called distil" in err, err.strip())

        # ── the port each server takes, and a held port's fallback
        made = []

        class Stand:
            def __init__(self, address, handler):
                made.append(address)
                self.socket = None

            def serve_forever(self):
                raise KeyboardInterrupt

            def server_close(self):
                pass

        server_mod.AppServer = Stand
        os.environ[server_mod.STAY_OPEN] = "1"
        root = base / "root"
        root.mkdir()

        def start(folder, *words):
            server_mod.app_back(held)
            server_mod.ROOT_OVERRIDE, server_mod.STATE_MEMORY = None, None
            sys.argv = ["server.py", "--no-browser", "--root", str(root), "--config", str(folder), *words]
            server_mod.main()
            return made[-1][1], server_mod.APP, server_mod.STATE_MEMORY

        # Idiograph's settings and recent list beside the run's own settings file, invented
        trial = base / "trial"
        trial.mkdir()
        idio_cfg = {"projects": [{"root": str(base / "kites")}], "interviewer": "Ada", "ai_prompt": "Idiograph's own prompt",
                    "corpus": "", "corpus_exclude": [], "gravity_reference": "",
                    "ai_suggest": True, "ai_provider": "local", "model": "a-model", "local_url": "http://127.0.0.1:9",
                    "local_model": "kite-model", "celebrations": False, "sound": True, "quit_when_closed": False,
                    "databases": [{"name": "Kite Index", "platform": "Kites", "by": "export"}],
                    "sift_email": "kites@example.org", "zotero": {"library": "group", "group_id": "4242"}}
        idio_state = {"recent": [{"path": "kites/Ada.xlsx"}],
                      "sift_reviews": [{"folder": str(base / "kite review"), "opened": 1, "run": "Run 2", "name": "Kites"},
                                       {"folder": "kite review two", "opened": 2}],
                      "trace_projects": [{"folder": str(base / "kite claims"), "opened": 3}]}
        (trial / "config.json").write_text(json.dumps(idio_cfg), encoding="utf-8")
        (trial / "state.json").write_text(json.dumps(idio_state), encoding="utf-8")
        before = digest(trial / "config.json", trial / "state.json")

        port, app, _ = start(trial / "own-idiograph.json")
        check("with no --app the server is Idiograph on 8765, its version Idiograph's, and nothing is copied",
              port == 8765 and app == "idiograph" and server_mod.VERSION == app_identity.version("idiograph")
              and app_identity.MARKER not in json.loads((trial / "own-idiograph.json").read_text(encoding="utf-8")),
              f"{app} on {port}")
        port_s, app_s, memory = start(trial / "config.sift.json", "--app", "sift")
        sift_cfg = json.loads((trial / "config.sift.json").read_text(encoding="utf-8"))
        port_t, app_t, memory_t = start(trial / "config.trace.json", "--app", "trace")
        trace_cfg = json.loads((trial / "config.trace.json").read_text(encoding="utf-8"))
        port_x, _, _ = start(trial / "config.sift.json", "--app", "sift", "--port", "8853")
        check("--app sift takes 8766 and --app trace 8767, and --port still wins",
              (port_s, app_s, port_t, app_t, port_x) == (8766, "sift", 8767, "trace", 8853),
              f"{port_s} {port_t} {port_x}")

        shared = ("ai_suggest", "ai_provider", "model", "local_url", "local_model", "celebrations", "sound", "quit_when_closed")
        check("Sift's first start takes the AI settings, Celebrations and Sound, the closing tick, the databases, the "
              "Unpaywall email and the Zotero library from Idiograph's settings, and none of Idiograph's own",
              all(sift_cfg.get(k) == idio_cfg[k] for k in shared + ("databases", "sift_email", "zotero"))
              and sift_cfg.get("projects") == [] and sift_cfg.get("interviewer") != "Ada"
              and sift_cfg.get("ai_prompt") != "Idiograph's own prompt" and sift_cfg.get(app_identity.MARKER),
              ", ".join(k for k in shared if sift_cfg.get(k) != idio_cfg[k]))
        check("and Sift's projects with the run each had open, never the recent cases or Trace's projects",
              memory and memory.get("sift_reviews") == idio_state["sift_reviews"] and memory.get("recent") == []
              and "trace_projects" not in memory, json.dumps((memory or {}).get("sift_reviews"))[:120])
        check("Trace's first start takes the shared settings and Trace's projects, never Sift's settings or projects",
              all(trace_cfg.get(k) == idio_cfg[k] for k in shared) and "sift_email" not in trace_cfg
              and "databases" not in trace_cfg and memory_t.get("trace_projects") == idio_state["trace_projects"]
              and "sift_reviews" not in memory_t)
        idio_keys = set(server_mod.defaults("idiograph")) - set(server_mod.DEFAULTS)
        check("since the sixth build Sift's and Trace's settings files hold no setting of Idiograph's, its defaults "
              "Idiograph's alone, nor Trace's any of Sift's",
              idio_keys and not idio_keys & set(sift_cfg) and not idio_keys & set(trace_cfg)
              and {"interviewer", "corpus", "themes", "nudges"} <= idio_keys,
              str(sorted(idio_keys & (set(sift_cfg) | set(trace_cfg)))))
        check("Idiograph's settings and recent list are byte for byte as they were, every first start only reading them",
              digest(trial / "config.json", trial / "state.json") == before)

        # once: a later start copies nothing, though Idiograph's settings have changed since
        sift_cfg["sift_email"] = "his-own@example.org"
        (trial / "config.sift.json").write_text(json.dumps(sift_cfg), encoding="utf-8")
        (trial / "config.json").write_text(json.dumps(dict(idio_cfg, sift_email="later@example.org", sound=False)),
                                           encoding="utf-8")
        start(trial / "config.sift.json", "--app", "sift")
        again = json.loads((trial / "config.sift.json").read_text(encoding="utf-8"))
        check("the copy is made once: a second start of Sift keeps its own settings, the marker there",
              again.get("sift_email") == "his-own@example.org" and again.get("sound") is True
              and again.get(app_identity.MARKER) == sift_cfg[app_identity.MARKER])

        # a run given --config and no --root keeps its recent list beside that file, never the repo's
        alone = base / "alone"
        alone.mkdir()
        (alone / "config.json").write_text(json.dumps(idio_cfg), encoding="utf-8")
        (alone / "state.json").write_text(json.dumps(idio_state), encoding="utf-8")
        alone_before = digest(alone / "config.json", alone / "state.json")
        kept_fill = idiograph_routes.fill_demo
        idiograph_routes.fill_demo = lambda: []
        where = {}
        try:
            for app, own in (("idiograph", "own.json"), ("sift", "config.sift.json"), ("trace", "config.trace.json")):
                server_mod.app_back(held)
                server_mod.ROOT_OVERRIDE, server_mod.STATE_MEMORY = None, None
                sys.argv = ["server.py", "--no-browser", "--config", str(alone / own), "--app", app]
                server_mod.main()
                where[app] = server_mod.STATE_PATH
        finally:
            idiograph_routes.fill_demo = kept_fill

        def kept_list(name):
            path = alone / name
            return json.loads(path.read_text(encoding="utf-8")) if path.is_file() else {}

        check("a run given --config and no --root keeps its recent list beside that file, each app under its own "
              "name, Sift's and Trace's first starts writing there, never beside the code",
              where == {"idiograph": alone.resolve() / "state.json", "sift": alone.resolve() / "state.sift.json",
                        "trace": alone.resolve() / "state.trace.json"}
              and kept_list("state.sift.json").get("sift_reviews") == idio_state["sift_reviews"]
              and kept_list("state.trace.json").get("trace_projects") == idio_state["trace_projects"]
              and all(Path(TOOL).resolve() not in Path(p).resolve().parents for p in where.values()),
              json.dumps({k: str(v) for k, v in where.items()}))
        check("and Idiograph's settings and recent list beside it are only read",
              digest(alone / "config.json", alone / "state.json") == alone_before)

        # a frozen app's own folder: a relative project folder made whole, and the key file copied once
        server_mod.app_back(held)
        server_mod.STATE_MEMORY = None
        idio_data, sift_data = mac["idiograph"]["data"], mac["sift"]["data"]
        idio_data.mkdir(parents=True)
        sift_data.mkdir(parents=True)
        (idio_data / "config.json").write_text(json.dumps(idio_cfg), encoding="utf-8")
        (idio_data / "state.json").write_text(json.dumps(idio_state), encoding="utf-8")
        (idio_data / ".env").write_text("INVENTED_SETTING=kites\n", encoding="utf-8")
        frozen_before = digest(idio_data / "config.json", idio_data / "state.json", idio_data / ".env")
        server_mod.STATE_PATH = sift_data / "state.json"
        sources = {"config": idio_data / "config.json", "state": idio_data / "state.json", "env": idio_data / ".env",
                   "base": idio_data}
        first = server_mod.first_start_copy("sift", sift_data / "config.json", sources, own_env=sift_data / ".env",
                                            own_base=sift_data)
        (idio_data / ".env").write_text("INVENTED_SETTING=changed\n", encoding="utf-8")
        second = server_mod.first_start_copy("sift", sift_data / "config.json", sources, own_env=sift_data / ".env",
                                             own_base=sift_data)
        rows = json.loads((sift_data / "state.json").read_text(encoding="utf-8"))["sift_reviews"]
        check("in its own folder Sift finds a project's folder given from Idiograph's folder there, and the key file "
              "where there is no keychain is copied once",
              first and not second and rows[1]["folder"] == str(idio_data / "kite review two")
              and rows[0]["folder"] == str(base / "kite review")
              and (sift_data / ".env").read_text(encoding="utf-8") == "INVENTED_SETTING=kites\n",
              rows[1]["folder"])
        (idio_data / ".env").write_text("INVENTED_SETTING=kites\n", encoding="utf-8")
        check("and leaves Idiograph's files there byte for byte as they were",
              digest(idio_data / "config.json", idio_data / "state.json", idio_data / ".env") == frozen_before)

        # ── the fallback from a held port
        mac_l, win_l = load("mac_launcher"), load("windows_launcher")
        for mod in (mac_l, win_l):
            mod.ours = lambda pids: False
        held_by_other = {8765: {999999}}
        check("a launcher whose port is held falls back past the family's other two ports, Idiograph to 8768",
              mac_l.choose_port(8765, held_by_other) == (8768, False)
              and win_l.choose_port(8765, held_by_other) == (8768, False)
              and mac_l.choose_port(8766, {8766: {1}}) == (8768, False)
              and mac_l.choose_port(8789, {8789: {1}}) == (8790, False)
              and list(app_identity.fallback_ports(8765, 4)) == [8765, 8768, 8769]
              and mac_l.PORT == win_l.PORT == 8765 and mac_l.APP == "idiograph",
              str(mac_l.choose_port(8765, held_by_other)))
        rust = support.source("packaging/tauri/src-tauri/src/main.rs").read_text(encoding="utf-8")
        check("the window's own fallback skips them too, as its Rust test checks",
              "const FAMILY_PORTS: [u16; 3] = [8765, 8766, 8767];" in rust and "tried_ports(first).find(" in rust)

        # ── versions.json, read by each reader
        real = app_identity.versions()
        check("versions.json holds Idiograph 0.9.24, Sift 1.0.0 and Trace 1.0.0",
              real == {"idiograph": "0.9.24", "sift": "1.0.0", "trace": "1.0.0"}, json.dumps(real))
        invented = base / "versions.json"
        invented.write_text(json.dumps({"idiograph": "4.5.6", "sift": "7.8.9", "trace": "2.3.4"}), encoding="utf-8")
        was_file = app_identity.VERSIONS_FILE
        sys.path.insert(0, str(support.source("packaging")))
        sys.path.insert(0, str(support.source("packaging/tauri")))
        try:
            release, update_proof = load("release"), load("update_proof", "packaging/tauri")
            build_windows, build_mac = load("build_windows"), load("build_mac")
            app_identity.VERSIONS_FILE = invented
            server_mod.app_back(held)
            server_mod.use_app("sift")
            sift_version, sift_whats = server_mod.VERSION, server_mod.whats_new_source().name
            server_mod.use_app("trace")
            trace_version = server_mod.VERSION
            got = {"release": release.server_version(), "next": update_proof.next_version(),
                   "windows": build_windows.app_version(), "mac": build_mac.app_version(),
                   "sift": sift_version, "trace": trace_version, "mcp": mcp_server.Server(app="sift").app_version()}
        finally:
            app_identity.VERSIONS_FILE = was_file
            sys.path.remove(str(support.source("packaging/tauri")))
            sys.path.remove(str(support.source("packaging")))
        check("the server, the MCP server, release.py, update_proof's next, and both builds read their app's entry",
              got == {"release": "4.5.6", "next": "4.5.7", "windows": "4.5.6", "mac": "4.5.6", "sift": "7.8.9",
                      "trace": "2.3.4", "mcp": "7.8.9"} and sift_whats == "whats-new-sift.md", json.dumps(got))
        next_run = subprocess.run([sys.executable, str(support.source("packaging/tauri/update_proof.py")), "next"],
                                  capture_output=True, text=True, encoding="utf-8", timeout=60)
        bundle = support.source("packaging/build_mac.py").read_text(encoding="utf-8")
        check("update_proof's next is the patch after versions.json's, and both builds ship the file",
              next_run.stdout.strip() == ".".join(real["idiograph"].split(".")[:2] + [str(int(real["idiograph"].split(".")[2]) + 1)]) and "versions.json" in app_identity.files("family") and '"app_identity"' in bundle,
              next_run.stdout.strip() or next_run.stderr.strip()[-200:])
    finally:
        team_sync.start = kept_looks
        server_mod.app_back(held)
        (server_mod.ROOT_OVERRIDE, server_mod.STATE_MEMORY, server_mod.ARGV, sys.argv[:],
         server_mod.AppServer, stay) = kept
        if stay is None:
            os.environ.pop(server_mod.STAY_OPEN, None)
        else:
            os.environ[server_mod.STAY_OPEN] = stay
