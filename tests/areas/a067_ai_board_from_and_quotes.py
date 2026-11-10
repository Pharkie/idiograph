from __future__ import annotations

import json
import shutil

import openpyxl

import ai_suggest as ai_mod
import workbook as wb_mod

from . import support
from .support import (
    DEMO_QUESTION, DEMO_SHEET, add_second_sheet, check, demo_copy, skip,
)
import idiograph_routes


def test_ai_board_from_and_quotes(scratch):
    print("\n67. New AI board from all statements or from the board on the canvas (170), and the quote "
          "that carries each PET picked by the AI board (171)")
    import subprocess
    import server as server_mod
    import themes as themes_mod
    import themes_ai

    root = scratch / "aiboard-root"
    work = demo_copy(root, "Juno", "Juno - EN & ES.xlsx")
    (root / "idiograph-project.json").write_text(json.dumps(
        {"name": "Scratch", "research_question": DEMO_QUESTION}), encoding="utf-8")
    add_second_sheet(work)
    book = openpyxl.load_workbook(work, rich_text=True)
    ws = book[DEMO_SHEET]
    cols = wb_mod.detect_columns(ws)
    ws.cell(3, cols["kq"]).value = '"the house is quiet"\n\n"she is already there"'
    ws.cell(5, cols["kq"]).value = '"the lead by the door"'
    book.save(work)
    book.close()
    read = themes_mod.read_cards(work)
    k = [c["key"] for c in read["cards"]]
    ki = [key for key in k if key.startswith(f"{DEMO_SHEET}:")]
    k2 = [key for key in k if key.startswith("2d:")]
    words = {q["key"]: q["text"] for row in read["quotes"].values() for q in row["quotes"]}
    q3a, q3b, q5 = f"{DEMO_SHEET}:3:0", f"{DEMO_SHEET}:3:1", f"{DEMO_SHEET}:5:0"
    line_of = lambda key: f"- {key} ("

    # ── A. what each From sends
    mine = themes_mod.blank_version(read["cards"])
    mine["groups"] = [{"id": "g1", "label": "Mornings first", "members": [ki[0], ki[1]], "x": 0, "y": 0}]
    mine["discarded"] = [ki[2]]
    whole = themes_mod.merge(read["cards"], themes_mod.blank_version(read["cards"]))
    every = themes_ai.statements_of(whole)
    told = themes_ai.group_user(every, None, "")
    check("170: All statements sends every statement of the case, every sheet, by key, sheet, timecode and words",
          [s["key"] for s in every] == k and all(line_of(key) in told for key in k)
          and len({s["sheet"] for s in every}) == 2 and whole["discarded"] == [],
          f"{len(every)} of {len(k)}")
    check("170: with All statements the prompt says nothing of his groups, not even that there are none",
          "His labels" not in told and "There are no labels" not in told and "keep any that hold" not in told
          and told.endswith("Group the statements."))
    merged = themes_mod.merge(read["cards"], mine)
    asked = themes_ai.group_user(themes_ai.statements_of(merged), themes_ai.labels_of(merged), "")
    check("170: the board as before: its cards not discarded, its labels his to keep, merge or replace",
          line_of(ki[2]) not in asked and f"- Mornings first: {ki[0]}, {ki[1]}" in asked
          and "keep any that hold, merge them or replace them" in asked
          and "There are no labels on the canvas yet." in themes_ai.group_user(every, [], ""))

    # ── B. the picks prompt and its strict reading
    laid = themes_ai.lay_out(
        [{"label": "Mornings that belong to the dog", "members": [ki[0], ki[1], ki[3]], "groups": []},
         {"label": "A second sheet of days", "members": [k2[0], k2[1], k2[2]],
          "groups": [{"label": "Rows further on", "members": [k2[3], k2[4]]}]},
         {"label": "Nothing quoted here", "members": [ki[6], ki[7]], "groups": []}], whole["cards"], [])
    targets = themes_ai.picks_targets(laid, read["quotes"], read["sheets"])
    by_target = {t["id"]: t for t in targets}
    check("171: each PET and sub-theme goes by its title with the key quotes of the rows under it, a label with none left out",
          [t["id"] for t in targets] == ["g1", "g2", "g4"]
          and [q["key"] for q in by_target["g1"]["quotes"]] == [q3a, q3b, q5]
          and [q["key"] for q in by_target["g2"]["quotes"]] == [f"2d:{r}:0" for r in range(2, 7)]
          and [q["key"] for q in by_target["g4"]["quotes"]] == ["2d:5:0", "2d:6:0"]
          and by_target["g4"]["inside"] == "A second sheet of days" and by_target["g1"]["inside"] is None,
          str([(t["id"], len(t["quotes"])) for t in targets]))
    check("171: a label that carries his own picks is not sent",
          [t["id"] for t in themes_ai.picks_targets(laid, read["quotes"], read["sheets"], {"g1"})] == ["g2", "g4"])
    user = themes_ai.picks_user(targets)
    system = themes_ai.picks_system(DEMO_QUESTION)
    check("171: the prompt names each label by id and title, each quote by its pick key and words, a sub-theme with its PET",
          "Theme g1: Mornings that belong to the dog" in user and f'- {q3a} "the house is quiet"' in user
          and f'- {q5} "the lead by the door"' in user
          and "Sub-theme g4: Rows further on, inside the theme A second sheet of days" in user
          and "Nothing quoted here" not in user and user.endswith("Pick the quotes."))
    allowed = {t["id"]: {q["key"] for q in t["quotes"]} for t in targets}
    answer = json.dumps({"picks": [
        {"id": "g1", "quotes": [q3b, f"{DEMO_SHEET}:99:0", q5, q3a]},
        {"id": "g2", "quotes": [q3a]},
        {"id": "g4", "quotes": "2d:6:0"},
        {"id": "g3", "quotes": [f"{DEMO_SHEET}:7:0"]},
        {"id": "g1", "quotes": [q3a]}]})
    parsed = themes_ai.parse_picks(answer, allowed)
    check("171: read strictly: a key not the label's dropped, past two the first two, a label with none keeps none",
          parsed == {"picks": {"g1": [q3b, q5], "g4": ["2d:6:0"]}}, str(parsed))
    check("171: fences and a keyed shape read the same, and an answer that is not JSON or was cut off is one line",
          themes_ai.parse_picks(f"```json\n{answer}\n```", allowed) == parsed
          and themes_ai.parse_picks(json.dumps({"picks": {"g4": ["2d:5:0", "2d:5:0"]}}), allowed) == {"picks": {"g4": ["2d:5:0"]}}
          and themes_ai.parse_picks("nothing", allowed) == {"error": themes_ai.NOT_JSON}
          and themes_ai.parse_picks('{"groups": []}', allowed) == {"error": themes_ai.NOT_JSON}
          and themes_ai.parse_picks('{"picks": [{"id": "g1", "quo', allowed, truncated=True) == {"error": ai_mod.TOO_LONG}
          and themes_ai.pick_quotes([], DEMO_QUESTION, {"provider": "anthropic", "key": "k"}, lambda *a: 1 / 0) == {"picks": {}})
    seen = []

    def short(method, url, headers, payload, timeout):
        seen.append((payload["max_tokens"], timeout))
        return 200, json.dumps({"content": [{"type": "text", "text": answer}], "stop_reason": "end_turn"})

    quick = themes_ai.pick_quotes(targets, DEMO_QUESTION, {"provider": "anthropic", "key": "k", "model": "claude-haiku-4-5"}, short)
    check("171: one call for the whole board, a short answer with a minute to come back, read strictly",
          quick == parsed and seen == [(themes_ai.PICKS_MAX_TOKENS, themes_ai.PICKS_TIMEOUT)], str(seen))
    his = [{"id": "g7", "label": "  mornings THAT belong to the dog ", "members": []},
           {"id": "g8", "label": "A second sheet of days", "members": []}]
    carried = themes_ai.carry_picks(laid, his, {"g7": [q3a, "2d:9:0"], "g8": []})
    check("171: his picks stay on a label titled as his, those whose row is still under it",
          carried == {"g1": [q3a]}, str(carried))

    # ── C. the route, through a transport that stands in for the provider
    real = (server_mod.CONFIG_PATH, server_mod.ROOT_OVERRIDE, ai_mod.find_key, ai_mod.http_call)
    config_path = scratch / "aiboard" / "config.json"
    config_path.parent.mkdir(parents=True, exist_ok=True)
    config_path.write_text(json.dumps({"ai_suggest": True, "ai_provider": "anthropic", "model": "claude-haiku-4-5",
                                       "pets_provider": "anthropic", "pets_model": "claude-opus-5-5"}), encoding="utf-8")
    sent, mode = [], {"picks": "good", "group": "quoted"}
    grouped = {"quoted": [{"label": "Mornings that belong to the dog", "members": [ki[0], ki[1], ki[3]]},
                          {"label": "A second sheet of days", "members": [k2[0], k2[1], k2[2]],
                           "groups": [{"label": "Rows further on", "members": [k2[3], k2[4]]}]},
                          {"label": "Nothing quoted here", "members": [ki[6], ki[7]]}],
               "bare": [{"label": "Nothing quoted here", "members": [ki[6], ki[7], ki[9]]}]}

    def wire(method, url, headers, payload, timeout):
        system = payload["system"]
        sent.append({"system": system, "user": payload["messages"][-1]["content"], "model": payload["model"],
                     "max_tokens": payload["max_tokens"], "timeout": timeout})
        if themes_ai.PICKS_TASK in system:
            if mode["picks"] == "fail":
                return 529, '{"error": "overloaded"}'
            if mode["picks"] == "slow":
                raise TimeoutError("timed out")
            text = answer if mode["picks"] == "good" else "I would pick the first."
        else:
            text = json.dumps({"groups": grouped[mode["group"]]})
        return 200, json.dumps({"content": [{"type": "text", "text": text}], "stop_reason": "end_turn"})

    path = themes_mod.themes_path(work)
    file = lambda: json.loads(path.read_text(encoding="utf-8"))
    try:
        server_mod.CONFIG_PATH = config_path
        server_mod.ROOT_OVERRIDE = str(root)
        ai_mod.find_key = lambda *a, **kw: "k-test"
        ai_mod.http_call = wire
        opened = idiograph_routes.api_themes({"workbook": str(work)})
        check("170: /api/themes says New AI board takes From", opened.get("from_all") is True)
        board = {**opened["version"], "cards": {c["key"]: {"x": c["x"], "y": c["y"], "text": c["text"]} for c in opened["cards"]},
                 "groups": [{"id": "g1", "label": "Mornings that belong to the dog", "members": [ki[0], ki[1]], "x": 0, "y": 0}],
                 "discarded": [ki[2]], "picks": {"g1": [q3a]}}
        idiograph_routes.api_themes_save({"workbook": str(work), "version": board})
        mine_saved = file()["boards"][0]
        book_bytes = work.read_bytes()

        made = idiograph_routes.api_themes_ai({"workbook": str(work), "op": "group", "version": "v1", "hint": "", "from": "all"})
        new = file()["boards"][-1]
        first, second = (sent + [{}, {}])[:2]
        check("170: from all, the grouping goes with every statement, the discarded one too, and none of his labels",
              len(sent) == 2 and all(line_of(key) in first["user"] for key in k)
              and "Mornings that belong to the dog" not in first["user"] and "His labels" not in first["user"]
              and "There are no labels" not in first["user"], f"{len(sent)} calls")
        check("170: the board's note and the answer say it was made from all statements, and echo From",
              new["note"].startswith("Proposed by Opus 5.5 from all statements on ") and made["made"]["from"] == "all statements"
              and made["made"]["source"] == "all" and new["name"] == "Board 2" and new["discarded"] == [], new["note"])
        check("171: one second call, through the PETs model, with the picks prompt and the room a model that thinks gets",
              themes_ai.PICKS_TASK in second.get("system", "") and second.get("model") == "claude-opus-5-5"
              and first.get("model") == "claude-opus-5-5" and second.get("max_tokens") == ai_mod.THINKING_MAX_TOKENS
              and second.get("timeout") == themes_ai.PICKS_THINKING_TIMEOUT and "Theme g1: Mornings that belong to the dog" in second.get("user", "")
              and "Nothing quoted here" not in second.get("user", ""))
        check("171: the picks are written into the new board as a tick by hand writes them, the words beside them",
              new["picks"] == {"g1": [q3b, q5], "g4": ["2d:6:0"]}
              and new.get("quoted") == {q3b: words[q3b], q5: words[q5], "2d:6:0": words["2d:6:0"]}, str(new["picks"]))
        state = idiograph_routes.api_themes({"workbook": str(work)})
        outline = themes_mod.outline(read, themes_mod.current_version(themes_mod.load(work)))
        check("171: the screen and the print view's outline carry them as any pick",
              state["picks"] == new["picks"]
              and [q["key"] for q in outline["themes"][0]["picks"]] == [q3b, q5], str(state["picks"]))
        check("171: the note says how many PETs carry picks, the answer too, and the line has nothing to add",
              "not placed. Quotes picked for 1 of 3 PETs." in new["note"] and made["made"]["picked"] == 1
              and made["made"]["unpicked"] is False, new["note"])
        check("170, 171: the board it was made from is as it was, and the workbook is never written",
              file()["boards"][0] == mine_saved and work.read_bytes() == book_bytes)

        sent.clear()
        made = idiograph_routes.api_themes_ai({"workbook": str(work), "op": "group", "version": "v1", "hint": "", "from": "board"})
        new = file()["boards"][-1]
        check("170: from the board, the grouping goes as before, its discard left out and his label sent",
              len(sent) == 2 and line_of(ki[2]) not in sent[0]["user"]
              and f"- Mornings that belong to the dog: {ki[0]}, {ki[1]}" in sent[0]["user"]
              and made["made"]["from"] == "Board 1" and made["made"]["source"] == "board"
              and new["note"].startswith("Proposed by Opus 5.5 from Board 1 on "))
        check("171: a label titled as his keeps his picks and is not sent, the rest are picked",
              "Theme g1" not in sent[1]["user"] and "Theme g2: A second sheet of days" in sent[1]["user"]
              and new["picks"] == {"g1": [q3a], "g4": ["2d:6:0"]} and new["quoted"][q3a] == words[q3a], str(new["picks"]))
        sent.clear()
        idiograph_routes.api_themes_ai({"workbook": str(work), "op": "group", "version": "v1", "hint": ""})
        check("170: a page from before From sends none, and the board goes as it always did",
              "His labels" in sent[0]["user"] and file()["boards"][-1]["note"].startswith("Proposed by Opus 5.5 from Board 1 on "))

        outcomes = []
        for how in ("fail", "slow", "junk"):
            mode["picks"] = how
            count = len(file()["boards"])
            made = idiograph_routes.api_themes_ai({"workbook": str(work), "op": "group", "version": "v1", "from": "all"})
            new = file()["boards"][-1]
            outcomes.append(len(file()["boards"]) == count + 1 and new["picks"] == {} and "quoted" not in new
                            and made["made"]["unpicked"] is True and "Quotes picked for 0 of 3 PETs." in new["note"])
        check("171: when the picks call fails, times out or cannot be read, the board is still made, with no picks",
              outcomes == [True, True, True], str(outcomes))
        mode.update(picks="good", group="bare")
        sent.clear()
        made = idiograph_routes.api_themes_ai({"workbook": str(work), "op": "group", "version": "v1", "from": "all"})
        check("171: a board whose cards carry no key quotes sends no second call and says nothing of picks",
              len(sent) == 1 and made["made"]["unpicked"] is False and file()["boards"][-1]["picks"] == {}
              and "Quotes picked for 0 of 1 PET." in file()["boards"][-1]["note"])
    finally:
        server_mod.CONFIG_PATH, server_mod.ROOT_OVERRIDE, ai_mod.find_key, ai_mod.http_call = real

    # ── D. the page
    js = support.text("apps/idiograph/static/themes.js")
    fn = lambda name: js.split(f"function {name}(", 1)[1].split("\n}", 1)[0] if f"function {name}(" in js else ""
    group = fn("thAutoGroup")
    check("170: Make sends From, and its count is every statement with All statements",
          "from: whole ? 'all' : 'board' });" in group and "(whole || thOnCanvas(TH.v, key))" in group)

    node = shutil.which("node")
    if not node:
        skip("170: From in node", "no node on this machine")
    else:
        script = scratch / "aiboard-from.js"
        script.write_text(support.i18n_js() + js + r"""
const els = {};
const opts = [{ dataset: { from: 'all' } }, { dataset: { from: 'board' } }];
for (const o of opts) { o.on = null; o.classList = { toggle: (c, on) => { o.on = on; } }; o.setAttribute = () => {}; }
function $(id) { return els[id] || (els[id] = { id, hidden: true, textContent: '', title: '' }); }
globalThis.document = { querySelectorAll: () => opts };
const RESTART_LINE = 'Restart the server to finish this update.';
const out = {};
TH.meta = { id: 'v3', name: 'Board 3' };
TH.aiFrom = 'all';
thAiFromDraw();
out.all = [$('th-aicard-title').textContent, $('th-from-board').textContent, opts[0].on, opts[1].on];
TH.aiFrom = 'board';
thAiFromDraw();
out.board = [$('th-aicard-title').textContent, opts[0].on, opts[1].on];
let asked = 0;
globalThis.api = async () => { asked += 1; return {}; };
Object.assign(TH, { live: true, busy: false, ai: { on: true }, fromAll: false, aiFrom: 'all' });
thAutoGroup().then(() => {
  out.old = [$('th-aicard-said').hidden, $('th-aicard-said').textContent, asked];
  console.log(JSON.stringify(out));
});
""", encoding="utf-8")
        run = subprocess.run([node, str(script)], capture_output=True, text=True, encoding="utf-8")
        out = json.loads(run.stdout) if run.returncode == 0 and run.stdout.strip() else {}
        check("170: in node, All statements in front of a server from before From says to restart in the card and asks nothing",
              out.get("old") == [False, "Restart the server to finish this update.", 0], str(out.get("old")))
