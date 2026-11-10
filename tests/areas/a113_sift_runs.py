from __future__ import annotations

import csv
import json
import os
import shutil
from pathlib import Path

from . import support
from .support import check, grip_js, line_of_js, refusal_of, skip


@support.as_app("sift")
def test_sift_runs(scratch):
    print("\n113. Sift's runs, 9 October: every run kept, a later run that day its own folder named run 2 and up, a "
          "draft's run marked, Screening keeping the run he last opened, the home card naming it, a problem under its "
          "block and a block's Remove at its foot")
    import subprocess
    import cli
    import mcp_server
    import sift_mcp
    import server as server_mod
    import sift_routes
    import sift
    import sift_search as ss

    sjs = support.text("apps/sift/static/sift_search.js")
    app = support.text("family/static/shell.js", "apps/idiograph/static/distil.js")
    # Sift's parts of the shell, from app.js since the family codebase's third build (22 October 2026)
    sset = support.text("apps/sift/static/sift_settings.js")
    fn = lambda src, name: src.split(f"function {name}(", 1)[1].split("\n}", 1)[0] if f"function {name}(" in src else ""
    whole = lambda src, name: f"function {name}(" + fn(src, name) + "\n}"
    node = shutil.which("node")
    base = scratch / "sift-runs-113"
    shutil.rmtree(base, ignore_errors=True)
    base.mkdir(parents=True)
    files = lambda at: {p.relative_to(at).as_posix(): p.read_bytes() for p in sorted(at.rglob("*")) if p.is_file()}
    # every record invented, on community orchards
    ris = lambda *recs: "".join(f"TY  - JOUR\nTI  - {t}\nPY  - {y}\n" + (f"DO  - {d}\n" if d else "")
                                + "AB  - An invented abstract on an orchard.\nER  - \n\n" for t, y, d in recs).encode("utf-8")
    ctx = lambda: ss.Context(base={}, pause=lambda s: None)
    listed = [{"source": "psycinfo", "platform": "ebsco", "how": "export"}, {"source": "scopus", "how": "export"}]

    # ── A. a run's name: its day, its number that day, its words, and the order the runs were made
    order = base / "order-review"
    for name in ["2026-09-20"] + [f"2026-09-20-{n}" for n in range(2, 10)] + ["2026-09-19", "2026-09-21"]:
        (order / "runs" / name).mkdir(parents=True)
    check("113: a run folder's name gives its day and its number that day, a folder of another name standing as it is, "
          "and its name in words, the day and, from the second, run 2",
          ss.run_parts("2026-10-09") == ("2026-10-09", 1) and ss.run_parts("2026-10-09-2") == ("2026-10-09", 2)
          and ss.run_parts("2026-10-09-12") == ("2026-10-09", 12) and ss.run_parts("pilot") == ("pilot", 1)
          and ss.run_parts("2026-10-09-1") == ("2026-10-09-1", 1)
          and ss.run_said("2026-10-09") == "9 October 2026" and ss.run_said("2026-10-09-2") == "9 October 2026, run 2"
          and ss.run_said("pilot") == "pilot", ss.run_said("2026-10-09-2"))
    check("113: a new run of a day takes the day's next number, the tenth after the ninth, and the runs stand in the "
          "order they were made, a day's later runs after its first and before the next day",
          ss.next_run(order, "2026-09-20") == "2026-09-20-10" and ss.next_run(order, "2026-09-22") == "2026-09-22"
          and [p.name for p in ss.run_dirs(order)][:3] == ["2026-09-21", "2026-09-20-9", "2026-09-20-8"]
          and [p.name for p in ss.run_dirs(order)][-2:] == ["2026-09-20", "2026-09-19"]
          and [p.name for p in sift_routes.run_folders(order)] == [p.name for p in ss.run_dirs(order)],
          str([p.name for p in ss.run_dirs(order)]))

    review = base / "orchard-review"
    review.mkdir()
    ss.save(review, {"databases": ["psycinfo", "scopus"], "blocks": [{"name": "Orchards", "terms": ["orchard*", "\"community orchard\""]}]})
    ss.register(review)
    day = "2026-09-14"
    runs_dir = review / "runs"
    kept_env = os.environ.get(ss.STUB_ENV)
    # every key read from the smoke's keychain in memory, and no request made, every database going by export
    os.environ[ss.STUB_ENV] = "http://127.0.0.1:9"
    kept = (server_mod.CONFIG_PATH, server_mod.ROOT_OVERRIDE, server_mod.STATE_PATH, server_mod.STATE_MEMORY)
    live_config = server_mod.CONFIG_PATH.read_bytes() if server_mod.CONFIG_PATH.exists() else None
    # a run waits for nothing between pages or before a retry, since nothing it asks is answered
    real_init = ss.Context.__init__
    ss.Context.__init__ = lambda self, base=None, pause=None, page=None, email="": real_init(
        self, base, pause if pause is not None else (lambda seconds: None), page, email)
    try:
        # ── B. every run kept: a drop begins the day's run, Run completes it, and Run again makes the next
        ss.take_export(review, "psycinfo", ris(("Apples shared in a village", "2019", "10.5555/orch.1"),
                                               ("Pruning days together", "2020", "")), "p.ris", day=day, ctx=ctx(), listed=listed)
        began = json.loads((runs_dir / day / "run.json").read_text(encoding="utf-8"))
        one = ss.run(review, day=day, ctx=ctx(), listed=listed)
        done1 = json.loads((runs_dir / day / "run.json").read_text(encoding="utf-8"))
        check("113: a drop before Run begins the day's run, marked as waiting for Run, and Run completes that run, never a "
              "second one beside it",
              began.get("waiting_for_run") is True and one["date"] == day and "waiting_for_run" not in done1
              # runs/ holds the run folders and, since 12 October, later (124), numbers.json, each run's number
              and one["merged"] == 2 and sorted(p.name for p in runs_dir.iterdir() if p.is_dir()) == [day]
              and sorted(p.name for p in runs_dir.iterdir() if p.is_file()) == [ss.NUMBERS_NAME], str(began.get("waiting_for_run")))
        first = files(runs_dir / day)
        two = ss.run(review, day=day, ctx=ctx(), listed=listed)
        took = ss.take_export(review, "psycinfo", ris(("Apples shared in a village", "2019", "10.5555/orch.1"),
                                                      ("Cider and neighbours", "2021", "10.5555/orch.3"),
                                                      ("Grafting for beginners", "2022", "")), "p.ris", day=day, ctx=ctx(),
                              listed=listed)
        three = ss.run(review, day=day, ctx=ctx(), listed=listed)
        took3 = ss.take_export(review, "scopus", ris(("Blossom walks", "2023", "10.5555/orch.4")), "s.ris", day=day,
                               ctx=ctx(), listed=listed)
        listed_runs = ss.runs(review)
        check("113: a second and a third run on one day are kept beside the first, runs/<day>-2 and -3, the first byte for "
              "byte as it was, and a drop goes to the day's newest run, the one still waiting on its exports",
              (two["date"], three["date"]) == (f"{day}-2", f"{day}-3") and files(runs_dir / day) == first
              and took["date"] == f"{day}-2" and took["merged"] == 3 and took3["date"] == f"{day}-3" and took3["merged"] == 1
              and len(sift.load(runs_dir / f"{day}-2").ids) == 3 and len(sift.load(runs_dir / day).ids) == 2
              and [r["date"] for r in listed_runs] == [f"{day}-3", f"{day}-2", day], str([r["date"] for r in listed_runs]))
        check("113, updated 12 October, later (124): the runs list names each run plainly by its number in the order made "
              "and its day, Run 2, 14 September 2026, with its day and its number that day, and log.csv dates each search by its day",
              [r["label"] for r in listed_runs] == ["Run 3, 14 September 2026", "Run 2, 14 September 2026", "Run 1, 14 September 2026"]
              and [r["number"] for r in listed_runs] == [3, 2, 1]
              and [(r["day"], r["n"]) for r in listed_runs] == [(day, 3), (day, 2), (day, 1)]
              and {row["date"] for row in ss.read_log(runs_dir / f"{day}-2")} == {day}, str([r["label"] for r in listed_runs]))

        # ── C. a run once begun is never written, and its line
        sift.decide(runs_dir / f"{day}-3", "R001", "ta", "include")
        third_files = files(runs_dir / f"{day}-3")
        refused = refusal_of(lambda: ss.take_export(review, "scopus", ris(("Blossom walks", "2023", "10.5555/orch.4")),
                                                    "s.ris", day=day, ctx=ctx(), listed=listed))
        four = ss.run(review, day=day, ctx=ctx(), listed=listed, follows="none")
        check("113: a drop on a run whose screening has begun is refused in one line, naming the run plainly and saying Run "
              "makes a new run, never to run on another day, and Run makes the next run, the begun one left byte for byte",
              refused == "The run of 14 September 2026, run 3 holds its screening log, so it was left as it is. Run makes a new run."
              and four["date"] == f"{day}-4" and files(runs_dir / f"{day}-3") == third_files, refused)

        # ── D. a later run that day follows an earlier one of the same day, by its folder's name
        sift.decide(runs_dir / day, "R001", "ta", "include")
        offered = [r["date"] for r in ss.follow_choices(review, ss.next_run(review, day))]
        default = ss.default_follows(review, day)
        five =ss.run(review, day=day, ctx=ctx(), listed=listed, follows=day)
        carried5 = ss.take_export(review, "psycinfo", ris(("Apples shared in a village", "2019", "10.5555/orch.1"),
                                                          ("Wassail in the rain", "2024", "")), "p.ris", day=day, ctx=ctx(),
                                  listed=listed)
        meta5 = json.loads((runs_dir / f"{day}-5" / "run.json").read_text(encoding="utf-8"))
        rows5 = {r["source"]: r for r in carried5["rows"]}
        check("113: a later run that day may follow an earlier run of the same day, offered and the default, its decisions "
              "carried, and its own searches told from the earlier one's in log.csv",
              offered == [f"{day}-3", day] and default == f"{day}-3"
              and five["date"] == f"{day}-5" and carried5["follows"]["date"] == day and carried5["follows"]["carried"] == 2
              and carried5["follows"]["label"] == "Run 1, 14 September 2026" and meta5["carried"]["searches"] == 2
              and rows5["psycinfo"]["hits"] == "2" and len(carried5["rows"]) == 2
              and len(ss.read_log(runs_dir / f"{day}-5")) == 4, str(carried5["follows"]))
        sift.decide(runs_dir / f"{day}-5", "R001", "ta", "include")
        self_named = refusal_of(lambda: ss.run(review, day="2026-09-15", ctx=ctx(), listed=listed, follows="2026-09-15",
                                               dry_run=True))
        later = refusal_of(lambda: ss.run(review, day="2026-09-13", ctx=ctx(), listed=listed, follows=f"{day}-2",
                                          dry_run=True))
        check("113: a run that names a later run, or itself, is refused in one line, naming the run plainly",
              later == "The run of 14 September 2026, run 2 comes after this one, so this run cannot follow it."
              and self_named == "A run cannot follow itself.", later)

        # ── E. a draft's run marked, a registered one not
        ss.save(review, {"databases": ["psycinfo", "scopus"], "blocks": [{"name": "Orchards", "terms": ["orchard*"]}]},
                reason="Trying the shorter block")
        six = ss.run(review, which="draft", day=day, ctx=ctx(), listed=listed, follows="none")
        meta6 = json.loads((runs_dir / f"{day}-6" / "run.json").read_text(encoding="utf-8"))
        heads = {r["date"]: ss.run_lines(r)[0] for r in ss.runs(review)}
        check("113: a run of a version not yet registered is kept as a draft's in run.json, nothing stopping it, and the "
              "command line names it as from a draft, not registered, a registered version's run by its version",
              six["date"] == f"{day}-6" and meta6["draft"] is True and meta6["version"] == 2 and six["draft"] is True
              and heads[f"{day}-6"] == "Run of 14 September 2026, run 6, in runs/2026-09-14-6, draft version 2, unregistered."
              and heads[f"{day}-2"] == "Run of 14 September 2026, run 2, in runs/2026-09-14-2, plan version 1."
              and "draft version 2, unregistered" in ss.run_title(runs_dir / f"{day}-6")
              # the screens name a run by its number since 12 October, later (124), the command line by its day
              and ss.run_title(runs_dir / f"{day}-2") == "Run 2, 14 September 2026", heads[f"{day}-6"])

        # ── F. the old shape, one run a day, reads as it did
        old = base / "old-review"
        old.mkdir()
        ss.save(old, {"databases": ["psycinfo"], "blocks": [{"name": "Orchards", "terms": ["orchard*"]}]})
        ss.register(old)
        earlier, follower, waiting = (old / "runs" / d for d in ("2026-08-01", "2026-08-05", "2026-08-09"))
        for at in (earlier, follower):
            at.mkdir(parents=True)
            with open(at / sift.CSV_NAME, "w", encoding="utf-8", newline="") as fh:
                csv.writer(fh).writerows([["rec_id", "title", "abstract"], ["R001", "Old pear trees", "An invented abstract."]])
        (earlier / sift.SEARCHES_NAME).write_text("date,source,interface,query,hits,records_saved,note\n"
                                                  "2026-08-01,PsycInfo,x,orchard*,1,1,plan version 1\n", encoding="utf-8")
        (follower / sift.SEARCHES_NAME).write_text("date,source,interface,query,hits,records_saved,note\n"
                                                   "2026-08-01,PsycInfo,x,orchard*,1,1,plan version 1\n"
                                                   "2026-08-05,PsycInfo,x,orchard*,4,4,plan version 1\n", encoding="utf-8")
        (follower / ss.RUN_FILE).write_text(json.dumps({"version": 1, "draft": False, "date": "2026-08-05",
                                                        "sources": {"psycinfo": {"name": "PsycInfo", "state": "done", "how": "export"}},
                                                        "follows": {"date": "2026-08-01", "carried": 1, "new": 0, "again": 1}}),
                                            encoding="utf-8")
        waiting.mkdir()
        (waiting / ss.RUN_FILE).write_text(json.dumps({"version": 1, "draft": False, "date": "2026-08-09", "exports": {},
                                                       "sources": {"psycinfo": {"name": "PsycInfo", "state": "waiting",
                                                                                "how": "export", "note": "not run yet"}}}),
                                           encoding="utf-8")
        old_runs = ss.runs(old)
        completes = ss.run(old, day="2026-08-09", ctx=ctx(), listed=listed, dry_run=True)
        check("113: a folder of the old shape, one run a day, reads as it always did: its runs by day, their names, a run "
              "that follows another its own day's rows, and a run a drop began before the mark completed by Run",
              [r["date"] for r in old_runs] == ["2026-08-09", "2026-08-05", "2026-08-01"]
              and [r["label"] for r in old_runs] == ["Run 3, 9 August 2026", "Run 2, 5 August 2026", "Run 1, 1 August 2026"]
              and [(row["name"], row["hits"]) for row in old_runs[1]["rows"]] == [("PsycInfo", "4")]
              and old_runs[1]["follows"]["label"] == "Run 1, 1 August 2026"
              and sift_routes.newest_screening(old).name == "2026-08-05" and completes["date"] == "2026-08-09",
              str([r["date"] for r in old_runs]))
        (waiting / sift.CSV_NAME).write_text("rec_id,title,abstract\n", encoding="utf-8")
        passed_by = sift_routes.newest_screening(old).name
        (waiting / sift.CSV_NAME).unlink()
        check("113, 11 October: a newer run whose screening is a header alone, from before an empty run wrote none, never "
              "stands before an earlier run with records as the one Screening opens",
              passed_by == "2026-08-05" and not sift.has_records(waiting) and sift.has_records(follower), passed_by)

        # ── G. Screening keeps his run, kept in the app's list and never in the review's folder
        cfg_file = base / "config.json"
        cfg_file.write_text(json.dumps({"projects": []}), encoding="utf-8")
        server_mod.CONFIG_PATH, server_mod.ROOT_OVERRIDE = cfg_file, None
        server_mod.STATE_PATH = base / "never-state.json"
        server_mod.STATE_MEMORY = {"recent": []}
        rv = sift_routes.api_sift_review
        rv({"op": "open", "folder": str(review)})
        never = rv({"op": "read", "folder": str(review)})["review"]
        before = files(review)
        read2 = sift_routes.api_sift({"op": "read", "folder": str(runs_dir / f"{day}-2")})
        entry = sift_routes.kept_review(review.resolve())
        after = files(review)
        # Sift's read writes the run's own prisma.md, sift.json and lock, as it always has, and nothing else
        changed = {k for k in set(before) | set(after) if before.get(k) != after.get(k)}
        check("113: a review he has never opened a run of opens its newest run with a screening, and the run he opens is "
              "kept in the app's list of reviews, never in the review's folder",
              never["opens"] == f"{day}-5" and Path(never["screening"]).name == f"{day}-5"
              and entry.get("run") == f"{day}-2" and read2["review"]["opens"] == f"{day}-2" and read2["review"]["run"] == f"{day}-2"
              and read2["review"]["label"] == "Run 2, 14 September 2026"
              and changed <= {f"runs/{day}-2/{n}" for n in (sift.PRISMA_NAME, "sift.json", "screening.lock")}
              and server_mod.STATE_MEMORY["sift_reviews"][0]["run"] == f"{day}-2"
              and not server_mod.STATE_PATH.exists(), str(sorted(changed)))
        seven = ss.run(review, day=day, ctx=ctx(), listed=listed, follows="none")
        ss.take_export(review, "scopus", ris(("Ladders and long grass", "2025", "")), "s.ris", day=day, ctx=ctx(), listed=listed)
        held = sift_routes.api_sift_search({"op": "read", "folder": str(review)})
        kept_view = rv({"op": "read", "folder": str(review)})["review"]
        check("113: a new run with records never takes over Screening by itself: the step still opens the run he opened last",
              seven["date"] == f"{day}-7" and sift.is_screening(runs_dir / f"{day}-7") and kept_view["opens"] == f"{day}-2"
              and Path(kept_view["screening"]).name == f"{day}-2" and held["review"]["opens"] == f"{day}-2"
              and held["runs"][0]["date"] == f"{day}-7", str(kept_view))
        opened = sift_routes.api_sift_search({"op": "screening", "folder": str(review), "date": f"{day}-7"})
        sift_routes.api_sift({"op": "read", "folder": opened["folder"]})
        then = rv({"op": "read", "folder": str(review)})["review"]
        renamed = rv({"op": "open", "folder": str(review), "name": "My orchards"})
        check("113: opening another run from the runs makes it the one Screening opens, and opening the project again keeps it",
              then["opens"] == f"{day}-7" and renamed["review"]["opens"] == f"{day}-7"
              and sift_routes.kept_review(review.resolve()).get("run") == f"{day}-7", str(then))

        # ── H. the home card names the run Screening opens, never a newer run that brought nothing
        empty_run = ss.run(review, day=day, ctx=ctx(), listed=listed, follows="none")
        row_of = lambda: next(r for r in sift_routes.review_rows() if server_mod.abs_path(r["folder"]).resolve() == review.resolve())
        row = row_of()
        shutil.rmtree(runs_dir / f"{day}-7")
        gone_row = row_of()
        check("113: the home card names the run Screening opens by its name in words, with that run's counts, never a newer "
              "run that brought nothing, and a kept run since gone gives way to the newest with a screening",
              empty_run["records"] == 0 and empty_run["date"] == f"{day}-8"
              and row["run"]["date"] == f"{day}-7" and row["run"]["label"] == "Run 7, 14 September 2026"
              and row["run"]["screening"] is True and row["run"]["stages"]["ta"]["records"] == 1
              and Path(row["screening"]).name == f"{day}-7"
              and gone_row["run"]["date"] == f"{day}-5" and Path(gone_row["screening"]).name == f"{day}-5", str(row["run"])[:200])

        # ── I. the command line and MCP name runs by their folders
        c_runs = cli.run(["sift", "search", "runs", str(review)])
        c_dry = cli.run(["sift", "search", "run", str(review), "--date", day, "--follows", f"{day}-2", "--dry-run"])
        run_tool = next(t for t in sift_mcp.SEARCH_TOOLS if t["name"] == "sift_search_run")
        check("113: on the command line runs names each run plainly with its folder, which --follows takes, and a dry run "
              "says the next run's folder and the run it follows by name",
              c_runs[0] == 0 and "Run of 14 September 2026, run 2, in runs/2026-09-14-2, plan version 1." in c_runs[1]
              and c_dry[0] == 0 and "into runs/2026-09-14-9:" in c_dry[1]
              and "It follows the run of 14 September 2026, run 2, carrying 3 records, 0 of them decided." in c_dry[1]
              and "2026-10-01-2" in run_tool["inputSchema"]["properties"]["follows"]["description"]
              and "runs/<today>-2/" in run_tool["description"], c_dry[1][-300:])
    finally:
        ss.Context.__init__ = real_init
        (server_mod.CONFIG_PATH, server_mod.ROOT_OVERRIDE, server_mod.STATE_PATH, server_mod.STATE_MEMORY) = kept
        os.environ.pop(ss.STUB_ENV, None)
        if kept_env is not None:
            os.environ[ss.STUB_ENV] = kept_env
    check("113: the live config.json is exactly as it was",
          (server_mod.CONFIG_PATH.read_bytes() if server_mod.CONFIG_PATH.exists() else None) == live_config)

    # ── J. a problem with a term under its own block, as well as under Register
    plan = ss.clean_plan({"databases": ["scopus"], "blocks": [{"name": "Orchards", "terms": ["orchard*"]},
                                                              {"name": "Sharing", "terms": ["share AND swap", "glean*"]}]})
    st = ss.state(base / "orchard-review")
    check("113: each block's own problems are sent beside the plan's, a problem with a term under its block as well as "
          "where it shows now",
          ss.block_problems(plan) == [[], ["share AND swap holds an operator. Put each term on a line of its own."]]
          and "Sharing: share AND swap holds an operator. Put each term on a line of its own." in ss.problems(plan)
          and isinstance(st["block_problems"], list) and len(st["block_problems"]) == len(st["plan"]["blocks"]),
          str(ss.block_problems(plan)))

    # ── K. the screen in node: the blocks, the runs list, the head, Carry decisions from and the home card
    if not node:
        skip("113: the screen's runs and blocks in node", "node is not installed")
    else:
        script = base / "runs-113.js"
        harness = r"""
const els = {};
const mk = (id) => ({ id, setAttribute(k, v) { (this.attrs = this.attrs || {})[k] = v; }, innerHTML: '', value: '', hidden: false, textContent: '', disabled: false, title: '', dataset: {},
  onclick: null, focus() {}, click() { return this.onclick ? this.onclick() : undefined; },
  querySelectorAll: () => [], querySelector: () => null, matches: () => false, closest: () => null });
const $ = (id) => els[id] || (els[id] = mk(id));
$('settings').hidden = true;
$('feedback').hidden = true;
$('sfs-ask').hidden = true;
$('sfs-mark-card').hidden = true;
async function api() { return {}; }
const say = () => {};
const esc = (s) => String(s).replace(/[&<>]/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;' }[c]));
const escAttr = (s) => esc(s).replace(/"/g, '&quot;');
const plural = (n, word) => `${n} ${word}${n === 1 ? '' : 's'}`;
const grow = () => {};
const needsRestart = () => false;
const RESTART_LINE = 'Restart the server to finish this update.';
const document = { activeElement: null, querySelectorAll: () => [], createElement: () => mk('made'), body: { insertBefore() {} } };
const window = { addEventListener() {}, scrollTo() {} };
const localStorage = { getItem: () => null, setItem() {} };
function siftOpen() {}
function sfLeave(then) { then(); }
async function loadLibrary() {}
"""
        body = grip_js() + "\n" + support.table_js() + "\n" + sjs.rsplit("\nsfsBoot();", 1)[0]
        # the band's name drawn by the family's own (bandNameSet, barsD, 6 November 2026)
        home = (whole(app, "bandNameSet") + "\n" + line_of_js(app, "const plural = ").replace("const plural", "const homePlural") + "\n"
                + whole(sset, "reviewDay") + "\n" + whole(sset, "reviewDecided").replace("plural(", "homePlural(") + "\n"
                + whole(sset, "reviewLine") + "\n")
        run = r"""
const out = {};
SFS.catalog = { sources: ['psycinfo', 'scopus'], names: { psycinfo: 'PsycInfo', scopus: 'Scopus' }, keyless: [], apis: ['scopus'],
  scopes: [['tak', 'Title, abstract and keywords']], types: [], platformed: ['psycinfo'], platforms: [['ebsco', 'EBSCO']], sites: {}, platform_sites: {}, hosts: {} };
SFS.plan = { databases: ['scopus'], others: {}, platforms: {}, blocks: [{ name: 'Orchards', terms: ['orchard*'], scope: 'tak', scopes: {} },
  { name: 'Sharing', terms: ['share AND swap'], scope: 'tak', scopes: {} }], years: {}, types: [], benchmark: [], benchmark_titles: {}, overrides: {} };
SFS.data = { block_problems: [[], ['share AND swap holds an operator. Put each term on a line of its own.']], strings: [], problems: [] };
// the blocks drawn: Remove at each block's foot, a box for its problems under its terms
sfsDrawBlocks();
out.blocks = $('sfs-blocks').innerHTML;
// the problems drawn into each block's box, and Remove taking its block and its problems with it
const box = () => ({ innerHTML: '', hidden: true });
const field = () => ({ value: '', oninput: null, onchange: null, onclick: null });
const fake = (i) => { const parts = { '.sfs-bproblems': box(), '.sfs-bname': field(), '.sfs-bscope': field(), '.sfs-terms': field(), '.sfs-bremove': field() };
  return { dataset: { i: String(i) }, parts, querySelector: (sel) => parts[sel] || null, querySelectorAll: () => [] }; };
let blocksEls = [fake(0), fake(1)];
$('sfs-blocks').querySelectorAll = () => blocksEls;
sfsDrawBlockProblems();
out.boxes = blocksEls.map((el) => [el.parts['.sfs-bproblems'].innerHTML, el.parts['.sfs-bproblems'].hidden]);
sfsDrawBlocks();
const removing = blocksEls[0];
blocksEls = [fake(0)];
// an empty block goes at once, and one holding terms asks first (117, see test_sift_ux_review)
SFS.plan.blocks[0].terms = [''];
removing.parts['.sfs-bremove'].onclick();
clearTimeout(SFS.saveTimer);
out.removed = { blocks: SFS.plan.blocks.map((b) => b.name), problems: SFS.data.block_problems,
  box: [blocksEls[0].parts['.sfs-bproblems'].innerHTML, blocksEls[0].parts['.sfs-bproblems'].hidden] };
// the runs list: Today and its number, a draft's run marked, the run Screening opens, a newer run with records
SFS.today = '2026-09-14';
SFS.review = { opens: '2026-09-14', folder: 'r', searches: true, screening: 'r/runs/2026-09-14' };
// each run numbered in the order made, as the server sends it since 12 October, later (124)
const r3 = { date: '2026-09-14-3', day: '2026-09-14', n: 3, number: 6, label: 'Run 6, 14 September 2026', screening: true, records: 4, merged: 3, filled: 0, version: 1, draft: false, missed: [], benchmark: 0, decided: 1, rows: [] };
const r2 = { date: '2026-09-14-2', day: '2026-09-14', n: 2, number: 5, label: 'Run 5, 14 September 2026', screening: true, records: 3, merged: 3, filled: 0, version: 2, draft: true, missed: [], benchmark: 0, decided: 0, rows: [] };
const r1 = { date: '2026-09-14', day: '2026-09-14', n: 1, number: 4, label: 'Run 4, 14 September 2026', screening: true, records: 2, merged: 2, filled: 0, version: 1, draft: false, missed: [], benchmark: 0, decided: 2, rows: [] };
const r0 = { date: '2026-09-10', day: '2026-09-10', n: 1, number: 3, label: 'Run 3, 10 September 2026', screening: true, records: 2, merged: 2, filled: 0, version: 1, draft: false, missed: [], benchmark: 0, decided: 0, rows: [], follows: { date: '2026-09-01-2', label: 'Run 2, 1 September 2026', carried: 2, new: 0, again: 1 } };
SFS.runs = [r3, r2, r1, r0];
SFS.open.add('run:2026-09-10');
out.today = sfsRunRow(r3);
out.draft = sfsRunRow(r2);
out.opened = sfsRunRow(r1);
out.older = sfsRunRow(r0);
SFS.today = '2026-09-20';
out.later = sfsRunRow(r3);
// a database that failed, said in the server's plain words, never the address, the query or what the answer
// held, which the run's log keeps (17 October, later)
out.failed = sfsRunRow(Object.assign({}, r3, { rows: [{ source: 'pubmed', name: 'PubMed', how: 'api', state: 'failed',
  hits: '', saved: '', said: 'PubMed did not answer (HTTP 503).',
  note: 'plan version 1, failed: HTTP 503 from 127.0.0.1:1/entrez/eutils/esearch.fcgi: {"error": "unavailable"}' }] }));
SFS.today = '2027-01-05';
out.nextYear = sfsRunRow(r3);
SFS.today = '2026-09-20';
SFS.follows = null;
sfsDrawFollows(null);
out.follows = [$('sfs-follows').innerHTML, SFS.follows];
// the head names the run, its number and its draft mark
rvHead('screening', { name: 'Orchard review', folder: 'r', searches: true, screening: 'r/runs/2026-09-14-2', opens: '2026-09-14-2',
  run: '2026-09-14-2', label: 'Run 5, 14 September 2026, draft version 2, unregistered' });
out.head = $('sf-name').title;
// the home card names the run Screening opens
out.card = reviewLine({ there: true, searches: true, version: 2, draft: true,
  run: { date: '2026-09-14-2', label: 'Run 5, 14 September 2026', screening: true, stages: { ta: { records: 3, decided: 1, undecided: 2 }, ft: { records: 0 } } } });
out.oldCard = reviewLine({ there: true, searches: true, run: { date: '2026-09-14', screening: false } });
console.log(JSON.stringify(out));
"""
        script.write_text(harness + body + "\n" + home + run, encoding="utf-8")
        ran = subprocess.run([node, str(script)], capture_output=True, text=True, encoding="utf-8", timeout=60, env=dict(os.environ, TZ="UTC"))
        if ran.returncode != 0:
            check("113: the screen's runs and blocks run in node", False, ran.stderr.strip()[:500])
        else:
            o = json.loads(ran.stdout)
            blocks = o["blocks"].split('<div class="sfs-block"')[1:]
            b2 = blocks[1] if len(blocks) > 1 else ""
            at = [b2.find(w) for w in ('class="sfs-terms"', 'class="sfs-problems sfs-bproblems"', 'class="sfs-own"',
                                       '<p class="sfs-block-foot"><button type="button" class="ghost small btn-remove sfs-bremove">Remove</button></p>')]
            check("113, updated 12 October (117): in node, a problem with a term shows under its own block, the other "
                  "block's box hidden, and Remove on an empty block takes it and its problems at once so none stands "
                  "under the wrong block",
                  o["boxes"] == [["", True], ["<p>share AND swap holds an operator. Put each term on a line of its own.</p>", False]]
                  and o["removed"]["blocks"] == ["Sharing"]
                  and o["removed"]["problems"] == [["share AND swap holds an operator. Put each term on a line of its own."]]
                  and o["removed"]["box"] == ["<p>share AND swap holds an operator. Put each term on a line of its own.</p>", False],
                  str(o["removed"]))
            name = lambda html: html.split('class="sfs-run-name">', 1)[1].split("</th>", 1)[0] if "sfs-run-name" in html else ""
            check("113, updated 12 October (123): in node, Keep the decisions from names each run as the runs list does and "
                  "offers a run of the same day, the newest with decisions chosen first",
                  o["follows"][0] == '<option value="2026-09-14-3">Run 6, 14 September</option>'
                  '<option value="2026-09-14">Run 4, 14 September</option><option value="none">No earlier run</option>'
                  and o["follows"][1] == "2026-09-14-3", str(o["follows"]))
