#!/usr/bin/env python3
"""Trace's own entry (22 October 2026, the family codebase's second build): the family's folders and
Trace's on the path (`boot.setup("trace")`), Trace's routes registered with the family's server, then the
server run as Trace. A frozen launcher imports this module by its name (`app_identity.entry`), so the build
starts from Trace's own code. From source it runs as `python3 apps/trace/trace_main.py`, with the
server's own options, `--port`, `--no-browser`, `--config` and the rest, and `--app trace` when none is
given.
"""
from __future__ import annotations

import sys
from pathlib import Path

# from source the family's root is two folders up, and frozen the bundle has put it on the path already
if not getattr(sys, "frozen", False):
    _root = str(Path(__file__).resolve().parents[2])
    if _root not in sys.path:
        sys.path.insert(0, _root)
import boot  # noqa: E402

boot.setup("trace")

import app_identity  # noqa: E402
import server  # noqa: E402
import trace_routes  # noqa: E402,F401  Trace's routes, registered with the server as it is imported


def main(argv: list[str] | None = None) -> None:
    """The family's server run as Trace, its options as given, `--app trace` put first when they name none."""
    args = list(sys.argv[1:] if argv is None else argv)
    if not app_identity.asked(args):
        args = ["--app", "trace", *args]
    sys.argv = [sys.argv[0], *args]
    server.main()


if __name__ == "__main__":
    main()
