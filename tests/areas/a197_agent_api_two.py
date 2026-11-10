from __future__ import annotations

import json
import shutil

from . import support
from .support import check


def test_agent_api_two(scratch):
    print("\n197. Agent access, the next gaps: an order on a GETs board, a label's level changed keeping the layout, "
          "a rebuild keeping the layout, the GETs copies taken, and card words after a turn write")
    import cli
    import gets as gets_mod
    import mcp_server
    import server as server_mod
    import themes
    from workbook import WorkbookError

    pristine = support.DEMO_PRISTINE
    root = scratch / "agent-api-two-root"
    shutil.rmtree(root, ignore_errors=True)
    for name in ("Juno", "Rowan", "Mabel"):
        case = root / name
        (case / "Working").mkdir(parents=True)
        shutil.copy2(pristine / f"{name} - EN & ES.xlsx", case / f"{name} - EN & ES.xlsx")
        for side in (pristine / "Working").glob(f"{name} - *"):
            shutil.copy2(side, case / "Working" / side.name)
    (root / server_mod.PROJECT_FILE).write_text(json.dumps({
        "name": "Dogs, a scratch project", "agents": {"allowed": True, "at": "2026-10-19T10:00:00+01:00"}}), encoding="utf-8")
    config_file = scratch / "agent-api-two-config.json"
    config_file.write_text(json.dumps({"root": str(root), "interviewer": "Adam"}), encoding="utf-8")
    book = root / "Rowan" / "Rowan - EN & ES.xlsx"
    themes_file = themes.themes_path(book)
    books = [{"case": n, "workbook": str(root / n / f"{n} - EN & ES.xlsx")} for n in ("Juno", "Rowan", "Mabel")]

    def run(*args):
        return cli.run(["--root", str(root), "--config", str(config_file), *args])

    def answer(*args):
        code, out, err = run(*args, "--json")
        return code, (support.plain(json.loads(out)) if out.strip() else {}), err

    def spec(name: str, value: dict) -> str:
        path = scratch / f"agent-api-two-{name}.json"
        path.write_text(json.dumps(value), encoding="utf-8")
        return str(path)

    def ops(*operations) -> str:
        return spec("ops", {"operations": list(operations)})

    def saved() -> dict:
        return json.loads(themes_file.read_text(encoding="utf-8"))

    def board(vid="v1") -> dict:
        return next(b for b in saved()["boards"] if b["id"] == vid)

    def drawn(b: dict, height=None) -> tuple[dict, dict, dict]:
        v = themes.normalise(b)
        return v, themes.layout_boxes(v, height), themes.parents_of(v["groups"])

    def overlaps(b: dict, height=None) -> int:
        """Siblings that overlap, the labels at the top and the cards in none among them."""
        v, d, parents = drawn(b, height)
        by_id = {g["id"]: g for g in v["groups"]}
        tops = [g for g in by_id if g not in parents] + [k for k in v["cards"] if k not in parents and k not in v["discarded"]]
        n = 0
        for members in [tops] + [g["members"] for g in v["groups"]]:
            boxes = [d["frames"][m] if m in by_id else d["cards"].get(m) for m in members]
            boxes = [x for x in boxes if x]
            n += sum(1 for i, a in enumerate(boxes) for c in boxes[i + 1:] if themes.clash(a, c))
        return n

    def offsets(b: dict, keys: list[str]) -> list[tuple[int, int]]:
        """Where each card stands from the first, the arrangement a block keeps when it moves whole."""
        cards = b["cards"]
        x0, y0 = cards[keys[0]]["x"], cards[keys[0]]["y"]
        return [(cards[k]["x"] - x0, cards[k]["y"] - y0) for k in keys]

    def spots(b: dict, keys) -> dict:
        return {k: (b["cards"][k]["x"], b["cards"][k]["y"]) for k in keys}

    kept = (server_mod.CONFIG_PATH, server_mod.ROOT_OVERRIDE, server_mod.STATE_MEMORY)
    try:
        start = board()
        v0, _, parents0 = drawn(start)
        by0 = {g["id"]: g for g in v0["groups"]}
        sub = next(g for g in by0 if g in parents0)       # a sub-theme with no groups yet
        pet = parents0[sub]
        held = themes.cards_under(by0, sub)
        others = [k for g in by0 if g not in (pet, sub) and parents0.get(g) != pet for k in themes.cards_under(by0, g)]

        # ── A. groups made in a sub-theme over its own statements, where they stand
        half = len(held) // 2
        code, data, err = answer("board", "apply", "Rowan", "v1", "--ops", ops(
            {"op": "make", "ref": "a", "title": "Listening on the road", "inside": sub, "members": held[:half]},
            {"op": "make", "ref": "b", "title": "The body on watch", "inside": sub, "members": held[half:]}),
            "--note", "Two groups")
        groups_made = data.get("made") or []
        after = board()
        check("197: groups made inside a sub-theme wrap its statements where they stand, nothing overlapping",
              code == 0 and len(groups_made) == 2 and offsets(after, held[:half]) == offsets(start, held[:half])
              and overlaps(after) == 0, err)

        # ── B. the sub-theme's groups lifted to sub-themes of a new PET, on the board as it is
        before = board()
        history = len(before.get("history") or [])
        raw = themes_file.read_bytes()
        lift = ops({"op": "make", "ref": "p", "title": "Watching for dogs that are not there", "inside": None,
                    "members": groups_made},
                   {"op": "apart", "label": sub})
        code, dry, _ = answer("board", "apply", "Rowan", "v1", "--ops", lift, "--note", "Split the PET", "--dry-run")
        check("197: a change of levels has a dry run that writes nothing",
              code == 0 and dry.get("dry_run") is True and themes_file.read_bytes() == raw, dry.get("said", ""))
        code, data, err = answer("board", "apply", "Rowan", "v1", "--ops", lift, "--note", "Split the PET",
                                 "--tool", "Claude Code")
        after = board()
        v1, _, parents1 = drawn(after)
        new_pet = (data.get("made") or [None])[0]
        untouched = [k for k in others if k in after["cards"]]
        check("197: the groups become sub-themes of the new PET, the sub-theme they sat in gone, in one History step",
              code == 0 and new_pet and new_pet not in parents1
              and all(parents1.get(g) == new_pet for g in groups_made) and sub not in {g["id"] for g in v1["groups"]}
              and len(after.get("history") or []) == history + 1
              and after["history"][-1]["name"] == "Before: Split the PET", err)
        check("197: each group keeps its arrangement, the other PETs their places, and nothing overlaps",
              offsets(after, held[:half]) == offsets(before, held[:half])
              and offsets(after, held[half:]) == offsets(before, held[half:])
              and sum(1 for k in untouched if spots(after, [k]) == spots(before, [k])) >= len(untouched) // 2
              and overlaps(after) == 0, json.dumps(data.get("said"))[:300])

        # ── C. a sub-theme lifted to a PET and a PET nested in another, the layout kept inside each
        lifted = groups_made[0]
        nested = next(g for g in v1["groups"] if g["id"] not in parents1 and g["id"] not in (pet, new_pet)
                      and not any(m in {x["id"] for x in v1["groups"]} for m in g["members"]))["id"]
        target = next(g["id"] for g in v1["groups"] if g["id"] not in parents1 and g["id"] not in (pet, new_pet, nested))
        inner = themes.cards_under({g["id"]: g for g in v1["groups"]}, nested)
        before = board()
        code, data, err = answer("board", "apply", "Rowan", "v1", "--ops", ops(
            {"op": "move", "items": [lifted], "to": None}, {"op": "move", "items": [nested], "to": target}),
            "--note", "Levels")
        after = board()
        _, _, parents2 = drawn(after)
        check("197: a sub-theme moved to null is a PET and a PET moved into another its sub-theme, each kept whole",
              code == 0 and lifted not in parents2 and parents2.get(nested) == target
              and offsets(after, held[:half]) == offsets(before, held[:half])
              and offsets(after, inner) == offsets(before, inner) and overlaps(after) == 0, err or data.get("said", ""))

        # ── D. board new keeps the layout of the board it came from, in the order given
        code, view, _ = answer("board", "show", "Rowan", "v1")

        def label(t, depth=0):
            out = {"title": t["label"], "members": [s["id"] for s in t["statements"]], "picks": [p["key"] for p in t["picks"]]}
            inner_labels = [label(x, depth + 1) for x in t["themes"]]
            if inner_labels:
                out["subs" if depth == 0 else "groups"] = inner_labels
            return out
        pets = [label(t) for t in view["themes"]]
        wanted = [p["title"] for p in reversed(pets)]
        source = board()
        code, data, err = answer("board", "new", "Rowan", "--from", spec("new", {"pets": list(reversed(pets))}),
                                 "--note", "The same PETs, the other way round")
        made = board(data.get("id"))
        code2, shown, _ = answer("board", "show", "Rowan", data.get("id"))
        sv, _, sp = drawn(source)
        sby = {g["id"]: g for g in sv["groups"]}
        whole = [themes.cards_under(sby, t) for t in sby if t not in sp]
        check("197: board new keeps the source board's arrangement inside every PET it keeps, in the order given",
              code == 0 and data.get("layout") == "Board 1" and [t["label"] for t in shown["themes"]] == wanted
              and all(offsets(made, keys) == offsets(source, keys) for keys in whole if keys)
              and overlaps(made) == 0, err or json.dumps(data)[:300])
        code, fresh, err = answer("board", "new", "Rowan", "--from", spec("new", {"pets": list(reversed(pets))}),
                                  "--note", "Laid out afresh", "--layout", "fresh")
        laid = board(fresh.get("id"))
        check("197: --layout fresh lays a new board out afresh, as before",
              code == 0 and fresh.get("layout") == "fresh"
              and any(offsets(laid, keys) != offsets(source, keys) for keys in whole if len(keys) > 2), err)
        one = view["themes"][0]["statements"][0]["id"]
        run("board", "canvas", "Rowan", "v1", "--note", "Back to the first")

        # ── E. a turn write's new words on every board's card, an open page told and never saving the old ones
        code, turn, _ = answer("turn", "show", "Rowan", "Initial", "7")
        row = turn["turns"][0] if "turns" in turn else turn[0] if isinstance(turn, list) else turn
        pairs = row["pairs"]
        old_words = pairs[0]["statement"]
        pairs[0] = dict(pairs[0], statement="Out walking when nobody else is")
        page_saw = "2026-10-01T09:00:00+01:00"   # the page opened the board before the write
        code, data, err = answer("turn", "write", "Rowan", "Initial", "7", "--from", spec("turn", {"pairs": pairs}),
                                 "--note", "Reword it", "--tool", "Claude Code")
        key = themes.card_key("Initial", 7, 0)
        took = [b for b in saved()["boards"] if b["cards"].get(key, {}).get("text") == "Out walking when nobody else is"]
        code2, shown, _ = answer("board", "show", "Rowan", "v1")
        words_shown = [s["text"] for t in shown["themes"] for s in t["statements"] + [x for y in t["themes"] for x in y["statements"]]
                       if s["key"] == key]
        check("197: a turn write puts a statement's new words on every board's card that held the old ones",
              code == 0 and len(took) >= 1 and all(b["changed"]["tool"] == "Claude Code" for b in took)
              and not any(b["cards"].get(key, {}).get("text") == old_words for b in saved()["boards"])
              and words_shown == ["Out walking when nobody else is"] and data.get("boards_reworded"), err)
        merged = themes.state(book, "Rowan")
        card = next(c for c in merged["cards"] if c["key"] == key)
        stale = dict(board(), updated=page_saw)
        refused = False
        try:
            themes.save(book, stale, "Rowan")
        except WorkbookError:
            refused = True
        check("197: the screen shows the new words with no changed mark, and a page that last saw the old ones never saves over them",
              card["text"] == "Out walking when nobody else is" and not card.get("changed") and refused
              and board()["cards"][key]["text"] == "Out walking when nobody else is")

        # ── F. the GETs board: an order, and its copy of a case taken again after a retitle
        data_g, _, _, _ = gets_mod.assemble(root, books, themes.now_iso())
        gets_mod.write(root, gets_mod._file(data_g, themes.now_iso()))
        cards_g = list(data_g["boards"][0]["cards"])
        rowan = [k for k in cards_g if k.startswith("Rowan/")]
        mabel = [k for k in cards_g if k.startswith("Mabel/")]
        raw = gets_mod.gets_path(root).read_bytes()
        change = ops({"op": "make", "ref": "a", "title": "Walks at the edges of the day", "inside": None,
                      "members": [rowan[0], mabel[0], mabel[1]]},
                     {"op": "make", "ref": "b", "title": "Letting a dog go", "inside": None, "members": [rowan[1], mabel[2]]},
                     {"op": "order", "under": "a", "items": [mabel[1], rowan[0]]},
                     {"op": "order", "under": None, "items": ["b", "a"]})
        code, dry, _ = answer("gets", "apply", "b1", "--ops", change, "--note", "Two GETs", "--dry-run")
        dry_kept = gets_mod.gets_path(root).read_bytes() == raw
        code2, data, err = answer("gets", "apply", "b1", "--ops", change, "--note", "Two GETs")
        code3, tree, _ = answer("gets", "show")
        gets_board = gets_mod.load(root)["boards"][0]
        check("197: an order on a GETs board sets its GETs and the cards in a GET in the order asked, one History step",
              code == 0 and dry_kept and code2 == 0 and [t["label"] for t in tree["themes"]] == ["Letting a dog go",
                                                                                                   "Walks at the edges of the day"]
              and [c["key"] for c in tree["themes"][1]["cards"]] == [mabel[1], rowan[0], mabel[0]]
              and len(gets_board.get("history") or []) == 1 and overlaps(gets_board, gets_mod.card_height) == 0,
              err or json.dumps(dry)[:200])

        pet_id = rowan[0].split("/", 1)[1]
        run("board", "apply", "Rowan", "v1", "--ops", ops({"op": "retitle", "label": pet_id, "title": "Her timetable, dark at both ends"}),
            "--note", "Shorter")
        code, tree, _ = answer("gets", "show")
        copy = lambda: next(p for p in gets_mod.load(root)["cases"]["Rowan"]["pets"] if p["id"] == pet_id)["title"]
        state = gets_mod.state(root, books)
        status = next(c for c in state["cases"] if c["case"] == "Rowan")
        check("197: a PET retitled on its board leaves the GETs copy as it was, marked changed, and gets show says so",
              copy() != "Her timetable, dark at both ends" and status["status"] == "changed"
              and [c["case"] for c in tree.get("changed") or []] == ["Rowan"])
        raw = gets_mod.gets_path(root).read_bytes()
        code, dry, _ = answer("gets", "take", "Rowan", "--note", "Take Rowan", "--dry-run")
        dry_kept = gets_mod.gets_path(root).read_bytes() == raw
        code2, data, err = answer("gets", "take", "Rowan", "--note", "Take Rowan", "--tool", "Claude Code")
        boards_g = gets_mod.load(root)["boards"]
        code3, again, _ = answer("gets", "take", "Rowan", "--note", "Again")
        check("197: gets take takes the changes as Take the changes does, a revision first on every GETs board, once",
              code == 0 and dry_kept and dry["changes"]["retitled"] and code2 == 0
              and copy() == "Her timetable, dark at both ends"
              and all(b["history"][-1]["name"] == "Before Rowan's changes came in" for b in boards_g)
              and all(b["changed"]["tool"] == "Claude Code" for b in boards_g)
              and code3 == 0 and again.get("changed") is False, err)

        # ── G. the same through MCP
        srv = mcp_server.Server(str(root), config=str(config_file))
        srv.receive(json.dumps({"jsonrpc": "2.0", "id": 1, "method": "initialize",
                                "params": {"protocolVersion": "2025-06-18", "clientInfo": {"name": "claude-code"}}}))

        def call(name, **given):
            return srv.receive(json.dumps({"jsonrpc": "2.0", "id": 2, "method": "tools/call",
                                           "params": {"name": name, "arguments": given}}))["result"]
        res = call("gets_take", case="Rowan", request="Take Rowan", dry_run=True)
        res2 = call("board_new", case="Rowan", request="Fresh", dry_run=True, layout="fresh",
                    pets=[{"title": "A walk", "members": [one]}])
        check("197: through MCP gets_take and board_new's layout run as on the command line",
              not res["isError"] and support.plain(res["structuredContent"]).get("changed") is False
              and not res2["isError"] and support.plain(res2["structuredContent"])["layout"] == "fresh", json.dumps(res)[:300])
    finally:
        server_mod.CONFIG_PATH, server_mod.ROOT_OVERRIDE, server_mod.STATE_MEMORY = kept
