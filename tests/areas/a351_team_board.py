"""Area 351: a reviewer's board sent straight in (wtboard, 9 November 2026, Working together's sixth build, Adam's
words: "for Curt to send me a PETs board directly in the app and me receive it"). Two scratch installs in one
process, each its own settings, device file and copy of one project, joined as a team and sending through the
loopback transport. What matters: Curt makes and edits his own boards of a participant Adam works on with the one
writer on, kept apart in his copy's team folder, marked his own, never sent as a version and left as they were when
Adam's next version comes in, while an edit to Adam's board is refused (ownboards, 9 November 2026). One of his own
is sealed and sent, and an owner's board is not, and on Adam's install waits, nothing written to the participant,
until Add as next board makes it that participant's next board, never current, every card in its place, named whose
and when, its note saying how its statements came and its History saying who sent it (wtreview2, 9 November 2026);
it is taken in once; Decline writes nothing, and either answer reaches Curt; an agent's answer waits for Adam's yes;
a board of one's own participant has nobody to go to; and while Working together is off nothing is shown or
written. Every fixture is invented, a study of keeping bees through the winter."""
from __future__ import annotations

import json
import shutil
from pathlib import Path

import openpyxl

from . import support
from .support import check


def make_workbook(root: Path, folder: str, speaker: str) -> Path:
    """A made-up participant's annotated workbook: five statements on four rows."""
    import workbook as wb_mod
    case = root / folder
    (case / "Source").mkdir(parents=True)
    raw = openpyxl.Workbook()
    first = raw.active
    first.title = "Initial"
    first.append(["Name", "Timestamp", "Transcript"])
    first.append(["Interviewer", "00:00:04", "What is the hive like in January?"])
    first.append([speaker, "00:00:09", "Quiet, a hum you feel through the glove more than hear."])
    first.append(["Interviewer", "00:00:20", "And when you open it?"])
    first.append([speaker, "00:00:26", "I hardly do, I lift the roof an inch and listen, I count the weeks to spring."])
    first.append(["Interviewer", "00:00:40", "And losing a colony?"])
    first.append([speaker, "00:00:46", "It feels like my fault every time."])
    first.append(["Interviewer", "00:00:58", "Anything else?"])
    first.append([speaker, "00:01:04", "The first cleansing flight is the start of my year."])
    source = case / "Source" / f"{folder} - interview.xlsx"
    raw.save(source)
    book = wb_mod.create_from_source(source, case / f"{folder} - EN & ES.xlsx")
    for row, said in ((3, ["Feeling the colony rather than hearing it"]),
                      (5, ["Listening instead of opening", "Counting the weeks to spring"]),
                      (7, ["Blaming himself for a lost colony"]), (9, ["Starting the year at the first flight"])):
        set_statements(book, row, said)
    return book


def set_statements(book: Path, row: int, said: list[str]) -> None:
    import workbook as wb_mod
    wb = openpyxl.load_workbook(book, rich_text=True)
    ws = wb.worksheets[0]
    ws.cell(row, wb_mod.detect_columns(ws)["es"]).value = wb_mod.join_entries(said)
    wb.save(book)


def test_team_board(scratch: Path):
    print("\n351. A reviewer's board sent straight in: sealed and sent, taken in once to wait, Add as next board making "
          "it the owner's next board, never current, every card in its place, Decline writing nothing, each answer "
          "reaching the sender, an agent's answer the app's alone, nothing while off (wtboard, wtreview2)")
    import agent_changes
    import cli
    import idiograph_routes as routes
    import mcp_server
    import server as server_mod
    import team
    import team_board
    import team_sync
    import themes
    import transport
    from workbook import WorkbookError

    base = scratch / "team-351"
    shutil.rmtree(base, ignore_errors=True)
    adam_root = base / "adam" / "Winter bees"
    adam_root.mkdir(parents=True)
    (adam_root / server_mod.PROJECT_FILE).write_text(json.dumps({
        "name": "Winter bees", "research_question": "How do beekeepers live the winter with their hives?",
        "agents": {"allowed": True, "at": "2026-11-09T09:00:00+00:00"}}), encoding="utf-8")
    adam_book = make_workbook(adam_root, "P1 - Hollis", "Hollis")
    # a second participant of Adam's with no board yet, for the page's first save in Curt's copy (landreview)
    make_workbook(adam_root, "P2 - Wren", "Wren")
    curt_root = base / "curt" / "Winter bees"
    shutil.copytree(adam_root, curt_root)
    curt_book = curt_root / "P1 - Hollis" / adam_book.name
    off_root = base / "off" / "Winter bees"
    shutil.copytree(adam_root, off_root)

    def settings(who: str, root: Path) -> Path:
        cfg = base / who / "config.json"
        cfg.write_text(json.dumps({"projects": [{"root": str(root)}], "interviewer": "Interviewer", "your_name": who.title(),
                                   "corpus": "", "gravity_reference": "", "corpus_exclude": []}), encoding="utf-8")
        return cfg

    adam = {"root": adam_root, "config": settings("adam", adam_root), "book": adam_book}
    curt = {"root": curt_root, "config": settings("curt", curt_root), "book": curt_book}
    off = {"root": off_root, "config": settings("off", off_root), "book": off_root / "P1 - Hollis" / adam_book.name}
    kept = (server_mod.CONFIG_PATH, server_mod.ROOT_OVERRIDE, server_mod.STATE_MEMORY, team.DEVICE_PATH,
            transport.OVERRIDE)
    hub = transport.Hub()
    transport.OVERRIDE = lambda dev, data: transport.Loopback(dev.get("id") or "", hub=hub)

    def at(who):
        server_mod.CONFIG_PATH = who["config"]
        server_mod.ROOT_OVERRIDE = None
        team.DEVICE_PATH = None

    def wt(who, **body):
        at(who)
        return routes.api_team(dict(body, root=str(who["root"])))

    def tb(who, **body):
        at(who)
        return routes.api_team_board(dict(body, workbook=str(who["book"])))

    def run(who, *args):
        code, out, err = cli.run(["--config", str(who["config"]), "--root", str(who["root"]), "--json", *args])
        got = support.plain(json.loads(out)) if out.strip() else {}
        return code, got, err + (got.get("error", "") if code else "")

    def boards(who) -> list[dict]:
        at(who)
        return themes.boards_of(themes.load(who["book"]) or {})

    def plan(name: str, pets: list) -> Path:
        path = base / f"{name}.json"
        path.write_text(json.dumps({"pets": [{"title": t, "members": m} for t, m in pets]}), encoding="utf-8")
        return path

    def refused(fn) -> str:
        try:
            fn()
            return ""
        except WorkbookError as exc:
            return str(exc)

    try:
        # 1. off: nothing shown and nothing written
        before = sorted(p.name for p in off_root.rglob("*"))
        shown = tb(off, op="show")
        taken = tb(off, op="take")
        check("351: while Working together is off the boards are off alone, a take brings nothing and writes nothing, "
              "and the menu's item is not there",
              shown == {"board": {"on": False}} and taken == {"board": {"on": False}}
              and sorted(p.name for p in off_root.rglob("*")) == before, json.dumps([shown, taken]))

        # the team: Adam the lead, who works on every participant, Curt joined from an invite
        wt(adam, op="on", name="Adam")
        made = wt(adam, op="invite")
        wt(curt, op="join", words=made["words"], name="Curt")
        wt(adam, op="admit", invite=made["invite"], match=True)
        done = wt(curt, op="joined", invite=made["invite"])
        check("351: the two installs make a team, Adam its lead", done.get("joined") is True, json.dumps(done)[:300])

        # the page's first save of a board of Wren in Curt's copy, Wren Adam's with no board yet (landreview, 9 November
        # 2026): the canvas offers v1, it is written as Curt's own under an id of his own, and the answer names that id
        # so the page takes it at once and its next save goes through
        at(curt)
        wren = curt_root / "P2 - Wren" / "P2 - Wren - EN & ES.xlsx"
        offered = routes.api_themes({"workbook": str(wren)})
        first = dict(themes.blank_version(themes.read_cards(wren)["cards"]), id=offered["current"])
        at(curt)
        saved1 = routes.api_themes_save({"workbook": str(wren), "version": first})
        took = (saved1.get("version") or {}).get("id") or ""
        at(curt)
        saved2 = routes.api_themes_save({"workbook": str(wren), "version": dict(first, id=took,
                                                                                v=saved1["version"].get("v"))})
        at(curt)
        wren_boards = themes.boards_of(themes.load(wren) or {})
        check("351: Curt's first board of a participant of Adam's with none yet is written as his own, the save's answer "
              "naming its own id, and the next save under that id goes through",
              offered["current"] == themes.FIRST_VERSION and took.startswith(themes.OWN_ID)
              and saved2.get("saved") is True and [b["id"] for b in wren_boards] == [took]
              and all(b.get(themes.OWN) for b in wren_boards)
              and not themes.themes_path(wren).exists(), json.dumps([saved1, saved2])[:400])

        # Curt's own boards of Hollis, made in his copy with the one writer on (ownboards, 9 November 2026): Hollis is
        # Adam's, so they are kept apart in Curt's team folder, and Adam's PETs file in Curt's copy is never written
        import workbook as wb_guard
        pets_file = themes.themes_path(curt_book)
        theirs_before = pets_file.read_bytes() if pets_file.exists() else b""
        guarded = wb_guard.WRITE_GUARD is not None
        his = []
        for i, pets in enumerate(([("The hive felt, not opened", ["S1", "S2"]), ("Waiting for spring", ["S3", "S5"])],
                                  [("All of it", ["S1", "S2", "S3", "S4", "S5"])]), start=1):
            his.append(run(curt, "board", "new", "Hollis", "--from", str(plan(f"curt{i}", pets)), "--note",
                           "Curt's grouping", "--tool", "Claude Code"))
        at(curt)
        own_at = team_board.own_file(curt_book)
        theirs_after = pets_file.read_bytes() if pets_file.exists() else b""
        check("351: Curt's two boards made in his copy with the one writer on, kept apart in his team folder, "
              "Adam's PETs file in his copy untouched",
              guarded and all(c == 0 for c, _, _ in his) and own_at is not None and own_at.is_file()
              and ".idiograph-team" in own_at.parts and theirs_after == theirs_before
              and len(themes.boards_of(json.loads(own_at.read_text(encoding="utf-8")))) == 2,
              " ".join(e for _, _, e in his) + str(own_at))
        curt_boards = boards(curt)
        sent_board = next(b for b in curt_boards if any(g["label"] == "Waiting for spring" for g in b["groups"]))
        other_board = next(b for b in curt_boards if any(g["label"] == "All of it" for g in b["groups"]))
        listed = run(curt, "board", "list", "Hollis")[1].get("boards") or []
        check("351: his boards list shows them as any board, each marked his own",
              all(b.get(themes.OWN) for b in (sent_board, other_board))
              and sorted(x["id"] for x in listed if x.get("own")) == sorted([sent_board["id"], other_board["id"]])
              and all(str(x["id"]).startswith(themes.OWN_ID) for x in listed if x.get("own")),
              json.dumps(listed)[:400])

        # Curt edits his own board, from the app's route and an agent's op, with dry runs and History as any board
        at(curt)
        before_dry = own_at.read_bytes()
        dry_rename = routes.api_themes_versions({"workbook": str(curt_book), "op": "rename", "id": other_board["id"],
                                                 "name": "Everything at once", "dry_run": True})
        same_after_dry = own_at.read_bytes()
        at(curt)
        renamed = routes.api_themes_versions({"workbook": str(curt_book), "op": "rename", "id": other_board["id"],
                                              "name": "Everything at once"})
        noted = run(curt, "board", "rename", "Hollis", "Everything at once", "One broad PET", "--note",
                    "Curt's rename", "--tool", "Claude Code")
        dry_note = run(curt, "board", "rename", "Hollis", "One broad PET", "Never this", "--dry-run")
        at(curt)
        mine_now = {b["id"]: b for b in themes.boards_of(json.loads(own_at.read_text(encoding="utf-8")))}
        revs = [r.get("name") or "" for r in themes.history_of(mine_now[other_board["id"]])]
        check("351: Curt renames his own board from the app and from the command line, a dry run writing nothing, "
              "each kept in his own file, the agent's rename in the board's History, and Adam's PETs file in his copy "
              "still untouched",
              dry_rename.get("dry_run") is True and same_after_dry == before_dry and noted[0] == 0 and dry_note[0] == 0
              and any(v["name"] == "Everything at once" for v in renamed.get("versions") or [])
              and mine_now[other_board["id"]]["name"] == "One broad PET"
              and any("Everything at once" in r for r in revs)
              and (pets_file.read_bytes() if pets_file.exists() else b"") == theirs_before,
              noted[2] + dry_note[2] + json.dumps(revs))
        other_board = dict(other_board, name="One broad PET")

        # the owner's boards stay the owner's: an edit to one of Adam's in Curt's copy is the one writer's refusal
        own_adam = run(adam, "board", "new", "Hollis", "--from", str(plan("adam0", [("Cold months", ["S1", "S4"])])),
                       "--note", "Adam's first", "--tool", "Claude Code")
        own_bytes = own_at.read_bytes()
        at(adam)
        gave = team_sync.sync(adam_root, now=True)
        at(curt)
        got = team_sync.sync(curt_root, now=True)
        at(curt)
        check("351: a new version of Hollis from Adam leaves Curt's own boards as they were, and Curt's sync sends "
              "no version of Hollis",
              "P1 - Hollis" in (gave.get("sent") or []) and "P1 - Hollis" in (got.get("applied") or [])
              and own_at.read_bytes() == own_bytes and not got.get("sent"),
              json.dumps({"gave": gave, "got": got}))
        at(curt)
        adams = [b for b in boards(curt) if not b.get(themes.OWN)]
        touched = run(curt, "board", "rename", "Hollis", adams[0]["id"] if adams else "v1", "Curt's name for it",
                      "--note", "Rename Adam's", "--tool", "Claude Code") if adams else (0, {}, "")
        check("351: Adam's new version comes into Curt's copy beside Curt's own boards, and Curt's rename of Adam's "
              "board is refused as Adam's",
              own_adam[0] == 0 and [b["name"] for b in adams] == ["Board 1"] and touched[0] != 0
              and "is Adam's" in touched[2] and len([b for b in boards(curt) if b.get(themes.OWN)]) == 2,
              touched[2] + json.dumps([b["name"] for b in boards(curt)]))

        # 2. Adam's own participant has nobody to send to
        at(adam)
        mine = refused(lambda: tb(adam, op="send", board="Board 1"))
        show_adam = tb(adam, op="show")["board"]
        show_curt = tb(curt, op="show")["board"]
        check("351: Send board is offered on a participant someone else works on, to them, and refused on one's own",
              show_curt.get("can_send") is True and show_curt.get("owner") == "Adam" and show_adam.get("can_send") is False
              and mine == "P1 - Hollis is yours, so there is nobody to send this board to.", mine + json.dumps(show_curt)[:200])

        # meanwhile Adam rewords one statement of his
        set_statements(adam_book, 7, ["Taking the loss of a colony as his own fault"])

        # 3. Curt sends Board 2 from the command line, as Send board does
        dry = run(curt, "team", "board-send", "Hollis", "--board", sent_board["id"], "--dry-run")
        nothing_yet = hub.boxes.copy()
        code, sent, err = run(curt, "team", "board-send", "Hollis", "--board", sent_board["id"], "--note",
                              "Send Adam my grouping", "--tool", "Claude Code")
        team_id = team.read_team(adam_root)["team"]
        box = hub.boxes.get(team_id) or []
        raw = box[-1][2] if box else b""
        check("351: a dry run sends nothing, and the send seals the board to the team: the relay's bytes carry no title, "
              "no statement and no name",
              dry[0] == 0 and nothing_yet == {k: v for k, v in hub.boxes.items() if k in nothing_yet} and code == 0
              and sent.get("to") == "Adam" and raw and b"Waiting for spring" not in raw and b"Hollis" not in raw
              and b"Curt" not in raw, err)
        theirs_sent = refused(lambda: tb(curt, op="send", board=adams[0]["id"])) if adams else ""
        at(curt)
        curt_dev = (team.device() or {}).get("id")
        at(adam)
        roster = team.read_team(adam_root)["roster"]
        kinds = [team.open_envelope(r, roster, team.project_keys(team_id)).get("kind")
                 for _, d, r in (hub.boxes.get(team_id) or []) if d == curt_dev]
        check("351: only a board of his own goes, and what Curt's install has sent is boards, never a version",
              theirs_sent == "Board 1 is Adam's and can't be changed from here."
              and "board" in kinds and not {"version", "gets_version"} & set(kinds), theirs_sent + json.dumps(kinds))

        # 4. Adam's PETs screen takes it in: it waits, nothing written to Hollis, until Add as next board
        own = run(adam, "board", "new", "Hollis", "--from", str(plan("adam", [("Weather and waiting", ["S1", "S3"])])),
                  "--note", "Adam's own", "--tool", "Claude Code")
        at(adam)
        current_before = (themes.load(adam_book) or {}).get("current")
        check("351: Adam's own board of Hollis, current", own[0] == 0 and current_before, own[2])
        hollis = {str(p.relative_to(adam_root)): p.read_bytes() for p in sorted((adam_root / "P1 - Hollis").rglob("*"))
                  if p.is_file()}
        n_boards = len(boards(adam))
        came = tb(adam, op="take")
        at(adam)
        after_take = {str(p.relative_to(adam_root)): p.read_bytes()
                      for p in sorted((adam_root / "P1 - Hollis").rglob("*")) if p.is_file()}
        waiting = came["board"].get("waiting") or []
        check("351: Curt's board comes in on Adam's install and waits for his answer: Hollis's files byte for byte as "
              "they were, no board added, and the board kept whole in the team folder's record",
              len(came.get("came") or []) == 1 and after_take == hollis and len(boards(adam)) == n_boards
              and [w["ref"] for w in waiting] == [came["came"][0]["ref"]] and "held" not in waiting[0]
              and isinstance((team_board.read_ledger(adam_root)["came"][0].get("held") or {}).get("board"), dict),
              json.dumps(came)[:500])

        # 5. taken in once
        again = tb(adam, op="take")
        check("351: a second take brings nothing", not again.get("came") and len(boards(adam)) == n_boards,
              json.dumps(again)[:300])

        # 6. an agent's answer is the app's alone, since it goes back to the teammate (noholds, 13 November 2026),
        # and the app's Add as next board adds it
        kept_ops, agent_changes.ALL_OPS = agent_changes.ALL_OPS, None
        try:
            code, held, err = run(adam, "team", "board-answer", "--ref", came["came"][0]["ref"], "--note",
                                  "Keep Curt's", "--tool", "Claude Code")
        finally:
            agent_changes.ALL_OPS = kept_ops
        waiting = tb(adam, op="show")["board"].get("waiting") or []
        check("351: an agent's answer to a teammate's board is refused as the app's alone, nothing answered",
              code != 0 and "Only the app does this" in err and len(waiting) == 1, err + json.dumps(held)[:300])
        yes = tb(adam, op="answer", ref=came["came"][0]["ref"], accept=True)
        after = boards(adam)
        new = next((b for b in after if b["id"] == yes.get("added")), {})
        day = routes.day_said(came["came"][0]["sent"])
        groups = {g["label"]: sorted(g["members"]) for g in new.get("groups", [])}
        want = {g["label"]: sorted(g["members"]) for g in sent_board["groups"]}
        check("351: Add as next board adds Curt's board as Hollis's next board, never current, named whose and when, "
              "every PET and card where Curt put it, and the screen's answer carries the boards",
              new and new.get("name") == f"Curt's board, {day}"
              and (themes.load(adam_book) or {}).get("current") == current_before != new.get("id")
              and groups == want and {"Waiting for spring", "The hive felt, not opened"} == set(groups)
              and any(v["id"] == new.get("id") for v in (yes.get("state") or {}).get("versions") or []),
              json.dumps({"yes": {k: v for k, v in yes.items() if k != "state"}, "groups": groups})[:600])
        hist = themes.history_of(new)
        check("351: its note says whose board and when it was sent and how its statements came, the reworded one "
              "counted, then Curt's own note, and its History says who sent it",
              new.get("note", "").startswith(f"Curt's board, sent {day}: ") and "1 reworded since" in new.get("note", "")
              and new.get("note", "").endswith("\n" + sent_board["note"])
              and [r.get("name") for r in hist] == ["Sent by Curt"]
              and (new.get("origin") or {}).get("team") == came["came"][0]["ref"],
              json.dumps({"note": new.get("note"), "hist": [r.get("name") for r in hist]}))
        at(curt)
        mcp = mcp_server.Server(root=str(curt_root), config=str(curt["config"]))
        res = mcp.call(mcp.by_name["team_board_take"], {"request": "See what Adam said"})
        heard = support.plain(res.get("structuredContent") or {}) if not res.get("isError") else {}
        at(curt)
        sent_rec = team_board.read_ledger(curt_root)["sent"]
        check("351: Curt's install, through MCP's team_board_take, hears it was accepted",
              [a.get("accept") for a in heard.get("answers") or []] == [True]
              and [s.get("answer") for s in sent_rec] == ["accepted"], json.dumps(heard)[:400] + json.dumps(res)[:200])
        twice = refused(lambda: tb(adam, op="answer", ref=came["came"][0]["ref"], accept=False))

        # 7. Board 3 sent, and declined: nothing written to Hollis
        tb(curt, op="send", board=other_board["id"])
        came3 = tb(adam, op="take")
        at(adam)
        hollis = {str(p.relative_to(adam_root)): p.read_bytes() for p in sorted((adam_root / "P1 - Hollis").rglob("*"))
                  if p.is_file()}
        no = tb(adam, op="answer", workbook=str(adam_book), accept=False, reason="One PET is too broad")
        at(adam)
        same = {str(p.relative_to(adam_root)): p.read_bytes() for p in sorted((adam_root / "P1 - Hollis").rglob("*"))
                if p.is_file()} == hollis
        tb(curt, op="take")
        at(curt)
        sent_rec = team_board.read_ledger(curt_root)["sent"]
        check("351: Decline writes nothing to Hollis's files, the answer reaching Curt with its reason, and a board "
              "answered before is refused a second answer",
              came3.get("came") and no.get("accept") is False and same
              and [s.get("answer") for s in sent_rec] == ["accepted", "declined"]
              and sent_rec[1].get("reason") == "One PET is too broad"
              and twice == "That board has been answered already.", json.dumps(sent_rec)[:400] + twice)

        # 8. History on both sides
        at(adam)
        a_hist = [h["op"] for h in json.loads((adam_root / "idiograph-history.json").read_text(encoding="utf-8"))["history"]]
        c_hist = json.loads((curt_root / "idiograph-history.json").read_text(encoding="utf-8"))["history"]
        check("351: each step is a line in the project's History, the sender's send with its tool and the answers "
              "heard",
              a_hist.count("team board-take") == 2 and a_hist.count("team board-answer") == 2
              and any(h["op"] == "team board-send" and h.get("tool") == "Claude Code" for h in c_hist)
              and any(f"Adam declined your {other_board['name']} of P1 - Hollis." in h["changes"] for h in c_hist),
              json.dumps(a_hist) + json.dumps([h["changes"] for h in c_hist])[:400])

        # 9. one loop: the server's own look, team_sync's, takes a board in and hears its answer, as the PETs
        # screen's take does (landwt, 9 November 2026)
        tb(curt, op="send", board=sent_board["id"])
        at(adam)
        looked = team_sync.sync(adam_root)
        later = tb(adam, op="take")
        at(adam)
        fourth = next((x for x in team_board.read_ledger(adam_root)["came"] if not x.get("answer")), {})
        added = tb(adam, op="answer", ref=fourth.get("ref") or "", accept=True)
        at(curt)
        heard = team_sync.sync(curt_root)
        at(curt)
        sent_rec = team_board.read_ledger(curt_root)["sent"]
        check("351: the server's loop takes a teammate's board in to wait, a take after it bringing nothing, and on "
              "the sender's install hears the answer",
              looked.get("taken") == ["board"] and not later.get("came") and fourth
              and any(b["id"] == added.get("added") for b in boards(adam)) and heard.get("taken") == ["board"]
              and [x.get("answer") for x in sent_rec] == ["accepted", "declined", "accepted"],
              json.dumps({"looked": looked, "heard": heard, "sent": [x.get("answer") for x in sent_rec]})[:500])

        # 10. a board of a participant with no board yet (smokefix, 9 November 2026, the live relay test): Curt's board
        # of Wren, whom Adam has no board of, comes in as Wren's only board and on the canvas, no empty Board 1 beside it
        adam_wren = adam_root / "P2 - Wren" / wren.name
        at(adam)
        none_before = themes.boards_of(themes.load(adam_wren) or {})
        at(curt)
        routes.api_team_board({"op": "send", "workbook": str(wren), "board": took})
        at(adam)
        wren_came = routes.api_team_board({"op": "take", "workbook": str(adam_wren)})
        ref = ((wren_came.get("came") or [{}])[0]).get("ref") or ""
        at(adam)
        only = routes.api_team_board({"op": "answer", "workbook": str(adam_wren), "ref": ref, "accept": True})
        at(adam)
        wren_file = themes.load(adam_wren) or {}
        check("351: Curt's board of a participant Adam has no board of becomes that participant's only board, on the "
              "canvas, with no empty Board 1 made beside it",
              not none_before and ref and [b["id"] for b in themes.boards_of(wren_file)] == [only.get("added")]
              and wren_file.get("current") == only.get("added")
              and themes.boards_of(wren_file)[0]["name"].startswith("Curt's board, "),
              json.dumps({"added": only.get("added"), "file": {k: v for k, v in wren_file.items() if k != "boards"},
                          "names": [b.get("name") for b in themes.boards_of(wren_file)]})[:500])
    finally:
        (server_mod.CONFIG_PATH, server_mod.ROOT_OVERRIDE, server_mod.STATE_MEMORY, team.DEVICE_PATH,
         transport.OVERRIDE) = kept
