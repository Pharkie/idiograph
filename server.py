#!/usr/bin/env python3
"""The family's server from the root (22 October 2026, the family codebase's fourth build): family/server.py,
run as run.sh, run.command, run.bat and Restart run this file, with its options, `--app`, `--port`,
`--no-browser`, `--root` and `--config` (see there). Every app's routes register as it starts, Idiograph's by
default and Sift's and Trace's with `--app`, as before the split.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import boot  # noqa: E402

boot.shim(__name__, "server")
