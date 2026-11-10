"""311. The table of PETs' pages (pdfexport, Adam, 31 October 2026).

Adam printed a participant's table from the Mac's window and saved it as PDF: a PET's title fell at the
foot of a page with its rows on the next, and the last page was blank but for one green bar. Checked
here on the demo's Juno, invented, in a scratch copy: every title, a PET's, a sub-PET's and a group's,
sits in a part of its block that a page never splits, `.lead`, with the first row under it, the rest
following in `.cont`; the Mac's web view printing every point as a point, as
Chrome does, and the table typeset by Typst ending on a page that carries rows. Export as PDF is the
server's, through Typst, since 9 November 2026 (area 367).
"""
from __future__ import annotations

import json
import re
import shutil
from pathlib import Path

from . import support
from .support import DEMO_QUESTION, check


NODE_PDF = r"""
const out = {};
let state = null;
const fresh = () => ({ calls: [], saved: null, printed: 0, exported: null, said: [] });
const TH = { live: true, busy: false, printable: true, dirty: false, path: 'Juno.xlsx', meta: { id: 'b1', name: 'Board 1' } };
const t = (key) => (key === 'themes.pdf.failed' ? 'The PDF was not saved.' : key);
let failing = null;
const say = (line) => state.said.push(line);
const needsRestart = () => false;
const RESTART_LINE = 'restart';
const thTitleDone = () => {};
const thNoteDone = () => {};
const thFlush = async () => {};
const thWhere = () => ({});
const thIncludesSent = (asQuery) => (asQuery ? { sending: '0' } : { sending: false });
const thPrint = () => { state.printed += 1; };
const thExported = (info) => { state.exported = info; };
const console = { warn: () => {} };
async function api(url, body) {
  state.calls.push([url, body]);
  if (failing) throw new Error(failing);
  return { path: '/cases/Juno/Juno - Board 1 - PETs.pdf', shown: ['Juno - Board 1 - PETs.pdf'], version: { name: 'Board 1' } };
}
const window = { location: { href: 'http://127.0.0.1:8799/#pets' } };
/*FN*/
(async () => {
  state = fresh();
  await thPdf();
  out.window = state;
  state = fresh();
  failing = 'The PDF could not be made, so nothing was written.';
  await thPdf();
  out.failed = state;
  process.stdout.write(JSON.stringify(out) + '\n');
})();
"""


def rule(css: str, selector: str) -> str:
    """The declarations of the first plain rule whose selector list is `selector` exactly."""
    for heads, body in re.findall(r"([^{}]+)\{([^{}]*)\}", css):
        if [h.strip() for h in heads.split(",")] == [s.strip() for s in selector.split(",")]:
            return body
    return ""


def head_of(page: str) -> str:
    """The page's head, its `<header class="head">` to its close."""
    return page.split('<header class="head">', 1)[-1].split("</header>", 1)[0]


def words(markup: str) -> str:
    """The text of a piece of markup, its tags gone, its entities read and its spaces single."""
    import html as html_mod

    return " ".join(html_mod.unescape(re.sub(r"<[^>]+>", " ", markup)).split())


def parse(html_text: str) -> dict:
    """The page's sections and divs as a tree, each node its tag, its classes and its children."""
    from html.parser import HTMLParser

    root = {"tag": "root", "class": [], "kids": []}
    stack = [root]

    class Tree(HTMLParser):
        def handle_starttag(self, tag, attrs):
            if tag in ("section", "div"):
                node = {"tag": tag, "class": (dict(attrs).get("class") or "").split(), "kids": []}
                stack[-1]["kids"].append(node)
                stack.append(node)

        def handle_endtag(self, tag):
            if tag in ("section", "div") and len(stack) > 1:
                stack.pop()

    Tree().feed(html_text)
    return root


def walk(node: dict):
    for kid in node["kids"]:
        yield kid
        yield from walk(kid)


def test_print_pages(scratch: Path):
    print("\n311. The table of PETs' pages: a title kept with its first row, nothing spilling onto a page of its "
          "own after the last row, and a point printed as a point in the Mac's web view")
    import gets_print
    import i18n
    import print_pdf
    import themes_print

    root = scratch / "a311"
    shutil.rmtree(root, ignore_errors=True)
    (root / "Juno" / "Working").mkdir(parents=True)
    # the demo as it ships, Juno's board of five PETs and their sub-PETs among it
    pristine = support.DEMO_SHIPPED
    for name in ("Juno", "Mabel", "Rowan"):
        (root / name / "Working").mkdir(parents=True, exist_ok=True)
        shutil.copy2(pristine / f"{name} - EN & ES.xlsx", root / name / f"{name} - EN & ES.xlsx")
        for side in sorted((pristine / "Working").glob(f"{name} - *")):
            shutil.copy2(side, root / name / "Working" / side.name)
    # the demo's GETs board, for its print's foot and Save as PDF's place
    shutil.copy2(pristine / "idiograph-gets.json", root / "idiograph-gets.json")
    book = root / "Juno" / "Juno - EN & ES.xlsx"
    page = themes_print.page(book, "Juno", None, DEMO_QUESTION, auto=False)
    main = page.split("<main>", 1)[1].split("</main>", 1)[0]

    # ── A. every title in a lead with the first row under it
    heads = list(re.finditer(r'<h([2-5]) class="(?:pet-title|sub-title|group-title)"', main))
    alone = []
    for m in heads:
        # the lead the title opens, up to where that lead's own section closes: its first row is in it,
        # a sub-PET's lead nested inside closing first
        opened = main.rfind("<section ", 0, m.start())
        tag = main[opened:main.index(">", opened)]
        rest = main[m.end():]
        if " lead" not in tag or '<div class="item">' not in rest.split("</section>", 1)[0]:
            alone.append(re.sub(r"<[^>]+>", "", main[m.start():main.index("</h", m.start())])[:40])
    leads = re.findall(r'<section class="block [^"]*\blead\b', main)
    check("311: every PET's, sub-PET's and group's title sits in its block's lead with its first row, the rest after it",
          heads and not alone and len(leads) == len(heads) and main.count('class="block') == len(leads) + main.count(" cont\">"),
          f"{len(heads)} titles, {len(leads)} leads, alone: {alone}")
    css = re.findall(r"<style>(.*?)</style>", page, flags=re.S)[0]
    check("311: a lead is never split across a page, nor a row, so a title never stands alone at a page's foot",
          "break-inside: avoid" in rule(css, ".lead") and "break-inside: avoid" in rule(css, ".item"))

    # ── A2. nothing more kept together than a title and its first row, so the rows flow and the pages fill
    # (Adam, 31 October, later: no sub-PET kept whole, no last rows kept together)
    tree = parse(main)
    sections = [n for n in walk(tree) if n["tag"] == "section"]
    leads = [n for n in sections if "lead" in n["class"]]
    rows_in = lambda n: sum(1 for k in walk(n) if "item" in k["class"])
    held = [rows_in(n) for n in leads if not any("lead" in k["class"] for k in walk(n))]
    check("311: a lead holds its title and its first row alone, a PET's with its first sub-PET's title and first row, "
          "and every other row flows",
          held and all(n == 1 for n in held) and not any("tail" in k["class"] for k in walk(tree))
          and main.count('<div class="item">') > len(held), f"rows in each innermost lead: {held}")

    # ── B. nothing below the last row to spill onto a page of its own: the headless print at the end holds it,
    # a check of the padding and margins that do it going on 2 November (testspeed), spacing for review shots

    # the foot in three parts (Adam, 31 October): the participant, the project and the table at the left, the
    # researcher and Confidential in the middle, the page at the right
    named = themes_print.page(book, "Juno", None, DEMO_QUESTION, auto=False, project="Living with a dog", researcher="Ada Lark")
    plain = themes_print.page(book, "Juno", None, DEMO_QUESTION, auto=False, confidential=False)
    # a box's content, its pieces joined into one string as Chrome joins them, the right box's counters as served
    raw = lambda text, where: (re.search(r"@bottom-" + where + r" \{ content: (.*?);(?: --idiograph-fit: \d+;)? font-family", text)
                               or [None, None])[1]
    box = lambda text, where: (raw(text, where) if where == "right" or raw(text, where) is None
                               else '"' + "".join(re.findall(r'"((?:[^"\\]|\\.)*)"', raw(text, where))) + '"')
    day = themes_print.when_printed()
    check("311: the foot on paper: participant with the board in brackets, project and table at the left, the "
          "researcher, Confidential and the date in the middle, and the page of how many at the right, never the themes "
          "file, and the head with the project before the question and nothing at its top right",
          box(named, "left") == '"Juno (Board 1)  ·  Living with a dog  ·  Table of Personal Experiential Themes"'
          and box(named, "center") == f'"Ada Lark  ·  Confidential  ·  {day}"' and box(page, "center") == f'"Confidential  ·  {day}"'
          and box(plain, "center") == f'"{day}"' and box(page, "left") == '"Juno (Board 1)  ·  Table of Personal Experiential Themes"'
          and 'class="stamp"' not in named and words(head_of(named)).index("Living with a dog") < words(head_of(named)).index(DEMO_QUESTION)
          and box(named, "right") == '"Page " counter(page) " of " counter(pages) !important' and ".themes.json" not in page,
          f"{box(named, 'left')} | {box(named, 'center')} | {box(named, 'right')}")

    # ── C. a point a point in WebKit's print, which prints a CSS pixel as 0.8 of a point, the PETs and the GETs print alike
    true_size = re.compile(r"@supports \(font: -apple-system-body\) \{\s*@media print \{ html \{ zoom: \.9375; \} \}")
    import server as server_mod
    import idiograph_routes
    shutil.copy2(support.source("demo/idiograph-project.json"), root / "idiograph-project.json")
    saved = (server_mod.ROOT_OVERRIDE, server_mod.STATE_MEMORY)
    server_mod.ROOT_OVERRIDE, server_mod.STATE_MEMORY = str(root), {"recent": []}
    try:
        code, gets_page = idiograph_routes.gets_print_page({"root": str(root), "what": "table", "detail": "full", "auto": "0"})
    finally:
        server_mod.ROOT_OVERRIDE, server_mod.STATE_MEMORY = saved
    check("311: the table of PETs and the GETs print print at their own size in the Mac's web view, each point a point",
          true_size.search(page) is not None and code == 200 and true_size.search(gets_page) is not None
          and true_size.search(gets_print.PAGE) is None)
    # the GETs table's head as the table of PETs has it (Adam, 31 October): the table's name and the research question
    # in the head, and neither print saying the PETs or the GETs marked complete
    gets_head, named_table = words(head_of(gets_page)), i18n.t("page_print.gets.table_name")
    check("311: the GETs table's head carries the table's name and the research question, and no printed table says "
          "the PETs or the GETs marked complete",
          named_table in gets_head and DEMO_QUESTION in gets_head
          and gets_head.index(named_table) < gets_head.index(DEMO_QUESTION)
          and "marked complete" not in gets_page.split("<main>", 1)[0] and "marked complete" not in page,
          gets_head[:200])

    # ── E. Export as PDF: the server writes the file where Word's goes, made by Typst (typst5, 9 November 2026)
    import gets as gets_mod
    server_mod.ROOT_OVERRIDE, server_mod.STATE_MEMORY = str(root), {"recent": []}
    try:
        place = idiograph_routes.api_themes_export({"workbook": str(book), "op": "pdf", "sending": False})
        again = idiograph_routes.api_themes_export({"workbook": str(book), "op": "pdf", "sending": False})
        written = (root / "Juno" / place["name"]).read_bytes()
        (root / "Juno" / place["name"]).unlink()
        (root / "Juno" / again["name"]).unlink()
        gets_root = root
        gets_file = gets_mod.load(gets_root)
        gets_board = (themes_print.th.boards_of(gets_file) or [{}])[0].get("id", "")
        gets_place = idiograph_routes.api_gets_boards({"root": str(gets_root), "board": gets_board, "op": "pdf", "what": "table"}) if gets_board else {}
    finally:
        server_mod.ROOT_OVERRIDE, server_mod.STATE_MEMORY = saved
    check("311: Export as PDF writes the PDF beside the workbook, named as the print view names it",
          Path(place["path"]).parent == book.parent and place["name"] == f"{print_pdf.stem_of('Juno', place['version']['name'])}.pdf"
          and place["shown"] == [place["name"]] and written[:5] == b"%PDF-", json.dumps(place)[:300])
    check("311: a file there already, the next PDF takes the date and time in its name, never over it",
          again["dated"] is True and again["name"] != place["name"] and again["name"].startswith(place["name"][:-4]), again["name"])
    check("311: a GETs board's Save as PDF goes at the project's root, named as gets export names it",
          bool(gets_board) and (Path(gets_place["path"]).parent == gets_root and gets_place["name"].endswith(" - GET table.pdf")
                             and Path(gets_place["path"]).read_bytes()[:5] == b"%PDF-"),
          json.dumps(gets_place)[:300])
    if gets_place:
        Path(gets_place["path"]).unlink()

    # the page's own Export as PDF, in node: in the window and a browser's tab alike it asks the server, which writes
    # the file, and says what it wrote, or the server's plain sentence when it could not
    themes_js = support.text("apps/idiograph/static/themes.js")
    fn = "async function thPdf(" + themes_js.split("async function thPdf(", 1)[1].split("\n}\n", 1)[0] + "\n}\n"
    result = support.run_node(NODE_PDF.replace("/*FN*/", fn), scratch / "a311", "a311-pdf.js")
    got = json.loads(result.stdout.strip().splitlines()[-1]) if result.returncode == 0 and result.stdout.strip() else {}
    window_run, failed_run = got.get("window") or {}, got.get("failed") or {}
    check("311: Export as PDF asks the server to write the file, in the window and a browser's tab alike, and says what "
          "it wrote",
          window_run.get("calls") == [["/api/themes-export", {"workbook": "Juno.xlsx", "version": "b1", "op": "pdf", "sending": False}]]
          and window_run.get("exported") == {"shown": ["Juno - Board 1 - PETs.pdf"], "name": "Board 1", "reveal": True, "word": False}
          and not window_run.get("printed"), result.stderr[-400:] or json.dumps(got)[:500])
    check("311: a PDF the server could not make says the server's plain sentence, and no line names a file",
          failed_run.get("said") == ["The PDF could not be made, so nothing was written."] and not failed_run.get("exported"),
          json.dumps(failed_run))

    # ── F. Your name, the name documents carry: the foot's and Word's author, the interviewer's name while it is empty
    import themes_word
    held_config = server_mod.CONFIG_PATH
    server_mod.CONFIG_PATH = root / "config.json"
    server_mod.CONFIG_PATH.write_text(json.dumps({"interviewer": "Kit"}), encoding="utf-8")
    try:
        before_name = idiograph_routes.researcher_name()
        server_mod.api_settings({"your_name": "  Ada   Lark "})
        read_back = server_mod.api_settings({"op": "read"})["config"].get("your_name")
        named_now = idiograph_routes.researcher_name()
        server_mod.api_settings({"your_name": ""})
        emptied = idiograph_routes.researcher_name()
    finally:
        server_mod.CONFIG_PATH = held_config
    check("311: Your name is saved on its own line, read back by the settings' read op, named in the foot and as "
          "Word's author, and with it empty the interviewer's name stands in",
          before_name == "Kit" and read_back == "Ada Lark" and named_now == "Ada Lark" and emptied == "Kit",
          f"{before_name} | {read_back} | {named_now} | {emptied}")
    import io
    import zipfile
    core = lambda data: zipfile.ZipFile(io.BytesIO(data)).read("docProps/core.xml").decode("utf-8")
    check("311: Word's author field carries the name, and a document with no name carries none",
          "<dc:creator>Ada Lark</dc:creator>" in core(themes_word.package([], "T", author="Ada Lark"))
          and "dc:creator" not in core(themes_word.package([], "T")))

    # ── G. the foot on the Mac (exportpdf2): the window reads the foot from the print view's own @page margin boxes,
    # as served, and draws it on paper, since the Mac's web view draws no margin box, so one place says the foot.
    import html as html_mod
    import i18n
    window_js = support.text("packaging/tauri/window.js")
    served = server_mod.own_margins(themes_print.page(book, "Juno", None, DEMO_QUESTION, auto=False, project="Living with a dog",
                                                      researcher="Ada Lark"))
    gets_served = server_mod.own_margins(gets_print.page(root, [], {"name": "Living with a dog"}, auto=False, researcher="Ada Lark"))
    styles = lambda doc: "\n".join(re.findall(r"<style>(.*?)</style>", doc, flags=re.S))
    screen_foot = lambda doc: html_mod.unescape(re.findall(r"<footer>(.*?)</footer>", doc, flags=re.S)[-1])
    node_foot = ("var calls = [];\nvar window = { __TAURI_INTERNALS__: { invoke: function (c, a) { calls.push([c, a]); "
                 "return Promise.resolve(a.path); } }, __IDIOGRAPH_OS__: 'linux', addEventListener: function () {},"
                 " document: { addEventListener: function () {}, querySelectorAll: function () { return []; } } };\n"
                 "var PAGES = " + json.dumps({"pets": served, "gets": gets_served}) + ";\n"
                 "var fetch = function (href) { return Promise.resolve({ ok: true, text: function () { return Promise.resolve(PAGES[href]); } }); };\n"
                 "function DOMParser() {}\nDOMParser.prototype.parseFromString = function (doc) { var found = [];"
                 " doc.replace(/<style>([\\s\\S]*?)<\\/style>/g, function (_, css) { found.push({ textContent: css }); });"
                 " return { querySelectorAll: function () { return found; } }; };\n"
                 + window_js + "\n"
                 "var CSS = " + json.dumps({"pets": styles(served), "gets": styles(gets_served), "none": "@page { size: A4 }"}) + ";\n"
                 "var out = { read: {} };\nfor (var k in CSS) out.read[k] = idiographPageFoot(CSS[k]);\n"
                 "process.stdout.write(JSON.stringify(out) + '\\n');\n")
    ran = support.run_node(node_foot, scratch / "a311", "a311-foot.js")
    feet = json.loads(ran.stdout.strip().splitlines()[-1]) if ran.returncode == 0 and ran.stdout.strip() else {}
    said = lambda box, page, pages: "".join(p if isinstance(p, str) else str(page if p.get("counter") == "page" else pages)
                                            for p in (box or []))
    pets_foot, gets_foot = (feet.get("read") or {}).get("pets") or {}, (feet.get("read") or {}).get("gets") or {}
    joined = lambda foot: said(foot.get("left"), 1, 1) + "  ·  " + said(foot.get("center"), 1, 1)
    check("311: the window reads the print view's foot from its own @page boxes as served: the participant, project and "
          "table at the left, the name, Confidential and the date in the middle, the page and count at the right, "
          "the page's margins and type",
          joined(pets_foot) == screen_foot(served) and "Juno" in joined(pets_foot) and "Ada Lark" in joined(pets_foot)
          and said(pets_foot.get("right"), 2, 3) == i18n.t("page_print.page_of", page=2, pages=3)
          and pets_foot.get("margins") == [14, 16, 16, 16] and pets_foot.get("size") == 7
          and str(pets_foot.get("color")).upper() == themes_print.PRINT_FAINT.upper(),
          ran.stderr[-400:] or json.dumps(pets_foot)[:500])
    check("311: the GETs print's foot is read the same way, and a page with no foot asks the window for none",
          joined(gets_foot) == screen_foot(gets_served) and said(gets_foot.get("right"), 4, 4) == i18n.t("page_print.page_of", page=4, pages=4)
          and gets_foot.get("margins") == [14, 14, 14, 14] and (feet.get("read") or {}).get("none") is None,
          json.dumps(gets_foot)[:400])
    node_print = ("var calls = [];\nvar CSS = " + json.dumps(styles(served)) + ";\n"
                  "var window = { __TAURI_INTERNALS__: { invoke: function (c, a) { calls.push([c, a]); return Promise.resolve(null); } },"
                  " __IDIOGRAPH_OS__: 'macos', addEventListener: function () {}, location: { href: 'http://127.0.0.1:8799/themes/print' },"
                  " document: { title: 'Juno', addEventListener: function () {}, querySelectorAll: function () { return [{ textContent: CSS }]; } } };\n"
                  + window_js + "\nwindow.print();\n"
                  "process.stdout.write(JSON.stringify({ calls: calls, foot: idiographPageFoot(CSS) }) + '\\n');\n")
    ran_print = support.run_node(node_print, scratch / "a311", "a311-foot-print.js")
    printed = json.loads(ran_print.stdout.strip().splitlines()[-1]) if ran_print.returncode == 0 and ran_print.stdout.strip() else {}
    asked = [a for c, a in printed.get("calls") or [] if c == "print"]
    check("311: the window's Print on a Mac hands it the same foot, read by the same reader from the page it prints",
          len(asked) == 1 and asked[0].get("foot") == pets_foot and asked[0].get("orientation") == "landscape",
          ran_print.stderr[-400:] or json.dumps(printed)[:400])

    # ── H. a foot that never collides (Adam, 1 November 2026): the page's own script measures the parts in the foot's
    # type and, when the three would come closer than the clear gap, shortens the project with an ellipsis, nothing
    # else cut, and sets the middle centred between the left's end and the right's start. Run in node with a page whose
    # type is 2 px a character, an invented participant, project and name
    long_project = "Keeping bees on a city allotment through four winters of change, loss and starting again"
    fit_js = r"""
const made = [];
const probe = { style: {}, textContent: '', getBoundingClientRect() { return { width: [...this.textContent].length * 2 }; }, remove() {} };
const document = { body: { appendChild() {} }, head: { appendChild(s) { made.push(s.textContent); } },
  createElement(tag) { return tag === 'span' ? probe : { textContent: '', setAttribute() {} }; } };
const runs = /*RUNS*/;
const out = [];
for (const FOOT of runs) {
  made.length = 0;
  /*FIT*/
  out.push(made[0] || null);
}
process.stdout.write(JSON.stringify(out) + '\n');
"""
    feet_given = []
    for project in (long_project, "Bees"):
        pieces, fit = themes_print.foot_pieces("P7 Alder", project, i18n.t("page_print.pets.table_name"), board="Board 2")
        middle = "Bo Quill  ·  Confidential  ·  1 November 2026"
        said = json.loads(themes_print.foot_fit(pieces, fit, middle, themes_print.STYLE)
                          .split("const FOOT = ", 1)[1].split(";\n(function", 1)[0])
        # a line 400 px wide: room for the short project, not for the long one
        feet_given.append(dict(said, width=400 * 25.4 / 96, gap=6))
    ran_fit = support.run_node(fit_js.replace("/*RUNS*/", json.dumps(feet_given)).replace("/*FIT*/", themes_print.FOOT_FIT.strip()),
                               scratch / "a311", "a311-foot-fit.js")
    fitted = json.loads(ran_fit.stdout.strip().splitlines()[-1]) if ran_fit.returncode == 0 and ran_fit.stdout.strip() else [None, None]
    left_of = lambda css: (re.search(r'@bottom-left \{ content: "(.*)"; \}', css or "") or [None, ""])[1].replace("\\A0 ", "\u00a0")
    long_left, short_left = left_of(fitted[0]), left_of(fitted[1])
    cut_at = long_left.find("\u2026")
    kept = long_left[:cut_at].split("  ·  ")[-1] if cut_at > 0 else ""
    before_middle = lambda line: line.split("Bo Quill", 1)[0].rstrip("\u00a0")
    width = lambda s: len(s) * 2
    # the middle's start lies midway between the left part's end and where "Page 0 of 0" starts
    page_0 = width(i18n.t("page_print.page_of", page="0", pages="0"))
    centred = lambda line: abs((width(line.split("Bo Quill", 1)[0])) - (width(before_middle(line))
                               + (400 - page_0 - width(before_middle(line)) - width("Bo Quill  ·  Confidential  ·  1 November 2026")) / 2)) <= 2
    check("311: a foot too long for its line has its project shortened at a word with an ellipsis, the participant, the board, the "
          "table, the name, Confidential and the date whole, the middle set between the left and the right, and a short "
          "project left whole",
          cut_at > 0 and long_project.startswith(kept) and 0 < len(kept) < len(long_project) and long_project[len(kept)] in " ,;:."
          and long_left.startswith("P7 Alder (Board 2)  ·  ") and before_middle(long_left).endswith("\u2026  ·  Table of Personal Experiential Themes")
          and long_left.endswith("Bo Quill  ·  Confidential  ·  1 November 2026")
          and "@bottom-center { content: none; }" in (fitted[0] or "")
          and short_left.startswith("P7 Alder (Board 2)  ·  Bees  ·  Table of Personal Experiential Themes\u00a0")
          and "\u2026" not in short_left and centred(short_left) and centred(long_left),
          ran_fit.stderr[-400:] or f"{long_left!r} | {short_left!r}")
    pieces, fit = themes_print.foot_pieces("P7 Alder", long_project, "GET table", board="Board 2")
    gets_pieces, gets_fit = themes_print.foot_pieces(long_project, "", "GET table", board="Board 2", cut_case=True)
    marked = themes_print.page_foot(pieces, "Bo Quill", numbered=True, fit=fit)
    read_fit = support.run_node(window_js.split("(function () {\n  var win = window;", 1)[0]
                                + "\nprocess.stdout.write(JSON.stringify(idiographPageFoot(" + json.dumps(marked) + ")) + '\\n');\n",
                                scratch / "a311", "a311-foot-mark.js")
    mark_read = json.loads(read_fit.stdout.strip().splitlines()[-1]) if read_fit.returncode == 0 and read_fit.stdout.strip() else {}
    check("311: the piece to shorten is the project, the GETs' project where the participant stands, and the Mac's window "
          "reads which it is from the page's foot",
          pieces[fit] == long_project and gets_pieces[gets_fit] == long_project and gets_pieces[1] == " (Board 2)"
          and mark_read.get("fit") == fit and (mark_read.get("left") or [None] * 9)[fit] == long_project,
          read_fit.stderr[-300:] or json.dumps(mark_read)[:300])

    # ── D. the table typeset by Typst ending on a page with rows on it, never a page of the foot line alone
    import pdftext
    import typeset
    data = themes_print.typst_data(book, "Juno", None, DEMO_QUESTION)
    last = pdftext.pages_text(typeset.render(themes_print.TEMPLATE, data))[-1]
    rows = [s["text"] for t in data["themes"] for s in themes_word_rows(t)]
    check("311: Juno's table typeset ends on a page with rows on it, never a page of the foot line alone",
          any(support.squashed(r) in support.squashed(last) for r in rows), last[:200])


def themes_word_rows(theme: dict) -> list[dict]:
    """Every statement row under a block of the Typst data, at any depth."""
    out = []
    for it in theme["items"]:
        out += themes_word_rows(it) if it["kind"] == "theme" else [it]
    return out
