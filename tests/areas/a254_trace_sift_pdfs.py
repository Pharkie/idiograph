"""Trace's own app finds a reference's PDF in Sift's screenings again (22 October 2026, the family codebase's
second build, Adam's call taken on the plan's lean): it lost them in the split of 20 October, its own state
having no list of Sift's projects. Trace's routes read Sift's own list from Sift's state file, read and
never written, and since the cutover (the sixth build, 23 October 2026), when Idiograph stopped serving Trace and Sift,
whatever the state of the run asking holds."""
from __future__ import annotations

import hashlib
import json
import shutil
from pathlib import Path

from .support import check


def test_trace_sift_pdfs(scratch):
    print("\n254. Trace's own app finds a reference's PDF in Sift's screenings, reading Sift's list of its projects and "
          "never writing it, whatever list the run's own state holds")
    import server as server_mod
    import trace_claims as tr
    import trace_routes

    base = scratch / "trace-sift-254"
    shutil.rmtree(base, ignore_errors=True)
    base.mkdir(parents=True)
    sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()
    listing = lambda folder: sorted(p.relative_to(folder).as_posix() for p in Path(folder).rglob("*"))

    # an invented review of beekeeping, its screening and a record's PDF, and Sift's own list naming it
    review = base / "Hive review"
    (review / "pdfs").mkdir(parents=True)
    (review / "screening.csv").write_text(
        "rec_id,title,abstract,doi\nR001,Swarm timing in town apiaries,Hives swarm earlier in towns.,10.5555/hive.2020.3\n",
        encoding="utf-8")
    (review / "pdfs" / "R001.pdf").write_bytes(b"%PDF-1.4\n%%EOF\n")
    sift_state = base / "state.sift.json"
    sift_state.write_text(json.dumps({"recent": [], "sift_reviews": [{"folder": "Hive review", "opened": 1}]}), encoding="utf-8")
    # a Trace project whose manuscript cites that record by its DOI
    project = base / "Swarm notes"
    tr.make(project, "Swarm notes")
    manuscript = base / "swarm draft.md"
    manuscript.write_text("# Swarms\n\nTown hives swarm a week earlier (Abara, 2020).\n\n## References\n\n"
                          "Abara, N. (2020). Swarm timing in town apiaries. *Hive Studies*, 2, 1-9. "
                          "https://doi.org/10.5555/hive.2020.3\n", encoding="utf-8")
    doc = tr.add(project, manuscript)["doc"]
    before = (sha(sift_state), listing(review))

    held = server_mod.app_held()
    kept = (server_mod.STATE_MEMORY, trace_routes.SIFT_PATHS)
    try:
        trace_routes.SIFT_PATHS = lambda: {"state": sift_state, "base": base}
        # Trace's own app: its state has no list of Sift's, and Sift's own is read
        server_mod.use_app("trace")
        server_mod.STATE_MEMORY = {"recent": []}
        own = trace_routes.trace_screenings()
        row = next(r for r in tr.rows(project, doc, screenings=own)["rows"] if r["kind"] == "claim")
        gone_list = base / "no-state.sift.json"
        trace_routes.SIFT_PATHS = lambda: {"state": gone_list, "base": base}
        none_there = trace_routes.trace_screenings()
        gone_list.write_text("{not json", encoding="utf-8")
        unreadable = trace_routes.trace_screenings()
        trace_routes.SIFT_PATHS = lambda: {"state": sift_state, "base": base}
        # a run whose own state holds a list of Sift's projects, as Idiograph's did while it served Sift, still
        # reads Sift's own list alone
        server_mod.STATE_MEMORY = {"recent": [], "sift_reviews": [{"folder": str(base / "gone"), "opened": 1}]}
        state_list = trace_routes.trace_screenings()
    finally:
        server_mod.app_back(held)
        server_mod.STATE_MEMORY, trace_routes.SIFT_PATHS = kept

    check("254: in Trace's own app a claim's reference finds its PDF in a screening of a project in Sift's own list, "
          "by its DOI, as it did inside Idiograph",
          [p.resolve() for p in own] == [review.resolve()] and row["pdf"] is True, json.dumps({k: row.get(k) for k in ("pdf", "pdf_from", "ref")}))
    check("254: Sift's list and its screening are only read: the state file's bytes and the review's files as they were",
          (sha(sift_state), listing(review)) == before)
    check("254: with no state file of Sift's, or one that cannot be read, Trace finds none there and goes on",
          none_there == [] and unreadable == [])
    check("254: since the cutover Trace reads Sift's own list whatever list the run's own state holds",
          [p.resolve() for p in state_list] == [review.resolve()])
