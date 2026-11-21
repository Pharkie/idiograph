"""Area 406: an agent changes an entry of the project's list of names, or takes one off, on his word (namesset, 16
November 2026, Adam: "if you're not able to do it via MCP or the API, you should be able to").

On the demo's three participants made a project, with invented names the demo's transcripts hold. `names set`'s dry run
writes nothing and answers each field before and after and the entry's finds before and after, counts alone. An entry
his review marked keeps the mark whatever an agent sets, so `names replace` leaves it, until his own edit of it in the
app (namesbuild, 17 November 2026, in place of Review each). Except phrases are cleared, added and taken off.
`names remove` and its undo put the list back byte for byte, as does a set's undo. An entry the list lacks is refused in
one line. No answer, record line or agent log line holds a real name or an except phrase, the command line's and the
MCP server's alike."""
from __future__ import annotations

import hashlib
import json
import os
import shutil
import stat
from pathlib import Path

import openpyxl

from . import support
from .support import check

# invented names the demo's transcripts hold: one participant's late husband, a neighbour, and the dog
REAL = ("Dennis", "Terry", "Pepper")
EXCEPT = "Pepper did a perfect sit"


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
    return [w for w in REAL + ("Denny",) if w in s] + ([EXCEPT] if EXCEPT in s else [])


def test_names_set(scratch: Path):
    print("\n406. Names changed and taken off the list by an agent on his word: the dry run's fields and counts with "
          "nothing written, a marked entry left until his own edit, except phrases set and cleared, remove and undo "
          "byte for byte, and no real name said back (namesset, 16 November)")
    import agent_changes
    import agent_log
    import cli
    import idiograph_routes as routes
    import mcp_server
    import names as names_mod
    import server as server_mod

    base = scratch / "names-set-406"
    shutil.rmtree(base, ignore_errors=True)
    root = base / "Dogs at home"
    root.mkdir(parents=True)
    (root / server_mod.PROJECT_FILE).write_text(json.dumps({
        "name": "Dogs at home", "research_question": support.DEMO_QUESTION,
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
        # the list as he made it in the app
        routes.api_names({"op": "set", "root": rid, "entries": [
            {"real": ["Dennis"], "to": "[husband]", "for": "Mabel"},
            {"real": ["Terry"], "to": "[neighbour]"},
            {"real": ["Pepper"], "to": "[dog]", "except": [EXCEPT]}]})
        listed = root / names_mod.FILE
        # a find of the neighbour unticked in his review marked the entry (namesbuild)
        names_mod.save_at(root, names_mod.with_marks(routes.pseudo_list(root), {1}))
        texts = [text_of(b) for b in books]
        terry = sum(t.count("Terry") for t in texts)
        pepper = sum(t.count("Pepper") for t in texts)
        inside = sum(t.count(EXCEPT) for t in texts)
        start = digest(root)

        # ── 1. the dry run: each field before and after, the finds before and after, nothing written
        code, dry, err = run("names", "set", "2", "--to", "[next door]", "--note", "Terry as next door",
                             "--dry-run")
        check("406: set's dry run says the field before and after, and that a replace leaves the marked entry's finds "
              "before and after, since no agent clears the mark",
              code == 0 and dry["dry_run"] is True and dry["entry"] == 2
              and dry["changed"] == {"to": {"before": "[neighbour]", "after": "[next door]"}}
              and dry["finds"]["before"]["replaced"] == 0 and dry["finds"]["before"]["left"] == terry and terry >= 3
              and dry["finds"]["after"]["replaced"] == 0 and dry["finds"]["after"]["hits"] == terry
              and dry["finds"]["after"]["by_participant"], err + json.dumps(dry)[:500])
        check("406: the dry run writes nothing: the list, the record, the restore store all as they were",
              digest(root) == start and not (root / agent_changes.FILE).exists()
              and not (root / agent_changes.STORE).exists())

        # ── 2. the except phrases: cleared, added back, one not held refused without being said back
        code, cleared, err = run("names", "set", "3", "--no-except", "--dry-run")
        check("406: clearing the except phrases counts the finds inside them as flagged again",
              code == 0 and cleared["changed"] == {"except": {"before": 1, "after": 0}} and inside >= 1
              and cleared["finds"]["before"]["hits"] == pepper - inside and cleared["finds"]["after"]["hits"] == pepper,
              err + json.dumps(cleared)[:400])
        spec = base / "changes.json"
        spec.write_text(json.dumps({"except": []}), encoding="utf-8")
        code, _c, err = run("names", "set", "3", "--from", str(spec), "--note", "Clear the dog's phrase", "--run", "ex")
        cleared_list = routes.pseudo_list(root)
        code2, _a, err2 = run("names", "set", "3", "--except-add", EXCEPT, "--except-add", "Pepper the pup",
                              "--note", f"Add back {EXCEPT}", "--run", "ex")
        added_list = routes.pseudo_list(root)
        code3, _r, err3 = run("names", "set", "3", "--except-remove", "pepper THE pup", "--note", "x", "--run", "ex")
        check("406: except phrases set, cleared, added and taken off (case ignored), the rest of the entry as it was",
              code == 0 and code2 == 0 and code3 == 0 and "except" not in cleared_list[2]
              and added_list[2]["except"] == [EXCEPT, "Pepper the pup"]
              and routes.pseudo_list(root)[2] == {"real": ["Pepper"], "to": "[dog]", "for": None,
                                                  "except": [EXCEPT]}, err + err2 + err3)
        before_bad = listed.read_bytes()

        # ── 2b. a guess is never confirmed: right and wrong spellings and phrases answer alike, dry and real (review)
        def asked(*args):
            code_, got, err_ = run("names", "set", *args, "--note", "x", "--run", "guess")
            return code_, got.get("changed"), err_

        guesses = [(("1", "--real", "Dennis"), ("1", "--real", "Derek")),
                   (("3", "--except-add", EXCEPT), ("3", "--except-add", "Pepper sat down")),
                   (("3", "--except", EXCEPT), ("3", "--except", "Pepper sat down")),
                   (("3", "--except-remove", EXCEPT), ("3", "--except-remove", "Pepper rolled over"))]
        same = []
        for right, wrong in guesses:
            for dry_flag in (("--dry-run",), ()):
                kept_list = listed.read_bytes()
                n0 = len(agent_changes.read(root))
                r = asked(*right, *dry_flag)
                n_right = len(agent_changes.read(root)) - n0
                listed.write_bytes(kept_list)
                n0 = len(agent_changes.read(root))
                w = asked(*wrong, *dry_flag)
                n_wrong = len(agent_changes.read(root)) - n0
                listed.write_bytes(kept_list)
                same.append((right[1:], dry_flag, r[0] == w[0] == 0, r[1] == w[1] and bool(r[1]), n_right == n_wrong,
                             r[2] + w[2]))
        check("406: a right and a wrong guess of a spelling or an except phrase give the same answer and the same record, "
              "dry and real, a phrase to take off that the entry lacks passed by (namesset review)",
              all(ok_code and ok_same and ok_rec for _a, _d, ok_code, ok_same, ok_rec, _e in same)
              and listed.read_bytes() == before_bad,
              json.dumps([(a[0], d, c, s, n, e[:120]) for a, d, c, s, n, e in same if not (c and s and n)]))

        # ── 2c. an entry holding forty except phrases refuses every add alike, a held phrase and a guess (lowsfix)
        full_list = routes.pseudo_list(root)
        full = [dict(e) for e in full_list]
        full[2]["except"] = [f"phrase number {n}" for n in range(40)]
        names_mod.save_at(root, full)
        full_bytes = listed.read_bytes()
        refusals = [run("names", "set", "3", "--except-add", phrase, "--note", "x", "--run", "full")
                    for phrase in ("phrase number 7", "a phrase it does not hold")]
        check("406: an entry holding forty except phrases refuses an add of a held phrase and of a guess alike, nothing "
              "written",
              all(c != 0 and "40" in e for c, _g, e in refusals) and listed.read_bytes() == full_bytes,
              json.dumps([(c, e[:100]) for c, _g, e in refusals]))
        names_mod.save_at(root, full_list)

        # a rename's write of the list keeps an entry the store cannot take, never dropping it (lowsfix)
        import case_files
        odd = {"real": [], "to": "[odd]", "for": None}
        case_files.names_write(root, listed, {"entries": full_list + [odd]})
        check("406: a rename's write of the list keeps an entry the store cannot read as it is",
              json.loads(listed.read_text(encoding="utf-8"))["entries"][-1] == odd
              and len(json.loads(listed.read_text(encoding="utf-8"))["entries"]) == len(full_list) + 1)
        names_mod.save_at(root, full_list)

        # ── 3. an entry the list lacks, a participant the project lacks, a change that is none
        code, _x, err = run("names", "set", "9", "--to", "[x]", "--note", "x")
        code2, _y, err2 = run("names", "remove", "9", "--note", "x")
        code3, _z, err3 = run("names", "set", "1", "--for", "Nobody", "--note", "x")
        check("406: an entry the list does not have is refused in one line, set and remove alike, and a participant "
              "the project lacks too, nothing written",
              code != 0 and code2 != 0 and "no entry 9" in err and "no entry 9" in err2 and code3 != 0
              and "Juno" in err3 and listed.read_bytes() == before_bad, err + err2 + err3)
        n_lines = len(agent_changes.read(root))
        code, same, err = run("names", "set", "2", "--to", "[neighbour]", "--note", "x", "--run", "same")
        check("406: a change to what the entry is already writes nothing and keeps no line",
              code == 0 and same["changed"] == {} and listed.read_bytes() == before_bad
              and len(agent_changes.read(root)) == n_lines, err)

        # ── 4. a set undone, then a remove undone, each byte for byte
        held = listed.read_bytes()
        code, moved, err = run("names", "set", "1", "--for", "everyone", "--real", "Dennis, Denny", "--to", "[partner]",
                               "--note", "Dennis and Denny for everyone", "--run", "who")
        line = agent_changes.read(root)[-1]
        now = routes.pseudo_list(root)[0]
        check("406: set changes whom it is for, the spellings and the replacement, one line in the record with his "
              "request kept as …",
              code == 0 and now == {"real": ["Dennis", "Denny"], "to": "[partner]", "for": None}
              and set(moved["changed"]) == {"for", "real", "to"}
              and moved["changed"]["real"] == {"before": 1, "after": 2}
              and line["op"] == "names set" and line["request"] == "…" and line["files"] == 1 and not leaked(line)
              and line["what_changed"].startswith("Changed entry 1 ") and "whom it is for" in line["what_changed"]
              and (os.name == "nt" or stat.S_IMODE(listed.stat().st_mode) == 0o600), err + json.dumps(line)[:300])
        code, _u, err = run("agents", "undo-change", line["id"], "--note", "Put entry 1 back")
        check("406: agents undo-change puts the entry back byte for byte", code == 0 and listed.read_bytes() == held, err)
        code, gone, err = run("names", "remove", "1", "--dry-run")
        check("406: remove's dry run names the entry by number and counts the finds it flagged, nothing written",
              code == 0 and gone["dry_run"] is True and gone["removed"] == 1 and gone["gone"][0]["entry"] == 1
              and gone["gone"][0]["to"] == "[husband]" and gone["gone"][0]["hits"] >= 4
              and [p["participant"] for p in gone["gone"][0]["by_participant"]] == ["Mabel"]
              and listed.read_bytes() == held, err + json.dumps(gone)[:400])
        code, removed, err = run("names", "remove", "1", "--note", "Take Dennis off the list", "--run", "rm")
        line = agent_changes.read(root)[-1]
        check("406: an agent's remove is no longer refused: the entry taken off, the rest numbered again, one line in "
              "the record",
              code == 0 and removed["count"] == 2 and [e["to"] for e in routes.pseudo_list(root)] == ["[neighbour]", "[dog]"]
              and line["op"] == "names remove" and line["request"] == "…" and not leaked(line)
              and line["what_changed"] == "Took entry 1 off the list of names to replace.", err + line["what_changed"])
        code, _u, err = run("agents", "undo-run", line["run"], "--note", "Back as it was")
        check("406: the remove's run undone puts the list back byte for byte, mode 600",
              code == 0 and listed.read_bytes() == held
              and (os.name == "nt" or stat.S_IMODE(listed.stat().st_mode) == 0o600), err)
        # an entry he unticked is the app's alone to take off (namesfix M1), so the mark goes first, and comes back after
        marked_bytes = listed.read_bytes()
        names_mod.save_at(root, [{k: v for k, v in e.items() if k != "unticked"} for e in routes.pseudo_list(root)])
        unmarked = listed.read_bytes()
        code, _r, err = run("names", "remove", "1", "2", "3", "--note", "Clear the list", "--run", "all")
        line = agent_changes.read(root)[-1]
        gone_file = not listed.exists()
        code2, _u, err2 = run("agents", "undo-change", line["id"], "--note", "Undo")
        check("406: taking every entry off takes the file away, and the undo brings it back byte for byte",
              code == 0 and gone_file and code2 == 0 and listed.read_bytes() == unmarked, err + err2)
        listed.write_bytes(marked_bytes)

        # ── 5. the mark an agent's set keeps; his own edit of the entry in the app clears it, and a replace then writes
        code, held_back, err = run("names", "replace", "--note", "x", "--dry-run")
        code, _s, err = run("names", "set", "2", "--to", "[next door]", "--note", "Terry as next door", "--run", "rv")
        kept_mark = routes.pseudo_list(root)[1].get("unticked") is True
        right = run("names", "set", "2", "--real", "Terry", "--note", "x", "--dry-run")
        wrong = run("names", "set", "2", "--real", "Terence", "--note", "x", "--dry-run")
        check("406: an agent's set of a marked entry's spellings is refused the same for a right guess and a wrong one "
              "(lowsfix)",
              right[0] != 0 and wrong[0] != 0 and right[2] == wrong[2]
              and routes.pseudo_list(root)[1]["real"] == ["Terry"], right[2] + wrong[2])
        his = [{k: v for k, v in e.items() if k not in ("entry", "unticked")}
               for e in routes.api_names({"op": "list", "root": rid})["entries"]]
        his[1]["to"] = "[neighbour]"
        routes.api_names({"op": "set", "root": rid, "entries": his})
        code2, done, err2 = run("names", "replace", "--note", "Replace them", "--run", "rv2")
        mabel_now = "\n".join(text_of(b) for b in books)
        check("406: an agent's set keeps the mark, and once his own edit clears it names replace writes every find it "
              "held back",
              held_back["names"]["left"] >= terry and held_back["names"]["held"] == 1 and code == 0 and kept_mark
              and code2 == 0 and "Terry" not in mabel_now and mabel_now.count("[neighbour]") >= terry
              and EXCEPT in mabel_now, err + err2)

        # ── 6. MCP: names_set and names_remove, no name in any answer
        srv = mcp_server.Server(str(root), config=str(config))
        srv.receive(json.dumps({"jsonrpc": "2.0", "id": 0, "method": "initialize",
                                "params": {"protocolVersion": "2025-06-18", "clientInfo": {"name": "claude-code"}}}))

        def call(name, args, n):
            got = srv.receive(json.dumps({"jsonrpc": "2.0", "id": n, "method": "tools/call",
                                          "params": {"name": name, "arguments": args}}))["result"]
            outs.append(json.dumps(got))
            return got

        tools = {t["name"]: t for t in srv.receive(json.dumps({"jsonrpc": "2.0", "id": 9, "method": "tools/list"}))["result"]["tools"]}
        check("406: the MCP server lists names_set, a tool that writes", "names_set" in tools
              and tools["names_set"]["annotations"]["readOnlyHint"] is False)
        count = len(agent_changes.read(root))
        m_dry = call("names_set", {"entry": 3, "except_add": ["Pepper the pup"], "request": "Add Pepper the pup",
                                   "dry_run": True}, 1)
        m_set = call("names_set", {"entry": 3, "to": "[pup]", "request": "Write the dog as pup"}, 2)
        m_bad = call("names_set", {"entry": 7, "to": "[x]", "request": "Change Dennis"}, 3)
        m_rm = call("names_remove", {"entries": [3], "request": "Drop Pepper", "dry_run": True}, 4)
        agent_log.flush()
        log_text = log.read_text(encoding="utf-8") if log.exists() else ""
        check("406: MCP's names_set dry run and write, a refusal and names_remove's dry run, one line for the write, no "
              "name in any answer or the agent log",
              not m_dry.get("isError") and m_dry["structuredContent"]["changed"] == {"except": {"before": 1, "added": 1}}
              and not m_set.get("isError") and routes.pseudo_list(root)[2]["to"] == "[pup]"
              and m_bad.get("isError") and not m_rm.get("isError") and m_rm["structuredContent"]["gone"][0]["entry"] == 3
              and len(agent_changes.read(root)) == count + 1 and agent_changes.read(root)[-1]["op"] == "names set"
              and not leaked(log_text) and "pup" not in log_text,
              json.dumps([m_dry, m_bad])[:500] + log_text[-300:])

        # ── 7. nothing said back anywhere: every answer, the record, History and the agent log
        record = (root / agent_changes.FILE).read_text(encoding="utf-8")
        history = (root / "idiograph-history.json").read_text(encoding="utf-8") if (root / "idiograph-history.json").exists() else ""
        check("406: no answer, record line, History line or agent log line holds a real name or an except phrase",
              not leaked(" ".join(outs)) and not leaked(record) and not leaked(history) and not leaked(log_text),
              str(leaked(" ".join(outs))) + str(leaked(record)) + str(leaked(log_text)))
    finally:
        (server_mod.CONFIG_PATH, server_mod.ROOT_OVERRIDE, server_mod.STATE_PATH, server_mod.STATE_MEMORY,
         agent_changes.ALL_OPS, place) = kept
        if place is None:
            os.environ.pop(agent_log.PLACE, None)
        else:
            os.environ[agent_log.PLACE] = place
