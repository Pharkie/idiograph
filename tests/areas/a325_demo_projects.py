"""Area 325: the two demos (demos, 3 November 2026, Adam that evening): a thematic analysis demo of the same three
invented participants beside the IPA demo, both in a Demo projects section on Home apart from his projects, shut
until he opens it and kept as he leaves it. The thematic analysis demo built from its sources the same bytes every
time, opening as a thematic analysis project with its code list and its Themes board, put back by Reset demo, never
read as cases of the IPA demo, and staged by the Mac build; `--demo` still reading the IPA demo and `--demo ta` the
thematic analysis one; Home's fold in node."""
from __future__ import annotations

import hashlib
import importlib.util
import json
import shutil
from pathlib import Path

from . import support
from .support import check
import idiograph_routes


def sha(path: Path) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def tree(folder: Path) -> dict:
    return {p.relative_to(folder).as_posix(): sha(p) for p in sorted(Path(folder).rglob("*")) if p.is_file()}


# Home's fold of the Demo projects section, its own code run in node with a stand-in for the page: shut on a Home
# with projects, open on one with none, kept as he leaves it either way
FOLD = r"""
const store = {};
global.localStorage = { getItem: (k) => (k in store ? store[k] : null), setItem: (k, v) => { store[k] = String(v); } };
const el = (id) => ({ id, classes: new Set(), attrs: {}, onclick: null,
  classList: { toggle(c, on) { if (on) this.o.classes.add(c); else this.o.classes.delete(c); }, contains(c) { return this.o.classes.has(c); } },
  setAttribute(k, v) { this.attrs[k] = v; } });
const els = { 'home-demos': el('home-demos'), 'demos-head': el('demos-head') };
for (const e of Object.values(els)) e.classList.o = e;
global.$ = (id) => els[id];
SHELL
DISTIL
const shut = () => els['home-demos'].classes.has('shut');
const out = {};
demosFold(false); out.withProjects = shut();
demosFold(true); out.noProjects = shut();
els['demos-head'].onclick(); out.closed = shut();
demosFold(true); out.keptShutNone = shut();
els['demos-head'].onclick(); out.opened = shut();
demosFold(false); out.keptOpen = shut();
out.expanded = els['demos-head'].attrs['aria-expanded'];
console.log(JSON.stringify(out));
"""


def piece(js: str, start: str, end: str) -> str:
    at = js.index(start)
    return js[at:js.index(end, at)]


def test_demo_projects(scratch):
    print("\n325. Two demos: the thematic analysis demo of the same three participants, both apart from his projects "
          "on Home, shut until opened, and --demo naming which")
    import cli
    import codes as codes_mod
    import i18n
    import make_demo
    import server as server_mod

    shipped = support.source("demo")
    ta_src = shipped / make_demo.TA_FOLDER

    # ── the thematic analysis demo built twice from its sources into scratch, the same bytes as it ships
    builds = []
    for n in (1, 2):
        into = scratch / f"a325-build-{n}"
        shutil.rmtree(into, ignore_errors=True)
        built = make_demo.build_ta_all(into / "ta", shipped)
        builds.append((into / "ta", built))
    first, built = builds[0]
    names = [f"{c} - EN & ES.xlsx" for c in make_demo.CASES]
    same = all(sha(first / c / n) == sha(builds[1][0] / c / n) for c, n in zip(make_demo.CASES, names))
    same = same and all(sha(first / f) == sha(builds[1][0] / f) for f in (make_demo.GETS_FILE, make_demo.CODES_FILE))
    # each workbook as the same parts holding the same trees, as area 74 reads the IPA demo's, since another Python's
    # XML writer spells them differently (Windows's 3.11 without lxml writes `<x />` where the Mac's writes `<x/>`,
    # winfix, 4 November 2026), and the two files of JSON byte for byte
    ships = all(support.same_workbook(first / c / n, ta_src / "pristine" / n)
                for c, n in zip(make_demo.CASES, names)) and all(
        sha(first / f) == sha(ta_src / "pristine" / f) for f in (make_demo.GETS_FILE, make_demo.CODES_FILE))
    check("325: the thematic analysis demo builds from its sources the same bytes twice, and the same as it ships",
          same and ships, f"same {same}, ships {ships}")

    # ── what it holds: a thematic analysis project of the same three participants, codes on extracts, notes, a board
    project = json.loads((ta_src / server_mod.PROJECT_FILE).read_text(encoding="utf-8"))
    listed = json.loads((first / make_demo.CODES_FILE).read_text(encoding="utf-8"))
    people = codes_mod.study_rows(make_demo.ta_books(first))
    extracts = codes_mod.extracts_of(people)
    by_extract: dict = {}
    for x in extracts:
        by_extract.setdefault((x["case"], x["row"], x["quote"]), []).append(x["code"])
    notes = sum(1 for case in make_demo.CASES for t in json.loads(
        (ta_src / "source" / f"{case} - coding.json").read_text(encoding="utf-8"))["turns"] if t.get("note"))
    ipa_csv = [(shipped / "source" / f"{c} - interview.csv").read_bytes() for c in make_demo.CASES]
    check("325: a thematic analysis project of the IPA demo's three participants, from the same interviews, every "
          "code in its list with a description, several codes on some extracts, and notes",
          project.get("method") == "ta" and sorted(p["case"] for p in people) == sorted(make_demo.CASES)
          and all(make_demo.ta_sources(c, shipped)[0].read_bytes() == b for c, b in zip(make_demo.CASES, ipa_csv))
          and len(listed["codes"]) >= 15 and all(c["description"] for c in listed["codes"])
          and sum(1 for codes in by_extract.values() if len(codes) > 1) >= 10 and notes >= 10,
          f"{len(listed['codes'])} codes, {len(by_extract)} extracts, {notes} notes")
    gets_data = json.loads((first / make_demo.GETS_FILE).read_text(encoding="utf-8"))
    board = gets_data["boards"][0]
    parents = {m: g["id"] for g in board["groups"] for m in g["members"]}
    subs = [g for g in board["groups"] if g["id"] in parents]
    with i18n.in_method("ta"):
        line = codes_mod.line_codes(gets_data)
    placed = {line[k] for k in board["cards"] if k in line}
    split = [code for code in placed if len({parents.get(k) for k in board["cards"] if line.get(k) == code}) > 1]
    check("325: its Themes board holds themes with definitions and notes, a subtheme inside a theme, each code's "
          "every extract under one theme, two codes not placed, and it is the Current board",
          len(board["groups"]) - len(subs) >= 3 and len(subs) >= 1
          and all(g.get("description") for g in board["groups"]) and any(g.get("note") for g in board["groups"])
          and not split and len(listed["codes"]) - len(placed) == 2
          and len(board["cards"]) == sum(1 for x in extracts if x["code"] in placed)
          and gets_data.get("chosen") == board["id"], f"{len(board['groups'])} labels, {len(placed)} codes placed, {split}")

    # ── a scratch demo with both demos, read as the server reads them
    demo = scratch / "a325-demo"
    ship = scratch / "a325-shipped"
    for folder in (demo, ship):
        shutil.rmtree(folder, ignore_errors=True)
    shutil.copytree(support.DEMO_PRISTINE, ship / "pristine")
    shutil.copytree(ta_src / "pristine", ship / "ta" / "pristine")
    for root, src in ((demo, shipped), (demo / "ta", ta_src)):
        root.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(src / server_mod.PROJECT_FILE, root / server_mod.PROJECT_FILE)
    own = scratch / "a325-own"
    shutil.rmtree(own, ignore_errors=True)
    (own / "Wren").mkdir(parents=True)
    shutil.copyfile(support.DEMO_WORKBOOK, own / "Wren" / "Wren - EN & ES.xlsx")
    (own / server_mod.PROJECT_FILE).write_text(json.dumps({"name": "Keeping bees"}), encoding="utf-8")
    config = scratch / "a325-config.json"
    config.write_text(json.dumps({"projects": [{"root": str(own)}], "corpus": "", "gravity_reference": "",
                                  "corpus_exclude": [], "interviewer": "Adam"}), encoding="utf-8")
    kept = {k: getattr(server_mod, k) for k in ("DEMO_DIR", "SHIPPED_DEMO", "DEMO_CASE", "DEMO_WORKBOOK", "DEMO_PROJECT",
                                                "CONFIG_PATH", "STATE_MEMORY", "ROOT_OVERRIDE")}
    try:
        server_mod.DEMO_DIR, server_mod.SHIPPED_DEMO = demo, ship
        server_mod.DEMO_CASE = demo / "Juno"
        server_mod.DEMO_WORKBOOK = server_mod.DEMO_CASE / "Juno - EN & ES.xlsx"
        server_mod.DEMO_PROJECT = demo / server_mod.PROJECT_FILE
        server_mod.CONFIG_PATH, server_mod.STATE_MEMORY, server_mod.ROOT_OVERRIDE = config, {"recent": []}, None
        filled = idiograph_routes.fill_demo()
        ta = server_mod.demo_ta_dir()
        check("325: a start fills both demos from the shipped copy, the thematic analysis demo's code list and Themes "
              "board at its root",
              (ta / make_demo.CODES_FILE).is_file() and (ta / make_demo.GETS_FILE).is_file()
              and all((root / c / f"{c} - EN & ES.xlsx").is_file() for root in (demo, ta) for c in make_demo.CASES)
              and len(filled) >= 14, f"{len(filled)} files")

        home = idiograph_routes.api_cases({})
        p_ta = home.get("demo_ta_project") or {}
        check("325: Home's answer lists the two demos apart from his projects, the IPA demo's three and the thematic "
              "analysis demo's three, each project its own",
              [s["project"]["name"] for s in home["projects"]] == ["Keeping bees"]
              and [d["case"] for d in home["demos"]] == list(make_demo.CASES)
              and [d["case"] for d in home["demos_ta"]] == list(make_demo.CASES)
              and all(Path(d["path"]).parts[-3:] == ("ta", d["case"], f"{d['case']} - EN & ES.xlsx") for d in home["demos_ta"])
              and p_ta.get("method") == "ta" and p_ta.get("id") == "demo-ta" and p_ta.get("demo") is True
              and home["demo_project"]["method"] == "ipa" and home["demo_project"]["id"] == "demo",
              json.dumps({k: home.get(k) for k in ("demo_ta_project",)}, default=str)[:300])
        check("325: the IPA demo never reads the thematic analysis demo's participants as cases of its own, nor its "
              "board's study",
              sorted(r["case"] for r in idiograph_routes.list_cases(demo)) == sorted(make_demo.CASES)
              and not any(Path(r["path"]).parts[-3] == "ta" for r in idiograph_routes.list_cases(demo))
              and sorted(b["case"] for b in idiograph_routes.gets_books(demo)) == sorted(make_demo.CASES)
              and all("/ta/" not in str(b["workbook"]).replace("\\", "/") for b in idiograph_routes.gets_books(demo))
              and all(server_mod.same_folder(server_mod.project_of(b["workbook"]), ta) for b in idiograph_routes.gets_books(ta)))

        juno_ta = ta / "Juno" / "Juno - EN & ES.xlsx"
        codes_read = idiograph_routes.api_codes({"root": "demo-ta"})
        check("325: the thematic analysis demo opens as a thematic analysis project, its case's project the demo's own, "
              "its code list read with every description",
              idiograph_routes.read_project(server_mod.project_of(juno_ta))["method"] == "ta"
              and server_mod.project_named("demo-ta") == ta and idiograph_routes.project_id(ta) == "demo-ta"
              and len(codes_read["codes"]) == len(listed["codes"])
              and all(c.get("description") for c in codes_read["codes"]),
              str(sorted(codes_read.keys()))[:200])

        refusals = []
        for call in (lambda: idiograph_routes.api_project({"root": "demo-ta", "name": "Another"}),
                     lambda: idiograph_routes.write_order(ta, list(make_demo.CASES)),
                     lambda: idiograph_routes.send_root("demo-ta")):
            try:
                call()
                refusals.append(False)
            except Exception:  # noqa: BLE001
                refusals.append(True)
        check("325: the thematic analysis demo's project, order and Share a copy are fixed as the IPA demo's are",
              all(refusals), str(refusals))

        # Reset demo on the thematic analysis demo's page: its files put back, the IPA demo's left alone
        before_ipa = tree(demo / "Juno")
        (ta / make_demo.CODES_FILE).write_text("{}", encoding="utf-8")
        shutil.copyfile(support.DEMO_WORKBOOK, juno_ta)
        answer = idiograph_routes.api_reset_demo({"demo": "ta"})
        check("325: Reset demo with demo ta puts the thematic analysis demo back as it ships, its code list with it, "
              "and leaves the IPA demo alone",
              answer.get("demo") == "demo-ta" and sha(ta / make_demo.CODES_FILE) == sha(ta_src / "pristine" / make_demo.CODES_FILE)
              and sha(juno_ta) == sha(ta_src / "pristine" / "Juno - EN & ES.xlsx") and tree(demo / "Juno") == before_ipa,
              json.dumps(answer))

        # the command line: --demo the IPA demo as ever, --demo ta and --demo=ta the thematic analysis one
        code, out, err = cli.run(["--demo", "--config", str(config), "cases", "--json"])
        ipa = support.plain(json.loads(out)) if code == 0 else {}
        code_ta, out_ta, err_ta = cli.run(["--demo", "ta", "--config", str(config), "cases", "--json"])
        tad = support.plain(json.loads(out_ta)) if code_ta == 0 else {}
        code_eq, out_eq, _ = cli.run(["cases", "--json", "--demo=ta", "--config", str(config)])
        eq = support.plain(json.loads(out_eq)) if code_eq == 0 else {}
        check("325: --demo still reads the IPA demo, and --demo ta (or --demo=ta) the thematic analysis demo",
              code == 0 and ipa["project"]["demo"] and ipa["project"].get("method", "ipa") == "ipa"
              and code_ta == 0 and tad["project"]["demo"] and tad["project"]["method"] == "ta"
              and [c["case"] for c in tad["cases"]] == sorted(make_demo.CASES)
              and code_eq == 0 and eq["project"]["method"] == "ta", (err or err_ta or out_ta)[:300])
        check("325: a word after --demo that names no demo is the command, as ever",
              cli.demo_words(["--demo", "cases"]) == ["--demo", "cases"]
              and cli.demo_words(["--demo", "ta", "cases"]) == ["--demo", "--demo-ta", "cases"]
              and cli.demo_words(["--demo=ipa", "cases"]) == ["--demo", "cases"]
              and cli.demo_asked(["--demo", "ta"]) == "ta" and cli.demo_asked(["--demo"]) is True
              and cli.demo_asked(["cases"]) is False)
        import mcp_server
        entry = mcp_server.desktop_entry(ta, demo="ta")
        check("325: an agent's entry for the thematic analysis demo runs the MCP server with --demo ta, the IPA "
              "demo's with --demo",
              entry["args"][-2:] == ["--demo", "ta"] and mcp_server.desktop_entry(demo, demo=True)["args"][-1] == "--demo")
    finally:
        for k, v in kept.items():
            setattr(server_mod, k, v)

    # ── the Mac build stages the thematic analysis demo inside the demo, as Reset demo leaves it
    spec = importlib.util.spec_from_file_location("idiograph_build_mac_325", support.source("packaging/build_mac.py"))
    build = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(build)
    stage = scratch / "a325-stage"
    shutil.rmtree(stage, ignore_errors=True)
    stage.mkdir(parents=True)
    staged = tree(build.stage_cases(stage))
    want = [f"ta/{c}/{c} - EN & ES.xlsx" for c in make_demo.CASES] + [
        f"ta/{c}/Working/{c} - EN & ES.progress.json" for c in make_demo.CASES] + [
        f"ta/{make_demo.GETS_FILE}", f"ta/{make_demo.CODES_FILE}", "ta/idiograph-project.json",
        f"ta/pristine/{make_demo.CODES_FILE}"]
    check("325: the Mac build stages the thematic analysis demo inside the demo with its code list and Themes board",
          all(w in staged for w in want) and staged[f"ta/{make_demo.CODES_FILE}"] == staged[f"ta/pristine/{make_demo.CODES_FILE}"],
          str([w for w in want if w not in staged])[:200])

    # ── Home's fold, the page's own code in node
    shell_js = support.text("family/static/shell.js")
    distil_js = support.text("apps/idiograph/static/distil.js")
    shell_part = piece(shell_js, "function shutIds()", "/* a section's head folds it")
    distil_part = piece(distil_js, "const DEMOS_OPEN", "/* The picker: Distil's cards")
    script = FOLD.replace("SHELL", "const FOLD_KEY = 'idiograph-shut';\n" + shell_part).replace("DISTIL", distil_part)
    run = support.run_node(script, scratch, "a325-fold.js")
    try:
        out = json.loads(run.stdout.strip().splitlines()[-1])
    except (ValueError, IndexError):
        out = {}
    check("325: Home's Demo projects section is shut by default beside his projects, open on a Home with none, and "
          "kept as he leaves it, opened or shut, across a reload",
          out == {"withProjects": True, "noProjects": False, "closed": True, "keptShutNone": True, "opened": False,
                  "keptOpen": False, "expanded": "true"},
          (run.stdout + run.stderr)[-400:])
