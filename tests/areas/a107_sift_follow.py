from __future__ import annotations

import csv
import inspect
import json
import os
import shutil

from . import support
from .support import check, follow_stub, refusal_of, skip, urllib_path


@support.as_app("sift")
def test_sift_follow(scratch):
    print("\n107. Sift's searches settled against each database's own help, the open-ended year put in at the run, "
          "and a later run carrying an earlier screening's decisions, by PRISMA 2020 and PRISMA-S")
    import datetime as dt
    import http.server
    import subprocess
    import threading
    import cli
    import mcp_server
    import sift_mcp
    import server as server_mod
    import sift_routes
    import sift
    import sift_search as ss

    sjs = support.text("apps/sift/static/sift_search.js")
    sfjs = support.text("apps/sift/static/sift.js")
    base = scratch / "sift-follow"
    shutil.rmtree(base, ignore_errors=True)
    base.mkdir(parents=True)
    kept_clock, kept_env, kept_runner = ss.CLOCK, os.environ.pop(ss.STUB_ENV, None), ss.RUNNER
    ss.CLOCK = lambda: dt.date(2031, 3, 4)
    # no key in the keychain, so the run never asks the real `security` tool
    ss.RUNNER = lambda argv, **_: ss.Done(44, "\n")
    state = {"phase": 1}
    httpd = http.server.ThreadingHTTPServer(("127.0.0.1", 0), follow_stub(state))
    threading.Thread(target=httpd.serve_forever, kwargs={"poll_interval": 0.05}, daemon=True).start()
    stub = f"http://127.0.0.1:{httpd.server_address[1]}"
    ctx = lambda: ss.Context(base={s: stub + urllib_path(u) for s, u in ss.ENDPOINTS.items()}, pause=lambda s: None)
    # a run the command line makes waits for nothing between pages or before a retry, since every request goes
    # to the stub on loopback
    real_init = ss.Context.__init__
    ss.Context.__init__ = lambda self, base=None, pause=None, page=None, email="": real_init(
        self, base, pause if pause is not None else (lambda seconds: None), page, email)
    try:
        # ── A. every writer and every platform against strings written by hand, the clock at 4 March 2031
        blocks = [{"name": "Hives", "terms": ["beekeep*", '"urban apiary"']}, {"name": "Calm", "terms": ["wellbeing"]}]
        on = lambda p, years: {s["source"]: s for s in ss.strings(ss.clean_plan({
            "databases": list(ss.SOURCES), "other_name": "Hive Index", "platforms": {"psycinfo": p, "cinahl": p},
            "blocks": blocks, "years": years}))}
        ebsco, ovid, proquest = (on(p, {"from": 2005}) for p in ("ebsco", "ovid", "proquest"))
        want = {
            "scopus": 'TITLE-ABS-KEY(beekeep* OR "urban apiary") AND TITLE-ABS-KEY(wellbeing) AND PUBYEAR > 2004',
            "wos": 'TS=(beekeep* OR "urban apiary") AND TS=(wellbeing) AND PY=(2005-2031)',
            "pubmed": '(beekeep*[tiab] OR "urban apiary"[tiab]) AND (wellbeing[tiab]) AND 2005:3000[dp]',
            "epmc": ('(TITLE_ABS:beekeep* OR KW:beekeep* OR TITLE_ABS:"urban apiary" OR KW:"urban apiary") AND '
                     '(TITLE_ABS:wellbeing OR KW:wellbeing) AND PUB_YEAR:[2005 TO 2031]'),
            "openalex": 'title_and_abstract.search:(beekeep OR "urban apiary") AND (wellbeing),publication_year:>2004',
            "embase": "(beekeep* OR 'urban apiary'):ti,ab,kw AND (wellbeing):ti,ab,kw",
            "pqdt": 'TITLE,ABSTRACT,IF(beekeep* OR "urban apiary") AND TITLE,ABSTRACT,IF(wellbeing)',
            "scholar": 'beekeep OR "urban apiary" wellbeing',
            "other": '(beekeep* OR "urban apiary") AND (wellbeing)',
        }
        for s, w in want.items():
            check(f"107: {ss.NAMES[s]}'s string from an invented plan, as its own help has it and as written by hand",
                  ebsco[s]["query"] == w, ebsco[s]["query"])
        by_hand = {
            ("psycinfo", "ebsco"): ('(TI (beekeep* OR "urban apiary") OR AB (beekeep* OR "urban apiary") OR KW (beekeep* OR '
                                    '"urban apiary")) AND (TI (wellbeing) OR AB (wellbeing) OR KW (wellbeing))'),
            ("psycinfo", "ovid"): '(beekeep* OR "urban apiary").ti,ab,id. AND (wellbeing).ti,ab,id.',
            ("psycinfo", "proquest"): 'TITLE,ABSTRACT,IF(beekeep* OR "urban apiary") AND TITLE,ABSTRACT,IF(wellbeing)',
            ("cinahl", "ebsco"): ('(TI (beekeep* OR "urban apiary") OR AB (beekeep* OR "urban apiary") OR SU (beekeep* OR '
                                  '"urban apiary")) AND (TI (wellbeing) OR AB (wellbeing) OR SU (wellbeing))'),
            ("cinahl", "ovid"): '(beekeep* OR "urban apiary").ti,ab. AND (wellbeing).ti,ab.',
            ("cinahl", "proquest"): 'TITLE,ABSTRACT(beekeep* OR "urban apiary") AND TITLE,ABSTRACT(wellbeing)',
        }
        plat = {"ebsco": ebsco, "ovid": ovid, "proquest": proquest}
        for (s, p), w in by_hand.items():
            check(f"107: {ss.NAMES[s]} on {ss.PLATFORM_NAMES[p]}, as written by hand", plat[p][s]["query"] == w, plat[p][s]["query"])
        run_note = "{} has no open end to a range of years, so the year of the run, 2031, ends it."
        check("107: Web of Science and Europe PMC document no open end, so a year from alone ends at the year of the run, "
              "said in a note, while Scopus, PubMed and OpenAlex keep their own open forms with none",
              run_note.format("Web of Science") in ebsco["wos"]["notes"] and run_note.format("Europe PMC") in ebsco["epmc"]["notes"]
              and not any("year of the run" in n for s in ("scopus", "pubmed", "openalex") for n in ebsco[s]["notes"]),
              str(ebsco["wos"]["notes"]))
        check("107: ProQuest's keywords field is IF, so no note says PsycInfo there or Dissertations & Theses lacks one, and "
              "a truncated term says ProQuest's asterisk stands for up to five characters",
              not any("no keywords field" in n for n in proquest["psycinfo"]["notes"] + ebsco["pqdt"]["notes"])
              and ss.PROQUEST_STAR in proquest["psycinfo"]["notes"] and ss.PROQUEST_STAR in ebsco["pqdt"]["notes"]
              and ss.PROQUEST_STAR == "ProQuest's asterisk stands for up to five characters.", str(ebsco["pqdt"]["notes"]))
        check("107: CINAHL is offered on EBSCO alone, so a plan naming it on Ovid or ProQuest still reads, its string written "
              "with a note that the vendor no longer offers it, and on EBSCO with none",
              ss.OFFERED == {"psycinfo": ("ebsco", "ovid", "proquest"), "cinahl": ("ebsco",)}
              and "Ovid no longer offers CINAHL, which EBSCO alone offers now." in ovid["cinahl"]["notes"]
              and "ProQuest no longer offers CINAHL, which EBSCO alone offers now." in proquest["cinahl"]["notes"]
              and not any("no longer offers" in n for n in ebsco["cinahl"]["notes"] + ovid["psycinfo"]["notes"])
              and ss.clean_plan({"databases": ["cinahl"], "platforms": {"cinahl": "ovid"}})["platforms"] == {"cinahl": "ovid"}
              and ss.clean_databases([{"source": "cinahl", "platform": "proquest"}]) == [
                  {"source": "cinahl", "platform": "proquest", "how": "export"}]
              and sift_routes.search_catalog()["offered"] == {"psycinfo": [["ebsco", "EBSCO"], ["ovid", "Ovid"], ["proquest", "ProQuest"]],
                                                            "cinahl": [["ebsco", "EBSCO"]]}, str(ovid["cinahl"]["notes"]))
        to = on("ebsco", {"to": 2015})
        both = on("ebsco", {"from": 2005, "to": 2020})
        check("107: a year to alone starts at each database's own low side, Web of Science at 1900, and both ends need no note",
              to["wos"]["query"].endswith("PY=(1900-2015)") and to["pubmed"]["query"].endswith("1000:2015[dp]")
              and to["epmc"]["query"].endswith("PUB_YEAR:[1000 TO 2015]") and to["scopus"]["query"].endswith("PUBYEAR < 2016")
              and to["openalex"]["query"].endswith(",publication_year:<2016") and both["wos"]["query"].endswith("PY=(2005-2020)")
              and both["epmc"]["query"].endswith("PUB_YEAR:[2005 TO 2020]")
              and not any("year of the run" in n for d in (to, both) for s in d.values() for n in s["notes"]), to["wos"]["query"])
        later = on("ebsco", {"from": 2040})
        ss.CLOCK = lambda: dt.date(2032, 1, 2)
        moved = on("ebsco", {"from": 2005})
        ss.CLOCK = lambda: dt.date(2031, 3, 4)
        check("107: the year put in is the clock's, so the plan screen shows this year's string, and a plan that starts "
              "after it ends at its start",
              moved["wos"]["query"].endswith("PY=(2005-2032)") and moved["epmc"]["query"].endswith("PUB_YEAR:[2005 TO 2032]")
              and later["wos"]["query"].endswith("PY=(2040-2040)") and ss.this_year() == 2031, moved["wos"]["query"])
        node = shutil.which("node")
        if node:
            script = base / "plat-node.js"
            body = lambda name: "function " + name + sjs.split("function " + name, 1)[1].split("\n}\n", 1)[0] + "\n}\n"
            script.write_text(body("sfsPlatforms") + body("sfsFollowChoices")
                              + "const cat = { platforms: [['ebsco', 'EBSCO'], ['ovid', 'Ovid'], ['proquest', 'ProQuest']],\n"
                              + "  offered: { cinahl: [['ebsco', 'EBSCO']] } };\n"
                              + "const runs = [{ date: '2026-10-09', screening: true, decided: 4 }, { date: '2026-10-08', screening: true, decided: 3 },\n"
                              + "  { date: '2026-10-05', screening: true, decided: 0 }, { date: '2026-10-03', screening: false, decided: 0 },\n"
                              + "  { date: '2026-10-01', screening: true, decided: 2 }];\n"
                              + "console.log(JSON.stringify([sfsPlatforms(cat, 'cinahl', 'ebsco'), sfsPlatforms(cat, 'cinahl', 'ovid'),\n"
                              + "  sfsPlatforms(cat, 'psycinfo', 'proquest').length, sfsFollowChoices(runs, '2026-10-09').map((r) => r.date)]));\n",
                              encoding="utf-8")
            ran = subprocess.run([node, str(script)], capture_output=True, text=True, encoding="utf-8", timeout=60)
            got = json.loads(ran.stdout or "null") if ran.returncode == 0 else None
            check("107: in node, CINAHL offers EBSCO alone, a plan's Ovid kept as no longer offered, and Follows offers the "
                  "earlier runs with decisions, newest first, a run of today among them since Run makes a new run (9 October)",
                  got == [[["ebsco", "EBSCO"]], [["ebsco", "EBSCO"], ["ovid", "Ovid, no longer offered"]], 3,
                          ["2026-10-09", "2026-10-08", "2026-10-01"]], (ran.stdout or ran.stderr)[:300])
        else:
            skip("107: the platforms and Follows in node", "no node on this machine")

        # ── B. an earlier run on 1 October, the year put in when the string is sent
        review = base / "bee-review"
        review.mkdir()
        (review / "reasons.csv").write_text("stage,code,meaning\nta,E1,Not about keeping bees\nft,F1,No interviews\n",
                                            encoding="utf-8")
        ss.save(review, {"databases": ["psycinfo", "epmc", "openalex"], "blocks": blocks, "years": {"from": 2005}})
        ss.register(review)
        d1, d2, d3 = "2026-10-01", "2026-10-08", "2026-10-15"
        ris = lambda *recs: "".join(f"TY  - JOUR\nTI  - {t}\nPY  - {y}\n" + (f"DO  - {d}\n" if d else "")
                                    + "AB  - An invented abstract on keepers.\nER  - \n\n" for t, y, d in recs).encode("utf-8")
        ss.take_export(review, "psycinfo", ris(("Honey and the city", "2018", ""), ("Hives on the roof", "2019", "10.5555/bee.1")),
                       "p.ris", day=d1, ctx=ctx())
        first = ss.run(review, day=d1, ctx=ctx())
        f1 = review / "runs" / d1
        with open(f1 / "log.csv", encoding="utf-8", newline="") as fh:
            sent_log = {r["source"]: r for r in csv.DictReader(fh)}
        sent = [q["query"] for p, q in state["asked"] if p.endswith("/search")]
        check("107: the run sends the year of the run and log.csv records exactly what was sent, the plan screen's string",
              sent == [want["epmc"]] and sent_log["Europe PMC"]["query"] == want["epmc"]
              and {s["source"]: s for s in ss.state(review)["strings"]}["epmc"]["query"] == want["epmc"]
              and first["follows"] is None, str(sent))
        sc1 = sift.load(f1)
        check("107: the earlier run's screening, five records R001 up in year and title order",
              [(r, sc1.cell(r, "title"), sc1.cell(r, "sources")) for r in sc1.ids] == [
                  ("R001", "Honey and the city", "PsycInfo"), ("R002", "Hives on the roof", "PsycInfo; Europe PMC"),
                  ("R003", "Smoke and patience", "Europe PMC; OpenAlex"), ("R004", "Swarm season notes", "Europe PMC"),
                  ("R005", "Queenless colonies and calm", "OpenAlex")], str(sc1.ids))
        sift.decide(f1, "R002", "ta", "include")
        sift.decide(f1, "R002", "ft", "include")
        sift.decide(f1, "R003", "ta", "exclude", "E1", note="Honey alone, no keeping.")
        sift.decide(f1, "R004", "ta", "maybe")
        sift.set_field(f1, "R001", "rating", 4)
        sift.set_field(f1, "R001", "notes", "An invented note on the roof.")
        sift.column(f1, "add", name="Setting", kind="choice", options=["Rooftop", "Allotment"])
        sift.set_field(f1, "R001", "col_setting", "Rooftop")
        sift.propose_review(f1, "ta", [{"rec_id": "R005", "decision": "include", "grounds": "keepers spoke of calm"}])
        sift.write_ai(f1, "R005", "ta", "maybe", grounds="calm at the hive")
        pdf = b"%PDF-1.4 an invented report on rooftop hives\n"
        sift.save_pdf(f1, "R002", pdf)
        earlier_n = {(e["rec_id"], e.get("stage") or e.get("field")): e["n"] for e in sift.read_lines(f1) if e.get("rec_id")}
        before = {p.relative_to(f1).as_posix(): p.read_bytes() for p in f1.rglob("*") if p.is_file()}
        check("107: the earlier run is offered to follow once it holds decisions, and is the default",
              ss.follow_choices(review, d2)[0]["date"] == d1 and ss.default_follows(review, d2) == d1
              and ss.runs(review)[0]["decided"] == 3 and ss.follow_choices(review, d1) == [])

        # ── C. a later run on 8 October following it
        state["phase"] = 2
        ss.take_export(review, "psycinfo", ris(("Honey and the city", "2018", ""), ("Calm keepers", "2024", "")), "p.ris", day=d2,
                       ctx=ctx())
        second = ss.run(review, day=d2, ctx=ctx(), follows=d1)
        f2 = review / "runs" / d2
        after = {p.relative_to(f1).as_posix(): p.read_bytes() for p in f1.rglob("*") if p.is_file()}
        check("107: the earlier run's folder is read and never written, every file byte for byte as it was and none added",
              after == before, str(sorted(set(after) ^ set(before))))
        sc2 = sift.load(f2)
        rows = {r: sc2.record(r) for r in sc2.ids}
        check("107: the later screening holds every earlier record by its rec_id, then the new ones numbered on from the "
              "highest, in year and title order",
              sc2.ids == ["R001", "R002", "R003", "R004", "R005", "R006", "R007"]
              and all(rows[r]["title"] == sc1.cell(r, "title") for r in sc1.ids)
              and rows["R006"]["title"] == "Bees on allotments" and rows["R007"]["title"] == "Calm keepers", str(sc2.ids))
        check("107: a record found again gains the later run's databases after its own, a field it lacked taken from the "
              "find, and one not found again is kept as it was",
              rows["R002"]["sources"] == "PsycInfo; Europe PMC; OpenAlex" and rows["R004"]["sources"] == "Europe PMC; OpenAlex"
              and rows["R004"]["doi"] == "10.5555/bee.7" and rows["R001"]["sources"] == "PsycInfo"
              and rows["R003"]["sources"] == "Europe PMC; OpenAlex" and rows["R005"]["sources"] == "OpenAlex"
              and rows["R003"]["doi"] == "10.5555/bee.2", str({r: rows[r]["sources"] for r in rows}))
        held = sift.states(sift.read_log(f2))
        st = lambda rec, stage: {k: sift.state_of(sc2, held, rec, stage)[k] for k in ("decision", "reason", "note")}
        check("107: the decisions arrive at both stages, the reasons and notes with them, and the CSV is written from the log",
              st("R002", "ta")["decision"] == "include" and st("R002", "ft")["decision"] == "include"
              and st("R003", "ta") == {"decision": "exclude", "reason": "E1", "note": "Honey alone, no keeping."}
              and st("R004", "ta")["decision"] == "maybe"
              and (rows["R002"]["decision"], rows["R002"]["ft_decision"], rows["R003"]["decision"], rows["R003"]["reason"],
                   rows["R004"]["decision"]) == ("include", "include", "exclude", "E1", "maybe"), str(rows["R003"]))
        check("107: the new records are undecided at both stages",
              all(not st(r, s)["decision"] and not rows[r]["decision"] and not rows[r]["ft_decision"]
                  for r in ("R006", "R007") for s in ("ta", "ft")))
        lines = sift.read_lines(f2)
        carries = {(e["rec_id"], e.get("stage") or e.get("field")): e for e in lines if e.get("act") == "carry"}
        check("107: the log opens with follow, naming the earlier run, the records carried, the new and those found again",
              lines[0]["act"] == "follow" and lines[0]["run"] == d1 and lines[0]["records"] == ["R001", "R002", "R003", "R004", "R005"]
              and lines[0]["new"] == ["R006", "R007"] and lines[0]["again"] == ["R001", "R002", "R004"] and lines[0]["n"] == 1,
              str(lines[0])[:200])
        check("107: each carried decision and field is a carry line of its own, through sift's append, naming the earlier "
              "run's day and the line of its log it comes from",
              len(lines) == 8 and all(e["from"]["run"] == d1 for e in carries.values())
              and carries[("R002", "title and abstract")]["from"]["n"] == earlier_n[("R002", "title and abstract")]
              and carries[("R002", "full text")]["from"]["n"] == earlier_n[("R002", "full text")]
              and carries[("R003", "title and abstract")]["from"]["n"] == earlier_n[("R003", "title and abstract")]
              and carries[("R001", "rating")]["from"]["n"] == earlier_n[("R001", "rating")]
              and carries[("R001", "col_setting")]["value"] == "Rooftop" and [e["n"] for e in lines] == list(range(1, 9))
              and sift.undo(f2)["undone"] is None, str([(k, v["from"]) for k, v in carries.items()])[:300])
        fields = sift.fields_of(sc2, "R001")
        check("107: his own fields and columns are carried, the rating, the notes and a choice column with its settings",
              fields["rating"] == 4 and fields["notes"] == "An invented note on the roof." and fields["own"]["col_setting"] == "Rooftop"
              and [c["name"] for c in sift.table_settings(f2)["own"]] == ["Setting"]
              and sift.table_settings(f2)["own"][0]["options"] == ["Rooftop", "Allotment"], str(fields))
        check("107: the proposal columns are carried as they stand, the review's and Sift's own",
              rows["R005"]["proposed_decision"] == "include" and rows["R005"]["grounds"] == "keepers spoke of calm"
              and rows["R005"]["ai_proposed_decision"] == "maybe" and rows["R005"]["ai_grounds"] == "calm at the hive")
        check("107: a PDF is copied, never moved", (f2 / "pdfs" / "R002.pdf").read_bytes() == pdf
              and (f1 / "pdfs" / "R002.pdf").read_bytes() == pdf)
        with open(f2 / "log.csv", encoding="utf-8", newline="") as fh:
            both_runs = list(csv.DictReader(fh))
        check("107: log.csv holds both runs' searches with their dates, as PRISMA-S asks, the earlier first",
              [(r["date"], r["source"]) for r in both_runs] == [(d1, "PsycInfo"), (d1, "Europe PMC"), (d1, "OpenAlex"),
                                                               (d2, "PsycInfo"), (d2, "Europe PMC"), (d2, "OpenAlex")]
              and [r["records_saved"] for r in both_runs] == ["2", "3", "2", "2", "2", "2"], str(both_runs)[:200])
        c2 = sift.counts(sc2)
        flow = sift.prisma_source(c2)
        check("107, 156: the counts take each record once, the earlier run's and this run's searches each said, and "
              "the PRISMA flow counts this run's own search and records alone since 16 October, the earlier run out of it",
              c2["records"] == 7 and c2["stages"]["ta"]["records"] == 7 and c2["follows"] == {
                  "run": d1, "carried": 5, "again": 3, "new": 2}
              and c2["searches"]["saved"] == 13 and c2["flow"]["duplicates"] == 1 and c2["flow"]["records"] == 5
              and c2["searches"]["dates"] == {d1: {"hits": 7, "saved": 7}, d2: {"hits": 6, "saved": 6}}
              and "Records identified<br/>from databases<br/>(n = 6)<br/>PsycInfo (n = 2)<br/>Europe PMC (n = 2)<br/>OpenAlex (n = 2)" in flow
              and "Search of" not in flow and "New in this run" not in flow
              and "Duplicate records<br/>removed (n = 1)" in flow and "Records screened<br/>(n = 5)" in flow, flow[:300])
        rows_out = sift.count_rows(c2)
        check("107: the export's rows say each search's records, those carried, found again and new",
              rows_out[:5] == [["identification", f"records saved {d1}", 7], ["identification", f"records saved {d2}", 6],
                               ["identification", f"carried from the run of {d1}", 5], ["identification", "found again", 3],
                               ["identification", "new in this run", 2]]
              and sift.count_rows(sift.counts(sc1))[0][0] == "title and abstract", str(rows_out[:5]))
        # two runs of one day, the later following the earlier: the log's rows split where a database comes again
        same_day = scratch / "same_day_runs"
        same_day.mkdir(exist_ok=True)
        (same_day / "log.csv").write_text(
            "date,source,interface,query,hits,records_saved,note\n"
            f"{d1},PsycInfo,,,4,4,\n{d1},OpenAlex,,,3,3,\n{d1},PsycInfo,,,5,5,\n{d1},OpenAlex,,,2,2,\n"
            f"{d2},PsycInfo,,,1,1,\n{d2},OpenAlex,,,1,1,\n", encoding="utf-8")
        split = sift.searches(same_day)
        fake = dict(c2, searches=split, flow=dict(c2["flow"], duplicates=10))
        flow_split = sift.prisma_source(fake)
        rows_split = sift.count_rows(fake)
        check("107, 156: two runs on one day are two searches in the export, a database met again that day beginning "
              "the second, a lone run that day plain (13 October, evening), and the PRISMA flow names no search, "
              "counting the active run's alone since 16 October",
              [(r["date"], r["saved"]) for r in split["runs"]] == [(d1, 7), (d1, 7), (d2, 2)]
              and split["dates"][d1] == {"hits": 14, "saved": 14}
              and "search of" not in flow_split.lower() and "(n = 14)" not in flow_split
              and [r[1] for r in rows_split[:3]] == [f"records saved {d1}, search 1", f"records saved {d1}, search 2",
                                                    f"records saved {d2}"], flow_split[:400])
        shown = {r["rec_id"]: r for r in sift.screen(f2)["records"]}
        check("107: the screen marks the records new in this run, and a screening that follows none marks none",
              [r for r in shown if shown[r]["new"]] == ["R006", "R007"] and not any(r["new"] for r in sift.screen(f1)["records"])
              and sift.decide(f2, "R006", "ta", "include")["record"]["new"] is True)
        sift.undo(f2)
        meta = json.loads((f2 / "run.json").read_text(encoding="utf-8"))
        check("107: run.json keeps the run it follows and what the carry wrote, and the summary says it",
              meta["follows"] == {"date": d1, "carried": 5, "new": 2, "again": 3} and meta["carried"]["log"] == 8
              and meta["carried"]["pdfs"] == {"R002.pdf": len(pdf)} and meta["carried"]["settings"] is True
              and second["follows"]["new"] == 2 and second["merged"] == 7
              and any(line.startswith("  Follows the run of 1 October 2026: 5 records carried with their decisions, "
                                      "3 found again, 2 new.") for line in ss.run_lines(second)), str(meta["follows"]))

        # ── D. begun only by what comes after the carry
        check("107: a folder holding a decision, an undo and the carry is begun by its log", ss.begun(f2) == "its screening log")
        state["phase"] = 2
        d4 = "2026-10-11"
        ss.take_export(review, "psycinfo", ris(("Calm keepers", "2024", "")), "p.ris", day=d4, ctx=ctx())
        ss.run(review, day=d4, ctx=ctx(), follows=d1)
        f4 = review / "runs" / d4
        fresh = ss.begun(f4)
        f4_files = {p.relative_to(f4).as_posix(): p.read_bytes() for p in f4.rglob("*") if p.is_file()}
        again = ss.run(review, day=d4, ctx=ctx(), follows=d1)
        f42 = review / "runs" / f"{d4}-2"
        drop = ss.take_export(review, "psycinfo", ris(("Calm keepers", "2024", ""), ("Honey and the city", "2018", "")),
                              "p.ris", day=d4, ctx=ctx())
        lines4 = sift.read_lines(f42)
        check("107, 9 October: a folder holding the carry alone is not begun, a rerun that day makes the day's next run and "
              "leaves it as it is, and a drop on that next run writes it afresh, its log the carry's own each time",
              fresh == "" and again["date"] == f"{d4}-2" and again["begun"] == "" and drop["date"] == f"{d4}-2"
              and drop["begun"] == "" and lines4[0]["act"] == "follow"
              and {p.relative_to(f4).as_posix(): p.read_bytes() for p in f4.rglob("*") if p.is_file()} == f4_files
              and sum(1 for e in lines4 if e["act"] == "follow") == 1 and drop["follows"]["again"] == 3
              and (f42 / "pdfs" / "R002.pdf").read_bytes() == pdf, str(drop["follows"]))
        sift.set_field(f42, "R006", "rating", 2)
        check("107: one change of his after the carry makes it begun, a drop on it is refused, and a rerun makes the next "
              "run, leaving it as it is",
              ss.begun(f42) == "its screening log"
              and refusal_of(lambda: ss.take_export(review, "psycinfo", ris(("Calm keepers", "2024", "")), "p.ris", day=d4,
                                                    ctx=ctx())).startswith("The run of 11 October 2026, run 2 holds")
              and ss.run(review, day=d4, ctx=ctx(), follows=d1, dry_run=True)["date"] == f"{d4}-3"
              and not (review / "runs" / f"{d4}-3").exists())

        # ── E. None, and the refusals
        nothing = ss.run(review, day=d3, ctx=ctx(), follows="none")
        f3 = review / "runs" / d3
        check("107: None makes a run that carries nothing, its rec_ids R001 up, every record undecided and no log",
              nothing["follows"] is None and sift.load(f3).ids == ["R001", "R002", "R003"] and not (f3 / sift.LOG_NAME).exists()
              and sift.counts(sift.load(f3))["follows"] is None and sift.decided(f3) == 0, str(sift.load(f3).ids))
        (review / "runs" / "2026-09-30").mkdir()
        (review / "runs" / "2026-09-30" / "psycinfo.ris").write_bytes(ris(("Honey and the city", "2018", "")))
        # a run a dropped export began, which Run completes, is the one run that could name itself
        d6 = "2026-10-16"
        ss.take_export(review, "psycinfo", ris(("Honey and the city", "2018", "")), "p.ris", day=d6, ctx=ctx())
        refused = {
            "itself": refusal_of(lambda: ss.run(review, day=d6, ctx=ctx(), follows=d6, dry_run=True)),
            "later": refusal_of(lambda: ss.run(review, day="2026-10-05", ctx=ctx(), follows=d2, dry_run=True)),
            "none": refusal_of(lambda: ss.run(review, day=d3, ctx=ctx(), follows="2026-09-30", dry_run=True)),
            "gone": refusal_of(lambda: ss.run(review, day=d3, ctx=ctx(), follows="2026-09-01", dry_run=True)),
        }
        check("107: following itself, a later day or a run with no screening is refused in one line",
              refused == {"itself": "A run cannot follow itself.",
                          "later": "The run of 8 October 2026 comes after this one, so this run cannot follow it.",
                          "none": "The run of 30 September 2026 holds no screening, so this run cannot follow it.",
                          "gone": "The run of 1 September 2026 holds no screening, so this run cannot follow it."}, str(refused))

        # ── F. the command line and MCP
        os.environ[ss.STUB_ENV] = stub
        cfg = base / "bee-config.json"
        cfg.write_text(json.dumps({"databases": [{"source": "epmc", "how": "api"}, {"source": "openalex", "how": "api"}]}),
                       encoding="utf-8")
        argv = ["sift", "search", "run", str(review), "--config", str(cfg)]
        c_default = cli.run(argv + ["--date", "2026-10-22", "--dry-run"])
        c_none = cli.run(argv + ["--date", "2026-10-22", "--dry-run", "--follows", "none"])
        c_run = cli.run(argv + ["--date", "2026-10-20", "--follows", d1, "--json"])
        c_later = cli.run(argv + ["--date", "2026-10-21", "--follows", "2026-12-01"])
        got = support.plain(json.loads(c_run[1])) if c_run[0] == 0 else {}
        check("107: on the command line --follows names the run a run follows, none carries nothing, and left out it is "
              "the newest earlier run with decisions",
              c_default[0] == 0 and "It follows the run of 11 October 2026, run 2, carrying 7 records, 3 of them decided." in c_default[1]
              and c_none[0] == 0 and "It follows no earlier run." in c_none[1]
              # the run followed named by its number since 12 October, later (124)
              and got.get("follows") == {"date": d1, "carried": 5, "new": 1, "again": 2,
                                         "label": f"Run {ss.run_numbers(review)[d1]}, 1 October 2026",
                                         "number": ss.run_numbers(review)[d1]}
              and c_later[0] == 1 and c_later[2].strip() == "The run of 1 December 2026 comes after this one, so this run "
                                                            "cannot follow it.", c_default[1][-200:] + c_run[2])
        by_name = {t["name"]: t for t in sift_mcp.SEARCH_TOOLS}
        args = mcp_server.arguments(by_name["sift_search_run"], {"folder": str(review), "follows": d1}, {}, "Claude Code")
        srv = mcp_server.Server(config=str(cfg))
        m_dry = srv.call(by_name["sift_search_run"], {"folder": str(review), "dry_run": True, "follows": "none"})
        m_default = srv.call(by_name["sift_search_run"], {"folder": str(review), "dry_run": True})
        check("107: the MCP run tool takes follows the same way, and its dry run says the run it would follow",
              "follows" in by_name["sift_search_run"]["inputSchema"]["properties"] and args.follows == d1
              and m_dry["isError"] is False and m_dry["structuredContent"]["follows"] is None
              and m_default["structuredContent"]["follows"]["date"] == "2026-10-20"
              and "taking dry_run and follows" in mcp_server.instructions("sift"), str(m_default)[:200])
        del os.environ[ss.STUB_ENV]
        src = inspect.getsource(sift_routes.api_sift_search)
        check("107: the screen's run step sends follows, which the route passes to the run and its thread",
              "follows = search_mod.follow_day(body.get(\"follows\"))" in src and "follows=follows" in src
              and "args=(folder, key, listed, follows)" in src
              and "{ op: 'run', folder: SFS.folder, follows }" in sjs and "sfsDrawFollows(live);" in sjs)
    finally:
        ss.Context.__init__ = real_init
        ss.CLOCK, ss.RUNNER = kept_clock, kept_runner
        os.environ.pop(ss.STUB_ENV, None)
        if kept_env is not None:
            os.environ[ss.STUB_ENV] = kept_env
        httpd.shutdown()
        httpd.server_close()

    # ── G. the page's words, the table's filter, the docs and the voice
    check("107, 12 October: the table's Found by filter offers New in this run when the screening has new records",
          "const SF_NEW = '|new';" in sfjs and "[SF_NEW]: 'New in this run'" in sfjs
          and "...((records || []).some((r) => r.new) ? [word(SF_NEW)] : [])" in sfjs and "...(r.new ? [SF_NEW] : [])" in sfjs)
