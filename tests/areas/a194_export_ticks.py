from __future__ import annotations

import json
import re
import shutil
import zipfile

from . import support
from .support import DEMO_QUESTION, check
import idiograph_routes


def test_export_ticks(scratch):
    print("\n194. The PETs table's export, the print view and Word, with two ticks, Include not placed and Include "
          "binned experiential statements, both off on a new install and his last choice kept (Adam, 18 October)")
    import mcp_server
    import server as server_mod
    import themes as themes_mod
    import themes_print
    import themes_word

    # the fixture: the demo's Rowan as an invented case of an invented project, its board with statements
    # not placed and one in the bin, and a settings file of its own with neither key
    pristine = support.DEMO_PRISTINE
    root = scratch / "ticks-root"
    shutil.rmtree(root, ignore_errors=True)
    folder = root / "P3 - Tansy"
    folder.mkdir(parents=True)
    book = folder / "P3 Tansy - EN & ES.xlsx"
    shutil.copy2(pristine / "Rowan - EN & ES.xlsx", book)
    held = json.loads((pristine / "Working" / "Rowan - EN & ES.themes.json").read_text(encoding="utf-8"))
    held["case"], held["workbook"] = "P3 - Tansy", book.name
    themes_mod.themes_path(book).parent.mkdir(parents=True, exist_ok=True)
    themes_mod.themes_path(book).write_text(json.dumps(held, ensure_ascii=False), encoding="utf-8")
    (root / "idiograph-project.json").write_text(json.dumps({"name": "Dogs, a ticks project",
                                                             "research_question": DEMO_QUESTION}), encoding="utf-8")
    cfg = scratch / "ticks-config.json"
    cfg.write_text(json.dumps({"projects": [{"root": str(root)}], "interviewer": "Adam"}), encoding="utf-8")
    board, _ = themes_word.board_of(book)
    np_head = f"Not placed ({len(board['unplaced'])})"
    dc_head = f"Experiential statements set aside ({len(board['discarded'])})"

    def printed(page: str) -> tuple[bool, bool]:
        return f"<h2>{np_head}</h2>" in page, f"<h2>{dc_head}</h2>" in page

    def worded(name: str) -> tuple[bool, bool]:
        with zipfile.ZipFile(folder / name) as z:
            text = " ".join(re.findall(r"<w:t[^>]*>([^<]*)</w:t>", z.read("word/document.xml").decode("utf-8")))
        return np_head in text, dc_head in text

    kept = (server_mod.CONFIG_PATH, server_mod.ROOT_OVERRIDE, server_mod.STATE_MEMORY)
    try:
        server_mod.CONFIG_PATH, server_mod.ROOT_OVERRIDE = cfg, str(root)
        server_mod.STATE_MEMORY = {"recent": []}

        def shown(query: dict | None = None, body: dict | None = None) -> tuple:
            code, page = idiograph_routes.themes_print_page(dict({"workbook": str(book), "auto": "0"}, **(query or {})))
            word = idiograph_routes.api_themes_export(dict({"workbook": str(book), "op": "word"}, **(body or {})))
            return code, printed(page), worded(str(word["word"]).replace("\\", "/").rsplit("/", 1)[-1]), page

        # the default: a new install's settings, and a file with neither key, leave both parts out
        fresh = server_mod.merge_config({})
        first = shown()
        check("194: both ticks off on a new install, and the print view and the Word document hold the PETs alone, "
              "with no Not placed or Binned experiential statements heading and no empty part at the end",
              board["unplaced"] and board["discarded"] and fresh["export_not_placed"] is False
              and fresh["export_binned"] is False and first[:3] == (200, (False, False), (False, False))
              and '<section class="rest">' not in first[3], str(first[:3]))

        # each tick on alone, then both, as the print view's query and the Word export's body send them
        alone_np = shown({"unplaced": "1", "binned": "0"}, {"unplaced": True, "binned": False})
        alone_dc = shown({"unplaced": "0", "binned": "1"}, {"unplaced": False, "binned": True})
        both = shown({"unplaced": "1", "binned": "1"}, {"unplaced": True, "binned": True})
        check("194: Include not placed alone puts Not placed at the end of the print view and the Word document, "
              "and the bin stays out", alone_np[1:3] == ((True, False), (True, False)), str(alone_np[1:3]))
        check("194: Include binned experiential statements alone puts the bin, under Binned experiential statements, at the end of both, "
              "and Not placed stays out",
              alone_dc[1:3] == ((False, True), (False, True)), str(alone_dc[1:3]))
        check("194: both ticks on put both parts at the end of both, Not placed then the bin",
              both[1:3] == ((True, True), (True, True))
              and both[3].index(f"<h2>{np_head}</h2>") < both[3].index(f"<h2>{dc_head}</h2>"), str(both[1:3]))

        # the choice kept: a tick saved from Export or the print view lands in the settings file, every
        # other key kept, and an export that names neither follows it, after a restart too
        server_mod.api_settings({"export_not_placed": True})
        saved = json.loads(cfg.read_text(encoding="utf-8"))
        after = shown()
        restarted = server_mod.merge_config(json.loads(cfg.read_text(encoding="utf-8")))
        check("194: a tick saved is kept in the settings file, the interviewer kept beside it, and the next print "
              "and Word export follow it with nothing said, as they do after a restart",
              saved.get("export_not_placed") is True and saved.get("export_binned") is False
              and saved.get("interviewer") == "Adam" and after[1:3] == ((True, False), (True, False))
              and restarted["export_not_placed"] is True and restarted["export_binned"] is False, str(after[1:3]))
        server_mod.api_settings({"export_not_placed": False, "export_binned": True})
        swapped = shown()
        server_mod.api_settings({"export_binned": False})
        off = shown()
        check("194: ticked the other way and then off again, the exports follow each time",
              swapped[1:3] == ((False, True), (False, True)) and off[1:3] == ((False, False), (False, False)),
              f"{swapped[1:3]} {off[1:3]}")

        # the print view's two ticks, drawn as the page is, each a row inside its label
        on_page = both[3]
        boxes = {box: re.search(rf'<label class="tick"><input type="checkbox" id="{box}"( checked)?> ([^<]+)</label>',
                                on_page) for box in ("include-unplaced", "include-binned")}
        plain_page = off[3]
        check("194: the print view carries the two ticks, each toggling from its whole row, ticked as the page "
              "is drawn and unticked on a page drawn without them",
              all(boxes.values()) and all(m.group(1) for m in boxes.values())
              and 'id="include-unplaced" checked' not in plain_page and 'id="include-binned" checked' not in plain_page
              and [m.group(2) for m in boxes.values()] == ["Include not placed", "Include statements set aside"])
    finally:
        server_mod.CONFIG_PATH, server_mod.ROOT_OVERRIDE, server_mod.STATE_MEMORY = kept

    # the print view's script: a tick saves to its key and draws the page again by its query, in node
    script = ("const saved = []; const replaced = [];\n"
              "const boxes = {};\n"
              "const document = { getElementById: (id) => (boxes[id] = boxes[id] || { id, checked: false }), fonts: null };\n"
              "global.fetch = async (url, opts) => { saved.push([url, JSON.parse(opts.body)]); return {}; };\n"
              "global.window = { location: { href: 'http://127.0.0.1:8787/themes/print?workbook=x&board=v1', "
              "replace: (u) => replaced.push(u) }, print: () => {} };\n"
              "const AUTO = false;\n"
              f"const INCLUDES = {json.dumps([[b, k, q] for b, k, q in themes_print.INCLUDES])};\n"
              + themes_print.SCRIPT +
              "\n(async () => { boxes['include-binned'].checked = true; await boxes['include-binned'].onchange();\n"
              "boxes['include-unplaced'].checked = false; await boxes['include-unplaced'].onchange();\n"
              "console.log(JSON.stringify({ saved, replaced })); })();\n")
    run = support.run_node(script, scratch, "print-ticks-194.js", timeout=60)
    try:
        out = json.loads(run.stdout.strip().splitlines()[-1])
    except (ValueError, IndexError):
        out = {}
    check("194: in node, a tick on the print view saves its choice to its own key in the settings and draws the "
          "page again by its query with the dialog shut",
          out.get("saved") == [["/api/settings", {"export_binned": True}], ["/api/settings", {"export_not_placed": False}]]
          and "binned=1" in out["replaced"][0] and "auto=0" in out["replaced"][0]
          and "unplaced=0" in out["replaced"][1], (run.stdout + run.stderr)[:400])

    # the PETs screen's Export menu: the same two ticks, each a row inside its label, sent with Table and Word
    page_src = support.page_text()
    js = support.text("apps/idiograph/static/themes.js")
    menu = page_src.split('id="th-xmenu"', 1)[1].split('<div class="th-body">', 1)[0]
    rows = re.findall(r'<label class="view-row"(?: title="[^"]*")?><input type="checkbox" id="[^"]+" data-include="([^"]+)"> ([^<]+)</label>', menu)
    check("194: Export on the PETs screen carries the two ticks, each a whole row inside its label, saving to the "
          "keys the print view and the server read",
          [r for r in rows if r[0] in ("export_not_placed", "export_binned")] == [("export_not_placed", "Include not placed"), ("export_binned", "Include statements set aside")]
          and all(k in server_mod.defaults() for k, _ in rows), str(rows))
    fn = lambda name: js.split(f"function {name}(", 1)[1].split("\n}", 1)[0]
    script = ("let TH = { config: { export_not_placed: true } };\n"
              + "const TH_INCLUDES" + js.split("const TH_INCLUDES", 1)[1].split(";\n", 1)[0] + ";\n"
              + "const thIncluded = (key) => !!(TH.config && TH.config[key]);\n"
              + "function thIncludesSent(asQuery) {" + fn("thIncludesSent").split("{", 1)[1] + "\n}\n"
              + "const a = [thIncludesSent(true), thIncludesSent(false)];\n"
              + "TH.config = null; a.push(thIncludesSent(false));\n"
              + "console.log(JSON.stringify(a));\n")
    run = support.run_node(script, scratch, "includes-sent-194.js", timeout=60)
    try:
        sent = json.loads(run.stdout.strip().splitlines()[-1])
    except (ValueError, IndexError):
        sent = []
    check("194: in node, Table sends the ticks in its query and Word in its body as the settings hold them, both "
          "off when the screen has no settings yet",
          [{k: x[k] for k in ("unplaced", "binned", "sending")} for x in sent] == [
              {"unplaced": "1", "binned": "0", "sending": "0"}, {"unplaced": True, "binned": False, "sending": False},
              {"unplaced": False, "binned": False, "sending": False}]
          and "thIncludesSent(true)" in fn("thPrint") and "thIncludesSent(false)" in fn("thExport"),
          (run.stdout + run.stderr)[:400])

    # the command line and MCP: both parts out unless asked for
    plain = themes_word.plain(themes_word.blocks("P3 - Tansy", board))
    asked = themes_word.plain(themes_word.blocks("P3 - Tansy", board, unplaced=True, binned=True))
    t = next(x for x in mcp_server.TOOLS if x["name"] == "board_export")
    bare = mcp_server.arguments(t, {"case": "P3 - Tansy"}, {"project": None}, "test")
    full = mcp_server.arguments(t, {"case": "P3 - Tansy", "not_placed": True, "binned": True}, {"project": None}, "test")
    check("194: the Word document leaves both parts out unless asked, and board export over MCP takes not_placed "
          "and binned, both off when left out",
          np_head not in plain and dc_head not in plain and np_head in asked and dc_head in asked
          and (bare.not_placed, bare.binned, full.not_placed, full.binned) == (False, False, True, True))
