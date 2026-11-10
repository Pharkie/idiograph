"""Area 246: Using your own AI agent (21 October 2026). The box at the end of each app's AI features page names
this install's own command line, MCP server and guide: the Mac app's server with cli or mcp, the Windows app's
console twin, a run from source's command beside the code and the venv's python running mcp_server.py, each app
its own, and the route that gives the words."""
from __future__ import annotations

from .support import check


def test_agent_start():
    print("\n246. Using your own AI agent: each install's own command line, MCP server and guide in the box, each app its own")
    import server as server_mod

    mac = "/Applications/Sift.app/Contents/Resources/server/Sift"
    got = server_mod.agent_commands("sift", frozen=True, executable=mac,
                                    here="/Applications/Sift.app/Contents/Resources/server/_internal", system="darwin")
    check("246: the Mac app's Sift runs its own server with cli and with mcp, and its own guide",
          got["cli"] == [mac, "cli"] and got["mcp"] == [mac, "mcp"]
          and got["guide"].endswith("/docs/agents-sift.md") and got["uri"] == "sift://guide", str(got))

    win = r"C:\Users\Wren\AppData\Local\Trace\server\Trace.exe"
    got = server_mod.agent_commands("trace", frozen=True, executable=win,
                                    here=r"C:\Users\Wren\AppData\Local\Trace\server\_internal", system="win32")
    console = r"C:\Users\Wren\AppData\Local\Trace\server\Trace-console.exe"
    check("246: the Windows app's Trace runs its console twin, never the windowed one, and its guide in Windows' shape",
          got["cli"] == [console, "cli"] and got["mcp"] == [console, "mcp"]
          and got["guide"] == r"C:\Users\Wren\AppData\Local\Trace\server\_internal\docs\agents-trace.md", str(got))

    src = server_mod.HERE
    got = server_mod.agent_commands("sift", frozen=False, executable="/usr/bin/python3", here=src, system="darwin")
    check("246: from source Sift's command is the sift beside the code, its MCP server mcp_server.py with --app sift",
          got["cli"] == [str(src / "sift")] and got["mcp"][-3:] == [str(src / "mcp_server.py"), "--app", "sift"], str(got))
    got = server_mod.agent_commands("idiograph", frozen=False, executable="/usr/bin/python3", here=src, system="darwin")
    check("246: from source Idiograph's MCP server takes no --app, and its command is idiograph",
          got["cli"] == [str(src / "idiograph")] and got["mcp"][-1] == str(src / "mcp_server.py"), str(got))

    text = server_mod.agent_start(server_mod.agent_commands("idiograph", frozen=True, executable="/Applications/Idio graph.app/x/Idiograph",
                                                            here="/Applications/Idio graph.app/x", system="darwin"))
    check("246: the words quote a path with a space, add the server for Claude Code at user scope, ask for a dry run, "
          "and Idiograph's name the project tick",
          "'/Applications/Idio graph.app/x/Idiograph' cli cases" in text
          and "claude mcp add --scope user idiograph -- '/Applications/Idio graph.app/x/Idiograph' mcp" in text
          and "dry run first" in text and "Allow AI agents to read this project" in text, text)
    sift = server_mod.agent_start(server_mod.agent_commands("sift", frozen=True, executable=mac, here="/x", system="darwin"))
    check("246: Sift's words name its own guide and no project tick", "sift://guide" in sift and "Allow AI agents" not in sift, sift)

    answer = server_mod.api_agent_start({})
    check("246: the route answers the words with the paths they hold, the route every app answers",
          answer["text"] and answer["cli"] and answer["mcp"] and server_mod.route_owner(server_mod.AGENT_START_PATH) == "shared",
          str(sorted(answer)))
