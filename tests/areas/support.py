"""What the suite's areas share: where the app and its fixtures are, the check counter and its two
calls, check and skip, the demo fixture, the helpers and constants more than one area uses, and the
suite's own checks that close every run. An area imports from here what it needs, so nothing shared
is written twice (17 October)."""
from __future__ import annotations

import contextlib
import json
import os
import re
import shutil
import signal
import subprocess
import sys
import time
from pathlib import Path

import openpyxl
from openpyxl.cell.rich_text import CellRichText, TextBlock

# every app module the suite has imported at its start from the first, loaded here before any area
# runs, whichever area uses it
import ai_suggest as ai_mod
import audio as audio_mod
import corpus
import export as export_mod
import make_app
import nudges
import rounds as rounds_mod
import workbook as wb_mod
from workbook import WorkbookError

# the suite's own folder, tests, which holds this package, and the app's folder above it
HERE = Path(__file__).resolve().parent.parent
TOOL = HERE.parent

# Every file the areas read is named by its path as it is now, `family/static/shell.js` or
# `apps/sift/sift.py` (the family codebase's sixth build, 23 October 2026). Until then an alias table took a
# file's path from before the family's folders to where it was, app.js to shell.js and distil.js among them.
# A page file split in two is read as one text through `text`, its parts in order: app.js was the family's
# shell and Idiograph's distil.js, style.css the family's and distil.css.
APP_JS = ("family/static/shell.js", "apps/idiograph/static/distil.js")


def source(path: str) -> Path:
    """A file of the app's folder by its path from it, `family/static/shell.js` or `server.py`."""
    return TOOL / path


def same_workbook(a_path, b_path) -> bool:
    """Two .xlsx files the same: byte for byte, or, written by another Python whose XML writer spells
    one tree differently (3.11 writes `<x />` where 3.14 writes `<x/>`, 14 October), the same parts
    in the same order holding the same trees, every namespace resolved and every word kept."""
    import zipfile
    from xml.etree import ElementTree as ET

    def tree(el):
        return (el.tag, tuple(sorted(el.attrib.items())), el.text or "", el.tail or "", tuple(tree(c) for c in el))

    if Path(a_path).read_bytes() == Path(b_path).read_bytes():
        return True
    with zipfile.ZipFile(a_path) as za, zipfile.ZipFile(b_path) as zb:
        if za.namelist() != zb.namelist():
            return False
        for name in za.namelist():
            x, y = za.read(name), zb.read(name)
            if x != y and (not name.endswith((".xml", ".rels")) or tree(ET.fromstring(x)) != tree(ET.fromstring(y))):
                return False
    return True


def text(*paths: str) -> str:
    """The text of the app's files by their paths from its folder, joined in order, one file's text for one. Sift's
    scripts read with the words they take from the catalogue by key alone put back as English (`english_js`), as
    the checks written before those words moved read them (siftlang, 1 November 2026)."""
    return "\n".join(english_js(t) if path.startswith("apps/sift/static/") and path.endswith(".js") else t
                     for path in paths for t in [(TOOL / path).read_text(encoding="utf-8")])


def section(text: str, name: str) -> str:
    """A script's section by its heading's name, the text after `/* ─── name ── */` to the next heading, as the
    page's scripts mark them, wherever in the shell or Distil the fifth build put it."""
    after = text.split(f" {name} ── */", 1)[1]
    head = re.search(r"^/\* ──", after, re.M)
    return after[:head.start()] if head else after


def distil_hooks(app: str | None = None) -> str:
    """Idiograph's part registered with the family, `FAMILY_APPS.idiograph = {...};` from distil.js, with the
    shell's `appsSay` and `appsKeys` that ask it, for a node harness that runs a piece of the page whose family
    function asks an app (the fifth build, 23 October 2026). The harness defines FAMILY_APPS first."""
    app = text(*APP_JS) if app is None else app
    reg = "FAMILY_APPS.idiograph = {" + app.split("\nFAMILY_APPS.idiograph = {", 1)[1].split("\n};\n", 1)[0] + "\n};\n"
    asks = "".join("function " + name + app.split(f"\nfunction {name}", 1)[1].split("\n}\n", 1)[0] + "\n}\n"
                   for name in ("appsSay", "appsKeys"))
    return asks + reg


KEYS_AT = (("if (appsKeys('keysEscape', e)) return;", "distilKeysEscape"),
           ("if (appsKeys('keysEscapeLast', e)) return;", "distilKeysEscapeLast"),
           ("if (appsKeys('keysCards', e)) return;", "distilKeysCards"),
           ("appsKeys('keys', e);", "distilKeys"))


def keydown_text(app: str | None = None) -> str:
    """The page's one keydown as the keys meet it, as one text: since the fifth build (23 October 2026) the
    family's handler in shell.js asks each app's keys in their turn (`appsKeys`), and Distil's are four functions
    of distil.js, each put back here where the handler asks for it, its `return true` a `return` again, as
    app.js's handler had them, at its depth. `app` is app.js's text, the shell's and Distil's joined (`text`)."""
    app = text(*APP_JS) if app is None else app
    body = app.split("document.addEventListener('keydown', (e) => {", 1)[1].split("\n  });", 1)[0]
    for line, name in KEYS_AT:
        fn = app.split(f"\nfunction {name}(e) {{\n", 1)[1].split("\n}\n", 1)[0]
        fn = fn.replace("return true;", "return;").replace("\n  return false;", "")
        # each line at the handler's depth again, where the call stands, as app.js's handler had it
        at = body.index(line)
        indent = at - body.rfind("\n", 0, at) - 1
        fn = "\n".join((" " * (indent - 2) + ln) if ln.strip() else ln for ln in fn.split("\n")).lstrip(" ")
        body = body.replace(line, fn, 1)
    return body


def page_text(path: str = "family/static/page.html", app: str | None = None) -> str:
    """The family's page, family/static/page.html or design.html, as the server serves it to `app`, the suite's
    own by default, Idiograph: each slot filled with the app's parts of it, Sift's from apps/sift/static/sift.html
    and Trace's from apps/trace/static/trace.html (`server.assembled`, 22 October 2026). Since the cutover (the
    sixth build, 23 October 2026) each app's page holds its own parts alone."""
    import server
    return server.assembled(text(path), app)


def i18n_js(app: str | None = None) -> str:
    """The text layer for a harness that runs the page's scripts in node (i18ncore, 28 October 2026): the catalogue
    in English as the served page has it, `var I18N = ...`, then family/static/i18n.js, so t(), tDate and tList
    answer as on the page. Put it before the script's pieces."""
    import boot
    import i18n
    import server
    # with no app named, every app's catalogue, so a piece of Sift's scripts run beside the family's finds its
    # words whichever app the area answers as (siftlang, 1 November 2026)
    inline = i18n.script("en", boot.roots(server.apps_served(app)) if app else boot.roots())
    return inline[len("<script>"):-len("</script>")] + "\n" + text("family/static/i18n.js") + "\n"


def english_js(code: str) -> str:
    """A script's text with each word it takes from the catalogue by key alone put back as the English it reads
    (siftlang, 1 November 2026), for a check that reads a script's own text as it stood before its words moved: a
    `${esc(t('key'))}` or `${escAttr(t('key'))}` inside a template becomes its words, escaped, and a `t('key')`
    with no slots a quoted literal, in double quotes where the words hold an apostrophe. A message with slots or a
    count's forms is left as its call, which a check names by its key."""
    import html as html_mod
    import boot
    import i18n
    words = i18n.messages("en", boot.roots())

    def plain(key):
        said = words.get(key)
        return said if isinstance(said, str) else None

    def inline(m):
        said = plain(m.group(2))
        if said is None:
            return m.group(0)
        out = html_mod.escape(said, quote=False)
        return out.replace('"', "&quot;") if m.group(1) == "escAttr" else out

    def literal(m):
        said = plain(m.group(1))
        if said is None or "\n" in said or "\\" in said or ("'" in said and '"' in said):
            return m.group(0)
        return f'"{said}"' if "'" in said else f"'{said}'"

    code = re.sub(r"\$\{(esc|escAttr)\(t\('([a-z_][\w.]*)'\)\)\}", inline, code)
    return re.sub(r"\bt\('([a-z_][\w.]*)'\)", literal, code)


def node_text_layer(scratch: Path) -> None:
    """Every script a check runs in node with the text layer in front of it, as the page loads i18n.js before
    every other script (siftlang, 1 November 2026, when Sift's own words moved into the catalogue): a preload in
    the scratch folder, named in NODE_OPTIONS for this process and its children, runs the English catalogue,
    i18n.js and the shell's esc and escAttr in node's global scope, so a piece of sift.js or sift_search.js finds
    t() as on the page. A harness that puts `i18n_js()` first itself still does, its own taking the place of the
    preload's."""
    preload = Path(scratch) / "node-text-layer.js"
    # and the shell's esc and escAttr, which the words put into markup pass through, as every page has them
    shell = text("family/static/shell.js").splitlines()
    escapes = "".join(ln + "\n" for ln in shell if ln.startswith(("const esc = ", "const escAttr = ")))
    preload.write_text("require('vm').runInThisContext(" + json.dumps(i18n_js() + escapes) + ");\n", encoding="utf-8")
    _NODE_OPTIONS.setdefault("before", os.environ.get("NODE_OPTIONS", ""))
    os.environ["NODE_OPTIONS"] = (_NODE_OPTIONS["before"] + " --require " + json.dumps(str(preload))).strip()


# the NODE_OPTIONS the suite found, before node_text_layer added its preload
_NODE_OPTIONS: dict = {}


def run_node(script: str, scratch: Path, name: str = "node-run.js", timeout: int = 30):
    """`script` run by node from a file of its own in the area's scratch, never on node's command line with
    -e: a script carrying the catalogue (i18n_js) runs past Windows's 32,767 characters there, WinError 206
    (the 0.9.11 tag run, 28 October 2026). Answers the finished process, its output as UTF-8 text."""
    path = Path(scratch) / name
    path.write_text(script, encoding="utf-8")
    return subprocess.run([shutil.which("node") or "node", str(path)], capture_output=True, text=True,
                          encoding="utf-8", timeout=timeout)


def every_page(path: str = "family/static/page.html") -> str:
    """The family's page with every app's parts in its slots, in the family's order, as Idiograph's page was
    until the cutover (the sixth build, 23 October 2026), for a check over the markup of all three apps at
    once. No server serves it: each app's page holds its own parts alone."""
    import boot
    import server
    parts: dict = {}
    for app in boot.APPS:
        for slot, part in server.page_parts(app).items():
            parts[slot] = parts.get(slot, "") + part
    # and its words filled from the catalogue in English, as each app's served page has them (i18ncore, 28 October 2026)
    import i18n
    return i18n.fill(server.SLOT.sub(lambda m: parts.get(m.group(1), ""), text(path)), "en", boot.roots(), {"app": "Idiograph"})


@contextlib.contextmanager
def as_app(app: str):
    """The suite's server and command line answering as `app`, Sift or Trace, in this process (the sixth
    build, 23 October 2026, when Idiograph stopped answering for them): the app that answers routes, commands
    and the page changes, and the paths the area set stay. No first start copies anything into an area's
    settings, as a run with --config copies nothing."""
    import app_identity
    import cli
    import server
    kept = (server.APP, server.IDENTITY, server.VERSION, cli.first_start)
    server.APP, server.IDENTITY, server.VERSION = app, app_identity.identity(app), app_identity.version(app)
    cli.first_start = lambda *_: False
    try:
        yield
    finally:
        server.APP, server.IDENTITY, server.VERSION, cli.first_start = kept


def build_mac():
    """packaging/build_mac.py as a module, for a check of what each app's build ships (its folder lists, which
    since the sixth build, 23 October 2026, are each app's own and the family's)."""
    import importlib
    folder = str(TOOL / "packaging")
    if folder not in sys.path:
        sys.path.insert(0, folder)
    return importlib.import_module("build_mac")


def code_files(pattern: str = "*.py") -> list[Path]:
    """The app's own files matching `pattern` in each folder its modules sit in, the root, family/ and
    each app's under apps/ (boot.py), sorted by name, so a check over every module finds a moved one."""
    folders = [TOOL, TOOL / "family"] + sorted(p for p in (TOOL / "apps").glob("*") if p.is_dir())
    return sorted((p for folder in folders for p in folder.glob(pattern) if p.is_file()), key=lambda p: p.name)


def static_folders() -> list[Path]:
    """Every static/ folder of the page, the family's and each app's, the one place a check over every page
    file looks (the sixth build, 23 October 2026, where a check of the root's old static/ found nothing)."""
    return [TOOL / "family" / "static"] + sorted(p / "static" for p in (TOOL / "apps").glob("*") if (p / "static").is_dir())


# The reference checks read real study data on the maintainer's Mac: finished cases, a corpus of
# statements and participants' transcripts. Where that data lives, which cases are the reference and
# the studies' pseudonyms are kept out of the public tree, in a local file the suite and the gate read
# when it is there (21 October 2026). IDIOGRAPH_GATE_LOCAL names it elsewhere. With no such file, as
# on GitHub's machines, every check that needs real data skips. Its keys are in docs/internals.md,
# "The local gate file".
GATE_LOCAL_ENV = "IDIOGRAPH_GATE_LOCAL"
GATE_LOCAL_DEFAULT = "~/.config/idiograph/gate.local.json"


def gate_local() -> dict:
    """The local gate file as a dict, or an empty one when it is absent or unreadable."""
    path = Path(os.environ.get(GATE_LOCAL_ENV, "").strip() or GATE_LOCAL_DEFAULT).expanduser()
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}
    return data if isinstance(data, dict) else {}


LOCAL = gate_local()

# A path that is never there, for a fixture this machine has no data for, so its check skips.
NOWHERE = HERE / "no-real-data-on-this-machine"

# REPO is the folder holding the real data, IDIOGRAPH_ACADEMY first, else the local file's "academy"
_academy = os.environ.get("IDIOGRAPH_ACADEMY", "").strip() or str(LOCAL.get("academy") or "").strip()
REPO = Path(_academy).expanduser() if _academy else NOWHERE


def in_repo(key: str) -> Path:
    """The local file's path under REPO for this key, or NOWHERE when it names none."""
    rel = str(LOCAL.get(key) or "").strip()
    return REPO / rel if rel and REPO is not NOWHERE else NOWHERE


# The folder names no app code may hold, so no run defaults to a study's folder: the two generic ones,
# and each study's own top folder from the local file
STUDY_FOLDERS = tuple(dict.fromkeys(["Main Data", "Participant Data"] + [
    Path(str(LOCAL.get(key))).parts[0] for key in ("main_data", "participants")
    if isinstance(LOCAL.get(key), str) and Path(str(LOCAL.get(key))).parts]))

MAIN_DATA_ENV = "IDIOGRAPH_MAIN_DATA"
DEFAULT_MAIN = in_repo("main_data")
CORPUS_MD = in_repo("corpus")
PARTICIPANTS = in_repo("participants")

# The demo case travels with the app, so it is the fixture for everything that needs no more than
# an EN & ES workbook. Since 26 October the demo ships as a finished project (Adam, 24 October), every
# turn annotated, every board with descriptions and the GETs done, and the checks that annotate a turn,
# trim, assign, count, describe a label or take a case into the GETs need work still to do. So the
# fixture is the demo as it shipped until then, built once per run from the demo's own sources, its
# transcripts and annotations, by the app's create_from_source, the turn screen's saves and
# `make_demo.build_written`: Juno's head start, statements on her first six turns, the first turn's
# note, the sixth turn's key quote and the two highlights they hold, the rest untouched and no board
# (see `head_start`), and Rowan's and Mabel's finished cases with their boards less the descriptions,
# laid out in a pristine copy's shape, `DEMO_PRISTINE`, the workbooks at its root and their sidecars in
# its `Working/`. The shipped demo itself, `demo/pristine/`, is read where a check is about the demo
# as it ships (areas 29, 73 and 74).
DEMO_SHIPPED = source("demo/pristine")
HEAD_START = 6


def head_start(into: Path) -> Path:
    """Juno's head-start workbook built into `into`, a folder of its own, with its progress file beside
    it in `Working/` as the app writes one: her first six turns as her annotations give them, the note
    on the first alone, the key quote on the sixth alone and the highlights of those two, and the
    progress file's rows and last place for them. The interviewer is named as the transcript names him."""
    import tempfile
    import make_demo
    rows = make_demo.read_turns()
    notes = make_demo.read_annotations(make_demo.written_sources(make_demo.PARTICIPANT)[1])
    into.mkdir(parents=True, exist_ok=True)
    book = into / make_demo.WORKBOOK.name
    with tempfile.TemporaryDirectory(prefix="demo-fixture-") as tmp:
        wb_mod.create_from_source(make_demo.written_source(rows, Path(tmp) / "Juno - interview.xlsx"), book)
    case = wb_mod.read_case(book)
    hers = [r for s in case["sheets"] for r in s["rows"] if r["name"] == make_demo.PARTICIPANT]
    progress = rounds_mod.load_progress(book)
    for i, (row, item) in enumerate(zip(hers[:HEAD_START], notes["turns"][:HEAD_START])):
        quote = item["kq"][0] if i == HEAD_START - 1 and item.get("kq") else ""
        wb_mod.save_turn(book, make_demo.SHEET, row["row"], "\n".join(item["es"]), item.get("en", "") if i == 0 else "",
                         f'"{quote}"' if quote else "")
        progress["rows"][rounds_mod.row_key(make_demo.SHEET, row["row"])] = rounds_mod.HAS_CONTENT
        phrase = item.get("crux") if i in (0, HEAD_START - 1) else None
        if phrase:
            at = row["text"].find(phrase)
            wb_mod.save_crux(book, make_demo.SHEET, row["row"], at, at + len(phrase), phrase, op="add")
    progress["last"] = {"sheet": make_demo.SHEET, "row": hers[HEAD_START - 1]["row"]}
    rounds_mod.save_progress(book, progress)
    return book


def undescribed(into: Path) -> Path:
    """A copy of the demo's sources in `into/source/`, every PET's and sub-PET's description taken out of
    the annotations, as the demo's boards were before 26 October. Answers `into`, a demo folder
    `make_demo.build_written` builds from."""
    import make_demo
    folder = into / "source"
    folder.mkdir(parents=True, exist_ok=True)
    for name in make_demo.CASES:
        csv_path, notes_path = make_demo.written_sources(name)
        shutil.copyfile(csv_path, folder / csv_path.name)
        notes = json.loads(notes_path.read_text(encoding="utf-8"))
        for pet in notes["board"]["pets"]:
            for label in [pet] + list(pet.get("subs") or []):
                label.pop("description", None)
        (folder / notes_path.name).write_text(json.dumps(notes, ensure_ascii=False, indent=1), encoding="utf-8")
    return into


def _fixture() -> Path:
    """The demo as it shipped until 26 October in a pristine copy's shape, built in a folder of its own
    removed when the run ends (see the note above)."""
    import atexit
    import tempfile
    import make_demo
    import themes as themes_mod
    folder = Path(tempfile.mkdtemp(prefix="idiograph-demo-fixture-"))
    atexit.register(shutil.rmtree, folder, True)
    pristine = folder / "pristine"
    (pristine / "Working").mkdir(parents=True)
    juno = head_start(folder / "build" / make_demo.PARTICIPANT)
    shutil.copyfile(juno, pristine / juno.name)
    shutil.copyfile(rounds_mod.progress_path(juno), pristine / "Working" / rounds_mod.progress_path(juno).name)
    sources = undescribed(folder / "sources")
    for name in make_demo.WRITTEN:
        built = make_demo.build_written(name, folder / "build", sources)
        shutil.copyfile(built["workbook"], pristine / built["workbook"].name)
        for side in (rounds_mod.progress_path(built["workbook"]), themes_mod.themes_path(built["workbook"])):
            shutil.copyfile(side, pristine / "Working" / side.name)
    return pristine


DEMO_PRISTINE = _fixture()
DEMO_WORKBOOK = DEMO_PRISTINE / "Juno - EN & ES.xlsx"

DEMO_SHEET = "Initial"
# The two research questions the prompt checks are written with: an invented one in the GRAVITY
# shape, and the demo's own, as its committed project file states it.
GRAVITY_QUESTION = ("How do people experience altered gravity, weightlessness and hypergravity "
                    "during parabolic flight?")
DEMO_QUESTION = ("How do people experience sharing a home with a dog, and what does the dog come to "
                 "mean to them?")


def main_data() -> Path:
    """Where the GRAVITY cases sit. The environment variable points it somewhere else."""
    override = os.environ.get(MAIN_DATA_ENV, "").strip()
    return Path(override).expanduser() if override else DEFAULT_MAIN


MAIN = main_data()


def case_path(prefix: str, *parts: str) -> Path:
    """A fixture inside a case folder, found by its pseudonym prefix.

    Case folders carry a second name that must never reach the repo, so nothing here spells a
    folder out. An unmatched prefix returns a path that does not exist, and the test skips.
    """
    folders = sorted(MAIN.glob(prefix + "*"))
    base = folders[0] if folders else MAIN / prefix
    return base.joinpath(*parts)


def local_case(key: str) -> Path:
    """A reference fixture the local file names by key, as [folder prefix, part, ...], else NOWHERE."""
    spec = LOCAL.get(key)
    if not (isinstance(spec, list) and spec and all(isinstance(p, str) and p for p in spec)):
        return NOWHERE
    return case_path(spec[0], *spec[1:])


def local_parts(key: str) -> list[str]:
    """A list of path parts the local file names by key, or none."""
    spec = LOCAL.get(key)
    return [p for p in spec if isinstance(p, str) and p] if isinstance(spec, list) else []


# The reference workbook, a finished case the app's format and export were built against, and a
# real transcript the import is checked on. Both named only in the local file.
REFERENCE_WORKBOOK = local_case("reference_workbook")
REFERENCE_SOURCE = local_case("reference_source")


def set_main_data(folder: str) -> None:
    """Point the reference fixtures at another folder, for a run that proves nothing needs them."""
    global MAIN, REFERENCE_WORKBOOK, REFERENCE_SOURCE
    os.environ[MAIN_DATA_ENV] = folder
    MAIN = main_data()
    REFERENCE_WORKBOOK = local_case("reference_workbook")
    REFERENCE_SOURCE = local_case("reference_source")


PASSED, FAILED, SKIPPED = [], [], []


def check(name, condition, detail=""):
    if condition:
        PASSED.append(name)
        print(f"  ok    {name}{(' - ' + detail) if detail else ''}")
    else:
        FAILED.append(name)
        print(f"  FAIL  {name}{(' - ' + detail) if detail else ''}")


def skip(name, why):
    SKIPPED.append(name)
    print(f"  skip  {name} - {why}")


# The browsers the suite drives its checks of the page in, headless, looked for where their installers put them
# (since 9 November 2026, typst5, the app itself reaches no browser: every PDF and picture is Typst's, so the
# lookup that was print_pdf.browser lives here for the checks alone)
MAC_BROWSERS = ("Google Chrome.app/Contents/MacOS/Google Chrome", "Chromium.app/Contents/MacOS/Chromium",
                "Brave Browser.app/Contents/MacOS/Brave Browser", "Microsoft Edge.app/Contents/MacOS/Microsoft Edge")
PATH_BROWSERS = ("google-chrome", "google-chrome-stable", "chromium", "chromium-browser", "brave-browser", "microsoft-edge")
WINDOWS_BROWSERS = (r"Google\Chrome\Application\chrome.exe", r"Microsoft\Edge\Application\msedge.exe",
                    r"BraveSoftware\Brave-Browser\Application\brave.exe")


def browser() -> Path | None:
    """A Chromium the suite can drive headless, `IDIOGRAPH_PDF_BROWSER` naming one, or None when the computer has
    none."""
    named = os.environ.get("IDIOGRAPH_PDF_BROWSER", "").strip()
    if named:
        return Path(named) if Path(named).is_file() else None
    if sys.platform == "darwin":
        for folder in (Path("/Applications"), Path.home() / "Applications"):
            for app in MAC_BROWSERS:
                if (folder / app).is_file():
                    return folder / app
    for name in PATH_BROWSERS:
        found = shutil.which(name)
        if found:
            return Path(found)
    if os.name == "nt":
        for base in (os.environ.get("PROGRAMFILES"), os.environ.get("PROGRAMFILES(X86)"), os.environ.get("LOCALAPPDATA")):
            for exe in WINDOWS_BROWSERS:
                if base and (Path(base) / exe).is_file():
                    return Path(base) / exe
    return None


def typeset_words(kept: list):
    """A stand-in for `print_pdf.typeset_pdf` that typesets for real and keeps each PDF's words in `kept`, squashed of
    their spaces and folded, so a check can find what the page printed (typst5, 9 November 2026, where the checks
    before kept the HTML page a browser was handed)."""
    import pdftext
    import print_pdf
    real = print_pdf.typeset_pdf

    def made(template, data):
        out = real(template, data)
        kept.append(squashed(" ".join(pdftext.pages_text(out))))
        return out
    return real, made


def squashed(text: str) -> str:
    """Words as a PDF's text and a page's are compared by: no spaces, folded."""
    return re.sub(r"\s+", "", str(text)).casefold()


def faulty_env(env: dict | None = None) -> dict:
    """`env`, or this process's environment, with Python's faulthandler asked for, so a child server sent
    SIGABRT writes every thread's Python traceback into its output before it ends (cidiag, 7 November 2026,
    the GitHub Mac's five real-server checks)."""
    return dict(os.environ if env is None else env, PYTHONFAULTHANDLER="1")


class ChildWatch:
    """What a failed check of a real child server says, made as the child starts. `answered()` times its first
    answer. When a wait on the child runs out, `ran_out()` notes the child's state and the port's sockets, sends
    it SIGABRT so faulthandler writes every thread's traceback into its output, and gives it a few seconds to
    end. The signal goes on GitHub's runners alone, never on Windows, since on a Mac at a desk each abort puts
    up the system's report that Python quit unexpectedly (7 November). `says(output)` is the check's detail on a failure: the seconds to the first answer
    or that there was none, the child's exit code or that it is still running, and the last 3000 characters of
    its output, faulthandler's dump whole after them. It decides nothing, and a check's pass condition never
    reads it."""

    TAIL, DUMP = 3000, 8000

    def __init__(self, kid, port: int | None = None):
        self.kid, self.port = kid, port
        self.began = time.monotonic()
        self.first = self.out_at = None
        self.state = self.why = self.sockets = ""
        self.sent = False

    def answered(self) -> None:
        """The child answered a request: the first time is noted."""
        if self.first is None:
            self.first = time.monotonic() - self.began

    def ran_out(self, why: str = "") -> None:
        """A wait on the child has run out, or a connect to it has failed. Only the first is noted, and the
        signal is sent once, to a child that still runs."""
        if self.out_at is None:
            self.out_at, self.why = time.monotonic() - self.began, why
            code = self.kid.poll()
            self.state = "still running" if code is None else f"exit code {code}"
            self.sockets = self.socket_lines()
        if (self.sent or sys.platform == "win32" or not os.environ.get("GITHUB_ACTIONS")
                or self.kid.poll() is not None):
            return
        self.sent = True
        try:
            self.kid.send_signal(signal.SIGABRT)
            self.kid.wait(5)
        except (OSError, subprocess.TimeoutExpired):
            pass

    def socket_lines(self) -> str:
        """The Mac's sockets on the child's port as the wait runs out, its listen queue among them, where
        a connect that times out would show a full queue. Empty elsewhere and where netstat does not run."""
        if sys.platform != "darwin" or not self.port:
            return ""
        mine = re.compile(rf"\.{self.port}(\s|$)")
        found, asked, waiting = [], False, 0
        for command in (["netstat", "-an", "-p", "tcp"], ["netstat", "-Lan"]):
            try:
                ran = subprocess.run(command, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=10)
            except (OSError, subprocess.SubprocessError):
                continue
            asked = True
            for line in (" ".join(line.split()) for line in ran.stdout.splitlines() if mine.search(line)):
                if line.endswith("TIME_WAIT"):
                    waiting += 1
                else:
                    found.append(line)
        found += [f"{waiting} in TIME_WAIT"] if waiting else []
        return " | ".join(found[:12]) or ("none listed" if asked else "")

    def says(self, output: str = "") -> str:
        """The detail of a failed check: when the child first answered, how it stands, what it printed."""
        now = time.monotonic() - self.began
        if self.first is not None:
            said = f"first answer {self.first:.1f} s after the start"
        else:
            said = f"no answer in {(now if self.out_at is None else self.out_at):.1f} s"
        code = self.kid.poll()
        if self.out_at is None:
            how = "still running" if code is None else f"exit code {code}"
        else:
            how = f"{self.state} at {self.out_at:.1f} s, when {self.why or 'a wait ran out'}"
            if self.sent:
                how += f", sent SIGABRT, then {'still running' if code is None else f'exit code {code}'}"
        # the last TAIL characters of the output, and where faulthandler wrote its dump, the dump whole from its
        # first line (a Python with a C stack to print puts the threads' own tracebacks first and a long run of
        # frames after), so a tail of threads never cuts the one that was running
        text = (output or "").replace("\r\n", "\n").strip()
        cut = text.rfind("Fatal Python error")
        shown = text[-self.TAIL:] if cut < 0 else text[:cut].strip()[-self.TAIL:] + "\n" + text[cut:][:self.DUMP]
        sockets = f"\nsockets on the port then: {self.sockets}" if self.sockets else ""
        return f"{said}, child {how}{sockets}\nchild output, last {self.TAIL} characters:\n{shown or '(nothing)'}"


def slashed(path) -> str:
    """A path as text with slashes, so a check of the folders in a line reads the same on Windows,
    whose lines keep its backslashes, as on a Mac (14 October)."""
    return str(path).replace("\\", "/")


def mode_is(path, mode: int) -> bool:
    """A file's permission bits are `mode`, on a system that keeps them. Windows keeps a read-only
    flag alone, so there the bits are not asked (14 October)."""
    import stat
    return os.name == "nt" or stat.S_IMODE(Path(path).stat().st_mode) == mode


def cell_signature(cell):
    """Everything about a cell that must survive a save: value, every run and its colour, format."""
    value = cell.value
    if isinstance(value, CellRichText):
        runs = tuple(
            ("run", b.text, getattr(b.font.color, "theme", None), getattr(b.font.color, "tint", None),
             b.font.rFont, b.font.sz, b.font.b, b.font.i)
            if isinstance(b, TextBlock) else ("text", str(b))
            for b in value
        )
        body = ("rich", runs)
    else:
        body = ("plain", value)
    return (body, cell.number_format, cell.font.name, cell.font.sz, cell.font.b,
            cell.alignment.wrap_text, cell.alignment.vertical)


def compare_workbooks(a_path, b_path, allowed: set[tuple[str, int, int]]):
    """Every cell of every sheet, plus widths, freeze panes and zoom. Returns a list of complaints."""
    a = openpyxl.load_workbook(a_path, rich_text=True)
    b = openpyxl.load_workbook(b_path, rich_text=True)
    problems = []
    if a.sheetnames != b.sheetnames:
        problems.append(f"sheet names {a.sheetnames} vs {b.sheetnames}")
    checked = 0
    for name in a.sheetnames:
        sa, sb = a[name], b[name]
        if (sa.max_row, sa.max_column) != (sb.max_row, sb.max_column):
            problems.append(f"{name}: shape {(sa.max_row, sa.max_column)} vs {(sb.max_row, sb.max_column)}")
        wa = {k: v.width for k, v in sa.column_dimensions.items()}
        wb_ = {k: v.width for k, v in sb.column_dimensions.items()}
        if wa != wb_:
            problems.append(f"{name}: column widths {wa} vs {wb_}")
        if sa.freeze_panes != sb.freeze_panes:
            problems.append(f"{name}: freeze panes {sa.freeze_panes} vs {sb.freeze_panes}")
        if sa.sheet_view.zoomScale != sb.sheet_view.zoomScale:
            problems.append(f"{name}: zoom {sa.sheet_view.zoomScale} vs {sb.sheet_view.zoomScale}")
        for r in range(1, sa.max_row + 1):
            for c in range(1, sa.max_column + 1):
                checked += 1
                if (name, r, c) in allowed:
                    continue
                if cell_signature(sa.cell(r, c)) != cell_signature(sb.cell(r, c)):
                    problems.append(f"{name} r{r}c{c}: {cell_signature(sa.cell(r, c))!r} vs {cell_signature(sb.cell(r, c))!r}")
    a.close(); b.close()
    return problems, checked


def count_rich(path):
    wb = openpyxl.load_workbook(path, rich_text=True)
    n = sum(1 for ws in wb.worksheets for r in range(2, ws.max_row + 1)
            if isinstance(ws.cell(r, 4).value, CellRichText))
    wb.close()
    return n


# ─────────────────────────────────────────────────────── the demo fixture ──

def demo_copy(scratch, *parts) -> Path:
    """A scratch copy of the demo workbook. The demo itself is never opened for writing."""
    out = scratch.joinpath(*parts)
    out.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(DEMO_WORKBOOK, out)
    return out


def demo_sheet(path):
    """The demo sheet, the name her turns carry and the name his do.

    The demo is built with the interviewer from `config.json`, so neither name is spelled out
    here. Her turns are the ones carrying the head start.
    """
    case = wb_mod.read_case(path)
    sheet = next(s for s in case["sheets"] if s["name"] == DEMO_SHEET)
    her = next(r["name"] for r in sheet["rows"] if r["es"].strip())
    him = next(r["name"] for r in sheet["rows"] if r["name"] != her)
    return sheet, her, him


def add_second_sheet(path: Path, name: str = "2d", rows: int = 10) -> Path:
    """A second sheet on a scratch copy, in the six columns the app writes.

    The demo ships with one sheet, and the trim and the wipe both have something to say about what
    happens to the sheets they were not pointed at.
    """
    book = openpyxl.load_workbook(path, rich_text=True)
    ws = book.create_sheet(name)
    for col, head in zip("ABCDEF", wb_mod.HEADER):
        ws[f"{col}1"] = head
    _, her, him = demo_sheet(path)
    for r in range(2, rows + 2):
        ws.cell(r, 1, him if r % 2 else her)
        ws.cell(r, 2, f"00:{r:02d}:00")
        ws.cell(r, 3, f"A statement on row {r}")
        ws.cell(r, 4, f"A turn on the second sheet, row {r}, with words enough to read as one.")
        ws.cell(r, 5, f"A note on row {r}")
        ws.cell(r, 6, f'"a quote on row {r}"')
    book.save(path)
    book.close()
    return path


def sheet_signature(path, sheet):
    """Every cell of one sheet, plus the widths, freeze pane, zoom and any fill."""
    wb = openpyxl.load_workbook(path, rich_text=True)
    ws = wb[sheet]
    cells = [[cell_signature(ws.cell(r, c)) for c in range(1, ws.max_column + 1)]
             for r in range(1, ws.max_row + 1)]
    fills = [(r, c) for r in range(1, ws.max_row + 1) for c in range(1, ws.max_column + 1)
             if ws.cell(r, c).fill and ws.cell(r, c).fill.fill_type]
    shape = ({k: v.width for k, v in ws.column_dimensions.items()}, ws.freeze_panes,
             ws.sheet_view.zoomScale)
    heights = {k: v.height for k, v in ws.row_dimensions.items() if v.height is not None}
    wb.close()
    return cells, fills, shape, heights


def orange_runs(path, sheet):
    wb = openpyxl.load_workbook(path, rich_text=True)
    ws = wb[sheet]
    out = []
    for r in range(2, ws.max_row + 1):
        value = ws.cell(r, 4).value
        if isinstance(value, CellRichText):
            for b in value:
                if isinstance(b, TextBlock) and getattr(b.font.color, "theme", None) == 9:
                    out.append(b.text)
    wb.close()
    return out


def css_block(css: str, selector: str) -> str:
    """The declarations of the first rule written with this selector, or an empty string."""
    at = css.find(selector + " ")
    if at < 0:
        at = css.find(selector + "{")
    if at < 0:
        return ""
    return css[at:css.find("}", at)]


def cell_face(path, sheet, row, col=4):
    """Everything about a cell except what is in it: the style an edit must leave alone."""
    wb = openpyxl.load_workbook(path, rich_text=True)
    cell = wb[sheet].cell(row, col)
    face = (cell.font.name, cell.font.sz, cell.font.b, cell.font.i,
            cell.alignment.wrap_text, cell.alignment.vertical, cell.number_format,
            cell.fill.fill_type if cell.fill else None)
    wb.close()
    return face


def row_cells(path, sheet, row):
    """Name, timecode value and transcript text of one row, as the workbook holds them."""
    wb = openpyxl.load_workbook(path, rich_text=True)
    ws = wb[sheet]
    out = (ws.cell(row, 1).value, ws.cell(row, 2).value, wb_mod.plain_text(ws.cell(row, 4).value),
           [wb_mod.split_entries(ws.cell(row, c).value) for c in (3, 5, 6)])
    wb.close()
    return out


def max_row(path, sheet):
    wb = openpyxl.load_workbook(path)
    n = wb[sheet].max_row
    wb.close()
    return n


def json_strings(value, skip_keys=("path", "suggested")):
    """Every string in a JSON answer, with the fields named in skip_keys left out."""
    if isinstance(value, dict):
        for k, v in value.items():
            if k not in skip_keys:
                yield from json_strings(v, skip_keys)
    elif isinstance(value, list):
        for v in value:
            yield from json_strings(v, skip_keys)
    elif isinstance(value, str):
        yield value


def plain(value):
    """An answer with the marking of the project's words taken off (`cli.mark`, 26 October 2026), so a check
    that reads its words reads them as they were. A file's JSON passes through as it is. Area 274 checks the
    marking itself."""
    import cli
    return cli.unmark(value)


def unfenced(text):
    """An MCP answer's text without the <untrusted_text> block round it (`cli.fenced`), as it was before."""
    head, foot = "<untrusted_text>\n", "\n</untrusted_text>"
    text = str(text)
    if text.startswith(head) and text.endswith(foot):
        return text[len(head):-len(foot)]
    return text


def plain_result(result):
    """An MCP tool's result with the marking off its structured answer and the block off its text (`plain`,
    `unfenced`), as it was before Sift's and Trace's answers were marked too (2 November 2026). Area 318
    checks the marking itself."""
    if not isinstance(result, dict):
        return result
    out = dict(result)
    if "structuredContent" in out:
        out["structuredContent"] = plain(out["structuredContent"])
    if isinstance(out.get("content"), list):
        out["content"] = [dict(c, text=unfenced(c["text"])) if isinstance(c, dict) and "text" in c else c
                          for c in out["content"]]
    return out


# The pseudonyms of the maintainer's studies, from the local file. No shipped file, README or doc may
# name any of them. With no local file the list is empty: area 38's audit of the shipped files then skips, and the
# other checks that look for these names find none.
STUDY_PSEUDONYMS = tuple(n for n in (LOCAL.get("study_pseudonyms") or []) if isinstance(n, str) and n)

ISO_OFFSET = re.compile(r"^\d{4}-\d\d-\d\dT\d\d:\d\d:\d\d[+-]\d\d:\d\d$")

# The four points of the sparkles every AI control carries, the first stroke of its path.
SPARKLES = "M12 3.2c.95 4.2 2.65 5.9 6.85 6.85"


def copied_second_sheet(path: Path, name: str = "2d", blank: bool = True) -> Path:
    """The demo's own sheet copied with openpyxl as a second sheet, so both sheets cut into the same
    rounds. With `blank` every statement on both sheets is cleared, so nothing is decided until a
    check says."""
    book = openpyxl.load_workbook(path, rich_text=True)
    ws = book.copy_worksheet(book[DEMO_SHEET])
    ws.title = name
    if blank:
        for sheet in book.worksheets:
            for r in range(2, sheet.max_row + 1):
                sheet.cell(r, 3).value = None
    book.save(path)
    book.close()
    return path


MAKE_WAY_CHECK = r"""
const keep = (x) => JSON.parse(JSON.stringify(x));
const card = (x, y) => ({ x, y, text: 'A', time: '00:01' });
const size = (item) => (item.startsWith('g') ? { w: 120, h: 30 } : item.startsWith('n') ? { w: 80, h: 47 } : { w: 200, h: 80 });
const M = TH_MARGIN;
const board = (cards, notes = []) => ({ cards: Object.fromEntries(Object.entries(cards).map(([k, [x, y]]) => [k, card(x, y)])),
  groups: [], discarded: [], picks: {}, stickies: notes });
// a drag as the page starts one (thDragStart): what moves, where each stood, the board's spots, the labels as they
// stand, which hold still while it lasts, and the bodies a drop goes into, at the level it keeps (thBodiesFor)
const start = (v, cards, groups = [], notes = [], sz = size) => {
  TH.v = v;
  thLayout(v, sz, null);
  const moving = thMoving(v, new Set(cards), new Set(groups), new Set(notes));
  const starts = {};
  for (const it of moving) { const o = thIsGroup(v, it) ? thGroup(v, it) : (v.cards[it] || thSticky(v, it)); starts[it] = { x: o.x, y: o.y }; }
  const parents = thParents(v);
  const nest = [...moving].some((it) => thIsGroup(v, it) && !moving.has(parents[it]));
  const d = { moving, starts, nest, dx: 0, dy: 0, alt: false, before: thSnap(v, []), was: thLabelBoxes(thLayout(v, sz, null)), from: thSpots(v) };
  d.hit = thLayout(v, sz, null);
  d.frames = thBodiesFor(v, moving, d.hit);
  return d;
};
// what thTargetAt finds at a world point: nothing with Alt held (31 October), a theme's title strip by the labels of
// what stays, which hold still, or the body of the PET or sub-PET the drop goes into at its level, by the frames as
// the drag began
const hitAt = (v, d, pt) => {
  if (d.alt) return null;
  for (const g of v.groups) {
    const l = !d.moving.has(g.id) && d.hit[g.id] && d.hit[g.id].label;
    if (l && pt.x >= l.x && pt.x <= l.x + l.w && pt.y >= l.y && pt.y <= l.y + l.h) return { group: g.id, onLabel: true };
  }
  const body = d.frames ? thInnermost(d.frames, pt, d.moving) : null;
  return body ? { group: body, frame: true, body: true } : null;
};
// the pointer moved by dx, dy, over the world point pt, as thWay takes it
const move = (v, d, dx, dy, pt, sz = size) => {
  d.dx = dx; d.dy = dy;
  const hit = hitAt(v, d, pt);
  d.hitNow = hit;
  d.out = !!(hit && hit.body) && thMergeInto(v, d.moving, hit.group);
  const home = thWayHome(v, d.moving, d.nest, hit, d.alt);
  const moved = thPreview(v, sz, d, home);
  return { hit, home, moved: [...moved].sort() };
};
const at = (v, id) => { const o = thIsGroup(v, id) ? thGroup(v, id) : (v.cards[id] || thSticky(v, id)); return [o.x, o.y]; };
const home = (v, was, id) => at(v, id)[0] === was.cards[id].x && at(v, id)[1] === was.cards[id].y;
const boxOf = (v, id, sz = size) => { const o = v.cards[id] || thSticky(v, id); return { x: o.x, y: o.y, w: sz(id).w, h: sz(id).h }; };
// every label not dragged where it stood as the drag began, in the layout the drag draws
const pinned = (v, d) => {
  const lay = thDragLayout(v, size, d.moving, !!(d.alt || d.out), d.from.groups);
  return v.groups.filter((g) => !d.moving.has(g.id)).every((g) => lay[g.id].label.x === d.from.groups[g.id].x && lay[g.id].label.y === d.from.groups[g.id].y);
};
const out = {};

// a card in no PET into the middle of a PET of nine, a card under the PET and a PET elsewhere on the canvas
{
  const cells = {};
  for (let r = 0; r < 3; r += 1) for (let c = 0; c < 3; c += 1) cells[`p:${r}${c}:0`] = [c * 210, r * 90];
  const v = board(Object.assign({}, cells, { 'f:1:0': [1500, 0], 'k:1:0': [210, 300], 'q:1:0': [1500, 600] }));
  const P = thMakeGroup(v, Object.keys(cells), 'Nine');
  const Q = thMakeGroup(v, ['q:1:0'], 'Far');
  const d = start(v, ['f:1:0']);
  const was = keep(thSpots(v));
  const kids = Object.keys(cells);
  const one = move(v, d, 210 - 1500, 90, { x: 310, y: 130 });
  const first = keep(thSpots(v));
  out.middle = { hit: one.hit, home: one.home === P, cards: one.moved.length > 0 && one.moved.every((k) => kids.includes(k)),
    label: pinned(v, d), landed: at(v, 'f:1:0'),
    near: kids.filter((k) => thMeets(boxOf(v, k), boxOf(v, 'f:1:0'), M)).length,
    far: home(v, was, 'q:1:0') && at(v, Q)[1] === was.groups[Q].y && home(v, was, 'k:1:0') };
  // on to the open canvas far off: every one of the nine back on its own spot, and nothing on the canvas moves
  const off = move(v, d, 0, 900, { x: 1600, y: 940 });
  out.back = { home: off.home, all: kids.every((k) => home(v, was, k)), moved: off.moved };
  // back into the middle the same as the first time, and the same twice over, never from the last preview
  move(v, d, 210 - 1500, 90, { x: 310, y: 130 });
  out.back.same = JSON.stringify(keep(thSpots(v))) === JSON.stringify(first);
  move(v, d, 210 - 1500 + 30, 90, { x: 340, y: 130 });
  const nudged = keep(thSpots(v));
  move(v, d, 210 - 1500 + 30, 90, { x: 340, y: 130 });
  out.back.again = JSON.stringify(keep(thSpots(v))) === JSON.stringify(nudged);
  // the drop: it goes into the PET where let go, the nine stay where they made room, and nothing overlaps
  const last = move(v, d, 210 - 1500, 90, { x: 310, y: 130 });
  const made = keep(thSpots(v));
  const { joined } = thDrop(v, d.moving, last.hit && !last.hit.frame ? last.hit.group : null, last.hit && last.hit.frame ? last.hit.group : null);
  thSettle(v, size, d.moving, d.was, [], TH_PASSES, true);
  out.drop = { joined, landed: at(v, 'f:1:0'), stayed: kids.every((k) => home(v, made, k)), clashes: thClashes(v, size).length,
    member: thParents(v)['f:1:0'] === P };
  // one step of undo: the board as the drag began puts back what was dragged and all that made room
  thPut(v, d.before);
  out.undo = { cards: JSON.stringify(keep(thSpots(v)).cards) === JSON.stringify(was.cards), loose: thParents(v)['f:1:0'] === undefined };
}

// between two cards of a PET's row, and under one: the row makes room for each, the PET's title still
{
  const v = board({ 'r:1:0': [0, 0], 'r:2:0': [210, 0], 'r:3:0': [420, 0], 'f:1:0': [2000, 0] });
  const R = thMakeGroup(v, ['r:1:0', 'r:2:0', 'r:3:0'], 'Row');
  const d = start(v, ['f:1:0']);
  const between = move(v, d, 105 - 2000, 0, { x: 205, y: 40 });
  const near = () => ['r:1:0', 'r:2:0', 'r:3:0'].filter((k) => thMeets(boxOf(v, k), boxOf(v, 'f:1:0'), M)).length;
  out.row = { between: [between.home === R, near(), at(v, 'f:1:0'), between.moved.includes(R), pinned(v, d)] };
  const under = move(v, d, 210 - 2000, 50, { x: 310, y: 88 });
  out.row.under = [under.home === R, near(), at(v, 'f:1:0'), under.moved.includes(R), pinned(v, d)];
}

// eight passes at most: a PET of ten tall cards in a row, a card dragged onto the first
{
  const tall = () => ({ w: 200, h: 300 });
  const row = {};
  for (let i = 0; i < 10; i += 1) row[`c:${i}:0`] = [i * 210, 0];
  const mk = () => { const v = board(Object.assign({}, row, { 'd:1:0': [5000, 0] })); return [v, thMakeGroup(v, Object.keys(row), 'Ten')]; };
  const [v] = mk();
  const d = start(v, ['d:1:0'], [], [], tall);
  move(v, d, -5100, 0, { x: 0, y: 150 }, tall);
  out.passes = { eight: Object.keys(row).map((k) => at(v, k)[0]) };
  const [w, T] = mk();
  const e = start(w, ['d:1:0'], [], [], tall);
  e.dx = -5100;
  thPreview(w, tall, e, null);
  thMakeWay(w, tall, e.moving, T, false, 9, e.from.groups);
  out.passes.nine = Object.keys(row).map((k) => at(w, k)[0]);
}

// Esc: everything back on its start, what was dragged too
{
  const v = board({ 'a:1:0': [0, 0], 'a:2:0': [210, 0], 'b:1:0': [900, 0] });
  thMakeGroup(v, ['a:1:0', 'a:2:0'], 'Pair');
  const d = start(v, ['b:1:0']);
  const was = keep(thSpots(v));
  move(v, d, -800, 20, { x: 200, y: 60 });
  const shifted = JSON.stringify(keep(thSpots(v)).cards) !== JSON.stringify(was.cards);
  thPreview(v, size, Object.assign({}, d, { dx: 0, dy: 0 }), null);
  out.esc = { shifted, back: JSON.stringify(keep(thSpots(v))) === JSON.stringify(was) };
}

// a selection of two dragged as one into a PET's row of three: each member's box makes room
{
  const v = board({ 'k:1:0': [0, 0], 'k:2:0': [210, 0], 'k:3:0': [420, 0], 's:1:0': [2000, 0], 's:2:0': [2210, 0] });
  const K = thMakeGroup(v, ['k:1:0', 'k:2:0', 'k:3:0'], 'Three');
  const d = start(v, ['s:1:0', 's:2:0']);
  const r = move(v, d, -1900, 20, { x: 200, y: 60 });
  out.selection = { home: r.home === K, landed: [at(v, 's:1:0'), at(v, 's:2:0')], moved: r.moved,
    near: ['k:1:0', 'k:2:0', 'k:3:0'].filter((k) => ['s:1:0', 's:2:0'].some((s) => thMeets(boxOf(v, k), boxOf(v, s), M))).length };
}

// a PET across the canvas over a card in no PET and another PET: nothing moves while it is dragged, and the drop
// sends them clear, that PET as one block
{
  const v = board({ 'a:1:0': [3000, 0], 'a:2:0': [3000, 90], 'k:1:0': [0, 0], 'b:1:0': [0, 300], 'b:2:0': [210, 300] });
  const A = thMakeGroup(v, ['a:1:0', 'a:2:0'], 'Walks');
  const B = thMakeGroup(v, ['b:1:0', 'b:2:0'], 'Mornings');
  const d = start(v, [], [A]);
  const was = keep(thSpots(v));
  const r = move(v, d, -2900, 160, { x: 160, y: 140 });
  const still = home(v, was, 'k:1:0') && home(v, was, 'b:1:0') && home(v, was, 'b:2:0') && at(v, B)[1] === was.groups[B].y;
  thDrop(v, d.moving, null, null);
  thSettle(v, size, d.moving, d.was, [], TH_PASSES, true);
  const lay = thLayout(v, size, null);
  const shift = (id, kind) => [at(v, id)[0] - was[kind][id].x, at(v, id)[1] - was[kind][id].y];
  const block = [shift('b:1:0', 'cards'), shift('b:2:0', 'cards'), shift(B, 'groups')];
  out.pet = { hit: r.hit, home: r.home, moved: r.moved, still, landed: [at(v, 'a:1:0'), at(v, 'a:2:0')],
    clear: !thMeets(lay[A].frame, boxOf(v, 'k:1:0'), M) && !thMeets(lay[A].frame, lay[B].frame, M),
    block: block.every((b) => b[0] === block[0][0] && b[1] === block[0][1]) && (block[0][0] !== 0 || block[0][1] !== 0),
    clashes: thClashes(v, size).length };
}

// a sub-theme inside its PET: the PET's own cards make room, a sibling sub-theme and the canvas stay still, and no Merge
{
  const v = board({ 'p:1:0': [0, 0], 'p:2:0': [210, 0], 'p:3:0': [420, 0], 's:1:0': [0, 200], 's:2:0': [210, 200],
    'o:1:0': [700, 0], 'k:1:0': [1200, 0] });
  const S = thMakeGroup(v, ['s:1:0', 's:2:0'], 'Inner');
  const O = thMakeGroup(v, ['o:1:0'], 'Beside');
  const P = thMakeGroup(v, ['p:1:0', 'p:2:0', 'p:3:0', S, O], 'Outer');
  const d = start(v, [], [S]);
  const was = keep(thSpots(v));
  const r = move(v, d, 100, -150, { x: 320, y: 40 });
  const lay = thLayout(v, size, null);
  out.sub = { nest: d.nest, hit: r.hit, home: r.home === P, merge: thMergeInto(v, d.moving, P),
    near: ['p:1:0', 'p:2:0', 'p:3:0'].filter((k) => thMeets(lay[S].frame, boxOf(v, k), M)).length,
    landed: [at(v, 's:1:0'), at(v, 's:2:0')], canvas: home(v, was, 'k:1:0'), sibling: home(v, was, 'o:1:0') && at(v, O)[0] === was.groups[O].x,
    moved: r.moved.every((k) => k.startsWith('p:')) && r.moved.length > 0 };
}

// a PET beside another and inside its body: that PET holds still, since a PET goes into no body, and over its title
// strip it merges, the title still under the pointer and nothing moving, and the drop nests, nothing overlapping
{
  const v = board({ 'a:1:0': [3000, 0], 't:1:0': [0, 0], 't:2:0': [210, 0], 't:3:0': [0, 90], 't:4:0': [210, 90] });
  const A = thMakeGroup(v, ['a:1:0'], 'Nights alone');
  const T = thMakeGroup(v, ['t:1:0', 't:2:0', 't:3:0', 't:4:0'], 'Mornings');
  const d = start(v, [], [A]);
  const was = keep(thSpots(v));
  const tf = d.hit[T].frame;
  const tl = d.hit[T].label;
  const tCards = ['t:1:0', 't:2:0', 't:3:0', 't:4:0'];
  const beside = move(v, d, -3000 + tf.x + tf.w + 20 - 100, 0, { x: tf.x + tf.w + 20, y: 40 });
  const held = () => tCards.every((k) => home(v, was, k)) && at(v, T)[0] === was.groups[T].x && at(v, T)[1] === was.groups[T].y;
  const besideHeld = held() && beside.moved.length === 0;
  const inside = move(v, d, -3000 + 200 - 100, 40, { x: 200, y: 80 });
  const body = { hit: inside.hit, home: inside.home, held: held() && inside.moved.length === 0 };
  const strip = move(v, d, -3000 + tl.x + 10, tl.y + tl.h + 30, { x: tl.x + 10, y: tl.y + tl.h / 2 });
  const lay = thDragLayout(v, size, d.moving, false, d.from.groups);
  out.merge = { beside: beside.home, besideHeld, body, strip: strip.hit, home: strip.home === T,
    title: lay[T].label.x === tl.x && lay[T].label.y === tl.y, still: held() && strip.moved.length === 0, into: thMergeInto(v, d.moving, T) };
  thDrop(v, d.moving, strip.hit.group, null);
  thSettle(v, size, d.moving, d.was, [], TH_PASSES, true);
  Object.assign(out.merge, { nested: thParents(v)[A] === T, clashes: thClashes(v, size).length });
}

// Alt: nothing takes the card, its own PET holds still while it is dragged, and the drop takes it out where it is let go
{
  const v = board({ 'p:1:0': [0, 0], 'p:2:0': [210, 0], 'p:3:0': [420, 0] });
  thMakeGroup(v, ['p:1:0', 'p:2:0', 'p:3:0'], 'Out');
  const d = start(v, ['p:2:0']);
  d.alt = true;
  const was = keep(thSpots(v));
  const r = move(v, d, 0, 40, { x: 310, y: 80 });
  out.alt = { hit: r.hit, home: r.home, moved: r.moved, still: home(v, was, 'p:1:0') && home(v, was, 'p:3:0') && pinned(v, d) };
  const { left } = thDrop(v, d.moving, null, r.hit && r.hit.group, true);
  thSettle(v, size, d.moving, d.was, [], TH_PASSES, true);
  Object.assign(out.alt, { left, landed: at(v, 'p:2:0'), clashes: thClashes(v, size).length, out: thParents(v)['p:2:0'] === undefined });
}

// a card dragged into another PET's body: it shows leaving its own, whose frame lets go of it, that PET's cards make
// room, the PET itself holds still, and the drop takes it in
{
  const v = board({ 'q:1:0': [0, 0], 'q:2:0': [210, 0], 'p:1:0': [0, 400], 'p:2:0': [210, 400], 'k:1:0': [700, 0] });
  const Q = thMakeGroup(v, ['q:1:0', 'q:2:0'], 'Into');
  const F = thMakeGroup(v, ['p:1:0', 'p:2:0'], 'From');
  const d = start(v, ['p:2:0']);
  const was = keep(thSpots(v));
  const r = move(v, d, -100, -390, { x: 200, y: 50 });
  const lay = thDragLayout(v, size, d.moving, !!d.out, d.from.groups);
  out.join = { home: r.home === Q, hit: r.hit, moved: r.moved, out: d.out, label: pinned(v, d),
    near: ['q:1:0', 'q:2:0'].filter((k) => thMeets(boxOf(v, k), boxOf(v, 'p:2:0'), M)).length,
    shrunk: lay[F].frame.y > 300, canvas: home(v, was, 'k:1:0') };
  const res = thDrop(v, d.moving, null, r.hit.group);
  thSettle(v, size, d.moving, d.was, [], TH_PASSES, true);
  Object.assign(out.join, { joined: res.joined, parent: thParents(v)['p:2:0'] === Q, clashes: thClashes(v, size).length });
}

// a sticky note dragged into a PET's body: its cards make room by the note's box, and the drop takes the note in
{
  const v = board({ 'k:1:0': [0, 0], 'k:2:0': [210, 0] }, [{ id: 'n1', text: 'not sure', colour: 'yellow', x: 900, y: 0 }]);
  const K = thMakeGroup(v, ['k:1:0', 'k:2:0'], 'Two');
  const d = start(v, [], [], ['n1']);
  const r = move(v, d, -720, 10, { x: 220, y: 30 });
  out.note = { home: r.home === K, moved: r.moved, landed: at(v, 'n1'),
    near: ['k:1:0', 'k:2:0'].filter((k) => thMeets(boxOf(v, k), boxOf(v, 'n1'), M)).length };
  thDrop(v, d.moving, null, r.hit && r.hit.group);
  out.note.inside = thSticky(v, 'n1').in === K;
}

// over the bin nothing makes way, and the slide's arithmetic: 160 ms eased out, at once with reduced motion
{
  const v = board({ 'a:1:0': [0, 0], 'b:1:0': [900, 0] });
  const d = start(v, ['b:1:0']);
  d.dx = -800;
  out.bin = [thWayHome(v, d.moving, false, { discard: true }, false), thPreview(v, size, d, null).size, at(v, 'a:1:0')];
  const s = { from: { x: 0, y: 0 }, to: { x: 100, y: 0 }, t0: 1000 };
  const mid = thWayAt(s, 1080);
  out.slide = [thWayAt(s, 1000).x, mid.x > 50 && mid.x < 100 && !mid.done, thWayAt(s, 1160).x, thWayAt(s, 1160).done,
    thWayAt(s, 1000, true).x, thWayAt(s, 1000, true).done];
  // a locked revision makes no way
  const w = board({ 'a:1:0': [0, 0], 'b:1:0': [900, 0] });
  const e = start(w, ['b:1:0']);
  w.readonly = true;
  e.dx = -900;
  out.locked = thMakeWay(w, size, e.moving, '', false).size;
}
console.log(JSON.stringify(out));
"""


def line_of_js(js: str, start: str) -> str:
    """The line of app.js that opens with `start`, for a piece of it run in node."""
    return next(line for line in js.splitlines() if line.startswith(start))


def quote_span_js() -> str:
    """distil.js's pieces for a quote across her passages (quotespan, 30 October 2026), which the quote's marks,
    the pieces being built and the candidate call since then: the passages next to one, where a quote stands
    among them, the pieces held in each and the refusals, for a node harness that runs the marks or `Q`. It goes
    after quote.js, whose `quoteReach`, `quotePieces` and `assembleAcross` they call, and needs the harness's own
    `S`, `current`, `livePairs`, `repaintRow`, `rowByKey` and `t` where it calls the parts that use them."""
    app = text("apps/idiograph/static/distil.js")
    lines = [line_of_js(app, start) for start in ("const KQ_NEAR = ", "const speakerKey = ", "const rowText = ",
                                                  "const pendingLayer = ")]
    fns = ["function " + name + "(" + app.split(f"\nfunction {name}(", 1)[1].split("\n}\n", 1)[0] + "\n}"
           for name in ("quoteRun", "quoteTurns", "kqFarKeys", "kqFarPaint", "kqFarTitle", "piecesIn", "pendingRows",
                        "paintPending", "takeBeside", "besideRefusal")]
    return "\n".join(lines + fns) + "\n"


def sift_words_js(js: str) -> str:
    """Sift's decisions' words and keys from sift.js, `SF_WORDS` to `sfKeyDecision`, for a piece of it run
    in node, the words of each stage since 12 October, up to the suggestion's titles since 14 October."""
    return "const SF_WORDS = " + js.split("const SF_WORDS = ", 1)[1].split("\nconst SF_SUGGESTION = ", 1)[0]


def table_js() -> str:
    """The family's table, family/static/table.js, for a node harness that runs a piece of sift.js, whose
    table sorts, filters, counts and draws its groups through it since the family codebase's third build.
    It goes ahead of the piece, as the page loads it first, and the text layer ahead of it, as the page loads that
    before every script (i18ncore, 28 October 2026)."""
    return i18n_js() + text("family/static/table.js")


def grip_js() -> str:
    """The handle app.js shares with Sift since 12 October, gripHtml, gripDrag and gripKeys, for a
    node harness that runs sift_search.js without app.js."""
    app = text(*APP_JS)
    return "\n".join(f"function {name}(" + app.split(f"function {name}(", 1)[1].split("\n}", 1)[0] + "\n}"
                     for name in ("gripHtml", "gripDrag", "gripKeys"))


def search_stub(state: dict):
    """A stand-in for the five databases' APIs, for area 104 and a smoke run, on an invented topic,
    allotment gardening and wellbeing. `state` counts each path's requests under `calls`, names the
    keys Scopus and Web of Science take under `keys`, and with `wos_fails` Web of Science refuses
    and says the key it was sent back in its answer, as a careless server might. Since 14 October (133)
    PubMed gives MeSH headings, Europe PMC a `keywordList` and OpenAlex `keywords` too, and each its
    language."""
    import http.server
    import urllib.parse as up

    def inverted(text):
        out = {}
        for i, w in enumerate(text.split()):
            out.setdefault(w, []).append(i)
        return out

    a_text = "Twelve plot holders described growing food together across one season."
    c_text = "Gardeners spoke of sharing water in a dry July."
    pubmed = {
        "9001": ("Plot holders' wellbeing across a season", "2018", "10.5555/allot.4", "Birch", "D",
                 "Invented Journal of Plots", ["To hear plot holders.", "Eight plot holders kept diaries."]),
        "9002": ("Growing together on the allotment", "2019", "10.5555/allot.1", "Fern", "A",
                 "Journal of Invented Gardens", [a_text]),
    }
    epmc = [
        {"id": "1", "source": "MED", "title": "Growing together on the allotment", "authorString": "Fern A, Reed B.",
         "pubYear": "2019", "doi": "10.5555/allot.1", "abstractText": f"<p>{a_text}</p>",
         "journalInfo": {"journal": {"title": "Journal of Invented Gardens"}}, "pubTypeList": {"pubType": ["Journal Article"]},
         "keywordList": {"keyword": ["allotments", "community gardens", "food growing"]}, "language": "eng"},
        {"id": "PPR2", "source": "PPR", "title": "Water butts and neighbours", "authorString": "Oak F.", "pubYear": "2020",
         "abstractText": c_text, "journalInfo": {"journal": {"title": "Invented Gardens"}}, "pubTypeList": {"pubType": ["Preprint"]}},
    ]
    openalex = [
        {"id": "https://openalex.org/W1", "doi": "https://doi.org/10.5555/allot.1", "title": "Growing together on the allotment",
         "publication_year": 2019, "type": "article", "authorships": [{"author": {"display_name": "Ann Fern"}}],
         "primary_location": {"source": {"display_name": "Journal of Invented Gardens"}}, "abstract_inverted_index": inverted(a_text)},
        {"id": "https://openalex.org/W3", "doi": "https://doi.org/10.5555/allot.3", "title": "Water Butts and Neighbours.",
         "publication_year": 2020, "type": "article", "authorships": [{"author": {"display_name": "Fay Oak"}}],
         "primary_location": {"source": {"display_name": "Invented Gardens"}}, "abstract_inverted_index": inverted(c_text),
         "keywords": [{"display_name": "Water conservation", "score": 0.5}], "language": "en"},
        {"id": "https://openalex.org/W6", "doi": "https://doi.org/10.5555/allot.6", "title": "Plot holders' wellbeing across a season",
         "publication_year": 2018, "type": "article", "authorships": [{"author": {"display_name": "Gil Elm"}}],
         "primary_location": {"source": None}, "abstract_inverted_index": inverted("A second study with the same title.")},
    ]
    fills = {"10.5555/allot.2": "Nine gardeners talked about their sheds as places to be alone."}
    scopus = [
        {"eid": "2-s2.0-1", "dc:title": "Growing together on the allotment", "author": [{"authname": "Fern A."}],
         "prism:coverDate": "2019-04-01", "prism:publicationName": "Journal of Invented Gardens", "prism:doi": "10.5555/allot.1",
         "dc:description": a_text, "subtypeDescription": "Article", "authkeywords": "allotments | food"},
        {"eid": "2-s2.0-2", "dc:title": "Sheds, soil and solitude", "dc:creator": "Ash E.", "prism:coverDate": "2021-01-01",
         "prism:publicationName": "Invented Soil Review", "prism:doi": "10.5555/allot.2", "subtypeDescription": "Article"},
    ]
    wos = [
        {"uid": "WOS:1", "title": "Sheds, soil and solitude", "types": ["Article"], "names": {"authors": [{"displayName": "Ash, E"}]},
         "source": {"sourceTitle": "INVENTED SOIL REVIEW", "publishYear": 2021}, "identifiers": {"doi": "10.5555/allot.2"}},
        {"uid": "WOS:2", "title": "Allotment waiting lists and wellbeing", "types": ["Article"],
         "names": {"authors": [{"displayName": "Yew, H"}]}, "source": {"sourceTitle": "INVENTED POLICY", "publishYear": 2022},
         "identifiers": {"doi": "10.5555/allot.5"}},
    ]

    class Stub(http.server.BaseHTTPRequestHandler):
        def log_message(self, *args):
            pass

        def send(self, code, body, ctype="application/json"):
            data = body.encode("utf-8") if isinstance(body, str) else json.dumps(body).encode("utf-8")
            self.send_response(code)
            self.send_header("Content-Type", ctype)
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)

        def do_GET(self):
            url = up.urlparse(self.path)
            q = {k: v[0] for k, v in up.parse_qs(url.query).items()}
            state.setdefault("calls", {})
            state["calls"][url.path] = state["calls"].get(url.path, 0) + 1
            state.setdefault("asked", []).append((url.path, q))
            if url.path.endswith("/esearch.fcgi"):
                ids = sorted(pubmed)
                start, size = int(q.get("retstart", 0)), int(q.get("retmax", 20))
                return self.send(200, {"esearchresult": {"count": str(len(ids)), "idlist": ids[start:start + size],
                                                         "querytranslation": "stub translation"}})
            if url.path.endswith("/efetch.fcgi"):
                parts = []
                for pmid in q.get("id", "").split(","):
                    t, y, doi, last, ini, journal, abstract = pubmed[pmid]
                    texts = "".join(f"<AbstractText>{a}</AbstractText>" for a in abstract)
                    parts.append(f"<PubmedArticle><MedlineCitation><PMID>{pmid}</PMID><Article><Journal><JournalIssue><PubDate>"
                                 f"<Year>{y}</Year></PubDate></JournalIssue><Title>{journal}</Title></Journal>"
                                 f"<ArticleTitle>{t}</ArticleTitle><Abstract>{texts}</Abstract><AuthorList><Author>"
                                 f"<LastName>{last}</LastName><Initials>{ini}</Initials></Author></AuthorList>"
                                 "<Language>eng</Language>"
                                 "<PublicationTypeList><PublicationType>Journal Article</PublicationType></PublicationTypeList>"
                                 "</Article><MeshHeadingList><MeshHeading><DescriptorName UI=\"D1\">Gardening</DescriptorName>"
                                 "</MeshHeading></MeshHeadingList><KeywordList><Keyword>allotments</Keyword></KeywordList>"
                                 "</MedlineCitation>"
                                 f"<PubmedData><ArticleIdList><ArticleId IdType=\"doi\">{doi}</ArticleId></ArticleIdList>"
                                 "</PubmedData></PubmedArticle>")
                return self.send(200, "<PubmedArticleSet>" + "".join(parts) + "</PubmedArticleSet>", "text/xml")
            if url.path.endswith("/europepmc/webservices/rest/search"):
                size = int(q.get("pageSize", 25))
                start = 0 if q.get("cursorMark") == "*" else int(q.get("cursorMark", "c0")[1:])
                page = epmc[start:start + size]
                return self.send(200, {"hitCount": len(epmc), "nextCursorMark": f"c{start + size}",
                                       "resultList": {"result": page}})
            if url.path.endswith("/works"):
                f = q.get("filter", "")
                if f.startswith("doi:"):
                    found = [{"id": "W" + d, "doi": "https://doi.org/" + d, "abstract_inverted_index": inverted(fills[d])}
                             for d in f[4:].split("|") if d in fills]
                    return self.send(200, {"meta": {"count": len(found)}, "results": found})
                size = int(q.get("per-page", 25))
                start = 0 if q.get("cursor") == "*" else int(q.get("cursor", "n0")[1:])
                nxt = f"n{start + size}" if start + size < len(openalex) else None
                return self.send(200, {"meta": {"count": len(openalex), "next_cursor": nxt},
                                       "results": openalex[start:start + size]})
            if url.path.endswith("/content/search/scopus"):
                if self.headers.get("X-ELS-APIKey") not in state["keys"]["scopus"]:
                    return self.send(401, {"service-error": {"status": {"statusText": "Invalid API key"}}})
                if state.get("scopus_standard_only") and q.get("view") == "COMPLETE":
                    return self.send(403, {"service-error": {"status": {"statusText": "View not allowed"}}})
                start, size = int(q.get("start", 0)), int(q.get("count", 25))
                rows = [dict(e) for e in scopus[start:start + size]]
                if q.get("view") == "STANDARD":
                    for e in rows:
                        e.pop("dc:description", None)
                return self.send(200, {"search-results": {"opensearch:totalResults": str(len(scopus)), "entry": rows}})
            if url.path.endswith("/apis/wos-starter/v1/documents"):
                key = self.headers.get("X-ApiKey") or ""
                if state.get("wos_fails"):
                    return self.send(401, f"Invalid key {key} for this API")
                if key not in state["keys"]["wos"]:
                    return self.send(401, {"message": "Invalid key"})
                page, size = int(q.get("page", 1)), int(q.get("limit", 10))
                return self.send(200, {"metadata": {"total": len(wos)}, "hits": wos[(page - 1) * size:page * size]})
            return self.send(404, {"error": "no such path"})

    return Stub


def follow_stub(state: dict):
    """A stand-in for Europe PMC and OpenAlex, for area 107 and a smoke run, on an invented topic,
    urban beekeeping and calm. `state["phase"]` 1 answers as an earlier run's search, 2 as a later
    one's, and every query asked is kept under `asked`. Each record carries its keywords and language
    since 14 October (133)."""
    import http.server
    import urllib.parse as up

    def inverted(text):
        out = {}
        for i, w in enumerate(text.split()):
            out.setdefault(w, []).append(i)
        return out

    def epmc(title, year, doi="", abstract="An invented study of keepers and their hives."):
        return {"id": title[:6], "source": "MED", "title": title, "authorString": "Hive A.", "pubYear": year, "doi": doi,
                "abstractText": abstract, "journalInfo": {"journal": {"title": "Invented Apiary Journal"}},
                "pubTypeList": {"pubType": ["Journal Article"]}, "keywordList": {"keyword": ["beekeeping"]}, "language": "eng"}

    # each work's keywords as Europe PMC and OpenAlex give them, since 14 October (133)
    def alex(title, year, doi, abstract="Invented keepers spoke of calm at the hive."):
        return {"id": "https://openalex.org/W" + doi[-1], "doi": "https://doi.org/" + doi, "title": title,
                "publication_year": int(year), "type": "article", "authorships": [{"author": {"display_name": "Bea Comb"}}],
                "primary_location": {"source": {"display_name": "Invented Apiary Journal"}},
                "abstract_inverted_index": inverted(abstract),
                "keywords": [{"display_name": "Urban beekeeping", "score": 0.6}, {"display_name": "Calm", "score": 0.3}],
                "language": "en"}

    found = {
        (1, "epmc"): [epmc("Hives on the roof", "2019", "10.5555/bee.1"), epmc("Smoke and patience", "2020", "10.5555/bee.2"),
                      epmc("Swarm season notes", "2021")],
        (1, "openalex"): [alex("Smoke and patience", "2020", "10.5555/bee.2"), alex("Queenless colonies and calm", "2022", "10.5555/bee.4")],
        (2, "epmc"): [epmc("Hives on the roof", "2019", "10.5555/bee.1"), epmc("Bees on allotments", "2023", "10.5555/bee.6")],
        (2, "openalex"): [alex("Hives on the roof", "2019", "10.5555/bee.1"), alex("Swarm Season Notes", "2021", "10.5555/bee.7")],
    }

    class Stub(http.server.BaseHTTPRequestHandler):
        def log_message(self, *args):
            pass

        def send(self, body):
            data = json.dumps(body).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)

        def do_GET(self):
            url = up.urlparse(self.path)
            q = {k: v[0] for k, v in up.parse_qs(url.query).items()}
            state.setdefault("asked", []).append((url.path, q))
            phase = state.get("phase", 1)
            if url.path.endswith("/europepmc/webservices/rest/search"):
                rows = found[(phase, "epmc")]
                return self.send({"hitCount": len(rows), "nextCursorMark": "*", "resultList": {"result": rows}})
            if url.path.endswith("/works"):
                if q.get("filter", "").startswith("doi:"):
                    return self.send({"meta": {"count": 0}, "results": []})
                rows = found[(phase, "openalex")]
                return self.send({"meta": {"count": len(rows), "next_cursor": None}, "results": rows})
            return self.send({"error": "no such path"})

    return Stub


# A small page built from markup for node, enough to press a row as a browser does: the elements and
# their attributes, closest, contains, querySelector with plain selectors, listeners that bubble, a
# tick's own click, and `press`, which sends a click as the document hears it in app.js and then does
# what HTML says a label does, so a press on a label's words ticks its box and a press on another
# control inside it does not.
MINI_PAGE_JS = r"""
const VOID = new Set(['input', 'br', 'img', 'hr', 'meta', 'link', 'source']);
function simple(n, sel) {
  const m = sel.match(/^([a-z0-9-]*)((?:\[[^\]]+\]|[.#][\w-]+)*)$/i);
  if (!m) throw new Error(`no such selector here: ${sel}`);
  if (m[1] && n.tag !== m[1].toLowerCase()) return false;
  for (const part of m[2].match(/\[[^\]]+\]|[.#][\w-]+/g) || []) {
    if (part[0] === '#') { if (n.attrs.id !== part.slice(1)) return false; continue; }
    if (part[0] === '.') { if (!String(n.attrs.class || '').split(/\s+/).includes(part.slice(1))) return false; continue; }
    const a = part.slice(1, -1).match(/^([^=]+?)(?:="([^"]*)")?$/);
    if (!(a[1] in n.attrs)) return false;
    if (a[2] !== undefined && n.attrs[a[1]] !== a[2]) return false;
  }
  return true;
}
function fire(target, type) {
  const e = { type, target };
  for (let x = target; x; x = x.parent) (x.listeners[type] || []).forEach((f) => f(e));
}
function el(tag, attrs, parent) {
  const n = { tag, attrs, parent, children: [], listeners: {}, text: '' };
  n.checked = 'checked' in attrs;
  n.disabled = 'disabled' in attrs;
  n.all = () => n.children.filter((c) => c.tag !== '#text').flatMap((c) => [c, ...c.all()]);
  n.matches = (sel) => n.tag[0] !== '#' && sel.split(',').some((one) => simple(n, one.trim()));
  n.closest = (sel) => { for (let x = n; x; x = x.parent) if (x.matches(sel)) return x; return null; };
  n.contains = (o) => { for (let x = o; x; x = x.parent) if (x === n) return true; return false; };
  n.querySelector = (sel) => n.all().find((x) => x.matches(sel)) || null;
  n.querySelectorAll = (sel) => n.all().filter((x) => x.matches(sel));
  n.addEventListener = (type, f) => { (n.listeners[type] = n.listeners[type] || []).push(f); };
  n.click = () => {
    if (n.disabled) return;
    const box = n.tag === 'input' && ['checkbox', 'radio'].includes(n.attrs.type);
    if (box) n.checked = n.attrs.type === 'radio' ? true : !n.checked;
    fire(n, box ? 'change' : 'click');
  };
  return n;
}
function parse(html) {
  const root = el('#root', {}, null);
  let at = root;
  const re = /<!--[\s\S]*?-->|<\/([a-zA-Z0-9-]+)\s*>|<([a-zA-Z][a-zA-Z0-9-]*)((?:\s+[^\s=>\/]+(?:\s*=\s*(?:"[^"]*"|'[^']*'|[^\s>]+))?)*)\s*(\/?)>|([^<]+)/g;
  let m;
  while ((m = re.exec(html))) {
    if (m[1]) {
      for (let x = at; x; x = x.parent) if (x.tag === m[1].toLowerCase()) { at = x.parent; break; }
    } else if (m[2]) {
      const attrs = {};
      for (const a of (m[3] || '').matchAll(/([^\s=]+)(?:\s*=\s*(?:"([^"]*)"|'([^']*)'|([^\s>]+)))?/g)) attrs[a[1]] = a[2] ?? a[3] ?? a[4] ?? '';
      const n = el(m[2].toLowerCase(), attrs, at);
      at.children.push(n);
      if (!VOID.has(n.tag) && !m[4]) at = n;
    } else if (m[5] && m[5].trim()) {
      const t = el('#text', {}, at);
      t.text = m[5];
      at.children.push(t);
    }
  }
  return root;
}
// a press: the pointer goes down on `down` and the click lands on `on`, the nearest element over both
// for a drag let go somewhere else, the document hearing it as app.js does, and then a label's own
// way: a press on a tick is its own, on another control does what that control does, and anywhere
// else inside a label clicks the label's control
function press(on, down = on) {
  tickPressed = down;
  tickRowClick({ target: on, defaultPrevented: false });
  tickPressed = null;
  const hit = on.closest('a, button, input, select, textarea');
  if (hit) {
    if (hit.tag === 'input' && ['checkbox', 'radio'].includes(hit.attrs.type)) hit.click();
    return;
  }
  const label = on.closest('label');
  if (!label) return;
  let page = label;
  while (page.parent) page = page.parent;
  const control = label.attrs.for ? page.all().find((x) => x.attrs.id === label.attrs.for)
    : label.querySelector('input, button, select, textarea');
  if (control) control.click();
}
"""

HEX_COLOUR = re.compile(r"(?<![&\w])#(?:[0-9A-Fa-f]{8}|[0-9A-Fa-f]{6}|[0-9A-Fa-f]{3,4})(?![\w-])")
COLOUR_FUNCTION = re.compile(r"\b(?:rgba?|hsla?|hwb|lab|lch|oklab|oklch)\(\s*[\d.]")


def blanked(text: str, pattern: str) -> str:
    """Each match of `pattern` as spaces, its newlines kept, so a line number still counts true."""
    return re.sub(pattern, lambda m: re.sub(r"[^\n]", " ", m.group(0)), text, flags=re.S)


def css_rules(text: str) -> list:
    """Every rule in a stylesheet that holds declarations, as (selector, [(property, value, line)], the
    at-rule it sits in or ""), comments set aside and a url(...) blanked, so a data URI's markup is never
    read for a colour or a brace."""
    text = blanked(blanked(text, r"/\*.*?\*/"), r"url\((?:\"[^\"]*\"|'[^']*'|[^)]*)\)")
    out, stack, start = [], [], 0
    for m in re.finditer(r"[{}]", text):
        if m.group(0) == "{":
            stack.append((" ".join(text[start:m.start()].split()), m.end()))
        elif stack:
            head, at = stack.pop()
            body = text[at:m.start()]
            if not head.startswith("@") and "{" not in body:
                decls = []
                for d in re.finditer(r"[^;]+", body):
                    if ":" in d.group(0) and d.group(0).strip():
                        prop, value = d.group(0).split(":", 1)
                        first = at + d.start() + len(d.group(0)) - len(d.group(0).lstrip())
                        decls.append((prop.strip(), " ".join(value.split()), text.count("\n", 0, first) + 1))
                out.append((head, decls, next((h for h, _ in reversed(stack) if h.startswith("@")), "")))
        start = m.end()
    return out


def tokens_of(tokens_css: str) -> dict:
    """tokens.css's values: `light` and `dark` for the tokens a theme sets, `same` for the rest, each a
    name to its value as written."""
    out = {"light": {}, "dark": {}, "same": {}}
    for selector, decls, at in css_rules(tokens_css):
        values = {p: v for p, v, _ in decls if p.startswith("--")}
        if selector == ':root, [data-theme="light"]':
            out["light"].update(values)
        elif selector == '[data-theme="dark"]' and not at:
            out["dark"].update(values)
        elif selector in (":root", ":root, [data-theme]"):
            out["same"].update(values)
    return out


def contrast_ratio(a: str, b: str) -> float:
    """WCAG's contrast between two opaque colours written #RRGGBB."""
    def lum(h):
        c = [int(h.lstrip("#")[i:i + 2], 16) / 255 for i in (0, 2, 4)]
        c = [x / 12.92 if x <= 0.04045 else ((x + 0.055) / 1.055) ** 2.4 for x in c]
        return 0.2126 * c[0] + 0.7152 * c[1] + 0.0722 * c[2]
    hi, lo = sorted((lum(a), lum(b)), reverse=True)
    return (hi + 0.05) / (lo + 0.05)


def palette_of(css: str, prefix: str) -> dict:
    """A palette's colours from a stylesheet's token blocks, `light` and `dark`, each a name to its value as
    written, for the custom properties that start with `prefix`."""
    out = {"light": {}, "dark": {}}
    for selector, decls, at in css_rules(css):
        values = {p: v for p, v, _ in decls if p.startswith(prefix)}
        if selector == ':root, [data-theme="light"]':
            out["light"].update(values)
        elif selector == '[data-theme="dark"]' and not at:
            out["dark"].update(values)
    return out


# How far apart the cases' colours stand, each theme its own (16 October, later, 157): the least colour
# distance between any two, the least under protanopia, deuteranopia and tritanopia, and the least as small
# marks a quarter of a degree across, a badge's disc on the canvas at 59%. They stood at 12, 6 and none for
# both themes, and the dark palette, apart by those, read as one pale lilac in Blue, Indigo, Purple and
# Slate, so each is raised to what its theme reached, never lowered.
CASE_APART = {"light": {"plain": 14.9, "cvd": 7.5, "small": 1.45}, "dark": {"plain": 20.0, "cvd": 10.5, "small": 2.65}}
CASE_MARK_DEGREES = 0.25
# The 25 since 21 October (More colours): the eight hold CASE_APART between any two as before, and all 25 hold
# these between neighbours in the picker, each and the next in its order and each and the one under it in its
# grid of five, as he sees them side by side, with ALL_25 the least between any two of them. Measured with
# CIEDE2000 on the colours as written and as Machado, Oliveira and Fernandes (2009) simulate protanopia,
# deuteranopia and tritanopia at full severity, and as small marks after Stone, Szafir and Setlur (2014).
CASE_NEIGHBOURS = {"light": {"plain": 11.0, "cvd": 8.0, "small": 1.45}, "dark": {"plain": 12.5, "cvd": 8.5, "small": 1.7}}
CASE_ALL_25 = 7.5
CASE_GRID = 5


def small_mark_distance(c1: str, c2: str, degrees: float = CASE_MARK_DEGREES) -> float:
    """How far apart two colours written #RRGGBB look as marks `degrees` across, in noticeable differences,
    after Stone, Szafir and Setlur (2014): each of CIELAB's L, a and b over the difference half of viewers notice at that
    size, 5.079 + 0.751/s, 5.339 + 1.541/s and 5.349 + 2.871/s for s degrees, so a small mark's hue counts
    for less beside its lightness than a large patch's does."""
    import math
    one, two = cie_lab(c1), cie_lab(c2)
    seen = [(5.079, 0.751), (5.339, 1.541), (5.349, 2.871)]
    return math.sqrt(sum(((x - y) / (a + b / degrees)) ** 2 for x, y, (a, b) in zip(one, two, seen)))


def case_palette_problems(themes_css: str, tokens_css: str) -> list:
    """What area 147 holds the cases' palette of the GETs board to (16 October, 157), the rules it holds the
    parts' colours to brought to a categorical set: 25 colours since 21 October, `--th-case0` on, in light and in
    dark alike, each a badge's ground under a letter in the card's colour, so 4.5 to 1 or more on paper,
    card and sunk paper, any two of the first eight apart by CASE_APART's colour distance, under protanopia,
    deuteranopia and tritanopia, and as small marks, every two neighbours in the picker by CASE_NEIGHBOURS's and
    any two of the 25 by CASE_ALL_25, 15 or more from every judgement's colour, the crux orange among them,
    and no hue from red to amber, below 75 degrees of OKLCH or above 345. Each problem as a line, none when
    the palette holds."""
    import itertools
    values = tokens_of(tokens_css)
    pal = palette_of(themes_css, "--th-case")
    wrong = []
    names = [f"--th-case{i}" for i in range(max(len(pal["light"]), 25))]
    if set(pal["light"]) != set(names) or set(pal["dark"]) != set(names):
        wrong.append(f"the palette is not --th-case0 on in both themes: {sorted(pal['light'])} {sorted(pal['dark'])}")
        return wrong
    for theme in ("light", "dark"):
        hexes = [pal[theme][n] for n in names]
        for n, h in zip(names, hexes):
            for ground in ("--paper", "--card", "--paper-sunk"):
                r = contrast_ratio(h, values[theme][ground])
                if r < 4.5:
                    wrong.append(f"{theme} {n} {h} on {ground} {r:.2f}")
            for judge in ("--good", "--amber", "--danger", "--crux"):
                d = colour_distance(h, values[theme][judge])
                if d < 15:
                    wrong.append(f"{theme} {n} {h} near {judge} {d:.1f}")
            hue = oklch_hue(h)
            if hue < 75 or hue > 345:
                wrong.append(f"{theme} {n} {h} a red or an orange, hue {hue:.0f}")
        apart = CASE_APART[theme]
        near = CASE_NEIGHBOURS[theme]
        pairs = [(i, i + 1) for i in range(len(names) - 1)] + [(i, i + CASE_GRID) for i in range(len(names) - CASE_GRID)]
        for i, j in pairs:
            a, b, n1, n2 = hexes[i], hexes[j], names[i], names[j]
            d = colour_distance(a, b)
            if d < near["plain"]:
                wrong.append(f"{theme} neighbours {n1}/{n2} {d:.1f}")
            for kind in CVD_MATRICES:
                d = colour_distance(cvd_simulate(a, kind), cvd_simulate(b, kind))
                if d < near["cvd"]:
                    wrong.append(f"{theme} neighbours {n1}/{n2} {kind} {d:.1f}")
            d = small_mark_distance(a, b)
            if d < near["small"]:
                wrong.append(f"{theme} neighbours {n1}/{n2} as small marks {d:.2f}")
        for (n1, a), (n2, b) in itertools.combinations(list(zip(names, hexes)), 2):
            d = colour_distance(a, b)
            if d < CASE_ALL_25:
                wrong.append(f"{theme} {n1}/{n2} {d:.1f}, too near to tell apart")
        for (n1, a), (n2, b) in itertools.combinations(list(zip(names[:8], hexes[:8])), 2):
            d = colour_distance(a, b)
            if d < apart["plain"]:
                wrong.append(f"{theme} {n1}/{n2} {d:.1f}")
            for kind in CVD_MATRICES:
                d = colour_distance(cvd_simulate(a, kind), cvd_simulate(b, kind))
                if d < apart["cvd"]:
                    wrong.append(f"{theme} {n1}/{n2} {kind} {d:.1f}")
            d = small_mark_distance(a, b)
            if d < apart["small"]:
                wrong.append(f"{theme} {n1}/{n2} as small marks {d:.2f}")
    return wrong


TOP_BAR_SHARED = ("search", "shortcuts", "feedback", "settings")
TOP_BAR_BACKS = ("to-library", "th-back", "sf-back", "sfs-back", "tr-back")
# Distil's steps in the book's order, one row on each of its bars since 18 October (area 177)
DISTIL_STEPS = ("statements", "pets", "gets")


def top_bar_kinds(bar: str) -> list:
    """Each button of a title bar's markup in its order, by what it is: `cases` and `inspector` for a
    sidebar's toggle, `back` for the way back, `step` for a step of a row of steps written in the
    markup, Distil's since 18 October, `search`, `shortcuts`, `feedback`, `settings` and `appearance`
    by name, and `own` for any other tool, a switcher left out. Search took Find's place on the bars
    on 17 October, and a bar's Find and replace counts in the same place."""
    kinds = []
    for tag in re.findall(r"<button\b[^>]*>", bar):
        ident = (re.search(r'\bid="([^"]+)"', tag) or [None, ""])[1]
        label = (re.search(r'\baria-label="([^"]+)"', tag) or [None, ""])[1]
        if 'data-door="cases"' in tag:
            kinds.append("cases")
        elif 'data-door="side"' in tag:
            kinds.append("inspector")
        elif ident in TOP_BAR_BACKS:
            kinds.append("back")
        elif 'data-step="' in tag:
            kinds.append("step")
        elif label == "Appearance" or ident.endswith("-theme"):
            kinds.append("appearance")
        elif label in ("Search", "Find and replace"):
            kinds.append("search")
        elif label == "Shortcuts":
            kinds.append("shortcuts")
        elif label == "Send feedback":
            kinds.append("feedback")
        elif label.lower().endswith("settings"):
            kinds.append("settings")
        elif "bar-tool" in tag:
            kinds.append("own")
    return kinds


def top_bar_problems(bars: dict) -> list:
    """What breaks The title bar in docs/design.md, bar by bar (16 October, area 155): Appearance on a
    bar, Send feedback or Settings missing or doubled, the tools every bar ends with out of their order,
    one of the screen's own tools after them, Cases anywhere but the left end, Inspector anywhere but
    the right end, the way back anywhere but first, after Cases where there is one, and since 18 October
    a row of steps split, before the way back or after a tool, or Distil's out of the book's order."""
    out = []
    for name, bar in bars.items():
        kinds = top_bar_kinds(bar)
        if "appearance" in kinds:
            out.append(f"{name}: Appearance on the bar")
        for one in ("feedback", "settings"):
            if kinds.count(one) != 1:
                out.append(f"{name}: {kinds.count(one)} of {one}")
        shared = [k for k in kinds if k in TOP_BAR_SHARED]
        if shared != sorted(shared, key=TOP_BAR_SHARED.index) or len(set(shared)) != len(shared):
            out.append(f"{name}: the shared tools out of order, {shared}")
        first = next((i for i, k in enumerate(kinds) if k in TOP_BAR_SHARED), len(kinds))
        if "own" in kinds[first:]:
            out.append(f"{name}: a tool of its own after the shared ones")
        if "cases" in kinds and (kinds.index("cases") != 0 or kinds.count("cases") != 1):
            out.append(f"{name}: Cases away from the left end")
        if "inspector" in kinds and (kinds.index("inspector") != len(kinds) - 1 or kinds.count("inspector") != 1):
            out.append(f"{name}: Inspector away from the right end")
        if "back" in kinds and kinds.index("back") != (1 if kinds[:1] == ["cases"] else 0):
            out.append(f"{name}: the way back not first")
        if kinds and kinds[-1] not in ("settings", "inspector"):
            out.append(f"{name}: {kinds[-1]} after Settings")
        at = [i for i, k in enumerate(kinds) if k == "step"]
        if at:
            if at != list(range(at[0], at[0] + len(at))):
                out.append(f"{name}: the steps apart")
            if "back" in kinds and kinds.index("back") > at[0]:
                out.append(f"{name}: the steps before the way back")
            if any(k not in ("cases", "back") for k in kinds[:at[0]]):
                out.append(f"{name}: the steps after a tool")
            distil = [s for s in re.findall(r'<button\b[^>]*\bdata-step="([^"]+)"', bar) if s in DISTIL_STEPS]
            if distil and distil != list(DISTIL_STEPS):
                out.append(f"{name}: Distil's steps out of the book's order, {distil}")
    return out


def cie_lab(h: str) -> tuple:
    """A colour written #RRGGBB in CIELAB, D65."""
    def lin(c):
        return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4
    r, g, b = (lin(int(h.lstrip("#")[i:i + 2], 16) / 255) for i in (0, 2, 4))
    x = (0.4124 * r + 0.3576 * g + 0.1805 * b) / 0.95047
    y = 0.2126 * r + 0.7152 * g + 0.0722 * b
    z = (0.0193 * r + 0.1192 * g + 0.9505 * b) / 1.08883
    f = lambda t: t ** (1 / 3) if t > 0.008856 else 7.787 * t + 16 / 116
    return 116 * f(y) - 16, 500 * (f(x) - f(y)), 200 * (f(y) - f(z))


def colour_distance(c1: str, c2: str) -> float:
    """CIEDE2000, the colour difference between two colours written #RRGGBB, about 2 the least an eye
    tells apart side by side and 10 or more two colours that read as different."""
    return lab_distance(cie_lab(c1), cie_lab(c2))


def lab_distance(one: tuple, two: tuple) -> float:
    """CIEDE2000 between two CIELAB colours, after Sharma, Wu and Dalal (2005)."""
    import math
    (l1, a1, b1), (l2, a2, b2) = one, two
    cb = (math.hypot(a1, b1) + math.hypot(a2, b2)) / 2
    g = 0.5 * (1 - math.sqrt(cb ** 7 / (cb ** 7 + 25 ** 7)))
    a1, a2 = a1 * (1 + g), a2 * (1 + g)
    c1p, c2p = math.hypot(a1, b1), math.hypot(a2, b2)
    h1, h2 = math.degrees(math.atan2(b1, a1)) % 360, math.degrees(math.atan2(b2, a2)) % 360
    dh = 0 if c1p * c2p == 0 else (h2 - h1 if abs(h2 - h1) <= 180 else h2 - h1 - 360 if h2 > h1 else h2 - h1 + 360)
    d_l, d_c, d_h = l2 - l1, c2p - c1p, 2 * math.sqrt(c1p * c2p) * math.sin(math.radians(dh / 2))
    lb, cbp = (l1 + l2) / 2, (c1p + c2p) / 2
    hb = (h1 + h2 if c1p * c2p == 0 else (h1 + h2) / 2 if abs(h1 - h2) <= 180
          else (h1 + h2 + 360) / 2 if h1 + h2 < 360 else (h1 + h2 - 360) / 2)
    t = (1 - 0.17 * math.cos(math.radians(hb - 30)) + 0.24 * math.cos(math.radians(2 * hb))
         + 0.32 * math.cos(math.radians(3 * hb + 6)) - 0.20 * math.cos(math.radians(4 * hb - 63)))
    s_l = 1 + 0.015 * (lb - 50) ** 2 / math.sqrt(20 + (lb - 50) ** 2)
    s_c, s_h = 1 + 0.045 * cbp, 1 + 0.015 * cbp * t
    r_t = (-math.sin(math.radians(60 * math.exp(-((hb - 275) / 25) ** 2)))
           * 2 * math.sqrt(cbp ** 7 / (cbp ** 7 + 25 ** 7)))
    return math.sqrt((d_l / s_l) ** 2 + (d_c / s_c) ** 2 + (d_h / s_h) ** 2 + r_t * (d_c / s_c) * (d_h / s_h))


# Machado, Oliveira and Fernandes (2009), severity 1, in linear RGB: how a colour looks to a person with
# protanopia, deuteranopia or tritanopia
CVD_MATRICES = {
    "protan": ((0.152286, 1.052583, -0.204868), (0.114503, 0.786281, 0.099216), (-0.003882, -0.048116, 1.051998)),
    "deutan": ((0.367322, 0.860646, -0.227968), (0.280085, 0.672501, 0.047413), (-0.011820, 0.042940, 0.968881)),
    "tritan": ((1.255528, -0.076749, -0.178779), (-0.078411, 0.930809, 0.147602), (0.004733, 0.691367, 0.303900)),
}


def cvd_simulate(h: str, kind: str) -> str:
    """A colour written #RRGGBB as `kind` of colour blindness sees it, after Machado, Oliveira and Fernandes."""
    lin = lambda x: x / 12.92 if x <= 0.04045 else ((x + 0.055) / 1.055) ** 2.4
    out = lambda x: 12.92 * x if x <= 0.0031308 else 1.055 * x ** (1 / 2.4) - 0.055
    c = [lin(int(h.lstrip("#")[i:i + 2], 16) / 255) for i in (0, 2, 4)]
    m = CVD_MATRICES[kind]
    seen = [max(0.0, min(1.0, sum(m[r][k] * c[k] for k in range(3)))) for r in range(3)]
    return "#" + "".join(f"{round(out(x) * 255):02X}" for x in seen)


def oklch_hue(h: str) -> float:
    """A colour written #RRGGBB's hue in OKLCH, in degrees, after Ottosson (2020)."""
    import math
    lin = lambda x: x / 12.92 if x <= 0.04045 else ((x + 0.055) / 1.055) ** 2.4
    r, g, b = (lin(int(h.lstrip("#")[i:i + 2], 16) / 255) for i in (0, 2, 4))
    l = (0.4122214708 * r + 0.5363325363 * g + 0.0514459929 * b) ** (1 / 3)
    m = (0.2119034982 * r + 0.6806995451 * g + 0.1073969566 * b) ** (1 / 3)
    s = (0.0883024619 * r + 0.2817188376 * g + 0.6299787005 * b) ** (1 / 3)
    a = 1.9779984951 * l - 2.4285922050 * m + 0.4505937099 * s
    bb = 0.0259040371 * l + 0.7827717662 * m - 0.8086757660 * s
    return math.degrees(math.atan2(bb, a)) % 360


def refusal_of(fn) -> str:
    try:
        fn()
    except WorkbookError as exc:
        return str(exc)
    return ""


def urllib_path(url: str) -> str:
    from urllib.parse import urlparse
    return urlparse(url).path


# ─────────────────────────────────────────────────────── the suite's own files ──

def suite_files() -> list[Path]:
    """Every Python file of the suite, the runner first, then this package's in name order, the support
    module and every area among them. A check of the suite's own words reads them all."""
    return [HERE / "test_idiograph.py"] + sorted((HERE / "areas").glob("*.py"))


def suite_text() -> str:
    """The words of every Python file of the suite, one file after another."""
    return "\n".join(p.read_text(encoding="utf-8") for p in suite_files())


# ─────────────────────────────────────── the suite's own checks, after every run ──

def areas_listed(listed) -> None:
    """Every area's file under areas/ in the runner's list once, in the order of its number, and every
    name in the list a file, so an area added without its line, or a line left without its file, fails."""
    files = sorted(p.stem for p in (HERE / "areas").glob("a[0-9][0-9][0-9]_*.py"))
    numbers = [int(name[1:4]) for name in listed]
    unlisted, missing = sorted(set(files) - set(listed)), sorted(set(listed) - set(files))
    check("the suite's areas: every file under tests/areas is in the runner's list once, in the order of its "
          "number, and every name in the list is a file",
          files and not unlisted and not missing and len(set(listed)) == len(listed) and numbers == sorted(numbers),
          f"{len(files)} areas" if not (unlisted or missing) else f"not listed {unlisted[:5]}, no file {missing[:5]}")


# the oldest Python the app runs on, the README's 3.11, which GitHub's Windows run uses, and where the
# installer from python.org puts it on a Mac
OLDEST_PYTHON = (3, 11)
MAC_PYTHON_311 = "/Library/Frameworks/Python.framework/Versions/3.11/bin/python3.11"
# what that Python runs: every path on its input compiled, nothing written, each one that fails a line
COMPILE_EACH = (
    "import sys\n"
    "for path in sys.stdin.buffer.read().decode('utf-8').splitlines():\n"
    "    try:\n"
    "        with open(path, 'rb') as fh:\n"
    "            compile(fh.read(), path, 'exec', dont_inherit=True)\n"
    "    except SyntaxError as exc:\n"
    "        print(f'{path}:{exc.lineno} {exc.msg}')\n"
)


def oldest_python() -> list[str] | None:
    """A command that runs Python 3.11, each one asked its version: this Python when it is 3.11, else
    python3.11 on the path, the Mac's from python.org, or Windows's py launcher. None on a machine
    with none of them."""
    if sys.version_info[:2] == OLDEST_PYTHON:
        return [sys.executable]
    on_path = shutil.which("python3.11")
    tries = ([[on_path]] if on_path else []) + ([[MAC_PYTHON_311]] if Path(MAC_PYTHON_311).is_file() else [])
    tries += [["py", "-3.11"]] if shutil.which("py") else []
    for command in tries:
        try:
            asked = subprocess.run(command + ["-I", "-c", "import sys\nprint(*sys.version_info[:2])"],
                                   capture_output=True, timeout=60)
        except (OSError, subprocess.TimeoutExpired):
            continue
        if asked.returncode == 0 and asked.stdout.decode("utf-8", errors="replace").split() == ["3", "11"]:
            return command
    return None


def app_python_files() -> list[Path]:
    """Every Python file under the app's folder that git keeps or would keep, tracked or new and not
    ignored, and in a copy with no git, the gate's snapshot among them, every one under it but the first
    run's .venv, a build's folders and the caches. Git is asked of the folder itself, whatever a
    caller's environment points it at."""
    alone = {k: v for k, v in os.environ.items() if not k.startswith("GIT_")}
    try:
        listed = subprocess.run(["git", "ls-files", "-z", "--cached", "--others", "--exclude-standard", "--", "*.py"],
                                cwd=TOOL, capture_output=True, timeout=60, env=dict(alone, GIT_OPTIONAL_LOCKS="0"))
    except (OSError, subprocess.TimeoutExpired):
        listed = None
    if listed is not None and listed.returncode == 0 and listed.stdout:
        return sorted({TOOL / p for p in listed.stdout.decode("utf-8").split("\0") if p and (TOOL / p).is_file()})
    left_out = {".venv", ".venv-setup", "build", "dist", "__pycache__", "node_modules"}
    return sorted(p for p in TOOL.rglob("*.py") if not left_out & set(p.relative_to(TOOL).parts))


def oldest_python_compiles() -> None:
    """Every Python file of the app compiled by Python 3.11 when the machine has one, since a form
    newer than 3.11 in any of them, a check's line among them, stops every run on GitHub's Windows
    machine while the Mac's newer Python passes it (16 October). A skip says so on a machine with none."""
    name = "every Python file of the app, the suite's among them, compiles on Python 3.11, the oldest it runs on"
    command = oldest_python()
    if command is None:
        return skip(name, "no Python 3.11 on this machine")
    files = app_python_files()
    ran = subprocess.run(command + ["-I", "-c", COMPILE_EACH], cwd=TOOL, capture_output=True, timeout=600,
                         input="\n".join(p.relative_to(TOOL).as_posix() for p in files).encode("utf-8"))
    failed = [line for line in ran.stdout.decode("utf-8", errors="replace").splitlines() if line.strip()]
    said = ran.stderr.decode("utf-8", errors="replace").strip()
    check(name, ran.returncode == 0 and not failed and len(files) > 30,
          f"{len(files)} files" if ran.returncode == 0 and not failed else str(failed[:5] or said[-300:]))
