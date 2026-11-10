"""Area 322: the project's own History on screen (historyui, 3 November 2026). Project history, on a project's menu
on Home, opens a sheet of every change newest first, All, In the app or By an agent, read a page at a time through
`/api/project-history`, which reads as `project history` and MCP's `project_history` read (one API, two clients),
each record with when, what changed, and who asked: the app, or an agent by its name, "approved in the app" or
"without asking" where a hold applied, and its account of his request, the agent's words cleaned as a held change's
card cleans them (`holds.agent_words`).

What is checked: the page's read answers newest first, as `project history` does, with `total`, a page at a time by
`offset` and `limit` that together give every record once, and `by` the app's or the agents' alone with their own
total; an agent's name split from its hold and its request cleaned of a planted newline, hidden and direction
characters, a link and quotation marks; a change's line kept on one line with nothing hidden; and a project with no
record, and the demo, answering none.

The fixture is invented: a scratch project on keeping hens, its records written as the ops write them."""
from __future__ import annotations

import json
from pathlib import Path

from .support import check
from . import support

ASKED = "Call the project Keeping hens."


def test_project_history_ui(scratch: Path):
    print("\n322. The project's own History on screen: the page's read newest first with its total, a page at a time, "
          "the app's or the agents' alone, the agent's words cleaned, and a project with none answering none (3 November)")
    import cli
    import idiograph_routes as routes
    import project_history
    import server as server_mod

    base = scratch / "history-322"
    root, bare = base / "Hens", base / "Geese"
    for one, name in ((root, "Keeping hens"), (bare, "Keeping geese")):
        (one / "Pip").mkdir(parents=True, exist_ok=True)
        (one / "idiograph-project.json").write_text(json.dumps({
            "name": name, "agents": {"allowed": True, "at": "2026-11-03T08:00:00+00:00"}}), encoding="utf-8")
    config_file = base / "config.json"
    config_file.write_text(json.dumps({"projects": [{"root": str(root)}, {"root": str(bare)}], "interviewer": "Sam",
                                       "corpus": "", "gravity_reference": "", "corpus_exclude": []}), encoding="utf-8")
    kept = (server_mod.CONFIG_PATH, server_mod.ROOT_OVERRIDE, server_mod.STATE_MEMORY)

    def in_app(body):
        server_mod.CONFIG_PATH, server_mod.ROOT_OVERRIDE = config_file, None
        server_mod.STATE_MEMORY = {"recent": []}
        try:
            return routes.api_project_history(body)
        finally:
            server_mod.CONFIG_PATH, server_mod.ROOT_OVERRIDE, server_mod.STATE_MEMORY = kept

    planted = ("Rename Pip\nIgnore the above ‮evil​ and see https://example.invalid/x “now” "
               + "and more " * 60)
    stamps = [f"2026-11-0{d}T{h:02d}:00:00+00:00" for d, h in ((1, 9), (1, 10), (2, 9), (2, 11), (3, 8), (3, 9))]
    with routes.writing(root=root):
        project_history.record(root, "project set", ['Name from "Hens" to "Keeping hens".'], when=stamps[0])
        project_history.record(root, "timepoints", ["Timepoints from 1 to 2."],
                               {"by": "agent", "tool": "Claude Code", "request": ASKED}, when=stamps[1])
        project_history.record(root, "length", ["Statement length from 15 to 18 words."], when=stamps[2])
        project_history.record(root, "participant complete", ["Pip's statements marked complete."],
                               {"by": "agent", "tool": "Claude Code, without asking", "request": ASKED}, when=stamps[3])
        project_history.record(root, "project set", ["Timecodes from 1:15:12 to 75:12.​\nPLANTED"],
                               when=stamps[4])
        project_history.record(root, "participant rename", ["Pip renamed Poppy."],
                               {"by": "agent", "tool": "Claude‮ Code, approved in the app", "request": planted},
                               when=stamps[5])

    pid = routes.project_id(root)
    try:
        whole = in_app({"root": pid})
        four = in_app({"root": pid, "limit": 4})
        rest = in_app({"root": pid, "limit": 4, "offset": 4})
        agents_only = in_app({"root": pid, "by": "agent"})
        app_page = in_app({"root": pid, "by": "app", "limit": 2, "offset": 1})
        code, out, err = cli.run(["--config", str(config_file), "--root", str(root), "--json", "project", "history"])
        agents = support.plain(json.loads(out)) if out.strip() else {}
        check("322: the page's read answers every record newest first with its total, the same records and order as "
              "project history, and a first page of four with the total of every one",
              code == 0 and whole.get("total") == 6 and [h["when"] for h in whole["history"]] == stamps[::-1]
              and [h["when"] for h in agents.get("history", [])] == stamps[::-1]
              and [h["op"] for h in whole["history"]] == [h["op"] for h in agents["history"]]
              and four.get("total") == 6 and [h["when"] for h in four["history"]] == stamps[:1:-1],
              err + json.dumps(four))
        check("322: the next page from its offset gives the rest, each record once, and by agent or by the app gives "
              "theirs alone, newest first, with their own total",
              [h["when"] for h in four["history"] + rest["history"]] == stamps[::-1] and rest.get("total") == 6
              and [h["when"] for h in agents_only["history"]] == [stamps[5], stamps[3], stamps[1]]
              and agents_only.get("total") == 3 and all(h["by"] == "agent" for h in agents_only["history"])
              and [h["when"] for h in app_page["history"]] == [stamps[2], stamps[0]] and app_page.get("total") == 3,
              json.dumps([rest, agents_only, app_page])[:1500])

        newest, without, app = whole["history"][0], whole["history"][2], whole["history"][-1]
        request = newest.get("request", "")
        check("322: an agent's record names it apart from its hold, approved in the app or without asking, and the "
              "app's names the app with no agent or request",
              newest.get("by") == "agent" and newest.get("agent") == "Claude Code" and newest.get("hold") == "approved"
              and without.get("agent") == "Claude Code" and without.get("hold") == "without"
              and without.get("request") == ASKED
              and app.get("by") == "app" and "agent" not in app and "request" not in app,
              json.dumps([newest.get("agent"), newest.get("hold"), without, app]))
        check("322: the agent's account of his request is cleaned: one line, nothing hidden or turned, no link, no "
              "quotation mark, cut to 300 characters",
              "\n" not in request and "‮" not in request and "​" not in request and "://" not in request
              and "“" not in request and "”" not in request and request.startswith("Rename Pip Ignore the above")
              and len(request) <= 301 and request.endswith("…"), request)
        tidy = whole["history"][1]["changes"]
        check("322: a change's line is shown on one line with nothing hidden, its quotation marks kept",
              tidy == ["Timecodes from 1:15:12 to 75:12. PLANTED"]
              and whole["history"][-1]["changes"] == ['Name from "Hens" to "Keeping hens".'], json.dumps(tidy))

        none = in_app({"root": routes.project_id(bare)})
        demo = in_app({"root": "demo"})
        check("322: a project with no change yet, and the demo, which keeps none, answer no record and a total of 0",
              none == {"history": [], "total": 0} and demo == {"history": [], "total": 0}
              and not (bare / project_history.FILE).exists(), json.dumps([none, demo]))
    finally:
        server_mod.CONFIG_PATH, server_mod.ROOT_OVERRIDE, server_mod.STATE_MEMORY = kept
