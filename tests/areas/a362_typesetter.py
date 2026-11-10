"""Area 362: the typesetter (typst1, 9 November 2026, Adam, 9 November about 18:10: Typst for every PDF and picture,
no fallback). On the source path, typst-py: `typeset.render` making a PDF and one PNG a page from a tiny invented
template with its data given as the input `data`, a template with an error raising `Failed` with the catalogue's
sentence and Typst's own words going to the log alone, and the fonts folder the only fonts, a page asking for a font
the folder lacks (one every Mac and Windows has) set in the folder's, never the system's. The frozen path against a
stand-in typesetter (not on Windows, which runs no script by its name): the data on its standard input, its PNGs
split, a failure, a typesetter that never ends and one that is not there each saying its own sentence. The pin: the
typesetter's crates at the Typst typst-py carries. The builds: the typesetter beside the frozen server on all three
systems, typst-py kept out of every frozen server, the .deb refused without it, and CI's tests installing typst-py.
The typesetter itself and the parity of its pages with typst-py's are proved by the builder and by mac_daily.py."""
from __future__ import annotations

import contextlib
import importlib.util
import io
import json
import re
import sys
from pathlib import Path

from . import support
from .support import check, skip

# an invented two-page view about a beekeeper's hives, its words from the data
TEMPLATE = """#let d = json(bytes(sys.inputs.data))
#set page(width: 100mm, height: 60mm, margin: 8mm)
#set text(font: "Charis SIL", size: 11pt)
= #text(font: "Nunito Sans")[#d.title]
#for hive in d.hives [
  #hive.name holds #hive.frames frames.
  #pagebreak(weak: true)
]
"""
DATA = {"title": "The apiary in spring", "hives": [{"name": "Hive Clover", "frames": 9}, {"name": "Hive Heather", "frames": 7}]}
# a page asking for fonts every Mac or Windows has and the folder does not
SYSTEM_FONTS = '#set text(font: ("Helvetica", "Arial", "Times New Roman", "DejaVu Sans"))\nThe smoker is lit.\n'
BROKEN = '#let d = json(bytes(sys.inputs.data))\n#d.title.no-such-field(\n'


def load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def font_names(pdf: bytes) -> set[str]:
    """Each font the PDF embeds by its BaseFont, its subset tag taken off."""
    import pdftext
    names = set()
    for body in pdftext.objects(pdf).values():
        for m in re.finditer(rb"/BaseFont\s*/(?:[A-Z]{6}\+)?([^\s/<>\[\]()]+)", pdftext.head_of(body)):
            names.add(m.group(1).decode("latin-1"))
    return names


def test_typesetter(scratch: Path):
    print("\n362. The typesetter: Typst's pages from a template and its data, its failures, its fonts and its builds")
    import i18n
    import pdftext
    import typeset
    root = scratch / "typesetter"
    root.mkdir(parents=True, exist_ok=True)
    (root / "hives.typ").write_text(TEMPLATE, encoding="utf-8")
    (root / "system.typ").write_text(SYSTEM_FONTS, encoding="utf-8")
    (root / "broken.typ").write_text(BROKEN, encoding="utf-8")

    # ── A. the source path, typst-py
    try:
        import typst  # noqa: F401
        have_typst = True
    except ImportError:
        have_typst = False
    if not have_typst:
        skip("362: typst-py's pages", f"typst-py {typeset.TYPST_PY} is not installed here")
    else:
        pdf = typeset.render(root / "hives.typ", DATA)
        pages = pdftext.pages_text(pdf) if isinstance(pdf, bytes) else []
        check("362: render makes a PDF from the template and its data, one page a hive, the words the data's",
              typeset.engine() == "typst-py" and isinstance(pdf, bytes) and pdf.startswith(b"%PDF-") and len(pages) == 2
              and "The apiary in spring" in pages[0] and "Hive Clover holds 9 frames" in pages[0]
              and "Hive Heather holds 7 frames" in pages[1], str(pages))
        pngs = typeset.render(root / "hives.typ", DATA, fmt="png", ppi=72)
        big = typeset.render(root / "hives.typ", DATA, fmt="png", ppi=144)
        width = lambda png: int.from_bytes(png[16:20], "big")
        check("362: fmt png makes one PNG a page at the ppi asked, 100 mm wide at 72 and twice that at 144",
              isinstance(pngs, list) and len(pngs) == 2 and all(p.startswith(b"\x89PNG\r\n\x1a\n") for p in pngs)
              and abs(width(pngs[0]) - 283) <= 1 and abs(width(big[0]) - 2 * width(pngs[0])) <= 1,
              str([width(p) for p in pngs] + [width(p) for p in big]))
        names = font_names(pdf)
        check("362: the page is set in the app's own fonts, Charis SIL and Nunito Sans",
              any(n.startswith("CharisSIL") for n in names) and any(n.startswith("NunitoSans") for n in names), str(names))
        system = font_names(typeset.render(root / "system.typ", {}))
        check("362: a page asking for Helvetica, Arial, Times New Roman or DejaVu Sans is set in a font of the folder's, "
              "never the system's",
              bool(system) and all(n.startswith(("CharisSIL", "NunitoSans")) for n in system), str(system))
        log = io.StringIO()
        try:
            with contextlib.redirect_stderr(log):
                typeset.render(root / "broken.typ", DATA)
            said = None
        except typeset.Failed as exc:
            said = str(exc)
        check("362: a template with an error raises Failed with the catalogue's plain sentence, Typst's words in the log alone",
              said == i18n.t("typeset.failed") and "typeset:" in log.getvalue() and "broken.typ" in log.getvalue()
              and "broken.typ" not in (said or ""), f"{said!r} / {log.getvalue()[-300:]!r}")
        try:
            typeset.render(root / "hives.typ", DATA, fmt="svg")
            refused = False
        except ValueError:
            refused = True
        check("362: a format other than pdf or png is refused", refused)

    # ── B. the frozen path, against a stand-in typesetter
    check("362: the frozen app's typesetter is found beside the executable the server runs as",
          typeset.helper_path(str(Path("/Applications/Idiograph.app/Contents/Resources/server/Idiograph")))
          == Path("/Applications/Idiograph.app/Contents/Resources/server").resolve() / ("idiograph-typeset"
                                                                                       + (".exe" if sys.platform == "win32" else "")))
    if sys.platform == "win32":
        skip("362: the frozen path against a stand-in", "Windows runs no script by its name")
    else:
        stand = root / "stand-in"
        stand.write_text(
            f"#!{sys.executable}\n"
            "import sys, json, time\n"
            "a = sys.argv[1:]\n"
            "data = json.loads(sys.stdin.read())\n"
            "if data.get('fail'): sys.stderr.write('error: hives.typ:3:1: unknown variable: honey\\n'); sys.exit(1)\n"
            "if data.get('slow'): time.sleep(30)\n"
            "fmt = a[a.index('--format') + 1]\n"
            "out = sys.stdout.buffer\n"
            "if fmt == 'pdf': out.write(b'%PDF-1.7 ' + data['title'].encode())\n"
            "else:\n"
            "    for n in range(2):\n"
            "        page = b'\\x89PNG page ' + str(n).encode() + b' ' + a[a.index('--ppi') + 1].encode()\n"
            "        out.write(len(page).to_bytes(8, 'big') + page)\n",
            encoding="utf-8")
        stand.chmod(0o755)
        tpl = (root / "hives.typ").resolve()
        text = json.dumps(DATA)
        pdf = typeset.by_helper(stand, tpl, text, "pdf", 144.0)
        pngs = typeset.by_helper(stand, tpl, text, "png", 96.0)
        check("362: the typesetter gets the data on its standard input and its PDF comes back whole",
              pdf == b"%PDF-1.7 The apiary in spring", str(pdf[:40]))
        check("362: its PNGs come back split, one a page, at the ppi asked",
              pngs == [b"\x89PNG page 0 96", b"\x89PNG page 1 96"], str(pngs))
        cmd = typeset.helper_command(stand, tpl, "png", 96.0)
        check("362: it is given the template's folder as the root, the fonts folder and nothing else of the disk",
              cmd[1:7] == ["--root", str(tpl.parent), "--main", "hives.typ", "--fonts", str(typeset.fonts_dir())]
              and (typeset.fonts_dir() / "CharisSIL-Regular-latin.ttf").is_file(), str(cmd))
        sentences = []
        for data, limit, helper in (({"fail": True}, 20, stand), ({"slow": True}, 1, stand), ({}, 20, root / "none")):
            log = io.StringIO()
            try:
                with contextlib.redirect_stderr(log):
                    typeset.by_helper(helper, tpl, json.dumps(data), "pdf", 144.0, limit=limit)
                sentences.append((None, ""))
            except typeset.Failed as exc:
                sentences.append((str(exc), log.getvalue()))
        check("362: a failure, a typesetter past its time and one not there each say the catalogue's own sentence",
              [s for s, _ in sentences] == [i18n.t("typeset.failed"), i18n.t("typeset.slow"), i18n.t("typeset.missing")],
              str([s for s, _ in sentences]))
        check("362: the typesetter's own diagnostics go to the server's log",
              "unknown variable: honey" in sentences[0][1] and "hives.typ:3:1" in sentences[0][1], sentences[0][1][-200:])
        try:
            typeset.split_pages((9).to_bytes(8, "big") + b"cut")
            cut = False
        except ValueError:
            cut = True
        check("362: a PNG stream cut short is refused, not taken as pages", cut)

    # ── C. the pin and the builds
    cargo = support.text("packaging/tauri/typeset/Cargo.toml")
    pins = dict(re.findall(r'^(typst(?:-pdf|-layout|-render)?) = "=([0-9.]+)"$', cargo, re.M))
    lock = support.text("packaging/tauri/typeset/Cargo.lock")
    locked = dict(re.findall(r'name = "(typst(?:-pdf|-layout|-render)?)"\nversion = "([0-9.]+)"', lock))
    check("362: the typesetter's four typst crates are pinned with = to the Typst typst-py carries, and Cargo.lock agrees",
          pins == {k: typeset.TYPST for k in ("typst", "typst-pdf", "typst-layout", "typst-render")} and locked == pins
          and "lto = true" in cargo and 'opt-level = "s"' in cargo, f"{pins} {locked}")
    if have_typst:
        from importlib.metadata import version
        check("362: the typst-py here is the one pinned", version("typst") == typeset.TYPST_PY, version("typst"))
    build_mac = support.build_mac()
    spec = build_mac.write_spec(root, _stage(root, build_mac), "9.9.9")
    linux = load("idiograph_362_build_linux", support.source("packaging") / "build_linux.py")
    windows = load("idiograph_362_build_windows", support.source("packaging") / "build_windows.py")
    specs = [spec.read_text(encoding="utf-8"), linux.write_spec(root, root / "stage").read_text(encoding="utf-8"),
             windows.write_spec(root, root / "stage").read_text(encoding="utf-8")]
    check("362: no frozen server takes typst-py, on the Mac, Linux or Windows, and each takes typeset",
          all("'typst'" in s and "'typeset'" in s for s in specs))
    sources = support.text("packaging/build_mac.py", "packaging/build_windows.py", "packaging/build_linux.py")
    check("362: each system's build puts the typesetter beside the frozen server and typesets a line with it",
          sources.count("typeset_helper.place(typeset_helper.build(build), frozen)") == 3
          and sources.count("typeset_helper.check(") == 3)
    helper = load("idiograph_362_typeset_helper", support.source("packaging") / "typeset_helper.py")
    cmd = helper.build_command(Path("/b/typeset-target"))
    check("362: cargo builds it release and locked, into the build's own folder",
          cmd[:4] == ["cargo", "build", "--release", "--locked"] and "/b/typeset-target" in [c.replace("\\", "/") for c in cmd]
          and helper.exe_name(True) == "idiograph-typeset.exe" and helper.exe_name(False) == "idiograph-typeset")
    tree = root / "deb"
    server = tree / "usr" / "lib" / "Idiograph" / "server"
    (server / "_internal").mkdir(parents=True, exist_ok=True)
    (server / "Idiograph").write_text("", encoding="utf-8")
    names = {"product": "Idiograph", "main": "idiograph", "name": "Idiograph", "app": "sift", "test": True}
    without = linux.deb_problems(tree, linux.WEBKIT_PACKAGE, names)
    (server / "idiograph-typeset").write_text("", encoding="utf-8")
    (server / "idiograph-typeset").chmod(0o755)
    with_it = linux.deb_problems(tree, linux.WEBKIT_PACKAGE, names)
    check("362: check_deb refuses a .deb without the typesetter beside the server",
          any("typesetter" in p for p in without) and not any("typesetter" in p for p in with_it), str(without))
    flow = support.text(".github/workflows/windows-installer.yml")
    check("362: CI's three test jobs install typst-py at the pin",
          flow.count(f"typst=={typeset.TYPST_PY}") == 3)
    daily = load("idiograph_362_mac_daily", support.source("packaging") / "mac_daily.py")
    app = Path("/x/Idiograph.app")
    check("362: mac_daily.py looks for the typesetter beside the server inside the app",
          daily.typesetter_of(app) == app / "Contents" / "Resources" / "server" / "idiograph-typeset")


def _stage(root: Path, build_mac) -> Path:
    """A stage holding what the spec names, a config and nothing else."""
    stage = root / "stage"
    stage.mkdir(exist_ok=True)
    (stage / "config.json").write_text("{}\n", encoding="utf-8")
    return stage
