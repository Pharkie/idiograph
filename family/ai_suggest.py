"""The family's AI (22 October 2026, the family codebase's fourth build, from the root's ai_suggest.py): the
providers, the key, the models and the transport every app's AI goes through, Idiograph's statements prompt
being its own, apps/idiograph/statement_prompts.py, as Sift's and Trace's prompts are theirs.

The key is read at call time, inside the server process, and never logged, echoed or returned. It
lives in the macOS keychain as a generic password under the service name `ANTHROPIC_API_KEY`,
written by `save_key` from the settings panel, and `Tools/idiograph/.env` is read first when that
file carries one. Saving passes the value as an argument to `security`, which makes it visible in
the process list for the life of that call, milliseconds on a single-user Mac. An error from the
API comes back as one line carrying the HTTP status and nothing else, so no header and no key can
reach the page or the console.

Two providers answer. Anthropic, over the Messages API with the key, and Local, a model Ollama runs
on this machine, which needs no key and sends nothing anywhere. Both passes of a suggestion go
through `complete`, which picks the provider.

The transport and the `security` runner are both parameters, so the tests run with no key, no
keychain, no Ollama and no network. A transport is `(method, url, headers, payload, timeout)` and
answers `(status, body)`.
"""
from __future__ import annotations

import getpass
import json
import os
import re
import shutil
import subprocess
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

import i18n

ENDPOINT = "https://api.anthropic.com/v1/messages"
MODELS_ENDPOINT = "https://api.anthropic.com/v1/models"
MODEL = "claude-haiku-5-5"
VERSION = "2023-06-01"
MAX_TOKENS = 600
TIMEOUT = 20
# A model that thinks by default spends part of max_tokens on thinking before it writes, and takes
# longer about it, so it gets room for both. Its answer is still the same short JSON.
THINKING_MAX_TOKENS = 16000
THINKING_TIMEOUT = 120
LIST_TIMEOUT = 8

ANTHROPIC = "anthropic"
LOCAL = "local"
# The OpenAI-style providers (aiwire, 8 November 2026): one wire shape, `POST {base}/chat/completions` and
# `GET {base}/models`, with a small table of presets giving each named provider its address, its header, its
# plain name and the keychain item its key lives in.
MISTRAL = "mistral"
GEMINI = "gemini"
OPENAI = "openai"
AZURE = "azure"
OTHER = "other"
LMSTUDIO = "lmstudio"
OPENAI_SHAPED = (MISTRAL, GEMINI, OPENAI, AZURE, OTHER, LMSTUDIO)
PROVIDERS = (ANTHROPIC, LOCAL) + OPENAI_SHAPED
OPENAI_TIMEOUT = 60
AZURE_API_VERSION = "2024-10-21"
OTHER_KEY_SERVICE = "IDIOGRAPH_AI_KEY"
LOOPBACK = ("127.0.0.1", "localhost", "::1")
# LM Studio's usual address, the one Settings fills its Address with (aipage, 8 November 2026)
LMSTUDIO_URL = "http://127.0.0.1:1234/v1"

# `keyed`: the provider wants a key. `address`: the page asks for one. `deployment`: Azure's. `tokens`: the
# field its ceiling goes in. `model`: the one used when none is chosen.
PRESETS = {
    # Mistral's EU endpoint (aipage, 8 November 2026): its global api.mistral.ai makes no promise where a request
    # is processed, and api.eu.mistral.ai processes it in the EU, as Settings' line says
    MISTRAL: {"name": "Mistral", "base": "https://api.eu.mistral.ai/v1", "header": "bearer",
              "service": "MISTRAL_API_KEY", "keyed": True, "model": "mistral-small-latest", "tokens": "max_tokens"},
    GEMINI: {"name": "Google Gemini", "base": "https://generativelanguage.googleapis.com/v1beta/openai",
             "header": "bearer", "service": "GEMINI_API_KEY", "keyed": True, "model": "gemini-2.0-flash",
             "tokens": "max_tokens"},
    OPENAI: {"name": "OpenAI", "base": "https://api.openai.com/v1", "header": "bearer",
             "service": "OPENAI_API_KEY", "keyed": True, "model": "gpt-4o-mini", "tokens": "max_completion_tokens"},
    AZURE: {"name": "Azure OpenAI", "base": "", "header": "api-key", "service": "AZURE_OPENAI_API_KEY",
            "keyed": True, "model": "", "tokens": "max_completion_tokens", "address": True, "deployment": True},
    OTHER: {"name": "", "base": "", "header": "bearer", "service": OTHER_KEY_SERVICE, "keyed": False,
            "model": "", "tokens": "max_tokens", "address": True},
    LMSTUDIO: {"name": "LM Studio", "base": LMSTUDIO_URL, "header": "bearer", "service": "",
               "keyed": False, "model": "", "tokens": "max_tokens"},
}


# The current Anthropic models, in the order the dropdown lists them, with the price in dollars per
# million input and output tokens. `thinks` marks the ones that think when the request carries no
# `thinking` field. None of them is ever sent `temperature`, `top_p`, `top_k` or `thinking`.
ANTHROPIC_MODELS = [
    {"id": "claude-fable-5-1", "name": "Fable 5.1", "input": 10, "output": 50, "thinks": True},
    {"id": "claude-opus-5-5", "name": "Opus 5.5", "input": 4, "output": 20, "thinks": True},
    {"id": "claude-opus-5", "name": "Opus 5", "input": 5, "output": 25, "thinks": True},
    {"id": "claude-opus-4-8", "name": "Opus 4.8", "input": 5, "output": 25, "thinks": False},
    {"id": "claude-opus-4-7", "name": "Opus 4.7", "input": 5, "output": 25, "thinks": False},
    {"id": "claude-opus-4-6", "name": "Opus 4.6", "input": 5, "output": 25, "thinks": False},
    {"id": "claude-sonnet-5-5", "name": "Sonnet 5.5", "input": 2, "output": 10, "thinks": True},
    {"id": "claude-sonnet-5", "name": "Sonnet 5", "input": 2, "output": 10, "thinks": True},
    {"id": "claude-sonnet-4-6", "name": "Sonnet 4.6", "input": 3, "output": 15, "thinks": False},
    {"id": "claude-haiku-5-5", "name": "Haiku 5.5", "input": 0.1, "output": 0.5, "thinks": True},
    {"id": "claude-haiku-4-5", "name": "Haiku 4.5", "input": 1, "output": 5, "thinks": False},
]
DATED = re.compile(r"-\d{8}$")

# Local means Ollama on this machine. Its list of pulled models is `/api/tags`, and a chat is
# `/api/chat` with streaming off and the answer held to JSON.
LOCAL_URL = "http://127.0.0.1:11434"
LOCAL_TIMEOUT = 180
LOCAL_LIST_TIMEOUT = 2

KEYCHAIN_SERVICE = "ANTHROPIC_API_KEY"
# a call asked for while the app's AI switch is off, refused in one line (Sift's and Trace's AI)
# the one line for an answer that is not the JSON asked for, in plain words, shared by Distil's, Sift's and
# Trace's AI code (15 October)


def refused_said(who: str, status: int, keyed: bool = True) -> str:
    """A call that came back with an error status, in plain words with the status in brackets, never what
    the answer held, as Sift's searches and the feedback note say theirs (17 October, later)."""
    if status in (401, 403) and keyed:
        return i18n.t("errors.refused_key", who=who, status=status)
    if status == 429:
        return i18n.t("errors.asked_break", who=who, status=status)
    if status >= 500:
        return i18n.t("errors.did_not_answer", who=who, status=status)
    return i18n.t("errors.refused_request", who=who, status=status)

KEY_LINE = re.compile(r"^\s*(?:export\s+)?ANTHROPIC_API_KEY\s*=\s*(.*?)\s*$")
FENCE = re.compile(r"^```[a-zA-Z]*\s*|\s*```$")


# ----------------------------------------------------------------- the key

def key_line(service: str = KEYCHAIN_SERVICE) -> re.Pattern:
    """The line of a `.env` that carries the key stored under `service`."""
    if service == KEYCHAIN_SERVICE:
        return KEY_LINE
    return re.compile(rf"^\s*(?:export\s+)?{re.escape(service)}\s*=\s*(.*?)\s*$")


def read_key(env_path: Path | None, service: str = KEYCHAIN_SERVICE) -> str | None:
    """The key stored under `service`, `ANTHROPIC_API_KEY` unless another is named, from a `.env`,
    tolerating `export`, quotes, comments and blank lines. No file, or None for one, is no key.

    The value is returned to the caller that makes the request and goes nowhere else.
    """
    if env_path is None:
        return None
    path = Path(env_path)
    if not path.exists():
        return None
    try:
        text = path.read_text(encoding="utf-8")
    except OSError:
        return None
    pattern = key_line(service)
    for line in text.splitlines():
        if line.lstrip().startswith("#"):
            continue
        m = pattern.match(line)
        if not m:
            continue
        value = m.group(1)
        if value and value[0] in "\"'" and value[-1] == value[0] and len(value) > 1:
            value = value[1:-1]
        value = value.strip()
        if value:
            return value
    return None


def keychain_key(service: str = KEYCHAIN_SERVICE, runner=None) -> str | None:
    """The generic password stored under `service` in the login keychain, or None.

    Runs the `security` tool inside the server process. The value is returned to the caller that
    makes the request and goes nowhere else: no log, no response, no exception text.
    """
    run = runner or subprocess.run
    try:
        done = run(["security", "find-generic-password", "-s", service, "-w"],
                   capture_output=True, text=True, encoding="utf-8", timeout=5, check=False)
    except Exception:
        return None
    if getattr(done, "returncode", 1) != 0:
        return None
    value = (getattr(done, "stdout", "") or "").strip()
    return value or None


def find_key(env_path: Path | None, runner=None, service: str = KEYCHAIN_SERVICE) -> str | None:
    """The key stored under `service` from `.env` when the file carries one, else from the
    keychain, else None."""
    return read_key(env_path, service) or keychain_key(service, runner=runner)


def security_missing(runner=None) -> bool:
    """True when this machine has no `security` tool, so a file is the only place a key can go.

    A runner handed in by the tests stands in for the tool, so it is never called missing there.
    """
    if runner is not None:
        return False
    return shutil.which("security") is None


def store_in_env(env_path: Path, value: str | None, service: str = KEYCHAIN_SERVICE) -> None:
    """Write or remove the key stored under `service` in a `.env` at mode 0600, leaving other lines
    alone.

    Only reached on a machine with no keychain. On a Mac the key goes to the keychain and this
    file is never written.
    """
    path = Path(env_path)
    pattern = key_line(service)
    lines: list[str] = []
    if path.exists():
        lines = [ln for ln in path.read_text(encoding="utf-8").splitlines() if not pattern.match(ln)]
    if value:
        lines.append(f"{service}={value}")
    text = "\n".join(lines).strip("\n")
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as handle:
        handle.write(text + ("\n" if text else ""))
    os.chmod(path, 0o600)


def current_user() -> str:
    try:
        return getpass.getuser()
    except Exception:
        return os.environ.get("USER") or "idiograph"


def save_key(value: str | None, runner=None, service: str = KEYCHAIN_SERVICE,
             account: str | None = None, env_path: Path | None = None) -> dict:
    """Store the key under `service` in the keychain, or in a `.env` on a machine with no keychain.

    Returns `{"saved": True, "source": ...}` or one error line. The value itself is never
    returned, never logged and never written to config.json.
    """
    value = str(value or "").strip()
    if not value:
        return {"error": i18n.t("errors.key_field")}
    if security_missing(runner):
        if env_path is None:
            return {"error": i18n.t("errors.nowhere_machine_store_key")}
        try:
            store_in_env(env_path, value, service)
        except OSError:
            return {"error": i18n.t("errors.key_could_written_file")}
        return {"saved": True, "source": "file"}
    run = runner or subprocess.run
    try:
        done = run(["security", "add-generic-password",
                    "-a", account or current_user(), "-s", service, "-w", value, "-U"],
                   capture_output=True, text=True, encoding="utf-8", timeout=10, check=False)
    except Exception:
        # the exception text can carry the argv, and the argv carries the key, so it is dropped
        return {"error": i18n.t("errors.keychain_would_take_key")}
    if getattr(done, "returncode", 1) != 0:
        return {"error": i18n.t("errors.keychain_would_take_key")}
    return {"saved": True, "source": "keychain"}


def clear_key(runner=None, service: str = KEYCHAIN_SERVICE, env_path: Path | None = None) -> dict:
    """Delete the key stored under `service` from wherever this machine keeps it."""
    if security_missing(runner):
        if env_path is None or not read_key(env_path, service):
            return {"cleared": False}
        try:
            store_in_env(env_path, None, service)
        except OSError:
            return {"cleared": False}
        return {"cleared": True}
    run = runner or subprocess.run
    try:
        done = run(["security", "delete-generic-password", "-s", service],
                   capture_output=True, text=True, encoding="utf-8", timeout=10, check=False)
    except Exception:
        return {"cleared": False}
    return {"cleared": getattr(done, "returncode", 1) == 0}


def key_status(env_path: Path | None, runner=None, service: str = KEYCHAIN_SERVICE) -> dict:
    """Whether a key is stored under `service` and where it sits, never what it is.

    `.env` is answered first, because that is the order `find_key` reads them in.
    """
    if read_key(env_path, service):
        return {"set": True, "source": "file"}
    if keychain_key(service, runner=runner):
        return {"set": True, "source": "keychain"}
    return {"set": False, "source": None}


# ------------------------------------------------------------------- prompt

def bullets(items: list[str]) -> str:
    return "\n".join(f"- {str(i).strip()}" for i in items if str(i).strip())


def anthropic_payload(system: str, user: str, model: str | None = None,
                      max_tokens: int | None = None) -> dict:
    """Model, ceiling, system and one user turn. Nothing else.

    No `temperature`, `top_p` or `top_k`, which the 5.x models refuse, no `thinking` field, so each
    model does what it does by default, and no assistant turn to prefill the answer. `max_tokens`
    is for a caller whose answer runs longer than a suggestion's, the grouping on the Themes screen.
    """
    chosen = str(model or "").strip() or MODEL
    ceiling = int(max_tokens) if max_tokens else (THINKING_MAX_TOKENS if thinks(chosen) else MAX_TOKENS)
    return {
        "model": chosen,
        "max_tokens": ceiling,
        "system": system,
        "messages": [{"role": "user", "content": user}],
    }


# Ollama's own context is a few thousand tokens unless asked for more, which a case of a hundred
# statements runs past, so a caller that sets a ceiling gets this much room as well.
LOCAL_CONTEXT = 16384


def local_payload(system: str, user: str, model: str, max_tokens: int | None = None) -> dict:
    """An Ollama chat: one answer, not a stream, held to JSON."""
    payload = {
        "model": model,
        "stream": False,
        "format": "json",
        "messages": [{"role": "system", "content": system}, {"role": "user", "content": user}],
    }
    if max_tokens:
        payload["options"] = {"num_predict": int(max_tokens), "num_ctx": LOCAL_CONTEXT}
    return payload


# ------------------------------------------------------------------- models

def plain_model(model_id: str | None) -> str:
    """`claude-haiku-4-5-20251001` as `claude-haiku-4-5`: a dated id is shown by its plain one."""
    return DATED.sub("", str(model_id or "").strip())


def model_entry(model_id: str | None) -> dict | None:
    plain = plain_model(model_id)
    return next((m for m in ANTHROPIC_MODELS if m["id"] == plain), None)


def model_name(model_id: str | None) -> str:
    entry = model_entry(model_id)
    return entry["name"] if entry else plain_model(model_id)


def thinks(model_id: str | None) -> bool:
    """Whether a model thinks by default. A model not in the table is given the room in case."""
    entry = model_entry(model_id)
    return True if entry is None else bool(entry["thinks"])


def price(dollars: float) -> str:
    return f"${dollars:g}"


def price_line(entry: dict) -> str:
    """`$2 in, $10 out, per million tokens`, the line under the Model list for the chosen model."""
    return f"{price(entry['input'])} in, {price(entry['output'])} out, per million tokens"


def price_hint(entry: dict) -> str:
    """`Sonnet 5.5 · $2 in, $10 out, per million tokens`, so the two prices say which is which."""
    return f"{entry['name']} · {price_line(entry)}"


def model_options(entries: list[dict]) -> list[dict]:
    return [{"id": m["id"], "name": m["name"], "hint": price_hint(m), "price": price_line(m)} for m in entries]


def anthropic_headers(key: str) -> dict:
    return {"x-api-key": key, "anthropic-version": VERSION, "content-type": "application/json"}


def anthropic_models(key: str | None, transport=None, timeout: float = LIST_TIMEOUT) -> dict:
    """The models this account can call, filtered to the table and in its order.

    The built-in table stands in when no key is stored or the live list does not answer, so the
    dropdown always has something in it, `failed` true when it stands in for a live list that failed, so
    Settings says its note in the warning tint. Nothing about the key comes back.
    """
    builtin = model_options(ANTHROPIC_MODELS)
    if not key:
        return {"models": builtin, "source": "builtin",
                "note": i18n.t("errors.built_list")}
    send = transport or http_call
    try:
        status, body = send("GET", f"{MODELS_ENDPOINT}?limit=1000", anthropic_headers(key), None, timeout)
    except Exception:
        status, body = 0, ""
    if status != 200:
        why = i18n.t("errors.anthropic_did_answer") if status == 0 else refused_said("Anthropic", status)
        return {"models": builtin, "source": "builtin", "failed": True,
                "note": f"The built-in list, because {why}"}
    try:
        data = json.loads(body)
        live = {plain_model(m.get("id")) for m in data.get("data") or [] if isinstance(m, dict)}
    except (ValueError, TypeError, AttributeError):
        return {"models": builtin, "source": "builtin", "failed": True,
                "note": i18n.t("errors.built_list_because_live_list_2")}
    chosen = [m for m in ANTHROPIC_MODELS if m["id"] in live]
    if not chosen:
        return {"models": builtin, "source": "builtin", "failed": True,
                "note": i18n.t("errors.built_list_because_live_list")}
    return {"models": model_options(chosen), "source": "live", "note": i18n.t("errors.from_account_s_live_list")}


# Check key's three answers in Settings (21 October): the key works, it was refused, or nothing answered
KEY_WORKS = i18n.t("errors.key_works")
KEY_REFUSED = i18n.t("errors.key_accepted")
KEY_UNCHECKED = i18n.t("errors.anthropic_did_answer_key_could")


def check_key(key: str | None, transport=None, timeout: float = LIST_TIMEOUT) -> dict:
    """Check key in Settings: whether Anthropic accepts the key, by asking it which models the key can
    call, the one GET `anthropic_models` makes. `{"ok": True, "said", "anthropic"}` with the list as
    `anthropic_models` gives it, or `{"ok": False, "said"}`: refused for a 401 or 403, not checked when
    nothing answered or another status came back. Nothing about the key comes back."""
    if not key:
        return {"ok": False, "said": i18n.t("errors.put_key_field_first")}
    seen: dict = {}

    def recording(method, url, headers, payload, wait):
        status, body = (transport or http_call)(method, url, headers, payload, wait)
        seen["status"] = status
        return status, body

    listed = anthropic_models(key, transport=recording, timeout=timeout)
    status = seen.get("status", 0)
    if status in (401, 403):
        return {"ok": False, "said": KEY_REFUSED}
    if status != 200:
        return {"ok": False, "said": KEY_UNCHECKED if status == 0
                else f"The key could not be checked, because {refused_said('Anthropic', status)}"}
    return {"ok": True, "said": KEY_WORKS, "anthropic": listed}


def local_base(url: str | None) -> str:
    """The Ollama address from config, or the default one. Only an http address is taken."""
    text = str(url or "").strip().rstrip("/")
    return text if re.match(r"^https?://[^\s/]+", text) else LOCAL_URL


def local_models(url: str | None = None, transport=None, timeout: float = LOCAL_LIST_TIMEOUT) -> dict:
    """The models pulled into Ollama here, or the fact that Ollama is not there and what to do."""
    base = local_base(url)
    send = transport or http_call
    try:
        status, body = send("GET", f"{base}/api/tags", {}, None, timeout)
    except Exception:
        status, body = 0, ""
    if status != 200:
        return {"running": False, "models": [], "note": i18n.t("errors.ollama_installed_running_install_from"), "url": base}
    try:
        data = json.loads(body)
        names = [str(m.get("name")).strip() for m in data.get("models") or []
                 if isinstance(m, dict) and str(m.get("name") or "").strip()]
    except (ValueError, TypeError, AttributeError):
        return {"running": False, "models": [], "note": i18n.t("errors.ollama_installed_running_install_from"), "url": base}
    return {"running": True, "url": base, "note": "" if names else i18n.t("errors.ollama_running_models_pulled_pull"),
            "models": [{"id": n, "name": n, "hint": f"{n} · on this machine"} for n in names]}


# ------------------------------------------------------------------ parsing

def strip_fences(text: str) -> str:
    out = str(text or "").strip()
    if out.startswith("```"):
        out = FENCE.sub("", out).strip()
    first, last = out.find("{"), out.rfind("}")
    if first >= 0 and last > first:
        out = out[first:last + 1]
    return out


def message_text(data: dict) -> str:
    """The text blocks of a Messages API response, joined.

    A model that thinks sends `thinking` blocks first, empty unless asked otherwise, and they are
    passed over: the answer is in the `text` blocks alone.
    """
    blocks = (data or {}).get("content") or []
    return "".join(b.get("text", "") for b in blocks if isinstance(b, dict) and b.get("type") == "text")



# ------------------------------------------------------------ the smoke run's stub

# A smoke run's loopback stub (the family codebase's third build, 22 October 2026, from Sift's
# `sift_search.py`, since the family's key and model routes ask it too): `IDIOGRAPH_SEARCH_STUB`, a loopback
# address, sends every request to a stub server and every key to a keychain held in memory, so a smoke run
# never reaches the internet, the login keychain or a `.env`.
STUB_ENV = "IDIOGRAPH_SEARCH_STUB"


def stub_base() -> str:
    """The stub server every request goes to in a smoke run, a loopback address alone, or empty."""
    base = os.environ.get(STUB_ENV, "").strip().rstrip("/")
    host = urllib.parse.urlparse(base).hostname or ""
    return base if host in ("127.0.0.1", "localhost", "::1") else ""


class Done:
    """What a run of the `security` tool answers: its code and what it printed."""

    def __init__(self, code: int, out: str = ""):
        self.returncode, self.stdout, self.stderr = code, out, ""


class MemoryKeychain:
    """The keychain in a smoke run, held in this process alone and gone when it ends, so a smoke run
    never reads or writes the login keychain or a `.env`. It answers the `security` tool's three
    commands, and a service never saved or removed holds a stand-in that names it."""

    def __init__(self):
        self.held: dict[str, str | None] = {}

    def value(self, service: str) -> str | None:
        return self.held[service] if service in self.held else f"stub-{service.lower()}"

    def __call__(self, argv, **_):
        act, service = argv[1], argv[argv.index("-s") + 1]
        if act == "add-generic-password":
            self.held[service] = argv[argv.index("-w") + 1]
            return Done(0)
        if act == "delete-generic-password":
            had = self.value(service)
            self.held[service] = None
            return Done(0 if had else 44)
        found = self.value(service)
        return Done(0 if found else 44, (found or "") + "\n")


STUB_KEYCHAIN = MemoryKeychain()


# ---------------------------------------------------------------- transport

def http_call(method: str, url: str, headers: dict, payload: dict | None = None,
              timeout: float = TIMEOUT) -> tuple[int, str]:
    """One HTTP request. Returns the status and the body, and never logs either.

    A status other than 2xx comes back with no body, because an error body can echo a header and
    the key rides in one. A request that never completes is status 0.
    """
    data = None if payload is None else json.dumps(payload).encode("utf-8")
    request = urllib.request.Request(url, data=data, method=method, headers=dict(headers or {}))
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            return int(response.status), response.read().decode("utf-8", "replace")
    except urllib.error.HTTPError as exc:
        return int(exc.code), ""
    except Exception:
        return 0, ""


def http_post(payload: dict, key: str, timeout: float = TIMEOUT) -> tuple[int, str]:
    """POST to the Messages API, the shape this module had before it carried two providers."""
    return http_call("POST", ENDPOINT, anthropic_headers(key), payload, timeout)


# ------------------------------------------------- the OpenAI-style providers (aiwire)

def is_local(provider: str | None) -> bool:
    """A model that runs on this machine: Ollama, or LM Studio."""
    return provider in (LOCAL, LMSTUDIO)


def is_openai(provider: str | None) -> bool:
    return provider in OPENAI_SHAPED


def host_of(url: str | None) -> str:
    """The host (with its port when it has one) an address names, or empty."""
    return urllib.parse.urlparse(str(url or "").strip()).netloc


def address_ok(address: str | None) -> bool:
    """An address a call may go to: https, or http on this machine alone. Nothing else is ever asked."""
    parts = urllib.parse.urlparse(str(address or "").strip())
    if not parts.netloc or not parts.hostname:
        return False
    return parts.scheme == "https" or (parts.scheme == "http" and parts.hostname in LOOPBACK)


def who_of(provider: str, address: str | None = None) -> str:
    """The provider's plain name, or for Another service the host its address names."""
    name = PRESETS.get(provider, {}).get("name")
    return name or host_of(address) or "The service"


def key_service(provider: str, address: str | None = None) -> str:
    """The keychain item a provider's key lives in: its own, so switching provider loses nothing and
    removing one key removes that one alone. Another service's is named by its host."""
    if provider == OTHER:
        return f"{OTHER_KEY_SERVICE} {host_of(address)}".strip()
    return PRESETS[provider]["service"] if provider in PRESETS else KEYCHAIN_SERVICE


def openai_root(provider: str, address: str | None = None) -> str:
    """The address a provider's calls go under, its preset's or the typed one, or empty when there is none
    or it is refused. In a smoke run, while `IDIOGRAPH_SEARCH_STUB` names a loopback stub, every host that is
    not already on this machine is replaced by `{stub}/{provider}`, so no run reaches a real service, and
    LM Studio's preset address too."""
    preset = PRESETS[provider]
    typed = bool(preset.get("address"))
    base = str(address or "").strip().rstrip("/") if typed else preset["base"]
    # LM Studio at the address Settings holds (aipage, 8 November 2026), its usual one when none is set or the
    # one set is refused, and in a smoke run sent to the stub as its preset is
    if provider == LMSTUDIO and address_ok(address):
        base = str(address).strip().rstrip("/")
    if not base or (typed and not address_ok(base)):
        return ""
    stub = stub_base()
    if stub:
        parts = urllib.parse.urlparse(base)
        if not typed or parts.hostname not in LOOPBACK:
            base = f"{stub}/{provider}{parts.path}".rstrip("/")
    return base


def openai_url(provider: str, what: str, address: str | None = None, deployment: str | None = None,
               api_version: str | None = None) -> str:
    """The URL of `chat` or `models` for a provider, empty when its address is missing or refused. Azure's
    chat goes to the deployment, `{address}/openai/deployments/{deployment}/chat/completions?api-version=`."""
    root = openai_root(provider, address)
    if not root:
        return ""
    if provider == AZURE:
        version = urllib.parse.quote(str(api_version or "").strip() or AZURE_API_VERSION)
        if what == "chat":
            name = urllib.parse.quote(str(deployment or "").strip(), safe="")
            return f"{root}/openai/deployments/{name}/chat/completions?api-version={version}"
        return f"{root}/openai/models?api-version={version}"
    return f"{root}/chat/completions" if what == "chat" else f"{root}/models"


def openai_headers(provider: str, key: str | None) -> dict:
    """Bearer for most, `api-key` for Azure. No key, no header (LM Studio, a service with none)."""
    out = {"content-type": "application/json"}
    if key:
        if PRESETS[provider]["header"] == "api-key":
            out["api-key"] = key
        else:
            out["authorization"] = f"Bearer {key}"
    return out


def openai_payload(system: str, user: str, model: str, max_tokens: int | None = None,
                   provider: str = OTHER) -> dict:
    """Model and two turns, system then user. No temperature, and a ceiling only when the caller sets one."""
    payload = {"model": model, "messages": [{"role": "system", "content": system},
                                            {"role": "user", "content": user}]}
    if max_tokens:
        payload[PRESETS.get(provider, {}).get("tokens", "max_tokens")] = int(max_tokens)
    return payload


def openai_no_answer(provider: str, address: str | None) -> str:
    """Nothing answered: LM Studio's server is not running, else the address."""
    if provider == LMSTUDIO:
        return i18n.t("errors.lmstudio_not_running")
    if PRESETS[provider].get("address"):
        return i18n.t("errors.nothing_answered_address", who=who_of(provider, address))
    return i18n.t("errors.did_not_answer_check_connection", who=who_of(provider, address))


def openai_refused(provider: str, address: str | None, status: int, deployment: str | None = None) -> str:
    """A status the call came back with, in plain words through `refused_said`, Azure's 404 naming the
    deployment."""
    if provider == AZURE and status == 404 and str(deployment or "").strip():
        return i18n.t("errors.no_deployment_named", name=str(deployment).strip(), status=status)
    preset = PRESETS[provider]
    return refused_said(who_of(provider, address), status, keyed=bool(preset["keyed"] or preset.get("address")))


def route_problem(provider: str, key, model, address, deployment, listing: bool = False) -> str | None:
    """The one line a provider's route is refused with before any call, or None when it can be asked.
    `listing` is for a model list or Check key, which need no model and no deployment."""
    if provider == ANTHROPIC:
        return None if key else i18n.t("errors.key_add_one_settings_under")
    if provider == LOCAL:
        return None if str(model or "").strip() else i18n.t("errors.local_model_chosen_pick_one")
    preset = PRESETS[provider]
    if preset.get("address"):
        if not str(address or "").strip():
            return i18n.t("errors.no_address_add_one")
        if not address_ok(address):
            return i18n.t("errors.address_must_be_https")
    if preset["keyed"] and not key:
        return i18n.t("errors.key_add_one_settings_under")
    if listing:
        return None
    if preset.get("deployment"):
        return None if str(deployment or "").strip() else i18n.t("errors.no_deployment_add_one")
    if not str(model or "").strip() and not preset["model"]:
        return i18n.t("errors.no_model_chosen_pick_one")
    return None


def openai_model_list(provider: str, key: str | None, address: str | None = None,
                      transport=None, timeout: float = LIST_TIMEOUT) -> dict:
    """The models a provider lists, from `GET {base}/models`, or for Azure none (the deployment is typed).
    `{"models": [...], "source": "live", "note"}` or `{"models": [], "failed": True, "note": ...}`, the
    note the plain line a failure says. Nothing about the key comes back."""
    if provider == AZURE:
        return {"models": [], "source": "typed", "note": ""}
    problem = route_problem(provider, key, None, address, None, listing=True)
    if problem:
        return {"models": [], "failed": True, "note": problem}
    send = transport or http_call
    try:
        status, body = send("GET", openai_url(provider, "models", address), openai_headers(provider, key), None,
                            timeout)
    except Exception:
        status, body = 0, ""
    who = who_of(provider, address)
    if status != 200:
        said = openai_no_answer(provider, address) if status == 0 else openai_refused(provider, address, status)
        return {"models": [], "failed": True, "note": said}
    try:
        data = json.loads(body)
        ids = [str(m.get("id")).strip() for m in (data or {}).get("data") or []
               if isinstance(m, dict) and str(m.get("id") or "").strip()]
    except (ValueError, TypeError, AttributeError):
        return {"models": [], "failed": True, "note": i18n.t("errors.model_s_answer_could_read")}
    names = sorted({i[len("models/"):] if i.startswith("models/") else i for i in ids})
    note = i18n.t("errors.from_list", who=who)
    return {"models": [{"id": n, "name": n, "hint": note} for n in names], "source": "live", "note": note}


def check_openai_key(provider: str, key: str | None, address: str | None = None, transport=None,
                     timeout: float = LIST_TIMEOUT, api_version: str | None = None) -> dict:
    """Check key for an OpenAI-style provider: whether it takes the key, by asking for its list of models
    (Azure's, at `/openai/models`). `{"ok": True, "said", "list"}` or `{"ok": False, "said"}`."""
    if PRESETS[provider]["keyed"] and not key:
        return {"ok": False, "said": i18n.t("errors.put_key_field_first")}
    problem = route_problem(provider, key, None, address, None, listing=True)
    if problem:
        return {"ok": False, "said": problem}
    send = transport or http_call
    try:
        status, _body = send("GET", openai_url(provider, "models", address, None, api_version),
                             openai_headers(provider, key), None, timeout)
    except Exception:
        status = 0
    if status in (401, 403):
        return {"ok": False, "said": KEY_REFUSED}
    if status != 200:
        said = openai_no_answer(provider, address) if status == 0 else openai_refused(provider, address, status)
        return {"ok": False, "said": i18n.t("errors.key_could_checked_because", why=said)}
    return {"ok": True, "said": KEY_WORKS, "list": openai_model_list(provider, key, address, transport, timeout)}


# a route, the provider, the model, the key and the local address a call takes (see `server.ai_route`)

def route_ready(route: dict) -> dict | None:
    """None when a route can be asked, else its refusal: no key for a provider that wants one, no model
    chosen for a local one, no deployment for Azure, an address that is missing or not https (Sift's and
    Trace's AI, and since aiwire the OpenAI-style providers')."""
    provider = route.get("provider") if route.get("provider") in PROVIDERS else ANTHROPIC
    said = route_problem(provider, route.get("key"), route.get("model"), route.get("address"),
                         route.get("deployment"))
    return {"error": said} if said else None


def route_model(route: dict) -> str:
    """The model a route asks, by the name the app gives it, "Opus 5.5", or a local one's name on this
    machine, which Sift's own proposal records as what made it (14 October)."""
    provider = route.get("provider") if route.get("provider") in PROVIDERS else ANTHROPIC
    model = str(route.get("model") or "").strip()
    if is_local(provider):
        return f"{model} on this machine" if model else ""
    if provider in OPENAI_SHAPED:
        model = str(route.get("deployment") or "").strip() if provider == AZURE else (model or PRESETS[provider]["model"])
        who = who_of(provider, route.get("address"))
        return f"{model}, {who}" if model else who
    return model_name(model or MODEL)


def complete_openai(system: str, user: str, provider: str, model: str | None, key: str | None,
                    address: str | None, deployment: str | None, transport, timeout: float | None,
                    max_tokens: int | None, api_version: str | None = None) -> dict:
    """One OpenAI-style chat. `{"text", "truncated"}` or one error line, through `refused_said`."""
    chosen = str(model or "").strip() or PRESETS[provider]["model"]
    if provider == AZURE:
        chosen = str(deployment or "").strip()
    problem = route_problem(provider, key, chosen, address, deployment)
    if problem:
        return {"error": problem}
    send = transport or http_call
    wait = timeout or (LOCAL_TIMEOUT if provider == LMSTUDIO else OPENAI_TIMEOUT)
    try:
        status, body = send("POST", openai_url(provider, "chat", address, deployment, api_version),
                            openai_headers(provider, key),
                            openai_payload(system, user, chosen, max_tokens, provider), wait)
    except Exception:
        status, body = 0, ""
    if status == 0:
        return {"error": openai_no_answer(provider, address)}
    if status != 200:
        return {"error": openai_refused(provider, address, status, deployment)}
    try:
        data = json.loads(body)
        choice = ((data or {}).get("choices") or [{}])[0]
        text = str(((choice or {}).get("message") or {}).get("content") or "")
        finish = (choice or {}).get("finish_reason")
    except (ValueError, TypeError, AttributeError, IndexError):
        return {"error": i18n.t("errors.model_s_answer_could_read")}
    if finish == "content_filter":
        return {"error": i18n.t("errors.model_declined_answer_passage")}
    if not text.strip():
        return {"error": i18n.t("errors.answer_ran_past_length_limit") if finish == "length"
                else i18n.t("errors.answer_carried_text")}
    return {"text": text, "truncated": finish == "length"}


def complete(system: str, user: str, provider: str = ANTHROPIC, model: str | None = None,
             key: str | None = None, local_url: str | None = None, transport=None,
             timeout: float | None = None, max_tokens: int | None = None,
             address: str | None = None, deployment: str | None = None) -> dict:
    """One call to the chosen provider. `{"text": ...}`, with `truncated` when it ran out of room,
    or one error line. Both passes of a suggestion come through here, and the Themes screen's two
    calls, which pass a ceiling of their own. `address` and `deployment` are for the OpenAI-style
    providers that take them (Azure, Another service).
    """
    send = transport or http_call
    if provider in OPENAI_SHAPED:
        return complete_openai(system, user, provider, model, key, address, deployment, transport, timeout,
                               max_tokens)
    if provider == LOCAL:
        chosen = str(model or "").strip()
        if not chosen:
            return {"error": i18n.t("errors.local_model_chosen_pick_one")}
        try:
            status, body = send("POST", f"{local_base(local_url)}/api/chat",
                                {"content-type": "application/json"},
                                local_payload(system, user, chosen, max_tokens), timeout or LOCAL_TIMEOUT)
        except Exception:
            status, body = 0, ""
        if status == 0:
            return {"error": i18n.t("errors.ollama_did_answer_start_choose")}
        if status != 200:
            return {"error": refused_said("Ollama", status, keyed=False)}
        try:
            data = json.loads(body)
            text = str(((data or {}).get("message") or {}).get("content") or "")
        except (ValueError, TypeError, AttributeError):
            return {"error": i18n.t("errors.model_s_answer_could_read")}
        if not text.strip():
            return {"error": i18n.t("errors.local_model_sent_back_nothing")}
        return {"text": text, "truncated": data.get("done_reason") == "length"}

    if not key:
        return {"error": i18n.t("errors.key_add_one_settings_under")}
    payload = anthropic_payload(system, user, model, max_tokens)
    wait = timeout or (THINKING_TIMEOUT if thinks(payload["model"]) else TIMEOUT)
    try:
        status, body = send("POST", ENDPOINT, anthropic_headers(key), payload, wait)
    except Exception:
        return {"error": i18n.t("errors.suggestion_call_did_complete")}
    if status == 0:
        return {"error": i18n.t("errors.suggestion_call_did_complete")}
    if status != 200:
        return {"error": refused_said("Anthropic", status)}
    try:
        data = json.loads(body)
    except (ValueError, TypeError):
        return {"error": i18n.t("errors.model_s_answer_could_read")}
    if not isinstance(data, dict):
        return {"error": i18n.t("errors.model_s_answer_could_read")}
    stop = data.get("stop_reason")
    if stop == "refusal":
        return {"error": i18n.t("errors.model_declined_answer_passage")}
    text = message_text(data)
    if not text.strip():
        return {"error": i18n.t("errors.answer_ran_past_length_limit") if stop == "max_tokens" else i18n.t("errors.answer_carried_text")}
    return {"text": text, "truncated": stop == "max_tokens"}

def __getattr__(name: str) -> str:
    """The refusals other modules and the checks name as this module's, each read in the run's language when
    asked for (the text layer, 28 October 2026)."""
    said = {
        "LOCAL_MISSING": lambda: i18n.t("errors.ollama_installed_running_install_from"),
        "LOCAL_EMPTY": lambda: i18n.t("errors.ollama_running_models_pulled_pull"),
        "LOCAL_DOWN": lambda: i18n.t("errors.ollama_did_answer_start_choose"),
        "NO_LOCAL_MODEL": lambda: i18n.t("errors.local_model_chosen_pick_one"),
        "NO_KEY": lambda: i18n.t("errors.key_add_one_settings_under"),
        "AI_OFF": lambda: i18n.t("errors.ai_features_off_turn_them"),
        "REFUSED": lambda: i18n.t("errors.model_declined_answer_passage"),
        "TOO_LONG": lambda: i18n.t("errors.answer_ran_past_length_limit"),
        "NOT_JSON": lambda: i18n.t("errors.model_s_answer_could_read"),
    }
    if name in said:
        return said[name]()
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
