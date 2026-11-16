"""Area 397: the notes an agent's boards carried about their own making, taken off (sidebarcopy, 16 November 2026, Adam:
"archaeology and unhelpful").

What is checked, on the demo's three participants made a project: a board an agent makes through `board new` and a copy
through `board duplicate` and `gets duplicate` carry no note of who made them, when and for what request, while the
`made` mark keeps it for the board menu. For boards written with the notes the older way, a made one with an agent's
own note after it, a made one with none, a copy, and a note he wrote: the dry run counts by participant and kind and
writes nothing, the op takes the making off, keeps the agent's own note and his, gives a board with no mark its mark,
copies each file to _Archive first, keeps one line in the record of agents' changes, a second run finds nothing, and the
run's undo puts every file back byte for byte. MCP's clear_made_notes runs the same op."""
from __future__ import annotations

import hashlib
import json
import os
import shutil
from pathlib import Path

from .support import check
from . import support

ASKED = "Take the notes of who made the boards off."
MADE = ("Made by Claude Code in a conversation on 9 November 2026 at 22:21, for the request 'Group them by who they are "
        "afraid of'. 3 PETs, 18 placed, 2 not placed.")
COPY = "Duplicated from Board 1 by Claude Code in a conversation on 9 November 2026 at 22:30, for the request 'Try another'."


def digest(root: Path) -> dict:
    """Every file of the project by its contents, the lock files set aside."""
    return {p.relative_to(root).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in sorted(root.rglob("*")) if p.is_file() and not p.name.endswith(".lock")}


def test_clear_made_notes(scratch: Path):
    print("\n397. The notes of how an agent's boards were made: none written, the old ones taken off with the agent's own "
          "note and his kept, the dry run's counts and nothing written, the archive copies, one record line, a second run "
          "finding nothing, the run's undo, and MCP (sidebarcopy, 16 November)")
    import agent_changes
    import agent_log
    import cli
    import mcp_server
    import server as server_mod
    import themes

    base = scratch / "clear-made-notes-397"
    shutil.rmtree(base, ignore_errors=True)
    root = base / "Dogs at home"
    root.mkdir(parents=True)
    (root / server_mod.PROJECT_FILE).write_text(json.dumps({
        "name": "Dogs at home", "research_question": support.DEMO_QUESTION,
        "agents": {"allowed": True, "at": "2026-11-16T09:00:00+00:00"}}), encoding="utf-8")
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
        # ── the notes as an earlier build wrote them: a made board with an agent's note after it, one with none and no
        # mark, a copy, and one he wrote
        book = next((root / "Rowan").glob("*.xlsx"))
        path = themes.themes_path(book)
        stored = json.loads(path.read_text(encoding="utf-8"))
        boards = stored["boards"]
        boards[0]["note"] = MADE + " Its note: Grouped by the fear each names."
        boards[0].pop("made", None)
        dup = json.loads(json.dumps(boards[0]))
        dup.update(id="v98", name="A copy", note=COPY)
        dup.pop("made", None)
        boards.append(dup)
        extra = json.loads(json.dumps(boards[0]))
        extra.update(id="v99", name="His own", note="A note he wrote himself.")
        extra.pop("made", None)
        extra["history"] = []
        boards.append(extra)
        # a sentence he added after a copy's note, ending in a quoted word, and words he changed inside the agent's
        # sentence of a board whose mark keeps the request: both are his, so both stay
        added = json.loads(json.dumps(dup))
        added.update(id="v97", name="Added after", note=COPY + " I tried 'this'.")
        changed = json.loads(json.dumps(boards[0]))
        changed.update(id="v96", name="Changed inside", note=MADE.replace("afraid of", "scared of"),
                       made={"by": "agent", "tool": "Claude Code", "request": "Group them by who they are afraid of",
                             "at": "2026-11-09T22:21:00+00:00"})
        boards.extend([added, changed])
        path.write_text(themes.render(stored) + "\n", encoding="utf-8")
        gd = json.loads((root / "idiograph-gets.json").read_text(encoding="utf-8"))
        gd["boards"][0]["note"] = MADE
        (root / "idiograph-gets.json").write_text(themes.render(gd) + "\n", encoding="utf-8")
        start = digest(root)

        # ── 1. the dry run: counts by participant and kind, nothing written
        code, dry, err = run("clear-made-notes", "--dry-run", tool=None)
        by = {p["case"]: p for p in dry.get("by_participant") or []}
        check("397: the dry run counts the made boards and the copies by participant, the project's own as the project, "
              "and names the files, never a word of a note",
              code == 0 and dry.get("dry_run") is True and by.get("Rowan", {}).get("made") == 1 and by["Rowan"]["copies"] == 1
              and by.get("", {}).get("made") == 1 and dry["boards"] == 3 and dry["left"] == 2 and by["Rowan"]["left"] == 2 and "idiograph-gets.json" in dry["files"]
              and "Group them by" not in json.dumps(dry), err + json.dumps(dry)[:500])
        check("397: the dry run writes nothing: no record, no restore point and no archive copy",
              digest(root) == start and not (root / agent_changes.FILE).exists() and not list(root.rglob("_Archive")),
              str(sorted(set(digest(root)) ^ set(start))))
        code, _, err = run("clear-made-notes")
        check("397: the op with no request is refused, nothing written", code != 0 and "--note" in err and digest(root) == start, err)

        # ── 2. the op
        code, done, err = run("clear-made-notes", "--note", ASKED)
        stored = json.loads(path.read_text(encoding="utf-8"))
        by_id = {b["id"]: b for b in stored["boards"]}
        first, copied, his = stored["boards"][0], by_id["v98"], by_id["v99"]
        gd = json.loads((root / "idiograph-gets.json").read_text(encoding="utf-8"))
        check("397: the op takes the making off a made board and keeps the agent's own note, gives a board with no mark its mark, "
              "empties a copy's note and leaves the note he wrote",
              code == 0 and done["boards"] == 3 and first["note"] == "Grouped by the fear each names."
              and first["made"]["tool"] == "Claude Code" and first["made"]["request"] == "Group them by who they are afraid of"
              and "note" not in copied and his["note"] == "A note he wrote himself."
              and "note" not in gd["boards"][0] and gd["boards"][0].get("made", {}).get("tool") == "Claude Code",
              err + json.dumps(done)[:300])
        check("397: a note with a sentence of his after it, or words of his inside the agent's, is left and stays on its board",
              "I tried 'this'." in next(b for b in stored["boards"] if b["id"] == "v97")["note"]
              and "scared of" in next(b for b in stored["boards"] if b["id"] == "v96")["note"] and done["left"] == 2,
              json.dumps(done)[:300])
        import clear_made_notes as notes_mod
        bare = {"note": MADE, "id": "x"}
        kind = notes_mod.settle(bare, "2026-11-10T10:00:00+00:00")
        check("397: a board with no created time still gets its mark, from the file's time, before its note goes",
              kind == "made" and bare["made"]["at"] == "2026-11-10T10:00:00+00:00" and "note" not in bare, json.dumps(bare))
        check("397: a note that has only the agent's first words, before the op, still reads as made by an agent",
              themes.made_said({"note": "Made by Claude Code in a conversation on 5 October 2026 at 19:02, for the request "
                                        "'x'. I added this."}) == {"by": "agent", "said": "Made by an agent", "edited": False})
        check("397: the board menu still says an agent made the board, from its mark",
              themes.made_said(first) == {"by": "agent", "said": "Made by an agent", "edited": False}
              and themes.made_said(his) is None, json.dumps(themes.made_said(first)))
        mine = [n for n in root.glob("Rowan/**/_Archive/*")]
        top = [n for n in (root / "_Archive").iterdir()] if (root / "_Archive").is_dir() else []
        check("397: a copy of each file as it was is in its _Archive, named pre-clear-made-notes, and no other file touched",
              len(mine) == 1 and "(pre-clear-made-notes " in mine[0].name and len(top) == 1
              and "(pre-clear-made-notes " in top[0].name
              and all(digest(root).get(k) == v for k, v in start.items() if not k.endswith(".json")), str([n.name for n in mine + top]))
        lines = agent_changes.read(root)
        check("397: the op is one line in the record of agents' changes with his request, and a second run finds nothing",
              len([e for e in lines if e["op"] == "clear-made-notes"]) == 1
              and [e for e in lines if e["op"] == "clear-made-notes"][0]["request"] == ASKED
              and run("clear-made-notes", "--note", ASKED)[1].get("boards") == 0, json.dumps(lines)[-400:])
        code, _, err = run("validate", tool=None)
        check("397: idiograph validate is clean after the op", code == 0, err)

        # ── 3. the run's undo
        rid = [e for e in lines if e["op"] == "clear-made-notes"][0]["run"]
        code, undone, err = run("agents", "undo-run", rid, "--note", "Put them back")
        now = digest(root)
        check("397: the run's undo puts the boards' files back byte for byte",
              code == 0 and all(now.get(k) == v for k, v in start.items() if k.endswith(".json")), err + json.dumps(undone)[:300])

        # ── 4. what an agent writes now carries no note of its making, and keeps its mark
        (base / "spec.json").write_text(json.dumps({"pets": [{"title": "A lonely year", "members": ["S1", "S2"]}]}), encoding="utf-8")
        code, made, err = run("board", "new", "Rowan", "--from", str(base / "spec.json"), "--note", "A new grouping")
        stored = json.loads(themes.themes_path(book).read_text(encoding="utf-8"))
        board = stored["boards"][-1]
        check("397: a board an agent makes carries no note of who made it and the mark that it did, and its answer none",
              code == 0 and not board.get("note") and board["made"]["tool"] == "Claude Code"
              and board["made"]["request"] == "A new grouping" and not made.get("note"), err + json.dumps(board)[:300])
        code, dup, err = run("board", "duplicate", "Rowan", board["name"], "--note", "A copy")
        stored = json.loads(themes.themes_path(book).read_text(encoding="utf-8"))
        check("397: a copy an agent makes through board duplicate has no note, and none in its answer",
              code == 0 and not stored["boards"][-1].get("note") and not dup.get("note"), err + json.dumps(dup)[:300])
        code, dup, err = run("gets", "duplicate", "Board 1", "--note", "A copy of the GETs")
        gets_data = json.loads((root / "idiograph-gets.json").read_text(encoding="utf-8"))
        check("397: a copy through gets duplicate has no note either",
              code == 0 and not gets_data["boards"][-1].get("note") and not dup.get("note"), err + json.dumps(dup)[:300])

        # ── 5. MCP
        tools = {t["name"]: t for t in mcp_server.tools_for("idiograph")}
        t = tools.get("clear_made_notes")
        check("397: MCP's clear_made_notes writes, takes dry_run and the request, and maps to the command line's op",
              t is not None and not t["annotations"]["readOnlyHint"]
              and {"dry_run", "request"} <= set(t["inputSchema"]["properties"]), json.dumps(t)[:300] if t else "")
    finally:
        agent_changes.ALL_OPS = kept[0]
        if kept[1] is None:
            os.environ.pop(agent_log.PLACE, None)
        else:
            os.environ[agent_log.PLACE] = kept[1]
        agent_log.flush()
