"""Search across the app (17 and 18 October): every word typed, in any order, case and accents set aside,
as Sift's find boxes match a choice (`sfFindMatch` in sift.js), over what a case, a project, a Sift
project, a Trace project or all of them hold. Two ticks beside the field narrow that, Whole word, on at first
as in Find and replace, and Match case, off until set (searchmods, 6 November 2026, see Word forms below),
which the HTTP route, the command line and MCP take alike, Whole word on unless they say false.

In Distil a case holds its passages and the interviewer's notes on his own, its statements, quotes
and exploratory notes, from the workbook, and its PETs, sub-themes, their notes, its sticky notes and
each board's note, from its themes file. A project holds every case of its study, and its GETs, their
notes, the GET table's row notes, the participant notes, the GETs boards' sticky notes and board notes,
from `idiograph-gets.json`, the cases by their names and the research question. History revisions, AI
threads and reviews stay out.

A Sift project holds the records of the screening its Screening step opens, each record's title, its ID
with it, abstract, authors and journal, his decision notes at each stage, his own fields, his form's
answers and his key excerpts, from `screening.csv`, its log and `sift.json`, and its plan's search terms
and exclusion reasons, the newest version of `search_plan.json` and the review's `reasons.csv`. A Trace
project holds each manuscript's claims, the references they cite and his notes on the claims, the
manuscript read as Trace reads it, with the project's reference list and each manuscript's log. AI
proposals, AI passages and PDFs' text stay out. Everything is every project the home screen lists, the
three parts in the order a study does them, Sift, Distil and Trace.

What a file holds is read once and kept in memory against the file's time and size, as the home screen
keeps the workbooks it reads (`server.read_book`), so the second search over the same files reads none of
them, and items read from several files, a screening's or a manuscript's, against each one's. Nothing is
ever written: no index on disk, which would be a second copy of the participants' words and go stale, and
no file of the project's. The engine is the family's, the standard library alone (the family codebase's
fourth build, 22 October 2026, family/app_search.py). Each app's part, its kinds and its finder, is its own,
registered from apps/idiograph/idiograph_find.py (Distil's, with its two scopes, This case and This project),
apps/sift/sift_find.py and apps/trace/trace_find.py (`register`, the family codebase's second, third and fourth
builds, 22 October 2026).
"""
from __future__ import annotations

import functools
import re
import time
import unicodedata
from pathlib import Path

import boot
import i18n

# the three parts in the order a study does them, as the home screen stands them, Sift, Distil and Trace,
# each with its kinds, which Everything lists under the part's name, each registered from its app's module,
# Distil's from apps/idiograph/idiograph_find.py, Sift's from apps/sift/sift_find.py and Trace's from
# apps/trace/trace_find.py, each in its place (see `register`)
ORDER = ("sift", "distil", "trace")
PARTS: tuple = ()
ALL_KINDS: tuple = ()
# the scopes a search takes, Distil's This case and This project, then each other part's by its name, then
# Everything, and the kinds each holds
SCOPES = ("all",)
SCOPE_KINDS = {"all": ALL_KINDS}
# the most results one answer carries, the counts always counting them all
LIMIT = 200
# a long passage or note is cut to a window round the first word found, this many characters, with
# about a third of it before that word
SNIPPET = 240
BEFORE = 70
ELLIPSIS = "…"

# each kind by its name, one and many, as the card names them (`SEARCH_KINDS` in search.js), for the command
# line's answer (20 October), each registered part's in turn
KIND_NAMES: dict = {}
# a part's names said by the run as it stands, where they change with it (taword, 1 November 2026: a thematic
# analysis project's Codes and Extracts in place of IPA's Statements and Quotes), each a function of the kind and
# whether many are meant, giving None where the kind's registered name stands
KIND_NAMERS: list = []


def kind_name(kind: str, many: bool = False) -> str:
    """A kind's name, one or many, as the run says it (see `KIND_NAMERS`), else as its part registered it."""
    for namer in KIND_NAMERS:
        said = namer(kind, many)
        if said:
            return said
    return (KIND_NAMES.get(kind) or (kind, kind))[1 if many else 0]
# the kinds an agent names together, each a few of the card's (20 October), beside the card's own names, each
# registered part's in turn
KIND_GROUPS: dict = {}

# what has been read, each kept against the time and size of the file it came from
HELD: dict[tuple, tuple] = {}
MARKS = re.compile("[̀-ͯ]")


def fold(text) -> str:
    """Words as a search compares them: accents taken off and in lower case, "Café" read as "cafe"."""
    return plain(text).lower()


def plain(text) -> str:
    """Words as Match case compares them: accents taken off and the case kept, "Café" read as "Cafe"."""
    return MARKS.sub("", unicodedata.normalize("NFD", str(text or "")))


# ------------------------------------------------------------------ word forms

# Word forms (20 October): a word typed finds its other forms too, "sleep" finding "sleeps", "sleeping" and
# "slept", "walked" finding "walk" and "walking". A small, plain English rule set and no dependency. The word
# typed is found anywhere in a text as before, and each other form only as a whole word, so "man" finding
# "men" never finds "moment". A phrase in quotation marks is matched as typed, with no other form.
#
# Two modifiers (searchmods, 6 November 2026), as Find and replace's ticks are, Whole word on at first (Adam, 6
# November, "Whole word on") and Match case off until set. This engine reads what it is told, off unless `whole`
# or `case` is passed, and `options` is where a request's default is: Whole word on unless it says false. Whole word:
# each word typed is found only as a whole word, with its other forms, so "cat" finds "cat" and "cats" and never
# "catch", and a phrase only where it starts and ends on word edges, a word edge being what Find and replace's
# Whole word takes for one, no letter or digit beside an end that is one itself. Match case: the word as typed, its
# case kept and its accents still set aside, "Will" never finding "will", its other forms in the case it was typed
# in, "Sleep" finding "Sleeps" and "Slept" and never "sleeps", and a word of mixed case, "McDonald", none.
#
# The irregular words, each with its other forms. Forms that are as often another word are left out, "left"
# for leave, "saw" for see, "lay" for lie, "rose" for rise, "fell" for fall and "bit" for bite.
IRREGULAR = {
    "sleep": "slept", "wake": "woke woken", "awake": "awoke awoken", "feel": "felt", "keep": "kept",
    "meet": "met", "think": "thought", "bring": "brought", "buy": "bought", "catch": "caught", "teach": "taught",
    "seek": "sought", "fight": "fought", "go": "goes went gone going", "come": "came", "become": "became",
    "take": "took taken", "give": "gave given", "see": "seen sees seeing", "know": "knew known", "grow": "grew grown",
    "throw": "threw thrown", "fly": "flew flown flies", "draw": "drew drawn", "begin": "began begun",
    "drink": "drank drunk", "sing": "sang sung", "swim": "swam swum", "run": "ran", "sit": "sat",
    "stand": "stood", "understand": "understood", "get": "got gotten", "forget": "forgot forgotten",
    "speak": "spoke spoken", "break": "broke broken", "choose": "chose chosen", "write": "wrote written",
    "ride": "rode ridden", "drive": "drove driven", "eat": "ate eaten", "hold": "held", "tell": "told",
    "sell": "sold", "find": "found", "lose": "lost", "win": "won", "hear": "heard", "say": "said says",
    "pay": "paid", "make": "made", "mean": "meant", "send": "sent", "spend": "spent", "build": "built",
    "lend": "lent", "bend": "bent", "feed": "fed", "lead": "led", "bleed": "bled", "hide": "hid hidden",
    "shake": "shook shaken", "wear": "wore worn", "tear": "tore torn", "swear": "swore sworn",
    "dream": "dreamt", "learn": "learnt", "burn": "burnt", "smell": "smelt", "spill": "spilt", "kneel": "knelt",
    "weep": "wept", "sweep": "swept", "creep": "crept", "shine": "shone", "shoot": "shot", "dig": "dug",
    "hang": "hung", "stick": "stuck", "strike": "struck", "swing": "swung", "cling": "clung", "sink": "sank sunk",
    "shrink": "shrank shrunk", "ring": "rang rung", "spring": "sprang sprung", "freeze": "froze frozen",
    "steal": "stole stolen", "arise": "arose arisen", "have": "has had having", "do": "does did done doing",
    "die": "dies died dying", "tie": "ties tied tying", "child": "children", "person": "people", "man": "men",
    "woman": "women", "mouse": "mice", "foot": "feet", "tooth": "teeth", "life": "lives", "wife": "wives",
    "knife": "knives", "self": "selves", "leaf": "leaves"}
FORMS_OF = {lemma: tuple(said.split()) for lemma, said in IRREGULAR.items()}
LEMMAS_OF: dict[str, list[str]] = {}
for _lemma, _forms in FORMS_OF.items():
    for _f in _forms:
        LEMMAS_OF.setdefault(_f, []).append(_lemma)
# words that end as a form does and are words of their own, never taken back to a shorter one
OWN_WORDS = frozenset("""always during evening morning nothing something anything everything thing things news
series species perhaps ceiling wedding indeed hundred sacred naked wicked kindness business being""".split())
VOWELS = set("aeiou")
# the last letters a short word doubles before -ing and -ed, "stop" stopping, "travel" travelling
DOUBLES = set("bdgklmnprtv")
SINGLE = re.compile(r"^[a-z]+$")


def lemmas(word: str, deeper: bool = True) -> list[str]:
    """The plain forms a word typed may be a form of, itself first: "slept" sleep, "walked" walk, "tried" try,
    "making" mak and make, "running" runn and run. A stem that is no word does no harm, since what it gives
    is found only as a whole word. Each is three letters or more and holds a vowel."""
    out = [word]
    out += LEMMAS_OF.get(word, [])
    if len(word) < 4 or word in OWN_WORDS:
        return out
    took = []
    if word.endswith(("ies", "ied")):
        took.append(word[:-3] + "y")
    elif word.endswith("ying") and len(word) == 5:
        took.append(word[:-4] + "ie")
    elif word.endswith(("ing", "ed")):
        s = word[:-3] if word.endswith("ing") else word[:-2]
        # a last consonant doubled is undone, "running" run, "stopped" stop, and otherwise the stem is taken
        # with and without a final e, "making" make, "walked" walk
        doubled = len(s) > 2 and s[-1] == s[-2] and s[-1] not in "lsz" and s[-1] not in VOWELS
        if not (VOWELS | {"y"}) & set(s) or (word.endswith("eed") and len(word) <= 5):
            pass                # "bring", "thing", "need" and "feed" are words of their own
        elif doubled:
            took.append(s[:-1])
        else:
            took += [s, s + "e"]
    elif word.endswith("es"):
        took += [word[:-2], word[:-1]]
    elif word.endswith("s") and not word.endswith(("ss", "us", "is")):
        took.append(word[:-1])
    for s in took:
        if len(s) >= 3 and s not in out:
            out.append(s)
            # once more, so "feelings" goes back to feeling and then to feel
            if deeper:
                out += [x for x in lemmas(s, False)[1:] if x not in out]
    for s in list(out[1:]):
        for f in LEMMAS_OF.get(s, []):
            if f not in out:
                out.append(f)
    return out


def inflected(lemma: str) -> list[str]:
    """A plain form's other forms by the regular rules, both ways where a rule may go either way, "visit" to
    "visiting" and "visitting", since a form no text holds finds nothing: -s or -es, -ing and -ed, a final e
    dropped, a y made ie, a last consonant doubled."""
    out = list(FORMS_OF.get(lemma, ()))
    if len(lemma) < 3:
        return out
    last = lemma[-1]
    if lemma.endswith(("s", "x", "z", "ch", "sh")):
        out.append(lemma + "es")
    elif last == "y" and lemma[-2] not in VOWELS:
        out += [lemma[:-1] + "ies", lemma[:-1] + "ied"]
    else:
        out.append(lemma + "s")
    if lemma.endswith("ie"):
        out.append(lemma[:-2] + "ying")
    if last == "e":
        out += [lemma[:-1] + "ing", lemma + "d"]
        if lemma.endswith(("ee", "ye", "oe")):
            out.append(lemma + "ing")
    else:
        out += [lemma + "ing", lemma + "ed"]
        if last in DOUBLES and lemma[-2] in VOWELS and lemma[-3:-2] not in VOWELS:
            out += [lemma + last + "ing", lemma + last + "ed"]
    return out


# a letter or a digit, as Find and replace's Whole word reads one (`wordish` in distil.js)
ALNUM = r"[^\W_]"


def edged(word: str) -> str:
    """The pattern that finds `word` only as a whole word: it may not run into a letter or a digit at an end that
    is one itself, so "so" is never found inside "also" or "sofa" and is found in "so," and "so's"."""
    before = rf"(?<!{ALNUM})" if word[:1] and re.match(ALNUM, word[0]) else ""
    after = rf"(?!{ALNUM})" if word[-1:] and re.match(ALNUM, word[-1]) else ""
    return before + re.escape(word) + after


def recase(form: str, word: str) -> str | None:
    """A form in the case of the word it is a form of, as Match case finds it: a word in lower case gives its forms
    in lower case, "Sleep" gives "Sleeps" and "SLEEP" gives "SLEEPS", and a word of mixed case gives none."""
    if word.islower():
        return form
    if word[:1].isupper() and word[1:].islower():
        return form[:1].upper() + form[1:]
    if word.isupper() and len(word) > 1:
        return form.upper()
    return None


def own_number(word: str) -> list[str]:
    """The word's plural, or the singular of a plural typed, by the regular rules, whatever else it is a form of."""
    if len(word) < 3:
        return []
    out = []
    if word.endswith("ies") and len(word) > 4:
        out.append(word[:-3] + "y")
    if word.endswith("es") and word[:-2].endswith(("s", "x", "z", "ch", "sh")):
        out.append(word[:-2])
    if word.endswith("s") and not word.endswith(("ss", "us", "is")):
        out.append(word[:-1])
    if word.endswith(("s", "x", "z", "ch", "sh")):
        out.append(word + "es")
    elif word.endswith("y") and word[-2] not in VOWELS:
        out.append(word[:-1] + "ies")
    else:
        out.append(word + "s")
    return out


class Term(str):
    """A word typed, folded, as a search compares it, with its other forms (see `lemmas` and `inflected`) and
    the pattern that finds them as whole words. A word in a quoted phrase has none. With `whole` the pattern
    finds the word itself as a whole word too, and with `case` the word keeps its case and so do its forms."""
    forms: tuple = ()
    rx = None
    whole = False
    case = False


def term(word: str, widen: bool = True, whole: bool = False, case: bool = False) -> Term:
    t = Term(word)
    t.whole, t.case = whole, case
    low = fold(word)
    made = []
    if widen and SINGLE.match(low):
        found = lemmas(low)
        # a form typed is taken back to its plain form, which gives the others, never inflected itself
        if len(found) > 1 and low.endswith(("s", "ed", "ing")) and low not in FORMS_OF:
            found = [x for x in found if x != low]
        for lemma in found:
            # a form on the way back, "feeling" from "feelings", is found but never inflected itself
            bare = (lemma not in LEMMAS_OF and (lemma == low or not lemma.endswith(("ing", "ed"))
                                                or len(lemmas(lemma, False)) == 1))
            for f in [lemma] + (inflected(lemma) if bare else []):
                if f != low and f not in made:
                    made.append(f)
        if whole:
            # the typed word's own plural, and the singular of a plural typed, so "feeling" finds "feelings"
            for f in own_number(low):
                if f != low and f not in made:
                    made.append(f)
        if case:
            made = [g for g in dict.fromkeys(recase(f, word) for f in made) if g and g != word]
    t.forms = tuple(made)
    if whole:
        # the word itself among them, each found only where it stands on word edges
        every = sorted([str(word)] + made, key=len, reverse=True)
        t.rx = re.compile("|".join(edged(f) for f in every))
    elif made:
        letters = "A-Za-z0-9" if case else "a-z0-9"
        t.rx = re.compile(rf"(?<![{letters}])(?:" + "|".join(re.escape(f) for f in sorted(made, key=len, reverse=True))
                          + rf")(?![{letters}])")
    return t


class Words(list):
    """The words typed, with the modifiers they were read under: `whole` and `case`, and with `case` `loose`, the
    same words read with no Match case, which a text must pass before its case is looked at (see `hit`)."""
    whole = False
    case = False
    loose = None


def words_of(q, widen: bool = True, whole: bool = False, case: bool = False) -> Words:
    """The words typed, folded, each once, each with its other forms unless `widen` is false, `whole` finding
    each only as a whole word and `case` keeping its case."""
    out = Words()
    out.whole, out.case = whole, case
    for w in (plain(q) if case else fold(q)).split():
        if w not in out:
            out.append(term(w, widen, whole, case))
    if case:
        out.loose = words_of(q, widen, whole, False)
    return out


QUOTES = ('"', "“", "”")


class Phrase(str):
    """A phrase in quotation marks, with the modifiers it was read under."""
    whole = False
    case = False


def query(q, whole: bool = False, case: bool = False) -> tuple[str, Words, str]:
    """The words a search reads from what was typed: the text, its words and, when it stands in quotation
    marks, the phrase, every hit then holding it as typed, its words with no other form. `whole` and `case`
    are the modifiers, Whole word and Match case, each off unless passed (see `options` for a request's)."""
    q = str(q or "").strip()
    if len(q) > 1 and q[0] in QUOTES and q[-1] in QUOTES:
        q = q[1:-1].strip()
        phrase = Phrase(q)
        phrase.whole, phrase.case = whole, case
        return q, words_of(q, False, whole, case), phrase
    return q, words_of(q, True, whole, case), ""


def options(body) -> tuple[bool, bool]:
    """The modifiers a request asks for, `whole_word` and `match_case`. Whole word is on unless the request says
    false, as the card opens with it ticked (Adam, 6 November 2026), and Match case on only when it says true."""
    body = body if isinstance(body, dict) else {}
    return body.get("whole_word") is not False, body.get("match_case") is True


def found_in(text: str, w) -> bool:
    """A word typed in a text folded as the word is (`fold`, or `plain` under Match case), anywhere as typed or one
    of its other forms as a whole word, and under Whole word only as a whole word, its other forms too."""
    rx = getattr(w, "rx", None)
    if getattr(w, "whole", False):
        return rx is not None and rx.search(text) is not None
    return w in text or (rx is not None and rx.search(text) is not None)


def matches(folded: str, words: list[str]) -> bool:
    """Every word typed somewhere in the text, in any order, as `sfFindMatch` reads a choice, or one of its
    other forms as a whole word. The text is folded as the words are, which under Match case is `plain`."""
    return bool(words) and all(found_in(folded, w) for w in words)


def searched(it: dict) -> str:
    """What an item is searched on, as written: its text, or where its `f` was made of more than its text, a
    record's ID with its title, the `s` that says so."""
    return it.get("s") or it["text"]


def hit(it: dict, words: list[str]) -> bool:
    """Whether an item holds every word typed, by the rules the words were typed under. The folded text it holds
    from the start answers a search with no Match case and, with it, passes what could be found in any case, so the
    accents are taken off the text as written only for what passes."""
    if not words:
        return False
    if not getattr(words, "case", False):
        return matches(it["f"], words)
    return matches(it["f"], words.loose) and matches(plain(searched(it)), words)


def holds(text: str, words: list[str]) -> bool:
    """Whether a text that is no item, a participant's name or the research question, holds every word typed."""
    return hit({"f": fold(text), "text": str(text or "")}, words)


def forms_said(words: list) -> list[str]:
    """The other forms of the words typed, for the page to mark them where they stand as whole words."""
    out = []
    for w in words:
        out += [f for f in getattr(w, "forms", ()) if f not in out]
    return out


def spans_of(text: str, w) -> list[tuple[int, int]]:
    """Where a word typed stands in a text folded as the word is, as typed and as each of its other forms, and
    under Whole word wherever it stands as a whole word."""
    if getattr(w, "whole", False):
        return [(m.start(), m.end()) for m in w.rx.finditer(text)]
    out, start = [], 0
    while w and (k := text.find(w, start)) >= 0:
        out.append((k, k + len(w)))
        start = k + len(w)
    if getattr(w, "rx", None) is not None:
        out += [(m.start(), m.end()) for m in w.rx.finditer(text)]
    return out


def file_mark(path: Path) -> tuple | None:
    try:
        st = Path(path).stat()
    except OSError:
        return None
    return st.st_mtime_ns, st.st_size


def held(path: Path, kind: str, read, extra=None, also=()):
    """What `read` makes of a file, read once and kept until its time or size changes, or the time or size
    of any file of `also` it reads beside it, one of those not there marked as none. A file not there holds
    nothing, and one that cannot be read holds nothing until it changes."""
    mark = file_mark(path)
    if mark is None:
        return []
    if also:
        mark = (mark,) + tuple(file_mark(p) for p in also)
    key = (str(path), kind, extra)
    got = HELD.get(key)
    if got and got[0] == mark:
        return got[1]
    try:
        items = read(path)
    except Exception:
        items = []
    HELD[key] = (mark, items)
    return items


def item(kind: str, text: str, where: str, go: dict, order: tuple, sheet: str = "") -> dict:
    return {"kind": kind, "text": text, "f": fold(text), "where": where, "go": go, "order": order, "sheet": sheet}


# ------------------------------------------------------------------ a part's text

def flat(text) -> str:
    """Words on one line, every run of spaces and line ends one space."""
    return " ".join(str(text or "").split())


def search_all(q: str, kinds=(), projects=(), limit: int = LIMIT, whole: bool = False, match_case: bool = False,
               **more: list[dict]) -> dict:
    """The results of `q` over every project the home screen lists, Everything: each registered part's by its
    name in `more`, Distil's `distil`, each `{"id", "name", "cases", "project", "gets_file", "labels"}`,
    searched as This project searches it, Sift's `sift`, each `{"id", "name", "screening", "screening_id",
    "review", "review_id"}`, and Trace's `trace`, each `{"id", "name", "folder", "folder_id"}`, in the home
    screen's order, the parts in a study's. Each result names its project, and `projects` narrows them to the
    projects ticked, by `key`, the part and the id. `whole` and `match_case` are Whole word and Match case."""
    started = time.perf_counter()
    q, words, phrase = query(q, whole, match_case)
    found, rows = [], []
    for part, _kinds in PARTS:
        for p in more.get(part) or []:
            key = f"{part}:{p['id']}"
            rows.append({"key": key, "name": p["name"], "part": part})
            if not words:
                continue
            got = FOUND[part](words, p)
            found += [dict(it, pkey=key, project=p["name"], prank=len(rows) - 1) for it in phrased(got, phrase)]
    return answer(q, "all", words, found, started, kinds=kinds, projects=projects, project_rows=rows, limit=limit)


PART_OF: dict = {}
# each registered part's finder over one of its projects under Everything, by the part's name
FOUND: dict = {}
# the scopes a part names for itself, Distil's This case and This project, in the order they register, the
# parts searched by their own name as a scope, and the screens whose results carry their case's path
OWN_SCOPES: list = []
PART_SCOPES: list = []
CASE_SCREENS: set = set()


def register(part: str, kinds: tuple, found, names: dict, *groups: tuple, scopes: dict | None = None,
             screens=(), namer=None) -> None:
    """A part of an app's own, from its module (the family codebase's second build, 22 October 2026):
    its kinds, in its place among the parts in a study's order (`ORDER`), a scope of its name after This
    project's and before Everything, `found`, its finder over one project as Everything lists it, each kind's
    `names`, one and many, and `groups`, each the name an agent gives some of its kinds together and the
    kinds. Since the fourth build Distil's too, from apps/idiograph/idiograph_find.py, whose `scopes` name its
    own, This case and This project, with the kinds each holds, first among the scopes in place of one of the
    part's name, and whose `screens`, a passage's, a board's and the GETs', carry the case's path in each
    result. `namer` says a kind's name as the run stands where it changes with it (see `KIND_NAMERS`). Called
    once, as its module is first imported (Sift's from apps/sift/sift_find.py, Trace's from
    apps/trace/trace_find.py)."""
    global PARTS, ALL_KINDS, SCOPES
    rank = lambda name: ORDER.index(name) if name in ORDER else len(ORDER)  # noqa: E731
    PARTS = tuple(sorted(PARTS + ((part, tuple(kinds)),), key=lambda p: rank(p[0])))
    ALL_KINDS = tuple(k for _, ks in PARTS for k in ks)
    if scopes:
        OWN_SCOPES.extend(s for s in scopes if s not in OWN_SCOPES)
        SCOPE_KINDS.update({s: tuple(k) for s, k in scopes.items()})
    else:
        PART_SCOPES.append(part)
        SCOPE_KINDS[part] = tuple(kinds)
    SCOPES = tuple(OWN_SCOPES) + tuple(sorted(PART_SCOPES, key=rank)) + ("all",)
    SCOPE_KINDS["all"] = ALL_KINDS
    PART_OF.update({kind: part for kind in kinds})
    KIND_NAMES.update(names)
    if namer is not None:
        KIND_NAMERS.append(namer)
    KIND_GROUPS.update({name: tuple(members) for name, members in groups})
    CASE_SCREENS.update(screens)
    FOUND[part] = found


def answer(q: str, scope: str, words: list[str], found: list[dict], started: float, kinds=(), only_cases=(),
           sheets=(), projects=(), case_names=(), project_rows=(), limit: int = LIMIT) -> dict:
    """A search's answer from what it found. `kinds`, `only_cases`, `sheets` and `projects` narrow what is
    shown, each ticked filter one of a group that may be any, and every group's counts are counted with the
    other groups' ticks alone, so a tick never hides its own neighbours. Case and Sheet are This project's
    alone, and Project Everything's. The first `limit` results by kind, in the parts' order, project, case
    and place, each with its words, cut to a window round the first word found when long, where it is in
    small type and where a click lands, and with Everything its project and its part."""
    kinds, only_cases, sheets, projects = set(kinds or ()), set(only_cases or ()), set(sheets or ()), set(projects or ())
    if scope != "project":
        only_cases, sheets = set(), set()
    if scope != "all":
        projects = set()

    def kept(it: dict, but: str = "") -> bool:
        return ((but == "kind" or not kinds or it["kind"] in kinds)
                and (but == "case" or not only_cases or it.get("case") in only_cases)
                and (but == "sheet" or not sheets or it.get("sheet") in sheets)
                and (but == "project" or not projects or it.get("pkey") in projects))

    counts = {k: 0 for k in SCOPE_KINDS[scope]}
    for it in found:
        if kept(it, "kind") and it["kind"] in counts:
            counts[it["kind"]] += 1
    by_case, by_sheet, by_project = {}, {}, {}
    for it in found:
        if it.get("case") and kept(it, "case"):
            by_case[it["case"]] = by_case.get(it["case"], 0) + 1
        if it.get("sheet") and kept(it, "sheet"):
            by_sheet[it["sheet"]] = by_sheet.get(it["sheet"], 0) + 1
        if it.get("pkey") and kept(it, "project"):
            by_project[it["pkey"]] = by_project.get(it["pkey"], 0) + 1
    sheet_order = []
    for it in found:
        if it.get("sheet") and it["sheet"] not in sheet_order:
            sheet_order.append(it["sheet"])
    shown = sorted((it for it in found if kept(it)),
                   key=lambda it: (ALL_KINDS.index(it["kind"]), it.get("prank", 0), it["rank"], it["order"]))
    results = []
    for it in shown[:max(0, int(limit))]:
        go = dict(it["go"])
        if go.get("screen") in CASE_SCREENS:
            go["path"] = it["path"]
        one = {"kind": it["kind"], "text": snippet(it["text"], words), "where": it["where"],
               "case": it.get("case", ""), "sheet": it.get("sheet", ""), "go": go}
        if scope == "all":
            one.update(project=it.get("project", ""), part=PART_OF[it["kind"]])
        results.append(one)
    out = {"q": str(q or ""), "scope": scope, "results": results, "total": len(shown), "counts": counts,
           "forms": forms_said(words), "whole_word": bool(getattr(words, "whole", False)),
           "match_case": bool(getattr(words, "case", False)),
           "cases": [{"name": n, "count": by_case.get(n, 0)} for n in case_names] if scope == "project" else [],
           "sheets": [{"name": s, "count": by_sheet.get(s, 0)} for s in sheet_order] if scope == "project" else []}
    if scope == "all":
        out["parts"] = [[part, list(k)] for part, k in PARTS]
        out["projects"] = [dict(p, count=by_project.get(p["key"], 0)) for p in project_rows]
    out["ms"] = round((time.perf_counter() - started) * 1000, 1)
    return out


def phrased(found: list[dict], phrase: str) -> list[dict]:
    """What was found, with a phrase in quotation marks only the hits that hold it as typed."""
    return [it for it in found if phrase_in(it["text"], phrase)] if phrase else found


def phrase_in(text: str, phrase: str) -> bool:
    """The words of `phrase` together in `text`, in their order, case, accents and runs of spaces aside,
    for a search an agent puts in quotation marks (20 October). It narrows what every word typed found. A
    phrase read under Whole word is found only where it starts and ends on word edges, and under Match case
    with its case kept."""
    norm = plain if getattr(phrase, "case", False) else fold
    want, have = " ".join(norm(phrase).split()), " ".join(norm(text).split())
    if getattr(phrase, "whole", False):
        return phrase_pattern(want).search(have) is not None
    return want in have


@functools.lru_cache(maxsize=128)
def phrase_pattern(phrase: str):
    """The pattern that finds a phrase only on word edges (`edged`)."""
    return re.compile(edged(phrase))


def marked(text: str, words: list[str], mark: str = "**") -> str:
    """`text` with every place a word typed is found in it between two `mark`s, case and accents set aside
    as a search compares them, places that touch or overlap marked as one, for an agent's answer (20
    October). Each character is folded on its own, so a place found maps back to the words as written. Under
    Match case the case is kept, and under Whole word only a whole word is marked."""
    text = str(text or "")
    norm = plain if getattr(words, "case", False) else fold
    folded, at = [], []
    for i, ch in enumerate(text):
        for c in norm(ch):
            folded.append(c)
            at.append(i)
    flat_text = "".join(folded)
    spans = []
    for w in words:
        for k, stop in spans_of(flat_text, w):
            end = at[stop - 1] + 1
            while end < len(text) and not norm(text[end]):
                end += 1
            spans.append((at[k], end))
    out, last = [], 0
    for s, e in sorted(spans):
        if out and s <= out[-1][1]:
            out[-1][1] = max(out[-1][1], e)
        else:
            out.append([s, e])
    parts = []
    for s, e in out:
        parts += [text[last:s], mark, text[s:e], mark]
        last = e
    return "".join(parts) + text[last:]


def snippet(text: str, words: list[str]) -> str:
    """A long text cut to a window round the first word found, an ellipsis at each end it was cut at,
    the cut made at a space. A short one whole."""
    text = str(text or "")
    if len(text) <= SNIPPET:
        return text
    low = (plain if getattr(words, "case", False) else fold)(text)
    hits = [min(k for k, _ in spans_of(low, w)) for w in words if spans_of(low, w)]
    first = min(hits) if hits else 0
    start = max(0, first - BEFORE)
    if start:
        space = text.find(" ", start)
        start = space + 1 if 0 <= space < first else start
    end = min(len(text), start + SNIPPET)
    if end < len(text):
        space = text.rfind(" ", start, end)
        end = space if space > first else end
    return (ELLIPSIS if start else "") + text[start:end].strip() + (ELLIPSIS if end < len(text) else "")


# each app's own parts registered, Distil's from apps/idiograph/idiograph_find.py, Sift's from
# apps/sift/sift_find.py and Trace's from apps/trace/trace_find.py, each imported by its name
boot.load("find")


def __getattr__(name: str) -> str:
    """The refusals other modules and the checks name as this module's, each read in the run's language when
    asked for (the text layer, 28 October 2026)."""
    said = {
        "NO_CASE": lambda: i18n.t("errors.say_which_participant_nothing_searched"),
        "NO_PROJECT": lambda: i18n.t("errors.say_which_project_nothing_searched"),
        "NO_SCOPE": lambda: i18n.t("errors.search_participant_project_sift_project"),
        "NO_SCOPE_IDIOGRAPH": lambda: i18n.t("errors.search_participant_project_everything"),
    }
    if name in said:
        return said[name]()
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
