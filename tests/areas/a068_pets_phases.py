from __future__ import annotations

import json
import re
import shutil
from pathlib import Path

import rounds as rounds_mod
from workbook import WorkbookError

from . import support
from .support import check, demo_copy, skip
import idiograph_routes


def test_pets_phases(scratch):
    print("\n68. Two phases, each marked complete, Statements complete and PETs complete, on the case list "
          "and the print view (177), and another case's PETs from the PETs screen, as a canvas or a table (178)")
    import subprocess
    from urllib.parse import urlencode
    import server as server_mod
    import themes as themes_mod
    import themes_print

    app = support.text("family/static/shell.js", "apps/idiograph/static/distil.js")
    js = support.text("apps/idiograph/static/themes.js")
    fn = lambda src, name: src.split(f"function {name}(", 1)[1].split("\n}", 1)[0]
    spark = "M12 3.2c.95"

    # \u2500\u2500 B. Mark PETs complete, through a board op, in the themes file
    root = scratch / "phases-root"
    juno = demo_copy(root, "Juno", "Juno - EN & ES.xlsx")
    wren = demo_copy(root, "P8 - Wren", "P8 Wren - EN & ES.xlsx")
    plain = demo_copy(root, "Plain", "Plain - EN & ES.xlsx")
    saved = (server_mod.ROOT_OVERRIDE, server_mod.STATE_PATH, server_mod.STATE_MEMORY)
    server_mod.ROOT_OVERRIDE = str(root)
    server_mod.STATE_MEMORY = {"recent": []}
    tfile = themes_mod.themes_path
    held = lambda w=juno: json.loads(tfile(w).read_text(encoding="utf-8"))
    op = lambda act, w=juno, **extra: idiograph_routes.api_themes_versions(dict({"workbook": str(w), "op": act}, **extra))

    def refused(call):
        try:
            call()
        except WorkbookError as exc:
            return str(exc)
        return ""

    def snapshot():
        return {str(p): (p.read_bytes(), p.stat().st_mtime_ns) for p in sorted(root.rglob("*")) if p.is_file()}

    try:
        check("177: Mark PETs complete with no themes file and no Current board is refused, and nothing is written",
              refused(lambda: op("complete")) == themes_mod.NO_CURRENT and not tfile(juno).exists())
        op("new")
        before = tfile(juno).read_bytes()
        check("177: and so is it on a file whose boards have none marked current, the file as it was",
              refused(lambda: op("complete")) == themes_mod.NO_CURRENT and tfile(juno).read_bytes() == before)
        op("choose", id="v1")
        boards = held()["boards"]
        marked = op("complete")
        file = held()
        rec = file.get("complete") or {}
        check("177: marked, `complete` holds the time, the Current board's id and its name",
              set(rec) == {"at", "board", "name"} and rec["board"] == "v1" and rec["name"] == "Board 1"
              and bool(re.match(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}", str(rec.get("at")))), str(rec))
        check("177: it sits at the top of the file after `chosen` and before the boards, and no board changes",
              list(file).index("complete") == list(file).index("chosen") + 1 < list(file).index("boards")
              and file["boards"] == boards and file["current"] == "v2", str(list(file)))
        check("177: the answer carries the mark, and the board on the canvas is the one it was",
              marked["complete"] == rec and marked["current"] == "v2" and marked["chosen"] == "v1"
              and idiograph_routes.api_themes({"workbook": str(juno)})["complete"] == rec)
        stamp = tfile(juno).read_bytes()
        again = op("complete")
        check("177: marking PETs already marked keeps the first time and writes nothing",
              again["complete"] == rec and tfile(juno).read_bytes() == stamp)
        board = idiograph_routes.api_themes({"workbook": str(juno)})
        body = dict(board["version"], cards={c["key"]: {"x": c["x"], "y": c["y"], "text": c["text"]} for c in board["cards"]},
                    groups=[], discarded=[], picks={}, complete=None)
        idiograph_routes.api_themes_save({"workbook": str(juno), "version": body})
        check("177: a save from the canvas, the autosave, never touches the mark", held()["complete"] == rec)
        op("rename", id="v1", name="Mornings board")
        check("177: the mark names the board by the name it has now while the file holds it, the record as it was",
              themes_mod.complete_of(held())["name"] == "Mornings board" and held()["complete"] == rec)
        unmarked = op("choose", id=None)
        check("177: unmarking the Current board leaves the record as it stands",
              unmarked["chosen"] is None and held()["complete"] == rec and unmarked["complete"]["board"] == "v1")
        check("177: with no Current board left, the mark stays and Reopen is still there to take it off",
              refused(lambda: op("complete")) == "" and held()["complete"] == rec)
        op("delete", id="v1")
        gone = held()
        check("177: deleting the board it names leaves the record too, which then names the board as it was marked",
              "v1" not in [b["id"] for b in gone["boards"]] and gone["complete"] == rec
              and themes_mod.complete_of(gone) == {"at": rec["at"], "board": "v1", "name": "Board 1"})
        check("177: anything but a record in that shape reads as no mark",
              all(themes_mod.complete_of(d) is None for d in (None, {}, {"complete": "yes"}, {"complete": {"at": 5}},
                                                               {"complete": {"at": " "}}, {"complete": None})))

        # the print view no longer says it (Adam, 31 October 2026: "I don't want that")
        printed = themes_print.page(juno, "Juno", None, "", auto=False)
        check("177: the print view does not say the PETs are marked complete",
              "marked complete" not in printed and '<p class="done">' not in printed and not hasattr(themes_print, "done_line"))

        # the case list: Statements complete, PETs complete, and Case complete for both
        op("new", w=wren)
        op("choose", w=wren, id="v1")
        wren_rec = op("complete", w=wren)["complete"]
        rounds_mod.set_complete(juno, True)
        rounds_mod.set_complete(plain, True)
        server_mod.save_state({"recent": [{"path": server_mod.rel_path(wren), "name": wren.stem, "case": "P8 - Wren", "opened": 1}]})
        listed = idiograph_routes.api_cases({})
        rows = {Path(c["path"]).name: c for c in listed["cases"]}
        check("177: each row of the case list carries the PETs' mark read from the themes file, or none",
              rows[juno.name]["pets_complete"] == themes_mod.complete_of(held()) and rows[wren.name]["pets_complete"] == wren_rec
              and rows[plain.name]["pets_complete"] is None and rows[juno.name]["complete"] and rows[wren.name]["complete"] is None,
              str({k: (v.get("complete"), v.get("pets_complete")) for k, v in rows.items()}))
        check("177: and so does its entry in the recent list, and the demo's card carries the key",
              listed["recent"] and listed["recent"][0]["pets_complete"] == wren_rec
              and "pets_complete" in (idiograph_routes.demo_entry() or {"pets_complete": None}))

        # \u2500\u2500 C. the switcher's list: the cases of the project with a themes file
        archived = demo_copy(root, "_Archive", "Old", "Old - EN & ES.xlsx")
        op("new", w=archived)
        backup = demo_copy(root, "P8 - Wren", "P8 Wren - EN & ES (pre-trim).xlsx")
        op("new", w=backup)
        ghost = root / "Ghost" / "Working" / "Ghost - EN & ES.themes.json"
        ghost.parent.mkdir(parents=True, exist_ok=True)
        ghost.write_text(tfile(wren).read_text(encoding="utf-8"), encoding="utf-8")
        before = snapshot()
        cases = idiograph_routes.api_themes_cases({"workbook": str(juno)})["cases"]
        by_case = {c["case"]: c for c in cases}
        check("178: the switcher lists every case with a themes file, by its pseudonym and in that order, and nothing else",
              [c["case"] for c in cases] == ["Juno", "P8 - Wren"] and [c["name"] for c in cases] == [juno.stem, wren.stem],
              str([(c["case"], c["name"]) for c in cases]))
        check("178: the case on the screen is the current one, and each carries the board it opens on",
              by_case["Juno"]["current"] and not by_case["P8 - Wren"]["current"]
              and by_case["P8 - Wren"]["board"] == "v1" and by_case["P8 - Wren"]["chosen"]
              and by_case["P8 - Wren"]["board_name"] == "Board 1"
              and by_case["Juno"]["board"] == held()["current"] and not by_case["Juno"]["chosen"])
        table = idiograph_routes.PRINT_PATH + "?" + urlencode({"workbook": server_mod.rel_path(wren), "board": "v1", "auto": "0"})
        check("178: Open as table is that board's print view with the dialog shut",
              by_case["P8 - Wren"]["table"] == table and "auto=0" in table
              and by_case["Juno"]["table"].endswith("&board=" + held()["current"] + "&auto=0"), by_case["P8 - Wren"]["table"])
        code, html = idiograph_routes.themes_print_page({"workbook": server_mod.rel_path(wren), "board": "v1", "auto": "0"})
        check("178: the table opens as the print view of that board, read-only, with no dialog",
              code == 200 and "const AUTO = false;" in html and "P8 Wren (" in html)
        mine = idiograph_routes.api_themes_cases({"workbook": str(plain)})["cases"]
        check("178: a case with no themes file yet still lists itself, on its first board",
              [c["case"] for c in mine] == ["Juno", "P8 - Wren", "Plain"]
              and [c["current"] for c in mine] == [False, False, True] and mine[2]["board"] == "" and mine[2]["board_name"] == "Board 1")
        demo = idiograph_routes.themes_cases(server_mod.DEMO_WORKBOOK)
        check("178: the demo is a project of its own and lists its three cases, the one open the current one",
              [c["case"] for c in demo] == ["Juno", "Mabel", "Rowan"] and demo[0]["current"]
              and [c["current"] for c in demo].count(True) == 1)

        # another case opens on its Current board, else the board last open, and nothing is written
        shown = idiograph_routes.api_themes({"workbook": str(wren), "board": "v1"})
        last = idiograph_routes.api_themes({"workbook": str(wren)})
        wrong = idiograph_routes.api_themes({"workbook": str(wren), "board": "v9"})
        check("178: /api/themes with `board` shows that board, without it the board last open, and an unknown one falls back",
              shown["version"]["id"] == "v1" and shown["current"] == "v1" and last["version"]["id"] == "v2"
              and wrong["version"]["id"] == "v2" and held(wren)["current"] == "v2")
        check("178: nothing is written by the list, the table or the open on another board",
              snapshot() == before and not any(p.suffix == ".tmp" for p in root.rglob("*")))
        revised = idiograph_routes.api_themes_boards({"workbook": str(wren), "op": "revision", "id": "v1", "name": "Looked at"})
        check("178: a board op on the board the switcher opened answers with that board, so the canvas never jumps",
              revised["version"]["id"] == "v1" and revised["history"] and revised["history"][0]["name"] == "Looked at"
              and held(wren)["current"] == "v2")
        refused_outside = False
        try:
            idiograph_routes.api_themes_cases({"workbook": str(scratch / "elsewhere.xlsx")})
        except server_mod.OutsideRoot:
            refused_outside = True
        check("178: the route is in the table and refuses a workbook outside the case root",
              server_mod.ROUTES.get("/api/themes-cases") is idiograph_routes.api_themes_cases and refused_outside)

        # reopen takes the mark off, and a reopen with none writes nothing
        shut = op("reopen")
        check("177: Reopen PETs takes the mark off the file, and the print view says nothing more",
              shut["complete"] is None and "complete" not in held()
              and '<p class="done">' not in themes_print.page(juno, "Juno", None, "", auto=False))
        stamp = tfile(juno).read_bytes()
        op("reopen")
        check("177: reopening PETs that are not marked writes nothing", tfile(juno).read_bytes() == stamp)
    finally:
        server_mod.ROOT_OVERRIDE, server_mod.STATE_PATH, server_mod.STATE_MEMORY = saved

    marker = fn(js, "thPetsDone")
    check("177: the entries go through the board op, never the autosave, and the mark fires the third level of confetti once",
          "thBoardOp(mark ? 'complete' : 'reopen')" in marker and "if (mark && TH.done && !was) { confetti(3);" in marker
          and "if (!TH.doneable) { thVsaid(RESTART_LINE); return; }" in marker and "/api/themes-save" not in marker
          and "else if (what === 'pets-done') thPetsDone(true);" in js and "else if (what === 'pets-reopen') thPetsDone(false);" in js
          and "function confetti(" not in js)
    check("177: the screen takes the mark from every answer, and a server from before it sends none",
          "TH.done = data.complete || null;" in fn(js, "thLoad")
          and "TH.doneable = Object.prototype.hasOwnProperty.call(data, 'complete');" in fn(js, "thLoad")
          and "if (Object.prototype.hasOwnProperty.call(data, 'complete')) TH.done = data.complete || null;" in fn(js, "thTakeBoards"))
    lister = fn(js, "thCasemenu")
    check("178: the menu asks for the list each time it opens, and says to restart in front of a server from before it",
          "api('/api/themes-cases', { workbook: TH.path })" in lister and "needsRestart(err) ? RESTART_LINE : err.message" in lister
          and "if (ask === TH.casesAsk && TH.casemenu) thCasemenuDraw(data.cases || []);" in lister
          and "Promise.resolve(thCasemenu(!TH.casemenu))" in js)
    going = fn(js, "thCaseGo")
    check("178: a case opens its PETs on the board it opens on, the canvas saved first, the way back to the case list",
          going.index("await thFlush();") < going.index("themesOpen(c.path,") and "board: c.board" in going and "to: 'cases'" in going
          and "loadLibrary()" in going
          and "opts.board ? { workbook: path, board: opts.board } : { workbook: path }" in fn(js, "themesOpen"))
    check("178: Open as table opens the board's print view in a tab of its own, this case's save written first",
          "window.open(waiting ? 'about:blank' : c.table, '_blank')" in fn(js, "thTable")
          and "const waiting = !!c.current && !!(TH.dirty || TH.chain || TH.saveTimer);" in fn(js, "thTable")
          and "tab.location.href = c.table;" in fn(js, "thTable"))
    check("178: Esc closes the switcher, the board menu closes it, and so does leaving or opening another case",
          "else if (TH.casemenu) thCasemenu(false);" in fn(js, "thKeyDown") and "if (open && TH.casemenu) thCasemenu(false);" in fn(js, "thVmenu")
          and "thCasemenu(false);" in fn(js, "themesOpen") and "thCasemenu(false);" in fn(js, "themesLeave"))

    # \u2500\u2500 E. in node: the case list's marks, the board menu's foot and the switcher's rows
    node = shutil.which("node")
    if not node:
        skip("177, 178: the marks, the menu and the switcher in node", "no node on this machine")
    else:
        lines = app.splitlines()
        pick = lambda start: next(line for line in lines if line.startswith(start))
        tjs = js.splitlines()
        tpick = lambda start: next(line for line in tjs if line.startswith(start))
        source = "\n".join([pick("const esc = "), pick("const escAttr = "), support.i18n_js(),
                            "function whenOf(" + fn(app, "whenOf") + "\n}", pick("const dayOf = "),
                            "function caseMarks(" + fn(app, "caseMarks") + "\n}",
                            tpick("const TH_TICK_ICON = "), tpick("const TH_CHOSEN_ICON = "), tpick("const TH_SPARK_ICON = "),
                            "function thWithAi(" + fn(js, "thWithAi") + "\n}",
                            "function thVmenuDraw(" + fn(js, "thVmenuDraw") + "\n}",
                            "function thCasemenuDraw(" + fn(js, "thCasemenuDraw") + "\n}"])
        script = scratch / "phases-check.js"
        script.write_text(
            "const els = {};\n"
            "const $ = (id) => (id.startsWith('th-vedit') ? null : els[id] || (els[id] = { innerHTML: '', style: {}, offsetWidth: 300,\n"
            "  getBoundingClientRect: () => ({ left: 100, bottom: 46 }) }));\n"
            "const window = { innerWidth: 1200 };\n"
            "const thAiOn = () => false;\n"
            "const TH = { cases: [], vedit: null, meta: { id: 'v2', name: 'Board 2', note: '' },\n"
            "  boards: [{ id: 'v1', name: 'Board 1', note: '' }, { id: 'v2', name: 'Board 2', note: '' }], chosen: 'v1', done: null };\n"
            + source + "\n"
            "const rec = { at: '2026-10-04T16:20:11+01:00', board: 'v1', name: 'Board 1' };\n"
            "const es = '2026-10-03T14:05:00';\n"
            "const out = { none: caseMarks({}), es: caseMarks({ complete: es }), pets: caseMarks({ pets_complete: rec }),\n"
            "  both: caseMarks({ complete: es, pets_complete: rec }), old: caseMarks({ complete: null, pets_complete: { board: 'v1' } }) };\n"
            "thVmenuDraw(); out.open = $('th-vmenu').innerHTML;\n"
            "TH.chosen = null; thVmenuDraw(); out.none_chosen = $('th-vmenu').innerHTML;\n"
            "TH.done = rec; thVmenuDraw(); out.done = $('th-vmenu').innerHTML;\n"
            "thCasemenuDraw([{ path: 'a', case: 'Juno', board_name: 'Board 2', chosen: false, current: true, table: '/t?a' },\n"
            "  { path: 'b', case: 'P8 - Wren', board_name: 'Board 1', chosen: true, current: false, table: '/t?b' }]);\n"
            "out.cases = $('th-casemenu').innerHTML; out.kept = TH.cases.length; out.left = $('th-casemenu').style.left;\n"
            "console.log(JSON.stringify(out));\n", encoding="utf-8")
        run = subprocess.run([node, str(script)], capture_output=True, text=True, encoding="utf-8")
        out = json.loads(run.stdout) if run.returncode == 0 and run.stdout.strip() else {}
        if not out:
            check("177, 178: the marks, the menu and the switcher run in node", False, run.stderr.strip()[:300])
        else:
            check("177: in node, the row says Statements complete or PETs complete, each with its date in the tooltip",
                  out["es"] == ' \u00b7 <span class="case-mark" title="Experiential statements marked complete, 3 Oct 2026">Statements complete</span>'
                  and out["pets"] == ' \u00b7 <span class="case-mark" title="PETs marked complete, 4 Oct 2026, on Board 1">PETs complete</span>',
                  str([out["es"], out["pets"]]))
            check("177: in node, a case with both says Case complete in their place, and one with neither says nothing",
                  out["both"] == (' \u00b7 <span class="case-mark" title="Experiential statements marked complete, 3 Oct 2026. '
                                  'PETs marked complete, 4 Oct 2026, on Board 1.">Participant complete</span>')
                  and out["none"] == "" and out["old"] == "", str([out["both"], out["none"], out["old"]]))
            foot_of = lambda h: h.split('<div class="row-menu-rule"></div>')[-1]
            check("177: in node, with a Current board the menu ends on Mark PETs complete, and with none it is disabled",
                  'data-vop="pets-done" title="Mark the PETs on Board 1, the Current board, complete">Mark PETs complete</button>'
                  in foot_of(out["open"])
                  and 'data-vop="pets-done" disabled title="Mark a board as current first">Mark PETs complete</button>' in foot_of(out["none_chosen"])
                  and "th-vdone" not in out["open"], foot_of(out["open"])[:300])
            row_v1 = out["done"].split('data-switch="v1"', 1)[1].split("</button>", 1)[0] if 'data-switch="v1"' in out["done"] else ""
            check("177: in node, marked, the board it was marked on shows the tick, PETs complete and the date, and the entry reads Reopen PETs",
                  'class="th-vdone"' in row_v1 and "PETs complete<span class=\"th-vdone-date\">4 Oct 2026</span>" in row_v1
                  and out["done"].count('class="th-vdone"') == 1
                  and 'data-vop="pets-reopen" title="PETs marked complete on 4 Oct 2026 at 16:20, on Board 1">Reopen PETs</button>'
                  in foot_of(out["done"]) and "Mark PETs complete" not in out["done"], row_v1[:300])
            rows_html = out["cases"]
            check("178: in node, the switcher ticks this case, offers the other as a button, and Open as table on both",
                  rows_html.count(">Open as table</button>") == 2 and rows_html.count('data-case="') == 1
                  and 'data-case="1"' in rows_html and '<div class="th-vitem on">' in rows_html
                  and rows_html.count('th-vchosen-word">Current</span>') == 1 and out["kept"] == 2
                  and out["left"] == "94px" and spark not in rows_html, rows_html[:300])
