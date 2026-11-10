#!/usr/bin/env python3
"""Release a version of Idiograph to the testers' updaters, on Adam's Mac, on his word (17 October 2026,
the third Tauri build).

    python3 packaging/release.py v0.9.1 --dry-run   # everything but the upload, into build/release/v0.9.1
    python3 packaging/release.py v0.9.1             # and then the upload, the release public at once
    python3 packaging/release.py v0.9.1 --draft     # the upload as a draft, which he publishes on GitHub

A version tag `v` and its number, pushed to the app's repository, builds both installers on GitHub's
machines and puts them on a draft release there (`.github/workflows/windows-installer.yml`). This
script then:

1. Collects the three files from that draft with `gh`: `Idiograph.dmg` for a first install on a Mac,
   `Idiograph.app.tar.gz`, the Mac app as Tauri's updater takes it, and `Idiograph-Setup.exe`, which
   installs on Windows and updates there too. And, when the draft has them (the Linux job is allowed to
   fail while it is new, linux57, 9 November 2026), `Idiograph-x86_64.AppImage`, the Linux download and
   the file Tauri's updater replaces in place, and `Idiograph-amd64.deb` for Ubuntu, Debian and Mint,
   which cannot update itself and is not in the manifest.
2. Reads the notes for this version from `docs/whats-new.md`, its section of eight lines or fewer.
3. Reads the update key from the macOS Keychain, `idiograph-update-key` and its password
   `idiograph-update-key-password`, which `packaging/make_update_key.sh` put there, through `security`
   at the moment it signs. Neither is ever printed, written to a file or passed on a command line, and
   neither is a GitHub secret. A key whose public half is not the one in `tauri.conf.json` is refused,
   since every copy of the app checks against that one: Adam's own since 18 October (the fifth Tauri
   build), key 3CEA6A356EFB3E63, where a placeholder that refused every key had stood.
4. Signs every update file (the Mac's, the Windows installer and the AppImage), binding each signature to this version as `tauri signer sign
   --app-version` does, checks every signature again with the public key, and writes `latest.json` in
   Tauri's updater's form: the version, the date, the notes and, for each system, the file's address and
   its signature. The Mac app is for Apple Silicon alone, `darwin-aarch64` and no `darwin-x86_64` (relfix,
   9 November 2026), and one whose executable has no arm64 part is refused. The AppImage is `linux-x86_64`,
   and a release with no AppImage has no such entry.
5. Writes the release's notes, `notes.md`: the version's lines and a table, "Which file do I need?", each
   computer's download linked under this release (`which_file`).
6. Publishes the release with `gh` to every repository in `names(app)["repos"]`: the app's own,
   Pharkie/idiograph, where every copy from 0.9.24 on asks for `releases/latest/download/latest.json`,
   and, for the transitional 0.9.24 (pubreadme, 10 November 2026, Adam's ruling about 12:50), the old
   public releases repository, Pharkie/idiograph-releases, where every older copy asks, so they update to
   a copy that asks the new one (`ALSO`). Each repository gets its own `latest.json` and notes, every
   address in them on that repository. On the app's own repository the tag's draft release, which holds
   the files already, becomes the release: `latest.json` added and the draft published. A repository
   that has the version published already is passed over, so a run that failed half way finishes the
   rest, and an archived one is passed over too, so once idiograph-releases is archived the releases go
   to Pharkie/idiograph alone with nothing changed here.

`--from <folder>` takes the three files from a folder in place of the draft. A folder a signing run
has already written, with `latest.json` and `notes.md` beside the files, is uploaded as it is, its
signatures checked again with the public key and nothing signed twice: when an upload fails, the script
says the line that finishes it, `release.py <tag> --from build/release/<tag>`. `--test-key
<folder>` signs with a throwaway key made there, `update.key`, its password in `update.key.password`
and its public half in `update.key.pub`, in place of the Keychain's and tauri.conf.json's: the checks'
own hook (area 173), never for a release. With it, `--whats-new <file>` reads a check's own notes in
place of docs/whats-new.md, for a test release proved end to end (area 175, the fourth Tauri build).

Each app released on its own (20 October, the three-app split's build 6): the tag names the app,
`sift-v1.0.0` Sift's 1.0.0, `trace-v1.0.0` Trace's, and a bare `v0.9.3` (or `idiograph-v0.9.3`)
Idiograph's. The workflow builds only the tagged app, and this script takes that app's three files
(`Sift.dmg`, `Sift.app.tar.gz`, `Sift-Setup.exe`), its notes (`docs/whats-new-sift.md`), its version in
versions.json and its own releases repository (`Pharkie/sift-releases`). `--app` may name the app as
well, and is refused when the tag names another. One update key signs all three apps. A dry run says
what it would publish, where and under which tag, and uploads nothing.
"""
from __future__ import annotations

import argparse
import base64
import getpass
import json
import os
import re
import shutil
import struct
import subprocess
import sys
import tarfile
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
TOOL = HERE.parent
sys.path.insert(0, str(HERE))

import minisign  # noqa: E402  the signatures Tauri's updater checks, beside this file
sys.path.insert(1, str(TOOL))
import boot  # noqa: E402  the family's folders on the path (boot.py)
boot.setup()
import app_identity  # noqa: E402  each app's version, from versions.json at the top

# the codebase's repository, whose draft releases hold every app's builds
APP_REPO = "Pharkie/idiograph"
# Idiograph's releases repository and files, `names` giving each app's (Sift's in Pharkie/sift-releases):
# its own repository's releases since 0.9.24 (pubreadme, 10 November 2026), app_identity's `releases`
RELEASES_REPO = "Pharkie/idiograph"
# the repositories a release goes to as well as the app's own: the old releases repository, for the
# transitional 0.9.24, so the copies that ask it update to one that asks Pharkie/idiograph. Archived after,
# it is passed over by itself (`archived`)
ALSO = {"idiograph": ("Pharkie/idiograph-releases",)}
# what a release's notes say each computer downloads, in the order the table lists them, by the key in `names`
WHICH_FILE = (("Mac with Apple Silicon (M1 or later)", "dmg"), ("Windows", "windows"),
              ("Linux: Ubuntu or Debian", "deb"), ("Linux: any other", "linux"))
# the three files a version ships as, the names the draft and the releases repository give them
DMG, MAC_UPDATE, WINDOWS = "Idiograph.dmg", "Idiograph.app.tar.gz", "Idiograph-Setup.exe"
FILES = (DMG, MAC_UPDATE, WINDOWS)
# the Linux pair, which a release carries when the Linux job made them: the AppImage is the download and
# the update file, the .deb a download alone
LINUX, DEB = "Idiograph-x86_64.AppImage", "Idiograph-amd64.deb"
LINUX_FILES = (LINUX, DEB)
MANIFEST = "latest.json"
# the Keychain's two items, as make_update_key.sh names them
KEY_ITEM, PASSWORD_ITEM = "idiograph-update-key", "idiograph-update-key-password"
WHATS_NEW = TOOL / "docs" / "whats-new.md"
CONF = HERE / "tauri" / "src-tauri" / "tauri.conf.json"
NOTES_LINES = 8
# how a release is uploaded, a name the checks stand in for, so nothing of theirs reaches GitHub
GH = ["gh"]
# what reads one Keychain item's secret, a name the checks stand in for, so they never touch it
SECURITY = ["security", "find-generic-password", "-a", getpass.getuser(), "-w", "-s"]
# a Mach-O's architectures by their CPU type, as a fat file lists them
CPU = {0x01000007: "x86_64", 0x0100000C: "aarch64"}
# the one Mac the updater is offered to, Apple Silicon (relfix, 9 November 2026): Intel Macs keep the copy they have
MAC_ARCH = "aarch64"
MAC_PLATFORM = f"darwin-{MAC_ARCH}"


class Refused(SystemExit):
    """The release stopped, in one line, with nothing uploaded."""


def say(line: str) -> None:
    print(line, flush=True)


# ── the version and its notes ───────────────────────────────────────────────────────────────────

# a version tag: the app's name and a hyphen, or nothing for Idiograph, then v and three numbers
TAG = re.compile(r"(?:(idiograph|sift|trace)-)?v(\d+\.\d+\.\d+)")


def tag_app(tag: str) -> tuple[str, str]:
    """The app a tag is for and its version: `sift-v1.0.0` Sift's 1.0.0, `trace-v1.0.0` Trace's, and
    `v0.9.3` or `idiograph-v0.9.3` Idiograph's. Anything else is refused."""
    m = TAG.fullmatch(tag.strip())
    if not m:
        raise Refused(f"{tag} is not a version tag: v and three numbers for Idiograph, v0.9.1, or the app's "
                      "name first for Sift or Trace, sift-v1.0.0.")
    return m.group(1) or app_identity.DEFAULT, m.group(2)


def version_of(tag: str) -> str:
    return tag_app(tag)[1]


def names(app: str = app_identity.DEFAULT) -> dict:
    """What a release of `app` holds and where it goes: its three files, `Sift.dmg`, `Sift.app.tar.gz` and
    `Sift-Setup.exe` for Sift, the two Linux files it may also hold (`linux`, `Sift-x86_64.AppImage`, and
    `deb`, `Sift-amd64.deb`), its notes file and its own releases repository."""
    ident = app_identity.APPS[app_identity.check(app)]
    name = ident["name"]
    dmg, mac_update, windows = f"{name}.dmg", f"{name}.app.tar.gz", f"{name}-Setup.exe"
    linux, deb = f"{name}-x86_64.AppImage", f"{name}-amd64.deb"
    return {"name": name, "dmg": dmg, "mac_update": mac_update, "windows": windows, "files": (dmg, mac_update, windows),
            "linux": linux, "deb": deb, "linux_files": (linux, deb),
            "repo": ident["releases"], "repos": (ident["releases"], *ALSO.get(ident["id"], ())),
            "whats_new": WHATS_NEW if ident["id"] == app_identity.DEFAULT else TOOL / "docs" / ident["whats_new"]}


def server_version(app: str = app_identity.DEFAULT) -> str:
    """The app's own version, its entry in versions.json, which the server reads too."""
    return app_identity.version(app)


def notes_for(version: str, text: str | None = None, app: str = app_identity.DEFAULT) -> tuple[str, str]:
    """The date and the notes of `version` in the app's What's new, docs/whats-new.md for Idiograph and
    docs/whats-new-sift.md for Sift, or the text given: its heading, `## 0.9.1, 17 October 2026`, and the
    lines under it, eight or fewer."""
    path = names(app)["whats_new"]
    shown = f"docs/{path.name}"
    if text is None:
        if not path.is_file():
            raise Refused(f"There is no {shown} yet, so {names(app)['name']} has no notes to release.")
        text = path.read_text(encoding="utf-8")
    m = re.search(rf"^## {re.escape(version)}, ([^\n]+)\n(.*?)(?=^## |\Z)", text, re.M | re.S)
    if not m:
        raise Refused(f"{shown} has no section for {version}.")
    lines = [ln.strip() for ln in m.group(2).strip().splitlines() if ln.strip()]
    if not lines:
        raise Refused(f"{shown} says nothing under {version}.")
    if len(lines) > NOTES_LINES:
        raise Refused(f"{shown} has {len(lines)} lines under {version}, and {NOTES_LINES} is the most.")
    return m.group(1).strip(), "\n".join(lines)


# ── the files ───────────────────────────────────────────────────────────────────────────────────

def collect(tag: str, into: Path, source: Path | None, app: str = app_identity.DEFAULT) -> dict[str, Path]:
    """The three files of the app's version, and the Linux AppImage and .deb when the release has them, from
    the codebase's draft release, or from `source`, into `into`."""
    files, linux = names(app)["files"], names(app)["linux_files"]
    into.mkdir(parents=True, exist_ok=True)
    if source:
        for name in (*files, *linux):
            if (source / name).is_file() and (into / name).resolve() != (source / name).resolve():
                shutil.copyfile(source / name, into / name)
    else:
        run_gh(["release", "download", tag, "--repo", APP_REPO, "--dir", str(into), "--clobber",
                *[arg for name in files for arg in ("--pattern", name)]])
        # the Linux files on their own, since gh refuses a pattern that matches nothing and a release
        # whose Linux job failed has none (that, and only that, is not a fault)
        try:
            run_gh(["release", "download", tag, "--repo", APP_REPO, "--dir", str(into), "--clobber",
                    *[arg for name in linux for arg in ("--pattern", name)]], capture=True)
        except subprocess.CalledProcessError as exc:
            if "no assets match" not in (exc.stderr or "") + (exc.stdout or ""):
                raise
    missing = [name for name in files if not (into / name).is_file()]
    if missing:
        raise Refused(f"The release {tag} lacks {', '.join(missing)}.")
    held = [name for name in (*files, *linux) if (into / name).is_file()]
    if names(app)["linux"] not in held:
        say("Note: the release has no Linux AppImage, so it goes out for the Mac and Windows alone.")
        held = [name for name in held if name not in linux]
    return {name: into / name for name in held}


def mac_archs(update: Path) -> list[str]:
    """The architectures the Mac app in its update file runs on, from its executable's own header."""
    with tarfile.open(update, "r:gz") as tar:
        exe = next((m for m in tar.getmembers() if re.fullmatch(r"[^/]+\.app/Contents/MacOS/[^/]+", m.name) and m.isfile()), None)
        if exe is None:
            raise Refused(f"{update.name} holds no app.")
        head = tar.extractfile(exe).read(4096)
    magic = struct.unpack(">I", head[:4])[0]
    if magic in (0xCAFEBABE, 0xCAFEBABF):
        count = struct.unpack(">I", head[4:8])[0]
        step = 20 if magic == 0xCAFEBABE else 32
        types = [struct.unpack(">I", head[8 + i * step:12 + i * step])[0] for i in range(count)]
    elif magic in (0xCFFAEDFE, 0xCEFAEDFE):
        types = [struct.unpack("<I", head[4:8])[0]]
    else:
        raise Refused(f"{update.name}'s app has no Mac executable.")
    archs = sorted({CPU[t] for t in types if t in CPU})
    if not archs:
        raise Refused(f"{update.name}'s app is for no Mac this release knows.")
    return archs


# ── the key ─────────────────────────────────────────────────────────────────────────────────────

def keychain(item: str) -> str:
    """One item's secret from the login Keychain, read as it is needed and never shown."""
    try:
        done = subprocess.run([*SECURITY, item], capture_output=True, text=True, encoding="utf-8", timeout=120)
    except (OSError, subprocess.TimeoutExpired):
        done = None
    if done is None or done.returncode != 0 or not done.stdout.strip():
        raise Refused(f"The Keychain has no {item}. Make the key once with packaging/make_update_key.sh.")
    return done.stdout.strip()


def conf_public_key() -> str:
    return json.loads(CONF.read_text(encoding="utf-8")).get("plugins", {}).get("updater", {}).get("pubkey", "")


def update_key(test_key: Path | None) -> tuple[minisign.SecretKey, str]:
    """The secret key opened, and the public key every copy of the app checks against: the Keychain's
    and tauri.conf.json's, or for a check the throwaway pair in `test_key`."""
    if test_key:
        blob = (test_key / "update.key").read_text(encoding="utf-8").strip()
        password = (test_key / "update.key.password").read_text(encoding="utf-8").strip()
        public = (test_key / "update.key.pub").read_text(encoding="utf-8").strip()
    else:
        blob, password, public = keychain(KEY_ITEM), keychain(PASSWORD_ITEM), conf_public_key()
    try:
        minisign.read_public(public)
    except minisign.BadKey:
        raise Refused("tauri.conf.json has no public key yet, so every copy would refuse this release. "
                      "Put in the one packaging/make_update_key.sh printed.")
    try:
        key = minisign.open_secret(blob, password)
    except minisign.BadKey as exc:
        raise Refused(f"The update key did not open: {exc}.")
    if key.public_key() != public:
        raise Refused("The update key is not the one tauri.conf.json names, so every copy would refuse this release.")
    return key, public




# ── the manifest ────────────────────────────────────────────────────────────────────────────────

def download_url(tag: str, name: str, app: str = app_identity.DEFAULT) -> str:
    return f"https://github.com/{names(app)['repo']}/releases/download/{tag}/{name}"


def manifest(version: str, tag: str, notes: str, signatures: dict[str, str],
             now: datetime | None = None, app: str = app_identity.DEFAULT) -> dict:
    """latest.json in Tauri's updater's form, for the app's own releases repository, the Mac's entry
    Apple Silicon's alone."""
    named = names(app)
    mac, windows = named["mac_update"], named["windows"]
    platforms = {MAC_PLATFORM: {"signature": signatures[mac], "url": download_url(tag, mac, app)}}
    platforms["windows-x86_64"] = {"signature": signatures[windows], "url": download_url(tag, windows, app)}
    if named["linux"] in signatures:
        platforms["linux-x86_64"] = {"signature": signatures[named["linux"]], "url": download_url(tag, named["linux"], app)}
    when = (now or datetime.now(timezone.utc)).replace(microsecond=0)
    return {"version": version, "notes": notes, "pub_date": when.isoformat().replace("+00:00", "Z"),
            "platforms": platforms}


def for_repo(text: str, repo: str, app: str = app_identity.DEFAULT) -> str:
    """A manifest's or a notes file's text with every address on the app's own releases repository moved
    to `repo`'s, so each repository a release goes to holds its own files' addresses. The signatures do not
    change: they are the files', never the addresses'."""
    own = names(app)["repo"]
    return text if repo == own else text.replace(f"https://github.com/{own}/releases/", f"https://github.com/{repo}/releases/")


def which_file(tag: str, held, app: str = app_identity.DEFAULT) -> str:
    """The notes' table, "Which file do I need?": each computer and its download in this release, linked on
    the app's own releases repository, the Linux rows only when the release has their files."""
    named = names(app)
    rows = [f"| {computer} | [{named[key]}]({download_url(tag, named[key], app)}) |"
            for computer, key in WHICH_FILE if named[key] in held]
    return "\n".join(["### Which file do I need?", "", "| Your computer | The file |", "| --- | --- |", *rows, "",
                      "The other files are for the app's own updates."])


def sign_all(key: minisign.SecretKey, public: str, files: dict[str, Path], version: str,
             app: str = app_identity.DEFAULT) -> dict[str, str]:
    """Every update file signed for this version (the Mac's, the Windows installer and, when the release has
    it, the Linux AppImage), each signature written beside its file and checked again with the public key
    before anything else happens. The .deb is never signed: the updater does not take it."""
    signatures = {}
    for name in (names(app)["mac_update"], names(app)["windows"], names(app)["linux"]):
        if name not in files:
            continue
        data = files[name].read_bytes()
        signature = minisign.sign(key, data, minisign.trusted_comment(name, version))
        if minisign.verify(public, data, signature) is None:
            raise Refused(f"The signature of {name} did not check, so nothing was uploaded.")
        files[name].with_name(name + ".sig").write_text(signature, encoding="utf-8")
        signatures[name] = signature
    return signatures


def check_manifest(data: dict, public: str, files: dict[str, Path], version: str,
                   app: str = app_identity.DEFAULT) -> list[str]:
    """What is wrong with a manifest, as an updater sees it: each system's signature against its own
    file and the version, every address on the app's releases repository. Empty when nothing is."""
    repo = names(app)["repo"]
    wrong = []
    if data.get("version") != version:
        wrong.append(f"the version {data.get('version')} is not {version}")
    if MAC_PLATFORM not in data.get("platforms", {}):
        wrong.append(f"there is no {MAC_PLATFORM}")
    for platform in sorted(data.get("platforms", {})):
        if platform.startswith("darwin-") and platform != MAC_PLATFORM:
            wrong.append(f"{platform} is listed, and the Mac app is for Apple Silicon alone")
    for platform, entry in sorted(data.get("platforms", {}).items()):
        name = entry.get("url", "").rsplit("/", 1)[-1]
        if not entry.get("url", "").startswith(f"https://github.com/{repo}/releases/download/"):
            wrong.append(f"{platform}'s address is not on {repo}")
        if name not in files:
            wrong.append(f"{platform} names {name}, which is not in the release")
            continue
        comment = minisign.verify(public, files[name].read_bytes(), entry.get("signature", ""))
        if comment is None:
            wrong.append(f"{platform}'s signature does not check against {name}")
        elif f"version:{version}" not in comment.split("\t"):
            wrong.append(f"{platform}'s signature is not for {version}")
    return wrong


# ── the upload ──────────────────────────────────────────────────────────────────────────────────

def run_gh(args: list[str], capture: bool = False) -> subprocess.CompletedProcess:
    return subprocess.run([*GH, *args], check=True, text=True, encoding="utf-8", capture_output=capture)


def upload(tag: str, version: str, notes: Path, files: list[Path], draft: bool, app: str = app_identity.DEFAULT,
           repo: str | None = None) -> None:
    """The release made on one repository, the app's releases repository unless `repo` names another: a
    draft of the tag there (the app's own repository's) given latest.json and published, or else a new
    release, the repository's first commit made first when it has none, since GitHub tags a release on a
    commit. A version published there already is never replaced (`targets` passes it over)."""
    repo = repo or names(app)["repo"]
    name = names(app)["name"]
    title = f"{name} {version}"
    if release_state(tag, repo) == "draft":
        # the app's own repository, whose draft holds the tag's files: latest.json added, and published
        run_gh(["release", "upload", tag, "--repo", repo, "--clobber", *[str(f) for f in files]])
        run_gh(["release", "edit", tag, "--repo", repo, "--title", title, "--notes-file", str(notes),
                *([] if draft else ["--draft=false"])])
        return
    if repo_empty(repo):
        readme = (f"# {name} releases\n\nThe versions of {name} its updater installs. "
                  "Each release holds the Mac disk image, the Windows installer, the Linux AppImage and .deb "
                  "and latest.json.\n")
        run_gh(["api", "-X", "PUT", f"repos/{repo}/contents/README.md", "-f", f"message={name} releases",
                "-f", f"content={base64.b64encode(readme.encode()).decode()}"])
    run_gh(["release", "create", tag, "--repo", repo, "--title", title,
            "--notes-file", str(notes), *(["--draft"] if draft else []), *[str(f) for f in files]])


def repo_empty(repo: str) -> bool:
    """Whether the repository has no commit yet, from GitHub's answer for its newest one: a 409, "Git
    Repository is empty", when it has none. Never its size, which GitHub gives as 0 KB for one holding a
    short README alone (22 October, the 0.9.3 release). Any other failure is said, never taken for empty."""
    done = subprocess.run([*GH, "api", f"repos/{repo}/commits?per_page=1", "--jq", "length"], capture_output=True,
                          text=True, encoding="utf-8")
    if done.returncode == 0:
        return False
    said = ((done.stderr or "") + (done.stdout or "")).strip()
    if "Git Repository is empty" in said:
        return True
    raise Refused(f"GitHub did not say whether {repo} has a commit: {said.splitlines()[-1] if said else done.returncode}.")


def release_state(tag: str, repo: str) -> str:
    """Whether `repo` has the tag's release: "none", "draft" or "published"."""
    done = subprocess.run([*GH, "release", "view", tag, "--repo", repo, "--json", "isDraft", "--jq", ".isDraft"],
                          capture_output=True, text=True, encoding="utf-8")
    if done.returncode != 0:
        return "none"
    return "draft" if done.stdout.strip() == "true" else "published"


def releases_has(tag: str, app: str = app_identity.DEFAULT, repo: str | None = None) -> bool:
    return release_state(tag, repo or names(app)["repo"]) == "published"


def archived(repo: str) -> bool:
    """Whether GitHub says the repository is archived, where nothing can be published."""
    done = subprocess.run([*GH, "repo", "view", repo, "--json", "isArchived", "--jq", ".isArchived"],
                          capture_output=True, text=True, encoding="utf-8")
    return done.returncode == 0 and done.stdout.strip() == "true"


def targets(tag: str, app: str = app_identity.DEFAULT) -> list[str]:
    """The repositories this release still goes to, in order: each of the app's, less one that is archived
    or has the version published already, each said. None left is refused: a version is released once."""
    repos, left = names(app)["repos"], []
    for repo in repos:
        if repo != names(app)["repo"] and archived(repo):
            say(f"{repo} is archived, so the release does not go there.")
        elif releases_has(tag, app, repo):
            say(f"{repo} has {tag} already, left as it is.")
        else:
            left.append(repo)
    if not left:
        raise Refused(f"{' and '.join(repos)} already {'have' if len(repos) > 1 else 'has'} {tag}. "
                      "A version is released once.")
    return left


def which(value: str) -> str:
    """The lines the workflow adds to its environment for the app a run builds, from a tag or an app's
    name: `APP=sift` and `APP_NAME=Sift` for `sift-v1.0.0` or `sift`, so the rule from tag to app is
    written once, here (`tag_app`)."""
    name = value.strip().lower()
    app = name if name in app_identity.APPS else tag_app(value)[0]
    return f"APP={app}\nAPP_NAME={names(app)['name']}\n"


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Sign a version's update files, write latest.json and upload them.")
    ap.add_argument("tag", nargs="?", help="the version's tag: v and its number for Idiograph, v0.9.1, the app's name "
                                           "first for Sift or Trace, sift-v1.0.0")
    ap.add_argument("--which", metavar="TAG_OR_APP", help="say only which app a tag or a name is, as the workflow reads it")
    ap.add_argument("--app", choices=list(app_identity.APPS), help="the app released, which the tag names already")
    ap.add_argument("--dry-run", action="store_true", help="everything but the upload, saying what it would publish")
    ap.add_argument("--draft", action="store_true", help="upload as a draft, published by hand on GitHub")
    ap.add_argument("--from", dest="source", help="take the three files from this folder, not the draft release")
    ap.add_argument("--out", help="the folder the files and latest.json go in, build/release/<tag> by default")
    ap.add_argument("--test-key", help="a check's throwaway key pair in this folder, never the Keychain's")
    ap.add_argument("--whats-new", help="with --test-key, a check's own notes in place of the app's What's new")
    args = ap.parse_args(argv)
    if args.which:
        # the bytes as they are, so Windows writes no carriage return into the workflow's environment
        sys.stdout.buffer.write(which(args.which).encode("utf-8"))
        sys.stdout.flush()
        return 0
    if not args.tag:
        raise Refused("Name the version's tag, v0.9.1 for Idiograph or sift-v1.0.0 for Sift.")

    app, version = tag_app(args.tag)
    if args.app and args.app != app:
        raise Refused(f"The tag {args.tag} is {names(app)['name']}'s, not {names(args.app)['name']}'s.")
    named = names(app)
    if not args.test_key and version != server_version(app):
        raise Refused(f"versions.json says {server_version(app)} for {named['name']}, and the tag {args.tag}.")
    if args.whats_new and not args.test_key:
        raise Refused("--whats-new is a check's, with --test-key alone.")
    date, notes = notes_for(version, Path(args.whats_new).read_text(encoding="utf-8") if args.whats_new else None, app)
    source = Path(args.source).expanduser().resolve() if args.source else None
    out = Path(args.out).expanduser().resolve() if args.out else TOOL / "build" / "release" / args.tag
    files = collect(args.tag, out, source, app)
    if source and (source / MANIFEST).is_file():
        return finish(args, app, version, source, out, files)
    if MAC_ARCH not in mac_archs(files[named["mac_update"]]):
        raise Refused(f"{named['mac_update']} is not for Apple Silicon, and the Mac app is for Apple Silicon alone.")
    key, public = update_key(Path(args.test_key).expanduser().resolve() if args.test_key else None)
    signatures = sign_all(key, public, files, version, app)
    data = manifest(version, args.tag, notes, signatures, app=app)
    wrong = check_manifest(data, public, files, version, app)
    if wrong:
        raise Refused("latest.json is wrong: " + "; ".join(wrong) + ".")
    (out / MANIFEST).write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    notes_file = out / "notes.md"
    notes_file.write_text(f"{named['name']} {version}, {date}\n\n{notes}\n\n{which_file(args.tag, files, app)}\n",
                          encoding="utf-8")
    on_linux = f" and {named['linux']} for Linux" if named["linux"] in files else ""
    say(f"Signed {named['mac_update']} for Apple Silicon and {named['windows']} for Windows{on_linux}, version "
        f"{version}, and wrote {MANIFEST} in {out}")
    shipped = [files[n] for n in (*named["files"], *named["linux_files"]) if n in files] + [out / MANIFEST]
    if args.dry_run:
        source = Path(args.whats_new).name if args.whats_new else f"docs/{named['whats_new'].name}"
        say(f"Would publish {named['name']} {version} to {' and '.join(named['repos'])} as {args.tag}"
            f"{', a draft' if args.draft else ''}: {', '.join(p.name for p in shipped)}, with the notes from {source} "
            "and the table of which file to download.")
        say("Dry run: nothing uploaded.")
        return 0
    return send(args, app, version, out, notes_file, shipped)


def finish(args, app: str, version: str, source: Path, out: Path, files: dict[str, Path]) -> int:
    """A folder a signing run wrote, uploaded as it is: its latest.json checked again against the files
    with the public key, so nothing is signed twice and nothing changed since goes out."""
    named = names(app)
    if args.test_key:
        public = (Path(args.test_key).expanduser().resolve() / "update.key.pub").read_text(encoding="utf-8").strip()
    else:
        public = conf_public_key()
    try:
        data = json.loads((source / MANIFEST).read_text(encoding="utf-8"))
    except ValueError:
        data = {}
    wrong = check_manifest(data, public, files, version, app)
    if wrong:
        raise Refused(f"{MANIFEST} in {source} is wrong: " + "; ".join(wrong) + ". Take it out of the folder to sign again.")
    if not (source / "notes.md").is_file():
        raise Refused(f"{source} has {MANIFEST} but no notes.md. Take {MANIFEST} out of the folder to sign again.")
    for name in (MANIFEST, "notes.md"):
        if (out / name).resolve() != (source / name).resolve():
            shutil.copyfile(source / name, out / name)
    say(f"{out} is signed for {version} already, its signatures checked again, so nothing is signed twice")
    shipped = [files[n] for n in (*named["files"], *named["linux_files"]) if n in files] + [out / MANIFEST]
    if args.dry_run:
        say(f"Would publish {named['name']} {version} to {' and '.join(named['repos'])} as {args.tag}"
            f"{', a draft' if args.draft else ''}: {', '.join(p.name for p in shipped)}, with the notes in notes.md.")
        say("Dry run: nothing uploaded.")
        return 0
    return send(args, app, version, out, out / "notes.md", shipped)


def send(args, app: str, version: str, out: Path, notes_file: Path, shipped: list[Path]) -> int:
    """The upload to each repository the release still goes to, each with its own latest.json and notes, their
    addresses on that repository (`for_repo`), and when one fails, the line that finishes it from the signed
    folder, which passes over the repositories done already."""
    named = names(app)
    done = []
    for repo in targets(args.tag, app):
        files, notes = shipped, notes_file
        if repo != named["repo"]:
            # the other repository's own manifest and notes, in a folder of their own beside the signed files
            there = out / ("to-" + repo.replace("/", "-"))
            there.mkdir(exist_ok=True)
            for name, source in ((MANIFEST, out / MANIFEST), ("notes.md", notes_file)):
                (there / name).write_text(for_repo(source.read_text(encoding="utf-8"), repo, app), encoding="utf-8")
            files = [there / MANIFEST if f.name == MANIFEST else f for f in shipped]
            notes = there / "notes.md"
        try:
            upload(args.tag, version, notes, files, args.draft, app, repo)
        except subprocess.CalledProcessError as exc:
            rest = [args.tag, "--from", str(out)] + (["--draft"] if args.draft else []) \
                + (["--test-key", args.test_key] if args.test_key else [])
            raise Refused(f"The upload to {repo} failed ({' '.join(map(str, exc.cmd[len(GH):len(GH) + 3]))}, "
                          f"exit {exc.returncode}){', after ' + ' and '.join(done) if done else ''}. The signed files "
                          f"are in {out}. Once the fault is mended, finish without signing again: python3 "
                          f"packaging/release.py {' '.join(rest)}")
        done.append(repo)
    say(f"Released {named['name']} {version} to {' and '.join(done)}" + (" as a draft." if args.draft else "."))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
