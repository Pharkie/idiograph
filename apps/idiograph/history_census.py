#!/usr/bin/env python3
"""Every revision of every board of a project, read only: keys and hashes, never words (historybuild, 16 November
2026). Run before and after History moves out of the board files (see `board_history`), on a copy, to prove nothing
was lost: each board file of each participant's `Working/` (PETs of every timepoint, LPETs) and the GETs and LGETs at
the root, each board by its id with each revision's id, time, a hash of its name, whether it was automatic, its kind,
a hash of its slots and its state's SHA-256, read from the chunks beside the file or from inside it alike.

    history_census.py <project folder> [--json out.json]

Prints the totals by file, and with --json writes the whole census. Two censuses are compared with `same`."""
from __future__ import annotations

import json
import sys
from pathlib import Path

BOARD_FILE = (".themes.json", ".lpets.json")
ROOT_FILES = ("idiograph-gets.json", "idiograph-lgets.json")


def board_files(root: Path) -> list[Path]:
    """The project's board files: every participant's in `Working/`, and the root's, `_Archive` and hidden folders
    left out."""
    root = Path(root)
    out = [root / n for n in ROOT_FILES if (root / n).is_file()]
    for path in sorted(root.rglob("Working/*.json")):
        rel = path.relative_to(root).parts
        if any(p.startswith(".") or p == "_Archive" for p in rel):
            continue
        name = path.name
        if name.endswith(BOARD_FILE) or (".themes-t" in name and name.endswith(".json")):
            out.append(path)
    return out


def census(root: Path) -> dict:
    """`files` by their path from the root, each `{board id: [revision rows]}`, and `total`."""
    import board_history
    root = Path(root)
    files = {}
    for path in board_files(root):
        files[path.relative_to(root).as_posix()] = board_history.census(path)["boards"]
    total = sum(len(rows) for boards in files.values() for rows in boards.values())
    return {"files": files, "total": total}


def same(a: dict, b: dict) -> list[str]:
    """Where two censuses differ, by file and board, empty when they are the same revision for revision."""
    out = []
    for f in sorted(set(a["files"]) | set(b["files"])):
        x, y = a["files"].get(f) or {}, b["files"].get(f) or {}
        for board in sorted(set(x) | set(y)):
            if [list(r) for r in x.get(board) or []] != [list(r) for r in y.get(board) or []]:
                out.append(f"{f} {board}: {len(x.get(board) or [])} then {len(y.get(board) or [])}")
    return out


def main(argv: list[str]) -> int:
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
    import boot
    boot.setup()
    if not argv:
        print(__doc__)
        return 2
    held = census(Path(argv[0]))
    # each file by its number and kind alone, never a participant's folder, whose name may carry a second name
    for i, (f, boards) in enumerate(held["files"].items(), 1):
        kind = f.rsplit("/", 1)[-1].split(".", 1)[-1] if "/" in f else f
        print(f"{sum(len(r) for r in boards.values()):6d}  {len(boards):3d} boards  file {i} ({kind})")
    print(f"{held['total']:6d}  revisions in all")
    if "--json" in argv:
        Path(argv[argv.index("--json") + 1]).write_text(json.dumps(held, indent=1) + "\n", encoding="utf-8", newline="\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
