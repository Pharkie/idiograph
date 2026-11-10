#!/usr/bin/env python3
"""Remake a patch made before the family's files moved, so it applies after (22 October 2026, the
family codebase's first build).

    python3 packaging/repath.py <patch> --from <sha>              # the moves since <sha>, to HEAD
    python3 packaging/repath.py <patch> --from <sha> --to main --out <new patch>
    python3 packaging/repath.py <patch> --move old.py=family/old.py

A patch names each file by its path when it was made. The moves are read from git, every file renamed
between `--from` (the commit the patch was made against) and `--to` (HEAD unless given), with any
`--move old=new` added by hand. Each path the patch names is rewritten to where the file is now: the
`diff --git` line, the `---` and `+++` lines and a rename's or copy's own lines. The hunks are left as
they are, so `git apply --3way` takes care of lines that changed in a moved file.

A file split into several (app.js into shell.js and distil.js, the suite's alias table in
tests/areas/support.py) cannot be repathed, since its hunks belong to either part: such a file is
named in one line and its part of the patch is kept under the old path, to be remade by hand. The new
patch goes to `--out`, or replaces nothing and is printed when `--out` is left out. The standard
library only.
"""
from __future__ import annotations

import argparse
import ast
import re
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
TOOL = HERE.parent
SUPPORT = TOOL / "tests" / "areas" / "support.py"
# the lines of a patch that name a file, and the part of each that is the path
PATH_LINES = (
    (re.compile(r"^diff --git a/(\S+) b/(\S+)$"), "diff --git a/{0} b/{1}"),
    (re.compile(r"^--- a/(.+)$"), "--- a/{0}"),
    (re.compile(r"^\+\+\+ b/(.+)$"), "+++ b/{0}"),
    (re.compile(r"^rename from (.+)$"), "rename from {0}"),
    (re.compile(r"^rename to (.+)$"), "rename to {0}"),
    (re.compile(r"^copy from (.+)$"), "copy from {0}"),
    (re.compile(r"^copy to (.+)$"), "copy to {0}"),
)


def git_moves(base: str, to: str = "HEAD", tool: Path = TOOL) -> dict[str, str]:
    """Each file git finds renamed from `base` to `to`, old path to new."""
    out = subprocess.run(["git", "-c", "core.quotepath=off", "-C", str(tool), "diff", "-M", "--name-status",
                          "--diff-filter=R", base, to], capture_output=True, text=True, encoding="utf-8")
    if out.returncode != 0:
        raise SystemExit(f"git could not compare {base} with {to}: {out.stderr.strip()}")
    moves = {}
    for line in out.stdout.splitlines():
        parts = line.split("\t")
        if len(parts) == 3 and parts[0].startswith("R"):
            moves[parts[1]] = parts[2]
    return moves


def splits(support: Path = SUPPORT) -> dict[str, tuple[str, ...]]:
    """The suite's alias table's paths that became several files, read from its source, not imported."""
    try:
        tree = ast.parse(support.read_text(encoding="utf-8"))
    except (OSError, SyntaxError):
        return {}
    for node in tree.body:
        target = node.target if isinstance(node, ast.AnnAssign) else (node.targets[0] if isinstance(node, ast.Assign) else None)
        if isinstance(target, ast.Name) and target.id == "ALIASES" and node.value is not None:
            table = ast.literal_eval(node.value)
            return {old: tuple(new) for old, new in table.items() if len(new) > 1}
    return {}


def repath(text: str, moves: dict[str, str], split: dict[str, tuple[str, ...]] | None = None) -> tuple[str, list[str], list[str]]:
    """The patch with each moved path rewritten, the paths it moved and the split files it left as they were."""
    split = split or {}
    moved, kept = [], []
    out = []
    for line in text.splitlines(keepends=True):
        bare = line.rstrip("\r\n")
        ending = line[len(bare):]
        for rx, shape in PATH_LINES:
            m = rx.match(bare)
            if not m:
                continue
            paths = list(m.groups())
            for i, path in enumerate(paths):
                if path in split:
                    kept.append(path)
                elif path in moves:
                    moved.append(path)
                    paths[i] = moves[path]
            bare = shape.format(*paths)
            break
        out.append(bare + ending)
    return "".join(out), sorted(set(moved)), sorted(set(kept))


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Rewrite a patch's paths for the files that moved since it was made.")
    ap.add_argument("patch", help="the patch to remake")
    ap.add_argument("--from", dest="base", help="the commit the patch was made against")
    ap.add_argument("--to", default="HEAD", help="where the files are now, HEAD by default")
    ap.add_argument("--move", action="append", default=[], help="old=new, a move added by hand, more than once")
    ap.add_argument("--out", help="the new patch's file, printed when left out")
    args = ap.parse_args(argv)
    moves = git_moves(args.base, args.to) if args.base else {}
    for pair in args.move:
        old, sep, new = pair.partition("=")
        if not sep or not old or not new:
            ap.error(f"--move takes old=new, not {pair}")
        moves[old] = new
    text = Path(args.patch).read_text(encoding="utf-8")
    new, moved, kept = repath(text, moves, splits())
    if args.out:
        Path(args.out).write_text(new, encoding="utf-8")
    else:
        sys.stdout.write(new)
    said = sys.stderr if not args.out else sys.stdout
    print(f"Repathed {len(moved)} file{'s' if len(moved) != 1 else ''}: {', '.join(moved) or 'none'}.", file=said)
    if kept:
        print(f"Left under the old path, split since, remake by hand: {', '.join(kept)}.", file=said)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
