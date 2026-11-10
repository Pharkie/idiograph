#!/usr/bin/env python3
"""The family's command line from the root (22 October 2026, the family codebase's fourth build):
family/cli.py, run as `./idiograph`, `./sift`, `./trace` and their .bat files run this file, with the
command's words (see there and docs/agents.md).
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import boot  # noqa: E402

boot.shim(__name__, "cli")
