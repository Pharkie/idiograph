"""Area 407: Also an ordinary word on the project's list of names, in place of Match case (ordinaryword, Adam's option
B of 16 November 2026: Match case flagged "Hope you're well" at a sentence's start and missed a lowercase "hope" that
was the name).

On the demo's three participants made a project, with "Will", which one transcript holds once with its capital and
twice as the ordinary word. An entry ticked Also an ordinary word flags only the find with the capital letter, holds it
for review as Review each does (never replaced by `names replace`, nor taken by an agent), and is replaced only when the
app's own Review and replace ticks it. An old entry with Match case reads as the new tick and is written in the new
shape on the next save. `names add --ordinary-word`, `names set --ordinary-word`, MCP's `names_add` and `names_set`
with `word`, the key file's fifth column and the label check honour it. No answer, record line or agent log line holds
the real name."""
from __future__ import annotations

import hashlib
import json
import os
import re
import shutil
from pathlib import Path

import openpyxl

from . import support
from .support import check

# the name, an English word as well, and a second invented spelling the demo does not hold
NAME = "Will"
OTHER = "Wilbur"
CAP = re.compile(r"(?<![^\W_])Will(?![^\W_])")
LOW = re.compile(r"(?<![^\W_])will(?![^\W_])")


def digest(root: Path) -> dict:
    return {p.relative_to(root).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in sorted(root.rglob("*")) if p.is_file() and not p.name.endswith(".lock")}


def text_of(book: Path) -> str:
    wb = openpyxl.load_workbook(book)
    try:
        return "\n".join(str(v) for ws in wb.worksheets for row in ws.iter_rows(values_only=True) for v in row
                         if isinstance(v, str))
    finally:
        wb.close()


def leaked(blob) -> list:
    s = blob if isinstance(blob, str) else json.dumps(blob)
    return ([OTHER] if OTHER in s else []) + (["Will"] if CAP.search(s) else [])


def test_ordinary_word(scratch: Path):
    print("\n407. Also an ordinary word on the list of names: only the capitalised find flagged, held for review and "
          "never replaced in bulk, an old Match case read as it, names add and set with the new option, and no real "
          "name said back (ordinaryword, 16 November)")
    import agent_changes
    import agent_log
    import cli
    import idiograph_routes as routes
    import mcp_server
    import names as names_mod
    import participants as people_mod
    import server as server_mod

    base = scratch / "ordinary-word-407"
    shutil.rmtree(base, ignore_errors=True)
    root = base / "Bees at home"
    root.mkdir(parents=True)
    (root / server_mod.PROJECT_FILE).write_text(json.dumps({
        "name": "Bees at home", "research_question": support.DEMO_QUESTION,
        "agents": {"allowed": True, "at": "2026-11-16T09:00:00+00:00"}}), encoding="utf-8")
    shipped = support.DEMO_SHIPPED
    for n, who in enumerate(("Juno", "Mabel", "Rowan"), start=1):
        folder = root / f"P{n} - {who}"
        (folder / "Working").mkdir(parents=True)
        shutil.copy2(shipped / f"{who} - EN & ES.xlsx", folder / f"{who} - EN & ES.xlsx")
        for side in sorted((shipped / "Working").glob(f"{who} - EN & ES.*")):
            shutil.copy2(side, folder / "Working" / side.name)
    books = [next(root.glob(f"P{n}*")) / f"{w} - EN & ES.xlsx" for n, w in ((1, "Juno"), (2, "Mabel"), (3, "Rowan"))]
    cfg = base / "config.json"
    cfg.write_text(json.dumps({"projects": [], "interviewer": "Interviewer"}), encoding="utf-8")
    config = base / "agent-config.json"
    config.write_text(json.dumps({"root": str(root), "interviewer": "Interviewer"}), encoding="utf-8")
    log = base / "agent-log.json"
    kept = (server_mod.CONFIG_PATH, server_mod.ROOT_OVERRIDE, server_mod.STATE_PATH, server_mod.STATE_MEMORY,
            agent_changes.ALL_OPS, os.environ.get(agent_log.PLACE))
    outs: list[str] = []

    def run(*args, tool="Claude Code"):
        given = ["--config", str(config), "--root", str(root), "--json", *args] + (["--tool", tool] if tool else [])
        code, out, err = cli.run(given)
        outs.append(out + err)
        return code, (support.plain(json.loads(out)) if out.strip() and code == 0 else {}), err + (out if code else "")

    try:
        server_mod.CONFIG_PATH, server_mod.ROOT_OVERRIDE = cfg, None
        server_mod.STATE_PATH, server_mod.STATE_MEMORY = base / "state.json", {"recent": []}
        agent_changes.ALL_OPS = None
        os.environ[agent_log.PLACE] = str(log)
        routes.add_project(root)
        rid = routes.project_id(root)
        texts = [text_of(b) for b in books]
        caps = sum(len(CAP.findall(t)) for t in texts)
        lows = sum(len(LOW.findall(t)) for t in texts)
        check("407: the demo holds the name with its capital and as the ordinary word", caps >= 1 and lows >= 1,
              f"{caps} {lows}")

        # ── 1. an old list's Match case reads as Also an ordinary word, and is written so on the next save
        listed = root / names_mod.FILE
        listed.write_text(json.dumps({"entries": [{"real": [NAME, OTHER], "to": "[son]", "for": None, "case": True}]}),
                          encoding="utf-8")
        read = routes.pseudo_list(root)
        app_list = routes.api_names({"op": "list", "root": rid})
        code, agent_list, err = run("names", "list", tool=None)
        check("407: an old entry with Match case reads as Also an ordinary word, the app's list and an agent's alike",
              read == [{"real": [NAME, OTHER], "to": "[son]", "for": None, "word": True}]
              and app_list["entries"][0].get("word") is True and "case" not in app_list["entries"][0]
              and code == 0 and agent_list["entries"][0] == {"entry": 1, "to": "[son]", "for": None, "spellings": 2,
                                                             "word": True}, err + json.dumps(agent_list)[:300])
        routes.api_names({"op": "set", "root": rid, "entries": [dict(e) for e in app_list["entries"]]})
        saved = json.loads(listed.read_text(encoding="utf-8"))["entries"]
        check("407: the next save writes the entry in the new shape, no Match case left",
              saved == [{"real": [NAME, OTHER], "to": "[son]", "for": None, "word": True}], json.dumps(saved))
        start = digest(root)

        # ── 2. only the capitalised find is flagged, and it waits for review
        code, checked, err = run("names", "check", tool=None)
        app_check = routes.api_names({"op": "check", "root": rid, "names_preview": True})
        finds = app_check["names"]["finds"]
        check("407: names check flags each capitalised find and none of the ordinary word, every one left for review",
              code == 0 and checked["names"]["replaced"] == 0 and checked["names"]["left"] == caps
              and checked["names"]["by_entry"][0].get("word") is True
              and len(finds) == caps and all(f["found"] == NAME and f["review"] and f["word"] and f["skipped"]
                                             for f in finds), err + json.dumps(checked)[:300])

        # ── 3. a bulk replace, an agent's and the app's alike, leaves the held finds; an agent cannot take one
        code, dry, err = run("names", "replace", "--note", "Replace the names", "--dry-run")
        code2, done, err2 = run("names", "replace", "--note", "Replace the names", "--run", "bulk")
        routes.api_names({"op": "replace", "root": rid})
        after = [text_of(b) for b in books]
        try:
            routes.api_names({"op": "replace", "root": rid, "take": ["1:1"], "tool": "Claude Code", "request": "x"})
            took = ""
        except Exception as exc:
            took = str(exc)
        check("407: a bulk replace leaves every held find as written, the ordinary word untouched, and an agent's take "
              "is refused",
              code == 0 and code2 == 0 and dry["names"]["replaced"] == 0 and done["names"]["replaced"] == 0
              and done["names"]["left"] == caps and after == texts and "[son]" not in "".join(after)
              and "Review each or Also an ordinary word" in took, err + err2 + took)
        check("407: nothing was written by the replaces that replaced nothing, the list and workbooks as they were",
              {k: v for k, v in digest(root).items() if not k.startswith((".idiograph-restore", "idiograph-agent"))}
              == {k: v for k, v in start.items() if not k.startswith((".idiograph-restore", "idiograph-agent"))})

        # ── 4. the app's Review and replace ticks one: that alone is replaced, the ordinary word kept
        routes.api_names({"op": "replace", "root": rid, "take": ["1:1"]})
        ticked = "\n".join(text_of(b) for b in books)
        check("407: the find he ticks in Review and replace is replaced, the rest as written",
              ticked.count("[son]") == 1 and len(CAP.findall(ticked)) == caps - 1 and len(LOW.findall(ticked)) == lows,
              str(ticked.count("[son]")))

        # ── 5. the label and pen portrait check finds the name in its case alone
        word_list = routes.pseudo_list(root)
        check("407: the label check refuses the name with its capital and lets the ordinary word through",
              people_mod.real_name_in("Will and the bees", word_list) == 1
              and people_mod.real_name_in("the will to keep bees", word_list) is None)

        # ── 6. the key file keeps the tick in a fifth column, a four-column key reading as before
        back = names_mod.read_key("key.csv", names_mod.write_key(word_list).encode("utf-8"))
        four = names_mod.read_key("key.csv", f"Real name,Pseudonym,Review each,Except in\n{OTHER},[son],,\n".encode("utf-8"))
        check("407: the key file keeps Also an ordinary word, and a key without that column reads with it off",
              back[0].get("word") is True and "word" not in four[0], json.dumps(back))

        # ── 7. names add and names set with the new option, dry run first, then MCP's
        mid = digest(root)
        code, add_dry, err = run("names", "add", "--real", "Hope", "--to", "[daughter]", "--ordinary-word",
                                 "--note", "Add Hope as a name that is also a word", "--dry-run")
        unwritten = digest(root) == mid
        code2, added, err2 = run("names", "add", "--real", "Hope", "--to", "[daughter]", "--ordinary-word",
                                 "--note", "Add Hope as a name that is also a word", "--run", "add")
        check("407: names add --ordinary-word: its dry run writes nothing, then the entry is ticked",
              code == 0 and add_dry["dry_run"] is True and add_dry["entries"][0].get("word") is True and unwritten
              and code2 == 0 and routes.pseudo_list(root)[-1] == {"real": ["Hope"], "to": "[daughter]", "for": None,
                                                                   "word": True},
              err + err2 + json.dumps(add_dry)[:200] + json.dumps(routes.pseudo_list(root)[-1]))
        code, set_dry, err = run("names", "set", "1", "--ordinary-word", "off", "--note", "Replace Will everywhere",
                                 "--dry-run")
        check("407: names set --ordinary-word off says the tick goes and that a replace would then write the finds, "
              "the ordinary word among them",
              code == 0 and set_dry["changed"] == {"word": {"before": True, "after": False}}
              and set_dry["finds"]["before"]["replaced"] == 0
              and set_dry["finds"]["after"]["replaced"] == caps - 1 + lows, err + json.dumps(set_dry)[:300])
        srv = mcp_server.Server(str(root), config=str(config))
        srv.receive(json.dumps({"jsonrpc": "2.0", "id": 0, "method": "initialize",
                                "params": {"protocolVersion": "2025-06-18", "clientInfo": {"name": "claude-code"}}}))

        def call(name, args, n):
            got = srv.receive(json.dumps({"jsonrpc": "2.0", "id": n, "method": "tools/call",
                                          "params": {"name": name, "arguments": args}}))["result"]
            outs.append(json.dumps(got))
            return got

        tools = {t["name"]: t for t in srv.receive(json.dumps({"jsonrpc": "2.0", "id": 9, "method": "tools/list"}))["result"]["tools"]}
        m_add = call("names_add", {"entries": [{"real": ["Faith"], "to": "[aunt]", "word": True}],
                                   "request": "Add Faith, a word too"}, 1)
        m_set = call("names_set", {"entry": 2, "word": False, "request": "Hope is only ever the name"}, 2)
        listed_now = routes.pseudo_list(root)
        check("407: MCP's names_add and names_set take word, its schema saying so, and Match case is gone from both",
              "word" in tools["names_add"]["inputSchema"]["properties"]["entries"]["items"]["properties"]
              and "case" not in tools["names_add"]["inputSchema"]["properties"]["entries"]["items"]["properties"]
              and "word" in tools["names_set"]["inputSchema"]["properties"]
              and "case" not in tools["names_set"]["inputSchema"]["properties"]
              and not m_add.get("isError") and not m_set.get("isError")
              and listed_now[-1].get("word") is True and "word" not in listed_now[1],
              json.dumps([m_add, m_set])[:500])

        # ── 9. (wordfix M1) the tick finds a capital first letter, the rest in any case, however the list spells it
        said = "Hope came. I hope so. HOPE! hope."
        found = {sp: [h["found"] for h in names_mod.find(said, [names_mod.clean_entry(
            {"real": sp, "to": "[daughter]", "word": True})], None)] for sp in ("Hope", "hope")}
        lower_key = names_mod.read_key("key.csv", "Real name,Pseudonym,Review each,Except in,Also an ordinary word\n"
                                                  "hope,[daughter],,,yes\n".encode("utf-8"))
        check("407: Also an ordinary word flags Hope and HOPE and never hope, whether the list holds Hope or hope, a "
              "lower-case key file cell alike, and a bulk replace leaves them",
              found == {"Hope": ["Hope", "HOPE"], "hope": ["Hope", "HOPE"]}
              and [h["found"] for h in names_mod.find(said, lower_key, None)] == ["Hope", "HOPE"]
              and names_mod.plain(said, lower_key, None) == said, json.dumps(found))
        # the capitalised find was ticked and replaced in 4., so the transcripts hold the ordinary word alone now
        code, low_dry, err = run("names", "add", "--real", NAME.lower(), "--to", "[son]", "--ordinary-word",
                                 "--note", "Add will, a word too", "--dry-run")
        check("407: an agent's lower-case --real counts the capitalised finds alone, never the ordinary word",
              code == 0 and low_dry["entries"][0]["hits"] == 0 and lows >= 1, err + json.dumps(low_dry)[:300])

        # ── 10. (wordfix M2) an old initials entry's Match case, which the old page forced, stays its own matching
        initials = names_mod.clean_entry({"real": ["T.M."], "to": "[teacher]", "for": None, "case": True})
        check("407: an old initials entry with Match case is not read as Also an ordinary word, and is still replaced "
              "in bulk, by its case",
              "word" not in initials and names_mod.plain("T.M. said, TM and T. M. and tm.", [initials], None)
              == "[teacher] said, [teacher] and [teacher] and tm.", json.dumps(initials))

        # ── 11. (wordfix L1) a new entry only a tick apart from one for the same people is refused, dry run alike
        held_list = routes.pseudo_list(root)
        faith = next(n for n, e in enumerate(held_list, start=1) if "Faith" in e["real"])
        before_l1 = digest(root)
        refusals = []
        for extra in ([], ["--ordinary-word", "--review-each"]):
            for dry_flag in (["--dry-run"], []):
                code, _out, err = run("names", "add", "--real", "Faith", "--to", "[aunt]", *extra,
                                      "--note", "Add Faith", *dry_flag)
                refusals.append((code, err))
        m_twice = call("names_add", {"entries": [{"real": ["Faith"], "to": "[aunt]"}], "request": "Add Faith"}, 3)
        check("407: names add of a spelling an entry for the same people holds, only Also an ordinary word or Review "
              "each apart, is refused in one line naming that entry and names set, dry run and MCP alike, nothing "
              "written",
              all(c != 0 and f"names set {faith}" in e and "Faith" not in e for c, e in refusals)
              and "Also an ordinary word off" in refusals[0][1] and "Review each on" in refusals[2][1]
              and m_twice.get("isError") and digest(root) == before_l1
              and routes.pseudo_list(root) == held_list, json.dumps(refusals)[:600])

        # ── 12. (wordfix M3) a REFI-QDA import's memos: a held find counted, then on the Review card and replaced
        # only when ticked
        from .a244_qdpx import at, code as qcode, package, selection
        fox = base / "Fox at home"
        fox.mkdir()
        (fox / server_mod.PROJECT_FILE).write_text(json.dumps({"name": "Fox at home", "agents": {"allowed": True, "at": "2026-11-16T09:00:00+00:00"}}), encoding="utf-8")
        routes.add_project(fox)
        fid = routes.project_id(fox)
        names_mod.save_at(fox, [{"real": ["Hope"], "to": "[daughter]", "for": None, "word": True}])
        t = "Kit: What happened in March?\nLark: The fox got in.\nKit: And now?\nLark: The run is safe.\n"
        sels = selection("q1", at(t, "The fox got in"), ["k1"])
        memo_text = "Hope rang about the fox. I hope the run holds."
        notes = f'<Note guid="n1" name="March memo"><PlainTextContent>{memo_text}</PlainTextContent></Note>'
        src = (f'<TextSource guid="t1" name="Lark interview" plainTextPath="internal://t1.txt">{sels}'
               f'<NoteRef targetGUID="n1"/></TextSource>')
        qpath = base / "fox.qdpx"
        qpath.write_bytes(package("ATLAS.ti 23.2", qcode("k1", "The fox"), src, {"Sources/t1.txt": t.encode("utf-8")},
                                  notes=notes))
        asked = {"sources": [{"source": 1, "pseudonym": "Lark"}], "memos": "source"}
        dry_q = routes.qdpx_import(fox, qpath, dict(asked))
        memo_counts = [e for e in dry_q["names"]["by_entry"] if e["entry"] == 1]
        routes.qdpx_import(fox, qpath, dict(asked), make=True)
        lark = next(fox.glob("P* - Lark"))
        memo_file = next((lark / "Source").glob("*memos*.txt"))
        check("407: a REFI-QDA import counts the memo's held find under memos as left, and writes it as it is, the "
              "ordinary word too",
              memo_counts and memo_counts[0]["left"] == 1 and memo_counts[0]["replaced"] == 0
              and memo_counts[0]["parts"].get("memos") == 1
              and memo_text in memo_file.read_text(encoding="utf-8"), json.dumps(dry_q["names"])[:400])
        fox_check = routes.api_names({"op": "check", "root": fid, "names_preview": True})
        memo_finds = [f for f in fox_check["names"]["finds"] if f["where"].get("part") == "memos"]
        fox_agent = routes.api_names({"op": "check", "root": fid, "tool": "Claude Code"})
        routes.api_names({"op": "replace", "root": fid, "tool": "Claude Code", "request": "x"})
        untouched = memo_file.read_text(encoding="utf-8")
        routes.api_names({"op": "replace", "root": fid, "take": [f"{f['entry']}:{f['nth']}" for f in memo_finds]})
        replaced_memo = memo_file.read_text(encoding="utf-8")
        check("407: Check finds the memo's held find for the Review card, an agent's replace leaves it, and his tick "
              "replaces it alone, the memos file kept in _Archive first",
              len(memo_finds) == 1 and memo_finds[0]["found"] == "Hope" and memo_finds[0]["skipped"]
              and fox_check["participants"] == 0 and fox_agent["names"]["left"] >= 1
              and "Hope" not in json.dumps(fox_agent) and memo_text in untouched
              and "[daughter] rang about the fox. I hope the run holds." in replaced_memo
              and any("memos" in p.name for p in (lark / "_Archive").glob("*pre-names*")),
              json.dumps(memo_finds)[:400] + replaced_memo[:200])

        # ── 13. (wordfix2) a memos file an agent's replace writes: kept by the run's restore point, one line in the
        # record, undone byte for byte by the change's undo and the run's; its byte order mark and line endings kept;
        # named "memos", never by its file's name; and one changed since the app's Check left as it is
        routes.api_names({"op": "set", "root": rid, "entries": [
            {"real": [NAME], "to": "[son]", "for": None, "word": True},
            {"real": ["Zebedee"], "to": "[friend]", "for": None}]})
        juno_src = books[0].parent / "Source"
        juno_src.mkdir(exist_ok=True)
        memo_b = juno_src / "Zebedee - memos.txt"
        memo_a = juno_src / "Juno - memos 2.txt"
        bom = b"\xef\xbb\xbf"
        b_bytes = bom + "Memos\r\nZebedee rang. Will came by.\r\nI will ring Zebedee.\r\n".encode("utf-8")
        a_bytes = "Will A.\r\n".encode("utf-8")
        memo_b.write_bytes(b_bytes)
        memo_a.write_bytes(a_bytes)
        code, m_dry, err = run("names", "replace", "--note", "Replace the names", "--dry-run")
        dry_same = memo_b.read_bytes() == b_bytes
        n_lines = len(agent_changes.read(root))
        code2, m_done, err2 = run("names", "replace", "--note", "Replace the names", "--run", "memos1")
        written = memo_b.read_bytes()
        m_line = agent_changes.read(root)[-1]
        check("407: an agent's replace writes the memos file's plain finds alone, its byte order mark and CRLF line "
              "endings kept, its dry run writing nothing, one line in the record naming Juno's memos",
              code == 0 and code2 == 0 and dry_same and m_dry["names"]["replaced"] == 2
              and written == bom + "Memos\r\n[friend] rang. Will came by.\r\nI will ring [friend].\r\n".encode("utf-8")
              and memo_a.read_bytes() == a_bytes
              and len(agent_changes.read(root)) == n_lines + 1 and m_line["op"] == "names replace"
              and m_line["files"] >= 1 and "Juno's memos" in m_line["what_changed"],
              err + err2 + json.dumps(m_line)[:400] + repr(written[:80]))
        said_back = json.dumps(m_dry) + json.dumps(m_done) + json.dumps(m_line)
        check("407: the memos file is named memos in an agent's counts and lines, never by its file's name",
              "Zebedee" not in said_back and "memos 2" not in said_back
              and any(p["interview"] == "memos" for e in m_done["names"]["by_entry"] for p in e["in"]),
              said_back[:500])
        code, _u, err = run("agents", "undo-change", m_line["id"], "--note", "Put the memos back")
        back_one = memo_b.read_bytes()
        code2, _again, err2 = run("names", "replace", "--note", "Replace the names", "--run", "memos2")
        r_line = agent_changes.read(root)[-1]
        code3, _u2, err3 = run("agents", "undo-run", r_line["run"], "--note", "Back as it was")
        check("407: agents undo-change and the run's undo each put the memos file back byte for byte",
              code == 0 and back_one == b_bytes and code2 == 0 and r_line["run"] != m_line["run"]
              and code3 == 0 and memo_b.read_bytes() == b_bytes, err + err2 + err3)
        app_m = routes.api_names({"op": "check", "root": rid, "names_preview": True})
        held_m = [f for f in app_m["names"]["finds"] if f["where"].get("part") == "memos" and f["found"] == NAME]
        seen_m = app_m.get("memos_seen") or []
        # the first memos file in order changes after Check: one more find of the held name
        memo_a.write_bytes("Will A. Will again.\r\n".encode("utf-8"))
        take_b = [f"{f['entry']}:{f['nth']}" for f in held_m[1:2]]
        moved = routes.api_names({"op": "replace", "root": rid, "take": take_b, "memos_seen": seen_m})
        check("407: a Replace whose memos file changed since Check leaves that file as it is and counts it, and the "
              "find he ticked in the next file is still the one replaced",
              len(held_m) == 2 and len(seen_m) == 2 and moved["memos_changed"] == 1
              and memo_a.read_bytes() == "Will A. Will again.\r\n".encode("utf-8")
              and "[son] came by." in memo_b.read_text(encoding="utf-8-sig")
              and "[friend] rang." in memo_b.read_text(encoding="utf-8-sig")
              and moved["names"]["left"] >= 2, json.dumps(moved)[:400] + json.dumps(seen_m))

        # ── 13b. (memoscase) a memos file in a folder named `source`, not `Source` (a disk that ignores case would
        # open it): left untouched and uncounted, by the app's Check and an agent's replace alike, so no write
        # escapes the record and the restore point
        low_src = books[1].parent / "source"
        if not (books[1].parent / "Source").exists():
            low_src.mkdir()
            low_memo = low_src / "Zebedee - memos.txt"
            low_bytes = "Zebedee rang. Will came by.\r\n".encode("utf-8")
            low_memo.write_bytes(low_bytes)
            n_before = len(agent_changes.read(root))
            code, l_done, err = run("names", "replace", "--note", "Replace the names", "--run", "memos3")
            lines_after = agent_changes.read(root)[n_before:]
            app_l = routes.api_names({"op": "check", "root": rid, "names_preview": True})
            in_low = [f for f in app_l["names"]["finds"] if f["where"].get("participant") == "Mabel"
                      and f["where"].get("part") == "memos"]
            check("407: a memos file in a folder named source, not Source, is left as it is and counted by neither "
                  "Check nor an agent's replace",
                  code == 0 and low_memo.read_bytes() == low_bytes and not in_low
                  and not any("Mabel's memos" in (ln.get("what_changed") or "") for ln in lines_after),
                  err + json.dumps(l_done)[:300] + json.dumps(in_low)[:200])

        # ── 8. nothing said back anywhere: every answer, the record and the agent log
        agent_log.flush()
        log_text = log.read_text(encoding="utf-8") if log.exists() else ""
        record = (root / agent_changes.FILE).read_text(encoding="utf-8")
        check("407: no answer, record line or agent log line holds the real name",
              not leaked(" ".join(outs)) and not leaked(record) and not leaked(log_text)
              and "Hope" not in record and "Faith" not in record and "Faith" not in log_text,
              str(leaked(" ".join(outs))) + str(leaked(record)) + str(leaked(log_text)))
    finally:
        (server_mod.CONFIG_PATH, server_mod.ROOT_OVERRIDE, server_mod.STATE_PATH, server_mod.STATE_MEMORY,
         agent_changes.ALL_OPS, place) = kept
        if place is None:
            os.environ.pop(agent_log.PLACE, None)
        else:
            os.environ[agent_log.PLACE] = place
