#!/usr/bin/env python3
"""Sift's AI proposals, an experiment, off unless the app's AI switch and the screening's own are on.

Screening works whole by hand. The switch in Settings, `ai_suggest`, is the app's one switch for
every AI feature, and with it off Sift shows no proposal and no AI control at all. Beside it each
screening has its own switch and prompt in `sift.json` beside the CSV, `{"ai_proposals": false,
"prompt": ""}`, off on every screening until he turns it on in Sift's settings card. An empty prompt
is the default one here, DEFAULT_PROMPT, which the card shows for him to edit.

A proposal is one call through `ai_suggest.complete`, so it goes out with the provider, the model
and the key a suggestion on the turn screen takes, and no key of its own. It sends one record, its
title, authors, year, journal and abstract, with the stage's reason codes from `reasons.csv`, and
asks for include, maybe or exclude, a code on an exclude, and as grounds a stretch of the title or
abstract word for word. At full text it sends the same, since the app reads no PDF's text. The
answer is read strictly and written into Sift's own columns through `sift.write_ai`, never the
review's proposal columns and never a decision. He decides every record. The bench in Sift's
settings, `trial`, sends one record he picks with the prompt as the box holds it, saved or not, and
answers what came back, writing nothing anywhere.

The transport is a parameter, the shape `complete` takes, so the suite runs against a stub of its
own and nothing reaches a model.
"""
from __future__ import annotations

import sift_words
import json
from pathlib import Path

import ai_suggest as ai_mod
# a route's readiness and its model's name, the family's since 22 October 2026, which Trace's AI asks too
from ai_suggest import route_model, route_ready  # noqa: F401
import locks
import sift

SETTINGS_NAME = "sift.json"
OFF = ai_mod.AI_OFF
# This module's words for a person, read in the run's language when said: inside the module through `_w`,
# from others and the checks as the module's names (`__getattr__`)
SAID = {
    "SIFT_OFF": lambda: sift_words.t("sift_server.ai.off"),
    "NO_DECISION": lambda: sift_words.t("sift_server.ai.no_decision"),
    "NOTHING_TO_READ": lambda: sift_words.t("sift_server.ai.nothing_to_read"),
}


def _w(name: str) -> str:
    return SAID[name]()


def __getattr__(name: str) -> str:
    """This module's words other modules and the checks name, read in the run's language."""
    if name in SAID:
        return SAID[name]()
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
NOT_JSON = ai_mod.NOT_JSON
GROUNDS_MAX = 600
# the room an answer gets, beyond a model that thinks, which takes its own (see ai_suggest)
MAX_TOKENS = 400

DEFAULT_PROMPT = """You help screen the records of a systematic review. You see one record at a time, at the {stage} stage, and propose a decision. The reviewer reads your proposal and makes every decision.

Judge the record by its title and abstract against the review's reasons for exclusion at this stage:
{codes}

Propose exclude when the title or abstract plainly meets one of these reasons, and give that reason's code. Propose include when nothing in them meets a reason. Propose maybe when they leave it open, and take maybe over a guess.

As grounds, copy the short stretch of the title or abstract your proposal rests on, word for word, never a summary."""

SHAPE = "\n".join([
    "Answer with strict JSON and nothing else, in this shape:",
    '{"decision": "include", "reason": "", "grounds": "the words, copied exactly"}',
    "decision is include, maybe or exclude. reason is the code of the reason on an exclude, and empty otherwise.",
])


# ------------------------------------------------------------------ settings

def settings_path(folder) -> Path:
    return Path(folder) / SETTINGS_NAME


def settings(folder) -> dict:
    """The screening's own AI settings from `sift.json` beside the CSV: `ai_proposals`, off with no
    file, and `prompt`, empty for the default. A file that cannot be read counts as none."""
    try:
        data = json.loads(settings_path(folder).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        data = {}
    if not isinstance(data, dict):
        data = {}
    prompt = data.get("prompt")
    return {"ai_proposals": data.get("ai_proposals") is True, "prompt": prompt if isinstance(prompt, str) else ""}


def save_settings(folder, ai_proposals=None, prompt=None, wait: float | None = None) -> dict:
    """The switch, the prompt or both written to `sift.json`, whole, through a temporary file, under
    the screening's lock, every other key it holds kept. A prompt the same as the default is kept as
    empty, so a later default reaches it."""
    sift.load(folder)
    with locks.held(sift.lock_path(folder), wait):
        try:
            data = json.loads(settings_path(folder).read_text(encoding="utf-8"))
        except (OSError, ValueError):
            data = {}
        if not isinstance(data, dict):
            data = {}
        if ai_proposals is not None:
            data["ai_proposals"] = bool(ai_proposals)
        if prompt is not None:
            text = str(prompt).replace("\r\n", "\n").strip()
            data["prompt"] = "" if text == DEFAULT_PROMPT.strip() else text
        data.setdefault("ai_proposals", False)
        data.setdefault("prompt", "")
        sift.write_atomic(settings_path(folder), json.dumps(data, indent=2, ensure_ascii=False) + "\n")
    return settings(folder)


def prompt_of(held: dict) -> str:
    """The prompt a proposal goes out with: his own when he has written one, else the default."""
    return str(held.get("prompt") or "").strip() or DEFAULT_PROMPT


# ------------------------------------------------------------------- the call

def codes_block(codes: list[dict]) -> str:
    if not codes:
        return "No reasons are named for this stage."
    return "\n".join(f"{r['code']}: {r['meaning']}" if r.get("meaning") else r["code"] for r in codes)


def system_prompt(template: str, stage: str, codes: list[dict]) -> str:
    """The prompt with the stage and its codes in place of `{stage}` and `{codes}`, and the shape of
    the answer after it when the prompt does not ask for it, so an edited prompt still comes back
    readable."""
    text = str(template or DEFAULT_PROMPT).replace("{stage}", sift.STAGE_WORDS[stage]).replace("{codes}", codes_block(codes))
    return text if '"decision"' in text else f"{text}\n\n{SHAPE}"


def user_message(view: dict, stage: str) -> str:
    """One record as the call sends it: its id, title, authors, year, journal and abstract."""
    lines = [f"Record {view['rec_id']}, at {sift.STAGE_WORDS[stage]}.", f"Title: {view['title']}"]
    for key, word in (("authors", "Authors"), ("year", "Year"), ("journal", "Journal")):
        if view.get(key):
            lines.append(f"{word}: {view[key]}")
    lines.append("Abstract:")
    lines.append(view["abstract"] or "(none)")
    return "\n".join(lines)


def parse(text: str, codes: list[dict], stage: str, truncated: bool = False) -> dict:
    """The answer read strictly: its decision in the files' words, a reason code of the stage on an
    exclude when the stage has any, none otherwise, and its grounds on one line. Anything else is one
    error line and nothing is written."""
    try:
        data = json.loads(ai_mod.strip_fences(text))
    except (ValueError, TypeError):
        return {"error": ai_mod.TOO_LONG if truncated else NOT_JSON}
    if not isinstance(data, dict):
        return {"error": NOT_JSON}
    word = sift.decision_word(data.get("decision"))
    if word not in sift.DECISIONS:
        return {"error": _w("NO_DECISION")}
    reason = sift.one_line(data.get("reason"))
    known = {r["code"].lower(): r["code"] for r in codes}
    if word == "exclude" and known:
        if reason.lower() not in known:
            return {"error": sift_words.t("sift_server.ai.not_a_code", reason=reason or sift_words.t("sift_server.ai.no_reason"),
                                stage=sift.stage_said(stage))}
        reason = known[reason.lower()]
    elif word != "exclude":
        reason = ""
    return {"decision": word, "reason": reason, "grounds": sift.one_line(data.get("grounds"))[:GROUNDS_MAX]}


def asked(folder, rec_id, stage, route: dict, transport=None, prompt: str | None = None) -> dict:
    """One record asked of the app's AI and its answer read strictly, nothing written: the record and
    the stage asked about with the decision, the reason and the grounds, or one error line. `prompt`
    is a prompt of his not yet saved, the bench's, and with none the screening's own goes."""
    sc = sift.load(folder)
    entries = sift.read_log(folder)
    held = sift.states(entries)
    rec, stage = sift.checked(sc, held, rec_id, stage)
    view = sift.record_view(sc, held, rec)
    if not view["title"] and not view["abstract"]:
        return {"error": _w("NOTHING_TO_READ")}
    refused = route_ready(route)
    if refused:
        return refused
    codes = sift.reasons(folder)[stage]
    template = prompt if isinstance(prompt, str) and prompt.strip() else prompt_of(settings(folder))
    provider = route.get("provider") if route.get("provider") in ai_mod.PROVIDERS else ai_mod.ANTHROPIC
    answer = ai_mod.complete(system_prompt(template, stage, codes), user_message(view, stage),
                             provider, route.get("model"), route.get("key"),
                             route.get("local_url"), transport, None,
                             None if provider == ai_mod.ANTHROPIC and ai_mod.thinks(route.get("model")) else MAX_TOKENS,
                             route.get("address"), route.get("deployment"))
    if "error" in answer:
        return answer
    parsed = parse(answer["text"], codes, stage, bool(answer.get("truncated")))
    if "error" in parsed:
        return parsed
    return dict(parsed, rec_id=rec, stage=stage, title=view["title"], abstract=view["abstract"], n=view.get("n"))


def propose(folder, rec_id, stage, route: dict, transport=None) -> dict:
    """One record's proposal from the app's AI, written into Sift's own columns, or one error line
    with nothing written. `route` is the app's own, the provider, the model, the key and the local
    address a suggestion takes (see `server.ai_route`)."""
    got = asked(folder, rec_id, stage, route, transport)
    if "error" in got:
        return got
    out = sift.write_ai(folder, got["rec_id"], got["stage"], got["decision"], got["reason"], got["grounds"],
                        model=route_model(route))
    return dict(out, asked={"rec_id": got["rec_id"], "stage": got["stage"]})


def trial(folder, rec_id, stage, route: dict, prompt: str | None = None, transport=None) -> dict:
    """The bench in Sift's settings: one record asked with the prompt as the box holds it, saved or
    not, and what came back answered, never written anywhere, the CSV, the log and sift.json as they
    were. `found` says whether the title or the abstract holds the grounds word for word."""
    got = asked(folder, rec_id, stage, route, transport, prompt)
    if "error" in got:
        return got
    _, found = sift.ground_spans(got["abstract"], got["grounds"])
    in_title = bool(got["grounds"]) and "".join(got["grounds"].split()).lower() in "".join(got["title"].split()).lower()
    return {"rec_id": got["rec_id"], "n": got["n"], "stage": got["stage"], "decision": got["decision"],
            "reason": got["reason"], "grounds": got["grounds"], "found": bool(found) or in_title}


def plan(folder, stage, which: str) -> dict:
    """The records a proposal for the round would ask about, before any call: the round's undecided
    records with no proposal of Sift's own at the stage yet, one call each."""
    sc = sift.load(folder)
    entries = sift.read_log(folder)
    held = sift.states(entries)
    stage = sift.stage_key(stage)
    ids = [rec for rec in sift.listed(sc, entries, stage, which)
           if not sift.state_of(sc, held, rec, stage)["decision"]
           and not any(p["source"] == sift.FROM_SIFT for p in sift.proposals_of(sc, rec, stage))]
    return {"ids": ids, "calls": len(ids), "stage": stage, "round": which}
