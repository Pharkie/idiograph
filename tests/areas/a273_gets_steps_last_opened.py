"""Area 273: the steps of the project's GETs open the participant last opened (26 October 2026, getsB, Adam's
option B). The GETs opened from Home's card came through the first participant in case order, so its Experiential
statements and PETs tabs opened them whoever was opened last. The GETs answer now carries `last_opened`, the
participant of the project opened last in the recent list the app already keeps, and in a project of two or
more timepoints the timepoint whose PETs were opened last, kept on that participant's entry. The page's
`gtStepCase` takes it on the GETs or LGETs opened from Home's card, and the GETs opened from a participant's PETs
keep that participant, as before.

The fixtures are invented: a project on learning to row on a river, three made-up participants, and a project of
two timepoints on a first winter of sea swimming, two more."""
from __future__ import annotations

import base64
import json
import shutil
import subprocess
from pathlib import Path

from . import support
from .support import check, skip

ROW = ("Cox: [00:00:03] What was the first outing like?\n{who}: [00:00:08] Cold hands on the oar, and no rhythm.\n"
       "Cox: [00:00:40] And now?\n{who}: [00:02:10] The boat runs on when we stop.\n")
SWIM = ("Cox: [00:00:03] How was the water?\n{who}: [00:00:08] It took my breath before I was in.\n")
LATER = ("Cox: [00:00:02] And in the new year?\n{who}: [00:00:06] I go in slowly now, and talk to it.\n")


def test_gets_steps_last_opened(scratch: Path):
    print("\n273. The project's GETs opened from Home's card: its Experiential statements and PETs tabs open the "
          "participant last opened in the project, from the recent list, at the timepoint last opened in a project of "
          "two or more, the first in order with none opened, and the participant's own from their PETs (26 October)")
    import server as server_mod
    import idiograph_routes as routes

    b64 = lambda text: base64.b64encode(text.encode("utf-8")).decode("ascii")
    base = scratch / "a273"
    shutil.rmtree(base, ignore_errors=True)
    base.mkdir(parents=True)
    cfg_file = base / "config-273.json"
    cfg_file.write_text(json.dumps({"projects": [], "interviewer": "Cox", "corpus": "", "gravity_reference": "",
                                    "corpus_exclude": []}), encoding="utf-8")
    kept = (server_mod.CONFIG_PATH, server_mod.ROOT_OVERRIDE, server_mod.STATE_PATH, server_mod.STATE_MEMORY)

    def row(who, text, interview, **more):
        return dict({"name": f"{who.lower()}-{interview.lower()}.txt", "data": b64(text.format(who=who)), "pseudonym": who,
                     "interview": interview, "speakers": {"Cox": "interviewer", who: "participant"}}, **more)

    def call(route: str, body: dict) -> dict:
        # through the dispatch's own scope, as a request from the page comes in
        with routes.route_scope(route, body):
            return server_mod.ROUTES[route](body)

    rel = lambda p: server_mod.rel_path(p)
    try:
        server_mod.CONFIG_PATH, server_mod.ROOT_OVERRIDE = cfg_file, None
        server_mod.STATE_PATH, server_mod.STATE_MEMORY = base / "a273-state.json", {"recent": []}

        # ── A. a project of one timepoint, three participants
        river = base / "Learning to row"
        river.mkdir()
        routes.api_new_project({"op": "make", "folder": str(river), "name": "Learning to row",
                                "research_question": "How do adults take to rowing on a river?",
                                "files": [row(w, ROW, "Interview") for w in ("Ash", "Bryn", "Cole")]})
        books = {w: river / f"P{n} - {w}" / f"P{n} {w} - EN & ES.xlsx" for n, w in ((1, "Ash"), (2, "Bryn"), (3, "Cole"))}
        head = routes.gets_head(river)
        none = call("/api/gets", {"workbook": head["path"]})
        check("273: with no participant opened yet, the GETs from Home's card come through the first in order and "
              "answer no participant opened last",
              head["path"] == rel(books["Ash"]) and none.get("last_opened") is None and "last_opened" in none,
              json.dumps([head["path"], none.get("last_opened")]))

        call("/api/themes", {"workbook": str(books["Cole"])})
        routes.api_open({"path": str(books["Bryn"])})
        call("/api/themes", {"workbook": str(books["Ash"]), "beside": True})
        got = call("/api/gets", {"workbook": head["path"]})
        check("273: Cole's PETs then Bryn's statements opened, the GETs answer Bryn, a board looked at beside the "
              "canvas not counting, with no timepoint in a project of one",
              got.get("last_opened") == {"case": "P2 - Bryn", "path": rel(books["Bryn"]), "timepoint": None},
              json.dumps(got.get("last_opened")))
        check("273: and the recent list's entries in a project of one carry nothing new",
              all(sorted(r) == ["case", "name", "opened", "path"] for r in server_mod.STATE_MEMORY["recent"]),
              json.dumps(server_mod.STATE_MEMORY["recent"])[:300])
        through = call("/api/gets", {"workbook": str(books["Cole"])})
        check("273: the GETs opened through another participant's workbook answer the same participant opened last",
              (through.get("last_opened") or {}).get("case") == "P2 - Bryn")

        # ── B. a project of two timepoints: Wren at T1 and T2, Fen at T1
        sea = base / "Winter sea"
        sea.mkdir()
        made = routes.api_new_project({"op": "make", "folder": str(sea), "name": "Winter sea",
                                       "research_question": "How do people come to swim in the sea through a winter?",
                                       "files": [row("Wren", SWIM, "Autumn"), row("Fen", SWIM, "Autumn")]})
        root_id = made["project"]["id"]
        routes.api_project({"root": root_id, "timepoints": [{"label": "Autumn", "description": ""},
                                                             {"label": "New year", "description": ""}]})
        routes.api_add_transcripts({"op": "add", "root": root_id, "files": [row("Wren", LATER, "Later", timepoint=2)]})
        wren, fen = sea / "P1 - Wren" / "P1 Wren - EN & ES.xlsx", sea / "P2 - Fen" / "P2 Fen - EN & ES.xlsx"
        call("/api/themes", {"workbook": str(fen)})
        call("/api/themes", {"workbook": str(wren), "timepoint": 2})
        routes.api_open({"path": str(wren)})
        lhead = routes.gets_head(sea)
        lgets = call("/api/gets", {"workbook": lhead["path"]})
        check("273: in a project of two timepoints the LGETs answer Wren, opened last, at T2, whose PETs were opened "
              "last, an open of the statements screen keeping it",
              lhead.get("lgets") and lgets.get("lgets")
              and lgets.get("last_opened") == {"case": "P1 - Wren", "path": rel(wren), "timepoint": 2},
              json.dumps([lhead.get("lgets"), lgets.get("lgets"), lgets.get("last_opened")]))
        call("/api/themes", {"workbook": str(fen)})
        again = call("/api/gets", {"workbook": lhead["path"]})
        lp = call("/api/gets", {"workbook": str(wren), "lpets": True})
        check("273: Fen's PETs opened after, the LGETs answer Fen at T1, and a participant's LPETs answer none",
              again.get("last_opened") == {"case": "P2 - Fen", "path": rel(fen), "timepoint": 1}
              and lp.get("lpets") and lp.get("last_opened") is None,
              json.dumps([again.get("last_opened"), lp.get("last_opened")]))
    finally:
        server_mod.CONFIG_PATH, server_mod.ROOT_OVERRIDE, server_mod.STATE_PATH, server_mod.STATE_MEMORY = kept

    _steps_in_node(scratch)


HARNESS = r"""
const els = {};
const $ = (id) => (els[id] = els[id] || { id, hidden: false, title: '' });
const calls = [];
const TH_STEPS = ['statements', 'pets', 'lpets', 'gets', 'lgets', 'trajectories'];
let TH;
const thGets = () => TH.mode === 'gets';
for (const name of ['dsTabsDraw', 'thPickerPlace', 'thTpDraw', 'thTitleDone', 'thNoteDone', 'thViewEnd', 'thVmenu', 'say'])
  globalThis[name] = () => {};
const thFlush = async () => {};
const navGo = async (_fn, go) => go();
const themesOpen = (path, opts) => calls.push(['pets', path, opts.timepoint || null, opts.to]);
const getsOpen = (path, opts) => calls.push(['gets', path, opts]);
const themesBack = () => calls.push(['back']);
for (const name of ['gtFromPets', 'thToLpets', 'thToTraj']) globalThis[name] = () => calls.push([name]);
const openStatements = (path, opts) => calls.push(['statements', path, opts.timepoint || null, opts.to]);
const thWhere = () => ({});
const CASES = [{ case: 'P1 - Ash', who: 'Ash', path: 'row/P1 - Ash/ash.xlsx' }, { case: 'P2 - Bryn', who: 'Bryn', path: 'row/P2 - Bryn/bryn.xlsx' },
  { case: 'P3 - Cole', who: 'Cole', path: 'row/P3 - Cole/cole.xlsx' }];
const gets = (to, path, last, more = {}) => Object.assign({ mode: 'gets', to, path, live: true, busy: false, dirty: false, lpets: false, lgets: false,
  meta: { id: 'b1' }, back: null, label: '', v: {}, view: { x: 0, y: 0, z: 1 }, lastPick: null, sel: { cards: [], groups: [], stickies: [] },
  gets: { cases: CASES, last } }, more);
const out = {};
const run = async (name, t) => {
  TH = t;
  thStepsDraw();
  out[name] = { es: $('th-step-es').title, pets: $('th-step-pets').title };
  await thStepTo('pets');
  TH = t;
  await thStepTo('statements');
  await new Promise((r) => setTimeout(r, 0));
  out[name].went = calls.splice(0).filter((c) => c[0] !== 'gets');
};
(async () => {
  const bryn = { case: 'P2 - Bryn', path: 'row/P2 - Bryn/bryn.xlsx', timepoint: null };
  await run('card', gets('cases', CASES[0].path, bryn));
  await run('none', gets('cases', CASES[0].path, null));
  await run('pets', gets('pets', CASES[2].path, bryn));
  await run('lgets', gets('cases', CASES[0].path, { case: 'P2 - Bryn', path: 'row/P2 - Bryn/bryn.xlsx', timepoint: 2 }, { lgets: true }));
  console.log(JSON.stringify(out));
})().catch((e) => { console.error(String(e && e.stack || e)); process.exit(1); });
"""


def _steps_in_node(scratch: Path):
    """The page's own gtStepCase, thStepAt, thStepsDraw, thStepTo, gtToPets and thToStatements in node, on an invented
    project's GETs: the tooltips name the participant the tabs open, and each tab opens them."""
    node = shutil.which("node")
    if not node:
        skip("273: the steps in node", "node is not on this machine")
        return
    tjs = support.text("apps/idiograph/static/themes.js")

    def whole(name: str) -> str:
        head = f"function {name}("
        at = tjs.index(head)
        if tjs[max(0, at - 6):at] == "async ":
            at -= 6
        return tjs[at:tjs.index("\n}\n", at) + 3]

    def arrow(name: str) -> str:
        at = tjs.index(f"const {name} = ")
        end = tjs.index("\n", at) if tjs[tjs.index("\n", at) - 1] == ";" else tjs.index("\n};\n", at) + 3
        return tjs[at:end] + "\n"

    pieces = [arrow("thStageNow"), whole("gtStepCase"), arrow("thStepAt"), whole("thStepsDraw"), whole("thStepTo"),
              whole("gtToPets"), whole("thToStatements")]
    script = scratch / "a273-steps.js"
    script.write_text(support.i18n_js() + "\n".join(pieces) + HARNESS, encoding="utf-8")
    run = subprocess.run([node, str(script)], capture_output=True, text=True, encoding="utf-8", timeout=60)
    o = json.loads(run.stdout) if run.returncode == 0 and run.stdout.strip() else {}
    bryn, ash, cole = "row/P2 - Bryn/bryn.xlsx", "row/P1 - Ash/ash.xlsx", "row/P3 - Cole/cole.xlsx"
    check("273: in node, the GETs from Home's card with Bryn opened last: both tooltips name Bryn, and PETs and "
          "Experiential statements open Bryn",
          o.get("card") == {"es": "Experiential statements for Bryn", "pets": "PETs for Bryn",
                            "went": [["pets", bryn, None, "gets"], ["statements", bryn, None, "gets"]]},
          (run.stdout + run.stderr)[:600])
    check("273: in node, with no participant opened yet, the first in order, Ash, as before",
          o.get("none") == {"es": "Experiential statements for Ash", "pets": "PETs for Ash",
                            "went": [["pets", ash, None, "gets"], ["statements", ash, None, "gets"]]}, str(o.get("none")))
    check("273: in node, the GETs opened from Cole's PETs keep Cole, whoever was opened last, PETs going back to them",
          (o.get("pets") or {}).get("es") == "Experiential statements for Cole"
          and (o.get("pets") or {}).get("went") == [["back"], ["statements", cole, None, "gets"]], str(o.get("pets")))
    check("273: in node, the LGETs from Home's card open Bryn at the timepoint whose PETs were opened last, T2",
          (o.get("lgets") or {}).get("went") == [["pets", bryn, 2, "lgets"], ["statements", bryn, 2, "lgets"]],
          str(o.get("lgets")))
