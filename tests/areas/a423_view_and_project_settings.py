"""Area 423: Settings holds the app's own settings alone, a screen's own are in its View, and the nudges and the
interviewer's name are a project's own (viewbuild, Adam's ruling of 17 November 2026).

The nudges: a project made from now on starts with every one off, the book's default; a project whose file has none,
every project made before, reads the nudges the app's settings held for every project until now, so it keeps what it
had; reading or opening a project writes nothing; the demos' are off; and an agent reads and sets them through the
route the statements screen's View uses (`project set --nudges`, MCP's project_set), its dry run writing nothing, its
write one line in the record of agents' changes and undone byte for byte. The interviewer's name likewise, from
Project settings: a project with none reads the app's settings' name, and every reader of it on the server (the
rounds, the statements screen's payload) reads the project's once it has one. Settings' Save no longer takes either.

And the rule, docs/design.md's row: the Settings dialog holds no screen's or project's setting (General, Language and
formats and AI features alone; no rounds, nudges, minimap, columns, status bar or interviewer there), the status bar's
on and off setting is gone, and every screen's top bar has Guidance before Search, Send feedback and Settings, View
before it only where a View has something the status bar has not (viewfix, Adam's ruling of 17 November 2026 about
12:40): the statements screen (and a thematic analysis project's Coding, the same screen) has View, the boards (PETs,
GETs, LPETs, LGETs and the Themes board, one screen), Trajectories and the Code list none.

Since viewfix: Work in rounds, its minutes and the rounds a day are a project's own too, as the nudges; a call to
/api/project refused for any one field writes none of them, with the statement length and the timepoints handled
beside the rest; a fresh install's settings, holding no nudges, read every nudge off; an interviewer's name empty or
a participant's is refused; the documents' name is Your name alone; every demo's project file names its interviewer;
and a status bar button of more than two states (the Minimap) takes the next state on a click and opens a menu of
them on a right click, each state set from it."""
from __future__ import annotations

import hashlib
import json
import re
import shutil
from pathlib import Path

from .support import check
from . import support

ASKED = "He asked for the nudges he uses"
LEGACY = {"length": True, "lead": True, "quote": False, "semicolon": True, "emdash": True, "arrow": False,
          "readsas": True}
LEGACY_ON = ["length", "lead", "semicolon", "emdash", "readsas"]


def digest(root: Path) -> dict:
    """Every file of the project by its contents, the locks, the record of agents' changes with its restore points
    and the project's History, a log the record never restores, set aside."""
    import agent_changes
    out = {}
    for p in sorted(root.rglob("*")):
        rel = p.relative_to(root).as_posix()
        if (not p.is_file() or p.name.endswith(".lock") or rel == agent_changes.FILE
                or rel.startswith(agent_changes.STORE) or "_Archive/" in rel or rel in agent_changes.NEVER):
            continue
        out[rel] = hashlib.sha256(p.read_bytes()).hexdigest()
    return out


def ordered_tools(page: str, section: str) -> list[str]:
    at = page.index(f'<section id="{section}"')
    rail = page.index('<div class="rail', at)
    end = page.index("\n  </div>", rail)
    out = []
    for m in re.finditer(r"<button\b[^>]*>", page[rail:end]):
        tag = m.group(0)
        if "bar-tool" in tag:
            out.append(re.search(r'id="([^"]+)"', tag).group(1))
    return out


def test_view_and_project_settings(scratch: Path):
    print("\n423. Settings the app's own alone, a screen's own in its View, the nudges and the interviewer a project's "
          "own (viewbuild, 17 November)")
    import agent_changes
    import agent_log
    import cli
    import mcp_server
    import os
    import idiograph_routes as routes
    import server as server_mod

    base = scratch / "view-423"
    shutil.rmtree(base, ignore_errors=True)
    old = base / "Old"
    old.mkdir(parents=True)
    demo = support.source("demo")
    held = json.loads((demo / server_mod.PROJECT_FILE).read_text(encoding="utf-8"))
    held["agents"] = {"allowed": True, "at": "2026-11-17T09:00:00+00:00"}
    held.pop("nudges", None)
    held.pop("interviewer", None)
    (old / server_mod.PROJECT_FILE).write_text(json.dumps(held, indent=2), encoding="utf-8")
    for who in ("Juno", "Mabel"):
        (old / who / "Working").mkdir(parents=True)
        shutil.copy2(demo / "pristine" / f"{who} - EN & ES.xlsx", old / who / f"{who} - EN & ES.xlsx")
    config_file = base / "config.json"
    config_file.write_text(json.dumps({"projects": [{"root": str(old)}], "interviewer": "Adam", "nudges": LEGACY,
                                       "status_bar": False, "corpus": "", "gravity_reference": "",
                                       "corpus_exclude": [], "work_in_rounds": True, "round_minutes": 12,
                                       "daily_target": 4}), encoding="utf-8")
    log = base / "agent-log.json"
    kept = (agent_changes.ALL_OPS, os.environ.get(agent_log.PLACE), server_mod.CONFIG_PATH, server_mod.STATE_PATH,
            server_mod.STATE_MEMORY)
    agent_changes.ALL_OPS = None
    os.environ[agent_log.PLACE] = str(log)
    server_mod.CONFIG_PATH = config_file
    server_mod.STATE_PATH = base / "state.json"
    server_mod.STATE_MEMORY = {"recent": []}

    def run(*args, root=old, tool="Claude Code"):
        given = ["--config", str(config_file), "--root", str(root), "--json", *args]
        if tool is not None:
            given += ["--tool", tool]
        return cli.run(given)

    try:
        start = digest(old)
        book = old / "Juno" / "Juno - EN & ES.xlsx"

        # A project from before keeps the nudges the app's settings held for every project, and reading it writes
        # nothing: the project's read, the statements screen's payload, the nudges' route and an agent's show
        project = routes.read_project(old)
        payload = routes.case_payload(book)
        lines = routes.api_nudges({"path": str(book), "text": "She said 'home' then; left"})["lines"]
        flags = {f["check"] for line in lines for f in line["flags"]}
        code, out, err = run("project", "show", tool=None)
        shown = support.plain(json.loads(out)) if code == 0 and out.strip() else {}
        check("423: a project from before reads the nudges the app's settings held, its interviewer the settings' name",
              project["nudges"] == LEGACY_ON and project["interviewer"] == "Adam"
              and payload["project"]["nudges"] == LEGACY_ON and payload["config"]["interviewer"] == "Adam"
              and (shown.get("project") or {}).get("nudges") == LEGACY_ON, json.dumps(project)[:300] + out[:300])
        check("423: the nudges' route speaks with the project's nudges, quote off there, lead and semicolon on",
              {"lead", "semicolon"} <= flags and "quote" not in flags, str(flags))
        check("423: reading and opening a project from before writes nothing", digest(old) == start, "")

        # the demos' nudges are off
        demo_project = routes.read_project(server_mod.DEMO_DIR)
        check("423: a demo's nudges are off", demo_project["nudges"] == [], str(demo_project.get("nudges")))

        # Settings' Save no longer takes the nudges or the interviewer, which are the project's
        cfg = {"nudges": dict(LEGACY), "interviewer": "Adam"}
        routes.save_settings(cfg, {"nudges": {"quote": True}, "interviewer": "Someone"})
        check("423: Settings' Save leaves the nudges and the interviewer as the file has them",
              cfg == {"nudges": LEGACY, "interviewer": "Adam"}, json.dumps(cfg))
        merged = server_mod.merge_config({"status_bar": False})
        check("423: the status bar's on and off setting is gone, a file's key passed over",
              "status_bar" not in merged and "status_bar" not in server_mod.defaults(), str(merged.get("status_bar")))

        # an agent's dry run says the change and writes nothing; MCP's likewise
        code, out, err = run("project", "set", "--nudges", "length,quote", "--interviewer", "Sam Reed", "--dry-run")
        answer = support.plain(json.loads(out)) if code == 0 and out.strip() else {}
        check("423: an agent's dry run of the nudges and the interviewer names both changes and writes nothing",
              code == 0 and answer.get("dry_run") is True and len(answer.get("changes") or []) == 2
              and (answer.get("project") or {}).get("nudges") == ["length", "quote"]
              and digest(old) == start and not agent_changes.read(old), (err or "")[:300] + out[:300])
        mcp = mcp_server.Server(str(old), config=str(config_file))
        mcp.receive(json.dumps({"jsonrpc": "2.0", "id": 1, "method": "initialize",
                                "params": {"protocolVersion": "2025-06-18", "clientInfo": {"name": "claude-code"}}}))
        res = mcp.receive(json.dumps({"jsonrpc": "2.0", "id": 2, "method": "tools/call", "params": {
            "name": "project_set", "arguments": {"nudges": [], "interviewer": "Sam Reed", "dry_run": True,
                                                 "request": ASKED}}}))["result"]
        check("423: MCP's project_set in a dry run takes the nudges and the interviewer and writes nothing",
              not res["isError"] and "Nudges on from" in json.dumps(res) and digest(old) == start
              and not agent_changes.read(old), json.dumps(res)[:400])

        # refusals, nothing written
        code, out, err = run("project", "set", "--nudges", "length,bogus", "--note", ASKED)
        check("423: an unknown nudge is refused in one line, nothing written",
              code != 0 and digest(old) == start and not agent_changes.read(old), (err or "")[:200] + out[:200])
        code, out, err = run("project", "set", "--nudges", "none", "--note", ASKED, root=server_mod.DEMO_DIR)
        check("423: a demo's nudges are fixed, refused", code != 0, out[:200])

        # viewfix, H1: a call refused for any one of its fields writes none of them, from an agent and on the route
        code, out, err = run("project", "set", "--interviewer", "Leah", "--nudges", "length,bogus", "--note", ASKED)
        check("423: a good interviewer beside an unknown nudge is refused whole, nothing written, no record line",
              code != 0 and digest(old) == start and not agent_changes.read(old), (err or "")[:200] + out[:200])
        refused = []
        for body in ({"name": "Renamed", "nudges": "bogus"}, {"name": "Renamed", "statement_words": 99},
                     {"interviewer": "Leah", "timepoints": "many"}, {"name": "Renamed", "round_minutes": 99},
                     {"nudges": {"length": 1}}, {"interviewer": ""}, {"interviewer": "juno"},
                     {"work_in_rounds": "maybe"}, {"daily_target": 0}):
            for dry in (True, False):
                try:
                    routes.api_project(dict(body, root=routes.project_id(old), dry_run=dry))
                    refused.append(("taken", body, dry))
                except routes.WorkbookError:
                    pass
        check("423: a call with any field refused writes nothing, dry run or real (a bad nudge, statement length, "
              "timepoints, minutes, a nudge neither true nor false, an empty interviewer, a participant's name)",
              not refused and digest(old) == start, str(refused)[:300])
        both = routes.api_project({"root": routes.project_id(old), "name": "Renamed", "statement_words": 20,
                                   "research_question": held.get("research_question"), "dry_run": True})
        check("423: a dry run of the name beside the statement length answers both, never dropping the name",
              both["project"]["name"] == "Renamed" and both["project"]["statement_words"] == 20
              and len(both["changes"]) == 2 and digest(old) == start, json.dumps(both["changes"]))

        # viewfix: the rounds, a project's own; a project from before reads the settings' rounds
        project = routes.read_project(old)
        payload = routes.case_payload(book)
        check("423: a project from before reads Work in rounds, its minutes and rounds a day from the settings",
              (project["work_in_rounds"], project["round_minutes"], project["daily_target"]) == (True, 12, 4)
              and (payload["config"]["work_in_rounds"], payload["config"]["round_minutes"]) == (True, 12)
              and digest(old) == start, json.dumps({k: project[k] for k in routes.ROUNDS_KEYS}))
        code, out, err = run("project", "set", "--rounds", "off", "--round-minutes", "15", "--rounds-a-day", "3",
                             "--dry-run")
        answer = support.plain(json.loads(out)) if code == 0 and out.strip() else {}
        check("423: an agent's dry run of the rounds names three changes and writes nothing",
              code == 0 and len(answer.get("changes") or []) == 3 and digest(old) == start
              and not agent_changes.read(old), (err or "")[:300] + out[:300])
        code, out, err = run("project", "set", "--rounds", "off", "--round-minutes", "15", "--rounds-a-day", "3",
                             "--note", ASKED)
        records = agent_changes.read(old)
        payload = routes.case_payload(book)
        check("423: the rounds' real write is one record line and the statements screen reads the project's",
              code == 0 and len(records) == 1 and payload["config"]["work_in_rounds"] is False
              and payload["config"]["round_minutes"] == 15 and payload["config"]["daily_target"] == 3,
              (err or "")[:300] + json.dumps(records)[:300])
        if records:
            code, out, err = run("agents", "undo-run", records[0]["run"], "--note", "Put it back")
            check("423: undoing the rounds' run puts the project file back byte for byte",
                  code == 0 and digest(old) == start, (err or "")[:300] + out[:300])
        cfg = {"work_in_rounds": True, "round_minutes": 12}
        routes.save_settings(cfg, {"work_in_rounds": False, "round_minutes": 30, "daily_target": 9})
        check("423: Settings' Save leaves the rounds as the file has them", cfg == {"work_in_rounds": True,
                                                                                  "round_minutes": 12}, json.dumps(cfg))
        check("423: a demo's rounds are off", routes.read_project(server_mod.DEMO_DIR)["work_in_rounds"] is False, "")

        # viewfix: every demo names its interviewer in its project file, the RTA demo's Leah
        shipped = support.source("demo")
        names = {sub: json.loads((shipped / sub / server_mod.PROJECT_FILE).read_text(encoding="utf-8")).get("interviewer")
                 for sub in (".", "ta", "lipa", "rta")}
        check("423: every demo's project file names its interviewer, Leah on the reflexive thematic analysis demo",
              names == {".": "Adam", "ta": "Adam", "lipa": "Adam", "rta": "Leah"}, str(names))

        # viewfix, L1 and M2: a fresh install's settings hold no nudges and no interviewer
        bare = base / "bare.json"
        bare.write_text(json.dumps({"projects": [{"root": str(old)}]}), encoding="utf-8")
        server_mod.CONFIG_PATH = bare
        check("423: on a fresh install a project with no nudges of its own reads every nudge off, no interviewer, "
              "and documents carry no name", routes.read_project(old)["nudges"] == []
              and routes.read_project(old)["interviewer"] == "" and routes.researcher_name() == "", "")
        bare.write_text(json.dumps({"projects": [{"root": str(old)}], "interviewer": "Adam"}), encoding="utf-8")
        check("423: documents never carry the interviewer's name in place of Your name", routes.researcher_name() == "",
              routes.researcher_name())
        # viewfix2, M-1: the file a fresh install's first start writes (shipped_config) and the file after one full
        # Settings save hold every nudge false, so a project with no nudges key reads them off
        shipped = base / "shipped.json"
        shipped.write_text(json.dumps({**server_mod.shipped_config(), "projects": [{"root": str(old)}]}), encoding="utf-8")
        server_mod.CONFIG_PATH = shipped
        off_shipped = routes.read_project(old)["nudges"]
        saved_only = base / "saved-once.json"
        saved_only.write_text(json.dumps({"projects": [{"root": str(old)}]}), encoding="utf-8")
        server_mod.CONFIG_PATH = saved_only
        server_mod.api_settings({"your_name": "Ada Lark"})
        held_after = json.loads(saved_only.read_text(encoding="utf-8")).get("nudges")
        off_saved = routes.read_project(old)["nudges"]
        check("423: with the config a fresh install's first start writes, and after one Settings save, a project with no "
              "nudges of its own reads every nudge off", off_shipped == [] and off_saved == []
              and isinstance(held_after, dict) and not any(held_after.values()), f"{off_shipped} {off_saved} {held_after}")
        server_mod.CONFIG_PATH = config_file

        # the real write: one record line, the project's own now, undone byte for byte
        earlier = len(agent_changes.read(old))
        code, out, err = run("project", "set", "--nudges", "length,quote", "--interviewer", "Sam Reed",
                             "--note", ASKED)
        records = agent_changes.read(old)[earlier:]
        after = routes.read_project(old)
        check("423: the real write is one record line and the project holds its own nudges and interviewer",
              code == 0 and len(records) == 1 and records[0].get("op") == "project set"
              and after["nudges"] == ["length", "quote"] and after["interviewer"] == "Sam Reed",
              (err or "")[:300] + json.dumps(records)[:300])
        payload = routes.case_payload(book)
        lines = routes.api_nudges({"path": str(book), "text": "She said 'home' then; left"})["lines"]
        flags = {f["check"] for line in lines for f in line["flags"]}
        check("423: the statements screen and the nudges' route read the project's own once it has them",
              payload["config"]["interviewer"] == "Sam Reed" and routes.interviewer_for(book) == "Sam Reed"
              and "quote" in flags and "lead" not in flags, str(flags))
        if records:
            code, out, err = run("agents", "undo-run", records[0]["run"], "--note", "Put it back")
            check("423: undoing the agent's run puts the project file back byte for byte",
                  code == 0 and digest(old) == start, (err or "")[:300] + out[:300])

        # a project made from now on starts with every nudge off
        fresh = base / "Fresh"
        fresh.mkdir()
        code, out, err = cli.run(["--config", str(config_file), "--json", "project", "new", str(fresh), "--name", "Fresh",
                                  "--transcript", str(server_mod.SAMPLE_CSV), "--pseudonym", "Kit",
                                  "--note", "A new project", "--tool", "Claude Code"])
        file_fresh = fresh / server_mod.PROJECT_FILE
        held_fresh = json.loads(file_fresh.read_text(encoding="utf-8")) if file_fresh.is_file() else {}
        check("423: a project made now starts with every nudge off and rounds off, written in its file with its "
              "interviewer, the speaker its transcript marks", code == 0 and held_fresh.get("nudges") == []
              and routes.read_project(fresh)["nudges"] == [] and held_fresh.get("work_in_rounds") is False
              and held_fresh.get("interviewer") == "Adam",
              (err or "")[:300] + json.dumps(held_fresh)[:300])

        # viewfix, L3: transcripts added to a project with no interviewer of its own, on a fresh install, write the
        # interviewer the rows mark into its file, and the new interviews' turns stand under that name
        bare_cfg = base / "bare-add.json"
        fresh2 = base / "Fresh two"
        fresh2.mkdir()
        (fresh2 / server_mod.PROJECT_FILE).write_text(json.dumps({"name": "Fresh two", "nudges": [], "agents": {"allowed": True, "at": "2026-11-17T09:00:00+00:00"}}), encoding="utf-8")
        bare_cfg.write_text(json.dumps({"projects": [{"root": str(fresh2)}]}), encoding="utf-8")
        listing = base / "add.json"
        listing.write_text(json.dumps([{"file": str(server_mod.SAMPLE_CSV), "pseudonym": "Kit", "interview": "Initial",
                                        "speakers": {"Adam": "interviewer", "Juno": "participant"}}]), encoding="utf-8")
        code, out, err = cli.run(["--config", str(bare_cfg), "--root", str(fresh2), "--json", "project",
                                  "add-transcripts", "--from", str(listing), "--note", "His interviews",
                                  "--tool", "Claude Code"])
        held_two = json.loads((fresh2 / server_mod.PROJECT_FILE).read_text(encoding="utf-8"))
        check("423: Add transcripts on a project with no interviewer writes the one the rows mark into its file",
              code == 0 and held_two.get("interviewer") == "Adam", (err or "")[:300] + json.dumps(held_two)[:200])
        server_mod.CONFIG_PATH = config_file

        # the Settings dialog holds no screen's or project's setting
        page = support.page_text()
        start_at = page.index('<div class="overlay" id="settings"')
        dialog = page[start_at:page.index('<div class="settings-foot">', start_at)]
        tabs = re.findall(r'role="tab" id="tab-([a-z]+)"', dialog)
        screen_ids = ("set-rounds", "set-minutes", "set-target", "nudge-switches", "data-nudge", "set-minimap",
                      "set-larger", "set-show-statements", "set-stacked", "set-widths-reset", "set-status-bar",
                      "set-interviewer", "pane-statements", "pane-pets")
        check("423: Settings has General, Language and formats and AI features alone, and none of a screen's or a "
              "project's settings", tabs == ["general", "formats", "ai"] and not [i for i in screen_ids if i in dialog],
              f"{tabs} {[i for i in screen_ids if i in dialog]}")
        check("423: the statement prompt, the test bench and PETs' model are under AI features, Your name under General",
              all(x in dialog[dialog.index('id="pane-ai"'):] for x in ('id="set-prompt"', 'id="bench"', 'id="set-pets-model"'))
              and 'id="set-your-name"' in dialog[dialog.index('id="pane-general"'):dialog.index('id="pane-formats"')], "")
        view = page[page.index('id="view-menu"'):]
        view = view[:view.index("\n  </div>")]
        check("423: the statements screen's View holds the larger passage, Work in rounds, its two numbers and the "
              "nudges, and no minimap, the status bar's",
              all(f'id="{i}"' in view for i in ("view-larger", "view-rounds", "view-minutes", "view-target", "view-nudges"))
              and "minimap" not in view, view[:200])
        check("423: no board, Trajectories or the Code list has a View or its menu",
              not [i for i in ("th-view", "th-viewmenu", "tj-view", "tj-viewmenu", "cd-view")
                   if f'id="{i}"' in page], "")
        check("423: Project settings holds the interviewer's name",
              'id="set-interviewer"' in page[page.index('id="projset"'):], "")

        # every screen's bar: View (the statements screen's alone) and Guidance, then Search, Send feedback and Settings
        for section, want in (("work", ["view", "guide"]), ("themes", ["guide"]), ("traj", ["guide"]),
                              ("codes-screen", ["guide"])):
            tools = ordered_tools(page, section)
            names = [re.sub(r"^(btn|th|tj|cd)-", "", t).replace("guide-btn", "guide") for t in tools]
            check(f"423: the {section} screen's bar has {' and '.join(want)} first, then Search, Send feedback and "
                  "Settings", names == want + ["search", "feedback", "settings"], str(tools))
        js = support.text("apps/idiograph/static/themes.js")
        check("423: a board's Guidance opens the sidebar on its Guidance tab, and the status bar is always drawn",
              "thSideOpen('guidance')" in js and "thStatusOn" not in js, "")
        # the Code list's Guidance: its own lines from ta_codes_guidance.md, eight with their examples
        rail = routes.api_guidance({}).get("codes") or {}
        codes_js = support.text("apps/idiograph/static/codes.js")
        check("423: the Code list's Guidance has its own lines, each with Less this and More this, opened from its bar",
              len(rail.get("lines") or []) == 8 and all(e.get("less") and e.get("more") for e in rail.get("examples") or [])
              and "$('cd-guide').onclick = () => cdGuide(!cdGuideOpen());" in codes_js
              and "drawRules(rail.lines || [], rail.examples || [], $('cd-rules'), 'cd-rule-ex');" in codes_js,
              str(len(rail.get("lines") or [])))
        # the page's scripts share one scope, so a function named as another screen's would stand in for it
        scripts = "".join(support.text(f"apps/idiograph/static/{n}.js") for n in ("distil", "themes", "trajectories", "codes"))
        names = ("viewRounds", "viewRoundNumber", "viewRoundsSave", "viewNudge", "thGuideButton", "thGuideToggle",
                 "cycleWire", "cycleMenu", "cycleMenuDraw", "minimapButton", "thMapButton", "cdGuide", "cdGuideDraw")
        twice = [n for n in names if len(re.findall(rf"\bfunction {n}\(", scripts)) != 1]
        gone = [n for n in ("thViewMenu", "thViewChange", "trajViewMenu", "trajViewDraw") if f"function {n}(" in scripts]
        check("423: each View, Guidance and cycling function is declared once across the page's scripts, the boards' "
              "and Trajectories' View gone", not twice and not gone, str(twice + gone))
        # every button of more than two states goes through the one cycling code path
        traj = support.text("apps/idiograph/static/trajectories.js")
        distil = support.text("apps/idiograph/static/distil.js")
        check("423: the Minimap on the statements screen and the boards, and Quotes on the boards and Trajectories, "
              "are wired through cycleWire",
              "cycleWire($('es-map-btn'), MINIMAP_CYCLE);" in distil and "cycleWire($('th-map-btn'), TH_MAP_CYCLE);" in js
              and "cycleWire($('th-quotes-btn'), TH_QUOTES_CYCLE);" in js
              and "cycleWire($('tj-quotes-btn'), TJ_QUOTES_CYCLE);" in traj, "")
        import shutil as _sh
        if not _sh.which("node"):
            support.skip("423: the Minimap's click and menu in node", "node is not installed")
        else:
            a = distil.index("const CYCLE_HOLD = 550;")
            block = distil[a:distil.index("// the minimap's three ways", a)]
            script = r"""
const handlers = {}; const docHandlers = [];
const el = (name) => ({ name, hidden: true, innerHTML: '', style: {}, dataset: {}, offsetWidth: 120, offsetHeight: 90,
  attrs: {}, on: {}, setAttribute(k, v) { this.attrs[k] = v; },
  addEventListener(type, fn) { (this.on[type] = this.on[type] || []).push(fn); },
  contains(x) { return x === this; }, getBoundingClientRect: () => ({ left: 300, top: 700, right: 330, bottom: 720 }) });
const document = { addEventListener: (type, fn) => docHandlers.push([type, fn]) };
const window = { innerWidth: 1280 };
const esc = (s) => String(s); const t = (k) => k;
""" + block + r"""
const btn = el('btn'); const menu = el('menu'); const bar = el('bar');
let mode = 'auto'; const sets = [];
const o = { menu, ways: ['auto', 'on', 'off'], now: () => mode, set: (m) => { sets.push(m); mode = m; },
  head: () => 'Minimap', row: (m) => m, bar: () => bar };
cycleWire(btn, o);
const clicks = [];
for (let i = 0; i < 3; i += 1) { btn.onclick(); clicks.push(mode); }
const ev = { preventDefault() {}, stopPropagation() {}, clientX: 310 };
btn.on.contextmenu[0](ev);
const opened = { hidden: menu.hidden, rows: (menu.innerHTML.match(/data-cway="/g) || []).length,
  ticked: /aria-checked="true"[^>]*data-cway="auto"/.test(menu.innerHTML) };
const chosen = [];
for (const m of ['off', 'on', 'auto']) {
  await menu.on.click[0]({ target: { closest: () => ({ dataset: { cway: m } }) } });
  chosen.push([mode, menu.hidden, new RegExp('aria-checked="true"[^>]*data-cway="' + m + '"').test(menu.innerHTML)]);
}
const esc2 = docHandlers.find(([type]) => type === 'keydown')[1];
esc2({ key: 'Escape', preventDefault() {}, stopPropagation() {} });
console.log(JSON.stringify({ clicks, opened, chosen, shut: menu.hidden }));
"""
            done = support.run_node("(async () => {" + script + "})();", scratch, "a423-cycle.js")
            got = json.loads(done.stdout.strip().splitlines()[-1]) if done.returncode == 0 and done.stdout.strip() else {}
            check("423: the Minimap's click takes Auto to On to Off and back to Auto",
                  got.get("clicks") == ["on", "off", "auto"], done.stderr[-300:] + done.stdout[-300:])
            check("423: a right click opens its menu of the three, the one in use ticked, and each row sets its state, "
                  "the menu staying open, Esc shutting it",
                  got.get("opened") == {"hidden": False, "rows": 3, "ticked": True}
                  and got.get("chosen") == [["off", False, True], ["on", False, True], ["auto", False, True]]
                  and got.get("shut") is True, json.dumps(got))
    finally:
        (agent_changes.ALL_OPS, place, server_mod.CONFIG_PATH, server_mod.STATE_PATH, server_mod.STATE_MEMORY) = kept
        if place is None:
            os.environ.pop(agent_log.PLACE, None)
        else:
            os.environ[agent_log.PLACE] = place
