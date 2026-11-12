from __future__ import annotations

import json
import re
import shutil
from pathlib import Path

from . import support
from .support import DEMO_QUESTION, add_second_sheet, check, demo_copy
import idiograph_routes
import idiograph_cli


def test_word_export(scratch):
    print("\n87. The PETs as a Word document, the IPA book's table of PETs, beside the workbook and never "
          "over a file, from the Export menu, the command line and MCP (192)")
    import hashlib
    import xml.etree.ElementTree as ET
    import zipfile
    from datetime import datetime
    import cli
    import mcp_server
    import server as server_mod
    import themes as themes_mod
    import themes_word

    js = support.text("apps/idiograph/static/themes.js")
    build_src = support.source("packaging/build_mac.py").read_text(encoding="utf-8")
    server_src = support.source("apps/idiograph/idiograph_routes.py").read_text(encoding="utf-8")
    cli_src = support.source("apps/idiograph/idiograph_cli.py").read_text(encoding="utf-8")
    fn = lambda src, name: src.split(f"function {name}(", 1)[1].split("\n}", 1)[0] if f"function {name}(" in src else ""
    sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()
    pristine = support.DEMO_PRISTINE
    W = themes_word.W
    tag = lambda name: f"{{{W}}}{name}"

    # \u2500\u2500 A. the fixture: the demo's Rowan as an invented case with a number and a second name, a second
    # sheet, and a sub-theme a level further in, then Juno with no number and no board yet
    root = scratch / "word-root"
    shutil.rmtree(root, ignore_errors=True)
    folder = root / "P{} - {}-{}".format(4, "Wren", "Testname")
    folder.mkdir(parents=True)
    wren = folder / "P4 Wren - EN & ES.xlsx"
    shutil.copy2(pristine / "Rowan - EN & ES.xlsx", wren)
    add_second_sheet(wren, "Follow-up", rows=4)
    held = json.loads((pristine / "Working" / "Rowan - EN & ES.themes.json").read_text(encoding="utf-8"))
    held["case"], held["workbook"] = "P4 - Wren", wren.name
    board = held["boards"][0]
    deep = "Initial:33:0"
    for g in board["groups"]:
        if g["id"] == "g6":
            g["members"] = ["g9" if m == deep else m for m in g["members"]]
    spot = board["cards"][deep]
    board["groups"].append({"id": "g9", "label": "Up at quarter past five & listening",
                            "note": "Kept apart <for now> & on its own\nA second line he wrote.",
                            "members": [deep], "x": spot["x"] - 12, "y": spot["y"] - 40})
    themes_mod.themes_path(wren).parent.mkdir(parents=True, exist_ok=True)
    themes_mod.themes_path(wren).write_text(json.dumps(held, ensure_ascii=False, indent=1), encoding="utf-8")
    juno = demo_copy(root, "Juno", "Juno - EN & ES.xlsx")
    (root / "idiograph-project.json").write_text(json.dumps({
        "name": "Dogs, a Word project", "research_question": DEMO_QUESTION,
        "agents": {"allowed": True, "at": "2026-10-06T10:00:00+01:00"}}), encoding="utf-8")
    cfg = scratch / "word-config.json"
    cfg.write_text(json.dumps({"root": str(root), "interviewer": "Adam"}), encoding="utf-8")

    def unzip(path: Path) -> dict:
        with zipfile.ZipFile(path) as z:
            return {n: z.read(n).decode("utf-8") for n in z.namelist()}

    def paras(xml: str) -> list[dict]:
        out = []
        for p in ET.fromstring(xml).iter(tag("p")):
            style, num, lvl = p.find(f"{tag('pPr')}/{tag('pStyle')}"), p.find(f".//{tag('numId')}"), p.find(f".//{tag('ilvl')}")
            runs = [("".join(t.text or "" for t in r.iter(tag("t"))), r.find(f"{tag('rPr')}/{tag('i')}") is not None,
                     r.find(f"{tag('rPr')}/{tag('b')}") is not None) for r in p.iter(tag("r"))]
            out.append({"style": style.get(tag("val")) if style is not None else "Normal",
                        "num": num.get(tag("val")) if num is not None else "",
                        "lvl": lvl.get(tag("val")) if lvl is not None else "",
                        "text": "".join(r[0] for r in runs), "italic": bool(runs) and all(r[1] for r in runs),
                        "bold": bool(runs) and all(r[2] for r in runs)})
        return out

    kept = (server_mod.ROOT_OVERRIDE, server_mod.STATE_MEMORY, server_mod.PLATFORM, idiograph_routes.REVEAL)
    revealed, refused = [], []
    before = {"book": sha(wren), "themes": sha(themes_mod.themes_path(wren)), "juno": sha(juno)}
    try:
        server_mod.ROOT_OVERRIDE = str(root)
        server_mod.STATE_MEMORY = {"recent": []}
        outline = themes_word.board_of(wren)[0]
        first = idiograph_routes.api_themes_export({"workbook": str(wren), "op": "word", "unplaced": True, "binned": True})
        first_sha = sha(folder / first["word"])
        second = idiograph_routes.api_themes_export({"workbook": str(wren), "op": "word", "unplaced": True, "binned": True})
        bare_one = idiograph_routes.api_themes_export({"workbook": str(juno), "op": "word", "unplaced": True, "binned": True})
        opened = idiograph_routes.api_themes({"workbook": str(wren)})
        server_mod.PLATFORM = "darwin"
        idiograph_routes.REVEAL = lambda target: revealed.append(Path(target))
        shown = idiograph_routes.api_themes_export({"workbook": str(wren), "op": "reveal", "file": first["shown"][0]})
        for named in (wren.name, "../Juno/" + bare_one["word"]):
            try:
                idiograph_routes.api_themes_export({"workbook": str(wren), "op": "reveal", "file": named})
                refused.append(False)
            except server_mod.OutsideRoot:
                refused.append(True)
    finally:
        server_mod.ROOT_OVERRIDE, server_mod.STATE_MEMORY, server_mod.PLATFORM, idiograph_routes.REVEAL = kept
    parts = unzip(folder / first["word"])
    doc = paras(parts["word/document.xml"])
    texts = [p["text"] for p in doc]

    # \u2500\u2500 B. the package
    names = ["[Content_Types].xml", "_rels/.rels", "word/document.xml", "word/styles.xml",
             "word/settings.xml", "word/_rels/document.xml.rels", "docProps/core.xml"]
    types = ET.fromstring(parts["[Content_Types].xml"])
    ct = "{http://schemas.openxmlformats.org/package/2006/content-types}"
    over = {o.get("PartName"): o.get("ContentType") for o in types.iter(f"{ct}Override")}
    default = {d.get("Extension"): d.get("ContentType") for d in types.iter(f"{ct}Default")}
    mime = "application/vnd.openxmlformats-officedocument.wordprocessingml"
    check("87, 205: the file is a zip of the Word parts, [Content_Types].xml first, each named with its content type, no numbering",
          list(parts) == names
          and over == {"/word/document.xml": f"{mime}.document.main+xml", "/word/styles.xml": f"{mime}.styles+xml",
                       "/word/settings.xml": f"{mime}.settings+xml",
                       "/docProps/core.xml": "application/vnd.openxmlformats-package.core-properties+xml"}
          and default == {"rels": "application/vnd.openxmlformats-package.relationships+xml", "xml": "application/xml"},
          str(list(parts)))
    rels = {r.get("Target") for name in ("_rels/.rels", "word/_rels/document.xml.rels")
            for r in ET.fromstring(parts[name]).iter("{http://schemas.openxmlformats.org/package/2006/relationships}Relationship")}
    formed = []
    for name, text in parts.items():
        try:
            ET.fromstring(text.encode("utf-8"))
            formed.append(True)
        except ET.ParseError:
            formed.append(False)
    check("87: every part is well-formed XML, and every relationship points at a part the package holds",
          all(formed) and rels == {"word/document.xml", "docProps/core.xml", "styles.xml", "settings.xml"}
          and themes_word.xml_text("a\x01b & <c>") == "ab &amp; &lt;c&gt;")

    # \u2500\u2500 C. the words, in the shape of the book's table of PETs (205, which replaced the approved draft's shape)
    lines = themes_word.plain(themes_word.blocks("P4 - Wren", outline, unplaced=True, binned=True))
    check("87, 205: the participant heads it under Heading 1, the table's name its subtitle, and no list of the PETs under it",
          doc[0] == {"style": "Heading1", "num": "", "lvl": "", "text": "P4 Wren", "italic": False, "bold": False}
          and doc[1] == {"style": "Subtitle", "num": "", "lvl": "", "text": "Table of Personal Experiential Themes",
                         "italic": False, "bold": False}
          and "Draft PETs:" not in texts and not any(t.startswith("A first go") for t in texts)
          and not any(p["num"] or p["lvl"] for p in doc) and doc[2]["style"] == "Heading2", texts[0])
    heads = [(p["style"], p["text"]) for p in doc if p["style"].startswith("Heading")]
    want_heads = [("Heading1", "P4 Wren")]

    nums = themes_word.th.pet_numbers(outline["themes"])

    def headed(ts, depth):
        for t in ts:
            want_heads.append((f"Heading{min(5, depth + 2)}", themes_word.th.numbered(nums[t["id"]], t["label"])))
            headed(t["themes"], depth + 1)

    headed(outline["themes"], 0)
    np_head, dc_head = f"Not placed ({len(outline['unplaced'])})", f"Experiential statements set aside ({len(outline['discarded'])})"
    want_heads += [("Heading2", np_head), ("Heading2", dc_head)]
    deep_title = next((t for _s, t in heads if t.endswith(" Up at quarter past five & listening")), "")
    check("87, 205, 207, 208: each PET a heading lettered A, each sub-theme a level down, a group a level more, in the canvas's order",
          heads == want_heads and ("Heading4", deep_title) in heads and re.match(r"^[A-Z]+\d+\.\d+ Up at", deep_title)
          and ("Heading2", f"A. {outline['themes'][0]['label']}") == heads[1] and "Quotes" not in texts, str(heads[:4]))
    at = lambda s: f"({s['sheet']}, {s['time']})"
    g1 = outline["themes"][0]
    start = texts.index(f"A. {g1['label']}")
    deep_at = texts.index(deep_title)
    check("87, 205: a PET's note in italics, then its statements, each followed by its sheet's name and timecode",
          doc[start + 1] == {"style": "Normal", "num": "", "lvl": "", "text": g1["note"], "italic": True, "bold": False}
          and all(f"{s['text']} {at(s)}" in texts for s in g1["statements"])
          and doc[start + 2]["text"] == f"{g1['statements'][0]['text']} {at(g1['statements'][0])}"
          and "Walking when nobody else does (Initial, 01:39)" in texts
          and [p["text"] for p in doc[deep_at + 1:deep_at + 3] if p["italic"]] == ["Kept apart <for now> & on its own",
                                                                                  "A second line he wrote."],
          str(doc[start + 1:start + 3]))
    quoted = [t for t in texts if "this is all right, this is ours" in t]
    check("87, 205: no Quotes heading, the picked quote once, as its statement's own, in single curly marks under it",
          quoted == ["\u2018this is all right, this is ours\u2019"]
          and texts[texts.index(quoted[0]) - 1] == "Frost, an empty field and her loops (Initial, 02:19)"
          and not any('"' in t or "\u201c" in t or "\u2018\u2018" in t for t in texts)
          and themes_word.bare('"\u201csaid\u201d"') == "said" and themes_word.bare("\u2018said\u2019") == "said",
          str(quoted))
    rest = texts[texts.index(np_head) + 1:texts.index(dc_head)]
    want_rest = [x for s in outline["unplaced"]
                 for x in [f"{s['text']} {at(s)}"] + ([f"\u2018{themes_word.bare(s['quote'])}\u2019"] if s["quote"] else [])]
    check("87, 205: Not placed and Discarded after the PETs, in transcript order, each quote under its statement",
          rest == want_rest and "A statement on row 2 (Follow-up, 02:00)" in rest
          and rest[rest.index("A statement on row 2 (Follow-up, 02:00)") + 1] == "\u2018a quote on row 2\u2019"
          and texts[texts.index(dc_head) + 1] == "Nocturnal, and not really joking (Initial, 01:39)", str(rest[:3]))
    check("87, 205: no key at the end, each reference naming its sheet",
          not any(t.startswith("Key:") or "(#" in t for t in texts) and doc[-1]["style"] != "Heading2")
    check("87: the document's words are its paragraphs as the module sets them out, run for run",
          texts == ["".join(r["text"] for r in b["runs"]) for b in themes_word.blocks("P4 - Wren", outline, unplaced=True, binned=True)]
          and len(lines) == len(texts))
    juno_doc = paras(unzip(juno.parent / bare_one["word"])["word/document.xml"])
    juno_texts = [p["text"] for p in juno_doc]
    check("87, 205: a case with no number is headed by its name alone, its board the one an open offers, all Not placed",
          bare_one["word"] == "Juno - PETs (Board 1).docx" and juno_texts[:2] == ["Juno", "Table of Personal Experiential Themes"]
          and re.fullmatch(r"Not placed \(\d+\)", juno_texts[2]) and not any(t.startswith("Experiential statements set aside") for t in juno_texts)
          and not any(t.startswith("Key:") for t in juno_texts)
          and not any(p["num"] for p in juno_doc)
          and themes_word.heading("P12 - Alder") == "P12 Alder",
          str(juno_texts[:3]))

    # \u2500\u2500 D. the styles: Word's own names, a serif at 11pt, no colour, no fill, no table
    styles = parts["word/styles.xml"]
    check("87, 205: Heading 1 to 4 under Word's own names with their outline levels, Normal a serif at 11pt, no list style",
          all(f'w:styleId="Heading{n}"><w:name w:val="heading {n}"/>' in styles and f'<w:outlineLvl w:val="{n - 1}"/>' in styles
              for n in range(1, 5))
          and '<w:style w:type="paragraph" w:default="1" w:styleId="Normal"><w:name w:val="Normal"/>' in styles
          and 'w:ascii="Times New Roman"' in styles and '<w:sz w:val="22"/>' in styles
          and "List Paragraph" not in styles and not any("numbering" in name for name in parts))
    check("87: no colour, no fill, no shading, no list and no table anywhere in the package",
          not any(w in text for text in parts.values() for w in ("w:color", "w:shd", "w:fill", "w:highlight", "themeColor",
                                                                  "w:tbl", "w:themeFill", "w:numPr")))

    # \u2500\u2500 E. the name at the case's root, never over a file, the workbook only read
    check("87: the file sits at the case folder's root beside the workbook, named by the pseudonym, the line naming it so",
          first["word"] == "P4 Wren - PETs (Board 1).docx" and first["shown"] == [first["word"]]
          and (folder / first["word"]).is_file() and not (folder / "Working" / first["word"]).exists()
          and first["dated"] is False and first["version"]["name"] == "Board 1"
          and "Testname" not in json.dumps([first, second, bare_one]))
    when = datetime(2026, 3, 9, 8, 5).astimezone()
    dry = themes_word.write(wren, "P4 - Wren", now=when, dry_run=True, unplaced=True, binned=True)
    third = themes_word.write(wren, "P4 - Wren", now=when, unplaced=True, binned=True)
    fourth = themes_word.write(wren, "P4 - Wren", now=when, unplaced=True, binned=True)
    check("87: a taken name never written over: the date and time go in it, then a count, the first file unchanged",
          second["dated"] is True and re.fullmatch(r"P4 Wren - PETs \(Board 1, \d{1,2} [A-Z][a-z]{2} \d{2}\.\d{2}\)\.docx", second["word"])
          and third["name"] == "P4 Wren - PETs (Board 1, 9 Mar 08.05).docx"
          and fourth["name"] == "P4 Wren - PETs (Board 1, 9 Mar 08.05, 2).docx"
          and dry["dry_run"] is True and dry["name"] == third["name"] and sha(folder / first["word"]) == first_sha,
          second["word"])
    check("87: the workbook and the themes file only read, Juno given no themes file",
          sha(wren) == before["book"] and sha(themes_mod.themes_path(wren)) == before["themes"] and sha(juno) == before["juno"]
          and not themes_mod.themes_path(juno).exists())
    check("87: Show in Finder opens on the Word document at the case's root, and still refuses the workbook and another case's file",
          shown == {"revealed": first["word"]} and revealed == [(folder / first["word"]).resolve()] and refused == [True, True])

    exporter = fn(js, "thExport")
    check("87: Word document saves the canvas first and asks for op word, a server from before it the restart line",
          "thExport(op.dataset.xop === 'word');" in js and "async function thExport(word = false)" in js
          and "if (word) Object.assign(body, { op: 'word' }, thIncludesSent(false));" in exporter and "await thFlush();" in exporter
          and exporter.index("if (word && !TH.wordable) { say(RESTART_LINE, 6000); return; }") < exporter.index("api('/api/themes-export'")
          and "TH.wordable = !!data.word;" in fn(js, "themesOpen") and opened.get("word") is True
          and "thExported({ shown," in exporter and "file: TH.exported.shown[0]" in fn(js, "thReveal"))

    # \u2500\u2500 G. the command line and MCP
    base = ["--root", str(root), "--config", str(cfg)]
    docx = lambda: sorted(p.name for p in folder.iterdir() if p.suffix == ".docx")
    have = docx()
    code_dry, out_dry, _ = cli.run(base + ["board", "export", "Wren", "--word", "--dry-run"])
    after_dry = docx()
    code_no, _, err_no = cli.run(base + ["board", "export", "Wren"])
    code_cli, out_cli, _ = cli.run(base + ["board", "export", "Wren", "Board 1", "--word", "--json"])
    made_cli = support.plain(json.loads(out_cli)) if code_cli == 0 else {}
    check("87: board export --word --dry-run says the file it would write and writes nothing, and with no --word is refused",
          code_dry == 0 and out_dry.startswith("Dry run, nothing was written. It would write P4 Wren - PETs (Board 1, ")
          and "The plain name was taken" in out_dry and after_dry == have
          and code_no == 1 and "--word" in err_no and "--pdf" in err_no,
          out_dry[:120])
    check("87: board export --word writes a new dated file beside the others, never over one, its JSON naming it",
          code_cli == 0 and made_cli.get("dated") is True and made_cli.get("file", "").startswith("P4 Wren - PETs (Board 1, ")
          and made_cli["file"] in docx() and len(docx()) == len(have) + 1 and made_cli["counts"]["pets"] == len(outline["themes"])
          and "Testname" not in out_cli + out_dry and sha(folder / first["word"]) == first_sha)
    tool = mcp_server.BY_NAME["board_export"]
    mcp = mcp_server.Server(str(root), config=str(cfg))
    mcp_dry = mcp.call(tool, {"case": "Wren", "dry_run": True})
    after_mcp_dry = docx()
    mcp_made = mcp.call(tool, {"case": "Wren", "board": "Board 1"})
    check("87: MCP's board_export takes dry_run and no request, marked as writing and never destroying, and writes as the command line",
          tool["command"] == ("board", "export") and set(tool["inputSchema"]["properties"]) == {"case", "board", "labels", "not_placed", "set_aside", "binned", "stacked", "descriptions", "format", "for_sending", "replace", "board_note", "out", "dry_run", "timepoint", "canvas", "portrait"}
          and tool["inputSchema"]["required"] == ["case"] and tool["annotations"]["readOnlyHint"] is False
          and tool["annotations"]["destructiveHint"] is False
          and mcp_dry["isError"] is False and support.unfenced(mcp_dry["content"][0]["text"]).startswith("Dry run, nothing was written.")
          and after_mcp_dry == sorted(have + [made_cli.get("file", "")])
          and mcp_made["isError"] is False and support.plain(mcp_made["structuredContent"])["file"] in docx()
          and len(docx()) == len(after_mcp_dry) + 1
          and "board_export" in mcp_server.TOOLS_LINE and ("board", "export") in idiograph_cli.COMMANDS,
          support.unfenced(mcp_made["content"][0]["text"])[:100])

    # \u2500\u2500 H. the bundle, the docs and the words
    check("87: the new module joins the Mac bundle's modules, imported by the server and the command line",
          "themes_word" in support.build_mac().modules("idiograph")
          and "import themes_word\n" in server_src and "import themes_word\n" in cli_src)
