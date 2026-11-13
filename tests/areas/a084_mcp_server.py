from __future__ import annotations

import contextlib
import inspect
import io
import json
import os
import shutil
import sys
from pathlib import Path

import rounds as rounds_mod
import workbook as wb_mod

from . import support
from .support import DEMO_QUESTION, TOOL, check
import idiograph_routes
import idiograph_cli


def test_mcp_server(scratch):
    print("\n84. The MCP server, the command line's commands as tools, Add Idiograph to Claude Desktop, and Restart "
          "and Quit in the page (189)")
    import http.client
    import shlex
    import socket
    import subprocess
    import threading
    import time
    from datetime import datetime
    from http.server import ThreadingHTTPServer
    import cli
    import locks
    import mcp_server
    import sift_mcp
    import trace_mcp
    import server as server_mod
    import themes as themes_mod

    sys.path.insert(0, str(support.source("packaging")))
    try:
        import mac_launcher
    finally:
        sys.path.remove(str(support.source("packaging")))

    app = support.text("family/static/shell.js", "apps/idiograph/static/distil.js")
    server_src = "\n".join(support.source(f).read_text(encoding="utf-8")
                           for f in ("family/server.py", "apps/idiograph/idiograph_routes.py"))
    launch_src = support.source("packaging/mac_launcher.py").read_text(encoding="utf-8")
    build_src = support.source("packaging/build_mac.py").read_text(encoding="utf-8")
    fn = lambda src, name: src.split(f"function {name}(", 1)[1].split("\n}", 1)[0] if f"function {name}(" in src else ""
    pristine = support.DEMO_PRISTINE
    py = sys.executable

    def make_root(at: Path, allowed: bool = True) -> Path:
        """Invented cases from the demo's pristine copy, each with its sidecars, and a project file."""
        shutil.rmtree(at, ignore_errors=True)
        for name in ("Juno", "Rowan", "Mabel"):
            case = at / name
            (case / "Working").mkdir(parents=True)
            shutil.copy2(pristine / f"{name} - EN & ES.xlsx", case / f"{name} - EN & ES.xlsx")
            for side in (pristine / "Working").glob(f"{name} - *"):
                shutil.copy2(side, case / "Working" / side.name)
        held = {"name": "Dogs, an MCP project", "research_question": DEMO_QUESTION}
        if allowed:
            held["agents"] = {"allowed": True, "at": "2026-10-05T20:00:00+01:00"}
        (at / server_mod.PROJECT_FILE).write_text(json.dumps(held), encoding="utf-8")
        return at

    def files(at: Path) -> dict:
        return {p.relative_to(at).as_posix(): p.read_bytes() for p in sorted(at.rglob("*")) if p.is_file() and p.name != locks.NAME}

    root = make_root(scratch / "mcp-root")
    closed = make_root(scratch / "mcp-closed", allowed=False)
    config_file = scratch / "mcp-config.json"
    config_file.write_text(json.dumps({"root": str(root), "interviewer": "Adam"}), encoding="utf-8")
    juno, rowan = root / "Juno" / "Juno - EN & ES.xlsx", root / "Rowan" / "Rowan - EN & ES.xlsx"
    desktop_file = scratch / "mcp-desktop" / "claude_desktop_config.json"

    kept = (server_mod.CONFIG_PATH, server_mod.ROOT_OVERRIDE, server_mod.STATE_MEMORY, server_mod.EXEC,
            server_mod.ARGV, server_mod.RELAUNCH, server_mod.FROZEN, server_mod.restart_blocked, dict(server_mod.PATHS),
            locks.WAIT, dict(server_mod.SERVER_STATE), os.environ.get(mcp_server.DESKTOP_ENV), server_mod.SPAWN)
    try:
        os.environ[mcp_server.DESKTOP_ENV] = str(desktop_file)

        def rpc(srv, method, params=None, mid=1):
            message = {"jsonrpc": "2.0", "id": mid, "method": method}
            if params is not None:
                message["params"] = params
            return srv.receive(json.dumps(message))

        def call(srv, name, **given):
            return rpc(srv, "tools/call", {"name": name, "arguments": given})["result"]

        # ── A. the protocol, in this process
        srv = mcp_server.Server(str(root), config=str(config_file))
        hello = rpc(srv, "initialize", {"protocolVersion": "2025-06-18", "capabilities": {},
                                        "clientInfo": {"name": "claude-ai", "version": "0.1.0"}})
        result = hello["result"]
        check("84: initialize answers the version the client asks for when it is one it speaks, with tools, its name and the app's version",
              hello["jsonrpc"] == "2.0" and hello["id"] == 1 and result["protocolVersion"] == "2025-06-18"
              and result["capabilities"] == {"tools": {"listChanged": False}, "prompts": {"listChanged": False}, "resources": {"listChanged": False}}
              and result["serverInfo"] == {"name": "idiograph", "title": "Idiograph", "version": server_mod.VERSION}
              and srv.client == "Claude Desktop")
        later = mcp_server.Server(str(root)).receive(json.dumps({"jsonrpc": "2.0", "id": "a", "method": "initialize",
                                                                 "params": {"protocolVersion": "2031-01-01"}}))
        bare = mcp_server.Server(str(root)).receive(json.dumps({"jsonrpc": "2.0", "id": 2, "method": "initialize"}))
        check("84: a version it does not speak, or none, is answered with its latest, and an id of text is kept",
              later["id"] == "a" and later["result"]["protocolVersion"] == mcp_server.LATEST == mcp_server.VERSIONS[0]
              and bare["result"]["protocolVersion"] == mcp_server.LATEST
              and set(mcp_server.VERSIONS) >= {"2024-11-05", "2025-03-26", "2025-06-18"})
        told = result["instructions"]
        check("84: its instructions are the guide's privacy line, the tools, the method and the conventions, dry_run for --dry-run",
              told.startswith("Read this first. What you read of this project goes to your model's provider.")
              and "Call cases first" in told and "## The method" in told and "Never use causal language." in told
              and "## The conventions" in told and "Set a statement aside only when he asks." in told
              and "Run every write with dry_run first" in told and "--dry-run" not in told and "## Reading" not in told)
        check("84: notifications/initialized and any other notification are taken in silence",
              srv.receive(json.dumps({"jsonrpc": "2.0", "method": "notifications/initialized"})) is None
              and srv.receive(json.dumps({"jsonrpc": "2.0", "method": "notifications/cancelled", "params": {"requestId": 1}})) is None)
        check("84: ping answers an empty result with its id",
              rpc(srv, "ping", mid=7) == {"jsonrpc": "2.0", "id": 7, "result": {}})
        nope = rpc(srv, "sampling/createMessage", mid=8)
        check("84: an unknown method is answered with the JSON-RPC error for a method not found",
              nope == {"jsonrpc": "2.0", "id": 8, "error": {"code": -32601, "message": "Method not found: sampling/createMessage"}})
        bad = [srv.receive(x) for x in ("{not json", "[]", '"a word"', '{"jsonrpc": "2.0", "id": 4}',
                                        '{"jsonrpc": "1.0", "id": 5, "method": "ping"}',
                                        '{"jsonrpc": "2.0", "id": 6, "method": "ping", "params": [1]}',
                                        '{"jsonrpc": "2.0", "id": null, "method": "ping"}')]
        check("84: a malformed line gets the parse error, a request in no right shape the invalid request, and params not a record the invalid params",
              bad[0] == {"jsonrpc": "2.0", "id": None, "error": {"code": -32700, "message": "Parse error"}}
              and [b["error"]["code"] for b in bad[1:]] == [-32600, -32600, -32600, -32600, -32602, -32600]
              and bad[3]["id"] == 4 and bad[5]["id"] == 6, str(bad))
        batch = srv.receive(json.dumps([{"jsonrpc": "2.0", "id": 10, "method": "ping"},
                                        {"jsonrpc": "2.0", "method": "notifications/initialized"}]))
        check("84: a client's answer to nothing is ignored, and a batch is answered by its requests alone",
              srv.receive(json.dumps({"jsonrpc": "2.0", "id": 3, "result": {}})) is None
              and batch == [{"jsonrpc": "2.0", "id": 10, "result": {}}])
        unknown = rpc(srv, "tools/call", {"name": "board_burn", "arguments": {}}, mid=11)
        check("84: a tool it does not have is the invalid params error, never a crash",
              unknown["error"] == {"code": -32602, "message": "Unknown tool: board_burn"})

        # ── B. tools/list, every command with its schema and its marks
        tools = rpc(srv, "tools/list", mid=12)["result"]["tools"]
        names = [t["name"] for t in tools]
        writers = {t["name"]: t for t in tools if not t["annotations"]["readOnlyHint"]}
        # Sift's and Trace's tools followed the project's until the cutover (the sixth build, 23 October 2026),
        # and since it they are on their own apps' servers alone (see areas 99, 104, 143, 145 and 226)
        sifts = [t["name"] for t in sift_mcp.SIFT_TOOLS + sift_mcp.SEARCH_TOOLS + [sift_mcp.DATABASES_TOOL, trace_mcp.TRACE_TOOL]]
        check("84: tools/list names every command of the command line, each a tool of its own, and none of Sift's or Trace's",
              names == ["cases", "search", "statements", "board_list", "board_show", "board_compare", "board_new", "board_import", "board_apply",
                        "board_current", "board_canvas", "board_rename", "board_duplicate", "board_fresh", "board_delete", "board_export",
                        "gets_export", "gets_show", "gets_apply", "gets_import", "gets_colour", "gets_take", "turn_show", "turn_write",
                        "turn_edit", "turn_interviewer_note", "turn_assign", "turn_assign_undo", "turn_trim", "turn_trim_undo",
                        "copies_refresh", "import", "import_qdpx", "timepoints", "timepoints_set",
                        "trajectories_show", "trajectories_apply", "codes_list", "codes_show", "codes_new", "codes_rename",
                        "codes_describe", "codes_merge", "codes_delete", "codes_add", "codes_remove", "codes_apply_last",
                        "codes_in_vivo", "codes_undo", "codes_redo",
                        "statement_length", "statement_length_set", "settings", "settings_set", "audio_offset", "audio_attach", "quote_heading", "transcript_replace", "transcript_replace_undo", "validate", "agent_changes", "agent_undo_run", "agent_log", "project_send", "project_export_qdpx", "project_send_list", "project_open_copy",
                        "project_add_transcripts", "project_boards_in",
                        "project_set", "project_remove", "project_show", "project_history", "team_show", "team_on", "team_set", "team_invite",
                        "team_answers", "team_admit", "team_join", "team_joined", "team_remove", "team_lead", "team_take", "team_send",
                        "team_board_send", "team_board_take", "team_board_answer", "team_boards",
                        "names_list", "names_check", "names_replace", "names_remove",
                        "project_new", "participant_rename", "participant_show", "participant_set",
                        "demographics_show", "demographics_apply", "demographics_move_tags", "participant_complete",
                        "participant_export", "board_note", "board_history", "board_revision", "board_restore", "board_copy", "board_complete", "gets_fresh",
                        "gets_duplicate", "gets_rename", "gets_note", "gets_canvas", "gets_current", "gets_delete",
                        "gets_complete", "gets_history", "gets_revision", "gets_restore", "gets_subs", "gets_settings",
                        "gets_settings_set", "team_review", "team_ask", "team_comment", "team_review_send", "team_reply",
                        "team_thread", "team_review_done", "team_suggest", "team_suggestion_answer"]
              and not set(sifts) & set(names)
              and {t["command"] for t in mcp_server.TOOLS if t["command"][0] not in ("sift", "trace")}
              == set(idiograph_cli.COMMANDS) | {("search", None), ("project", "open-copy")}
              and all("command" not in t for t in tools))
        check("84: each with a JSON Schema for its input, a title and a plain description, no em dash and no semicolon",
              all(t["inputSchema"]["type"] == "object" and t["inputSchema"]["additionalProperties"] is False
                  and t["title"] and len(t["description"]) > 60 and "\u2014" not in t["description"] and ";" not in t["description"]
                  for t in tools)
              and tools[2]["inputSchema"]["required"] == ["case"] and "case" in tools[4]["inputSchema"]["properties"]
              and tools[6]["inputSchema"]["properties"]["pets"]["items"]["required"] == ["title"])
        writers = {n: t for n, t in writers.items() if n not in sifts}
        check("84: the read tools are marked as only reading, and the writing ones take request and dry_run, request required",
              sorted(writers) == ["agent_undo_run", "audio_attach", "audio_offset", "board_apply", "board_canvas", "board_complete", "board_copy",
                                 "board_current", "board_delete", "board_duplicate", "board_export",
                                 "board_fresh", "board_import", "board_new", "board_note", "board_rename",
                                 "board_restore", "board_revision",
                                 "codes_add", "codes_apply_last", "codes_delete", "codes_describe", "codes_in_vivo", "codes_merge",
                                 "codes_new", "codes_redo",
                                 "codes_remove", "codes_rename", "codes_undo", "copies_refresh", "demographics_apply",
                                 "demographics_move_tags",
                                 "gets_apply", "gets_canvas",
                                 "gets_colour", "gets_complete", "gets_current", "gets_delete",
                                 "gets_duplicate", "gets_export", "gets_fresh", "gets_import", "gets_note",
                                 "gets_rename", "gets_restore", "gets_revision", "gets_settings_set",
                                 "gets_subs", "gets_take", "import", "import_qdpx", "names_remove", "names_replace",
                                 "participant_complete", "participant_export", "participant_rename", "participant_set",
                                 "project_add_transcripts",
                                 "project_boards_in", "project_export_qdpx", "project_new", "project_open_copy", "project_remove", "project_send",
                                 "project_set", "quote_heading", "settings_set", "statement_length_set",
                                 "team_admit", "team_ask", "team_board_answer", "team_board_send", "team_board_take",
                                 "team_comment", "team_invite", "team_join", "team_joined", "team_lead", "team_on",
                                 "team_remove", "team_reply", "team_review_done", "team_review_send", "team_send",
                                 "team_set", "team_suggest", "team_suggestion_answer", "team_take", "team_thread",
                                 "timepoints_set",
                                 "trajectories_apply", "transcript_replace", "transcript_replace_undo", "turn_assign", "turn_assign_undo", "turn_edit",
                                 "turn_interviewer_note", "turn_trim", "turn_trim_undo", "turn_write"]
              and all(t["annotations"]["readOnlyHint"] is True and t["annotations"]["openWorldHint"] is False
                      for t in tools if t["name"] not in writers and t["name"] not in sifts)
              and all({"request", "dry_run"} <= set(t["inputSchema"]["properties"]) and "request" in t["inputSchema"]["required"]
                      for n, t in writers.items() if n not in ("board_export", "gets_export", "participant_export", "project_send", "project_export_qdpx",
                                                                        "project_open_copy", "team_send"))
              # Send now writes no History, so it takes request without asking for it (smokefix, 9 November 2026)
              and {"request", "dry_run"} <= set(writers["team_send"]["inputSchema"]["properties"])
              and "request" not in (writers["team_send"]["inputSchema"].get("required") or [])
              and writers["board_new"]["annotations"]["destructiveHint"] is False
              and writers["turn_write"]["annotations"]["destructiveHint"] is True)

        # ── C. each read tool on an invented project, the command line's own words and JSON
        def same(name, argv, **given):
            got = call(srv, name, **given)
            code, out, _ = cli.run(["--root", str(root), "--config", str(config_file), *argv])
            _, data, _ = cli.run(["--root", str(root), "--config", str(config_file), *argv, "--json"])
            text = support.unfenced(got["content"][0]["text"]) if len(got["content"]) == 1 and got["content"][0]["type"] == "text" else None
            return (got["isError"] is False and code == 0 and text is not None and text.rstrip("\n") == out.rstrip("\n")
                    and support.plain(got["structuredContent"]) == support.plain(json.loads(data))), got

        ok_cases, got = same("cases", ["cases"])
        check("84: cases is the command line's cases, its words as text and its JSON as structuredContent",
              ok_cases and "Dogs, an MCP project" in support.unfenced(got["content"][0]["text"])
              and [c["case"] for c in support.plain(got["structuredContent"])["cases"]] == ["Juno", "Mabel", "Rowan"])
        ok_st, got = same("statements", ["statements", "Rowan"], case="Rowan")
        check("84: statements, board_list and board_show are the commands of their names on a case named by its pseudonym",
              ok_st and support.plain(got["structuredContent"])["statements"][0]["id"] == "S1"
              and same("board_list", ["board", "list", "Rowan"], case="Rowan")[0]
              and same("board_show", ["board", "show", "Rowan", "v1"], case="Rowan", board="v1")[0]
              and same("board_show", ["board", "show", "Rowan"], case="Rowan")[0])
        check("84: turn_show takes a row or a span, and validate reads every file against its schema",
              same("turn_show", ["turn", "show", "Juno", "Initial", "14-15"], case="Juno", sheet="Initial", row="14-15")[0]
              and same("turn_show", ["turn", "show", "Juno", "Initial", "15"], case="Juno", sheet="Initial", row=15)[0]
              and same("validate", ["validate"])[0] and support.plain(call(srv, "validate")["structuredContent"])["valid"] is True)
        gets = call(srv, "gets_show")
        check("84: gets_show on a project with no GETs file is the command line's refusal, as an error result",
              gets["isError"] is True and support.unfenced(gets["content"][0]["text"]) == "This project has no GETs file yet. It comes with the first act on the GETs screen."
              and support.plain(gets["structuredContent"])["lines"] == [support.unfenced(gets["content"][0]["text"])])

        # ── D. a dry run, then a real write, a revision kept, made naming the client
        plan = [{"title": "A lonely year she filled", "note": "His reading of the year.", "members": ["S2", "S3", "S4"],
                 "subs": [{"title": "Company on the dark walks", "members": ["S5", "S6"]}]},
                {"title": "A flat that could not hold her", "members": ["S20", "S21"]}]
        before = files(root)
        dry = call(srv, "board_new", case="Rowan", pets=plan, not_placed={"S1": "Tense more than experience"},
                   request="Make a board of two PETs", dry_run=True)
        check("84: board_new with dry_run says what it would make and writes nothing",
              dry["isError"] is False and support.unfenced(dry["content"][0]["text"]).startswith("Dry run, nothing was written. It would make Board 2 on Rowan, from Board 1: 2 PETs")
              and support.plain(dry["structuredContent"])["dry_run"] is True and files(root) == before)
        loose = call(srv, "board_new", case="Rowan", pets=json.dumps(plan), request="Make a board", dry_run=True)
        check("84: a structure sent as JSON text, as some clients send one, is read as the structure",
              loose["isError"] is False and support.unfenced(loose["content"][0]["text"]).startswith("Dry run") and files(root) == before)
        made = call(srv, "board_new", case="Rowan", pets=plan, not_placed={"S1": "Tense more than experience"},
                    request="Make a board of two PETs")
        stored = json.loads(themes_mod.themes_path(rowan).read_text(encoding="utf-8"))
        board = stored["boards"][-1]
        check("84: the real write lands as the next board, Board N as 184 names it, made by the client initialize named, with his request",
              made["isError"] is False and support.plain(made["structuredContent"])["name"] == "Board 2" and board["name"] == "Board 2"
              and board["made"]["by"] == "agent" and board["made"]["tool"] == "Claude Desktop"
              and board["made"]["request"] == "Make a board of two PETs"
              and board["note"].startswith("Made by Claude Desktop in a conversation on ")
              and support.unfenced(made["content"][0]["text"]).startswith("Made Board 2 on Rowan, from Board 1: 2 PETs"))
        changed = call(srv, "board_apply", case="Rowan", board="Board 2",
                       operations=[{"op": "retitle", "label": "g1", "title": "A lonely year that she filled"}],
                       request="Retitle the lonely year")
        after = json.loads(themes_mod.themes_path(rowan).read_text(encoding="utf-8"))["boards"][-1]
        history = themes_mod.history_of(after)
        check("84: board_apply changes the board through revise's operations, the board as it stood kept first in its History",
              changed["isError"] is False and "kept first in its History" in support.unfenced(changed["content"][0]["text"])
              and any(g["label"] == "A lonely year that she filled" for g in after["groups"])
              and history and history[-1]["name"] == "Before: Retitle the lonely year"
              and history[-1]["made"]["tool"] == "Claude Desktop" and after["changed"]["tool"] == "Claude Desktop")
        compared = call(srv, "board_compare", case="Rowan", boards=["v1", "Board 2"])
        check("84: board_compare takes the boards as a list, as the command line takes them",
              compared["isError"] is False and support.plain(compared["structuredContent"])["boards"][1]["name"] == "Board 2"
              and "statement pairs placed alike" in support.unfenced(compared["content"][0]["text"]))
        turn = {"statements": ["A walk she knows better than anyone"],
                "quotes": ["there are mornings where I genuinely think she is walking me"]}
        book_before = juno.read_bytes()
        dry_turn = call(srv, "turn_write", case="Juno", sheet="Initial", row=15, request="Code turn 15", dry_run=True, **turn)
        lock = wb_mod.lock_file(juno)
        lock.write_text("", encoding="utf-8")
        try:
            held = call(srv, "turn_write", case="Juno", sheet="Initial", row=15, request="Code turn 15", **turn)
        finally:
            lock.unlink()
        check("84: turn_write's dry run writes nothing, and Excel holding the workbook is a refusal with its own line",
              dry_turn["isError"] is False and support.unfenced(dry_turn["content"][0]["text"]).startswith("Dry run, nothing was written.")
              and held["isError"] is True and "is open in Excel" in support.unfenced(held["content"][0]["text"])
              and juno.read_bytes() == book_before and not (root / "Juno" / "_Archive").exists())
        wrote = call(srv, "turn_write", case="Juno", sheet="Initial", row="15", request="Code turn 15", **turn)
        edit = json.loads(rounds_mod.progress_path(juno).read_text(encoding="utf-8"))["edits"][-1]
        check("84: the real turn write keeps the trim-style backup first, and the progress file names the client",
              wrote["isError"] is False and len(list((root / "Juno" / "_Archive").glob("*.xlsx"))) == 1
              and edit["tool"] == "Claude Desktop" and edit["request"] == "Code turn 15")

        # ── E. refusals as results with isError, the refusal's own line, never a crash
        shut = mcp_server.Server(str(closed), config=str(config_file))
        refused = call(shut, "cases")
        check("84: a project without the privacy tick is refused in the command line's own line, as an error result",
              refused["isError"] is True and support.unfenced(refused["content"][0]["text"]) == idiograph_cli.PRIVATE
              and support.plain(refused["structuredContent"]) == {"error": idiograph_cli.PRIVATE, "lines": [idiograph_cli.PRIVATE]})
        nobody = call(srv, "statements", case="Nobody")
        stray = call(srv, "board_new", case="Rowan", pets=[{"title": "A PET", "members": ["S999"]}], request="Try", dry_run=True)
        binned = call(srv, "board_apply", case="Rowan", board="Board 2", operations=[{"op": "delete", "items": ["S2"]}],
                      request="Delete it")
        check("84: an unknown case, an unknown statement and a delete come back as error results, nothing written",
              nobody["isError"] is True and support.unfenced(nobody["content"][0]["text"]).startswith("No participant called Nobody in this project.")
              and stray["isError"] is True and "S999 in 'A PET' is not a statement of this participant." in support.unfenced(stray["content"][0]["text"])
              and binned["isError"] is True and idiograph_cli.NO_DELETE in support.unfenced(binned["content"][0]["text"]))
        missing = call(srv, "board_show")
        extra = call(srv, "cases", colour="blue")
        wrong = call(srv, "board_new", case="Rowan", pets="not a list", request="Try")
        check("84: an input the schema refuses says which, in plain words, with nothing done",
              missing["isError"] is True and support.unfenced(missing["content"][0]["text"]) == "input.case is missing.\nNothing was done."
              and extra["isError"] is True and "input.colour is not an input this tool takes." in support.unfenced(extra["content"][0]["text"])
              and wrong["isError"] is True and "input.pets should be a list, not text." in support.unfenced(wrong["content"][0]["text"]))
        broken = mcp_server.Server(str(root), config=str(config_file))
        broken.receive(json.dumps({"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {}}))
        real_perform = cli.perform
        cli.perform = lambda args: 1 / 0
        try:
            with contextlib.redirect_stderr(io.StringIO()):
                crashed = call(broken, "cases")
        finally:
            cli.perform = real_perform
        check("84: a bug in a command is an error result saying so in one line, never a crash",
              crashed["isError"] is True and support.unfenced(crashed["content"][0]["text"]) == "Idiograph could not do that: ZeroDivisionError. Nothing more was done.")
        check("84: made names the client by its clientInfo, Claude Code and any other by its title or name, an agent with none",
              mcp_server.client_name({"name": "claude-code"}) == "Claude Code"
              and mcp_server.client_name({"name": "some-client", "title": "Some Client"}) == "Some Client"
              and mcp_server.client_name({"name": "some-client"}) == "some-client" and mcp_server.client_name(None) == ""
              and idiograph_cli.mark(cli.argparse.Namespace(tool="", note="x"), "now")["tool"] == cli.TOOL)

        # ── F. a child process: stdout holds nothing but the protocol, and the Mac app's way runs it too
        lines = [{"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {"protocolVersion": "2025-11-25",
                                                                                "clientInfo": {"name": "claude-ai"}}},
                 {"jsonrpc": "2.0", "method": "notifications/initialized"},
                 {"jsonrpc": "2.0", "id": 2, "method": "tools/list"},
                 {"jsonrpc": "2.0", "id": 3, "method": "tools/call", "params": {"name": "board_list", "arguments": {"case": "Rowan"}}}]
        feed = ("\n".join(json.dumps(x) for x in lines) + "\nnot json at all\n\n").encode("utf-8")
        noisy = ("import sys\nsys.path.insert(0, %r)\nimport mcp_server\nreal = mcp_server.Server.call\n"
                 "def call(self, t, given):\n    print('a line the app printed')\n    return real(self, t, given)\n"
                 "mcp_server.Server.call = call\nraise SystemExit(mcp_server.main(sys.argv[1:]))\n") % str(TOOL)
        env = dict(os.environ, PYTHONUNBUFFERED="1")
        run = subprocess.run([py, "-c", noisy, "--root", str(root), "--config", str(config_file)], input=feed,
                             capture_output=True, timeout=120, env=env)
        answers = [support.plain(json.loads(x)) for x in run.stdout.decode("utf-8").splitlines()]
        quiet_ok = (run.returncode == 0 and [a.get("id") for a in answers] == [1, 2, 3, None]
              and all(a["jsonrpc"] == "2.0" for a in answers) and answers[0]["result"]["protocolVersion"] == "2025-11-25"
              and answers[3]["error"]["code"] == -32700 and "a line the app printed" in run.stderr.decode("utf-8")
              and "a line the app printed" not in run.stdout.decode("utf-8")
              and support.unfenced(answers[2]["result"]["content"][0]["text"]).startswith("Rowan: 2 boards"))
        check("84: run as a child, standard output holds the protocol alone, a print by the app going to standard error",
              quiet_ok, "" if quiet_ok else run.stderr.decode("utf-8")[-300:])
        launched = subprocess.run([py, str(support.source("packaging/mac_launcher.py")), "mcp", "--root", str(root), "--config",
                                   str(config_file)], input=feed, capture_output=True, timeout=120, env=env)
        via = [support.plain(json.loads(x)) for x in launched.stdout.decode("utf-8").splitlines()]
        via_ok = (launched.returncode == 0 and [a.get("id") for a in via] == [1, 2, 3, None]
              and 'if given[:1] == ["mcp"]:' in launch_src and "return mcp.main(args)" in launch_src
              and all("mcp_server" in support.build_mac().modules(app) for app in ("idiograph", "sift", "trace"))
              and '"cli", "locks",' in build_src)
        check("84: the Mac app's executable with mcp first runs the same server, as the bundle runs it",
              via_ok, "" if via_ok else launched.stderr.decode("utf-8")[-300:])

        # ── G. the entry, from source and in the bundle
        fake = scratch / "mcp-fake-repo"
        shutil.rmtree(fake, ignore_errors=True)
        tool = fake / "Tools" / "idiograph"
        tool.mkdir(parents=True)
        # a stub file where the venv's python goes, never a link to a real python (14 October)
        inside = ("Scripts", "python.exe") if sys.platform.startswith("win") else ("bin", "python3")
        stub = fake.joinpath(".venv", *inside)
        stub.parent.mkdir(parents=True)
        stub.write_text("a stand-in, never run\n", encoding="utf-8")
        source_cmd = mcp_server.server_command(frozen=False, here=tool)
        bare_cmd = mcp_server.server_command(frozen=False, executable="/usr/bin/python3", here=scratch / "mcp-no-venv" / "a" / "b")
        app_exe = "/Applications/Idiograph.app/Contents/MacOS/Idiograph"
        check("84: from source the entry runs the venv's python by its own path, never the one its link leads to, with mcp_server.py",
              source_cmd == [str(stub), str(tool / "mcp_server.py")]
              and ".resolve()" not in inspect.getsource(mcp_server.venv_python)
              and bare_cmd[0] == os.path.abspath("/usr/bin/python3"))
        # the Mac app's entry asked of a Mac by name, so it reads the same on the Windows machine the suite
        # also runs on, whose app names its console twin in its place (14 October)
        entry = mcp_server.desktop_entry(root, frozen=True, executable=app_exe, system="darwin")
        check("84: in the Mac app the entry is the app's own executable with mcp first, then --root, --demo or --config",
              entry == {"command": app_exe, "args": ["mcp", "--root", str(root)]}
              and mcp_server.desktop_entry(None, demo=True, frozen=True, executable=app_exe, system="darwin")["args"] == ["mcp", "--demo"]
              and mcp_server.desktop_entry(root, config=config_file, frozen=True, executable=app_exe, system="darwin")["args"][-2:]
              == ["--config", str(config_file)])
        shown = mcp_server.setup(entry)
        # the line quoted for the shell it is pasted into: cmd's quoting on Windows, a Mac's elsewhere
        line = (subprocess.list2cmdline([app_exe, "mcp", "--root", str(root)]) if sys.platform == "win32"
                else f"{app_exe} mcp --root {shlex.quote(str(root))}")
        check("84: the card's entry for any other client and the one line for Claude Code",
              support.plain(json.loads(shown["json"])) == {"mcpServers": {"idiograph": entry}}
              and shown["claude_code"] == f"claude mcp add --scope user idiograph -- {line}"
              and shown["desktop"] == mcp_server.shown_path(desktop_file) and shown["there"] is False)

        # ── H. the config writer, only ever at the scratch file the environment names
        home_path = None
        held_env = os.environ.pop(mcp_server.DESKTOP_ENV)
        try:
            home_path = mcp_server.desktop_config_path()
        finally:
            os.environ[mcp_server.DESKTOP_ENV] = held_env
        check("84: Claude Desktop's file is the one under Application Support on a Mac, and the environment variable points it at a scratch file",
              mcp_server.desktop_config_path() == desktop_file
              and (sys.platform != "darwin"
                   or home_path == Path.home() / "Library" / "Application Support" / "Claude" / "claude_desktop_config.json"))
        shutil.rmtree(desktop_file.parent, ignore_errors=True)
        first = mcp_server.add_to_desktop(entry)
        check("84: a new file is made with the entry under mcpServers, and the line says to restart Claude Desktop",
              first["written"] is True and first["backup"] is None
              and json.loads(desktop_file.read_text(encoding="utf-8")) == {"mcpServers": {"idiograph": entry}}
              and first["said"] == "Added Idiograph to Claude Desktop. Restart Claude Desktop to use it.")
        others = {"preferences": {"theme": "dark"}, "mcpServers": {"notes": {"command": "/usr/bin/notes", "args": []}}}
        desktop_file.write_text(json.dumps(others), encoding="utf-8")
        old_bytes = desktop_file.read_bytes()
        second = mcp_server.add_to_desktop(entry, now=datetime(2026, 10, 5, 19, 2, 33))
        now_held = json.loads(desktop_file.read_text(encoding="utf-8"))
        copy = desktop_file.with_name("claude_desktop_config.json.before-idiograph-20261005-190233")
        check("84: a file already there keeps every other entry and key, and a copy of it as it was is kept beside it first",
              second["written"] is True and now_held["preferences"] == {"theme": "dark"}
              and now_held["mcpServers"] == {"notes": {"command": "/usr/bin/notes", "args": []}, "idiograph": entry}
              and copy.read_bytes() == old_bytes and second["backup"] == copy.name and copy.name in second["said"]
              and second["said"].endswith("Restart Claude Desktop to use it."))
        copies = sorted(desktop_file.parent.iterdir())
        again = mcp_server.add_to_desktop(entry)
        check("84: the same entry again is said to be there and writes nothing, no second copy",
              again["written"] is False and sorted(desktop_file.parent.iterdir()) == copies)
        desktop_file.write_text('{"mcpServers": {', encoding="utf-8")
        refusals = []
        for text in ('{"mcpServers": {', "[1, 2]", '{"mcpServers": []}'):
            desktop_file.write_text(text, encoding="utf-8")
            try:
                mcp_server.add_to_desktop(entry)
                refusals.append(None)
            except mcp_server.DesktopRefused as exc:
                refusals.append((str(exc), desktop_file.read_text(encoding="utf-8") == text))
        check("84: a file that is not valid JSON, or not a record of servers, is refused in one line and left as it is",
              refusals == [(mcp_server.INVALID, True)] * 3 and "\n" not in mcp_server.INVALID)

        # ── I. the route, from the server's own page alone
        server_mod.CONFIG_PATH = config_file
        server_mod.ROOT_OVERRIDE = str(root)
        server_mod.STATE_MEMORY = {"recent": []}
        desktop_file.unlink()
        routed = idiograph_routes.api_mcp({"path": str(juno), "op": "show"})
        check("84: /api/mcp shows the entry for the project in front of him, its root and this server's own settings file",
              routed["entry"]["args"][-4:] == ["--root", str(root.resolve()), "--config", str(config_file)]
              and routed["entry"]["args"][0].endswith("mcp_server.py") and routed["there"] is False and not desktop_file.exists())
        added = idiograph_routes.api_mcp({"path": str(juno), "op": "add"})
        check("84: and with add writes it into the file Claude Desktop reads, here the scratch one",
              added["written"] is True and json.loads(desktop_file.read_text(encoding="utf-8"))["mcpServers"]["idiograph"]
              == routed["entry"] and "/api/mcp" in server_mod.POST_ONLY and server_mod.ROUTES["/api/mcp"] is idiograph_routes.api_mcp)

        httpd = ThreadingHTTPServer(("127.0.0.1", 0), server_mod.Handler)
        port = httpd.server_address[1]
        serving = threading.Thread(target=httpd.serve_forever, kwargs={"poll_interval": 0.05}, daemon=True)
        serving.start()

        def post(path, body, origin=None, host=None):
            conn = http.client.HTTPConnection("127.0.0.1", port, timeout=20)
            headers = {"Content-Type": "application/json", "Host": host or f"127.0.0.1:{port}"}
            if origin:
                headers["Origin"] = origin
            conn.request("POST", path, json.dumps(body), headers)
            res = conn.getresponse()
            out = (res.status, json.loads(res.read() or b"{}"))
            conn.close()
            return out

        def get(path):
            conn = http.client.HTTPConnection("127.0.0.1", port, timeout=20)
            conn.request("GET", path)
            res = conn.getresponse()
            out = (res.status, json.loads(res.read() or b"{}"))
            conn.close()
            return out

        own = f"http://127.0.0.1:{port}"
        elsewhere = post("/api/server", {"op": "quit"}, origin="https://example.com")
        rebound = post("/api/server", {"op": "quit"}, origin=f"http://example.com:{port}", host=f"example.com:{port}")
        mcp_elsewhere = post("/api/mcp", {"path": str(juno), "op": "add"}, origin="https://example.com")
        check("84: a POST from a page served anywhere else is refused, by its Origin or its Host, and nothing stops",
              elsewhere == (403, {"error": server_mod.named(server_mod.ELSEWHERE)}) and rebound[0] == 403 and mcp_elsewhere[0] == 403
              and server_mod.SERVER_STATE["op"] is None and serving.is_alive()
              and server_mod.own_origin({"Host": f"localhost:{port}", "Origin": f"http://localhost:{port}"}, ("127.0.0.1", port))
              and not server_mod.own_origin({"Host": f"127.0.0.1:{port}", "Origin": "null"}, ("127.0.0.1", port)))
        def get_as(path, host):
            conn = http.client.HTTPConnection("127.0.0.1", port, timeout=20)
            conn.request("GET", path, headers={"Host": host})
            res = conn.getresponse()
            out = (res.status, json.loads(res.read() or b"{}"))
            conn.close()
            return out

        any_post = post("/api/stamp", {}, origin="https://example.com")
        own_post = post("/api/stamp", {}, origin=own)
        foreign_get = get_as("/api/server", f"example.com:{port}")
        check("every route, not Restart and Quit alone, refuses a page served elsewhere and a name that only points here, "
              "and the app's own page is answered",
              any_post == (403, {"error": server_mod.named(server_mod.ELSEWHERE)}) and own_post[0] != 403
              and foreign_get == (403, {"error": server_mod.named(server_mod.ELSEWHERE)}) and get("/api/server")[0] == 200
              and "if not own_origin(self.headers, self.server.server_address):" in
              inspect.getsource(server_mod.Handler.do_GET) + inspect.getsource(server_mod.Handler.do_POST)
              and inspect.getsource(server_mod.Handler.do_POST).count("own_origin(") == 2,
              f"{any_post} {own_post[0]} {foreign_get}")
        state = get("/api/server")
        check("84: a GET answers the server's state, its start, its pid, whether it can restart and how to open it again, and never acts",
              state[0] == 200 and state[1]["started"] == server_mod.STARTED and state[1]["pid"] == os.getpid()
              and state[1]["restart"] is None and state[1]["reopen"].startswith("To open it again,")
              and get("/api/server?op=quit")[1]["started"] == server_mod.STARTED and serving.is_alive())
        check("84: an op that is neither is refused",
              post("/api/server", {"op": "stop"}, origin=own) == (400, {"error": "The op is restart or quit."}))
        server_mod.restart_blocked = lambda system=None: server_mod.named(server_mod.WINDOWS_LINE)
        windows = post("/api/server", {"op": "restart"}, origin=own)
        server_mod.restart_blocked = kept[7]
        # Windows with no way to start the server anew says it cannot, and with the server's own, spawn_again,
        # or the Windows app's, it can (14 October)
        server_mod.SPAWN = None
        no_way = server_mod.restart_blocked("win32")
        server_mod.SPAWN = server_mod.spawn_again
        own_way = server_mod.restart_blocked("win32")
        server_mod.SPAWN = kept[12]
        check("84: where the way it runs cannot restart itself, Restart says so in one line and does nothing",
              windows == (409, {"error": server_mod.named(server_mod.WINDOWS_LINE)}) and serving.is_alive()
              and no_way == server_mod.named(server_mod.WINDOWS_LINE) and own_way is None and server_mod.restart_blocked("darwin") is None)
        locks.WAIT = 0.1
        server_mod._lock.acquire()
        try:
            busy = post("/api/server", {"op": "restart"}, origin=own)
        finally:
            server_mod._lock.release()
        locks.WAIT = kept[9]
        letgo = threading.Timer(0.2, server_mod._lock.release)
        server_mod._lock.acquire()
        started_at = time.monotonic()
        letgo.start()
        waited = server_mod.quiet(wait=5)
        took = time.monotonic() - started_at
        check("84: a write in hand is waited for, and one still under way after the wait refuses in one line",
              busy == (409, {"error": "A write is still under way, so Idiograph did not restart. Try again in a moment."})
              and server_mod.SERVER_STATE["op"] is None and waited is True and took >= 0.15)
        answer = post("/api/server", {"op": "restart"}, origin=own)
        serving.join(10)
        check("84: Restart answers first, with the start the page waits past, then the serving stops",
              answer[0] == 200 and answer[1]["op"] == "restart" and answer[1]["started"] == server_mod.STARTED
              and server_mod.SERVER_STATE["op"] == "restart" and not serving.is_alive())
        httpd.socket.close()
        execs = []
        # the way a Mac and Linux run it again, asked on any system, Windows's own way (SPAWN) set aside
        server_mod.SPAWN = None
        server_mod.EXEC = lambda path, argv, env: execs.append((path, list(argv), dict(env)))
        server_mod.ARGV = [str(support.source("server.py")), "--port", "8790", "--no-browser"]
        server_mod.RELAUNCH = None
        with contextlib.redirect_stdout(io.StringIO()):
            server_mod.finish("restart", 8790)
            server_mod.FROZEN = True
            server_mod.finish("restart", 8790)
            server_mod.FROZEN = kept[6]
            server_mod.RELAUNCH = mac_launcher.relaunch_command("8790", ["--no-browser"])
            server_mod.finish("restart", 8790)
        check("84: then the same program runs again in this process, with the same arguments, the frozen app with --serve",
              execs[0][0] == sys.executable and execs[0][1] == [sys.executable, str(support.source("server.py")), "--port", "8790", "--no-browser"]
              and execs[0][2][server_mod.RESTARTED] == "1" and "PYINSTALLER_RESET_ENVIRONMENT" not in execs[0][2]
              and execs[1][1] == [sys.executable, "--serve", "--port", "8790", "--no-browser"]
              and execs[1][2]["PYINSTALLER_RESET_ENVIRONMENT"] == "1"
              and execs[2][1] == [sys.executable, str(support.source("packaging/mac_launcher.py").resolve()), "--serve", "--port",
                                  "8790", "--no-browser"]
              and server_mod._lock.acquire(timeout=1) and (server_mod._lock.release() or True))
        logs = scratch / "mcp-logs"
        logs.mkdir(exist_ok=True)
        server_mod.PATHS["logs"] = logs
        (logs / "idiograph-8790.pid").write_text(f"{os.getpid()}\n", encoding="utf-8")
        (logs / "idiograph-8791.pid").write_text("1\n", encoding="utf-8")
        with contextlib.redirect_stdout(io.StringIO()):
            server_mod.finish("quit", 8790)
            server_mod.finish("quit", 8791)
        check("84: Quit clears the pid file a launcher keeps when it names this process, and leaves another's alone",
              not (logs / "idiograph-8790.pid").exists() and (logs / "idiograph-8791.pid").read_text(encoding="utf-8") == "1\n"
              and len(execs) == 3)

        def no_exec(path, argv, env):
            raise OSError("no such file")

        server_mod.EXEC = no_exec
        (logs / "idiograph-8790.pid").write_text(f"{os.getpid()}\n", encoding="utf-8")
        said_out = io.StringIO()
        with contextlib.redirect_stdout(said_out):
            server_mod.finish("restart", 8790)
        check("84: a program that cannot run again ends as Quit does, saying why, the pid file cleared",
              "Idiograph could not start again: no such file" in said_out.getvalue()
              and "Idiograph is closed." in said_out.getvalue() and not (logs / "idiograph-8790.pid").exists()
              and server_mod._lock.acquire(timeout=1) and (server_mod._lock.release() or True))
        main_src = server_src.split("def main() -> None:", 1)[1]
        check("84: main finishes a restart or a quit once the serving stops, closing the socket without waiting on open requests",
              'if SERVER_STATE["op"]:\n            # Restart and Quit close the socket at once' in main_src
              and "server.socket.close()" in main_src and 'finish(SERVER_STATE["op"], args.port)' in main_src
              and "not args.no_browser and not os.environ.get(RESTARTED)" in main_src
              and "server.RELAUNCH = relaunch_command(port, extra)" in launch_src)

        # ── I2. the start asks no name of the network (7 November 2026, GitHub's Mac)
        looked = []

        def no_lookup(name=""):
            looked.append(name)
            raise OSError("no name lookup at the start")

        kept_fqdn = socket.getfqdn
        socket.getfqdn = no_lookup
        try:
            bound = server_mod.AppServer(("127.0.0.1", 0), server_mod.Handler)
        except OSError as gone:
            bound = gone
        finally:
            socket.getfqdn = kept_fqdn
        named = getattr(bound, "server_name", None), getattr(bound, "server_port", None)
        if isinstance(bound, server_mod.AppServer):
            bound.server_close()
        check("84, 7 November: the server binds without looking up this computer's name, which held every real "
              "server's start for half a minute on GitHub's Mac",
              isinstance(bound, server_mod.AppServer) and not looked and named[0] == "127.0.0.1"
              and isinstance(named[1], int) and named[1] > 0
              and "socketserver.TCPServer.server_bind(self)" in server_src, f"{looked} {named}")

        # ── J. a real restart and quit, a child server on a free port of a scratch root
        with socket.socket() as probe:
            probe.bind(("127.0.0.1", 0))
            free = probe.getsockname()[1]
        child = subprocess.Popen([py, str(support.source("server.py")), "--port", str(free), "--no-browser", "--root", str(root),
                                  "--config", str(config_file)], stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                                 env=support.faulty_env(dict(os.environ, PYTHONUNBUFFERED="1", IDIOGRAPH_START="run.sh")))
        watch = support.ChildWatch(child, free)
        port = free

        def wait_state(not_started=None, seconds=20):
            until = time.monotonic() + seconds
            while time.monotonic() < until:
                try:
                    status, data = get("/api/server")
                    if status == 200 and data.get("started") != not_started:
                        watch.answered()
                        return data
                except OSError:
                    pass
                time.sleep(0.05)
            watch.ran_out(f"wait_state's {seconds} s ran out")
            return None

        def port_closed(seconds=20):
            until = time.monotonic() + seconds
            while True:
                with socket.socket() as probe:
                    if probe.connect_ex(("127.0.0.1", port)) != 0:
                        return True
                if time.monotonic() >= until:
                    watch.ran_out(f"port_closed's {seconds} s ran out")
                    return False
                time.sleep(0.05)

        errors = []

        def step(what, run, default):
            """One call of the run: its answer, or `default` where a connect or a read fails, the failure kept
            for the detail and the child, if it still runs, sent SIGABRT, so the check can say what it saw."""
            try:
                return run()
            except (OSError, http.client.HTTPException, ValueError, subprocess.TimeoutExpired) as err:
                errors.append(f"{what}: {type(err).__name__}: {err}")
                watch.ran_out(f"{what} failed")
                return default

        first_state = second_state = None
        restarted = quit_answer = (None, {})
        code = None
        refused_port = False
        try:
            first_state = wait_state()
            own = f"http://127.0.0.1:{port}"
            restarted = step("the restart call", lambda: post("/api/server", {"op": "restart"}, origin=own), (None, {}))
            second_state = wait_state(not_started=first_state and first_state["started"])
            quit_answer = step("the quit call", lambda: post("/api/server", {"op": "quit"}, origin=own), (None, {}))
            code = step("the child's exit", lambda: child.wait(20), None)
            # on Windows the server starts anew as a process of its own, writing to the same output, so the
            # port is watched until it closes rather than the first process alone waited for (14 October)
            refused_port = port_closed()
        finally:
            if child.poll() is None:
                child.kill()
                child.wait(10)
            anew = (second_state or {}).get("pid")
            if anew and anew != child.pid and not refused_port:
                try:
                    os.kill(anew, 15)
                except OSError:
                    pass
        said = child.stdout.read().decode("utf-8", errors="replace")
        # the same process on a Mac and on Linux, and on Windows, which cannot run a program again in
        # one process, a process of its own that the first hands on to and then ends
        pids_ok = (second_state["pid"] != first_state["pid"] == child.pid if sys.platform == "win32"
                   else second_state["pid"] == first_state["pid"] == child.pid) if first_state and second_state else False
        # each part of the pass condition by name, so a failure says which one is false (cidiag, 7 November 2026)
        parts = {"first_state": first_state is not None, "restart_200": restarted[0] == 200,
                 "second_state": second_state is not None, "pids_ok": pids_ok,
                 "new_start": (first_state is not None and second_state is not None
                               and second_state["started"] != first_state["started"]),
                 "quit_200": quit_answer[0] == 200,
                 "reopen_line": quit_answer[0] == 200 and quit_answer[1].get("reopen") == "To open it again, run run.sh.",
                 "exit_0": code == 0, "port_closed": bool(refused_port), "restarting_said": "Restarting." in said,
                 "two_running_lines": said.count("Idiograph is running at") == 2,
                 "closed_said": "Idiograph is closed." in said}
        real_ok = all(parts.values())
        check("84: a real server restarts, in the same process with a new start on the same pid, on Windows in a process "
              "of its own, then quits with the port closed",
              real_ok, "" if real_ok else
              f"real_ok parts: {parts}, pids {(first_state or {}).get('pid')} then {(second_state or {}).get('pid')} "
              f"(child {child.pid}), exit code {code}, calls that failed: {errors or 'none'}\n{watch.says(said)}")
    finally:
        (server_mod.CONFIG_PATH, server_mod.ROOT_OVERRIDE, server_mod.STATE_MEMORY, server_mod.EXEC, server_mod.ARGV,
         server_mod.RELAUNCH, server_mod.FROZEN, server_mod.restart_blocked) = kept[:8]
        server_mod.PATHS.clear()
        server_mod.PATHS.update(kept[8])
        locks.WAIT = kept[9]
        server_mod.SERVER_STATE.clear()
        server_mod.SERVER_STATE.update(kept[10])
        if kept[11] is None:
            os.environ.pop(mcp_server.DESKTOP_ENV, None)
        else:
            os.environ[mcp_server.DESKTOP_ENV] = kept[11]
        server_mod.SPAWN = kept[12]

    # ── K. the page: Settings' two steps, the restart line's button and the old server's line
    check("84: the page asks /api/server at boot, and only a server with the route gets the buttons",
          "SERVER.info = await api('/api/server');" in fn(app, "serverBoot") and "SERVER.old = needsRestart(err);" in fn(app, "serverBoot")
          and "if (SERVER.info) restartButtons();" in fn(app, "serverBoot") and "serverBoot();" in app.split("function boot(", 1)[1]
          and "$('server-old').hidden = !SERVER.old;" in fn(app, "drawServerOps"))
    op = fn(app, "serverOp")
    check("84: Restart and Quit save what is pending first, Restart shows Restarting and waits, Quit says it is closed",
          op.index("await savePending()") < op.index("await api('/api/server', { op })")
          and "serverGone(t('shell.server.closed', { app: APP_NAME }), data.reopen || '')" in op
          and "serverGone(t('shell.server.restarting'), '');" in op
          and "await serverBack(data.started" in op and "say(cannot, 9000); return;" in op
          # each app's own pending work, Idiograph's in its own hook since the fifth build (23 October 2026)
          and "own.savePending && !(await own.savePending())" in fn(app, "savePending")
          and "await commit(current(), false);" in fn(app, "distilSavePending") and "await thFlush();" in fn(app, "distilSavePending")
          and "keepNote(true)" in fn(app, "distilSavePending"))
    back = fn(app, "serverBack")
    check("84: the page reloads itself once the server answers from a new start",
          "data.started !== started) { location.reload(); return; }" in back and "fetch('/api/server'" in back)
    buttons = fn(app, "restartButtons")
    check("84: the restart line gains a Restart wherever it shows, watched once, one button to a line",
          "text.nodeValue.includes(RESTART_LINE)" in buttons and "new MutationObserver(" in buttons
          and "button.textContent = t('shell.server.restart_button');" in buttons and "c.classList.contains(RESTART_NOW)" in buttons
          and "if (SERVER.watch" in buttons and "serverOp('restart');" in app.split("closest(`.${RESTART_NOW}`)", 1)[1][:200])
    check("84: Add opens the card from /api/mcp and writes with add, an old server saying to restart",
          "api('/api/mcp', { ...projectBody(), op: 'show' })" in fn(app, "mcpShow")
          and "api('/api/mcp', { ...projectBody(), op: 'add' })" in fn(app, "mcpAdd")
          and "needsRestart(err) ? RESTART_LINE : err.message" in fn(app, "mcpAdd") and "drawMcp();" in fn(app, "drawAgents"))
