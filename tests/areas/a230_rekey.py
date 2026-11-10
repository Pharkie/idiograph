from __future__ import annotations

import json
import shutil

from . import support
from .support import check
import idiograph_cli

SHEET = "Initial"
ROW = 5


def test_rekey(scratch):
    print("\n230. A turn write that removes a statement keeps every board right (rekey, 20 October, from a write that "
          "left 22 of 72 statements out): every card follows its statement to its new line, a removed statement's card "
          "comes off, stacks and labels whole, the dry run naming both, and board apply's remove and remove_missing "
          "for a card missing from the workbook, refused for one whose statement is there")
    import cli
    import gets
    import mcp_server
    import server as server_mod
    import themes

    # the fixture: the demo's invented Mabel in a scratch project, agents allowed, a second board beside
    # hers with a stack of three topped by the statement the write removes
    pristine = support.DEMO_PRISTINE
    root = scratch / "a230-root"
    shutil.rmtree(root, ignore_errors=True)
    case = root / "Mabel"
    (case / "Working").mkdir(parents=True)
    book = case / "Mabel - EN & ES.xlsx"
    shutil.copy2(pristine / book.name, book)
    for side in (pristine / "Working").glob("Mabel - *"):
        shutil.copy2(side, case / "Working" / side.name)
    (root / server_mod.PROJECT_FILE).write_text(json.dumps({
        "name": "Gardens, a rekey project", "agents": {"allowed": True, "at": "2026-10-20T10:00:00+01:00"}}),
        encoding="utf-8")
    cfg = scratch / "a230-config.json"
    cfg.write_text(json.dumps({"root": str(root), "interviewer": "Adam", "corpus": "", "gravity_reference": "",
                               "corpus_exclude": []}), encoding="utf-8")
    themes_file = themes.themes_path(book)
    K = lambda line, row=ROW: themes.card_key(SHEET, row, line)
    data = json.loads(themes_file.read_text(encoding="utf-8"))
    first = data["boards"][0]
    second = themes.stack_onto(themes.normalise(first), [K(0), K(2, 7)], K(1))
    second = dict(support.plain(json.loads(json.dumps(first))), **{k: second[k] for k in themes.STATE_KEYS if k in second},
                  id="v2", name="Board 2", history=[])
    data["boards"].append(second)
    themes_file.write_text(json.dumps(data), encoding="utf-8")
    read = themes.read_cards(book)
    words = {c["key"]: c["text"] for c in read["cards"]}
    owner = themes.parents_of(first["groups"])[K(1)]

    def run(*args):
        return cli.run(["--root", str(root), "--config", str(cfg), *args])

    def answer(*args):
        code, out, err = run(*args, "--json")
        return code, (support.plain(json.loads(out)) if out.strip() else {}), err

    def spec(name, value) -> str:
        path = scratch / f"a230-{name}.json"
        path.write_text(json.dumps(value), encoding="utf-8")
        return str(path)

    def boards() -> dict:
        return {b["id"]: b for b in json.loads(themes_file.read_text(encoding="utf-8"))["boards"]}

    # ── A. the dry run names every card that would move and every one that would go, writing nothing
    code, shown, err = answer("turn", "show", "Mabel", SHEET, str(ROW))
    pairs = shown["turns"][0]["pairs"] if code == 0 else []
    check("230: turn show gives each statement its key", [p.get("key") for p in pairs] == [K(0), K(1), K(2)], str(pairs))
    kept = [p for p in pairs if p.get("key") != K(1)]
    write = spec("drop", {"pairs": kept, "request": "Take out the second statement"})
    before = (book.read_bytes(), themes_file.read_bytes())
    code, dry, err = answer("turn", "write", "Mabel", SHEET, str(ROW), "--from", write, "--dry-run")
    _, text, _ = run("turn", "write", "Mabel", SHEET, str(ROW), "--from", write, "--dry-run")
    moved = {(c["board"], m["from"], m["to"]) for c in dry.get("cards") or [] for m in c["moved"]}
    gone = {(c["board"], m["key"]) for c in dry.get("cards") or [] for m in c["removed"]}
    check("230: the dry run names the card that moves key and the card that goes, on every board, and writes nothing",
          code == 0 and moved == {("v1", K(2), K(1)), ("v2", K(2), K(1))} and gone == {("v1", K(1)), ("v2", K(1))}
          and f"the card {K(2)} '{words[K(2)]}' would move to {K(1)}" in text
          and f"the card {K(1)} '{words[K(1)]}' would be taken off" in text
          and (book.read_bytes(), themes_file.read_bytes()) == before, f"{err.strip()[:300]} {text[:400]}")

    # ── B. the write: every card follows its statement, the removed one's card off, stacks and labels whole
    code, done, err = answer("turn", "write", "Mabel", SHEET, str(ROW), "--from", write, "--note", "Take out the second",
                             "--tool", "Claude Code")
    after = boards()
    one, two = themes.normalise(after["v1"]), themes.normalise(after["v2"])
    check("230: the write moves the later card to its statement's new line on every board, in its own label",
          code == 0 and one["cards"][K(1)]["text"] == words[K(2)] and two["cards"][K(1)]["text"] == words[K(2)]
          and themes.parents_of(one["groups"]).get(K(1)) == owner and K(2) not in one["cards"], err.strip()[:300])
    check("230: the removed statement's card is gone from every board, no card left missing from the workbook",
          all(words[K(1)] not in [c["text"] for c in b["cards"].values()] for b in (one, two))
          and all(k in {c["key"] for c in themes.read_cards(book)["cards"]} for b in (one, two) for k in b["cards"]),
          str(sorted(one["cards"])[:6]))
    check("230: a stack whose top was removed stays whole under the next statement in it, in the top's label",
          two.get("stacks") == {K(0): [K(2, 7)]} and themes.parents_of(two["groups"]).get(K(0)) == owner,
          str(two.get("stacks")))
    check("230: each board keeps the board as it stood first in its History and is marked changed in a conversation",
          all((b.get("history") or [{}])[-1].get("name") == "Before: Take out the second statement"
              and (b.get("changed") or {}).get("tool") == "Claude Code" for b in after.values())
          and len(done.get("cards") or []) == 2, json.dumps([b.get("changed") for b in after.values()])[:300])
    code, show, _ = run("board", "show", "Mabel", "v1")
    check("230: board show lists no card as no longer in the workbook after the write",
          code == 0 and "no longer in the workbook" not in show, show[-300:])

    # ── C. keys that are not this passage's statements are refused, nothing written
    before = (book.read_bytes(), themes_file.read_bytes())
    code, _, err = run("turn", "write", "Mabel", SHEET, str(ROW), "--from",
                       spec("badkey", {"pairs": [dict(kept[0], key=K(0, 7)), dict(kept[1], key=K(0, 7))]}),
                       "--note", "Bad keys")
    check("230: a pair's key from another passage, or sent twice, is refused, nothing written",
          code == 1 and idiograph_cli.NOT_THIS_LINE in err and (book.read_bytes(), themes_file.read_bytes()) == before,
          err.strip()[:300])

    # ── D. stale cards from before, cleared through board apply
    data = json.loads(themes_file.read_text(encoding="utf-8"))
    board = data["boards"][0]
    stale = [K(7), K(8)]
    for k, said in zip(stale, ("An old line removed in Excel", "Another line long gone")):
        board["cards"][k] = {"x": 0, "y": 0, "text": said}
        next(g for g in board["groups"] if g["id"] == owner)["members"].append(k)
    themes_file.write_text(json.dumps(data), encoding="utf-8")
    code, show, _ = run("board", "show", "Mabel", "v1")
    check("230: an old board with stale cards opens as before, each marked no longer in the workbook",
          code == 0 and show.count("no longer in the workbook") == 2, show[-300:])

    def apply(name, *operations, dry=False):
        args = ["board", "apply", "Mabel", "v1", "--ops", spec(name, {"request": "Clear the stale cards",
                                                                       "operations": list(operations)})]
        return answer(*args, *(["--dry-run"] if dry else []))

    before = themes_file.read_bytes()
    code, out, _ = apply("live", {"op": "remove", "items": [K(0)]})
    err = out.get("error", "")
    check("230: remove refuses a card whose statement is in the workbook, the whole change, nothing written",
          code == 1 and "whose statement is in the workbook" in err and themes_file.read_bytes() == before,
          err.strip()[:300])
    code, out, err = apply("one", {"op": "remove", "items": [K(7)]}, dry=True)
    check("230: remove's dry run says the card it would take off and writes nothing",
          code == 0 and out.get("removed") == [K(7)] and K(7) in out.get("said", "") and themes_file.read_bytes() == before,
          err.strip()[:300])
    code, out, err = apply("one", {"op": "remove", "items": [K(7)]})
    held = themes.normalise(boards()["v1"])
    check("230: remove takes the named stale card off, its label kept, one step in History",
          code == 0 and K(7) not in held["cards"] and K(8) in held["cards"]
          and K(7) not in next(g for g in held["groups"] if g["id"] == owner)["members"]
          and boards()["v1"]["history"][-1]["name"] == "Before: Clear the stale cards", err.strip()[:300])
    code, out, err = apply("all", {"op": "remove_missing"})
    held = themes.normalise(boards()["v1"])
    check("230: remove_missing takes off every card on the board missing from the workbook",
          code == 0 and out.get("removed") == [K(8)] and K(8) not in held["cards"], err.strip()[:300])
    code, out, _ = apply("none", {"op": "remove_missing"})
    err = out.get("error", "")
    check("230: remove_missing with nothing missing is refused", code == 1 and "is missing from the workbook" in err,
          err.strip()[:300])

    # ── E. the MCP server's board_apply takes the same, and turn_write's pairs take a key
    data = json.loads(themes_file.read_text(encoding="utf-8"))
    data["boards"][1]["cards"][K(9)] = {"x": 0, "y": 0, "text": "A stale line for the MCP"}
    themes_file.write_text(json.dumps(data), encoding="utf-8")
    mcp = mcp_server.Server(str(root), config=str(cfg))
    mcp.receive(json.dumps({"jsonrpc": "2.0", "id": 1, "method": "initialize",
                            "params": {"protocolVersion": "2025-06-18", "capabilities": {},
                                       "clientInfo": {"name": "claude-ai", "version": "0.1.0"}}}))
    listed = mcp.receive(json.dumps({"jsonrpc": "2.0", "id": 2, "method": "tools/list"}))
    tools = {t["name"]: t for t in listed["result"]["tools"]}
    called = mcp.receive(json.dumps({"jsonrpc": "2.0", "id": 3, "method": "tools/call", "params": {
        "name": "board_apply", "arguments": {"case": "Mabel", "board": "v2", "request": "Clear it",
                                             "operations": [{"op": "remove_missing"}]}}}))
    check("230: the MCP server's board_apply takes remove_missing, and turn_write's pairs take a key",
          called["result"]["isError"] is False and K(9) not in boards()["v2"]["cards"]
          and "remove_missing" in tools["board_apply"]["inputSchema"]["properties"]["operations"]["description"]
          and "key" in tools["turn_write"]["inputSchema"]["properties"]["pairs"]["items"]["properties"],
          str(called)[:300])

    # ── F. the lines a write moves, and a GETs board's cards following their words when the changes are taken
    check("230: passage_lines takes keys as given, else the same words, by place, then the most alike wording",
          themes.passage_lines(["a", "b", "c"], ["a", "c"]) == {0: 0, 1: None, 2: 1}
          and themes.passage_lines(["a", "b", "c"], ["x", "y"], [2, None]) == {0: None, 1: None, 2: 0}
          and themes.passage_lines(["The walk at dawn", "Rain on the shed", "A garden she keeps"],
                                   ["The walk at dawn", "A garden she keeps now"]) == {0: 0, 1: None, 2: 1}
          and themes.passage_lines(["one", "two"], ["one", "two reworded"]) == {0: 0, 1: 1})
    old = {K(0): {"text": "First"}, K(1): {"text": "Second"}, K(2): {"text": "Third"}}
    fresh = {K(0): {"text": "First"}, K(1): {"text": "Third"}}
    cards = {f"Mabel/es/{k}": {"x": 0, "y": 0} for k in old}
    moved = gets.lines_followed("Mabel", cards, old, fresh)
    check("230: a GETs board's statement cards follow their words when a case's changes are taken",
          moved.get(f"Mabel/es/{K(2)}") == f"Mabel/es/{K(1)}" and moved.get(f"Mabel/es/{K(1)}") == f"Mabel/es/{K(3)}"
          and f"Mabel/es/{K(0)}" not in moved, json.dumps(moved))
