"""Area 424: the kind of project, one value, and the project's page by it (projectbuild, Adam's rulings of 17 November
2026).

A project's `method` is "ipa", "lipa" (longitudinal IPA) or "ta" (reflexive thematic analysis), chosen on New project
and fixed after. A project from before with "ipa", or none, and two or more timepoints reads as "lipa" with nothing
written, since opening a project writes nothing. New project is two steps: the page's card makes the project alone,
with a longitudinal project's timepoints, and its page offers Add transcripts. Agents make one through the same route
(`project new --method lipa --timepoint`, MCP's project_new) and read the method beside a longitudinal project's
timepoints (`project show`, MCP's project_show). No client changes a method, and an IPA or a thematic analysis project
takes no timepoints, each refused in one line with nothing written, dry run and real. The project's page draws the work
across participants as a row of tiles on top, LGETs and Trajectories, GETs, or Code list and Themes, and a longitudinal
participant's box has LPETs after PETs, all from that one value.

What is checked, on scratch copies of the longitudinal and the reflexive thematic analysis demos made projects of their
own and on projects made here: an old project with timepoints reads lipa and reading it every way writes nothing; New
project's route with each method makes the right file, a lipa project's timepoints in it, no participant, and its dry
run writes nothing, nor do the command line's and MCP's; a method change and timepoints on an IPA or a thematic
analysis project are refused whole; a longitudinal project's timepoints set by an agent are one record line, undone
byte for byte, and kept at one timepoint; and the page's data and its own functions draw the top row and the tags by
the method. Every fixture is invented or a shipped demo."""
from __future__ import annotations

import base64
import hashlib
import json
import os
import shutil
from pathlib import Path

from . import support
from .support import check

TALK = ("Kit: [00:00:03] What did the plot look like the first time?\n"
        "Wren: [00:00:08] Brambles to my shoulders, and a shed with no door.\n"
        "Kit: [00:00:20] And now?\n"
        "Wren: [00:00:26] Beans. Too many beans.\n")


def files(root: Path) -> dict:
    """Every file under a project by its contents, the locks, the record of agents' changes and its store, the History
    and archive copies set aside."""
    import agent_changes
    out = {}
    for p in sorted(root.rglob("*")):
        rel = p.relative_to(root).as_posix()
        if (not p.is_file() or p.name.endswith(".lock") or rel == agent_changes.FILE or rel.startswith(agent_changes.STORE)
                or "_Archive/" in rel or rel in agent_changes.NEVER or rel.startswith(".history")):
            continue
        out[rel] = hashlib.sha256(p.read_bytes()).hexdigest()
    return out


def demo_copy(src: Path, root: Path, people: tuple) -> None:
    """A shipped demo copied as an ordinary project, as the server's start fills a demo."""
    import server as server_mod
    for who in people:
        (root / who / "Working").mkdir(parents=True)
        shutil.copy2(src / "pristine" / f"{who} - EN & ES.xlsx", root / who / f"{who} - EN & ES.xlsx")
        for one in sorted((src / "pristine" / "Working").glob(f"{who} - EN & ES.*")):
            shutil.copy2(one, root / who / "Working" / one.name)
    for one in (src / "pristine").glob("*.json"):
        shutil.copy2(one, root / one.name)
    held = json.loads((src / server_mod.PROJECT_FILE).read_text(encoding="utf-8"))
    held["agents"] = {"allowed": True, "at": "2026-11-17T09:00:00+00:00"}
    (root / server_mod.PROJECT_FILE).write_text(json.dumps(held), encoding="utf-8")


def test_project_kind(scratch: Path):
    print("\n424. The kind of project, one value, fixed at New project, and the project's page drawn by it (projectbuild)")
    import agent_changes
    import agent_log
    import cli
    import idiograph_routes as routes
    import mcp_server
    import server as server_mod
    from workbook import WorkbookError

    base = scratch / "kind-424"
    shutil.rmtree(base, ignore_errors=True)
    base.mkdir(parents=True)
    lipa = base / "Allotment study"
    rta = base / "Home working"
    demo_copy(support.source("demo/lipa"), lipa, ("Arlo", "Hollis", "Nell"))
    demo_copy(support.source("demo/rta"), rta, ("Dev", "Ffion", "Glen", "Kemi", "Ros", "Toby"))
    config_file = base / "config.json"

    def config(*roots):
        config_file.write_text(json.dumps({"projects": [{"root": str(r)} for r in roots], "interviewer": "Kit",
                                           "corpus": "", "gravity_reference": "", "corpus_exclude": []}), encoding="utf-8")

    config(lipa, rta)
    log = base / "agent-log.json"
    kept = (agent_changes.ALL_OPS, os.environ.get(agent_log.PLACE), server_mod.CONFIG_PATH, server_mod.ROOT_OVERRIDE,
            server_mod.STATE_PATH, server_mod.STATE_MEMORY)
    agent_changes.ALL_OPS = None
    os.environ[agent_log.PLACE] = str(log)
    server_mod.CONFIG_PATH, server_mod.ROOT_OVERRIDE = config_file, None
    server_mod.STATE_PATH, server_mod.STATE_MEMORY = base / "state.json", {"recent": []}

    def run(*args, root=None, tool="Claude Code"):
        given = ["--config", str(config_file), *(["--root", str(root)] if root else []), "--json", *args]
        if tool is not None:
            given += ["--tool", tool]
        code, out, err = cli.run(given)
        got = support.plain(json.loads(out)) if out.strip() else {}
        return code, got, err + (got.get("error", "") if code != 0 else "")

    def refused(fn, body) -> str:
        try:
            fn(body)
        except WorkbookError as exc:
            return str(exc)
        return ""

    def project_of(root):
        return json.loads((root / server_mod.PROJECT_FILE).read_text(encoding="utf-8"))

    def section(root):
        for s in routes.api_cases({})["projects"]:
            if s["id"] == routes.project_id(root):
                return s
        return {}

    try:
        # ── A. an old longitudinal project, IPA's with three timepoints and no method of its own, reads lipa, and
        # reading it every way writes nothing
        old = project_of(lipa)
        start = files(lipa)
        book = lipa / "Arlo" / "Arlo - EN & ES.xlsx"
        read = routes.read_project(lipa)
        page = section(lipa)
        routes.api_open({"path": str(book)})
        routes.api_project({"root": routes.project_id(lipa)})
        code, shown, err = run("project", "show", root=lipa, tool=None)
        code2, study, err2 = run("cases", root=lipa, tool=None)
        mcp = mcp_server.Server(root=str(lipa), config=str(config_file))
        res = mcp.call(mcp.by_name["project_show"], {})
        mshown = (res.get("structuredContent") or {}).get("project", {})
        check("424: a project from before, no method and three timepoints, reads lipa through the route, Home, project "
              "show, cases and MCP, its timepoints beside the method",
              "method" not in old and len(old.get("timepoints") or []) == 3 and read["method"] == "lipa"
              and page.get("project", {}).get("method") == "lipa" and code == 0 and shown["project"]["method"] == "lipa"
              and [t["label"] for t in shown["project"].get("timepoints") or []] == ["T1", "T2", "T3"]
              and code2 == 0 and study["project"]["method"] == "lipa" and mshown.get("method") == "lipa"
              and len(mshown.get("timepoints") or []) == 3, err + err2 + json.dumps(res)[:300])
        check("424: and opening, listing and reading it wrote nothing, its file still naming no method",
              files(lipa) == start and "method" not in project_of(lipa), "")

        # ── B. New project's route, each method, no transcripts: the right file, a lipa project's timepoints, no
        # participant, and its dry run nothing
        made = {}
        for method in ("ipa", "lipa", "ta"):
            folder = base / f"made-{method}"
            folder.mkdir()
            body = {"op": "make", "folder": str(folder), "name": f"A {method} project", "research_question": "How?",
                    "method": method, "files": [],
                    **({"timepoints": [{"label": "T1", "description": "Spring"}, {"label": "T2", "description": "Autumn"}]}
                       if method == "lipa" else {})}
            dry = routes.api_new_project(dict(body, dry_run=True))
            nothing = not list(folder.iterdir())
            got = routes.api_new_project(body)
            made[method] = (folder, got, dry, nothing)
        ipa_root, ta_root, lipa_root = made["ipa"][0], made["ta"][0], made["lipa"][0]
        check("424: New project's dry run names the method and a lipa project's timepoints and writes nothing",
              all(m[3] for m in made.values()) and made["lipa"][2]["method"] == "lipa"
              and [t["label"] for t in made["lipa"][2]["timepoints"]] == ["T1", "T2"] and made["ipa"][2]["method"] == "ipa"
              and "timepoints" not in made["ipa"][2], json.dumps(made["lipa"][2])[:300])
        check("424: each method's project file names it, a lipa project's its timepoints, an IPA and a thematic analysis "
              "project's none, and no project has a participant",
              project_of(ipa_root).get("method") == "ipa" and "timepoints" not in project_of(ipa_root)
              and project_of(ta_root).get("method") == "ta" and "timepoints" not in project_of(ta_root)
              and project_of(lipa_root).get("method") == "lipa"
              and project_of(lipa_root).get("timepoints") == [{"label": "T1", "description": "Spring"},
                                                               {"label": "T2", "description": "Autumn"}]
              and all(sorted(p.name for p in m[0].iterdir() if not p.name.endswith('.lock')) == [server_mod.PROJECT_FILE]
                      for m in made.values())
              and all(m[1]["cases"] == [] and m[1]["project"]["method"] == k for k, m in made.items()),
              json.dumps({k: project_of(m[0]) for k, m in made.items()})[:400])
        one = base / "made-lipa-one"
        one.mkdir()
        routes.api_new_project({"op": "make", "folder": str(one), "name": "One round", "method": "lipa", "files": []})
        check("424: a longitudinal project made with no timepoints given has T1 and T2 and reads lipa",
              project_of(one).get("timepoints") == [{"label": "T1", "description": ""}, {"label": "T2", "description": ""}]
              and routes.read_project(one)["method"] == "lipa"
              and routes.longitudinal(routes.read_project(one)["timepoints"]), json.dumps(project_of(one)))
        # one timepoint is refused for a new longitudinal project, a number of one too, with nothing written, dry run
        # and real (lipamin, Adam's ruling of 17 November)
        few = base / "made-few"
        few.mkdir()
        said_few = [refused(routes.api_new_project, {"op": "make", "folder": str(few), "name": "X", "method": "lipa",
                                                     "files": [], "timepoints": given, **extra})
                    for given in ([{"label": "T1"}], 1) for extra in ({}, {"dry_run": True})]
        code_few, _, err_few = run("project", "new", str(few), "--name", "X", "--method", "lipa", "--timepoint", "T1=Before")
        check("424: a new longitudinal project of one timepoint is refused in one line with nothing written, through the "
              "route, dry run and real, and the command line",
              all(said_few) and all("\n" not in x for x in said_few) and code_few != 0 and not list(few.iterdir()),
              " | ".join(said_few) + err_few)
        # a file from 0.9.30 made at one timepoint, written as it was then: it reads lipa, reading writes nothing
        held_one = project_of(one)
        held_one["timepoints"] = [{"label": "T1", "description": ""}]
        (one / server_mod.PROJECT_FILE).write_text(json.dumps(held_one), encoding="utf-8")
        start_one = files(one)
        read_one = routes.read_project(one)
        check("424: a longitudinal project from 0.9.30 with one timepoint still reads lipa and reading it writes nothing",
              read_one["method"] == "lipa" and routes.longitudinal(read_one["timepoints"]) and files(one) == start_one, "")
        bad = base / "made-bad"
        bad.mkdir()
        said = [refused(routes.api_new_project, {"op": "make", "folder": str(bad), "name": "X", "method": m, "files": [],
                                                 "timepoints": [{"label": "T1"}, {"label": "T2"}]}) for m in ("ipa", "ta")]
        said.append(refused(routes.api_new_project, {"op": "make", "folder": str(bad), "name": "X", "method": "grounded"}))
        check("424: New project refuses timepoints for IPA and thematic analysis and a method that is not one, in one "
              "line each, nothing written", all(said) and "IPA project has no timepoints" in said[0]
              and "ipa, lipa or ta" in said[2] and not list(bad.iterdir()), " | ".join(said))

        # the command line and MCP make one through the same route
        agent = base / "agent-lipa"
        agent.mkdir()
        code, dry, err = run("project", "new", str(agent), "--name", "Allotment", "--method", "lipa",
                             "--timepoint", "T1=Before", "--timepoint", "Later=A year on", "--dry-run")
        nothing = not list(agent.iterdir())
        code2, got, err2 = run("project", "new", str(agent), "--name", "Allotment", "--method", "lipa",
                               "--timepoint", "T1=Before", "--timepoint", "Later=A year on", "--note", "A longitudinal one")
        check("424: project new --method lipa --timepoint: the dry run names them and writes nothing, the real one makes "
              "the project with its timepoints and no participant",
              code == 0 and dry.get("method") == "lipa" and [t["label"] for t in dry.get("timepoints") or []] == ["T1", "Later"]
              and nothing and code2 == 0 and got["project"]["method"] == "lipa" and got["cases"] == []
              and project_of(agent).get("timepoints") == [{"label": "T1", "description": "Before"},
                                                            {"label": "Later", "description": "A year on"}],
              err + err2 + json.dumps(got)[:200])
        other = base / "mcp-lipa"
        other.mkdir()
        res = mcp.call(mcp.by_name["project_new"], {"folder": str(other), "method": "lipa", "dry_run": True,
                                                    "request": "Look first",
                                                    "timepoints": [{"label": "T1", "description": "Spring"},
                                                                   {"label": "T2", "description": "Autumn"}]})
        sc = support.plain(res.get("structuredContent") or {})
        res_one = mcp.call(mcp.by_name["project_new"], {"folder": str(other), "method": "lipa", "dry_run": True,
                                                        "request": "Look first", "timepoints": [{"label": "T1"}]})
        res_none = mcp.call(mcp.by_name["project_new"], {"folder": str(other), "method": "lipa", "dry_run": True,
                                                         "request": "Look first"})
        none_tps = support.plain(res_none.get("structuredContent") or {}).get("timepoints") or []
        check("424: MCP's project_new takes lipa and its timepoints with no transcripts, T1 and T2 when none are given, "
              "one refused, its dry run writing nothing",
              not res.get("isError") and sc.get("method") == "lipa"
              and [t["label"] for t in sc.get("timepoints") or []] == ["T1", "T2"] and not list(other.iterdir())
              and res_one.get("isError") and not res_none.get("isError") and [t["label"] for t in none_tps] == ["T1", "T2"],
              json.dumps([res, res_one])[:400])

        # ── C. no client changes a method, and IPA and thematic analysis projects take no timepoints: refused whole
        config(lipa, rta, ipa_root, ta_root, lipa_root, one)
        for root in (ipa_root, ta_root, lipa_root):
            routes.api_project({"root": routes.project_id(root), "agents": True})
        held = {r: files(r) for r in (ipa_root, ta_root, lipa_root, lipa)}
        said = []
        for root, body in ((ipa_root, {"timepoints": 2}), (ipa_root, {"timepoints": [{"label": "T1"}, {"label": "T2"}]}),
                           (ta_root, {"timepoints": 2}), (ipa_root, {"method": "lipa", "name": "Renamed"}),
                           (lipa_root, {"method": "ipa", "name": "Renamed"}), (lipa, {"method": "ta"}),
                           (ta_root, {"method": "ipa"})):
            for dry in (True, False):
                said.append(refused(routes.api_project, dict(body, root=routes.project_id(root), dry_run=dry)))
        (base / "tp.json").write_text(json.dumps([{"label": "T1"}, {"label": "T2"}]), encoding="utf-8")
        code, _, err = run("timepoints", "--from", str(base / "tp.json"), "--note", "Two", root=ipa_root)
        code2, _, err2 = run("project", "set", "--method", "lipa", "--note", "Make it longitudinal", root=ipa_root)
        code3, _, err3 = run("project", "set", "--method", "ipa", "--dry-run", root=lipa)
        mcp_ipa = mcp_server.Server(root=str(ipa_root), config=str(config_file))
        res = mcp_ipa.call(mcp_ipa.by_name["timepoints_set"], {"timepoints": [{"label": "T1"}, {"label": "T2"}],
                                                               "request": "Two"})
        check("424: a method change and timepoints on an IPA or a thematic analysis project are refused in one line, dry "
              "run and real, through the route, the command line and MCP, nothing written",
              all(said) and all("\n" not in s for s in said) and code != 0 and "no timepoints" in err
              and code2 != 0 and "chosen when it was made" in err2 and code3 != 0 and res.get("isError")
              and all(files(r) == held[r] for r in held) and not agent_changes.read(ipa_root),
              " | ".join(said) + err + err2 + err3)

        # the timepoints read on an IPA and on a thematic analysis project answers none, with its line, command line and
        # MCP alike, and on a longitudinal project of one timepoint it answers T1 as longitudinal
        read_said = []
        for root, name in ((ipa_root, "A ipa project"), (ta_root, "A ta project")):
            code, got, err = run("timepoints", root=root, tool=None)
            mcp_one = mcp_server.Server(root=str(root), config=str(config_file))
            res = mcp_one.call(mcp_one.by_name["timepoints"], {})
            sc = support.plain(res.get("structuredContent") or {})
            read_said.append((code, got, err, res, sc))
        routes.api_project({"root": routes.project_id(one), "agents": True})
        code, got, err = run("timepoints", root=one, tool=None)
        check("424: the timepoints read on an IPA and on a thematic analysis project answers [] and says it has none, "
              "through the command line and MCP alike, and on a longitudinal project of one answers T1",
              all(c == 0 and g.get("timepoints") == [] and g.get("longitudinal") is False and not r.get("isError")
                  and sc.get("timepoints") == [] for c, g, e, r, sc in read_said)
              and code == 0 and [t["label"] for t in got.get("timepoints") or []] == ["T1"] and got.get("longitudinal") is True
              and all(f"{m} projects have no timepoints" in json.dumps(r["content"])
                      for (c, g, e, r, sc), m in zip(read_said, ("Interpretative Phenomenological Analysis",
                                                                 "Reflexive thematic analysis"))),
              json.dumps([code, got, err] + [x[1:2] for x in read_said])[:700])

        # ── a longitudinal project's timepoints set by an agent: one record line, undone byte for byte, and kept at one
        tps = base / "tp3.json"
        tps.write_text(json.dumps([{"label": "T1", "description": "Spring"}, {"label": "T2", "description": "Autumn"},
                                   {"label": "T3", "description": "A year on"}]), encoding="utf-8")
        before = files(lipa_root)
        code, out, err = run("timepoints", "--from", str(tps), "--note", "A third round", root=lipa_root)
        lines = agent_changes.read(lipa_root)
        check("424: an agent's timepoints on a lipa project are saved, one record line",
              code == 0 and len(project_of(lipa_root)["timepoints"]) == 3 and len(lines) == 1, err + json.dumps(lines)[:300])
        if lines:
            code, _, err = run("agents", "undo-run", lines[0]["run"], "--note", "Put it back", root=lipa_root)
            check("424: undoing that run puts the project back byte for byte", code == 0 and files(lipa_root) == before, err)
        # lowering below two is refused whole, by the route, the command line and MCP, dry run and real
        held_two, lines_two = files(lipa_root), len(agent_changes.read(lipa_root))
        one_tp = base / "tp1.json"
        one_tp.write_text(json.dumps([{"label": "T1", "description": "Spring"}]), encoding="utf-8")
        low_said = [refused(routes.api_project, {"root": routes.project_id(lipa_root), "timepoints": n, **extra})
                    for n in (1, [{"label": "T1"}]) for extra in ({}, {"dry_run": True})]
        code_low, _, err_low = run("timepoints", "--from", str(one_tp), "--note", "One", root=lipa_root)
        code_low2, _, err_low2 = run("timepoints", "--from", str(one_tp), "--dry-run", root=lipa_root)
        mcp_low = mcp_server.Server(root=str(lipa_root), config=str(config_file))
        res_low = mcp_low.call(mcp_low.by_name["timepoints_set"], {"timepoints": [{"label": "T1"}], "request": "One"})
        check("424: lowering a longitudinal project below two timepoints is refused in one line with nothing written, "
              "through the route, the command line and MCP",
              all(low_said) and all("\n" not in x for x in low_said) and code_low != 0 and code_low2 != 0
              and res_low.get("isError") and files(lipa_root) == held_two and len(agent_changes.read(lipa_root)) == lines_two,
              " | ".join(low_said) + err_low + err_low2 + json.dumps(res_low)[:200])
        # a one-timepoint project from 0.9.30 may keep its one and raise it, never lower
        raised = routes.api_project({"root": routes.project_id(one), "timepoints": 2})
        check("424: a longitudinal project made at one timepoint before this can raise its count and stays longitudinal",
              len(project_of(one)["timepoints"]) == 2 and raised["project"]["method"] == "lipa"
              and routes.longitudinal(raised["project"]["timepoints"]), json.dumps(project_of(one)))
        # the fixtures below are 0.9.30 projects of one timepoint, as a file from then was written
        for root, desc in ((lipa_root, "Spring"), (one, "")):
            held_one = project_of(root)
            held_one["timepoints"] = [{"label": "T1", "description": desc}]
            (root / server_mod.PROJECT_FILE).write_text(json.dumps(held_one), encoding="utf-8")
        # such a project can save its one timepoint, a relabel of T1, but none at all is refused as one is
        relabel = routes.api_project({"root": routes.project_id(one), "timepoints": [{"label": "Round", "description": "Once"}]})
        none_said = [refused(routes.api_project, {"root": routes.project_id(one), "timepoints": n}) for n in (0, [])]
        check("424: a one-timepoint longitudinal project can save its one timepoint, relabelled, and none at all is refused "
              "with the two it needs named",
              project_of(one)["timepoints"] == [{"label": "Round", "description": "Once"}]
              and relabel["project"]["method"] == "lipa" and all("from 2 to 10" in x for x in none_said), " | ".join(none_said))
        held_one = project_of(one)
        held_one["timepoints"] = [{"label": "T1", "description": ""}]
        (one / server_mod.PROJECT_FILE).write_text(json.dumps(held_one), encoding="utf-8")

        # ── D. the page's data: the row across participants and each participant's box follow the method
        talk = base / "Wren interview.txt"
        talk.write_text(TALK, encoding="utf-8")
        data = base64.b64encode(talk.read_bytes()).decode("ascii")
        for root in (lipa_root, ipa_root):
            read = routes.api_new_project({"op": "read", "name": talk.name, "data": data})
            routes.api_add_transcripts({"op": "add", "root": routes.project_id(root), "names_reviewed": True, "files": [
                {"name": talk.name, "data": data, "pseudonym": "Wren", "interview": read["interview"],
                 "speakers": read["speaker_roles"]}]})
        s_lipa, s_old, s_ipa, s_ta = section(lipa_root), section(lipa), section(ipa_root), section(rta)
        wren = (s_lipa.get("participants") or [{}])[0]
        wren_ipa = (s_ipa.get("participants") or [{}])[0]
        arlo = next((p for p in s_old.get("participants") or [] if p["case"] == "Arlo"), {})
        check("424: a longitudinal project's row is LGETs with Trajectories beside them, an IPA project's GETs, a "
              "thematic analysis project's Themes with its code list beside them",
              (s_old.get("gets") or {}).get("method") == "lipa" and (s_old["gets"].get("lgets") is True)
              and s_old["gets"].get("trajectories") == {"trajectories": 3, "participants": 3, "placed": 3}
              and (s_ipa.get("gets") or {}).get("method") == "ipa" and "trajectories" not in s_ipa["gets"]
              and not s_ipa["gets"].get("lgets") and (s_ta.get("gets") or {}).get("method") == "ta"
              and s_ta["gets"].get("codes", {}).get("codes", 0) > 0 and "trajectories" not in s_ta["gets"],
              json.dumps({k: (v.get("gets") or {}) for k, v in (("old", s_old), ("ipa", s_ipa), ("ta", s_ta))})[:600])
        check("424: each participant of a longitudinal project, at one timepoint too, has their timepoints and their "
              "LPETs on their row, and an IPA project's participant neither",
              len(wren.get("timepoints") or []) == 1 and isinstance(wren.get("lpets"), dict)
              and wren["lpets"].get("boards") == 0 and arlo.get("lpets", {}).get("boards", 0) >= 1
              and arlo["lpets"].get("board") and "timepoints" not in wren_ipa and "lpets" not in wren_ipa
              and (s_lipa.get("gets") or {}).get("lgets") is True, json.dumps([wren, arlo.get("lpets")])[:500])

        # ── E. a shared copy of a longitudinal project of one timepoint coming back: its rows carry T1's label
        import project_pack
        import themes
        import workbook as wb_mod
        one_root = one
        agent_changes.ALL_OPS = True  # the suite stands in for the app, whose Share a copy is no agent's
        routes.api_project({"root": routes.project_id(one_root), "agents": True})
        story = base / "Wren story.txt"
        story.write_text(TALK, encoding="utf-8")
        read = routes.api_new_project({"op": "read", "name": story.name, "data": data})
        routes.api_add_transcripts({"op": "add", "root": routes.project_id(one_root), "names_reviewed": True, "files": [
            {"name": story.name, "data": data, "pseudonym": "Wren", "interview": "Before", "speakers": read["speaker_roles"]}]})
        book_one = next(one_root.glob("*Wren*/*.xlsx"))
        import openpyxl
        wb = openpyxl.load_workbook(book_one, read_only=True)
        sheet = "Before" if "Before" in wb.sheetnames else wb.sheetnames[0]
        wren_rows = [r for r, v in enumerate(wb[sheet].iter_rows(min_row=2, max_col=1, values_only=True), start=2)
                     if str(v[0] or "").strip() == "Wren"]
        wb.close()
        wb_mod.save_turn(book_one, sheet, wren_rows[0], "Brambles and a shed with no door", "", "")
        wb_mod.save_turn(book_one, sheet, wren_rows[1], "Too many beans", "", "")
        plan = base / "one-plan.json"
        plan.write_text(json.dumps({"pets": [{"title": "All of it", "members": ["S1", "S2"]}]}), encoding="utf-8")
        curt = base / "one-curt.json"
        curt.write_text(json.dumps({"projects": [], "interviewer": "Kit", "your_name": "Curt", "corpus": "",
                                    "gravity_reference": "", "corpus_exclude": []}), encoding="utf-8")
        sent, back, into = base / "one.idiograph", base / "one-back.idiograph", base / "one-into"
        into.mkdir()
        cfg = str(config_file)
        steps = [cli.run(["--config", cfg, "--root", str(one_root), "board", "new", "Wren", "--from", str(plan),
                          "--note", "Mine", "--tool", "Claude Code"]),
                 cli.run(["--config", cfg, "--root", str(one_root), "project", "send", "--to", str(sent)]),
                 cli.run(["--config", str(curt), "project", "open-copy", str(sent), "--into", str(into)])]
        copy = next(into.iterdir(), None)
        if copy is not None:
            steps += [cli.run(["--config", str(curt), "--root", str(copy), "board", "new", "Wren", "--from", str(plan),
                               "--note", "Curt's", "--tool", "Claude Code"]),
                      cli.run(["--config", str(curt), "--root", str(copy), "project", "send", "--to", str(back)])]
        dry_back = routes.boards_in(one_root, back, from_name="Curt", dry_run=True) if back.exists() else {}
        rows = dry_back.get("participants") or []
        check("424: a longitudinal project of one timepoint, its copy sent and coming back, has rows that carry T1's label",
              all(c == 0 for c, _, _ in steps) and rows and all(r["timepoint_label"] == "T1" for r in rows),
              " ".join(e for _, _, e in steps)[:400] + json.dumps(rows)[:300])

        # and the page's own functions draw the tiles, the tags and the LPETs line from that data
        app = support.text("family/static/shell.js", "apps/idiograph/static/distil.js")
        fn = lambda name: ("function " + name + "(" + app.split(f"function {name}(", 1)[1].split("\n}", 1)[0] + "\n}")
        script = support.i18n_js("idiograph") + r"""
const esc = (s) => String(s); const escAttr = esc;
""" + "\n".join(fn(n) for n in ("projKind", "kindTag", "getsLine", "drawGetsCard", "trajTileLine", "codesTileLine",
                                "lpetsLine")) + r"""
const box = () => ({ html: '', set innerHTML(v) { this.html = v; }, get innerHTML() { return this.html; }, hidden: true,
  style: { setProperty(k, v) { this[k] = v; } } });
const tiles = (gets, method) => { const b = box(); tIn(method, () => drawGetsCard(b, gets)); return [...b.html.matchAll(/data-act="(\w+)"[^>]*><span class="pc-name">([^<]*)<\/span><span class="pc-line">([^<]*)</g)].map((m) => [m[1], m[2], m[3]]); };
const SL = JSON.parse(process.argv[2]);
console.log(JSON.stringify({
  lipa: tiles(SL.lipa, 'lipa'), ipa: tiles(SL.ipa, 'ipa'), ta: tiles(SL.ta, 'ta'),
  kinds: [projKind(SL.p_old), projKind(SL.p_ipa), projKind(SL.p_ta), projKind(SL.p_one), projKind(null)],
  tags: [kindTag('ipa'), kindTag('lipa'), kindTag('ta')],
  lpets: [lpetsLine(SL.arlo), lpetsLine({ boards: 0, board: null, complete: null }), lpetsLine(null)],
}));
"""
        given = {"lipa": s_old["gets"], "ipa": s_ipa["gets"], "ta": s_ta["gets"], "p_old": {"timepoints": old["timepoints"]},
                 "p_ipa": s_ipa["project"], "p_ta": s_ta["project"], "p_one": s_lipa["project"], "arlo": arlo.get("lpets")}
        path = base / "kind-424.js"
        path.write_text(script, encoding="utf-8")
        import subprocess
        ran = subprocess.run(["node", str(path), json.dumps(given)], capture_output=True, text=True, encoding="utf-8", timeout=60)
        try:
            o = json.loads(ran.stdout.strip().splitlines()[-1])
        except (ValueError, IndexError):
            o = {}
        check("424: in the page's scripts the row is two tiles for lipa (LGETs, Trajectories with its count), one for "
              "IPA (GETs) and two for RTA (Code list with its count, Themes)",
              [t[0] for t in o.get("lipa", [])] == ["gets", "trajectories"] and o["lipa"][0][1] == "LGETs"
              and o["lipa"][1][2] == "3 trajectories · 3 of 3 participants placed"
              and [t[:2] for t in o.get("ipa", [])] == [["gets", "GETs"]]
              and [t[:2] for t in o.get("ta", [])] == [["codes", "Code list"], ["gets", "Themes"]]
              and o["ta"][0][2].endswith("codes"), (ran.stdout + ran.stderr)[-600:])
        check("424: and the kind and its tag come from the one value: an old project with timepoints LIPA, IPA, RTA, a "
              "longitudinal project of one LIPA, the LPETs line as PETs' reads",
              o.get("kinds") == ["lipa", "ipa", "ta", "lipa", "ipa"] and o.get("tags") == ["IPA", "LIPA", "RTA"]
              and o.get("lpets", [""])[0].startswith("Board 1") and "LPETs complete" in o["lpets"][0]
              and o["lpets"][1:] == ["No LPETs yet", "No LPETs yet"], (ran.stdout + ran.stderr)[-600:])
    except WorkbookError as exc:
        check("424: the routes run", False, str(exc))
    finally:
        agent_changes.ALL_OPS = kept[0]
        if kept[1] is None:
            os.environ.pop(agent_log.PLACE, None)
        else:
            os.environ[agent_log.PLACE] = kept[1]
        (server_mod.CONFIG_PATH, server_mod.ROOT_OVERRIDE, server_mod.STATE_PATH, server_mod.STATE_MEMORY) = kept[2:]
