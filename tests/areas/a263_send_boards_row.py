"""Area 263: Share a copy's Boards row (26 October 2026, Adam's option A): one row of radios, Current board
only and All boards, under the card's choice in both its forms, there only when a board file that would go
holds two or more boards, All boards to start. The card's own code runs in node on what /api/send-list
answers for an invented project, its rows drawn from the real list, and the choice it makes goes to the
window's send (/api/send-project) and a browser's download (/project/send), whose files are read back:
Current board only sends each board file with its current board alone, All boards sends them whole.

The fixtures are invented: a project on keeping bees, two made-up participants, Hollis with three boards
(Board 2 the Current board) and Petra with one, and GETs of two boards."""
from __future__ import annotations

import json
import shutil
import subprocess
import zipfile
from pathlib import Path

from . import support
from .a258_send_chosen import make_workbook
from .support import check, skip

# the page's stand-ins: elements by id, the rows' inputs read from the HTML the card writes, and the
# helpers sendProject calls
HARNESS = r"""
const els = {};
const el = (id) => els[id] || (els[id] = { id, checked: false, hidden: false, disabled: false, textContent: '', style: {}, focus() {} });
const rows = el('sc-rows');
rows.inputs = [];
Object.defineProperty(rows, 'innerHTML', { set(html) {
  rows.inputs = [...html.matchAll(/<input [^>]*>/g)].map((m) => ({
    dataset: { i: /data-i="(\d+)"/.exec(m[0])[1], k: /data-k="(\w+)"/.exec(m[0])[1] }, checked: / checked/.test(m[0]) }));
} });
rows.querySelectorAll = (sel) => {
  const k = /data-k="(\w+)"/.exec(sel);
  return k ? rows.inputs.filter((b) => b.dataset.k === k[1] && (!sel.includes(':checked') || b.checked)) : [];
};
const $ = (id) => el(id);
const document = { activeElement: null };
const esc = (s) => String(s), escAttr = (s) => String(s);
const show = (id) => { el(id).hidden = false; };
const hide = (id) => { el(id).hidden = true; };
const say = () => {}, needsRestart = () => false, RESTART_LINE = '';
let LIST = null;
const api = async () => JSON.parse(JSON.stringify(LIST));
const tick = (k, label, on) => {
  const i = SC.list.participants.findIndex((p) => p.label === label);
  rows.inputs.find((b) => b.dataset.k === k && Number(b.dataset.i) === i).checked = on;
};
// the two Boards radios one group, as a page's are: one checked unchecks the other
const radio = {};
for (const [id, other] of [['sc-boards-current', 'sc-boards-all'], ['sc-boards-all', 'sc-boards-current']]) {
  Object.defineProperty(el(id), 'checked', { get: () => radio[id] === true, set: (v) => { radio[id] = !!v; if (v) radio[other] = false; } });
}
const mode = (whole) => { el('sc-whole').checked = whole; el('sc-choose').checked = !whole; };
const pick = (current) => { el('sc-boards-current').checked = current; el('sc-boards-all').checked = !current; };
const lists = JSON.parse(process.argv[2]);
const out = {};
async function open(name, list, whole, then) {
  LIST = list;
  await sendProject('root', 'Keeping bees');
  const start = { shown: !el('sc-boards-below').hidden, all: el('sc-boards-all').checked, current: el('sc-boards-current').checked };
  mode(whole);
  if (then) then();
  scDraw();
  const before = scChoice();
  pick(true);
  scDraw();
  out[name] = { start, shown: !el('sc-boards-below').hidden, before, card: scChoice() };
}
(async () => {
  const many = lists.many, single = lists.single;
  const getsOnly = Object.assign(JSON.parse(JSON.stringify(single)), { gets_boards: many.gets_boards });
  await open('whole', many, true);
  await open('choose', many, false);
  await open('choosePetraAlone', many, false, () => tick('on', 'P1 - Hollis', false));
  await open('chooseHollisNoPets', many, false, () => tick('pets', 'P1 - Hollis', false));
  await open('wholeSingle', single, true);
  await open('wholeGetsOnly', getsOnly, true);
  await open('chooseGetsOnly', getsOnly, false);
  console.log(JSON.stringify(out));
})().catch((err) => { console.error(err.stack); process.exit(1); });
"""


def test_send_boards_row(scratch: Path):
    print("\n263. Share a copy's Boards row: there when a board file going has two or more boards, All boards to start, "
          "the choice reaching the window's send and a browser's download in both forms")
    import cli
    import project_pack
    import server as server_mod
    import idiograph_routes as routes

    node = shutil.which("node")
    if not node:
        return skip("263: the card's Boards row in node", "no node on this machine")
    js = support.source("apps/idiograph/static/distil.js").read_text(encoding="utf-8")
    start, end = js.find("const SC = {"), js.find("/* Share…: the window's save panel")
    if start < 0 or end < start:
        return check("263: Share a copy's card code is found in distil.js", False, "const SC or scGo's comment not found")

    base = scratch / "send-263"
    shutil.rmtree(base, ignore_errors=True)
    root = base / "Keeping bees"
    root.mkdir(parents=True)
    (root / server_mod.PROJECT_FILE).write_text(json.dumps({
        "name": "Keeping bees", "research_question": "How do people live keeping bees?",
        "agents": {"allowed": True, "at": "2026-10-26T10:00:00+00:00"}, "uid": "a263beef0000cafe"}), encoding="utf-8")
    make_workbook(root, "P1 - Hollis", "Hollis")
    make_workbook(root, "P2 - Petra", "Petra")
    config_file = base / "config-263.json"
    config_file.write_text(json.dumps({"projects": [], "interviewer": "Interviewer", "corpus": "",
                                       "gravity_reference": "", "corpus_exclude": []}), encoding="utf-8")
    out_dir = base / "out"
    out_dir.mkdir()
    plan = base / "plan.json"
    plan.write_text(json.dumps({"pets": [{"title": "Smoke and patience", "members": ["S1"]}],
                                "not_placed": {"S2": ""}}), encoding="utf-8")

    def board(*args):
        code, _, err = cli.run(["--config", str(config_file), "--root", str(root), "board", *args, "--tool", "Claude Code"])
        return code == 0, err

    made = [board("new", who, "--from", str(plan), "--note", "A first board") for who in ("Hollis", "Petra")]
    check("263: a board each for the fixture, through the API", all(ok for ok, _ in made), " ".join(e for _, e in made))
    kept = (server_mod.CONFIG_PATH, server_mod.ROOT_OVERRIDE, server_mod.STATE_MEMORY)
    try:
        server_mod.CONFIG_PATH, server_mod.ROOT_OVERRIDE, server_mod.STATE_MEMORY = config_file, None, {"recent": []}
        routes.add_project(root)
        single = routes.send_list(root)
        made = [board("new", "Hollis", "--from", str(plan), "--note", "Another board") for _ in range(2)]
        made.append(board("current", "Hollis", "Board 2", "--note", "Go with Board 2"))
        check("263: Hollis has three boards, Board 2 the Current board", all(ok for ok, _ in made), " ".join(e for _, e in made))
        (root / "idiograph-gets.json").write_text(json.dumps({
            "schema": 1, "cases": {"P1 - Hollis": {}, "P2 - Petra": {}}, "current": "g2", "chosen": "g2",
            "boards": [{"id": "g1", "name": "Board 1", "gets": []}, {"id": "g2", "name": "Board 2", "gets": []}]}),
            encoding="utf-8")
        many = routes.send_list(root)

        script = base / "card-263.js"
        script.write_text(support.i18n_js() + js[start:end] + HARNESS, encoding="utf-8")
        run = subprocess.run([node, str(script), json.dumps({"single": single, "many": many})],
                             capture_output=True, text=True, encoding="utf-8", timeout=120)
        if run.returncode != 0:
            return check("263: the card's code runs in node", False, run.stderr.strip()[:800])
        got = json.loads(run.stdout)
        for name in ("whole", "choose"):
            g = got[name]
            check(f"263: {name}: the Boards row is there, All boards to start, and the card sends all until Current board "
                  "only is chosen",
                  g["shown"] and g["start"]["all"] and not g["start"]["current"] and g["before"]["boards"] == "all"
                  and g["card"]["boards"] == "current", json.dumps(g))
        check("263: Choose participants with Petra alone, her one board, has no Boards row and sends all boards",
              not got["choosePetraAlone"]["shown"] and got["choosePetraAlone"]["card"]["boards"] == "all"
              and got["choosePetraAlone"]["card"]["participants"] == ["P2 - Petra"], json.dumps(got["choosePetraAlone"]))
        check("263: Choose participants with Hollis's PETs unticked has no Boards row and sends all boards",
              not got["chooseHollisNoPets"]["shown"] and got["chooseHollisNoPets"]["card"]["boards"] == "all",
              json.dumps(got["chooseHollisNoPets"]))
        check("263: Whole project with every board file of one board has no Boards row",
              not got["wholeSingle"]["shown"] and got["wholeSingle"]["card"]["boards"] == "all", json.dumps(got["wholeSingle"]))
        check("263: GETs of two boards bring the row to Whole project, never to Choose participants, where the GETs stay out",
              got["wholeGetsOnly"]["shown"] and not got["chooseGetsOnly"]["shown"],
              json.dumps([got["wholeGetsOnly"], got["chooseGetsOnly"]]))

        before = {p.relative_to(root).as_posix(): p.read_bytes() for p in sorted(root.rglob("*")) if p.is_file()}
        themes = "P1 - Hollis/Working/P1 - Hollis - EN & ES.themes.json"

        def boards_in(file: Path) -> tuple:
            with zipfile.ZipFile(file) as zf:
                names = zf.namelist()
                held = json.loads(zf.read(project_pack.TOP + themes))
                gets = (json.loads(zf.read(project_pack.TOP + "idiograph-gets.json"))
                        if project_pack.TOP + "idiograph-gets.json" in names else None)
            return [b["name"] for b in held["boards"]], (None if gets is None else [b["name"] for b in gets["boards"]])

        class Download:
            """A browser's request to the download, its answer kept."""
            def __init__(self):
                import io
                self.wfile, self.status, self.close_connection = io.BytesIO(), None, False
            def send_response(self, code):
                self.status = code
            def send_header(self, *_):
                pass
            def end_headers(self):
                pass
            def _json(self, data, code):
                self.status, self.error = code, data

        want = {("whole", "current"): (["Board 2"], ["Board 2"]), ("whole", "all"): (["Board 1", "Board 2", "Board 3"], ["Board 1", "Board 2"]),
                ("choose", "current"): (["Board 2"], None), ("choose", "all"): (["Board 1", "Board 2", "Board 3"], None)}
        for (name, which), expect in want.items():
            card = got[name]["card"] if which == "current" else got[name]["before"]
            routes.api_send_project({"root": str(root), "to": str(out_dir / f"{name}-{which}"), "card": card})
            window = boards_in(out_dir / f"{name}-{which}.idiograph")
            dl = Download()
            routes.send_zip(dl, {"root": str(root), "card": json.dumps(card)})
            (out_dir / f"{name}-{which}-browser.idiograph").write_bytes(dl.wfile.getvalue())
            browser = boards_in(out_dir / f"{name}-{which}-browser.idiograph") if dl.status == 200 else None
            said = "Current board only" if which == "current" else "All boards"
            check(f"263: {name}, {said}: the window's send and a browser's download both hold Hollis's "
                  f"{', '.join(expect[0])}{'' if expect[1] is None else ' and GETs ' + ', '.join(expect[1])}",
                  window == expect and browser == expect, f"window {window} browser {browser} status {dl.status}")
        after = {p.relative_to(root).as_posix(): p.read_bytes() for p in sorted(root.rglob("*")) if p.is_file()}
        check("263: the project is byte for byte as it was after every send", after == before)
    finally:
        server_mod.CONFIG_PATH, server_mod.ROOT_OVERRIDE, server_mod.STATE_MEMORY = kept
