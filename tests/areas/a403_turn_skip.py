"""Area 403: passages decided with no statement, for an agent, as Skip decides one in the app (leaveout, 16 November
2026, the gap the GRAVITY session met: an agent could decide a passage only by writing a note).

What is checked, on a scratch copy of the demo made a project, with Juno's last passages made undecided (their
statements and quotes taken out of the scratch workbook and their rows' states out of its progress file): the dry run
of `turn skip` counts the passages it would mark, by participant and timepoint, and writes nothing, no record, no
restore point, no lock. A mark that would make a passage it does not name count as passed is refused whole, its dry run
too, naming those rows. A passage with statements, the interviewer's turn and a span taking in a passage with
statements are each refused in one line, nothing written. The op marks the
passage as the page's own Skip (`/api/commit` with no field) marks it on a twin: the same progress file rows and the
same counts everywhere they are read, the passages decided, the rounds, Home's line and the case summary, the
workbook untouched. The reason lands in the change's line of the record of agents' changes alone, never in the notes
column nor the progress file. The change's undo puts the progress file back byte for byte and the passage is
undecided again. MCP's turn_skip runs the same op."""
from __future__ import annotations

import hashlib
import json
import shutil
from pathlib import Path

import openpyxl

from .support import check
from . import support

ASKED = "Mark the small talk at the end as needing no statement"
REASON = "Small talk about the weather, nothing of her experience"
ROWS_OUT = (73, 75, 79)


def digest(root: Path) -> dict:
    """Every file of the project by its contents, the lock files set aside."""
    return {p.relative_to(root).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in sorted(root.rglob("*")) if p.is_file() and not p.name.endswith(".lock")}


def make(root: Path) -> Path:
    """The demo's three participants as a project at `root`, Juno's last passages made undecided: her rows 73, 75 and
    79 lose their statements and quotes in the workbook, and her progress file every row's state from 71 on and its
    place, so 71 to 79 are passages with no statement nobody has decided. Answers Juno's workbook."""
    import server as server_mod
    import workbook as wb_mod
    root.mkdir(parents=True)
    (root / server_mod.PROJECT_FILE).write_text(json.dumps({
        "name": "Dogs at home", "research_question": support.DEMO_QUESTION,
        "agents": {"allowed": True, "at": "2026-11-16T09:00:00+00:00"}}), encoding="utf-8")
    shipped = support.DEMO_SHIPPED
    for book in sorted(shipped.glob("*.xlsx")):
        who = book.name.split(" - ")[0]
        (root / who / "Working").mkdir(parents=True)
        shutil.copy2(book, root / who / book.name)
        for side in sorted((shipped / "Working").glob(f"{book.stem}.*")):
            shutil.copy2(side, root / who / "Working" / side.name)
    juno = root / "Juno" / "Juno - EN & ES.xlsx"
    wb = openpyxl.load_workbook(juno, rich_text=True)
    ws, cols = next(wb_mod._transcript_sheets(wb))
    for r in ROWS_OUT:
        ws.cell(r, cols["es"]).value = None
        ws.cell(r, cols["kq"]).value = None
    wb.save(juno)
    wb.close()
    side = root / "Juno" / "Working" / "Juno - EN & ES.progress.json"
    data = json.loads(side.read_text(encoding="utf-8"))
    data["rows"] = {k: v for k, v in (data.get("rows") or {}).items() if int(k.rpartition(":")[2]) < 71}
    data["last"] = None
    side.write_text(json.dumps(data, indent=1, ensure_ascii=False), encoding="utf-8")
    return juno


def test_turn_skip(scratch: Path):
    print("\n403. Passages decided with no statement for an agent, as Skip decides one: the dry run's counts and "
          "nothing written, the refusals, the same state and counts as the app's own Skip, the reason in the record "
          "alone, the change's undo, and MCP (leaveout, 16 November)")
    import agent_changes
    import agent_log
    import cli
    import i18n
    import idiograph_routes as routes
    import mcp_server
    import os
    import rounds as rounds_mod
    import server as server_mod
    import workbook as wb_mod

    base = scratch / "turn-skip-403"
    shutil.rmtree(base, ignore_errors=True)
    root = base / "Dogs at home"
    juno = make(root)
    # the twin the page's own Skip is made on, outside every project the command line reads
    twin_root = base / "twin" / "Dogs at home"
    twin = make(twin_root)
    config_file = base / "config.json"
    config_file.write_text(json.dumps({"projects": [{"root": str(root)}], "interviewer": "Adam",
                                       "corpus": "", "gravity_reference": "", "corpus_exclude": []}), encoding="utf-8")
    log = base / "agent-log.json"
    kept = (agent_changes.ALL_OPS, os.environ.get(agent_log.PLACE))
    agent_changes.ALL_OPS = None
    os.environ[agent_log.PLACE] = str(log)
    side = rounds_mod.progress_path(juno)

    def run(*args, tool="Claude Code"):
        given = ["--config", str(config_file), "--root", str(root), "--json", *args]
        if tool is not None:
            given += ["--tool", tool]
        code, out, err = cli.run(given)
        return code, (support.plain(json.loads(out)) if out.strip() else {}), err + (out if code else "")

    def page(route, body, at=twin_root):
        held = (server_mod.ROOT_OVERRIDE, server_mod.CONFIG_PATH, server_mod.STATE_MEMORY)
        server_mod.ROOT_OVERRIDE, server_mod.CONFIG_PATH, server_mod.STATE_MEMORY = str(at), config_file, {"recent": []}
        try:
            return route(body)
        finally:
            server_mod.ROOT_OVERRIDE, server_mod.CONFIG_PATH, server_mod.STATE_MEMORY = held

    def refusal(err: str) -> list:
        """A refusal's lines, as the command line's JSON gives them."""
        try:
            return json.loads(err[err.index("{"):]).get("lines") or []
        except ValueError:
            return [err]

    def states(book: Path) -> dict:
        return page(lambda _b: routes.refresh_summary(book), {}, at=book.parent.parent)["states"]

    def notes(book: Path) -> dict:
        wb = openpyxl.load_workbook(book, rich_text=True)
        try:
            ws, cols = next(wb_mod._transcript_sheets(wb))
            return {r: wb_mod.plain_text(ws.cell(r, cols["en"]).value) for r in range(2, ws.max_row + 1)}
        finally:
            wb.close()

    try:
        start, before_states = digest(root), states(juno)
        check("403: the scratch copy has Juno's passages 71 to 79 undecided with no statement, and 69 holds statements",
              all(before_states.get(f"Initial:{r}") == rounds_mod.UNVISITED for r in (71, 73, 75, 77, 79))
              and before_states.get("Initial:69") == rounds_mod.HAS_CONTENT, json.dumps(before_states)[-400:])

        # ── 1. a mark that would pass passages not named is refused, its dry run too, naming them
        for extra in ((), ("--dry-run",)):
            code, _x, err = run("turn", "skip", "Juno", "Initial", "75", *extra, *(() if extra else ("--note", ASKED)))
            check(f"403: marking 75 alone{' (dry run)' if extra else ''} would pass 71 and 73, not named, so it is "
                  "refused whole in one line naming them, nothing written",
                  code != 0 and len(refusal(err)) == 1 and "Rows 71 and 73 of Initial" in refusal(err)[0]
                  and "count them as passed" in refusal(err)[0] and digest(root) == start, err[:300])

        # ── 2. the dry run: the passages it would mark, the counts, nothing written
        code, dry, err = run("turn", "skip", "Juno", "Initial", "71-75", "--dry-run", tool=None)
        check("403: the dry run of 71-75 marks 71, 73 and 75, the participant's alone, and says the passages decided "
              "before and after, by participant and timepoint, rows alone",
              code == 0 and dry.get("dry_run") is True and dry.get("marked") == [71, 73, 75]
              and dry.get("case") == "Juno" and dry.get("timepoint", {}).get("label") == "T1"
              and dry["decided"]["after"] == dry["decided"]["before"] + 3 and dry["decided"]["total"] == len(before_states),
              err + json.dumps(dry)[:500])
        check("403: the dry run writes nothing: no record, no restore point, no lock",
              digest(root) == start and not (root / agent_changes.FILE).exists()
              and not (root / agent_changes.STORE).exists(), str(sorted(set(digest(root)) ^ set(start))))

        # ── 3. refusals, each one line, nothing written
        code, _x, err = run("turn", "skip", "Juno", "Initial", "69", "--note", ASKED)
        check("403: a passage with statements is refused in one line, nothing written",
              code != 0 and len(refusal(err)) == 1 and "holds statements" in refusal(err)[0] and digest(root) == start,
              err[:300])
        code, _x, err = run("turn", "skip", "Juno", "Initial", "65-75", "--note", ASKED)
        check("403: a span taking in passages with statements is refused whole, naming them, nothing written",
              code != 0 and "65, 67 and 69" in err and digest(root) == start, err[:300])
        code, _x, err = run("turn", "skip", "Juno", "Initial", "74", "--note", ASKED)
        check("403: the interviewer's turn is refused, never a passage to decide, nothing written",
              code != 0 and "interviewer's" in err and digest(root) == start, err[:300])
        code, _x, err = run("turn", "skip", "Juno", "Initial", "75")
        check("403: a write with no request is refused, nothing written", code != 0 and digest(root) == start, err[:300])

        # ── 4. the op, and the app's own Skip on the twin, passage by passage
        code, done, err = run("turn", "skip", "Juno", "Initial", "71-75", "--note", ASKED, "--reason", REASON)
        for r in (71, 73, 75):
            page(routes.api_commit, {"path": str(twin), "sheet": "Initial", "row": r, "round": None})
        mine, theirs = json.loads(side.read_text(encoding="utf-8")), json.loads(
            rounds_mod.progress_path(twin).read_text(encoding="utf-8"))
        check("403: the op marks rows 71, 73 and 75 decided with no statement, the state the app's Skip writes, and "
              "every other row's state as it was",
              code == 0 and done.get("marked") == [71, 73, 75]
              and all(mine["rows"].get(f"Initial:{r}") == rounds_mod.REVIEWED_EMPTY for r in (71, 73, 75))
              and mine["rows"] == theirs["rows"], err + json.dumps(done)[:300])
        after_mine, after_theirs = states(juno), states(twin)
        summary = lambda book: page(lambda _b: routes.refresh_summary(book), {}, at=book.parent.parent)
        s_mine, s_theirs = summary(juno), summary(twin)
        same = ("turnsDone", "turnsTotal", "roundsDone", "roundTurns", "sheetRounds", "complete")
        home_mine = page(lambda _b: routes.turns_of(juno, "Adam"), {}, at=root)
        home_theirs = page(lambda _b: routes.turns_of(twin, "Adam"), {}, at=twin_root)
        check("403: it counts as decided everywhere the app counts, as the app's own Skip does: every passage's state, "
              "the passages decided, the rounds and Home's line, 77 still undecided",
              after_mine == after_theirs and all(s_mine[k] == s_theirs[k] for k in same) and home_mine == home_theirs
              and home_mine["done"] == s_mine["turnsDone"]
              and after_mine["Initial:77"] == rounds_mod.UNVISITED,
              json.dumps({k: (s_mine[k], s_theirs[k]) for k in ("turnsDone", "roundsDone")}))
        check("403: the workbook is untouched, and so is every board and every other participant's file",
              all(digest(root)[k] == v for k, v in start.items() if not k.endswith("Juno - EN & ES.progress.json")),
              str([k for k, v in start.items() if digest(root).get(k) != v]))
        lines = agent_changes.read(root)
        check("403: the op is one line in the record of agents' changes, its request and its reason there, the "
              "passage named by sheet and row",
              len(lines) == 1 and lines[0]["op"] == "turn skip" and lines[0]["request"] == ASKED
              and lines[0].get("reason") == REASON and lines[0]["target"].get("rows") == "71-75"
              and lines[0]["target"].get("case") == "Juno", json.dumps(lines)[:500])
        import argparse
        import idiograph_cli
        shown = page(lambda _b: agent_changes.review(idiograph_cli.Project(root, False)), {}, at=root)
        change = next((c for r in shown.get("runs") or [] for c in r.get("changes") or [] if c.get("id") == lines[0]["id"]), {})
        check("403: Project history's By an agent gives the change its reason, cleaned as the agent's request is",
              change.get("reason") == REASON, json.dumps(change)[:300])
        other = argparse.Namespace(command="team", act="suggest", note=ASKED, reason="Another op's reason")
        kept_line = agent_changes.entry_for(idiograph_cli.Project(root, False), other, {"id": "r9"}, {}, [], [])
        check("403: another op's reason is never kept in the record, turn skip's alone", "reason" not in kept_line,
              json.dumps(kept_line)[:300])
        check("403: the reason never lands in the notes column nor the progress file",
              notes(juno) == notes(twin) and REASON not in side.read_text(encoding="utf-8")
              and not any(REASON in str(v) for v in notes(juno).values()), "")
        edits = [e for e in mine.get("edits") or [] if e.get("skipped")]
        check("403: the progress file keeps each passage under edits as the agent's, so an open statements screen sees it",
              [e["row"] for e in edits] == [71, 73, 75] and edits[0].get("by") == "agent"
              and edits[0].get("request") == ASKED, json.dumps(edits))
        code, again, err = run("turn", "skip", "Juno", "Initial", "75", "--note", ASKED)
        check("403: a passage already decided with no statement is marked again by nothing, no second line",
              code == 0 and again.get("marked") == [] and again.get("already") == [75] and len(agent_changes.read(root)) == 1,
              err + json.dumps(again)[:300])

        # ── 5. the change's undo puts it back
        code, undone, err = run("agents", "undo-change", lines[0]["id"], "--note", "Put the passage back")
        check("403: the change's undo puts the progress file back byte for byte, and 71 to 75 are undecided again",
              code == 0 and digest(root).get("Juno/Working/Juno - EN & ES.progress.json")
              == start["Juno/Working/Juno - EN & ES.progress.json"]
              and all(states(juno).get(f"Initial:{r}") == rounds_mod.UNVISITED for r in (71, 73, 75)), err + json.dumps(undone)[:300])

        # ── 6. in a project of timepoints the dry run names the timepoint its sheet is at
        lroot = base / "Allotment"
        (lroot / "Arlo" / "Working").mkdir(parents=True)
        lipa = support.source("demo/lipa")
        shutil.copy2(lipa / server_mod.PROJECT_FILE, lroot / server_mod.PROJECT_FILE)
        held = json.loads((lroot / server_mod.PROJECT_FILE).read_text(encoding="utf-8"))
        held["agents"] = {"allowed": True, "at": "2026-11-16T09:00:00+00:00"}
        (lroot / server_mod.PROJECT_FILE).write_text(json.dumps(held), encoding="utf-8")
        shutil.copy2(lipa / "pristine" / "Arlo - EN & ES.xlsx", lroot / "Arlo" / "Arlo - EN & ES.xlsx")
        for one in sorted((lipa / "pristine" / "Working").glob("Arlo - EN & ES.*")):
            shutil.copy2(one, lroot / "Arlo" / "Working" / one.name)
        lstart = digest(lroot)
        code, ldry, err = cli.run(["--config", str(config_file), "--root", str(lroot), "--json",
                                   "turn", "skip", "Arlo", "T2", "9", "--dry-run"])
        ldry = support.plain(json.loads(ldry)) if code == 0 and ldry.strip() else {}
        check("403: in a project of timepoints the dry run names the timepoint the sheet is at, T2, and writes nothing",
              code == 0 and ldry.get("timepoint") == {"n": 2, "label": "T2"} and ldry.get("case") == "Arlo"
              and 9 in (ldry.get("marked") or []) + (ldry.get("already") or []) and digest(lroot) == lstart,
              err + json.dumps(ldry)[:300])

        # ── 7. MCP's turn_skip runs the same op
        tools = {t["name"]: t for t in mcp_server.tools_for("idiograph")}
        t = tools.get("turn_skip")
        args = mcp_server.arguments(dict(t, command=("turn", "skip")) if t else {"command": ("turn", "skip")},
                                    {"case": "Juno", "sheet": "Initial", "rows": "71-79", "reason": REASON,
                                     "request": ASKED, "dry_run": True}, {"root": str(root)}, "Claude Desktop")
        check("403: MCP's turn_skip writes, takes the participant, sheet, rows, reason and dry_run, and maps to turn skip",
              t is not None and not t["annotations"]["readOnlyHint"] and t["command"] == ("turn", "skip")
              and {"case", "sheet", "rows", "reason", "dry_run", "request"} <= set(t["inputSchema"]["properties"])
              and args.rows == "71-79" and args.reason == REASON and args.case == "Juno", json.dumps(t)[:300] if t else "")

        # ── 8. a reason for passages decided with no statement already (skipreason, 16 November 2026): recorded in
        # one line with no file written, its dry run writing nothing, By an agent showing it, its undo allowed and
        # putting nothing back, a call mixing both kinds marking one and recording the reason for all
        def project_files() -> dict:
            return {k: v for k, v in digest(root).items()
                    if k != agent_changes.FILE and not k.startswith(agent_changes.STORE + "/")}

        def change_shown(cid: str) -> dict:
            shown = page(lambda _b: agent_changes.review(idiograph_cli.Project(root, False)), {}, at=root)
            return next((c for r in shown.get("runs") or [] for c in r.get("changes") or [] if c.get("id") == cid), {})

        code, first, err = run("turn", "skip", "Juno", "Initial", "71-73", "--note", ASKED)
        check("403: 71 and 73 marked decided with no statement, no reason given",
              code == 0 and first.get("marked") == [71, 73], err + json.dumps(first)[:300])
        held_record, held_files, held_all = agent_changes.read(root), project_files(), digest(root)
        code, dry, err = run("turn", "skip", "Juno", "Initial", "71-73", "--reason", REASON, "--dry-run")
        check("403: the dry run of a reason for passages decided already names them by row and writes nothing, not "
              "even the record's line",
              code == 0 and dry.get("marked") == [] and dry.get("already") == [71, 73]
              and dry.get("reason_rows") == {"marked": [], "already": [71, 73]}
              and digest(root) == held_all and agent_changes.read(root) == held_record, err + json.dumps(dry)[:300])
        # another agent, so the line starts a run of its own
        code, alone, err = run("turn", "skip", "Juno", "Initial", "71-73", "--note", ASKED, "--reason", REASON,
                               tool="Another agent")
        record = agent_changes.read(root)
        line = record[-1] if record else {}
        own = agent_changes.load_run(root, line.get("run", "")) or {}
        check("403: a reason for passages decided already is one line in the record, its reason and the rows it covers "
              "there, the answer saying it was recorded, no file of the project written, its run keeping its restore "
              "point, and the passages' states as they were",
              code == 0 and len(record) == len(held_record) + 1 and line.get("op") == "turn skip"
              and alone.get("recorded") is True and alone.get("changed") is False
              and bool(own.get("point")) and own.get("id") not in [r.get("run") for r in held_record]
              and line.get("reason") == REASON and line.get("reason_rows") == {"marked": [], "already": [71, 73]}
              and line.get("files") == 0 and "71" in line.get("what_changed", "") and "73" in line.get("what_changed", "")
              and REASON not in line.get("what_changed", "") and project_files() == held_files
              and all(states(juno).get(f"Initial:{r}") == rounds_mod.REVIEWED_EMPTY for r in (71, 73)),
              err + json.dumps(line)[:500])
        code, bare, err = run("turn", "skip", "Juno", "Initial", "71-73", "--note", ASKED)
        check("403: without a reason the same call is still no change and no line",
              code == 0 and bare.get("marked") == [] and len(agent_changes.read(root)) == len(record), err[:300])
        shown_alone = change_shown(line.get("id", ""))
        check("403: By an agent gives the line its reason and its own line, and Undo can take it back",
              shown_alone.get("reason") == REASON and shown_alone.get("state") == "ok"
              and shown_alone.get("line") and shown_alone.get("line") != i18n.t("agentchanges.op.turn_skip"),
              json.dumps(shown_alone)[:300])
        code, undone, err = run("agents", "undo-change", line.get("id", ""), "--note", "Take the reason back")
        check("403: its undo is allowed and puts nothing back, every file of the project as it was and the passages "
              "still decided, and By an agent shows it undone",
              code == 0 and undone.get("put_back") == 0 and undone.get("taken_away") == 0
              and project_files() == held_files and change_shown(line.get("id", "")).get("state") == "undone"
              and all(states(juno).get(f"Initial:{r}") == rounds_mod.REVIEWED_EMPTY for r in (71, 73)),
              err + json.dumps(undone)[:300])

        def run_shown(rid: str) -> dict:
            shown = page(lambda _b: agent_changes.review(idiograph_cli.Project(root, False)), {}, at=root)
            return next((r for r in shown.get("runs") or [] if r.get("id") == rid), {})

        # a run that changed no file, undone: marked undone as it stands, so By an agent offers no Undo again
        undo_rid = undone.get("undo_run", "")
        check("403: the undo of a reason line keeps its restore point as every run does, and By an agent offers its run's Undo",
              bool((agent_changes.load_run(root, undo_rid) or {}).get("point"))
              and run_shown(undo_rid).get("undo") == "run", json.dumps(run_shown(undo_rid))[:300])
        code, back_again, err = run("agents", "undo-run", undo_rid, "--note", "Have the reason back")
        check("403: undoing that undo's run marks it undone with nothing to put back, the reason line can be undone "
              "again, and By an agent offers no Undo for the undo's run",
              code == 0 and back_again.get("put_back") == 0 and project_files() == held_files
              and (agent_changes.load_run(root, undo_rid) or {}).get("undone")
              and run_shown(undo_rid).get("undo") is None and change_shown(line.get("id", "")).get("state") == "ok",
              err + json.dumps(run_shown(undo_rid))[:300])
        code, back_twice, err = run("agents", "undo-run", undo_rid, "--note", "Again")
        check("403: a run of no file undone already is refused, nothing written",
              code != 0 and project_files() == held_files, err[:300])
        code, whole, err = run("agents", "undo-run", line.get("run", ""), "--note", "Take the reason's run back")
        check("403: the reason line's own run undone is marked undone, nothing put back, and By an agent offers no "
              "Undo for it or its change",
              code == 0 and whole.get("put_back") == 0 and project_files() == held_files
              and (agent_changes.load_run(root, line.get("run", "")) or {}).get("undone")
              and run_shown(line.get("run", "")).get("undo") is None
              and change_shown(line.get("id", "")).get("state") == "none", err + json.dumps(whole)[:300])

        # the third review's repro: a reason line's run, then a real write joining it by its id with --run, then the
        # run undone: its files put back, never deleted as made
        code, third, err = run("turn", "skip", "Juno", "Initial", "71-73", "--note", ASKED, "--reason", REASON,
                               tool="Third agent")
        joined = agent_changes.read(root)[-1].get("run", "")
        code_join, marked75, err_join = run("turn", "skip", "Juno", "Initial", "75", "--note", ASKED, "--run", joined,
                                            tool="Third agent")
        check("403: a write joining a reason line's run by its id marks 75 in that run",
              code == 0 and code_join == 0 and marked75.get("marked") == [75]
              and agent_changes.read(root)[-1].get("run") == joined
              and states(juno).get("Initial:75") == rounds_mod.REVIEWED_EMPTY, err + err_join[:300])
        code, joined_undo, err = run("agents", "undo-run", joined, "--note", "Take the third run back")
        check("403: that run's undo puts the progress file back as it was before the run, never deleting it, and 75 "
              "is undecided again",
              code == 0 and joined_undo.get("put_back") == 1 and joined_undo.get("taken_away") == 0
              and project_files() == held_files and side.is_file()
              and states(juno).get("Initial:75") == rounds_mod.UNVISITED, err + json.dumps(joined_undo)[:300])

        held_record = agent_changes.read(root)
        code, mixed, err = run("turn", "skip", "Juno", "Initial", "71-75", "--note", ASKED, "--reason", REASON)
        record = agent_changes.read(root)
        line = record[-1] if record else {}
        check("403: a call naming an undecided passage and two decided already marks the one and records the reason "
              "for all three in one line",
              code == 0 and mixed.get("marked") == [75] and mixed.get("already") == [71, 73]
              and len(record) == len(held_record) + 1 and line.get("reason") == REASON
              and line.get("reason_rows") == {"marked": [75], "already": [71, 73]} and line.get("files") == 1
              and states(juno).get("Initial:75") == rounds_mod.REVIEWED_EMPTY, err + json.dumps(line)[:500])
        code, undone, err = run("agents", "undo-change", line.get("id", ""), "--note", "Put 75 back")
        check("403: the mixed line's undo puts 75 back undecided and leaves 71 and 73 decided",
              code == 0 and states(juno).get("Initial:75") == rounds_mod.UNVISITED
              and all(states(juno).get(f"Initial:{r}") == rounds_mod.REVIEWED_EMPTY for r in (71, 73)),
              err + json.dumps(undone)[:300])

        # a passage saved empty through turn write with a note in place of a reason, as agents did before turn skip:
        # the state is the one Skip writes, the reason moves to the record and the note is cleared
        code, _w, err = run("turn", "skip", "Juno", "Initial", "75", "--note", ASKED)
        noted = base / "noted.json"
        noted.write_text(json.dumps({"statements": [], "notes": ["Small talk, no statement"], "request": ASKED}),
                         encoding="utf-8")
        code, _w, err = run("turn", "write", "Juno", "Initial", "77", "--from", str(noted))
        check("403: a passage saved empty through turn write is in the state Skip writes",
              code == 0 and json.loads(side.read_text(encoding="utf-8"))["rows"].get("Initial:77") == rounds_mod.REVIEWED_EMPTY,
              err[:300])
        code, moved_reason, err = run("turn", "skip", "Juno", "Initial", "77", "--note", ASKED, "--reason", REASON)
        cleared = base / "cleared.json"
        cleared.write_text(json.dumps({"notes": [], "request": ASKED}), encoding="utf-8")
        code_clear, _w, err_clear = run("turn", "write", "Juno", "Initial", "77", "--from", str(cleared))
        check("403: its reason is recorded with turn skip, then turn write clears the note and the passage stays decided",
              code == 0 and moved_reason.get("already") == [77] and agent_changes.read(root)[-2].get("reason") == REASON
              and code_clear == 0 and not notes(juno).get(77)
              and json.loads(side.read_text(encoding="utf-8"))["rows"].get("Initial:77") == rounds_mod.REVIEWED_EMPTY,
              err + err_clear + json.dumps(moved_reason)[:300])
    finally:
        agent_changes.ALL_OPS = kept[0]
        if kept[1] is None:
            os.environ.pop(agent_log.PLACE, None)
        else:
            os.environ[agent_log.PLACE] = kept[1]
        agent_log.flush()
