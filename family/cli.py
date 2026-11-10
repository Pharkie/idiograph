"""The family's command line (22 October 2026, the family codebase's fourth build, from the root's cli.py):
each app's commands for an AI agent in a conversation, Claude Code, Claude Desktop or Codex, on the app's
own code. The root's cli.py runs it, as `./idiograph`, `./sift`, `./trace` and their .bat files do:

    ./idiograph cases                  # from the app's folder, idiograph.bat on Windows
    ./sift search strings "<review folder>"
    ./trace <folder>

What every app shares is here: the options, the parser at the top, the refusals of another app's command by
name (see `args_for`), `perform`, which the MCP server runs each tool through, Search over a project by its
folder and the answer of every Search, the check of a file against its schema, and `main`. Each app's own
commands register with it as `boot.load("cli")` at the foot of this file imports them by their names:
Idiograph's, the family's first app's, at the top of `idiograph` (`register_own`, apps/idiograph/
idiograph_cli.py), and Sift's and Trace's each at the top of its own command (`register`), which since the
cutover (the sixth build, 23 October 2026) `idiograph` refuses by name. Plain readable text by default, and `--json`
for exact output. Every case goes by its pseudonym, and a case folder's second part never reaches any
output or error. The guides an agent reads are `docs/agents.md`, `docs/agents-sift.md` and
`docs/agents-trace.md`.
"""
from __future__ import annotations

import argparse
import contextlib
import io
import json
import re
import shlex
import sys
import time
from datetime import datetime
from pathlib import Path

# every entry puts the family's folders on the path first (boot.py), the root's cli.py among them, so each
# module is found by its plain name wherever it sits
if not getattr(sys, "frozen", False) and str(Path(__file__).resolve().parents[1]) not in sys.path:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import boot  # noqa: E402

boot.setup()

import agent_log  # noqa: E402
import app_folders  # noqa: E402
import app_identity  # noqa: E402
import app_search  # noqa: E402
import i18n  # noqa: E402
import server as srv  # noqa: E402
from errors import WorkbookError  # noqa: E402

# The words this module says, read in the run's language when said (i18nleft4, 2 November 2026): other
# modules and the checks read them as the module's names, through `__getattr__`, as themes_ai's are
SAID = {
    "NO_WORDS": lambda **v: i18n.t("family_cli.said.no_words", v),
    "NO_FOLDER": lambda **v: i18n.t("family_cli.said.no_folder", v),
}


def _w(name: str, **vals) -> str:
    return SAID[name](**vals)


def __getattr__(name: str) -> str:
    """This module's words other modules and the checks name, read in the run's language."""
    if name in SAID:
        return SAID[name]()
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


SCHEMAS = boot.resource("docs/schemas")
# a case folder's second name, which is never printed: a folder `P<n> - Pseudonym-Secondname` is
# `P<n> - Pseudonym`, as the server shows it
SECOND = re.compile(r"\b(P\d+ - [A-Z][a-z]+)-[A-Z][a-z]+")
TOOL = "an AI agent"


class Refused(Exception):
    """A command that cannot go ahead, with each reason one plain line."""

    def __init__(self, *lines: str):
        super().__init__("\n".join(lines))
        self.lines = [str(line) for line in lines if str(line)]


# ------------------------------------------------------------------ output

def scrub(text: str) -> str:
    """Every case folder in the words by its pseudonym alone."""
    return SECOND.sub(r"\1", str(text))


def dumps(value, app: str | None = None) -> str:
    """Every answer as JSON, `--json`'s and the MCP server's alike, its project words marked (see `mark`) by
    the plain keys of `app`, or this run's: Idiograph's PLAIN, and Sift's and Trace's own (see `plain_of`)."""
    return scrub(json.dumps(mark(value, plain=plain_of(app or srv.APP)), ensure_ascii=False, indent=1))


# Words a participant or the interviewer said, or anyone wrote into the project, marked as data in every JSON
# answer of Idiograph's, never as an instruction to the agent reading it (Adam, 26 October 2026: "participant
# words returned to agents ... marked as untrusted data, yes"), and since 2 November 2026 Sift's and Trace's
# too (Adam, by dialog): a database's titles, abstracts and keywords, which anyone can publish, and a
# manuscript's claims and its references' words, each app by its own plain keys (see `plain_of`).
# Every answer passes through `dumps`, so this is the one place:
# each string comes back as {"untrusted_text": "..."} unless its key is one of PLAIN's, the app's own ids,
# keys, times, kinds, counts and the names an agent hands back as an input. A key not named here is marked,
# so a new answer's words are marked before anyone thinks of them. Plain text for a person stays as it is.
UNTRUSTED = "untrusted_text"
PLAIN = frozenset((
    # ids, keys and versions the app makes
    "id", "ids", "key", "keys", "items", "order", "group", "board", "boards", "revision", "version", "more",
    "export_label", "row",
    # the names an agent hands back as an input: a participant's pseudonym, a sheet, a timepoint
    "case", "sheet", "sheets", "timepoint",
    # times
    "at", "created", "updated", "time", "statements_complete",
    # the app's own words and kinds, and the files it names
    "kind", "kind_name", "scope", "unit", "count", "words", "error", "lines", "tool", "command", "q", "files",
    "workbook", "settings", "kinds",
    # a project's method, ipa or ta (tadraw, 31 October 2026)
    "method",
    # an action waiting for his yes: its op and where it stands, the app's own words (holds, 27 October 2026)
    "op", "status",
))


# each app's own plain keys, Sift's and Trace's, registered from their modules (see `register`)
APP_PLAIN: dict = {}


def plain_of(app: str) -> frozenset:
    """The keys whose strings stay plain in `app`'s answers: Idiograph's PLAIN, or Sift's or Trace's own, and
    for an app that named none, a refusal's two alone, so its words are marked before anyone thinks of them."""
    if app == app_identity.DEFAULT:
        return PLAIN
    return APP_PLAIN.get(app, frozenset(("error", "lines")))


def mark(value, key: str | None = None, plain: frozenset = PLAIN):
    """An answer with each string of the project's words as {"untrusted_text": "..."}, by its key (see
    PLAIN, or the app's own `plain`), a list's strings by the list's key. An empty string, a number, a yes or
    no and a string already marked stay as they are."""
    if isinstance(value, dict):
        if set(value) == {UNTRUSTED}:
            return value
        return {k: mark(v, k, plain) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [mark(v, key, plain) for v in value]
    if isinstance(value, str) and value and key not in plain:
        return {UNTRUSTED: value}
    return value


def marked(value) -> bool:
    """Whether an answer, as `mark` leaves it, holds any of the project's words."""
    if isinstance(value, dict):
        return set(value) == {UNTRUSTED} or any(marked(v) for v in value.values())
    if isinstance(value, list):
        return any(marked(v) for v in value)
    return False


def unmark(value):
    """A structure an agent hands back with the marking taken off, so a board read with `board show --json`
    goes back as it came."""
    if isinstance(value, dict):
        if set(value) == {UNTRUSTED} and isinstance(value[UNTRUSTED], str):
            return value[UNTRUSTED]
        return {k: unmark(v) for k, v in value.items()}
    if isinstance(value, list):
        return [unmark(v) for v in value]
    return value


FENCE = re.compile(r"<\s*(/?)\s*untrusted_text\s*>", re.IGNORECASE)


def fenced(text: str) -> str:
    """An answer's plain words for an agent, between <untrusted_text> and </untrusted_text>, a marker inside
    them made harmless so nothing a participant said can close the block early."""
    inside = FENCE.sub(lambda m: f"[{m.group(1)}{UNTRUSTED}]", str(text))
    return f"<{UNTRUSTED}>\n{inside}\n</{UNTRUSTED}>"


def when_said(iso) -> str:
    """A time as a line says it: 5 October 2026 at 19:02."""
    try:
        at = datetime.fromisoformat(str(iso))
    except (TypeError, ValueError):
        return str(iso or "")
    return f"{at.day} {at:%B %Y} at {at:%H:%M}"


def plural(n: int, one: str, many: str | None = None) -> str:
    return f"{n} {one if n == 1 else (many or one + 's')}"


# ---------------------------------------------------------------- board new

def read_spec(path) -> object:
    """A file of JSON read, or a structure handed over already read, as the MCP server hands over
    an agent's, taken as it is."""
    if not isinstance(path, (str, Path)):
        return unmark(path)
    try:
        return unmark(json.loads(Path(path).read_text(encoding="utf-8")))
    except OSError:
        raise Refused(i18n.t("family_cli.read_spec.could_not_be_read", path=path))
    except ValueError as exc:
        raise Refused(i18n.t("family_cli.read_spec.is_not_json", path=path, exc=exc))


# ----------------------------------------------------------------- validate

def schema_of(name: str) -> dict:
    return json.loads((SCHEMAS / f"{name}.schema.json").read_text(encoding="utf-8"))


TYPES = {"object": dict, "array": list, "string": str, "boolean": bool, "null": type(None)}


def type_ok(value, kind: str) -> bool:
    if kind == "integer":
        return isinstance(value, int) and not isinstance(value, bool)
    if kind == "number":
        return isinstance(value, (int, float)) and not isinstance(value, bool)
    return isinstance(value, TYPES[kind])


def kind_of(value) -> str:
    if value is None:
        return "null"
    if isinstance(value, bool):
        return i18n.t("family_cli.kind_of.true_or_false")
    if isinstance(value, (int, float)):
        return i18n.t("family_cli.kind_of.a_number")
    if isinstance(value, str):
        return i18n.t("family_cli.word.text")
    if isinstance(value, list):
        return i18n.t("family_cli.kind_of.a_list")
    return i18n.t("family_cli.kind_of.a_record")


WORD = {"object": lambda: i18n.t("family_cli.kind_of.a_record"), "array": lambda: i18n.t("family_cli.kind_of.a_list"),
        "string": lambda: i18n.t("family_cli.word.text"), "integer": lambda: i18n.t("family_cli.word.a_whole_number"),
        "number": lambda: i18n.t("family_cli.kind_of.a_number"),
        "boolean": lambda: i18n.t("family_cli.kind_of.true_or_false"), "null": lambda: "null"}


def conform(value, schema: dict, at: str, defs: dict, out: list) -> None:
    """The JSON Schema keywords the shipped schemas use, read here with the standard library:
    `$ref`, `anyOf`, `type`, `enum`, `const`, `pattern`, `minimum`, `minLength`, `required`,
    `properties`, `additionalProperties` and `items`, a `$ref` into another of them by its file
    name. Each problem is one plain line."""
    if "$ref" in schema:
        place, _, part = str(schema["$ref"]).partition("#")
        if place:
            defs = schema_of(place.replace(".schema.json", "")).get("$defs") or {}
        schema = defs[part.split("/")[-1]]
    if "anyOf" in schema:
        trials = []
        for option in schema["anyOf"]:
            found: list = []
            conform(value, option, at, defs, found)
            if not found:
                return
            trials.append(found)
        out.append(min(trials, key=len)[0] if len(trials) == 1 else i18n.t("family_cli.conform.is_not_in_any_shape_it", at=at, kind=kind_of(value)))
        return
    kinds = schema.get("type")
    if kinds:
        kinds = kinds if isinstance(kinds, list) else [kinds]
        if not any(type_ok(value, k) for k in kinds):
            out.append(i18n.t("family_cli.conform.should_be_not", at=at, list=' or '.join(WORD[k]() for k in kinds), kind=kind_of(value)))
            return
    if "const" in schema and value != schema["const"]:
        out.append(i18n.t("family_cli.conform.should_be", at=at, dumps=json.dumps(schema['const'])))
    if "enum" in schema and value not in schema["enum"]:
        out.append(i18n.t("family_cli.conform.should_be_one_of_not", at=at, list=', '.join(json.dumps(x) for x in schema['enum']), dumps=json.dumps(value)))
    if isinstance(value, str):
        if "minLength" in schema and len(value.strip()) < schema["minLength"]:
            out.append(i18n.t("family_cli.conform.is_empty", at=at))
        if "pattern" in schema and not re.search(schema["pattern"], value):
            out.append(i18n.t("family_cli.conform.does_not_read_as_it_should", at=at, value=value[:40]))
    if isinstance(value, (int, float)) and not isinstance(value, bool) and "minimum" in schema and value < schema["minimum"]:
        out.append(i18n.t("family_cli.conform.is_below", at=at, minimum=schema['minimum']))
    if isinstance(value, dict):
        for key in schema.get("required") or []:
            if key not in value:
                out.append(i18n.t("family_cli.conform.is_missing", at=at, key_=key))
        props = schema.get("properties") or {}
        extra = schema.get("additionalProperties", True)
        for key, item in value.items():
            where = f"{at}.{key}" if re.match(r"^[A-Za-z_]\w*$", str(key)) else f"{at}[{json.dumps(key, ensure_ascii=False)}]"
            if key in props:
                conform(item, props[key], where, defs, out)
            elif extra is False:
                out.append(i18n.t("family_cli.conform.is_not_something_this_file_holds", where=where))
            elif isinstance(extra, dict):
                conform(item, extra, where, defs, out)
    if isinstance(value, list) and isinstance(schema.get("items"), dict):
        for i, item in enumerate(value):
            conform(item, schema["items"], f"{at}[{i}]", defs, out)


# ------------------------------------------------------------------ search

SEARCH_LIMIT = 25


def search_words(given, whole: bool = True, match_case: bool = False) -> tuple[str, list[str], str]:
    """The words an agent asked for as the search reads them, as the app's Search reads them
    (`app_search.query`): the words typed, each folded and with its other forms, "slept" for sleep, and the
    phrase when they stand in quotation marks, which every hit then holds as typed, with no other form. `whole`
    and `match_case` are the card's Whole word, on unless an agent turns it off as the card opens with it
    ticked, and Match case, off unless asked for."""
    q = " ".join(str(w) for w in (given if isinstance(given, list) else [given or ""])).strip()
    q, words, phrase = app_search.query(q, whole, match_case)
    if not words:
        raise Refused(_w("NO_WORDS"))
    return q, words, phrase


def search_modifiers(args) -> tuple[bool, bool]:
    """The card's two ticks as an agent sets them, `--whole-word` or `--no-whole-word` and `--match-case`, or the
    tool's `whole_word` and `match_case`. Whole word is on unless it is false, as the card opens (Adam, 6 November
    2026), and Match case off unless it is true."""
    return getattr(args, "whole_word", True) is not False, getattr(args, "match_case", False) is True


def search_kinds(value) -> set[str]:
    """The kinds asked for, by the card's names, passage, statement, or the agent's groups, passages, notes,
    pets, records, with commas in one string or as a list. None asked is every kind."""
    given = value if isinstance(value, list) else str(value or "").split(",")
    out = set()
    for raw in given:
        word = " ".join(str(raw).split()).lower()
        if not word:
            continue
        if word in app_search.KIND_GROUPS:
            out.update(app_search.KIND_GROUPS[word])
        elif word in app_search.KIND_NAMES:
            out.add(word)
        else:
            raise Refused(i18n.t("family_cli.search_kinds.no_kind_called_the_kinds_or", raw=raw, list=', '.join(app_search.KIND_GROUPS), list2=', '.join(app_search.KIND_NAMES)))
    return out


def search_page(args) -> tuple[int, int]:
    """Where a page of hits starts, from the cursor `more` an earlier answer gave, and how many it holds."""
    limit = getattr(args, "limit", None)
    try:
        limit = SEARCH_LIMIT if limit in (None, "") else int(limit)
    except (TypeError, ValueError):
        raise Refused(i18n.t("family_cli.search_page.is_not_a_number_of_hits", limit=limit)) from None
    if not 1 <= limit <= app_search.LIMIT:
        raise Refused(i18n.t("family_cli.search_page.a_page_holds_1_to_hits", limit=app_search.LIMIT))
    more = str(getattr(args, "more", None) or "0").strip()
    if not more.isdigit():
        raise Refused(i18n.t("family_cli.search_page.is_not_a_cursor_a_search", more=more))
    return int(more), limit


def quoted_arg(value) -> str:
    text = str(value)
    return text if re.fullmatch(r"[\w.:/-]+", text) else '"' + text.replace('"', '\\"') + '"'


def opener(tool: str, arguments: dict, command: list, project: str = "") -> dict:
    """The tool that opens a hit whole and its inputs, and the same as a command line."""
    head = ["idiograph"] + (["--project", project] if project else [])
    return {"tool": tool, "arguments": arguments, "command": " ".join(quoted_arg(w) for w in head + command)}


def search_hit(r: dict, project: str, many: bool, cases: dict, p, board: str | None) -> dict:
    """One hit as an agent takes it: its kind, the case, where it is, the snippet with every word marked, and
    what its app adds for the screen it lands on (see `register`), Idiograph's the speaker, a statement's id
    and key with where the board places it, `p` its project, `cases` its cases read for this page and `board`
    the board asked for, and every app's the tool that opens it."""
    go = r.get("go") or {}
    hit = {"kind": r["kind"], "kind_name": app_search.kind_name(r["kind"]), "case": r.get("case", ""),
           "where": r["where"], "snippet": r["marked"]}
    if many:
        hit["project"] = project
    named = project if many else ""
    screen = go.get("screen")
    if screen in CASE_HITS:
        CASE_HITS[screen](hit, r, go, named, cases, p, board)
    elif screen in SCREEN_HITS:
        SCREEN_HITS[screen](hit, go)
    return hit


def search_answer(q: str, words: list[str], phrase: str, found: list[dict], scope: str, started: float) -> dict:
    """The app's own answer over what the app's own search found (`app_search.answer`), every hit, with
    a phrase's hits alone kept first and every snippet's words marked."""
    if phrase:
        found = [it for it in found if app_search.phrase_in(it["text"], phrase)]
    got = app_search.answer(q, scope, words, found, started, limit=10 ** 9)
    for r in got["results"]:
        r["marked"] = app_search.marked(r["text"], words)
    return got


def cmd_search_folder(args) -> tuple:
    """`search <words> --folder <folder>`: the app's Search over a Sift project, the screening the folder
    holds and the plan above it, or a review's own folder, its plan and the screening its Screening step
    opens, or a Trace project. A screening holds published records and a Trace project his own manuscripts,
    so it needs no project and no tick, as `sift` and `trace` do."""
    started = time.perf_counter()
    q, words, phrase = search_words(getattr(args, "words", ""), *search_modifiers(args))
    kinds = search_kinds(getattr(args, "kinds", None))
    start, limit = search_page(args)
    given = Path(args.folder).expanduser()
    if not given.is_dir():
        raise Refused(i18n.t("family_cli.search_folder.that_folder_is_not_there"))
    folder = given.resolve()

    def own(scope: str) -> str:
        # each app's Search over its own kinds alone, refused before anything is read: Sift's never
        # reading a Trace project, nor Trace's a Sift one
        if scope not in app_identity.served(srv.APP):
            them, us = app_identity.APPS[scope]["name"], app_identity.APPS[srv.APP]["name"]
            raise Refused(i18n.t("family_cli.search_folder.that_folder_is_s_not_s", them=them, us=us, scope=scope))
        return scope

    # each app's own Search over its projects, Sift's first, then Trace's (see `register`)
    for app, theirs in APP_COMMANDS.items():
        try:
            project = theirs["folder"](folder)
        except WorkbookError:
            continue
        scope = own(app)
        found = theirs["found"](words, project, str(project))
        break
    else:
        raise Refused(_w("NO_FOLDER"))
    answers = [(folder.name, None, scope, search_answer(q, words, phrase, found, scope, started))]
    return search_said(q, phrase, scope, answers, kinds, start, limit, None, [], words.whole, words.case)


def search_said(q: str, phrase: str, scope: str, answers: list, kinds: set, start: int, limit: int,
                board: str | None, closed: list[str], whole_word: bool | None = None,
                match_case: bool | None = None) -> tuple:
    """The hits of every answer, project by project, the kinds asked for alone, one page of them from
    `start`, with the counts by kind and by case over every hit, and the cursor to the next page."""
    many = len(answers) > 1
    rows, counts, by_case = [], {}, {}
    for name, p, _scope, got in answers:
        for k, n in got["counts"].items():
            counts[k] = counts.get(k, 0) + n
        for r in got["results"]:
            if kinds and r["kind"] not in kinds:
                continue
            rows.append((name, p, r))
            if r.get("case"):
                label = f"{r['case']} ({name})" if many else r["case"]
                by_case[label] = by_case.get(label, 0) + 1
    if start > len(rows):
        raise Refused(i18n.t("family_cli.search_said.is_past_the_hits_of_this", start=start, n_rows=len(rows)))
    cases: dict = {}
    page = []
    for name, p, r in rows[start:start + limit]:
        held = cases.setdefault(name, {})
        page.append(search_hit(r, name, many, held, p, board))
    after = start + len(page)
    more = str(after) if after < len(rows) else None
    asked = answers[0][3] if answers else {}
    out = {"q": q, "phrase": bool(phrase), "whole_word": bool(asked.get("whole_word") if whole_word is None else whole_word),
           "match_case": bool(asked.get("match_case") if match_case is None else match_case), "scope": scope, "kinds": sorted(kinds), "total": len(rows),
           "counts": {k: n for k, n in counts.items() if n}, "cases": [{"case": c, "count": n} for c, n in by_case.items()],
           "results": page, "start": start, "more": more}
    if many:
        out["projects"] = [name for name, *_ in answers]
    if closed:
        out["closed"] = closed
    said = f'"{q}"' if phrase else q
    lines = [f"{i18n.t('family_cli.n.hit', n=len(rows))} for {said}" + (i18n.t("family_cli.search_said.from_to", v_=start + 1, after=after) if page and (start or more) else "")
             + (":" if page else ".")]
    if out["counts"]:
        lines.append(i18n.t("family_cli.search_said.by_kind_every_kind") + ", ".join(
            f"{app_search.kind_name(k, n != 1)} {n}" for k, n in out["counts"].items()) + ".")
    if by_case:
        lines.append(i18n.t("family_cli.search_said.by_case") + ", ".join(f"{c} {n}" for c, n in by_case.items()) + ".")
    for n, h in enumerate(page, start=start + 1):
        head = " · ".join(x for x in (h.get("project", ""), h["case"], h["where"], h["kind_name"], h.get("speaker", "")) if x)
        lines += ["", f"{n}. {head}", f"   {h['snippet']}"]
        if h.get("id"):
            placed = h.get("placed")
            on = ""
            if placed:
                mark = f", {placed['export_label']}" if placed.get("export_label") else ""
                on = i18n.t("family_cli.search_said.on", name=placed['name'], mark=mark, where=placed['where'])
            lines.append(f"   {h['id']} {h['key']}{on}")
        if h.get("open"):
            lines.append(i18n.t("family_cli.search_said.open", command=h['open']['command']))
    if not page and start:
        lines.append(i18n.t("family_cli.search_said.no_hits_after_the_first", start=start))
    if more:
        lines += ["", i18n.t("family_cli.search_said.more_the_same_search_with_more", more=more)]
    for name in closed:
        lines += ["", i18n.t("family_cli.search_said.closed_to_ai_agents_settings_projects", name=name)]
    return out, lines


# -------------------------------------------------------------------- main

def parser(app: str | None = None, search: bool = False) -> argparse.ArgumentParser:
    """The command line's parser for one of the family's apps, Idiograph's by default. Sift's takes the
    `sift` command's arguments at its top, `sift search strings <folder>`, Trace's the `trace` command's,
    and with `search` either is its Search alone, `search <words> --folder <folder>`."""
    name = app_identity.check(app)
    # the options go before the command or after it alike. Below the top they default to nothing at
    # all, so an option given before the command is never put back to its default after it, and the
    # top's defaults are its own, never the ones the commands share
    def options() -> argparse.ArgumentParser:
        made = argparse.ArgumentParser(add_help=False)
        made.add_argument("--project", default=argparse.SUPPRESS, help="the project of this name, of those Idiograph holds")
        made.add_argument("--root", default=argparse.SUPPRESS, help="the project in this folder, for this run alone")
        made.add_argument("--demo", action="store_true", default=argparse.SUPPRESS,
                          help="work on the demo, Living with a dog, the IPA one, or with `--demo ta` the thematic analysis one")
        made.add_argument("--demo-ta", action="store_true", default=argparse.SUPPRESS, help=argparse.SUPPRESS)
        made.add_argument("--config", default=argparse.SUPPRESS, help="a settings file in place of config.json")
        made.add_argument("--json", action="store_true", default=argparse.SUPPRESS, help="exact output, as JSON")
        return made

    common = options()
    if name != app_identity.DEFAULT:
        own = app_identity.APPS[name]["name"]
        if search:
            ap = argparse.ArgumentParser(prog=name, parents=[options()],
                                         description=f"{own}'s Search, over one project by its folder.")
            ap.set_defaults(project=None, root=None, demo=False, config=None, json=False)
            add_search(ap.add_subparsers(dest="command", required=True), common)
            return ap
        theirs = APP_COMMANDS[name]
        ap = argparse.ArgumentParser(prog=name, description=theirs["about"])
        ap.set_defaults(command=name, act=None, project=None, root=None, demo=False, config=None, json=False)
        theirs["arguments"](ap)
        return ap
    writes = argparse.ArgumentParser(add_help=False)
    writes.add_argument("--dry-run", action="store_true", help="say what would change and write nothing")
    writes.add_argument("--note", default="", help="his request in his own words, which the board and its History name")
    writes.add_argument("--tool", default="", help="the tool the agent works in, such as Claude Code")
    # the family's first app's own commands at the top, Idiograph's, as its module registers them
    own = OWN_APP.get(name, {})
    ap = argparse.ArgumentParser(prog="idiograph", parents=[options()], description=own.get("about"))
    ap.set_defaults(project=None, root=None, demo=False, config=None, json=False)
    sub = ap.add_subparsers(dest="command", required=True)
    if own:
        own["arguments"](sub, common, writes)
    add_search(sub, common)
    return ap


def add_search(sub, common) -> None:
    """The app's Search as a command, `search <words>`, each app's own."""
    x = sub.add_parser("search", parents=[common],
                       help="the app's Search: words in passages, statements, notes, PETs, GETs, records and claims, "
                            "across the participants, each hit with where it is and the command that opens it")
    x.add_argument("words", nargs="+", help="the words, every one in any order, or a phrase in quotation marks")
    x.add_argument("--whole-word", action=argparse.BooleanOptionalAction, default=True,
                   help="each word only as a whole word, with its other forms, as the card's Whole word tick: cat "
                        "finds cat and cats, never catch, and a phrase only on word edges. On by default, "
                        "--no-whole-word finds a word inside a longer one too")
    x.add_argument("--match-case", action="store_true", default=False,
                   help="each word in the case typed, accents still set aside, its other forms in that case, as "
                        "the card's Match case tick. Off by default")
    x.add_argument("--case", default=None, help="this participant alone, by their pseudonym")
    x.add_argument("--board", default=None, help="with --case, this board's PETs and notes alone, and its statements "
                                                 "placed as it places them, the Current board's by default")
    x.add_argument("--kinds", default=None, help="these kinds alone, with commas: passages, statements, quotes, notes, "
                                                 "pets, gets, boards, cases, records, plan or claims, or the search "
                                                 "card's own, passage, enote, petnote and the rest")
    x.add_argument("--limit", default=None, help=f"the hits a page holds, {SEARCH_LIMIT} when left out, "
                                                 f"{app_search.LIMIT} at most")
    x.add_argument("--more", default=None, help="the cursor the answer before gave, for its next page")
    x.add_argument("--folder", default=None, help="a Sift project's screening or review folder, or a Trace project's "
                                                  "folder, in place of a project of Idiograph's")


# Each app's own commands, the first word after the app's command, so a word that is another app's is
# refused by name: Idiograph's, and Sift's `sift` and Trace's `trace`, the words `idiograph sift ...` and
# `idiograph trace ...` took until the cutover (the sixth build, 23 October 2026), each now refused with the
# command to run in its place. Sift's and Trace's commands take a folder first, and `search` and `agents` (the
# agent log, `agents log`, since siftlog, 3 November 2026) are every app's own (FAMILY_WORDS).
OWN_COMMANDS = {"idiograph": ("cases", "statements", "board", "gets", "turn", "import", "qdpx", "timepoints", "length", "offset",
                              "validate", "project", "trajectories", "codes", "transcript", "hold", "names"),
                "sift": ("sift",), "trace": ("trace",)}
FAMILY_WORDS = ("search", "agents")


def owner_of(word: str) -> str | None:
    """The app whose command `word` is, or None for a word that is no app's command."""
    return next((app for app, words in OWN_COMMANDS.items() if word in words), None)


def elsewhere(given: list[str], app: str) -> str | None:
    """The refusal for a command another app has, naming that app and the command to run in its place,
    or None when `app` runs it: its own, or a folder."""
    if not given:
        return None
    owner = owner_of(given[0])
    if owner is None or owner in app_identity.served(app):
        return None
    them, us = app_identity.APPS[owner]["name"], app_identity.APPS[app]["name"]
    rest = given if owner == app_identity.DEFAULT else given[1:]
    return i18n.t("family_cli.elsewhere.is_s_not_s_run_it", given=given[0], them=them, us=us, list=shlex.join([owner, *rest]))


# the top's options that take a value, as `options` in `parser` adds them
VALUED = ("--project", "--root", "--config")


# the words that name a demo to `--demo` (demos, 3 November 2026): `ta` the thematic analysis demo, `ipa` the IPA one,
# which `--demo` alone names as ever
DEMO_WORDS = ("ipa", "ta")


def demo_words(given: list[str]) -> list[str]:
    """`given` with `--demo ta` and `--demo=ta` read as the thematic analysis demo, `--demo --demo-ta`, and `--demo ipa`
    or `--demo=ipa` as `--demo`, so a word after `--demo` that names no demo is the command as ever."""
    out, i = [], 0
    while i < len(given):
        word = given[i]
        said = word.split("=", 1)[1].strip().lower() if word.startswith("--demo=") else None
        if said is None and word == "--demo" and i + 1 < len(given) and given[i + 1].strip().lower() in DEMO_WORDS:
            said, i = given[i + 1].strip().lower(), i + 1
        if said is not None:
            out += ["--demo"] + (["--demo-ta"] if said == "ta" else [])
        else:
            out.append(word)
        i += 1
    return out


def demo_of(args):
    """The parsed words with `demo` naming the demo asked for: "ta" for the thematic analysis demo, True for the IPA
    demo, False for none."""
    if getattr(args, "demo_ta", False):
        args.demo = "ta"
    if hasattr(args, "demo_ta"):
        del args.demo_ta
    return args


def leading_last(given: list[str]) -> list[str]:
    """`given` with the options before its first word moved after the rest, each with its value."""
    i = 0
    while i < len(given) and given[i].startswith("-") and given[i] != "--":
        i += 2 if given[i] in VALUED else 1
    return given[i:] + given[:i] if 0 < i < len(given) else given


def args_for(given: list[str], app: str):
    """`given`, the words after the app's command, parsed for `app`: Idiograph's as ever, Sift's with the
    `sift` command's arguments at the top, a leading `sift`, the old form, taken as the same, Trace's
    likewise, and `search ... --folder <folder>` on either their Search. A refusal is Refused."""
    # the options before the command go after it, so `sift --config x search ...` is read as
    # `sift search ... --config x` is, Sift's and Trace's parsers taking them at either end
    given = demo_words(given)
    moved = leading_last(given)
    line = elsewhere(moved, app)
    if line:
        raise Refused(line)
    if app == app_identity.DEFAULT:
        return demo_of(parser().parse_args(given))
    given = moved
    if given[:1] == [app]:
        given = given[1:]
    folder = any(w == "--folder" or w.startswith("--folder=") for w in given)
    if given[:1] == ["search"] and folder:
        return parser(app, search=True).parse_args(given)
    # the app's agent log, `sift agents log` and `trace agents log`, every app's (siftlog, 3 November 2026)
    if given[:1] == ["agents"]:
        return agents_parser(app).parse_args(given[1:])
    # words after `search` with no folder, which are not one of the app's own acts after `search`, Sift's
    # `sift search plan` among them
    theirs = APP_COMMANDS.get(app)
    if theirs and theirs.get("search_refused") and given[:1] == ["search"] and len(given) > 1 \
            and given[1] not in theirs["search_acts"] and not given[1].startswith("-"):
        raise Refused(theirs["search_refused"])
    return parser(app).parse_args(given)


def agents_parser(app: str) -> argparse.ArgumentParser:
    """Sift's and Trace's `agents log`, the app's agent log read alone (siftlog, 3 November 2026), as Idiograph's
    own parser takes it: `--since` a day, `--limit` the newest, `--config` a settings file for a trial."""
    ap = argparse.ArgumentParser(prog=f"{app} agents", description="the app's record of agents: the agent log, "
                                                                   "each refusal of an agent, read alone")
    ap.set_defaults(command="agents", project=None, root=None, demo=False, config=None, json=False)
    acts = ap.add_subparsers(dest="act", required=True)
    x = acts.add_parser("log", help="the agent log, newest first")
    add_agents_log(x)
    x.add_argument("--json", action="store_true", default=argparse.SUPPRESS, help="exact output, as JSON")
    x.add_argument("--config", default=argparse.SUPPRESS, help="a settings file in place of the app's own, for a trial")
    return ap


def add_agents_log(x) -> None:
    """`agents log`'s own options, every app's."""
    x.add_argument("--since", default=None, help="from this day on, 2026-11-03")
    x.add_argument("--limit", type=int, default=None, help="the newest entries alone, this many")


def agents_log(args, allowed=None) -> tuple:
    """The agent log (agentlog and siftlog, 3 November 2026, see agent_log.py), newest first, every app's own
    beside its own settings: each refusal of an agent and each turn of Dangerously skip permissions, read alone.
    `allowed`, Idiograph's, the names of the projects agents may read: a refusal naming another, or none it could,
    comes back only in the count `closed`, never by its name. Sift and Trace tick no project for agents, so give
    none. `--since` a day, `--limit` the newest."""
    since = str(getattr(args, "since", None) or "").strip()
    if since and not re.fullmatch(r"\d{4}-\d{2}-\d{2}", since):
        raise Refused(i18n.t("family_cli.agents_log.since_not_a_date", since=since))
    limit = getattr(args, "limit", None)
    every = agent_log.read(config=getattr(args, "config", None))
    shown, closed = [], 0
    for e in every:
        if since and str(e.get("time") or "")[:10] < since:
            continue
        if allowed is not None and e.get("kind") != "switch" and (
                e.get("closed") or (e.get("project") and e["project"] not in allowed)):
            closed += 1
            continue
        shown.append(agent_log.public(e))
    if limit and limit > 0:
        shown = shown[:limit]
    answer = {"entries": shown, "closed": closed, "total": len(every)}
    if not every:
        return answer, [i18n.t("family_cli.agents_log.none_yet")]
    lines = [i18n.t("family_cli.agents_log.head", entries=i18n.t("family_cli.agents_log.n_entries", n=len(every)))]
    for e in shown:
        when = when_said(e["time"])
        if e["kind"] == "switch":
            lines.append(i18n.t("family_cli.agents_log.switch_on", when=when) if e["on"]
                         else i18n.t("family_cli.agents_log.switch_off", when=when))
            continue
        lines.append(i18n.t("family_cli.agents_log.entry", when=when, agent=e["agent"] or TOOL, call=e["call"],
                            line=e["line"]))
        if e["request"]:
            lines.append("  " + i18n.t("family_cli.agents_log.asked", request=e["request"]))
    if closed:
        lines.append(i18n.t("family_cli.agents_log.closed", n=closed))
    return answer, lines


# Each app's own command line, registered from its module (the family codebase's second build, 22 October
# 2026), so this file names no app's module: Sift's from apps/sift/sift_cli.py and Trace's from
# apps/trace/trace_cli.py, which `boot.load("cli")` at the foot of this file imports by its name, in the
# family's order, and Idiograph's, the family's first app's, from apps/idiograph/idiograph_cli.py (the
# fourth build), its commands at the top of `idiograph` (`register_own`).
APP_COMMANDS: dict = {}
OWN_APP: dict = {}
# a Search hit's opener by the screen it lands on, an app's own (see `search_hit`), and Idiograph's, whose
# hits are placed on a participant's board
SCREEN_HITS: dict = {}
CASE_HITS: dict = {}


def register(app: str, run, arguments, about: str, folder=None, found=None, screen=(), hit=None,
             search_refused: str = "", search_acts=(), plain=(), words=(), named=None) -> None:
    """`app`'s own command, the first word after its command, its name: `run`, which takes the parsed
    arguments and answers as a command does, `arguments`, which adds them to a parser, at the top of the
    app's own command, `about`, its words there, `folder` and `found`, its Search over one of its projects by its folder, the one refusing a folder
    that is not one with WorkbookError, `screen` and `hit`, a hit landing on its screen, or on each of its
    screens, given its opener, `search_refused`, the line for Search given words with no folder,
    `search_acts`, the words after `search` that are its own acts, never words to search for, and `plain`,
    the keys whose strings its answers keep plain, every other string marked (see `mark`), and for the agent
    log (siftlog, 3 November 2026) `words`, its own acts as a command line gives them, the only words of a
    refused command the log keeps besides flag names, and `named`, a project's name for the log given a
    folder an agent named. Called once, as its module is first imported."""
    APP_PLAIN[app] = frozenset(plain) | {"error", "lines"}
    APP_COMMANDS[app] = {"run": run, "arguments": arguments, "about": about, "folder": folder,
                         "found": found, "search_refused": search_refused, "search_acts": tuple(search_acts),
                         "words": tuple(words), "named": named}
    if hit is not None:
        for name in (screen,) if isinstance(screen, str) else screen:
            if name:
                SCREEN_HITS[name] = hit


def register_own(app: str, arguments, perform, about: str, hits: dict | None = None,
                 page_only: dict | None = None, where=None) -> None:
    """The family's first app's own commands at the top of its command line, Idiograph's (the fourth build,
    22 October 2026): `arguments`, which adds them under the parser's commands given the options every
    command takes and a write's, `perform`, which runs one on its parsed arguments and answers as `perform`
    does, `about`, the line the parser describes itself with, and `hits`, its Search's hits by the screen
    each lands on, each given the hit, the result, where it goes, the project it names, the cases read for the
    page, the project and the board asked for, and `page_only`, the commands an agent may ask for that only the app's
    window does, by their words, each with its line, and `where`, the project a refusal was asked of before one
    opened (the agent log, 3 November 2026). Called once, as its module is first imported."""
    OWN_APP[app] = {"arguments": arguments, "perform": perform, "about": about, "page_only": page_only or {},
                    "where": where}
    CASE_HITS.update(hits or {})


def perform(args) -> tuple[dict, list[str]]:
    """One command on its parsed arguments: its answer and its plain lines, or Refused. The
    server's settings it reads by are put back after it however it ends. What `main` prints, and
    what the MCP server hands an agent (see `mcp_server.py`). Sift's and Trace's commands run as they
    register, and Idiograph's, every other, as `register_own` gives them."""
    for word in ("note", "tool"):
        if not hasattr(args, word):
            setattr(args, word, "")
    if not hasattr(args, "dry_run"):
        args.dry_run = False
    if not hasattr(args, "project"):
        args.project = None
    refused = outside(args, srv.APP)
    if refused:
        raise Refused(refused)
    if args.command == "agents" and srv.APP != app_identity.DEFAULT:
        # Sift's or Trace's own agent log, beside its own settings (siftlog, 3 November 2026), and Idiograph's
        # among its own commands, which knows the projects agents may read
        return agents_log(args)
    if args.command in APP_COMMANDS:
        # an app's own command, Sift's or Trace's, needs no project of Distil's
        return APP_COMMANDS[args.command]["run"](args)
    if args.command == "search" and getattr(args, "folder", None):
        # a Sift or Trace project by its folder, as sift and trace take one, with no project of Distil's
        kept = (srv.CONFIG_PATH, srv.STATE_MEMORY)
        try:
            if getattr(args, "config", None):
                srv.CONFIG_PATH = Path(args.config).expanduser().resolve()
            srv.STATE_MEMORY = {"recent": []}
            return cmd_search_folder(args)
        finally:
            srv.CONFIG_PATH, srv.STATE_MEMORY = kept
    # the family's first app's own commands, Idiograph's, on its projects (see `register_own`)
    own = OWN_APP.get(app_identity.DEFAULT)
    if own is None:
        raise Refused(i18n.t("family_cli.perform.is_not_a_command_of_this", command=args.command))
    return own["perform"](args)


def first_start(app: str, words: list[str]) -> bool:
    """Sift's or Trace's first start, when its command line or MCP server runs before its window ever
    has: what it shares with Idiograph copied from Idiograph's files into its own, once, as the app's
    own start does (see `server.first_start_copy`), so `sift search run` finds his databases. A run
    given its own settings file, `--config`, is a trial and copies nothing. Answers whether it copied."""
    if app == app_identity.DEFAULT or any(w == "--config" or w.startswith("--config=") for w in words):
        return False
    try:
        return srv.first_start_copy(app)
    except (OSError, ValueError):
        return False


def outside(args, app: str) -> str | None:
    """The refusal for a command whose app this run does not serve, or None. The parser offers only the
    app's own, and this holds it for the MCP server's calls too, so an agent given Sift or Trace never
    reaches a project's participants."""
    command = getattr(args, "command", None)
    if command == "search":
        owner = app_identity.DEFAULT if not getattr(args, "folder", None) else None
    else:
        owner = owner_of(command or "")
    if owner is None or owner in app_identity.served(app):
        return None
    them, us = app_identity.APPS[owner]["name"], app_identity.APPS[app]["name"]
    if command == "search":
        return i18n.t("family_cli.outside.s_search_reads_one_project_by", us=us, app=app)
    return i18n.t("family_cli.outside.is_s_not_s", command=command, them=them, us=us)


def main(argv: list[str] | None = None, out=None, err=None) -> int:
    """Run one command and answer in plain text, or JSON with `--json`. A refusal is one line a
    reason, and exits 1, having written nothing."""
    out = out or sys.stdout
    err = err or sys.stderr
    given = list(sys.argv[1:] if argv is None else argv)
    # `--app sift` or `--app trace`, anywhere, reads and writes that app's settings (see `app_identity`),
    # and with none it is this run's own app, Idiograph's from source
    try:
        app = app_identity.asked(given) or srv.APP
    except app_identity.UnknownApp as exc:
        err.write(f"{exc}\n")
        return 2
    held = srv.app_held()
    srv.use_app(app)
    try:
        words = app_identity.strip_app(given)
        agent_log.begin()
        bare = argparse.Namespace(json="--json" in words)
        # a command the window alone does, which an agent asked for by its words, is refused in one line saying so
        own_line = page_only(words, app)
        if own_line:
            code = refuse([own_line], bare, out, err)
            logged(app, words, None, [own_line], "page_only")
            return code
        said = io.StringIO()
        try:
            with contextlib.redirect_stderr(said):
                args = args_for(words, app)
        except SystemExit as exc:
            sys.stderr.write(said.getvalue())
            if exc.code:
                logged(app, words, None, *parse_refusal(said.getvalue(), words, app))
            return int(exc.code or 0)
        except Refused as exc:
            code = refuse(exc.lines, bare, out, err)
            logged(app, words, None, exc.lines, "no_command")
            return code
        sys.stderr.write(said.getvalue())
        first_start(app, words)
        try:
            answer, lines = perform(args)
        except Refused as exc:
            code = refuse(exc.lines, args, out, err)
            logged(app, words, args, exc.lines, "")
            return code
        except (WorkbookError, FileNotFoundError, OSError) as exc:
            code = refuse([str(exc)], args, out, err)
            logged(app, words, args, [str(exc)], getattr(exc, "code", ""))
            return code
        out.write(dumps(answer) + "\n" if args.json else scrub("\n".join(lines)) + "\n")
        return 0
    finally:
        srv.app_back(held)


# ------------------------------------------------------------------ the agent log

# the arguments that name where a command works or who asks, which the log keeps or leaves out on purpose, so
# they are never taken out of a refusal's line as a value the agent handed in (see `agent_log.scrubbed`)
NAMES = frozenset(("command", "act", "project", "root", "demo", "config", "json", "case", "board", "sheet",
                   "timepoint", "tool", "dry_run", "lpets", "app"))


def lead_words(words: list[str], app: str | None = None) -> list[str]:
    """The command's own words as an agent gave them, the first, and the second where the first is a command of
    the family's, never a value. Sift's and Trace's take a folder first, so theirs are their own acts alone,
    wherever they stand (see `app_lead`)."""
    if app and app != app_identity.DEFAULT:
        return app_lead(app, words)
    lead = []
    for w in leading_last(list(words)):
        if w.startswith("-"):
            break
        lead.append(w)
    known = (owner_of(lead[0]) is not None or lead[0] in FAMILY_WORDS) if lead else False
    return lead[:2] if known else lead[:1]


def app_lead(app: str, words: list[str]) -> list[str]:
    """Sift's or Trace's command words as an agent gave them for the agent log (siftlog, 3 November 2026): `agents
    log`, `search` given a folder, or the app's own acts as it registered them (`register`'s `words`), `search plan`
    or `list`, never a folder, a record, a document or a word searched for."""
    rest = leading_last(list(words))
    if rest[:1] == [app]:
        rest = rest[1:]
    plain = []
    for w in rest:
        if w == "--":
            break
        if not w.startswith("-"):
            plain.append(w)
    if plain[:1] == ["agents"]:
        return ["agents", *[w for w in plain[1:2] if w == "log"]]
    if plain[:1] == ["search"] and any(w == "--folder" or w.startswith("--folder=") for w in rest):
        return ["search"]
    vocab = APP_COMMANDS.get(app, {}).get("words") or ()
    return [w for w in plain if w in vocab][:2]


def app_op(app: str, head: list[str]) -> str:
    """The op of Sift's or Trace's command words as the log keeps it, as its MCP tool names it: `sift list` for
    `sift <folder> list`, `sift plan` for `sift search plan <folder>`, `search`, `agents log`, or the app's name."""
    if head[:2] == ["agents", "log"] or head == ["search"]:
        return " ".join(head)
    return f"{app} {head[-1]}" if head else app


def app_project(app: str, candidates) -> None:
    """The project a refusal of Sift or Trace was asked of, into `agent_log.HERE`: the first of `candidates` that
    is a folder, by its project's name as the app's `named` gives it, else the folder's own name. Never a path."""
    named = APP_COMMANDS.get(app, {}).get("named")
    for c in candidates:
        if not isinstance(c, str) or not c.strip():
            continue
        try:
            folder = Path(c).expanduser()
            if folder.is_dir():
                agent_log.at_project(named(folder) if named else folder.resolve().name)
                return
        except Exception:
            continue


def flag_value(words: list[str], flag: str) -> str:
    """The value given to `flag` in `words`, `--note x` or `--note=x`, or ""."""
    for i, w in enumerate(words):
        if w == flag and i + 1 < len(words):
            return str(words[i + 1])
        if w.startswith(flag + "="):
            return w.split("=", 1)[1]
    return ""


def page_only(words: list[str], app: str) -> str:
    """The line refusing a command only the app's window does, an agent asking for it by its words, or ""."""
    lead = tuple(lead_words(words))
    table = OWN_APP.get(app, {}).get("page_only") or {}
    line = table.get(lead) or table.get(lead[:1]) or ""
    return line() if callable(line) else line


def parse_refusal(said: str, words: list[str], app: str | None = None) -> tuple[list[str], str]:
    """A refusal of the parser as the log keeps it: no such command, or a command in a shape it does not take, each
    in a plain line (siftlog, 3 November 2026, the coordinator: never the parser's own words). Sift's and Trace's
    take a folder first, so a word they lack is a choice they don't have, never a command named."""
    if app and app != app_identity.DEFAULT:
        if "invalid choice" in said:
            return [i18n.t("family_cli.parse.no_choice")], "no_command"
        return [parse_said(said)], "invalid"
    lead = lead_words(words, app)
    if "invalid choice" in said or not lead:
        return [i18n.t("family_cli.no_such_command", words=" ".join(lead) or "idiograph")], "no_command"
    return [parse_said(said)], "invalid"


def parse_said(said: str) -> str:
    """The parser's refusal of a command's shape in a plain line: an option it doesn't take, by its flag names alone,
    something it needs and was not given, by its names, a choice it doesn't have, or any other shape."""
    tail = said.strip().splitlines()[-1].split("error: ", 1)[-1] if said.strip() else ""
    if tail.startswith("unrecognized arguments:"):
        flags = [w.split("=", 1)[0] for w in tail.split(":", 1)[1].split() if w.startswith("-") and len(w) > 1]
        if flags:
            return i18n.t("family_cli.parse.no_option", flags=", ".join(dict.fromkeys(flags)))
    if tail.startswith("the following arguments are required:"):
        return i18n.t("family_cli.parse.missing", names=tail.split(":", 1)[1].strip())
    took = re.match(r"argument (\S+?)(?:/\S+)?: expected (?:one|at least one) argument", tail)
    if took:
        return i18n.t("family_cli.parse.missing", names=took.group(1))
    if "invalid choice" in tail:
        return i18n.t("family_cli.parse.no_choice")
    return i18n.t("family_cli.parse.shape")


def logged(app: str, words: list[str], args, lines: list[str], code: str) -> None:
    """A refusal of an agent's command into the agent log (see agent_log.py), each app's into its own beside its
    own settings (Sift's and Trace's since siftlog, 3 November 2026). Its values never: every word the agent handed
    in that is not a name is taken out of the line, and the call keeps the command's words and flag names alone,
    Sift's and Trace's their acts, never a folder, a record or a document."""
    own = app == app_identity.DEFAULT
    try:
        flags = [w for w in words if w.startswith("-") and w.split("=", 1)[0] not in ("--config", "--json")]
        if args is not None and getattr(args, "command", None):
            head = [args.command] + ([args.act] if getattr(args, "act", None) else [])
            head = head if own else lead_words(words, app)
            given = vars(args)
            # Sift's `search` and `zotero` stand where a folder does, words of the command, never values
            values = [v for v in agent_log.strings({k: v for k, v in given.items() if k not in NAMES}) if v not in head]
            agent, request = str(given.get("tool") or ""), str(given.get("note") or "")
            folders = [given.get("folder"), given.get("rec_id")]
        else:
            head = lead_words(words, app)
            agent, request = flag_value(words, "--tool"), flag_value(words, "--note")
            values = [w.split("=", 1)[-1] for w in words if w not in head and not (w.startswith("-") and "=" not in w)]
            folders = [w for w in words if not w.startswith("-")]
        line = " ".join(str(x) for x in lines if str(x))
        if not code:
            code = "not_allowed" if own and line == _private() else "refused"
        if not agent_log.HERE["project"] and not agent_log.HERE["closed"]:
            if own:
                where_asked(flag_value(words, "--project") or None, flag_value(words, "--root") or None,
                            demo_asked(words), flag_value(words, "--config") or None)
            else:
                app_project(app, folders)
        entry = agent_log.entry(
            via="cli", agent=agent, request=request, values=values, code=code, line=scrub(line),
            call=agent_log.call_of([app, *head, *flags], len(head) + 1),
            op=" ".join(head) if own else app_op(app, head),
            project=agent_log.HERE["project"], closed=agent_log.HERE["closed"])
        config = getattr(args, "config", None) if args is not None else flag_value(words, "--config")
        agent_log.add(entry, agent_log.place(config or None))
    except Exception:            # never a refusal of its own: the log is a record, and the command's answer stands
        return


def demo_asked(words: list[str]):
    """The demo a command's words name, as `demo_of` reads it: "ta", True or False."""
    said = demo_words([str(w) for w in words])
    return "ta" if "--demo-ta" in said else "--demo" in said


def where_asked(project, root, demo, config) -> None:
    """The project a refusal was asked of before any opened, a parser's or an unknown tool's, through the app's own
    hook (`register_own`'s `where`), into `agent_log.HERE`: by its name where agents may read it, else by a count."""
    own = OWN_APP.get(app_identity.DEFAULT, {}).get("where")
    if own is None:
        return
    try:
        name, closed = own(project, root, demo, config)
    except Exception:
        return
    if closed:
        agent_log.at_closed(closed)
    elif name:
        agent_log.at_project(name)


def _private() -> str:
    """The line refusing a project agents may not read, Idiograph's, or "" before its module is loaded."""
    try:
        return i18n.t("cli.said.private")
    except Exception:
        return ""


def refuse(lines: list[str], args, out, err) -> int:
    if getattr(args, "json", False):
        out.write(dumps({"error": " ".join(lines), "lines": lines}) + "\n")
    else:
        err.write(scrub("\n".join(lines)) + "\n")
    return 1


def run(argv: list[str]) -> tuple[int, str, str]:
    """One command run here, for the suite: its exit code, what it printed and what it said went
    wrong."""
    out, err = io.StringIO(), io.StringIO()
    code = main(argv, out, err)
    return code, out.getvalue(), err.getvalue()


def script() -> int:
    """The command line run as a script, from the root's cli.py (see `boot.shim`): its answers in UTF-8 to an
    agent reading through a pipe, whatever the system's code page."""
    app_folders.utf8_streams()
    return main()


# each app's own commands registered, Idiograph's from apps/idiograph/idiograph_cli.py, Sift's from
# apps/sift/sift_cli.py and Trace's from apps/trace/trace_cli.py, each imported by its name (see `register`)
boot.load("cli")
