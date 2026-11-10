from __future__ import annotations

import inspect
import json
import shutil

import openpyxl

import rounds as rounds_mod
import workbook as wb_mod

from . import support
from .support import DEMO_SHEET, add_second_sheet, check, demo_copy, demo_sheet, json_strings, skip, slashed
import idiograph_routes


def test_library_and_sheets(scratch):
    print("\n34. Pseudonym labels, the recent list, backups hidden, the sheet switcher, the case-complete card")
    import subprocess
    import server as server_mod

    # ── A. the display label. Every invented name is assembled at run time, so the folder-name
    # sweep in area 12 never meets one spelled out in this file
    suffixed = "P9 - {}-{}".format("Juno", "Example")
    lower = "P9 - {}-{}".format("Juno", "example")
    check("a case folder with a second name shows its pseudonym alone",
          server_mod.display_case(suffixed) == "P9 - Juno", server_mod.display_case(suffixed))
    check("a folder with no second name is left as it is",
          server_mod.display_case("P9 - Juno") == "P9 - Juno")
    check("the demo's folder is left as it is", server_mod.display_case("Juno") == "Juno"
          and server_mod.display_case(server_mod.DEMO_CASE.name) == server_mod.DEMO_CASE.name)
    check("a second part in lower case is left alone", server_mod.display_case(lower) == lower)
    check("a path on the screen shows every case folder by its pseudonym",
          server_mod.display_path(f"Main Data/{suffixed}/Working/x.csv") == "Main Data/P9 - Juno/Working/x.csv")

    # ── B. a scratch root served the way a --root run serves it: the recent list in memory
    root = scratch / "library-root"
    juno = demo_copy(root, suffixed, "Juno - EN & ES.xlsx")
    wren = add_second_sheet(demo_copy(root, "P8 - Wren", "P8 Wren - EN & ES.xlsx"))
    raw = root / "P8 - Wren" / "Source" / "P8 - Wren v2.xlsx"
    raw.parent.mkdir(parents=True, exist_ok=True)
    book = openpyxl.Workbook()
    book.active.title = "Initial"
    book.active.append(["Name", "Timestamp", "Transcript"])
    book.active.append(["Wren", "00:00:05", "An invented line."])
    book.save(raw)
    backups = [root / "P8 - Wren" / "P8 Wren - EN & ES (pre-trim).xlsx",
               root / "P8 - Wren" / "P8 Wren v2 (complete 30Sep26).xlsx",
               root / "P8 - Wren" / "Source" / "P8 - Wren v2 (pre-assign 2026-09-30 1912).xlsx"]
    for b in backups:
        shutil.copy2(wren if "Source" not in b.parts else raw, b)
    kept = (server_mod.ROOT_OVERRIDE, server_mod.STATE_PATH, server_mod.STATE_MEMORY)
    state_file = scratch / "library-state.json"
    server_mod.ROOT_OVERRIDE = str(root)
    server_mod.STATE_PATH = state_file
    server_mod.STATE_MEMORY = {"recent": []}
    try:
        cases = idiograph_routes.api_cases({})
        names = [c["name"] for c in cases["cases"]]
        check("All cases hides every backup copy, wherever it sits",
              not any(b.stem in names for b in backups), str(names))
        check("and keeps the annotated workbooks and the raw source",
              sorted(names) == sorted([juno.stem, wren.stem, raw.stem])
              and next(c for c in cases["cases"] if c["name"] == raw.stem)["kind"] == "raw", str(names))
        labels = {c["name"]: c["case"] for c in cases["cases"]}
        check("the case label in All cases is the pseudonym alone",
              labels[juno.stem] == "P9 - Juno" and labels[wren.stem] == "P8 - Wren", str(labels))
        leaks = [v for v in json_strings(json.loads(json.dumps(cases, default=str))) if "-Example" in v]
        check("the second name never reaches the JSON of /api/cases outside the path fields", not leaks,
              f"{len(list(json_strings(cases)))} strings checked" if not leaks else str(leaks))
        opened = idiograph_routes.api_open({"path": str(juno)})
        leaks = [v for v in json_strings(json.loads(json.dumps(opened, default=str))) if "-Example" in v]
        check("nor the JSON of /api/open", not leaks, "the workbook's own name and the config carry none")
        idiograph_routes.api_open({"path": str(wren)})
        recent = idiograph_routes.api_cases({})["recent"]
        check("the recent list puts the case opened last on top",
              [r["name"] for r in recent] == [wren.stem, juno.stem], str([r["name"] for r in recent]))
        idiograph_routes.api_open({"path": str(juno)})
        recent = idiograph_routes.api_cases({})["recent"]
        check("and moves a case opened again back to the top",
              [r["name"] for r in recent] == [juno.stem, wren.stem], str([r["name"] for r in recent]))
        listed = {c["path"]: c["sheets"] for c in idiograph_routes.api_cases({})["cases"]}
        check("a recent row carries the sheets All cases shows for the same workbook",
              all(r["sheets"] == listed[r["path"]] for r in recent)
              and next(r for r in recent if r["name"] == wren.stem)["sheets"] == [DEMO_SHEET, "2d"],
              str([(r["name"], r["sheets"]) for r in recent]))
        check("and its label is the pseudonym alone", [r["case"] for r in recent] == ["P9 - Juno", "P8 - Wren"])
        check("a run with --root never writes state.json", not state_file.exists(),
              "the recent list stayed in memory")
        check("main keeps a --root run's recent list in memory, empty at a first start (updated 17 October, later, "
              "area 165, where a restart carries it across)",
              "STATE_MEMORY = carried_state()" in inspect.getsource(server_mod.start_up)
              and server_mod.carried_state({}) == {"recent": []})

        # an entry written before the label rule, in the file, as a live server keeps it
        server_mod.STATE_MEMORY = None
        old = {"path": str(juno), "name": juno.stem, "case": suffixed, "opened": 1}
        state_file.write_text(json.dumps({"recent": [old]}), encoding="utf-8")
        mapped = idiograph_routes.api_cases({})["recent"]
        check("an old entry is shown by its pseudonym on the way out",
              [r["case"] for r in mapped] == ["P9 - Juno"], str([r["case"] for r in mapped]))
        idiograph_routes.api_open({"path": str(wren)})
        stored = json.loads(state_file.read_text(encoding="utf-8"))["recent"]
        check("and is rewritten in the file on the next save",
              [r["case"] for r in stored] == ["P8 - Wren", "P9 - Juno"]
              and not any("-Example" in r["case"] for r in stored), str([r["case"] for r in stored]))
        exported = idiograph_routes.api_export({"path": str(juno)})
        check("the export line names the case folder by its pseudonym",
              "-Example" not in exported["path"] and "/P9 - Juno/Working/" in slashed(exported["path"]),
              slashed(exported["path"]).rsplit("/", 1)[-1])
        demo = idiograph_routes.demo_entry()
        check("the demo entry's label goes through the same rule",
              demo is None or demo["case"] == server_mod.display_case(server_mod.DEMO_CASE.name)
              and "display_case(" in inspect.getsource(idiograph_routes.demo_entry))
    finally:
        server_mod.ROOT_OVERRIDE, server_mod.STATE_PATH, server_mod.STATE_MEMORY = kept

    # ── C. the page: the library, the switcher, the chords, the card
    static = server_mod.HERE / "static"
    page = support.page_text()
    js = support.text("family/static/shell.js", "apps/idiograph/static/distil.js")
    fn = lambda name: js.split(f"function {name}(", 1)[1].split("\n}", 1)[0]
    check("the way back fetches the library afresh and saves a typed field on the way",
          "$('done-library').onclick = () => { hide('round-done'); toLibrary(); };" in js
          and "await commit(current(), false);" in fn("toLibraryNow") and "loadLibrary()" in fn("toLibraryNow"))
    check("the sections are cleared first and a stale answer is dropped",
          "$('projects').innerHTML = '';" in fn("loadLibrary") and "if (ask !== libraryAsk) return;" in fn("loadLibrary")
          and fn("loadLibrary").index("innerHTML = ''") < fn("loadLibrary").index("await api((own && own.homeRoute) || '/api/home')")
          and "homeRoute: '/api/cases'" in js)
    check("the page draws the rows in the order the server sends, his order",
          ".sort(" not in fn("loadLibrary") and ".sort(" not in fn("drawCards") and ".sort(" not in fn("renderFiles")
          and ".sort(" not in fn("drawPage") and ".sort(" not in fn("drawPick")
          and "drawHome();" in fn("loadLibrary") and "drawPick(data, sections);" in fn("distilHomeDraw")
          and "drawCards(list, s.participants || [], { id: s.id });" in fn("drawPage"))
    check("a file row reads its sheets, and never falls back to a path",
          "const meta = (item.sheets || []).join(', ');" in fn("renderFiles")
          and "item.case || item.path" not in js)
    check("the create card names the source by case and file, never by its path, through sourceSaid since 17 "
          "October, later, which names the file alone where its name holds the participant's (area 166)",
          "$('create-from').textContent = item.path" not in js
          and "$('create-from').textContent = sourceSaid(item);" in fn("offerCreate")
          and "fileOf(item.path)" in fn("sourceSaid") and "fileOf(item.suggested)" in fn("offerCreate"))
    check("choosing a sheet goes through goTo",
          "$('sheet-switch').onchange = () => toSheet($('sheet-switch').value);" in js
          and "return goTo(k);" in fn("toSheet") and "const k = sheetStop(sheet);" in fn("toSheet"))
    keys = support.keydown_text(js)
    check("Ctrl + Cmd + Up and Down step through the sheets from the keydown handler, never a bracket chord",
          "const sheetStep = SEEK(e) && !$('work').hidden" in keys and "stepSheet(sheetStep)" in keys
          and "e.key === 'ArrowUp' ? -1 : e.key === 'ArrowDown' ? 1 : 0" in keys
          and "BracketLeft" not in keys
          and keys.index("stepSheet(sheetStep)") < keys.index("if (typing || MOD(e) || e.altKey) return;"))
    card = page.split('<div class="overlay" id="round-done" hidden>', 1)[1].split('<div class="overlay"', 1)[0]
    check("the round card carries the way back to the list and a box for the pace",
          '<button class="primary" id="done-library" hidden>Back to the participants</button>' in card
          and 'id="done-eta-box"' in card and 'id="done-figures"' in card
          and "$('done-library').onclick = () => { hide('round-done'); toLibrary(); };" in js)

    node = shutil.which("node")
    if not node:
        return skip("the sheet picking and the card in node", "no node on this machine")

    # ── D. the picking function, on the demo with a second sheet whose turns are all decided
    work = add_second_sheet(demo_copy(scratch, "sheets", "Juno - EN & ES.xlsx"))
    case = wb_mod.read_case(work)
    _, her, him = demo_sheet(work)
    rnds = rounds_mod.build_rounds(case["sheets"], 10, him)
    summ = rounds_mod.summary(case["sheets"], rounds_mod.load_progress(work), rnds, him, 2)
    flat = [{"sheet": s["name"], "row": r["row"], "key": f"{s['name']}:{r['row']}", "name": r["name"]}
            for s in case["sheets"] for r in s["rows"]]
    stops = [i for i, r in enumerate(flat) if rounds_mod.is_stop(r, him)]
    on = lambda sheet: [k for k, i in enumerate(stops) if flat[i]["sheet"] == sheet]
    first_open = next(k for k in on(DEMO_SHEET) if summ["states"][flat[stops[k]]["key"]] == "unvisited")
    passed_summ = dict(summ, states=dict(summ["states"]))
    passed_summ["states"][flat[stops[first_open]]["key"]] = "passed"
    lines = [line for line in js.splitlines()
             if line.startswith("const sheetNames = ") or line.startswith("const sheetLabel = ")]
    source = "\n".join(lines + [f"function {n}(" + fn(n) + "\n}" for n in ("sheetStop", "toSheet", "stepSheet")])
    script = scratch / "sheets-check.js"
    script.write_text(support.i18n_js() +
        "const S = { data: { sheets: " + json.dumps([{"name": s["name"]} for s in case["sheets"]] + [{"name": "Notes"}])
        + ", progress: " + json.dumps(summ) + " }, flat: " + json.dumps(flat) + ", stops: " + json.dumps(stops) + ", at: 0 };\n"
        "const said = []; const went = [];\n"
        "const say = (m) => said.push(m); const goTo = (k) => { went.push(k); S.at = k; return Promise.resolve(); };\n"
        "const drawSheetLabel = () => {}; const current = () => S.flat[S.stops[S.at]];\n"
        + source + "\n"
        "const out = { initial: sheetStop('Initial'), second: sheetStop('2d'), none: sheetStop('Notes') };\n"
        "S.at = " + str(on(DEMO_SHEET)[0]) + "; stepSheet(-1); out.before = said.slice();\n"
        "stepSheet(1); out.next = went.slice(); stepSheet(-1); out.back = went.slice();\n"
        "toSheet('Notes'); out.notes = said.slice(); out.wentNotes = went.length;\n"
        "S.data.progress = " + json.dumps(passed_summ) + "; out.passed = sheetStop('Initial');\n"
        "console.log(JSON.stringify(out));\n", encoding="utf-8")
    run = subprocess.run([node, str(script)], capture_output=True, text=True, encoding="utf-8")
    if run.returncode != 0:
        return check("the sheet picking runs in node", False, run.stderr.strip()[:200])
    out = json.loads(run.stdout)
    check("a sheet lands on its first undecided participant turn",
          out["initial"] == first_open, f"stop {out['initial']}, after the head start")
    check("a sheet whose turns are all decided lands on its first turn",
          out["second"] == on("2d")[0], f"stop {out['second']}")
    check("a sheet with no participant turns offers none", out["none"] == -1)
    check("a passed turn counts as decided", out["passed"] > first_open, f"stop {out['passed']}")
    check("the next sheet goes through goTo, and the one before comes back to its first undecided turn",
          out["next"] == [on("2d")[0]] and out["back"] == [on("2d")[0], first_open], str(out["back"]))
    check("there is no sheet before the first, and it says so",
          out["before"] == ["This is the participant's first sheet."], str(out["before"]))
    check("a sheet with no participant turns is refused with a line and no move",
          out["wentNotes"] == 2 and "No participant passages" in out["notes"][-1])

    # ── E. the round card: a finished case, and a pace not yet measured
    lines_src = js.split("const LINES = [", 1)[1].split("];", 1)[0]
    # the dates through Intl since i18ncore (28 October 2026), the text layer before the pieces
    months = support.i18n_js()
    day_line = next(line for line in js.splitlines() if line.startswith("const dayOf = "))
    # with Work in rounds ticked, as the card behaves with rounds on (15 October)
    source = "\n".join([months, "const LINES = [" + lines_src + "];", "\n".join(ln for ln in js.splitlines() if ln.startswith(("function roundsOn(", "function roundsHere("))),
                        "function whenOf(" + fn("whenOf") + "\n}", day_line,
                        "function drawDoneMark(" + fn("drawDoneMark") + "\n}",
                        "function formatMinutes(" + fn("formatMinutes") + "\n}",
                        "function roundDone(" + fn("roundDone") + "\n}"])
    script = scratch / "card-check.js"
    script.write_text(
        "const els = {};\n"
        "const $ = (id) => els[id] || (els[id] = { textContent: '', hidden: false,\n"
        "  classList: { on: new Set(), toggle(c, v) { if (v) this.on.add(c); else this.on.delete(c); } } });\n"
        "const S = { data: { progress: null, config: { work_in_rounds: true } } }; const show = () => {}; const confetti = () => {};\n"
        + source + "\n"
        "const view = () => ({ line: $('done-line').textContent, eta: $('done-eta').textContent,\n"
        "  pending: $('done-eta').classList.on.has('pending'), etaHidden: $('done-eta-box').hidden,\n"
        "  two: $('done-figures').classList.on.has('two'), daily: $('done-daily').textContent,\n"
        "  next: $('done-next').hidden, library: $('done-library').hidden, kicker: $('done-kicker').textContent });\n"
        "const base = { roundsDone: [1, 2, 3, 4, 5], dailyTarget: 2, todayRounds: 4, streak: 3 };\n"
        "S.data.progress = { ...base, roundsLeft: 0, minutesLeft: null }; roundDone([5], true); const done = view();\n"
        "S.data.progress = { ...base, roundsDone: [1, 2], roundsLeft: 3, minutesLeft: null, todayRounds: 1 }; roundDone([2], true); const early = view();\n"
        "S.data.progress = { ...base, roundsDone: [1, 2], roundsLeft: 3, minutesLeft: 95, todayRounds: 1 }; roundDone([2], true); const timed = view();\n"
        "console.log(JSON.stringify({ done, early, timed }));\n", encoding="utf-8")
    run = subprocess.run([node, str(script)], capture_output=True, text=True, encoding="utf-8")
    if run.returncode != 0:
        return check("the round card runs in node", False, run.stderr.strip()[:200])
    out = json.loads(run.stdout)
    done, early, timed = out["done"], out["early"], out["timed"]
    check("a finished case says so under the round's own kicker",
          done["kicker"] == "Round 5 done" and done["line"] == "Participant complete.", done["line"])
    check("and drops the pace", done["etaHidden"] and done["two"])
    check("with rounds left and no pace yet the figure explains itself in the small type",
          early["eta"] == "measured after the next round" and early["pending"] and not early["etaHidden"]
          and not early["two"] and not early["next"] and early["library"] and early["line"] != "Participant complete.",
          early["eta"])
    check("with a pace it is the minutes, in the numeral face",
          timed["eta"] == __import__("i18n").t("distil.length.hours_minutes", h=1, m=35) and not timed["pending"], timed["eta"])
