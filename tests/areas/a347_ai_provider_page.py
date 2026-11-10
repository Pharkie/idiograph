"""Area 347: the AI features page's providers (aipage, 8 November 2026, aiprov's drawing built, Adam that evening by
dialog). What matters is what a choice does: choosing each of the eight providers shows its own rows and hides the
rest, the Address of the two local ones filled with their usual address, a key checked or removed under the chosen
provider's own keychain item, Save sending each provider's address and model to its own key in the settings file,
the AI switch off hiding every new row and asking the server nothing, and the command line and MCP setting the
same keys through the app's own `/api/settings`. The page's part runs in the computer's own browser, headless, on
the app's own functions and markup, the server answered by a stand-in that records what it is asked. The keychain
is the one held in memory, and nothing leaves this computer. Every key, model and host is invented, a project on
keeping bees."""
from __future__ import annotations

import html as html_mod
import json
import os
import subprocess
import tempfile
from pathlib import Path

from . import support
from .support import check, skip

PROVIDERS = ("anthropic", "mistral", "gemini", "openai", "azure", "other", "local", "lmstudio")
# the rows each provider shows, the rest hidden: Anthropic's, Ollama's, the OpenAI-style one's, the Address, the
# Deployment in place of the Model, and the key row
SHOWS = {
    "anthropic": {"anthropic", "key"},
    "mistral": {"other", "model", "key"},
    "gemini": {"other", "model", "key"},
    "openai": {"other", "model", "key"},
    "azure": {"other", "address", "deployment", "key"},
    "other": {"other", "address", "model", "key"},
    "local": {"local", "address"},
    "lmstudio": {"other", "address", "model"},
}
ROWS = {"anthropic": "ai-anthropic", "local": "ai-local", "other": "ai-other", "address": "ai-address",
        "deployment": "deployment-row", "model": "other-model-row", "key": "ai-key"}

RUN = r"""
const out = { rows: {}, where: {}, address: {}, asked: {} };
const tick = () => new Promise((r) => setTimeout(r, 0));
const shown = (id) => { const el = $(id); return !!el && !el.closest('[hidden]'); };
const ROWS = __ROWS__;
(async () => {
  aiHeldOpen({ ai_suggest: true, ai_provider: 'anthropic', model: 'claude-haiku-5-5', local_url: '', lmstudio_url: '',
    ai_address: '', ai_deployment: 'hive-eu', ai_models: { gemini: 'g-hive' }, other_model: '' });
  $('set-ai').checked = true;
  aiSetDraw();
  await loadModels();
  for (const p of __PROVIDERS__) {
    CALLS.length = 0;
    $('set-provider').value = p;
    chooseProvider();
    for (let i = 0; i < 4; i += 1) await tick();
    out.rows[p] = Object.keys(ROWS).filter((k) => shown(ROWS[k]));
    out.where[p] = shown('ai-where') ? $('ai-where').textContent : '';
    out.address[p] = shown('ai-address') ? $('set-address').value : null;
    out.asked[p] = CALLS.map((c) => [c.path, c.body && c.body.provider]);
  }
  // Another service: an address typed, the where line naming its host, the key and the list asked there
  $('set-provider').value = 'other';
  chooseProvider();
  await tick();
  $('set-address').value = 'https://chat.hives.example/v1';
  typeAddress();
  out.otherWhere = $('ai-where').textContent;
  CALLS.length = 0;
  leaveAddress();
  for (let i = 0; i < 4; i += 1) await tick();
  out.otherAsked = CALLS.map((c) => [c.path, c.body.provider, c.body.ai_address]);
  // Mistral's key checked and removed: each sent with Mistral named, so the server files it under Mistral's item
  $('set-provider').value = 'mistral';
  chooseProvider();
  for (let i = 0; i < 4; i += 1) await tick();
  CALLS.length = 0;
  $('set-key').value = 'k-hive-347';
  await checkKey();
  await clearKey();
  out.keyAsked = CALLS.filter((c) => c.path !== '/api/models').map((c) => [c.path, c.body.provider, !!c.body.key, !!c.body.clear]);
  out.keyField = $('set-key').value;
  // a model chosen for Mistral, then LM Studio's address typed, and Save's body
  $('set-other-model').value = 'm-two';
  pickOther();
  $('set-provider').value = 'lmstudio';
  chooseProvider();
  await tick();
  $('set-address').value = 'http://127.0.0.1:4321/v1';
  typeAddress();
  const body = {};
  aiSaveBody(body);
  out.save = body;
  // the switch off: every row under it hidden, and the server asked nothing
  CALLS.length = 0;
  $('set-ai').checked = false;
  aiSetDraw();
  out.offShown = ['set-provider', 'ai-where', 'set-address', 'set-key', 'set-other-model', 'set-other-name',
    'set-deployment', 'set-model', 'set-local-model'].filter(shown);
  out.offInside = ['ai-where', 'ai-address', 'ai-other', 'deployment-row', 'set-other-name']
    .every((id) => $(id) && $(id).closest('#ai-more[data-ai-set]'));
  out.offAsked = CALLS.length;
  document.getElementById('out').textContent = JSON.stringify(out);
})().catch((err) => { document.getElementById('out').textContent = JSON.stringify({ error: String(err && err.stack || err) }); });
"""

# the server's answers, as /api/models, /api/key-status, /api/check-key and /api/key send them
STAND_IN = r"""
const CALLS = [];
async function api(path, body) {
  CALLS.push({ path, body: body || {} });
  const p = (body && body.provider) || 'anthropic';
  if (path === '/api/models') {
    const openai = ['anthropic', 'local'].includes(p) ? null
      : { provider: p, models: p === 'azure' ? [] : [{ id: 'm-one', name: 'm-one' }, { id: 'm-two', name: 'm-two' }],
        source: p === 'azure' ? 'typed' : 'live', note: '' };
    return { provider: p, model: p === 'anthropic' ? 'claude-haiku-5-5' : 'm-one', local_model: '',
      anthropic: { models: [{ id: 'claude-haiku-5-5', name: 'Haiku 5.5', price: '$1 in' }], source: 'builtin', note: '' },
      local: { running: true, models: [{ id: 'bee:7b', name: 'bee:7b' }], note: '', url: body.local_url },
      ...(openai ? { openai } : {}) };
  }
  if (path === '/api/key-status') return { set: false, source: null };
  if (path === '/api/check-key') return { ok: true, said: 'This key works.', source: 'keychain',
    openai: { provider: p, models: [{ id: 'm-one', name: 'm-one' }, { id: 'm-two', name: 'm-two' }], source: 'live', note: '' } };
  if (path === '/api/key') return { cleared: true };
  return {};
}
"""


def whole(src: str, head: str) -> str:
    at = src.index(head)
    return src[at:src.index("\n}\n", at) + 3]


def line_of(src: str, start: str) -> str:
    return next(ln for ln in src.splitlines() if ln.strip().startswith(start))


def page_part() -> str:
    """The AI features page's switch and everything under it, as the served page has them, its words in English."""
    import boot
    import i18n
    page = support.page_text()
    at = page.index('<label class="ai-master" id="ai-sub">')
    part = page[at:page.index('<!-- Using your own AI agents', at)]
    words = i18n.messages("en", boot.roots())
    for key in sorted(set(__import__("re").findall(r"\{\{([a-z_][\w.]*)\}\}", part))):
        said = words.get(key)
        part = part.replace("{{" + key + "}}", html_mod.escape(said if isinstance(said, str) else key))
    return part.replace("<!--slot:ai-feature-->", "")


def run_page(exe) -> dict:
    shell = support.text("family/static/shell.js")
    start = shell.index("/* The providers (aiprov's drawing")
    block = shell[start:shell.index("/* The provider and the model go only to a server", start)]
    parts = [
        support.i18n_js(),
        "const $ = (id) => document.getElementById(id);",
        "const S = {};",
        "const RESTART_LINE = 'restart';",
        "const needsRestart = () => false;",
        "const olderServer = () => new Error('older');",
        line_of(shell, "const aiOn = "), line_of(shell, "const esc = "), line_of(shell, "const escAttr = "),
        line_of(shell, "const withCode = "),
        whole(shell, "function saidIn("), line_of(shell, "const saidErr = "),
        line_of(shell, "const stale = "), line_of(shell, "const drawRestart = "),
        whole(shell, "function aiSetDraw("),
        STAND_IN, block,
    ]
    script = "\n".join(parts) + RUN.replace("__ROWS__", json.dumps(ROWS)).replace("__PROVIDERS__", json.dumps(PROVIDERS))
    doc = ('<!doctype html><html><head><meta charset="utf-8"><style>[hidden]{display:none !important}</style></head>'
           '<body><div id="settings">' + page_part() + '</div><pre id="out">none</pre>'
           '<script>' + script + '</script></body></html>')
    with tempfile.TemporaryDirectory(prefix="idiograph-347-") as tmp:
        page_file = Path(tmp) / "ai.html"
        page_file.write_text(doc, encoding="utf-8")
        cmd = [str(exe), "--headless", "--disable-gpu", "--no-first-run", "--no-default-browser-check",
               "--disable-extensions", "--disable-background-networking", "--disable-component-update",
               "--disable-sync", "--disable-default-apps", "--password-store=basic", "--use-mock-keychain",
               f"--user-data-dir={Path(tmp) / 'profile'}", "--window-size=1280,800", "--virtual-time-budget=4000",
               "--dump-dom", page_file.as_uri()]
        try:
            dumped = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", timeout=120).stdout
        except (OSError, subprocess.TimeoutExpired) as err:
            dumped = str(err)
    said = dumped.split('<pre id="out">', 1)[1].split("</pre>", 1)[0] if '<pre id="out">' in dumped else "{}"
    return json.loads(html_mod.unescape(said)) if said.startswith("{") else {"said": said[:300]}


def test_ai_provider_page(scratch: Path):
    print("\n347. The AI features page's providers (aipage, 8 November 2026): each provider's rows, its own key, Save's "
          "keys, the switch off asking nothing, and the command line and MCP setting them")
    exe = support.browser()
    if exe is None:
        skip("347: the page in a real browser", "no Chrome, Chromium, Brave or Edge on this computer")
    else:
        page_checks(run_page(exe))
    server_checks(scratch)


def page_checks(o: dict):
    detail = json.dumps(o)[:700]
    rows = o.get("rows") or {}
    check("347: choosing each of the eight providers shows its own rows and hides the rest (Azure's Deployment in "
          "place of a Model, the Address for Azure, Another service and the two local ones, no key row for a local one)",
          all(set(rows.get(p) or []) == SHOWS[p] for p in PROVIDERS), json.dumps(rows))
    asked = o.get("asked") or {}
    check("347: each provider chosen asks for its own key's state and its own list, by name, and a local one no key",
          all(["/api/models", p] in asked.get(p, []) for p in PROVIDERS)
          and all((["/api/key-status", p] in asked.get(p, [])) == ("key" in SHOWS[p]) for p in PROVIDERS),
          json.dumps(asked))
    where = o.get("where") or {}
    check("347: the line under the list says where the passages go for each, the local ones on this machine",
          where.get("mistral") == "Passages go to Mistral, in the EU." and where.get("local") == where.get("lmstudio")
          == "Passages stay on this machine." and where.get("anthropic", "").startswith("Passages go to Anthropic.")
          and all(where.get(p) for p in PROVIDERS if p != "other"), json.dumps(where))
    address = o.get("address") or {}
    check("347: the two local ones' Address is filled with the usual address",
          address.get("local") == "http://127.0.0.1:11434" and address.get("lmstudio") == "http://127.0.0.1:1234/v1",
          json.dumps(address))
    check("347: Another service's address typed names its host in the line, and leaving the field asks for its key "
          "and its list at that address",
          o.get("otherWhere") == "Passages go to chat.hives.example."
          and ["/api/key-status", "other", "https://chat.hives.example/v1"] in (o.get("otherAsked") or [])
          and ["/api/models", "other", "https://chat.hives.example/v1"] in (o.get("otherAsked") or []), detail)
    check("347: Check key and Remove go with the chosen provider named, so the key is filed under its own item, and "
          "the field is emptied",
          o.get("keyAsked") == [["/api/check-key", "mistral", True, False], ["/api/key", "mistral", False, True],
                                ["/api/key-status", "mistral", False, False]] and o.get("keyField") == "", detail)
    save = o.get("save") or {}
    check("347: Save sends the provider, each address to its own key, Azure's deployment and each provider's model",
          save.get("ai_provider") == "lmstudio" and save.get("lmstudio_url") == "http://127.0.0.1:4321/v1"
          and save.get("local_url") == "http://127.0.0.1:11434" and save.get("ai_address") == "https://chat.hives.example/v1"
          and save.get("ai_deployment") == "hive-eu" and (save.get("ai_models") or {}).get("mistral") == "m-two"
          and (save.get("ai_models") or {}).get("gemini") == "g-hive" and "other" not in (save.get("ai_models") or {}),
          json.dumps(save))
    check("347: with the switch off every row under it is hidden, all inside #ai-more, and the server is asked nothing",
          o.get("offShown") == [] and o.get("offInside") is True and o.get("offAsked") == 0, detail)


def server_checks(scratch: Path):
    import ai_suggest as ai_mod
    import cli
    import mcp_server
    import server as server_mod
    from .a316_code_list import make_project

    base = scratch / "ai-provider-347"
    root = base / "Bees"
    make_project(root, "ipa")
    config_file = base / "config.json"
    config_file.write_text(json.dumps({"projects": [{"root": str(root)}], "corpus": "", "gravity_reference": "",
                                       "corpus_exclude": [], "ai_suggest": False}), encoding="utf-8")
    kept = (server_mod.CONFIG_PATH, server_mod.ROOT_OVERRIDE)
    was_env = os.environ.get(ai_mod.STUB_ENV)
    was_held = dict(ai_mod.STUB_KEYCHAIN.held)
    was_call = ai_mod.http_call
    sent: list = []

    def nowhere(method, url, *_a, **_k):
        sent.append((method, url))
        return 0, ""

    try:
        # a stub address nothing answers at, so every key goes to the keychain held in memory, and every request is
        # recorded and answered by nothing
        os.environ[ai_mod.STUB_ENV] = "http://127.0.0.1:9"
        ai_mod.http_call = nowhere
        server_mod.CONFIG_PATH = config_file
        held = ai_mod.STUB_KEYCHAIN.held
        held.clear()
        for p in ("mistral", "gemini", "openai", "azure"):
            server_mod.api_key({"provider": p, "key": f"k-{p}-347"})
        server_mod.api_key({"key": "k-anthropic-347"})
        check("347: each provider's key is saved under its own keychain item, Anthropic's under its own",
              all(held.get(ai_mod.PRESETS[p]["service"]) == f"k-{p}-347" for p in ("mistral", "gemini", "openai", "azure"))
              and held.get(ai_mod.KEYCHAIN_SERVICE) == "k-anthropic-347", str(sorted(held)))
        sent.clear()
        off = [server_mod.api_models({"provider": p}) for p in ("mistral", "gemini", "other", "lmstudio")]
        check("347: with the switch off, no OpenAI-style provider's list is asked, so nothing is sent",
              all(o["openai"]["source"] == "off" for o in off) and not sent, str(sent))
        lms = server_mod.ai_route_fields(dict(server_mod.config(), lmstudio_url="http://127.0.0.1:4321/v1"), "lmstudio")
        check("347: LM Studio's calls go to the address in Settings, its usual one when that is none",
              ai_mod.openai_url("lmstudio", "chat", lms["address"]).startswith("http://127.0.0.1:9/lmstudio/v1")
              and lms["address"] == "http://127.0.0.1:4321/v1"
              and server_mod.defaults()["lmstudio_url"] == "http://127.0.0.1:1234/v1", str(lms))
        os.environ.pop(ai_mod.STUB_ENV, None)
        check("347: outside a smoke run LM Studio is asked at its address, and Mistral at its EU address",
              ai_mod.openai_url("lmstudio", "models", "http://127.0.0.1:4321/v1") == "http://127.0.0.1:4321/v1/models"
              and ai_mod.openai_url("lmstudio", "models", "") == "http://127.0.0.1:1234/v1/models"
              and ai_mod.openai_url("mistral", "chat").startswith("https://api.eu.mistral.ai/v1/"), "")
        os.environ[ai_mod.STUB_ENV] = "http://127.0.0.1:9"
    finally:
        ai_mod.http_call = was_call
        server_mod.CONFIG_PATH, server_mod.ROOT_OVERRIDE = kept
        if was_env is None:
            os.environ.pop(ai_mod.STUB_ENV, None)
        else:
            os.environ[ai_mod.STUB_ENV] = was_env
        ai_mod.STUB_KEYCHAIN.held.clear()
        ai_mod.STUB_KEYCHAIN.held.update(was_held)

    # the command line and MCP: the same keys through /api/settings, never a key
    def run_json(*args):
        code, out, err = cli.run(["--config", str(config_file), "--root", str(root), "--json", *args])
        got = support.plain(json.loads(out)) if out.strip() else {}
        return code, got, err

    def saved() -> dict:
        return json.loads(config_file.read_text(encoding="utf-8"))

    code, read, err = run_json("settings")
    check("347: settings reads the provider, the model and where the passages go, and nothing about a key",
          code == 0 and read.get("ai_provider") == "anthropic" and read.get("ai_on") is False
          and read.get("ai_where", "").startswith("Passages go to Anthropic.")
          and not any("key" in k for k in read), err + json.dumps(read)[:300])
    before = config_file.read_bytes()
    code, dry, err = run_json("settings", "--ai-provider", "azure", "--ai-address", "https://hives.openai.azure.example",
                              "--ai-deployment", "hive-eu", "--dry-run")
    check("347: a dry run says what would be set and writes nothing",
          code == 0 and dry.get("ai_provider") == "azure" and dry.get("ai_deployment") == "hive-eu"
          and config_file.read_bytes() == before, err + json.dumps(dry)[:300])
    code, done, err = run_json("settings", "--ai-provider", "azure", "--ai-address", "https://hives.openai.azure.example",
                               "--ai-deployment", "hive-eu", "--note", "Use the university's Azure")
    c = saved()
    check("347: the command line sets Azure, its address and its deployment in the settings file",
          code == 0 and c.get("ai_provider") == "azure" and c.get("ai_address") == "https://hives.openai.azure.example"
          and c.get("ai_deployment") == "hive-eu", err + json.dumps(done)[:300])
    refused = [run_json("settings", *a, "--note", "x")[0] for a in (
        ("--ai-provider", "hives"), ("--ai-address", "http://hives.example"), ("--ai-model", "gpt-hive"),
        ("--ai-provider", "mistral", "--ai-deployment", "d"), ("--ai-provider", "openai", "--ai-address", "https://x.example"))]
    check("347: an unknown provider, an address not https, a model for Azure, a deployment but for Azure and an "
          "address for a provider with none are refused, nothing written",
          all(r != 0 for r in refused) and saved() == c, str(refused))
    code, _, err = run_json("settings", "--ai-provider", "lmstudio", "--ai-address", "", "--ai-model", "bee-7b",
                            "--note", "Use LM Studio")
    c = saved()
    check("347: a local one's address emptied puts its usual one back, and its model goes to its own key",
          code == 0 and c.get("lmstudio_url") == "http://127.0.0.1:1234/v1" and c.get("ai_models", {}).get("lmstudio") == "bee-7b",
          err + json.dumps(c)[:300])

    mcp = mcp_server.Server(root=str(root), config=str(config_file))
    said = lambda res: support.plain(res.get("structuredContent") or {})
    r1 = mcp.call(mcp.by_name["settings_set"], {"ai_provider": "mistral", "ai_model": "mistral-large-latest",
                                                 "request": "Use Mistral in the EU"})
    c = saved()
    r2 = mcp.call(mcp.by_name["settings"], {})
    r3 = mcp.call(mcp.by_name["settings_set"], {"ai_provider": "other", "ai_address": "ftp://hives.example",
                                                 "request": "Another service"})
    schema = mcp.by_name["settings_set"]["inputSchema"]["properties"]
    check("347: MCP sets the provider and its model the same way, reads them back, refuses a bad address, and takes "
          "no key",
          not r1["isError"] and c.get("ai_provider") == "mistral" and c.get("ai_models", {}).get("mistral")
          == "mistral-large-latest" and said(r2).get("ai_model") == "mistral-large-latest"
          and said(r2).get("ai_where") == "Passages go to Mistral, in the EU." and r3["isError"] and saved() == c
          and not any("key" in k for k in schema), json.dumps([r1.get("isError"), r3.get("isError"), sorted(schema)])[:400])
