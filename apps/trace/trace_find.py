"""Trace's part of Search (22 October 2026, the family codebase's second build, from app_search.py): what a
Trace project holds that the words typed are in, each manuscript's claims, the references they cite and
his notes on the claims, the manuscript read as Trace reads it, with the project's reference list and
each manuscript's log, read only. Its kinds and its finder are registered with the family's Search engine,
`app_search.register`, which the engine's import of this module by its name makes (`boot.load`). AI
passages and PDFs' text stay out.
"""
from __future__ import annotations

import time
from pathlib import Path

import app_search as engine
import trace_claims as trace_mod

# Trace's kinds: a claim, the reference it cites and his note on the claim
TRACE_KINDS = ("claim", "reference", "cnote")
NO_TRACE = "Say which Trace project, so nothing was searched."
# each kind by its name, one and many, as the card names them (`SEARCH_KINDS` in search.js)
NAMES = {"claim": ("Claim", "Claims"), "reference": ("Reference", "References"), "cnote": ("Claim note", "Claim notes")}


def manuscript_items(folder: Path, entry: dict) -> list[dict]:
    """One manuscript of a Trace project as Trace reads it, read only: each claim, the sentence that cites a
    reference, a citation no reference answers among them, his note on each claim, and each reference its
    claims take, cited or not, in the manuscript's order. `where` is the manuscript, the section and the
    reference as the claim cites it, "seed protocol.md · Background · Okafor, 2019", and `go` the manuscript
    and the row that opens, a reference's first claim or for one never cited its own row."""
    got = trace_mod.analyse(entry["path"], trace_mod.listed(folder))
    state = trace_mod.states(trace_mod.read_lines(folder, entry["doc"]))
    by = {r["key"]: r for r in got["references"]}
    name = entry["name"]
    go = {"screen": "trace", "doc": entry["doc"]}
    out = []
    for n, c in enumerate(got["claims"]):
        cited = trace_mod.short_of(by[c["ref"]]) if c["ref"] in by else str(c.get("missing") or "")
        where = " · ".join(p for p in (name, c.get("section") or "", cited) if p)
        out.append(engine.item("claim", engine.flat(c["sentence"]), where, dict(go, key=c["key"]), (n, 0)))
        note = engine.flat(trace_mod.claim_state(state, c["key"])["note"])
        if note:
            out.append(engine.item("cnote", note, where, dict(go, key=c["key"], field="note"), (n, 1)))
    for m, r in enumerate(got["references"]):
        first = r["claims"][0]["key"] if r.get("claims") else r["key"]
        out.append(engine.item("reference", engine.flat(r["text"]), name, dict(go, key=first), (100000 + m, 0)))
    return out


def list_items(path: Path, name: str) -> list[dict]:
    """A Trace project's reference list alone, before any manuscript, read only: each reference, its own row
    to open."""
    return [engine.item("reference", engine.flat(r["text"]), name, {"screen": "trace", "doc": "", "key": r["key"]}, (m, 0))
            for m, r in enumerate(trace_mod.read_list(path))]


def trace_found(words: list[str], folder: Path, folder_id: str = "") -> list[dict]:
    """What a Trace project holds that every word typed is in: each manuscript's items, read from the
    manuscript, the project's reference list and the manuscript's log, a reference two manuscripts share
    found once, at the first, or with no manuscript the reference list's, each `go` naming the project's
    folder as the page does, `folder_id`."""
    found, seen = [], set()
    listed = trace_mod.list_of(folder)
    list_path = Path(listed["path"]) if listed else None
    docs = trace_mod.docs(folder)
    for entry in docs:
        also = (trace_mod.log_path(folder, entry["doc"]),) + ((list_path,) if list_path is not None else ())
        for it in engine.held(Path(entry["path"]), "manuscript", lambda _p, e=entry: manuscript_items(folder, e),
                              extra=(str(folder), entry["doc"]), also=also):
            if not engine.hit(it, words):
                continue
            if it["kind"] == "reference":
                if it["f"] in seen:
                    continue
                seen.add(it["f"])
            found.append(dict(it, go=dict(it["go"], folder=folder_id), rank=0, path=""))
    if not docs and list_path is not None:
        for it in engine.held(list_path, "trace-list", lambda p: list_items(p, listed["name"]), extra=str(folder)):
            if engine.hit(it, words):
                found.append(dict(it, go=dict(it["go"], folder=folder_id), rank=0, path=""))
    return found


def search_trace(q: str, folder: Path, folder_id: str = "", kinds=(), limit: int = engine.LIMIT, whole: bool = False,
                 match_case: bool = False) -> dict:
    """The results of `q` over a Trace project, its manuscripts' claims, references and notes (see
    `trace_found`), `whole` and `match_case` being Whole word and Match case."""
    started = time.perf_counter()
    q, words, phrase = engine.query(q, whole, match_case)
    found = engine.phrased(trace_found(words, folder, folder_id) if words else [], phrase)
    return engine.answer(q, "trace", words, found, started, kinds=kinds, limit=limit)


engine.register("trace", TRACE_KINDS, lambda words, p: trace_found(words, p["folder"], p.get("folder_id", "")),
                NAMES, ("claims", TRACE_KINDS))
