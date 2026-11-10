"""Sift's part of Search (22 October 2026, the family codebase's third build, from app_search.py): what a
Sift project holds that the words typed are in, the records of the screening its Screening step opens, each
record's title, its ID with it, abstract, authors and journal, his decision notes at each stage, his own
fields, his form's answers and his key excerpts, from `screening.csv`, its log and `sift.json`, and its plan's
search terms and exclusion reasons, the newest version of `search_plan.json` and the review's `reasons.csv`,
each read only. Its kinds and its finder are registered with the family's Search engine, `app_search.register`,
which the engine's import of this module by its name makes (`boot.load`). AI proposals and PDFs' text stay
out.
"""
from __future__ import annotations

import sift_words
import time
from pathlib import Path

import app_search as engine
import sift as sift_mod
import sift_search as plan_mod

# Sift's kinds (18 October): a record by its title, abstract, authors or journal, then what he wrote of it,
# his decision note, his own fields, his form's answers and his key excerpts, then the plan's search terms
# and its exclusion reasons
SIFT_KINDS = ("record", "dnote", "field", "form", "excerpt", "term", "reason")
# a record's parts as the record names them, the ID searched with the title
RECORD_PARTS = (("title", lambda: sift_words.t("sift_server.find.title")), ("authors", lambda: sift_words.t("sift_server.find.authors")),
                ("journal", lambda: sift_words.t("sift_server.find.journal")), ("abstract", lambda: sift_words.t("sift_server.find.abstract")))
# his own fields beside his columns, as the record names them
OWN_FIELDS = (("notes", lambda: sift_words.t("sift_server.find.notes")), ("digest", lambda: sift_words.t("sift_server.find.digest")),
              ("critique", lambda: sift_words.t("sift_server.find.critique")))
# each said as the search is run, in the run's language
STAGE_SAID = {"ta": lambda: sift_words.t("sift_server.find.ta"), "ft": lambda: sift_words.t("sift_server.find.ft")}
PLAN_SAID = lambda: sift_words.t("sift_server.find.plan")  # noqa: E731
# This module's words for a person, read in the run's language when said: inside the module through `_w`,
# from others and the checks as the module's names (`__getattr__`)
SAID = {
    "NO_SIFT": lambda: sift_words.t("sift_server.find.no_sift"),
}


def _w(name: str) -> str:
    return SAID[name]()


def __getattr__(name: str) -> str:
    """This module's words other modules and the checks name, read in the run's language."""
    if name in SAID:
        return SAID[name]()
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
# each kind by its name, one and many, as the card names them (`SEARCH_KINDS` in search.js)
NAMES = {"record": ("Record", "Records"), "dnote": ("Decision note", "Decision notes"), "field": ("Field", "Fields"),
         "form": ("Form answer", "Form answers"), "excerpt": ("Key excerpt", "Key excerpts"),
         "term": ("Search term", "Search terms"), "reason": ("Exclusion reason", "Exclusion reasons")}


# ------------------------------------------------------------------ a screening and its plan

def screening_items(folder: Path) -> list[dict]:
    """Every record of a screening as Sift holds it, read only: its title, searched with its ID, its
    authors, its journal and its abstract, his note on its decision at each stage, his notes, digest and
    critique and each column of his, a column on the form of Extract and appraise as one of the form's
    answers, and his key excerpts, record by record in the CSV's order. `where` is the record's ID and the
    part, "R010 · Abstract", and `go` the record, the stage it lands at and the part, the field or the
    excerpt it shows. A record lands at full text once it has Yes or Maybe at title and abstract, a form's
    answer at Extract and appraise while the record is one of its papers, and a note or an excerpt at the
    stage it was made at while the record still stands there."""
    sc = sift_mod.load(folder)
    state = sift_mod.states(sift_mod.read_log(folder))
    table = sift_mod.read_settings(folder).get("table")
    own = sift_mod.own_columns(table if isinstance(table, dict) else {}, sc)
    extract = set(sift_mod.included_ids(sc, state)) | set(sift_mod.benchmark_ids(sc))
    out = []
    for n, rec in enumerate(sc.ids):
        full = sift_mod.in_stage(sc, state, rec, "ft")
        stage = "ft" if full else "ta"
        go = {"screen": "sift", "rec": rec, "stage": stage}
        for k, (part, said) in enumerate(RECORD_PARTS):
            text = engine.flat(sift_mod.plain(sc.cell(rec, part)))
            if not text:
                continue
            one = engine.item("record", text, f"{rec} · {said()}", dict(go, field=part), (n, k))
            if part == "title":
                one["s"] = f"{rec} {text}"
                one["f"] = engine.fold(one["s"])
            out.append(one)
        for k, at in enumerate(sift_mod.STAGES):
            note = engine.flat(sift_mod.state_of(sc, state, rec, at)["note"])
            if note:
                lands = at == "ta" or full
                out.append(engine.item("dnote", note, f"{rec} · {STAGE_SAID[at]()}",
                                dict(go, stage=at if lands else "ta", field="note" if lands else ""), (n, 10 + k)))
        for k, (name, said) in enumerate(OWN_FIELDS):
            text = engine.flat(sc.cell(rec, name))
            if text:
                out.append(engine.item("field", text, f"{rec} · {said()}", dict(go, field=name), (n, 20 + k)))
        for k, c in enumerate(own):
            value = sc.cell(rec, c["key"])
            if not value.strip():
                continue
            text = engine.flat(sift_mod.form_cell(c, value))
            if sift_mod.on_form(c):
                out.append(engine.item("form", text, f"{rec} · {c['name']}",
                                dict(go, stage="ex" if rec in extract else stage, field=c["key"], form=True), (n, 100 + k)))
            else:
                out.append(engine.item("field", text, f"{rec} · {c['name']}", dict(go, field=c["key"]), (n, 100 + k)))
        for k, x in enumerate(sift_mod.excerpts_of(sc.cell(rec, sift_mod.EXCERPTS_COLUMN))):
            at = x["stage"] if x["stage"] == "ta" or full else "ta"
            out.append(engine.item("excerpt", x["text"], f"{rec} · {STAGE_SAID[x['stage']]()}",
                            dict(go, stage=at, field="excerpt", line=k), (n, 1000 + k)))
    return out


def plan_items(review: Path) -> list[dict]:
    """A review's plan as Search strategy shows it, read only: the newest version's search terms, block by
    block, as typed, and its exclusion reasons, the review folder's own `reasons.csv` where it holds one, a
    reason searched by its code and its meaning. `where` says Search strategy and the block, with its name
    when it has one, or the reason's code, and `go` the block and the term's line, or the reason's row."""
    last = plan_mod.newest(plan_mod.read_file(review))
    plan = plan_mod.clean_plan(last["plan"]) if last else plan_mod.blank_plan()
    kept = plan_mod.file_reasons(review)
    reasons = kept["reasons"] if kept else plan["reasons"]
    out = []
    for i, block in enumerate(plan["blocks"]):
        head = " · ".join(p for p in (PLAN_SAID(), sift_words.t("sift_server.block", i=i + 1), block["name"]) if p)
        for j, term in enumerate(block["terms"]):
            out.append(engine.item("term", term, head, {"screen": "searches", "block": i, "line": j}, (i, j)))
    for i, r in enumerate(reasons):
        one = engine.item("reason", r["meaning"] or r["code"], f"{PLAN_SAID()} · {r['code']}", {"screen": "searches", "reason": i},
                   (10000, i))
        one["s"] = f"{r['code']} {r['meaning']}"
        one["f"] = engine.fold(one["s"])
        out.append(one)
    return out


def sift_found(words: list[str], screening: Path | None, screening_id: str = "", review: Path | None = None,
               review_id: str = "") -> list[dict]:
    """What a Sift project holds that every word typed is in: the records of `screening`, the one its
    Screening step opens or the one on the screen, read from its CSV, its log, `sift.json` and, for the
    benchmark papers Extract and appraise opens, the plan above it, and the plan of `review`, each `go`
    naming its folder as the page does, `screening_id` or `review_id`."""
    found = []
    if screening is not None:
        above = sift_mod.review_of(screening)
        also = (sift_mod.log_path(screening), Path(screening) / sift_mod.SETTINGS_NAME) + (
            (plan_mod.plan_path(above),) if above is not None else ())
        for it in engine.held(sift_mod.csv_path(screening), "screening", lambda _p: screening_items(screening), also=also):
            if engine.hit(it, words):
                found.append(dict(it, go=dict(it["go"], folder=screening_id), rank=0, path=""))
    if review is not None:
        for it in engine.held(plan_mod.plan_path(review), "plan", lambda _p: plan_items(review),
                       also=(Path(review) / sift_mod.REASONS_NAME,)):
            if engine.hit(it, words):
                found.append(dict(it, go=dict(it["go"], folder=review_id), rank=0, path=""))
    return found


def search_sift(q: str, screening: Path | None, screening_id: str = "", review: Path | None = None,
                review_id: str = "", kinds=(), limit: int = engine.LIMIT, whole: bool = False,
                match_case: bool = False) -> dict:
    """The results of `q` over a Sift project, its screening's records and its plan (see `sift_found`), `whole`
    and `match_case` being Whole word and Match case."""
    started = time.perf_counter()
    q, words, phrase = engine.query(q, whole, match_case)
    found = engine.phrased(sift_found(words, screening, screening_id, review, review_id) if words else [], phrase)
    return engine.answer(q, "sift", words, found, started, kinds=kinds, limit=limit)


engine.register("sift", SIFT_KINDS,
                lambda words, p: sift_found(words, p.get("screening"), p.get("screening_id", ""), p.get("review"),
                                            p.get("review_id", "")),
                NAMES, ("records", ("record", "dnote", "field", "form", "excerpt")), ("plan", ("term", "reason")))
