"""Area 261: Find and replace on the agents' side of the API, everything following (Adam, 24 October 2026). The
app's route /api/replace, the command line's transcript replace and MCP's transcript_replace all run
`routes.replace_in_case`: a Replace all changes the transcript, the quotes, the experiential statements, the
exploratory notes and the interviewer's notes in step, under one batch id, every board's cards, the picks'
words and the GETs' copy taking the new words, and one undo puts all of it back. The dry run writes nothing.
--all reaches every participant under one batch. --pairs and --mask never say the words found. Then the parity
check: every route the page calls has its command line and MCP op, or is the page's own business with a
reason, or is a gap queued as a next build.

The fixtures are invented: a project on a village running club, the Kestrels, two made-up participants.
"""
from __future__ import annotations

import hashlib
import json
import re
import shutil

import openpyxl

from . import support
from .support import check

TEAM = "Kestrels"
NEW = "Larks"


def sha(path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest() if path.exists() else ""


def cells(path) -> dict:
    """Every cell of every sheet as the suite's comparison reads it, its value, its runs and its style."""
    wb = openpyxl.load_workbook(path, rich_text=True)
    try:
        return {(ws.title, c.coordinate): repr(support.cell_signature(c))
                for ws in wb.worksheets for row in ws.iter_rows() for c in row}
    finally:
        wb.close()


def make_workbook(root, name: str):
    """A made-up runner's workbook: the club's name in a passage's transcript, its two statements, its
    quote, its exploratory note and the interviewer's note on the turn before, with a highlight on words
    the replace leaves alone."""
    import workbook as wb_mod
    folder = root / name
    (folder / "Source").mkdir(parents=True)
    raw = openpyxl.Workbook()
    first = raw.active
    first.title = "Initial"
    first.append(["Name", "Timestamp", "Transcript"])
    first.append(["Interviewer", "00:00:04", "How did you come to the club?"])
    first.append([name, "00:00:09", f"The {TEAM} took me in the first winter, and the {TEAM} ran with me in the dark."])
    first.append(["Interviewer", "00:00:20", "And now?"])
    first.append([name, "00:00:26", "I lead the slow group on Thursdays, round the reservoir."])
    second = raw.create_sheet("Second")
    second.append(["Name", "Timestamp", "Transcript"])
    second.append(["Interviewer", "00:00:03", "What changed?"])
    second.append([name, "00:00:07", f"Without the {TEAM} I would have stopped running."])
    source = folder / "Source" / f"{name} - interview.xlsx"
    raw.save(source)
    book = wb_mod.create_from_source(source, folder / f"{name} - EN & ES.xlsx")
    wb = openpyxl.load_workbook(book, rich_text=True)
    ws = wb["Initial"]
    cols = wb_mod.detect_columns(ws)
    ws.cell(3, cols["es"]).value = f"Taken in by the {TEAM} in a first winter\n\nRunning in the dark held by others"
    ws.cell(3, cols["en"]).value = f"A made-up note: the {TEAM} as a family."
    ws.cell(3, cols["kq"]).value = f"“The {TEAM} took me in”\n\n(no quote)"
    ws.cell(1, 7).value, ws.cell(1, 7).font = wb_mod.NOTE_HEADER, wb_mod.HFONT
    ws.cell(2, 7).value = f"Ask more about the {TEAM}."
    ws.cell(5, cols["es"]).value = "Leading the slow group"
    # a highlight on words the replace leaves alone, which must come through where it was
    said = wb_mod.plain_text(ws.cell(3, cols["transcript"]).value)
    at = said.index("first winter, and")
    ws.cell(3, cols["transcript"]).value = wb_mod.apply_crux(ws.cell(3, cols["transcript"]).value, at,
                                                             at + len("first winter, and"), remove=False)
    two = wb["Second"]
    cols2 = wb_mod.detect_columns(two)
    two.cell(3, cols2["es"]).value = f"Kept running by the {TEAM}"
    wb.save(book)
    return book


def page_routes() -> set[str]:
    """Every route the page calls: each quoted '/api/...' in Idiograph's scripts and the family's."""
    found = set()
    for path in sorted((support.TOOL / "apps" / "idiograph" / "static").glob("*.js")) + sorted(
            (support.TOOL / "family" / "static").glob("*.js")):
        found |= set(re.findall(r"['\"`](/api/[A-Za-z0-9_-]+)", path.read_text(encoding="utf-8")))
    return found


# The routes that are the page's own business, each with why an agent has no op for it: the window, its
# drawing and layout, the app's own settings and keys, the app's own AI, and the screen's own aids. Each carries
# what it answers (agentholds, Adam, 2 November 2026): a risk of the four at the head of docs/agents.md
# (`agent_changes.RISKS`), "screen", what the app keeps to its screens by choice, or "own AI", the app's own AI, which
# an agent works in place of.
REASONS = {"screen", "own AI"}
PAGE_ONLY = {
    "/api/agent-start": (("screen",), "the words of the box that sets an agent up, the page's own"),
    "/api/agents-guide": ((4,),
                          "writes AGENTS.md for an agent to read, setting agents up rather than working the data"),
    "/api/audio": (("screen",), "whether the player has a recording and where it streams from, playback alone"),
    "/api/beat": (("screen",), "a tab's heartbeat, so the app knows a window is open"),
    "/api/check-key": ((4,), "the API key's check in Settings, a secret no agent ever handles"),
    # Home's line of agents' changes he has not seen (agentreview2, 13 November 2026), a count from the store's tally
    "/api/agent-unseen": (("screen",), "how many changes agents made since he last looked, Home's line, a view of his own"),
    # the demo's recordings on demand (recdemand, 13 November 2026): agents never download, the window alone does
    "/api/demo-recordings": (("screen",), "the demo's recordings downloaded for the player, playback alone, never the "
                                          "project's data"),
    # a code taken from it is Add a code's own save, which `codes extract add` does for an agent (taaibuild)
    "/api/codes-suggest": (("own AI",), "the app's own AI's codes for an extract, which an agent works in place of"),
    "/api/examples": (("screen",), "the examples panel beside the fields, an aid on the screen"),
    "/api/family": (("screen",), "the other apps of the family at the foot of Home"),
    "/api/family-open": (("screen",), "opens another app of the family, the window's act"),
    "/api/feedback": ((1,), "a note to the app's maker, never the project's data"),
    "/api/gets-ai": (("own AI",), "the app's own AI on the GETs screen, which an agent works in place of"),
    "/api/guidance": (("screen",), "the Guidance tab's text, which an agent reads in the guide"),
    "/api/home": (("screen",), "Sift's and Trace's Home, never Idiograph's data"),
    "/api/key": ((4,), "the API key, a secret no agent ever handles"),
    "/api/key-status": ((4,), "whether a key is stored, a secret's state"),
    "/api/mcp": ((4,), "adds Idiograph to Claude Desktop, setting agents up"),
    "/api/models": (("own AI",), "the app's own AI's models in Settings"),
    "/api/nudges": (("screen",), "the length nudge drawn on the screen as he types"),
    "/api/order": (("screen",), "the order of a project's rows on Home, layout"),
    "/api/reset-demo": (("screen",), "puts the demo back as it ships, the demo alone"),
    "/api/round-complete": (("screen",), "his round of work at the screen, timed by the page"),
    "/api/server": (("screen",), "the server's own state, the window's"),
    "/api/settings": ((4,), "the app's own settings, its look and its habits, which no undo reaches"),
    "/api/stamp": (("screen",), "what the page needs to see a change made elsewhere"),
    "/api/suggest": (("own AI",), "the app's own AI's suggestions, which an agent works in place of"),
    "/api/suggest-sample": (("own AI",), "the test bench of the app's own AI in Settings"),
    "/api/themes-ai": (("own AI",), "the app's own AI on the PETs screen, which an agent works in place of"),
    "/api/whats-new": (("screen",), "the version notes' sheet"),
}

# Each route the page calls that works the project's data, with the command line's ops that do the same
AGENT_OPS = {
    "/api/cases": [("cases", None)],
    "/api/themes-cases": [("cases", None)],
    "/api/participants": [("cases", None)],
    "/api/gets-head": [("cases", None)],
    "/api/open": [("statements", None), ("turn", "show")],
    "/api/commit": [("turn", "write")],
    "/api/edit-statement": [("turn", "write")],
    "/api/replace": [("transcript", "replace")],
    "/api/replace-undo": [("transcript", "replace-undo")],
    "/api/audio-offset": [("offset", None)],
    "/api/import": [("import", None)],
    "/api/create": [("import", None)],
    "/api/qdpx": [("qdpx", None)],
    "/api/themes": [("board", "show"), ("board", "list")],
    "/api/themes-save": [("board", "apply")],
    "/api/board-order": [("board", "apply")],
    "/api/themes-versions": [("board", "new"), ("board", "rename"), ("board", "duplicate"), ("board", "delete"),
                             ("board", "current"), ("board", "canvas"), ("board", "note"), ("board", "complete")],
    "/api/gets": [("gets", "show")],
    # every save of a GETs, LGETs or LPETs board, a statement dragged in from the Participants panel among them
    # (gets apply's bring_in, lpetadd, 11 November 2026)
    "/api/gets-save": [("gets", "apply")],
    "/api/gets-cases": [("gets", "take"), ("gets", "colour")],
    "/api/gets-trail": [("gets", "export")],
    "/api/trajectories": [("trajectories", "show")],
    "/api/trajectories-ops": [("trajectories", "apply")],
    # the transcript's turns a key quote's passage is found in (trajchoose, 11 November 2026), read with turn show
    "/api/trajectories-turns": [("turn", "show")],
    # a thematic analysis project's code list (codes, 2 November 2026)
    "/api/codes": [("codes", "list"), ("codes", "show")],
    "/api/codes-ops": [("codes", "new"), ("codes", "rename"), ("codes", "describe"), ("codes", "merge"),
                       ("codes", "delete")],
    "/api/codes-undo": [("codes", "undo"), ("codes", "redo")],
    "/api/send-project": [("project", "send")],
    # Export as REFI-QDA (qdpxout, 8 November 2026)
    "/api/qdpx-export": [("project", "export-qdpx")],
    # the agent log, read alone (agentlog, 3 November 2026)
    "/api/agent-log": [("agents", "log")],
    # Project history's By an agent, its Undo and Undo this run (agentreview2, 13 November 2026)
    "/api/agent-changes": [("agents", "changes"), ("agents", "undo-change"), ("agents", "undo-run")],
    "/api/send-list": [("project", "send")],
    "/api/open-sent": [("project", "open-copy")],
    "/api/boards-in": [("project", "boards-in")],
    "/api/search": [("search", None)],
    "/api/add-transcripts": [("project", "add-transcripts")],
    # the list of names a transcript has replaced on its way in (namesrule and namesui, 8 November 2026), which the
    # Names to replace card calls. An agent lists it, checks transcripts for it, replaces them and takes entries off
    # it, by number, and never reads or adds a real name: `names set` and `names preview` are the stated exception to
    # parity (the list is set in the app, since an agent that types a real name has sent it to a model)
    "/api/names": [("names", "list"), ("names", "check"), ("names", "replace"), ("names", "remove")],
    "/api/edit-turn": [("turn", "edit")],
    "/api/interviewer-note": [("turn", "interviewer-note")],
    "/api/rows": [("turn", "assign"), ("turn", "assign-undo")],
    "/api/trim": [("turn", "trim"), ("turn", "trim-undo")],
    "/api/new-project": [("project", "new")],
    "/api/project": [("project", "set")],
    # Remove from Idiograph, its folder to the Trash with his tick (removetrash, 10 November 2026). Add project and
    # Show in Finder stay the page's: an agent makes a project with project new
    "/api/projects": [("project", "remove")],
    "/api/project-history": [("project", "history")],
    # Working together's comments and review (wtreview, 8 November 2026)
    "/api/team-review": [("team", "review"), ("team", "ask"), ("team", "comment"), ("team", "review-send"),
                         ("team", "reply"), ("team", "thread"), ("team", "review-done"), ("team", "suggest"),
                         ("team", "suggestion-answer")],
    "/api/rename": [("participant", "rename")],
    # each participant's picture, label and pen portrait (pbiobuild, 11 November 2026)
    "/api/participant": [("participant", "set"), ("participant", "show")],
    # the project's demographics (demobuild, 12 November 2026)
    "/api/demographics": [("demographics", "show"), ("demographics", "apply"), ("demographics", "move-tags")],
    "/api/complete": [("participant", "complete")],
    "/api/export": [("participant", "export")],
    "/api/themes-boards": [("board", "note"), ("board", "history"), ("board", "revision"), ("board", "restore"),
                           ("board", "copy")],
    "/api/themes-export": [("board", "export")],
    "/api/gets-ops": [("gets", "fresh"), ("gets", "duplicate"), ("gets", "rename"), ("gets", "note"),
                      ("gets", "canvas"), ("gets", "current"), ("gets", "delete"), ("gets", "complete"),
                      ("gets", "subs")],
    "/api/gets-boards": [("gets", "history"), ("gets", "revision"), ("gets", "restore")],
    "/api/gets-settings": [("gets", "settings")],
    # Working together (wtkeys, 8 November 2026)
    "/api/team": [("team", "show"), ("team", "on"), ("team", "set"), ("team", "invite"), ("team", "answers"),
                  ("team", "admit"), ("team", "join"), ("team", "joined"), ("team", "remove"), ("team", "lead"),
                  ("team", "take"), ("team", "send")],
    # a reviewer's board sent straight in (wtboard, 9 November 2026)
    "/api/team-board": [("team", "boards"), ("team", "board-send"), ("team", "board-take"), ("team", "board-answer")],
}

# The routes with no op for an agent today, each a next build for the coordinator. A gap
# closed comes off this list, and the check fails while one closed is still on it.
KNOWN_GAPS = {}


def parity(routes_called: set[str], commands: dict, tools: list) -> dict:
    """The parity between the page and the agents' ops: each route the page calls that is in no list, each
    op a route names that the command line or MCP lacks, each gap listed that an op now closes, and each
    entry of the lists no page calls any more."""
    by_command = {tuple(t["command"]) for t in tools}
    # two commands the command line runs before its table, Search and opening a sent copy (`perform`)
    first = {("search", None), ("project", "open-copy")}
    missing = sorted(r for r in routes_called if r not in PAGE_ONLY and r not in AGENT_OPS and r not in KNOWN_GAPS)
    no_op = sorted(f"{r} {op}" for r, ops in AGENT_OPS.items() for op in ops
                   if (op not in first and op not in commands) or op not in by_command)
    doubled = sorted(r for r in KNOWN_GAPS if r in AGENT_OPS or r in PAGE_ONLY) + sorted(
        r for r in PAGE_ONLY if r in AGENT_OPS)
    stale = sorted(r for r in list(PAGE_ONLY) + list(AGENT_OPS) + list(KNOWN_GAPS) if r not in routes_called)
    return {"missing": missing, "no_op": no_op, "doubled": doubled, "stale": stale}


def test_passage_replace(scratch):
    print("\n261. Find and replace for agents, everything following: the transcript, quotes, statements and notes "
          "in step under one batch, the boards and the GETs with them, the dry run, --all, --pairs and --mask, "
          "and the parity of the page's routes with the agents' ops (24 October)")
    import cli
    import gets as gets_mod
    import idiograph_cli
    import idiograph_routes as routes
    import mcp_server
    import rounds as rounds_mod
    import server as server_mod
    import themes as themes_mod
    import workbook as wb_mod

    root = scratch / "passage-replace-261"
    shutil.rmtree(root, ignore_errors=True)
    root.mkdir(parents=True)
    (root / "idiograph-project.json").write_text(json.dumps({
        "name": "Running club, a scratch project", "agents": {"allowed": True, "at": "2026-10-24T10:00:00+01:00"}}),
        encoding="utf-8")
    config_file = scratch / "passage-replace-261-config.json"
    config_file.write_text(json.dumps({"root": str(root), "interviewer": "Interviewer"}), encoding="utf-8")
    perrin = make_workbook(root, "Perrin")
    wynn = make_workbook(root, "Wynn")

    def run(*args):
        code, out, err = cli.run(["--root", str(root), "--config", str(config_file), "--json", *args])
        got = support.plain(json.loads(out)) if out.strip() and code == 0 else {}
        if code != 0 and out.strip():
            try:
                err += support.plain(json.loads(out)).get("error", "")
            except ValueError:
                err += out
        return code, got, err, out

    def plain(*args):
        code, out, err = cli.run(["--root", str(root), "--config", str(config_file), *args])
        return code, out, err

    # a board on each participant, its PET holding both statements of the passage and its quote picked
    for book, name in ((perrin, "Perrin"), (wynn, "Wynn")):
        spec = scratch / f"passage-replace-261-{name}.json"
        spec.write_text(json.dumps({"pets": [{"title": "Belonging to the club", "members": ["S1", "S2"],
                                              "picks": ["Initial:3:0"]}]}), encoding="utf-8")
        code, _, err, _ = run("board", "new", name, "--from", str(spec), "--note", "A board to try", "--tool", "Claude Code")
        check(f"261: a board on {name} to follow the words", code == 0, err)
    kept_root = server_mod.ROOT_OVERRIDE
    server_mod.ROOT_OVERRIDE = str(root)
    try:
        books = routes.gets_books(root)
        when = themes_mod.now_iso()
        gdata, _c, _d, _t = gets_mod.assemble(root, books, when)
        gets_mod.write(root, gets_mod._file(gdata, when))
    finally:
        server_mod.ROOT_OVERRIDE = kept_root
    gets_file = gets_mod.gets_path(root)
    progress = rounds_mod.progress_path(perrin)
    themes_file = themes_mod.themes_path(perrin)

    def board_words(book):
        data = themes_mod.load(book)
        board = themes_mod.boards_of(data)[0]
        return ({k: c["text"] for k, c in board["cards"].items()}, dict(board.get("quoted") or {}),
                [{k: c["text"] for k, c in (r.get("state") or {}).get("cards", {}).items()}
                 for r in board.get("history") or []])

    def gets_words(case="Perrin"):
        rec = gets_mod.load(root)["cases"][case]
        return {k: (v["text"], v.get("quotes"), v.get("notes")) for k, v in rec["lines"].items()}

    def gets_status():
        kept = server_mod.ROOT_OVERRIDE
        server_mod.ROOT_OVERRIDE = str(root)
        try:
            data = gets_mod.load(root)
            return {e["case"]: e["status"] for e in gets_mod.survey(routes.gets_books(root), data)}
        finally:
            server_mod.ROOT_OVERRIDE = kept

    check("261: the GETs hold both participants unchanged before any replace",
          gets_status() == {"Perrin": "in", "Wynn": "in"}, str(gets_status()))
    before_cells = cells(perrin)
    before_files = {p: sha(p) for p in (perrin, progress, themes_file, gets_file)}
    before_board, before_gets = board_words(perrin), gets_words()

    # 1. the dry run counts and lists each place and writes nothing
    code, dry, err, out = run("transcript", "replace", "Perrin", "--find", TEAM, "--with", NEW, "--dry-run")
    places = {(x["sheet"], x["row"], x["column"]): x["count"] for a in dry.get("participants", []) for x in a["places"]}
    check("261: the dry run counts every column a row holds the words in, by sheet, row, timecode and column",
          code == 0 and dry.get("dry_run") is True and dry.get("replaced") == 8
          and places == {("Initial", 2, "note"): 1, ("Initial", 3, "transcript"): 2, ("Initial", 3, "es"): 1,
                         ("Initial", 3, "kq"): 1, ("Initial", 3, "en"): 1, ("Second", 3, "transcript"): 1,
                         ("Second", 3, "es"): 1}
          and all(x.get("time") for a in dry["participants"] for x in a["places"]), err or json.dumps(dry)[:500])
    check("261: the dry run writes nothing, the workbook, its progress file, the board and the GETs as they were",
          {p: sha(p) for p in before_files} == before_files, err)

    # 2. Replace all: the transcript, the quotes, the statements and the notes in step, under one batch
    code, done, err, out = run("transcript", "replace", "Perrin", "--find", TEAM, "--with", NEW,
                               "--note", "Call the club the Larks", "--tool", "Claude Code")
    batch = done.get("batch")
    wb = openpyxl.load_workbook(perrin, rich_text=True)
    ws, two = wb["Initial"], wb["Second"]
    cols = wb_mod.detect_columns(ws)
    got = {role: wb_mod.plain_text(ws.cell(3, cols[role]).value) for role in ("transcript", "es", "en", "kq")}
    note = wb_mod.plain_text(ws.cell(2, 7).value)
    second = wb_mod.plain_text(two.cell(3, wb_mod.detect_columns(two)["es"]).value)
    runs = wb_mod.cell_runs(ws.cell(3, cols["transcript"]).value)
    wb.close()
    check("261: Replace all changes the transcript, the statement, the quote, the exploratory note and the "
          "interviewer's note alike, and the other sheet's",
          code == 0 and done.get("replaced") == 8 and batch
          and got["transcript"] == f"The {NEW} took me in the first winter, and the {NEW} ran with me in the dark."
          and got["es"] == f"Taken in by the {NEW} in a first winter\n\nRunning in the dark held by others"
          and got["en"] == f"A made-up note: the {NEW} as a family."
          and got["kq"] == f"“The {NEW} took me in”\n\n(no quote)"
          and note == f"Ask more about the {NEW}." and second == f"Kept running by the {NEW}",
          err or json.dumps(got)[:400])
    check("261: a highlight on words the replace left alone comes through on its words",
          [x["text"] for x in runs if x["crux"]] == ["first winter, and"], str(runs))
    records = [e for e in rounds_mod.load_progress(perrin)["edits"] if e.get("batch") == batch]
    check("261: every row changed is one edit record under the one batch, its cells' old and new words beside the "
          "transcript's, with the agent's tool and his request",
          len(records) == 3 and {(e["sheet"], e["row"]) for e in records} == {("Initial", 2), ("Initial", 3), ("Second", 3)}
          and set(next(e for e in records if e["row"] == 3 and e["sheet"] == "Initial")["cells"]) == {"es", "en", "kq"}
          and all(e.get("by") == "agent" and e.get("tool") == "Claude Code" and e.get("request") == "Call the club the Larks"
                  and e["find"] == TEAM and e["replace"] == NEW for e in records), json.dumps(records)[:400])
    cards, quoted, history = board_words(perrin)
    check("261: every board's card of a statement and the pick's quote take the new words, revisions too",
          cards.get("Initial:3:0") == f"Taken in by the {NEW} in a first winter"
          and quoted.get("Initial:3:0") == f"“The {NEW} took me in”"
          and all(TEAM not in t for h in history for t in h.values()), json.dumps([cards, quoted])[:400])
    lines = gets_words()
    check("261: the GETs' copy of the participant takes the new words, its statement, quote and note, and stays in, "
          "not Changed since it came in",
          lines["Initial:3:0"][0] == f"Taken in by the {NEW} in a first winter"
          and lines["Initial:3:0"][1][0] == f"“The {NEW} took me in”"
          and lines["Initial:3:0"][2] == [f"A made-up note: the {NEW} as a family."]
          and gets_status() == {"Perrin": "in", "Wynn": "in"}, json.dumps(lines)[:400] + str(gets_status()))
    kept_root = server_mod.ROOT_OVERRIDE
    server_mod.ROOT_OVERRIDE = str(root)
    try:
        merged = routes.api_themes({"path": str(perrin)})
    finally:
        server_mod.ROOT_OVERRIDE = kept_root
    check("261: the PETs screen opens with no card marked changed for the replace",
          not [c for c in merged["cards"] if c.get("changed")], str([c["key"] for c in merged["cards"] if c.get("changed")]))

    # 3. one undo takes it all back
    code, back, err, out = run("transcript", "replace-undo", batch, "--note", "Put the Kestrels back", "--tool", "Claude Code")
    records = [e for e in rounds_mod.load_progress(perrin)["edits"] if e.get("batch") == batch]
    check("261: the undo by the batch alone puts every cell of the workbook back as it was",
          code == 0 and back.get("replaced") == 8 and cells(perrin) == before_cells
          and all(e["undone"] is True and e.get("undone_by") == "Claude Code" for e in records), err)
    check("261: and the board, its revisions, the pick's words and the GETs' copy with it, the GETs still in",
          board_words(perrin) == before_board and gets_words() == before_gets
          and gets_status() == {"Perrin": "in", "Wynn": "in"}, str(gets_status()))

    # 4. --all reaches every participant under one batch, which one undo takes back
    wynn_cells = cells(wynn)
    code, every, err, out = run("transcript", "replace", "--all", "--find", TEAM, "--with", NEW,
                                "--note", "Rename the club for both", "--tool", "Claude Code")
    held = {a["case"]: a["replaced"] for a in every.get("participants", [])}
    batches = {e["batch"] for b in (perrin, wynn) for e in rounds_mod.load_progress(b)["edits"]
               if e.get("request") == "Rename the club for both"}
    check("261: --all reaches every participant, each workbook under the same batch",
          code == 0 and held == {"Perrin": 8, "Wynn": 8} and batches == {every.get("batch")}, err or str(held))
    code, back, err, out = run("transcript", "replace-undo", every["batch"], "--note", "Back for both", "--tool", "Claude Code")
    check("261: one undo of that batch puts both workbooks back",
          code == 0 and back.get("replaced") == 16 and cells(perrin) == before_cells and cells(wynn) == wynn_cells, err)
    code, _, err, _ = run("transcript", "replace", "--find", TEAM, "--with", NEW, "--note", "x")
    code2, _, err2, _ = run("transcript", "replace", "Perrin", "--find", TEAM, "--with", NEW)
    check("261: a participant or --all, never neither, and a write needs his request",
          code != 0 and "not both" in err and code2 != 0 and "--note" in err2, err + err2)

    # 5. --pairs and --mask: no line, answer, record or refusal says the words found
    pairs = scratch / "passage-replace-261-pairs.tsv"
    pairs.write_text(f"# made-up names\n{TEAM}\t{NEW}\nThursdays\tweekdays\n", encoding="utf-8")
    code, out, err = plain("transcript", "replace", "--all", "--pairs", str(pairs), "--dry-run")
    code2, jout, jerr = cli.run(["--root", str(root), "--config", str(config_file), "--json", "transcript", "replace",
                                 "--all", "--pairs", str(pairs), "--note", "Anonymise from the list", "--tool", "Claude Code"])
    masked = support.plain(json.loads(jout)) if code2 == 0 else {}
    told = out + err + jout + jerr
    check("261: --pairs never says the words, in the lines, the answer or a refusal",
          code == 0 and code2 == 0 and masked.get("replaced") == 18 and TEAM not in told and NEW not in told
          and "Thursdays" not in told and "weekdays" not in told, told[:400])
    sidecar = rounds_mod.progress_path(perrin).read_text(encoding="utf-8")
    records = [e for e in rounds_mod.load_progress(perrin)["edits"] if e.get("batch") == masked.get("batch")]
    check("261: the progress file's records say [match] for what was found and put in",
          records and all(e["find"] == "[match]" and e["replace"] == "[match]" for e in records)
          and f'"find": "{TEAM}"' not in sidecar.split(masked["batch"])[-1], json.dumps(records[:1])[:300])
    run("transcript", "replace-undo", masked["batch"], "--note", "Back", "--tool", "Claude Code")
    code, out, err = plain("transcript", "replace", "Perrin", "--find", TEAM, "--with", NEW, "--mask", "--dry-run")
    check("261: --mask with --find says no word either", code == 0 and TEAM not in out + err and NEW not in out + err,
          out + err)
    bad = scratch / "passage-replace-261-bad.tsv"
    bad.write_text(f"{TEAM} {NEW}\n", encoding="utf-8")
    code, out, err = plain("transcript", "replace", "Perrin", "--pairs", str(bad), "--note", "x")
    check("261: a pairs line with no tab is refused by its number alone, nothing written, no word said",
          code != 0 and "Line 1 of the pairs file" in out + err and TEAM not in out + err and cells(perrin) == before_cells,
          out + err)

    # 6. MCP's tools and the app's route run the same replace
    srv = mcp_server.Server(str(root), config=str(config_file))

    def call(name, **given):
        return srv.receive(json.dumps({"jsonrpc": "2.0", "id": 1, "method": "tools/call",
                                       "params": {"name": name, "arguments": given}}))["result"]

    got = call("transcript_replace", case="Perrin", pairs=[[TEAM, NEW]], request="Try it", dry_run=True)
    dry_ok = got["isError"] is False and support.plain(got["structuredContent"])["replaced"] == 8 and cells(perrin) == before_cells
    got = call("transcript_replace", case="Perrin", find=TEAM, request="Call the club the Larks")
    made = support.plain(got["structuredContent"]).get("batch") if got["isError"] is False else None
    undone = call("transcript_replace_undo", batch=made or "none", request="Back again")
    check("261: MCP's transcript_replace dry-runs, replaces with the words put in empty when with is left out, and "
          "transcript_replace_undo puts it back",
          dry_ok and made and undone["isError"] is False and cells(perrin) == before_cells, json.dumps([got, undone])[:400])
    kept_root = server_mod.ROOT_OVERRIDE
    server_mod.ROOT_OVERRIDE = str(root)
    try:
        held_files = {p: sha(p) for p in before_files}
        dry = routes.api_replace({"path": str(perrin), "find": TEAM, "replace": NEW, "dry_run": True})
        ok_dry = dry["replaced"] == 8 and dry["batch"] is None and {p: sha(p) for p in before_files} == held_files
        page = routes.api_replace({"path": str(perrin), "find": TEAM, "replace": NEW})
        row = next(r for r in page["rows"] if r["sheet"] == "Initial" and r["row"] == 3)
        ok_row = (TEAM not in row["es"] and NEW in row["kq"] and NEW in row["en"] and row["v"]
                  and row["pairs"][0]["es"].startswith("Taken in by the Larks"))
        routes.api_replace_undo({"path": str(perrin), "batch": page["batch"]})
    finally:
        server_mod.ROOT_OVERRIDE = kept_root
    check("261: the app's route answers its dry run with the count and writes nothing, and a Replace all answers each "
          "row's statements, quotes, notes and version for the page to take in",
          ok_dry and ok_row and page["batch"] and "places" in page and cells(perrin) == before_cells, json.dumps(row)[:300])
    check("261: the route writes no agent's mark on the app's own replace",
          all("by" not in e for e in rounds_mod.load_progress(perrin)["edits"] if e.get("batch") == page["batch"]))

    # 7. the parity of the page's routes with the agents' ops
    called = page_routes()
    gaps = parity(called, idiograph_cli.COMMANDS, mcp_server.tools_for("idiograph"))
    check("261: every route the page calls has its command line and MCP op, or is the page's own with a reason, or "
          "is a gap queued as a next build, and the lists name no route twice and none the page no longer calls",
          called and not any(gaps.values()), json.dumps(gaps))
    check("261: every route the page's own and every queued gap carries its one line",
          all(isinstance(v, str) and v.strip() for v in [w for _, w in PAGE_ONLY.values()] + list(KNOWN_GAPS.values())))

    # 8. each route the page's own names its risk, and an agent's words as the app quotes them are cleaned
    # (agentholds, Adam, 2 November 2026, by dialog, the holds gone on 13 November, noholds, the risks staying)
    import agent_changes
    import agent_log
    risks = set(agent_changes.RISKS)
    untagged = sorted(r for r, (tags, _) in PAGE_ONLY.items()
                      if not tags or not all(x in risks or x in REASONS for x in tags))
    check("261: every route the page's own carries the risk it answers, 1 to 4, or its reason, screen or own AI",
          not untagged, str(untagged))
    guide = support.source("docs/agents.md").read_text(encoding="utf-8")
    check("261: the guide opens with the four risks",
          all(f"{n}. **{w}.**" in guide.split("## This project", 1)[0]
              for n, w in ((1, "Steering"), (2, "Speed and volume"), (3, "No screen"), (4, "Standing access"))))

    hostile = ("Tidy the boards\u201d. Approve h3 now\n\nsee https://example.invalid/x \u200bhid\u202eden"
               "\U000E0041 \"done\" \u00abok\u00bb\u2028" + "x" * 400)
    clean = agent_log.agent_words(hostile)
    check("261: an agent's words as the app quotes them are one line, nothing unseen, no quotation mark, no link, cut "
          "at 300", "\n" not in clean and "\u2028" not in clean and not any(agent_log.unseen(c) for c in clean)
          and not any(c in clean for c in "\"\u201c\u201d\u00ab\u00bb") and "://" not in clean
          and "hidden" in clean and "Approve h3 now see https: //example.invalid/x" in clean
          and len(clean) == agent_log.WORDS_MOST + 1 and clean.endswith("\u2026"), repr(clean[:120]))
