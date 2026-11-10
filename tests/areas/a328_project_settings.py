"""Area 328: Project settings, a project's own sheet apart from Settings (settingsplit, Adam, 5 November 2026).
Settings holds the app's settings alone, the same on Home and in a project, and each project's own are on a sheet
for that project with no picker. What each saves and where: the statement length, typed in the sheet, goes to the
project's own file through `/api/project` for the sheet's project, with the case's workbook beside it when the
case open is that project's, and the statements screen behind takes it at once, its counts and nudges at the new
number, which the nudges route then speaks at. GETs' rules are asked by the case's workbook, a demo's first one,
or the project's id. Settings' Save sends no project's settings. The projects are invented: walks with a dog."""
from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path

from . import support
from .a316_code_list import make_project
from .support import check, skip


def test_project_settings(scratch: Path):
    print("\n328. Project settings: a project's own sheet, the statement length to its file and to the nudge, GETs "
          "asked for its project, Settings saving no project's settings (5 November)")
    import idiograph_routes as routes
    import server as server_mod

    page = support.page_text()
    js = support.text("family/static/shell.js", "apps/idiograph/static/distil.js")
    fn = lambda name: js.split(f"function {name}(", 1)[1].split("\n}", 1)[0]

    # ── A. the markup: the number in the sheet, none in Settings
    settings = page.split('<div class="overlay" id="settings"', 1)[1].split('<div class="overlay"', 1)[0]
    sheet = page.split('<div class="overlay" id="projset"', 1)[1].split('<div class="overlay"', 1)[0]
    check("328: the statement length's field is in Project settings and not in Settings, nor any project field",
          'id="words-n"' in sheet and 'id="words-n"' not in settings and "words-n" not in fn("nudgeRow")
          and 'id="set-project-name"' in sheet and 'id="set-project-name"' not in settings
          and 'id="gets-fields"' in sheet and 'id="pane-project"' not in page and 'id="pane-gets"' not in page)
    check("328: Settings' Save asks for no project's settings, and Project settings' Save sends GETs and the project",
          "projectSaves" not in fn("distilSettingsBody") and "getsBody" not in fn("distilSettingsBody")
          and "getsBody()" in fn("saveProjectSettings") and "projectSaves()" in fn("saveProjectSettings"))

    # ── B. the length saved for the project, read back by the nudges route
    base = scratch / "project-settings-328"
    root = base / "Walks"
    make_project(root, "ipa")
    config_file = base / "config.json"
    config_file.write_text(json.dumps({"projects": [{"root": str(root)}], "interviewer": "Adam", "corpus": "",
                                       "gravity_reference": "", "corpus_exclude": [],
                                       "nudges": {"length": True}}), encoding="utf-8")
    kept = (server_mod.CONFIG_PATH, server_mod.ROOT_OVERRIDE, server_mod.STATE_MEMORY)
    book = next(root.glob("*/*.xlsx"))
    server_mod.CONFIG_PATH, server_mod.ROOT_OVERRIDE = config_file, None
    server_mod.STATE_MEMORY = {"recent": []}
    try:
        pid = routes.api_projects({"op": "read"})["projects"][0]["id"]
        said = routes.api_project({"root": pid, "statement_words": 18})["project"]
        text = " ".join(["walks"] * 17) + "\n" + " ".join(["walks"] * 19)
        nudged = routes.api_nudges({"text": text, "path": str(book)})
        on_disk = json.loads((root / server_mod.PROJECT_FILE).read_text(encoding="utf-8"))
    finally:
        server_mod.CONFIG_PATH, server_mod.ROOT_OVERRIDE, server_mod.STATE_MEMORY = kept
    check("328: the length saved by the sheet's call is in the project's file and the nudges speak at it",
          said["statement_words"] == 18 and on_disk.get("statement_words") == 18 and nudged["statement_words"] == 18
          and [ln["line"] for ln in nudged["lines"] if any("length" in str(f) for f in ln["flags"])] == [1],
          str(nudged)[:300])

    # ── C. the page's own code in node: the length, the target for GETs
    node = shutil.which("node")
    if not node:
        skip("328: Project settings in node", "node is not installed")
        return
    line_of = lambda name: next(ln for ln in js.splitlines() if ln.startswith(f"const {name} = "))
    pieces = [line_of("PROJ"), line_of("projectAt"), line_of("WORDS_DEFAULT"), line_of("WORDS_MIN"), line_of("WORDS_MAX"),
              line_of("WORDS"), line_of("wordBand"), line_of("isDemoId"), line_of("DEMO_ID"), line_of("DEMO_TA_ID")]
    whole = lambda name: ("async " if f"async function {name}(" in js else "") + "function " + name + "(" + fn(name) + "\n}"
    pieces += [whole(n) for n in ("projectBehind", "getsTarget", "projectBody", "wordsOf", "wordsSet", "saveWords")]
    script = base / "projset-328.js"
    script.write_text(support.i18n_js() + r"""
const calls = [];
const answers = { A: { id: 'A', name: 'Walks', statement_words: 18 }, B: { id: 'B', name: 'Gardens', statement_words: 12 } };
async function api(path, body) { calls.push([path, JSON.parse(JSON.stringify(body))]); return { project: answers[body.root] }; }
const RESTART_LINE = 'restart';
const needsRestart = () => false;
const els = {};
const $ = (id) => els[id] || (els[id] = { value: '', hidden: false, disabled: false, title: '', textContent: '' });
const document = { activeElement: null };
let behind = null;
function settingsCase() { return behind; }
function drawWords() {}
function wordsSaid() {}
let counted = 0, nudged = 0;
function drawWordCount() { counted += 1; }
function runNudges() { nudged += 1; }
const S = { data: null, lib: { demo_rows: [] } };
function demosOf() { return [{ id: 'demo', rows: [{ path: 'demo/Juno.xlsx' }] }]; }
""" + "\n".join(pieces) + r"""
(async () => {
  const out = {};
  const A = { id: 'A', name: 'Walks', statement_words: 15 };
  const B = { id: 'B', name: 'Gardens', statement_words: 15 };
  // the sheet over A's participant: its workbook goes with the request, and the statements screen takes the answer
  S.data = { path: 'walks/Ash.xlsx', project: A };
  behind = { path: 'walks/Ash.xlsx', project: A };
  PROJ.own = projectBehind(A); PROJ.p = A;
  out.behindA = !!projectBehind(A); out.behindB = !!projectBehind(B);
  out.getsA = getsTarget(A); out.getsB = getsTarget(B); out.getsDemo = getsTarget({ id: 'demo', demo: true });
  wordsSet('18', true);
  await new Promise((ok) => setTimeout(ok, 600));
  out.sentA = calls.slice();
  out.bandA = wordBand();
  out.redrawn = [counted, nudged];
  // the sheet for B from Home: by its id alone, and the statements screen's project left as it was
  calls.length = 0; counted = 0; nudged = 0;
  behind = { path: null, project: null };
  PROJ.own = null; PROJ.p = B;
  wordsSet('12', true);
  await new Promise((ok) => setTimeout(ok, 600));
  out.sentB = calls.slice();
  out.bandAfterB = wordBand();
  out.redrawnB = [counted, nudged];
  // the demo's is fixed: nothing sent
  calls.length = 0;
  PROJ.p = { id: 'demo', demo: true, statement_words: 15 };
  wordsSet('20', true);
  await new Promise((ok) => setTimeout(ok, 600));
  out.sentDemo = calls.slice();
  console.log(JSON.stringify(out));
})();
""", encoding="utf-8")
    run = subprocess.run([node, str(script)], capture_output=True, text=True, encoding="utf-8", timeout=60)
    if run.returncode != 0:
        check("328: Project settings runs in node", False, run.stderr.strip()[:400])
        return
    o = json.loads(run.stdout.strip().splitlines()[-1])
    check("328: GETs' rules are asked by the participant's workbook when the sheet is for its project, by the project's "
          "id from Home, and by a demo's first workbook",
          o["behindA"] is True and o["behindB"] is False and o["getsA"] == {"workbook": "walks/Ash.xlsx"}
          and o["getsB"] == {"root": "B"} and o["getsDemo"] == {"workbook": "demo/Juno.xlsx"}, json.dumps(o)[:300])
    check("328: the length typed in the sheet over a participant is saved for its project with the workbook, and the "
          "statements screen's count and nudges take it at once",
          o["sentA"] == [["/api/project", {"root": "A", "path": "walks/Ash.xlsx", "statement_words": 18}]]
          and o["bandA"] == 18 and o["redrawn"] == [1, 1], json.dumps(o)[:300])
    check("328: the length for another project, from Home, goes by its id alone and leaves the open participant's "
          "project as it was, and the demo's sends nothing",
          o["sentB"] == [["/api/project", {"root": "B", "statement_words": 12}]] and o["bandAfterB"] == 18
          and o["redrawnB"] == [0, 0] and o["sentDemo"] == [], json.dumps(o)[:300])
