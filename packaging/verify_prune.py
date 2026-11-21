#!/usr/bin/env python3
"""Take the build trees and old app copies out of `.verify/` (diskhygiene, 20 November 2026).

Builders' output folders `.verify/wip-*/` and the gate's copies of the app (`app-before-*`, `release-v*`) grew to
over 100 GB. This is a dry run unless `--commit` is given: it prints what it would delete and the space that frees,
and deletes nothing.

What goes, and only when it was last touched more than 3 days ago (`--days`):
  - in a `wip-*` folder: build trees (a folder named `target`, `node_modules`, `.venv`, `venv`,
    `.wip`, `*.app` or `idiograph-motion-*`, and a folder named `build` or `dist` only with a build tool's file
    beside it, `package.json`, `Cargo.toml` and the like, or a `profile*`, `chrome-profile*` or `user-data*` folder
    only with a browser's own files inside, `Local State` or `Default`), and any file over 20 MB that is
    not a `*.patch`;
  - `app-before-*` and `release-v*` at the top of `.verify/`: all but the newest three of each kind.
What stays: every `*.patch`, and every `*.md`, `*.msg`, `*.txt`, `*.log`, `*.json` and image that is under 20 MB (a
file over 20 MB goes whatever it is, a patch apart), anything touched in the last 3 days (the latest of its
modification, change and birth times, so a fresh copy made by `cp -p`, `ditto` or `tar` counts as new), `.verify/keep`,
and the gate's own files (history.log, the train logs, the participant words files and the rest), which this never
looks at. Run from a worktree, it prunes the main checkout's `.verify` (found through git's common folder).

    .venv/bin/python packaging/verify_prune.py                 # what it would free
    .venv/bin/python packaging/verify_prune.py --commit        # delete it
"""
from __future__ import annotations

import argparse
import fnmatch
import os
import shutil
import stat
import subprocess
import sys
import time
from pathlib import Path

BIG = 20 * 1024 * 1024
KEEP_NEWEST = 3
# folders no builder would keep anything in, taken wherever they stand
BUILD_DIRS = ("target", "node_modules", ".venv", "venv", ".wip", "*.app", "idiograph-motion-*")
# names a builder might also use for a folder of its own (a brief called build, a folder of profile shots): taken only
# with a sign of what they are, a build tool's file beside `build` and `dist`, a browser's own files inside a profile
MAYBE_DIRS = ("build", "dist", "profile", "profile-*", "profile*", "chrome-profile*", "user-data*")
BUILD_BESIDE = ("package.json", "Cargo.toml", "pyproject.toml", "setup.py", "tauri.conf.json", "Makefile",
                "build_mac.py", "build_windows.py", "CMakeLists.txt")
PROFILE_INSIDE = ("Local State", "Default", "First Run")


def is_build_tree(path: Path) -> bool:
    """Whether a folder with a name in BUILD_DIRS or MAYBE_DIRS is a build tree or a browser profile."""
    name = path.name
    if any(fnmatch.fnmatch(name, pattern) for pattern in BUILD_DIRS):
        return True
    if not any(fnmatch.fnmatch(name, pattern) for pattern in MAYBE_DIRS):
        return False
    if name in ("build", "dist"):
        return any((path.parent / marker).exists() for marker in BUILD_BESIDE)
    return any((path / marker).exists() for marker in PROFILE_INSIDE)


COPIES = ("app-before-*", "release-v*")


def touched(info: os.stat_result) -> float:
    """When a file was last touched: the latest of its modification, change and birth times."""
    return max(info.st_mtime, info.st_ctime, getattr(info, "st_birthtime", 0.0))


def main_verify() -> Path:
    """The `.verify` of the main checkout, through git's common folder, so a run from a worktree prunes the real one."""
    here = Path(__file__).resolve().parent.parent
    try:
        out = subprocess.run(["git", "-C", str(here), "rev-parse", "--path-format=absolute", "--git-common-dir"],
                             capture_output=True, text=True, encoding="utf-8", timeout=20).stdout.strip()
        if out:
            return Path(out).parent / ".verify"
    except (OSError, subprocess.SubprocessError):
        pass
    return here / ".verify"


def size_and_newest(path: Path) -> tuple[int, float]:
    """The bytes under `path` (a file or a folder, links not followed) and the newest modification time in it."""
    try:
        info = path.lstat()
    except OSError:
        return 0, 0.0
    total, newest = info.st_size, touched(info)
    if stat.S_ISDIR(info.st_mode):
        for root, dirs, files in os.walk(path, followlinks=False):
            for name in dirs + files:
                try:
                    item = os.lstat(os.path.join(root, name))
                except OSError:
                    continue
                total += item.st_size if stat.S_ISREG(item.st_mode) else 0
                newest = max(newest, touched(item))
    return total, newest


def plan(verify: Path, days: float = 3, now: float | None = None) -> list[tuple[str, Path, int]]:
    """Every thing to delete as (why, path, bytes), under the rules in the module's docstring."""
    cutoff = (time.time() if now is None else now) - days * 86400
    found: list[tuple[str, Path, int]] = []
    if not verify.is_dir():
        return found
    for wip in sorted(p for p in verify.glob("wip-*") if p.is_dir() and not p.is_symlink()):
        for root, dirs, files in os.walk(wip, followlinks=False):
            keep_walking = []
            for name in dirs:
                path = Path(root) / name
                if path.is_symlink():
                    continue
                if is_build_tree(path):
                    total, newest = size_and_newest(path)
                    if newest < cutoff:
                        found.append(("build tree", path, total))
                    continue
                keep_walking.append(name)
            dirs[:] = keep_walking
            for name in files:
                path = Path(root) / name
                try:
                    info = path.lstat()
                except OSError:
                    continue
                if (stat.S_ISREG(info.st_mode) and info.st_size > BIG and not name.endswith(".patch")
                        and touched(info) < cutoff):
                    found.append(("file over 20 MB", path, info.st_size))
    for pattern in COPIES:
        copies = sorted((p for p in verify.glob(pattern) if p.is_dir() and not p.is_symlink()),
                        key=lambda p: (size_and_newest(p)[1], p.name), reverse=True)
        for path in copies[KEEP_NEWEST:]:
            total, newest = size_and_newest(path)
            if newest < cutoff:
                found.append((f"older {pattern.rstrip('*')} copy", path, total))
    return found


def remove(path: Path) -> None:
    """Delete a file or folder, making a read-only folder (Rust's and Cargo's make them) writable first."""
    def fix(function, target, _info):
        if not os.path.islink(os.path.dirname(target)):
            os.chmod(os.path.dirname(target), 0o700)
        if not os.path.islink(target):
            os.chmod(target, 0o700)
        function(target)
    if path.is_dir() and not path.is_symlink():
        shutil.rmtree(path, onerror=fix)
    else:
        path.unlink(missing_ok=True)


def gigabytes(n: int) -> str:
    return f"{n / 1024 ** 3:.2f} GB" if n >= 1024 ** 3 else f"{n / 1024 ** 2:.1f} MB"


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Prune .verify/: a dry run unless --commit.")
    ap.add_argument("--commit", action="store_true", help="delete what the dry run lists")
    ap.add_argument("--days", type=float, default=3, help="leave anything touched in the last N days (default 3)")
    ap.add_argument("--verify-dir", default=str(main_verify()),
                    help="the folder to prune (default the main checkout's .verify)")
    args = ap.parse_args(argv)
    verify = Path(args.verify_dir)
    items = plan(verify, args.days)
    by_why: dict[str, list[int]] = {}
    for why, path, total in items:
        print(f"{gigabytes(total):>10}  {why}: {path.relative_to(verify)}")
        by_why.setdefault(why, []).append(total)
    print()
    for why, sizes in sorted(by_why.items()):
        print(f"  {why}: {len(sizes)} items, {gigabytes(sum(sizes))}")
    total = sum(t for _, _, t in items)
    if not args.commit:
        print(f"Dry run: would free {gigabytes(total)} in {len(items)} items. Nothing was deleted. Run with --commit to delete.")
        return 0
    for _, path, _ in items:
        try:
            remove(path)
        except OSError as exc:
            print(f"could not delete {path}: {exc}", file=sys.stderr)
    print(f"Deleted {len(items)} items, {gigabytes(total)}.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
