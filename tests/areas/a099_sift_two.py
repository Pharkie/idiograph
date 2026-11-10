from __future__ import annotations

import csv
import inspect
import json
import os
import re
import shutil
import sys
from pathlib import Path

from workbook import WorkbookError

from . import support
from .support import TOOL, check, mode_is, skip


@support.as_app("sift")
def test_sift_two(scratch):
    print("\n99. Sift, round 2: the PRISMA flow in Mermaid and prisma.md, the vendored Mermaid, AI proposals behind the "
          "app's AI switch and the screening's own, the MCP tools for the review's side, and a dropped PDF")
    import base64
    import http.server
    import subprocess
    import threading
    import urllib.error
    import urllib.request
    import cli
    import sift_cli
    import locks
    import mcp_server
    import sift_mcp
    import server as server_mod
    import sift_routes
    import sift
    import sift_ai
    sys.path.insert(0, str(support.source("packaging")))
    import build_mac as build

    page = support.page_text()
    sjs = support.text("apps/sift/static/sift.js")
    # Sift's styles as its page loads them, the frame it shares with Trace first (tracestyle, 30 October 2026)
    scss = support.text("family/static/frame.css", "apps/sift/static/sift.css")
    guide = support.source("docs/agents-sift.md").read_text(encoding="utf-8")
    notice = support.source("NOTICE.md").read_text(encoding="utf-8")
    flat = lambda text: " ".join(str(text).split())
    fn = lambda src, name: src.split(f"function {name}(", 1)[1].split("\n}", 1)[0] if f"function {name}(" in src else ""
    node = shutil.which("node")

    # ── A. an invented screening on village choirs, every figure counted by hand
    base = scratch / "sift-two"
    shutil.rmtree(base, ignore_errors=True)
    folder = base / "choirs"
    folder.mkdir(parents=True)
    head = ["rec_id", "title", "authors", "year", "sources", "abstract", "proposed_decision", "proposed_reason", "grounds",
            "decision", "reason"]
    records = [
        ["C01", "Singing in the village hall", "Alto, A.", "2020", "Index A; Index B",
         "Twenty members spoke of the hall on Tuesday nights and what singing together meant.", "include", "", "what singing together meant", "", ""],
        ["C02", "Acoustics of small halls", "Bass, B.", "2019", "Index A", "Reverberation was measured in twelve halls.",
         "exclude", "E1", "Reverberation was measured", "", ""],
        ["C03", "Choir numbers since 1950", "Clef, C.", "2018", "Index B", "A count of choirs by county since 1950.",
         "exclude", "E2", "A count of choirs", "", ""],
        ["C04", "Leaving the choir", "Duet, D.", "2021", "Index A", "Former members told of the evening they stopped going.",
         "maybe", "", "the evening they stopped going", "", ""],
        ["C05", "First rehearsals", "Echo, E.", "2022", "Index B; Index A", "New singers described their first rehearsal.",
         "", "", "", "", ""],
        ["C06", "Carols on the green", "Forte, F.", "2023", "citation chasing", "Carol singers spoke of a winter on the green.",
         "", "", "", "", ""],
        ["C07", "The choir as a home", "Gamut, G.", "2024", "reference lists; citation chasing",
         "Members reflected on the choir as a second home.", "", "", "", "", ""],
        ["C08", "Pitch drift in amateur choirs", "Harmony, H.", "2017", "Index A", "A trial of tuning aids in forty choirs.",
         "exclude", "E1", "A trial of tuning aids", "", ""],
    ]
    csv_file = folder / sift.CSV_NAME

    def write_csv(rows, at=csv_file, header=head):
        with open(at, "w", encoding="utf-8", newline="") as fh:
            w = csv.writer(fh)
            w.writerow(header)
            w.writerows(rows)

    def rows_of(path=csv_file) -> list[dict]:
        with open(path, encoding="utf-8-sig", newline="") as fh:
            return list(csv.DictReader(fh))

    write_csv(records)
    os.chmod(csv_file, 0o640)
    (folder / sift.REASONS_NAME).write_text("stage,code,meaning\nta,E1,Not about lived experience\nta,E2,Not qualitative\n"
                                            "ft,F1,No full text found\nft,F2,Not an interview study\n", encoding="utf-8")
    (folder / sift.SEARCHES_NAME).write_text("date,source,interface,query,hits,records_saved,note\n"
                                             "inv,index-a,Invented A,choir*,8,6,\ninv,index-b,Invented B,choir*,5,4,\n",
                                             encoding="utf-8")

    def flow_parts(source: str) -> dict:
        """The Mermaid source read back: its nodes and their words, its links, drawn and not, and the class of each node."""
        lines = source.rstrip("\n").split("\n")
        nodes, links, hidden, classes, defs, odd = {}, [], [], {}, [], []
        for line in lines[1:]:
            s = line.strip()
            m = re.fullmatch(r'([a-z]+)\["([^"]*)"\]', s)
            if m:
                odd += [m.group(1)] if m.group(1) in nodes else []
                nodes[m.group(1)] = m.group(2)
            elif re.fullmatch(r"[a-z]+ --> [a-z]+", s):
                links.append(tuple(s.split(" --> ")))
            elif re.fullmatch(r"[a-z]+ ~~~ [a-z]+", s):
                hidden.append(tuple(s.split(" ~~~ ")))
            elif s.startswith("classDef "):
                defs.append(s.split()[1])
            elif re.fullmatch(r"class [a-z,]+ (done|now|future)", s):
                for key in s.split()[1].split(","):
                    odd += [key] if key in classes else []
                    classes[key] = s.split()[2]
            else:
                odd.append(s)
        return {"head": lines[0], "nodes": nodes, "links": links, "hidden": hidden, "classes": classes, "defs": defs, "odd": odd}

    def words(parts, key) -> str:
        return parts["nodes"].get(key, "").replace("<br/>", " | ")

    before = sift.prisma_source(sift.counts(sift.load(folder)))
    fresh = flow_parts(before)
    check("99: before any decision only identification is done, screening under way and every later stage drawn as future",
          fresh["classes"]["db"] == fresh["classes"]["dup"] == fresh["classes"]["other"] == "done"
          and fresh["classes"]["screened"] == fresh["classes"]["excluded"] == "now"
          and all(fresh["classes"][k] == "future" for k in ("sought", "missing", "assessed", "ftexcluded", "included")),
          str(fresh["classes"]))

    # the decisions, at both stages, and two PDFs
    for rec, decision, reason in (("C01", "include", ""), ("C02", "exclude", "E1"), ("C03", "exclude", "E2"), ("C04", "maybe", ""),
                                  ("C05", "include", ""), ("C06", "include", ""), ("C08", "exclude", "E1")):
        sift.decide(folder, rec, "ta", decision, reason)
    (folder / "pdfs").mkdir()
    for rec in ("C01", "C05"):
        (folder / "pdfs" / f"{rec}.pdf").write_bytes(b"%PDF-1.4\n% an invented report\n%%EOF\n")
    sift.decide(folder, "C01", "ft", "include")
    sift.decide(folder, "C05", "ft", "exclude", "F1")
    sift.decide(folder, "C04", "ft", "maybe")
    c = sift.counts(sift.load(folder))
    f = c["flow"]
    check("99: identification by hand: 10 records saved by two databases, 6 of the CSV's from them, so 4 duplicates, and 2 "
          "from other methods by their sources",
          (c["searches"]["saved"], f["databases"], f["duplicates"], f["other"]) == (10, 6, 4, 2)
          and f["others"] == {"citation chasing": 2, "reference lists": 1} and sift.other_method("citation chasing")
          and not sift.other_method("Index A; citation chasing") and not sift.other_method(""), str(f))
    check("99: screening, retrieval and eligibility by hand: 7 screened, 1 awaiting, 1 maybe, 3 excluded as E1 2 and E2 1, 4 "
          "reports sought, 2 not yet retrieved, 3 assessed, 1 awaiting, 1 excluded as F1, 1 included",
          (c["stages"]["ta"]["decided"], c["stages"]["ta"]["undecided"], c["stages"]["ta"]["maybe"], c["stages"]["ta"]["exclude"])
          == (7, 1, 1, 3) and c["stages"]["ta"]["reasons"] == {"E1": 2, "E2": 1}
          and (f["sought"], f["not_retrieved"], f["retrieved"]) == (4, 2, 2)
          and (c["stages"]["ft"]["decided"], c["stages"]["ft"]["undecided"], c["stages"]["ft"]["exclude"], c["stages"]["ft"]["include"])
          == (3, 1, 1, 1) and c["stages"]["ft"]["reasons"] == {"F1": 1}, str(c["stages"]["ft"]))
    source = sift.prisma_source(c)
    parts = flow_parts(source)
    check("99, updated 12 October (118): the flow carries those figures, Records screened every record after "
          "duplicates, each box in PRISMA's words with its count, every database by name",
          words(parts, "db") == "Records identified | from databases | (n = 10) | index-a (n = 6) | index-b (n = 4)"
          and words(parts, "dup") == "Duplicate records | removed (n = 4)"
          and words(parts, "other") == "Records identified | from other methods | (n = 2) | citation chasing (n = 2) | reference lists (n = 1)"
          and words(parts, "screened") == "Records screened | (n = 8) | To screen | (n = 1) | Maybe (n = 1)"
          and words(parts, "excluded") == "Records excluded | (n = 3) | E1 (n = 2) | E2 (n = 1)"
          and words(parts, "sought") == "Reports sought | for retrieval | (n = 4)"
          and words(parts, "missing") == "Reports not yet | retrieved (n = 2)"
          and words(parts, "assessed") == "Reports assessed | for eligibility | (n = 3) | To screen | (n = 1) | Maybe (n = 1)"
          and words(parts, "ftexcluded") == "Reports excluded | (n = 1) | F1 (n = 1)"
          # updated 13 October (128): the last box says the reports of the studies included too, as PRISMA 2020's does
          and words(parts, "included") == "Studies included | in review (n = 1) | Reports of included | studies (n = 1)", source)
    check("99: the Mermaid source is valid in shape: one flowchart, each node once, every link between nodes it holds, the "
          "side boxes held in a column of their own by links never drawn, and each node in one class of three",
          parts["head"] == "flowchart TD" and not parts["odd"] and set(parts["defs"]) == {"done", "now", "future"}
          and set(parts["classes"]) == set(parts["nodes"])
          and all(a in parts["nodes"] and b in parts["nodes"] for a, b in parts["links"] + parts["hidden"])
          and ("db", "dup") in parts["links"] and ("screened", "sought") in parts["links"] and ("assessed", "included") in parts["links"]
          and parts["hidden"] == [("dup", "excluded"), ("excluded", "missing"), ("missing", "ftexcluded")]
          and "stroke-dasharray" in source.split("classDef future", 1)[1].split("\n", 1)[0]
          and all('"' not in v and "<" not in v.replace("<br/>", "") for v in parts["nodes"].values()), str(parts["odd"]))
    check("99: the stages under way and those to come: screening, retrieval, eligibility and included all under way here",
          f["phases"] == {"identification": "done", "screening": "now", "retrieval": "now", "eligibility": "now", "included": "now"}
          and parts["classes"]["included"] == "now", str(f["phases"]))
    check("99: a code or a name with a quote, a hash or an angle bracket goes in as Mermaid's entity codes",
          sift.mermaid_text('E"1 <b> #2') == "E#quot;1 #lt;b#gt; #35;2" and sift.n_of(3) == "(n = 3)")

    # done, and a screening with no log.csv
    done = base / "done"
    done.mkdir()
    write_csv([records[1]], done / sift.CSV_NAME)
    (done / sift.REASONS_NAME).write_text((folder / sift.REASONS_NAME).read_text(encoding="utf-8"), encoding="utf-8")
    sift.decide(done, "C02", "ta", "exclude", "E1")
    ended = flow_parts(sift.prisma_source(sift.counts(sift.load(done))))
    check("99: a screening every record of which is rejected at title and abstract is done at every stage, and with no "
          "log.csv the databases' box counts the CSV's own records and no duplicates box is drawn",
          set(ended["classes"].values()) == {"done"} and "dup" not in ended["nodes"] and "other" not in ended["nodes"]
          and words(ended, "db") == "Records identified | from databases | (n = 1)"
          and ended["hidden"] == [("excluded", "missing"), ("missing", "ftexcluded")], str(ended["classes"]))

    # ── B. prisma.md, rewritten on a decision and on an undo
    md = folder / sift.PRISMA_NAME
    held_md = md.read_text(encoding="utf-8")
    check("99: prisma.md beside the CSV is a heading and one fenced mermaid block holding the flow as it stands",
          held_md == f"# PRISMA flow\n\n```mermaid\n{source}```\n" and held_md.count("```") == 2
          and sift.prisma_markdown(source).startswith("# PRISMA flow\n\n```mermaid\nflowchart TD\n"))
    sift.decide(folder, "C07", "ta", "exclude", "E2")
    after_decide = md.read_text(encoding="utf-8")
    sift.undo(folder)
    after_undo = md.read_text(encoding="utf-8")
    check("99: a decision writes prisma.md afresh, and an undo writes it back as it was",
          after_decide != held_md and "Records excluded<br/>(n = 4)<br/>E1 (n = 2)<br/>E2 (n = 2)" in after_decide
          and after_undo == held_md and not [p for p in folder.iterdir() if p.suffix == ".tmp"]
          and "write_atomic(path, text)" in inspect.getsource(sift.write_prisma)
          and "write_prisma(sc.folder, out[\"prisma\"])" in inspect.getsource(sift.settled)
          and all("settled(sc, entries, rec)" in inspect.getsource(f) for f in (sift.decide, sift.note, sift.undo)))
    unchanged = md.stat().st_mtime_ns
    nothing = sift.write_prisma(folder, source)
    check("99: a flow that has not moved is not written again", nothing is False and md.stat().st_mtime_ns == unchanged)
    md.unlink()
    opened_src = sift.refresh_prisma(folder)
    check("99: opening a screening writes prisma.md when it is missing, the same flow", md.read_text(encoding="utf-8") == held_md
          and opened_src == source)
    code, out, _ = cli.run(["sift", str(folder), "prisma"])
    code_j, out_j, _ = cli.run(["sift", str(folder), "prisma", "--json"])
    check("99: sift <folder> prisma prints the source, and --json gives it with the file's name",
          code == 0 and out == source and code_j == 0 and support.plain(json.loads(out_j))["prisma"] == source
          and json.loads(out_j)["file"] == "prisma.md", out[:120])

    # ── C. the vendored Mermaid, its licence, and what the bundle carries
    vendor = support.source("apps/sift/static/vendor/mermaid.min.js").parent
    mjs = (vendor / "mermaid.min.js").read_bytes() if (vendor / "mermaid.min.js").is_file() else b""
    licence = (vendor / "LICENSE-mermaid.txt").read_text(encoding="utf-8") if (vendor / "LICENSE-mermaid.txt").is_file() else ""
    check("99: Mermaid 11.14.0 is vendored in static/vendor with its MIT licence beside it, and NOTICE.md names it",
          b'version:"11.14.0"' in mjs and len(mjs) > 1_000_000 and b"sourceMappingURL" not in mjs
          and "Mermaid 11.14.0" in licence and "The MIT License" in licence and "Knut Sveidqvist" in licence
          and "Mermaid 11.14.0" in notice and "MIT License" in notice.split("Mermaid", 1)[1].split("\n", 1)[0])
    check("99: Sift's bundle's list names both files, Sift's own, a build without them stops, and sift_ai is among its "
          "modules, none of them in Idiograph's",
          {"static/vendor/mermaid.min.js", "static/vendor/LICENSE-mermaid.txt"}
          <= {Path(p).as_posix() for p in build.vendored("sift")}
          and all(Path(p).relative_to("static").as_posix() in build.static_files("sift") for p in build.vendored("sift"))
          and "vendor/mermaid.min.js" not in build.static_files("idiograph")
          and not any("mermaid" in Path(p).name for p in build.vendored("idiograph"))
          and "sift_ai" in build.modules("sift") and "sift_ai" not in build.modules("idiograph")
          and "missing = [str(item) for item in vendored(app)" in inspect.getsource(build.bundle_inputs)
          and "bundle_inputs(stage, app)" in inspect.getsource(build.write_spec))
    check("99: the page loads it from the app the first time the flow is drawn, never from the web, and no script tag waits for it",
          "const SF_MERMAID = '/vendor/mermaid.min.js';" in sjs and "tag.src = SF_MERMAID;" in fn(sjs, "sfMermaid")
          and not re.search(r"<script[^>]*mermaid", page, flags=re.I) and not re.search(r"https?://", fn(sjs, "sfMermaid")))
    check("99, updated 17 October, later (165): Mermaid is set strict, and the flow drawn again when the theme changes",
          "securityLevel: 'strict'" in fn(sjs, "sfFlowDraw")
          and "document.addEventListener('idiograph-theme', () => { if (sfShown()) sfFlow(); });" in fn(sjs, "sfBoot")
          and "sfFlowTake(data.prisma);" in fn(sjs, "sfLand"))

    # ── D. the AI settings, per screening, off by default
    other = base / "other"
    other.mkdir()
    write_csv(records[:2], other / sift.CSV_NAME)
    first = sift_ai.settings(folder)
    saved = sift_ai.save_settings(folder, True, "Judge {stage} against {codes}.")
    check("99: AI proposals are off on a new screening, and its switch and prompt are kept in sift.json beside its CSV, "
          "another screening's left off",
          first == {"ai_proposals": False, "prompt": ""} and not (other / sift_ai.SETTINGS_NAME).exists()
          and saved == {"ai_proposals": True, "prompt": "Judge {stage} against {codes}."}
          and json.loads((folder / "sift.json").read_text(encoding="utf-8")) == {"ai_proposals": True, "prompt": "Judge {stage} against {codes}."}
          and sift_ai.settings(other) == {"ai_proposals": False, "prompt": ""})
    sift_ai.save_settings(folder, prompt=sift_ai.DEFAULT_PROMPT + "\n")
    check("99: a prompt the same as the default is kept as empty, so a later default reaches it, and the prompt sent is the default",
          sift_ai.settings(folder) == {"ai_proposals": True, "prompt": ""} and sift_ai.prompt_of(sift_ai.settings(folder)) == sift_ai.DEFAULT_PROMPT)
    told = sift_ai.system_prompt(sift_ai.DEFAULT_PROMPT, "ta", sift.reasons(folder)["ta"])
    check("99: the default prompt is plain and by the book: one record's title and abstract against the stage's codes, include, "
          "maybe or exclude, a code, and grounds word for word, in strict JSON",
          "{stage}" in sift_ai.DEFAULT_PROMPT and "{codes}" in sift_ai.DEFAULT_PROMPT and "at the title and abstract stage" in told
          and "E1: Not about lived experience\nE2: Not qualitative" in told and "word for word" in told
          and "take maybe over a guess" in told and told.endswith(sift_ai.SHAPE) and chr(0x2014) not in sift_ai.DEFAULT_PROMPT + sift_ai.SHAPE
          and ";" not in sift_ai.DEFAULT_PROMPT and sift_ai.system_prompt('Say {"decision": x}', "ft", []) == 'Say {"decision": x}')
    parsed = [sift_ai.parse(t, sift.reasons(folder)["ta"], "ta") for t in (
        '```json\n{"decision": "reject", "reason": "e2", "grounds": "A count  of choirs"}\n```',
        '{"decision": "maybe", "reason": "E1", "grounds": "x"}', '{"decision": "exclude", "reason": "E9"}',
        '{"decision": "perhaps"}', "no json here")]
    check("99: an answer is read strictly: the files' words, a reject's code matched to the stage's own, none on a maybe, and "
          "anything else one line",
          parsed[0] == {"decision": "exclude", "reason": "E2", "grounds": "A count of choirs"}
          and parsed[1] == {"decision": "maybe", "reason": "", "grounds": "x"}
          and parsed[2] == {"error": "The answer gave E9, which is no reason code at title and abstract."}
          and parsed[3] == {"error": sift_ai.NO_DECISION} and parsed[4] == {"error": sift_ai.NOT_JSON}, str(parsed))

    # ── E. the AI columns, under the lock, the review's never, and the counts split by source
    before_cells = {r["rec_id"]: {k: r.get(k, "") for k in head} for r in rows_of()}
    log_before = (folder / sift.LOG_NAME).read_bytes()
    busy = ""
    with locks.held(sift.lock_path(folder)):
        try:
            sift.write_ai(folder, "C07", "ta", "include", wait=0.2)
        except WorkbookError as exc:
            busy = str(exc)
    got = sift.write_ai(folder, "C07", "ta", "include", "E1", "the choir as a second home")
    after = {r["rec_id"]: r for r in rows_of()}
    check("99: Sift's own proposal goes in ai_proposed_decision, ai_proposed_reason and ai_grounds, added after the last column, "
          "under screening.lock, no reason on an accept",
          busy == locks.BUSY and list(after["C07"])[-3:] == ["ai_proposed_decision", "ai_proposed_reason", "ai_grounds"]
          and (after["C07"]["ai_proposed_decision"], after["C07"]["ai_proposed_reason"], after["C07"]["ai_grounds"])
          == ("include", "", "the choir as a second home")
          and inspect.getsource(sift.write_ai).index("locks.held(") < inspect.getsource(sift.write_ai).index("sc = load(folder)"))
    check("99: the review's proposal columns, the decisions and the log are untouched by it, and the CSV keeps its file mode",
          all({k: after[r][k] for k in head} == before_cells[r] for r in before_cells)
          and (folder / sift.LOG_NAME).read_bytes() == log_before and mode_is(csv_file, 0o640)
          and got["record"]["stages"]["ta"]["proposals"] == [dict(got["record"]["stages"]["ta"]["proposal"])]
          and got["record"]["stages"]["ta"]["proposal"]["source"] == "sift")
    sift.write_ai(folder, "C04", "ft", "exclude", "F2", "they stopped going")
    view = sift.record_view(sift.load(folder), sift.states(sift.read_log(folder)), "C04")
    check("99: at full text the ft_ai_ three, and a record with both shows the review's first, which Enter takes and the log records",
          rows_of()[3]["ft_ai_proposed_decision"] == "exclude" and rows_of()[3]["ft_ai_proposed_reason"] == "F2"
          and [p["source"] for p in view["stages"]["ta"]["proposals"]] == ["csv"]
          and [p["source"] for p in view["stages"]["ft"]["proposals"]] == ["sift"]
          and "ai_proposed_decision" not in dict(view["more"]) and "ft_ai_grounds" not in dict(view["more"]))
    sift.write_ai(folder, "C01", "ta", "maybe", "", "Tuesday nights")
    both = sift.record_view(sift.load(folder), {}, "C01")["stages"]["ta"]
    check("99: with both, the proposals come in order, CSV then Sift, and each one's grounds are found in the abstract",
          [p["source"] for p in both["proposals"]] == ["csv", "sift"] and both["proposal"]["source"] == "csv"
          and all(p["found"] is True for p in both["proposals"]))
    sift.decide(folder, "C07", "ta", "include")
    line = json.loads((folder / sift.LOG_NAME).read_text(encoding="utf-8").splitlines()[-1])
    split = sift.counts(sift.load(folder))["stages"]["ta"]["sources"]
    rows = sift.count_rows(sift.counts(sift.load(folder)))
    check("99: a decision on a record with Sift's proposal alone records it with source sift, and the counts and the export "
          "split by it",
          line["proposal"] == {"decision": "include", "reason": "", "source": "sift"} and split["sift"]["matched"] == 1
          and ["title and abstract", "matched the proposal from sift", 1] in rows and "csv" in split)
    sift.undo(folder)

    # ── F. the server: the app's switch, the screening's, the call count before a batch and a stub model
    calls = []

    class Stub(http.server.BaseHTTPRequestHandler):
        """A local model in Ollama's shape on this machine, every answer invented."""
        def log_message(self, *args):
            pass

        def do_POST(self):
            payload = json.loads(self.rfile.read(int(self.headers.get("Content-Length") or 0)) or b"{}")
            user = next((m["content"] for m in payload.get("messages", []) if m.get("role") == "user"), "")
            calls.append({"user": user, "system": payload["messages"][0]["content"], "model": payload.get("model")})
            rec = re.search(r"Record (\S+?),", user)
            answer = {"decision": "exclude", "reason": "E2", "grounds": "first rehearsal"} if rec and rec.group(1) == "C05" \
                else {"decision": "maybe", "reason": "", "grounds": "a winter on the green"}
            body = json.dumps({"message": {"content": json.dumps(answer)}, "done": True, "done_reason": "stop"}).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

    try:
        stub = http.server.ThreadingHTTPServer(("127.0.0.1", 8790), Stub)
    except OSError:
        stub = http.server.ThreadingHTTPServer(("127.0.0.1", 0), Stub)
    threading.Thread(target=stub.serve_forever, kwargs={"poll_interval": 0.05}, daemon=True).start()
    stub_url = f"http://127.0.0.1:{stub.server_address[1]}"
    on_cfg = base / "config-on.json"
    off_cfg = base / "config-off.json"
    on_cfg.write_text(json.dumps({"interviewer": "Adam", "ai_suggest": True, "ai_provider": "local", "local_url": stub_url,
                                  "local_model": "stub"}), encoding="utf-8")
    off_cfg.write_text(json.dumps({"interviewer": "Adam", "ai_suggest": False, "ai_provider": "local", "local_url": stub_url,
                                   "local_model": "stub"}), encoding="utf-8")
    kept = (server_mod.CONFIG_PATH, server_mod.ROOT_OVERRIDE, server_mod.STATE_MEMORY)
    empty_root = base / "no-cases"
    empty_root.mkdir()

    def refusal(body) -> str:
        try:
            got = sift_routes.api_sift(body)
        except WorkbookError as exc:
            return str(exc)
        return got.get("error", "") if isinstance(got, dict) else ""

    try:
        server_mod.ROOT_OVERRIDE = str(empty_root)
        server_mod.STATE_MEMORY = {"recent": []}
        server_mod.CONFIG_PATH = off_cfg
        sift_routes.api_sift_review({"op": "open", "folder": str(folder)})
        sift_ai.save_settings(folder, False)
        read_off = sift_routes.api_sift({"op": "read", "folder": str(folder)})
        refused_off = [refusal({"op": op, "folder": str(folder), "rec_id": "C07", "stage": "ta", "round": "undecided",
                                "ai_proposals": True}) for op in ("settings", "plan", "propose")]
        check("99: with the app's AI switch off the screen hears no AI setting and every AI act is refused, nothing asked",
              read_off["config"] == {"ai_suggest": False} and read_off["ai"] is None
              and refused_off == [sift_ai.OFF] * 3 and not calls and sift_ai.settings(folder)["ai_proposals"] is False
              and sift_routes.api_sift({"op": "stamp", "folder": str(folder)})["config"] == {"ai_suggest": False}
              and "aiOn(now.config) !== SF.aiMaster" in fn(sjs, "sfFresh"), str(refused_off))
        decided_off = sift_routes.api_sift({"op": "decide", "folder": str(folder), "rec_id": "C07", "stage": "ta",
                                           "decision": "include"})
        line = json.loads((folder / sift.LOG_NAME).read_text(encoding="utf-8").splitlines()[-1])
        check("99: and with it off the log still records the proposal and its source",
              line["proposal"]["source"] == "sift" and decided_off["changed"] and "prisma" in decided_off)
        sift_routes.api_sift({"op": "undo", "folder": str(folder)})
        server_mod.CONFIG_PATH = on_cfg
        read_on = sift_routes.api_sift({"op": "read", "folder": str(folder)})
        refused_sift = [refusal({"op": op, "folder": str(folder), "rec_id": "C07", "stage": "ta", "round": "undecided"})
                        for op in ("plan", "propose")]
        check("99: with the app's switch on and the screening's off, the screen has its settings and the model's name, and "
              "no proposal is asked",
              read_on["config"] == {"ai_suggest": True} and read_on["ai"]["on"] is False
              and read_on["ai"]["model_name"] == "stub on this machine" and read_on["ai"]["prompt"] == sift_ai.DEFAULT_PROMPT
              and read_on["ai"]["default"] == sift_ai.DEFAULT_PROMPT and refused_sift == [sift_ai.SIFT_OFF] * 2 and not calls,
              str(refused_sift))
        turned = sift_routes.api_sift({"op": "settings", "folder": str(folder), "ai_proposals": True})
        held_plan = sift_routes.api_sift({"op": "plan", "folder": str(folder), "stage": "ta", "round": "undecided"})
        # C07's proposal from Sift taken out again, as another writer would, so the round has one to ask about
        with locks.held(sift.lock_path(folder)):
            rows_before = rows_of()
            with open(csv_file, "w", encoding="utf-8", newline="") as fh:
                w = csv.DictWriter(fh, fieldnames=list(rows_before[0].keys()))
                w.writeheader()
                w.writerows([dict(r, ai_proposed_decision="", ai_proposed_reason="", ai_grounds="") if r["rec_id"] == "C07" else r
                             for r in rows_before])
        os.chmod(csv_file, 0o640)
        plan = sift_routes.api_sift({"op": "plan", "folder": str(folder), "stage": "ta", "round": "undecided"})
        check("99: the screening's switch turned on from its settings, and the plan for the round counts its calls before any "
              "is made: its undecided records with no proposal from Sift",
              turned["ai"]["on"] is True and held_plan["calls"] == 0 and held_plan["ids"] == []
              and plan == {"ids": ["C07"], "calls": 1, "stage": "ta", "round": "undecided"}
              and sift_ai.plan(folder, "ta", "all")["ids"] == ["C07"] and not calls, str((held_plan, plan)))
        asked = sift_routes.api_sift({"op": "propose", "folder": str(folder), "rec_id": "C07", "stage": "ta"})
        mine = {r["rec_id"]: r for r in rows_of()}
        check("99: a proposal for this record goes to the provider in the app's settings, here a stub, with the record, the "
              "stage's codes and the prompt, and lands in Sift's own columns",
              len(calls) == 1 and calls[0]["model"] == "stub" and "Record C07, at title and abstract." in calls[0]["user"]
              and "Members reflected on the choir as a second home." in calls[0]["user"]
              and "E2: Not qualitative" in calls[0]["system"] and asked["asked"] == {"rec_id": "C07", "stage": "ta"}
              and mine["C07"]["ai_proposed_decision"] == "maybe" and mine["C07"]["proposed_decision"] == ""
              and mine["C07"]["decision"] == "" and asked["record"]["stages"]["ta"]["proposal"]["source"] == "sift"
              and sift_routes.api_sift({"op": "plan", "folder": str(folder), "stage": "ta", "round": "undecided"})["calls"] == 0,
              str(calls[:1]))
        bad = refusal({"op": "propose", "folder": str(folder), "rec_id": "C05", "stage": "ft"})
        ft_answer = sift_routes.api_sift({"op": "propose", "folder": str(folder), "rec_id": "C06", "stage": "ft"})
        check("99: an answer that names a code of another stage is refused in one line and nothing written, and at full text "
              "the ft_ai_ three are written",
              bad == "The answer gave E2, which is no reason code at full text." and rows_of()[4].get("ft_ai_proposed_decision", "") == ""
              and ft_answer["record"]["stages"]["ft"]["proposal"]["decision"] == "maybe"
              and {r["rec_id"]: r for r in rows_of()}["C06"]["ft_ai_proposed_decision"] == "maybe", bad)
    finally:
        (server_mod.CONFIG_PATH, server_mod.ROOT_OVERRIDE, server_mod.STATE_MEMORY) = kept
        stub.shutdown()
        stub.server_close()

    # ── G. the page: the switch, the controls, the sparkles on them alone, the count before a batch
    screen = page.split('<section id="sift"', 1)[1].split("</section>", 1)[0] if '<section id="sift"' in page else ""
    sift_pane = page.split('id="pane-sift"', 1)[1].split("</section>", 1)[0] if 'id="pane-sift"' in page else ""
    batch = fn(sjs, "sfAiAll")
    check("99: a proposal for the round asks the plan, says its calls and the model in the question card, and only then asks",
          batch.index("op: 'plan'") < batch.index("await sfAsk(") < batch.index("op: 'propose'")
          and "'sift.ai.ask_line', { n: plan.calls" in batch and "SF.ai.model_name" in batch and "if (SF.batch.stop) break;" in batch
          and "if (SF.batch) { SF.batch.stop = true;" in batch)
    check("99, updated 12 October (117, 121) and 14 October (138): every AI part follows the app's switch: aiOn(config), no "
          "AI suggestion drawn, no "
          "Differs from the proposal in the Decision filter, no matched count, and with it on none until a decision meets a "
          "proposal, no AI setting, no Enter key while no suggestion shows and no AI control with it off, the bench under "
          "Sift in Settings with the AI proposals, a suggestion by keyword rules or that says nothing shown either way",
          "SF.aiMaster = aiOn(data.config);" in fn(sjs, "sfTake") and "SF.ai = SF.aiMaster ? data.ai || null : null;" in fn(sjs, "sfTake")
          and "const props = sfSuggestions(st);" in fn(sjs, "sfDraw")
          and "const sfSuggestions = (st) => ((st && st.proposals) || []).filter((p) => SF.aiMaster || !sfSuggestionOf(p).ai).slice(0, 2);" in sjs
          and "st.proposed = !!SF.aiMaster && (st.proposals || []).length > 0;" in fn(sjs, "sfMark")
          and "(SF.aiMaster && n('matched') + n('overruled') ? `<span class=\"sf-against\">" in fn(sjs, "sfBar")
          and "if (!rec || !b || SF.benchBusy || !$('set-ai').checked) return;" in fn(sjs, "sfBenchTry")
          and "$('sf-key-enter').hidden = !SF.records.some((r) => sfSuggestions(sfStage(r)).length);" in fn(sjs, "sfBar")
          and "const prop = sfSuggestions(sfStage(r))[i] || {};" in fn(sjs, "sfTakeProposal")
          and "const sfAiReady = () => !!(SF.aiMaster && SF.ai && SF.ai.on);" in sjs and "$('sf-ai').hidden = !sfAiReady() || !r;" in fn(sjs, "sfAiDraw")
          and 'id="sf-settings" type="button" title="Sift\'s settings" aria-label="Sift\'s settings">' in screen
          and 'id="sf-bench"' in sift_pane.split('<div id="sfa-block" data-ai-set>', 1)[-1].split('<div class="zot"', 1)[0]
          and 'id="sf-ai" hidden>' in screen and 'id="sf-proposal" role="group" aria-labelledby="sf-prop-title" hidden>' in screen)
    check("99: a proposal's answer lands its proposals alone, so a decision made while it was asked is never drawn back",
          "r.stages[stage].proposals = fresh.stages[stage].proposals;" in fn(sjs, "sfLandProposal")
          and "decision" not in fn(sjs, "sfLandProposal").split("for (const stage", 1)[1]
          and "sfLandProposal(await api('/api/sift', { op: 'propose'" in fn(sjs, "sfAiOne"))
    card = page.split('id="pane-sift"', 1)[1].split("</section>", 1)[0].split('id="sfa-block"', 1)[1] if 'id="sfa-block"' in page else ""
    # Sift's parts of the shell, from app.js since the family codebase's third build (22 October 2026)
    sset = support.text("apps/sift/static/sift_settings.js")
    check("99, 9 October: under Sift in Settings, a screening's switch, the prompt, Reset to default and the model, saved to its "
          "route, and Sift's cog opens Settings there, the bench trying the prompt as the box holds it",
          "AI proposals for this screening</label>" in card and 'id="sfa-prompt" class="prompt-box"' in card
          and ">Reset to default</button>" in card and 'id="sfa-model"' in card
          and "out.push({ op: 'settings', folder, ai_proposals: h.on, prompt: h.prompt });" in fn(sset, "sfaSaves")
          and "$('sf-settings').onclick = () => openSettings('sift');" in sjs and "prompt: $('sfa-prompt').value" in fn(sjs, "sfBenchTry")
          and "sfSetOpen" not in sjs and "sfSetSave" not in sjs)
    if node:
        script = scratch / "sift-two-marks.js"
        script.write_text("function sfMarks(" + fn(sjs, "sfMarks").split("function sfMarks(", 1)[-1] + "\n}\n"
                          + "console.log(JSON.stringify([sfMarks([{marks: [[10, 20]]}, {marks: [[15, 30], [2, 4]]}]), sfMarks([])]));\n",
                          encoding="utf-8")
        ran = subprocess.run([node, str(script)], capture_output=True, text=True, encoding="utf-8", timeout=60)
        check("99: in node, the grounds of both proposals are marked as one run, an overlap joined",
              ran.returncode == 0 and json.loads(ran.stdout or "null") == [[[2, 4], [10, 30]], []], (ran.stdout or ran.stderr)[:200])
    else:
        skip("99: the marks of both proposals in node", "no node on this machine")

    # ── H. the MCP tools and the command line for the review's side
    names = [t["name"] for t in sift_mcp.SIFT_TOOLS]
    by = {t["name"]: t for t in sift_mcp.SIFT_TOOLS}
    readers = ["sift_list", "sift_show", "sift_counts", "sift_export", "sift_prisma", "sift_form"]
    check("99, updated 13 October, later (129): eight MCP tools for a screening, each a command of sift, its folder required, "
          "six only reading, sift_form among them",
          names == readers + ["sift_add", "sift_propose"] and all(t in mcp_server.TOOLS for t in sift_mcp.SIFT_TOOLS)
          and all(t["command"][0] == "sift" and t["command"][1] in sift_cli.SIFT_ACTS for t in sift_mcp.SIFT_TOOLS)
          and all("folder" in t["inputSchema"]["required"] and t["inputSchema"]["additionalProperties"] is False for t in sift_mcp.SIFT_TOOLS)
          and all(by[n]["annotations"]["readOnlyHint"] is True and "dry_run" not in by[n]["inputSchema"]["properties"] for n in readers)
          and all(by[n]["annotations"]["readOnlyHint"] is False and "dry_run" in by[n]["inputSchema"]["properties"]
                  and "request" not in by[n]["inputSchema"]["properties"] for n in ("sift_add", "sift_propose"))
          and by["sift_propose"]["annotations"]["destructiveHint"] is True and by["sift_add"]["annotations"]["destructiveHint"] is False
          and by["sift_list"]["inputSchema"]["properties"]["round"]["enum"]
          == ["to-screen", "maybe", "yes", "include", "no", "exclude", "all", "differs", "apart", "undecided", "accepted",
              "rejected"]
          and all(sift.round_key(v) in sift.FILTERS + (sift.APART,)
                  for v in by["sift_list"]["inputSchema"]["properties"]["round"]["enum"])
          and all(chr(0x2014) not in t["description"] and ";" not in t["description"] and len(t["description"]) > 60
                  for t in sift_mcp.SIFT_TOOLS))
    check("99: no tool and no act decides, notes or undoes a record, and the guide and the server's instructions say so",
          not ({"decide", "note", "undo"} & set(sift_cli.SIFT_ACTS))
          and not any({"decision", "reason", "note"} & set(t["inputSchema"]["properties"]) for t in sift_mcp.SIFT_TOOLS)
          and "No tool decides, notes or undoes a record, which are his alone in Sift." in mcp_server.instructions("sift")
          and "Never decide, note or undo a record." in flat(guide)
          and "In a screening, never decide, note or undo a record." in mcp_server.instructions("sift"))

    def snapshot(at: Path) -> dict:
        return {p.relative_to(at).as_posix(): p.read_bytes() for p in sorted(at.rglob("*")) if p.is_file() and p.name != sift.LOCK_NAME}

    srv = mcp_server.Server(str(empty_root), app="sift")
    srv.receive(json.dumps({"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {"clientInfo": {"name": "claude-ai"}}}))

    def tool_call(name, **given):
        return support.plain_result(srv.receive(json.dumps({"jsonrpc": "2.0", "id": 2, "method": "tools/call",
                                                            "params": {"name": name, "arguments": given}}))["result"])

    held = snapshot(folder)
    answers = {n: tool_call(n, folder=str(folder)) for n in ("sift_counts", "sift_export", "sift_prisma")}
    answers["sift_list"] = tool_call("sift_list", folder=str(folder), stage="ft", round="all")
    answers["sift_show"] = tool_call("sift_show", folder=str(folder), rec_id="C01")
    check("99: the five reading tools answer as the command line does and write nothing, the export its rows and no file",
          all(a["isError"] is False for a in answers.values()) and snapshot(folder) == held
          and not (folder / sift.COUNTS_NAME).exists() and answers["sift_prisma"]["structuredContent"]["prisma"] == sift.prisma_source(sift.counts(sift.load(folder)))
          and answers["sift_export"]["structuredContent"]["rows"] == sift.count_rows(sift.counts(sift.load(folder)))
          and [r["rec_id"] for r in answers["sift_list"]["structuredContent"]["records"]] == ["C01", "C04", "C05", "C06"]
          and [e["act"] for e in answers["sift_show"]["structuredContent"]["history"]] == ["decide", "decide"]
          and answers["sift_show"]["content"][0]["text"].startswith("C01: Singing in the village hall")
          and answers["sift_counts"]["structuredContent"]["counts"]["flow"]["duplicates"] == 4,
          str({k: a["content"][0]["text"][:60] for k, a in answers.items() if a["isError"]}))
    clash = tool_call("sift_add", folder=str(folder), records=[{"rec_id": "C03", "title": "A clash"}])
    unknown = tool_call("sift_add", folder=str(folder), records=[{"title": "A row", "decision": "include", "colour": "red"}])
    dry = tool_call("sift_add", folder=str(folder), records=[{"title": "Tenors wanted"}], dry_run=True)
    check("99: add records is refused on a clash, on a decision column or a column the CSV lacks, nothing written, and its "
          "dry run writes nothing",
          clash["isError"] and "C03 is in screening.csv already." in clash["content"][0]["text"]
          and "Nothing was added." in clash["content"][0]["text"] and unknown["isError"]
          and "decision is Sift's to write, never a new record's." in unknown["content"][0]["text"]
          and "screening.csv has no column colour." in unknown["content"][0]["text"]
          and dry["isError"] is False and dry["structuredContent"]["added"] == ["C09"] and snapshot(folder) == held,
          clash["content"][0]["text"])
    held_rows = rows_of()
    added = tool_call("sift_add", folder=str(folder), records=[{"title": "Tenors wanted", "sources": ["Index A", "citation chasing"],
                                                                 "year": 2025, "abstract": "Two tenors spoke of joining late."},
                                                                {"rec_id": "X1", "title": "A record of its own id"}])
    grown = rows_of()
    check("99: added records go at the foot under the lock, rec_id continuing the sequence, every row before them kept, and "
          "prisma.md written afresh",
          added["isError"] is False and added["structuredContent"]["added"] == ["C09", "X1"]
          and [r["rec_id"] for r in grown] == ["C01", "C02", "C03", "C04", "C05", "C06", "C07", "C08", "C09", "X1"]
          and grown[8]["sources"] == "Index A; citation chasing" and grown[8]["year"] == "2025" and grown[8]["decision"] == ""
          and [{k: r[k] for k in held_rows[0]} for r in grown[:8]] == held_rows
          and "To screen<br/>(n = 3)" in (folder / sift.PRISMA_NAME).read_text(encoding="utf-8")
          and "removed (n = 2)" in (folder / sift.PRISMA_NAME).read_text(encoding="utf-8")
          and "locks.held(lock_path(folder), wait)" in inspect.getsource(sift.add_records)
          and sift.next_ids(["R001", "R068"], 2) == ["R069", "R070"] and sift.next_ids(["a", "b"], 1) is None
          and mode_is(csv_file, 0o640), added["content"][0]["text"])
    wrong = tool_call("sift_propose", folder=str(folder), stage="ta",
                      proposals=[{"rec_id": "C09", "decision": "reject", "reason": "F1"}, {"rec_id": "C99", "decision": "include"}])
    wrote = tool_call("sift_propose", folder=str(folder), stage="ta",
                      proposals=[{"rec_id": "C09", "decision": "reject", "reason": "E2", "grounds": "joining late"},
                                 {"rec_id": "X1", "decision": "maybe", "reason": "E1", "grounds": "words it never holds"}])
    ft = tool_call("sift_propose", folder=str(folder), stage="ft", proposals=[{"rec_id": "C06", "decision": "include"}])
    now = {r["rec_id"]: r for r in rows_of()}
    check("99: the review's proposals go into its own columns for named records, a wrong code or a record the CSV lacks "
          "refusing the whole write, never a decision, Sift's columns or the log",
          wrong["isError"] and "C09: F1 is not a reason code at title and abstract." in wrong["content"][0]["text"]
          and "There is no record C99 in screening.csv." in wrong["content"][0]["text"]
          and wrote["isError"] is False and (now["C09"]["proposed_decision"], now["C09"]["proposed_reason"], now["C09"]["grounds"])
          == ("exclude", "E2", "joining late") and (now["X1"]["proposed_decision"], now["X1"]["proposed_reason"]) == ("maybe", "")
          and wrote["structuredContent"]["not_found"] == ["X1"] and now["C09"]["decision"] == "" and now["C09"]["ai_proposed_decision"] == ""
          and ft["isError"] is False and now["C06"]["ft_proposed_decision"] == "include"
          and (folder / sift.LOG_NAME).read_bytes().count(b"\n") == held[sift.LOG_NAME].count(b"\n")
          and "locks.held(lock_path(folder), wait)" in inspect.getsource(sift.propose_review), wrong["content"][0]["text"])
    list_code, list_out, _ = cli.run(["sift", str(folder), "list", "--round", "all"])
    show_code, show_out, _ = cli.run(["sift", str(folder), "show", "C09"])
    add_file = base / "more.json"
    add_file.write_text(json.dumps({"records": [{"title": "Altos at the back"}]}), encoding="utf-8")
    add_code, add_out, _ = cli.run(["sift", str(folder), "add", "--from", str(add_file), "--dry-run"])
    check("99: the command line has the same acts, list, show and add among them, add's dry run naming the rec_id it would take",
          list_code == 0 and "C09  To screen  Tenors wanted (2025), proposed No E2 (csv)" in list_out
          and show_code == 0 and "Title and abstract: To screen, proposed No E2 (csv)." in show_out
          and add_code == 0 and add_out.strip() == "It would add 1 record at the foot of screening.csv: C10."
          and [r["rec_id"] for r in rows_of()][-1] == "X1", add_out + list_out[:200])

    # ── I. a dropped PDF, kept, the replacement asked first
    pdf = b"%PDF-1.4\n% an invented report on altos\n%%EOF\n"
    pdf2 = b"%PDF-1.4\n% a second invented report\n%%EOF\n"
    md_before = (folder / sift.PRISMA_NAME).read_text(encoding="utf-8")
    kept_pdf = sift.save_pdf(folder, "C06", pdf)
    first_bytes, md_after = (folder / "pdfs" / "C06.pdf").read_bytes(), (folder / sift.PRISMA_NAME).read_text(encoding="utf-8")
    again = sift.save_pdf(folder, "C06", pdf2)
    second_bytes = (folder / "pdfs" / "C06.pdf").read_bytes()
    replaced = sift.save_pdf(folder, "C06", pdf2, replace=True)
    not_pdf = ""
    try:
        sift.save_pdf(folder, "C04", b"<html>not a pdf</html>")
    except sift.SiftError as exc:
        not_pdf = str(exc)
    check("99: a dropped PDF is kept as pdfs/<rec_id>.pdf for the record showing and the flow's reports retrieved move",
          kept_pdf["saved"] is True and kept_pdf["exists"] is False and first_bytes == pdf
          and kept_pdf["record"]["pdf"] is True and "Reports not yet<br/>retrieved (n = 1)" in kept_pdf["prisma"]
          and md_after != md_before and "Reports not yet<br/>retrieved (n = 1)" in md_after,
          str({k: v for k, v in kept_pdf.items() if k in ("saved", "exists")}) + kept_pdf["prisma"].split("missing", 1)[-1][:60])
    check("99: one already there is replaced only when asked, and anything that is not a PDF is refused",
          again["exists"] is True and again["saved"] is False and second_bytes == pdf
          and replaced["saved"] is True and replaced["exists"] is True
          and (folder / "pdfs" / "C06.pdf").read_bytes() == pdf2 and not_pdf == "That file is not a PDF, so it was not kept."
          and not (folder / "pdfs" / "C04.pdf").exists() and not [p for p in (folder / "pdfs").iterdir() if p.suffix == ".tmp"])
    try:
        server_mod.CONFIG_PATH = off_cfg
        server_mod.ROOT_OVERRIDE = str(empty_root)
        server_mod.STATE_MEMORY = {"recent": []}
        sift_routes.api_sift_review({"op": "open", "folder": str(folder)})
        by_route = sift_routes.api_sift({"op": "pdf", "folder": str(folder), "rec_id": "C04",
                                        "data": base64.b64encode(pdf).decode("ascii")})
        asked_first = sift_routes.api_sift({"op": "pdf", "folder": str(folder), "rec_id": "C04",
                                           "data": base64.b64encode(pdf2).decode("ascii")})
        garbled = refusal({"op": "pdf", "folder": str(folder), "rec_id": "C04", "data": "not base64!"})
        httpd = http.server.ThreadingHTTPServer(("127.0.0.1", 0), server_mod.Handler)
        threading.Thread(target=httpd.serve_forever, kwargs={"poll_interval": 0.05}, daemon=True).start()
        try:
            with urllib.request.urlopen(f"http://127.0.0.1:{httpd.server_address[1]}/vendor/mermaid.min.js", timeout=10) as r:
                served = (r.status, r.headers.get("Content-Type", ""), len(r.read()))
        except urllib.error.URLError as exc:
            served = (0, str(exc), 0)
        finally:
            httpd.shutdown()
            httpd.server_close()
    finally:
        (server_mod.CONFIG_PATH, server_mod.ROOT_OVERRIDE, server_mod.STATE_MEMORY) = kept
    drop = fn(sjs, "sfDropPdf")
    check("99: the route keeps a PDF sent in base64, answers exists for one already there and writes nothing, and refuses a "
          "garbled one, and the page asks before it sends replace",
          by_route["saved"] is True and (folder / "pdfs" / "C04.pdf").read_bytes() == pdf and asked_first["exists"] is True
          and asked_first["saved"] is False and garbled == "That file did not arrive whole, so it was not kept."
          and drop.index("let got = await ask(false);") < drop.index("await sfAsk('Replace the PDF'") < drop.index("got = await ask(true);")
          and "Nothing is fetched from the web." in sjs and "fetch(" not in sjs
          and "window.addEventListener('drop', sfDrop);" in fn(sjs, "sfBoot") and ".sf-body.dragging .sf-frame { pointer-events: none; }" in scss)
    check("99: the server serves the vendored Mermaid from static as JavaScript", served[0] == 200 and "javascript" in served[1]
          and served[2] == len(mjs), str(served))
