from __future__ import annotations

import json
import re
import shutil

from . import support
from .support import DEMO_QUESTION, check, skip
import idiograph_routes


def test_send_tick(scratch):
    print("\n200. For sending, a tick beside the PETs table's export's other two: the PDF and the Word document named "
          "by the case alone and no board's name on the page, his last choice kept, the GETs print the same, and "
          "board export --pdf on the command line and in the MCP server (Adam, 19 October)")
    import cli
    import mcp_server
    import print_pdf
    import server as server_mod
    import themes as themes_mod
    import themes_word

    # the fixture: the demo's three cases in an invented project, Rowan's as P3 - Tansy, with agents allowed,
    # and a settings file of its own with none of the export's keys
    pristine = support.DEMO_PRISTINE
    root = scratch / "send-root"
    shutil.rmtree(root, ignore_errors=True)
    for name, case in (("Rowan", "P3 - Tansy"), ("Juno", "P4 - Wick"), ("Mabel", "P5 - Quince")):
        folder = root / case
        (folder / "Working").mkdir(parents=True)
        book = folder / f"{case.replace(' -', '')} - EN & ES.xlsx"
        shutil.copy2(pristine / f"{name} - EN & ES.xlsx", book)
        held = pristine / "Working" / f"{name} - EN & ES.themes.json"
        if held.exists():
            data = json.loads(held.read_text(encoding="utf-8"))
            data["case"], data["workbook"] = case, book.name
            themes_mod.themes_path(book).write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
    (root / server_mod.PROJECT_FILE).write_text(json.dumps({
        "name": "Dogs, a sending project", "research_question": DEMO_QUESTION,
        "agents": {"allowed": True, "at": "2026-10-19T10:00:00+01:00"}}), encoding="utf-8")
    cfg = scratch / "send-config.json"
    cfg.write_text(json.dumps({"projects": [{"root": str(root)}], "interviewer": "Adam"}), encoding="utf-8")
    folder = root / "P3 - Tansy"
    book = folder / "P3 Tansy - EN & ES.xlsx"
    board, version = themes_word.board_of(book)
    name = version["name"]
    np_head = f"Not placed ({len(board['unplaced'])})"
    dc_head = f"Experiential statements set aside ({len(board['discarded'])})"

    def title(page: str) -> str:
        found = re.search(r"<title>([^<]*)</title>", page)
        return found.group(1) if found else ""

    def bare_page(page: str) -> bool:
        """No board's name and no Current board anywhere on the page, the foot kept."""
        head = page.split("<main>", 1)[0]
        return ('class="board"' not in head and "Current board" not in head and f"on {name}" not in head
                and "@bottom-left { content: " in page)

    kept = (server_mod.CONFIG_PATH, server_mod.ROOT_OVERRIDE, server_mod.STATE_MEMORY)
    try:
        server_mod.CONFIG_PATH, server_mod.ROOT_OVERRIDE = cfg, str(root)
        server_mod.STATE_MEMORY = {"recent": []}

        def shown(query: dict | None = None, body: dict | None = None) -> tuple:
            code, page = idiograph_routes.themes_print_page(dict({"workbook": str(book), "auto": "0"}, **(query or {})))
            word = idiograph_routes.api_themes_export(dict({"workbook": str(book), "op": "word"}, **(body or {})))
            return code, page, str(word["word"]).replace("\\", "/").rsplit("/", 1)[-1]

        # off, as on a new install: the board named on the page, in its title and in the Word document's name
        fresh = server_mod.merge_config({})
        code, page, word = shown()
        check("200: For sending is off on a new install, and the print view and Word name the board as before",
              fresh["export_for_sending"] is False and code == 200 and title(page) == f"P3 - Tansy - {name} - PETs"
              and f"P3 Tansy ({name})" in page
              and word == f"P3 Tansy - PETs ({name}).docx", f"{title(page)} {word}")

        # on: the case alone, no board on the page, the foot kept, and a second Word file never over the first
        code, page, word = shown({"sending": "1"}, {"sending": True})
        first = (folder / word).read_bytes()
        _, _, again = shown({"sending": "1"}, {"sending": True})
        check("200: with For sending the print view's title, which names the PDF, is the case alone, the page carries "
              "no board's name and no Current board, the foot stays, and Word is named by the case alone",
              code == 200 and title(page) == "P3 - Tansy" and bare_page(page) and word == "P3 - Tansy.docx",
              f"{title(page)} {word}")
        check("200: a second Word file for sending takes the date and time in its name and leaves the first as it was",
              again.startswith("P3 - Tansy (") and again.endswith(").docx") and (folder / word).read_bytes() == first,
              again)

        # his last choice kept: saved in the settings, the next exports follow it with nothing said
        server_mod.api_settings({"export_for_sending": True})
        saved = json.loads(cfg.read_text(encoding="utf-8"))
        _, page_on, word_on = shown()
        server_mod.api_settings({"export_for_sending": False})
        _, page_off, _ = shown()
        check("200: For sending ticked is kept in the settings file, the next print view and Word follow it, and off "
              "again they name the board",
              saved.get("export_for_sending") is True and saved.get("interviewer") == "Adam"
              and title(page_on) == "P3 - Tansy" and word_on.startswith("P3 - Tansy")
              and title(page_off) == f"P3 - Tansy - {name} - PETs", f"{title(page_on)} {word_on} {title(page_off)}")
        check("200: the print view carries Leave out the board's name beside its other ticks, ticked as the page is drawn",
              re.search(r"<label class=.tick.><input type=.checkbox. id=.for-sending. checked> Leave out the board(?:'|&#x27;|&#39;)s name</label>", page_on)
              and 'id="for-sending" checked' not in page_off)

        # the GETs print: the board named without, unnamed with
        gets_off = idiograph_routes.gets_print_page({"root": str(root), "auto": "0", "what": "all", "sending": "0"})
        gets_on = idiograph_routes.gets_print_page({"root": str(root), "auto": "0", "what": "all", "sending": "1"})
        check("200: the GETs print for sending names no board in its head, its PET tables or its title",
              gets_off[0] == gets_on[0] == 200 and "Board" in title(gets_off[1])
              and title(gets_on[1]) == "Dogs, a sending project - GETs"
              and 'class="board"' not in gets_on[1].split("<footer>", 1)[0] and 'class="board"' in gets_off[1]
              and "@bottom-left { content: " in gets_on[1], f"{title(gets_off[1])} | {title(gets_on[1])}")
    finally:
        server_mod.CONFIG_PATH, server_mod.ROOT_OVERRIDE, server_mod.STATE_MEMORY = kept

    # the command line's PDF, with each option, each typeset by Typst and its words kept (typst5)
    printed: list[str] = []
    sq = support.squashed

    def bare_text(text: str) -> bool:
        """No board's name and no Current board anywhere in the PDF's words."""
        return sq(name) not in text and sq("Current board") not in text

    def run(*args):
        return cli.run(["--root", str(root), "--config", str(cfg), *args, "--json"])

    def answer(*args):
        code, out, err = run(*args)
        return code, (support.plain(json.loads(out)) if out.strip() else {}), err

    for old in folder.glob("*.pdf"):
        old.unlink()
    try:
        real_typeset, print_pdf.typeset_pdf = support.typeset_words(printed)
        c1, plain, _ = answer("board", "export", "P3 - Tansy", "--pdf")
        c2, with_np, _ = answer("board", "export", "P3 - Tansy", "--pdf", "--not-placed")
        c3, with_dc, _ = answer("board", "export", "P3 - Tansy", "--pdf", "--binned")
        check("200: board export --pdf writes the print view's page as a PDF beside the workbook, named as the print "
              "view names it, Not placed and the bin out unless asked for, and a second one never over the first",
              (c1, c2, c3) == (0, 0, 0) and plain["file"] == f"P3 - Tansy - {name} - PETs.pdf" and plain["format"] == "pdf"
              and (folder / plain["file"]).read_bytes().startswith(b"%PDF-")
              and sq(np_head) not in printed[0] and sq(dc_head) not in printed[0]
              and sq(np_head) in printed[1] and sq(dc_head) not in printed[1] and sq(dc_head) in printed[2]
              and with_np["dated"] and with_np["file"] != plain["file"], json.dumps([plain, with_np])[:400])
        c4, sent, _ = answer("board", "export", "P3 - Tansy", "--pdf", "--for-sending")
        c5, dry, _ = answer("board", "export", "P3 - Tansy", "--pdf", "--for-sending", "--replace", "--dry-run")
        count = len(printed)
        c6, replaced, _ = answer("board", "export", "P3 - Tansy", "--pdf", "--for-sending", "--replace")
        check("200: --for-sending names the PDF by the case alone with no board on its page, and --replace writes over "
              "that one name, the dry run printing and writing nothing",
              (c4, c5, c6) == (0, 0, 0) and sent["file"] == "P3 - Tansy.pdf" and sent["for_sending"] is True
              and bare_text(printed[3]) and dry["dry_run"] is True and count == 4 and len(printed) == 5
              and replaced["file"] == "P3 - Tansy.pdf" and replaced["replaced"] is True
              and (folder / "P3 - Tansy.pdf").read_bytes().startswith(b"%PDF-")
              and not list(folder.glob(".*.part")), json.dumps([sent, replaced])[:400])
        c7, out7, err7 = run("board", "export", "P3 - Tansy", "--word", "--replace")
        c8, out8, err8 = run("board", "export", "P3 - Tansy")
        err7, err8 = out7 + err7, out8 + err8
        check("200: --replace is refused with --word, and an export naming neither --word nor --pdf is refused",
              c7 != 0 and "--replace" in err7 and c8 != 0 and "--pdf" in err8, err7 + err8)

        # the same through MCP
        srv = mcp_server.Server(str(root), config=str(cfg))
        srv.receive(json.dumps({"jsonrpc": "2.0", "id": 1, "method": "initialize",
                                "params": {"protocolVersion": "2025-06-18", "clientInfo": {"name": "claude-code"}}}))
        res = srv.receive(json.dumps({"jsonrpc": "2.0", "id": 2, "method": "tools/call", "params": {
            "name": "board_export", "arguments": {"case": "P3 - Tansy", "format": "pdf", "for_sending": True,
                                                  "replace": True, "binned": True}}}))["result"]
        word = srv.receive(json.dumps({"jsonrpc": "2.0", "id": 3, "method": "tools/call", "params": {
            "name": "board_export", "arguments": {"case": "P3 - Tansy", "for_sending": True}}}))["result"]
        check("200: through MCP board_export takes format pdf, for_sending and replace, and Word stays its default",
              not res["isError"] and support.plain(res["structuredContent"])["file"] == "P3 - Tansy.pdf"
              and sq(dc_head) in printed[-1] and bare_text(printed[-1])
              and not word["isError"] and support.plain(word["structuredContent"])["format"] == "word"
              and support.plain(word["structuredContent"])["file"].startswith("P3 - Tansy"), json.dumps(res)[:300])
    finally:
        print_pdf.typeset_pdf = real_typeset

