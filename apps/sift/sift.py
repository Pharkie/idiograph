#!/usr/bin/env python3
"""Sift: screening for a systematic review inside Idiograph, one record at a time.

A screening is a folder holding `screening.csv`, UTF-8 with a header and one record a row. `rec_id`,
`title` and `abstract` are required, and every other column is shown when present. Beside it Sift
keeps `screening.log.jsonl`, one JSON line for each act, appended and never rewritten. After each
act the CSV's decision columns, `decision` and `reason` at title and abstract and `ft_decision` and
`ft_reason` at full text, are written afresh from the log, through a temporary file and
`os.replace`, the full text pair added when the CSV lacks it. The review's proposal columns are
written only by `propose_review`, for the review's own side through the command line or MCP, and
Sift's own proposals, asked of the app's AI from the screen (see `sift_ai.py`), go in columns of
their own, `ai_proposed_decision`, `ai_proposed_reason` and `ai_grounds`, `ft_ai_` at full text.
What made the review's proposal is read from `proposed_by` or `ft_proposed_by`, keyword rules or
model: and its name, which Sift never writes, and the model that made Sift's own is written in
`ai_proposed_by`. Each decision's line in the log says whether it matched the suggestions the record
showed (see `suggestion_match`), and never which control made it. `reasons.csv` beside the CSV names the reason codes, `code,meaning`, each offered at both stages, or
in a file of before `stage,code,meaning`, each at its own stage, and `pdfs/<rec_id>.pdf`
is a record's PDF. A run's screening takes the PDF of a record that has none from the review's
earlier runs, by DOI or by title and year, when the run is made and each time it opens (see
`gather_pdfs`). `prisma.md` beside the CSV holds the PRISMA 2020 flow as Mermaid, written afresh
from the counts after every act that moves them. A second screener's side, `sift_second.py`, writes
lines of its own in the log, `act` `second`, which `read_log` passes over, so none moves a decision
of his, and the counts and the flow name the two screeners from them.

His own fields beside the decisions are columns of Sift's own too: `participants` and
`participants_confirmed`, `rating`, `notes`, `digest` and `critique`, and `col_<name>` for each
column he adds, named, typed and ordered in `sift.json` beside the CSV with the table's view, and
the table's filters and its find boxes' words kept there as he left them. Each
change is one line of the log, `field` or `column`, its old value and its new, and the CSV is
written whole under the lock as the decisions are. His key excerpts, words of a record's title or
abstract he keeps with H, are a column of Sift's own as well, `excerpts`, written by `excerpt` from the
screen alone, each kept or removed one `excerpt` line of the log that Undo takes back (14 October). A
participant count guessed from the abstract
is worked out on reading and never written until he confirms it or types his own. Each record's
number, 1 up by rec_id order, is kept in `sift.json` too, given when the screening is first opened
and to a record added later the next, so no sort, filter or new record ever changes one. A reject
carries one reason, and a reason an older line gives as two codes keeps its first. A sync to Zotero
writes each record's item key in a column of its own, `zotero_key`, through `write_zotero`, which no
other act touches and Start again keeps (see `sift_zotero.py`). A run writes each record's count of
citations, OpenAlex's by its DOI, in `cited_by` and the day it was asked in `cited_by_date`, and Find
citation counts fills both for a screening made before through `write_cited`, which no other act
touches and Start again keeps (see `sift_search.py`).

A screening that a later run of a review's searches carries from an earlier run opens its log with
one `follow` line, naming the earlier run's day, the records carried, those new and those found
again, and the earlier decisions, notes and fields of his come after it as `carry` lines, each
naming the earlier run's day and line of its log (see `sift_search.py`). A carried decision stands
as his own does, and Undo never takes one back. The counts and the flow count each record once and
say the records new in this run.

The files say include, maybe and exclude, the words the proposal column uses, and nothing for a
record not yet decided. The screen and the command line show them in each stage's words since 12
October, `SHOWN_WORDS`: title and abstract is a filter, Yes, Maybe and No, and full text the
decision, Include, Maybe and Exclude, a record waiting at either To screen. The words alone changed,
never what the files hold. The server, the command line and any later layer read and write a
screening through this module alone, which reads one through the family's `screenings.py`. It calls
no model and sends nothing anywhere. The standard library, `locks.py` and the family's `errors.py`,
`files.py`, `textfiles.py` and `screenings.py` only.

One writer at a time: `screening.lock` beside the CSV, an empty file, is the lock, taken as
`locks.py` takes every lock of the app, an exclusive `fcntl.flock` on it, `msvcrt.locking` on
Windows. Every act takes it, reads the CSV and the log afresh, appends to the log and writes the CSV
whole, then lets it go. Another writer, a script that adds records or fills the proposal columns,
takes the same lock the same way around its own read and write, and writes the CSV whole to a
temporary file in the folder and renames it over the old one. Rows are found by rec_id, never by
place, so a record added at the foot is read on the screen's next open and nothing is reordered or
dropped. `log.csv` beside the CSV, the search tool's record of each search, is read for the counts
of records identified.
"""
from __future__ import annotations

import formats
import sift_words
import contextlib
import csv
import io
import json
import os
import re
import tempfile
import unicodedata
from datetime import datetime
from pathlib import Path

import locks
from errors import WorkbookError
from files import now_iso, write_atomic  # noqa: F401  the family's, which Sift has always written through
from textfiles import BLOCK, TAG, plain  # noqa: F401  the family's, a record's markup taken out
import screenings
from errors import ScreeningError
# the screening as it is read, the family's since 22 October 2026 (family/screenings.py), which Trace
# reads too, kept by these names here
from screenings import CSV_NAME, PDF_DIR, REQUIRED, ZOTERO_COLUMN, Screening, csv_path, is_screening, pdf_path  # noqa: F401

LOG_NAME = "screening.log.jsonl"
REASONS_NAME = "reasons.csv"
COUNTS_NAME = "screening.counts.csv"
LOCK_NAME = "screening.lock"
SEARCHES_NAME = "log.csv"
PRISMA_NAME = "prisma.md"
# where a proposal came from, which each line of the log records beside it: the CSV's proposal
# columns, written by the review's own tooling, Sift's own, asked from the screen, or none
FROM_CSV = "csv"
FROM_SIFT = "sift"
TOOL = "Sift"
STAGES = ("ta", "ft")
STAGE_WORDS = {"ta": "title and abstract", "ft": "full text"}
# the stage as a sentence for a person names it, in the run's language (STAGE_WORDS is the files' and the command line's)
STAGE_SAID_KEYS = {"ta": "sift_server.stage.ta", "ft": "sift_server.stage.ft"}


def stage_said(stage) -> str:
    """The stage as a refusal or a line for a person says it, title and abstract or full text."""
    return sift_words.t("sift_server.stage.ft") if stage == "ft" else sift_words.t("sift_server.stage.ta")


DECISIONS = ("include", "maybe", "exclude")
# What a decision reads as at each stage (12 October): title and abstract is a filter, so Yes, Maybe
# and No, Yes and Maybe both going on to full text, and full text the decision, so Include, Maybe and
# Exclude, a record waiting at either To screen. Words only: the CSV, the log, sift.json and the second
# screener's files keep include, maybe and exclude, and an empty decision, as they always have.
SHOWN_WORDS = {"ta": {"include": "Yes", "maybe": "Maybe", "exclude": "No"},
               "ft": {"include": "Include", "maybe": "Maybe", "exclude": "Exclude"}}
TO_SCREEN = "To screen"
# his decision and reason at each stage, which Sift writes, and the proposal, which it never does, with
# what made it, `proposed_by` or `ft_proposed_by`, which Sift reads alone (14 October)
COLUMNS = {
    "ta": {"decision": "decision", "reason": "reason", "proposed": "proposed_decision",
           "proposed_reason": "proposed_reason", "grounds": "grounds", "by": "proposed_by"},
    "ft": {"decision": "ft_decision", "reason": "ft_reason", "proposed": "ft_proposed_decision",
           "proposed_reason": "ft_proposed_reason", "grounds": "ft_grounds", "by": "ft_proposed_by"},
}
PROPOSAL_COLUMNS = tuple(c[k] for c in COLUMNS.values() for k in ("proposed", "proposed_reason", "grounds", "by"))
DECISION_COLUMNS = tuple(c[k] for c in COLUMNS.values() for k in ("decision", "reason"))
# Sift's own proposals at each stage, in columns of their own, which the review's columns never share, the
# model that answered named in `ai_proposed_by` or `ft_ai_proposed_by` as Sift writes one (14 October)
AI_COLUMNS = {
    "ta": {"proposed": "ai_proposed_decision", "proposed_reason": "ai_proposed_reason", "grounds": "ai_grounds",
           "by": "ai_proposed_by"},
    "ft": {"proposed": "ft_ai_proposed_decision", "proposed_reason": "ft_ai_proposed_reason", "grounds": "ft_ai_grounds",
           "by": "ft_ai_proposed_by"},
}
AI_PROPOSAL_COLUMNS = tuple(c[k] for c in AI_COLUMNS.values() for k in ("proposed", "proposed_reason", "grounds", "by"))
# What made a suggestion, as its `proposed_by` cell says it (14 October, Adam's words): keyword rules, a model
# named after "model:", its name and version, or nothing said, any other words taken as nothing said. Sift's
# own are its AI's, the model named when Sift wrote it. A suggestion a model made is an AI suggestion, which
# shows only with the app's AI switch on, and one by keyword rules or that says nothing shows either way
BY_RULES = "keyword rules"
BY_MODEL = "model:"
BY_SIFT = "Sift's AI"
# a suggestion in the log's words, by what made it: its noun, and what goes in the brackets after it
SUGGESTION_SAID = {"rules": ("suggestion", "keyword rules, from the CSV"), "model": ("AI suggestion", "{model}, from the CSV"),
                   "unstated": ("suggestion", "from the CSV"), "sift": ("AI suggestion", "from Sift"),
                   "sift_model": ("AI suggestion", "{model}, from Sift")}
SCREENER_SAID = "The screener's decision"
# the proposals a record can hold, in the order the screen shows them, the review's first
SOURCES = ((FROM_CSV, COLUMNS), (FROM_SIFT, AI_COLUMNS))
# a record found by another method than a database search, by the words its sources give, as
# PRISMA 2020 counts websites, organisations and citation searching apart from the databases
OTHER_METHODS = re.compile(r"citation|reference|hand.?search|website|organi[sz]ation|expert|snowball|grey|gray|"
                           r"other method|manual|contact", re.I)
# a rec_id that runs in a sequence, R001 or G12, its letters and its number
SEQUENCE = re.compile(r"^(.*?)(\d+)$")
# the record's count of citations, OpenAlex's `cited_by_count` by its DOI, and the day it was asked,
# which a run writes and Find citation counts fills for a screening made before (12 October)
CITED_COLUMN = "cited_by"
CITED_DATE = "cited_by_date"
# Sift's own columns from OpenAlex and Crossref (13 October), which a run writes in the same pass as Cited
# by and Fill from OpenAlex fills for a screening made before: whether the paper was retracted, corrected
# or given an expression of concern, with each notice's DOI and date, OpenAlex's open access, the
# countries of the authors' institutions, OpenAlex's authors with their IDs, and the day each service
# was asked. A record's references, Crossref's and OpenAlex's, are kept beside the CSV in
# `screening.references.json`, so which key works it cites is worked out on reading.
RETRACTION_COLUMN = "retraction"
NOTICES_COLUMN = "retraction_notices"
OA_COLUMN = "open_access"
COUNTRIES_COLUMN = "countries"
AUTHORS_COLUMN = "openalex_authors"
OPENALEX_DATE = "openalex_date"
CROSSREF_DATE = "crossref_date"
FILLED = (CITED_COLUMN, CITED_DATE, RETRACTION_COLUMN, NOTICES_COLUMN, OA_COLUMN, COUNTRIES_COLUMN, AUTHORS_COLUMN,
          OPENALEX_DATE, CROSSREF_DATE)
# a record's keywords as the databases give them, the fullest list, or OpenAlex's for a record with none
# (14 October), which a run writes after the screening's own columns and Fill from OpenAlex fills where a
# record lacks them, never writing over any. The terms of the plan are found in them (see `record_match`).
KEYWORDS_COLUMN = "keywords"
# a record's language by its English name, English or Portuguese, several parted by semicolons as several
# choices are, empty when no source gives one (14 October). The review's own side writes it in some runs,
# added at the end of the header, so a column there is read and its values kept, and a run writes it at
# the end of its header from each database's own field, a record's own metadata before OpenAlex's
# detection from its text (see `sift_search.LANGUAGE_ORDER`), and Fill from OpenAlex fills an empty cell.
LANGUAGE_COLUMN = "language"
# each language's English name by its ISO 639-1 code and its ISO 639-2 codes, bibliographic and
# terminological, a code not here kept as given and undetermined, `und`, as none
LANGUAGE_NAMES = {}
for _name, _codes in (
        ("English", "en eng"), ("Portuguese", "pt por"), ("Spanish", "es spa"), ("French", "fr fre fra"),
        ("German", "de ger deu"), ("Italian", "it ita"), ("Dutch", "nl dut nld"), ("Chinese", "zh chi zho"),
        ("Japanese", "ja jpn"), ("Korean", "ko kor"), ("Russian", "ru rus"), ("Arabic", "ar ara"),
        ("Polish", "pl pol"), ("Turkish", "tr tur"), ("Swedish", "sv swe"), ("Norwegian", "no nor nb nob nn nno"),
        ("Danish", "da dan"), ("Finnish", "fi fin"), ("Greek", "el gre ell"), ("Hebrew", "he heb"),
        ("Hindi", "hi hin"), ("Czech", "cs cze ces"), ("Hungarian", "hu hun"), ("Romanian", "ro rum ron"),
        ("Catalan", "ca cat"), ("Persian", "fa per fas"), ("Indonesian", "id ind"), ("Malay", "ms may msa"),
        ("Thai", "th tha"), ("Vietnamese", "vi vie"), ("Ukrainian", "uk ukr"), ("Croatian", "hr hrv"),
        ("Serbian", "sr srp"), ("Slovak", "sk slo slk"), ("Slovenian", "sl slv"), ("Bulgarian", "bg bul"),
        ("Lithuanian", "lt lit"), ("Latvian", "lv lav"), ("Estonian", "et est"), ("Icelandic", "is ice isl"),
        ("Irish", "ga gle"), ("Welsh", "cy wel cym"), ("Afrikaans", "af afr"), ("Bengali", "bn ben"),
        ("Urdu", "ur urd"), ("Tamil", "ta tam"), ("Swahili", "sw swa"), ("Latin", "la lat"), ("Galician", "gl glg"),
        ("Basque", "eu baq eus"), ("Albanian", "sq alb sqi"), ("Armenian", "hy arm hye"), ("Georgian", "ka geo kat"),
        ("Macedonian", "mk mac mkd"), ("Bosnian", "bs bos"), ("Filipino", "tl tgl fil"), ("Punjabi", "pa pan"),
        ("Nepali", "ne nep"), ("Sinhala", "si sin"), ("Burmese", "my bur mya"), ("Khmer", "km khm"),
        ("Mongolian", "mn mon"), ("Kazakh", "kk kaz"), ("Uzbek", "uz uzb"), ("Azerbaijani", "az aze"),
        ("Amharic", "am amh"), ("Yoruba", "yo yor"), ("Zulu", "zu zul"), ("Maori", "mi mao mri")):
    LANGUAGE_NAMES.update({c: _name for c in _codes.split()})
    LANGUAGE_NAMES[_name.casefold()] = _name
del _name, _codes
# undetermined and no linguistic content, which name no language
NO_LANGUAGE = ("und", "zxx")
# what the retraction column holds, each kind once in this order, `none` once asked with none found
NOTICE_KINDS = ("retracted", "expression of concern", "corrected")
NO_NOTICE = "none"
# OpenAlex's kinds of open access, `closed` for none
OA_KINDS = ("diamond", "gold", "green", "hybrid", "bronze", "closed")
REFERENCES_NAME = "screening.references.json"
# the study a record is a report of, his own as a decision is, a plain label shared by the reports he
# links, Study 3, and empty for a record that stands alone (13 October)
STUDY_COLUMN = "study"
STUDY_LABEL = re.compile(r"Study (\d+)")
# the columns the record's head shows by name, and the rest shown after the abstract when they hold anything
SHOWN = ("rec_id", "title", "authors", "year", "journal", "doi", "sources", "abstract") + FILLED
FILTERS = ("undecided", "maybe", "accepted", "rejected", "all", "differs")
# a round named in the stages' words, each the round it has always been (12 October): to-screen the
# records not yet decided, yes or include those taken forward, no or exclude those left out
ROUND_SAID = {"to-screen": "undecided", "to screen": "undecided", "yes": "accepted", "include": "accepted",
              "no": "rejected", "exclude": "rejected"}
# the round Where we differ, the records where he and the second screener went different ways (see
# `sift_second.py`), a round of the screen and the command line beside the rest
APART = "apart"
# the act of every line the second screener's side writes in the log, which `read_log` passes over
SECOND_ACT = "second"
WORDS = {"include": "include", "included": "include", "accept": "include", "accepted": "include", "yes": "include",
         "exclude": "exclude", "excluded": "exclude", "reject": "exclude", "rejected": "exclude", "no": "exclude",
         "maybe": "maybe", "unsure": "maybe"}
STAGE_SAID = {"ta": "ta", "title and abstract": "ta", "title": "ta", "abstract": "ta", "tiab": "ta",
              "ft": "ft", "full text": "ft", "fulltext": "ft", "full": "ft", "full-text": "ft"}
SETTINGS_NAME = "sift.json"
# his own fields, each a column of Sift's own that no other writer touches, and the columns he adds,
# each `col_` and his name for it
FIELDS = ("participants", "rating", "notes", "digest", "critique")
# His key excerpts (14 October): words of a record's title or abstract he keeps with H on the screen to
# support his decision, as `q` keeps a quote on Experiential statements, each with the stage it was made
# at, its words and its pieces' offsets, so its marks come back. A column of Sift's own, `excerpts`, holds
# them as JSON in ASCII alone (see `excerpts_cell`), and only the screen writes it (see `excerpt`).
EXCERPTS_COLUMN = "excerpts"
EXCERPT_ACT = "excerpt"
EXCERPT_PLACES = ("title", "abstract")
EXCERPT_JOIN = " \u2026 "
EXCERPT_PIECES = 40
# a cell's most, under the 32,767 characters Excel keeps in one
EXCERPT_MAX = 30000
OWN_COLUMNS = ("participants", "participants_confirmed", "rating", "notes", "digest", "critique", STUDY_COLUMN,
               EXCERPTS_COLUMN)
OWN_PREFIX = "col_"
CONFIRMED = "yes"
RATING_MAX = 5
# the types of a column he adds: text, a choice list, or a whole number, a count of analysts say, which
# sorts as numbers and filters by a slider as the participants do (13 October), and for the form of
# Extract and appraise yes or no, several choices, long text and passages, each a quoted passage with its
# page (13 October, later). Set columns adds the first three, Set up the form any of them.
COLUMN_TYPES = ("text", "choice", "number", "yesno", "multi", "long", "passages")
TABLE_TYPES = ("text", "choice", "number")
CHOICE_TYPES = ("choice", "multi")
# the highest whole number a Number column takes
NUMBER_MAX = 10 ** 9
NAME_MAX = 80
# the table's columns of its own, in their first order, each shown or hidden at first, the column of
# the CSV it takes or how it is worked out, and how it sorts and filters. The abstract and the DOI are
# hidden at first, each read on the record (12 October), Cited by shows after Year, and a sift.json
# that holds his columns keeps them. The record's ID is in none of them: it is the table's first column
# always, in place of the record's number (13 October), so a sift.json that names it passes it over.
# The five columns of 13 October, Retracted or corrected, Open access, Country, Study and Cites key works,
# are hidden at first, each read on the record and offered by Set columns, and a retracted, corrected or
# questioned record says so beside its title in the table and on the record. Matched in, where a record's
# terms of each block were found or how a database found it without them (14 October, see `record_match`),
# is hidden at first too, and so is Language, the record's languages by name, after Country (14 October).
TABLE_COLUMNS = (("found", True), ("title", True), ("authors", True), ("year", True), ("cited", True),
                 ("abstract", False), ("participants", True), ("doi", False), ("pdf", True), ("decision", True),
                 ("study", False), ("rating", True), ("notes", False), ("digest", False), ("critique", False),
                 ("journal", False), ("retracted", False), ("oa", False), ("country", False), ("language", False),
                 ("keyworks", False), ("matched", False))
# the first columns a sift.json's columns were placed under, 2 since 12 October, when the abstract and
# the DOI came off the table at first: columns placed before it take both off once, and what he shows
# after it stands
FIRST = 2
FIRST_OFF = ("abstract", "doi")
# the filters' sidebar's width in pixels, which he drags, kept in sift.json within these
SIDEBAR_MIN, SIDEBAR_MAX = 180, 560
# and the PRISMA flow's sidebar's, kept beside it under `flow` (12 October)
FLOW_MIN, FLOW_MAX = 240, 720
VIEWS = ("record", "table")
# the table's filters kept in sift.json under `table`: `filters`, each column's ticks as a list, or for
# the columns a slider filters its two ends, `from` and `to`, either open as null, and `none`, the
# records with no number, and `find`, the words in a long group's find box, by column
RANGE_COLUMNS = ("year", "cited", "participants", "rating")
# a filter kept beyond the table's columns: At title and abstract, the group the table has at full text
# alone, where each record stood at the first stage (12 October), and Extract and appraise's Benchmark
# papers and Form, done or not (13 October, later). The groups of the plan's blocks, `term:` and the
# block's place, are kept too (see `TERM_KEY`).
STAGE_FILTERS = ("tadec", "bench", "formdone")
FILTER_MAX = 200
# a review column the table can show beyond its own, by its name in the CSV after this mark
EXTRA = "csv:"
# the column a search writes a record's web address in, which the record's head shows as a link
URL_COLUMN = "url"
# each record's number in sift.json, 1 up by rec_id order, kept once given, so a sort or a filter
# never changes it and a record added later takes the next
NUMBERS_KEY = "numbers"


class SiftError(WorkbookError):
    """A screening that cannot be read, or an act that cannot go ahead, said in one plain line."""


# ------------------------------------------------------------------ words

def decision_word(value) -> str:
    """A decision as the files hold it, include, maybe or exclude, from any of the words that mean
    one, and empty for anything else."""
    return WORDS.get(" ".join(str(value or "").split()).lower(), "")


def shown_word(stage, decision) -> str:
    """A decision as the screen shows it at a stage, Yes or Include and the rest, To screen for none
    (12 October). The files keep the decision as it was."""
    return SHOWN_WORDS[stage_key(stage)].get(decision_word(decision), TO_SCREEN)


def round_key(which) -> str:
    """A round as `listed` knows it, from its own name or the stages' words for it, refused otherwise."""
    key = " ".join(str(which or "").split()).lower()
    key = ROUND_SAID.get(key, key)
    if key not in FILTERS and key != APART:
        raise SiftError(sift_words.t("sift_server.the_round_is_to_screen"))
    return key


def stage_key(value) -> str:
    """`ta` or `ft` from either key or the stage's words, refused otherwise."""
    key = STAGE_SAID.get(" ".join(str(value or "").split()).lower())
    if not key:
        raise SiftError(sift_words.t("sift_server.the_stage_is_title_and"))
    return key


def is_own(name: str) -> bool:
    """Whether a column is one of his own fields or a column he added, which only Sift writes."""
    return name in OWN_COLUMNS or str(name).startswith(OWN_PREFIX)


def sources_of(text) -> list[str]:
    """The searches a record's `sources` names, each once, in the cell's order."""
    out = []
    for name in re.split(r"[;|]", str(text or "")):
        name = " ".join(name.split())
        if name and name not in out:
            out.append(name)
    return out


# ------------------------------------------------------------- the participant guess

UNITS = {"one": 1, "two": 2, "three": 3, "four": 4, "five": 5, "six": 6, "seven": 7, "eight": 8, "nine": 9,
         "ten": 10, "eleven": 11, "twelve": 12, "thirteen": 13, "fourteen": 14, "fifteen": 15, "sixteen": 16,
         "seventeen": 17, "eighteen": 18, "nineteen": 19}
TENS = {"twenty": 20, "thirty": 30, "forty": 40}
SMALL = ("one", "two", "three", "four", "five", "six", "seven", "eight", "nine")
WORD_NUMBER = (rf"(?:(?:{'|'.join(TENS)})(?:[-\s](?:{'|'.join(SMALL)}))?|fifty|"
               + "|".join(sorted(UNITS, key=len, reverse=True)) + ")")
# a number as digits, with a comma for the thousands, or in words up to fifty, never the end of a
# hyphened word, so fifty-one gives none
COUNT = rf"(?<![\w-])(\d{{1,3}}(?:,\d{{3}})+|\d+|{WORD_NUMBER})(?![\w-])"
# the people a study's count names, as abstracts name them
PEOPLE = ("participants?", "interviewees?", "respondents?", "informants?", "individuals?", "people", "persons?",
          "adults?", "adolescents?", "youths?", "children", "child", "women", "woman", "men", "man", "girls?", "boys?",
          "mothers?", "fathers?", "parents?", "patients?", "survivors?", "students?", "nurses?", "midwives", "midwife",
          "doctors?", "physicians?", "clinicians?", "practitioners?", "professionals?", "therapists?", "counsell?ors?",
          "carers?", "caregivers?", "veterans?", "users?", "members?", "volunteers?", "employees?", "workers?",
          "teachers?", "athletes?", "refugees?", "subjects?", "residents?")
# a word or two between the count and the people, "eight British adults", never a word that makes it
# a part of a larger whole or another thing counted
BETWEEN = r"(?:(?!(?:of|with|in|and|or|from|to|were|was|who|the|a|an|than|per|at|on|for|by)\b)(?![\d,]+\s)[A-Za-z0-9][\w-]*\s+){0,2}"
PEOPLE_RE = re.compile(rf"{COUNT}\s+{BETWEEN}({'|'.join(PEOPLE)})\b", re.I)
# the people named as a crowd, so a count past one never takes a word that names one, 178 patient
# experiences
CROWD = ("people", "children", "women", "men", "midwives")
N_RE = re.compile(r"(?<![\w-])n\s*=\s*(\d{1,3}(?:,\d{3})+|\d+)(?!\d|\.\d)", re.I)
SAMPLE_RE = re.compile(rf"\bsample(?:\s+size)?\s+of\s+{COUNT}(?=\s*[,.;:()]|\s*$)", re.I)
# a count split by kind, "six men and four women", which leaves the whole unsure
SPLIT_RE = re.compile(rf"\s+and\s+{COUNT}\s+{BETWEEN}(?:{'|'.join(PEOPLE)})\b", re.I)
GUESS_MAX = 9999


def number_of(text: str) -> int | None:
    """A count as digits or words, `twenty-three` 23, or None for anything else."""
    s = " ".join(str(text or "").lower().replace("-", " ").split())
    if re.fullmatch(r"\d{1,3}(?:,\d{3})+|\d+", s):
        return int(s.replace(",", ""))
    parts = s.split()
    if len(parts) == 1:
        return UNITS.get(s, TENS.get(s, 50 if s == "fifty" else None))
    if len(parts) == 2 and parts[0] in TENS and parts[1] in SMALL:
        return TENS[parts[0]] + UNITS[parts[1]]
    return None


def plausible(raw: str) -> int | None:
    """A count a study could report, never nought, never past GUESS_MAX, and never four digits that
    read as a year, 2019 participants."""
    n = number_of(raw)
    if n is None or n < 1 or n > GUESS_MAX:
        return None
    if re.fullmatch(r"(?:19|20)\d\d", raw.strip()):
        return None
    return n


def guess_participants(abstract) -> int | None:
    """The number of participants an abstract gives, by pattern alone, "n = 12", "N=8", "12
    participants", "twelve interviewees", "eight adults" or "a sample of 14.": the first plausible
    one in the text, and None when unsure, as when it gives the count split by kind and no whole."""
    text = plain(abstract)
    found: list[tuple[int, int]] = []
    for m in N_RE.finditer(text):
        n = plausible(m.group(1))
        if n is not None:
            found.append((m.start(), n))
    for m in SAMPLE_RE.finditer(text):
        n = plausible(m.group(1))
        if n is not None:
            found.append((m.start(), n))
    split_from = -1
    for m in PEOPLE_RE.finditer(text):
        if m.start() < split_from:
            continue
        tail = SPLIT_RE.match(text, m.end())
        if tail:
            split_from = tail.end()
            continue
        n = plausible(m.group(1))
        word = m.group(2).lower()
        if n is not None and (n == 1 or word in CROWD or word.endswith("s")):
            found.append((m.start(), n))
    return min(found)[1] if found else None


def natural(code: str) -> tuple:
    """E2 before E10."""
    return tuple(int(p) if p.isdigit() else p.lower() for p in re.split(r"(\d+)", str(code)))


def case_free(ch: str) -> str:
    """A character in lower case where that keeps it one character, so an offset into the text still counts true."""
    low = ch.lower()
    return low if len(low) == 1 else ch


def ground_spans(text: str, grounds: str) -> tuple[list[list[int]], bool | None]:
    """Where the grounds stand in the text, whitespace and case set aside and nothing looser, as
    `[start, end]` offsets into it, and whether every piece was found, None when there are no grounds.
    Pieces joined by an ellipsis are each found, in order where they can be. Case is set aside since 17
    October, where "ten plot holders described" went unfound in an abstract that opens "Ten plot holders
    described". It changes what the screen says of a suggestion's grounds, never a decision."""
    pieces = [p for p in re.split(r"\s*(?:\.\.\.|…)\s*", plain(grounds)) if p.strip()]
    if not pieces:
        return [], None
    kept, at = [], []
    for i, ch in enumerate(text):
        if not ch.isspace():
            kept.append(case_free(ch))
            at.append(i)
    hay = "".join(kept)
    spans, missing, start = [], 0, 0
    for piece in pieces:
        needle = "".join(case_free(ch) for ch in "".join(piece.split()))
        k = hay.find(needle, start)
        if k < 0:
            k = hay.find(needle)
        if k < 0 or not needle:
            missing += 1
            continue
        spans.append([at[k], at[k + len(needle) - 1] + 1])
        start = k + len(needle)
    return sorted(spans), missing == 0


# ----------------------------------------------------------------- the CSV

def log_path(folder) -> Path:
    return Path(folder) / LOG_NAME


def lock_path(folder) -> Path:
    return Path(folder) / LOCK_NAME


def stamp(folder) -> list:
    """The CSV's and the log's modification time and size, which change with any write, so the
    screen reads the screening again only when another writer has touched it."""
    out = []
    for path in (csv_path(folder), log_path(folder)):
        try:
            st = path.stat()
            out += [st.st_mtime_ns, st.st_size]
        except OSError:
            out += [0, 0]
    return out


def has_records(folder) -> bool:
    """Whether a screening's CSV holds a record below its header, as a run that brought none, written
    before such a run wrote no CSV, does not. Only reads."""
    try:
        with open(csv_path(folder), encoding="utf-8-sig", newline="") as fh:
            rows = csv.reader(fh)
            next(rows, None)
            return any(any(cell.strip() for cell in row) for row in rows)
    except (OSError, UnicodeDecodeError, csv.Error):
        return False


def load(folder) -> Screening:
    """The screening in `folder`, refused in one line when it has no CSV, the CSV lacks a required
    column, or a record has no rec_id or shares one, read as the family's `screenings.py` reads it."""
    try:
        return screenings.load(folder)
    except ScreeningError as exc:
        raise SiftError(str(exc)) from None


def csv_text(sc: Screening) -> str:
    out = io.StringIO(newline="")
    writer = csv.writer(out, lineterminator=sc.newline)
    writer.writerow(sc.header)
    writer.writerows(sc.rows)
    return ("﻿" if sc.bom else "") + out.getvalue()


# ----------------------------------------------------------------- the log

def read_log(folder) -> list[dict]:
    """Every act of his in the log, oldest first. A line that is not JSON, the end of a write a crash
    cut short, is passed over, and so is every line of the second screener's, `act` `second` (see
    `sift_second.py`), so none of theirs ever moves a decision of his."""
    path = log_path(folder)
    if not path.is_file():
        return []
    out = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            entry = json.loads(line)
        except ValueError:
            continue
        if his_line(entry):
            out.append(entry)
    return out


def his_line(entry) -> bool:
    """Whether a line of the log is an act of his on a record at a stage, as `read_log` reads them."""
    return (isinstance(entry, dict) and bool(entry.get("rec_id")) and entry.get("act") != SECOND_ACT
            and bool(STAGE_SAID.get(str(entry.get("stage", "")).lower())))


def excerpt_line(entry) -> bool:
    """Whether a line of the log keeps or removes a key excerpt of his, or undoes one, lines that carry no
    stage of their own, since each excerpt carries its own (see `excerpt`)."""
    return (isinstance(entry, dict) and bool(entry.get("rec_id")) and entry.get("field") == EXCERPTS_COLUMN
            and entry.get("act") in (EXCERPT_ACT, "undo"))


def undo_lines(folder) -> list[dict]:
    """The lines Undo reads, oldest first: his acts as `read_log` reads them, and since 14 October his key
    excerpts and their undos, so one Undo takes back the newest of them all."""
    return [e for e in read_lines(folder) if his_line(e) or excerpt_line(e)]


def next_n(folder) -> int:
    path = log_path(folder)
    if not path.is_file():
        return 1
    return sum(1 for line in path.read_text(encoding="utf-8").splitlines() if line.strip()) + 1


def append(folder, entry: dict) -> None:
    """One line added to the end of the log, flushed to the disk. Nothing before it is touched."""
    path = log_path(folder)
    with open(path, "ab") as fh:
        if fh.tell() > 0:
            with open(path, "rb") as held:
                held.seek(-1, os.SEEK_END)
                if held.read(1) != b"\n":
                    fh.write(b"\n")
        fh.write((json.dumps(entry, ensure_ascii=False) + "\n").encode("utf-8"))
        fh.flush()
        os.fsync(fh.fileno())


def follow_of(folder) -> dict | None:
    """The first line of a screening's log when it is `follow`, the line a run that follows an earlier
    one opens its log with, naming the earlier run, the records carried, those new and those found
    again, or None."""
    path = log_path(folder)
    try:
        with open(path, encoding="utf-8") as fh:
            first = fh.readline()
        entry = json.loads(first) if first.strip() else None
    except (OSError, ValueError, UnicodeDecodeError):
        return None
    return entry if isinstance(entry, dict) and entry.get("act") == "follow" else None


def carried_of(folder) -> set[str] | None:
    """The records a screening carried from the earlier run it follows, or None when it follows none."""
    f = follow_of(folder)
    return {str(r) for r in f.get("records") or []} if f else None


def states(entries: list[dict]) -> dict[tuple[str, str], dict]:
    """The last act on each record at each stage, which holds where it stands, a decision carried
    from an earlier run among them."""
    held: dict[tuple[str, str], dict] = {}
    for entry in entries:
        held[(str(entry["rec_id"]), STAGE_SAID[str(entry["stage"]).lower()])] = entry
    return held


def first_reason(value) -> str:
    """A reject's reason as one code, one reason a record: the first of two or more that an older line
    or cell names, parted by a semicolon, a comma or a bar, or the first of a list."""
    if isinstance(value, (list, tuple)):
        value = next((v for v in value if str(v or "").strip()), "")
    parts = [p.strip() for p in re.split(r"[;,|]", str(value or "")) if p.strip()]
    return parts[0] if parts else ""


def state_of(sc: Screening, held: dict, rec: str, stage: str) -> dict:
    """Where a record stands at a stage: the log's last act on it, or with none the CSV's own cells. A
    reason that names two codes keeps its first."""
    entry = held.get((rec, stage))
    if entry is not None:
        return {"decision": decision_word(entry.get("decision")), "reason": first_reason(entry.get("reason")),
                "note": str(entry.get("note") or ""), "at": entry.get("at")}
    cols = COLUMNS[stage]
    decision = decision_word(sc.cell(rec, cols["decision"]))
    return {"decision": decision, "reason": first_reason(sc.cell(rec, cols["reason"])) if decision else "",
            "note": "", "at": None}


def made_by(source: str, cell) -> dict:
    """What made a suggestion, from its source and its `proposed_by` cell (14 October): `kind` rules,
    model or unstated for the review's, sift or sift_model for Sift's own, `by` as the log keeps it,
    keyword rules, model: and its name, Sift's AI or nothing, `model` the name alone, and `ai`, whether a
    model made it."""
    said = " ".join(str(cell or "").split())
    model = said[len(BY_MODEL):].strip() if said.lower().startswith(BY_MODEL) else ""
    if source == FROM_SIFT:
        return {"kind": "sift_model" if model else "sift", "by": f"{BY_MODEL} {model}" if model else BY_SIFT,
                "model": model, "ai": True}
    if said.lower().startswith(BY_MODEL):
        return {"kind": "model", "by": f"{BY_MODEL} {model}".rstrip(), "model": model, "ai": True}
    if said.lower() == BY_RULES:
        return {"kind": "rules", "by": BY_RULES, "model": "", "ai": False}
    return {"kind": "unstated", "by": "", "model": "", "ai": False}


def proposals_of(sc: Screening, rec: str, stage: str) -> list[dict]:
    """Every proposal the CSV holds now for a record at a stage, the review's first, `source` `csv`,
    then Sift's own, `source` `sift`, each with its decision, reason and grounds, and what made it (see
    `made_by`)."""
    out = []
    for source, table in SOURCES:
        cols = table[stage]
        decision = decision_word(sc.cell(rec, cols["proposed"]))
        if decision:
            out.append(dict({"decision": decision, "reason": sc.cell(rec, cols["proposed_reason"]).strip(),
                             "grounds": sc.cell(rec, cols["grounds"]).strip(), "source": source},
                            **made_by(source, sc.cell(rec, cols["by"]))))
    return out


def proposal_of(sc: Screening, rec: str, stage: str) -> dict:
    """The proposal the screen shows first for a record at a stage, the one Enter takes and the log
    records: the review's when the CSV holds one, else Sift's own, or empty with none."""
    found = proposals_of(sc, rec, stage)
    return found[0] if found else {"decision": "", "reason": "", "grounds": "", "source": "", "kind": "", "by": "",
                                   "model": "", "ai": False}


def suggestions_shown(sc: Screening, rec: str, stage: str, ai_on: bool) -> list[dict]:
    """The suggestions the record shows at a stage, two at most, the review's first: every one with the
    app's AI switch on, and with it off those by keyword rules or that say nothing of what made them (14
    October, Adam's choice)."""
    return [p for p in proposals_of(sc, rec, stage) if ai_on or not p["ai"]][:2]


def matched_of(st: dict, p: dict) -> bool:
    """Whether his decision is a suggestion's, the same decision and, for an exclude, the same reason."""
    return st["decision"] == p["decision"] and (st["decision"] != "exclude" or st["reason"] == p["reason"])


def suggestion_match(sc: Screening, rec: str, stage: str, st: dict, ai_on: bool) -> dict:
    """What a decision's line records of the suggestions shown with it (14 October): `matched_suggestion`,
    yes when his decision and reason are a suggestion's, no when they are none of them, empty with none
    shown, `suggestion_source` and `suggestion_by` of the one it matched, else of the first shown, and with
    two shown `other_suggestion`, the other's source, what made it and whether it matched. Never which
    button made the decision, which the screen does not say."""
    shown = suggestions_shown(sc, rec, stage, ai_on)
    if not shown:
        return {"matched_suggestion": "", "suggestion_source": "", "suggestion_by": ""}
    hit = next((p for p in shown if matched_of(st, p)), None)
    first = hit or shown[0]
    out = {"matched_suggestion": "yes" if hit else "no", "suggestion_source": first["source"], "suggestion_by": first["by"]}
    other = next((p for p in shown if p is not first), None)
    if other is not None:
        out["other_suggestion"] = {"source": other["source"], "by": other["by"], "matched": "yes" if matched_of(st, other) else "no"}
    return out


def suggestion_label(source: str, by: str) -> str:
    """A suggestion in the log's words, from its source and what made it: "the suggestion (keyword rules, from
    the CSV)", "the AI suggestion (Opus 5.5, from the CSV)" and the like, AI only where a model made it."""
    model = by[len(BY_MODEL):].strip() if by.lower().startswith(BY_MODEL) else ""
    if source == FROM_SIFT:
        kind = "sift_model" if model else "sift"
    else:
        kind = "model" if by.lower().startswith(BY_MODEL) else "rules" if by == BY_RULES else "unstated"
    noun, detail = SUGGESTION_SAID[kind]
    return f"the {noun} ({detail.format(model=model or 'a model')})"


def suggestion_words(entry: dict) -> str:
    """What a decision's line says of the suggestions shown with it, in plain words, or nothing when none
    was shown: "The screener's decision matched the suggestion (keyword rules, from the CSV)", "did not
    match", and the other suggestion after "and" when two were shown."""
    said = str(entry.get("matched_suggestion") or "")
    if said not in ("yes", "no"):
        return ""
    verb = lambda m: "matched" if m == "yes" else "did not match"
    out = f"{SCREENER_SAID} {verb(said)} {suggestion_label(str(entry.get('suggestion_source') or ''), str(entry.get('suggestion_by') or ''))}"
    other = entry.get("other_suggestion")
    if isinstance(other, dict):
        out += f" and {verb(other.get('matched'))} {suggestion_label(str(other.get('source') or ''), str(other.get('by') or ''))}"
    return out


def proposal_seen(sc: Screening, held: dict, rec: str, stage: str) -> dict:
    """The proposal his decision stands against: the one the log's last act on the record recorded,
    the proposal on the screen when he acted, or with no act the CSV's now. The counts and the round
    of decisions that differ both take it, so a proposal changed after he decided never moves them."""
    entry = held.get((rec, stage))
    seen = entry.get("proposal") if entry is not None else None
    if isinstance(seen, dict):
        decision = decision_word(seen.get("decision"))
        return {"decision": decision, "reason": str(seen.get("reason") or "") if decision else "",
                "source": str(seen.get("source") or (FROM_CSV if decision else "")) if decision else ""}
    now = proposal_of(sc, rec, stage)
    return {k: now[k] for k in ("decision", "reason", "source")}


def in_stage(sc: Screening, held: dict, rec: str, stage: str) -> bool:
    """Title and abstract holds every record, and full text every record with Yes or Maybe there."""
    return stage == "ta" or state_of(sc, held, rec, "ta")["decision"] in ("include", "maybe")


def rebuild(sc: Screening, entries: list[dict]) -> bool:
    """The CSV's decision columns written afresh from the log, for every record the log names, the
    rest as they were. `decision` and `reason`, or `ft_decision` and `ft_reason`, go after the last
    column when the CSV lacks them. Written through a temporary file and `os.replace`, and only when
    something changed. The answer is whether it wrote."""
    held = states(entries)
    before = csv_text(sc)
    for stage in STAGES:
        named = [rec for (rec, st) in held if st == stage and rec in sc.at]
        if not named:
            continue
        cols = COLUMNS[stage]
        for rec in named:
            st = state_of(sc, held, rec, stage)
            set_cells(sc, rec, {cols["decision"]: st["decision"], cols["reason"]: st["reason"]})
    after = csv_text(sc)
    if after == before:
        return False
    write_atomic(csv_path(sc.folder), after)
    return True


def set_cells(sc: Screening, rec: str, values: dict) -> None:
    """Cells of one record set by column name, a column the CSV lacks added after the last one,
    every other row given it empty."""
    for name in values:
        if name not in sc.col:
            sc.col[name] = len(sc.header)
            sc.header.append(name)
            for row in sc.rows:
                row.append("")
    row = sc.rows[sc.at[rec]]
    while len(row) < len(sc.header):
        row.append("")
    for name, value in values.items():
        row[sc.col[name]] = value


# ----------------------------------------------------------------- reasons

def reasons(folder, sc: Screening | None = None) -> dict:
    """The reason codes of each stage, in the file's order, from `reasons.csv` beside the CSV, with
    every code a proposal names that the file does not after them, bare. `file` says whether the file
    is there, and `said` is one line when it cannot be read."""
    out = {"ta": [], "ft": [], "file": False, "said": ""}
    path = Path(folder) / REASONS_NAME
    if path.is_file():
        out["file"] = True
        try:
            rows = list(csv.reader(io.StringIO(path.read_bytes().decode("utf-8-sig"), newline="")))
        except (UnicodeDecodeError, OSError, csv.Error):
            rows = []
        head = [h.strip().lower() for h in rows[0]] if rows else []
        if "code" not in head:
            out["said"] = sift_words.t("sift_server.needs_the_columns_code_and", reasons_name=REASONS_NAME)
        else:
            at = {name: head.index(name) for name in ("stage", "code", "meaning") if name in head}
            pick = lambda row, name: row[at[name]].strip() if name in at and at[name] < len(row) else ""
            for row in rows[1:]:
                code = pick(row, "code")
                if not code:
                    continue
                said = pick(row, "stage")
                stages = STAGES if not said else ([STAGE_SAID[said.lower()]] if said.lower() in STAGE_SAID else [])
                for stage in stages:
                    if all(r["code"] != code for r in out[stage]):
                        out[stage].append({"code": code, "meaning": pick(row, "meaning")})
    if sc is not None:
        for stage in STAGES:
            known = {r["code"] for r in out[stage]}
            # an exclude's reason alone, since a reason on an include or a maybe, a review's own words among them,
            # is no reason to exclude and was offered with No in red until 17 October
            bare = {p["reason"] for rec in sc.ids for p in proposals_of(sc, rec, stage)
                    if p["decision"] == "exclude"} - known - {""}
            out[stage] += [{"code": code, "meaning": ""} for code in sorted(bare, key=natural)]
    return out


def reason_problem(stage: str, reason: str, codes: list[str], lower: bool = False) -> str:
    """What is wrong with a reject's reason at a stage, or empty (12 October, later). At full text a
    reject takes one of the stage's codes whenever it has any, since PRISMA 2020's flow diagram gives
    reasons for the reports excluded there, and at title and abstract a reason is optional, one given
    being a code of the stage."""
    if not reason:
        if stage != "ft" or not codes:
            return ""
        # after a proposal's name, as a part of its line
        if lower:
            return sift_words.t("sift_server.exclude_needs_reason_after", codes=', '.join(codes))
        return sift_words.t("sift_server.exclude_at_full_text_takes", codes=', '.join(codes))
    return sift_words.t("sift_server.is_not_a_reason_code", reason=reason, stage=stage_said(stage)) if codes and reason not in codes else ""


# ----------------------------------------------------------------- the acts

def answer(sc: Screening, entries: list[dict], rec: str | None = None, extras: dict | None = None) -> dict:
    """What every act answers: the record as the screen draws it, its proposals as the CSV now holds
    them among it, the counts, the flow drawn from them, what Undo would take back and the stamp the
    files now carry. `extras` is the screening's own (see `extras_of`), worked out here when not given."""
    held = states(entries)
    c = counts(sc, entries)
    out = {"counts": c, "prisma": prisma_source(c), "undo": undo_said(entries, sc.folder), "stamp": stamp(sc.folder)}
    if rec is not None:
        out["rec_id"] = rec
        out["record"] = record_view(sc, held, rec, extras=extras)
        out["stages"] = {stage: {k: out["record"]["stages"][stage][k] for k in ("decision", "reason", "note", "at", "in")}
                         for stage in STAGES}
    return out


def entry_for(sc: Screening, held: dict, rec: str, stage: str, act: str, st: dict, tool: str, n: int) -> dict:
    was = state_of(sc, held, rec, stage)
    proposal = proposal_of(sc, rec, stage)
    return {"n": n, "at": now_iso(), "act": act, "rec_id": rec, "stage": STAGE_WORDS[stage],
            "decision": st["decision"], "reason": st["reason"], "note": st["note"],
            "proposal": {"decision": proposal["decision"], "reason": proposal["reason"], "source": proposal["source"]},
            "was": {"decision": was["decision"], "reason": was["reason"], "note": was["note"]}, "tool": tool}


def checked(sc: Screening, held: dict, rec_id, stage) -> tuple[str, str]:
    rec = str(rec_id or "").strip()
    stage = stage_key(stage)
    if rec not in sc.at:
        raise SiftError(sift_words.t("sift_server.there_is_no_record_in", rec=rec or sift_words.t("sift_server.none_named"), csv_name=CSV_NAME))
    if not in_stage(sc, held, rec, stage):
        raise SiftError(sift_words.t("sift_server.did_not_go_on_to", rec=rec))
    return rec, stage


def clean_note(text) -> str:
    return "\n".join(line.rstrip() for line in str(text or "").strip().splitlines())


def decide(folder, rec_id, stage, decision, reason: str = "", note=None, tool: str = TOOL,
           wait: float | None = None, second: dict | None = None, ai_on: bool = False) -> dict:
    """His decision on a record at a stage: one line added to the log, then the CSV's decision columns
    written afresh. A reject's reason is optional at title and abstract and required at full text
    whenever the stage has codes, and one given is a code of the stage (see `reason_problem`). Include
    and maybe carry none. `note` None keeps the note as it stands. A decision that changes nothing writes
    nothing. `second` is the project's second screener settings, which the server passes, so a
    decision on a calibration record is marked so in the log, and a decision that completes a draw
    unblinds it or records its agreement (see `sift_second.py`). `ai_on` is the app's AI switch, which
    the server passes, so the line says whether his decision matched the suggestions shown with it (see
    `suggestion_match`)."""
    import sift_second  # here, since it reads this module first
    word = decision_word(decision)
    if word not in DECISIONS:
        raise SiftError(sift_words.t("sift_server.the_decision_is_yes_maybe"))
    with locks.held(lock_path(folder), wait):
        sc = load(folder)
        entries = read_log(folder)
        held = states(entries)
        rec, stage = checked(sc, held, rec_id, stage)
        entry = decide_in(sc, entries, rec, stage, word, reason, note, tool,
                          sift_second.marks(sc, entries, rec, stage, second), ai_on)
        if entry is None:
            return dict(answer(sc, entries, rec), changed=False)
        rebuild(sc, entries)
        sift_second.settle(sc, entries, second, tool)
        return dict(settled(sc, entries, rec), changed=True)


def decide_in(sc: Screening, entries: list[dict], rec: str, stage: str, word: str, reason, note, tool: str,
              extra: dict | None = None, ai_on: bool = False) -> dict | None:
    """One decision of his written to the log, the caller holding the lock and having checked the
    record and the stage, `extra` added to its line: the reason checked against the stage's codes, the
    note kept when `note` is None, and whether it matched the suggestions shown with it, `ai_on` the
    app's AI switch (see `suggestion_match`). Answers the line, or None when it changes nothing."""
    held = states(entries)
    reason = str(reason or "").strip() if word == "exclude" else ""
    codes = [r["code"] for r in reasons(sc.folder, sc)[stage]]
    said = reason_problem(stage, reason, codes) if word == "exclude" else ""
    if said:
        raise SiftError(said)
    was = state_of(sc, held, rec, stage)
    st = {"decision": word, "reason": reason, "note": was["note"] if note is None else clean_note(note)}
    if all(st[k] == was[k] for k in st):
        return None
    entry = entry_for(sc, held, rec, stage, "decide", st, tool, next_n(sc.folder))
    entry.update(suggestion_match(sc, rec, stage, st, ai_on))
    entry.update(extra or {})
    append(sc.folder, entry)
    entries.append(entry)
    return entry


def settled(sc: Screening, entries: list[dict], rec: str | None = None, extras: dict | None = None) -> dict:
    """An act's answer, with `prisma.md` written afresh from its counts when they moved the flow."""
    out = answer(sc, entries, rec, extras)
    write_prisma(sc.folder, out["prisma"])
    return out


def note(folder, rec_id, stage, text, tool: str = TOOL, wait: float | None = None) -> dict:
    """A note on a record at a stage, its decision and reason as they stand, one line in the log."""
    with locks.held(lock_path(folder), wait):
        sc = load(folder)
        entries = read_log(folder)
        held = states(entries)
        rec, stage = checked(sc, held, rec_id, stage)
        was = state_of(sc, held, rec, stage)
        st = dict(was, note=clean_note(text))
        if st["note"] == was["note"]:
            return dict(answer(sc, entries, rec), changed=False)
        entry = entry_for(sc, held, rec, stage, "note", st, tool, next_n(folder))
        append(folder, entry)
        entries.append(entry)
        rebuild(sc, entries)
        return dict(settled(sc, entries, rec), changed=True)


def undo_target(entries: list[dict]) -> dict | None:
    """The newest decision, note or key excerpt kept or removed not yet undone, which Undo takes back, so a
    second Undo takes back the one before it. `entries` as `read_log` reads them hold no excerpt, and as
    `undo_lines` reads them they hold his excerpts too."""
    undone = {e.get("undoes") for e in entries if e.get("act") == "undo"}
    for entry in reversed(entries):
        if entry.get("act") in ("decide", "note", EXCERPT_ACT) and entry.get("n") not in undone:
            return entry
    return None


def undo_said(entries: list[dict], folder=None) -> dict | None:
    """What Undo would take back, its record, stage and line, and `what`, `excerpt` for a key excerpt, whose
    stage is the one it was made at. With `folder` the log is read for his excerpts too (see `undo_lines`)."""
    target = undo_target(undo_lines(folder) if folder is not None else entries)
    if target is None:
        return None
    if target.get("act") == EXCERPT_ACT:
        item = target.get("excerpt") if isinstance(target.get("excerpt"), dict) else {}
        return {"rec_id": target["rec_id"], "stage": item.get("stage") if item.get("stage") in STAGES else "ta",
                "n": target.get("n"), "what": EXCERPT_ACT}
    return {"rec_id": target["rec_id"], "stage": STAGE_SAID[str(target["stage"]).lower()], "n": target.get("n")}


def undo(folder, tool: str = TOOL, wait: float | None = None, second: dict | None = None) -> dict:
    """Undo: one more line in the log, putting the record back where it stood before the newest
    decision, note or key excerpt kept or removed not yet undone, then the CSV written afresh. Nothing
    in the log is removed."""
    with locks.held(lock_path(folder), wait):
        sc = load(folder)
        entries = read_log(folder)
        target = undo_target(undo_lines(folder))
        if target is None:
            return dict(answer(sc, entries), undone=None)
        if target.get("act") == EXCERPT_ACT:
            return undo_excerpt(sc, entries, target, tool)
        held = states(entries)
        rec, stage = str(target["rec_id"]), STAGE_SAID[str(target["stage"]).lower()]
        if rec not in sc.at:
            raise SiftError(sift_words.t("sift_server.is_no_longer_in_so_2", rec=rec, csv_name=CSV_NAME))
        back = target.get("was") or {}
        st = {"decision": decision_word(back.get("decision")), "reason": str(back.get("reason") or ""),
              "note": str(back.get("note") or "")}
        entry = entry_for(sc, held, rec, stage, "undo", st, tool, next_n(folder))
        entry["undoes"] = target.get("n")
        append(folder, entry)
        entries.append(entry)
        rebuild(sc, entries)
        import sift_second  # here, since it reads this module first
        sift_second.settle(sc, entries, second, tool)
        return dict(settled(sc, entries, rec), undone={"rec_id": rec, "stage": stage, "n": target.get("n")})


def undo_excerpt(sc: Screening, entries: list[dict], target: dict, tool: str) -> dict:
    """Undo of a key excerpt kept or removed, the caller holding the lock: the record's excerpts put back as
    they stood before it, by one more line, `act` `undo` with `field` `excerpts`, the `undoes`, `change` and
    `excerpt` it takes back and the cell's `was` and `value`, and no stage, as the line it undoes has none.
    `undone` names the excerpt, so the screen marks its words again after an undo of one kept."""
    rec = str(target["rec_id"])
    if rec not in sc.at:
        raise SiftError(sift_words.t("sift_server.is_no_longer_in_so", rec=rec, csv_name=CSV_NAME))
    item = target.get("excerpt") if isinstance(target.get("excerpt"), dict) else {}
    now, back = sc.cell(rec, EXCERPTS_COLUMN), str(target.get("was") or "")
    entry = {"n": next_n(sc.folder), "at": now_iso(), "act": "undo", "rec_id": rec, "field": EXCERPTS_COLUMN,
             "change": target.get("change"), "excerpt": item, "was": now, "value": back, "undoes": target.get("n"),
             "tool": tool}
    append(sc.folder, entry)
    set_cells(sc, rec, {EXCERPTS_COLUMN: back})
    write_atomic(csv_path(sc.folder), csv_text(sc))
    stage = item.get("stage") if item.get("stage") in STAGES else "ta"
    return dict(answer(sc, entries, rec), undone={"rec_id": rec, "stage": stage, "n": target.get("n"), "what": EXCERPT_ACT,
                                                  "change": target.get("change"), "excerpt": item})


# --------------------------------------------------------- rounds and counts

def listed(sc: Screening, entries: list[dict], stage, which: str) -> list[str]:
    """The records of a round, in the CSV's order: those of the stage still to screen, at maybe, taken
    forward or left out, all of them, those whose decision differs from the proposal, or `apart`,
    those where he and the second screener went different ways once he can see theirs. A round goes
    by its own name or the stages' words for it (see `round_key`)."""
    stage = stage_key(stage)
    which = round_key(which)
    if which == APART:
        import sift_second  # here, since it reads this module first
        apart = set(sift_second.differences_of(sc.folder, sc, stage))
        return [rec for rec in sc.ids if rec in apart]
    held = states(entries)
    out = []
    for rec in sc.ids:
        if not in_stage(sc, held, rec, stage):
            continue
        mine = state_of(sc, held, rec, stage)["decision"]
        theirs = proposal_seen(sc, held, rec, stage)["decision"]
        keep = {"undecided": not mine, "maybe": mine == "maybe", "accepted": mine == "include",
                "rejected": mine == "exclude", "all": True,
                "differs": bool(mine and theirs and mine != theirs)}[which]
        if keep:
            out.append(rec)
    return out


def against() -> dict:
    """The decisions set against a proposal, overall or from one source."""
    return {"proposed": 0, "matched": 0, "overruled": 0, "reason_differs": 0,
            "table": {p: {d: 0 for d in DECISIONS} for p in DECISIONS}}


def searches(folder) -> dict:
    """The searches `log.csv` beside the CSV records, one row each, `date, source, interface, query,
    hits, records_saved, note`, with the hits and the records saved summed by source and in all, for
    the identification a flow diagram opens with. Empty with no file, and a figure that is not a
    whole number counts as none. `runs` is each search in the order the log holds them, its `date` and
    sums: a run's rows go one per database, so a database met again on the same day begins the next
    run's, two runs on one day two searches (13 October, evening)."""
    out = {"file": False, "rows": [], "sources": {}, "hits": 0, "saved": 0, "dates": {}, "runs": []}
    path = Path(folder) / SEARCHES_NAME
    if not path.is_file():
        return out
    out["file"] = True
    try:
        rows = list(csv.DictReader(io.StringIO(path.read_bytes().decode("utf-8-sig"), newline="")))
    except (UnicodeDecodeError, OSError, csv.Error):
        return out
    number = lambda v: int(v) if str(v or "").strip().isdigit() else 0
    for row in rows:
        row = {str(k or "").strip().lower(): str(v or "").strip() for k, v in row.items()}
        source = row.get("source", "")
        hits, saved = number(row.get("hits")), number(row.get("records_saved"))
        out["rows"].append(row)
        held = out["sources"].setdefault(source, {"hits": 0, "saved": 0})
        held["hits"] += hits
        held["saved"] += saved
        day = out["dates"].setdefault(row.get("date", ""), {"hits": 0, "saved": 0})
        day["hits"] += hits
        day["saved"] += saved
        last = out["runs"][-1] if out["runs"] else None
        if last is None or last["date"] != row.get("date", "") or source in last["sources"]:
            last = {"date": row.get("date", ""), "sources": [], "hits": 0, "saved": 0}
            out["runs"].append(last)
        last["sources"].append(source)
        last["hits"] += hits
        last["saved"] += saved
        out["hits"] += hits
        out["saved"] += saved
    return out


def counts(sc: Screening, entries: list[dict] | None = None) -> dict:
    """The one count of a screening, which the screen, the command line, the export and the PRISMA
    flow all take: for each stage the records in it, decided and undecided, each decision, each
    reason of the rejects, and against the proposal those that matched it and those he overruled,
    the rejects whose reason differs, the decisions with no proposal and the whole table of proposal
    against decision, in all and split by where the proposal came from. A decision is set against
    the proposal he saw when he made it, and an undecided record counts the proposal the CSV holds
    now. `searches` is what `log.csv` says of the searches, and `flow` the rest of what the PRISMA
    flow takes (see `flow_of`). `follows`, for a screening that follows an earlier run, names that
    run and counts the records carried from it, those found again and those new in this run, each
    record counted once, or is None."""
    held = states(read_log(sc.folder) if entries is None else entries)
    out = {"records": len(sc.ids), "stages": {}, "searches": searches(sc.folder), "follows": None}
    f = follow_of(sc.folder)
    if f:
        carried = {str(r) for r in f.get("records") or []} & set(sc.ids)
        again = {str(r) for r in f.get("again") or []} & carried
        out["follows"] = {"run": str(f.get("run") or ""), "carried": len(carried), "again": len(again),
                          "new": len(sc.ids) - len(carried)}
    out["stages"] = stage_counts(sc, held, sc.ids)
    # the studies and their reports over every record, for the export's rows beside the stages' own,
    # where the flow counts the active run's alone
    studies, reports = included_counts(sc, held, sc.ids)
    out["included"] = {"studies": studies, "reports": reports}
    out["flow"] = flow_of(sc, held, out)
    # the two screeners, from the log alone, or None with no second screener's draw
    import sift_second  # here, since it reads this module first
    out["second"] = sift_second.report(sc.folder, sc, read_log(sc.folder) if entries is None else entries)
    return out


def stage_counts(sc: Screening, held: dict, ids) -> dict:
    """Each stage's count over the records `ids` names, in the CSV's order: the records in it, decided
    and undecided, each decision, each reason of the rejects, and against the proposal, as `counts`
    sets them out. The screen's counts take every record, and the PRISMA flow's the active run's alone
    (see `own_search`)."""
    out = {}
    for stage in STAGES:
        c = {"stage": STAGE_WORDS[stage], "records": 0, "decided": 0, "undecided": 0,
             "include": 0, "maybe": 0, "exclude": 0, "reasons": {}, "unproposed": 0, **against(), "sources": {}}
        for rec in ids:
            if not in_stage(sc, held, rec, stage):
                continue
            c["records"] += 1
            mine = state_of(sc, held, rec, stage)
            theirs = proposal_seen(sc, held, rec, stage) if mine["decision"] else proposal_of(sc, rec, stage)
            mark = [c, c["sources"].setdefault(theirs["source"], against())] if theirs["decision"] else []
            for m in mark:
                m["proposed"] += 1
            if not mine["decision"]:
                c["undecided"] += 1
                continue
            c["decided"] += 1
            c[mine["decision"]] += 1
            if mine["decision"] == "exclude":
                code = mine["reason"] or "no reason"
                c["reasons"][code] = c["reasons"].get(code, 0) + 1
            if not theirs["decision"]:
                c["unproposed"] += 1
            for m in mark:
                m["table"][theirs["decision"]][mine["decision"]] += 1
                if mine["decision"] != theirs["decision"]:
                    m["overruled"] += 1
                    continue
                m["matched"] += 1
                if mine["decision"] == "exclude" and mine["reason"] != theirs["reason"]:
                    m["reason_differs"] += 1
        c["reasons"] = dict(sorted(c["reasons"].items(), key=lambda kv: natural(kv[0])))
        c["sources"] = dict(sorted(c["sources"].items()))
        out[stage] = c
    return out


# ------------------------------------------------------------- the PRISMA flow

# A run's own file, which the searches write beside its screening (see `sift_search.RUN_FILE`)
RUN_NAME = "run.json"
# the flow's one line where no run is active to count, in place of a sum of every search
NO_ACTIVE = "No active run to count"


def own_search(folder) -> dict:
    """The search the PRISMA flow counts (16 October): the active run's alone, since PRISMA 2020's
    diagram reports the review's own search and Sift marks it as the run made active. The screening of
    a run is that run, which Screening opens once it is made active, so its own rows of `log.csv` are
    those after the earlier runs' rows a run that follows another carries at its head, `carried`'s
    `searches` in `run.json`, or in a folder from before that count its own day's, and every row for a
    run that follows none. `earlier` is the records only an earlier run found, carried with their
    decisions and not found again, which stay in the screening and out of the flow, and none for a run
    that follows none. A screening of no run whose log holds
    more than one search, one another tool wrote, has no active run, `active` False, and the flow says
    so in place of a sum. `rows`, `hits`, `saved` and `sources` are the run's own, summed by database
    as `searches` sums the whole log. Only reads."""
    s = searches(folder)
    out = {"file": s["file"], "active": True, "rows": [], "sources": {}, "hits": 0, "saved": 0, "earlier": set()}
    if not s["file"]:
        return out
    try:
        meta = json.loads((Path(folder) / RUN_NAME).read_text(encoding="utf-8"))
    except (OSError, ValueError, UnicodeDecodeError):
        meta = None
    rows = s["rows"]
    if isinstance(meta, dict):
        follows = meta.get("follows") if isinstance(meta.get("follows"), dict) else None
        kept = meta.get("carried") if isinstance(meta.get("carried"), dict) else {}
        if follows and isinstance(kept.get("searches"), int):
            rows = rows[kept["searches"]:]
        elif follows:
            rows = [r for r in rows if r.get("date", "") == str(meta.get("date") or "")]
    elif len(s["runs"]) > 1:
        return dict(out, active=False)
    number = lambda v: int(v) if str(v or "").strip().isdigit() else 0
    for row in rows:
        source = row.get("source", "")
        hits, saved = number(row.get("hits")), number(row.get("records_saved"))
        held = out["sources"].setdefault(source, {"hits": 0, "saved": 0})
        held["hits"] += hits
        held["saved"] += saved
        out["hits"] += hits
        out["saved"] += saved
    out["rows"] = rows
    f = follow_of(folder)
    if f:
        out["earlier"] = {str(r) for r in f.get("records") or []} - {str(r) for r in f.get("again") or []}
    return out

def other_method(sources: str) -> bool:
    """Whether a record's sources say it was found by another method than a database search,
    citation chasing, a website or an organisation among them, and by no database at all."""
    names = [s.strip() for s in re.split(r"[;|]", str(sources or "")) if s.strip()]
    return bool(names) and all(OTHER_METHODS.search(name) for name in names)


def flow_of(sc: Screening, held: dict, c: dict) -> dict:
    """What the PRISMA 2020 flow takes, from the active run alone (16 October, see `own_search`):
    `search`, the run's own search, the records from databases and from other methods, those by each
    other method, the duplicates removed, the run's records saved less its records from databases,
    None with no figures or no active run, `stages`, each stage's counts over the run's records, the
    screen's own when the run holds every record, the reports with and without `pdfs/<rec_id>.pdf`, the
    studies included and the reports of them, PRISMA 2020 counting both (13 October), the reports he
    linked as one study counted once among the studies and a report linked to none a study of its own,
    and how far each stage has got, `done`, `now` or `future`. A record only an earlier run found, or
    another tool's search where no run is active, stays in the screening and out of every count here
    but the one line that says so."""
    s = own_search(sc.folder)
    others: dict[str, int] = {}
    other = 0
    ids = []
    for rec in sc.ids:
        sources = sc.cell(rec, "sources")
        if other_method(sources):
            other += 1
            for name in [x.strip() for x in re.split(r"[;|]", sources) if x.strip()]:
                others[name] = others.get(name, 0) + 1
        elif rec in s["earlier"]:
            continue
        ids.append(rec)
    databases = len(ids) - other
    duplicates = max(0, s["saved"] - databases) if s["file"] and s["active"] and s["saved"] else None
    stages = c["stages"] if len(ids) == len(sc.ids) else stage_counts(sc, held, ids)
    sought = [rec for rec in ids if in_stage(sc, held, rec, "ft")]
    missing = sum(1 for rec in sought if pdf_path(sc.folder, rec) is None)
    studies, reports = included_counts(sc, held, ids)
    ta, ft = stages["ta"], stages["ft"]
    screened = "future" if not ta["records"] else "done" if not ta["undecided"] else "now"
    if screened == "done" and not ft["records"]:
        later = {"retrieval": "done", "eligibility": "done", "included": "done"}
    else:
        retrieval = ("future" if not ft["records"] else "done" if screened == "done" and not missing else "now")
        eligibility = ("future" if not ft["decided"] else
                       "done" if screened == "done" and not ft["undecided"] else "now")
        included = "done" if eligibility == "done" else "now" if ft["include"] else "future"
        later = {"retrieval": retrieval, "eligibility": eligibility, "included": included}
    search = {"file": s["file"], "active": s["active"], "saved": s["saved"], "hits": s["hits"],
              "sources": s["sources"], "earlier": len(s["earlier"])}
    return {"databases": databases, "other": other, "others": dict(sorted(others.items())), "duplicates": duplicates,
            "sought": len(sought), "retrieved": len(sought) - missing, "not_retrieved": missing,
            "studies": studies, "reports": reports, "records": len(ids), "search": search, "stages": stages,
            "phases": dict({"identification": "done" if sc.ids else "now", "screening": screened}, **later)}


def included_counts(sc: Screening, held: dict, ids) -> tuple[int, int]:
    """The studies included and the reports of them among the records `ids` names, the reports he linked
    as one study counted once among the studies and a report linked to none a study of its own."""
    within = set(ids)
    reports = [rec for rec in included_ids(sc, held) if rec in within]
    linked = {one_line(sc.cell(rec, STUDY_COLUMN)) for rec in reports} - {""}
    return len(linked) + sum(1 for rec in reports if not one_line(sc.cell(rec, STUDY_COLUMN))), len(reports)


def mermaid_text(text) -> str:
    """Words as a Mermaid label in double quotes holds them: a hash, a double quote and the angle
    brackets as Mermaid's own entity codes, the spacing tidied."""
    s = " ".join(str(text or "").split())
    return s.replace("#", "#35;").replace('"', "#quot;").replace("<", "#lt;").replace(">", "#gt;")


def n_of(n) -> str:
    return f"(n = {n})"


def day_words(iso) -> str:
    """A day as the flow says it, 1 October 2026, or as it stands when it is not a date."""
    try:
        at = datetime.strptime(str(iso)[:10], "%Y-%m-%d")
    except ValueError:
        return str(iso or "")
    return f"{at.day} {at:%B %Y}"


def prisma_source(c: dict) -> str:
    """The PRISMA 2020 flow of a new review (Page et al. 2021) as a Mermaid flowchart, from the one
    count and nothing else, and every figure in it the active run's alone (16 October, see `flow_of`):
    identification, records from each database as the run's own rows of `log.csv` saved them, the
    duplicates removed and the records from other methods, then screening, its records excluded by
    reason and those still to screen or at maybe, retrieval, eligibility with the reports excluded by
    reason, and the studies included. The earlier runs a run follows stay out of it, and with no
    active run the first box says so in one line and sums no search. Each box carries its stage's
    class, `done`, `now` or `future`, a stage not yet reached drawn dashed."""
    f = c["flow"]
    stages = f.get("stages") or c["stages"]
    ta, ft = stages["ta"], stages["ft"]
    phase = f["phases"]
    s = f.get("search") or {"active": True, "saved": c["searches"]["saved"], "sources": c["searches"]["sources"]}
    lines = ["flowchart TD"]
    nodes: list[tuple[str, list[str], str]] = []
    # each line of a box in the run's language, as Mermaid's label holds it
    w = mermaid_text
    # each box in PRISMA's own words, its count on a line under them, kept short for a narrow sidebar
    if not s["active"]:
        db = [w(sift_words.t("sift_server.flow.identified")), w(sift_words.t("sift_server.flow.from_databases")), w(sift_words.t("sift_server.flow.no_active"))]
    else:
        db = [w(sift_words.t("sift_server.flow.identified")), w(sift_words.t("sift_server.flow.from_databases")),
              n_of(s["saved"] if f["duplicates"] is not None else f["databases"])]
    if f["duplicates"] is not None:
        db += [f"{mermaid_text(name)} {n_of(v['saved'])}" for name, v in s["sources"].items() if name]
    nodes.append(("db", db, "identification"))
    if f["duplicates"] is not None:
        nodes.append(("dup", [w(sift_words.t("sift_server.flow.duplicates")), w(sift_words.t("sift_server.flow.removed", count=n_of(f['duplicates'])))], "identification"))
    if f["other"]:
        nodes.append(("other", [w(sift_words.t("sift_server.flow.identified")), w(sift_words.t("sift_server.flow.from_other")), n_of(f["other"])]
                      + [f"{mermaid_text(name)} {n_of(n)}" for name, n in f["others"].items()], "identification"))
    # every record after the duplicates are removed is a record screened, as PRISMA counts it, those
    # still to screen said inside the box while the screening goes on, To screen since 12 October, later,
    # as the screen says it, PRISMA's own words in the box kept as they are
    nodes.append(("screened", [w(sift_words.t("sift_server.flow.screened")), n_of(ta["records"]), w(sift_words.t("sift_server.flow.to_screen")), n_of(ta["undecided"]),
                               w(sift_words.t("sift_server.flow.maybe", count=n_of(ta['maybe'])))], "screening"))
    nodes.append(("excluded", [w(sift_words.t("sift_server.flow.excluded")), n_of(ta["exclude"])]
                  + [f"{mermaid_text(code)} {n_of(n)}" for code, n in ta["reasons"].items()], "screening"))
    nodes.append(("sought", [w(sift_words.t("sift_server.flow.sought")), w(sift_words.t("sift_server.flow.for_retrieval")), n_of(f["sought"])], "retrieval"))
    nodes.append(("missing", [w(sift_words.t("sift_server.flow.not_yet")), w(sift_words.t("sift_server.flow.retrieved", count=n_of(f['not_retrieved'])))], "retrieval"))
    nodes.append(("assessed", [w(sift_words.t("sift_server.flow.assessed")), w(sift_words.t("sift_server.flow.for_eligibility")), n_of(ft["decided"]),
                               w(sift_words.t("sift_server.flow.to_screen")), n_of(ft["undecided"]), w(sift_words.t("sift_server.flow.maybe", count=n_of(ft['maybe'])))],
                  "eligibility"))
    nodes.append(("ftexcluded", [w(sift_words.t("sift_server.flow.ft_excluded")), n_of(ft["exclude"])]
                  + [f"{mermaid_text(code)} {n_of(n)}" for code, n in ft["reasons"].items()], "eligibility"))
    # the studies included and the reports of them, as PRISMA 2020's last box counts them (13 October)
    nodes.append(("included", [w(sift_words.t("sift_server.flow.studies")), w(sift_words.t("sift_server.flow.in_review", count=n_of(f.get('studies', ft['include'])))),
                               w(sift_words.t("sift_server.flow.reports_of")), w(sift_words.t("sift_server.flow.of_studies", count=n_of(f.get('reports', ft['include']))))],
                  "included"))
    # the two screeners of each stage, a box beside the stage's, once a second screener has a draw there
    import sift_second  # here, since it reads this module first
    two = c.get("second") or {}
    for stage, key in (("ta", "twota"), ("ft", "twoft")):
        if two.get(stage):
            nodes.append((key, sift_second.flow_lines(two[stage]), "screening" if stage == "ta" else "eligibility"))
    for key, words, _ in nodes:
        lines.append(f'  {key}["{"<br/>".join(words)}"]')
    have = {key for key, _, _ in nodes}
    edges = [("db", "dup"), ("db", "screened"), ("other", "screened"), ("screened", "excluded"), ("screened", "sought"),
             ("sought", "missing"), ("sought", "assessed"), ("assessed", "ftexcluded"), ("assessed", "included")]
    lines += [f"  {a} --> {b}" for a, b in edges if a in have and b in have]
    lines += [f"  {a} -.- {b}" for a, b in (("screened", "twota"), ("assessed", "twoft")) if b in have]
    # the boxes at the side joined by links never drawn, so they stand in a column of their own beside
    # the main one, as PRISMA's template sets them
    side = [key for key in ("dup", "excluded", "missing", "ftexcluded") if key in have]
    lines += [f"  {a} ~~~ {b}" for a, b in zip(side, side[1:])]
    lines += ["  classDef done stroke-width:1px", "  classDef now stroke-width:2px",
              "  classDef future stroke-dasharray:4 3"]
    for state in ("done", "now", "future"):
        keys = [key for key, _, stage in nodes if phase[stage] == state]
        if keys:
            lines.append(f"  class {','.join(keys)} {state}")
    return "\n".join(lines) + "\n"


def prisma_markdown(source: str) -> str:
    """`prisma.md` as written: a heading and one fenced Mermaid block."""
    return f"# PRISMA flow\n\n```mermaid\n{source}```\n"


def write_prisma(folder, source: str) -> bool:
    """`prisma.md` beside the CSV written afresh, through a temporary file and `os.replace`, when its
    flow differs from the one there. The answer is whether it wrote."""
    path = Path(folder) / PRISMA_NAME
    text = prisma_markdown(source)
    try:
        if path.read_text(encoding="utf-8") == text:
            return False
    except (OSError, UnicodeDecodeError):
        pass
    write_atomic(path, text)
    return True


def refresh_prisma(folder, wait: float | None = 1.0) -> str:
    """The flow as the screening stands, `prisma.md` written afresh under the lock when it differs,
    and left as it is while another writer holds the lock or the folder takes no write. Opening a
    screening calls it."""
    try:
        with locks.held(lock_path(folder), wait):
            source = prisma_source(counts(load(folder)))
            write_prisma(folder, source)
            return source
    except WorkbookError as exc:
        if exc.code != "busy":
            raise
    except OSError:
        pass
    return prisma_source(counts(load(folder)))


def against_rows(name: str, a: dict, src: str = "") -> list[list]:
    said = f" from {src}" if src else ""
    rows = [[name, f"with a proposal{said}", a["proposed"]], [name, f"matched the proposal{said}", a["matched"]],
            [name, f"overruled the proposal{said}", a["overruled"]],
            [name, f"exclude with another reason than proposed{said}", a["reason_differs"]]]
    return rows + [[name, f"proposal {p}{said}, decision {d}", a["table"][p][d]] for p in DECISIONS for d in DECISIONS]


def count_rows(c: dict) -> list[list]:
    """The counts as the export's rows, `stage,measure,count`, in the files' words: each stage's
    records and decisions, the rejects by reason, then the decisions against the proposal in all and
    again for each source a proposal came from."""
    rows = []
    follows = c.get("follows")
    if follows:
        # a run that follows an earlier one, its identification by search, each record counted once, two
        # searches of one day each with its number that day
        runs = [r for r in c["searches"]["runs"] if r["date"]]
        for r in runs:
            same = [x for x in runs if x["date"] == r["date"]]
            n = f", search {next(i for i, x in enumerate(same) if x is r) + 1}" if len(same) > 1 else ""
            rows.append(["identification", f"records saved {r['date']}{n}", r["saved"]])
        rows += [["identification", f"carried from the run of {follows['run']}", follows["carried"]],
                 ["identification", "found again", follows["again"]], ["identification", "new in this run", follows["new"]]]
    for stage in STAGES:
        s = c["stages"][stage]
        name = s["stage"]
        rows += [[name, "records", s["records"]], [name, "decided", s["decided"]], [name, "undecided", s["undecided"]],
                 [name, "include", s["include"]], [name, "maybe", s["maybe"]], [name, "exclude", s["exclude"]]]
        rows += [[name, f"exclude {code}", n] for code, n in s["reasons"].items()]
        whole = c.get("included") or c.get("flow", {})
        if stage == "ft" and "studies" in whole:
            rows += [[name, "studies included", whole["studies"]], [name, "reports of included studies", whole["reports"]]]
        rows += [[name, "decided with no proposal", s["unproposed"]]] + against_rows(name, s)
        for src, a in s["sources"].items():
            rows += against_rows(name, a, src)
    import sift_second  # here, since it reads this module first
    rows += sift_second.count_rows(c.get("second"))
    return rows


def counts_csv(c: dict) -> str:
    out = io.StringIO(newline="")
    writer = csv.writer(out, lineterminator="\n")
    writer.writerow(["stage", "measure", "count"])
    writer.writerows(count_rows(c))
    return out.getvalue()


def export(folder, dry_run: bool = False, wait: float | None = None) -> dict:
    """The counts written as `screening.counts.csv` beside the CSV, whole each time from the log,
    or with `dry_run` only said."""
    with locks.held(lock_path(folder), wait):
        sc = load(folder)
        c = counts(sc)
        path = Path(folder) / COUNTS_NAME
        if not dry_run:
            write_atomic(path, counts_csv(c))
        return {"counts": c, "rows": count_rows(c), "file": COUNTS_NAME, "path": str(path), "written": not dry_run}


# ------------------------------------------------------------- the included records

# Export included records (12 October): the records included at full text written beside the CSV, as
# Write the counts writes its file there, once as RIS for a reference manager and once as CSV for a
# spreadsheet, whole each time, the CSV's own cells and nothing of his decisions or fields but his key
# excerpts, as text in a last column of the CSV since 14 October (see `excerpts_text`)
INCLUDED_RIS = "screening.included.ris"
INCLUDED_CSV = "screening.included.csv"
INCLUDED_COLUMNS = ("rec_id", "title", "authors", "year", "journal", "doi", "pub_type", "url", "abstract", "sources")
# a record's type for RIS, from the type Sync to Zotero gives it
RIS_TYPE = {"journalArticle": "JOUR", "thesis": "THES", "preprint": "UNPB", "bookSection": "CHAP", "book": "BOOK",
            "conferencePaper": "CPAPER", "report": "RPRT", "webpage": "ELEC", "document": "GEN"}


def included_ids(sc: Screening, held: dict) -> list[str]:
    """The records included at full text, in the CSV's order."""
    return [rec for rec in sc.ids if in_stage(sc, held, rec, "ft") and state_of(sc, held, rec, "ft")["decision"] == "include"]


def ris_text(sc: Screening, ids: list[str]) -> str:
    """The records as RIS: each its type, title, every author as `Last, First`, year, journal, DOI, web
    address, abstract and its rec_id in a note, then ER."""
    import sift_zotero  # here, since it reads this module first
    out = []
    for rec in ids:
        cell = lambda name: one_line(sc.cell(rec, name))
        kind = sift_zotero.item_type(cell("pub_type"), cell("journal"))
        lines = [("TY", RIS_TYPE.get(kind, "GEN")), ("TI", cell("title"))]
        for who in sift_zotero.creators_of(sc.cell(rec, "authors")):
            lines.append(("AU", f"{who['lastName']}, {who['firstName']}".rstrip(", ") if "lastName" in who else who.get("name", "")))
        lines += [("PY", cell("year")), ("T2" if kind == "bookSection" else "JO", cell("journal")), ("DO", cell("doi")),
                  ("UR", cell(URL_COLUMN) or doi_link(cell("doi"))), ("AB", cell("abstract")), ("N1", f"Sift: {rec}")]
        out += [f"{tag}  - {value}" for tag, value in lines if value] + ["ER  - ", ""]
    return "\n".join(out)


def included_csv(sc: Screening, ids: list[str]) -> str:
    """The records as CSV, the CSV's own cells of `INCLUDED_COLUMNS` and his key excerpts as text after them."""
    out = io.StringIO(newline="")
    writer = csv.writer(out, lineterminator="\n")
    writer.writerow(INCLUDED_COLUMNS + (EXCERPTS_COLUMN,))
    writer.writerows([[sc.cell(rec, name) for name in INCLUDED_COLUMNS] + [excerpts_text(sc.cell(rec, EXCERPTS_COLUMN))]
                      for rec in ids])
    return out.getvalue()


def export_included(folder, dry_run: bool = False, wait: float | None = None) -> dict:
    """The records included at full text written as `screening.included.ris` and `screening.included.csv`
    beside the CSV, whole each time from the log, or with `dry_run` only counted. With none included
    yet nothing is written."""
    with locks.held(lock_path(folder), wait):
        sc = load(folder)
        ids = included_ids(sc, states(read_log(folder)))
        write = bool(ids) and not dry_run
        if write:
            write_atomic(Path(folder) / INCLUDED_RIS, ris_text(sc, ids))
            write_atomic(Path(folder) / INCLUDED_CSV, included_csv(sc, ids))
        return {"records": len(ids), "files": [INCLUDED_RIS, INCLUDED_CSV], "written": write}


# ------------------------------------------------------------- starting again

# A screening started again, to trial it and begin afresh: the log moved whole into `_Archive/`
# beside the CSV, never deleted or written again, and every column Sift writes emptied, his
# decisions at both stages, his own fields and columns and Sift's own proposals. The review's
# proposals, reasons.csv, pdfs/, sift.json and every other file stay as they are.
ARCHIVE_DIR = "_Archive"
RESET_COLUMNS = DECISION_COLUMNS + OWN_COLUMNS + AI_PROPOSAL_COLUMNS


def reset_said(sc: Screening, entries: list[dict]) -> dict:
    """What starting again clears: the decisions and the notes at both stages, each record's own."""
    held = states(entries)
    stood = [state_of(sc, held, rec, stage) for rec in sc.ids for stage in STAGES]
    return {"decisions": sum(1 for s in stood if s["decision"]), "notes": sum(1 for s in stood if s["note"])}


def archive_name(folder, when: datetime | None = None) -> Path:
    """Where the log goes in `_Archive/`, `screening.log (<date-time>).jsonl`, a second the same
    second numbered after it, so no copy is ever written over."""
    stamp = (when or datetime.now()).strftime("%Y-%m-%d %H.%M.%S")
    base = Path(folder) / ARCHIVE_DIR
    path, n = base / f"screening.log ({stamp}).jsonl", 2
    while path.exists():
        path, n = base / f"screening.log ({stamp} {n}).jsonl", n + 1
    return path


def reset(folder, dry_run: bool = False, wait: float | None = None) -> dict:
    """The screening started again under its lock: the log moved whole into `_Archive/`, every
    decision column at both stages emptied with his own fields, his columns and Sift's own
    proposals, then the counts file, when there is one, and `prisma.md` written afresh. With
    `dry_run` it only says what it would clear. The answer says the decisions and notes cleared and
    the copy kept."""
    with locks.held(lock_path(folder), wait):
        sc = load(folder)
        said = reset_said(sc, read_log(folder))
        if dry_run:
            return dict(said, archive=ARCHIVE_DIR, dry_run=True)
        kept = ""
        if log_path(folder).exists():
            target = archive_name(folder)
            target.parent.mkdir(exist_ok=True)
            os.replace(log_path(folder), target)
            kept = f"{ARCHIVE_DIR}/{target.name}"
        cleared = [i for i, name in enumerate(sc.header) if name in RESET_COLUMNS or is_own(name)]
        before = csv_text(sc)
        for row in sc.rows:
            for i in cleared:
                if i < len(row):
                    row[i] = ""
        if csv_text(sc) != before:
            write_atomic(csv_path(folder), csv_text(sc))
        c = counts(load(folder))
        write_prisma(folder, prisma_source(c))
        if (Path(folder) / COUNTS_NAME).exists():
            write_atomic(Path(folder) / COUNTS_NAME, counts_csv(c))
        # the second screener's file, when there is one, written afresh from the log, which now holds none
        import sift_second  # here, since it reads this module first
        if (Path(folder) / sift_second.MIRROR_NAME).exists():
            sift_second.write_mirror(folder, sift_second.two_of(folder, load(folder), []))
        return dict(said, archive=kept, dry_run=False, counts=c)


# ------------------------------------- OpenAlex's and Crossref's columns, key works and studies

# each country of ISO 3166-1 by its two letters, in plain English, as the Country column names it, and a
# code it does not hold as it stands
COUNTRY_NAMES = dict(pair.split(":", 1) for pair in (
    "AD:Andorra|AE:United Arab Emirates|AF:Afghanistan|AG:Antigua and Barbuda|AI:Anguilla|AL:Albania|AM:Armenia|"
    "AO:Angola|AQ:Antarctica|AR:Argentina|AS:American Samoa|AT:Austria|AU:Australia|AW:Aruba|AX:Åland Islands|"
    "AZ:Azerbaijan|BA:Bosnia and Herzegovina|BB:Barbados|BD:Bangladesh|BE:Belgium|BF:Burkina Faso|BG:Bulgaria|"
    "BH:Bahrain|BI:Burundi|BJ:Benin|BL:Saint Barthélemy|BM:Bermuda|BN:Brunei|BO:Bolivia|BQ:Caribbean Netherlands|"
    "BR:Brazil|BS:Bahamas|BT:Bhutan|BV:Bouvet Island|BW:Botswana|BY:Belarus|BZ:Belize|CA:Canada|CC:Cocos Islands|"
    "CD:Democratic Republic of the Congo|CF:Central African Republic|CG:Republic of the Congo|CH:Switzerland|"
    "CI:Côte d'Ivoire|CK:Cook Islands|CL:Chile|CM:Cameroon|CN:China|CO:Colombia|CR:Costa Rica|CU:Cuba|CV:Cape Verde|"
    "CW:Curaçao|CX:Christmas Island|CY:Cyprus|CZ:Czechia|DE:Germany|DJ:Djibouti|DK:Denmark|DM:Dominica|"
    "DO:Dominican Republic|DZ:Algeria|EC:Ecuador|EE:Estonia|EG:Egypt|EH:Western Sahara|ER:Eritrea|ES:Spain|"
    "ET:Ethiopia|FI:Finland|FJ:Fiji|FK:Falkland Islands|FM:Micronesia|FO:Faroe Islands|FR:France|GA:Gabon|"
    "GB:United Kingdom|GD:Grenada|GE:Georgia|GF:French Guiana|GG:Guernsey|GH:Ghana|GI:Gibraltar|GL:Greenland|"
    "GM:Gambia|GN:Guinea|GP:Guadeloupe|GQ:Equatorial Guinea|GR:Greece|GS:South Georgia and the South Sandwich Islands|"
    "GT:Guatemala|GU:Guam|GW:Guinea-Bissau|GY:Guyana|HK:Hong Kong|HM:Heard Island and McDonald Islands|HN:Honduras|"
    "HR:Croatia|HT:Haiti|HU:Hungary|ID:Indonesia|IE:Ireland|IL:Israel|IM:Isle of Man|IN:India|"
    "IO:British Indian Ocean Territory|IQ:Iraq|IR:Iran|IS:Iceland|IT:Italy|JE:Jersey|JM:Jamaica|JO:Jordan|JP:Japan|"
    "KE:Kenya|KG:Kyrgyzstan|KH:Cambodia|KI:Kiribati|KM:Comoros|KN:Saint Kitts and Nevis|KP:North Korea|"
    "KR:South Korea|KW:Kuwait|KY:Cayman Islands|KZ:Kazakhstan|LA:Laos|LB:Lebanon|LC:Saint Lucia|LI:Liechtenstein|"
    "LK:Sri Lanka|LR:Liberia|LS:Lesotho|LT:Lithuania|LU:Luxembourg|LV:Latvia|LY:Libya|MA:Morocco|MC:Monaco|"
    "MD:Moldova|ME:Montenegro|MF:Saint Martin|MG:Madagascar|MH:Marshall Islands|MK:North Macedonia|ML:Mali|"
    "MM:Myanmar|MN:Mongolia|MO:Macao|MP:Northern Mariana Islands|MQ:Martinique|MR:Mauritania|MS:Montserrat|MT:Malta|"
    "MU:Mauritius|MV:Maldives|MW:Malawi|MX:Mexico|MY:Malaysia|MZ:Mozambique|NA:Namibia|NC:New Caledonia|NE:Niger|"
    "NF:Norfolk Island|NG:Nigeria|NI:Nicaragua|NL:Netherlands|NO:Norway|NP:Nepal|NR:Nauru|NU:Niue|NZ:New Zealand|"
    "OM:Oman|PA:Panama|PE:Peru|PF:French Polynesia|PG:Papua New Guinea|PH:Philippines|PK:Pakistan|PL:Poland|"
    "PM:Saint Pierre and Miquelon|PN:Pitcairn Islands|PR:Puerto Rico|PS:Palestine|PT:Portugal|PW:Palau|PY:Paraguay|"
    "QA:Qatar|RE:Réunion|RO:Romania|RS:Serbia|RU:Russia|RW:Rwanda|SA:Saudi Arabia|SB:Solomon Islands|SC:Seychelles|"
    "SD:Sudan|SE:Sweden|SG:Singapore|SH:Saint Helena|SI:Slovenia|SJ:Svalbard and Jan Mayen|SK:Slovakia|"
    "SL:Sierra Leone|SM:San Marino|SN:Senegal|SO:Somalia|SR:Suriname|SS:South Sudan|ST:São Tomé and Príncipe|"
    "SV:El Salvador|SX:Sint Maarten|SY:Syria|SZ:Eswatini|TC:Turks and Caicos Islands|TD:Chad|"
    "TF:French Southern Territories|TG:Togo|TH:Thailand|TJ:Tajikistan|TK:Tokelau|TL:Timor-Leste|TM:Turkmenistan|"
    "TN:Tunisia|TO:Tonga|TR:Turkey|TT:Trinidad and Tobago|TV:Tuvalu|TW:Taiwan|TZ:Tanzania|UA:Ukraine|UG:Uganda|"
    "UM:United States Minor Outlying Islands|US:United States|UY:Uruguay|UZ:Uzbekistan|VA:Vatican City|"
    "VC:Saint Vincent and the Grenadines|VE:Venezuela|VG:British Virgin Islands|VI:US Virgin Islands|VN:Vietnam|"
    "VU:Vanuatu|WF:Wallis and Futuna|WS:Samoa|XK:Kosovo|YE:Yemen|YT:Mayotte|ZA:South Africa|ZM:Zambia|ZW:Zimbabwe"
).split("|"))
# OpenAlex's kinds of open access in plain words, as the record says where a paper is open
OA_WORDS = {"diamond": "in an open-access journal that charges no fee", "gold": "in an open-access journal",
            "hybrid": "in a subscription journal", "bronze": "free to read on the publisher's site",
            "green": "in a repository"}
# a key work's year matches a reference's within one either way, since a book is often cited by its online
# year, one before its print year, or by a reprint's, which still tells apart editions years apart
YEAR_SLACK = 1
# a key work's main title found with its subtitle's first word after it, however the rest of the subtitle
# is cited, with this many letters wrong when the main title is at least MAIN_MIN letters long
MAIN_SLACK = 2
MAIN_MIN = 16
# a record's own authors and OpenAlex's, `Ida Gannet (A5012345)`, and a run of initials at a name's end
OA_AUTHOR = re.compile(r"^(.*?)\s*\((A\d+)\)$")
INITIALS_TAIL = re.compile(r"(?:[A-Z]\.?-?){1,4}")
# the words a title shares with another that say nothing of which study it is
COMMON_WORDS = set("""about after among amongst approach based before being between beyond case cases during each
    experience experiences experiencing explore explored exploring exploration exploratory from have into lived living
    life lives qualitative quantitative analysis interpretative interpretive phenomenological phenomenology
    perspective perspectives people participants research review study studies their them they this those through
    toward towards understanding using what when where which while with within without women young adults""".split())
# a title's word is distinctive when at most this share of the screening's titles carries it, and two titles
# carry it at least
RARE_SHARE = 0.05
# the suggestions a record shows at most, the strongest first
SUGGEST_MAX = 5


def fold(text) -> str:
    """Words as two are compared by: the markup out, accents taken off, case folded, the spacing tidied."""
    s = unicodedata.normalize("NFKD", plain(text))
    return " ".join("".join(ch for ch in s if not unicodedata.combining(ch)).casefold().split())


def fold_title(text) -> str:
    """A title as a key work's is found in a reference by: its letters and digits alone, folded."""
    return "".join(ch for ch in fold(text) if ch.isalnum())


def country_codes(value) -> list[str]:
    """The countries a record's cell names, each two letters once, in its order."""
    parts = (p.strip().upper() for p in re.split(r"[;|,]", str(value or "")))
    return [c for c in dict.fromkeys(parts) if re.fullmatch(r"[A-Z]{2}", c)]


def country_name(code: str) -> str:
    return COUNTRY_NAMES.get(code, code)


def language_name(value) -> str:
    """One language as Sift writes it (14 October): its English name for an ISO 639-1 or 639-2 code or for
    its name in any case, `eng` and `en` English, a code it does not know kept as given, and none for
    undetermined."""
    text = " ".join(str(value or "").split()).strip(" .")
    key = text.casefold()
    if not key or key in NO_LANGUAGE:
        return ""
    return LANGUAGE_NAMES.get(key, text)


def language_list(values) -> list[str]:
    """The languages of a record, each by `language_name`, once, in their order, from a cell or a source's
    values, parted by semicolons, commas or bars."""
    items = [values] if isinstance(values, str) or values is None else list(values)
    names = (language_name(p) for v in items for p in re.split(r"[;|,]", str(v or "")))
    return [n for n in dict.fromkeys(names) if n]


def language_cell(values) -> str:
    """A record's languages as its cell holds them, parted by semicolons as several choices are."""
    return "; ".join(language_list(values))


def notice_kinds(value) -> list[str] | None:
    """What the retraction column says, retracted, expression of concern and corrected in that order, an
    empty list once it was asked and none was found, and None when it was never asked."""
    text = " ".join(str(value or "").split()).lower()
    if not text:
        return None
    held = {p.strip() for p in re.split(r"[;|,]", text)}
    return [k for k in NOTICE_KINDS if k in held]


def notices_of(value) -> list[dict]:
    """The notices the record's `retraction_notices` keeps, each its kind, its DOI, its date and where it
    was found, from a JSON list, and none from anything else."""
    try:
        data = json.loads(value) if str(value or "").strip() else []
    except ValueError:
        return []
    out = []
    for n in data if isinstance(data, list) else []:
        if isinstance(n, dict) and n.get("kind") in NOTICE_KINDS:
            out.append({k: one_line(n.get(k)) for k in ("kind", "doi", "date", "from")})
    return out


def openalex_authors_of(value) -> list[tuple[str, str]]:
    """The authors OpenAlex gives a record as its cell keeps them, each name with its ID, `Ida Gannet
    (A5012345)`, a name with none kept with an empty ID."""
    out = []
    for part in str(value or "").split(";"):
        part = " ".join(part.split())
        if part:
            m = OA_AUTHOR.match(part)
            out.append((m.group(1).strip(), m.group(2)) if m else (part, ""))
    return out


def name_key(name) -> str:
    """An author as two lists are compared by: the surname's last word and the first initial, accents and
    case folded, from `Gannet, Ida`, `Gannet IA`, `I. A. Gannet` or `Ida Gannet` alike, empty for none."""
    text = " ".join(str(name or "").split()).strip(" ,;")
    if not text:
        return ""
    if "," in text:
        surname, given = text.split(",", 1)
    else:
        parts = text.split()
        tail = []
        while len(parts) > 1 and INITIALS_TAIL.fullmatch(parts[-1]):
            tail.insert(0, parts.pop())
        if tail:
            surname, given = " ".join(parts), " ".join(tail)
        else:
            surname, given = parts[-1], " ".join(parts[:-1])
    words = [w for w in (fold_title(w) for w in surname.split()) if w]
    if not words:
        return ""
    initial = next((ch for ch in fold(given) if ch.isalpha()), "")
    return f"{words[-1]} {initial}".strip()


def author_list(sc: Screening, rec: str) -> list[tuple[str, str, str]]:
    """A record's authors as the suggestions compare them, each its OpenAlex ID or empty, its key and its
    name as the record gives it, once each: OpenAlex's list when the record has one, else its own."""
    import sift_search  # here, since it reads this module first
    given = openalex_authors_of(sc.cell(rec, AUTHORS_COLUMN))
    if not given:
        given = [(n, "") for n in sift_search.author_names(sc.cell(rec, "authors"))]
    out, seen = [], set()
    for name, aid in given:
        key = name_key(name)
        mark = aid or key
        if key and mark not in seen:
            seen.add(mark)
            out.append((aid, key, name))
    return out


def shared_authors(a: list, b: list) -> list[int]:
    """The authors two records share, as places in the first list: each matched by OpenAlex ID where both
    have one, else by its key, each author of the second matched once, the order of either set aside."""
    used, out = set(), []
    for i, (aid, akey, _) in enumerate(a):
        for j, (bid, bkey, _) in enumerate(b):
            if j not in used and ((aid == bid) if (aid and bid) else (akey == bkey)):
                used.add(j)
                out.append(i)
                break
    return out


def given_first(name: str) -> str:
    """An author as a line names them, `Gannet, Ida` as Ida Gannet, any other as it stands."""
    surname, comma, given = str(name or "").partition(",")
    return f"{given.strip()} {surname.strip()}".strip() if comma and given.strip() else one_line(name)


def and_join(items: list[str]) -> str:
    """Words as a line lists them, A, B and C, as the run's language joins a list."""
    return formats.list_words([one_line(i) for i in items if one_line(i)])


def or_join(items: list[str]) -> str:
    """Words as a line offers them, A, B or C (14 October, later)."""
    items = [one_line(i) for i in items if one_line(i)]
    return formats.list_words(items, "or")


def title_words(text) -> set[str]:
    """A title's words of four letters or more, folded, the common ones of research titles left out."""
    return {w for w in re.findall(r"[^\W\d_]{4,}", fold(text)) if w not in COMMON_WORDS}


def study_number(label) -> int | None:
    m = STUDY_LABEL.fullmatch(" ".join(str(label or "").split()))
    return int(m.group(1)) if m else None


def study_order(label) -> tuple:
    n = study_number(label)
    return (0, n, "") if n is not None else (1, 0, str(label))


def studies_of(sc: Screening) -> dict[str, list[str]]:
    """Each study he has linked and its reports, in the CSV's order."""
    out: dict[str, list[str]] = {}
    for rec in sc.ids:
        label = one_line(sc.cell(rec, STUDY_COLUMN))
        if label:
            out.setdefault(label, []).append(rec)
    return out


_REFERENCES: dict = {}
# the last screening's authors and title words, as `extras_of` works them out, by its folder
_EXTRAS: dict = {}


def references(folder) -> dict:
    """The references `screening.references.json` keeps by rec_id, each record's `crossref`, a list of
    each reference's DOI, year and folded titles, and `openalex`, the IDs of the works OpenAlex says it
    cites, either missing until its service was asked. Read once for each change to the file."""
    path = Path(folder) / REFERENCES_NAME
    try:
        st = path.stat()
    except OSError:
        return {}
    mark = (str(path.resolve()), st.st_mtime_ns, st.st_size)
    held = _REFERENCES.get(mark[0])
    if held and held[0] == mark:
        return held[1]
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError, UnicodeDecodeError):
        data = {}
    records = data.get("records") if isinstance(data, dict) and isinstance(data.get("records"), dict) else {}
    out = {str(k): v for k, v in records.items() if isinstance(v, dict)}
    _REFERENCES.clear()
    _REFERENCES[mark[0]] = (mark, out)
    return out


def write_references(folder, records: dict) -> None:
    """`screening.references.json` written whole through a temporary file, or taken away with none. The
    caller holds the lock."""
    path = Path(folder) / REFERENCES_NAME
    if records:
        write_atomic(path, json.dumps({"records": records}, ensure_ascii=False, separators=(",", ":")) + "\n")
    else:
        path.unlink(missing_ok=True)


def review_of(folder) -> Path | None:
    """The review a screening's plan is kept in: the folder over `runs/` for a run's screening, else the
    screening's own folder when it holds a plan, else None."""
    here = Path(folder)
    if here.parent.name == RUNS_NAME:
        return here.parent.parent
    return here if (here / "search_plan.json").is_file() else None


def key_works_of(folder) -> list[dict]:
    """The review's key works as its plan keeps them (see `sift_search.key_works`), or none."""
    review = review_of(folder)
    if review is None:
        return []
    import sift_search  # here, since it reads this module first
    try:
        return sift_search.key_works(review)
    except WorkbookError:
        return []


def key_work_key(kw: dict) -> str:
    """A key work as a record's list and the filters name it: its OpenAlex ID, else its DOI, else its
    folded title and year."""
    if kw.get("id"):
        return str(kw["id"])
    if kw.get("doi"):
        return "doi:" + str(kw["doi"])
    return "title:" + fold_title(kw.get("title")) + "|" + str(kw.get("year") or "")


def key_work_label(kw: dict) -> str:
    """A key work as a pill names it: its title before any subtitle and its year, or its DOI."""
    title = one_line(kw.get("title")).split(": ", 1)[0]
    if not title:
        return one_line(kw.get("doi")) or str(kw.get("id") or "")
    return f"{title} ({kw['year']})" if kw.get("year") else title


def near_in(want: str, text: str, slack: int) -> bool:
    """Whether `text` holds `want` with at most `slack` letters wrong, left out or added (Sellers' edit
    distance to the best stretch of `text`)."""
    if not want:
        return False
    if want in text:
        return True
    if slack <= 0 or len(text) < len(want) - slack:
        return False
    prev = [0] * (len(text) + 1)
    for i, wc in enumerate(want, 1):
        cur = [i] + [0] * len(text)
        for j, tc in enumerate(text, 1):
            cur[j] = min(prev[j - 1] + (wc != tc), prev[j] + 1, cur[j - 1] + 1)
        prev = cur
    return min(prev) <= slack


def title_forms(title) -> tuple[str, str]:
    """A key work's title as references are matched to it: the whole title folded, and its main title
    followed by its subtitle's first word, folded, or empty when it has no subtitle."""
    whole = fold_title(title)
    main, _, sub = one_line(title).partition(":")
    first = re.findall(r"[^\W_]+", fold(sub))
    return whole, (fold_title(main) + first[0] if first and fold_title(main) else "")


def ref_cites(kw: dict, ref) -> bool:
    """Whether one of Crossref's references is a key work: its DOI is the key work's, or one of its titles
    holds the key work's title, folded, or holds its main title with its subtitle's first word straight
    after it, the main title allowed MAIN_SLACK letters wrong when it is long enough, since a book is
    often cited with its subtitle garbled or a word of its title misspelt ("Interpretive" for
    "Interpretative"), and its year is the key work's within YEAR_SLACK, any year doing for a key work
    kept with none. The subtitle's first word keeps out another work that shares the main title alone."""
    if not isinstance(ref, list) or len(ref) < 2:
        return False
    doi, year, texts = str(ref[0] or ""), str(ref[1] or ""), [str(t) for t in ref[2:]]
    if kw.get("doi") and doi and doi == kw["doi"]:
        return True
    want, lead = title_forms(kw.get("title"))
    if not want:
        return False
    if not any(want in t for t in texts):
        main_len = len(fold_title(one_line(kw.get("title")).partition(":")[0]))
        slack = MAIN_SLACK if main_len >= MAIN_MIN else 0
        tail = lead[main_len:]
        if not lead or not any(tail in t and near_in(lead, t, slack) for t in texts):
            return False
    if not kw.get("year"):
        return True
    return year.isdigit() and str(kw["year"]).isdigit() and abs(int(year) - int(kw["year"])) <= YEAR_SLACK


# what the command line says, as the record does, of a record whose key works Sift cannot check, which
# Cites key works calls Can't check (Adam's dialog, 14 October, later): `cites_of` gave None
CITES_UNCHECKED = "Crossref holds no reference list for this record, so Sift cannot check."


def cites_of(entry, works: list) -> list[str] | None:
    """The key works a record cites, by key: by Crossref's references when Crossref holds any for it, and
    only when it holds none by OpenAlex's, by each key work's OpenAlex ID, or None when neither service
    has told Sift its references. OpenAlex's references cannot show a key work kept with no OpenAlex ID,
    so when they find none and such a key work is in the list, the answer is None, not none cited."""
    if not isinstance(entry, dict):
        return None
    cr = entry.get("crossref")
    if isinstance(cr, list) and cr:
        return [key_work_key(k) for k in works if any(ref_cites(k, ref) for ref in cr)]
    oa = entry.get("openalex")
    if isinstance(oa, list):
        held = set(oa)
        found = [key_work_key(k) for k in works if k.get("id") and k["id"] in held]
        if found or all(k.get("id") for k in works):
            return found
    return None


def extras_of(sc: Screening) -> dict:
    """What a record's view takes beyond its own row, worked out once for the screening: the review's key
    works, the references kept, his studies, and every record's authors, title words and participants for
    the suggestions, with each author's records found by ID and by key. The authors and the title words
    are held while the cells they come from stand as they were, so an act on a record works none of
    them out again."""
    sign = hash(tuple((rec, sc.cell(rec, "authors"), sc.cell(rec, AUTHORS_COLUMN), sc.cell(rec, "title")) for rec in sc.ids))
    place = str(Path(sc.folder).resolve())
    held = _EXTRAS.get(place)
    if held and held[0] == sign:
        people, by, words, df = held[1]
    else:
        people = {rec: author_list(sc, rec) for rec in sc.ids}
        by: dict[str, list[str]] = {}
        for rec, authors in people.items():
            for aid, key, _ in authors:
                for mark in (f"id:{aid}" if aid else "", f"name:{key}"):
                    if mark:
                        by.setdefault(mark, []).append(rec)
        words = {rec: title_words(sc.cell(rec, "title")) for rec in sc.ids}
        df: dict[str, int] = {}
        for ws in words.values():
            for w in ws:
                df[w] = df.get(w, 0) + 1
        _EXTRAS.clear()
        _EXTRAS[place] = (sign, (people, by, words, df))
    held = read_settings(sc.folder).get("table")
    held = held if isinstance(held, dict) else {}
    own = own_columns(held, sc)
    terms = terms_of_plan(sc.folder)
    return {"works": key_works_of(sc.folder), "refs": references(sc.folder), "studies": studies_of(sc),
            "people": people, "by": by, "words": words, "df": df,
            "rare": max(2, int(RARE_SHARE * len(sc.ids))), "counts": {},
            "form": form_fields(own, sections_of(held, own)), "own": own, "terms": terms,
            "how": match_context(sc.folder, terms)}


def participants_of(sc: Screening, rec: str, ex: dict) -> int | None:
    """A record's count of participants, his own or the abstract's guess, worked out once."""
    held = ex["counts"]
    if rec not in held:
        f = fields_of(sc, rec)
        given = f["participants"]
        held[rec] = int(given) if f["confirmed"] and given.isdigit() else f["guess"]
    return held[rec]


def suggestions(sc: Screening, rec: str, ex: dict) -> list[dict]:
    """The records Sift suggests may be reports of one study with this one, never a link by itself (13
    October): each sharing two or more authors with it, or one who makes up at least half the shorter list,
    authors compared as sets, by OpenAlex ID where both have one, else by surname and first initial, and
    none in its study already. Each says the authors shared over the shorter list, then what strengthens
    it, the same count of participants, the distinctive title words both carry and years within four,
    the strongest first, at most SUGGEST_MAX. A record with no authors has none."""
    mine = ex["people"].get(rec) or []
    if not mine:
        return []
    study = one_line(sc.cell(rec, STUDY_COLUMN))
    seen: set[str] = set()
    for aid, key, _ in mine:
        for mark in (f"id:{aid}" if aid else "", f"name:{key}"):
            seen.update(ex["by"].get(mark, []) if mark else [])
    out = []
    for other in [r for r in sc.ids if r in seen and r != rec]:
        theirs = ex["people"].get(other) or []
        if study and one_line(sc.cell(other, STUDY_COLUMN)) == study:
            continue
        shared = shared_authors(mine, theirs)
        n, m = len(shared), min(len(mine), len(theirs))
        if not (n >= 2 or (n >= 1 and 2 * n >= m)):
            continue
        names = [given_first(mine[i][2]) for i in shared]
        reasons = [sift_words.t("sift_server.study.shares", shared=n, n=m, other=other, names=and_join(names))]
        strength = 0
        a, b = participants_of(sc, rec, ex), participants_of(sc, other, ex)
        if a and a == b:
            reasons.append(sift_words.t("sift_server.study.participants", n=a))
            strength += 1
        common = sorted(w for w in ex["words"][rec] & ex["words"][other] if ex["df"].get(w, 0) <= ex["rare"])
        if common:
            reasons.append(sift_words.t("sift_server.study.titles", words=formats.list_words(common)))
            strength += 1
        ya, yb = match_year(sc.cell(rec, "year")), match_year(sc.cell(other, "year"))
        if ya and yb and abs(int(ya) - int(yb)) <= 4:
            reasons.append(sift_words.t("sift_server.study.same_year", year=ya) if ya == yb
                           else sift_words.t("sift_server.study.years", first=min(ya, yb), last=max(ya, yb)))
            strength += 1
        out.append({"rec_id": other, "title": plain(sc.cell(other, "title")), "year": sc.cell(other, "year").strip(),
                    "study": one_line(sc.cell(other, STUDY_COLUMN)), "shared": n, "of": m, "names": names,
                    "reasons": reasons, "rank": (n / m if m else 0, n, strength)})
    out.sort(key=lambda s: s["rank"], reverse=True)
    return [{k: v for k, v in s.items() if k != "rank"} for s in out[:SUGGEST_MAX]]


def own_view(sc: Screening, rec: str, ex: dict) -> dict:
    """A record's columns from OpenAlex and Crossref and its study as the screen draws them: `notices`,
    its kinds, an empty list once asked with none and None when never asked, with each notice, `oa`,
    OpenAlex's kind of open access or empty, `countries` by name, `study` and the other reports of it,
    `cites`, the key works it cites by key or None while its references are not known, and `suggest`,
    the records Sift suggests are reports of the same study."""
    study = one_line(sc.cell(rec, STUDY_COLUMN))
    oa = sc.cell(rec, OA_COLUMN).strip().lower()
    return {"notices": {"kinds": notice_kinds(sc.cell(rec, RETRACTION_COLUMN)), "list": notices_of(sc.cell(rec, NOTICES_COLUMN))},
            "oa": oa if oa in OA_KINDS else "", "countries": [country_name(c) for c in country_codes(sc.cell(rec, COUNTRIES_COLUMN))],
            "study": study, "study_with": [r for r in ex["studies"].get(study, []) if r != rec] if study else [],
            "cites": cites_of(ex["refs"].get(rec), ex["works"]), "suggest": suggestions(sc, rec, ex),
            "openalex_date": sc.cell(rec, OPENALEX_DATE).strip(), "crossref_date": sc.cell(rec, CROSSREF_DATE).strip()}


def key_works_view(works: list) -> list[dict]:
    """The review's key works as the screen and the reading tools name them, each its key and its label."""
    return [{"key": key_work_key(k), "label": key_work_label(k), "title": one_line(k.get("title")),
             "year": str(k.get("year") or ""), "doi": str(k.get("doi") or ""), "id": str(k.get("id") or "")} for k in works]


def next_study(sc: Screening, folder) -> str:
    """The label a new study takes, the number after the highest the CSV or the log has ever given, so no
    study's label is given twice."""
    used = [study_number(sc.cell(r, STUDY_COLUMN)) for r in sc.ids]
    used += [study_number(e.get("study")) for e in read_lines(folder) if e.get("act") == "study"]
    return f"Study {max([n for n in used if n] + [0]) + 1}"


def study(folder, act, rec_id, other=None, tool: str = TOOL, wait: float | None = None) -> dict:
    """Same study and Unlink (13 October), his to make as a decision is: `link` puts the record and
    `other` in one study, a new one when neither is in one, the study either is in when one is, and when
    both are in studies of their own the later study's reports join the earlier's. `unlink` takes the
    record out of its study, and the last report left in a study with it, since a study of one report
    links nothing. Each is one line of the log, `act` `study`, naming the records it moved and their
    studies before, and the CSV is written whole under the lock as his fields are. A link that changes
    nothing writes nothing. The answer is what every act answers, the flow among it, with `records`, the
    records it moved and the one linked, as the screen draws them."""
    act = str(act or "").strip()
    if act not in ("link", "unlink"):
        raise SiftError(sift_words.t("sift_server.a_study_is_linked_or"))
    with locks.held(lock_path(folder), wait):
        sc = load(folder)
        entries = read_log(folder)
        rec = str(rec_id or "").strip()
        if rec not in sc.at:
            raise SiftError(sift_words.t("sift_server.there_is_no_record_in", rec=rec or sift_words.t("sift_server.none_named"), csv_name=CSV_NAME))
        label = lambda r: one_line(sc.cell(r, STUDY_COLUMN))
        moved: dict[str, str] = {}
        two = ""
        if act == "link":
            two = str(other or "").strip()
            if two not in sc.at:
                raise SiftError(sift_words.t("sift_server.there_is_no_record_in_2", two=two or sift_words.t("sift_server.none_named"), csv_name=CSV_NAME))
            if two == rec:
                raise SiftError(sift_words.t("sift_server.a_record_cannot_be_linked"))
            a, b = label(rec), label(two)
            if a and a == b:
                return dict(answer(sc, entries, rec), records=[], changed=False)
            if a and b:
                target, gone = sorted((a, b), key=study_order)
                moved = {r: gone for r in sc.ids if label(r) == gone}
            elif a or b:
                target = a or b
                moved = {(two if a else rec): ""}
            else:
                target = next_study(sc, folder)
                moved = {rec: "", two: ""}
            for r in moved:
                set_cells(sc, r, {STUDY_COLUMN: target})
            entry = {"n": next_n(folder), "at": now_iso(), "act": "study", "change": "link", "rec_id": rec, "with": two,
                     "study": target, "was": moved, "records": [r for r in sc.ids if label(r) == target], "tool": tool}
        else:
            a = label(rec)
            if not a:
                return dict(answer(sc, entries, rec), records=[], changed=False)
            left = [r for r in sc.ids if label(r) == a and r != rec]
            moved = {rec: a, **({left[0]: a} if len(left) == 1 else {})}
            for r in moved:
                set_cells(sc, r, {STUDY_COLUMN: ""})
            entry = {"n": next_n(folder), "at": now_iso(), "act": "study", "change": "unlink", "rec_id": rec,
                     "study": a, "was": moved, "records": [r for r in left if r not in moved], "tool": tool}
        append(folder, entry)
        write_atomic(csv_path(folder), csv_text(sc))
        ex = extras_of(sc)
        held = states(entries)
        touched = [r for r in sc.ids if r in moved or r in (rec, two)]
        out = settled(sc, entries, rec, ex)
        return dict(out, records=[record_view(sc, held, r, extras=ex) for r in touched], changed=True)


def write_filled(folder, cells: dict, refs: dict | None = None, wait: float | None = None) -> int:
    """Sift's own columns from OpenAlex and Crossref for records of a screening, `cells` by rec_id, each a
    record of column and value, written under the lock, a column the CSV lacks added after the last, and
    each record's references, `refs` by rec_id, each its `crossref` and `openalex` lists, kept in
    `screening.references.json` (see `sift_search.fill_columns`). Only those columns, and a record's
    keywords and language where it holds none (14 October): a column of any other name, or a record the CSV no longer
    holds, is passed over, and never a decision, a proposal, a field of his or the log. Each file is
    written only when it changed. Answers how many records it filled."""
    with locks.held(lock_path(folder), wait):
        sc = load(folder)
        before = csv_text(sc)
        done = set()
        for rec, values in (cells or {}).items():
            rec = str(rec).strip()
            kept = {k: one_line(v) if k != NOTICES_COLUMN else str(v or "").strip()
                    for k, v in (values or {}).items() if k in FILLED and v is not None}
            for name in (KEYWORDS_COLUMN, LANGUAGE_COLUMN):
                words = one_line((values or {}).get(name)) if isinstance(values, dict) else ""
                if words and rec in sc.at and not sc.cell(rec, name).strip():
                    kept[name] = words
            if rec in sc.at and kept:
                set_cells(sc, rec, kept)
                done.add(rec)
        if csv_text(sc) != before:
            write_atomic(csv_path(folder), csv_text(sc))
        held = dict(references(folder))
        changed = False
        for rec, entry in (refs or {}).items():
            rec = str(rec).strip()
            if rec not in sc.at or not isinstance(entry, dict):
                continue
            now = dict(held.get(rec) or {})
            for part in ("crossref", "openalex"):
                if isinstance(entry.get(part), list):
                    now[part] = entry[part]
            if now != held.get(rec):
                held[rec] = now
                changed = True
            done.add(rec)
        if changed:
            write_references(folder, held)
        return len(done)


# ------------------------------------------------- the plan's terms in Screening's filters

# Which of the search's terms a record holds (13 October, later), a group of the filters for each block of
# the plan as Search strategy holds it now, its newest version or the draft, since the filter looks forward
# and is no audit. A term is found in the record's title, its abstract and its keywords, the CSV's
# `keywords` column since 14 October and those the run's raw files hold, case and accents folded: a
# phrase as a phrase, quoted or of several words as the plan writes one, a trailing asterisk as
# truncation, a bare word on word boundaries. A term in the
# syntax of a database, a field tag or NEAR and the like, which the plan keeps as he typed it, is found
# by its plain words, each of them. Worked out as the screen reads the screening, from the plan and the
# CSV, so nothing is written and every run made before has it at once.
TERM_GROUP = "term:"
TERM_KEY = re.compile(r"term:\d{1,3}")
# what is taken out of a term Sift cannot read before its plain words are read: a tag in square or curly
# brackets, an Ovid field list after a full stop, a field's name before its bracket, a field code in
# capitals, and the operators of proximity and of logic
TERM_SYNTAX = re.compile(r"\[[^\]]*\]|\{[^}]*\}|\.[A-Za-z]{2,}(?:,[A-Za-z]{2,})*\.|\b[A-Z][A-Z-]*\s*=?\s*\("
                         r"|\b(?:TI|AB|KW|SU|TX|MH|MM|TS|SO|DE|ID)\b\s*[=:]?")
TERM_OPERATORS = re.compile(r"(?:and|or|not|near|adj|pre|w|n)\d*", re.I)
TERM_WORDS = re.compile(r"[^\W_][\w'-]*\*?")
_TERMS: dict = {}
_KEYWORDS: dict = {}


def term_pattern(words: list[str]) -> re.Pattern:
    """Words as one pattern over folded text: each in turn, parted by spaces or a hyphen, a hyphen of a
    word standing for a hyphen, a space or none, a word ending in an asterisk any word it begins, each at
    a word's edge."""
    parts = []
    for w in words:
        w = fold(w)
        cut = w.endswith("*")
        w = w.rstrip("*")
        body = r"[-\s]?".join(re.escape(p) for p in w.split("-") if p)
        parts.append(body + (r"\w*" if cut else ""))
    return re.compile(r"(?<!\w)" + r"[-\s]+".join(parts) + r"(?!\w)")


def term_rule(line: str) -> list[re.Pattern]:
    """The patterns a term is found by, each of them in the text: the term as Search strategy reads it,
    one pattern, or for a term in a database's syntax Sift cannot read, each of its plain words."""
    import sift_search  # here, since it reads this module first
    t, _ = sift_search.parse_term(line)
    if t is not None:
        return [term_pattern(t["text"].split())]
    text = TERM_SYNTAX.sub(" ", re.sub(r"[$?#]", "*", str(line or "")))
    words = [w for w in TERM_WORDS.findall(text.replace("/", " "))
             if not TERM_OPERATORS.fullmatch(w) and not w.strip("*").isdigit()]
    return [term_pattern([w]) for w in words]


def terms_of_plan(folder) -> list[dict]:
    """The blocks of the review's plan as its newest version holds them, the draft among them, each its
    place, `i`, its name and its terms as he wrote them with the patterns they are found by, a block with no
    term left out, or none for a screening of no review. Read once for each change to the plan."""
    review = review_of(folder)
    if review is None:
        return []
    import sift_search  # here, since it reads this module first
    path = sift_search.plan_path(review)
    try:
        st = path.stat()
    except OSError:
        return []
    mark = (str(path.resolve()), st.st_mtime_ns, st.st_size)
    held = _TERMS.get(mark[0])
    if held and held[0] == mark:
        return held[1]
    try:
        last = sift_search.newest(sift_search.read_file(review))
    except WorkbookError:
        last = None
    out = []
    if last:
        plan = sift_search.clean_plan(last.get("plan"))
        for i, b in enumerate(plan["blocks"]):
            terms = [{"term": t, "rule": term_rule(t)} for t in b["terms"]]
            terms = [t for t in terms if t["rule"]]
            if terms:
                out.append({"i": i, "name": b["name"], "terms": terms})
    _TERMS.clear()
    _TERMS[mark[0]] = (mark, out)
    return out


def blocks_view(blocks: list, records: list | None = None, how: dict | None = None) -> list[dict]:
    """The blocks as the screen names their groups: each its key, `term:` and its place, its label, Block 1
    and its name, and its terms as he wrote them, and with the records' views, `why`, each line that says
    how a database found a record holding none of the block's terms that any record stands under, in
    `MATCH_LINES` order, each naming the databases of every record under it in the order of the run's
    plan (see `match_context`), a field Sift cannot name last."""
    out = []
    for b in blocks:
        key = f"{TERM_GROUP}{b['i']}"
        view = {"key": key, "label": sift_words.t("sift_server.block_named", i=b['i'] + 1, name=b["name"]) if b["name"]
                else sift_words.t("sift_server.block", i=b['i'] + 1),
                "terms": [t["term"] for t in b["terms"]]}
        if records is not None:
            named: dict[str, list] = {}
            for r in records:
                for w in ((r.get("matched") or {}).get(key) or {}).get("why") or []:
                    have = named.setdefault(w["value"], [])
                    have += [n for n in w["names"] if n not in have]
            rank = {n: i for i, n in enumerate((how or {}).get("order") or [])}
            view["why"] = []
            for kind in MATCH_LINES:
                if MATCH_MARK + kind in named:
                    names = sorted(named[MATCH_MARK + kind], key=lambda n: rank.get(db_key(n), len(rank)))
                    view["why"].append({"value": MATCH_MARK + kind, "label": match_line(kind, names)})
        out.append(view)
    return out


def keywords_index(folder) -> tuple[dict, dict]:
    """The keywords the run's raw files hold, by each record's DOI and by its title, as a record of the CSV
    is matched to them, read once for each change to the files. None for a screening with no raw files."""
    import sift_search  # here, since it reads this module first
    files = sorted(Path(folder).glob("raw_*.json"))
    marks = []
    for f in files:
        try:
            st = f.stat()
            marks.append((f.name, st.st_mtime_ns, st.st_size))
        except OSError:
            continue
    mark = (str(Path(folder).resolve()), tuple(marks))
    held = _KEYWORDS.get(mark[0])
    if held and held[0] == mark:
        return held[1]
    by_doi: dict[str, list] = {}
    by_title: dict[str, list] = {}
    for f in files:
        try:
            data = json.loads(f.read_text(encoding="utf-8"))
        except (OSError, ValueError, UnicodeDecodeError):
            continue
        for r in data if isinstance(data, list) else []:
            words = one_line(r.get("keywords")) if isinstance(r, dict) else ""
            if not words:
                continue
            doi, title = sift_search.doi_key(r.get("doi")), match_title(r.get("title"))
            if doi:
                by_doi.setdefault(doi, []).append(words)
            if title:
                by_title.setdefault(title, []).append(words)
    _KEYWORDS.clear()
    _KEYWORDS[mark[0]] = (mark, (by_doi, by_title))
    return by_doi, by_title


def record_terms(sc: Screening, rec: str, blocks: list) -> dict:
    """The terms of each block a record holds, by the block's key, each as he wrote it, in the block's
    order, an empty list for a block none of whose terms it holds (see `record_match`)."""
    return record_match(sc, rec, blocks, NO_MATCH)[0]


# Where a block's terms were found in a record (14 October), and for a record holding none of them in the
# text Sift has, how it matched as written: from the databases that found it, its `sources`, and the
# fields each searched the block in, as the run's plan has them (see `sift_search.beyond_text`). Europe PMC
# searches methods sections where the plan asks, and the databases their own keyword and index fields,
# which Sift never holds whole, Scopus's index terms, PsycInfo's key concepts, PubMed's keywords and the
# like, and some records come with no abstract. Adam chose these words, kept here alone, the screen, the
# command line and MCP taking them from the screening's view, each line a value of the block's filter group
# as a bar and its kind. A record that fits two shows both, and one no database's fields explain stands
# under the last, a field Sift cannot name, whose value is the bar and `none`, the filters' own blank.
# Where its terms were found is Title, Abstract or Keywords. The full-text line, on Adam's yes of 14
# October, names the databases that searched the block in full text, Europe PMC's BODY, OpenAlex's full
# text, EBSCO's TX and Google Scholar. Reworded on 14 October, later, by Adam's dialog, so a reader
# understands them at once: in the filters each line stands under a heading of two lines, `MATCH_HEAD`,
# the databases joined A, B or C, and on the record and the command line each block that holds none of its
# terms is one sentence, `MATCH_NONE` and then `MATCH_SAID` for each of its lines, its or their as the
# databases are one or several.
MATCH_LINES = {"methods": "{} methods sections", "keywords": "{} keywords", "fulltext": "{} full text",
               "noabstract": "the abstract, which Sift does not hold", "none": "a field Sift cannot name"}
MATCH_SAID = {"methods": "{} matched at least one in {} methods sections, which Sift does not hold, so Sift cannot say which.",
              "keywords": "{} matched at least one in {} keywords, which Sift does not hold, so Sift cannot say which.",
              "fulltext": "{} matched at least one in {} full text, which Sift does not hold, so Sift cannot say which.",
              "noabstract": "The database matched at least one in the abstract, which Sift does not hold.",
              "none": "The database matched at least one in a field Sift cannot name."}
MATCH_HEAD = ("None of the above in the title or abstract.", "The database matched at least one in:")
MATCH_NONE = "none in the title or abstract."
MATCH_PLACES = (("title", "Title"), ("abstract", "Abstract"), ("keywords", "Keywords"))
# the command line's words before where a block's terms were found, the Matched in column's heading on the page
MATCHED_IN = "Matched in"
# the same lines for a person, in the run's language, the page's filters and record
MATCH_LINE_KEYS = {"methods": lambda names: sift_words.t("sift_server.match.line.methods", names=names),
                   "keywords": lambda names: sift_words.t("sift_server.match.line.keywords", names=names),
                   "fulltext": lambda names: sift_words.t("sift_server.match.line.fulltext", names=names),
                   "noabstract": lambda names: sift_words.t("sift_server.match.line.noabstract"),
                   "none": lambda names: sift_words.t("sift_server.match.line.none")}
MATCH_SAID_KEYS = {"methods": lambda names, n: sift_words.t("sift_server.match.said.methods", names=names, n=n),
                   "keywords": lambda names, n: sift_words.t("sift_server.match.said.keywords", names=names, n=n),
                   "fulltext": lambda names, n: sift_words.t("sift_server.match.said.fulltext", names=names, n=n),
                   "noabstract": lambda names, n: sift_words.t("sift_server.match.said.noabstract"),
                   "none": lambda names, n: sift_words.t("sift_server.match.said.none")}
MATCH_PLACE_KEYS = {"title": lambda: sift_words.t("sift_server.match.place.title"),
                    "abstract": lambda: sift_words.t("sift_server.match.place.abstract"),
                    "keywords": lambda: sift_words.t("sift_server.match.place.keywords")}
MATCH_MARK = "|"
# what a record's databases searched when nothing says, so no line is given
NO_MATCH = {"names": {}, "blocks": {}, "order": []}
_MATCH: dict = {}


def db_key(name) -> str:
    """A database's name as `sources` and the plan are matched by, its spacing tidied and its case folded
    (14 October)."""
    return " ".join(str(name or "").split()).casefold()


def match_line(kind: str, names: list) -> str:
    """One of Adam's lines as the filters say it, the databases it names joined A, B or C."""
    return MATCH_LINE_KEYS[kind](or_join(names))


def match_said(kind: str, names: list) -> str:
    """One of Adam's lines as the record says it, a sentence, the databases joined A, B or C and its or
    their after them as they are one or several (14 October, later)."""
    return MATCH_SAID_KEYS[kind](or_join(names), len(names) or 1)


def match_context(folder, blocks: list) -> dict:
    """What each database searched each block of the plan in beyond a record's title and abstract (see
    `sift_search.beyond_text`), worked out once for the screening: `names`, each name `sources` may give
    a database, folded by `db_key`, to the database it stands for, every database Sift knows, the plan's
    others and the run's own, `blocks`, by each block's place, each database's field, `methods`, `keywords`
    or `fulltext`, and `order`, the plan's databases' names in its order. The plan is the version the run
    ran, as `run.json` names it, else the newest, a block it lacks taken from the newest. Read once for each
    change to the plan or the run, and `NO_MATCH` for a screening of no review."""
    review = review_of(folder)
    if review is None or not blocks:
        return NO_MATCH
    import sift_search  # here, since it reads this module first
    marks = []
    for p in (sift_search.plan_path(review), Path(folder) / sift_search.RUN_FILE):
        try:
            st = p.stat()
            marks.append((st.st_mtime_ns, st.st_size))
        except OSError:
            marks.append(None)
    mark = (str(Path(folder).resolve()), tuple(marks), tuple(b["i"] for b in blocks))
    held = _MATCH.get(mark[0])
    if held and held[0] == mark:
        return held[1]
    try:
        versions = sift_search.read_file(review)["versions"]
    except WorkbookError:
        versions = []
    meta = sift_search.read_run(Path(folder))
    ran = next((v for v in versions if v.get("version") == meta.get("version")), None)
    last = sift_search.clean_plan(versions[-1]["plan"] if versions else None)
    plan = sift_search.clean_plan(ran["plan"]) if ran else last
    names = {db_key(n): s for s, n in sift_search.NAMES.items() if s != sift_search.OTHER}
    names.update({db_key(n): s for s, n in sift_search.FULL_NAMES.items()})
    for p in (last, plan):
        names.update({db_key(sift_search.name_of(s, p)): s for s in p["databases"]})
    for s, said in (meta.get("sources") or {}).items():
        if isinstance(said, dict) and sift_search.known(s) and db_key(said.get("name")):
            names[db_key(said.get("name"))] = s
    fields = {}
    for b in blocks:
        i = b["i"]
        block = plan["blocks"][i] if i < len(plan["blocks"]) else last["blocks"][i] if i < len(last["blocks"]) else None
        if block is not None:
            fields[i] = {s: sift_search.beyond_text(block, s, plan) for s in set(names.values())}
    order = [db_key(sift_search.name_of(s, plan)) for s in plan["databases"]]
    out = {"names": names, "blocks": fields, "order": order}
    _MATCH.clear()
    _MATCH[mark[0]] = (mark, out)
    return out


def match_why(sc: Screening, rec: str, i: int, how: dict) -> list[dict]:
    """The lines that say how a record holding none of block `i`'s terms in the text Sift has was found,
    each its `value`, a bar and its kind, its `label`, the line as the filters say it naming the record's
    own databases in the order of the run's plan, `said`, the line as the record says it, and those
    `names`: the databases that found it and searched the block in methods sections, those that searched
    their keyword or index fields, those that searched its full text (14 October), and no abstract when it
    has none, in that order, and a field Sift cannot name when none of these fits (14 October, later)."""
    found: dict[str, list] = {"methods": [], "keywords": [], "fulltext": []}
    fields = (how.get("blocks") or {}).get(i) or {}
    for name in sources_of(sc.cell(rec, "sources")):
        kind = fields.get(how["names"].get(db_key(name), ""), "")
        if kind in found and name not in found[kind]:
            found[kind].append(name)
    rank = {n: k for k, n in enumerate(how.get("order") or [])}
    found = {k: sorted(n, key=lambda x: rank.get(db_key(x), len(rank))) for k, n in found.items()}
    kinds = [(k, n) for k, n in found.items() if n]
    if not plain(sc.cell(rec, "abstract")).strip():
        kinds.append(("noabstract", []))
    return [{"value": MATCH_MARK + k, "label": match_line(k, n), "said": match_said(k, n), "names": n}
            for k, n in kinds or [("none", [])]]


def record_match(sc: Screening, rec: str, blocks: list, how: dict | None = None) -> tuple[dict, dict]:
    """The terms of each block a record holds and where, by the block's key: `terms`, each as he wrote
    it, in the block's order, an empty list for a block none of whose terms it holds, and `matched`, for
    a block it holds terms of, `in`, the fields they were found in, Title, Abstract or Keywords, and for
    one it holds none of, `why`, the lines that say how it was found (see `match_why`), and `said`, the
    record's sentence for the block after its name, `MATCH_NONE` and each line's own (14 October, later),
    with `how` from `match_context`, worked out when not given. A term is found in the title, the abstract
    and the keywords, the CSV's `keywords` column and those the run's raw files hold."""
    if not blocks:
        return {}, {}
    import sift_search  # here, since it reads this module first
    by_doi, by_title = keywords_index(sc.folder)
    doi = sift_search.doi_key(sc.cell(rec, "doi"))
    words = by_doi.get(doi) if doi else None
    if words is None:
        words = by_title.get(match_title(sc.cell(rec, "title"))) or []
    kws = [w for w in dict.fromkeys([one_line(sc.cell(rec, KEYWORDS_COLUMN))] + list(words)) if w]
    fields = {"title": fold(sc.cell(rec, "title")), "abstract": fold(sc.cell(rec, "abstract")), "keywords": fold(" | ".join(kws))}
    text = " | ".join(fields.values())
    terms, matched = {}, {}
    for b in blocks:
        key = f"{TERM_GROUP}{b['i']}"
        held = [t for t in b["terms"] if all(p.search(text) for p in t["rule"])]
        terms[key] = [t["term"] for t in held]
        if held:
            places = [MATCH_PLACE_KEYS[place]() for place, _ in MATCH_PLACES
                      if any(p.search(fields[place]) for t in held for p in t["rule"])]
            matched[key] = {"in": places, "why": []}
        else:
            if how is None:
                how = match_context(sc.folder, blocks)
            why = match_why(sc, rec, b["i"], how)
            matched[key] = {"in": [], "why": why, "said": " ".join([sift_words.t("sift_server.match.none")] + [w["said"] for w in why])}
    return terms, matched


# ------------------------------------------------------------------ the screen

def record_view(sc: Screening, held: dict, rec: str, carried=False, numbers: dict | None = None,
                extras: dict | None = None) -> dict:
    """One record as the screen draws it: its number, `n`, the fields of its head, the address its
    `url` column gives, as a link when it is one, the abstract as plain text, the columns beyond them
    that hold anything, and at each stage where it stands, its proposals, the review's first and then
    Sift's own, each with the grounds found in the abstract, and `proposal`, the first of them. `new`
    says it is new in a screening that follows an earlier run, `carried` the records carried from it,
    read from the log when not given, `numbers` each record's number, read from sift.json when
    not given, and `extras` what its columns from OpenAlex and Crossref and its study take (see
    `own_view`), worked out when not given. `form` is its form of Extract and appraise (see
    `form_state`), `terms` the terms of each block of the plan it holds and `matched` where they were
    found or how it was found without them (see `record_match`), `language` its languages by name
    (see `language_list`), and `excerpts` his key excerpts (see `excerpts_of`)."""
    carried = carried_of(sc.folder) if carried is False else carried
    numbers = numbers_of(sc.folder, sc) if numbers is None else numbers
    ex = extras or extras_of(sc)
    abstract = plain(sc.cell(rec, "abstract"))
    stages = {}
    for stage in STAGES:
        props = []
        for prop in proposals_of(sc, rec, stage) or [proposal_of(sc, rec, stage)]:
            spans, found = ground_spans(abstract, prop["grounds"])
            props.append(dict(prop, grounds=plain(prop["grounds"]), marks=spans, found=found))
        st = state_of(sc, held, rec, stage)
        seen = proposal_seen(sc, held, rec, stage)["decision"]
        # whether his decision differs from the proposal it stands against, a tick of the Decision filter
        stages[stage] = dict(st, **{
            "in": in_stage(sc, held, rec, stage), "proposal": props[0],
            "proposals": [p for p in props if p["decision"]],
            "differs": bool(st["decision"] and seen and st["decision"] != seen)})
    skip = set(SHOWN) | set(PROPOSAL_COLUMNS) | set(DECISION_COLUMNS) | set(AI_PROPOSAL_COLUMNS) | {ZOTERO_COLUMN}
    url = url_link(sc.cell(rec, URL_COLUMN))
    if url:
        skip.add(URL_COLUMN)
    doi = sc.cell(rec, "doi").strip()
    terms, matched = record_match(sc, rec, ex["terms"], ex["how"])
    return {"rec_id": rec, "n": numbers.get(rec), "title": plain(sc.cell(rec, "title")),
            "authors": plain(sc.cell(rec, "authors")),
            "year": sc.cell(rec, "year").strip(), "journal": plain(sc.cell(rec, "journal")),
            "doi": doi, "link": doi_link(doi), "url": url, "sources": sc.cell(rec, "sources").strip(),
            "abstract": abstract, "found": sources_of(sc.cell(rec, "sources")),
            # the language by its English names, as the Language column says it (14 October)
            "more": [[name, plain(sc.cell(rec, name)) if name != LANGUAGE_COLUMN else ", ".join(language_list(sc.cell(rec, name)))]
                     for name in sc.header if name not in skip and not is_own(name) and sc.cell(rec, name).strip()],
            "fields": fields_of(sc, rec, abstract), "cited": cited_of(sc.cell(rec, CITED_COLUMN)),
            "cited_date": sc.cell(rec, CITED_DATE).strip(),
            "stages": stages, "pdf": pdf_path(sc.folder, rec) is not None,
            "new": carried is not None and rec not in carried, **own_view(sc, rec, ex),
            "form": form_state(sc, rec, ex["form"], ex["own"]), "terms": terms, "matched": matched,
            "language": language_list(sc.cell(rec, LANGUAGE_COLUMN)), "excerpts": excerpts_of(sc.cell(rec, EXCERPTS_COLUMN))}


def cited_of(value) -> int | None:
    """A record's count of citations as a whole number, nought among them, or None when its cell holds none."""
    text = str(value or "").strip()
    return int(text) if text.isdigit() else None


def url_link(value) -> str:
    """A cell as a link when it is one web address and nothing else, else empty."""
    s = str(value or "").strip()
    return s if re.fullmatch(r"https?://[^\s<>\"']+", s, re.I) else ""


def doi_link(doi: str) -> str:
    """A DOI as a link: the address as it is when it is one, else on doi.org."""
    d = str(doi or "").strip()
    if not d:
        return ""
    if re.match(r"^https?://", d, re.I):
        return d
    return "https://doi.org/" + re.sub(r"^doi:\s*", "", d, flags=re.I)


def screen(folder) -> dict:
    """Everything the screen needs to open a screening: every record with its number, the reason
    codes, the counts and the flow drawn from them, the table's view and columns, the review's key
    works, which the Cites key works column names, the blocks of its plan, whose terms and lines the
    filters take (see `terms_of_plan` and `blocks_view`), with the heading over the lines, `match_head`,
    and its benchmark papers, which Extract and appraise's filter lists."""
    sc = load(folder)
    entries = read_log(folder)
    held = states(entries)
    c = counts(sc, entries)
    carried = carried_of(folder)
    numbers = numbers_of(folder, sc)
    ex = extras_of(sc)
    records = [record_view(sc, held, rec, carried, numbers, ex) for rec in sc.ids]
    return {"name": Path(folder).name, "records": records,
            "key_works": key_works_view(ex["works"]), "blocks": blocks_view(ex["terms"], records, ex["how"]),
            "match_head": [sift_words.t("sift_server.match.head_none"), sift_words.t("sift_server.match.head_in")], "bench": benchmark_ids(sc),
            "reasons": reasons(folder, sc), "counts": c, "prisma": prisma_source(c), "undo": undo_said(entries, folder),
            "columns": sc.header, "table": table_settings(folder, sc), "stamp": stamp(folder), "log": LOG_NAME,
            "file": CSV_NAME}


def decided(folder) -> int:
    """How many records of a screening hold a decision at either stage, read without a write."""
    sc = load(folder)
    held = states(read_log(folder))
    return sum(1 for rec in sc.ids if any(state_of(sc, held, rec, stage)["decision"] for stage in STAGES))


def summary(folder) -> dict:
    """A screening's line for the home screen, read without a write: its records and how many are
    decided at each stage, or `said`, one line when it cannot be read."""
    try:
        c = counts(load(folder))
    except (SiftError, OSError) as exc:
        return {"said": str(exc)}
    return {"records": c["records"],
            "stages": {stage: {k: c["stages"][stage][k] for k in ("records", "decided", "undecided")} for stage in STAGES}}


# ------------------------------------------------- Sift's own proposals, and the review's side

def one_line(text) -> str:
    return " ".join(str(text or "").split())


def write_ai(folder, rec_id, stage, decision, reason: str = "", grounds: str = "", wait: float | None = None,
             model: str = "") -> dict:
    """Sift's own proposal for a record at a stage, asked of the app's AI from the screen, written
    under the lock into its own columns, `ai_proposed_decision`, `ai_proposed_reason` and
    `ai_grounds`, or the `ft_ai_` three, each added after the last column when missing, and the model
    that answered, `model`, as "model: " and its name in `ai_proposed_by` or `ft_ai_proposed_by` (14
    October), emptied when none is given. Never the review's proposal columns, a decision or the log.
    The answer is what every act answers."""
    word = decision_word(decision)
    if word not in DECISIONS:
        raise SiftError(sift_words.t("sift_server.a_proposal_is_include_maybe"))
    with locks.held(lock_path(folder), wait):
        sc = load(folder)
        entries = read_log(folder)
        held = states(entries)
        rec, stage = checked(sc, held, rec_id, stage)
        cols = AI_COLUMNS[stage]
        cells = {cols["proposed"]: word, cols["proposed_reason"]: one_line(reason) if word == "exclude" else "",
                 cols["grounds"]: one_line(grounds)}
        if one_line(model) or cols["by"] in sc.col:
            cells[cols["by"]] = f"{BY_MODEL} {one_line(model)}" if one_line(model) else ""
        set_cells(sc, rec, cells)
        write_atomic(csv_path(folder), csv_text(sc))
        return answer(sc, entries, rec)


def write_zotero(folder, keys: dict, wait: float | None = None) -> int:
    """Each record's item key in Zotero, `keys` by rec_id, written under the lock into
    `zotero_key`, added after the last column when missing, so a later sync finds the item it made. A
    record the CSV no longer holds is passed over. Never a decision, a proposal or the log. Answers how
    many it wrote."""
    with locks.held(lock_path(folder), wait):
        sc = load(folder)
        n = 0
        for rec, key in keys.items():
            rec, key = str(rec).strip(), one_line(key)
            if rec in sc.at and re.fullmatch(r"[A-Z0-9]{8}", key) and sc.cell(rec, ZOTERO_COLUMN) != key:
                set_cells(sc, rec, {ZOTERO_COLUMN: key})
                n += 1
        if n:
            write_atomic(csv_path(folder), csv_text(sc))
        return n


def write_cited(folder, counts: dict, day: str, wait: float | None = None) -> int:
    """Each record's count of citations, `counts` by rec_id, with the day it was asked, written under
    the lock into Sift's own `cited_by` and `cited_by_date`, each added after the last column when
    missing (see `sift_search.find_citations`). A record the CSV no longer holds, or a count that is
    not a whole number, is passed over. Never a decision, a proposal, a field of his or the log, and
    the CSV is written only when a cell changed. Answers how many records it filled."""
    with locks.held(lock_path(folder), wait):
        sc = load(folder)
        n, changed = 0, False
        for rec, count in counts.items():
            rec = str(rec).strip()
            if rec not in sc.at or not isinstance(count, int) or isinstance(count, bool) or count < 0:
                continue
            cells = {CITED_COLUMN: str(count), CITED_DATE: one_line(day)}
            if CITED_COLUMN not in sc.col or CITED_DATE not in sc.col or any(sc.cell(rec, k) != v for k, v in cells.items()):
                set_cells(sc, rec, cells)
                changed = True
            n += 1
        if changed:
            write_atomic(csv_path(folder), csv_text(sc))
        return n


def propose_review(folder, stage, items, dry_run: bool = False, wait: float | None = None) -> dict:
    """The review's own proposals for named records at a stage, from its side through the command
    line or MCP, written under the lock into `proposed_decision`, `proposed_reason` and `grounds`, or
    the `ft_` three, each added after the last column when missing. Each item names `rec_id`,
    `decision`, `reason` and `grounds`. A record the CSV lacks or named twice, a decision that is not
    one, or a reject's reason that does not stand (see `reason_problem`) refuses the whole write. Never a
    decision, Sift's own columns or the log. The answer names the records written and those whose
    grounds the abstract does not hold word for word."""
    stage = stage_key(stage)
    if not isinstance(items, list) or not items:
        raise SiftError(sift_words.t("sift_server.name_at_least_one_record"))
    with locks.held(lock_path(folder), wait):
        sc = load(folder)
        codes = [r["code"] for r in reasons(folder)[stage]]
        problems, plan, seen = [], [], set()
        for i, item in enumerate(items, 1):
            if not isinstance(item, dict):
                problems.append(sift_words.t("sift_server.proposal_is_not_a_record", i=i))
                continue
            rec = str(item.get("rec_id") or "").strip()
            word = decision_word(item.get("decision"))
            reason = one_line(item.get("reason"))
            who = rec or sift_words.t("sift_server.proposal", i=i)
            if rec not in sc.at:
                problems.append(sift_words.t("sift_server.there_is_no_record_in", rec=rec or sift_words.t("sift_server.none_named"), csv_name=CSV_NAME))
            elif rec in seen:
                problems.append(sift_words.t("sift_server.is_named_twice_2", rec=rec))
            seen.add(rec)
            if word not in DECISIONS:
                problems.append(sift_words.t("sift_server.the_decision_is_include_maybe", who=who))
            elif word == "exclude" and reason_problem(stage, reason, codes):
                said = reason_problem(stage, reason, codes)
                problems.append(sift_words.t("sift_server.who_said", who=who, said=reason_problem(stage, reason, codes, lower=True)))
            plan.append((rec, word, reason if word == "exclude" else "", one_line(item.get("grounds"))))
        if problems:
            raise SiftError("\n".join(problems + [sift_words.t("sift_server.nothing_was_written")]))
        cols = COLUMNS[stage]
        unfound = []
        for rec, word, reason, grounds in plan:
            set_cells(sc, rec, {cols["proposed"]: word, cols["proposed_reason"]: reason, cols["grounds"]: grounds})
            if grounds and ground_spans(plain(sc.cell(rec, "abstract")), grounds)[1] is False:
                unfound.append(rec)
        if not dry_run:
            write_atomic(csv_path(folder), csv_text(sc))
        return {"written": [p[0] for p in plan], "stage": STAGE_WORDS[stage], "not_found": unfound,
                "columns": [cols["proposed"], cols["proposed_reason"], cols["grounds"]], "dry_run": bool(dry_run)}


def next_ids(ids: list[str], k: int, taken=frozenset()) -> list[str] | None:
    """k rec_ids continuing the CSV's sequence, R069 after R068, its letters and its width kept,
    passing over any in `taken`, or None when its rec_ids run in no sequence."""
    found = [m for m in (SEQUENCE.match(i) for i in ids) if m]
    if not found:
        return None
    prefixes: dict[str, int] = {}
    for m in found:
        prefixes[m.group(1)] = prefixes.get(m.group(1), 0) + 1
    prefix = max(prefixes, key=lambda p: (prefixes[p], p == found[-1].group(1)))
    mine = [m for m in found if m.group(1) == prefix]
    width = max(len(m.group(2)) for m in mine)
    n = max(int(m.group(2)) for m in mine)
    out, used = [], set(ids) | set(taken)
    while len(out) < k:
        n += 1
        rec = f"{prefix}{str(n).zfill(width)}"
        if rec not in used:
            out.append(rec)
    return out


def cell_text(value) -> str:
    """A value as a cell holds it: a list joined by semicolons, as the sources are, nothing as empty."""
    if value is None:
        return ""
    if isinstance(value, (list, tuple)):
        return "; ".join(one_line(v) for v in value if one_line(v))
    return str(value).strip()


def add_records(folder, records, dry_run: bool = False, wait: float | None = None) -> dict:
    """Records added at the foot of the CSV under the lock, from the review's side through the
    command line or MCP, every row before them and the order of the columns kept. Each record is a
    record of the CSV's own columns, `title` required. One with no `rec_id` takes the next of the
    CSV's sequence. A rec_id the CSV holds already or named twice, a column the CSV lacks, or a
    decision, Sift's own proposal column or a field or column of his refuses the whole write.
    `prisma.md` is written afresh."""
    if not isinstance(records, list) or not records:
        raise SiftError(sift_words.t("sift_server.give_at_least_one_record"))
    with locks.held(lock_path(folder), wait):
        sc = load(folder)
        never = set(DECISION_COLUMNS) | set(AI_PROPOSAL_COLUMNS)
        problems, given = [], []
        bare = sum(1 for r in records if isinstance(r, dict) and not cell_text(r.get("rec_id")))
        for i, rec in enumerate(records, 1):
            if not isinstance(rec, dict):
                problems.append(sift_words.t("sift_server.record_is_not_a_record", i=i))
                continue
            names = [str(k).strip() for k in rec]
            barred = sorted(n for n in names if n in never)
            his = sorted(n for n in names if is_own(n))
            unknown = sorted(n for n in names if n not in sc.col and n not in never and not is_own(n))
            if barred:
                problems.append(sift_words.t("sift_server.record_barred", i=i, names=', '.join(barred), n=len(barred)))
            if his:
                problems.append(sift_words.t("sift_server.record_his", i=i, names=', '.join(his), n=len(his)))
            if unknown:
                problems.append(sift_words.t("sift_server.record_has_no_column", i=i, csv_name=CSV_NAME, unknown=', '.join(unknown)))
            if not cell_text(rec.get("title")):
                problems.append(sift_words.t("sift_server.record_has_no_title", i=i))
            own = cell_text(rec.get("rec_id"))
            if own:
                if own in sc.at:
                    problems.append(sift_words.t("sift_server.is_in_already", own=own, csv_name=CSV_NAME))
                elif own in given:
                    problems.append(sift_words.t("sift_server.is_named_twice_4", own=own))
                elif own != one_line(own) or own.startswith(".") or any(c in own for c in "/\\\x00:"):
                    problems.append(sift_words.t("sift_server.cannot_be_a_rec_id", own=own))
                given.append(own)
        fresh = (next_ids(sc.ids, bare, given) or []) if bare else []
        if len(fresh) < bare:
            problems.append(sift_words.t("sift_server.give_each_record_a_rec", csv_name=CSV_NAME))
        if problems:
            raise SiftError("\n".join(problems + [sift_words.t("sift_server.nothing_was_added")]))
        added = []
        for rec in records:
            row = [""] * len(sc.header)
            for k, v in rec.items():
                row[sc.col[str(k).strip()]] = cell_text(v)
            rid = cell_text(rec.get("rec_id")) or fresh.pop(0)
            row[sc.col["rec_id"]] = rid
            sc.rows.append(row)
            added.append(rid)
        if not dry_run:
            write_atomic(csv_path(folder), csv_text(sc))
            write_prisma(folder, prisma_source(counts(load(folder))))
        return {"added": added, "records": len(sc.rows), "dry_run": bool(dry_run)}


# ------------------------------------------------------- his own fields and columns

def fields_of(sc: Screening, rec: str, abstract: str | None = None) -> dict:
    """His own fields on a record as the screen and the reading tools give them: the participants he
    gave, `confirmed` once he has confirmed a count or typed his own, `guess`, the count the abstract
    gives by pattern while he has not, never written, the rating as a number or None, the notes, the
    digest and the critique, and `own`, each column he added by its column's name."""
    given = sc.cell(rec, "participants").strip()
    confirmed = sc.cell(rec, "participants_confirmed").strip().lower() == CONFIRMED or bool(given)
    rating = sc.cell(rec, "rating").strip()
    text = plain(sc.cell(rec, "abstract")) if abstract is None else abstract
    return {"participants": given, "confirmed": confirmed, "guess": None if confirmed else guess_participants(text),
            "rating": int(rating) if rating.isdigit() and 1 <= int(rating) <= RATING_MAX else None,
            "notes": sc.cell(rec, "notes"), "digest": sc.cell(rec, "digest"), "critique": sc.cell(rec, "critique"),
            "own": {name: sc.cell(rec, name) for name in sc.header if name.startswith(OWN_PREFIX)}}


def long_text(value) -> str:
    """Notes, a digest or a critique as the CSV keeps them, lines ending in a plain newline and no
    trailing spaces, the text trimmed at both ends."""
    lines = str(value or "").replace("\r\n", "\n").replace("\r", "\n").strip().split("\n")
    return "\n".join(line.rstrip() for line in lines).strip()


def own_columns(settings: dict, sc: Screening) -> list[dict]:
    """The columns he added, in the order sift.json keeps them, each with its column, his name for
    it, its type and its choices, and since 13 October where it shows, the screening's table, the form
    of Extract and appraise or both, whether it offers Not reported, the field and the values it is
    shown for, its section and the Sift column it starts from (see `own_entry`), and any `col_` column of
    the CSV that sift.json has lost as text on the table, named from its column."""
    out, seen = [], set()
    held = settings.get("own") if isinstance(settings.get("own"), list) else []
    for c in held:
        if not isinstance(c, dict):
            continue
        key = str(c.get("key") or "")
        if not key.startswith(OWN_PREFIX) or key in seen:
            continue
        out.append(own_entry(c, key))
        seen.add(key)
    for name in sc.header:
        if name.startswith(OWN_PREFIX) and name not in seen:
            out.append(own_entry({"name": name[len(OWN_PREFIX):].replace("_", " ")}, name))
            seen.add(name)
    return out


# ------------------------------------------------------- the form of Extract and appraise

# Extract and appraise (13 October, later), the stage after full text, where each paper included at full
# text has its data extracted and its quality appraised on a form each project sets up, as PRISMA 2020's
# items 9 to 11 ask and Covidence and Cochrane's practice have it. The form is his own columns, one
# definition: each column says where it shows, `where`, the screening's table, the form or both, so a
# column moves between them with its values. Its name lives here and in the page's `RV_FORM_NAME` alone.
FORM_STAGE = "Extract and appraise"
WHERE = ("table", "form", "both")
# a field's value when the paper does not report it, offered on a field whose `not_reported` is on, the
# default for a new field of the form
NOT_REPORTED = "not reported"
# the Sift columns a field may start from, shown as its value until he changes it, and the types of field
# that may start from one, since a Sift column is words or a whole number
SIFT_SOURCES = ("citation", "title", "authors", "journal", "year", "doi", "country", "study", "participants")
FROM_TYPES = ("text", "long", "number")
# the types of field another field may be shown for, by the values it holds
CONDITION_TYPES = ("choice", "yesno", "multi")
YES_NO = ("yes", "no")
# a field's key, the CSV column it is written to after `col_` and the column the export names it by
KEY_SHAPE = re.compile(r"[A-Za-z0-9_]{1,60}")
# the export's own first columns, which no key may take
FIRST_KEYS = ("rec_id", "study")
PASSAGE_MAX = 4000
PAGE_MAX = 20
# the export of the form, one row per record included at full text, beside the screening
FORM_CSV = "screening.form.csv"
OWN_KEYS = ("key", "name", "type", "options", "where", "not_reported", "when", "section", "from")


def own_entry(c: dict, key: str) -> dict:
    """One column of his as sift.json keeps it, every part read with its default: `where` the table for a
    column made before 13 October, `not_reported` off, `when` none or the field and the values it is shown
    for, `section` none, `from` none."""
    kind = c.get("type") if c.get("type") in COLUMN_TYPES else "text"
    options = choices_of(c.get("options")) if kind in CHOICE_TYPES else []
    when = c.get("when") if isinstance(c.get("when"), dict) else None
    if when is not None:
        values = [one_line(v) for v in when.get("values") or [] if isinstance(v, str) and one_line(v)]
        ctl = str(when.get("key") or "")
        when = {"key": ctl, "values": list(dict.fromkeys(values))} if ctl.startswith(OWN_PREFIX) and values else None
    source = str(c.get("from") or "")
    if not (source in SIFT_SOURCES or (source.startswith(OWN_PREFIX) and source != key)) or kind not in FROM_TYPES:
        source = ""
    return {"key": key, "name": one_line(c.get("name")) or key[len(OWN_PREFIX):], "type": kind, "options": options,
            "where": c.get("where") if c.get("where") in WHERE else "table", "not_reported": c.get("not_reported") is True,
            "when": when, "section": one_line(c.get("section"))[:NAME_MAX], "from": source}


def kept_entry(c: dict) -> dict:
    return {k: c[k] for k in OWN_KEYS}


def on_form(c: dict) -> bool:
    return c.get("where") in ("form", "both")


def on_table(c: dict) -> bool:
    return c.get("where", "table") in ("table", "both")


def sections_of(held: dict, own: list) -> list[str]:
    """The form's section headings in his order, as sift.json keeps them under `sections`, each once, and a
    section a field names that the list lacks after them."""
    raw = held.get("sections") if isinstance(held.get("sections"), list) else []
    out = list(dict.fromkeys(one_line(s)[:NAME_MAX] for s in raw if isinstance(s, str) and one_line(s)))
    for c in own:
        if c["section"] and c["section"] not in out:
            out.append(c["section"])
    return out


def form_order(own: list, sections: list) -> list[dict]:
    """His columns in the form's order: those in no section first, then each section's in the sections'
    order, each in the order sift.json keeps them."""
    at = {s: i + 1 for i, s in enumerate(sections)}
    return sorted(own, key=lambda c: at.get(c["section"], 0) if c["section"] else 0)


def form_fields(own: list, sections: list) -> list[dict]:
    """The fields of the form, those of his columns that show on it, in its order."""
    return [c for c in form_order(own, sections) if on_form(c)]


def own_key(value) -> str:
    """A field's key as he gives it, with or without `col_`, as the CSV's column, or empty."""
    text = str(value or "").strip()
    return text if text.startswith(OWN_PREFIX) else OWN_PREFIX + text if text else ""


def plain_key(key: str) -> str:
    """A field's key as the export and Set up the form name it, its CSV column without `col_`."""
    return key[len(OWN_PREFIX):] if key.startswith(OWN_PREFIX) else key


def citation_of(sc: Screening, rec: str) -> str:
    """A record's citation in one line, its authors, year, title, journal and DOI's link as the CSV holds
    them, each piece ended by a full stop: Ward, Nell (2021). Keeping hives. Invented Apiary. https://..."""
    authors, year = plain(sc.cell(rec, "authors")), sc.cell(rec, "year").strip()
    head = " ".join(p for p in (authors, f"({year})" if year else "") if p)
    out = []
    for piece in (head, plain(sc.cell(rec, "title")), plain(sc.cell(rec, "journal"))):
        piece = one_line(piece)
        if piece:
            out.append(piece if piece[-1] in ".?!" else piece + ".")
    link = doi_link(sc.cell(rec, "doi"))
    return " ".join(out + ([link] if link else []))


def sift_value(sc: Screening, rec: str, source: str) -> str:
    """The value of the Sift column a field starts from, on one record."""
    if source == "citation":
        return citation_of(sc, rec)
    if source in ("title", "authors", "journal"):
        return plain(sc.cell(rec, source))
    if source in ("year", "doi"):
        return sc.cell(rec, source).strip()
    if source == "country":
        return ", ".join(country_name(c) for c in country_codes(sc.cell(rec, COUNTRIES_COLUMN)))
    if source == "study":
        return one_line(sc.cell(rec, STUDY_COLUMN))
    if source == "participants":
        f = fields_of(sc, rec, "")
        return f["participants"] if f["confirmed"] else ""
    if source.startswith(OWN_PREFIX):
        return long_text(sc.cell(rec, source))
    return ""


def start_value(sc: Screening, rec: str, c: dict) -> str:
    """The value a field that starts from a Sift column takes on a record, as its type holds it: a Number
    field's a whole number or none, a Text field's one line, or none for a field that starts from none."""
    if not c.get("from"):
        return ""
    value = sift_value(sc, rec, c["from"])
    if c["type"] == "number":
        return value if re.fullmatch(r"\d+", value) else ""
    return one_line(value) if c["type"] == "text" else value


def field_value(sc: Screening, rec: str, c: dict) -> tuple[str, bool]:
    """A field's value on a record and whether it is Sift's: his own cell when it holds anything, else for
    a field that starts from a Sift column that column's value, shown until he changes it."""
    own = sc.cell(rec, c["key"]) if c["key"] in sc.col else ""
    if own.strip() or not c.get("from"):
        return own, False
    value = start_value(sc, rec, c)
    return value, bool(value)


def multi_parts(value) -> list[str]:
    """The choices a Several choices cell holds, parted by a semicolon, each once."""
    return list(dict.fromkeys(one_line(p) for p in str(value or "").split(";") if one_line(p)))


def passages_of(value) -> list[dict]:
    """The passages a Passages cell holds, a JSON list of `page` and `text`, each with words, and none from
    anything else."""
    try:
        data = json.loads(value) if str(value or "").strip().startswith("[") else []
    except ValueError:
        return []
    out = []
    for p in data if isinstance(data, list) else []:
        if isinstance(p, dict) and long_text(p.get("text")):
            out.append({"page": one_line(p.get("page"))[:PAGE_MAX], "text": long_text(p.get("text"))[:PASSAGE_MAX]})
    return out


def holds_value(c: dict, value: str, wanted) -> bool:
    """Whether a choice, yes or no, or several choices field holds one of the values another field is
    shown for. Not reported holds none of them."""
    if not value.strip() or value == NOT_REPORTED:
        return False
    parts = multi_parts(value) if c["type"] == "multi" else [one_line(value)]
    return any(p in wanted for p in parts)


def shown_fields(sc: Screening, rec: str, fields: list) -> list[dict]:
    """The fields of the form shown on a record, in its order: each with no condition, and each shown for
    values of another field when that field is shown and holds one of them. A field whose condition names
    a field no longer there, or of a type that holds no choice, is shown, and a hidden field keeps its
    value."""
    by = {c["key"]: c for c in fields}
    held: dict[str, bool] = {}

    def shown(c: dict, seen: frozenset) -> bool:
        if c["key"] in held:
            return held[c["key"]]
        w = c.get("when")
        ctl = by.get(w["key"]) if w else None
        ok = True
        if ctl is not None and ctl["type"] in CONDITION_TYPES and ctl["key"] not in seen and ctl is not c:
            ok = shown(ctl, seen | {c["key"]}) and holds_value(ctl, field_value(sc, rec, ctl)[0], set(w["values"]))
        held[c["key"]] = ok
        return ok

    return [c for c in fields if shown(c, frozenset())]


def filled(c: dict, value: str) -> bool:
    """Whether a field holds a value, Not reported among them, a Passages field at least one passage."""
    if value == NOT_REPORTED:
        return True
    if c["type"] == "passages":
        return bool(passages_of(value))
    if c["type"] == "multi":
        return bool(multi_parts(value))
    return bool(value.strip())


def form_state(sc: Screening, rec: str, fields: list, own: list | None = None) -> dict:
    """A record's form as the screen and the reading tools give it: `shown`, the keys of the fields shown on
    it, `sift`, each field, or each column of his of `own` when given, that starts from a Sift column with
    that column's value, which it shows while his own cell is empty, and `done`, whether every field shown holds a value or Not reported, never on a
    form with no field."""
    shown = shown_fields(sc, rec, fields)
    starts = {c["key"]: start_value(sc, rec, c) for c in (own if own is not None else fields) if c.get("from")}
    return {"shown": [c["key"] for c in shown], "sift": {k: v for k, v in starts.items() if v},
            "done": bool(shown) and all(filled(c, field_value(sc, rec, c)[0]) for c in shown)}


def own_cell(sc: Screening, rec: str, c: dict, value) -> str:
    """The cell a change to a field of his writes, the value checked by its type: one line of text, long
    text, a whole number, one of its choices, yes or no, several of its choices joined by a semicolon in
    their order, or passages, each its words and its page, as a JSON list. Not reported is taken on a field
    that offers it. The value the cell holds already always stands, so a choice taken out of the list is
    kept until he changes it."""
    was = sc.cell(rec, c["key"]) if c["key"] in sc.col else ""
    kind = c["type"]
    if kind == "passages":
        given = value if isinstance(value, list) else []
        if isinstance(value, str):
            given = passages_of(value) if value.strip().startswith("[") else value
        if isinstance(given, str):
            if one_line(given).lower() == NOT_REPORTED and (c["not_reported"] or was == NOT_REPORTED):
                return NOT_REPORTED
            if one_line(given):
                raise SiftError(sift_words.t("sift_server.takes_passages_each_its_words", name=c['name']))
            given = []
        kept = []
        for p in given:
            if not isinstance(p, dict):
                raise SiftError(sift_words.t("sift_server.takes_passages_each_its_words", name=c['name']))
            text, page = long_text(p.get("text")), one_line(p.get("page"))
            if len(text) > PASSAGE_MAX or len(page) > PAGE_MAX:
                raise SiftError(sift_words.t("sift_server.a_passage_is_at_most", passage_max=PASSAGE_MAX, page_max=PAGE_MAX))
            if text:
                kept.append({"page": page, "text": text})
        return json.dumps(kept, ensure_ascii=False) if kept else ""
    if kind == "multi":
        parts = [one_line(p) for p in value] if isinstance(value, (list, tuple)) else multi_parts(value)
        parts = [p for p in dict.fromkeys(parts) if p]
        if [p.lower() for p in parts] == [NOT_REPORTED] and (c["not_reported"] or was == NOT_REPORTED):
            return NOT_REPORTED
        kept = multi_parts(was)
        for p in parts:
            if p not in c["options"] and p not in kept:
                raise SiftError(sift_words.t("sift_server.is_not_one_of_the_3", p=p, name=c['name']))
        return "; ".join([o for o in c["options"] if o in parts] + [p for p in parts if p not in c["options"]])
    text = long_text(value) if kind == "long" else one_line(cell_text(value) if isinstance(value, (list, tuple)) else value)
    if text == (long_text(was) if kind == "long" else one_line(was)):
        return was
    if text.lower() == NOT_REPORTED and c["not_reported"]:
        return NOT_REPORTED
    if kind == "choice" and text and text not in c["options"]:
        raise SiftError(sift_words.t("sift_server.is_not_one_of_the", text=text, name=c['name']))
    if kind == "yesno":
        if text and text.lower() not in YES_NO:
            raise SiftError(sift_words.t("sift_server.is_yes_or_no_or", name=c['name']))
        return text.lower()
    if kind == "number":
        text = text.replace(",", "")
        if text and (not text.isdigit() or int(text) > NUMBER_MAX):
            raise SiftError(sift_words.t("sift_server.is_a_whole_number_or", name=c['name']))
        return str(int(text)) if text else ""
    return text


def read_settings(folder) -> dict:
    """`sift.json` beside the CSV as it stands, every key it holds, or an empty record when it is not
    there or cannot be read."""
    try:
        data = json.loads((Path(folder) / SETTINGS_NAME).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}
    return data if isinstance(data, dict) else {}


def write_settings(folder, data: dict) -> None:
    """`sift.json` written whole through a temporary file, every key it holds kept, the AI switch and
    the prompt among them. The caller holds the lock."""
    write_atomic(Path(folder) / SETTINGS_NAME, json.dumps(data, indent=2, ensure_ascii=False) + "\n")


def numbers_of(folder, sc: Screening, data: dict | None = None) -> dict[str, int]:
    """Each record's number, a plain whole number from 1: the one sift.json keeps for it, and for a
    record with none the next after the highest ever given, those new taken in rec_id order, E2
    before E10. A number is never given twice, and never again once its record has gone."""
    data = read_settings(folder) if data is None else data
    kept = data.get(NUMBERS_KEY) if isinstance(data.get(NUMBERS_KEY), dict) else {}
    good = {str(rec): n for rec, n in kept.items() if isinstance(n, int) and not isinstance(n, bool) and n >= 1}
    out: dict[str, int] = {}
    taken: set[int] = set()
    for rec in sc.ids:
        n = good.get(rec)
        if n is not None and n not in taken:
            out[rec] = n
            taken.add(n)
    top = max(list(good.values()) + [0])
    for rec in sorted((r for r in sc.ids if r not in out), key=natural):
        top += 1
        out[rec] = top
    return out


def keep_numbers(folder, wait: float | None = 1.0) -> bool:
    """The numbers of records that have none yet written into sift.json under the lock, every other
    key it holds kept and every number given before kept with it, the numbers of records gone among
    them. Opening a screening calls it. Left as it is while another writer holds the lock or the
    folder takes no write. The answer is whether it wrote."""
    try:
        with locks.held(lock_path(folder), wait):
            sc = load(folder)
            data = read_settings(folder)
            kept = data.get(NUMBERS_KEY) if isinstance(data.get(NUMBERS_KEY), dict) else {}
            now = numbers_of(folder, sc, data)
            fresh = {rec: n for rec, n in now.items() if kept.get(rec) != n}
            if not fresh:
                return False
            data[NUMBERS_KEY] = dict(kept, **fresh)
            write_settings(folder, data)
            return True
    except WorkbookError as exc:
        if exc.code != "busy":
            raise
    except OSError:
        pass
    return False


def extra_columns(sc: Screening) -> list[str]:
    """The review's columns the table can show beyond its own, those the record's head does not
    name and no decision, proposal or column of his, each as `csv:` and its name, and not the language,
    which is the table's own Language (14 October)."""
    known = (set(SHOWN) | set(PROPOSAL_COLUMNS) | set(DECISION_COLUMNS) | set(AI_PROPOSAL_COLUMNS)
             | {ZOTERO_COLUMN, LANGUAGE_COLUMN})
    return [EXTRA + name for name in sc.header if name not in known and not is_own(name)]


def range_keys(own) -> set[str]:
    """The columns a slider filters: the year, the count of citations, the participants and the
    rating, and each column of his of the Number type (13 October)."""
    return set(RANGE_COLUMNS) | {c["key"] for c in own or [] if c.get("type") == "number"}


def kept_filters(filters, find, keys, ranges=RANGE_COLUMNS) -> tuple[dict, dict]:
    """The table's filters and find boxes as sift.json keeps them, each for a column of `keys`, the
    columns the table has: a slider's column, one of `ranges`, the year, the participants, the rating
    or a Number column of his, its two ends, whole numbers or null, and `none`, any other column the
    values ticked in its group, each once, and each find box's words on one line. A filter that holds
    nothing, one on a column the table no longer has and anything of another shape are let go. Which
    values a group offers is the page's to say (`sfKeptRead` in sift.js), which lets go a tick that
    names a choice no record now carries."""
    out, words = {}, {}
    end = lambda v: v if isinstance(v, int) and not isinstance(v, bool) else None
    for key, f in (filters.items() if isinstance(filters, dict) else []):
        if key not in keys and not TERM_KEY.fullmatch(str(key)):
            continue
        if key in ranges and isinstance(f, dict):
            held = {"from": end(f.get("from")), "to": end(f.get("to")), "none": f.get("none") is True}
            if held["from"] is not None or held["to"] is not None or held["none"]:
                out[key] = held
        elif key not in ranges and isinstance(f, list):
            ticks = list(dict.fromkeys(v for v in f if isinstance(v, str) and v.strip() and len(v) <= 500))
            if ticks:
                out[key] = ticks[:FILTER_MAX]
    for key, typed in (find.items() if isinstance(find, dict) else []):
        if (key in keys or TERM_KEY.fullmatch(str(key))) and key not in ranges and isinstance(typed, str) and typed.strip():
            words[key] = " ".join(typed.split())[:FILTER_MAX]
    return out, words


def table_settings(folder, sc: Screening | None = None) -> dict:
    """The table as sift.json keeps it for this screening: `view`, record or table, `columns`, every
    column the table can show in his order, each `key` and `shown`, those he has not placed after
    them in their first order, `own`, the columns he added, `filters` and `find`, the filters and
    the find boxes' words as he left them (see `kept_filters`), `sidebar`, the filters' sidebar's
    width as he dragged it, or None, and `flow`, the PRISMA flow's sidebar's the same way. A column of the table's own added since he placed his goes after
    the one before it in the first order, and columns placed before the first columns of 12 October,
    `first` short of FIRST, show neither the abstract nor the DOI. A key sift.json names that the
    screening no longer has is passed over."""
    sc = sc if sc is not None else load(folder)
    held = read_settings(folder).get("table")
    held = held if isinstance(held, dict) else {}
    own = own_columns(held, sc)
    first = list(TABLE_COLUMNS) + [(key, False) for key in extra_columns(sc)] + [(c["key"], False) for c in own]
    there = {key for key, _ in first}
    columns, seen = [], set()
    before = held.get("first") != FIRST
    for c in held.get("columns") if isinstance(held.get("columns"), list) else []:
        key = str(c.get("key") or "") if isinstance(c, dict) else ""
        if key in there and key not in seen:
            columns.append({"key": key, "shown": c.get("shown") is True and not (before and key in FIRST_OFF)})
            seen.add(key)
    order = [key for key, _ in TABLE_COLUMNS]
    for key, shown in first:
        if key in seen:
            continue
        at = len(columns)
        if key in order:
            here = [c["key"] for c in columns]
            before = [k for k in order[:order.index(key)] if k in here]
            at = here.index(before[-1]) + 1 if before else 0
        columns.insert(at, {"key": key, "shown": shown})
        seen.add(key)
    view = held.get("view") if held.get("view") in VIEWS else "record"
    filters, find = kept_filters(held.get("filters"), held.get("find"), seen | set(STAGE_FILTERS), range_keys(own))
    return {"view": view, "columns": columns, "own": own, "filters": filters, "find": find,
            "sidebar": sidebar_width(held.get("sidebar")), "flow": sidebar_width(held.get("flow"), FLOW_MIN, FLOW_MAX),
            "defaults": default_columns(sc, own), "sections": sections_of(held, own)}


def default_columns(sc: Screening, own: list) -> list:
    """The table's columns as they first stand, which Set columns' Reset to default puts back (12
    October): the app's own in `TABLE_COLUMNS` order, each shown or hidden as there, the CSV's other
    columns hidden after them, and his own columns at the end, shown when they show on the screening's
    table and hidden when they are the form's alone, as the form's fields are offered at first."""
    return ([{"key": key, "shown": shown} for key, shown in TABLE_COLUMNS]
            + [{"key": key, "shown": False} for key in extra_columns(sc)]
            + [{"key": c["key"], "shown": on_table(c)} for c in own])


def sidebar_width(value, low: int = SIDEBAR_MIN, high: int = SIDEBAR_MAX) -> int | None:
    """A sidebar's width as sift.json keeps it, a whole number of pixels within its limits, the
    filters' unless others are given, or None for anything else."""
    if not isinstance(value, (int, float)) or isinstance(value, bool):
        return None
    return int(max(low, min(high, round(value))))


def sidebar_widths(value) -> dict:
    """The sidebars' widths a view names, as sift.json keeps them, `sidebar` the filters' and `flow`
    the PRISMA flow's (12 October). A number alone is the filters' width, as it was before, and a
    record names either or both, `filters` and `flow`. Anything else is refused in one line."""
    given = value if isinstance(value, dict) else {"filters": value}
    out = {}
    for name, key, low, high in (("filters", "sidebar", SIDEBAR_MIN, SIDEBAR_MAX), ("flow", "flow", FLOW_MIN, FLOW_MAX)):
        if name in given:
            out[key] = sidebar_width(given[name], low, high)
    if not out or None in out.values() or set(given) - {"filters", "flow"}:
        raise SiftError(sift_words.t("sift_server.the_sidebar_s_width_is"))
    return out


def save_view(folder, view=None, columns=None, filters=None, find=None, wait: float | None = None,
              sidebar=None) -> dict:
    """The table's view, record or table, its columns shown and their order, its filters and its find
    boxes' words, and the sidebars' widths, any of them, written to sift.json under the lock,
    every other key it holds kept. `columns` is a list of `key` and `shown` and may name the columns in
    any order, those it leaves out kept after them, and marks them placed under the first columns of
    now, `first`. `filters` and `find` each replace what was kept, as `kept_filters` takes them, and an
    empty one, as Clear all leaves it, takes it away. `sidebar` is the filters' width, or a record of
    the filters' and the flow's (see `sidebar_widths`), each kept within its limits."""
    if view is not None and view not in VIEWS:
        raise SiftError(sift_words.t("sift_server.the_view_is_record_or"))
    if filters is not None and not isinstance(filters, dict):
        raise SiftError(sift_words.t("sift_server.the_filters_are_a_record"))
    if find is not None and not isinstance(find, dict):
        raise SiftError(sift_words.t("sift_server.the_find_boxes_words_are"))
    widths = sidebar_widths(sidebar) if sidebar is not None else {}
    with locks.held(lock_path(folder), wait):
        sc = load(folder)
        data = read_settings(folder)
        held = data.get("table") if isinstance(data.get("table"), dict) else {}
        now = table_settings(folder, sc)
        if view is not None:
            held["view"] = view
        if columns is not None:
            if not isinstance(columns, list):
                raise SiftError(sift_words.t("sift_server.the_columns_are_a_list"))
            known = {c["key"] for c in now["columns"]}
            given = []
            for c in columns:
                key = str(c.get("key") or "") if isinstance(c, dict) else ""
                if key not in known:
                    raise SiftError(sift_words.t("sift_server.the_table_has_no_column", column=key or sift_words.t("sift_server.none_named")))
                if key not in [g["key"] for g in given]:
                    given.append({"key": key, "shown": c.get("shown") is True})
            named = {g["key"] for g in given}
            held["columns"] = given + [c for c in now["columns"] if c["key"] not in named]
            held["first"] = FIRST
        held.update(widths)
        if filters is not None or find is not None:
            keys = {c["key"] for c in now["columns"]} | set(STAGE_FILTERS)
            cleaned = kept_filters(filters if filters is not None else now["filters"],
                                   find if find is not None else now["find"], keys, range_keys(now["own"]))
            for name, value in zip(("filters", "find"), cleaned):
                if value:
                    held[name] = value
                else:
                    held.pop(name, None)
        held.setdefault("own", [kept_entry(c) for c in now["own"]])
        data["table"] = held
        write_settings(folder, data)
        return table_settings(folder, sc)


def field_cells(sc: Screening, rec: str, field, value, table: dict) -> tuple[str, dict]:
    """The column a field names and the cells a change to it writes, the value checked: a rating 1
    to 5 or none, participants a whole number, nought among them, or none, which the screen says is
    unknown, with `participants_confirmed` set, notes, a
    digest or a critique as long text, and a column of his as one line, a choice one of its choices
    and a Number column's a whole number, nought among them, or none (13 October), and by the types of
    the form of 13 October, later, as `own_cell` checks them. A field that is none of these, a review
    column among them, is refused."""
    name = str(field or "").strip()
    if name == "rating":
        text = str(value if value is not None else "").strip()
        if text in ("", "0"):
            return name, {"rating": ""}
        if not text.isdigit() or not 1 <= int(text) <= RATING_MAX:
            raise SiftError(sift_words.t("sift_server.a_rating_is_1_to", rating_max=RATING_MAX))
        return name, {"rating": str(int(text))}
    if name == "participants":
        text = str(value if value is not None else "").strip().replace(",", "")
        if text and (not text.isdigit() or not 0 <= int(text) <= GUESS_MAX * 10):
            raise SiftError(sift_words.t("sift_server.participants_is_a_whole_number"))
        return name, {"participants": str(int(text)) if text else "", "participants_confirmed": CONFIRMED}
    if name in ("notes", "digest", "critique"):
        return name, {name: long_text(value)}
    mine = {c["key"]: c for c in table["own"]}
    if name in mine:
        return name, {name: own_cell(sc, rec, mine[name], value)}
    raise SiftError(sift_words.t("sift_server.is_not_a_field_of", name=name or sift_words.t("sift_server.none_named")))


def set_field(folder, rec_id, field, value, tool: str = TOOL, wait: float | None = None) -> dict:
    """One of his own fields on a record, under the lock: one line added to the log, `act` `field`,
    with the field, its old value and its new, then the CSV written whole. Participants records the
    guess on the screen when he confirmed, and sets `participants_confirmed`. A change that changes
    nothing writes nothing. The answer is what every act answers."""
    with locks.held(lock_path(folder), wait):
        sc = load(folder)
        entries = read_log(folder)
        rec = str(rec_id or "").strip()
        if rec not in sc.at:
            raise SiftError(sift_words.t("sift_server.there_is_no_record_in", rec=rec or sift_words.t("sift_server.none_named"), csv_name=CSV_NAME))
        name, cells = field_cells(sc, rec, field, value, table_settings(folder, sc))
        if all(sc.cell(rec, k) == v for k, v in cells.items()):
            return dict(answer(sc, entries, rec), changed=False)
        entry = {"n": next_n(folder), "at": now_iso(), "act": "field", "rec_id": rec, "field": name,
                 "was": sc.cell(rec, name), "value": cells[name], "tool": tool}
        if name == "participants":
            fields = fields_of(sc, rec)
            entry["guess"] = fields["guess"]
            entry["was_confirmed"] = fields["confirmed"]
        append(folder, entry)
        set_cells(sc, rec, cells)
        write_atomic(csv_path(folder), csv_text(sc))
        return dict(answer(sc, entries, rec), changed=True)


# ------------------------------------------------------------- his key excerpts

def excerpts_of(value) -> list[dict]:
    """A record's key excerpts from its `excerpts` cell, in the order he made them, each its `stage`, `ta` or
    `ft`, its `text`, the words of its pieces joined with an ellipsis, and its `pieces`, each `in` the title
    or the abstract with its `start` and `end` in that text as the screen shows it, plain. A cell that is not
    the JSON Sift writes reads as none, and an excerpt that is not whole is passed over."""
    try:
        items = json.loads(str(value or "").strip() or "[]")
    except ValueError:
        return []
    whole = lambda n: isinstance(n, int) and not isinstance(n, bool)
    out = []
    for item in items if isinstance(items, list) else []:
        if not isinstance(item, dict) or item.get("stage") not in STAGES:
            continue
        pieces = [{"in": p["in"], "start": p["start"], "end": p["end"]} for p in item.get("pieces") or []
                  if isinstance(p, dict) and p.get("in") in EXCERPT_PLACES and whole(p.get("start")) and whole(p.get("end"))
                  and 0 <= p["start"] < p["end"]]
        text = " ".join(str(item.get("text") or "").split())
        if pieces and text:
            out.append({"stage": item["stage"], "text": text, "pieces": pieces})
    return out


def excerpts_cell(items: list[dict]) -> str:
    """Key excerpts as their cell: JSON in ASCII alone, every other character written as its escape, so a
    reading or a saving of the CSV in Excel in another encoding never changes it, and empty with none."""
    return json.dumps(items, ensure_ascii=True, separators=(",", ":")) if items else ""


def excerpts_text(value) -> str:
    """Key excerpts as text, for an export: each in quotation marks with the stage it was made at in
    brackets after it, one a line."""
    return "\n".join(f'"{e["text"]}" ({STAGE_WORDS[e["stage"]]})' for e in excerpts_of(value))


def excerpt_pieces(sc: Screening, rec: str, pieces) -> tuple[list[dict], str]:
    """The pieces of a new key excerpt checked against the record's title and abstract as the screen shows
    them, and its words. Each piece is in the title or the abstract, within it and holding a word, the
    title's before the abstract's and each after the one before it, as the screen's `quote.js` leaves them,
    and the words are each piece's, its spaces run together, joined with an ellipsis. Refused in one line
    when they are not."""
    if not isinstance(pieces, list) or not pieces or len(pieces) > EXCERPT_PIECES:
        raise SiftError(sift_words.t("sift_server.a_key_excerpt_is_1", excerpt_pieces=EXCERPT_PIECES))
    texts = {"title": plain(sc.cell(rec, "title")), "abstract": plain(sc.cell(rec, "abstract"))}
    whole = lambda n: isinstance(n, int) and not isinstance(n, bool)
    out, words, last = [], [], (0, 0)
    for p in pieces:
        p = p if isinstance(p, dict) else {}
        where, start, end = p.get("in"), p.get("start"), p.get("end")
        if where not in EXCERPT_PLACES or not whole(start) or not whole(end):
            raise SiftError(sift_words.t("sift_server.a_piece_of_a_key"))
        text = texts[where]
        if not 0 <= start < end <= len(text) or not text[start:end].strip():
            raise SiftError(sift_words.t("sift_server.a_piece_of_a_key"))
        if (EXCERPT_PLACES.index(where), start) < last:
            raise SiftError(sift_words.t("sift_server.the_pieces_of_a_key"))
        out.append({"in": where, "start": start, "end": end})
        words.append(" ".join(text[start:end].split()))
        last = (EXCERPT_PLACES.index(where), end)
    return out, EXCERPT_JOIN.join(words)


def excerpt(folder, act, rec_id, stage=None, pieces=None, at=None, text=None, tool: str = TOOL,
            wait: float | None = None) -> dict:
    """One of his key excerpts on a record, under the lock, from the screen alone (14 October): `add` keeps
    the pieces as one excerpt made at `stage`, after the record's others, and `remove` takes out the one at
    `at`, `text` its words as the screen shows them, so a list that changed under it refuses. One line in
    the log, `act` `excerpt`, with `field` `excerpts`, `change` add or remove, the `excerpt` and the cell's
    `was` and `value`, and no stage of its own, since the excerpt carries its own, then the CSV written whole,
    as a change to his fields is. Undo takes it back as it takes back a decision (see `undo_excerpt`). No
    command and no tool calls it, his excerpts being his alone. The answer is what every act answers."""
    with locks.held(lock_path(folder), wait):
        sc = load(folder)
        entries = read_log(folder)
        rec = str(rec_id or "").strip()
        if rec not in sc.at:
            raise SiftError(sift_words.t("sift_server.there_is_no_record_in", rec=rec or sift_words.t("sift_server.none_named"), csv_name=CSV_NAME))
        was = sc.cell(rec, EXCERPTS_COLUMN)
        items = excerpts_of(was)
        if act == "add":
            rec, stage = checked(sc, states(entries), rec, stage)
            kept, words = excerpt_pieces(sc, rec, pieces)
            item = {"stage": stage, "text": words, "pieces": kept}
            items.append(item)
        elif act == "remove":
            i = at if isinstance(at, int) and not isinstance(at, bool) else -1
            if not 0 <= i < len(items) or (text is not None and items[i]["text"] != " ".join(str(text).split())):
                raise SiftError(sift_words.t("sift_server.that_key_excerpt_is_no"))
            item = items.pop(i)
        else:
            raise SiftError(sift_words.t("sift_server.a_key_excerpt_is_added"))
        value = excerpts_cell(items)
        if len(value) > EXCERPT_MAX:
            raise SiftError(sift_words.t("sift_server.the_record_holds_as_many"))
        entry = {"n": next_n(folder), "at": now_iso(), "act": EXCERPT_ACT, "rec_id": rec, "field": EXCERPTS_COLUMN,
                 "change": act, "excerpt": item, "was": was, "value": value, "tool": tool}
        append(folder, entry)
        set_cells(sc, rec, {EXCERPTS_COLUMN: value})
        write_atomic(csv_path(folder), csv_text(sc))
        return dict(answer(sc, entries, rec), changed=True)


def slug(name: str) -> str:
    """A column's name as its column in the CSV after `col_`, lower case, letters and numbers joined
    by underscores, Method of analysis as method_of_analysis."""
    return "_".join(re.findall(r"[0-9a-z]+", str(name or "").lower()))


def choices_of(options) -> list[str]:
    """A choice list's choices, each one line, each once, in his order, from a list or lines of text."""
    items = options.split("\n") if isinstance(options, str) else options if isinstance(options, list) else []
    out = []
    for item in items:
        text = one_line(item)
        if text and text not in out:
            out.append(text)
    return out


def drop_column(sc: Screening, name: str) -> None:
    i = sc.col[name]
    del sc.header[i]
    for row in sc.rows:
        if i < len(row):
            del row[i]
    sc.col = {n: k for k, n in enumerate(sc.header)}


def column(folder, act, key=None, name=None, kind=None, options=None, tool: str = TOOL, wait: float | None = None) -> dict:
    """A column of his own, under the lock: `add` with a name, a type and a choice's choices, `change` its
    name or its choices, and `remove`. Each is one line of the log, `act` `column`, and the CSV and
    sift.json written whole. A new column is `col_` and its name, added after the last column and shown in
    the table. A new name renames its column in the CSV while its key is the one its name gave it, and a
    key he set in Set up the form stays (13 October, later). A removal drops the column from the CSV, its
    values kept in the log line, and a field shown for its values, or starting from it, is shown always
    and starts from nothing. The review's columns are never touched. The answer is the table's
    settings, the column's key and whether it changed."""
    act = str(act or "").strip()
    if act not in ("add", "change", "remove"):
        raise SiftError(sift_words.t("sift_server.a_column_is_added_changed"))
    if act == "add":
        kind = kind if kind in COLUMN_TYPES else "text"
        return form_field(folder, None, {"name": name, "type": kind, "options": options, "where": "table",
                                         "not_reported": False}, tool=tool, wait=wait, said="column")
    if act == "change":
        spec = {"name": name} if name is not None else {}
        if options is not None:
            spec["options"] = options
        return form_field(folder, key, spec, tool=tool, wait=wait, said="column")
    with locks.held(lock_path(folder), wait):
        sc = load(folder)
        data = read_settings(folder)
        held = data.get("table") if isinstance(data.get("table"), dict) else {}
        now = table_settings(folder, sc)
        own = [dict(c) for c in now["own"]]
        mine = {c["key"]: c for c in own}
        key = str(key or "").strip()
        if key not in mine:
            raise SiftError(sift_words.t("sift_server.there_is_no_column_of", column=key or sift_words.t("sift_server.none_named")))
        c = mine[key]
        values = {rec: sc.cell(rec, key) for rec in sc.ids if sc.cell(rec, key)}
        if key in sc.col:
            drop_column(sc, key)
        own = [o for o in own if o["key"] != key]
        for o in own:
            if o["when"] and o["when"]["key"] == key:
                o["when"] = None
            if o["from"] == key:
                o["from"] = ""
        entry = {"n": next_n(folder), "at": now_iso(), "act": "column", "change": "remove", "column": key,
                 "name": c["name"], "type": c["type"], "options": c["options"], "values": values, "tool": tool}
        append(folder, entry)
        write_atomic(csv_path(folder), csv_text(sc))
        keep_own(folder, data, held, own, [o for o in now["columns"] if o["key"] != key], now["sections"], gone=key)
        return dict(table=table_settings(folder, load(folder)), key=key, changed=True)


def keep_own(folder, data: dict, held: dict, own: list, columns: list, sections: list, gone: str = "",
             moved: tuple = ()) -> None:
    """His columns, the table's columns and the form's sections written to sift.json, the caller holding
    the lock, his columns in the form's order. A filter kept on a column follows its new key, `moved`, the
    old and the new, and goes with it when it is removed, `gone`."""
    held["own"] = [kept_entry(c) for c in form_order(own, sections)]
    held["columns"] = columns
    held["first"] = FIRST
    held["sections"] = list(sections)
    for kept in (held.get(k) for k in ("filters", "find")):
        if not isinstance(kept, dict):
            continue
        if gone and gone in kept:
            kept.pop(gone)
        if moved and moved[0] in kept:
            kept[moved[1]] = kept.pop(moved[0])
    data["table"] = held
    write_settings(folder, data)


def condition_of(c: dict, raw, by: dict) -> dict | None:
    """The field and the values a field is shown for, checked: none, or a field of the form that holds a
    choice, a yes or no or several choices, never the field itself, and one or more of its values, refused
    in one line otherwise and when the two would each wait on the other."""
    if not raw:
        return None
    if not isinstance(raw, dict):
        raise SiftError(sift_words.t("sift_server.shown_when_names_a_field"))
    ctl = by.get(own_key(raw.get("key")))
    if ctl is None or ctl["key"] == c["key"]:
        raise SiftError(sift_words.t("sift_server.shown_when_names_another_field"))
    if ctl["type"] not in CONDITION_TYPES:
        raise SiftError(sift_words.t("sift_server.holds_no_choice_so_no", name=ctl['name']))
    given = raw.get("values")
    values = [one_line(v) for v in (given if isinstance(given, list) else [given]) if one_line(v)]
    values = list(dict.fromkeys(values))
    if not values:
        raise SiftError(sift_words.t("sift_server.pick_at_least_one_value", name=ctl['name']))
    known = list(YES_NO) if ctl["type"] == "yesno" else ctl["options"]
    gone = [v for v in values if v not in known]
    if gone:
        raise SiftError(sift_words.t("sift_server.is_not_one_of_the_2", gone=gone[0], name=ctl['name']))
    at, seen = ctl, {c["key"]}
    while at is not None and at.get("when"):
        if at["key"] in seen:
            break
        seen.add(at["key"])
        at = by.get(at["when"]["key"])
        if at is not None and at["key"] == c["key"]:
            raise SiftError(sift_words.t("sift_server.is_shown_for_the_values", name=ctl['name'], name2=c['name']))
    return {"key": ctl["key"], "values": values}


def form_field(folder, key=None, spec=None, tool: str = TOOL, wait: float | None = None, said: str = "field") -> dict:
    """One column of his set whole, under the lock (13 October, later), for Set up the form and the
    coordinator's call: with no `key` a new one, else the one of that key, `spec` naming any of `name`,
    `key`, `type`, `options`, `where`, `not_reported`, `when`, `section` and `from`, each left out kept as it
    stands, or for a new one its default, a field of the form offering Not reported. `key` is the field's
    key with or without `col_`, letters, digits and underscores, unique, by default the one its name
    gives, which follows a new name until he sets one of his own. A new key renames its column in the CSV,
    its values with it, and a field shown for it or starting from it follows. A new field is added after
    the CSV's last column, shown on the table when it shows there and offered hidden on the form's.
    A choice taken out of a list leaves the values that hold it as they are. One line of the log, `act`
    `column`, `change` `add` or `change`, with the field whole and on a change `was`, as it stood, and
    `to` on a new key. A change that changes nothing writes nothing. The answer is the table's settings,
    the field's key and whether it changed."""
    spec = spec if isinstance(spec, dict) else {}
    with locks.held(lock_path(folder), wait):
        sc = load(folder)
        data = read_settings(folder)
        held = data.get("table") if isinstance(data.get("table"), dict) else {}
        now = table_settings(folder, sc)
        own = [dict(c) for c in now["own"]]
        by = {c["key"]: c for c in own}
        sections = list(now["sections"])
        columns = [dict(o) for o in now["columns"]]
        adding = key is None
        if adding:
            c = own_entry({"where": "form", "not_reported": True}, "")
            c["name"] = ""
            was = None
        else:
            given = str(key or "").strip()
            key = own_key(given)
            if key not in by:
                raise SiftError(sift_words.t("sift_server.there_is_no_column_of_2", given=given or sift_words.t("sift_server.none_named")))
            c = by[key]
            was = kept_entry(c)
        label = one_line(spec["name"]) if spec.get("name") is not None else c["name"]
        what = "column" if said == "column" else "field"
        if not slug(label):
            raise SiftError(sift_words.t("sift_server.a_s_name_needs_a", what=what))
        if len(label) > NAME_MAX:
            raise SiftError(sift_words.t("sift_server.a_s_name_is_at", what=what, name_max=NAME_MAX))
        kind = spec.get("type", c["type"]) if spec.get("type") is not None else c["type"]
        if kind not in COLUMN_TYPES:
            raise SiftError(sift_words.t("sift_server.the_type_is_text_choice"))
        choices = choices_of(spec["options"]) if spec.get("options") is not None else c["options"]
        choices = choices if kind in CHOICE_TYPES else []
        if kind in CHOICE_TYPES and not choices:
            raise SiftError(sift_words.t("sift_server.a_choice_list_needs_at"))
        if kind == "multi" and any(";" in o for o in choices):
            raise SiftError(sift_words.t("sift_server.a_choice_of_several_choices"))
        where = spec.get("where", c["where"]) if spec.get("where") is not None else c["where"]
        if where not in WHERE:
            raise SiftError(sift_words.t("sift_server.a_field_shows_on_the"))
        nr = spec["not_reported"] is True if "not_reported" in spec else c["not_reported"]
        section = one_line(spec["section"])[:NAME_MAX] if spec.get("section") is not None else c["section"]
        source = str(spec["from"] or "") if "from" in spec else c["from"]
        if source:
            source = source if source in SIFT_SOURCES else own_key(source)
            if not (source in SIFT_SOURCES or source in by) or source == c["key"]:
                raise SiftError(sift_words.t("sift_server.is_not_a_sift_column", source=source))
            if kind not in FROM_TYPES:
                raise SiftError(sift_words.t("sift_server.only_a_text_long_text"))
            if source in by and by[source]["type"] == "passages":
                raise SiftError(sift_words.t("sift_server.a_field_cannot_start_from"))
        # the key: his when he gives one, else the name's, which a new name moves while the key is the old name's
        if spec.get("key") is not None and str(spec.get("key")).strip():
            new = own_key(spec["key"])
            if not KEY_SHAPE.fullmatch(plain_key(new)):
                raise SiftError(sift_words.t("sift_server.a_key_is_letters_digits"))
        elif adding or (label != c["name"] and c["key"] == OWN_PREFIX + slug(c["name"])):
            new = OWN_PREFIX + slug(label)[:60]
        else:
            new = c["key"]
        if plain_key(new).lower() in FIRST_KEYS and where != "table":
            raise SiftError(sift_words.t("sift_server.the_key_is_the_export", new=plain_key(new)))
        taken = {h.lower() for h in sc.header} | {o["key"].lower() for o in own}
        if new != c["key"] and new.lower() in taken - {c["key"].lower()}:
            other = next((o["name"] for o in own if o["key"].lower() == new.lower()), plain_key(new))
            if spec.get("key") is not None and str(spec.get("key")).strip():
                raise SiftError(sift_words.t("sift_server.the_key_is_s_already", new=plain_key(new), other=other))
            raise SiftError(sift_words.t("sift_server.there_is_a_already", what=what, label=label))
        probe = dict(c, key=new, type=kind, options=choices)
        rest = {o["key"]: o for o in own if o["key"] != c["key"]}
        rest[new] = probe
        when = condition_of(probe, spec["when"], rest) if "when" in spec else c["when"]
        if when and not adding and when["key"] == c["key"]:
            when = None
        # a field that decides when others show stays a field of choices while they wait on it
        waiting = [o["name"] for o in own if o["key"] != c["key"] and o["when"] and o["when"]["key"] == c["key"]]
        if waiting and kind not in CONDITION_TYPES:
            raise SiftError(sift_words.t("sift_server.decides_when_show_so_it", label=label, waiting=and_join(waiting)))
        after = dict(c, key=new, name=label, type=kind, options=choices, where=where, not_reported=nr, when=when,
                     section=section, **{"from": source})
        if not adding and kept_entry(after) == was:
            return dict(table=now, key=c["key"], changed=False)
        entry = {"n": next_n(folder), "at": now_iso(), "act": "column", "change": "add" if adding else "change",
                 "column": c["key"] if not adding else new, **{k: after[k] for k in OWN_KEYS if k != "key"}, "tool": tool}
        if adding:
            own.append(after)
            if new not in sc.col:
                sc.col[new] = len(sc.header)
                sc.header.append(new)
                for row in sc.rows:
                    row.append("")
            columns.append({"key": new, "shown": on_table(after)})
        else:
            entry["was"] = {k: was[k] for k in OWN_KEYS if k != "key"}
            own = [after if o["key"] == c["key"] else o for o in own]
            if new != c["key"]:
                entry["to"] = new
                if c["key"] in sc.col:
                    sc.header[sc.col[c["key"]]] = new
                    sc.col = {n: k for k, n in enumerate(sc.header)}
                columns = [dict(o, key=new) if o["key"] == c["key"] else o for o in columns]
                for o in own:
                    if o["when"] and o["when"]["key"] == c["key"]:
                        o["when"] = dict(o["when"], key=new)
                    if o["from"] == c["key"]:
                        o["from"] = new
            # a field newly on the screening's table shows there
            if not on_table(c) and on_table(after):
                columns = [dict(o, shown=True) if o["key"] == new else o for o in columns]
        if section and section not in sections:
            sections.append(section)
        append(folder, entry)
        write_atomic(csv_path(folder), csv_text(sc))
        keep_own(folder, data, held, own, columns, sections, moved=(c["key"], new) if not adding and new != c["key"] else ())
        return dict(table=table_settings(folder, load(folder)), key=new, changed=True)


def order_form(folder, sections, wait: float | None = None) -> dict:
    """The form's sections and fields in his order, under the lock (13 October, later), for the handles of
    Set up the form and the coordinator's call: `sections` a list of `name` and `fields`, the keys of the
    fields under that heading in order, with or without `col_`, a section of no name holding the fields
    before the first heading. A field named moves to the section it is named under, and one not named
    keeps its section after those named. A section left out goes when no field is in it. Like the table's
    order, it is kept in sift.json and never a line of the log. The answer is the table's settings."""
    if not isinstance(sections, list):
        raise SiftError(sift_words.t("sift_server.the_form_s_order_is"))
    with locks.held(lock_path(folder), wait):
        sc = load(folder)
        data = read_settings(folder)
        held = data.get("table") if isinstance(data.get("table"), dict) else {}
        now = table_settings(folder, sc)
        own = [dict(c) for c in now["own"]]
        by = {c["key"]: c for c in own}
        names, placed = [], []
        for s in sections:
            if not isinstance(s, dict):
                raise SiftError(sift_words.t("sift_server.each_section_is_a_name"))
            name = one_line(s.get("name"))
            if len(name) > NAME_MAX:
                raise SiftError(sift_words.t("sift_server.a_section_s_name_is", name_max=NAME_MAX))
            if name:
                if name in names:
                    raise SiftError(sift_words.t("sift_server.there_is_a_section_already", name=name))
                names.append(name)
            for k in s.get("fields") or []:
                k = own_key(k)
                if k not in by:
                    raise SiftError(sift_words.t("sift_server.there_is_no_field_of", k=plain_key(k) or sift_words.t("sift_server.none_named")))
                if k in placed:
                    raise SiftError(sift_words.t("sift_server.is_named_twice", name=by[k]['name']))
                placed.append(k)
                by[k]["section"] = name
        order = [by[k] for k in placed] + [c for c in own if c["key"] not in placed]
        names += [c["section"] for c in order if c["section"] and c["section"] not in names]
        names = list(dict.fromkeys(names))
        keep_own(folder, data, held, order, now["columns"], names)
        return {"table": table_settings(folder, load(folder))}


def benchmark_ids(sc: Screening) -> list[str]:
    """The records of a screening that are the review's benchmark papers, as its plan's newest version
    names them, by DOI, else for a record with none by the title the plan keeps, in the CSV's order."""
    review = review_of(sc.folder)
    if review is None:
        return []
    import sift_search  # here, since it reads this module first
    try:
        last = sift_search.newest(sift_search.read_file(review))
    except WorkbookError:
        return []
    if not last:
        return []
    plan = sift_search.clean_plan(last.get("plan"))
    dois = {sift_search.doi_key(d) for d in plan["benchmark"]}
    titles = {match_title(t) for t in plan["benchmark_titles"].values()} - {""}
    out = []
    for rec in sc.ids:
        doi = sift_search.doi_key(sc.cell(rec, "doi"))
        if (doi and doi in dois) or (not doi and match_title(sc.cell(rec, "title")) in titles):
            out.append(rec)
    return out


def form_round(folder) -> dict:
    """Extract and appraise's records, read without a write: `ids`, the records included at full text, and
    `bench`, the review's benchmark papers whatever their decision, which its filter Benchmark papers
    lists so he can pilot the form on them before any paper is included, with the form itself, its
    `sections` and `fields` as `form_of` gives them (13 October, evening)."""
    sc = load(folder)
    return dict(form_of(folder, sc), ids=included_ids(sc, states(read_log(folder))), bench=benchmark_ids(sc))


def form_cell(c: dict, value: str) -> str:
    """A field's value as the export writes it: Not reported as `not reported`, several choices joined by a
    semicolon and a space, passages each as `p. 4: "its words"` joined by a bar between spaces, the rest as
    the CSV holds it."""
    if value == NOT_REPORTED:
        return NOT_REPORTED
    if c["type"] == "multi":
        return "; ".join(multi_parts(value))
    if c["type"] == "passages":
        return " | ".join((f'p. {p["page"]}: ' if p["page"] else "") + f'"{p["text"]}"' for p in passages_of(value))
    return value


def form_of(folder, sc: Screening | None = None) -> dict:
    """The form as the reading tools and the export take it: its sections in order and its fields, each
    as sift.json keeps it with its plain key."""
    sc = sc if sc is not None else load(folder)
    t = table_settings(folder, sc)
    fields = form_fields(t["own"], t["sections"])
    return {"stage": FORM_STAGE, "sections": t["sections"], "fields": [dict(kept_entry(c), plain_key=plain_key(c["key"]))
                                                                      for c in fields]}


def form_rows(sc: Screening, fields: list, ids: list) -> tuple[list[str], list[list[str]]]:
    """The export's header and its rows: `rec_id` and `study`, then each field of the form under its plain
    key, a field not shown on a record left empty."""
    head = list(FIRST_KEYS) + [plain_key(c["key"]) for c in fields]
    rows = []
    for rec in ids:
        shown = {c["key"] for c in shown_fields(sc, rec, fields)}
        rows.append([rec, one_line(sc.cell(rec, STUDY_COLUMN))]
                    + [form_cell(c, field_value(sc, rec, c)[0]) if c["key"] in shown else "" for c in fields])
    return head, rows


def form_read(folder) -> dict:
    """Extract and appraise to read, never to write, for the command line and MCP: the form, each record
    included at full text with whether it is done and its row as the export writes it, the benchmark
    papers, and how many are done."""
    sc = load(folder)
    form = form_of(folder, sc)
    fields = [c for c in table_settings(folder, sc)["own"] if c["key"] in {f["key"] for f in form["fields"]}]
    fields = [next(c for c in fields if c["key"] == f["key"]) for f in form["fields"]]
    ids = included_ids(sc, states(read_log(folder)))
    head, rows = form_rows(sc, fields, ids)
    records = [{"rec_id": rec, "title": plain(sc.cell(rec, "title")), "done": form_state(sc, rec, fields)["done"],
                "values": dict(zip(head, row))} for rec, row in zip(ids, rows)]
    return dict(form, records=records, columns=head, bench=benchmark_ids(sc), file=FORM_CSV,
                done=sum(1 for r in records if r["done"]))


def export_form(folder, dry_run: bool = False, wait: float | None = None) -> dict:
    """Export the form: `screening.form.csv` beside the CSV, one row per record included at full text, whole
    each time, or with `dry_run` only counted. With no field on the form or no record included nothing is
    written."""
    with locks.held(lock_path(folder), wait):
        got = form_read(folder)
        write = bool(got["fields"]) and bool(got["records"]) and not dry_run
        if write:
            out = io.StringIO(newline="")
            w = csv.writer(out, lineterminator="\n")
            w.writerow(got["columns"])
            w.writerows([[r["values"][k] for k in got["columns"]] for r in got["records"]])
            write_atomic(Path(folder) / FORM_CSV, out.getvalue())
        return {"records": len(got["records"]), "fields": len(got["fields"]), "file": FORM_CSV, "written": write,
                "columns": got["columns"]}


# ------------------------------------------------------- reading for the command line

def rows_of_round(folder, stage="ta", which: str = "undecided") -> dict:
    """A round's records, in the CSV's order, each with its number, its title, year, the searches that
    found it, where it stands at the stage, the proposal shown first, whether it has a PDF, his own
    fields, what the retraction column says, `notices`, and the study he linked it to, to read and
    never to write. `columns` names his own columns."""
    sc = load(folder)
    entries = read_log(folder)
    held = states(entries)
    stage = stage_key(stage)
    numbers = numbers_of(folder, sc)
    out = []
    for rec in listed(sc, entries, stage, which):
        st = state_of(sc, held, rec, stage)
        prop = proposal_of(sc, rec, stage)
        out.append({"rec_id": rec, "n": numbers.get(rec), "title": plain(sc.cell(rec, "title")),
                    "year": sc.cell(rec, "year").strip(),
                    "found": sources_of(sc.cell(rec, "sources")),
                    "decision": st["decision"], "reason": st["reason"], "note": st["note"],
                    "proposal": {k: prop[k] for k in ("decision", "reason", "source")},
                    "pdf": pdf_path(sc.folder, rec) is not None, "fields": fields_of(sc, rec),
                    "notices": notice_kinds(sc.cell(rec, RETRACTION_COLUMN)) or [], "study": one_line(sc.cell(rec, STUDY_COLUMN))})
    return {"stage": STAGE_WORDS[stage], "round": round_key(which), "records": out, "columns": own_said(folder, sc)}


def own_said(folder, sc: Screening) -> list[dict]:
    """His own columns as the reading tools give them, each its column, his name, type and choices, and
    since 13 October, later, where it shows, Not reported, what it is shown for, its section and the Sift
    column it starts from, as sift.json keeps them."""
    return [kept_entry(c) for c in table_settings(folder, sc)["own"]]


def read_lines(folder) -> list[dict]:
    """Every line of the log that is a JSON record, the decisions and notes and the changes to his
    fields and columns alike, oldest first."""
    path = log_path(folder)
    if not path.is_file():
        return []
    out = []
    for line in path.read_text(encoding="utf-8").splitlines():
        try:
            entry = json.loads(line) if line.strip() else None
        except ValueError:
            continue
        if isinstance(entry, dict):
            out.append(entry)
    return out


def history(folder, rec_id) -> dict:
    """One record as the screen draws it, his own fields among it, with every line of the log on it,
    its decisions, notes and changes to his fields, and each link or unlink of a study that moved it,
    oldest first."""
    import sift_second  # here, since it reads this module first
    sc = load(folder)
    entries = read_log(folder)
    rec = str(rec_id or "").strip()
    if rec not in sc.at:
        raise SiftError(sift_words.t("sift_server.there_is_no_record_in", rec=rec or sift_words.t("sift_server.none_named"), csv_name=CSV_NAME))
    # the second screener's decisions he cannot see yet are left out, blind as the screen is
    hidden = sift_second.hidden_lines(folder, sc, entries)
    ex = extras_of(sc)
    return {"record": record_view(sc, states(entries), rec, extras=ex), "columns": own_said(folder, sc),
            "key_works": key_works_view(ex["works"]), "blocks": blocks_view(ex["terms"]),
            "history": [e for e in read_lines(folder) if (str(e.get("rec_id")) == rec or names_record(e, rec))
                        and not (e.get("act") == SECOND_ACT and e.get("n") in hidden)]}


def names_record(entry: dict, rec: str) -> bool:
    """Whether a link or unlink of a study names a record beyond the one it was made on: the record linked
    to, or one it moved."""
    was = entry.get("was") if isinstance(entry.get("was"), dict) else {}
    return entry.get("act") == "study" and (str(entry.get("with") or "") == rec or rec in was)


# ------------------------------------------------------------------ a dropped PDF

def save_pdf(folder, rec_id, data: bytes, replace: bool = False, wait: float | None = None) -> dict:
    """A PDF dropped on the pane, kept as `pdfs/<rec_id>.pdf` beside the CSV for a record the CSV
    holds, through a temporary file and `os.replace`. One already there is replaced only with
    `replace`, and without it the answer says `exists` and nothing is written. Bytes that are not a
    PDF are refused. `prisma.md` is written afresh, since the reports retrieved have moved."""
    if not isinstance(data, (bytes, bytearray)) or bytes(data[:5]) != b"%PDF-":
        raise SiftError(sift_words.t("sift_server.that_file_is_not_a"))
    with locks.held(lock_path(folder), wait):
        sc = load(folder)
        entries = read_log(folder)
        rec = str(rec_id or "")
        if rec not in sc.at:
            raise SiftError(sift_words.t("sift_server.there_is_no_record_in", rec=rec or sift_words.t("sift_server.none_named"), csv_name=CSV_NAME))
        if rec != rec.strip() or rec.startswith(".") or any(c in rec for c in "/\\\x00:"):
            raise SiftError(sift_words.t("sift_server.cannot_name_a_file_so", rec=rec))
        there = pdf_path(folder, rec)
        if there is not None and not replace:
            return dict(answer(sc, entries, rec), exists=True, saved=False)
        base = Path(folder) / PDF_DIR
        base.mkdir(exist_ok=True)
        target = there if there is not None else base / f"{rec}.pdf"
        fd, tmp = tempfile.mkstemp(dir=str(target.parent), prefix=f".{target.name}.", suffix=".tmp")
        try:
            os.chmod(tmp, 0o644)
            with os.fdopen(fd, "wb") as fh:
                fh.write(bytes(data))
                fh.flush()
                os.fsync(fh.fileno())
            os.replace(tmp, target)
        except BaseException:
            try:
                os.unlink(tmp)
            except OSError:
                pass
            raise
        # a PDF of his own in place of one found in an earlier run is his from now on
        forget_found(folder, target.name)
        return dict(settled(sc, entries, rec), exists=there is not None, saved=True)


# ------------------------------------------------------------------ PDFs found in earlier runs

# A PDF belongs to the paper, not the run (12 October). A run's screening takes the PDF of each record
# that has none from the review's earlier runs, the runs beside it under `runs/`, matched by DOI, else
# by title and year when one of the two records has no DOI, as an EBSCO export's records have none.
# A title and year that match two papers in a run, or records of two DOIs, take nothing. Each PDF is a
# plain copy, never over a file there, and `pdfs/.found.json` names each with its size and where it
# came from, so one found this way is never taken for his own work on the screening and a run
# written afresh takes it away (see `sift_search.begun`). No PDF lookup reads that file.
FOUND_NAME = ".found.json"
RUNS_NAME = "runs"
RUN_ORDER = re.compile(r"(\d{4}-\d{2}-\d{2})(?:-(\d{1,4}))?")


def match_doi(value) -> str:
    """A DOI as two records' PDFs are matched by: lower case, with no address, `doi:` or spaces."""
    d = " ".join(str(value or "").split()).lower()
    d = re.sub(r"^(?:https?://)?(?:dx\.)?doi\.org/", "", d)
    d = re.sub(r"^doi:\s*", "", d)
    return d.strip().rstrip(".")


def match_title(value) -> str:
    """A title as two records' PDFs are matched by: its letters and digits alone, in lower case."""
    return re.sub(r"[\W_]+", "", plain(value).lower())


def match_year(value) -> str:
    m = re.search(r"(?<!\d)(1[5-9]\d\d|2\d\d\d)(?!\d)", str(value or ""))
    return m.group(1) if m else ""


def run_order(name: str) -> tuple:
    """A run folder's day and its number that day, as `sift_search.run_parts` reads them."""
    m = RUN_ORDER.fullmatch(name)
    return (m.group(1), int(m.group(2) or 1)) if m else (name, 1)


def found_pdfs(folder) -> dict:
    """The PDFs a screening took from earlier runs, `{name: {"size", "from"}}`, or empty."""
    try:
        data = json.loads((Path(folder) / PDF_DIR / FOUND_NAME).read_text(encoding="utf-8"))
    except (OSError, ValueError, UnicodeDecodeError):
        return {}
    return {k: v for k, v in data.items() if isinstance(v, dict)} if isinstance(data, dict) else {}


def write_found(folder, found: dict) -> None:
    path = Path(folder) / PDF_DIR / FOUND_NAME
    if found:
        write_atomic(path, json.dumps(found, ensure_ascii=False, indent=1) + "\n")
    else:
        path.unlink(missing_ok=True)


def forget_found(folder, name: str) -> None:
    found = found_pdfs(folder)
    if name in found:
        del found[name]
        write_found(folder, found)


def own_pdfs(folder) -> dict:
    """A screening's own PDFs, each name with its size: every file in `pdfs/` but one found in an
    earlier run and unchanged since, which is no work on this screening."""
    base = Path(folder) / PDF_DIR
    if not base.is_dir():
        return {}
    found = found_pdfs(folder)
    out = {}
    for p in base.iterdir():
        if not p.is_file() or p.name.startswith("."):
            continue
        size = p.stat().st_size
        if (found.get(p.name) or {}).get("size") != size:
            out[p.name] = size
    return out


def clear_found(folder) -> None:
    """The PDFs found in earlier runs and unchanged since taken away, before a run is written afresh
    and its records numbered anew. Called only once nothing of his is in the run."""
    base = Path(folder) / PDF_DIR
    for name, said in found_pdfs(folder).items():
        p = base / name
        if p.is_file() and not p.is_symlink() and p.parent.resolve() == base.resolve() and p.stat().st_size == said.get("size"):
            p.unlink()
    (base / FOUND_NAME).unlink(missing_ok=True)


def earlier_runs(folder) -> list[Path]:
    """The review's runs made before the run whose screening `folder` is, those beside it under `runs/`
    that hold a screening and a PDF, newest first, or none for a screening that is not a run's."""
    here = Path(folder).resolve()
    if here.parent.name != RUNS_NAME:
        return []
    mine = run_order(here.name)
    out = []
    for p in here.parent.iterdir():
        if p.name.startswith(".") or not p.is_dir() or run_order(p.name) >= mine:
            continue
        pdfs = p / PDF_DIR
        if pdfs.is_dir() and any(q.suffix.lower() == ".pdf" for q in pdfs.iterdir()) and is_screening(p):
            out.append(p)
    return sorted(out, key=lambda p: run_order(p.name), reverse=True)


def pdf_index(runs: list[Path]) -> tuple[dict, dict]:
    """The earlier runs' records as a PDF is found by: each DOI with the newest run's PDF for it, and
    each title and year with every record of a run that has them, its run, its DOI and its PDF."""
    by_doi: dict[str, Path] = {}
    by_title: dict[tuple, list] = {}
    for run in runs:
        try:
            sc = load(run)
        except (WorkbookError, OSError):
            continue
        for rec in sc.ids:
            doi = match_doi(sc.cell(rec, "doi"))
            pdf = pdf_path(run, rec)
            if doi and pdf is not None and doi not in by_doi:
                by_doi[doi] = pdf
            key = (match_title(sc.cell(rec, "title")), match_year(sc.cell(rec, "year")))
            if key[0] and key[1]:
                by_title.setdefault(key, []).append((run.name, doi, pdf))
    return by_doi, by_title


def pdf_for(sc: Screening, rec: str, by_doi: dict, by_title: dict) -> Path | None:
    """The PDF a record takes from an earlier run: the one of its DOI, else the one of its title and
    year from a record with no DOI or the same, none when a run holds two records of them or they carry
    two DOIs, since that would be a guess."""
    doi = match_doi(sc.cell(rec, "doi"))
    if doi and doi in by_doi:
        return by_doi[doi]
    key = (match_title(sc.cell(rec, "title")), match_year(sc.cell(rec, "year")))
    if not key[0] or not key[1]:
        return None
    held = [c for c in by_title.get(key, []) if not (doi and c[1] and c[1] != doi)]
    runs = [c[0] for c in held]
    if len(runs) != len(set(runs)) or len({c[1] for c in held if c[1]}) > 1:
        return None
    return next((c[2] for c in held if c[2] is not None), None)


def gather_pdfs(folder, wait: float | None = 1.0, held: bool = False) -> int:
    """Each record of a run's screening with no PDF given the one an earlier run of the review holds for
    its paper (see `pdf_for`), a plain copy as `pdfs/<rec_id>.pdf`, never over a file there and never
    anywhere outside `pdfs/`, under the screening's lock, and named in `pdfs/.found.json`. A run calls
    it once its screening is written, and opening a screening calls it, so a PDF added to an earlier
    run later still reaches it. Left as it is while another writer holds the lock or the folder takes
    no write, and the lock is taken only when there is a PDF to take, or not at all when the caller,
    `held`, holds it already, as a run writing its folder does. The answer is how many it took."""
    runs = earlier_runs(folder)
    if not runs:
        return 0
    safe = lambda rec: rec and rec == rec.strip() and not rec.startswith(".") and not any(c in rec for c in "/\\\x00:")
    try:
        sc = load(folder)
        by_doi, by_title = pdf_index(runs)
        if not any(pdf_for(sc, rec, by_doi, by_title) for rec in sc.ids if safe(rec) and pdf_path(folder, rec) is None):
            return 0
        with contextlib.nullcontext() if held else locks.held(lock_path(folder), wait):
            sc = load(folder)
            wanting = [rec for rec in sc.ids if safe(rec) and pdf_path(folder, rec) is None]
            base = Path(folder) / PDF_DIR
            found = found_pdfs(folder)
            taken = 0
            for rec in wanting:
                src = pdf_for(sc, rec, by_doi, by_title)
                if src is None:
                    continue
                base.mkdir(exist_ok=True)
                target = base / f"{rec}.pdf"
                if target.exists() or target.is_symlink() or target.resolve().parent != base.resolve():
                    continue
                fd, tmp = tempfile.mkstemp(dir=str(base), prefix=f".{target.name}.", suffix=".tmp")
                try:
                    os.chmod(tmp, 0o644)
                    with os.fdopen(fd, "wb") as fh:
                        fh.write(src.read_bytes())
                        fh.flush()
                        os.fsync(fh.fileno())
                    os.replace(tmp, target)
                except BaseException:
                    try:
                        os.unlink(tmp)
                    except OSError:
                        pass
                    raise
                found[target.name] = {"size": target.stat().st_size, "from": f"{src.parent.parent.name}/{src.name}"}
                taken += 1
            if taken:
                write_found(folder, found)
            return taken
    except (WorkbookError, OSError):
        return 0
