"""Area 249: a GETs card that grows through a take makes room below it (22 October 2026). A PET that gained a
description, or a title a line longer, came in through gets take at its new height with every card round it left
where it was, so it ran over the card below it in its GET or in the pile until Arrange. The take now moves what a
grown card meets below it straight down, just far enough to keep the margin, and on in turn, and a GET whose
frame so grew pushes what lies below it the same way.

The checks build the GETs on the demo's invented participants, one board with Rowan's cards in a GET and Mabel's
in the pile, another with every card in the pile, write a made-up description on each of Rowan's PETs and
sub-PETs, take Rowan's changes, and read the saved file: no two neighbours nearer than the margin, nothing moved
sideways or up, and a take that changes no card's height moves nothing.
"""
from __future__ import annotations

import json
import shutil
from itertools import combinations

from . import support
from .support import check

SAID = "Walks at dawn and at dusk that set the shape of every day, whatever the weather"


def test_take_makes_room(scratch):
    print("\n249. A GETs card that grows through a take makes room below it, in a GET and in the pile (22 October)")
    import cli
    import gets as gets_mod
    import themes

    pristine = support.DEMO_PRISTINE
    root = scratch / "take-room-249-root"
    shutil.rmtree(root, ignore_errors=True)
    for name in ("Juno", "Rowan", "Mabel"):
        case = root / name
        (case / "Working").mkdir(parents=True)
        shutil.copy2(pristine / f"{name} - EN & ES.xlsx", case / f"{name} - EN & ES.xlsx")
        for side in (pristine / "Working").glob(f"{name} - *"):
            shutil.copy2(side, case / "Working" / side.name)
    (root / "idiograph-project.json").write_text(json.dumps({
        "name": "Dogs, a scratch project", "agents": {"allowed": True, "at": "2026-10-22T10:00:00+01:00"}}), encoding="utf-8")
    config_file = scratch / "take-room-249-config.json"
    config_file.write_text(json.dumps({"root": str(root), "interviewer": "Adam"}), encoding="utf-8")
    books = [{"case": n, "workbook": str(root / n / f"{n} - EN & ES.xlsx")} for n in ("Juno", "Rowan", "Mabel")]
    book = root / "Rowan" / "Rowan - EN & ES.xlsx"
    n_ops = [0]

    def answer(*args):
        code, out, err = cli.run(["--root", str(root), "--config", str(config_file), *args, "--json"])
        return code, (json.loads(out) if out.strip() else {}), err

    def ops(*operations) -> str:
        n_ops[0] += 1
        path = scratch / f"take-room-249-ops-{n_ops[0]}.json"
        path.write_text(json.dumps({"operations": list(operations)}), encoding="utf-8")
        return str(path)

    data, _, _, _ = gets_mod.assemble(root, books, themes.now_iso())
    gets_mod.write(root, gets_mod._file(data, themes.now_iso()))
    gfile = gets_mod.gets_path(root)
    gets_mod.version_op(root, books, "new", {"name": "All in the pile"})
    code, shown, err = answer("gets", "apply", "b1", "--ops", ops(
        {"op": "make", "ref": "a", "title": "Days given their shape", "inside": None,
         "members": [k for k in json.loads(gfile.read_text(encoding="utf-8"))["boards"][0]["cards"] if k.startswith("Rowan/")]}),
        "--note", "One GET")
    check("249: a GET made of Rowan's cards, and a second board with every card in the pile",
          code == 0 and len(json.loads(gfile.read_text(encoding="utf-8"))["boards"]) == 2, err)

    def clashes(board: dict, file: dict) -> list:
        shown = themes.normalise(gets_mod.named(board, file))
        drawn = themes.layout_boxes(shown, gets_mod.card_height)
        boxes = themes._solid_boxes(shown, drawn)
        gone = themes.off_canvas(shown)
        parents = themes.parents_of(shown["groups"])
        return [(a, b) for a, b in combinations(sorted(boxes), 2) if a not in gone and b not in gone
                and parents.get(a) == parents.get(b) and themes.clash(boxes[a], boxes[b], themes.MARGIN - 1)]

    before = json.loads(gfile.read_text(encoding="utf-8"))
    check("249: no card nearer its neighbour than the margin before the take",
          all(not clashes(b, before) for b in before["boards"]), str([clashes(b, before) for b in before["boards"]]))

    board = json.loads(themes.themes_path(book).read_text(encoding="utf-8"))["boards"][0]
    labels = [g["id"] for g in board["groups"]]
    code, _, err = answer("board", "apply", "Rowan", "v1", "--ops", ops(
        *[{"op": "describe", "label": gid, "description": SAID} for gid in labels]), "--note", "Describe", "--tool", "Claude Code")
    code_t, _, err_t = answer("gets", "take", "Rowan", "--note", "Take the descriptions")
    after = json.loads(gfile.read_text(encoding="utf-8"))
    check("249: after a take that brings a description to each of Rowan's PETs, no two cards on either board "
          "are nearer than the margin, in the GET or in the pile",
          code == 0 and code_t == 0 and all(not clashes(b, after) for b in after["boards"]),
          err + err_t + str([clashes(b, after) for b in after["boards"]]))
    spots = lambda f: {(b["id"], k): (c["x"], c["y"]) for b in f["boards"] for k, c in b["cards"].items()}
    was, now = spots(before), spots(after)
    moved = [k for k in was if now.get(k) != was[k]]
    check("249: what made room moved straight down, never sideways or up, and some cards did move",
          moved and all(now[k][0] == was[k][0] and now[k][1] > was[k][1] for k in moved), str(moved[:6]))

    code, _, err = answer("board", "apply", "Rowan", "v1", "--ops", ops(
        {"op": "note", "label": labels[0], "note": "A note the GETs cards do not show."}), "--note", "A note", "--tool", "Claude Code")
    code_t, _, err_t = answer("gets", "take", "Rowan", "--note", "Take the note")
    again = json.loads(gfile.read_text(encoding="utf-8"))
    check("249: a take that changes no card's height moves nothing", code_t == 0 and spots(again) == now, err + err_t)

    # ── a second card of one item moved into the label already holding the first is refused, on the page and for an
    # agent, nothing written (Adam, 21 November 2026)
    gets_mod.settings_op(root, books, {"one_per_pet": False})
    now_data = json.loads(gfile.read_text(encoding="utf-8"))
    pile = next(b for b in now_data["boards"] if b["id"] == "b2")
    pets = [k for k in pile["cards"] if k.startswith("Rowan/") and "/es/" not in k and not k.endswith("/2")][:2]
    code, _o, err = answer("gets", "apply", "b2", "--ops", ops(
        {"op": "make", "ref": "a", "title": "One", "inside": None, "members": [pets[0]]},
        {"op": "make", "ref": "b", "title": "Two", "inside": None, "members": [pets[1]]}), "--note", "Two GETs")
    code, _o, err = answer("gets", "apply", "b2", "--ops", ops({"op": "also", "item": pets[0], "to": "Two"}),
                           "--note", "A second card")
    stood = json.loads(gfile.read_text(encoding="utf-8"))
    board2 = next(b for b in stood["boards"] if b["id"] == "b2")
    one = next(g for g in board2["groups"] if g["label"] == "One")["id"]
    check("249: a second card of a PET made under another label by an agent",
          code == 0 and pets[0] + "/2" in board2["cards"] and themes.parents_of(board2["groups"]).get(pets[0] + "/2") != one, err)
    move = ops({"op": "move", "items": [pets[0] + "/2"], "to": one})
    bytes_before = gfile.read_bytes()
    outs = [answer("gets", "apply", "b2", "--ops", move, "--dry-run"),
            answer("gets", "apply", "b2", "--ops", move, "--note", "Into the first's label")]
    check("249: an agent's move of the second card into the label holding the first is refused in one line, the dry "
          "run too, and nothing is written",
          all(c != 0 and "already has a card in" in d.get("error", "") for c, d, e in outs)
          and gfile.read_bytes() == bytes_before, " | ".join(str(d)[:200] for _c, d, _e in outs))
    version = json.loads(json.dumps(board2))
    for g in version["groups"]:
        g["members"] = [m for m in g["members"] if m != pets[0] + "/2"]
        if g["id"] == one:
            g["members"].append(pets[0] + "/2")
    version["v"] = themes.board_version(board2)
    try:
        gets_mod.save(root, books, version)
        page_said = ""
    except Exception as exc:
        page_said = str(exc)
    check("249: the page's save of the same move is refused in one line, nothing written",
          "already has a card in" in page_said and gfile.read_bytes() == bytes_before, page_said)

    # ── a pair already on a board stays whatever happens round it, and a card moved into its label is refused
    def bd(groups, cards=("X/g1", "X/g1/2", "X/g1/3")):
        return {"cards": {k: {"text": k} for k in cards}, "discarded": [],
                "groups": [{"id": i, "label": t, "members": m} for i, t, m in groups]}
    old = bd([("G1", "One", ["X/g1", "X/g1/2"])])
    check("249: a board that held two cards of one item in a label still saves with the label given another id, with "
          "something else added beside it, and with its label merged into another",
          gets_mod.new_twins(old, bd([("G9", "One", ["X/g1", "X/g1/2"])])) == []
          and gets_mod.new_twins(old, bd([("G1", "One", ["X/g1", "X/g1/2"]), ("G2", "Other", [])])) == []
          and gets_mod.new_twins(old, bd([("G2", "Merged", ["X/g1", "X/g1/2"])])) == [])
    check("249: a third card moved into the label of an old pair is refused like any other, and so is a pair made by "
          "merging two labels that held one card each",
          gets_mod.new_twins(old, bd([("G1", "One", ["X/g1", "X/g1/2", "X/g1/3"])])) == [("X/g1", "G1")]
          and gets_mod.new_twins(bd([("G1", "One", ["X/g1"]), ("G2", "Two", ["X/g1/2"])]), bd([("G1", "One", ["X/g1", "X/g1/2"])])) == [("X/g1", "G1")])
    check("249: the line names a label with no title plainly",
          "a label with no title" in gets_mod.twin_said(bd([("G1", "", ["X/g1"])]), ("X/g1", "G1"), key=True))
    held_names = gets_mod.NAMES.set({})
    try:
        nest_was = bd([("T", "LPET", ["S1", "S2"]), ("S1", "", ["X/g1"]), ("S2", "", ["X/g1/2"])])
        nest_now = bd([("U", "Outer", ["T"]), ("T", "LPET", ["S1", "S2"]), ("S1", "", ["X/g1"]), ("S2", "", ["X/g1/2"])])
        check("249: on LPETs an old pair whose LPET is nested under another is not refused, and one made by moving a "
              "card under the LPET is",
              gets_mod.new_twins(nest_was, nest_now) == []
              and gets_mod.new_twins(bd([("T", "LPET", ["S1"]), ("S1", "", ["X/g1"]), ("V", "Two", ["X/g1/2"])]),
                                     bd([("T", "LPET", ["S1", "V"]), ("S1", "", ["X/g1"]), ("V", "Two", ["X/g1/2"])])) == [("X/g1", "T")])
    finally:
        gets_mod.NAMES.reset(held_names)
