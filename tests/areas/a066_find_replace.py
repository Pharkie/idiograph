from __future__ import annotations

import inspect
import json
import re
import shutil

import openpyxl

import rounds as rounds_mod
import workbook as wb_mod
from workbook import WorkbookError

from . import support
from .support import DEMO_SHEET, cell_face, check, compare_workbooks, demo_copy, skip
import idiograph_routes


def test_find_replace(scratch):
    print("\n66. Find and replace over the transcript, every sheet of the workbook (139)")
    import subprocess
    import server as server_mod

    js = support.text("family/static/shell.js", "apps/idiograph/static/distil.js")
    fn = lambda name: js.split(f"function {name}(", 1)[1].split("\n}", 1)[0] if f"function {name}(" in js else ""
    whole = lambda name: f"function {name}(" + fn(name) + "\n}"
    found = lambda text, find, **kw: [list(s) for s in wb_mod.find_spans(text, find, **kw)]

    # ── A. the matcher: literal, whole word bounded by anything not a letter or a digit, case
    line = "So I also went, so. A sofa, so-so, and so on"
    check("139: whole word with case unticked finds So, so, and so-so, and never also or sofa",
          found(line, "so") == [[0, 2], [16, 18], [28, 30], [31, 33], [39, 41]], str(found(line, "so")))
    check("139: Match case leaves the capital out",
          found(line, "so", case=True) == [[16, 18], [28, 30], [31, 33], [39, 41]])
    check("139: with Whole word unticked the words inside also and sofa are found too",
          found(line, "so", word=False) == [[0, 2], [7, 9], [16, 18], [22, 24], [28, 30], [31, 33], [39, 41]])
    check("139: the match is literal, never a pattern, and a digit bounds a word as a letter does",
          found("axb a.b", "a.b") == [[4, 7]] and found("(so) so", "(so)") == [[0, 4]]
          and found("so2 so", "so") == [[4, 6]] and found("2so so", "so") == [[4, 6]])
    check("139: an end that is not a letter or a digit needs no boundary, so 'so ' is found before the next word",
          found("so I went", "so ") == [[0, 3]] and found("so, then", "so,") == [[0, 3]])
    check("139: occurrences never overlap, and a refused one is passed by a character, not by its length",
          found("aaa", "aa", word=False) == [[0, 2]] and found("aa aaa", "aa") == [[0, 2]]
          and found("baa aa", "aa") == [[4, 6]])
    check("139: letters beyond ASCII are letters, and case folds on them too",
          found("Café so", "café") == [[0, 4]] and found("naïve", "na", word=True) == []
          and found("", "so") == [] and found("so", "") == [])

    node = shutil.which("node")
    cases = [(line, "so", True, False), (line, "so", True, True), (line, "so", False, False),
             ("axb a.b", "a.b", True, False), ("so2 so 2so", "so", True, False), ("so I went", "so ", True, False),
             ("aa aaa baa aa", "aa", True, False), ("Café so CAFÉ", "café", True, False), ("[so] so", "[so]", True, False),
             ("naïve na", "na", True, False), ("So, SO so", "So", True, True), ("x\\y x", "\\", False, False)]
    if node:
        source = "\n".join(l for l in js.splitlines()
                           if l.startswith("const FIND_WORDISH = ") or l.startswith("const wordish = "))
        script = scratch / "find-spans.js"
        script.write_text(support.i18n_js() + source + "\n" + whole("findSpans") + "\n"
                          "const cases = " + json.dumps(cases) + ";\n"
                          "console.log(JSON.stringify(cases.map(([t, f, w, c]) => findSpans(t, f, w, c).map((s) => [s.start, s.end]))));\n",
                          encoding="utf-8")
        run = subprocess.run([node, str(script)], capture_output=True, text=True, encoding="utf-8")
        js_spans = json.loads(run.stdout) if run.returncode == 0 else run.stderr.strip()[:300]
        py_spans = [found(t, f, word=w, case=c) for t, f, w, c in cases]
        check("139: in node, the page's matcher finds exactly what the server's does, case for case",
              js_spans == py_spans, str(js_spans)[:300])
    else:
        skip("139: the page's matcher in node", "no node on this machine")

    # ── B. Replace all across two sheets, on a scratch copy given a second sheet copied from the demo's
    root = scratch / "find-replace"
    work = demo_copy(root, "Juno", "Juno - EN & ES.xlsx")
    book = openpyxl.load_workbook(work, rich_text=True)
    copy = book.copy_worksheet(book[DEMO_SHEET])
    copy.title = "2d"
    copy.delete_rows(30, copy.max_row)
    book.save(work)
    book.close()
    keep = root / "before.xlsx"
    shutil.copy2(work, keep)
    # every cell a row holds the words in, since 24 October the statements, quotes and notes beside the
    # transcript ("Everything follows"), each entry of an annotation cell on its own
    expect, wanted, rows_hit = {}, {}, set()
    book = openpyxl.load_workbook(keep, rich_text=True)
    for ws in book.worksheets:
        cols = wb_mod.detect_columns(ws)
        for r in range(2, ws.max_row + 1):
            old = wb_mod.plain_text(ws.cell(r, cols["transcript"]).value)
            hits = wb_mod.find_spans(old, "so")
            if hits:
                expect[(ws.title, r, cols["transcript"])] = wb_mod._splice(old, hits, "so,", keep=True)
                wanted[ws.title] = wanted.get(ws.title, 0) + len(hits)
                rows_hit.add((ws.title, r))
            for role in ("es", "kq", "en", "note"):
                if role not in cols:
                    continue
                new, n = wb_mod._replaced_entries(ws.cell(r, cols[role]).value, role, [("so", "so,")], True, False)
                if n:
                    expect[(ws.title, r, cols[role])] = new
                    wanted[ws.title] = wanted.get(ws.title, 0) + n
                    rows_hit.add((ws.title, r))
    book.close()
    transcript_of = lambda sheet, row: expect.get((sheet, row, 4))
    saved = (server_mod.ROOT_OVERRIDE, server_mod.STATE_PATH, server_mod.STATE_MEMORY)
    server_mod.ROOT_OVERRIDE = str(root)
    server_mod.STATE_MEMORY = {"recent": []}
    try:
        check("139: the routes are /api/replace and /api/replace-undo, after /api/edit-turn, each under the lock",
              server_mod.ROUTES.get("/api/replace") is idiograph_routes.api_replace
              and server_mod.ROUTES.get("/api/replace-undo") is idiograph_routes.api_replace_undo
              and list(server_mod.ROUTES).index("/api/replace") == list(server_mod.ROUTES).index("/api/edit-turn") + 1
              and "with writing(path, root=root):" in inspect.getsource(idiograph_routes.replace_in_case)
              and "with writing(path, root=" in inspect.getsource(idiograph_routes.undo_in_case))
        answer = idiograph_routes.api_replace({"path": str(work), "find": "so", "replace": "so,", "word": True, "case": False})
        after = root / "after.xlsx"
        shutil.copy2(work, after)
        check("139: Replace all counts every sheet, the count per sheet the matcher's own, in every column it reaches",
              answer["counts"] == wanted and set(wanted) == {DEMO_SHEET, "2d"}
              and answer["replaced"] == sum(wanted.values()) and answer["batch"]
              and any(k[2] != 4 for k in expect), f"{answer['counts']} of {wanted}")
        book = openpyxl.load_workbook(work, rich_text=True)
        wrong = [k for k, v in expect.items() if wb_mod.split_entries(wb_mod.plain_text(book[k[0]].cell(k[1], k[2]).value))
                 != wb_mod.split_entries(v)]
        header = [book[s].cell(1, 4).value for s in book.sheetnames]
        book.close()
        check("139: every occurrence on both sheets is replaced, the statements, quotes and notes with the transcript, "
              "and the header row is never touched",
              not wrong and header == ["Transcript", "Transcript"], f"{len(expect)} cells, {len(wrong)} wrong")
        problems, checked = compare_workbooks(keep, work, set(expect))
        check("139: every other cell is as it was, by the cell-by-cell comparison, run by run",
              not problems and checked > 600, f"{checked} cells compared, {len(problems)} differences "
              + "; ".join(problems[:2]))
        first = min(k for k in expect if k[0] == DEMO_SHEET and k[2] == 4)
        check("139: a changed cell keeps its style and takes no fill",
              cell_face(work, DEMO_SHEET, first[1]) == cell_face(keep, DEMO_SHEET, first[1])
              and cell_face(work, DEMO_SHEET, first[1])[-1] is None)
        check("139: the answer carries each row changed as the reader renders it, with its statements, quotes and notes",
              len(answer["rows"]) == len(rows_hit)
              and all({"sheet", "row", "text", "runs", "dropped", "es", "en", "kq", "pairs", "v", "note"} <= set(r)
                      for r in answer["rows"])
              and all(r["text"] == (transcript_of(r["sheet"], r["row"]) or r["text"]) for r in answer["rows"])
              and all("".join(x["text"] for x in r["runs"]) == r["text"] for r in answer["rows"]))
        records = [e for e in rounds_mod.load_progress(work)["edits"] if e.get("batch") == answer["batch"]]
        check("139: every changed row is one edit record under the call's one batch id, with find, replace and the count",
              len(records) == len(rows_hit) and len(rounds_mod.load_progress(work)["edits"]) == len(records)
              and all(e["find"] == "so" and e["replace"] == "so," and e["when"] for e in records)
              and sum(e["count"] for e in records) == answer["replaced"]
              and all(e["new"] == (transcript_of(e["sheet"], e["row"]) or e["old"]) for e in records),
              f"{len(records)} records, batch {answer['batch']}")

        back = idiograph_routes.api_replace_undo({"path": str(work), "batch": answer["batch"]})
        problems, checked = compare_workbooks(keep, work, set())
        records = [e for e in rounds_mod.load_progress(work)["edits"] if e.get("batch") == answer["batch"]]
        check("139: undo writes every row back, and every cell of the workbook is as it was",
              not problems and back["replaced"] == answer["replaced"] and len(back["rows"]) == len(rows_hit),
              f"{checked} cells compared, {len(problems)} differences")
        check("139: undo marks the batch's records undone, and keeps them",
              records and all(e["undone"] is True and e["undone_when"] for e in records))
        try:
            idiograph_routes.api_replace_undo({"path": str(work), "batch": answer["batch"]})
            twice = None
        except WorkbookError as exc:
            twice = str(exc)
        check("139: a replace already undone is refused", twice == "That replace has already been undone.", str(twice))
        again = idiograph_routes.api_replace_undo({"path": str(work), "batch": answer["batch"], "redo": True})
        problems, _ = compare_workbooks(after, work, set())
        records = [e for e in rounds_mod.load_progress(work)["edits"] if e.get("batch") == answer["batch"]]
        check("139: redo applies the batch again from its records, cell for cell, and marks them done again",
              not problems and again["redo"] is True and again["replaced"] == answer["replaced"]
              and all(e["undone"] is False and e["redone_when"] for e in records), f"{len(problems)} differences")
        try:
            idiograph_routes.api_replace_undo({"path": str(work), "batch": "nothing-here"})
            unknown = None
        except WorkbookError as exc:
            unknown = str(exc)
        check("139: a batch the progress file has no record of is refused", unknown is not None and "no record" in unknown)
        idiograph_routes.api_replace_undo({"path": str(work), "batch": answer["batch"]})

        # ── C. the highlights: re-keyed when their words survive, dropped and put back when the replace lands inside
        rows = {r["row"]: r for r in wb_mod.read_case(work)["sheets"][0]["rows"]}
        lit = [r for r in rows.values() if any(x["crux"] for x in r["runs"])]
        one, two = lit[0], lit[1]
        phrase = next(x["text"] for x in one["runs"] if x["crux"])
        at = one["text"].index(phrase)
        outside = next(w for w in re.findall(r"[A-Za-z]{4,}", one["text"][:at])
                       if w.lower() not in phrase.lower() and len(wb_mod.find_spans(one["text"], w, case=True)) == 1)
        moved = idiograph_routes.api_replace({"path": str(work), "find": outside, "replace": outside + " indeed",
                                        "case": True, "sheet": DEMO_SHEET, "row": one["row"], "ordinal": 0,
                                        "text": one["text"]})
        runs = moved["rows"][0]["runs"]
        start = sum(len(x["text"]) for x in runs[:next(i for i, x in enumerate(runs) if x["crux"])])
        check("139: a highlight whose words survive the replace is found again at its new place",
              [x["text"] for x in runs if x["crux"]] == [phrase] and start == at + len(" indeed")
              and moved["rows"][0]["dropped"] == [], f"{phrase[:30]!r} now at {start}")
        inner = next(x["text"] for x in two["runs"] if x["crux"])
        word = next(w for w in re.findall(r"[A-Za-z]{4,}", inner))
        hits = wb_mod.find_spans(two["text"], word, case=True)
        span = two["text"].index(inner)
        place = next(k for k, (s, e) in enumerate(hits) if span <= s and e <= span + len(inner))
        held = root / "lit.xlsx"
        shutil.copy2(work, held)
        lost = idiograph_routes.api_replace({"path": str(work), "find": word, "replace": word.upper() + "X",
                                       "case": True, "sheet": DEMO_SHEET, "row": two["row"], "ordinal": place,
                                       "text": two["text"]})
        record = rounds_mod.load_progress(work)["edits"][-1]
        check("139: a replace inside a highlight drops it, names it, and the record says where it sat",
              lost["rows"][0]["dropped"] == [inner] and not any(x["crux"] for x in lost["rows"][0]["runs"])
              and record["batch"] == lost["batch"] and record["crux"][0][:2] == [span, span + len(inner)]
              and record["crux"][0][2].get("theme") == 9, str(record.get("crux")))
        idiograph_routes.api_replace_undo({"path": str(work), "batch": lost["batch"]})
        problems, _ = compare_workbooks(held, work, set())
        check("139: undo puts the dropped highlight back on its words, in the font it had, cell for cell",
              not problems, f"{len(problems)} differences " + "; ".join(problems[:1]))

        # ── D. one occurrence by its place, and the refusals
        rows = {r["row"]: r for r in wb_mod.read_case(work)["sheets"][0]["rows"]}
        many = next(r for r in rows.values() if len(wb_mod.find_spans(r["text"], "so")) >= 2)
        s, e = wb_mod.find_spans(many["text"], "so")[1]
        single = idiograph_routes.api_replace({"path": str(work), "find": "so", "replace": "so,", "sheet": DEMO_SHEET,
                                         "row": many["row"], "ordinal": 1, "text": many["text"]})
        check("139: Replace names the occurrence by its place among the row's matches, and changes that one alone",
              single["rows"][0]["text"] == many["text"][:s] + "so," + many["text"][e:]
              and single["counts"] == {DEMO_SHEET: 1} and len(single["rows"]) == 1)
        held = work.read_bytes()
        refusals = []
        for body in ({"ordinal": 9}, {"ordinal": 0, "text": many["text"]}, {"row": 1, "ordinal": 0}):
            try:
                idiograph_routes.api_replace(dict({"path": str(work), "find": "so", "replace": "so,", "sheet": DEMO_SHEET,
                                             "row": many["row"]}, **body))
                refusals.append(None)
            except WorkbookError as exc:
                refusals.append(str(exc))
        check("139: a place no longer there, or a row that reads otherwise now, is refused and nothing is written",
              refusals[:2] == [wb_mod.FIND_MOVED, wb_mod.FIND_MOVED] and work.read_bytes() == held, str(refusals[:2]))
        check("139: the header row is never edited, named or not", refusals[2] == "The header row is never edited.")
        heads = idiograph_routes.api_replace({"path": str(work), "find": "Transcript", "replace": "Text"})
        check("139: a find that only the header holds changes nothing, not one byte",
              heads["rows"] == [] and heads["batch"] is None and work.read_bytes() == held)
        try:
            idiograph_routes.api_replace({"path": str(work), "find": "", "replace": "x"})
            empty = None
        except WorkbookError as exc:
            empty = str(exc)
        same = idiograph_routes.api_replace({"path": str(work), "find": "so", "replace": "so"})
        check("139: an empty Find is refused, and a Replace equal to Find does nothing",
              empty == wb_mod.EMPTY_FIND and (same["batch"], same["rows"], same["counts"], same["replaced"]) == (None, [], {}, 0)
              and work.read_bytes() == held, str(empty))
        lock = wb_mod.lock_file(work)
        lock.write_bytes(b"pretend Excel lock")
        locked = []
        for call, body in ((idiograph_routes.api_replace, {"find": "so", "replace": "so,"}),
                           (idiograph_routes.api_replace_undo, {"batch": single["batch"]})):
            try:
                call(dict({"path": str(work)}, **body))
                locked.append(None)
            except WorkbookError as exc:
                locked.append(str(exc))
        lock.unlink()
        check("139: a workbook Excel has open is refused with the turn screen's line, the replace and its undo alike",
              all(m and "Close it in Excel first" in m for m in locked) and work.read_bytes() == held, str(locked))
        wb_mod.edit_turn(work, DEMO_SHEET, many["row"], single["rows"][0]["text"] + " Then.")
        held = work.read_bytes()
        try:
            idiograph_routes.api_replace_undo({"path": str(work), "batch": single["batch"]})
            stale = None
        except WorkbookError as exc:
            stale = str(exc)
        check("139: an undo whose row was changed since is refused whole, and nothing is written",
              stale == wb_mod.REPLACE_MOVED and work.read_bytes() == held, str(stale))
        check("139: the ticks read true and false from a body or a query string",
              idiograph_routes.ticked("false", True) is False and idiograph_routes.ticked(None, True) is True
              and idiograph_routes.ticked("true", False) is True and idiograph_routes.ticked(False, True) is False)
    finally:
        server_mod.ROOT_OVERRIDE, server_mod.STATE_PATH, server_mod.STATE_MEMORY = saved

    # ── E. the page: the card, the icon, the key, the washes, the counts and the undo
    keys = support.keydown_text(js)
    check("139: Cmd + Shift + F opens it on the turn screen, from the fields as well, and never over another card",
          "e.shiftKey" in keys and "(e.key || '').toLowerCase() === 'f'" in keys and "openFind(); return;" in keys
          and keys.index("if (anyOverlayOpen()) return;") < keys.index("openFind();")
          < keys.index("if (typing || MOD(e) || e.altKey) return;")
          # the bar's magnifier Search's since 17 October, and Replace in the transcript opening the card (area 168)
          # Search's Replace asks Idiograph's part since the fifth build (23 October 2026), which opens the card
          and "$('btn-find')" not in js and "own.searchReplace(words);" in support.text("family/static/search.js")
          and "openFind();" in fn("distilSearchReplace")
          and "'find'" not in js.split("const OVERLAYS = ", 1)[1].split("\n", 1)[0])
    own = js.split("$('find').addEventListener('keydown', (e) => {", 1)[1].split("\n  });", 1)[0]
    check("139: Esc closes it, Enter in Find is Next and with Shift Previous, Enter in Replace with replaces",
          "closeFind(); return;" in own and "findStep(e.shiftKey ? -1 : 1)" in own and "findReplace(false)" in own
          and "e.stopPropagation()" in own and "findOpen() && !$('work').hidden) { e.preventDefault(); closeFind(); return; }" in keys)
    check("139: an open turn editor is cancelled as the card opens, and the margin's boxes close",
          "if (S.editing) closeEditor();" in fn("openFind") and "closeTimeEdit();" in fn("openFind")
          and "closeRowMenu();" in fn("openFind"))
    check("139: Next and Previous cross the sheets through the switcher's own path, and the caret comes back to the card",
          "await toSheet(hit.sheet);" in fn("findFocus") and "caret.focus({ preventScroll: true })" in fn("findFocus")
          and "findScroll" in fn("findFocus") and "(FIND.at + delta + all.length) % all.length" in fn("findStep"))
    check("139: Replace sends the place and the row's text, and a focus never sits off the sheet on screen",
          "ordinal: hit.ord, text: row.text" in fn("findReplace") and "api('/api/replace', body)" in fn("findReplace")
          and "hit.sheet !== S.sheetDrawn" in fn("findReplace") and "h.sheet === S.sheetDrawn" in fn("findAfter"))
    check("139: one press is one entry on the stack, its turn the first row changed on the sheet on screen",
          "undoPush({" in fn("findReplace") and "batch: data.batch" in fn("findReplace")
          and "rows.find((r) => r.row.sheet === S.sheetDrawn) || rows[0]" in fn("findReplace")
          and "api('/api/replace-undo', { path: S.data.path, batch: entry.batch, redo })" in fn("replaceBack")
          and "FIND_FIELDS.includes(el.id)" in fn("nativeUndoOwns"))
    check("139: a server from before this says to restart and nothing changes",
          "needsRestart(err) ? RESTART_LINE : err.message" in fn("findReplace")
          and "needsRestart(err) ? RESTART_LINE : err.message" in fn("replaceBack"))

    if node:
        script = scratch / "find-count.js"
        script.write_text(support.i18n_js() +
            "const els = {};\n"
            "const $ = (id) => (els[id] = els[id] || { textContent: '', disabled: false, value: '' });\n"
            "let FIND = { hits: [], at: -1, busy: false };\n"
            "const sheetNames = () => ['Initial', '2d'];\n"
            "const findOptions = () => ({ find: $('find-text').value });\n"
            "const findRoom = () => {};\n"
            + whole("drawFindCount") + "\n"
            "const hit = (sheet, crux) => ({ sheet, crux });\n"
            "const read = () => [els['find-said'].textContent, els['find-total'].textContent, els['find-all'].textContent, els['find-all'].disabled];\n"
            "const out = {};\n"
            "$('find-text').value = ''; drawFindCount(); out.empty = read();\n"
            "$('find-text').value = 'zz'; drawFindCount(); out.none = read();\n"
            "$('find-text').value = 'so';\n"
            "FIND.hits = [...Array(14)].map((_, k) => hit('Initial', k < 2)).concat([...Array(3)].map(() => hit('2d', false)));\n"
            "drawFindCount(); out.two = read();\n"
            "FIND.hits = [hit('Initial', true), hit('Initial', false)]; drawFindCount(); out.one = read();\n"
            "FIND.hits = [hit('2d', false)]; drawFindCount(); out.second = read();\n"
            "console.log(JSON.stringify(out));\n", encoding="utf-8")
        run = subprocess.run([node, str(script)], capture_output=True, text=True, encoding="utf-8")
        if run.returncode != 0:
            check("139: the count line runs in node", False, run.stderr.strip()[:300])
        else:
            out = json.loads(run.stdout)
            check("139: in node, the line reads the count per sheet with the total beside it, and Replace all its number",
                  out["two"] == ["14 on Initial, 3 on 2d · 2 inside workbook highlights", "17 on 2 sheets", "Replace all 17", False],
                  str(out["two"]))
            check("139: in node, nothing while Find is empty, No occurrences when there are none, Replace all disabled",
                  out["empty"] == ["", "", "Replace all", True] and out["none"] == ["No occurrences", "", "Replace all", True],
                  str([out["empty"], out["none"]]))
            check("139: in node, one sheet names itself with no total, and one occurrence in a highlight is said so, a "
                  "workbook highlight since Highlight left the screen on 16 October",
                  out["one"] == ["2 on Initial · 1 inside a workbook highlight", "", "Replace all 2", False]
                  and out["second"] == ["1 on 2d", "", "Replace all 1", False], str([out["one"], out["second"]]))

    # ── F. the manual and the internals
    check("139: with Match case off a replacement takes the case of what it replaces",
          wb_mod.keep_case("So", "so,") == "So," and wb_mod.keep_case("SO", "so,") == "SO,"
          and wb_mod.keep_case("so", "so,") == "so," and wb_mod.keep_case("so", "So,") == "So,"
          and wb_mod._splice("So I went, so to speak", [(0, 2), (11, 13)], "so,", keep=True) == "So, I went, so, to speak"
          and wb_mod._splice("So I went", [(0, 2)], "so,") == "so, I went")
