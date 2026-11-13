"""Area 377: boards an agent builds come out square, not one long column, and Auto-arrange and the arrange operation
lay a whole board out wide in the order it reads (boardgrid, 12 November 2026).

Adam, 12 November, of a GRAVITY board an agent built through `board apply`: "I'm constantly having to rearrange the
boards that you provide ... you do them very vertically, so they end up very long and narrow ... first of all I do
auto arrange to grid. So you need to make it more square ... I can't see everything on screen all at once." And of
his own Auto-arrange that evening, which scrambled a PET's sub-PETs: the layout must use the width and the height
"and has the right order when put into the table version". Three causes. A PET made over statements waiting in Not
placed wrapped the places they last had in a pile nobody saw, and a new PET stood below the whole board. A Grid set a
label's sub-PETs one under another, its row width taken from a card's width. And there was no whole-board arrange.

What is checked, on an invented participant, Tamsin, learning to row at forty, 80 statements in five PETs with
sub-PETs of mixed sizes, wide and tall. The board as an agent builds it through the command line, in one change and
in a change a PET, comes out between 3:4 and 2:1 wide, no label's statements in one column of more than five, each
PET and each label reading in the order the makes named, and `board new` the same. The whole board's arrange
operation, its dry run writing nothing, keeps every place's order and the PETs table's order on a board laid out as
one tall column and lays it out within the same shape, History keeping the board first. Arrange grid on a PET of
sub-PETs sets them in rows across it, in order. And in node, the page's own thArrangeBoard and thArrange give the
same places as the server's, and keep every place's order when a described label's height follows the width of what
it holds.
"""
from __future__ import annotations

import json
import shutil
from pathlib import Path

import openpyxl

from . import support
from .support import check as said_check, skip


def check(name, ok, detail=""):
    said_check(name, ok, json.dumps(detail, default=str)[:900])


OPEN = ["The first morning on the water", "My hands on the oar", "The coach on the bank", "Falling in at the lock",
        "The boathouse at six", "Rowing in a four", "The cold in January", "Learning to feather",
        "My shoulders the day after", "The heron by the weir", "Racing for the first time", "My sister watching",
        "The sound of the slide", "Being the oldest beginner", "The fog over the river", "Steering past the swans"]
TAIL = ["felt like being let into a secret nobody had told me about.",
        "made me feel clumsy and then, slowly, less so.",
        "was the part of the week I kept for myself and told nobody about.",
        "showed me how much I had stopped trying new things since the children were born.",
        "frightened me more than I let anyone see, and I went back anyway."]
TALK = [f"{OPEN[n % len(OPEN)]} {TAIL[(n // len(OPEN)) % len(TAIL)]}" for n in range(80)]

# five PETs: their own statements, then sub-PETs of mixed sizes, one of twelve and one of one
PLAN = [
    ("Being a beginner at forty", 1, [12, 2, 7]),
    ("The river as somewhere of her own", 4, [1, 9]),
    ("A body that learns slowly", 0, [3, 3, 10, 1, 2]),
    ("Fear, and going back anyway", 6, []),
    ("Who she is in the boat", 2, [8, 1, 5, 3]),
]
SUBS = ["The first weeks", "What the coach saw", "Others watching", "Mornings alone", "A word for it", "The cold",
        "Hands and back", "Getting it wrong", "The lock", "Going back", "In a crew", "Steering", "The weir", "Racing"]
DESCRIBED = ("What she found she could still learn, slowly and in front of others, when nobody expected her to, and what "
             "it cost her to be seen getting it wrong on the water, morning after morning, by people half her age who "
             "had rowed since school")

STUBS = """
globalThis.$ = () => null;
globalThis.esc = (s) => String(s);
globalThis.escAttr = (s) => String(s);
globalThis.say = () => {};
globalThis.MOD = (e) => !!(e && e.metaKey);
globalThis.api = async () => ({});
"""

HARNESS = r"""
const out = {};
const copy = (o) => JSON.parse(JSON.stringify(o));
const spots = (v) => Object.fromEntries(Object.entries(v.cards).map(([k, c]) => [k, [Math.round(c.x), Math.round(c.y)]]));
// every place's reading order as the page reads it, the PETs and inside each label
const orders = (v, size) => {
  const layout = thLayout(v, size, null);
  const parents = thParents(v);
  const o = { '': gtCanvasOrder(v.groups.filter((g) => parents[g.id] === undefined)) };
  for (const g of v.groups) o[g.id] = thThemeOrder(v, g.id, layout);
  return JSON.stringify(o);
};
// the same places as the server's arrange, at the server's sizes
{
  const S = SAME.sizes;
  const size = (id) => { const s = S.cards[id] || S.labels[id]; return { w: s[0], h: s[1] }; };
  const v = copy(SAME.board);
  thArrangeBoard(v, size, 'grid');
  out.board = spots(v);
  const p = copy(SAME.board);
  thArrange(p, SAME.pet, size, 'grid');
  out.pet = spots(p);
}
// a described label's height follows the width of what it holds, as thLabelsWiden draws it: the order kept
{
  const S = DESC.sizes;
  const v = copy(DESC.board);
  const at = (id, w) => {
    const s = S.labels[id];
    if (!S.described[id]) return { w: s[0], h: s[1] };
    const wide = Math.max(340, Math.floor(w || 0));
    return { w: wide, h: s[1] + 18 * Math.ceil((S.described[id] * 7.2) / (wide - 73)) };
  };
  let now = {};
  const size = (id, body) => (S.cards[id] ? { w: S.cards[id][0], h: S.cards[id][1] } : body !== undefined ? at(id, body) : now[id]);
  const measure = () => {
    for (let pass = 0; pass < 3; pass += 1) {
      const layout = thLayout(v, size, null);
      now = Object.fromEntries(v.groups.map((g) => [g.id, at(g.id, layout[g.id] && layout[g.id].body ? layout[g.id].body.w : 0)]));
    }
  };
  now = Object.fromEntries(v.groups.map((g) => [g.id, at(g.id, 0)]));
  measure();
  const before = orders(v, size);
  thArrangeBoard(v, size, 'grid');
  measure();
  out.described = { before, after: orders(v, size), clash: thClashes(v, size).length };
}
console.log(JSON.stringify(out));
"""


def make_workbook(root: Path, folder: str, speaker: str) -> Path:
    """Tamsin's annotated workbook, a statement to each of her 80 turns, one line long to four."""
    import workbook as wb_mod
    case = root / folder
    (case / "Source").mkdir(parents=True)
    raw = openpyxl.Workbook()
    first = raw.active
    first.title = "Initial"
    first.append(["Name", "Timestamp", "Transcript"])
    for n, said in enumerate(TALK):
        first.append(["Interviewer", f"00:{n // 2:02d}:{(n % 2) * 30 + 4:02d}", "And then?"])
        first.append([speaker, f"00:{n // 2:02d}:{(n % 2) * 30 + 20:02d}", said])
    source = case / "Source" / f"{folder} - interview.xlsx"
    raw.save(source)
    book = wb_mod.create_from_source(source, case / f"{folder} - EN & ES.xlsx")
    wb = openpyxl.load_workbook(book, rich_text=True)
    ws = wb.worksheets[0]
    cols = wb_mod.detect_columns(ws)
    for n, said in enumerate(TALK):
        ws.cell(3 + 2 * n, cols["es"]).value = " ".join((said.rstrip(".") + ", " + said).split()[:4 + 4 * (n % 4)])
    wb.save(book)
    return book


def plan_ops(described: bool = False):
    """The makes an agent sends, a PET then its sub-PETs, each over statements waiting in Not placed, and the same as
    `board new`'s structure, with the order each label's members were named in."""
    n = iter(range(1, 81))
    ops, pets, named = [], [], {}
    s_i = 0
    for p, (title, own, subs) in enumerate(PLAN, start=1):
        members = [f"S{next(n)}" for _ in range(own)]
        ops.append({"op": "make", "ref": f"p{p}", "title": title, "inside": None, "members": members})
        named[title] = list(members)
        pet = {"title": title, "members": members, "subs": []}
        for s, size in enumerate(subs, start=1):
            sub = SUBS[s_i % len(SUBS)]
            s_i += 1
            kids = [f"S{next(n)}" for _ in range(size)]
            ops.append({"op": "make", "ref": f"p{p}s{s}", "title": sub, "inside": f"p{p}", "members": kids})
            if described and s % 2:
                ops.append({"op": "describe", "label": f"p{p}s{s}", "description": DESCRIBED})
            named[title].append(sub)
            named[sub] = kids
            pet["subs"].append({"title": sub, "members": kids})
        pets.append(pet)
    return ops, pets, named


def shape(board: dict) -> dict:
    """A board's whole width and height by the server's sizes, w / h, and the longest column of statements in a label
    holding more than five of its own."""
    import themes
    v = themes.normalise(board)
    d = themes.layout_boxes(v)
    parents = themes.parents_of(v["groups"])
    tops = [g["id"] for g in v["groups"] if g["id"] not in parents]
    u = themes.union([d["frames"][t] for t in tops])
    longest = 0
    for g in v["groups"]:
        own = [m for m in g["members"] if m in d["cards"]]
        if len(own) > 5:
            xs: dict = {}
            for m in own:
                xs[round(d["cards"][m][0])] = xs.get(round(d["cards"][m][0]), 0) + 1
            longest = max([longest] + list(xs.values()))
    return {"w": round(u[2]), "h": round(u[3]), "aspect": round(u[2] / u[3], 2), "longest": longest}


def orders(board: dict, sids: dict | None = None) -> dict:
    """Every place's reading order, the PETs under "" and each label under its title, statements by their short ids,
    and the PETs table's order of statements."""
    import themes
    v = themes.normalise(board)
    d = themes.layout_boxes(v)
    title = {g["id"]: g["label"] for g in v["groups"]}
    say = lambda m: title.get(m) or (sids or {}).get(m, m)
    out = {"": [say(m) for m in themes.order_of(v, None, d)]}
    for g in v["groups"]:
        out[g["label"]] = [say(m) for m in themes.order_of(v, g["id"], d)]
    out["table"] = [say(m) for m in themes.placed_order(v)]
    return out


def test_board_grid(scratch: Path):
    print("\n377. Boards an agent builds come out square, not one long column, and the whole board's arrange lays "
          "it out wide in the order it reads, the app's and the operation's alike (boardgrid, 12 November 2026)")
    import cli
    import server as server_mod
    import themes

    base = scratch / "board-grid-377"
    shutil.rmtree(base, ignore_errors=True)
    config_file = base / "config-377.json"
    base.mkdir(parents=True)
    config_file.write_text(json.dumps({"projects": [], "interviewer": "Interviewer", "corpus": "",
                                       "gravity_reference": "", "corpus_exclude": []}), encoding="utf-8")

    def project(name: str) -> Path:
        root = base / name / "Rowing"
        root.mkdir(parents=True)
        (root / server_mod.PROJECT_FILE).write_text(json.dumps({
            "name": "Rowing", "research_question": "How do adults experience learning to row?",
            "agents": {"allowed": True, "at": "2026-11-12T09:00:00+00:00"}}), encoding="utf-8")
        make_workbook(root, "P1 - Tamsin", "Tamsin")
        return root

    def run(root, *args):
        return cli.run(["--config", str(config_file), "--root", str(root), *args])

    def board_of(root) -> dict:
        f = next((root / "P1 - Tamsin" / "Working").glob("* - EN & ES.themes.json"))
        return themes.current_version(json.loads(f.read_text(encoding="utf-8")))

    def apply(root, ops, note, *more):
        spec = root.parent / "ops.json"
        spec.write_text(json.dumps({"operations": ops}), encoding="utf-8")
        return run(root, "board", "apply", "Tamsin", board_of(root)["name"], "--ops", str(spec), "--note", note,
                   "--tool", "Claude Code", *more)

    def sids_of(root) -> dict:
        read = themes.read_cards(next((root / "P1 - Tamsin").glob("* - EN & ES.xlsx")))
        return {c["key"]: f"S{i}" for i, c in enumerate(read["cards"], start=1)}

    def wide(s: dict) -> bool:
        return 0.75 <= s["aspect"] <= 2 and s["longest"] <= 5

    ops, pets, named = plan_ops()

    def read_as_named(o: dict) -> bool:
        return o[""] == [p[0] for p in PLAN] and all(o[label] == want for label, want in named.items())

    # ── A. built as an agent builds it, in one change and in a change a PET
    built = {}
    for how in ("one change", "a change a PET"):
        root = project(how.replace(" ", "-"))
        made = run(root, "board", "fresh", "Tamsin", "--start", "empty", "--note", "A board to build", "--tool", "Claude Code")
        chunks = [ops] if how == "one change" else [[o for o in ops if o["ref"].startswith(f"p{p}")] for p in range(1, 6)]
        done = [apply(root, chunk, f"Build part {i + 1}") for i, chunk in enumerate(chunks)]
        board = board_of(root)
        s, o = shape(board), orders(board, sids_of(root))
        built[how] = (root, board)
        check(f"377: a board an agent builds from Not placed in {how} comes out between 3:4 and 2:1 wide, no label's "
              "statements in one column of more than five, the PETs and every label reading in the order the makes "
              "named them",
              made[0] == 0 and all(d[0] == 0 for d in done) and wide(s) and read_as_named(o),
              {"shape": s, "codes": [made[0]] + [d[0] for d in done], "pets": o[""],
               "said": [(d[1] + d[2])[-200:] for d in done if d[0]]})

    # ── B. board new from the same structure, with no board yet and over a board whose statements all wait
    for how in ("no board yet", "a board waiting"):
        root = project("new-" + how.replace(" ", "-"))
        if how == "a board waiting":
            run(root, "board", "fresh", "Tamsin", "--start", "empty", "--note", "Start", "--tool", "Claude Code")
        plan = root.parent / "plan.json"
        plan.write_text(json.dumps({"pets": pets, "not_placed": {}}), encoding="utf-8")
        made = run(root, "board", "new", "Tamsin", "--from", str(plan), "--note", "Her first board", "--tool", "Claude Code")
        board = board_of(root)
        s, o = shape(board), orders(board, sids_of(root))
        check(f"377: board new with {how} comes out between 3:4 and 2:1 wide, in the order given",
              made[0] == 0 and wide(s) and read_as_named(o), {"shape": s, "code": made[0], "pets": o[""],
                                                               "said": (made[1] + made[2])[-300:]})

    # ── C. the whole board's arrange on a board laid out as one tall column, each PET's sub-PETs one under another
    root, board = built["one change"]
    tall = themes.normalise(board)
    in_order = themes.order_of(tall, None)
    for t in in_order:
        tall = themes.arrange(tall, t, "column")
    y = 0
    for t in in_order:
        f = themes.layout_boxes(tall)["frames"][t]
        themes._shift({g["id"]: g for g in tall["groups"]}, tall, t, -f[0], y - f[1])
        themes.sync_labels(tall)
        y += f[3] + themes.COPY_GAP
    was = orders(tall)
    s_tall = shape(tall)
    flat = themes.arrange_board(tall, "grid")
    check("377: the whole board's arrange lays a board of one tall column out between 3:4 and 2:1 wide, every PET, "
          "sub-PET and statement and the PETs table reading exactly as before",
          s_tall["aspect"] < 0.75 and wide(shape(flat)) and orders(flat) == was,
          {"before": s_tall, "after": shape(flat), "drift": [k for k in was if was[k] != orders(flat).get(k)]})
    again = themes.arrange_board(flat, "grid")
    check("377: arranged again, the board stands as it was", [c for c in again["cards"].values()] == list(flat["cards"].values()))

    # through the command line, as an agent finishes a board, dry run first, on the board built a change a PET, whose
    # PETs each took the next free place as they came
    croot, cboard = built["a change a PET"]
    f = next((croot / "P1 - Tamsin" / "Working").glob("* - EN & ES.themes.json"))
    raw = f.read_bytes()
    dry = apply(croot, [{"op": "arrange", "way": "grid"}], "Arrange the board", "--dry-run")
    kept = f.read_bytes() == raw
    before = orders(cboard)
    steps = len(themes.history_of(cboard))
    want = {k: (c["x"], c["y"]) for k, c in themes.arrange_board(cboard)["cards"].items()}
    done = apply(croot, [{"op": "arrange", "way": "grid"}], "Arrange the board")
    after = board_of(croot)
    check("377: board apply's arrange with no label arranges the whole board, its dry run writing nothing, every place "
          "reading as before, the board kept first in History, and the same places as the server's own arrange",
          dry[0] == 0 and kept and done[0] == 0 and "whole board" in done[1] and orders(after) == before
          and len(themes.history_of(after)) == steps + 1 and want != {k: (c["x"], c["y"]) for k, c in cboard["cards"].items()}
          and {k: (c["x"], c["y"]) for k, c in after["cards"].items()} == want,
          {"dry": (dry[1] + dry[2])[-200:], "done": (done[1] + done[2])[-200:]})
    bad = apply(croot, [{"op": "arrange", "way": "spiral"}], "Arrange the board")
    check("377: a whole-board arrange a way Auto-arrange has not got is refused, nothing written",
          bad[0] != 0 and "grid" in (bad[1] + bad[2]))

    # ── D. arrange grid on a PET of sub-PETs lays them in rows across it, in order, never one column
    pet = next(g["id"] for g in tall["groups"] if g["label"] == "A body that learns slowly")
    gridded = themes.arrange(tall, pet, "grid")
    d = themes.layout_boxes(gridded)
    subs = [m for m in next(g for g in gridded["groups"] if g["id"] == pet)["members"]]
    lefts = {round(d["frames"][m][0]) for m in subs}
    check("377: Auto-arrange's grid on a PET of five sub-PETs sets them in rows across it, not one column, in the order "
          "they read", len(lefts) >= 2 and orders(gridded)["A body that learns slowly"] == was["A body that learns slowly"],
          {"lefts": sorted(lefts), "order": orders(gridded)["A body that learns slowly"]})

    # ── E. the page's own code in node: the same places, and the order kept as a described label's height follows
    if not shutil.which("node"):
        skip("377: the page's Auto-arrange under node", "node is not on this machine")
        return

    def page_board(v: dict) -> dict:
        v = themes.normalise(v)
        return {"cards": {k: dict(c) for k, c in v["cards"].items()}, "groups": v["groups"], "discarded": v["discarded"],
                "stacks": v.get("stacks") or {}, "stickies": [], "picks": v.get("picks") or {}}

    def sizes(v: dict) -> dict:
        d = themes.layout_boxes(themes.normalise(v))
        return {"cards": {k: [b[2], b[3]] for k, b in d["cards"].items()},
                "labels": {g: [b[2], b[3]] for g, b in d["labels"].items()}}

    droot = project("described")
    run(droot, "board", "fresh", "Tamsin", "--start", "empty", "--note", "A board to build", "--tool", "Claude Code")
    dops, _, _ = plan_ops(described=True)
    apply(droot, dops, "Build it described")
    dboard = themes.normalise(board_of(droot))
    # each PET a column first, so the whole board's grid widens what each described label holds and its title and
    # description take fewer lines
    for t in themes.order_of(dboard, None):
        dboard = themes.arrange(dboard, t, "column")
    plain = {g: themes.label_size(lab, any(m in {x["id"] for x in dboard["groups"]} for m in members))
             for g, lab, members in [(x["id"], x["label"], x["members"]) for x in dboard["groups"]]}
    dsizes = {"cards": sizes(dboard)["cards"], "labels": {g: list(s) for g, s in plain.items()},
              "described": {g["id"]: len(themes.description_of(g)) for g in dboard["groups"] if themes.description_of(g)}}
    script = (support.i18n_js() + STUBS + support.text("apps/idiograph/static/themes.js")
              + f"\nconst SAME = {json.dumps({'board': page_board(tall), 'sizes': sizes(tall), 'pet': pet})};\n"
              + f"const DESC = {json.dumps({'board': page_board(dboard), 'sizes': dsizes})};\n" + HARNESS)
    ran = support.run_node(script, base, "board-grid-377.js", timeout=240)
    try:
        o = json.loads(ran.stdout.strip().splitlines()[-1])
    except (ValueError, IndexError):
        o = {}
    if not o:
        check("377: the page's own code runs in node", False, (ran.stdout + ran.stderr)[-900:])
        return
    server_board = {k: [c["x"], c["y"]] for k, c in themes.arrange_board(tall, "grid")["cards"].items()}
    server_pet = {k: [c["x"], c["y"]] for k, c in themes.arrange(tall, pet, "grid")["cards"].items()
                  if k in themes.cards_under({g["id"]: g for g in tall["groups"]}, pet)}
    check("377: the page's Auto-arrange with nothing selected gives every statement the place the arrange operation gives "
          "it, and on a PET of sub-PETs the same places as the server's arrange",
          o["board"] == server_board and {k: o["pet"][k] for k in server_pet} == server_pet,
          {"board": [k for k in server_board if o["board"].get(k) != server_board[k]][:6],
           "pet": [k for k in server_pet if o["pet"].get(k) != server_pet[k]][:6]})
    check("377: on the page, with each described label's height following the width of what it holds, the whole board's "
          "Auto-arrange keeps every place's order, nothing overlapping",
          o["described"]["before"] == o["described"]["after"] and o["described"]["clash"] == 0,
          {"clash": o["described"]["clash"]} | ({"before": o["described"]["before"][:400], "after": o["described"]["after"][:400]}
                                                 if o["described"]["before"] != o["described"]["after"] else {}))
