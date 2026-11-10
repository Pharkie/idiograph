"""Area 356: Sift and Trace on Linux, each its own build (linux9, 9 November 2026, build 9 of the Linux plan). The
Linux build takes the app it is asked for as the Mac's and Windows's do, and the three come out as three apps. Here,
on any machine, for each of Idiograph, Sift and Trace: what a Linux build lays over tauri.conf.json (the product
and executable's name, the identifier, the app's own icon files and its update address, the .idiograph type for
Idiograph alone), the AppImage's and .deb's names in the builder and in release.py, the frozen executable's name
telling the server which app it is, what `check_deb` asks of an unpacked .deb (made up here) including the
desktop entry's own icon and no file type for Sift and Trace, the dry run, and the workflow taking the app from the
tag. What only a CI run on a tag proves (Tauri's bundler writing the entry, the icons landing under their names,
the AppImage starting) is not here. All made-up folders. Nothing here uses a participant's words."""
from __future__ import annotations

import contextlib
import importlib.util
import io
import re
import shutil
import subprocess
import sys
from pathlib import Path

from . import support
from .support import check

APPS = ("idiograph", "sift", "trace")
LABEL = {"idiograph": "Idiograph", "sift": "Sift", "trace": "Trace"}


def job_block(workflow: str, job: str) -> str:
    found = re.search(rf"^  {re.escape(job)}:\n(.*?)(?=^  [A-Za-z0-9_-]+:\n|\Z)", workflow, re.S | re.M)
    return found.group(1) if found else ""


def test_linux_three_apps(scratch: Path):
    print("\n356. Sift and Trace on Linux: each app's names, icons, update address, file type, .deb contents and tag (linux9)")
    sys.path.insert(0, str(support.source("packaging")))

    def load(name, folder="packaging"):
        spec = importlib.util.spec_from_file_location(f"idiograph_356_{name}", support.source(folder) / f"{name}.py")
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        return mod

    build_linux = load("build_linux")
    release = load("release")
    window = build_linux.window
    app_identity = build_linux.app_identity
    src = support.source("packaging/tauri/src-tauri")
    root = scratch / "linux_three"
    shutil.rmtree(root, ignore_errors=True)
    root.mkdir(parents=True)

    # A. what a Linux build lays over tauri.conf.json, per app
    over = {a: window.overrides("1.2.3", False, None, None, a, True) for a in APPS}
    names = {a: build_linux.window_names(a, False) for a in APPS}
    for a in APPS:
        ident, label = app_identity.APPS[a], LABEL[a]
        conf = over[a]
        check(f"356: {label}'s Linux window is named for itself, with its own identifier and the version",
              names[a]["product"] == label and names[a]["main"] == label and names[a]["name"] == label
              and conf.get("version") == "1.2.3"
              and conf.get("identifier", ident["bundle_id"]) == ident["bundle_id"], str(names[a]))
        icons = conf.get("bundle", {}).get("icon")
        folder = window.icon_dir(a)
        if a == "idiograph":
            check("356: Idiograph keeps tauri.conf.json's own icons", icons is None and folder == "icons")
        else:
            check(f"356: {label}'s Linux window names its own icon files, each there on disk",
                  icons == [f"{folder}/{f}" for f in window.ICON_FILES] and folder == f"icons/{a}"
                  and all((src / i).is_file() for i in icons), str(icons))
        endpoint = conf.get("plugins", {}).get("updater", {}).get("endpoints", [None])[0]
        if a == "idiograph":
            base = (src / "tauri.conf.json").read_text(encoding="utf-8")
            check("356: Idiograph's update address is tauri.conf.json's own, its releases repository's",
                  endpoint is None and ident["releases"] in base and "latest.json" in base)
        else:
            check(f"356: {label}'s update address is its own releases repository's latest.json, on GitHub over https",
                  endpoint == f"https://github.com/{ident['releases']}/releases/latest/download/latest.json"
                  and ident["releases"].lower().startswith("pharkie/" + a), str(endpoint))
        got = conf.get("bundle", {})
        if a == "idiograph":
            kinds = got.get("fileAssociations") or []
            check("356: Idiograph's Linux build claims .idiograph, with the mime type and the .deb's mime file",
                  len(kinds) == 1 and kinds[0]["mimeType"] == window.LINUX_MIME
                  and got["linux"]["deb"]["files"] == {window.LINUX_MIME_DEST: window.LINUX_MIME_FILE, **window.LINUX_MIME_ICONS}
                  and got["linux"]["deb"]["desktopTemplate"] == window.LINUX_DESKTOP_TEMPLATE)
        else:
            check(f"356: {label}'s Linux build has no file type and no mime file, so .idiograph stays Idiograph's",
                  got.get("fileAssociations", "absent") is None and "files" not in got.get("linux", {}).get("deb", {}), str(got))

    pictures = {a: (src / window.icon_dir(a) / "128x128.png").read_bytes() for a in APPS}
    check("356: the three apps' 128 pixel icons are three different pictures", len(set(pictures.values())) == 3)
    check("356: the Linux resource file is shared, carrying the server as server/ for each app alike",
          '"../../../build/tauri-server/": "server/"' in (src / "tauri.linux.conf.json").read_text(encoding="utf-8"))

    # B. the files each build writes, and release.py's names for them
    for a in APPS:
        label, rel = LABEL[a], release.names(a)
        check(f"356: {label}'s builder and release.py agree on the AppImage's and .deb's names, which carry {label}",
              names[a]["appimage"] == rel["linux"] == f"{label}-x86_64.AppImage"
              and names[a]["deb"] == rel["deb"] == f"{label}-amd64.deb"
              and rel["linux_files"] == (names[a]["appimage"], names[a]["deb"]), f"{names[a]} {rel}")
        check(f"356: {label}'s frozen executable, named {label}, tells the server which app it is",
              app_identity.from_executable(f"/usr/lib/{label}/server/{label}") == a
              and build_linux.name_of(a) == label and build_linux.smoke_command(Path("/x"), 1234, a)[0] == Path("/x") / label)
    check("356: each app's test app is named for its app and is no real app's name", all(
        build_linux.window_names(a, True)["product"] == f"{LABEL[a]} Test" for a in APPS))
    rs = (src / "src" / "app.rs").read_text(encoding="utf-8")
    check("356: the window knows its app by its executable's name, which on Linux is the product name, for all three",
          all(f'name: "{LABEL[a]}"' in rs for a in APPS) and "eq_ignore_ascii_case" in rs)

    # C. check_deb's expectations, per app, on made-up unpacked .debs
    depends = "libc6 (>= 2.35), libgtk-3-0, libwebkit2gtk-4.1-0"

    def tree(a, tag, mime=False, icon=True, entry_icon=True):
        n = names[a]
        t = root / f"{a}-{tag}"
        (t / "usr" / "bin").mkdir(parents=True)
        (t / "usr" / "bin" / n["main"]).write_bytes(b"x")
        srv = t / "usr" / "lib" / n["product"] / "server"
        (srv / "_internal").mkdir(parents=True)
        (srv / n["name"]).write_bytes(b"x")
        # the typesetter beside the server (typst1, 9 November 2026)
        (srv / "idiograph-typeset").write_bytes(b"x")
        (srv / "idiograph-typeset").chmod(0o755)
        apps = t / "usr" / "share" / "applications"
        apps.mkdir(parents=True)
        # Idiograph's own claims the type, takes files on its Exec line and has the type's icon (linuxfix)
        takes = a == "idiograph" and mime
        lines = (f"[Desktop Entry]\nName={n['product']}\nExec={n['main']}{' %F' if takes else ''}\n"
                 + (f"Icon={n['main']}\n" if entry_icon else ""))
        if mime:
            lines += f"MimeType={window.LINUX_MIME};\n"
        if takes:
            for dest in window.LINUX_MIME_ICONS:
                (t / dest.lstrip("/")).parent.mkdir(parents=True, exist_ok=True)
                (t / dest.lstrip("/")).write_bytes(b"x")
        (apps / f"{n['main']}.desktop").write_text(lines, encoding="utf-8")
        if icon:
            pic = t / "usr" / "share" / "icons" / "hicolor" / "128x128" / "apps"
            pic.mkdir(parents=True, exist_ok=True)
            (pic / f"{n['main']}.png").write_bytes(b"x")
        if a == "idiograph" and mime:
            target = t / window.LINUX_MIME_DEST.lstrip("/")
            target.parent.mkdir(parents=True)
            target.write_text("<mime-info/>", encoding="utf-8")
        return t

    for a in APPS:
        label = LABEL[a]
        claims_type = a == "idiograph"
        right = build_linux.deb_problems(tree(a, "ok", mime=claims_type), depends, names[a])
        check(f"356: {label}'s .deb with its window, server, one entry with its own icon and "
              f"{'the .idiograph type' if claims_type else 'no file type'} is right", right == [], str(right))
        no_icon = build_linux.deb_problems(tree(a, "noicon", mime=claims_type, icon=False), depends, names[a])
        no_line = build_linux.deb_problems(tree(a, "noline", mime=claims_type, entry_icon=False), depends, names[a])
        check(f"356: {label}'s .deb with no picture for its entry's icon, or an entry with no Icon line, is refused",
              len(no_icon) == 1 and "picture named" in no_icon[0] and len(no_line) == 1 and "no Icon line" in no_line[0],
              f"{no_icon} {no_line}")
        other = [x for x in APPS if x != a][0]
        wrong = build_linux.deb_problems(tree(other, f"for-{a}", mime=other == "idiograph"), depends, names[a])
        check(f"356: {LABEL[other]}'s files do not pass for {label}'s .deb", len(wrong) >= 2, str(wrong))
        if a != "idiograph":
            claims = build_linux.deb_problems(tree(a, "claims", mime=True), depends, names[a])
            check(f"356: a {label} .deb claiming Idiograph's file type is refused",
                  len(claims) == 1 and "only Idiograph" in claims[0], str(claims))
    mine = build_linux.deb_problems(tree("idiograph", "nomime"), depends, names["idiograph"])
    check("356: an Idiograph .deb without the file type, %F or the type's icon is still refused", len(mine) == 4, str(mine))

    # D. the dry run, per app
    for a in APPS:
        label = LABEL[a]
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            code = build_linux.main(["--app", a, "--dry-run", "--window", "--out", str(root / f"dry-{a}")])
        said = buf.getvalue()
        spec = (root / f"dry-{a}" / "build" / f"{label}-linux.spec").read_text(encoding="utf-8")
        check(f"356: the dry run for {label} names its files, its server folder, its executable and "
              f"{'the .idiograph type' if a == 'idiograph' else 'no file type'}, and writes its own spec",
              code == 0 and f"{label}-x86_64.AppImage" in said and f"{label}-amd64.deb" in said
              and f"usr/lib/{label}/server" in said and f"usr/bin/{label}" in said
              and (".idiograph type" in said) == (a == "idiograph")
              and (a == "idiograph" or "no file type" in said) and f"name='{label}'" in spec, said[-500:])
        for other in APPS:
            if other != a:
                check(f"356: the dry run for {label} never names {LABEL[other]}'s files",
                      f"{LABEL[other]}-x86_64" not in said and f"{LABEL[other]}-amd64" not in said)

    # E. the workflow takes the app from the tag
    workflow = (support.source(".github/workflows/windows-installer.yml")).read_text(encoding="utf-8")
    job = job_block(workflow, "linux-app")
    check("356: a tag of any of the three apps starts the workflow, and the run's app is read from the tag by release.py --which",
          'tags: ["v*", "idiograph-v*", "sift-v*", "trace-v*"]' in workflow
          and "BUILD_FOR: ${{ github.ref_type == 'tag' && github.ref_name || inputs.app || 'idiograph' }}" in workflow
          and 'release.py --which "$BUILD_FOR" >> "$GITHUB_ENV"' in job)
    check("356: the Linux job builds, drives, keeps and names the app it was given, never a name written into it",
          'build_linux.py --app "$APP" --smoke --window' in job
          and '--app "dist/${APP_NAME}-x86_64.AppImage" --id "$APP"' in job
          and "dist/${{ env.APP_NAME }}-x86_64.AppImage" in job and "dist/${{ env.APP_NAME }}-amd64.deb" in job
          and "name: ${{ env.APP_NAME }}-Linux" in job
          and not re.search(r"\b(Idiograph|Sift|Trace)-(x86_64|amd64)", job), job[:200])

    def which(value):
        return subprocess.run([sys.executable, str(support.source("packaging/release.py")), "--which", value],
                              capture_output=True, text=True, encoding="utf-8", timeout=60).stdout
    check("356: the tags v0.9.22, idiograph-v0.9.22, sift-v1.0.0 and trace-v1.0.0 pick Idiograph, Idiograph, Sift and Trace",
          [which(t) for t in ("v0.9.22", "idiograph-v0.9.22", "sift-v1.0.0", "trace-v1.0.0")]
          == ["APP=idiograph\nAPP_NAME=Idiograph\n"] * 2 + ["APP=sift\nAPP_NAME=Sift\n", "APP=trace\nAPP_NAME=Trace\n"])
    rel_job = job_block(workflow, "release")
    check("356: the release job takes the Linux files by the app's name too, from that app's own artifact",
          '"$APP_NAME-x86_64.AppImage" "$APP_NAME-amd64.deb"' in rel_job and "name: ${{ env.APP_NAME }}-Linux" in rel_job)
