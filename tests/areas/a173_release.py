from __future__ import annotations

import base64
import json
import os
import re
import shutil
import stat
import struct
import subprocess
import sys
import tarfile
from pathlib import Path

from . import support
from .support import STUDY_PSEUDONYMS, check, skip

# Tauri's own CLI, 2.12.1, signed a file with a throwaway key made in a check's folder on 17 October and
# thrown away after: the public key, the file and the signature, none of them secret, so the suite holds
# Python's checking to the signatures Tauri itself makes
TAURI_PUBLIC = ("dW50cnVzdGVkIGNvbW1lbnQ6IG1pbmlzaWduIHB1YmxpYyBrZXk6IEZGRTlGMUU0RUYxNUY5QTcKUldTbitSWHY1UEhwLy9S"
                "WmRzNDJ0QXF4MDhCVHBKUUdsVjRTWVRkTWFpOHEyTjY1WUR2QndKRjAK")
TAURI_FILE = b"a file about dogs at home\n"
TAURI_SIGNATURE = (
    "dW50cnVzdGVkIGNvbW1lbnQ6IHNpZ25hdHVyZSBmcm9tIHRhdXJpIHNlY3JldCBrZXkKUlVTbitSWHY1UEhwLzRRTEk5RzZUcTlucEcr"
    "UUo4T2tkVFdqd3RBQmNid0ZTNEczYloyM2FNN2R5amFQaG1WYjdxQ0FGanJ3aE5JN3lGZzJIOFhpNStWZ2lueWtvM0pyaWdRPQp0cnVz"
    "dGVkIGNvbW1lbnQ6IHRpbWVzdGFtcDoxNzkyMjY4MzUxCWZpbGU6ZG9ncy50eHQJdmVyc2lvbjowLjkuMQp5SUZuV2ZJckNNYk53aHZH"
    "bEFwQVd4TzM4bFBGUUNrTUg4dU16a2NoY3F1K0IyRW4vOUwyNi9PRWhyRVI3aGtHemUwYUwvNi9FKzJTbmg2N0J3c2lBUT09Cg==")
# a fat Mach-O header for both of a Mac's architectures, a thin one for Apple Silicon alone and one for Intel alone
FAT = struct.pack(">II", 0xCAFEBABE, 2) + struct.pack(">IIIII", 0x01000007, 3, 4096, 16, 12) \
    + struct.pack(">IIIII", 0x0100000C, 0, 8192, 16, 14) + b"\0" * 64
THIN = struct.pack("<II", 0xFEEDFACF, 0x0100000C) + b"\0" * 64
INTEL = struct.pack("<II", 0xFEEDFACF, 0x01000007) + b"\0" * 64


def js_function(src: str, name: str) -> str:
    """A top-level function of a page script, from its `function` line to the brace that closes it."""
    m = re.search(rf"^(?:async )?function {name}\(", src, re.M)
    if not m:
        return ""
    end = src.find("\n}\n", m.start())
    return src[m.start():end + 3] if end > 0 else ""


def fake_app(folder: Path, name: str, exe: bytes) -> Path:
    """An app bundle of the check's own: an executable whose header names its architectures, a link
    as PyInstaller's frozen server keeps one, and a plain file."""
    app = folder / f"{name}.app"
    (app / "Contents" / "MacOS").mkdir(parents=True)
    (app / "Contents" / "MacOS" / name).write_bytes(exe)
    server = app / "Contents" / "Resources" / "server" / "_internal"
    server.mkdir(parents=True)
    (server / "Python.real").write_bytes(b"the frozen server's own Python, invented")
    try:
        (server / "Python").symlink_to("Python.real")
    except OSError:
        pass
    (app / "Contents" / "Info.plist").write_text("<plist/>\n", encoding="utf-8")
    return app


def test_release(scratch):
    print("\n173. Idiograph's installers and its release, the third Tauri build (17 October): the Mac app, its disk "
          "image and update file and the Windows installer from Tauri's bundler, the release script's manifest "
          "signed with a throwaway key and a changed file refused, the update key's script with a Keychain of the "
          "check's own, and what the second build's screenshots found")
    sys.path.insert(0, str(support.source("packaging")))
    sys.path.insert(0, str(support.source("packaging/tauri")))
    import importlib
    import minisign
    import release
    import bundle as window
    importlib.reload(minisign)
    import server as server_mod

    read = lambda path: Path(path).read_text(encoding="utf-8")
    tauri = support.source("packaging/tauri")
    src = tauri / "src-tauri"
    conf = json.loads(read(src / "tauri.conf.json"))
    mac_conf = json.loads(read(src / "tauri.macos.conf.json"))
    app_js, readme = support.text("family/static/shell.js", "apps/idiograph/static/distil.js"), read(support.source("README.md"))
    whats_new = read(support.source("docs/whats-new.md"))
    workflows = support.source(".github/workflows")
    main_yml = read(workflows / "windows-installer.yml")
    release_src, key_sh = read(support.source("packaging/release.py")), read(support.source("packaging/make_update_key.sh"))
    minisign_src, bundle_src = read(support.source("packaging/minisign.py")), read(tauri / "bundle.py")
    base = scratch / "release-173"
    shutil.rmtree(base, ignore_errors=True)
    base.mkdir(parents=True)

    # ── A. minisign's signatures, as Tauri's updater checks them
    comment = minisign.verify(TAURI_PUBLIC, TAURI_FILE, TAURI_SIGNATURE)
    check("173: a signature Tauri's own CLI made checks against its public key, its trusted comment naming the "
          "file and the version, and the same signature refuses a changed file",
          comment == "timestamp:1792268351\tfile:dogs.txt\tversion:0.9.1"
          and minisign.verify(TAURI_PUBLIC, TAURI_FILE + b"!", TAURI_SIGNATURE) is None, str(comment))
    key_dir = base / "key"
    key_dir.mkdir()
    password = "a throwaway password for dogs"
    blob = minisign.make_secret(password)
    key = minisign.open_secret(blob, password)
    public = key.public_key()
    (key_dir / "update.key").write_text(blob, encoding="utf-8")
    (key_dir / "update.key.password").write_text(password, encoding="utf-8")
    (key_dir / "update.key.pub").write_text(public, encoding="utf-8")
    try:
        minisign.open_secret(blob, "the wrong password")
        wrong_pw = "opened"
    except minisign.BadKey as exc:
        wrong_pw = str(exc)
    lines = base64.b64decode(blob).decode().splitlines()
    check("173: a throwaway key made in the check's folder is minisign's, sealed with scrypt, and opens with its "
          "password alone, its public half in the form tauri.conf.json holds",
          lines[0] == "untrusted comment: rsign encrypted secret key" and base64.b64decode(lines[1])[:6] == b"EdScB2"
          and wrong_pw == "the password does not open this key"
          and base64.b64decode(public).decode().startswith("untrusted comment: minisign public key: ")
          and minisign.read_public(public)[1] == key.public and "seed" not in repr(key) and key.seed.hex() not in repr(key))
    signed = minisign.sign(key, b"an update about dogs", minisign.trusted_comment("Idiograph-Setup.exe", "0.9.1", 1792268400))
    check("173: a signature made here checks with the public key, binds the file's name and the version as Tauri's "
          "--app-version does, and fails on a changed file, another key's public half or a changed comment",
          minisign.verify(public, b"an update about dogs", signed) == "timestamp:1792268400\tfile:Idiograph-Setup.exe\tversion:0.9.1"
          and minisign.verify(public, b"an update about cats", signed) is None
          and minisign.verify(TAURI_PUBLIC, b"an update about dogs", signed) is None
          and minisign.verify(public, b"an update about dogs", base64.b64encode(
              base64.b64decode(signed).replace(b"version:0.9.1", b"version:0.9.2")).decode()) is None
          and base64.b64decode(signed).decode().splitlines()[0] == "untrusted comment: signature from tauri secret key")
    # Adam's public key since 18 October (the fifth Tauri build, area 180), where a placeholder stood that no
    # signature could match. The placeholder's words are kept here, so a key that is no key is still refused
    placeholder = ("NOT MADE YET: the public key packaging/make_update_key.sh prints goes here, and until it does "
                   "every update is refused")
    adams = conf["plugins"]["updater"]["pubkey"]
    try:
        keynum, adams_public = minisign.read_public(adams)
        adams_id = keynum[::-1].hex().upper()
    except minisign.BadKey:
        adams_id, adams_public = "refused", b""
    try:
        minisign.read_public(placeholder)
        refused = "read"
    except minisign.BadKey:
        refused = "refused"
    check("173, updated 18 October (180): tauri.conf.json holds Adam's public key, minisign's key 3CEA6A356EFB3E63, "
          "never a throwaway one of a check's, a placeholder that is no key is refused, and the updater asks the "
          "releases repository's latest.json",
          adams_id == "3CEA6A356EFB3E63" and len(adams_public) == 32 and adams_public != key.public
          and base64.b64decode(adams).decode().startswith("untrusted comment: minisign public key: 3CEA6A356EFB3E63\n")
          and refused == "refused"
          and conf["plugins"]["updater"]["endpoints"] == ["https://github.com/Pharkie/idiograph/releases/latest/download/latest.json"],
          adams_id)

    # ── B. the release script, with the check's own files, key and gh
    builds = base / "builds"
    builds.mkdir()
    universal = window.update_tarball(fake_app(base / "app-both", "Idiograph", FAT), builds / release.MAC_UPDATE)
    (builds / release.WINDOWS).write_bytes(b"MZ an installer of the check's own")
    (builds / release.DMG).write_bytes(b"a disk image of the check's own")
    out = base / "out"
    said = subprocess.run([sys.executable, str(support.source("packaging/release.py")), "v0.9.1", "--from", str(builds),
                           "--test-key", str(key_dir), "--out", str(out), "--dry-run"],
                          capture_output=True, text=True, encoding="utf-8", timeout=300)
    manifest = json.loads(read(out / "latest.json")) if (out / "latest.json").is_file() else {}
    try:
        date, notes = release.notes_for("0.9.1")
    except SystemExit as exc:
        date, notes = "", f"refused: {exc}"
    platforms = manifest.get("platforms", {})
    files = {n: out / n for n in release.FILES}
    check("173: a dry run collects the three files, signs both update files with the throwaway key, writes latest.json "
          "in Tauri's form with the notes of whats-new.md, and uploads nothing",
          said.returncode == 0 and manifest.get("version") == "0.9.1" and manifest.get("notes") == notes
          and re.fullmatch(r"\d{4}-\d\d-\d\dT\d\d:\d\d:\d\dZ", manifest.get("pub_date", "")) is not None
          and sorted(platforms) == ["darwin-aarch64", "windows-x86_64"]
          and platforms["windows-x86_64"]["url"] == "https://github.com/Pharkie/idiograph/releases/download/v0.9.1/Idiograph-Setup.exe"
          and platforms["darwin-aarch64"]["url"].endswith("/v0.9.1/Idiograph.app.tar.gz")
          and "Dry run: nothing uploaded." in said.stdout
          and (out / "Idiograph-Setup.exe.sig").read_text(encoding="utf-8") == platforms["windows-x86_64"]["signature"],
          (said.stdout + said.stderr)[-600:])
    check("173: every signature in the manifest checks against its own file with the throwaway public key, for 0.9.1",
          release.check_manifest(manifest, public, files, "0.9.1") == []
          and all(f"version:0.9.1" in (minisign.verify(public, files[e["url"].rsplit("/", 1)[1]].read_bytes(), e["signature"]) or "")
                  for e in platforms.values()))
    tampered = dict(files)
    changed = base / "changed-Idiograph-Setup.exe"
    changed.write_bytes(files[release.WINDOWS].read_bytes() + b"!")
    tampered[release.WINDOWS] = changed
    downgraded = json.loads(json.dumps(manifest))
    downgraded["version"] = "0.9.2"
    moved = json.loads(json.dumps(manifest))
    moved["platforms"]["windows-x86_64"]["url"] = "https://example.com/Idiograph-Setup.exe"
    check("173: a changed file is refused, as is a manifest that names another version than its signatures were made "
          "for, or a file anywhere but the releases repository",
          release.check_manifest(manifest, public, tampered, "0.9.1") == ["windows-x86_64's signature does not check against Idiograph-Setup.exe"]
          and any("is not for 0.9.2" in w for w in release.check_manifest(downgraded, public, files, "0.9.2"))
          and any("is not on Pharkie/idiograph" in w for w in release.check_manifest(moved, public, files, "0.9.1")))
    thin = window.update_tarball(fake_app(base / "app-one", "Idiograph", THIN), base / "thin.tar.gz")
    intel = base / "intel"
    intel.mkdir()
    window.update_tarball(fake_app(base / "app-intel", "Idiograph", INTEL), intel / release.MAC_UPDATE)
    for name in (release.WINDOWS, release.DMG):
        shutil.copyfile(builds / name, intel / name)
    refused = subprocess.run([sys.executable, str(support.source("packaging/release.py")), "v0.9.1", "--from", str(intel),
                              "--test-key", str(key_dir), "--out", str(base / "out-intel"), "--dry-run"],
                             capture_output=True, text=True, encoding="utf-8", timeout=300)
    with_intel = json.loads(json.dumps(manifest))
    with_intel["platforms"]["darwin-x86_64"] = dict(with_intel["platforms"]["darwin-aarch64"])
    check("173, updated 9 November (relfix): the Mac app is offered to Apple Silicon alone, darwin-aarch64, whatever its "
          "executable holds, one with no arm64 part is refused with nothing signed, and a manifest with a darwin-x86_64 "
          "entry is wrong",
          release.mac_archs(universal) == ["aarch64", "x86_64"] and release.mac_archs(thin) == ["aarch64"]
          and refused.returncode != 0 and "not for Apple Silicon" in refused.stdout + refused.stderr
          and not (base / "out-intel" / "latest.json").exists()
          and release.check_manifest(with_intel, public, files, "0.9.1")
          == ["darwin-x86_64 is listed, and the Mac app is for Apple Silicon alone"],
          (refused.stdout + refused.stderr)[-300:])

    other = base / "other-key"
    other.mkdir()
    for name in ("update.key", "update.key.password"):
        shutil.copyfile(key_dir / name, other / name)
    (other / "update.key.pub").write_text(minisign.open_secret(minisign.make_secret("x"), "x").public_key(), encoding="utf-8")
    holder = base / "placeholder-key"
    holder.mkdir()
    for name in ("update.key", "update.key.password"):
        shutil.copyfile(key_dir / name, holder / name)
    (holder / "update.key.pub").write_text(placeholder, encoding="utf-8")
    # a check's throwaway key held up against Adam's public key, as a release with the wrong key would be
    against_adams = base / "against-adams-key"
    against_adams.mkdir()
    for name in ("update.key", "update.key.password"):
        shutil.copyfile(key_dir / name, against_adams / name)
    (against_adams / "update.key.pub").write_text(adams, encoding="utf-8")
    refusals = {}
    for label, folder in (("other", other), ("placeholder", holder), ("adams", against_adams)):
        try:
            release.update_key(folder)
            refusals[label] = "taken"
        except SystemExit as exc:
            refusals[label] = str(exc)
    check("173, updated 18 October (180): a key whose public half is not the app's is refused, a check's throwaway "
          "key against Adam's public key among them, and so is any key against a placeholder, so no release goes out "
          "that every copy would refuse",
          refusals["other"].startswith("The update key is not the one tauri.conf.json names")
          and refusals["adams"].startswith("The update key is not the one tauri.conf.json names")
          and refusals["placeholder"].startswith("tauri.conf.json has no public key yet"), str(refusals))
    check("173: the release reads the Keychain only to sign, through security's own find-generic-password, never "
          "prints a key or writes one to a file, and a check's key comes through --test-key alone",
          release.SECURITY[:2] == ["security", "find-generic-password"] and release.KEY_ITEM == "idiograph-update-key"
          and release.PASSWORD_ITEM == "idiograph-update-key-password" and "capture_output=True" in release_src
          and not re.search(r"print\([^)]*(blob|password|seed)", release_src) and "write_text(blob" not in release_src
          and "TAURI_SIGNING_PRIVATE_KEY" not in release_src and "secrets." not in read(support.source(".github/workflows/windows-installer.yml")))

    # the upload, with a gh of the check's own that writes down what it is asked
    # its first argument the repository's state: "empty" with no commit (GitHub's 409), "readme" with one
    # commit and a size of 0 KB, as idiograph-releases had on 22 October, "there" with the tag already
    # released, "lost" with a 404, "failing" where the release's create fails, and since pubreadme (10
    # November 2026, two repositories: Pharkie/idiograph and the old idiograph-releases) "draft" where the
    # app's own repository holds the tag's draft, "half" where it has the version published and the old one
    # not, "archived" where the old one is archived
    gh = base / "gh_stub.py"
    gh.write_text(
        "import json, sys\nstate, args = sys.argv[1], sys.argv[2:]\n"
        "open(sys.argv[0] + '.' + state + '.log', 'a').write(json.dumps(args) + '\\n')\n"
        "repo = args[args.index('--repo') + 1] if '--repo' in args else ''\n"
        "if args[:2] == ['release', 'view']:\n"
        "    if state == 'there' or (state == 'half' and repo == 'Pharkie/idiograph'): print('false'); sys.exit(0)\n"
        "    if state == 'draft' and repo == 'Pharkie/idiograph': print('true'); sys.exit(0)\n"
        "    sys.exit(1)\n"
        "if args[:2] == ['repo', 'view']: print('true' if state == 'archived' else 'false'); sys.exit(0)\n"
        "if args[:1] == ['api'] and '--jq' in args and '.size' in args: print('0'); sys.exit(0)\n"
        "if args[:1] == ['api'] and '/commits' in args[1]:\n"
        "    if state == 'empty': sys.stderr.write('gh: Git Repository is empty. (HTTP 409)\\n'); sys.exit(1)\n"
        "    if state == 'lost': sys.stderr.write('gh: Not Found (HTTP 404)\\n'); sys.exit(1)\n"
        "    print('1'); sys.exit(0)\n"
        "if args[:3] == ['api', '-X', 'PUT'] and state != 'empty':\n"
        "    sys.stderr.write('gh: Invalid request. \"sha\" wasn\\'t supplied. (HTTP 422)\\n'); sys.exit(1)\n"
        "if args[:2] == ['release', 'create'] and state == 'failing': sys.exit(1)\n", encoding="utf-8")

    def upload_with(state, argv):
        kept_gh = release.GH
        try:
            release.GH = [sys.executable, str(gh), state]
            done = release.main(argv)
        except SystemExit as exc:
            done = f"refused: {exc}"
        finally:
            release.GH = kept_gh
        log = Path(f"{gh}.{state}.log")
        asked = [json.loads(line) for line in log.read_text(encoding="utf-8").splitlines()] if log.exists() else []
        log.unlink(missing_ok=True)
        return done, asked

    signing = ["v0.9.1", "--from", str(builds), "--test-key", str(key_dir), "--out", str(out)]
    shutil.rmtree(out)
    uploaded, asked = upload_with("empty", signing)
    creates = [a for a in asked if a[:2] == ["release", "create"]]
    create = creates[0] if creates else []
    check("173: the upload makes the releases repository's first commit when it has none, then the release with the "
          "three files and latest.json, published, with the notes, and a version already there is refused",
          uploaded == 0 and asked[0][:2] == ["release", "view"] and any(a[:3] == ["api", "-X", "PUT"] for a in asked)
          and create[:5] == ["release", "create", "v0.9.1", "--repo", "Pharkie/idiograph"]
          and "--draft" not in create and [Path(a).name for a in create[-4:]] == ["Idiograph.dmg", "Idiograph.app.tar.gz",
                                                                                  "Idiograph-Setup.exe", "latest.json"]
          and "--notes-file" in create
          and [a[:2] for a in asked].index(["api", "-X"]) < asked.index(create), str(asked)[:500])

    # pubreadme (10 November 2026, Adam's ruling about 12:50): the transitional 0.9.24 goes to Pharkie/idiograph and
    # to the old idiograph-releases, each repository's latest.json and notes naming its own files
    old = creates[1] if len(creates) > 1 else []
    old_files = [Path(a) for a in old if a.endswith((".json", ".md"))]
    old_manifest = json.loads(read(old_files[-1])) if old_files and old_files[-1].name == "latest.json" else {}
    old_notes = read(old[old.index("--notes-file") + 1]) if "--notes-file" in old else ""
    own_notes = read(out / "notes.md") if (out / "notes.md").is_file() else ""
    own_manifest = json.loads(read(out / "latest.json")) if (out / "latest.json").is_file() else {}
    check("173, pubreadme (10 November): a release goes to Pharkie/idiograph and then to Pharkie/idiograph-releases, the "
          "updater's old address, each with its own latest.json, every address on that repository and the same signatures, "
          "and notes holding the version's lines and the table of which file to download, linked on that repository",
          len(creates) == 2 and old[:5] == ["release", "create", "v0.9.1", "--repo", "Pharkie/idiograph-releases"]
          and all(e["url"].startswith("https://github.com/Pharkie/idiograph/releases/download/v0.9.1/")
                  for e in own_manifest.get("platforms", {}).values())
          and sorted(old_manifest.get("platforms", {})) == sorted(own_manifest.get("platforms", {}))
          and all(e["url"].startswith("https://github.com/Pharkie/idiograph-releases/releases/download/v0.9.1/")
                  and e["signature"] == own_manifest["platforms"][k]["signature"] for k, e in old_manifest.get("platforms", {}).items())
          and "### Which file do I need?" in own_notes
          and "| Mac with Apple Silicon (M1 or later) | [Idiograph.dmg](https://github.com/Pharkie/idiograph/releases/download/v0.9.1/Idiograph.dmg) |" in own_notes
          and "| Windows | [Idiograph-Setup.exe](https://github.com/Pharkie/idiograph/releases/download/v0.9.1/Idiograph-Setup.exe) |" in own_notes
          and "AppImage" not in own_notes and ".deb" not in own_notes
          and "https://github.com/Pharkie/idiograph-releases/releases/download/v0.9.1/Idiograph.dmg" in old_notes
          and "Pharkie/idiograph/" not in old_notes,
          f"{old} | {own_notes} | {old_notes}"[:900])

    # 22 October (relfix): idiograph-releases held 0.9.1 and a short README, and GitHub gave its size as
    # 0 KB, so the release took it for empty, made README.md again without its sha and was refused (422)
    readme_done, readme_asked = upload_with("readme", ["v0.9.1", "--from", str(out), "--out", str(out), "--test-key", str(key_dir)])
    readme_create = next((a for a in readme_asked if a[:2] == ["release", "create"]), [])
    there_done, there_asked = upload_with("there", ["v0.9.1", "--from", str(out), "--out", str(out), "--test-key", str(key_dir)])
    lost_done, lost_asked = upload_with("lost", ["v0.9.1", "--from", str(out), "--out", str(out), "--test-key", str(key_dir)])
    check("173, updated 22 October (relfix): a releases repository with a commit and a size of 0 KB goes straight to the release, never "
          "making README.md again, a version already there is refused before anything is asked of the repository, "
          "and a repository GitHub cannot say is empty is refused, never taken for empty",
          readme_done == 0 and not any(a[:3] == ["api", "-X", "PUT"] for a in readme_asked)
          and readme_create[:5] == ["release", "create", "v0.9.1", "--repo", "Pharkie/idiograph"]
          and not any("--jq" in a and ".size" in a for a in readme_asked)
          and str(there_done).startswith("refused: Pharkie/idiograph and Pharkie/idiograph-releases already have v0.9.1")
          and all(a[:2] in (["release", "view"], ["repo", "view"]) for a in there_asked)
          and str(lost_done).startswith("refused: GitHub did not say whether Pharkie/idiograph has a commit")
          and "404" in str(lost_done) and not any(a[:2] in (["release", "create"], ["api", "-X"]) for a in lost_asked),
          f"{readme_done} {readme_asked} | {there_done} | {lost_done} {lost_asked}"[:900])

    # pubreadme: on the app's own repository the tag's draft, which holds the files, is given latest.json and
    # published, never a second release made, a repository with the version out already is passed over, so a
    # half-done run finishes the rest, and an archived one is passed over too
    def resumed_from(state):
        return upload_with(state, ["v0.9.1", "--from", str(out), "--out", str(out), "--test-key", str(key_dir)])
    draft_done, draft_asked = resumed_from("draft")
    half_done, half_asked = resumed_from("half")
    arch_done, arch_asked = resumed_from("archived")
    repos_of = lambda asked, verb: [a[a.index("--repo") + 1] for a in asked if a[:2] == ["release", verb]]
    draft_upload = next((a for a in draft_asked if a[:2] == ["release", "upload"]), [])
    draft_edit = next((a for a in draft_asked if a[:2] == ["release", "edit"]), [])
    check("173, pubreadme (10 November): the draft release on Pharkie/idiograph gets latest.json and is published with "
          "its title and notes, the old repository gets a release of its own, a repository that has the version is "
          "passed over and one archived is too",
          draft_done == 0 and repos_of(draft_asked, "create") == ["Pharkie/idiograph-releases"]
          and draft_upload[3:6] == ["--repo", "Pharkie/idiograph", "--clobber"] and Path(draft_upload[-1]).name == "latest.json"
          and draft_edit[2:5] == ["v0.9.1", "--repo", "Pharkie/idiograph"] and "--draft=false" in draft_edit
          and draft_edit[draft_edit.index("--title") + 1] == "Idiograph 0.9.1"
          and Path(draft_edit[draft_edit.index("--notes-file") + 1]) == (out / "notes.md").resolve()
          and draft_asked.index(draft_upload) < draft_asked.index(draft_edit)
          and half_done == 0 and repos_of(half_asked, "create") == ["Pharkie/idiograph-releases"]
          and not repos_of(half_asked, "edit")
          and arch_done == 0 and repos_of(arch_asked, "create") == ["Pharkie/idiograph"]
          and ["repo", "view", "Pharkie/idiograph-releases"] in [a[:3] for a in arch_asked],
          f"{draft_done} {draft_asked} | {half_done} {half_asked} | {arch_done} {arch_asked}"[:1200])

    # a failed upload after signing says the line that finishes it, and that line uploads the signed folder
    # without signing again: a key folder holding the public half alone, so any signing would fail
    shutil.rmtree(out)
    failed, _ = upload_with("failing", signing)
    sigs = {n: (out / n).read_bytes() for n in ("Idiograph.app.tar.gz.sig", "Idiograph-Setup.exe.sig", "latest.json")} \
        if (out / "latest.json").is_file() else {}
    public_only = base / "public-only"
    public_only.mkdir(exist_ok=True)
    shutil.copyfile(key_dir / "update.key.pub", public_only / "update.key.pub")
    resumed, resumed_asked = upload_with("readme", ["v0.9.1", "--from", str(out), "--out", str(out), "--test-key", str(public_only)])
    resumed_create = next((a for a in resumed_asked if a[:2] == ["release", "create"]), [])
    # a file changed in the signed folder since is refused, nothing uploaded
    tampered = base / "tampered"
    shutil.copytree(out, tampered)
    (tampered / release.WINDOWS).write_bytes(b"MZ another installer")
    refused_tamper, tamper_asked = upload_with("readme", ["v0.9.1", "--from", str(tampered), "--out", str(tampered), "--test-key", str(public_only)])
    check("173, updated 22 October (relfix): an upload that fails after signing keeps the signed folder and says the command that finishes "
          "it, and that command, --from the folder, uploads it as signed, its signatures checked again and nothing "
          "signed twice, while a file changed since is refused",
          str(failed).startswith("refused: The upload to Pharkie/idiograph failed")
          and f"python3 packaging/release.py v0.9.1 --from {out.resolve()}" in str(failed) and len(sigs) == 3
          and resumed == 0 and [Path(a).name for a in resumed_create[-4:]] == ["Idiograph.dmg", "Idiograph.app.tar.gz",
                                                                              "Idiograph-Setup.exe", "latest.json"]
          and Path(resumed_create[resumed_create.index("--notes-file") + 1]) == (out / "notes.md").resolve()
          and all((out / n).read_bytes() == b for n, b in sigs.items())
          and str(refused_tamper).startswith(f"refused: latest.json in {tampered.resolve()} is wrong")
          and not any(a[:2] == ["release", "create"] for a in tamper_asked),
          f"{failed} | {resumed} {resumed_asked} | {refused_tamper}"[:900])

    # the notes
    heading = re.findall(r"^## (\d+\.\d+\.\d+), (\d{1,2} [A-Z][a-z]+ \d{4})$", whats_new, re.M)
    too_many = "## 0.9.1, 17 October 2026\n" + "\n".join(f"line {n}" for n in range(9)) + "\n"
    try:
        release.notes_for("0.9.1", too_many)
        long_said = "taken"
    except SystemExit as exc:
        long_said = str(exc)
    try:
        release.notes_for("9.9.9")
        none_said = "taken"
    except SystemExit as exc:
        none_said = str(exc)
    check("173: docs/whats-new.md holds the versions newest first, each its number and date then a plain line a part, "
          "eight at most, the server's own version among them, and the release takes that version's section",
          heading and heading[0][0] == server_mod.VERSION and dict(heading).get("0.9.1") == date and 1 <= len(notes.splitlines()) <= 8
          and "eight at most" not in notes and long_said.startswith("docs/whats-new.md has 9 lines")
          and none_said == "docs/whats-new.md has no section for 9.9.9." and "\u2014" not in whats_new
          and not any(re.search(rf"\b{n}\b", whats_new) for n in STUDY_PSEUDONYMS), str(heading))

    # ── C. the key's script, with a Keychain of the check's own
    if sys.platform == "win32" or not shutil.which("sh"):
        skip("173: the update key's script", "it runs on a Mac, and this is not one")
    else:
        kc, tmp, stubs = base / "keychain", base / "tmp", base / "stubs"
        for folder in (kc, tmp, stubs):
            folder.mkdir()
        packaging = support.source("packaging")
        cli = stubs / "tauri"
        # since the fourth build (175) the CLI is given no password on its command line and asks for it on its
        # terminal, twice, which key_prompt.py answers: the stand-in asks the same way, and seals the key it
        # makes under the password it was given, as the CLI does
        cli.write_text(f"""#!/bin/sh
# Tauri's CLI as the check stands it in: signer generate -w PATH, asking for the password on its terminal
echo called >> "{stubs}/cli-calls"
echo "$*" >> "{stubs}/cli-args"
[ -f "{stubs}/fail" ] && {{ echo "no key: dW50cnVzdGVkIGNvbW1lbnQ6IHJzaWduIGVuY3J5cHRlZCBzZWNyZXQga2V5IHNlY3JldA=="; exit 1; }}
while [ $# -gt 0 ]; do case "$1" in -w) out="$2"; shift ;; esac; shift; done
printf 'Password: ' > /dev/tty; stty -echo < /dev/tty; read first < /dev/tty; stty echo < /dev/tty
printf '\\nPassword (one more time): ' > /dev/tty; stty -echo < /dev/tty; read second < /dev/tty; stty echo < /dev/tty
[ "$first" = "$second" ] || {{ echo "passwords don't match!"; exit 1; }}
printf %s "$first" > "{stubs}/password-given"
"{sys.executable}" -c "import sys; sys.path.insert(0, sys.argv[1]); import minisign; k = minisign.make_secret(sys.argv[2]); open(sys.argv[3], 'w').write(k); open(sys.argv[3] + '.pub', 'w').write(minisign.open_secret(k, sys.argv[2]).public_key())" "{packaging}" "$first" "$out"
echo "Your keypair was generated successfully"
""", encoding="utf-8")
        cli.chmod(0o755)
        security = stubs / "security"
        security.write_text(f'#!/bin/sh\necho "$@" >> "{stubs}/security-calls"\nexit 1\n', encoding="utf-8")
        security.chmod(0o755)
        env = dict(os.environ, IDIOGRAPH_KEYCHAIN_STUB=str(kc), IDIOGRAPH_TAURI_CLI=str(cli), TMPDIR=str(tmp),
                   PATH=f"{stubs}{os.pathsep}{os.environ.get('PATH', '')}")
        script = str(support.source("packaging/make_update_key.sh"))
        first = subprocess.run(["sh", script], env=env, capture_output=True, text=True, encoding="utf-8", timeout=120)
        given = (stubs / "password-given").read_text(encoding="utf-8") if (stubs / "password-given").exists() else ""
        kept_key = (kc / "idiograph-update-key").read_text(encoding="utf-8") if (kc / "idiograph-update-key").exists() else ""
        kept_pw = (kc / "idiograph-update-key-password").read_text(encoding="utf-8") if (kc / "idiograph-update-key-password").exists() else ""
        modes = [stat.S_IMODE((kc / n).stat().st_mode) for n in ("idiograph-update-key", "idiograph-update-key-password") if (kc / n).exists()]
        printed = first.stdout + first.stderr
        made = kept_key
        made_pub = minisign.open_secret(made, given).public_key() if made and given else ""
        args_given = (stubs / "cli-args").read_text(encoding="utf-8") if (stubs / "cli-args").exists() else ""
        check("173, updated 18 October (175): the key's script makes the pair with Tauri's CLI under a password of 40 "
              "made at random, which reaches the CLI on its terminal and never its command line, puts the key and its "
              "password in the Keychain for this user alone, and leaves nothing behind in its folder",
              first.returncode == 0 and made_pub != "" and re.fullmatch(r"[A-Za-z0-9]{40}", given) is not None
              and given not in args_given and "-p" not in args_given.split() and "--ci" not in args_given
              and kept_pw == given and modes == [0o600, 0o600] and list(tmp.iterdir()) == [], printed[-500:])
        check("173: it prints the public key alone, never the key or its password, names where it goes, and asks for both "
              "to be kept in 1Password",
              made_pub in printed and made not in printed and given not in printed
              and "tauri.conf.json" in printed and "1Password" in printed and "idiograph-update-key-password" in printed)
        again = subprocess.run(["sh", script], env=env, capture_output=True, text=True, encoding="utf-8", timeout=120)
        check("173: a second run refuses and changes nothing, so a key in use is never replaced",
              again.returncode == 1 and "already holds" in again.stderr
              and (kc / "idiograph-update-key").read_text(encoding="utf-8") == made
              and (stubs / "cli-calls").read_text(encoding="utf-8").count("called") == 1)
        for n in ("idiograph-update-key", "idiograph-update-key-password"):
            (kc / n).unlink()
        (stubs / "fail").write_text("", encoding="utf-8")
        failed = subprocess.run(["sh", script], env=env, capture_output=True, text=True, encoding="utf-8", timeout=120)
        check("173: a CLI that fails stops it with the CLI's words, any key in them hidden, and nothing is kept",
              failed.returncode == 1 and "<key>" in failed.stderr and "dW50cnVzdGVk" not in failed.stderr
              and list(kc.iterdir()) == [] and list(tmp.iterdir()) == [])
        check("173: with the Keychain's stand-in, the script never runs security, and without it puts each item in "
              "through security -i on standard input, never on security's own command line",
              not (stubs / "security-calls").exists() and "| security -i" in key_sh
              and "add-generic-password -a" in key_sh and "-w \"$(" not in key_sh and "-U" not in key_sh
              and "trap 'rm -rf \"$work\"' EXIT" in key_sh)

    # ── D. the bundle: Tauri's, around the frozen server
    frozen = base / "frozen"
    (frozen / "_internal").mkdir(parents=True)
    (frozen / "_internal" / "Python.real").write_bytes(b"invented")
    try:
        (frozen / "_internal" / "Python").symlink_to("Python.real")
        links = True
    except OSError:
        links = False
    staged = window.stage_source(base / "stage", frozen)
    root = base / "stage" / "tauri"
    check("173: the window's source is laid out outside the checkout as the app's folder holds it, so tauri.conf.json's "
          "paths find the frozen server and the manual there, its links kept as links",
          staged == root / "packaging" / "tauri" / "src-tauri" and (staged / "tauri.conf.json").is_file()
          and (staged.parent / "window.js").is_file() and (root / "docs" / "manual.md").is_file()
          and (not links or (root / "build" / "tauri-server" / "_internal" / "Python").is_symlink())
          and not (staged / "target").exists())
    built_in = [(rs.name, inc) for rs in sorted((staged / "src").glob("*.rs"))
                for inc in re.findall(r'include_(?:str|bytes)!\("([^"]+)"\)', rs.read_text(encoding="utf-8"))]
    check("173: every file the window's source builds in (include_str!) is found from the staged source, as the "
          "Mac and Windows builds compile it there, English's menus among them (the 0.9.11 tag run)",
          built_in and all((staged / "src" / inc).resolve().is_file() for _, inc in built_in)
          and any(inc.endswith("i18n/en/menus.json") for _, inc in built_in),
          str([b for b in built_in if not (staged / "src" / b[1]).resolve().is_file()]))
    if links:
        twice = window.update_tarball(fake_app(base / "app-again", "Idiograph", FAT), base / "again.tar.gz")
        again_bytes = window.update_tarball(base / "app-again" / "Idiograph.app", base / "again2.tar.gz").read_bytes()
        with tarfile.open(twice) as tar:
            names = tar.getnames()
            link = tar.getmember("Idiograph.app/Contents/Resources/server/_internal/Python")
        check("173: the Mac's update file holds the app under its own name at its top, its links as links, the same "
              "app making the same file",
              names[0] == "Idiograph.app" and all(n.startswith("Idiograph.app") for n in names) and link.issym()
              and link.linkname == "Python.real" and twice.read_bytes() == again_bytes)
    else:
        skip("173: the Mac's update file keeps links", "this machine makes no links")
    check("173: a build lays the server's version and, for a check, the test app's identity over tauri.conf.json, and "
          "on a Mac the frozen server goes in through files, which keeps its links, where resources copied each as a file",
          window.overrides("0.9.1") == {"version": "0.9.1"}
          and window.overrides("0.9.1", test=True)["identifier"] == "uk.co.adamknowles.idiograph.test"
          and mac_conf == {"bundle": {"macOS": {"files": {"Resources/server": "../../../build/tauri-server"}}}}
          and json.loads(read(src / "tauri.windows.conf.json"))["bundle"]["resources"] == {"../../../build/tauri-server/": "server/"}
          and "../../../build/tauri-server/" not in conf["bundle"]["resources"]
          and window.cli_command({"IDIOGRAPH_TAURI_CLI": "/x/tauri.js"}) == ["node", "/x/tauri.js"]
          and window.cli_command({})[-2:] == ["--yes", "@tauri-apps/cli@2.12.1"] and window.TAURI_CLI == "2.12.1"
          and window.build_command(["t"], ["app", "dmg"], Path("c.json"), True, ["drive"])
          == ["t", "build", "--bundles", "app,dmg", "--config", "c.json", "--target", "universal-apple-darwin", "--features", "drive"])

    # ── E. what the second build's screenshots found, the parts that behave
    check("173: the server's queue of connections waiting to be taken is 128 long, where five let Windows refuse the "
          "burst two windows make reloading at once after a Restart, so a page came back without its script",
          server_mod.AppServer.request_queue_size == 128 and issubclass(server_mod.AppServer, server_mod.ThreadingHTTPServer)
          and 'server = AppServer(("127.0.0.1", args.port), Handler)' in read(support.source("family/server.py")))
    node = shutil.which("node")
    if node:
        harness = base / "recent.js"
        harness.write_text(js_function(app_js, "recentNames") + r"""
const list = [
  { part: 'sift', name: 'Dog routines', folder: '/w/sift-a' },
  { part: 'distil', name: 'Living with a dog', id: '/w/Dogs at home' },
  { part: 'distil', name: 'Walks', id: '/w/walks' },
  { part: 'distil', name: 'Living with a dog', id: 'demo', demo: true },
  { part: 'trace', name: 'Dog routines', folder: '/w/trace' },
  { part: 'trace', name: 'Notes', folder: '/a/same' },
  { part: 'trace', name: 'notes', folder: '/b/same' },
];
console.log(JSON.stringify(recentNames(list).map((r) => r.name)));
""", encoding="utf-8")
        ran = subprocess.run([node, str(harness)], capture_output=True, text=True, encoding="utf-8")
        try:
            names = json.loads(ran.stdout.strip().splitlines()[-1])
        except (ValueError, IndexError):
            names = []
        check("173: Open Recent tells two projects of a part with one name apart, the demo by its tag's word and any "
              "other by its folder's name, then its whole folder, and leaves a name no other shares as it is",
              names == ["Dog routines", "Living with a dog (Dogs at home)", "Walks", "Living with a dog (demo)",
                        "Dog routines", "Notes (/a/same)", "notes (/b/same)"], ran.stderr[-300:] or str(names))
    else:
        skip("173: Open Recent's names under node", "node is not on this machine")

    # ── F. the workflows and the checks on GitHub (21 October, for the public copy): the suite on every pull
    # request, on Windows, a Mac and Linux, never as pull_request_target, so a fork's run has no secret and
    # a read-only token, and the release alone may write, on a tag. A push to main runs nothing (23 October)
    jobs = "\n" + main_yml.split("\njobs:\n", 1)[1] if "\njobs:\n" in main_yml else ""
    on = main_yml.split("\non:\n", 1)[1].split("\npermissions:", 1)[0] if "\non:\n" in main_yml else ""
    release_job = jobs.split("\n  release:\n", 1)[1].split("\n  macos:\n", 1)[0] if "\n  release:\n" in jobs else ""
    check("173, updated 23 October: the suite runs on every pull request, never on a push to main, on Windows, a "
          "Mac and Linux, never as pull_request_target, with no secret, and only the release on a tag may write",
          "\n  pull_request:\n" in on and "pull_request_target" not in main_yml and "branches:" not in on
          and "\n  windows:\n" in jobs and "\n  macos:\n" in jobs and "\n  linux:\n" in jobs
          and "runs-on: ubuntu-latest" in jobs.split("\n  linux:\n", 1)[-1]
          and "\npermissions:\n  contents: read\n" in main_yml and "contents: write" in release_job
          and "if: github.ref_type == 'tag'" in release_job and main_yml.count("contents: write") == 1
          and "secrets." not in main_yml and not (workflows / "tauri.yml").exists())


    # ── G. kept here once for the whole suite since the review of 18 October (testreview3): the README's
    # length, the skill a user installs matching agents.md, and no study's pseudonym in what a release ships
    check("173: README stays under 1,000 words", len(readme.split()) < 1000, f"{len(readme.split())} words")
    guide, skill = read(support.source("docs/agents.md")), read(support.source("skills/idiograph/SKILL.md"))
    check("173: the skill a user installs ends with agents.md word for word",
          "\n---\n\n" in skill and skill.split("\n---\n\n", 1)[1] == guide)
    shipped = "\n".join([whats_new, minisign_src, release_src, key_sh, bundle_src, read(src / "windows" / "hooks.nsh")])
    check("173: the release notes and the release's code name no study's pseudonym",
          not any(re.search(rf"\b{n}\b", shipped) for n in STUDY_PSEUDONYMS))
