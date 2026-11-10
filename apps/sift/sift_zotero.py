#!/usr/bin/env python3
"""Sift's sync to Zotero: a screening's records, each with its PDF, put in a Zotero collection named
for its Sift project, through Zotero's own Web API, version 3, on his own key. It calls no model, so
it stands outside the AI switch, and it runs only when he presses Sync or runs
`sift zotero sync <folder>`.

The settings are `zotero` in `config.json`: `library`, `user` for his own library, the default, or
`group` for a group library by its `group_id`. His own library is the key's owner's, which Zotero
gives with the key's own record, so no user id is asked for. The key is kept in the macOS keychain under `ZOTERO_API_KEY`, through `sift_search`'s own
`save_key`, `clear_key` and `key_saved`, as every key of the app is, never in a file, a log, an
answer or an error. It goes in the `Zotero-API-Key` header to api.zotero.org alone, and never to
the address a PDF is uploaded to.

A sync takes the records chosen, every record accepted at full text by default, or the rows the
table shows, or every record, and the collection named for the Sift project, made when the library
has none of that name at its top. Each record is matched to an item by the key Sift keeps in its own
column of the CSV, `zotero_key`, else by an item of the collection with the same DOI, or with no DOI
the same title and year, so nothing is ever made twice. A record with no item gets one of the type
its `pub_type` names, a journal article unless it names another, its fields mapped onto the fields
Zotero's template for that type holds, a DOI the type has no field for written in Extra as Zotero
reads it, and `Sift: <rec_id>` in Extra. An item that stands gains what it lacks: a field it holds
empty, the collection and the Extra line, and its tags of Sift's own, `sift:` and the decision and
stage, `sift:include-ft`, or `sift:reason-` and a reason's code, are set to the record's as it
stands, every other tag kept. A field he has filled in Zotero is never written over. A record
synced before and not chosen now keeps its item and loses only its tags of Sift's own. Sift never
deletes an item, an attachment or a collection.

A record's `pdfs/<rec_id>.pdf` goes up as the item's attachment when the item has no PDF yet, in the
API's three steps after the attachment item is made: authorise, with the file's MD5, name, size and
time, upload, to the address the authorisation gives with its prefix and suffix around the file,
and register. An authorisation that answers that the file exists already needs neither of the rest.

Every change of an item sends `If-Unmodified-Since-Version` with the version it was read at, and a
change refused for a newer version is read again and tried once more. The collection is made with
the library's version, so a collection made meanwhile elsewhere is found rather than made twice.
Each new item and attachment is written with a `Zotero-Write-Token`, so a request sent again never
makes two. A `Backoff` header holds the next request back for its seconds, and a 429 or a 503 is
tried again after its `Retry-After`. Every error is one plain line with the key scrubbed out.

`zotero.lock` beside the CSV keeps one sync of a screening at a time, and the keys go into the CSV
through `sift.write_zotero` under the screening's own lock, a batch at a time, so a sync cut short
still knows the items it made. `IDIOGRAPH_SEARCH_STUB`, a loopback address, sends every request to a
stub server, the host at the head of the path as Sift's searches send theirs, and every key to the
smoke run's own keychain held in memory, and the transport is a parameter, so the suite and a smoke
run never reach Zotero. The standard library, `locks.py`, `sift.py` and `sift_search.py` only.
"""
from __future__ import annotations

import sift_words
import hashlib
import json
import re
import secrets
import time
import unicodedata
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

import locks
import sift
import sift_search as ss
from errors import WorkbookError

API = "https://api.zotero.org"
KEY_SERVICE = "ZOTERO_API_KEY"
API_VERSION = "3"
UA = "Idiograph-Sift/1.0 (Zotero sync)"
TIMEOUT = 60
# the most objects one write takes and the most a page of a listing holds, as the API sets them
BATCH = 50
PAGE = 100
# a request tried this many times at most when the API asks for a wait, each wait held to WAIT_MOST
TRIES = 4
WAIT_MOST = 120
LOCK_NAME = "zotero.lock"
SETTINGS_KEY = "zotero"
LIBRARIES = ("user", "group")
# the records a sync takes: those included at full text, the rows the table shows, or every one
WHICH = ("included", "filter", "all")
TAG = "sift:"
EXTRA_MARK = "Sift:"
PDF_TITLE = "Full Text PDF"
PDF_MAX = 200 * 1024 * 1024
CREATORS_MOST = 100
# an item's type from the words a record's `pub_type` holds, the first that matches, the more
# particular first so a book chapter is never a book
TYPES = ((re.compile(r"thesis|dissertation", re.I), "thesis"),
         (re.compile(r"preprint|posted.content", re.I), "preprint"),
         (re.compile(r"chapter|book.?section|book.?part|incollection", re.I), "bookSection"),
         (re.compile(r"\bbook\b|monograph", re.I), "book"),
         (re.compile(r"conference|proceedings|congress|symposium", re.I), "conferencePaper"),
         (re.compile(r"\breport\b|working paper", re.I), "report"),
         (re.compile(r"web.?page|website", re.I), "webpage"))
# the field the record's `journal` cell goes in for each type, none for a book
VENUE = {"journalArticle": "publicationTitle", "preprint": "repository", "conferencePaper": "proceedingsTitle",
         "thesis": "university", "bookSection": "bookTitle", "report": "institution", "webpage": "websiteTitle",
         "document": "publisher"}
# This module's words for a person, read in the run's language when said: inside the module through `_w`,
# from others and the checks as the module's names (`__getattr__`)
SAID = {
    "NO_KEY": lambda: sift_words.t("sift_server.zotero.no_key"),
}


def _w(name: str) -> str:
    return SAID[name]()


def __getattr__(name: str) -> str:
    """This module's words other modules and the checks name, read in the run's language."""
    if name in SAID:
        return SAID[name]()
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


class ZoteroError(WorkbookError):
    """A sync or a check that cannot go ahead, said in one plain line with no key in it."""


# ------------------------------------------------------------------ settings and the key

def digits(value, most: int = 12) -> str:
    return re.sub(r"\D", "", str(value or ""))[:most]


def clean_settings(raw) -> dict:
    """The settings as `config.json` keeps them: the library, `user` unless `group` is named, and the
    group's id, digits alone. A user id an older config holds is passed over, since the key names its
    own user."""
    raw = raw if isinstance(raw, dict) else {}
    return {"library": raw.get("library") if raw.get("library") in LIBRARIES else "user",
            "group_id": digits(raw.get("group_id"))}


def settings_of(cfg) -> dict:
    return clean_settings((cfg or {}).get(SETTINGS_KEY))


def prefix_of(s: dict, user_id: str = "") -> str:
    """The library's place in the API, `/users/<id>` for the key's own user or `/groups/<id>`, refused
    when its id is missing."""
    if s["library"] == "group":
        if not s["group_id"]:
            raise ZoteroError(sift_words.t("sift_server.zotero.give_the_group_library_s"))
        return f"/groups/{s['group_id']}"
    if not user_id:
        raise ZoteroError(sift_words.t("sift_server.zotero.zotero_did_not_say_whose"))
    return f"/users/{user_id}"


def key_record(c: "Client") -> dict:
    """The key's own record from Zotero, its `userID`, name and access, refused in one line."""
    status, _, got = c.send("GET", "/keys/current")
    if status in (403, 404):
        raise ZoteroError(sift_words.t("sift_server.zotero.zotero_did_not_take_that"))
    if status != 200:
        raise c.fail(status, got, sift_words.t("sift_server.zotero.checking_the_key"))
    try:
        data = json.loads(got.decode("utf-8"))
    except ValueError:
        raise ZoteroError(sift_words.t("sift_server.zotero.zotero_answered_with_something_that")) from None
    return data if isinstance(data, dict) else {}


def save_key(value) -> dict:
    """The key stored in the keychain under ZOTERO_API_KEY. The answer says whether it was saved and
    never what it is."""
    return ss.save_key(KEY_SERVICE, value)


def clear_key() -> dict:
    return ss.clear_key(KEY_SERVICE)


def key_saved() -> bool:
    return ss.key_saved(KEY_SERVICE)


def read_key() -> str | None:
    return ss.read_key(KEY_SERVICE)


# ------------------------------------------------------------------ the transport

def stubbed(url: str) -> str:
    """Where a request goes: in a smoke run the stub server, the real host at the head of the path, and
    otherwise the address as it is."""
    base = ss.stub_base()
    if not base:
        return url
    p = urllib.parse.urlparse(url)
    return f"{base}/{p.netloc}{p.path}" + (f"?{p.query}" if p.query else "")


def http_call(method: str, url: str, headers: dict, body: bytes | None) -> tuple[int, dict, bytes]:
    """One request: its status, its headers with their names in lower case, and its body, or status 0
    with nothing when it never answers. Nothing about it is logged."""
    req = urllib.request.Request(stubbed(url), data=body, method=method, headers=dict(headers, **{"User-Agent": UA}))
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT) as r:
            return int(r.status), {k.lower(): v for k, v in r.headers.items()}, r.read()
    except urllib.error.HTTPError as exc:
        try:
            data = exc.read()
        except Exception:
            data = b""
        return int(exc.code), {k.lower(): v for k, v in (exc.headers or {}).items()}, data
    except Exception:
        return 0, {}, b""


def seconds(value) -> float:
    try:
        return max(0.0, float(str(value or "").strip()))
    except ValueError:
        return 0.0


class Client:
    """Requests to one library on one key, `call` the transport and `sleep` the wait, which the suite
    replaces. The key goes in a header to api.zotero.org alone and is scrubbed from every line."""

    def __init__(self, key: str, prefix: str = "", call=None, sleep=None):
        self.key = key or ""
        self.prefix = prefix
        self.call = call or http_call
        self.sleep = sleep or time.sleep
        self.pause = 0.0
        self.templates: dict[str, dict] = {}

    def scrub(self, text) -> str:
        return " ".join(ss.scrub(text, [self.key]).split())[:300]

    def send(self, method: str, where: str, params: dict | None = None, data=None, form: dict | None = None,
             raw: bytes | None = None, headers: dict | None = None, keyed: bool = True) -> tuple[int, dict, bytes]:
        """One request to `where`, a path under the API or, for an upload, the address the API gave,
        with JSON `data`, a `form` or `raw` bytes. Waits as `Backoff` asks before the next request, and
        on 429 or 503 tries again after `Retry-After`."""
        url = where if where.startswith(("http://", "https://")) else API + where
        if params:
            url += ("&" if "?" in url else "?") + urllib.parse.urlencode(params)
        hdrs = dict(headers or {})
        if keyed:
            hdrs.update({"Zotero-API-Key": self.key, "Zotero-API-Version": API_VERSION})
        body = None
        if data is not None:
            body = json.dumps(data, ensure_ascii=False).encode("utf-8")
            hdrs["Content-Type"] = "application/json"
        elif form is not None:
            body = urllib.parse.urlencode(form).encode("utf-8")
            hdrs["Content-Type"] = "application/x-www-form-urlencoded"
        elif raw is not None:
            body = raw
        status, head, got = 0, {}, b""
        for n in range(TRIES):
            if self.pause:
                self.sleep(self.pause)
                self.pause = 0.0
            status, head, got = self.call(method, url, hdrs, body)
            back = seconds(head.get("backoff"))
            if back:
                self.pause = min(back, WAIT_MOST)
            if status in (429, 503) and n < TRIES - 1:
                self.sleep(min(seconds(head.get("retry-after")) or 5.0 * (n + 1), WAIT_MOST))
                continue
            break
        return status, head, got

    def lib(self, path: str) -> str:
        return self.prefix + path

    def fail(self, status: int, got: bytes, doing: str) -> ZoteroError:
        """A refusal said plainly by its status, the API's own words after it where they help."""
        words = self.scrub(got.decode("utf-8", "replace")) if got else ""
        if status == 0:
            return ZoteroError(sift_words.t("sift_server.zotero.zotero_did_not_answer_while", doing=doing))
        if status == 403:
            return ZoteroError(sift_words.t("sift_server.zotero.zotero_refused_the_key_while", doing=doing))
        if status == 404:
            return ZoteroError(sift_words.t("sift_server.zotero.zotero_has_no_such_library", doing=doing))
        if status == 413:
            return ZoteroError(sift_words.t("sift_server.zotero.your_zotero_storage_is_full"), code="zotero_storage_full")
        if status == 429:
            return ZoteroError(sift_words.t("sift_server.zotero.zotero_asked_for_a_break"))
        return ZoteroError(sift_words.t("sift_server.zotero.answered_words", status=status, doing=doing, words=words) if words
                           else sift_words.t("sift_server.zotero.answered", status=status, doing=doing))

    def json(self, method: str, where: str, doing: str, ok=(200,), **kw):
        status, head, got = self.send(method, where, **kw)
        if status not in ok:
            raise self.fail(status, got, doing)
        try:
            return (json.loads(got.decode("utf-8")) if got else None), head
        except ValueError:
            raise ZoteroError(sift_words.t("sift_server.zotero.zotero_answered_with_something_that_2", doing=doing)) from None

    def listing(self, path: str, doing: str, params: dict | None = None) -> tuple[list, str]:
        """Every object of a listing, page by page, and the library's version it was read at."""
        out, start, version = [], 0, ""
        while True:
            got, head = self.json("GET", self.lib(path), doing, params=dict(params or {}, limit=PAGE, start=start))
            got = got if isinstance(got, list) else []
            out += [o for o in got if isinstance(o, dict)]
            version = version or str(head.get("last-modified-version") or "")
            total = int(seconds(head.get("total-results")) or 0)
            start += PAGE
            if not got or start >= total:
                return out, version

    def template(self, kind: str) -> dict:
        """Zotero's empty item of a type, its fields the ones the type holds, asked once a sync."""
        if kind not in self.templates:
            got, _ = self.json("GET", "/items/new", "reading Zotero's fields", params={"itemType": kind}, keyed=False)
            self.templates[kind] = got if isinstance(got, dict) else {}
        return self.templates[kind]


# ------------------------------------------------------------------ check

def check(cfg, given=None, call=None) -> dict:
    """Whether the key saved works with the library the settings name, or `given` as Settings holds
    them before Save: the key's own record, read once, and a group's name, said in one line. Settings
    asks it as soon as a key is saved. The key is never in the answer."""
    s = clean_settings(given) if isinstance(given, dict) else settings_of(cfg)
    key = read_key()
    if not key:
        return {"ok": False, "said": _w("NO_KEY")}
    c = Client(key, "", call)
    try:
        data = key_record(c)
    except ZoteroError as exc:
        return {"ok": False, "said": str(exc)}
    uid = digits(data.get("userID"))
    access = data.get("access") if isinstance(data.get("access"), dict) else {}
    if s["library"] == "user":
        name = " ".join(str(data.get("username") or data.get("displayName") or "").split()) or sift_words.t("sift_server.zotero.user", uid=uid)
        own = access.get("user") if isinstance(access.get("user"), dict) else {}
        if not own.get("library"):
            return {"ok": False, "said": sift_words.t("sift_server.zotero.the_key_cannot_read_the_2", name=name)}
        if not own.get("write"):
            return {"ok": False, "said": sift_words.t("sift_server.zotero.the_key_reads_the_library", name=name)}
        return {"ok": True, "said": sift_words.t("sift_server.zotero.the_key_works_with_the_2", name=name)}
    if not s["group_id"]:
        return {"ok": False, "said": sift_words.t("sift_server.zotero.give_the_group_library_s_2")}
    groups = access.get("groups") if isinstance(access.get("groups"), dict) else {}
    held = groups.get(s["group_id"]) or groups.get("all") or {}
    status, _, got = c.send("GET", f"/groups/{s['group_id']}")
    if status != 200:
        return {"ok": False, "said": sift_words.t("sift_server.zotero.zotero_has_no_group_that", group_id=s['group_id'])}
    try:
        group = json.loads(got.decode("utf-8"))
    except ValueError:
        group = {}
    name = " ".join(str(((group or {}).get("data") or {}).get("name") or "").split()) or sift_words.t("sift_server.zotero.group", group_id=s['group_id'])
    if not held.get("library"):
        return {"ok": False, "said": sift_words.t("sift_server.zotero.the_key_cannot_read_the", name=name)}
    if not held.get("write"):
        return {"ok": False, "said": sift_words.t("sift_server.zotero.the_key_reads_the_group", name=name)}
    return {"ok": True, "said": sift_words.t("sift_server.zotero.the_key_works_with_the", name=name)}


# ------------------------------------------------------------------ records into items

def norm(text) -> str:
    """Words as two are matched by: letters and digits alone, folded."""
    return "".join(ch for ch in unicodedata.normalize("NFKC", sift.plain(text)).casefold() if ch.isalnum())


def norm_doi(text) -> str:
    d = str(text or "").strip().lower()
    d = re.sub(r"^(https?://(dx\.)?doi\.org/|doi:\s*)", "", d)
    return d.strip()


def item_type(pub_type: str, journal: str = "") -> str:
    """The item's type from the record's `pub_type`, a journal article unless the words name another,
    and a document when the record names neither a type nor a journal."""
    text = str(pub_type or "")
    for pattern, kind in TYPES:
        if pattern.search(text):
            return kind
    return "journalArticle" if str(journal or "").strip() or text.strip() else "document"


def initials_of(token: str) -> str:
    """Initials as Zotero's styles read them, `JJ` and `T.C.` as `J. J.` and `T. C.`, a hyphened pair kept."""
    if "-" in token:
        return token if token.endswith(".") else token + "."
    return " ".join(f"{c}." for c in re.findall(r"[A-Z]", token))


def creators_of(authors: str) -> list[dict]:
    """The authors as Zotero's creators, each of `sift_search.author_names` a first and a last name:
    `Last, First`, `Last Initials` as Europe PMC and Scopus give it, or `First Last`, initials written
    `J. J.`, and one word a single name."""
    out = []
    for name in ss.author_names(authors):
        if "," in name:
            last, first = (p.strip() for p in name.split(",", 1))
            first = initials_of(first) if ss.INITIALS.match(first) else first
            out.append({"creatorType": "author", "lastName": last, "firstName": first})
        elif " " in name:
            words = name.split()
            if ss.INITIALS.match(words[-1]):
                last, first = " ".join(words[:-1]), initials_of(words[-1])
            else:
                first, last = " ".join(words[:-1]), words[-1]
                if all(ss.INITIALS.match(w) for w in words[:-1]):
                    first = " ".join(initials_of(w) for w in words[:-1])
            out.append({"creatorType": "author", "lastName": last, "firstName": first})
        else:
            out.append({"creatorType": "author", "name": name})
        if len(out) >= CREATORS_MOST:
            break
    return out


def creators_before(authors: str) -> list[dict]:
    """The creators a sync wrote before 12 October 2026, `Larkin M.` as a first name Larkin and a last
    name M., kept only so a sync can put right an item it made then and nobody has changed since."""
    out = []
    for part in re.split(r"[;|]", str(authors or "")):
        name = " ".join(part.split()).strip(" ,")
        if not name or name.lower().rstrip(".") == "et al":
            continue
        if "," in name:
            last, first = (p.strip() for p in name.split(",", 1))
            out.append({"creatorType": "author", "lastName": last, "firstName": first})
        elif " " in name:
            first, last = name.rsplit(" ", 1)
            out.append({"creatorType": "author", "lastName": last, "firstName": first})
        else:
            out.append({"creatorType": "author", "name": name})
        if len(out) >= CREATORS_MOST:
            break
    return out


def wanted(sc, rec: str) -> dict:
    """What an item of the record holds, by Zotero's field names, before its type's template keeps the
    fields the type has: its type, title, creators, date, venue, DOI, address and abstract."""
    get = lambda name: sift.one_line(sift.plain(sc.cell(rec, name)))
    journal = get("journal")
    kind = item_type(get("pub_type"), journal)
    out = {"itemType": kind, "title": get("title"), "creators": creators_of(sc.cell(rec, "authors")),
           "date": get("year"), "DOI": norm_doi(sc.cell(rec, "doi")), "url": sift.url_link(sc.cell(rec, sift.URL_COLUMN)),
           "abstractNote": sift.plain(sc.cell(rec, "abstract")).strip()}
    if VENUE.get(kind) and journal:
        out[VENUE[kind]] = journal
    return out


def mark_line(rec: str) -> str:
    return f"{EXTRA_MARK} {rec}"


def with_mark(extra: str, rec: str) -> str:
    """Extra with its one line of Sift's own, `Sift: <rec_id>`, put in or put right, every other line
    kept as it was."""
    lines = [ln for ln in str(extra or "").splitlines() if not ln.strip().startswith(EXTRA_MARK)]
    return "\n".join([ln for ln in lines] + [mark_line(rec)]).strip("\n")


def new_item(client: Client, sc, rec: str, coll: str, tags: list[str]) -> dict:
    """A new item of the record, its fields those its type's template holds, a DOI the type has no
    field for in Extra as Zotero reads it, the collection and its tags of Sift's own."""
    want = wanted(sc, rec)
    tpl = client.template(want["itemType"])
    fields = tpl or want
    item = {k: v for k, v in want.items() if (k in fields or k == "itemType") and v}
    extra = [mark_line(rec)]
    if want["DOI"] and "DOI" not in fields:
        extra.insert(0, f"DOI: {want['DOI']}")
    item.update({"extra": "\n".join(extra), "tags": [{"tag": t} for t in tags], "collections": [coll] if coll else []})
    return item


def tags_of(sc, held: dict, rec: str) -> list[str]:
    """The record's tags of Sift's own: its decision at each stage it has one, `sift:include-ta`, and each
    reason's code, `sift:reason-E5`, in that order, each once."""
    out = []
    for stage in sift.STAGES:
        st = sift.state_of(sc, held, rec, stage)
        if st["decision"]:
            out.append(f"{TAG}{st['decision']}-{stage}")
    for stage in sift.STAGES:
        st = sift.state_of(sc, held, rec, stage)
        code = re.sub(r"\s+", "", st["reason"]) if st["decision"] == "exclude" else ""
        if code and f"{TAG}reason-{code}" not in out:
            out.append(f"{TAG}reason-{code}")
    return out


def sift_tags(data: dict) -> list[str]:
    return sorted(str(t.get("tag") or "") for t in data.get("tags") or [] if isinstance(t, dict)
                  and str(t.get("tag") or "").startswith(TAG))


def retagged(data: dict, tags: list[str]) -> list[dict]:
    """An item's tags with its tags of Sift's own set to `tags`, every other tag kept as it was."""
    others = [t for t in data.get("tags") or [] if isinstance(t, dict) and not str(t.get("tag") or "").startswith(TAG)]
    return others + [{"tag": t} for t in tags]


def patch_of(data: dict, sc, rec: str, coll: str, tags: list[str], chosen: bool) -> dict:
    """What an item that stands lacks: for a record chosen, each field it holds empty, the collection and
    the Extra line, and for every record its tags of Sift's own set to the record's. A field filled in
    Zotero is never written over, save creators exactly as a sync before 12 October 2026 wrote them,
    which are put right. Empty when nothing would change."""
    out = {}
    if chosen:
        for k, v in wanted(sc, rec).items():
            if k in ("itemType", "creators") or not v or k not in data:
                continue
            if not str(data.get(k) or "").strip():
                out[k] = v
        made = creators_of(sc.cell(rec, "authors"))
        if not data.get("creators") and "creators" in data:
            if made:
                out["creators"] = made
        elif made and data.get("creators") != made and data.get("creators") == creators_before(sc.cell(rec, "authors")):
            out["creators"] = made
        if coll and coll not in (data.get("collections") or []):
            out["collections"] = list(data.get("collections") or []) + [coll]
        extra = with_mark(data.get("extra") or "", rec)
        if "extra" in data and extra != (data.get("extra") or ""):
            out["extra"] = extra
    if sift_tags(data) != sorted(tags):
        out["tags"] = retagged(data, tags)
    return out


def chosen_ids(sc, held: dict, which: str, ids=None) -> list[str]:
    """The records a sync takes, in the CSV's order: those included at full text, those `ids` names, the
    rows the table shows, or every one."""
    if which not in WHICH:
        raise ZoteroError(sift_words.t("sift_server.zotero.the_records_are_those_included"))
    if which == "all":
        return list(sc.ids)
    if which == "filter":
        named = {str(i) for i in ids or [] if isinstance(i, (str, int))}
        return [rec for rec in sc.ids if rec in named]
    return [rec for rec in sc.ids if sift.state_of(sc, held, rec, "ft")["decision"] == "include"]


def project_name(folder) -> str:
    """The Sift project a screening belongs to, the review above a run's folder or the screening's own,
    by its plan's name or its folder's."""
    folder = Path(folder).resolve()
    review = folder.parent.parent if folder.parent.name == ss.RUNS_DIR else folder
    return ss.own_name(review) or review.name


def pdf_name(sc, rec: str) -> str:
    """The attachment's file name, the first author's last name, the year and the title, as Zotero names
    its own, or the rec_id."""
    people = creators_of(sc.cell(rec, "authors"))
    first = (people[0].get("lastName") or people[0].get("name") or "") if people else ""
    words = " ".join(w for w in (first, sc.cell(rec, "year").strip(), sift.one_line(sift.plain(sc.cell(rec, "title")))) if w)
    words = re.sub(r'[\\/:*?"<>|\x00-\x1f]+', " ", words)
    words = " ".join(words.split())[:80].strip(" .")
    return (words or rec) + ".pdf"


# ------------------------------------------------------------------ the survey

def has_pdf(client: Client, data: dict, meta: dict, doing: str) -> bool:
    """Whether an item holds a PDF already among its attachments, asked only when it has children."""
    if not int(seconds((meta or {}).get("numChildren")) or 0):
        return False
    got, _ = client.json("GET", client.lib(f"/items/{data['key']}/children"), doing)
    return any(isinstance(o, dict) and (o.get("data") or {}).get("itemType") == "attachment"
               and (o.get("data") or {}).get("contentType") == "application/pdf" for o in got or [])


def find_collection(client: Client, name: str) -> tuple[dict | None, str]:
    """The collection at the library's top whose name is the project's, or None, and the library's
    version it was read at."""
    every, version = client.listing("/collections", sift_words.t("sift_server.zotero.reading_the_collections"))
    want = norm(name)
    for c in every:
        d = c.get("data") or {}
        if norm(d.get("name")) == want and not d.get("parentCollection"):
            return c, version
    return None, version


def items_by_key(client: Client, keys) -> dict[str, dict]:
    """The items whose keys the CSV holds, fifty a request, each as the API gives it, an item gone from
    the library left out."""
    keys = sorted({k for k in keys if re.fullmatch(r"[A-Z0-9]{8}", k or "")})
    out = {}
    for i in range(0, len(keys), BATCH):
        got, _ = client.json("GET", client.lib("/items"), sift_words.t("sift_server.zotero.reading_the_items_sift_made"),
                             params={"itemKey": ",".join(keys[i:i + BATCH]), "limit": BATCH})
        for o in got or []:
            if isinstance(o, dict) and o.get("key"):
                out[o["key"]] = o
    return out


def survey(client: Client, folder, name: str, which: str = "included", ids=None) -> dict:
    """What a sync would do, read from Zotero and the screening, nothing written: the collection and
    whether it stands, and for each record its item or none, what that item lacks and whether its PDF
    goes up. `adds`, `updates`, `leaves` and `pdfs` count them."""
    sc = sift.load(folder)
    held = sift.states(sift.read_log(folder))
    picked = chosen_ids(sc, held, which, ids)
    keyed = {rec: sc.cell(rec, sift.ZOTERO_COLUMN).strip() for rec in sc.ids if sc.cell(rec, sift.ZOTERO_COLUMN).strip()}
    coll, version = find_collection(client, name)
    known = items_by_key(client, keyed.values())
    pool = client.listing(f"/collections/{coll['key']}/items/top", sift_words.t("sift_server.zotero.reading_the_collection"))[0] if coll else []
    by_doi, by_title = {}, {}
    for o in pool:
        d = o.get("data") or {}
        doi = norm_doi(d.get("DOI") or next((ln.split(":", 1)[1] for ln in str(d.get("extra") or "").splitlines()
                                              if ln.lower().startswith("doi:")), ""))
        if doi:
            by_doi.setdefault(doi, o)
        title = norm(d.get("title"))
        if title:
            by_title.setdefault(title, []).append(o)
    taken: set[str] = set()
    plan = []
    coll_key = coll["key"] if coll else ""
    for rec in picked:
        item = known.get(keyed.get(rec, ""))
        if item is None:
            doi = norm_doi(sc.cell(rec, "doi"))
            item = by_doi.get(doi) if doi else None
            if item is None:
                year = sc.cell(rec, "year").strip()[:4]
                for o in by_title.get(norm(sc.cell(rec, "title")), []):
                    date = str((o.get("data") or {}).get("date") or "")
                    if not year or not date or year in date:
                        item = o
                        break
            if item is not None and item.get("key") in taken:
                item = None
        tags = tags_of(sc, held, rec)
        pdf = sift.pdf_path(folder, rec)
        if item is None:
            plan.append({"rec_id": rec, "act": "add", "tags": tags, "pdf": pdf is not None})
            continue
        taken.add(item["key"])
        data = item.get("data") or {}
        patch = patch_of(data, sc, rec, coll_key, tags, True)
        if not coll_key:
            patch["collections"] = list(data.get("collections") or [])     # put right once the collection is made
        goes = pdf is not None and not has_pdf(client, data, item.get("meta") or {}, sift_words.t("sift_server.zotero.reading_an_item_s_attachments"))
        plan.append({"rec_id": rec, "act": "update" if patch else "leave", "key": item["key"], "version": item.get("version"),
                     "patch": patch, "tags": tags, "pdf": goes, "relink": keyed.get(rec) != item["key"]})
    for rec, key in keyed.items():
        if rec in picked or key in taken or key not in known:
            continue
        data = known[key].get("data") or {}
        patch = patch_of(data, sc, rec, "", [], False)
        taken.add(key)
        plan.append({"rec_id": rec, "act": "update" if patch else "leave", "key": key, "version": known[key].get("version"),
                     "patch": patch, "tags": [], "pdf": False, "relink": False, "unchosen": True})
    count = lambda act: sum(1 for p in plan if p["act"] == act)
    return {"collection": name, "collection_key": coll_key, "collection_there": coll is not None, "library_version": version,
            "chosen": len(picked), "plan": plan, "adds": count("add"), "updates": count("update"),
            "leaves": count("leave"), "pdfs": sum(1 for p in plan if p["pdf"])}


def n_items(n: int) -> str:
    return sift_words.t("sift_server.zotero.n_items", n=n)


def n_pdfs(n: int) -> str:
    return sift_words.t("sift_server.zotero.n_pdfs", n=n)


def preview_line(s: dict) -> str:
    """The preview in one line: what Sync adds, updates and leaves, the PDFs it uploads, and the
    collection, made when it is not there."""
    where = (sift_words.t("sift_server.zotero.the_collection", name=s['collection']) if s["collection_there"]
             else sift_words.t("sift_server.zotero.the_collection_made", name=s['collection']))
    return sift_words.t("sift_server.zotero.preview", where=where, adds=n_items(s['adds']), updates=s['updates'], leaves=s['leaves'],
                  pdfs=n_pdfs(s['pdfs']))


def done_line(d: dict) -> str:
    line = sift_words.t("sift_server.zotero.done", added=n_items(d['added']), updated=d['updated'], left=d['left'],
                  pdfs=n_pdfs(d['uploaded']), name=d['collection'])
    return line + (f" {d['said']}" if d.get("said") else "")


def public(s: dict) -> dict:
    """A survey as the page and the command line take it, without the items' own data."""
    return {k: s[k] for k in ("collection", "collection_there", "chosen", "adds", "updates", "leaves", "pdfs")} \
        | {"said": preview_line(s)}


# ------------------------------------------------------------------ the sync

def token() -> str:
    return secrets.token_hex(16)


def make_collection(client: Client, name: str, version: str) -> str:
    """The collection made at the library's top, sent with the library's version it was looked for at,
    so one made meanwhile elsewhere is found rather than made twice."""
    for _ in range(2):
        heads = {"Zotero-Write-Token": token()}
        if version:
            heads["If-Unmodified-Since-Version"] = version
        status, head, got = client.send("POST", client.lib("/collections"), data=[{"name": name, "parentCollection": False}],
                                        headers=heads)
        if status == 412:
            found, version = find_collection(client, name)
            if found:
                return found["key"]
            continue
        if status != 200:
            raise client.fail(status, got, sift_words.t("sift_server.zotero.making_the_collection"))
        try:
            done = json.loads(got.decode("utf-8"))
        except ValueError:
            done = {}
        key = (done.get("success") or {}).get("0") or ((done.get("successful") or {}).get("0") or {}).get("key")
        if key:
            return key
        failed = (done.get("failed") or {}).get("0") or {}
        raise ZoteroError(client.scrub(sift_words.t("sift_server.zotero.zotero_would_not_make_the",
                                                 message=failed.get('message') or sift_words.t("sift_server.zotero.no_reason_given"))))
    raise ZoteroError(sift_words.t("sift_server.zotero.the_library_kept_changing_while"))


def write_many(client: Client, objects: list[dict], doing: str) -> list[tuple[str | None, str]]:
    """New objects written fifty at a time, each batch with its own write token, answering each one's
    key or None and the reason Zotero gave for one it refused."""
    out = []
    for i in range(0, len(objects), BATCH):
        part = objects[i:i + BATCH]
        got, _ = client.json("POST", client.lib("/items"), doing, data=part, headers={"Zotero-Write-Token": token()})
        got = got if isinstance(got, dict) else {}
        for n in range(len(part)):
            key = (got.get("success") or {}).get(str(n)) or ((got.get("successful") or {}).get(str(n)) or {}).get("key")
            failed = (got.get("failed") or {}).get(str(n)) or {}
            out.append((key, "" if key else client.scrub(failed.get("message") or sift_words.t("sift_server.zotero.zotero_gave_no_reason"))))
    return out


def change(client: Client, sc, rec: str, step: dict, coll: str) -> bool:
    """One item changed with the version it was read at, and when Zotero answers that it has changed
    since, read again and tried once more. Answers whether it changed."""
    key, version, patch = step["key"], step.get("version"), step["patch"]
    for _ in range(2):
        heads = {"If-Unmodified-Since-Version": str(version)} if version is not None else {}
        status, _, got = client.send("PATCH", client.lib(f"/items/{key}"), data=patch, headers=heads)
        if status in (200, 204):
            return True
        if status != 412:
            raise client.fail(status, got, sift_words.t("sift_server.zotero.changing_an_item"))
        fresh, _ = client.json("GET", client.lib(f"/items/{key}"), sift_words.t("sift_server.zotero.reading_an_item_again"))
        data = (fresh or {}).get("data") or {}
        version = (fresh or {}).get("version")
        patch = patch_of(data, sc, rec, coll if not step.get("unchosen") else "", step["tags"] if not step.get("unchosen")
                         else [], not step.get("unchosen"))
        if not patch:
            return False
    raise ZoteroError(sift_words.t("sift_server.zotero.an_item_kept_changing_in"))


def upload(client: Client, sc, rec: str, parent: str) -> bool:
    """A record's PDF put on its item: the attachment item made, then authorised, uploaded and
    registered, the three steps of Zotero's file upload. Answers whether a PDF went up."""
    path = sift.pdf_path(sc.folder, rec)
    if path is None:
        return False
    data = path.read_bytes()
    if len(data) > PDF_MAX:
        raise ZoteroError(sift_words.t("sift_server.zotero.the_pdf_of_is_over", rec=rec))
    name = pdf_name(sc, rec)
    made = write_many(client, [{"itemType": "attachment", "parentItem": parent, "linkMode": "imported_file",
                                "title": PDF_TITLE, "contentType": "application/pdf", "charset": "", "filename": name,
                                "tags": [], "relations": {}}], "making the PDF's attachment")
    att, why = made[0]
    if not att:
        raise ZoteroError(sift_words.t("sift_server.zotero.zotero_would_not_take_the", rec=rec, why=why))
    mtime = int(path.stat().st_mtime * 1000)
    md5 = hashlib.md5(data).hexdigest()
    got, _ = client.json("POST", client.lib(f"/items/{att}/file"), "authorising the PDF's upload",
                         form={"md5": md5, "filename": name, "filesize": len(data), "mtime": mtime},
                         headers={"If-None-Match": "*"})
    got = got if isinstance(got, dict) else {}
    if got.get("exists"):
        return True
    url = str(got.get("url") or "")
    if not (url.startswith("https://") or ss.stub_base()):
        raise ZoteroError(sift_words.t("sift_server.zotero.zotero_gave_an_upload_address"))
    body = str(got.get("prefix") or "").encode("utf-8") + data + str(got.get("suffix") or "").encode("utf-8")
    status, _, sent = client.send("POST", url, raw=body, headers={"Content-Type": str(got.get("contentType") or "application/pdf")},
                                  keyed=False)
    if status not in (200, 201, 204):
        raise client.fail(status, sent, "uploading the PDF")
    status, _, sent = client.send("POST", client.lib(f"/items/{att}/file"), form={"upload": str(got.get("uploadKey") or "")},
                                  headers={"If-None-Match": "*"})
    if status not in (200, 204):
        raise client.fail(status, sent, "registering the PDF")
    return True


def sync(folder, cfg, which: str = "included", ids=None, name: str | None = None, dry_run: bool = False,
         call=None, sleep=None, progress=None) -> dict:
    """The sync: the survey, and unless `dry_run` the collection made when it is not there, the new
    items written fifty at a time and their keys put in the CSV, each item that lacks something
    changed, and each PDF uploaded. `progress(done, of)` hears each step. Nothing is ever deleted.
    The answer holds the counts and `said`, the line the screen and the command line say."""
    s = settings_of(cfg)
    if s["library"] == "group":
        prefix_of(s)
    key = read_key()
    if not key:
        raise ZoteroError(_w("NO_KEY"))
    client = Client(key, "", call, sleep)
    client.prefix = prefix_of(s, digits(key_record(client).get("userID")) if s["library"] == "user" else "")
    folder = Path(folder)
    name = sift.one_line(name) or project_name(folder)
    if dry_run:
        return public(survey(client, folder, name, which, ids))
    lock = locks.held(folder / LOCK_NAME, wait=0)
    try:
        lock.__enter__()
    except WorkbookError:
        raise ZoteroError(sift_words.t("sift_server.routes.a_sync_of_this_screening")) from None
    try:
        return run(client, folder, name, which, ids, progress)
    finally:
        lock.__exit__(None, None, None)


def run(client: Client, folder: Path, name: str, which: str, ids, progress) -> dict:
    s = survey(client, folder, name, which, ids)
    plan = s["plan"]
    steps = sum(1 for p in plan if p["act"] != "leave") + s["pdfs"]
    done = {"n": 0}

    def heard() -> None:
        done["n"] += 1
        if progress:
            progress(done["n"], steps)

    if progress:
        progress(0, steps)
    coll = s["collection_key"] or make_collection(client, name, s["library_version"])
    sc = sift.load(folder)
    out = {"collection": name, "added": 0, "updated": 0, "left": s["leaves"], "uploaded": 0, "refused": [], "said": ""}
    keys: dict[str, str] = {}
    adds = [p for p in plan if p["act"] == "add"]
    for i in range(0, len(adds), BATCH):
        part = adds[i:i + BATCH]
        made = write_many(client, [new_item(client, sc, p["rec_id"], coll, p["tags"]) for p in part], sift_words.t("sift_server.zotero.adding_the_items"))
        batch = {}
        for p, (key, why) in zip(part, made):
            if key:
                p["key"] = key
                batch[p["rec_id"]] = key
                out["added"] += 1
            else:
                out["refused"].append(f"{p['rec_id']}: {why}")
                p["pdf"] = False
            heard()
        if batch:
            sift.write_zotero(folder, batch)
            keys.update(batch)
    for p in plan:
        if p["act"] == "update":
            if not s["collection_key"] and not p.get("unchosen"):
                data_colls = p["patch"].get("collections") or []
                p["patch"]["collections"] = data_colls + ([coll] if coll not in data_colls else [])
            if change(client, sc, p["rec_id"], p, coll):
                out["updated"] += 1
            else:
                out["left"] += 1
            heard()
        if p["act"] in ("update", "leave") and p.get("relink"):
            keys[p["rec_id"]] = p["key"]
    relinks = {rec: k for rec, k in keys.items() if sc.cell(rec, sift.ZOTERO_COLUMN).strip() != k}
    if relinks:
        sift.write_zotero(folder, relinks)
    for p in plan:
        if not p["pdf"] or not p.get("key"):
            continue
        try:
            if upload(client, sc, p["rec_id"], p["key"]):
                out["uploaded"] += 1
        except ZoteroError as exc:
            out["said"] = str(exc)
            if exc.code == "zotero_storage_full":
                break
        heard()
    if out["refused"]:
        out["said"] = (sift_words.t("sift_server.zotero.refused", items=n_items(len(out['refused'])), first=out['refused'][0])
                       + " " + out["said"]).strip()
    out["note"] = out["said"]
    out["said"] = done_line(out)
    return out
