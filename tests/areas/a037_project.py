from __future__ import annotations

import json
from pathlib import Path

import ai_suggest as ai_mod
from workbook import WorkbookError

from . import support
from .support import DEMO_QUESTION, GRAVITY_QUESTION, check, demo_copy
import idiograph_routes
import statement_prompts


def test_project(scratch):
    print("\n37. The project: its file at the root, the research question band, the prompt that follows it")
    import datetime as dt
    import server as server_mod
    static = server_mod.HERE / "static"
    page = support.page_text()
    js = support.text("family/static/shell.js", "apps/idiograph/static/distil.js")

    # The live root's project file is the coordinator's to write, and the demo's is committed. Both
    # are compared by their stat before and after, and neither is ever opened here for writing.
    def stamp_of(p: Path):
        return (p.exists(), p.stat().st_mtime_ns, p.stat().st_size) if p.exists() else (False, 0, 0)

    # every project the live settings name, read before anything here points the server elsewhere
    live_files = [server_mod.configured(entry["root"]) / server_mod.PROJECT_FILE
                  for entry in server_mod.projects_in(server_mod.saved_config())]
    live_before = [stamp_of(f) for f in live_files]
    demo_before = stamp_of(server_mod.DEMO_PROJECT)

    # ── A. the demo's own file, committed beside it
    shipped = json.loads(server_mod.DEMO_PROJECT.read_text(encoding="utf-8"))
    check("the demo ships its own project file with a name, a question and a timestamp",
          server_mod.DEMO_PROJECT == server_mod.DEMO_DIR / "idiograph-project.json"
          and set(shipped) == {"name", "research_question", "updated"}
          and shipped["name"] == "Living with a dog" and shipped["research_question"] == DEMO_QUESTION
          and dt.datetime.fromisoformat(shipped["updated"]).tzinfo is not None, str(shipped))

    # ── B. the file at a scratch root, read and written there and nowhere else
    root = scratch / "project-root"
    wren = demo_copy(root, "P8 - Wren", "P8 Wren - EN & ES.xlsx")
    writes = []
    real_save = server_mod.save_json

    def recorded(path, data):
        writes.append(Path(path))
        return real_save(path, data)

    kept = (server_mod.ROOT_OVERRIDE, server_mod.STATE_PATH, server_mod.STATE_MEMORY,
            server_mod.CONFIG_PATH, server_mod.save_json, ai_mod.find_key, ai_mod.http_call)
    server_mod.ROOT_OVERRIDE = str(root)
    server_mod.STATE_PATH = scratch / "project-state.json"
    server_mod.STATE_MEMORY = {"recent": []}
    server_mod.CONFIG_PATH = scratch / "project-config.json"
    server_mod.save_json = recorded
    target = root / server_mod.PROJECT_FILE
    try:
        fresh = idiograph_routes.read_project(root)
        check("with no file the project takes its root folder's name and has no question",
              fresh["name"] == "project-root" and fresh["research_question"] == ""
              and fresh["updated"] is None and fresh["demo"] is False and not target.exists(), str(fresh))
        named = scratch / "P9 - {}-{}".format("Alpha", "Beta")
        named.mkdir(parents=True, exist_ok=True)
        check("a root that is a case folder is named by its pseudonym alone",
              idiograph_routes.read_project(named)["name"] == "P9 - Alpha")
        check("the root it shows is the root the library shows",
              fresh["root"] == server_mod.display_path(server_mod.rel_path(root)))
        cases = idiograph_routes.api_cases({})
        check("/api/cases carries the project of the root", cases.get("project") == fresh, str(cases.get("project")))
        opened = idiograph_routes.api_open({"path": str(wren)})
        check("/api/open carries it too, for a case under the root",
              opened.get("project") == fresh, str(opened.get("project")))
        check("reading the project wrote nothing", not writes and not target.exists())

        answer = idiograph_routes.api_project({"name": "  Living with gravity ", "path": str(wren),
                                         "research_question": "  " + GRAVITY_QUESTION + "\n"})
        on_disk = json.loads(target.read_text(encoding="utf-8"))
        check("a save writes idiograph-project.json at the scratch root, trimmed",
              set(on_disk) == {"name", "research_question", "updated"}
              and on_disk["name"] == "Living with gravity" and on_disk["research_question"] == GRAVITY_QUESTION,
              str(on_disk))
        when = dt.datetime.fromisoformat(on_disk["updated"])
        check("updated is an ISO timestamp with its offset, taken at the save",
              when.tzinfo is not None
              and abs((dt.datetime.now(dt.timezone.utc) - when).total_seconds()) < 300, on_disk["updated"])
        check("the answer is the project as it now reads",
              answer["project"]["name"] == "Living with gravity"
              and answer["project"]["research_question"] == GRAVITY_QUESTION)
        check("/api/cases and /api/open read the file afresh",
              idiograph_routes.api_cases({})["project"]["research_question"] == GRAVITY_QUESTION
              and idiograph_routes.api_open({"path": str(wren)})["project"]["research_question"] == GRAVITY_QUESTION)
        count = len(writes)
        check("/api/project with neither field reads and writes nothing",
              idiograph_routes.api_project({})["project"]["name"] == "Living with gravity" and len(writes) == count)
        on_disk["note"] = "kept"
        target.write_text(json.dumps(on_disk), encoding="utf-8")
        idiograph_routes.api_project({"name": "", "research_question": ""})
        again = json.loads(target.read_text(encoding="utf-8"))
        check("a later save keeps any other key in the file, and stores an empty question empty",
              again.get("note") == "kept" and again["research_question"] == "" and again["name"] == "")
        check("an empty name reads as the root folder's name again",
              idiograph_routes.read_project(root)["name"] == "project-root")
        check("every write landed in the scratch root, in the project file",
              writes and all(w.resolve() == target.resolve() for w in writes),
              f"{len(writes)} writes")

        # the demo: its own file, whatever the root's says, and never a save
        demo_project = (idiograph_routes.api_open({"path": str(server_mod.DEMO_WORKBOOK)})["project"]
                        if server_mod.DEMO_WORKBOOK.exists()
                        else idiograph_routes.read_project(idiograph_routes.project_root(server_mod.DEMO_WORKBOOK)))
        check("the demo opens with its own project, read from its own file",
              demo_project["name"] == "Living with a dog"
              and demo_project["research_question"] == DEMO_QUESTION and demo_project["demo"] is True
              and idiograph_routes.project_root(server_mod.DEMO_WORKBOOK) == server_mod.DEMO_DIR, str(demo_project))
        check("asked about the demo, /api/project reads the demo's file",
              idiograph_routes.api_project({"path": str(server_mod.DEMO_WORKBOOK)})["project"]["research_question"]
              == DEMO_QUESTION)
        count = len(writes)
        refused = False
        try:
            idiograph_routes.api_project({"path": str(server_mod.DEMO_WORKBOOK), "research_question": "Anything else?"})
        except WorkbookError:
            refused = True
        check("a save for the demo is refused, and nothing is written",
              refused and len(writes) == count and stamp_of(server_mod.DEMO_PROJECT) == demo_before)

        # a root that is not there: refused, and no folder made to hold the file
        server_mod.ROOT_OVERRIDE = str(scratch / "no-such-root")
        refused = False
        try:
            idiograph_routes.api_project({"name": "x", "research_question": "y"})
        except WorkbookError:
            refused = True
        check("a root that is not there is refused, and nothing is made to hold the file",
              refused and not (scratch / "no-such-root").exists() and len(writes) == count)
        server_mod.ROOT_OVERRIDE = str(root)

        # ── C. the prompt follows the project, through the server, on a fake transport
        server_mod.save_json = real_save
        idiograph_routes.api_project({"name": "Living with gravity", "research_question": GRAVITY_QUESTION})
        sent = []

        def wire(method, url, headers, payload, timeout):
            sent.append(payload)
            body = {"tags": ["t"], "candidates": ["A candidate"]}
            return 200, json.dumps({"content": [{"type": "text", "text": json.dumps(body)}], "stop_reason": "end_turn"})

        ai_mod.find_key = lambda *a, **kw: "k-test"
        ai_mod.http_call = wire
        server_mod.CONFIG_PATH.write_text(json.dumps({"ai_suggest": True}), encoding="utf-8")
        idiograph_routes.api_suggest({"turn": "My hands were shaking.", "prior": "And?", "path": str(wren)})
        check("a suggestion on a case carries its root's question in the system prompt",
              len(sent) == 2 and f"The study asks: {GRAVITY_QUESTION}" in sent[0]["system"]
              and "{research_question}" not in sent[0]["system"] and sent[0]["system"] == sent[1]["system"])
        sent.clear()
        idiograph_routes.api_suggest({"turn": "My hands were shaking.", "prior": "And?",
                                "path": str(server_mod.DEMO_WORKBOOK)})
        check("a suggestion on the demo carries the demo's question",
              sent and f"The study asks: {DEMO_QUESTION}" in sent[0]["system"]
              and GRAVITY_QUESTION not in sent[0]["system"])
        sent.clear()
        idiograph_routes.api_suggest({"turn": "My hands were shaking."})
        check("a page that sends no path gets the root's question",
              sent and f"The study asks: {GRAVITY_QUESTION}" in sent[0]["system"])
        sent.clear()
        idiograph_routes.api_suggest_sample({"text": "Adam: And then?\nJuno: My hands were shaking.",
                                       "provider": "anthropic", "research_question": "A bench question"})
        check("the bench sends the question as it stands in the panel, saved or not",
              sent and "The study asks: A bench question. Every statement" in sent[0]["system"])
        idiograph_routes.api_project({"name": "Living with gravity", "research_question": ""})
        sent.clear()
        idiograph_routes.api_suggest({"turn": "My hands were shaking.", "path": str(wren)})
        check("with no question the placeholder goes with its sentence",
              sent and "The study asks" not in sent[0]["system"] and "{research_question}" not in sent[0]["system"]
              and "\n\n\n" not in sent[0]["system"])
        server_mod.CONFIG_PATH.write_text(json.dumps({"ai_suggest": True, "ai_prompt": "Only this. Answer in JSON."}),
                                          encoding="utf-8")
        idiograph_routes.api_project({"name": "Living with gravity", "research_question": GRAVITY_QUESTION})
        sent.clear()
        idiograph_routes.api_suggest({"turn": "My hands were shaking.", "path": str(wren)})
        check("a stored template without the placeholder is sent as it stands",
              sent and sent[0]["system"] == "Only this. Answer in JSON.", sent[0]["system"] if sent else "")
    finally:
        (server_mod.ROOT_OVERRIDE, server_mod.STATE_PATH, server_mod.STATE_MEMORY,
         server_mod.CONFIG_PATH, server_mod.save_json, ai_mod.find_key, ai_mod.http_call) = kept
    check("every live project's file is exactly as it was", [stamp_of(f) for f in live_files] == live_before,
          f"{sum(1 for b in live_before if b[0])} present of {len(live_before)}")
    check("so is the demo's", stamp_of(server_mod.DEMO_PROJECT) == demo_before)
    check("the route is there", server_mod.ROUTES.get("/api/project") is idiograph_routes.api_project)

    # ── D. the placeholder itself
    check("the default prompt carries {research_question} and no study of its own",
          "{research_question}" in statement_prompts.DEFAULT_PROMPT and "altered gravity" not in statement_prompts.DEFAULT_PROMPT
          and "parabolic" not in statement_prompts.DEFAULT_PROMPT and server_mod.defaults()["ai_prompt"] == statement_prompts.DEFAULT_PROMPT)
    empty = statement_prompts.system_prompt(["One idea each."], ["Never getting to have it out"], research_question="  ")
    check("empty, it goes with its sentence and leaves no hole",
          "The study asks" not in empty and "{research_question}" not in empty and "\n\n\n" not in empty
          and "rewrites or discards.\n\nAn experiential statement is" in empty)
    check("a question with no closing mark gets a full stop, and a broken line is one line",
          statement_prompts.question_block("What is it like\nto float") .startswith("The study asks: What is it like to float. ")
          and statement_prompts.question_block(None) == "")

    # ── F. Project settings (in Settings, under Projects, until settingsplit, 5 November 2026)
    card = page.split('<div class="overlay" id="projset"', 1)[1].split('<div class="overlay"', 1)[0]
    check("the demo's project is shown read-only, with a line saying it is fixed",
          'id="project-fixed" hidden>The demo\'s project is fixed.</p>' in card
          and "$('set-question').readOnly = fixed;" in js and "$('project-fixed').hidden = !fixed;" in js)
    opener = js.split("function openProjectSettings(", 1)[1].split("\n}", 1)[0]
    own_open = js.split("function distilSettingsOpen(", 1)[1].split("\n}", 1)[0]
    check("Project settings is drawn from the project it was opened for, the screen behind's copy when it is that one, "
          "and Settings no longer holds a project",
          "const own = projectBehind(p);" in opener and "drawProjectPane(shown);" in opener and "show('projset');" in opener
          and "openProjects" not in js and "PROJ" not in own_open and 'id="pane-project"' not in page)
    saver = js.split("async function saveProjectSettings(", 1)[1].split("\n}", 1)[0]
    saves_fn = js.split("function projectSaves(", 1)[1].split("\n}", 1)[0]
    taker = js.split("function projectTake(", 1)[1].split("\n}", 1)[0]
    check("Save writes the project through /api/project, only when it changed, never for the demo",
          "await api('/api/project', sent)" in saver and "for (const sent of sends)" in saver
          and "if (!p || p.demo) return out;" in saves_fn and "drawBand();" in taker)
    asker = js.split("async function askAI(", 1)[1].split("\n}", 1)[0]
    bench_fn = js.split("async function runBench(", 1)[1].split("\n}", 1)[0]
    body_fn = js.split("function suggestBody(", 1)[1].split("\n}", 1)[0]
    check("the suggestion sends its case, and the bench the question in the panel",
          "suggestBody(" in asker and "path: S.data ? S.data.path : ''" in body_fn
          and "body.research_question = String(own.research_question || '');" in bench_fn)
