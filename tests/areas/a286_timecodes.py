"""Area 286: timecodes, the project's own (28 October 2026, Adam: a project's setting, not the user's, a new project
starting on 1:15:12). Each form at five seconds, the last second before the hour, the hour, an hour and a quarter and
past ten hours, in Python and in the page's own function alike, a project with none reading 1:15:12, the setting saved
in the project file and followed by the transcript, a board's cards and quotes, the print view, Word, the command line's
turn lines and the GETs, the GETs file keeping its own so no case reads as changed, the dry runs of the route, the
command line and MCP writing nothing, the refusals, and in node a page in front of a server from before it."""
from __future__ import annotations

import json
import re
import shutil
import zipfile

from workbook import WorkbookError

from . import support
from .support import DEMO_QUESTION, DEMO_SHEET, check, demo_copy

SAMPLES = (5, 3599, 3600, 4512, 10 * 3600 + 4512)
WANT = {
    "75:12": ["00:05", "59:59", "60:00", "75:12", "675:12"],
    "1:15:12": ["00:05", "59:59", "1:00:00", "1:15:12", "11:15:12"],
    "01:15:12": ["00:00:05", "00:59:59", "01:00:00", "01:15:12", "11:15:12"],
}


def test_timecodes(scratch):
    print("\n286. Timecodes, the project's own: 75:12, 1:15:12 or 01:15:12 in Settings, Projects, every timecode of the "
          "project following it, a project with none on 1:15:12, and the agents' project set --timecodes (28 October)")
    import cli
    import gets as gets_mod
    import idiograph_cli
    import idiograph_routes as routes
    import mcp_server
    import server as server_mod
    import themes as themes_mod
    import themes_print
    import workbook as wb_mod

    # ── A. one function, three forms, in Python and in the page
    got = {f: [wb_mod.timecode(s, f) for s in SAMPLES] for f in wb_mod.TIMECODES}
    check("286: each form at 0:05, 59:59, the hour, 75:12 and past ten hours, and no time for no seconds",
          got == WANT and wb_mod.TIMECODES == ("75:12", "1:15:12", "01:15:12")
          and all(wb_mod.timecode(None, f) == "" for f in wb_mod.TIMECODES), json.dumps(got))
    check("286: a project's timecodes read 1:15:12 when the file has none or anything else, and the form given when it is one",
          [wb_mod.timecodes_of(v) for v in (None, "", "1:15", "75:12", "01:15:12", 75)]
          == ["1:15:12", "1:15:12", "1:15:12", "75:12", "01:15:12", "1:15:12"]
          and wb_mod.timecode(4512) == "1:15:12" and wb_mod.timecode(4512, None) == "1:15:12"
          and routes.read_project(None)["timecodes"] == "1:15:12")
    check("286: a timecode typed in any form reads back as its seconds, so the box's prefill saves as it was",
          all(wb_mod.parse_timecode(w) == s for f in WANT for w, s in zip(WANT[f], SAMPLES)))
    distil = support.text("apps/idiograph/static/distil.js")
    fn = lambda name: "function " + name + "(" + distil.split(f"function {name}(", 1)[1].split("\n}", 1)[0] + "\n}\n"
    head = distil.split("const TIMECODES = ", 1)[1].split(";", 1)[0]
    of = distil.split("const timecodesOf = ", 1)[1].split(";\n", 1)[0]
    script = (f"const TIMECODES = {head};\nconst timecodesOf = {of};\n" + fn("timecode")
              + f"const out = {{}};\nfor (const f of TIMECODES) out[f] = {list(SAMPLES)}.map((s) => timecode(s, f));\n"
              + "out.none = timecodesOf({ name: 'An older server' });\nout.nothing = timecodesOf(null);\n"
              + "out.kept = timecodesOf({ timecodes: '75:12' });\nout.half = timecode(4512.7, '1:15:12');\n"
              + "console.log(JSON.stringify(out));\n")
    run = support.run_node(script, scratch, "timecodes-286.js")
    page = json.loads(run.stdout) if run.returncode == 0 and run.stdout.strip() else {}
    check("286: the page's timecode writes each form as the server does, a project with no timecodes, from a server "
          "before them, reading 1:15:12, and the player's fractions of a second dropped",
          {f: page.get(f) for f in WANT} == WANT and page.get("none") == "1:15:12" and page.get("nothing") == "1:15:12"
          and page.get("kept") == "75:12" and page.get("half") == "1:15:12", run.stderr[:300] or run.stdout[:300])

    # ── B. the fixture: an invented project, one participant on the demo's words, a passage moved past the hour
    root = scratch / "timecodes-286"
    shutil.rmtree(root, ignore_errors=True)
    folder = root / "P1 - Wren"
    book = demo_copy(folder, "P1 Wren - EN & ES.xlsx")
    pfile = root / "idiograph-project.json"
    project = {"name": "Keeping hens, a scratch project", "research_question": DEMO_QUESTION,
               "agents": {"allowed": True, "at": "2026-10-28T10:00:00+00:00"}, "order": ["P1 - Wren"],
               "colour": "an invented key the app does not know"}
    pfile.write_text(json.dumps(project), encoding="utf-8")
    cfg = scratch / "timecodes-286-config.json"
    cfg.write_text(json.dumps({"projects": [{"root": str(root)}], "interviewer": "Adam"}), encoding="utf-8")
    read = themes_mod.read_cards(book)
    quoted = next(c for c in read["cards"] if themes_mod.row_key(c["sheet"], c["row"]) in read["quotes"])
    rows = {(r["sheet"], r["row"]): r for s in wb_mod.read_case(book)["sheets"] for r in s["rows"]}
    moved = rows[(quoted["sheet"], quoted["row"])]
    wb_mod.edit_turn(book, quoted["sheet"], quoted["row"], moved["text"], "1:15:12")
    others = [c for c in read["cards"] if c["key"] != quoted["key"]][:2]
    board = themes_mod.blank_version(themes_mod.read_cards(book)["cards"])
    board["cards"][quoted["key"]].update(x=0, y=100)
    board["groups"] = [{"id": "g1", "label": "Mornings with the hens", "members": [quoted["key"]] + [c["key"] for c in others],
                        "x": 0, "y": 40}]
    board["picks"] = {"g1": [quoted["key"]]}
    themes_mod.save(book, board, "P1 - Wren")

    def word_text(path) -> str:
        with zipfile.ZipFile(path) as z:
            body = z.read("word/document.xml").decode("utf-8")
        return "".join(re.findall(r"<w:t(?: [^>]*)?>([^<]*)</w:t>", body))

    kept = (server_mod.CONFIG_PATH, server_mod.ROOT_OVERRIDE, server_mod.STATE_MEMORY)
    try:
        server_mod.CONFIG_PATH, server_mod.ROOT_OVERRIDE = cfg, str(root)
        server_mod.STATE_MEMORY = {"recent": []}

        def seen() -> dict:
            """Every place the project's timecode shows, the passage moved to an hour and a quarter."""
            opened = routes.api_open({"path": str(book)})
            row = next(r for s in opened["sheets"] for r in s["rows"] if r["sheet"] == quoted["sheet"] and r["row"] == quoted["row"])
            th = routes.api_themes({"workbook": str(book)})
            card = next((c for c in th["cards"] if c["key"] == quoted["key"]), {})
            quote = (th.get("quotes") or {}).get(themes_mod.row_key(quoted["sheet"], quoted["row"])) or {}
            code, printed = routes.themes_print_page({"workbook": str(book), "auto": "0"})
            word = routes.api_themes_export({"workbook": str(book), "op": "word"})
            words = word_text(folder / word["word"].split("/")[-1])
            (folder / word["word"].split("/")[-1]).unlink()
            return {"project": (opened.get("project") or {}).get("timecodes"), "margin": row["time"],
                    "card": card.get("time"), "quote": quote.get("time"), "print": code == 200 and printed,
                    "word": words, "themes": (th.get("project") or {}).get("timecodes")}

        first = seen()
        check("286: a project with no timecodes reads 1:15:12, sent with the case and the board, and the margin, a card, "
              "its quote, the print view and Word all write the passage at 1:15:12",
              first["project"] == first["themes"] == "1:15:12" and first["margin"] == first["card"] == first["quote"] == "1:15:12"
              and "1:15:12" in first["print"] and "1:15:12" in first["word"] and "75:12" not in first["word"],
              json.dumps({k: v for k, v in first.items() if k not in ("print", "word")}))

        before = pfile.read_bytes()
        dry = routes.api_project({"path": str(book), "timecodes": "75:12", "dry_run": True})
        check("286: the route's dry run answers the project as it would be and its change, and writes nothing",
              dry["dry_run"] is True and dry["project"]["timecodes"] == "75:12" and dry["changes"] == ["Timecodes from 1:15:12 to 75:12."]
              and pfile.read_bytes() == before and routes.read_project(root)["timecodes"] == "1:15:12", json.dumps(dry["changes"]))

        saved = routes.api_project({"path": str(book), "timecodes": "75:12"})
        after = json.loads(pfile.read_text(encoding="utf-8"))
        check("286: Timecodes saves timecodes in the project file at once, every other key kept, an unknown one among them",
              saved["project"]["timecodes"] == "75:12" and saved["changes"] == ["Timecodes from 1:15:12 to 75:12."]
              and after == dict(project, timecodes="75:12"), str(after)[:200])
        second = seen()
        check("286: kept at 75:12, the transcript, the board's card and quote, print and Word all follow at once",
              second["project"] == second["themes"] == "75:12" and second["margin"] == second["card"] == second["quote"] == "75:12"
              and "75:12" in second["print"] and "1:15:12" not in second["print"] and "75:12" in second["word"]
              and "1:15:12" not in second["word"], json.dumps({k: v for k, v in second.items() if k not in ("print", "word")}))
        routes.api_project({"path": str(book), "timecodes": "01:15:12"})
        third = seen()
        check("286: and at 01:15:12 the hours always show, every place alike",
              third["margin"] == third["card"] == third["quote"] == "01:15:12" and "01:15:12" in third["print"]
              and "01:15:12" in third["word"], json.dumps({k: v for k, v in third.items() if k not in ("print", "word")}))
        exported = routes.api_export({"path": str(book)})
        csv_text = "".join(f.read_text(encoding="utf-8-sig") for f in folder.rglob("*.csv"))
        check("286: the statements CSV keeps 01:15:12 whatever the project's timecodes",
              "01:15:12" in csv_text and ",1:15:12" not in csv_text, str(exported)[:200])

        held = pfile.read_bytes()
        try:
            routes.api_project({"path": str(book), "timecodes": "1:15"})
            bad = ""
        except WorkbookError as exc:
            bad = str(exc)
        demo_file = server_mod.DEMO_PROJECT.read_bytes()
        try:
            routes.api_project({"root": "demo", "timecodes": "75:12"})
            demo_said = ""
        except WorkbookError as exc:
            demo_said = str(exc)
        check("286: anything but the three is refused with nothing written, and so is a save for the demo",
              bad == "Timecodes are 75:12, 1:15:12 or 01:15:12, so nothing was saved." and pfile.read_bytes() == held
              and demo_said == "The demo's project is fixed." and server_mod.DEMO_PROJECT.read_bytes() == demo_file
              and routes.read_project(server_mod.DEMO_DIR)["timecodes"] == "1:15:12", bad)

        # ── C. the GETs keep their file as it was, the times shown the project's way
        routes.api_project({"path": str(book), "timecodes": "1:15:12"})
        books = routes.gets_books(root)
        when = themes_mod.now_iso()
        gdata, _c, _d, _t = gets_mod.assemble(root, books, when)
        gets_mod.write(root, gets_mod._file(gdata, when))
        gfile = gets_mod.gets_path(root)
        on_disk = gfile.read_bytes()
        line = lambda data: data["cases"]["P1 - Wren"]["lines"][quoted["key"]]
        routes.api_project({"path": str(book), "timecodes": "75:12"})
        loaded = gets_mod.load(root)
        rec = loaded["cases"]["P1 - Wren"]
        fresh = gets_mod.snapshot(book)
        gets_mod.write(root, loaded)
        check("286: the GETs file keeps every time as 1:15:12, its lines read in the project's 75:12, a write keeping the "
              "file's form and the case unchanged since it came in",
              json.loads(on_disk)["cases"]["P1 - Wren"]["lines"][quoted["key"]]["time"] == "1:15:12"
              and line(loaded)["time"] == "75:12" and fresh["lines"][quoted["key"]]["time"] == "75:12"
              and gets_mod.snap_hash(fresh) == rec["hash"] and gfile.read_bytes() == on_disk,
              f"{line(loaded)['time']} {gets_mod.snap_hash(fresh)} {rec['hash']}")
        lined = {"seconds": 4512, "time": "T1, 1:15:12", "cite": "T1"}
        gets_mod.retimed(lined, "01:15:12")
        check("286: a time cited with its timepoint keeps it, T1, 01:15:12", lined["time"] == "T1, 01:15:12", lined["time"])

        # ── D. the command line and MCP: project set --timecodes, its dry run, the turn lines
        cmd = lambda *a: cli.run(["--root", str(root), "--config", str(cfg), *a])
        held = pfile.read_bytes()
        code1, out1, err1 = cmd("project", "set", "--timecodes", "01:15:12", "--dry-run")
        code2, out2, err2 = cmd("project", "set", "--timecodes", "1:15", "--note", "his words")
        check("286: project set --timecodes says its change in a dry run and writes nothing, and takes the three alone",
              code1 == 0 and out1.startswith("Dry run, nothing was written.") and "Timecodes from 75:12 to 01:15:12." in out1
              and "Timecodes: 01:15:12" in out1 and pfile.read_bytes() == held and code2 != 0 and pfile.read_bytes() == held,
              (out1 + err1 + err2)[:300])
        code3, out3, err3 = cmd("project", "set", "--timecodes", "01:15:12", "--note", "Cite them with the hours always",
                                "--tool", "Claude Code", "--json")
        code4, out4, err4 = cmd("turn", "show", "Wren", quoted["sheet"], str(quoted["row"]))
        check("286: project set --timecodes saves as Settings does, and the command line's turn lines follow it",
              code3 == 0 and json.loads(pfile.read_text(encoding="utf-8")) == dict(project, timecodes="01:15:12")
              and code4 == 0 and "01:15:12" in out4, (err3 + err4 + out4)[:300])
        mcp = mcp_server.Server(root=str(root), config=str(cfg))
        tool = mcp.by_name["project_set"]
        held = pfile.read_bytes()
        res = mcp.call(tool, {"timecodes": "75:12", "dry_run": True, "request": "Look first"})
        check("286: MCP's project_set takes timecodes, the three alone, and its dry run writes nothing",
              tool["inputSchema"]["properties"]["timecodes"]["enum"] == list(wb_mod.TIMECODES)
              and res["isError"] is False and "Timecodes from 01:15:12 to 75:12." in json.dumps(res)
              and pfile.read_bytes() == held, json.dumps(res)[:300])
        check("286: the parity of the page's save with the agents' op: the key the page sends to /api/project is the one "
              "project set and MCP's project_set send, on the op the parity check maps that route to",
              "timecodes: value" in distil.split("async function saveTimecodes(", 1)[1].split("\n}", 1)[0]
              and ("project", "set") in idiograph_cli.COMMANDS and tuple(tool["command"]) == ("project", "set")
              and "timecodes" in tool["inputSchema"]["properties"])
        code5, out5, _e5 = cmd("validate")
        pfile.write_text(json.dumps(dict(json.loads(pfile.read_text(encoding="utf-8")), timecodes="1:15")), encoding="utf-8")
        code6, out6, err6 = cmd("validate")
        check("286: validate reads timecodes against the project schema, and the app reads anything else as 1:15:12",
              code5 == 0 and code6 == 0 and "project.timecodes should be one of" in out6 + err6
              and routes.read_project(root)["timecodes"] == "1:15:12", (out6 + err6)[:300])
    finally:
        server_mod.CONFIG_PATH, server_mod.ROOT_OVERRIDE, server_mod.STATE_MEMORY = kept

    # ── E. the page in front of a server from before it, and the row drawn as the project holds it
    stub = (support.i18n_js("idiograph")
            + "const els = {};\nconst $ = (id) => els[id] || (els[id] = { id, hidden: false, textContent: '', dataset: {}, "
              "classList: { toggle() {} }, setAttribute() {}, querySelectorAll: () => buttons });\n"
            + "const buttons = ['75:12', '1:15:12', '01:15:12'].map((tc) => ({ dataset: { tc }, on: false, disabled: false, "
              "classList: { toggle(_c, on) { this.owner.on = on; } }, setAttribute() {} }));\n"
            + "buttons.forEach((b) => { b.classList.owner = b; });\n"
            + "const RESTART_LINE = 'restart';\nconst said = [];\nconst saidIn = (id, text) => said.push([id, text]);\n"
            + "const saidErr = (id, err) => said.push([id, String(err)]);\nconst S = { data: null };\nconst TH = { live: false };\n"
            + "const p = { id: 'r1', name: 'Hens', demo: false };\nconst PROJ = { own: p, list: [p], at: 'r1' };\n"
            + "const projectAt = () => p;\nconst projectBody = (q) => ({ root: q.id });\nlet sent = null;\n"
            + "const api = async (route, body) => { sent = [route, body]; return { project: { name: 'Hens' } }; };\n"
            + f"const TIMECODES = {head};\nconst timecodesOf = {of};\n" + fn("timecode") + fn("drawTimecodes")
            + "async " + fn("saveTimecodes")
            + "(async () => {\n  drawTimecodes(p);\n  const drawn = buttons.filter((b) => b.on).map((b) => b.dataset.tc);\n"
              "  await saveTimecodes('75:12');\n"
              "  console.log(JSON.stringify({ drawn, sent, said, kept: p.timecodes || null, shown: els['tc-said'].hidden }));\n})();\n")
    run2 = support.run_node(stub, scratch, "timecodes-older-286.js")
    older = json.loads(run2.stdout) if run2.returncode == 0 and run2.stdout.strip() else {}
    check("286: in front of a server from before it the row ticks 1:15:12, a press sends timecodes, and an answer without "
          "them says to restart under the row and keeps nothing",
          older.get("drawn") == ["1:15:12"] and older.get("sent") == ["/api/project", {"root": "r1", "timecodes": "75:12"}]
          and older.get("said") == [["tc-said", "restart"]] and older.get("kept") is None and older.get("shown") is False,
          run2.stderr[:400] or run2.stdout[:300])
