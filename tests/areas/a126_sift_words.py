from __future__ import annotations

import csv
import io
import json
import re
import shutil

import openpyxl

from . import support
from .support import check, refusal_of, skip


@support.as_app("sift")
def test_sift_words(scratch):
    print("\n126. The decisions' words, 12 October: title and abstract a filter, Yes, Maybe and No, full text the decision, "
          "Include, Maybe and Exclude, a record waiting at either To screen, Y, M and N or I, M and E with the old A and "
          "R still working, the note on T, and what is stored unchanged")
    import subprocess
    import cli
    import sift
    import sift_second as two

    sift_src = support.text("apps/sift/static/sift.js")
    node = shutil.which("node")
    base = scratch / "sift-words-126"
    shutil.rmtree(base, ignore_errors=True)
    base.mkdir(parents=True)
    old_words = re.compile(r"\b(Accept|Accepted|Reject|Rejected|Undecided)\b")

    def hives(folder: Path, n: int = 6, letter: str = "H", topic: str = "hive") -> Path:
        """An invented screening on urban beekeeping, a proposal of No on its second record"""
        folder.mkdir(parents=True, exist_ok=True)
        rows = [["rec_id", "title", "authors", "year", "journal", "abstract", "proposed_decision", "proposed_reason", "grounds"]]
        for i in range(1, n + 1):
            rows.append([f"{letter}{i:03d}", f"Keeping a {topic} on the roof, site {i}", "Comb, A; Drone, B", str(2010 + i),
                         "Invented Apiary Notes", f"Six keepers spoke of the {topic} at site {i}.",
                         "exclude" if i == 2 else "", "E1" if i == 2 else "", ""])
        out = io.StringIO()
        csv.writer(out, lineterminator="\n").writerows(rows)
        (folder / sift.CSV_NAME).write_text(out.getvalue(), encoding="utf-8")
        (folder / sift.REASONS_NAME).write_text("stage,code,meaning\nta,E1,Not about bees\nta,E2,No keepers\n"
                                                "ft,F1,No full text\n", encoding="utf-8")
        return folder

    def csv_rows(folder: Path) -> dict:
        with open(folder / sift.CSV_NAME, encoding="utf-8-sig", newline="") as fh:
            return {r["rec_id"]: r for r in csv.DictReader(fh)}

    # ── A. the words, one map on each side, and what reads them
    check("126: the new words read as the stored values, and the old ones still do",
          [sift.decision_word(w) for w in ("Yes", "no", "Include", "exclude", "Maybe", "Accept", "Rejected", "x")]
          == ["include", "exclude", "include", "exclude", "maybe", "include", "exclude", ""])
    check("126: a round goes by the stages' words or its own name, to-screen, yes or include, no or exclude, and anything "
          "else is refused in one line that names the new words",
          [sift.round_key(w) for w in ("to-screen", "To screen", "yes", "Include", "no", "exclude", "undecided", "accepted",
                                       "rejected", "maybe", "all", "differs", "apart")]
          == ["undecided", "undecided", "accepted", "accepted", "rejected", "rejected", "undecided", "accepted", "rejected",
              "maybe", "all", "differs", "apart"]
          and bool(refusal_of(lambda: sift.round_key("later"))))
    js_words = sift_src.split("const SF_WORDS = ", 1)[1].split("\nconst SF_SUGGESTION = ", 1)[0]


    # ── C. in node: the keys
    keymap = {}
    if not node:
        skip("126: the words and keys in node", "node is not installed")
    else:
        harness = "const SF_WORDS = " + js_words + r"""
const out = { keys: {} };
for (const stage of ['ta', 'ft']) {
  out.keys[stage] = {};
  for (const k of ['y', 'm', 'n', 'i', 'e', 'a', 'r', 't', 'u']) out.keys[stage][k] = sfKeyDecision(k, stage);
}
console.log(JSON.stringify(out));
"""
        probe = base / "words.js"
        probe.write_text(harness, encoding="utf-8")
        ran = subprocess.run([node, str(probe)], capture_output=True, text=True, encoding="utf-8", timeout=60)
        out = json.loads(ran.stdout) if ran.returncode == 0 and ran.stdout.strip() else {}
        keymap = out.get("keys") or {}
        check("126: in node, Y, M and N at title and abstract and I, M and E at full text, A and R at both, the other "
              "stage's letters and T, the note's, taking no decision",
              keymap == {"ta": {"y": "include", "m": "maybe", "n": "exclude", "i": "", "e": "", "a": "include", "r": "exclude", "t": "", "u": ""},
                         "ft": {"y": "", "m": "maybe", "n": "", "i": "include", "e": "exclude", "a": "include", "r": "exclude", "t": "", "u": ""}},
              (ran.stderr or json.dumps(keymap))[:400])

    # ── D. a decision by each key, what is stored unchanged
    run = hives(base / "Hive review" / "runs" / "2026-10-12")
    ta_keys = keymap.get("ta") or {"y": "include", "m": "maybe", "n": "exclude", "a": "include", "r": "exclude"}
    ft_keys = keymap.get("ft") or {"i": "include", "m": "maybe", "e": "exclude"}
    sift.decide(run, "H001", "ta", ta_keys["y"])
    sift.decide(run, "H002", "ta", ta_keys["n"], "E1")
    sift.decide(run, "H003", "ta", ta_keys["m"])
    sift.decide(run, "H004", "ta", ta_keys["a"])
    sift.decide(run, "H005", "ta", ta_keys["r"], "E2")
    sift.decide(run, "H001", "ft", ft_keys["i"])
    sift.decide(run, "H003", "ft", ft_keys["e"], "F1")
    sift.decide(run, "H004", "ft", ft_keys["m"])
    rows = csv_rows(run)
    log = [e for e in sift.read_log(run) if e.get("act") == "decide"]
    check("126: a decision by each key at each stage, Y, N, M, A and R, then I, E and M, stores what the files always "
          "held, include, maybe or exclude, in the CSV's decision columns and the log, a record not yet decided empty",
          [rows[r]["decision"] for r in ("H001", "H002", "H003", "H004", "H005", "H006")] == ["include", "exclude", "maybe", "include", "exclude", ""]
          and [rows[r]["reason"] for r in ("H002", "H005")] == ["E1", "E2"]
          and [rows[r]["ft_decision"] for r in ("H001", "H003", "H004")] == ["include", "exclude", "maybe"] and rows["H003"]["ft_reason"] == "F1"
          and [e["decision"] for e in log] == ["include", "exclude", "maybe", "include", "exclude", "include", "exclude", "maybe"]
          and all(set(r) >= {"decision", "ft_decision"} for r in rows.values()), str([(e["rec_id"], e["decision"]) for e in log]))
    check("126: a decision is refused for a record not taken forward, a word that is none, and Exclude at full text "
          "with no reason",
          all(refusal_of(f) for f in (lambda: sift.decide(run, "H002", "ft", "include"),
                                      lambda: sift.decide(run, "H006", "ta", "perhaps"),
                                      lambda: sift.decide(run, "H004", "ft", "exclude"))))
    flow = sift.prisma_source(sift.counts(sift.load(run)))
    check("126: the flow says To screen inside Records screened and Reports assessed, Sift's own line, PRISMA's own box "
          "words as they were",
          '"Records screened<br/>(n = 6)<br/>To screen<br/>(n = 1)<br/>Maybe (n = 1)"' in flow
          and '"Reports assessed<br/>for eligibility<br/>(n = 3)<br/>To screen<br/>(n = 0)<br/>Maybe (n = 1)"' in flow
          and "Awaiting a decision" not in flow and "Records excluded" in flow and "Reports excluded" in flow
          and "Studies included" in flow, flow[:500])
    check("126: the counts file keeps its measure names, the review's own tooling reading them",
          [r[1] for r in sift.count_rows(sift.counts(sift.load(run))) if r[0] == "title and abstract"][:6]
          == ["records", "decided", "undecided", "include", "maybe", "exclude"])

    # ── E. the command line
    code_c, counts_text, _ = cli.run(["sift", str(run), "counts"])
    code_l, ta_screen, _ = cli.run(["sift", str(run), "list", "--stage", "ta", "--round", "to-screen"])
    code_o, ta_old, _ = cli.run(["sift", str(run), "list", "--stage", "ta"])
    code_y, ta_yes, _ = cli.run(["sift", str(run), "list", "--stage", "ta", "--round", "yes"])
    code_n, ta_no, _ = cli.run(["sift", str(run), "list", "--stage", "ta", "--round", "no"])
    code_i, ft_inc, _ = cli.run(["sift", str(run), "list", "--stage", "ft", "--round", "include"])
    code_j, ta_json, _ = cli.run(["sift", str(run), "list", "--stage", "ta", "--round", "no", "--json"])
    code_s, show, _ = cli.run(["sift", str(run), "show", "H002"])
    code_t, show_ft, _ = cli.run(["sift", str(run), "show", "H003"])
    code_b, _, bad = cli.run(["sift", str(run), "list", "--round", "accepted-ish"])
    got_json = support.plain(json.loads(ta_json)) if code_j == 0 else {}
    check("126: the command line's counts in each stage's words, Yes, Maybe and No, then Include, Maybe and Exclude, "
          "with those still to screen",
          code_c == 0 and "Title and abstract: 6 records, 5 decided, 1 to screen." in counts_text
          and "  Yes 2, Maybe 1, No 2 (E1 1, E2 1)." in counts_text
          and "Full text: 3 records, 3 decided, 0 to screen." in counts_text and "  Include 1, Maybe 1, Exclude 1 (F1 1)." in counts_text
          and not old_words.search(counts_text) and "undecided" not in counts_text and "reject" not in counts_text.lower(), counts_text)
    check("126: the command line's record lines in the stage's words, To screen, Yes, No with its reason and the proposal "
          "too, Include at full text, the default round to-screen and the old undecided the same",
          code_l == code_o == code_y == code_n == code_i == 0
          and ta_screen.splitlines()[0] == "Screening 2026-10-12, title and abstract, to screen: 1 record."
          and ta_screen.splitlines()[1].startswith("H006  To screen  Keeping a hive on the roof, site 6 (2016), no proposal")
          and ta_old == ta_screen
          and [l.split("  ")[:2] for l in ta_yes.splitlines()[1:]] == [["H001", "Yes"], ["H004", "Yes"]]
          and ta_yes.splitlines()[0] == "Screening 2026-10-12, title and abstract, Yes: 2 records."
          and ta_no.splitlines()[1].startswith("H002  No E1  Keeping a hive on the roof, site 2 (2012), proposed No E1 (csv)")
          and ft_inc.splitlines()[0] == "Screening 2026-10-12, full text, Include: 1 record." and "H001  Include  " in ft_inc
          and not old_words.search(ta_screen + ta_yes + ta_no + ft_inc), ta_no + ft_inc)
    check("126: the JSON keeps the stored values and the round's own name",
          got_json.get("round") == "rejected" and [(r["rec_id"], r["decision"], r["reason"]) for r in got_json.get("records", [])]
          == [("H002", "exclude", "E1"), ("H005", "exclude", "E2")]
          and got_json["records"][0]["proposal"]["decision"] == "exclude", str(got_json)[:300])
    check("126: a record shown says its stage's decisions and the log's lines in the stage's words, and a round that is "
          "none is refused in the new words",
          code_s == code_t == 0 and "Title and abstract: No E1, proposed No E1 (csv)." in show
          and re.search(r"\d\. .*, decide No E1 at title and abstract, Sift", show)
          and "Title and abstract: Maybe, no proposal." in show_ft and "Full text: Exclude F1, no proposal." in show_ft
          and re.search(r", decide Exclude F1 at full text, Sift", show_ft)
          and not old_words.search(show + show_ft) and "undecided" not in show + show_ft
          and code_b != 0 and "to-screen, maybe, yes or include, no or exclude" in bad, show + bad)

    # ── F. the second screener's workbooks and the differences workbook
    pond = hives(base / "Pond review" / "runs" / "2026-10-12", letter="P", topic="pond")
    on = {"on": True, "first": "KB", "name": "LW", "share": 100, "calibration": 0, "kappa": 0.6}
    made = two.make_workbook(pond, "ta", on, question="How do keepers live a swarm?")
    path = pond / made["file"]
    wb = openpyxl.load_workbook(path)
    recs = wb["Records"]
    dvs = {str(dv.sqref): dv for dv in recs.data_validations.dataValidation}
    check("126: the second screener's workbook at title and abstract offers Yes, Maybe and No in its Decision column",
          dvs.get("G2:G7") is not None and dvs["G2:G7"].formula1 == '"Yes,Maybe,No"', str(list(dvs)))
    fill = {"P001": "Yes", "P002": "No", "P003": "Maybe", "P004": "Accept", "P005": "Reject"}
    for r in range(2, recs.max_row + 1):
        rec = recs.cell(row=r, column=1).value
        if rec in fill:
            recs.cell(row=r, column=7).value = fill[rec]
        if rec in ("P002", "P005"):
            recs.cell(row=r, column=8).value = "E1 Not about bees"
    buf = io.BytesIO()
    wb.save(buf)
    got = two.take_back(pond, buf.getvalue(), path.name, on)
    took = {e["rec_id"]: e["decision"] for e in two.lines_of(pond) if e.get("change") == "decision"}
    with open(pond / two.MIRROR_NAME, encoding="utf-8-sig", newline="") as fh:
        mirror = list(csv.reader(fh))
    check("126: taken back, Yes, No and Maybe and a workbook's older Accept and Reject are kept as include, exclude and "
          "maybe in the log and screening.second.csv, as before, the blank row still to screen",
          got["taken"] == 5 and got["blank"] == 1
          and took == {"P001": "include", "P002": "exclude", "P003": "maybe", "P004": "include", "P005": "exclude"}
          and {row[1]: row[2] for row in mirror[1:]} == took, str(took) + str(mirror[:3]))
    for rec, d in (("P001", "include"), ("P002", "include"), ("P003", "maybe"), ("P004", "include"), ("P005", "exclude"), ("P006", "include")):
        sift.decide(pond, rec, "ta", d, "E2" if d == "exclude" else "", second=on)
    wb2 = openpyxl.load_workbook(path)
    for r in range(2, wb2["Records"].max_row + 1):
        if wb2["Records"].cell(row=r, column=1).value == "P006":
            wb2["Records"].cell(row=r, column=7).value = "Yes"
    buf = io.BytesIO()
    wb2.save(buf)
    two.take_back(pond, buf.getvalue(), path.name, on)
    diff = two.make_differences(pond, "ta", on)
    dws = openpyxl.load_workbook(pond / diff["file"])["Differences"]
    drow = {dws.cell(row=r, column=1).value: (dws.cell(row=r, column=3).value, dws.cell(row=r, column=6).value)
            for r in range(2, dws.max_row + 1)}
    check("126: the differences workbook gives both decisions in the stage's words, Yes against No",
          drow.get("P002") == ("Yes", "No"), str(drow))
    settled = two.settle_one(pond, "P002", "ta", "agreed", "Yes", settings=on)
    outcome = [e for e in two.lines_of(pond) if e.get("change") == "outcome"]
    check("126: an outcome given as Yes is kept as include, and one that is no decision refused",
          bool(settled) and outcome and outcome[-1]["decision"] == "include"
          and bool(refusal_of(lambda: two.settle_one(pond, "P002", "ta", "agreed", "perhaps", settings=on))), str(outcome[-1:]))
    ft_made = two.make_workbook(pond, "ft", on)
    fwb = openpyxl.load_workbook(pond / ft_made["file"])
    ftdv = [dv for dv in fwb["Records"].data_validations.dataValidation if str(dv.sqref).startswith("G")]
    check("126: at full text the workbook offers Include and Exclude in its Decision column",
          len(ftdv) == 1 and ftdv[0].formula1 == '"Include,Exclude"', str(len(ftdv)))

    # ── G. a made-up language (siftlang, 1 November 2026): Sift's words come from its catalogue, so a language of
    # its own shows on a Sift screen, in Sift's scripts and in a Sift refusal, while English reads as before
    import boot
    import i18n
    import server as server_mod
    import sift_routes
    zz = {
        "page_sift.json": {"page_sift.screens.export_prisma_counts": "Zz the PRISMA zz",
                           "page_sift.screens.start_again": "Zz again"},
        "sift.json": {"sift.ta.include": "Zz-yes", "sift.to_screen": "Zz waiting"},
        "sift_server.json": {"sift_server.the_round_is_to_screen": "Zz: no such round.",
                             "sift_server.routes.not_opened": "Zz: open its project first.",
                             "sift_server.flow.screened": "Zz screened"},
    }
    fx = scratch / "a126-zz"
    shutil.rmtree(fx, ignore_errors=True)
    (fx / "static" / "i18n" / "zz").mkdir(parents=True)
    for name, messages in zz.items():
        (fx / "static" / "i18n" / "zz" / name).write_text(json.dumps(messages), encoding="utf-8")
    kept = (i18n.LANGUAGE, i18n.ROOTS)
    try:
        i18n.ROOTS = lambda: [*boot.roots(server_mod.apps_served("sift")), fx]
        i18n.LANGUAGE = lambda: "zz"
        page = i18n.fill(support.source("apps/sift/static/sift.html").read_text(encoding="utf-8"), "zz",
                         slots={"app": "Sift"})
        refused = refusal_of(lambda: sift.round_key("later"))
        guard = sift_routes.NOT_OPENED
        flow = sift.prisma_source(sift.counts(sift.load(pond)))
        script = i18n.script("zz")[len("<script>"):-len("</script>")]
    finally:
        i18n.LANGUAGE, i18n.ROOTS = kept
    check("126: in a made-up language a Sift screen's markup takes its words, Export PRISMA counts and Start again in "
          "it, the words it lacks in English",
          ">Zz the PRISMA zz<" in page and ">Zz again<" in page and ">Export to Zotero<" in page
          and ">Export PRISMA counts<" not in page)
    check("126: in a made-up language a Sift refusal, a module's word another module names and the PRISMA flow's box "
          "are in its words, and in English as before",
          refused == "Zz: no such round." and guard == "Zz: open its project first." and '["Zz screened<br/>' in flow
          and sift_routes.NOT_OPENED.startswith("That screening is in no Sift project")
          and refusal_of(lambda: sift.round_key("later")).startswith("The round is to-screen"), str([refused, guard]))
    if node:
        probe = scratch / "a126-zz.js"
        # sift.js as it is, its words by key, not as the checks before read it back in English
        raw = support.source("apps/sift/static/sift.js").read_text(encoding="utf-8")
        probe.write_text(script + "\n" + support.text("family/static/i18n.js") + "\n" + support.sift_words_js(raw)
                         + "\nconsole.log(JSON.stringify([SF_WORDS.ta.include, SF_WORDS.ft.include, t('sift.to_screen')]));\n",
                         encoding="utf-8")
        ran = subprocess.run([node, str(probe)], capture_output=True, text=True, encoding="utf-8", timeout=60)
        said = (json.loads(ran.stdout.strip().splitlines()[-1]) if ran.returncode == 0 and ran.stdout.strip()
                else ran.stderr[-300:])
        check("126: in a made-up language sift.js's decisions take its words, Yes as Zz-yes and To screen as Zz waiting, "
              "Include, which it lacks, in English", said == ["Zz-yes", "Include", "Zz waiting"], str(said))

