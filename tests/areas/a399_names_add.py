"""Area 399: an agent adds names to the project's list on his word, and the list's two exceptions (namesop, 16 November
2026, Adam: "Can you not do this via the MCP? and if not ask the idiograph coordinator to make sure that you can and
then do it.").

On the demo's three participants made a project, with invented names the demo's transcripts hold. `names add`'s dry
run writes nothing (no list, no record, no restore point) and answers counts by participant and part alone, no real
name. The add is one line in the record of agents' changes, his request with the names taken out, the list kept mode
600 and its copies in the restore store too, and `agents undo-change` and a run's undo put the list back as it was,
refused over his own later edit. A Review each entry is never replaced in bulk, by an agent or by the app's replace,
only the find he ticks (`take`, which an agent cannot give). A find inside an except phrase is never flagged nor
replaced. Every read an agent makes, the command line's and the MCP server's, says no real name, and a refusal's
request in the agent log has the names taken out."""
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
ASKED = "Add Dennis as her husband, Terry to review, and Pepper the dog"


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
    return [w for w in REAL if w in s] + ([EXCEPT] if EXCEPT in s else [])


def test_names_add(scratch: Path):
    print("\n399. Names added by an agent on his word: the dry run's counts and nothing written, the add recorded and "
          "undone, Review each never replaced in bulk, an except phrase never flagged, and no real name said back "
          "(namesop, 16 November)")
    import agent_changes
    import agent_log
    import cli
    import idiograph_routes as routes
    import mcp_server
    import names as names_mod
    import server as server_mod

    base = scratch / "names-add-399"
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
    # by the folder made above, never its name written out, which area 74 reads as a name kept from the demo's text
    mabel = next(root.glob("P2*")) / "Mabel - EN & ES.xlsx"
    start_text = text_of(mabel)
    cfg = base / "config.json"
    cfg.write_text(json.dumps({"projects": [], "interviewer": "Interviewer"}), encoding="utf-8")
    config = base / "agent-config.json"
    config.write_text(json.dumps({"root": str(root), "interviewer": "Interviewer"}), encoding="utf-8")
    log = base / "agent-log.json"
    kept = (server_mod.CONFIG_PATH, server_mod.ROOT_OVERRIDE, server_mod.STATE_PATH, server_mod.STATE_MEMORY,
            agent_changes.ALL_OPS, os.environ.get(agent_log.PLACE))
    spec = base / "names.json"
    spec.write_text(json.dumps([
        {"real": ["Dennis"], "to": "[husband]", "for": "Mabel"},
        {"real": ["Terry"], "to": "[neighbour]", "review": True},
        {"real": ["Pepper"], "to": "[dog]", "except": [EXCEPT]}]), encoding="utf-8")

    def run(*args, tool="Claude Code"):
        given = ["--config", str(config), "--root", str(root), "--json", *args] + (["--tool", tool] if tool else [])
        code, out, err = cli.run(given)
        return code, (support.plain(json.loads(out)) if out.strip() and code == 0 else {}), err + (out if code else ""), out

    try:
        server_mod.CONFIG_PATH, server_mod.ROOT_OVERRIDE = cfg, None
        server_mod.STATE_PATH, server_mod.STATE_MEMORY = base / "state.json", {"recent": []}
        agent_changes.ALL_OPS = None
        os.environ[agent_log.PLACE] = str(log)
        routes.add_project(root)
        rid = routes.project_id(root)
        start = digest(root)

        # ── 1. the dry run: counts by participant and part, nothing written, no real name said back
        code, dry, err, out = run("names", "add", "--from", str(spec), "--dry-run")
        rows = {e["to"]: e for e in dry.get("entries", [])}
        husband = rows.get("[husband]", {})
        places = {p["participant"]: p for p in husband.get("by_participant", [])}
        texts = [text_of(root / f"P{n} - {w}" / f"{w} - EN & ES.xlsx") for n, w in ((1, "Juno"), (2, "Mabel"), (3, "Rowan"))]
        pepper_all = sum(t.count("Pepper") for t in texts)
        inside = sum(t.count(EXCEPT) for t in texts)
        check("399: the dry run counts each new entry's finds by participant and by part, the transcript, statements "
              "and notes among them",
              code == 0 and dry["dry_run"] is True and dry["added"] == 3 and husband.get("entry") == 1
              and list(places) == ["Mabel"] and places["Mabel"]["transcript"] >= 4 and places["Mabel"]["notes"] >= 1
              and places["Mabel"]["statements"] >= 1 and husband["hits"] == sum(
                  places["Mabel"][k] for k in ("transcript", "quotes", "statements", "notes"))
              and rows["[neighbour]"].get("review") is True and rows["[dog]"].get("excepts") == 1,
              err + json.dumps(dry)[:600])
        check("399: an except phrase's find is never flagged, so the dog's count leaves out the finds inside it",
              inside >= 1 and rows.get("[dog]", {}).get("hits") == pepper_all - inside,
              f"{rows.get('[dog]', {}).get('hits')} of {pepper_all}, {inside} inside")
        check("399: the dry run writes nothing: no list, no record, no restore point, every file as it was",
              digest(root) == start and not (root / names_mod.FILE).exists()
              and not (root / agent_changes.FILE).exists() and not (root / agent_changes.STORE).exists())
        check("399: the dry run's answer and its lines say no real name", not leaked(out), str(leaked(out)))

        # ── 2. the add: one line in the record, his request with the names out, the list mode 600
        code, added, err, out = run("names", "add", "--from", str(spec), "--note", ASKED, "--run", "first")
        lines = agent_changes.read(root)
        listed = root / names_mod.FILE
        mode = stat.S_IMODE(listed.stat().st_mode) if listed.exists() else 0
        check("399: the add writes the list, mode 600, three entries as given, and says no real name",
              code == 0 and added["added"] == 3 and added["count"] == 3 and listed.is_file()
              and (mode == 0o600 or os.name == "nt") and [e["real"] for e in routes.pseudo_list(root)] == [
                  ["Dennis"], ["Terry"], ["Pepper"]]
              and routes.pseudo_list(root)[1].get("review") is True and routes.pseudo_list(root)[2]["except"] == [EXCEPT]
              and not leaked(out), err + str(leaked(out)))
        check("399: the add is one line in the record of agents' changes, the list named, his request kept as … "
              "(namesfix2)",
              len(lines) == 1 and lines[0]["op"] == "names add" and lines[0]["files"] == 1
              and "list of names" in lines[0]["what_changed"] and not leaked(lines[0])
              and lines[0]["request"] == "…", json.dumps(lines)[:500])
        objs = [p for p in (root / agent_changes.STORE / "objects").iterdir() if p.is_file()]
        check("399: the list's copy in the restore store is read by its owner alone",
              os.name == "nt" or all(stat.S_IMODE(p.stat().st_mode) == 0o600 for p in objs), str(len(objs)))
        code, again, err, _ = run("names", "add", "--real", "dennis", "--to", "[husband]", "--for", "Mabel",
                                  "--note", "again", "--dry-run")
        code_n, fresh_, err_n, _ = run("names", "add", "--real", "Dot", "--to", "[husband]", "--for", "Mabel",
                                       "--note", "again", "--dry-run")
        listed_row = (again.get("entries") or [{}])[0]
        check("399: a dry run's counts are the new entry's own finds, the same whatever the list holds (namesfix M1)",
              code == 0 and listed_row.get("hits") == husband.get("hits") and husband.get("hits", 0) > 0
              and listed_row.get("by_participant") == husband.get("by_participant")
              and "dennis" not in json.dumps(again).lower(), err + json.dumps(again)[:300])
        check("399: a dry run answers the list as it would be saved: a name it holds listed, no number, the count the "
              "list's, a new one numbered after it (namesfix M2)",
              code_n == 0 and again["added"] == 0 and again["count"] == 3 and listed_row.get("entry") is None
              and listed_row.get("listed") is True and fresh_["added"] == 1 and fresh_["count"] == 4
              and fresh_["entries"][0]["entry"] == 4, err_n + json.dumps(again)[:300] + json.dumps(fresh_)[:300])
        held_list, n_lines = listed.read_bytes(), len(agent_changes.read(root))
        code, again, err, _ = run("names", "add", "--real", "dennis", "--to", "[husband]", "--for", "Mabel",
                                  "--note", "again", "--run", "covered")
        check("399: the add itself of a name the list holds writes nothing and says so: the list and the record "
              "unchanged, added 0, the count the list's",
              code == 0 and again["added"] == 0 and again["count"] == 3 and listed.read_bytes() == held_list
              and len(agent_changes.read(root)) == n_lines, err)
        held_app = ""
        try:
            routes.api_names({"op": "add", "root": rid, "dry_run": True,
                              "entries": [{"real": ["dennis"], "to": "[husband]", "for": "Mabel"}]})
        except Exception as exc:
            held_app = str(exc)
        check("399: the app's own add is told the holding entry's number", "Entry 1" in held_app, held_app)
        # Match case on names add is its own option, never the participant a command names (review 4)
        code, cased, err, _ = run("names", "add", "--real", "Dot", "--to", "[friend]", "--for", "Mabel", "--case",
                                  "--note", "Add Dot", "--run", "cased")
        cased_line = agent_changes.read(root)[-1]
        check("399: --case is Match case on the entry, and the record names no participant 'True'",
              code == 0 and routes.pseudo_list(root)[-1]["case"] is True and "case" not in cased_line["target"]
              and "Dot" not in json.dumps(cased_line), err + json.dumps(cased_line)[:300])
        run("agents", "undo-change", cased_line["id"], "--note", "Take Dot off")

        # ── 3. undo: the change alone, then a run's, each putting the list back as it was
        code, undone, err, _ = run("agents", "undo-change", lines[0]["id"], "--note", "Take dennis and PEPPER back off")
        undo_line = agent_changes.read(root)[-1]
        check("399: any agent's request keeps no name of the list in the record, whole words, case ignored (review 3)",
              undo_line["op"] == "agents undo-change" and "back off" in undo_line["request"]
              and "dennis" not in undo_line["request"].lower() and "pepper" not in undo_line["request"].lower(),
              undo_line["request"])
        check("399: agents undo-change takes the list away again, as it was before the add, none",
              code == 0 and not listed.exists() and routes.pseudo_list(root) == [], err)
        routes.api_names({"op": "set", "root": rid, "entries": [{"real": ["Skye"], "to": "[dog]", "for": "Rowan"}]})
        before = listed.read_bytes()
        code, _a, err, _ = run("names", "add", "--from", str(spec), "--note", ASKED, "--run", "second")
        after_add = [e["real"] for e in routes.pseudo_list(root)]
        second = agent_changes.read(root)[-1]
        code2, _u, err2, _ = run("agents", "undo-run", second["run"], "--note", "Back as it was")
        check("399: on a list he made, an add goes at its end, and the run's undo puts his list back byte for byte",
              code == 0 and after_add == [["Skye"], ["Dennis"], ["Terry"], ["Pepper"]] and code2 == 0
              and listed.read_bytes() == before and (mode == 0o600 or os.name == "nt")
              and (os.name == "nt" or stat.S_IMODE(listed.stat().st_mode) == 0o600), err + err2)
        code, _a, err, _ = run("names", "add", "--from", str(spec), "--note", ASKED, "--run", "third")
        third = agent_changes.read(root)[-1]
        routes.api_names({"op": "set", "root": rid, "entries": routes.pseudo_list(root)[:3]})
        his = listed.read_bytes()
        code2, _u, err2, _ = run("agents", "undo-change", third["id"], "--note", "Undo it")
        check("399: an undo over his own later edit of the list is refused, the list as he left it",
              code == 0 and code2 != 0 and listed.read_bytes() == his, err2)
        routes.api_names({"op": "set", "root": rid, "entries": [
            {"real": ["Dennis"], "to": "[husband]", "for": "Mabel"},
            {"real": ["Terry"], "to": "[neighbour]", "review": True},
            {"real": ["Pepper"], "to": "[dog]", "except": EXCEPT}]})

        # ── 4. Review each never bulk-replaced, the except phrase never replaced
        terry = start_text.count("Terry")
        # a copy in Source holding the Review each name in a spelling no workbook row has (review 1)
        copy = mabel.parent / "Source" / "P2-Initial.txt"
        copy.parent.mkdir(exist_ok=True)
        copy.write_text("Interviewer: Who came?\nMabel: TERRY came by, and Dennis.\n", encoding="utf-8")
        code, replaced, err, out = run("names", "replace", "--note", "Replace Dennis everywhere", "--run", "fourth")
        now = text_of(mabel)
        copied = copy.read_text(encoding="utf-8")
        check("399: a Source copy keeps a Review each name's find as written, the others replaced",
              "TERRY came by" in copied and "Dennis" not in copied and "[husband]" in copied, copied)
        history = json.loads((root / "idiograph-history.json").read_text(encoding="utf-8"))
        check("399: the replace's request keeps no listed name in History or the record (review 3)",
              "Dennis" not in json.dumps(history) and "Dennis" not in json.dumps(agent_changes.read(root)[-1]),
              json.dumps(history)[-300:])
        check("399: an agent's replace leaves every find of a Review each name as written, and says so in counts",
              code == 0 and now.count("Terry") == terry and terry >= 3 and "[neighbour]" not in now
              and "Dennis" not in now and "[husband]" in now and not leaked(out), err + str(leaked(out)))
        check("399: a find inside an except phrase is left as written, every other replaced",
              EXCEPT in now and now.replace(EXCEPT, "").count("Pepper") == 0 and "[dog]" in now, str(now.count("Pepper")))
        code, refused, err, _ = run("names", "replace", "--note", "x", "--dry-run")
        got = routes.api_names({"op": "replace", "root": rid, "dry_run": True})
        check("399: the app's own replace with nothing ticked leaves a Review each name's finds too",
              got["names"]["replaced"] == 0 and got["names"]["left"] == terry, json.dumps(got["names"])[:300])
        took = False
        try:
            routes.api_names({"op": "replace", "root": rid, "take": ["2:1"], "tool": "Claude Code", "request": "x"})
        except Exception:
            took = True
        check("399: an agent naming a Review each find to replace is refused", took and text_of(mabel).count("Terry") == terry)
        # a copy in Source holding the Review each name as the workbook spells it, twice (namesfix M3)
        second = mabel.parent / "Source" / "P2-Second.txt"
        second.write_text("Mabel: Terry came first.\nMabel: Then Terry left.\n", encoding="utf-8")
        routes.api_names({"op": "replace", "root": rid, "take": ["2:1"]})
        check("399: the app replaces the one find he ticked, the others left", text_of(mabel).count("Terry") == terry - 1)
        check("399: one ticked find of a Review each name replaces none of those words in a Source copy while others "
              "alike are left (namesfix M3)",
              second.read_text(encoding="utf-8").count("Terry") == 2 and "[neighbour]" not in second.read_text(encoding="utf-8"),
              second.read_text(encoding="utf-8"))
        run_ = names_mod.Run([{"real": ["Terry"], "to": "[neighbour]", "for": None, "case": False, "review": True}])
        check("399: a copy has a Review each name replaced where he ticked those words and left none of them",
              run_.text("Terry came.", "Mabel", {}, mirror=set(), taken={(0, "Terry")}) == "[neighbour] came."
              and run_.text("Terry came.", "Mabel", {}, mirror={(0, "Terry")}, taken={(0, "Terry")}) == "Terry came."
              and run_.text("Terry came.", "Mabel", {}, mirror=set(), taken=set()) == "Terry came.")

        # ── 5. an agent's reads: names list and check, and MCP, never a real name
        code, listed_a, err, out_l = run("names", "list", tool=None)
        code_c, checked, err_c, out_c = run("names", "check", tool=None)
        check("399: names list and names check tell an agent numbers, ticks and counts, no real name",
              code == 0 and code_c == 0 and listed_a["entries"][1].get("review") is True
              and listed_a["entries"][2].get("excepts") == 1 and not leaked(out_l) and not leaked(out_c),
              str(leaked(out_l) + leaked(out_c)))
        srv = mcp_server.Server(str(root), config=str(config))
        srv.receive(json.dumps({"jsonrpc": "2.0", "id": 0, "method": "initialize",
                                "params": {"protocolVersion": "2025-06-18", "clientInfo": {"name": "claude-code"}}}))

        def call(name, args, n):
            return srv.receive(json.dumps({"jsonrpc": "2.0", "id": n, "method": "tools/call",
                                           "params": {"name": name, "arguments": args}}))["result"]

        tools = {t["name"]: t for t in srv.receive(json.dumps({"jsonrpc": "2.0", "id": 9, "method": "tools/list"}))["result"]["tools"]}
        check("399: the MCP server lists names_add, a tool that writes",
              "names_add" in tools and tools["names_add"]["annotations"]["readOnlyHint"] is False)
        mcp_dry = call("names_add", {"entries": [{"real": ["Terry Hollis"], "to": "[neighbour]"}],
                                     "request": "Add Terry Hollis", "dry_run": True}, 1)
        mcp_list = call("names_list", {}, 2)
        count = len(agent_changes.read(root))
        mcp_bad = call("names_add", {"entries": [{"real": ["Terry Hollis"], "to": "[x]", "for": "Nobody"}],
                                     "request": "Add Terry Hollis for Nobody"}, 3)
        agent_log.flush()
        log_text = log.read_text(encoding="utf-8") if log.exists() else ""
        check("399: MCP's names_add dry run and names_list say no real name, and a refusal's request in the agent log "
              "has the name taken out",
              not mcp_dry.get("isError") and mcp_dry["structuredContent"]["dry_run"] is True
              and not leaked(mcp_dry) and not leaked(mcp_list) and "Hollis" not in json.dumps(mcp_dry)
              and mcp_bad.get("isError") and "Hollis" not in log_text and "Terry" not in log_text
              and len(agent_changes.read(root)) == count, log_text[-400:] + json.dumps(mcp_bad)[:200])
        bad_code, _o, _e = cli.run(["--config", str(config), "--root", str(root), "names", "add", "--real", "Zelda",
                                    "--to", "Wren", "--bogus", "--note", "please add Zelda Quill"])
        mcp_early = call("names_add", {"entries": [{"real": ["Zelda"], "to": "Wren"}], "bogus": 1,
                                       "request": "please add Zelda Quill"}, 6)
        agent_log.flush()
        early_log = log.read_text(encoding="utf-8") if log.exists() else ""
        check("399: a request refused before the project opens is logged withheld, never its words (re-review 3)",
              bad_code != 0 and mcp_early.get("isError") and "Zelda" not in early_log and "Quill" not in early_log
              and agent_log.WITHHELD in early_log, early_log[-500:])
        mcp_jo = call("names_add", {"entries": [{"real": ["Jo", "Jane"], "to": "[x]", "for": "Nobody"}],
                                    "request": "add jo and JANE"}, 5)
        agent_log.flush()
        newest = (json.loads(log.read_text(encoding="utf-8")) if log.exists() else {})
        entries_ = newest.get("entries", newest) if isinstance(newest, dict) else newest
        said_req = " ".join(str(e.get("request", "")) for e in entries_ if isinstance(e, dict))
        import re as re_
        check("399: a names tool's refused request in the agent log keeps none of its words, short names and any case "
              "among them (review 2, namesfix L5)",
              mcp_jo.get("isError") and not re_.search(r"(?i)\b(jo|jane)\b", said_req) and "add jo" not in said_req.lower()
              and "…" in said_req, said_req)
        mcp_add = call("names_add", {"entries": [{"real": ["Terry Hollis"], "to": "[neighbour]", "review": True}],
                                     "request": "Add Terry Hollis to review"}, 4)
        last = agent_changes.read(root)[-1]
        check("399: MCP's names_add writes through the same op, one line in the record, no name in it",
              not mcp_add.get("isError") and len(agent_changes.read(root)) == count + 1 and last["op"] == "names add"
              and "Hollis" not in json.dumps(last) and len(routes.pseudo_list(root)) == 4,
              json.dumps(mcp_add)[:300])

        # ── 6. namesfix: an empty MCP add, an entry for one participant never covering one for everyone, the answer's
        # numbers the list's as saved, an except phrase holding a comma, and the names read wherever the list is
        n_record = len(agent_changes.read(root))
        mcp_empty = call("names_add", {"entries": [], "request": "add Quentin Marsh as her brother"}, 7)
        agent_log.flush()
        empty_log = log.read_text(encoding="utf-8") if log.exists() else ""
        check("399: MCP's names_add with no entries is refused, nothing written, and the log keeps no word of the "
              "request (namesfix L5)",
              mcp_empty.get("isError") and "Quentin" not in empty_log and "Marsh" not in empty_log
              and len(agent_changes.read(root)) == n_record and len(routes.pseudo_list(root)) == 4, empty_log[-400:])
        # the demo's dog is in one participant's transcript alone; the list has him for another participant only
        routes.api_names({"op": "set", "root": rid, "entries": [{"real": ["Pepper"], "to": "[dog]", "for": "Juno"}]})
        juno_only = listed.read_bytes()
        code, h1, err, out = run("names", "add", "--real", "Pepper", "--to", "[dog]", "--note", "Add the dog for everyone",
                                 "--run", "h1")
        saved = routes.pseudo_list(root)
        checked = routes.api_names({"op": "check", "root": rid, "tool": "Claude Code"})
        flagged = {p["participant"] for e in checked["names"]["by_entry"] if e["entry"] == 2 for p in e["in"]}
        check("399: an agent's add of a name for everyone is written when the list has it for one participant alone, "
              "and the others' finds are flagged by it (namesfix H1)",
              code == 0 and h1["added"] == 1 and h1["count"] == 2 and h1["entries"][0]["entry"] == 2
              and listed.read_bytes() != juno_only and len(saved) == 2 and saved[1]["for"] is None
              and "Mabel" in flagged and agent_changes.read(root)[-1]["op"] == "names add" and not leaked(out),
              err + json.dumps(h1)[:300] + json.dumps(checked)[:300])
        # the dog as the list now holds him, the same rules, so the list covers him (namesfix2)
        spec2 = base / "names2.json"
        spec2.write_text(json.dumps([dict(e, **({"except": []} if e["to"] == "[dog]" else {}))
                                     for e in json.loads(spec.read_text(encoding="utf-8"))]), encoding="utf-8")
        code, mixed, err, out = run("names", "add", "--from", str(spec2), "--note", "Add them again", "--run", "m2")
        saved = routes.pseudo_list(root)
        nums = {e["to"]: e.get("entry") for e in mixed.get("entries", [])}
        check("399: an add of one listed name and new ones answers the numbers and the count the list is saved with "
              "(namesfix M2)",
              code == 0 and mixed["count"] == len(saved) == 4 and mixed["added"] == 2 and nums.get("[dog]") is None
              and saved[nums["[husband]"] - 1]["real"] == ["Dennis"] and saved[nums["[neighbour]"] - 1]["real"] == ["Terry"],
              err + json.dumps(mixed)[:400])
        routes.api_names({"op": "set", "root": rid, "entries": [
            {"real": ["Potter"], "to": "[x]", "except": ["Potter, Harry", "Potter and the stone"]},
            {"real": ["Quill"], "to": "[y]", "except": "Potter, Harry; the quill pen"}]})
        saved = routes.pseudo_list(root)
        check("399: an except phrase may hold a comma: a list is kept as given, a string split at semicolons (namesfix L2)",
              saved[0]["except"] == ["Potter, Harry", "Potter and the stone"]
              and saved[1]["except"] == ["Potter, Harry", "the quill pen"], json.dumps(saved))
        old_dir = base / "old-names"
        old_dir.mkdir(exist_ok=True)
        key = "0123456789abcdef0123456789abcdef"
        (old_dir / f"{key}.json").write_text(json.dumps({"entries": [{"real": ["Ottoline"], "to": "[aunt]"}]}),
                                             encoding="utf-8")
        elsewhere = base / "Older project"
        elsewhere.mkdir(exist_ok=True)
        (elsewhere / server_mod.PROJECT_FILE).write_text(json.dumps({"name": "Older", names_mod.KEY_FIELD: key}),
                                                         encoding="utf-8")
        held_override = names_mod.OVERRIDE
        names_mod.OVERRIDE = old_dir
        try:
            words = agent_changes.secret_words(elsewhere)
        finally:
            names_mod.OVERRIDE = held_override
        check("399: the words taken out of a request are the list's wherever it is read from, nothing moved (namesfix)",
              words == ["Ottoline"] and (old_dir / f"{key}.json").is_file() and not (elsewhere / names_mod.FILE).exists(),
              str(words))
        # namesfix2: an earlier entry covers a new one only when Match case and Except in agree too
        routes.api_names({"op": "set", "root": rid, "entries": [{"real": ["Pepper"], "to": "[dog]"}]})
        code, differ, err, _ = run("names", "add", "--from", str(spec), "--note", "x", "--run", "rules")
        saved = routes.pseudo_list(root)
        nums = {e["to"]: e.get("entry") for e in differ.get("entries", [])}
        code2, same, err2, _ = run("names", "add", "--real", "PEPPER", "--to", "[dog]", "--note", "x", "--dry-run")
        check("399: a listed name with other Except in phrases is written as a new entry, one with the same rules is "
              "listed (namesfix2)",
              code == 0 and nums.get("[dog]") == 4 and saved[3].get("except") == [EXCEPT] and len(saved) == 4
              and code2 == 0 and same["entries"][0].get("listed") is True and same["added"] == 0, err + err2)
        app_case = routes.api_names({"op": "add", "root": rid, "dry_run": True,
                                     "entries": [{"real": ["Pepper"], "to": "[dog]", "case": True}]})
        check("399: the app's add of a listed name with Match case set where the list's is not is no repeat (namesfix2)",
              app_case["added"] == 1, json.dumps(app_case)[:200])
        # namesfix2: the key file keeps Review each and Except in, a phrase with a comma among them
        kept_list = [{"real": ["Terry", "T."], "to": "[neighbour]", "for": None, "case": False, "review": True},
                     {"real": ["Potter"], "to": "[x]", "for": None, "case": False, "except": ["Potter, Harry", "the stone"]},
                     {"real": ["Dot"], "to": "[friend]", "for": None, "case": False}]
        back = names_mod.read_key("key.csv", names_mod.write_key(kept_list).encode("utf-8"))
        old_key = names_mod.read_key("key.csv", "Real name,Pseudonym\nDot,[friend]\n".encode("utf-8"))
        check("399: the key file keeps Review each and Except in, and a two-column key reads as before (namesfix2)",
              [(e["real"], e["to"], e.get("review", False), e.get("except")) for e in back]
              == [(["Terry", "T."], "[neighbour]", True, None), (["Potter"], "[x]", False, ["Potter, Harry", "the stone"]),
                  (["Dot"], "[friend]", False, None)]
              and old_key == [{"real": ["Dot"], "to": "[friend]", "for": None, "case": False}], json.dumps(back))
    finally:
        (server_mod.CONFIG_PATH, server_mod.ROOT_OVERRIDE, server_mod.STATE_PATH, server_mod.STATE_MEMORY,
         agent_changes.ALL_OPS, place) = kept
        if place is None:
            os.environ.pop(agent_log.PLACE, None)
        else:
            os.environ[agent_log.PLACE] = place
