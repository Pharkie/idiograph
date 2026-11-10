"""Area 294: two board ops that said they did what they did not (boardgaps, 30 October 2026).

A statement written after a board was made, with `turn write` or in the app, has no card in the board's file
until the next save, and the canvas shows it waiting in Not placed. `board apply` read the file's cards alone, so
a move of it into a label said "moved" and left it out, `put_all_on` passed it over and `stack` refused it as
"not a statement on the board". Every op now takes it as one of the board's (`themes.with_new`). And a `move` to
null on a card lying loose on the canvas said it moved it out to Not placed while it stayed loose: now it waits
there, as Back to Not placed does on the canvas, and the answer names only what each move took out.

Every word invented: Kit asks Quill, who learnt to swim late, about the water at three points, Before, Midway and
3m, the last a sheet whose name starts with a figure, so its keys read 3m:5:1.
"""
from __future__ import annotations

import base64
import hashlib
import json
import os
import shutil
import subprocess
from pathlib import Path

import openpyxl

from . import support
from .support import check as said_check, skip


def check(name, ok, detail=""):
    said_check(name, ok, str(detail)[:700])


FIRST = ("Kit: [00:00:03] What did you expect of the pool?\nQuill: [00:00:09] That everyone would watch me.\n")
LATER = ("Kit: [00:00:02] How is the water now?\nQuill: [00:00:07] I put my face in without counting first.\n"
         "Kit: [00:00:30] And the deep end?\nQuill: [00:01:12] I go to the rope and hold it, and then I let go.\n"
         "Kit: [00:02:00] What changed?\nQuill: [00:02:40] The lifeguard stopped watching me, I think.\n"
         "Kit: [00:03:10] How did that feel?\nQuill: [00:03:55] Like being let off a lead, and a bit lonely.\n")
THREE = [{"label": "Before", "description": "Before the lessons"}, {"label": "Midway", "description": ""},
         {"label": "3m", "description": "Three months on"}]
OWN = ["Face in the water", "Letting go of the rope", "No longer watched", "Free and a little alone"]

# the page's model in node, as area 221 runs it: the state /api/themes answers loaded as thLoad loads it, a new
# statement dragged from Not placed into a PET and a loose card sent back to Not placed, and the body a save sends
PAGE = r"""
const state = JSON.parse(process.env.BG_STATE);
const want = JSON.parse(process.env.BG_WANT);
thRender = () => {}; thEase = () => {}; thSoon = () => {}; thInspectorOpen = () => {}; thPanelFollow = () => {};
thSettle = () => false; thFlash = () => {}; thListDraw = () => {}; thSideFlash = () => {}; thDrawSel = () => {};
thToWorld = (x, y) => ({ x, y }); thFit = () => {};
TH.mode = 'pets'; TH.live = true; TH.layout = {}; TH.sheets = state.sheets;
const cards = {}; for (const c of state.cards) cards[c.key] = Object.assign({}, c);
const v = { cards, groups: state.groups.map((g) => Object.assign({}, g, { members: g.members.slice() })),
  discarded: state.discarded.slice(), picks: state.picks || {}, stacks: state.stacks || {}, not_same: state.not_same || [],
  stickies: state.stickies || [], waits: true };
thWaitsRead(v);
TH.v = v;
TH.sel = { cards: new Set(), groups: new Set(), stickies: new Set() };
TH.stackable = true; TH.pairable = true; TH.stickable = true;
const out = { read: { waiting: thWaiting(v, want.fresh), loose: thOnCanvas(v, want.loose) } };
// the new statement let go on the PET's body
thTargetAt = () => ({ group: want.label });
thSideDrop([want.fresh], 400, 300);
// and the loose card sent back to Not placed, as Backspace and a drag onto the sidebar do
thWaitDo([want.loose]);
out.after = { inLabel: v.groups.find((g) => g.id === want.label).members.includes(want.fresh), waits: thWaiting(v, want.loose) };
out.body = thBody(v, state.version);
console.log(JSON.stringify(out));
"""


def test_board_gaps(scratch: Path):
    print("\n294. Board ops on a statement written after the board was made, a move into a label, put_all_on, a stack "
          "and an order, each dry run as its apply, board list counting it, and a move to null on a card loose on the "
          "canvas sending it to wait in Not placed, the answer naming only what moved, the page doing the same (30 October)")
    import cli
    import mcp_server
    import server as server_mod
    import themes
    import idiograph_routes
    import workbook as wb_mod

    b64 = lambda text: base64.b64encode(text.encode("utf-8")).decode("ascii")
    base = scratch / "board-gaps-294"
    shutil.rmtree(base, ignore_errors=True)
    base.mkdir(parents=True)
    cfg = base / "config.json"
    cfg.write_text(json.dumps({"projects": [], "interviewer": "Kit", "corpus": "", "gravity_reference": "",
                               "corpus_exclude": []}), encoding="utf-8")
    kept = (server_mod.CONFIG_PATH, server_mod.ROOT_OVERRIDE, server_mod.STATE_PATH, server_mod.STATE_MEMORY)

    def row(name, text, interview, **more):
        return dict({"name": name, "data": b64(text), "pseudonym": "Quill", "interview": interview,
                     "speakers": {"Kit": "interviewer", "Quill": "participant"}}, **more)

    try:
        server_mod.CONFIG_PATH, server_mod.ROOT_OVERRIDE = cfg, None
        server_mod.STATE_PATH, server_mod.STATE_MEMORY = base / "state.json", {"recent": []}
        root = base / "Swimming late"
        root.mkdir()
        made = idiograph_routes.api_new_project({"op": "make", "folder": str(root), "name": "Swimming late",
                                                 "research_question": "How do adults who learn to swim late live it?",
                                                 "files": [row("before.txt", FIRST, "Before")]})
        rid = made["project"]["id"]
        idiograph_routes.api_project({"root": rid, "agents": True})

        def run(*args):
            code, out, err = cli.run(["--root", str(root), "--config", str(cfg), *args, "--json"])
            try:
                return code, support.plain(json.loads(out)) if out.strip() else {}, err
            except ValueError:
                return code, {}, out + err

        def spec(name, value) -> str:
            path = base / name
            path.write_text(json.dumps(value), encoding="utf-8")
            return str(path)

        code, said, err = run("timepoints", "--from", spec("tp.json", THREE), "--note", "Three points", "--tool", "Claude Code")
        check("294: the command line sets the project's three timepoints", code == 0, (said, err))
        idiograph_routes.api_add_transcripts({"op": "add", "root": rid, "files": [row("later.txt", LATER, "3m", timepoint=3)]})
        book = root / "P1 - Quill" / "P1 Quill - EN & ES.xlsx"
        sheet = "3m"
        wb = openpyxl.load_workbook(book, read_only=True)
        try:
            rows = [r for r, values in enumerate(wb[sheet].iter_rows(min_row=2, max_col=1, values_only=True), start=2)
                    if str(values[0] or "").strip() == "Quill"]
        finally:
            wb.close()
        for r, said_here in zip(rows, OWN):
            wb_mod.save_turn(book, sheet, r, said_here, "", "")
        key = lambda r, line: themes.card_key(sheet, r, line)
        olds = [key(r, 0) for r in rows]
        check("294: the invented participant has four statements at 3m, their keys on a sheet named 3m",
              len(rows) == 4 and olds[0].startswith("3m:"), olds)

        tp = ("--timepoint", "3m")

        def board_file() -> dict:
            with themes.scoped(3):
                data = themes.load(book) or {}
            return themes.find_version(data, bid) or {}

        def sha() -> str:
            with themes.scoped(3):
                path = themes.themes_path(book)
            return hashlib.sha256(path.read_bytes()).hexdigest() if path.exists() else ""

        def apply(ops, note="As he asked", dry=False):
            return run("board", "apply", "Quill", bid, *tp, "--ops", spec("ops.json", {"operations": ops}), "--note", note,
                       "--tool", "Claude Code", *(["--dry-run"] if dry else []))

        def both(ops, note="As he asked"):
            """A change run dry first and then for real: the file untouched by the dry run, and what each said."""
            held = sha()
            dry = apply(ops, note, dry=True)
            same = sha() == held
            real = apply(ops, note)
            return dry, real, same

        def alike(dry, real) -> bool:
            """The dry run says what the apply did, word for word."""
            d = str(dry[1].get("said") or "").split(" it would have: ", 1)[-1]
            r = str(real[1].get("said") or "").split(f" {real[1].get('name')} as it stood", 1)[0]
            return dry[0] == real[0] == 0 and bool(d) and d == r[0].lower() + r[1:]

        def write_turn(r: int, *new: str):
            """New statements added to a passage as an agent adds them, those there sent back with their keys."""
            with themes.scoped(3):
                there = [c for c in themes.read_cards(book)["cards"] if c["row"] == r]
            pairs = [{"statement": c["text"], "quote": "", "key": c["key"]} for c in there]
            pairs += [{"statement": words, "quote": ""} for words in new]
            return run("turn", "write", "Quill", sheet, str(r), "--from", spec("turn.json", {"pairs": pairs}),
                       "--note", "Add a statement", "--tool", "Claude Code")

        code, said, err = run("board", "fresh", "Quill", *tp, "--note", "A board", "--tool", "Claude Code")
        bid = said.get("id")
        code, listed, err = run("board", "list", "Quill", *tp)
        made = next((b for b in listed.get("boards") or [] if b["id"] == bid), {})
        check("294: board fresh on a participant with no board yet names the board it made, the one on the canvas, "
              "past the Board 1 an open offers",
              code == 0 and made.get("canvas") is True and made.get("name") == said.get("name") == "Board 2"
              and said["said"].startswith("Made Board 2 on ") and "Board 1 is as before" in said["said"], (said, listed))
        dry, real, same = both([{"op": "make", "title": "Letting go", "members": [olds[0], olds[1]], "ref": "go"},
                                {"op": "put_all_on"}])
        label = next(g["id"] for g in board_file().get("groups") or [] if g["label"] == "Letting go")
        check("294: a board at 3m with a PET over two statements and the other two loose on the canvas",
              real[0] == 0 and {k for k, c in board_file()["cards"].items() if c.get("loose")} == {olds[2], olds[3]},
              (real, err))

        # ── A. a statement written after the board, moved into a label
        code, said, err = write_turn(rows[0], "Counting less each week")
        n1 = key(rows[0], 1)
        code, shown, err = run("board", "show", "Quill", bid, *tp)
        code, listed, err = run("board", "list", "Quill", *tp)
        entry = next(b for b in listed["boards"] if b["id"] == bid)
        check("294: board show lists a statement written after the board under Not placed, waiting, not loose",
              any(s["key"] == n1 and not s.get("loose") for s in shown.get("unplaced") or [])
              and n1 not in board_file()["cards"], shown.get("unplaced"))
        check("294: and board list counts it as waiting in Not placed, as the canvas does",
              entry["waiting"] == 1 and entry["not_placed"] == 3, entry)
        dry, real, same = both([{"op": "move", "items": [n1], "to": label}])
        members = next(g for g in board_file()["groups"] if g["id"] == label)["members"]
        check("294: a move of it into a label puts it there, the dry run writing nothing and saying what the apply did",
              n1 in members and same and alike(dry, real) and "moved one statement into 'Letting go'" in dry[1]["said"],
              (dry, real))

        # ── B. put_all_on takes a statement written after the board
        code, said, err = write_turn(rows[1], "Holding the rope less tightly")
        n2 = key(rows[1], 1)
        dry, real, same = both([{"op": "put_all_on"}])
        check("294: put_all_on puts a statement written after the board on the canvas, loose, as said in its dry run",
              board_file()["cards"].get(n2, {}).get("loose") is True and same and alike(dry, real)
              and "put the 1 statement waiting" in dry[1]["said"], (dry, real))

        # ── C. a stack of two written after the board
        code, said, err = write_turn(rows[2], "Unwatched at last", "Watched by nobody now")
        n3, n4 = key(rows[2], 1), key(rows[2], 2)
        dry, real, same = both([{"op": "stack", "items": [n4], "under": n3}])
        check("294: a stack names statements written after the board, the one under the other, as its dry run said",
              (board_file().get("stacks") or {}).get(n3) == [n4] and same and alike(dry, real), (dry, real))

        # ── D. an order naming one written after the board, moved in by the same change
        code, said, err = write_turn(rows[3], "Let off the lead")
        n5 = key(rows[3], 1)
        dry, real, same = both([{"op": "move", "items": [n5], "to": label},
                                {"op": "order", "under": label, "items": [n5, olds[1], olds[0], n1]}])
        code, shown, err = run("board", "show", "Quill", bid, *tp)
        pet = next(t for t in shown["themes"] if t["id"] == label)
        check("294: an order names one written after the board and moved in by the same change, as its dry run said",
              [s["key"] for s in pet["statements"]][:4] == [n5, olds[1], olds[0], n1] and same and alike(dry, real),
              (dry, real, [s["key"] for s in pet["statements"]]))

        # ── E. loose cards moved to null go to wait in Not placed
        loose = {k for k, c in board_file()["cards"].items() if c.get("loose")}
        dry, real, same = both([{"op": "move", "items": [olds[2], olds[3]], "to": None}])
        now = board_file()
        check("294: a move to null on two loose cards sends them to wait in Not placed, no longer loose, as its dry run said",
              {olds[2], olds[3]} <= loose and not any(now["cards"][k].get("loose") for k in (olds[2], olds[3]))
              and {olds[2], olds[3]} <= set(themes.waiting_keys(now)) and same and alike(dry, real)
              and "moved two statements out to Not placed" in dry[1]["said"], (dry, real))
        code, shown, err = run("board", "show", "Quill", bid, *tp)
        check("294: and board show no longer marks them on the canvas",
              not any(s.get("loose") for s in shown["unplaced"] if s["key"] in (olds[2], olds[3])), shown["unplaced"])
        held = sha()
        code, said, err = apply([{"op": "move", "items": [olds[2]], "to": None}])
        check("294: a move to null of one waiting already changes nothing and says so", code == 0 and sha() == held
              and said.get("changed") is False and "Nothing to change" in said.get("said", ""), said)
        sids = {s["key"]: s["id"] for s in run("statements", "Quill", *tp)[1]["statements"]}
        dry, real, same = both([{"op": "move", "items": [n2, olds[3]], "to": None}])
        check("294: one naming a loose card and one waiting moves the loose card alone and says the other waited already",
              not board_file()["cards"][n2].get("loose") and same and alike(dry, real)
              and "moved one statement out to Not placed" in dry[1]["said"]
              and f"Left {sids[olds[3]]} waiting in Not placed, as it was already" in dry[1]["said"], (dry, real))

        # ── F. MCP's board_apply, the same command
        code, said, err = write_turn(rows[1], "The rope as a choice")
        n6 = key(rows[1], 2)
        srv = mcp_server.Server(str(root), config=str(cfg))
        srv.receive(json.dumps({"jsonrpc": "2.0", "id": 1, "method": "initialize",
                                "params": {"protocolVersion": "2025-06-18", "clientInfo": {"name": "claude-ai"}}}))
        call = lambda args: srv.receive(json.dumps({"jsonrpc": "2.0", "id": 2, "method": "tools/call",
                                                    "params": {"name": "board_apply", "arguments": args}}))["result"]
        ask = {"case": "Quill", "board": bid, "timepoint": "3m", "request": "Into Letting go",
               "operations": [{"op": "move", "items": [n6], "to": label}]}
        res = call(dict(ask, dry_run=True))
        res2 = call(ask)
        members = next(g for g in board_file()["groups"] if g["id"] == label)["members"]
        check("294: through MCP, board_apply moves a statement written after the board into a label, dry run first",
              res["isError"] is False and res2["isError"] is False and n6 in members
              and "moved one statement into 'Letting go'" in res["content"][0]["text"], (res, res2))

        # ── G. the page does the same: a new statement dragged from Not placed into the PET, a loose card sent back
        code, said, err = apply([{"op": "put_all_on"}])
        code, said, err = write_turn(rows[3], "Alone in the lane")
        n7 = key(rows[3], 2)
        twin = base / "page" / "Swimming late"
        shutil.copytree(root, twin)
        dry, real, same = both([{"op": "move", "items": [n7], "to": label}, {"op": "move", "items": [olds[2]], "to": None}])
        agent = board_file()
        node = shutil.which("node")
        if not node:
            skip("294: the page's model in node", "node is not installed")
            return
        tbook = twin / "P1 - Quill" / "P1 Quill - EN & ES.xlsx"
        # what /api/themes answers and /api/themes-save writes, the twin being a folder no project names
        with themes.scoped(3):
            state = themes.state(tbook, "P1 - Quill", board=bid)
        script = base / "page-294.js"
        script.write_text(support.i18n_js() + """
globalThis.$ = (id) => (id === 'th-stage' ? { getBoundingClientRect: () => ({ left: 0, top: 0, width: 800, height: 600, right: 800, bottom: 600 }) } : null);
globalThis.esc = (s) => String(s);
globalThis.escAttr = (s) => String(s);
globalThis.say = () => {};
globalThis.MOD = (e) => !!(e && e.metaKey);
""" + support.text("apps/idiograph/static/themes.js") + PAGE, encoding="utf-8")
        env = dict(os.environ, BG_STATE=json.dumps(state, default=str),
                   BG_WANT=json.dumps({"fresh": n7, "loose": olds[2], "label": label}))
        ran = subprocess.run([node, str(script)], capture_output=True, text=True, encoding="utf-8", timeout=120, env=env)
        try:
            o = json.loads(ran.stdout.strip().splitlines()[-1])
        except (ValueError, IndexError):
            o = {}
        check("294: the page reads the new statement as waiting in Not placed and the loose card as on the canvas, and "
              "a drop of the one into the PET and Back to Not placed on the other do what the op did",
              o.get("read") == {"waiting": True, "loose": True} and o.get("after") == {"inLabel": True, "waits": True},
              (ran.stdout + ran.stderr)[:600])
        with themes.scoped(3):
            themes.save(tbook, o.get("body") or {}, "P1 - Quill")
            page = themes.find_version(themes.load(tbook) or {}, bid) or {}
        shape = lambda v: ({g["id"]: sorted(g["members"]) for g in v.get("groups") or []},
                           sorted(k for k, c in (v.get("cards") or {}).items() if c.get("loose")),
                           themes.waiting_keys(v), sorted(v.get("discarded") or []), v.get("stacks") or {})
        check("294: the board the page saves holds what the agent's op wrote: every label's statements, the loose cards, "
              "those waiting, Set aside and the stacks", shape(page) == shape(agent) and alike(dry, real) and same,
              (shape(page), shape(agent)))
    finally:
        server_mod.CONFIG_PATH, server_mod.ROOT_OVERRIDE, server_mod.STATE_PATH, server_mod.STATE_MEMORY = kept
