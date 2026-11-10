"""Area 258: a chosen send (23 October 2026, Adam: a tester makes PETs for one of his participants,
blinded, to compare with his own, and any subset of participants and kinds through the API). `project
send` takes `--participant` (repeatable), `--leave-out` and `--with` kinds (pets, gets, audio) and
`--blind`, the PETs and GETs left out. The chosen participants' workbooks always go, each folder named by
its label alone, recordings stay out unless asked for, `_Archive` copies never go, and GETs holding a
participant not sent stay out with a line, or are refused when asked for by name. The file opens as a
copy as any sent project does, the statements all there and no board. The source project is byte for
byte as it was. The MCP tool and the route take the same options. For the card's design E (23 October),
`--pets` and `--audio` choose the PETs and recordings participant by participant, `--leave-out audio`
alone sends the whole project but its recordings, and `--list` answers what each participant has.
`--boards current` (23 October) sends a participant of three boards with the current one alone, its
History left behind, and the copy opens on that board. `--boards all` is the send as before.

The fixtures are invented: a project on swimming in a lake at night, two made-up participants, one of
whose folders carries a second part after the pseudonym, as a study's folders may."""
from __future__ import annotations

import json
import shutil
import zipfile
from pathlib import Path, PurePosixPath

import openpyxl

from .support import check
from . import support


def make_workbook(root: Path, folder: str, speaker: str) -> Path:
    """A made-up participant's annotated workbook, its name carrying the whole folder name, with
    statements, quotes, notes and an Interviewer note."""
    import workbook as wb_mod
    case = root / folder
    (case / "Source").mkdir(parents=True)
    raw = openpyxl.Workbook()
    first = raw.active
    first.title = "Initial"
    first.append(["Name", "Timestamp", "Transcript"])
    first.append(["Interviewer", "00:00:04", "What is it like to swim at night?"])
    first.append([speaker, "00:00:09", "The water is warmer than the air and I cannot see my hands."])
    first.append(["Interviewer", "00:00:20", "And when you stop?"])
    first.append([speaker, "00:00:26", "I float and the stars come down to meet the lake."])
    source = case / "Source" / f"{folder} - interview.xlsx"
    raw.save(source)
    book = wb_mod.create_from_source(source, case / f"{folder} - EN & ES.xlsx")
    wb = openpyxl.load_workbook(book, rich_text=True)
    ws = wb.worksheets[0]
    cols = wb_mod.detect_columns(ws)
    ws.cell(3, cols["es"]).value = "Losing the edges of the body in dark water"
    ws.cell(3, cols["en"]).value = "A made-up note on the dark."
    ws.cell(3, cols["kq"]).value = "“I cannot see my hands”"
    ws.cell(5, cols["es"]).value = "The sky coming close while floating"
    ws.cell(5, cols["kq"]).value = "“the stars come down to meet the lake”"
    ws.cell(1, 7).value, ws.cell(1, 7).font = wb_mod.NOTE_HEADER, wb_mod.HFONT
    ws.cell(2, 7).value = "I led with the night too soon."
    wb.save(book)
    return book


def test_send_chosen(scratch: Path):
    print("\n258. A chosen send: some participants, kinds left out or asked for, --blind, opened as a copy")
    import cli
    import mcp_server
    import project_pack
    import rounds as rounds_mod
    import server as server_mod
    import idiograph_routes as routes

    base = scratch / "send-258"
    shutil.rmtree(base, ignore_errors=True)
    root = base / "Night swimming"
    root.mkdir(parents=True)
    second = "Pike"
    a_folder = "P1 - Tamsin" + "-" + second
    (root / server_mod.PROJECT_FILE).write_text(json.dumps({
        "name": "Night swimming", "research_question": "How do people live swimming in a lake at night?",
        "names": {"P1 - Tamsin": "Tamsin"}, "agents": {"allowed": True, "at": "2026-10-23T10:00:00+01:00"},
        # its own id, which a send writes when there is none (area 260)
        "uid": "a258beef0000cafe"}),
        encoding="utf-8")
    a_book = make_workbook(root, a_folder, "Tamsin")
    b_book = make_workbook(root, "P2 - Orrin", "Orrin")
    for book in (a_book, b_book):
        rounds_mod.save_progress(book, {"version": 1, "rows": {"Initial:3": "has-content", "Initial:5": "has-content"},
                                        "complete": {"at": "2026-10-20T10:00:00+01:00"},
                                        # a History whose requests name a board and a PET, as an agent's edits do
                                        "edits": [{"sheet": "Initial", "row": 3, "by": "agent", "tool": "Claude Code",
                                                   "request": "Put the best quote top of Dark water on Board 1",
                                                   "note": "Board 1, PET Dark water", "when": "2026-10-21T10:00:00+01:00"}],
                                        "assignments": [{"id": "a1", "sheet": "Initial", "row": 3, "note": "Board 1"}]})
    config_file = base / "config-258.json"
    config_file.write_text(json.dumps({"projects": [], "interviewer": "Interviewer", "corpus": "",
                                       "gravity_reference": "", "corpus_exclude": []}), encoding="utf-8")
    out_dir, into = base / "out", base / "into"
    out_dir.mkdir()
    into.mkdir()

    def run(*args):
        code, out, err = cli.run(["--config", str(config_file), *args])
        return code, out, err

    def run_json(*args):
        code, out, err = run("--json", *args)
        got = support.plain(json.loads(out)) if out.strip() else {}
        return code, (got if code == 0 else {}), err + (got.get("error", "") if code != 0 else "")

    # a board with its history through the API, then the PET draft, a PET table, GETs, an _Archive copy
    # and a recording beside them, as a project holds them
    plan = base / "plan.json"
    plan.write_text(json.dumps({"pets": [{"title": "Dark water", "members": ["S1"]}],
                                "not_placed": {"S2": ""}}), encoding="utf-8")
    for who in ("Tamsin", "Orrin"):
        code, _, err = run("--root", str(root), "board", "new", who, "--from", str(plan), "--note", "A first board",
                           "--tool", "Claude Code")
        check(f"258: a board is made on {who}'s canvas for the fixture", code == 0, err)
    a_case, b_case = root / a_folder, root / "P2 - Orrin"
    (a_case / "Working" / "P1 - Tamsin - PET draft (Board 1).md").write_text("# Dark water\n", encoding="utf-8")
    (a_case / "P1 - Tamsin - Board 1 - PETs.docx").write_bytes(b"PK\x03\x04 a PET table stands in here")
    (a_case / "P1 - Tamsin.pdf").write_bytes(b"%PDF-1.4 a PET table stands in here")
    (a_case / "_Archive").mkdir()
    (a_case / "_Archive" / "older.xlsx").write_bytes(b"an older copy")
    (a_case / "Source" / "Initial" / "Source").mkdir(parents=True)
    (a_case / "Source" / "Initial" / "Source" / "P1-Initial.m4a").write_bytes(bytes(range(256)) * 40)
    # working notes of the analyst's own and raw exports, none of them Idiograph's (23 October, a blinding leak)
    (a_case / "Working" / "PET grouping draft.md").write_text("# Dark water, then the sky\n", encoding="utf-8")
    (a_case / "Working" / "memo.md").write_text("A made-up memo.\n", encoding="utf-8")
    (a_case / "Working" / "P1 - Tamsin - All Experiential Statements.csv").write_text("statement\n", encoding="utf-8")
    (a_case / "Source" / "Initial" / "raw export.csv").write_text("speaker,text\n", encoding="utf-8")
    (a_case / "Source" / "Initial" / "misattributions.txt").write_text("none\n", encoding="utf-8")
    (a_case / "photo notes.txt").write_text("A made-up note.\n", encoding="utf-8")
    (root / "idiograph-gets.json").write_text(json.dumps({"schema": 1, "cases": {"P1 - Tamsin": {}, "P2 - Orrin": {}},
                                                          "boards": []}), encoding="utf-8")
    (root / "Night swimming - GETs.docx").write_bytes(b"PK\x03\x04 a GETs table stands in here")

    def files(at: Path) -> dict:
        return {p.relative_to(at).as_posix(): p.read_bytes() for p in sorted(at.rglob("*")) if p.is_file()}

    def held_in(file: Path) -> list:
        with zipfile.ZipFile(file) as zf:
            return sorted(n[len(project_pack.TOP):] for n in zf.namelist() if n.startswith(project_pack.TOP))

    code, before_rows, err = run_json("--root", str(root), "statements", "Tamsin")
    before = files(root)
    check("258: Tamsin's two statements read before the send", code == 0 and len(before_rows.get("statements", [])) == 2, err)

    kept = (server_mod.CONFIG_PATH, server_mod.ROOT_OVERRIDE, server_mod.STATE_MEMORY)
    try:
        # 1. the dry run lists every file and every kind left out, and writes nothing
        code, dry, err = run_json("--root", str(root), "project", "send", "--to", str(out_dir), "--participant", "Tamsin",
                                  "--blind", "--dry-run")
        check("258: --participant Tamsin --blind --dry-run lists the files and what stays out, and writes nothing",
              code == 0 and dry.get("dry_run") is True and dry.get("participants") == ["P1 - Tamsin"]
              and set(dry.get("left", {})) == {"pets", "gets", "audio", "notes", "source", "history", "archive", "participants"}
              and dry.get("kinds_out") == ["pets", "gets", "audio", "notes", "source"]
              and {"P1 - Tamsin/Working/PET grouping draft.md", "P1 - Tamsin/Working/memo.md", "P1 - Tamsin/photo notes.txt",
                   "P1 - Tamsin/Working/P1 - Tamsin - All Experiential Statements.csv"} <= set(dry["left"]["notes"])
              and {"P1 - Tamsin/Source/Initial/raw export.csv", "P1 - Tamsin/Source/Initial/misattributions.txt",
                   "P1 - Tamsin/Source/P1 - Tamsin - interview.xlsx"} <= set(dry["left"]["source"])
              and not list(out_dir.iterdir()) and files(root) == before, err or json.dumps(dry)[:400])
        code, said, err = run("--root", str(root), "project", "send", "--to", str(out_dir), "--participant", "Tamsin",
                              "--blind", "--dry-run")
        check("258: the dry run's lines name each file it would hold and each kind it leaves out, never the folder's second part",
              code == 0 and "  P1 - Tamsin/P1 - Tamsin - EN & ES.xlsx" in said and "Left out, PETs" in said
              and "Left out, GETs" in said and "Left out, recordings" in said and "Left out, _Archive copies" in said
              and "Left out, working notes" in said and "Left out, Source" in said
              and second not in said, said + err)

        # 2. the blinded file holds Tamsin alone, nothing of the grouping, her folder by her label
        code, done, err = run_json("--root", str(root), "project", "send", "--to", str(out_dir), "--participant", "Tamsin",
                                   "--blind")
        sent = out_dir / "Night swimming.idiograph"
        names = held_in(sent) if sent.is_file() else []
        done_blind = done.get("listed")
        check("258: the blinded file holds the project file and Tamsin's workbook and progress file alone, no working "
              "notes and no Source",
              code == 0 and names == sorted([
                  server_mod.PROJECT_FILE, "P1 - Tamsin/P1 - Tamsin - EN & ES.xlsx",
                  "P1 - Tamsin/Working/P1 - Tamsin - EN & ES.progress.json"]), err or str(names))
        check("258: no file of the blinded send carries a board, a draft, a table, a GETs file, a recording, an _Archive copy, "
              "Orrin or the folder's second part",
              not any(("themes" in n or "draft" in n or n.endswith((".docx", ".pdf", ".m4a")) or "gets" in n
                       or "_Archive" in n or "Orrin" in n or second in n) for n in names), str(names))
        with zipfile.ZipFile(sent) as zf:
            project_sent = json.loads(zf.read(project_pack.TOP + server_mod.PROJECT_FILE))
            head = json.loads(zf.read(project_pack.MANIFEST))
        check("258: the project file goes with its name and question and without Rename's names, the format unchanged",
              project_sent.get("research_question") == "How do people live swimming in a lake at night?"
              and "names" not in project_sent and head["format"] == project_pack.FORMAT
              and head["chosen"] == {"participants": ["P1 - Tamsin"], "left_out": ["pets", "gets", "audio", "notes", "source"]},
              json.dumps(head)[:300])
        check("258: the source project is byte for byte as it was after the send", files(root) == before)

        # 3. opened as a copy: Tamsin alone, every statement there, no board, statements complete kept
        code, _, err = run("project", "open-copy", str(sent), "--into", str(into))
        copy = into / "Night swimming"
        code2, cases, err2 = run_json("--root", str(copy), "cases")
        code3, rows, err3 = run_json("--root", str(copy), "statements", "Tamsin")
        check("258: the blinded file opens as a copy holding Tamsin alone, with no board yet",
              code == 0 and code2 == 0 and [c["case"] for c in cases.get("cases", [])] == ["P1 - Tamsin"]
              and cases["cases"][0]["boards"] == [] and cases["cases"][0]["statements_complete"]
              and not cases.get("project", {}).get("gets_file"), err + err2 + json.dumps(cases)[:300])
        strip = lambda rs: [{k: r.get(k) for k in ("key", "text", "quote", "quotes", "notes", "sheet", "row")} for r in rs]
        check("258: every one of Tamsin's statements is in the copy as it was, quotes and notes with them",
              code3 == 0 and strip(rows.get("statements", [])) == strip(before_rows["statements"]), err3)
        copied = copy / "P1 - Tamsin" / "P1 - Tamsin - EN & ES.xlsx"
        check("258: the workbook arrives byte for byte, its Interviewer note with it",
              copied.read_bytes() == a_book.read_bytes()
              and openpyxl.load_workbook(copied).worksheets[0].cell(2, 7).value == "I led with the night too soon.")

        progress_copy = json.loads((copy / "P1 - Tamsin" / "Working" / "P1 - Tamsin - EN & ES.progress.json")
                                   .read_text(encoding="utf-8"))
        check("258: the blinded progress file goes without its History, no edits, no assignments, no request, note "
              "or tool, its rows and completion kept",
              "edits" not in progress_copy and "assignments" not in progress_copy
              and not any(w in json.dumps(progress_copy) for w in ("Board", "Dark water", "request", "Claude Code"))
              and progress_copy.get("rows") == {"Initial:3": "has-content", "Initial:5": "has-content"}
              and progress_copy.get("complete") == {"at": "2026-10-20T10:00:00+01:00"}, json.dumps(progress_copy))

        # 4. a subset of two with PETs and without GETs
        code, done, err = run_json("--root", str(root), "project", "send", "--to", str(out_dir / "pets.idiograph"),
                                   "--participant", "Tamsin", "--participant", "P2 - Orrin", "--leave-out", "gets")
        names = held_in(out_dir / "pets.idiograph") if code == 0 else []
        check("258: --leave-out gets sends both participants with their boards and drafts and tables, no GETs, no recording",
              code == 0 and "P1 - Tamsin/Working/P1 - Tamsin - EN & ES.themes.json" in names
              and "P2 - Orrin/Working/P2 - Orrin - EN & ES.themes.json" in names
              and "P1 - Tamsin/Working/P1 - Tamsin - PET draft (Board 1).md" in names
              and "P1 - Tamsin/P1 - Tamsin - Board 1 - PETs.docx" in names
              and not any("gets" in n.lower() or n.endswith(".m4a") or "_Archive" in n for n in names)
              and done.get("kinds_out") == ["gets", "audio", "notes", "source"], err or str(names))
        with zipfile.ZipFile(out_dir / "pets.idiograph") as zf:
            kept_history = json.loads(zf.read(project_pack.TOP + "P1 - Tamsin/Working/P1 - Tamsin - EN & ES.progress.json"))
        check("258: a send that keeps the PETs keeps the progress file's History",
              kept_history.get("edits", [{}])[0].get("request") == "Put the best quote top of Dark water on Board 1"
              and "history" not in done.get("left", {}), json.dumps(kept_history)[:300])

        # 4b. working notes and Source go only when asked for, the grouping still out of a blinded send
        code, done, err = run_json("--root", str(root), "project", "send", "--to", str(out_dir / "notes.idiograph"),
                                   "--participant", "Tamsin", "--blind", "--with", "notes", "--with", "source")
        names = held_in(out_dir / "notes.idiograph") if code == 0 else []
        check("258: --with notes and --with source bring the working notes and Source, the boards still out",
              code == 0 and {"P1 - Tamsin/Working/PET grouping draft.md", "P1 - Tamsin/Working/memo.md",
                             "P1 - Tamsin/photo notes.txt", "P1 - Tamsin/Source/Initial/raw export.csv",
                             "P1 - Tamsin/Source/P1 - Tamsin - interview.xlsx"} <= set(names)
              and not any("themes" in n or "PET draft (" in n or n.endswith(".m4a") for n in names), err or str(names))

        # 5. GETs with a participant not sent: left out with a line, or refused when asked for
        code, done, err = run_json("--root", str(root), "project", "send", "--to", str(out_dir / "one.idiograph"),
                                   "--participant", "Tamsin")
        names = held_in(out_dir / "one.idiograph") if code == 0 else []
        check("258: GETs holding a participant not sent stay out, said in a line, the PETs going",
              code == 0 and "gets" in done.get("kinds_out", []) and "idiograph-gets.json" not in names
              and any("P2 - Orrin" in n for n in done.get("notes", []))
              and "P1 - Tamsin/Working/P1 - Tamsin - EN & ES.themes.json" in names, err or json.dumps(done)[:300])
        code, _, err = run("--root", str(root), "project", "send", "--to", str(out_dir / "refused.idiograph"),
                           "--participant", "Tamsin", "--with", "gets")
        check("258: GETs asked for with a participant not sent are refused, nothing written",
              code == 1 and "GETs hold P2 - Orrin" in err and not (out_dir / "refused.idiograph").exists(), err)
        code, done, err = run_json("--root", str(root), "project", "send", "--to", str(out_dir / "all.idiograph"),
                                   "--leave-out", "pets", "--with", "audio,gets")
        names = held_in(out_dir / "all.idiograph") if code == 0 else []
        check("258: every participant with GETs and recordings asked for and the PETs left out",
              code == 0 and "idiograph-gets.json" in names and "Night swimming - GETs.docx" in names
              and "P1 - Tamsin/Source/Initial/Source/P1-Initial.m4a" in names
              and not any("themes" in n or "PET draft" in n or "_Archive" in n for n in names)
              and not any(second in n for n in names), err or str(names))

        # 6. refusals: a name that is no participant's, a word that is no kind, a kind asked and left out
        for args, word in ((["--participant", "Nobody"], "no participant Nobody"),
                           (["--leave-out", "boards"], "not a kind"),
                           (["--leave-out", "audio", "--with", "audio"], "both asked for and left out")):
            code, _, err = run("--root", str(root), "project", "send", "--to", str(out_dir / "x.idiograph"), *args)
            check(f"258: {' '.join(args)} is refused in one line, nothing written",
                  code == 1 and word in err and not (out_dir / "x.idiograph").exists(), err)

        # 7. the MCP tool and the route take the same options
        mcp = mcp_server.Server(root=str(root), config=str(config_file))
        res = mcp.call(mcp.by_name["project_send"], {"to": str(out_dir / "mcp.idiograph"), "participants": ["Tamsin"],
                                                      "blind": True, "dry_run": True})
        text = json.dumps(res["content"])
        check("258: MCP's project_send takes participants and blind, its dry run listing the files and writing nothing",
              not res["isError"] and "P1 - Tamsin - EN & ES.xlsx" in text and "themes" not in text.split("Left out")[0]
              and "Left out, PETs" in text
              and not (out_dir / "mcp.idiograph").exists(), text[:300])
        server_mod.CONFIG_PATH, server_mod.ROOT_OVERRIDE, server_mod.STATE_MEMORY = config_file, None, {"recent": []}
        routes.add_project(root)
        to = out_dir / "route"
        dry = routes.api_send_project({"root": str(root), "to": str(to), "participants": ["Tamsin"], "blind": True,
                                       "dry_run": True})
        answer = routes.api_send_project({"root": str(root), "to": str(to), "participants": ["Tamsin"], "blind": True})
        check("258: the route's send takes the same options, its dry run writing nothing, and writes the same files",
              dry.get("dry_run") is True and dry.get("listed") == done_blind
              and answer.get("sent") is True and answer.get("participants") == ["P1 - Tamsin"]
              and held_in(to.with_suffix(".idiograph")) == held_in(sent), json.dumps(answer)[:300])

        # 8. design E (23 October): PETs and recordings chosen participant by participant, Tamsin with her
        # PETs and recording, Orrin with his statements alone
        code, done, err = run_json("--root", str(root), "project", "send", "--to", str(out_dir / "mixed.idiograph"),
                                   "--participant", "Tamsin", "--participant", "Orrin", "--pets", "Tamsin",
                                   "--audio", "Tamsin", "--leave-out", "gets")
        names = held_in(out_dir / "mixed.idiograph") if code == 0 else []
        check("258: a mixed send packs Tamsin's workbook, board, draft, tables and recording, and Orrin's workbook "
              "and progress file alone",
              code == 0 and sorted(names) == sorted([
                  server_mod.PROJECT_FILE,
                  "P1 - Tamsin/P1 - Tamsin - EN & ES.xlsx", "P1 - Tamsin/Working/P1 - Tamsin - EN & ES.progress.json",
                  "P1 - Tamsin/Working/P1 - Tamsin - EN & ES.themes.json",
                  "P1 - Tamsin/Working/P1 - Tamsin - PET draft (Board 1).md",
                  "P1 - Tamsin/P1 - Tamsin - Board 1 - PETs.docx", "P1 - Tamsin/P1 - Tamsin.pdf",
                  "P1 - Tamsin/Source/Initial/Source/P1-Initial.m4a",
                  "P2 - Orrin/P2 - Orrin - EN & ES.xlsx", "P2 - Orrin/Working/P2 - Orrin - EN & ES.progress.json"])
              and done.get("each") == {"P1 - Tamsin": ["pets", "audio"], "P2 - Orrin": []}, err or str(names))
        with zipfile.ZipFile(out_dir / "mixed.idiograph") as zf:
            tamsin = json.loads(zf.read(project_pack.TOP + "P1 - Tamsin/Working/P1 - Tamsin - EN & ES.progress.json"))
            orrin = json.loads(zf.read(project_pack.TOP + "P2 - Orrin/Working/P2 - Orrin - EN & ES.progress.json"))
            head = json.loads(zf.read(project_pack.MANIFEST))
        check("258: in a mixed send Tamsin's progress file keeps its History and Orrin's, his PETs out, goes without it",
              "edits" in tamsin and "edits" not in orrin and "assignments" not in orrin
              and orrin.get("complete") == {"at": "2026-10-20T10:00:00+01:00"}
              and head["chosen"].get("each") == {"P1 - Tamsin": ["pets", "audio"], "P2 - Orrin": []},
              json.dumps(orrin) + json.dumps(head.get("chosen")))
        for args, word in ((["--participant", "Tamsin", "--pets", "Orrin"], "not among the participants sent"),
                           (["--pets", "Tamsin", "--leave-out", "pets"], "left out for everyone"),
                           (["--audio", "Tamsin", "--with", "audio"], "asked for everyone"),
                           (["--audio", "Nobody"], "no participant Nobody")):
            code, _, err = run("--root", str(root), "project", "send", "--to", str(out_dir / "y.idiograph"), *args)
            check(f"258: {' '.join(args)} is refused in one line, nothing written",
                  code == 1 and word in err and not (out_dir / "y.idiograph").exists(), err)

        # 9. Whole project without its recordings: everything a plain send holds but the recording
        code, done, err = run_json("--root", str(root), "project", "send", "--to", str(out_dir / "noaudio.idiograph"),
                                   "--leave-out", "audio")
        names = held_in(out_dir / "noaudio.idiograph") if code == 0 else []
        # every file a plain send holds, the writers' lock never among them
        own = {k: v for k, v in files(root).items() if not project_pack.left_out(PurePosixPath(k))}
        whole = sorted(k for k in own if not k.endswith(".m4a"))
        with zipfile.ZipFile(out_dir / "noaudio.idiograph") as zf:
            project_sent = json.loads(zf.read(project_pack.TOP + server_mod.PROJECT_FILE))
        check("258: --leave-out audio alone sends the whole project, notes, Source, GETs, _Archive and History as they "
              "are, folders by their own names, and no recording",
              code == 0 and names == whole and "idiograph-gets.json" in names
              and f"{a_folder}/Working/memo.md" in names and f"{a_folder}/Source/Initial/raw export.csv" in names
              and f"{a_folder}/_Archive/older.xlsx" in names and not any(n.endswith(".m4a") for n in names)
              and "names" in project_sent and done.get("whole") is True and done.get("kinds_out") == ["audio"]
              and len(done.get("left", {}).get("audio", [])) == 1,
              err or str(sorted(set(names) ^ set(whole))) + json.dumps(done)[:300])

        # 10. the list the card draws itself from, Tamsin with a recording and Orrin with none
        code, listed, err = run_json("--root", str(root), "project", "send", "--list")
        rec = 256 * 40
        rows = {r["label"]: r for r in listed.get("participants", [])}
        check("258: project send --list answers each participant's PETs and recordings and their size, and the whole "
              "project's, writing nothing",
              code == 0 and list(rows) == ["P1 - Tamsin", "P2 - Orrin"]
              and rows["P1 - Tamsin"]["pets"] is True and rows["P1 - Tamsin"]["audio"] is True
              and rows["P1 - Tamsin"]["audio_bytes"] == rec
              and rows["P2 - Orrin"]["pets"] is True and rows["P2 - Orrin"]["audio"] is False
              and rows["P2 - Orrin"]["audio_bytes"] == 0
              and listed.get("audio_bytes") == rec and listed.get("gets") is True
              and listed.get("bytes") == sum(len(v) for v in own.values())
              and listed.get("bytes_less_audio") == listed.get("bytes") - rec
              and second not in json.dumps(listed), err or json.dumps(listed)[:400])
        res = mcp.call(mcp.by_name["project_send_list"], {})
        check("258: MCP's project_send_list and the route's /api/send-list answer the same",
              not res["isError"] and support.plain(res["structuredContent"])["participants"] == listed["participants"]
              and "P1 - Tamsin: PETs, recordings 10 KB." in support.unfenced(res["content"][0]["text"])
              and "P2 - Orrin: PETs." in support.unfenced(res["content"][0]["text"])
              and routes.api_send_list({"root": str(root)})["participants"] == listed["participants"],
              json.dumps(res["content"])[:300])
        answer = routes.api_send_project({"root": str(root), "to": str(out_dir / "route-mixed"), "participants": ["Tamsin"],
                                          "pets": ["Tamsin"], "audio": "Tamsin", "leave_out": ["gets"]})
        check("258: the route takes pets and audio by participant",
              answer.get("each") == {"P1 - Tamsin": ["pets", "audio"]}
              and "P1 - Tamsin/Source/Initial/Source/P1-Initial.m4a" in held_in(out_dir / "route-mixed.idiograph"),
              json.dumps(answer)[:300])

        # 11. Share a copy's card on Home (design E): its choices give exactly the sends the API makes
        both = ["P1 - Tamsin", "P2 - Orrin"]
        routes.api_send_project({"root": str(root), "to": str(out_dir / "plain-route")})
        routes.api_send_project({"root": str(root), "to": str(out_dir / "card-whole"),
                                 "card": {"whole": True, "audio": True}})
        check("258: the card's Whole project with Audio recordings ticked is the plain send, the whole project as it is",
              held_in(out_dir / "card-whole.idiograph") == held_in(out_dir / "plain-route.idiograph")
              and a_folder + "/_Archive/older.xlsx" in held_in(out_dir / "card-whole.idiograph"))
        answer = routes.api_send_project({"root": str(root), "to": str(out_dir / "card-whole-quiet"),
                                          "card": {"whole": True, "audio": False}})
        check("258: the card's Whole project with Audio recordings unticked is the whole project less its recordings",
              answer.get("whole") is True and held_in(out_dir / "card-whole-quiet.idiograph") == held_in(out_dir / "noaudio.idiograph"),
              json.dumps(answer)[:300])
        answer = routes.api_send_project({"root": str(root), "to": str(out_dir / "card-mixed"), "card": {
            "participants": both, "pets": ["P1 - Tamsin"], "audio": ["P1 - Tamsin"]}})
        check("258: the card's Choose participants with Tamsin's PETs and recording and Orrin's statements alone is the "
              "mixed send, no GETs",
              answer.get("each") == {"P1 - Tamsin": ["pets", "audio"], "P2 - Orrin": []}
              and held_in(out_dir / "card-mixed.idiograph") == held_in(out_dir / "mixed.idiograph")
              and "idiograph-gets.json" not in held_in(out_dir / "card-mixed.idiograph"), json.dumps(answer)[:300])
        answer = routes.api_send_project({"root": str(root), "to": str(out_dir / "card-blind"), "card": {
            "participants": ["P1 - Tamsin"], "pets": [], "audio": []}})
        check("258: the card with Tamsin alone and nothing else ticked is the blinded send, her workbook and progress "
              "file alone",
              answer.get("participants") == ["P1 - Tamsin"] and held_in(out_dir / "card-blind.idiograph") == held_in(sent),
              json.dumps(answer)[:300])
        try:
            routes.api_send_project({"root": str(root), "to": str(out_dir / "card-none"), "card": {"participants": []}})
            refused = False
        except server_mod.WorkbookError:
            refused = True
        check("258: the card with no participant ticked is refused, nothing written",
              refused and not (out_dir / "card-none.idiograph").exists())

        class Download:
            """A browser's request to the download, its answer kept."""
            def __init__(self):
                import io
                self.wfile, self.status, self.close_connection = io.BytesIO(), None, False
            def send_response(self, code):
                self.status = code
            def send_header(self, *_):
                pass
            def end_headers(self):
                pass
            def _json(self, data, code):
                self.status, self.error = code, data

        got = Download()
        routes.send_zip(got, {"root": str(root), "card": json.dumps({"participants": ["P1 - Tamsin"]})})
        browser = out_dir / "browser.idiograph"
        browser.write_bytes(got.wfile.getvalue())
        check("258: a browser's download takes the same choice, Tamsin alone the blinded file",
              got.status == 200 and held_in(browser) == held_in(sent), str(got.status))
        got = Download()
        routes.send_zip(got, {"root": str(root), "card": json.dumps({"whole": True, "audio": True})})
        browser.write_bytes(got.wfile.getvalue())
        check("258: a browser's download of Whole project with its recordings is the plain send",
              got.status == 200 and held_in(browser) == held_in(out_dir / "plain-route.idiograph"), str(got.status))
        check("258: the source project is byte for byte as it was after every send", files(root) == before)

        # 12. the current board alone (Adam, 23 October: "just include the current board, whichever number that
        # is"): Tamsin with three boards, Board 2 marked the Current board, Board 3 on the canvas
        for _ in range(2):
            code, _, err = run("--root", str(root), "board", "new", "Tamsin", "--from", str(plan), "--note", "Another board",
                               "--tool", "Claude Code")
            check("258: another board is made on Tamsin's canvas for the current-board fixture", code == 0, err)
        code, _, err = run("--root", str(root), "board", "current", "Tamsin", "Board 2", "--note", "Go with Board 2",
                           "--tool", "Claude Code")
        check("258: Board 2 is marked Tamsin's Current board", code == 0, err)
        (a_case / "Working" / "P1 - Tamsin - PET draft (Board 2).md").write_text("# Dark water, the second\n", encoding="utf-8")
        (a_case / "P1 - Tamsin - PETs (Board 2, 6 Oct 14.20).docx").write_bytes(b"PK\x03\x04 Board 2's table stands in here")
        (a_case / "P1 - Tamsin - PETs (Board 3).docx").write_bytes(b"PK\x03\x04 Board 3's table stands in here")
        before = files(root)
        code, listed, err = run_json("--root", str(root), "project", "send", "--list")
        rows = {r["label"]: r for r in listed.get("participants", [])}
        check("258: --list gives each participant's boards and the current one, Tamsin three with Board 2 current",
              code == 0 and [(b["kind"], b["boards"], b["current"]) for b in rows["P1 - Tamsin"]["boards"]] == [("PETs", 3, "Board 2")]
              and [(b["boards"], b["current"]) for b in rows["P2 - Orrin"]["boards"]] == [(1, "Board 1")], err or json.dumps(listed)[:400])
        cur = ("--root", str(root), "project", "send", "--participant", "Tamsin", "--pets", "Tamsin")
        code, dry, err = run_json(*cur, "--to", str(out_dir / "cur-dry.idiograph"), "--boards", "current", "--dry-run")
        check("258: the dry run of --boards current names the board that goes, Board 2 of Tamsin's three",
              code == 0 and [(b["participant"], b["kind"], b["board"], b["of"]) for b in dry.get("boards", [])]
              == [("P1 - Tamsin", "PETs", "Board 2", 3)] and dry.get("board_choice") == "current"
              and not (out_dir / "cur-dry.idiograph").exists(), err or json.dumps(dry)[:400])
        code, said, err = run(*cur, "--to", str(out_dir / "cur-dry.idiograph"), "--boards", "current", "--dry-run")
        check("258: the dry run's lines say the current board alone, Board 2 of 3 boards",
              code == 0 and "P1 - Tamsin's PETs, Board 2 of 3 boards." in said and second not in said, said + err)
        code, done, err = run_json(*cur, "--to", str(out_dir / "current.idiograph"), "--boards", "current")
        current_file = out_dir / "current.idiograph"
        names = held_in(current_file) if current_file.is_file() else []
        with zipfile.ZipFile(current_file) as zf:
            sent_themes = json.loads(zf.read(project_pack.TOP + "P1 - Tamsin/Working/P1 - Tamsin - EN & ES.themes.json"))
            sent_progress = json.loads(zf.read(project_pack.TOP + "P1 - Tamsin/Working/P1 - Tamsin - EN & ES.progress.json"))
            head = json.loads(zf.read(project_pack.MANIFEST))
        check("258: --boards current packs Tamsin's one board, Board 2, its own id and name, marked current and the Current "
              "board, without its restore points",
              code == 0 and [b["name"] for b in sent_themes["boards"]] == ["Board 2"]
              and sent_themes["current"] == sent_themes["chosen"] == sent_themes["boards"][0]["id"]
              and "history" not in sent_themes["boards"][0] and head["chosen"].get("boards") == "current",
              err or json.dumps(sent_themes)[:300])
        check("258: --boards current sends the progress file without its History, the statements' completion kept",
              not any(k in sent_progress for k in ("edits", "assignments")) and sent_progress.get("complete")
              and "P1 - Tamsin/Working/P1 - Tamsin - EN & ES.progress.json" in done.get("left", {}).get("history", []),
              json.dumps(sent_progress)[:300])
        check("258: --boards current keeps Board 2's draft and table alone, the other boards' and the untold ones left out",
              "P1 - Tamsin/Working/P1 - Tamsin - PET draft (Board 2).md" in names
              and "P1 - Tamsin/P1 - Tamsin - PETs (Board 2, 6 Oct 14.20).docx" in names
              and not any(n.endswith(("(Board 1).md", "(Board 3).docx", "Board 1 - PETs.docx", "Tamsin.pdf")) for n in names)
              and len(done.get("left", {}).get("boards", [])) == 4, str(names) + json.dumps(done.get("left", {}))[:300])
        code, every, err = run_json(*cur, "--to", str(out_dir / "every.idiograph"), "--boards", "all")
        code2, plain, err2 = run_json(*cur, "--to", str(out_dir / "plain-boards.idiograph"))
        with zipfile.ZipFile(out_dir / "every.idiograph") as zf:
            all_themes = json.loads(zf.read(project_pack.TOP + "P1 - Tamsin/Working/P1 - Tamsin - EN & ES.themes.json"))
        check("258: --boards all is the send as before, every board",
              code == 0 and code2 == 0 and held_in(out_dir / "every.idiograph") == held_in(out_dir / "plain-boards.idiograph")
              and len(all_themes["boards"]) == 3, err + err2)
        code, _, err = run("project", "open-copy", str(current_file), "--into", str(into))
        opened = into / "Night swimming copy 2" if (into / "Night swimming copy 2").is_dir() else into / "Night swimming copy"
        code2, boards_copy, err2 = run_json("--root", str(opened), "board", "list", "Tamsin")
        check("258: the copy opens with that one board, Board 2, the Current board and on the canvas",
              code == 0 and code2 == 0 and [(b["name"], b["current"], b["canvas"]) for b in boards_copy.get("boards", [])]
              == [("Board 2", True, True)], err + err2 + json.dumps(boards_copy)[:300])
        res = mcp.call(mcp.by_name["project_send"], {"to": str(out_dir / "mcp-cur.idiograph"), "participants": ["Tamsin"],
                                                      "pets": ["Tamsin"], "boards": "current", "dry_run": True})
        answer = routes.api_send_project({"root": str(root), "to": str(out_dir / "route-cur"), "participants": ["Tamsin"],
                                          "pets": ["Tamsin"], "boards": "current"})
        check("258: MCP's project_send and the route take boards current, the route's file Board 2 alone",
              not res["isError"] and "Board 2 of 3 boards" in json.dumps(res["content"])
              and [b["board"] for b in answer.get("boards", [])] == ["Board 2"] and answer.get("board_choice") == "current"
              and held_in(out_dir / "route-cur.idiograph") == names, json.dumps(res["content"])[:300] + json.dumps(answer)[:300])
        code, whole, err = run_json("--root", str(root), "project", "send", "--to", str(out_dir / "whole-cur.idiograph"),
                                    "--boards", "current")
        with zipfile.ZipFile(out_dir / "whole-cur.idiograph") as zf:
            whole_themes = json.loads(zf.read(project_pack.TOP + a_folder + "/Working/" + a_book.stem + ".themes.json"))
        check("258: --boards current alone is the whole project with each participant's current board alone",
              code == 0 and whole.get("whole") is True and sorted((b["participant"], b["board"]) for b in whole.get("boards", []))
              == [("P1 - Tamsin", "Board 2"), ("P2 - Orrin", "Board 1")] and [b["name"] for b in whole_themes["boards"]] == ["Board 2"],
              err or json.dumps(whole)[:300])
        check("258: --boards on Share a copy's card is a send's option",
              routes.card_options({"participants": ["P1 - Tamsin"], "pets": ["P1 - Tamsin"], "boards": "current"}).get("boards")
              == "current" and routes.card_options({"whole": True, "boards": "current"}) == {"boards": "current"})
        check("258: the source project is byte for byte as it was after the current-board sends", files(root) == before)
    finally:
        server_mod.CONFIG_PATH, server_mod.ROOT_OVERRIDE, server_mod.STATE_MEMORY = kept
