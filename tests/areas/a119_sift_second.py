from __future__ import annotations

import csv
import io
import json
import shutil

import openpyxl

from . import support
from .support import check, refusal_of, sift_words_js, skip


@support.as_app("sift")
def test_sift_second(scratch):
    print("\n119. Sift's second screener, 12 October: PRISMA 2020 item 8, the settings per project, calibration, a seeded "
          "draw, their workbook and its return, blind both ways, the agreement and kappa before any discussion, a "
          "further draw, Where we differ, the differences workbook, a third reviewer, and the counts and the flow")
    import base64
    import subprocess
    import server as server_mod
    import sift_routes
    import sift
    import sift_second as two

    flat = lambda text: " ".join(str(text).split())
    page = support.page_text()
    app = support.text("family/static/shell.js", "apps/idiograph/static/distil.js")
    # Sift's parts of the shell, from app.js since the family codebase's third build (22 October 2026)
    sset = support.text("apps/sift/static/sift_settings.js")
    sjs = support.text("apps/sift/static/sift.js")
    fn = lambda src, name: src.split(f"function {name}(", 1)[1].split("\n}", 1)[0] if f"function {name}(" in src else ""
    node = shutil.which("node")
    base = scratch / "sift-second-119"
    shutil.rmtree(base, ignore_errors=True)
    base.mkdir(parents=True)

    def tree(at: Path) -> dict:
        # each path with slashes on any system, and a lock file never read, since Windows refuses a
        # read of a file another holds locked (14 October)
        return {p.relative_to(at).as_posix(): (p.read_bytes() if p.is_file() and p.suffix != ".lock" else None)
                for p in sorted(at.rglob("*"))}

    def bells(folder: Path, n: int = 30) -> Path:
        """An invented screening on village bell-ringing, its own proposals, notes and ratings among it"""
        folder.mkdir(parents=True, exist_ok=True)
        rows = [["rec_id", "title", "authors", "year", "journal", "abstract", "proposed_decision", "proposed_reason",
                 "grounds", "rating", "notes"]]
        for i in range(1, n + 1):
            rows.append([f"B{i:03d}", f"Ringing the tenor bell, tower {i}", "Rope, A; Clapper, B", str(2000 + i % 20),
                         "Invented Campanology Notes", f"Eight ringers spoke of tower {i}." + (" =HYPERLINK(1)" if i == 7 else ""),
                         "include", "", f"GROUNDSWORD{i}", "4", f"MYNOTEWORD{i}"])
        out = io.StringIO()
        csv.writer(out, lineterminator="\n").writerows(rows)
        (folder / "screening.csv").write_text(out.getvalue(), encoding="utf-8")
        (folder / "reasons.csv").write_text("stage,code,meaning\nta,E1,Not about bells\nta,E2,No ringers\n"
                                            "ft,F1,No full text\nft,F2,Not qualitative\n", encoding="utf-8")
        return folder

    def fill(path: Path, rows: dict, sheet: str = "Records") -> bytes:
        """A workbook filled as the second screener might, by rec_id: Decision, Reason and Note, or Reply and its note"""
        wb = openpyxl.load_workbook(path)
        ws = wb[sheet]
        head = [str(c.value or "") for c in ws[1]]
        for r in range(2, ws.max_row + 1):
            rec = ws.cell(row=r, column=1).value
            for name, value in rows.get(rec, {}).items():
                ws.cell(row=r, column=head.index(name) + 1).value = value
        buf = io.BytesIO()
        wb.save(buf)
        return buf.getvalue()

    # ── A. the settings and their defaults
    s0 = two.settings_of(None)
    odd = two.settings_of({"on": "yes", "first": "  T   W ", "name": "R" * 60, "share": "250", "calibration": -4, "kappa": "abc"})
    check("119: the second screener's settings default by the book, off, every record drawn, no calibration and a "
          "further draw below a kappa of 0.6 (McHugh 2012), and anything of another shape is set to its default or "
          "kept to its bounds",
          s0 == {"on": False, "first": "", "name": "", "share": 100, "calibration": 0, "kappa": 0.6}
          and odd == {"on": False, "first": "T W", "name": "R" * 40, "share": 100, "calibration": 0, "kappa": 0.6}
          and two.settings_of({"share": 20, "calibration": 20, "kappa": 0.456, "on": True})["kappa"] == 0.46, str(odd))

    # ── B. calibration, the seeded draw, a further draw
    run = bells(base / "Bell review" / "runs" / "2026-10-12")
    on = {"on": True, "first": "TW", "name": "RM", "share": 40, "calibration": 5, "kappa": 0.6}
    off_said = refusal_of(lambda: two.make_workbook(run, "ta", dict(on, on=False)))
    cal_said = refusal_of(lambda: two.make_workbook(run, "ta", on))
    seen = two.view(run, on)["stages"]["ta"]
    for i in range(1, 6):
        sift.decide(run, f"B{i:03d}", "ta", "include", second=on)
    marked = [e for e in sift.read_log(run) if e.get("calibration")]
    check("119: the first records of a stage by number, as many as the calibration setting, are screened together, each "
          "decision on one marked calibration in the log, and no draw is made while one is undecided or while the "
          "second screener is off, each said in one line",
          [e["rec_id"] for e in marked] == ["B001", "B002", "B003", "B004", "B005"]
          and off_said == two.TURNED_OFF
          and cal_said == "Decide the 5 calibration records left at title and abstract first, together."
          and seen["calibration"] == 5 and seen["calibration_left"] == 5 and seen["size"] == 10
          and seen["waits"] == cal_said and seen["waits_calibration"] is True, cal_said)
    q = "How do ringers live the long peal?"
    made = two.make_workbook(run, "ta", on, question=q, eligibility=["Years: 2000 to 2026", "Document types: journal article"])
    lines = two.lines_of(run)
    draw1 = next(e for e in lines if e.get("change") == "draw")
    check("119: the first workbook makes the draw: the share of the records beyond calibration, rounded up, at random "
          "with a seed Sift chooses, logged with the calibration records, the pool in number order and the rec_ids "
          "drawn, and the draw repeats from its seed",
          made["records"] == 10 and made["drew"] == 1 and len(draw1["rec_ids"]) == 10
          and not set(draw1["rec_ids"]) & set(draw1["calibration"]) and draw1["calibration"] == [f"B{i:03d}" for i in range(1, 6)]
          and draw1["pool"] == [f"B{i:03d}" for i in range(6, 31)] and 100000 <= draw1["seed"] < 1000000
          and sorted(two.redraw(draw1["pool"], draw1["seed"], 10)) == sorted(draw1["rec_ids"])
          and draw1["first"] == "TW" and draw1["name"] == "RM" and draw1["share"] == 40
          and not any(e.get("act") == "second" for e in sift.read_log(run)), str(draw1.get("rec_ids")))
    drawn = draw1["rec_ids"]

    # ── C. their workbook: its sheets, dropdowns, protection, no fills and nothing of his
    path = run / made["file"]
    wb = openpyxl.load_workbook(path)
    about, recs, mark = wb["About"], wb["Records"], wb["sift"]
    about_text = flat(" ".join(str(c.value) for row in about.iter_rows() for c in row if c.value is not None))
    every = " ".join(str(c.value) for ws in wb.worksheets for row in ws.iter_rows() for c in row if c.value is not None)
    dvs = {str(dv.sqref): dv for dv in recs.data_validations.dataValidation}
    fills = [c.coordinate for ws in wb.worksheets for row in ws.iter_rows() for c in row if c.fill is not None and c.fill.fill_type]
    open_cells = sorted({c.column_letter for row in recs.iter_rows(min_row=2) for c in row if not c.protection.locked})
    check("119: their workbook is written beside the screening, its first sheet the review's question, the eligibility "
          "the plan sets and the reasons to reject at the stage, then the Records sheet, and a sheet no one sees",
          made["file"] == "Second screener, title and abstract.xlsx" and path.is_file()
          and wb.sheetnames == ["About", "Records", "sift"] and mark.sheet_state == "veryHidden"
          and q in about_text and "Years: 2000 to 2026" in about_text and "Document types: journal article" in about_text
          and "E1 Not about bells" in about_text and "E2 No ringers" in about_text and "F1" not in about_text, about_text[:300])
    head = [c.value for c in recs[1]]
    row7 = next((r for r in range(2, recs.max_row + 1) if recs.cell(row=r, column=1).value == "B007"), None)
    check("119: a row for each drawn record, rec_id, Title, Authors, Year, Journal and Abstract laid out to read, wrapped, "
          "wide and the header frozen, then Decision, Reason and Note, text that looks like a formula kept as text",
          head == ["rec_id", "Title", "Authors", "Year", "Journal", "Abstract", "Decision", "Reason", "Note"]
          and [recs.cell(row=r, column=1).value for r in range(2, recs.max_row + 1)] == drawn
          and recs.freeze_panes == "B2" and recs.column_dimensions["F"].width >= 60
          and recs.cell(row=2, column=6).alignment.wrap_text and recs.row_dimensions[2].height >= 15
          and (row7 is None or recs.cell(row=row7, column=6).data_type == "s"), str(head))
    check("119, updated 12 October (126): Decision is a dropdown of Yes, Maybe and No at title and abstract, Reason a dropdown of the plan's "
          "codes for the stage, and the sheets are protected with no password, so only Decision, Reason and Note take "
          "typing, the workbook's sheets kept as they are",
          dvs.get("G2:G11") is not None and dvs["G2:G11"].formula1 == '"Yes,Maybe,No"'
          and dvs.get("H2:H11") is not None and dvs["H2:H11"].formula1 == "sift!$D$1:$D$2"
          and [mark.cell(row=i, column=4).value for i in (1, 2)] == ["E1 Not about bells", "E2 No ringers"]
          and recs.protection.sheet and about.protection.sheet and not recs.protection.password
          and open_cells == ["G", "H", "I"] and wb.security is not None and wb.security.lockStructure, str(list(dvs)))
    check("119: no cell fill anywhere, and nothing of his decisions, notes, ratings or the proposals goes in",
          not fills and "MYNOTEWORD" not in every and "GROUNDSWORD" not in every and "include" not in every.lower()
          and not any(w in every for w in ("Accepted", "Rejected", "proposed")), str(fills[:5]))

    # ── D. blind both ways, then the workbook taken back
    sift.note(run, drawn[0], "ta", "MYNOTEWORD on a drawn one")
    his = {r: "include" for r in drawn[:6]} | {r: "exclude" for r in drawn[6:8]} | {r: "include" for r in drawn[8:]}
    theirs = {r: {"Decision": "Accept"} for r in drawn[:4]} | {r: {"Decision": "Maybe"} for r in drawn[4:6]}
    theirs |= {r: {"Decision": "Reject", "Reason": "E2 No ringers", "Note": "no ringers here"} for r in drawn[6:10]}
    theirs[drawn[9]]["Decision"] = None
    got = two.take_back(run, fill(path, theirs), path.name, on)
    stranger = openpyxl.Workbook()
    stranger.active.append(["rec_id", "Decision"])
    buf = io.BytesIO()
    stranger.save(buf)
    other = bells(base / "Other review" / "runs" / "2026-10-12")
    for i in range(1, 6):
        sift.decide(other, f"B{i:03d}", "ta", "include", second=on)
    other_book = other / two.make_workbook(other, "ta", on)["file"]
    refused = [refusal_of(lambda: two.take_back(run, buf.getvalue(), "mine.xlsx", on)),
               refusal_of(lambda: two.take_back(run, b"%PDF-1.4 not a workbook", "a.xlsx", on)),
               refusal_of(lambda: two.take_back(run, other_book.read_bytes(), other_book.name, on))]
    blind = two.view(run, on)
    hist = sift.history(run, drawn[0])["history"]
    check("119: a returned workbook is checked as the one Sift made for this screening and its decisions, reasons and "
          "notes taken in, each a line of the log, a row left blank staying undecided, and a stranger, a file that is no "
          "workbook and another screening's workbook each refused in one line",
          got["taken"] == 9 and got["blank"] == 1 and got["kind"] == "second"
          and refused == [two.NOT_OURS] * 3
          and sum(1 for e in two.lines_of(run) if e.get("change") == "decision") == 9
          and (run / two.MIRROR_NAME).read_text(encoding="utf-8").count("\n") == 10, str(refused))
    check("119: until he has decided every drawn record the second screener's decisions stay hidden from him: the side "
          "says how many came back and how many he has still to decide, never which way theirs went, and a record's "
          "history leaves them out",
          blind["stages"]["ta"]["back"] == 9 and blind["stages"]["ta"]["blind_left"] == 10
          and not any("theirs" in (x.get("ta") or {}) for x in blind["records"].values())
          and blind["stages"]["ta"]["agreements"] == [] and blind["stages"]["ta"]["differences"]["all"] == 0
          and not any(e.get("act") == "second" for e in hist)
          and sift.listed(sift.load(run), sift.read_log(run), "ta", "apart") == [], str(blind["stages"]["ta"]))
    for r, d in his.items():
        sift.decide(run, r, "ta", d, "E1" if d == "exclude" else "", second=on)
    lifted = two.view(run, on)
    unblind = [e for e in two.lines_of(run) if e.get("change") == "unblind"]
    check("119: once he has decided every drawn record the draw is unblinded, his decisions as they stood kept in the "
          "log beside it, and the record shows theirs, one not back yet saying so",
          len(unblind) == 1 and unblind[0]["mine"][drawn[7]] == ["exclude", "E1"]
          and lifted["records"][drawn[6]]["ta"]["theirs"]["reason"] == "E2"
          and lifted["records"][drawn[9]]["ta"]["theirs"] is None and lifted["stages"]["ta"]["agreements"] == []
          and any(e.get("change") == "decision" for e in sift.history(run, drawn[6])["history"] if e.get("act") == "second"),
          str(lifted["records"].get(drawn[9])))

    # ── E. the agreement, before any discussion, against a hand-worked example
    sift.decide(run, drawn[0], "ta", "maybe", second=on)
    got2 = two.take_back(run, fill(path, {drawn[9]: {"Decision": "Reject", "Reason": "E1 Not about bells"}}), "back again.xlsx", on)
    agreed = [e for e in two.lines_of(run) if e.get("change") == "agreement"]
    hand = two.agreement({f"x{i}": p for i, p in enumerate([["include", "include"]] * 6 + [["exclude", "exclude"]] * 2
                                                         + [["include", "exclude"]] * 2)})
    edge = two.agreement({f"y{i}": p for i, p in enumerate([["include", "include"]] * 4 + [["exclude", "exclude"]] * 4
                                                         + [["include", "exclude"], ["exclude", "include"]])})
    one_way = two.agreement({"z1": ["include", "maybe"], "z2": ["maybe", "include"]})
    a = agreed[0] if agreed else {}
    check("119: worked by hand, six both forward, two both rejecting and two he took forward that they rejected give 8 of "
          "10 alike, 0.8, and kappa (0.8 less 0.56) over 0.44, 0.545, four, four and one each way give exactly 0.6, and "
          "both putting every record one way gives no kappa",
          hand["alike"] == 8 and hand["proportion"] == 0.8 and hand["kappa"] == 0.545
          and hand["table"]["include"]["exclude"] == 2 and edge["kappa"] == 0.6 and one_way["kappa"] is None
          and one_way["alike"] == 2, str(hand))
    check("119: once both have decided the drawn records Sift records at once and for good, in the log, the number and "
          "proportion decided alike, the kappa on going forward against Reject, with the three-way table, his decisions "
          "taken as they stood before he saw theirs, so a change after makes no difference",
          got2["taken"] == 1 and len(agreed) == 1 and a.get("records") == 10 and a.get("alike") == 8
          and a.get("proportion") == 0.8 and a.get("kappa") == 0.545 and a["table"]["include"]["maybe"] == 2
          and a["table"]["include"]["exclude"] == 2 and a["pairs"][drawn[0]] == ["include", "include"]
          and a.get("threshold") == 0.6 and a.get("first") == "TW", str(a)[:300])
    view_a = two.view(run, on)["stages"]["ta"]
    further_said = refusal_of(lambda: two.draw(run, "ta", dict(on, kappa=0.5)))
    more = two.draw(run, "ta", on)
    draw2 = [e for e in two.lines_of(run) if e.get("change") == "draw"][-1]
    check("119: a kappa below the setting offers a further draw, which takes the same share from the records not yet "
          "drawn with its own seed logged, and none is offered at or above it",
          view_a["further"] and further_said == "A further draw is offered once a draw's kappa is below the setting."
          and more["draw"] == 2 and draw2["draw"] == 2 and len(draw2["rec_ids"]) == 10
          and not set(draw2["rec_ids"]) & set(drawn) and not set(draw2["rec_ids"]) & set(draw1["calibration"])
          and len(draw2["pool"]) == 15 and set(draw2["pool"]) == set(draw1["pool"]) - set(drawn)
          and sorted(two.redraw(draw2["pool"], draw2["seed"], 10)) == sorted(draw2["rec_ids"]),
          further_said)
    again = two.make_workbook(run, "ta", on)
    check("119: the workbook made again holds the records drawn and not yet back, under a name of its own, never written "
          "over the one sent",
          again["file"] == "Second screener, title and abstract (2).xlsx" and again["records"] == 10
          and path.is_file(), str(again))

    # ── F. Where we differ, the outcomes, the differences workbook and a third reviewer
    apart = sift.listed(sift.load(run), sift.read_log(run), "ta", "apart")
    rec_view = two.view(run, on)["records"]
    check("119: Where we differ holds the records one took forward and the other rejected, and the record shows both "
          "decisions, reasons and notes side by side with the outcome, open at first",
          apart == sorted(drawn[8:10], key=lambda r: int(r[1:])) and rec_view[drawn[8]]["ta"]["differs"]
          and rec_view[drawn[8]]["ta"]["outcome"]["state"] == "open"
          and rec_view[drawn[8]]["ta"]["theirs"] == {"decision": "exclude", "reason": "E2", "note": "no ringers here",
                                                      "at": rec_view[drawn[8]]["ta"]["theirs"]["at"]}
          and not rec_view[drawn[6]]["ta"]["differs"], str(apart))
    import mcp_server
    srv = mcp_server.Server(str(scratch), app="sift")
    srv.receive(json.dumps({"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {"clientInfo": {"name": "claude-ai"}}}))
    by_mcp = srv.receive(json.dumps({"jsonrpc": "2.0", "id": 2, "method": "tools/call",
                                     "params": {"name": "sift_list", "arguments": {"folder": str(run), "round": "apart"}}}))["result"]
    check("119: MCP's sift_list takes the round apart, Where we differ, and lists the same records (13 October, evening)",
          by_mcp["isError"] is False and [r["rec_id"] for r in by_mcp["structuredContent"]["records"]] == apart,
          json.dumps(by_mcp)[:300])
    diff = two.make_differences(run, "ta", on, question=q)
    dpath = run / diff["file"]
    dwb = openpyxl.load_workbook(dpath)
    dws = dwb["Differences"]
    dhead = [c.value for c in dws[1]]
    dfills = [c.coordinate for ws in dwb.worksheets for row in ws.iter_rows() for c in row if c.fill is not None and c.fill.fill_type]
    ddv = [dv.formula1 for dv in dws.data_validations.dataValidation]
    check("119: the differences workbook holds the open differences, rec_id, Title, both decisions, reasons and notes, "
          "then Reply as a dropdown, Agree with you or Keep mine, and Reply note, the only cells that take typing, with "
          "no fill",
          diff["records"] == 2 and dhead == ["rec_id", "Title", "TW: decision", "TW: reason", "TW: note", "RM: decision",
                                              "RM: reason", "RM: note", "Reply", "Reply note"]
          and ddv == ['"Agree with you,Keep mine"'] and dws.protection.sheet and not dfills
          and sorted({c.column_letter for row in dws.iter_rows(min_row=2) for c in row if not c.protection.locked}) == ["I", "J"]
          and dws.cell(row=2, column=3).value == "Yes" and dws.cell(row=2, column=6).value == "No", str(dhead))
    first, second = apart
    replies = two.take_back(run, fill(dpath, {first: {"Reply": "Agree with you", "Reply note": "fair"},
                                              second: {"Reply": "Keep mine", "Reply note": "still no ringers"}},
                                      "Differences"), dpath.name, on)
    after = two.view(run, on)["records"]
    check("119: taken back, Agree with you settles the record on his decision and Keep mine leaves it open, each reply "
          "logged with its note",
          replies["kind"] == "differences" and replies["agreed"] == 1 and replies["keep"] == 1
          and after[first]["ta"]["outcome"] == {"state": "agreed", "decision": "include", "reason": "", "by": "reply"}
          and after[second]["ta"]["outcome"]["state"] == "open"
          and after[second]["ta"]["replies"][0]["reply"] == "keep" and after[second]["ta"]["replies"][0]["note"] == "still no ringers",
          str(after[first]["ta"]["outcome"]))
    not_third = refusal_of(lambda: two.settle_one(run, second, "ta", "decided", "exclude", on))
    not_apart = refusal_of(lambda: two.settle_one(run, drawn[6], "ta", "agreed", "exclude", on))
    two.settle_one(run, second, "ta", "third", settings=on)
    waiting = two.view(run, on)["records"][second]["ta"]["outcome"]["state"]
    ruled = two.settle_one(run, second, "ta", "decided", "exclude", on)
    last = sift.read_log(run)[-1]
    check("119: a difference goes to a third reviewer and takes that reviewer's decision when it comes, his own decision "
          "changing by one more decision of his, logged as after the third reviewer, and an outcome is refused on a "
          "record not sent or where the two did not differ",
          waiting == "third" and ruled["record"]["stages"]["ta"]["decision"] == "exclude"
          and last["act"] == "decide" and last["after"] == "third reviewer" and last["reason"] == "E1"
          and not_third == two.NOT_THIRD and not_apart == two.NOT_APART, str(last))
    two.settle_one(run, first, "ta", "open", settings=on)
    two.settle_one(run, first, "ta", "agreed", "exclude", on)
    moved = sift.read_log(run)[-1]
    by_hand = sift.decide(run, drawn[6], "ta", "include", second=on)
    marked_after = sift.read_log(run)[-1]
    check("119: Agreed with a decision unlike his changes his by his hand, logged as after discussion, and any decision "
          "of his on a drawn record whose second decision he can see is marked so too",
          moved["act"] == "decide" and moved["after"] == "discussion" and moved["decision"] == "exclude"
          and moved["reason"] == "E2" and by_hand["changed"] and marked_after.get("after") == "discussion", str(moved))

    # ── G. the counts and the PRISMA flow
    c = sift.counts(sift.load(run))
    rows = {(r[0], r[1]): r[2] for r in sift.count_rows(c)}
    flow = sift.prisma_source(c)
    check("119: the counts name the two screeners, the share, each draw's seed, the calibration records, the agreement "
          "and kappa before discussion, and the differences settled by discussion and by the third reviewer",
          rows.get(("title and abstract", "first screener")) == "TW" and rows.get(("title and abstract", "second screener")) == "RM"
          and rows.get(("title and abstract", "share drawn for the second screener (%)")) == 40
          and rows.get(("title and abstract", "calibration records, screened together")) == 5
          and rows.get(("title and abstract", "draw 1 seed")) == draw1["seed"]
          and rows.get(("title and abstract", "draw 2 seed")) == draw2["seed"]
          and rows.get(("title and abstract", "decided alike before discussion")) == 8
          and rows.get(("title and abstract", "kappa before discussion, going forward against reject")) == 0.545
          and rows.get(("title and abstract", "first screener include, second screener exclude")) == 2
          and rows.get(("title and abstract", "differences settled by discussion")) == 1
          and rows.get(("title and abstract", "differences decided by a third reviewer")) == 1
          and not any(k[0] == "full text" and "screener" in k[1] for k in rows), str([k for k in rows if k[0] == "title and abstract"][-12:]))
    check("119: the PRISMA flow names the two screeners in a box beside the stage's, the share, calibration, each draw's "
          "seed, the agreement and kappa before discussion and the differences settled",
          'twota["Screened by TW and RM<br/>A 40% share by both<br/>Calibration (n = 5)<br/>' in flow
          and f"Draw 1, seed {draw1['seed']} (n = 10)" in flow and "Alike before discussion 8 of 10 (80%)" in flow
          and "Kappa 0.55" in flow and "Settled by discussion (n = 1)" in flow and "By a third reviewer (n = 1)" in flow
          and "  screened -.- twota" in flow and "twoft" not in flow, flow[-600:])

    # ── H. full text: the draw waits for title and abstract, then the PDFs folder
    ft_on = dict(on, calibration=0, share=100)
    small = bells(base / "Small review" / "runs" / "2026-10-12", n=6)
    for i in range(1, 7):
        sift.decide(small, f"B{i:03d}", "ta", "include" if i <= 3 else "exclude", "" if i <= 3 else "E1")
    (small / "pdfs").mkdir()
    for rec in ("B001", "B003"):
        (small / "pdfs" / f"{rec}.pdf").write_bytes(b"%PDF-1.4 bells\n")
    wait_run = bells(base / "Wait review" / "runs" / "2026-10-12", n=3)
    waited = refusal_of(lambda: two.make_workbook(wait_run, "ft", ft_on))
    wait_view = two.view(wait_run, ft_on)["stages"]["ft"]
    ftbook = two.make_workbook(small, "ft", ft_on)
    ftwb = openpyxl.load_workbook(small / ftbook["file"])
    ftdv = [dv.formula1 for dv in ftwb["Records"].data_validations.dataValidation]
    check("119, updated 12 October (126): at full text the draw waits until every record is decided at title and "
          "abstract, Decision offers Include and Exclude, and the PDFs the run holds for the drawn records are copied into a folder beside the workbook "
          "named by rec_id, the folder said to zip and send",
          waited == two.FT_WAITS and wait_view["waits"] == two.FT_WAITS and wait_view["waits_calibration"] is False
          and ftbook["file"] == "Second screener, full text.xlsx" and ftbook["records"] == 3
          and ftbook["pdfs"] == "Second screener, full text PDFs" and ftbook["missing"] == 1
          and sorted(p.name for p in (small / ftbook["pdfs"]).iterdir()) == ["B001.pdf", "B003.pdf"]
          and ftdv == ['"Include,Exclude"', "sift!$D$1:$D$2"]
          and [ftwb["sift"].cell(row=i, column=4).value for i in (1, 2)] == ["F1 No full text", "F2 Not qualitative"], str(ftbook))

    # ── I. through the server: the settings kept in the app's own list, the side with every read and act
    kept = (server_mod.CONFIG_PATH, server_mod.ROOT_OVERRIDE, server_mod.STATE_MEMORY)
    cfg_file = base / "config.json"
    cfg_file.write_text(json.dumps({"projects": []}), encoding="utf-8")
    review = bells(base / "Server review", n=12)
    try:
        server_mod.CONFIG_PATH, server_mod.ROOT_OVERRIDE, server_mod.STATE_MEMORY = cfg_file, None, {"recent": []}
        rv = sift_routes.api_sift_review
        rv({"op": "open", "folder": str(review)})
        mark_tree = tree(review)
        saved = rv({"op": "second", "folder": str(review), "second": {"on": True, "first": "TW", "name": "RM", "share": 50,
                                                                         "calibration": 2, "kappa": 0.7}})
        untouched = tree(review) == mark_tree
        read = sift_routes.api_sift({"op": "read", "folder": str(review)})
        entry = sift_routes.kept_review(review.resolve())
        decided = sift_routes.api_sift({"op": "decide", "folder": str(review), "rec_id": "B001", "stage": "ta", "decision": "include"})
        sift_routes.api_sift({"op": "decide", "folder": str(review), "rec_id": "B002", "stage": "ta", "decision": "include"})
        book = sift_routes.api_sift({"op": "second", "act": "workbook", "folder": str(review), "stage": "ta"})
        bad = refusal_of(lambda: sift_routes.api_sift({"op": "second", "act": "take", "folder": str(review),
                                                      "data": base64.b64encode(b"nothing").decode(), "name": "x.xlsx"}))
        taken = sift_routes.api_sift({"op": "second", "act": "take", "folder": str(review), "name": book["file"],
                                     "data": base64.b64encode(fill(review / book["file"], {})).decode()})
        wrong_act = refusal_of(lambda: sift_routes.api_sift({"op": "second", "act": "nothing", "folder": str(review)}))
        rows_after = sift_routes.review_rows()
    finally:
        server_mod.CONFIG_PATH, server_mod.ROOT_OVERRIDE, server_mod.STATE_MEMORY = kept
    check("119: the settings are the project's, saved under Sift in Settings into its entry in the app's own list and "
          "kept through every opening, the review's view and its card carrying them, and nothing written into its "
          "folder by saving them",
          saved["review"]["second"] == {"on": True, "first": "TW", "name": "RM", "share": 50, "calibration": 2, "kappa": 0.7}
          and entry and entry.get("second", {}).get("share") == 50 and read["review"]["second"]["on"]
          and any(r.get("second", {}).get("name") == "RM" for r in rows_after) and untouched, str(entry))
    check("119: through the server a read and every act answer the side as `second`, a decision on a calibration record "
          "is marked so, a workbook is made beside the screening, one taken back is checked and a stranger refused, and "
          "an act it does not know is refused in one line",
          read["second"]["stages"]["ta"]["calibration"] == 2 and decided["second"]["stages"]["ta"]["calibration_left"] == 1
          and any(e.get("calibration") for e in sift.read_log(review) if e["rec_id"] == "B001")
          and book["records"] == 5 and (review / book["file"]).is_file() and book["second"]["stages"]["ta"]["drawn"] == 5
          and bad == two.NOT_OURS and taken["taken"] == 0 and taken["blank"] == 5 and "counts" in taken
          and wrong_act == "The act is draw, workbook, differences, take or outcome.", bad)

    # ── J. Start again, and the log read for his decisions alone
    plain = bells(base / "Plain review", n=4)
    sift.decide(plain, "B001", "ta", "include")
    sift.append(plain, {"n": 2, "at": "2026-10-12T10:00:00+01:00", "act": "second", "change": "decision", "rec_id": "B001",
                        "stage": "title and abstract", "decision": "exclude", "reason": "E1", "note": ""})
    held = sift.states(sift.read_log(plain))
    two.write_mirror(plain, two.two_of(plain, sift.load(plain)))
    had = (plain / two.MIRROR_NAME).read_text(encoding="utf-8")
    sift.reset(plain)
    check("119: a second screener's line never moves a decision of his, and Start again writes their file afresh from "
          "the log it begins",
          sift.state_of(sift.load(plain), held, "B001", "ta")["decision"] == "include" and "B001,exclude" in had
          and (plain / two.MIRROR_NAME).read_text(encoding="utf-8") == "stage,rec_id,decision,reason,note,draw\n")

    # ── K. the page: the settings, the card, the record, the round and the drop
    part = page.split('id="sfp-two"', 1)[1].split('id="sfp-pdfs"', 1)[0] if 'id="sfp-two"' in page else ""
    check("119: under Sift in Settings each project has its Second screener part: the switch, off on a new project, "
          "the two names, the share, Every record or a share in per cent, the calibration records and the kappa, saved "
          "with Save as `second` and kept in the app's own list",
          "A second screener for this project</label>" in part and 'for="sfp-two-first">Your name or initials</label>' in part
          and 'for="sfp-two-name">Their name or initials</label>' in part
          and '<option value="every">Every record</option><option value="share">A share</option>' in part
          and 'for="sfp-two-cal">Calibration records</label>' in part
          and 'for="sfp-two-kappa">Offer a further draw below a kappa of</label>' in part
          and "out.push({ op: 'second', folder: item.review, second: draft.second });" in fn(sset, "sfpSaves")
          and "sfpTwoDraw();" in fn(sset, "sfpOwnDraw") and "second: $('sfp-two').hidden ? null : sfpTwoRead()" in fn(sset, "sfpKeep")
          and "const SFP_TWO = { on: false, first: '', name: '', share: 100, calibration: 0, kappa: 0.6 };" in sset
          and "if (sent.op === 'second' && onScreen('sift')) SFA.twoTurned = true;" in fn(sset, "sfpSend"))
    card = page.split('id="sf-two"', 1)[1].split("</div>\n</div>", 1)[0] if 'id="sf-two"' in page else ""
    check("119: Second screener stands in Sift's title bar while the project has one or the log holds their side, and "
          "opens its card with the three workbook acts, the take back by a file chosen or a drop anywhere on the screen",
          'id="sf-two-btn"' in page and "Second screener</span>" in page
          and "$('sf-two-btn').hidden = !sfTwoOn();" in fn(sjs, "sfBar")
          and ">Take back a workbook</button>" in card and ">Make the differences workbook</button>" in card
          and ">Make the second screener's workbook</button>" in card and 'accept=".xlsx,' in card
          and "if (file && /\\.xlsx$/i.test(file.name || '')) sfTwoTakeFile(file);" in fn(sjs, "sfDrop")
          and "const book = sfXlsx(e);" in fn(sjs, "sfDrag")
          and "if (!$('sf-two').hidden) {" in fn(sjs, "sfKeyDown") and "$('sf-two').hidden = true;" in fn(sjs, "sfLeave"))
    check("119, updated 12 October (121): the record shows the calibration mark, both sides once he can see theirs, and the "
          "outcome's buttons, and Where we differ is a tick of the Decision filter while the second screener's side holds "
          "a difference, marked from the side",
          'id="sf-cal"' in page and ">Calibration</span>" in page and 'id="sf-two-rec"' in page
          and "{ value: SF_APART, label: 'Where we differ' }" in fn(sjs, "sfGroups")
          and "st.apart = !!(two[stage] || {}).differs;" in fn(sjs, "sfMark")
          and "btn('agreed', 'include', t('sift.two.agreed_as', { word: w.include }))" in fn(sjs, "sfTwoRecDraw")
          and "btn('third', '', 'To a third reviewer')" in fn(sjs, "sfTwoRecDraw")
          and "btn('decided', 'exclude', t('sift.two.third_as', { word: w.exclude }))" in fn(sjs, "sfTwoRecDraw")
          and "sfTwoRecDraw(r);" in fn(sjs, "sfDraw") and "if (data.second) SF.second = data.second;" in fn(sjs, "sfLand")
          and "!ts.waits_calibration" in fn(sjs, "sfTwoDraw") and "parts.length === 1 ? parts[0]" in fn(sjs, "sfTwoDraw"))
    if node:
        harness = support.i18n_js() + r"""
const esc = (s) => String(s ?? '').replace(/[&<>"']/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' })[c]);
const plural = (n, word) => `${n} ${word}${n === 1 ? '' : 's'}`;
const SF = { stage: 'ta', second: { name: 'RM' } };
""" + sift_words_js(sjs) + "\n"
        pick = lambda name: "function " + name + "(" + fn(sjs, name) + "\n}\n"
        consts = "\n".join(line for line in sjs.splitlines() if line.startswith(("const sfTwoThem", "const sfTwoKappa", "const sfTwoPc")))
        body = harness + consts + "\n" + pick("sfTwoTook") + pick("sfTwoTable") + r"""
const out = {};
out.took = [sfTwoTook({ kind: 'second', taken: 9, blank: 1, file: 'b.xlsx' }), sfTwoTook({ kind: 'second', taken: 0, blank: 0, file: 'b.xlsx' }),
  sfTwoTook({ kind: 'differences', taken: 2, agreed: 1, keep: 1, file: 'd.xlsx' }), sfTwoTook({ kind: 'differences', taken: 1, agreed: 0, keep: 1, file: 'd.xlsx' })];
out.kappa = [sfTwoKappa(0.545), sfTwoKappa(null), sfTwoPc(0.8)];
out.table = sfTwoTable({ include: { include: 4, maybe: 2, exclude: 2 }, maybe: {}, exclude: { exclude: 2 } });
SF.stage = 'ft';
out.ft = sfTwoTable({ include: { include: 1, exclude: 1 }, exclude: { exclude: 3 } });
console.log(JSON.stringify(out));
"""
        script = base / "two.js"
        script.write_text(body, encoding="utf-8")
        ran = subprocess.run([node, str(script)], capture_output=True, text=True, encoding="utf-8", timeout=60)
        o = json.loads(ran.stdout) if ran.returncode == 0 and ran.stdout.strip() else {}
        check("119: in node, what a returned workbook brought is said in one line, the kappa to two places or none, and "
              "the table his decisions by row against theirs by column, Maybe only at title and abstract",
              o.get("took") == ["Took in 9 decisions from b.xlsx. 1 left blank is still to screen.", "No new decision in b.xlsx.",
                                "Took in 2 replies from d.xlsx, 1 agreed and 1 kept.", "Took in 1 reply from d.xlsx, 0 agreed and 1 kept."]
              and o.get("kappa") == ["0.55", "None, as both put every record one way", "80%"]
              and "<caption>Yours by row, RM's by column</caption>" in o.get("table", "")
              and "<th scope=\"row\">Maybe</th>" in o.get("table", "") and "Maybe" not in o.get("ft", "x")
              and "<td>3</td>" in o.get("ft", ""), (ran.stderr or ran.stdout)[:400])
    else:
        skip("119: in node, the card's lines and table", "node is not installed")
