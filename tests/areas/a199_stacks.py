from __future__ import annotations

import csv
import json
import re
import shutil
import subprocess
import zipfile

from . import support
from .support import check, skip
import idiograph_routes


def test_stacks(scratch):
    print("\n199. Stacks on the PETs board: statements stacked under a better one, which stands for them in the "
          "table and the exports, saved and read back, the tick, the API's stack, unstack and top, and taking out "
          "(Adam, 19 October)")
    import cli
    import export as export_mod
    import mcp_server
    import server as server_mod
    import themes
    import themes_print
    import themes_word

    # the fixture: the demo's Rowan in a scratch project of its own, agents allowed, his board as it ships
    pristine = support.DEMO_PRISTINE
    root = scratch / "stacks-root"
    shutil.rmtree(root, ignore_errors=True)
    case = root / "Rowan"
    (case / "Working").mkdir(parents=True)
    book = case / "Rowan - EN & ES.xlsx"
    shutil.copy2(pristine / book.name, book)
    for side in (pristine / "Working").glob("Rowan - *"):
        shutil.copy2(side, case / "Working" / side.name)
    (root / server_mod.PROJECT_FILE).write_text(json.dumps({
        "name": "Dogs, a stacks project", "agents": {"allowed": True, "at": "2026-10-19T10:00:00+01:00"}}), encoding="utf-8")
    cfg = scratch / "stacks-config.json"
    cfg.write_text(json.dumps({"root": str(root), "interviewer": "Adam"}), encoding="utf-8")
    themes_file = themes.themes_path(book)
    read = themes.read_cards(book)
    sids = themes.short_ids(read["cards"])
    key_of = {s: k for k, s in sids.items()}

    def run(*args):
        return cli.run(["--root", str(root), "--config", str(cfg), *args])

    def answer(*args):
        code, out, err = run(*args, "--json")
        return code, (support.plain(json.loads(out)) if out.strip() else {}), err

    def ops(*operations, request="Stack the ones that say it again") -> str:
        path = scratch / "stacks-ops.json"
        path.write_text(json.dumps({"request": request, "operations": list(operations)}), encoding="utf-8")
        return str(path)

    def board(vid="v1") -> dict:
        return next(b for b in json.loads(themes_file.read_text(encoding="utf-8"))["boards"] if b["id"] == vid)

    start = themes.normalise(board())
    parents = themes.parents_of(start["groups"])
    by_id = {g["id"]: g for g in start["groups"]}
    pet = next(g for g in by_id if g not in parents and len([m for m in by_id[g]["members"] if m in start["cards"]]) >= 3)
    own = [m for m in by_id[pet]["members"] if m in start["cards"]]
    top, under = own[0], own[1:3]
    loose = next(k for k in start["cards"] if k not in parents and k not in start["discarded"])
    T, U1, U2, L = (sids[k] for k in (top, under[0], under[1], loose))

    kept = (server_mod.CONFIG_PATH, server_mod.ROOT_OVERRIDE, server_mod.STATE_MEMORY)
    try:
        server_mod.CONFIG_PATH, server_mod.ROOT_OVERRIDE = cfg, str(root)
        server_mod.STATE_MEMORY = {"recent": []}

        # ── A. the op and its dry run, through the command line
        before = themes_file.read_bytes()
        code, dry, _ = answer("board", "apply", "Rowan", "v1", "--ops", ops(
            {"op": "stack", "items": [U1, U2, L], "under": T}), "--dry-run")
        check("199: a stack op's dry run says what it would do and writes nothing",
              code == 0 and dry.get("dry_run") is True and themes_file.read_bytes() == before
              and f"under {T}" in dry.get("said", ""), str(dry)[:300])
        code, done, _ = answer("board", "apply", "Rowan", "v1", "--ops", ops(
            {"op": "stack", "items": [U1, U2, L], "under": T}), "--note", "Stack the ones that say it again",
            "--tool", "Claude Code")
        after = board()
        check("199: the stack op puts the statements under the top, out of its PET and out of Not placed, the top in "
              "its place, in one revision of its History",
              code == 0 and after.get("stacks") == {top: under + [loose]}
              and top in next(g for g in after["groups"] if g["id"] == pet)["members"]
              and not any(k in g["members"] for g in after["groups"] for k in under + [loose])
              and len(after.get("history") or []) == len(board().get("history") or []) == 1
              and (after["history"][0]["state"].get("stacks") or {}) == (start.get("stacks") or {}), str(after.get("stacks")))
        code, said, err = answer("board", "apply", "Rowan", "v1", "--ops", ops(
            {"op": "stack", "items": [sids[own[-1]]], "under": U1}), "--note", "x", "--tool", "Claude Code")
        said = str(said.get("error") or "") + err
        check("199: a stack under a statement stacked under another is refused, nothing written",
              code != 0 and f"stacked under {T}" in said and board() == after, said[:300])

        # ── B. saved and read back: the board's file, the page's open, a save from a page before the stacks
        state = themes.state(book, "Rowan")
        check("199: the board as the page opens it carries its stacks, and a stacked statement in no label and not in "
              "the bin",
              state["stacks"] == {top: under + [loose]} and not any(k in g["members"] for g in state["groups"] for k in under)
              and loose not in state["discarded"], str(state.get("stacks")))
        page = dict(themes.normalise(board()))
        page.pop("stacks")
        themes.save(book, page, "Rowan")
        check("199: a save from a page before the stacks keeps the file's",
              board().get("stacks") == {top: under + [loose]}, str(board().get("stacks")))
        page = dict(themes.normalise(board()), stacks={})
        themes.save(book, page, "Rowan")
        check("199: a save that sends none takes them off, every stacked statement back in Not placed",
              not board().get("stacks") and not any(k in g["members"] for g in board()["groups"] for k in under), "")
        themes.save(book, dict(themes.normalise(board()), stacks={top: under + [loose]}), "Rowan")

        # ── C. the top stands for the stack in the table, Word and the draft, and the tick puts them under it
        fresh = server_mod.merge_config({})
        texts = {k: c["text"] for k, c in themes.normalise(board())["cards"].items()}

        def printed(query=None) -> str:
            return idiograph_routes.themes_print_page(dict({"workbook": str(book), "auto": "0"}, **(query or {})))[1]

        def worded(body=None) -> str:
            made = idiograph_routes.api_themes_export(dict({"workbook": str(book), "op": "word"}, **(body or {})))
            name = str(made["word"]).replace("\\", "/").rsplit("/", 1)[-1]
            with zipfile.ZipFile(case / name) as z:
                return " ".join(re.findall(r"<w:t[^>]*>([^<]*)</w:t>", z.read("word/document.xml").decode("utf-8")))

        head = themes.counted(themes.STACKED_HEAD, 3)
        plain_p, plain_w = printed(), worded()
        draft_off = themes.draft_markdown(book, "Rowan")[0]
        check("199: Include stacked statements is off on a new install, and the print view, the Word document and the "
              "PET draft hold the top alone, its stacked statements nowhere, Not placed's among them",
              fresh["export_stacked"] is False and texts[top] in plain_p and head not in plain_p
              and not any(texts[k] in plain_p for k in under) and head not in plain_w
              and not any(texts[k] in plain_w for k in under) and head not in draft_off
              and not any(texts[k] in draft_off for k in under + [loose]), "")
        on_p, on_w = printed({"stacked": "1"}), worded({"stacked": True})
        draft_on = themes.draft_markdown(book, "Rowan", stacked=True)[0]
        check("199: with the tick the stacked statements stand under their top, after it, in all three",
              head in on_p and on_p.index(texts[top]) < on_p.index(head) < on_p.index(texts[under[0]])
              and head in on_w and on_w.index(texts[top]) < on_w.index(texts[under[0]])
              and head in draft_on and draft_on.index(texts[top]) < draft_on.index(texts[under[0]]), "")
        server_mod.api_settings({"export_stacked": True})
        check("199: the tick saved in the settings is kept, and the next export with nothing said follows it",
              json.loads(cfg.read_text(encoding="utf-8")).get("export_stacked") is True and head in printed()
              and 'id="include-stacked" checked' in printed(), "")
        server_mod.api_settings({"export_stacked": False})
        out = scratch / "stacks.csv"
        export_mod.export(book, out, themes=(themes_file, None), guard=False)
        rows = list(csv.reader(out.open(encoding="utf-8-sig")))[1:]
        words = [r[2] for r in rows]
        check("199: the statements CSV lists every statement, each stacked one straight after its top with its top's "
              "words in the Proposed PET column",
              len(rows) == len(read["cards"]) and words.index(texts[under[0]]) == words.index(texts[top]) + 1
              and rows[words.index(texts[loose])][3] == f"{themes.STACKED_UNDER}: {texts[top]}", "")
        t = next(x for x in mcp_server.TOOLS if x["name"] == "board_export")
        check("199: board export over MCP takes stacked, off when left out",
              mcp_server.arguments(t, {"case": "Rowan"}, {"project": None}, "test").stacked is False
              and mcp_server.arguments(t, {"case": "Rowan", "stacked": True}, {"project": None}, "test").stacked is True, "")
        # the PDF takes the same option, each PDF typeset by Typst and its words kept (typst5)
        import print_pdf
        pages: list[str] = []
        real_typeset, print_pdf.typeset_pdf = support.typeset_words(pages)
        try:
            c1, _, e1 = answer("board", "export", "Rowan", "--pdf")
            c2, _, e2 = answer("board", "export", "Rowan", "--pdf", "--stacked")
        finally:
            print_pdf.typeset_pdf = real_typeset
        sq = support.squashed
        check("199: board export --pdf leaves the stacked statements out, and with --stacked puts them under their top",
              (c1, c2) == (0, 0) and len(pages) == 2 and sq(head) not in pages[0] and sq(head) in pages[1]
              and pages[1].index(sq(texts[top])) < pages[1].index(sq(head)) < pages[1].index(sq(texts[under[0]])), e1 + e2)

        # ── D. taking out and the top, through the API, and board show
        code, shown, _ = answer("board", "show", "Rowan", "v1")
        tree_top = next(s for t_ in shown["themes"] if t_["id"] == pet for s in t_["statements"] if s["key"] == top)
        check("199: board show gives the top its stacked statements with their ids, and Not placed leaves them out",
              [s["id"] for s in tree_top.get("stacked") or []] == [U1, U2, L]
              and loose not in [s["key"] for s in shown["unplaced"]], str(tree_top)[:300])
        code, _, _ = answer("board", "apply", "Rowan", "v1", "--ops", ops(
            {"op": "unstack", "items": [L]}, {"op": "top", "item": U1}), "--note", "Take one out", "--tool", "Claude Code")
        b = themes.normalise(board())
        check("199: unstack takes a statement out beside its top, into the top's PET, and top puts another on top in "
              "the old top's place, the old top first under it",
              code == 0 and b.get("stacks") == {under[0]: [top, under[1]]}
              and loose in next(g for g in b["groups"] if g["id"] == pet)["members"]
              and under[0] in next(g for g in b["groups"] if g["id"] == pet)["members"]
              and top not in next(g for g in b["groups"] if g["id"] == pet)["members"]
              and (b["cards"][under[0]]["x"], b["cards"][under[0]]["y"]) == (start["cards"][top]["x"], start["cards"][top]["y"]),
              str(b.get("stacks")))
        drawn = themes.layout_boxes(b)
        lb, tb = drawn["cards"][loose], (start["cards"][top]["x"], start["cards"][top]["y"])
        others = [box for k, box in drawn["cards"].items() if k != loose]
        check("199: a statement taken out lands clear of every other card",
              not any(themes.clash(lb, o) for o in others), str(lb))
        code, said, err = answer("board", "apply", "Rowan", "v1", "--ops", ops({"op": "unstack", "items": [L]}),
                                 "--note", "x", "--tool", "Claude Code")
        said = str(said.get("error") or "") + err
        check("199: taking out a statement in no stack is refused", code != 0 and "in no stack" in said, said[:200])

        # ── D2. a card taken out lands straight after the card it was stacked under (unstackorder, 13 November)
        spare = list(start["cards"])[:11]
        grid = {k: {"x": 40 + 330 * (i % 3), "y": 120 + 200 * (i // 3)} for i, k in enumerate(spare)}
        row = spare[:5]
        base = themes.normalise(dict(start, discarded=[], stacks={spare[1]: spare[5:8]}, notes=[], stickies=[],
                                     groups=[dict(by_id[pet], members=row, x=0, y=0)],
                                     cards={k: dict(c, **grid[k]) for k, c in start["cards"].items() if k in spare}))
        topk, first, second = spare[1], spare[5], spare[6]

        def reads(b):
            return themes.order_of(b, pet)

        def clear(b):
            drawn = themes.layout_boxes(b)
            boxes = [drawn["cards"][k] for k in b["cards"] if k in drawn["cards"] and k not in themes.off_canvas(b)]
            return not any(themes.clash(a, c) for i, a in enumerate(boxes) for c in boxes[i + 1:])

        was = reads(base)
        one = themes.take_out(base, [second])
        two = themes.take_out(base, [first, second])
        want_one = [m for m in was if m != second]
        want_one.insert(want_one.index(topk) + 1, second)
        want_two = was[:was.index(topk) + 1] + [first, second] + was[was.index(topk) + 1:]
        check("199: a statement taken out is read straight after the one it was stacked under, the others in their "
              "order, two from one stack in the order they held, and nothing overlaps",
              reads(one) == want_one and reads(two) == want_two and clear(one) and clear(two)
              and one["stacks"] == {topk: [spare[5], spare[7]]} and two["stacks"] == {topk: [spare[7]]},
              f"{reads(one)} {reads(two)}")
        keep_file = themes_file.read_bytes()
        filed = json.loads(keep_file)
        filed["boards"] = [dict(base, id="v1", history=[]) if b["id"] == "v1" else b for b in filed["boards"]]
        themes_file.write_text(json.dumps(filed), encoding="utf-8")
        code, _, _ = answer("board", "apply", "Rowan", "v1", "--ops", ops(
            {"op": "unstack", "items": [sids[first], sids[second]]}), "--note", "Take two out", "--tool", "Claude Code")
        api = themes.normalise(board())
        check("199: the unstack op reads the same, the cards straight after their top",
              code == 0 and themes.order_of(api, pet) == want_two and clear(api), str(themes.order_of(api, pet)))
        themes_file.write_bytes(keep_file)

        # ── E. board new takes stacked
        new = scratch / "stacks-new.json"
        new.write_text(json.dumps({"pets": [{"title": "Walks that start the day", "members": [T, L]}],
                                   "stacked": {T: [U2]}}), encoding="utf-8")
        code, made, _ = answer("board", "new", "Rowan", "--from", str(new), "--note", "A board with a stack",
                               "--tool", "Claude Code", "--layout", "fresh")
        nb = themes.normalise(board(made.get("id", "")) if code == 0 else {})
        check("199: board new makes a board with its stacks, the stacked statement in no label",
              code == 0 and nb.get("stacks") == {top: [under[1]]}
              and not any(under[1] in g["members"] for g in nb["groups"]), str(made)[:300])
        # board new keeping another board's layout keeps that board's stacks, each with its top
        keep = scratch / "stacks-keep.json"
        keep.write_text(json.dumps({"pets": [{"title": "Walks that start the day", "members": [T, L]}]}), encoding="utf-8")
        held_v1 = themes.normalise(board("v1")).get("stacks")
        code, made2, _ = answer("board", "new", "Rowan", "--from", str(keep), "--note", "Keep the layout",
                                "--tool", "Claude Code", "--layout", "v1")
        kb = themes.normalise(board(made2.get("id", "")) if code == 0 else {})
        check("199: board new keeping a board's layout keeps its stacks with their tops, but for a statement the new "
              "board places itself",
              code == 0 and held_v1 == {under[0]: [top, under[1]]} and kb.get("stacks") == {under[0]: [under[1]]}
              and not any(under[1] in g["members"] for g in kb["groups"]), str(kb.get("stacks")))
    finally:
        server_mod.CONFIG_PATH, server_mod.ROOT_OVERRIDE, server_mod.STATE_MEMORY = kept

    # Copy to board: a top copied brings its stack, out of wherever the target held it
    card = lambda x, y, t="A": {"x": x, "y": y, "text": t}
    src = {"id": "v1", "name": "Board 1", "cards": {k: card(i * 210, 40) for i, k in enumerate("abcd")},
           "groups": [{"id": "g1", "label": "One", "members": ["a", "b"], "x": 0, "y": 0}], "discarded": [], "picks": {},
           "stacks": {"a": ["c"]}}
    tgt = {"id": "v2", "name": "Board 2", "cards": {k: card(i * 210, 400) for i, k in enumerate("abcd")},
           "groups": [{"id": "g1", "label": "Else", "members": ["c", "d"], "x": 0, "y": 360}], "discarded": [], "picks": {}}
    copied, gid = themes.copy_into(src, "g1", tgt)
    check("199: Copy to board brings each top's stack with it, the statement under it leaving the target's PET",
          copied.get("stacks") == {"a": ["c"]} and not any("c" in g["members"] for g in copied["groups"])
          and set(next(g for g in copied["groups"] if g["id"] == gid)["members"]) == {"a", "b"}, str(copied.get("stacks")))

    # ── F. the page's model in node: a drop's stack, take out, Make this the top, and an open stack never saved
    node = shutil.which("node")
    if not node:
        skip("199: the stacks model in node", "node is not installed")
        return
    js = support.text("apps/idiograph/static/themes.js")
    script = scratch / "stacks-model.js"
    script.write_text(support.i18n_js() + """
globalThis.$ = () => null;
globalThis.esc = (s) => String(s);
globalThis.escAttr = (s) => String(s);
globalThis.say = () => {};
""" + js + r"""
const card = (x, y) => ({ x, y, text: 'A', time: '00:01' });
const size = (id) => (id.startsWith('g') ? { w: 120, h: 30 } : { w: 200, h: 80 });
const v = { cards: { a: card(0, 40), b: card(210, 40), c: card(0, 130), d: card(420, 40), e: card(0, 400) },
  groups: [{ id: 'g1', label: 'One', members: ['a', 'b', 'c'], x: 0, y: 0 }], discarded: ['d'], picks: {}, stickies: [], stacks: {} };
const out = {};
out.stack = thStackOnto(v, ['b', 'd'], 'a');
out.after = { stacks: JSON.parse(JSON.stringify(v.stacks)), members: v.groups[0].members.slice(), discarded: v.discarded.slice(),
  onCanvas: ['a', 'b', 'd'].map((k) => thOnCanvas(v, k)), counts: thCounts(v), badge: thBadgeText(v, 'g1') };
out.topped = thMakeTop(v, 'd');
out.made = { stacks: JSON.parse(JSON.stringify(v.stacks)), members: v.groups[0].members.slice(), at: [v.cards.d.x, v.cards.d.y] };
out.taken = thTakeOut(v, 'b', { x: 300, y: 50 });
out.out = { stacks: JSON.parse(JSON.stringify(v.stacks)), members: v.groups[0].members.slice(), at: [v.cards.b.x, v.cards.b.y] };
// a stack shown open moves what is below it down, and the save and the undo take where it all stood
TH.stackable = true; TH.mode = 'pets';
const before = thLayout(v, size, null);
const big = (id) => (id === 'd' ? { w: 200, h: 80 + 300 } : size(id));
TH.shifts = thStackRoom(v, big, 'd', { x: v.cards.d.x, y: v.cards.d.y + 80, w: 200 }, 300, before);
out.room = { c: v.cards.c.y, e: v.cards.e.y, shifts: TH.shifts.length };
const body = thBody(v, { id: 'v1', name: 'Board 1' });
const snap = thSnap(v, []);
out.saved = { c: body.cards.c.y, e: body.cards.e.y, stacks: body.stacks, snap: snap.cards.e.y, snapStacks: snap.stacks };
thShiftBack(v, TH.shifts); TH.shifts = [];
out.back = { c: v.cards.c.y, e: v.cards.e.y };
// Take out of the stack: just below the stack at its top's left edge, down past what stands there
TH.v = v;
out.below = thBelowStack(v, 'a', 'd');
// a card lifted out of an open stack is never moved down by the room the stack still makes
TH.lifting = 'e';
const lifted = thStackRoom(v, big, 'd', { x: v.cards.d.x, y: v.cards.d.y + 80, w: 200 }, 300, thLayout(v, size, null));
out.lift = { e: v.cards.e.y, moved: lifted.map((m) => m.id) };
thShiftBack(v, lifted); TH.lifting = null;
// the board's Table view with the stacks on it: the top stands for its stack, with how many it holds
const tree = thTableTree(v, thLayout(v, size, null));
out.table = { rows: tree.pets[0].items.map((x) => x.key), loose: tree.loose, row: thTableStatement(v, 'd', 'g1') };
// the paper edges a shut stack of 2, 3, 5 and 8 cards shows, the top and those under it
out.edges = [2, 3, 5, 8].map((n) => thStackEdges(n - 1));
// the GETs sidebar's Table tab gone, and a sidebar left on it opening the board's Table view instead
out.getsTabs = thTabsOf('gets');
out.tableTab = thTabOf('table', 'gets');
const kept = { 'idiograph-gets-board': JSON.stringify({ open: true, tab: 'table' }) };
globalThis.localStorage = { getItem: (k) => kept[k] ?? null, setItem: (k, val) => { kept[k] = val; } };
thFace = (face) => { out.faced = face; };
TH.mode = 'gets';
thSideTableGone();
out.keptSide = JSON.parse(kept['idiograph-gets-board']);
console.log(JSON.stringify(out));
""", encoding="utf-8")
    run_ = subprocess.run([node, str(script)], capture_output=True, text=True, encoding="utf-8", timeout=60)
    try:
        o = support.plain(json.loads(run_.stdout.strip().splitlines()[-1]))
    except (ValueError, IndexError):
        o = {}
    a = o.get("after") or {}
    check("199: in node, a drop's stack puts the cards under the top, out of the PET and the bin and off the "
          "canvas, the top's PET counting the top alone",
          o.get("stack") == ["b", "d"] and a.get("stacks") == {"a": ["b", "d"]} and a.get("members") == ["a", "c"]
          and a.get("discarded") == [] and a.get("onCanvas") == [True, False, False]
          and a.get("counts") == {"placed": 2, "unplaced": 1, "discarded": 0, "missing": 0} and a.get("badge") == "2", (run_.stdout + run_.stderr)[:400])
    m = o.get("made") or {}
    check("199: in node, Make this the top puts the card in the top's place and its PET, the old top first under it",
          o.get("topped") == "a" and m.get("stacks") == {"d": ["a", "b"]} and m.get("members") == ["d", "c"]
          and m.get("at") == [0, 40], str(m))
    t_ = o.get("out") or {}
    check("199: in node, a card taken out lands where it is let go, in its top's PET after the top",
          o.get("taken") == "d" and t_.get("stacks") == {"d": ["a"]} and t_.get("members") == ["d", "b", "c"]
          and t_.get("at") == [300, 50], str(t_))
    r, s = o.get("room") or {}, o.get("saved") or {}
    check("199: in node, a stack shown open moves what stands below it down, and the save and a step of undo keep "
          "where everything stood, the stacks with them, and shut again it all moves back",
          r.get("e", 0) > 400 and s.get("e") == 400 and s.get("snap") == 400 and s.get("c") == 130
          and s.get("stacks") == {"d": ["a"]} and s.get("snapStacks") == {"d": ["a"]}
          and o.get("back") == {"c": 130, "e": 400}, json.dumps(o)[:400])
    check("199: in node, Take out of the stack puts the card just below the stack at its top's left edge, past the "
          "card standing there, never above or beside", o.get("below") == {"x": 0, "y": 220}, str(o.get("below")))
    lf = o.get("lift") or {}
    check("199: in node, a card dragged out of an open stack stays under the pointer, the room the stack makes moving "
          "what stands below it and never the card lifted", lf.get("e") == 400 and "e" not in (lf.get("moved") or ["e"])
          and "c" in (lf.get("moved") or []), str(lf))
    tb = o.get("table") or {}
    check("199: in node, the board's Table view shows a top with how many are stacked under it, and the statement "
          "under it in no row of its own", sorted(tb.get("rows") or []) == ["b", "c", "d"] and tb.get("loose") == ["e"]
          and "1 stacked" in str(tb.get("row")), str(tb)[:400])
    # a stack's paper edges show its count: the edges a class draws, read from the page's own stylesheet
    css = support.text("apps/idiograph/static/themes.css")

    def drawn_edges(e) -> int:
        rule = re.search(r"\.th-card\.edges-%d \{ --edges: ([^}]*)\}" % e["edges"], css)
        return rule.group(1).count("var(--rule-firm)") if rule else -1

    edges = o.get("edges") or []
    check("199: in node, a shut stack of 2, 3 and 5 cards shows 1, 2 and 4 paper edges, and of 8 four edges and the plus",
          [drawn_edges(e) for e in edges] == [1, 2, 4, 4] and [e.get("more") for e in edges] == [False, False, False, True]
          and "'<span class=\"th-edgemore\" aria-hidden=\"true\">+</span>'" in js, str(edges))
    page = support.page_text()
    check("199: in node, the GETs sidebar has no Table tab, and one left open on it opens the board's Table view",
          "table" not in (o.get("getsTabs") or ["table"]) and o.get("tableTab") == "inspector"
          and 'data-tab="table"' not in page and o.get("faced") == "table"
          and o.get("keptSide") == {"open": False, "tab": "inspector"}, str({k: o.get(k) for k in ("getsTabs", "faced", "keptSide")}))
