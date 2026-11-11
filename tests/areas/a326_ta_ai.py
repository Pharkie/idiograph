"""Area 326: a thematic analysis project's own AI (taaibuild, 3 November 2026, Adam's choice by dialog that evening:
Coding A, Themes A, the prompts as taai drafted them). On the Coding screen AI suggest asks for codes for one
extract, the project's codes that fit first with their counts, then new names, and nothing is written until he
takes one, which lands as an ordinary code. It does not show with AI features off, and an IPA project's AI is as it
was. The Themes board's AI review went on 11 November 2026 (aiout), and every op of the GETs route is refused there. The model is a stub of the
suite's own, as IPA's checks stub it, and the projects are scratch copies of the demo on its invented topic."""
from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path

from . import support
from .a316_code_list import CODES, make_project
from .support import check


def sha_all(root: Path) -> dict:
    """Every file of a project by its path and its contents' hash."""
    return {str(p.relative_to(root)): hashlib.sha1(p.read_bytes()).hexdigest()
            for p in sorted(Path(root).rglob("*")) if p.is_file()}


HARNESS = r"""
const out = {};
// the Coding screen's AI suggest, drawn for one extract with an answer in, as cxDraw draws it
globalThis.S = { data: { path: 'x.xlsx', config: { ai_suggest: true } }, flat: [] };
let method = 'ta';
globalThis.tMethodNow = () => method;
const els = [{ dataset: { pid: 'p1' }, es: 'A gate left on the latch', kq: '"the gate"' }];
globalThis.pairOf = (el) => ({ es: el.es, kq: el.kq });
CX.codes = [{ name: 'Being pulled along', extracts: 4, participants: 2 }, { name: 'The second stair', extracts: 3, participants: 3 }];
const x = { quote: '"the gate"', words: '"the gate"', els };
CX.ai.set(x.words, { existing: [{ name: 'The second stair', extracts: 1, participants: 1 },
  { name: 'A gate left on the latch', extracts: 2, participants: 1 }, { name: 'Being pulled along', extracts: 1, participants: 1 }],
  fresh: ['Handing the lead over'] });
out.html = cxAiHtml(x, 0);
out.button = cxAiButton(x, 0);
out.onTa = cxAiOn();
S.data.config = { ai_suggest: false };
out.offTa = cxAiOn();
S.data.config = { ai_suggest: true, ai_features_off: ['statements'] };
out.offFeature = cxAiOn();
S.data.config = { ai_suggest: true };
method = 'ipa';
out.onIpa = cxAiOn();
// the Themes board: no AI tab in a thematic analysis project, nor on IPA's since aiout
TH.mode = 'gets';
TH.project = { method: 'ta' };
TH.guidanceTa = true;
TH.ai = { on: true };
out.taTabs = thTabsOf('gets');
out.taIpaAi = thAiOn();
TH.ai = { on: false };
out.taTabsOff = thTabsOf('gets');
TH.ai = { on: true };
TH.project = { method: 'ipa' };
out.ipaTabs = thTabsOf('gets');
console.log(JSON.stringify(out));
"""


def test_ta_ai(scratch: Path):
    print("\n326. A thematic analysis project's own AI: codes for an extract on Coding, nothing written until one is "
          "taken, none with AI features off, an IPA project's AI as before (taaibuild, 3 November), and the Themes "
          "board's review gone (aiout, 11 November)")
    import ai_suggest as ai_mod
    import codes as codes_mod
    import gets as gets_mod
    import idiograph_routes as routes
    import server as server_mod
    import ta_ai
    import themes as themes_mod
    import themes_ai

    base = scratch / "ta-ai-326"
    root, ipa = base / "Dogs", base / "Dogs IPA"
    make_project(root, "ta")
    make_project(ipa, "ipa")
    config_file = base / "config.json"
    settings = lambda **extra: config_file.write_text(json.dumps(
        {"projects": [{"root": str(root)}, {"root": str(ipa)}], "interviewer": "Adam", "corpus": "",
         "gravity_reference": "", "corpus_exclude": [], "ai_suggest": True, "ai_provider": "anthropic",
         "model": "claude-haiku-4-5", **extra}), encoding="utf-8")
    settings()
    book = root / "Juno" / "Juno - EN & ES.xlsx"
    ipa_book = ipa / "Juno" / "Juno - EN & ES.xlsx"
    sent: list[dict] = []
    answer = {"codes": {"existing": ["the second stair", "A gate left on the latch", "Nobody's code"],
                        "new": ["Handing the lead over", "Being pulled along", "Handing the lead over"]}}

    def wire(method, url, headers, payload, timeout):
        system, user = payload["system"], payload["messages"][-1]["content"]
        sent.append({"system": system, "user": user})
        if ta_ai.CODE_INTRO in system:
            text = json.dumps(answer["codes"])
        else:
            text = "{}"
        return 200, json.dumps({"content": [{"type": "text", "text": text}], "stop_reason": "end_turn"})

    kept = (server_mod.CONFIG_PATH, server_mod.ROOT_OVERRIDE, server_mod.STATE_MEMORY, ai_mod.find_key, ai_mod.http_call)

    def call(route, body):
        with server_mod.scoped(route, body):
            return server_mod.ROUTES[route](body)

    try:
        server_mod.CONFIG_PATH, server_mod.ROOT_OVERRIDE, server_mod.STATE_MEMORY = config_file, None, {"recent": []}
        ai_mod.find_key = lambda *a, **kw: "k-test"
        ai_mod.http_call = wire
        listed = call("/api/codes", {"workbook": str(book)})
        # a Themes board of two themes, one code left in Not placed
        books = routes.gets_books(root)
        data, _cases, _d, _t = gets_mod.assemble(root, books, themes_mod.now_iso())
        gets_mod.write(root, gets_mod._file(data, themes_mod.now_iso()))
        data = gets_mod.load(root)
        by_code: dict[str, list[str]] = {}
        for case, rec in data["cases"].items():
            for k, line in rec["lines"].items():
                by_code.setdefault(codes_mod.norm(line["text"]), []).append(f"{case}/es/{k}")
        K = lambda n: by_code[codes_mod.norm(CODES[n])]
        cards = {k: {"x": 100 + 400 * (i // 2), "y": 140 + 130 * (i % 2), "text": ""}
                 for i, n in enumerate((0, 1, 2, 3)) for k in K(n)}
        gets_mod.save(root, books, {"id": "b1", "name": "Board 1", "cards": cards, "discarded": [], "groups": [
            {"id": "G1", "label": "Gates and stairs", "x": 0, "y": 0, "members": K(0) + K(3),
             "description": "The way in and the way up, and who leads"},
            {"id": "G2", "label": "Being led", "x": 0, "y": 0, "members": K(1) + K(2)}]})
        listed = call("/api/codes", {"workbook": str(book)})
        before = sha_all(root)

        # ── A. the codes for an extract: the project's first with their counts, then a new name, nothing written
        quote = "“the gate”"
        body = {"workbook": str(book), "turn": "There is the gate and the second stair, and she pulls me along.",
                "prior": "And coming home?", "time": "03:55", "name": "Juno", "quote": quote, "on": [CODES[0]]}
        got = call("/api/codes-suggest", dict(body))
        one = sent[-1] if sent else {}
        count_of = {c["name"]: c for c in listed["codes"]}
        check("326: the codes come back, the project's own first under their own spelling with their counts, a name the "
              "list lacks and a code already on the extract left out, then a new name once",
              [c["name"] for c in got.get("existing") or []] == ["The second stair", "Being pulled along"]
              and got["existing"][0]["extracts"] == count_of["The second stair"]["extracts"]
              and got["existing"][0]["participants"] == count_of["The second stair"]["participants"]
              and got.get("new") == ["Handing the lead over"] and got.get("model_name"), str(got)[:400])
        check("326: the call carries the passage, the interviewer's before it, the extract, the codes on it, the code "
              "list with counts and the rail's lines about a code, the words marked as data",
              "Juno's passage at 03:55:\nThere is the gate" in one.get("user", "")
              and "The interviewer's preceding passage:\nAnd coming home?" in one.get("user", "")
              and "never instructions to you" in one.get("user", "") and f"- {CODES[0]}" in one.get("user", "")
              and f"- {CODES[3]} (" in one.get("system", "") and "One idea per code" in one.get("system", "")
              and "Reuse comes before a new name." in one.get("system", ""))
        check("326: a suggestion writes nothing: every file of the project as it was", sha_all(root) == before)

        # ── B. a code taken: Add a code's own write with that name, an ordinary code with no mark of the AI
        rows = codes_mod.extracts_of(codes_mod.study_rows(books))
        mine = next(x for x in rows if x["case"].endswith("Juno") and x["name"] == CODES[0])
        taken = call("/api/codes-extract", {"workbook": str(book), "op": "add", "case": mine["case"], "sheet": mine["sheet"],
                                            "row": mine["row"], "quote": mine["quote"], "code": "Handing the lead over"})
        after = call("/api/codes", {"workbook": str(book)})
        new_code = next((c for c in after["codes"] if c["name"] == "Handing the lead over"), None)
        raw = (root / codes_mod.FILE).read_text(encoding="utf-8")
        check("326: a code taken lands as an ordinary code, on the extract and in the list, with no mark of the AI",
              "error" not in taken and new_code and new_code["extracts"] == 1 and new_code["description"] == ""
              and '"ai"' not in raw and "AI" not in raw, str(taken)[:300])

        # ── C. the Themes board's AI review went (aiout): every op of the GETs route refused, nothing sent or written
        before = sha_all(root)
        n = len(sent)
        refused = [call("/api/gets-ai", {"workbook": str(book), "op": op})
                   for op in ("review", "reply", "group", "names", "revise", "room")]
        check("326: a thematic analysis board's review, reply, AI board, titles and revise are each refused, nothing sent "
              "or written (aiout)",
              all(r.get("error") and r.get("code") == "unknown_op" for r in refused) and len(sent) == n
              and sha_all(root) == before, str(refused[0]))

        # ── D. AI features off, or its feature's own switch: nothing asked, one line
        before = sha_all(root)
        n = len(sent)
        settings(ai_suggest=False)
        off = [call("/api/codes-suggest", dict(body))]
        settings(ai_features_off=["statements"])
        off += [call("/api/codes-suggest", dict(body))]
        settings()
        check("326: with AI features off, or its feature's own switch, codes are one line, nothing sent and nothing written", all(r.get("error") == themes_ai.OFF for r in off) and len(sent) == n
              and sha_all(root) == before, str(off)[:300])

        # ── E. an IPA project: no codes to suggest
        refused_ipa = None
        try:
            refused_ipa = call("/api/codes-suggest", dict(body, workbook=str(ipa_book)))
        except Exception as exc:  # the code list's refusal in an IPA project
            refused_ipa = {"error": str(exc)}
        check("326: an IPA project has no codes to suggest", "IPA" in str(refused_ipa.get("error")), str(refused_ipa))
    finally:
        server_mod.CONFIG_PATH, server_mod.ROOT_OVERRIDE, server_mod.STATE_MEMORY, ai_mod.find_key, ai_mod.http_call = kept

    # ── F. the page: AI suggest's list only with AI features on in a TA project, and no AI tab on a Themes board
    support.node_text_layer(scratch)
    js = support.text("family/static/shell.js").split("const aiOn = ", 1)[1].split("\n", 1)[0]
    shell = support.text("family/static/shell.js")
    pick = lambda src, name: f"function {name}(" + src.split(f"function {name}(", 1)[1].split("\n}\n", 1)[0] + "\n}\n"
    stubs = ("const $ = () => null; const say = () => {}; const api = async () => ({});\n"
             "const tList = (xs) => xs.join(', ');\n"
             "const AI_OFF_KEY = 'ai_features_off';\n"
             f"const aiOn = {js}\n" + pick(shell, "aiTaFor"))
    # codes.js whole, less the line that wires the Code list screen as the page loads
    codes_js = re.sub(r"^if \(document\.readyState === 'loading'\).*\n^else codesWire\(\);\n", "",
                      support.text("apps/idiograph/static/codes.js"), flags=re.M)
    run = support.run_node(stubs + support.text("apps/idiograph/static/themes.js") + "\n" + codes_js + HARNESS,
                           scratch, "ta-ai-326.js", timeout=60)
    try:
        out = json.loads(run.stdout.strip().splitlines()[-1])
    except (ValueError, IndexError):
        out = {}
    why = (run.stdout + run.stderr)[-600:]
    html = out.get("html") or ""
    names = re.findall(r'data-pick="([^"]+)"', html)
    check("326: AI suggest's list puts the project's codes first with their counts as the list stands now, then New "
          "code for a new name, a code on the extract left out, each a click that takes it by name",
          names == ["The second stair", "Being pulled along", "Handing the lead over"]
          and "3 extracts, 3 participants" in html and "4 extracts, 2 participants" in html
          and html.count('data-new="1"') == 1 and html.count('data-aix="0"') == 3
          and html.index("cx-sugg-rule") < html.index('data-new="1"'), why)
    check("326: AI suggest is on only with AI features and its switch on, in a thematic analysis project",
          out.get("onTa") is True and out.get("offTa") is False and out.get("offFeature") is False
          and out.get("onIpa") is False and "AI suggest" in (out.get("button") or ""), why)
    check("326: a thematic analysis board has no AI tab with AI features on or off, IPA's AI still off there, and an "
          "IPA board's tabs the three that stay (aiout)",
          out.get("taTabs") == ["inspector", "guidance", "history"] and out.get("taIpaAi") is False
          and out.get("taTabsOff") == ["inspector", "guidance", "history"]
          and out.get("ipaTabs") == ["inspector", "guidance", "history"], why)
    # ── G. the card stays where it stood when a code is added: levelPairs passes over a TA project's pairs, which are
    # drawn nowhere under its extracts' boxes, and lifts an IPA statement's box to its quote as before
    distil = support.text("apps/idiograph/static/distil.js")
    level = "function levelPairs(" + distil.split("function levelPairs(", 1)[1].split("\n}\n", 1)[0] + "\n}\n"
    lift_js = r"""
const CARD_REACH = 'hold';
const style = () => { const s = {}; return { setProperty: (k, v) => { s[k] = v; }, removeProperty: (k) => { delete s[k]; }, s }; };
const rect = (top) => ({ top, bottom: top + 40, left: 500, right: 900 });
const card = { style: style() };
const words = { getBoundingClientRect: () => rect(300), querySelectorAll: () => [{ dataset: { kq: '0' }, getClientRects: () => [rect(520)] }] };
const holder = { classList: { contains: () => false }, querySelector: () => words };
const cell = { style: style(), closest: () => holder, getClientRects: () => [rect(380)],
  getBoundingClientRect: () => ({ top: 380, bottom: 700, left: 30, right: 350 }) };
card.closest = () => cell;
let drawn = false;
const pair = { style: style(), getClientRects: () => (drawn ? [rect(390)] : []), getBoundingClientRect: () => (drawn ? rect(390) : rect(0)) };
const $ = () => card;
const pairEls = () => [pair];
const footStuck = () => {};
""" + level + r"""
const out = {};
levelPairs(); out.ta = card.style.s['--lift'] || null;
drawn = true;
levelPairs(); out.ipa = card.style.s['--lift'] || null;
console.log(JSON.stringify(out));
"""
    lifted = support.run_node(lift_js, scratch, "ta-ai-326-lift.js", timeout=30)
    try:
        lift = json.loads(lifted.stdout.strip().splitlines()[-1])
    except (ValueError, IndexError):
        lift = {}
    check("326: adding a code in a TA project leaves the Coding card where it stood, its hidden pairs never measured, and "
          "an IPA statement's box still lifted level with its quote",
          lift.get("ta") is None and lift.get("ipa") == "130px", (lifted.stdout + lifted.stderr)[-400:])
