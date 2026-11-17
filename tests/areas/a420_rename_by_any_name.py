"""Area 420: an agent's participant rename finds the participant by any name the command line accepts (renamefix,
17 November 2026, Adam's rule that agents can do everything the app can).

A participant's folder renamed outside the app to `P<n> - <pseudonym>-<second name>`, as Adam's real projects name
them, kept its themes file naming the participant by the pseudonym alone, so `participant rename` (the command line
and MCP's participant_rename alike) asked the route for a folder by that name, which none had, and was refused "not in
this project now". It now finds the participant as every other participant command does (`Project.case`, which also
takes the folder's label as the app shows it), and hands the route that label.

What is checked, on a scratch copy of the longitudinal demo with Arlo's folder renamed so: the dry run, by the
pseudonym and by the folder's label, names the change and writes nothing; MCP's participant_rename does the same; the
real rename is one line in the record of agents' changes, and undoing its run puts every file back byte for byte; an
unknown name is refused with nothing written; and the folder's second name is in no answer, refusal or record line.

renamefix2, after the review: a folder whose label's pseudonym is not the participant's (a second name the folder
pattern does not strip, or another pseudonym given outside the app) is refused, dry run alike, nothing written and the
second name in no answer, record line or History; a workbook at the project's root is not found by the root's name."""
from __future__ import annotations

import hashlib
import json
import shutil
from pathlib import Path

from .support import check
from . import support

# the folder's second name, which no answer may carry
SECOND = "Smithson"
# a second name the folder pattern does not strip, so the label would carry it (renamefix2)
ODD = "McDonald"
ASKED = "He chose a new pseudonym"


def digest(root: Path) -> dict:
    """Every file of the project by its contents, the locks, the record of agents' changes with its restore points and
    the copies a rename keeps in `_Archive/` first (the app's backup convention, kept by an undo too) and the project's
    History, a log the record never restores (`agent_changes.NEVER`), set aside."""
    import agent_changes
    out = {}
    for p in sorted(root.rglob("*")):
        rel = p.relative_to(root).as_posix()
        if (not p.is_file() or p.name.endswith(".lock") or rel == agent_changes.FILE
                or rel.startswith(agent_changes.STORE) or "_Archive/" in rel or rel in agent_changes.NEVER):
            continue
        out[rel] = hashlib.sha256(p.read_bytes()).hexdigest()
    return out


def test_rename_by_any_name(scratch: Path):
    print("\n420. An agent's participant rename by any name the command line takes, the folder renamed outside the app "
          "(renamefix, 17 November)")
    import agent_changes
    import agent_log
    import cli
    import mcp_server
    import os
    import server as server_mod

    base = scratch / "rename-420"
    shutil.rmtree(base, ignore_errors=True)
    root = base / "Allotment"
    root.mkdir(parents=True)
    lipa = support.source("demo/lipa")
    held = json.loads((lipa / server_mod.PROJECT_FILE).read_text(encoding="utf-8"))
    held["agents"] = {"allowed": True, "at": "2026-11-17T09:00:00+00:00"}
    (root / server_mod.PROJECT_FILE).write_text(json.dumps(held), encoding="utf-8")
    folders = {"Arlo": f"P1 - Arlo-{SECOND}", "Hollis": "Hollis", "Nell": "Nell"}
    for who, name in folders.items():
        (root / name / "Working").mkdir(parents=True)
        shutil.copy2(lipa / "pristine" / f"{who} - EN & ES.xlsx", root / name / f"{who} - EN & ES.xlsx")
        for one in sorted((lipa / "pristine" / "Working").glob(f"{who} - EN & ES.*")):
            shutil.copy2(one, root / name / "Working" / one.name)
    for one in ("idiograph-lgets.json", "idiograph-trajectories.json"):
        shutil.copy2(lipa / "pristine" / one, root / one)
    config_file = base / "config.json"
    config_file.write_text(json.dumps({"projects": [{"root": str(root)}], "interviewer": "Adam", "corpus": "",
                                       "gravity_reference": "", "corpus_exclude": []}), encoding="utf-8")
    log = base / "agent-log.json"
    kept = (agent_changes.ALL_OPS, os.environ.get(agent_log.PLACE))
    agent_changes.ALL_OPS = None
    os.environ[agent_log.PLACE] = str(log)

    def run(*args, tool="Claude Code"):
        given = ["--config", str(config_file), "--root", str(root), "--json", *args]
        if tool is not None:
            given += ["--tool", tool]
        code, out, err = cli.run(given)
        return code, out, err

    def said(*texts) -> bool:
        """Whether the folder's second name is in none of the texts."""
        return not any(SECOND in str(t) for t in texts)

    try:
        start = digest(root)

        # the dry run by the pseudonym the themes file names, and by the folder's label as the app shows it
        for name in ("Arlo", "P1 - Arlo"):
            code, out, err = run("participant", "rename", name, "Ansel", "--dry-run")
            answer = support.plain(json.loads(out)) if code == 0 and out.strip() else {}
            check(f"420: the dry run by {name!r} names the change, writes nothing and never the folder's second name",
                  code == 0 and answer.get("dry_run") is True and answer.get("new") == "Ansel" and answer.get("changes")
                  and digest(root) == start and not agent_changes.read(root) and said(out, err),
                  (err or "")[:300] + out[:300])

        # MCP's participant_rename, the same command
        mcp = mcp_server.Server(str(root), config=str(config_file))
        mcp.receive(json.dumps({"jsonrpc": "2.0", "id": 1, "method": "initialize",
                                "params": {"protocolVersion": "2025-06-18", "clientInfo": {"name": "claude-code"}}}))
        res = mcp.receive(json.dumps({"jsonrpc": "2.0", "id": 2, "method": "tools/call", "params": {
            "name": "participant_rename", "arguments": {"case": "Arlo", "name": "Ansel", "folder": False,
                                                        "dry_run": True, "request": ASKED}}}))["result"]
        check("420: MCP's participant_rename in a dry run names the change and writes nothing",
              not res["isError"] and digest(root) == start and not agent_changes.read(root)
              and said(json.dumps(res)), json.dumps(res)[:400])

        # an unknown name, refused with nothing written
        code, out, err = run("participant", "rename", "Bramble", "Ansel", "--note", ASKED)
        check("420: an unknown name is refused, nothing written", code != 0 and digest(root) == start
              and not agent_changes.read(root) and said(out, err), (err or "")[:300])

        # the real rename, the folder kept: one record line, its run undone byte for byte
        code, out, err = run("participant", "rename", "Arlo", "Ansel", "--note", ASKED)
        answer = support.plain(json.loads(out)) if code == 0 and out.strip() else {}
        lines = agent_changes.read(root)
        check("420: the real rename by the pseudonym renames him, one record line, the folder's second name in neither",
              code == 0 and answer.get("new") == "Ansel" and len(lines) == 1
              and lines[0].get("op") == "participant rename" and digest(root) != start
              and (root / folders["Arlo"]).is_dir() and said(out, err, json.dumps(lines)),
              (err or "")[:300] + out[:300] + json.dumps(lines)[:300])
        code, out, err = run("cases", tool=None)
        check("420: the participant is Ansel now", code == 0 and "Ansel" in out and said(out), (err or "")[:200] + out[:300])
        if lines:
            code, out, err = run("agents", "undo-run", lines[0]["run"], "--note", "Put it back")
            check("420: undoing the rename's run puts every file back byte for byte, the second name in no answer",
                  code == 0 and digest(root) == start and said(out, err, json.dumps(agent_changes.read(root))),
                  (err or "")[:300] + out[:300] + str(sorted(set(digest(root).items()) ^ set(start.items())))[:600])

        # the folder ticked: the dry run says so and never the folder's second name
        code, out, err = run("participant", "rename", "P1", "Ansel", "--folder", "--dry-run")
        answer = support.plain(json.loads(out)) if code == 0 and out.strip() else {}
        check("420: the dry run by `P1` with the folder ticked names the folder's change, writes nothing and never the "
              "folder's second name", code == 0 and answer.get("folder_changes") and digest(root) == start
              and said(out, err), (err or "")[:300] + out[:300])

        # two folders the name finds: refused in one line, nothing written
        records = len(agent_changes.read(root))
        (root / "Hollis").rename(root / "P1 - Hollis")
        code, out, err = run("participant", "rename", "P1", "Ansel", "--note", ASKED)
        check("420: a name two folders' labels share is refused in one line, nothing written, no second name",
              code != 0 and len((json.loads(out) if out.strip() else {}).get("lines") or [0, 0]) == 1
              and len(agent_changes.read(root)) == records
              and said(out, err), f"{code} {err!r} {out[:300]}")
        (root / "P1 - Hollis").rename(root / "Hollis")

        # renamefix2: a folder whose label is not the participant's name, a second name the app does not strip or
        # another pseudonym given outside the app, is refused, dry run alike, nothing written, no second name said
        records = len(agent_changes.read(root))
        history = root / "idiograph-history.json"
        told = history.read_bytes() if history.is_file() else b""
        now = digest(root)
        for folder, asked, was in ((f"P1 - Arlo-{ODD}", "Arlo", folders["Arlo"]), ("P2 - Zed", "Hollis", "Hollis"),
                                   ("P2 - Zed", "P2", "Hollis")):
            (root / was).rename(root / folder)
            outs = []
            for extra in (["--dry-run"], ["--note", ASKED]):
                code, out, err = run("participant", "rename", asked, "Ansel", *extra)
                outs.append((code, out, err))
            (root / folder).rename(root / was)
            check(f"420: with the folder renamed outside the app to {folder.replace(ODD, 'its second name')}, "
                  f"renaming by {asked} is refused in one line, dry run alike, nothing written and the second name in "
                  "no answer, record line or History",
                  all(c != 0 and len((json.loads(o) if o.strip() else {}).get("lines") or [0, 0]) == 1
                      and not any(ODD in str(x) or SECOND in str(x) for x in (o, e)) for c, o, e in outs)
                  and digest(root) == now and len(agent_changes.read(root)) == records
                  and (history.read_bytes() if history.is_file() else b"") == told,
                  str([(c, o[:200], e[:100]) for c, o, e in outs]))

        # a workbook at the project's root is never found by the project folder's name
        loose = root / "Nell - EN & ES.xlsx"
        loose.write_bytes((root / "Nell" / "Nell - EN & ES.xlsx").read_bytes())
        shutil.copytree(root / "Nell" / "Working", root / "Working")
        code, out, err = run("participant", "rename", root.name, "Ansel", "--dry-run")
        code2, out2, err2 = run("board", "show", root.name, tool=None)
        check("420: a workbook at the project's root, its themes file naming its participant, is not found by the "
              "project folder's name", code != 0 and "no participant called" in out.lower() and code2 != 0
              and "no participant called" in out2.lower(), f"{code} {out[:300]} {code2} {out2[:300]}")
        loose.unlink()
        shutil.rmtree(root / "Working")
        check("420: nothing was written by the refusals", digest(root) == now, "")

        # the record and the agent log never carry the second name
        agent_log.flush()
        record = agent_changes.record_path(root)
        history = root / "idiograph-history.json"
        check("420: the record of agents' changes, the agent log and the project's History never name the folder's "
              "second name, the History keeping the rename",
              said(record.read_text(encoding="utf-8") if record.is_file() else "",
                   log.read_text(encoding="utf-8") if log.is_file() else "",
                   history.read_text(encoding="utf-8") if history.is_file() else "")
              and history.is_file() and "participant rename" in history.read_text(encoding="utf-8"), "")
    finally:
        agent_changes.ALL_OPS = kept[0]
        if kept[1] is None:
            os.environ.pop(agent_log.PLACE, None)
        else:
            os.environ[agent_log.PLACE] = kept[1]
        agent_log.flush()
