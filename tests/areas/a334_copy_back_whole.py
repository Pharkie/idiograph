"""Area 334: a shared copy's boards coming back whole and chosen (copyback, Adam, 6 November 2026, after a tester's
copy of 11 boards came back with 42 of its cards unplaced and Add boards that could not be pressed). A send
carries its sender's Your name, so the file names whose copy it is, and `project boards-in` takes it when
--from-name is not given. Every card of a board brought in keeps its place: matched by its words first, a
statement moved by a removal before it in its passage found on its row, then by its key, a statement reworded
since the copy was sent linked to his and showing his wording now, and else placed in the copy's wording as no
longer in the project, a removed statement whose key now holds another, and the other analyst's own added at a
key that holds one of his. Only the boards chosen come in, by participant and name. MCP and the command line
answer alike, and Open a shared copy's card, its own code run in node on the op's dry run, fills the name from
the file, ticks every board, says what is missing beside a button that cannot be pressed and sends the boards
ticked.

The fixtures are invented: a project on fishing at night, one made-up participant."""
from __future__ import annotations

import json
import shutil
import zipfile
from pathlib import Path

import openpyxl

from . import support
from .support import check, skip


def make_workbook(root: Path, folder: str, speaker: str) -> Path:
    """A made-up participant's annotated workbook: five statements on four rows, two of them sharing a row."""
    import workbook as wb_mod
    case = root / folder
    (case / "Source").mkdir(parents=True)
    raw = openpyxl.Workbook()
    first = raw.active
    first.title = "Initial"
    first.append(["Name", "Timestamp", "Transcript"])
    first.append(["Interviewer", "00:00:04", "What is it like to fish at night?"])
    first.append([speaker, "00:00:09", "The water goes black and the float is all there is."])
    first.append(["Interviewer", "00:00:20", "And the waiting?"])
    first.append([speaker, "00:00:26", "Hours go by, I lose my name out there, I am only watching."])
    first.append(["Interviewer", "00:00:40", "And going home?"])
    first.append([speaker, "00:00:46", "Packing up at dawn feels like waking."])
    first.append(["Interviewer", "00:00:58", "Anything else?"])
    first.append([speaker, "00:01:04", "The cold gets in the hands first."])
    source = case / "Source" / f"{folder} - interview.xlsx"
    raw.save(source)
    book = wb_mod.create_from_source(source, case / f"{folder} - EN & ES.xlsx")
    for row, said in ((3, ["Narrowing the world to the float"]),
                      (5, ["Losing the self in the long wait", "Becoming only the watching"]),
                      (7, ["Leaving the night as waking from it"]), (9, ["Feeling the cold first in the hands"])):
        set_statements(book, row, said)
    return book


def set_statements(book: Path, row: int, said: list[str]) -> None:
    """A row's statements written as an analyst's edit leaves them, a blank line between two."""
    import workbook as wb_mod
    wb = openpyxl.load_workbook(book, rich_text=True)
    ws = wb.worksheets[0]
    ws.cell(row, wb_mod.detect_columns(ws)["es"]).value = wb_mod.join_entries(said)
    wb.save(book)


# the card's stand-ins: elements by id, the ticks read from the HTML the card writes, and what it calls
HARNESS = r"""
// escaped as the page's own are, and an attribute read back as a browser reads it, a character no attribute
// holds, NUL, coming back as U+FFFD as a browser's parser gives it
const esc = (s) => String(s).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
const escAttr = (s) => esc(s).replace(/"/g, '&quot;');
const unattr = (s) => s.replace(/\u0000/g, '�').replace(/&quot;/g, '"').replace(/&lt;/g, '<').replace(/&gt;/g, '>')
  .replace(/&amp;/g, '&');
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
const state = () => ({ who: el('cb-who').value, go: el('cb-go').textContent, disabled: el('cb-go').disabled,
  need: el('cb-need').hidden ? '' : el('cb-need').textContent, as: el('cb-as').hidden ? '' : el('cb-as').textContent,
  all: el('cb-all').checked, some: el('cb-all').indeterminate, ticked: rows.inputs.filter((b) => b.checked).length,
  lines: [...rows.html.matchAll(/<p class="cb-line">([^<]*)<\/p>/g)].map((m) => m[1]),
  heads: [...rows.html.matchAll(/<p class="cb-p">([^<]*)<\/p>/g)].map((m) => m[1]),
  labels: [...rows.html.matchAll(/<span>([^<]*)<\/span><\/label>/g)].map((m) => m[1]) });
(async () => {
  const out = {};
  out.opened = await cbOpen({ returning: { root: 'r', name: 'Night fishing' } }, { file: '/x/Back.idiograph' });
  out.open = state();
  // two boards unticked: the button counts the one left
  for (const i of [1, 2]) { rows.inputs[i].checked = false; cbTick(tickEvent(rows.inputs[i])); }
  out.two_off = state();
  await cbGo();
  out.body = sent[sent.length - 1];
  // the card again, every board unticked by the tick for all of them
  await cbOpen({ returning: { root: 'r', name: 'Night fishing' } }, { file: '/x/Back.idiograph' });
  el('cb-all').checked = false;
  cbTick(tickEvent(el('cb-all')));
  out.none = state();
  rows.inputs[0].checked = true;
  cbTick(tickEvent(rows.inputs[0]));
  el('cb-who').value = '';
  cbDraw();
  out.nameless = state();
  el('cb-all').checked = false;
  cbTick(tickEvent(el('cb-all')));
  out.both = state();
  el('cb-who').value = 'Curt';
  el('cb-all').checked = true;
  cbTick(tickEvent(el('cb-all')));
  out.again = state();
  console.log(JSON.stringify(out));
})().catch((err) => { console.error(err.stack); process.exit(1); });
"""


def test_copy_back_whole(scratch: Path):
    print("\n334. A shared copy's boards come back whole and chosen: every card in its place, matched by its words, then "
          "its key, the name from the file, and Open a shared copy's card ticking and saying what is missing")
    import cli
    import mcp_server
    import project_pack
    import server as server_mod
    import themes
    import idiograph_routes as routes

    base = scratch / "copyback-334"
    shutil.rmtree(base, ignore_errors=True)
    root = base / "Night fishing"
    root.mkdir(parents=True)
    (root / server_mod.PROJECT_FILE).write_text(json.dumps({
        "name": "Night fishing", "research_question": "How do people live fishing at night?",
        "agents": {"allowed": True, "at": "2026-11-06T09:00:00+00:00"}}), encoding="utf-8")
    book = make_workbook(root, "P1 - Orwin", "Orwin")
    config_file = base / "config-334.json"
    config_file.write_text(json.dumps({"projects": [{"root": str(root)}], "interviewer": "Interviewer", "corpus": "",
                                       "gravity_reference": "", "corpus_exclude": []}), encoding="utf-8")
    curt_config = base / "curt-334.json"
    curt_config.write_text(json.dumps({"projects": [], "interviewer": "Interviewer", "your_name": "Curt", "corpus": "",
                                       "gravity_reference": "", "corpus_exclude": []}), encoding="utf-8")
    out_dir, curt_into = base / "out", base / "curt"
    for d in (out_dir, curt_into):
        d.mkdir()

    def run(cfg, *args):
        return cli.run(["--config", str(cfg), *args])

    def run_json(cfg, *args):
        code, out, err = run(cfg, "--json", *args)
        got = support.plain(json.loads(out)) if out.strip() else {}
        return code, (got if code == 0 else {}), err + (got.get("error", "") if code != 0 else "")

    def head_of(file: Path) -> dict:
        with zipfile.ZipFile(file) as zf:
            return json.loads(zf.read(project_pack.MANIFEST))

    def plan(name: str, pets: list) -> Path:
        path = base / f"{name}.json"
        path.write_text(json.dumps({"pets": [{"title": t, "members": m} for t, m in pets]}), encoding="utf-8")
        return path

    kept = (server_mod.CONFIG_PATH, server_mod.ROOT_OVERRIDE, server_mod.STATE_MEMORY)
    try:
        code, _, err = run(config_file, "--root", str(root), "board", "new", "Orwin",
                           "--from", str(plan("his", [("At the float", ["S1"])])), "--note", "His board", "--tool", "Claude Code")
        check("334: his own board for the fixture", code == 0, err)
        sent = out_dir / "Night fishing.idiograph"
        code, _, err = run(config_file, "--root", str(root), "project", "send", "--to", str(sent), "--participant", "Orwin", "--blind")
        check("334: a send with no Your name in Settings names no sender", code == 0 and "from" not in head_of(sent), err)

        # Curt's copy: he adds a statement of his own to the dawn passage and makes three boards
        code, _, err = run(curt_config, "project", "open-copy", str(sent), "--into", str(curt_into))
        copy = curt_into / "Night fishing"
        c_book = copy / "P1 - Orwin" / "P1 - Orwin - EN & ES.xlsx"
        set_statements(c_book, 7, ["Leaving the night as waking from it", "Hearing the reel click as a clock"])
        boards = [("R2 Initial Grouping", [("Narrowing to the float", ["S1", "S2"]), ("Waking from the night", ["S3", "S4", "S5"])]),
                  ("R1 Clusters", [("Everything at once", ["S1", "S2", "S3", "S4", "S5", "S6"])]),
                  ("R2 Second pass", [("All watching", ["S1", "S2", "S3"]), ("Cold and dawn", ["S4", "S6"])])]
        made = []
        for i, (name, pets) in enumerate(boards, start=1):
            made.append(run(curt_config, "--root", str(copy), "board", "new", "Orwin", "--from", str(plan(f"curt{i}", pets)),
                            "--note", "Curt's grouping", "--tool", "Claude Code"))
            made.append(run(curt_config, "--root", str(copy), "board", "rename", "Orwin", f"Board {i}", name,
                            "--note", "Curt's name", "--tool", "Claude Code"))
        back = out_dir / "Back from Curt.idiograph"
        made.append(run(curt_config, "--root", str(copy), "project", "send", "--to", str(back)))
        check("334: Curt's copy opened, a statement of his added, three boards made and named, and sent back",
              code == 0 and all(c == 0 for c, _, _ in made) and back.is_file(), err + " ".join(e for _, _, e in made))
        check("334: the file sent back carries its sender's Your name", head_of(back).get("from") == "Curt",
              json.dumps({k: v for k, v in head_of(back).items() if k != "files"})[:300])

        # meanwhile he removes the first statement of the waiting passage, rewords the dawn one and adds one of his own
        set_statements(book, 5, ["Becoming only the watching"])
        set_statements(book, 7, ["Leaving the night as waking into the day", "Hurrying home before the light"])

        # 1. the dry run with no name given takes the file's, every board named by its own name in the copy
        server_mod.CONFIG_PATH, server_mod.ROOT_OVERRIDE = config_file, None
        dry = routes.boards_in(root, back, dry_run=True)
        got = {b["from"]: b for p in dry["participants"] for b in p["boards"]}
        first = got.get("R2 Initial Grouping", {})
        day = routes.day_said(dry.get("sent") or "")
        check("334: with no name given the dry run takes the file's, whose copy and each board's name saying Curt",
              dry.get("who") == "Curt" and dry.get("sender") == "Curt"
              and first.get("name") == f"Curt's R2 Initial Grouping, {day}" and len(got) == 3, json.dumps(dry)[:500])
        by = {s["key"]: s for s in first.get("not_matched", [])}
        check("334: matched by words first, a statement moved up its passage by a removal found there, then by key, "
              "the reworded one linked in his wording, the removed one and Curt's own placed in Curt's",
              first.get("statements") == 6 and first.get("matched") == 3 and first.get("by_key") == 1
              and first.get("copy_words") == 2
              and by.get("Initial:7:0", {}).get("wording") == "yours" and by["Initial:7:0"].get("kind") == "edited"
              and by["Initial:7:0"].get("now") == "Leaving the night as waking into the day"
              and by.get("Initial:5:0", {}).get("wording") == "copy" and by["Initial:5:0"].get("kind") == "gone"
              and by.get("Initial:7:1", {}).get("wording") == "copy" and by["Initial:7:1"].get("kind") == "own"
              and set(by) == {"Initial:5:0", "Initial:7:0", "Initial:7:1"}, json.dumps(first)[:700])

        # 2. two of the three boards chosen, by participant and name, brought in with the name from the file
        before = themes.load(book)
        done = routes.api_boards_in({"root": routes.project_id(root), "file": str(back), "from_name": "",
                                     "boards": [{"participant": "P1 - Orwin", "board": "R2 Initial Grouping"},
                                                {"participant": "P1 - Orwin", "board": "R2 Second pass"}]})
        data = themes.load(book)
        names = [b["name"] for b in data["boards"]]
        check("334: only the boards ticked come in, named as Curt's, after his own, not current",
              names == ["Board 1", f"Curt's R2 Initial Grouping, {day}", f"Curt's R2 Second pass, {day}"]
              and data.get("current") == before.get("current") and done.get("who") == "Curt", json.dumps(names))
        new = next((b for b in data["boards"] if b["name"].startswith("Curt's R2 Initial")), {})
        groups = {g["label"]: set(g["members"]) for g in new.get("groups", [])}
        check("334: every card keeps its PET, the statement moved up its passage at its new key, the removed one and "
              "Curt's own moved past their rows",
              groups == {"Narrowing to the float": {"Initial:3:0", "Initial:5:2"},
                         "Waking from the night": {"Initial:5:0", "Initial:7:0", "Initial:7:2"}}, str(groups))
        read = themes.read_cards(book)
        drawn = {c["key"]: c for c in themes.merge(read["cards"], new, read["quotes"])["cards"]}
        check("334: on his canvas the reworded card shows his wording now, the copy's kept as what it read",
              drawn["Initial:7:0"]["text"] == "Leaving the night as waking into the day" and drawn["Initial:7:0"].get("changed")
              and drawn["Initial:7:0"].get("stored") == "Leaving the night as waking from it", json.dumps(drawn["Initial:7:0"]))
        check("334: the removed statement and Curt's own are placed in Curt's wording, marked no longer in the workbook",
              drawn["Initial:5:2"].get("missing") and drawn["Initial:5:2"]["text"] == "Losing the self in the long wait"
              and drawn["Initial:7:2"].get("missing") and drawn["Initial:7:2"]["text"] == "Hearing the reel click as a clock"
              and drawn["Initial:5:0"]["text"] == "Becoming only the watching" and not drawn["Initial:5:0"].get("changed"),
              json.dumps({k: drawn[k] for k in ("Initial:5:2", "Initial:7:2", "Initial:5:0")}))
        check("334: his own statement at the key Curt added at waits under Not placed, never taken by Curt's card",
              drawn["Initial:7:1"]["text"] == "Hurrying home before the light" and drawn["Initial:7:1"].get("new")
              and "Initial:7:1" not in {m for g in new["groups"] for m in g["members"]}, json.dumps(drawn["Initial:7:1"]))
        check("334: the note says whose copy and how many match, then the copy's own note",
              new.get("note", "").startswith(f"Curt's copy, sent {day}: 3 statements as sent, "
                                             "1 reworded since, 1 removed since, 1 of Curt's own.\n"),
              new.get("note", ""))

        # 3. the command line takes the file's name too and says each card's wording, and MCP answers alike
        code, said, err = run(config_file, "--root", str(root), "project", "boards-in", str(back), "--dry-run")
        check("334: the command line's dry run takes the file's name and says how each card comes in",
              code == 0 and "Whose copy: Curt, the name the file carries." in said and "R1 Clusters as Curt's R1 Clusters" in said
              and "In this project's wording, linked to its statement by the key:" in said
              and "Initial:7:0 \"Leaving the night as waking from it\", here \"Leaving the night as waking into the day\"" in said
              and "In the copy's wording, as no longer in this project:" in said, said + err)
        code, came, err = run_json(config_file, "--root", str(root), "project", "boards-in", str(back), "--board", "R1 Clusters",
                                   "--note", "Bring Curt's clusters in", "--tool", "Claude Code")
        check("334: --board alone, with no --from-name, brings that board in named as Curt's",
              code == 0 and [b["name"] for p in came.get("participants", []) for b in p["boards"]] == [f"Curt's R1 Clusters, {day}"],
              err + json.dumps(came)[:300])
        mcp = mcp_server.Server(root=str(root), config=str(config_file))
        res = mcp.call(mcp.by_name["project_boards_in"], {"file": str(back), "dry_run": True, "request": "Look first"})
        mcp_said = support.plain(res.get("structuredContent") or {}) if not res.get("isError") else {}
        check("334: MCP's project_boards_in with no from_name takes the file's name, as the command line does",
              mcp_said.get("who") == "Curt" and mcp_said.get("sender") == "Curt", json.dumps(res)[:300])

        # 4. Open a shared copy's card, its own code in node on the op's dry run of a fresh project's copy
        node = shutil.which("node")
        if not node:
            return skip("334: the card in node", "no node on this machine")
        fresh = base / "Fresh" / "Night fishing"
        fresh.parent.mkdir()
        shutil.copytree(root, fresh, ignore=shutil.ignore_patterns("Working"))
        (fresh / "P1 - Orwin" / "Working").mkdir()
        card_dry = routes.boards_in(fresh, back, dry_run=True)
        js = support.source("apps/idiograph/static/distil.js").read_text(encoding="utf-8")
        start = js.find("/* Open a shared copy's card for a copy of one of his projects coming back")
        end = js.find("/* the card's keys: Esc shuts it, Enter presses its button")
        shown = next(line for line in js.splitlines() if line.startswith("const caseShown = "))
        if start < 0 or end < start:
            return check("334: the card's code is found in distil.js", False, "its comments not found")
        script = (support.i18n_js() + shown + "\n" + js[start:end]
                  + HARNESS.replace("JSON.parse(process.argv[2])", json.dumps({"dry": card_dry})))
        ran = support.run_node(script, base, "card-334.js", timeout=60)
        if ran.returncode != 0:
            return check("334: the card's code runs in node", False, ran.stderr.strip()[:800])
        out = json.loads(ran.stdout)
        o = out["open"]
        check("334: the card opens with the name from the file, every board ticked under its participant by its own name, "
              "and Add 3 boards ready",
              out["opened"] is True and o["who"] == "Curt" and o["ticked"] == 3 and o["all"] and not o["some"]
              and o["go"] == "Add 3 boards" and not o["disabled"] and not o["need"] and o["heads"] == ["P1 Orwin"]
              and sorted(o["labels"]) == ["R1 Clusters", "R2 Initial Grouping", "R2 Second pass"]
              and o["as"].startswith("Comes in as: Curt's "), json.dumps(o))
        check("334: once under the participant's boards, how its statements came, in plain words",
              o["lines"] == ["1 of these statements you have reworded since you sent the copy, and 1 you have removed. "
                             "Curt added 1 in the copy. They keep their places on these boards, in your current wording, "
                             "and the rest in Curt's."], json.dumps(o["lines"]))
        t = out["two_off"]
        check("334: two boards unticked, the button counts the one left, the tick for all of them half set, and Add "
              "sends that board alone with the name",
              t["go"] == "Add 1 board" and not t["disabled"] and t["ticked"] == 1 and t["some"]
              and out["body"].get("from_name") == "Curt"
              and out["body"].get("boards") == [{"participant": "P1 - Orwin", "board": o["labels"][0], "timepoint": 1}],
              json.dumps(out["body"]))
        check("334: with no board ticked, no name, or neither, the button cannot be pressed and the line beside it says why",
              out["none"]["disabled"] and out["none"]["need"] == "Tick a board." and out["none"]["go"] == "Add 0 boards"
              and out["nameless"]["disabled"] and out["nameless"]["need"] == "Type a name." and not out["nameless"]["as"]
              and out["both"]["disabled"] and out["both"]["need"] == "Tick a board and type a name."
              and not out["again"]["disabled"] and not out["again"]["need"] and out["again"]["ticked"] == 3,
              json.dumps({k: out[k] for k in ("none", "nameless", "both", "again")}))
    finally:
        server_mod.CONFIG_PATH, server_mod.ROOT_OVERRIDE, server_mod.STATE_MEMORY = kept
