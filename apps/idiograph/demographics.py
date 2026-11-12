#!/usr/bin/env python3
"""Participants' demographics, set per project (demobuild, 12 November 2026, Adam's option A of demodraw's
proposal, by dialog, "A, plus B's table").

A project keeps its own categories once, in its file, `idiograph-project.json`, under `demographics`, in his
order: each a name, a kind, `list` (a value to choose from a list, one each) or `words` (free words, up to WORDS_MAX
each), whether it shows as a pill on the rows, the pickers and Trajectories, `show`, and its values in order, each
with its colour, a place in the participants' palette (`trajectories.TAG_NAMES`), so Female reads the same colour
on every row. Each participant's values are kept in their own set under `participants` (`participants.py`), by the
category's name, a list's one word a string and free words a list, so Rename, History and a shared copy carry them
as they carry the label and the pen portrait:

    "demographics": [
      {"name": "Gender", "kind": "list", "show": true,
       "values": [{"word": "Female", "colour": 0}, {"word": "Male", "colour": 6}]},
      {"name": "Nationality", "kind": "words", "show": true, "export": false,
       "values": [{"word": "Spanish", "colour": 2}]}],
    "participants_table": "sum",
    "participants": {"P1 - Juno": {"label": "...", "values": {"Gender": "Female", "Nationality": ["Spanish"]}}}

A free word nobody has any more leaves its category at the next save (`tidy`). `export`, left out until he unticks
or ticks a category on the GETs print card, follows `show`: a category shown as a pill goes into the participants
table and the PETs' pen portrait line until he says otherwise. `participants_table`, `each` or `sum`, is how that
table carries them, a column each or a short table of counts, a thematic analysis project's first choice the sum.

Every change goes through `apply` (the categories and their values, `demographics apply`) or `set_values` (one
participant's, `participant set --value`), each checked first and refused whole, with nothing written, when one
part is wrong. Trajectories' tags from before (`placed[case]["tags"]`, their colours in its `tags` map) become each
participant's values in a Tags category of free words, each word keeping its colour (`settle`), the map itself kept
whole since LPETs' domains share it. Standard library, the Trajectories module's palette and the names list's
finder through the caller.
"""
from __future__ import annotations

import json
import re
import shutil
from pathlib import Path

import formats
import i18n
import trajectories as traj_mod
from workbook import WorkbookError

KEY = "demographics"
TABLE_KEY = "participants_table"
VALUES = "values"
TAGS = "Tags"
KINDS = ("list", "words")
HOWS = ("each", "sum")
NAME_MAX = 40
WORD_MAX = 40
WORDS_MAX = 12
CATS_MAX = 20
LIST_MAX = 40
COLOURS = traj_mod.TAG_NAMES
ARCHIVE_LABEL = "pre-demographics"
OPS = ("add", "rename", "kind", "show", "move", "remove", "export", "table", "value_add", "value_rename",
       "value_colour", "value_move", "value_remove", "value_to")
# the starting set Add category offers (the proposal's), each by its catalogue keys: its name, its kind and its values
STARTERS = (
    ("gender", "list", ("female", "male", "non_binary")),
    ("age_range", "list", ("age_18", "age_30", "age_40", "age_50", "age_60", "age_70")),
    ("nationality", "words", ()),
    ("first_language", "words", ()),
    ("occupation", "words", ()),
)


class People(dict):
    """Every participant's set by label, as `participants.view` reads them, with the project's categories, `cats`,
    and for an export how its participants table carries them, `table` (`{"how", "cats"}`), or None."""
    cats: list = []
    table: dict | None = None


def words(text) -> str:
    return " ".join(str(text or "").split())


def starters() -> list[dict]:
    """The starting set in the run's language: each category's name, kind and values."""
    words = {"gender": i18n.t("demographics.starter.gender"), "female": i18n.t("demographics.starter.female"),
             "male": i18n.t("demographics.starter.male"), "non_binary": i18n.t("demographics.starter.non_binary"),
             "age_range": i18n.t("demographics.starter.age_range"), "age_18": i18n.t("demographics.starter.age_18"),
             "age_30": i18n.t("demographics.starter.age_30"), "age_40": i18n.t("demographics.starter.age_40"),
             "age_50": i18n.t("demographics.starter.age_50"), "age_60": i18n.t("demographics.starter.age_60"),
             "age_70": i18n.t("demographics.starter.age_70"), "nationality": i18n.t("demographics.starter.nationality"),
             "first_language": i18n.t("demographics.starter.first_language"),
             "occupation": i18n.t("demographics.starter.occupation")}
    return [{"name": words[key], "kind": kind, "values": [words[v] for v in values]} for key, kind, values in STARTERS]


# ------------------------------------------------------------------ as the file keeps them

def colour_ok(n) -> bool:
    return isinstance(n, int) and not isinstance(n, bool) and 0 <= n < len(COLOURS)


def cat_kept(raw) -> dict | None:
    """One category as the file keeps it, None when it has no name."""
    if not isinstance(raw, dict):
        return None
    name = words(raw.get("name"))[:NAME_MAX]
    if not name:
        return None
    out = {"name": name, "kind": raw.get("kind") if raw.get("kind") in KINDS else "words",
           "show": raw.get("show") is not False, "values": []}
    seen = set()
    for v in raw.get("values") if isinstance(raw.get("values"), list) else []:
        v = {"word": v} if isinstance(v, str) else v
        if not isinstance(v, dict):
            continue
        word = words(v.get("word"))[:WORD_MAX]
        if word and word.lower() not in seen:
            seen.add(word.lower())
            out["values"].append({"word": word, "colour": v["colour"] if colour_ok(v.get("colour")) else None})
    if isinstance(raw.get("export"), bool):
        out["export"] = raw["export"]
    return out


def cats_of(project: dict | None) -> list[dict]:
    """The project's categories in his order, each name once in any case, a value with no colour given one."""
    out, seen = [], set()
    held = (project or {}).get(KEY) if isinstance(project, dict) else None
    for raw in held if isinstance(held, list) else []:
        cat = cat_kept(raw)
        if cat is not None and cat["name"].lower() not in seen and len(out) < CATS_MAX:
            seen.add(cat["name"].lower())
            out.append(cat)
    for cat in out:
        for v in cat["values"]:
            if v["colour"] is None:
                v["colour"] = fresh_colour(out)
    return out


def how_of(project: dict | None, method: str = "ipa") -> str:
    """How the participants table carries the categories: his choice, else one row each, a thematic analysis
    project's In sum."""
    said = (project or {}).get(TABLE_KEY) if isinstance(project, dict) else None
    return said if said in HOWS else ("sum" if method == "ta" else "each")


def values_kept(raw) -> dict:
    """A participant's values as the file keeps them, read loosely: a category's name and a word or a list of words,
    an empty one left out. `values_for` reads them against the categories."""
    out = {}
    for name, given in (raw.items() if isinstance(raw, dict) else ()):
        name = words(name)[:NAME_MAX]
        if not name:
            continue
        if isinstance(given, list):
            kept, seen = [], set()
            for w in given:
                w = words(w)[:WORD_MAX]
                if w and w.lower() not in seen:
                    seen.add(w.lower())
                    kept.append(w)
            if kept:
                out[name] = kept[:WORDS_MAX]
        elif words(given):
            out[name] = words(given)[:WORD_MAX]
    return out


def cat_named(cats: list[dict], name) -> dict | None:
    name = words(name).lower()
    return next((c for c in cats if c["name"].lower() == name), None)


def value_named(cat: dict, word) -> dict | None:
    word = words(word).lower()
    return next((v for v in cat["values"] if v["word"].lower() == word), None)


def given_words(held) -> list[str]:
    return [held] if isinstance(held, str) else list(held or [])


def values_for(raw, cats: list[dict]) -> dict:
    """A participant's values against the categories, in their order: a list's one value as the list spells it, a
    value the list lacks left out, free words as the category spells each it holds. A category gone is left out."""
    held = {k.lower(): v for k, v in values_kept(raw).items()}
    out = {}
    for cat in cats:
        mine = given_words(held.get(cat["name"].lower()))
        if cat["kind"] == "list":
            found = next((value_named(cat, w) for w in mine if value_named(cat, w)), None)
            if found:
                out[cat["name"]] = found["word"]
        else:
            kept = []
            for w in mine:
                v = value_named(cat, w)
                word = v["word"] if v else w
                if word.lower() not in (x.lower() for x in kept):
                    kept.append(word)
            if kept:
                out[cat["name"]] = kept
    return out


def fresh_colour(cats: list[dict]) -> int:
    """The first of the participants' palette fewest values use, so each new value reads apart."""
    used = [v["colour"] for c in cats for v in c["values"] if colour_ok(v.get("colour"))]
    return min(range(len(COLOURS)), key=lambda i: (used.count(i), i))


def colour_of(said) -> int:
    """A colour by its name in the participants' palette, Brown, or its place there from 0, refused otherwise."""
    return traj_mod.tag_colour_of(said)


# ------------------------------------------------------------------ as the screens and the agents read them

def pills(cats: list[dict], values: dict) -> list[dict]:
    """The pills a participant shows: the categories shown, in their order, each value its own, `{"category",
    "word", "colour"}`."""
    out = []
    mine = values_for(values, cats)
    for cat in cats:
        if not cat["show"]:
            continue
        for w in given_words(mine.get(cat["name"])):
            v = value_named(cat, w)
            out.append({"category": cat["name"], "word": w, "colour": v["colour"] if v else 0})
    return out


def answer(cats: list[dict]) -> list[dict]:
    """The categories as the page draws them and an agent reads them, each with `export`, whether it goes into the
    participants table and the pen portrait's line."""
    return [dict(c, values=[dict(v) for v in c["values"]], export=exported(c)) for c in cats]


def exported(cat: dict) -> bool:
    return cat["export"] if isinstance(cat.get("export"), bool) else bool(cat["show"])


def shown_line(cats: list[dict], values: dict) -> str:
    """A participant's values in a line, "Female, 70 and over, British", the categories ticked for the exports in
    their order, the PETs' pen portrait line."""
    mine = values_for(values, cats)
    return ", ".join(w for c in cats if exported(c) for w in given_words(mine.get(c["name"])))


def cell(cat: dict, values: dict) -> str:
    """A participant's value in one category for a table's cell, free words joined by commas."""
    return ", ".join(given_words(values.get(cat["name"])))


def sums(cats: list[dict], everyone: list[dict]) -> list[dict]:
    """The participants table In sum: each category ticked with its values counted over `everyone`'s values, in the
    category's order, `{"name", "counts"}`, "Female (2), Male (1)", a category nobody has a value in left out."""
    out = []
    for cat in cats:
        counts: dict[str, int] = {}
        for values in everyone:
            for w in given_words(values_for(values, [cat]).get(cat["name"])):
                counts[w] = counts.get(w, 0) + 1
        order = [v["word"] for v in cat["values"]]
        listed = sorted(counts, key=lambda w: (order.index(w) if w in order else len(order), w.lower()))
        if listed:
            out.append({"name": cat["name"], "counts": ", ".join(f"{w} ({counts[w]})" for w in listed)})
    return out


# ------------------------------------------------------------------ a change

# each refusal's line by its name, in the catalogue under demographics.refuse
REFUSALS = {
    "no_category": lambda **v: i18n.t("demographics.refuse.no_category", **v),
    "no_category_none": lambda **v: i18n.t("demographics.refuse.no_category_none", **v),
    "no_value": lambda **v: i18n.t("demographics.refuse.no_value", **v),
    "no_value_none": lambda **v: i18n.t("demographics.refuse.no_value_none", **v),
    "two_values": lambda **v: i18n.t("demographics.refuse.two_values", **v),
    "name_taken": lambda **v: i18n.t("demographics.refuse.name_taken", **v),
    "value_taken": lambda **v: i18n.t("demographics.refuse.value_taken", **v),
    "needs_name": lambda **v: i18n.t("demographics.refuse.needs_name", **v),
    "needs_value": lambda **v: i18n.t("demographics.refuse.needs_value", **v),
    "name_long": lambda **v: i18n.t("demographics.refuse.name_long", **v),
    "value_long": lambda **v: i18n.t("demographics.refuse.value_long", **v),
    "words_many": lambda **v: i18n.t("demographics.refuse.words_many", **v),
    "cats_many": lambda **v: i18n.t("demographics.refuse.cats_many", **v),
    "list_many": lambda **v: i18n.t("demographics.refuse.list_many", **v),
    "kind": lambda **v: i18n.t("demographics.refuse.kind", **v),
    "how": lambda **v: i18n.t("demographics.refuse.how", **v),
    "real_name": lambda **v: i18n.t("demographics.refuse.real_name", **v),
    "not_op": lambda **v: i18n.t("demographics.refuse.not_op", **v),
    "ops_list": lambda **v: i18n.t("demographics.refuse.ops_list", **v),
    "values_list": lambda **v: i18n.t("demographics.refuse.values_list", **v),
    "values_shape": lambda **v: i18n.t("demographics.refuse.values_shape", **v),
    "to_list_two": lambda **v: i18n.t("demographics.refuse.to_list_two", **v),
    "words_add": lambda **v: i18n.t("demographics.refuse.words_add", **v),
    "value_to_same": lambda **v: i18n.t("demographics.refuse.value_to_same", **v),
    "value_to_list": lambda **v: i18n.t("demographics.refuse.value_to_list", **v),
}


def refuse(key: str, **slots) -> None:
    raise WorkbookError(REFUSALS[key](**slots))


def no_category(cats: list[dict], name) -> None:
    listed = formats.list_words([c["name"] for c in cats])
    refuse("no_category" if cats else "no_category_none", name=words(name) or "?", list=listed)


def find_cat(cats: list[dict], name) -> dict:
    cat = cat_named(cats, name)
    if cat is None:
        no_category(cats, name)
    return cat


def no_value(cat: dict, word) -> None:
    listed = formats.list_words([v["word"] for v in cat["values"]])
    refuse("no_value" if cat["values"] else "no_value_none", category=cat["name"], value=words(word) or "?",
           list=listed)


def find_value(cat: dict, word) -> dict:
    v = value_named(cat, word)
    if v is None:
        no_value(cat, word)
    return v


def checked_name(cats: list[dict], name, but: dict | None = None) -> str:
    name = words(name)
    if not name:
        refuse("needs_name")
    if len(name) > NAME_MAX:
        refuse("name_long", most=NAME_MAX)
    other = cat_named(cats, name)
    if other is not None and other is not but:
        refuse("name_taken", name=other["name"])
    return name


def checked_word(word, real_name=None) -> str:
    word = words(word)
    if not word:
        refuse("needs_value")
    if len(word) > WORD_MAX:
        refuse("value_long", most=WORD_MAX)
    entry = real_name(word) if real_name else None
    if entry:
        refuse("real_name", entry=entry)
    return word


def holders(people: dict, cat: dict, word: str | None = None) -> list[str]:
    """Who has a value in a category, or this word of it, in case order."""
    out = []
    for case, kept in people.items():
        mine = given_words(values_for((kept or {}).get(VALUES), [cat]).get(cat["name"]))
        if mine and (word is None or word.lower() in (w.lower() for w in mine)):
            out.append(case)
    return sorted(out, key=traj_mod.case_order)


def who(case: str) -> str:
    return traj_mod.who(case)


def their(names: list[str]) -> str:
    """"Juno's", "Mabel's and Rowan's"."""
    return formats.list_words([f"{n}'s" for n in names])


def poss(name: str) -> str:
    """A category's name as an owner, "Gender's", "Tags'"."""
    return f"{name}'" if name.endswith("s") else f"{name}'s"


def put(people: dict, case: str, cat: dict, mine: list[str]) -> None:
    """A participant's words in a category written to their set, a list's one word as a string, none taking it off."""
    entry = people.setdefault(case, {})
    held = values_kept(entry.get(VALUES))
    for k in [k for k in held if k.lower() == cat["name"].lower()]:
        held.pop(k)
    if mine:
        held[cat["name"]] = mine[0] if cat["kind"] == "list" else list(mine)
    if held:
        entry[VALUES] = held
    else:
        entry.pop(VALUES, None)


def at_of(op: dict, n: int, limit: int) -> int:
    at = op.get("at")
    if at is None or at == "":
        return limit
    try:
        return max(0, min(limit, int(at)))
    except (TypeError, ValueError):
        raise WorkbookError(i18n.t("server.operation_gives_place_which_number", n=n, at=at)) from None


def values_given(raw) -> list:
    """A category's values as an `add` gives them, words or `{"word", "colour"}`."""
    if raw is None:
        return []
    if isinstance(raw, str):
        raw = [w for w in raw.split(",")]
    if not isinstance(raw, list):
        refuse("values_list")
    return raw


def apply(cats: list[dict], people: dict, ops, real_name=None, table: dict | None = None) -> tuple[list[str], bool]:
    """Each operation run on `cats` and `people` in order, in place, answering a line for each change and whether
    a value came off anyone, so the caller copies the project file to `_Archive/` first. Refused as a whole, with
    both to be thrown away, when one is wrong:

    - `add`, `name`, `kind` (list or words, words without it), `values` (words or `{"word", "colour"}`), `show`
      (true without it), `at` (its place from 0, the end without it)
    - `rename`, `category`, `name`, on everyone who has a value in it
    - `kind`, `category`, `kind`: a list turned to free words keeps every value, free words turned to a list make
      the words in use its values, refused while someone has two
    - `show`, `category`, `show`, true or false, its pill on the rows, the pickers and Trajectories
    - `move`, `category`, `at`
    - `remove`, `category`, its values taken off everyone who had one
    - `export`, `category`, `export`, true or false, whether it goes into the participants table and the PETs'
      pen portrait line, and `table`, `how`, each or sum, how the participants table carries them
    - `value_add`, `category`, `value`, `colour` (a palette name, a fresh one without it), `at`, a list's alone
    - `value_rename`, `category`, `value`, `to`, on everyone who has it
    - `value_colour`, `category`, `value`, `colour`
    - `value_move`, `category`, `value`, `at`
    - `value_remove`, `category`, `value`, taken off everyone who has it
    - `value_to`, `category`, `value`, `to`, another category, the word and everyone who has it moved there,
      joining a value of the same words there

    `real_name(text)` answers the entry of the project's list of names to replace a word holds, or None, and
    `table`, `{"how"}`, holds how the participants table carries them, which `table` changes."""
    if not isinstance(ops, list):
        refuse("ops_list")
    said: list[str] = []
    took = False
    for n, op in enumerate(ops, start=1):
        kind = str((op or {}).get("op") or "") if isinstance(op, dict) else ""
        if kind not in OPS:
            refuse("not_op", n=n, op=kind or "empty")

        def cat_of(key: str = "category") -> dict:
            return find_cat(cats, op.get(key))

        if kind == "add":
            name = checked_name(cats, op.get("name"))
            if len(cats) >= CATS_MAX:
                refuse("cats_many", most=CATS_MAX)
            entry = real_name(name) if real_name else None
            if entry:
                refuse("real_name", entry=entry)
            how = words(op.get("kind")).lower() or "words"
            if how not in KINDS:
                refuse("kind", kind=words(op.get("kind")))
            cat = {"name": name, "kind": how, "show": op.get("show") is not False, "values": []}
            given = values_given(op.get("values"))
            if len(given) > LIST_MAX:
                refuse("list_many", most=LIST_MAX)
            for raw in given:
                raw = raw if isinstance(raw, dict) else {"word": raw}
                word = checked_word(raw.get("word"), real_name)
                if value_named(cat, word) is None:
                    colour = colour_of(raw["colour"]) if raw.get("colour") not in (None, "") else None
                    cat["values"].append({"word": word, "colour": colour})
            cats.insert(at_of(op, n, len(cats)), cat)
            for v in cat["values"]:
                if v["colour"] is None:
                    v["colour"] = fresh_colour(cats)
            listed = ", ".join(v["word"] for v in cat["values"])
            said.append(f"{name} added, a list: {listed}." if how == "list" and listed else
                        f"{name} added, a list." if how == "list" else f"{name} added, free words.")
        elif kind == "rename":
            cat = cat_of()
            name = checked_name(cats, op.get("name"), but=cat)
            entry = real_name(name) if real_name else None
            if entry:
                refuse("real_name", entry=entry)
            if name != cat["name"]:
                had = {case: values_for((kept or {}).get(VALUES), [cat]).get(cat["name"]) for case, kept in people.items()}
                was = cat["name"]
                cat["name"] = name
                for case, mine in had.items():
                    if mine:
                        put(people, case, dict(cat, name=was), [])
                        put(people, case, cat, given_words(mine))
                said.append(f"{was} renamed {name}.")
        elif kind == "kind":
            cat = cat_of()
            how = words(op.get("kind")).lower()
            if how not in KINDS:
                refuse("kind", kind=words(op.get("kind")))
            if how != cat["kind"]:
                if how == "list":
                    many = [case for case in holders(people, cat)
                            if len(given_words(values_for(people[case].get(VALUES), [cat]).get(cat["name"]))) > 1]
                    if many:
                        refuse("to_list_two", category=cat["name"], who=formats.list_words([who(c) for c in many]))
                    if len(cat["values"]) > LIST_MAX:
                        refuse("list_many", most=LIST_MAX)
                had = {case: given_words(values_for(people[case].get(VALUES), [cat]).get(cat["name"]))
                       for case in holders(people, cat)}
                # free words turned to a list make every word in use one of its values
                for mine in had.values():
                    for w in mine:
                        if value_named(cat, w) is None:
                            cat["values"].append({"word": w, "colour": fresh_colour(cats)})
                cat["kind"] = how
                for case, mine in had.items():
                    put(people, case, cat, mine)
                said.append(f"{cat['name']} is a list now." if how == "list" else f"{cat['name']} is free words now.")
        elif kind == "show":
            cat = cat_of()
            show = op.get("show") in (True, 1, "1", "true", "yes", "on")
            if show != cat["show"]:
                cat["show"] = show
                said.append(f"{cat['name']} shown as a pill." if show else f"{cat['name']} no longer shown as a pill.")
        elif kind == "export":
            cat = cat_of()
            on = op.get("export") in (True, 1, "1", "true", "yes", "on")
            if on != exported(cat):
                cat["export"] = on
                said.append(f"{cat['name']} goes into the participants table." if on
                            else f"{cat['name']} left out of the participants table.")
        elif kind == "table":
            how = words(op.get("how")).lower()
            if how not in HOWS:
                refuse("how", how=words(op.get("how")) or "?")
            if table is not None and how != table.get("how"):
                table["how"] = how
                said.append("The participants table has a row for each participant." if how == "each"
                            else "The participants table counts the values in sum.")
        elif kind == "move":
            cat = cat_of()
            cats.remove(cat)
            at = at_of(op, n, len(cats))
            cats.insert(at, cat)
            said.append(f"{cat['name']} moved to place {at + 1}.")
        elif kind == "remove":
            cat = cat_of()
            whose = []
            for v in cat["values"]:
                names = [who(c) for c in holders(people, cat, v["word"])]
                if names:
                    whose.append(f"{their(names)} {v['word']}")
            for case in holders(people, cat):
                put(people, case, cat, [])
            cats.remove(cat)
            took = took or bool(whose)
            said.append(f"{cat['name']} removed, with {formats.list_words(whose)}." if whose
                        else f"{cat['name']} removed.")
        elif kind == "value_add":
            cat = cat_of()
            if cat["kind"] != "list":
                refuse("words_add", category=cat["name"])
            word = checked_word(op.get("value"), real_name)
            if value_named(cat, word) is not None:
                refuse("value_taken", category=cat["name"], value=value_named(cat, word)["word"])
            if len(cat["values"]) >= LIST_MAX:
                refuse("list_many", most=LIST_MAX)
            colour = colour_of(op["colour"]) if op.get("colour") not in (None, "") else fresh_colour(cats)
            cat["values"].insert(at_of(op, n, len(cat["values"])), {"word": word, "colour": colour})
            said.append(f"{poss(cat['name'])} {word} added.")
        elif kind == "value_rename":
            cat = cat_of()
            v = find_value(cat, op.get("value"))
            to = checked_word(op.get("to"), real_name)
            other = value_named(cat, to)
            if other is not None and other is not v:
                refuse("value_taken", category=cat["name"], value=other["word"])
            if to != v["word"]:
                was = v["word"]
                whose = holders(people, cat, was)
                for case in whose:
                    mine = given_words(values_for(people[case].get(VALUES), [cat]).get(cat["name"]))
                    put(people, case, cat, [to if w.lower() == was.lower() else w for w in mine])
                v["word"] = to
                said.append(f"{poss(cat['name'])} {was} renamed {to}" + (f", on {len(whose)} participant"
                                                                      f"{'s' if len(whose) != 1 else ''}." if whose else "."))
        elif kind == "value_colour":
            cat = cat_of()
            v = find_value(cat, op.get("value"))
            colour = colour_of(op.get("colour"))
            if colour != v["colour"]:
                v["colour"] = colour
                said.append(f"{poss(cat['name'])} {v['word']} is {COLOURS[colour]} now.")
        elif kind == "value_move":
            cat = cat_of()
            v = find_value(cat, op.get("value"))
            cat["values"].remove(v)
            at = at_of(op, n, len(cat["values"]))
            cat["values"].insert(at, v)
            said.append(f"{poss(cat['name'])} {v['word']} moved to place {at + 1}.")
        elif kind == "value_remove":
            cat = cat_of()
            v = find_value(cat, op.get("value"))
            whose = holders(people, cat, v["word"])
            for case in whose:
                mine = given_words(values_for(people[case].get(VALUES), [cat]).get(cat["name"]))
                put(people, case, cat, [w for w in mine if w.lower() != v["word"].lower()])
            cat["values"].remove(v)
            took = took or bool(whose)
            said.append(f"{poss(cat['name'])} {v['word']} removed" + (
                f", from {formats.list_words([who(c) for c in whose])}." if whose else "."))
        elif kind == "value_to":
            cat = cat_of()
            v = find_value(cat, op.get("value"))
            to = cat_of("to")
            if to is cat:
                refuse("value_to_same", value=v["word"], category=cat["name"])
            whose = holders(people, cat, v["word"])
            there = value_named(to, v["word"])
            if to["kind"] == "list":
                clash = []
                for case in whose:
                    have = given_words(values_for(people[case].get(VALUES), [to]).get(to["name"]))
                    if have and have[0].lower() != v["word"].lower():
                        clash.append(f"{who(case)} ({have[0]})")
                if clash:
                    refuse("value_to_list", category=to["name"], value=v["word"],
                           who=formats.list_words(clash))
                if there is None and len(to["values"]) >= LIST_MAX:
                    refuse("list_many", most=LIST_MAX)
            if there is None:
                there = {"word": v["word"], "colour": v["colour"]}
                to["values"].append(there)
            for case in whose:
                mine = given_words(values_for(people[case].get(VALUES), [cat]).get(cat["name"]))
                put(people, case, cat, [w for w in mine if w.lower() != v["word"].lower()])
                have = given_words(values_for(people[case].get(VALUES), [to]).get(to["name"]))
                if there["word"].lower() not in (w.lower() for w in have):
                    if to["kind"] == "words" and len(have) >= WORDS_MAX:
                        refuse("words_many", most=WORDS_MAX)
                    put(people, case, to, have + [there["word"]] if to["kind"] == "words" else [there["word"]])
            cat["values"].remove(v)
            said.append(f"{v['word']} moved from {cat['name']} to {to['name']}"
                        + (f", with {formats.list_words([who(c) for c in whose])}." if whose else "."))
    return said, took


def set_values(cats: list[dict], people: dict, case: str, given, real_name=None) -> list[str]:
    """One participant's values changed in `people`, in place, answering a line for each change. `given` is
    `{category: value}`: a list's one word, free words as a list or one string with commas between them, and "" or
    an empty list clearing it, each category left out kept as it is. A free word the category lacks joins it with a
    colour of its own. Refused whole, with both to be thrown away, for a category the project lacks, a value not in
    a list, two for a list, a word over its limit or holding a name from the list of names to replace, or more
    words than a category holds."""
    if not isinstance(given, dict):
        refuse("values_shape")
    said = []
    name = who(case)
    for cat_name, raw in given.items():
        if raw is None:
            continue
        cat = find_cat(cats, cat_name)
        if isinstance(raw, list):
            asked = [words(w) for w in raw if words(w)]
        elif cat["kind"] == "words":
            asked = [words(w) for w in str(raw).split(",") if words(w)]
        else:
            asked = [words(raw)] if words(raw) else []
        if cat["kind"] == "list":
            if len(asked) > 1:
                refuse("two_values", category=cat["name"], who=name,
                       values=formats.list_words(asked))
            mine = []
            for w in asked:
                mine.append(find_value(cat, w)["word"])
        else:
            mine = []
            for w in asked:
                w = checked_word(w, real_name)
                v = value_named(cat, w)
                word = v["word"] if v else w
                if word.lower() not in (x.lower() for x in mine):
                    mine.append(word)
            if len(mine) > WORDS_MAX:
                refuse("words_many", most=WORDS_MAX)
            for w in mine:
                if value_named(cat, w) is None:
                    cat["values"].append({"word": w, "colour": fresh_colour(cats)})
        was = given_words(values_for((people.get(case) or {}).get(VALUES), [cat]).get(cat["name"]))
        if [w.lower() for w in was] == [w.lower() for w in mine] and was == mine:
            continue
        put(people, case, cat, mine)
        said.append(f"{name}'s {cat['name']} is {formats.list_words(mine)} now." if mine
                    else f"{name}'s {cat['name']} cleared.")
    return said


def tidy(cats: list[dict], people: dict) -> None:
    """Before a save: every participant's values read against the categories, a value of a category gone or not
    in its list left out, and each free word nobody has any more taken out of its category."""
    for case in list(people):
        kept = people[case]
        if not isinstance(kept, dict):
            continue
        mine = values_for(kept.get(VALUES), cats)
        if mine:
            kept[VALUES] = mine
        else:
            kept.pop(VALUES, None)
    for cat in cats:
        if cat["kind"] != "words":
            continue
        used = {w.lower() for kept in people.values() if isinstance(kept, dict)
                for w in given_words(values_for(kept.get(VALUES), [cat]).get(cat["name"]))}
        cat["values"] = [v for v in cat["values"] if v["word"].lower() in used]


def written(cats: list[dict]) -> list[dict]:
    """The categories as the project file keeps them."""
    out = []
    for c in cats:
        entry = {"name": c["name"], "kind": c["kind"], "show": bool(c["show"]),
                 "values": [{"word": v["word"], "colour": v["colour"]} for v in c["values"]]}
        if isinstance(c.get("export"), bool):
            entry["export"] = c["export"]
        out.append(entry)
    return out


# ------------------------------------------------------------------ from a REFI-QDA package

LIST_FROM = 12


def package_text(value: dict) -> str:
    """A variable's value as a word: a Boolean as Yes or No, anything else its own words."""
    if value.get("kind") == "BooleanValue":
        return (i18n.t("demographics.qdpx.yes") if value["text"].lower() in ("true", "1") else i18n.t("demographics.qdpx.no"))
    return words(value.get("text"))


def number_of(text: str) -> float | None:
    try:
        return float(text)
    except ValueError:
        return None


def from_package(pkg: dict, people: dict[str, list[str]]) -> tuple[list[dict], dict[str, dict], list[str]]:
    """A REFI-QDA package's variables as the participants' demographics (demobuild, 12 November 2026): each variable
    a category, `{"name", "kind", "values"}`, and each participant's values, `people` being each participant the
    import makes or joins, by label, with their sources' guids in order. A value on a case (NVivo's case attributes)
    goes to the participant whose sources the case holds, a value on a source (MAXQDA's document variables) to the
    participant whose interview it is, their first interview's where two differ, and those participants come back
    in the third part of the answer. A variable of LIST_FROM values or fewer becomes a list in the order first met
    (Booleans as Yes and No, numbers in order), more becomes free words. An Idiograph package's own variables come
    back as they went: a list with its values in their order from its description, free words split at commas."""
    variables = pkg.get("variable_list") or []
    if not variables or not people:
        return [], {}, []
    own = str(pkg.get("origin") or "").startswith("Idiograph")
    case_values = [(set(c.get("sources") or []), c.get("variables") or {}) for c in pkg.get("cases") or []]
    source_values = {s["guid"]: s.get("variables") or {} for s in pkg.get("sources") or []}
    got: dict[str, dict] = {}
    differ: list[str] = []
    for label, guids in people.items():
        mine: dict = {}
        for held, values in case_values:
            if held & set(guids):
                for g, v in values.items():
                    mine.setdefault(g, v)
        first: dict = {}
        for g in guids:
            for vg, v in source_values.get(g, {}).items():
                if vg in first and first[vg]["text"] != v["text"] and label not in differ:
                    differ.append(label)
                first.setdefault(vg, v)
        for vg, v in first.items():
            mine.setdefault(vg, v)
        got[label] = mine
    cats: list[dict] = []
    values: dict[str, dict] = {label: {} for label in people}
    list_head = i18n.t("demographics.qdpx.list_head")
    for var in variables:
        name = words(var.get("name"))[:NAME_MAX]
        if not name or cat_named(cats, name) is not None or len(cats) >= CATS_MAX:
            continue
        held = [(label, package_text(got[label][var["guid"]])[:WORD_MAX if not own else 10 ** 6])
                for label in people if var["guid"] in got[label]]
        held = [(label, text) for label, text in held if text]
        lines = [words(x) for x in str(var.get("description") or "").splitlines() if words(x)]
        if own:
            kind = "list" if len(lines) > 1 or (lines and lines[0] == list_head) else "words"
        else:
            distinct = list(dict.fromkeys(text for _l, text in held))
            kind = "list" if len(distinct) <= LIST_FROM else "words"
        if kind == "list":
            order = [w[:WORD_MAX] for w in lines[1:]] if own else []
            met = list(dict.fromkeys(text[:WORD_MAX] for _l, text in held))
            if not own and met and all(number_of(t) is not None for t in met):
                met.sort(key=number_of)
            listed = list(dict.fromkeys(order + [t for t in met if t.lower() not in (o.lower() for o in order)]))
            cats.append({"name": name, "kind": "list", "values": listed[:LIST_MAX]})
            for label, text in held:
                values[label][name] = text[:WORD_MAX]
        else:
            cats.append({"name": name, "kind": "words", "values": []})
            for label, text in held:
                split = [w[:WORD_MAX] for w in (text.split(",") if own else [text]) if words(w)]
                values[label][name] = [words(w) for w in split][:WORDS_MAX]
    return cats, {k: v for k, v in values.items() if v}, differ


def package_lines(cats: list[dict], values: dict[str, dict], differ: list[str]) -> list[str]:
    """The import's lines for its Demographics tick: each category with its kind and who has what."""
    out = []
    for cat in cats:
        whose: dict[str, list[str]] = {}
        for label, mine in values.items():
            for w in given_words(mine.get(cat["name"])):
                whose.setdefault(w, []).append(who(label))
        said = formats.list_words([f"{w} for {formats.list_words(names)}" for w, names in whose.items()])
        kind = i18n.t("demographics.cli.list") if cat["kind"] == "list" else i18n.t("demographics.cli.words")
        out.append(i18n.t("demographics.qdpx.line", name=cat["name"], kind=kind,
                          values=said or i18n.t("demographics.qdpx.nobody")))
    if differ:
        out.append(i18n.t("demographics.qdpx.differ", who=formats.list_words([who(x) for x in differ])))
    return out


def package_ops(cats: list[dict], held: list[dict]) -> list[dict]:
    """The operations that bring a package's categories into the project's, `held`: a category the project lacks
    added, and a list the project has given the values it lacks."""
    ops = []
    for cat in cats:
        there = cat_named(held, cat["name"])
        if there is None:
            ops.append({"op": "add", "name": cat["name"], "kind": cat["kind"],
                        "values": cat["values"] if cat["kind"] == "list" else []})
        elif there["kind"] == "list":
            for w in cat["values"]:
                if value_named(there, w) is None:
                    ops.append({"op": "value_add", "category": there["name"], "value": w})
    return ops


# ------------------------------------------------------------------ Trajectories' tags moved over

def traj_raw(root: Path) -> dict | None:
    path = traj_mod.path_of(root)
    if not path.exists():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    return data if isinstance(data, dict) else None


def traj_tags(data: dict | None) -> dict[str, list[str]]:
    """Each participant's tags a Trajectories file from before keeps on `placed`, by label."""
    placed = (data or {}).get("placed") if isinstance((data or {}).get("placed"), dict) else {}
    out = {}
    for case, at in placed.items():
        tags = traj_mod.tags_kept(at.get("tags")) if isinstance(at, dict) else []
        if tags:
            out[str(case)] = tags
    return out


def traj_colours(data: dict | None) -> dict[str, int]:
    held = (data or {}).get("tags") if isinstance((data or {}).get("tags"), dict) else {}
    return {words(w).lower(): n for w, n in held.items() if words(w) and colour_ok(n)}


def unsettled(root: Path) -> bool:
    """Whether the project's Trajectories file still keeps tags on a participant."""
    return bool(traj_tags(traj_raw(root)))


def key_of(people: dict, case: str) -> str:
    if case in people:
        return case
    name = who(case).lower()
    return next((k for k in people if who(k).lower() == name), case)


def merge_tags(cats: list[dict], people: dict, data: dict | None) -> list[str]:
    """Trajectories' tags into a Tags category of free words, in place, each word keeping the colour Trajectories
    gave it, each participant's joining what they hold there already. Answers whose moved, in case order."""
    tags = traj_tags(data)
    if not tags:
        return []
    colours = traj_colours(data)
    cat = cat_named(cats, TAGS)
    if cat is None:
        cat = {"name": TAGS, "kind": "words", "show": True, "values": []}
        cats.append(cat)
    if cat["kind"] == "list" and any(len(t) > 1 for t in tags.values()):
        cat["kind"] = "words"
    for case, words_ in sorted(tags.items(), key=lambda x: traj_mod.case_order(x[0])):
        key = key_of(people, case)
        have = given_words(values_for((people.get(key) or {}).get(VALUES), [cat]).get(cat["name"]))
        for w in words_:
            v = value_named(cat, w)
            if v is None:
                v = {"word": w, "colour": colours.get(w.lower(), fresh_colour(cats))}
                cat["values"].append(v)
            if v["word"].lower() not in (x.lower() for x in have):
                have.append(v["word"])
        put(people, key, cat, have[:WORDS_MAX] if cat["kind"] == "words" else have[:1])
    return sorted(tags, key=traj_mod.case_order)


def view(root: Path | None, project: dict, people: dict) -> People:
    """Every participant's set with the project's categories, as the screens and the agents read them: the project
    file's, and where a Trajectories file from before keeps tags, those merged into Tags as `settle` would move
    them. Only reads."""
    cats = cats_of(project)
    out = People({k: dict(v) for k, v in people.items()})
    if root is not None:
        merge_tags(cats, out, traj_raw(root))
    out.cats = cats
    return out


def move_plan(root: Path, project: dict, people: dict) -> list[str]:
    """What `settle` would move, a line each and the History's line, nothing written: the dry run of the move."""
    data = traj_raw(root)
    tags = traj_tags(data)
    if not tags:
        return []
    lines = [f"{who(case)}: {', '.join(tags[case])}." for case in sorted(tags, key=traj_mod.case_order)]
    return lines + [summary(len(tags))]


def summary(n: int) -> str:
    return f"Tags of {n} participant{'s' if n != 1 else ''} moved from Trajectories to the Tags category."


def archive_copy(path: Path, stamp: str) -> None:
    """A copy of a file in `_Archive/` beside it, `<stem> (pre-demographics <date-time>).json`, never over one."""
    folder = Path(path).parent / "_Archive"
    folder.mkdir(parents=True, exist_ok=True)
    stem = Path(path).name[:-len(".json")] if Path(path).name.endswith(".json") else Path(path).stem
    target, n = folder / f"{stem} ({ARCHIVE_LABEL} {stamp}).json", 2
    while target.exists():
        target, n = folder / f"{stem} ({ARCHIVE_LABEL} {stamp}-{n}).json", n + 1
    shutil.copy2(path, target)


def stamp_of(when: str) -> str:
    return re.sub(r"[^0-9T]", "", str(when))[:15].replace("T", "-") or "0"


def settle(root: Path, project: dict, project_path: Path, when: str, save_json, write_traj, sets_of, sets_written,
           sets_key: str) -> list[str]:
    """Trajectories' tags moved into each participant's values in the Tags category for good, the caller holding
    the project's lock: both files copied to `_Archive/` first, the project file written with the categories and
    the values, then `tags` taken off `placed` in the Trajectories file, its colour map kept whole, since LPETs'
    domains share it. Answers the History's line, none when there was nothing to move. `sets_of` and `sets_written`
    read and write the participants' sets (`participants.own_of`, `written`), kept under `sets_key`."""
    data = traj_raw(root)
    if not traj_tags(data):
        return []
    cats = cats_of(project)
    people = sets_of(project)
    moved = merge_tags(cats, people, data)
    stamp = stamp_of(when)
    if project_path.exists():
        archive_copy(project_path, stamp)
    archive_copy(traj_mod.path_of(root), stamp)
    tidy(cats, people)
    project[KEY] = written(cats)
    sets = sets_written(people)
    if sets:
        project[sets_key] = sets
    save_json(project_path, project)
    for at in (data.get("placed") or {}).values():
        if isinstance(at, dict):
            at.pop("tags", None)
    line = summary(len(moved))
    data["updated"] = when
    data["history"] = ((data.get("history") if isinstance(data.get("history"), list) else [])
                       + [{"when": when, "changes": [line]}])[-traj_mod.HISTORY_MAX:]
    write_traj(root, data)
    return [line]
