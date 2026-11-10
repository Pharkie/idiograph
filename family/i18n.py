"""The text layer (i18ncore, 28 October 2026): every word the page shows comes from one place, a catalogue of
messages by key, and this module is its Python side, the server's `t()` and the page's markers filled.

The catalogue is plain JSON, one file per area per language, `static/i18n/<language>/<area>.json` in the family's
folder and in each app's (`family/static/i18n/en/shell.json`, `apps/idiograph/static/i18n/en/statements.json`),
merged at load. Every key in a file starts with the file's name and a dot (`shell.update.ready` in `shell.json`), so
two files never hold one key and two builders moving different areas never edit one file. A message is a whole
sentence with named slots, `"{app} {version} is ready."`, or, for a count, an object with a form for each of the
language's plural categories, `{"one": "{n} statement", "other": "{n} statements"}`, picked by the slot `n`. A
key ending `_html` holds markup and goes into the page as it is; every other message is text, escaped.

English (`en`) is the base and British. Another language, or an overlay such as `en-US`, is a folder of files of
the same shape that replaces whole messages by key: a lookup takes the most specific folder that has the key,
then the less specific, then English, then the key itself, named once on stderr. The language is `language` in
the settings, a tag such as `es` or `en-US`, set by the Language row under Settings, General, and when that is
unset or empty, the computer's own. The first overlay is `en-US`, American English (i18nus, 28 October 2026).

The page gets the merged catalogue inline (`fill`, where `<!--i18n-->` stands in page.html) and its markers,
`{{page.settings.title}}`, filled when the server puts the page together, so the first paint is already in the
chosen language. The scripts' side is `static/i18n.js`.

A project's method (tadraw, 31 October 2026, thematic analysis's phase one) is the one key that swaps the words of
its method's things: IPA's participant, experiential statement, PET and GET, the base's, or thematic analysis's code,
coded extract and theme. A method other than IPA is a folder beside its language's, `<language>.<method>`
(`en.ta`), of files of the same shape holding the whole sentences that method says otherwise. A lookup for a
method takes its folders first, most specific language first, then the language's own chain, so a key the method
leaves alone reads as IPA's. The page gets each method's messages beside the base's (`script`), and the scripts
pick by the project in front.
"""

from __future__ import annotations

import contextlib
import contextvars
import html
import json
import locale
import os
import re
import sys
from pathlib import Path

import boot

# the base language, whose files hold every key, and the locale its dates and plurals are written in
BASE = "en"
LOCALE_OF = {"en": "en-GB"}
# a language's tag as the settings hold it, `es`, `en-US` or `pt-BR`
TAG = re.compile(r"^[a-z]{2,3}(?:-[A-Za-z0-9]{2,8})*$")
# a key: lowercase words and digits joined by dots, its first word its file's name
KEY = re.compile(r"^[a-z][a-z0-9_]*(?:\.[a-z0-9_]+)+$")
SLOT = re.compile(r"\{(\w+)\}")
# a marker in the page's markup, filled by `fill`
MARK = re.compile(r"\{\{([a-z][a-z0-9_]*(?:\.[a-z0-9_]+)+)\}\}")
# where the page takes the catalogue for its scripts
SCRIPT_MARK = "<!--i18n-->"
# a language that stands in for the computer's own, which the suite sets to en-GB so its checks read British
# English on a computer in any language (i18nus, 28 October 2026)
COMPUTER_STANDIN = "IDIOGRAPH_COMPUTER_LANGUAGE"
# the categories a language's counts fall into (CLDR's rules, integers alone), the rest `other`
# A project's methods (tadraw, 31 October 2026): IPA, the base, whose words are the catalogue's own, and thematic
# analysis, whose words are in `<language>.ta` folders. A project file with no method is IPA's
METHODS = ("ipa", "ta")
BASE_METHOD = "ipa"
# The method a request or a command is in (tagaps, 1 November 2026): the project it names, set for its run by
# `in_method`, so every line the server says in a thematic analysis project, a refusal, a status line, an export's
# headings or a print view's, reads in that method's words without each call naming it. IPA's when none is set
NOW_METHOD: contextvars.ContextVar = contextvars.ContextVar("i18n_method", default=None)
PLURAL_RULES = {
    "en": lambda n: "one" if n == 1 else "other",
    "es": lambda n: "one" if n == 1 else "other",
    "hi": lambda n: "one" if n in (0, 1) else "other",
}

# Formats apart from the language (fmtcore, 28 October 2026, Adam's B of that day): the order a date is written
# in, the clock a time of day is written by and where a number's commas and points go, each chosen under
# Settings, Language and formats, and each "" for the computer's own. The settings hold them as `formats`, one
# object beside `language`, each key one of its choices here. The month's name still comes from the language.
FORMATS = {
    "dates": ("dmy", "mdy", "ymd"),            # 28 Oct 2026, Oct 28, 2026, 2026-10-28
    "time": ("24", "12"),                      # 14:05, 2:05 pm
    "numbers": ("comma", "point", "space", "apostrophe"),  # 1,234.5, 1.234,5, 1 234,5, 1'234.5
}
# The computer's own formats as the window reads them on the Mac and on Windows, handed to the server it starts:
# a small JSON of the computer's own writing of 28 October 2026, of 14:05 and of 1234.5, `{"date": "28/10/2026",
# "time": "14:05", "number": "1,234.50"}`, each mapped to the nearest choice (`computer_formats`). The suite sets
# it as it sets the computer's language. With none, as in a browser, the page writes as its language's locale does
COMPUTER_FORMATS = "IDIOGRAPH_COMPUTER_FORMATS"

# Set by the server: the language a run is in, read afresh from its settings, and the folders its catalogue is
# read from, the apps it serves and the family's (boot.roots), and the formats its settings choose
LANGUAGE = lambda: ""  # noqa: E731
ROOTS = lambda: boot.roots()  # noqa: E731
CHOSEN_FORMATS = lambda: {}  # noqa: E731

_COMPUTER: list = []
_MISSED: set = set()
_READ: dict = {}


def normal(tag: str | None) -> str:
    """A tag as the catalogue's folders are named, `en_GB.UTF-8` as `en-GB`, or "" for one that is no language."""
    tag = str(tag or "").strip().split(".", 1)[0].split("@", 1)[0].replace("_", "-")
    if not tag or tag in ("C", "POSIX"):
        return ""
    head, *rest = tag.split("-")
    tag = "-".join([head.lower(), *[(r.upper() if len(r) == 2 else r) for r in rest]])
    return tag if TAG.match(tag) else ""


def computer_language() -> str:
    """The computer's own language, read once a run: the Mac's first preferred language, Windows' user locale,
    else the environment's (LC_ALL, LC_MESSAGES, LANG) or Python's locale, English when none says.
    IDIOGRAPH_COMPUTER_LANGUAGE, where it is set, stands in for all of them."""
    if _COMPUTER:
        return _COMPUTER[0]
    found = normal(os.environ.get(COMPUTER_STANDIN))
    if not found:
        try:
            if sys.platform == "darwin":
                import plistlib
                prefs = Path.home() / "Library" / "Preferences" / ".GlobalPreferences.plist"
                with prefs.open("rb") as fh:
                    langs = plistlib.load(fh).get("AppleLanguages") or []
                found = normal(langs[0]) if langs else ""
            elif sys.platform == "win32":
                import ctypes
                buf = ctypes.create_unicode_buffer(85)
                if ctypes.windll.kernel32.GetUserDefaultLocaleName(buf, 85):
                    found = normal(buf.value)
        except Exception:  # noqa: BLE001 - any failure reads as no answer, and the next way is asked
            found = ""
    if not found:
        for name in ("LC_ALL", "LC_MESSAGES", "LANG"):
            found = normal(os.environ.get(name))
            if found:
                break
    if not found:
        try:
            found = normal(locale.getlocale()[0])
        except (ValueError, TypeError):
            found = ""
    _COMPUTER.append(found or BASE)
    return _COMPUTER[0]


def chosen(cfg: dict | None) -> str:
    """The language the settings choose, `language` there, or the computer's when that is unset or empty."""
    tag = normal((cfg or {}).get("language"))
    return tag or computer_language()


def formats_of(held) -> dict:
    """The formats a settings file holds, each of `FORMATS`' keys one of its choices or "" for the computer's own,
    whatever else the file has."""
    held = held if isinstance(held, dict) else {}
    return {name: (held.get(name) if held.get(name) in choices else "") for name, choices in FORMATS.items()}


def format_refused(sent) -> str | None:
    """Why a `formats` sent to the settings is refused, naming the first key or choice that is not one, or None
    when every key is one of `FORMATS`' and each value one of its choices or ""."""
    if not isinstance(sent, dict):
        return "formats"
    for name, value in sent.items():
        if name not in FORMATS:
            return name
        if value != "" and value not in FORMATS[name]:
            return f"{name} {value}"
    return None


def nearest_date(text: str) -> str:
    """The date choice nearest a computer's own writing of 28 October 2026: the year first is 2026-10-28, the
    month before the day Oct 28, 2026, else 28 Oct 2026. "" when the day or the year cannot be found."""
    text = str(text or "")
    day = text.find("28")
    year = text.find("2026")
    if year < 0:
        # a two-digit year, the 26 that is not the 28's
        year = next((m.start() for m in re.finditer(r"(?<!\d)26(?!\d)", text)), -1)
    if day < 0 or year < 0:
        return ""
    month = next((m.start() for m in re.finditer(r"(?<!\d)10(?!\d)", text)), -1)
    if month < 0:
        month = next((m.start() for m in re.finditer(r"[^\W\d_]+", text)), -1)
    if year < day and (month < 0 or year < month):
        return "ymd"
    return "mdy" if 0 <= month < day else "dmy"


def nearest_time(text: str) -> str:
    """The clock nearest a computer's own writing of 14:05: 24-hour where it writes 14, else 12-hour."""
    text = str(text or "")
    if not re.search(r"\d", text):
        return ""
    return "24" if "14" in text else "12"


def nearest_number(text: str) -> str:
    """The number choice nearest a computer's own writing of 1234.5: a decimal comma with points between the
    thousands is 1.234,5, with a space or none 1 234,5, a decimal point with an apostrophe 1'234.5, and any other
    1,234.5. "" when the number's digits are not found."""
    found = re.search(r"1(\D?)234(\D)5", str(text or ""))
    if not found:
        return ""
    group, decimal = found.group(1), found.group(2)
    if decimal == ",":
        return "point" if group == "." else "space"
    return "apostrophe" if group in ("'", "’") else "comma"


def computer_formats(env=None) -> dict:
    """The computer's own formats, each mapped to its nearest choice, from what the window hands the server in
    IDIOGRAPH_COMPUTER_FORMATS, read afresh each time, or each "" where it says nothing, as in a browser."""
    try:
        said = json.loads((os.environ if env is None else env).get(COMPUTER_FORMATS) or "{}")
    except ValueError:
        said = {}
    said = said if isinstance(said, dict) else {}
    return {"dates": nearest_date(said.get("date")), "time": nearest_time(said.get("time")),
            "numbers": nearest_number(said.get("number"))}


def folders(roots=None) -> list[Path]:
    """Each folder holding a catalogue, `static/i18n` under each of `roots` that has one, in their order."""
    return [base for root in (ROOTS() if roots is None else roots) if (base := Path(root) / "static" / "i18n").is_dir()]


def languages(roots=None) -> list[str]:
    """Every language and overlay with a folder, `en` first."""
    found = {p.name for base in folders(roots) for p in base.iterdir() if p.is_dir() and normal(p.name) == p.name}
    return sorted(found, key=lambda tag: (tag != BASE, tag))


def chain(tag: str | None, roots=None) -> list[str]:
    """The folders a lookup in `tag` takes, most specific first and English last: `en-US`, `en` for en-US,
    `es-MX`, `es`, `en` for es-MX, each only where it has a folder, English always."""
    have = set(languages(roots))
    parts = (normal(tag) or BASE).split("-")
    out = [t for t in ("-".join(parts[:i]) for i in range(len(parts), 0, -1)) if t in have and t != BASE]
    return out + [BASE]


def locale_of(tag: str | None, roots=None) -> str:
    """The locale the page writes dates, lists and plurals in: that of the most specific folder the lookup
    takes, English's being British, so the computer's en-US reads as en-GB until an en-US overlay is there."""
    first = chain(tag, roots)[0]
    return LOCALE_OF.get(first, first)


def files(tag: str, roots=None) -> list[Path]:
    """One language's or overlay's files, every folder's, in the order they are merged."""
    return [p for base in folders(roots) for p in sorted((base / tag).glob("*.json"))]


def read_file(path: Path) -> dict:
    """One file's messages, read afresh only when it changed."""
    stamp = path.stat().st_mtime_ns
    held = _READ.get(path)
    if held and held[0] == stamp:
        return held[1]
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"{path} is not one JSON object")
    _READ[path] = (stamp, data)
    return data


def own(tag: str, roots=None) -> dict:
    """The messages of one language's or overlay's folder alone, its files merged."""
    out: dict = {}
    for path in files(tag, roots):
        out.update(read_file(path))
    return out


def long_text(path, tag: str | None = None) -> Path:
    """A long text's file in the run's language (or `tag`): the guidance rails and What's new are whole files, not
    catalogue keys, so a language's own sits beside the English one with the tag before the suffix
    (`guidance.es.md` beside `guidance.md`, `whats-new.es.md` beside `whats-new.md`). The most specific tag that has
    a file wins (`es-MX` reads `guidance.es-MX.md`, then `guidance.es.md`) and English, the file itself, is the
    fallback, so a language with no file shows English."""
    path = Path(path)
    parts = (normal(LANGUAGE() if tag is None else tag) or BASE).split("-")
    for i in range(len(parts), 0, -1):
        lang = "-".join(parts[:i])
        if lang == BASE:
            break
        found = path.with_name(f"{path.stem}.{lang}{path.suffix}")
        if found.is_file():
            return found
    return path


def method_of(given) -> str:
    """A method as a project file or a call gives it, one of METHODS, IPA for none or anything else."""
    given = str(given or "").strip().lower()
    return given if given in METHODS else BASE_METHOD


@contextlib.contextmanager
def in_method(method):
    """A run in `method`'s words, each `t` with no method of its own reading through it, the method before put
    back after. None leaves the method as it is."""
    if method is None:
        yield
        return
    token = NOW_METHOD.set(method_of(method))
    try:
        yield
    finally:
        NOW_METHOD.reset(token)


def method_now() -> str:
    """The method the run is in, IPA's when none is set (see `in_method`)."""
    return method_of(NOW_METHOD.get())


def method_chain(tag: str | None, method: str, roots=None) -> list[str]:
    """The method's own folders a lookup in `tag` takes, most specific first (`en-US.ta`, `en.ta`), each only
    where it is there, none for IPA, whose words are the language's own."""
    if method_of(method) == BASE_METHOD:
        return []
    have = {p.name for base in folders(roots) for p in base.iterdir() if p.is_dir()}
    return [f"{lang}.{method}" for lang in chain(tag, roots) if f"{lang}.{method}" in have]


def method_messages(method: str, tag: str | None = None, roots=None) -> dict:
    """The messages a method says otherwise in `tag`, its folders merged, the most specific language's last, and
    nothing for IPA."""
    out: dict = {}
    for step in reversed(method_chain(tag if tag is not None else LANGUAGE(), method, roots)):
        out.update(own(step, roots))
    return out


def messages(tag: str | None = None, roots=None, method: str | None = None) -> dict:
    """Every message in `tag`, English's under the most specific folder's, so a key missing from a language
    reads in English, and with a method its own sentences over them."""
    tag = tag if tag is not None else LANGUAGE()
    out: dict = {}
    for step in reversed(chain(tag, roots)):
        out.update(own(step, roots))
    if method:
        out.update(method_messages(method, tag, roots))
    return out


def plural(tag: str, n) -> str:
    """The plural category `n` falls in for a language, `other` for a language with no rule here."""
    rule = PLURAL_RULES.get((normal(tag) or BASE).split("-")[0], PLURAL_RULES[BASE])
    try:
        return rule(abs(float(n)) if not float(n).is_integer() else abs(int(float(n))))
    except (TypeError, ValueError):
        return "other"


def form(message, vals: dict | None, tag: str) -> str:
    """A message with its slots filled: for a count, the form for the category `n` falls in (or `other`), and
    each `{name}` the value of that name, a slot with no value left as it stands."""
    if isinstance(message, dict):
        cat = plural(tag, (vals or {}).get("n", 0))
        message = message.get(cat, message.get("other", ""))
    text = str(message)
    if vals:
        text = SLOT.sub(lambda m: str(vals[m.group(1)]) if m.group(1) in vals else m.group(0), text)
    return text


def missing(key: str) -> str:
    """A key no catalogue has: the key itself, named once on stderr."""
    if key not in _MISSED:
        _MISSED.add(key)
        print(f"i18n: no message for {key}", file=sys.stderr)
    return key


def t(key: str, vals: dict | None = None, *, lang: str | None = None, roots=None, method: str | None = None,
      **slots) -> str:
    """The message `key` in the run's language (or `lang`), its slots filled from `vals` and `slots`, in the words
    of `method` where it says the sentence otherwise, or of the method the run is in (`in_method`)."""
    tag = lang if lang is not None else LANGUAGE()
    found = messages(tag, roots, method if method is not None else NOW_METHOD.get()).get(key)
    if found is None:
        return missing(key)
    return form(found, {**(vals or {}), **slots} or None, locale_of(tag, roots))


def script(tag: str | None = None, roots=None, marked: dict | None = None) -> str:
    """The catalogue as the page's scripts take it, one inline script setting I18N: the language, its locale,
    the locale the computer's own language reads in (`computer`, which Settings' Language row names), the
    formats the settings choose and the computer's own (`formats`, `computer_formats`, each "" for none),
    every message, and `methods`, each method's own sentences by key (thematic analysis's, tadraw), with
    `marked`, the markup's words a method says otherwise, each key with the slots it was filled with, which the
    scripts word again for the project in front. `<` is written as its escape so no message can close the
    script."""
    tag = tag if tag is not None else LANGUAGE()
    data = {"language": normal(tag) or BASE, "locale": locale_of(tag, roots),
            "computer": locale_of(computer_language(), roots), "formats": formats_of(CHOSEN_FORMATS()),
            "computer_formats": computer_formats(), "messages": messages(tag, roots),
            "methods": {m: method_messages(m, tag, roots) for m in METHODS if m != BASE_METHOD},
            "marked": marked or {}}
    text = json.dumps(data, ensure_ascii=False, separators=(",", ":")).replace("<", "\\u003c")
    return f"<script>var I18N = {text};</script>"


def fill(page: str, tag: str | None = None, roots=None, slots: dict | None = None) -> str:
    """A page with each `{{key}}` marker its message, its slots filled from `slots` (the server gives `app`, the
    app's name), escaped unless the key ends `_html`, and the catalogue where `<!--i18n-->` stands. A marker
    whose words a method says otherwise is named in the catalogue's `marked`, so the page can word it again."""
    tag = tag if tag is not None else LANGUAGE()
    found = messages(tag, roots)
    varied = set().union(*(method_messages(m, tag, roots) for m in METHODS if m != BASE_METHOD))
    marked: dict = {}

    def one(m: re.Match) -> str:
        key = m.group(1)
        if key not in found:
            return html.escape(missing(key))
        text = form(found[key], slots, tag)
        if key in varied and not key.endswith("_html"):
            marked[key] = {k: str(v) for k, v in (slots or {}).items()}
        # an apostrophe stays as it is, every attribute in the page being in double quotes
        return text if key.endswith("_html") else html.escape(text, quote=False).replace('"', "&quot;")

    page = MARK.sub(one, page)
    if SCRIPT_MARK in page:
        page = page.replace(SCRIPT_MARK, script(tag, roots, marked), 1)
    return page
