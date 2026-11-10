"""Sift's command line (22 October 2026, the family codebase's third build, from cli.py): `sift <folder> <act>`,
a screening for a systematic review by its folder, `sift search <act> <folder>`, a review's searches, and
`sift zotero sync <folder>`, a sync to his Zotero library, with its arguments, its words, its Search over a
project by its folder and its hits' openers, registered with the family's command line by `cli.register`,
which the command line's import of this module by its name makes (`boot.load`). `./sift` runs it at its top,
as `idiograph sift` did under Idiograph until the cutover (23 October 2026). A screening or a review holds published
records and no participant's words, so it needs no project and no tick. See docs/agents-sift.md.
"""
from __future__ import annotations

import argparse
from pathlib import Path

import cli
import server as srv
import sift as sift_mod
import sift_find
import sift_routes as routes
import sift_search as search_mod
import sift_words
import sift_zotero as zotero_mod
from errors import WorkbookError

# The words this module says, read in the run's language when said (i18nleft4, 2 November 2026): other
# modules and the checks read them as the module's names, through `__getattr__`, as themes_ai's are
SAID = {
    "NO_YES": lambda **v: sift_words.t("sift_cli.said.no_yes", v),
}


def _w(name: str, **vals) -> str:
    return SAID[name](**vals)


def __getattr__(name: str) -> str:
    """This module's words other modules and the checks name, read in the run's language."""
    if name in SAID:
        return SAID[name]()
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")

SIFT_ABOUT = ("Sift's command line, for an AI agent in a conversation: a screening for a systematic review by its "
              "folder, sift <folder> list, with search first a review's search plan, strings and runs, sift search "
              "strings <folder>, and with zotero first a sync to his Zotero library. sift search <words> --folder "
              "<folder> is Sift's Search. See docs/agents-sift.md.")


# -------------------------------------------------------------------- sift

def sift_lines(name: str, c: dict) -> list[str]:
    """A screening's counts in plain lines, each stage's records, its decisions in the stage's words,
    Yes, Maybe and No or Include, Maybe and Exclude, with the reasons for No or Exclude, those still to
    screen, then the decisions against the proposal."""
    lines = [sift_words.t("sift_cli.sift_lines.screening", name=name, records=sift_words.t("sift_cli.n.record", n=c['records']))]
    for stage in sift_mod.STAGES:
        s = c["stages"][stage]
        w = sift_mod.SHOWN_WORDS[stage]
        reasons = ", ".join(f"{code} {n}" for code, n in s["reasons"].items())
        lines += [sift_words.t("sift_cli.sift_lines.decided_to_screen", capitalize=s['stage'].capitalize(), records=sift_words.t("sift_cli.n.record", n=s['records']), decided=s['decided'], undecided=s['undecided']),
                  f"  {w['include']} {s['include']}, {w['maybe']} {s['maybe']}, {w['exclude']} {s['exclude']}"
                  + (f" ({reasons})." if reasons else "."),
                  sift_words.t("sift_cli.sift_lines.with_a_proposal_matched_overruled_another", proposed=s['proposed'], matched=s['matched'], overruled=s['overruled'], reason_differs=s['reason_differs'], unproposed=s['unproposed'])]
    return lines


def round_words(stage: str, which: str) -> str:
    """A round in the stage's words for a heading line, To screen, Yes or Include and the rest (12 October)."""
    w = sift_mod.SHOWN_WORDS[sift_mod.stage_key(stage)]
    return {"undecided": sift_mod.TO_SCREEN.lower(), "maybe": w["maybe"], "accepted": w["include"], "rejected": w["exclude"],
            "all": "all", "differs": "differs from the proposal", "apart": "where we differ"}.get(which, which)


SIFT_ACTS = ("counts", "export", "prisma", "list", "show", "add", "propose", "reset", "form")




def proposal_said(p: dict, stage: str = "ta") -> str:
    """A proposal in the stage's words, \"proposed No E2 (csv)\", what made it after its source where that
    is said, \"(csv, keyword rules)\" or \"(sift, model: Opus 5.5)\" (14 October), or no proposal."""
    if not p.get("decision"):
        return sift_words.t("sift_cli.said.no_proposal")
    by = p.get("by") if p.get("by") and p.get("by") != sift_mod.BY_SIFT else ""
    return (sift_words.t("sift_cli.proposal_said.proposed", shown_word=sift_mod.shown_word(stage, p['decision']), v_=' ' + p['reason'] if p.get('reason') else '', get=p.get('source') or 'csv', v_2=', ' + by if by else ''))


def decision_said(stage, decision: str, reason: str = "") -> str:
    """A decision of his in the stage's words with its reason, \"No E2\", \"Include\" or \"To screen\", as the
    screen shows it (12 October). The files keep include, maybe and exclude."""
    try:
        word = sift_mod.shown_word(stage, decision)
    except sift_mod.SiftError:
        word = decision or sift_mod.TO_SCREEN
    return f"{word}{' ' + reason if reason else ''}"


def own_said(r: dict) -> str:
    """What a record's line says of its columns of 13 October when they say anything: retracted,
    corrected or an expression of concern, and the study he linked it to."""
    out = "".join(f", {k}" for k in r.get("notices") or [])
    return out + (f", {r['study']}" if r.get("study") else "")


MONTHS = ("January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November",
          "December")


def notice_day(iso: str) -> str:
    """A notice's date as a line says it, 9 January 2031, November 2030 for a month alone, or its year."""
    parts = str(iso or "").split("-")
    if len(parts) == 2 and parts[1].isdigit() and 1 <= int(parts[1]) <= 12:
        return f"{MONTHS[int(parts[1]) - 1]} {parts[0]}"
    return search_mod.day_said(iso) if len(parts) == 3 else str(iso or "")


def facts_lines(r: dict, works: list) -> list[str]:
    """A record's columns from OpenAlex and Crossref and its study in plain lines, for `sift show`: each
    notice with its date and DOI, open access, the countries, the key works it cites while the review has
    any, the study he linked it to, and each record Sift suggests is a report of the same study, with its
    reasons. A column never asked says unknown, and key works Sift cannot check say why, as the record
    does (14 October, later)."""
    kinds, notices = r["notices"]["kinds"], r["notices"]["list"]
    said = [f"{n['kind']}" + (f" {notice_day(n['date'])}" if n.get("date") else "")
            + (sift_words.t("sift_cli.facts_lines.notice", doi=n['doi']) if n.get("doi") else sift_words.t("sift_cli.facts_lines.says", from_=n['from']) if n.get("from") else "") for n in notices]
    lines = [sift_words.t("sift_cli.facts_lines.retracted_or_corrected") + ("unknown" if kinds is None else sift_mod.and_join(said) or sift_mod.and_join(kinds) or "none") + "."]
    lines.append(sift_words.t("sift_cli.facts_lines.open_access") + ("unknown" if not r["oa"] else "closed" if r["oa"] == "closed"
                                    else f"open, {sift_mod.OA_WORDS.get(r['oa'], r['oa'])}") + ".")
    lines.append(sift_words.t("sift_cli.facts_lines.country") + (sift_mod.and_join(r["countries"]) or "unknown") + ".")
    if works:
        named = {k["key"]: k["label"] for k in works}
        cites = "" if r["cites"] is None else sift_mod.and_join([named.get(k, k) for k in r["cites"]]) or "none"
        lines.append(sift_words.t("sift_cli.facts_lines.cites_key_works") + (f"{cites}." if cites else sift_mod.CITES_UNCHECKED))
    lines.append(sift_words.t("sift_cli.facts_lines.study", study=r['study']) + (sift_words.t("sift_cli.facts_lines.with", list=', '.join(r['study_with'])) if r["study_with"] else "") + "."
                 if r["study"] else sift_words.t("sift_cli.facts_lines.study_not_linked"))
    lines += [sift_words.t("sift_cli.facts_lines.same_study", list='. '.join(s['reasons'])) for s in r["suggest"]]
    return lines


def form_lines(name: str, got: dict) -> list[str]:
    """Extract and appraise in plain lines, for `sift form`: the form's fields, each its key, type, where
    it shows, whether it offers Not reported, what it is shown for and the Sift column it starts from,
    under its section, then each record included at full text, done or not, and the benchmark papers."""
    fields = got["fields"]
    lines = [sift_words.t("sift_cli.form_lines.of_of_included_at_full_text", stage=got['stage'], name=name, fields=sift_words.t("sift_cli.n.field", n=len(fields)), done=got['done'], records=sift_words.t("sift_cli.n.record", n=len(got['records'])))]
    names = {c["key"]: c["name"] for c in fields}
    section = None
    for c in fields:
        if c["section"] != section:
            section = c["section"]
            lines.append(f"{section}:" if section else sift_words.t("sift_cli.form_lines.in_no_section"))
        said = [c["type"], {"form": "on the form", "both": "on the form and the table", "table": "on the table"}[c["where"]]]
        if c["options"]:
            said.append("choices " + ", ".join(c["options"]))
        if c["not_reported"]:
            said.append(sift_words.t("sift_cli.form_lines.not_reported_offered"))
        if c["when"]:
            said.append(sift_words.t("sift_cli.form_lines.shown_when_is", get=names.get(c['when']['key'], c['when']['key']), list=' or '.join(c['when']['values'])))
        if c["from"]:
            said.append(sift_words.t("sift_cli.form_lines.starts_from", from_=c['from']))
        lines.append(f"  {c['plain_key']}: {c['name']} ({', '.join(said)})")
    lines += [f"{r['rec_id']}  {'done' if r['done'] else sift_words.t('sift_cli.said.not_done')}  {r['title']}" for r in got["records"]]
    if got["bench"]:
        lines.append(sift_words.t("sift_cli.form_lines.benchmark_papers", list=', '.join(got['bench'])))
    return lines


def form_said(r: dict) -> list[str]:
    """Whether a record's form is done, for `sift show`, once the form has a field shown on it."""
    f = r.get("form") or {}
    return [sift_words.t("sift_cli.form_said.form", v_='done' if f.get('done') else sift_words.t("sift_cli.said.not_done"))] if f.get("shown") else []


def terms_lines(r: dict, blocks: list) -> list[str]:
    """The terms of each block of the plan a record holds, for `sift show`, with where they were found,
    and for a block it holds none of, the record's sentence that says how a database found it, as the
    screen's view words it (14 October, later)."""
    held = r.get("terms") or {}
    matched = r.get("matched") or {}
    out = []
    for b in blocks:
        got = held.get(b["key"]) or []
        m = matched.get(b["key"]) or {}
        if got:
            where = f" {sift_mod.MATCHED_IN} {', '.join(m['in'])}." if m.get("in") else ""
            out.append(f"{b['label']}: {', '.join(got)}.{where}")
        else:
            out.append(f"{b['label']}: {m.get('said') or sift_mod.MATCH_NONE}")
    return out


def fields_said(f: dict, found: list) -> str:
    """His rating and the participants on a record's line, and how many searches found it when more
    than one did."""
    out = ""
    if len(found) > 1:
        out += sift_words.t("sift_cli.fields_said.found_by", n_found=len(found))
    if f.get("rating"):
        out += sift_words.t("sift_cli.fields_said.rated", rating=f['rating'])
    if f.get("confirmed") and f.get("participants"):
        out += sift_words.t("sift_cli.fields_said.participants_2", participants=f['participants'])
    elif f.get("guess"):
        out += sift_words.t("sift_cli.fields_said.participants", guess=f['guess'])
    return out


def line_said(e: dict) -> str:
    """A line of the log in a few words: a decision, note or undo at its stage, a change to one of his
    fields, the old value and the new, either carried from the earlier run a run follows, or a link or
    an unlink of a study."""
    if e.get("act") == "study":
        if e.get("change") == "unlink":
            return sift_words.t("sift_cli.line_said.taken_out_of", get=e.get('rec_id'), get2=e.get('study'))
        return sift_words.t("sift_cli.line_said.and_linked_as_one_study", get=e.get('rec_id'), get2=e.get('with'), get3=e.get('study'))
    if sift_mod.excerpt_line(e):
        return excerpt_said(e)
    if e.get("act") == "carry":
        when = search_mod.run_said((e.get("from") or {}).get("run"))
        if e.get("field") == sift_mod.EXCERPTS_COLUMN:
            return sift_words.t("sift_cli.line_said.carried_from_the_run_of_2", excerpts=sift_words.t("sift_cli.n.key_excerpt", n=len(sift_mod.excerpts_of(e.get('value')))), when=when)
        if e.get("field"):
            return sift_words.t("sift_cli.line_said.carried_from_the_run_of", get=e.get('field'), list=' '.join(str(e.get('value') or '').split())[:60], when=when)
        return sift_words.t("sift_cli.line_said.at_carried_from_the_run_of", decision=decision_said(e.get('stage'), e.get('decision'), e.get('reason')), get=e.get('stage'), when=when)
    if e.get("act") == "field":
        new, old = " ".join(str(e.get("value") or "").split()), " ".join(str(e.get("was") or "").split())
        cut = lambda t: t if len(t) <= 60 else t[:57] + "..."
        return f"{e.get('field')} {cut(new) or 'cleared'}" + (sift_words.t("sift_cli.line_said.was", cut=cut(old)) if old else "")
    return f"{e.get('act')} {decision_said(e.get('stage'), e.get('decision'), e.get('reason'))} at {e.get('stage')}"


def excerpt_said(e: dict) -> str:
    """A key excerpt's line of the log in a few words: kept or removed, or the undo of either, with the stage
    it was made at and its words, cut short past 60 characters."""
    item = e.get("excerpt") if isinstance(e.get("excerpt"), dict) else {}
    words = " ".join(str(item.get("text") or "").split())
    words = words if len(words) <= 60 else words[:57] + "..."
    where = sift_mod.STAGE_WORDS.get(item.get("stage"), "")
    done = "kept" if e.get("change") == "add" else "removed"
    head = sift_words.t("sift_cli.excerpt_said.undo_of_a_key_excerpt", done=done) if e.get("act") == "undo" else sift_words.t("sift_cli.excerpt_said.key_excerpt", done=done)
    return f"{head}{' at ' + where if where else ''}, \"{words}\""


def excerpts_said(r: dict) -> list:
    """His key excerpts on a record, for `sift show`, one a line in the order he made them, each with the
    stage it was made at."""
    return [sift_words.t("sift_cli.excerpts_said.key_excerpt_at", stage_words=sift_mod.STAGE_WORDS[x['stage']], text=x['text']) for x in r.get("excerpts") or []]


def records_from(spec) -> list:
    """The records or proposals of `--from`, a list, or a record holding one under `records` or `proposals`."""
    if isinstance(spec, dict):
        spec = spec.get("records", spec.get("proposals"))
    if not isinstance(spec, list):
        raise cli.Refused(sift_words.t("sift_cli.records_from.the_input_is_a_list_of"))
    return spec


def cmd_sift(args) -> tuple:
    """`sift <folder> <act>`: a screening for a systematic review by its folder. `counts`, the counts
    the screen shows, `export`, those counts written as `screening.counts.csv` beside its CSV,
    `prisma`, the PRISMA flow as Mermaid, `list`, a round's records, `show`, one record with every
    line of the log on it, and for the review's side `add`, records added at the foot, and
    `propose`, its proposals for named records at a stage. `list` and `show` give his own fields, the
    rating, the participants, the notes, the digest, the critique and his columns, to read, and `show`
    his key excerpts too. No act decides, notes or undoes a record or writes a field, a column or a key
    excerpt of his, which are his alone in Sift. `reset`, his own to run and only with `--yes`, starts the screening again as Start again
    on its screen does, its log kept in `_Archive/`. A screening holds published records and no
    participant's words, so it needs no project and no tick."""
    if args.act in SEARCH_ACTS or getattr(args, "search", False):
        return cmd_sift_search(args)
    if args.act in ZOTERO_ACTS:
        return cmd_sift_zotero(args)
    folder = Path(args.folder).expanduser()
    if not sift_mod.is_screening(folder):
        raise cli.Refused(sift_words.t("sift_cli.said.that_folder_holds_no", csv_name=sift_mod.CSV_NAME))
    name = folder.resolve().name
    act = args.act
    stage = getattr(args, "stage", None) or "ta"
    if act == "counts":
        c = sift_mod.counts(sift_mod.load(folder))
        return {"folder": name, "counts": c, "rows": sift_mod.count_rows(c)}, sift_lines(name, c)
    if act == "prisma":
        source = sift_mod.prisma_source(sift_mod.counts(sift_mod.load(folder)))
        return {"folder": name, "prisma": source, "file": sift_mod.PRISMA_NAME}, source.rstrip("\n").splitlines()
    if act == "list":
        got = sift_mod.rows_of_round(folder, stage, getattr(args, "round", None) or "undecided")
        lines = [sift_words.t("sift_cli.sift.screening", name=name, stage=got['stage'], round=round_words(stage, got['round']), records=sift_words.t("sift_cli.n.record", n=len(got['records'])))]
        lines += [f"{r['rec_id']}  {decision_said(stage, r['decision'], r['reason'])}  "
                  f"{r['title']}{' (' + r['year'] + ')' if r['year'] else ''}, {proposal_said(r['proposal'], stage)}"
                  f"{sift_words.t('sift_cli.sift.pdf') if r['pdf'] else ''}{fields_said(r['fields'], r['found'])}{own_said(r)}" for r in got["records"]]
        return dict(got, folder=name), lines
    if act == "form":
        got = sift_mod.form_read(folder)
        return dict(got, folder=name), form_lines(name, got)
    if act == "show":
        rec = getattr(args, "rec_id", None)
        if not rec:
            raise cli.Refused(sift_words.t("sift_cli.sift.name_the_record_sift_folder_show"))
        got = sift_mod.history(folder, rec)
        r = got["record"]
        lines = [f"{r['rec_id']}: {r['title']}", ", ".join(x for x in (r["authors"], r["year"], r["journal"], r["doi"]) if x)]
        for key in sift_mod.STAGES:
            st = r["stages"][key]
            if not st["in"]:
                continue
            props = "; ".join(proposal_said(p, key) for p in st["proposals"]) or sift_words.t("sift_cli.said.no_proposal")
            lines.append(f"{sift_mod.STAGE_WORDS[key].capitalize()}: {decision_said(key, st['decision'], st['reason'])}, "
                         f"{props}.{sift_words.t('sift_cli.sift.note') + st['note'] if st['note'] else ''}")
        lines += excerpts_said(r)
        f = r["fields"]
        lines.append(f"{'Databases' if len(r['found']) > 1 else 'Database'}: {', '.join(r['found']) or sift_words.t('sift_cli.sift.none_named')}.")
        lines.append(sift_words.t("sift_cli.sift.participants") + (f"{f['participants'] or 'none'}" if f["confirmed"]
                                         else sift_words.t("sift_cli.sift.a_guess", guess=f['guess']) if f["guess"] else "none") + ".")
        lines.append(sift_words.t("sift_cli.sift.my_rating_of", rating=f['rating'], rating_max=sift_mod.RATING_MAX) if f["rating"] else sift_words.t("sift_cli.sift.my_rating_not_rated"))
        for key, label in (("notes", "Notes"), ("digest", "Digest"), ("critique", "Critique")):
            if f[key]:
                lines.append(f"{label}: {' '.join(f[key].split())}")
        for c in got["columns"]:
            mine = (f["own"].get(c["key"]) or "").strip()
            if mine:
                lines.append(f"{c['name']}: {' '.join(sift_mod.form_cell(c, f['own'][c['key']]).split())}")
            elif c["key"] in r["form"]["sift"]:
                lines.append(sift_words.t("sift_cli.sift.from_sift", name=c['name'], sift=r['form']['sift'][c['key']]))
        lines += form_said(r)
        lines += terms_lines(r, got.get("blocks") or [])
        lines += facts_lines(r, got.get("key_works") or [])
        lines.append(sift_words.t("sift_cli.sift.pdf_in_the_log", v_='yes' if r['pdf'] else 'none', lines=sift_words.t("sift_cli.n.line", n=len(got['history']))))
        # a decision's line says whether it matched the suggestions shown with it, never which control made it
        lines += [f"  {e.get('n')}. {cli.when_said(e.get('at'))}, {line_said(e)}, {e.get('tool') or ''}".rstrip(", ")
                  + (f". {sift_mod.suggestion_words(e)}." if sift_mod.suggestion_words(e) else "")
                  for e in got["history"]]
        return dict(got, folder=name), lines
    if act == "add":
        if not getattr(args, "source", None):
            raise cli.Refused(sift_words.t("sift_cli.sift.give_the_records_with_from_a"))
        done = sift_mod.add_records(folder, records_from(cli.read_spec(args.source)), dry_run=args.dry_run)
        verb = sift_words.t("sift_cli.sift.it_would_add") if args.dry_run else "Added"
        return dict(done, folder=name), [sift_words.t("sift_cli.sift.at_the_foot_of", verb=verb, records=sift_words.t("sift_cli.n.record", n=len(done['added'])), csv_name=sift_mod.CSV_NAME, list=', '.join(done['added']))]
    if act == "propose":
        if not getattr(args, "source", None):
            raise cli.Refused(sift_words.t("sift_cli.sift.give_the_proposals_with_from_a"))
        done = sift_mod.propose_review(folder, stage, records_from(cli.read_spec(args.source)), dry_run=args.dry_run)
        verb = sift_words.t("sift_cli.sift.it_would_write") if args.dry_run else "Wrote"
        lines = [sift_words.t("sift_cli.sift.the_proposals_at_of_into", verb=verb, stage=done['stage'], records=sift_words.t("sift_cli.n.record", n=len(done['written'])), list=', '.join(done['columns']), list2=', '.join(done['written']))]
        if done["not_found"]:
            lines.append(sift_words.t("sift_cli.sift.the_abstract_does_not_hold_the", list=', '.join(done['not_found'])))
        return dict(done, folder=name), lines
    if act == "reset":
        if not args.dry_run and not getattr(args, "yes", False):
            raise cli.Refused(_w("NO_YES"))
        done = sift_mod.reset(folder, dry_run=args.dry_run)
        cleared = sift_words.t("sift_cli.sift.and_with_his_fields", decisions=sift_words.t("sift_cli.n.decision", n=done['decisions']), notes=sift_words.t("sift_cli.n.note", n=done['notes']))
        if args.dry_run:
            return dict(done, folder=name), [sift_words.t("sift_cli.sift.starting_again_would_clear_and_keep", name=name, cleared=cleared, archive_dir=sift_mod.ARCHIVE_DIR)]
        kept = sift_words.t("sift_cli.sift.its_log_kept_as", archive=done['archive']) if done["archive"] else ""
        return ({k: v for k, v in done.items() if k != "counts"} | {"folder": name},
                [sift_words.t("sift_cli.sift.started_again_cleared", name=name, cleared=cleared, kept=kept)])
    done = sift_mod.export(folder, dry_run=args.dry_run)
    said = (sift_words.t("sift_cli.sift.it_would_write_beside", counts_name=sift_mod.COUNTS_NAME, csv_name=sift_mod.CSV_NAME, rows=sift_words.t("sift_cli.n.row", n=len(done['rows'])))
            if args.dry_run else sift_words.t("sift_cli.sift.wrote_beside", counts_name=sift_mod.COUNTS_NAME, csv_name=sift_mod.CSV_NAME, rows=sift_words.t("sift_cli.n.row", n=len(done['rows']))))
    return ({"folder": folder.resolve().name, "counts": done["counts"], "rows": done["rows"], "file": done["file"],
             "written": done["written"]}, [said] + sift_lines(folder.resolve().name, done["counts"]))


# ------------------------------------------------------------- sift searches

SEARCH_ACTS = ("plan", "strings", "register", "run", "runs", "databases")


def version_said(v: dict | None) -> str:
    if not v:
        return sift_words.t("sift_cli.version_said.no_version_yet")
    if v.get("registered"):
        return sift_words.t("sift_cli.version_said.version_registered", version=v['version'], day=search_mod.day_said(v['registered']))
    return sift_words.t("sift_cli.version_said.version_a_draft", version=v['version'])


def plan_lines(name: str, st: dict) -> list[str]:
    """A search plan in plain lines: its newest version, the databases, each block, the limits, the
    benchmark, every version and what stands in the way of registering or running it."""
    plan = st["plan"]
    lines = [sift_words.t("sift_cli.plan_lines.search_plan_in", name=name, version=version_said(st['current']))]
    if st["current"].get("reason"):
        lines.append(sift_words.t("sift_cli.plan_lines.reason_for_its_changes", reason=st['current']['reason']))
    lines.append(sift_words.t("sift_cli.plan_lines.databases") + (", ".join(search_mod.name_of(s, plan) for s in plan["databases"]) or "none") + ".")
    for i, b in enumerate(plan["blocks"]):
        own = "".join(sift_words.t("sift_cli.plan_lines.in", scope_words=search_mod.SCOPE_WORDS[sc], name=search_mod.name_of(s, plan)) for s, sc in b["scopes"].items())
        lines.append(sift_words.t("sift_cli.plan_lines.block_in", v_=i + 1, block_name=search_mod.block_name(plan, i), scope_words=search_mod.SCOPE_WORDS[b['scope']], own=own, list=', '.join(b['terms']) or sift_words.t("sift_cli.plan_lines.no_terms")))
    limits = [w for w in (search_mod.years_words(plan), search_mod.types_words(plan["types"])) if w]
    lines.append(sift_words.t("sift_cli.plan_lines.limits") + (", ".join(limits) if limits else "none") + sift_words.t("sift_cli.plan_lines.no_language_limit"))
    if plan["benchmark"]:
        lines.append(sift_words.t("sift_cli.plan_lines.benchmark", list=', '.join(plan['benchmark'])))
    if st.get("key_works"):
        lines.append(sift_words.t("sift_cli.plan_lines.key_works") + sift_mod.and_join([sift_mod.key_work_label(k) + (f" {k['doi']}" if k["doi"] else "")
                                                        for k in st["key_works"]]) + ".")
    lines += [f"  {version_said(v).capitalize()}" + (f": {v['reason']}" if v.get("reason") else ".") for v in st["versions"]]
    lines += st["problems"]
    return lines


def cmd_sift_search(args) -> tuple:
    """`sift search <act> <folder>`: a review's searches by its folder, the one that holds runs/.
    `plan`, the plan's newest version with every version's head, `strings`, each database's string,
    `--version` an earlier one's, `register`, the newest version frozen and `search_plan.md` written,
    which is his to run and never an agent's, `run`, a run of the newest registered version, `--draft`
    the newest draft, into a new run folder, `runs/<day>/` or a later run that day `runs/<day>-2/` and
    up, by API where his own list of databases holds it by API and its key is set and an export
    already in the folder for the rest, carrying the screening of the newest earlier run with
    decisions, or of the run `--follows` names by its folder's name, or of none with `--follows none`,
    and `runs`, each run named in words with its folder, its counts and the benchmark it missed. `databases`, with no folder, is his own list of databases from the settings,
    each with how it is searched and whether each key is saved, never the key, and nothing here saves,
    removes or shows a key. A review holds published records and no participant's words, so it needs
    no project and no tick. Since 14 October `strings` says the rewrites Sift made for each database, and
    `run` checks truncation first, each truncated term counted alone with and without its asterisk in the
    databases it searches by API that take truncation, the dry run saying the table and its flags and a run
    keeping it in its folder as `dry_run_terms.csv`."""
    act = args.act
    if getattr(args, "search", False):
        given = args.folder
    elif args.folder != "search":
        raise cli.Refused(sift_words.t("sift_cli.sift_search.is_an_act_of_sift_search", act=act)
                      + (" <folder>." if act != "databases" else "."))
    else:
        given = getattr(args, "rec_id", None)
    if act == "databases":
        rows = search_mod.database_rows(search_mod.databases(srv.config()))
        return {"databases": rows}, search_mod.database_lines(rows)
    if not given:
        raise cli.Refused(sift_words.t("sift_cli.sift_search.name_the_review_folder_sift_search", act=act))
    folder = Path(given).expanduser()
    if not folder.is_dir():
        raise cli.Refused(sift_words.t("sift_cli.sift_search.that_folder_is_not_there"))
    name = folder.resolve().name
    if act == "runs":
        found = search_mod.runs(folder)
        lines = [sift_words.t("sift_cli.sift_search.runs_in", name=name, n_found=len(found))] + [line for r in found for line in search_mod.run_lines(r)]
        return {"folder": name, "runs": found}, lines
    st = search_mod.state(folder)
    if st["current"] is None:
        raise cli.Refused(sift_words.t("sift_cli.sift_search.there_is_no_search_plan_in"))
    if act == "plan":
        return ({"folder": name, "current": st["current"], "versions": st["versions"], "plan": st["plan"],
                 "registered": st["registered"], "problems": st["problems"]}, plan_lines(name, st))
    if act == "strings":
        data = search_mod.read_file(folder)
        n = getattr(args, "version", None)
        v = search_mod.version_of(data, int(n)) if n else search_mod.newest(data)
        if v is None:
            raise cli.Refused(sift_words.t("sift_cli.sift_search.there_is_no_version", n=n))
        found = search_mod.strings(search_mod.clean_plan(v["plan"]))
        lines = [sift_words.t("sift_cli.sift_search.the_strings_of_in", version=version_said(v), name=name)]
        for s in found:
            lines += [f"{s['name']}:", f"  {s['query']}"]
            if s["override"]:
                lines.append(sift_words.t("sift_cli.sift_search.edited_manually", reason=s['override']['reason']))
            # the rewrites Sift made for the database, one to a line (14 October)
            elif s["rewrites"]:
                lines += [sift_words.t("sift_cli.sift_search.rewrites")] + [f"    {w}" for w in s["rewrites"]]
            lines += [f"  {n}" for n in s["notes"]] + ([f"  {s['limits']}"] if s["limits"] else [])
        return {"folder": name, "version": v["version"], "registered": v.get("registered"), "strings": found}, lines
    if act == "register":
        done = search_mod.register(folder, getattr(args, "reason", None), dry_run=args.dry_run)
        verb = sift_words.t("sift_cli.sift_search.it_would_register") if args.dry_run else "Registered"
        said = sift_words.t("sift_cli.sift_search.version_of_the_search_plan_in", verb=verb, registered=done['registered'], name=name)
        said += "." if args.dry_run else sift_words.t("sift_cli.sift_search.and_wrote_beside_it", plan_md=search_mod.PLAN_MD)
        return dict(done, folder=name), [said, ""] + done["markdown"].rstrip("\n").splitlines()
    which = "draft" if getattr(args, "draft", False) else None
    day = getattr(args, "date", None) or search_mod.today().isoformat()
    # the run it follows, the newest earlier run with decisions unless --follows names one or none
    follows = getattr(args, "follows", None)
    follows = search_mod.default_follows(folder, day) if follows is None else follows
    # the truncation check first, in the dry run's answer, and before a run's searches, its table kept in the
    # run folder (14 October)
    done = search_mod.run(folder, which=which, day=day, dry_run=args.dry_run,
                          listed=search_mod.databases(srv.config()), follows=follows, check_terms=True)
    if args.dry_run:
        lines = [sift_words.t("sift_cli.sift_search.it_would_run_version_into", version=done['version'], v_=sift_words.t("sift_cli.sift_search.a_draft") if done['draft'] else '', runs_dir=search_mod.RUNS_DIR, date=done['date'])]
        for s in done["sources"]:
            how = sift_words.t("sift_cli.sift_search.by_api") if s["how"] == "api" else (sift_words.t("sift_cli.sift_search.from_the_export_in_the_folder") if s["export"] else sift_words.t("sift_cli.sift_search.by_export_none_dropped_yet"))
            lines.append(f"  {s['name']}: {how}.")
        f = done.get("follows")
        lines.append(sift_words.t("sift_cli.sift_search.it_follows_the_run_of_carrying", run=search_mod.run_said(f['date']), records=sift_words.t("sift_cli.n.record", n=f['records']), decided=f['decided']) if f else sift_words.t("sift_cli.sift_search.it_follows_no_earlier_run"))
        return dict(done, folder=name), lines + search_mod.terms_lines(done.get("terms"))
    return dict(done, folder=name), search_mod.run_lines(done)


# ------------------------------------------------------------- sift zotero

ZOTERO_ACTS = ("sync",)


def cmd_sift_zotero(args) -> tuple:
    """`sift zotero sync <folder>`: a screening's records put in his Zotero library, in a collection
    named for its Sift project, each with its PDF, as Sync to Zotero on its screen does (see
    `sift_zotero.py`). Every record included at full text, or with `--all` every record. `--dry-run`
    says what it would add, update and leave and the PDFs it would upload, writing nothing. It reads
    the library from the settings, `--config` when it is given, and the key from the keychain, and
    never prints, saves or removes a key. A sync is his to run, the dry run anyone's."""
    if args.folder != "zotero":
        raise cli.Refused(sift_words.t("sift_cli.sift_zotero.is_an_act_of_sift_zotero", act=args.act))
    given = getattr(args, "rec_id", None)
    if not given:
        raise cli.Refused(sift_words.t("sift_cli.sift_zotero.name_the_screenings_folder_sift_zotero", act=args.act))
    folder = Path(given).expanduser()
    if not sift_mod.is_screening(folder):
        raise cli.Refused(sift_words.t("sift_cli.said.that_folder_holds_no", csv_name=sift_mod.CSV_NAME))
    which = "all" if getattr(args, "all", False) else "included"
    done = zotero_mod.sync(folder, srv.config(), which, dry_run=args.dry_run)
    name = folder.resolve().name
    if args.dry_run:
        return dict(done, folder=name, which=which), [done["said"]]
    return dict({k: v for k, v in done.items() if k != "refused"}, folder=name, which=which), [done["said"]]


def add_sift_arguments(x) -> None:
    """The `sift` command's arguments, at the top of the `sift` command, and under `idiograph sift` until the cutover."""
    x.add_argument("folder", help="the folder that holds screening.csv, or search, or zotero")
    x.add_argument("act", choices=SIFT_ACTS + SEARCH_ACTS + ZOTERO_ACTS)
    x.add_argument("rec_id", nargs="?", help="the record, for show, or after search the review folder, or after "
                                             "zotero the screening's folder")
    x.add_argument("--reason", default=None, help="the reason for a new version's changes, for search register")
    x.add_argument("--draft", action="store_true", help="run the newest draft, for search run")
    x.add_argument("--date", default=None, help="the run's day, YYYY-MM-DD, today by default, a later run that day "
                                                "taking the folder <day>-2 and up, for search run")
    x.add_argument("--follows", default=None, help="the earlier run whose screening search run carries, by its folder's "
                                                   "name as runs gives it, 2026-10-01 or 2026-10-01-2, or none, the "
                                                   "newest earlier run with decisions by default")
    x.add_argument("--version", type=int, default=None, help="the version whose strings to give, for search strings")
    x.add_argument("--stage", default=None, help="ta, title and abstract, the default, or ft, full text")
    x.add_argument("--round", default=None, help="to-screen, the default, maybe, yes or include, no or exclude, all, differs or apart "
                   "(where you and the second screener differ), for list, the older undecided, accepted and rejected "
                   "still taken")
    x.add_argument("--from", dest="source", default=None, help="a JSON file of the records to add or the proposals to write")
    x.add_argument("--json", action="store_true", default=argparse.SUPPRESS, help="exact output, as JSON")
    x.add_argument("--config", default=argparse.SUPPRESS, help="a settings file in place of config.json, for search "
                                                                 "databases and search run")
    x.add_argument("--dry-run", action="store_true", help="say what export, add, propose, reset or zotero sync would write "
                                                          "and write nothing")
    x.add_argument("--yes", action="store_true", help="go ahead with reset, which clears every decision, note and field")
    x.add_argument("--all", action="store_true", help="every record, for zotero sync, not only those included at full text")


def run(args) -> tuple:
    """The `sift` command on its parsed arguments (see `cmd_sift`). A screening or a review needs no project,
    and reads the settings only for his list of databases and his Zotero library, from `--config` when it is
    given, the server's settings file put back after it however it ends."""
    kept = srv.CONFIG_PATH
    try:
        if getattr(args, "config", None):
            srv.CONFIG_PATH = Path(args.config).expanduser().resolve()
        return cmd_sift(args)
    finally:
        srv.CONFIG_PATH = kept


# ------------------------------------------------------------------ search

SEARCH_REFUSED = ("Sift's Search reads one project by its folder: sift search <words> --folder <folder>. "
                  f"A review's searches are sift search {', '.join(SEARCH_ACTS[:-1])} or {SEARCH_ACTS[-1]} "
                  "<review folder>.")


def search_folder(folder: Path) -> Path:
    """A Sift project for Search by its folder: a screening's, the one holding screening.csv, or a review's
    own, the one holding its plan, refused with WorkbookError when it is neither, so the next app's Search
    is asked."""
    if sift_mod.is_screening(folder) or search_mod.plan_path(folder).is_file():
        return folder
    raise WorkbookError(sift_words.t("sift_cli.search_folder.that_folder_holds_no_screening_or"))


def search_found(words: list[str], folder: Path, _folder_id: str = "") -> list[dict]:
    """Sift's Search over a project by its folder: a screening's records and the plan above it, or a review's
    own plan and the screening its Screening step opens (see `sift_find.sift_found`)."""
    if sift_mod.is_screening(folder):
        review = sift_mod.review_of(folder)
        review = review if review is not None and search_mod.plan_path(review).is_file() else None
        return sift_find.sift_found(words, folder, str(folder), review, str(review) if review else "")
    try:
        screening = routes.screening_of(folder, routes.kept_review(folder))
    except (OSError, ValueError, WorkbookError):
        screening = None
    return sift_find.sift_found(words, screening, str(screening) if screening else "", folder, str(folder))


def search_hit(hit: dict, go: dict) -> None:
    """A Search hit landing on Sift's screen, a record with its stage and sift_show, which reads it whole,
    or on Search strategy, its plan, which sift_search_plan reads."""
    if go.get("screen") == "sift":
        hit.update(rec_id=go.get("rec", ""), stage=go.get("stage", ""))
        hit["open"] = cli.opener("sift_show", {"folder": go.get("folder", ""), "rec_id": go.get("rec", "")},
                                 ["sift", go.get("folder", ""), "show", go.get("rec", "")])
    else:
        hit["open"] = cli.opener("sift_search_plan", {"folder": go.get("folder", "")},
                                 ["sift", "search", "plan", go.get("folder", "")])


def log_name(folder: Path) -> str:
    """A Sift project's name in the agent log (siftlog, 3 November 2026): its review's folder's, the one over runs/,
    for a run's screening, else the folder's own."""
    return (sift_mod.review_of(folder) or Path(folder)).resolve().name


# The keys whose strings Sift's answers keep plain for an agent (Adam, 2 November 2026, by dialog: mark Sift's
# text too), every other string marked as {"untrusted_text": ...} by `cli.mark`, since a record's title,
# abstract, keywords and every column a database or a CSV gave it are words anyone can publish. Only what Sift
# makes or checks is named here: ids, a decision and its stage, kinds, dates and the files and folders it names.
# A reason, a model or a proposal's maker comes from the CSV and is marked, and `more` is a record's other
# columns here, never a cursor as in Idiograph's.
SIFT_PLAIN = (
    # ids and keys Sift makes, and a plan's version
    "rec_id", "id", "key", "keys", "plain_key", "n", "version", "plan_version",
    # what an agent hands back as an input: a folder, a stage, a round, which records a sync takes
    "folder", "stage", "round", "which",
    # a decision and Sift's own kinds and words for where things are
    "decision", "kind", "kind_name", "type", "how", "service", "source", "act", "change", "field", "in",
    "matched_suggestion", "suggestion_source",
    # the PRISMA flow's phases, each done, now or to come
    "identification", "screening", "retrieval", "eligibility", "included",
    # dates and times
    "at", "saved", "registered", "date", "day", "added", "cited_date", "openalex_date", "crossref_date",
    # the records and columns an act names by their ids, and the files it writes
    "written", "not_found", "bench", "columns", "shown", "file", "files", "archive",
    # the client that acted, the command that opens a hit, and the search an agent sent, said back
    "tool", "command", "q", "scope", "kinds",
)

cli.register("sift", run, add_sift_arguments, SIFT_ABOUT, folder=search_folder, found=search_found,
             screen=("sift", "searches"), hit=search_hit, search_refused=SEARCH_REFUSED, search_acts=SEARCH_ACTS,
             plain=SIFT_PLAIN, words=(*SIFT_ACTS, *SEARCH_ACTS, *ZOTERO_ACTS, "search", "zotero"), named=log_name)
