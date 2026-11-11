#!/usr/bin/env python3
"""The AI's titles on the PETs and GETs screens, off until the switch in Settings is on, and the plain
pieces a board made or changed through the API is built with.

A title suggestion is one call through `ai_suggest.complete`, so it goes out with the provider, the model
and the key a suggestion on the turn screen uses, and carries the project's research question. Its system
prompt is its own, written here. The IPA guidance it carries is read from `pet_guidance.md` beside this
file on every call: section 1, what a theme is, and the title's rules of section 3, the rules for a theme.
Editing that file changes what the AI is told.

A title suggestion sends one theme as the workbook and the board hold it, its title and its note when
it has them, each statement in the order the canvas reads it with its timecode and every key quote
of its turn, the picked ones marked, its sub-themes the same way, and the other labels on the
canvas. It asks for three titles, each from a different angle, with what a theme is and what an
experiential statement is, under the rules for a title, its register, negative material and
recurrence. A page from before it sends the statements as bare text, which still builds a prompt.
The GETs screen asks the same one layer up, at the end of this file, with section 4 of the guidance
file, what a GET is and its rules, which the GETs screen's Guidance tab shows with section 5.

The rest asks no model. `lay_out` sets a structure out on the canvas as a board of round blobs, the
command line's board make and the demo's boards, and `revise_ops` reads the operations of a change
strictly against a plain board, its labels, the keys on it and the quotes of their rows, applying each
in order to a copy, the command line's board apply and gets apply: one that names a key, a label or a
quote that is not there is refused. The board and the applier are plain dicts with no PETs in their
names, so a board of another kind can pass through them.

Nothing here reads a key, opens a workbook or writes a file. The transport is a parameter, the shape
`complete` takes, so the tests run with no key, no Ollama and no network.
"""
from __future__ import annotations

import json
import re
from pathlib import Path

import ai_suggest as ai_mod
import boot
import formats
import i18n
import themes as th

# The words the person reads, the refusals and the lines a change through the API writes, from the catalogue
# (apps/idiograph/static/i18n/en/themes_ai.json, i18nleft, 1 November 2026), each read in the run's language
# when said: inside this module through `_w`, from others as the module's names (`__getattr__`). The prompts
# stay English, the model's own language here.
SAID = {
    "OFF": lambda **v: i18n.t("themes_ai.off", v),
    "NO_TITLES": lambda **v: i18n.t("themes_ai.no_titles", v),
    "NOTHING_TO_NAME": lambda **v: i18n.t("themes_ai.nothing_to_name", v),
    "NO_SUCH_PET": lambda **v: i18n.t("themes_ai.no_such_pet", v),
    "NO_GUIDANCE": lambda **v: i18n.t("themes_ai.no_guidance", v),
    "FROM_ALL": lambda **v: i18n.t("themes_ai.from_all", v),
    "NOTHING_CHANGED": lambda **v: i18n.t("themes_ai.nothing_changed", v),
    "UNKNOWN_STATEMENT": lambda **v: i18n.t("themes_ai.unknown_statement", v),
    "UNKNOWN_LABEL": lambda **v: i18n.t("themes_ai.unknown_label", v),
    "UNKNOWN_QUOTE": lambda **v: i18n.t("themes_ai.unknown_quote", v),
    "NOT_DONE": lambda **v: i18n.t("themes_ai.not_done", v),
    "INSIDE_ITSELF": lambda **v: i18n.t("themes_ai.inside_itself", v),
    "UNREADABLE": lambda **v: i18n.t("themes_ai.unreadable", v),
    "NO_SUCH_GET": lambda **v: i18n.t("themes_ai.no_such_get", v),
    "NOTHING_UNDER": lambda **v: i18n.t("themes_ai.nothing_under", v),
    # the family's, read where it is said rather than frozen when this module was first imported
    "NOT_JSON": lambda **v: ai_mod.NOT_JSON,
    # the revision kept before a change, "Before: " and his request, its head alone for the command line's cut
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

# The guidance a title's prompt carries, read afresh on every call: the prose of `## 1.`, what a
# theme is, and rules 5, 6, 8 and 11 of `## 3.`: the title, its register, negative and unresolved
# material as valid, and recurrence as grounding.
GUIDANCE = boot.resource("pet_guidance.md")
WHAT_A_THEME = 1
RULES = 3
TITLE_RULES = (5, 6, 8, 11)

NAMES_MAX_TOKENS = 800
NAMES_TIMEOUT = 30
NAMES_THINKING_TIMEOUT = 120
# The most quotes a pick names through `revise_ops` on a board that sets no `pick_max` of its own. A
# pick by hand, and board apply's on PETs, takes every quote he picks.
PICKS_MAX = 2
# A title's prompt grows with the key quotes under each statement. It keeps within the room a
# local model's context leaves once 12,000 tokens are kept for the answer, at about four characters
# to a token. A theme past it loses the quotes of the statements lowest on the canvas first, and the
# answer says so in one line.
ANSWER_ROOM = 12000
CHARS_PER_TOKEN = 4
PROMPT_CEILING = (ai_mod.LOCAL_CONTEXT - ANSWER_ROOM) * CHARS_PER_TOKEN

LABEL_LIMIT = 160
NAMES = 3

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


NAMES_SHAPE = "\n".join([
    "Answer with strict JSON and nothing else, in this shape:",
    '{"names": ["...", "...", "..."]}',
])


NOTE_NAMES = "His note on this theme, his own reasoning for it:"


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


def names_system(question: str | None, rules=None, theme: str | None = None) -> str:
    """The titles' system prompt, in this order: the introduction, the research question, what a
    theme is from section 1 of the guidance file, what an experiential statement is, the task, then
    rules 5, 6, 8 and 11 of section 3, the title, its register, negative and unresolved material as
    valid and recurrence as grounding, the format line and the shape. A file without section 1
    sends one sentence on a theme in its place."""
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


def one_line(text) -> str:
    return " ".join(str(text or "").split())


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
    """One theme as the titles prompt sets it out: its
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
    """What a title's prompt says of the quotes it leaves out for room."""
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


def room_said(result: dict, bare: int, line) -> dict:
    """An answer from a prompt cut for room, its `said` saying what went, `line(bare)` for the
    quotes or the words of `bare` statements, with `trimmed` counting them. An error, or an answer
    from a prompt sent whole, is as it was."""
    if "error" in result or not bare:
        return result
    return dict(result, said=line(bare), trimmed=bare)


def _said(item: dict) -> str:
    return " ".join(str(item.get("text") or "").split())


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


# ------------------------------------------------------------------- layout

# The canvas's own measures come from `themes`, the ones the first pile is laid with, so a
# board laid out here and a pile agree on how tall a card is and how wide a label runs, and every space here
# is the one margin a card always keeps: between two cards, and between a theme's own cards and a
# sub-theme's frame. Two themes' frames stand two margins apart, and the cards left out four
# margins to the side, so the themes still read as apart at the zoom that fits them all.
CARD_W = th.CARD_W
INNER_GAP = th.MARGIN        # between two cards inside a theme
PART_GAP = th.MARGIN         # between the parts of a theme: its own cards and each sub-theme's frame
THEME_GAP = 2 * th.MARGIN    # between two themes' frames on the plane
PILE_SIDE = 4 * th.MARGIN    # between the themes and the pile of cards left out


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


def lay_out(groups: list[dict], cards: list[dict], discarded: list[str], size=None) -> dict:
    """A structure as a board of the canvas.

    Each theme is a round blob: its label at the top and its cards packed under it in rows that fill
    a circle, each sub-theme a blob of its own inside its theme's frame, and each group a sub-theme
    carries under `groups` a blob inside the sub-theme's. The themes are set out on
    the plane in the order given, row by row inside a circle, with clear gaps between
    their frames. The cards left out lie in a pile of their own to the right, in transcript order,
    the missing ones last. A discarded card stays discarded, where it was: nothing laid out here puts
    a card in the bin. The labels are numbered g1 on, the themes first, then each sub-theme followed by its
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
        tall = lambda k: size(k, texts[k])
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


# ------------------------------------------------------ the quotes that carry each PET

def _row_of(key: str):
    sheet, row, _ = th.split_card_key(key)
    return None if row is None else th.row_key(sheet, row)


def quoted_of(picks: dict, quotes: dict) -> dict:
    """The words of every quote the picks name, as the workbook holds them, which a save by hand
    keeps beside the picks so each can follow its words."""
    words = {q["key"]: q["text"] for row in (quotes or {}).values() for q in row.get("quotes") or []}
    return {k: words[k] for chosen in picks.values() for k in chosen if k in words}


# ------------------------------------------------------------------ the applier
#
# A change to a board by the operations it names, never a whole board, so everything it does not
# name keeps its place: the command line's board apply and gets apply, and so an agent's. The board
# here is a plain dict, `revise_start`'s: `items`, the keys on it an operation may name, `groups`,
# each label by its id with its title, its note and its members, `picks` by label, and `quotes`, the
# quote keys of each row. Nothing in it is particular to PETs. A board of another kind may carry
# three keys more: `prefix`, the letter its labels' ids start with, `card_quotes`, the quote keys
# each card carries, and `pick_max`, the quotes a pick may name. A board with no `pick_max` is held
# to `PICKS_MAX`. Board apply's carries None, the app's own rule for a pick by hand, every quote
# named, each once (see `themes.picks_kept`).

REVISE_OPS = ("retitle", "note", "move", "make", "merge", "apart", "pick")
DESCRIBE = "describe"   # a label's description, his own words, through board apply and gets apply alone
NOTE_LIMIT = 2000
REVISE_LINE = 80     # the request in a revision's name, cut at a word to one short line

# a small number in words, for the prompts
COUNTS = ("no", "one", "two", "three", "four", "five", "six", "seven", "eight", "nine", "ten")


def revise_start(read: dict, version: dict) -> dict:
    """The plain board the applier works on, from the workbook as `themes.read_cards`
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
    """An operation left out, with why."""


def clean_note(text) -> str:
    """A note as a change writes it: one paragraph, no em dash, no semicolon, not past its length."""
    words = " ".join(str(text or "").split())
    return re.sub(r"\s*\u2014\s*", ", ", words).replace(";", ",")[:NOTE_LIMIT].strip()


def revise_ops(board: dict, raw) -> tuple[dict, list[dict], list[str], dict]:
    """The operations of a change read strictly and applied in order to a copy of `board`, from
    `revise_start`. Each is applied whole or refused whole: one that names a statement, a label or a
    quote that is not there, that would put a label inside itself, that cannot be read, or that asks
    for something the applier does not do, the bin or a statement's words among them, is refused with
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
            # a description is his own words, written by an agent only on his word (Adam, 21 October)
            if kind not in REVISE_OPS and kind != DESCRIBE:
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


def change_line(applied: list[dict], before: dict) -> str:
    """What the operations applied did, said plainly from the board before them. Four at most, then how many more. A board's `unit` names what its cards are,
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


def _structure(board: dict) -> dict:
    """What a change can do to a board, to tell whether it did anything."""
    return {"groups": board.get("groups") or [], "picks": {g: k for g, k in (board.get("picks") or {}).items() if k}}


def revision_name(words: str) -> str:
    """The revision kept before a change, "Before: " and his request on one line, cut at a word
    past REVISE_LINE characters with an ellipsis."""
    said = one_line(words)
    if len(said) > REVISE_LINE:
        said = said[:REVISE_LINE].rsplit(" ", 1)[0].rstrip(",.:") + "…"
    return i18n.t("themes_ai.revision_before", request=said)


# ---------------------------------------------------------------------- GETs
#
# Three titles for a GET, one layer up on the GETs screen, through the same route and the same call.
# What goes is built by `gets` from the GETs file as plain dicts, each card by its participant's
# pseudonym, a PET with its note, its sub-themes and their statements, and never a participant note,
# a sticky note or a row's note. The guidance is section 4 of `pet_guidance.md`, what a GET is and
# its rules. Section 5, the questions a reviewer asks of a GETs board, is the Guidance tab's.

GETS = 4
GETS_QUESTIONS = 5
GETS_TITLE_RULES = (5, 6, 7, 8)
# a provider's own room, past which the PETs words of a GETs prompt go, statement by statement
ANTHROPIC_CONTEXT = 200000

GETS_INTRO = ("You help a researcher doing Interpretative Phenomenological Analysis (IPA, Smith, Flowers "
              "and Larkin) at the step after the personal experiential themes, where every participant's "
              "PETs are looked across for what they share and where they part, and grouped into group "
              "experiential themes, GETs. He does that work himself. You offer a first try, which he "
              "keeps, changes or throws away.")


GET = ("A group experiential theme gathers the PETs, sub-themes and statements of several participants "
       "that share an experiential meaning, and shows where they part as well as what they share.")


def gets_question_block(question: str | None) -> str:
    """The project's research question as the GETs prompts say it, or nothing when there is none."""
    asked = one_line(question)
    if not asked:
        return ""
    if asked[-1] not in ".?!":
        asked += "."
    return (f"The study asks: {asked} Every GET answers that question across the participants: what "
            "matters to them, and how it matters in each one's own way.")


def where_of(item: dict) -> str:
    return ", ".join(p for p in (item.get("sheet"), item.get("time")) if p)


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


def gets_ids(version: dict) -> dict:
    """A board laid out by `lay_out` with its labels numbered as the GETs screen numbers them, G1
    on, where `lay_out` numbers them as PETs, g1 on."""
    names = {g["id"]: "G" + g["id"][1:] for g in version.get("groups") or [] if re.match(r"^g\d+$", g["id"])}
    groups = [dict(g, id=names.get(g["id"], g["id"]), members=[names.get(m, m) for m in g["members"]])
              for g in version.get("groups") or []]
    picks = {names.get(k, k): v for k, v in (version.get("picks") or {}).items()}
    return dict(version, groups=groups, picks=picks)


# ------------------------------------------------------- GETs: a board set out

def gets_card_lines(c: dict, pad: str, bare=frozenset()) -> list[str]:
    """One card under a GET as the titles set it out: a PET or a sub-theme by its key, its participant
    and title, with its note and its statements, a statement by its key, its participant, sheet,
    timecode and words."""
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
    return out


def gets_get_lines(g: dict, total: int, minimum: int, depth: int = 0, bare=frozenset()) -> list[str]:
    """One sub-theme of a GET as the titles set it out: its id, title and count against his
    minimum, his note on it, its cards in the order the canvas reads them, each row's key quote, the
    participants with nothing under it, and its sub-themes under it."""
    pad = "  " * depth
    under = ", under his minimum" if not depth and g.get("count", 0) < minimum else ""
    out = [f"{pad}{'Sub-theme' if depth else 'GET'} {g['id']}: {titled(g.get('label'))} "
           f"({g.get('count', 0)} of {total} {'participant' if total == 1 else 'participants'}{under})"]
    if one_line(g.get("note")):
        out.append(f"{pad}  Analyst's note: {one_line(g.get('note'))}")
    for c in g.get("cards") or []:
        out += gets_card_lines(c, pad + "  ", bare)
    for row in g.get("rows") or []:
        if row.get("quote"):
            out.append(f"{pad}  Quote for {row['who']}: {th.quoted(one_line(row['quote']['text']))}")
    if g.get("missing"):
        out.append(f"{pad}  Nothing under it from: {', '.join(g['missing'])}.")
    for sub in g.get("themes") or []:
        out += gets_get_lines(sub, total, minimum, depth + 1, bare)
    return out


def board_order(board: dict) -> list[tuple[str, int]]:
    """A GET's statements in the order their words go for room, as `cut_order` orders them: the
    lowest statement of every card first."""
    cards = []

    def walk(g: dict) -> None:
        cards.extend(g.get("cards") or [])
        for sub in g.get("themes") or []:
            walk(sub)

    for g in board.get("themes") or []:
        walk(g)
    return cut_order([{"pets": [{"key": c["key"], "statements": c.get("statements") or [], "subs": []}
                                for c in cards if c["kind"] in ("pet", "sub")]}])


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
    section 4, the task, rules 5 to 8 of section 4, recurrence, negative trajectories, the title and
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


# ------------------------------------------------------------ GETs: the Guidance tab

def section_heading(section: int, path: Path | None = None) -> str:
    """A section's heading in the guidance file, without its number, or nothing."""
    try:
        text = Path(path or GUIDANCE).read_text(encoding="utf-8")
    except OSError:
        return ""
    found = re.search(rf"^##\s+{int(section)}\.\s+(.*\S)\s*$", text, re.M)
    return found.group(1) if found else ""


def gets_guidance_lines(path: Path | None = None) -> list[dict]:
    """The Guidance tab on the GETs screen: the GETs sections of the guidance file the titles read, each
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
