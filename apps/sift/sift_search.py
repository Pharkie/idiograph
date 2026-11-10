#!/usr/bin/env python3
"""Sift's searches: the plan a review's searches are written from, each database's own string,
registration, the runs, and the records of a run merged into a screening (see `sift.py`).

A review folder is the folder that holds `runs/`. Its plan is `search_plan.json`, every version
kept whole, `{"versions": [{"version", "saved", "registered", "reason", "plan"}]}`. A plan holds the
databases chosen, any others it names, `other`, `other2` and up, each by its name under `others`,
the concept blocks, each a name and its terms, a phrase in double quotes and `*`
for truncation on a single word alone, a plan holding a phrase with truncation neither saved nor run
(14 October, see PHRASE_TRUNCATION), the terms of a block ORed and the blocks ANDed, each block's field scope, title,
abstract and keywords by default, methods sections or full text, which a database may override for
that block, the limits, years from and to and document types, the benchmark, DOIs a run must find,
with the title typed or found from its DOI for each under `benchmark_titles`, the exclusion reasons
in one list, and any database's string edited manually with its reason. No language limit is
written: language is applied at screening, so a search counts every language. Export writes the
newest version, a draft or registered, to `search_plan.md`, the file he registers on OSF or PROSPERO
himself, and Mark as registered freezes the newest version with the time, the registry and its
registration number or link. An edit after that is a draft of the next version, which needs a
reason before it is registered or run. The exclusion reasons live in the review folder's own
`reasons.csv`, which the screen writes as he edits them (see `save_reasons`).

A run writes `runs/<date>/` in the shape a screening reads: `raw_<source>.json` for each database,
the records it gave, `log.csv`, `date,source,interface,query,hits,records_saved,note`, a row a
database for PRISMA-S, `screening.csv`, the records merged and deduplicated by DOI, a version suffix
set aside, and then by title and year, a record with no year by an unambiguous title, an abstract a
database lacks and the authors of a record that names one or none filled from OpenAlex by DOI, with
each record's count of citations and the day it was asked, `cited_by` and `cited_by_date`, in the
same request, its keywords, the fullest list a database gives or else OpenAlex's, in `keywords` after
the screening's own columns, and its language by name in `language` at the end (14 October), and Sift's
own columns of 13 October after the rest, whether the paper was retracted,
corrected or given an expression of concern, from OpenAlex's `is_retracted` and Crossref's `updated-by`
by DOI, its open access, the countries of its authors' institutions, OpenAlex's authors with their IDs,
the days OpenAlex and Crossref were asked and an empty `study` for his links, with each record's
references, Crossref's and OpenAlex's, in `screening.references.json`, `rec_id` R001 up in year and
title order, `reasons.csv`
copied from the review folder's own when there is one, `run.json`, the version it ran and how
each database went, and when the run checked truncation first `dry_run_terms.csv`, the dry run's
table of each truncated term's counts (14 October, see `truncation_check`). A run that brings no records writes no `screening.csv`, so it never stands in
place of the screening the review's Screening step opens. Each record with no PDF takes the one an
earlier run holds for its paper, by DOI or by title and year (see `sift.gather_pdfs`), which never
counts as a screening begun. A database with no API, with no key, or that the
user's own list does not hold by API, is searched on its own site with the string Sift writes, and
its RIS, BibTeX or CSV export, dropped on the screen, is kept as `<source>.ris`, `<source>.bib` or
`<source>.csv` in the run folder and taken in.

Every run is kept. Run always writes a new run folder, a later run that day `runs/<date>-2/`, then
`-3`, never one written before, but for a run a dropped export began that Run has not yet run, of the
same version and with its screening not begun, which Run completes. An export dropped goes to the
newest run of the day, the run still waiting on exports, and is refused when that run's screening
has begun. A run is numbered in the order the runs were made, its number kept in `runs/numbers.json`
from the time a run folder is made, so a run removed by hand moves no other run's number, and the
screens name it by that number and its day, Run 3, 12 October 2026, the command line by its day and
its number that day, 9 October 2026, run 2. The runs stand in the order they were made. A folder of the old shape, one run a
day, reads as it always did. A run of a version not yet registered keeps `draft` in `run.json`, and
the screen and the command line name it as from a draft, not registered.

A later run may follow an earlier run of the same folder, `follows`, the earlier run's folder name. Its
screening then holds every record of the earlier one, with its rec_id, its decisions at both stages
and his own fields, the found-by of both runs where a record is found again, and the later run's
new records after them, deduplicated against the earlier ones by `merge`'s rules and numbered on
from the earlier highest rec_id, undecided. The decisions and his fields arrive through `sift.append`
as lines of their own kind, `carry`, each naming the earlier run's day and log line, after a first
line, `follow`, that names the records carried and those new, and the CSV is written from the log as
Sift always writes it. The earlier run's folder is read and never written, its PDFs copied, its
proposal columns carried as they stand, and the later `log.csv` holds both runs' searches with their
dates, as PRISMA-S asks. `run.json`'s `carried` keeps what the carry wrote, so a folder holding the
carry alone is not a screening begun and an export dropped on it writes it afresh.

The user's own list of databases is kept in `config.json` under `databases`, each with its platform
and whether it goes by API or by export. Every key, Scopus's and Web of Science's, and OpenAlex's
and PubMed's optional ones, is read at run time through `ai_suggest.find_key` by its keychain service,
and saved, removed and said to be saved or not through `ai_suggest`'s own functions, never printed
and never written by this module, and every error and note passes through `scrub` first.
OpenAlex's key goes as `api_key` on every OpenAlex request when one is saved.
The plan file keeps the review's key works beside its versions, `key_works`, never in a version, so an
edit to them never makes a draft (see `save_key_works`).
`IDIOGRAPH_SEARCH_STUB`, a loopback address, sends every request to a stub server and every key to a
keychain held in memory, for a smoke run alone, Crossref's with its host at the head of the path. The standard library, `locks.py`, `sift.py` and
`ai_suggest.py` only. It calls no model.
"""
from __future__ import annotations

import formats
import sift_words
import contextlib
import csv
import hashlib
import io
import json
import os
import re
import tempfile
import time
import unicodedata
import urllib.error
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from datetime import date as Date, datetime
from pathlib import Path

import ai_suggest
import locks
import sift
from ai_suggest import STUB_ENV, STUB_KEYCHAIN, Done, MemoryKeychain, stub_base  # noqa: F401  the family's smoke-run stub
from errors import WorkbookError
from pdftext import norm_doi  # noqa: F401  the family's, a DOI as two records are compared by
# a review's run folders as they are read, the family's since 22 October 2026 (family/screenings.py)
from screenings import RUN_NAME, RUNS_DIR, run_dirs, run_parts, runs_path  # noqa: F401

PLAN_NAME = "search_plan.json"
# the review's own name and question, which New review writes beside the versions
REVIEW_KEYS = ("name", "question")
PLAN_MD = "search_plan.md"
RUN_FILE = "run.json"
LOCK_NAME = "search.lock"
UA = "Idiograph-Sift/1.0 (systematic review search)"
TIMEOUT = 60

SOURCES = ("scopus", "wos", "psycinfo", "cinahl", "pubmed", "epmc", "openalex", "embase", "pqdt", "scholar", "other")
NAMES = {"scopus": "Scopus", "wos": "Web of Science", "psycinfo": "PsycInfo", "cinahl": "CINAHL", "pubmed": "PubMed",
         "epmc": "Europe PMC", "openalex": "OpenAlex", "embase": "Embase", "pqdt": "ProQuest Dissertations & Theses",
         "scholar": "Google Scholar", "other": "Other database"}
KEYLESS = ("pubmed", "epmc", "openalex")
# the databases Sift searches by API, the rest searched on their own sites and taken in by export
APIS = ("scopus", "wos", "pubmed", "epmc", "openalex")
# the key a keyed API cannot run without, read from the keychain, and Scopus's optional institution token
KEYS = {"scopus": "ELSEVIER_API_KEY", "wos": "CLARIVATE_API_KEY"}
TOKENS = {"scopus": "ELSEVIER_INSTTOKEN"}
# OpenAlex's own key, optional: sent as `api_key` on every OpenAlex request when one is saved
OPENALEX_KEY = "OPENALEX_API_KEY"
# each API's key fields in Settings, by the keychain service each is stored under, the optional ones
# raising a database's limits or naming an institution
KEY_FIELDS = {
    "scopus": ({"service": "ELSEVIER_API_KEY", "label": "API key", "optional": False},
               {"service": "ELSEVIER_INSTTOKEN", "label": "Institution token", "optional": True}),
    "wos": ({"service": "CLARIVATE_API_KEY", "label": "API key", "optional": False},),
    "openalex": ({"service": "OPENALEX_API_KEY", "label": "API key", "optional": True},),
    "pubmed": ({"service": "NCBI_API_KEY", "label": "API key", "optional": True},),
    "epmc": (),
}
SERVICES = tuple(f["service"] for fields in KEY_FIELDS.values() for f in fields)
# the keys of Sift's other services, kept, removed and said to be saved through the same functions as
# the databases' keys: Zotero's, for a sync (see `sift_zotero.py`)
OTHER_SERVICES = ("ZOTERO_API_KEY",)
# the platforms PsycInfo and CINAHL are searched on, EBSCO the default, each with its own syntax
PLATFORMED = ("psycinfo", "cinahl")
PLATFORMS = ("ebsco", "ovid", "proquest")
PLATFORM_NAMES = {"ebsco": "EBSCO", "ovid": "Ovid", "proquest": "ProQuest"}
# the platforms each vendor offers the database on now, which Settings and the plan screen offer. CINAHL
# is on EBSCO alone, so a plan or a list that names it on Ovid or ProQuest still reads, its string
# written with a note that says so
OFFERED = {"psycinfo": ("ebsco", "ovid", "proquest"), "cinahl": ("ebsco",)}
PLATFORM_HOSTS = {"ebsco": "EBSCOhost", "ovid": "Ovid", "proquest": "ProQuest"}
FULL_NAMES = {"psycinfo": "APA PsycInfo", "cinahl": "CINAHL"}
DATABASES_KEY = "databases"
ENDPOINTS = {"pubmed": "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/",
             "epmc": "https://www.ebi.ac.uk/europepmc/webservices/rest/search",
             "openalex": "https://api.openalex.org/works",
             "scopus": "https://api.elsevier.com/content/search/scopus",
             "wos": "https://api.clarivate.com/apis/wos-starter/v1/documents"}
# Crossref's works, asked by DOI for a paper's notices of retraction, correction or concern and its
# references, in the polite pool with the email Sift's settings keep (13 October)
CROSSREF = "https://api.crossref.org/works"
INTERFACE = {"scopus": "Scopus Search API (api.elsevier.com)",
             "wos": "Web of Science Core Collection, Starter API (api.clarivate.com)",
             "pubmed": "PubMed via NCBI E-utilities",
             "epmc": "Europe PMC REST API",
             "openalex": "OpenAlex API, title and abstract (api.openalex.org)"}
EXPORTED = {"scopus": "Scopus, Advanced search, export", "wos": "Web of Science Core Collection, Advanced Search, export",
            "embase": "Embase on Embase.com, export", "pqdt": "ProQuest Dissertations & Theses Global on ProQuest, export",
            "scholar": "Google Scholar, Publish or Perish CSV export"}
# each database's own search page, which the screen opens in a new tab for a database searched there,
# and the platform's for PsycInfo and CINAHL. A link he follows, never a request the app makes
SITES = {"scopus": "https://www.scopus.com/search/form.uri?display=advanced",
         "wos": "https://www.webofscience.com/wos/woscc/advanced-search",
         "pubmed": "https://pubmed.ncbi.nlm.nih.gov/advanced/", "epmc": "https://europepmc.org/advancesearch",
         "openalex": "https://openalex.org/", "embase": "https://www.embase.com/",
         "pqdt": "https://www.proquest.com/pqdtglobal/advanced", "scholar": "https://scholar.google.com/"}
PLATFORM_SITES = {"ebsco": "https://search.ebscohost.com/", "ovid": "https://ovidsp.ovid.com/",
                  "proquest": "https://www.proquest.com/"}
# a database the plan names, beyond those Sift knows: `other` for the first, then `other2` up, each
# named in the plan's `others`, searched on its own site and taken in by export
OTHER = "other"
OTHER_ID = re.compile(r"other(?:[2-9]|1\d|20)?")
PAGE = {"pubmed": 500, "epmc": 1000, "openalex": 200, "scopus": 25, "wos": 50}
PAUSE = {"pubmed": 0.4, "epmc": 0.3, "openalex": 0.2, "scopus": 0.3, "wos": 1.1}
PUBMED_MOST = 10000
SCOPUS_MOST = 5000

SCOPES = ("tak", "methods", "fulltext")
SCOPE_WORDS = {"tak": "title, abstract and keywords", "methods": "methods sections", "fulltext": "full text"}
# the same as a line for a person says them, in the run's language, where SCOPE_WORDS stays the plan file's
SCOPE_SAID = {"tak": lambda: sift_words.t("sift_server.search.scope.tak"), "methods": lambda: sift_words.t("sift_server.search.scope.methods"),
              "fulltext": lambda: sift_words.t("sift_server.search.scope.fulltext")}


def scope_said(scope: str) -> str:
    """A field scope as a line for a person says it, title, abstract and keywords."""
    return SCOPE_SAID[scope]() if scope in SCOPE_SAID else str(scope)
# the field scopes each database can search, any other falling back to the first, title, abstract and
# keywords, or for Google Scholar, which has no fields, the whole text. PsycInfo and CINAHL search full
# text on EBSCO alone
HAS = {"scopus": ("tak",), "wos": ("tak",), "psycinfo": ("tak", "fulltext"), "cinahl": ("tak", "fulltext"),
       "pubmed": ("tak",), "epmc": ("tak", "methods", "fulltext"), "openalex": ("tak", "fulltext"), "embase": ("tak",),
       "pqdt": ("tak",), "scholar": ("fulltext",), "other": ("tak", "methods", "fulltext")}
SCHOLAR_MOST = 256
TYPES = ("article", "review", "chapter", "conference", "dissertation", "preprint")
TYPE_WORDS = {"article": "journal article", "review": "review", "chapter": "book chapter",
              "conference": "conference paper", "dissertation": "dissertation", "preprint": "preprint"}
# each document type as a database writes it, where the database has it
TYPE_CODES = {
    "scopus": {"article": "DOCTYPE(ar)", "review": "DOCTYPE(re)", "chapter": "DOCTYPE(ch)", "conference": "DOCTYPE(cp)"},
    "wos": {"article": "Article", "review": "Review", "chapter": '"Book Chapter"', "conference": '"Proceedings Paper"'},
    "pubmed": {"article": '"journal article"[pt]', "review": "review[pt]", "preprint": "preprint[pt]"},
    "epmc": {"article": 'PUB_TYPE:"journal article"', "review": 'PUB_TYPE:"review"', "preprint": "SRC:PPR"},
    "openalex": {"article": "article", "review": "review", "chapter": "book-chapter", "dissertation": "dissertation",
                 "preprint": "preprint"},
}
# the far ends of a range of years where a database's help gives no open end of its own: PubMed's
# 3000, which NLM's own filters end a range with, and 1000 at the low side. Web of Science and Europe
# PMC document no open end, so a range of theirs ends at the year of the run, put in when the string
# is sent, and Web of Science's begins at 1900, the first year of its own timespan
YEAR_LOW, YEAR_HIGH = 1000, 3000
WOS_FIRST = 1900
RUN_YEAR = ("wos", "epmc")
# the day as the suite stands it, `Date.today` when None, which the year of the run is read from
CLOCK = None
COLUMNS = ["rec_id", "title", "authors", "year", "journal", "doi", "pub_type", "sources", "abstract_from", "abstract",
           sift.CITED_COLUMN, sift.CITED_DATE,
           "proposed_decision", "proposed_reason", "grounds", "decision", "reason", "ft_proposed_decision",
           "ft_proposed_reason", "ft_grounds", "ft_decision", "ft_reason", sift.KEYWORDS_COLUMN]
# the cells of a merged record a run writes into its screening as they stand, its keywords among them since
# 14 October, after the screening's own columns
WRITTEN = ("rec_id", "title", "authors", "year", "journal", "doi", "pub_type", "abstract_from", "abstract",
           sift.CITED_COLUMN, sift.CITED_DATE, sift.KEYWORDS_COLUMN, "url") + sift.FILLED[2:] + (sift.LANGUAGE_COLUMN,)
# Sift's own columns of 13 October, after every column a run wrote before them and the link: what OpenAlex
# and Crossref say, and his study, empty until he links a record
OWN_AFTER = list(sift.FILLED[2:]) + [sift.STUDY_COLUMN]
LOG_COLUMNS = ["date", "source", "interface", "query", "hits", "records_saved", "note"]
RIS_TYPES = {"JOUR": "journal article", "JFULL": "journal article", "BOOK": "book", "CHAP": "book chapter",
             "CONF": "conference paper", "CPAPER": "conference paper", "THES": "dissertation", "RPRT": "report",
             "GEN": "generic", "ELEC": "web page"}
WORKED = re.compile(r"[a-z0-9]", re.I)
OPERATOR = re.compile(r"(?:^|\s)(?:AND|OR|NOT|NEAR/\d+|W/\d+|PRE/\d+)(?:\s|$)")
SYNTAX = re.compile(r"[()\[\]{}=:,;|<>\"]")
DOI = re.compile(r"^10\.\d{3,9}/\S+$")


class SearchError(WorkbookError):
    """A plan that cannot be saved, registered or run, or a run that cannot go ahead, in plain lines, said
    one after another when there are several (14 October), never as a list of them. A request that failed
    says in plain words which database and what happened, its status in brackets, and keeps beside that
    `detail`, the status, the address and the start of the answer, for the run's own log alone, and
    `status`, the status, 0 for none (17 October, later; `code` until 31 October, when `code` became the
    refusal's own, errors.CODES)."""

    def __init__(self, *args, detail: str = "", status: int | None = None):
        super().__init__(*args)
        self.detail, self.status = detail, status

    def __str__(self) -> str:
        return " ".join(str(a) for a in self.args) if len(self.args) > 1 else super().__str__()


def logged(e: Exception) -> str:
    """What the run's own log keeps of a failure: a request's full detail, or the line itself."""
    return getattr(e, "detail", "") or str(e)


# This module's words for a person, read in the run's language when said: inside the module through `_w`,
# from others and the checks as the module's names (`__getattr__`)
SAID = {
    "STALE_PLAN": lambda: sift_words.t("sift_server.search.stale"),
    "PHRASE_TRUNCATION": lambda: sift_words.t("sift_server.search.phrase_truncation"),
    "NO_TERM": lambda: sift_words.t("sift_server.search.no_term"),
    "PROQUEST_STAR": lambda: sift_words.t("sift_server.search.proquest_star"),
}


def _w(name: str) -> str:
    return SAID[name]()


def __getattr__(name: str) -> str:
    """This module's words other modules and the checks name, read in the run's language."""
    if name in SAID:
        return SAID[name]()
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


class StalePlan(SearchError):
    """A save of the plan or the reasons from a page that read the plan in another version than the file
    holds now, another window's save among them, refused with nothing written (19 October). `now` is the
    version the file holds, which Overwrite sends back."""

    def __init__(self, now: str):
        super().__init__(_w("STALE_PLAN"))
        self.now = now


def plan_version(data: dict) -> str:
    """The plan's version as a page reads it: the newest version's number and a hash of it as the file
    holds it, so two saves within one second still differ."""
    last = newest(data)
    if not last:
        return ""
    held = hashlib.sha1(json.dumps(last, sort_keys=True, ensure_ascii=False).encode("utf-8")).hexdigest()[:12]
    return f"{last.get('version')}:{held}"


def refuse_stale(data: dict, seen) -> None:
    """StalePlan when `seen`, the version a page last read, is not the plan's now. None is never stale."""
    said = str(seen or "").strip()
    if said and said != plan_version(data):
        raise StalePlan(plan_version(data))


class Unsaved(SearchError):
    """A plan the save refused (14 October), its lines the terms that stand in the way, with `view`, what the
    screen draws of the plan it was sent: its problems and each block's own."""

    def __init__(self, lines: list[str], view: dict):
        super().__init__(*lines)
        self.lines, self.view = list(lines), view


# ------------------------------------------------------------------ small things

def now_iso() -> str:
    return datetime.now().astimezone().isoformat(timespec="seconds")


def today() -> Date:
    """Today, or the day the suite stands in its place through CLOCK."""
    return CLOCK() if CLOCK else Date.today()


def this_year() -> int:
    """The year of the run, which a range of years with no open end of its own ends at."""
    return today().year


def day_said(iso) -> str:
    """A date as a line says it: 8 October 2026."""
    try:
        at = datetime.fromisoformat(str(iso))
    except (TypeError, ValueError):
        try:
            at = datetime.combine(Date.fromisoformat(str(iso)), datetime.min.time())
        except (TypeError, ValueError):
            return str(iso or "")
    return f"{at.day} {at:%B %Y}"


def one_line(text) -> str:
    return " ".join(str(text or "").split())


def plural(n: int, one: str, many: str | None = None) -> str:
    return f"{n} {one if n == 1 else (many or one + 's')}"


def doi_key(value) -> str:
    """A DOI as the merge compares it: normalised, with a trailing version suffix, `.v1` or `.v2` as
    figshare gives one, taken off, so two versions of one item are one record."""
    return re.sub(r"\.v\d+$", "", norm_doi(value))


def norm_title(value) -> str:
    """A title as two records are compared by: its letters and digits alone, in lower case."""
    return re.sub(r"[\W_]+", "", sift.plain(value).lower())


def year_of(value) -> str:
    """The year of a date field: a year standing as a word, as in 2019, 2019-08-03, 2019/08/03 or a RIS
    2019///, or the head of a compact date, 20190803 or 201908, as EBSCO writes one."""
    s = str(value or "")
    m = (re.search(r"\b(1[5-9]\d\d|2\d\d\d)\b", s)
         or re.search(r"(?<!\d)(1[5-9]\d\d|2\d\d\d)(?:0[1-9]|1[0-2])(?:0[1-9]|[12]\d|3[01])?(?!\d)", s))
    return m.group(1) if m else ""


def write_text(path: Path, text: str) -> None:
    """A file written whole through a temporary file beside it and `os.replace`."""
    sift.write_atomic(Path(path), text)


def is_other(source) -> bool:
    """Whether a source is a database the plan names, `other`, `other2` and up."""
    return isinstance(source, str) and bool(OTHER_ID.fullmatch(source))


def kind_of(source: str) -> str:
    """The database a source writes and searches as: itself, or `other` for each one the plan names."""
    return OTHER if is_other(source) else source


def known(source) -> bool:
    return source in SOURCES or is_other(source)


def other_rank(source: str) -> int:
    return 1 if source == OTHER else int(source[len(OTHER):])


def in_order(sources) -> list[str]:
    """Sources in Sift's own order, the databases the plan names after them in the order they were added."""
    held = {s for s in sources if known(s)}
    return [s for s in SOURCES if s != OTHER and s in held] + sorted((s for s in held if is_other(s)), key=other_rank)


def name_of(source: str, plan: dict | None = None) -> str:
    """A database by the name the screen, `log.csv` and `sources` give it, one the plan names by that
    name, which a plan from before several kept as `other_name`."""
    if is_other(source) and plan:
        named = one_line((plan.get("others") or {}).get(source))
        if not named and source == OTHER:
            named = one_line(plan.get("other_name"))
        if named:
            return named
    return NAMES.get(kind_of(source), source)


def platform_of(source: str, plan: dict | None = None) -> str:
    """The platform the plan searches PsycInfo or CINAHL on, EBSCO unless it names another, and
    empty for a database with one platform."""
    if source not in PLATFORMED:
        return ""
    held = (plan or {}).get("platforms") or {}
    return held.get(source) if held.get(source) in PLATFORMS else "ebsco"


def label_of(source: str, plan: dict | None = None) -> str:
    """A database as a note names it, with its platform where it has several: PsycInfo on Ovid."""
    p = platform_of(source, plan)
    return f"{name_of(source, plan)} on {PLATFORM_NAMES[p]}" if p else name_of(source, plan)


# ------------------------------------------------------------------ the terms

# Truncation on single words only (Adam, 14 October): Scopus and PubMed honour an asterisk inside a quoted
# phrase, Europe PMC passes over it in title, abstract and keywords and finds nothing for it in methods, and
# OpenAlex takes no truncation, so a string holding one runs and its hits come back with no sign of what was
# missed. A phrase holding an asterisk or a question mark cannot stand, quoted or of several words, and a plan
# holding one is neither saved nor run.


def parse_term(raw) -> tuple[dict | None, str]:
    """One term as typed, `allotment*` or `"community garden"`, as `{"text", "phrase"}`, or the one
    line saying why it cannot stand. A term of several words is a phrase, quoted or not, and a phrase
    holds no truncation (see PHRASE_TRUNCATION)."""
    s = one_line(raw)
    if not s:
        return None, ""
    quoted = len(s) >= 2 and s[0] == '"' and s[-1] == '"'
    text = one_line(s[1:-1]) if quoted else s
    if not text or not WORKED.search(text):
        return None, sift_words.t("sift_server.search.holds_no_word", s=s)
    if SYNTAX.search(text):
        return None, sift_words.t("sift_server.search.holds_a_mark_a_database", s=s)
    if not quoted and OPERATOR.search(text):
        return None, sift_words.t("sift_server.search.holds_an_operator_put_each", s=s)
    if (quoted or " " in text) and re.search(r"[*?]", text):
        return None, sift_words.t("sift_server.search.term_said", term=s, said=_w("PHRASE_TRUNCATION"))
    if re.search(r"\*\w|(?:^|\s)\*", text):
        return None, sift_words.t("sift_server.search.an_asterisk_ends_a_word", s=s)
    return {"text": text, "phrase": quoted or " " in text}, ""


def term_as_typed(t: dict) -> str:
    return f'"{t["text"]}"' if t["phrase"] else t["text"]


def terms_of(block: dict) -> list[dict]:
    out = []
    for raw in block.get("terms") or []:
        t, _ = parse_term(raw)
        if t is not None:
            out.append(t)
    return out


# ------------------------------------------------------------------- the plan

def blank_plan() -> dict:
    return {"databases": [], "others": {}, "platforms": {}, "blocks": [], "years": {"from": None, "to": None},
            "types": [], "reasons": [], "benchmark": [], "benchmark_titles": {}, "overrides": {}}


# The exclusion reasons, one list (12 October, later): each a short code and its meaning, offered at
# both stages of screening, a reason optional on a reject at title and abstract and required at full
# text (see `sift.reason_problem`). The review folder's `reasons.csv` holds them, which the app writes
# as he edits them, `code,meaning`, a row a reason in his order. A file of before, `stage,code,meaning`
# with each row at `ta` or `ft`, is still read, each code offered at its own stage, until he edits it.
REASON_STAGES = ("ta", "ft")
REASONS_HEAD = ("code", "meaning")
CODE_MAX = 12
MEANING_MAX = 200


def reasons_of(raw) -> list[dict]:
    """Exclusion reasons as one list in their order, each `{code, meaning}`: from a list of those, or of
    lines that each start with the code, "E1 Not about lived experience", a colon, comma or dash after
    the code let go, or from a plan of before, which held a list for each stage, title and abstract
    first. A line with no code, or a code held already, is let go, and a code is kept to `CODE_MAX`
    letters and a meaning to `MEANING_MAX`."""
    if isinstance(raw, dict):
        items = []
        for stage in REASON_STAGES:
            held = raw.get(stage) or []
            items += held.splitlines() if isinstance(held, str) else (held if isinstance(held, list) else [])
    else:
        items = raw.splitlines() if isinstance(raw, str) else (raw if isinstance(raw, list) else [])
    rows = []
    for item in items:
        if isinstance(item, dict):
            code, meaning = one_line(item.get("code")), one_line(item.get("meaning"))
        else:
            parts = one_line(item).split(" ", 1)
            code = parts[0].rstrip(":,.-") if parts[0] else ""
            meaning = re.sub(r"^[\s:,\-]+", "", parts[1]) if len(parts) > 1 else ""
        code = code[:CODE_MAX]
        if code and all(r["code"].lower() != code.lower() for r in rows):
            rows.append({"code": code, "meaning": meaning[:MEANING_MAX]})
    return rows


def file_reasons(folder) -> dict | None:
    """The review folder's own `reasons.csv` as one list, `reasons`, in the file's order, a file of
    before's title and abstract codes first, with `staged`, whether it is a file of before that offers
    each code at its own stage, and `said`, one line when it cannot be read, or None when the folder
    holds none. When it is there it is the one place the reasons live: the plan takes them from it as
    it is saved and registered, so `search_plan.md` and the file never differ. Only reads."""
    path = Path(folder) / sift.REASONS_NAME
    if not path.is_file():
        return None
    held = sift.reasons(folder)
    return {"reasons": reasons_of({stage: held[stage] for stage in REASON_STAGES}),
            "staged": held["ta"] != held["ft"], "said": held["said"]}


def with_file_reasons(folder, plan: dict) -> dict:
    """A plan with the review folder's own reasons in place of its own when the folder holds
    `reasons.csv`, and as it is when it holds none."""
    held = file_reasons(folder)
    return plan if held is None else dict(plan, reasons=held["reasons"])


def reasons_text(rows: list[dict]) -> str:
    """Reasons as `reasons.csv` holds them in its one-list form, `code,meaning`, a row a reason in their
    order, the header alone when there are none."""
    out = io.StringIO(newline="")
    writer = csv.writer(out, lineterminator="\n")
    writer.writerow(list(REASONS_HEAD))
    writer.writerows([r["code"], r["meaning"]] for r in rows)
    return out.getvalue()


def reasons_csv(plan: dict) -> str:
    """A plan's exclusion reasons as a run's `reasons.csv` holds them when the review folder holds none,
    in the one-list form, or empty when the plan holds none."""
    return reasons_text(plan["reasons"]) if plan["reasons"] else ""


def benchmark_of(raw) -> tuple[list[str], dict]:
    """The benchmark's DOIs, each once, and the titles typed after them. A line is a DOI with its title
    after it, or several DOIs, and a plan from before titles a list of DOIs alone."""
    lines = raw.splitlines() if isinstance(raw, str) else [str(x) for x in raw if isinstance(x, (str, int, float))]
    dois, titles = [], {}
    for line in lines:
        rest, found = re.sub(r"^[\s,]+", "", str(line)).rstrip(), []
        while rest:
            m = re.match(r"([^\s,]+)[\s,]*", rest)
            d = norm_doi(m.group(1))
            if found and not DOI.match(d):
                break
            found.append(d)
            rest = rest[m.end():]
            if not DOI.match(d):
                break
        for d in found:
            if d and d not in dois:
                dois.append(d)
        if len(found) == 1 and found[0] and one_line(rest):
            titles[found[0]] = one_line(rest)[:240]
    return dois, {d: titles[d] for d in dois if titles.get(d)}


def as_year(value):
    s = one_line(value)
    if not s:
        return None
    try:
        return int(s)
    except ValueError:
        return s


def clean_plan(raw) -> dict:
    """A plan as the file keeps it, from what the screen or a file sent: the databases in Sift's own
    order, those the plan names after them with their names, the platform each chosen PsycInfo or
    CINAHL is searched on, EBSCO unless another is named, each block's terms one to a line with a
    phrase in quotes, its scope and the databases' own scopes for it, the years, the document types,
    the exclusion reasons in one list (`reasons_of`), the benchmark's DOIs with the title typed or
    found for each, and the strings edited manually. Nothing here
    refuses: `problems` says what stands in the way of registering or running."""
    raw = raw if isinstance(raw, dict) else {}
    chosen = {str(d) for d in (raw.get("databases") or []) if isinstance(d, str)}
    plan = blank_plan()
    plan["databases"] = in_order(chosen)
    named = raw.get("others") if isinstance(raw.get("others"), dict) else {}
    if OTHER not in named and one_line(raw.get("other_name")):
        named = dict(named, other=raw.get("other_name"))
    plan["others"] = {s: one_line(named.get(s))[:60] for s in plan["databases"] if is_other(s) and one_line(named.get(s))}
    held = raw.get("platforms") if isinstance(raw.get("platforms"), dict) else {}
    plan["platforms"] = {s: (held.get(s) if held.get(s) in PLATFORMS else "ebsco")
                         for s in PLATFORMED if s in plan["databases"]}
    for b in raw.get("blocks") or []:
        if not isinstance(b, dict):
            continue
        terms = b.get("terms") or []
        if isinstance(terms, str):
            terms = terms.splitlines()
        kept = []
        for t in terms:
            parsed, said = parse_term(t)
            line = term_as_typed(parsed) if parsed else one_line(t)
            if line and line not in kept:
                kept.append(line)
        scope = b.get("scope") if b.get("scope") in SCOPES else "tak"
        own = b.get("scopes") if isinstance(b.get("scopes"), dict) else {}
        scopes = {s: own[s] for s in in_order(own) if own.get(s) in SCOPES and own.get(s) != scope}
        plan["blocks"].append({"name": one_line(b.get("name"))[:80], "terms": kept, "scope": scope, "scopes": scopes})
    years = raw.get("years") if isinstance(raw.get("years"), dict) else {}
    plan["years"] = {"from": as_year(years.get("from")), "to": as_year(years.get("to"))}
    wanted = {str(t) for t in (raw.get("types") or []) if isinstance(t, str)}
    plan["types"] = [t for t in TYPES if t in wanted]
    plan["reasons"] = reasons_of(raw.get("reasons"))
    dois, typed = benchmark_of(raw.get("benchmark") or [])
    kept = raw.get("benchmark_titles") if isinstance(raw.get("benchmark_titles"), dict) else {}
    plan["benchmark"] = dois
    plan["benchmark_titles"] = {d: typed.get(d) or one_line(kept.get(d))[:240] for d in dois
                                if typed.get(d) or one_line(kept.get(d))}
    over = raw.get("overrides") if isinstance(raw.get("overrides"), dict) else {}
    for s in in_order(over):
        o = over.get(s)
        if isinstance(o, dict) and str(o.get("query") or "").strip():
            plan["overrides"][s] = {"query": str(o["query"]).strip(), "reason": one_line(o.get("reason"))}
    return plan


def block_name(plan: dict, i: int) -> str:
    return plan["blocks"][i]["name"] or f"Block {i + 1}"


def term_problems(block: dict) -> list[str]:
    """What stands in the way in one block's terms, a line for each term that cannot stand."""
    out = []
    for t in block["terms"]:
        _, said = parse_term(t)
        if said:
            out.append(said)
    return out


def block_problems(plan: dict) -> list[list[str]]:
    """Each block's own problems, in the blocks' order, which the screen shows under the block as well."""
    return [term_problems(b) for b in plan["blocks"]]




def terms_problems(plan: dict) -> list[str]:
    """What stands in the way in the search terms as a whole, no block holding a term, which the screen
    shows under Search terms as well as under Register, beside its cause (17 October, later)."""
    return [] if any(b["terms"] for b in plan["blocks"]) else [_w("NO_TERM")]


def problems(plan: dict) -> list[str]:
    """What stands in the way of registering or running the plan, one line each, empty when nothing does."""
    out = []
    if not plan["databases"]:
        out.append(sift_words.t("sift_server.search.choose_at_least_one_database"))
    out += terms_problems(plan)
    for i, b in enumerate(plan["blocks"]):
        out += [f"{block_name(plan, i)}: {said}" for said in term_problems(b)]
    a, b = plan["years"]["from"], plan["years"]["to"]
    for label, y in (("from", a), ("to", b)):
        if y is not None and (not isinstance(y, int) or not 1800 <= y <= 2100):
            out.append(sift_words.t("sift_server.search.the_year_is_a_year", label=label))
    if isinstance(a, int) and isinstance(b, int) and a > b:
        out.append(sift_words.t("sift_server.search.the_year_from_comes_after"))
    for d in plan["benchmark"]:
        if not DOI.match(d):
            out.append(sift_words.t("sift_server.search.is_not_a_doi", d=d))
    for s, o in plan["overrides"].items():
        if s in plan["databases"] and not o["reason"]:
            out.append(sift_words.t("sift_server.search.s_edited_string_needs_its", s=name_of(s, plan)))
    if any(is_other(s) and not plan["others"].get(s) for s in plan["databases"]):
        out.append(sift_words.t("sift_server.search.name_the_other_database"))
    return out


def phrase_problems(plan: dict) -> list[str]:
    """The plan's phrases that hold truncation (14 October), each as `problems` names it, by its block, which
    keep the plan from being saved as well as from being registered or run."""
    return [f"{block_name(plan, i)}: {said}" for i, b in enumerate(plan["blocks"]) for said in term_problems(b)
            if said.endswith(_w("PHRASE_TRUNCATION"))]


# ---------------------------------------------------------------- the writers

def scope_for(block: dict, source: str) -> str:
    return block["scopes"].get(source) or block["scope"]


def has(source: str, plan: dict | None = None) -> tuple:
    """The field scopes a database searches on the platform the plan names for it."""
    if platform_of(source, plan) in ("ovid", "proquest"):
        return ("tak",)
    return HAS[kind_of(source)]


def used_scope(block: dict, source: str, plan: dict | None = None) -> str:
    """The scope a database searches a block in: the one asked for where it has it, else its first,
    title, abstract and keywords, or the whole text for a database with no fields."""
    scope = scope_for(block, source)
    own = has(source, plan)
    return scope if scope in own else own[0]


# the databases whose search of title, abstract and keywords reaches no keyword or index field (14 October):
# OpenAlex's title and abstract search, and CINAHL on Ovid or ProQuest (see FIELD_NOTES). Every other
# database's reaches one Sift never holds whole, Scopus's author keywords and index terms, Web of Science's
# Keywords Plus, PubMed's keywords within its title and abstract field, Europe PMC's KW, PsycInfo's KW on
# EBSCO, its Key Concepts on Ovid and IF on ProQuest, CINAHL's subject fields on EBSCO, Embase's kw and the
# IF of ProQuest Dissertations & Theses
NO_KEYWORDS = (("openalex", ""), ("cinahl", "ovid"), ("cinahl", "proquest"))


def beyond_text(block: dict, source: str, plan: dict | None = None) -> str:
    """Where a database searched a block beyond a record's title and abstract (14 October), which says how a
    record holding none of the block's terms in the text Sift has was found: `methods`, its methods
    sections, `keywords`, its keyword or index fields, `fulltext`, its whole text, or empty for none."""
    used = used_scope(block, source, plan)
    if used != "tak":
        return used
    return "" if (kind_of(source), platform_of(source, plan)) in NO_KEYWORDS else "keywords"


def or_join(parts: list[str]) -> str:
    return " OR ".join(parts)


def years_of(plan: dict) -> tuple:
    y = plan["years"]
    a = y["from"] if isinstance(y["from"], int) else None
    b = y["to"] if isinstance(y["to"], int) else None
    return a, b


def years_words(plan: dict) -> str:
    a, b = years_of(plan)
    if a and b:
        return f"published {a} to {b}"
    if a:
        return f"published {a} on"
    if b:
        return f"published up to {b}"
    return ""


def types_words(types: list[str]) -> str:
    words = [TYPE_WORDS[t] for t in types]
    return words[0] if len(words) == 1 else ", ".join(words[:-1]) + " and " + words[-1] if words else ""


def run_end(a) -> int:
    """The end of a range of years with no open end of its own: the year of the run, or the start
    when a plan begins after it."""
    return max(this_year(), a or 0)


def years_clause(source: str, plan: dict) -> str:
    """The plan's years as a database's string writes them, or empty for none or a database whose site takes
    them: the one place each writer and the strings view's rewrites read them from (14 October)."""
    a, b = years_of(plan)
    kind = kind_of(source)
    if not (a or b):
        return ""
    if kind == "scopus":
        return " AND ".join(([f"PUBYEAR > {a - 1}"] if a else []) + ([f"PUBYEAR < {b + 1}"] if b else []))
    if kind == "wos":
        return f"PY=({a or WOS_FIRST}-{b or run_end(a)})"
    if kind == "pubmed":
        return f"{a or YEAR_LOW}:{b or YEAR_HIGH}[dp]"
    if kind == "epmc":
        return f"PUB_YEAR:[{a or YEAR_LOW} TO {b or run_end(a)}]"
    if kind == "openalex":
        return f"publication_year:{a}-{b}" if a and b else (f"publication_year:>{a - 1}" if a else f"publication_year:<{b + 1}")
    return ""


def types_clause(source: str, plan: dict) -> str:
    """The plan's document types as a database's string writes them, the types it lacks left out, or empty, read
    by each writer and the strings view's rewrites (14 October)."""
    kind = kind_of(source)
    codes = [TYPE_CODES[kind][t] for t in plan["types"] if t in TYPE_CODES.get(kind, {})]
    if not codes:
        return ""
    if kind == "wos":
        return f"DT=({or_join(codes)})"
    if kind == "openalex":
        return "type:" + "|".join(codes)
    return codes[0] if len(codes) == 1 else f"({or_join(codes)})"


def limits_of(source: str, plan: dict) -> list[str]:
    """The years and the types as a database's string ends with them, each where the plan has it."""
    return [c for c in (years_clause(source, plan), types_clause(source, plan)) if c]


def write_scopus(plan: dict, blocks: list) -> str:
    parts = [f"TITLE-ABS-KEY({or_join(term_as_typed(t) for t in terms)})" for _, terms in blocks]
    return " AND ".join(parts + limits_of("scopus", plan))


def write_wos(plan: dict, blocks: list) -> str:
    parts = [f"TS=({or_join(term_as_typed(t) for t in terms)})" for _, terms in blocks]
    return " AND ".join(parts + limits_of("wos", plan))


def write_pubmed(plan: dict, blocks: list) -> str:
    parts = [f"({or_join(term_as_typed(t) + '[tiab]' for t in terms)})" for _, terms in blocks]
    return " AND ".join(parts + limits_of("pubmed", plan))


EPMC_FIELDS = {"tak": ("TITLE_ABS", "KW"), "methods": ("METHODS",), "fulltext": ("TITLE_ABS", "KW", "BODY")}


def write_epmc(plan: dict, blocks: list) -> str:
    parts = []
    for scope, terms in blocks:
        parts.append(f"({or_join(f'{field}:{term_as_typed(t)}' for t in terms for field in EPMC_FIELDS[scope])})")
    return " AND ".join(parts + limits_of("epmc", plan))


def bare(t: dict) -> str:
    """A term as OpenAlex takes it, which stems and has no truncation: the asterisks left out."""
    text = one_line(t["text"].replace("*", ""))
    return f'"{text}"' if t["phrase"] else text


def write_openalex(plan: dict, blocks: list) -> str:
    filters = []
    for scope, key in (("tak", "title_and_abstract.search"), ("fulltext", "fulltext.search")):
        mine = [terms for s, terms in blocks if s == scope]
        if mine:
            filters.append(f"{key}:" + " AND ".join(f"({or_join(bare(t) for t in terms)})" for terms in mine))
    return ",".join(filters + limits_of("openalex", plan))


# the fields a block of title, abstract and keywords is searched in on each platform. PsycInfo has no
# keywords field on Ovid, where its Key Concepts, `id`, stand in, and CINAHL has none on EBSCO, where
# `SU`, its subject fields with their keywords, stands in, as the platforms' own help has it. ProQuest's
# codes are TITLE, ABSTRACT and IF, its keywords and identifiers, joined by commas to search them at once
EBSCO_FIELDS = {"psycinfo": ("TI", "AB", "KW"), "cinahl": ("TI", "AB", "SU")}
OVID_FIELDS = {"psycinfo": "ti,ab,id", "cinahl": "ti,ab"}
PROQUEST_FIELDS = {"psycinfo": "TITLE,ABSTRACT,IF", "pqdt": "TITLE,ABSTRACT,IF", "cinahl": "TITLE,ABSTRACT"}


def write_ebsco(plan: dict, blocks: list, source: str = "psycinfo") -> str:
    """EBSCOhost's field codes, `TI (...) OR AB (...)`, and `TX` for full text."""
    parts = []
    for scope, terms in blocks:
        s = or_join(term_as_typed(t) for t in terms)
        fields = " OR ".join(f"{f} ({s})" for f in EBSCO_FIELDS[source])
        parts.append(f"TX ({s})" if scope == "fulltext" else f"({fields})")
    return " AND ".join(parts)


def write_psycinfo(plan: dict, blocks: list) -> str:
    return write_ebsco(plan, blocks, "psycinfo")


def write_ovid(plan: dict, blocks: list, source: str = "psycinfo") -> str:
    """Ovid's line, each block's terms in brackets with the fields after them, `.ti,ab,id.`, and no
    adjacency operator."""
    return " AND ".join(f"({or_join(term_as_typed(t) for t in terms)}).{OVID_FIELDS[source]}." for _, terms in blocks)


def write_proquest(plan: dict, blocks: list, source: str = "pqdt") -> str:
    """ProQuest's field codes, `TITLE,ABSTRACT,IF(...)`, a block's terms searched in its title, abstract
    and keywords at once, for PsycInfo and Dissertations & Theses, and CINAHL in title and abstract."""
    return " AND ".join(f"{PROQUEST_FIELDS[source]}({or_join(term_as_typed(t) for t in terms)})" for _, terms in blocks)


def write_embase(plan: dict, blocks: list) -> str:
    """Embase.com's syntax, a phrase in single quotes and each block's fields after it, `:ti,ab,kw`."""
    def term(t: dict) -> str:
        return f"'{t['text']}'" if t["phrase"] else t["text"]
    return " AND ".join(f"({or_join(term(t) for t in terms)}):ti,ab,kw" for _, terms in blocks)


def scholar_text(kept: list[list[dict]]) -> str:
    """Google Scholar's plain string: a phrase in double quotes, no asterisk, no field, the terms of a
    block joined by OR, which Google reads before the space that joins the blocks."""
    return " ".join(or_join(bare(t) for t in terms) for terms in kept if terms)


def scholar_fit(blocks: list) -> tuple[str, list[str]]:
    """The string within the length Google Scholar takes, the last term of the longest block left out
    in turn until it fits, every block keeping one term, and the terms left out."""
    kept = [list(terms) for _, terms in blocks]
    dropped = []
    while len(scholar_text(kept)) > SCHOLAR_MOST:
        longest = max(range(len(kept)), key=lambda i: (len(kept[i]), -i))
        if len(kept[longest]) < 2:
            break
        dropped.append(bare(kept[longest].pop()))
    return scholar_text(kept), dropped


def write_scholar(plan: dict, blocks: list) -> str:
    return scholar_fit(blocks)[0]


def write_other(plan: dict, blocks: list) -> str:
    return " AND ".join(f"({or_join(term_as_typed(t) for t in terms)})" for _, terms in blocks)


WRITERS = {"scopus": write_scopus, "wos": write_wos, "pubmed": write_pubmed, "epmc": write_epmc,
           "openalex": write_openalex, "psycinfo": write_psycinfo, "embase": write_embase, "pqdt": write_proquest,
           "scholar": write_scholar, "other": write_other}


def writer_for(source: str, plan: dict):
    """The writer of a database's string, on the platform the plan names for PsycInfo and CINAHL."""
    p = platform_of(source, plan)
    if p == "ovid":
        return lambda pl, blocks: write_ovid(pl, blocks, source)
    if p == "proquest":
        return lambda pl, blocks: write_proquest(pl, blocks, source)
    if p == "ebsco":
        return lambda pl, blocks: write_ebsco(pl, blocks, source)
    return WRITERS[kind_of(source)]


# the databases whose strings carry no limits, so the site's own limiters take them
LIMITERS = ("psycinfo", "cinahl", "embase", "pqdt", "scholar", "other")
# what a string searches in place of keywords, where a platform has no keywords field
FIELD_NOTES = {
    ("psycinfo", "ovid"): lambda: sift_words.t("sift_server.search.field.psycinfo_ovid"),
    ("cinahl", "ebsco"): lambda: sift_words.t("sift_server.search.field.cinahl_ebsco"),
    ("cinahl", "ovid"): lambda: sift_words.t("sift_server.search.field.cinahl_ovid"),
    ("cinahl", "proquest"): lambda: sift_words.t("sift_server.search.field.cinahl_proquest"),
}
# a platform its vendor no longer offers the database on, said under a string a plan still names it for
RETIRED = {
    ("cinahl", "ovid"): lambda: sift_words.t("sift_server.search.retired.ovid"),
    ("cinahl", "proquest"): lambda: sift_words.t("sift_server.search.retired.proquest"),
}


def written(plan: dict, source: str) -> dict:
    """One database's string as Sift writes it from the plan, with its notes: a block searched in
    other fields than asked, OpenAlex's stemming, a document type the database lacks, and the limits
    the site's own limiters take."""
    notes = []
    blocks = []
    for i, block in enumerate(plan["blocks"]):
        terms = terms_of(block)
        if not terms:
            continue
        asked, used = scope_for(block, source), used_scope(block, source, plan)
        if asked != used and source != "scholar":
            notes.append(sift_words.t("sift_server.search.no_field", name=label_of(source, plan), asked=scope_said(asked),
                                block=block_name(plan, i), used=scope_said(used)))
        blocks.append((used, terms))
    query = writer_for(source, plan)(plan, blocks) if blocks else ""
    starred = any("*" in t["text"] for _, terms in blocks for t in terms)
    if source == "openalex" and starred:
        notes.append(sift_words.t("sift_server.search.openalex_s_search_stems_words"))
    platform = platform_of(source, plan)
    if (source, platform) in RETIRED:
        notes.append(RETIRED[(source, platform)]())
    said = FIELD_NOTES.get((source, platform))
    if said and any(scope == "tak" for scope, _ in blocks):
        notes.append(said())
    if starred and (platform == "proquest" or source == "pqdt"):
        notes.append(_w("PROQUEST_STAR"))
    a, b = years_of(plan)
    if blocks and source in RUN_YEAR and a and not b:
        notes.append(sift_words.t("sift_server.search.no_open_end", name=name_of(source, plan), year=run_end(a)))
    if source == "scholar" and blocks:
        starred = any("*" in t["text"] for _, terms in blocks for t in terms)
        notes.append(sift_words.t("sift_server.search.scholar_starred", most=SCHOLAR_MOST) if starred
                     else sift_words.t("sift_server.search.scholar", most=SCHOLAR_MOST))
        dropped = scholar_fit(blocks)[1]
        if dropped:
            notes.append(sift_words.t("sift_server.search.to_keep_within", terms=', '.join(dropped), n=len(dropped)))
    if source in TYPE_CODES:
        lacking = [t for t in plan["types"] if t not in TYPE_CODES[source]]
        if lacking:
            notes.append(sift_words.t("sift_server.search.no_type", name=name_of(source, plan), types=types_words(lacking)))
    limits = ""
    if kind_of(source) in LIMITERS:
        said = [w for w in (years_words(plan), types_words(plan["types"])) if w]
        if said:
            limits = sift_words.t("sift_server.search.set_on_site", limits=", ".join(said))
    return {"query": query, "notes": notes, "limits": limits}


# each database's own fields for a block by the scope it searches it in, as its string names them, for the
# rewrites beside each string (14 October). EBSCO, Ovid and ProQuest name theirs in EBSCO_FIELDS,
# OVID_FIELDS and PROQUEST_FIELDS
FIELD_CODES = {("scopus", "tak"): ("TITLE-ABS-KEY",), ("wos", "tak"): ("TS",), ("pubmed", "tak"): ("[tiab]",),
               ("epmc", "tak"): EPMC_FIELDS["tak"], ("epmc", "methods"): EPMC_FIELDS["methods"],
               ("epmc", "fulltext"): EPMC_FIELDS["fulltext"], ("openalex", "tak"): ("title_and_abstract.search",),
               ("openalex", "fulltext"): ("fulltext.search",), ("embase", "tak"): ("ti", "ab", "kw"),
               ("pqdt", "tak"): ("TITLE", "ABSTRACT", "IF")}
# what a database searches in place of keywords in a block of title, abstract and keywords, where it has no
# keywords field of its own, in the rewrites' plain words (see FIELD_NOTES)
KEYWORD_SWAPS = {("psycinfo", "ovid"): lambda: sift_words.t("sift_server.search.swap.psycinfo_ovid"),
                 ("cinahl", "ebsco"): lambda: sift_words.t("sift_server.search.swap.cinahl_ebsco"),
                 ("cinahl", "ovid"): lambda: sift_words.t("sift_server.search.swap.tiab"),
                 ("cinahl", "proquest"): lambda: sift_words.t("sift_server.search.swap.tiab"),
                 ("openalex", ""): lambda: sift_words.t("sift_server.search.swap.tiab")}


def field_codes(source: str, plan: dict, scope: str) -> tuple:
    """The fields a database's string searches a block in, by the scope it searches it in and the platform the
    plan names, or none for a database whose string names no field."""
    p = platform_of(source, plan)
    if p == "ebsco":
        return ("TX",) if scope == "fulltext" else EBSCO_FIELDS[source]
    if p == "ovid":
        return tuple(OVID_FIELDS[source].split(","))
    if p == "proquest":
        return tuple(PROQUEST_FIELDS[source].split(","))
    return FIELD_CODES.get((kind_of(source), scope), ())


def fields_said(codes: tuple) -> str:
    """Fields as a rewrite names them: the METHODS field, the TITLE_ABS, KW and BODY fields."""
    return sift_words.t("sift_server.search.fields", fields=formats.list_words(list(codes)), n=len(codes))


def block_said(plan: dict, i: int) -> str:
    """A block as a rewrite names it: the Method block, or Block 2 for a block with no name."""
    name = plan["blocks"][i]["name"]
    return sift_words.t("sift_server.search.the_block", name=name) if name else sift_words.t("sift_server.block", i=i + 1)


def rewrites(plan: dict, source: str) -> list[str]:
    """What Sift changed from the plan in writing a database's string, in plain words, beside the string on
    the strings view and in the command line's strings (14 October): a block searched in other fields than
    title, abstract and keywords, or in a database's own in place of the scope it lacks, the fields that
    stand in for keywords, the asterisks left out where a database takes no truncation, a phrase in single
    quotes, the terms left out to fit, the years and the types in the database's own words and a type it
    lacks. A string edited manually is Sift's no longer, so its reason stands alone."""
    over = plan["overrides"].get(source)
    if over:
        return [over["reason"] or sift_words.t("sift_server.search.edited")]
    blocks = [(i, b, terms_of(b)) for i, b in enumerate(plan["blocks"])]
    blocks = [(i, b, terms) for i, b, terms in blocks if terms]
    if not blocks:
        return []
    kind, platform = kind_of(source), platform_of(source, plan)
    out = []
    for i, b, _ in blocks:
        used = used_scope(b, source, plan)
        codes = field_codes(source, plan, used)
        if (scope_for(b, source) != "tak" or used != "tak") and codes:
            out.append(sift_words.t("sift_server.search.block_in", block=block_said(plan, i), fields=fields_said(codes)))
    if KEYWORD_SWAPS.get((kind, platform)) and any(used_scope(b, source, plan) == "tak" for _, b, _ in blocks):
        out.append(KEYWORD_SWAPS[(kind, platform)]())
    terms = [t for _, _, ts in blocks for t in ts]
    if kind == "openalex" and any("*" in t["text"] for t in terms):
        out.append(sift_words.t("sift_server.search.asterisks_removed_openalex_stems"))
    if kind == "scholar":
        if any("*" in t["text"] for t in terms):
            out.append(sift_words.t("sift_server.search.asterisks_removed_google_scholar_has"))
        dropped = scholar_fit([(used_scope(b, source, plan), ts) for _, b, ts in blocks])[1]
        if dropped:
            out.append(sift_words.t("sift_server.search.left_to_fit", terms=', '.join(dropped)))
    if kind == "embase" and any(t["phrase"] for t in terms):
        out.append(sift_words.t("sift_server.search.phrases_in_single_quotes"))
    if kind not in LIMITERS:
        if years_clause(source, plan):
            out.append(sift_words.t("sift_server.search.from_years", clause=years_clause(source, plan)))
        if types_clause(source, plan):
            out.append(sift_words.t("sift_server.search.from_types", clause=types_clause(source, plan)))
        lacking = [t for t in plan["types"] if t not in TYPE_CODES.get(kind, {})]
        if lacking:
            out.append(sift_words.t("sift_server.search.types_left", types=types_words(lacking), n=len(lacking)))
    return out


def strings(plan: dict) -> list[dict]:
    """Each chosen database's string: Sift's own, `written`, and the one a run uses, `query`, the
    hand-written one when there is one, with its reason, then the notes and the limits, the rewrites
    Sift made for it (see `rewrites`) and the platform PsycInfo or CINAHL is searched on."""
    out = []
    for s in plan["databases"]:
        w = written(plan, s)
        over = plan["overrides"].get(s)
        out.append({"source": s, "name": name_of(s, plan), "platform": PLATFORM_NAMES.get(platform_of(s, plan), ""),
                    "written": w["query"], "query": over["query"] if over else w["query"], "override": over,
                    "notes": w["notes"], "limits": w["limits"], "rewrites": rewrites(plan, s)})
    return out


# ---------------------------------------------------------------- the file

def plan_path(folder) -> Path:
    return Path(folder) / PLAN_NAME


def lock_path(folder) -> Path:
    return Path(folder) / LOCK_NAME


def read_file(folder) -> dict:
    """`search_plan.json`, or an empty one when there is none, with the review's own name and question
    where New review wrote them, kept through every write. A file that cannot be read is refused,
    never written over."""
    path = plan_path(folder)
    if not path.is_file():
        return {"versions": []}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError, UnicodeDecodeError):
        raise SearchError(sift_words.t("sift_server.search.cannot_be_read_so_it", plan_name=PLAN_NAME)) from None
    versions = data.get("versions") if isinstance(data, dict) else None
    if not isinstance(versions, list):
        raise SearchError(sift_words.t("sift_server.search.holds_no_versions_so_it", plan_name=PLAN_NAME))
    out = {k: data[k] for k in REVIEW_KEYS if isinstance(data.get(k), str)}
    if isinstance(data.get(KEY_WORKS), list):
        out[KEY_WORKS] = clean_key_works(data[KEY_WORKS])
    out["versions"] = [v for v in versions if isinstance(v, dict) and isinstance(v.get("plan"), dict)]
    return out


def write_file(folder, data: dict) -> None:
    write_text(plan_path(folder), json.dumps(data, ensure_ascii=False, indent=1) + "\n")


def new_plan(folder, name: str, question: str = "") -> None:
    """A new review's `search_plan.json`: its name, its question when it has one, and no version yet,
    so the first change on the Searches screen makes version 1. Refused when the folder holds a plan."""
    if plan_path(folder).exists():
        raise SearchError(sift_words.t("sift_server.search.that_folder_holds_a_already", plan_name=PLAN_NAME))
    data = {"name": one_line(name)}
    if one_line(question):
        data["question"] = one_line(question)
    data["versions"] = []
    write_file(folder, data)


def own_name(folder) -> str:
    """The name a review's plan gives itself, or empty when it gives none or cannot be read."""
    return own_field(folder, "name")


def own_question(folder) -> str:
    """The research question a review's plan holds, New project's, or empty when it holds none."""
    return own_field(folder, "question")


def own_field(folder, key: str) -> str:
    try:
        data = json.loads(plan_path(folder).read_text(encoding="utf-8"))
    except (OSError, ValueError, UnicodeDecodeError):
        return ""
    return one_line(data.get(key)) if isinstance(data, dict) and isinstance(data.get(key), str) else ""


def newest(data: dict) -> dict | None:
    return data["versions"][-1] if data["versions"] else None


def registered_of(data: dict) -> dict | None:
    """The newest registered version, or None."""
    for v in reversed(data["versions"]):
        if v.get("registered"):
            return v
    return None


def version_of(data: dict, n) -> dict | None:
    for v in data["versions"]:
        if v.get("version") == n:
            return v
    return None


def save(folder, raw_plan, reason=None, wait: float | None = None, seen=None) -> dict:
    """The plan as the screen holds it, saved: the draft written over, or with the newest version
    registered a draft of the next made, unless the plan is the registered one as it stands. A
    draft brought back to the registered plan is dropped. `reason` None keeps the draft's reason. With
    the review folder's own `reasons.csv` the plan's reasons are the file's (see `file_reasons`). A plan
    holding a phrase with truncation is refused and nothing is written (14 October), `Unsaved` carrying
    what the screen draws of it (see `phrase_problems`). `seen`, the plan's version as the page last read
    it (see `plan_version`), is refused with `StalePlan` and nothing written when the plan holds another
    version now (19 October)."""
    plan = with_file_reasons(folder, clean_plan(raw_plan))
    held = phrase_problems(plan)
    if held:
        raise Unsaved(held, {"problems": problems(plan), "block_problems": block_problems(plan),
                             "terms_problems": terms_problems(plan)})
    with locks.held(lock_path(folder), wait):
        data = read_file(folder)
        refuse_stale(data, seen)
        last = newest(data)
        if last is None:
            data["versions"].append({"version": 1, "saved": now_iso(), "registered": None, "reason": "", "plan": plan})
        elif last.get("registered"):
            if clean_plan(last["plan"]) == plan:
                return state(folder, data)
            data["versions"].append({"version": int(last["version"]) + 1, "saved": now_iso(), "registered": None,
                                     "reason": one_line(reason), "plan": plan})
        else:
            back = registered_of(data)
            if back is not None and clean_plan(back["plan"]) == plan:
                data["versions"].pop()
            else:
                last.update(plan=plan, saved=now_iso())
                if reason is not None:
                    last["reason"] = one_line(reason)
        write_file(folder, data)
        return state(folder, data)


def save_reasons(folder, raw, wait: float | None = None, seen=None) -> dict:
    """The exclusion reasons as the screen edits them, one list in his order (12 October, later),
    written to the review folder's own `reasons.csv` in its one-list form (see `reasons_text`), a file
    of before written in that form once he edits it, and the plan saved with them, so the newest version
    holds them and a registered version stays as it is, a draft of the next made. A run whose screening
    has not begun takes the new file too, and a run begun keeps the copy it was made with. No reasons
    leaves the header alone, so the plan's reasons of before never come back. A plan holding a phrase
    with truncation keeps its reasons in the file alone until it can be saved again (14 October), which
    takes them from the file then. `seen` is refused as `save` refuses it, before anything is written."""
    text = reasons_text(reasons_of(raw))
    with locks.held(lock_path(folder), wait), contextlib.ExitStack() as runs:
        refuse_stale(read_file(folder), seen)
        # each run folder taking the file has its screening lock taken first (26 October), as a drop
        # takes it, and is asked again under the lock whether its screening has begun, so a lock
        # another writer holds refuses with BUSY before anything is written
        taking = [run_dir for run_dir in run_dirs(folder)
                  if ((run_dir / sift.REASONS_NAME).exists() or sift.is_screening(run_dir)) and not begun(run_dir)]
        for run_dir in taking:
            runs.enter_context(locks.held(sift.lock_path(run_dir), wait))
        write_text(Path(folder) / sift.REASONS_NAME, text)
        for run_dir in taking:
            if not begun(run_dir):
                write_text(run_dir / sift.REASONS_NAME, text)
        last = newest(read_file(folder))
    try:
        return save(folder, last["plan"] if last else blank_plan(), wait=wait)
    except Unsaved as exc:
        return dict(state(folder), unsaved=exc.lines)


def ready(v: dict, plan: dict) -> list[str]:
    """What stands in the way of registering or running a version."""
    out = problems(plan)
    if not v.get("registered") and int(v.get("version") or 1) > 1 and not one_line(v.get("reason")):
        out.append(sift_words.t("sift_server.search.version_needs_the_reason_for", version=v['version']))
    return out


# the registries a plan is registered with, as Mark as registered offers them, and any other by its name
REGISTRIES = ("OSF", "PROSPERO")
REGISTRY_MAX = 60
REGISTRATION_MAX = 240


def registered_with(v: dict) -> str:
    """Where a registered version was registered, its registry and its number or link, "with PROSPERO,
    CRD42026000001", as PRISMA 2020's item 24a asks, or empty for a version registered before the
    registry was kept."""
    registry, number = one_line(v.get("registry")), one_line(v.get("registration"))
    return f"with {registry}, {number}" if registry and number else (f"with {registry}" if registry else "")


def register(folder, reason=None, dry_run: bool = False, wait: float | None = None, registry=None,
             registration=None) -> dict:
    """Mark as registered (12 October, later): the newest version frozen with the time, the registry it
    was registered with, `registry`, OSF, PROSPERO or another by its name, and its registration number
    or link, `registration`, kept with it, and `search_plan.md` written afresh so the file says so. Sift
    registers nothing anywhere: he registers the plan himself, with the file Export writes. A version
    after the first takes its reason here or from the screen. With the review folder's own `reasons.csv`
    the version registered takes the file's reasons. Refused, in plain lines, when the newest version is
    registered already or the plan is not ready."""
    with locks.held(lock_path(folder), wait):
        data = read_file(folder)
        last = newest(data)
        if last is None:
            raise SearchError(sift_words.t("sift_server.search.there_is_no_search_plan"))
        if last.get("registered"):
            raise SearchError(sift_words.t("sift_server.search.version_is_registered_and_unchanged", version=last['version']))
        if reason is not None and one_line(reason):
            last["reason"] = one_line(reason)
        plan = with_file_reasons(folder, clean_plan(last["plan"]))
        said = ready(last, plan)
        if said:
            raise SearchError(*said)
        last.update(plan=plan, registered=now_iso())
        if one_line(registry):
            last.update(registry=one_line(registry)[:REGISTRY_MAX], registration=one_line(registration)[:REGISTRATION_MAX])
        text = markdown(data, last)
        if not dry_run:
            write_file(folder, data)
            write_text(Path(folder) / PLAN_MD, text)
        return dict(state(folder, data), markdown=text, registered=last["version"], dry_run=bool(dry_run))


def export(folder, wait: float | None = None) -> dict:
    """Export search_plan.md (12 October, later): the newest version, a draft or registered, written to
    `search_plan.md` in the review's folder, the file he registers on OSF or PROSPERO himself. Nothing
    is frozen or sent anywhere. With the review folder's own `reasons.csv` the file says its reasons.
    Refused when there is no version yet."""
    with locks.held(lock_path(folder), wait):
        data = read_file(folder)
        last = newest(data)
        if last is None:
            raise SearchError(sift_words.t("sift_server.search.there_is_no_search_plan"))
        shown = dict(last, plan=with_file_reasons(folder, clean_plan(last["plan"])))
        text = markdown(data, shown)
        write_text(Path(folder) / PLAN_MD, text)
        return dict(state(folder, data), exported=text, file=PLAN_MD)


def markdown(data: dict, v: dict) -> str:
    """A version as Markdown, the text search_plan.md holds, to register on OSF or PROSPERO: whether
    and where it is registered, the databases, the blocks with their fields, the limits and
    restrictions, the exclusion reasons, the benchmark, each database's string and the versions
    registered before it."""
    plan = clean_plan(v["plan"])
    lines = [f"# Search plan, version {v['version']}", ""]
    where = registered_with(v)
    when = (f"Registered {day_said(v.get('registered'))}{' ' + where if where else ''}." if v.get("registered")
            else "Not yet registered.")
    if int(v["version"]) > 1 and v.get("reason"):
        when += f" Changed from version {int(v['version']) - 1}: {one_line(v['reason']).rstrip('.')}."
    lines += [when, "", "## Databases", ""]
    names = []
    for s in plan["databases"]:
        names.append(name_of(s, plan) + (" (by export)" if kind_of(s) in LIMITERS else ""))
    lines += [", ".join(names) + ".", "", "## Blocks", "",
              "Terms within a block are combined with OR, and the blocks with AND. An asterisk truncates a word, and "
              "double quotes hold a phrase.", ""]
    for i, b in enumerate(plan["blocks"]):
        if not b["terms"]:
            continue
        field = SCOPE_WORDS[b["scope"]]
        own = [f"{SCOPE_WORDS[sc]} in {name_of(s, plan)}" for s, sc in b["scopes"].items() if s in plan["databases"]]
        where = field + (f", {', '.join(own)}" if own else "")
        lines += [f"{i + 1}. {block_name(plan, i)}, searched in {where}: {', '.join(b['terms'])}.", ""]
    limit = []
    if years_words(plan):
        limit.append(years_words(plan).capitalize() + ".")
    if plan["types"]:
        limit.append(f"Document types: {types_words(plan['types'])}.")
    lines += ["## Limits and restrictions", "", " ".join(limit) or "No limit of years or document type.",
              "No language limit: language is applied at screening.", ""]
    if plan["reasons"]:
        lines += ["## Exclusion reasons", "", "Optional at title and abstract, and one is required for each report "
                  "excluded at full text.", ""]
        lines += [f"- {r['code']}" + (f": {r['meaning']}" if r["meaning"] else "") for r in plan["reasons"]]
        lines += [""]
    if plan["benchmark"]:
        named = [f"{d} ({plan['benchmark_titles'][d]})" if plan["benchmark_titles"].get(d) else d
                 for d in plan["benchmark"]]
        lines += ["## Benchmark", "", f"A run must find {', '.join(named)}.", ""]
    lines += ["## Search strings", ""]
    for s in strings(plan):
        lines += [f"### {s['name']}" + (f" on {s['platform']}" if s["platform"] else ""), "", "```", s["query"], "```", ""]
        if s["override"]:
            lines += [f"Edited manually: {s['override']['reason'].rstrip('.')}.", ""]
        for note in s["notes"]:
            lines += [note, ""]
        if s["limits"]:
            lines += [s["limits"], ""]
    before = [x for x in data["versions"] if x.get("registered") and int(x["version"]) < int(v["version"])]
    if before:
        lines += ["## Earlier versions", ""]
        for x in before:
            why = f" {one_line(x.get('reason')).rstrip('.')}." if x.get("reason") else ""
            where = registered_with(x)
            lines += [f"Version {x['version']}, registered {day_said(x['registered'])}{' ' + where if where else ''}.{why}", ""]
    return "\n".join(lines).rstrip("\n") + "\n"


def state(folder, data: dict | None = None, with_runs: bool = False) -> dict:
    """The plan as the screen draws it: the newest version and its plan, every version's head, each
    database's string, what stands in the way of registering or running and each block's own share of
    it, `block_problems`, the registered version's Markdown, each version before the newest with its
    own, `text`, each registered version's registry and its number or link, whether the folder holds
    `search_plan.md`, `plan_file`, with the runs each benchmark DOI's title where the plan or a run
    knows it, `reasons_file`, the review folder's own reasons when it holds `reasons.csv`, which
    the screen edits in place of the plan's own, or None, and `key_works`, the review's key works."""
    data = read_file(folder) if data is None else data
    last = newest(data)
    plan = clean_plan(last["plan"]) if last else blank_plan()
    reg = registered_of(data)
    head = lambda v: {"version": v.get("version"), "saved": v.get("saved"), "registered": v.get("registered"),
                      "reason": v.get("reason") or "", "registry": one_line(v.get("registry")),
                      "registration": one_line(v.get("registration"))}
    # each version before the newest with its plan as Markdown, `text`, so the screen can show it
    heads = [dict(head(v), **({"text": markdown(data, v)} if v is not last else {})) for v in data["versions"]]
    return {"name": Path(folder).resolve().name, "file": PLAN_NAME, "versions": heads,
            "current": head(last) if last else None,
            "plan": plan, "strings": strings(plan), "problems": ready(last, plan) if last else [],
            "block_problems": block_problems(plan), "registered": reg["version"] if reg else None, "markdown": markdown(data, reg) if reg else "",
            # no block with a term, said under Search terms as well (17 October, later)
            "terms_problems": terms_problems(plan) if last else [],
            "runs": runs(folder) if with_runs else None,
            "titles": benchmark_titles(folder, plan) if with_runs else dict(plan["benchmark_titles"]),
            "reasons_file": file_reasons(folder), "plan_file": (Path(folder) / PLAN_MD).is_file(),
            "key_works": list(data.get(KEY_WORKS) or []),
            # the plan's version, which the page's saves carry back (19 October)
            "plan_version": plan_version(data),
            # how many truncated terms the newest version holds, for Check truncation on the screen (14 October)
            "truncated": len(starred(plan))}


# ---------------------------------------------------------------- the keys

# the program the keychain is read with, `subprocess.run` when None, which the suite replaces
RUNNER = None
# the `.env` a key is kept in on a machine with no keychain, which the server names (see `app_paths`)
ENV_PATH: Path | None = None


def key_runner():
    """The `security` runner every key goes through: the smoke run's own keychain while every request
    goes to a loopback stub, else the suite's stand-in or the tool itself."""
    return STUB_KEYCHAIN if stub_base() else RUNNER


def key_file(run) -> Path | None:
    """The `.env` a key is kept in, only on a machine with no keychain and never in a smoke run."""
    if run is STUB_KEYCHAIN:
        return None
    return ENV_PATH if ai_suggest.security_missing(run) else None


def check_service(service) -> str:
    if service not in SERVICES and service not in OTHER_SERVICES:
        raise SearchError(sift_words.t("sift_server.search.sift_keeps_no_key_by"))
    return service


def save_key(service: str, value) -> dict:
    """A database's key stored under its service, as the Anthropic key is, through `ai_suggest`.
    The answer says whether it was saved and never what it is."""
    run = key_runner()
    done = ai_suggest.save_key(value, runner=run, service=check_service(service), env_path=key_file(run))
    return {"error": done["error"]} if done.get("error") else {"saved": True}


def clear_key(service: str) -> dict:
    run = key_runner()
    return {"cleared": bool(ai_suggest.clear_key(runner=run, service=check_service(service),
                                                 env_path=key_file(run)).get("cleared"))}


def key_saved(service: str) -> bool:
    """Whether a key is stored under the service, never what it is."""
    run = key_runner()
    return bool(ai_suggest.key_status(key_file(run), runner=run, service=check_service(service)).get("set"))


def crossref_for(openalex: str) -> str:
    """Crossref's works address beside OpenAlex's: the real one for the real OpenAlex, and for any other,
    a stub's, the same server with Crossref's host at the head of the path, `/api.crossref.org/works`."""
    if openalex == ENDPOINTS["openalex"]:
        return CROSSREF
    p = urllib.parse.urlparse(openalex)
    return f"{p.scheme}://{p.netloc}/{urllib.parse.urlparse(CROSSREF).netloc}{urllib.parse.urlparse(CROSSREF).path}" if p.netloc else ""


def endpoints() -> dict:
    """Each API's address, every one sent to the stub server in a smoke run, its path kept."""
    base = stub_base()
    if not base:
        return dict(ENDPOINTS)
    return {s: base + urllib.parse.urlparse(url).path for s, url in ENDPOINTS.items()}


def read_key(service: str) -> str | None:
    """A key as it is stored, through `ai_suggest.find_key`, the one way every run and check reads
    one: the login keychain, a `.env` on a machine with none, and in a smoke run the smoke's own
    keychain, its stand-in naming the service. The value goes to the request and nowhere else."""
    run = key_runner()
    return ai_suggest.find_key(key_file(run), runner=run, service=service)


def keys_set() -> dict:
    """Which keyed databases have their key, each True or False, the value never kept."""
    return {s: bool(read_key(KEYS[s])) for s in KEYS}


def listed_row(source: str, listed) -> dict | None:
    return next((r for r in listed or [] if r.get("source") == source), None)


def how_of(source: str, have: dict, listed=None) -> str:
    """`api` for a database Sift searches itself, keyless or with its key saved, else `export`, Sift's
    default. A row of the user's own list decides for its own database, by export when it says so, by
    API when it says so and Sift can, and a database the list does not hold, or every database while
    the list is empty, goes by its default (12 October), so a saved key is never set aside for an
    empty list."""
    row = listed_row(source, listed) if listed else None
    if row is not None and row.get("how") != "api":
        return "export"
    if source in KEYLESS or (source in KEYS and have.get(source)):
        return "api"
    return "export"


# ------------------------------------------------------------- the user's list

def clean_databases(raw) -> list[dict]:
    """The user's own list of databases as `config.json` keeps it, in his order: each a database Sift
    knows, or another by its name, the platform PsycInfo and CINAHL are searched on, EBSCO unless
    another is named, and `api` or `export`, by API only where Sift has one. A database held twice,
    or another of the same name, is kept once."""
    out, seen = [], set()
    for r in raw if isinstance(raw, list) else []:
        if not isinstance(r, dict) or r.get("source") not in SOURCES:
            continue
        s = r["source"]
        row = {"source": s}
        if s == "other":
            row["name"] = one_line(r.get("name"))[:60]
            if not row["name"]:
                continue
        mark = s + ":" + row.get("name", "").lower()
        if mark in seen:
            continue
        seen.add(mark)
        if s in PLATFORMED:
            row["platform"] = r.get("platform") if r.get("platform") in PLATFORMS else "ebsco"
        row["how"] = "api" if s in APIS and r.get("how", "api") == "api" else "export"
        out.append(row)
    return out


def databases(cfg: dict | None) -> list[dict]:
    """The user's list from the settings, empty when they hold none."""
    return clean_databases((cfg or {}).get(DATABASES_KEY))


def row_name(row: dict) -> str:
    p = row.get("platform")
    name = row.get("name") or NAMES[row["source"]]
    return f"{name} on {PLATFORM_NAMES[p]}" if p else name


def database_rows(listed) -> list[dict]:
    """The user's list with each key field and whether its key is saved, never the key."""
    out = []
    for row in clean_databases(listed):
        keys = [dict(f, saved=key_saved(f["service"])) for f in KEY_FIELDS.get(row["source"], ())]
        out.append(dict(row, label=row_name(row), keys=keys if row["how"] == "api" else []))
    return out


def database_lines(rows: list[dict]) -> list[str]:
    """The user's list in plain lines, for the command line: each database, how it is searched and
    whether each key is saved, never the key."""
    lines = [f"Databases: {len(rows)}." if rows else "Databases: none."]
    for r in rows:
        keys = [f"{k['service']} {'saved' if k['saved'] else 'not set'}" for k in r["keys"]]
        lines.append(f"  {r['label']}: {'by API' if r['how'] == 'api' else 'by export'}"
                     + (", " + ", ".join(keys) if keys else "") + ".")
    return lines


# ---------------------------------------------------------------- requests

class Context:
    """What a run's requests share: the addresses, the secrets to scrub, the pause between pages,
    the page sizes, and the error said last."""

    def __init__(self, base: dict | None = None, pause=None, page: dict | None = None, email: str = ""):
        self.base = dict(endpoints(), **(base or {}))
        self.pause = pause if pause is not None else time.sleep
        self.page = dict(PAGE, **(page or {}))
        self.secrets: list[str] = []
        self.openalex_key: str | None = None
        # the email Crossref's polite pool asks for, Sift's settings' own, and Crossref's address, the real
        # one only while OpenAlex's is, so a run sent to a stub sends Crossref's requests to the same stub
        self.email = one_line(email)
        self.crossref = self.base.get("crossref") or crossref_for(self.base.get("openalex", ""))

    def keep(self, secret: str | None) -> str | None:
        if secret:
            self.secrets.append(secret)
        return secret

    def scrub(self, text) -> str:
        return scrub(text, self.secrets)


def openalex_params(ctx: Context, params: dict) -> dict:
    """An OpenAlex request's parameters, with `api_key` when the login keychain holds OPENALEX_API_KEY,
    read once a run and kept among the secrets scrubbed from every error and note, else as they came."""
    if ctx.openalex_key is None:
        ctx.openalex_key = ctx.keep(read_key(OPENALEX_KEY)) or ""
    return dict(params, api_key=ctx.openalex_key) if ctx.openalex_key else dict(params)


def scrub(text, secrets) -> str:
    """Words with every secret in them replaced, so no key reaches a log, a note or the screen."""
    out = str(text or "")
    for s in sorted({s for s in secrets if s}, key=len, reverse=True):
        out = out.replace(s, "[key]")
        out = out.replace(urllib.parse.quote(s, safe=""), "[key]")
    return out


def service_of(ctx: Context, url: str) -> str:
    """The database a request goes to, or Crossref, by its address among the run's own, the longest first,
    so the screen names it and never the address."""
    known = [(base, NAMES[s]) for s, base in ctx.base.items() if s in NAMES and base] + [(ctx.crossref, "Crossref")]
    for base, name in sorted(known, key=lambda k: len(k[0] or ""), reverse=True):
        if base and url.startswith(base):
            return name
    return "The database"


def failed_said(who: str, code: int | None, keyed: bool = False) -> str:
    """A failed request in plain words for the screen (17 October, later): the database, what happened and
    its status in brackets, never an address, a query or what the server's answer held."""
    if not code:
        return f"{who} did not answer."
    if code in (401, 403):
        what = "refused the key" if keyed else "refused the request"
    elif code == 429:
        what = "asked for a break from requests"
    elif code >= 500:
        what = "did not answer"
    else:
        what = "refused the request"
    return f"{who} {what} (HTTP {code})."


def unread_said(who: str) -> str:
    """An answer Sift could not read, in plain words for the screen."""
    return f"{who} sent something Sift could not read."


def note_said(who: str, source: str, note) -> str:
    """A failed database's line for the screen from the full note a run made before 17 October, later,
    kept in its `run.json`: what `get` says now for a status, no answer or an answer it could not read, a
    keyed database refusing its key, and any other note, already in plain words, as it is."""
    note = one_line(note)
    m = re.match(r"HTTP (\d+) from ", note)
    if m:
        return failed_said(who, int(m.group(1)), source in KEYS)
    if note.startswith("No answer from "):
        return failed_said(who, 0)
    if re.search(r"not JSON|cannot read", note) or re.match(r"[A-Z]\w*(Error|Exception): ", note):
        return unread_said(who)
    return note or f"{who} could not be searched."


def get(ctx: Context, url: str, params: dict | None = None, headers: dict | None = None, as_json: bool = True,
        tries: int = 3):
    """One GET, again after a pause on 429 or a server error, its answer as JSON or text, or a
    SearchError saying in plain words which database and what happened, with the status, the address and
    the start of the body in its `detail` for the run's log, both scrubbed."""
    full = url + ("?" + urllib.parse.urlencode(params) if params else "")
    req = urllib.request.Request(full, headers={"User-Agent": UA, **(headers or {})})
    where = urllib.parse.urlparse(url)
    who = service_of(ctx, url)
    # whether the request carried a key, so a refusal says it refused the key
    keyed = any(v and str(v) in ctx.secrets for v in [*(params or {}).values(), *(headers or {}).values()])
    for n in range(tries):
        try:
            with urllib.request.urlopen(req, timeout=TIMEOUT) as r:
                body = r.read().decode("utf-8", "replace")
            return json.loads(body) if as_json else body
        except urllib.error.HTTPError as e:
            if e.code in (429, 500, 502, 503, 504) and n < tries - 1:
                ctx.pause(2 * (n + 1))
                continue
            try:
                said = e.read().decode("utf-8", "replace")
            except Exception:
                said = ""
            raise SearchError(failed_said(who, e.code, keyed), status=e.code,
                              detail=ctx.scrub(f"HTTP {e.code} from {where.netloc}{where.path}: {one_line(said)[:200]}")) from None
        except (urllib.error.URLError, TimeoutError, OSError) as e:
            if n < tries - 1:
                ctx.pause(2 * (n + 1))
                continue
            raise SearchError(failed_said(who, 0), status=0,
                              detail=ctx.scrub(f"No answer from {where.netloc}: {one_line(getattr(e, 'reason', e))}")) from None
        except ValueError:
            raise SearchError(unread_said(who), detail=f"{where.netloc} answered with something that is not JSON.") from None
    raise SearchError(failed_said(who, 0), status=0, detail=f"No answer from {where.netloc}.")


# a run of initials, JJ, T.C., M. or J.-P., and a name that ends in one, as Europe PMC and Scopus write them
INITIALS = re.compile(r"^[A-Z](?:\.?-?[A-Z]){0,3}\.?$")
SURNAME_INITIALS = re.compile(r"^\S.*\s[A-Z](?:\.?-?[A-Z]){0,3}\.?$")


def author_names(authors) -> list[str]:
    """Each author of a record's `authors`, parted by semicolons or bars, or by commas when every part
    is a surname and its initials, `Kvam TM, Stewart LH.`, and else one name, `Baker, Michael` among
    them. `et al.` is no one."""
    text = " ".join(str(authors or "").split()).strip()
    if re.search(r"[;|]", text):
        parts = re.split(r"[;|]", text)
    else:
        pieces = [p.strip() for p in text.split(",")]
        named = [p for p in pieces if p and p.lower().rstrip(".") != "et al"]
        parts = pieces if len(pieces) > 1 and named and all(SURNAME_INITIALS.match(p) for p in named) else [text]
    out = []
    for part in parts:
        name = part.strip(" ,")
        if name and name.lower().rstrip(".") != "et al":
            out.append(name)
    return out


def record(source: str, sid, title, authors, year, journal, doi, abstract, pub_type, keywords="", url="",
           language="") -> dict:
    return {"source": source, "source_id": one_line(sid), "title": one_line(sift.plain(title)),
            "authors": one_line(authors), "year": year_of(year), "journal": one_line(sift.plain(journal)),
            "doi": norm_doi(doi), "abstract": one_line(sift.plain(abstract)), "pub_type": one_line(pub_type),
            "keywords": one_line(keywords), "url": one_line(url), "language": sift.language_cell(language)}


def keyword_list(words) -> str:
    """Keywords as a record keeps them, each on one line and once, case set aside, in their order, parted by
    semicolons (14 October)."""
    out, seen = [], set()
    for w in words or []:
        w = one_line(sift.plain(w))
        if w and w.casefold() not in seen:
            seen.add(w.casefold())
            out.append(w)
    return "; ".join(out)


def keyword_count(text) -> int:
    """How many keywords a record's cell holds, parted by semicolons as `keyword_list` parts them."""
    return len([w for w in str(text or "").split(";") if w.strip()])


def openalex_keywords(w: dict) -> str:
    """A work's keywords as OpenAlex gives them, each by its display name, in its order (14 October)."""
    return keyword_list((k.get("display_name") if isinstance(k, dict) else k) for k in (w or {}).get("keywords") or []
                        if isinstance(k, (dict, str)))


def inverted(index) -> str:
    """An abstract from OpenAlex's inverted index, its words put back in their places."""
    if not isinstance(index, dict):
        return ""
    return " ".join(w for _, w in sorted((p, w) for w, ps in index.items() for p in (ps or []) if isinstance(p, int)))


# ------------------------------------------------------------------ the APIs

def ncbi(ctx: Context) -> dict:
    """NCBI's optional key as a parameter, which raises PubMed's limit, or nothing when none is saved."""
    key = ctx.keep(read_key("NCBI_API_KEY"))
    return {"api_key": key} if key else {}


def run_pubmed(ctx: Context, query: str) -> tuple[int, list, str]:
    base = ctx.base["pubmed"]
    size = ctx.page["pubmed"]
    ids, hits, note, start = [], 0, "", 0
    own = ncbi(ctx)
    while True:
        s = get(ctx, base + "esearch.fcgi", {"db": "pubmed", "term": query, "retstart": start, "retmax": size,
                                              "retmode": "json", **own})
        res = s.get("esearchresult") or {}
        hits = int(res.get("count") or 0)
        if not note and res.get("querytranslation"):
            note = "translation: " + one_line(res["querytranslation"])
        got = [str(i) for i in res.get("idlist") or []]
        ids += got
        start += size
        if not got or start >= min(hits, PUBMED_MOST):
            break
        ctx.pause(PAUSE["pubmed"])
    if hits > PUBMED_MOST:
        note = (note + ", " if note else "") + f"PubMed gives the first {PUBMED_MOST:,}"
    out = []
    for i in range(0, len(ids), 200):
        ctx.pause(PAUSE["pubmed"])
        xml = get(ctx, base + "efetch.fcgi", {"db": "pubmed", "id": ",".join(ids[i:i + 200]), "retmode": "xml", **own},
                  as_json=False)
        try:
            root = ET.fromstring(xml)
        except ET.ParseError:
            raise SearchError(unread_said("PubMed"), detail="PubMed answered with XML Sift cannot read.") from None
        for a in root.iter("PubmedArticle"):
            art = a.find("MedlineCitation/Article")
            if art is None:
                continue
            authors = "; ".join(f"{x.findtext('LastName', '')}, {x.findtext('Initials', '')}".rstrip(", ")
                                for x in art.findall("AuthorList/Author") if x.findtext("LastName"))
            abstract = " ".join("".join(t.itertext()) for t in art.findall("Abstract/AbstractText"))
            doi = next((x.text for x in a.findall("PubmedData/ArticleIdList/ArticleId") if x.get("IdType") == "doi"), "")
            year = (art.findtext("Journal/JournalIssue/PubDate/Year")
                    or art.findtext("Journal/JournalIssue/PubDate/MedlineDate") or "")
            title = art.find("ArticleTitle")
            # its keywords, then its MeSH headings, each once (14 October)
            kws = keyword_list(["".join(k.itertext()) for k in a.findall("MedlineCitation/KeywordList/Keyword")]
                               + ["".join(d.itertext())
                                  for d in a.findall("MedlineCitation/MeshHeadingList/MeshHeading/DescriptorName")])
            out.append(record("PubMed", a.findtext("MedlineCitation/PMID"), "".join(title.itertext()) if title is not None else "",
                              authors, year, art.findtext("Journal/Title"), doi, abstract,
                              "; ".join(x.text or "" for x in art.findall("PublicationTypeList/PublicationType")), kws,
                              language=[x.text or "" for x in art.findall("Language")]))
    return hits, out, note


def run_epmc(ctx: Context, query: str) -> tuple[int, list, str]:
    params = {"query": query, "format": "json", "resultType": "core", "pageSize": ctx.page["epmc"], "cursorMark": "*"}
    out, hits = [], 0
    while True:
        d = get(ctx, ctx.base["epmc"], params)
        hits = int(d.get("hitCount") or 0)
        for r in (d.get("resultList") or {}).get("result") or []:
            kws = keyword_list((r.get("keywordList") or {}).get("keyword") or [])
            out.append(record("Europe PMC", f"{r.get('source')}:{r.get('id')}", r.get("title"), r.get("authorString"),
                              r.get("pubYear"), ((r.get("journalInfo") or {}).get("journal") or {}).get("title"),
                              r.get("doi"), r.get("abstractText"),
                              "; ".join((r.get("pubTypeList") or {}).get("pubType") or []), kws,
                              language=r.get("language") or ""))
        nxt = d.get("nextCursorMark")
        if not nxt or nxt == params["cursorMark"] or len(out) >= hits or not (d.get("resultList") or {}).get("result"):
            return hits, out, ""
        params["cursorMark"] = nxt
        ctx.pause(PAUSE["epmc"])


OPENALEX_FIELDS = "id,doi,title,publication_year,authorships,primary_location,type,abstract_inverted_index,keywords,language"


def openalex_authors(w: dict) -> str:
    """A work's authors as OpenAlex lists them, each by its display name, in its order, parted by
    semicolons, a name it leaves empty passed over."""
    names = [one_line((a.get("author") or {}).get("display_name")) for a in w.get("authorships") or []
             if isinstance(a, dict)]
    return "; ".join(n for n in names if n)


def openalex_record(w: dict) -> dict:
    src = (w.get("primary_location") or {}).get("source") or {}
    return record("OpenAlex", w.get("id"), w.get("title"), openalex_authors(w), w.get("publication_year"),
                  src.get("display_name"), w.get("doi"), inverted(w.get("abstract_inverted_index")), w.get("type"),
                  openalex_keywords(w), language=w.get("language") or "")


def run_openalex(ctx: Context, query: str) -> tuple[int, list, str]:
    params = {"filter": query, "per-page": ctx.page["openalex"], "cursor": "*", "select": OPENALEX_FIELDS}
    out, hits = [], 0
    while True:
        d = get(ctx, ctx.base["openalex"], openalex_params(ctx, params))
        hits = int((d.get("meta") or {}).get("count") or 0)
        results = d.get("results") or []
        out += [openalex_record(w) for w in results]
        params["cursor"] = (d.get("meta") or {}).get("next_cursor")
        if not results or not params["cursor"] or len(out) >= hits:
            return hits, out, "stemmed, no truncation"
        ctx.pause(PAUSE["openalex"])


def run_scopus(ctx: Context, query: str) -> tuple[int, list, str]:
    key = ctx.keep(read_key(KEYS["scopus"]))
    if not key:
        raise SearchError(sift_words.t("sift_server.search.there_is_no_elsevier_api"))
    headers = {"X-ELS-APIKey": key, "Accept": "application/json"}
    token = ctx.keep(read_key(TOKENS["scopus"]))
    if token:
        headers["X-ELS-Insttoken"] = token
    view, note, out, start, hits = "COMPLETE", "", [], 0, 0
    size = ctx.page["scopus"]
    while True:
        try:
            d = get(ctx, ctx.base["scopus"], {"query": query, "view": view, "count": size, "start": start}, headers)
        except SearchError as e:
            if view == "COMPLETE" and e.status in (401, 403):
                view, note = "STANDARD", "COMPLETE view refused, STANDARD used, with no abstracts"
                continue
            raise
        sr = d.get("search-results") or {}
        hits = int(sr.get("opensearch:totalResults") or 0)
        entries = [e for e in sr.get("entry") or [] if "error" not in e]
        for e in entries:
            authors = "; ".join(a.get("authname", "") for a in e.get("author") or []) or e.get("dc:creator", "")
            out.append(record("Scopus", e.get("eid"), e.get("dc:title"), authors, e.get("prism:coverDate"),
                              e.get("prism:publicationName"), e.get("prism:doi"), e.get("dc:description"),
                              e.get("subtypeDescription"), str(e.get("authkeywords") or "").replace(" | ", "; ")))
        start += size
        if not entries or start >= min(hits, SCOPUS_MOST):
            break
        ctx.pause(PAUSE["scopus"])
    if hits > SCOPUS_MOST:
        note = (note + ", " if note else "") + f"Scopus gives the first {SCOPUS_MOST:,} this way"
    return hits, out, note


def run_wos(ctx: Context, query: str) -> tuple[int, list, str]:
    key = ctx.keep(read_key(KEYS["wos"]))
    if not key:
        raise SearchError(sift_words.t("sift_server.search.there_is_no_clarivate_api"))
    out, page, hits = [], 1, 0
    size = ctx.page["wos"]
    while True:
        d = get(ctx, ctx.base["wos"], {"q": query, "db": "WOS", "limit": size, "page": page}, {"X-ApiKey": key})
        hits = int((d.get("metadata") or {}).get("total") or 0)
        for h in d.get("hits") or []:
            src = h.get("source") or {}
            authors = "; ".join(a.get("displayName", "") for a in (h.get("names") or {}).get("authors") or [])
            kws = "; ".join((h.get("keywords") or {}).get("authorKeywords") or [])
            out.append(record("Web of Science", h.get("uid"), h.get("title"), authors, src.get("publishYear"),
                              src.get("sourceTitle"), (h.get("identifiers") or {}).get("doi"), "",
                              "; ".join(h.get("types") or []), kws))
        if not d.get("hits") or page * size >= hits:
            return hits, out, "the Starter API gives no abstracts"
        page += 1
        ctx.pause(PAUSE["wos"])


RUNNERS = {"pubmed": run_pubmed, "epmc": run_epmc, "openalex": run_openalex, "scopus": run_scopus, "wos": run_wos}


# ------------------------------------------------------------ the truncation check

# The dry run's truncation check (14 October): each truncated term of the plan, a single word with its
# asterisk, counted alone in its block's fields with the plan's years and types, with and without the
# asterisk, in each database Sift searches by API whose syntax takes truncation, one request for each form
# and Sift's usual pause between them. A database whose two counts are equal while another's differ reads
# the asterisk as nothing, and one with no hits while another has some is either written wrongly or does
# not hold the work, so both are flagged before a run and never found after. OpenAlex takes no truncation
# and Sift leaves its asterisks out, so it is not asked. A run that checks keeps the table in its folder as
# TERMS_NAME and the flags in `run.json`.
TRUNCATES = ("scopus", "wos", "pubmed", "epmc")
TERMS_NAME = "dry_run_terms.csv"
TERMS_COLUMNS = ["block", "term", "database", "with_asterisk", "without_asterisk", "flag", "query", "query_without"]
# Adam's two flags, the first naming the database, the term and the term without its asterisk, and the
# second as a run's flags name it, with its term
READS_AS = "{name} reads {term} as {bare}"
NO_HITS = "No hits in {name}: syntax or coverage?"
NO_HITS_FOR = "No hits in {name} for {term}: syntax or coverage?"


def starred(plan: dict) -> list[tuple[int, dict]]:
    """Each truncated term of the plan, a single word with an asterisk, with its block's place, in the plan's
    order and once in its block."""
    out = []
    for i, block in enumerate(plan["blocks"]):
        for t in terms_of(block):
            if not t["phrase"] and "*" in t["text"] and (i, t) not in out:
                out.append((i, t))
    return out


def alone(plan: dict, i: int, text: str) -> dict:
    """The plan with block `i` holding one term and no other block beside it, its fields, the years and the
    types kept and no string edited manually, so a database's writer writes that term's count alone."""
    return dict(plan, blocks=[dict(plan["blocks"][i], terms=[text])], overrides={})


def counter(source: str, ctx: Context):
    """How one database is asked for a count, as its runner asks it but for a single record or none, its key
    read once, every answer read for its number of hits alone."""
    if source == "pubmed":
        own = ncbi(ctx)
        return lambda q: int(((get(ctx, ctx.base["pubmed"] + "esearch.fcgi", {"db": "pubmed", "term": q, "retmax": 0,
                                                                              "retmode": "json", **own}, tries=2)
                               .get("esearchresult") or {}).get("count") or 0))
    if source == "epmc":
        return lambda q: int(get(ctx, ctx.base["epmc"], {"query": q, "format": "json", "resultType": "idlist", "pageSize": 1},
                                 tries=2).get("hitCount") or 0)
    if source == "scopus":
        key = ctx.keep(read_key(KEYS["scopus"]))
        if not key:
            raise SearchError(sift_words.t("sift_server.search.there_is_no_elsevier_api"))
        headers = {"X-ELS-APIKey": key, "Accept": "application/json"}
        token = ctx.keep(read_key(TOKENS["scopus"]))
        if token:
            headers["X-ELS-Insttoken"] = token
        return lambda q: int((get(ctx, ctx.base["scopus"], {"query": q, "count": 1, "view": "STANDARD"}, headers, tries=2)
                              .get("search-results") or {}).get("opensearch:totalResults") or 0)
    key = ctx.keep(read_key(KEYS["wos"]))
    if not key:
        raise SearchError(sift_words.t("sift_server.search.there_is_no_clarivate_api"))
    return lambda q: int((get(ctx, ctx.base["wos"], {"q": q, "db": "WOS", "limit": 1, "page": 1}, {"X-ApiKey": key}, tries=2)
                          .get("metadata") or {}).get("total") or 0)


def flag_rows(rows: list[dict]) -> None:
    """Each row's flag, worked out term by term across the databases that counted it: no hits where another
    database has some, else the asterisk read as nothing where its counts are equal and another's differ."""
    by_term: dict[tuple, list] = {}
    for r in rows:
        by_term.setdefault((r["i"], r["term"]), []).append(r)
    for group in by_term.values():
        counted = [r for r in group if isinstance(r["with"], int) and isinstance(r["without"], int)]
        hits = [r for r in counted if r["with"] > 0]
        differ = [r for r in counted if r["with"] != r["without"]]
        for r in counted:
            if r["with"] == 0 and hits:
                r["flag"] = NO_HITS.format(name=r["name"])
            elif r["with"] == r["without"] and differ:
                r["flag"] = READS_AS.format(name=r["name"], term=r["term"], bare=r["bare"])


def truncation_check(plan: dict, sources, ctx: Context, progress=None) -> dict:
    """The truncation check for the databases among `sources` that take truncation, each truncated term
    counted alone with and without its asterisk (see `starred`, `alone` and `counter`), Sift's pause for
    the database between one request and the next, as a run pauses between pages. A database whose key is
    missing or whose request fails is said on its rows and asked no more. `progress(source, state)` hears
    each database checked and done. The answer is `rows`, each its block, term, the term without its
    asterisk, the database, the two counts, the two queries, the failure said in plain words for the screen,
    `said`, and in full for the run's file, `detail` (17 October, later), and its flag, `flags`, the
    flags in plain lines with their terms, and `sources`, the databases asked by name."""
    terms = starred(plan)
    asked = [s for s in in_order(sources) if s in TRUNCATES] if terms else []
    rows = []
    for s in asked:
        if progress:
            progress(s, "checking")
        name, failed, detail, first = name_of(s, plan), "", "", True
        try:
            count = counter(s, ctx)
        except SearchError as e:
            failed, detail = ctx.scrub(str(e)), ctx.scrub(logged(e))
        for i, t in terms:
            bare = one_line(t["text"].replace("*", ""))
            row = {"i": i, "block": block_name(plan, i), "term": t["text"], "bare": bare, "source": s, "name": name,
                   "with": None, "without": None, "query": written(alone(plan, i, t["text"]), s)["query"],
                   "query_without": written(alone(plan, i, bare), s)["query"], "said": "", "detail": "", "flag": ""}
            for key, query in (("with", row["query"]), ("without", row["query_without"])):
                if failed:
                    break
                if not first:
                    ctx.pause(PAUSE[s])
                first = False
                try:
                    row[key] = count(query)
                except SearchError as e:
                    failed, detail = ctx.scrub(str(e)), ctx.scrub(logged(e))
                except (ValueError, TypeError, AttributeError) as e:     # a count that is not one, said and passed over
                    failed, detail = unread_said(name), ctx.scrub(f"{type(e).__name__}: {e}")
            if row["with"] is None or row["without"] is None:
                row["said"], row["detail"] = failed, detail
            rows.append(row)
        if progress:
            progress(s, "waiting")
    flag_rows(rows)
    flags = [r["flag"] if not r["flag"].startswith("No hits") else NO_HITS_FOR.format(name=r["name"], term=r["term"])
             for r in rows if r["flag"]]
    return {"rows": rows, "flags": flags, "sources": [name_of(s, plan) for s in asked]}


def terms_text(rows: list[dict]) -> str:
    """The truncation check's table as `dry_run_terms.csv` holds it, a row a term in each database, a count
    that failed empty with the failure in its flag."""
    out = io.StringIO(newline="")
    w = csv.writer(out, lineterminator="\r\n")
    w.writerow(TERMS_COLUMNS)
    for r in rows:
        w.writerow([r["block"], r["term"], r["name"], "" if r["with"] is None else r["with"],
                    "" if r["without"] is None else r["without"],
                    r["flag"] or (f"failed: {r.get('detail') or r['said']}" if r["said"] else ""),
                    r["query"], r["query_without"]])
    return out.getvalue()


def terms_lines(table: dict) -> list[str]:
    """The truncation check in plain lines, for the command line's dry run: each term with its counts in each
    database, with and without its asterisk, then each flag."""
    if not table or not table.get("rows"):
        return []
    lines = ["Truncation, each term alone with and without its asterisk:"]
    by_term: dict[tuple, list] = {}
    for r in table["rows"]:
        by_term.setdefault((r["i"], r["term"]), []).append(r)
    for (_, term), group in by_term.items():
        # the failure in full, as the run's file keeps it, for the command line's reader
        said = [f"{r['name']} failed, {r.get('detail') or r['said']}" if r["said"] else f"{r['name']} {r['with']:,} and {r['without']:,}"
                for r in group]
        lines.append(f"  {term}, {group[0]['block']}: {', '.join(said)}.")
    lines += [f"  {f}." if not f.endswith("?") else f"  {f}" for f in table["flags"]]
    return lines


def check_terms(folder, which="newest", listed=None, ctx: Context | None = None) -> dict:
    """Check truncation on the screen (14 October), the dry run's truncation check alone, for the version a
    run would take, `newest` as the screen runs it, refused in plain lines as a run is when the plan is not
    ready: the databases it searches by API, by the user's own list, `listed`, each checked (see
    `truncation_check`). Nothing is written. The answer is the table with the version checked."""
    ctx = ctx or Context()
    _, v, plan = plan_for_run(folder, which)
    have = keys_set()
    api = [s for s in plan["databases"] if how_of(s, have, listed) == "api"]
    return dict(truncation_check(plan, api, ctx), version=v["version"])


# ------------------------------------------------------------------ Check

CHECK_TERM = "health"


def check_scopus(ctx: Context, key: str | None) -> None:
    headers = {"X-ELS-APIKey": key or "", "Accept": "application/json"}
    token = ctx.keep(read_key(TOKENS["scopus"]))
    if token:
        headers["X-ELS-Insttoken"] = token
    get(ctx, ctx.base["scopus"], {"query": f"TITLE({CHECK_TERM})", "count": 1, "view": "STANDARD"}, headers, tries=1)


def check_wos(ctx: Context, key: str | None) -> None:
    get(ctx, ctx.base["wos"], {"q": f"TS=({CHECK_TERM})", "db": "WOS", "limit": 1, "page": 1}, {"X-ApiKey": key or ""},
        tries=1)


def check_openalex(ctx: Context, key: str | None) -> None:
    get(ctx, ctx.base["openalex"], {"search": CHECK_TERM, "per-page": 1, "select": "id", **({"api_key": key} if key else {})},
        tries=1)


def check_pubmed(ctx: Context, key: str | None) -> None:
    get(ctx, ctx.base["pubmed"] + "esearch.fcgi", {"db": "pubmed", "term": CHECK_TERM, "retmax": 1, "retmode": "json",
                                                   **({"api_key": key} if key else {})}, tries=1)


CHECKS = {"scopus": check_scopus, "wos": check_wos, "openalex": check_openalex, "pubmed": check_pubmed}


def check(source: str, ctx: Context | None = None) -> dict:
    """Check, beside a database's key in Settings: a search for one record sent with the key as it is
    stored, and one line saying whether the database took it. The key goes to that request alone, and
    the line is scrubbed of it."""
    if source not in CHECKS:
        raise SearchError(sift_words.t("sift_server.search.sift_has_no_key_to"))
    ctx = ctx or Context()
    name = NAMES[source]
    field = KEY_FIELDS[source][0]
    key = ctx.keep(read_key(field["service"]))
    if not key and not field["optional"]:
        return {"ok": False, "said": sift_words.t("sift_server.search.there_is_no_key_to", name=name)}
    try:
        CHECKS[source](ctx, key)
    except SearchError as e:
        # the status in brackets, as every failed request says it on the screen (17 October, later)
        if key and e.status in (400, 401, 403):
            return {"ok": False, "said": sift_words.t("sift_server.search.refused_the_key_http", name=name, status=e.status)}
        return {"ok": False, "said": ctx.scrub(str(e))}
    return {"ok": True, "said": sift_words.t("sift_server.search.accepted_the_key", name=name) if key else sift_words.t("sift_server.search.answered_with_no_key", name=name)}


# what the fill asks OpenAlex for, by DOI: the abstract, the authors and the count of citations, and since
# 13 October whether the paper was retracted, its open access and the works it cites
FILL_FIELDS = ("id,doi,abstract_inverted_index,authorships,cited_by_count,is_retracted,open_access,referenced_works,"
               "keywords,language")
# what Fill from OpenAlex asks it for, for a screening made before: Sift's own columns, and since 14 October
# the keywords and the language of a record that lacks them
OWN_FIELDS = "id,doi,authorships,cited_by_count,is_retracted,open_access,referenced_works,keywords,language"
# what Crossref is asked for, each paper's updates and its references, all of a record without `select`
# where Crossref refuses it
CROSSREF_SELECT = "DOI,updated-by,reference"
# Crossref's kinds of update, by the words the retraction column says them in, and any other passed over
UPDATE_KINDS = {"retraction": "retracted", "partial_retraction": "retracted", "withdrawal": "retracted",
                "removal": "retracted", "expression_of_concern": "expression of concern", "correction": "corrected",
                "corrigendum": "corrected", "erratum": "corrected"}
# the fields of a Crossref reference a key work's title is found in, since publishers put a book's
# title in any of them
REF_TITLES = ("series-title", "volume-title", "article-title", "journal-title", "unstructured")
# what Find citation counts asks it for, for a screening made before, and how many DOIs a request
CITED_FIELDS = "id,doi,cited_by_count"
BATCH = 50


def asked_doi(doi) -> bool:
    """Whether a DOI is one OpenAlex can be asked for by a filter, a single DOI with no bar, comma or space."""
    return bool(doi) and not re.search(r"[|,\s]", str(doi))


def works_by_doi(ctx: Context, dois: list[str], select: str) -> dict:
    """OpenAlex's works for up to BATCH DOIs in one request, by each DOI as `norm_doi` gives it, or a
    SearchError when the request fails."""
    d = get(ctx, ctx.base["openalex"], openalex_params(ctx, {"filter": "doi:" + "|".join(dois), "per-page": BATCH,
                                                             "select": select}))
    return {norm_doi(w.get("doi")): w for w in d.get("results") or [] if isinstance(w, dict)}


def cited_count(w: dict) -> int | None:
    """A work's `cited_by_count`, a whole number, nought among them, or None when OpenAlex gives none."""
    c = (w or {}).get("cited_by_count")
    return c if isinstance(c, int) and not isinstance(c, bool) and c >= 0 else None


def short_id(value, letter: str) -> str:
    """An OpenAlex ID as its letter and number, W2741809807 from its address, or empty."""
    m = re.search(rf"({letter}\d+)\s*$", str(value or ""))
    return m.group(1) if m else ""


def openalex_cells(w: dict, day: str) -> dict:
    """Sift's own cells from one OpenAlex work (13 October): its count of citations with the day, its
    kind of open access, `closed` for none, the countries of its authors' institutions, each once in its
    order, an author's own countries where OpenAlex names no institution's, its authors with their IDs,
    and the day it was asked."""
    cells = {sift.OPENALEX_DATE: day}
    count = cited_count(w)
    if count is not None:
        cells[sift.CITED_COLUMN], cells[sift.CITED_DATE] = str(count), day
    oa = w.get("open_access") if isinstance(w.get("open_access"), dict) else {}
    status = one_line(oa.get("oa_status")).lower()
    cells[sift.OA_COLUMN] = status if status in sift.OA_KINDS else ("closed" if oa.get("is_oa") is False else "")
    codes, people = [], []
    for a in w.get("authorships") or []:
        if not isinstance(a, dict):
            continue
        found = [str(i.get("country_code") or "").upper() for i in a.get("institutions") or []
                 if isinstance(i, dict) and i.get("country_code")]
        codes += found or [str(c).upper() for c in a.get("countries") or [] if c]
        au = a.get("author") if isinstance(a.get("author"), dict) else {}
        name, aid = one_line(au.get("display_name")), short_id(au.get("id"), "A")
        if name:
            people.append(f"{name} ({aid})" if aid else name)
    cells[sift.COUNTRIES_COLUMN] = "; ".join(dict.fromkeys(c for c in codes if re.fullmatch(r"[A-Z]{2}", c)))
    cells[sift.AUTHORS_COLUMN] = "; ".join(people)
    return cells


def openalex_refs(w: dict) -> list[str]:
    """The works OpenAlex says a work cites, each by its ID."""
    return [i for i in (short_id(x, "W") for x in w.get("referenced_works") or []) if i]


def date_of(value) -> str:
    """A Crossref date as the record keeps it, 2023-01-05, or its year and month, or its year, or empty."""
    parts = ((value or {}).get("date-parts") or [[]])[0] if isinstance(value, dict) else []
    parts = [p for p in parts or [] if isinstance(p, int)][:3]
    return "-".join([f"{parts[0]:04d}"] + [f"{p:02d}" for p in parts[1:]]) if parts else ""


def crossref_works(ctx: Context, dois: list[str]) -> dict:
    """Crossref's records for up to BATCH DOIs in one request, by each DOI as `norm_doi` gives it, its
    updates and references alone, asked again whole when Crossref refuses the `select`, or a SearchError
    when the request fails. The email Sift's settings keep goes as `mailto`, for Crossref's polite pool."""
    params = {"filter": ",".join("doi:" + d for d in dois), "rows": len(dois), "select": CROSSREF_SELECT}
    if ctx.email:
        params["mailto"] = ctx.email
    try:
        d = get(ctx, ctx.crossref, params)
    except SearchError as e:
        if e.status != 400:
            raise
        params.pop("select")
        d = get(ctx, ctx.crossref, params)
    message = d.get("message") if isinstance(d, dict) else None
    items = message.get("items") if isinstance(message, dict) else None
    if not isinstance(items, list):
        raise SearchError(unread_said("Crossref"), detail="Crossref answered with something Sift cannot read.")
    return {norm_doi(i.get("DOI")): i for i in items if isinstance(i, dict) and i.get("DOI")}


def crossref_notices(item: dict) -> list[dict]:
    """A paper's notices as Crossref's `updated-by` gives them: a retraction, a withdrawal or a removal as
    retracted, an expression of concern, and a correction, a corrigendum or an erratum as corrected, each
    with the notice's DOI and date, any other update passed over."""
    out = []
    for u in item.get("updated-by") or []:
        kind = UPDATE_KINDS.get(re.sub(r"[\s-]+", "_", one_line(u.get("type")).lower())) if isinstance(u, dict) else None
        if kind:
            out.append({"kind": kind, "doi": norm_doi(u.get("DOI")), "date": date_of(u.get("updated")), "from": "Crossref"})
    return out


def crossref_refs(item: dict) -> list[list[str]]:
    """A paper's references as Crossref holds them, each its DOI, its year, its own or the first its
    `unstructured` text names, and each title it gives in REF_TITLES, folded (see `sift.fold_title`), so a
    key work is found among them on reading."""
    out = []
    for r in item.get("reference") or []:
        if not isinstance(r, dict):
            continue
        texts = [t for t in dict.fromkeys(sift.fold_title(r.get(k)) for k in REF_TITLES) if t]
        doi = norm_doi(r.get("DOI"))
        if doi or texts:
            out.append([doi, year_of(r.get("year")) or year_of(r.get("unstructured"))] + texts)
    return out


def retraction_cells(kinds, notices: list, retracted, found) -> dict:
    """The retraction column's two cells from what the record held, `kinds` and `notices`, and what was
    asked now, `retracted`, OpenAlex's `is_retracted`, or None when OpenAlex was not asked or did not know
    the paper, and `found`, Crossref's notices, or None the same way: each kind once, retracted, expression
    of concern and corrected in that order, `none` once either service has said and neither names one,
    and each notice once by its kind and DOI. Nothing when neither has ever said."""
    if kinds is None and retracted is None and found is None:
        return {}
    have = set(kinds or [])
    held = [dict(n) for n in notices or []]
    for n in found or []:
        have.add(n["kind"])
        if all((h["kind"], h["doi"]) != (n["kind"], n["doi"]) for h in held):
            held.append(n)
    if retracted:
        have.add("retracted")
        if not any(h["kind"] == "retracted" for h in held):
            held.append({"kind": "retracted", "doi": "", "date": "", "from": "OpenAlex"})
    words = [k for k in sift.NOTICE_KINDS if k in have]
    return {sift.RETRACTION_COLUMN: "; ".join(words) or sift.NO_NOTICE,
            sift.NOTICES_COLUMN: json.dumps(held, ensure_ascii=False) if held else ""}


def fill_from_openalex(ctx: Context, merged: list[dict], bibliographic: bool = True) -> dict:
    """What the databases lacked, filled from OpenAlex by DOI, fifty DOIs a request, every record with
    a DOI asked about: an abstract a record lacks, marked as from OpenAlex, the authors of a record that
    names one or none, as Scopus's search gives only the first, OpenAlex's list joined as its own records
    join it, when it names more, and each record's count of citations with the day it was asked (12
    October), and in the same pass Sift's own columns of 13 October (see `openalex_cells`), with Crossref
    asked for the same fifty DOIs, its notices and references, and the retraction column from both (see
    `retraction_cells`). Each record's references go under `references`, `openalex` and `crossref`, for
    `screening.references.json`. The keywords and the language of a record that lacks them are filled
    from OpenAlex's and never written over (14 October). With `bibliographic` false, as for a record
    carried from an earlier run, which is never changed, the abstract and the authors are left as they
    are, OpenAlex is asked only for a record whose own columns lack its day or a count, or that lacks
    keywords or a language, and Crossref only for one that lacks Crossref's day. A request that fails
    leaves those records as they were. The answer counts the abstracts, the records' authors, their
    counts of citations and the records OpenAlex and Crossref each answered for, and says the first
    failure, `said`."""
    wanted = [m for m in merged if asked_doi(norm_doi(m.get("doi")))]
    out = {"abstracts": 0, "authors": 0, "cited": 0, "openalex": 0, "crossref": 0, "said": ""}
    day = today().isoformat()
    blank = lambda m, k: not one_line(m.get(k))
    # `ask`, where a record carries it, says which of the two to ask, as Fill from OpenAlex sets it
    asks = lambda m, i, default: bool(m["ask"][i]) if isinstance(m.get("ask"), tuple) else default
    for i in range(0, len(wanted), BATCH):
        part = wanted[i:i + BATCH]
        to_oa = [m for m in part if asks(m, 0, bibliographic or blank(m, sift.OPENALEX_DATE) or blank(m, sift.CITED_COLUMN)
                                         or blank(m, sift.KEYWORDS_COLUMN) or blank(m, sift.LANGUAGE_COLUMN))]
        to_cr = [m for m in part if asks(m, 1, bibliographic or blank(m, sift.CROSSREF_DATE))]
        found, items = {}, {}
        if to_oa:
            try:
                found = works_by_doi(ctx, [norm_doi(m["doi"]) for m in to_oa], FILL_FIELDS if bibliographic else OWN_FIELDS)
            except SearchError as e:
                found, out["said"] = {}, out["said"] or ctx.scrub(str(e))
        if to_cr and ctx.crossref:
            try:
                items = crossref_works(ctx, [norm_doi(m["doi"]) for m in to_cr])
            except SearchError as e:
                items, out["said"] = {}, out["said"] or ctx.scrub(str(e))
        for m in part:
            doi = norm_doi(m["doi"])
            w = found.get(doi) if any(x is m for x in to_oa) else None
            item = items.get(doi) if any(x is m for x in to_cr) else None
            if bibliographic and w:
                text = inverted(w.get("abstract_inverted_index"))
                if text and not m["abstract"]:
                    m["abstract"], m["abstract_from"] = text, "OpenAlex"
                    out["abstracts"] += 1
                names = openalex_authors(w)
                if len(author_names(names)) > len(author_names(m["authors"])) and len(author_names(m["authors"])) <= 1:
                    m["authors"] = names
                    out["authors"] += 1
            # the keywords and the language of a record that lacks them, never written over (14 October)
            if w and not one_line(m.get(sift.KEYWORDS_COLUMN)) and openalex_keywords(w):
                m[sift.KEYWORDS_COLUMN] = openalex_keywords(w)
            if w and not one_line(m.get(sift.LANGUAGE_COLUMN)) and sift.language_cell(w.get("language")):
                m[sift.LANGUAGE_COLUMN] = sift.language_cell(w.get("language"))
            refs = {}
            if w:
                cells = openalex_cells(w, day)
                out["cited"] += int(sift.CITED_COLUMN in cells)
                out["openalex"] += 1
                m.update(cells)
                refs["openalex"] = openalex_refs(w)
            if item is not None:
                m[sift.CROSSREF_DATE] = day
                out["crossref"] += 1
                refs["crossref"] = crossref_refs(item)
            m.update(retraction_cells(sift.notice_kinds(m.get(sift.RETRACTION_COLUMN)), sift.notices_of(m.get(sift.NOTICES_COLUMN)),
                                      bool(w.get("is_retracted")) if w else None,
                                      crossref_notices(item) if item is not None else None))
            if refs:
                m["references"] = dict(m.get("references") or {}, **refs)
        ctx.pause(PAUSE["openalex"])
    return out


def fill_wants(sc, rec: str, refs: dict) -> tuple[bool, bool]:
    """Whether Fill from OpenAlex asks about a record: OpenAlex when its own columns lack OpenAlex's day,
    its count of citations or its references, or it lacks keywords or a language (14 October), and
    Crossref when they lack Crossref's day or its references."""
    entry = refs.get(rec) if isinstance(refs.get(rec), dict) else {}
    blank = lambda k: not sc.cell(rec, k).strip()
    return (blank(sift.OPENALEX_DATE) or blank(sift.CITED_COLUMN) or blank(sift.KEYWORDS_COLUMN) or blank(sift.LANGUAGE_COLUMN)
            or "openalex" not in entry,
            blank(sift.CROSSREF_DATE) or "crossref" not in entry)


def fill_plan(folder) -> dict:
    """What Fill from OpenAlex would go through for a screening made before (13 October), before anything
    is asked: its records with a DOI, in the CSV's order, `of` of them, `records` in all, and `missing`,
    those that lack one of Sift's own columns from OpenAlex or Crossref. Only reads."""
    sc = sift.load(folder)
    refs = sift.references(folder)
    ids = [rec for rec in sc.ids if asked_doi(norm_doi(sc.cell(rec, "doi")))]
    return {"ids": ids, "of": len(ids), "records": len(sc.ids),
            "missing": sum(1 for rec in ids if any(fill_wants(sc, rec, refs)))}


def fill_columns(folder, at: int = 0, ctx: Context | None = None, keep=None, email: str = "") -> dict:
    """Fill from OpenAlex, for a screening made before (13 October), in place of Find citation counts:
    the next BATCH of its records with a DOI from `at`, in the CSV's order, those of them that lack one of
    Sift's own columns, keywords or a language asked of OpenAlex in one request and of Crossref in
    another, as a run asks them (see `fill_wants`), and every cell found written with today's date
    through `keep`, which takes the cells and the references by rec_id, `sift.write_filled` when not
    given, Cited by among them. The asking is done before the screening's lock is taken. The answer
    says where the next batch starts, `at`, how many records with a DOI there are, `of`, how many this
    batch asked about, `asked`, and filled, `filled`, or `said`, one line when neither service answered."""
    ctx = ctx or Context(email=email)
    if email:
        ctx.email = one_line(email)
    plan = fill_plan(folder)
    at = max(0, int(at or 0))
    part = plan["ids"][at:at + BATCH]
    out = {"at": at + len(part), "of": plan["of"], "records": plan["records"], "asked": 0, "filled": 0, "said": ""}
    if not part:
        return out
    sc = sift.load(folder)
    refs = sift.references(folder)
    items = []
    for rec in part:
        oa, cr = fill_wants(sc, rec, refs)
        if oa or cr:
            items.append({"rec_id": rec, "doi": norm_doi(sc.cell(rec, "doi")), "ask": (oa, cr),
                          **{k: sc.cell(rec, k) for k in sift.FILLED + (sift.KEYWORDS_COLUMN, sift.LANGUAGE_COLUMN)}})
    out["asked"] = len(items)
    if not items:
        return out
    got = fill_from_openalex(ctx, items, bibliographic=False)
    if got["said"] and not got["openalex"] and not got["crossref"]:
        return dict(out, said=got["said"])
    answered = [m for m in items if m.get("references")]
    # Sift's own columns, and the keywords and the language where OpenAlex gave a record that lacked them
    # some (14 October), written only where the cell is empty
    cells = {m["rec_id"]: dict({k: m.get(k) or "" for k in sift.FILLED},
                               **{k: m[k] for k in (sift.KEYWORDS_COLUMN, sift.LANGUAGE_COLUMN) if m.get(k)}) for m in answered}
    held = {m["rec_id"]: m["references"] for m in answered}
    out["filled"] = (keep or (lambda c, r: sift.write_filled(folder, c, r)))(cells, held) if answered else 0
    return out


def citation_plan(folder) -> dict:
    """What Find citation counts would ask about for a screening made before, before anything is asked:
    its records with a DOI, in the CSV's order, `of` of them, and `records` in all. Only reads."""
    sc = sift.load(folder)
    ids = [rec for rec in sc.ids if asked_doi(norm_doi(sc.cell(rec, "doi")))]
    return {"ids": ids, "of": len(ids), "records": len(sc.ids)}


def find_citations(folder, at: int = 0, ctx: Context | None = None, keep=None) -> dict:
    """Find citation counts, for a screening made before (12 October): the next BATCH of its records with
    a DOI from `at`, in the CSV's order, asked of OpenAlex in one request for their `cited_by_count`,
    and each count found written with today's date into Sift's own `cited_by` and `cited_by_date`
    through `keep`, which takes the counts by rec_id and the day, `sift.write_cited` when not given.
    The asking is done before the screening's lock is taken. The answer says where the next batch
    starts, `at`, how many records with a DOI there are, `of`, and how many this batch filled,
    `filled`, or `said`, one line when OpenAlex did not answer."""
    ctx = ctx or Context()
    plan = citation_plan(folder)
    at = max(0, int(at or 0))
    part = plan["ids"][at:at + BATCH]
    out = {"at": at + len(part), "of": plan["of"], "records": plan["records"], "asked": len(part), "filled": 0, "said": ""}
    if not part:
        return out
    sc = sift.load(folder)
    dois = {rec: norm_doi(sc.cell(rec, "doi")) for rec in part}
    try:
        found = works_by_doi(ctx, list(dois.values()), CITED_FIELDS)
    except SearchError as e:
        return dict(out, said=ctx.scrub(str(e)))
    counts = {rec: cited_count(found.get(doi)) for rec, doi in dois.items()}
    counts = {rec: c for rec, c in counts.items() if c is not None}
    day = today().isoformat()
    out["filled"] = (keep or (lambda got, when: sift.write_cited(folder, got, when)))(counts, day) if counts else 0
    return out


TITLE_FIELDS = "id,doi,display_name"


def paper_title(doi, ctx: Context | None = None) -> dict:
    """A benchmark paper's title found from its DOI (12 October, later), asked of OpenAlex in one
    request when he adds the DOI on the Search strategy screen: `{doi, title, said}`, `said` one line
    when the DOI is not one or OpenAlex does not know it or does not answer. Nothing is written here:
    the screen keeps the title in the plan's `benchmark_titles` as it saves."""
    d = norm_doi(doi)
    if not DOI.match(d) or not asked_doi(d):
        return {"doi": d, "title": "", "said": sift_words.t("sift_server.search.is_not_a_doi", d=d or sift_words.t("sift_server.search.that"))}
    ctx = ctx or Context()
    try:
        found = works_by_doi(ctx, [d], TITLE_FIELDS)
    except SearchError as e:
        return {"doi": d, "title": "", "said": ctx.scrub(str(e))}
    w = found.get(d) or {}
    title = one_line(sift.plain(w.get("display_name") or w.get("title") or ""))[:240]
    return {"doi": d, "title": title, "said": "" if title else sift_words.t("sift_server.search.openalex_does_not_know_that")}


# ------------------------------------------------------------------ the key works

# The review's key works (13 October): works the studies it seeks would cite, the Cites key works column
# showing which records cite each. They are kept in `search_plan.json` beside the versions, never in one,
# so an edit never makes a draft version to register again, and each is its OpenAlex ID where OpenAlex
# holds it, its DOI where it has one, and the title and year he gave or OpenAlex's for a DOI. A record
# cites a key work by Crossref's references when Crossref holds any for it, and else by OpenAlex's (see
# `sift.cites_of`).
KEY_WORKS = "key_works"
KEY_TITLE_MAX = 300
# what the lookup asks OpenAlex for, and how many of a title's works it offers to pick from
WORK_FIELDS = "id,doi,display_name,publication_year,authorships,cited_by_count"
PICKS = 5


def clean_key_works(raw) -> list[dict]:
    """The key works as the plan file keeps them, from what the screen or a file sent: each its OpenAlex
    ID, W and its number, or empty, its DOI or empty, its title and its year, a work with none of an ID, a
    DOI or a title let go, and a work held already, by its ID, its DOI or its title and year, kept once."""
    out, seen = [], set()
    for k in raw if isinstance(raw, list) else []:
        if not isinstance(k, dict):
            continue
        kid = short_id(k.get("id"), "W")
        doi = norm_doi(k.get("doi"))
        doi = doi if DOI.match(doi) else ""
        title = one_line(sift.plain(k.get("title")))[:KEY_TITLE_MAX]
        year = year_of(k.get("year"))
        if not (kid or doi or title):
            continue
        marks = {m for m in (f"id:{kid}" if kid else "", f"doi:{doi}" if doi else "",
                             f"title:{sift.fold_title(title)}|{year}" if title else "") if m}
        if marks & seen:
            continue
        seen |= marks
        out.append({"id": kid, "doi": doi, "title": title, "year": year})
    return out


def key_works(folder) -> list[dict]:
    """The review's key works, in his order, none when the plan holds none or cannot be read. Only reads."""
    try:
        return list(read_file(folder).get(KEY_WORKS) or [])
    except SearchError:
        return []


def save_key_works(folder, rows, wait: float | None = None) -> dict:
    """The key works as the Plan's Key works part holds them, written to `search_plan.json` beside its
    versions under the plan's lock, each once (see `clean_key_works`), no version touched, so a registered
    plan stays as it is. The answer is the plan as the screen draws it."""
    if not isinstance(rows, list):
        raise SearchError(sift_words.t("sift_server.search.the_key_works_are_a"))
    with locks.held(lock_path(folder), wait):
        data = read_file(folder)
        data[KEY_WORKS] = clean_key_works(rows)
        write_file(folder, data)
        return state(folder, data)


def work_pick(w: dict) -> dict:
    """One OpenAlex work as Add a key work offers it to pick: its ID, DOI, title, year, first authors and
    count of citations."""
    names = author_names(openalex_authors(w))
    authors = ", ".join(names) if len(names) <= 3 else f"{', '.join(names[:3])} and {len(names) - 3} more"
    return {"id": short_id(w.get("id"), "W"), "doi": norm_doi(w.get("doi")),
            "title": one_line(sift.plain(w.get("display_name") or w.get("title") or ""))[:KEY_TITLE_MAX],
            "year": str(w.get("publication_year") or ""), "authors": authors, "cited": cited_count(w)}


def find_works(text, ctx: Context | None = None) -> dict:
    """Add a key work's lookup (13 October), asked of OpenAlex when he gives a DOI or a title on the Plan:
    a DOI by itself, and a title in OpenAlex's search of works, its first PICKS works to pick from, each
    with its title, year, first authors and count of citations. `said` is one line when there is nothing
    to offer or OpenAlex does not answer. Nothing is written here."""
    raw = one_line(text)
    d = norm_doi(raw)
    ctx = ctx or Context()
    if DOI.match(d):
        if not asked_doi(d):
            return {"doi": d, "works": [], "said": sift_words.t("sift_server.search.is_not_a_doi", d=d)}
        try:
            found = works_by_doi(ctx, [d], WORK_FIELDS)
        except SearchError as e:
            return {"doi": d, "works": [], "said": ctx.scrub(str(e))}
        w = found.get(d)
        return {"doi": d, "works": [work_pick(w)] if w else [], "said": "" if w else sift_words.t("sift_server.search.openalex_does_not_know_that")}
    if not raw:
        return {"doi": "", "works": [], "said": sift_words.t("sift_server.search.give_a_doi_or_a")}
    try:
        data = get(ctx, ctx.base["openalex"], openalex_params(ctx, {"search": raw[:KEY_TITLE_MAX], "per-page": PICKS,
                                                                    "select": WORK_FIELDS}))
    except SearchError as e:
        return {"doi": "", "works": [], "said": ctx.scrub(str(e))}
    works = [work_pick(w) for w in (data.get("results") or [])[:PICKS] if isinstance(w, dict)]
    return {"doi": "", "works": works, "said": "" if works else sift_words.t("sift_server.search.openalex_found_no_work_of")}


# ----------------------------------------------------------------- the exports

def read_ris(text: str, source: str) -> list[dict]:
    """The records of a RIS export: TY, TI or T1, AU or A1, PY or Y1, AB, DO, JO, JF or T2, KW, and LA,
    its language since 14 October, a line that carries no tag joined to the one before it."""
    out, cur, last = [], {}, None
    for line in text.splitlines():
        m = re.match(r"^([A-Z][A-Z0-9])  -(?: (.*))?$", line.rstrip("\r"))
        if not m:
            if last and line.strip() and cur.get(last):
                cur[last][-1] = (cur[last][-1] + " " + line.strip()).strip()
            continue
        tag, val = m.group(1), (m.group(2) or "").strip()
        if tag == "ER":
            if cur:
                first = lambda *tags: next((cur[t][0] for t in tags if cur.get(t)), "")
                many = lambda *tags: next((cur[t] for t in tags if cur.get(t)), [])
                ty = first("TY")
                doi = first("DO") or next((u for u in cur.get("UR", []) if "doi.org/" in u.lower()), "")
                out.append(record(source, first("AN", "ID", "U2"), first("TI", "T1"), "; ".join(many("AU", "A1")),
                                  first("PY", "Y1", "DA"), first("JO", "JF", "T2", "JA", "SO"), doi,
                                  " ".join(many("AB", "N2")), first("M3") or RIS_TYPES.get(ty.upper(), ty),
                                  "; ".join(cur.get("KW", [])), language=cur.get("LA", [])))
            cur, last = {}, None
            continue
        cur.setdefault(tag, []).append(val)
        last = tag
    return [r for r in out if r["title"]]


# each field's column by the names the databases give it, the first found taken, EBSCO's newer
# export's `publicationDate` and `plink`, its link to the record, and never its `publisher` as a
# journal, since a publisher is not one
CSV_NAMES = {"title": ("title", "article title", "document title", "ti"),
             "authors": ("authors", "author", "author full names", "author(s)", "au"),
             "year": ("year", "publication year", "py", "publication date", "publicationdate", "date"),
             "journal": ("source title", "journal", "journal title", "publication title", "publication", "source", "so"),
             "doi": ("doi", "do", "digital object identifier"),
             "abstract": ("abstract", "ab"),
             "pub_type": ("document type", "publication type", "type", "dt"),
             "keywords": ("author keywords", "keywords", "subjects", "kw"),
             "url": ("url", "plink", "link"), "language": ("language", "la", "language of original document")}


def read_csv_export(text: str, source: str) -> list[dict]:
    """The records of a CSV export, its columns found by the names the databases give them."""
    rows = list(csv.reader(io.StringIO(text, newline="")))
    if not rows:
        return []
    head = [one_line(h).lower() for h in rows[0]]
    at = {}
    for key, names in CSV_NAMES.items():
        for name in names:
            if name in head:
                at[key] = head.index(name)
                break
    if "title" not in at:
        return []
    pick = lambda row, key: row[at[key]] if key in at and at[key] < len(row) else ""
    return [record(source, "", pick(r, "title"), pick(r, "authors"), pick(r, "year"), pick(r, "journal"), pick(r, "doi"),
                   pick(r, "abstract"), pick(r, "pub_type"), pick(r, "keywords"), pick(r, "url"), pick(r, "language"))
            for r in rows[1:]
            if one_line(pick(r, "title"))]


BIB_ENTRY = re.compile(r"@\s*([A-Za-z]+)\s*[{(]")
BIB_TYPES = {"article": "journal article", "book": "book", "inbook": "book chapter", "incollection": "book chapter",
             "inproceedings": "conference paper", "conference": "conference paper", "phdthesis": "dissertation",
             "mastersthesis": "dissertation", "thesis": "dissertation", "techreport": "report", "report": "report",
             "online": "web page", "misc": "generic"}
# LaTeX's accent commands, each as the combining mark it puts over or under its letter
ACCENTS = {"'": "\u0301", "`": "\u0300", "^": "\u0302", '"': "\u0308", "~": "\u0303", "=": "\u0304", ".": "\u0307",
           "u": "\u0306", "v": "\u030c", "H": "\u030b", "c": "\u0327", "k": "\u0328", "r": "\u030a"}
LETTERS = {"ss": "\u00df", "o": "\u00f8", "O": "\u00d8", "aa": "\u00e5", "AA": "\u00c5", "ae": "\u00e6", "AE": "\u00c6",
           "oe": "\u0153", "OE": "\u0152", "l": "\u0142", "L": "\u0141", "i": "i", "j": "j"}


def latex_plain(text: str) -> str:
    """A BibTeX value as plain text: the accents put on their letters, `{\\'e}` and `\\'{e}` alike,
    the named letters, the escaped marks and the dashes, then the braces taken away."""
    s = str(text or "")
    s = re.sub(r"\{\\([A-Za-z]{1,2})\}", lambda m: LETTERS.get(m.group(1), m.group(0)), s)
    s = re.sub(r"\\([A-Za-z]{1,2})(?![A-Za-z])\s?", lambda m: LETTERS.get(m.group(1), m.group(0)), s)

    def accent(m) -> str:
        mark, letter = m.group(1), m.group(2) or m.group(3) or ""
        letter = letter[1:] if letter.startswith("\\") else letter       # a dotless i or j, \i or \j
        return unicodedata.normalize("NFC", letter + ACCENTS[mark]) if letter else m.group(0)

    s = re.sub(r"\\([\'`^\"~=.])\s*(?:\{(\\?[A-Za-z])\}|(\\?[A-Za-z]))", accent, s)
    s = re.sub(r"\\([uvHckr])\s*(?:\{(\\?[A-Za-z])\}|\s(\\?[A-Za-z]))", accent, s)
    s = re.sub(r"\\([&%$#_{}])", r"\1", s)
    s = s.replace("---", "\u2014").replace("--", "\u2013").replace("~", " ")
    s = re.sub(r"\\[A-Za-z]+\s*", "", s)
    return one_line(s.replace("{", "").replace("}", ""))


def bib_value(text: str, at: int) -> tuple[str, int]:
    """One field's value from `at`: in braces, nested braces kept, in double quotes, or a bare word
    or number, with `#` joining parts. Its text and where it ends."""
    parts = []
    n = len(text)
    while at < n:
        while at < n and text[at].isspace():
            at += 1
        if at < n and text[at] == "{":
            depth, start = 0, at
            while at < n:
                if text[at] == "{" and text[at - 1:at] != "\\":
                    depth += 1
                elif text[at] == "}" and text[at - 1:at] != "\\":
                    depth -= 1
                    if depth == 0:
                        break
                at += 1
            parts.append(text[start + 1:at])
            at += 1
        elif at < n and text[at] == '"':
            start = at = at + 1
            depth = 0
            while at < n and not (text[at] == '"' and depth == 0 and text[at - 1] != "\\"):
                depth += {"{": 1, "}": -1}.get(text[at], 0)
                at += 1
            parts.append(text[start:at])
            at += 1
        else:
            m = re.match(r"[^,}\)#\s]+", text[at:])
            parts.append(m.group(0) if m else "")
            at += len(m.group(0)) if m else 0
        while at < n and text[at].isspace():
            at += 1
        if at < n and text[at] == "#":
            at += 1
            continue
        break
    return "".join(parts), at


def read_bib(text: str, source: str) -> list[dict]:
    """The records of a BibTeX export: each entry's title, its authors split on " and ", its year or
    date, journal or the book or proceedings it is in, DOI, or a doi.org address under url, abstract,
    keywords and language, the LaTeX of each undone. Comments, strings and preambles are passed over."""
    out, pos, n = [], 0, len(text)
    while True:
        m = BIB_ENTRY.search(text, pos)
        if not m:
            break
        kind = m.group(1).lower()
        pos = at = m.end()
        if kind in ("comment", "string", "preamble"):
            continue
        key = re.match(r"\s*([^,\s]*)\s*,", text[at:])
        at += key.end() if key else 0
        fields = {}
        while at < n:
            f = re.match(r"\s*([A-Za-z][\w:.-]*)\s*=\s*", text[at:])
            if not f:
                break
            value, at = bib_value(text, at + f.end())
            fields[f.group(1).lower()] = latex_plain(value)
            while at < n and text[at] in " \t\r\n,":
                at += 1
            if at < n and text[at] in "})":
                break
        pos = max(pos, at)
        authors ="; ".join(one_line(a) for a in re.split(r"\s+and\s+", fields.get("author", "")) if one_line(a))
        url = fields.get("url", "")
        doi = fields.get("doi") or (url if "doi.org/" in url.lower() else "")
        kws = "; ".join(k.strip() for k in re.split(r"[;,]", fields.get("keywords", "")) if k.strip())
        out.append(record(source, key.group(1) if key else "", fields.get("title", ""), authors,
                          fields.get("year") or fields.get("date", ""),
                          fields.get("journal") or fields.get("journaltitle") or fields.get("booktitle", ""),
                          doi, fields.get("abstract", ""), BIB_TYPES.get(kind, kind), kws,
                          language=fields.get("language", "")))
    return [r for r in out if r["title"]]


EXPORT_KINDS = ("ris", "csv", "bib")


def read_export(data: bytes, name: str, source: str) -> tuple[str, list[dict]]:
    """A dropped export read as RIS, BibTeX or CSV, whichever it is: its kind, `ris`, `bib` or `csv`,
    and its records."""
    raw = bytes(data)
    if raw[:2] in (b"\xff\xfe", b"\xfe\xff"):
        text = raw.decode("utf-16", "replace")
    else:
        try:
            text = raw.decode("utf-8-sig")
        except UnicodeDecodeError:
            text = raw.decode("latin-1")
    if re.search(r"^TY  -", text, re.M):
        return "ris", read_ris(text, source)
    if str(name or "").lower().endswith(".ris"):
        return "ris", []
    if str(name or "").lower().endswith(".bib") or re.match(r"\s*(?:%[^\n]*\n\s*)*@\s*[A-Za-z]+\s*[{(]", text):
        return "bib", read_bib(text, source)
    return "csv", read_csv_export(text, source)


# ------------------------------------------------------------------- the merge

def near_years(year: str) -> list[str]:
    """A year and the years one either side, the year itself first, for matching a title across two
    databases' dates of one item. A year that is not a number is matched as it is."""
    y = str(year or "").strip()
    return [y, str(int(y) - 1), str(int(y) + 1)] if y.isdigit() else [y]


# the types that say no more than that a record is a paper, which a more telling type stands before
PLAIN_TYPES = {"", "article", "journal article", "journal-article", "article-journal", "research article",
               "research-article", "journal", "academic journal", "peer reviewed journal", "text", "other"}


def fuller_title(a: str, b: str) -> str:
    """Of two titles of one record, one not in capitals throughout, then the one of more words, which
    keeps a subtitle, else the first."""
    if not a or not b:
        return a or b
    if a.isupper() != b.isupper():
        return b if a.isupper() else a
    words = lambda t: len(re.findall(r"\w+", t))
    return b if words(b) > words(a) else a


def abbreviates(short: str, full: str) -> bool:
    """Whether one journal name is the other cut short, `J Psychoactive Drugs` of `Journal of
    Psychoactive Drugs`, each of its words the start of a later word of the full name, in order."""
    words = lambda t: re.findall(r"[a-z0-9]+", t.casefold())
    s, f = words(short), words(full)
    if not s or len(s) > len(f) or s == f:
        return False
    i = 0
    for w in f:
        if i < len(s) and w.startswith(s[i]):
            i += 1
    return i == len(s)


def fuller_journal(a: str, b: str) -> str:
    """Of two names of one journal, the full name over its abbreviation and one not in capitals
    throughout, else the first."""
    if not a or not b:
        return a or b
    if abbreviates(a, b):
        return b
    if a.casefold() == b.casefold() and a.isupper() and not b.isupper():
        return b
    return a


def telling_type(a: str, b: str) -> str:
    """Of two types of one record, the one that says more than that it is a paper, a thesis, a review
    or a chapter, else the first."""
    plain = lambda t: " ".join(str(t or "").casefold().split()) in PLAIN_TYPES
    return b if plain(a) and not plain(b) else (a or b)


def merge(records: list[dict], anchors=()) -> list[dict]:
    """The records of every database as one list: a record joins one with the same DOI, a version
    suffix aside, or else with the same title and a year at most one apart, its own year first, unless
    both carry DOIs that differ, as a thesis and its paper or two databases' dates of one item. A record
    with no year joins by its DOI, or else by its title alone when exactly one record carries that
    title and their DOIs do not differ, and stands apart when none or several do. Two versions of one
    DOI keep the shorter. `sources` names each database that found it, in the order of the run, and
    each field is the best any of them gives: the fullest list of authors, since Scopus gives only the
    first, the fullest list of keywords and the language by `LANGUAGE_ORDER` (14 October), the title
    not in capitals and with its subtitle, the journal's full name, the type that says most, the
    longest abstract, the year most of them give, the earliest on a tie, and a field one lacks taken
    from the next. `anchors`, an earlier run's records a later run follows,
    each stand first and alone, marked `kept`, never joined to one another and never given another's
    DOI, and a record of the run joins one by the same rules, its database added after the earlier
    run's and a field the earlier record lacks taken from it. `found` marks each record this run found."""
    merged, by_doi, by_title, by_name, later = [], {}, {}, {}, []
    years: dict[int, list[str]] = {}
    order: dict[str, int] = {}
    for r in records:
        order.setdefault(r["source"], len(order))

    def begin(r: dict) -> dict:
        m = {k: r.get(k, "") for k in ("title", "authors", "year", "journal", "doi", "abstract", "pub_type", "url", "keywords",
                                       "language")}
        m["sources"], m["abstract_from"] = [r["source"]], (r["source"] if r["abstract"] else "")
        m["language_from"] = r["source"] if m["language"] else ""
        m["found"] = True
        merged.append(m)
        years[id(m)] = [m["year"]] if m["year"] else []
        return m

    def join(m: dict, r: dict) -> None:
        m["found"] = True
        if r["source"] not in m["sources"]:
            m["sources"].append(r["source"])
        if not m.get("kept") and m["doi"] and r["doi"] and len(r["doi"]) < len(m["doi"]):
            m["doi"] = r["doi"]
        for f in ("title", "doi", "authors", "journal", "pub_type", "year", "url"):
            m[f] = m[f] or r.get(f, "")
        if not m.get("kept"):
            if len(author_names(r.get("authors"))) > len(author_names(m["authors"])):
                m["authors"] = r["authors"]
            m["title"] = fuller_title(m["title"], r.get("title", ""))
            m["journal"] = fuller_journal(m["journal"], r.get("journal", ""))
            m["pub_type"] = telling_type(m["pub_type"], r.get("pub_type", ""))
            if r.get("year"):
                years.setdefault(id(m), []).append(r["year"])
        if r["abstract"] and (not m["abstract"] or (not m.get("kept") and len(r["abstract"]) > len(m["abstract"]))):
            m["abstract"], m["abstract_from"] = r["abstract"], r["source"]
        kws = r.get("keywords") or ""
        if kws and (not m.get("keywords") or (not m.get("kept") and keyword_count(kws) > keyword_count(m["keywords"]))):
            m["keywords"] = kws
        # an earlier run's record keeps its language, and one it lacked is taken by the same order
        said = r.get("language") or ""
        ranked = not m.get("kept") or m.get("language_from")
        if said and (not m.get("language") or (ranked and language_rank(r["source"]) < language_rank(m.get("language_from")))):
            m["language"], m["language_from"] = said, r["source"]

    def held(m: dict) -> None:
        if m["doi"]:
            by_doi.setdefault(doi_key(m["doi"]), m)
        name = norm_title(m["title"])
        if name and m["year"]:
            by_title.setdefault(name + "|" + m["year"], m)
        if name and all(x is not m for x in by_name.get(name, [])):
            by_name.setdefault(name, []).append(m)

    differ = lambda m, r: bool(m["doi"] and r["doi"] and doi_key(m["doi"]) != doi_key(r["doi"]))
    for a in anchors:
        m = dict(a, sources=list(a["sources"]), kept=True, first=len(a["sources"]), found=False)
        merged.append(m)
        held(m)
    for r in records:
        m = by_doi.get(doi_key(r["doi"])) if r["doi"] else None
        if m is None and not r["year"]:
            later.append(r)
            continue
        if m is None and norm_title(r["title"]):
            for y in near_years(r["year"]):
                m = by_title.get(norm_title(r["title"]) + "|" + y)
                if m is not None and not differ(m, r):
                    break
                m = None
        if m is None:
            m = begin(r)
        else:
            join(m, r)
        held(m)
    for r in later:
        m = by_doi.get(doi_key(r["doi"])) if r["doi"] else None
        same = by_name.get(norm_title(r["title"]), []) if norm_title(r["title"]) else []
        if m is None and len(same) == 1 and not differ(same[0], r):
            m = same[0]
        if m is None:
            m = begin(r)
        else:
            join(m, r)
        held(m)
    # an earlier record with no year takes the one record of this run that carries its title, as a
    # record of the run with no year would join it
    for a in [m for m in merged if m.get("kept") and not m["year"] and norm_title(m["title"])]:
        same = [m for m in by_name.get(norm_title(a["title"]), []) if m is not a]
        if len(same) == 1 and not same[0].get("kept") and not differ(a, same[0]) and same[0] in merged:
            other = same[0]
            for s in other["sources"]:
                join(a, dict(other, source=s, abstract=""))
            if not a["abstract"] and other["abstract"]:
                a["abstract"], a["abstract_from"] = other["abstract"], other["abstract_from"]
            merged.remove(other)
    for m in merged:
        if m.get("kept"):
            m["sources"][m["first"]:] = sorted(m["sources"][m["first"]:], key=lambda s: order.get(s, len(order)))
        else:
            m["sources"].sort(key=lambda s: order.get(s, len(order)))
            seen = years.get(id(m)) or []
            if len(set(seen)) > 1:
                m["year"] = min(set(seen), key=lambda y: (-seen.count(y), y))
    return merged


# the order a merged record's language is kept in where its databases give different ones (14 October):
# a record's own metadata, PubMed's, Europe PMC's, PsycInfo's, Web of Science's and Scopus's, then any
# other database's, before OpenAlex's, which OpenAlex detects from the text
LANGUAGE_ORDER = tuple(NAMES[s] for s in ("pubmed", "epmc", "psycinfo", "wos", "scopus"))


def language_rank(source) -> int:
    """Where a database stands in `LANGUAGE_ORDER`, any other after them, OpenAlex last and none after it."""
    if source in LANGUAGE_ORDER:
        return LANGUAGE_ORDER.index(source)
    if source == NAMES["openalex"]:
        return len(LANGUAGE_ORDER) + 1
    return len(LANGUAGE_ORDER) if source else len(LANGUAGE_ORDER) + 2


def ordered(merged: list[dict]) -> list[dict]:
    """The merged records in year and title order, each given its rec_id, R001 up."""
    out = sorted(merged, key=lambda m: (m["year"], sift.plain(m["title"]).lower(), m["doi"]))
    width = max(3, len(str(len(out))))
    for n, m in enumerate(out, 1):
        m["rec_id"] = f"R{str(n).zfill(width)}"
    return out


def screening_text(merged: list[dict]) -> str:
    """The screening's CSV, with a `url` column after the rest when a record carries a link, as an
    export with no DOIs gives one, then Sift's own columns of 13 October, and the language at the end, where
    the review's own side adds it (14 October)."""
    out = io.StringIO(newline="")
    w = csv.writer(out, lineterminator="\r\n")
    columns = COLUMNS + (["url"] if any(m.get("url") for m in merged) else []) + OWN_AFTER + [sift.LANGUAGE_COLUMN]
    w.writerow(columns)
    for m in merged:
        row = dict({c: "" for c in columns}, **{k: m.get(k, "") for k in WRITTEN if k in columns})
        row["sources"] = "; ".join(m["sources"])
        w.writerow([row[c] for c in columns])
    return out.getvalue()


def log_text(rows: list[dict]) -> str:
    out = io.StringIO(newline="")
    w = csv.DictWriter(out, fieldnames=LOG_COLUMNS, lineterminator="\r\n")
    w.writeheader()
    for r in rows:
        w.writerow({c: r.get(c, "") for c in LOG_COLUMNS})
    return out.getvalue()


# ------------------------------------------------------------------- the runs

def run_path(folder, day: str) -> Path:
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_.-]{0,40}", str(day or "")) or ".." in str(day):
        raise SearchError(sift_words.t("sift_server.search.cannot_name_a_run_folder", day=day))
    return runs_path(folder) / str(day)


def run_said(name, folder=None) -> str:
    """A run as a line names it. With its review's folder, as the screens name it, by its number in the
    order the runs were made and its day, Run 3, 12 October 2026 (12 October, later), a run not made yet
    by the number it will take (see `run_numbers`). With none, as the command line and its refusals
    name it beside its folder, by its day and its number that day, 9 October 2026, run 2. A folder of
    another name as it stands."""
    day, n = run_parts(name)
    if folder is not None:
        numbers = run_numbers(folder)
        return f"Run {numbers.get(str(name)) or max(numbers.values(), default=0) + 1}, {day_said(day)}"
    return f"{day_said(day)}, run {n}" if n > 1 else day_said(day)


def draft_said(version) -> str:
    """The words that mark a run of a version not yet registered, as they stand after a run's name."""
    return f"draft version {version}, unregistered"


def review_of_run(run_dir: Path) -> Path | None:
    """The review folder a run folder sits in, the folder above its `runs/`, or None."""
    run_dir = Path(run_dir)
    return run_dir.parent.parent if run_dir.parent.name == RUNS_DIR else None


def run_title(run_dir: Path) -> str:
    """A run's name in words with its mark when its version was a draft: Run 3, 9 October 2026, draft
    version 3, unregistered."""
    meta = read_run(run_dir)
    said = run_said(Path(run_dir).name, review_of_run(run_dir))
    return f"{said}, {draft_said(meta['version'])}" if meta.get("draft") and meta.get("version") else said


# each run's number in the order the runs were made, kept by its folder's name (12 October, later)
NUMBERS_NAME = "numbers.json"


def held_numbers(folder) -> dict:
    """The numbers `runs/numbers.json` keeps, each a run folder's name and its number, or none."""
    try:
        held = json.loads((runs_path(folder) / NUMBERS_NAME).read_text(encoding="utf-8"))
    except (OSError, ValueError, UnicodeDecodeError):
        return {}
    if not isinstance(held, dict):
        return {}
    return {str(k): v for k, v in held.items() if isinstance(v, int) and not isinstance(v, bool) and v > 0}


def run_numbers(folder) -> dict:
    """Each run's number, Run 1 up in the order the runs were made, by its folder's name: those
    `runs/numbers.json` keeps, then each run it does not hold yet after the highest, in the order made.
    A number kept stays its run's, so a run removed by hand never moves a later run's number. Only
    reads."""
    numbers = held_numbers(folder)
    top = max(numbers.values(), default=0)
    for p in reversed(run_dirs(folder)):
        if p.name not in numbers:
            top += 1
            numbers[p.name] = top
    return numbers


def keep_numbers(folder) -> None:
    """`runs/numbers.json` written as a run folder is made, so each run's number is kept from then on,
    and only when a run it does not hold is there. The caller holds the folder's lock."""
    numbers = run_numbers(folder)
    if numbers != held_numbers(folder):
        write_text(runs_path(folder) / NUMBERS_NAME, json.dumps(numbers, indent=1) + "\n")


def day_run(folder, day: str) -> Path | None:
    """The newest run of a day, the one an export dropped that day goes to, or None."""
    return next((p for p in run_dirs(folder) if run_parts(p.name)[0] == day), None)


def next_run(folder, day: str) -> str:
    """The folder name a new run of `day` takes: the day itself while nothing has that name, else the
    number after the day's highest, `<day>-2` up."""
    run_path(folder, day)
    base = runs_path(folder)
    if not (base / day).exists():
        return day
    n = max([run_parts(p.name)[1] for p in run_dirs(folder) if run_parts(p.name)[0] == day] + [1]) + 1
    while (base / f"{day}-{n}").exists():
        n += 1
    return f"{day}-{n}"


def waits_for_run(meta: dict) -> bool:
    """Whether a run is one a dropped export began and Run has not yet run: marked so when the export
    began it, or, in a folder from before the mark, with a database still waiting for Run."""
    return meta.get("waiting_for_run") is True or any(
        isinstance(s, dict) and s.get("state") == "waiting" for s in (meta.get("sources") or {}).values())


def run_target(folder, day: str, v: dict) -> str:
    """The run folder a run of version `v` on `day` writes: the day's newest run when a dropped export
    began it and Run has not yet run it, of the same version, its screening not begun, else a new run,
    the day's next. A run written before is never written again."""
    last = day_run(folder, day)
    if last is not None:
        meta = read_run(last)
        if waits_for_run(meta) and meta.get("version") == v["version"] and not begun(last):
            return last.name
    return next_run(folder, day)


def begun(run_dir: Path) -> str:
    """Why a run folder's screening may not be replaced, or empty: a decision or a proposal in its
    CSV, its log, or a PDF kept for a record. A run that follows an earlier one is begun only by what
    came after its carry, a line of the log, a PDF or a change to its CSV, while the carry's log is
    there, and once its screening is started again, its log gone to `_Archive/`, as any other run."""
    carried = read_run(run_dir).get("carried")
    if isinstance(carried, dict) and (run_dir / sift.LOG_NAME).exists():
        return changed_since(run_dir, carried)
    if (run_dir / sift.LOG_NAME).exists():
        return sift_words.t("sift_server.search.its_screening_log")
    # a PDF found in an earlier run, unchanged since, is no work on this screening (see `sift.own_pdfs`)
    if sift.own_pdfs(run_dir):
        return "PDFs"
    path = run_dir / sift.CSV_NAME
    if path.is_file():
        try:
            rows = list(csv.DictReader(io.StringIO(path.read_bytes().decode("utf-8-sig"), newline="")))
        except (OSError, UnicodeDecodeError, csv.Error):
            return sift_words.t("sift_server.search.a_screening_csv_sift_cannot")
        filled = lambda cols: any(one_line(r.get(c)) for r in rows for c in cols)
        if filled(sift.DECISION_COLUMNS):
            return "screening decisions"
        if filled(sift.PROPOSAL_COLUMNS + sift.AI_PROPOSAL_COLUMNS):
            return "proposals"
    return ""


def refuse_begun(run_dir: Path) -> None:
    why = begun(run_dir)
    if why:
        raise SearchError(sift_words.t("sift_server.search.the_run_of_holds_so", name=run_said(run_dir.name), why=why))


def read_run(run_dir: Path) -> dict:
    try:
        data = json.loads((run_dir / RUN_FILE).read_text(encoding="utf-8"))
        return data if isinstance(data, dict) else {}
    except (OSError, ValueError, UnicodeDecodeError):
        return {}


def read_log(run_dir: Path) -> list[dict]:
    try:
        return [dict(r) for r in csv.DictReader(io.StringIO((run_dir / sift.SEARCHES_NAME).read_bytes().decode("utf-8-sig"),
                                                             newline=""))]
    except (OSError, UnicodeDecodeError, csv.Error):
        return []


def export_file(run_dir: Path, source: str) -> Path | None:
    for ext in EXPORT_KINDS:
        p = run_dir / f"{source}.{ext}"
        if p.is_file():
            return p
    return None


def pick_version(data: dict, which) -> dict:
    """The version a run takes: `None` the newest registered, `draft` the newest draft, `newest` the
    newest of either, or a number."""
    last = newest(data)
    if last is None:
        raise SearchError(sift_words.t("sift_server.search.there_is_no_search_plan"))
    if which is None:
        v = registered_of(data)
        if v is None:
            raise SearchError(sift_words.t("sift_server.search.no_version_of_the_plan"))
        return v
    if which == "draft":
        if last.get("registered"):
            raise SearchError(sift_words.t("sift_server.search.there_is_no_draft_version", version=last['version']))
        return last
    if which == "newest":
        return last
    v = version_of(data, int(which))
    if v is None:
        raise SearchError(sift_words.t("sift_server.search.there_is_no_version", which=which))
    return v


def benchmark_said(plan: dict, dois: set[str]) -> tuple[list[str], str]:
    """The benchmark's DOIs not among `dois`, a version suffix aside as the merge sets it aside, and
    the words a note gives them, empty with no benchmark."""
    if not plan["benchmark"]:
        return [], ""
    keys = {doi_key(d) for d in dois}
    missed = [d for d in plan["benchmark"] if doi_key(d) not in keys]
    found = len(plan["benchmark"]) - len(missed)
    said = f"benchmark {found} of {len(plan['benchmark'])}"
    return missed, said + (f", missed {', '.join(missed)}" if missed else "")


NO_DOIS = "No DOIs in this export"


def source_benchmark(plan: dict, recs: list[dict], every: list[dict], export: bool = False) -> str:
    """One database's benchmark words for its line in `log.csv`. A benchmark DOI counts as found when
    one of its records carries it, or when one of its records with no DOI carries the title of a
    record of the run that does. An export whose records carry no DOI at all and match none of the
    benchmark by title says so, and names none as missed."""
    if not plan["benchmark"]:
        return ""
    titled: dict[str, set] = {}
    for r in every:
        if r.get("doi") and norm_title(r.get("title")):
            titled.setdefault(doi_key(r["doi"]), set()).add(norm_title(r["title"]))
    dois = {r["doi"] for r in recs if r.get("doi")}
    bare = {norm_title(r.get("title")) for r in recs if not r.get("doi")} - {""}
    found = dois | {d for d in plan["benchmark"] if titled.get(doi_key(d), set()) & bare}
    missed, said = benchmark_said(plan, found)
    if export and recs and not dois and len(missed) == len(plan["benchmark"]):
        return NO_DOIS
    return said


def plan_for_run(folder, which) -> tuple[dict, dict, dict]:
    data = read_file(folder)
    v = pick_version(data, which)
    plan = clean_plan(v["plan"])
    said = ready(v, plan)
    if said:
        raise SearchError(*said)
    return data, v, plan


# ------------------------------------------------------------ following an earlier run

NONE = "none"
# the bibliographic cells of a carried record, each filled from this run only where the earlier is empty
CARRIED_CELLS = ("title", "authors", "year", "journal", "doi", "pub_type", "abstract", "abstract_from", "url",
                 sift.KEYWORDS_COLUMN, sift.LANGUAGE_COLUMN)


def csv_sha(run_dir: Path) -> str:
    return hashlib.sha256((run_dir / sift.CSV_NAME).read_bytes()).hexdigest()


def changed_since(run_dir: Path, carried: dict) -> str:
    """Why a run that follows an earlier one is begun, or empty: a line of its log after the carry's
    own, a PDF the carry did not copy, or its CSV changed since the carry wrote it."""
    log = run_dir / sift.LOG_NAME
    try:
        lines = sum(1 for line in log.read_text(encoding="utf-8").splitlines() if line.strip()) if log.is_file() else 0
    except (OSError, UnicodeDecodeError):
        return sift_words.t("sift_server.search.its_screening_log")
    if lines != carried.get("log"):
        return sift_words.t("sift_server.search.its_screening_log")
    if sift.own_pdfs(run_dir) != (carried.get("pdfs") or {}):
        return "PDFs"
    try:
        same = csv_sha(run_dir) == carried.get("csv")
    except OSError:
        return sift_words.t("sift_server.search.a_screening_csv_sift_cannot")
    return "" if same else sift_words.t("sift_server.search.a_screening_csv_changed_since")


def clear_carry(run_dir: Path, carried) -> None:
    """What a carry wrote into a run folder taken away, its log, the PDFs it copied and the settings,
    before the run is written afresh. Called only once `begun` has found nothing after the carry."""
    if not isinstance(carried, dict):
        return
    gone = [run_dir / sift.LOG_NAME] + ([run_dir / sift.SETTINGS_NAME] if carried.get("settings") else [])
    gone += [run_dir / sift.PDF_DIR / name for name in carried.get("pdfs") or {}]
    for p in gone:
        if p.is_file():
            p.unlink()


def follow_day(value) -> str | None:
    """The run a run follows, by its folder's name, from the screen, the command line or MCP, or None
    for none."""
    s = one_line(value)
    return None if not s or s.lower() == NONE else s


def decided_of(run_dir: Path) -> int:
    """How many of a run's records hold a decision at either stage, read without a write."""
    try:
        return sift.decided(run_dir) if sift.is_screening(run_dir) else 0
    except (sift.SiftError, OSError):
        return 0


def follow_choices(folder, name: str) -> list[dict]:
    """The earlier runs the screen offers the run `name` to follow: each run made before it whose
    screening holds a decision, newest first, an earlier run of the same day among them."""
    return [r for r in runs(folder) if run_parts(r["date"]) < run_parts(name) and r["screening"] and r.get("decided")]


def default_follows(folder, day: str | None = None) -> str | None:
    """The run a new run of `day` follows when none is named: the newest earlier run with decisions."""
    found = follow_choices(folder, next_run(folder, day or today().isoformat()))
    return found[0]["date"] if found else None


def check_follows(folder, name: str, follows) -> str | None:
    """The run the run `name` follows, by its folder's name, refused in one line when it is that run, a
    later one, or a run with no screening."""
    earlier = follow_day(follows)
    if earlier is None:
        return None
    path = run_path(folder, earlier)
    if earlier == name:
        raise SearchError(sift_words.t("sift_server.search.a_run_cannot_follow_itself"))
    if run_parts(earlier) > run_parts(name):
        raise SearchError(sift_words.t("sift_server.search.the_run_of_comes_after", earlier=run_said(earlier)))
    if not sift.is_screening(path):
        raise SearchError(sift_words.t("sift_server.search.the_run_of_holds_no", earlier=run_said(earlier)))
    return earlier


def follow_said(folder, earlier: str | None) -> dict | None:
    """The run a dry run would follow, its name in words, its records and how many are decided, or None."""
    if not earlier:
        return None
    path = run_path(folder, earlier)
    try:
        n = len(sift.load(path).ids)
    except (sift.SiftError, OSError):
        n = 0
    return {"date": earlier, "label": run_said(earlier, folder), "records": n, "decided": decided_of(path)}


def followed_lock(folder, follows: str | None, wait: float | None = None):
    """The lock of the run a run follows held while its screening is carried, when it has one, so a write
    there is never read half done. With none, nothing has ever written it and nothing is made."""
    lock = sift.lock_path(run_path(folder, follows)) if follows else None
    return locks.held(lock, wait) if lock is not None and lock.is_file() else contextlib.nullcontext()


@contextlib.contextmanager
def writing(folder, run_dir: Path, follows: str | None, wait: float | None = None):
    """A run folder's screening lock held for a drop, with the lock of the run it follows, both taken
    before anything in the run folder is removed or written (23 October). A lock another writer holds
    refuses with BUSY having touched nothing, the run folder as it was."""
    with locks.held(sift.lock_path(run_dir), wait), followed_lock(folder, follows, wait):
        yield


def anchors_of(sc) -> list[dict]:
    """An earlier screening's records as the merge takes them, each with its rec_id and sources."""
    out = []
    for rec in sc.ids:
        m = {k: sc.cell(rec, k).strip() for k in ("title", "authors", "year", "journal", "doi", "abstract", "pub_type",
                                                  "abstract_from", "url", sift.KEYWORDS_COLUMN, sift.LANGUAGE_COLUMN)
             + sift.FILLED}
        out.append(dict(m, rec_id=rec, sources=sift.sources_of(sc.cell(rec, "sources"))))
    return out


def numbered_on(fresh: list[dict], ids: list[str]) -> list[dict]:
    """A later run's new records in year and title order, each given the rec_id after the earlier
    run's highest, its letters and width kept."""
    out = sorted(fresh, key=lambda m: (m["year"], sift.plain(m["title"]).lower(), m["doi"]))
    names = sift.next_ids(ids, len(out)) or sift.next_ids(["R000"], len(out), set(ids)) or []
    for m, rec in zip(out, names):
        m["rec_id"] = rec
    return out


def carried_text(sc, kept: list[dict], fresh: list[dict]) -> str:
    """The later run's CSV: every record of the earlier, its cells as they stand but the decisions,
    which the log brings, with its sources joined and a cell it lacked taken from this run, Sift's own
    columns from OpenAlex and Crossref as this run filled them, his study among the cells as they stand,
    then the new records, every column of the earlier CSV kept after the screening's own."""
    columns = list(COLUMNS) + (["url"] if "url" in sc.header or any(m.get("url") for m in kept + fresh) else []) + OWN_AFTER
    columns += [h for h in sc.header if h not in columns]
    # the language where the earlier CSV holds it, the review's own side's or a run's, else at the end
    columns += [sift.LANGUAGE_COLUMN] if sift.LANGUAGE_COLUMN not in columns else []
    out = io.StringIO(newline="")
    w = csv.writer(out, lineterminator="\r\n")
    w.writerow(columns)
    for m in kept:
        row = dict({c: "" for c in columns}, **sc.record(m["rec_id"]))
        for f in CARRIED_CELLS:
            if not row.get(f, "").strip() and m.get(f):
                row[f] = m[f]
        for f in sift.FILLED:
            if m.get(f):
                row[f] = m[f]
        row["sources"] = "; ".join(m["sources"])
        row.update({c: "" for c in sift.DECISION_COLUMNS})
        w.writerow([row.get(c, "") for c in columns])
    for m in fresh:
        row = dict({c: "" for c in columns}, **{k: m.get(k, "") for k in WRITTEN})
        row["sources"] = "; ".join(m["sources"])
        w.writerow([row[c] for c in columns])
    return out.getvalue()


def last_line(lines: list[dict], rec: str, field: str) -> dict | None:
    """The newest line of a log that set one of his fields on a record, by hand or by a carry, his study
    by the link or unlink that moved it (13 October)."""
    for e in reversed(lines):
        if str(e.get("rec_id")) == rec and e.get("field") == field and e.get("act") in ("field", "carry"):
            return e
        if field == sift.STUDY_COLUMN and e.get("act") == "study" and (str(e.get("rec_id")) == rec or sift.names_record(e, rec)):
            return e
    return None


def carry_log(run_dir: Path, earlier: Path, sc, day: str, kept: list[dict], fresh: list[dict]) -> int:
    """The carry, through `sift.append` into the later run's fresh log: a `follow` line naming the
    earlier run, the records carried, those new and those found again, then for each record carried
    a `carry` line for each stage it stands at, its decision, reason and note and the proposal it
    stood against, and one for each of his fields that holds a value, each naming the earlier run's
    day and the line of its log it comes from, or none where only its CSV held it. The answer is the
    number of lines written."""
    entries = sift.read_log(earlier)
    held = sift.states(entries)
    lines = sift.read_lines(earlier)
    n = 0

    def add(entry: dict) -> None:
        nonlocal n
        n += 1
        sift.append(run_dir, dict({"n": n, "at": now_iso()}, **entry, tool=sift.TOOL))

    add({"act": "follow", "run": day, "records": [m["rec_id"] for m in kept], "new": [m["rec_id"] for m in fresh],
         "again": [m["rec_id"] for m in kept if m.get("found")]})
    for m in kept:
        rec = m["rec_id"]
        for stage in sift.STAGES:
            st = sift.state_of(sc, held, rec, stage)
            if not (st["decision"] or st["note"]):
                continue
            last = held.get((rec, stage))
            add({"act": "carry", "rec_id": rec, "stage": sift.STAGE_WORDS[stage], "decision": st["decision"],
                 "reason": st["reason"], "note": st["note"], "proposal": sift.proposal_seen(sc, held, rec, stage),
                 "was": {"decision": "", "reason": "", "note": ""},
                 "from": {"run": day, "n": last.get("n") if last else None, "at": st["at"]}})
        for name in sc.header:
            value = sc.cell(rec, name)
            if sift.is_own(name) and value.strip():
                last = last_line(lines, rec, name)
                add({"act": "carry", "rec_id": rec, "field": name, "was": "", "value": value,
                     "from": {"run": day, "n": last.get("n") if last else None}})
    return n


def carry(folder, run_dir: Path, day: str, records: list[dict], ctx: Context) -> dict:
    """A later run's screening written from the earlier run it follows, read under its lock and never
    written: the records merged with the earlier ones as anchors, the CSV, the log of the carry and the
    CSV's decisions rebuilt from it, his settings and the PDFs copied. The answer is what `run.json`
    keeps of it. The caller holds both runs' locks (see `writing`)."""
    earlier = run_path(folder, day)
    sc = sift.load(earlier)
    merged = merge(records, anchors=anchors_of(sc))
    kept = [m for m in merged if m.get("kept")]
    fresh = [m for m in merged if not m.get("kept")]
    # a record carried from the earlier run is never changed or asked about, so only the new ones are filled,
    # Fill from OpenAlex filling a carried one's own columns where it lacks them, and the references go with it
    got = fill_from_openalex(ctx, fresh)
    fresh = numbered_on(fresh, sc.ids)
    refs = {m["rec_id"]: dict(sift.references(earlier).get(m["rec_id"]) or {}, **(m.get("references") or {}))
            for m in kept}
    refs.update({m["rec_id"]: m["references"] for m in fresh if m.get("references")})
    settings = sift.read_settings(earlier)
    pdfs = {m["rec_id"]: sift.pdf_path(earlier, m["rec_id"]) for m in kept}
    write_text(run_dir / sift.CSV_NAME, ctx.scrub(carried_text(sc, kept, fresh)))
    sift.write_references(run_dir, {k: v for k, v in refs.items() if v})
    lines = carry_log(run_dir, earlier, sc, day, kept, fresh)
    sift.rebuild(sift.load(run_dir), sift.read_log(run_dir))
    if settings:
        sift.write_settings(run_dir, settings)
    copied = {}
    for rec, src in pdfs.items():
        if src is None:
            continue
        (run_dir / sift.PDF_DIR).mkdir(exist_ok=True)
        target = run_dir / sift.PDF_DIR / f"{rec}.pdf"
        fd, tmp = tempfile.mkstemp(dir=str(target.parent), prefix=f".{target.name}.", suffix=".tmp")
        os.chmod(tmp, 0o644)
        with os.fdopen(fd, "wb") as fh:
            fh.write(src.read_bytes())
        os.replace(tmp, target)
        copied[target.name] = target.stat().st_size
    searched = read_log(earlier)
    return {"merged": kept + fresh, "filled": got["abstracts"], "authors_filled": got["authors"], "cited_filled": got["cited"],
            "openalex_filled": got["openalex"], "crossref_filled": got["crossref"],
            "searched": searched,
            "follows": {"date": day, "carried": len(kept), "new": len(fresh), "again": sum(1 for m in kept if m.get("found"))},
            "carried": {"log": lines, "pdfs": copied, "settings": bool(settings)}}


def by_api(run_dir: Path, source: str, how: str) -> bool:
    """Whether a run searches a database by its API: by API where its list or its default says so, unless an
    export of it waits in the run folder, which a database Sift searches with no key never takes."""
    dropped = (source not in KEYLESS or how == "export") and export_file(run_dir, source) is not None
    return how == "api" and not dropped and source in RUNNERS


def run(folder, which=None, day: str | None = None, sources=None, progress=None, ctx: Context | None = None,
        dry_run: bool = False, wait: float | None = None, listed=None, follows=None, check_terms: bool = False) -> dict:
    """A run of a version of the plan, a new run folder written whole, `runs/<day>/`, or for a later
    run that day `runs/<day>-2/` and up: each database searched by its API where Sift has one and its
    key is set, an export already in the folder taken in for the rest, then the records merged into
    `screening.csv` beside `log.csv`, `raw_<source>.json`, `reasons.csv` and `run.json`. A run a dropped
    export began that day, not yet run, is the one completed (see `run_target`), and no run written
    before is written again. With the user's own list, `listed`, a database it does not hold, or holds
    by export, goes by export. `progress(source, said)` hears each database start and end. `dry_run`
    says how each would go and sends nothing. `follows`, an earlier run's folder name, carries that
    run's screening into this one (see `carry`), refused when it is this run, a later one or a run
    with no screening, and None or `none` carries nothing. With `check_terms`, as the command line, MCP
    and the screen run, the truncation check comes first (see `truncation_check`): a dry run answers its
    table as `terms`, sending those counts alone, and a run writes it to TERMS_NAME in the run folder and
    its flags to `run.json` before any database is searched, each database checked heard as `checking`."""
    ctx = ctx or Context()
    day = day or today().isoformat()
    data, v, plan = plan_for_run(folder, which)
    name = run_target(folder, day, v)
    run_dir = run_path(folder, name)
    earlier = check_follows(folder, name, follows)
    chosen = [s for s in plan["databases"] if not sources or s in sources]
    have = keys_set()
    texts = {s["source"]: s for s in strings(plan)}
    if dry_run:
        out = {"dry_run": True, "date": name, "day": day, "label": run_said(name, folder), "version": v["version"],
               "draft": not v.get("registered"), "follows": follow_said(folder, earlier),
               "sources": [{"source": s, "name": name_of(s, plan), "how": how_of(s, have, listed),
                            "export": bool(export_file(run_dir, s)), "query": texts[s]["query"]} for s in chosen]}
        if check_terms:
            out["terms"] = truncation_check(plan, [s["source"] for s in out["sources"]
                                                   if by_api(run_dir, s["source"], s["how"])], ctx)
        return out
    with locks.held(lock_path(folder), wait):
        # chosen again under the folder's lock, so two runs at once never share a folder
        name = run_target(folder, day, v)
        run_dir = run_path(folder, name)
        earlier = check_follows(folder, name, follows)
        refuse_begun(run_dir)
        # the run's own screening lock taken before anything in its folder is removed (23 October), so a
        # run refused BUSY leaves the folder as it was. The run it follows is locked only while it is carried
        with locks.held(sift.lock_path(run_dir), wait):
            refuse_begun(run_dir)
            run_dir.mkdir(parents=True, exist_ok=True)
            keep_numbers(folder)
            old = read_run(run_dir)
            clear_carry(run_dir, old.get("carried"))
            for p in list(run_dir.glob("raw_*.json")) + [run_dir / n for n in (sift.CSV_NAME, sift.SEARCHES_NAME,
                                                                                sift.PRISMA_NAME, sift.COUNTS_NAME,
                                                                                sift.REFERENCES_NAME, TERMS_NAME)]:
                if p.is_file():
                    p.unlink()
            meta = {"version": v["version"], "draft": not v.get("registered"), "date": day, "started": now_iso(),
                    "finished": None, "sources": {}, "exports": {k: e for k, e in (old.get("exports") or {}).items()
                                                                 if k in chosen}}
            if earlier:
                meta["follows"] = {"date": earlier}
            for s in chosen:
                how = how_of(s, have, listed)
                dropped = (s not in KEYLESS or how == "export") and export_file(run_dir, s) is not None
                meta["sources"][s] = {"name": name_of(s, plan), "state": "waiting", "how": "export" if dropped else how}
            write_text(run_dir / RUN_FILE, json.dumps(meta, ensure_ascii=False, indent=1) + "\n")
            if check_terms:
                # the dry run's truncation check before any database is searched, its table kept in the run folder
                heard = (lambda s, state: progress(s, dict(meta["sources"][s], state=state))) if progress else None
                table = truncation_check(plan, [s for s in chosen if meta["sources"][s]["how"] == "api" and s in RUNNERS],
                                         ctx, heard)
                if table["rows"]:
                    write_text(run_dir / TERMS_NAME, ctx.scrub(terms_text(table["rows"])))
                    meta["terms"] = {"file": TERMS_NAME, "rows": len(table["rows"]), "flags": [ctx.scrub(f) for f in table["flags"]]}
            for s in chosen:
                said = meta["sources"][s]
                if said["how"] == "api" and s in RUNNERS:
                    said["state"] = "running"
                    if progress:
                        progress(s, dict(said))
                    try:
                        hits, recs, note = RUNNERS[s](ctx, texts[s]["query"])
                        said.update(state="done", hits=hits, saved=len(recs), note=ctx.scrub(note))
                        write_text(run_dir / f"raw_{s}.json", ctx.scrub(json.dumps(recs, ensure_ascii=False, indent=1)) + "\n")
                    # the failure in full in `note`, which the run's log keeps as before, and in plain words in
                    # `said`, which the screen shows (17 October, later)
                    except SearchError as e:
                        said.update(state="failed", note=ctx.scrub(logged(e)), said=ctx.scrub(str(e)))
                    except Exception as e:                      # a database's odd answer, said and passed over
                        said.update(state="failed", note=ctx.scrub(f"{type(e).__name__}: {e}"), said=unread_said(said["name"]))
                else:
                    take_file(run_dir, s, plan, v, meta, said)
                if progress:
                    progress(s, dict(said))
            with followed_lock(folder, earlier, wait):
                assemble(folder, run_dir, plan, v, meta, ctx)
            return summary(run_dir, meta)


def exported_said(source: str, plan: dict) -> str:
    """How `log.csv` names a database searched on its own site: PsycInfo and CINAHL with the platform."""
    p = platform_of(source, plan)
    if p:
        return f"{FULL_NAMES[source]} on {PLATFORM_HOSTS[p]}, export"
    return EXPORTED.get(source, f"{name_of(source, plan)}, export")


def take_file(run_dir: Path, s: str, plan: dict, v: dict, meta: dict, said: dict) -> None:
    """An export of the run folder taken in for a database, when it was dropped under the version
    run. One dropped under another version is set aside, its row saying so, `set_aside` beside its note."""
    said.pop("said", None)
    said.pop("set_aside", None)
    path = export_file(run_dir, s)
    if path is None:
        said.update(state="awaiting", note="awaiting the export")
        return
    held = (meta.get("exports") or {}).get(s) or {}
    if held.get("version") not in (None, v["version"]):
        said.update(state="awaiting", set_aside=True,
                    note=f"the export was made with version {held['version']}, so it was set aside")
        return
    kind, recs = read_export(path.read_bytes(), path.name, name_of(s, plan))
    said.update(state="done", how="export", hits=len(recs), saved=len(recs),
                note=f"{'BibTeX' if kind == 'bib' else kind.upper()} export ({path.name}), hits = records in it")
    write_text(run_dir / f"raw_{s}.json", json.dumps(recs, ensure_ascii=False, indent=1) + "\n")


def assemble(folder, run_dir: Path, plan: dict, v: dict, meta: dict, ctx: Context) -> None:
    """The run folder's `log.csv`, `screening.csv`, `reasons.csv` and `run.json` written from its raw
    files: the records merged, the missing abstracts and authors filled from OpenAlex, the benchmark checked. A
    run that follows an earlier one has what its last carry wrote taken away and is carried afresh,
    and its `log.csv` holds the earlier run's searches before its own. The caller holds the run's
    screening lock and the lock of the run it follows (see `writing`), so nothing here waits on a lock."""
    clear_carry(run_dir, meta.pop("carried", None))
    # the PDFs found in earlier runs go too, since the records are numbered afresh, and are found again
    # once the screening is written
    sift.clear_found(run_dir)
    texts = {s["source"]: s for s in strings(plan)}
    records = []
    found_by: dict[str, list] = {}
    for s in meta["sources"]:
        raw = run_dir / f"raw_{s}.json"
        recs = []
        if raw.is_file() and meta["sources"][s].get("state") == "done":
            try:
                recs = [r for r in json.loads(raw.read_text(encoding="utf-8")) if isinstance(r, dict)]
            except (OSError, ValueError):
                recs = []
        records += recs
        found_by[s] = recs
    follows = (meta.get("follows") or {}).get("date")
    rows, carried = [], None
    if follows and not records:
        # nothing came in to carry the earlier screening into, which waits for an export
        meta["follows"] = {"date": follows}
    if follows and records:
        carried = carry(folder, run_dir, follows, records, ctx)
        merged, filled, authored = carried["merged"], carried["filled"], carried["authors_filled"]
        cited, from_oa, from_cr = carried["cited_filled"], carried["openalex_filled"], carried["crossref_filled"]
        rows += [{c: r.get(c, "") for c in LOG_COLUMNS} for r in carried["searched"]]
    else:
        merged = merge(records)
        got = fill_from_openalex(ctx, merged)
        filled, authored, cited, from_oa, from_cr = (got[k] for k in ("abstracts", "authors", "cited", "openalex", "crossref"))
        merged = ordered(merged)
    dois = {m["doi"] for m in merged if m["doi"] and m.get("found", True)}
    missed, _ = benchmark_said(plan, dois)
    version = f"plan version {v['version']}" + (", draft" if not v.get("registered") else "")
    for s, said in meta["sources"].items():
        notes = [version]
        if said.get("note"):
            notes.append(said["note"] if said.get("state") != "failed" else "failed: " + said["note"])
        if said.get("state") == "done":
            bench = source_benchmark(plan, found_by[s], records, said.get("how") == "export")
            if bench:
                notes.append(bench)
        interface = INTERFACE.get(s, "") if said.get("how") == "api" else exported_said(s, plan)
        done = said.get("state") == "done"
        rows.append({"date": meta["date"], "source": name_of(s, plan), "interface": interface,
                     "query": texts[s]["query"] if s in texts else "", "hits": said.get("hits", "") if done else "",
                     "records_saved": said.get("saved", "") if done else "", "note": ctx.scrub(", ".join(notes))})
    write_text(run_dir / sift.SEARCHES_NAME, log_text(rows))
    # a run that brought no records makes no screening, so the screening he works in stays the one
    # the review's Screening step opens
    if carried is None and merged:
        write_text(run_dir / sift.CSV_NAME, ctx.scrub(screening_text(merged)))
        sift.write_references(run_dir, {m["rec_id"]: m["references"] for m in merged if m.get("references")})
    elif carried is None:
        (run_dir / sift.CSV_NAME).unlink(missing_ok=True)
        (run_dir / sift.REFERENCES_NAME).unlink(missing_ok=True)
    # the review's own reasons.csv beside the plan, which the review's own session writes, as always,
    # else for a run that has none the plan's exclusion reasons, and a run's own file never written over
    master = Path(folder) / sift.REASONS_NAME
    if master.is_file():
        write_text(run_dir / sift.REASONS_NAME, master.read_bytes().decode("utf-8-sig"))
    elif not (run_dir / sift.REASONS_NAME).exists() and reasons_csv(plan):
        write_text(run_dir / sift.REASONS_NAME, reasons_csv(plan))
    meta.update(finished=now_iso(), records=len(records), merged=len(merged), filled=filled, authors_filled=authored,
                cited_filled=cited, openalex_filled=from_oa, crossref_filled=from_cr, missed=missed,
                benchmark=len(plan["benchmark"]))
    if carried is not None:
        # `searches`, the earlier run's rows at the head of log.csv, so a run's own rows are told apart
        # from them though both runs fell on one day
        meta.update(follows=carried["follows"], carried=dict(carried["carried"], csv=csv_sha(run_dir),
                                                             searches=len(carried["searched"])))
    write_text(run_dir / RUN_FILE, json.dumps(meta, ensure_ascii=False, indent=1) + "\n")
    # each record with no PDF takes the one an earlier run holds for its paper (see `sift.gather_pdfs`)
    if sift.is_screening(run_dir):
        sift.gather_pdfs(run_dir, held=True)


def drop_target(folder, day: str, run=None) -> Path:
    """The run folder an export dropped on the Search strategy screen goes to (12 October): the run the
    screen shows, `run`, its folder's name, which is the newest run of its day, refused in one line
    when a later run of that day has been made since the screen was drawn, so a drop never goes into
    an earlier run of the day than the newest. With none named, as from the command line, the day's
    newest run, the one waiting on the export, and with no run that day yet a new run of the day."""
    if run:
        path = run_path(folder, run)
        if not path.is_dir():
            raise SearchError(sift_words.t("sift_server.search.there_is_no_run_of", run=run_said(run)))
        newest = day_run(folder, run_parts(path.name)[0])
        if newest is not None and newest.name != path.name:
            raise SearchError(sift_words.t("sift_server.search.the_run_of_came_after", name=run_said(newest.name), run=run_said(run)))
        return path
    return day_run(folder, day) or run_path(folder, next_run(folder, day))


def take_export(folder, source: str, data: bytes, name: str, day: str | None = None, which="newest",
                ctx: Context | None = None, wait: float | None = None, listed=None, run=None) -> dict:
    """A database's export, dropped on the screen, kept in the run the screen shows, `run`, or with none
    named the day's newest run folder, the run still waiting on exports (see `drop_target`), as
    `<source>.ris`, `<source>.bib` or `<source>.csv`, the others removed, then the run's files written
    afresh from what the folder holds, no API asked again. A run whose screening has begun is refused
    and left as it is. A database Sift searches itself with no key takes none, unless the user's own
    list, `listed`, sends it by export. With no run that day yet, one is begun for the version on the
    screen, the other databases waiting for Run, which completes it."""
    ctx = ctx or Context()
    day = day or today().isoformat()
    if not known(source):
        raise SearchError(sift_words.t("sift_server.search.that_is_not_one_of"))
    if source in KEYLESS and how_of(source, {}, listed) == "api":
        raise SearchError(sift_words.t("sift_server.search.sift_searches_that_database_itself"))
    run_path(folder, day)
    with locks.held(lock_path(folder), wait):
        run_dir = drop_target(folder, day, run)
        refuse_begun(run_dir)
        meta = read_run(run_dir)
        data_file = read_file(folder)
        v = version_of(data_file, meta.get("version")) if meta.get("version") else None
        if v is None:
            _, v, _ = plan_for_run(folder, which)
        plan = clean_plan(v["plan"])
        if source not in plan["databases"]:
            raise SearchError(sift_words.t("sift_server.search.is_not_one_of_version", source=name_of(source, plan), version=v['version']))
        kind, recs = read_export(data, name, name_of(source, plan))
        if not recs:
            raise SearchError(sift_words.t("sift_server.search.that_file_holds_no_records"))
        # the run's screening lock and the lock of the run it follows taken before anything in the run
        # folder is removed or written (23 October), so a drop refused BUSY leaves it as it was
        with writing(folder, run_dir, (meta.get("follows") or {}).get("date"), wait):
            refuse_begun(run_dir)
            run_dir.mkdir(parents=True, exist_ok=True)
            keep_numbers(folder)
            for ext in EXPORT_KINDS:
                p = run_dir / f"{source}.{ext}"
                if p.is_file():
                    p.unlink()
            target = run_dir / f"{source}.{kind}"
            fd, tmp = tempfile.mkstemp(dir=str(run_dir), prefix=f".{target.name}.", suffix=".tmp")
            with os.fdopen(fd, "wb") as fh:
                fh.write(bytes(data))
            os.replace(tmp, target)
            if not meta:
                have = keys_set()
                meta = {"version": v["version"], "draft": not v.get("registered"), "date": day, "started": now_iso(),
                        "finished": None, "exports": {}, "waiting_for_run": True,
                        "sources": {s: {"name": name_of(s, plan), "state": "waiting", "how": how_of(s, have, listed),
                                        "note": "not run yet"} for s in plan["databases"]}}
            meta.setdefault("exports", {})[source] = {"file": target.name, "version": v["version"], "at": now_iso()}
            said = meta["sources"].setdefault(source, {"name": name_of(source, plan)})
            take_file(run_dir, source, plan, v, meta, said)
            assemble(folder, run_dir, plan, v, meta, ctx)
            return dict(summary(run_dir, meta), taken={"source": source, "records": len(recs), "file": target.name})


def summary(run_dir: Path, meta: dict | None = None, numbers: dict | None = None) -> dict:
    """A run as the screen and the command line say it: `date`, its folder's name, which names it to
    every route, `day` and `n`, its day and its number that day, `number`, its number in the order the
    runs were made, from `numbers` or the review's own (see `run_numbers`), `label`, its name in words
    by that number, Run 3, 12 October 2026, the
    version and whether it was a draft, each database's row of `log.csv` with its state, and a failed
    one's line in plain words, `said` (see `note_said`), the records
    found, after duplicates, the abstracts filled, the records whose authors were and those whose
    counts of citations were, the benchmark
    missed, whether its screening has begun, how many records hold a decision, and the run it
    follows, its name in words, with the
    records carried, new and found again. A run that follows another keeps the earlier searches at the
    head of its `log.csv`, and its rows are those after them, or in a folder from before that count was
    kept its own day's."""
    meta = read_run(run_dir) if meta is None else meta
    review = review_of_run(run_dir)
    if numbers is None:
        numbers = run_numbers(review) if review is not None else {}
    named = lambda name: f"Run {numbers[name]}, {day_said(run_parts(name)[0])}" if name in numbers else run_said(name)
    follows = dict(meta["follows"]) if isinstance(meta.get("follows"), dict) else None
    if follows and follows.get("date"):
        follows["label"] = named(follows["date"])
        # and its number apart, so the page never reads it out of the words (31 October 2026)
        if follows["date"] in numbers:
            follows["number"] = numbers[follows["date"]]
    kept = meta.get("carried") if isinstance(meta.get("carried"), dict) else {}
    log = read_log(run_dir)
    if follows and isinstance(kept.get("searches"), int):
        mine = log[kept["searches"]:]
    else:
        mine = [r for r in log if not follows or r.get("date") == meta.get("date")]
    rows = {r.get("source", ""): r for r in mine}
    shown = []
    for s, said in (meta.get("sources") or {}).items():
        name = said.get("name") or NAMES.get(s, s)
        r = rows.pop(name, {})
        # a failed database in plain words, `said`, as the screen shows it, its note keeping the detail
        failed = said.get("state") == "failed"
        shown.append({"source": s, "name": name, "how": said.get("how", ""), "state": said.get("state", ""),
                      "hits": r.get("hits", ""), "saved": r.get("records_saved", ""),
                      "note": r.get("note", said.get("note", "")), "query": r.get("query", ""),
                      "said": (said.get("said") or note_said(name, s, said.get("note"))) if failed else ""})
    # a run another tool wrote, or a row its run file does not name, as `log.csv` has it
    for name, r in rows.items():
        shown.append({"source": "", "name": name, "how": "", "state": "done" if str(r.get("hits") or "").isdigit() else "",
                      "hits": r.get("hits", ""), "saved": r.get("records_saved", ""), "note": r.get("note", ""),
                      "query": r.get("query", ""), "said": ""})
    n = 0
    try:
        n = len(sift.load(run_dir).ids) if sift.is_screening(run_dir) else 0
    except (sift.SiftError, OSError):
        n = 0
    day, number = run_parts(run_dir.name)
    return {"date": run_dir.name, "day": day, "n": number, "number": numbers.get(run_dir.name), "label": named(run_dir.name),
            "folder": str(run_dir),
            "version": meta.get("version"), "draft": bool(meta.get("draft")),
            "finished": meta.get("finished"), "rows": shown, "records": meta.get("records"),
            "merged": n if sift.is_screening(run_dir) else meta.get("merged"), "filled": meta.get("filled"),
            "authors_filled": meta.get("authors_filled"), "cited_filled": meta.get("cited_filled"),
            "openalex_filled": meta.get("openalex_filled"), "crossref_filled": meta.get("crossref_filled"),
            "missed": meta.get("missed") or [], "benchmark": meta.get("benchmark"), "begun": begun(run_dir),
            "screening": sift.is_screening(run_dir), "decided": decided_of(run_dir), "follows": follows,
            # the truncation check the run made first, its file and its flags (14 October), or None
            "terms": meta.get("terms") if isinstance(meta.get("terms"), dict) else None}


def runs(folder) -> list[dict]:
    """Every run folder under `runs/`, newest first in the order they were made, as `summary` says it,
    each with its number (see `run_numbers`)."""
    numbers = run_numbers(folder)
    return [summary(d, numbers=numbers) for d in run_dirs(folder)]


def run_titles(run_dir: Path) -> list[tuple[str, str]]:
    """A run's records as DOI and title, from its raw files, or from its screening.csv for a run
    another tool wrote. Only reads."""
    out = []
    raws = sorted(run_dir.glob("raw_*.json"))
    for raw in raws:
        try:
            recs = json.loads(raw.read_text(encoding="utf-8"))
        except (OSError, ValueError, UnicodeDecodeError):
            continue
        if isinstance(recs, list):
            out += [(str(r.get("doi") or ""), str(r.get("title") or "")) for r in recs if isinstance(r, dict)]
    if not raws and sift.is_screening(run_dir):
        try:
            text = (run_dir / sift.CSV_NAME).read_bytes().decode("utf-8-sig")
            out += [(str(r.get("doi") or ""), str(r.get("title") or ""))
                    for r in csv.DictReader(io.StringIO(text, newline=""))]
        except (OSError, UnicodeDecodeError, csv.Error):
            pass
    return out


def benchmark_titles(folder, plan: dict | None = None) -> dict:
    """Each benchmark DOI of the plan, the newest version's when `plan` is None, with its title: the
    one typed after it in the plan, else the first a run's records give it, the newest run first. A DOI
    no run has found and the plan gives no title is left out. Only reads."""
    if plan is None:
        try:
            last = newest(read_file(folder))
        except SearchError:
            return {}
        plan = clean_plan(last["plan"]) if last else blank_plan()
    out = {d: plan["benchmark_titles"][d] for d in plan["benchmark"] if plan["benchmark_titles"].get(d)}
    left = {doi_key(d): d for d in plan["benchmark"] if d not in out}
    for run_dir in run_dirs(folder) if left else []:
        for doi, title in run_titles(run_dir):
            k = doi_key(doi) if doi else ""
            if k in left and one_line(title):
                out[left.pop(k)] = one_line(sift.plain(title))[:240]
        if not left:
            break
    return {d: out[d] for d in plan["benchmark"] if d in out}


def run_lines(r: dict) -> list[str]:
    """A run in plain lines, for the command line, named in words with its folder, which `--follows`
    takes, and a run of a draft marked as not registered."""
    head = f"Run of {run_said(r['date'])}, in {RUNS_DIR}/{r['date']}"
    if r.get("version") and r.get("draft"):
        head += f", {draft_said(r['version'])}"
    elif r.get("version"):
        head += f", plan version {r['version']}"
    lines = [head + "."]
    for row in r["rows"]:
        hits = f"{row['hits']} hits, {row['saved']} saved" if str(row["hits"]) != "" else "no records yet"
        lines.append(f"  {row['name']}: {hits}. {row['note']}")
    f = r.get("follows") or {}
    if r.get("merged") is not None:
        kept = f"{f.get('new') or 0} new" if f.get("date") else f"{r['merged']}"
        # the records whose authors were filled, and those whose counts of citations were, each said for a
        # run made since 12 October, which counts them
        authored, cited = r.get("authors_filled"), r.get("cited_filled")
        tail = [f"the authors of {plural(int(authored), 'record')}"] if authored is not None else []
        tail += [f"the citation counts of {plural(int(cited), 'record')}"] if cited is not None else []
        tail = "".join(f",{' and' if i == len(tail) - 1 else ''} {t}" for i, t in enumerate(tail))
        lines.append(f"  {plural(int(r.get('records') or 0), 'record')} found, {kept} after duplicates removed, "
                     f"{plural(int(r.get('filled') or 0), 'abstract')} filled from OpenAlex{tail}.")
        # Sift's own columns from OpenAlex and Crossref, said for a run made since 13 October, which counts them
        if r.get("openalex_filled") is not None:
            lines.append(f"  Retractions, open access, countries and references from OpenAlex for "
                         f"{plural(int(r['openalex_filled']), 'record')}, and from Crossref for {int(r.get('crossref_filled') or 0)}.")
    if f.get("date"):
        lines.append(f"  Follows the run of {run_said(f['date'])}: {plural(int(f.get('carried') or 0), 'record')} carried "
                     f"with their decisions, {f.get('again') or 0} found again, {f.get('new') or 0} new.")
    if r.get("missed"):
        lines.append(f"  Benchmark missed: {', '.join(r['missed'])}.")
    elif r.get("benchmark"):
        lines.append("  Every benchmark DOI found.")
    # the truncation check the run made first (14 October), each flag, or that none was raised
    held = r.get("terms") or {}
    if held.get("rows"):
        flags = held.get("flags") or []
        lines += [f"  {f}." if not f.endswith("?") else f"  {f}" for f in flags]
        if not flags:
            lines.append(f"  Truncation checked, nothing flagged, in {held.get('file') or TERMS_NAME}.")
    if r.get("begun"):
        lines.append(f"  Its screening holds {r['begun']}.")
    return lines
