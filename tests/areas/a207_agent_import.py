from __future__ import annotations

import io
import json
import os
import shutil
import zipfile
from xml.sax.saxutils import escape

import openpyxl

from .support import check
from . import support
import idiograph_routes
import idiograph_cli

W = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"

# an invented interview on keeping an allotment, Sam asking and Hazel answering, with notes beside it
ROWS = [
    ["Sam", "00:00:04", "How did the plot look when you first took it on?", ""],
    ["Hazel", "00:00:11", "Brambles everywhere. I could not see the shed.", "brambles as the year's neglect"],
    ["Sam", "00:01:02", "What did you clear first?", ""],
    ["Hazel", "00:01:09", "The path. I needed a way in before anything else.", "a way in, before growing"],
    ["Sam", "00:02:30", "And then?", ""],
    ["Hazel", "00:02:41", "Beans, because my father always grew beans.", "her father's beans, carried on"],
]
VTT = """WEBVTT

00:00:04.000 --> 00:00:08.000
<v Sam>Was the first summer hard?</v>

00:00:09.000 --> 00:00:14.000
<v Hazel>The slugs ate everything. I nearly gave it up.</v>

00:00:20.000 --> 00:00:22.000
<v Sam>What kept you going?</v>

00:00:23.000 --> 00:00:30.000
<v Hazel>The woman on the next plot gave me her spare leeks.</v>
"""


def word_table(rows) -> bytes:
    """A Word file holding one table, a paragraph a cell, as a table of transcript and notes is laid out."""
    cell = lambda text: f'<w:tc><w:p><w:r><w:t xml:space="preserve">{escape(text)}</w:t></w:r></w:p></w:tc>'
    table = "<w:tbl>" + "".join("<w:tr>" + "".join(cell(c) for c in row) + "</w:tr>" for row in rows) + "</w:tbl>"
    out = io.BytesIO()
    with zipfile.ZipFile(out, "w") as z:
        z.writestr("[Content_Types].xml", '<?xml version="1.0"?><Types '
                   'xmlns="http://schemas.openxmlformats.org/package/2006/content-types"/>')
        z.writestr("word/document.xml", f'<?xml version="1.0" encoding="UTF-8"?><w:document xmlns:w="{W}"><w:body>'
                                        f"{table}<w:sectPr/></w:body></w:document>")
    return out.getvalue()


def cells(path) -> dict:
    """Every sheet's values, row by row, what a workbook holds whoever wrote it."""
    book = openpyxl.load_workbook(path)
    try:
        return {ws.title: [list(r) for r in ws.iter_rows(values_only=True)] for ws in book.worksheets}
    finally:
        book.close()


def described(path) -> str:
    book = openpyxl.load_workbook(path)
    try:
        return str(book.properties.description or "")
    finally:
        book.close()


def test_agent_import(scratch):
    print("\n207. An import for AI agents through the one API: a transcript made into its raw source and a raw "
          "source into the case's workbook as the cards make them, dry run first, never over a file, the "
          "project's folder and the tick holding, and Claude Code's line at user scope (20 October)")
    import cli
    import convert
    import mcp_server
    import server as server_mod
    import workbook as wb_mod

    def make_root(at, allowed=True):
        shutil.rmtree(at, ignore_errors=True)
        source = at / "P2 - Hazel" / "Source"
        source.mkdir(parents=True)
        (source / "plot table.docx").write_bytes(word_table([["Speaker", "Time", "Transcript", "Notes"]] + ROWS))
        book = openpyxl.Workbook()
        ws = book.active
        ws.append(["Who", "When", "Said", "Thoughts"])
        for row in ROWS:
            ws.append(row)
        book.save(source / "plot sheet.xlsx")
        (source / "first summer.vtt").write_text(VTT, encoding="utf-8")
        held = {"name": "Allotments, an import project"}
        if allowed:
            held["agents"] = {"allowed": True, "at": "2026-10-20T01:00:00+01:00"}
        (at / server_mod.PROJECT_FILE).write_text(json.dumps(held), encoding="utf-8")
        (at / "loose.vtt").write_text(VTT, encoding="utf-8")
        return at

    def files(at):
        return {p.relative_to(at).as_posix(): p.read_bytes() for p in sorted(at.rglob("*")) if p.is_file()}

    kept = (server_mod.CONFIG_PATH, server_mod.ROOT_OVERRIDE, server_mod.STATE_MEMORY, server_mod.STATE_PATH)
    try:
        root = make_root(scratch / "a207-agent")
        twin = make_root(scratch / "a207-card")
        shut = make_root(scratch / "a207-shut", allowed=False)
        config = scratch / "a207-config.json"
        config.write_text(json.dumps({"root": str(root), "interviewer": "Researcher"}), encoding="utf-8")
        source = root / "P2 - Hazel" / "Source"

        def run(*argv, at=root):
            code, out, err = cli.run(["--root", str(at), "--config", str(config), *argv])
            return code, (support.plain(json.loads(out)) if "--json" in argv and out.strip() else out), err

        def card(name, **body):
            """The import card's Make on the twin, the same file, as the page asks for it."""
            server_mod.ROOT_OVERRIDE, server_mod.STATE_MEMORY = str(twin), {"recent": []}
            server_mod.STATE_PATH = scratch / "a207-state.json"
            server_mod.CONFIG_PATH = config
            got = idiograph_routes.api_import(dict(body, path=str(twin / "P2 - Hazel" / "Source" / name), op="make"))
            return server_mod.abs_path(got["source"]["path"])

        # ── A. a Word table, the dry run then the apply
        before = files(root)
        code, dry, _ = run("import", "P2 - Hazel/Source/plot table.docx", "--dry-run", "--json")
        check("207: a dry run on a Word table answers each column and its role, the speakers, the interviewer guessed, "
              "the first passages as they land and the file it would write, and writes nothing",
              code == 0 and dry["dry_run"] is True and files(root) == before
              and [(c["heading"], c["role"]) for c in dry["columns"]] == [("Speaker", "Speaker"), ("Time", "Time"),
                                                                          ("Transcript", "Transcript"), ("Notes", "Exploratory notes")]
              and [s["name"] for s in dry["speakers"]] == ["Sam", "Hazel"] and dry["interviewer"] == "Sam"
              and dry["interviewer_guessed"] is True and dry["interviewer_written_as"] == "Researcher"
              and [p["speaker"] for p in dry["passages"]] == ["Researcher", "Hazel"] * 3
              and dry["passages"][1]["notes"] == "brambles as the year's neglect"
              and dry["writes"] == "P2 - Hazel/Source/plot table.xlsx" and dry["count"] == 6, str(dry)[:400])
        code, _, err = run("import", "P2 - Hazel/Source/plot table.docx")
        check("207: an apply with no request is refused, nothing written",
              code == 1 and "--note" in err and files(root) == before, err)
        code, done, _ = run("import", "P2 - Hazel/Source/plot table.docx", "--note", "Bring in Hazel's plot interview",
                            "--tool", "Claude Code", "--json")
        raw = source / "plot table.xlsx"
        made = card("plot table.docx", interviewer="Sam")
        check("207: the apply writes the raw source the card's Make writes for the same file, cell for cell",
              code == 0 and done["written"] == "P2 - Hazel/Source/plot table.xlsx" and raw.is_file()
              and cells(raw) == cells(made), str(done)[:300])
        check("207: the workbook an agent wrote names the client and his request, the card's names nobody",
              described(raw).startswith("Made by Claude Code in a conversation on ")
              and "for the request 'Bring in Hazel's plot interview', from plot table.docx." in described(raw)
              and described(made) == "", described(raw))
        held = raw.read_bytes()
        code, _, err = run("import", "P2 - Hazel/Source/plot table.docx", "--note", "Again")
        check("207: an import never writes over a file already there, the card's line",
              code == 1 and "plot table.xlsx is already there." in err and raw.read_bytes() == held, err)

        # ── B. an Excel file with a role changed from the guess
        code, dry, _ = run("import", str(source / "plot sheet.xlsx"), "--dry-run", "--json")
        guessed = [c["role"] for c in dry["columns"]]
        code2, dry2, _ = run("import", str(source / "plot sheet.xlsx"), "--dry-run", "--json",
                             "--columns", "Speaker,Time,Transcript,Experiential statements")
        check("207: an Excel file's dry run guesses each column, and a role given in the call is the one it reads by",
              code == 0 and guessed == ["Speaker", "Time", "Transcript", "Exploratory notes"]
              and "The column headed Thoughts is left out." not in (dry.get("left_out") or [])
              and code2 == 0 and [c["role"] for c in dry2["columns"]][-1] == "Experiential statements"
              and dry2["passages"][1].get("statements") == "brambles as the year's neglect"
              and "notes" not in dry2["passages"][1] and dry2["writes"] == f"P2 - Hazel/Source/plot sheet{convert.CONVERTED}.xlsx",
              str(dry2)[:300])
        code, _, _ = run("import", str(source / "plot sheet.xlsx"), "--note", "Bring in the sheet",
                         "--columns", "Speaker,Time,Transcript,Experiential statements", "--interviewer", "Sam")
        made = card("plot sheet.xlsx", interviewer="Sam", columns=["name", "ts", "text", "es"])
        check("207: the Excel file lands as the card's Make lands it with the same roles",
              code == 0 and cells(source / f"plot sheet{convert.CONVERTED}.xlsx") == cells(made)
              and "Statements" in cells(made)[convert.SHEET][0])
        code, _, err = run("import", str(source / "plot sheet.xlsx"), "--dry-run", "--columns", "Speaker,Mood")
        check("207: a role that is not one is refused in one line naming it", code == 1 and err.startswith("Mood is not a role."), err)

        # ── C. a VTT file through the MCP tool, as Claude Code calls it
        srv = mcp_server.Server(str(root), config=str(config))
        srv.receive(json.dumps({"jsonrpc": "2.0", "id": 0, "method": "initialize",
                                "params": {"protocolVersion": "2025-06-18", "clientInfo": {"name": "claude-code"}}}))

        def call(**given):
            return srv.receive(json.dumps({"jsonrpc": "2.0", "id": 1, "method": "tools/call",
                                           "params": {"name": "import", "arguments": given}}))["result"]

        vtt = "P2 - Hazel/Source/first summer.vtt"
        before = files(root)
        got = call(file=vtt, request="Bring in the first summer", dry_run=True)
        dry = support.plain(got["structuredContent"])
        check("207: the MCP tool's dry run on a VTT file says the speakers, the interviewer and the passages, "
              "with no columns to choose, and writes nothing",
              got["isError"] is False and files(root) == before and dry["columns"] is None
              and dry["interviewer"] == "Sam" and len(dry["passages"]) == 4
              and dry["passages"][1] == {"speaker": "Hazel", "time": "00:09", "words": "The slugs ate everything. I nearly gave it up."}
              and support.unfenced(got["content"][0]["text"]).startswith("Dry run, nothing was written."), str(got)[:400])
        refused = call(file=vtt, request="x", columns=["Speaker"], dry_run=True)
        check("207: columns on a file with none are refused", refused["isError"] is True
              and idiograph_cli.NO_COLUMNS in support.unfenced(refused["content"][0]["text"]))
        got = call(file=vtt, request="Bring in the first summer", interviewer="Sam")
        made = card("first summer.vtt", interviewer="Sam")
        check("207: the tool's apply writes the card's raw source and names Claude Code",
              got["isError"] is False and cells(source / "first summer.xlsx") == cells(made)
              and described(source / "first summer.xlsx").startswith("Made by Claude Code in a conversation"),
              str(got)[:300])

        # ── D. a raw source made into the case's workbook, as the create card makes it
        before = files(root)
        code, dry, _ = run("import", "P2 - Hazel/Source/plot table.xlsx", "--dry-run", "--json")
        check("207: a raw source's dry run names the case's workbook it would write, for this participant's folder",
              code == 0 and dry["makes"] == "workbook" and dry["writes"] == "P2 - Hazel/P2 Hazel - EN & ES.xlsx"
              and dry["sheets"] == [convert.SHEET] and files(root) == before, str(dry)[:300])
        code, _, err = run("import", "P2 - Hazel/Source/plot table.xlsx", "--dry-run", "--interviewer", "Sam")
        check("207: a raw source takes no interviewer or columns", code == 1 and idiograph_cli.RAW_TAKES_NONE in err, err)
        code, _, _ = run("import", "P2 - Hazel/Source/plot table.xlsx", "--note", "Make Hazel's workbook")
        book = root / "P2 - Hazel" / "P2 Hazel - EN & ES.xlsx"
        theirs = wb_mod.create_from_source(twin / "P2 - Hazel" / "Source" / "plot table.xlsx", scratch / "a207-created.xlsx")
        check("207: the case's workbook is the one the create card makes from the same raw source, and names the agent",
              code == 0 and book.is_file() and cells(book) == cells(theirs)
              and "for the request 'Make Hazel's workbook'" in described(book))
        held = book.read_bytes()
        code, _, err = run("import", "P2 - Hazel/Source/plot table.xlsx", "--note", "Again")
        check("207: the case's workbook is never written over", code == 1 and "already there" in err and book.read_bytes() == held, err)
        code, _, err = run("import", "P2 - Hazel/P2 Hazel - EN & ES.xlsx", "--dry-run")
        check("207: a case's workbook is refused, nothing to import", code == 1 and "a participant's workbook already" in err, err)

        # ── E. the project's folder holds
        outside = scratch / "a207-outside.vtt"
        outside.write_text(VTT, encoding="utf-8")
        before = files(root)
        code, _, err = run("import", str(outside), "--dry-run")
        code2, _, err2 = run("import", "../a207-outside.vtt", "--dry-run")
        code3, _, err3 = run("import", "loose.vtt", "--dry-run")
        check("207: a file outside the project's folder is refused, by its full path or by ../, and one at its root "
              "outside any case, nothing written",
              code == 1 and err.strip() == idiograph_cli.OUTSIDE and code2 == 1 and err2.strip() == idiograph_cli.OUTSIDE
              and code3 == 1 and err3.strip() == idiograph_cli.NOT_IN_CASE and files(root) == before, err + err2 + err3)

        # ── F. the tick governs it
        before = files(shut)
        code, _, err = run("import", "P2 - Hazel/Source/first summer.vtt", "--note", "Bring it in", at=shut)
        shut_srv = mcp_server.Server(str(shut), config=str(config))
        got = shut_srv.receive(json.dumps({"jsonrpc": "2.0", "id": 1, "method": "tools/call", "params": {
            "name": "import", "arguments": {"file": "P2 - Hazel/Source/first summer.vtt", "request": "Bring it in"}}}))["result"]
        check("207: with the tick off the import is refused by the command line and the tool, nothing written",
              code == 1 and err.strip() == idiograph_cli.PRIVATE and got["isError"] is True
              and support.unfenced(got["content"][0]["text"]) == idiograph_cli.PRIVATE and files(shut) == before, err)

        # ── G. Claude Code's line at user scope, so it finds Idiograph from any folder
        held_env = os.environ.get(mcp_server.DESKTOP_ENV)
        os.environ[mcp_server.DESKTOP_ENV] = str(scratch / "a207-desktop.json")
        try:
            line = mcp_server.setup(mcp_server.desktop_entry(root))["claude_code"]
        finally:
            if held_env is None:
                os.environ.pop(mcp_server.DESKTOP_ENV, None)
            else:
                os.environ[mcp_server.DESKTOP_ENV] = held_env
        check("207: the Settings card's line for Claude Code adds Idiograph at user scope",
              line.startswith("claude mcp add --scope user idiograph -- "), line)
    finally:
        server_mod.CONFIG_PATH, server_mod.ROOT_OVERRIDE, server_mod.STATE_MEMORY, server_mod.STATE_PATH = kept
