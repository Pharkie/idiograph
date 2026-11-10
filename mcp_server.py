#!/usr/bin/env python3
"""The family's MCP server from the root (22 October 2026, the family codebase's fourth build):
family/mcp_server.py, run as an MCP client's settings run this file, with its options, `--root`,
`--project`, `--demo`, `--config` and `--app` (see there and docs/agents.md).
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import boot  # noqa: E402

boot.shim(__name__, "mcp_server")
