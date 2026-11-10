"""Area 350: the Linux window's bundles and the check that starts them (linux3, 8 November 2026, build 3 of the
Linux plan). Tauri's bundler makes an AppImage and a .deb around the frozen server on Linux, and
`packaging/tauri/drive_linux.py` starts the AppImage under xvfb. Here, on any machine: the bundle settings parsed
(the Linux file's resource and its .deb and AppImage parts, the settings a Linux build lays over
tauri.conf.json for Idiograph's own file type and for no other app's), the shared-mime-info file, the names of the
files a build writes, what `deb_problems` finds missing in an unpacked .deb (made up here), the dry run, how a
bundle of the right version is picked, the crate settings that give Linux its dialogs, the drive against a
stand-in window that answers, answers as another app, does not say it is in a window, never answers or will not
end, and the workflow's `linux-app` job read as text, with the Mac and Windows jobs' needs unchanged. What only a
real Linux run proves (Tauri's bundler, linuxdeploy, WebKitGTK under xvfb, the .deb's install) is not here. All
made-up folders. Nothing here uses a participant's words."""
from __future__ import annotations

import contextlib
import io
import json
import os
import re
import stat
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

from . import support
from .support import check

STUB = '''#!{python}
import json, os, signal, sys, threading, time
from http.server import BaseHTTPRequestHandler, HTTPServer
mode, app = {mode!r}, {app!r}
if mode == "silent":
    time.sleep(60)
if mode == "stubborn":
    signal.signal(signal.SIGTERM, signal.SIG_IGN)
else:
    signal.signal(signal.SIGTERM, lambda *a: os._exit(0))
class H(BaseHTTPRequestHandler):
    def log_message(self, *a): pass
    def do_GET(self):
        if self.path == "/api/server":
            body = json.dumps({{"app": app, "pid": os.getpid(), "window": mode != "nowindow"}}).encode()
        else:
            body = b"<html><body>page</body></html>"
        self.send_response(200); self.send_header("Content-Length", str(len(body))); self.end_headers(); self.wfile.write(body)
HTTPServer(("127.0.0.1", int(os.environ["IDIOGRAPH_PORT"])), H).serve_forever()
'''


def job_block(workflow: str, job: str) -> str:
    """The text of one job under `jobs:`, from its two-space key to the next job's."""
    found = re.search(rf"^  {re.escape(job)}:\n(.*?)(?=^  [A-Za-z0-9_-]+:\n|\Z)", workflow, re.S | re.M)
    return found.group(1) if found else ""


def test_linux_window_build(scratch: Path):
    print("\n350. The Linux window's bundles and the start under xvfb: settings, names, the .deb's contents, the drive against a stand-in (linux3)")
    import importlib.util

    def load(name, folder="packaging"):
        spec = importlib.util.spec_from_file_location(f"idiograph_350_{name}", support.source(folder) / f"{name}.py")
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        return mod

    build_linux = load("build_linux")
    drive_linux = load("drive_linux", "packaging/tauri")
    window = build_linux.window
    root = scratch / "linux_window"
    root.mkdir(parents=True, exist_ok=True)

    # the bundle settings
    src = support.source("packaging/tauri/src-tauri")
    conf = json.loads((src / "tauri.linux.conf.json").read_text(encoding="utf-8"))
    base = json.loads((src / "tauri.conf.json").read_text(encoding="utf-8"))
    check("350: Tauri's Linux file carries the frozen server as server/, and the .deb and AppImage settings",
          conf["bundle"]["resources"] == {"../../../build/tauri-server/": "server/"}
          and conf["bundle"]["linux"]["deb"]["section"] == "science"
          and conf["bundle"]["linux"]["appimage"]["bundleMediaFramework"] is False, str(conf))
    check("350: tauri.conf.json is still the Mac's and Windows's own, with no Linux target of its own in it",
          base["bundle"]["targets"] == ["app", "dmg", "nsis"] and "linux" not in base["bundle"])
    check("350: Linux has no bundle of its own named for it that the builds do not ask for (the bundler is run with --bundles)",
          'cmd = [*cli, "build", "--bundles"' in (support.source("packaging/tauri") / "bundle.py").read_text(encoding="utf-8"))

    # what a Linux build lays over tauri.conf.json
    plain = window.overrides("0.9.99", False, None, None, "idiograph", False)
    idio = window.overrides("0.9.99", False, None, None, "idiograph", True)
    kinds = idio["bundle"]["fileAssociations"]
    check("350: a Linux build of Idiograph claims .idiograph with the mime type the desktop entry names",
          len(kinds) == 1 and kinds[0]["ext"] == ["idiograph"] and kinds[0]["mimeType"] == window.LINUX_MIME, str(kinds))
    check("350: the .deb installs the mime file under shared-mime-info's folder",
          idio["bundle"]["linux"]["deb"]["files"] == {window.LINUX_MIME_DEST: window.LINUX_MIME_FILE, **window.LINUX_MIME_ICONS}
          and window.LINUX_MIME_DEST.startswith("/usr/share/mime/packages/"))
    check("350: a build that is not for Linux is laid over as it was, with no file type changed",
          "bundle" not in plain or "linux" not in plain.get("bundle", {}) and "fileAssociations" not in plain.get("bundle", {}), str(plain))
    for label, over in (("Sift", window.overrides("0.9.99", False, None, None, "sift", True)),
                        ("Trace", window.overrides("0.9.99", False, None, None, "trace", True)),
                        ("Idiograph's test app", window.overrides("0.9.99", True, None, None, "idiograph", True))):
        got = over.get("bundle", {})
        check(f"350: {label} claims no file type on Linux and installs no mime file",
              got.get("fileAssociations") is None and "files" not in got.get("linux", {}).get("deb", {}), str(got))
    mime = ET.parse(src / window.LINUX_MIME_FILE)
    ns = "{http://www.freedesktop.org/standards/shared-mime-info}"
    node = mime.getroot().find(f"{ns}mime-type")
    check("350: the mime file names the type and globs *.idiograph",
          node is not None and node.get("type") == window.LINUX_MIME and node.find(f"{ns}glob").get("pattern") == "*.idiograph")
    stage = window.stage_source(root / "stage", _frozen(root), app="idiograph")
    check("350: the staged window source carries the mime file where the bundler's config finds it",
          (stage / window.LINUX_MIME_FILE).is_file())

    # the crates: Linux gets GTK 3's dialogs, nothing else changes
    cargo = (src / "Cargo.toml").read_text(encoding="utf-8")
    lock = (src / "Cargo.lock").read_text(encoding="utf-8")
    rfd_lock = lock.split('name = "rfd"')[1].split("[[package]]")[0]
    check("350: Linux's own rfd has the GTK 3 backend, pinned, and the other systems' rfd is as it was",
          re.search(r"\[target\.'cfg\(target_os = \"linux\"\)'\.dependencies\]\nrfd = \{ version = \"=0\.17\.2\", default-features = false, features = \[\"gtk3\"\] \}", cargo)
          and 'rfd = { version = "=0.17.2", default-features = false }' in cargo and '"gtk-sys"' in rfd_lock and '"glib-sys"' in rfd_lock)

    # the names a build writes, and a bundle of the right version
    names = build_linux.window_names("idiograph", False)
    check("350: Idiograph's files are Idiograph-x86_64.AppImage and Idiograph-amd64.deb, in a folder Tauri names for the product",
          names["appimage"] == "Idiograph-x86_64.AppImage" and names["deb"] == "Idiograph-amd64.deb" and names["product"] == "Idiograph"
          and names["main"] == "Idiograph", str(names))
    test_names = build_linux.window_names("idiograph", True)
    sift = build_linux.window_names("sift", False)
    check("350: the test app and Sift are named for themselves",
          test_names["product"] == "Idiograph Test" and sift["name"] == "Sift" and sift["product"] == "Sift", f"{test_names} {sift}")
    made = root / "made"
    for folder, fname in (("deb", "Idiograph_0.9.1_amd64.deb"), ("deb", "Idiograph_0.9.2_amd64.deb"),
                          ("appimage", "Idiograph_0.9.2_amd64.AppImage")):
        (made / folder).mkdir(parents=True, exist_ok=True)
        (made / folder / fname).write_bytes(b"x")
    check("350: the bundle of this version is picked, never another's left beside it",
          window.linux_bundle_of(made, "deb", "0.9.2").name == "Idiograph_0.9.2_amd64.deb"
          and window.linux_bundle_of(made, "appimage", "0.9.2").name.endswith(".AppImage"))
    try:
        window.linux_bundle_of(made, "deb", "0.9.3")
        got = "no refusal"
    except SystemExit as exc:
        got = str(exc)
    check("350: with none of this version, the build stops and says so", "made no .deb for 0.9.3" in got, got)

    # an unpacked .deb, made up
    def deb_tree(name, names, desktop_mime, with_mime_file=True, with_server=True, desktops=1, with_icon=True):
        # a build that claims the type also takes files on its Exec line and has the type's icon (linuxfix)
        takes_files = bool(desktop_mime) and with_mime_file
        tree = root / name
        import shutil
        shutil.rmtree(tree, ignore_errors=True)
        (tree / "usr" / "bin").mkdir(parents=True)
        (tree / "usr" / "bin" / names["main"]).write_bytes(b"x")
        if with_server:
            srv = tree / "usr" / "lib" / names["product"] / "server"
            (srv / "_internal").mkdir(parents=True)
            (srv / names["name"]).write_bytes(b"x")
            # the typesetter beside the server (typst1, 9 November 2026)
            (srv / "idiograph-typeset").write_bytes(b"x")
            (srv / "idiograph-typeset").chmod(0o755)
        apps = tree / "usr" / "share" / "applications"
        apps.mkdir(parents=True)
        for i in range(desktops):
            line = f"MimeType={desktop_mime}\n" if desktop_mime else ""
            exec_line = f"Exec={names['main']}{' %F' if takes_files else ''}\n"
            (apps / f"{names['main']}{i or ''}.desktop").write_text(
                f"[Desktop Entry]\nName={names['product']}\n{exec_line}Icon={names['main']}\n{line}", encoding="utf-8")
        if takes_files:
            for dest in window.LINUX_MIME_ICONS:
                (tree / dest.lstrip("/")).parent.mkdir(parents=True, exist_ok=True)
                (tree / dest.lstrip("/")).write_bytes(b"x")
        if with_icon:
            (tree / "usr" / "share" / "icons" / "hicolor" / "128x128" / "apps").mkdir(parents=True, exist_ok=True)
            (tree / "usr" / "share" / "icons" / "hicolor" / "128x128" / "apps" / f"{names['main']}.png").write_bytes(b"x")
        if with_mime_file:
            target = tree / window.LINUX_MIME_DEST.lstrip("/")
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text("<mime-info/>", encoding="utf-8")
        return tree

    depends = "libc6 (>= 2.35), libgtk-3-0, libwebkit2gtk-4.1-0"
    ok = deb_tree("deb_ok", names, window.LINUX_MIME + ";")
    check("350: an Idiograph .deb with the window, the server, one entry, its dependency and its file type is right",
          build_linux.deb_problems(ok, depends, names) == [])
    bad = build_linux.deb_problems(deb_tree("deb_bad", names, None, with_mime_file=False, with_server=False, desktops=2, with_icon=False), "libc6", names)
    check("350: a .deb missing the server (and so its typesetter), the dependency, the file type and with two entries says each",
          len(bad) == 10 and any("typesetter" in b for b in bad) and any("%F" in b for b in bad) and any("hicolor" in b for b in bad) and any("picture named" in b for b in bad) and any("frozen server" in b for b in bad) and any("libwebkit2gtk-4.1" in b for b in bad)
          and any("MimeType" in b for b in bad) and any("shared-mime-info" in b or "mime/packages" in b for b in bad)
          and any("2 desktop entries" in b for b in bad), str(bad))
    sift_ok = deb_tree("deb_sift", sift, None, with_mime_file=False)
    check("350: Sift's .deb with no file type is right", build_linux.deb_problems(sift_ok, depends, sift) == [])
    sift_claims = build_linux.deb_problems(deb_tree("deb_sift_claims", sift, window.LINUX_MIME), depends, sift)
    check("350: a Sift .deb that claims Idiograph's file type is refused", len(sift_claims) == 1 and "only Idiograph" in sift_claims[0], str(sift_claims))

    # the dry run says the window's step
    buf = io.StringIO()
    real_out = root / "dry"
    with contextlib.redirect_stdout(buf):
        code = build_linux.main(["--dry-run", "--window", "--out", str(real_out)])
    said = buf.getvalue()
    check("350: the dry run says the window's step, its two files and what the .deb must hold",
          code == 0 and "5. Would run Tauri" in said and "Idiograph-x86_64.AppImage" in said and "Idiograph-amd64.deb" in said
          and "libwebkit2gtk-4.1" in said and ".idiograph type" in said, said[-600:])
    try:
        build_linux.main(["--dry-run", "--test-app"])
        got = "no refusal"
    except SystemExit as exc:
        got = str(exc)
    check("350: --test-app without --window is refused", "goes with --window" in got, got)

    # the drive, against a stand-in window
    def driven(mode, app="idiograph", **kw):
        stub = root / f"window-{mode}-{app}.py"
        stub.write_text(STUB.format(python=sys.executable, mode=mode, app=app), encoding="utf-8", newline="")
        stub.chmod(stub.stat().st_mode | stat.S_IXUSR)
        try:
            with contextlib.redirect_stdout(io.StringIO()):
                drive_linux.drive(stub, "idiograph", root / f"out-{mode}-{app}", **kw)
            return "passed"
        except SystemExit as exc:
            return str(exc)

    check("350: the drive's environment has a home of its own, no XDG folder of the machine's, the port, software drawing and, for an AppImage, no FUSE",
          _env_ok(drive_linux))
    if os.name == "nt":
        # the drive starts a script by its #! line and ends its process group, as on Linux alone
        support.skip("350: the drive against a stand-in window", "the drive runs on Linux, not on Windows")
    else:
        got = driven("obey", start_wait=30, end_wait=15)
        check("350: a window whose server answers as the app, in a window, and which ends when asked passes", got == "passed", got)
        results = json.loads((root / "out-obey-idiograph" / "results.json").read_text(encoding="utf-8"))
        check("350: the results are kept: the server's answer, the page, the end and the port closed",
              results["server"]["app"] == "idiograph" and results["page_bytes"] > 0 and results["port_closed"] is True
              and results["ended_in_seconds"] is not None, str(results))
        got = driven("obey", app="sift", start_wait=30, end_wait=15)
        check("350: a server that answers as another app fails it", "answered as 'sift'" in got, got)
        got = driven("nowindow", start_wait=30, end_wait=15)
        check("350: a server the window did not start fails it", "started by the window" in got, got)
        got = driven("silent", start_wait=1.5, end_wait=1)
        check("350: a window that never answers fails it", "did not answer" in got, got)
        got = driven("stubborn", start_wait=30, end_wait=1.5)
        check("350: a window that will not end when asked fails it, and is ended", "did not end" in got, got)

    # the workflow's job
    workflow = support.source(".github/workflows/windows-installer.yml").read_text(encoding="utf-8")
    job = job_block(workflow, "linux-app")
    release = job_block(workflow, "release")
    check("350: the Linux window job is on ubuntu-22.04, allowed to fail and time-limited", "runs-on: ubuntu-22.04" in job
          and "continue-on-error: true" in job and "timeout-minutes:" in job, job[:300])
    check("350: it runs on a tag and on a dispatch that asks for it, and on no pull request",
          "github.ref_type == 'tag'" in job and "inputs.linux_app" in job and "pull_request" not in job.split("steps:")[0])
    check("350: the dispatch has its own input, off by default",
          re.search(r"linux_app:\n(?:        .*\n)*?        default: false", workflow) is not None)
    check("350: it installs WebKitGTK 4.1's development files, GTK 3, xvfb and what the AppImage's tools run on",
          all(p in job for p in ("libwebkit2gtk-4.1-dev", "libgtk-3-dev", "xvfb", "libfuse2", "patchelf", "librsvg2-dev", "libssl-dev")))
    check("350: it builds the tagged app, bundles the window and starts the AppImage under xvfb with a session bus",
          'release.py --which "$BUILD_FOR"' in job and 'build_linux.py --app "$APP" --smoke --window' in job
          and "xvfb-run -a dbus-run-session --" in job and "drive_linux.py" in job and "x86_64.AppImage" in job)
    check("350: it keeps both files as an artifact even when the start failed", "upload-artifact" in job and "!cancelled()" in job
          and "-amd64.deb" in job and "-x86_64.AppImage" in job)
    check("350, updated 9 November (linux57): the release job waits for Windows and the Mac, runs whatever the Linux job "
          "did, and takes its files only when the job said ok",
          "needs.windows.result == 'success'" in release and "needs.mac-app.result == 'success'" in release
          and "needs: [windows, mac-app, linux-app]" in release and "needs.linux-app.outputs.ok" in release)
    for other in ("windows", "mac-app"):
        check(f"350: the {other} job does not mention the Linux window's files", "AppImage" not in job_block(workflow, other))


def _frozen(root: Path) -> Path:
    """A made-up frozen folder for the stage to copy."""
    frozen = root / "frozen_missing_ok"
    (frozen / "_internal").mkdir(parents=True, exist_ok=True)
    (frozen / "Idiograph").write_bytes(b"x")
    return frozen


def _env_ok(drive_linux) -> bool:
    base = {"PATH": "/bin", "DISPLAY": ":99", "WAYLAND_DISPLAY": "w", "BROWSER": "b", "XDG_DATA_HOME": "/d", "HOME": "/real",
            "APPDIR": "/mnt", "APPIMAGE": "/x.AppImage"}
    env = drive_linux.environment(Path("/h"), 8123, base, appimage=True)
    plain = drive_linux.environment(Path("/h"), 8123, base, appimage=False)
    return (env["HOME"] == str(Path("/h")) and env["IDIOGRAPH_PORT"] == "8123" and env["IDIOGRAPH_STAY_OPEN"] == "1"
            and env["DISPLAY"] == ":99" and env["PATH"] == "/bin"
            and not any(k in env for k in ("WAYLAND_DISPLAY", "BROWSER", "XDG_DATA_HOME", "APPDIR", "APPIMAGE"))
            and env["WEBKIT_DISABLE_DMABUF_RENDERER"] == "1" and env["APPIMAGE_EXTRACT_AND_RUN"] == "1"
            and "APPIMAGE_EXTRACT_AND_RUN" not in plain)
