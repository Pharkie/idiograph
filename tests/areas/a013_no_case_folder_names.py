from __future__ import annotations

import re

from .support import TOOL, check


def test_no_case_folder_names():
    print("\n12. No case folder name anywhere in the tool")
    # Case folders are `P<n> - <Pseudonym>-<second name>`, and the second name must never reach
    # git. Configured and test paths are globs on the pseudonym, and this sweep is what keeps it
    # that way. The pattern below does not match its own source, so the scan stays honest.
    pattern = re.compile(r"P\d - [A-Z][a-z]+-[A-Z][a-z]+")
    # `.env` holds a key and is never read here. `state.json` is the recent list the app writes as
    # Adam opens cases, and it is gitignored, so a case folder name in it never reaches git.
    skip_names = {".env", "state.json"}
    skip_suffixes = {".xlsx", ".csv", ".png", ".pyc"}
    # `build/` and `dist/` are what packaging/build_mac.py makes, the build venv among them, and are
    # gitignored as well
    skip_tops = {"build", "dist"}
    scanned, hits = 0, []
    for path in sorted(TOOL.rglob("*")):
        if (not path.is_file() or "__pycache__" in path.parts or path.relative_to(TOOL).parts[0] in skip_tops
                or path.name in skip_names or path.suffix in skip_suffixes):
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            continue
        scanned += 1
        for i, line in enumerate(text.splitlines(), 1):
            if pattern.search(line):
                hits.append(f"{path.relative_to(TOOL)}:{i}")
    check("no case folder name in any file under the tool", not hits,
          f"{scanned} text files scanned" if not hits else f"found in {', '.join(hits)}")
    # The probe is assembled at run time. Spelling a matching name out here would trip the sweep
    # above, which is the point: nothing that looks like a case folder survives in this folder.
    probe = "P9 - {}-{}".format("Alpha", "Beta")
    check("the sweep would catch one if it appeared", bool(pattern.search(probe)),
          "pattern checked against an invented pair")
