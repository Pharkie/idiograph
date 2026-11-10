from __future__ import annotations

import inspect
import json

import ai_suggest as ai_mod

from .support import GRAVITY_QUESTION, check
import statement_prompts


def anthropic_fake(fn):
    """A transport in the shape `complete` calls, `(method, url, headers, payload, timeout)`, around
    a fake that takes the payload, the key and the timeout, the shape these checks were written in."""
    def send(method, url, headers, payload, timeout):
        return fn(payload, (headers or {}).get("x-api-key"), timeout)
    return send


def test_key_and_suggest(scratch):
    print("\n16. The key, the prompt and the suggestion call")
    # a file written here, never the real one: nothing in this suite reads Tools/idiograph/.env
    env = scratch / "ai" / ".env"
    env.parent.mkdir(parents=True, exist_ok=True)
    check("a missing file is no key", ai_mod.read_key(env) is None)
    env.write_text("# a comment\n\nANTHROPIC_API_KEY=abc123\n", encoding="utf-8")
    check("a plain line parses", ai_mod.read_key(env) == "abc123")
    env.write_text('export ANTHROPIC_API_KEY="abc123"\n', encoding="utf-8")
    check("export and quotes are tolerated", ai_mod.read_key(env) == "abc123")
    env.write_text("ANTHROPIC_API_KEY= 'abc 123' \n", encoding="utf-8")
    check("spaces around the value are trimmed", ai_mod.read_key(env) == "abc 123")
    env.write_text("# ANTHROPIC_API_KEY=commented\nOTHER=1\n", encoding="utf-8")
    check("a commented line is not a key", ai_mod.read_key(env) is None)
    env.write_text("ANTHROPIC_API_KEY=\n", encoding="utf-8")
    check("an empty placeholder is not a key", ai_mod.read_key(env) is None)

    # The keychain, through a runner that stands in for the `security` tool. Nothing in this suite
    # runs `security` itself, so no real key is ever read, written or printed.
    calls = []

    class Done:
        def __init__(self, code, out=""):
            self.returncode, self.stdout, self.stderr = code, out, ""

    def runner(code, out=""):
        def run(argv, **kw):
            calls.append(list(argv))
            return Done(code, out)
        return run

    def angry(argv, **kw):
        calls.append(list(argv))
        raise OSError("no keychain on this machine")

    check("a keychain miss is no key", ai_mod.keychain_key(runner=runner(44)) is None)
    check("a keychain hit is the value, with the newline taken off",
          ai_mod.keychain_key(runner=runner(0, "from-the-keychain\n")) == "from-the-keychain")
    check("a keychain that throws is no key and never a traceback",
          ai_mod.keychain_key(runner=angry) is None)
    check("the lookup asks for the one service by name",
          calls[0] == ["security", "find-generic-password", "-s", "ANTHROPIC_API_KEY", "-w"],
          str(calls[0]))

    env.write_text("ANTHROPIC_API_KEY=from-the-file\n", encoding="utf-8")
    check("the file is read before the keychain",
          ai_mod.find_key(env, runner=runner(0, "from-the-keychain")) == "from-the-file")
    check("the status names the file as the source",
          ai_mod.key_status(env, runner=runner(0, "from-the-keychain")) == {"set": True, "source": "file"})
    env.write_text("OTHER=1\n", encoding="utf-8")
    check("with no key in the file the keychain answers",
          ai_mod.find_key(env, runner=runner(0, "from-the-keychain")) == "from-the-keychain")
    check("the status names the keychain",
          ai_mod.key_status(env, runner=runner(0, "x")) == {"set": True, "source": "keychain"})
    check("no key anywhere is said plainly",
          ai_mod.key_status(env, runner=runner(44)) == {"set": False, "source": None})

    # saving and removing, and the one call the value is allowed to appear in
    calls.clear()
    secret = "sk-ant-" + "not-a-real-key-99"
    saved = ai_mod.save_key(secret, runner=runner(0), account="tester", env_path=env)
    check("the key goes to the keychain", saved == {"saved": True, "source": "keychain"}, str(saved))
    added = [c for c in calls if "add-generic-password" in c]
    check("the save replaces any earlier item under the one service",
          len(added) == 1 and added[0][:2] == ["security", "add-generic-password"] and "-U" in added[0]
          and added[0][added[0].index("-s") + 1] == "ANTHROPIC_API_KEY"
          and added[0][added[0].index("-a") + 1] == "tester",
          " ".join(added[0][:6]))
    elsewhere = [c for c in calls if c is not added[0]]
    check("the key string is in that one call and in nothing else",
          sum(1 for c in calls if secret in c) == 1
          and not any(secret in " ".join(c) for c in elsewhere),
          f"{len(calls)} calls recorded")
    check("nothing the save returns carries the key", secret not in json.dumps(saved), str(saved))
    check("an empty field is refused before anything is run",
          "error" in ai_mod.save_key("   ", runner=runner(0)))
    refused = ai_mod.save_key(secret, runner=runner(1), env_path=env)
    check("a save the keychain refuses is one line, and no file is written",
          refused == {"error": "The keychain would not take the key."} and ai_mod.read_key(env) is None,
          "the .env is only written on a machine with no keychain at all")
    calls.clear()
    check("removing deletes the item under that service",
          ai_mod.clear_key(runner=runner(0), env_path=env) == {"cleared": True}
          and calls[0] == ["security", "delete-generic-password", "-s", "ANTHROPIC_API_KEY"],
          str(calls))
    check("removing when there is nothing there says so",
          ai_mod.clear_key(runner=runner(44), env_path=env) == {"cleared": False})
    check("the tests never reach the real keychain or the real .env",
          all(c[0] == "security" for c in calls) and ai_mod.security_missing(runner=runner(0)) is False,
          "every call went to the fake runner")

    # the endpoints, with the store itself stood in for, so no keychain is touched
    import server as server_mod
    passed_through = {}
    real = (ai_mod.save_key, ai_mod.clear_key, ai_mod.key_status)
    try:
        ai_mod.save_key = lambda value, **kw: passed_through.update(value=value) or {"saved": True}
        ai_mod.clear_key = lambda **kw: {"cleared": True}
        ai_mod.key_status = lambda *a, **kw: {"set": True, "source": "keychain"}
        answer = server_mod.api_key({"key": secret})
        check("the save endpoint answers that it saved it and nothing else",
              answer == {"saved": True}, str(answer))
        check("the endpoint hands the key straight to the store and keeps no copy",
              passed_through.get("value") == secret and secret not in json.dumps(answer))
        check("the remove endpoint answers plainly",
              server_mod.api_key({"clear": True}) == {"cleared": True})
        check("the status endpoint says whether and where, never what",
              server_mod.api_key_status({}) == {"set": True, "source": "keychain"})

        def explode(value, **kw):
            raise RuntimeError(f"the argv was security -w {value}")

        ai_mod.save_key = explode
        blew = server_mod.api_key({"key": secret})
        check("an exception from below never carries the key out",
              blew == {"error": "The key could not be stored."} and secret not in json.dumps(blew),
              str(blew))
    finally:
        ai_mod.save_key, ai_mod.clear_key, ai_mod.key_status = real
    # Sift's databases and its Zotero sync, whose `key` ops carry a key, joined from Sift's own routes (the
    # family codebase's third build, 22 October 2026)
    check("the verbose log says the path of a key request and never its body",
          server_mod.SILENT == ("/api/key", "/api/databases", "/api/zotero")
          and "the body is never logged" in inspect.getsource(server_mod.Handler.log_message))
    check("a settings save can never carry the key",
          '"key"' not in inspect.getsource(server_mod.api_settings),
          "the key goes to /api/key and the keychain, never to config.json")

    check("no key means one line, and no call",
          statement_prompts.suggest("a turn", key=None)["error"] == ai_mod.NO_KEY)

    sent = {}

    def fake(payload, key, timeout):
        sent.update(payload=payload, key=key, timeout=timeout)
        body = {"content": [{"type": "text", "text": json.dumps(
            {"tags": ["falling", "instruments"], "candidates": ["Watches the instruments and keeps steady"]})}]}
        return 200, json.dumps(body)

    out = statement_prompts.suggest("Looking at the instruments", prior="And then?", timecode="12:04",
                         name="Wren", guidance=["Experience, not event."],
                         examples=["A mood that does not survive the stairs"], key="k", transport=anthropic_fake(fake),
                         research_question=GRAVITY_QUESTION)
    check("tags and candidates come back parsed",
          out == {"tags": ["falling", "instruments"],
                  "candidates": ["Watches the instruments and keeps steady"]}, str(out))
    system = sent["payload"]["system"]
    check("the statement rules ride in the system prompt",
          "Experience, not event." in system and "fifteen at most" in system
          and "No em dashes" in system and "A mood that does not survive the stairs" in system)
    user = sent["payload"]["messages"][0]["content"]
    check("the user message carries the turn, the turn before it and the timecode",
          "Looking at the instruments" in user and "And then?" in user and "12:04" in user)

    # two passes: drafts first, then the critic keeps the strongest one to three
    seen, systems = [], []

    def two_pass(payload, key, timeout):
        seen.append(payload["messages"][0]["content"])
        systems.append(payload["system"])
        if len(seen) == 1:
            body = {"tags": ["blood", "focus"], "candidates": [f"draft {i}" for i in range(1, 8)]}
        else:
            body = {"tags": ["blood"], "candidates": ["Blood stops, attention narrows to the dials"]}
        return 200, json.dumps({"content": [{"type": "text", "text": json.dumps(body)}]})

    pruned = statement_prompts.suggest("Blood stops moving.", key="k", transport=anthropic_fake(two_pass))
    check("the first pass asks for drafts and the second hands them back with the critic's ask",
          len(seen) == 2 and "draft statements" in seen[0]
          and "- draft 7" in seen[1] and "Drop any that fail" in seen[1])
    check("the critic's answer is what comes back",
          pruned == {"tags": ["blood"], "candidates": ["Blood stops, attention narrows to the dials"]},
          str(pruned))
    check("the system prompt is sent unchanged in both passes, the critic's ask rides in the user message",
          len(systems) == 2 and systems[0] == systems[1]
          and "Drop any that fail" not in systems[1] and "Drop any that fail" not in statement_prompts.DEFAULT_PROMPT)
    seen.clear()

    def flaky(payload, key, timeout):
        seen.append(1)
        if len(seen) == 1:
            body = {"tags": ["t"], "candidates": ["a", "b", "c", "d"]}
            return 200, json.dumps({"content": [{"type": "text", "text": json.dumps(body)}]})
        return 500, ""

    check("a failed second pass leaves the first pass's drafts, cut to three",
          statement_prompts.suggest("x", key="k", transport=anthropic_fake(flaky)) == {"tags": ["t"], "candidates": ["a", "b", "c"]})
    seen.clear()

    def nothing(payload, key, timeout):
        seen.append(1)
        body = {"tags": ["logistics"], "candidates": []}
        return 200, json.dumps({"content": [{"type": "text", "text": json.dumps(body)}]})

    check("a turn with nothing experiential comes back after one call, tags and no candidates",
          statement_prompts.suggest("yes", key="k", transport=anthropic_fake(nothing)) == {"tags": ["logistics"], "candidates": []}
          and len(seen) == 1)
    check("the first pass may keep up to ten drafts",
          len(statement_prompts.parse_suggestions(json.dumps({"tags": ["a"], "candidates": list("abcdefghijkl")}),
                                       statement_prompts.DRAFTS)["candidates"]) == 10)

    # the prompt is a template, and the default is the prompt as it was sent before
    guidance = ["Experience, not event.", "One idea each."]
    examples = ["A mood that does not survive the stairs"]
    built = statement_prompts.system_prompt(guidance, examples, research_question=GRAVITY_QUESTION)
    check("both placeholders are gone once they are filled",
          "{guidance}" not in built and "{examples}" not in built
          and "{guidance}" in statement_prompts.DEFAULT_PROMPT and "{examples}" in statement_prompts.DEFAULT_PROMPT)
    own = statement_prompts.system_prompt(guidance, examples, "Read the turn.\n{guidance}\nAnswer in JSON.")
    check("a template of his own is sent as it stands",
          own == "Read the turn.\n- Experience, not event.\n- One idea each.\nAnswer in JSON.", repr(own))
    check("a template with no guidance block in it is still used",
          statement_prompts.system_prompt(guidance, examples, "Say something useful. Answer in JSON.")
          == "Say something useful. Answer in JSON.")
    no_json = statement_prompts.system_prompt(guidance, examples, "Say something useful.")
    check("a template with no JSON in it takes the shape instruction on the end",
          no_json.startswith("Say something useful.") and no_json.endswith(statement_prompts.SHAPE)
          and '{"tags"' in no_json, "so the answer stays parseable whatever he does to the prompt")
    check("an empty examples block collapses rather than leaving a hole",
          "\n\n\n" not in statement_prompts.system_prompt(guidance, []))
    check("an empty template falls back to the default",
          statement_prompts.system_prompt(guidance, examples, "   ", GRAVITY_QUESTION) == built)
    statement_prompts.suggest("a turn", key="k", transport=anthropic_fake(fake), template="Only this. JSON.", model="a-later-model")
    check("the template and the model from config are what is sent",
          sent["payload"]["system"] == "Only this. JSON." and sent["payload"]["model"] == "a-later-model",
          sent["payload"]["model"])

    fenced = statement_prompts.parse_suggestions('```json\n{"tags": ["a"], "candidates": ["b", "c"]}\n```')
    check("a fenced answer parses", fenced == {"tags": ["a"], "candidates": ["b", "c"]}, str(fenced))
    chatty = statement_prompts.parse_suggestions('Here you go: {"tags": ["a"], "candidates": []} hope that helps')
    check("a chatty answer still yields its JSON", chatty["tags"] == ["a"], str(chatty))
    check("eight tags at most and three candidates at most",
          statement_prompts.parse_suggestions(json.dumps({"tags": list("abcdefghijk"),
                                               "candidates": ["1", "2", "3", "4", "5"]}))
          == {"tags": list("abcdefgh"), "candidates": ["1", "2", "3"]})
    check("an unreadable answer is one error line, never a crash",
          "error" in statement_prompts.parse_suggestions("no json here at all"))

    def refuse(payload, key, timeout):
        return 401, "{\"error\": \"do not print me\"}"

    denied = statement_prompts.suggest("a turn", key="k", transport=anthropic_fake(refuse))
    check("an API error is one line in plain words with the status in brackets and nothing of the body (17 October, later)",
          denied == {"error": "Anthropic refused the key (HTTP 401)."}, str(denied))

    def broken(payload, key, timeout):
        raise OSError("no network")

    check("a transport that throws does not reach the interface as a traceback",
          statement_prompts.suggest("a turn", key="k", transport=anthropic_fake(broken))["error"]
          == "The suggestion call did not complete.")
