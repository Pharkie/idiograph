"""Area 343: Working together's comments and review on the team layer (wtreview, 8 November 2026, the spec's build 4,
Adam's yes to its defaults about 19:10 by dialog, review comments drafts until Send review; wtreview2, 9 November
2026). Three scratch installs in one process, Adam's, Curt's and Ivy's, each its own settings file, device file and
copy of the project, joined as one team, every message sealed by team.py and carried by team_sync's one loop: first
through the loopback transport, then through the shared folder (folder_transport) as the app registers it.

What is checked: nothing shown or written while Working together is off. Adam asks Curt for review of Juno, sealed,
and Juno shows "With Curt for review" until Curt's review comes back. Curt's comments stay drafts on his computer,
nothing sent, until Send review. The review comes to Adam with its comments, his line and an agent's comment
labelled with its tool, a teammate's words marked untrusted for agents, a thread round trip (Adam's reply and his
Resolve reaching Curt), and the thread left open on Done kept unresolved on both. Curt's board of Juno waits on
Adam's install with nothing written to Juno's files, kept across a restart, until Add as next board adds it, not
current, with its note, and a second board declined leaves Juno's files byte for byte as they were, each answer
reaching Curt. A message from a computer not on the roster, and one sealed under an older epoch's key, are dropped
and noted. The same round trip goes through a shared folder. The team folder never travels in Share a copy.

The fixture is invented: the demo's three dog owners, copied for each install."""
from __future__ import annotations

import html as html_mod
import importlib
import json
import os
import re
import shutil
import subprocess
import tempfile
from pathlib import Path

from . import support
from .support import DEMO_SHIPPED, check, skip

ASKED = "Ask Curt to look at Juno."


def make_project(root: Path) -> None:
    shutil.rmtree(root, ignore_errors=True)
    root.mkdir(parents=True)
    for name in ("Juno", "Rowan", "Mabel"):
        case = root / name
        (case / "Working").mkdir(parents=True)
        shutil.copy2(DEMO_SHIPPED / f"{name} - EN & ES.xlsx", case / f"{name} - EN & ES.xlsx")
        for kind in ("progress", "themes"):
            side = DEMO_SHIPPED / "Working" / f"{name} - EN & ES.{kind}.json"
            if side.exists():
                shutil.copy2(side, case / "Working" / side.name)
    shutil.copy2(DEMO_SHIPPED / "idiograph-gets.json", root / "idiograph-gets.json")
    (root / "idiograph-project.json").write_text(json.dumps({
        "name": "Living with a dog", "agents": {"allowed": True, "at": "2026-11-08T09:00:00+00:00"}}), encoding="utf-8")


def files_of(folder: Path) -> dict:
    return {str(p.relative_to(folder)): p.read_bytes() for p in sorted(folder.rglob("*")) if p.is_file()}


def test_team_review(scratch: Path):
    print("\n343. Working together's comments and review on the team layer: sealed through team_sync's one loop by "
          "loopback and shared folder, drafts until Send review, a thread round trip, resolved and kept unresolved, "
          "With Curt for review, a board held until Add as next board, a declined one writing nothing, a stranger's "
          "and an old epoch's message dropped, nothing while off (wtreview2)")
    import cli
    import idiograph_routes as routes
    import mcp_server
    import project_history
    import project_pack
    import review
    import server as server_mod
    import team
    import team_board
    import team_sync
    import themes
    import transport
    from workbook import WorkbookError

    base = scratch / "team-343"
    shutil.rmtree(base, ignore_errors=True)
    homes = {}
    for who in ("adam", "curt", "ivy", "off"):
        root = base / who / "Dogs"
        make_project(root)
        cfg = base / who / "config.json"
        cfg.write_text(json.dumps({"projects": [{"root": str(root)}], "interviewer": who.title(), "your_name": who.title(),
                                   "corpus": "", "gravity_reference": "", "corpus_exclude": []}), encoding="utf-8")
        homes[who] = {"root": root, "config": cfg, "book": root / "Juno" / "Juno - EN & ES.xlsx"}
    A, C = homes["adam"]["root"], homes["curt"]["root"]
    kept = (server_mod.CONFIG_PATH, server_mod.ROOT_OVERRIDE, server_mod.STATE_MEMORY, team.DEVICE_PATH,
            transport.OVERRIDE, os.environ.pop(transport.ENV, None))
    hub = {"hub": transport.Hub()}
    transport.OVERRIDE = lambda dev, data: transport.Loopback(dev.get("id") or "", hub=hub["hub"])

    def at(who):
        server_mod.CONFIG_PATH = homes[who]["config"]
        server_mod.ROOT_OVERRIDE = None
        server_mod.STATE_MEMORY = {"recent": []}
        team.DEVICE_PATH = None

    def page(who, body):
        at(who)
        return routes.api_team_review(dict(body, root=routes.project_id(homes[who]["root"])))

    def wt(who, **body):
        at(who)
        return routes.api_team(dict(body, root=str(homes[who]["root"])))

    def tb(who, **body):
        at(who)
        return routes.api_team_board(dict(body, root=str(homes[who]["root"])))

    def sync(who):
        at(who)
        return team_sync.sync(homes[who]["root"])

    def answer(who, *args, raw=False):
        at(who)
        code, out, err = cli.run(["--config", str(homes[who]["config"]), "--root", str(homes[who]["root"]), "--json",
                                  *args])
        got = json.loads(out) if out.strip() else {}
        return code, (got if raw else support.plain(got)), err + (json.dumps(got.get("error", "")) if code != 0 else "")

    def ask(who, *args):
        return answer(who, *args, "--note", ASKED, "--tool", "Claude Code")

    def mark() -> dict:
        return {name: len(box) for name, box in hub["hub"].boxes.items()}

    def sent_since(was: dict) -> list[bytes]:
        # each mailbox's own new messages, so a message added to one box is never counted as another's (winfix)
        return [raw for name, box in hub["hub"].boxes.items() for _n, _d, raw in box[was.get(name, 0):]]

    def log_of(root: Path) -> str:
        path = root / team.LOG_DIR / "log.jsonl"
        return path.read_text(encoding="utf-8") if path.exists() else ""

    def join(who, name):
        made = wt("adam", op="invite")
        wt(who, op="on", name=name)
        wt(who, op="join", words=made["words"], name=name)
        wt("adam", op="admit", invite=made["invite"], match=True)
        return wt(who, op="joined", invite=made["invite"])

    try:
        # a server's looks left running in this process by an earlier area would send for these installs between
        # the steps below, as they did on Windows (winfix, 9 November 2026)
        looks = team_sync._THREAD.get("thread")
        check("343: no server's Working together looks run in the suite's process",
              not (looks and looks.is_alive()), str(looks))
        # 1. off: nothing shown, every op refused, nothing written
        off = page("off", {"op": "state"})
        code, _g, err = ask("off", "team", "ask", "Juno", "--to", "Curt")
        refused = False
        try:
            page("off", {"op": "comment", "case": "Juno", "on": {"kind": "statement", "key": "Initial:5:0"}, "text": "x"})
        except WorkbookError:
            refused = True
        at("off")
        check("343: with Working together off the page is told nothing, there is no tag, and the ops refuse, writing "
              "nothing",
              off == {"on": False} and code != 0 and refused and team_sync.status(homes["off"]["root"]) is None
              and review.review_with(homes["off"]["root"]) == {}
              and not (homes["off"]["root"] / team.LOG_DIR).exists(), err + json.dumps(off))

        # the team: Adam its lead, Curt and Ivy joined from invites, Mabel Curt's
        wt("adam", op="on", name="Adam")
        joined = [join("curt", "Curt"), join("ivy", "Ivy")]
        wt("adam", op="set", owners={"Mabel": "Curt"})
        for who in ("curt", "ivy", "adam", "curt"):
            sync(who)
        st = page("curt", {"op": "state", "case": "Juno"})
        check("343: on, Curt's install knows him, Juno's owner and his own Mabel from the roster team.py keeps",
              all(j.get("joined") for j in joined) and st.get("on") is True and st.get("me") == "Curt"
              and st.get("owner") == "Adam" and st.get("mine") is False
              and st["owners"]["Mabel"] == {"name": "Curt", "mine": True}, json.dumps(st)[:400])

        # 2. Adam asks Curt to review Juno, a dry run first: sealed, and Juno tagged With Curt for review
        n_hist = len(project_history.load(A))
        n_sent = mark()
        code, dry, err = ask("adam", "team", "ask", "Juno", "--to", "Curt", "--line", "Is the regret one PET or two?",
                             "--dry-run")
        after_dry = len(sent_since(n_sent))
        code2, got, err2 = ask("adam", "team", "ask", "Juno", "--to", "Curt", "--line", "Is the regret one PET or two?")
        code3, _x, err3 = ask("adam", "team", "ask", "Mabel", "--to", "Curt")
        hist = project_history.load(A)
        news = sent_since(n_sent)
        at("adam")
        tags = team_sync.status(A)["tags"]
        check("343: Ask for review goes once, sealed (no line and no name in the bytes the transport carries), its dry "
              "run sending nothing, with its History record, an ask on a teammate's participant refused, and Juno "
              "tagged With Curt for review",
              code == 0 and dry.get("dry_run") is True and after_dry == 0 and code2 == 0 and len(news) == 1
              and b"regret" not in news[0] and b"Juno" not in news[0] and code3 != 0
              and len(hist) == n_hist + 1 and hist[-1]["op"] == "team ask" and hist[-1]["by"] == "agent"
              and hist[-1]["changes"] == ["Asked Curt to review Juno."] and tags.get("Juno") == {"review": "Curt"},
              json.dumps({"codes": [code, code2, code3], "sent": [sum(n_sent.values()), after_dry, len(news)], "dry": dry,
                          "words": [b"regret" in b or b"Juno" in b for b in news], "hist": [n_hist, len(hist)],
                          "last": hist[-1:], "tags": tags}) + err + err2)
        sync("curt")
        st = page("curt", {"op": "state", "case": "Juno"})
        check("343: the ask comes to Curt's install through team_sync's loop with Adam's line",
              [(a["from"], a["to"], a["line"]) for a in st["asks"]] == [("Adam", ["Curt"], "Is the regret one PET or two?")],
              json.dumps(st["asks"]))

        # the live relay test's findings (smokefix, 9 November 2026). Send now with no --note goes, since it writes no
        # History to name a request in, and through MCP with no request
        n_hist_c = len(project_history.load(C))
        code_send, sent_now, err_send = answer("curt", "team", "send", "--tool", "Claude Code")
        at("curt")
        mcp = mcp_server.Server(root=str(C), config=str(homes["curt"]["config"]))
        by_mcp = mcp.call(mcp.by_name["team_send"], {})
        check("343: team send with no --note, and MCP's team_send with no request, go and write no History",
              code_send == 0 and "sent" in sent_now and not by_mcp.get("isError")
              and "request" not in (mcp.by_name["team_send"]["inputSchema"].get("required") or [])
              and len(project_history.load(C)) == n_hist_c, err_send + json.dumps(by_mcp)[:300])
        # a write of a passage of Adam's from Curt's copy is refused in Adam's words first, though it would change
        # nothing, its dry run too, where Adam's own same write answers that there is nothing to write
        _c, turns, _e = answer("adam", "turn", "show", "Juno", "Initial", "1-80")
        same = next((t for t in turns.get("turns") or [] if t.get("notes")), {})
        spec_path = base / "same-notes.json"
        spec_path.write_text(json.dumps({"notes": same.get("notes") or []}), encoding="utf-8")
        juno_c = files_of(C / "Juno")
        his = answer("curt", "turn", "write", "Juno", "Initial", str(same.get("row")), "--from", str(spec_path),
                     "--note", "Keep the notes", "--tool", "Claude Code")
        his_dry = answer("curt", "turn", "write", "Juno", "Initial", str(same.get("row")), "--from", str(spec_path),
                         "--dry-run")
        owners = answer("adam", "turn", "write", "Juno", "Initial", str(same.get("row")), "--from", str(spec_path),
                        "--note", "Keep the notes", "--tool", "Claude Code")
        theirs = "Juno is Adam's. Comment or suggest instead."
        check("343: Curt's unchanged write of Adam's passage is refused as Adam's, its dry run too, nothing written, "
              "while Adam's own answers that nothing would change",
              same and his[0] != 0 and theirs in his[2] and "Nothing to write" not in his[2] and his_dry[0] != 0
              and theirs in his_dry[2] and files_of(C / "Juno") == juno_c and owners[0] == 0
              and owners[1].get("changed") is False, json.dumps([his[2], his_dry[2], owners[1]])[:500])

        # 3. Curt's comments are drafts: a passage from the page, a PET by his agent, nothing sent
        page("curt", {"op": "comment", "case": "Juno", "dry_run": True, "on": {"kind": "statement", "key": "Initial:5:0"},
                      "text": "dry"})
        n_sent = mark()
        c1 = page("curt", {"op": "comment", "case": "Juno", "text": "Is this experiential or her summing up?",
                           "on": {"kind": "passage", "key": "Initial:5", "time": "21:45",
                                  "words": "if you asked me to describe home"}})
        code, _c2, err = ask("curt", "team", "comment", "Juno", "--on", "pet", "--key", "g4",
                             "--words", "Grieving in advance", "--text", "Two PETs here?")
        refused = False
        try:
            page("curt", {"op": "comment", "case": "Mabel", "on": {"kind": "statement", "key": "Initial:3:0"}, "text": "x"})
        except WorkbookError:
            refused = True
        st = page("curt", {"op": "state", "case": "Juno"})
        drafted = len(sent_since(n_sent))
        sync("adam")
        adam = page("adam", {"op": "state", "case": "Juno"})
        check("343: Curt's comments stay drafts until Send review: nothing goes to the transport, nothing reaches Adam's "
              "install, and a comment on his own participant is refused",
              code == 0 and c1.get("id") and len(st["drafts"]) == 2 and drafted == 0 and refused
              and not adam["threads"] and not adam["reviews"], err + json.dumps(st["drafts"])[:300])

        # 4. Send review: the comments and the review go, and Adam's install shows one review not read
        code, _sent, err = ask("curt", "team", "review-send", "Juno")
        st = page("curt", {"op": "state", "case": "Juno"})
        went = len(sent_since(n_sent))
        sync("adam")
        adam = page("adam", {"op": "state", "case": "Juno"})
        rv = (adam["reviews"] or [{}])[0]
        th = {x["on"]: x for x in adam["threads"]}
        at("adam")
        tags = team_sync.status(A)["tags"]
        check("343: Send review sends both comments and the review, sealed, Curt's drafts emptied, and Adam's install "
              "has the review, not read, with his own question and each comment's words and author, the agent's "
              "labelled, and Juno's review tag gone now it has come back",
              code == 0 and not st["drafts"] and went == 3 and rv.get("from") == "Curt (Claude Code)"
              and rv.get("seen") is False and rv.get("comments") == 2 and rv.get("asked") == "Is the regret one PET or two?"
              and th["passage"]["quote"] == "if you asked me to describe home" and th["passage"]["time"] == "21:45"
              and th["passage"]["comments"][0]["by"] == "Curt"
              and th["pet"]["comments"][0]["by"] == "Curt (Claude Code)" and "Juno" not in tags,
              err + json.dumps(adam)[:600] + json.dumps(tags))

        # 5. a teammate's words reach an agent marked untrusted
        code, raw, err = answer("adam", "team", "review", "Juno", raw=True)
        texts = [c["text"] for t in raw.get("threads", []) for c in t["comments"]]
        quotes = [t["quote"] for t in raw.get("threads", [])]
        check("343: team review's answer marks each comment and each quoted passage as untrusted text",
              code == 0 and texts and all(isinstance(x, dict) and set(x) == {cli.UNTRUSTED} for x in texts + quotes),
              err + json.dumps(raw)[:400])

        # 6. Adam replies in the passage's thread (MCP), resolves it, and Done keeps the PET's unresolved
        at("adam")
        mcp = mcp_server.Server(root=str(A), config=str(homes["adam"]["config"]))
        res = mcp.call(mcp.by_name["team_reply"], {"thread": th["passage"]["id"], "text": "Summing up, keeping it.",
                                                   "request": "Reply to Curt."})
        page("adam", {"op": "thread", "thread": th["passage"]["id"], "state": "resolved"})
        page("adam", {"op": "done", "review": rv["id"]})
        adam = page("adam", {"op": "state", "case": "Juno"})
        sync("curt")
        curt = page("curt", {"op": "state", "case": "Juno"})
        cth = {x["on"]: x for x in curt["threads"]}
        hist = [h["op"] for h in project_history.load(A)]
        check("343: a thread round trip: Adam's reply, by his agent and labelled so, and his Resolve reach Curt, and "
              "the thread left open on Done is kept unresolved and still on view on both",
              not res.get("isError") and [r["seen"] for r in adam["reviews"]] == [True]
              and [c["text"] for c in cth["passage"]["comments"]] == ["Is this experiential or her summing up?",
                                                                      "Summing up, keeping it."]
              and cth["passage"]["comments"][1]["by"] == "Adam (an AI agent)" and cth["passage"]["status"] == "resolved"
              and cth["pet"]["status"] == "unresolved" and {x["on"] for x in adam["threads"]} == {"passage", "pet"}
              and {x["on"]: x["status"] for x in adam["threads"]}["pet"] == "unresolved"
              and hist[-3:] == ["team reply", "team thread", "team review done"],
              json.dumps(res)[:200] + json.dumps(curt["threads"])[:600] + str(hist[-4:]))

        # 7. a board Curt sends of Juno waits on Adam's install, nothing written to Juno, until Add as next board
        juno = A / "Juno"
        before = files_of(juno)
        # only a board of his own goes (ownboards, 9 November 2026): Curt duplicates Adam's into one of his own first
        at("curt")
        mine = routes.api_themes_versions({"workbook": str(homes["curt"]["book"]), "op": "duplicate",
                                           "id": (themes.load(homes["curt"]["book"]) or {}).get("current")})
        own_id = mine.get("current")
        tb("curt", op="send", workbook=str(homes["curt"]["book"]), board=own_id)
        took = sync("adam")
        waiting = files_of(juno)
        adam = page("adam", {"op": "state", "case": "Juno"})
        board_rv = next((r for r in adam["reviews"] if r.get("boards")), {})
        b1 = (board_rv.get("boards") or [{}])[0]
        at("adam")
        current = (themes.load(homes["adam"]["book"]) or {}).get("current")
        check("343: Curt's board of Juno comes in and waits: Juno's files byte for byte as they were, and it shows on "
              "Adam's line and card as Curt's review holding only a board, beside the board on the canvas",
              took.get("taken") == ["board"] and waiting == before and board_rv.get("from") == "Curt"
              and board_rv.get("comments") == 0 and board_rv.get("seen") is False and b1.get("answer") == ""
              and b1.get("case") == "Juno" and b1.get("beside"),
              json.dumps(took) + json.dumps(adam["reviews"])[:500])

        # a restart: the record on disk holds the board whole, the modules read afresh, and it still waits
        on_disk = json.loads((A / team.LOG_DIR / team_board.LEDGER).read_text(encoding="utf-8"))["came"]
        importlib.reload(team_board)
        importlib.reload(review)
        sync("adam")
        again = page("adam", {"op": "state", "case": "Juno"})
        still = [b for r in again["reviews"] for b in r.get("boards") or []]
        check("343: a board waiting is kept across a restart, whole in the team folder's record, nothing written "
              "meanwhile",
              [b["ref"] for b in still] == [b1.get("ref")] and files_of(juno) == before
              and isinstance((on_disk[-1].get("held") or {}).get("board"), dict) and on_disk[-1].get("answer") == "",
              json.dumps(again["reviews"])[:400])

        added = tb("adam", op="answer", ref=b1["ref"], accept=True, workbook=str(homes["adam"]["book"]))
        at("adam")
        held = themes.load(homes["adam"]["book"]) or {}
        new = next((v for v in themes.boards_of(held) if v.get("id") == added.get("added")), {})
        day = routes.day_said(b1.get("sent") or "")
        sync("curt")
        at("curt")
        sent_rec = team_board.read_ledger(C)["sent"]
        after_add = page("adam", {"op": "state", "case": "Juno"})
        check("343: Add as next board adds it to Juno as the next board, not current, named whose and when, with the "
              "wording 2 note and its History, the review answered off the line, and the answer reaching Curt",
              added.get("accept") is True and new and held.get("current") == current != new.get("id")
              and new.get("name") == f"Curt's board, {day}" and new.get("note", "").startswith(f"Curt's board, sent {day}: ")
              and [r.get("name") for r in themes.history_of(new)] == ["Sent by Curt"]
              and not any(r.get("boards") for r in after_add["reviews"])
              and [s.get("answer") for s in sent_rec] == ["accepted"],
              json.dumps({"current": [current, held.get("current")], "new": {k: new.get(k) for k in ("id", "name", "note")},
                          "hist": [r.get("name") for r in themes.history_of(new)] if new else [],
                          "boards": [r.get("boards") for r in after_add["reviews"]], "sent": sent_rec})[:900])

        # 8. a second board declined: nothing written to Juno, the record keeping it with its reason, the answer back
        before = files_of(juno)
        tb("curt", op="send", workbook=str(homes["curt"]["book"]), board=own_id)
        sync("adam")
        b2 = next((b for r in page("adam", {"op": "state", "case": "Juno"})["reviews"] for b in r.get("boards") or []), {})
        no = tb("adam", op="answer", ref=b2.get("ref") or "", accept=False, reason="One board of these is enough")
        at("adam")
        came = team_board.read_ledger(A)["came"]
        sync("curt")
        at("curt")
        sent_rec = team_board.read_ledger(C)["sent"]
        check("343: Decline leaves Juno's files byte for byte as they were, the record and the team log keep it with "
              "its reason and without the board, and the answer reaches Curt with the reason",
              no.get("accept") is False and files_of(juno) == before
              and came[-1].get("answer") == "declined" and came[-1].get("reason") == "One board of these is enough"
              and "held" not in came[-1] and "board_declined" in log_of(A)
              and [s.get("answer") for s in sent_rec] == ["accepted", "declined"]
              and sent_rec[-1].get("reason") == "One board of these is enough",
              json.dumps(came[-1])[:300] + json.dumps(sent_rec)[:300])

        # 9. a stranger's message, and one sealed under an older epoch's key, are dropped and noted
        wt("adam", op="remove", member="Ivy")
        sync("curt")
        at("curt")
        tid = team.read_team(C)["team"]
        epoch = int(team.read_team(A)["roster"]["epoch"])
        at("ivy")
        ivy_dev = team.device()
        ivy = team.read_team(homes["ivy"]["root"])
        old_key = team.project_key(tid, 1)
        stranger = team.seal_envelope(tid, 1, old_key, ivy_dev, ivy["member"], team.next_seq(tid), "comment",
                                      {"id": "s1", "thread": cth["pet"]["id"], "text": "From off the roster",
                                       "on": {"participant": "Juno", "kind": "pet"}})
        transport.Loopback(ivy_dev["id"], hub=hub["hub"]).send(tid, stranger)
        at("curt")
        curt_dev = team.device()
        curt_data = team.read_team(C)
        old = team.seal_envelope(tid, 1, team.project_key(tid, 1), curt_dev, curt_data["member"], team.next_seq(tid),
                                 "comment", {"id": "o1", "thread": cth["pet"]["id"], "text": "Sealed with the old key",
                                             "on": {"participant": "Juno", "kind": "pet"}})
        transport.Loopback(curt_dev["id"], hub=hub["hub"]).send(tid, old)
        sync("adam")
        adam = page("adam", {"op": "state", "case": "Juno"})
        pet = {x["on"]: x for x in adam["threads"]}["pet"]
        log = log_of(A)
        check("343: after Ivy is removed and the key changes, her message and one of Curt's sealed under the old "
              "epoch's key are dropped and noted in the team log, the thread as it was",
              epoch == 2 and '"not_on_roster"' in log and '"old_epoch"' in log and len(pet["comments"]) == 1,
              log[-400:] + json.dumps(pet)[:300])

        # 10. the same round trip through a shared folder, the route the app registers, no loopback
        shared = base / "OneDrive" / "Dogs"
        shared.mkdir(parents=True)
        # the lead alone chooses the route (relaywire, 9 November 2026), and Curt's install follows it from the lead's
        # roster, naming the shared folder where it sits on his computer
        wt("adam", op="set", route="folder", folder=str(shared))
        sync("adam")
        sync("curt")
        wt("curt", op="set", folder=str(shared))
        transport.OVERRIDE = None
        ask("curt", "team", "reply", cth["pet"]["id"], "--text", "The waiting and the grief feel different.")
        sync("adam")
        adam = page("adam", {"op": "state", "case": "Juno"})
        pet = {x["on"]: x for x in adam["threads"]}["pet"]
        page("adam", {"op": "thread", "thread": pet["id"], "state": "resolved"})
        sync("curt")
        curt = page("curt", {"op": "state", "case": "Juno"})
        cpet = {x["on"]: x for x in curt["threads"]}["pet"]
        team_dir = next(shared.glob("Idiograph *"), None)
        check("343: through the shared folder Curt's reply opens the thread again on Adam's install and Adam's Resolve "
              "reaches Curt, each message a sealed file in its sender's own folder",
              [c["text"] for c in pet["comments"]][-1] == "The waiting and the grief feel different."
              and pet["status"] == "open" and cpet["status"] == "resolved" and team_dir is not None
              and any(p.suffix == ".sealed" for p in team_dir.rglob("*"))
              and not any(b"grief" in p.read_bytes() for p in team_dir.rglob("*.sealed")),
              json.dumps(pet)[:300] + json.dumps(cpet)[:200])

        # 11. the team folder never travels in Share a copy
        names = [rel for _p, rel in project_pack.project_files(A)]
        check("343: the team folder stays out of a send",
              names and not any(team.LOG_DIR in n for n in names), str(names[:5]))

        # 12. the reviewer's tray covers nothing
        _tray_clear(scratch)
    except WorkbookError as exc:
        check("343: the page's calls run", False, str(exc))
    finally:
        (server_mod.CONFIG_PATH, server_mod.ROOT_OVERRIDE, server_mod.STATE_MEMORY, team.DEVICE_PATH,
         transport.OVERRIDE, env) = kept
        if env is not None:
            os.environ[transport.ENV] = env


TRAY_DRIVER = r"""
const $ = (id) => document.getElementById(id);
const RVW = { st: { owner: 'Adam', case: 'Juno', drafts: [{ case: 'Juno' }, { case: 'Juno' }] } };
const rvwReviewer = () => true;
const rvwScreen = () => 'work';
const rvwCountsOf = (n) => n + ' comments';
"""

TRAY_AFTER = r"""
const box = (el) => { const r = el.getBoundingClientRect(); return { l: r.left, t: r.top, r: r.right, b: r.bottom }; };
const meets = (a, b) => a.l < b.r && a.r > b.l && a.t < b.b && a.b > b.t;
const at = (el) => { const r = el.getBoundingClientRect(); return document.elementFromPoint((r.left + r.right) / 2, (r.top + r.bottom) / 2); };
const run = () => { try {
  document.getElementById('work').hidden = false;
  const head = $('cols-head');
  // the headings stand where drawColumns puts them: the notes' (the last) ends at the right edge with Columns in it
  head.style.cssText = 'display:flex;align-items:center;gap:12px';
  // below 800px the notes go under each passage's words, so the headings are two
  const names = innerWidth < 800 ? ['statements', 'transcript'] : ['statements', 'transcript', 'notes'];
  const grips = names.map((name, i) => {
    const h = document.createElement('div');
    h.className = 'col-head'; h.dataset.col = name;
    h.style.cssText = 'flex:none;width:120px;' + (i === names.length - 1 ? 'margin-right:12px' : i === 0 ? 'margin-right:' + Math.round(innerWidth * 0.12) + 'px' : 'margin-right:auto');
    h.innerHTML = '<button type="button" class="pc-grip" aria-label="Move ' + name + '"><svg viewBox="0 0 24 24" width="12" height="12" aria-hidden="true"></svg></button><span>' + name + '</span>';
    head.insertBefore(h, $('cols-pick'));
    return h.querySelector('.pc-grip');
  });
  measureBand();
  const bare = $('work').style.getPropertyValue('--band');
  rvwTrayDraw();
  const tray = $('wt-tray');
  const cols = $('cols-pick');
  const out = { bare, band: $('work').style.getPropertyValue('--band'), shown: !tray.hidden, inside: tray.parentElement.id,
    after: tray.previousElementSibling && tray.previousElementSibling.id };
  const heads = [...head.children].map(box);
  out.hits = heads.filter((h) => meets(h, box(tray))).length;
  out.cols = at(cols) === cols || cols.contains(at(cols));
  out.grips = grips.every((g) => g.getBoundingClientRect().width > 0 && (at(g) === g || g.contains(at(g))));
  out.tall = Math.round(tray.getBoundingClientRect().height);
  out.page = document.documentElement.scrollHeight <= innerHeight + 1;
  out.stageIn = box(document.querySelector('.reading')).b <= innerHeight + 1;
  RVW.st.drafts = [];
  rvwTrayDraw();
  out.hidden = tray.hidden;
  out.back = $('work').style.getPropertyValue('--band');
  document.getElementById('out').textContent = JSON.stringify(out);
  } catch (err) { document.getElementById('out').textContent = JSON.stringify({ err: String(err && err.stack || err).slice(0, 300) }); }
};
document.addEventListener('DOMContentLoaded', run);
"""


def _tray_clear(scratch):
    """The reviewer's tray covers nothing (trayfix, 10 November 2026): in the real page's markup and stylesheets and
    the real rvwTrayDraw and measureBand, at 1280 and 720, the tray stands as a row under the statements screen's
    toolbar and Columns and each column's grip are what a point at their centres reaches."""
    exe = support.browser()
    if exe is None:
        skip("343: the reviewer's tray covers nothing in a real browser", "no Chrome, Chromium, Brave or Edge on this computer")
        return
    page = support.text("apps/idiograph/static/idiograph.html")
    work = '<section id="work"' + page.split('<section id="work"', 1)[1].split("</section>", 1)[0] + "</section>"
    tray = '<div class="wt-tray"' + page.split('<div class="wt-tray"', 1)[1].split("</div>", 1)[0] + "</div>"
    css = "\n".join(support.text(p) for p in ("family/static/tokens.css", "family/static/style.css", "family/static/frame.css",
                                              "apps/idiograph/static/distil.css", "apps/idiograph/static/themes.css",
                                              "apps/idiograph/static/review.css"))
    review = support.text("apps/idiograph/static/review.js")
    band = support.text("apps/idiograph/static/distil.js")
    tray_fn = re.search(r"function rvwTrayDraw\(\) \{.*?\n\}\n", review, re.S)
    band_fn = re.search(r"function measureBand\(\) \{.*?\n\}\n", band, re.S)
    check("343: the tray's drawing and the statements screen's band are in the page's scripts, and the tray's styles "
          "no longer fix it over the screen", bool(tray_fn and band_fn) and "position: fixed" not in
          re.search(r"\.wt-tray \{.*?\}", support.text("apps/idiograph/static/review.css"), re.S).group(0))
    if not (tray_fn and band_fn):
        return
    results = {}
    with tempfile.TemporaryDirectory(prefix="idiograph-343-") as tmp:
        for width in (1280, 720):
            doc = ("<!doctype html><html><head><meta charset=\"utf-8\"><style>" + css + "</style></head><body>" + work + tray
                   + "<pre id=\"out\">none</pre><script>" + support.i18n_js("idiograph") + TRAY_DRIVER + tray_fn.group(0)
                   + band_fn.group(0) + TRAY_AFTER + "</script></body></html>")
            file = Path(tmp) / f"tray-{width}.html"
            file.write_text(doc, encoding="utf-8")
            cmd = [str(exe), "--headless", "--disable-gpu", "--no-first-run", "--no-default-browser-check",
                   "--disable-extensions", "--disable-background-networking", "--password-store=basic",
                   "--use-mock-keychain", f"--user-data-dir={Path(tmp) / f'profile-{width}'}", f"--window-size={width},800",
                   "--virtual-time-budget=3000", "--dump-dom", file.as_uri()]
            try:
                dumped = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", timeout=120).stdout
            except (OSError, subprocess.TimeoutExpired) as err:
                dumped = str(err)
            said = dumped.split('<pre id="out">', 1)[1].split("</pre>", 1)[0] if '<pre id="out">' in dumped else ""
            try:
                results[width] = json.loads(html_mod.unescape(said))
            except ValueError:
                results[width] = {}
    for width in (1280, 720):
        got = results.get(width, {})
        check(f"343: at {width}, the tray stands as a row under the toolbar, over none of the column headings, and Columns "
              "and each grip are what a point at their centres reaches",
              got.get("shown") is True and got.get("after") == "es-dock" and got.get("hits") == 0 and got.get("cols") is True
              and got.get("grips") is True, str(got)[:500])
        check(f"343: at {width}, the columns take the tray's room off their own height, the page not growing, and give it back "
              "when the tray goes", got.get("page") is True and got.get("stageIn") is True and got.get("hidden") is True
              and got.get("back") == got.get("bare") and got.get("tall", 0) > 20
              and float(got.get("band", "0px")[:-2] or 0) - float(got.get("bare", "0px")[:-2] or 0) >= got.get("tall", 99) - 1,
              str(got)[:500])
