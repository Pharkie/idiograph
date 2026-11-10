#!/usr/bin/env python3
"""The Themes screen's AI help, off until the switch in Settings is on.

Three calls, all through `ai_suggest.complete`, so they go out with the provider, the model and the
key a suggestion on the turn screen uses, and all carry the project's research question. Their
system prompts are their own, written here, because the prompt in Settings asks for statements in a
shape a grouping cannot use. The IPA guidance they carry is read from `pet_guidance.md` beside this
file on every call: section 1, what a theme is, section 3, the rules for a theme, and section 4, the
questions a reviewer asks. Editing that file changes what the AI is told.

A new AI proposal sends every card of a board that is not discarded, by its key, sheet, timecode
and words, with the labels that board already has and the note of each that has one, and asks for
a grouping into no more themes
than his limit, with the rules for a theme. The answer is read strictly and laid out on the canvas
as a board of round blobs, which the server adds through `themes.version_op` as a new one. The
board it was made from is never touched. What the answer leaves out stays in Not placed with its
reason, and nothing it answers goes to the bin. Made from all statements, it sends every statement of the
case with no labels and none discarded, and the prompt says nothing of his groups. A second call
then asks, for each theme and sub-theme by its title, the one key quote of the rows under it that
best carries the title, a second only when no single one does, and the answer is read strictly and
written as picks. A label that keeps his own picks is not asked about.

Title suggestion sends one theme as the workbook and the board hold it, its title and its note when
it has them, each statement in the order the canvas reads it with its timecode and every key quote
of its turn, the picked ones marked, its sub-themes the same way, and the other labels on the
canvas. It asks for three titles, each from a different angle, with what a theme is and what an
experiential statement is, under the rules for a title, its register, negative material and
recurrence. A page from before it sends the statements as bare text, which still builds a prompt.

The review sends the whole board, theme by theme with the statements, the picks, each theme's note
when it has one, the unplaced and the discarded, with the rules and the reviewer's questions, and
asks up to three questions of it, put plainly about the board and never in the first person. Ask
again sends every question earlier rounds asked, each with what he did with it, and asks for ones
not yet asked. A reply sends the board the same way with one question, its why, the exchange under
it so far and his words, and asks for a short answer in the same voice. Nothing on the board
changes: the page keeps the questions and the exchanges with the board.

A revise sends the board as it stands, each label by its id with its title, its note, its
statements each with its own key quote and its picks, its sub-themes under it, then the
statements not placed, with the rules for a theme, the thread of earlier requests on this board and
his request, and asks for operations on the board, never a whole board. Past the route's room the
quotes of the statements lowest on the canvas go first, then the thread's oldest lines, and the
answer's line says so, as a title's does. `revise_ops` reads the operations
strictly against a plain board, its labels, the keys on it and the quotes of their rows, applying
each in order to a copy: one that names a key, a label or a quote that is not there is refused and
the rest stand. The board, the parser and the applier are plain dicts with no PETs in their names,
so a board of another kind can pass through them.

The GETs screen has the same help one layer up, at the end of this file: a new AI board from every
case's PETs or a GETs board with the key quote of each row, three titles for a GET, the review with
its replies, and a revise through the same `revise_ops`, with sections 5 and 6 of the guidance file,
what a GET is and the questions a reviewer asks of a GETs board.

Nothing here reads a key, opens a workbook or writes a file. The transport is a parameter, the shape
`complete` takes, so the tests run with no key, no Ollama and no network.
"""
from __future__ import annotations

import json
import re
from datetime import datetime
from pathlib import Path

import ai_suggest as ai_mod
import boot
import formats
import i18n
import themes as th

# The words the person reads, the refusals and the lines an AI change writes, from the catalogue
# (apps/idiograph/static/i18n/en/themes_ai.json, i18nleft, 1 November 2026), each read in the run's language
# when said: inside this module through `_w`, from others as the module's names (`__getattr__`). The prompts
# stay English, the model's own language here.
SAID = {
    "OFF": lambda **v: i18n.t("themes_ai.off", v),
    "PLACED_NOTHING": lambda **v: i18n.t("themes_ai.placed_nothing", v),
    "NO_STATEMENTS": lambda **v: i18n.t("themes_ai.no_statements", v),
    "NO_TITLES": lambda **v: i18n.t("themes_ai.no_titles", v),
    "NOTHING_TO_NAME": lambda **v: i18n.t("themes_ai.nothing_to_name", v),
    "NO_SUCH_PET": lambda **v: i18n.t("themes_ai.no_such_pet", v),
    "TOO_MANY": lambda **v: i18n.t("themes_ai.too_many", v),
    "NO_QUESTIONS": lambda **v: i18n.t("themes_ai.no_questions", v),
    "NO_ANSWER": lambda **v: i18n.t("themes_ai.no_answer", v),
    "NO_REPLY": lambda **v: i18n.t("themes_ai.no_reply", v),
    "NO_SUCH_QUESTION": lambda **v: i18n.t("themes_ai.no_such_question", v),
    "NOTHING_TO_REVIEW": lambda **v: i18n.t("themes_ai.nothing_to_review", v),
    "NO_GUIDANCE": lambda **v: i18n.t("themes_ai.no_guidance", v),
    "FROM_ALL": lambda **v: i18n.t("themes_ai.from_all", v),
    "NO_REQUEST": lambda **v: i18n.t("themes_ai.no_request", v),
    "NO_CHANGES": lambda **v: i18n.t("themes_ai.no_changes", v),
    "NOTHING_CHANGED": lambda **v: i18n.t("themes_ai.nothing_changed", v),
    "UNKNOWN_STATEMENT": lambda **v: i18n.t("themes_ai.unknown_statement", v),
    "UNKNOWN_LABEL": lambda **v: i18n.t("themes_ai.unknown_label", v),
    "UNKNOWN_QUOTE": lambda **v: i18n.t("themes_ai.unknown_quote", v),
    "NOT_DONE": lambda **v: i18n.t("themes_ai.not_done", v),
    "INSIDE_ITSELF": lambda **v: i18n.t("themes_ai.inside_itself", v),
    "UNREADABLE": lambda **v: i18n.t("themes_ai.unreadable", v),
    "NO_PETS_TO_GROUP": lambda **v: i18n.t("themes_ai.no_pets_to_group", v),
    "PLACED_NO_PETS": lambda **v: i18n.t("themes_ai.placed_no_pets", v),
    "TOO_MANY_GETS": lambda **v: i18n.t("themes_ai.too_many_gets", v),
    "NO_SUCH_GET": lambda **v: i18n.t("themes_ai.no_such_get", v),
    "NOTHING_UNDER": lambda **v: i18n.t("themes_ai.nothing_under", v),
    "NOTHING_TO_REVIEW_GETS": lambda **v: i18n.t("themes_ai.nothing_to_review_gets", v),
    # the family's, read where it is said rather than frozen when this module was first imported
    "NOT_JSON": lambda **v: ai_mod.NOT_JSON,
    # the revision kept before a revise, "Before: " and his request, its head alone for the command line's cut
    "BEFORE": lambda **v: i18n.t("themes_ai.revision_before", {"request": ""}),
}


def _w(name: str, **vals) -> str:
    return SAID[name](**vals)


def __getattr__(name: str) -> str:
    """This module's words other modules and the checks name, `themes_ai.OFF`, read in the run's language."""
    if name in SAID:
        return SAID[name]()
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


UNTITLED = "Untitled"

# The guidance every prompt here carries, read afresh on every call: the numbered rules under
# `## 3.` and the numbered questions under `## 4.`. The names prompt takes the prose of `## 1.`,
# what a theme is, and rules 5, 6, 8 and 11: the title, its register, negative and unresolved
# material as valid, and recurrence as grounding.
GUIDANCE = boot.resource("pet_guidance.md")
WHAT_A_THEME = 1
RULES = 3
QUESTIONS = 4
TITLE_RULES = (5, 6, 8, 11)

# His limit on the themes a proposal makes, the stepper beside the hint: up to five by default,
# from two to nine. The prompt asks for between one fewer and the limit, and one more only with a
# reason, and an answer past that is refused.
CAP = 5
CAP_MIN = 2
CAP_MAX = 9
REASON_LIMIT = 300


def clean_cap(value, fallback: int = CAP) -> int:
    """A limit on the themes, a whole number from two to nine, whatever was sent."""
    try:
        number = int(float(value))
    except (TypeError, ValueError):
        number = fallback
    return max(CAP_MIN, min(CAP_MAX, number))

# A grouping answers with every key on the canvas once, which runs to thousands of tokens on a case
# of a hundred statements, so it gets far more room than a suggestion, and a model that thinks more
# again. It also takes longer, so it gets longer to answer.
GROUP_MAX_TOKENS = 12000
GROUP_THINKING_MAX_TOKENS = 32000
GROUP_TIMEOUT = 120
GROUP_THINKING_TIMEOUT = 300
GROUP_LOCAL_TIMEOUT = 600
NAMES_MAX_TOKENS = 800
NAMES_TIMEOUT = 30
NAMES_THINKING_TIMEOUT = 120
# The second call a new AI board makes, for the quotes that carry each PET: a short answer, an id
# and a key or two for each label, over a prompt that carries the board's key quotes. Two is an AI
# answer's limit alone, the picks call's and AI revise's: a pick by hand takes every quote he picks.
PICKS_MAX = 2
PICKS_MAX_TOKENS = 1500
PICKS_TIMEOUT = 60
PICKS_THINKING_TIMEOUT = 180
NO_PICKS = "No quotes picked."
# what a board made from every statement of the case is made from, in its note and its line
# A title's prompt grows with the key quotes under each statement. It keeps within the room a
# grouping's prompt has in a local model's context, the context less the answer the grouping leaves
# room for, at about four characters to a token. A theme past it loses the quotes of the statements
# lowest on the canvas first, and the answer says so in one line.
CHARS_PER_TOKEN = 4
PROMPT_CEILING = (ai_mod.LOCAL_CONTEXT - GROUP_MAX_TOKENS) * CHARS_PER_TOKEN

LABEL_LIMIT = 160
HINT_LIMIT = 200
NAMES = 3
# A review asks between one and three questions, and keeps the first three of an answer with more.
REVIEW_MIN = 1
REVIEW_MAX = 3
# A reply is two to five sentences, with the review's wait and room for a model that thinks.
REPLY_MAX_TOKENS = 800
REPLY_TEXT = th.THREAD_TEXT

# What a title carries on the page, whatever the guidance says: the canvas cleans these out anyway.
FORMAT = "No em dashes and no semicolons in a title."

INTRO = ("You help a researcher doing Interpretative Phenomenological Analysis (IPA, Smith, Flowers "
         "and Larkin) at the step after the experiential statements, where one participant's "
         "statements are clustered into personal experiential themes. He does that work himself. "
         "You offer a first try, which he keeps, changes or throws away.")

THEME = ("A personal experiential theme gathers statements that share an experiential meaning for "
         "this participant. Group by what the experience is like and what it comes to mean, never by "
         "topic, by the order of the interview or by the words the statements happen to share.")

# What an experiential statement is, for the titles, which are grounded in the statements and in
# the quotes kept beside them.
STATEMENT = ("An experiential statement is the researcher's own words for what a stretch of the "
             "transcript was like for the participant, or what they made of it, one idea each, a step "
             "above the transcript and grounded in it, with the participant's own phrasing kept in the "
             "key quotes beside it.")

REVIEW_INTRO = ("You help a researcher doing Interpretative Phenomenological Analysis (IPA, Smith, "
                "Flowers and Larkin) at the step where one participant's experiential statements are "
                "clustered into personal experiential themes. He has grouped them on a board himself, "
                "and asks you to review the grouping the way a careful peer reviewer or supervisor "
                "might: by asking questions of it. Every analytic judgement stays with him.")

GROUP_SHAPE = "\n".join([
    "Answer with strict JSON and nothing else, in this shape:",
    '{"groups": [{"label": "...", "members": ["<key>", "<key>"], '
    '"groups": [{"label": "...", "members": ["<key>"]}]}], '
    '"left_out": [{"key": "<key>", "reason": "..."}], "reason": "..."}',
    "Members are statement keys exactly as given. The \"groups\" inside a group holds its sub-themes,",
    "one level down, and is there only when the theme has distinct facets. \"left_out\" lists each",
    "statement left out of every theme, with why, and is empty when every statement is placed.",
    "\"reason\" is there only when there is one theme more than his limit, and says why. No key",
    "appears twice in the whole answer.",
])

# What a statement left out of every theme comes to: it stays in Not placed, beside the themes,
# with its reason under it, and the bin is his act alone (item 182).
LEFT_OUT = ("A statement you leave out of every theme stays beside them, in Not placed, with your reason "
            "under it, and he decides whether it goes. Nothing you answer puts a statement in the bin.")

NAMES_SHAPE = "\n".join([
    "Answer with strict JSON and nothing else, in this shape:",
    '{"names": ["...", "...", "..."]}',
])

# The voice of every question and every answer: plainly about the board, in the third person, with
# no first person in it, and the prompt's one example of a question put so.
REVIEW_EXAMPLE = ("Does the sub-theme 'Managing bodily overwhelm' sit at ease under a parent title about "
                  "joy, or is the uncomfortable side of her experience softened by its frame?")
VOICE = ("Write plainly about the board, in the third person. Never write in the first person, no I, "
         "me, my or we, and hold no opinion of your own.")

REVIEW_TASK = " ".join([
    "Ask at most three questions of this board, the most consequential first, and fewer when fewer",
    "matter.",
    "Check every theme before you choose, and never draw a pattern from a few of them.",
    "Each question rests on one of the rules, takes its lead from the reviewer's questions where one",
    "fits, and is grounded in something on the board: a theme, a sub-theme, a statement, a picked",
    "quote, a discarded statement or the statements left unplaced.",
    VOICE,
    "Ask, never rule: each is a question, never a verdict, such as",
    f"\"{REVIEW_EXAMPLE}\"",
    "The why under each question says plainly what on the board prompted it.",
    "Propose no new titles and no new groupings. He decides.",
    "In the question and the why, name a theme by its title and a statement by its own words, never",
    "by an id or a key, which belong in \"about\" alone.",
    "Plain words, no therapeutic jargon, no claim about causes, no em dashes and no semicolons.",
])

# A theme's note is the analyst's own reasoning for it. Each prompt that carries one says so in one
# line, and a prompt with no note in it carries no such line, so no prompt grows for a board without.
NOTES_GROUP = ("A label's note is his own reasoning for that theme, why it exists and what it holds, "
               "to weigh when you keep, merge or replace it.")
NOTE_NAMES = "His note on this theme, his own reasoning for it:"
NOTES_REVIEW = ("A theme may carry an analyst's note, his own reasoning for the theme, why it exists, "
                "what it holds and what it answers. Weigh it when you ask a question of that theme.")

REVIEW_SHAPE = "\n".join([
    "Answer with strict JSON and nothing else, in this shape:",
    '{"items": [{"about": "<group id or card key or null>", "question": "<one sentence, a question>", '
    '"rule": "<the rule number it rests on>", "why": "<one sentence grounding it in the board>"}]}',
    "\"about\" is the id of the theme or sub-theme, such as g2, or the key of the statement, exactly",
    "as the board gives them, and null when the question is about the board as a whole. \"rule\" is",
    "the number of the rule for a theme the question rests on, never the number of a reviewer's",
    "question. \"why\" says in one sentence what on the board prompted it.",
])

# Ask again: the questions earlier rounds asked, each with what he did with it, said in the system
# prompt only when there are some, so a first review's prompt is as it was.
ASKED_REVIEW = ("Earlier rounds have asked questions of this board, listed after it with what he did "
                "with each: ticked means he actioned it, crossed means he set it aside, and left open "
                "means he has not taken it up. Ask only questions not yet asked. Never ask again, in "
                "any words, a question he ticked or crossed.")
ASKED_STATES = {"considered": "ticked, actioned", "dismissed": "crossed, set aside", "open": "left open"}

# A reply on one question: his words back, a question of his own or his view, and a short answer.
REPLY_TASK = " ".join([
    "A review of this board asked him the question below, and he has written back to it, a question",
    "of his own or his view. Answer in two to five sentences, and answer what he asked.",
    "Take his view seriously: agree with it or question it from the statements on the board, and",
    "never decide for him.",
    VOICE,
    "Name a theme by its title and a statement by its own words, never by an id or a key.",
    "Plain words, no therapeutic jargon, no claim about causes, no em dashes and no semicolons.",
])
REPLY_SHAPE = "Answer with the words of the answer alone: no JSON, no heading and no list."


# ------------------------------------------------------------------ guidance

def guidance_items(section: int, path: Path | None = None) -> list[tuple[int, str]]:
    """The numbered items under one section of the guidance file, `## 3.` up to the next heading,
    each with the number the file gives it. Read afresh on every call, so an edit to the file
    reaches the next prompt with no restart. A file that is missing gives none."""
    try:
        text = Path(path or GUIDANCE).read_text(encoding="utf-8")
    except OSError:
        return []
    out: list[tuple[int, str]] = []
    inside = False
    for line in text.splitlines():
        if line.startswith("#"):
            inside = re.match(rf"^##\s+{int(section)}\.(?:\s|$)", line) is not None
            continue
        if not inside:
            continue
        item = re.match(r"^(\d+)\.\s+(.*\S)\s*$", line)
        if item:
            out.append((int(item.group(1)), item.group(2)))
        elif out and line[:1] in (" ", "\t") and line.strip():
            # a line carried on under its item
            out[-1] = (out[-1][0], f"{out[-1][1]} {line.strip()}")
    return out


def guidance_prose(section: int, path: Path | None = None) -> str:
    """The prose under one section of the guidance file, `## 1.` up to the next heading, its
    paragraphs as the file writes them, each on one line. Read afresh on every call, like the
    rules. A file that is missing, or has no such section, gives nothing."""
    try:
        text = Path(path or GUIDANCE).read_text(encoding="utf-8")
    except OSError:
        return ""
    paragraphs: list[list[str]] = []
    inside = False
    for line in text.splitlines():
        if line.startswith("#"):
            inside = re.match(rf"^##\s+{int(section)}\.(?:\s|$)", line) is not None
            continue
        if not inside:
            continue
        if line.strip():
            if not paragraphs or paragraphs[-1] is None:
                paragraphs.append([])
            paragraphs[-1].append(line.strip())
        elif paragraphs and paragraphs[-1] is not None:
            paragraphs.append(None)
    return "\n\n".join(" ".join(p) for p in paragraphs if p)


def numbered(items) -> str:
    return "\n".join(f"{n}. {text}" for n, text in items)


# ------------------------------------------------------------------- prompts

def question_block(question: str | None) -> str:
    """The project's research question as these prompts say it, or nothing when there is none."""
    asked = " ".join(str(question or "").split())
    if not asked:
        return ""
    if asked[-1] not in ".?!":
        asked += "."
    return (f"The study asks: {asked} Every theme answers that question for this participant: what "
            "matters to them, and in what way it matters.")


def _join(parts: list[str]) -> str:
    return re.sub(r"\n{3,}", "\n\n", "\n\n".join(p for p in parts if p is not None)).strip()


def limit_line(cap: int) -> str:
    """His limit as the prompt says it: between one fewer and the limit, one more only with a reason."""
    cap = clean_cap(cap)
    return (f"His limit is {cap} themes. Make between {cap - 1} and {cap} themes. Make {cap + 1} only "
            "when the statements cannot be held in fewer, and then say why in \"reason\". Never more.")


def rules_block(rules) -> str:
    return "The rules for a theme, from the IPA guidance he works by:\n" + numbered(rules)


def group_system(question: str | None, cap: int = CAP, rules=None) -> str:
    """The grouping's system prompt: the task with his limit, the rules for a theme from section 3
    of the guidance file, and the shape of the answer. His limit comes before rule 1."""
    rules = guidance_items(RULES) if rules is None else rules
    task = " ".join([
        THEME,
        "A theme may hold sub-themes, one level down. Each statement sits in one group at most.",
        limit_line(cap),
        "Where his limit and the rules differ on how many themes, his limit comes first.",
    ])
    asked = " ".join(str(question or "").split())
    # with no question set, rule 4 has nothing to measure a statement left out against
    discard = ("" if asked else "No research question is set, so leave a statement out only when it says "
               "nothing of the participant's experience.")
    place = ("Leave a statement out of every theme only where rule 4 would let it go, place every other "
             "statement, and say why each one left out goes in \"left_out\".")
    return _join([INTRO, question_block(question), task, rules_block(rules) if rules else None,
                  " ".join(p for p in (discard, place, LEFT_OUT) if p), FORMAT, GROUP_SHAPE])


def names_system(question: str | None, rules=None, theme: str | None = None) -> str:
    """The titles' system prompt, in this order: the introduction, the research question, what a
    theme is from section 1 of the guidance file, what an experiential statement is, the task, then
    rules 5, 6, 8 and 11 of section 3, the title, its register, negative and unresolved material as
    valid and recurrence as grounding, the format line and the shape. A file without section 1
    sends the one sentence on a theme the grouping carries in its place."""
    rules = guidance_items(RULES) if rules is None else rules
    theme = guidance_prose(WHAT_A_THEME) if theme is None else theme
    title = [(n, text) for n, text in rules if n in TITLE_RULES]
    task = " ".join([
        "Offer three titles for the theme he has gathered, each a different angle on what its",
        "statements share, each grounded in the statements and in the key quotes under them, and none",
        "repeating a label already on the canvas.",
    ])
    said = "Every title follows these rules from the IPA guidance he works by:\n" + numbered(title) if title else None
    return _join([INTRO, question_block(question), one_line(theme) and theme.strip() or THEME, STATEMENT, task,
                  said, FORMAT, NAMES_SHAPE])


def review_system(question: str | None, rules=None, questions=None, notes: bool = False,
                  asked: bool = False) -> str:
    """The review's system prompt: the rules for a theme from section 3 of the guidance file, the
    questions a reviewer asks from section 4, the task, and the shape of the answer. With `notes`,
    when a theme on the board carries one, it says what an analyst's note is, and with `asked`,
    when earlier rounds asked questions of the board, it asks for ones not yet asked."""
    rules = guidance_items(RULES) if rules is None else rules
    questions = guidance_items(QUESTIONS) if questions is None else questions
    return _join([REVIEW_INTRO, question_block(question), rules_block(rules),
                  "The questions a reviewer asks of a grouping:\n" + numbered(questions),
                  REVIEW_TASK, NOTES_REVIEW if notes else None, ASKED_REVIEW if asked else None, REVIEW_SHAPE])


def reply_system(question: str | None, rules=None, notes: bool = False) -> str:
    """A reply's system prompt: the review's introduction, the research question, the rules for a
    theme, the task of answering him in two to five sentences in the review's voice, what an
    analyst's note is when the board carries one, and the shape, plain words."""
    rules = guidance_items(RULES) if rules is None else rules
    return _join([REVIEW_INTRO, question_block(question), rules_block(rules), REPLY_TASK,
                  NOTES_REVIEW if notes else None, REPLY_SHAPE])


def statement_line(s: dict) -> str:
    where = ", ".join(p for p in (s.get("sheet"), s.get("time")) if p)
    return f"- {s['key']} ({where}) {' '.join(str(s.get('text') or '').split())}"


def one_line(text) -> str:
    return " ".join(str(text or "").split())


def label_lines(labels: list[dict], depth: int = 0) -> list[str]:
    """His labels as the grouping sends them, nested as they sit, each with the keys under it and
    its note on the line after it when it has one."""
    out = []
    for item in labels:
        members = ", ".join(item.get("members") or [])
        out.append(f"{'  ' * depth}- {item['label']}" + (f": {members}" if members else ""))
        if one_line(item.get("note")):
            out.append(f"{'  ' * depth}  Note: {one_line(item.get('note'))}")
        out.extend(label_lines(item.get("groups") or [], depth + 1))
    return out


def any_note(labels: list[dict]) -> bool:
    """Whether a label, at any depth, carries a note. Labels are `labels_of`'s or the outline's
    themes, which hold their sub-themes under `groups` and `themes`."""
    return any(one_line(item.get("note")) or any_note(item.get("groups") or item.get("themes") or [])
               for item in labels or [])


def clean_hint(hint) -> str:
    return " ".join(str(hint or "").split())[:HINT_LIMIT]


def group_user(statements: list[dict], labels: list[dict] | None, hint: str = "") -> str:
    """The grouping's user prompt: the statements, his labels with the keys under each, the hint and
    the ask. Labels of None, a board made from all statements, says nothing of his groups."""
    parts = ["The statements of this case, one per line, each with its key, its sheet and its timecode:\n"
             + "\n".join(statement_line(s) for s in statements)]
    if labels:
        parts.append("His labels on the canvas now, each with the keys under it. They are his own: keep "
                     "any that hold, merge them or replace them.\n"
                     + (NOTES_GROUP + "\n" if any_note(labels) else "") + "\n".join(label_lines(labels)))
    elif labels is not None:
        parts.append("There are no labels on the canvas yet.")
    hint = clean_hint(hint)
    if hint:
        # a hint such as "fewer groups" is read against the labels above, and it outranks the
        # general guidance in the system prompt, which the first tries showed it needs saying
        parts.append(f"His hint for this arrangement, which comes before the general guidance: {hint}")
    parts.append("Group the statements.")
    return "\n\n".join(parts)


def names_user(statements: list[str], label: str = "", others: list[str] | None = None, note: str = "") -> str:
    """The titles' user prompt as a page from before the theme went whole sends it: the statements
    as bare text, the title, the note and the other labels."""
    parts = ["The statements he has gathered:\n" + ai_mod.bullets(statements)]
    label = " ".join(str(label or "").split())
    parts.append(f"Its title now: {label}" if label and label != UNTITLED else "It has no title yet.")
    if one_line(note):
        parts.append(f"{NOTE_NAMES} {one_line(note)}")
    others = [o for o in (others or []) if str(o).strip()]
    if others:
        parts.append("The other labels on the canvas, so the titles sit beside them:\n" + ai_mod.bullets(others))
    parts.append("Three titles, each from a different angle.")
    return "\n\n".join(parts)


def titled(label) -> str:
    label = one_line(label)
    return label if label and label != UNTITLED else "no title yet"


def pet_lines(theme: dict, many: bool, bare=frozenset(), depth: int = 0, inside: str = "") -> list[str]:
    """One theme as the titles prompt sets it out, as `theme_lines` sets one out for the review: its
    title or "no title yet", his note on it, then each statement in the order the canvas reads them,
    with its sheet when the case has more than one and its timecode, and under it its own key
    quote in inverted commas with its timecode, a picked one marked "(picked)". Its sub-themes
    follow, indented, the same way. A statement in `bare` goes without its quotes, and a turn with
    none says nothing under its statement."""
    pad = "  " * depth
    head = f"{pad}{'Sub-theme' if depth or inside else 'Theme'}: {titled(theme.get('label'))}"
    if inside and not depth:
        head += (", inside a theme with no title yet" if titled(inside) == "no title yet"
                 else f", inside the theme {titled(inside)}")
    out = [head]
    if one_line(theme.get("note")):
        out.append(f"{pad}  {NOTE_NAMES} {one_line(theme.get('note'))}")
    for s in theme.get("statements") or []:
        where = [p for p in ((s.get("sheet") if many else ""), s.get("time")) if p]
        if s.get("missing"):
            where.append("no longer in the workbook")
        out.append(f"{pad}  - " + (f"({', '.join(where)}) " if where else "") + _said(s))
        if s.get("key") in bare:
            continue
        for q in s.get("quotes") or []:
            out.append(f"{pad}    {th.quoted(one_line(q.get('text')))}" + (f" ({q['time']})" if q.get("time") else "")
                       + (" (picked)" if q.get("picked") else ""))
    for sub in theme.get("themes") or []:
        out += pet_lines(sub, many, bare, depth + 1)
    return out


def pet_user(target: dict, bare=frozenset()) -> str:
    """The titles' user prompt for one theme, built on the server from the workbook and the board:
    the theme as `pet_lines` sets it out, a line when the quotes of some statements are left out for
    room, the other labels on the canvas, and the closing line."""
    many = bool(target.get("many"))
    intro = ("The theme he asks titles for, as the canvas reads it, top to bottom and left to right, "
             "higher meaning a better example. Each statement has its "
             + ("sheet and its timecode" if many else "timecode")
             + ", and under it its own key quote, in inverted commas with its timecode, "
               "one he picked to carry the theme marked (picked).")
    parts = [intro + "\n" + "\n".join(pet_lines(target, many, bare, inside=target.get("inside") or ""))]
    if bare:
        parts.append(quotes_left(len(bare)))
    others = [o for o in (target.get("others") or []) if one_line(o)]
    if others:
        parts.append("The other labels on the canvas, so the titles sit beside them:\n" + ai_mod.bullets(others))
    parts.append("Three titles, each from a different angle.")
    return "\n\n".join(parts)


def names_target(read: dict, version: dict, gid: str) -> dict | None:
    """The theme a title is asked for, from the workbook as `themes.read_cards` reads it and the
    board: `themes.outline`'s theme with that id, at any depth, each statement carrying every key
    quote of its turn with its timecode, the ones picked by the theme or by a sub-theme inside it
    marked, and the canvas height of each statement for the cut. `inside` is the title of the theme
    a sub-theme sits in, `others` every other label on the board, Untitled left out, once each, and
    `many` whether the case has more than one sheet. None when the board holds no such label."""
    board = th.outline(read, version)
    found, parent_of, labels = None, {}, []

    def walk(theme: dict, parent: dict | None) -> None:
        nonlocal found
        if theme["id"] == gid:
            found = theme
        parent_of[theme["id"]] = parent
        labels.append(theme)
        for sub in theme["themes"]:
            walk(sub, theme)

    for theme in board["themes"]:
        walk(theme, None)
    if found is None:
        return None
    own: set[str] = set()
    picked: set[str] = set()

    def gather(theme: dict) -> None:
        own.add(theme["id"])
        picked.update(p["key"] for p in theme["picks"])
        for sub in theme["themes"]:
            gather(sub)

    gather(found)
    spots = th.follow(version, read["cards"], read["quotes"])["cards"]
    quotes = read.get("quotes") or {}

    def with_quotes(theme: dict) -> dict:
        statements = []
        for s in theme["statements"]:
            sheet, row, _ = th.split_card_key(s["key"])
            held = quotes.get(th.row_key(sheet, row)) if row is not None and not s.get("missing") else None
            spot = spots.get(s["key"]) or {}
            # a statement goes with its own key quote, the one at its place on its turn
            statements.append(dict(s, x=spot.get("x", 0), y=spot.get("y", 0), quotes=[
                {"key": q["key"], "text": q["text"], "time": q.get("time") or held.get("time") or "", "picked": q["key"] in picked}
                for q in (held or {}).get("quotes") or [] if q["key"] == s["key"]]))
        return dict(theme, statements=statements, themes=[with_quotes(sub) for sub in theme["themes"]])

    others: list[str] = []
    for theme in labels:
        label = one_line(theme["label"])
        if theme["id"] not in own and label and label != UNTITLED and label not in others:
            others.append(label)
    parent = parent_of.get(gid)
    return dict(with_quotes(found), inside=(parent["label"] or UNTITLED) if parent else "", others=others,
                many=len(read.get("sheets") or []) > 1)


def statements_in(target: dict) -> list[dict]:
    """Every statement of a target at any depth, its own first and then each sub-theme's."""
    out = list(target.get("statements") or [])
    for sub in target.get("themes") or []:
        out += statements_in(sub)
    return out


def quotes_left(n: int) -> str:
    """What a prompt says of the quotes it leaves out for room, a title's and a revise's."""
    return (f"The key quotes of the {'statement' if n == 1 else f'{n} statements'} lowest on the canvas "
            "are left out here for room, which says nothing about them.")


def cut_quotes(system: str, build, statements: list[dict], ceiling: int) -> tuple[str, frozenset]:
    """A user prompt inside the ceiling where the quotes allow, `build(bare)` making it with the
    quotes of the statements in `bare` left out: past it, the quotes of the statements lowest on the
    canvas go first, by their `y` and then their `x`, one statement at a time, until the two prompts
    fit or none is left with quotes. Answers with the prompt and the keys whose quotes went."""
    bare: set[str] = set()
    user = build(frozenset())
    quoted_ones = [s for s in statements if s.get("quotes")]
    for s in sorted(quoted_ones, key=lambda s: (s.get("y", 0), s.get("x", 0)), reverse=True):
        if len(system) + len(user) <= ceiling:
            break
        bare.add(s["key"])
        user = build(frozenset(bare))
    return user, frozenset(bare)


def cut_for_room(system: str, target: dict, ceiling: int | None = None) -> tuple[str, frozenset]:
    """The user prompt for a title's target, inside the ceiling, `PROMPT_CEILING` characters for the
    two prompts unless another is given, where the quotes allow, through `cut_quotes`. Answers with
    the prompt and the keys whose quotes went."""
    return cut_quotes(system, lambda bare: pet_user(target, bare), statements_in(target),
                      PROMPT_CEILING if ceiling is None else ceiling)


def cut_line(n: int) -> str:
    """What the answer says when quotes went for room."""
    return i18n.t("themes_ai.room.quotes", n=n)


def thread_line(n: int) -> str:
    """What a revise's answer says when the oldest lines of its thread went for room."""
    return i18n.t("themes_ai.room.thread", n=n, count=_count_said(n))


def room_said(result: dict, bare: int, line, dropped: int = 0) -> dict:
    """An answer from a prompt cut for room, its `said` ending with what went, `line(bare)` for the
    quotes or the words of `bare` statements and `thread_line(dropped)` for the oldest lines of the
    thread, with `trimmed` and `dropped` counting them. The answer's own words are cut at a word
    where the whole would pass the length one line of a thread keeps, so the end is never lost. An
    error, or an answer from a prompt sent whole, is as it was."""
    if "error" in result or not (bare or dropped):
        return result
    tail = " ".join(p for p in (line(bare) if bare else "", thread_line(dropped) if dropped else "") if p)
    said = one_line(result.get("said"))
    room = th.THREAD_TEXT - len(tail) - 1
    if len(said) > room:
        said = said[:room].rsplit(" ", 1)[0]
    out = dict(result, said=" ".join(p for p in (said, tail) if p))
    if bare:
        out["trimmed"] = bare
    if dropped:
        out["dropped"] = dropped
    return out


def _where(item: dict) -> str:
    where = ", ".join(p for p in (item.get("sheet"), item.get("time")) if p)
    return f"{where}, no longer in the workbook" if item.get("missing") else where


def _said(item: dict) -> str:
    return " ".join(str(item.get("text") or "").split())


def theme_lines(theme: dict, depth: int = 0) -> list[str]:
    """One theme of the board as the review sends it: its id, title and count, his note on it when
    it has one, its statements in the order the canvas reads them, each with its key, sheet and
    timecode, the quotes picked to carry it, then its sub-themes indented under it."""
    pad = "  " * depth
    out = [f"{pad}{'Sub-theme' if depth else 'Theme'} {theme['id']}: {theme['label']} ({theme['count']})"]
    if one_line(theme.get("note")):
        out.append(f"{pad}  Analyst's note: {one_line(theme.get('note'))}")
    out += [f"{pad}  - {s['key']} ({_where(s)}) {_said(s)}" for s in theme["statements"]]
    if theme["picks"]:
        out.append(f"{pad}  Quotes picked to carry it:")
        out += [f"{pad}  - {th.quoted(_said(q))} ({_where(q)})" for q in theme["picks"]]
    else:
        out.append(f"{pad}  No quotes picked yet.")
    for sub in theme["themes"]:
        out += theme_lines(sub, depth + 1)
    return out


def review_user(board: dict, asked=None, parts=None) -> str:
    """The board for the review, from `themes.outline`: theme by theme in canvas order, then the
    statements left unplaced and those discarded, with the reason a proposal gave. With `asked`,
    from `asked_of`, the questions earlier rounds asked follow, each with what he did with it.
    `parts` is the board set out another way, a GETs board's (see `gets_board_parts`)."""
    parts = list(parts) if parts is not None else board_parts(board)
    if asked:
        parts.append("Questions earlier rounds asked of this board, with what he did with each:\n"
                     + "\n".join(f"- {th.quoted(one_line(a['question']))} ({ASKED_STATES.get(a.get('state'), ASKED_STATES['open'])})"
                                 for a in asked))
    parts.append("Review this board.")
    return "\n\n".join(parts)


def asked_of(review) -> list[dict]:
    """Every question the rounds of a stored review asked, oldest first, each with his state on it,
    open, considered or dismissed, for Ask again."""
    return [{"question": i["question"], "state": i.get("state") if i.get("state") in ASKED_STATES else "open"}
            for i in th.review_items(review) if one_line(i.get("question"))]


def reply_user(board: dict, item: dict, words: str, parts=None, keys=None) -> str:
    """A reply's user prompt: the board as the review sends it, then the question, why it was
    asked, the rule it rests on and what it is about, the exchange under it so far, and his words.
    `parts` and `keys` are a GETs board's, set out its own way (see `gets_board_parts`)."""
    parts = list(parts) if parts is not None else board_parts(board)
    said = [f"The question the review asked: {one_line(item.get('question'))}"]
    if one_line(item.get("why")):
        said.append(f"Why it was asked: {one_line(item.get('why'))}")
    if one_line(item.get("rule")):
        said.append(f"It rests on rule {one_line(item.get('rule'))}.")
    about = item.get("about")
    if not about:
        said.append("It is about the board as a whole.")
    elif about in (keys if keys is not None else board_keys(board)):
        said.append(f"It is about {about} on the board.")
    parts.append("\n".join(said))
    thread = th.thread_of(item.get("thread"))
    if thread:
        parts.append("The exchange on it so far:\n" + "\n".join(
            f"{'He wrote' if line['by'] == 'analyst' else 'The answer'}: {one_line(line['text'])}" for line in thread))
    parts.append(f"He writes now: {one_line(words)}")
    parts.append("Answer him.")
    return "\n\n".join(parts)


def board_parts(board: dict) -> list[str]:
    """The board as the review and a reply send it, in three parts: theme by theme, the statements
    left unplaced, and those discarded with the reason a proposal gave."""
    parts = ["The board, theme by theme in the order the canvas reads them, top to bottom and left to "
             "right. Inside a theme, higher means a better example, so its statements come in that "
             "order. Each statement has its key, its sheet and its timecode.\n"
             + "\n".join(line for t in board["themes"] for line in theme_lines(t))]
    left = board.get("unplaced") or []
    parts.append("Statements left unplaced:\n" + "\n".join(f"- {s['key']} ({_where(s)}) {_said(s)}"
                                                           + (f". Left out with the reason: {one_line(s['reason'])}" if s.get("reason") else "")
                                                           for s in left)
                 if left else "No statements are left unplaced.")
    thrown = board.get("discarded") or []
    parts.append("Statements discarded, with the reason given where there is one:\n"
                 + "\n".join(f"- {s['key']} ({_where(s)}) {_said(s)}"
                             + (f". The reason given: {' '.join(s['reason'].split())}" if s.get("reason") else "") for s in thrown)
                 if thrown else "No statements are discarded.")
    return parts


def board_keys(board: dict) -> set[str]:
    """Everything on a board a question can be about: every theme's id at any depth and every
    statement's key, placed, unplaced or discarded."""
    out: set[str] = set()

    def walk(theme: dict) -> None:
        out.add(theme["id"])
        out.update(s["key"] for s in theme["statements"])
        for sub in theme["themes"]:
            walk(sub)

    for theme in board.get("themes") or []:
        walk(theme)
    out.update(s["key"] for s in (board.get("unplaced") or []) + (board.get("discarded") or []))
    return out


# ------------------------------------------------------------- what is sent

def statements_of(merged: dict) -> list[dict]:
    """Every card of a merged board that is on the canvas: not discarded and still in the
    workbook, in transcript order, with its key, sheet, timecode and words."""
    gone = set(merged.get("discarded") or [])
    return [{"key": c["key"], "sheet": c.get("sheet") or "", "time": c.get("time") or "", "text": c["text"]}
            for c in merged.get("cards") or [] if c["key"] not in gone and not c.get("missing")]


def labels_of(merged: dict) -> list[dict]:
    """The labels a board holds, nested the way they sit, each with the keys of its own cards on
    the canvas and its `note` when it has one. A label over labels carries its labels as `groups`."""
    on = {s["key"] for s in statements_of(merged)}
    groups = merged.get("groups") or []
    by_id = {g["id"]: g for g in groups}
    held = {m for g in groups for m in g["members"]}

    def one(gid: str, seen: set) -> dict:
        g = by_id[gid]
        seen = seen | {gid}
        out = {"label": g["label"], "members": [m for m in g["members"] if m in on],
               "groups": [one(m, seen) for m in g["members"] if m in by_id and m not in seen]}
        if one_line(g.get("note")):
            out["note"] = g["note"]
        return out

    return [one(g["id"], set()) for g in groups if g["id"] not in held]


# ------------------------------------------------------------------ parsing

QUOTES = "\"'“”‘’"


def clean_label(text) -> str:
    """A label as the canvas keeps it: one line, no em dash, no semicolon, no inverted commas round
    the whole of it, and not past the length a label can carry."""
    words = " ".join(str(text or "").split())
    if len(words) >= 2 and words[0] in QUOTES and words[-1] in QUOTES:
        words = words[1:-1].strip()
    words = re.sub(r"\s*\u2014\s*", ", ", words).replace(";", ",")
    return words[:LABEL_LIMIT].strip()


def _load(text: str):
    try:
        return json.loads(ai_mod.strip_fences(text))
    except (ValueError, TypeError):
        pass
    # a bare list, which strip_fences cuts to its first object
    raw = str(text or "").strip()
    if raw.startswith("```"):
        raw = ai_mod.FENCE.sub("", raw).strip()
    try:
        return json.loads(raw)
    except (ValueError, TypeError):
        return None


def _children(group: dict) -> list:
    for name in ("groups", "subgroups", "sub_groups", "subthemes", "sub_themes"):
        if isinstance(group.get(name), list):
            return group[name]
    return []


def _flat(group: dict) -> list:
    """A group's members and, below it, the members of every group nested inside it, in order."""
    out = list(group.get("members") or []) if isinstance(group.get("members"), list) else []
    for child in _children(group):
        if isinstance(child, dict):
            out.extend(_flat(child))
    return out


def clean_reason(text) -> str:
    """A reason as a note can quote it: one line, no em dash, no semicolon, not past its length."""
    words = " ".join(str(text or "").split())
    words = re.sub(r"\s*\u2014\s*", ", ", words).replace(";", ",")
    return words[:REASON_LIMIT].strip()


def parse_grouping(text: str, keys, truncated: bool = False, cap: int | None = None) -> dict:
    """A grouping read strictly against the keys that were sent.

    Fences and chatter round the JSON are stripped. A key the case does not have is left out, and so
    is a key already placed: it keeps the first group that named it. A blank label is Untitled. A
    group nested one level down is a sub-theme, and anything nested deeper is folded into the
    sub-theme above it. A sub-theme with no members goes, and so does a theme with neither members
    nor sub-themes. `left_out` keeps each statement the answer leaves out of every theme with its
    reason, once each, a key already placed or not the case's left out of it, and an answer that
    says `discarded` reads the same, since nothing an AI answers goes to the bin. `left` counts
    every statement not placed, those left out among them. `reason` says why there is one theme past
    the limit. With `cap`, an answer of more themes than one past it is refused. An answer that
    places nothing is one error line, as is one that is not JSON, and one cut off at its length
    limit says so.
    """
    keys = list(keys)
    known = set(keys)
    data = _load(text)
    reason, thrown_raw = "", []
    if isinstance(data, dict):
        reason = clean_reason(data.get("reason")) if isinstance(data.get("reason"), str) else ""
        thrown_raw = [x for k in ("left_out", "not_placed", "discarded") if isinstance(data.get(k), list) for x in data[k]]
        data = data.get("groups") if isinstance(data.get("groups"), list) else data.get("themes")
    if not isinstance(data, list):
        return {"error": ai_mod.TOO_LONG if truncated else ai_mod.NOT_JSON}
    seen: set[str] = set()
    unknown: list[str] = []
    repeated = 0

    def take(members) -> list[str]:
        nonlocal repeated
        out = []
        for m in members:
            key = str(m).strip()
            if key not in known:
                if key not in unknown:
                    unknown.append(key)
            elif key in seen:
                repeated += 1
            else:
                seen.add(key)
                out.append(key)
        return out

    groups = []
    for g in data:
        if not isinstance(g, dict):
            continue
        label = clean_label(g.get("label") or g.get("name") or g.get("title")) or UNTITLED
        members = take(g.get("members") if isinstance(g.get("members"), list) else [])
        subs = []
        for s in _children(g):
            if not isinstance(s, dict):
                continue
            inner = take(_flat(s))
            if inner:
                subs.append({"label": clean_label(s.get("label") or s.get("name") or s.get("title")) or UNTITLED,
                             "members": inner})
        if members or subs:
            groups.append({"label": label, "members": members, "groups": subs})
    if not seen:
        return {"error": ai_mod.TOO_LONG if truncated else _w("PLACED_NOTHING")}
    if cap is not None and len(groups) > clean_cap(cap) + 1:
        return {"error": _w("TOO_MANY", n=len(groups), cap=clean_cap(cap))}
    placed = len(seen)
    left_out, out_keys = [], set()
    for item in thrown_raw:
        key, why = (item.get("key"), item.get("reason")) if isinstance(item, dict) else (item, "")
        key = str(key).strip() if key is not None else ""
        if key not in known:
            if key and key not in unknown:
                unknown.append(key)
        elif key in seen or key in out_keys:
            repeated += 1
        else:
            out_keys.add(key)
            left_out.append({"key": key, "reason": clean_reason(why)})
    return {"groups": groups, "placed": placed, "left": len(known - seen), "left_out": left_out,
            "reason": reason, "unknown": len(unknown), "repeated": repeated}


def parse_names(text: str, truncated: bool = False) -> dict:
    """Up to three titles, tidied and each once. None is one error line."""
    data = _load(text)
    if isinstance(data, dict):
        data = next((data[k] for k in ("names", "titles", "labels") if isinstance(data.get(k), list)), None)
    if not isinstance(data, list):
        return {"error": ai_mod.TOO_LONG if truncated else ai_mod.NOT_JSON}
    names, seen = [], set()
    for item in data:
        name = clean_label(item.get("name") or item.get("title") if isinstance(item, dict) else item)
        if name and name.lower() not in seen:
            seen.add(name.lower())
            names.append(name)
    if not names:
        return {"error": _w("NO_TITLES")}
    return {"names": names[:NAMES]}


def clean_sentence(text) -> str:
    """A question or its why as the panel shows it: one line, no em dash, no semicolon, not past
    the length a sentence runs to."""
    words = " ".join(str(text or "").split())
    words = re.sub(r"\s*\u2014\s*", ", ", words).replace(";", ",")
    return words[:th.REVIEW_TEXT].strip()


def parse_review(text: str, known, truncated: bool = False, rules=None, asked=()) -> dict:
    """A review read strictly against what is on the board.

    Fences and chatter round the JSON are stripped. Each item keeps its question, what it is
    about, the number of the rule it rests on and why, each open. A question that is empty or
    asked twice goes, and so does one an earlier round asked, from `asked`, the questions as they
    were kept. An `about` that names nothing on the board, a theme's id or a statement's key, is
    None, the whole board. Past three the first three stay. An answer with no question is one
    line, as is one that is not JSON, and one cut off at its length limit says so. With `rules`,
    the numbers of the rules for a theme, a rule that is not one of them is left blank."""
    known = {str(k) for k in known}
    numbers = {str(n) for n in rules} if rules is not None else None
    before = {clean_sentence(q).lower() for q in asked or ()}
    data = _load(text)
    if isinstance(data, dict):
        data = next((data[k] for k in ("items", "observations", "questions") if isinstance(data.get(k), list)), None)
    if not isinstance(data, list):
        return {"error": ai_mod.TOO_LONG if truncated else ai_mod.NOT_JSON}
    items, seen = [], set()
    for item in data:
        if not isinstance(item, dict):
            continue
        question = clean_sentence(item.get("question"))
        if not question or question.lower() in seen or question.lower() in before:
            continue
        seen.add(question.lower())
        about = " ".join(str(item.get("about") or "").split())
        if about not in known:
            # "Theme g2" or "statement Initial:12:0" names what it is about by its last word
            last = about.split(" ")[-1].strip(".,:") if about else ""
            about = last if last in known else ""
        rule = re.search(r"\d+", str(item.get("rule") or ""))
        rule = rule.group(0) if rule else ""
        if numbers is not None and rule not in numbers:
            rule = ""
        items.append({"about": about or None, "question": question, "rule": rule,
                      "why": clean_sentence(item.get("why")), "state": "open"})
    if not items:
        return {"error": ai_mod.TOO_LONG if truncated else _w("NO_QUESTIONS")}
    return {"items": items[:REVIEW_MAX]}


def parse_reply(text: str, truncated: bool = False) -> dict:
    """A reply's answer read strictly: fences go, an answer sent as JSON gives its words, the words
    run as one paragraph with no em dash and no semicolon, cut at a word before the length a line of
    the exchange keeps. An empty answer is one line, and so is one cut off at its length limit."""
    if truncated:
        return {"error": ai_mod.TOO_LONG}
    raw = str(text or "").strip()
    if raw.startswith("```"):
        raw = ai_mod.FENCE.sub("", raw).strip()
    if raw.startswith("{"):
        data = _load(raw)
        if isinstance(data, dict):
            raw = next((str(data[k]) for k in ("answer", "reply", "text") if isinstance(data.get(k), str)), "")
    words = " ".join(raw.split())
    words = re.sub(r"\s*\u2014\s*", ", ", words).replace(";", ",")
    if len(words) > REPLY_TEXT:
        words = words[:REPLY_TEXT].rsplit(" ", 1)[0]
    words = words.strip()
    if not words:
        return {"error": _w("NO_ANSWER")}
    return {"text": words}


# ------------------------------------------------------------------- layout

# The canvas's own measures come from `themes`, the ones the first pile is laid with, so a
# proposal and a pile agree on how tall a card is and how wide a label runs, and every space here
# is the one margin a card always keeps: between two cards, and between a theme's own cards and a
# sub-theme's frame. Two themes' frames stand two margins apart, and the cards left out four
# margins to the side, so the themes still read as apart at the zoom that fits them all.
CARD_W = th.CARD_W
INNER_GAP = th.MARGIN        # between two cards inside a theme
PART_GAP = th.MARGIN         # between the parts of a theme: its own cards and each sub-theme's frame
THEME_GAP = 2 * th.MARGIN    # between two themes' frames on the plane
PILE_SIDE = 4 * th.MARGIN    # between the themes and the pile of cards left out
# the reason under a card left out of every theme, in the small type, two lines at most, which the
# pile it lies in leaves room for
WHY_H = 36


def _blob(label: str, keys: list[str], subs: list[dict], texts: dict, size=None, depth: int = 0,
          description: str = "") -> dict:
    """One theme as a round blob, its frame's top-left corner at the origin: its own cards packed
    in rows that fill a circle, each sub-theme a blob of its own inside it, and each group a blob
    inside its sub-theme, the label at the top, left edge on the left edge of what it holds, as the
    page sets it. The labels come top first and then in the order they nest, a sub-theme before its
    groups. `size` gives a card's height from its key and words, a PETs card's by default, and
    `depth` is the label's own, 0 for a PET, which its count names its labels by."""
    size = size or _height
    parts = []
    if keys:
        spots = th.pack_round([(CARD_W, size(k, texts[k])) for k in keys], INNER_GAP)
        boxes = [(x, y, CARD_W, size(k, texts[k])) for k, (x, y) in zip(keys, spots)]
        box = th.union(boxes)
        parts.append({"w": box[2], "h": box[3], "cards": {k: (b[0] - box[0], b[1] - box[1]) for k, b in zip(keys, boxes)},
                      "labels": []})
    for s in subs:
        parts.append(_blob(s["label"], s["members"], s.get("groups") or [], texts, size, depth + 1,
                           s.get("description") or ""))
    spots = [(0, 0)] if len(parts) == 1 else th.pack_round([(p["w"], p["h"]) for p in parts], PART_GAP)
    body = th.union((x, y, p["w"], p["h"]) for (x, y), p in zip(spots, parts))
    w, h = th.label_size(label, bool(subs), 0, description, body[2])
    lx, ly = body[0], body[1] - th.LABEL_GAP - h
    whole = th.union([(lx, ly, w, h), body])
    ox, oy = whole[0] - th.FRAME_X, whole[1] - th.FRAME_Y
    cards, labels = {}, [{"label": label, "x": lx - ox, "y": ly - oy, "sub": False}]
    for (x, y), p in zip(spots, parts):
        for k, (cx, cy) in p["cards"].items():
            cards[k] = (x + cx - ox, y + cy - oy)
        for item in p["labels"]:
            labels.append(dict(item, x=x + item["x"] - ox, y=y + item["y"] - oy, sub=True))
    return {"w": whole[2] + 2 * th.FRAME_X, "h": whole[3] + 2 * th.FRAME_Y, "cards": cards, "labels": labels}


def _height(_key, text) -> int:
    return th.card_height(text)


def lay_out(groups: list[dict], cards: list[dict], discarded: list[str], size=None, why=frozenset()) -> dict:
    """A proposed grouping as a board of the canvas.

    Each theme is a round blob: its label at the top and its cards packed under it in rows that fill
    a circle, each sub-theme a blob of its own inside its theme's frame, and each group a sub-theme
    carries under `groups` a blob inside the sub-theme's. The themes are set out on
    the plane in the order the answer gives, row by row inside a circle, with clear gaps between
    their frames. The cards left out lie in a pile of their own to the right, in transcript order,
    the missing ones last, each one in `why`, left out with a reason, with room for the reason
    under it. A discarded card stays discarded, where it was: nothing an answer says puts a card in
    the bin. The labels are numbered g1 on, the themes first, then each sub-theme followed by its
    groups, and nothing overlaps. `size` gives a
    card's height from its key and words, a PETs card's by default, so a GETs board, whose cards
    carry their kind over their words, lays out the same way.
    """
    size = size or _height
    texts = {c["key"]: c["text"] for c in cards}
    order = [c["key"] for c in cards if not c.get("missing")] + [c["key"] for c in cards if c.get("missing")]
    gone = [k for k in discarded if k in texts]
    spot = {c["key"]: (int(c.get("x") or 0), int(c.get("y") or 0)) for c in cards}
    taken: set[str] = set(gone)

    def fresh(keys) -> list[str]:
        out = []
        for k in keys:
            if k in texts and k not in taken:
                taken.add(k)
                out.append(k)
        return out

    def kept(s: dict) -> dict | None:
        # a sub-theme or a group with what it holds, its groups the same way, one holding nothing gone
        members = fresh(s["members"])
        inner = [x for x in (kept(gr) for gr in s.get("groups") or []) if x]
        return ({"label": s["label"], "members": members, "groups": inner, "description": s.get("description") or ""}
                if members or inner else None)

    themes = []
    for g in groups:
        own = fresh(g["members"])
        subs = [x for x in (kept(s) for s in g["groups"]) if x]
        if own or subs:
            themes.append({"label": g["label"], "own": own, "subs": subs, "description": g.get("description") or ""})
    blobs = [_blob(t["label"], t["own"], t["subs"], texts, size, 0, t["description"]) for t in themes]
    homes = th.pack_round([(b["w"], b["h"]) for b in blobs], THEME_GAP) if blobs else []

    placed: dict[str, tuple[int, int]] = {}
    out_groups: list[dict] = []
    subs_out: list[dict] = []
    next_sub = len(themes)
    for i, (t, b, (hx, hy)) in enumerate(zip(themes, blobs, homes)):
        for k, (x, y) in b["cards"].items():
            placed[k] = (round(hx + x), round(hy + y))
        members = list(t["own"])
        # the blob's labels after its own come a sub-theme and then its groups, as `_blob` nests them
        spots = iter(b["labels"][1:])

        def place(s: dict, holder: list) -> None:
            nonlocal next_sub
            item = next(spots)
            next_sub += 1
            made = {"id": f"g{next_sub}", "label": s["label"], "members": list(s["members"]),
                    "x": round(hx + item["x"]), "y": round(hy + item["y"])}
            subs_out.append(made)
            holder.append(made["id"])
            for gr in s.get("groups") or []:
                place(gr, made["members"])

        for s in t["subs"]:
            place(s, members)
        top = b["labels"][0]
        out_groups.append({"id": f"g{i + 1}", "label": t["label"], "members": members,
                           "x": round(hx + top["x"]), "y": round(hy + top["y"])})

    left = [k for k in order if k not in taken]
    if left:
        tall = lambda k: size(k, texts[k]) + (WHY_H if k in why else 0)
        spots = th.pack_round([(CARD_W, tall(k)) for k in left], th.MARGIN)
        if blobs:
            plane = th.union((hx, hy, b["w"], b["h"]) for (hx, hy), b in zip(homes, blobs))
            heap = th.union((x, y, CARD_W, tall(k)) for k, (x, y) in zip(left, spots))
            dx = plane[0] + plane[2] + PILE_SIDE - heap[0]
            dy = plane[1] + plane[3] / 2 - (heap[1] + heap[3] / 2)
        else:
            dx = dy = 0
        for k, (x, y) in zip(left, spots):
            placed[k] = (round(x + dx), round(y + dy))
    for key in gone:
        placed[key] = spot.get(key, (0, 0))

    version_cards = {k: {"x": placed[k][0], "y": placed[k][1], "text": texts[k]} for k in order}
    return {"cards": version_cards, "groups": out_groups + subs_out, "discarded": gone, "picks": {}}


# --------------------------------------------------------------- the calls

def _route_ready(route: dict) -> dict | None:
    return ai_mod.route_ready(route)


def _ask(system: str, user: str, route: dict, transport, max_tokens: int, timeout: float) -> dict:
    provider = route.get("provider") if route.get("provider") in ai_mod.PROVIDERS else ai_mod.ANTHROPIC
    return ai_mod.complete(system, user, provider, route.get("model"), route.get("key"),
                           route.get("local_url"), transport, timeout, max_tokens,
                           route.get("address"), route.get("deployment"))


def group_room(route: dict) -> tuple[int, float]:
    """The token ceiling and the wait a grouping gets, and the review the same: room for a case of a
    hundred statements, more for a model that thinks, and longest for a local one."""
    local = ai_mod.is_local(route.get("provider"))
    thinking = not local and ai_mod.thinks(route.get("model") or ai_mod.MODEL)
    return (GROUP_THINKING_MAX_TOKENS if thinking else GROUP_MAX_TOKENS,
            GROUP_LOCAL_TIMEOUT if local else GROUP_THINKING_TIMEOUT if thinking else GROUP_TIMEOUT)


def group(statements: list[dict], labels: list[dict], question: str | None, hint: str,
          route: dict, transport=None, cap: int = CAP) -> dict:
    """One call for a grouping of the statements into no more themes than `cap` allows, read
    strictly, or one error line."""
    if not statements:
        return {"error": _w("NO_STATEMENTS")}
    rules = guidance_items(RULES)
    if not rules:
        return {"error": _w("NO_GUIDANCE")}
    refused = _route_ready(route)
    if refused:
        return refused
    cap = clean_cap(cap)
    tokens, wait = group_room(route)
    answer = _ask(group_system(question, cap, rules), group_user(statements, labels, hint), route, transport,
                  tokens, wait)
    if "error" in answer:
        return answer
    return parse_grouping(answer["text"], [s["key"] for s in statements], bool(answer.get("truncated")), cap)


def review(board: dict, question: str | None, route: dict, transport=None, asked=None) -> dict:
    """One call for between one and three questions of a board, from `themes.outline`, read
    strictly against what is on it, or one error line. `asked`, from `asked_of`, is every question
    earlier rounds asked, each with his state on it, which the prompt carries and the answer may not
    repeat. Nothing is written."""
    if not board.get("themes"):
        return {"error": _w("NOTHING_TO_REVIEW")}
    rules, questions = guidance_items(RULES), guidance_items(QUESTIONS)
    if not rules or not questions:
        return {"error": _w("NO_GUIDANCE")}
    refused = _route_ready(route)
    if refused:
        return refused
    asked = asked or []
    tokens, wait = group_room(route)
    answer = _ask(review_system(question, rules, questions, any_note(board["themes"]), bool(asked)),
                  review_user(board, asked), route, transport, tokens, wait)
    if "error" in answer:
        return answer
    return parse_review(answer["text"], board_keys(board), bool(answer.get("truncated")), [n for n, _ in rules],
                        [a["question"] for a in asked])


def reply(board: dict, item: dict | None, words: str, question: str | None, route: dict, transport=None) -> dict:
    """One call for a short answer to his words on one question of a review: the board from
    `themes.outline`, the question with its why and the exchange under it so far, read strictly, or
    one error line. Nothing is written."""
    if not one_line(words):
        return {"error": _w("NO_REPLY")}
    if not item or not one_line(item.get("question")):
        return {"error": _w("NO_SUCH_QUESTION")}
    rules = guidance_items(RULES)
    if not rules:
        return {"error": _w("NO_GUIDANCE")}
    refused = _route_ready(route)
    if refused:
        return refused
    local = ai_mod.is_local(route.get("provider"))
    thinking = not local and ai_mod.thinks(route.get("model") or ai_mod.MODEL)
    answer = _ask(reply_system(question, rules, any_note(board.get("themes") or [])), reply_user(board, item, words),
                  route, transport, ai_mod.THINKING_MAX_TOKENS if thinking else REPLY_MAX_TOKENS, group_room(route)[1])
    if "error" in answer:
        return answer
    return parse_reply(answer["text"], bool(answer.get("truncated")))


def _ask_names(system: str, user: str, route: dict, transport) -> dict:
    """The titles' one call, with the room and the wait a title gets, read strictly."""
    local = ai_mod.is_local(route.get("provider"))
    thinking = not local and ai_mod.thinks(route.get("model") or ai_mod.MODEL)
    answer = _ask(system, user, route, transport,
                  ai_mod.THINKING_MAX_TOKENS if thinking else NAMES_MAX_TOKENS,
                  ai_mod.LOCAL_TIMEOUT if local else NAMES_THINKING_TIMEOUT if thinking else NAMES_TIMEOUT)
    if "error" in answer:
        return answer
    return parse_names(answer["text"], bool(answer.get("truncated")))


def names(statements: list[str], label: str, others: list[str], question: str | None,
          route: dict, transport=None, note: str = "") -> dict:
    """One call for three titles for statements a page from before the whole theme sends as bare
    text, with the label's note when it has one, or one error line."""
    statements = [" ".join(str(s).split()) for s in statements or [] if str(s).strip()]
    if not statements:
        return {"error": _w("NOTHING_TO_NAME")}
    rules = guidance_items(RULES)
    if not any(n in TITLE_RULES for n, _ in rules):
        return {"error": _w("NO_GUIDANCE")}
    refused = _route_ready(route)
    if refused:
        return refused
    return _ask_names(names_system(question, rules), names_user(statements, label, others, note), route, transport)


def name_prompts(target: dict, question: str | None, rules=None) -> dict:
    """The two prompts a title for `target` sends, from `names_target`, with the keys of the
    statements whose quotes went for room."""
    rules = guidance_items(RULES) if rules is None else rules
    system = names_system(question, rules)
    user, bare = cut_for_room(system, target)
    return {"system": system, "user": user, "bare": bare}


def pet_names(target: dict | None, question: str | None, route: dict, transport=None) -> dict:
    """One call for three titles for a theme, from `names_target`, or one error line. When the
    quotes of some statements went for room, the answer says so in `said`."""
    if target is None:
        return {"error": _w("NO_SUCH_PET")}
    if not statements_in(target):
        return {"error": _w("NOTHING_TO_NAME")}
    rules = guidance_items(RULES)
    if not any(n in TITLE_RULES for n, _ in rules):
        return {"error": _w("NO_GUIDANCE")}
    refused = _route_ready(route)
    if refused:
        return refused
    built = name_prompts(target, question, rules)
    return room_said(_ask_names(built["system"], built["user"], route, transport), len(built["bare"]), cut_line)


def note(model_name: str, made_from: str, hint: str, result: dict, when: datetime | None = None,
         cap: int | None = None, picked: tuple[int, int] | None = None) -> str:
    """The new board's note, one line: who proposed it, from which board, when, the hint, the
    limit and the counts, with `picked`, how many PETs carry picked quotes of how many, then the
    model's reason as a sentence of its own when it gave one.

        Proposed by Haiku 4.5 from Board 4 on 2 October 2026 at 12:02, up to 5 PETs. 5 PETs, 69
        placed, 12 not placed. Quotes picked for 4 of 5 PETs.

    Why each statement was left out goes into the board under `ai`, which the card in Not placed
    shows, and never into the note."""
    when = when or datetime.now().astimezone()
    themes = len(result.get("groups") or [])
    head = made_head(model_name, made_from, hint, when)
    if cap is not None:
        head = i18n.t("themes_ai.note.up_to_pets", head=head, n=clean_cap(cap))
    said = i18n.t("themes_ai.note.pets_counts", head=head, n=themes, placed=result.get("placed", 0),
                  left=result.get("left", 0))
    if picked is not None:
        said += " " + i18n.t("themes_ai.note.pets_picked", picked=picked[0], n=picked[1])
    return said + reason_said(result)


def made_head(model_name: str, made_from: str, hint: str, when: datetime) -> str:
    """The note's first words, who proposed the board, from what, when, and the hint."""
    hint = clean_hint(hint)
    vals = {"model": model_name, "source": made_from, "day": when.day, "month": formats.LONG[when.month](),
            "year": when.year, "time": f"{when:%H:%M}"}
    return i18n.t("themes_ai.note.head_hint", vals, hint=hint) if hint else i18n.t("themes_ai.note.head", vals)


def reason_said(result: dict) -> str:
    """The model's reason for one more than his limit, as the note's last sentence, or nothing."""
    why = clean_reason(result.get("reason"))
    return " " + i18n.t("themes_ai.note.reason", why=why) + ("" if why[-1] in ".?!" else ".") if why else ""


def left_reasons(result: dict) -> dict:
    """What a proposal keeps with its board: why it left out each statement it left out, by key,
    under the board's `ai`, for the card in Not placed to show. The key keeps the name it had when
    the reasons were for the bin, `discarded`, so a board from before reads as it did. Nothing when
    none came with a reason."""
    reasons = {t["key"]: t["reason"] for t in result.get("left_out") or [] if t.get("reason")}
    return {"discarded": reasons} if reasons else {}


# ------------------------------------------------------ the quotes that carry each PET

PICKS_TASK = " ".join([
    "He has grouped the statements into themes. For each theme and each sub-theme below, pick the one",
    "key quote that best carries its title in the participant's own words. Pick a second only when no",
    "single quote carries the title. Pick only from the quotes listed under that theme or sub-theme, by",
    "their keys exactly as given. A sub-theme's quotes are its own, apart from the theme it sits in.",
    "Give no reasons.",
])

PICKS_SHAPE = "\n".join([
    "Answer with strict JSON and nothing else, in this shape:",
    '{"picks": [{"id": "<theme id>", "quotes": ["<quote key>"]}]}',
    "\"id\" is the id of the theme or sub-theme exactly as given, such as g2, and \"quotes\" holds one",
    "key, or two only when no single quote carries the title.",
])


def _row_of(key: str):
    sheet, row, _ = th.split_card_key(key)
    return None if row is None else th.row_key(sheet, row)


def carry_picks(version: dict, groups: list[dict], picks: dict) -> dict:
    """His own picks on a new board made from his: a label the proposal titles as one of his labels
    that carries picks keeps those of them whose row still has a card under it. Titles match with
    the case and the spacing set aside. Answers the picks kept, by the new board's label ids."""
    his: dict[str, list[str]] = {}
    for g in groups or []:
        title = one_line(g.get("label")).lower()
        if title and picks.get(g["id"]) and title not in his:
            his[title] = list(picks[g["id"]])
    by_id = {g["id"]: g for g in version.get("groups") or []}
    out: dict[str, list[str]] = {}
    for gid, g in by_id.items():
        chosen = his.get(one_line(g.get("label")).lower())
        if not chosen:
            continue
        rows = {_row_of(k) for k in th.cards_under(by_id, gid)}
        kept = [k for k in chosen if _row_of(k) in rows]
        if kept:
            out[gid] = kept
    return out


def picks_targets(version: dict, quotes: dict, sheets=(), keep=frozenset()) -> list[dict]:
    """The labels of a new board the picks call asks about, each PET followed by its sub-themes:
    its id, its title, the title of the PET a sub-theme sits in, and the key quotes of the cards
    under it, each statement's own, at any depth, in transcript order, each by its key and words. A
    label in
    `keep`, one that carries his own picks, is left out, and so is one whose cards carry no quotes."""
    groups = version.get("groups") or []
    by_id = {g["id"]: g for g in groups}
    parent = {m: g for g in groups for m in g["members"] if m in by_id}
    place = {s: i for i, s in enumerate(sheets or [])}
    order: list[dict] = []

    def walk(g: dict) -> None:
        order.append(g)
        for m in g["members"]:
            if m in by_id and by_id[m] not in order:
                walk(by_id[m])

    for g in groups:
        if g["id"] not in parent:
            walk(g)
    out = []
    for g in order:
        if g["id"] in keep:
            continue
        # its statements' own key quotes, in transcript order
        owned = []
        for key in th.cards_under(by_id, g["id"]):
            sheet, row, line = th.split_card_key(key)
            if row is not None and (sheet, row, line) not in owned:
                owned.append((sheet, row, line))
        owned.sort(key=lambda r: (place.get(r[0], len(place)), r[1], r[2]))
        said = [{"key": q["key"], "text": one_line(q.get("text"))} for q in
                (th.own_quote(quotes, th.card_key(*k)) for k in owned) if q and one_line(q.get("text"))]
        if said:
            up = parent.get(g["id"])
            out.append({"id": g["id"], "label": g["label"], "inside": up["label"] if up else None, "quotes": said})
    return out


def picks_system(question: str | None) -> str:
    """The picks call's system prompt: the introduction, the research question, the task and the
    shape of the answer."""
    return _join([INTRO, question_block(question), PICKS_TASK, PICKS_SHAPE])


def picks_user(targets: list[dict]) -> str:
    """The picks call's user prompt: each label by its id and its title, a sub-theme with the PET it
    sits in, and under it the key quotes it can take, each by its key and its words."""
    blocks = []
    for t in targets:
        if t.get("inside") is None:
            head = f"Theme {t['id']}: {titled(t['label'])}"
        elif titled(t["inside"]) == "no title yet":
            head = f"Sub-theme {t['id']}: {titled(t['label'])}, inside a theme with no title yet"
        else:
            head = f"Sub-theme {t['id']}: {titled(t['label'])}, inside the theme {titled(t['inside'])}"
        blocks.append("\n".join([head] + [f"- {q['key']} {th.quoted(q['text'])}" for q in t["quotes"]]))
    return "\n\n".join(["The themes on this board, each by its id and its title, with the key quotes of the "
                        "passages under it, each by its key and its words.", *blocks, "Pick the quotes."])


def parse_picks(text: str, allowed: dict, truncated: bool = False) -> dict:
    """The quotes picked for each label, read strictly against the quotes each was sent. Fences and
    chatter round the JSON are stripped. A label the call did not ask about is left out, and a label
    named twice keeps the first. A key not among that label's quotes is dropped, a key named twice
    counts once, more than two keep the first two, and a label with none keeps none. An answer that
    is not JSON is one error line, and one cut off at its length limit says so."""
    data = _load(text)
    if isinstance(data, dict):
        data = data.get("picks")
    if isinstance(data, dict):
        data = [{"id": gid, "quotes": keys} for gid, keys in data.items()]
    if not isinstance(data, list):
        return {"error": ai_mod.TOO_LONG if truncated else ai_mod.NOT_JSON}
    picks: dict[str, list[str]] = {}
    for item in data:
        if not isinstance(item, dict):
            continue
        gid = one_line(item.get("id"))
        if gid not in allowed or gid in picks:
            continue
        chosen = item.get("quotes") if item.get("quotes") is not None else item.get("keys")
        chosen = [chosen] if isinstance(chosen, str) else chosen if isinstance(chosen, list) else []
        kept: list[str] = []
        for key in chosen:
            key = one_line(key.get("key") if isinstance(key, dict) else key)
            if key in allowed[gid] and key not in kept:
                kept.append(key)
        if kept:
            picks[gid] = th.picks_kept(kept, PICKS_MAX)
    return {"picks": picks}


def pick_quotes(targets: list[dict], question: str | None, route: dict, transport=None) -> dict:
    """One call for the quotes that carry each label of `targets`, from `picks_targets`, read
    strictly, or one error line. With no targets nothing is asked and nothing is picked."""
    if not targets:
        return {"picks": {}}
    refused = _route_ready(route)
    if refused:
        return refused
    local = ai_mod.is_local(route.get("provider"))
    thinking = not local and ai_mod.thinks(route.get("model") or ai_mod.MODEL)
    answer = _ask(picks_system(question), picks_user(targets), route, transport,
                  ai_mod.THINKING_MAX_TOKENS if thinking else PICKS_MAX_TOKENS,
                  ai_mod.LOCAL_TIMEOUT if local else PICKS_THINKING_TIMEOUT if thinking else PICKS_TIMEOUT)
    if "error" in answer:
        return answer
    return parse_picks(answer["text"], {t["id"]: {q["key"] for q in t["quotes"]} for t in targets},
                       bool(answer.get("truncated")))


def quoted_of(picks: dict, quotes: dict) -> dict:
    """The words of every quote the picks name, as the workbook holds them, which a save by hand
    keeps beside the picks so each can follow its words."""
    words = {q["key"]: q["text"] for row in (quotes or {}).values() for q in row.get("quotes") or []}
    return {k: words[k] for chosen in picks.values() for k in chosen if k in words}


def picked_count(version: dict) -> tuple[int, int]:
    """How many of a board's PETs carry picks, and how many PETs it has, a PET being a label no
    other label holds."""
    groups = version.get("groups") or []
    inner = {m for g in groups for m in g["members"]}
    top = [g["id"] for g in groups if g["id"] not in inner]
    picks = version.get("picks") or {}
    return sum(1 for gid in top if picks.get(gid)), len(top)


# ----------------------------------------------------------------- AI revise
#
# His request in his own words, and the board changed by the operations the answer names, never a
# whole board, so everything he did not ask about keeps its place. The board here is a plain dict,
# `revise_start`'s: `items`, the keys on it an operation may name, `groups`, each label by its id
# with its title, its note and its members, `picks` by label, and `quotes`, the quote keys of each
# row. Nothing in it is particular to PETs. A GETs board carries three keys more: `prefix`, `G`, the
# letter its labels' ids start with, `card_quotes`, the quote keys each card carries, since a card
# there is a case's PET or statement and no row of one workbook, and `pick_max`, the quotes a pick
# may name, one for each case (see `gets_revise_start`). A board with no `pick_max` is an AI
# answer's, held to `PICKS_MAX`. The command line's carries None, the app's own rule for a pick by
# hand, every quote named, each once (see `themes.picks_kept`).

REVISE_OPS = ("retitle", "note", "move", "make", "merge", "apart", "pick")
DESCRIBE = "describe"   # a label's description, his own words, through board apply and gets apply alone
REVISE_MAX_TOKENS = 4000
NOTE_LIMIT = 2000
REVISE_LINE = 80     # the request in a revision's name, cut at a word to one short line

# why an operation was left out, as the answer's last sentence says it
COUNTS = ("no", "one", "two", "three", "four", "five", "six", "seven", "eight", "nine", "ten")

REVISE_INTRO = ("You help a researcher doing Interpretative Phenomenological Analysis (IPA, Smith, Flowers "
                "and Larkin) at the step where one participant's experiential statements are clustered "
                "into personal experiential themes. He has grouped them on a board himself, and asks in "
                "his own words for a change to it. You make the change he asks for and nothing else. "
                "Every analytic judgement stays with him.")

REVISE_EXAMPLE = ("Retitled 'Walks' as 'Evening walks that close the day together' and moved three "
                  "statements from 'A house that holds two' into it.")

REVISE_TASK = " ".join([
    "Change only what his request asks for, and leave everything else on the board where it is.",
    "Answer with operations on the board, never with a whole board.",
    "Name a statement by its key and a label by its id, exactly as the board gives them, and a label an",
    "earlier operation made by its ref.",
    "Operations run in order, each on the board as the ones before it left it.",
    "Never put a statement in the bin or take one out of it, never change a statement's words, and",
    "never name a statement that is not on the board.",
    "When the request, or a part of it, asks for something these operations cannot do, such as new",
    "words for a statement or the bin, make no operation for that part, change nothing else in its",
    "place, and say why in \"said\".",
    "A title follows the rules for a title, and a note is his own reasoning for a theme, why it exists",
    "and what it holds, in plain words.",
    "\"said\" says what changed in one or two plain sentences, such as",
    f"\"{REVISE_EXAMPLE}\"",
    VOICE,
    "In \"said\", name a theme by its title and a statement by its own words, never by an id or a key.",
    "Plain words, no therapeutic jargon, no claim about causes, no em dashes and no semicolons.",
])

REVISE_SHAPE = "\n".join([
    "Answer with strict JSON and nothing else, in this shape:",
    '{"operations": [], "said": "..."}',
    "Each operation is one of these:",
    '{"op": "retitle", "label": "<id>", "title": "..."} gives a label a new title.',
    '{"op": "note", "label": "<id>", "note": "..."} writes a label\'s note afresh.',
    '{"op": "move", "items": ["<key or id>"], "to": "<id or null>"} moves statements or labels into a',
    "label, a label becoming a sub-theme there, or with null out to Not placed, where a label stands as",
    "a theme of its own.",
    '{"op": "make", "ref": "new1", "title": "...", "inside": "<id or null>", "members": ["<key or id>"]}',
    "makes a label holding its members: a theme, or a sub-theme of the theme \"inside\" names.",
    '{"op": "merge", "label": "<id>", "into": "<id>"} moves every member of the first label into the',
    "second and takes the first away, the second keeping its title.",
    '{"op": "apart", "label": "<id>", "to": "parent"} takes a label away, its members going to the',
    "theme it sits in, or with \"to\" of \"unplaced\" out to Not placed.",
    '{"op": "pick", "label": "<id>", "quotes": ["<quote key>"]} sets the key quote that carries a',
    "label, a second only when no single one does, from the quotes of the statements under it.",
    "\"operations\" is empty when nothing should change.",
])


def revise_system(question: str | None, rules=None, theme: str | None = None, intro: str = REVISE_INTRO) -> str:
    """A revise's system prompt: the introduction, the research question, what a theme is from
    section 1 of the guidance file, the rules for a theme from section 3, the task with its voice,
    and the shape of the answer, the operations named. `intro` is the step the board belongs to."""
    rules = guidance_items(RULES) if rules is None else rules
    theme = guidance_prose(WHAT_A_THEME) if theme is None else theme
    return _join([intro, question_block(question), one_line(theme) and theme.strip() or THEME,
                  rules_block(rules) if rules else None, REVISE_TASK, FORMAT, REVISE_SHAPE])


def revise_board(read: dict, version: dict) -> dict:
    """The board a revise sends, `themes.outline`'s, each statement carrying its own key quote by
    its key and its place on the canvas, `x` and `y`, for the cut, the ones not placed too. Nothing
    is written."""
    board = th.outline(read, version)
    quotes = read.get("quotes") or {}
    spots = th.follow(version, read["cards"], read["quotes"])["cards"]

    def with_quotes(s: dict) -> dict:
        own = th.own_quote(quotes, s["key"]) if not s.get("missing") else None
        spot = spots.get(s["key"]) or {}
        return dict(s, x=spot.get("x", 0), y=spot.get("y", 0),
                    quotes=[{"key": own["key"], "text": own["text"]}] if own else [])

    def theme(t: dict) -> dict:
        return dict(t, statements=[with_quotes(s) for s in t["statements"]], themes=[theme(s) for s in t["themes"]])

    return dict(board, themes=[theme(t) for t in board["themes"]],
                unplaced=[with_quotes(s) for s in board.get("unplaced") or []])


def board_statements(board: dict) -> list[dict]:
    """Every statement a revise's board sends, under its labels at any depth and then not placed."""
    return [s for t in board.get("themes") or [] for s in statements_in(t)] + list(board.get("unplaced") or [])


def statement_block(s: dict, pad: str, rows: set, bare=frozenset()) -> list[str]:
    """One statement as a revise sends it, with its key, sheet and timecode, and under it its own
    key quote by its key, none for a statement in `bare`."""
    out = [f"{pad}- {s['key']} ({_where(s)}) {_said(s)}"]
    if s["key"] in bare:
        return out
    fresh = [q for q in s.get("quotes") or [] if q["key"] not in rows]
    rows.update(q["key"] for q in fresh)
    return out + [f"{pad}    quote {q['key']} {th.quoted(one_line(q.get('text')))}" for q in fresh]


def revise_lines(theme: dict, depth: int = 0, bare=frozenset()) -> list[str]:
    """One label of the board as a revise sends it: its id, title and count, its note, its
    statements in the order the canvas reads them with their turns' quotes, the quotes picked to
    carry it by their keys, then its sub-themes indented under it. A statement in `bare` goes
    without its quote."""
    pad = "  " * depth
    out = [f"{pad}{'Sub-theme' if depth else 'Theme'} {theme['id']}: {titled(theme.get('label'))} ({theme['count']})"]
    if one_line(theme.get("note")):
        out.append(f"{pad}  Note: {one_line(theme.get('note'))}")
    rows: set = set()
    for s in theme["statements"]:
        out += statement_block(s, pad + "  ", rows, bare)
    picked = [p["key"] for p in theme.get("picks") or []]
    out.append(f"{pad}  Picked to carry it: {', '.join(picked)}" if picked else f"{pad}  No quotes picked yet.")
    for sub in theme.get("themes") or []:
        out += revise_lines(sub, depth + 1, bare)
    return out


def thread_part(thread, dropped: int = 0) -> str:
    """A revise's thread as both screens' prompts send it, his requests so far on the board with
    their answers, oldest first, the oldest `dropped` lines left out for room and said so. Nothing
    for a board with no thread."""
    said = th.thread_of(thread)
    if not said:
        return ""
    kept = said[dropped:]
    if not kept:
        return "His requests so far on this board and their answers are left out here for room."
    gone = len(said) - len(kept)
    head = ("His requests so far on this board, oldest first, each with the answer. The board above is as it "
            "stands now, after whatever of those changes he kept or undid.")
    if gone:
        head += (" The oldest of these lines is" if gone == 1 else f" The {_count(gone)} oldest of these lines are") \
            + " left out here for room."
    return head + "\n" + "\n".join(f"{'He asked' if line['by'] == 'analyst' else 'The answer'}: {one_line(line['text'])}"
                                   for line in kept)


def cut_thread(system: str, build, lines: int, ceiling: int) -> tuple[str, int]:
    """A user prompt inside the ceiling where the thread allows, `build(dropped)` making it with the
    oldest `dropped` lines of its `lines` left out: past it, the oldest go one at a time, the newest
    kept, until the two prompts fit or none is left. Answers with the prompt and how many went."""
    dropped, user = 0, build(0)
    while dropped < lines and len(system) + len(user) > ceiling:
        dropped += 1
        user = build(dropped)
    return user, dropped


def revise_user(board: dict, thread, words: str, bare=frozenset(), dropped: int = 0) -> str:
    """A revise's user prompt: the board as it stands, label by label, then the statements not
    placed, the requests so far on this board with their answers, and his request. Sticky notes,
    the bin and the interviewer's notes are never in it. A statement in `bare` goes without its
    quote, and the oldest `dropped` lines of the thread go, each said in a line of the prompt."""
    themes = board.get("themes") or []
    parts = ["The board as it stands now, theme by theme in the order the canvas reads them, top to bottom "
             "and left to right. Each label has its id, and each statement its key, its sheet and its "
             "timecode, with the key quotes of its passage under it, each by its key.\n"
             + ("\n".join(line for t in themes for line in revise_lines(t, 0, bare)) if themes else "There are no labels yet.")]
    left = board.get("unplaced") or []
    rows: set = set()
    parts.append("Not placed:\n" + "\n".join(line for s in left for line in statement_block(s, "", rows, bare))
                 if left else "Every statement on the board is placed.")
    if bare:
        parts.append(quotes_left(len(bare)))
    said = thread_part(thread, dropped)
    if said:
        parts.append(said)
    parts.append(f"He asks now: {one_line(words)}")
    parts.append("Change the board.")
    return "\n\n".join(parts)


def revise_prompts(board: dict, thread, words: str, system: str, ceiling: int) -> dict:
    """The user prompt a revise sends, inside the ceiling where the quotes and the thread allow,
    with `bare`, the statements whose quotes went, and `dropped`, the thread's lines that went: past
    it, the quotes of the statements lowest on the canvas go first, one statement at a time, and with
    none left the oldest lines of the thread, one at a time, until the two prompts fit or none is
    left. The statements, their keys, the labels and his request always go whole."""
    said = th.thread_of(thread)
    user, bare = cut_quotes(system, lambda b: revise_user(board, said, words, b), board_statements(board), ceiling)
    user, dropped = cut_thread(system, lambda d: revise_user(board, said, words, bare, d), len(said), ceiling)
    return {"user": user, "bare": bare, "dropped": dropped}


def revise_start(read: dict, version: dict) -> dict:
    """The plain board revise's parser and applier work on, from the workbook as `themes.read_cards`
    reads it and a stored board: `items`, the statements on it, neither in the bin, nor stacked under
    another, nor gone from the workbook, `groups`, each label by its id with its title, its note and its members, `picks` by
    label, and `quotes`, the quote keys of each row by its row key. Its keys follow their words as
    the outline's do."""
    merged = th.merge(read["cards"], version, read["quotes"])
    # a statement stacked under another is none of the items, since its top stands for it
    thrown = set(merged["discarded"]) | th.stacked_keys(merged)
    items = [c["key"] for c in merged["cards"] if not c.get("missing") and c["key"] not in thrown]
    groups = []
    for g in merged["groups"]:
        kept = {"id": g["id"], "label": g["label"], "members": list(g["members"])}
        if one_line(g.get("note")):
            kept["note"] = g["note"]
        if th.description_of(g):
            kept[th.DESCRIPTION] = th.description_of(g)
        groups.append(kept)
    quotes = {row: [q["key"] for q in held.get("quotes") or []] for row, held in (read.get("quotes") or {}).items()}
    return {"items": items, "groups": groups, "picks": {g: list(k) for g, k in merged["picks"].items()},
            "quotes": quotes}


class Refused(Exception):
    """An operation left out, with why, as the answer's last sentence says it."""


def clean_note(text) -> str:
    """A note as a revise writes it: one paragraph, no em dash, no semicolon, not past its length."""
    words = " ".join(str(text or "").split())
    return re.sub(r"\s*\u2014\s*", ", ", words).replace(";", ",")[:NOTE_LIMIT].strip()


def revise_ops(board: dict, raw) -> tuple[dict, list[dict], list[str], dict]:
    """The operations of an answer read strictly and applied in order to a copy of `board`, from
    `revise_start`. Each is applied whole or refused whole: one that names a statement, a label or a
    quote that is not there, that would put a label inside itself, that cannot be read, or that asks
    for something revise does not do, the bin or a statement's words among them, is refused with
    why, and the rest stand. A label a `make` made is named by its ref in a later one, and takes an
    id past every id the board held. Picks keep only quotes of rows still under their label.

    Answers the board afterwards, the operations applied as they were read, the reason for each one
    refused, and `info`: `made`, the new labels' ids, and `gone`, each label taken away with where
    its members went, the label it merged into, the label it sat in, or None."""
    board = json.loads(json.dumps(board))
    items = set(board["items"])
    groups = board["groups"]
    picks = board["picks"]
    prefix = str(board.get("prefix") or "g")
    numbers = [int(str(g["id"])[len(prefix):]) for g in groups
               if str(g["id"]).startswith(prefix) and str(g["id"])[len(prefix):].isdigit()]
    top = max(numbers, default=0)
    carried = board.get("card_quotes") if isinstance(board.get("card_quotes"), dict) else None
    pick_max = board.get("pick_max", PICKS_MAX)
    pick_max = None if pick_max is None else max(1, int(pick_max))
    refs: dict[str, str] = {}
    made: list[str] = []
    gone: dict[str, str | None] = {}
    applied: list[dict] = []
    refused: list[str] = []

    def ids() -> dict:
        return {g["id"]: g for g in groups}

    def parent_of(it: str) -> str | None:
        return next((g["id"] for g in groups if it in g["members"]), None)

    def held_by(gid: str) -> set:
        """`gid` and every label inside it, at any depth."""
        known, out, stack = ids(), set(), [gid]
        while stack:
            at = stack.pop()
            if at in out or at not in known:
                continue
            out.add(at)
            stack.extend(m for m in known[at]["members"] if m in known)
        return out

    def known(name: str) -> str:
        """A name as the board holds it: a ref an earlier `make` gave, or the name itself, and
        "Theme g2" or "statement Initial:12:0" by its last word."""
        name = one_line(name)
        last = name.split(" ")[-1].strip(".,:'\"") if " " in name else name
        for said in (name, last):
            said = refs.get(said, said)
            if said in ids() or said in items:
                return said
        return refs.get(name, name)

    def label(name) -> str:
        name = known(name)
        if name not in ids():
            raise Refused(_w("UNKNOWN_LABEL"))
        return name

    def thing(name) -> str:
        if not isinstance(name, str):
            raise Refused(_w("UNREADABLE"))
        name = known(name)
        if name in ids() or name in items:
            return name
        raise Refused(_w("UNKNOWN_STATEMENT") if ":" in name else _w("UNKNOWN_LABEL"))

    def things(value) -> list[str]:
        value = [value] if isinstance(value, str) else value if isinstance(value, list) else None
        if not value:
            raise Refused(_w("UNREADABLE"))
        out = []
        for v in value:
            found = thing(v)
            if found not in out:
                out.append(found)
        return out

    def where(value) -> str | None:
        """Where a move or a new label goes: a label, or None for Not placed."""
        if value is None or one_line(value).lower() in ("", "null", "none", "unplaced", "not placed"):
            return None
        return label(value)

    def detach(it: str) -> None:
        for g in groups:
            if it in g["members"]:
                g["members"].remove(it)

    def no_loop(moving: list[str], into: str | None) -> None:
        if into is None:
            return
        for it in moving:
            if it in ids() and into in held_by(it):
                raise Refused(_w("INSIDE_ITSELF"))

    def remove(gid: str) -> None:
        detach(gid)
        groups[:] = [g for g in groups if g["id"] != gid]
        picks.pop(gid, None)

    def quotes_under(gid: str) -> set:
        """The quote keys a pick on `gid` may name: its cards' own, at any depth, with those it has
        picked already, or on a GETs board those each card under it carries."""
        under = th.cards_under(ids(), gid)
        if carried is not None:
            return {q for k in under for q in carried.get(k) or []}
        # its statements' own, a quote's key being its statement's, and the ones it has picked
        return ({k for k in under if k in board["quotes"].get(_row_of(k), [])}
                | {k for k in picks.get(gid, []) if _row_of(k) in {_row_of(u) for u in under}})

    for op in raw if isinstance(raw, list) else []:
        try:
            if not isinstance(op, dict):
                raise Refused(_w("UNREADABLE"))
            kind = one_line(op.get("op") or op.get("type")).lower()
            # a description is his own words, written by an agent only on his word through board apply and
            # gets apply, which mark their board `human`, never by an AI revise (Adam, 21 October)
            if kind not in REVISE_OPS and not (kind == DESCRIBE and board.get("human")):
                raise Refused(_w("NOT_DONE"))
            if kind == DESCRIBE:
                gid = label(op.get("label"))
                said = op.get("description")
                # "" or null takes it off, and one left out altogether cannot be read
                if "description" not in op or not isinstance(said, (str, type(None))):
                    raise Refused(_w("UNREADABLE"))
                words = th.description_of({th.DESCRIPTION: said})
                if words:
                    ids()[gid][th.DESCRIPTION] = words
                else:
                    ids()[gid].pop(th.DESCRIPTION, None)
                applied.append({"op": kind, "label": gid, "description": words})
            elif kind == "retitle":
                gid, title = label(op.get("label")), clean_label(op.get("title"))
                if not title:
                    raise Refused(_w("UNREADABLE"))
                ids()[gid]["label"] = title
                applied.append({"op": kind, "label": gid, "title": title})
            elif kind == "note":
                gid, words = label(op.get("label")), clean_note(op.get("note"))
                # a note given empty, "" or null, takes the label's note away, as clearing it does
                # on the canvas, and a note left out altogether cannot be read
                if not words and ("note" not in op or not isinstance(op.get("note"), (str, type(None)))):
                    raise Refused(_w("UNREADABLE"))
                if words:
                    ids()[gid]["note"] = words
                else:
                    ids()[gid].pop("note", None)
                applied.append({"op": kind, "label": gid, "note": words})
            elif kind == "move":
                moving = things(op.get("items") if op.get("items") is not None else op.get("item"))
                to = where(op.get("to"))
                if to in moving:
                    raise Refused(_w("INSIDE_ITSELF"))
                no_loop(moving, to)
                for it in moving:
                    detach(it)
                    if to is not None:
                        ids()[to]["members"].append(it)
                applied.append({"op": kind, "items": moving, "to": to})
            elif kind == "make":
                title = clean_label(op.get("title") or op.get("label")) or UNTITLED
                inside = where(op.get("inside"))
                # no members, or an empty list, makes an empty label to fill, as G with nothing selected and
                # New group inside do on the canvas and in the table (20 October)
                members = things(op.get("members")) if op.get("members") not in (None, []) else []
                if inside in members:
                    raise Refused(_w("INSIDE_ITSELF"))
                no_loop(members, inside)
                top += 1
                gid = f"{prefix}{top}"
                ref = one_line(op.get("ref"))
                if ref and ref not in ids() and ref not in items:
                    refs[ref] = gid
                for it in members:
                    detach(it)
                groups.append({"id": gid, "label": title, "members": list(members)})
                if inside is not None:
                    ids()[inside]["members"].append(gid)
                made.append(gid)
                applied.append({"op": kind, "label": gid, "title": title, "inside": inside, "members": members})
            elif kind == "merge":
                gid, into = label(op.get("label")), label(op.get("into"))
                if gid == into or into in held_by(gid):
                    raise Refused(_w("INSIDE_ITSELF"))
                for m in list(ids()[gid]["members"]):
                    detach(m)
                    ids()[into]["members"].append(m)
                joined = picks.get(into, []) + [k for k in picks.get(gid, []) if k not in picks.get(into, [])]
                remove(gid)
                if joined:
                    picks[into] = joined
                gone[gid] = into
                applied.append({"op": kind, "label": gid, "into": into})
            elif kind == "apart":
                gid = label(op.get("label"))
                up = parent_of(gid)
                out = one_line(op.get("to")).lower() in ("unplaced", "not placed", "null", "none")
                members = list(ids()[gid]["members"])
                if up is not None and not out:
                    owner = ids()[up]["members"]
                    at = owner.index(gid)
                    owner[at:at + 1] = [m for m in members if m not in owner]
                    ids()[gid]["members"] = []
                else:
                    for m in members:
                        detach(m)
                    up = None
                remove(gid)
                gone[gid] = up
                applied.append({"op": kind, "label": gid, "to": up})
            else:
                gid = label(op.get("label"))
                chosen = op.get("quotes") if op.get("quotes") is not None else op.get("quote")
                chosen = [chosen] if isinstance(chosen, str) else chosen if isinstance(chosen, list) else []
                keys: list[str] = []
                for k in chosen:
                    k = one_line(k.get("key") if isinstance(k, dict) else k)
                    if k and k not in keys:
                        keys.append(k)
                if not keys:
                    raise Refused(_w("UNREADABLE"))
                allowed = quotes_under(gid)
                if carried is not None:
                    # a quote named without its case, where one case under the label alone has it
                    def whole(k: str) -> str:
                        found = [a for a in allowed if a.split("/", 1)[-1] == k]
                        return found[0] if k not in allowed and "/" not in k and len(found) == 1 else k
                    keys = list(dict.fromkeys(whole(k) for k in keys))
                if any(k not in allowed for k in keys):
                    raise Refused(_w("UNKNOWN_QUOTE"))
                picks[gid] = th.picks_kept(keys, pick_max)
                applied.append({"op": kind, "label": gid, "quotes": list(picks[gid])})
        except Refused as why:
            refused.append(str(why))

    # a pick keeps only quotes of a row still under its label, and a label gone took its own
    known = ids()
    for gid in list(picks):
        if carried is not None:
            allowed = quotes_under(gid) if gid in known else set()
            kept = [k for k in picks[gid] if k in allowed]
        else:
            rows = {_row_of(k) for k in th.cards_under(known, gid)} if gid in known else set()
            kept = [k for k in picks[gid] if _row_of(k) in rows]
        if kept:
            picks[gid] = kept
        else:
            picks.pop(gid)
    return board, applied, refused, {"made": [g for g in made if g in known], "gone": gone}


def _count(n: int) -> str:
    """A small number in words, for the prompts, which stay English."""
    return COUNTS[n] if 0 <= n < len(COUNTS) else str(n)


# a small number in words in the run's language, for the lines the person reads
COUNTS_SAID = (lambda: i18n.t("themes_ai.number.no"), lambda: i18n.t("themes_ai.number.one"),
               lambda: i18n.t("themes_ai.number.two"), lambda: i18n.t("themes_ai.number.three"),
               lambda: i18n.t("themes_ai.number.four"), lambda: i18n.t("themes_ai.number.five"),
               lambda: i18n.t("themes_ai.number.six"), lambda: i18n.t("themes_ai.number.seven"),
               lambda: i18n.t("themes_ai.number.eight"), lambda: i18n.t("themes_ai.number.nine"),
               lambda: i18n.t("themes_ai.number.ten"))


def _count_said(n: int) -> str:
    return COUNTS_SAID[n]() if 0 <= n < len(COUNTS_SAID) else str(n)


# so many of a board's units, "two statements", "one card", "three labels", by the unit's own plural forms
UNITS_SAID = {"statement": lambda n: i18n.t("themes_ai.count.statement", n=n, count=_count_said(n)),
              "card": lambda n: i18n.t("themes_ai.count.card", n=n, count=_count_said(n)),
              "label": lambda n: i18n.t("themes_ai.count.label", n=n, count=_count_said(n))}


def _units(n: int, unit: str) -> str:
    said = UNITS_SAID.get(unit)
    return said(n) if said else f"{_count_said(n)} {unit if n == 1 else unit + 's'}"


def refused_line(refused: list[str]) -> str:
    """What the answer says of the operations left out, one sentence, or nothing for none:
    "Left out one change, which named a label not on the board." or "Left out three changes: two
    named a statement not on the board and one named a label not on the board." """
    if not refused:
        return ""
    if len(refused) == 1:
        return i18n.t("themes_ai.refused.one", why=refused[0])
    order: list[str] = []
    for why in refused:
        if why not in order:
            order.append(why)
    said = [i18n.t("themes_ai.refused.part", count=_count_said(refused.count(why)), why=why) for why in order]
    return i18n.t("themes_ai.refused.many", n=len(refused), count=_count_said(len(refused)),
                  list=formats.list_words(said))


def change_line(applied: list[dict], before: dict) -> str:
    """What the operations applied did, said plainly from the board before them, for an answer
    whose own words cannot be trusted to match: some of what it named was left out, or it said
    nothing. Four at most, then how many more. A board's `unit` names what its cards are,
    statements on a PETs board and cards on a GETs board."""
    unit = str(before.get("unit") or "statement")
    titles = {g["id"]: g["label"] for g in before.get("groups") or []}
    name = lambda gid: str(titles.get(gid) or gid)
    said = []
    for op in applied:
        kind = op["op"]
        if kind == "retitle":
            said.append(i18n.t("themes_ai.change.retitled", label=name(op["label"]), title=op["title"]))
            titles[op["label"]] = op["title"]
        elif kind == "note":
            said.append(i18n.t("themes_ai.change.note_rewrote", label=name(op["label"])) if op.get("note")
                        else i18n.t("themes_ai.change.note_off", label=name(op["label"])))
        elif kind == DESCRIBE:
            said.append(i18n.t("themes_ai.change.description_wrote", label=name(op["label"])) if op.get("description")
                        else i18n.t("themes_ai.change.description_off", label=name(op["label"])))
        elif kind == "move":
            n = sum(1 for i in op["items"] if i not in titles)
            labels = len(op["items"]) - n
            if op["to"]:
                what = formats.list_words([p for p in (_units(n, unit) if n else "",
                                                       _units(labels, "label") if labels else "") if p])
                said.append(i18n.t("themes_ai.change.moved_into", what=what, to=name(op["to"])))
            else:
                # a label taken out of every label stands at the top of the board, a statement in Not placed
                cards = i18n.t("themes_ai.change.moved_out", what=_units(n, unit)) if n else ""
                lifted = i18n.t("themes_ai.change.lifted", what=_units(labels, "label")) if labels else ""
                said.append(formats.list_words([x for x in (cards, lifted) if x]))
        elif kind == "make":
            titles[op["label"]] = op["title"]
            inside = name(op["inside"]) if op["inside"] else ""
            if op["members"]:
                said.append(i18n.t("themes_ai.change.made_inside", title=op["title"], inside=inside) if inside
                            else i18n.t("themes_ai.change.made", title=op["title"]))
            else:
                said.append(i18n.t("themes_ai.change.made_empty_inside", title=op["title"], inside=inside) if inside
                            else i18n.t("themes_ai.change.made_empty", title=op["title"]))
        elif kind == "merge":
            said.append(i18n.t("themes_ai.change.merged", label=name(op["label"]), into=name(op["into"])))
        elif kind == "apart":
            said.append(i18n.t("themes_ai.change.apart", label=name(op["label"])))
        else:
            said.append(i18n.t("themes_ai.change.picked", label=name(op["label"])))
    if not said:
        return _w("NOTHING_CHANGED")
    more = len(said) - 4
    said = said[:4] + ([i18n.t("themes_ai.change.more", n=more, count=_count_said(more))] if more > 0 else [])
    text = formats.list_words(said)
    return i18n.t("themes_ai.change.line", changes=text[0].upper() + text[1:])


def parse_revise(text: str, board: dict, truncated: bool = False) -> dict:
    """A revise's answer read strictly against `board`, from `revise_start`. Fences and chatter round
    the JSON are stripped, and the answer is `{"operations": [...], "said": "..."}`, or a bare list
    of operations. Its operations go through `revise_ops`. `said` is its own words, one paragraph
    with no em dash and no semicolon, when every operation stood, and when some were left out or it
    said nothing, the changes said plainly from what was applied, with a last sentence on what was
    left out. An answer that is not JSON, or carries no operations and no words, is one line, and
    one cut off at its length limit says so.

    Answers `applied`, `refused`, `said`, `changed`, whether the board differs, and with it
    `revised`, the labels and picks afterwards with `made` and `gone` for the page to land them."""
    data = _load(text)
    said, raw = "", None
    if isinstance(data, dict):
        said = data.get("said") if isinstance(data.get("said"), str) else ""
        raw = next((data[k] for k in ("operations", "ops", "changes") if isinstance(data.get(k), list)), None)
        if raw is None and said.strip():
            raw = []
    elif isinstance(data, list):
        raw = data
    if raw is None:
        return {"error": ai_mod.TOO_LONG if truncated else ai_mod.NOT_JSON if data is None else _w("NO_CHANGES")}
    after, applied, refused, info = revise_ops(board, raw)
    changed = _structure(after) != _structure(board)
    words = parse_reply(said).get("text", "")
    if refused or not words:
        words = change_line(applied, board) if (applied or refused) else (words or _w("NOTHING_CHANGED"))
        words = " ".join(p for p in (words, refused_line(refused)) if p)
    out = {"applied": applied, "refused": refused, "said": words, "changed": changed}
    if changed:
        out["revised"] = {"groups": after["groups"], "picks": after["picks"], **info}
    return out


def _structure(board: dict) -> dict:
    """What a revise can change of a board, to tell whether it changed anything."""
    return {"groups": board.get("groups") or [], "picks": {g: k for g, k in (board.get("picks") or {}).items() if k}}


def revision_name(words: str) -> str:
    """The revision kept before a revise, "Before: " and his request on one line, cut at a word
    past REVISE_LINE characters with an ellipsis."""
    said = one_line(words)
    if len(said) > REVISE_LINE:
        said = said[:REVISE_LINE].rsplit(" ", 1)[0].rstrip(",.:") + "…"
    return i18n.t("themes_ai.revision_before", request=said)


def revise(read: dict, version: dict, words: str, question: str | None, route: dict, transport=None,
           ceiling: int | None = None) -> dict:
    """One call for his request on a board: the board from the workbook and the stored board, its
    thread so far, the research question, the rules, and his words, read strictly, or one error
    line. When the prompt passes the route's room, `room_of` with the revise's own answer room, or
    `ceiling` when one is given, the quotes go and then the thread's oldest lines (see
    `revise_prompts`), and the answer's `said` ends by saying so. Nothing is written."""
    if not one_line(words):
        return {"error": _w("NO_REQUEST")}
    rules = guidance_items(RULES)
    if not rules:
        return {"error": _w("NO_GUIDANCE")}
    refused = _route_ready(route)
    if refused:
        return refused
    local = ai_mod.is_local(route.get("provider"))
    thinking = not local and ai_mod.thinks(route.get("model") or ai_mod.MODEL)
    tokens = ai_mod.THINKING_MAX_TOKENS if thinking else REVISE_MAX_TOKENS
    start = revise_start(read, version)
    system = revise_system(question, rules)
    built = revise_prompts(revise_board(read, version), th.revise_of(version), words, system,
                           room_of(route, tokens) if ceiling is None else ceiling)
    answer = _ask(system, built["user"], route, transport, tokens, group_room(route)[1])
    if "error" in answer:
        return answer
    return room_said(parse_revise(answer["text"], start, bool(answer.get("truncated"))), len(built["bare"]), cut_line,
                     built["dropped"])


# ---------------------------------------------------------------------- GETs
#
# The same help one layer up, on the GETs screen, through the same route and the same calls: a new
# AI board from every case's PETs or from a GETs board, the key quote of each row, three titles for
# a GET, the review with its replies, and a revise. What goes is built by `gets` from the GETs file
# as plain dicts, every case of the study by its pseudonym, each PET with its note, its sub-themes
# and their statements, and never a participant note, a sticky note or a row's note. The guidance
# is section 5 of `pet_guidance.md`, what a GET is and its rules, and section 6, the questions a
# reviewer asks of a GETs board.

GETS = 5
GETS_QUESTIONS = 6
GETS_TITLE_RULES = (5, 6, 7, 8)
# a provider's own room, past which the PETs words of a GETs prompt go, statement by statement
ANTHROPIC_CONTEXT = 200000
GETS_PICKS_MAX_TOKENS = 3000

GETS_INTRO = ("You help a researcher doing Interpretative Phenomenological Analysis (IPA, Smith, Flowers "
              "and Larkin) at the step after the personal experiential themes, where every participant's "
              "PETs are looked across for what they share and where they part, and grouped into group "
              "experiential themes, GETs. He does that work himself. You offer a first try, which he "
              "keeps, changes or throws away.")

GETS_REVIEW_INTRO = ("You help a researcher doing Interpretative Phenomenological Analysis (IPA, Smith, "
                     "Flowers and Larkin) at the step where every participant's personal experiential "
                     "themes are grouped into group experiential themes, GETs. He has grouped them on a "
                     "board himself, and asks you to review the grouping the way a careful peer reviewer "
                     "or supervisor might: by asking questions of it. Every analytic judgement stays with "
                     "him.")

GETS_REVISE_INTRO = ("You help a researcher doing Interpretative Phenomenological Analysis (IPA, Smith, "
                     "Flowers and Larkin) at the step where every participant's personal experiential "
                     "themes are grouped into group experiential themes, GETs. He has grouped them on a "
                     "board himself, and asks in his own words for a change to it. You make the change he "
                     "asks for and nothing else. Every analytic judgement stays with him.")

GET = ("A group experiential theme gathers the PETs, sub-themes and statements of several participants "
       "that share an experiential meaning, and shows where they part as well as what they share.")

GETS_SHAPE = "\n".join([
    "Answer with strict JSON and nothing else, in this shape:",
    '{"gets": [{"label": "...", "members": ["<PET or sub-theme key>", "<PET or sub-theme key>"], '
    '"groups": [{"label": "...", "members": ["<PET or sub-theme key>"]}]}], '
    '"left_out": [{"key": "<PET or sub-theme key>", "reason": "..."}], "reason": "..."}',
    "Members are the keys of PETs and sub-themes exactly as given. The \"groups\" inside a GET holds",
    "its sub-themes, one level down, there only when the GET has distinct facets. \"left_out\" lists",
    "each PET or sub-theme left out of every GET, with why, and is empty when every one is placed.",
    "\"reason\" is there only when there is one GET more than his limit, and says why.",
])

GETS_LEFT_OUT = ("A PET or a sub-theme you leave out of every GET stays beside them, in Not placed, with your "
                 "reason under it, and he decides what becomes of it. Nothing you answer puts a PET or a "
                 "sub-theme in the bin.")

GETS_REVIEW_TASK = " ".join([
    "Ask at most three questions of this board, the most consequential first, and fewer when fewer",
    "matter.",
    "Check every GET and every participant before you choose, and never draw a pattern from a few of",
    "them.",
    "Each question rests on one of the rules for a GET, takes its lead from the reviewer's questions",
    "where one fits, and is grounded in something on the board: a GET, a sub-theme, a participant's",
    "PET or statement, a row's key quote, a participant with nothing under a GET, or the PETs not",
    "placed.",
    VOICE,
    "Ask, never rule: each is a question, never a verdict.",
    "The why under each question says plainly what on the board prompted it.",
    "Propose no new titles and no new groupings. He decides.",
    "In the question and the why, name a GET by its title, a PET by its title and a participant by",
    "their pseudonym, never by an id or a key, which belong in \"about\" alone.",
    "Plain words, no therapeutic jargon, no claim about causes, no em dashes and no semicolons.",
])

GETS_REVIEW_SHAPE = "\n".join([
    "Answer with strict JSON and nothing else, in this shape:",
    '{"items": [{"about": "<GET id or card key or null>", "question": "<one sentence, a question>", '
    '"rule": "<the rule number it rests on>", "why": "<one sentence grounding it in the board>"}]}',
    "\"about\" is the id of the GET or sub-theme, such as G2, or the key of a card, exactly as the",
    "board gives them, and null when the question is about the board as a whole. \"rule\" is the",
    "number of the rule for a GET the question rests on, never the number of a reviewer's question.",
    "\"why\" says in one sentence what on the board prompted it.",
])

NOTES_GETS = ("A GET may carry an analyst's note, his own reasoning for it, why it exists, what it holds "
              "and what it answers. Weigh it when you ask a question of that GET.")

GETS_REPLY_TASK = " ".join([
    "A review of this board asked him the question below, and he has written back to it, a question",
    "of his own or his view. Answer in two to five sentences, and answer what he asked.",
    "Take his view seriously: agree with it or question it from what the participants' PETs and",
    "statements on the board say, and never decide for him.",
    VOICE,
    "Name a GET or a PET by its title and a participant by their pseudonym, never by an id or a key.",
    "Plain words, no therapeutic jargon, no claim about causes, no em dashes and no semicolons.",
])

GETS_PICKS_TASK = " ".join([
    "He has grouped the participants' PETs into GETs. For each row below, a GET and one participant",
    "under it, pick the one key quote of that participant's that best carries the GET's title in",
    "their own words. Pick only from the quotes listed under that row, by their keys exactly as",
    "given, and give no reasons.",
])

GETS_PICKS_SHAPE = "\n".join([
    "Answer with strict JSON and nothing else, in this shape:",
    '{"picks": [{"id": "<row id>", "quotes": ["<quote key>"]}]}',
    "\"id\" is the row's id exactly as given, such as G1/Juno, and \"quotes\" holds one key.",
])

GETS_REVISE_EXAMPLE = ("Retitled 'Walks' as 'Evening walks that close the day together' and moved two PETs "
                       "from 'A house that holds two' into it.")

GETS_REVISE_TASK = " ".join([
    "Change only what his request asks for, and leave everything else on the board where it is.",
    "Answer with operations on the board, never with a whole board.",
    "Name a card by its key and a GET by its id, exactly as the board gives them, and a label an",
    "earlier operation made by its ref.",
    "Operations run in order, each on the board as the ones before it left it.",
    "Never put a card in the bin or take one out of it, never change the words of a PET or a",
    "statement, never touch a participant note, and never name a card that is not on the board.",
    "When the request, or a part of it, asks for something these operations cannot do, such as the",
    "bin, a participant note or a change to a case's own PETs, make no operation for that part,",
    "change nothing else in its place, and say why in \"said\".",
    "A title follows the rules for a GET's title, and a note is his own reasoning for a GET, why it",
    "exists and what it holds, in plain words.",
    "\"said\" says what changed in one or two plain sentences, such as",
    f"\"{GETS_REVISE_EXAMPLE}\"",
    VOICE,
    "In \"said\", name a GET or a PET by its title and a participant by their pseudonym, never by an",
    "id or a key.",
    "Plain words, no therapeutic jargon, no claim about causes, no em dashes and no semicolons.",
])

GETS_REVISE_SHAPE = "\n".join([
    "Answer with strict JSON and nothing else, in this shape:",
    '{"operations": [], "said": "..."}',
    "Each operation is one of these:",
    '{"op": "retitle", "label": "<id>", "title": "..."} gives a GET or a sub-theme a new title.',
    '{"op": "note", "label": "<id>", "note": "..."} writes its note afresh.',
    '{"op": "move", "items": ["<card key or id>"], "to": "<id or null>"} moves cards or labels into a',
    "GET, a label becoming a sub-theme there, or with null out to Not placed.",
    '{"op": "make", "ref": "new1", "title": "...", "inside": "<id or null>", "members": ["<card key or id>"]}',
    "makes a label holding its members: a GET, or a sub-theme of the GET \"inside\" names.",
    '{"op": "merge", "label": "<id>", "into": "<id>"} moves every member of the first label into the',
    "second and takes the first away, the second keeping its title.",
    '{"op": "apart", "label": "<id>", "to": "parent"} takes a label away, its members going to the',
    "GET it sits in, or with \"to\" of \"unplaced\" out to Not placed.",
    '{"op": "pick", "label": "<GET id>", "quotes": ["<quote key>"]} sets the key quote of a',
    "participant's row under a GET, one quote for each participant at most, from the quotes listed",
    "under that participant's cards there.",
    "\"operations\" is empty when nothing should change.",
])


def gets_question_block(question: str | None) -> str:
    """The project's research question as the GETs prompts say it, or nothing when there is none."""
    asked = one_line(question)
    if not asked:
        return ""
    if asked[-1] not in ".?!":
        asked += "."
    return (f"The study asks: {asked} Every GET answers that question across the participants: what "
            "matters to them, and how it matters in each one's own way.")


def gets_guidance(rules=None, prose: str | None = None) -> str:
    """What a GET is and the rules for one, from section 5 of the guidance file, as the GETs
    prompts carry it, or the one sentence on a GET with no section 5."""
    rules = guidance_items(GETS) if rules is None else rules
    prose = guidance_prose(GETS) if prose is None else prose
    prose = "\n\n".join(p for p in prose.split("\n\n") if not re.match(r"^\d+\.\s", p)) if prose else ""
    head = prose.strip() or GET
    return head + ("\n\nThe rules for a GET, from the IPA guidance he works by:\n" + numbered(rules) if rules else "")


def gets_limit_line(cap: int) -> str:
    cap = clean_cap(cap)
    return (f"His limit is {cap} GETs. Make between {cap - 1} and {cap} GETs. Make {cap + 1} only when the "
            "PETs cannot be held in fewer, and then say why in \"reason\". Never more.")


def minimum_line(minimum: int, total: int) -> str:
    """His minimum as the GETs prompts say it."""
    return (f"His minimum is {int(minimum)} of the {int(total)} participants: a GET gathers material from at "
            "least that many as a rule. A GET under it stays his to keep, and recurrence is one signal of "
            "weight, never its measure.")


# each sub-theme of a case is an item of its own on a GETs board, a card apart from its PET, and the
# guidance's rule 3 says a GET can draw on either (item 193)
SUBS_AS_ITEMS = ("Every PET and every sub-theme is an item of its own, by its own key. A GET can draw on a PET or "
                 "on one of its sub-themes, so a sub-theme may go under the GET its PET sits under or under "
                 "another. Placing a PET does not place its sub-themes: name each sub-theme where it belongs.")


def per_pet_line(one_per_pet: bool) -> str:
    if one_per_pet:
        return ("Place each PET and each sub-theme under one GET, or one of that GET's own sub-themes, at "
                "most. " + SUBS_AS_ITEMS)
    return ("A PET or a sub-theme may sit under more than one GET where it belongs to each, named once under "
            "each. " + SUBS_AS_ITEMS)


def gets_group_system(question: str | None, cap: int = CAP, minimum: int = 1, total: int = 1,
                      one_per_pet: bool = True, rules=None) -> str:
    """A new AI board's system prompt on GETs: the introduction, the research question, the GETs
    section of the guidance file, the task with his limit, his minimum and One GET per PET as set,
    what a PET left out comes to, and the shape of the answer."""
    task = " ".join([
        "A GET gathers PETs and sub-themes of more than one participant as a rule, and may hold",
        "sub-themes of its own, one level down.", per_pet_line(one_per_pet), gets_limit_line(cap),
        "Where his limit and the rules differ on how many GETs, his limit comes first.",
        minimum_line(minimum, total),
    ])
    place = ("Place every PET and sub-theme that belongs under a GET, leave one out only where it shares "
             "nothing with the others, and say why each one left out goes in \"left_out\".")
    return _join([GETS_INTRO, gets_question_block(question), gets_guidance(rules), task,
                  " ".join([place, GETS_LEFT_OUT]), FORMAT, GETS_SHAPE])


def where_of(item: dict) -> str:
    return ", ".join(p for p in (item.get("sheet"), item.get("time")) if p)


def gets_pet_lines(pet: dict, bare=frozenset(), depth: int = 1, skip=frozenset(), kind: str = "") -> list[str]:
    """One PET of a case as a GETs prompt sets it out: its key and title, his note on it, its
    statements in the order its board reads them with their sheets and timecodes, and its
    sub-themes under it the same way. A statement in `bare` loses its words for room, and the line
    says how many did. A PET or a sub-theme in `skip` is not sent, and a sub-theme of one in `skip`
    that is not in it stands where its PET would have, still called a sub-theme, since it is an
    item of its own. `kind` names the line, a PET at the top and a sub-theme below by default."""
    if pet["key"] in skip:
        return [line for sub in pet.get("subs") or [] for line in gets_pet_lines(sub, bare, depth, skip, "Sub-theme")]
    pad = "  " * depth
    kind = kind or ("PET" if depth == 1 else "Sub-theme")
    out = [f"{pad[2:]}- {kind} {pet['key']}: {titled(pet.get('title'))}"]
    if one_line(pet.get("note")):
        out.append(f"{pad}{NOTE_NAMES} {one_line(pet.get('note'))}")
    cut = 0
    for s in pet.get("statements") or []:
        if s["key"] in bare:
            cut += 1
            continue
        out.append(f"{pad}- ({where_of(s)}) {_said(s)}")
    if cut:
        out.append(f"{pad}- the words of {_count(cut)} {'statement' if cut == 1 else 'statements'} more, left out for room")
    for sub in pet.get("subs") or []:
        out += gets_pet_lines(sub, bare, depth + 1, skip)
    return out


def gets_case_lines(case: dict, bare=frozenset(), skip=frozenset()) -> list[str]:
    """One case of the study as the GETs prompts set it out, by its pseudonym, or one line when it
    has no PETs yet. A PET in `skip` is not counted, and its sub-themes not in it are still sent."""
    if case.get("none"):
        return [f"{case['who']}: {case.get('said') or 'no PETs yet'}."]
    pets = case.get("pets") or []
    n = sum(1 for p in pets if p["key"] not in skip)
    head = f"{case['who']}{'' if case.get('complete') else ', PETs not complete'}, {n} {'PET' if n == 1 else 'PETs'}:"
    return [head] + [line for p in pets for line in gets_pet_lines(p, bare, 1, skip)]


def gets_label_lines(labels: list[dict], depth: int = 0) -> list[str]:
    """His GETs on a board as a new AI board from it sends them, nested as they sit, each with the
    PET and sub-theme keys under it and its note."""
    out = []
    for item in labels:
        members = ", ".join(item.get("members") or [])
        out.append(f"{'  ' * depth}- {item['id']} {titled(item['label'])}" + (f": {members}" if members else ""))
        if one_line(item.get("note")):
            out.append(f"{'  ' * depth}  Note: {one_line(item.get('note'))}")
        out.extend(gets_label_lines(item.get("groups") or [], depth + 1))
    return out


def gets_group_user(study: list[dict], labels: list[dict] | None, hint: str = "", bare=frozenset(),
                    skip=frozenset()) -> str:
    """A new AI board's user prompt on GETs: every case of the study, his GETs with what is under each
    when it is made from a board, the hint and the ask."""
    parts = ["The participants of the study, in case order, each with their PETs as their case holds them. "
             "Each PET has its key, its title, his note on it, its statements in the order its board reads "
             "them, each with its sheet and timecode, and its sub-themes under it, each by its own key and "
             "each an item of its own to place.\n\n"
             + "\n\n".join("\n".join(gets_case_lines(c, bare, skip)) for c in study)]
    if bare:
        parts.append(f"The words of {_count(len(bare))} {'statement' if len(bare) == 1 else 'statements'}, the lowest "
                     "in their PETs, are left out here for room, which says nothing about them.")
    if labels:
        parts.append("His GETs on the board now, each with the PETs and sub-themes under it. They are his own: "
                     "keep any that hold, merge them or replace them.\n"
                     + (NOTES_GETS + "\n" if any_note(labels) else "") + "\n".join(gets_label_lines(labels)))
    elif labels is not None:
        parts.append("There are no GETs on the board yet.")
    hint = clean_hint(hint)
    if hint:
        parts.append(f"His hint for this arrangement, which comes before the general guidance: {hint}")
    parts.append("Group the PETs and sub-themes into GETs.")
    return "\n\n".join(parts)


def cut_order(study: list[dict]) -> list[tuple[str, int]]:
    """The statements of the study in the order their words go for room, each with the length its
    line takes: the lowest statement of every PET first, then the next lowest, and so on, so every
    participant keeps words as long as any does."""
    ranked = []
    for ci, case in enumerate(study):
        def walk(pet: dict, at: list) -> None:
            statements = pet.get("statements") or []
            for i, s in enumerate(statements):
                ranked.append((len(statements) - 1 - i, ci, len(at), s["key"], len(_said(s)) + 24))
            at.append(pet["key"])
            for sub in pet.get("subs") or []:
                walk(sub, at)
        held: list = []
        for pet in case.get("pets") or []:
            walk(pet, held)
    ranked.sort(key=lambda r: (r[0], r[1], r[2]))
    return [(r[3], r[4]) for r in ranked]


def room_of(route: dict, tokens: int) -> int:
    """The characters a prompt has: a local model's context less the answer it leaves room for, and
    a provider's own larger one, at about four characters to a token."""
    if ai_mod.is_local(route.get("provider")):
        return PROMPT_CEILING
    return (ANTHROPIC_CONTEXT - tokens) * CHARS_PER_TOKEN


def cut_words(system: str, build, order: list[tuple[str, int]], ceiling: int) -> tuple[str, frozenset]:
    """A user prompt inside the ceiling where the words allow, `build(bare)` making it with the
    statements in `bare` left out: past it, statements go in `order`, from `cut_order`, until the two
    prompts fit or none is left. Answers with the prompt and the statements whose words went."""
    user = build(frozenset())
    over = len(system) + len(user) - ceiling
    if over <= 0:
        return user, frozenset()
    bare: list[str] = []
    rest = list(order)
    while rest and over > 0:
        key, size = rest.pop(0)
        bare.append(key)
        over -= size
    user = build(frozenset(bare))
    while rest and len(system) + len(user) > ceiling:
        bare.append(rest.pop(0)[0])
        user = build(frozenset(bare))
    return user, frozenset(bare)


def gets_cut_line(n: int) -> str:
    """What the card's line and the answer say when the words of some statements went for room."""
    return i18n.t("themes_ai.room.words", n=n, count=_count_said(n))


def gets_units(study: list[dict], skip=frozenset()) -> tuple[list[str], dict]:
    """The PETs and sub-themes a GETs answer may place, by key, each an item of its own, and each
    sub-theme's PET. One in `skip` is not an item, and its sub-themes not in it still are."""
    units, parent = [], {}

    def walk(pet: dict, up: str | None) -> None:
        if up:
            parent[pet["key"]] = up
        if pet["key"] not in skip:
            units.append(pet["key"])
        for sub in pet.get("subs") or []:
            walk(sub, pet["key"] if up is None else parent.get(up, up))

    for case in study:
        for pet in case.get("pets") or []:
            walk(pet, None)
    return units, parent


def parse_gets(text: str, units, parents: dict | None = None, truncated: bool = False, cap: int | None = None,
               one_per_pet: bool = True) -> dict:
    """A GETs grouping read strictly against the PETs and sub-themes that were sent, as
    `parse_grouping` reads one of statements.

    Fences and chatter round the JSON are stripped. A key the study does not have is left out. With
    One GET per PET a PET named twice keeps its first place, and with it off a PET named under a
    second GET takes a second card there, `<key>/2`, and once more `<key>/3`, while one named twice
    under the same GET keeps the first. A PET's sub-theme is an item of its own, a card apart from
    its PET (item 193), so it stands under any GET, the one its PET sits under or another, and the
    same rules hold for it. A blank label is Untitled, a nest deeper than one level folds into the
    sub-theme above it, a sub-theme with no members goes, and so does a GET with neither. `left_out`
    keeps each PET or sub-theme left out of every GET with its reason, once each, one placed or not
    the study's left out of it. `placed` counts the items placed, `subs` the sub-themes among them,
    by `parents`, and `left` those placed nowhere, which stand in Not placed. With `cap`, an answer
    of more GETs than one past it is refused whole. One that places nothing is one line, as is one
    that is not JSON, and one cut off at its length limit says so."""
    known = set(units)
    parents = parents or {}
    data = _load(text)
    reason, thrown_raw = "", []
    if isinstance(data, dict):
        reason = clean_reason(data.get("reason")) if isinstance(data.get("reason"), str) else ""
        thrown_raw = [x for k in ("left_out", "not_placed", "discarded") if isinstance(data.get(k), list) for x in data[k]]
        data = next((data[k] for k in ("gets", "groups", "themes") if isinstance(data.get(k), list)), None)
    if not isinstance(data, list):
        return {"error": ai_mod.TOO_LONG if truncated else ai_mod.NOT_JSON}
    placed_in: dict[str, list[int]] = {}
    unknown: list[str] = []
    repeated = 0
    tops: list[dict] = []

    def take(members, at: int) -> list[str]:
        nonlocal repeated
        out = []
        for m in members:
            key = one_line(m)
            if key not in known:
                if key not in unknown:
                    unknown.append(key)
                continue
            held = placed_in.setdefault(key, [])
            if at in held or (held and one_per_pet):
                repeated += 1
                continue
            held.append(at)
            out.append(key if len(held) == 1 else f"{key}/{len(held)}")
        return out

    for at, g in enumerate(x for x in data if isinstance(x, dict)):
        label = clean_label(g.get("label") or g.get("name") or g.get("title")) or UNTITLED
        members = take(g.get("members") if isinstance(g.get("members"), list) else [], at)
        subs = []
        for s in _children(g):
            if not isinstance(s, dict):
                continue
            inner = take(_flat(s), at)
            if inner:
                subs.append({"label": clean_label(s.get("label") or s.get("name") or s.get("title")) or UNTITLED,
                             "members": inner})
        tops.append({"label": label, "members": members, "groups": subs, "at": at})

    groups = [{"label": t["label"], "members": t["members"], "groups": t["groups"]}
              for t in tops if t["members"] or t["groups"]]
    seen = {k for k, at in placed_in.items() if at}
    if not seen:
        return {"error": ai_mod.TOO_LONG if truncated else _w("PLACED_NO_PETS")}
    if cap is not None and len(groups) > clean_cap(cap) + 1:
        return {"error": _w("TOO_MANY_GETS", n=len(groups), cap=clean_cap(cap))}
    left_out, out_keys = [], set()
    for item in thrown_raw:
        key, why = (item.get("key"), item.get("reason")) if isinstance(item, dict) else (item, "")
        key = one_line(key)
        if key not in known:
            if key and key not in unknown:
                unknown.append(key)
        elif key in seen or key in out_keys:
            repeated += 1
        else:
            out_keys.add(key)
            left_out.append({"key": key, "reason": clean_reason(why)})
    return {"groups": groups, "placed": len(seen), "subs": sum(1 for k in seen if k in parents),
            "left": sum(1 for u in units if u not in seen), "left_out": left_out, "reason": reason,
            "unknown": len(unknown), "repeated": repeated}


def gets_ids(version: dict) -> dict:
    """A board laid out by `lay_out` with its labels numbered as the GETs screen numbers them, G1
    on, where `lay_out` numbers them as PETs, g1 on."""
    names = {g["id"]: "G" + g["id"][1:] for g in version.get("groups") or [] if re.match(r"^g\d+$", g["id"])}
    groups = [dict(g, id=names.get(g["id"], g["id"]), members=[names.get(m, m) for m in g["members"]])
              for g in version.get("groups") or []]
    picks = {names.get(k, k): v for k, v in (version.get("picks") or {}).items()}
    return dict(version, groups=groups, picks=picks)


def gets_group(study: list[dict], labels: list[dict] | None, question: str | None, hint: str, route: dict,
               transport=None, cap: int = CAP, minimum: int = 1, total: int = 1, one_per_pet: bool = True,
               skip=frozenset(), ceiling: int | None = None) -> dict:
    """One call for a grouping of every case's PETs into no more GETs than `cap` allows, read
    strictly, or one error line. `skip` is the PETs a board's bin holds, which are not sent. When the
    prompt passes the route's room the words of the lowest statements go first, never a title, and
    the answer counts them in `cut`."""
    units, parents = gets_units(study, skip)
    if not units:
        return {"error": _w("NO_PETS_TO_GROUP")}
    rules = guidance_items(GETS)
    if not rules:
        return {"error": _w("NO_GUIDANCE")}
    refused = _route_ready(route)
    if refused:
        return refused
    cap = clean_cap(cap)
    tokens, wait = group_room(route)
    system = gets_group_system(question, cap, minimum, total, one_per_pet, rules)
    user, bare = cut_words(system, lambda b: gets_group_user(study, labels, hint, b, skip), cut_order(study),
                           room_of(route, tokens) if ceiling is None else ceiling)
    answer = _ask(system, user, route, transport, tokens, wait)
    if "error" in answer:
        return answer
    result = parse_gets(answer["text"], units, parents, bool(answer.get("truncated")), cap, one_per_pet)
    if "error" not in result:
        result["cut"] = len(bare)
    return result


def gets_room_cut(study: list[dict], labels: list[dict] | None, question: str | None, route: dict,
                  cap: int = CAP, minimum: int = 1, total: int = 1, one_per_pet: bool = True,
                  skip=frozenset()) -> int:
    """How many statements' words a new AI board on GETs would leave out for room, with no hint, for
    the card's line before Make. Nothing is asked."""
    tokens, _wait = group_room(route)
    system = gets_group_system(question, cap, minimum, total, one_per_pet)
    _user, bare = cut_words(system, lambda b: gets_group_user(study, labels, "", b, skip), cut_order(study),
                            room_of(route, tokens))
    return len(bare)


def gets_note(model_name: str, made_from: str, hint: str, result: dict, when: datetime | None = None,
              cap: int | None = None, picked: tuple[int, int] | None = None) -> str:
    """A new AI board's note on GETs, one line, as the PETs one is said:

        Proposed by Haiku 4.5 from every case's PETs on 5 October 2026 at 19:02, up to 5 GETs. 4 GETs,
        9 PETs and 3 sub-themes placed, 2 not placed. Quotes picked for 7 of 9 rows.

    The sub-themes placed are said when there are any. With the words of some statements left out
    for room it says so, and the model's reason for one GET past his limit comes last."""
    when = when or datetime.now().astimezone()
    n = len(result.get("groups") or [])
    subs = result.get("subs", 0)
    placed = result.get("placed", 0) - subs
    head = made_head(model_name, made_from, hint, when)
    if cap is not None:
        head = i18n.t("themes_ai.note.up_to_gets", head=head, n=clean_cap(cap))
    held = [i18n.t("themes_ai.note.pets_n", n=placed)] + ([i18n.t("themes_ai.note.subs_n", n=subs)] if subs else [])
    said = i18n.t("themes_ai.note.gets_counts", head=head, gets=i18n.t("themes_ai.note.gets_n", n=n),
                  placed=formats.list_words(held), left=result.get("left", 0))
    if picked is not None and picked[1]:
        said += " " + i18n.t("themes_ai.note.rows_picked", picked=picked[0], n=picked[1])
    if result.get("cut"):
        said += " " + gets_cut_line(result["cut"])
    return said + reason_said(result)


# --------------------------------------------------- GETs: the key quote of each row

def gets_picks_user(targets: list[dict]) -> str:
    """The rows' picks prompt: each GET by its id and title, and under it each participant with
    material there, a row by its id with that participant's key quotes, each by its key and words."""
    blocks, done = [], set()
    for t in targets:
        lines = []
        if t["get"] not in done:
            done.add(t["get"])
            lines.append(f"GET {t['get']}: {titled(t['label'])}")
        lines.append(f"Row {t['id']}, {t['who']}:")
        lines += [f"- {q['key']} {th.quoted(q['text'])}" for q in t["quotes"]]
        blocks.append("\n".join(lines))
    return "\n\n".join(["The GETs on this board, each by its id and its title, and under each a row for every "
                        "participant with material there, each by its id with that participant's key quotes, "
                        "each by its key and its words.", *blocks, "Pick the quotes."])


def gets_pick_quotes(targets: list[dict], question: str | None, route: dict, transport=None) -> dict:
    """One call for the key quote of each row of `targets`, from `gets.row_targets`, read strictly,
    or one error line: by row id, one quote each. With no rows nothing is asked."""
    if not targets:
        return {"picks": {}}
    refused = _route_ready(route)
    if refused:
        return refused
    local = ai_mod.is_local(route.get("provider"))
    thinking = not local and ai_mod.thinks(route.get("model") or ai_mod.MODEL)
    answer = _ask(_join([GETS_INTRO, gets_question_block(question), GETS_PICKS_TASK, GETS_PICKS_SHAPE]),
                  gets_picks_user(targets), route, transport,
                  ai_mod.THINKING_MAX_TOKENS if thinking else GETS_PICKS_MAX_TOKENS,
                  ai_mod.LOCAL_TIMEOUT if local else PICKS_THINKING_TIMEOUT if thinking else PICKS_TIMEOUT)
    if "error" in answer:
        return answer
    read = parse_picks(answer["text"], {t["id"]: {q["key"] for q in t["quotes"]} for t in targets},
                       bool(answer.get("truncated")))
    if "error" in read:
        return read
    return {"picks": {row: keys[:1] for row, keys in read["picks"].items()}}


# ------------------------------------------------------- GETs: a board set out

def gets_card_lines(c: dict, pad: str, bare=frozenset(), quotes: bool = False) -> list[str]:
    """One card under a GET, or not placed, as the review, a reply, a revise and the titles set it
    out: a PET or a sub-theme by its key, its participant and title, with its note and its
    statements, a statement by its key, its participant, sheet, timecode and words, and with
    `quotes` the key quotes it carries by their keys, for a pick. The reason an AI left it out
    follows when there is one."""
    if c["kind"] in ("pet", "sub"):
        out = [f"{pad}- {'PET' if c['kind'] == 'pet' else 'Sub-theme'} {c['key']} ({c['who']}): {titled(c.get('title'))}"
               + (", no longer in their PETs" if c.get("gone") else "")]
        if one_line(c.get("note")):
            out.append(f"{pad}  {NOTE_NAMES} {one_line(c.get('note'))}")
        cut = 0
        for s in c.get("statements") or []:
            if s["key"] in bare:
                cut += 1
                continue
            out.append(f"{pad}    - ({where_of(s)}) {_said(s)}")
        if cut:
            out.append(f"{pad}    - the words of {_count(cut)} {'statement' if cut == 1 else 'statements'} more, left out for room")
    else:
        out = [f"{pad}- Statement {c['key']} ({c['who']}, {where_of(c)}) {_said(c)}"]
    if quotes:
        out += [f"{pad}    quote {q['key']} {th.quoted(one_line(q.get('text')))}" for q in c.get("quotes") or []]
    if one_line(c.get("reason")):
        out.append(f"{pad}  Left out with the reason: {one_line(c.get('reason'))}")
    return out


def gets_get_lines(g: dict, total: int, minimum: int, depth: int = 0, bare=frozenset(), quotes: bool = False) -> list[str]:
    """One GET as the review, a reply and a revise set it out: its id, title and count against his
    minimum, his note on it, its cards in the order the canvas reads them, each row's key quote, the
    participants with nothing under it, and its sub-themes under it."""
    pad = "  " * depth
    under = ", under his minimum" if not depth and g.get("count", 0) < minimum else ""
    out = [f"{pad}{'Sub-theme' if depth else 'GET'} {g['id']}: {titled(g.get('label'))} "
           f"({g.get('count', 0)} of {total} {'participant' if total == 1 else 'participants'}{under})"]
    if one_line(g.get("note")):
        out.append(f"{pad}  Analyst's note: {one_line(g.get('note'))}")
    for c in g.get("cards") or []:
        out += gets_card_lines(c, pad + "  ", bare, quotes)
    for row in g.get("rows") or []:
        if row.get("quote"):
            out.append(f"{pad}  Quote for {row['who']}: "
                       f"{th.quoted(one_line(row['quote']['text']))}" + (f" (quote {row['case']}/{row['quote']['key']})" if quotes else ""))
    if g.get("missing"):
        out.append(f"{pad}  Nothing under it from: {', '.join(g['missing'])}.")
    for sub in g.get("themes") or []:
        out += gets_get_lines(sub, total, minimum, depth + 1, bare, quotes)
    return out


def gets_board_parts(board: dict, bare=frozenset(), quotes: bool = False) -> list[str]:
    """A GETs board, from `gets.ai_outline`, in three parts as the review and a reply send it: GET by
    GET, the cards not placed, and those in the bin with the reason given where there is one."""
    total, minimum = board.get("total", 0), board.get("minimum", 0)
    gets_ = board.get("themes") or []
    parts = ["The GETs board, GET by GET in the order the canvas reads them, top to bottom and left to right. "
             "Each GET has its id, its title and how many participants it holds, and under it each "
             "participant's PETs, sub-themes and statements by their keys, in the order the canvas reads "
             "them, higher meaning a better example.\n"
             + ("\n".join(line for g in gets_ for line in gets_get_lines(g, total, minimum, 0, bare, quotes))
                if gets_ else "There are no GETs yet.")]
    left = board.get("unplaced") or []
    parts.append("Not placed under any GET:\n" + "\n".join(line for c in left for line in gets_card_lines(c, "", bare, quotes))
                 if left else "Every card on the board is placed under a GET.")
    thrown = board.get("discarded") or []
    parts.append("In the bin, with the reason given where there is one:\n"
                 + "\n".join(line for c in thrown for line in gets_card_lines(c, "", bare)) if thrown else "Nothing is in the bin.")
    return parts


def gets_board_keys(board: dict) -> set[str]:
    """Everything on a GETs board a question can be about: every GET's id at any depth and every
    card's key, placed, not placed or in the bin."""
    out: set[str] = set()

    def walk(g: dict) -> None:
        out.add(g["id"])
        out.update(c["key"] for c in g.get("cards") or [])
        for sub in g.get("themes") or []:
            walk(sub)

    for g in board.get("themes") or []:
        walk(g)
    out.update(c["key"] for c in (board.get("unplaced") or []) + (board.get("discarded") or []))
    return out


def board_order(board: dict) -> list[tuple[str, int]]:
    """A GETs board's statements in the order their words go for room, as `cut_order` orders a
    study's: the lowest statement of every card first."""
    cards = []

    def walk(g: dict) -> None:
        cards.extend(g.get("cards") or [])
        for sub in g.get("themes") or []:
            walk(sub)

    for g in board.get("themes") or []:
        walk(g)
    cards += board.get("unplaced") or []
    return cut_order([{"pets": [{"key": c["key"], "statements": c.get("statements") or [], "subs": []}
                                for c in cards if c["kind"] in ("pet", "sub")]}])


def gets_review_system(question: str | None, rules=None, questions=None, notes: bool = False,
                       asked: bool = False) -> str:
    """A GETs review's system prompt: the rules for a GET from section 5, the questions a reviewer asks
    of a GETs board from section 6, the task, and the shape of the answer, with what an analyst's
    note is when a GET carries one and the earlier questions' line when there are some."""
    rules = guidance_items(GETS) if rules is None else rules
    questions = guidance_items(GETS_QUESTIONS) if questions is None else questions
    return _join([GETS_REVIEW_INTRO, gets_question_block(question), gets_guidance(rules),
                  "The questions a reviewer asks of a GETs board:\n" + numbered(questions),
                  GETS_REVIEW_TASK, NOTES_GETS if notes else None, ASKED_REVIEW if asked else None, GETS_REVIEW_SHAPE])


def gets_any_note(board: dict) -> bool:
    return any_note([{"note": g.get("note"), "groups": g.get("themes") or []} for g in board.get("themes") or []])


def gets_review(board: dict, question: str | None, route: dict, transport=None, asked=None,
                ceiling: int | None = None) -> dict:
    """One call for between one and three questions of a GETs board, from `gets.ai_outline`, read
    strictly against what is on it, or one error line. Nothing is written."""
    if not board.get("themes"):
        return {"error": _w("NOTHING_TO_REVIEW_GETS")}
    rules, questions = guidance_items(GETS), guidance_items(GETS_QUESTIONS)
    if not rules or not questions:
        return {"error": _w("NO_GUIDANCE")}
    refused = _route_ready(route)
    if refused:
        return refused
    asked = asked or []
    tokens, wait = group_room(route)
    system = gets_review_system(question, rules, questions, gets_any_note(board), bool(asked))
    user, _bare = cut_words(system, lambda b: review_user(board, asked, gets_board_parts(board, b)), board_order(board),
                            room_of(route, tokens) if ceiling is None else ceiling)
    answer = _ask(system, user, route, transport, tokens, wait)
    if "error" in answer:
        return answer
    return parse_review(answer["text"], gets_board_keys(board), bool(answer.get("truncated")), [n for n, _ in rules],
                        [a["question"] for a in asked])


def gets_reply(board: dict, item: dict | None, words: str, question: str | None, route: dict,
               transport=None, ceiling: int | None = None) -> dict:
    """One call for a short answer to his words on one question of a GETs review, read strictly, or
    one error line. Nothing is written."""
    if not one_line(words):
        return {"error": _w("NO_REPLY")}
    if not item or not one_line(item.get("question")):
        return {"error": _w("NO_SUCH_QUESTION")}
    rules = guidance_items(GETS)
    if not rules:
        return {"error": _w("NO_GUIDANCE")}
    refused = _route_ready(route)
    if refused:
        return refused
    local = ai_mod.is_local(route.get("provider"))
    thinking = not local and ai_mod.thinks(route.get("model") or ai_mod.MODEL)
    tokens = ai_mod.THINKING_MAX_TOKENS if thinking else REPLY_MAX_TOKENS
    system = _join([GETS_REVIEW_INTRO, gets_question_block(question), gets_guidance(rules), GETS_REPLY_TASK,
                    NOTES_GETS if gets_any_note(board) else None, REPLY_SHAPE])
    keys = gets_board_keys(board)
    user, _bare = cut_words(system, lambda b: reply_user(board, item, words, gets_board_parts(board, b), keys),
                            board_order(board), room_of(route, tokens) if ceiling is None else ceiling)
    answer = _ask(system, user, route, transport, tokens, group_room(route)[1])
    if "error" in answer:
        return answer
    return parse_reply(answer["text"], bool(answer.get("truncated")))


# ------------------------------------------------------- GETs: three titles

def gets_names_target(board: dict, gid: str) -> dict | None:
    """The GET or sub-theme a title is asked for, from `gets.ai_outline`, with `inside`, the GET a
    sub-theme sits in, and `others`, the titles of every other GET and sub-theme on the board once
    each, Untitled left out. None when the board holds no such label."""
    found, inside, labels = None, "", []

    def walk(g: dict, up: dict | None) -> None:
        nonlocal found, inside
        labels.append(g)
        if g["id"] == gid:
            found, inside = g, (up["label"] or UNTITLED) if up else ""
        for sub in g.get("themes") or []:
            walk(sub, g)

    for g in board.get("themes") or []:
        walk(g, None)
    if found is None:
        return None
    own = set()

    def mine(g: dict) -> None:
        own.add(g["id"])
        for sub in g.get("themes") or []:
            mine(sub)

    mine(found)
    others = []
    for g in labels:
        label = one_line(g.get("label"))
        if g["id"] not in own and label and label != UNTITLED and label not in others:
            others.append(label)
    return dict(found, inside=inside, others=others, total=board.get("total", 0), minimum=board.get("minimum", 0),
                study=board.get("study") or [])


def gets_names_system(question: str | None, rules=None, prose: str | None = None) -> str:
    """The GET titles' system prompt: the introduction, the research question, what a GET is from
    section 5, the task, rules 5 to 8 of section 5, recurrence, negative trajectories, the title and
    no cause, the format line and the shape."""
    rules = guidance_items(GETS) if rules is None else rules
    prose = guidance_prose(GETS) if prose is None else prose
    what = "\n\n".join(p for p in (prose or "").split("\n\n") if not re.match(r"^\d+\.\s", p)).strip() or GET
    title = [(n, text) for n, text in rules if n in GETS_TITLE_RULES]
    task = " ".join([
        "Offer three titles for the GET he has gathered, each a different angle on what its participants",
        "share and where they part, each grounded in the PETs, sub-themes and statements under it and",
        "close to the participants' own words, and none repeating the title of another GET on the board.",
    ])
    said = "Every title follows these rules from the IPA guidance he works by:\n" + numbered(title) if title else None
    return _join([GETS_INTRO, gets_question_block(question), what, task, said, FORMAT, NAMES_SHAPE])


def gets_names_user(target: dict, bare=frozenset()) -> str:
    """The GET titles' user prompt: the GET, his note on it, its count against his minimum, what
    each participant has under it, a participant with nothing there named so, its sub-themes, the
    other GETs' titles and the closing line."""
    head = f"{'Sub-theme' if target.get('inside') else 'GET'}: {titled(target.get('label'))}"
    if target.get("inside"):
        head += f", inside the GET {titled(target['inside'])}"
    lines = [head]
    if one_line(target.get("note")):
        lines.append(f"{NOTE_NAMES} {one_line(target.get('note'))}")
    total, minimum = target.get("total", 0), target.get("minimum", 0)
    lines.append(f"It holds material from {target.get('count', 0)} of the {total} "
                 f"{'participant' if total == 1 else 'participants'}, and his minimum is {minimum}.")
    for c in target.get("cards") or []:
        lines += gets_card_lines(c, "", bare)
    if target.get("missing"):
        lines.append(f"Nothing under it from: {', '.join(target['missing'])}.")
    for sub in target.get("themes") or []:
        lines += gets_get_lines(sub, total, minimum, 1, bare)
    parts = ["The GET he asks titles for, with what each participant has under it, in the order the canvas reads "
             "it, higher meaning a better example.\n" + "\n".join(lines)]
    if bare:
        parts.append(f"The words of {_count(len(bare))} {'statement' if len(bare) == 1 else 'statements'} are left "
                     "out here for room, which says nothing about them.")
    if target.get("others"):
        parts.append("The other GETs on the board, so the titles sit beside them:\n" + ai_mod.bullets(target["others"]))
    parts.append("Three titles, each from a different angle.")
    return "\n\n".join(parts)


def gets_names(target: dict | None, question: str | None, route: dict, transport=None,
               ceiling: int | None = None) -> dict:
    """One call for three titles for a GET or a sub-theme, from `gets_names_target`, or one error
    line, with `said` when the words of some statements went for room. Nothing is written."""
    if target is None:
        return {"error": _w("NO_SUCH_GET")}
    if not target.get("cards") and not target.get("themes"):
        return {"error": _w("NOTHING_UNDER")}
    rules = guidance_items(GETS)
    if not any(n in GETS_TITLE_RULES for n, _ in rules):
        return {"error": _w("NO_GUIDANCE")}
    refused = _route_ready(route)
    if refused:
        return refused
    system = gets_names_system(question, rules)
    user, bare = cut_words(system, lambda b: gets_names_user(target, b),
                           board_order({"themes": [target]}),
                           (room_of(route, NAMES_MAX_TOKENS) if ceiling is None else ceiling))
    return room_said(_ask_names(system, user, route, transport), len(bare), gets_cut_line)


# ------------------------------------------------------------ GETs: revise

def gets_revise_system(question: str | None, rules=None) -> str:
    """A GETs revise's system prompt: the introduction, the research question, the GETs section of
    the guidance file, the task with its voice, and the shape of the answer, the operations named."""
    return _join([GETS_REVISE_INTRO, gets_question_block(question), gets_guidance(rules), GETS_REVISE_TASK,
                  FORMAT, GETS_REVISE_SHAPE])


def gets_revise_user(board: dict, thread, words: str, bare=frozenset(), dropped: int = 0) -> str:
    """A GETs revise's user prompt: the board as it stands, GET by GET with every card's key quotes by
    their keys, the cards not placed, the requests so far on this board with their answers, and his
    request. Participant notes, sticky notes, row notes and the bin are never in it. The words of a
    statement in `bare` go, and the oldest `dropped` lines of the thread, each said in a line."""
    parts = gets_board_parts(board, bare, quotes=True)[:2]
    if bare:
        parts.append(f"The words of {_count(len(bare))} {'statement' if len(bare) == 1 else 'statements'} are left "
                     "out here for room, which says nothing about them.")
    said = thread_part(thread, dropped)
    if said:
        parts.append(said)
    parts.append(f"He asks now: {one_line(words)}")
    parts.append("Change the board.")
    return "\n\n".join(parts)


def gets_revise(board: dict, start: dict, thread, words: str, question: str | None, route: dict,
                transport=None, ceiling: int | None = None) -> dict:
    """One call for his request on a GETs board: the board from `gets.ai_outline`, the plain board
    `gets.revise_start` makes for the applier, its thread so far, the research question, the GETs
    guidance and his words, read strictly through `revise_ops`, or one error line. When the prompt
    passes the route's room the words of the lowest statements go first, as a new AI board's do, then
    the thread's oldest lines, and the answer's `said` ends by saying so, as a PETs revise's does.
    Nothing is written."""
    if not one_line(words):
        return {"error": _w("NO_REQUEST")}
    rules = guidance_items(GETS)
    if not rules:
        return {"error": _w("NO_GUIDANCE")}
    refused = _route_ready(route)
    if refused:
        return refused
    local = ai_mod.is_local(route.get("provider"))
    thinking = not local and ai_mod.thinks(route.get("model") or ai_mod.MODEL)
    tokens = ai_mod.THINKING_MAX_TOKENS if thinking else REVISE_MAX_TOKENS
    system = gets_revise_system(question, rules)
    ceiling = room_of(route, tokens) if ceiling is None else ceiling
    said = th.thread_of(thread)
    user, bare = cut_words(system, lambda b: gets_revise_user(board, said, words, b), board_order(board), ceiling)
    user, dropped = cut_thread(system, lambda d: gets_revise_user(board, said, words, bare, d), len(said), ceiling)
    answer = _ask(system, user, route, transport, tokens, group_room(route)[1])
    if "error" in answer:
        return answer
    return room_said(parse_revise(answer["text"], start, bool(answer.get("truncated"))), len(bare), gets_cut_line,
                     dropped)


def section_heading(section: int, path: Path | None = None) -> str:
    """A section's heading in the guidance file, without its number, or nothing."""
    try:
        text = Path(path or GUIDANCE).read_text(encoding="utf-8")
    except OSError:
        return ""
    found = re.search(rf"^##\s+{int(section)}\.\s+(.*\S)\s*$", text, re.M)
    return found.group(1) if found else ""


def gets_guidance_lines(path: Path | None = None) -> list[dict]:
    """The Guidance tab on the GETs screen: the GETs sections of the guidance file the AI reads, each
    `{"heading", "lines"}` as `/api/themes` carries the PETs tab's, what a GET is and its rules, then
    the questions a reviewer asks of a GETs board. Read afresh on every open, and a file without
    them gives none."""
    out = []
    prose = guidance_prose(GETS, path)
    paras = [p for p in prose.split("\n\n") if p.strip() and not re.match(r"^\d+\.\s", p)] if prose else []
    rules = [text for _, text in guidance_items(GETS, path)]
    if paras or rules:
        out.append({"heading": section_heading(GETS, path) or "Group experiential themes", "lines": paras + rules})
    questions = [text for _, text in guidance_items(GETS_QUESTIONS, path)]
    if questions:
        out.append({"heading": section_heading(GETS_QUESTIONS, path) or "Questions a reviewer asks of a GETs board",
                    "lines": questions})
    return out
