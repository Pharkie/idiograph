"""287. The print views on landscape A4 in the window (printland, 28 October 2026).

A Mac's print panel takes its page from the print info alone, never from a page's own @page size, so
the window reads that size from the page (window.js, idiographPagePaper) and hands it to its print,
which opens the panel on it (main.rs, print). Checked here, on the demo's invented cases in a scratch
root and in node: every print view, the table of PETs, the GET table, the audit trail, the full set and
the canvas, carries an @page size the window reads as landscape, A4 for the server's views, the app's
own page none, so its print stays as it was, and a page asking for portrait or another paper is read
as asking for it, a margin box's own size never taken for the page's.
"""
from __future__ import annotations

import json
import re
import shutil
from pathlib import Path

from . import support
from .support import check


def test_print_landscape(scratch: Path):
    print("\n287. The print views on landscape A4 in the window: the page's own @page size read for the print panel")
    import server as server_mod
    import idiograph_routes

    root = scratch / "print-landscape"
    shutil.rmtree(root, ignore_errors=True)
    pristine = support.DEMO_PRISTINE
    for name in ("Juno", "Rowan", "Mabel"):
        (root / name / "Working").mkdir(parents=True)
        shutil.copy2(pristine / f"{name} - EN & ES.xlsx", root / name / f"{name} - EN & ES.xlsx")
        for side in sorted((pristine / "Working").glob(f"{name} - *")):
            shutil.copy2(side, root / name / "Working" / side.name)
    shutil.copy2(support.source("demo/idiograph-project.json"), root / "idiograph-project.json")
    saved = (server_mod.ROOT_OVERRIDE, server_mod.STATE_PATH, server_mod.STATE_MEMORY)
    server_mod.ROOT_OVERRIDE = str(root)
    server_mod.STATE_MEMORY = {"recent": []}
    pages: dict = {}
    try:
        book = root / "Rowan" / "Rowan - EN & ES.xlsx"
        pages["table of PETs"] = idiograph_routes.themes_print_page({"workbook": str(book), "auto": "0"})
        for what, called in (("table", "GET table"), ("trail", "audit trail"), ("all", "full set")):
            pages[called] = idiograph_routes.gets_print_page({"root": str(root), "what": what, "detail": "full", "auto": "0"})
    finally:
        server_mod.ROOT_OVERRIDE, server_mod.STATE_PATH, server_mod.STATE_MEMORY = saved

    def styles(html: str) -> str:
        return "\n".join(re.findall(r"<style[^>]*>(.*?)</style>", html, flags=re.S))

    css = {name: styles(html) for name, (code, html) in pages.items() if code == 200}
    # the canvas's page is written by the page's own script, its style the template in thCanvasPage
    themes_js = support.text("apps/idiograph/static/themes.js")
    canvas = themes_js.split("function thCanvasPage(", 1)[1].split("const style = `", 1)[1].split("`;", 1)[0]
    css["canvas"] = canvas
    css["app page"] = "\n".join([styles(support.page_text()), support.text("family/static/style.css")])
    invented = {
        "portrait A4": "@page { size: A4; margin: 10mm }",
        "letter portrait": "@page { margin: 1in; size: letter portrait }",
        "margin box only": '@page { margin: 10mm; @bottom-left { content: "x"; font-size: 8pt } }',
        "last wins": "@page { size: A4 portrait } @media print { @page { size: A4 landscape } }",
        "commented": "/* @page { size: A4 landscape } */ @page { size: auto }",
    }
    css.update(invented)
    # a page with no window's bridge, where the file's own part does nothing and its reader stays
    script = ("var window = {};\n" + support.text("packaging/tauri/window.js")
              + "\nvar CSS = " + json.dumps(css) + ";\nvar out = {};\n"
              + "for (var k in CSS) out[k] = idiographPagePaper(CSS[k]);\n"
              + "console.log(JSON.stringify(out));\n")
    done = support.run_node(script, scratch, "a287-paper.js")
    read = json.loads(done.stdout.strip().splitlines()[-1]) if done.returncode == 0 and done.stdout.strip() else {}

    landscape_a4 = {"orientation": "landscape", "paper": "a4"}
    views = ("table of PETs", "GET table", "audit trail", "full set")
    check("287: every server print view answers and carries an @page size, read by the window as landscape A4",
          len(css) == len(views) + 2 + len(invented) and all(read.get(v) == landscape_a4 for v in views),
          json.dumps({v: read.get(v) for v in views}) + done.stderr[-300:])
    check("287: the canvas's print asks for landscape on the person's own paper, read as landscape with no paper",
          read.get("canvas") == {"orientation": "landscape", "paper": None}, json.dumps(read.get("canvas")))
    check("287: the app's own page says no size, so its print opens the panel as before",
          read.get("app page") == {}, json.dumps(read.get("app page")))
    check("287: portrait stays for a page that asks for it, a named paper alone portrait, the last rule winning, "
          "a margin box's size and a comment never taken",
          read.get("portrait A4") == {"orientation": "portrait", "paper": "a4"}
          and read.get("letter portrait") == {"orientation": "portrait", "paper": "letter"}
          and read.get("margin box only") == {} and read.get("last wins") == landscape_a4
          and read.get("commented") == {}, json.dumps({k: read.get(k) for k in invented}))

    # the window hands what it read to its print, which a Mac sets on the panel's print info
    window_js = support.text("packaging/tauri/window.js")
    main_rs = support.text("packaging/tauri/src-tauri/src/main.rs")
    printer = window_js.split("var printer = function (target) {", 1)[1].split("\n  };", 1)[0]
    command = main_rs.split("fn print(window: tauri::WebviewWindow", 1)[1].split("\n}\n", 1)[0]
    check("287: the page's paper goes with its Print to the window, which sets it on a Mac's print panel",
          "idiographPagePaper(" in printer and "asked.orientation" in printer and "asked.paper" in printer
          and "orientation: Option<String>" in command and "mac::print(" in command
          and "setOrientation:" in main_rs and "setPaperSize:" in main_rs)
