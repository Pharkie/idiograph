#!/usr/bin/env python3
"""The executable of the Linux app's frozen server, as `build_linux.py` makes it (linux2, 8 November 2026).

The Linux counterpart of `mac_launcher.py` and `windows_launcher.py`, and the thinnest of the three: the
window (Tauri's, a later build) starts the server and owns the dialogs, so this file offers no Stop,
Restart and Open dialog of its own. It hands each way in to the Mac launcher's code, which is
platform-free (`serve`, `command_line`, `mcp_server`, `split_args`), so the three apps' servers behave the
same on every system.

    Idiograph [--port N] [--no-browser] [--root FOLDER] [--config FILE] [--verbose]
    Idiograph --serve [the same]       the server itself, in the foreground
    Idiograph cli <command>            the command line an AI agent works through, docs/agents.md
    Idiograph mcp [--project NAME | --root FOLDER]   the MCP server, for Claude Desktop

With no `cli` or `mcp` the server runs in the foreground, as `run.sh` runs it, whether or not `--serve`
is given. The folders it writes in come from `app_folders` (XDG on Linux).
"""
from __future__ import annotations

import sys
from pathlib import Path

# run from the source the app's modules are a folder up, and frozen they are in the bundle
if not getattr(sys, "frozen", False):
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
    sys.path.insert(0, str(Path(__file__).resolve().parent))
import boot  # noqa: E402  the family's folders on the path (boot.py), the bundle's own frozen

boot.setup()
import mac_launcher as base  # noqa: E402  the server, the command line and the MCP server, as on a Mac


def main(argv: list[str] | None = None) -> int:
    given = sys.argv[1:] if argv is None else argv
    if given[:1] == ["cli"]:
        return base.command_line(given[1:])
    if given[:1] == ["mcp"]:
        return base.mcp_server(given[1:])
    _serving, port, extra = base.split_args(given)
    return base.serve(port, extra)


if __name__ == "__main__":
    raise SystemExit(main())
