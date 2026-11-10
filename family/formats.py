#!/usr/bin/env python3
"""Dates and lists the server writes for a person to read: Python's tDate, `date_words`, in the formats Settings,
Language and formats chooses (fmtsweep, 28 October 2026), and its tList, `list_words`, in the run's language
(i18ncodes, 31 October 2026), each as the page's own writes them.

A date: a print view's head and its marked-complete line, and the interviewer notes file's Exported on. The order of
the day, the month and the year is the setting's (`formats` in the settings, as the page's tDate reads it), else the
computer's own as the window hands it to the server, else the language's own. The month's name is the language's,
from `dates.json` in its catalogue, and the sentence that puts the three together is the language's too, so another
language words them its own way.

A list: the names, labels and counts a refusal or a line of the server's joins, "Wren, Ash and Rowan" in British
English and "Wren, Ash, and Rowan" in American, as the page's tList (Intl.ListFormat) joins them. The patterns are
CLDR's for the language, from `lists.json` in its catalogue, never ", ".join and " and " in code.

What is never written here: the saved files and agents' --json (ISO), backups' and file names' own forms, a
revision's name or provenance already written into a file, and the command line's and MCP's human lines, which stay
English since agents read them."""

from __future__ import annotations

from datetime import date, datetime

import i18n

# Each format's choice where neither the settings nor the computer say one, by the locale the language reads in,
# as the page's Intl writes that locale: British English and any language with no line here 28 October 2026
OWN = {"en-US": {"dates": "mdy", "time": "12"}}
DEFAULT = {"dates": "dmy", "time": "24", "numbers": "comma"}

# the months' names in the run's language, a key a month so the catalogue check finds each one used
LONG = {
    1: lambda lang=None: i18n.t("dates.month.january", lang=lang),
    2: lambda lang=None: i18n.t("dates.month.february", lang=lang),
    3: lambda lang=None: i18n.t("dates.month.march", lang=lang),
    4: lambda lang=None: i18n.t("dates.month.april", lang=lang),
    5: lambda lang=None: i18n.t("dates.month.may", lang=lang),
    6: lambda lang=None: i18n.t("dates.month.june", lang=lang),
    7: lambda lang=None: i18n.t("dates.month.july", lang=lang),
    8: lambda lang=None: i18n.t("dates.month.august", lang=lang),
    9: lambda lang=None: i18n.t("dates.month.september", lang=lang),
    10: lambda lang=None: i18n.t("dates.month.october", lang=lang),
    11: lambda lang=None: i18n.t("dates.month.november", lang=lang),
    12: lambda lang=None: i18n.t("dates.month.december", lang=lang),
}
SHORT = {
    1: lambda lang=None: i18n.t("dates.mon.jan", lang=lang),
    2: lambda lang=None: i18n.t("dates.mon.feb", lang=lang),
    3: lambda lang=None: i18n.t("dates.mon.mar", lang=lang),
    4: lambda lang=None: i18n.t("dates.mon.apr", lang=lang),
    5: lambda lang=None: i18n.t("dates.mon.may", lang=lang),
    6: lambda lang=None: i18n.t("dates.mon.jun", lang=lang),
    7: lambda lang=None: i18n.t("dates.mon.jul", lang=lang),
    8: lambda lang=None: i18n.t("dates.mon.aug", lang=lang),
    9: lambda lang=None: i18n.t("dates.mon.sep", lang=lang),
    10: lambda lang=None: i18n.t("dates.mon.oct", lang=lang),
    11: lambda lang=None: i18n.t("dates.mon.nov", lang=lang),
    12: lambda lang=None: i18n.t("dates.mon.dec", lang=lang),
}


def chosen(kind: str, lang: str | None = None) -> str:
    """The choice in force for `kind` (`dates`, `time`, `numbers`): the settings', else the computer's own, else
    the language's own. With `lang`, a fixed language a file keeps (a revision's English name), that language's
    own alone, so what is kept never follows a person's settings."""
    if lang is not None:
        return OWN.get(i18n.locale_of(lang), {}).get(kind) or DEFAULT[kind]
    held = i18n.formats_of(i18n.CHOSEN_FORMATS()).get(kind) or i18n.computer_formats().get(kind)
    if held:
        return held
    return OWN.get(i18n.locale_of(i18n.LANGUAGE()), {}).get(kind) or DEFAULT[kind]


def date_words(when: date | datetime, short: bool = False, lang: str | None = None) -> str:
    """A day in the dates format: 28 October 2026, October 28, 2026 or 2026-10-28, and with `short` 4 Oct 2026,
    Oct 4, 2026 or 2026-10-04. A datetime is read as it is, with no time zone brought into it. `lang` as for
    `chosen`."""
    order = chosen("dates", lang)
    if order == "ymd":
        return f"{when.year:04d}-{when.month:02d}-{when.day:02d}"
    month = (SHORT if short else LONG)[when.month](lang)
    if order == "mdy":
        return i18n.t("dates.mdy", day=when.day, month=month, year=when.year, lang=lang)
    return i18n.t("dates.dmy", day=when.day, month=month, year=when.year, lang=lang)


def day_words(when: date | datetime, lang: str | None = None) -> str:
    """A day and its month with no year, as the page's tDate writes one (a revision of this year in the History,
    the hold card's Asked line): 1 October, October 1 or 10-01. `lang` as for `chosen`."""
    order = chosen("dates", lang)
    if order == "ymd":
        return f"{when.month:02d}-{when.day:02d}"
    month = LONG[when.month](lang)
    if order == "mdy":
        return i18n.t("dates.md", day=when.day, month=month, lang=lang)
    return i18n.t("dates.dm", day=when.day, month=month, lang=lang)


def clock_words(when: datetime, lang: str | None = None) -> str:
    """A time of day by the time format, as the page's tTime writes it: 14:05 on the 24-hour clock, 2:05 pm on
    the 12-hour (2:05 PM in American English), its am and pm the language's. `lang` as for `chosen`."""
    if chosen("time", lang) != "12":
        return f"{when:%H:%M}"
    hour = when.hour % 12 or 12
    if when.hour < 12:
        return i18n.t("dates.clock.am", hour=hour, minute=f"{when.minute:02d}", lang=lang)
    return i18n.t("dates.clock.pm", hour=hour, minute=f"{when.minute:02d}", lang=lang)


# The patterns a list is joined by in the run's language, CLDR's four for "and" and for "or": two items alone, then
# for three or more the first pair, each pair in the middle and the last, each key written whole so the catalogue
# check finds it used
LISTS = {
    "and": {
        "two": lambda a, b, lang=None: i18n.t("lists.and.two", a=a, b=b, lang=lang),
        "start": lambda a, b, lang=None: i18n.t("lists.and.start", a=a, b=b, lang=lang),
        "middle": lambda a, b, lang=None: i18n.t("lists.and.middle", a=a, b=b, lang=lang),
        "end": lambda a, b, lang=None: i18n.t("lists.and.end", a=a, b=b, lang=lang),
    },
    "or": {
        "two": lambda a, b, lang=None: i18n.t("lists.or.two", a=a, b=b, lang=lang),
        "start": lambda a, b, lang=None: i18n.t("lists.or.start", a=a, b=b, lang=lang),
        "middle": lambda a, b, lang=None: i18n.t("lists.or.middle", a=a, b=b, lang=lang),
        "end": lambda a, b, lang=None: i18n.t("lists.or.end", a=a, b=b, lang=lang),
    },
}


def list_words(items, kind: str = "and", lang: str | None = None) -> str:
    """Items joined as the run's language (or `lang`) joins a list (the page's tList): "a", "a and b", "a, b and
    c" in British English and "a, b, and c" in American, and with `kind` "or" a choice, "a, b or c". Each item as
    it is, the researcher's words never changed."""
    words = [str(x) for x in items]
    if len(words) < 2:
        return words[0] if words else ""
    joins = LISTS[kind]
    if len(words) == 2:
        return joins["two"](words[0], words[1], lang)
    out = joins["end"](words[-2], words[-1], lang)
    for word in reversed(words[1:-2]):
        out = joins["middle"](word, out, lang)
    return joins["start"](words[0], out, lang)
