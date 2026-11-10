"""Area 238: Check key on the AI features page (Adam, 21 October 2026, round2fix). Through the app's stub hook,
`IDIOGRAPH_SEARCH_STUB` at a provider of this check's own on loopback, with the keychain held in memory: an
accepted key is stored and its models come back for the Model list, a refused one is never stored and the
list is left as it was, a key left out is the stored one, and a provider that does not answer is said. The
key never comes back in an answer. The large switch is the same shared setting, `ai_suggest`, as before.
Every key and model here is invented."""
from __future__ import annotations

import json
import os
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer

import ai_suggest as ai_mod
import server as server_mod
import sift_search as search_mod

from . import support
from .support import check

GOOD = "k-good-238"
MODELS = ["claude-opus-5-5", "claude-sonnet-5-5"]


class Provider(BaseHTTPRequestHandler):
    def do_GET(self):
        if not self.path.startswith("/anthropic/v1/models") or self.headers.get("x-api-key") != GOOD:
            self.send_response(401)
            self.end_headers()
            return
        body = json.dumps({"data": [{"id": m} for m in MODELS], "has_more": False}).encode()
        self.send_response(200)
        self.send_header("content-type", "application/json")
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, *_):
        pass


def test_check_key():
    print("\n238. Check key on the AI features page, against a stub provider on loopback, and the one switch")
    httpd = HTTPServer(("127.0.0.1", 0), Provider)
    threading.Thread(target=httpd.serve_forever, kwargs={"poll_interval": 0.05}, daemon=True).start()
    base = f"http://127.0.0.1:{httpd.server_address[1]}"
    was_env = os.environ.get(search_mod.STUB_ENV)
    was_held = dict(search_mod.STUB_KEYCHAIN.held)
    service = ai_mod.KEYCHAIN_SERVICE
    try:
        os.environ[search_mod.STUB_ENV] = base
        search_mod.STUB_KEYCHAIN.held[service] = None
        server_mod.forget_models()
        good = server_mod.api_check_key({"key": GOOD})
        check("238: an accepted key says so, comes back with the models it can call, and is stored",
              good.get("ok") is True and good.get("said") == ai_mod.KEY_WORKS
              and [m["id"] for m in good["anthropic"]["models"]] == MODELS
              and search_mod.STUB_KEYCHAIN.held.get(service) == GOOD, str(good))
        check("238: the key never comes back in the answer", GOOD not in json.dumps(good))
        listed = [m["id"] for m in server_mod.anthropic_list()["models"]]
        bad = server_mod.api_check_key({"key": "k-refused-238"})
        check("238: a refused key says so, is never stored, and the model list stays as it was",
              bad == {"ok": False, "said": ai_mod.KEY_REFUSED}
              and search_mod.STUB_KEYCHAIN.held.get(service) == GOOD
              and [m["id"] for m in server_mod.anthropic_list()["models"]] == listed == MODELS, str(bad))
        stored = server_mod.api_check_key({})
        check("238: with nothing typed, Check key checks the stored key", stored.get("ok") is True, str(stored))
        search_mod.STUB_KEYCHAIN.held[service] = None
        check("238: with nothing typed and nothing stored, it asks for the key first",
              server_mod.api_check_key({}) == {"ok": False, "said": "Put the key in the field first."})
        httpd.shutdown()
        httpd.server_close()
        gone = server_mod.api_check_key({"key": GOOD})
        check("238: a provider that does not answer is said, and the key is not stored",
              gone == {"ok": False, "said": ai_mod.KEY_UNCHECKED} and search_mod.STUB_KEYCHAIN.held.get(service) is None,
              str(gone))
        check("238: Check key is a route every app answers",
              server_mod.ROUTES.get("/api/check-key") is server_mod.api_check_key
              and server_mod.ROUTE_APP["/api/check-key"] == "shared")
    finally:
        if was_env is None:
            os.environ.pop(search_mod.STUB_ENV, None)
        else:
            os.environ[search_mod.STUB_ENV] = was_env
        search_mod.STUB_KEYCHAIN.held.clear()
        search_mod.STUB_KEYCHAIN.held.update(was_held)
        server_mod.forget_models()
        try:
            httpd.server_close()
        except OSError:
            pass

    page = support.page_text()
    app = support.text("family/static/shell.js", "apps/idiograph/static/distil.js")
    switch = page[page.index('<label class="ai-master"'):page.index("</label>", page.index('<label class="ai-master"'))]
    check("238: the large switch is the one box it always was, set-ai, a switch to a screen reader inside its row's label, "
          "saved as ai_suggest, off on a new install",
          'id="set-ai"' in switch and 'role="switch"' in switch and page.count('id="set-ai"') == 1
          and "ai_suggest: $('set-ai').checked," in app and server_mod.merge_config({})["ai_suggest"] is False)
