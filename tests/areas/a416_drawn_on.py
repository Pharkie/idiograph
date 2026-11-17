"""Area 416: what draws on a PET, a sub-theme or a statement (drawsword, 17 November 2026, Adam's requirements of that
day, points 3, 8 and 11).

An LPET is his interpretation, and the cards under it record what it draws on at each timepoint. The forward trace
reads that the other way: `board drawn-on` (MCP board_drawn_on, the PETs screen's Inspector through /api/drawn-on)
answers, for a participant's PETs at a timepoint, which LPETs of the board LGETs take draw on each PET, sub-theme and
statement, and his reason a PET is drawn on by none, which the LPETs' own operation `why` (trajectories apply) keeps
with its card in the LPETs board's Unplaced.

What is checked, on a scratch copy of the longitudinal demo's Arlo: the trace answers every PET and statement the
board's cards hold, each with the LPET whose card holds it, read independently from the board; a PET whose card an
agent moved out of its LPET is drawn on by none; the reason's dry run writes nothing; a reason on a PET an LPET draws
on is refused with nothing written; the reason kept is read back by the trace and the LPETs board, is one line in the
record of agents' changes, and its undo puts every file back byte for byte; a save of the board from the page keeps
it; and no answer carries a participant's words, statements and quotes alike.

drawswordfix, after the review, and drawswordfix2 after its recheck: a revision holds the reasons; with his tick
taken off a row, Trajectories and the LPET table give no key quote there, none standing in; once an agent puts the
PET's card back under its LPET the file keeps the reason and no read shows it (the page's data, the trace, gets show,
the canvas's PDF and picture), and the move's undo, byte for byte, shows it again; a save from the page drawing the
PET on keeps it hidden and the page's Undo, the earlier board saved again, shows it again; "" is taken on a PET drawn
on and takes it off the file; the trace the LPETs Inspector reads (`lpets`) says a set-aside sub-theme whose PET is under an LPET
is drawn on through it, and a reason there is refused; on a second LPETs board a reason is refused, naming the board
LGETs take, "" taken; and on a second PETs board at the timepoint `board drawn-on --pet` is refused, naming the board
the LPETs take that timepoint from."""
from __future__ import annotations

import hashlib
import json
import shutil
from pathlib import Path

from .support import check
from . import support

ASKED = "Say why no LPET draws on that PET"
WHY = "Folded into the prescribed-project thread, the same worry at this timepoint."


def digest(root: Path) -> dict:
    """Every file of the project by its contents, the locks, the record of agents' changes and its restore points
    set aside, and the History chunks put aside in superseded/, no part of any History (`board_history.SUPERSEDED`)."""
    import agent_changes
    out = {}
    for p in sorted(root.rglob("*")):
        rel = p.relative_to(root).as_posix()
        if (not p.is_file() or p.name.endswith(".lock") or rel == agent_changes.FILE
                or rel.startswith(agent_changes.STORE) or "_Archive/" in rel or "/superseded/" in rel):
            continue
        out[rel] = hashlib.sha256(p.read_bytes()).hexdigest()
    return out


def test_drawn_on(scratch: Path):
    print("\n416. What draws on a PET, a sub-theme or a statement, and his reason none does (drawsword, 17 November)")
    import agent_changes
    import agent_log
    import cli
    import gets as gets_mod
    import idiograph_routes as routes
    import os
    import server as server_mod
    import themes

    base = scratch / "drawn-on-416"
    shutil.rmtree(base, ignore_errors=True)
    root = base / "Allotment"
    (root / "Arlo" / "Working").mkdir(parents=True)
    lipa = support.source("demo/lipa")
    held = json.loads((lipa / server_mod.PROJECT_FILE).read_text(encoding="utf-8"))
    held["agents"] = {"allowed": True, "at": "2026-11-17T09:00:00+00:00"}
    (root / server_mod.PROJECT_FILE).write_text(json.dumps(held), encoding="utf-8")
    arlo = root / "Arlo" / "Arlo - EN & ES.xlsx"
    shutil.copy2(lipa / "pristine" / "Arlo - EN & ES.xlsx", arlo)
    for one in sorted((lipa / "pristine" / "Working").glob("Arlo - EN & ES.*")):
        shutil.copy2(one, root / "Arlo" / "Working" / one.name)
    shutil.copy2(lipa / "pristine" / "idiograph-lgets.json", root / "idiograph-lgets.json")
    config_file = base / "config.json"
    config_file.write_text(json.dumps({"projects": [{"root": str(root)}], "interviewer": "Adam", "corpus": "",
                                       "gravity_reference": "", "corpus_exclude": []}), encoding="utf-8")
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

    def raw(*args):
        code, out, err = cli.run(["--config", str(config_file), "--root", str(root), "--json", *args])
        return out

    def page(fn):
        was = (server_mod.ROOT_OVERRIDE, server_mod.CONFIG_PATH, server_mod.STATE_MEMORY)
        server_mod.ROOT_OVERRIDE, server_mod.CONFIG_PATH, server_mod.STATE_MEMORY = str(root), config_file, {"recent": []}
        try:
            return fn()
        finally:
            server_mod.ROOT_OVERRIDE, server_mod.CONFIG_PATH, server_mod.STATE_MEMORY = was

    def lpets_file() -> dict:
        def read():
            with routes.lpets_scope(arlo):
                return gets_mod.load(arlo)
        return page(read)

    def expected(data: dict, case: str) -> tuple[dict, dict]:
        """The LPETs whose cards hold each PET and statement of `case`, read from the board itself: its own card, a
        larger PET's card holding it, or a card of something inside it."""
        board = gets_mod.source_board(data)[0]
        rec = data["cases"][case]
        pets = {p["id"]: p for p in rec["pets"]}
        groups = {g["id"]: g for g in board["groups"]}
        inner = {g for g in groups for m in groups[g]["members"] if m in groups}
        thrown = set(board.get("discarded") or [])
        pet_of = {}
        for pid, p in pets.items():
            for k in p["statements"]:
                pet_of[k] = pid
        for k, line in rec["lines"].items():
            if line.get("stacked") in pet_of and k not in pet_of:
                pet_of[k] = pet_of[line["stacked"]]

        def ups(pid):
            out, at = [], pets[pid].get("parent")
            while at in pets:
                out.append(at)
                at = pets[at].get("parent")
            return out

        def downs(pid):
            return [x for x in pets if pid in ups(x)]

        want_p, want_s = {}, {}
        for gid in [g for g in groups if g not in inner]:
            todo, seen, keys = [gid], set(), []
            while todo:
                at = todo.pop()
                if at in seen:
                    continue
                seen.add(at)
                for m in groups[at]["members"]:
                    (todo if m in groups else keys).append(m)
            for key in keys:
                if key in thrown:
                    continue
                k = gets_mod.split_key(key)
                if k["case"] != case:
                    continue
                if k["kind"] == "group":
                    hit = [k["ident"]] + ups(k["ident"]) + downs(k["ident"])
                    for x in hit:
                        want_p.setdefault(x, set()).add(gid)
                    for s, p in pet_of.items():
                        if p in [k["ident"]] + downs(k["ident"]):
                            want_s.setdefault(s, set()).add(gid)
                elif k["kind"] == "es":
                    want_s.setdefault(k["ident"], set()).add(gid)
                    p = pet_of.get(k["ident"])
                    for x in ([p] + ups(p)) if p else []:
                        want_p.setdefault(x, set()).add(gid)
        return want_p, want_s

    try:
        start = digest(root)
        data = lpets_file()
        ok, said = True, []
        for n, case in ((1, "T1"), (2, "T2"), (3, "T3")):
            code, got, err = run("board", "drawn-on", "Arlo", "--timepoint", str(n), tool=None)
            want_p, want_s = expected(data, case)
            got_p = {pid: {d["id"] for d in p["lpets"]} for pid, p in (got.get("pets") or {}).items() if p["lpets"]}
            got_s = {k: {d["id"] for d in s["lpets"]} for k, s in (got.get("statements") or {}).items() if s["lpets"]}
            if code != 0 or got_p != want_p or got_s != want_s:
                ok = False
                said.append([case, code, err[:200], sorted(set(got_p) ^ set(want_p)), sorted(set(got_s) ^ set(want_s))])
        check("416: at each of Arlo's three timepoints the trace names, for every PET, sub-theme and statement, the "
              "LPETs whose cards hold it on the board LGETs take, as the board itself reads, and writes nothing",
              ok and digest(root) == start, json.dumps(said)[:600])

        code, got, err = run("board", "drawn-on", "Arlo", "--timepoint", "2", "--pet", "g3", tool=None)
        check("416: before any change, T2's PET g3 is drawn on whole by G3",
              code == 0 and [(d["id"], d["how"]) for d in got["pets"]["g3"]["lpets"]] == [("G3", "whole")],
              err[:300] + json.dumps(got)[:300])
        code, got, err = run("board", "drawn-on", "Arlo", "--timepoint", "2", "--pet", "g8", tool=None)
        check("416: its sub-theme g8 is drawn on by G3 through g3",
              code == 0 and [(d["id"], d["how"], d["via"]["id"]) for d in got["pets"]["g8"]["lpets"]] == [("G3", "through", "g3")],
              err[:300] + json.dumps(got)[:300])

        # ── a reason on a PET an LPET draws on is refused, nothing written
        ops = base / "why-416.json"
        ops.write_text(json.dumps([{"op": "why", "participant": "Arlo", "timepoint": "T2", "pet": "g3", "why": WHY}]), encoding="utf-8")
        code, _x, err = run("trajectories", "apply", "--ops", str(ops), "--note", ASKED)
        check("416: a reason on a PET an LPET draws on is refused, saying so, and nothing is written",
              code != 0 and "draws on" in err and digest(root) == start and not agent_changes.read(root), err[:300])

        # ── an agent takes the PET's card out of its LPET, then the trace says none draws on it
        move = base / "move-416.json"
        move.write_text(json.dumps([{"op": "move", "items": ["T2/g3"], "to": None}]), encoding="utf-8")
        code, _x, err = run("gets", "apply", "b1", "--lpets", "Arlo", "--ops", str(move), "--note", "Take it out")
        code2, got, err2 = run("board", "drawn-on", "Arlo", "--timepoint", "2", "--pet", "g3", tool=None)
        entry = (got.get("pets") or {}).get("g3") or {}
        check("416: with its card out of G3, no LPET draws on T2's g3, its card is on the board to hold a reason",
              code == 0 and code2 == 0 and entry.get("lpets") == [] and entry.get("card") is True and entry.get("why") == "",
              err[:200] + err2[:200] + json.dumps(entry)[:300])
        before = digest(root)
        records = len(agent_changes.read(root))

        code, dry, err = run("trajectories", "apply", "--ops", str(ops), "--dry-run")
        check("416: the reason's dry run says the change by the PET's id and writes nothing, no record line",
              code == 0 and any("g3" in c for c in dry.get("changes") or []) and digest(root) == before
              and len(agent_changes.read(root)) == records, err[:300] + json.dumps(dry.get("changes"))[:300])

        code, done, err = run("trajectories", "apply", "--ops", str(ops), "--note", ASKED)
        code2, got, err2 = run("board", "drawn-on", "Arlo", "--timepoint", "2", "--pet", "g3", tool=None)
        data = lpets_file()
        board = gets_mod.source_board(data)[0]
        check("416: the reason is kept on the PET's card on the LPETs board and read back by the trace",
              code == 0 and code2 == 0 and (got["pets"]["g3"].get("why") == WHY)
              and (board.get(themes.WHY) or {}).get("T2/g3") == WHY, err[:300] + err2[:300])
        lines = agent_changes.read(root)
        check("416: the reason is one line in the record of agents' changes",
              len(lines) == records + 1 and lines[-1].get("op") == "trajectories apply", json.dumps(lines[-1:])[:300])

        # ── no answer carries a participant's words
        rec = data["cases"]["T2"]
        spoken = [line.get("text") or "" for line in rec["lines"].values()] + [
            q.get("text") or "" for line in rec["lines"].values() for q in line.get("quotes") or [] if isinstance(q, dict)]
        texts = raw("board", "drawn-on", "Arlo", "--timepoint", "2") + json.dumps(done) + json.dumps(dry)
        check("416: neither the trace nor the reason's answers carry a statement's or a quote's words",
              spoken and not any(w and len(w) > 12 and w in texts for w in spoken), str(len(spoken)))

        # ── undo puts every file back byte for byte, the reason with them
        code_u, _x, err_u = run("agents", "undo-change", lines[-1]["id"], "--note", "Put it back")
        code2, got, err2 = run("board", "drawn-on", "Arlo", "--timepoint", "2", "--pet", "g3", tool=None)
        check("416: the reason's undo puts every file back byte for byte, and the trace reads no reason",
              code_u == 0 and digest(root) == before and code2 == 0 and got["pets"]["g3"].get("why") == "",
              err_u[:300] + str(sorted(k for k in before if digest(root).get(k) != before[k])))
        code, done, err = run("trajectories", "apply", "--ops", str(ops), "--note", ASKED)

        # ── a save of the board from the page keeps it, the page never sending it
        def save():
            with routes.lpets_scope(arlo):
                d = gets_mod.load(arlo)
                b = gets_mod.source_board(d)[0]
                version = {k: v for k, v in b.items() if k != themes.WHY}
                version["v"] = themes.board_version(b)
                gets_mod.save(arlo, routes.gets_books(arlo), version)
                return gets_mod.state(arlo, routes.gets_books(arlo), board=b["id"])
        answered = page(save)
        check("416: a save of the LPETs board from the page, which sends no reason, keeps it, and the board's answer "
              "carries it for the card in Unplaced",
              code == 0 and (answered.get("why") or {}).get("T2/g3") == WHY, err[:300] + json.dumps(answered.get("why")))

        # ── drawswordfix: a revision holds the reasons
        data = lpets_file()
        board = gets_mod.source_board(data)[0]
        check("416: a revision of the LPETs board holds his reasons (themes.STATE_KEYS), so a restore puts them back",
              (themes.board_state(board).get(themes.WHY) or {}).get("T2/g3") == WHY, json.dumps(themes.STATE_KEYS))

        # ── no stand-in key quote on LPETs (Adam's ruling of 17 November 2026): his tick taken off one row
        untick = base / "untick-416.json"
        untick.write_text(json.dumps([{"op": "quote", "participant": "Arlo", "lpet": "G1", "timepoint": "T1", "quote": ""}]), encoding="utf-8")
        code0, _x, err0 = run("trajectories", "apply", "--ops", str(untick), "--note", "Take the tick off")
        untick_line = agent_changes.read(root)[-1]
        code, shown, err = run("trajectories", "show", tool=None)
        cells = []

        def walk(x):
            if isinstance(x, dict):
                if "chosen" in x and "quote" in x and "choices" in x:
                    cells.append(x)
                for v in x.values():
                    walk(v)
            elif isinstance(x, list):
                for v in x:
                    walk(v)
        walk(shown)
        unticked = [c for c in cells if not c["chosen"]]
        check("416: Trajectories gives no key quote where he has ticked none, never the first standing in",
              code0 == 0 and code == 0 and unticked and all(c["quote"] is None for c in unticked)
              and any(c["choices"] for c in unticked), f"{len(cells)} cells, {len(unticked)} unticked " + err0[:200] + err[:200])

        def table_rows():
            with routes.lpets_scope(arlo):
                d = gets_mod.load(arlo)
                return [r for g in gets_mod.table(d, gets_mod.source_board(d)[0], ["T1", "T2", "T3"]) for r in g["rows"]]
        rows = page(table_rows)
        check("416: the LPET table, which its exports print, gives no key quote for a row he has ticked none on",
              any(not r["chosen"] for r in rows) and all(r["quote"] is None for r in rows if not r["chosen"]),
              str(sum(1 for r in rows if not r["chosen"])))
        code, _x, err = run("agents", "undo-change", untick_line["id"], "--note", "Tick it again")
        check("416: the tick's undo puts it back", code == 0, err[:300])

        # ── drawswordfix2: a reason is hidden from every read while an LPET draws on its PET, and the file keeps it
        def reads() -> dict:
            """What each read shows of the reason on T2's g3: the page's data for the board, the trace, `gets show`
            and the canvas's PDF and picture, beside what the file keeps."""
            import canvas_out

            def answered():
                with routes.lpets_scope(arlo):
                    d = gets_mod.load(arlo)
                    b = gets_mod.source_board(d)[0]
                    state = gets_mod.state(arlo, routes.gets_books(arlo), board=b["id"])
                    drawn = json.dumps(canvas_out.typst_data(state, "LPETs", gets=True, lpets=True), ensure_ascii=False)
                    return state, b, drawn
            state, b, canvas = page(answered)
            code, got, err = run("board", "drawn-on", "Arlo", "--timepoint", "2", "--pet", "g3", tool=None)
            shown = raw("gets", "show", "b1", "--lpets", "Arlo")
            entry = (got.get("pets") or {}).get("g3") or {}
            return {"page": (state.get("why") or {}).get("T2/g3"), "trace": entry.get("why") if code == 0 else err,
                    "show": WHY in shown, "canvas": WHY in canvas, "shown": bool(shown.strip()),
                    "file": (b.get(themes.WHY) or {}).get("T2/g3"), "lpets": [x["id"] for x in entry.get("lpets") or []]}
        loose = reads()
        check("416: with no LPET drawing on g3, the page's data, the trace and the canvas's PDF and picture show his "
              "reason",
              loose["page"] == WHY and loose["trace"] == WHY and loose["canvas"] and loose["file"] == WHY
              and loose["lpets"] == [] and loose["shown"], json.dumps(loose))
        before = digest(root)
        back = base / "back-416.json"
        back.write_text(json.dumps([{"op": "move", "items": ["T2/g3"], "to": "G3"}]), encoding="utf-8")
        code, _x, err = run("gets", "apply", "b1", "--lpets", "Arlo", "--ops", str(back), "--note", "Put it back in G3")
        drawn = reads()
        check("416: once an agent puts the PET's card back under G3 the file keeps his reason, and no read shows it: "
              "the page's data, the trace (G3, no why), gets show, the canvas's PDF and picture",
              code == 0 and drawn["file"] == WHY and drawn["page"] is None and drawn["trace"] is None
              and not drawn["show"] and drawn["shown"] and not drawn["canvas"] and drawn["lpets"] == ["G3"],
              err[:200] + json.dumps(drawn))
        moved_line = agent_changes.read(root)[-1]
        code_u, _x, err_u = run("agents", "undo-change", moved_line["id"], "--note", "Undo the move back")
        again = reads()
        check("416: the move's undo puts every file back byte for byte, and his reason shows again",
              code_u == 0 and digest(root) == before and again["page"] == WHY and again["trace"] == WHY,
              f"{code_u} " + err_u[:300] + str(sorted(k for k in before if digest(root).get(k) != before[k]))
              + json.dumps(again))

        # ── the page's own save draws the PET on, and the page's Undo, the earlier board saved again, shows it again
        def page_save(change):
            def go():
                with routes.lpets_scope(arlo):
                    d = gets_mod.load(arlo)
                    b = gets_mod.source_board(d)[0]
                    version = json.loads(json.dumps({k: v for k, v in b.items() if k != themes.WHY}))
                    change(version)
                    version["v"] = themes.board_version(b)
                    return gets_mod.save(arlo, routes.gets_books(arlo), version)
            return page(go)

        def earliest():
            with routes.lpets_scope(arlo):
                b = gets_mod.source_board(gets_mod.load(arlo))[0]
                return json.loads(json.dumps({k: v for k, v in b.items() if k not in (themes.WHY, "v")}))
        earlier = page(earliest)

        def into_g3(version):
            for g in version["groups"]:
                if g["id"] == "G3" and "T2/g3" not in g["members"]:
                    g["members"].append("T2/g3")
        saved = page_save(into_g3)
        drawn = reads()
        check("416: a save from the page that draws the PET on keeps his reason in the file, its answer and every read "
              "leaving it out",
              saved.get("saved") and "T2/g3" not in (saved.get("why") or {}) and drawn["file"] == WHY
              and drawn["lpets"] == ["G3"] and drawn["page"] is None and drawn["trace"] is None and not drawn["show"]
              and not drawn["canvas"], json.dumps(saved.get("why")) + json.dumps(drawn))

        def as_earlier(version):
            v = version.get("v")
            version.clear()
            version.update(json.loads(json.dumps(earlier)))
            if v is not None:
                version["v"] = v
        undone = page_save(as_earlier)
        again = reads()
        check("416: the page's Undo, the earlier board saved again as the page sends it, shows his reason again, in "
              "the save's answer and every read",
              undone.get("saved") and (undone.get("why") or {}).get("T2/g3") == WHY and again["page"] == WHY
              and again["trace"] == WHY and again["canvas"] and again["lpets"] == [] and again["file"] == WHY,
              json.dumps(undone.get("why")) + json.dumps(again))

        # ── drawn on again, "" takes the reason off the file, never refused
        code, _x, err = run("gets", "apply", "b1", "--lpets", "Arlo", "--ops", str(back), "--note", "Put it back in G3")
        clear = base / "clear-416.json"
        clear.write_text(json.dumps([{"op": "why", "participant": "Arlo", "timepoint": "T2", "pet": "g3", "why": ""}]), encoding="utf-8")
        code2, _x, err2 = run("trajectories", "apply", "--ops", str(clear), "--note", "Take the reason off")
        data = lpets_file()
        check("416: an empty reason on a PET an LPET draws on is taken, never refused, and takes it off the file",
              code == 0 and code2 == 0 and "T2/g3" not in (gets_mod.source_board(data)[0].get(themes.WHY) or {}),
              err[:200] + err2[:300])

        # ── the LPETs Inspector on a sub-theme's card set aside whose PET is under an LPET: the server's trace of the
        # board on the canvas says G3 draws on it through g3, so no reason's box is offered
        data = lpets_file()
        board = gets_mod.source_board(data)[0]
        aside = "T2/g8" in (board.get("discarded") or [])
        got = page(lambda: routes.api_drawn_on({"workbook": str(arlo), "timepoint": 2, "lpets": str(board["id"])}))
        g8 = (got.get("pets") or {}).get("g8") or {}
        check("416: T2's sub-theme g8, set aside on the LPETs board while its PET g3 is under G3, is drawn on through "
              "g3 in the trace the LPETs Inspector reads, with no why, on the board LGETs take",
              aside and [(d["id"], d["how"]) for d in g8.get("lpets") or []] == [("G3", "through")] and "why" not in g8
              and got["lpets_board"]["source"] is True, json.dumps(g8)[:300])
        g8op = base / "g8-416.json"
        g8op.write_text(json.dumps([{"op": "why", "participant": "Arlo", "timepoint": "T2", "pet": "g8", "why": WHY}]), encoding="utf-8")
        start_g8 = digest(root)
        code, _x, err = run("trajectories", "apply", "--ops", str(g8op), "--note", ASKED)
        check("416: a reason on that sub-theme is refused, saying what draws on it, nothing written",
              code != 0 and "draws on" in err and digest(root) == start_g8, err[:300])

        # ── another LPETs board: a reason is kept on the one LGETs take alone, and "" is taken anywhere
        code, made, err = run("gets", "duplicate", "b1", "--lpets", "Arlo", "--note", "A copy")
        data = lpets_file()
        source = str(gets_mod.source_board(data)[0]["id"])
        other = next(str(b["id"]) for b in gets_mod.boards_of(data) if str(b["id"]) != source)
        out = base / "out-416.json"
        out.write_text(json.dumps([{"op": "move", "items": ["T2/g3"], "to": None, }]), encoding="utf-8")
        code1, _x, err1 = run("gets", "apply", other, "--lpets", "Arlo", "--ops", str(out), "--note", "Take it out")
        elsewhere = base / "elsewhere-416.json"
        elsewhere.write_text(json.dumps([{"op": "why", "participant": "Arlo", "timepoint": "T2", "pet": "g3",
                                          "why": WHY, "board": other}]), encoding="utf-8")
        start_other = digest(root)
        code2, _x, err2 = run("trajectories", "apply", "--ops", str(elsewhere), "--note", ASKED)
        got = page(lambda: routes.api_drawn_on({"workbook": str(arlo), "timepoint": 2, "lpets": other}))
        check("416: on an LPETs board other than the one LGETs take a reason is refused, naming that board, nothing "
              "written, and the trace of that board says it is not the source",
              code == 0 and code1 == 0 and code2 != 0 and "LGETs take" in err2 and digest(root) == start_other
              and got["lpets_board"]["source"] is False and got["pets"]["g3"]["lpets"] == [],
              err[:200] + err1[:200] + err2[:300])
        elsewhere.write_text(json.dumps([{"op": "why", "participant": "Arlo", "timepoint": "T2", "pet": "g3",
                                          "why": "", "board": other}]), encoding="utf-8")
        code2, _x, err2 = run("trajectories", "apply", "--ops", str(elsewhere), "--note", ASKED)
        check("416: an empty reason there is taken, with nothing to take off", code2 == 0, err2[:300])

        # ── another PETs board at the timepoint: --pet is refused, naming the board the LPETs take
        code, made, err = run("board", "duplicate", "Arlo", "v1", "--timepoint", "2", "--note", "A copy")
        copy = str(made.get("id") or "")
        code2, _x, err2 = run("board", "drawn-on", "Arlo", copy, "--timepoint", "2", "--pet", "g3", tool=None)
        check("416: on another PETs board of the timepoint, board drawn-on --pet is refused, saying which board the "
              "LPETs take T2's PETs from",
              code == 0 and copy and code2 != 0 and "take their PETs at T2 from Board 1" in err2, err[:200] + err2[:300])
    finally:
        agent_changes.ALL_OPS = kept[0]
        if kept[1] is None:
            os.environ.pop(agent_log.PLACE, None)
        else:
            os.environ[agent_log.PLACE] = kept[1]
        agent_log.flush()
