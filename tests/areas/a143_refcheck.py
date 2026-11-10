from __future__ import annotations

import csv
import json
import re
import shutil
from pathlib import Path

from . import support
from .support import check, refusal_of, skip


@support.as_app("trace")
def test_refcheck(scratch):
    print("\n143. Check references, 14 October, Adam's words, in Trace since 15 October: a manuscript's references "
          "in a table like Sift's, each claim judged by him against its reference, Supports, Question or Doesn't "
          "support, a citation with no reference and a reference never cited listed as such, the PDF found by DOI, "
          "the AI finding passages it must show in the PDF's own words, a judgement never set by the AI or an agent, "
          "and the document never written. Since the test review of 18 October the screen's markup, styles and words are "
          "review shots, and what is read, judged, logged, found, served and never written stays")
    import argparse
    import base64
    import hashlib
    import ntpath
    from datetime import datetime
    import subprocess
    import textwrap
    import zipfile as zf
    import zlib as zl
    import ai_suggest as ai_mod
    import cli as cli_mod
    import convert
    import mcp_server
    import sift
    import sift_oa
    import trace_claims as refs
    import server as server_mod
    import sift_routes
    import trace_routes

    read = lambda path: Path(path).read_text(encoding="utf-8")
    fn = lambda src, name: src.split(f"function {name}(", 1)[1].split("\n}", 1)[0] if f"function {name}(" in src else ""
    whole = lambda src, name: f"function {name}(" + fn(src, name) + "\n}"
    rjs, app = support.text("apps/trace/static/trace.js"), support.text("family/static/shell.js", "apps/idiograph/static/distil.js")
    table = read(support.source("family/static/table.js"))
    refs_src, cli_src = read(support.source("apps/trace/trace_claims.py")), read(support.source("cli.py"))
    node = shutil.which("node")
    base = scratch / "refcheck-143"
    shutil.rmtree(base, ignore_errors=True)
    base.mkdir(parents=True)
    sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()

    def pdf_pages(pages):
        """An invented PDF, a page a string, in Helvetica, with a real cross-reference table"""
        ids = [4 + 2 * i for i in range(len(pages))]
        objs = {1: b"<< /Type /Catalog /Pages 2 0 R >>",
                2: f"<< /Type /Pages /Kids [{' '.join(f'{p} 0 R' for p in ids)}] /Count {len(pages)} >>".encode(),
                3: b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica /Encoding /WinAnsiEncoding >>"}
        for i, text in enumerate(pages):
            body = "BT /F1 11 Tf 14 TL 72 720 Td " + " ".join(
                "(" + ln.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)") + ") Tj T*" for ln in textwrap.wrap(text, 70)) + " ET"
            data = zl.compress(body.encode("cp1252"))
            objs[ids[i]] = f"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Resources << /Font << /F1 3 0 R >> >> /Contents {ids[i] + 1} 0 R >>".encode()
            objs[ids[i] + 1] = f"<< /Length {len(data)} /Filter /FlateDecode >>\nstream\n".encode() + data + b"\nendstream"
        out, at = bytearray(b"%PDF-1.4\n"), {}
        for k in sorted(objs):
            at[k] = len(out)
            out += f"{k} 0 obj\n".encode() + objs[k] + b"\nendobj\n"
        xref = len(out)
        out += f"xref\n0 {max(objs) + 1}\n0000000000 65535 f \n".encode() + b"".join(f"{at[k]:010d} 00000 n \n".encode() for k in range(1, max(objs) + 1))
        out += f"trailer\n<< /Size {max(objs) + 1} /Root 1 0 R >>\nstartxref\n{xref}\n%%EOF\n".encode()
        return bytes(out)

    # ── A. an invented protocol on community tool libraries, its reference list in APA's style
    body_md = """---
title: An invented protocol
---

# A protocol for a review of community tool libraries

## Background

Tool libraries lend drills and ladders to their members (Fenwick, 2018; Arden & Moyo, 2020). Fenwick (2018) traces the
first libraries, and Arden and Moyo (2020, p. 12) follow their volunteers. Castell et al.'s (2021) survey counts the
libraries in each city (see also Castell et al., 2021, pp. 4–5). The Tool Library Network [TLN] (2019) keeps a
register of them, and its later counts agree (TLN, 2019). Lending grew during COVID-19 (2020) in most cities (n = 12),
as Table 2 (see Appendix B) shows.

## Methods

We will report the review as the reporting guideline asks (Quint et al., 2022). Two reviewers will screen each record
(e.g., Lark, 2019a, 2019b; Brook, n.d.). In Lark (2019a) the reviewers met weekly. A study missing from the list is
cited here (Ostrander et al., 2016). An older survey is known only at second hand (Mallory, 1999, as cited in
Fenwick, 2018).

## References

Arden, P., & Moyo, T. (2020). Volunteers behind the counter. *Journal of Shared
Things*, 3(2), 10–24.

Brook, S. (n.d.). *Lending without money*. Commons Press.

Castell, R., Ivey, D., & Nunn, O. (2021). Counting the tool libraries. *Urban Commons*, 7, 1–15. https://doi.org/10.4321/uc.2021.007

Fenwick, A. (2018). *The first tool libraries*. Ladder Books.

Lark, M. (2019a). Two reviewers, one record. *Methods Notes*, 2, 5–9.

Lark, M. (2019b). Meeting weekly to agree. *Methods Notes*, 2, 10–14.

Mallory, J. (1999). *An early survey of lending*. Old Press.

Penhale, G. (2017). *An uncited essay on hammers*. Iron Press.

Quint, H., Ober, L., Sayer, K., & Tamm, V. (2022). A reporting guideline for reviews of shared things. *BMJ Methods*, 1, e42. https://doi.org/10.5555/bmjm.2022.42

Tool Library Network. (2019). *Register of tool libraries*. https://example.org/register
"""
    writing = base / "Writing"
    writing.mkdir()
    doc_md = writing / "protocol.md"
    doc_md.write_text(body_md, encoding="utf-8")
    got = refs.analyse(doc_md)
    by = {r["key"]: r for r in got["references"]}
    counts_of = {k: r["count"] for k, r in by.items()}
    check("143: the reference list read from under References, each entry its key, the first surname and the year with its "
          "letter, a wrapped entry one entry, a group's name whole and n.d. kept",
          list(by) == ["arden2020", "brooknd", "castell2021", "fenwick2018", "lark2019a", "lark2019b", "mallory1999",
                       "penhale2017", "quint2022", "toollibrarynetwork2019"]
          and by["arden2020"]["names"] == ["Arden", "Moyo"] and by["castell2021"]["names"] == ["Castell", "Ivey", "Nunn"]
          and by["toollibrarynetwork2019"]["names"] == ["Tool Library Network"] and by["brooknd"]["year"] == "n.d."
          and by["lark2019a"]["suffix"] == "a" and by["castell2021"]["doi"] == "10.4321/uc.2021.007"
          and by["arden2020"]["text"].endswith("Journal of Shared Things, 3(2), 10–24.") and "*" not in by["arden2020"]["text"]
          and got["sections"] == ["Background", "Methods"] and got["listed"] is True and got["source"] == "document", json.dumps(list(by)))
    check("143: each citation form APA writes is matched: one author, two with & and with and, et al. and its possessive, "
          "several in one bracket, a run of years with letters, e.g. and see, a page, as cited in, n.d., and a group by its "
          "name and by its abbreviation in square brackets, given alone later",
          counts_of == {"arden2020": 2, "brooknd": 1, "castell2021": 2, "fenwick2018": 3, "lark2019a": 2, "lark2019b": 1,
                        "mallory1999": 1, "penhale2017": 0, "quint2022": 1, "toollibrarynetwork2019": 2}
          and [c["as"] for c in by["arden2020"]["cites"]] == ["Arden & Moyo, 2020", "Arden & Moyo, 2020, p. 12"]
          and [c["as"] for c in by["castell2021"]["cites"]] == ["Castell et al., 2021", "Castell et al., 2021, pp. 4–5"]
          and [c["as"] for c in by["toollibrarynetwork2019"]["cites"]] == ["Tool Library Network, 2019", "TLN, 2019"]
          and [c["as"] for c in by["lark2019a"]["cites"]] == ["Lark, 2019a", "Lark, 2019a"], json.dumps(counts_of))
    check("143: a citation no reference answers is listed by its form, Ostrander et al., 2016, a reference never cited "
          "stands at nought, and words in capitals before a year, a count or a table in brackets are no citation",
          [(m["as"], m["count"]) for m in got["missing"]] == [("Ostrander et al., 2016", 1)] and by["penhale2017"]["cites"] == [],
          json.dumps([m["as"] for m in got["missing"]]))
    castell = by["castell2021"]
    keep = lambda c: {k: c[k] for k in ("section", "sentence", "as")}
    check("143: each claim is its citing sentence whole with its section's heading, once for a sentence that cites the "
          "reference twice, its opening words kept and no stop after et al. or p. ending it",
          [keep(c) for c in castell["claims"]] == [{"section": "Background", "sentence": "Castell et al.'s (2021) survey counts the libraries in each city "
                                                    "(see also Castell et al., 2021, pp. 4–5).", "as": ["Castell et al., 2021", "Castell et al., 2021, pp. 4–5"]}]
          and by["arden2020"]["claims"][1]["sentence"].startswith("Fenwick (2018) traces the first libraries")
          and keep(by["lark2019a"]["claims"][1]) == {"section": "Methods", "sentence": "In Lark (2019a) the reviewers met weekly.", "as": ["Lark, 2019a"]}
          and by["mallory1999"]["claims"][0]["sentence"].endswith("(Mallory, 1999, as cited in Fenwick, 2018).")
          and len(got["claims"]) == 14 and castell["claims"][0]["key"].startswith("castell2021~"),
          json.dumps(castell["claims"])[:300])

    # the same document as Word, its headings from a style named in another language and from Heading 2
    W = 'xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"'
    from xml.sax.saxutils import escape as xesc
    paras = []
    for line in body_md.split("---\n", 2)[2].strip().split("\n\n"):
        text = " ".join(line.split()).replace("*", "")
        m = re.match(r"^(#+)\s+(.*)$", text)
        style = ("Titre1" if len(m.group(1)) == 1 else "Heading2") if m else ""
        words = m.group(2) if m else text
        ppr = f'<w:pPr><w:pStyle w:val="{style}"/></w:pPr>' if style else ""
        paras.append(f'<w:p>{ppr}<w:r><w:rPr><w:i/></w:rPr><w:t xml:space="preserve">{xesc(words)}</w:t></w:r></w:p>')
    doc_x = writing / "protocol.docx"
    with zf.ZipFile(doc_x, "w") as book:
        book.writestr("[Content_Types].xml", '<?xml version="1.0" encoding="UTF-8"?><Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types"/>')
        book.writestr("word/document.xml", f'<?xml version="1.0" encoding="UTF-8"?><w:document {W}><w:body>{"".join(paras)}</w:body></w:document>')
        book.writestr("word/styles.xml", f'<?xml version="1.0" encoding="UTF-8"?><w:styles {W}><w:style w:type="paragraph" w:styleId="Titre1">'
                                          '<w:name w:val="heading 1"/></w:style><w:style w:type="paragraph" w:styleId="Heading2">'
                                          '<w:name w:val="heading 2"/></w:style></w:styles>')
    got_x = refs.analyse(doc_x)
    levels = convert.docx_paragraphs(doc_x.read_bytes(), "protocol.docx")
    check("143: a Word document reads the same, its headings by their styles' names in any language, and docx_text as before",
          {r["key"]: r["count"] for r in got_x["references"]} == counts_of and [m["as"] for m in got_x["missing"]] == ["Ostrander et al., 2016"]
          and got_x["sections"] == ["Background", "Methods"] and [lv for lv, _ in levels[:3]] == [1, 2, 0]
          and convert.docx_text(doc_x.read_bytes()).split("\n")[0] == "A protocol for a review of community tool libraries",
          json.dumps({r["key"]: r["count"] for r in got_x["references"]}))

    # ── B. a Trace project, its PDFs, a Sift project's screening run, then the server's route
    review = base / "Tool review"
    review.mkdir()
    (review / "search_plan.json").write_text(json.dumps({"name": "Tool libraries", "versions": []}), encoding="utf-8")
    run = review / "runs" / "2026-09-30"
    (run / "pdfs").mkdir(parents=True)
    with open(run / sift.CSV_NAME, "w", encoding="utf-8", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["rec_id", "title", "authors", "year", "doi", "abstract", "zotero_key"])
        w.writerow(["T001", "Volunteers behind the counter", "Arden, P.; Moyo, T.", "2020", "", "Volunteers run the counter.", "ABCD2345"])
    (run / "pdfs" / "T001.pdf").write_bytes(pdf_pages(["Volunteers behind the counter.", "Volunteers lend tools on Saturdays."]))
    project = base / "Tool trace"
    refs.make(project, "Tool trace")
    pdfs = project / refs.PDF_DIR
    pdfs.mkdir(parents=True)
    quint_pages = ["A reporting guideline for reviews of shared things. doi 10.5555/bmjm.2022.42",
                   "A review of shared things should report how many reviewers screened each record and how they settled "
                   "where they differed.", "The checklist holds twelve items."]
    (pdfs / "10.5555_bmjm.2022.42.pdf").write_bytes(pdf_pages(quint_pages))
    (pdfs / "counting.pdf").write_bytes(pdf_pages(["Counting the tool libraries. https://doi.org/10.4321/uc.2021.007",
                                                   "Each city held between two and nine tool libraries."]))
    (pdfs / "fenwick2018.pdf").write_bytes(pdf_pages(["The first tool libraries opened in church halls."]))
    before = {p.name: sha(p) for p in writing.iterdir()}
    listing_before = sorted(p.name for p in writing.iterdir())
    cfg = base / "config.json"
    cfg.write_text(json.dumps({"interviewer": "Adam", "ai_suggest": False, "ai_provider": "local", "local_model": "stub-model",
                               "local_url": "http://127.0.0.1:9", "zotero": {"library": "user", "group_id": ""}}), encoding="utf-8")
    empty_root = base / "no-cases"
    empty_root.mkdir()
    kept = (server_mod.CONFIG_PATH, server_mod.ROOT_OVERRIDE, server_mod.STATE_MEMORY, server_mod.PICK_FOLDER,
            server_mod.OPEN_FILE, server_mod.PLATFORM, ai_mod.http_call, trace_routes.SIFT_PATHS)
    call = lambda body: trace_routes.api_trace(dict(body, folder=str(project)))
    refused = lambda body: refusal_of(lambda: call(body))
    opened, asked, picked = [], [], []
    log = lambda: [json.loads(l) for l in (project / "protocol.log.jsonl").read_text(encoding="utf-8").splitlines() if l.strip()]
    claim_of = lambda ref, n=0: [c for c in got["claims"] if c["ref"] == ref][n]["key"]
    quint_c, castell_c, brook_c = claim_of("quint2022"), claim_of("castell2021"), claim_of("brooknd")
    missing_c = [c for c in got["claims"] if not c["ref"]][0]["key"]

    def stub(method, url, headers, payload, timeout):
        """the local model's chat, a passage the PDF holds for Quint et al., one it does not for Castell et al."""
        msg = payload["messages"][-1]["content"]
        asked.append(msg)
        if "reporting guideline for reviews" in msg.split("Claims the document makes of it", 1)[0]:
            ans = {"claims": [{"claim": 1, "found": True, "page": 3,
                               "passage": "should report how many reviewers  screened each record"}]}
        else:
            ans = {"claims": [{"claim": 1, "found": True, "page": 2, "passage": "Every city held at least forty tool libraries."}]}
        return 200, json.dumps({"message": {"content": json.dumps(ans)}, "done_reason": "stop"})

    try:
        server_mod.ROOT_OVERRIDE = str(empty_root)
        server_mod.STATE_MEMORY = {"recent": []}
        server_mod.CONFIG_PATH = cfg
        server_mod.OPEN_FILE = lambda target: opened.append(Path(target))
        ai_mod.http_call = stub
        try:
            call({"op": "list"})
            outside = ""
        except server_mod.OutsideRoot as exc:
            outside = str(exc)
        sift_routes.api_sift_review({"op": "open", "folder": str(review)})
        # Sift's own list of its projects, which Trace reads (area 254), holding the review as Sift keeps it
        sift_list = base / "state.sift.json"
        sift_list.write_text(json.dumps({"recent": [], "sift_reviews": server_mod.STATE_MEMORY["sift_reviews"]}), encoding="utf-8")
        trace_routes.SIFT_PATHS = lambda: {"state": sift_list, "base": base}
        made = trace_routes.api_trace_project({"op": "open", "folder": str(project)})
        empty = call({"op": "list"})
        server_mod.PLATFORM = "darwin"
        server_mod.PICK_FOLDER = lambda prompt, files=False: (picked.append((prompt, files)), None)[1]
        cancelled = call({"op": "add"})
        added = call({"op": "add", "path": str(doc_md)})
        again = call({"op": "add", "path": str(doc_md)})
        not_kind = refused({"op": "add", "path": str(base / "config.json")})
        view = call({"op": "read", "doc": "protocol"})
        rows = {r["key"]: r for r in view["rows"]}
        state_file = json.loads((project / "protocol.json").read_text(encoding="utf-8"))
        y = call({"op": "judge", "doc": "protocol", "claim": quint_c, "value": "Y"})
        n = call({"op": "judge", "doc": "protocol", "claim": castell_c, "value": "N"})
        note = call({"op": "note", "doc": "protocol", "claim": quint_c, "note": "Read the guideline's PDF myself."})
        missing_y = refused({"op": "judge", "doc": "protocol", "claim": missing_c, "value": "Y"})
        bad_value = refused({"op": "judge", "doc": "protocol", "claim": quint_c, "value": "maybe"})
        u1 = call({"op": "undo", "doc": "protocol"})
        u2 = call({"op": "undo", "doc": "protocol"})
        after_undo = {r["key"]: r for r in call({"op": "read", "doc": "protocol"})["rows"]}
        call({"op": "note", "doc": "protocol", "claim": quint_c, "note": "Read the guideline's PDF myself."})
        off_plan = refused({"op": "plan", "doc": "protocol"})
        off_point = refused({"op": "passages", "doc": "protocol", "ref": "quint2022"})
        cfg.write_text(json.dumps(dict(json.loads(cfg.read_text(encoding="utf-8")), ai_suggest=True)), encoding="utf-8")
        plan = call({"op": "plan", "doc": "protocol", "ids": [quint_c, castell_c, "penhale2017", brook_c]})
        good = call({"op": "passages", "doc": "protocol", "ref": "quint2022"})
        bad = call({"op": "passages", "doc": "protocol", "ref": "castell2021"})
        no_pdf = call({"op": "passages", "doc": "protocol", "ref": "brooknd"})
        seen_on = {r["key"]: r for r in call({"op": "read", "doc": "protocol"})["rows"]}
        y2 = call({"op": "judge", "doc": "protocol", "claim": quint_c, "value": "Y"})
        cfg.write_text(json.dumps(dict(json.loads(cfg.read_text(encoding="utf-8")), ai_suggest=False)), encoding="utf-8")
        seen_off = {r["key"]: r for r in call({"op": "read", "doc": "protocol"})["rows"]}
        call({"op": "open", "doc": "protocol", "ref": "quint2022"})
        open_none = refused({"op": "open", "doc": "protocol", "ref": "brooknd"})
        kept_pdf = call({"op": "pdf", "doc": "protocol", "ref": "brooknd", "data": base64.b64encode(pdf_pages(["Lending without money."])).decode()})
        pdf_twice = refused({"op": "pdf", "doc": "protocol", "ref": "brooknd", "data": base64.b64encode(pdf_pages(["Again."])).decode()})
        not_pdf = refused({"op": "pdf", "doc": "protocol", "ref": "lark2019a", "data": base64.b64encode(b"not a pdf").decode()})
        served = trace_routes.trace_pdf({"folder": str(project), "doc": "protocol", "ref": "quint2022"})
        served_none = trace_routes.trace_pdf({"folder": str(project), "doc": "protocol", "ref": "penhale2017"})
        server_mod.PICK_FOLDER = lambda prompt, files=False: (picked.append((prompt, files)), doc_x)[1]
        added_x = call({"op": "add"})
        docs_now = call({"op": "list"})["docs"]
    finally:
        (server_mod.CONFIG_PATH, server_mod.ROOT_OVERRIDE, server_mod.STATE_MEMORY, server_mod.PICK_FOLDER,
         server_mod.OPEN_FILE, server_mod.PLATFORM, ai_mod.http_call, trace_routes.SIFT_PATHS) = kept
    check("143: a project the list of Trace projects does not hold is refused, and the routes take a POST alone",
          outside == trace_routes.TRACE_NOT_OPENED and "/api/trace" in server_mod.POST_ONLY and "/api/trace-project" in server_mod.POST_ONLY
          and server_mod.ROUTES.get("/api/trace") is trace_routes.api_trace and "/api/sift-refs" not in server_mod.ROUTES
          and made["project"]["name"] == "Tool trace", outside)
    check("143: a document is added by its typed path or through the Mac's file dialog, a Cancel adds nothing, the same "
          "document added again is the one there, and anything but a manuscript or a reference list is refused in one line",
          empty["docs"] == [] and cancelled["chosen"] is False and picked[0] == (trace_routes.TRACE_PROMPT, True)
          and added["doc"] == "protocol" and again["doc"] == "protocol" and len(again["docs"]) == 1
          and not_kind == refs.NOT_KIND and added_x["doc"] == "protocol-2" and [d["doc"] for d in docs_now] == ["protocol", "protocol-2"],
          json.dumps([cancelled, added["doc"], not_kind]))
    check("143: the table's rows, each claim with its reference, section, PDF and no judgement, a citation with no reference "
          "a row of its own, and the PDF found by DOI in the file's name, by DOI on its first page, by its key, and as a "
          "screening record's by its title, with its Zotero item as a link for the Zotero app, every path with forward slashes",
          rows[quint_c]["pdf"] is True and rows[quint_c]["pdf_name"] == "pdfs/10.5555_bmjm.2022.42.pdf"
          and rows[castell_c]["pdf_name"] == "pdfs/counting.pdf"
          and rows[claim_of("fenwick2018")]["pdf_name"] == "pdfs/fenwick2018.pdf"
          and rows[claim_of("arden2020")]["pdf_from"] == "screening" and rows[claim_of("arden2020")]["pdf_name"] == "runs/2026-09-30/pdfs/T001.pdf"
          and rows[claim_of("arden2020")]["zotero"] == "zotero://select/library/items/ABCD2345" and rows[brook_c]["pdf"] is False
          and all(r["judged"] == "" and r["set"] == "" for r in view["rows"])
          and rows[missing_c]["kind"] == "missing" and rows[missing_c]["short"] == "Ostrander et al., 2016"
          and rows["penhale2017"]["kind"] == "uncited" and rows[castell_c]["section"] == "Background"
          and not any("\\" in r["pdf_name"] for r in view["rows"])
          and view["model_name"] == "" and view["config"] == {"ai_suggest": False},
          json.dumps({k: [r["pdf_name"], r["zotero"]] for k, r in rows.items()})[:600])
    check("143: the readable file is written in the project's own folder as the screen reads, each claim with no judgement "
          "and no day, and nothing is written beside the document",
          state_file["name"] == "protocol.md" and state_file["claims"][0] == {"key": claim_of("fenwick2018"), "reference": "fenwick2018",
                                                                              "section": "Background", "claim": got["claims"][0]["sentence"],
                                                                              "judged": "", "set": "", "note": ""}
          and state_file["no_reference"] == [{"cited_as": "Ostrander et al., 2016", "claim": "A study missing from the list is cited here (Ostrander et al., 2016)."}]
          and state_file["never_cited"] == ["penhale2017"] and state_file["counts"] == {"claims": 13, "judged": 0}
          and sorted(p.name for p in writing.iterdir()) == listing_before, json.dumps(state_file["claims"][0]))
    today = datetime.now().date().isoformat()
    check("143: a judgement is his, each a line of the log with the day, as the researcher's, and Undo takes back his newest "
          "note then his newest judgement, each by a line of its own",
          y["state"] == {"judged": "Y", "set": today, "note": ""} and n["state"]["judged"] == "N"
          and n["state"]["set"] == today and note["state"]["note"] == "Read the guideline's PDF myself."
          and missing_y == refs.NOTHING_TO_JUDGE and bad_value == refs.JUDGE_VALUES
          and u1["undone"]["what"] == "note" and u1["state"]["note"] == "" and u2["undone"] == {"claim": castell_c, "what": "judge", "n": 2}
          and after_undo[castell_c]["judged"] == "" and after_undo[castell_c]["set"] == ""
          and after_undo[quint_c]["judged"] == "Y", json.dumps([u1["undone"], u2["undone"]]))
    lines = log()
    judged_lines = [e for e in lines if e["act"] == "judge"]
    check("143: each judgement's line says it was the researcher's in plain words, with the AI's passages shown and what "
          "they found while the AI switch was on, never that an AI checked",
          all(e["by"] == "researcher" and e["tool"] == "Trace" for e in judged_lines)
          and judged_lines[0]["words"] == "The researcher judged it Supports" and "passages_shown" not in judged_lines[0]
          and judged_lines[-1]["passages_shown"] == {"model": "stub-model on this machine", "found": True, "unverified": False}
          and judged_lines[-1]["words"] == "The researcher judged it Supports, with the AI's passages shown, stub-model on this machine, "
                                           "a passage found"
          and not any("AI checked" in json.dumps(e) for e in lines) and y2["state"]["judged"] == "Y",
          json.dumps(judged_lines[-1])[:300])
    gp, bp = good["passages"], bad["passages"]
    check("143: with the AI switch off no passages are asked, and with it on the references of the rows shown with a PDF "
          "and no passages are named first, a call each",
          off_plan == off_point == sift_ai_off_line() and plan == {"ids": ["castell2021", "quint2022"], "calls": 2}
          and no_pdf.get("error") == refs.NO_PDF and no_pdf.get("status") == 502, json.dumps(plan))
    check("143: a passage the PDF holds is kept in the PDF's own words with the page it stands on, the model's spacing set "
          "aside, and one it does not hold is never kept as a quote, its words nowhere in the files",
          gp["claims"] == [{"n": 1, "found": True, "page": 2, "passage": "should report how many reviewers screened each record",
                            "claim": quint_c, "said": "We will report the review as the reporting guideline asks (Quint et al., 2022)."}]
          and gp["model"] == "stub-model on this machine" and gp["found"] == 1 and gp["of"] == 1
          and bp["claims"][0]["unverified"] is True and "passage" not in bp["claims"][0] and bp["found"] == 0
          and "forty" not in (project / "protocol.json").read_text(encoding="utf-8")
          and "forty" not in (project / "protocol.log.jsonl").read_text(encoding="utf-8")
          and "[Page 2]" in asked[0] and "1. (Methods) We will report the review" in asked[0], json.dumps(gp)[:400])
    check("143: passages never set a judgement: Castell et al.'s claim stays unjudged after its passages, and the log's "
          "passages lines are the AI's",
          bad.get("state") is None and seen_on[castell_c]["judged"] == "" and good.get("state") is None
          and seen_on[quint_c]["judged"] == "Y"
          and all(e["by"] == "ai" and "judged" not in e for e in lines if e["act"] == "passages")
          and seen_on[quint_c]["passages"]["found"] == 1 and seen_on[quint_c]["passage"]["page"] == 2
          and seen_off[quint_c]["passages"] is None and seen_off[quint_c]["passage"] is None,
          json.dumps(seen_on[castell_c])[:200])
    check("143: Open PDF opens it in the computer's own app, the pane serves it from the project alone, Add PDF keeps one "
          "under the reference's name, never over one there, and only a PDF",
          [Path(o).resolve() for o in opened] == [(pdfs / "10.5555_bmjm.2022.42.pdf").resolve()] and open_none == refs.NO_PDF and kept_pdf == {"saved": True}
          and (pdfs / "brooknd.pdf").is_file() and pdf_twice == refs.PDF_THERE and not_pdf == refs.NOT_PDF
          and served[0] == 200 and served[1][:5] == b"%PDF-" and served[2] == "application/pdf" and served_none[0] == 404,
          json.dumps([str(o) for o in opened]))
    check("143: the document is never written, Markdown or Word, and nothing new stands beside it",
          {p.name: sha(p) for p in writing.iterdir()} == before and sorted(p.name for p in writing.iterdir()) == listing_before
          and "write" not in fn(refs_src, "blocks_of") and "write" not in fn(refs_src, "analyse"))
    win_rel = ntpath.join("runs", "2026-09-30", "pdfs", "T001.pdf")
    check("143: a relative path Trace stores or answers takes forward slashes on any system, one written on Windows with "
          "backslashes among them, and is joined back with Path when opened (Windows, 15 October)",
          win_rel == "runs\\2026-09-30\\pdfs\\T001.pdf" and refs.slashed(win_rel) == "runs/2026-09-30/pdfs/T001.pdf"
          and refs.joined(review, refs.slashed(win_rel)) == review / "runs" / "2026-09-30" / "pdfs" / "T001.pdf"
          and refs.joined(review, win_rel) == review / "runs" / "2026-09-30" / "pdfs" / "T001.pdf"
          and refs.rel_name(review, run / "pdfs" / "T001.pdf") == "runs/2026-09-30/pdfs/T001.pdf", refs.slashed(win_rel))

    # ── C. the PDF's text page by page, and a passage found whatever its spacing, hyphens and case
    pages = sift_oa.pages_text(pdf_pages(quint_pages))
    check("143: every page of a PDF is read in order, the first page as first_page_text reads it, and a passage is found "
          "in order across an ellipsis, too short or absent found nowhere",
          len(pages) == 3 and pages[1].startswith("A review of shared things should report")
          and sift_oa.first_page_text(pdf_pages(quint_pages)) == pages[0]
          and refs.locate("A REVIEW of shared-things should report", pages) == (2, "A review of shared things should report")
          and refs.locate("how many reviewers … settled where they differed", pages)[1] == "how many reviewers … settled where they differed"
          and refs.locate("twelve", pages) is None and refs.locate("a sentence the PDF never held at all", pages) is None)

    # ── D. agents read alone: the command line and MCP
    log_sha = sha(project / "protocol.log.jsonl")
    shown = cli_mod.perform(argparse.Namespace(command="trace", folder=str(project), document="protocol", json=True,
                                               note="", tool="", project=None, dry_run=False))
    listed = cli_mod.perform(argparse.Namespace(command="trace", folder=str(project), document=None, json=True,
                                                note="", tool="", project=None, dry_run=False))
    t = mcp_server.BY_NAME.get("trace_claims")
    margs = mcp_server.arguments(t, {"folder": str(project), "document": "protocol.md"}, {}, "Claude Desktop") if t else None
    via_mcp = cli_mod.perform(margs) if margs else ({}, [])
    check("143: the command line's trace lists the manuscripts and reads one, every claim with its sentence, the judgement "
          "with the day, the note, the PDF and the passages, and the log, with no act that judges",
          listed[0]["documents"][0]["counts"]["judged"] == 1 and len(listed[0]["documents"]) == 2
          and any(line.startswith(f"Supports {today}  {quint_c}") for line in shown[1])
          and any("AI passages (stub-model on this machine): page 2" in line for line in shown[1])
          and any(refs.FAILED in line for line in shown[1]) and any(line.startswith("No reference  Ostrander et al., 2016") for line in shown[1])
          and shown[0]["log"][0]["act"] == "judge" and "sift_refs" not in cli_src and "REFS_ACTS" not in cli_src
          and cli_mod.parser("trace").parse_args([str(project)]).command == "trace", "\n".join(shown[1][:4]))
    check("143: MCP's trace_claims only reads, by the project's folder and the manuscript's name, and the log is as it was after both",
          t is not None and t["annotations"]["readOnlyHint"] is True and "document" in t["inputSchema"]["properties"]
          and via_mcp[0].get("doc") == "protocol" and sha(project / "protocol.log.jsonl") == log_sha
          and "no tool judges a claim or writes a note" in mcp_server.instructions("trace") and "sift_refs" not in mcp_server.BY_NAME,
          json.dumps(t["annotations"]) if t else "")

    # ── E. the screen in node: its columns through Sift's own table and filters, and a passage drawn
    if node:
        lead = app[app.index("const esc = "):app.index("// a line from the server with a command in backticks")]
        head = rjs.split("'use strict';", 1)[1].split("/* ── opening ── */", 1)[0]
        # the family's table whole (table.js), which Trace's screen draws through since 22 October 2026
        parts = [table.split("'use strict';", 1)[1], lead, "const $ = () => null;", head, whole(rjs, "trPassageHtml")]
        rows_json = json.dumps(list(seen_on.values()))
        probe = base / "refcheck-143.js"
        probe.write_text(support.i18n_js("trace") + "\n".join(parts) + f"""
TR.rows = {rows_json};
TR.doc = 'protocol';
TR.byId = new Map(TR.rows.map((r) => [r.key, r]));
const out = {{}};
const keys = () => TR.ids.slice();
TR.filters = {{ judged: ['Y'] }}; trApply(); out.yes = keys();
TR.filters = {{ isjudged: ['no'] }}; trApply(); out.no = keys();
TR.filters = {{ haspdf: ['no'] }}; trApply(); out.noPdf = keys();
TR.filters = {{ kind: ['missing', 'uncited'] }}; trApply(); out.notCited = keys();
TR.filters = {{ section: ['Background'] }}; trApply(); out.background = keys();
TR.filters = {{ short: ['Fenwick, 2018'] }}; trApply(); out.fenwick = keys();
TR.filters = {{}}; TR.sort = [{{ key: 'haspdf', dir: 'desc' }}]; trApply(); out.byPdf = keys().slice(0, 1);
TR.sort = tbSortNext([], TR_COLS.find((c) => c.key === 'haspdf'), false); out.firstSort = TR.sort;
TR.sort = [];
const data = trFacetsData();
out.groups = data.groups.map((g) => [g.label, g.choices.map((c) => c.label)]);
out.counts = data.counts;
out.html = tbGroupHtml(data.groups[1], data.counts.judged, 'tr-1', TR);
out.head = tbTvHeadHtml(TR_COLS, [{{ key: 'haspdf', dir: 'desc' }}]);
out.row = trRowHtml(TR.byId.get({json.dumps(quint_c)}));
out.blank = trRowHtml(TR.byId.get({json.dumps(castell_c)}));
out.missingRow = trRowHtml(TR.byId.get({json.dumps(missing_c)}));
const gp = TR.byId.get({json.dumps(quint_c)}).passage, bp = TR.byId.get({json.dumps(castell_c)}).passage;
out.good = trPassageHtml(gp);
out.bad = trPassageHtml(bp);
out.none = trPassageHtml({{ n: 1, found: false }});
out.short = [TR.byId.get({json.dumps(quint_c)}).short, TR.byId.get({json.dumps(claim_of("arden2020"))}).short, TR.byId.get({json.dumps(claim_of("fenwick2018"))}).short];
console.log(JSON.stringify(out));
""", encoding="utf-8")
        ran = subprocess.run([node, str(probe)], capture_output=True, text=True, encoding="utf-8", timeout=60)
        out = json.loads(ran.stdout) if ran.returncode == 0 and ran.stdout.strip() else {}
        why = (ran.stderr or json.dumps(out))[:600]
        check("143: in node, the family's table, tbFilterRows and tbSortRows, filters the rows by judgement, judged or not, PDF, how "
              "they are cited, the section and the reference, a citation with no reference under No reference alone, and "
              "PDF sorts those with one first",
              out.get("yes") == [quint_c] and missing_c not in out.get("no", ["x"]) and "penhale2017" not in out.get("no", ["x"])
              and len(out.get("no", [])) == 12 and missing_c not in out.get("noPdf", ["x"])
              and out.get("notCited") == [missing_c, "penhale2017"]
              and len(out.get("background", [])) == 6 and len(out.get("fenwick", [])) == 3
              and out.get("byPdf") and seen_on[out["byPdf"][0]]["pdf"] is True
              and out.get("firstSort") == [{"key": "haspdf", "dir": "desc"}], why)
        check("143: in node, the filters are the family's table's groups, Judged, Judgement, PDF, Citations, Section and Reference, each "
              "choice with its live count, Supports' dot in the screening's green, drawn by tbGroupHtml from the screen's own state",
              [g[0] for g in out.get("groups", [])] == ["Judged", "Judgement", "PDF", "Citations", "Section", "Reference"]
              and out.get("counts", {}).get("isjudged") == {"no": 12, "yes": 1} and out.get("counts", {}).get("kind", {}).get("missing") == 1
              and "Supports" in out.get("html", ""), why)
        check("143: in node, a judged claim's row shows Supports and its PDF, a claim not judged no judgement, and a "
              "citation with no reference a row with No reference and its form",
              "Supports" in out.get("row", "") and "PDF" in out.get("row", "")
              and '<td class="sf-c-dec"></td>' in out.get("blank", "") and "Supports" not in out.get("blank", "x")
              and "No reference" in out.get("missingRow", "") and "Ostrander et al., 2016" in out.get("missingRow", ""), why)
        check("143: in node, a passage is drawn in the PDF's words with its page, which shows that page, and a passage not "
              "in the PDF is never drawn as a quote, only the line that says so",
              'data-page="2">Page 2</button>' in out.get("good", "")
              and '<blockquote class="tr-passage">should report how many reviewers screened each record</blockquote>' in out.get("good", "")
              and "tr-passage" not in out.get("bad", "") and "forty" not in out.get("bad", "") and bool(out.get("bad"))
              and "tr-passage" not in out.get("none", "") and bool(out.get("none"))
              and out.get("short") == ["Quint et al., 2022", "Arden & Moyo, 2020", "Fenwick, 2018"], why)
    else:
        skip("143: the screen in node", "node is not on this machine")

    # ── F. the AI switch and the keys
    check("143: every AI part is marked data-ai with the sparkles, so the switch hides it",
          rjs.count('data-ai') >= 3)
    check("143: the keys are Y, Q and N as on a record, and Cmd + Z takes back the last judgement",
          "const TR_KEYS = { y: 'Y', q: 'Q', n: 'N' };" in rjs and "if (TR_KEYS[key]) { e.preventDefault(); trJudge(TR_KEYS[key]); }" in fn(rjs, "trKeyDown")
          and "if (MOD(e) && (e.key === 'z' || e.key === 'Z') && !e.shiftKey) { e.preventDefault(); trUndo(); return; }" in fn(rjs, "trKeyDown"))

def sift_ai_off_line() -> str:
    import sift_ai
    return sift_ai.OFF
