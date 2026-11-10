"""Area 344: the OpenAI-style providers' call (aiwire, 8 November 2026, the first build of aiprov's plan). One
wire shape, a chat completion and a model list, with a table of presets for Mistral, Google Gemini, OpenAI,
Azure OpenAI (address, deployment, api-version), Another service by its address and LM Studio. Against a
loopback stub of this check's own, one path per provider, through the app's stub hook
`IDIOGRAPH_SEARCH_STUB` and a keychain held in memory: the request each provider is sent (path, header, model,
messages, no temperature), a suggestion's round trip, the model list, a refused key, a missing deployment, a
rate limit, a 500, an answer that is no JSON, one cut at its length, a timeout and nothing answering, an
address refused unless https or on this computer, each provider's key its own keychain item, the key never in
an answer or a log line, and the AI switch off making no call. Every key, model, deployment and host here is
invented, and nothing leaves loopback."""
from __future__ import annotations

import io
import json
import logging
import os
import threading
import time
import urllib.parse
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

import ai_suggest as ai_mod
import server as server_mod

from .support import check

SUGGESTION = {"tags": ["pace", "quiet"], "candidates": ["The street was slow and I walked with it"]}
HTTPS_LINE = "The address must start with https://, unless it is on this computer."
DEPLOYMENT = "deploy-344"
GOOD = {p: f"k-{p}-344" for p in ("mistral", "gemini", "openai", "azure", "other")}


class Stub:
    """What the stub provider has been asked, and how it answers each provider now."""

    def __init__(self):
        self.seen: list[dict] = []
        self.mode: dict[str, str] = {}

    def reset(self):
        self.seen.clear()
        self.mode.clear()


STATE = Stub()


class Provider(BaseHTTPRequestHandler):
    def _reply(self, status, body=b"", kind="application/json"):
        try:
            self.send_response(status)
            self.send_header("content-type", kind)
            self.end_headers()
            self.wfile.write(body)
        except OSError:
            pass                                  # a client that gave up on a slow answer

    def _auth_ok(self, provider):
        if provider == "lmstudio" or (provider == "other" and not (self.headers.get("authorization")
                                                                    or self.headers.get("api-key"))):
            return True
        want = GOOD[provider]
        return self.headers.get("authorization") == f"Bearer {want}" or self.headers.get("api-key") == want

    def _handle(self):
        parts = urllib.parse.urlparse(self.path)
        provider = parts.path.lstrip("/").split("/", 1)[0]
        length = int(self.headers.get("content-length") or 0)
        raw = self.rfile.read(length) if length else b""
        STATE.seen.append({"method": self.command, "path": parts.path, "query": parts.query, "provider": provider,
                           "headers": {k.lower(): v for k, v in self.headers.items()},
                           "body": json.loads(raw) if raw else None})
        mode = STATE.mode.get(provider, "ok")
        if mode == "slow":
            time.sleep(1.0)
        if mode in ("401", "404", "429", "500"):
            return self._reply(int(mode), b'{"error": "echoing the key would go here"}')
        if not self._auth_ok(provider):
            return self._reply(401)
        if parts.path.endswith("/models"):
            data = [{"id": "models/m-b-344"}, {"id": "m-a-344"}, {"id": "m-a-344"}]
            return self._reply(200, json.dumps({"object": "list", "data": data}).encode())
        if mode == "nonjson":
            return self._reply(200, b"<html>not json</html>", "text/html")
        text, finish = json.dumps(SUGGESTION), "stop"
        if mode == "length":
            text, finish = '{"tags": ["pa', "length"
        if mode == "emptylength":
            text, finish = "", "length"
        if mode == "filtered":
            text, finish = "", "content_filter"
        body = {"choices": [{"index": 0, "message": {"role": "assistant", "content": text}, "finish_reason": finish}]}
        return self._reply(200, json.dumps(body).encode())

    do_GET = do_POST = _handle

    def log_message(self, *_):
        pass


def test_openai_providers(scratch: Path):
    print("\n344. The OpenAI-style providers, against a stub on loopback: the call, the list, the lines, the keys, "
          "the switch")
    import idiograph_routes

    httpd = ThreadingHTTPServer(("127.0.0.1", 0), Provider)
    httpd.daemon_threads = True
    threading.Thread(target=httpd.serve_forever, kwargs={"poll_interval": 0.05}, daemon=True).start()
    base = f"http://127.0.0.1:{httpd.server_address[1]}"
    other_address = f"{base}/other/v1"
    was_env = os.environ.get(ai_mod.STUB_ENV)
    was_held = dict(ai_mod.STUB_KEYCHAIN.held)
    real_config = server_mod.CONFIG_PATH
    config_path = scratch / "openai-providers" / "config.json"
    config_path.parent.mkdir(parents=True, exist_ok=True)
    log = io.StringIO()
    handler = logging.StreamHandler(log)
    logging.getLogger().addHandler(handler)
    answers: list = []
    try:
        os.environ[ai_mod.STUB_ENV] = base
        run(base, other_address, config_path, answers, idiograph_routes)
    finally:
        logging.getLogger().removeHandler(handler)
        server_mod.CONFIG_PATH = real_config
        if was_env is None:
            os.environ.pop(ai_mod.STUB_ENV, None)
        else:
            os.environ[ai_mod.STUB_ENV] = was_env
        ai_mod.STUB_KEYCHAIN.held.clear()
        ai_mod.STUB_KEYCHAIN.held.update(was_held)
        httpd.shutdown()
        httpd.server_close()
    where = {"answers": json.dumps(answers), "log": log.getvalue()}
    leaked = [(w, k) for w, text in where.items() for k in GOOD.values() if k in text]
    check("344: no key is in any answer or any log line", not leaked, str(leaked))


def run(base, other_address, config_path, answers, idiograph_routes):
    def ask(provider, **kw):
        kw.setdefault("key", GOOD.get(provider))
        out = ai_mod.complete("Sys prompt.", "User words.", provider, kw.pop("model", None), **kw)
        answers.append(out)
        return out

    # ── A. the request each provider is sent
    shapes = {
        "mistral": ("/mistral/v1/chat/completions", "mistral-small-latest", "authorization", {}),
        "gemini": ("/gemini/v1beta/openai/chat/completions", "gemini-2.0-flash", "authorization", {}),
        "openai": ("/openai/v1/chat/completions", "gpt-4o-mini", "authorization", {}),
        "lmstudio": ("/lmstudio/v1/chat/completions", "local-model-344", None, {"model": "local-model-344"}),
        "other": ("/other/v1/chat/completions", "other-model-344", "authorization",
                  {"model": "other-model-344", "address": other_address}),
        "azure": (f"/azure/openai/deployments/{DEPLOYMENT}/chat/completions", DEPLOYMENT, "api-key",
                  {"address": "https://example-344.openai.azure.example", "deployment": DEPLOYMENT}),
    }
    for provider, (path, model, header, extra) in shapes.items():
        STATE.reset()
        got = ask(provider, **extra)
        sent = STATE.seen[0] if STATE.seen else {}
        body = sent.get("body") or {}
        check(f"344: {provider} round trip: one POST to {path}, the text back",
              got == {"text": json.dumps(SUGGESTION), "truncated": False} and len(STATE.seen) == 1
              and sent["method"] == "POST" and sent["path"] == path, str((got, sent.get("path"))))
        check(f"344: {provider} sends the model, system then user, and no temperature or sampling field",
              body.get("model") == model and [m["role"] for m in body["messages"]] == ["system", "user"]
              and body["messages"][0]["content"] == "Sys prompt." and body["messages"][1]["content"] == "User words."
              and not {"temperature", "top_p", "top_k", "stream", "thinking"} & set(body), str(body)[:200])
        headers = sent.get("headers", {})
        if header == "authorization":
            ok = headers.get("authorization") == f"Bearer {GOOD[provider]}" and "api-key" not in headers
        elif header == "api-key":
            ok = headers.get("api-key") == GOOD[provider] and "authorization" not in headers
        else:
            ok = "authorization" not in headers and "api-key" not in headers
        check(f"344: {provider}'s key rides in "
              f"{'Bearer' if header == 'authorization' else 'the api-key header' if header else 'no header'} alone",
              ok and GOOD.get(provider, "\0") not in json.dumps(body), str(sorted(headers)))
    STATE.reset()
    ask("azure", address="https://example-344.openai.azure.example", deployment=DEPLOYMENT)
    check("344: Azure's URL is built from the address and the deployment, with the api-version",
          STATE.seen[0]["query"] == f"api-version={ai_mod.AZURE_API_VERSION}"
          and ai_mod.openai_url("azure", "chat", "https://res.openai.azure.example/", "dep x", "2025-01-01")
          .endswith("/openai/deployments/dep%20x/chat/completions?api-version=2025-01-01"), "")
    STATE.reset()
    ask("openai", max_tokens=300)
    ask("mistral", max_tokens=300)
    check("344: a ceiling goes in the field the provider reads, OpenAI's max_completion_tokens, Mistral's max_tokens",
          STATE.seen[0]["body"].get("max_completion_tokens") == 300 and "max_tokens" not in STATE.seen[0]["body"]
          and STATE.seen[1]["body"].get("max_tokens") == 300, "")

    # ── B. what comes back
    STATE.reset()
    STATE.mode["mistral"] = "length"
    cut = ask("mistral")
    STATE.mode["mistral"] = "emptylength"
    spent = ask("mistral")
    STATE.mode["mistral"] = "filtered"
    held = ask("mistral")
    STATE.mode["mistral"] = "nonjson"
    junk = ask("mistral")
    check("344: an answer cut at its length says so, an empty one cut at its length is the too-long line, "
          "a filtered one the declined line, and a body that is no JSON the unreadable line",
          cut.get("truncated") is True and spent == {"error": ai_mod.TOO_LONG} and held == {"error": ai_mod.REFUSED}
          and junk == {"error": ai_mod.NOT_JSON}, str((cut, spent, held, junk)))
    lines = {}
    for status in ("401", "404", "429", "500"):
        STATE.mode["mistral"] = status
        STATE.mode["azure"] = status
        lines[status] = ask("mistral")["error"], ask("azure", address="https://example-344.openai.azure.example",
                                                   deployment="gone-344")["error"]
    check("344: a refused key, a rate limit and a 500 are each one line from refused_said, with the status",
          lines["401"][0] == "Mistral refused the key (HTTP 401)."
          and lines["429"][0] == "Mistral asked for a break from requests (HTTP 429)."
          and lines["500"][0] == "Mistral did not answer (HTTP 500).", str(lines))
    check("344: Azure's 404 names the deployment, its other statuses are the same lines",
          lines["404"][1] == "Azure has no deployment named gone-344 (HTTP 404)."
          and lines["401"][1] == "Azure OpenAI refused the key (HTTP 401)."
          and lines["404"][0] == "Mistral refused the request (HTTP 404).", str(lines))
    check("344: nothing the provider's error body held reaches the line",
          all("echoing" not in v for pair in lines.values() for v in pair))
    STATE.reset()
    STATE.mode["other"] = "slow"
    began = time.monotonic()
    slow = ask("other", model="m", address=other_address, timeout=0.3)
    STATE.mode["mistral"] = "slow"
    slow_named = ask("mistral", timeout=0.3)
    check("344: a timeout is the address line for Another service, naming its host, and the connection line "
          "for a named provider",
          slow == {"error": f"Nothing answered at {base[len('http://'):]}. Check the address."}
          and slow_named == {"error": "Mistral did not answer. Check the connection."}
          and time.monotonic() - began < 3, str((slow, slow_named)))
    dead = ask("other", model="m", address="http://127.0.0.1:9/v1", timeout=1)
    check("344: nothing answering at the address is the same line",
          dead == {"error": "Nothing answered at 127.0.0.1:9. Check the address."}, str(dead))
    gone = ai_mod.complete("s", "u", "lmstudio", "m", transport=lambda *a: (0, ""))
    check("344: LM Studio's server not running says to start it, load a model, and it appears",
          gone == {"error": "LM Studio's server is not running. Start it in LM Studio, load a model, and it appears here."},
          str(gone))

    # ── C. the address, the key and the model asked for before any call
    STATE.reset()
    refusals = [ask("other", model="m", address=a) for a in ("http://example.invalid/v1", "ftp://example.invalid/v1",
                                                             "example.invalid/v1", "")]
    refusals.append(ask("azure", address="http://example.invalid", deployment=DEPLOYMENT))
    check("344: an address that is not https is refused unless it is on this computer, and no request is made",
          [r.get("error") for r in refusals[:3]] == [HTTPS_LINE] * 3
          and refusals[3] == {"error": "No address. Add one in Settings under AI features."}
          and refusals[4] == {"error": HTTPS_LINE} and not STATE.seen, str(refusals))
    ok_local = ask("other", model="m", address=f"http://localhost:{base.rsplit(':', 1)[1]}/other/v1")
    ok_https = ask("other", model="m", address="https://service-344.example/other/v1")
    check("344: http on localhost is taken, and an https address is taken (in a smoke run it goes to the stub, "
          "never out)", "text" in ok_local and "text" in ok_https and all(s["provider"] == "other" for s in STATE.seen),
          str((ok_local, ok_https)))
    STATE.reset()
    needs = [ask("mistral", key=None), ask("azure", address="https://example-344.openai.azure.example", deployment=""),
             ask("other", address=other_address), ask("lmstudio")]
    check("344: no key, no deployment and no model are each said before any call",
          needs[0] == {"error": ai_mod.NO_KEY} and needs[1] == {"error": "No deployment name. Add one in Settings under AI features."}
          and needs[2] == {"error": "No model chosen. Pick one in Settings under AI features."}
          and needs[3] == {"error": "No model chosen. Pick one in Settings under AI features."} and not STATE.seen,
          str(needs))
    check("344: Another service needs no key, LM Studio none, and the route says so",
          ai_mod.route_ready({"provider": "other", "model": "m", "address": other_address}) is None
          and ai_mod.route_ready({"provider": "lmstudio", "model": "m"}) is None
          and ai_mod.route_ready({"provider": "gemini", "key": "k"}) is None
          and ai_mod.route_ready({"provider": "gemini"}) == {"error": ai_mod.NO_KEY}
          and ai_mod.route_ready({"provider": "azure", "key": "k", "address": other_address}) ==
          {"error": "No deployment name. Add one in Settings under AI features."}, "")

    # ── D. the model list
    STATE.reset()
    listed = ai_mod.openai_model_list("gemini", GOOD["gemini"])
    check("344: a model list is a GET to the provider's /models, the ids sorted, repeats and a models/ prefix dropped, "
          "and named by its source",
          [m["id"] for m in listed["models"]] == ["m-a-344", "m-b-344"] and listed["source"] == "live"
          and listed["note"] == "From Google Gemini's list." and STATE.seen[0]["method"] == "GET"
          and STATE.seen[0]["path"] == "/gemini/v1beta/openai/models", str(listed))
    STATE.reset()
    typed = ai_mod.openai_model_list("azure", GOOD["azure"], "https://example-344.openai.azure.example")
    check("344: Azure lists none, the deployment is typed, and no request is made",
          typed["models"] == [] and typed["source"] == "typed" and not STATE.seen)
    STATE.mode["mistral"] = "401"
    refused = ai_mod.openai_model_list("mistral", "k-wrong")
    unset = ai_mod.openai_model_list("mistral", None)
    other_list = ai_mod.openai_model_list("other", None, other_address)
    check("344: a refused key or a missing one fails the list in a line, and Another service lists with no key",
          refused == {"models": [], "failed": True, "note": "Mistral refused the key (HTTP 401)."}
          and unset["failed"] and unset["note"] == ai_mod.NO_KEY and len(other_list["models"]) == 2
          and other_list["note"] == f"From {base[len('http://'):]}'s list.", str((refused, unset, other_list)))
    STATE.reset()

    # ── E. the server: keys, routes, the lists, Check key and the suggestion
    held = ai_mod.STUB_KEYCHAIN.held
    held.clear()
    server_mod.CONFIG_PATH = config_path
    config_path.write_text(json.dumps({"ai_suggest": True, "ai_provider": "mistral", "ai_address": other_address,
                                       "ai_deployment": DEPLOYMENT, "other_model": "other-model-344",
                                       "ai_models": {"mistral": "m-b-344"}}), encoding="utf-8")
    cfg = server_mod.config()
    check("344: config carries the address, the deployment, the api-version, Another service's model and the models",
          server_mod.defaults()["ai_address"] == "" and server_mod.defaults()["ai_api_version"] == ai_mod.AZURE_API_VERSION
          and server_mod.defaults()["ai_models"] == {} and cfg["ai_address"] == other_address
          and cfg["other_model"] == "other-model-344", "")
    for provider in ("mistral", "gemini", "openai", "azure"):
        saved = server_mod.api_key({"provider": provider, "key": GOOD[provider]})
        answers.append(saved)
        check(f"344: {provider}'s key is saved under its own item", saved == {"saved": True}
              and held.get(ai_mod.PRESETS[provider]["service"]) == GOOD[provider], str(saved))
    answers.append(server_mod.api_key({"provider": "other", "key": GOOD["other"]}))
    other_service = f"IDIOGRAPH_AI_KEY 127.0.0.1:{base.rsplit(':', 1)[1]}"
    check("344: Another service's key is named by its address's host, and Anthropic's item is untouched",
          held.get(other_service) == GOOD["other"] and ai_mod.KEYCHAIN_SERVICE not in held, str(sorted(held)))
    status = server_mod.api_key_status({"provider": "mistral"})
    held_before = dict(held)
    cleared = server_mod.api_key({"provider": "mistral", "clear": True})
    check("344: Remove removes the chosen provider's key alone",
          status == {"set": True, "source": "keychain"} and cleared == {"cleared": True}
          and held.get("MISTRAL_API_KEY") is None
          and all(held.get(k) == v for k, v in held_before.items() if k != "MISTRAL_API_KEY")
          and server_mod.api_key_status({"provider": "mistral"}) == {"set": False, "source": None}, str(cleared))
    check("344: a provider with no key item, LM Studio, saves none",
          "error" in server_mod.api_key({"provider": "lmstudio", "key": "x"}))
    check("344: Another service's key is not saved to an address that would be refused",
          "error" in server_mod.api_key({"provider": "other", "key": "x", "ai_address": "http://example.invalid"}))

    route = server_mod.ai_route(cfg, {"provider": "gemini"})
    azure = server_mod.ai_route(cfg, {"provider": "azure"})
    other = server_mod.ai_route(cfg, {"provider": "other"})
    lms = server_mod.ai_route(cfg, {"provider": "lmstudio", "model": "lm-344"})
    check("344: a route carries the provider's own key, its preset's model, and for Azure and Another service "
          "the address and the deployment",
          route["provider"] == "gemini" and route["key"] == GOOD["gemini"] and route["model"] == "gemini-2.0-flash"
          and azure["key"] == GOOD["azure"] and azure["deployment"] == DEPLOYMENT and azure["address"] == other_address
          and other["key"] == GOOD["other"] and other["model"] == "other-model-344"
          and lms["key"] is None and lms["model"] == "lm-344", str((route, azure, other, lms)))
    check("344: the model each provider is asked is the one chosen for it, else its preset's",
          server_mod.ai_route(cfg)["model"] == "m-b-344"
          and server_mod.ai_route(cfg, {"provider": "openai"})["model"] == "gpt-4o-mini"
          and server_mod.ai_model_words(dict(cfg, ai_provider="other")).startswith("other-model-344"), "")

    STATE.reset()
    held["MISTRAL_API_KEY"] = GOOD["mistral"]
    models = server_mod.api_models({})
    check("344: /api/models asks the chosen provider's list alone, as `openai`",
          models["provider"] == "mistral" and [m["id"] for m in models["openai"]["models"]] == ["m-a-344", "m-b-344"]
          and [s["provider"] for s in STATE.seen] == ["mistral"], str((models.get("openai"), STATE.seen)))
    STATE.reset()
    good = server_mod.api_check_key({"provider": "gemini", "key": GOOD["gemini"]})
    answers.append(good)
    check("344: Check key asks the provider's list, stores a typed key that works under its own item and returns "
          "the list", good.get("ok") is True and good["said"] == ai_mod.KEY_WORKS and good["source"] == "keychain"
          and len(good["openai"]["models"]) == 2 and held.get("GEMINI_API_KEY") == GOOD["gemini"], str(good))
    held["OPENAI_API_KEY"] = None
    bad = server_mod.api_check_key({"provider": "openai", "key": "k-wrong"})
    answers.append(bad)
    check("344: a refused key is said, is never stored, and the stored one is what a blank field checks",
          bad == {"ok": False, "said": ai_mod.KEY_REFUSED} and held.get("OPENAI_API_KEY") is None
          and server_mod.api_check_key({"provider": "azure", "ai_address": "https://example-344.openai.azure.example"})
          ["ok"] is True, str(bad))
    STATE.mode["mistral"] = "500"
    five = server_mod.api_check_key({"provider": "mistral", "key": GOOD["mistral"]})
    STATE.mode.pop("mistral")
    check("344: a 500 at Check key is not a verdict on the key",
          five == {"ok": False, "said": "The key could not be checked, because Mistral did not answer (HTTP 500)."},
          str(five))

    # the suggestion round trip through the app's own route, then the switch
    STATE.reset()
    held["MISTRAL_API_KEY"] = GOOD["mistral"]
    done = idiograph_routes.api_suggest({"turn": "I walked until the street went quiet.", "prior": "And then?"})
    answers.append(done)
    check("344: a suggestion through the app's route is two calls to the chosen provider and comes back as tags "
          "and candidates, naming the model",
          done.get("candidates") == SUGGESTION["candidates"] and done.get("tags") == SUGGESTION["tags"]
          and done.get("provider") == "mistral" and done.get("model") == "m-b-344"
          and [s["path"] for s in STATE.seen] == ["/mistral/v1/chat/completions"] * 2
          and all(s["body"]["model"] == "m-b-344" for s in STATE.seen), str(done)[:300])
    STATE.reset()
    config_path.write_text(json.dumps({"ai_suggest": False, "ai_provider": "mistral"}), encoding="utf-8")
    off = idiograph_routes.api_suggest({"turn": "I walked until the street went quiet."})
    off_models = server_mod.api_models({})
    off_other = server_mod.api_models({"provider": "gemini"})
    check("344: with the AI switch off a suggestion is refused and no list is asked, so no request is made at all",
          off.get("error") and "candidates" not in off and off_models["openai"]["source"] == "off"
          and off_other["openai"]["models"] == [] and not STATE.seen, str((off, STATE.seen)))
    held["MISTRAL_API_KEY"] = GOOD["mistral"]
    check("344: keys stay stored while the switch is off", held["MISTRAL_API_KEY"] == GOOD["mistral"]
          and server_mod.api_key_status({"provider": "gemini"})["set"] is True)

    # saving the settings writes the provider's own fields and never a key
    config_path.write_text(json.dumps({"ai_suggest": True}), encoding="utf-8")
    saved = server_mod.api_settings({"ai_provider": "azure", "ai_address": f" {other_address}/ ",
                                     "ai_deployment": DEPLOYMENT, "ai_api_version": "2025-01-01",
                                     "other_model": "o-344", "ai_models": {"openai": "gpt-344", "elsewhere": "x"}})
    cfg = saved["config"]
    check("344: Settings saves the provider, the address, the deployment, the api-version and the models, and "
          "drops a provider it does not know",
          cfg["ai_provider"] == "azure" and cfg["ai_address"] == f"{other_address}/".strip()
          and cfg["ai_deployment"] == DEPLOYMENT and cfg["ai_api_version"] == "2025-01-01"
          and cfg["other_model"] == "o-344" and cfg["ai_models"] == {"openai": "gpt-344"}
          and saved["ai"]["provider"] == "azure" and DEPLOYMENT in saved["ai"]["model_name"], str(saved)[:300])
    check("344: no key reaches the settings file", not any(k in config_path.read_text(encoding="utf-8")
                                                          for k in GOOD.values()))
