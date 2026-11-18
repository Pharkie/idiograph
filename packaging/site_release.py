#!/usr/bin/env python3
"""The release's site step (sitecheck, 18 November 2026, Adam: "The What's new, screenshots, features and the manual
need updating on the website whenever we do a release... we need to remember to do that every time").

    .venv/bin/python packaging/site_release.py check v0.9.32
    .venv/bin/python packaging/site_release.py checklist v0.9.32   # the checklist alone

`check <tag>` runs before a release is published (the harness's `idiograph-release` calls it first). It exits 1 and
prints one plain line per problem when the committed site is not ready for the release:

- What's new, the manual, every nav and the Download page's version are what `packaging/site_whats_new.py` writes
  from `docs/` and `versions.json` (the fix is to run that script and commit the site);
- `versions.json`, the newest section of `docs/whats-new.md` and the Download page's version are all the tag's.

It then prints a short checklist, which never fails the check, for the two things only a person can judge:

- Features: this release's What's new lines, to check each has its row on `site/holding/features.html`, and that no
  row still reads Planned or Experimental that the app now has;
- Screenshots: for each clip in `packaging/motion/clips/`, whether a file whose screen it records changed between the
  previous release tag and this one. A clip names its screens in a `// Screens:` line in its header (comma-separated
  repo paths, a folder ending in `/`). `app.mjs`'s line is the screens every clip starts from (the page, the stylesheet,
  the shell): its changed files print on a line of their own, `SHARED CHANGED`, for a person to judge, and never make a
  clip `re-record`. A clip whose own files changed prints `re-record <clip>` with those files; none, `clips: no screen
  of their own changed`.

Reads the repository and writes nothing. It never deploys, tags or pushes.
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import re
import subprocess
import sys
from pathlib import Path

TOOL = Path(__file__).resolve().parent.parent
CLIPS = TOOL / "packaging" / "motion" / "clips"
SCREENS = re.compile(r"^// Screens:\s*(.+?)\s*$", re.M)
TAG = re.compile(r"(?:idiograph-)?v(\d+\.\d+\.\d+)")
PLAIN = re.compile(r"v(\d+\.\d+\.\d+)")


def whats_new_module():
    spec = importlib.util.spec_from_file_location("site_whats_new", TOOL / "packaging" / "site_whats_new.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def version_of(tag: str) -> str:
    m = TAG.fullmatch(tag)
    if not m:
        raise ValueError(f"{tag!r} is not a release tag like v0.9.32 or idiograph-v0.9.32")
    return m.group(1)


def site_problems(tag: str, site: Path | None = None, text: str | None = None, version: str | None = None) -> list[str]:
    """One plain line per way the site is not ready for `tag`; empty when it is ready."""
    sw = whats_new_module()
    site = site or sw.SITE
    want = version_of(tag)
    out: list[str] = []
    if version is None:
        version = json.loads(sw.VERSIONS.read_text(encoding="utf-8"))["idiograph"]
    if text is None:
        text = sw.WHATS_NEW.read_text(encoding="utf-8")
    if version != want:
        out.append(f"versions.json says {version}, not {want}: bump the version before releasing {tag}")
    try:
        rels = sw.releases(text, version)
        if not rels:
            out.append(f"docs/whats-new.md has no section for {version}")
        elif rels[0]["version"] != want:
            out.append(f"the newest section of docs/whats-new.md is {rels[0]['version']}, not {want}")
        files = sw.outputs(site, text=text, version=version)
    except ValueError as e:
        out.append(str(e))
        return out
    stale = sorted(p.name for p, content in files.items()
                   if not p.is_file() or p.read_text(encoding="utf-8") != content)
    if stale:
        out.append("site/holding is not what the writer makes (" + ", ".join(stale)
                   + "): run packaging/site_whats_new.py and commit the site")
    dl = site / "download.html"
    if dl.is_file() and f'<p class="get-version">Version {want}</p>' not in dl.read_text(encoding="utf-8"):
        out.append(f"the Download page does not say Version {want}")
    page = site / sw.PAGE
    if page.is_file() and f"{want}" not in page.read_text(encoding="utf-8"):
        out.append(f"What's new on the site does not name {want}")
    return out


def clip_map() -> tuple[dict[str, list[str]], list[str]]:
    """Each clip's own repo paths it shows, read from its `// Screens:` line, and apart from them the shared paths
    in app.mjs's line. A clip is a .mjs script in packaging/motion/clips/ other than app.mjs."""
    def paths(file: Path) -> list[str]:
        m = SCREENS.search(file.read_text(encoding="utf-8"))
        return [p.strip() for p in m.group(1).split(",") if p.strip()] if m else []
    shared = paths(CLIPS / "app.mjs")
    out = {f.stem: paths(f) for f in sorted(CLIPS.glob("*.mjs")) if f.name != "app.mjs"}
    return out, shared


def git(*args: str) -> str:
    return subprocess.run(["git", *args], cwd=TOOL, capture_output=True, text=True, encoding="utf-8",
                          check=True).stdout


def previous_tag(tag: str) -> str | None:
    """The newest plain release tag with a lower version than `tag`."""
    top = tuple(int(x) for x in version_of(tag).split("."))
    for t in git("tag", "--list", "v*", "--sort=-v:refname").split():
        m = PLAIN.fullmatch(t)
        if m and tuple(int(x) for x in m.group(1).split(".")) < top:
            return t
    return None


def hits(changed: list[str], paths: list[str]) -> list[str]:
    return [c for c in changed if any(c == p or (p.endswith("/") and c.startswith(p)) for p in paths)]


def changed_clips(tag: str) -> tuple[dict[str, list[str]], list[str], str | None]:
    """The files that changed since the previous release tag, per clip that shows them, and those of the shared
    list, and that tag. `tag` may not exist yet; HEAD stands for it then."""
    prev = previous_tag(tag)
    if not prev:
        return {}, [], None
    ref = "HEAD"
    for cand in (tag, "v" + version_of(tag)):
        try:
            git("rev-parse", "--verify", "--quiet", cand + "^{commit}")
            ref = cand
            break
        except subprocess.CalledProcessError:
            continue
    changed = git("diff", "--name-only", f"{prev}..{ref}").splitlines()
    clips, shared = clip_map()
    own = {c: h for c, p in clips.items() if (h := hits(changed, p))}
    return own, hits(changed, shared), prev


def checklist(tag: str) -> list[str]:
    sw = whats_new_module()
    want = version_of(tag)
    lines = []
    rels = [r for r in sw.releases(sw.WHATS_NEW.read_text(encoding="utf-8"), want) if r["version"] == want]
    lines.append(f"FEATURES: check each of {want}'s What's new lines has its row on site/holding/features.html, "
                 "and that no row is still Planned or Experimental that the app now has:")
    for r in rels[:1]:
        lines.extend("  - " + x for x in r["lines"])
    try:
        own, shared, prev = changed_clips(tag)
    except (subprocess.CalledProcessError, OSError):
        return lines + ["SCREENSHOTS: git could not compare the release tags; check the clips by hand"]
    since = f" since {prev}" if prev else ""
    if shared:
        lines.append(f"SHARED CHANGED{since} (every clip starts from these; look at one clip if the change shows): "
                     + ", ".join(shared))
    if own:
        lines.append(f"SCREENSHOTS{since}:")
        lines.extend(f"  - re-record {c} ({', '.join(f)})" for c, f in own.items())
    else:
        lines.append(f"SCREENSHOTS: clips: no screen of their own changed{since}")
    return lines


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Check the website is ready for a release")
    ap.add_argument("action", choices=("check", "checklist"))
    ap.add_argument("tag", help="the release tag, like v0.9.32")
    args = ap.parse_args(argv)
    if args.action == "checklist":
        print("\n".join(checklist(args.tag)))
        return 0
    try:
        problems = site_problems(args.tag)
    except ValueError as e:
        problems = [str(e)]
    for p in problems:
        print(f"PROBLEM: {p}")
    if not problems:
        print(f"SITE: ready for {args.tag}")
        for line in checklist(args.tag):
            print(line)
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
