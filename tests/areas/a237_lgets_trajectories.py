from __future__ import annotations

import base64
import csv
import json
import os
import html as html_mod
import shutil
import subprocess
import tempfile
from pathlib import Path

from workbook import WorkbookError

from .support import check, skip
from . import support
import idiograph_routes

# Every word invented: Kit asks newcomers to an allotment about their first year on it, before the season,
# at midsummer and after the harvest. Wren is interviewed at T1 and T2, Ash at all three.
WREN_T1 = ("Kit: [00:00:03] What did you expect of the plot?\nWren: [00:00:08] Tidy rows, like the seed packets.\n"
           "Kit: [00:00:40] And the shed?\nWren: [00:35:55] I had not looked inside it yet.\n")
WREN_T2 = ("Kit: [00:00:02] How is it now?\nWren: [00:00:06] I ask the neighbours before I read the packet.\n")
ASH_T1 = ("Kit: [00:00:03] Why a plot?\nAsh: [00:00:09] To grow what my grandmother grew.\n")
ASH_T2 = ("Kit: [00:00:03] And now?\nAsh: [00:00:07] The beans failed and I asked next door.\n")
ASH_T3 = ("Kit: [00:00:03] After the harvest?\nAsh: [00:00:05] I keep a notebook of what the neighbours say.\n")
COMPOST = ("Kit: [00:00:03] What did you expect of the heap?\nWren: [00:00:08] That it would smell.\n")
THREE = [{"label": "T1", "description": "Before the season"}, {"label": "T2", "description": "Midsummer"},
         {"label": "T3", "description": "After the harvest"}]


def test_lgets_trajectories(scratch):
    print("\n237. Timepoints part 3 (21 October): every timepoint's statements in the statements CSV and the "
          "command line, a renamed timepoint moving nothing, LGETs made from LPETs and saved, the Trajectories board "
          "named, a participant placed and moved with the note kept, and a project of one timepoint unchanged")
    import cli
    import export as export_mod
    import gets as gets_mod
    import mcp_server
    import server as server_mod
    import themes
    import trajectories as traj_mod
    import workbook as wb_mod

    b64 = lambda text: base64.b64encode(text.encode("utf-8")).decode("ascii")
    base = scratch / "a237"
    shutil.rmtree(base, ignore_errors=True)
    base.mkdir(parents=True)
    cfg_file = scratch / "a237-config.json"
    cfg_file.write_text(json.dumps({"projects": [], "interviewer": "Kit", "corpus": "", "gravity_reference": "",
                                    "corpus_exclude": []}), encoding="utf-8")
    kept = (server_mod.CONFIG_PATH, server_mod.ROOT_OVERRIDE, server_mod.STATE_PATH, server_mod.STATE_MEMORY)

    def tree(at: Path) -> dict:
        return {p.relative_to(at).as_posix(): (p.read_bytes() if p.is_file() and p.suffix != ".lock" else None)
                for p in sorted(at.rglob("*"))}

    def row(name, text, who, interview, **more):
        return dict({"name": name, "data": b64(text), "pseudonym": who, "interview": interview,
                     "speakers": {"Kit": "interviewer", who: "participant"}}, **more)

    def said_rows(book: Path, sheet: str, who: str) -> list[int]:
        import openpyxl
        wb = openpyxl.load_workbook(book, read_only=True)
        try:
            return [r for r, values in enumerate(wb[sheet].iter_rows(min_row=2, max_col=1, values_only=True), start=2)
                    if str(values[0] or "").strip() == who]
        finally:
            wb.close()

    def call(route: str, body: dict) -> dict:
        with idiograph_routes.route_scope(route, body):
            return server_mod.ROUTES[route](body)

    def refused(route: str, body: dict) -> str:
        try:
            call(route, body)
        except WorkbookError as exc:
            return str(exc)
        return "answered"

    def board_of(book: Path, tp: int, groups: list):
        """A PETs board at a timepoint, each PET the cards at those places in the canvas's order."""
        st = call("/api/themes", {"workbook": str(book), "timepoint": tp})
        keys = [c["key"] for c in st["cards"]]
        v = dict(st["version"], cards={k: {"x": 0, "y": 40 * i} for i, k in enumerate(keys)},
                 groups=[{"id": f"g{i + 1}", "label": label, "members": [keys[j] for j in at], "x": 300 * i, "y": -40}
                         for i, (label, at) in enumerate(groups)], discarded=[], picks={})
        call("/api/themes-save", {"workbook": str(book), "timepoint": tp, "version": v})

    def lpets_of(book: Path, groups: list):
        """A participant's LPETs, each LPET the timepoint PETs of those titles."""
        lp = call("/api/gets", {"workbook": str(book), "lpets": True})
        pet = {c["text"]: c["key"] for c in lp["cards"] if c["kind"] == "pet"}
        lv = dict(lp["version"], cards={c["key"]: {"x": c["x"], "y": c["y"]} for c in lp["cards"]},
                  groups=[{"id": f"G{i + 1}", "label": label, "members": [pet[t] for t in titles], "x": 400 * i,
                           "y": -60} for i, (label, titles) in enumerate(groups)], discarded=[], picks={}, notes=[])
        call("/api/gets-save", {"workbook": str(book), "lpets": True, "version": lv})
        return lp

    try:
        server_mod.CONFIG_PATH, server_mod.ROOT_OVERRIDE = cfg_file, None
        server_mod.STATE_PATH, server_mod.STATE_MEMORY = scratch / "a237-state.json", {"recent": []}

        # ── A. a project of one timepoint, kept to compare at the end
        compost = base / "Compost study"
        compost.mkdir()
        idiograph_routes.api_new_project({"op": "make", "folder": str(compost), "name": "Compost study",
                                    "research_question": "How do people take to keeping compost?",
                                    "files": [row("first.txt", COMPOST, "Wren", "Interview")]})
        cbook = compost / "P1 - Wren" / "P1 Wren - EN & ES.xlsx"
        sheet0 = idiograph_routes.read_sheets(cbook)[1][0]
        wb_mod.save_turn(cbook, sheet0, said_rows(cbook, sheet0, "Wren")[0], "Expecting a smell", "", "")
        call("/api/export", {"path": str(cbook)})
        one_csv = export_mod.output_path(cbook).read_bytes()
        check("237: a project of one timepoint's statements CSV has the reference's columns and no Timepoint",
              one_csv.decode("utf-8-sig").splitlines()[0] == ",".join(export_mod.HEADER), str(one_csv[:120]))

        # ── B. a project of three timepoints, Wren at T1 and T2, Ash at all three
        garden = base / "Allotment year"
        garden.mkdir()
        made = idiograph_routes.api_new_project({"op": "make", "folder": str(garden), "name": "Allotment year",
                                           "research_question": "How do newcomers make sense of a first year on a plot?",
                                           "files": [row("wren-before.txt", WREN_T1, "Wren", "Before"),
                                                     row("ash-before.txt", ASH_T1, "Ash", "Before")]})
        root_id = made["project"]["id"]
        idiograph_routes.api_project({"root": root_id, "timepoints": THREE})
        idiograph_routes.api_project({"root": root_id, "agents": True})
        idiograph_routes.api_add_transcripts({"op": "add", "root": root_id, "files": [
            row("wren-mid.txt", WREN_T2, "Wren", "Midsummer", timepoint=2),
            row("ash-mid.txt", ASH_T2, "Ash", "Midsummer", timepoint=2),
            row("ash-after.txt", ASH_T3, "Ash", "Harvest", timepoint=3)]})
        wren = garden / "P1 - Wren" / "P1 Wren - EN & ES.xlsx"
        ash = garden / "P2 - Ash" / "P2 Ash - EN & ES.xlsx"
        w1, w2 = said_rows(wren, "Before", "Wren"), said_rows(wren, "Midsummer", "Wren")
        wb_mod.save_turn(wren, "Before", w1[0], "Expecting order\nTrusting the packet", "", "")
        wb_mod.save_turn(wren, "Before", w1[1], "Not yet inside the shed", "", "I had not looked inside it yet.")
        wb_mod.save_turn(wren, "Midsummer", w2[0], "Asking the neighbours first", "", "")
        wb_mod.save_turn(ash, "Before", said_rows(ash, "Before", "Ash")[0], "Growing a grandmother's plot", "", "")
        wb_mod.save_turn(ash, "Midsummer", said_rows(ash, "Midsummer", "Ash")[0], "Failing, then asking", "", "")
        wb_mod.save_turn(ash, "Harvest", said_rows(ash, "Harvest", "Ash")[0], "Writing down the neighbours", "", "")
        board_of(wren, 1, [("Order expected", [0, 1]), ("A shed unopened", [2])])
        board_of(wren, 2, [("Learning from neighbours", [0])])
        board_of(ash, 1, [("Carrying a family plot", [0])])
        board_of(ash, 2, [("Asking after a failure", [0])])
        board_of(ash, 3, [("A notebook of advice", [0])])

        # (a) every timepoint's statements in the CSV from Settings and the command line
        call("/api/export", {"path": str(wren)})
        with open(export_mod.output_path(wren), encoding="utf-8-sig", newline="") as fh:
            rows = list(csv.reader(fh))
        check("237: the statements CSV of a participant with timepoints holds every timepoint's statements, each "
              "with its timepoint, and each PET from that timepoint's board",
              rows[0] == export_mod.HEADER + ["Timepoint"]
              and [(r[2], r[3], r[5]) for r in rows[1:]] == [
                  ("Expecting order", "Order expected", "T1"), ("Trusting the packet", "Order expected", "T1"),
                  ("Not yet inside the shed", "A shed unopened", "T1"),
                  ("Asking the neighbours first", "Learning from neighbours", "T2")], str(rows))

        def run(*args):
            code, out, err = cli.run(["--root", str(garden), "--config", str(cfg_file), *args, "--json"])
            return code, (support.plain(json.loads(out)) if out.strip() else {}), err

        code, said, err = run("statements", "Wren")
        check("237: statements without --timepoint gives every timepoint's, each row with its timepoint",
              code == 0 and [(s["text"], s["timepoint"], s["timepoint_label"]) for s in said["statements"]] == [
                  ("Expecting order", 1, "T1"), ("Trusting the packet", 1, "T1"), ("Not yet inside the shed", 1, "T1"),
                  ("Asking the neighbours first", 2, "T2")], err or str(said)[:400])
        code, said2, err = run("statements", "Wren", "--timepoint", "T2")
        check("237: and with --timepoint that timepoint's alone",
              code == 0 and [s["text"] for s in said2["statements"]] == ["Asking the neighbours first"], err)

        # (b) a timepoint renamed moves nothing on the LPETs
        lpets_of(wren, [("From order to neighbours", ["Order expected", "Learning from neighbours"])])
        os.utime(wren)  # the workbook touched, so the LPETs read it afresh
        idiograph_routes.write_timepoints(garden, [dict(THREE[0], label="Spring"), THREE[1], THREE[2]])
        lp = call("/api/gets", {"workbook": str(wren), "lpets": True})
        status = {c["case"]: c["status"] for c in lp["cases"]}
        cited = lp["cases"][0]["lines"][themes.card_key("Before", w1[1], 0)]["time"]
        whos = sorted({c["who"] for c in lp["cards"] if c["kind"] == "pet"})
        check("237: a timepoint renamed leaves its LPETs as they came in, never changed since",
              status["T1"] == "in" and status["T2"] == "in", str(status))
        check("237: and cites it by its new label", cited == "Spring, 35:55" and whos == ["Spring", "T2"],
              f"{cited} {whos}")
        idiograph_routes.write_timepoints(garden, THREE)

        # ── C. LGETs from LPETs, as GETs from PETs
        lpets_of(ash, [("Turning to neighbours", ["Asking after a failure", "A notebook of advice"]),
                       ("A family plot", ["Carrying a family plot"])])
        lg = call("/api/gets", {"workbook": str(wren)})
        lpet_cards = sorted((c["who"], c["text"]) for c in lg["cards"] if c["kind"] == "pet")
        check("237: the project's board in a project of timepoints is its LGETs: each card a participant's LPET, "
              "named by the participant",
              lg.get("lgets") is True and lpet_cards == [("Ash", "A family plot"), ("Ash", "Turning to neighbours"),
                                                         ("Wren", "From order to neighbours")], str(lpet_cards))
        wcase = next(c for c in lg["cases"] if c["case"] == "P1 - Wren")
        wline = wcase["lines"][themes.card_key("Before", w1[0], 0)]
        wshed = wcase["lines"][themes.card_key("Before", w1[1], 0)]
        check("237: every statement keeps its timepoint's citation, T1, 35:55, and one under an LPET names it",
              wline["time"] == "T1, 00:08" and wline["pet"] == "G1" and wshed["time"] == "T1, 35:55"
              and wshed["pet"] is None, f"{wline} {wshed}")
        check("237: opening the LGETs writes nothing", not (garden / gets_mod.LGETS_FILE).exists())
        key = {c["text"]: c["key"] for c in lg["cards"] if c["kind"] == "pet"}
        gv = dict(lg["version"], cards={c["key"]: {"x": c["x"], "y": c["y"]} for c in lg["cards"]},
                  groups=[{"id": "G1", "label": "Learning the plot from others",
                           "members": [key["From order to neighbours"], key["Turning to neighbours"]], "x": 0, "y": -60}],
                  discarded=[], picks={}, notes=[])
        call("/api/gets-save", {"workbook": str(wren), "version": gv})
        lgfile = garden / gets_mod.LGETS_FILE
        saved = json.loads(lgfile.read_text(encoding="utf-8"))
        check("237: an LGET of Wren's and Ash's LPETs is saved in the project's LGETs file, the GETs file untouched",
              saved["boards"][0]["groups"][0]["label"] == "Learning the plot from others"
              and sorted(saved["cases"]) == ["P1 - Wren", "P2 - Ash"] and not (garden / gets_mod.FILE).exists(),
              str(sorted(saved)))
        again = call("/api/gets", {"workbook": str(wren)})
        check("237: the LGETs open again on that LGET, every participant in",
              [g["label"] for g in again["groups"]] == ["Learning the plot from others"]
              and {c["case"]: c["status"] for c in again["cases"]} == {"P1 - Wren": "in", "P2 - Ash": "in"},
              str([(c["case"], c["status"]) for c in again["cases"]]))
        check("237: the AI's help is refused on the LGETs", refused("/api/gets-ai", {"workbook": str(wren), "op": "room"})
              == idiograph_routes.LGETS_NO_AI)
        code, gshow, err = run("gets", "show")
        check("237: the command line's gets show reads the LGETs in a project of timepoints",
              code == 0 and "Learning the plot from others" in json.dumps(gshow), err or str(gshow)[:300])
        # a timepoint renamed moves nothing on the LGETs either
        os.utime(wren)
        idiograph_routes.write_timepoints(garden, [dict(THREE[0], label="Spring"), THREE[1], THREE[2]])
        renamed = call("/api/gets", {"workbook": str(wren)})
        rline = next(c for c in renamed["cases"] if c["case"] == "P1 - Wren")["lines"][themes.card_key("Before", w1[1], 0)]
        check("237: a timepoint renamed leaves the LGETs unchanged, citing it by its new label",
              {c["case"]: c["status"] for c in renamed["cases"]}["P1 - Wren"] == "in" and rline["time"] == "Spring, 35:55",
              f"{rline['time']}")
        idiograph_routes.write_timepoints(garden, THREE)

        # ── D. the Trajectories board: named on the board, a participant placed and moved, the note kept
        tfile = garden / traj_mod.FILE
        empty = call("/api/trajectories", {"workbook": str(wren)})
        check("237: the Trajectories board opens with no trajectories, every participant not placed, each card with "
              "their colour and their LPETs' titles, and writes nothing",
              empty["columns"] == [] and empty["unplaced"] == ["P1 - Wren", "P2 - Ash"] and not tfile.exists()
              and {c["case"]: c["lpets"] for c in empty["participants"]} == {
                  "P1 - Wren": ["From order to neighbours"], "P2 - Ash": ["Turning to neighbours", "A family plot"]}
              and all(isinstance(c["colour"], int) for c in empty["participants"]), str(empty["participants"]))
        ops = [{"op": "add", "title": "Steady"}, {"op": "add", "title": "Turning"},
               {"op": "place", "participant": "Wren", "column": "Steady"},
               {"op": "note", "participant": "Wren", "note": "Asks the neighbours by midsummer"}]
        dry = call("/api/trajectories-ops", {"workbook": str(wren), "ops": ops, "dry_run": True})
        check("237: a dry run says what it would change and writes nothing",
              dry["changes"][:2] == ["Steady added.", "Turning added."] and not tfile.exists()
              and [c["title"] for c in dry["columns"]] == ["Steady", "Turning"], str(dry["changes"]))
        call("/api/trajectories-ops", {"workbook": str(wren), "ops": ops})
        held = json.loads(tfile.read_text(encoding="utf-8"))
        check("237: trajectories named on the board and a participant placed with a note are saved",
              [c["title"] for c in held["columns"]] == ["Steady", "Turning"]
              and held["placed"]["P1 - Wren"] == {"column": "c1", "note": "Asks the neighbours by midsummer"}
              and held["history"][-1]["changes"][-1] == "The note on Wren changed.", str(held))
        moved = call("/api/trajectories-ops", {"workbook": str(wren), "ops": [
            {"op": "place", "participant": "P1 - Wren", "column": "Turning"}, {"op": "rename", "column": "c2", "title": "Opening out"}]})
        check("237: moving the participant to another trajectory keeps their note, and a renamed trajectory keeps them",
              moved["columns"][1]["title"] == "Opening out" and moved["columns"][1]["participants"] == ["P1 - Wren"]
              and next(c for c in moved["participants"] if c["case"] == "P1 - Wren")["note"] == "Asks the neighbours by midsummer",
              str(moved["columns"]))
        before = tfile.read_bytes()
        said = refused("/api/trajectories-ops", {"workbook": str(wren), "ops": [
            {"op": "add", "title": "Late"}, {"op": "place", "participant": "Nobody", "column": "Late"}]})
        check("237: an operation that is wrong refuses them all, nothing written",
              "not a participant" in said and tfile.read_bytes() == before, said)
        said = refused("/api/trajectories-ops", {"workbook": str(wren), "ops": [{"op": "add", "title": "opening OUT"}]})
        check("237: two trajectories of one title are refused", "already" in said, said)
        gone = call("/api/trajectories-ops", {"workbook": str(wren), "ops": [{"op": "remove", "column": "Opening out"}]})
        check("237: a trajectory taken away puts its participants back among those not placed, their notes kept",
              [c["title"] for c in gone["columns"]] == ["Steady"] and "P1 - Wren" in gone["unplaced"]
              and next(c for c in gone["participants"] if c["case"] == "P1 - Wren")["note"], str(gone["unplaced"]))
        code, tshow, err = run("trajectories", "show")
        check("237: the command line's trajectories show reads the board", code == 0
              and [c["title"] for c in tshow.get("columns") or []] == ["Steady"], err or str(tshow)[:300])
        opsfile = scratch / "a237-traj.json"
        opsfile.write_text(json.dumps({"operations": [{"op": "place", "participant": "Ash", "column": "Steady"}]}),
                           encoding="utf-8")
        first = tfile.read_bytes()
        code, tdry, err = run("trajectories", "apply", "--ops", str(opsfile), "--dry-run")
        mid = tfile.read_bytes()
        code2, tdone, err2 = run("trajectories", "apply", "--ops", str(opsfile), "--note", "Put Ash in Steady")
        check("237: trajectories apply, its dry run writing nothing, then placing Ash",
              code == 0 and tdry.get("dry_run") is True and mid == first and code2 == 0
              and json.loads(tfile.read_text(encoding="utf-8"))["placed"]["P2 - Ash"]["column"] == "c1",
              (err or "") + (err2 or ""))
        check("237: the MCP server has the trajectories tools",
              {"trajectories_show", "trajectories_apply"} <= {t["name"] for t in mcp_server.TOOLS})

        # ── E. a project of one timepoint: no LGETs, no Trajectories, its files as they always were
        cstate = tree(compost)
        plain = call("/api/gets", {"workbook": str(cbook)})
        check("237: a project of one timepoint's board is its GETs, as before", "lgets" not in plain, str(sorted(plain))[:200])
        check("237: and its Trajectories are refused", refused("/api/trajectories", {"workbook": str(cbook)})
              == idiograph_routes.TRAJ_ONE)
        cli.run(["--root", str(compost), "--config", str(cfg_file), "gets", "show", "--json"])
        call("/api/export", {"path": str(cbook)})
        check("237: reading it again changes no byte, its statements CSV the same",
              tree(compost) == cstate and export_mod.output_path(cbook).read_bytes() == one_csv)
        _hide_not_placed(scratch)
    finally:
        server_mod.CONFIG_PATH, server_mod.ROOT_OVERRIDE, server_mod.STATE_PATH, server_mod.STATE_MEMORY = kept


HIDE_DRIVER = r"""
const $ = (id) => document.getElementById(id);
const esc = (s) => String(s).replace(/[&<>]/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;' }[c]));
const escAttr = (s) => esc(s).replace(/"/g, '&quot;');
const say = () => {}; const api = async () => ({});
const pathProjectDraw = () => {}; const dsTabsDraw = () => {}; const dsTabsWatch = () => {};
const needsRestart = () => false; const RESTART_LINE = '';
"""

HIDE_AFTER = r"""
const people = [['P1 - Wren', 'Wren', ''], ['P2 - Ash', 'Ash', ''], ['P3 - Moss', 'Moss', 'c1'], ['P4 - Fern', 'Fern', 'c1'],
  ['P5 - Rue', 'Rue', 'c2'], ['P6 - Sage', 'Sage', 'c2'], ['P7 - Dill', 'Dill', 'c3'], ['P8 - Mint', 'Mint', 'c3']];
const data = { project: null, demo: false, unplaced: people.filter((p) => !p[2]).map((p) => p[0]),
  columns: ['c1', 'c2', 'c3'].map((id, i) => ({ id, title: ['Steady', 'Rising', 'Mixed'][i],
    participants: people.filter((p) => p[2] === id).map((p) => p[0]) })),
  participants: people.map((p, i) => ({ case: p[0], who: p[1], colour: i, note: '', lpets: ['Learning the plot'], column: p[2] })) };
const phase = location.hash.slice(1);
const out = { phase };
const widths = () => [...document.querySelectorAll('.tf-band')].map((c) => Math.round(c.getBoundingClientRect().width));
const sideways = () => { const b = document.getElementById('tj-body'); return b.scrollWidth > b.clientWidth + 1; };
const names = () => [...document.querySelectorAll('.tf-band')].map((c) => c.dataset.col);
const run = async () => {
  document.getElementById('traj').hidden = false;
  TJ.path = 'x'; TJ.sideOpen = trajSideStored();
  trajLoad(data);
  const b = document.getElementById('tj-open-side');
  out.start = { open: TJ.sideOpen, cols: names(), widths: widths(), sideways: sideways(), pressed: b.getAttribute('aria-pressed'), title: b.title };
  if (phase === 'one') {
    b.click();
    out.hidden = { open: TJ.sideOpen, cols: names(), widths: widths(), sideways: sideways(), pressed: b.getAttribute('aria-pressed'), title: b.title,
      stored: localStorage.getItem(TJ_SIDE_KEY), badge: b.querySelector('.th-door-n').textContent, badgeShown: !b.querySelector('.th-door-n').hidden };
    // a column removed while hidden still sends its people to Not placed, and Left from the first column goes there
    TJ.data = Object.assign({}, data, { unplaced: [...data.unplaced, 'P3 - Moss'] });
    trajDraw();
    out.more = document.querySelector('#tj-open-side .th-door-n').textContent;
    const order = tjOrder();
    out.order = order;
  }
  document.getElementById('out').textContent = JSON.stringify(out);
};
document.addEventListener('DOMContentLoaded', run);
"""


def _hide_not_placed(scratch):
    """The Trajectories board with its Not placed column hidden and shown (trajside, 10 November 2026), the real page's
    markup and stylesheets and trajectories.js in the computer's own browser at 1280 and 720: the button hides the
    column, the others take the width it frees, the choice is kept for a reload, the hidden column's count is on the
    button, and Left from the first column still goes to Not placed."""
    exe = support.browser()
    if exe is None:
        skip("237: the Not placed column hidden and shown in a real browser", "no Chrome, Chromium, Brave or Edge on this computer")
        return
    page = support.text("apps/idiograph/static/idiograph.html")
    traj = "<section id=\"traj\"" + page.split("<section id=\"traj\"", 1)[1].split("</section>", 1)[0] + "</section>"
    css = "\n".join(support.text(p) for p in ("family/static/tokens.css", "family/static/style.css", "family/static/frame.css",
                                              "apps/idiograph/static/distil.css", "apps/idiograph/static/themes.css"))
    js = support.text("apps/idiograph/static/trajectories.js")
    check("237: the Not placed column's button is on the Trajectories screen, kept in the browser under its own key, "
          "with the boards' words Hide and Show",
          'id="tj-open-side"' in traj and "idiograph-trajectories-side" in js
          and "t('themes.side.hide', { name })" in js and "t('themes.side.show', { name })" in js)
    results = {}
    with tempfile.TemporaryDirectory(prefix="idiograph-237-") as tmp:
        for width, phases in ((1280, ("one", "two")), (720, ("one", "two"))):
            profile = Path(tmp) / f"profile-{width}"
            for phase in phases:
                doc = ("<!doctype html><html><head><meta charset=\"utf-8\"><style>" + css + "</style></head><body>" + traj
                       + "<pre id=\"out\">none</pre><script>" + support.i18n_js("idiograph") + HIDE_DRIVER + js
                       + HIDE_AFTER + "</script></body></html>")
                file = Path(tmp) / f"traj-{width}-{phase}.html"
                file.write_text(doc, encoding="utf-8")
                cmd = [str(exe), "--headless", "--disable-gpu", "--no-first-run", "--no-default-browser-check",
                       "--disable-extensions", "--disable-background-networking", "--password-store=basic",
                       "--use-mock-keychain", f"--user-data-dir={profile}", f"--window-size={width},800",
                       "--virtual-time-budget=3000", "--dump-dom", file.as_uri() + "#" + phase]
                try:
                    dumped = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", timeout=120).stdout
                except (OSError, subprocess.TimeoutExpired) as err:
                    dumped = str(err)
                said = dumped.split('<pre id="out">', 1)[1].split("</pre>", 1)[0] if '<pre id="out">' in dumped else ""
                try:
                    results[(width, phase)] = json.loads(html_mod.unescape(said))
                except ValueError:
                    results[(width, phase)] = {}
    for width in (1280, 720):
        one, two = results.get((width, "one"), {}), results.get((width, "two"), {})
        start, hid = one.get("start") or {}, one.get("hidden") or {}
        sw, hw = start.get("widths") or [0], hid.get("widths") or [0]
        grows = not hid.get("sideways") and not start.get("sideways") and len(set(hw)) == 1 and hw[0] >= sw[0]
        check(f"237: at {width}, the Trajectories board opens with Not placed and its three columns, the button pressed in",
              start.get("open") is True and start.get("cols") == ["", "c1", "c2", "c3"] and start.get("pressed") == "true"
              and "Hide Not placed" == start.get("title"), str(one)[:500])
        check(f"237: at {width}, the button hides the Not placed column, leaving the three, keeps it in the browser, "
              "counts what waits on the button and names Show", hid.get("open") is False and hid.get("cols") == ["c1", "c2", "c3"]
              and hid.get("pressed") == "false" and hid.get("title") == "Show Not placed" and hid.get("stored") == "closed"
              and hid.get("badge") == "2" and hid.get("badgeShown") is True and one.get("more") == "3", str(one)[:500])
        check(f"237: at {width}, each trajectory is a band the whole width of the board (layout F, trajbuild2), with no "
              "sideways scroll whether Not placed shows or not", bool(grows) and len(hw) == 3 and min(hw) >= min(sw), str(one)[:500])
        check(f"237: at {width}, a reload finds the column hidden as it was left", (two.get("start") or {}).get("open") is False
              and (two.get("start") or {}).get("cols") == ["c1", "c2", "c3"] and (two.get("start") or {}).get("title") == "Show Not placed",
              str(two)[:500])
        check(f"237: at {width}, with the column hidden a participant can still go back to Not placed, Left from the first "
              "column and Backspace taking it there", one.get("order") == ["", "c1", "c2", "c3"], str(one)[:500])
