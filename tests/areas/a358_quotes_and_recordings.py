"""Area 358: a Quote column on import and a recording named by pseudonym and timepoint (ayabuild12, 9 November 2026,
the Ayahuasca plan's builds 1 and 2; Adam, 9 November about 13:40).

A table's column may be the quotes, a line a quote, each paired with the statement on the same line of the row's
statements cell: a quote past the last statement waits under Quotes to pair, a statement past the last quote has
none, and a quote not word for word in the passage is kept as the statement's quote, unmarked. An Excel file is read
at a named sheet, not only its first. A recording copied in is named by the participant's pseudonym and timepoint,
never the source's own name. Checked on the command line, the MCP server and the routes the cards call, with dry runs
and History. Every word is invented: three potters, Thistle, Heron and Moth, at T1 to T3."""
from __future__ import annotations

import io
import json
import shutil
from pathlib import Path

import openpyxl

from . import support
from .support import check

# Thistle at T1: two statements and two quotes, three statements and two quotes, a quote not word for word, and
# one more quote than statements
CSV = ("Speaker,Time,Transcript,Experiential statements,Quote\n"
       "Kit,0:02,How did the first morning at the wheel go?,,\n"
       'Thistle,0:06,"The clay was cold at first and then it warmed under my hands. I kept the wheel slow.",'
       '"Warmth arriving through the hands\nSlowness as care","it warmed under my hands\nI kept the wheel slow"\n'
       "Kit,0:20,And the pot that cracked?,,\n"
       'Thistle,0:24,"When the pot cracked I laughed, then I cried, then I started again.",'
       '"Laughter as a first answer to loss\nGrief following close\nStarting again as resolve",'
       '"When the pot cracked I laughed\nthen I started again"\n'
       'Thistle,0:40,My teacher never said much.,Silence as teaching,She hardly spoke at all\n'
       'Thistle,0:48,Glaze is a gamble every single time.,Uncertainty welcomed,"Glaze is a gamble\nevery single time"\n')
# the paired, the left to pair, the statements with no quote and the quotes not word for word in the CSV
CSV_COUNTS = {"paired": 6, "unpaired": 1, "no_quote": 1, "unmarked": 1}
# the made-up real name a recording's file carries, which must land nowhere
REAL = "Delphine Arkwright"


def heron_xlsx() -> bytes:
    """Heron at T2: a cover sheet first, the transcript on a sheet named "Heron T2", whose quotes column is headed
    Key quotes."""
    wb = openpyxl.Workbook()
    cover = wb.active
    cover.title = "Cover"
    cover.append(["About"])
    cover.append(["Pottery study, invented"])
    ws = wb.create_sheet("Heron T2")
    for row in (["Speaker", "Time", "Transcript", "Experiential statements", "Key quotes"],
                ["Kit", "0:03", "What changed since spring?", None, None],
                ["Heron", "0:09", "I stopped weighing every bowl and trusted my thumb.",
                 "Trusting the body's measure\nLetting go of numbers", "trusted my thumb\nI stopped weighing every bowl"],
                ["Heron", "0:30", "The kiln still frightens me a little.", "Fear held alongside craft", None]):
        ws.append(row)
    out = io.BytesIO()
    wb.save(out)
    return out.getvalue()


VTT_T1 = ("WEBVTT\n\n00:00:01.000 --> 00:00:03.000\n<v Kit>Where do you throw?</v>\n\n"
          "00:00:04.000 --> 00:00:08.000\n<v Moth>In the shed behind the bakery.</v>\n")
VTT_T3 = ("WEBVTT\n\n00:00:01.000 --> 00:00:03.000\n<v Kit>And now, a year on?</v>\n\n"
          "00:00:04.000 --> 00:00:09.000\n<v Moth>I fire my own kiln on Sundays.</v>\n")


def test_quotes_and_recordings(scratch):
    print("\n358. A Quote column on import, paired with the statements by order, an Excel file read at a named sheet, "
          "and a recording copied in under the participant's pseudonym and timepoint (ayabuild12, 9 November)")
    import cli
    import convert
    import mcp_server
    import server as server_mod
    import workbook as wb_mod
    import idiograph_routes as routes
    import rounds as rounds_mod

    base = scratch / "quotes-358"
    shutil.rmtree(base, ignore_errors=True)
    folder = base / "Pottery"
    inputs = base / "inputs"
    folder.mkdir(parents=True)
    inputs.mkdir()
    cfg = base / "config.json"
    cfg.write_text(json.dumps({"projects": [], "interviewer": "Researcher"}), encoding="utf-8")
    kept = (server_mod.CONFIG_PATH, server_mod.ROOT_OVERRIDE, server_mod.STATE_PATH, server_mod.STATE_MEMORY)
    try:
        server_mod.CONFIG_PATH, server_mod.ROOT_OVERRIDE = cfg, None
        server_mod.STATE_PATH, server_mod.STATE_MEMORY = base / "state.json", {"recent": []}
        (folder / server_mod.PROJECT_FILE).write_text(json.dumps(
            {"name": "Learning to throw", "timepoints": [{"label": "T1"}, {"label": "T2"}, {"label": "T3"}],
             "agents": {"allowed": True, "at": "2026-11-09T10:00:00+00:00"}}), encoding="utf-8")
        routes.add_project(folder)
        config = base / "agent-config.json"
        config.write_text(json.dumps({"root": str(folder), "interviewer": "Researcher"}), encoding="utf-8")

        def run(*argv):
            code_, out, err = cli.run(["--root", str(folder), "--config", str(config), "--json", *argv])
            return code_, (support.plain(json.loads(out)) if out.strip() and code_ == 0 else out), err

        def files():
            return sorted(p.relative_to(folder).as_posix() for p in folder.rglob("*"))

        (inputs / "thistle first morning.csv").write_text(CSV, encoding="utf-8")
        (inputs / "heron.xlsx").write_bytes(heron_xlsx())
        (inputs / "moth shed.vtt").write_text(VTT_T1, encoding="utf-8")

        # ── A. the card's read guesses the Quote column and counts what it brings
        import base64
        read = routes.api_new_project({"op": "read", "name": "thistle.csv",
                                       "data": base64.b64encode(CSV.encode()).decode("ascii")})
        check("358: a column headed Quote is read as the quotes, and the read counts them paired by order",
              read["roles"] == ["name", "ts", "text", "es", "kq"] and read["quotes"] == CSV_COUNTS
              and "kq" in read["shown"] and read["turns"][1]["kq"] == "it warmed under my hands\nI kept the wheel slow",
              json.dumps({k: read.get(k) for k in ("roles", "quotes", "shown")}))
        cover = routes.api_new_project({"op": "read", "name": "heron.xlsx",
                                        "data": base64.b64encode(heron_xlsx()).decode("ascii")})
        named = routes.api_new_project({"op": "read", "name": "heron.xlsx", "sheet": "Heron T2",
                                        "data": base64.b64encode(heron_xlsx()).decode("ascii")})
        check("358: an Excel file is read at its first sheet with anything in it, and at the sheet named, with its "
              "sheets listed for the chooser",
              cover["sheets"] == ["Cover", "Heron T2"] and cover["sheet"] == "Cover" and cover["count"] == 1
              and named["sheet"] == "Heron T2" and named["count"] == 3 and named["roles"][4] == "kq"
              and named["quotes"] == {"paired": 2, "unpaired": 0, "no_quote": 0, "unmarked": 0},
              json.dumps({k: (cover.get(k), named.get(k)) for k in ("sheets", "sheet", "count", "roles", "quotes")}))
        missing = routes.api_new_project({"op": "read", "name": "heron.xlsx", "sheet": "Nowhere",
                                          "data": base64.b64encode(heron_xlsx()).decode("ascii")})
        check("358: a sheet the file has not got is said in one line, and nothing is read",
              missing["said"] == "heron.xlsx has no sheet named Nowhere." and not missing["count"], str(missing.get("said")))

        # ── B. the command line's Add: the dry run counts, the add pairs them in the workbook
        spec = base / "spec.json"
        spec.write_text(json.dumps([
            {"file": str(inputs / "thistle first morning.csv"), "pseudonym": "Thistle", "interview": "First morning",
             "timepoint": "T1", "speakers": {"Kit": "Interviewer", "Thistle": "Participant"}},
            {"file": str(inputs / "heron.xlsx"), "pseudonym": "Heron", "interview": "Spring", "timepoint": "T2",
             "sheet": "Heron T2", "speakers": {"Kit": "Interviewer", "Heron": "Participant"}},
            {"file": str(inputs / "moth shed.vtt"), "pseudonym": "Moth", "interview": "Shed", "timepoint": "T1",
             "speakers": {"Kit": "Interviewer", "Moth": "Participant"}}]), encoding="utf-8")
        before = files()
        code_, dry, err = run("project", "add-transcripts", "--from", str(spec), "--dry-run")
        plan = {c["pseudonym"]: c["interviews"][0] for c in dry.get("plan", [])} if code_ == 0 else {}
        code_t, dry_text, _ = cli.run(["--root", str(folder), "--config", str(config), "project", "add-transcripts",
                                       "--from", str(spec), "--dry-run"])
        check("358: the Add's dry run counts each file's quotes, paired, to pair, with no quote and not word for word, "
              "names the sheet read, and writes nothing",
              code_ == 0 and files() == before and plan["Thistle"]["quotes"] == CSV_COUNTS
              and plan["Heron"]["sheet"] == "Heron T2" and plan["Heron"]["passages"] == 3 and "quotes" not in plan["Moth"]
              and code_t == 0 and "6 quotes paired with a statement, 1 waiting under Quotes to pair" in dry_text
              and "Read from the sheet Heron T2." in dry_text, err or dry_text[:600])
        code_, done, err = run("project", "add-transcripts", "--from", str(spec), "--note", "Bring in the potters",
                               "--tool", "Claude Code")
        thistle = folder / "P1 - Thistle" / "P1 Thistle - EN & ES.xlsx"
        rows = wb_mod.read_case(thistle)["sheets"][0]["rows"] if code_ == 0 else []
        by = {r["text"][:12]: r for r in rows}
        two, three, loose, extra = (by.get("The clay was"), by.get("When the pot"), by.get("My teacher n"),
                                    by.get("Glaze is a g"))
        check("358: two statements and two quotes in a cell are paired one to one",
              two and [p["kq"] for p in two["pairs"]] == ["it warmed under my hands", "I kept the wheel slow"]
              and not two["unpaired"], str(two and two["pairs"]))
        check("358: three statements and two quotes leave the third statement with no quote, nothing to pair",
              three and [p["kq"] for p in three["pairs"]] == ["When the pot cracked I laughed", "then I started again", ""]
              and not three["unpaired"], str(three and three["pairs"]))
        check("358: a quote past the last statement is kept and waits under Quotes to pair",
              extra and extra["unpaired"] and [p["kq"] for p in extra["pairs"]] == ["Glaze is a gamble", "every single time"]
              and extra["pairs"][1]["es"] == "", str(extra and extra["pairs"]))
        found = lambda rs, r, q: wb_mod.quote_turns(rs, rs.index(r), q, "Researcher")
        check("358: a quote word for word in the passage is marked there as the app keeps quotes, one that is not is "
              "kept as the statement's quote, unmarked, nothing lost",
              loose and loose["pairs"] == [{"es": "Silence as teaching", "kq": "She hardly spoke at all"}]
              and found(rows, loose, "She hardly spoke at all") == []
              and found(rows, two, "it warmed under my hands") and found(rows, three, "then I started again"),
              str(loose and loose["pairs"]))
        heron = folder / "P2 - Heron" / "P2 Heron - EN & ES.xlsx"
        heron_rows = wb_mod.read_case(heron)["sheets"][0]["rows"] if code_ == 0 else []
        check("358: the named sheet of the Excel file is the one brought in, its Key quotes paired too",
              len(heron_rows) == 3 and heron_rows[1]["pairs"] == [
                  {"es": "Trusting the body's measure", "kq": "trusted my thumb"},
                  {"es": "Letting go of numbers", "kq": "I stopped weighing every bowl"}]
              and heron_rows[2]["kq"] == "" and "Cover" not in json.dumps(heron_rows), str(heron_rows[1:2]))
        imports = rounds_mod.load_progress(thistle).get("imports") or [{}]
        check("358: History keeps the Add's quotes, counts only",
              code_ == 0 and imports[-1].get("quotes") == CSV_COUNTS and "Bring in the potters" in json.dumps(imports[-1]),
              err or json.dumps(imports[-1])[:300])

        # ── C. a recording named by pseudonym and timepoint, never by its source's name
        moth = folder / "P3 - Moth"
        (moth / "Source" / "kiln.vtt").write_text(VTT_T3, encoding="utf-8")
        recording = moth / "Source" / f"{REAL} kiln.m4a"
        recording.write_bytes(b"\x00\x00\x00\x18ftypM4A invented recording")
        card = routes.api_import({"path": str(moth / "Source" / "kiln.vtt"), "op": "read", "timepoint": 3,
                                  "audio": server_mod.rel_path(recording)})
        check("358: the import card's read says the name the recording will take, the pseudonym and the timepoint",
              card["audio_name"] == "Moth T3.m4a" and card["timepoint"] == 3, str(card.get("audio_name")))
        before = files()
        code_, dry_i, err = run("import", "P3 - Moth/Source/kiln.vtt", "--timepoint", "T3", "--dry-run",
                                "--audio", f"P3 - Moth/Source/{REAL} kiln.m4a")
        code_p, dry_said, _ = cli.run(["--root", str(folder), "--config", str(config), "import", "P3 - Moth/Source/kiln.vtt",
                                       "--timepoint", "T3", "--dry-run", "--audio", f"P3 - Moth/Source/{REAL} kiln.m4a"])
        check("358: the import's dry run says the copy's name and where it goes, under the pseudonym, writing nothing",
              code_ == 0 and files() == before and dry_i["audio_name"] == "Moth T3.m4a"
              and dry_i["audio_writes"] == "P3 - Moth/Source/T3/Source/Moth T3.m4a"
              and code_p == 0 and "The recording is copied as Moth T3.m4a." in dry_said, err or dry_said[:500])
        code_, made, err = run("import", "P3 - Moth/Source/kiln.vtt", "--timepoint", "T3", "--note", "Moth's kiln",
                               "--audio", f"P3 - Moth/Source/{REAL} kiln.m4a")
        landed = moth / "Source" / "T3" / "Source" / "Moth T3.m4a"
        copies = [p.relative_to(folder).as_posix() for p in folder.rglob("*") if p != recording and "Arkwright" in p.name]
        check("358: the recording is copied as Moth T3.m4a, its source's name in no path the import wrote",
              code_ == 0 and landed.read_bytes() == recording.read_bytes() and not copies
              and routes.api_audio({"path": str(moth / "P3 Moth - EN & ES.xlsx"), "sheet": "T3"})["name"] == "Moth T3.m4a",
              err or str(copies))
        check("358: a project of one timepoint names the copy by the pseudonym alone",
              routes.recording_name("P4 - Wick", 1, [{"n": 1}], Path(f"{REAL}.MP3")) == "Wick.mp3"
              and routes.recording_name("Wick", 2, [{"n": 1}, {"n": 2}], Path("x.wav")) == "Wick T2.wav")

        # ── D. the command line's import of a CSV with quotes, and a sheet asked of a file that is no Excel file
        (folder / "P1 - Thistle" / "Source" / "again.csv").write_text(CSV, encoding="utf-8")
        code_, dry_q, err = run("import", "P1 - Thistle/Source/again.csv", "--timepoint", "T2", "--dry-run",
                                "--columns", "Speaker, Time, Transcript, Experiential statements, Quote")
        code_s, _s, err_s = run("import", "P1 - Thistle/Source/again.csv", "--dry-run", "--sheet", "Heron T2")
        check("358: the import's dry run counts the quotes as the Add's does, and a sheet is refused for a CSV",
              code_ == 0 and dry_q["quotes"] == CSV_COUNTS and code_s != 0 and "only for an Excel file" in err_s + str(_s),
              f"{err} {err_s} {_s}"[:300])

        # ── E. the MCP server: the sheet and the Quote role on both tools
        srv = mcp_server.Server(str(folder), config=str(config))
        srv.receive(json.dumps({"jsonrpc": "2.0", "id": 0, "method": "initialize",
                                "params": {"protocolVersion": "2025-06-18", "clientInfo": {"name": "claude-code"}}}))
        tools = {t["name"]: t for t in srv.receive(json.dumps({"jsonrpc": "2.0", "id": 1, "method": "tools/list"}))["result"]["tools"]}
        item = tools["project_add_transcripts"]["inputSchema"]["properties"]["files"]["items"]["properties"]
        check("358: the MCP server's import and add-transcripts take a sheet",
              "sheet" in tools["import"]["inputSchema"]["properties"] and "sheet" in item)
        (inputs / "heron again.xlsx").write_bytes(heron_xlsx())
        got = srv.receive(json.dumps({"jsonrpc": "2.0", "id": 2, "method": "tools/call", "params": {
            "name": "project_add_transcripts", "arguments": {"dry_run": True, "request": "Bring in Wick", "files": [
                {"file": str(inputs / "heron again.xlsx"), "pseudonym": "Wick", "interview": "Spring", "sheet": "Heron T2",
                 "columns": ["Speaker", "Time", "Transcript", "Experiential statements", "Quote"],
                 "speakers": {"Kit": "Interviewer", "Heron": "Participant"}}]}}}))["result"]
        said = json.dumps(got)
        check("358: an MCP dry run reads the named sheet and counts its quotes",
              not got.get("isError") and "Heron T2" in said and '"paired": 2' in said, said[:500])

        # ── F. a recording attached to an interview already in (audioop, 9 November 2026)
        thistle_rec = inputs / f"{REAL} first morning.m4a"
        thistle_rec.write_bytes(b"\x00\x00\x00\x18ftypM4A thistle one")
        thistle_dir = folder / "P1 - Thistle" / "Source" / "First morning" / "Source"
        before = files()
        code_, dry_a, err = run("audio", "attach", "P1 - Thistle", "--file", str(thistle_rec), "--dry-run")
        code_t, dry_text, _ = cli.run(["--root", str(folder), "--config", str(config), "audio", "attach", "P1 - Thistle",
                                       "--file", str(thistle_rec), "--dry-run"])
        check("358: attach's dry run says the name the copy will take and where, writing nothing",
              code_ == 0 and files() == before and dry_a["recording"] == "Thistle T1.m4a"
              and dry_a["writes"] == "P1 - Thistle/Source/First morning/Source/Thistle T1.m4a"
              and code_t == 0 and "as Thistle T1.m4a" in dry_text and "Arkwright" not in dry_text, err or dry_text[:400])
        code_, got, err = run("audio", "attach", "P1 - Thistle", "--file", str(thistle_rec), "--note", "Thistle's first morning")
        copied = thistle_dir / "Thistle T1.m4a"
        record = (rounds_mod.load_progress(thistle).get("imports") or [{}])[-1]
        check("358: attach copies the recording as Thistle T1.m4a, the interview plays it, the source is where it was",
              code_ == 0 and copied.read_bytes() == thistle_rec.read_bytes() and thistle_rec.exists()
              and not [q for q in folder.rglob("*") if "Arkwright" in q.name and q != recording]
              and routes.api_audio({"path": str(thistle), "sheet": "First morning"})["name"] == "Thistle T1.m4a",
              err or str(got))
        check("358: attach is kept in History with the copy's name and his request, never the source's name",
              record.get("attach") is True and record.get("recording") == "Thistle T1.m4a"
              and record.get("sheet") == "First morning" and record.get("by") == "agent"
              and "Thistle's first morning" in json.dumps(record) and "Arkwright" not in json.dumps(record),
              json.dumps(record)[:300])
        before = files()
        code_, _g, err = run("audio", "attach", "P1 - Thistle", "--file", str(thistle_rec), "--note", "Again")
        code_d, _d, err_d = run("audio", "attach", "P1 - Thistle", "--file", str(thistle_rec), "--dry-run")
        check("358: an interview that has a recording is refused, wet or dry, and nothing changes",
              code_ != 0 and code_d != 0 and "has a recording already, Thistle T1.m4a" in err + str(_g)
              and "has a recording already" in err_d + str(_d) and files() == before, f"{err} {err_d}"[:300])
        longer = inputs / f"{REAL} longer take.m4a"
        longer.write_bytes(b"\x00\x00\x00\x18ftypM4A thistle a longer second take")
        code_, got, err = run("audio", "attach", "P1 - Thistle", "--file", str(longer), "--replace", "--offset", "-1.5",
                              "--note", "A better take")
        archived = sorted((folder / "P1 - Thistle" / "_Archive").glob("Thistle T1 before *.m4a"))
        check("358: --replace puts the new recording there, the old one kept in _Archive, and the offset beside it",
              code_ == 0 and copied.read_bytes() == longer.read_bytes() and len(archived) == 1
              and archived[0].read_bytes() == thistle_rec.read_bytes() and thistle_rec.exists() and longer.exists()
              and routes.api_audio({"path": str(thistle), "sheet": "First morning"})["offset"] == -1.5
              and sorted(q.name for q in thistle_dir.glob("*.m4a")) == ["Thistle T1.m4a"], err or str(got))
        # a participant's other timepoint, and the timepoint they have no interview at
        heron_rec = inputs / f"{REAL} spring.mp3"
        heron_rec.write_bytes(b"ID3 invented spring recording")
        code_n, _n, err_n = run("audio", "attach", "P2 - Heron", "--file", str(heron_rec), "--dry-run")
        code_, got, err = run("audio", "attach", "P2 - Heron", "--timepoint", "T2", "--file", str(heron_rec),
                              "--note", "Heron's spring")
        check("358: --timepoint names the interview, the copy is Heron T2.mp3, and a timepoint with no interview is refused",
              code_ == 0 and (folder / "P2 - Heron" / "Source" / "Spring" / "Source" / "Heron T2.mp3").exists()
              and routes.api_audio({"path": str(heron), "sheet": "Spring"})["name"] == "Heron T2.mp3"
              and code_n != 0 and "no interview at timepoint 1" in err_n + str(_n), f"{err} {err_n}"[:300])
        empty = inputs / "silence.m4a"
        empty.write_bytes(b"")
        notes = inputs / "notes.txt"
        notes.write_text("not a recording", encoding="utf-8")
        before = files()
        refused = {}
        for key, name in (("text", notes), ("empty", empty), ("gone", inputs / "nothing here.m4a")):
            refused[key] = run("audio", "attach", "P3 - Moth", "--timepoint", "T1", "--file", str(name), "--dry-run")
        refused["same"] = run("audio", "attach", "P1 - Thistle", "--file", str(copied), "--replace", "--dry-run")
        said_of = lambda k: refused[k][2] + str(refused[k][1])
        check("358: a file that is not a recording Idiograph plays, an empty one, one not there and the interview's own "
              "copy are each refused with nothing written",
              all(refused[k][0] != 0 for k in refused) and files() == before
              and "not one Idiograph plays" in said_of("text") and "is empty" in said_of("empty")
              and "not there" in said_of("gone") and "already" in said_of("same"), str({k: said_of(k)[:120] for k in refused}))
        project_file = folder / server_mod.PROJECT_FILE
        open_text = project_file.read_text(encoding="utf-8")
        shut = json.loads(open_text)
        shut["agents"] = {"allowed": False, "at": None}
        project_file.write_text(json.dumps(shut), encoding="utf-8")
        try:
            code_c, _c, err_c = run("audio", "attach", "P3 - Moth", "--timepoint", "T1", "--file", str(heron_rec), "--note", "x")
        finally:
            project_file.write_text(open_text, encoding="utf-8")
        check("358: a project closed to agents is refused", code_c != 0 and not (moth / "Source" / "Shed" / "Source").exists(),
              f"{err_c} {_c}"[:300])
        got = srv.receive(json.dumps({"jsonrpc": "2.0", "id": 3, "method": "tools/call", "params": {
            "name": "audio_attach", "arguments": {"dry_run": True, "request": "Moth's shed", "case": "P3 - Moth",
                                                  "file": str(heron_rec), "timepoint": 1}}}))["result"]
        said = json.dumps(got)
        check("358: the MCP server's audio_attach says the name in a dry run and takes replace",
              not got.get("isError") and "Moth T1.mp3" in said
              and "replace" in tools["audio_attach"]["inputSchema"]["properties"], said[:400])

        # ── G. add-transcripts with a recording on its entries, a new participant's and a further interview's
        quill_rec = inputs / f"{REAL} wheel.wav"
        quill_rec.write_bytes(b"RIFF invented wheel recording")
        heron_two = inputs / f"{REAL} summer.m4a"
        heron_two.write_bytes(b"\x00\x00\x00\x18ftypM4A heron summer")
        (inputs / "quill wheel.vtt").write_text(VTT_T1.replace("Moth", "Quill"), encoding="utf-8")
        (inputs / "heron summer.vtt").write_text(VTT_T3.replace("Moth", "Heron"), encoding="utf-8")
        spec = base / "spec-audio.json"
        spec.write_text(json.dumps([
            {"file": str(inputs / "quill wheel.vtt"), "pseudonym": "Quill", "interview": "Wheel", "timepoint": "T1",
             "audio": str(quill_rec), "speakers": {"Kit": "Interviewer", "Quill": "Participant"}},
            {"file": str(inputs / "heron summer.vtt"), "pseudonym": "Heron", "interview": "Summer", "timepoint": "T3",
             "audio": str(heron_two), "offset": 2, "speakers": {"Kit": "Interviewer", "Heron": "Participant"}}]),
            encoding="utf-8")
        before = files()
        code_, dry, err = run("project", "add-transcripts", "--from", str(spec), "--dry-run")
        named = {c["pseudonym"]: c["interviews"][0] for c in dry.get("plan", [])} if code_ == 0 else {}
        check("358: the Add's dry run says each entry's recording by the name it will take, writing nothing",
              code_ == 0 and files() == before and named["Quill"]["recording"] == "Quill T1.wav"
              and named["Heron"]["recording"] == "Heron T3.m4a", err or str(named))
        code_, done, err = run("project", "add-transcripts", "--from", str(spec), "--note", "Quill and Heron's summer")
        quill_at = next((folder / d / "Source" / "Wheel" / "Source" for d in sorted(q.name for q in folder.iterdir())
                         if d.endswith(" - Quill")), None)
        heron_at = folder / "P2 - Heron" / "Source" / "Summer" / "Source"
        quill_book = next(iter(sorted(folder.glob("P* - Quill/P* Quill - EN & ES.xlsx"))), None)
        check("358: the Add copies each entry's recording under the pseudonym and timepoint, the interview plays it, "
              "the offset is beside it and the sources stay put",
              code_ == 0 and quill_at and (quill_at / "Quill T1.wav").read_bytes() == quill_rec.read_bytes()
              and (heron_at / "Heron T3.m4a").read_bytes() == heron_two.read_bytes()
              and quill_rec.exists() and heron_two.exists()
              and not [q for q in folder.rglob("*") if "Arkwright" in q.name and q != recording]
              and routes.api_audio({"path": str(quill_book), "sheet": "Wheel"})["name"] == "Quill T1.wav"
              and routes.api_audio({"path": str(heron), "sheet": "Summer"})["name"] == "Heron T3.m4a"
              and routes.api_audio({"path": str(heron), "sheet": "Summer"})["offset"] == 2, err or str(done))
        record = (rounds_mod.load_progress(heron).get("imports") or [{}])[-1]
        check("358: History keeps the Add's recordings by their copies' names",
              record.get("recordings") == ["Heron T3.m4a"] and "Arkwright" not in json.dumps(record), json.dumps(record)[:300])
        (inputs / "bad.json").write_text(json.dumps([
            {"file": str(inputs / "quill wheel.vtt"), "pseudonym": "Ivy", "interview": "Wheel",
             "audio": str(notes), "speakers": {"Kit": "Interviewer", "Quill": "Participant"}}]), encoding="utf-8")
        before = files()
        code_, _b, err = run("project", "add-transcripts", "--from", str(inputs / "bad.json"), "--note", "x")
        check("358: an entry whose recording is not one the app plays refuses the whole Add before anything is written",
              code_ != 0 and files() == before and "not one Idiograph plays" in err + str(_b), f"{err} {_b}"[:300])

        # ── H. project new from a named sheet, with a Quote column
        fresh = base / "Fresh"
        fresh.mkdir()
        fresh_cfg = base / "fresh-config.json"
        fresh_cfg.write_text(json.dumps({"projects": [], "interviewer": "Researcher"}), encoding="utf-8")

        def make(*argv):
            code_, out, err = cli.run(["--config", str(fresh_cfg), "--json", "project", "new", str(fresh), "--name", "Fresh pots",
                                       "--pseudonym", "Heron", "--transcript", str(inputs / "heron.xlsx"),
                                       "--speakers", "Kit=Interviewer,Heron=Participant", *argv])
            return code_, (support.plain(json.loads(out)) if out.strip() and code_ == 0 else out), err

        code_a, cover_dry, err_a = make("--dry-run")
        code_, named_dry, err = make("--dry-run", "--sheet", "Heron T2", "--columns",
                                     "Speaker, Time, Transcript, Experiential statements, Quote")
        code_t, named_text, _ = cli.run(["--config", str(fresh_cfg), "project", "new", str(fresh), "--name", "Fresh pots",
                                         "--pseudonym", "Heron", "--transcript", str(inputs / "heron.xlsx"), "--dry-run",
                                         "--speakers", "Kit=Interviewer,Heron=Participant", "--sheet", "Heron T2",
                                         "--columns", "Speaker, Time, Transcript, Experiential statements, Quote"])
        one = named_dry["cases"][0]["interviews"][0] if code_ == 0 else {}
        check("358: project new's dry run reads the named sheet, counts its quotes and writes nothing",
              code_a == 0 and cover_dry["cases"][0]["interviews"][0].get("passages") == 1 and one.get("passages") == 3
              and one.get("sheet") == "Heron T2" and one.get("quotes", {}).get("paired") == 2
              and not any(fresh.iterdir()) and code_t == 0 and "Read from the sheet Heron T2." in named_text,
              err or err_a or named_text[:400])
        code_, made, err = make("--sheet", "Heron T2", "--columns", "Speaker, Time, Transcript, Experiential statements, Quote",
                                "--note", "Start the pottery study")
        fresh_book = next(iter(sorted(fresh.glob("P1 - Heron/P1 Heron - EN & ES.xlsx"))), None)
        fresh_rows = wb_mod.read_case(fresh_book)["sheets"][0]["rows"] if code_ == 0 and fresh_book else []
        check("358: project new makes the participant from the named sheet, its Quote column paired with the statements",
              code_ == 0 and len(fresh_rows) == 3 and fresh_rows[1]["pairs"] == [
                  {"es": "Trusting the body's measure", "kq": "trusted my thumb"},
                  {"es": "Letting go of numbers", "kq": "I stopped weighing every bowl"}]
              and "Cover" not in json.dumps(fresh_rows), err or str(fresh_rows[1:2]))
        new_item = tools["project_new"]["inputSchema"]["properties"]["transcripts"]["items"]["properties"]
        check("358: the MCP server's project_new takes a sheet and columns for each transcript",
              "sheet" in new_item and "columns" in new_item
              and "audio" in item and "offset" in item and "audio_attach" in tools)
    finally:
        (server_mod.CONFIG_PATH, server_mod.ROOT_OVERRIDE, server_mod.STATE_PATH, server_mod.STATE_MEMORY) = kept
