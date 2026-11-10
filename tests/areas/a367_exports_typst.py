"""Area 367: every export through Typst, the old routes gone (typst5, 9 November 2026, Adam, 9 November about 18:10:
Typst for every PDF and picture, "it should work or error", no fallback). Export as PDF of the table of PETs and of
each GETs view, the full set, the canvas's PDF and Save as an image, from the API the window and a browser's tab
call, and the command line's and MCP's exports, each made by `typeset.render` and written where it went before, under
the same name. A failing engine answers the catalogue's plain sentence and writes nothing. No route reaches a browser
or the window's print-to-file: `print_pdf.browser`, the held canvas page, the agents' headless browser, Linux's
`/api/page-file` and the window's `save_pdf`, `save_png` and `picture_page` are gone. On the demo's three invented
participants and an invented project of three timepoints, every word made up."""
from __future__ import annotations

import base64
import json
import re
import shutil
from pathlib import Path

from . import support
from .support import check, skip

# an invented study of three timepoints: Kit asks newcomers to a choir about their first year in it
WREN_T1 = ("Kit: [00:00:03] What did you expect of the choir?\nWren: [00:00:08] Scales, and being told off for "
           "singing flat.\nKit: [00:00:40] And the first concert?\nWren: [00:03:55] I mouthed the words at the back.\n")
WREN_T2 = "Kit: [00:00:02] How is it now?\nWren: [00:00:06] I ask the altos before I ask the score.\n"
ASH_T1 = "Kit: [00:00:03] Why a choir?\nAsh: [00:00:09] To sing what my grandmother sang.\n"
ASH_T2 = "Kit: [00:00:03] And now?\nAsh: [00:00:07] The solo went wrong and the tenors carried me.\n"
THREE = [{"label": "T1", "description": "Before the season"}, {"label": "T2", "description": "Midwinter"},
         {"label": "T3", "description": "After the summer concert"}]


def squash(text: str) -> str:
    return re.sub(r"\s+", "", str(text)).casefold()


def files(at: Path) -> dict:
    """Every file under a folder and its bytes, the lock files aside."""
    return {p.relative_to(at).as_posix(): p.read_bytes() for p in sorted(at.rglob("*"))
            if p.is_file() and not p.name.endswith(".lock") and not p.name.startswith(".")}


def a4_landscape(pdf: bytes) -> bool:
    """Whether the PDF's first page is A4 turned on its side, 842 by 595 points, give or take a point."""
    found = re.search(rb"/MediaBox\s*\[\s*0\s+0\s+([\d.]+)\s+([\d.]+)\s*\]", pdf)
    return bool(found) and abs(float(found.group(1)) - 841.89) < 2 and abs(float(found.group(2)) - 595.28) < 2


def test_exports_typst(scratch: Path):
    print("\n367. Every export through Typst: the table of PETs, the GETs views and the full set, the canvas's PDF and "
          "picture, from the API, the command line and MCP, a failing engine's plain sentence, the old routes gone")
    import i18n
    import idiograph_routes as routes
    import pdftext
    import server as srv
    from workbook import WorkbookError
    try:
        import typeset
    except ImportError:
        skip("367: the exports through Typst", "family/typeset.py is not here")
        return
    if not typeset.available():
        skip("367: the exports through Typst", "typst-py is not installed")
        return
    import canvas_out
    import cli
    import gets as gets_mod
    import mcp_server
    import print_pdf
    import themes as themes_mod

    # ── A. the old routes gone
    tauri = support.source("packaging/tauri")
    main_rs = (tauri / "src-tauri" / "src" / "main.rs").read_text(encoding="utf-8")
    build_rs = (tauri / "src-tauri" / "build.rs").read_text(encoding="utf-8")
    caps = (tauri / "src-tauri" / "capabilities" / "page.json").read_text(encoding="utf-8")
    window_js = (tauri / "window.js").read_text(encoding="utf-8")
    themes_js = support.text("apps/idiograph/static/themes.js")
    shell_js = support.text("family/static/shell.js")
    gone_py = [n for n in ("browser", "render", "margins_of", "MAC_APPS") if hasattr(print_pdf, n)]
    gone_py += [n for n in ("browser_page", "Cdp", "agent_shot", "shoot_held", "save_page", "hold", "held", "page_view",
                            "PAGE_PATH", "server_command") if hasattr(canvas_out, n)]
    check("367: no route reaches a browser: print_pdf's browser and render, canvas_out's headless browser, its held "
          "page and the agents' shot, and the server's /api/page-file and /themes/canvas are gone",
          not gone_py and "/api/page-file" not in srv.ROUTES and not hasattr(routes, "api_page_file")
          and "/themes/canvas" not in str(getattr(srv, "GET_PATHS", {})), str(gone_py))
    check("367: the window prints nothing to a file and pictures no page: save_pdf, save_png, print_to_pdf and "
          "picture_page gone from main.rs, its commands from build.rs and the capability, idiographSavePdf, "
          "idiographSavePng and idiographByServer from window.js, and the page asks the server alone",
          not re.search(r"fn (save_pdf|save_png|print_to_pdf|picture_page)\b|PrintToPdf|PNG_SCALE|PNG_SIZE_JS", main_rs)
          and "save_pdf" not in build_rs.split("fn main()", 1)[1] and "save-pdf" not in caps and "save-png" not in caps
          and not re.search(r"idiographSave(Pdf|Png)|idiographByServer", window_js + themes_js)
          and "/api/page-file" not in themes_js and "thWindowSave" not in themes_js
          and "__idiographShot" not in themes_js + shell_js
          # Print on paper stays the window's
          and "fn print(" in main_rs and "mac::print(" in main_rs and "drawPageBorderWithSize" in main_rs)

    kept = (srv.CONFIG_PATH, srv.ROOT_OVERRIDE, srv.STATE_PATH, srv.STATE_MEMORY)
    real_render = typeset.render
    rendered: list[tuple[str, str]] = []

    def counting(template, data, **how):
        rendered.append((Path(template).name, how.get("fmt", "pdf")))
        return real_render(template, data, **how)

    def call(route: str, body: dict) -> dict:
        with routes.route_scope(route, body):
            return srv.ROUTES[route](body)

    def refused(route: str, body: dict) -> str:
        try:
            call(route, body)
        except WorkbookError as exc:
            return str(exc)
        return "answered"

    try:
        typeset.render = counting
        cfg = scratch / "a367-config.json"
        cfg.write_text(json.dumps({"projects": [], "interviewer": "Kit", "corpus": "", "gravity_reference": "",
                                   "corpus_exclude": [], "your_name": "A. Researcher"}), encoding="utf-8")
        srv.CONFIG_PATH, srv.STATE_PATH, srv.STATE_MEMORY = cfg, scratch / "a367-state.json", {"recent": []}

        # the demo's three participants in a project of their own
        root = scratch / "a367" / "demo"
        shutil.rmtree(root, ignore_errors=True)
        src = support.DEMO_SHIPPED
        for name in ("Juno", "Mabel", "Rowan"):
            (root / name / "Working").mkdir(parents=True)
            shutil.copy2(src / f"{name} - EN & ES.xlsx", root / name / f"{name} - EN & ES.xlsx")
            for side in sorted((src / "Working").glob(f"{name} - *")):
                shutil.copy2(side, root / name / "Working" / side.name)
        (root / srv.PROJECT_FILE).write_text(json.dumps({"name": "Dogs at home, an invented study",
                                                         "research_question": support.DEMO_QUESTION,
                                                         "agents": {"allowed": True, "at": "2026-11-09T20:00:00+00:00"}}),
                                             encoding="utf-8")
        srv.ROOT_OVERRIDE = str(root)
        book = root / "Juno" / "Juno - EN & ES.xlsx"
        bid = themes_mod.load(book)["boards"][0]["id"]
        case_before = files(root / "Juno" / "Working")

        # ── B. the table of PETs from the API, as Export as PDF asks for it
        rendered.clear()
        made = call("/api/themes-export", {"workbook": str(book), "version": bid, "op": "pdf", "unplaced": True})
        pdf = (root / "Juno" / made["name"]).read_bytes()
        pages = pdftext.pages_text(pdf)
        again = call("/api/themes-export", {"workbook": str(book), "version": bid, "op": "pdf"})
        check("367: Export as PDF of the table of PETs: the server writes it beside the workbook through Typst, named as "
              "the print view names it, landscape A4, the participant, the board, Not placed as ticked and the "
              "researcher in its text, a second one dated beside it",
              made["name"] == "Juno - Board 1 - PETs.pdf" and made["shown"] == [made["name"]] and pdf[:5] == b"%PDF-"
              and rendered[0] == ("pets_table_main.typ", "pdf") and a4_landscape(pdf) and len(pages) >= 2
              and squash("Juno") in squash(pages[0]) and squash("Not placed") in squash(" ".join(pages))
              and squash("A. Researcher") in squash(pages[0]) and again["dated"] is True
              and again["name"] != made["name"] and (root / "Juno" / again["name"]).is_file()
              and "margins" not in made, json.dumps([made, again])[:400])
        before = files(root)
        dry = call("/api/themes-export", {"workbook": str(book), "version": bid, "op": "pdf", "dry_run": True})
        check("367: its dry run names the file and makes and writes nothing, and the board's files are only read",
              dry.get("dry_run") is True and files(root) == before and files(root / "Juno" / "Working") == case_before)

        # ── C. the canvas's PDF and picture from the API, as the canvas's Save as PDF and Save as an image ask
        rendered.clear()
        cpdf = call("/api/themes-export", {"workbook": str(book), "version": bid, "op": "canvas", "kind": "pdf"})
        cpng = call("/api/themes-export", {"workbook": str(book), "version": bid, "op": "canvas", "kind": "png",
                                           "quotes": "full"})
        pdf_c = (root / "Juno" / cpdf["name"]).read_bytes()
        png_c = (root / "Juno" / cpng["name"]).read_bytes()
        w, h = canvas_out.png_size(png_c)
        check("367: the canvas's Save as PDF and Save as an image: drawn by Typst from the board, one landscape A4 page "
              "and a PNG twice the board's size, beside the workbook named as the table with canvas after it",
              cpdf["name"] == "Juno - Board 1 - PETs canvas.pdf" and cpng["name"] == "Juno - Board 1 - PETs canvas.png"
              and [r[0] for r in rendered] == ["canvas-main.typ", "canvas-main.typ"] and a4_landscape(pdf_c)
              and len(pdftext.pages_text(pdf_c)) == 1 and w > 1000 and h > 500 and cpng.get("pixels") == [w, h],
              json.dumps([cpdf, cpng])[:400])
        check("367: Quotes on cards goes as the canvas shows it: the picture with quotes taller than without",
              h > canvas_out.png_size(canvas_out.typeset_canvas(canvas_out.pets_data(book, "Juno", bid), "png"))[1],
              str((w, h)))

        # ── D. the GETs, the full set and the GETs canvas
        books = sorted(routes.gets_books(root), key=lambda b: gets_mod.case_order(b["case"]))
        data_g, _, _, _ = gets_mod.assemble(root, books, themes_mod.now_iso())
        gets_mod.write(root, gets_mod._file(data_g, themes_mod.now_iso()))
        cards = list(data_g["boards"][0]["cards"])
        g = data_g["boards"][0]
        rowan = [k for k in cards if k.startswith("Rowan/")]
        mabel = [k for k in cards if k.startswith("Mabel/")]
        juno = [k for k in cards if k.startswith("Juno/")]
        saved = call("/api/gets", {"root": str(root)})
        version = dict(saved["version"], cards={c["key"]: {"x": c["x"], "y": c["y"]} for c in saved["cards"]},
                       groups=[{"id": "G1", "label": "Walks at the edges of the day", "members": [rowan[0], mabel[0], juno[0]],
                                "x": 0, "y": -60},
                               {"id": "G2", "label": "Letting a dog go", "members": [rowan[1], mabel[1]], "x": 900, "y": -60}],
                       discarded=[], picks={}, notes=[])
        call("/api/gets-save", {"root": str(root), "version": version})
        gid = g["id"]
        rendered.clear()
        answers = {what: call("/api/gets-boards", {"root": str(root), "board": gid, "op": "pdf", "what": what})
                   for what in ("table", "trail", "all")}
        texts = {what: pdftext.pages_text((root / a["name"]).read_bytes()) for what, a in answers.items()}
        check("367: the GETs print card's Save as PDF: the GET table, the audit trail and the full set each written at "
              "the project's root through Typst, named as gets export names them",
              [a["name"] for a in answers.values()] == ["Dogs at home, an invented study - Board 1 - GET table.pdf",
                                                         "Dogs at home, an invented study - Board 1 - Audit trail.pdf",
                                                         "Dogs at home, an invented study - Board 1 - GETs.pdf"]
              and [r[0] for r in rendered] == ["gets.typ", "gets.typ", "gets-all.typ"]
              and all(squash("Letting a dog go") in squash(" ".join(t)) for t in texts.values()),
              json.dumps([a["name"] for a in answers.values()]))
        full = texts["all"]
        heads = [i18n.t("page_print.gets.contents"), i18n.t("page_print.gets.pet_tables"), i18n.t("page_print.gets.table"),
                 i18n.t("page_print.gets.trail")]
        joined = squash(" ".join(full))
        at = [joined.find(squash(x), joined.find(squash(heads[0])) + 1 if i else 0) for i, x in enumerate(heads)]
        # each participant's table of PETs on a page of its own, in the study's order, after the contents
        starts = [next((i for i, p in enumerate(full) if squash(i18n.t("page_print.gets.pet_table") + who) in squash(p)), -1)
                  for who in ("Juno", "Mabel", "Rowan")]
        check("367: the full set as today's orders it: the contents, then each participant's table of PETs from a page "
              "of its own, then the GET table and the audit trail, the table's and the trail's pages among them",
              all(x >= 0 for x in at) and at == sorted(at) and all(s > 0 for s in starts) and starts == sorted(set(starts))
              and len(full) > len(texts["table"]) + len(texts["trail"]), f"{at} {starts} {len(full)}")
        juno_pets = [t["label"] for t in themes_mod.outline(themes_mod.read_cards(book),
                                                            themes_mod.normalise(themes_mod.load(book)["boards"][0]))["themes"]]
        check("367: a participant's table in the full set holds their PETs", juno_pets and
              all(squash(x) in joined for x in juno_pets[:2]), str(juno_pets[:3]))
        rendered.clear()
        gpng = call("/api/gets-boards", {"root": str(root), "board": gid, "op": "canvas", "kind": "png", "notes": True})
        gpdf = call("/api/gets-boards", {"root": str(root), "board": gid, "op": "canvas", "kind": "pdf"})
        check("367: the GETs canvas's picture and PDF at the project's root, drawn by Typst",
              gpng["name"] == "Dogs at home, an invented study - Board 1 - GETs canvas.png"
              and (root / gpng["name"]).read_bytes()[:8] == b"\x89PNG\r\n\x1a\n" and a4_landscape((root / gpdf["name"]).read_bytes())
              and [r[0] for r in rendered] == ["canvas-main.typ", "canvas-main.typ"], json.dumps([gpng, gpdf])[:300])

        # ── E. a failing engine: the plain sentence, and nothing written
        def failing(template, data, **how):
            raise typeset.Failed(i18n.t("typeset.failed"))
        typeset.render = failing
        before = files(root)
        said = [refused("/api/themes-export", {"workbook": str(book), "version": bid, "op": "pdf"}),
                refused("/api/themes-export", {"workbook": str(book), "version": bid, "op": "canvas", "kind": "png"}),
                refused("/api/gets-boards", {"root": str(root), "board": gid, "op": "pdf", "what": "all"}),
                refused("/api/gets-boards", {"root": str(root), "board": gid, "op": "canvas", "kind": "pdf"})]

        def run(*args):
            code, out, err = cli.run(["--root", str(root), "--config", str(cfg), *args, "--json"])
            return code, out + err

        c1, s1 = run("board", "export", "Juno", "--pdf")
        c2, s2 = run("gets", "export", "--canvas", "png")
        mcp = mcp_server.Server(str(root), config=str(cfg))
        mcp.receive(json.dumps({"jsonrpc": "2.0", "id": 1, "method": "initialize",
                                "params": {"protocolVersion": "2025-06-18", "clientInfo": {"name": "claude-code"}}}))
        tool = lambda name, args: mcp.receive(json.dumps({"jsonrpc": "2.0", "id": 2, "method": "tools/call",
                                                          "params": {"name": name, "arguments": args}}))["result"]
        m1 = tool("board_export", {"case": "Juno", "canvas": "pdf"})
        sentence = i18n.t("typeset.failed")
        check("367: when Typst fails, the API, the command line and MCP each answer the catalogue's plain sentence and "
              "nothing is written",
              all(s == sentence for s in said) and c1 != 0 and sentence in s1 and c2 != 0 and sentence in s2
              and m1.get("isError") and sentence in json.dumps(m1) and files(root) == before,
              json.dumps([said, s1[-200:], s2[-200:]])[:600])
        typeset.render = counting

        # ── F. the command line and MCP, as the app makes them
        out = scratch / "a367-out"
        shutil.rmtree(out, ignore_errors=True)
        out.mkdir()
        rendered.clear()
        c3, s3 = run("board", "export", "Juno", "--pdf", "--out", str(out))
        c4, s4 = run("board", "export", "Juno", "--canvas", "png", "--out", str(out))
        c5, s5 = run("gets", "export", "--what", "all", "--out", str(out))
        c6, s6 = run("gets", "export", "--canvas", "pdf", "--out", str(out), "--replace")
        m2 = tool("board_export", {"case": "Juno", "canvas": "png", "out": str(out / "for a slide.png")})
        m3 = tool("gets_export", {"what": "trail", "out": str(out)})
        made_out = sorted(p.name for p in out.iterdir())
        check("367: board export --pdf and --canvas, gets export --what all and --canvas, and MCP's board_export and "
              "gets_export, each typeset by Typst and written where --out names",
              c3 == c4 == c5 == c6 == 0 and not m2.get("isError") and not m3.get("isError")
              and made_out == sorted(["Juno - Board 1 - PETs.pdf", "Juno - Board 1 - PETs canvas.png",
                                      "Dogs at home, an invented study - Board 1 - GETs.pdf",
                                      "Dogs at home, an invented study - Board 1 - GETs canvas.pdf", "for a slide.png",
                                      "Dogs at home, an invented study - Board 1 - Audit trail.pdf"])
              and [r[0] for r in rendered] == ["pets_table_main.typ", "canvas-main.typ", "gets-all.typ", "canvas-main.typ",
                                               "canvas-main.typ", "gets.typ"]
              and all(p.stat().st_size > 2000 for p in out.iterdir()), json.dumps([made_out, s3[-200:], s5[-200:]])[:500])
        pixels = support.plain(json.loads(s4))
        check("367: the command line's picture names its size in pixels, the PNG's own",
              pixels.get("pixels") == list(canvas_out.png_size((out / "Juno - Board 1 - PETs canvas.png").read_bytes())),
              s4[-300:])

        # ── G. LPETs and LGETs, on an invented project of three timepoints
        b64 = lambda text: base64.b64encode(text.encode("utf-8")).decode("ascii")

        def row(name, text, who, interview, **more):
            return dict({"name": name, "data": b64(text), "pseudonym": who, "interview": interview,
                         "speakers": {"Kit": "interviewer", who: "participant"}}, **more)

        choir = scratch / "a367" / "Choir year"
        shutil.rmtree(choir, ignore_errors=True)
        choir.mkdir(parents=True)
        srv.ROOT_OVERRIDE = None
        project = routes.api_new_project({"op": "make", "folder": str(choir), "name": "Choir year",
                                          "research_question": "How do newcomers make sense of a first year in a choir?",
                                          "files": [row("wren-1.txt", WREN_T1, "Wren", "Before"),
                                                    row("ash-1.txt", ASH_T1, "Ash", "Before")]})
        pid = project["project"]["id"]
        routes.api_project({"root": pid, "timepoints": THREE})
        routes.api_project({"root": pid, "agents": True})
        routes.api_add_transcripts({"op": "add", "root": pid, "files": [
            row("wren-2.txt", WREN_T2, "Wren", "Midwinter", timepoint=2),
            row("ash-2.txt", ASH_T2, "Ash", "Midwinter", timepoint=2)]})
        import workbook as wb_mod
        wren = choir / "P1 - Wren" / "P1 Wren - EN & ES.xlsx"
        ash = choir / "P2 - Ash" / "P2 Ash - EN & ES.xlsx"

        def said_rows(path: Path, sheet: str, who: str) -> list[int]:
            import openpyxl
            wb = openpyxl.load_workbook(path, read_only=True)
            try:
                return [r for r, v in enumerate(wb[sheet].iter_rows(min_row=2, max_col=1, values_only=True), start=2)
                        if str(v[0] or "").strip() == who]
            finally:
                wb.close()

        wb_mod.save_turn(wren, "Before", said_rows(wren, "Before", "Wren")[0], "Expecting scales\nFearing the flat note", "", "")
        wb_mod.save_turn(wren, "Before", said_rows(wren, "Before", "Wren")[1], "Hiding at the back", "", "")
        wb_mod.save_turn(wren, "Midwinter", said_rows(wren, "Midwinter", "Wren")[0], "Asking the altos first", "", "")
        wb_mod.save_turn(ash, "Before", said_rows(ash, "Before", "Ash")[0], "Singing a grandmother's songs", "", "")
        wb_mod.save_turn(ash, "Midwinter", said_rows(ash, "Midwinter", "Ash")[0], "Carried by the tenors", "", "")

        def board_of(path: Path, tp: int, groups: list):
            st = call("/api/themes", {"workbook": str(path), "timepoint": tp})
            keys = [c["key"] for c in st["cards"]]
            v = dict(st["version"], cards={k: {"x": 0, "y": 40 * i} for i, k in enumerate(keys)},
                     groups=[{"id": f"g{i + 1}", "label": label, "members": [keys[j] for j in at], "x": 300 * i, "y": -40}
                             for i, (label, at) in enumerate(groups)], discarded=[], picks={})
            call("/api/themes-save", {"workbook": str(path), "timepoint": tp, "version": v})

        def lpets_of(path: Path, groups: list) -> dict:
            lp = call("/api/gets", {"workbook": str(path), "lpets": True})
            pet = {c["text"]: c["key"] for c in lp["cards"] if c["kind"] == "pet"}
            lv = dict(lp["version"], cards={c["key"]: {"x": c["x"], "y": c["y"]} for c in lp["cards"]},
                      groups=[{"id": f"G{i + 1}", "label": label, "members": [pet[t] for t in titles], "x": 400 * i,
                               "y": -60} for i, (label, titles) in enumerate(groups)], discarded=[], picks={}, notes=[])
            call("/api/gets-save", {"workbook": str(path), "lpets": True, "version": lv})
            return lp

        board_of(wren, 1, [("Order expected", [0, 1]), ("Out of sight", [2])])
        board_of(wren, 2, [("Learning from the altos", [0])])
        board_of(ash, 1, [("A family's songs", [0])])
        board_of(ash, 2, [("Held up by others", [0])])
        lp = lpets_of(wren, [("From the score to the altos", ["Order expected", "Learning from the altos"])])
        lpets_of(ash, [("Others' voices", ["Held up by others", "A family's songs"])])
        rendered.clear()
        t2 = call("/api/themes-export", {"workbook": str(wren), "op": "canvas", "kind": "pdf", "timepoint": 2})
        lcan = call("/api/gets-boards", {"workbook": str(wren), "lpets": True, "op": "canvas", "kind": "png",
                                         "board": lp["version"]["id"]})
        lgets = call("/api/gets", {"workbook": str(wren)})
        lg_v = dict(lgets["version"], cards={c["key"]: {"x": c["x"], "y": c["y"]} for c in lgets["cards"]},
                    groups=[{"id": "G1", "label": "Leaning on other singers",
                             "members": [c["key"] for c in lgets["cards"] if c["kind"] == "pet"], "x": 0, "y": -60}],
                    discarded=[], picks={}, notes=[])
        call("/api/gets-save", {"workbook": str(wren), "version": lg_v})
        lg_pdf = call("/api/gets-boards", {"workbook": str(wren), "op": "pdf", "what": "table",
                                           "board": lgets["version"]["id"]})
        lg_can = call("/api/gets-boards", {"workbook": str(wren), "op": "canvas", "kind": "pdf",
                                           "board": lgets["version"]["id"]})
        lg_text = squash(" ".join(pdftext.pages_text((choir / lg_pdf["name"]).read_bytes())))
        lc_text = squash(" ".join(pdftext.pages_text((choir / lg_can["name"]).read_bytes())))
        t2_text = squash(" ".join(pdftext.pages_text((wren.parent / t2["name"]).read_bytes())))
        check("367: a timepoint's PETs canvas, a participant's LPETs canvas beside their workbook and the LGET table "
              "and canvas at the project's root, each through Typst with its own words",
              (wren.parent / t2["name"]).is_file() and squash("Learning from the altos") in t2_text
              and squash("Order expected") not in t2_text
              and lcan["name"] == "P1 - Wren - Board 1 - LPETs canvas.png" and (wren.parent / lcan["name"]).is_file()
              and squash("Leaning on other singers") in lg_text and squash("From the score to the altos") in lg_text
              and squash("Leaning on other singers") in lc_text and squash("LPET") in lc_text
              and squash("Longitudinal Group") in lg_text
              and [r[0] for r in rendered] == ["canvas-main.typ", "canvas-main.typ", "gets.typ", "canvas-main.typ"],
              json.dumps([lcan["name"], lg_pdf["name"], lg_can["name"], rendered, t2_text[:300], lg_text[:300],
                          lc_text[:300]]))
        lout = scratch / "a367-lout"
        shutil.rmtree(lout, ignore_errors=True)
        lout.mkdir()
        code, said_l, err = cli.run(["--root", str(choir), "--config", str(cfg), "gets", "export", "--lpets", "P1 - Wren",
                                     "--out", str(lout), "--json"])
        code2, said_c, err2 = cli.run(["--root", str(choir), "--config", str(cfg), "gets", "export", "--lpets", "P1 - Wren",
                                       "--canvas", "png", "--out", str(lout), "--json"])
        ltext = squash(" ".join(pdftext.pages_text((lout / support.plain(json.loads(said_l))["file"]).read_bytes()))) if code == 0 else ""
        check("367: the command line's LPET table and LPETs canvas of a participant, through Typst",
              code == 0 and squash("From the score to the altos") in ltext and squash("Longitudinal Personal") in ltext
              and code2 == 0 and (lout / support.plain(json.loads(said_c))["file"]).read_bytes()[:4] == b"\x89PNG",
              json.dumps([code, code2, ltext[:300], (said_c + err2)[-300:]]))

        # ── H. what typst4 left: clamped lines cut with "…", the close pairs' lines, a code's card
        from .a365_typst_canvas import fixture_state
        state = fixture_state()
        state["groups"][0]["description"] = ("Calm learned through the body before the hands know what to do, " * 9).strip()
        quote = ("I stood there with the frame in my hands and the whole colony moving across it, and I could hear my "
                 "own breath, and the teacher said nothing at all, which was the lesson that nothing needed saying")
        state["quotes"] = {"Initial:3": {"quotes": [{"key": "Initial:3:0", "text": quote}]}}
        for c in state["cards"]:
            if c["key"] in ("Initial:3:0", "Initial:3:1"):
                c.update(seconds=70 if c["key"].endswith("0") else 72, row=3)
        short = canvas_out.typst_data(state, "P4 Quill · Board 1", quotes="short", close=60)
        full = canvas_out.typst_data(state, "P4 Quill · Board 1", quotes="full")
        short_text = squash(" ".join(pdftext.pages_text(canvas_out.typeset_canvas(short, "pdf"))))
        full_text = squash(" ".join(pdftext.pages_text(canvas_out.typeset_canvas(full, "pdf"))))
        check("367: a label's description past six lines and a short quote past three end in an ellipsis as the canvas "
              "cuts them, and Full shows the quote whole",
              short_text.count("…") >= 2 and squash(quote) not in short_text and squash(quote) in full_text
              and squash(state["groups"][0]["description"]) not in short_text, str(short_text.count("…")))
        expected = [p["items"] for p in themes_mod.close_pairs(
            {"groups": state["groups"], "cards": {c["key"]: {} for c in state["cards"]}, "not_same": []},
            {c["key"]: c for c in state["cards"]}, 60)]
        drawn_keys = {c["key"] for c in short["cards"] if c["drawn"] and not c["missing"]}
        check("367: with Close pairs on, the canvas's data carries the board's close pairs as board show gives them, "
              "those on the canvas, and none with it off or on GETs",
              short["pairs"] and [p for p in expected if set(p) <= drawn_keys] == short["pairs"]
              and ["Initial:3:0", "Initial:3:1"] in short["pairs"] and full["pairs"] == [], json.dumps(short["pairs"][:4]))
        ta_root = scratch / "a367" / "ta"
        shutil.rmtree(ta_root, ignore_errors=True)
        ta_src = support.source("demo/ta/pristine")
        for name in ("Juno", "Mabel", "Rowan"):
            (ta_root / name / "Working").mkdir(parents=True)
            shutil.copy2(ta_src / f"{name} - EN & ES.xlsx", ta_root / name / f"{name} - EN & ES.xlsx")
            for side in sorted((ta_src / "Working").glob(f"{name} - *")):
                shutil.copy2(side, ta_root / name / "Working" / side.name)
        for extra in ("idiograph-gets.json", "idiograph-codes.json"):
            if (ta_src / extra).exists():
                shutil.copy2(ta_src / extra, ta_root / extra)
        shutil.copy2(support.source("demo/ta/idiograph-project.json"), ta_root / "idiograph-project.json")
        srv.ROOT_OVERRIDE = str(ta_root)
        ta_board = gets_mod.load(ta_root)["boards"][0]["id"]
        with routes.route_scope("/api/gets", {"root": str(ta_root)}):
            ta_data = canvas_out.gets_data(ta_root, routes.gets_books(ta_root), "Codes", ta_board)
        codes = [c for c in ta_data["cards"] if c["kind"] == "code"]
        ta_made = call("/api/gets-boards", {"root": str(ta_root), "board": ta_board, "op": "canvas", "kind": "pdf"})
        ta_text = squash(" ".join(pdftext.pages_text((ta_root / ta_made["name"]).read_bytes())))
        check("367: a thematic analysis project's board of themes draws each code as its code's card: Code with its "
              "extracts, the code's name and each participant's letter with how many are theirs",
              codes and all(c["kicker"].startswith(i18n.t("codes.card_kicker", extracts="").split("{")[0].strip()[:4])
                            and c["whos"] and sum(int(w["n"]) for w in c["whos"]) == int(re.search(r"\d+", c["kicker"]).group())
                            for c in codes)
              and squash(codes[0]["kicker"]) in ta_text and squash(codes[0]["text"]) in ta_text,
              json.dumps([(c["kicker"], c["text"], c["whos"]) for c in codes[:2]]))
    finally:
        typeset.render = real_render
        srv.CONFIG_PATH, srv.ROOT_OVERRIDE, srv.STATE_PATH, srv.STATE_MEMORY = kept
