"""Area 355: the Linux download's updates and its release (linux57, 9 November 2026, builds 5 and 7 of the Linux
plan). `packaging/release.py` knows `linux-x86_64` beside `darwin-*` and `windows-x86_64`: the AppImage is the Linux
download and the file Tauri's updater replaces in place, signed with the same key and bound to the version, and the
.deb goes out beside it, unsigned and not in the manifest. A release whose Linux job failed has neither, and goes
out for the Mac and Windows alone. Here, on any machine: a fake release with all three systems through a dry run
with a throwaway key (the manifest's entries, each signature checked against its own file, no signature for the
.deb), the same without the Linux files, a changed AppImage refused, the names for Sift and Trace, the files
collected from a draft with a `gh` of the check's own (a draft with no Linux files tolerated, any other failure
not), the upload carrying the six files and latest.json, `release.py --which`, and the workflow read as text: the
steps of the release job in order, the Linux job's `ok` output, `linux-server` for a dispatch alone, and the
README's Linux line under 1,000 words. What only GitHub's machines prove (the AppImage itself, the artifact
hand-over) is not here. All made-up files. Nothing here uses a participant's words."""
from __future__ import annotations

import base64
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

from . import support
from .support import check
from .a173_release import FAT, fake_app


def job_block(workflow: str, job: str) -> str:
    """The text of one job under `jobs:`, from its two-space key to the next job's."""
    found = re.search(rf"^  {re.escape(job)}:\n(.*?)(?=^  [A-Za-z0-9_-]+:\n|\Z)", workflow, re.S | re.M)
    return found.group(1) if found else ""


def step_names(block: str) -> list[str]:
    """What each step of a job is called, its `name:`, else its `uses:` or the first line of its `run:`, in order."""
    steps = block.split("    steps:\n", 1)[1] if "    steps:\n" in block else ""
    out = []
    for chunk in re.split(r"^      - ", steps, flags=re.M)[1:]:
        found = re.search(r"(?:\A|^ {8})name: (.+)$", chunk, re.M) or re.search(r"uses: (\S+)", chunk) or re.search(r"run: (.+)", chunk)
        out.append(found.group(1).strip() if found else "?")
    return out


GH_STUB = (
    "import json, sys\nstate, args = sys.argv[1], sys.argv[2:]\n"
    "open(sys.argv[0] + '.' + state + '.log', 'a').write(json.dumps(args) + '\\n')\n"
    "if args[:2] == ['release', 'view']: sys.exit(1)\n"
    "if args[:1] == ['api']: print('1'); sys.exit(0)\n"
    "if args[:2] == ['release', 'download']:\n"
    "    pats = [args[i + 1] for i, a in enumerate(args) if a == '--pattern']\n"
    "    into = args[args.index('--dir') + 1]\n"
    "    linux = any('x86_64.AppImage' in p or 'amd64.deb' in p for p in pats)\n"
    "    if linux and state == 'nolinux':\n"
    "        sys.stderr.write('no assets match the file pattern\\n'); sys.exit(1)\n"
    "    if linux and state == 'broken':\n"
    "        sys.stderr.write('gh: Bad gateway (HTTP 502)\\n'); sys.exit(1)\n"
    "    for p in pats:\n"
    "        open(into + '/' + p, 'wb').write(b'made up ' + p.encode())\n"
)


def test_linux_release(scratch: Path):
    print("\n355. The Linux download's updates and release: linux-x86_64 in latest.json, the AppImage signed and the .deb not, "
          "a release without Linux files, the draft collected, the workflow's release job (linux57)")
    sys.path.insert(0, str(support.source("packaging")))
    sys.path.insert(0, str(support.source("packaging/tauri")))
    import importlib
    import minisign
    import release
    import bundle as window
    importlib.reload(minisign)

    read = lambda path: Path(path).read_text(encoding="utf-8")
    base = scratch / "release-355"
    shutil.rmtree(base, ignore_errors=True)
    base.mkdir(parents=True)

    key_dir = base / "key"
    key_dir.mkdir()
    password = "a throwaway password for sailing"
    blob = minisign.make_secret(password)
    public = minisign.open_secret(blob, password).public_key()
    (key_dir / "update.key").write_text(blob, encoding="utf-8")
    (key_dir / "update.key.password").write_text(password, encoding="utf-8")
    (key_dir / "update.key.pub").write_text(public, encoding="utf-8")

    # ── A. a fake release with all three systems, and the same with no Linux files
    builds = base / "builds"
    builds.mkdir()
    window.update_tarball(fake_app(base / "app-both", "Idiograph", FAT), builds / release.MAC_UPDATE)
    (builds / release.WINDOWS).write_bytes(b"MZ an installer of the check's own")
    (builds / release.DMG).write_bytes(b"a disk image of the check's own")
    (builds / release.LINUX).write_bytes(b"\x7fELF an AppImage of the check's own")
    (builds / release.DEB).write_bytes(b"!<arch> a .deb of the check's own")
    out = base / "out"

    def dry(source: Path, to: Path):
        done = subprocess.run([sys.executable, str(support.source("packaging/release.py")), "v0.9.1", "--from", str(source),
                               "--test-key", str(key_dir), "--out", str(to), "--dry-run"],
                              capture_output=True, text=True, encoding="utf-8", timeout=300)
        manifest = json.loads(read(to / "latest.json")) if (to / "latest.json").is_file() else {}
        return done, manifest

    done, manifest = dry(builds, out)
    platforms = manifest.get("platforms", {})
    files = {n: out / n for n in (*release.FILES, *release.LINUX_FILES)}
    check("355: a dry run on a release with the Mac, Windows and Linux files writes latest.json with all three systems, "
          "linux-x86_64 naming the AppImage on the releases repository, and uploads nothing",
          done.returncode == 0 and sorted(platforms) == ["darwin-aarch64", "linux-x86_64", "windows-x86_64"]
          and platforms["linux-x86_64"]["url"] == "https://github.com/Pharkie/idiograph/releases/download/v0.9.1/Idiograph-x86_64.AppImage"
          and "Dry run: nothing uploaded." in done.stdout and "Idiograph-x86_64.AppImage for Linux" in done.stdout,
          (done.stdout + done.stderr)[-500:])
    check("355: the AppImage's signature checks against the AppImage with the throwaway public key for 0.9.1, is written "
          "beside it as the Mac's and Windows's are, and the .deb has no signature and no entry",
          release.check_manifest(manifest, public, files, "0.9.1") == []
          and "version:0.9.1" in (minisign.verify(public, files[release.LINUX].read_bytes(), platforms["linux-x86_64"]["signature"]) or "")
          and (out / "Idiograph-x86_64.AppImage.sig").read_text(encoding="utf-8") == platforms["linux-x86_64"]["signature"]
          and not (out / "Idiograph-amd64.deb.sig").exists()
          and not any(e["url"].endswith(".deb") for e in platforms.values()))
    check("355: the dry run says it would publish the AppImage and the .deb with the other files and latest.json",
          re.search(r"Would publish Idiograph 0\.9\.1 .*Idiograph\.dmg, Idiograph\.app\.tar\.gz, Idiograph-Setup\.exe, "
                    r"Idiograph-x86_64\.AppImage, Idiograph-amd64\.deb, latest\.json", done.stdout) is not None, done.stdout[-400:])
    changed = base / "changed.AppImage"
    changed.write_bytes(files[release.LINUX].read_bytes() + b"!")
    tampered = dict(files)
    tampered[release.LINUX] = changed
    moved = json.loads(json.dumps(manifest))
    moved["platforms"]["linux-x86_64"]["url"] = "https://example.com/Idiograph-x86_64.AppImage"
    check("355: a changed AppImage is refused, as is one served from anywhere but the releases repository",
          release.check_manifest(manifest, public, tampered, "0.9.1") == ["linux-x86_64's signature does not check against Idiograph-x86_64.AppImage"]
          and any("is not on Pharkie/idiograph" in w for w in release.check_manifest(moved, public, files, "0.9.1")))

    plain = base / "plain"
    plain.mkdir()
    for name in release.FILES:
        shutil.copyfile(builds / name, plain / name)
    done_plain, manifest_plain = dry(plain, base / "out-plain")
    check("355: a release whose Linux job failed, with no AppImage and no .deb, still goes out for the Mac and Windows alone, "
          "saying so, with no linux-x86_64",
          done_plain.returncode == 0 and sorted(manifest_plain.get("platforms", {})) == ["darwin-aarch64", "windows-x86_64"]
          and "no Linux AppImage" in done_plain.stdout and "AppImage" not in done_plain.stdout.split("Would publish", 1)[-1],
          (done_plain.stdout + done_plain.stderr)[-400:])
    lone = base / "lone"
    lone.mkdir()
    shutil.copytree(plain, lone, dirs_exist_ok=True)
    shutil.copyfile(builds / release.DEB, lone / release.DEB)
    done_lone, manifest_lone = dry(lone, base / "out-lone")
    check("355: a .deb alone, with no AppImage, is not shipped, since nothing updates from it and the AppImage is the Linux download",
          done_lone.returncode == 0 and "linux-x86_64" not in manifest_lone.get("platforms", {})
          and "Idiograph-amd64.deb" not in done_lone.stdout.split("Would publish", 1)[-1], done_lone.stdout[-400:])

    # ── B. the names for each app, and release.py --which
    sift, trace = release.names("sift"), release.names("trace")
    check("355: Sift and Trace name their own Linux files, and the .deb is never among the files a release must hold",
          sift["linux"] == "Sift-x86_64.AppImage" and sift["deb"] == "Sift-amd64.deb"
          and trace["linux_files"] == ("Trace-x86_64.AppImage", "Trace-amd64.deb")
          and release.names()["linux"] == release.LINUX and release.names()["deb"] == release.DEB
          and release.DEB not in release.FILES and release.LINUX not in release.FILES
          and sift["repo"] == "Pharkie/sift-releases")
    def which(value):
        return subprocess.run([sys.executable, str(support.source("packaging/release.py")), "--which", value],
                              capture_output=True, text=True, encoding="utf-8", timeout=60).stdout
    check("355: release.py --which says the app and its name for a tag or a name, as the workflow reads it",
          which("v0.9.1") == "APP=idiograph\nAPP_NAME=Idiograph\n" and which("sift-v1.0.0") == "APP=sift\nAPP_NAME=Sift\n"
          and which("trace") == "APP=trace\nAPP_NAME=Trace\n", which("v0.9.1"))

    # ── C. the draft collected with a gh of the check's own, and the upload
    gh = base / "gh_stub.py"
    gh.write_text(GH_STUB, encoding="utf-8")

    def collect_with(state, into):
        kept = release.GH
        try:
            release.GH = [sys.executable, str(gh), state]
            got = release.collect("v0.9.1", into, None)
            result = sorted(got)
        except (SystemExit, subprocess.CalledProcessError) as exc:
            result = f"stopped: {type(exc).__name__}"
        finally:
            release.GH = kept
        return result
    both = collect_with("both", base / "got-both")
    nolinux = collect_with("nolinux", base / "got-nolinux")
    broken = collect_with("broken", base / "got-broken")
    check("355: collecting a draft takes the Linux files when it has them, goes on without them when gh says no asset "
          "matches, and stops on any other failure rather than taking a half release for a whole one",
          both == sorted((*release.FILES, *release.LINUX_FILES)) and nolinux == sorted(release.FILES)
          and broken == "stopped: CalledProcessError", f"{both} | {nolinux} | {broken}")
    for log in base.glob("gh_stub.py.*.log"):
        log.unlink()

    def upload(source: Path, to: Path):
        kept = release.GH
        try:
            release.GH = [sys.executable, str(gh), "up"]
            done = release.main(["v0.9.1", "--from", str(source), "--test-key", str(key_dir), "--out", str(to)])
        except SystemExit as exc:
            done = f"refused: {exc}"
        finally:
            release.GH = kept
        log = Path(f"{gh}.up.log")
        asked = [json.loads(line) for line in log.read_text(encoding="utf-8").splitlines()] if log.exists() else []
        log.unlink(missing_ok=True)
        return done, next((a for a in asked if a[:2] == ["release", "create"]), [])
    sent, create = upload(builds, base / "out-up")
    shutil.rmtree(base / "out-up-plain", ignore_errors=True)
    sent_plain, create_plain = upload(plain, base / "out-up-plain")
    check("355: the upload carries the Linux AppImage and .deb with the three files and latest.json when the release has "
          "them, and the three files and latest.json alone when it has not",
          sent == 0 and [Path(a).name for a in create[-6:]] == ["Idiograph.dmg", "Idiograph.app.tar.gz", "Idiograph-Setup.exe",
                                                               "Idiograph-x86_64.AppImage", "Idiograph-amd64.deb", "latest.json"]
          and sent_plain == 0 and [Path(a).name for a in create_plain[-4:]] == ["Idiograph.dmg", "Idiograph.app.tar.gz",
                                                                               "Idiograph-Setup.exe", "latest.json"],
          f"{sent} {create[-6:]} | {sent_plain} {create_plain[-4:]}")

    # ── D. the workflow, read as text
    workflow = read(support.source(".github/workflows/windows-installer.yml"))
    server_job, app_job, release_job = (job_block(workflow, j) for j in ("linux-server", "linux-app", "release"))
    steps = step_names(release_job)
    check("355: the release job's steps, in order: the code, which app, the Windows installer, the Mac files, the Linux "
          "files when the Linux job said ok, then the draft release",
          steps == ["actions/checkout@v4", 'python3 packaging/release.py --which "$GITHUB_REF_NAME" >> "$GITHUB_ENV"',
                    "actions/download-artifact@v4", "actions/download-artifact@v4", "actions/download-artifact@v4",
                    "The draft release"], str(steps))
    check("355: the Linux files come from the artifact the Linux job kept, only when its ok output is true, and go on the "
          "draft release only when they are there",
          release_job.count("name: ${{ env.APP_NAME }}-Linux") == 1 and "if: needs.linux-app.outputs.ok == 'true'" in release_job
          and 'LINUX_OK: ${{ needs.linux-app.outputs.ok }}' in release_job and '"$APP_NAME-x86_64.AppImage" "$APP_NAME-amd64.deb"' in release_job
          and '[ "$LINUX_OK" = true ] && [ -f "$f" ]' in release_job)
    check("355: the release runs once Windows and the Mac have passed, whatever the Linux job did, and waits for all three",
          "needs: [windows, mac-app, linux-app]" in release_job and "!cancelled()" in release_job
          and "needs.windows.result == 'success'" in release_job and "needs.mac-app.result == 'success'" in release_job
          and "needs.linux-app.result" not in release_job and "if: github.ref_type == 'tag'" in release_job)
    names_in_app = [n for n in step_names(app_job)]
    check("355: the Linux job stays allowed to fail, says ok only after its last real step, and keeps its files either way",
          "continue-on-error: true" in app_job and "ok: ${{ steps.done.outputs.ok }}" in app_job
          and 'echo "ok=true" >> "$GITHUB_OUTPUT"' in app_job and "id: done" in app_job
          and app_job.index("drive_linux.py") < app_job.index("id: done") < app_job.index("actions/upload-artifact@v4")
          and "!cancelled()" in app_job.split("id: done", 1)[1] and len(names_in_app) >= 8, str(names_in_app))
    check("355: linux-server runs for a dispatch that asks for it alone, no longer on a tag, since linux-app repeats its smoke",
          "github.ref_type" not in server_job and "inputs.linux_server" in server_job
          and 'build_linux.py --app "$APP" --smoke' in server_job and 'build_linux.py --app "$APP" --smoke --window' in app_job)
    check("355: the signing secret is still not in the workflow, the update files being signed on the maintainer's Mac alone",
          "secrets." not in workflow and "TAURI_SIGNING" not in workflow and "createUpdaterArtifacts" not in workflow)

    # ── E. the README's line
    readme = read(support.source("README.md"))
    linux = readme.split("### Linux", 1)[1].split("###", 1)[0] if "### Linux" in readme else ""
    check("355: the README tells a Linux user what to download, the AppImage first and the .deb for Ubuntu, Debian and Mint, "
          "and the FUSE line for Ubuntu 24.04, and stays under 1,000 words",
          "Idiograph-x86_64.AppImage" in linux and "Idiograph-amd64.deb" in linux and "Mint" in linux and "libfuse2t64" in linux
          and linux.index("AppImage") < linux.index(".deb") and len(readme.split()) < 1000, f"{len(readme.split())} words")
