"""Names replaced as a transcript comes in (namesrule, 8 November 2026, the first build of three).

A project can hold a list of real names and the pseudonym each is written as. A transcript added to the
project, by any road, has them replaced on its way in, so the workbooks never hold a real name. This module is
the whole of it apart from the places the routes call it: the store, the rules and a CSV or Excel key's read.

The store (namesui, Adam's pick of 8 November 2026 about 22:50: the list lives in the project's folder and moves
with it). The list is one file, `idiograph-names.json`, beside the project file at the project's root, mode 600.
It is named for the app and for what it holds, so a researcher who hands the folder on by hand sees it and knows
what it is. It is never in a workbook, History, the progress file, the agent log, a shared copy
(`project_pack.LEFT_OUT`) or an export, and the app copies it nowhere. A list namesrule kept in the app's own
folder, `names/<key>.json` under the key the project file held as `names_key`, is moved into the project's folder
the first time it is read, and the key and the old file go (`load_at`).

The rules (Adam's picks, 8 November 2026):
1. Whole words by Unicode letters and digits: "Ann" is never found in "Annabel" or "annual".
2. Case ignored in the finding, the list's spelling written. A find whose first letter is lower case where the
   spelling's is a capital ("hope" for Hope) is a lower-case find: left as written unless he ticks it in the app's
   review (`Run`'s `take`), never replaced in bulk or by an agent (namesbuild, Adam's design of 17 November 2026).
3. An apostrophe, hyphen or full stop ends a word, so "Tilda's" becomes "Wren's".
4. A run of spaces or a line break inside a name matches.
5. Initials ("T.M.") match with or without the dots and the space between, always by case.
6. The longest first, in one pass, so no replacement is ever replaced again.
7. Several spellings an entry. Misspellings are not guessed.

An entry is `{"real": [spellings], "to": replacement, "for": a participant's pseudonym or None for everyone}`, with
`"except": [phrases]`, phrases a find inside is never a find at all (namesop, 16 November 2026, for a surname that is
also a book series' title), and `"unticked": True`, the mark the app's Review and replace or Add writes on an entry
when he unticks one of its finds (namesbuild): an agent's replace, and any write he has not reviewed, leaves every
find of a marked entry as written, and no agent clears the mark (his own edit of the entry in the app does). Both
are kept only when set. Review each and Also an ordinary word went with namesbuild (Adam, 17 November 2026: each find
is decided in the review, its sentence beside its tick): an old entry's `review`, `word` and Match case `case` are
read as nothing and dropped on the next save. Entries are numbered from 1 in the list's order, and a
find by its entry's number and its place among that entry's finds in one Add (`nth`), which is how a skip or a take
names it without a real name.
"""
from __future__ import annotations

import csv
import io
import json
import os
import re
from pathlib import Path

import i18n

# the list's file at the project's root (namesui)
FILE = "idiograph-names.json"
# where namesrule kept a list before, read for the one move into the project's folder: a test gives its own folder
# here, else the environment's, else the app's data folder (see `folder`)
OVERRIDE: Path | None = None
ENV = "IDIOGRAPH_NAMES_DIR"
KEY_FIELD = "names_key"
MOST_ENTRIES = 5000
MOST_SPELLINGS = 40
MOST_EXCEPT = 40
INITIALS = re.compile(r"^(?:[A-Z]\.\s?){2,4}$|^[A-Z]{2,4}$")
KEY_OK = re.compile(r"^[0-9a-f]{32}$")
# the most characters either side of a find the review shows of its sentence (namesbuild)
SENTENCE = 240
# a full stop, question or exclamation mark, with any closing quotation mark or bracket after it, then a space
SENTENCE_END = re.compile(r"[.!?][\"”’)]*(?=\s)|\n")
# a participant's memos file in their Source folder, as a REFI-QDA import writes it (`<pseudonym> - memos.txt`, then
# ` 2` and on): searched and replaced as a passage is (wordfix), kept by an agent's restore point (wordfix2), and
# named in every count and line by MEMOS_PLACE alone, never by its file's name, which may be his own (wordfix2 N3)
MEMOS_FILE = re.compile(r"^.+ - memos(?: \d+)?\.txt$")
MEMOS_PLACE = "memos"


class NamesError(ValueError):
    """A list or a request that cannot be taken, one line."""


# ------------------------------------------------------------------ the store

def folder() -> Path:
    """The folder namesrule kept the lists in, `names` in the app's own data folder, read for the one move."""
    if OVERRIDE is not None:
        return Path(OVERRIDE)
    if os.environ.get(ENV):
        return Path(os.environ[ENV])
    import server as srv  # the family's, on the path by now
    return Path(srv.PATHS["data"]) / "names"


def path_at(root) -> Path:
    """The list's file in a project's folder."""
    return Path(root) / FILE


def old_path(key) -> Path | None:
    key = str(key or "")
    return folder() / f"{key}.json" if KEY_OK.match(key) else None


def read_file(path: Path) -> list[dict]:
    """The entries a list's file holds, none when it cannot be read."""
    try:
        data = json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return []
    rows = data.get("entries") if isinstance(data, dict) else None
    out = []
    for raw in rows if isinstance(rows, list) else []:
        try:
            out.append(clean_entry(raw))
        except NamesError:
            continue
    return out


def load_at(root, project: dict | None = None, project_path: Path | None = None) -> list[dict]:
    """A project's entries, none when it has no list. A list namesrule kept in the app's own folder under the
    project file's `names_key` is moved here once: written into the project's folder, the old file deleted and
    the key taken out of the project file (`project` and `project_path`, the project file as read and its path)."""
    if root is None:
        return []
    here = path_at(root)
    if here.is_file():
        return read_file(here)
    old = old_path((project or {}).get(KEY_FIELD))
    if old is None or not old.is_file():
        return []
    entries = read_file(old)
    try:
        if entries:
            save_at(root, entries)
        old.unlink(missing_ok=True)
        if project_path is not None and isinstance(project, dict):
            kept = {k: v for k, v in project.items() if k != KEY_FIELD}
            tmp = Path(project_path).with_name(f".{Path(project_path).name}.names")
            tmp.write_text(json.dumps(kept, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
            os.replace(tmp, project_path)
    except OSError:
        pass
    return entries


def entries_at(root) -> list[dict]:
    """A project's entries wherever `load_at` would find them, nothing moved or written: the project's folder's
    list, else one namesrule kept in the app's own folder under the project file's key. What takes the names out of
    an agent's request reads this, so it sees every name a call through `load_at` will use (namesfix)."""
    if root is None:
        return []
    here = path_at(root)
    if here.is_file():
        return read_file(here)
    try:
        import server as srv  # the family's, on the path by now
        project = json.loads((Path(root) / srv.PROJECT_FILE).read_text(encoding="utf-8"))
    except (OSError, ValueError, ImportError):
        return []
    old = old_path(project.get(KEY_FIELD) if isinstance(project, dict) else None)
    return read_file(old) if old is not None and old.is_file() else []


def with_real_names(entries: list[dict], files) -> list[dict]:
    """The list with an entry for each Real name typed on Add transcripts' rows (namesui), for that participant
    alone: the name as typed and, when it has more than one word, its first, written as the pseudonym. A name the
    list already holds for that participant or for everyone makes none."""
    out = list(entries)
    for f in files if isinstance(files, list) else []:
        if not isinstance(f, dict):
            continue
        real = " ".join(str(f.get("real") or "").split())
        who = " ".join(str(f.get("pseudonym") or "").split())
        if not real or not who:
            continue
        words = real.split()
        spellings = [real] + ([words[0]] if len(words) > 1 and len(words[0]) > 1 else [])
        held = {s.casefold() for e in out if applies(e, who) for s in e["real"]}
        spellings = [s for s in spellings if s.casefold() not in held]
        if spellings:
            out.append(clean_entry({"real": spellings, "to": who, "for": who}))
    return out


def save_at(root, entries: list[dict]) -> None:
    """The entries written whole into the project's folder, mode 600, never over a file half written. An empty
    list takes the file away."""
    target = path_at(root)
    if not entries:
        try:
            target.unlink(missing_ok=True)
        except OSError:
            pass
        return
    tmp = target.with_name(f".{target.stem}.tmp")
    flags = os.O_WRONLY | os.O_CREAT | os.O_TRUNC
    fd = os.open(tmp, flags, 0o600)
    with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as fh:
        json.dump({"entries": entries}, fh, ensure_ascii=False, indent=1)
    os.replace(tmp, target)
    try:
        os.chmod(target, 0o600)
    except OSError:
        pass


def clean_entry(raw) -> dict:
    """One entry as the store keeps it, or a refusal in one line: spellings a list of words (a string with
    commas is split), a replacement, `for` a participant's name or None, the except phrases and the mark."""
    if not isinstance(raw, dict):
        raise NamesError(i18n.t("names.each_name"))
    spell = raw.get("real", raw.get("spellings"))
    if isinstance(spell, str):
        spell = spell.split(",")
    spell = [" ".join(str(s).split()) for s in (spell if isinstance(spell, list) else [])]
    spell = [s for s in spell if s]
    seen, kept = set(), []
    for s in spell:
        if s.lower() not in seen:
            seen.add(s.lower())
            kept.append(s)
    if not kept:
        raise NamesError(i18n.t("names.give_name"))
    if len(kept) > MOST_SPELLINGS:
        raise NamesError(i18n.t("names.too_many_spellings", n=MOST_SPELLINGS))
    to = " ".join(str(raw.get("to") if raw.get("to") is not None else raw.get("replacement") or "").split())
    if not to:
        raise NamesError(i18n.t("names.give_replacement"))
    who = " ".join(str(raw.get("for") or raw.get("in") or "").split())
    if who.lower() in ("everyone", "everybody", "all"):
        who = ""
    out = {"real": kept, "to": to, "for": who or None}
    # Review each, Also an ordinary word and Match case went with namesbuild (17 November 2026): read as nothing
    phrases = raw.get("except")
    if isinstance(phrases, str):
        # a list as the app, the command line and the MCP server send it; a string's phrases have semicolons
        # between, never commas, which a phrase may hold, "Potter, Harry" one phrase (namesfix)
        phrases = phrases.split(";")
    held: list[str] = []
    for x in (phrases if isinstance(phrases, list) else []):
        x = " ".join(str(x).split())
        if x and x.lower() not in {h.lower() for h in held}:
            held.append(x)
    if len(held) > MOST_EXCEPT:
        raise NamesError(i18n.t("names.too_many_except", n=MOST_EXCEPT))
    if held:
        out["except"] = held
    # the mark his Review and replace or Add wrote when he unticked one of its finds (namesbuild), kept only when set
    if raw.get("unticked") is True:
        out["unticked"] = True
    return out


def same_entry(a: dict, b: dict) -> bool:
    """Whether two entries are the same but for the mark: spellings, replacement, whom it is for, except phrases."""
    def key(e):
        return ([s.casefold() for s in e["real"]], e["to"], (e["for"] or "").casefold(),
                [x.casefold() for x in e.get("except") or ()])
    return key(a) == key(b)


def marks_carried(old: list[dict], new: list[dict]) -> list[dict]:
    """The app's Names to replace saved: each entry the same as one before keeps that one's mark, and an entry he
    edited loses it, since his own edit is his choice again (namesbuild). Answers the new list."""
    held = [e for e in old if e.get("unticked")]
    out = []
    for e in new:
        e = {k: v for k, v in e.items() if k != "unticked"}
        if any(same_entry(e, h) for h in held):
            e["unticked"] = True
        out.append(e)
    return out


def marks_kept(on_disk: list[dict], entries: list[dict]) -> list[dict]:
    """`entries` with the mark on each that is the same, by `same_entry`, as a marked entry of the list on disk, so a
    save of entries read before a write that marked one never drops that mark (namesfix2). Answers the list."""
    held = [e for e in on_disk if e.get("unticked")]
    return [dict(e, unticked=True) if not e.get("unticked") and any(same_entry(e, h) for h in held) else e
            for e in entries]


def marked(entries: list[dict]) -> set[int]:
    """The entries, from 0, his review has marked: every find of each is left by an agent's replace (namesbuild)."""
    return {n for n, e in enumerate(entries) if e.get("unticked")}


def with_marks(entries: list[dict], unticked) -> list[dict]:
    """The list with the mark on each entry, from 0, in `unticked`, the rest as they are."""
    return [dict(e, unticked=True) if n in unticked and not e.get("unticked") else e for n, e in enumerate(entries)]


def clean_entries(rows) -> list[dict]:
    if not isinstance(rows, list):
        raise NamesError(i18n.t("names.give_list"))
    if len(rows) > MOST_ENTRIES:
        raise NamesError(i18n.t("names.too_many_names", n=MOST_ENTRIES))
    return [clean_entry(r) for r in rows]


# ------------------------------------------------------------------ the rules

def variant_pattern(text: str) -> tuple[str, bool]:
    """A spelling's pattern, and whether it is initials (matched by case always)."""
    t = text.strip()
    if INITIALS.match(t):
        letters = [c for c in t if c.isalpha()]
        return r"\.?\s?".join(re.escape(c) for c in letters) + r"\.?", True
    return r"\s+".join(re.escape(w) for w in t.split()), False


def lower_find(found: str, spelling: str) -> bool:
    """Whether a find is a lower-case find of its spelling: its first letter lower case where the spelling's is not,
    "hope" for Hope, which is left as written unless he ticks it (namesbuild). A spelling the list writes in lower
    case ("de la Cruz") has no lower-case finds."""
    f = next((c for c in found if c.isalpha()), "")
    s = next((c for c in spelling if c.isalpha()), "")
    return bool(f) and f.islower() and not s.islower()


def applies(entry: dict, who) -> bool:
    mine = entry.get("for")
    return not mine or (who is not None and str(mine).strip().casefold() == str(who).strip().casefold())


_compiled: dict = {}


def compile_list(entries: list[dict], who):
    """One pattern for the entries that apply to `who` (everyone's alone when `who` is None), the longest
    spelling first, and for each alternative the entry it is and its spelling."""
    key = (json.dumps(entries, sort_keys=True), None if who is None else str(who).strip().casefold())
    if key in _compiled:
        return _compiled[key]
    alts = []
    for n, e in enumerate(entries):
        if not applies(e, who):
            continue
        for v in e["real"]:
            pat, initials = variant_pattern(v)
            body = f"(?:{pat})" if initials else f"(?i:{pat})"
            alts.append((len(v), n, body, v))
    alts.sort(key=lambda a: -a[0])
    parts, index = [], []
    for i, (_, n, body, v) in enumerate(alts):
        parts.append(f"(?P<g{i}>{body})")
        index.append((n, v))
    rx = re.compile(r"(?<![^\W_])(?:" + "|".join(parts) + r")(?![^\W_])") if parts else None
    if len(_compiled) > 64:
        _compiled.clear()
    _compiled[key] = (rx, index)
    return rx, index


_excepts: dict = {}


def except_rx(phrases: list[str]):
    """One pattern for an entry's except phrases, whole words, case ignored, a run of spaces matching any."""
    key = tuple(phrases)
    if key not in _excepts:
        if len(_excepts) > 256:
            _excepts.clear()
        body = "|".join(r"\s+".join(re.escape(w) for w in p.split()) for p in sorted(phrases, key=len, reverse=True))
        _excepts[key] = re.compile(r"(?<![^\W_])(?i:" + body + r")(?![^\W_])") if body else None
    return _excepts[key]


def find(text: str, entries: list[dict], who) -> list[dict]:
    """Every find in the text, in order: its entry (from 0), the words found, where, the replacement and whether
    it is a lower-case find (`lower_find`). A find inside one of its entry's except phrases is no find at all
    (namesop)."""
    rx, index = compile_list(entries, who)
    if rx is None or not text:
        return []
    out = []
    for m in rx.finditer(text):
        g = next(k for k, v in m.groupdict().items() if v is not None)
        n, spelling = index[int(g[1:])]
        out.append({"entry": n, "found": m.group(0), "to": entries[n]["to"], "at": m.start(), "end": m.end(),
                    "lower": lower_find(m.group(0), spelling)})
    spans: dict[int, list] = {}
    for n in {h["entry"] for h in out if entries[h["entry"]].get("except")}:
        ex = except_rx(entries[n]["except"])
        spans[n] = [(m.start(), m.end()) for m in ex.finditer(text)] if ex is not None else []
    if spans:
        out = [h for h in out if not any(s <= h["at"] and h["end"] <= e for s, e in spans.get(h["entry"], ()))]
    return out


def plain(text: str, entries: list[dict], who) -> str:
    """The text with every find replaced, no skip, a lower-case find left as written (namesbuild)."""
    out, last = [], 0
    for h in find(text, entries, who):
        if h["lower"]:
            continue
        out += [text[last:h["at"]], h["to"]]
        last = h["end"]
    out.append(text[last:])
    return "".join(out)


def mask(value, entries: list[dict]):
    """`value` with every spelling on the list masked in every string at any depth (a dict's values, a list's items),
    whatever its case, a lower-case find and an entry the researcher marked among them, an except phrase and the
    entry's participant ignored, each written as its entry's replacement. For an agent's answer, which never says a
    listed word (21 November 2026). A key of a dict is left as it is."""
    plain_entries = [{"real": e["real"], "to": e["to"], "for": None} for e in entries or []]
    if not plain_entries:
        return value

    def walk(v):
        if isinstance(v, str):
            out, last = [], 0
            for h in find(v, plain_entries, None):
                out += [v[last:h["at"]], h["to"]]
                last = h["end"]
            return "".join(out + [v[last:]]) if out else v
        if isinstance(v, dict):
            return {k: walk(x) for k, x in v.items()}
        if isinstance(v, (list, tuple)):
            return [walk(x) for x in v]
        return v
    return walk(value)


def read_skip(value) -> set[tuple[int, int]]:
    """A skip as a call gives it, `(entry, nth)` each from 1: strings "3:1" (one line with commas too), pairs
    [3, 1] or {"entry": 3, "nth": 1}. Refused in one line when one is none of those."""
    if value in (None, "", []):
        return set()
    items = value.split(",") if isinstance(value, str) else (list(value) if isinstance(value, (list, tuple)) else [value])
    out = set()
    for it in items:
        try:
            if isinstance(it, dict):
                a, b = int(it["entry"]), int(it["nth"])
            elif isinstance(it, (list, tuple)):
                a, b = int(it[0]), int(it[1])
            else:
                a, b = (int(x) for x in str(it).strip().split(":"))
        except (KeyError, IndexError, TypeError, ValueError):
            raise NamesError(i18n.t("names.skip_shape")) from None
        if a < 1 or b < 1:
            raise NamesError(i18n.t("names.skip_shape"))
        out.add((a, b))
    return out


# a title's full stop, which ends no sentence (namesfix): Dr. Ann, Mrs. Hill
SENTENCE_TITLES = frozenset(("dr", "mr", "mrs", "ms", "mx", "prof", "rev", "st", "sr", "jr", "fr", "sgt", "capt",
                             "col", "gen", "lt", "hon", "messrs", "mme", "mlle"))


def sentence_title(text: str, at: int) -> bool:
    """Whether the full stop at `at` closes a title such as Dr. or Mrs., the word before it alone."""
    if text[at] != ".":
        return False
    m = re.search(r"(\w+)$", text[:at])
    return bool(m) and m.group(1).casefold() in SENTENCE_TITLES and (m.start() == 0 or not text[m.start() - 1].isalnum())


def sentence_ends(text: str, m) -> bool:
    """Whether the match of `SENTENCE_END` ends a sentence: not a title's full stop, and not a mark closed by a
    quotation mark or bracket (a quoted `!` or `?` in the middle of a sentence) before a word in lower case (lowsfix)."""
    if sentence_title(text, m.start()):
        return False
    if text[m.start()] in ".!?" and m.end() - m.start() > 1:
        word = text[m.end():].lstrip()[:1]
        if word and word.islower():
            return False
    return True


def sentence(text: str, at: int, end: int) -> tuple[str, str]:
    """The words before and after a find to the ends of its sentence, for the app's review, which shows each find in
    its whole sentence (namesbuild): back to a full stop, question or exclamation mark followed by a space, or a line
    break, and on to the next, a title's full stop (Dr., Mrs.) ending none, each side cut at `SENTENCE` characters with an ellipsis."""
    start = 0
    for m in SENTENCE_END.finditer(text, 0, at):
        if sentence_ends(text, m):
            start = m.end()
    stop = len(text)
    m = next((m for m in SENTENCE_END.finditer(text, end) if sentence_ends(text, m)), None)
    if m is not None:
        stop = m.end() if text[m.start()] in ".!?" else m.start()
    before, after = text[start:at], text[end:stop]
    if len(before) > SENTENCE:
        cut = before[-SENTENCE:]
        before = "…" + (cut[cut.find(" ") + 1:] if " " in cut else cut)
    if len(after) > SENTENCE:
        cut = after[:SENTENCE]
        after = (cut[:cut.rfind(" ")] if " " in cut else cut) + "…"
    return quotes_balanced(before.lstrip(), after.rstrip())


def quotes_balanced(before: str, after: str) -> tuple[str, str]:
    """The words either side of a find with balanced double quotation marks, or none (namesfix2): a sentence cut
    inside a quotation, or a quote held in its marks and cut at a full stop, would otherwise show a closing mark with
    no opening one, or the other way round. A mark left alone at either end goes; if one is still left alone inside,
    every double mark goes."""
    tail = " .,;:!?…"
    # curly marks, each kind counted
    while (before + after).count("”") > (before + after).count("“") and "”" in after:
        i = after.rfind("”")
        after = after[:i] + after[i + 1:]
    while (before + after).count("“") > (before + after).count("”") and "“" in before:
        i = before.find("“")
        before = before[:i] + before[i + 1:]
    if (before + after).count("\"") % 2:
        if after.rstrip(tail).endswith("\""):
            i = len(after.rstrip(tail)) - 1
            after = after[:i] + after[i + 1:]
        elif before.lstrip().startswith("\""):
            before = before.replace("\"", "", 1)
        if (before + after).count("\"") % 2:
            before, after = before.replace("\"", ""), after.replace("\"", "")
    if (before + after).count("“") != (before + after).count("”"):
        before, after = (x.replace("“", "").replace("”", "") for x in (before, after))
    return before.lstrip(), after.rstrip()


class Run:
    """The names applied through one Add, one import or one replace: the finds in the order they come, each entry's
    finds counted across every file (its `nth`), and the skips left as written. `text` is one piece of text, with
    `where` saying whose it is, a dict the finds carry (the participant, the interview, the part and the turn).
    A lower-case find is left as written unless `take` names it, a find he ticked in the app, so no bulk replace and
    no agent ever replaces one, and every find of an entry in `hold` (from 0, the entries his review marked, for an
    agent's write or one he did not review) is left as written (namesbuild, 17 November 2026)."""

    def __init__(self, entries: list[dict], skip=(), take=(), hold=()):
        self.entries = entries
        self.skip = set(skip)
        self.take = set(take)
        self.hold = set(hold)
        self.tally: dict[int, int] = {}
        self.finds: list[dict] = []

    def __bool__(self) -> bool:
        return bool(self.entries)

    def text(self, text: str, who, where: dict, mirror: set | None = None, taken: set | None = None) -> str:
        """`text` with its finds replaced, the skipped ones kept. `mirror` is a set of `(entry, found words)`
        a passage's text left alone, which a quote of the passage leaves alone too and does not count. A lower-case
        find there is left unless `taken` holds the same `(entry, found words)`, those he ticked, and `mirror` does
        not, so a copy or a raw source never has one replaced in bulk, nor one he left unticked where the same words
        were ticked elsewhere (namesfix)."""
        if not self.entries or not text:
            return text
        out, last = [], 0
        for h in find(text, self.entries, who):
            out.append(text[last:h["at"]])
            last = h["end"]
            pair = (h["entry"], h["found"])
            if mirror is not None:
                if h["entry"] in self.hold:
                    skipped = True
                elif h["lower"]:
                    # replaced only when he ticked those words and left none of them as written in the same place:
                    # a copy cannot tell which of two finds alike he ticked, so it keeps both (namesfix M3)
                    skipped = pair not in (taken or set()) or pair in mirror
                else:
                    skipped = pair in mirror
                out.append(h["found"] if skipped else h["to"])
                continue
            n = self.tally[h["entry"]] = self.tally.get(h["entry"], 0) + 1
            key = (h["entry"] + 1, n)
            held = h["entry"] in self.hold
            if held:
                skipped = True
            elif h["lower"]:
                skipped = key not in self.take
            else:
                skipped = key in self.skip
            before, after = sentence(text, h["at"], h["end"])
            # the words of its sentence, for the app's own review alone (namesbuild), never an agent's answer
            self.finds.append({"entry": h["entry"] + 1, "nth": n, "found": h["found"], "to": h["to"],
                               "skipped": skipped, "lower": h["lower"], "held": held, "at": h["at"],
                               "where": dict(where), "before": before, "after": after})
            out.append(h["found"] if skipped else h["to"])
        out.append(text[last:])
        return "".join(out)

    def left(self, since: int) -> set:
        """What the finds since the `since`th left as written, for a quote to mirror."""
        return {(f["entry"] - 1, f["found"]) for f in self.finds[since:] if f["skipped"]}

    def took(self, since: int) -> set:
        """What the lower-case finds since the `since`th replaced, the ones he ticked, for a quote, a raw source or a
        copy to mirror."""
        return {(f["entry"] - 1, f["found"]) for f in self.finds[since:] if f["lower"] and not f["skipped"]}

    def unticked(self) -> set[int]:
        """The entries, from 0, one of whose finds with its capital a skip left as written, a find he unticked: the
        app's Replace or Add marks each (namesbuild)."""
        return {f["entry"] - 1 for f in self.finds
                if f["skipped"] and not f["lower"] and not f["held"] and (f["entry"], f["nth"]) in self.skip}

    # --- what a call is told

    def replaced(self) -> int:
        return sum(1 for f in self.finds if not f["skipped"])

    def counts(self) -> dict:
        """Counts only, no name: each entry that was found, its replacement, how many were replaced and left (the
        lower-case finds among those left as `lower`, and `held` for an entry his review marked), and where, by
        participant and interview, with `held`, how many marked entries were found. This is what an agent is
        told."""
        by: dict[int, dict] = {}
        for f in self.finds:
            e = by.setdefault(f["entry"], {"entry": f["entry"], "to": f["to"], "replaced": 0, "left": 0, "lower": 0,
                                           "in": {}, "parts": {}})
            e["left" if f["skipped"] else "replaced"] += 1
            if f["skipped"] and f["lower"]:
                e["lower"] += 1
            w = f["where"]
            e["parts"][w.get("part") or ""] = e["parts"].get(w.get("part") or "", 0) + 1
            spot = e["in"].setdefault((w.get("participant") or "", w.get("interview") or ""), 0)
            e["in"][(w.get("participant") or "", w.get("interview") or "")] = spot + 1
        rows = []
        for n in sorted(by):
            e = by[n]
            rows.append({"entry": n, "to": e["to"], "replaced": e["replaced"], "left": e["left"], "lower": e["lower"],
                         **({"held": True} if n - 1 in self.hold else {}),
                         "parts": dict(sorted(e["parts"].items())),
                         "in": [{"participant": p, "interview": i, "count": c} for (p, i), c in sorted(e["in"].items())]})
        return {"entries": len(self.entries), "replaced": self.replaced(), "left": len(self.finds) - self.replaced(),
                "held": sum(1 for r in rows if r.get("held")), "by_entry": rows}

    def preview(self) -> list[dict]:
        """For the app's own screen: every find with the words found, its place and whether it is skipped."""
        return [dict(f) for f in self.finds]


def say(counts: dict) -> str:
    """One line for a call's counts, no name: `3 replaced, 1 left as it is`."""
    if counts["left"]:
        return i18n.t("names.say_left", replaced=counts["replaced"], left=counts["left"])
    return i18n.t("names.say_replaced", replaced=counts["replaced"])


def lines(counts: dict) -> list[str]:
    """The counts as lines: `entry 3, [partner]: 2 in Wren, Interview`."""
    out = []
    for e in counts["by_entry"]:
        places = "; ".join(i18n.t("names.place", count=x["count"], participant=x["participant"],
                                  interview=x["interview"]) for x in e["in"])
        out.append(i18n.t("names.line_entry", entry=e["entry"], to=e["to"], places=places))
        # each key written out in its own call, so the check of keys in use finds it
        if e.get("held"):
            out.append(i18n.t("names.line_held", n=e["left"]))
        elif e.get("lower"):
            out.append(i18n.t("names.line_lower", n=e["lower"]))
    return out


# ------------------------------------------------------------------ a transcript's text, the copy kept

def render(turns, notes=None) -> str:
    """A transcript's turns as plain text, `[mm:ss] Name: words`, a note under its turn, for the copy kept in
    Source when the names were replaced (the original is not kept)."""
    out = []
    for i, (name, seconds, words) in enumerate(turns):
        stamp = ""
        if seconds is not None:
            s = int(seconds)
            stamp = f"[{s // 60:02d}:{s % 60:02d}] "
        out.append(f"{stamp}{name}: {words}".rstrip())
        held = notes[i] if notes and i < len(notes) and isinstance(notes[i], dict) else {}
        for key in ("en", "es"):
            if held.get(key):
                out.append("  Note: " + " ".join(str(held[key]).split()))
        if held.get("kq"):
            out.append("  Quote: " + " ".join(str(held["kq"]).split()))
    return "\n".join(out) + "\n"


# ------------------------------------------------------------------ a key read from, and written to, a file

def read_key(name: str, data: bytes) -> list[dict]:
    """A key, a CSV or an Excel file the researcher keeps, the real name or names (commas between spellings) then
    the pseudonym, and as the app writes one a third column, the except phrases with semicolons between, a first row
    of headings passed over when its second cell is "pseudonym" or "replace"-like. A key of four or five columns, as
    the app wrote one before namesbuild (Review each third, Except in fourth, Also an ordinary word fifth), known by
    its headings (`key_old_shape`), reads its names and its except phrases alone. Returns entries for everyone."""
    low = str(name).lower()
    rows: list[list] = []
    if low.endswith((".xlsx", ".xlsm")):
        import openpyxl
        wb = openpyxl.load_workbook(io.BytesIO(data), read_only=True, data_only=True)
        try:
            ws = wb.worksheets[0]
            for r in ws.iter_rows(values_only=True):
                rows.append([c for c in r[:5]])
        finally:
            wb.close()
    else:
        text = data.decode("utf-8-sig", errors="replace")
        rows = [r[:5] for r in csv.reader(io.StringIO(text))]
    at = 3 if key_old_shape(rows) else 2
    out = []
    for i, r in enumerate(rows):
        r = [("" if c is None else str(c)).strip() for c in (list(r) + ["", "", "", "", ""])[:5]]
        if not r[0] or not r[1]:
            continue
        if i == 0 and re.match(r"(?i)^(pseudonym|replace|replacement|alias|new)", r[1]):
            continue
        out.append(clean_entry({"real": r[0], "to": r[1], "except": r[at]}))
    if not out:
        raise NamesError(i18n.t("names.key_empty"))
    return out


# the old key's headings, its third column Review each (namesop to namesbuild), and the words a tick was written as
KEY_OLD_HEADS = ("review each", "review", "match case")
KEY_OLD_TICKS = ("", "yes", "y", "true", "1", "x", "no", "n", "false", "0")


def key_old_shape(rows: list[list]) -> bool:
    """Whether a key is the old shape, the except phrases fourth (namesfix L1): known by its heading row, a third
    heading the old one's, or with no heading row by a fourth or fifth cell holding something while every third cell
    is a tick or empty, never by how many cells a row has, so a trailing comma or a notes column after Except in
    never moves the except phrases."""
    def cell(r, n):
        return ("" if n >= len(r) or r[n] is None else str(r[n])).strip()
    if not rows:
        return False
    first = rows[0]
    if re.match(r"(?i)^(pseudonym|replace|replacement|alias|new)", cell(first, 1)):
        return cell(first, 2).casefold() in KEY_OLD_HEADS
    return (any(cell(r, 3) or cell(r, 4) for r in rows)
            and all(cell(r, 2).casefold() in KEY_OLD_TICKS for r in rows if cell(r, 0) and cell(r, 1)))


def write_key(entries: list[dict]) -> str:
    """The list as a CSV for another computer: the spellings joined with commas, the replacement and the except
    phrases with semicolons between (namesfix2). Entries for one participant lose that, and the mark stays here."""
    buf = io.StringIO()
    w = csv.writer(buf, lineterminator="\n")
    w.writerow([i18n.t("names.key_head_real"), i18n.t("names.key_head_to"), i18n.t("names.key_head_except")])
    for e in entries:
        w.writerow([", ".join(e["real"]), e["to"], "; ".join(e.get("except") or [])])
    return buf.getvalue()
