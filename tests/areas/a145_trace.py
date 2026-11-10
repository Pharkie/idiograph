from __future__ import annotations

import json
import shutil
from pathlib import Path

from . import support
from .support import check, refusal_of
import idiograph_routes
import statement_prompts


@support.as_app("trace")
def test_trace(scratch):
    print("\n145. Trace, 15 October, Adam's words: a third part of Idiograph beside Distil and Sift, not a stage of Sift, "
          "a manuscript or a reference list alone, CSV, RIS or BibTeX, the claim the unit, each citation with its "
          "sentence and the sentence before where it leans on it, Supports, Question or Doesn't support his alone, "
          "the AI's passages shown only when found in the PDF, Sift's Check references read in place, and the three "
          "parts named as verbs, Distil, Sift, Trace. Since the test review of 18 October the screens' words, pills and "
          "layout are review shots, and the project, its claims, its lists, his judgements and what the agents may do stay")
    import argparse
    import hashlib
    import cli as cli_mod
    import mcp_server
    import ai_suggest as ai_mod
    import sift_ai
    import themes_ai
    import trace_claims as tr
    import server as server_mod
    import trace_routes

    read = lambda path: Path(path).read_text(encoding="utf-8")
    fn = lambda src, name: src.split(f"function {name}(", 1)[1].split("\n}", 1)[0] if f"function {name}(" in src else ""
    base = scratch / "trace-145"
    shutil.rmtree(base, ignore_errors=True)
    base.mkdir(parents=True)
    sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()

    # ── B. a project made, renamed, read and removed, as Sift's are, each with its own folder
    cfg = base / "config.json"
    cfg.write_text(json.dumps({"interviewer": "Adam", "ai_suggest": False}), encoding="utf-8")
    roots = base / "no-cases"
    roots.mkdir()
    empty_place, full_place = base / "Seed check", base / "Writing"
    empty_place.mkdir()
    full_place.mkdir()
    (full_place / "notes.txt").write_text("a note", encoding="utf-8")
    kept = (server_mod.CONFIG_PATH, server_mod.ROOT_OVERRIDE, server_mod.STATE_MEMORY, server_mod.PICK_FOLDER, server_mod.PLATFORM)
    picked = []
    try:
        server_mod.CONFIG_PATH = cfg
        server_mod.ROOT_OVERRIDE = str(roots)
        server_mod.STATE_MEMORY = {"recent": []}
        server_mod.PLATFORM = "darwin"
        server_mod.PICK_FOLDER = lambda prompt, files=False: (picked.append(prompt), empty_place)[1]
        chosen = trace_routes.api_trace_project({"op": "folder", "mode": "new"})
        made = trace_routes.api_trace_project({"op": "new", "folder": str(empty_place), "name": "Seed check"})
        inside = trace_routes.api_trace_project({"op": "new", "folder": str(full_place), "name": "Seed paper"})
        twice = refusal_of(lambda: trace_routes.api_trace_project({"op": "new", "folder": str(empty_place), "name": "Again"}))
        cards = server_mod.api_home({})["traces"]
        renamed = trace_routes.api_trace_project({"op": "rename", "folder": str(empty_place), "name": "Seed library protocol"})
        listed_files = sorted(p.name for p in empty_place.iterdir())
        gone = trace_routes.api_trace_project({"op": "forget", "folder": inside["project"]["folder"]})
        after = server_mod.api_home({})["traces"]
        not_project = refusal_of(lambda: trace_routes.api_trace_project({"op": "open", "folder": str(roots)}))
    finally:
        (server_mod.CONFIG_PATH, server_mod.ROOT_OVERRIDE, server_mod.STATE_MEMORY, server_mod.PICK_FOLDER, server_mod.PLATFORM) = kept
    # the folder the server names back is held as a path, never as text with a slash in it, so the check reads
    # the same on Windows, where it comes back with backslashes (GitHub's Windows run, 15 October)
    check("145: New project takes a folder through the Mac's dialog or typed, makes the project in an empty folder or in a "
          "new folder inside one that holds anything, refuses a folder that holds one, and lists it on the first screen",
          picked == [trace_routes.NEW_TRACE_PROMPT] and chosen == {"chosen": True, "folder": str(empty_place.resolve()), "name": "Seed check"}
          and (empty_place / tr.PROJECT_FILE).is_file()
          and server_mod.same_folder(server_mod.abs_path(inside["project"]["folder"]), full_place / "Seed paper")
          and (full_place / "Seed paper" / tr.PROJECT_FILE).is_file() and (full_place / "notes.txt").is_file()
          and twice == "That folder holds a Trace project already."
          and [c["name"] for c in cards] == ["Seed paper", "Seed check"] and cards[1]["line"] == "No document yet"
          and made["project"]["name"] == "Seed check", json.dumps(cards)[:300])
    check("145: a project is renamed in the app's own list, never in its folder, and Remove from Idiograph takes it out of "
          "the list alone, its folder and files left as they are",
          renamed["project"]["name"] == "Seed library protocol" and listed_files == [tr.PROJECT_FILE]
          and json.loads((empty_place / tr.PROJECT_FILE).read_text(encoding="utf-8"))["name"] == "Seed check"
          and gone["name"] == "Seed paper" and [c["name"] for c in after] == ["Seed library protocol"]
          and (full_place / "Seed paper" / tr.PROJECT_FILE).is_file() and not_project == tr.NOT_A_PROJECT, json.dumps(after)[:200])

    # ── C. claims, each with the sentence before where it leans on it
    body = """# A protocol on community seed libraries

## Background

Seed libraries lend seeds to gardeners each spring. These loans are returned as saved seed at harvest (Okafor, 2019).
Some libraries keep paper records only (Vance & Ito, 2021). Okafor (2019) describes the first library in a school hall.
However, most libraries lose a third of their stock each year (Brennan et al., 2020).

## References

Brennan, T., Okafor, N., & Lisle, P. (2020). Losing seed. *Seed Studies*, 4, 1–9. https://doi.org/10.7777/ss.2020.4

Okafor, N. (2019). *The first seed library*. Garden Press.

Vance, R., & Ito, K. (2021). Paper records in small libraries. *Library Notes*, 9, 20–31.
"""
    project = empty_place
    writing = base / "Drafts"
    writing.mkdir()
    doc = writing / "seed protocol.md"
    doc.write_text(body, encoding="utf-8")
    got = tr.analyse(doc)
    by = {(c["ref"], c["sentence"][:12]): c for c in got["claims"]}
    leaned = by[("okafor2019", "These loans ")]
    check("145: a citation that closes a sentence leaning on the one before, These or However, is a claim with that "
          "sentence before it, and a sentence that leans on nothing, or whose citation opens it, has none",
          leaned["before"] == "Seed libraries lend seeds to gardeners each spring."
          and by[("brennan2020", "However, mos")]["before"] == "Okafor (2019) describes the first library in a school hall."
          and by[("vance2021", "Some librari")]["before"] == "" and by[("okafor2019", "Okafor (2019")]["before"] == ""
          and [c["ref"] for c in got["claims"]] == ["okafor2019", "vance2021", "okafor2019", "brennan2020"]
          and tr.leans("This growth is steady (Ober, 2018).") and not tr.leans("Libraries grew (Ober, 2018)."),
          json.dumps([[c["ref"], c["before"][:20]] for c in got["claims"]]))

    # ── D. reference lists alone: a CSV of any reference manager's columns, RIS and BibTeX
    zcsv = base / "zotero export.csv"
    zcsv.write_text('﻿"Key","Item Type","Publication Year","Author","Title","Publication Title","DOI"\n'
                    '"QRST2345","journalArticle","2020","Brennan, Tom; Okafor, Nia; Lisle, Pat","Losing seed","Seed Studies",""\n'
                    '"UVWX6789","book","2019","Okafor, Nia","The first seed library","",""\n'
                    '"ABCD6789","journalArticle","2021","Vance, Rae; Ito, Ken","Paper records in small libraries","Library Notes","10.8888/ln.2021.9"\n'
                    '"EFGH2345","journalArticle","2018","Ober, Lin","Seed swaps","Seed Studies",""\n'
                    '"JKLM2345","journalArticle","2018","Ober, Lin","A garden ledger","Seed Studies",""\n', encoding="utf-8")
    plain = base / "plain list.csv"
    plain.write_text("Reference;DOI\n\"Okafor, N. (2019). The first seed library. Garden Press.\";\n", encoding="utf-8")
    ris = base / "export.ris"
    ris.write_text("TY  - JOUR\nAU  - Brennan, Tom\nAU  - Okafor, Nia\nAU  - Lisle, Pat\nTI  - Losing seed\nT2  - Seed Studies\n"
                   "PY  - 2020\nDO  - 10.7777/ss.2020.4\nER  - \n\nTY  - BOOK\nAU  - Seed Library Network\nTI  - A register\n"
                   "PY  - 2017///\nER  - \n", encoding="utf-8")
    bib = base / "export.bib"
    bib.write_text("@comment{an export}\n@article{brennan2020, author = {Tom Brennan and Okafor, Nia and Pat Lisle}, "
                   "title = {Losing {Seed}}, journal = {Seed Studies}, year = {2020}, doi = {10.7777/ss.2020.4}}\n"
                   "@book{network, author = {{Seed Library Network}}, title = \"A register\", date = {2017-05-01}}\n"
                   "@article{muller, author = {M{\\\"u}ller, Jo}, title = {Ok}, year = 2016}\n", encoding="utf-8")
    zl, pl, rl, bl = tr.read_list(zcsv), tr.read_list(plain), tr.read_list(ris), tr.read_list(bib)
    check("145: a CSV of Zotero's columns gives each reference its surnames, year, DOI and Zotero item, the same authors' "
          "works of one year lettered by their titles as APA letters them, and a CSV of whole references reads each as an "
          "entry of a reference list",
          [r["key"] for r in zl] == ["brennan2020", "okafor2019", "vance2021", "ober2018b", "ober2018a"]
          and zl[0]["names"] == ["Brennan", "Okafor", "Lisle"] and zl[0]["zotero"] == "QRST2345" and zl[2]["doi"] == "10.8888/ln.2021.9"
          and zl[3]["title"] == "Seed swaps" and zl[0]["text"] == "Brennan, Tom; Okafor, Nia; Lisle, Pat (2020). Losing seed. Seed Studies."
          and [r["key"] for r in pl] == ["okafor2019"] and pl[0]["title"] == "The first seed library.",
          json.dumps([[r["key"], r["names"], r["zotero"]] for r in zl]))
    check("145: an RIS and a BibTeX export read alike, a group's name whole, a name written Given Surname by its surname, "
          "BibTeX's accents made letters and its braces taken away",
          [(r["key"], r["names"], r["doi"]) for r in rl] == [("brennan2020", ["Brennan", "Okafor", "Lisle"], "10.7777/ss.2020.4"),
                                                            ("seedlibrarynetwork2017", ["Seed Library Network"], "")]
          and [(r["key"], r["names"]) for r in bl] == [("brennan2020", ["Brennan", "Okafor", "Lisle"]),
                                                       ("seedlibrarynetwork2017", ["Seed Library Network"]), ("muller2016", ["Müller"])]
          and bl[0]["title"] == "Losing Seed" and bl[0]["doi"] == "10.7777/ss.2020.4"
          and refusal_of(lambda: tr.read_list(base / "config.json")) == tr.NOT_KIND,
          json.dumps([[r["key"], r["names"]] for r in rl + bl]))

    # a reference list alone, then a manuscript with no list of its own matched to it, then one with its own
    bare = writing / "bare draft.md"
    bare.write_text("# A draft\n\nSeed swaps grew in spring (Ober, 2018a). This made a ledger worth keeping (Ober, 2018b).\n"
                    "Paper records persist (Vance & Ito, 2021).\n", encoding="utf-8")
    shas = {p: sha(p) for p in (zcsv, bare, doc)}
    kept = (server_mod.CONFIG_PATH, server_mod.ROOT_OVERRIDE, server_mod.STATE_MEMORY)
    try:
        server_mod.CONFIG_PATH = cfg
        server_mod.ROOT_OVERRIDE = str(roots)
        server_mod.STATE_MEMORY = {"recent": []}
        trace_routes.api_trace_project({"op": "open", "folder": str(project)})
        call = lambda body: trace_routes.api_trace(dict(body, folder=str(project)))
        refused = lambda body: refusal_of(lambda: call(body))
        no_list = refused({"op": "add", "path": str(bare)})
        list_added = call({"op": "add", "path": str(zcsv)})
        alone = call({"op": "read", "doc": ""})
        (project / "pdfs").mkdir()
        (project / "pdfs" / "okafor2019.pdf").write_bytes(b"%PDF-1.4\n%%EOF\n")
        alone_pdf = call({"op": "read", "doc": ""})
        bare_added = call({"op": "add", "path": str(bare)})
        bare_view = call({"op": "read", "doc": bare_added["doc"]})
        own_added = call({"op": "add", "path": str(doc)})
        own_view = call({"op": "read", "doc": own_added["doc"]})
        claims = [r for r in own_view["rows"] if r["kind"] == "claim"]
        k1, k2 = claims[0]["key"], claims[1]["key"]
        q = call({"op": "judge", "doc": own_added["doc"], "claim": k1, "value": "q"})
        nn = call({"op": "judge", "doc": own_added["doc"], "claim": k2, "value": "N"})
        undone = call({"op": "undo", "doc": own_added["doc"]})
        wrong_doc = refused({"op": "read", "doc": "nothing-here"})
        cards = server_mod.api_home({})["traces"]
    finally:
        (server_mod.CONFIG_PATH, server_mod.ROOT_OVERRIDE, server_mod.STATE_MEMORY) = kept
    check("145: a manuscript with no reference list waits for the project's list, and a reference list alone is a table "
          "of its references with their PDFs and no claim",
          no_list == tr.NO_REF_LIST and list_added["list"]["name"] == "zotero export.csv" and "doc" not in list_added
          and alone["doc"] == "" and [r["kind"] for r in alone["rows"]] == ["uncited"] * 5 and alone["source"] == "list"
          and [r["pdf"] for r in alone_pdf["rows"]][1] is True and alone_pdf["rows"][1]["pdf_name"] == "pdfs/okafor2019.pdf",
          json.dumps(alone["rows"][0])[:300])
    check("145: a manuscript with no list of its own is matched to the project's list, Ober (2018a) and (2018b) to the "
          "lettered works, and one with its own takes the list's DOI and Zotero item where its own entry has none",
          bare_view["source"] == "list" and [r["ref"] for r in bare_view["rows"] if r["kind"] == "claim"] == ["ober2018a", "ober2018b", "vance2021"]
          and [r for r in bare_view["rows"] if r["kind"] == "claim"][1]["before"] == "Seed swaps grew in spring (Ober, 2018a)."
          and own_view["source"] == "document" and claims[0]["zotero"] == "zotero://select/library/items/UVWX6789"
          and [r for r in own_view["rows"] if r["ref"] == "vance2021"][0]["doi"] == "10.8888/ln.2021.9"
          and "Supports" not in json.dumps([r["judged"] for r in own_view["rows"]]),
          json.dumps([[r["ref"], r["kind"]] for r in bare_view["rows"]]))
    check("145: Supports, Question and Doesn't support are his, a key in either case, Undo takes back the newest, and the "
          "card on the first screen counts the claims he has judged",
          q["state"]["judged"] == "Q" and nn["state"]["judged"] == "N" and undone["undone"]["claim"] == k2
          and undone["state"]["judged"] == "" and wrong_doc == "That document is not in this project."
          and cards[0]["line"] == "seed protocol.md, and 1 more, 1 of 4 claims judged", json.dumps(cards)[:300])
    check("145: the manuscript and the reference list are only read, never written, and nothing new stands beside them",
          all(sha(p) == h for p, h in shas.items()) and sorted(p.name for p in writing.iterdir()) == ["bare draft.md", "seed protocol.md"])

    # ── E. Sift's Check references of 14 October read in place
    review = base / "Seed review"
    old = review / "reference_check"
    old.mkdir(parents=True)
    (review / "search_plan.json").write_text(json.dumps({"name": "Seed review", "versions": []}), encoding="utf-8")
    (old / "protocol.json").write_text(json.dumps({"document": str(doc), "name": doc.name, "added": "2026-10-14T10:00:00",
                                                   "references": [{"key": "okafor2019", "checked": "Y"}]}), encoding="utf-8")
    (old / "protocol.log.jsonl").write_text(json.dumps({"n": 1, "at": "2026-10-14T10:01:00", "act": "check", "ref": "okafor2019",
                                                        "checked": "Y", "by": "screener"}) + "\n", encoding="utf-8")
    kept = (server_mod.CONFIG_PATH, server_mod.ROOT_OVERRIDE, server_mod.STATE_MEMORY)
    try:
        server_mod.CONFIG_PATH = cfg
        server_mod.ROOT_OVERRIDE = str(roots)
        server_mod.STATE_MEMORY = {"recent": []}
        opened = trace_routes.api_trace_project({"op": "open", "folder": str(review)})
        legacy = trace_routes.api_trace({"op": "read", "folder": opened["project"]["folder"], "doc": "protocol"})
    finally:
        (server_mod.CONFIG_PATH, server_mod.ROOT_OVERRIDE, server_mod.STATE_MEMORY) = kept
    history = tr.history(old, "protocol")
    check("145: Sift's Check references folder is read in place as a Trace project, opened by its Sift project's folder, "
          "its old Checked line kept in its history and never read as a judgement of a claim",
          server_mod.same_folder(server_mod.abs_path(opened["project"]["folder"]), old) and opened["project"]["name"] == "Seed review"
          and not (old / tr.PROJECT_FILE).exists() and [r["judged"] for r in legacy["rows"] if r["kind"] == "claim"] == ["", "", "", ""]
          and history[0]["words"] == "The screener set the reference checked in Sift"
          and json.loads((old / "protocol.log.jsonl").read_text(encoding="utf-8").splitlines()[0])["act"] == "check",
          json.dumps(history)[:200])

    # ── F. the agents read alone, and no AI or agent ever judges
    shown = cli_mod.perform(argparse.Namespace(command="trace", folder=str(project), document=None, json=True))
    writes = [t for t in mcp_server.TOOLS if t["command"][0] == "trace" and not t["annotations"]["readOnlyHint"]]
    check("145: the command line's trace and MCP's trace_claims read alone, the reference list named, and no tool or act "
          "of an agent or the AI sets a judgement",
          shown[0]["list"]["name"] == "zotero export.csv" and len(shown[0]["documents"]) == 2 and writes == []
          and "def act(" in read(support.source("apps/trace/trace_claims.py")) and "act(" not in fn(read(support.source("apps/trace/trace_cli.py")), "cmd_trace")
          and "judged" not in read(support.source("apps/trace/trace_claims.py")).split("def find_passages", 1)[1].split("\ndef ", 1)[0].replace("judgement", ""),
          "\n".join(shown[1][:3]))

    check("145: an answer that is not the JSON asked for is an error, one line that Distil's, Sift's and Trace's AI code share",
          sift_ai.NOT_JSON is ai_mod.NOT_JSON and themes_ai.NOT_JSON is ai_mod.NOT_JSON and tr.NOT_JSON is ai_mod.NOT_JSON
          and statement_prompts.parse_suggestions("no json here") == {"error": ai_mod.NOT_JSON})
