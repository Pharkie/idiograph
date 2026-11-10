from __future__ import annotations

import json
import shutil
import struct
import subprocess
import sys
from pathlib import Path

from . import support
from .support import check

# a fat Mach-O header for both of a Mac's architectures, as area 173 has it
FAT = struct.pack(">II", 0xCAFEBABE, 2) + struct.pack(">IIIII", 0x01000007, 3, 4096, 16, 12) \
    + struct.pack(">IIIII", 0x0100000C, 0, 8192, 16, 14) + b"\0" * 64
# a made-up app's notes, on a made-up topic, for a dry run of Sift's release
NOTES = "# What's new\n\n## 1.0.0, 20 October 2026\n\nSift sorts the records about beekeeping in its own window.\n"


def fake_app(folder: Path, name: str) -> Path:
    app = folder / f"{name}.app"
    (app / "Contents" / "MacOS").mkdir(parents=True)
    (app / "Contents" / "MacOS" / name).write_bytes(FAT)
    (app / "Contents" / "Info.plist").write_text("<plist/>\n", encoding="utf-8")
    return app


def test_pack(scratch):
    print("\n229. Each app built and released on its own (20 October, the three-app split's build 6): Sift's and "
          "Trace's icons, each build's Tauri settings, executables and installer per app, a tag naming its app, "
          "and release.py's dry run per app, with its own files, notes and releases repository")
    sys.path.insert(0, str(support.source("packaging")))
    sys.path.insert(0, str(support.source("packaging/tauri")))
    import app_identity
    import build_mac
    import build_windows
    import bundle
    import make_app
    import minisign
    import release

    base = scratch / "a229"
    shutil.rmtree(base, ignore_errors=True)
    base.mkdir(parents=True)
    src = support.source("packaging/tauri/src-tauri")

    # ── A. the icons
    drawn = {app: make_app.draw_icon(64, app) for app in ("idiograph", "sift", "trace")}
    small = {app: make_app.draw_icon(16, app) for app in ("idiograph", "sift", "trace")}
    committed = {}
    for app in ("sift", "trace"):
        folder = src / bundle.icon_dir(app)
        committed[app] = all((folder / name).is_file() for name in bundle.ICON_FILES) and (
            (folder / "32x32.png").read_bytes() == make_app.png_bytes(32, make_app.draw_icon(32, app))
            and (folder / "128x128@2x.png").read_bytes() == make_app.png_bytes(256, make_app.draw_icon(256, app))
            and (folder / "icon.ico").read_bytes() == build_windows.ico_bytes(app=app)
            and (folder / "icon.icns").read_bytes()[:4] == b"icns"
            and support.source(f"apps/{app}/static/favicon-{app}.svg").is_file())
    check("229: Sift's and Trace's icons are drawn apart from Idiograph's and from each other at every size, and the "
          "files their builds read are the drawing as it stands, Idiograph's own icons where they always were",
          len({bytes(v) for v in drawn.values()}) == 3 and len({bytes(v) for v in small.values()}) == 3
          and all(committed.values()) and bundle.icon_dir("idiograph") == "icons"
          and (src / "icons" / "icon.icns").is_file(), str(committed))

    # ── B. each build's settings per app
    sift, trace, idio = (bundle.overrides("1.0.0", app=a) for a in ("sift", "trace", "idiograph"))
    conf = json.loads((src / "tauri.conf.json").read_text(encoding="utf-8"))
    laid = bundle.merged(conf, sift)
    check("229: Sift's build lays its own name, bundle id, version, icons, installer icon and update address over "
          "tauri.conf.json, Trace's its own, and Idiograph's lays its version alone, as before",
          idio == {"version": "1.0.0"}
          and laid["productName"] == laid["mainBinaryName"] == "Sift" and laid["identifier"] == "uk.co.adamknowles.sift"
          and laid["version"] == "1.0.0" and laid["bundle"]["icon"][0] == "icons/sift/32x32.png"
          and laid["bundle"]["windows"]["nsis"]["installerIcon"] == "icons/sift/icon.ico"
          and laid["bundle"]["windows"]["nsis"]["installMode"] == "currentUser"
          and laid["plugins"]["updater"]["endpoints"] == ["https://github.com/Pharkie/sift-releases/releases/latest/download/latest.json"]
          and laid["plugins"]["updater"]["pubkey"] == conf["plugins"]["updater"]["pubkey"]
          and laid["bundle"]["resources"]["../../../docs/whats-new.md"] == "docs/whats-new-sift.md"
          and trace["identifier"] == "uk.co.adamknowles.trace" and trace["bundle"]["icon"][-1] == "icons/trace/icon.ico"
          and trace["plugins"]["updater"]["endpoints"][0].startswith("https://github.com/Pharkie/trace-releases/"),
          json.dumps(sift)[:400])
    test = bundle.overrides("1.0.0", test=True, windows_sign="ABC123", app="sift")
    check("229: Sift's test app is Sift Test under its own bundle id, and a signed build keeps Sift's installer icons "
          "beside the thumbprint",
          test["productName"] == "Sift Test" and test["identifier"] == "uk.co.adamknowles.sift.test"
          and test["bundle"]["windows"]["certificateThumbprint"] == "ABC123"
          and test["bundle"]["windows"]["nsis"]["installerIcon"] == "icons/sift/icon.ico", json.dumps(test)[:400])

    out = base / "win"
    said = subprocess.run([sys.executable, str(support.source("packaging/build_windows.py")), "--dry-run", "--app", "sift",
                           "--out", str(out)], capture_output=True, text=True, encoding="utf-8", timeout=600)
    spec = (out / "build" / "Sift-windows.spec").read_text(encoding="utf-8") if (out / "build" / "Sift-windows.spec").is_file() else ""
    settings = json.loads((out / "build" / "tauri-config.json").read_text(encoding="utf-8")) if (out / "build" / "tauri-config.json").is_file() else {}
    check("229: the Windows build of Sift freezes Sift.exe and Sift-console.exe with Sift's icon, and its Setup is "
          "Sift-Setup.exe, installing Sift in its own folder under LocalAppData at Sift's version",
          said.returncode == 0 and "name='Sift'" in spec and "name='Sift-console'" in spec and "Sift.ico" in spec
          and "Sift-Setup.exe" in said.stdout and "%LOCALAPPDATA%\\Sift " in said.stdout
          and settings.get("productName") == "Sift" and settings.get("version") == app_identity.version("sift")
          and (out / "build" / "stage" / "Sift.ico").read_bytes() == build_windows.ico_bytes(app="sift"),
          (said.stdout + said.stderr)[-500:])
    (base / "mac").mkdir()
    mac_spec = build_mac.write_spec(base / "mac", base / "mac-stage", "1.0.0", None, "trace").read_text(encoding="utf-8")
    check("229: the Mac build of Trace freezes its server as Trace, the name by which it knows it is Trace, and the "
          "executables' names each say their app",
          "name='Trace'" in mac_spec and build_mac.server_name("trace") == "Trace"
          and app_identity.from_executable("Trace") == "trace" and app_identity.from_executable("Sift-console.exe") == "sift"
          and build_windows.names("trace")["setup"] == "Trace-Setup", mac_spec[-300:])
    hooks = (src / "windows" / "hooks.nsh").read_text(encoding="utf-8")
    check("229: each app's Setup stops the server its own folder holds, and only Idiograph's removes the Inno Setup "
          "install, which was Idiograph's",
          all(f"$INSTDIR\\server\\{n}-console.exe" in hooks for n in ("Idiograph", "Sift", "Trace"))
          and 'StrCpy $R1 "${PRODUCTNAME}" 9' in hooks and '${If} $R1 == "Idiograph"' in hooks)

    # ── C. the tag names its app
    tags = {}
    for tag in ("v0.9.3", "idiograph-v0.9.3", "sift-v1.0.0", "trace-v1.2.10"):
        tags[tag] = release.tag_app(tag)
    refused = []
    for tag in ("1.0.0", "sift-1.0.0", "distil-v1.0.0", "sift-v1.0", "vsift1.0.0"):
        try:
            release.tag_app(tag)
            refused.append(f"{tag} taken")
        except SystemExit:
            pass
    which = subprocess.run([sys.executable, str(support.source("packaging/release.py")), "--which", "trace-v1.0.0"],
                           capture_output=True, encoding="utf-8", timeout=60)
    workflow = support.source(".github/workflows/windows-installer.yml").read_text(encoding="utf-8")
    check("229: a tag names its app, sift-v1.0.0 Sift's and trace-v Trace's, a bare v or idiograph-v Idiograph's, "
          "anything else refused, and the workflow builds the tagged app through that one rule",
          tags == {"v0.9.3": ("idiograph", "0.9.3"), "idiograph-v0.9.3": ("idiograph", "0.9.3"),
                   "sift-v1.0.0": ("sift", "1.0.0"), "trace-v1.2.10": ("trace", "1.2.10")}
          and not refused and release.which("sift") == "APP=sift\nAPP_NAME=Sift\n"
          and which.returncode == 0 and which.stdout == "APP=trace\nAPP_NAME=Trace\n"
          and 'tags: ["v*", "idiograph-v*", "sift-v*", "trace-v*"]' in workflow
          and workflow.count('release.py --which "') == 5
          and "python packaging/build_windows.py --app ${{ env.APP }}" in workflow
          and "python3 packaging/build_mac.py --unsigned --app ${{ env.APP }}" in workflow,
          f"{tags} {refused} {which.stdout!r}")

    # ── D. release.py's dry run per app
    key_dir = base / "key"
    key_dir.mkdir()
    password = "a throwaway password for bees"
    blob = minisign.make_secret(password)
    public = minisign.open_secret(blob, password).public_key()
    (key_dir / "update.key").write_text(blob, encoding="utf-8")
    (key_dir / "update.key.password").write_text(password, encoding="utf-8")
    (key_dir / "update.key.pub").write_text(public, encoding="utf-8")
    builds = base / "builds"
    builds.mkdir()
    bundle.update_tarball(fake_app(base / "app", "Sift"), builds / "Sift.app.tar.gz")
    (builds / "Sift-Setup.exe").write_bytes(b"MZ an installer of the check's own")
    (builds / "Sift.dmg").write_bytes(b"a disk image of the check's own")
    notes = base / "whats-new-sift.md"
    notes.write_text(NOTES, encoding="utf-8")
    rel = base / "release"
    said = subprocess.run([sys.executable, str(support.source("packaging/release.py")), "sift-v1.0.0", "--from", str(builds),
                           "--test-key", str(key_dir), "--whats-new", str(notes), "--out", str(rel), "--dry-run"],
                          capture_output=True, text=True, encoding="utf-8", timeout=300)
    manifest = json.loads((rel / "latest.json").read_text(encoding="utf-8")) if (rel / "latest.json").is_file() else {}
    platforms = manifest.get("platforms", {})
    files = {n: rel / n for n in ("Sift.dmg", "Sift.app.tar.gz", "Sift-Setup.exe")}
    check("229: Sift's dry run signs Sift's two update files, writes a latest.json whose every address is on "
          "Pharkie/sift-releases under the sift-v tag, with Sift's notes, says what it would publish and where, and "
          "uploads nothing",
          said.returncode == 0 and manifest.get("version") == "1.0.0"
          and manifest.get("notes") == "Sift sorts the records about beekeeping in its own window."
          and platforms.get("windows-x86_64", {}).get("url") == "https://github.com/Pharkie/sift-releases/releases/download/sift-v1.0.0/Sift-Setup.exe"
          and platforms.get("darwin-aarch64", {}).get("url", "").endswith("/sift-v1.0.0/Sift.app.tar.gz")
          and release.check_manifest(manifest, public, files, "1.0.0", "sift") == []
          and release.check_manifest(manifest, public, files, "1.0.0") != []
          and "Would publish Sift 1.0.0 to Pharkie/sift-releases as sift-v1.0.0: Sift.dmg, Sift.app.tar.gz, "
              "Sift-Setup.exe, latest.json" in said.stdout
          and "Dry run: nothing uploaded." in said.stdout
          and (rel / "notes.md").read_text(encoding="utf-8").startswith("Sift 1.0.0, 20 October 2026"),
          (said.stdout + said.stderr)[-600:])
    refusals = {}
    for label, argv in (("other app", ["sift-v1.0.0", "--app", "trace", "--dry-run"]),
                        ("version", ["sift-v9.9.9", "--dry-run"]),
                        ("no tag", ["--dry-run"])):
        try:
            release.main(argv)
            refusals[label] = "taken"
        except SystemExit as exc:
            refusals[label] = str(exc)
    no_notes = "taken"
    if not release.names("trace")["whats_new"].is_file():
        try:
            release.notes_for("1.0.0", app="trace")
        except SystemExit as exc:
            no_notes = str(exc)
    else:
        no_notes = "There is no docs/whats-new-trace.md"
    check("229: a tag of one app given another's --app is refused, as is a version versions.json does not hold for "
          "that app, and an app with no notes of its own says so plainly, before anything is collected or signed",
          refusals["other app"] == "The tag sift-v1.0.0 is Sift's, not Trace's."
          and refusals["version"].startswith(f"versions.json says {app_identity.version('sift')} for Sift")
          and refusals["no tag"].startswith("Name the version's tag")
          and no_notes.startswith("There is no docs/whats-new-trace.md"), f"{refusals} {no_notes}")
