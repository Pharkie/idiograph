from __future__ import annotations

import inspect
import json

import ai_suggest as ai_mod

from . import support

from .support import check
import idiograph_routes
import statement_prompts


def test_ai_settings(scratch):
    print("\n36. The model, the provider, the test bench and the settings panel (items 51 to 54)")
    import server as server_mod
    static = server_mod.HERE / "static"
    js = support.text("family/static/shell.js", "apps/idiograph/static/distil.js")

    def answer(body, status=200):
        return status, json.dumps(body)

    def text_reply(obj, stop="end_turn", thinking=True):
        blocks = [{"type": "thinking", "thinking": "", "signature": "sig"}] if thinking else []
        blocks.append({"type": "text", "text": json.dumps(obj)})
        return {"content": blocks, "stop_reason": stop}

    # ── A. the Anthropic request, built to the current models
    ids = [m["id"] for m in ai_mod.ANTHROPIC_MODELS]
    banned = ("temperature", "top_p", "top_k", "thinking")
    bodies = {m: ai_mod.anthropic_payload("sys", "user", m) for m in ids + ["claude-some-later-model"]}
    check("no request carries temperature, top_p, top_k or thinking, on any model",
          all(not any(k in body for k in banned) for body in bodies.values()),
          "each model thinks or not as it does by default")
    check("no request prefills an assistant turn",
          all([msg["role"] for msg in body["messages"]] == ["user"] for body in bodies.values()))
    check("the request is model, ceiling, system and messages and nothing else",
          all(set(body) == {"model", "max_tokens", "system", "messages"} for body in bodies.values()))
    check("a model that thinks by default gets room for it, one that does not keeps the 600 ceiling",
          bodies["claude-opus-5-5"]["max_tokens"] == ai_mod.THINKING_MAX_TOKENS
          and bodies["claude-fable-5-1"]["max_tokens"] == ai_mod.THINKING_MAX_TOKENS
          and bodies["claude-sonnet-5-5"]["max_tokens"] == ai_mod.THINKING_MAX_TOKENS
          and bodies["claude-haiku-4-5"]["max_tokens"] == 600
          and bodies["claude-opus-4-8"]["max_tokens"] == 600
          and bodies["claude-some-later-model"]["max_tokens"] == ai_mod.THINKING_MAX_TOKENS,
          "a model not in the table is given the room in case")

    calls = []

    def recorder(reply):
        def send(method, url, headers, payload, timeout):
            calls.append({"method": method, "url": url, "headers": dict(headers or {}),
                          "payload": payload, "timeout": timeout})
            return reply(len(calls))
        return send

    reply = recorder(lambda n: answer(text_reply(
        {"tags": ["shaking", "voice"], "candidates": [f"draft {n}a", f"draft {n}b"]})))
    out = statement_prompts.suggest("My hands were shaking.", prior="And then?", key="k-test", transport=reply,
                         model="claude-opus-5-5")
    check("the answer is read from the text blocks, with a thinking block in front of them",
          out == {"tags": ["shaking", "voice"], "candidates": ["draft 2a", "draft 2b"]}, str(out))
    check("both passes go to the Messages API with the version header, the key in its header alone",
          len(calls) == 2 and all(c["method"] == "POST" and c["url"] == ai_mod.ENDPOINT
                                  and c["headers"].get("anthropic-version") == "2023-06-01"
                                  and c["headers"].get("x-api-key") == "k-test"
                                  and "k-test" not in json.dumps(c["payload"]) for c in calls))
    check("a model that thinks waits longer, one that does not keeps the short clock",
          calls[0]["timeout"] == ai_mod.THINKING_TIMEOUT
          and ai_mod.complete("s", "u", key="k", model="claude-haiku-4-5",
                              transport=recorder(lambda n: answer(text_reply({"tags": ["a"]}))))
          and calls[-1]["timeout"] == ai_mod.TIMEOUT)
    check("thinking text never reaches the answer",
          ai_mod.message_text({"content": [{"type": "thinking", "thinking": "private"},
                                           {"type": "text", "text": "public"}]}) == "public")

    calls.clear()
    refused = statement_prompts.suggest("a turn", key="k", transport=recorder(lambda n: answer(
        {"content": [], "stop_reason": "refusal", "stop_details": {"type": "refusal", "category": "cyber"}})))
    check("a refusal is one error line, and no second pass follows it",
          refused == {"error": ai_mod.REFUSED} and len(calls) == 1, str(refused))
    cut = statement_prompts.suggest("a turn", key="k", transport=recorder(lambda n: answer(
        {"content": [{"type": "text", "text": '{"tags": ["a"], "candidates": ["b'}], "stop_reason": "max_tokens"})))
    check("an answer cut off by its ceiling says so, rather than that it was not JSON",
          cut == {"error": ai_mod.TOO_LONG}, str(cut))
    empty = ai_mod.complete("s", "u", key="k", transport=recorder(lambda n: answer(
        {"content": [{"type": "thinking", "thinking": ""}], "stop_reason": "max_tokens"})))
    check("a ceiling spent on thinking with no text written is the same line", empty == {"error": ai_mod.TOO_LONG})

    # ── B. the model list
    plain = ai_mod.plain_model("claude-haiku-4-5-20251001")
    check("a stored dated id maps to the plain one, and a plain id stays as it is",
          plain == "claude-haiku-4-5" and ai_mod.plain_model("claude-opus-5-5") == "claude-opus-5-5"
          and ai_mod.model_name("claude-haiku-4-5-20251001") == "Haiku 4.5", plain)
    calls.clear()
    live = ai_mod.anthropic_models("k-test", transport=recorder(lambda n: answer({"data": [
        {"id": "claude-haiku-4-5-20251001", "display_name": "Claude Haiku 4.5"},
        {"id": "claude-3-haiku-20240307", "display_name": "Claude Haiku 3"},
        {"id": "claude-sonnet-5-5", "display_name": "Claude Sonnet 5.5"},
        {"id": "claude-sonnet-4-5-20250929", "display_name": "Claude Sonnet 4.5"},
        {"id": "claude-opus-5-5", "display_name": "Claude Opus 5.5"}], "has_more": False})))
    check("the live list is cut to the table and put in its order, dated ids matched",
          [m["id"] for m in live["models"]] == ["claude-opus-5-5", "claude-sonnet-5-5", "claude-haiku-4-5"]
          and live["source"] == "live", str([m["id"] for m in live["models"]]))
    check("the live list is one GET to /v1/models with the key and version headers",
          len(calls) == 1 and calls[0]["method"] == "GET"
          and calls[0]["url"].startswith(ai_mod.MODELS_ENDPOINT) and calls[0]["payload"] is None
          and calls[0]["headers"].get("x-api-key") == "k-test"
          and calls[0]["headers"].get("anthropic-version") == "2023-06-01")
    check("nothing about the key comes back in the list", "k-test" not in json.dumps(live))
    full = [m["id"] for m in ai_mod.model_options(ai_mod.ANTHROPIC_MODELS)]
    failed = ai_mod.anthropic_models("k", transport=recorder(lambda n: (500, "")))
    gone = ai_mod.anthropic_models("k", transport=recorder(lambda n: (0, "")))
    junk = ai_mod.anthropic_models("k", transport=recorder(lambda n: (200, "not json")))
    calls.clear()
    keyless = ai_mod.anthropic_models(None, transport=recorder(lambda n: (200, "{}")))
    check("a failed live list falls back to the whole built-in table and says why",
          [m["id"] for m in failed["models"]] == full and failed["source"] == "builtin"
          and "500" in failed["note"] and "did not answer" in gone["note"]
          and [m["id"] for m in junk["models"]] == full)
    check("with no key the built-in table stands, and no call is made",
          [m["id"] for m in keyless["models"]] == full and keyless["source"] == "builtin" and not calls)

    # ── C. Ollama, entirely through a fake: it is not installed on this machine
    calls.clear()
    tags = ai_mod.local_models("http://127.0.0.1:11434/", transport=recorder(lambda n: answer(
        {"models": [{"name": "llama3.1:8b", "size": 1}, {"name": "qwen2.5:7b"}]})))
    check("Ollama's pulled models are listed from /api/tags",
          tags["running"] is True and [m["id"] for m in tags["models"]] == ["llama3.1:8b", "qwen2.5:7b"]
          and calls[0]["method"] == "GET" and calls[0]["url"] == "http://127.0.0.1:11434/api/tags", str(tags))
    down = ai_mod.local_models(None, transport=recorder(lambda n: (0, "")))
    check("Ollama not there is said, with what to do",
          down["running"] is False and down["models"] == []
          and down["note"] == ("Ollama is not installed or not running. Install it from ollama.com, pull a "
                               "model (for example `ollama pull llama3.1:8b`), and it appears here."))
    bare = ai_mod.local_models(None, transport=recorder(lambda n: answer({"models": []})))
    check("Ollama running with nothing pulled says that instead", bare["running"] and bare["note"] == ai_mod.LOCAL_EMPTY)
    check("the address comes from config, and anything but an http address falls back",
          ai_mod.local_base("http://10.0.0.5:11434/") == "http://10.0.0.5:11434"
          and ai_mod.local_base("file:///etc") == ai_mod.LOCAL_URL and ai_mod.local_base("") == ai_mod.LOCAL_URL)
    calls.clear()
    local_reply = recorder(lambda n: answer({"model": "llama3.1:8b", "done": True, "done_reason": "stop",
                                             "message": {"role": "assistant", "content": json.dumps(
                                                 {"tags": ["hands"], "candidates": [f"local {n}"]})}}))
    local = statement_prompts.suggest("My hands were shaking.", prior="And?", key=None, transport=local_reply,
                           provider="local", model="llama3.1:8b", local_url="http://127.0.0.1:11434")
    chat = calls[0] if calls else {}
    check("a local suggestion needs no key and runs both passes on the local model",
          local == {"tags": ["hands"], "candidates": ["local 2"]} and len(calls) == 2, str(local))
    check("the local call is a POST to /api/chat, not streamed, held to JSON, system then user",
          chat.get("method") == "POST" and chat.get("url") == "http://127.0.0.1:11434/api/chat"
          and chat["payload"]["stream"] is False and chat["payload"]["format"] == "json"
          and chat["payload"]["model"] == "llama3.1:8b"
          and [m["role"] for m in chat["payload"]["messages"]] == ["system", "user"]
          and "My hands were shaking." in chat["payload"]["messages"][1]["content"])
    check("nothing about the key goes to the local model",
          all("x-api-key" not in c["headers"] and "k-test" not in json.dumps(c) for c in calls))
    check("a local provider with no model chosen says so before any call",
          statement_prompts.suggest("a turn", provider="local", model="", transport=local_reply) == {"error": ai_mod.NO_LOCAL_MODEL})
    check("Ollama gone mid-suggestion is one line",
          statement_prompts.suggest("a turn", provider="local", model="m", transport=recorder(lambda n: (0, "")))
          == {"error": ai_mod.LOCAL_DOWN})
    check("a local answer cut at its length says so",
          statement_prompts.suggest("a turn", provider="local", model="m", transport=recorder(lambda n: answer(
              {"message": {"content": '{"tags": ["a'}, "done_reason": "length"}))) == {"error": ai_mod.TOO_LONG})

    # ── D. the server: routing, the bench, the model list and the cache
    defaults = server_mod.defaults()
    check("config carries the provider, the model, the local address and the local model, with defaults",
          defaults["ai_provider"] == "anthropic" and defaults["model"] == "claude-haiku-5-5"
          and defaults["local_url"] == "http://127.0.0.1:11434" and defaults["local_model"] == ""
          and all(k in server_mod.merge_config({}) for k in ("ai_provider", "local_url", "local_model")))
    found_keys = []
    real = (ai_mod.find_key, ai_mod.http_call, ai_mod.anthropic_models, ai_mod.local_models,
            server_mod.CONFIG_PATH, server_mod.save_json, server_mod.ROOT_OVERRIDE)
    scratch_config = scratch / "ai-settings" / "config.json"
    scratch_config.parent.mkdir(parents=True, exist_ok=True)
    try:
        ai_mod.find_key = lambda *a, **kw: found_keys.append(1) or "k-test"
        server_mod.CONFIG_PATH = scratch_config
        scratch_config.write_text(json.dumps({"ai_suggest": True, "model": "claude-haiku-4-5-20251001", "ai_provider": "local",
                                              "local_model": "llama3.1:8b"}), encoding="utf-8")
        cfg = server_mod.config()
        route = server_mod.ai_route(cfg)
        check("a local route never looks the key up",
              route["provider"] == "local" and route["key"] is None and route["model"] == "llama3.1:8b"
              and not found_keys)
        route = server_mod.ai_route(cfg, {"provider": "anthropic", "model": "claude-sonnet-5-5",
                                          "ai_prompt": "Bench prompt. JSON."})
        check("the bench may carry its own provider, model and prompt for one call",
              route["provider"] == "anthropic" and route["model"] == "claude-sonnet-5-5"
              and route["key"] == "k-test" and route["template"] == "Bench prompt. JSON." and found_keys)
        route = server_mod.ai_route(server_mod.merge_config({}), {"provider": "elsewhere"})
        check("an unknown provider falls back to Anthropic and the default model",
              route["provider"] == "anthropic" and route["model"] == "claude-haiku-5-5")

        sample = idiograph_routes.api_suggest_sample({})
        check("the bench's turn is Juno's, from the demo transcript, with the interviewer's before it",
              sample.get("name") == "Juno" and sample["turn"].startswith(statement_prompts.SAMPLE_OPENS)
              and sample["prior"] == "What was happening in you, on that drive?"
              and sample["text"].endswith(sample["turn"]) and f"{sample['interviewer']}: " in sample["text"],
              sample.get("time", ""))
        decoy = scratch / "ai-settings" / "root"
        (decoy / "source").mkdir(parents=True, exist_ok=True)
        (decoy / "source" / "Juno - interview.csv").write_text(
            "Name,Timestamp,Transcript\nAdam,00:00:00,Asked\nJuno,00:00:05,A decoy turn from a case root\n",
            encoding="utf-8")
        server_mod.ROOT_OVERRIDE = str(decoy)
        again = idiograph_routes.api_suggest_sample({"path": str(decoy / "source" / "Juno - interview.csv")})
        check("the sample is read from the demo folder and never from a case root",
              again["turn"] == sample["turn"] and "decoy" not in again["text"]
              and server_mod.SAMPLE_CSV == server_mod.DEMO_DIR / "source" / "Juno - interview.csv"
              and server_mod.SAMPLE_CSV.resolve().is_relative_to(server_mod.HERE.resolve())
              and "root" not in inspect.getsource(idiograph_routes.api_suggest_sample).split('"""')[-1])
        server_mod.ROOT_OVERRIDE = real[6]

        split = statement_prompts.split_sample(sample["text"])
        check("the box splits into the turn, the turn before it and the speaker",
              split["name"] == "Juno" and split["turn"] == sample["turn"] and split["prior"] == sample["prior"])
        check("a box with no names in it is all turn",
              statement_prompts.split_sample("just words\non two lines") == {"prior": "", "turn": "just words on two lines", "name": ""})

        writes = []
        server_mod.save_json = lambda *a, **kw: writes.append(a)
        sent = []

        def wire(method, url, headers, payload, timeout):
            sent.append({"url": url, "payload": payload, "headers": headers})
            body = {"tags": ["hands", "voice"], "candidates": ["Hands shake, a bright voice not her own"]}
            if "/api/chat" in url:
                return 200, json.dumps({"message": {"content": json.dumps(body)}, "done_reason": "stop"})
            return 200, json.dumps(text_reply(body))

        ai_mod.http_call = wire
        bench = idiograph_routes.api_suggest_sample({"text": sample["text"], "provider": "anthropic",
                                               "model": "claude-haiku-4-5"})
        check("the bench runs the same two passes and names the model and the seconds",
              bench.get("candidates") == ["Hands shake, a bright voice not her own"]
              and bench.get("tags") == ["hands", "voice"] and bench.get("model") == "claude-haiku-4-5"
              and bench.get("model_name") == "Haiku 4.5" and isinstance(bench.get("seconds"), float)
              and len(sent) == 2 and all(s["url"] == ai_mod.ENDPOINT for s in sent), str(bench))
        first_user = sent[0]["payload"]["messages"][0]["content"]
        check("the bench sends Juno's passage with the interviewer's passage before it, the prompt saying passage "
              "(16 October)",
              sample["turn"] in first_user and sample["prior"] in first_user and "Juno's passage" in first_user)
        sent.clear()
        bench_local = idiograph_routes.api_suggest_sample({"text": sample["text"], "provider": "local",
                                                     "local_model": "llama3.1:8b"})
        check("the bench on Local goes to Ollama and names the local model",
              bench_local.get("model") == "llama3.1:8b" and "on this machine" in bench_local.get("model_name", "")
              and len(sent) == 2 and all("/api/chat" in s["url"] for s in sent), str(bench_local))
        sent.clear()
        plain_ask = idiograph_routes.api_suggest({"turn": "My hands were shaking.", "prior": "And?"})
        check("the button under the statement field takes the provider from config, Local here",
              plain_ask.get("candidates") and all("/api/chat" in s["url"] for s in sent) and len(sent) == 2)
        check("nothing the bench or the button says is written anywhere", not writes)

        counted = []

        def fake_list(key, **kw):
            counted.append(key)
            return {"models": ai_mod.model_options(ai_mod.ANTHROPIC_MODELS[-1:]), "source": "live", "note": ""}

        ai_mod.anthropic_models = fake_list
        ai_mod.local_models = lambda url=None, **kw: {"running": False, "models": [], "note": ai_mod.LOCAL_MISSING,
                                                       "url": ai_mod.local_base(url)}
        server_mod.forget_models()
        models = server_mod.api_models({})
        server_mod.api_models({})
        check("/api/models answers both providers' lists, the choice and the local status",
              models["provider"] == "local" and models["model"] == "claude-haiku-4-5"
              and models["local_model"] == "llama3.1:8b" and models["anthropic"]["source"] == "live"
              and models["local"]["running"] is False and models["local"]["note"] == ai_mod.LOCAL_MISSING,
              "the stored dated id comes back plain")
        check("the live list is asked for once and held", len(counted) == 1 and "k-test" not in json.dumps(models))
        server_mod.api_models({"fresh": "1"})
        check("a fresh ask goes past the held list", len(counted) == 2)
        real_save = ai_mod.save_key
        ai_mod.save_key = lambda value, **kw: {"saved": True}
        try:
            server_mod.api_key({"key": "k-new"})
        finally:
            ai_mod.save_key = real_save
        server_mod.api_models({})
        check("saving a key lets the held list go", len(counted) == 3)

        # settings: the new keys land, an unknown provider is refused, a dated id is kept
        server_mod.save_json = real[5]
        scratch_config.write_text(json.dumps({"model": "claude-haiku-4-5-20251001"}), encoding="utf-8")
        saved = server_mod.api_settings({"ai_provider": "local", "local_model": "qwen2.5:7b",
                                         "model": "claude-haiku-4-5"})["config"]
        on_disk = json.loads(scratch_config.read_text(encoding="utf-8"))
        check("a save stores the provider and the local model",
              on_disk["ai_provider"] == "local" and on_disk["local_model"] == "qwen2.5:7b"
              and saved["ai_provider"] == "local")
        check("the plain id of the stored dated model leaves the stored id as it was",
              on_disk["model"] == "claude-haiku-4-5-20251001")
        server_mod.api_settings({"ai_provider": "elsewhere", "model": "claude-sonnet-5-5"})
        on_disk = json.loads(scratch_config.read_text(encoding="utf-8"))
        check("an unknown provider is never stored, and a new model is",
              on_disk["ai_provider"] == "local" and on_disk["model"] == "claude-sonnet-5-5")
        check("a save with fields the server does not know about does not throw",
              "config" in server_mod.api_settings({"some_later_field": True, "nudges": {}}))
    finally:
        (ai_mod.find_key, ai_mod.http_call, ai_mod.anthropic_models, ai_mod.local_models,
         server_mod.CONFIG_PATH, server_mod.save_json, server_mod.ROOT_OVERRIDE) = real
        server_mod.forget_models()
    check("the routes carry the bench and the model list",
          server_mod.ROUTES["/api/suggest-sample"] is idiograph_routes.api_suggest_sample
          and server_mod.ROUTES["/api/models"] is server_mod.api_models)
    check("a smoke or trial server can keep its settings in a file of its own",
          '"--config"' in inspect.getsource(server_mod.main) and "CONFIG_PATH = Path(args.config)" in inspect.getsource(server_mod.start_up))

    # ── E. the settings panel
    # the family's screens' categories in screenPane, Idiograph's in its own, distilScreenPane, since the fifth build
    screen_pane = "".join(js.split(f"function {name}(", 1)[1].split("\n}", 1)[0]
                          for name in ("screenPane", "distilScreenPane") if f"function {name}(" in js)
    check("116: the chosen category holds while the card is open, and the next open goes to the screen's own",
          # the tab's session holds the way back, Home's fold and, since 22 October, whether the mark has come
          # in on Home (HOME_MARK_KEY), and since 28 October the one reopening of Settings on General after the
          # Language row's reload (LANGUAGE_AGAIN), never a Settings pane
          all("RETURN_KEY" in ln or "HOME_KEY" in ln or "HOME_MARK_KEY" in ln or "LANGUAGE_AGAIN" in ln
              for ln in js.splitlines() if "sessionStorage" in ln)
          and "PANE_KEY" not in js and "storedPane" not in js
          and "showPane(pane || screenPane());" in js
          and "if (onScreen('sift-search')) return 'databases';" in screen_pane
          and "if (onScreen('sift')) return 'sift';" in screen_pane
          and "if (onScreen('trace')) return 'trace';" in screen_pane
          and "if (onScreen('themes')) return 'pets';" in screen_pane
          and "if (onScreen('work')) return 'statements';" in screen_pane and "return appsSay('screenPane') || 'general';" in screen_pane)
    check("the arrow keys walk the categories", "function paneKeys(" in js and "'keydown', paneKeys" in js)
    saver = js.split("async function saveSettings(", 1)[1].split("\n}", 1)[0]
    check("the provider and the model go only to a server that sent the lists",
          "if (S.models) aiSaveBody(body);" in saver
          and "body.ai_provider = providerNow();" in js.split("function aiSaveBody(", 1)[1].split("\n}", 1)[0])
    bench_fn = js.split("async function runBench(", 1)[1].split("\n}", 1)[0]
    check("the bench shows the concepts, the candidates, the model and the seconds, and writes nothing",
          "'/api/suggest-sample'" in bench_fn and "data.model_name" in bench_fn and "seconds" in bench_fn
          and "bench-tags" in bench_fn and "bench-candidates" in bench_fn
          and "'/api/settings'" not in bench_fn and "takeCandidate" not in bench_fn)
