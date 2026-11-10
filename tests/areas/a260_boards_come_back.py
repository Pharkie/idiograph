"""Area 260: a shared copy coming back (26 October 2026, Adam's ruling of 23 October: a copy he sent and
the other analyst sent back is "conceptually the same project"). A send gives the project file its own id
when it has none, and the file names it, with a print of each statement sent. A copy opened keeps them in
its project file's `copy_of`, taking no id of the project's as its own. `project boards-in` adds the
copy's boards to the same participant in the project it came from: its dry run lists each board, its new
name and every statement it cannot match, the import adds each one the next board, not current, named
whose and when, with its History's revision naming the file, every card in its place, a statement edited in
between, or the other analyst's own rewording, linked by its key (copyback, 6 November 2026, where it waited under
Not placed before), and nothing else in the project changing. A
second run adds nothing, a file from another project or the project's own send is refused, and so is a
participant the project does not have. A file from before the ids is matched by the project's name. The
MCP tool and the route answer as the command line does, and `board compare` takes the board brought in.

The fixtures are invented: a project on flying kites in winter, two made-up participants."""
from __future__ import annotations

import hashlib
import json
import shutil
import zipfile
from pathlib import Path

import openpyxl

from .support import check
from . import support


def make_workbook(root: Path, folder: str, speaker: str) -> Path:
    """A made-up participant's annotated workbook with three statements, one to a row."""
    import workbook as wb_mod
    case = root / folder
    (case / "Source").mkdir(parents=True)
    raw = openpyxl.Workbook()
    first = raw.active
    first.title = "Initial"
    first.append(["Name", "Timestamp", "Transcript"])
    first.append(["Interviewer", "00:00:04", "What is it like to fly a kite in winter?"])
    first.append([speaker, "00:00:09", "The line hums in my gloves and the cold goes up it."])
    first.append(["Interviewer", "00:00:20", "And when it climbs?"])
    first.append([speaker, "00:00:26", "I forget my feet, I am up there with it."])
    first.append(["Interviewer", "00:00:40", "And bringing it down?"])
    first.append([speaker, "00:00:46", "Winding in feels like coming home too early."])
    source = case / "Source" / f"{folder} - interview.xlsx"
    raw.save(source)
    book = wb_mod.create_from_source(source, case / f"{folder} - EN & ES.xlsx")
    wb = openpyxl.load_workbook(book, rich_text=True)
    ws = wb.worksheets[0]
    cols = wb_mod.detect_columns(ws)
    ws.cell(3, cols["es"]).value = "Feeling the cold travel down the line"
    ws.cell(3, cols["kq"]).value = "“the cold goes up it”"
    ws.cell(5, cols["es"]).value = "Leaving the body behind as the kite climbs"
    ws.cell(5, cols["kq"]).value = "“I forget my feet”"
    ws.cell(7, cols["es"]).value = "Ending the flight as an early return home"
    wb.save(book)
    return book


def set_statement(book: Path, row: int, text: str) -> None:
    """A statement of the invented workbook reworded, as an analyst's edit leaves it."""
    import workbook as wb_mod
    wb = openpyxl.load_workbook(book, rich_text=True)
    ws = wb.worksheets[0]
    ws.cell(row, wb_mod.detect_columns(ws)["es"]).value = text
    wb.save(book)


def rezip(src: Path, dst: Path, head_fn=None, rename=None, project_fn=None) -> None:
    """A sent file written again with its list's head changed by `head_fn`, every path's `rename` pair
    swapped, and its project file changed by `project_fn`, each file's print kept true."""
    import project_pack
    import server as server_mod
    with zipfile.ZipFile(src) as zf:
        head = json.loads(zf.read(project_pack.MANIFEST))
        held = {n[len(project_pack.TOP):]: zf.read(n) for n in zf.namelist() if n.startswith(project_pack.TOP)}
    out = {}
    for rel, data in held.items():
        if rel == server_mod.PROJECT_FILE and project_fn:
            data = json.dumps(project_fn(support.plain(json.loads(data)))).encode("utf-8")
        if rename:
            rel = rel.replace(*rename)
        out[rel] = data
    head["files"] = [{"path": rel, "bytes": len(d), "sha256": hashlib.sha256(d).hexdigest()} for rel, d in out.items()]
    if head_fn:
        head = head_fn(head)
    with zipfile.ZipFile(dst, "w") as zf:
        zf.writestr(project_pack.MANIFEST, json.dumps(head))
        for rel, data in out.items():
            zf.writestr(project_pack.TOP + rel, data)


def test_boards_come_back(scratch: Path):
    print("\n260. A shared copy coming back: its boards added to the project it came from")
    import cli
    import locks
    import mcp_server
    import project_pack
    import server as server_mod
    import idiograph_routes as routes

    base = scratch / "back-260"
    shutil.rmtree(base, ignore_errors=True)
    root = base / "Kite flying"
    root.mkdir(parents=True)
    project_json = {"name": "Kite flying", "research_question": "How do people live flying kites in winter?",
                    "agents": {"allowed": True, "at": "2026-10-26T09:00:00+00:00"}}
    (root / server_mod.PROJECT_FILE).write_text(json.dumps(project_json), encoding="utf-8")
    a_book = make_workbook(root, "P1 - Ysolde", "Ysolde")
    b_book = make_workbook(root, "P2 - Corran", "Corran")
    config_file = base / "config-260.json"
    config_file.write_text(json.dumps({"projects": [], "interviewer": "Interviewer", "corpus": "",
                                       "gravity_reference": "", "corpus_exclude": []}), encoding="utf-8")
    out_dir, into = base / "out", base / "into"
    out_dir.mkdir()
    into.mkdir()

    def run(*args):
        return cli.run(["--config", str(config_file), *args])

    def run_json(*args):
        code, out, err = run("--json", *args)
        got = support.plain(json.loads(out)) if out.strip() else {}
        return code, (got if code == 0 else {}), err + (got.get("error", "") if code != 0 else "")

    def files(at: Path) -> dict:
        return {p.relative_to(at).as_posix(): p.read_bytes() for p in sorted(at.rglob("*"))
                if p.is_file() and p.name != locks.NAME}

    def themes_of(book: Path) -> dict:
        return json.loads((book.parent / "Working" / f"{book.stem}.themes.json").read_text(encoding="utf-8"))

    plan = base / "plan.json"
    plan.write_text(json.dumps({"pets": [{"title": "Cold on the line", "members": ["S1"]},
                                         {"title": "Up with the kite", "members": ["S2", "S3"]}]}), encoding="utf-8")
    kept = (server_mod.CONFIG_PATH, server_mod.ROOT_OVERRIDE, server_mod.STATE_MEMORY)
    try:
        for who in ("Ysolde", "Corran"):
            code, _, err = run("--root", str(root), "board", "new", who, "--from", str(plan), "--note", "His first board",
                               "--tool", "Claude Code")
            check(f"260: his own board is made on {who}'s canvas for the fixture", code == 0, err)

        # 1. the first send gives the project its own id, its dry run saying so and writing nothing
        before = files(root)
        code, dry, err = run_json("--root", str(root), "project", "send", "--to", str(out_dir), "--participant", "Ysolde",
                                  "--blind", "--dry-run")
        check("260: the first send's dry run says the project file would take an id, and writes nothing",
              code == 0 and dry.get("uid_made") is True and files(root) == before and not list(out_dir.iterdir()), err)
        code, said, err = run("--root", str(root), "project", "send", "--to", str(out_dir), "--participant", "Ysolde", "--blind")
        sent = out_dir / "Kite flying.idiograph"
        uid = json.loads((root / server_mod.PROJECT_FILE).read_text(encoding="utf-8")).get("uid")
        after = files(root)
        check("260: the send writes the id into the project file, every other key and file as it was",
              code == 0 and bool(uid) and support.plain(json.loads(after.pop(server_mod.PROJECT_FILE))) == dict(project_json, uid=uid)
              and after == {k: v for k, v in before.items() if k != server_mod.PROJECT_FILE}
              and "took an id of its own" in said, said + err)
        with zipfile.ZipFile(sent) as zf:
            head = json.loads(zf.read(project_pack.MANIFEST))
        check("260: the sent file names the project's id and prints Ysolde's three statements, no one else's",
              head.get("uid") == uid and list(head.get("statements", {})) == ["P1 - Ysolde"]
              and len(head["statements"]["P1 - Ysolde"]) == 3 and "copy_of" not in head, json.dumps(head)[:300])
        before_again = files(root)
        code, said, err = run("--root", str(root), "project", "send", "--to", str(out_dir / "second.idiograph"),
                              "--participant", "Ysolde", "--blind")
        check("260: a second send keeps the id and changes nothing", code == 0 and files(root) == before_again
              and "Nothing in the project changed." in said and "id" not in said.split("Nothing")[-1], said + err)

        # 2. opened as Curt's copy: the origin kept, no id of the project's taken as its own
        code, done, err = run_json("project", "open-copy", str(sent), "--into", str(into), "--from-name", "Curt")
        copy = into / "Kite flying"
        held = json.loads((copy / server_mod.PROJECT_FILE).read_text(encoding="utf-8")) if copy.is_dir() else {}
        check("260: the copy keeps the project it came from, its id, sent time and statements, and has no id of its own yet",
              code == 0 and held.get("copy_of", {}).get("uid") == uid and "uid" not in held
              and held["copy_of"].get("statements") == head["statements"] and held["copy_of"].get("sent") == head["sent"]
              and held.get("name") == "Kite flying, Curt's copy" and done.get("name") == "Kite flying, Curt's copy",
              err + json.dumps(held)[:300])

        # 3. Curt rewords one statement and makes his board, then Adam edits another in his project
        c_book = copy / "P1 - Ysolde" / "P1 - Ysolde - EN & ES.xlsx"
        set_statement(c_book, 7, "Winding in as a return home too soon")
        curt_plan = base / "curt.json"
        curt_plan.write_text(json.dumps({"pets": [{"title": "The kite as the body's elsewhere", "members": ["S2", "S3"]},
                                                  {"title": "Cold as contact", "members": ["S1"]}]}), encoding="utf-8")
        code, _, err = run("--root", str(copy), "board", "new", "Ysolde", "--from", str(curt_plan), "--note", "Curt's grouping",
                           "--tool", "Claude Code")
        check("260: Curt's board is made in his copy", code == 0, err)
        code, said, err = run("--root", str(copy), "project", "send", "--to", str(out_dir / "Back from Curt.idiograph"))
        back = out_dir / "Back from Curt.idiograph"
        with zipfile.ZipFile(back) as zf:
            back_head = json.loads(zf.read(project_pack.MANIFEST))
        copy_uid = json.loads((copy / server_mod.PROJECT_FILE).read_text(encoding="utf-8")).get("uid")
        check("260: the copy sent back takes its own id and names the project it came from",
              code == 0 and copy_uid and copy_uid != uid and back_head.get("uid") == copy_uid
              and back_head.get("copy_of", {}).get("uid") == uid, said + err)
        set_statement(a_book, 3, "Feeling the winter cold arrive through the line")
        before = files(root)
        board1 = themes_of(a_book)["boards"][0]

        # 4. the dry run lists the board, its new name and every statement not matched, and writes nothing
        code, dry, err = run_json("--root", str(root), "project", "boards-in", str(back), "--from-name", "Curt", "--dry-run")
        rows = dry.get("participants", [])
        b = rows[0]["boards"][0] if rows and rows[0].get("boards") else {}
        reasons = {s["key"]: s["reason"] for s in b.get("not_matched", [])}
        check("260: the dry run lists Curt's board for Ysolde alone, as Curt's board with its day, 1 of 3 matched",
              code == 0 and dry.get("matched_by") == "id" and [r["case"] for r in rows] == ["P1 - Ysolde"]
              and b.get("from") == "Board 1" and b.get("name", "").startswith("Curt's board, ")
              and b.get("matched") == 1 and b.get("statements") == 3 and files(root) == before, err + json.dumps(dry)[:500])
        check("260: the statement Adam edited since and Curt's own reworded one are listed as not matched, with their reasons",
              reasons == {"Initial:3:0": "Edited in this project since the copy was sent.",
                          "Initial:7:0": "Curt's own statement, edited, merged or added in the copy."}, json.dumps(reasons))
        code, said, err = run("--root", str(root), "project", "boards-in", str(back), "--from-name", "Curt", "--dry-run")
        check("260: its lines say what it would add, each card placed as in the copy, the two not read the same linked by "
              "their keys in this project's wording, and that nothing else would change",
              code == 0 and "it would add 1 board, not current" in said and "every one placed as in the copy" in said
              and "In this project's wording, linked to its statement by the key:" in said
              and "Initial:7:0 \"Winding in as a return home too soon\", here \"Ending the flight as an early return home\"" in said
              and "Nothing else in the project would change" in said, said + err)
        code, _, err = run("--root", str(root), "project", "boards-in", str(back), "--note", "Bring Curt's boards in")
        check("260: without --from-name nothing is brought in", code == 1 and "--from-name" in err and files(root) == before, err)
        code, _, err = run("--root", str(root), "project", "boards-in", str(back), "--from-name", "Curt")
        check("260: without his request nothing is brought in", code == 1 and "--note" in err and files(root) == before, err)

        # 5. brought in: the next board, not current, named whose and when, the rest of the project as it was
        code, done, err = run_json("--root", str(root), "project", "boards-in", str(back), "--from-name", "Curt",
                                   "--note", "Bring Curt's boards in", "--tool", "Claude Code")
        data = themes_of(a_book)
        boards = data["boards"]
        new = boards[-1] if len(boards) == 2 else {}
        placed = {m for g in new.get("groups", []) for m in g["members"]}
        check("260: Curt's board comes in after Board 1, not on the canvas and not current, its name whose and when",
              code == 0 and len(boards) == 2 and boards[0] == board1 and data.get("current") == board1["id"]
              and data.get("chosen") in (None, board1["id"]) and new.get("name") == b.get("name")
              and new.get("id") not in (None, board1["id"]), err + json.dumps(data)[:400])
        check("260: every card stays in its PET (copyback, 6 November 2026), the two not read the same linked by their keys, "
              "his wording now beside the copy's, none waiting under Not placed",
              placed == {"Initial:3:0", "Initial:5:0", "Initial:7:0"} and not new.get("ai")
              and new["cards"]["Initial:3:0"] == dict(new["cards"]["Initial:3:0"], text="Feeling the cold travel down the line",
                                                      live="Feeling the winter cold arrive through the line")
              and new["cards"]["Initial:7:0"].get("text") == "Winding in as a return home too soon"
              and new["cards"]["Initial:7:0"].get("live") == "Ending the flight as an early return home", json.dumps(new)[:600])
        check("260: its History records the import with the file's name, its origin and note say where it came from",
              [r["name"] for r in new.get("history", [])] == ["Brought in from Back from Curt.idiograph"]
              and new.get("origin", {}).get("who") == "Curt" and new["origin"].get("board") == "Board 1"
              and new["origin"].get("file") == "Back from Curt.idiograph"
              and new.get("note", "").startswith("Curt's copy, sent ") and new["note"].split("\n")[0].endswith(".")
              and "1 statement as sent" in new["note"],
              json.dumps({k: new.get(k) for k in ("origin", "note")}))
        after = files(root)
        themes_rel = "P1 - Ysolde/Working/P1 - Ysolde - EN & ES.themes.json"
        after.pop(themes_rel)
        check("260: nothing else in the project changed, Ysolde's workbook and progress, Corran's files and the project file "
              "byte for byte", after == {k: v for k, v in before.items() if k != themes_rel})
        code, statements, err = run_json("--root", str(root), "statements", "Ysolde")
        check("260: Ysolde's statements read as before, Adam's edit kept",
              code == 0 and [s["text"] for s in statements.get("statements", [])][0]
              == "Feeling the winter cold arrive through the line", err)

        # 6. a second run adds nothing, the board already in
        before = files(root)
        code, again, err = run_json("--root", str(root), "project", "boards-in", str(back), "--from-name", "Curt",
                                    "--note", "Bring Curt's boards in again")
        check("260: a second run brings in nothing, the board in the project already",
              code == 0 and again["participants"][0]["already"] == ["Board 1"] and not again["participants"][0]["boards"]
              and files(root) == before, err + json.dumps(again)[:300])

        # 7. board compare takes the board brought in
        code, cmp, err = run_json("--root", str(root), "board", "compare", "Ysolde", "Board 1", new.get("name", ""))
        check("260: board compare compares the board brought in with his own",
              code == 0 and [x["name"] for x in cmp.get("boards", [])] == ["Board 1", new.get("name")], err)

        # 8. refusals: his own send, another project's copy, a participant he does not have
        code, _, err = run("--root", str(root), "project", "boards-in", str(sent), "--from-name", "Curt", "--note", "x")
        check("260: the project's own send is refused as no copy coming back",
              code == 1 and "as it was sent, not a copy coming back" in err and files(root) == before, err)
        other = out_dir / "Other.idiograph"
        rezip(back, other, project_fn=lambda d: dict(d, copy_of=dict(d["copy_of"], uid="0123456789abcdef",
                                                                         name="Kite making")))
        code, _, err = run("--root", str(root), "project", "boards-in", str(other), "--from-name", "Curt", "--note", "x")
        check("260: a copy of another project is refused, naming it", code == 1 and "a copy of Kite making, not of Kite flying"
              in err and "Open a shared copy" in err and files(root) == before, err)
        stranger = out_dir / "Stranger.idiograph"
        rezip(back, stranger, rename=("P1 - Ysolde", "P3 - Brannoch"))
        code, _, err = run("--root", str(root), "project", "boards-in", str(stranger), "--from-name", "Curt", "--note", "x")
        check("260: a participant the project does not have is refused, naming them",
              code == 1 and "P3 - Brannoch is not in Kite flying" in err and files(root) == before, err)

        # 9. a file from an Idiograph before the ids is matched by the project's name, without the prints
        legacy = out_dir / "Legacy.idiograph"
        strip = lambda d: dict(d, copy_of={"name": "Kite flying", "opened": d["copy_of"]["opened"]})
        rezip(back, legacy, head_fn=lambda h: {k: v for k, v in h.items() if k not in project_pack.ORIGIN_KEYS},
              project_fn=lambda d: {k: v for k, v in strip(d).items() if k != "uid"})
        code, old, err = run_json("--root", str(root), "project", "boards-in", str(legacy), "--from-name", "Curt", "--dry-run")
        got = old.get("participants", [{}])[0].get("boards", [{}])
        check("260: a file from before the ids is matched by the project's name, its unmatched statements said plainly",
              code == 0 and old.get("matched_by") == "name" and got and {s["reason"] for s in got[0]["not_matched"]}
              == {"Reads differently in this project."} and files(root) == before, err + json.dumps(old)[:400])

        # 10. the MCP tool and the route answer as the command line does
        mcp = mcp_server.Server(root=str(root), config=str(config_file))
        res = mcp.call(mcp.by_name["project_boards_in"], {"file": str(legacy), "from_name": "Curt", "dry_run": True,
                                                          "request": "Look first"})
        mcp_said = support.plain(res.get("structuredContent") or {}) if not res.get("isError") else {}
        server_mod.CONFIG_PATH, server_mod.ROOT_OVERRIDE = config_file, str(root)
        routed = routes.api_boards_in({"root": str(root), "file": str(legacy), "from_name": "Curt", "dry_run": True})
        server_mod.CONFIG_PATH, server_mod.ROOT_OVERRIDE = kept[0], kept[1]
        strip_answer = lambda a: [[{k: x[k] for k in ("from", "name", "matched", "statements")} for x in r["boards"]]
                                  for r in a.get("participants", [])]
        check("260: MCP's project_boards_in and the route's /api/boards-in answer the dry run as the command line does",
              strip_answer(mcp_said) == strip_answer(old) == strip_answer(routed) and files(root) == before,
              json.dumps(res)[:300])

        # 11. opened alongside, a copy coming back says which project of his it belongs to
        settings = json.loads(config_file.read_text(encoding="utf-8"))
        settings["projects"].append({"root": str(root)})
        config_file.write_text(json.dumps(settings), encoding="utf-8")
        code, opened, err = run_json("project", "open-copy", str(back), "--into", str(into), "--from-name", "Curt",
                                     "--dry-run")
        check("260: open-copy of a copy coming back names the project it belongs to, under a name saying whose it is",
              code == 0 and opened.get("name") == "Kite flying, Curt's copy"
              and opened.get("returning") == "Kite flying", err + json.dumps(opened))
    finally:
        server_mod.CONFIG_PATH, server_mod.ROOT_OVERRIDE, server_mod.STATE_MEMORY = kept
