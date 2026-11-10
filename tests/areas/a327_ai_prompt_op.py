"""Area 327: the statements' AI prompt for agents (promptop, 4 November 2026, Adam's rule "one API, two clients").
Settings, AI features holds the prompt a suggestion goes out with, `ai_prompt` in his settings, and an agent had
no op for it. `settings` now reads it, `settings --ai-prompt-file` sets it from a text file and
`settings --ai-prompt-default` puts the default back, through `/api/settings` as the page's Save does, and the
MCP's `settings` and `settings_set` do the same. What is set is what the next suggestion's system prompt is made
from, read back through the routes the page reads. An empty file, a file that cannot be read and a missing
request are refused with nothing written, and a dry run writes nothing.

The projects and the prompts are invented: a prompt about a dog on the stairs."""
from __future__ import annotations

import json
from pathlib import Path

from . import support
from .a316_code_list import make_project
from .support import check


def test_ai_prompt_op(scratch: Path):
    print("\n327. The statements' AI prompt for agents: settings reads it, sets it from a file, puts the default back, "
          "the next suggestion's prompt carrying it, refusals and dry runs writing nothing, MCP the same (4 November)")
    import cli
    import idiograph_routes as routes
    import mcp_server
    import server as server_mod
    import statement_prompts as prompts

    base = scratch / "ai-prompt-327"
    root = base / "Dogs"
    make_project(root, "ta")
    config_file = base / "config.json"
    config_file.write_text(json.dumps({"projects": [{"root": str(root)}], "interviewer": "Adam", "corpus": "",
                                       "gravity_reference": "", "corpus_exclude": []}), encoding="utf-8")
    kept = (server_mod.CONFIG_PATH, server_mod.ROOT_OVERRIDE, server_mod.STATE_MEMORY)
    mine = "You help with the dog on the stairs. {research_question}\n\nHis guidance:\n{guidance}\n\n{examples}\n"
    note = ("--note", "Put my own prompt in")
    wrote = base / "mine.txt"
    wrote.write_text(mine, encoding="utf-8")
    empty = base / "empty.txt"
    empty.write_text("  \n\n", encoding="utf-8")
    bytes_file = base / "bytes.txt"
    bytes_file.write_bytes(b"\xff\xfe\x00 not text")

    def run(*args):
        return cli.run(["--config", str(config_file), "--root", str(root), *args])

    def run_json(*args):
        code, out, err = run("--json", *args)
        got = support.plain(json.loads(out)) if out.strip() else {}
        return code, (got if code == 0 else {}), err + (got.get("error", "") if code != 0 else "")

    def page(fn, body):
        """The page's call on this settings file."""
        server_mod.CONFIG_PATH, server_mod.ROOT_OVERRIDE = config_file, str(root)
        server_mod.STATE_MEMORY = {"recent": []}
        try:
            return fn(body)
        finally:
            server_mod.CONFIG_PATH, server_mod.ROOT_OVERRIDE, server_mod.STATE_MEMORY = kept

    def saved() -> str:
        """The prompt as the page's settings read hands it."""
        return page(server_mod.api_settings, {"op": "read"})["config"].get("ai_prompt") or ""

    def suggestion_system() -> str:
        """The system prompt the next suggestion is made from, by the route's own template."""
        server_mod.CONFIG_PATH, server_mod.ROOT_OVERRIDE = config_file, str(root)
        try:
            template = server_mod.ai_route(server_mod.config())["template"]
        finally:
            server_mod.CONFIG_PATH, server_mod.ROOT_OVERRIDE = kept[0], kept[1]
        return prompts.system_prompt(["Dogs name the stairs"], [], template, "")

    def file_bytes() -> bytes:
        return config_file.read_bytes()

    default = page(routes.api_guidance, {})["prompt_default"]
    code, read, err = run_json("settings")
    check("327: settings reads the prompt, the default at first, its text in the JSON",
          code == 0 and read.get("ai_prompt_is_default") is True and read.get("ai_prompt") == default
          and saved() in ("", default), err + json.dumps(read)[:200])

    before = file_bytes()
    code, dry, err = run_json("settings", "--ai-prompt-file", str(wrote), *note, "--dry-run")
    check("327: a dry run says the prompt would be his own and writes nothing",
          code == 0 and dry.get("dry_run") is True and dry.get("ai_prompt_is_default") is False
          and file_bytes() == before and "dog on the stairs" not in suggestion_system(), err + json.dumps(dry)[:200])

    code, done, err = run_json("settings", "--ai-prompt-file", str(wrote), *note)
    system = suggestion_system()
    code2, read2, _ = run_json("settings")
    check("327: set from a file, the page's settings read it back and the next suggestion's prompt carries it",
          code == 0 and done.get("ai_prompt_is_default") is False and saved() == mine
          and "You help with the dog on the stairs." in system and "Dogs name the stairs" in system
          and read2.get("ai_prompt") == mine and read2.get("ai_prompt_is_default") is False, err + system[:200])

    after = file_bytes()
    refused = {
        "no request": run("settings", "--ai-prompt-default"),
        "empty file": run("settings", "--ai-prompt-file", str(empty), *note),
        "empty file, dry run": run("settings", "--ai-prompt-file", str(empty), *note, "--dry-run"),
        "missing file": run("settings", "--ai-prompt-file", str(base / "nowhere.txt"), *note),
        "not text": run("settings", "--ai-prompt-file", str(bytes_file), *note),
        "both": run("settings", "--ai-prompt-file", str(wrote), "--ai-prompt-default", *note),
    }
    check("327: no request, an empty file, a missing file, one that is not text and both options are refused, nothing written",
          all(code != 0 for code, _, _ in refused.values()) and file_bytes() == after and saved() == mine,
          json.dumps({k: v[2][:80] for k, v in refused.items()}))

    code, back, err = run_json("settings", "--ai-prompt-default", *note)
    check("327: the default put back, as Settings' own button puts it, and the next prompt is the default's",
          code == 0 and back.get("ai_prompt_is_default") is True and saved() == default
          and "dog on the stairs" not in suggestion_system(), err + json.dumps(back)[:200])

    # the MCP's tools, the same
    mcp = mcp_server.Server(root=str(root), config=str(config_file))
    said = lambda res: support.plain(res.get("structuredContent") or {})
    r0 = mcp.call(mcp.by_name["settings"], {})
    held = file_bytes()
    r1 = mcp.call(mcp.by_name["settings_set"], {"ai_prompt": mine, "dry_run": True, "request": "Look first"})
    r2 = mcp.call(mcp.by_name["settings_set"], {"ai_prompt": mine})
    r3 = mcp.call(mcp.by_name["settings_set"], {"ai_prompt": "   ", "request": "Empty"})
    r4 = mcp.call(mcp.by_name["settings_set"], {"request": "Nothing to set"})
    r5 = mcp.call(mcp.by_name["settings_set"], {"ai_prompt": mine, "ai_prompt_default": True, "request": "Both"})
    check("327: MCP reads the prompt and its set refuses no request, an empty text, nothing given and both, writing nothing",
          not r0["isError"] and said(r0).get("ai_prompt_is_default") is True
          and not r1["isError"] and said(r1).get("dry_run") is True
          and r2["isError"] and r3["isError"] and r4["isError"] and r5["isError"] and file_bytes() == held,
          json.dumps([r0.get("isError"), r1.get("isError"), r2, r3, r4, r5])[:500])

    r6 = mcp.call(mcp.by_name["settings_set"], {"ai_prompt": mine, "request": "Put my prompt in"})
    own = saved() == mine and "You help with the dog on the stairs." in suggestion_system()
    r7 = mcp.call(mcp.by_name["settings"], {})
    r8 = mcp.call(mcp.by_name["settings_set"], {"ai_prompt_default": True, "request": "Back to the default"})
    check("327: MCP sets the text, the next suggestion's prompt carries it, and the default goes back",
          not r6["isError"] and own and said(r7).get("ai_prompt") == mine and said(r7).get("ai_prompt_is_default") is False
          and not r8["isError"] and saved() == default and "dog on the stairs" not in suggestion_system(),
          json.dumps([r6, r8])[:400])

    # Your name still sets as it did, beside the prompt, in one call
    code, both, err = run_json("settings", "--your-name", "Ada Lark", "--ai-prompt-file", str(wrote), *note)
    check("327: Your name and the prompt set together, each as it is set alone",
          code == 0 and both.get("your_name") == "Ada Lark" and both.get("ai_prompt_is_default") is False
          and saved() == mine, err + json.dumps(both)[:200])
