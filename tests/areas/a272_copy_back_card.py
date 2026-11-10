"""Area 272: Open a shared copy knowing a copy of one of his projects coming back (26 October 2026, Adam's
option A for the app's part of train 61's return journey). The page reads the file with /api/open-sent's
`check`, which says the project it belongs to, from a path or from a browser's file chooser, and says
nothing for a stranger's file. Add its boards calls /api/boards-in, its dry run first, writing nothing,
then for real: each board comes in not current, its note saying whose copy, when it was sent and how its
statements came (copyback2, 8 November 2026), the file's name kept in its origin and History, and nothing else in the
project changes. Open as its own project still opens the copy as Open a shared copy always has, named as
the other analyst's, and the project it came from is left as it was.

The fixtures are invented: a project on flying kites in winter, two made-up participants."""
from __future__ import annotations

import base64
import json
import shutil
from pathlib import Path

from .a260_boards_come_back import make_workbook, set_statement
from .support import check


def test_copy_back_card(scratch: Path):
    print("\n272. Open a shared copy and a copy coming back: recognised, its boards added not current with the "
          "short note, or opened as its own project as before (26 October)")
    import cli
    import locks
    import server as server_mod
    import idiograph_routes as routes

    base = scratch / "copy-back-272"
    shutil.rmtree(base, ignore_errors=True)
    root = base / "Kite flying"
    root.mkdir(parents=True)
    (root / server_mod.PROJECT_FILE).write_text(json.dumps({
        "name": "Kite flying", "research_question": "How do people live flying kites in winter?",
        "agents": {"allowed": True, "at": "2026-10-26T09:00:00+00:00"}}), encoding="utf-8")
    a_book = make_workbook(root, "P1 - Ysolde", "Ysolde")
    make_workbook(root, "P2 - Corran", "Corran")
    stranger_root = base / "Kite making"
    stranger_root.mkdir()
    (stranger_root / server_mod.PROJECT_FILE).write_text(json.dumps({
        "name": "Kite making", "agents": {"allowed": True, "at": "2026-10-26T09:00:00+00:00"}}), encoding="utf-8")
    make_workbook(stranger_root, "P1 - Ysolde", "Ysolde")
    config_file = base / "config-272.json"
    config_file.write_text(json.dumps({"projects": [{"root": str(root)}], "interviewer": "Interviewer", "corpus": "",
                                       "gravity_reference": "", "corpus_exclude": []}), encoding="utf-8")
    curt_config = base / "curt-272.json"
    curt_config.write_text(json.dumps({"projects": [], "interviewer": "Interviewer", "corpus": "",
                                       "gravity_reference": "", "corpus_exclude": []}), encoding="utf-8")
    out_dir, curt_into, into = base / "out", base / "curt", base / "into"
    for d in (out_dir, curt_into, into):
        d.mkdir()

    def run(cfg, *args):
        return cli.run(["--config", str(cfg), *args])

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
        code, _, err = run(config_file, "--root", str(root), "board", "new", "Ysolde", "--from", str(plan),
                           "--note", "His first board", "--tool", "Claude Code")
        check("272: his own board is made on Ysolde's canvas for the fixture", code == 0, err)
        sent = out_dir / "Kite flying.idiograph"
        code, _, err = run(config_file, "--root", str(root), "project", "send", "--to", str(sent), "--participant", "Ysolde", "--blind")
        check("272: Ysolde is sent to Curt, blinded", code == 0, err)
        code, _, err = run(curt_config, "project", "open-copy", str(sent), "--into", str(curt_into))
        copy = curt_into / "Kite flying"
        c_book = copy / "P1 - Ysolde" / "P1 - Ysolde - EN & ES.xlsx"
        set_statement(c_book, 7, "Winding in as a return home too soon")
        curt_plan = base / "curt.json"
        curt_plan.write_text(json.dumps({"pets": [{"title": "The kite as the body's elsewhere", "members": ["S2", "S3"]},
                                                  {"title": "Cold as contact", "members": ["S1"]}]}), encoding="utf-8")
        code2, _, err2 = run(curt_config, "--root", str(copy), "board", "new", "Ysolde", "--from", str(curt_plan),
                             "--note", "Curt's grouping", "--tool", "Claude Code")
        curt_note = "Grouped by how the cold and the climb feel.\nThe ending kept apart on purpose."
        code4, _, err4 = run(curt_config, "--root", str(copy), "board", "note", "Ysolde", "Board 1", curt_note,
                             "--note", "Curt's reasons", "--tool", "Claude Code")
        check("272: Curt writes his reasons in his board's note in the copy", code4 == 0, err4)
        back = out_dir / "Back from Curt.idiograph"
        code3, _, err3 = run(curt_config, "--root", str(copy), "project", "send", "--to", str(back))
        check("272: Curt's copy opened, his board made in it with one statement reworded, and sent back",
              code == 0 and code2 == 0 and code3 == 0 and back.is_file(), err + err2 + err3)
        stranger = out_dir / "Kite making.idiograph"
        code, _, err = run(config_file, "--root", str(stranger_root), "project", "send", "--to", str(stranger))
        check("272: a stranger's project is sent, for the file that is not his", code == 0, err)

        server_mod.CONFIG_PATH, server_mod.ROOT_OVERRIDE = config_file, None
        pid = routes.project_id(root)
        before = files(root)
        board1 = themes_of(a_book)["boards"][0]

        # 1. the file read: a copy coming back names his project, by a path or a browser's upload, a stranger's none
        said = routes.api_open_sent({"file": str(back), "check": True})
        data = base64.b64encode(back.read_bytes()).decode("ascii")
        upload = routes.api_open_sent({"data": data, "name": back.name, "check": True})
        check("272: the copy coming back is recognised as Kite flying's, from its path and from a browser's upload",
              said.get("returning") == {"root": pid, "name": "Kite flying"}
              and upload.get("returning") == said["returning"] and said.get("checked") is True, json.dumps(said))
        other = routes.api_open_sent({"file": str(stranger), "check": True})
        own = routes.api_open_sent({"file": str(sent), "check": True})
        check("272: a stranger's file, and the project's own send, are no copy coming back",
              other.get("checked") is True and "returning" not in other and "returning" not in own, json.dumps(other))

        # 2. the card's dry run writes nothing and answers each participant's workbook for the landing
        dry = routes.api_boards_in({"root": pid, "data": data, "name": back.name, "from_name": "Curt", "dry_run": True})
        row = (dry.get("participants") or [{}])[0]
        b = (row.get("boards") or [{}])[0]
        check("272: the dry run from the upload lists Curt's board for Ysolde, 2 of 3 matching, and writes nothing",
              row.get("case") == "P1 - Ysolde" and b.get("matched") == 2 and b.get("statements") == 3
              and b.get("name", "").startswith("Curt's board, ") and row.get("path", "").endswith("P1 - Ysolde - EN & ES.xlsx")
              and files(root) == before, json.dumps(dry)[:400])

        # 3. Add board: in, not current, the short note, the file's name in its origin and History, nothing else
        done = routes.api_boards_in({"root": pid, "data": data, "name": back.name, "from_name": "Curt"})
        got = themes_of(a_book)
        new = got["boards"][-1] if len(got["boards"]) == 2 else {}
        day = routes.day_said(dry.get("sent") or "")
        check("272: Add board brings Curt's board in after Board 1, not current and not on the canvas",
              done.get("dry_run") is False and got["boards"][0] == board1 and got.get("current") == board1["id"]
              and got.get("chosen") in (None, board1["id"]) and new.get("name") == b.get("name"), json.dumps(got)[:300])
        check("272: its note is the short line, whose copy, when sent and how many match, with no file name, then "
              "Curt's own note from the copy whole on the next line",
              new.get("note", "").startswith(f"Curt's copy, sent {day}: 2 statements as sent")
              and new["note"].endswith(f"\n{curt_note}"), new.get("note", ""))
        check("272: the file's own name, as he chose it, is kept in its origin and its History",
              new.get("origin", {}).get("file") == back.name
              and [r["name"] for r in new.get("history", [])] == [f"Brought in from {back.name}"], json.dumps(new.get("origin")))
        after = files(root)
        themes_rel = "P1 - Ysolde/Working/P1 - Ysolde - EN & ES.themes.json"
        after.pop(themes_rel)
        check("272: nothing else in the project changed", after == {k: v for k, v in before.items() if k != themes_rel})

        # 4. Open as its own project opens the copy as today, named as Curt's, his project left as it was
        before = files(root)
        opened = routes.api_open_sent({"file": str(back), "into": str(into), "from_name": "Curt"})
        folder = Path(opened.get("folder") or "")
        check("272: Open as its own project opens the copy in a new folder, named as Curt's, and lists it",
              opened.get("opened") is not False and folder.is_dir() and opened.get("name") == "Kite flying, Curt's copy"
              and any(p.get("name") == "Kite flying, Curt's copy" for p in opened.get("projects", [])), json.dumps(opened)[:300])
        check("272: and Kite flying is left as it was", files(root) == before)
        plain = routes.api_open_sent({"file": str(stranger), "into": str(into)})
        check("272: a stranger's file still opens as a copy as before", plain.get("name") == "Kite making"
              and Path(plain.get("folder") or "").is_dir(), json.dumps(plain)[:200])
    finally:
        server_mod.CONFIG_PATH, server_mod.ROOT_OVERRIDE, server_mod.STATE_MEMORY = kept
