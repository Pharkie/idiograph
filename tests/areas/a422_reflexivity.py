"""Area 422: Reflexivity, a project's own setting (settingsbuild, 17 November 2026, Adam: "reflexivity is a project
setting... it's more a write-up thing").

One text in Project settings, the researcher's reflexivity statement, kept in the project file as `reflexivity` while
it holds words, printed by no export (reflexout, Adam, 17 November 2026: "It's just there if you want to paste it somewhere
else"): not the tables' print view, Word document or PDF. Agents read it with `project show` (MCP's project_show), its words marked as
data, and set it with `project set --reflexivity` or `--reflexivity-file` (MCP's project_set), through the route the
page uses, /api/project. The reflexive thematic analysis demo's statement is its project's Reflexivity, where it was
the Themes board's note.

What is checked, on a scratch copy of that demo made a project of its own: it reads the demo's statement; the print
view, the Word document and the PDF print none of the statement and no Reflexivity section; a dry run writes
nothing and makes no record line; a real set is one line in the record of agents' changes, saying a count of words and
never the words, and undoing its run puts the project file back byte for byte; taken away, the key leaves the file and
no export holds the section; MCP's dry run writes nothing and its set is read back by project_show, marked
untrusted_text; and a text too long, a file that cannot be read and both options together are refused with nothing
written. After settingsfix: a save of the name and question with a statement too long writes neither; the line
says "1 word" in the catalogue's forms; a whole send and a chosen send leave the sender's Reflexivity out, the copy
opened has none and a copy coming back leaves his project file byte for byte; and Reset demo puts a demo's project
file back as it ships, its Reflexivity with it, where the demo worked on is not the shipped folder. The demo's own is fixed as every Project settings field of a demo is (api_project), not checked here since
a run against the repo's demo would fill it."""
from __future__ import annotations

import hashlib
import json
import shutil
import zipfile
from pathlib import Path

from . import support
from .support import check

ASKED = "His reflexivity statement, as he wrote it"
NEW = ("I came to this study as a remote worker myself.\nI kept a note after each interview.")


def files(root: Path) -> dict:
    """Every file of the project by its contents, the locks, the record of agents' changes and its store, the
    project's History and archive copies set aside."""
    import agent_changes
    out = {}
    for p in sorted(root.rglob("*")):
        rel = p.relative_to(root).as_posix()
        if (not p.is_file() or p.name.endswith(".lock") or p.suffix in (".docx", ".pdf") or rel == agent_changes.FILE
                or rel.startswith(agent_changes.STORE) or "_Archive/" in rel or rel in agent_changes.NEVER):
            continue
        out[rel] = hashlib.sha256(p.read_bytes()).hexdigest()
    return out


def test_reflexivity(scratch: Path):
    print("\n422. Reflexivity, a project's own setting, in the tables' exports and for agents (settingsbuild)")
    import agent_changes
    import agent_log
    import cli
    import idiograph_routes as routes
    import mcp_server
    import os
    import pdftext
    import server as server_mod

    base = scratch / "reflexivity-422"
    shutil.rmtree(base, ignore_errors=True)
    root = base / "Working from home"
    root.mkdir(parents=True)
    rta = support.source("demo/rta")
    held = json.loads((rta / server_mod.PROJECT_FILE).read_text(encoding="utf-8"))
    statement = str(held.get("reflexivity") or "")
    held["agents"] = {"allowed": True, "at": "2026-11-17T09:00:00+00:00"}
    (root / server_mod.PROJECT_FILE).write_text(json.dumps(held), encoding="utf-8")
    for who in ("Kemi", "Toby", "Ros", "Glen", "Dev", "Ffion"):
        (root / who / "Working").mkdir(parents=True)
        shutil.copy2(rta / "pristine" / f"{who} - EN & ES.xlsx", root / who / f"{who} - EN & ES.xlsx")
        for one in sorted((rta / "pristine" / "Working").glob(f"{who} - EN & ES.*")):
            shutil.copy2(one, root / who / "Working" / one.name)
    for one in ("idiograph-gets.json", "idiograph-codes.json"):
        shutil.copy2(rta / "pristine" / one, root / one)
    config_file = base / "config.json"
    config_file.write_text(json.dumps({"projects": [{"root": str(root)}], "interviewer": "Leah", "corpus": "",
                                       "gravity_reference": "", "corpus_exclude": []}), encoding="utf-8")
    log = base / "agent-log.json"
    kept = (agent_changes.ALL_OPS, os.environ.get(agent_log.PLACE), server_mod.CONFIG_PATH)
    agent_changes.ALL_OPS = None
    os.environ[agent_log.PLACE] = str(log)

    def run(*args, tool="Claude Code"):
        given = ["--config", str(config_file), "--root", str(root), "--json", *args]
        if tool is not None:
            given += ["--tool", tool]
        return cli.run(given)

    def exports(tag: str) -> dict:
        """The table's print view, Word document and PDF, each as text, the participants table ticked."""
        out = {}
        server_mod.CONFIG_PATH = config_file
        try:
            code, html = routes.gets_print_page({"root": str(root), "auto": "0", "participants": "1"})
            out["html"] = html.split("<main>", 1)[-1] if code == 200 else ""
        finally:
            server_mod.CONFIG_PATH = kept[2]
        code, said, err = run("gets", "export", "--participants", "--word", tool=None)
        if code == 0:
            made = Path(support.plain(json.loads(said))["path"])
            with zipfile.ZipFile(made) as z:
                out["word"] = z.read("word/document.xml").decode("utf-8")
            made.unlink()
        code, said, err = run("gets", "export", "--participants", "--out", str(base / f"{tag}.pdf"), "--replace",
                              tool=None)
        if code == 0:
            out["pdf"] = " ".join(pdftext.pages_text((base / f"{tag}.pdf").read_bytes()))
        else:
            out["pdf_said"] = err
        return out

    try:
        check("422: the reflexive thematic analysis demo's statement is its project's Reflexivity, read with the project",
              statement.startswith("I am ") and routes.read_project(root)["reflexivity"] == statement, statement[:80])
        start = files(root)

        # ── the exports print none of it (reflexout)
        first = statement.split(".")[0]
        got = exports("with")
        def prints_none(text: str) -> bool:
            """Whether the export holds neither the statement's words nor a Reflexivity heading."""
            flat = support.squashed(text)
            return bool(text) and support.squashed(first) not in flat and support.squashed("Reflexivity") not in flat
        check("422: with a statement, the print view prints none of it and no Reflexivity section (reflexout)",
              prints_none(got.get("html", "")) and 'id="reflexivity"' not in got.get("html", "")
              and "Participants" in got.get("html", ""), got.get("html", "")[:200])
        check("422: with a statement, Word's document prints none of it", prints_none(got.get("word", "")),
              got.get("word", "")[:200])
        if "pdf" in got:
            check("422: with a statement, the PDF prints none of it", prints_none(got["pdf"]), got["pdf"][:300])
        else:
            print(f"  (the PDF skipped: {got.get('pdf_said', '')[:120]})")
        check("422: an export writes nothing of the project's", files(root) == start, "")

        # ── an agent's set: the dry run writes nothing, the set is one record line, undone byte for byte
        code, out, err = run("project", "set", "--reflexivity", NEW, "--dry-run")
        answer = support.plain(json.loads(out)) if code == 0 and out.strip() else {}
        check("422: the dry run says the change by its words' count and writes nothing, no record line",
              code == 0 and answer.get("dry_run") is True and answer.get("changes") == [
                  f"Reflexivity changed, from {routes.reflexivity_words(statement)} words to {routes.reflexivity_words(NEW)} words."]
              and files(root) == start and not agent_changes.read(root) and "remote worker" not in out,
              (err or "")[:300] + out[:300])
        text_file = base / "reflexivity.txt"
        text_file.write_text(NEW, encoding="utf-8")
        code, out, err = run("project", "set", "--reflexivity-file", str(text_file), "--note", ASKED)
        lines = agent_changes.read(root)
        check("422: the set is saved in the project file, one record line naming no words of it",
              code == 0 and json.loads((root / server_mod.PROJECT_FILE).read_text(encoding="utf-8")).get("reflexivity") == NEW
              and len(lines) == 1 and lines[0].get("op") == "project set" and "remote worker" not in json.dumps(lines)
              and "remote worker" not in out, (err or "")[:300] + json.dumps(lines)[:300])
        code, out, err = run("project", "show", tool=None)
        shown = json.loads(out) if code == 0 and out.strip() else {}
        check("422: project show reads it back, its words marked untrusted_text",
              shown.get("project", {}).get("reflexivity") == {"untrusted_text": NEW}, out[:300])
        if lines:
            code, out, err = run("agents", "undo-run", lines[0]["run"], "--note", "Put it back")
            check("422: undoing the set's run puts every file back byte for byte", code == 0 and files(root) == start,
                  (err or "")[:300] + out[:200])

        # ── taken away: the key leaves the file and no export holds the section
        code, out, err = run("project", "set", "--reflexivity", "", "--note", ASKED)
        held_now = json.loads((root / server_mod.PROJECT_FILE).read_text(encoding="utf-8"))
        answer = support.plain(json.loads(out)) if code == 0 and out.strip() else {}
        check("422: an empty statement takes the key out of the project file, every other key kept",
              code == 0 and "reflexivity" not in held_now and held_now.get("name") == held["name"]
              and answer.get("changes") == ["Reflexivity taken away."], (err or "")[:300] + out[:300])
        got = exports("without")
        check("422: with none, no export holds a Reflexivity section, the participants table still there",
              'id="reflexivity"' not in got.get("html", "x") and "Participants" in got.get("html", "")
              and "Reflexivity" not in got.get("word", "Reflexivity")
              and ("pdf" not in got or "Reflexivity" not in got["pdf"]),
              got.get("word", "")[:200])
        emptied = files(root)

        # ── MCP's project_set: the dry run writes nothing, the set is read back by project_show
        mcp = mcp_server.Server(str(root), config=str(config_file))
        mcp.receive(json.dumps({"jsonrpc": "2.0", "id": 1, "method": "initialize",
                                "params": {"protocolVersion": "2025-06-18", "clientInfo": {"name": "claude-code"}}}))

        def call(n, name, arguments):
            return mcp.receive(json.dumps({"jsonrpc": "2.0", "id": n, "method": "tools/call",
                                           "params": {"name": name, "arguments": arguments}}))["result"]

        res = call(2, "project_set", {"reflexivity": NEW, "dry_run": True, "request": ASKED})
        check("422: MCP's project_set in a dry run writes nothing", not res["isError"] and files(root) == emptied,
              json.dumps(res)[:300])
        res = call(3, "project_set", {"reflexivity": NEW, "request": ASKED})
        shown = call(4, "project_show", {})
        check("422: MCP's project_set saves it and project_show reads it back marked untrusted_text",
              not res["isError"] and not shown["isError"]
              and shown["structuredContent"]["project"]["reflexivity"] == {"untrusted_text": NEW}
              and "<untrusted_text>" in shown["content"][0]["text"], json.dumps(shown)[:400])
        set_once = files(root)

        # ── refusals, nothing written
        code, out, err = run("project", "set", "--reflexivity", "x" * (routes.REFLEXIVITY_MOST + 1), "--note", ASKED)
        refused_long = code != 0 and files(root) == set_once
        code, out, err = run("project", "set", "--reflexivity-file", str(base / "none.txt"), "--note", ASKED)
        refused_file = code != 0 and files(root) == set_once
        code, out, err = run("project", "set", "--reflexivity", "a", "--reflexivity-file", str(text_file), "--note", ASKED)
        refused_both = code != 0 and files(root) == set_once
        check("422: a statement too long, a file that cannot be read and both options together are each refused, "
              "nothing written", refused_long and refused_file and refused_both,
              str((refused_long, refused_file, refused_both)))

        # ── settingsfix: the page's save of a name with a statement too long writes neither
        def as_page(fn, *args, **kw):
            server_mod.CONFIG_PATH, server_mod.STATE_MEMORY = config_file, {"recent": []}
            try:
                return fn(*args, **kw)
            finally:
                server_mod.CONFIG_PATH, server_mod.STATE_MEMORY = kept[2], kept_memory

        kept_memory = server_mod.STATE_MEMORY
        try:
            as_page(routes.api_project, {"root": str(root), "name": "Another name", "research_question": "Another?",
                                         "reflexivity": "x" * (routes.REFLEXIVITY_MOST + 1)})
            refused = False
        except routes.WorkbookError:
            refused = True
        check("422: a save of the name and question with a statement too long is refused whole, nothing written",
              refused and files(root) == set_once, str(refused))

        # ── settingsfix: the History's and the record's line counts one word as one word
        check("422: the change's line says 1 word and 2 words in the catalogue's forms",
              routes.reflexivity_changes("", "Alone") == ["Reflexivity written, 1 word."]
              and routes.reflexivity_changes("Alone", "Two words") == ["Reflexivity changed, from 1 word to 2 words."],
              str(routes.reflexivity_changes("", "Alone")))

        # ── settingsfix: a shared copy leaves the sender's Reflexivity out, and a copy coming back never touches his
        import project_pack as pack_mod

        def sent_project(file: Path) -> dict:
            with zipfile.ZipFile(file) as z:
                return json.loads(z.read(pack_mod.TOP + server_mod.PROJECT_FILE).decode("utf-8"))

        whole = base / "whole.idiograph"
        as_page(routes.send_project, root, whole)
        chosen = base / "chosen.idiograph"
        as_page(routes.send_project, root, chosen, participants=["Kemi"], leave_out=["gets"])
        own = json.loads((root / server_mod.PROJECT_FILE).read_text(encoding="utf-8"))
        got_whole, got_chosen = sent_project(whole), sent_project(chosen)
        check("422: a whole send and a chosen send leave the sender's Reflexivity out, every other key kept, his own "
              "file keeping it",
              "reflexivity" not in got_whole and "reflexivity" not in got_chosen and own.get("reflexivity") == NEW
              and got_whole.get("name") == own.get("name") and got_whole.get("demographics") == own.get("demographics")
              and got_chosen.get("research_question") == own.get("research_question"),
              json.dumps(sorted(got_whole))[:300])
        into = base / "copies"
        into.mkdir()
        opened = as_page(routes.open_copy, whole, into, from_name="Curt")
        copy_root = Path(opened.get("project", {}).get("root") or opened.get("folder") or "")
        copy_project = json.loads((copy_root / server_mod.PROJECT_FILE).read_text(encoding="utf-8"))
        check("422: the copy opened has no Reflexivity of the sender's", copy_root.is_dir()
              and "reflexivity" not in copy_project, json.dumps(sorted(copy_project))[:300])
        # the copy's own statement, its analyst's, and the copy sent back
        as_page(routes.api_project, {"root": str(copy_root), "reflexivity": "The second analyst's own statement."})
        back = base / "back.idiograph"
        as_page(routes.send_project, copy_root, back)
        before_back = (root / server_mod.PROJECT_FILE).read_bytes()
        try:
            as_page(routes.boards_in, root, back, from_name="Curt", request=ASKED)
        except routes.WorkbookError as exc:
            print(f"  (boards in said: {str(exc)[:120]})")
        check("422: a copy coming back carries no Reflexivity and leaves his project file byte for byte",
              "reflexivity" not in sent_project(back)
              and (root / server_mod.PROJECT_FILE).read_bytes() == before_back, "")

        # ── settingsfix: Reset demo puts the demo's project file back as it ships, its Reflexivity with it, where
        # the demo worked on is not the shipped one (the Mac app's)
        import make_demo
        shipped = base / "shipped-rta"
        shutil.copytree(rta, shipped, ignore=shutil.ignore_patterns("*.m4a", "source"))
        live = base / "live-rta"
        make_demo.fill(shipped / "pristine", live)
        older = json.loads((shipped / server_mod.PROJECT_FILE).read_text(encoding="utf-8"))
        older.pop("reflexivity", None)
        (live / server_mod.PROJECT_FILE).write_text(json.dumps(older), encoding="utf-8")
        make_demo.reset_all(shipped / "pristine", live)
        check("422: Reset demo puts the demo's project file back as it ships, its statement in Reflexivity",
              (live / server_mod.PROJECT_FILE).read_bytes() == (shipped / server_mod.PROJECT_FILE).read_bytes()
              and routes.read_project(live)["reflexivity"] == statement, "")
        repo_like = (shipped / server_mod.PROJECT_FILE).read_bytes()
        make_demo.reset_all(shipped / "pristine", shipped)
        check("422: Reset demo where the demo is the shipped folder leaves its project file as it is",
              (shipped / server_mod.PROJECT_FILE).read_bytes() == repo_like, "")
    finally:
        agent_changes.ALL_OPS = kept[0]
        if kept[1] is None:
            os.environ.pop(agent_log.PLACE, None)
        else:
            os.environ[agent_log.PLACE] = kept[1]
        server_mod.CONFIG_PATH = kept[2]
