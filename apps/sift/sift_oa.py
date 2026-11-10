#!/usr/bin/env python3
"""Sift's open-access PDFs: Find open-access PDFs, in Sift's settings, looks for each record of a
screening that passed title and abstract, accepted or kept at maybe there, and has no
`pdfs/<rec_id>.pdf` beside the CSV, and keeps what it finds there through
`sift.save_pdf`, the one way a PDF reaches that folder. It calls no model, so it stands outside the
AI switch, and it runs only when he presses it.

A record with a DOI is asked of OpenAlex by its DOI and of Unpaywall,
`api.unpaywall.org/v2/<doi>?email=<his email>`, the email he gives once in Sift's settings and
`config.json` keeps as `sift_email`. A record with no DOI, as PsycInfo's are, is matched in OpenAlex
by its exact title, normalised, and its year. The places tried, in order: OpenAlex's own copy,
`content_urls.pdf` on content.openalex.org when `has_content.pdf` says it holds one, then OpenAlex's
`best_oa_location.pdf_url`, Unpaywall's `url_for_pdf` for its best location and then the rest,
Europe PMC's `?pdf=render` for a paper with a PMC id, and the `pdf_url` of each of OpenAlex's other
`locations`, the field OpenAlex names `locations` now. OpenAlex's key, when one is saved (see
`sift_search.read_key`), goes as `api_key` to both OpenAlex hosts. pmc.ncbi.nlm.nih.gov refuses
scripts, so it is never asked.

A download is kept only when it is a PDF, `%PDF-` in its first bytes, and its first page's text
carries the record's title, so a library's form or a sign-in page served in a paper's place is
refused. The text is read by the family's `pdftext.py` with the standard library alone: the first
page found through the catalogue's page tree, its content streams inflated, its strings read through
each font's ToUnicode map where it has one. A PDF already in `pdfs/` is never overwritten: a record that has one
is passed over before anything is asked and again at the write, so another fetcher can work the
same folder.

`IDIOGRAPH_SEARCH_STUB`, a loopback address, sends every request to a stub server, the host put at
the head of the path, as Sift's searches send theirs, and the transport is a parameter, so the suite
and a smoke run never reach a real service. The standard library, `sift.py`, `sift_search.py` and the
family's `pdftext.py` only.
"""
from __future__ import annotations

import sift_words
import json
import re
import urllib.error
import urllib.parse
import urllib.request

import sift
import sift_search as ss
# a PDF's text and a title as two are matched, the family's since 22 October 2026 (family/pdftext.py),
# which Trace reads a reference's PDF through too, kept by these names here
from pdftext import (ESCAPES, OBJ, PAGE, REF, TOKEN, cmap, content_text, decode, dict_at, first_page,  # noqa: F401
                     first_page_text, fonts, head_of, inflate, inner, is_pdf, literal, norm_title, objects, page_list,
                     page_text, pages_text, ref_of, resources, stream_of)

OPENALEX = "https://api.openalex.org/works"
UNPAYWALL = "https://api.unpaywall.org/v2/"
EUROPE_PMC = "https://europepmc.org/articles/"
OPENALEX_HOSTS = ("api.openalex.org", "content.openalex.org")
# hosts that refuse a script, never asked
REFUSING = ("pmc.ncbi.nlm.nih.gov",)
UA = "Idiograph-Sift/1.0 (open-access PDFs)"
TIMEOUT = 30
PDF_MAX = 100 * 1024 * 1024
# the places tried for one record at most, so one record never holds the run long
TRIES = 8
# the share of the title's longer words the first page must hold when the title is not there whole
WORDS_NEEDED = 0.8
# This module's words for a person, read in the run's language when said: inside the module through `_w`,
# from others and the checks as the module's names (`__getattr__`)
SAID = {
    "NO_EMAIL": lambda: sift_words.t("sift_server.oa.no_email"),
}


def _w(name: str) -> str:
    return SAID[name]()


def __getattr__(name: str) -> str:
    """This module's words other modules and the checks name, read in the run's language."""
    if name in SAID:
        return SAID[name]()
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


# ------------------------------------------------------------------ the records

def plan(folder) -> dict:
    """The records a run would look for, in the CSV's order, before anything is asked: those that passed
    title and abstract, accepted or kept at maybe there, the reports PRISMA seeks for retrieval, with no
    PDF yet (12 October). `passed` counts the records that passed and `have` those of them with a PDF."""
    sc = sift.load(folder)
    held = sift.states(sift.read_log(folder))
    passed = [rec for rec in sc.ids if sift.in_stage(sc, held, rec, "ft")]
    ids = [rec for rec in passed if sift.pdf_path(folder, rec) is None]
    return {"ids": ids, "records": len(sc.ids), "passed": len(passed), "have": len(passed) - len(ids)}


# ---------------------------------------------------------------- requests

def stubbed(url: str) -> str:
    """Where a request goes: in a smoke run the stub server, the real host at the head of the path, and
    otherwise the address as it is."""
    base = ss.stub_base()
    if not base:
        return url
    p = urllib.parse.urlparse(url)
    return f"{base}/{p.netloc}{p.path}" + (f"?{p.query}" if p.query else "")


def http_fetch(url: str) -> tuple[int, str, bytes]:
    """One GET: its status, its content type and its body, at most PDF_MAX, or status 0 when it never
    answers. Nothing about it is logged."""
    req = urllib.request.Request(stubbed(url), headers={"User-Agent": UA, "Accept": "application/json, application/pdf, */*"})
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT) as r:
            body = r.read(PDF_MAX + 1)
            return int(r.status), str(r.headers.get("Content-Type") or ""), body
    except urllib.error.HTTPError as exc:
        return int(exc.code), "", b""
    except Exception:
        return 0, "", b""


def with_key(url: str, key: str | None) -> str:
    """An OpenAlex address with `api_key` when a key is saved, any other as it is."""
    if not key or urllib.parse.urlparse(url).netloc not in OPENALEX_HOSTS:
        return url
    return url + ("&" if "?" in url else "?") + urllib.parse.urlencode({"api_key": key})


def get_json(fetch, url: str, key: str | None = None) -> dict | None:
    status, _, body = fetch(with_key(url, key))
    if status != 200:
        return None
    try:
        data = json.loads(body.decode("utf-8", "replace"))
    except ValueError:
        return None
    return data if isinstance(data, dict) else None


def quoted(doi: str) -> str:
    return urllib.parse.quote(doi, safe="/()._-;:")


def work_by_doi(fetch, doi: str, key: str | None) -> dict | None:
    return get_json(fetch, f"{OPENALEX}/doi:{quoted(doi)}", key)


def work_by_title(fetch, title: str, year: str, key: str | None) -> dict | None:
    """The OpenAlex work whose title, normalised, is the record's own and whose year is its year, or None."""
    want = norm_title(title)
    if not want or not year:
        return None
    query = urllib.parse.urlencode({"search": sift.plain(title), "filter": f"publication_year:{year}", "per-page": 10})
    data = get_json(fetch, f"{OPENALEX}?{query}", key)
    for work in (data or {}).get("results") or []:
        if isinstance(work, dict) and norm_title(work.get("title") or work.get("display_name")) == want \
                and str(work.get("publication_year") or "") == str(year):
            return work
    return None


def pmc_of(work: dict) -> str:
    """The PMC id OpenAlex gives a work, PMC1234567, or empty."""
    raw = str(((work or {}).get("ids") or {}).get("pmcid") or "")
    m = re.search(r"(PMC)?(\d+)\s*/?$", raw, re.I)
    return f"PMC{m.group(2)}" if raw and m else ""


def places(work: dict | None, unpaywall: dict | None) -> list[tuple[str, str]]:
    """The addresses a PDF might come from, each once, in the order they are tried, each with the
    words for where it came from."""
    out: list[tuple[str, str]] = []

    def add(url, where):
        url = str(url or "").strip()
        host = urllib.parse.urlparse(url).netloc.lower()
        if url.lower().startswith(("http://", "https://")) and host not in REFUSING and url not in [u for u, _ in out]:
            out.append((url, where))

    w = work or {}
    if (w.get("has_content") or {}).get("pdf"):
        add((w.get("content_urls") or {}).get("pdf"), "OpenAlex")
    add((w.get("best_oa_location") or {}).get("pdf_url"), "OpenAlex")
    u = unpaywall or {}
    add((u.get("best_oa_location") or {}).get("url_for_pdf"), "Unpaywall")
    for loc in u.get("oa_locations") or []:
        if isinstance(loc, dict):
            add(loc.get("url_for_pdf"), "Unpaywall")
    pmc = pmc_of(w)
    if pmc:
        add(f"{EUROPE_PMC}{pmc}?pdf=render", "Europe PMC")
    for loc in w.get("locations") or []:
        if isinstance(loc, dict):
            add(loc.get("pdf_url"), "OpenAlex")
    return out[:TRIES]


# ---------------------------------------------------------------- one record

def find(folder, rec_id, email: str = "", fetch=None, keep=None, key=False) -> dict:
    """One record looked for and, when found, kept as `pdfs/<rec_id>.pdf` through `keep`, which takes
    the bytes and answers as `sift.save_pdf` does, `sift.save_pdf` itself when not given. The answer
    names the record, `saved` when a PDF was kept, `skipped` when one was there already, `where` it
    came from, and `said`, one line on why none was kept. `key` is OpenAlex's key, read through
    `sift_search.read_key` when not given. Nothing here ever overwrites a PDF."""
    fetch = fetch or http_fetch
    sc = sift.load(folder)
    rec = str(rec_id or "")
    if rec not in sc.at:
        raise sift.SiftError(sift_words.t("sift_server.there_is_no_record_in", rec=rec or sift_words.t("sift_server.none_named"), csv_name=sift.CSV_NAME))
    out = {"rec_id": rec, "saved": False, "skipped": False, "where": "", "said": ""}
    if sift.pdf_path(folder, rec) is not None:
        return dict(out, skipped=True, said=sift_words.t("sift_server.oa.it_has_a_pdf_already"))
    if key is False:
        key = ss.read_key(ss.OPENALEX_KEY)
    title = sift.plain(sc.cell(rec, "title"))
    doi = ss.norm_doi(sc.cell(rec, "doi"))
    year = ss.year_of(sc.cell(rec, "year"))
    work = work_by_doi(fetch, doi, key) if doi else work_by_title(fetch, title, year, key)
    if not doi and work:
        doi = ss.norm_doi(work.get("doi"))
    if not doi and not work:
        return dict(out, said=sift_words.t("sift_server.oa.no_doi_and_openalex_holds"))
    unpaywall = get_json(fetch, f"{UNPAYWALL}{quoted(doi)}?{urllib.parse.urlencode({'email': email})}") \
        if doi and email else None
    tried = places(work, unpaywall)
    if not tried:
        return dict(out, said=sift_words.t("sift_server.oa.no_open_access_copy_is"))
    refused = sift_words.t("sift_server.oa.every_copy_listed_refused_a")
    for url, where in tried:
        status, _, body = fetch(with_key(url, key))
        if status != 200 or not body or len(body) > PDF_MAX:
            continue
        if not is_pdf(body):
            refused = sift_words.t("sift_server.oa.no_copy_listed_answered_with")
            continue
        if not carries_title(first_page_text(body), title):
            refused = sift_words.t("sift_server.oa.no_pdf_found_carries_the")
            continue
        kept = (keep or (lambda data: sift.save_pdf(folder, rec, data, replace=False)))(body)
        if kept.get("exists") and not kept.get("saved"):
            return dict(out, skipped=True, said=sift_words.t("sift_server.oa.it_has_a_pdf_already"), answer=kept)
        return dict(out, saved=True, where=where, answer=kept)
    return dict(out, said=refused)


def carries_title(text: str, title: str) -> bool:
    """Whether a page's text carries a title: the whole of it, its letters and digits in order, or
    when a line break or a ligature parts it, most of its longer words."""
    want, body = norm_title(title), norm_title(text)
    if not want or not body:
        return False
    if want in body:
        return True
    words = [w for w in (norm_title(w) for w in sift.plain(title).split()) if len(w) >= 4]
    return bool(words) and sum(1 for w in words if w in body) / len(words) >= WORDS_NEEDED
