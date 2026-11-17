#!/usr/bin/env python3
"""Add the reflexive thematic analysis demo's six recordings to the demos' release, demo-recordings-1 (rtabuild, 17
November 2026). Run it only on Adam's yes: it publishes six files on the public repository's release.

    .venv/bin/python packaging/upload_rta_recordings.py            says what it would upload, uploads nothing
    .venv/bin/python packaging/upload_rta_recordings.py --yes      uploads them

Each of the six is the recording `make_demo_rta.py --audio` put in packaging/recording for the interview as it
stands, named by its transcript's hash, and must match its size and sha256 in demo/recordings.json, or nothing is
uploaded. The six go up as new assets beside the others (`gh release upload`, never replacing an asset of the same
name, so a copy that already downloaded one is never handed other bytes under its name). One of the six already on
the release is checked by the sha256 GitHub gives for it (its `digest`) and its size against the manifest: the same
bytes are passed over, and other bytes refuse the whole run, nothing uploaded, since a recording is never replaced
(rtafix, 17 November 2026). The licence goes up the same way, a new asset under the name the manifest gives it,
`LICENSE-audio-<first 8 of its sha256>.md` (`demo_recordings.licence_asset`), so the old `LICENSE-audio.md`, which
the copies already out download by their own manifests, stays as it is. The one asset replaced is the release's copy
of the manifest, recordings.json, which no copy of the app reads: each reads the manifest it ships. Then each of the
six, the licence and the manifest are read back from the release's listing by their size and sha256.
`packaging/release.py` refuses a version while any file the manifest names is not on the release so.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import boot  # noqa: E402

boot.setup()
sys.path.insert(0, str(ROOT / "packaging"))

import demo_recordings as demo_rec  # noqa: E402
import make_demo_rta as rta  # noqa: E402
import release  # noqa: E402  the release's assets read with gh, its GH the checks' stand-in (area 421)

REPO = "Pharkie/idiograph"
MANIFEST = ROOT / "demo" / demo_rec.MANIFEST
FOLDER = ROOT / "packaging" / "recording"


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def the_six() -> tuple[str, list[Path], dict, dict]:
    """The release's tag, the six recordings, each checked against the manifest, the manifest's entries by file and
    its licence's entry, the licence checked too, or SystemExit with the reason."""
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    entries = {e["file"]: e for e in manifest.get("recordings") or []}
    files = []
    for name in rta.recording_names():
        path, entry = FOLDER / name, entries.get(name)
        if entry is None:
            raise SystemExit(f"demo/recordings.json does not name {name}: run make_demo_rta.py --audio first.")
        if not path.is_file():
            raise SystemExit(f"{name} is not in packaging/recording: run make_demo_rta.py --audio first.")
        if path.stat().st_size != entry["size"] or sha(path) != entry["sha256"]:
            raise SystemExit(f"{name} is not the recording the manifest names (its size or sha256 differs).")
        files.append(path)
    licence = manifest.get("licence") or {}
    path = FOLDER / demo_rec.LICENCE
    if (not licence or not path.is_file() or path.stat().st_size != licence["size"] or sha(path) != licence["sha256"]
            or licence["file"] != demo_rec.licence_asset(licence["sha256"])):
        raise SystemExit(f"{path.name} is not the licence the manifest names: run make_demo.py --manifest first.")
    return str(manifest.get("release") or demo_rec.RELEASE), files, entries, licence


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Add the reflexive thematic analysis demo's recordings to the release.")
    ap.add_argument("--yes", action="store_true", help="upload them (Adam's yes); without it nothing is uploaded")
    a = ap.parse_args(argv)
    tag, files, entries, licence = the_six()
    total = sum(p.stat().st_size for p in files)
    print(f"To {REPO}, release {tag}:")
    for p in files:
        print(f"  {p.name}  {p.stat().st_size / 1e6:.2f} MB")
    print(f"  {licence['file']}, the licence, unless the release has it already")
    print(f"  {MANIFEST.name}, replacing the release's copy")
    print(f"  {len(files)} recordings, {total / 1e6:.1f} MB in all")
    if not a.yes:
        print("Nothing uploaded. Run again with --yes to upload.")
        return 0
    try:
        there = release.release_assets(tag, REPO)
    except SystemExit as exc:
        print(str(exc), file=sys.stderr)
        return 1
    # a recording or the licence of the same name already there is passed over only when its bytes are the
    # manifest's: other bytes under its name would fail every download's checksum, and neither is ever replaced
    ours = [*(entries[p.name] for p in files), licence]
    unsummed = release.no_checksum(ours, there)
    if unsummed:
        print(f"GitHub gave no checksum for {', '.join(unsummed)}, so upgrade gh and run again. Nothing uploaded.",
              file=sys.stderr)
        return 1
    clash = [e["file"] for e in ours if e["file"] in there and release.unreleased([e], there)]
    if clash:
        print(f"On the release with another size or sha256 than demo/recordings.json names: {', '.join(clash)}. "
              "Nothing uploaded. A recording or licence is never replaced: check which bytes are right, and if the "
              "release's are wrong and no copy has downloaded them, delete those assets on GitHub by hand, then run "
              "this again.", file=sys.stderr)
        return 1
    new = [p for p in files if p.name not in there]
    with tempfile.TemporaryDirectory() as held:
        if licence["file"] not in there:
            # the licence under its name on the release, which gh takes from the file's own name
            new.append(Path(shutil.copyfile(FOLDER / demo_rec.LICENCE, Path(held) / licence["file"])))
        if new:
            subprocess.run([*release.GH, "release", "upload", tag, *map(str, new), "--repo", REPO], check=True)
    # the release's copy of the manifest, the one asset replaced: no copy of the app reads it
    subprocess.run([*release.GH, "release", "upload", tag, str(MANIFEST), "--repo", REPO, "--clobber"], check=True)
    try:
        got = release.release_assets(tag, REPO)
    except SystemExit as exc:
        print(str(exc), file=sys.stderr)
        return 1
    manifest = {"file": MANIFEST.name, "size": MANIFEST.stat().st_size, "sha256": sha(MANIFEST)}
    wrong = release.unreleased([entries[p.name] for p in files] + [licence, manifest], got)
    if wrong:
        print(f"Not on the release at its size and sha256: {', '.join(wrong)}", file=sys.stderr)
        return 1
    sent = [p for p in new if p.name != licence["file"]]
    print(f"Done: {len(sent)} recordings uploaded, {len(files) - len(sent)} there already with the same bytes, the "
          f"licence {'uploaded' if len(sent) < len(new) else 'there already'}, and the manifest replaced.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
