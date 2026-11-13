from __future__ import annotations

import inspect
import json
import shutil

import openpyxl

import rounds as rounds_mod
from workbook import WorkbookError

from . import support
from .support import STUDY_FOLDERS, TOOL, check, json_strings, line_of_js, skip
import idiograph_routes
import idiograph_cli


def test_projects(scratch):
    print("\n89. Projects and rows (201 to 204): a row per case in his order, a section per project with its head, "
          "its GETs and its fold, no single root, Settings' Projects, and --project on the command line and MCP")
    import subprocess
    import cli
    import locks
    import mcp_server
    import server as server_mod
    import themes as themes_mod

    pristine = support.DEMO_PRISTINE
    js = support.text("family/static/shell.js", "apps/idiograph/static/distil.js")
    fn = lambda name: js.split(f"function {name}(", 1)[1].split("\n}", 1)[0] if f"function {name}(" in js else ""
    whole = lambda name: f"function {name}(" + fn(name) + "\n}"
    async_whole = lambda name: f"async function {name}(" + fn(name) + "\n}"

    # ── A. three invented studies under a scratch folder, every name made up
    base = scratch / "projects-89"
    shutil.rmtree(base, ignore_errors=True)
    bees, cello, kites = base / "Bees study", base / "Cello study", base / "Kites study"

    def case_from(name, case_dir, stem):
        """A demo case's pristine workbook in an invented case folder under a new stem, with its
        sidecars, its themes file naming the case as the folder shows it."""
        case_dir.mkdir(parents=True, exist_ok=True)
        book = case_dir / f"{stem}.xlsx"
        shutil.copy2(pristine / f"{name} - EN & ES.xlsx", book)
        (case_dir / "Working").mkdir(exist_ok=True)
        for kind in (".progress.json", ".themes.json"):
            src = pristine / "Working" / f"{name} - EN & ES{kind}"
            if src.exists():
                shutil.copy2(src, case_dir / "Working" / f"{stem}{kind}")
        board = themes_mod.themes_path(book)
        if board.exists():
            data = json.loads(board.read_text(encoding="utf-8"))
            data["case"] = server_mod.display_case(case_dir.name)
            board.write_text(json.dumps(data, indent=1), encoding="utf-8")
        return book

    def raw_at(path):
        path.parent.mkdir(parents=True, exist_ok=True)
        book = openpyxl.Workbook()
        book.active.title = "Initial"
        book.active.append(["Name", "Timestamp", "Transcript"])
        book.active.append(["Ada", "00:00:05", "An invented line."])
        book.save(path)
        return path

    def project_file(root, name, question, **more):
        (root / "idiograph-project.json").write_text(json.dumps(dict({"name": name, "research_question": question}, **more)),
                                                     encoding="utf-8")

    folder = lambda root, n, who: root / "P{} - {}-{}".format(n, who, "Example")
    ada = case_from("Rowan", folder(bees, 1, "Ada"), "P1 Ada - EN & ES")
    raw_at(folder(bees, 2, "Bea") / "Source" / "P2 - Bea v1.xlsx")
    cal = case_from("Mabel", folder(bees, 3, "Cal"), "P3 Cal - EN & ES")
    loose = case_from("Juno", bees, "Loose - EN & ES")
    project_file(bees, "Keeping bees", "How do people experience keeping bees at home?")
    ada_b = case_from("Juno", folder(cello, 1, "Ada"), "P1 Ada cello - EN & ES")
    dee = case_from("Mabel", folder(cello, 4, "Dee"), "P4 Dee - EN & ES")
    project_file(cello, "Learning the cello", "How do adults experience learning the cello late in life?")
    eve = case_from("Rowan", folder(kites, 5, "Eve"), "P5 Eve - EN & ES")
    project_file(kites, "Flying kites", "How do people experience flying kites on open ground?")

    def tree(at: Path) -> dict:
        return {p.relative_to(at).as_posix(): p.read_bytes() for p in sorted(at.rglob("*")) if p.is_file() and p.name != locks.NAME}

    cfg_file = scratch / "projects-89-config.json"
    old_shape = {"root": str(bees), "interviewer": "Quill", "round_minutes": 10}
    cfg_file.write_text(json.dumps(old_shape), encoding="utf-8")
    rel = server_mod.rel_path
    kept = (server_mod.CONFIG_PATH, server_mod.ROOT_OVERRIDE, server_mod.STATE_PATH, server_mod.STATE_MEMORY,
            server_mod.PLATFORM, server_mod.PICK_FOLDER)
    live_config = server_mod.CONFIG_PATH.read_bytes() if server_mod.CONFIG_PATH.exists() else None
    try:
        server_mod.CONFIG_PATH, server_mod.ROOT_OVERRIDE = cfg_file, None
        server_mod.STATE_PATH, server_mod.STATE_MEMORY = scratch / "projects-89-state.json", {"recent": []}
        server_mod.PLATFORM = "darwin"

        # ── B. no single root: the settings, an old file, --root
        check("89: the projects a settings file names, a file from before them read as one project with its root",
              server_mod.projects_in({"root": "Cases"}) == [{"root": "Cases"}]
              and server_mod.projects_in({"projects": [{"root": "A"}, {"root": ""}, "x", {"root": "B"}]}) == [{"root": "A"}, {"root": "B"}]
              and server_mod.projects_in({"root": ""}) == [] and server_mod.projects_in({}) == []
              and server_mod.projects_in({"root": "Old", "projects": []}) == [])
        cfg = server_mod.config()
        check("89: an old config.json with root reads as one project with that root, and no root key is merged in",
              cfg["projects"] == [{"root": str(bees)}] and "root" not in cfg
              and [p.resolve() for p in server_mod.project_roots()] == [bees.resolve()])
        held = cfg_file.read_bytes()
        idiograph_routes.api_cases({})
        check("89: reading it writes nothing, so it keeps its old shape until Settings saves",
              cfg_file.read_bytes() == held)
        server_mod.api_settings({"interviewer": "Quill"})
        stored = json.loads(cfg_file.read_text(encoding="utf-8"))
        check("89: a save from Settings writes it in the new shape, every other setting kept",
              stored["projects"] == [{"root": str(bees)}] and "root" not in stored and stored["interviewer"] == "Quill")
        stored["projects"] = [{"root": str(bees)}, {"root": str(cello)}]
        cfg_file.write_text(json.dumps(stored), encoding="utf-8")
        server_mod.ROOT_OVERRIDE = str(kites)
        try:
            one = idiograph_routes.api_cases({})
            check("89: --root is a run of that one project, whatever the file names",
                  [s["project"]["name"] for s in one["projects"]] == ["Flying kites"] and one["one"] is True
                  and not server_mod.within_root(ada) and server_mod.within_root(eve))
        finally:
            server_mod.ROOT_OVERRIDE = None
        app_code = "\n".join(support.source(name).read_text(encoding="utf-8") for name in
                             ("server.py", "cli.py", "mcp_server.py", "family/server.py", "family/cli.py",
                              "family/mcp_server.py", "apps/idiograph/idiograph_routes.py", "apps/idiograph/idiograph_cli.py",
                              "apps/idiograph/idiograph_mcp.py", "apps/idiograph/gets.py", "apps/idiograph/themes.py",
                              "apps/idiograph/workbook.py", "apps/idiograph/rounds.py",
                              "apps/idiograph/shared_strings.py", "packaging/mac_launcher.py", "packaging/build_mac.py",
                              "family/static/shell.js", "apps/idiograph/static/distil.js", "apps/idiograph/static/themes.js",
                              "family/static/page.html", "apps/idiograph/static/idiograph.html"))
        check("89: nothing in the code names a study's folder, and the defaults name no project",
              not any(w in app_code for w in STUDY_FOLDERS)
              and server_mod.defaults()["projects"] == [] and "root" not in server_mod.defaults())

        # ── C. two projects, two sections, each its head, its rows and its GETs
        listed = idiograph_routes.api_cases({})
        sections = listed["projects"]
        by = {s["project"]["name"]: s for s in sections}
        check("89: two projects make two sections, in the order they were added, each with its name and question",
              [s["project"]["name"] for s in sections] == ["Keeping bees", "Learning the cello"]
              and by["Keeping bees"]["project"]["research_question"] == "How do people experience keeping bees at home?"
              and [s["id"] for s in sections] == [rel(bees), rel(cello)] and all(s["there"] for s in sections))
        check("89: each section's rows come from its own root alone",
              [c["case"] for c in by["Keeping bees"]["participants"]] == ["P1 - Ada", "P2 - Bea", "P3 - Cal", "Loose - EN & ES"]
              and [c["case"] for c in by["Learning the cello"]["participants"]] == ["P1 - Ada", "P4 - Dee"]
              and by["Learning the cello"]["participants"][0]["path"] == rel(ada_b))
        check("89: each section's GETs card is its own project's, from its own root",
              by["Keeping bees"]["gets"]["name"] == "Keeping bees" and by["Learning the cello"]["gets"]["name"] == "Learning the cello"
              and by["Keeping bees"]["gets"]["cases"] == 3 and by["Learning the cello"]["gets"]["cases"] == 2
              and idiograph_routes.gets_root({"workbook": str(dee)}).resolve() == cello.resolve()
              and idiograph_routes.gets_print_root({"root": str(cello)}).resolve() == cello.resolve())
        check("89: the top of the answer stays the first project's, for a page from before the projects",
              listed["participants"] == sections[0]["participants"] and listed["root"] == rel(bees)
              and listed["project"]["name"] == "Keeping bees" and listed["gets"] == sections[0]["gets"]
              and len(listed["cases"]) == len(sections[0]["cases"]) + len(sections[1]["cases"])
              and listed["demo_project"]["name"] == "Living with a dog")
        leaks = [v for v in json_strings(support.plain(json.loads(json.dumps(listed, default=str))), ("path", "suggested", "id", "root"))
                 if "-Example" in v]
        check("89: no second name reaches the sections outside the paths", not leaks, str(leaks[:3]))

        # ── D. the project of a path
        outside = scratch / "projects-89-elsewhere.xlsx"
        refused = []
        for value in (str(outside), str(base / "x.xlsx")):
            try:
                idiograph_routes.case_path(value)
                refused.append(False)
            except server_mod.OutsideRoot:
                refused.append(True)
        check("89: the project of a path is the project whose root holds it, the demo's for the demo",
              server_mod.project_of(ada).resolve() == bees.resolve() and server_mod.project_of(dee).resolve() == cello.resolve()
              and server_mod.project_of(server_mod.DEMO_WORKBOOK) == server_mod.DEMO_DIR
              and idiograph_routes.project_root(ada_b).resolve() == cello.resolve())
        check("89: a path under no project's root is refused, as OutsideRoot was",
              server_mod.project_of(outside) is None and server_mod.project_of(eve) is None
              and not server_mod.within_root(eve) and refused == [True, True])
        named_refused = False
        try:
            server_mod.project_named(str(kites))
        except server_mod.OutsideRoot:
            named_refused = True
        check("89: a project named by its id is found, and a folder that is no project's root is refused",
              server_mod.project_named(rel(cello)).resolve() == cello.resolve() and server_mod.project_named("demo") == server_mod.DEMO_DIR
              and named_refused)
        check("89: a project's id names a case folder in its root by its pseudonym alone, a glob the server resolves",
              idiograph_routes.project_id(folder(bees, 1, "Ada")).endswith("P1 - Ada*")
              and "Example" not in idiograph_routes.project_id(folder(bees, 1, "Ada"))
              and server_mod.configured(idiograph_routes.project_id(folder(bees, 1, "Ada"))).resolve() == folder(bees, 1, "Ada").resolve()
              and idiograph_routes.project_id(server_mod.DEMO_DIR) == "demo" and idiograph_routes.project_id(None) == "")
        switcher = idiograph_routes.themes_cases(ada)
        check("89: the PETs screen's switcher lists the cases of its own project alone",
              switcher and all(server_mod.abs_path(c["path"]).resolve().is_relative_to(bees.resolve()) for c in switcher)
              and not any("cello" in c["path"] for c in switcher))

        # ── E. Recent and the squares across projects
        idiograph_routes.api_open({"path": str(ada_b)})
        listed = idiograph_routes.api_cases({})
        conts = [(s["project"]["name"], c["case"]) for s in listed["projects"] for c in s["participants"] if "continue" in c]
        check("89, 101: the case opened last heads the recent list, in whichever project it is, and no row carries continue",
              listed["recent"][0]["path"] == rel(ada_b) and conts == [], str(conts))
        idiograph_routes.api_themes({"workbook": str(loose)})
        listed = idiograph_routes.api_cases({})
        conts = [(s["project"]["name"], c["case"]) for s in listed["projects"] for c in s["participants"] if "continue" in c]
        check("89: opening a case of the other project puts it at the head, and the recent list keeps both",
              conts == [] and [r["path"] for r in listed["recent"]] == [rel(loose), rel(ada_b)], str(conts))

        # ── F. his order, in the project file
        cards = [{"case": c} for c in ("P1 - Ada", "P2 - Bea", "P3 - Cal", "P10 - Eve", "Loose")]
        check("89: the cases his order names come first, in its order, the rest after in case order, a stale label passed over",
              [c["case"] for c in idiograph_routes.in_his_order(cards, ["P3 - Cal", "P9 - Gone", "P1 - Ada"])]
              == ["P3 - Cal", "P1 - Ada", "P2 - Bea", "P10 - Eve", "Loose"]
              and [c["case"] for c in idiograph_routes.in_his_order(cards, [])] == [c["case"] for c in cards])
        project_file(bees, "Keeping bees", "How do people experience keeping bees at home?",
                     updated="2026-10-01T12:00:00+01:00", note="kept")
        answer = idiograph_routes.api_order({"root": rel(bees), "order": ["Loose - EN & ES", "P3 - Cal", "P9 - Gone", "P1 - {}-{}".format("Ada", "Example")]})
        on_disk = json.loads((bees / server_mod.PROJECT_FILE).read_text(encoding="utf-8"))
        rows = [c["case"] for c in idiograph_routes.api_cases({})["projects"][0]["participants"]]
        check("89: a move writes order to the project file, every other key of the file kept",
              on_disk["order"] == answer["order"] == ["Loose - EN & ES", "P3 - Cal", "P9 - Gone", "P1 - Ada"]
              and on_disk["note"] == "kept" and on_disk["updated"] == "2026-10-01T12:00:00+01:00"
              and on_disk["name"] == "Keeping bees" and "-Example" not in json.dumps(on_disk), str(on_disk.get("order")))
        check("89: the rows stand in his order, a case missing from it after them and the stale label passed over",
              rows == ["Loose - EN & ES", "P3 - Cal", "P1 - Ada", "P2 - Bea"], str(rows))
        check("89: a project with no order shows case order",
              [c["case"] for c in idiograph_routes.api_cases({})["projects"][1]["participants"]] == ["P1 - Ada", "P4 - Dee"]
              and "order" not in json.loads((cello / server_mod.PROJECT_FILE).read_text(encoding="utf-8")))
        demo_before = server_mod.DEMO_PROJECT.read_bytes()
        demo_refused, stranger = False, False
        try:
            idiograph_routes.api_order({"root": "demo", "order": ["Mabel", "Juno"]})
        except WorkbookError:
            demo_refused = True
        try:
            idiograph_routes.api_order({"root": str(kites), "order": ["P5 - Eve"]})
        except server_mod.OutsideRoot:
            stranger = True
        demos = idiograph_routes.api_cases({})["demo_participants"]
        check("89: the demo's order is fixed, a move for it refused and its file untouched",
              demo_refused and server_mod.DEMO_PROJECT.read_bytes() == demo_before
              and [c["case"] for c in demos] == [c for c in idiograph_routes.DEMO_CASES if (server_mod.DEMO_DIR / c).is_dir()])
        check("89: an order for a folder that is no project's root is refused", stranger
              and "order" not in json.loads((kites / server_mod.PROJECT_FILE).read_text(encoding="utf-8")))
        check("89: the order and the projects routes are in the table, and take a POST alone",
              server_mod.ROUTES.get("/api/order") is idiograph_routes.api_order
              and server_mod.ROUTES.get("/api/projects") is idiograph_routes.api_projects
              and {"/api/order", "/api/projects"} <= set(server_mod.POST_ONLY))

        # ── G. Settings' Projects: the list, add, refuse, remove, the tick per project
        view = idiograph_routes.api_projects({})
        check("89: Projects lists every project with its id, name, question, root and tick, and whether the dialog is there",
              [p["name"] for p in view["projects"]] == ["Keeping bees", "Learning the cello"]
              and [p["id"] for p in view["projects"]] == [rel(bees), rel(cello)]
              and all(set(p) >= {"research_question", "root", "agents", "demo"} for p in view["projects"])
              and view["choose"] is True and view["one"] is False)
        before_files = tree(kites)
        asked = []
        server_mod.PICK_FOLDER = lambda: asked.append(1)
        cancel = idiograph_routes.api_projects({"op": "add"})
        check("89: Add project with the dialog cancelled adds nothing", cancel["added"] is False and asked == [1]
              and len(json.loads(cfg_file.read_text(encoding="utf-8"))["projects"]) == 2)
        server_mod.PICK_FOLDER = lambda: kites
        added = idiograph_routes.api_projects({"op": "add"})
        stored = json.loads(cfg_file.read_text(encoding="utf-8"))
        check("89: Add project with the Mac's folder dialog makes a project after the others, every setting kept",
              added["added"] is True and added["project"]["name"] == "Flying kites"
              and [p["name"] for p in added["projects"]] == ["Keeping bees", "Learning the cello", "Flying kites"]
              and stored["projects"][-1] == {"root": str(kites.resolve())} and stored["interviewer"] == "Quill"
              and [s["project"]["name"] for s in idiograph_routes.api_cases({})["projects"]][-1] == "Flying kites",
              f"{stored['projects'][-1]} {[p['name'] for p in added['projects']]}")
        refusals = {}
        for label, path in (("again", kites), ("nested", folder(bees, 1, "Ada")), ("holding", base),
                            ("demo", server_mod.DEMO_DIR / "Juno"), ("app", TOOL.parent), ("nowhere", base / "none")):
            held = cfg_file.read_bytes()
            try:
                idiograph_routes.api_projects({"op": "add", "path": str(path)})
                refusals[label] = "added"
            except WorkbookError as exc:
                refusals[label] = str(exc) if cfg_file.read_bytes() == held else "written"
        check("89: a folder added already, one inside a project's root or holding one, the app's or the demo's, refused, nothing written",
              refusals["again"] == "That folder is Flying kites, a project already."
              and refusals["nested"] == "That folder is inside Keeping bees, a project already."
              and refusals["holding"].startswith("That folder holds ") and refusals["holding"].endswith(", a project already.")
              and "the app or its demo" in refusals["demo"] and "the app or its demo" in refusals["app"]
              and refusals["nowhere"] == "That folder is not there, so nothing was added.", str(refusals))
        server_mod.PLATFORM = "linux"
        try:
            idiograph_routes.api_projects({"op": "add"})
            off = None
        except WorkbookError as exc:
            off = str(exc)
        check("89: off a Mac there is no dialog, and Add project takes the folder's path typed",
              off == server_mod.NO_DIALOG == "The folder dialog is on a Mac only. Type the folder's path."
              and idiograph_routes.api_projects({})["choose"] is False)
        server_mod.PLATFORM = "darwin"
        removed = idiograph_routes.api_projects({"op": "remove", "root": rel(kites)})
        stored = json.loads(cfg_file.read_text(encoding="utf-8"))
        gone = False
        try:
            idiograph_routes.case_path(str(eve))
        except server_mod.OutsideRoot:
            gone = True
        after = tree(kites)
        check("89: Remove from Idiograph forgets the project and touches none of its files",
              removed["removed"] is True and removed["name"] == "Flying kites"
              and [p["name"] for p in removed["projects"]] == ["Keeping bees", "Learning the cello"]
              and len(stored["projects"]) == 2 and gone
              and after == before_files and kites.is_dir() and eve.is_file(),
              f"{removed.get('name')} {len(stored['projects'])} {gone} {sorted(set(after) ^ set(before_files))}")
        demo_kept = False
        try:
            idiograph_routes.api_projects({"op": "remove", "root": "demo"})
        except WorkbookError:
            demo_kept = True
        server_mod.ROOT_OVERRIDE = str(bees)
        one_run = []
        for body in ({"op": "add", "path": str(kites)}, {"op": "remove", "root": rel(bees)}):
            try:
                idiograph_routes.api_projects(body)
                one_run.append(None)
            except WorkbookError as exc:
                one_run.append(str(exc))
        server_mod.ROOT_OVERRIDE = None
        check("89: the demo stays, and a run of one project adds and removes none",
              demo_kept and one_run == [idiograph_routes.ONE_RUN] * 2
              and len(json.loads(cfg_file.read_text(encoding="utf-8"))["projects"]) == 2)
        idiograph_routes.api_project({"root": rel(bees), "agents": True})
        bees_file = json.loads((bees / server_mod.PROJECT_FILE).read_text(encoding="utf-8"))
        cello_file = json.loads((cello / server_mod.PROJECT_FILE).read_text(encoding="utf-8"))
        unnamed = None
        try:
            idiograph_routes.api_project({"name": "Which one"})
        except WorkbookError as exc:
            unnamed = str(exc)
        check("89: the privacy tick is each project's own, in its own file, and a save naming no project is refused",
              bees_file["agents"]["allowed"] is True and "agents" not in cello_file
              and idiograph_routes.api_project({"root": rel(cello)})["project"]["agents"]["allowed"] is False
              and idiograph_routes.api_project({"path": str(dee)})["project"]["name"] == "Learning the cello"
              and unnamed == "Say which project, so nothing was saved.")
        idiograph_routes.api_project({"root": rel(cello), "name": "Learning the cello", "research_question": "Asked anew"})
        check("89: a project's name and question save to its own file and no other",
              json.loads((cello / server_mod.PROJECT_FILE).read_text(encoding="utf-8"))["research_question"] == "Asked anew"
              and json.loads((bees / server_mod.PROJECT_FILE).read_text(encoding="utf-8"))["research_question"]
              == "How do people experience keeping bees at home?")

        # ── H. the command line and the MCP server across projects
        idiograph_routes.api_project({"root": rel(cello), "agents": True})

        def run(*args):
            return cli.run(["--config", str(cfg_file), *args])

        code, out, err = run("cases", "--json")
        got = support.plain(json.loads(out)) if out.strip() else {}
        check("89: cases with no option lists each project's cases under its name",
              code == 0 and [p["name"] for p in got.get("projects", [])] == ["Keeping bees", "Learning the cello"]
              and [c["case"] for c in got["projects"][1]["cases"]] == ["P1 - Ada", "P4 - Dee"], (out or err)[:200])
        code, out, err = run("cases")
        check("89: and in plain words, each project's name over its cases",
              code == 0 and out.index("Keeping bees") < out.index("P3 - Cal") < out.index("Learning the cello") < out.index("P4 - Dee")
              and "-Example" not in out)
        code, out, err = run("statements", "P4 - Dee", "--json")
        check("89: a case one project holds is named by its pseudonym alone",
              code == 0 and support.plain(json.loads(out))["case"] == "P4 - Dee" and support.plain(json.loads(out))["workbook"] == dee.name)
        code, out, err = run("statements", "Ada")
        check("89: a pseudonym two projects share is refused in one line asking for --project",
              code == 1 and not out and len(err.strip().splitlines()) == 1 and "--project" in err
              and "Keeping bees" in err and "Learning the cello" in err, err.strip())
        code, out, err = run("--project", "Learning the cello", "statements", "Ada", "--json")
        code2, out2, err2 = run("statements", "P1 - Ada", "--project", "keeping bees", "--json")
        check("89: --project names the project, before the command or after it, its name in any case",
              code == 0 and support.plain(json.loads(out))["workbook"] == ada_b.name and code2 == 0 and support.plain(json.loads(out2))["workbook"] == ada.name)
        code, out, err = run("--project", "Nope", "cases")
        check("89: a project name no project has is refused, naming the projects",
              code == 1 and "No project called Nope." in err and "Keeping bees, Learning the cello" in err)
        code, out, err = run("gets", "show")
        check("89: gets with several projects asks for --project", code == 1 and "--project" in err and len(err.strip().splitlines()) == 1)
        code, out, err = run("--root", str(cello), "cases", "--json")
        got = support.plain(json.loads(out)) if out.strip() else {}
        check("89: --root is a run of that one project, its answer in the one project's shape",
              code == 0 and got.get("project", {}).get("name") == "Learning the cello" and "projects" not in got
              and server_mod.ROOT_OVERRIDE is None)
        idiograph_routes.api_project({"root": rel(cello), "agents": False})
        code, out, err = run("cases")
        code2, out2, err2 = run("--project", "Learning the cello", "cases")
        check("89: a project closed to agents is never read, said in one line, and refused when named",
              code == 0 and "Learning the cello: closed to AI agents." in out and "P4 - Dee" not in out
              and code2 == 1 and idiograph_cli.PRIVATE in err2)
        code, out, err = run("validate", "--json")
        check("89: validate reads every project open to agents", code == 0 and support.plain(json.loads(out))["projects"][0]["valid"] is True)
        idiograph_routes.api_project({"root": rel(cello), "agents": True})
        both = mcp_server.Server(config=str(cfg_file))
        named = mcp_server.Server(config=str(cfg_file), project="Learning the cello")
        shared = both.call(mcp_server.BY_NAME["statements"], {"case": "P1 - Ada"})
        picked = named.call(mcp_server.BY_NAME["statements"], {"case": "P1 - Ada"})
        listed = both.call(mcp_server.BY_NAME["cases"], {})
        check("89: the MCP tools read every project, refuse a shared pseudonym, and take --project",
              shared["isError"] is True and "--project" in support.unfenced(shared["content"][0]["text"])
              and picked["isError"] is False and support.plain(picked["structuredContent"])["workbook"] == ada_b.name
              and [p["name"] for p in support.plain(listed["structuredContent"])["projects"]] == ["Keeping bees", "Learning the cello"]
              and '"--project"' in inspect.getsource(mcp_server.main) and "each project's under its name" in mcp_server.TOOLS_LINE)
        check("89: the command line's options carry --project, put back after every run",
              "--project" in cli.parser().format_help() and "args.project = None" in inspect.getsource(cli.perform)
              and "srv.CONFIG_PATH, srv.ROOT_OVERRIDE, srv.STATE_MEMORY = kept" in inspect.getsource(idiograph_cli.perform))
    finally:
        (server_mod.CONFIG_PATH, server_mod.ROOT_OVERRIDE, server_mod.STATE_PATH, server_mod.STATE_MEMORY,
         server_mod.PLATFORM, server_mod.PICK_FOLDER) = kept
    check("89: the live config.json is exactly as it was",
          (server_mod.CONFIG_PATH.read_bytes() if server_mod.CONFIG_PATH.exists() else None) == live_config)

    # ── I. the page: the sections, the rows, the fold, Settings' Projects
    draw = fn("drawPick")
    card_fn = fn("homeCardHtml")
    page_fn = fn("drawPage")
    check("89, 9 October, updated 18 October (area 177): each project a card, its name, question and line, the demo's "
          "after them in a section of their own (demos, 3 November 2026), and a card opens its page, its name and "
          "question at the head, its rows, then its GETs card",
          '<span class="hc-name">${esc(c.name)}</span>' in card_fn and '<span class="hc-question">${esc(c.question)}</span>' in card_fn
          and '<span class="pc-line hc-line">${esc(c.line)}</span>' in card_fn
          and "foldable($('home-analysis'), $('analysis-head'), 'analysis');" in draw
          and draw.index("sections.map(") < draw.index("demosOf(data).map(")
          and "b.onclick = () => openPage(b.dataset.id);" in draw
          and "pageHead(p.name || t('distil.home.project'), p.research_question || '', false, !!p.copy);" in page_fn
          and page_fn.index("drawCards(list, s.participants || [], { id: s.id });") < page_fn.index("drawGetsCard($('hp-gets'), s.gets);")
          and "drawHome();" in fn("loadLibrary"))
    node = shutil.which("node")
    if not node:
        skip("89: the rows, the keys, the drag, the fold and Projects in node", "node is not installed")
        return
    pieces = [line_of_js(js, "const esc = "), line_of_js(js, "const escAttr = "), line_of_js(js, "const plural = "),
              whole("esLine"), whole("petsLine"), whole("gripHtml"), whole("cardHtml"), line_of_js(js, "const labelsOf = "),
              async_whole("saveOrder"), whole("cardGrip"), whole("gripDrag"), whole("gripKeys"), line_of_js(js, "const FOLD_KEY = "),
              whole("shutIds"), whole("keepFold"), whole("foldable"), line_of_js(js, "const PROJ = "),
              line_of_js(js, "const projectAt = "), whole("projectBody"), whole("projectSaves")]
    script = scratch / "projects-89.js"
    script.write_text(support.i18n_js() + r"""
const calls = [];
async function api(path, body) { calls.push([path, JSON.parse(JSON.stringify(body))]); return {}; }
function say() {}
const RESTART_LINE = 'restart';
const needsRestart = () => false;
const said = { textContent: '' };
const fields = { 'set-project-name': { value: '' }, 'set-question': { value: '' }, 'set-agents': { checked: false } };
const $ = (id) => (id === 'order-said' ? said : fields[id]);
function settingsCase() { return { path: 'wb-a' }; }
const window = { on: {}, addEventListener(t, f) { (this.on[t] = this.on[t] || []).push(f); },
  removeEventListener(t, f) { this.on[t] = (this.on[t] || []).filter((g) => g !== f); },
  fire(t, ev) { for (const f of (this.on[t] || []).slice()) f(ev); } };
const store = {};
let localStorage = { getItem: (k) => (k in store ? store[k] : null), setItem: (k, v) => { store[k] = String(v); } };
""" + "\n".join(pieces) + r"""
function makeList(labels) {
  const list = { rows: [] };
  list.querySelectorAll = () => list.rows.slice();
  list.insertBefore = (li, ref) => { list.rows = list.rows.filter((r) => r !== li); const at = ref ? list.rows.indexOf(ref) : -1;
    list.rows.splice(at < 0 ? list.rows.length : at, 0, li); };
  list.appendChild = (li) => list.insertBefore(li, null);
  Object.defineProperty(list, 'lastElementChild', { get: () => list.rows[list.rows.length - 1] || null });
  for (const label of labels) {
    const li = { dataset: { case: label }, focused: 0, classes: new Set() };
    li.classList = { add: (c) => li.classes.add(c), remove: (c) => li.classes.delete(c) };
    li.querySelector = () => ({ focus: () => { li.focused += 1; } });
    Object.defineProperty(li, 'nextElementSibling', { get: () => list.rows[list.rows.indexOf(li) + 1] || null });
    li.getBoundingClientRect = () => ({ top: list.rows.indexOf(li) * 50, height: 40 });
    list.rows.push(li);
  }
  return list;
}
const names = (list) => list.rows.map((r) => r.dataset.case);
const key = (k, alt = true) => ({ altKey: alt, key: k, prevented: false, preventDefault() { this.prevented = true; }, stopPropagation() {} });
const listening = () => Object.values(window.on).reduce((n, l) => n + l.length, 0);
function el() {
  const e = { attrs: {}, classes: new Set(), onclick: null };
  e.setAttribute = (k, v) => { e.attrs[k] = v; };
  e.classList = { toggle: (c, on) => (on ? e.classes.add(c) : e.classes.delete(c)), contains: (c) => e.classes.has(c) };
  return e;
}
(async () => {
  const out = {};
  const card = { case: 'P1 - Ada', path: 'a', turns: { done: 3, total: 9 }, board: 'Board 1', boards: 1, files: [] };
  out.html = { row: cardHtml(card), fixed: cardHtml(card, true), demo: cardHtml(Object.assign({}, card, { demo: true })),
    go: cardHtml(Object.assign({}, card, { continue: 'pets' })), start: cardHtml({ case: 'P2 - Bea', path: null, start: { path: 'b', kind: 'raw' } }) };
  const list = makeList(['P1 - Ada', 'P2 - Bea', 'P3 - Cal']);
  gripKeys(key('ArrowUp'), list.rows[2], list, cardGrip(list, 'ROOT-A'));
  out.up = names(list);
  out.said = said.textContent;
  gripKeys(key('ArrowUp'), list.rows[0], list, cardGrip(list, 'ROOT-A'));
  out.top = names(list);
  gripKeys(key('ArrowDown'), list.rows[0], list, cardGrip(list, 'ROOT-A'));
  out.down = names(list);
  const plain = key('ArrowDown', false);
  gripKeys(plain, list.rows[0], list, cardGrip(list, 'ROOT-A'));
  out.plain = [names(list), plain.prevented];
  out.focused = list.rows.map((r) => r.focused);
  await null;
  out.keyCalls = calls.splice(0);
  const dl = makeList(['A', 'B', 'C', 'D']);
  const d = dl.rows[3];
  gripDrag({ button: 0, pointerId: 7, currentTarget: {}, preventDefault() {} }, d, dl, cardGrip(dl, 'ROOT-B'));
  out.dragging = d.classes.has('dragging');
  window.fire('pointermove', { pointerId: 7, clientY: 60 });
  out.mid = names(dl);
  window.fire('pointermove', { pointerId: 9, clientY: 0 });
  out.other = names(dl);
  window.fire('pointermove', { pointerId: 7, clientY: 5 });
  out.first = names(dl);
  window.fire('pointerup', { pointerId: 7 });
  await null;
  out.dragCalls = calls.splice(0);
  out.dropped = [d.classes.has('dragging'), listening()];
  const same = makeList(['A', 'B']);
  gripDrag({ button: 0, pointerId: 3, preventDefault() {} }, same.rows[0], same, cardGrip(same, 'R'));
  window.fire('pointerup', { pointerId: 3 });
  gripDrag({ button: 2, pointerId: 4, preventDefault() {} }, same.rows[0], same, cardGrip(same, 'R'));
  await null;
  out.unmoved = [calls.length, listening()];
  const a = el(), ah = el(), b = el(), bh = el();
  foldable(a, ah, 'ROOT-A');
  foldable(b, bh, 'demo');
  out.fold = { start: [a.classes.has('shut'), ah.attrs['aria-expanded'], b.classes.has('shut')] };
  ah.onclick();
  out.fold.shut = [a.classes.has('shut'), ah.attrs['aria-expanded'], store['idiograph-shut']];
  const a2 = el(), ah2 = el(), b2 = el(), bh2 = el();
  foldable(a2, ah2, 'ROOT-A');
  foldable(b2, bh2, 'demo');
  out.fold.reload = [a2.classes.has('shut'), ah2.attrs['aria-expanded'], b2.classes.has('shut')];
  ah2.onclick();
  out.fold.open = [a2.classes.has('shut'), store['idiograph-shut']];
  localStorage = { getItem() { throw new Error('private'); }, setItem() { throw new Error('private'); } };
  const c = el(), ch = el();
  foldable(c, ch, 'ROOT-C');
  ch.onclick();
  out.fold.private = [c.classes.has('shut'), ch.attrs['aria-expanded']];
  // Project settings, one project a sheet (settingsplit): the screen behind's own, then another, then the demo
  PROJ.own = { id: 'A', name: 'Keeping bees', research_question: 'Q-A', agents: { allowed: false } };
  PROJ.p = PROJ.own;
  fields['set-project-name'].value = ' Keeping bees, renamed ';
  fields['set-question'].value = 'Q-A';
  fields['set-agents'].checked = false;
  out.saves = projectSaves();
  PROJ.p = { id: 'B', name: 'Learning the cello', research_question: 'Q-B', agents: { allowed: true } };
  fields['set-project-name'].value = 'Learning the cello';
  fields['set-question'].value = 'Q-B';
  fields['set-agents'].checked = false;
  out.saves.push(...projectSaves());
  PROJ.p = { id: 'demo', name: 'Living with a dog', research_question: 'Q-D', demo: true, agents: { allowed: true } };
  fields['set-project-name'].value = 'Changed';
  out.demoSaves = projectSaves();
  console.log(JSON.stringify(out));
})();
""", encoding="utf-8")
    ran = subprocess.run([node, str(script)], capture_output=True, text=True, encoding="utf-8")
    if ran.returncode != 0:
        check("89: the rows, the keys, the drag, the fold and Projects run in node", False, ran.stderr.strip()[:400])
        return
    o = support.plain(json.loads(ran.stdout))
    h = o["html"]
    check("89: the demo's rows, and a row drawn fixed, have no handle to drag",
          h["fixed"].startswith('<span class="pc-grip none" aria-hidden="true"></span>') and 'data-act="grip"' not in h["fixed"]
          and h["demo"].startswith('<span class="pc-grip none"') and '<span class="tag demo">demo</span>' in h["demo"])
    check("89: Alt + Up and Alt + Down move a row one place, the handle keeping the focus, the place said",
          o["up"] == ["P1 - Ada", "P3 - Cal", "P2 - Bea"] and o["top"] == o["up"] and o["down"] == ["P3 - Cal", "P1 - Ada", "P2 - Bea"]
          and o["plain"] == [o["down"], False] and sum(o["focused"]) == 2 and o["said"] == "P3 Cal, 2 of 3", str(o["focused"]))
    check("89: each move by the keys saves the whole order of its project, and a move off the end saves nothing",
          o["keyCalls"] == [["/api/order", {"root": "ROOT-A", "order": ["P1 - Ada", "P3 - Cal", "P2 - Bea"]}],
                            ["/api/order", {"root": "ROOT-A", "order": ["P3 - Cal", "P1 - Ada", "P2 - Bea"]}]], str(o["keyCalls"]))
    check("89: a drag carries the row past each one's middle, following its own pointer alone",
          o["dragging"] is True and o["mid"] == ["A", "D", "B", "C"] and o["other"] == o["mid"] and o["first"] == ["D", "A", "B", "C"])
    check("89: let go somewhere new, the drag saves the order once and lets the pointer go, and one let go where it began saves nothing",
          o["dragCalls"] == [["/api/order", {"root": "ROOT-B", "order": ["D", "A", "B", "C"]}]]
          and o["dropped"] == [False, 0] and o["unmoved"] == [0, 0], str(o["dragCalls"]))
    check("89: a section's head folds it, the fold kept per project, a reload keeping it, and the other left open",
          o["fold"]["start"] == [False, "true", False] and o["fold"]["shut"] == [True, "false", '["ROOT-A"]']
          and o["fold"]["reload"] == [True, "false", False] and o["fold"]["open"] == [False, "[]"]
          and o["fold"]["private"] == [True, "false"], str(o["fold"]))
    check("89: Save sends the project when it changed, by its id, the case's own with its workbook, the tick on its own, the demo never",
          o["saves"] == [{"root": "A", "path": "wb-a", "name": "Keeping bees, renamed", "research_question": "Q-A"},
                         {"root": "B", "agents": False}] and o["demoSaves"] == [], str(o["saves"]))

    # ── J. Project settings in the page (Settings' Projects until settingsplit, 5 November 2026, with its picker)
    check("89: Project settings shows the one project it was opened for, the screen behind's copy when it is that one, "
          "with no picker",
          "const own = projectBehind(p);" in fn("openProjectSettings") and "PROJ.p = shown;" in fn("openProjectSettings")
          and "drawPicker" not in js and 'id="project-pick"' not in support.page_text())
    remove = fn("removeProject")
    check("89: Remove from Idiograph asks in Remove's card first (removetrash), saves what is typed over its own case, "
          "and goes home",
          "const asked = await askRemove(p.name);" in remove
          and "if (own && !(await savePending())) return;" in remove
          and "api('/api/projects', { op: 'remove', root: p.id, trash: asked.trash, page: pageId() })" in remove
          and "if (own) { S.noSpot = true; homeKeep(''); location.reload(); return; }" in remove)
    check("89: Open project folder is Home's alone since settingsplit, the one page function, the dialog on a Mac and the "
          "typed path elsewhere",
          "settingsAddProject" not in js and 'id="project-add"' not in support.page_text()
          and js.count("api('/api/projects', { op: 'add', path })\n      : await picking((chosen) => api('/api/projects', { op: 'add', path: chosen }), btn, PICK_SAYS.project)") == 1)
