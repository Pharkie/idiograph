"""Area 335: a shared copy coming back with the sender's own boards as he sent them (copyback2, 8 November 2026,
after a tester's copy came back offering the sender's own Board 1 as the tester's, once he had reworded a statement
on it). A send records the places print of each board it carries and the copy keeps it, so a board the tester never
touched is the sender's own whatever he has done to his own since, and a copy that kept no prints finds it by his
boards and their History. It stays out unless chosen by name, and one the tester moved a card on comes in as the
tester's. The note of a board brought in says whose copy, when it was sent and how its statements came, and
`board note` rewrites it. Open a shared copy's card, in node on the op's dry run, leaves the sender's
own out of its list with a line under the participant (Adam's option A, 8 November 2026). And three faults found on
f17e8ac (bugcheck): a board unticked at one timepoint came in with the same name at another, a participant found
by pseudonym alone took no board on Add, and MCP took boards by name alone where the card chooses participant,
board and timepoint.

The fixtures are invented: a project on mending kites, made-up participants."""
from __future__ import annotations

import base64
import json
import shutil
import zipfile
from pathlib import Path

from . import support
from .support import check, skip
from .a334_copy_back_whole import make_workbook, set_statements

# the card's stand-ins, as area 334's
HARNESS = r"""
const esc = (s) => String(s).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
const escAttr = (s) => esc(s).replace(/"/g, '&quot;');
const unattr = (s) => s.replace(/&quot;/g, '"').replace(/&lt;/g, '<').replace(/&gt;/g, '>').replace(/&amp;/g, '&');
const els = {};
const el = (id) => els[id] || (els[id] = { id, value: '', checked: false, indeterminate: false, hidden: false, disabled: false,
  textContent: '', dataset: {}, focus() {}, isConnected: true });
const rows = el('cb-rows');
rows.inputs = [];
Object.defineProperty(rows, 'innerHTML', { set(html) {
  rows.html = html;
  rows.inputs = [...html.matchAll(/<input [^>]*>/g)].map((m) => ({ dataset: { cb: unattr(/data-cb="([^"]*)"/.exec(m[0])[1]) },
    checked: / checked/.test(m[0]), type: 'checkbox', focus() {} }));
}, get() { return rows.html || ''; } });
rows.querySelectorAll = () => rows.inputs;
const $ = (id) => el(id);
const document = { activeElement: null };
const show = (id) => { el(id).hidden = false; };
const hide = (id) => { el(id).hidden = true; };
const say = () => {}, needsRestart = () => false, RESTART_LINE = '';
const sentInto = () => {}, loadLibrary = async () => {}, openThemes = () => {}, navGo = async () => {}, thVmenu = () => {};
const given = JSON.parse(process.argv[2]);
const sent = [];
const api = async (path, body) => { sent.push(JSON.parse(JSON.stringify(body))); return JSON.parse(JSON.stringify(given.dry)); };
const tickEvent = (box) => ({ target: { closest: () => box } });
const state = () => ({ go: el('cb-go').textContent, disabled: el('cb-go').disabled,
  ticks: [...rows.html.matchAll(/<label class="cb-tick"><input [^>]*?( checked)?>(?:<span>([^<]*)<\/span>)/g)]
    .map((m) => ({ name: m[2], on: !!m[1] })),
  lines: [...rows.html.matchAll(/<p class="cb-line[^"]*">([^<]*)<\/p>/g)].map((m) => m[1]) });
(async () => {
  const out = {};
  await cbOpen({ returning: { root: 'r', name: 'Kite mending' } }, { file: '/x/Back.idiograph' });
  out.a = state();
  await cbGo();
  out.a.body = sent[sent.length - 1];
  console.log(JSON.stringify(out));
})().catch((err) => { console.error(err.stack); process.exit(1); });
"""

T1_TEXT = ("Kit: [00:00:03] What did you expect of the first kite?\nWren: [00:00:08] That it would fly first time.\n"
           "Kit: [00:00:40] And the string?\nWren: [00:01:55] I had not thought about the string.\n")
T2_TEXT = ("Kit: [00:00:02] How is it now?\nWren: [00:00:06] I patch the sail before I trust the wind.\n"
           "Kit: [00:00:30] Why patch?\nWren: [00:02:33] A small tear grows in a gust.\n")


def test_copy_back_as_sent(scratch: Path):
    print("\n335. A shared copy coming back with the sender's own boards as sent: found by where they put their cards "
          "whatever he has done since, left out unless chosen, the tester's own offered, the note, board note, the "
          "card leaving it out, and choices by participant, board and timepoint")
    import cli
    import mcp_server
    import project_pack
    import server as server_mod
    import themes
    import workbook as wb_mod
    import idiograph_routes as routes

    base = scratch / "copyback-335"
    shutil.rmtree(base, ignore_errors=True)
    root = base / "Kite mending"
    root.mkdir(parents=True)
    (root / server_mod.PROJECT_FILE).write_text(json.dumps({
        "name": "Kite mending", "research_question": "How do people live mending kites?",
        "agents": {"allowed": True, "at": "2026-11-08T09:00:00+00:00"}}), encoding="utf-8")
    book = make_workbook(root, "P1 - Hollis", "Hollis")
    config_file = base / "config-335.json"
    config_file.write_text(json.dumps({"projects": [{"root": str(root)}], "interviewer": "Interviewer", "corpus": "",
                                       "gravity_reference": "", "corpus_exclude": []}), encoding="utf-8")
    curt_config = base / "curt-335.json"
    curt_config.write_text(json.dumps({"projects": [], "interviewer": "Interviewer", "your_name": "Curt", "corpus": "",
                                       "gravity_reference": "", "corpus_exclude": []}), encoding="utf-8")
    out_dir, curt_into = base / "out", base / "curt"
    for d in (out_dir, curt_into):
        d.mkdir()

    def run(cfg, *args):
        return cli.run(["--config", str(cfg), *[str(a) for a in args]])

    def run_json(cfg, *args):
        code, out, err = run(cfg, "--json", *args)
        got = support.plain(json.loads(out)) if out.strip() else {}
        return code, (got if code == 0 else {}), err + (got.get("error", "") if code != 0 else "")

    def plan(name: str, pets: list) -> Path:
        path = base / f"{name}.json"
        path.write_text(json.dumps({"pets": [{"title": t, "members": m} for t, m in pets]}), encoding="utf-8")
        return path

    def ops(name: str, listed: list) -> Path:
        path = base / f"{name}.json"
        path.write_text(json.dumps(listed), encoding="utf-8")
        return path

    def group_id(cbook: Path, board: str, label: str) -> str:
        data = themes.load(cbook)
        b = next(x for x in data["boards"] if x["name"] == board)
        return next(g["id"] for g in b["groups"] if g["label"] == label)

    def by_name(dry: dict, key: str) -> dict:
        return {b["from"]: b for p in dry["participants"] for b in p.get(key, [])}

    kept = (server_mod.CONFIG_PATH, server_mod.ROOT_OVERRIDE, server_mod.STATE_PATH, server_mod.STATE_MEMORY)
    try:
        server_mod.CONFIG_PATH, server_mod.ROOT_OVERRIDE = config_file, None
        made = [run(config_file, "--root", root, "board", "new", "Hollis", "--from",
                    plan("his1", [("At the float", ["S1", "S2"]), ("Waking", ["S3", "S4", "S5"])]),
                    "--note", "His board", "--tool", "Claude Code"),
                run(config_file, "--root", root, "board", "new", "Hollis", "--from",
                    plan("his2", [("Watching", ["S1", "S2", "S3"]), ("Leaving", ["S4", "S5"])]),
                    "--note", "His second", "--tool", "Claude Code")]
        sent = out_dir / "Kite mending.idiograph"
        made.append(run(config_file, "--root", root, "project", "send", "--to", sent))
        with zipfile.ZipFile(sent) as zf:
            head = json.loads(zf.read(project_pack.MANIFEST))
        his = [themes.places_print(b) for b in themes.load(book)["boards"]]
        check("335: a send records where each board it carries puts its cards, by participant",
              all(c == 0 for c, _, _ in made) and head.get("boards") == {"P1 - Hollis": his} and len(set(his)) == 2,
              " ".join(e for _, _, e in made) + json.dumps(head.get("boards")))

        # Curt's copy: his own board 2 with one card moved, a new board of his, and Board 1 left as it came
        made = [run(curt_config, "project", "open-copy", sent, "--into", curt_into)]
        copy = curt_into / "Kite mending"
        c_book = copy / "P1 - Hollis" / "P1 - Hollis - EN & ES.xlsx"
        kept_copy = json.loads((copy / server_mod.PROJECT_FILE).read_text(encoding="utf-8")).get("copy_of", {})
        made.append(run(curt_config, "--root", copy, "board", "apply", "Hollis", "Board 2", "--ops",
                        ops("move1", [{"op": "move", "items": ["S5"], "to": group_id(c_book, "Board 2", "Watching")}]),
                        "--note", "One card moved", "--tool", "Claude Code"))
        made.append(run(curt_config, "--root", copy, "board", "new", "Hollis", "--from",
                        plan("curt", [("Cold", ["S5"]), ("The rest", ["S1", "S2", "S3", "S4"])]),
                        "--note", "Curt's grouping", "--tool", "Claude Code"))
        made.append(run(curt_config, "--root", copy, "board", "rename", "Hollis", "Board 3", "R2 Grouping",
                        "--note", "Curt's name", "--tool", "Claude Code"))
        back = out_dir / "Back from Curt.idiograph"
        made.append(run(curt_config, "--root", copy, "project", "send", "--to", back))
        check("335: the copy keeps the prints as sent, and Curt moves one card on Board 2, makes a board and sends it back",
              all(c == 0 for c, _, _ in made) and kept_copy.get("boards") == {"P1 - Hollis": his} and back.is_file(),
              " ".join(e for _, _, e in made))

        # meanwhile he rewords a statement on his own boards and moves a card on his own Board 1
        set_statements(book, 9, ["Feeling the cold in the hands before anything"])
        code, _, err = run(config_file, "--root", root, "board", "apply", "Hollis", "Board 1", "--ops",
                           ops("move2", [{"op": "move", "items": ["S3"], "to": group_id(book, "Board 1", "At the float")}]),
                           "--note", "His own change", "--tool", "Claude Code")
        check("335: he edits his own Board 1 since", code == 0, err)
        moved_root = base / "Moved" / "Kite mending"
        shutil.copytree(root, moved_root)

        # 1. the dry run: Board 1 his own as sent, whatever he has done to it, Board 2 and R2 Grouping Curt's
        dry = routes.boards_in(root, back, dry_run=True)
        offered, own = by_name(dry, "boards"), by_name(dry, "as_sent")
        check("335: a board Curt left as sent is found as his own after he edits his own, and is left out",
              sorted(own) == ["Board 1"] and own["Board 1"].get("as_sent") is True
              and sorted(offered) == ["Board 2", "R2 Grouping"] and not dry["participants"][0]["already"],
              json.dumps({"own": sorted(own), "offered": sorted(offered), "already": dry["participants"][0]["already"]}))
        check("335: a board Curt moved one card on is offered as his, not as the sender's own",
              "as_sent" not in offered["Board 2"], json.dumps(offered["Board 2"])[:300])

        # 2. a copy from before the prints: his boards and their History find it the same
        old = out_dir / "Back from Curt, old.idiograph"
        with zipfile.ZipFile(back) as zin, zipfile.ZipFile(old, "w", zipfile.ZIP_DEFLATED) as zout:
            for item in zin.infolist():
                data = zin.read(item.filename)
                if item.filename == project_pack.TOP + server_mod.PROJECT_FILE:
                    proj = json.loads(data)
                    proj["copy_of"].pop("boards", None)
                    data = json.dumps(proj).encode("utf-8")
                    listed = item.filename
                zout.writestr(item, data)
        # the list's print of the project file, changed with it, so the file arrives whole
        with zipfile.ZipFile(old) as zf:
            files = {n: zf.read(n) for n in zf.namelist()}
        manifest = json.loads(files[project_pack.MANIFEST])
        import hashlib
        for entry in manifest["files"]:
            if project_pack.TOP + entry["path"] == listed:
                entry["sha256"] = hashlib.sha256(files[listed]).hexdigest()
                entry["bytes"] = len(files[listed])
        files[project_pack.MANIFEST] = json.dumps(manifest).encode("utf-8")
        with zipfile.ZipFile(old, "w", zipfile.ZIP_DEFLATED) as zf:
            for n, data in files.items():
                zf.writestr(n, data)
        dry_old = routes.boards_in(root, old, dry_run=True)
        check("335: a copy that kept no prints finds his own board as sent by his boards' History",
              sorted(by_name(dry_old, "as_sent")) == ["Board 1"] and sorted(by_name(dry_old, "boards")) == ["Board 2", "R2 Grouping"],
              json.dumps({k: sorted(by_name(dry_old, k)) for k in ("as_sent", "boards")}))

        # 2b. MCP chooses as the card does: participant, board and timepoint
        mcp = mcp_server.Server(root=str(root), config=str(config_file))
        res = mcp.call(mcp.by_name["project_boards_in"], {"file": str(back), "dry_run": True, "request": "Look first",
                                                           "boards": [{"participant": "Hollis", "board": "Board 1", "timepoint": 1}]})
        mcp_said = support.plain(res.get("structuredContent") or {}) if not res.get("isError") else {}
        check("335: MCP's project_boards_in takes a participant, board and timepoint, as the card sends them",
              [b["from"] for p in mcp_said.get("participants", []) for b in p["boards"]] == ["Board 1"], json.dumps(res)[:400])

        # 3. how each board's statements came, and the note it is brought in with
        day = routes.day_said(dry.get("sent") or "")
        came = offered["R2 Grouping"].get("came")
        check("335: the dry run says how each board's statements came: as sent, reworded since, removed since, Curt's own",
              came == {"statements": 5, "as_sent": 4, "reworded": 1, "removed": 0, "own": 0}, json.dumps(came))
        done = routes.boards_in(root, back, from_name="", dry_run=False, request="Bring Curt's boards in")
        names = [b["name"] for b in themes.load(book)["boards"]]
        check("335: brought in with no choice, his own as sent stays out and Curt's two come in",
              names == ["Board 1", "Board 2", f"Curt's Board 2, {day}", f"Curt's R2 Grouping, {day}"]
              and [b["from"] for p in done["participants"] for b in p["as_sent"]] == ["Board 1"], json.dumps(names))
        new = next(b for b in themes.load(book)["boards"] if b["name"] == f"Curt's R2 Grouping, {day}")
        check("335: its note says whose copy, when it was sent and how its statements came, then the copy's own note",
              new.get("note", "").startswith(routes.board_in_note("Curt's", day, came) + "\nMade by Claude Code")
              and new["note"].startswith(f"Curt's copy, sent {day}: 4 statements as sent, 1 reworded since."),
              new.get("note", ""))
        code, came_in, err = run_json(config_file, "--root", root, "project", "boards-in", back, "--board", "Board 1",
                                      "--note", "His own back too", "--tool", "Claude Code")
        got = [b for p in came_in.get("participants", []) for b in p["boards"]]
        check("335: his own as sent comes in when --board names it, marked so",
              code == 0 and [b["from"] for b in got] == ["Board 1"] and got[0].get("as_sent") is True, err + json.dumps(got)[:300])
        code, said, err = run(config_file, "--root", root, "project", "boards-in", old, "--dry-run")
        check("335: the command line's dry run says which boards are his own as sent",
              code == 0 and "P1 - Hollis: your own as you sent them, left out: Board 1." in said, said + err)

        # 4. a board's note rewritten through the API, as Claude will rewrite the old lines
        target = f"Curt's R2 Grouping, {day}"
        before = themes.load(book)
        code, _, err = run(config_file, "--root", root, "board", "note", "Hollis", target, "A note rewritten", "--dry-run")
        check("335: board note's dry run writes nothing", code == 0 and themes.load(book) == before, err)
        code, _, err = run(config_file, "--root", root, "board", "note", "Hollis", target, "A note rewritten",
                           "--note", "Rewrite the note", "--tool", "Claude Code")
        b = next(x for x in themes.load(book)["boards"] if x["name"] == target)
        check("335: board note rewrites a brought-in board's note, the board kept first in its History",
              code == 0 and b.get("note") == "A note rewritten" and len(themes.history_of(b)) == 2, err)
        res = mcp.call(mcp.by_name["board_note"], {"case": "Hollis", "board": target, "note": "Again", "dry_run": True,
                                                    "request": "Look first"})
        check("335: MCP's board_note is its twin", not res.get("isError"), json.dumps(res)[:300])

        # 6. a participant found by pseudonym alone takes the boards ticked by the project's label
        old_folder, new_folder = moved_root / "P1 - Hollis", moved_root / "P3 - Hollis"
        old_folder.rename(new_folder)
        moved_book = next(new_folder.glob("*.xlsx"))
        try:
            moved = routes.boards_in(moved_root, back, from_name="Curt",
                                     boards=[{"participant": "P3 - Hollis", "board": "R2 Grouping", "timepoint": 1}])
            moved_names = [b["name"] for b in themes.load(moved_book)["boards"]]
            why = ""
        except Exception as exc:
            moved, moved_names, why = {}, [], str(exc)
        check("335: a participant matched by pseudonym alone takes the board ticked by the project's label",
              moved_names[-1:] == [f"Curt's R2 Grouping, {day}"] and len(moved_names) == 3, why + json.dumps(moved_names))

        # 5. the card, in node on the op's dry run of a fresh copy of the project
        node = shutil.which("node")
        if not node:
            skip("335: the card in node", "no node on this machine")
        else:
            js = support.source("apps/idiograph/static/distil.js").read_text(encoding="utf-8")
            start = js.find("/* Open a shared copy's card for a copy of one of his projects coming back")
            end = js.find("/* the card's keys: Esc shuts it, Enter presses its button")
            shown = next(line for line in js.splitlines() if line.startswith("const caseShown = "))
            # the first dry run, Curt's two boards and his own as sent, as the card first sees the copy
            script = (support.i18n_js() + shown + "\n" + js[start:end]
                      + HARNESS.replace("JSON.parse(process.argv[2])", json.dumps({"dry": dry})))
            ran = support.run_node(script, base, "card-335.js", timeout=60)
            if ran.returncode != 0:
                check("335: the card's code runs in node", False, ran.stderr.strip()[:800])
            else:
                out = json.loads(ran.stdout)
                a = out["a"]
                check("335: his own as sent is left out of the list, a line under the participant says how many, "
                      "and Add sends Curt's two",
                      [t["name"] for t in a["ticks"]] == ["Board 2", "R2 Grouping"] and a["go"] == "Add 2 boards"
                      and a["lines"][-1] == "1 board is your own as you sent it, so it is left out."
                      and [x["board"] for x in a["body"]["boards"]] == ["Board 2", "R2 Grouping"], json.dumps(a))

        # 8. a board unticked at one timepoint stays out though a board of the same name comes in at another
        tp_check(scratch, base, routes, server_mod, themes, wb_mod, cli)
    finally:
        server_mod.CONFIG_PATH, server_mod.ROOT_OVERRIDE, server_mod.STATE_PATH, server_mod.STATE_MEMORY = kept


def tp_check(scratch: Path, base: Path, routes, server_mod, themes, wb_mod, cli) -> None:
    b64 = lambda text: base64.b64encode(text.encode("utf-8")).decode("ascii")

    def row(name, text, who, interview, **more):
        return dict({"name": name, "data": b64(text), "pseudonym": who, "interview": interview,
                     "speakers": {"Kit": "interviewer", who: "participant"}}, **more)

    cfg = base / "tp-config.json"
    cfg.write_text(json.dumps({"projects": [], "interviewer": "Kit", "corpus": "", "gravity_reference": "",
                               "corpus_exclude": []}), encoding="utf-8")
    curt = base / "tp-curt.json"
    curt.write_text(json.dumps({"projects": [], "interviewer": "Kit", "your_name": "Curt", "corpus": "",
                                "gravity_reference": "", "corpus_exclude": []}), encoding="utf-8")
    server_mod.CONFIG_PATH, server_mod.ROOT_OVERRIDE = cfg, None
    server_mod.STATE_PATH, server_mod.STATE_MEMORY = base / "tp-state.json", {"recent": []}
    garden = base / "Kite year"
    garden.mkdir()
    made = routes.api_new_project({"op": "make", "folder": str(garden), "name": "Kite year",
                                   "research_question": "How do newcomers take to mending kites?",
                                   "files": [row("before.txt", T1_TEXT, "Wren", "Before")]})
    rid = made["project"]["id"]
    routes.api_project({"root": rid, "timepoints": [{"label": "T1", "description": ""}, {"label": "T2", "description": ""}]})
    routes.api_project({"root": rid, "agents": True})
    routes.api_add_transcripts({"op": "add", "root": rid, "files": [row("later.txt", T2_TEXT, "Wren", "Later", timepoint=2)]})
    book = garden / "P1 - Wren" / "P1 Wren - EN & ES.xlsx"
    import openpyxl
    wb = openpyxl.load_workbook(book, read_only=True)
    rows = {s: [r for r, v in enumerate(wb[s].iter_rows(min_row=2, max_col=1, values_only=True), start=2)
                if str(v[0] or "").strip() == "Wren"] for s in ("Before", "Later")}
    wb.close()
    wb_mod.save_turn(book, "Before", rows["Before"][0], "Expecting flight at once", "", "")
    wb_mod.save_turn(book, "Before", rows["Before"][1], "Overlooking the string", "", "")
    wb_mod.save_turn(book, "Later", rows["Later"][0], "Patching before trusting", "", "")
    wb_mod.save_turn(book, "Later", rows["Later"][1], "Small tears growing", "", "")
    p = base / "tp-plan.json"
    p.write_text(json.dumps({"pets": [{"title": "All of it", "members": ["S1", "S2"]}]}), encoding="utf-8")
    p2 = base / "tp-plan2.json"
    p2.write_text(json.dumps({"pets": [{"title": "First", "members": ["S1"]}, {"title": "Second", "members": ["S2"]}]}),
                  encoding="utf-8")
    ran = []
    for n in ("1", "2"):
        ran.append(cli.run(["--config", str(cfg), "--root", str(garden), "board", "new", "Wren", "--timepoint", n,
                            "--from", str(p), "--note", "His", "--tool", "Claude Code"]))
    sent, back, into = base / "Kite year.idiograph", base / "Kite year back.idiograph", base / "tp-into"
    into.mkdir()
    ran.append(cli.run(["--config", str(cfg), "--root", str(garden), "project", "send", "--to", str(sent)]))
    ran.append(cli.run(["--config", str(curt), "project", "open-copy", str(sent), "--into", str(into)]))
    copy = into / "Kite year"
    for n in ("1", "2"):
        ran.append(cli.run(["--config", str(curt), "--root", str(copy), "board", "new", "Wren", "--timepoint", n,
                            "--from", str(p2), "--note", "Curt's", "--tool", "Claude Code"]))
    ran.append(cli.run(["--config", str(curt), "--root", str(copy), "project", "send", "--to", str(back)]))
    check("335: a project of two timepoints, his board at each, Curt's Board 2 at each, sent back",
          all(c == 0 for c, _, _ in ran), " ".join(e for _, _, e in ran)[:600])
    with themes.scoped(2):
        t2_before = [b["name"] for b in themes.load(book)["boards"]]
    code, said, err = cli.run(["--config", str(cfg), "--root", str(garden), "project", "boards-in", str(back),
                               "--board-of", "Wren", "Board 2", "T1", "--dry-run", "--json"])
    dry = support.plain(json.loads(said)) if code == 0 else {}
    check("335: --board-of chooses one participant's board at one timepoint, as the card's tick does",
          [(r["timepoint"], b["from"]) for r in dry.get("participants", []) for b in r["boards"]] == [(1, "Board 2")],
          err + said[:400])
    done = routes.boards_in(garden, back, from_name="Curt",
                            boards=[{"participant": "P1 - Wren", "board": "Board 2", "timepoint": 1}])
    t1_names = [b["name"] for b in themes.load(book)["boards"]]
    with themes.scoped(2):
        t2_after = [b["name"] for b in themes.load(book)["boards"]]
    check("335: a board ticked at T1 alone comes in at T1, and its namesake unticked at T2 stays out",
          len(t1_names) == 2 and t1_names[-1].startswith("Curt's Board 2") and t2_after == t2_before
          and [r["timepoint"] for r in done["participants"] if r["boards"]] == [1], json.dumps([t1_names, t2_after]))
