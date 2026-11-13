"""Area 392: all bold and font colours taken out of a project, the words unchanged (clearformat, 13 November 2026,
Adam's ruling: "the quotes that are selected pick out the most relevant words").

What is checked, on the demo's three participants made a project: bold and coloured runs put into a transcript cell,
a key quote's cell, a statement and an exploratory note of one participant, an italic run beside them, and his bold
on a key quote of a GETs board's table row. The dry run counts by participant and by part and writes nothing, no
record, no restore point, no lock, no archive copy. The op clears every bold and colour, a highlight's orange
among them, leaves the italics and every cell's plain text as they were, copies the workbook and the board file to
_Archive first, keeps one line in the record of agents' changes, and a second run finds nothing. The run's undo puts
every file back byte for byte, the formatting with it. A cell whose words would read otherwise refuses the whole, every
file put back. MCP's clear_formatting runs the same op."""
from __future__ import annotations

import hashlib
import json
import shutil
from pathlib import Path

import openpyxl
from openpyxl.cell.rich_text import CellRichText, TextBlock
from openpyxl.cell.text import InlineFont
from openpyxl.styles import Font
from openpyxl.styles.colors import Color

from .support import check
from . import support

ASKED = "Take all the bold and colours out, the quotes pick out the words."


def digest(root: Path) -> dict:
    """Every file of the project by its contents, the lock files set aside."""
    return {p.relative_to(root).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in sorted(root.rglob("*")) if p.is_file() and not p.name.endswith(".lock")}


def words(path: Path) -> dict:
    import workbook as wb_mod
    wb = openpyxl.load_workbook(path, rich_text=True)
    try:
        return {(ws.title, c.coordinate): wb_mod.plain_text(c.value) if isinstance(c.value, (str, CellRichText)) else repr(c.value)
                for ws in wb.worksheets for row in ws.iter_rows() for c in row if c.value is not None}
    finally:
        wb.close()


def faces(path: Path, sheet: str, row: int, cols: dict) -> dict:
    """Each role's cell on the row: its own font's bold and colour, and each run's bold, italic and colour."""
    wb = openpyxl.load_workbook(path, rich_text=True)
    try:
        ws = wb[sheet]
        out = {}
        for role, col in cols.items():
            c = ws.cell(row, col)
            runs = [(bool(b.font.b), bool(b.font.i), b.font.color is not None)
                    for b in (c.value if isinstance(c.value, CellRichText) else []) if isinstance(b, TextBlock)]
            out[role] = {"bold": bool(c.font.b), "colour": c.font.color is not None and c.font.color.rgb not in (None, "FF000000")
                         and c.font.color.type == "rgb", "runs": runs}
        return out
    finally:
        wb.close()


def test_clear_formatting(scratch: Path):
    print("\n392. Bold and font colours out of a whole project: the dry run's counts and nothing written, every bold "
          "and colour cleared with the words and the italics kept, the archive copies, one record line, a second run "
          "finding nothing, the run's undo, a refusal putting every file back, and MCP (clearformat, 13 November)")
    import agent_changes
    import agent_log
    import cli
    import clear_format
    import mcp_server
    import os
    import workbook as wb_mod

    base = scratch / "clear-formatting-392"
    shutil.rmtree(base, ignore_errors=True)
    root = base / "Dogs at home"
    root.mkdir(parents=True)
    import server as server_mod
    (root / server_mod.PROJECT_FILE).write_text(json.dumps({
        "name": "Dogs at home", "research_question": support.DEMO_QUESTION,
        "agents": {"allowed": True, "at": "2026-11-13T09:00:00+00:00"}}), encoding="utf-8")
    shipped = support.DEMO_SHIPPED
    for book in sorted(shipped.glob("*.xlsx")):
        who = book.name.split(" - ")[0]
        (root / who / "Working").mkdir(parents=True)
        shutil.copy2(book, root / who / book.name)
        for side in sorted((shipped / "Working").glob(f"{book.stem}.*")):
            shutil.copy2(side, root / who / "Working" / side.name)
    shutil.copy2(shipped / "idiograph-gets.json", root / "idiograph-gets.json")
    config_file = base / "config.json"
    config_file.write_text(json.dumps({"projects": [{"root": str(root)}], "interviewer": "Interviewer",
                                       "corpus": "", "gravity_reference": "", "corpus_exclude": []}), encoding="utf-8")
    log = base / "agent-log.json"
    kept = (agent_changes.ALL_OPS, os.environ.get(agent_log.PLACE))
    agent_changes.ALL_OPS = None
    os.environ[agent_log.PLACE] = str(log)

    def run(*args, tool="Claude Code"):
        given = ["--config", str(config_file), "--root", str(root), "--json", *args]
        if tool is not None:
            given += ["--tool", tool]
        code, out, err = cli.run(given)
        return code, (support.plain(json.loads(out)) if out.strip() else {}), err + (out if code else "")

    try:
        # ── the formatting put in: one participant's row, bold and colour in four columns, italics beside them
        juno = root / "Juno" / "Juno - EN & ES.xlsx"
        # the demo's own highlights, orange runs in the transcripts, counted before anything is put in
        books = [{"case": who, "workbook": root / who / f"{who} - EN & ES.xlsx"} for who in ("Juno", "Mabel", "Rowan")]
        base_plan = clear_format.plan(root, books)
        own = {p["case"]: p for p in base_plan["by_participant"]}
        wb = openpyxl.load_workbook(juno, rich_text=True)
        ws, cols = next(wb_mod._transcript_sheets(wb))
        sheet = ws.title
        # a row of plain words alone, so its four cells count for what is put in here, the demo's own highlights
        # elsewhere counted as they stand
        row = next(r for r in range(2, ws.max_row + 1)
                   if all(isinstance(ws.cell(r, cols[k]).value, str) and ws.cell(r, cols[k]).value.strip()
                          and not clear_format.marked(ws.cell(r, cols[k]).font) for k in ("transcript", "es", "kq", "en"))
                   and len(ws.cell(r, cols["transcript"]).value) > 20)
        said = wb_mod.plain_text(ws.cell(row, cols["transcript"]).value)
        ws.cell(row, cols["transcript"]).value = CellRichText(
            TextBlock(InlineFont(b=True), said[:5]), TextBlock(InlineFont(color=Color(rgb="FFFF0000")), said[5:10]),
            TextBlock(InlineFont(i=True), said[10:15]), TextBlock(InlineFont(rFont="Calibri", sz=11, color=Color(theme=9)),
                                                                  said[15:20]), said[20:])
        ws.cell(row, cols["kq"]).font = Font(bold=True, color="FF1F4E79")
        es = wb_mod.plain_text(ws.cell(row, cols["es"]).value)
        ws.cell(row, cols["es"]).value = CellRichText(TextBlock(InlineFont(color=Color(rgb="FF00B050")), es[:3]), es[3:])
        en = wb_mod.plain_text(ws.cell(row, cols["en"]).value)
        ws.cell(row, cols["en"]).value = CellRichText(TextBlock(InlineFont(b=True, i=True), en[:4]), en[4:])
        wb.save(juno)
        wb.close()
        gets_file = root / "idiograph-gets.json"
        gd = json.loads(gets_file.read_text(encoding="utf-8"))
        gd["boards"][0]["rows"]["G1"]["Juno"]["bold"] = [[0, 4]]
        gets_file.write_text(json.dumps(gd, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
        roles = {k: cols[k] for k in ("transcript", "es", "kq", "en")}
        start, start_words, start_gets = digest(root), words(juno), gets_file.read_bytes()

        # ── 1. the dry run: counts by participant and part, nothing written
        code, dry, err = run("clear-formatting", "--dry-run", tool=None)
        juno_counts = next((p for p in dry.get("by_participant") or [] if p["case"] == "Juno"), {})
        check("392: the dry run counts Juno's transcript, quote, statement and note cells and the board's key quote, "
              "and no one else's, and names the files by kind and path, never a word",
              code == 0 and dry.get("dry_run") is True
              and juno_counts.get("transcript") == own.get("Juno", {}).get("transcript", 0) + 1
              and juno_counts.get("quotes") == 1 and juno_counts.get("statements") == 1 and juno_counts.get("notes") == 1
              and juno_counts.get("copies") == 1 and dry["cells"] == base_plan["cells"] + 4
              and all(p == own.get(p["case"]) for p in dry["by_participant"] if p["case"] != "Juno")
              and dry["rows"] == 1 and "Juno/Juno - EN & ES.xlsx" in dry["workbooks"]
              and dry["boards"] == ["idiograph-gets.json"] and said[:20] not in json.dumps(dry), err + json.dumps(dry)[:600])
        check("392: the dry run writes nothing: no record, no restore point, no lock and no archive copy",
              digest(root) == start and not (root / agent_changes.FILE).exists()
              and not (root / agent_changes.STORE).exists() and not list(root.rglob("_Archive")), str(sorted(digest(root))))

        # ── 2. the op: every bold and colour off, the words and the italics kept, the copies first
        code, done, err = run("clear-formatting", "--note", ASKED)
        after = faces(juno, sheet, row, roles)
        check("392: the op clears the bold and colour of the transcript's runs, the highlight's orange among them, the "
              "quote cell's own font, the statement's coloured run and the note's bold run",
              code == 0 and done.get("cells") == base_plan["cells"] + 4 and done.get("rows") == 1
              and not any(b or c for b, _i, c in after["transcript"]["runs"])
              and not after["kq"]["bold"] and not after["kq"]["colour"]
              and not any(c for _b, _i, c in after["es"]["runs"]) and not any(b for b, _i, _c in after["en"]["runs"]),
              err + json.dumps(after))
        check("392: the italics stay, the transcript's italic run and the note's, and every cell's plain text is as it was",
              any(i for _b, i, _c in after["transcript"]["runs"]) and any(i for _b, i, _c in after["en"]["runs"])
              and words(juno) == start_words, json.dumps(after))
        gd = json.loads(gets_file.read_text(encoding="utf-8"))
        check("392: his bold on the GETs board's key quote is gone, the row and its quote kept",
              "bold" not in gd["boards"][0]["rows"]["G1"]["Juno"] and gd["boards"][0]["rows"]["G1"]["Juno"]["quote"],
              json.dumps(gd["boards"][0]["rows"]["G1"]["Juno"]))
        archive = sorted(p.name for p in (root / "Juno" / "_Archive").iterdir()) if (root / "Juno" / "_Archive").is_dir() else []
        root_archive = sorted(p.name for p in (root / "_Archive").iterdir()) if (root / "_Archive").is_dir() else []
        check("392: a copy of the workbook as it was is in the participant's _Archive and of the GETs file in the "
              "root's, each named pre-clear-formatting, and no participant's board or progress file touched",
              len(archive) == 1 and archive[0].startswith("Juno - EN & ES (pre-clear-formatting ")
              and len(root_archive) == 1 and root_archive[0].startswith("idiograph-gets (pre-clear-formatting ")
              and (root / "_Archive" / root_archive[0]).read_bytes() == start_gets
              and all(digest(root).get(k) == v for k, v in start.items() if "/Working/" in k),
              str(archive + root_archive))
        lines = agent_changes.read(root)
        check("392: the op is one line in the record of agents' changes, with his request, never a participant's words",
              len(lines) == 1 and lines[0]["op"] == "clear-formatting" and lines[0]["request"] == ASKED
              and said[:20] not in json.dumps(lines), json.dumps(lines)[:600])
        code, valid, err = run("validate", tool=None)
        check("392: idiograph validate is clean after the op", code == 0, err + json.dumps(valid)[:400])
        code, again, err = run("clear-formatting", "--note", ASKED)
        check("392: a second run finds nothing to clear and writes nothing",
              code == 0 and again.get("cells") == 0 and again.get("rows") == 0 and len(agent_changes.read(root)) == 1,
              err + json.dumps(again)[:300])

        # ── 3. the run's undo puts every file back, the formatting with it
        rid = lines[0]["run"]
        code, undone, err = run("agents", "undo-run", rid, "--note", "Put the formatting back")
        now = digest(root)
        check("392: the run's undo puts the workbook and the GETs file back byte for byte, its bold and colours with them",
              code == 0 and now["Juno/Juno - EN & ES.xlsx"] == start["Juno/Juno - EN & ES.xlsx"]
              and now["idiograph-gets.json"] == start["idiograph-gets.json"]
              and faces(juno, sheet, row, roles)["kq"]["bold"], err + json.dumps(undone)[:400])

        # ── 4. a cell whose words would read otherwise refuses the whole, every file put back
        before = digest(root)
        real = clear_format.clear_book

        def wrong(book):
            counts = real(book)
            ws2, cols2 = next(wb_mod._transcript_sheets(book))
            ws2.cell(row, cols2["transcript"]).value = "changed words"
            return counts
        clear_format.clear_book = wrong
        try:
            code, refused, err = run("clear-formatting", "--note", ASKED)
        finally:
            clear_format.clear_book = real
        after_refusal = digest(root)
        check("392: words that would read otherwise refuse the whole op in one line, the workbook and the GETs file as "
              "they were",
              code != 0 and "would have changed the words" in err
              and after_refusal["Juno/Juno - EN & ES.xlsx"] == before["Juno/Juno - EN & ES.xlsx"]
              and after_refusal["idiograph-gets.json"] == before["idiograph-gets.json"], err[:300])

        # ── 5. MCP's clear_formatting runs the same op
        tools = {t["name"]: t for t in mcp_server.tools_for("idiograph")}
        t = tools.get("clear_formatting")
        check("392: MCP's clear_formatting writes, takes the participant as case and dry_run, and maps to the command "
              "line's op", t is not None and not t["annotations"]["readOnlyHint"]
              and {"case", "dry_run", "request"} <= set(t["inputSchema"]["properties"]), json.dumps(t)[:300] if t else "")
    finally:
        agent_changes.ALL_OPS = kept[0]
        if kept[1] is None:
            os.environ.pop(agent_log.PLACE, None)
        else:
            os.environ[agent_log.PLACE] = kept[1]
        agent_log.flush()
