from __future__ import annotations

import hashlib
import io
import json
import shutil
import zipfile
from xml.sax.saxutils import escape, quoteattr

import openpyxl

from .support import check
from . import support
import idiograph_routes
import idiograph_cli

# Every package here is written by the suite itself, on an invented topic, keeping an allotment, with
# invented people: Sam asks, and Wren, Ash, Hazel and Rowan answer. Never a real study's file.
NS = "urn:QDA-XML:project:1.0"

ATLAS_TEXT = ("Sam: How did the plot look when you first took it on?\n"
              "Wren: Brambles everywhere. I could not see the shed at all.\n"
              "Sam: What did you clear first?\n"
              "Wren: The path. I needed a way in before anything else. Then the beds.\n"
              "Sam: And the neighbours?\n"
              "Wren: The woman next door gave me her spare leeks, and that kept me going.\n")
TESTER_TEXT = ("My father grew beans every summer, and the smell of the vines in July was the whole of my "
             "childhood. When I took the plot I planted beans before anything else, without thinking.\n\n"
             "There is a bench at the end where I sit after the watering. Nobody asks anything of me there. "
             "I watch the light go off the beans and I think of him.\n\n"
             "The first year the slugs had everything, and I nearly gave it up, but the beans came through.\n")
NVIVO_TEXT = ("Sam: Was the first summer hard?\n"
              "Ash: The slugs ate everything. I nearly gave it up.\n"
              "Sam: What kept you going?\n"
              "Ash: The committee lent me a rotavator, and the soil turned over in one afternoon.\n")
MAXQDA_TEXT = ("Sam: What do you grow now?\n"
               "Hazel: Squash, mostly, because it forgives me when I am away.\n"
               "Sam: Do you share it?\n"
               "Hazel: Half goes to the food bank on Saturdays. I like that it leaves the plot.\n")
EDGE_TEXT = ("Sam: Tell me about the shed.\r\n"
             "Rowan: \U0001F331 The shed leans now, and the roof lets the rain in.\r\n"
             "Sam: Will you mend it?\r\n"
             "Rowan: Next spring, when the money comes. Until then the tools stay dry under a tarp.\r\n")


def at(text: str, phrase: str, nth: int = 0) -> tuple[int, int]:
    start = -1
    for _ in range(nth + 1):
        start = text.index(phrase, start + 1)
    return start, start + len(phrase)


def selection(guid: str, span, codes=(), comment: str = "", notes=(), user: str = "u1", tag: str = "PlainTextSelection") -> str:
    inner = f"<Description>{escape(comment)}</Description>" if comment else ""
    inner += "".join(f'<Coding guid="c-{guid}-{i}" creatingUser="{user}"><CodeRef targetGUID="{c}"/></Coding>'
                     for i, c in enumerate(codes))
    inner += "".join(f'<NoteRef targetGUID="{n}"/>' for n in notes)
    if tag == "TranscriptSelection":
        return f'<TranscriptSelection guid="{guid}" fromSyncPoint="{span[0]}" toSyncPoint="{span[1]}" creatingUser="{user}">{inner}</TranscriptSelection>'
    return (f'<PlainTextSelection guid="{guid}" startPosition="{span[0]}" endPosition="{span[1]}" '
            f'creatingUser="{user}">{inner}</PlainTextSelection>')


def package(origin: str, codes: str, sources: str, files: dict, extra: str = "", users=("u1",),
            notes: str = "", doctype: bool = False) -> bytes:
    """A .qdpx as a programme exports one: project.qde and its Sources folder, in a zip."""
    people = "".join(f'<User guid="{u}" name="Coder {u}"/>' for u in users)
    qde = (('<?xml version="1.0" encoding="utf-8"?>' + ('<!DOCTYPE Project [<!ENTITY a "aaaa">]>' if doctype else ""))
           + f'<Project xmlns="{NS}" name="Allotments" origin={quoteattr(origin)}><Users>{people}</Users>'
           f'<CodeBook><Codes>{codes}</Codes></CodeBook><Sources>{sources}</Sources>'
           + (f"<Notes>{notes}</Notes>" if notes else "") + extra + "</Project>")
    out = io.BytesIO()
    with zipfile.ZipFile(out, "w") as z:
        z.writestr("project.qde", qde)
        for name, data in files.items():
            z.writestr(name, data)
    return out.getvalue()


def code(guid: str, name: str, children: str = "") -> str:
    return f'<Code guid="{guid}" name="{escape(name)}" isCodable="true">{children}</Code>'


def atlas() -> bytes:
    t = ATLAS_TEXT
    sels = (selection("q1", at(t, "Brambles everywhere."), ["k1"], comment="the neglect, all at once")
            + selection("q2", at(t, "I could not see the shed at all."))
            + selection("q3", at(t, "I needed a way in"), ["k2"])
            + selection("q4", at(t, "The woman next door gave me her spare leeks"), ["k3"]))
    codes = code("k1", "Overwhelmed by the plot") + code("k2", "Finding a way in") + code("k3", "Kindness of neighbours")
    sets = ('<Sets><Set guid="s1" name="Taking it on"><MemberCode targetGUID="k1"/><MemberCode targetGUID="k2"/></Set>'
            '<Set guid="s2" name="Other people"><MemberCode targetGUID="k3"/></Set></Sets>')
    src = f'<TextSource guid="t1" name="Wren interview" plainTextPath="internal://t1.txt">{sels}</TextSource>'
    return package("ATLAS.ti 23.2", codes, src, {"Sources/t1.txt": t.encode("utf-8")}, extra=sets)


def tester() -> bytes:
    t = TESTER_TEXT
    sels = (selection("q1", at(t, "My father grew beans every summer"), ["k1"])
            + selection("q2", at(t, "I planted beans before anything else"), ["k1"])
            + selection("q3", at(t, "I think of him."), ["k1"]))
    src = f'<TextSource guid="t1" name="Rowan, garden walk" plainTextPath="internal://t1.txt">{sels}</TextSource>'
    return package("MAXQDA 2024", code("k1", "Beans as his father's"), src, {"Sources/t1.txt": t.encode("utf-8")})


def nvivo() -> bytes:
    t = NVIVO_TEXT
    p2, p4 = t.index("Ash: The slugs"), t.index("Ash: The committee")
    q_start, q_end = at(t, "The committee lent me a rotavator")
    sync = (f'<SyncPoint guid="y0" position="0" timeStamp="0"/><SyncPoint guid="y2" position="{p2}" timeStamp="9000"/>'
            f'<SyncPoint guid="y4" position="{p4}" timeStamp="65000"/>'
            f'<SyncPoint guid="ya" position="{q_start}" timeStamp="66000"/><SyncPoint guid="yb" position="{q_end}" timeStamp="69000"/>')
    sels = selection("q1", ("ya", "yb"), ["k1"], notes=["n1"], tag="TranscriptSelection")
    audio = (f'<AudioSource guid="a1" name="Ash, first summer" path="internal://a1.m4a"><NoteRef targetGUID="n2"/>'
             f'<Transcript guid="tr1" plainTextPath="internal://tr1.txt">{sync}{sels}</Transcript></AudioSource>')
    notes = ('<Note guid="n1" name="Annotation"><PlainTextContent>help that arrived from the committee</PlainTextContent></Note>'
             '<Note guid="n2" name="After the interview"><PlainTextContent>Ash spoke faster about the rotavator.</PlainTextContent></Note>'
             '<Note guid="n3" name="Project memo"><PlainTextContent>A free memo on the whole project.</PlainTextContent></Note>')
    extra = ('<Variables><Variable guid="v1" name="Years on the plot" typeOfVariable="Integer"/></Variables>'
             '<Cases><Case guid="c1" name="Ash"><SourceRef targetGUID="a1"/><VariableValue><VariableRef targetGUID="v1"/>'
             '<IntegerValue>3</IntegerValue></VariableValue></Case></Cases>')
    return package("NVivo 14", code("k1", "Help from the committee"), audio,
                   {"Sources/tr1.txt": t.encode("utf-8"), "Sources/a1.m4a": b"\x00\x00\x00\x18ftypM4A fake audio"},
                   extra=extra, notes=notes)


def maxqda() -> bytes:
    t = MAXQDA_TEXT
    sels = (selection("q1", at(t, "Squash, mostly, because it forgives me"), ["k1"], comment="the plot forgives absence", user="u1")
            + selection("q2", at(t, "Half goes to the food bank on Saturdays."), ["k2"], user="u2")
            + selection("q3", at(t, "I like that it leaves the plot."), ["k2"], user="u1"))
    src = f'<TextSource guid="t1" name="Hazel T1" plainTextPath="internal://t1.txt">{sels}</TextSource>'
    sets = '<Sets><Set guid="s1" name="Documents"><MemberSource targetGUID="t1"/></Set></Sets>'
    return package("MAXQDA 2024 (Release 24.1)", code("k1", "Forgiving crops") + code("k2", "Giving it away"), src,
                   {"Sources/t1.txt": t.encode("utf-8")}, extra=sets, users=("u1", "u2"))


def edge() -> bytes:
    t = EDGE_TEXT
    sels = (selection("q1", at(t, "The shed leans now"), ["k1"])
            + selection("q2", (t.index("the roof lets"), t.index("Will you mend") + 8), ["k2"]))
    srcs = (f'<TextSource guid="t1" name="Rowan T1" plainTextPath="internal://t1.txt">{sels}</TextSource>'
            '<TextSource guid="t2" name="Lost notes" plainTextPath="internal://gone.txt"/>'
            '<PDFSource guid="p1" name="Plot rules" path="internal://p1.pdf"/>')
    return package("ATLAS.ti 9", code("k1", "The shed failing") + code("k2", "Rain getting in"), srcs,
                   {"Sources/t1.txt": t.encode("utf-8"), "Sources/p1.pdf": b"%PDF-1.4 fake", "../outside.txt": b"never read"})


def test_qdpx(scratch):
    print("\n244. A REFI-QDA project (.qdpx) from ATLAS.ti, NVivo or MAXQDA brought in as participants through "
          "the one API: codes as statements, comments as notes, blank statements, memos, recordings, the PET "
          "draft, the dry run, the refusals, the original only read (21 October)")
    import cli
    import mcp_server
    import qdpx
    import server as server_mod
    import themes
    import workbook as wb_mod

    def make_root(name, allowed=True, timepoints=None):
        at_ = scratch / name
        shutil.rmtree(at_, ignore_errors=True)
        (at_ / "Imports").mkdir(parents=True)
        held = {"name": "Allotments, a qdpx project"}
        if allowed:
            held["agents"] = {"allowed": True, "at": "2026-10-21T01:00:00+01:00"}
        if timepoints:
            held["timepoints"] = timepoints
        (at_ / server_mod.PROJECT_FILE).write_text(json.dumps(held), encoding="utf-8")
        for flavour, made in (("atlas", atlas), ("tester", tester), ("nvivo", nvivo), ("maxqda", maxqda), ("edge", edge)):
            (at_ / "Imports" / f"{flavour}.qdpx").write_bytes(made())
        return at_

    def files(at_):
        return {p.relative_to(at_).as_posix(): p.read_bytes() for p in sorted(at_.rglob("*")) if p.is_file()}

    def digest(p):
        return hashlib.sha1(p.read_bytes()).hexdigest()

    def rows_of(book, sheet):
        wb = openpyxl.load_workbook(book)
        try:
            return [list(r) for r in wb[sheet].iter_rows(values_only=True)]
        finally:
            wb.close()

    kept = (server_mod.CONFIG_PATH, server_mod.ROOT_OVERRIDE, server_mod.STATE_MEMORY, server_mod.STATE_PATH)
    try:
        root = make_root("a244-qdpx")
        config = scratch / "a244-config.json"
        config.write_text(json.dumps({"root": str(root), "interviewer": "Researcher"}), encoding="utf-8")

        def run(*argv, at_=root):
            code_, out, err = cli.run(["--root", str(at_), "--config", str(config), *argv])
            return code_, (support.plain(json.loads(out)) if "--json" in argv and out.strip() else out), err

        # -- the reader, the passages and the quotes
        pkg_path = root / "Imports" / "atlas.qdpx"
        read = qdpx.read_package(pkg_path)
        split = qdpx.passages(ATLAS_TEXT)
        check("244: the reader takes an ATLAS.ti project's sources, codes, code groups and quotations, and splits its "
              "text a Name: line a passage as plain text is split",
              read["package"] == "ATLAS.ti" and len(read["sources"]) == 1 and len(read["sources"][0]["selections"]) == 4
              and [s["name"] for s in read["sets"]] == ["Taking it on", "Other people"]
              and [p["name"] for p in split] == ["Sam", "Wren"] * 3
              and split[1]["words"] == "Brambles everywhere. I could not see the shed at all.", str(split[:2]))
        t = TESTER_TEXT
        quote = qdpx.assemble_quote([at(t, "I planted beans before anything else"), at(t, "My father grew beans every summer")], t)
        check("244: pieces of one passage make one quote in transcript order, an ellipsis where they are not next to each other",
              quote == '"My father grew beans every summer … I planted beans before anything else"', quote)
        # another programme's package is read as before LPETs travelled (qdpxlpets, 12 November 2026): a code named
        # LPETs is a code like any, and a set holding a code that cannot be coded beside one that can is a code group
        mixed = scratch / "a244-mixed.qdpx"
        mixed.write_bytes(package(
            "ATLAS.ti 23.2", '<Code guid="p1" name="Wren" isCodable="false"><Code guid="l1" name="LPETs" isCodable="false">'
            '<Code guid="l2" name="Later on" isCodable="false"/></Code>' + code("k1", "Finding a way in") + "</Code>",
            f'<TextSource guid="t1" name="Wren interview" plainTextPath="internal://t1.txt">'
            f'{selection("q1", at(ATLAS_TEXT, "I needed a way in"), ["k1"])}</TextSource>',
            {"Sources/t1.txt": ATLAS_TEXT.encode("utf-8")},
            extra='<Sets><Set guid="s1" name="Later on"><MemberCode targetGUID="l2"/><MemberCode targetGUID="k1"/></Set></Sets>'))
        got = qdpx.read_package(mixed)
        check("244: another programme's code named LPETs is no LPET, and its set of codes is a code group and a set of "
              "codes that cannot be coded as before",
              qdpx.lpet_codes(got) == {} and qdpx.lpet_trees(got) == [] and qdpx.lpet_sets(got) == ({}, [])
              and [g["name"] for g in qdpx.code_groups(got)] == ["Later on"]
              and [g["name"] for g in qdpx.upper_groups(got)] == ["Later on"], str(qdpx.code_groups(got))[:300])

        # -- A. ATLAS.ti: the dry run writes nothing, then the apply with the PET draft
        before, original = files(root), digest(pkg_path)
        code_, dry, _ = run("qdpx", "Imports/atlas.qdpx", "--dry-run", "--json")
        check("244: a dry run with no sources named lists each source, its speakers and first passages, says what is "
              "held back, and writes nothing",
              code_ == 0 and dry["dry_run"] is True and files(root) == before and dry["said"] == idiograph_routes.QDPX_NAME_SOURCES
              and dry["sources"][0]["speakers"][0] == {"name": "Sam", "turns": 3, "role": "Interviewer"}
              and dry["sources"][0]["passages"][1]["statements"][0] == {"statement": "Overwhelmed by the plot",
                                                                        "quote": '"Brambles everywhere."'}
              and dry["sources"][0]["passages"][1]["notes"] == ["the neglect, all at once"]
              and dry["groups"] == ["Taking it on", "Other people"], str(dry)[:600])
        code_, _, err = run("qdpx", "Imports/atlas.qdpx", "--sources", "1=Wren")
        check("244: an apply with no request is refused, nothing written", code_ == 1 and "--note" in err and files(root) == before, err)
        code_, done, err = run("qdpx", "Imports/atlas.qdpx", "--sources", "1=Wren:3", "--pets", "--note",
                               "Bring in Wren from ATLAS.ti", "--tool", "Claude Code", "--json")
        book = root / "P3 - Wren" / "P3 Wren - EN & ES.xlsx"
        sheet = rows_of(book, "Interview") if book.is_file() else []
        check("244: the apply makes the participant as Add makes one, a copy of the .qdpx in Source, the raw source and the "
              "workbook, the original only read",
              code_ == 0 and done["written"] == ["P3 - Wren"] and book.is_file() and digest(pkg_path) == original
              and (root / "P3 - Wren" / "Source" / "Interview" / "P3-Interview.qdpx").read_bytes() == pkg_path.read_bytes()
              and (root / "P3 - Wren" / "Source" / "P3 Wren - transcript.xlsx").is_file(), err or str(done)[:300])
        wren = sheet[2] if len(sheet) > 2 else [None] * 6
        check("244: a code is an experiential statement named by the code, its quotation the quote, and a comment an "
              "exploratory note on the passage (rulings 1 and 2)",
              wren[0] == "Wren" and wren[2] == "Overwhelmed by the plot" and wren[4] == "the neglect, all at once"
              and wren[5].split("\n\n")[0] == '"Brambles everywhere."', str(wren))
        check("244: a quotation with no code and no comment is a blank experiential statement, its quote kept after the "
              "statements and its words empty (ruling 3)",
              wb_mod.pairs_of(wren[2], wren[5]) == [{"es": "Overwhelmed by the plot", "kq": '"Brambles everywhere."'},
                                                    {"es": "", "kq": '"I could not see the shed at all."'}], str(wren))
        progress = json.loads((root / "P3 - Wren" / "Working" / "P3 Wren - EN & ES.progress.json").read_text(encoding="utf-8"))
        check("244: the workbook names who made it and his request, and its History keeps the import's lines",
              "Bring in Wren from ATLAS.ti" in str(openpyxl.load_workbook(book).properties.description)
              and progress["imports"][0]["from"] == "atlas.qdpx"
              and progress["imports"][0]["lines"][0].startswith("From atlas.qdpx (ATLAS.ti): 1 participant, 6 passages, "
                                                                "1 comment as an exploratory note, 3 codes as 3 experiential statements"),
              str(progress.get("imports"))[:400])
        data = themes.load(book)
        board = themes.current_version(data) if data else {}
        labels = sorted(g["label"] for g in (board or {}).get("groups", []))
        check("244: the PET draft is a board From ATLAS.ti, a PET a code group holding its codes' statements (ruling 6)",
              board.get("name") == "From ATLAS.ti" and labels == ["Other people", "Taking it on"], str(labels))

        # blank statements meet every reader: the turn, the statements, the board
        code1, shown, err1 = run("turn", "show", "Wren", "Interview", "3", "--json")
        code2, _, err2 = run("statements", "Wren", "--json")
        code3, _, err3 = run("board", "show", "Wren", "--json")
        check("244: a passage holding a blank statement reads back through turn show, statements and board show without error",
              code1 == 0 and code2 == 0 and code3 == 0
              and {"statement": "", "quote": '"I could not see the shed at all."'} in shown["turns"][0]["pairs"],
              (err1 or err2 or err3 or str(shown))[:400])

        # -- B. A tester's: one code over three long quotations
        code_, done, err = run("qdpx", "Imports/tester.qdpx", "--sources", "1=Rowan", "--note", "Bring in a tester's walk", "--json")
        rowan = next(root.glob("P* - Rowan/P* Rowan - EN & ES.xlsx"), None)
        walk = rows_of(rowan, "Interview") if rowan else []
        check("244: a tester's flavour: a code over two quotations of one passage is one statement whose quote is both pieces "
              "with an ellipsis, and the code's quotation in another passage gives the statement once there",
              code_ == 0 and len(walk) == 4
              and walk[1][2] == "Beans as his father's"
              and walk[1][5] == '"My father grew beans every summer … I planted beans before anything else"'
              and walk[2][2] == "Beans as his father's" and walk[2][5] == '"I think of him."' and walk[3][2] is None,
              err or str(walk)[:500])

        # -- C. NVivo: a recording's transcript, sync points, a memo, the recording copied
        code_, done, err = run("qdpx", "Imports/nvivo.qdpx", "--sources", "1=Ash", "--note", "Bring in Ash", "--json")
        ash = next(root.glob("P* - Ash"), None)
        rows = rows_of(next(ash.glob("P* Ash - EN & ES.xlsx")), "Interview") if ash else []
        memo = (ash / "Source" / "Ash - memos.txt") if ash else None
        check("244: NVivo's audio source: each passage timed from its sync point, the annotation a note, the recording "
              "copied in for the player, the source's memo to Ash - memos.txt (rulings 4 and 5)",
              code_ == 0 and wb_mod.ts_seconds(rows[2][1]) == 9
              and wb_mod.ts_seconds(rows[4][1]) == 65
              and rows[4][2] == "Help from the committee" and rows[4][4] == "help that arrived from the committee"
              and (ash / "Source" / "Interview" / "Source" / "Ash.m4a").is_file()
              and "Ash spoke faster about the rotavator." in memo.read_text(encoding="utf-8")
              and any("1 variable left out" in line and "1 free memo left out" in line for line in done["lines"]),
              err or str(done.get("lines")))

        # -- D. MAXQDA: one coder's work alone, comments as statements
        code_, dry, _ = run("qdpx", "Imports/maxqda.qdpx", "--sources", "1=Hazel", "--user", "Coder u1",
                            "--comments", "statements", "--dry-run", "--json")
        first = dry["sources"][0]["passages"]
        check("244: MAXQDA's segments with one coder chosen leave the other's codings out, and a comment as a statement "
              "takes its quotation as the quote",
              code_ == 0 and dry["sources"][0]["coders"] == ["Coder u1", "Coder u2"]
              and {s["statement"] for s in first[1]["statements"]} == {"the plot forgives absence", "Forgiving crops"}
              and [s["statement"] for s in first[3]["statements"]] == ["Giving it away"]
              and any("1 coding by other coders left out" in line for line in dry["lines"]), str(dry)[:600])

        # -- E. the edges: CRLF, an emoji before a quotation, one across passages, a missing source, a PDF, a ../ name
        code_, dry, _ = run("qdpx", "Imports/edge.qdpx", "--dry-run", "--json")
        lines = " ".join(dry["lines"])
        statements = [s for p in dry["sources"][0]["passages"] for s in p.get("statements", [])]
        check("244: the edges: an emoji before a quotation keeps its words, a quotation across passages is cut at its "
              "passage's end and said, a missing source, a PDF and a name climbing out of the package left out and said",
              code_ == 0 and statements[0]["quote"] == '"The shed leans now"'
              and statements[1]["quote"] == '"the roof lets the rain in."'
              and dry["sources"][1]["left_out"].startswith("Lost notes is left out")
              and dry["sources"][2]["left_out"] == "Plot rules is a PDF document, so it is left out."
              and "1 PDF document left out" in lines and "unsafe name left out" in lines
              and "1 quotation that crosses passages cut" in lines,
              str(dry)[:800])

        # -- F. refusals
        outside = scratch / "a244-outside.qdpx"
        outside.write_bytes(atlas())
        code_, _, err = run("qdpx", str(outside), "--dry-run")
        check("244: a .qdpx outside the project's folder is refused", code_ == 1 and idiograph_cli.OUTSIDE in err, err)
        (root / "Imports" / "bad.qdpx").write_bytes(b"not a zip")
        code_, _, err = run("qdpx", "Imports/bad.qdpx", "--dry-run")
        check("244: a file that is no zip is refused in one line", code_ == 1 and qdpx.NOT_A_PACKAGE in err, err)
        (root / "Imports" / "typed.qdpx").write_bytes(package("ATLAS.ti", "", "", {}, doctype=True))
        code_, _, err = run("qdpx", "Imports/typed.qdpx", "--dry-run")
        check("244: a project.qde with a document type is refused, so no entity is ever expanded",
              code_ == 1 and qdpx.DOCTYPE in err, err)
        before = files(root)
        code_, _, err = run("qdpx", "Imports/atlas.qdpx", "--sources", "1=Wren", "--note", "Again")
        check("244: a pseudonym's interview already there is refused with nothing written",
              code_ == 1 and "Interview already" in err and files(root) == before, err)
        code_, _, err = run("qdpx", "Imports/atlas.qdpx", "--sources", "9=Wren", "--note", "x")
        check("244: a source that is not there is refused", code_ == 1 and "There is no source 9." in err, err)
        code_, _, err = run("qdpx", "Imports/edge.qdpx", "--sources", "3=Moss", "--note", "x")
        check("244: a source that is left out cannot be brought in", code_ == 1 and "PDF document" in err, err)
        shut = make_root("a244-shut", allowed=False)
        code_, _, err = cli.run(["--root", str(shut), "--config", str(config), "qdpx", "Imports/atlas.qdpx", "--dry-run"])
        check("244: a project that does not allow AI agents is refused", code_ == 1 and "Allow AI agents" in err, err)

        # a failure on the way takes away what it wrote
        before = files(root)
        real = idiograph_routes.qdpx_board

        def broken(*a, **k):
            raise OSError("disk full")

        idiograph_routes.qdpx_board = broken
        try:
            code_, _, err = run("qdpx", "Imports/atlas.qdpx", "--sources", "1=Moss", "--pets", "--note", "x")
        finally:
            idiograph_routes.qdpx_board = real
        check("244: a failure on the way takes away everything the import wrote",
              code_ == 1 and files(root) == before and "nothing was written" in err, err)

        # -- G. the MCP tool, the same function
        srv = mcp_server.Server(str(root), config=str(config))
        srv.receive(json.dumps({"jsonrpc": "2.0", "id": 0, "method": "initialize",
                                "params": {"protocolVersion": "2025-06-18", "clientInfo": {"name": "claude-code"}}}))
        got = srv.receive(json.dumps({"jsonrpc": "2.0", "id": 1, "method": "tools/call", "params": {
            "name": "import_qdpx", "arguments": {"file": "Imports/maxqda.qdpx", "request": "Bring in Hazel",
                                                 "sources": [{"source": 1, "pseudonym": "Hazel", "number": 8}],
                                                 "codes": "notes"}}}))["result"]
        hazel = root / "P8 - Hazel" / "P8 Hazel - EN & ES.xlsx"
        rows = rows_of(hazel, "T1") if hazel.is_file() else []
        check("244: the MCP tool import_qdpx brings a project in through the same function, codes as notes when asked",
              got["isError"] is False and rows and rows[2][4].split("\n\n")[-1] == "Forgiving crops" and rows[2][2] is None,
              str(got)[:400])
    finally:
        server_mod.CONFIG_PATH, server_mod.ROOT_OVERRIDE, server_mod.STATE_MEMORY, server_mod.STATE_PATH = kept
