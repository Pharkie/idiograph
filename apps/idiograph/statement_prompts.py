"""Idiograph's statements prompt (22 October 2026, the family codebase's fourth build, from ai_suggest.py):
concept tags and candidate statements for one turn, off until Adam turns them on. The prompt, its rules, its
shape and its two passes, the drafts and the critic, the key quotes he took, the research question, the test
bench's sample turn from the demo, and the parse of an answer, on the family's transport, `ai_suggest`, which
picks the provider and holds the key. `DEFAULT_PROMPT` is the default of Idiograph's `ai_prompt` setting.

Nothing here writes to a workbook. The endpoint answers with tags and three candidates, and the interface
only puts one into the statement field when Adam clicks it.
"""
from __future__ import annotations

import csv
import json
import re
from pathlib import Path

import ai_suggest as ai_mod

# The test bench in settings runs on one turn of the demo case, never on a participant's words,
# because the app may be shown or shared. The turn is found by its opening words, so a rebuild of
# the demo's timecodes leaves the choice where it was.
SAMPLE_OPENS = "My hands were shaking"

RULES = [
    "Present tense.",
    "One experiential claim per statement, phrased as what is experienced, not as a topic.",
    "Drop the subject where the meaning survives: 'Waking before the house does', not 'She wakes early'.",
    "Grounded in the participant's own words, a level above paraphrase.",
    "Name the phenomenon the research question is about, never 'it'.",
    "Mark the participant's stance: welcome, jarring, a relief, unexpected, feared.",
    "No causal language: never say why something happened.",
    "No therapeutic or psychological jargon.",
    "Three to ten words is the norm, fifteen at most.",
    "No em dashes and no semicolons.",
]

# The shape instruction is required, because the parse below reads strict JSON. A template Adam
# has edited down to nothing else keeps this, appended, so a suggestion still comes back readable.
SHAPE = "\n".join([
    "Answer with strict JSON and nothing else, in this shape:",
    '{"tags": ["...", "..."], "candidates": ["...", "...", "..."]}',
    "Four to eight tags, each one or two words, naming what is at stake in the passage.",
    "One to three candidates: one when the passage is short or holds a single experiential claim, up",
    "to three for a longer passage, never padded, ordered from the closest to the participant's words",
    "to the most interpretative. When the passage holds nothing experiential (logistics, a yes, a",
    "repeat of the question), return the tags and an empty candidates list.",
])

# Two passes. The first asks for more drafts than will be kept, the second hands them back with
# the rules and keeps the strongest one to three. The critic's instruction rides in the user
# message, so the system prompt Adam edits in settings is sent unchanged both times.
DRAFTS = 10
DRAFT_ASK = (f"Tags, then up to {DRAFTS} draft statements for this passage only, more than you will keep, "
             "each a different reading of what is experienced.")
CRITIC_ASK = "\n".join([
    "Check each draft against the definition of an experiential statement and every rule in the",
    "system prompt. Drop any that fail: a bare event or narrative fact, a topic rather than an",
    "experience, a stance dropped, ambivalence smoothed over, a cause, jargon, off the research",
    "question. Rewrite any that nearly pass. Then return the tags and",
    "the strongest one to three, one when the passage is short or holds a single experiential claim,",
    "up to three for a longer passage, never padded, ordered from the closest to the participant's",
    "words to the most interpretative.",
])

# The key quotes he has already taken from the turn, when there are any: the statement he wants is
# most likely about those words. They go after the turn and before the ask, in both passes, ten at
# most and each cut at 400 characters. The whole turn still goes, unchanged.
QUOTES_MAX = 10
QUOTE_CHARS = 400
QUOTES_LEAD = ("The analyst took these words from the passage as key quotes. Centre the statements on them, "
               "reading them in the light of the whole passage:")

# The prompt as sent, with `{guidance}` and `{examples}` filled in as bulleted blocks and
# `{research_question}` with the project's question (see question_block). It is the default for the
# `ai_prompt` key in config.json, and the settings panel edits it from there.
RESEARCH_QUESTION = "{research_question}"
DEFAULT_PROMPT = "\n".join([
    "You help a researcher doing Interpretative Phenomenological Analysis (IPA, Smith, Flowers and",
    "Larkin) at step 3: writing experiential statements for one interview passage. The statement box",
    "is empty. You offer first suggestions that he rewrites or discards.",
    "",
    RESEARCH_QUESTION,
    "",
    "An experiential statement is a concise interpretative summary of what matters to the",
    "participant in a passage and how. It captures what the experience was like for the",
    "participant, or what they made of it, with their stance: the concern, what is done, felt or",
    "noticed. It stays grounded in the participant's words, in the analyst's own words a step above",
    "paraphrase. Naming what the experience was like, with the stance, is enough. A bare event, a",
    "narrative fact, a topic label or a description that drops the stance is not a statement. Keep",
    "ambivalence as it was said, never smoothed into gladness. The participant's own comparisons and",
    "evaluations are their reflection on the experience and stand in their own terms. A statement",
    "that explains why is too far: never a cause.",
    "",
    "Attend to linguistic quirks and the participant's own phrasing, to cultural difference and",
    "a second language, to emotional signifiers however small, and to existential import, which",
    "lives in the experience itself: what it touches in the participant's sense of body, self, time,",
    "safety, others or the world, where it does.",
    "",
    "His guidance, in his own words:",
    "{guidance}",
    "",
    "Every candidate statement must follow these rules:",
] + [f"- {r}" for r in RULES] + [
    "",
    "Statements he has written himself, as the register to match:",
    "{examples}",
    "",
    SHAPE,
])


def question_block(question: str | None) -> str:
    """The project's research question as the prompt says it, or nothing when there is none.

    "The study asks: <question>", then the sentence that makes it what every statement answers.
    With no question both go, so the prompt never names a question it does not have.
    """
    asked = " ".join(str(question or "").split())
    if not asked:
        return ""
    if asked[-1] not in ".?!":
        asked += "."
    return (f"The study asks: {asked} Every statement answers that question for this passage: what "
            "matters to the participant here, and in what way it matters.")


def system_prompt(guidance: list[str], examples: list[str], template: str | None = None,
                  research_question: str | None = None) -> str:
    """The template from config with its blocks filled in.

    `{guidance}` and `{examples}` become bulleted blocks, and an empty block collapses rather than
    leaving a hole. `{research_question}` becomes the project's question, and goes with its
    sentence when the project has none. A template with no `{guidance}` or no
    `{research_question}` in it is sent as it stands, because Adam may want one without. A
    template with no JSON in it takes the shape instruction on the end, so the answer stays
    parseable whatever else he has done to it.
    """
    text = str(template or "").strip() or DEFAULT_PROMPT
    text = text.replace(RESEARCH_QUESTION, question_block(research_question))
    text = text.replace("{guidance}", ai_mod.bullets(guidance)).replace("{examples}", ai_mod.bullets(examples))
    text = re.sub(r"\n{3,}", "\n\n", text).strip()
    if "JSON" not in text:
        text = f"{text}\n\n{SHAPE}"
    return text


def clean_quotes(value) -> list[str]:
    """The key quotes a page sent: a list of strings alone, the empty ones dropped, ten at most and
    each cut at 400 characters. Anything else, a string, a number or a list with anything but
    strings in it, is none."""
    if not isinstance(value, list) or not all(isinstance(q, str) for q in value):
        return []
    return [q.strip()[:QUOTE_CHARS] for q in value if q.strip()][:QUOTES_MAX]


def user_message(turn: str, prior: str = "", timecode: str = "", name: str = "",
                 drafts: list[str] | None = None, quotes: list[str] | None = None) -> str:
    """The turn for the first pass, or the turn with the drafts and the critic's ask for the second.
    The key quotes, when any came, stand between the turn and the rest in both."""
    parts = []
    if prior.strip():
        parts.append(f"The interviewer's preceding passage:\n{prior.strip()}")
    who = name.strip() or "The participant"
    stamp = f" at {timecode}" if timecode else ""
    parts.append(f"{who}'s passage{stamp}:\n{turn.strip()}")
    taken = clean_quotes(quotes) if quotes else []
    if taken:
        parts.append(f"{QUOTES_LEAD}\n{ai_mod.bullets(taken)}")
    if drafts is None:
        parts.append(DRAFT_ASK)
    else:
        parts.append("Your drafts for this passage:\n" + ai_mod.bullets(drafts))
        parts.append(CRITIC_ASK)
    return "\n\n".join(parts)


def build_payload(turn: str, prior: str, timecode: str, name: str,
                  guidance: list[str], examples: list[str],
                  template: str | None = None, model: str | None = None,
                  drafts: list[str] | None = None, research_question: str | None = None,
                  quotes: list[str] | None = None) -> dict:
    """The Messages API body for one pass, as `complete` sends it."""
    return ai_mod.anthropic_payload(system_prompt(guidance, examples, template, research_question),
                             user_message(turn, prior, timecode, name, drafts, quotes), model)


# --------------------------------------------------------------- the sample

def sample_turn(path: Path) -> dict:
    """One participant turn from the demo transcript, with the interviewer's turn before it.

    Read at request time from the demo CSV and from nowhere else. The turn that opens with
    `SAMPLE_OPENS` is the one, and the longest participant turn stands in if it has gone. The bench
    shows `prior` above its box and `turn` in it, and sends `time` and `name` with them, the four
    fields the button under the statement field sends. `text` is the older one-box form.
    """
    try:
        with Path(path).open(encoding="utf-8-sig", newline="") as fh:
            rows = [r for r in csv.DictReader(fh) if (r.get("Transcript") or "").strip()]
    except (OSError, csv.Error):
        return {"error": "The demo transcript is not there, so the bench has no passage to offer."}
    if len(rows) < 2:
        return {"error": "The demo transcript has no passage to offer."}
    asker = (rows[0].get("Name") or "").strip()
    pairs = [(rows[i - 1], rows[i]) for i in range(1, len(rows))
             if (rows[i].get("Name") or "").strip() != asker
             and (rows[i - 1].get("Name") or "").strip() == asker]
    if not pairs:
        return {"error": "The demo transcript has no passage to offer."}
    pick = next((p for p in pairs if p[1]["Transcript"].strip().startswith(SAMPLE_OPENS)), None)
    before, turn = pick or max(pairs, key=lambda p: len(p[1]["Transcript"]))
    who, them = asker, (turn.get("Name") or "").strip()
    prior, said = before["Transcript"].strip(), turn["Transcript"].strip()
    return {"interviewer": who, "name": them, "prior": prior, "turn": said,
            "time": (turn.get("Timestamp") or "").strip(),
            "text": f"{who}: {prior}\n\n{them}: {said}"}


SPEAKER = re.compile(r"^\s*([A-Z][\w'.-]*(?: [A-Z][\w'.-]*)?):\s*(.*)$")


def split_sample(text: str) -> dict:
    """The older one-box bench as the turn, the turn before it and the speaker's name.

    A page from before the bench sent the four fields of the real call still sends this.

    Each `Name:` line starts a speaker's turn. The last one is the turn to read and everything
    before it is the context. A box with no names in it is all turn.
    """
    blocks: list[list] = []
    for line in str(text or "").splitlines():
        found = SPEAKER.match(line)
        if found:
            blocks.append([found.group(1), [found.group(2)]])
        elif blocks:
            blocks[-1][1].append(line)
        else:
            blocks.append(["", [line]])
    said = [(who, " ".join(part.strip() for part in lines if part.strip())) for who, lines in blocks]
    said = [(who, words) for who, words in said if words]
    if not said:
        return {"prior": "", "turn": "", "name": ""}
    name, turn = said[-1]
    return {"prior": "\n".join(words for _, words in said[:-1]), "turn": turn, "name": name}


def parse_suggestions(text: str, limit: int = 3) -> dict:
    """Model text into tags and candidates. Anything unreadable comes back as one error line."""
    try:
        data = json.loads(ai_mod.strip_fences(text))
    except (ValueError, TypeError):
        return {"error": ai_mod.NOT_JSON}
    if not isinstance(data, dict):
        return {"error": ai_mod.NOT_JSON}
    tags = [str(t).strip() for t in data.get("tags") or [] if str(t).strip()]
    candidates = [str(c).strip() for c in data.get("candidates") or [] if str(c).strip()]
    if not tags and not candidates:
        return {"error": "The answer carried no tags and no candidates."}
    return {"tags": tags[:8], "candidates": candidates[:max(1, int(limit))]}


def suggest(turn: str, prior: str = "", timecode: str = "", name: str = "",
            guidance: list[str] | None = None, examples: list[str] | None = None,
            key: str | None = None, transport=None, timeout: float | None = None,
            template: str | None = None, model: str | None = None,
            provider: str = ai_mod.ANTHROPIC, local_url: str | None = None,
            research_question: str | None = None, quotes: list[str] | None = None,
            address: str | None = None, deployment: str | None = None) -> dict:
    """Tags and one to three candidates for one turn, or a dict carrying one error line.

    Two calls: the first drafts up to ten statements, the second checks them against the rules and
    keeps the strongest. A second call that fails leaves the first's drafts, cut to three, so a
    hiccup costs quality and never the suggestion. Both go to the same provider and model, and both
    carry the key quotes when any came. With Local the key is never asked for.
    """
    if not (turn or "").strip():
        return {"error": "There is nothing in this passage to read."}
    provider = provider if provider in ai_mod.PROVIDERS else ai_mod.ANTHROPIC
    refused = ai_mod.route_ready({"provider": provider, "key": key, "model": model, "address": address,
                                  "deployment": deployment})
    if refused:
        return refused
    system = system_prompt(guidance or [], examples or [], template, research_question)

    def call(drafts: list[str] | None, limit: int) -> dict:
        answer = ai_mod.complete(system, user_message(turn, prior, timecode, name, drafts, quotes), provider,
                          model, key, local_url, transport, timeout, None, address, deployment)
        if "error" in answer:
            return answer
        parsed = parse_suggestions(answer["text"], limit)
        if "error" in parsed and answer.get("truncated"):
            return {"error": ai_mod.TOO_LONG}
        return parsed

    first = call(None, DRAFTS)
    if "error" in first or not first["candidates"]:
        return first
    second = call(first["candidates"], 3)
    if "error" in second:
        return {"tags": first["tags"], "candidates": first["candidates"][:3]}
    return {"tags": second["tags"] or first["tags"], "candidates": second["candidates"]}

