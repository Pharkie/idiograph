"""Idiograph's window bundled by Tauri's own bundler around the frozen server (17 October 2026, the
third Tauri build): on a Mac `Idiograph.app`, its disk image and the update file the updater takes, on
Windows the installer. `packaging/build_mac.py` and `packaging/build_windows.py` call it once the server
is frozen, and nothing else does. The standard library only.

The window's source is laid out under `<out>/tauri` as it sits in the app's folder, with the frozen
server as `build/tauri-server` and the manual as `docs/manual.md`, so the relative paths in
`tauri.conf.json` find them there and nothing is ever written in the checkout. Cargo's target goes in
`<out>/target`. The bundler runs with `CI=true`, so the disk image is made without a Finder window
scripted on the screen, as `hdiutil` made the one before. On a Mac the frozen server goes in through
`tauri.macos.conf.json`'s `files`, which keeps its links as links (`resources` copied each link as a
file, 83 MB where 56 do), and on Windows through `tauri.windows.conf.json`'s `resources`, beside the
window's own executable. Tauri lays each system's file over `tauri.conf.json` by itself.

The CLI is Tauri's own at TAURI_CLI: IDIOGRAPH_TAURI_CLI names one already installed (its `tauri.js`,
run by node, or a binary), and without it npx fetches that version. A test build is the test app,
"Idiograph Test", `uk.co.adamknowles.idiograph.test`, so no test copy is ever taken for the real app.

Since the fourth build (18 October): the bundle carries `docs/whats-new.md` beside the manual, which
the page's What's new reads through the server, and on a Mac the disk image is made by `disk_image`,
dmgbuild in the build venv, laid out as a Finder window shows it, Idiograph at the left, an arrow, and
Applications at the right, where Tauri's own image had no layout and its script would have driven a
Finder window on the screen. A test build alone may carry a check's own version, its notes, and an
update key and address of the check's own (`test_update`), so a release can be proved end to end on
this machine with a throwaway key, and a build that ships never can.

Since the three-app split's build 6 (20 October): a build is of one app, Idiograph, Sift or Trace
(`app_identity`), and `overrides` lays that app's name, bundle id, icons and update address over
tauri.conf.json, which stays Idiograph's own. Sift's icons are under `src-tauri/icons/sift`, Trace's under
`src-tauri/icons/trace` (`make_icons.py` draws them), and the bundle carries the app's own What's new.

Since 6 November (fileassoc): tauri.conf.json makes `.idiograph`, a shared copy, Idiograph's own document type, and
`NO_FILES` takes it out of Sift's and Trace's builds and out of every test app's, so a double click on a shared copy
never opens another app of the family, nor a test copy in the place of the real app.

Since the Linux plan's build 3 (linux3, 8 November 2026): `build_linux.py` calls it too, for `deb` and
`appimage`, the frozen server going in through `tauri.linux.conf.json`'s `resources`, which Tauri lays at
`<prefix>/lib/<product name>/server` in the .deb and in the AppImage's mount. Idiograph's own Linux build
alone (`linux=True`, no test app, no Sift or Trace) claims `.idiograph`: Tauri writes only the `MimeType=`
line of the desktop entry from `mimeType`, so the type's name for shared-mime-info goes in as the file
`src-tauri/linux/uk.co.adamknowles.idiograph.xml`, which the .deb's `files` put in `/usr/share/mime/packages`.
An AppImage registers nothing alone.

Since linuxfix (9 November 2026): Idiograph's own Linux build also has the .deb put the app's mark in the hicolor
theme's mimetypes folders under the icon name the mime file gives the type, so a shared copy shows it in a file
manager, and its desktop entry is written from `src-tauri/linux/idiograph.desktop`, Tauri's own with `%F` after the
executable, so Open With and a double click hand the file to the app.
"""
from __future__ import annotations

import gzip
import json
import os
import shutil
import subprocess
import sys
import tarfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
TOOL = HERE.parent.parent
SRC = HERE / "src-tauri"
# the Tauri CLI every build uses, the one the crates in Cargo.lock were made with
TAURI_CLI = "2.12.1"
CLI_ENV = "IDIOGRAPH_TAURI_CLI"
# the test app's identity, laid over tauri.conf.json's own for every check
TEST_IDENTITY = {"identifier": "uk.co.adamknowles.idiograph.test", "productName": "Idiograph Test",
                 "mainBinaryName": "Idiograph Test"}
# what a build that claims no file type lays over tauri.conf.json, Sift's, Trace's and every test app's: its
# fileAssociations, Idiograph's shared copy, taken away (null, which Tauri's merge of a --config file removes)
NO_FILES = {"bundle": {"fileAssociations": None}}
# the Linux .deb's name for a shared copy, the file that tells shared-mime-info of it (in src-tauri/) and where
# the .deb puts that file, the Linux counterpart of the exported type the Mac's Info.plist carries
LINUX_MIME = "application/x-idiograph-shared-copy"
LINUX_MIME_FILE = "linux/uk.co.adamknowles.idiograph.xml"
LINUX_MIME_DEST = "/usr/share/mime/packages/uk.co.adamknowles.idiograph.xml"
# a shared copy's picture in a file manager, the app's own mark under the icon name the mime file gives the type, in
# the hicolor theme's mimetypes folders, each size from the app's own icon files (linuxfix, 9 November 2026)
LINUX_MIME_ICON = "application-x-idiograph"
LINUX_MIME_ICONS = {f"/usr/share/icons/hicolor/{size}/mimetypes/{LINUX_MIME_ICON}.png": f"icons/{source}"
                    for size, source in (("32x32", "32x32.png"), ("128x128", "128x128.png"), ("256x256", "128x128@2x.png"))}
# the desktop entry Idiograph's own .deb and AppImage carry, Tauri's own with `%F` after the executable, so a file
# opened with it from a file manager reaches the app (linuxfix): Tauri's has none, and Sift and Trace take no files
LINUX_DESKTOP_TEMPLATE = "linux/idiograph.desktop"
# the icon files tauri.conf.json names, in its order, each app's in its own folder under src-tauri
ICON_FILES = ("32x32.png", "128x128.png", "128x128@2x.png", "icon.icns", "icon.ico")
# the files outside packaging/ the window's source builds in (include_str!), by their paths in the app's folder
WINDOW_BUILDS_IN = ("family/static/i18n/en/menus.json",)
# what a build of the window leaves beside its source and never needs again
LEAVE = ("target", "gen", "autogenerated", "node_modules")
# the update file of the Mac app, which Tauri's updater unpacks over the app it runs from
UPDATE_FILE = "Idiograph.app.tar.gz"
# the disk image's window, 660 by 400 and its two icons' centres, the arrow drawn between them by
# draw_pictures.py in its background
import draw_pictures  # noqa: E402  beside this file
sys.path.insert(0, str(TOOL))
import boot  # noqa: E402  the family's folders on the path (boot.py)
boot.setup()
import app_identity  # noqa: E402  each app's name, bundle id and update address
DMG_BACKGROUND = draw_pictures.BACKGROUND
DMG_WINDOW = draw_pictures.WINDOW
DMG_ICONS = (draw_pictures.APP_AT, draw_pictures.APPLICATIONS_AT)
DMG_ICON_SIZE = 128


def say(line: str) -> None:
    print(line, flush=True)


def cli_command(env: dict | None = None) -> list[str]:
    """The command that runs the Tauri CLI: the one IDIOGRAPH_TAURI_CLI names, through node when it
    is the CLI's script, or else npx with the pinned version."""
    env = os.environ if env is None else env
    named = (env.get(CLI_ENV) or "").strip()
    if named:
        # a path as the folder this runs from finds it, since the bundler runs in another
        named = str(Path(named).resolve()) if Path(named).exists() else named
        return ["node", named] if named.endswith(".js") else [named]
    npx = shutil.which("npx") or "npx"
    return [npx, "--yes", f"@tauri-apps/cli@{TAURI_CLI}"]


def icon_dir(app: str = app_identity.DEFAULT) -> str:
    """The app's icons' folder under src-tauri: Idiograph's `icons`, as it always was, Sift's
    `icons/sift` and Trace's `icons/trace`."""
    name = app_identity.check(app)
    return "icons" if name == app_identity.DEFAULT else f"icons/{name}"


def test_identity(app: str = app_identity.DEFAULT) -> dict:
    """The test app's identity for `app`: Idiograph Test as before, Sift Test, Trace Test, each its
    app's bundle id with `.test` after it, so no test copy is taken for the real app."""
    name = app_identity.check(app)
    if name == app_identity.DEFAULT:
        return dict(TEST_IDENTITY)
    shown = f"{app_identity.APPS[name]['name']} Test"
    return {"identifier": f"{app_identity.APPS[name]['bundle_id']}.test", "productName": shown, "mainBinaryName": shown}


def app_conf(app: str = app_identity.DEFAULT) -> dict:
    """What `app` lays over tauri.conf.json, Idiograph's own, which needs nothing: its name, its bundle
    id, its icons, the installer's icon, its update address and its What's new under its own name, and no
    file type of its own, since a shared copy is Idiograph's (`NO_FILES`)."""
    name = app_identity.check(app)
    if name == app_identity.DEFAULT:
        return {}
    ident, icons = app_identity.APPS[name], icon_dir(name)
    return {
        "productName": ident["name"], "mainBinaryName": ident["name"], "identifier": ident["bundle_id"],
        "bundle": {
            "shortDescription": ident["name"],
            "icon": [f"{icons}/{f}" for f in ICON_FILES],
            "resources": {"../../../docs/manual.md": "docs/manual.md",
                          "../../../docs/whats-new.md": f"docs/{ident['whats_new']}"},
            "windows": {"nsis": {"installerIcon": f"{icons}/icon.ico", "uninstallerIcon": f"{icons}/icon.ico"}},
            **NO_FILES["bundle"],
        },
        "plugins": {"updater": {"endpoints": [ident["endpoint"]]}},
    }


def merged(base: dict, over: dict) -> dict:
    """`over` laid on `base` as Tauri lays a --config file on tauri.conf.json, a JSON merge patch:
    objects merged key by key, anything else replaced."""
    out = dict(base)
    for key, value in over.items():
        out[key] = merged(out[key], value) if isinstance(value, dict) and isinstance(out.get(key), dict) else value
    return out


def notes_file(app: str = app_identity.DEFAULT) -> Path:
    """The app's What's new in the checkout, `docs/whats-new.md` for Idiograph, `docs/whats-new-sift.md`
    for Sift."""
    return TOOL / "docs" / app_identity.APPS[app_identity.check(app)]["whats_new"]


def stage_source(out: Path, frozen: Path, whats_new: Path | None = None, app: str = app_identity.DEFAULT) -> Path:
    """The window's source under `<out>/tauri` as the app's folder holds it, the frozen server as
    `build/tauri-server` with its links kept, the manual and the app's What's new, `whats_new` in its
    place for a test build, English's menus (`WINDOW_BUILDS_IN`) at their place in the family's folder, and
    the folder the bundler runs in. An app with no What's new of its own
    yet carries a heading alone, so its What's new lists nothing, never another app's notes."""
    root = out / "tauri"
    for part in ("packaging", "build", "docs", "family"):
        shutil.rmtree(root / part, ignore_errors=True)
    src = root / "packaging" / "tauri" / "src-tauri"
    shutil.copytree(SRC, src, ignore=shutil.ignore_patterns(*LEAVE))
    shutil.copyfile(HERE / "window.js", src.parent / "window.js")
    # the files the window builds in from beyond packaging/, each at its path in the app's folder, so
    # words.rs's include_str! finds English's menus the same way in the checkout and in the stage
    for part in WINDOW_BUILDS_IN:
        (root / part).parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(TOOL / part, root / part)
    (root / "docs").mkdir(parents=True)
    # the app's own manual, Sift's docs/manual-sift.md for Sift, under the one name the window reads
    shutil.copyfile(TOOL / "docs" / app_identity.APPS[app_identity.check(app)]["manual"], root / "docs" / "manual.md")
    notes = whats_new or notes_file(app)
    if notes.is_file():
        shutil.copyfile(notes, root / "docs" / "whats-new.md")
    else:
        say(f"No {notes.name} yet, so {app_identity.APPS[app_identity.check(app)]['name']}'s What's new lists nothing")
        (root / "docs" / "whats-new.md").write_text("# What's new\n", encoding="utf-8")
    shutil.copytree(frozen, root / "build" / "tauri-server", symlinks=True)
    return src


def test_update(pubkey: str, url: str) -> dict:
    """A check's own update settings, for a test build alone: the public half of a throwaway key and the
    address of a manifest on this machine, plain http allowed there since nothing leaves it."""
    plugin = {"pubkey": pubkey.strip(), "endpoints": [url]}
    if url.startswith("http://"):
        if not url.startswith(("http://127.0.0.1:", "http://localhost:")):
            raise SystemExit("A check's update address over plain http is on this machine alone.")
        plugin["dangerousInsecureTransportProtocol"] = True
    return {"plugins": {"updater": plugin}}


def linux_file_type(app: str = app_identity.DEFAULT, test: bool = False) -> dict:
    """What a Linux build of Idiograph's own lays over tauri.conf.json to claim `.idiograph`: its file
    association with the mime type the desktop entry names (the array replaces tauri.conf.json's, so it is
    that one with `mimeType` added), the mime file the .deb installs and the type's icon beside it, and the desktop
    entry with `%F` (`LINUX_DESKTOP_TEMPLATE`), which Tauri's AppImage takes from the .deb's. Nothing for Sift, Trace
    or a test app."""
    if app_identity.check(app) != app_identity.DEFAULT or test:
        return {}
    base = json.loads((SRC / "tauri.conf.json").read_text(encoding="utf-8"))
    kinds = [dict(kind, mimeType=LINUX_MIME) for kind in base["bundle"]["fileAssociations"]]
    files = {LINUX_MIME_DEST: LINUX_MIME_FILE, **LINUX_MIME_ICONS}
    return {"bundle": {"fileAssociations": kinds,
                       "linux": {"deb": {"files": files, "desktopTemplate": LINUX_DESKTOP_TEMPLATE}}}}


def overrides(version: str, test: bool = False, windows_sign: str | None = None, update: dict | None = None,
              app: str = app_identity.DEFAULT, linux: bool = False) -> dict:
    """What a build lays over tauri.conf.json: the app's own (`app_conf`, nothing for Idiograph), the
    app's version, so the window, its installer and its update file carry the number `server.py` does,
    the test app's identity for a check, with no file type of its own (`NO_FILES`), on Windows a
    certificate's thumbprint for Tauri to sign the window and the installer with, and for a test build alone
    a check's own update settings (`test_update`), and on Linux Idiograph's own file type (`linux_file_type`)."""
    if update and not test:
        raise SystemExit("A check's own update key and address go in the test app alone, never in Idiograph.")
    conf: dict = merged(app_conf(app), {"version": version})
    if test:
        conf.update(test_identity(app))
        conf = merged(conf, NO_FILES)
    if update:
        conf = merged(conf, update)
    if linux:
        conf = merged(conf, linux_file_type(app, test))
    if windows_sign:
        conf = merged(conf, {"bundle": {"windows": {"certificateThumbprint": windows_sign, "digestAlgorithm": "sha256",
                                                    "timestampUrl": "http://timestamp.digicert.com"}}})
    return conf


def target_triple(universal: bool) -> str | None:
    """The target Tauri builds for: both of a Mac's architectures in one app, or this machine's own."""
    return "universal-apple-darwin" if universal else None


def bundle_dir(out: Path, universal: bool) -> Path:
    """Where Tauri leaves the bundles: under the target's own folder when one was named."""
    triple = target_triple(universal)
    return out / "target" / triple / "release" / "bundle" if triple else out / "target" / "release" / "bundle"


def build_command(cli: list[str], bundles: list[str], config: Path, universal: bool, features: list[str]) -> list[str]:
    cmd = [*cli, "build", "--bundles", ",".join(bundles), "--config", str(config)]
    if target_triple(universal):
        cmd += ["--target", target_triple(universal)]
    if features:
        cmd += ["--features", ",".join(features)]
    return cmd


def bundle(frozen: Path, out: Path, version: str, bundles: list[str], *, test: bool = False,
           universal: bool = False, features: list[str] | None = None, windows_sign: str | None = None,
           env: dict | None = None, update: dict | None = None, whats_new: Path | None = None,
           app: str = app_identity.DEFAULT, linux: bool = False) -> Path:
    """Tauri's bundler run on the window of `app` around `frozen`, the folder PyInstaller made, its
    outputs under `<out>/target`. Answers the folder the bundles are in."""
    if whats_new and not test:
        raise SystemExit("A check's own notes go in the test app alone.")
    src = stage_source(out, frozen, whats_new, app)
    config = out / "tauri-config.json"
    config.write_text(json.dumps(overrides(version, test, windows_sign, update, app, linux), indent=2) + "\n", encoding="utf-8")
    run_env = dict(os.environ if env is None else env)
    run_env.update(CARGO_TARGET_DIR=str(out / "target"), CI="true")
    cmd = build_command(cli_command(run_env), bundles, config, universal, list(features or []))
    say(f"Bundling the window with Tauri {TAURI_CLI}: {', '.join(bundles)}"
        + (", both of a Mac's architectures" if universal else ""))
    subprocess.run(cmd, cwd=src, env=run_env, check=True)
    return bundle_dir(out, universal)


def linux_bundle_of(made: Path, kind: str, version: str) -> Path:
    """The .deb or the AppImage Tauri's bundler made for this version, `<product>_<version>_amd64.deb` under
    `deb` and `<product>_<version>_amd64.AppImage` under `appimage`, never another version's left beside it."""
    suffix = {"deb": ".deb", "appimage": ".AppImage"}[kind]
    found = sorted(p for p in (made / kind).glob(f"*{suffix}") if f"_{version}_" in p.name)
    if not found:
        raise SystemExit(f"Tauri's bundler made no {suffix} for {version} in {made / kind}.")
    return found[-1]


def update_tarball(app: Path, dest: Path) -> Path:
    """The Mac app as the file Tauri's updater takes: the bundle under its own name at the archive's
    top, its links kept as links and its modes as they are, gzipped, in a fixed order with no owner
    and no time of its own beyond the files', so the same app makes the same file."""
    dest.parent.mkdir(parents=True, exist_ok=True)

    def clean(info: tarfile.TarInfo) -> tarfile.TarInfo:
        info.uid = info.gid = 0
        info.uname = info.gname = ""
        return info

    with open(dest, "wb") as raw:
        with gzip.GzipFile(filename="", mode="wb", fileobj=raw, mtime=0) as gz:
            with tarfile.open(fileobj=gz, mode="w", format=tarfile.PAX_FORMAT) as tar:
                paths = [app, *sorted(app.rglob("*"), key=lambda p: p.relative_to(app).as_posix())]
                for path in paths:
                    name = (Path(app.name) / path.relative_to(app)).as_posix() if path != app else app.name
                    tar.add(path, arcname=name, recursive=False, filter=clean)
    return dest


def dmg_settings(app: Path, background: Path = DMG_BACKGROUND) -> dict:
    """dmgbuild's settings for the disk image: the app and a link to Applications, each where the
    background's arrow leads, the window 660 by 400 with no toolbar, sidebar, path or status bar, the
    icons at 128 pixels, and the background with its @2x beside it for a Retina screen."""
    (x, y), (ax, ay) = DMG_ICONS
    return {
        "format": "UDZO",
        "filesystem": "HFS+",
        "files": [str(app)],
        "symlinks": {"Applications": "/Applications"},
        "icon_locations": {app.name: [x, y], "Applications": [ax, ay]},
        "background": str(background),
        "window_rect": [[200, 120], list(DMG_WINDOW)],
        "default_view": "icon-view",
        "show_status_bar": False,
        "show_tab_view": False,
        "show_toolbar": False,
        "show_pathbar": False,
        "show_sidebar": False,
        "show_icon_preview": False,
        "icon_size": DMG_ICON_SIZE,
        "text_size": 13,
        "include_icon_view_settings": True,
    }


# what runs dmgbuild in the build venv: the settings from a file, the image and its volume's name
DMGBUILD = ("import json, sys, dmgbuild\n"
            "settings = json.load(open(sys.argv[1], encoding='utf-8'))\n"
            "dmgbuild.build_dmg(sys.argv[2], sys.argv[3], settings=settings)\n")


def disk_image(app: Path, dest: Path, py: Path, volume: str, work: Path) -> Path:
    """The disk image made by dmgbuild with `py`, the build venv's Python, from `app`: no Finder window
    is opened, since dmgbuild writes the window's layout into the image itself."""
    work.mkdir(parents=True, exist_ok=True)
    settings = work / "dmg-settings.json"
    settings.write_text(json.dumps(dmg_settings(app), indent=2) + "\n", encoding="utf-8")
    dest.unlink(missing_ok=True)
    say(f"Making the disk image {dest.name} with dmgbuild, laid out for the Finder")
    subprocess.run([str(py), "-c", DMGBUILD, str(settings), str(dest), volume], check=True)
    return dest


def size_mb(path: Path) -> float:
    if path.is_file():
        return path.stat().st_size / 1e6
    return sum(p.lstat().st_size for p in path.rglob("*") if p.is_file() and not p.is_symlink()) / 1e6


if __name__ == "__main__":
    sys.exit("Run packaging/build_mac.py or packaging/build_windows.py, which freeze the server first.")
