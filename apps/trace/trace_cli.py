"""Trace's command line (22 October 2026, the family codebase's second build, from cli.py): `trace <folder>
[<document>]`, a Trace project by its folder, which only reads, its arguments, its words and its Search over
a project by its folder, registered with the family's command line by `cli.register`, which the command
line's import of this module by its name makes (`boot.load`). `./trace` runs it at its top, as `idiograph
trace` did under Idiograph until the cutover (23 October 2026). A reference's PDF is looked for in the screenings of
Sift's projects as Trace's routes find them (`trace_routes.found_in`). See docs/agents-trace.md.
"""
from __future__ import annotations

import argparse
from pathlib import Path

import cli
import i18n
import server as srv
import trace_claims as trace_mod
import trace_find
import trace_routes as routes
from errors import WorkbookError

TRACE_ABOUT = ("Trace's command line, for an AI agent in a conversation: a Trace project's manuscripts and each "
               "claim with his judgement, to read, trace <folder> [document]. trace search <words> --folder "
               "<folder> is Trace's Search. See docs/agents-trace.md.")
SEARCH_REFUSED = "Trace's Search reads one project by its folder: trace search <words> --folder <folder>."


def trace_row_said(r: dict) -> str:
    """A row of Trace in one line: a claim with his judgement and the day he gave it, its reference and its
    sentence, its PDF and his note, a citation with no reference by its form, or a reference never cited."""
    pdf = i18n.t("trace_cli.trace_row_said.pdf") if r["pdf"] else i18n.t("trace_cli.trace_row_said.no_pdf")
    if r["kind"] == "missing":
        return i18n.t("trace_cli.trace_row_said.no_reference", short=r['short'], section=r['section'], sentence=r['sentence'])
    if r["kind"] == "uncited":
        return i18n.t("trace_cli.trace_row_said.never_cited", ref=r['ref'], reference=r['reference'], pdf=pdf)
    judged = f"{trace_mod.JUDGEMENTS[r['judged']]} {r['set']}" if r["judged"] else i18n.t("trace_cli.trace_row_said.not_judged")
    return (f"{judged}  {r['key']}  {r['short']}  {r['section']}: {r['sentence']}{pdf}"
            f"{i18n.t('trace_cli.trace_row_said.note') + ' '.join(r['note'].split()) if r['note'] else ''}")


def cmd_trace(args) -> tuple:
    """`trace <folder> [<document>]`: a Trace project by its folder, which only reads (15 October). With no
    document each manuscript with its counts and the reference list, and with one, named by its files' name
    or its file's name, each claim in the manuscript's order, its sentence whole with the sentence before
    where it leans on it, its section and reference, his judgement, Supports, Question or Doesn't support
    with the day he gave it, his note, the reference's PDF and the AI's passages with their model, each
    citation no reference answers, each reference never cited, and every line of its log. No act judges a
    claim or writes a note, which are his alone in Trace, and none calls a model. The manuscript is read as
    it now stands and never written."""
    given = Path(args.folder).expanduser()
    if not given.is_dir():
        raise cli.Refused(i18n.t("trace_cli.trace.that_folder_is_not_there"))
    try:
        folder = trace_mod.to_open(given)
    except WorkbookError as exc:
        raise cli.Refused(str(exc)) from None
    name = trace_mod.own_name(folder)
    entries = trace_mod.docs(folder)
    held = trace_mod.list_of(folder)
    found_in = routes.found_in()
    doc_named = getattr(args, "document", None)
    if not doc_named:
        out = []
        lines = [i18n.t("trace_cli.trace.trace_project", name=name, manuscripts=i18n.t("trace_cli.n.manuscript", n=len(entries)))
                 + (i18n.t("trace_cli.trace.its_reference_list", name=held['name']) if held else ".")]
        for d in entries:
            c = trace_mod.counts(trace_mod.rows(folder, d["doc"], screenings=found_in))
            out.append(dict(d, path=srv.display_path(srv.rel_path(Path(d["path"]))), counts=c))
            lines.append(i18n.t("trace_cli.trace.judged_supports_question_doesn_t_support", doc=d['doc'], name=d['name'], claims=i18n.t("trace_cli.n.claim", n=c['claims']), judged=c['judged'], supports=c['supports'], question=c['question'], not_supported=c['not_supported'], citations=i18n.t("trace_cli.n.citation", n=c['no_reference']), never_cited=c['never_cited'], pdf=c['pdf'], references=i18n.t("trace_cli.n.reference", n=c['references'])))
        listed = dict(held, path=srv.display_path(srv.rel_path(Path(held["path"])))) if held else None
        return {"project": name, "documents": out, "list": listed}, lines
    doc = next((d["doc"] for d in entries if doc_named in (d["doc"], d["name"])), None)
    if doc is None:
        raise cli.Refused(i18n.t("trace_cli.trace.the_documents_are", no_doc=trace_mod.NO_DOC, list=', '.join(d['doc'] for d in entries) or i18n.t("trace_cli.trace.none_yet")))
    view = trace_mod.rows(folder, doc, screenings=found_in)
    c = trace_mod.counts(view)
    view = dict(view, path=srv.display_path(srv.rel_path(Path(view["path"]))), counts=c, log=trace_mod.history(folder, doc))
    lines = [i18n.t("trace_cli.trace.in_judged_not_judged", name=view['name'], name2=name, claims=i18n.t("trace_cli.n.claim", n=c['claims']), judged=c['judged'], not_judged=c['not_judged'])]
    for r in view["rows"]:
        lines.append(trace_row_said(r))
        if r["before"]:
            lines.append(i18n.t("trace_cli.trace.the_sentence_before", before=r['before']))
        p, model = r.get("passage"), (r.get("passages") or {}).get("model")
        if p and p.get("passage"):
            lines.append(i18n.t("trace_cli.trace.ai_passages_page", model=model, page=p['page'], passage=p['passage']))
        elif p:
            lines.append(i18n.t("trace_cli.trace.ai_passages", model=model, failed=trace_mod.FAILED if p.get('unverified') else trace_mod.NOT_FOUND))
    for e in view["log"]:
        at, what = e.get("at", ""), e.get("claim") or e.get("ref")
        if e.get("act") in ("judge", "check"):
            lines.append(f"  {at}  {what}: {e.get('words')}.")
        elif e.get("act") == "note":
            lines.append(i18n.t("trace_cli.trace.the_researchers_note", at=at, what=what))
        elif e.get("act") == "undo":
            lines.append(i18n.t("trace_cli.trace.undone_line", at=at, what=what, get=e.get('undoes')))
        elif e.get("act") in ("passages", "pointer"):
            lines.append(i18n.t("trace_cli.trace.the_ais_passages", at=at, what=what, get=(e.get('passages') or e.get('pointer') or {}).get('model')))
    return view, lines


def add_trace_arguments(x) -> None:
    """The `trace` command's arguments, at the top of the `trace` command, and under `idiograph trace` until the cutover."""
    x.add_argument("folder", help="the Trace project's folder")
    x.add_argument("document", nargs="?", help="the manuscript, by the name its files take or its file's name")
    x.add_argument("--json", action="store_true", default=argparse.SUPPRESS, help="exact output, as JSON")
    x.add_argument("--config", default=argparse.SUPPRESS, help="a settings file in place of Trace's own, for a trial")


def search_hit(hit: dict, go: dict) -> None:
    """A Search hit landing on Trace's screen: its manuscript, and trace_claims, which opens it whole."""
    hit["document"] = go.get("doc", "")
    args = {"folder": go.get("folder", "")}
    if go.get("doc"):
        args["document"] = go["doc"]
    hit["open"] = cli.opener("trace_claims", args, ["trace", go.get("folder", "")] + ([go["doc"]] if go.get("doc") else []))


# The keys whose strings Trace's answers keep plain for an agent (Adam, 2 November 2026, by dialog: mark Trace's
# text too), every other string marked as {"untrusted_text": ...} by `cli.mark`, since a manuscript's claims,
# its headings and its references' words, a PDF's passages and his notes are words anyone may have written.
# Only what Trace makes is named here: a claim's and a reference's keys, a manuscript's id, kinds, judgements,
# dates, the log's own words and the files and folders it names.
TRACE_PLAIN = (
    # keys Trace makes: a claim's, a reference's, a manuscript's, a line of the log's
    "key", "claim", "ref", "doc", "document", "n", "undoes",
    # what an agent hands back as an input
    "folder",
    # Trace's own kinds, a judgement Y, Q or N, an act, who made it and where a reference came from
    "kind", "kind_name", "judged", "act", "what", "by", "source",
    # dates and times
    "at", "added", "made", "set",
    # the log's line in Trace's own words, and the files it names
    "words", "file", "files",
    # the client that acted, the command that opens a hit, the search an agent sent, said back, and its cursor
    "tool", "command", "q", "scope", "kinds", "more",
)

cli.register("trace", cmd_trace, add_trace_arguments, TRACE_ABOUT, folder=trace_mod.to_open,
             found=trace_find.trace_found, screen="trace", hit=search_hit, search_refused=SEARCH_REFUSED,
             plain=TRACE_PLAIN, named=trace_mod.own_name)
