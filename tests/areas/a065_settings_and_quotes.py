from __future__ import annotations

import json
import shutil

import ai_suggest as ai_mod
import nudges

from . import support
from .support import check, demo_copy, skip
import idiograph_routes
import statement_prompts


def test_settings_and_quotes(scratch):
    print("\n65. Settings' AI folded into Experiential statements and a model of the PETs screen's own (162), the "
          "test bench said to be invented data (163), an info mark on every nudge (164), the PET limit said as it "
          "works (165), and AI suggest sending the turn's key quotes (168)")
    import subprocess
    import server as server_mod
    import themes_ai

    app = support.text("family/static/shell.js", "apps/idiograph/static/distil.js")
    fn = lambda src, name: src.split(f"function {name}(", 1)[1].split("\n}", 1)[0]
    whole = lambda name: f"function {name}(" + fn(app, name) + "\n}"
    lines = app.splitlines()

    def const(name):
        """A top-level const of app.js, over as many lines as it runs to."""
        start = next(i for i, line in enumerate(lines) if line.startswith(f"const {name} = "))
        end = start
        while not lines[end].rstrip().endswith(";"):
            end += 1
        return "\n".join(lines[start:end + 1])

    # ── B. the PETs screen's own model (162)
    saver = fn(app, "saveSettings")
    check("162: Save sends pets_provider and pets_model as a pair, and only to a server that sent the lists",
          "if (S.models) aiSaveBody(body);" in saver and "body.pets_provider = own ? own.provider : '';" in fn(app, "aiSaveBody")
          and "body.pets_model = own ? own.model : '';" in fn(app, "aiSaveBody"))

    # the PETs select, its line and the key's place in node, on the lists as the server builds them
    tags = lambda method, url, headers, payload, timeout: (200, json.dumps({"models": [{"name": "llama3.1:8b"}, {"name": "qwen2.5:7b"}]}))
    down = lambda method, url, headers, payload, timeout: (0, "")
    lists = {"anthropic": {"models": ai_mod.model_options(ai_mod.ANTHROPIC_MODELS)},
             "local": ai_mod.local_models(None, transport=tags)}
    no_local = {"anthropic": lists["anthropic"], "local": ai_mod.local_models(None, transport=down)}
    haiku, opus = ai_mod.model_name("claude-haiku-4-5"), ai_mod.model_name("claude-opus-5-5")

    # ── C. the nudges, the limit and the quotes, from the page's own code
    node = shutil.which("node")
    out = None
    if not node:
        skip("162 to 168: the PETs select, the info marks, the limit and the quotes in node", "no node on this machine")
    else:
        source = "\n".join([const("esc"), const("escAttr"), const("keyHome"), const("PROVIDER_ROWS"), const("PROVIDER_NAMES"),
                            const("LOOPBACK"), const("providerNow"), const("rowsOf"), const("openaiShaped"), const("hostOf"),
                            const("whoOf"), const("otherModel"), const("petsProvider"), const("NUDGES"),
                            const("WORDS_DEFAULT"), const("WORDS_MIN"), const("WORDS_MAX"),
                            const("INFO_ICON"), const("capOf"), const("capNow"), const("CAP_LINES"), const("capStep"),
                            const("QUOTES_MAX"), const("QUOTE_CHARS")]
                           + [whole(n) for n in ("petsValue", "petsChoice", "modelLabel", "statementsLabel", "drawPetsNote", "drawKeyPlace",
                                                 "fillPetsModels", "nudgeRow", "capLine", "drawCap", "keyQuotes",
                                                 "suggestBody")])
        script = scratch / "settings-and-quotes.js"
        script.write_text(support.i18n_js() +
            "const els = {};\n"
            "function $(id) {\n"
            "  if (!els[id]) els[id] = { id, value: '', textContent: '', hidden: false, innerHTML: '', title: '', disabled: false,\n"
            "    parentNode: null, kids: [],\n"
            "    appendChild(c) { if (c.parentNode) c.parentNode.kids = c.parentNode.kids.filter((k) => k !== c); c.parentNode = this; this.kids.push(c); return c; },\n"
            "    after(n) { if (n.parentNode) n.parentNode.kids = n.parentNode.kids.filter((k) => k !== n); n.parentNode = this.parentNode; this.parentNode.kids.push(n); },\n"
            "    before(n) { this.after(n); } };\n"
            "  return els[id];\n"
            "}\n"
            "$('ai-settings').appendChild($('ai-choice')); $('ai-settings').appendChild($('ai-key'));\n"
            "const S = { models: null, data: { path: 'cases/Juno - EN & ES.xlsx' } };\n"
            + source + "\n"
            "const LISTS = " + json.dumps(lists) + ";\n"
            "const NO_LOCAL = " + json.dumps(no_local) + ";\n"
            "const options = () => [...$('set-pets-model').innerHTML.matchAll(/<option value=\"([^\"]*)\">([^<]*)<\\/option>/g)].map((m) => [m[1], m[2]]);\n"
            "const key = () => [$('ai-key').parentNode.id, $('ai-key').hidden];\n"
            "function state(provider, model, local, pets) {\n"
            "  $('set-provider').value = provider; $('set-model').value = model; $('set-local-model').value = local;\n"
            "  $('set-pets-model').value = pets; drawPetsNote();\n"
            "  return [$('pets-model-note').textContent, ...key()];\n"
            "}\n"
            "const out = {};\n"
            "S.models = LISTS;\n"
            "fillPetsModels(LISTS, ''); out.options = options(); out.chosen = $('set-pets-model').value;\n"
            "fillPetsModels(NO_LOCAL, ''); out.noLocal = options();\n"
            "fillPetsModels(LISTS, 'anthropic:claude-gone-1'); out.stored = options().slice(-1)[0]; out.storedChosen = $('set-pets-model').value;\n"
            "out.same = state('anthropic', 'claude-haiku-4-5', 'llama3.1:8b', '');\n"
            "out.own = state('anthropic', 'claude-haiku-4-5', 'llama3.1:8b', 'anthropic:claude-opus-5-5');\n"
            "out.localSame = state('local', 'claude-haiku-4-5', 'llama3.1:8b', '');\n"
            "out.localPetsAnthropic = state('local', 'claude-haiku-4-5', 'llama3.1:8b', 'anthropic:claude-opus-5-5');\n"
            "out.localBoth = state('local', 'claude-haiku-4-5', 'llama3.1:8b', 'local:qwen2.5:7b');\n"
            "out.anthropicPetsLocal = state('anthropic', 'claude-haiku-4-5', 'llama3.1:8b', 'local:qwen2.5:7b');\n"
            "out.back = state('local', 'claude-haiku-4-5', '', '');\n"
            "out.values = [petsValue({}), petsValue({ pets_provider: 'anthropic', pets_model: 'claude-opus-5-5' }),\n"
            "  petsValue({ pets_provider: 'anthropic', pets_model: '' }), petsValue({ pets_provider: 'elsewhere', pets_model: 'x' }),\n"
            "  petsValue({ pets_provider: 'local', pets_model: 'qwen2.5:7b' }), petsValue(undefined)];\n"
            "out.nudges = Object.entries(NUDGES).map(([k, [label, about]]) => [k, label, about, nudgeRow(k, label, about, k !== 'arrow')]);\n"
            "out.icon = INFO_ICON;\n"
            "out.lines = [2, 3, 4, 5, 6, 7, 8, 9].map((n) => capLine(n));\n"
            "drawCap(5); out.drawn = $('set-cap-line').textContent; capStep(1); out.stepped = $('set-cap-line').textContent;\n"
            "for (let k = 0; k < 9; k += 1) capStep(-1); out.floor = $('set-cap-line').textContent;\n"
            "out.quotes = keyQuotes('\"I needed the walk\"\\n\\n  \\u201cevery gate\\u201d  \\nplain words');\n"
            "out.empty = [keyQuotes(''), keyQuotes('  \\n \\n'), keyQuotes(undefined)];\n"
            "out.many = keyQuotes(Array.from({ length: 12 }, (_, i) => `\"q${i}\"`).join('\\n'));\n"
            "out.long = keyQuotes('\"' + 'y'.repeat(450) + '\"')[0].length;\n"
            "out.bodies = [suggestBody('t', 'p', '01:00', 'Juno'), suggestBody('t', 'p', '01:00', 'Juno', []),\n"
            "  suggestBody('t', 'p', '01:00', 'Juno', keyQuotes('\"every gate\"'))];\n"
            "console.log(JSON.stringify(out));\n", encoding="utf-8")
        run = subprocess.run([node, str(script)], capture_output=True, text=True, encoding="utf-8")
        if run.returncode != 0:
            check("162 to 168: the settings and the quotes run in node", False, run.stderr.strip()[:400])
        else:
            out = json.loads(run.stdout)

    if out:
        hints = [m["hint"] for m in lists["anthropic"]["models"]]
        check("162: the select's first option is Same as Experiential statements, the default, then every Anthropic model the statements' select offers, labelled as there",
              out["options"][0] == ["", "Same as Experiential statements"] and out["chosen"] == ""
              and [o[1] for o in out["options"][1:len(hints) + 1]] == hints
              and all(o[0] == f"anthropic:{m['id']}" for o, m in zip(out["options"][1:], lists["anthropic"]["models"])),
              str(out["options"][:3]))
        check("162: then the local models when Ollama answers, labelled as the local select labels them, and none when it does not",
              out["options"][len(hints) + 1:] == [["local:llama3.1:8b", "llama3.1:8b · on this machine"],
                                                  ["local:qwen2.5:7b", "qwen2.5:7b · on this machine"]]
              and out["noLocal"] == out["options"][:len(hints) + 1], str(out["options"][len(hints) + 1:]))
        check("162: a stored PETs model the lists no longer carry is kept and said to be",
              out["stored"] == ["anthropic:claude-gone-1", "claude-gone-1 · stored, not in this list"]
              and out["storedChosen"] == "anthropic:claude-gone-1", str(out["stored"]))
        check("162: the line names the model the PETs screen uses now, and follows the selects",
              out["same"][0] == f"Uses {haiku}, the Experiential statements model." and out["own"][0] == f"Uses {opus}."
              and out["localSame"][0] == "Uses llama3.1:8b on this machine, the Experiential statements model."
              and out["anthropicPetsLocal"][0] == "Uses qwen2.5:7b on this machine."
              and out["back"][0] == "Uses a local model, the Experiential statements model.",
              f"{out['same'][0]} / {out['own'][0]}")
        check("162: the settings' two keys read as one choice, and anything short of a provider and a model reads as the same",
              out["values"] == ["", "anthropic:claude-opus-5-5", "", "", "local:qwen2.5:7b", ""], str(out["values"]))

    # ── D. the routes and the saved keys, through a transport that stands in for the provider
    real = (server_mod.CONFIG_PATH, server_mod.ROOT_OVERRIDE, ai_mod.find_key, ai_mod.http_call)
    base = scratch / "settings-and-quotes"
    config_path = base / "config.json"
    root = base / "root"
    work = demo_copy(root, "Juno", "Juno - EN & ES.xlsx")
    sent, reply = [], ['{"groups": []}']

    def wire(method, url, headers, payload, timeout):
        sent.append({"url": url, "model": (payload or {}).get("model"),
                     "user": ((payload or {}).get("messages") or [{}])[-1].get("content", "")})
        if "/api/chat" in url:
            return 200, json.dumps({"message": {"content": reply[0]}, "done_reason": "stop"})
        return 200, json.dumps({"content": [{"type": "text", "text": reply[0]}], "stop_reason": "end_turn"})

    def settings(**extra):
        config_path.write_text(json.dumps({"ai_suggest": True, "ai_provider": "anthropic", "model": "claude-haiku-4-5",
                                           "local_model": "llama3.1:8b", **extra}), encoding="utf-8")

    on_disk = lambda: json.loads(config_path.read_text(encoding="utf-8"))
    turn = "We took the long way round the park, and she stopped at every gate. I think I needed the walk more than she did."
    quoted = ["I needed the walk more than she did", "every gate"]
    lead = statement_prompts.QUOTES_LEAD
    part = lead + "\n- I needed the walk more than she did\n- every gate"
    try:
        server_mod.CONFIG_PATH = config_path
        server_mod.ROOT_OVERRIDE = str(root)
        ai_mod.find_key = lambda *a, **kw: "k-test"
        ai_mod.http_call = wire
        settings()
        cfg = server_mod.config()
        check("162: a config from before the two keys reads them empty, and the PETs route is the statements route",
              cfg["pets_provider"] == "" and cfg["pets_model"] == "" and idiograph_routes.pets_choice(cfg) == {}
              and idiograph_routes.pets_route(cfg) == server_mod.ai_route(cfg)
              and server_mod.ai_state(cfg)["model_name"] == haiku)
        saved = server_mod.api_settings({"pets_provider": "anthropic", "pets_model": "claude-opus-5-5"})
        check("162: Save writes pets_provider and pets_model to the settings file, and they are read back",
              on_disk()["pets_provider"] == "anthropic" and on_disk()["pets_model"] == "claude-opus-5-5"
              and server_mod.config()["pets_model"] == "claude-opus-5-5" and saved["config"]["pets_provider"] == "anthropic"
              and saved["ai"]["model_name"] == opus)
        server_mod.api_settings({"round_minutes": 10})
        kept = on_disk()
        cleared = []
        for body in ({"pets_provider": "", "pets_model": ""}, {"pets_provider": "elsewhere", "pets_model": "x"},
                     {"pets_provider": "local", "pets_model": "  "}, {"pets_model": "claude-opus-5-5"}):
            server_mod.api_settings({"pets_provider": "anthropic", "pets_model": "claude-opus-5-5"})
            server_mod.api_settings(body)
            cleared.append((on_disk()["pets_provider"], on_disk()["pets_model"]))
        check("162: a save without them keeps them, and anything short of a known provider with a model clears both",
              kept["pets_provider"] == "anthropic" and kept["pets_model"] == "claude-opus-5-5"
              and cleared == [("", "")] * 4, str(cleared))

        settings(pets_provider="anthropic", pets_model="claude-opus-5-5", ai_provider="local")
        cfg = server_mod.config()
        stmt, own = server_mod.ai_route(cfg), idiograph_routes.pets_route(cfg)
        check("162: PETs on an Anthropic model and statements on Local: the PETs route is Anthropic with the key, the statements route Local",
              (own["provider"], own["model"], own["key"]) == ("anthropic", "claude-opus-5-5", "k-test")
              and (stmt["provider"], stmt["model"], stmt["key"]) == ("local", "llama3.1:8b", None)
              and own["template"] == stmt["template"] and own["local_url"] == stmt["local_url"]
              and server_mod.ai_state(cfg)["model_name"] == opus)
        settings(pets_provider="local", pets_model="qwen2.5:7b")
        cfg = server_mod.config()
        own = idiograph_routes.pets_route(cfg)
        check("162: PETs on a local model and statements on Anthropic: the PETs route is Local with no key",
              (own["provider"], own["model"], own["key"]) == ("local", "qwen2.5:7b", None)
              and server_mod.ai_route(cfg)["model"] == "claude-haiku-4-5"
              and server_mod.ai_state(cfg)["model_name"] == "qwen2.5:7b on this machine")

        settings(pets_provider="anthropic", pets_model="claude-opus-5-5")
        sent.clear()
        idiograph_routes.api_themes_ai({"workbook": str(work), "op": "group"})
        idiograph_routes.api_themes_ai({"workbook": str(work), "op": "names", "statements": ["Mornings kept for the dog"],
                                  "label": "Mornings"})
        asked_pets = [c["model"] for c in sent]
        opened = idiograph_routes.api_themes({"workbook": str(work)})
        sent.clear()
        idiograph_routes.api_suggest_sample({"turn": turn, "prior": "", "time": "", "name": "Juno"})
        bench = [c["model"] for c in sent]
        sent.clear()
        idiograph_routes.api_suggest({"turn": turn, "prior": "", "time": "", "name": "Juno", "path": str(work)})
        button = [c["model"] for c in sent]
        check("162: with a PETs model set, the AI board and the titles ask it and the card names it, the bench and AI suggest the statements model",
              asked_pets == ["claude-opus-5-5", "claude-opus-5-5"] and opened["ai"]["model_name"] == opus
              and bench and set(bench) == {"claude-haiku-4-5"} and button and set(button) == {"claude-haiku-4-5"},
              f"{asked_pets} {bench} {button}")
        settings()
        sent.clear()
        idiograph_routes.api_themes_ai({"workbook": str(work), "op": "group"})
        check("162: with none set they ask the statements model, as before",
              [c["model"] for c in sent] == ["claude-haiku-4-5"]
              and idiograph_routes.api_themes({"workbook": str(work)})["ai"]["model_name"] == haiku)

        # ── E. the key quotes in the request (168)
        reply[0] = json.dumps({"tags": ["the walk"], "candidates": ["Walk as hers more than the dog's", "Gates as pauses"]})

        def asked(extra):
            sent.clear()
            answer = idiograph_routes.api_suggest({"turn": turn, "prior": "How was the morning?", "time": "03:12", "name": "Juno",
                                             "path": str(work), **extra})
            return answer, [c["user"] for c in sent]

        answer, users = asked({"quotes": quoted})
        check("168: /api/suggest sends the quotes in both passes, the drafts' and the critic's, and the answer counts them",
              len(users) == 2 and all(part in u for u in users) and answer.get("quotes") == 2
              and answer.get("candidates") and "Your drafts for this passage:" in users[1], str(answer)[:200])
        bad = [asked({"quotes": q}) for q in ("I needed the walk", [1, 2], ["a", 3], {"q": "a"}, None, [])] + [asked({})]
        check("168: quotes that are not a list of strings, or none, are ignored, as an old page is answered",
              all(len(us) == 2 and all(lead not in u for u in us) and "quotes" not in a for a, us in bad))
        answer, users = asked({"quotes": ["z" * 500] + [f"q{i}" for i in range(12)]})
        check("168: ten quotes at most go, each cut at 400 characters",
              users and all("- " + "z" * 400 + "\n" in u and "z" * 401 not in u for u in users)
              and all(f"- q{i}\n" in users[0] for i in range(9)) and "- q9" not in users[0]
              and answer.get("quotes") == 10)
        sent.clear()
        idiograph_routes.api_suggest_sample({"turn": turn, "prior": "", "time": "", "name": "Juno", "quotes": quoted})
        check("168: the test bench sends none, and its route reads none",
              sent and all(lead not in c["user"] for c in sent)
              and "suggestBody(text, $('bench-prior').value, S.bench.time, S.bench.name)" in fn(app, "runBench")
              and "quotes" not in fn(app, "runBench") and "with your key quotes" not in fn(app, "runBench"))
    finally:
        server_mod.CONFIG_PATH, server_mod.ROOT_OVERRIDE, ai_mod.find_key, ai_mod.http_call = real

    plain1 = statement_prompts.user_message(turn, "How was the morning?", "03:12", "Juno")
    plain2 = statement_prompts.user_message(turn, "How was the morning?", "03:12", "Juno", ["Draft one"])
    with1 = statement_prompts.user_message(turn, "How was the morning?", "03:12", "Juno", None, quoted)
    with2 = statement_prompts.user_message(turn, "How was the morning?", "03:12", "Juno", ["Draft one"], quoted)
    check("168: user_message with no quotes is as it was, the part nowhere",
          lead not in plain1 + plain2 and plain1.endswith(statement_prompts.DRAFT_ASK) and plain2.endswith(statement_prompts.CRITIC_ASK)
          and statement_prompts.user_message(turn, "", "", "", None, []) == statement_prompts.user_message(turn))
    check("168: with quotes the part stands after the whole turn and before the ask in the drafts' pass, and nothing else changes",
          part in with1 and with1.index(turn) < with1.index(part) < with1.index(statement_prompts.DRAFT_ASK)
          and with1.replace("\n\n" + part, "") == plain1)
    check("168: and in the critic's pass after the turn, before the drafts and the ask",
          part in with2 and with2.index(turn) < with2.index(part) < with2.index("Your drafts for this passage:")
          < with2.index(statement_prompts.CRITIC_ASK) and with2.replace("\n\n" + part, "") == plain2)
    if out:
        check("168: in node, the field's lines go one quote each, the quote marks off, the empty ones dropped",
              out["quotes"] == ["I needed the walk", "every gate", "plain words"] and out["empty"] == [[], [], []],
              str(out["quotes"]))
        check("168: in node, ten at most and each cut at 400 characters",
              out["many"] == [f"q{i}" for i in range(10)] and out["long"] == 400)
        check("168: in node, an empty field sends no quotes key at all, and quotes ride beside the four fields and the case",
              "quotes" not in out["bodies"][0] and "quotes" not in out["bodies"][1]
              and out["bodies"][2] == {"turn": "t", "prior": "p", "time": "01:00", "name": "Juno",
                                       "path": "cases/Juno - EN & ES.xlsx", "quotes": ["every gate"]})

    # ── G. every nudge explained (164)
    if out:
        rows = {k: (label, about, row) for k, label, about, row in out["nudges"]}
        check("164: an info mark and a tooltip for every nudge the server checks, in its order",
              list(rows) == list(nudges.CHECKS), str(list(rows)))

    # ── H. the PET limit said as it works (165)
    check("165: limit_line asks for one fewer than the limit or the limit, and one more only with a reason",
          all(f"Make between {n - 1} and {n} themes. Make {n + 1} only when" in themes_ai.limit_line(n) for n in range(2, 10)))
