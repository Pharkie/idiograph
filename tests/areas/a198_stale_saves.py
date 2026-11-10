from __future__ import annotations

import json
import shutil

from . import support
from .support import check
import idiograph_routes


def test_stale_saves(scratch):
    print("\n198. No work lost between the page and an agent, 19 October: a save that carries what the page last read, "
          "refused with nothing written over a board or a plan changed since, a fresh one taken, Overwrite taken, and an "
          "agent's stale write refused the same way")
    import cli
    import gets as gets_mod
    import mcp_server
    import server as server_mod
    import sift_search as ss
    import themes
    from workbook import WorkbookError

    pristine = support.DEMO_PRISTINE
    root = scratch / "stale-saves-root"
    shutil.rmtree(root, ignore_errors=True)
    for name in ("Juno", "Rowan", "Mabel"):
        case = root / name
        (case / "Working").mkdir(parents=True)
        shutil.copy2(pristine / f"{name} - EN & ES.xlsx", case / f"{name} - EN & ES.xlsx")
        for side in (pristine / "Working").glob(f"{name} - *"):
            shutil.copy2(side, case / "Working" / side.name)
    (root / server_mod.PROJECT_FILE).write_text(json.dumps({
        "name": "Dogs, a scratch project", "agents": {"allowed": True, "at": "2026-10-19T10:00:00+01:00"}}), encoding="utf-8")
    config_file = scratch / "stale-saves-config.json"
    config_file.write_text(json.dumps({"root": str(root), "interviewer": "Adam"}), encoding="utf-8")
    book = root / "Rowan" / "Rowan - EN & ES.xlsx"
    books = [{"case": n, "workbook": str(root / n / f"{n} - EN & ES.xlsx")} for n in ("Juno", "Rowan", "Mabel")]
    gfile = gets_mod.gets_path(root)
    tfile = themes.themes_path(book)

    def run(*args):
        return cli.run(["--root", str(root), "--config", str(config_file), *args])

    def answer(*args):
        code, out, err = run(*args, "--json")
        return code, (json.loads(out) if out.strip() else {}), err

    def ops_file(name: str, value) -> str:
        path = scratch / f"stale-saves-{name}.json"
        path.write_text(json.dumps(value), encoding="utf-8")
        return str(path)

    def page_body(shown: dict) -> dict:
        """The board as the page sends it, from what an open gave it."""
        return dict(shown["version"], cards={c["key"]: {"x": c["x"], "y": c["y"], "text": c.get("text") or ""}
                                             for c in shown["cards"]},
                    groups=[dict(g, members=list(g["members"])) for g in shown["groups"]],
                    discarded=list(shown["discarded"]), picks={}, notes=list(shown.get("stickies") or []))

    kept = (server_mod.CONFIG_PATH, server_mod.ROOT_OVERRIDE, server_mod.STATE_MEMORY)
    server_mod.ROOT_OVERRIDE = str(root)
    server_mod.STATE_MEMORY = {"recent": []}
    try:
        # ── A. the GETs page: a save over a board changed since it was loaded
        data_g, _, _, _ = gets_mod.assemble(root, books, themes.now_iso())
        gets_mod.write(root, gets_mod._file(data_g, themes.now_iso()))
        any_book = books[0]["workbook"]
        first = idiograph_routes.api_gets({"workbook": any_book})
        second = idiograph_routes.api_gets({"workbook": any_book})
        keys = [c["key"] for c in first["cards"]]
        mine = page_body(first)
        mine["groups"] = [{"id": "G1", "label": "Walks at the edges of the day", "members": keys[:2], "x": 0, "y": 0}]
        took = idiograph_routes.api_gets_save({"workbook": any_book, "version": mine})
        held = gfile.read_bytes()
        theirs = page_body(second)
        theirs["groups"] = [{"id": "G1", "label": "Letting a dog go", "members": keys[2:4], "x": 0, "y": 0}]
        refused = idiograph_routes.api_gets_save({"workbook": any_book, "version": theirs})
        check("198: a GETs save from a page loaded before another window's save is refused, nothing written, the version named",
              took.get("saved") and refused.get("status") == 409 and gfile.read_bytes() == held
              and refused.get("stale", {}).get("board") == "b1" and refused["stale"].get("v") == took["version"]["v"],
              json.dumps(refused)[:200])
        fresh = dict(mine, v=took["version"]["v"], groups=mine["groups"] + [
            {"id": "G2", "label": "Letting a dog go", "members": keys[2:4], "x": 0, "y": 300}])
        again = idiograph_routes.api_gets_save({"workbook": any_book, "version": fresh})
        over = idiograph_routes.api_gets_save({"workbook": any_book, "version": dict(theirs, v=again["version"]["v"])})
        board_g = gets_mod.load(root)["boards"][0]
        check("198: a GETs save carrying the board's version is taken, and Overwrite, the version the refusal named, is taken too",
              again.get("saved") and over.get("saved") and [g["label"] for g in board_g["groups"]] == ["Letting a dog go"])

        # ── B. an agent's gets apply under an open page: the page's next save is refused, the agent's change kept
        loaded = idiograph_routes.api_gets({"workbook": any_book})
        change = ops_file("gets", {"operations": [{"op": "retitle", "label": "G1", "title": "A dog let go at the gate"}]})
        code, _, err = answer("gets", "apply", "b1", "--ops", change, "--note", "Shorter title")
        held = gfile.read_bytes()
        late = idiograph_routes.api_gets_save({"workbook": any_book, "version": page_body(loaded)})
        titles = [g["label"] for g in gets_mod.load(root)["boards"][0]["groups"]]
        check("198: after an agent's gets apply an open GETs page's save is refused with nothing written, the agent's words kept",
              code == 0 and late.get("status") == 409 and gfile.read_bytes() == held and titles == ["A dog let go at the gate"], err)

        # ── C. an agent's stale write to the GETs refused, on the command line and through MCP
        code, shown, _ = answer("gets", "show")
        seen = shown.get("version")
        moved = page_body(idiograph_routes.api_gets({"workbook": any_book}))
        moved["cards"][keys[5]]["x"] += 400
        idiograph_routes.api_gets_save({"workbook": any_book, "version": moved})
        held = gfile.read_bytes()
        stale_ops = ops_file("gets-stale", {"version": seen, "operations": [{"op": "retitle", "label": "G1", "title": "Gone"}]})
        code2, said, _ = answer("gets", "apply", "b1", "--ops", stale_ops, "--note", "Retitle")
        err2 = said.get("error") or ""
        srv = mcp_server.Server(str(root), config=str(config_file))
        srv.receive(json.dumps({"jsonrpc": "2.0", "id": 1, "method": "initialize",
                                "params": {"protocolVersion": "2025-06-18", "clientInfo": {"name": "claude-code"}}}))

        def call(name, **given):
            return srv.receive(json.dumps({"jsonrpc": "2.0", "id": 2, "method": "tools/call",
                                           "params": {"name": name, "arguments": given}}))["result"]
        res = call("gets_apply", board="b1", request="Retitle", version=seen,
                   operations=[{"op": "retitle", "label": "G1", "title": "Gone"}])
        check("198: an agent's gets apply carrying a version read before a page's save is refused, nothing written, also through MCP",
              code == 0 and bool(seen) and code2 != 0 and "has changed since it was read" in err2
              and res["isError"] and gfile.read_bytes() == held, err2)
        code, shown, _ = answer("gets", "show")
        fresh_ops = ops_file("gets-fresh", {"version": shown["version"],
                                            "operations": [{"op": "retitle", "label": "G1", "title": "Let go at the gate"}]})
        code3, _, err3 = answer("gets", "apply", "b1", "--ops", fresh_ops, "--note", "Retitle")
        check("198: the same write carrying the version it read now is taken",
              code3 == 0 and [g["label"] for g in gets_mod.load(root)["boards"][0]["groups"]] == ["Let go at the gate"], err3)

        # ── D. the PETs boards: two windows, and an agent's stale board apply
        one = themes.state(book, "Rowan")
        two = themes.state(book, "Rowan")
        mine = dict(page_body(one), groups=[dict(g, members=list(g["members"])) for g in one["groups"]])
        took = themes.save(book, mine, "Rowan")
        held = tfile.read_bytes()
        try:
            themes.save(book, dict(page_body(two), groups=[]), "Rowan")
            refused = None
        except themes.StaleBoard as exc:
            refused = exc
        reply = idiograph_routes.api_themes_save({"workbook": str(book), "version": dict(page_body(two), groups=[])})
        check("198: a PETs save from a second window loaded before the first one's save is refused, nothing written",
              took.get("saved") and refused is not None and refused.now == took["version"]["v"]
              and reply.get("status") == 409 and tfile.read_bytes() == held)
        over = themes.save(book, dict(page_body(two), groups=[], v=took["version"]["v"]), "Rowan")
        check("198: Overwrite on the PETs screen, the version the refusal named, is taken", over.get("saved"))
        code, shown, _ = answer("board", "show", "Rowan")
        themes.save(book, dict(page_body(two), v=over["version"]["v"]), "Rowan")
        held = tfile.read_bytes()
        stale_ops = ops_file("board-stale", {"version": shown.get("version"), "operations": [
            {"op": "note", "label": one["groups"][0]["id"], "note": "Said twice"}]})
        code2, said, _ = answer("board", "apply", "Rowan", "v1", "--ops", stale_ops, "--note", "A note")
        err2 = said.get("error") or ""
        check("198: an agent's board apply carrying a version read before a page's save is refused, nothing written",
              code == 0 and bool(shown.get("version")) and code2 != 0 and "has changed since it was read" in err2
              and tfile.read_bytes() == held, err2)

        # ── E. Sift's plan and its reasons: a save from a page that read the plan before another window's save
        review = scratch / "stale-saves-review"
        shutil.rmtree(review, ignore_errors=True)
        review.mkdir(parents=True)
        plan = ss.blank_plan()
        start = ss.save(review, plan)
        page_saw = start["plan_version"]
        mine = dict(plan, blocks=[{"name": "Kilns", "terms": ["anagama kiln"]}])
        after = ss.save(review, mine, seen=page_saw)
        held = ss.plan_path(review).read_bytes()
        try:
            ss.save(review, dict(plan, blocks=[{"name": "Glazes", "terms": ["ash glaze"]}]), seen=page_saw)
            plan_refused = None
        except ss.StalePlan as exc:
            plan_refused = exc
        reasons_file = review / "reasons.csv"
        reasons_before = reasons_file.read_bytes() if reasons_file.exists() else None
        try:
            ss.save_reasons(review, [{"code": "T1", "meaning": "Not about kilns"}], seen=page_saw)
            reasons_refused = False
        except ss.StalePlan:
            reasons_refused = True
        reasons_after = reasons_file.read_bytes() if reasons_file.exists() else None
        check("198: a plan save and a reasons save from a page that read the plan before another save are refused, nothing written",
              after["plan_version"] != page_saw and plan_refused is not None and plan_refused.now == after["plan_version"]
              and ss.plan_path(review).read_bytes() == held and reasons_refused and reasons_after == reasons_before)
        taken = ss.save(review, dict(plan, blocks=[{"name": "Glazes", "terms": ["ash glaze"]}]), seen=after["plan_version"])
        check("198: a plan save carrying the version it read now is taken",
              [b["name"] for b in ss.newest(ss.read_file(review))["plan"]["blocks"]] == ["Glazes"] and taken["plan_version"])
    except WorkbookError as exc:
        check("198: no step was refused on the way", False, str(exc))
    finally:
        server_mod.CONFIG_PATH, server_mod.ROOT_OVERRIDE, server_mod.STATE_MEMORY = kept
