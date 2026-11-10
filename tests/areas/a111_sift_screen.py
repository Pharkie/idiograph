from __future__ import annotations

import csv
import json
import os
import re
import shutil

from workbook import WorkbookError

from . import support
from .support import check, sift_words_js, skip


@support.as_app("sift")
def test_sift_screen(scratch):
    print("\n111. Sift's screen reworked: the table first and a record opened from it, two bars at the top and one at the "
          "foot, the PRISMA flow a sidebar, the stages plain, decisions as pills, a number for each record, the year and "
          "star filters, one reason a record over the record, the grounds named, links and PDFs, open-access PDFs found "
          "against a stub, and the bench against a stub model")
    import http.server
    import subprocess
    import threading
    import urllib.parse
    import zlib
    import server as server_mod
    import sift_routes
    import sift
    import sift_ai
    import sift_oa
    import sift_search as ss

    page = support.page_text()
    app = support.text("family/static/shell.js", "apps/idiograph/static/distil.js")
    # Sift's parts of the shell, from app.js since the family codebase's third build (22 October 2026)
    sset = support.text("apps/sift/static/sift_settings.js")
    sjs = support.text("apps/sift/static/sift.js")
    # Sift's styles as its page loads them, the frame it shares with Trace first (tracestyle, 30 October 2026)
    scss = support.text("family/static/frame.css", "apps/sift/static/sift.css")
    fn = lambda src, name: src.split(f"function {name}(", 1)[1].split("\n}", 1)[0] if f"function {name}(" in src else ""
    node = shutil.which("node")
    screen = page.split('<section id="sift"', 1)[1].split("</section>", 1)[0]
    rail = screen.split('<div class="rail sf-rail">', 1)[1].split('<div class="sf-main"', 1)[0]
    # Sift's own settings, under Sift in Settings since its card went (9 October)
    card = page.split('id="pane-sift"', 1)[1].split("</section>", 1)[0] if 'id="pane-sift"' in page else ""

    # ── A. an invented review on repair cafés, its rec_ids out of order in the CSV
    base = scratch / "sift-screen-111"
    shutil.rmtree(base, ignore_errors=True)
    folder = base / "Repair cafes"
    folder.mkdir(parents=True)
    head = ["rec_id", "title", "authors", "year", "journal", "doi", "url", "sources", "abstract",
            "proposed_decision", "proposed_reason", "grounds"]
    rows = [
        ["Q10", "Mending kettles on a Saturday", "Solder, A.", "2019", "Invented Repairs", "10.5555/fix.10",
         "https://example.org/fix/10", "OpenAlex", "Nine volunteers fixed kettles for neighbours. They spoke of pride.",
         "include", "", "Nine volunteers fixed kettles for neighbours."],
        ["Q2", "A survey of sewing circles", "Thread, B.", "2021", "Invented Repairs", "10.5555/fix.2", "not a link",
         "OpenAlex", "A survey with no interviews at all.", "exclude", "E2", "A survey with no interviews at all."],
        ["Q1", "Bicycle repair as company", "Spoke, C.", "2017", "Invented Repairs", "", "https://example.org/fix/1",
         "OpenAlex", "Seven riders described repairing bicycles together.", "", "", ""],
        ["Q3", "Lamps and long evenings", "Wick, D.", "2021", "Invented Repairs", "10.5555/fix.3", "", "OpenAlex",
         "Twelve people repaired lamps.", "", "", ""],
        ["Q4", "Radios that talk back", "Valve, E.", "2023", "Invented Repairs", "10.5555/fix.4", "", "OpenAlex",
         "An essay on radios.", "", "", ""],
    ]
    with open(folder / sift.CSV_NAME, "w", encoding="utf-8", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(head)
        w.writerows(rows)
    with open(folder / sift.REASONS_NAME, "w", encoding="utf-8", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["stage", "code", "meaning"])
        w.writerows([["ta", f"E{k}", m] for k, m in enumerate(
            ("Not about repair", "No interviews", "Not empirical", "Not in English", "Children only", "Duplicate"), 1)])

    def pdf_with(text: str, cmap: bytes | None = None, hexed: str = "") -> bytes:
        """A one-page PDF of invented words, a simple font's string or two-byte codes through a ToUnicode map"""
        content = (f"BT /F1 14 Tf 72 720 Td [{hexed}] TJ ET" if hexed else f"BT /F1 14 Tf 72 720 Td ({text}) Tj ET").encode()
        data = zlib.compress(content)
        objs = [b"<< /Type /Catalog /Pages 2 0 R >>", b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
                b"<< /Type /Page /Parent 2 0 R /Resources << /Font << /F1 4 0 R >> >> /Contents 5 0 R >>",
                b"<< /Type /Font /Subtype /Type0 /BaseFont /Invented" + (b" /ToUnicode 6 0 R" if cmap else b"") + b" >>",
                f"<< /Length {len(data)} /Filter /FlateDecode >>\nstream\n".encode() + data + b"\nendstream"]
        if cmap:
            packed = zlib.compress(cmap)
            objs.append(f"<< /Length {len(packed)} /Filter /FlateDecode >>\nstream\n".encode() + packed + b"\nendstream")
        body = b"".join(f"{i} 0 obj\n".encode() + o + b"\nendobj\n" for i, o in enumerate(objs, 1))
        return b"%PDF-1.4\n" + body + b"trailer\n<< /Root 1 0 R >>\n%%EOF\n"

    (folder / "pdfs").mkdir()
    q4_pdf = pdf_with("Radios that talk back")
    (folder / "pdfs" / "Q4.pdf").write_bytes(q4_pdf)

    # ── B. a number for each record, fixed once given
    first = {r["rec_id"]: r["n"] for r in sift.screen(folder)["records"]}
    check("111: each record's number runs 1 up in rec_id order, Q1 before Q2 before Q10, whatever the CSV's order, and "
          "reading writes nothing",
          first == {"Q1": 1, "Q2": 2, "Q3": 3, "Q4": 4, "Q10": 5} and not (folder / sift.SETTINGS_NAME).exists(), str(first))
    wrote = sift.keep_numbers(folder)
    held = json.loads((folder / sift.SETTINGS_NAME).read_text(encoding="utf-8")).get("numbers")
    again = sift.keep_numbers(folder)
    sift.add_records(folder, [{"rec_id": "Q0", "title": "Clocks in the kitchen", "abstract": "Six menders of clocks."}])
    after = {r["rec_id"]: r["n"] for r in sift.screen(folder)["records"]}
    sift.keep_numbers(folder)
    sift_ai.save_settings(folder, False, "")
    sift.save_view(folder, columns=[{"key": "notes", "shown": True}])
    kept = json.loads((folder / sift.SETTINGS_NAME).read_text(encoding="utf-8")).get("numbers")
    check("111: once given the numbers are kept in sift.json, a record added later that sorts first takes the next, the rest "
          "stay as they were, and the AI settings and the table's columns keep them when they write",
          wrote is True and held == first and again is False and after == dict(first, Q0=6) and kept == after, str(after))
    check("111: the reading tools give the number as n",
          {r["rec_id"]: r["n"] for r in sift.rows_of_round(folder, "ta", "all")["records"]} == after
          and sift.history(folder, "Q3")["record"]["n"] == 3)

    # ── C. one reason a record
    older = {"n": sift.next_n(folder), "at": "2026-10-01T10:00:00+01:00", "act": "decide", "rec_id": "Q2",
             "stage": "title and abstract", "decision": "exclude", "reason": "E2; E5", "note": "",
             "proposal": {"decision": "exclude", "reason": "E2", "source": "csv"},
             "was": {"decision": "", "reason": "", "note": ""}, "tool": "older"}
    sift.append(folder, older)
    sc = sift.load(folder)
    held = sift.states(sift.read_log(folder))
    try:
        sift.decide(folder, "Q3", "ta", "exclude", "E1; E2")
        two = "decided"
    except WorkbookError as exc:
        two = str(exc)
    check("111: one reason a record: a reject whose older line names two keeps its first, where it stands and in the counts, "
          "and a decision naming two is refused",
          sift.state_of(sc, held, "Q2", "ta")["reason"] == "E2" and sift.counts(sc)["stages"]["ta"]["reasons"] == {"E2": 1}
          and sift.first_reason("E3, E4") == "E3" and sift.first_reason(["", "E6", "E1"]) == "E6"
          and sift.first_reason("E1|E2") == "E1" and sift.first_reason("") == "" and two == "E1; E2 is not a reason code at title and abstract.",
          two)

    # ── D. the record's links
    v10, v2 = sift.record_view(sc, held, "Q10"), sift.record_view(sc, held, "Q2")
    check("111: a record's web address is a link when its url column holds one address, and stays among the other columns "
          "as text when it does not",
          v10["url"] == "https://example.org/fix/10" and "url" not in [k for k, _ in v10["more"]]
          and v2["url"] == "" and ["url", "not a link"] in v2["more"] and v10["link"] == "https://doi.org/10.5555/fix.10")

    # ── E. a PDF's first page, read with the standard library
    cmap = (b"1 begincodespacerange <0000> <FFFF> endcodespacerange\n2 beginbfchar <0003> <0020> <0011> <002E> endbfchar\n"
            b"1 beginbfrange <0024> <003D> <0041> endbfrange\n1 beginbfrange <0044> <005D> <0061> endbfrange")
    enc = lambda s: "".join("0003" if ch == " " else f"{0x24 + ord(ch) - 65:04X}" if ch.isupper() else f"{0x44 + ord(ch) - 97:04X}"
                            for ch in s)
    simple = pdf_with("Mending kettles on a Saturday")
    hexed = pdf_with("", cmap, f"<{enc('Lamps and')}> -300 <{enc('long evenings')}>")
    form = pdf_with("Interlibrary loan request form")
    check("111: a PDF's first page read with the standard library, a simple font's strings and two-byte codes through the "
          "font's ToUnicode map, a wide gap a space, and nothing from a page that is not a PDF",
          sift_oa.first_page_text(simple) == "Mending kettles on a Saturday"
          and sift_oa.first_page_text(hexed) == "Lamps and long evenings" and sift_oa.first_page_text(b"<html>Sign in</html>") == "",
          sift_oa.first_page_text(hexed))
    check("111: a first page carries the title whole, or most of its longer words when a break or a ligature parts it, and a "
          "library's form in a paper's place does not",
          sift_oa.carries_title("MENDING KETTLES on a Satur- day", "Mending kettles on a Saturday")
          and sift_oa.carries_title("radios that do talk back", "Radios that talk back")
          and not sift_oa.carries_title(sift_oa.first_page_text(form), "Mending kettles on a Saturday")
          and not sift_oa.carries_title("", "Anything"))

    # ── F. Find open-access PDFs against a stub of its own, in the process
    asked = []

    def answer(url):
        """OpenAlex, Unpaywall and the hosts their copies sit on, every answer invented"""
        asked.append(url)
        p = urllib.parse.urlparse(url)
        if p.netloc == "api.openalex.org" and "/works/doi:" in p.path:
            n = p.path.rsplit(".", 1)[-1]
            work = {"doi": f"https://doi.org/10.5555/fix.{n}", "has_content": {"pdf": n == "10"},
                    "content_urls": {"pdf": f"https://content.openalex.org/works/W{n}.pdf"},
                    "best_oa_location": {"pdf_url": f"https://repo.example.org/{n}.pdf" if n in ("2", "3") else None},
                    "locations": [{"pdf_url": "https://pmc.ncbi.nlm.nih.gov/articles/PMC1/pdf"}]}
            return 200, "application/json", json.dumps(work).encode()
        if p.netloc == "api.openalex.org" and p.path == "/works":
            q = urllib.parse.parse_qs(p.query)
            hit = "Bicycle repair as company" in q.get("search", [""])[0] and q.get("filter") == ["publication_year:2017"]
            res = [{"title": "Bicycle repair as company", "publication_year": 2017, "doi": None,
                    "best_oa_location": {"pdf_url": "https://repo.example.org/1.pdf"}}] if hit else []
            return 200, "application/json", json.dumps({"results": res}).encode()
        if p.netloc == "api.unpaywall.org":
            return 200, "application/json", json.dumps({"best_oa_location": None, "oa_locations": []}).encode()
        if p.netloc == "content.openalex.org":
            return 200, "application/pdf", simple
        if p.netloc == "repo.example.org":
            n = p.path.strip("/").split(".")[0]
            if n == "2":
                return 200, "text/html", b"<html><body>Sign in</body></html>"
            if n == "3":
                return 200, "application/pdf", form
            if n == "1":
                return 200, "application/pdf", pdf_with("Bicycle repair as company")
        return 404, "", b""

    # only the records that passed title and abstract are looked for (118), so those the finder is tried
    # on pass it first, Q2 rejected there and so left out of the plan, and asked about by hand below
    for rec in ("Q10", "Q1", "Q3", "Q0"):
        sift.decide(folder, rec, "ta", "maybe" if rec == "Q0" else "include")
    plan = sift_oa.plan(folder)
    found = {rec: sift_oa.find(folder, rec, "reader@example.org", fetch=answer, key=None) for rec in plan["ids"] + ["Q2"]}
    asked_before = len(asked)
    passed = sift_oa.find(folder, "Q4", "reader@example.org", fetch=answer, key=None)
    saved = sorted(rec for rec, got in found.items() if got["saved"])
    check("111, updated 12 October (118): the plan names every record that passed title and abstract with no PDF, one "
          "rejected there left out, before anything is asked",
          plan == {"ids": ["Q10", "Q1", "Q3", "Q0"], "records": 6, "passed": 4, "have": 0}, str(plan))
    check("111: a PDF whose first page carries the title is saved as pdfs/<rec_id>.pdf, OpenAlex's own copy first, and a "
          "record with no DOI is matched in OpenAlex by its exact title and year",
          saved == ["Q1", "Q10"] and found["Q10"]["where"] == "OpenAlex"
          and (folder / "pdfs" / "Q10.pdf").read_bytes() == simple
          and (folder / "pdfs" / "Q1.pdf").read_bytes().startswith(b"%PDF-")
          and "record" in found["Q10"]["answer"] and found["Q10"]["answer"]["record"]["pdf"] is True, str(found))
    check("111: an answer that is not a PDF is refused, a PDF without the record's title is refused, and a record with no DOI "
          "that OpenAlex does not hold is said so, nothing written for any of them",
          found["Q2"]["said"] == "No copy listed answered with a PDF." and not (folder / "pdfs" / "Q2.pdf").exists()
          and found["Q3"]["said"] == "No PDF found carries the record's title on its first page."
          and not (folder / "pdfs" / "Q3.pdf").exists()
          and found["Q0"]["said"] == "No DOI, and OpenAlex holds no work of that title and year.", str(found))
    check("111: a PDF already there is kept, passed over before anything is asked, and pmc.ncbi.nlm.nih.gov, which refuses "
          "scripts, is never asked, and Unpaywall is asked with his email",
          passed["skipped"] is True and len(asked) == asked_before and (folder / "pdfs" / "Q4.pdf").read_bytes() == q4_pdf
          and not any("pmc.ncbi.nlm.nih.gov" in u for u in asked)
          and any(u.startswith("https://api.unpaywall.org/v2/10.5555/fix.10?email=reader%40example.org") for u in asked))

    def racing(url):
        """another fetcher keeps the record's PDF while this one downloads its own"""
        got = answer(url)
        if got[1] == "application/pdf":
            (folder / "pdfs" / "Q3.pdf").write_bytes(q4_pdf)
            return 200, "application/pdf", pdf_with("Lamps and long evenings")
        return got

    raced = sift_oa.find(folder, "Q3", "reader@example.org", fetch=racing, key=None)
    check("111: a PDF another fetcher keeps while this one downloads is never written over, and the record is said skipped",
          raced["skipped"] is True and raced["saved"] is False and (folder / "pdfs" / "Q3.pdf").read_bytes() == q4_pdf, str(raced))
    (folder / "pdfs" / "Q3.pdf").unlink()

    # ── G. the server's routes, the finder through the stub hook on loopback, the email, and the bench on a stub model
    class Stub(http.server.BaseHTTPRequestHandler):
        def log_message(self, *a):
            pass

        def do_GET(self):
            host, _, rest = self.path.lstrip("/").partition("/")
            seen.append(self.path)
            code, ctype, body = answer(f"https://{host}/{rest}")
            self.send_response(code)
            self.send_header("Content-Type", ctype or "text/plain")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def do_POST(self):
            size = int(self.headers.get("Content-Length") or 0)
            sent = json.loads(self.rfile.read(size) or b"{}")
            calls.append(sent)
            said = {"decision": "exclude", "reason": "E2", "grounds": "Nine volunteers fixed kettles for neighbours."}
            out = json.dumps({"message": {"content": json.dumps(said)}, "done": True, "done_reason": "stop"}).encode()
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(out)))
            self.end_headers()
            self.wfile.write(out)

    seen, calls = [], []
    stub = http.server.ThreadingHTTPServer(("127.0.0.1", 0), Stub)
    threading.Thread(target=stub.serve_forever, kwargs={"poll_interval": 0.05}, daemon=True).start()
    stub_url = f"http://127.0.0.1:{stub.server_address[1]}"
    cfg_file = base / "config.json"
    cfg_file.write_text(json.dumps({"interviewer": "Adam", "ai_suggest": True, "ai_provider": "local", "local_url": stub_url,
                                    "local_model": "stub", "sift_email": ""}), encoding="utf-8")
    roots = base / "no-cases"
    roots.mkdir()
    kept_state = (server_mod.CONFIG_PATH, server_mod.ROOT_OVERRIDE, server_mod.STATE_MEMORY, ss.RUNNER,
                  os.environ.pop(ss.STUB_ENV, None))

    def refusal(body) -> str:
        try:
            got = sift_routes.api_sift(body)
        except (WorkbookError, server_mod.OutsideRoot) as exc:
            return str(exc)
        return got.get("error", "") if isinstance(got, dict) else ""

    try:
        server_mod.CONFIG_PATH, server_mod.ROOT_OVERRIDE, server_mod.STATE_MEMORY = cfg_file, str(roots), {"recent": []}
        ss.RUNNER = lambda argv, **_: (_ for _ in ()).throw(AssertionError("the keychain was asked"))
        sift_routes.api_sift_review({"op": "open", "folder": str(folder)})
        read = sift_routes.api_sift({"op": "read", "folder": str(folder)})
        no_email = refusal({"op": "oa_find", "folder": str(folder), "rec_id": "Q3"})
        bad_email = refusal({"op": "email", "folder": str(folder), "email": "not an email"})
        good = sift_routes.api_sift({"op": "email", "folder": str(folder), "email": " reader@example.org "})
        stored = json.loads(cfg_file.read_text(encoding="utf-8"))
        check("111: the screen reads each record's number and the email, Find open-access PDFs asks for the email first, and "
              "the email is saved to config.json, every other setting kept, one that is not an address refused",
              read["email"] == "" and {r["rec_id"]: r["n"] for r in read["records"]} == after
              and no_email == sift_oa.NO_EMAIL and bad_email == "That is not an email address."
              and good == {"email": "reader@example.org"} and stored["sift_email"] == "reader@example.org"
              and stored["local_model"] == "stub" and stored["ai_provider"] == "local", no_email)
        os.environ[ss.STUB_ENV] = "http://192.0.2.1:9"
        far = sift_oa.stubbed("https://api.openalex.org/works/doi:10.5555/fix.3?select=id")
        os.environ[ss.STUB_ENV] = stub_url
        near = sift_oa.stubbed("https://api.openalex.org/works/doi:10.5555/fix.3?select=id")
        oa_plan = sift_routes.api_sift({"op": "oa_plan", "folder": str(folder)})
        q3 = dict(sift_routes.api_sift({"op": "oa_find", "folder": str(folder), "rec_id": "Q3"}))
        answer_q3 = sift_oa.find
        sift_oa.find = lambda *a, **k: dict(answer_q3(*a, **dict(k, fetch=lambda u: (200, "application/pdf",
                                                                                      pdf_with("Lamps and long evenings"))
                                                                  if "repo.example.org/3" in u else answer(u))))
        try:
            q3_found = sift_routes.api_sift({"op": "oa_find", "folder": str(folder), "rec_id": "Q3"})
        finally:
            sift_oa.find = answer_q3
        check("111: the stub hook sends every request to a loopback stub alone, the host at the head of the path, and an "
              "address that is not loopback is left as it is",
              far == "https://api.openalex.org/works/doi:10.5555/fix.3?select=id"
              and near == f"{stub_url}/api.openalex.org/works/doi:10.5555/fix.3?select=id", near)
        check("111, updated 12 October (118): through the server and the stub on loopback, the plan the records that passed "
              "title and abstract with no PDF, OpenAlex asked with the stand-in key a smoke run holds, and a PDF without "
              "the title refused there too, then one with it kept with the record and the flow, never the keychain asked",
              oa_plan["ids"] == ["Q3", "Q0"] and q3["saved"] is False
              and q3["said"] == "No PDF found carries the record's title on its first page."
              and any(s.startswith("/api.openalex.org/works/doi:10.5555/fix.3?api_key=stub-openalex_api_key") for s in seen)
              and not any("api_key" in s for s in seen if s.startswith(("/api.unpaywall.org", "/repo.example.org")))
              and q3_found["saved"] is True and q3_found["record"]["pdf"] is True and "prisma" in q3_found
              and (folder / "pdfs" / "Q3.pdf").read_bytes().startswith(b"%PDF-"), str(seen[-6:]))
        os.environ.pop(ss.STUB_ENV, None)
        files = lambda: {name: (folder / name).read_bytes() for name in (sift.CSV_NAME, sift.LOG_NAME, sift.SETTINGS_NAME)}
        before = files()
        tried = sift_routes.api_sift({"op": "try", "folder": str(folder), "rec_id": "Q10", "stage": "ta",
                                     "prompt": "Judge at {stage} with {codes}. Bench words of mine."})
        check("111: the bench sends the one record picked to the model, here a stub, with the prompt as the box holds it, "
              "unsaved, while the screening's own AI switch is off, and answers what came back with the model and the time",
              len(calls) == 1 and "Bench words of mine." in calls[0]["messages"][0]["content"]
              and "title and abstract" in calls[0]["messages"][0]["content"]
              and "Mending kettles on a Saturday" in calls[0]["messages"][-1]["content"]
              and (tried["decision"], tried["reason"], tried["found"], tried["n"]) == ("exclude", "E2", True, 5)
              and tried["model_name"] == "stub on this machine" and "seconds" in tried
              and sift_ai.settings(folder)["ai_proposals"] is False, str(tried))
        check("111: and the bench writes nothing, the CSV, the log and sift.json as they were",
              files() == before and "ai_proposed_decision" not in sift.load(folder).header)
        cfg_file.write_text(json.dumps(dict(stored, ai_suggest=False)), encoding="utf-8")
        off = refusal({"op": "try", "folder": str(folder), "rec_id": "Q10", "stage": "ta", "prompt": "x"})
        check("111: with the app's AI switch off the bench is refused and nothing is asked",
              off == sift_ai.OFF and len(calls) == 1, off)
        cfg_file.write_text(json.dumps(stored), encoding="utf-8")
        pdf_saved = sift_routes.api_sift({"op": "pdf", "folder": str(folder), "rec_id": "Q2",
                                         "data": __import__("base64").b64encode(pdf_with("A survey of sewing circles")).decode()})
        check("111: a PDF chosen with Add PDF goes through the pdf op that a dropped one always has, into pdfs/<rec_id>.pdf",
              pdf_saved["saved"] is True and (folder / "pdfs" / "Q2.pdf").exists()
              and "op: 'pdf', folder: SF.folder, rec_id: r.rec_id, data, replace" in fn(sjs, "sfDropPdf")
              and "if (file) sfDropPdf(file);" in fn(sjs, "sfBoot")
              and """$('sf-links').addEventListener('click', (e) => { if (e.target.closest('[data-act="add-pdf"]')) sfPdfChoose(); });""" in fn(sjs, "sfBoot"))
    finally:
        (server_mod.CONFIG_PATH, server_mod.ROOT_OVERRIDE, server_mod.STATE_MEMORY, ss.RUNNER, held_env) = kept_state
        os.environ.pop(ss.STUB_ENV, None)
        if held_env is not None:
            os.environ[ss.STUB_ENV] = held_env
        stub.shutdown()
        stub.server_close()

    # ── H. the page: the table first, the bars, the sidebar, the stages
    down = fn(sjs, "sfKeyDown")
    check("111, updated 12 October (122) and 6 November 2026 (330, the path's name its project's menu): a click or Enter "
          "on a row opens that record, and its way back, Esc or the "
          "browser's Back returns to the table",
          "sfOpenRecord(true);" in fn(sjs, "sfTvBoot")
          and "if (key === 'Enter') { e.preventDefault(); sfOpenRecord(); return; }" in down
          and "if (!SF.picking && SF.view === 'record' && key === 'Escape') { e.preventDefault(); sfToTable(); return; }" in down
          and "bandMenuWire('sf-name', () => siftBandMenu());" in fn(sjs, "sfBoot")
          and "['t', 'p', 'ArrowLeft', 'ArrowRight'].includes(key)" in down and "key === 'ArrowLeft'" in down)
    view_fn = fn(sjs, "sfSetView")
    check("111: the way back keeps the table's filters, sort and row: the view changes and nothing else, the scroll put back "
          "and the chosen row brought into view",
          all(w not in view_fn for w in ("SF.filters", "SF.sort", "sfApply", "sfRound", "SF.at"))
          and "$('sf-tv-box').scrollTop = SF.tvScroll;" in view_fn and "SF.tvReveal = true;" in view_fn)

    # ── I. pills, numbers, filters and links in node
    block = sjs.split("/* ── the table's rows: its columns, sort and filter, worked out with no page ── */", 1)[-1].split(
        "/* ── the table, drawn ── */", 1)[0]
    block = support.table_js() + "\n" + block
    lead = app[app.index("const esc = "):app.index("// a line from the server with a command in backticks")]
    view = sift.screen(folder)
    if node:
        parts = [block, lead, sift_words_js(sjs),
                 "function sfMeaning(code) { return code === 'E2' ? 'No interviews' : ''; }",
                 "const SF = " + json.dumps({"stage": "ta", "filters": {}, "table": view["table"], "records": view["records"],
                                             "counts": {"stages": {"ft": {"records": 0}}}}) + ";",
                 "SF.facetsMore = new Set();", "SF.facetsFind = {};"]
        parts += [f"function {name}(" + fn(sjs, name) + "\n}" for name in (
            "sfPillHtml", "sfLinked", "sfStars", "sfTvCell", "sfRangeEnds", "sfBarsHtml", "sfRangeHtml")]
        parts.append("const sfFtEmpty = " + sjs.split("const sfFtEmpty = ", 1)[1].split(";\n", 1)[0] + ";")
        probe = scratch / "sift-screen-111.js"
        probe.write_text("\n".join(parts) + r"""
const byId = new Map(SF.records.map((r) => [r.rec_id, r]));
const ids = SF.records.map((r) => r.rec_id);
const cols = sfAllCols();
const col = (k) => cols.find((c) => c.key === k);
const kept = (filters) => tbFilterRows(ids, byId, filters, cols, sfRead('ta'));
const nOf = (list) => list.map((id) => byId.get(id).n);
const titled = tbSortRows(ids, byId, [{ key: 'title', dir: 'asc' }], cols, sfRead('ta'));
const groups = sfGroups(SF.records, SF.records, cols, 'ta', [], {});
const counts = tbFacetCounts(SF.records, groups, {}, sfRead('ta'));
const bars = sfRangeBars(SF.records, groups, {}, 'ta');
SF.stage = 'ft';
const ftEmpty = sfFtEmpty();
SF.stage = 'ta';
console.log(JSON.stringify({
  pills: [sfPillHtml('include'), sfPillHtml('maybe'), sfPillHtml('exclude', 'E2'), sfPillHtml('')],
  first: cols[0].key,
  titled: titled.map((id) => [id, byId.get(id).n]),
  filteredN: nOf(tbSortRows(kept({ year: { from: 2019, to: 2021 } }), byId, [{ key: 'year', dir: 'desc' }], cols, sfRead('ta'))),
  byNumber: [kept({ n: '2' }).length, kept({ n: ['2'] }).length, groups.some((g) => g.key === 'n'),
    Object.keys(sfTicksRead({ n: '1-3' }, groups)).length],
  numberSorted: nOf(tbSortRows(ids, byId, [{ key: 'n', dir: 'desc' }], cols, sfRead('ta'))),
  idSorted: tbSortRows(ids, byId, [{ key: 'rec_id', dir: 'desc' }], cols, sfRead('ta')),
  cell: sfTvCell(byId.get('Q10'), col('rec_id')),
  years: ['year', 'rating'].map((k) => groups.find((g) => g.key === k)).map((g) => [g.low, g.high, g.choices.map((c) => c.value)]),
  year: sfRangeHtml(groups.find((g) => g.key === 'year'), counts.year, 0, bars.year),
  rating: sfRangeHtml(groups.find((g) => g.key === 'rating'), counts.rating, 1, bars.rating),
  unrated: kept({ rating: { from: null, to: null, none: true } }).length,
  rated: kept({ rating: { from: 1, to: null } }).length,
  link: [sfLinked('https://example.org/fix/10'), sfLinked('not <a> link'), sfLinked('javascript:alert(1)')],
  ftEmpty,
}));
""", encoding="utf-8")
        ran = subprocess.run([node, str(probe)], capture_output=True, text=True, encoding="utf-8", timeout=60)
        out = json.loads(ran.stdout) if ran.returncode == 0 and ran.stdout.strip() else {}
        check("111, updated 13 October (127): in node, the ID is the first column in place of the number, sorting in natural "
              "order, Q10 after Q4, the number no column to sort by, and each record keeps its own under a sort and a filter",
              out.get("first") == "rec_id"
              and out.get("titled") == [["Q2", 2], ["Q1", 1], ["Q0", 6], ["Q3", 3], ["Q10", 5], ["Q4", 4]]
              and out.get("filteredN") == [2, 3, 5] and out.get("numberSorted") == [5, 2, 1, 3, 4, 6]
              and out.get("idSorted") == ["Q10", "Q4", "Q3", "Q2", "Q1", "Q0"]
              and out.get("cell") == '<td class="mono sf-c-id">Q10</td>', json.dumps(out)[:300])
        check("111, 12 October: in node, the number is no longer searched, the browser's find finding it: no group of the "
              "filters names it and a search held from before is let go, every record shown",
              out.get("byNumber") == [6, 6, False, 0], str(out.get("byNumber")))
        year, rating = out.get("year", ""), out.get("rating", "")
        check("111, updated 12 October (121): in node, Year a slider from the earliest year the records carry to the latest "
              "with No year under it, My rating one from one star to five with Not rated under it, a record with no stars "
              "never at nought, each with its two handles and two boxes, and no list to pick from",
              out.get("years") == [[2017, 2023, ["|none"]], [1, 5, ["|none"]]]
              and year.count('type="range"') == 2 and year.count('type="number"') == 2 and year.count('type="checkbox"') == 1
              and ">No year<" in year and rating.count('type="range"') == 2 and rating.count('type="checkbox"') == 1
              and ">Not rated<" in rating and '<span class="sf-runit">stars</span>' in rating
              and "<select" not in year + rating and 'type="search"' not in year + rating
              and out.get("unrated") == 6 and out.get("rated") == 0, year[:300])
        check("111: in node, a web address is a link that opens a new tab, and anything else stays text, a script address "
              "never a link",
              out.get("link") == ['<a href="https://example.org/fix/10" target="_blank" rel="noopener noreferrer">https://example.org/fix/10</a>',
                                  "not &lt;a&gt; link", "javascript:alert(1)"]
              and out.get("ftEmpty") is True, str(out.get("link")))
    else:
        skip("111: pills, numbers, filters and links in node", "no node on this machine")

    # ── J. the reasons, the grounds, the links, the PDFs
    why = page.split('<div class="overlay sf-why" id="sf-why"', 1)[1].split("</div>\n</div>", 1)[0]
    check("111: the reasons are a short list over the record or the table, one reason a record, numbered, taken by a press "
          "or a number key, Esc or a press beside it cancelling, and the top bar of reasons is gone",
          'id="sf-reasons" role="radiogroup"' in why and "sf-tv-reasons" not in page + sjs and 'id="sf-reasons"' not in screen
          # numbered from 1 past No reason, 0, at title and abstract since 12 October, later (124)
          and "$('sf-why').hidden = !SF.picking;" in fn(sjs, "sfReasonsDraw") and "${i - off < 9 ? i - off + 1 : ''}" in fn(sjs, "sfReasonsDraw")
          and "sfDecide('exclude', codes[Number(key) - 1].code, true)" in down
          and "if (key === 'Escape' || sfKeyDecision(key, SF.stage) === 'exclude') { e.preventDefault(); sfPicking(false); return; }" in down
          and "if (e.target === $('sf-why')) sfPicking(false);" in fn(sjs, "sfBoot") and ".sf-why-card { width: min(26em, 100%);" in scss)
    run = fn(sjs, "sfOaRun")
    check("111: Find open-access PDFs sits under Sift in Settings outside the AI switch, for the project chosen there, asks "
          "the email once, then each record with no PDF in turn, and says the count at the end",
          'id="sf-oa-go"' in card and "data-ai" not in card.split('<div id="sfa-block" data-ai-set>', 1)[0]
          and "const folder = sfaFolder() || SF.folder;" in run
          and 'id="sf-settings" type="button" title="Sift\'s settings" aria-label="Sift\'s settings">' in rail
          and run.index("op: 'oa_plan'") < run.index("op: 'oa_find'") and "'sift.oa.found', { found, of }" in run
          and "'Unpaywall asks for your email first.'" in run and "if (!(await sfEmailSave())) return;" in run
          and "op: 'email'" in fn(sjs, "sfEmailSave") and "if (SF.oa) SF.oa.stop = true;" in fn(sjs, "sfLeave"))
    bench = fn(sjs, "sfBenchTry")
    check("111: the bench stands under the AI proposals in Settings, Sift, its record picked from the project chosen there, its "
          "cost said first, and Try, with the sparkles, sends the prompt as the box holds it and writes nothing",
          'id="sf-bench-rec"' in card.split('<div id="sfa-block" data-ai-set>', 1)[-1]
          and 'id="sf-bench-try"' in card.split('<div id="sfa-block" data-ai-set>', 1)[-1]
          and "$('sf-bench-try').insertAdjacentHTML('afterbegin', TB_SPARKS);" in fn(sjs, "sfBoot")
          and "'sift.bench.line'" in fn(sjs, "sfBenchCost")
          and "op: 'try', folder: b.folder, rec_id: rec, stage: b.stage," in bench and "prompt: $('sfa-prompt').value" in bench
          and "'settings'" not in bench and "'propose'" not in bench and "sfBenchFill(folder, h.model);" in fn(sset, "sfaShow"))
