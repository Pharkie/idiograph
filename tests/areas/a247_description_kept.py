"""Area 247: a label's description kept on every path that writes a board (22 October 2026). On a real board
all three PET descriptions vanished in twenty minutes of edits in the app and an agent's writes. The page's
save sent a hand-picked few of each label's fields, its id, title, note, members and place, so every save from
the canvas took every description off the board. The page now sends each label whole with its description,
"" for none, and the server keeps the file's for a label sent with no description at all, as a page loaded
from an older copy of the app sends.

The checks drive each path in turn on a board with descriptions on two PETs and a sub-PET, and read the file
after each: the page's own save, run in node, after a rename, a reorder and a move, and a description taken
off there; an old page's save; a page loaded before a description was written, which meets the stale-save
notice and takes nothing away; the AI revise's landing on the page; turn write rewording a statement and
widening a quote; board apply's retitle, note, move, make, order under a label and of the PETs, merge, stack
and align; a revision kept and restored; a theme copied to another board; and on the GETs board, a GET's
description through take and through the page's save, old and new. The fixtures are the demo's invented
participants and made-up descriptions on its topic, living with a dog.
"""
from __future__ import annotations

import json
import shutil
import subprocess

from . import support
from .support import check, skip

PET_DESC = "Out in the dark at both ends of the day, and happiest with her there"
SUB_DESC = "A watchfulness he noticed only once she had gone"
TWO_DESC = "The flat and the company, the same eighteen months"
GET_DESC = "Days that begin and end with the dog, for both of them"


def test_description_kept(scratch):
    print("\n247. A label's description kept on every path that writes a board: the page's save, turn write, "
          "board apply, revisions, copies and the GETs (22 October)")
    import cli
    import gets as gets_mod
    import themes

    pristine = support.DEMO_PRISTINE
    root = scratch / "desc-kept-247-root"
    shutil.rmtree(root, ignore_errors=True)
    for name in ("Juno", "Rowan", "Mabel"):
        case = root / name
        (case / "Working").mkdir(parents=True)
        shutil.copy2(pristine / f"{name} - EN & ES.xlsx", case / f"{name} - EN & ES.xlsx")
        for side in (pristine / "Working").glob(f"{name} - *"):
            shutil.copy2(side, case / "Working" / side.name)
    (root / "idiograph-project.json").write_text(json.dumps({
        "name": "Dogs, a scratch project", "agents": {"allowed": True, "at": "2026-10-21T10:00:00+01:00"}}), encoding="utf-8")
    config_file = scratch / "desc-kept-247-config.json"
    config_file.write_text(json.dumps({"root": str(root), "interviewer": "Adam"}), encoding="utf-8")
    book = root / "Rowan" / "Rowan - EN & ES.xlsx"
    themes_file = themes.themes_path(book)
    books = [{"case": n, "workbook": str(root / n / f"{n} - EN & ES.xlsx")} for n in ("Juno", "Rowan", "Mabel")]
    n_ops = [0]

    def answer(*args):
        code, out, err = cli.run(["--root", str(root), "--config", str(config_file), *args, "--json"])
        return code, (support.plain(json.loads(out)) if out.strip() else {}), err

    def ops(*operations) -> str:
        n_ops[0] += 1
        path = scratch / f"desc-kept-247-ops-{n_ops[0]}.json"
        path.write_text(json.dumps({"operations": list(operations)}), encoding="utf-8")
        return str(path)

    def apply(note, *operations):
        return answer("board", "apply", "Rowan", "v1", "--ops", ops(*operations), "--note", note, "--tool", "Claude Code")

    def board(vid="v1") -> dict:
        return next(b for b in json.loads(themes_file.read_text(encoding="utf-8"))["boards"] if b["id"] == vid)

    def descs(b: dict) -> dict:
        return {g["id"]: g["description"] for g in b.get("groups") or [] if g.get("description")}

    start = board()
    parents = themes.parents_of(start["groups"])
    sub = next(g["id"] for g in start["groups"] if g["id"] in parents)
    pet = parents[sub]
    tops = [g["id"] for g in start["groups"] if g["id"] not in parents]
    two = next(t for t in tops if t != pet)
    code, done, err = apply("Describe three", {"op": "describe", "label": pet, "description": PET_DESC},
                            {"op": "describe", "label": sub, "description": SUB_DESC},
                            {"op": "describe", "label": two, "description": TWO_DESC})
    want = {pet: PET_DESC, sub: SUB_DESC, two: TWO_DESC}
    check("247: three descriptions written on the board, two PETs and a sub-PET", code == 0 and descs(board()) == want,
          done.get("said", "") + err)

    # ── A. the page's own save, its thBody run in node over the board as the page loads it
    node = shutil.which("node")
    js = support.text("apps/idiograph/static/themes.js")

    def page_body(b: dict, edit: str, meta: dict | None = None) -> dict | None:
        """The body the page's save sends for board `b` after the page-side `edit`, with the meta the page
        holds, by default the board as the file holds it now."""
        if not node:
            return None
        meta = meta or {"id": b["id"], "name": b.get("name"), "note": b.get("note") or "", "created": b.get("created"),
                        "updated": b.get("updated"), "v": themes.board_version(b)}
        shown = themes.normalise(b)
        script = scratch / "desc-kept-247-page.js"
        script.write_text(support.i18n_js() + js + "\nconst data = " + json.dumps(shown) + ";\nconst meta = " + json.dumps(meta) + r""";
const v = { cards: {}, groups: data.groups.map((g) => Object.assign({}, g, { members: g.members.slice() })),
  discarded: data.discarded.slice(), picks: JSON.parse(JSON.stringify(data.picks || {})), stickies: null, waits: false };
for (const [k, c] of Object.entries(data.cards)) v.cards[k] = Object.assign({ key: k }, c);
const out = {};
""" + edit + "\nconsole.log(JSON.stringify(Object.assign({ body: thBody(v, meta) }, out)));\n", encoding="utf-8")
        run = subprocess.run([node, str(script)], capture_output=True, text=True, encoding="utf-8")
        if run.returncode != 0:
            print(run.stderr[:600])
            return None
        return support.plain(json.loads(run.stdout))

    if not node:
        skip("247: the page's save in node", "no node on this machine")
    else:
        moving = next(m for m in themes.normalise(board())["groups"][[g["id"] for g in board()["groups"]].index(pet)]["members"]
                      if ":" in m)
        edits = [
            ("a rename of the PET", f"thGroup(v, {json.dumps(pet)}).label = 'Living on her timetable';"),
            ("a reorder of the PETs", f"const a = thGroup(v, {json.dumps(pet)}), b = thGroup(v, {json.dumps(two)});"
                                      " [a.x, b.x] = [b.x, a.x]; [a.y, b.y] = [b.y, a.y];"),
            ("a statement moved to another PET", f"thGroup(v, {json.dumps(pet)}).members = thGroup(v, {json.dumps(pet)})"
                                                 f".members.filter((m) => m !== {json.dumps(moving)});"
                                                 f" thGroup(v, {json.dumps(two)}).members.push({json.dumps(moving)});"),
        ]
        for what, edit in edits:
            got = page_body(board(), edit)
            sent = {g["id"]: g.get("description") for g in (got or {}).get("body", {}).get("groups") or []}
            try:
                themes.save(book, got["body"], "Rowan")
                saved = None
            except Exception as exc:  # noqa: BLE001
                saved = str(exc)
            check(f"247: the page's save after {what} sends every label's description and the file keeps all three",
                  got is not None and saved is None and all(sent.get(g) == d for g, d in want.items())
                  and all("description" in g for g in got["body"]["groups"]) and descs(board()) == want,
                  f"{saved} {descs(board())}")
        got = page_body(board(), f"out.changed = thSetDesc(v, {json.dumps(sub)}, '');")
        themes.save(book, got["body"], "Rowan")
        check("247: a description taken off on the page goes from the file on its save, sent as \"\", the others kept",
              got["changed"] is True and descs(board()) == {pet: PET_DESC, two: TWO_DESC}, str(descs(board())))
        apply("Put it back", {"op": "describe", "label": sub, "description": SUB_DESC})

        # the AI revise's landing on the page: a revise that gives labels without descriptions keeps them
        revised = {"groups": [{k: x for k, x in g.items() if k not in ("description", "x", "y")} for g in board()["groups"]],
                   "picks": board()["picks"]}
        got = page_body(board(), "thReviseTake(v, " + json.dumps(revised) + ", () => ({ w: 200, h: 80 }));")
        landed = {g["id"]: g.get("description") for g in (got or {}).get("body", {}).get("groups") or []}
        check("247: an AI revise landed on the page keeps each label's description, which a revise never writes",
              got is not None and all(landed.get(g) == d for g, d in want.items()), str(landed))

        # ── B. a page loaded before a description was written meets the stale-save notice and takes nothing away
        before = board()
        old = page_body(before, f"thGroup(v, {json.dumps(pet)}).label = 'Retitled on an old page';")
        apply("A fourth", {"op": "describe", "label": tops[-1], "description": "Written after the page was loaded"})
        held = themes_file.read_bytes()
        try:
            themes.save(book, old["body"], "Rowan")
            refused = ""
        except Exception as exc:  # noqa: BLE001
            refused = str(exc)
        after = board()
        check("247: a page loaded before a description was written, then saved, is refused with the notice that the "
              "board changed since the page was loaded, and every description stays",
              bool(refused) and ("changed since" in refused or "conversation" in refused or "elsewhere" in refused)
              and descs(after) == dict(want, **{tops[-1]: "Written after the page was loaded"})
              and after["groups"] == support.plain(json.loads(held.decode("utf-8")))["boards"][[b["id"] for b in support.plain(json.loads(held))["boards"]].index("v1")]["groups"],
              refused)
        apply("Take the fourth off", {"op": "describe", "label": tops[-1], "description": ""})

    # ── C. a page from an older copy of the app, which sends no description at all, takes none away
    b = board()
    body = {"id": b["id"], "name": b["name"], "note": b.get("note") or "", "created": b["created"], "updated": b["updated"],
            "v": themes.board_version(b), "cards": b["cards"], "discarded": b["discarded"], "picks": b["picks"],
            "groups": [{k: x for k, x in g.items() if k != "description"} for g in b["groups"]]}
    body["groups"][0]["label"] = "Renamed on an old page"
    themes.save(book, body, "Rowan")
    check("247: a save from a page that sends no description on its labels keeps the file's, its rename taken",
          descs(board()) == want and board()["groups"][0]["label"] == "Renamed on an old page", str(descs(board())))

    # ── D. turn write: a statement reworded in place, then a quote widened
    read = themes.read_cards(book)
    under_pet = [m for m in next(g for g in board()["groups"] if g["id"] == pet)["members"] if ":" in m]
    sheet, row, _ = themes.split_card_key(under_pet[0])
    code, shown, err = answer("turn", "show", "Rowan", sheet, str(row))
    turn = shown["turns"][0]
    pairs = [dict(p) for p in turn["pairs"]]
    pairs[0]["statement"] = pairs[0]["statement"] + " in the dark"
    spec = scratch / "desc-kept-247-turn.json"
    spec.write_text(json.dumps({"request": "Reword the first", "version": turn["version"], "pairs": pairs}), encoding="utf-8")
    code_w, wrote, err_w = answer("turn", "write", "Rowan", sheet, str(row), "--from", str(spec), "--tool", "Claude Code")
    check("247: turn write rewording a statement on a PET keeps every description", code_w == 0 and descs(board()) == want,
          wrote.get("said", "") + err_w)
    code, shown, err = answer("turn", "show", "Rowan", sheet, str(row))
    turn = shown["turns"][0]
    pairs = [dict(p) for p in turn["pairs"]]
    text = turn["text"]
    held_q = next((p["quote"].strip('"') for p in pairs if p["quote"]), "")
    at = text.find(held_q) if held_q else -1
    wider = text[max(0, at - 30):at + len(held_q)].lstrip(" ,.") if at >= 0 else ""
    wider = wider[wider.find(" ") + 1:] if at > 30 else wider
    for p in pairs:
        if p["quote"]:
            p["quote"] = wider
            break
    spec.write_text(json.dumps({"request": "Widen the quote", "version": turn["version"], "pairs": pairs}), encoding="utf-8")
    code_w, wrote, err_w = answer("turn", "write", "Rowan", sheet, str(row), "--from", str(spec), "--tool", "Claude Code")
    check("247: turn write widening a quote keeps every description",
          code_w == 0 and wrote.get("changed", True) is not False and descs(board()) == want, wrote.get("said", "") + err_w)

    # ── E. board apply, each op that rewrites labels
    v = themes.normalise(board())
    drawn = themes.layout_boxes(v)
    inner = themes.order_of(v, pet, drawn)
    pets_order = themes.order_of(v, None, drawn)
    loose = [k for k in v["cards"] if k not in v["discarded"] and not any(k in g["members"] for g in v["groups"])]
    statement = next(m for m in next(g for g in v["groups"] if g["id"] == two)["members"] if ":" in m)
    other = next(t for t in tops if t not in (pet, two))
    cards_two = [m for m in next(g for g in v["groups"] if g["id"] == two)["members"] if ":" in m]
    cards_pet = [m for m in next(g for g in v["groups"] if g["id"] == pet)["members"] if ":" in m]
    steps = [
        ("retitle", [{"op": "retitle", "label": pet, "title": "Living on her timetable"}]),
        ("note", [{"op": "note", "label": two, "note": "The flat and the company together."}]),
        ("move", [{"op": "move", "items": [statement], "to": pet}]),
        ("make", [{"op": "make", "ref": "n", "title": "A new one", "inside": None, "members": loose[:1] or []}]),
        ("order under a label", [{"op": "order", "under": pet, "items": list(reversed(inner))}]),
        ("order of the PETs", [{"op": "order", "under": None, "items": list(reversed(pets_order))}]),
        ("merge of another PET", [{"op": "merge", "label": other, "into": two}]),
        ("stack", [{"op": "stack", "items": cards_two[1:2], "under": cards_two[0]}] if len(cards_two) > 1 else []),
        ("align", [{"op": "align", "items": cards_pet[:2], "to": "top"}] if len(cards_pet) > 1 else []),
    ]
    for what, operations in steps:
        if not operations:
            continue
        code, done, err = apply(f"Apply {what}", *operations)
        check(f"247: board apply's {what} keeps every description", code == 0 and descs(board()) == want,
              (done.get("said", "") + err)[:300] + f" {descs(board())}")

    # ── F. a revision kept and restored, and a theme copied to another board
    held = themes.history_of(board())
    revision = held[-1]["id"]
    apply("Take one off", {"op": "describe", "label": two, "description": ""})
    themes.board_op(book, "restore", {"id": "v1", "revision": revision}, "Rowan")
    check("247: a revision restored brings back the descriptions it held", descs(board()) == want, str(descs(board())))
    code, fresh, err = answer("board", "fresh", "Rowan", "--name", "Another", "--note", "Another board")
    target = fresh.get("id") or ""
    themes.board_op(book, "copy", {"id": "v1", "group": pet, "to": target}, "Rowan")
    copied = descs(board(target)) if target else {}
    check("247: a PET copied to another board brings its description and its sub-PET's",
          target and sorted(copied.values()) == sorted([PET_DESC, SUB_DESC]), f"{err} {copied}")

    # ── G. the GETs: a GET's description through take, and through the page's save, old and new
    data_g, _, _, _ = gets_mod.assemble(root, books, themes.now_iso())
    gets_mod.write(root, gets_mod._file(data_g, themes.now_iso()))
    gfile = gets_mod.gets_path(root)
    rowan = [k for k in data_g["boards"][0]["cards"] if k.startswith("Rowan/")]
    code, made_get, err = answer("gets", "apply", "b1", "--ops", ops(
        {"op": "make", "ref": "a", "title": "A day given its shape by the dog", "inside": None, "members": rowan[:1]}),
        "--note", "One GET")
    gid = (made_get.get("made") or [""])[0]
    answer("gets", "apply", "b1", "--ops", ops({"op": "describe", "label": gid, "description": GET_DESC}), "--note", "Describe")
    gdesc = lambda: next((g.get("description") for g in json.loads(gfile.read_text(encoding="utf-8"))["boards"][0]["groups"]
                          if g["id"] == gid), None)
    apply("A change to take", {"op": "retitle", "label": two, "title": "Company, and the flat closing in"})
    code_t, took, err_t = answer("gets", "take", "Rowan", "--note", "Take Rowan's change")
    check("247: a GET's description stays through gets take", gid and code_t == 0 and gdesc() == GET_DESC,
          took.get("said", "") + err_t)
    disk = json.loads(gfile.read_text(encoding="utf-8"))["boards"][0]
    old_page = dict(disk, v=themes.board_version(disk),
                    groups=[{k: x for k, x in g.items() if k != "description"} for g in disk["groups"]])
    old_page.pop("history", None)
    gets_mod.save(root, books, old_page)
    kept_old = gdesc()
    disk = json.loads(gfile.read_text(encoding="utf-8"))["boards"][0]
    new_page = dict(disk, v=themes.board_version(disk))
    new_page.pop("history", None)
    if node:
        got = page_body(disk, "TH.mode = 'gets';", {"id": disk["id"], "name": disk.get("name"), "note": "",
                                                    "created": disk.get("created"), "updated": disk.get("updated"),
                                                    "v": themes.board_version(disk)})
        new_page = dict(new_page, groups=got["body"]["groups"]) if got else new_page
    gets_mod.save(root, books, new_page)
    kept_new = gdesc()
    disk = json.loads(gfile.read_text(encoding="utf-8"))["boards"][0]
    gets_mod.save(root, books, dict(disk, v=themes.board_version(disk), groups=[
        dict(g, description="") if g["id"] == gid else g for g in disk["groups"]]))
    check("247: the GETs board's save keeps a GET's description from an old page that sends none and from a page "
          "of now, and takes it off when sent as \"\"",
          kept_old == GET_DESC and kept_new == GET_DESC and gdesc() is None, f"{kept_old} {kept_new} {gdesc()}")
    answer("gets", "apply", "b1", "--ops", ops({"op": "describe", "label": gid, "description": GET_DESC}), "--note", "Again")
    start_g = gets_mod.revise_start(json.loads(gfile.read_text(encoding="utf-8"))["boards"][0],
                                    json.loads(gfile.read_text(encoding="utf-8")), ["Juno", "Rowan", "Mabel"])
    check("247: the GETs AI revise starts from each GET whole, its description with it, so its landing keeps it",
          next(g for g in start_g["groups"] if g["id"] == gid).get("description") == GET_DESC, "")
