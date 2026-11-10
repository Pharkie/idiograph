from __future__ import annotations

import json
import shutil

import openpyxl

import ai_suggest as ai_mod
import workbook as wb_mod
from workbook import WorkbookError

from . import support
from .support import (
    DEMO_QUESTION, DEMO_SHEET, add_second_sheet, check, compare_workbooks, css_block, demo_copy, skip,
)
import idiograph_routes


def test_titles_and_edit(scratch):
    print("\n57. The titles get the PET whole (122) and ask for a label alone (123), a statement edited in place (124), "
          "the board menu by scope (132), the empty Inspector's head (133), and keys alone on the card (135)")
    import http.server
    import subprocess
    import threading
    import urllib.error
    import urllib.request
    import server as server_mod
    import themes as themes_mod
    import themes_ai

    js = support.text("apps/idiograph/static/themes.js")
    css = support.text("apps/idiograph/static/themes.css")
    fn = lambda src, name: src.split(f"function {name}(", 1)[1].split("\n}", 1)[0]

    # ── A. the titles' system prompt
    STATEMENT = themes_ai.STATEMENT
    section1 = themes_ai.guidance_prose(1)
    edited = scratch / "titles-guidance.md"
    edited.write_text("# Edited\n\n## 1. What a theme is\n\nAn invented first line\nthat runs on.\n\nA second paragraph.\n\n"
                      "## 3. Rules\n\n5. A title of four words.\n8. Keep the sad ones.\n", encoding="utf-8")
    bare_file = scratch / "titles-guidance-bare.md"
    bare_file.write_text("# Edited\n\n## 3. Rules\n\n5. A title of four words.\n", encoding="utf-8")
    held = themes_ai.GUIDANCE
    try:
        themes_ai.GUIDANCE = edited
        afresh = themes_ai.names_system("")
        themes_ai.GUIDANCE = bare_file
        fallback = themes_ai.names_system("")
    finally:
        themes_ai.GUIDANCE = held
    check("122: section 1 is read from the file afresh on every call, its paragraphs each on one line",
          "An invented first line that runs on.\n\nA second paragraph." in afresh and "8. Keep the sad ones." in afresh
          and themes_ai.THEME not in afresh)
    check("122: a guidance file without section 1 sends the one sentence on a theme in its place",
          themes_ai.THEME in fallback and STATEMENT in fallback and "5. A title of four words." in fallback
          and fallback.index(themes_ai.THEME) < fallback.index(STATEMENT))

    # ── B. the user prompt, built on the server from the workbook and the board
    root = scratch / "titles-root"
    work = demo_copy(root, "Juno", "Juno - EN & ES.xlsx")
    (root / "idiograph-project.json").write_text(json.dumps({"name": "Scratch", "research_question": DEMO_QUESTION}),
                                                 encoding="utf-8")
    add_second_sheet(work)
    first = themes_mod.read_cards(work)
    cards = [c for c in first["cards"] if c["sheet"] == DEMO_SHEET]
    row3 = cards[0]["row"]
    book = openpyxl.load_workbook(work, rich_text=True)
    ws = book[DEMO_SHEET]
    cols = wb_mod.detect_columns(ws)
    ws.cell(row3, cols["kq"]).value = '"the house is quiet"\n\n"she is already there"'
    book.save(work)
    book.close()
    read = themes_mod.read_cards(work)
    k = [c["key"] for c in read["cards"] if c["sheet"] == DEMO_SHEET]
    texts = {c["key"]: c["text"] for c in read["cards"]}
    time_of = {c["key"]: c["time"] for c in read["cards"]}
    quotes = read["quotes"][themes_mod.row_key(DEMO_SHEET, row3)]["quotes"]
    WHY = "Mornings are hers and the dog's."
    saved_root = server_mod.ROOT_OVERRIDE
    real = (server_mod.CONFIG_PATH, ai_mod.find_key, ai_mod.http_call, themes_ai.PROMPT_CEILING)
    server_mod.ROOT_OVERRIDE = str(root)
    config_path = scratch / "titles-config.json"
    config_path.write_text(json.dumps({"ai_provider": "anthropic", "model": "claude-haiku-4-5", "ai_suggest": True}),
                           encoding="utf-8")
    sent, replies = [], []

    def wire(method, url, headers, payload, timeout):
        sent.append(payload)
        return 200, json.dumps({"content": [{"type": "text", "text": replies[0](payload)}], "stop_reason": "end_turn"})

    try:
        server_mod.CONFIG_PATH = config_path
        ai_mod.find_key = lambda *a, **kw: "k-test"
        ai_mod.http_call = wire
        opened = idiograph_routes.api_themes({"workbook": str(work)})
        board = themes_mod.blank_version(read["cards"])
        for key, (x, y) in zip(k, [(0, 0), (0, 100), (0, 200), (0, 400), (0, 500), (900, 0), (1800, 0)]):
            board["cards"][key].update(x=x, y=y)
        board.update(id=opened["version"]["id"], name=opened["version"]["name"],
                     groups=[{"id": "g1", "label": "Untitled", "note": WHY, "members": [k[0], k[1], k[2], "g2"], "x": 0, "y": -40},
                             {"id": "g2", "label": "Walks", "members": [k[3], k[4]], "x": 0, "y": 360},
                             {"id": "g3", "label": "A house that holds two", "members": [k[5]], "x": 900, "y": -40},
                             {"id": "g4", "label": "Untitled", "members": [k[6]], "x": 1800, "y": -40}],
                     picks={"g1": [quotes[1]["key"]]})
        idiograph_routes.api_themes_save({"workbook": str(work), "version": board})
        themes_file = themes_mod.themes_path(work)
        before = (work.read_bytes(), themes_file.read_bytes())
        replies[:] = [lambda p: json.dumps({"names": ["Mornings that belong to the dog", "A walk before the house wakes",
                                                      "mornings that belong to the dog", "A fourth"]})]
        named = idiograph_routes.api_themes_ai({"workbook": str(work), "op": "names", "version": "v1", "group": "g1"})
        user = sent[-1]["messages"][0]["content"]
        check("122: through the fake transport the answer parses as before, tidied and each once, with the model",
              named.get("names") == ["Mornings that belong to the dog", "A walk before the house wakes", "A fourth"]
              and named["model_name"] == "Haiku 4.5" and "said" not in named, str(named))
        check("122: the request goes with the four rules and section 1, and the room a title has",
              section1 in sent[-1]["system"] and STATEMENT in sent[-1]["system"]
              and sent[-1]["max_tokens"] == themes_ai.NAMES_MAX_TOKENS)
        lines = user.split("\n")
        at = lines.index(f"  - ({DEMO_SHEET}, {time_of[k[0]]}) {texts[k[0]]}") if f"  - ({DEMO_SHEET}, {time_of[k[0]]}) {texts[k[0]]}" in lines else -1
        check("122: the PET's title or no title yet, his note, then each statement with its sheet and its timecode, as the canvas reads them",
              "Theme: no title yet" in lines and f"  {themes_ai.NOTE_NAMES} {WHY}" in lines and at > 0
              and [l for l in lines if l.startswith("  - ")] == [f"  - ({DEMO_SHEET}, {time_of[key]}) {texts[key]}" for key in k[:3]],
              user[:400])
        check("122, 198: under each statement its own key quote, in inverted commas with its timecode, the picked one marked",
              lines[at + 1] == f'    "the house is quiet" ({time_of[k[0]]})'
              and lines[at + 2] == f"  - ({DEMO_SHEET}, {time_of[k[1]]}) {texts[k[1]]}"
              and lines[at + 3] == f'    "she is already there" ({time_of[k[1]]}) (picked)'
              and lines[at + 4] == f"  - ({DEMO_SHEET}, {time_of[k[2]]}) {texts[k[2]]}"
              and user.count(") (picked)") == 1 and user.count('"the house is quiet"') == 1, "\n".join(lines[at:at + 5]))
        sub_at = lines.index("  Sub-theme: Walks") if "  Sub-theme: Walks" in lines else -1
        check("122: the sub-theme sits under it with its title and its statements the same way, and a turn with no quotes says nothing",
              sub_at > at and lines[sub_at + 1] == f"    - ({DEMO_SHEET}, {time_of[k[3]]}) {texts[k[3]]}"
              and lines[sub_at + 2] == f"    - ({DEMO_SHEET}, {time_of[k[4]]}) {texts[k[4]]}", "\n".join(lines[sub_at:sub_at + 3]))
        check("122: then the other labels on the canvas, Untitled and its own sub-theme left out, then the closing line",
              "The other labels on the canvas, so the titles sit beside them:\n- A house that holds two\n\nThree titles, each from a different angle." in user
              and "- Walks" not in user and "- Untitled" not in user and user.endswith("Three titles, each from a different angle."))
        check("122: asking writes nothing, the workbook and the themes file as they were",
              (work.read_bytes(), themes_file.read_bytes()) == before)
        shown = themes_ai.pet_user(themes_ai.names_target(dict(read, sheets=read["sheets"][:1]), themes_mod.load(work)["boards"][0], "g1"))
        sub = themes_ai.pet_user(themes_ai.names_target(read, themes_mod.load(work)["boards"][0], "g2"))
        check("122: a case of one sheet leaves the sheet out, and a sub-theme asked for says which PET it sits in",
              f"  - ({time_of[k[0]]}) {texts[k[0]]}" in shown.split("\n") and f"({DEMO_SHEET}, " not in shown
              and "Sub-theme: Walks, inside a theme with no title yet" in sub and "Theme: no title yet" not in sub)
        calls = len(sent)
        gone = idiograph_routes.api_themes_ai({"workbook": str(work), "op": "names", "version": "v1", "group": "g9"})
        check("122: a label no longer on the board is one line and no call",
              gone == {"error": themes_ai.NO_SUCH_PET} and len(sent) == calls)

        # the room: quotes go from the statements lowest on the canvas first, and the answer says so.
        # Each statement sends its own quote alone (198), so the two are made long enough that leaving
        # one out saves more than the line saying so costs
        book = openpyxl.load_workbook(work, rich_text=True)
        book[DEMO_SHEET].cell(row3, cols["kq"]).value = ('"the house is quiet' + ", and still" * 30 + '"\n\n'
                                                         '"she is already there' + ", and waiting" * 30 + '"')
        book.save(work)
        book.close()
        read = themes_mod.read_cards(work)
        target = themes_ai.names_target(read, themes_mod.load(work)["boards"][0], "g1")
        whole = themes_ai.name_prompts(target, DEMO_QUESTION)
        # the third statement has no quote of its own, so the second's goes first, and alone
        two = themes_ai.pet_user(target, frozenset({k[1]}))
        themes_ai.PROMPT_CEILING = len(whole["system"]) + len(two)
        cut = idiograph_routes.api_themes_ai({"workbook": str(work), "op": "names", "version": "v1", "group": "g1"})
        trimmed = sent[-1]["messages"][0]["content"].split("\n")
        quoted_under = lambda key: trimmed[1 + trimmed.index(f"  - ({DEMO_SHEET}, {time_of[key]}) {texts[key]}")].startswith('    "')
        check("122: a prompt past the ceiling drops the quotes of the statements lowest on the canvas first, and says so in one line",
              whole["bare"] == frozenset() and len(whole["system"]) + len(whole["user"]) > themes_ai.PROMPT_CEILING
              and cut.get("trimmed") == 1 and cut.get("said") == themes_ai.cut_line(1)
              and sent[-1]["messages"][0]["content"] == two and quoted_under(k[0]) and not quoted_under(k[1]) and not quoted_under(k[2])
              and "The key quotes of the statement lowest on the canvas are left out here for room" in two, str(cut))
        themes_ai.PROMPT_CEILING = real[3]

        # the old body still builds the old prompt
        old = idiograph_routes.api_themes_ai({"workbook": str(work), "op": "names", "statements": ["one", "two"],
                                        "label": "Mornings", "others": ["Walks"], "note": WHY})
        check("122: a page from before this sends the statements as bare text, which still builds a prompt and answers",
              old.get("names") and sent[-1]["messages"][0]["content"] == themes_ai.names_user(["one", "two"], "Mornings", ["Walks"], WHY)
              and sent[-1]["system"] == themes_ai.names_system(DEMO_QUESTION))

        # ── C. a statement edited in place
        es = cols["es"]
        cell_before = openpyxl.load_workbook(work)[DEMO_SHEET].cell(row3, es)
        style_before = (cell_before.font.name, cell_before.font.sz, cell_before.alignment.wrap_text,
                        cell_before.alignment.vertical, cell_before.number_format, cell_before.fill.fill_type)
        lines_before = wb_mod.split_entries(cell_before.value)
        progress = work.parent / "Working" / f"{work.stem}.progress.json"
        had_progress = progress.read_bytes() if progress.exists() else None
        copy = scratch / "titles-before.xlsx"
        shutil.copy(work, copy)
        edited_answer = idiograph_routes.api_edit_statement({"workbook": str(work), "sheet": DEMO_SHEET, "row": row3, "line": 1,
                                                       "text": "  Quiet in the house,\nnever empty  ", "old": lines_before[1]})
        after = openpyxl.load_workbook(work, read_only=True)
        cell_after = next(after[DEMO_SHEET].iter_rows(min_row=row3, max_row=row3, min_col=es, max_col=es))[0]
        lines_after = wb_mod.split_entries(cell_after.value)
        after.close()
        styled = openpyxl.load_workbook(work)[DEMO_SHEET].cell(row3, es)
        problems, _ = compare_workbooks(copy, work, {(DEMO_SHEET, row3, es)})
        check("124: the route replaces that one line, one line only, and keeps every other line in its place",
              {k: x for k, x in edited_answer.items() if k not in ("versions", "copies", "histories")} == {"sheet": DEMO_SHEET, "row": row3, "line": 1, "old": lines_before[1],
                                "text": "Quiet in the house, never empty", "changed": True}
              and lines_after == [lines_before[0], "Quiet in the house, never empty"] + lines_before[2:], str(lines_after))
        check("124: the cell keeps its font, alignment and number format and gains no fill, and nothing else in the workbook moves",
              (styled.font.name, styled.font.sz, styled.alignment.wrap_text, styled.alignment.vertical, styled.number_format,
               styled.fill.fill_type) == style_before and style_before[-1] is None and not problems, str(problems[:3]))
        check("124: the progress file is left as it was",
              (progress.read_bytes() if progress.exists() else None) == had_progress)

        def refused(body):
            try:
                idiograph_routes.api_edit_statement(dict({"workbook": str(work), "sheet": DEMO_SHEET, "row": row3, "line": 1}, **body))
            except WorkbookError as exc:
                return str(exc)
            return ""

        now = work.read_bytes()
        check("124: an empty text is refused with a line, and so is a line that reads otherwise now, or is gone",
              refused({"text": "  \n "}) == wb_mod.EMPTY_STATEMENT
              and refused({"text": "x", "old": "Something else"}) == wb_mod.STATEMENT_MOVED
              and refused({"text": "x", "line": 9}) == wb_mod.NO_STATEMENT and work.read_bytes() == now)
        lock = wb_mod.lock_file(work)
        lock.write_text("", encoding="utf-8")
        try:
            locked = refused({"text": "Locked out", "old": "Quiet in the house, never empty"})
        finally:
            lock.unlink()
        check("124: a workbook Excel has open is refused with the turn screen's line, and nothing is written",
              locked == f"{work.name} is open in Excel. Close it in Excel first, then try again." and work.read_bytes() == now)
        check("124: the same text writes nothing, and the check asks the server and writes nothing",
              idiograph_routes.api_edit_statement({"workbook": str(work), "sheet": DEMO_SHEET, "row": row3, "line": 1,
                                             "text": "Quiet in the house, never empty"})["changed"] is False
              and idiograph_routes.api_edit_statement({"workbook": str(work), "check": True}) == {"ready": True, "copies": True}
              and work.read_bytes() == now)
        back = idiograph_routes.api_edit_statement({"workbook": str(work), "sheet": DEMO_SHEET, "row": row3, "line": 1,
                                              "text": lines_before[1], "old": "Quiet in the house, never empty"})
        check("124: undo's write puts the old words back through the same route",
              back["text"] == lines_before[1] and wb_mod.split_entries(
                  openpyxl.load_workbook(work)[DEMO_SHEET].cell(row3, es).value) == lines_before)
        outside = demo_copy(scratch, "titles-elsewhere", "Juno - EN & ES.xlsx")
        try:
            idiograph_routes.api_edit_statement({"workbook": str(outside), "sheet": DEMO_SHEET, "row": row3, "line": 0, "text": "x"})
            stray = True
        except server_mod.OutsideRoot:
            stray = False
        check("124: a workbook outside the root is refused", not stray)
        httpd = http.server.ThreadingHTTPServer(("127.0.0.1", 0), server_mod.Handler)
        threading.Thread(target=httpd.serve_forever, kwargs={"poll_interval": 0.05}, daemon=True).start()

        def post(route, payload):
            req = urllib.request.Request(f"http://127.0.0.1:{httpd.server_address[1]}{route}",
                                         data=json.dumps(payload).encode("utf-8"), headers={"Content-Type": "application/json"})
            try:
                with urllib.request.urlopen(req, timeout=10) as r:
                    return r.status, json.loads(r.read())
            except urllib.error.HTTPError as exc:
                return exc.code, json.loads(exc.read())

        try:
            ready = post("/api/edit-statement", {"workbook": str(work), "check": True})
            empty = post("/api/edit-statement", {"workbook": str(work), "sheet": DEMO_SHEET, "row": row3, "line": 1, "text": ""})
            route = server_mod.ROUTES.pop("/api/edit-statement")
            try:
                older = post("/api/edit-statement", {"workbook": str(work), "check": True})
            finally:
                server_mod.ROUTES["/api/edit-statement"] = route
        finally:
            httpd.shutdown()
            httpd.server_close()
        check("124: over HTTP the route answers, a refusal is a 409 with its line, and a server from before it says No such endpoint",
              ready == (200, {"ready": True, "copies": True}) and empty == (409, {"error": wb_mod.EMPTY_STATEMENT})
              and older == (404, {"error": "No such endpoint.", "code": "no_endpoint"}))
    finally:
        server_mod.ROOT_OVERRIDE = saved_root
        server_mod.CONFIG_PATH, ai_mod.find_key, ai_mod.http_call, themes_ai.PROMPT_CEILING = real

    # ── D. the page: the titles for a label alone
    names_html = fn(js, "thNamesHtml")
    ask = fn(js, "thNamesAsk")
    check("122: the page saves the canvas, then sends the label by its id and its board, and shows the server's line on room",
          ask.index("await thFlush();") < ask.index("api(thAiPath()") and "group: own.id" in fn(js, "thNamesBody")
          and "version: TH.meta ? TH.meta.id : null" in fn(js, "thNamesBody")
          and "if (nm.said) html += `<p class=\"th-names-note\">${esc(nm.said)}</p>`;" in names_html)
    check("123: the button shows for a label alone, never for a card, and n with cards and no label says to group them",
          "if (!thAiOn() || !item || item.kind !== 'group') return '';" in names_html
          and "const TH_GROUP_FIRST = t('themes.names.group_first');" in js
          and "if (target && target.kind === 'cards') { say(TH_GROUP_FIRST); return; }" in ask
          and "thSelCards" not in js and "kind: 'sel'" not in js and "item.kind === 'sel'" not in js
          and "thMakeGroup(" not in fn(js, "thNameApply") and "over the selection" not in names_html)

    # ── E. the page: a statement edited in place
    edit_open = fn(js, "thCardEditOpen")
    edit_done = fn(js, "thCardEditDone")
    write = fn(js, "thStatementWrite")
    check("124, 156, 297, 298: a double-click on a statement card opens the box over the card again since 30 October, as "
          "one on a label opens its title, on a GETs statement card too",
          "if (item.kind === 'group') thTitleOpen(item.id);\n      else thCardEditOpen(item.id);" in fn(js, "thPointerUp")
          and "box.className = 'th-title-edit th-card-edit';" in edit_open and "text.hidden = true;" in edit_open
          and ".th-card-edit {" in css and "font-size: 14.5px" in css_block(css, ".th-card-edit"))
    check("124: Enter keeps it, Esc leaves it, one line only, an empty text refused, a missing card and a revision on view refused",
          "if (e.key === 'Enter') {" in edit_open and "thCardEditDone(false)" in edit_open
          and "box.value.replace(/[\\r\\n]+/g, ' ')" in edit_open and "if (!thOneLine(box.value)) { say(TH_EDIT_EMPTY); return; }" in edit_open
          and "if (c.missing || c.gone || !thLineAt(key, c)) { say(TH_EDIT_MISSING); return; }" in edit_open and "thRefuse('edit')" in edit_open
          and "if (!text) { say(TH_EDIT_EMPTY); return; }" in edit_done)
    check("124: a server from before the route says to restart on the double-click and changes nothing",
          "await api(TH_EDIT_ROUTE, { workbook: TH.path, check: true });" in edit_open
          and "say(needsRestart(err) ? RESTART_LINE : err.message, 6000);" in edit_open
          and edit_open.index("check: true") < edit_open.index("document.createElement('textarea')"))
    check("124: the write sends what the line read, takes the new text onto the card with no changed mark, and saves as usual",
          "text: to, old: from" in write and "card.changed = false;" in write and "delete card.stored;" in write
          and "thSoon();" in write and "{ edit: { key, from: data.old, to: data.text }, what: t('themes.step.statement_edited') }" in write
          and "if (stack[stack.length - 1].edit) { thStatementStep(stack[stack.length - 1], backwards); return; }" in fn(js, "thUndo"))

    node = shutil.which("node")
    if node:
        script = scratch / "titles-edit.js"
        script.write_text(support.i18n_js() + """
const said = [];
const calls = [];
let fail = null;
// the page's elements, none here, so the board's minimap that a move asks for has nothing to draw (area 179)
globalThis.$ = () => null;
globalThis.esc = (s) => String(s).replace(/[&<>]/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;' }[c]));
globalThis.escAttr = (s) => esc(s).replace(/"/g, '&quot;');
globalThis.say = (m) => said.push(m);
globalThis.RESTART_LINE = 'Restart the server to finish this update.';
globalThis.needsRestart = (e) => String((e && e.message) || e).includes('No such endpoint.');
globalThis.api = async (path, body) => {
  calls.push([path, body]);
  if (fail) throw new Error(fail);
  return { text: body.text, old: body.old, changed: true };
};
""" + js + r"""
thRender = () => {};
thPanelDraw = () => {};
thSoon = () => {};
const tick = () => new Promise((r) => setTimeout(r, 0));
(async () => {
  const card = (row, line, text) => ({ sheet: 'S', row, line, text, x: 0, y: 0, seconds: 1, time: '00:01' });
  TH.live = true;
  TH.path = 'w.xlsx';
  TH.ai = { on: true };
  TH.v = { cards: { 'S:3:0': card(3, 0, 'first'), 'S:3:1': Object.assign(card(3, 1, 'old words'), { changed: true, stored: 'older' }) },
    groups: [], discarded: [], picks: {} };
  const g = thMakeGroup(TH.v, ['S:3:0', 'S:3:1'], 'Mornings');
  const out = {};
  out.html = [thNamesHtml({ kind: 'card', id: 'S:3:0' }), thNamesHtml({ kind: 'group', id: g }).includes('AI suggest PET titles')];
  out.wrote = await thStatementWrite('S:3:1', 'old words', 'new words', true);
  const c = TH.v.cards['S:3:1'];
  out.after = [c.text, c.changed, 'stored' in c, TH.undo.length, TH.undo[0].edit, calls[0][0], calls[0][1]];
  thUndo(true);
  await tick();
  out.undone = [TH.v.cards['S:3:1'].text, calls[1][1].text, calls[1][1].old, TH.undo.length, TH.redo.length];
  thUndo(false);
  await tick();
  out.redone = [TH.v.cards['S:3:1'].text, calls[2][1].text, TH.undo.length, TH.redo.length];
  fail = 'w.xlsx is open in Excel. Close it in Excel first, then try again.';
  thUndo(true);
  await tick();
  out.failed = [TH.v.cards['S:3:1'].text, said[said.length - 1], TH.undo.length, TH.redo.length];
  fail = 'No such endpoint.';
  out.old = [await thStatementWrite('S:3:1', 'new words', 'other', true), said[said.length - 1], TH.v.cards['S:3:1'].text];
  console.log(JSON.stringify(out));
})();
""", encoding="utf-8")
        run = subprocess.run([node, str(script)], capture_output=True, text=True, encoding="utf-8")
        if run.returncode != 0:
            check("124: the edit model runs in node", False, run.stderr.strip()[:300])
        else:
            out = json.loads(run.stdout)
            check("123: in node, a card's Inspector carries no AI suggest and a label's does",
                  out["html"] == ["", True], str(out["html"]))
            check("124: in node, a write takes the new text onto the card with no changed mark, and is one step of undo",
                  out["wrote"] is True and out["after"][:5] == ["new words", False, False, 1, {"key": "S:3:1", "from": "old words", "to": "new words"}]
                  and out["after"][5] == "/api/edit-statement"
                  and out["after"][6] == {"workbook": "w.xlsx", "sheet": "S", "row": 3, "line": 1, "text": "new words", "old": "old words"},
                  str(out["after"]))
            check("124: in node, undo writes the old text back through the route, and redo the new",
                  out["undone"] == ["old words", "old words", "new words", 0, 1] and out["redone"] == ["new words", "new words", 1, 0],
                  f"{out['undone']} {out['redone']}")
            check("124: in node, a failed write is one line, the card keeps its text and the step stays where it was",
                  out["failed"] == ["new words", "w.xlsx is open in Excel. Close it in Excel first, then try again.", 1, 0]
                  and out["old"] == [False, "Restart the server to finish this update.", "new words"], f"{out['failed']} {out['old']}")
    else:
        skip("124: the edit model in node", "no node on this machine")
