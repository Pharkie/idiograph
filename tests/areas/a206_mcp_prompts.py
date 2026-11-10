from __future__ import annotations

import json
import shutil

from . import support
from .support import DEMO_QUESTION, check


def test_mcp_prompts(scratch):
    print("\n206. The MCP server's prompt and resources for a stranger's agent: start, the guide whole and by "
          "section, the file schemas and the project's AGENTS.md, the tick refusing the prompt and the project's "
          "resource when off (Adam, 19 October)")
    import mcp_server
    import server as server_mod

    pristine = support.DEMO_PRISTINE

    def make_root(at, allowed):
        """The demo's invented cases in a project of their own, a guide of the project's own beside them."""
        shutil.rmtree(at, ignore_errors=True)
        for name in ("Juno", "Rowan", "Mabel"):
            (at / name / "Working").mkdir(parents=True)
            shutil.copy2(pristine / f"{name} - EN & ES.xlsx", at / name / f"{name} - EN & ES.xlsx")
            for side in (pristine / "Working").glob(f"{name} - *"):
                shutil.copy2(side, at / name / "Working" / side.name)
        held = {"name": "Kennels, a prompt project", "research_question": DEMO_QUESTION}
        if allowed:
            held["agents"] = {"allowed": True, "at": "2026-10-19T21:00:00+01:00"}
        (at / server_mod.PROJECT_FILE).write_text(json.dumps(held), encoding="utf-8")
        (at / "AGENTS.md").write_text("# The kennels' own guide\n\nRead the walks first.\n", encoding="utf-8")
        return at

    def files(at):
        return {p.relative_to(at).as_posix(): p.read_bytes() for p in sorted(at.rglob("*")) if p.is_file()}

    kept = (server_mod.CONFIG_PATH, server_mod.ROOT_OVERRIDE, server_mod.STATE_MEMORY)
    try:
        opened = make_root(scratch / "prompts-open", True)
        closed = make_root(scratch / "prompts-closed", False)
        config = scratch / "prompts-config.json"
        config.write_text(json.dumps({"root": str(opened), "interviewer": "Researcher"}), encoding="utf-8")
        before = files(opened)

        def server(root):
            srv = mcp_server.Server(str(root), config=str(config))
            srv.receive(json.dumps({"jsonrpc": "2.0", "id": 0, "method": "initialize",
                                    "params": {"protocolVersion": "2025-06-18", "clientInfo": {"name": "claude-code"}}}))
            return srv

        def rpc(srv, method, params=None):
            return srv.receive(json.dumps({"jsonrpc": "2.0", "id": 1, "method": method, "params": params or {}}))

        srv = server(opened)
        hello = mcp_server.Server(str(opened), config=str(config)).receive(json.dumps(
            {"jsonrpc": "2.0", "id": 0, "method": "initialize", "params": {"protocolVersion": "2025-06-18"}}))
        caps = hello["result"]["capabilities"]
        check("206: initialize offers prompts and resources beside the tools",
              "prompts" in caps and "resources" in caps and "tools" in caps, str(caps))

        # prompts/list and prompts/get
        listed = rpc(srv, "prompts/list")["result"]["prompts"]
        check("206: prompts/list offers start, Start working with Idiograph, with his first request optional",
              [p["name"] for p in listed] == ["start"] and listed[0]["title"] == "Start working with Idiograph"
              and listed[0]["arguments"] == [{"name": "request", "description": listed[0]["arguments"][0]["description"],
                                              "required": False}], str(listed)[:300])
        got = rpc(srv, "prompts/get", {"name": "start", "arguments": {"request": "Show me Rowan's PETs"}})["result"]
        text = got["messages"][0]["content"]["text"]
        check("206: prompts/get start hands a user message with the privacy line, the project as cases gives it, "
              "dry runs, the resources and his first request",
              got["messages"][0]["role"] == "user" and got["messages"][0]["content"]["type"] == "text"
              and "goes to your model's provider" in text and "Kennels, a prompt project" in text
              and DEMO_QUESTION in text and "Rowan" in text and "dry_run true" in text
              and "idiograph://guide" in text and "idiograph://project/AGENTS.md" in text
              and text.rstrip().endswith("His first request: Show me Rowan's PETs"), text[:400])
        bare = rpc(srv, "prompts/get", {"name": "start"})["result"]["messages"][0]["content"]["text"]
        check("206: without a request the prompt carries none", "His first request" not in bare and "Kennels" in bare)
        unknown = rpc(srv, "prompts/get", {"name": "finish"})
        check("206: an unknown prompt is refused with the error for invalid params",
              unknown.get("error", {}).get("code") == mcp_server.INVALID_PARAMS, str(unknown))

        # resources/list and resources/read
        res = {r["uri"]: r for r in rpc(srv, "resources/list")["result"]["resources"]}
        guide = support.source("docs/agents.md").read_text(encoding="utf-8")
        schemas = sorted(p.name for p in support.source("docs/schemas").glob("*.json"))
        check("206: resources/list gives the guide whole, each of its sections, every schema and the project's AGENTS.md",
              "idiograph://guide" in res and "idiograph://guide/writing" in res and "idiograph://guide/the-conventions" in res
              and len([u for u in res if u.startswith("idiograph://guide/")]) == guide.count("\n## ")
              and all(f"idiograph://schemas/{n}" in res for n in schemas) and "idiograph://project/AGENTS.md" in res,
              str(sorted(res))[:400])
        read = lambda uri: rpc(srv, "resources/read", {"uri": uri})
        whole = read("idiograph://guide")["result"]["contents"][0]
        part = read("idiograph://guide/the-method")["result"]["contents"][0]["text"]
        schema = read(f"idiograph://schemas/{schemas[0]}")["result"]["contents"][0]
        own = read("idiograph://project/AGENTS.md")["result"]["contents"][0]["text"]
        check("206: resources/read gives the guide whole, a section alone, a schema as JSON and the project's own guide",
              whole["text"] == guide and whole["mimeType"] == "text/markdown"
              and part.startswith("## The method\n") and "Never use causal language." in part and "## The conventions" not in part
              and isinstance(support.plain(json.loads(schema["text"])), dict) and schema["mimeType"] == "application/schema+json"
              and own.startswith("# The kennels' own guide"), part[:200])
        missing = read("idiograph://schemas/../agents.md")
        check("206: a resource it does not hold is refused with the protocol's error, never a file beside it",
              missing.get("error", {}).get("code") == mcp_server.NOT_FOUND
              and read("idiograph://elsewhere").get("error", {}).get("code") == mcp_server.NOT_FOUND, str(missing))
        check("206: the prompt and the resources write nothing", files(opened) == before)

        # the tick off: the prompt and the project's resource answer with the line that says where to tick it
        shut = server(closed)
        said = rpc(shut, "prompts/get", {"name": "start"})["result"]["messages"][0]["content"]["text"]
        listed_shut = {r["uri"] for r in rpc(shut, "resources/list")["result"]["resources"]}
        own_shut = rpc(shut, "resources/read", {"uri": "idiograph://project/AGENTS.md"})["result"]["contents"][0]["text"]
        check("206: with the tick off the prompt is the line that says where to tick it, and nothing of the project",
              "Allow AI agents to read this project" in said and "Kennels" not in said and "Rowan" not in said, said)
        check("206: with the tick off the project's AGENTS.md answers with the same line, the guide still read",
              "idiograph://project/AGENTS.md" in listed_shut and "Allow AI agents to read this project" in own_shut
              and "kennels' own guide" not in own_shut
              and rpc(shut, "resources/read", {"uri": "idiograph://guide/the-method"})["result"]["contents"][0]["text"]
              .startswith("## The method"), own_shut)

        # never longer: the instructions stay within what they were on 19 October, and what a stranger's
        # agent must not miss stands within the first 2,000 characters, all Claude Code keeps
        told = mcp_server.instructions()
        first = told[:mcp_server.CORE_LIMIT]
        check("206: the instructions stay no longer than 8,288 characters, the privacy line, cases first, dry runs, "
              "setting aside only when he asks, add_notes and the resources within their first 2,000",
              len(told) <= 8288 and first.startswith("Read this first.") and "Call cases first" in first
              and "dry_run" in first and "set one aside only when he asks" in first and "add_notes" in first
              and "idiograph://guide" in first and "## The conventions" in told, str(len(told)))

        # add_notes: one note added through the API, every note the passage holds kept, the CLI and MCP alike
        import cli
        juno = opened / "Juno" / "Juno - EN & ES.xlsx"
        rowan = opened / "Rowan" / "Rowan - EN & ES.xlsx"
        call = lambda name, args: rpc(srv, "tools/call", {"name": name, "arguments": args})["result"]
        shown = support.plain(call("turn_show", {"case": "Rowan", "sheet": "Initial", "row": 11})["structuredContent"])
        turn = (shown.get("turns") or [shown])[0]
        held = list(turn.get("notes") or [])
        dry = call("turn_write", {"case": "Rowan", "sheet": "Initial", "row": 11, "add_notes": ["Check this on the walk home."],
                                  "request": "Add a note", "dry_run": True})
        after_dry = rowan.read_bytes()
        check("206: turn_write add_notes on a dry run says it adds one and keeps the rest, and writes nothing",
              held and not dry["isError"] and "add 1 exploratory note" in support.unfenced(dry["content"][0]["text"])
              and f"keeping the {cli.plural(len(held), 'note')} there" in support.unfenced(dry["content"][0]["text"])
              and after_dry == before["Rowan/Rowan - EN & ES.xlsx"], support.unfenced(dry["content"][0]["text"])[:300])
        wrote = call("turn_write", {"case": "Rowan", "sheet": "Initial", "row": 11, "add_notes": ["Check this on the walk home."],
                                    "request": "Add a note"})
        again = support.plain(call("turn_show", {"case": "Rowan", "sheet": "Initial", "row": 11})["structuredContent"])
        notes_now = (again.get("turns") or [again])[0].get("notes")
        check("206: turn_write add_notes adds the note after those there, every one of them kept",
              not wrote["isError"] and notes_now == held + ["Check this on the walk home."], str(notes_now))
        same = call("turn_write", {"case": "Rowan", "sheet": "Initial", "row": 11, "add_notes": ["Check this on the walk home."],
                                   "request": "Add a note"})
        both = call("turn_write", {"case": "Rowan", "sheet": "Initial", "row": 11, "add_notes": ["x"], "notes": ["y"],
                                   "request": "Add a note"})
        check("206: a note the passage holds already is not added twice, and notes with add_notes is refused",
              not same["isError"] and "Nothing to write" in support.unfenced(same["content"][0]["text"])
              and both["isError"] and "add_notes" in support.unfenced(both["content"][0]["text"]), support.unfenced(both["content"][0]["text"])[:200])
        spec = scratch / "prompts-add.json"
        spec.write_text(json.dumps({"add_notes": ["A second look at the spaniel."]}), encoding="utf-8")
        code, out, err = cli.run(["--root", str(opened), "--config", str(config), "turn", "write", "Rowan", "Initial", "11",
                                  "--from", str(spec), "--note", "Add another", "--tool", "Claude Code"])
        code2, out2, _ = cli.run(["--root", str(opened), "--config", str(config), "--json", "turn", "show", "Rowan",
                                  "Initial", "11"])
        shown2 = support.plain(json.loads(out2))
        notes_cli = (shown2.get("turns") or [shown2])[0].get("notes")
        check("206: the command line takes add_notes from its file the same way",
              code == 0 and notes_cli == held + ["Check this on the walk home.", "A second look at the spaniel."]
              and juno.exists(), (out + err)[:300] + str(notes_cli))
    finally:
        server_mod.CONFIG_PATH, server_mod.ROOT_OVERRIDE, server_mod.STATE_MEMORY = kept
