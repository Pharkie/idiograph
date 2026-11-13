"""Area 368: Working together's suggestions (wtsuggest, 10 November 2026, the spec's build 5, Adam's yes by dialog
about 10:55 that morning: as drawn and approved in wtshots 08, 09 and 11). Two scratch installs in one process,
Adam's and Curt's, each its own settings file, device file and copy of the project, joined as one team over the
loopback transport, every message sealed by team.py and carried by team_sync's one loop, as areas 343 and 351 run.

What is checked: Curt, on Adam's Juno, suggests a statement's wording and a PET's title from the page and a GET's
title through the command line, each a draft on his computer, its dry run writing nothing, nothing sent until Send
review. What goes is the op the command line would run, unrun (`turn write` with the passage's pairs, `board apply`
and `gets apply` with a `retitle`), with `seen` and his reason, and Juno's files stay as they were until Adam
answers. Accept of the wording runs `turn write` as Approve runs a held change, the statement reworded in its
place, its edit and the project's History naming `by: "member"`, Curt, Adam who accepted it and the suggestion, its
tool "Curt's suggestion, accepted in the app", and the answer reaches Curt. The PET's title, retitled by Adam since,
shows as changed with Now as it reads, and Accept still runs, by its dry run on the PET as it stands. Declining the
GET's title through MCP waits for Adam's yes as a held change, and once approved writes nothing to the GETs file
and the answer with its reason reaches Curt, whose list keeps it declined. A suggestion through MCP on a statement
Adam then took out is Decline only. A teammate's suggestion reaches agents marked untrusted.

The fixture is invented: the demo's three dog owners, copied for each install."""
from __future__ import annotations

import json
import os
import shutil
from pathlib import Path

from . import support
from .support import DEMO_SHIPPED, check

ASKED = "Suggest a better wording to Adam."


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
        "name": "Living with a dog", "agents": {"allowed": True, "at": "2026-11-10T09:00:00+00:00"}}), encoding="utf-8")


def files_of(folder: Path) -> dict:
    return {str(p.relative_to(folder)): p.read_bytes() for p in sorted(folder.rglob("*")) if p.is_file()}


def test_team_suggestions(scratch: Path):
    print("\n368. Working together's suggestions: a statement's wording and a PET's and a GET's title suggested as "
          "drafts, sent unrun with Send review, accepted through the op's own run with History by the member, a "
          "changed one accepted by its dry run, an agent's answer refused as the app's alone and his decline writing "
          "nothing, one on "
          "a removed statement Decline only, each answer back with the reviewer (wtsuggest)")
    import agent_changes
    import cli
    import idiograph_cli as icli
    import idiograph_routes as routes
    import mcp_server
    import project_history
    import review
    import server as server_mod
    import team
    import team_sync
    import themes
    import transport
    from workbook import WorkbookError

    base = scratch / "team-368"
    shutil.rmtree(base, ignore_errors=True)
    homes = {}
    for who in ("adam", "curt"):
        root = base / who / "Dogs"
        make_project(root)
        cfg = base / who / "config.json"
        cfg.write_text(json.dumps({"projects": [{"root": str(root)}], "interviewer": "Adam", "your_name": who.title(),
                                   "corpus": "", "gravity_reference": "", "corpus_exclude": []}), encoding="utf-8")
        homes[who] = {"root": root, "config": cfg, "book": root / "Juno" / "Juno - EN & ES.xlsx"}
    A, C = homes["adam"]["root"], homes["curt"]["root"]
    kept = (server_mod.CONFIG_PATH, server_mod.ROOT_OVERRIDE, server_mod.STATE_MEMORY, team.DEVICE_PATH,
            transport.OVERRIDE, os.environ.pop(transport.ENV, None), agent_changes.ALL_OPS)
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

    def sync(who):
        at(who)
        return team_sync.sync(homes[who]["root"])

    def run(who, *args, raw=False):
        at(who)
        code, out, err = cli.run(["--config", str(homes[who]["config"]), "--root", str(homes[who]["root"]), "--json",
                                  *args])
        got = json.loads(out) if out.strip() else {}
        return code, (got if raw else support.plain(got)), err + (json.dumps(got.get("error", "")) if code != 0 else "")

    def mark() -> dict:
        return {name: len(box) for name, box in hub["hub"].boxes.items()}

    def sent_since(was: dict) -> list[bytes]:
        return [raw for name, box in hub["hub"].boxes.items() for _n, _d, raw in box[was.get(name, 0):]]

    def turns(who):
        at(who)
        rows, _ = icli.turns_of(homes[who]["book"], "Initial")
        return rows

    def labels(who):
        at(who)
        data = themes.load(homes[who]["book"]) or {}
        board = next(b for b in themes.boards_of(data) if b.get("id") == themes.chosen_of(data))
        return board, {g["id"]: g["label"] for g in board["groups"]}

    def gets_labels(root):
        data = json.loads((root / "idiograph-gets.json").read_text(encoding="utf-8"))
        board = next(b for b in data["boards"] if b["id"] == data.get("chosen")) if data.get("chosen") else data["boards"][0]
        return board, {g["id"]: g["label"] for g in board["groups"]}

    def suggestion_of(state, sid):
        return next((s for r in state["reviews"] for s in r.get("suggestions") or [] if s["id"] == sid), {})

    try:
        agent_changes.ALL_OPS = True
        # the team: Adam its lead, Curt joined from an invite, Juno and the GETs board Adam's
        wt("adam", op="on", name="Adam")
        made = wt("adam", op="invite")
        wt("curt", op="on", name="Curt")
        wt("curt", op="join", words=made["words"], name="Curt")
        wt("adam", op="admit", invite=made["invite"], match=True)
        wt("curt", op="joined", invite=made["invite"])
        for who in ("curt", "adam", "curt"):
            sync(who)

        # the targets, read from Curt's copy: a passage with two statements or more, a PET of the Current board and
        # a GET of the Current GETs board
        rows = turns("curt")
        turn = next(t for t in rows if len(t["statements"]) >= 2 and t["name"] != "Adam")
        row, first, last = turn["row"], turn["statements"][0], turn["statements"][-1]
        key0 = themes.card_key("Initial", row, 0)
        keyl = themes.card_key("Initial", row, len(turn["statements"]) - 1)
        pet_board, pets = labels("curt")
        pet_id, pet_title = next(iter(pets.items()))
        gets_board, gets = gets_labels(C)
        get_id, get_title = next(iter(gets.items()))

        # 1. Curt's three suggestions are drafts: dry runs writing nothing, nothing sent
        juno_a, gets_a = files_of(A / "Juno"), (A / "idiograph-gets.json").read_bytes()
        n_sent = mark()
        n_hist_c = len(project_history.load(C))
        dry = page("curt", {"op": "suggest", "case": "Juno", "dry_run": True, "text": "Home, never a thought first",
                            "on": {"kind": "statement", "key": key0, "words": first}})
        after_dry = page("curt", {"op": "state", "case": "Juno"})
        w = page("curt", {"op": "suggest", "case": "Juno", "text": "Home with the dog in it, never a thought first",
                          "reason": "It reads as her summing up.",
                          "on": {"kind": "statement", "key": key0, "words": first, "time": turn["time"]}})
        p = page("curt", {"op": "suggest", "case": "Juno", "text": "What never got said, and why",
                          "on": {"kind": "pet", "key": pet_id, "words": pet_title, "board": pet_board["id"]}})
        code, g, err = run("curt", "team", "suggest", "--on", "get", "--key", get_id, "--words", get_title,
                           "--text", "A reason nobody argues with", "--reason", "Shorter", "--note", ASKED,
                           "--tool", "Claude Code")
        refused = []
        for body in ({"case": "Juno", "text": first, "on": {"kind": "statement", "key": key0, "words": first}},
                     {"case": "Juno", "text": "", "on": {"kind": "statement", "key": key0}},
                     {"case": "Juno", "text": "x", "on": {"kind": "statement", "key": "Initial:9999:0"}}):
            try:
                page("curt", dict(body, op="suggest"))
            except WorkbookError as exc:
                refused.append(str(exc))
        st = page("curt", {"op": "state", "case": "Juno"})
        gets_st = page("curt", {"op": "state", "case": ""})
        check("368: Curt's suggestions are drafts on his computer: a dry run keeps nothing, the wording and the PET's "
              "title from the page and the GET's through the command line kept, nothing sent, a suggestion of the "
              "same words, of no words and on a passage not there refused, each kept with its History line",
              dry.get("dry_run") is True and not after_dry["suggested"] and w.get("id") and p.get("id") and code == 0
              and len(st["suggested"]) == 2 and len(gets_st["suggested"]) == 1 and not sent_since(n_sent)
              and len(refused) == 3 and "reads now" in refused[0]
              and len(project_history.load(C)) == n_hist_c + 3
              and project_history.load(C)[-1]["op"] == "team suggest",
              err + json.dumps([dry, st["suggested"], refused])[:800])
        check("368: each draft is the op the command line would run: turn write with every pair of the passage by its "
              "key and the one statement in its new words, board apply and gets apply with a retitle, and seen",
              w["op"]["command"] == "turn" and w["op"]["act"] == "write" and w["op"]["row"] == str(row)
              and [x["statement"] for x in w["op"]["from"]["pairs"]]
              == ["Home with the dog in it, never a thought first"] + turn["statements"][1:]
              and [x["key"] for x in w["op"]["from"]["pairs"]][0] == key0 and w["seen"] == first
              and p["op"]["command"] == "board" and p["op"]["ops"]["operations"]
              == [{"op": "retitle", "label": pet_id, "title": "What never got said, and why"}]
              and g["op"]["command"] == "gets" and g["op"]["ops"]["operations"][0]["label"] == get_id,
              json.dumps([w.get("op"), p.get("op"), g.get("op")])[:900])

        # 2. Send review: the suggestions go unrun, sealed, and wait on Adam's install with nothing written
        page("curt", {"op": "send", "case": "Juno", "line": "Two for Juno."})
        code_s, _x, err_s = run("curt", "team", "review-send", "--note", ASKED, "--tool", "Claude Code")
        went = sent_since(n_sent)
        sync("adam")
        adam = page("adam", {"op": "state", "case": "Juno"})
        rv = next((r for r in adam["reviews"] if r["suggestions"]), {})
        sw = suggestion_of(adam, w["id"])
        sp = suggestion_of(adam, p["id"])
        adam_gets = page("adam", {"op": "state", "case": ""})
        sg = suggestion_of(adam_gets, g["id"])
        check("368: Send review takes the suggestions sealed (no words in the bytes), and Adam's install has them "
              "waiting on the review with Now and Curt's words, Juno's files and the GETs file as they were",
              code_s == 0 and len(went) == 5 and not any(b"never a thought" in b for b in went)
              and rv.get("waiting") == 2 and sw.get("now") == first and sw.get("suggested")
              == "Home with the dog in it, never a thought first" and sw.get("stale") is False
              and sw.get("reason") == "It reads as her summing up." and sw.get("status") == "waiting"
              and sp.get("now") == pet_title and sg.get("by") == "Curt (Claude Code)"
              and files_of(A / "Juno") == juno_a and (A / "idiograph-gets.json").read_bytes() == gets_a,
              err_s + json.dumps(adam["reviews"])[:900])

        # 3. a teammate's suggestion reaches an agent marked untrusted
        code, raw, err = run("adam", "team", "review", "Juno", raw=True)
        said = [s for r in raw.get("reviews", []) for s in r.get("suggestions") or []]
        check("368: team review's answer marks each suggestion's words, Now and the reason as untrusted text",
              code == 0 and said and all(isinstance(s[k], dict) and set(s[k]) == {cli.UNTRUSTED}
                                         for s in said for k in ("suggested", "seen", "now")),
              err + json.dumps(said)[:400])

        # 4. Accept the wording: turn write runs, History by the member, the answer back to Curt
        n_hist = len(project_history.load(A))
        yes_dry = page("adam", {"op": "answer", "suggestion": w["id"], "accept": True, "dry_run": True})
        unchanged = files_of(A / "Juno") == juno_a
        yes = page("adam", {"op": "answer", "suggestion": w["id"], "accept": True})
        now = next(t for t in turns("adam") if t["row"] == row)
        at("adam")
        edits = json.loads((A / "Juno" / "Working" / "Juno - EN & ES.progress.json").read_text(encoding="utf-8"))["edits"]
        rec = project_history.load(A)[-1]
        sync("curt")
        curt = page("curt", {"op": "state", "case": "Juno"})
        mine = {s["id"]: s for s in curt["suggestions"]}
        check("368: Accept of the wording runs turn write after its dry run (which wrote nothing): the statement "
              "reworded in its place, the others as they were, its edit and the project's History by the member, "
              "Curt, accepted by Adam, the suggestion's id and the tool, and the answer reaching Curt",
              yes_dry.get("dry_run") is True and unchanged and yes.get("accept") is True
              and now["statements"] == ["Home with the dog in it, never a thought first"] + turn["statements"][1:]
              and edits[-1].get("by") == "member" and edits[-1].get("member") == "Curt"
              and edits[-1].get("accepted_by") == "Adam" and edits[-1].get("suggestion") == w["id"]
              and edits[-1].get("tool") == "Curt's suggestion, accepted in the app"
              and len(project_history.load(A)) == n_hist + 1 and rec["op"] == "team suggestion-answer"
              and rec["by"] == "member" and rec["member"] == "Curt" and rec["accepted_by"] == "Adam"
              and rec["suggestion"] == w["id"] and rec["tool"] == "Curt's suggestion, accepted in the app"
              and mine[w["id"]]["status"] == "accepted",
              json.dumps([yes, edits[-1:], rec, curt["suggestions"]])[:900])
        again = None
        try:
            page("adam", {"op": "answer", "suggestion": w["id"], "accept": True})
        except WorkbookError as exc:
            again = str(exc)
        check("368: a suggestion answered once is refused a second answer", again and "answered" in again, str(again))

        # 5. the PET retitled by Adam since: marked changed, Now as it reads, and Accept still runs by its dry run
        spec = base / "retitle.json"
        spec.write_text(json.dumps({"operations": [{"op": "retitle", "label": pet_id, "title": "Five years of it, never said"}]}),
                        encoding="utf-8")
        code, _r, err = run("adam", "board", "apply", "Juno", pet_board["id"], "--ops", str(spec), "--note",
                            "Tighten the title", "--tool", "Claude Code")
        sp = suggestion_of(page("adam", {"op": "state", "case": "Juno"}), p["id"])
        yes = page("adam", {"op": "answer", "suggestion": p["id"], "accept": True})
        board, titles = labels("adam")
        check("368: Adam's own retitle since marks the PET's suggestion changed, Now as it reads and seen as Curt "
              "saw it, and Accept runs on the PET as it stands, its board's change marked by the member",
              code == 0 and sp.get("stale") is True and sp.get("now") == "Five years of it, never said"
              and sp.get("seen") == pet_title and yes.get("accept") is True
              and titles[pet_id] == "What never got said, and why"
              and (board.get("changed") or {}).get("by") == "member"
              and (board.get("changed") or {}).get("member") == "Curt",
              err + json.dumps([sp, yes, board.get("changed")])[:700])

        # 6. the GET's title: Adam's agent's decline refused as the app's alone, since the answer goes to Curt
        # (noholds, 13 November 2026), nothing answered, then his own decline in the app writing nothing to the GETs
        # file and the answer back
        gets_before = (A / "idiograph-gets.json").read_bytes()
        at("adam")
        mcp = mcp_server.Server(root=str(A), config=str(homes["adam"]["config"]))
        agent_changes.ALL_OPS = None
        try:
            held = mcp.call(mcp.by_name["team_suggestion_answer"],
                            {"suggestion": g["id"], "decline": True, "reason": "The longer one is hers",
                             "request": "Decline Curt's GET title."})
        finally:
            agent_changes.ALL_OPS = True
        waits = suggestion_of(page("adam", {"op": "state", "case": ""}), g["id"]).get("status")
        page("adam", {"op": "answer", "suggestion": g["id"], "accept": False, "reason": "The longer one is hers"})
        sync("curt")
        curt_gets = page("curt", {"op": "state", "case": ""})
        mine = {s["id"]: s for s in curt_gets["suggestions"]}
        check("368: an agent's decline of a teammate's suggestion is refused as the app's alone, nothing answered, and "
              "his decline in the app writes nothing to the GETs file and the answer with its reason reaches Curt, "
              "whose list keeps it declined",
              held.get("isError") and "Only the app does this" in json.dumps(held) and waits == "waiting"
              and (A / "idiograph-gets.json").read_bytes() == gets_before
              and mine[g["id"]]["status"] == "declined" and mine[g["id"]]["answer_reason"] == "The longer one is hers",
              json.dumps([held, curt_gets["suggestions"]])[:800])

        # 7. a suggestion through MCP on a statement Adam then took out is Decline only
        at("curt")
        cm = mcp_server.Server(root=str(C), config=str(homes["curt"]["config"]))
        res = cm.call(cm.by_name["team_suggest"], {"case": "Juno", "on": "statement", "at": keyl, "text": "Kept for later",
                                                   "request": "Suggest a wording."})
        sid = support.plain(res.get("structuredContent") or {}).get("id")
        run("curt", "team", "review-send", "Juno", "--note", ASKED, "--tool", "Claude Code")
        sync("adam")
        cut = base / "cut.json"
        pairs = [{"statement": s, "key": themes.card_key("Initial", row, i)}
                 for i, s in enumerate(next(t for t in turns("adam") if t["row"] == row)["statements"][:-1])]
        cut.write_text(json.dumps({"pairs": pairs}), encoding="utf-8")
        code, _c, err = run("adam", "turn", "write", "Juno", "Initial", str(row), "--from", str(cut), "--note",
                            "Take the last one out", "--tool", "Claude Code")
        sx = suggestion_of(page("adam", {"op": "state", "case": "Juno"}), sid)
        juno_now = files_of(A / "Juno")
        no_accept = None
        try:
            page("adam", {"op": "answer", "suggestion": sid, "accept": True})
        except WorkbookError as exc:
            no_accept = str(exc)
        no = page("adam", {"op": "answer", "suggestion": sid, "accept": False})
        check("368: MCP's team_suggest sends a suggestion, and once its statement is taken out it is gone: Accept "
              "refused, Juno's files as they were, and Decline answered",
              not res.get("isError") and sid and code == 0 and sx.get("gone") is True and no_accept
              and "gone since Curt" in no_accept and files_of(A / "Juno") == juno_now and no.get("accept") is False,
              err + json.dumps([res, sx, no_accept, no])[:700])
    except WorkbookError as exc:
        check("368: the page's calls run", False, str(exc))
    finally:
        (server_mod.CONFIG_PATH, server_mod.ROOT_OVERRIDE, server_mod.STATE_MEMORY, team.DEVICE_PATH,
         transport.OVERRIDE, env, agent_changes.ALL_OPS) = kept
        if env is not None:
            os.environ[transport.ENV] = env
