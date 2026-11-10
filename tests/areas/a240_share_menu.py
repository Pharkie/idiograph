"""Area 240: a project card's menu on Home, as Adam ruled on the drawings of 21 October 2026 (Way A,
sendproj3). Each item does its job: Share a copy writes the whole project as one file, Show in Finder
shows its folder and writes nothing, Project settings opens that project's own sheet, and Remove from
Idiograph takes the project off Home and leaves its folder as it was. The demo's card holds Project
settings alone and a missing folder's card Remove alone. A copy opened from a shared file is marked so,
its card and page tagged "copy", and the folder dialog names the new folder made. Every fixture is
invented, a project on keeping bees."""
from __future__ import annotations

import json
import re
import shutil
import subprocess
import zipfile
from pathlib import Path

import project_pack
import server as server_mod

from . import support
from .support import check, skip
import idiograph_routes


def whole(src: str, head: str) -> str:
    at = src.index(head)
    return src[at:src.index("\n}\n", at) + 3]


def line_of(src: str, start: str) -> str:
    return next(ln for ln in src.splitlines() if ln.startswith(start))


def test_share_menu(scratch: Path):
    print("\n240. A project card's menu: Share a copy, Show in Finder, Project settings, Remove from Idiograph")
    js = support.text("family/static/shell.js", "apps/idiograph/static/distil.js")
    base = scratch / "share-240"
    shutil.rmtree(base, ignore_errors=True)
    root = base / "Keeping bees"
    (root / "P1 - Wren" / "Source").mkdir(parents=True)
    (root / server_mod.PROJECT_FILE).write_text(json.dumps({"name": "Keeping bees", "research_question":
                                                            "How do beekeepers live through a cold spring?",
                                                            "uid": "a240beef0000cafe"}), encoding="utf-8")
    (root / "P1 - Wren" / "P1 Wren - EN & ES.xlsx").write_bytes(b"PK\x03\x04 a workbook stands in here")
    (root / "P1 - Wren" / "Source" / "spring.m4a").write_bytes(bytes(range(256)) * 40)
    other = base / "Hive notes"
    (other / "P1 - Hollis").mkdir(parents=True)
    gone = base / "Swarm season"
    out, into = base / "out", base / "into"
    out.mkdir()
    into.mkdir()
    config_file = base / "config-240.json"
    config_file.write_text(json.dumps({"projects": [{"root": str(root)}, {"root": str(other)}, {"root": str(gone)}],
                                       "interviewer": "Sam", "corpus": "", "gravity_reference": "",
                                       "corpus_exclude": []}), encoding="utf-8")

    def files(at: Path) -> dict:
        return {p.relative_to(at).as_posix(): p.read_bytes() for p in sorted(at.rglob("*")) if p.is_file()}

    live = server_mod.CONFIG_PATH.read_bytes() if server_mod.CONFIG_PATH.exists() else None
    kept = (server_mod.CONFIG_PATH, server_mod.ROOT_OVERRIDE, server_mod.STATE_MEMORY, server_mod.PLATFORM,
            idiograph_routes.SHOW_FOLDER, server_mod.PICK_FOLDER)
    try:
        server_mod.CONFIG_PATH, server_mod.ROOT_OVERRIDE, server_mod.STATE_MEMORY = config_file, None, {"recent": []}
        ids = {p["name"]: p["id"] for p in idiograph_routes.projects_view()["projects"]}
        before = files(root)

        # Share a copy: the whole project written as one file to the path the save panel chose
        done = idiograph_routes.api_send_project({"root": ids["Keeping bees"], "to": str(out / "Keeping bees")})
        sent = out / "Keeping bees.idiograph"
        with zipfile.ZipFile(sent) as zf:
            names = set(zf.namelist())
        check("240: Share a copy writes Keeping bees.idiograph holding every file of the project, the project unchanged",
              done.get("sent") is True and sent.is_file() and files(root) == before
              and {project_pack.TOP + k for k in files(root)} <= names, str(sorted(names)))

        # Show in Finder: the project's folder shown and nothing written, the demo and a missing folder refused
        shown = []
        idiograph_routes.SHOW_FOLDER = lambda folder: shown.append(Path(folder))
        server_mod.PLATFORM = "darwin"
        answer = idiograph_routes.api_projects({"op": "reveal", "root": ids["Keeping bees"]})
        check("240: Show in Finder shows the project's own folder and writes nothing",
              answer.get("revealed") is True and len(shown) == 1 and server_mod.same_folder(shown[0], root)
              and files(root) == before, str(shown))
        refused = []
        for value in ("demo", ids["Swarm season"]):
            try:
                idiograph_routes.api_projects({"op": "reveal", "root": value})
                refused.append(False)
            except server_mod.WorkbookError:
                refused.append(True)
        server_mod.PLATFORM = "freebsd14"
        try:
            idiograph_routes.api_projects({"op": "reveal", "root": ids["Keeping bees"]})
            refused.append(False)
        except server_mod.WorkbookError:
            refused.append(True)
        server_mod.PLATFORM = kept[3]
        check("240: Show in Finder refuses the demo, a folder that is not there and a machine that is no Mac, Windows or Linux",
              refused == [True, True, True] and len(shown) == 1, str(refused))

        # Remove from Idiograph: off the list, its folder exactly as it was, a missing folder's card too
        other_before = files(other)
        answer = idiograph_routes.api_projects({"op": "remove", "root": ids["Hive notes"]})
        roots = [e["root"] for e in json.loads(config_file.read_text(encoding="utf-8"))["projects"]]
        check("240: Remove from Idiograph takes the project off Home and leaves its folder and files as they were",
              answer.get("removed") is True and "Hive notes" not in [p["name"] for p in answer["projects"]]
              and files(other) == other_before and str(other) not in roots, str(roots))
        answer = idiograph_routes.api_projects({"op": "remove", "root": ids["Swarm season"]})
        check("240: a card whose folder is gone is removed the same way",
              answer.get("removed") is True and [p["name"] for p in answer["projects"]] == ["Keeping bees"])

        # Open a shared copy: the copy marked, the original never; the folder dialog names the new folder
        asked = []
        server_mod.PLATFORM = "darwin"
        server_mod.PICK_FOLDER = lambda prompt=None, files=False: (asked.append(prompt), sent if files else into)[1]
        opened = idiograph_routes.api_open_sent({})
        server_mod.PLATFORM = kept[3]
        copy = into / "Keeping bees"
        held = json.loads((copy / server_mod.PROJECT_FILE).read_text(encoding="utf-8"))
        check("240: a shared copy opens marked a copy, its name and question kept, the project shared never marked",
              opened.get("opened") is True and opened["project"]["copy"] is True
              and held.get("copy_of", {}).get("name") == "Keeping bees" and held.get("research_question")
              == "How do beekeepers live through a cold spring?"
              and idiograph_routes.read_project(root)["copy"] is False and files(root) == before, json.dumps(held))
        check("240: the dialogs say Choose the shared copy, then name the new folder made inside the one chosen",
              asked == ["Choose the shared copy.",
                        "Choose the folder to put the copy in. A new folder, Keeping bees, is made inside it."]
              and idiograph_routes.api_open_sent({"file": str(sent), "check": True}).get("folder") == "Keeping bees", str(asked))
    finally:
        (server_mod.CONFIG_PATH, server_mod.ROOT_OVERRIDE, server_mod.STATE_MEMORY, server_mod.PLATFORM,
         idiograph_routes.SHOW_FOLDER, server_mod.PICK_FOLDER) = kept
    check("240: the live settings file is exactly as it was",
          (server_mod.CONFIG_PATH.read_bytes() if server_mod.CONFIG_PATH.exists() else None) == live)

    # the menus and Project settings, on the page's own code in node
    node = shutil.which("node")
    if not node:
        skip("240: the card menus and Project settings in node", "node is not installed")
        return
    pieces = [line_of(js, "const esc = "), line_of(js, "const escAttr = "), line_of(js, "const SHARE_LINE = "),
              line_of(js, "const PROJ = "), line_of(js, "const projectAt = "),
              whole(js, "function homeMenuItems("), whole(js, "function homeMenuRows("), whole(js, "function homeMenuHtml("),
              whole(js, "function projectMenuHtml("), whole(js, "function projectMenuWord("), whole(js, "function projectDotsHtml("),
              whole(js, "function homeCardHtml("),
              whole(js, "function projectSettingsFor(")]
    script = base / "menus-240.js"
    script.write_text(support.i18n_js() + r"""
const APP = 'idiograph';
const APP_NAME = 'Idiograph';
let MAC = true;
let inWindow = false;
const windowPicks = () => inWindow;
const S = { oneRun: false, chooseRoot: false };
const els = {};
const $ = (id) => els[id] || (els[id] = { hidden: false, innerHTML: '' });
const calls = { settings: [], sheets: [] };
function openSettings(pane) { calls.settings.push(pane); }
function openProjectSettings(p) { calls.sheets.push(p ? p.id : null); PROJ.p = p; }
""" + "\n".join(pieces) + r"""
const out = {};
const project = { id: 'ROOT-BEES', name: 'Keeping bees', line: '1 participant' };
out.browser = homeMenuItems(project, { window: false, oneRun: false });
out.window = homeMenuItems(project, { window: true, oneRun: false });
out.demo = homeMenuItems({ id: 'demo', demo: true }, { window: true, oneRun: false });
out.missing = homeMenuItems({ id: 'ROOT-GONE', missing: true }, { window: true, oneRun: false });
out.oneRun = homeMenuItems(project, { window: true, oneRun: true });
out.missingOne = homeMenuItems({ id: 'ROOT-GONE', missing: true }, { window: true, oneRun: true });
out.macHtml = homeMenuHtml(out.window, { window: true, mac: true });
out.winHtml = homeMenuHtml(out.window, { window: true, mac: false });
out.browserHtml = homeMenuHtml(out.browser, { window: false, mac: true });
out.copyCard = homeCardHtml({ ...project, copy: true });
out.plainCard = homeCardHtml(project);
S.oneRun = true;
out.demoCard = homeCardHtml({ id: 'demo', demo: true, name: 'Living with a dog', line: '3 participants' });
S.oneRun = false;
// Project settings on the second of three projects: its own sheet for that project, Settings never opened
// (settingsplit, 5 November 2026)
const list = [{ id: 'ROOT-A', name: 'Hive notes' }, { id: 'ROOT-BEES', name: 'Keeping bees' }, { id: 'ROOT-C', name: 'Swarms' }];
projectSettingsFor(list[1]);
out.firstAt = projectAt() && projectAt().id;
// the demo's, read-only
projectSettingsFor({ id: 'demo', demo: true, name: 'Living with a dog' });
out.demoAt = projectAt() && projectAt().id;
// a card with no project behind it opens nothing
projectSettingsFor(undefined);
out.sheets = calls.sheets;
out.settings = calls.settings;
console.log(JSON.stringify(out));
""", encoding="utf-8")
    run = subprocess.run([node, str(script)], capture_output=True, text=True, encoding="utf-8", timeout=60)
    if run.returncode != 0:
        check("240: the menus run in node", False, run.stderr.strip()[:400])
        return
    o = json.loads(run.stdout.strip().splitlines()[-1])
    check("240: a project's menu holds Share a copy, Show in Finder in the window alone, Project settings, Project "
          "history under it (historyui), then Remove",
          o["window"] == ["share", "qdpx", "show", "settings", "history", "remove"]
          and o["browser"] == ["share", "qdpx", "settings", "history", "remove"]
          and o["oneRun"] == ["share", "qdpx", "show", "settings", "history"], json.dumps(o)[:300])
    check("240: the demo's card holds Project settings alone and a missing folder's Remove alone, none in a run of one",
          o["demo"] == ["settings"] and o["missing"] == ["remove"] and o["missingOne"] == [], json.dumps(o)[:300])
    check("240: each item carries its act, Remove after its rule, and the browser's Share a copy its line under it",
          re.findall(r'data-act="([a-z]+)"', o["macHtml"]) == ["share", "qdpx", "show", "settings", "history", "remove"]
          and o["macHtml"].index('row-menu-rule') < o["macHtml"].index('data-act="remove"')
          and "Show in Finder" in o["macHtml"] and "Show in Explorer" in o["winHtml"]
          and "doesn&#39;t track changes" not in o["macHtml"] and "track changes between copies" in o["browserHtml"],
          o["browserHtml"][:300])
    check("240: a shared copy's card carries its copy tag, a plain one none, and the demo's its menu in a run of one",
          '<span class="tag copy">copy</span>' in o["copyCard"] and 'tag copy' not in o["plainCard"]
          and 'data-act="settings"' in o["demoCard"] and 'data-act="remove"' not in o["demoCard"], o["copyCard"][:300])
    check("240: Project settings opens that card's project's own sheet, never Settings, and the demo's its own",
          o["settings"] == [] and o["sheets"] == ["ROOT-BEES", "demo"] and o["firstAt"] == "ROOT-BEES"
          and o["demoAt"] == "demo", json.dumps(o)[:300])
