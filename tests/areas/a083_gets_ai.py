from __future__ import annotations

import json
import shutil

import openpyxl

import ai_suggest as ai_mod
import workbook as wb_mod

from . import support
from .support import DEMO_QUESTION, DEMO_SHEET, check, demo_copy, skip
import idiograph_routes


def test_gets_ai(scratch):
    print("\n83. AI suggest GET titles on GETs, the GETs sections of the guidance and their Guidance tab, names that "
          "are just names (184) and an agent's board marked with AI. The GETs screen's New AI board, review and revise "
          "went on 11 November 2026 (aiout), and an op of theirs is refused")
    import subprocess
    import cli
    import gets as gets_mod
    import server as server_mod
    import themes as themes_mod
    import themes_ai

    js = support.text("apps/idiograph/static/themes.js")
    guidance = support.source("apps/idiograph/pet_guidance.md").read_text(encoding="utf-8")
    fn = lambda src, name: src.split(f"function {name}(", 1)[1].split("\n}", 1)[0] if f"function {name}(" in src else ""

    # ── A. the GETs sections of the guidance, numbered as its sections are, and the PETs titles' prompt as it was
    rules4, questions5 = themes_ai.guidance_items(4), themes_ai.guidance_items(5)
    check("83: the guidance holds section 4, what a GET is and its rules, and section 5, the questions of a GETs board, "
          "with Sources after them, the PETs reviewer's questions gone with the review (aiout)",
          [n for n, _ in rules4] == list(range(1, 10)) and [n for n, _ in questions5] == list(range(1, 16))
          and guidance.index("## 3. Rules") < guidance.index("## 4. Group") < guidance.index("## 5. Questions") < guidance.index("## 6. Sources")
          and "Questions a reviewer asks of a grouping" not in guidance
          and (themes_ai.GETS, themes_ai.GETS_QUESTIONS) == (4, 5) and (themes_ai.WHAT_A_THEME, themes_ai.RULES) == (1, 3),
          str(len(rules4)))
    stripped = scratch / "guidance-pets-only.md"
    stripped.write_text(guidance.split("## 4. Group experiential themes", 1)[0] + "## 6. Sources\n", encoding="utf-8")
    held = themes_ai.GUIDANCE
    now = themes_ai.names_system(DEMO_QUESTION)
    try:
        themes_ai.GUIDANCE = stripped
        without = themes_ai.names_system(DEMO_QUESTION)
    finally:
        themes_ai.GUIDANCE = held
    check("83: the PETs titles' prompt carries exactly the sections it carried, the same with or without the GETs sections",
          now == without and not any(text in now for _, text in rules4 + questions5))

    # ── B. the fixture: three invented cases from the demo, one with no PETs yet
    root = scratch / "gets-ai-root"
    shutil.rmtree(root, ignore_errors=True)
    books = {name: demo_copy(root, name, f"{name} - EN & ES.xlsx") for name in ("Wren", "Ash", "Moss")}
    (root / "idiograph-project.json").write_text(json.dumps({"name": "Scratch", "research_question": DEMO_QUESTION}),
                                                 encoding="utf-8")
    read = themes_mod.read_cards(books["Wren"])
    keys = [c["key"] for c in read["cards"]]
    for name in ("Wren", "Ash"):
        book = openpyxl.load_workbook(books[name], rich_text=True)
        ws = book[DEMO_SHEET]
        cols = wb_mod.detect_columns(ws)
        row = read["cards"][0]["row"]
        ws.cell(row, cols["kq"]).value = '"the stair at six"\n\n"she is there first"' if name == "Wren" else '"a lead by the door"'
        book.save(books[name])
        book.close()

    def board(vid, name, groups):
        b = themes_mod.blank_version(themes_mod.read_cards(books["Wren"])["cards"])
        b.update(id=vid, name=name, groups=groups)
        return b

    wren_pets = [{"id": "g1", "label": "Mornings that start at the stair", "note": "An invented note on mornings.",
                  "members": keys[0:2] + ["g3"], "x": 0, "y": 0},
                 {"id": "g2", "label": "Walks that close the day", "members": keys[4:6], "x": 0, "y": 400},
                 {"id": "g3", "label": "Early light in the hall", "members": keys[2:4], "x": 0, "y": 200}]
    ash_pets = [{"id": "g1", "label": "A lead by the door", "members": keys[0:3], "x": 0, "y": 0},
                {"id": "g2", "label": "Evenings kept for two", "members": keys[6:8], "x": 0, "y": 300}]
    for name, groups in (("Wren", wren_pets), ("Ash", ash_pets)):
        themes_mod.write(books[name], {"schema": 2, "case": name, "workbook": books[name].name, "current": "v1",
                                       "chosen": "v1", "boards": [board("v1", "Board 1", groups)],
                                       "complete": {"at": "2026-10-05T10:00:00+01:00", "board": "v1", "name": "Board 1"}})
    saved = (server_mod.CONFIG_PATH, server_mod.ROOT_OVERRIDE, server_mod.STATE_MEMORY, ai_mod.find_key, ai_mod.http_call)
    config_path = scratch / "gets-ai" / "config.json"
    config_path.parent.mkdir(parents=True, exist_ok=True)
    settings = lambda **extra: config_path.write_text(json.dumps(
        {"ai_suggest": True, "ai_provider": "anthropic", "model": "claude-haiku-4-5",
         "pets_provider": "anthropic", "pets_model": "claude-opus-5-5", **extra}), encoding="utf-8")
    settings()
    sent = []
    book_sha = lambda: {n: p.read_bytes() for n, p in books.items()}
    themes_sha = lambda: {n: themes_mod.themes_path(p).read_bytes() for n, p in books.items() if themes_mod.themes_path(p).exists()}
    W, A = "Wren", "Ash"

    def wire(method, url, headers, payload, timeout):
        system, user = payload["system"], payload["messages"][-1]["content"]
        sent.append({"system": system, "user": user, "model": payload["model"]})
        text = json.dumps({"names": ["Mornings that turn round the dog", "A day that starts at the stair",
                                     "Mornings that turn round the dog", "Light first, then the walk"]})
        return 200, json.dumps({"content": [{"type": "text", "text": text}], "stop_reason": "end_turn"})

    gfile = gets_mod.gets_path(root)
    gdata = lambda: json.loads(gfile.read_text(encoding="utf-8"))
    any_book = str(books["Wren"])
    try:
        server_mod.CONFIG_PATH = config_path
        server_mod.ROOT_OVERRIDE = str(root)
        server_mod.STATE_MEMORY = {"recent": []}
        ai_mod.find_key = lambda *a, **kw: "k-test"
        ai_mod.http_call = wire
        before_books, before_themes = book_sha(), themes_sha()

        # ── C. the switch off, and what the screen is told
        settings(ai_suggest=False)
        off = idiograph_routes.api_gets_ai({"workbook": any_book, "op": "names"})
        opened = idiograph_routes.api_gets({"workbook": any_book})
        check("83: with the switch off the titles are one line, nothing sent and nothing written",
              off == {"error": themes_ai.OFF} and not sent and not gfile.exists() and opened["ai"]["on"] is False)
        settings()
        opened = idiograph_routes.api_gets({"workbook": any_book})
        check("83: /api/gets says the switch and the PETs model, no GETs limit, and the Guidance tab's GETs sections",
              opened["ai"] == {"on": True, "provider": "anthropic", "model_name": "Opus 5.5"}
              and not any(k in opened for k in ("gets_ai", "from_all", "revisable"))
              and [g["heading"] for g in opened["guidance"]] == ["Group experiential themes", "Questions a reviewer asks of a GETs board"]
              and opened["guidance"][0]["lines"][0].startswith("A group experiential theme (GET) is a pattern")
              and len(opened["guidance"][0]["lines"]) == 10 and len(opened["guidance"][1]["lines"]) == 15 and not gfile.exists())

        # his own first board on GETs, with a participant note, a sticky note and a row note, none of which may go
        idiograph_routes.api_gets_save({"workbook": any_book, "version": dict(
            {k: x for k, x in opened["version"].items() if k != "v"}, cards={c["key"]: {"x": c["x"], "y": c["y"], "text": c["text"]} for c in opened["cards"]}
            | {f"{W}/pn/1": {"x": 900, "y": 900, "text": "An invented participant note, private"}},
            groups=[{"id": "G1", "label": "Mornings kept round the dog", "note": "His invented note on the GET",
                     "members": [f"{W}/g1", f"{A}/g1", f"{W}/pn/1"], "x": 0, "y": 0},
                    {"id": "G2", "label": "Walks at the end of the day", "members": [f"{W}/g2", "G3"], "x": 0, "y": 600},
                    {"id": "G3", "label": "Light in the hall", "members": [f"{W}/g3"], "x": 0, "y": 700}],
            discarded=[f"{A}/g2"], picks={}, notes=[{"id": "n1", "text": "An invented sticky note, private", "colour": "yellow", "x": 50, "y": 50}],
            rows={"G1": {W: {"quote": "", "note": "An invented row note, private"}}})})
        board_id = gdata()["boards"][0]["id"]
        before = gfile.read_bytes()

        # aiout: a new AI board, the room line, a review, a reply and a revise are each an op the help does not do
        gone = [idiograph_routes.api_gets_ai({"workbook": any_book, "op": op, "version": board_id, "text": "words"})
                for op in ("group", "room", "review", "reply", "revise")]
        check("83: aiout, every op but the titles is refused as one the help does not do, nothing sent or written",
              all(g.get("code") == "unknown_op" for g in gone) and not sent and gfile.read_bytes() == before
              and book_sha() == before_books and themes_sha() == before_themes, str(gone[0]))

        # ── I. AI suggest GET titles
        named = idiograph_routes.api_gets_ai({"workbook": any_book, "op": "names", "version": board_id, "group": "G1"})
        user, system = sent[0]["user"], sent[0]["system"]
        check("83: three titles for a GET from what sits under it across the cases, the cases named, its count against the minimum",
              named["names"] == ["Mornings that turn round the dog", "A day that starts at the stair", "Light first, then the walk"]
              and "GET: Mornings kept round the dog" in user and f"- PET {W}/g1 (Wren): Mornings that start at the stair" in user
              and f"- PET {A}/g1 (Ash): A lead by the door" in user and "It holds material from 2 of the 3 participants, and his minimum is 3." in user
              and "Nothing under it from: Moss." in user and "- Untitled" not in user and named["model_name"] == "Opus 5.5", user[:400])
        check("83: the other GETs' titles go so the three stay distinct, with the title rules of section 4 and no other",
              "The other GETs on the board, so the titles sit beside them:\n- Walks at the end of the day\n- Light in the hall" in user
              and all(f"{n}. {t}" in system for n, t in rules4 if n in (5, 6, 7, 8))
              and not any(f"{n}. {t}" in system for n, t in rules4 if n not in (5, 6, 7, 8))
              and "Offer three titles for the GET he has gathered" in system and "close to the participants' own words" in system)
        check("83: participant notes, sticky notes and row notes never go to a model, and the titles write nothing",
              "private" not in json.dumps(sent) and gfile.read_bytes() == before and book_sha() == before_books)
        check("83: a GET no longer on the board, or with nothing under it, asks nothing",
              idiograph_routes.api_gets_ai({"workbook": any_book, "op": "names", "version": board_id, "group": "G9"}) == {"error": themes_ai.NO_SUCH_GET}
              and len(sent) == 1)

        # ── L. 184 on GETs: a duplicate is his, and New board names the next free number
        copy = idiograph_routes.api_gets_ops({"workbook": any_book, "op": "duplicate", "id": board_id})
        twin = gdata()["boards"][-1]
        check("83: 184, a duplicate is his and carries no with AI",
              "made" not in twin and "with_ai" not in next(v for v in copy["versions"] if v["id"] == twin["id"]))
        plain = idiograph_routes.api_gets_ops({"workbook": any_book, "op": "new"})
        check("83: 184, New board on GETs names the next free number too",
              plain["version"]["name"] == f"Board {len(plain['versions'])}")
    finally:
        server_mod.CONFIG_PATH, server_mod.ROOT_OVERRIDE, server_mod.STATE_MEMORY, ai_mod.find_key, ai_mod.http_call = saved

    # ── M. 182 and 184 on the PETs screen
    proot = scratch / "gets-ai-pets"
    shutil.rmtree(proot, ignore_errors=True)
    work = demo_copy(proot, "Juno", "Juno - EN & ES.xlsx")
    (proot / "idiograph-project.json").write_text(json.dumps({"name": "Scratch", "research_question": DEMO_QUESTION,
                                                              "agents": {"allowed": True, "at": "2026-10-05T10:00:00+01:00"}}),
                                                  encoding="utf-8")
    pread = themes_mod.read_cards(work)
    pk = [c["key"] for c in pread["cards"]]
    old_board = themes_mod.blank_version(pread["cards"])
    old_board.update(id="v2", name="AI board 3", discarded=[pk[-1]], ai={"discarded": {pk[-1]: "about the weather"}},
                     note="Proposed by Haiku 4.5 from Board 1 on 2 October 2026 at 12:02, up to 5 PETs. 1 PET, 2 placed, 1 discarded, 0 unplaced.",
                     groups=[{"id": "g1", "label": "Mornings", "members": pk[:2], "x": 0, "y": 0}])
    agent_board = dict(themes_mod.blank_version(pread["cards"]), id="v3", name="Board 3",
                       made={"by": "agent", "tool": "Claude Code", "request": "one board", "at": "2026-10-05T11:00:00+01:00"})
    themes_mod.write(work, {"schema": 2, "case": "Juno", "workbook": work.name, "current": "v1",
                            "boards": [themes_mod.blank_version(pread["cards"]), old_board, agent_board]})
    old_kept = json.loads(json.dumps(themes_mod.load(work)["boards"][1]))
    pfile = lambda: json.loads(themes_mod.themes_path(work).read_text(encoding="utf-8"))
    try:
        server_mod.CONFIG_PATH = config_path
        server_mod.ROOT_OVERRIDE = str(proot)
        server_mod.STATE_MEMORY = {"recent": []}
        settings()
        opened = idiograph_routes.api_themes({"workbook": str(work)})
        listed = {v["name"]: v.get("with_ai") for v in opened["versions"]}
        check("83: 184, an old AI board keeps its name and is an ordinary board now, an agent's carries with AI from its "
              "mark, his own nothing (aiout)",
              listed == {"Board 1": None, "AI board 3": None,
                         "Board 3": {"by": "agent", "said": "Claude Code in a conversation", "edited": False}}, str(listed))
        idiograph_routes.api_themes_versions({"workbook": str(work), "op": "switch", "id": "v2"})
        shown = idiograph_routes.api_themes({"workbook": str(work)})
        body = dict({k: x for k, x in shown["version"].items() if k != "v"},
                    cards={c["key"]: {"x": c["x"], "y": c["y"], "text": c["text"]} for c in shown["cards"]},
                    groups=shown["groups"], discarded=shown["discarded"], picks=shown["picks"],
                    ai={"discarded": shown["discard_reasons"]}, notes=[])
        idiograph_routes.api_themes_save({"workbook": str(work), "version": body})
        check("83: 182, an old AI board's discards and their reasons stay in its bin as they are through a save",
              pfile()["boards"][1]["discarded"] == old_kept["discarded"] and pfile()["boards"][1]["ai"] == old_kept["ai"]
              and pfile()["boards"][1]["name"] == "AI board 3" and shown["discard_reasons"] == {pk[-1]: "about the weather"})
        twin = idiograph_routes.api_themes_versions({"workbook": str(work), "op": "duplicate"})
        fresh = idiograph_routes.api_themes_versions({"workbook": str(work), "op": "new"})
        check("83: 184, a duplicate is his with no with AI, and New board names the next free number",
              "with_ai" not in twin["version"]
              and "made" not in next(b for b in pfile()["boards"] if b["id"] == twin["version"]["id"])
              and fresh["version"]["name"] == "Board 5"
              and themes_mod.board_name([{"name": "Board 1"}, {"name": "Board 3"}]) == "Board 4"
              and themes_mod.board_name([{"name": "Board 2"}]) == "Board 3" and themes_mod.board_name([], "Mine") == "Mine",
              fresh["version"]["name"])
        switch = idiograph_routes.api_themes_cases({"workbook": str(work)})
        check("83: 184, the case switcher lists the agent's board's with AI after its name too",
              all("with_ai" in c or not c.get("board_name", "").startswith("Board 3") for c in switch["cases"]))
    finally:
        server_mod.CONFIG_PATH, server_mod.ROOT_OVERRIDE, server_mod.STATE_MEMORY, ai_mod.find_key, ai_mod.http_call = saved

    # ── N. 184, the command line's board new makes Board N, with AI
    croot = scratch / "gets-ai-cli"
    shutil.rmtree(croot, ignore_errors=True)
    cbook = demo_copy(croot, "Juno", "Juno - EN & ES.xlsx")
    (croot / "idiograph-project.json").write_text(json.dumps({"name": "Scratch", "research_question": DEMO_QUESTION,
                                                              "agents": {"allowed": True, "at": "2026-10-05T10:00:00+01:00"}}),
                                                  encoding="utf-8")
    cfg_file = scratch / "gets-ai-cli-config.json"
    cfg_file.write_text(json.dumps({"root": str(croot), "interviewer": "Adam"}), encoding="utf-8")
    spec = scratch / "gets-ai-board.json"
    spec.write_text(json.dumps({"pets": [{"title": "Mornings at the stair", "members": ["S1", "S2"]}],
                                "not_placed": {"S3": "It fits no PET"}}), encoding="utf-8")
    code, out, err = cli.run(["--root", str(croot), "--config", str(cfg_file), "board", "new", "Juno", "--from", str(spec),
                              "--note", "One board", "--tool", "Claude Code"])
    stored = themes_mod.load(cbook)
    newest = stored["boards"][-1] if stored else {}
    check("83: 184, the command line's board new makes Board N with AI, an agent's mark carrying its hash, Board 1 "
          "on a case with no themes file (95)",
          code == 0 and out.startswith("Made Board 1 on Juno") and newest.get("name") == "Board 1"
          and len(stored["boards"]) == 1
          and newest["made"]["by"] == "agent" and len(newest["made"].get("hash") or "") == 64
          and themes_mod.summary(newest)["with_ai"]["said"] == "Claude Code in a conversation, from all statements", out + err)

    # ── O. the page
    check("83: the titles are the one AI press on PETs and GETs, through one helper that asks the PETs route or on GETs its own",
          "api(thAiPath()," in fn(js, "thNamesAsk") and js.count("api(thAiPath(),") == 1
          and "const thAiPath = () => (TH.mode === 'gets' ? '/api/gets-ai' : '/api/themes-ai');" in js
          and js.count("'/api/gets-ai'") == 2 and "needsRestart(err)" in fn(js, "thNamesAsk"))
    panel = fn(js, "gtPanelDraw")
    check("83: AI suggest GET titles in a GET's Inspector, the PETs control's words changed, its one step of undo the rename's",
          "thNamesHtml(item, { unit: owner !== undefined ? t('themes.unit.sub') : thGetWord() })" in panel
          and "thDone(before, t('themes.step.renamed')" in fn(js, "thNameApply") and "thLeftOutHtml(v, item.id, owner)" in panel)
    node = shutil.which("node")
    if not node:
        skip("83: the page's new parts in node", "no node on this machine")
    else:
        script = scratch / "gets-ai.js"
        script.write_text(support.i18n_js() + js + r"""
const els = {};
function $(id) { return els[id] || (els[id] = { id, hidden: true, textContent: '', title: '' }); }
const esc = (s) => String(s).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
const escAttr = (s) => esc(s).replace(/"/g, '&quot;');
const out = {};
out.mark = [thWithAi(null), thWithAi({ said: 'Opus 5.5, from all statements', edited: false }),
  thWithAi({ said: 'Opus 5.5, from Board 2', edited: true })];
const v = { cards: { a: {}, b: {} }, groups: [], discarded: ['b'], ai: { discarded: { a: 'off the question', b: 'binned' } } };
out.why = [thWhyHtml(v, 'a', undefined), thWhyHtml(v, 'a', 'g1'), thWhyHtml(v, 'b', undefined)];
TH.mode = 'gets'; out.gets = thAiPath(); TH.mode = 'pets'; out.pets = thAiPath();
console.log(JSON.stringify(out));
""", encoding="utf-8")
        run = subprocess.run([node, str(script)], capture_output=True, text=True, encoding="utf-8")
        out = json.loads(run.stdout) if run.returncode == 0 and run.stdout.strip() else {}
        check("83: in node, the reason under a card in Not placed, and none once placed or in the bin",
              out.get("why") == ['<p class="th-pile-why th-card-why">off the question</p>', "", ""], str(out.get("why")))
        check("83: in node, the GETs route on GETs and the PETs one on PETs, and with AI after an agent's board, edited or not",
              out.get("gets") == "/api/gets-ai" and out.get("pets") == "/api/themes-ai" and out.get("mark", [None])[0] == ""
              and "with AI" in out.get("mark", ["", ""])[1] and "edited by you since" in out.get("mark", ["", "", ""])[2], str(out))
