"""Area 357: the app makes its project on the relay (relaywire, 9 November 2026; Adam's ruling of 8 November about
17:00 to 19:10 by dialog: the relay at idiograph.app, him its operator, Adam and Curt only). The relay makes a project
only for an operator code and answers its own id. Before this build the team layer sent under team.json's own team
id, which the relay never made, so a lead's first send was refused. Now the lead's relay code makes the project once,
its id goes into the signed list of people, and the relay route maps the team's id to it.

The relay in relay/ runs on this computer through Miniflare on a free loopback port with a made-up operator code, as
area 342 runs it, and three scratch installs in one process drive it through the app's own route, its command line
and its MCP server, no loopback. What matters: a wrong code, no connection and an agent asking for the relay are each
refused with nothing written; the lead's code makes the project and is kept nowhere on disk; an invite, the six
digits and They match go through the relay, a team's own relay's address carried in the link; the member's computer
reaches the project once the lead has let it in; a version of a participant goes from owner to member and a board
from member to owner through team_sync's look; and a removed computer is refused by the relay. Skips where this
computer has no node, no Miniflare or no `cryptography`. Every fixture is invented, a study of keeping bees through
the winter."""
from __future__ import annotations

import hashlib
import io
import json
import re
import shutil
import subprocess
import sys
import threading
import time
from pathlib import Path

from . import support
from .support import check, skip

WRONG = "not-the-operator-code-at-all-0000"


def look_until(team_sync, root: Path, came, seconds: float = 10) -> dict:
    """The app's look, again every quarter second until `came(answer)` or `seconds` have passed, as the app's own
    looks come again: a relay under load may answer one late or not at all (teamflake, 9 November 2026). Answers the
    last look's answer with `tries`, how many it took."""
    deadline, tries = time.monotonic() + seconds, 0
    while True:
        got = team_sync.sync(root)
        tries += 1
        if came(got) or time.monotonic() > deadline:
            return dict(got, tries=tries)
        time.sleep(0.25)


def files_of(folder: Path) -> dict:
    """Every file under a folder with its SHA-256, so a check can say nothing was written, the project's empty lock
    file aside, which every write takes whether it writes or not."""
    return {str(p.relative_to(folder)): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in sorted(Path(folder).rglob("*")) if p.is_file() and p.name != ".idiograph.lock"}


def test_relay_project(scratch: Path):
    print("\n357. The app makes its project on the relay: the lead's relay code once, kept nowhere, the relay's id in "
          "the list of people, invite, pairing, versions and boards through it, a removed computer refused (relaywire)")
    try:
        import cryptography  # noqa: F401
    except ImportError:
        return skip("357: the project made on the relay", "no cryptography in this Python")
    held_code(scratch)
    from .a342_relay import CODE, free_port, miniflare_folder
    node = shutil.which("node")
    folder = miniflare_folder()
    if not node or not folder:
        return skip("357: the project made on the relay", "no node or no Miniflare on this machine")
    port = free_port()
    child = subprocess.Popen([node, str(support.source("relay/test/serve.mjs")), "--port", str(port), "--codes", CODE,
                              "--invite-limit", "1000", "--miniflare", str(folder)],
                             stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                             cwd=str(scratch), encoding="utf-8", errors="replace")
    said = []
    ready = threading.Event()

    def read():
        for line in child.stdout:
            said.append(line.rstrip())
            if line.startswith("ready "):
                ready.set()
    threading.Thread(target=read, daemon=True).start()
    try:
        if not ready.wait(60):
            return check("357: the relay starts on this computer", False, " | ".join(said[-10:]))
        drive(scratch, f"http://127.0.0.1:{port}/relay/v1")
    finally:
        try:
            child.stdin.close()
        except OSError:
            pass
        try:
            child.wait(timeout=10)
        except subprocess.TimeoutExpired:
            child.kill()
            child.wait(timeout=10)


def held_code(scratch: Path) -> None:
    """A relay code never waits in a hold (smokefix, 9 November 2026, the live relay test): with Dangerously skip
    permissions off, `team on` and `team set` with --code-stdin are refused in a line, the standard input left unread
    and nothing written, no hold kept, where before the hold's dry run read the code and threw it away and his Approve
    turned on with none. With the setting on, the op runs as before, here to a relay out of reach. No relay needed."""
    import cli
    import holds
    import server as server_mod
    import team
    from .a342_relay import CODE, free_port
    from .a351_team_board import make_workbook

    base = scratch / "team-357-held"
    shutil.rmtree(base, ignore_errors=True)
    root = base / "ada" / "Winter bees"
    root.mkdir(parents=True)
    (root / server_mod.PROJECT_FILE).write_text(json.dumps({
        "name": "Winter bees", "research_question": "How do beekeepers live the winter with their hives?",
        "agents": {"allowed": True, "at": "2026-11-09T09:00:00+00:00"}}), encoding="utf-8")
    make_workbook(root, "P1 - Marlow", "Marlow")
    cfg = base / "ada" / "config.json"
    closed = f"http://127.0.0.1:{free_port()}/relay/v1"
    kept = (server_mod.CONFIG_PATH, server_mod.ROOT_OVERRIDE, team.DEVICE_PATH, holds.RUN_AT_ONCE)

    def settings(skip_on: bool) -> None:
        cfg.write_text(json.dumps({"projects": [{"root": str(root)}], "interviewer": "Interviewer", "your_name": "Ada",
                                   "corpus": "", "gravity_reference": "", "corpus_exclude": [],
                                   "skip_permissions": skip_on}), encoding="utf-8")

    def run(*args) -> tuple:
        server_mod.CONFIG_PATH, server_mod.ROOT_OVERRIDE, team.DEVICE_PATH = cfg, None, None
        was, given = sys.stdin, io.StringIO(CODE + "\n")
        sys.stdin = given
        try:
            code, out, err = cli.run(["--config", str(cfg), "--root", str(root), "--json", *args,
                                      "--note", "Put it on the relay", "--tool", "Claude Code"])
        finally:
            sys.stdin = was
        got = json.loads(out) if out.strip() else {}
        return code, err + (got.get("error", "") if code else ""), given.read()

    try:
        holds.RUN_AT_ONCE = None
        settings(False)
        before = files_of(base)
        on = run("team", "on", "--route", "relay", "--relay-url", closed, "--name", "Ada", "--code-stdin")
        put = run("team", "set", "--code-stdin")
        line = "A relay code is typed in Project settings, or run this with Dangerously skip permissions on."
        check("357: with Dangerously skip permissions off, team on and team set with a relay code are refused in a "
              "line, not held: the code left unread on the standard input, no hold kept and nothing written",
              on[0] != 0 and put[0] != 0 and line in on[1] and line in put[1] and on[2] == put[2] == CODE + "\n"
              and not (root / holds.FILE).exists() and files_of(base) == before, f"{on} | {put}")
        settings(True)
        before = files_of(base)
        ran = run("team", "on", "--route", "relay", "--relay-url", closed, "--name", "Ada", "--code-stdin")
        check("357: with the setting on, team on with the code runs as before, reading it, here refused by a relay out "
              "of reach with nothing written",
              ran[0] != 0 and line not in ran[1] and "relay could not be reached" in ran[1] and ran[2] == ""
              and files_of(base) == before, str(ran))
    finally:
        server_mod.CONFIG_PATH, server_mod.ROOT_OVERRIDE, team.DEVICE_PATH, holds.RUN_AT_ONCE = kept


def drive(scratch: Path, url: str):
    import cli
    import idiograph_routes as routes
    import mcp_server
    import project_history as hist_mod
    import server as server_mod
    import team
    import team_sync
    import themes
    import transport
    import workbook as wb_mod
    from workbook import WorkbookError
    from .a342_relay import CODE, free_port
    from .a351_team_board import make_workbook, set_statements

    base = scratch / "team-357"
    shutil.rmtree(base, ignore_errors=True)
    lead_root = base / "ada" / "Winter bees"
    lead_root.mkdir(parents=True)
    (lead_root / server_mod.PROJECT_FILE).write_text(json.dumps({
        "name": "Winter bees", "research_question": "How do beekeepers live the winter with their hives?",
        "agents": {"allowed": True, "at": "2026-11-09T09:00:00+00:00"}}), encoding="utf-8")
    lead_book = make_workbook(lead_root, "P1 - Marlow", "Marlow")
    member_root = base / "bo" / "Winter bees"
    shutil.copytree(lead_root, member_root)
    solo_root = base / "cy" / "Winter bees"
    shutil.copytree(lead_root, solo_root)

    def settings(who: str, root: Path) -> Path:
        cfg = base / who / "config.json"
        cfg.write_text(json.dumps({"projects": [{"root": str(root)}], "interviewer": "Interviewer",
                                   "your_name": who.title(), "corpus": "", "gravity_reference": "",
                                   "corpus_exclude": []}), encoding="utf-8")
        return cfg

    lead = {"root": lead_root, "config": settings("ada", lead_root), "book": lead_book, "home": base / "ada"}
    member = {"root": member_root, "config": settings("bo", member_root), "home": base / "bo",
              "book": member_root / "P1 - Marlow" / lead_book.name}
    solo = {"root": solo_root, "config": settings("cy", solo_root), "home": base / "cy"}
    kept = (server_mod.CONFIG_PATH, server_mod.ROOT_OVERRIDE, team.DEVICE_PATH, transport.OVERRIDE)
    transport.OVERRIDE = None

    def at(who):
        server_mod.CONFIG_PATH = who["config"]
        server_mod.ROOT_OVERRIDE = None
        team.DEVICE_PATH = None

    def wt(who, **body):
        at(who)
        return routes.api_team(dict(body, root=str(who["root"])))

    def refused(fn) -> str:
        try:
            fn()
            return ""
        except WorkbookError as exc:
            return str(exc)

    def run(who, *args, stdin: str = ""):
        at(who)
        was = sys.stdin
        sys.stdin = io.StringIO(stdin)
        try:
            code, out, err = cli.run(["--config", str(who["config"]), "--root", str(who["root"]), "--json", *args])
        finally:
            sys.stdin = was
        got = support.plain(json.loads(out)) if out.strip() else {}
        return code, got, err + (got.get("error", "") if code else "")

    def history(who) -> list:
        at(who)
        return [line for r in hist_mod.load(who["root"]) for line in r.get("changes") or []]

    try:
        # 1. a wrong code, and no connection, on a fresh install: refused in plain words, nothing written anywhere
        before = files_of(member["home"])
        wrong = run(member, "team", "on", "--route", "relay", "--relay-url", url, "--name", "Bo", "--code-stdin",
                    "--note", "Work on it with Ada", stdin=WRONG + "\n")
        closed = f"http://127.0.0.1:{free_port()}/relay/v1"
        away = run(member, "team", "on", "--route", "relay", "--relay-url", closed, "--name", "Bo", "--code-stdin",
                   "--note", "Work on it with Ada", stdin=CODE + "\n")
        check("357: a wrong relay code and a relay out of reach are each refused in plain words, with no team file, "
              "no device file and no History written",
              wrong[0] != 0 and "relay code is not right" in wrong[2] and away[0] != 0
              and "relay could not be reached" in away[2] and files_of(member["home"]) == before,
              f"{wrong[2]} | {away[2]} | {sorted(set(files_of(member['home']).items()) ^ set(before.items()))}")

        # 2. an agent asking for the relay through MCP is refused: the code is his
        at(member)
        mcp = mcp_server.Server(root=str(member_root), config=str(member["config"]))
        asked = mcp.call(mcp.by_name["team_on"], {"name": "Bo", "request": "Turn on working together"})
        text = " ".join(c.get("text", "") for c in asked.get("content") or [])
        check("357: MCP's team_on refuses the relay route with a plain line, the code being his, and writes nothing",
              asked.get("isError") is True and "relay code" in text and files_of(member["home"]) == before, text)

        # 3. the lead turns on through the relay: no project there yet, so the code is asked and an invite refused
        wt(lead, op="on", name="Ada", route="relay", relay_url=url)
        shown = wt(lead, op="show")["team"]
        no_invite = refused(lambda: wt(lead, op="invite"))
        held_file = (lead_root / team.FILE).read_bytes()
        history_was = history(lead)
        bad = refused(lambda: wt(lead, op="set", code=WRONG))
        check("357: on through the relay with no project there, the lead's section asks for the relay code, an invite is "
              "refused until then, and a wrong code is refused with team.json and History as they were",
              shown.get("needs_code") is True and shown.get("on_relay") is False and "not on the relay yet" in no_invite
              and "relay code is not right" in bad and (lead_root / team.FILE).read_bytes() == held_file
              and history(lead) == history_was, json.dumps(shown)[:300] + no_invite + bad)

        # 4. the code from the command line's standard input makes the project, its id in the signed list of people
        made = run(lead, "team", "set", "--code-stdin", "--note", "Put it on the relay", stdin=CODE + "\n")
        data = team.read_team(lead_root)
        note = (data.get("roster") or {}).get("relay") or {}
        shown = wt(lead, op="show")["team"]
        at(lead)
        come = team.come(lead_root)
        check("357: the lead's code makes the project on the relay: the relay's own 32-hex id, not the team's, kept in "
              "the list of people the lead signs, with the team's own relay's address, the section no longer asking, "
              "a line in History, and the relay letting the lead's computer in",
              made[0] == 0 and re.fullmatch(r"[0-9a-f]{32}", note.get("project") or "") is not None
              and note["project"] != data.get("team") and note.get("url") == url and shown.get("needs_code") is False
              and shown.get("on_relay") is True and team.check_roster(data["roster"]) is not None
              and "The project made on the relay." in history(lead) and come == [], made[2] + json.dumps(note))

        # 5. a fresh install turned on with its code at once, from the command line
        solo_made = run(solo, "team", "on", "--route", "relay", "--relay-url", url, "--name", "Cy", "--code-stdin",
                        "--note", "Work on it with others", stdin=CODE + "\n")
        solo_note = ((team.read_team(solo_root) or {}).get("roster") or {}).get("relay") or {}
        check("357: turning on with the code makes the keys, the team and its project on the relay in one go",
              solo_made[0] == 0 and len(solo_note.get("project") or "") == 32
              and (solo["home"] / team.DEVICE_FILE).is_file(), solo_made[2])

        # 6. invite, the six digits and They match, through the relay, the link carrying the team's own relay
        invite = wt(lead, op="invite")
        joining = wt(member, op="join", words=invite["link"], name="Bo")
        answered = wt(lead, op="answers", invite=invite["invite"])
        wt(lead, op="admit", invite=invite["invite"], match=True)
        joined = wt(member, op="joined", invite=invite["invite"])
        member_data = team.read_team(member_root) or {}
        at(member)
        member_come = team.come(member_root)
        check("357: the invite's link carries the team's own relay, the joiner's answer and the lead's They match go "
              "through the relay's invite mailbox with the same six digits on both, and the joiner's team names the "
              "relay's project, which lets his computer in once the lead has admitted it",
              "?relay=" in invite["link"] and joining.get("code") == answered.get("code") and joined.get("joined") is True
              and ((member_data.get("roster") or {}).get("relay") or {}).get("project") == note["project"]
              and isinstance(member_come, list), json.dumps([joining.get("code"), answered, joined])[:400])

        # 7. a version of the lead's participant reaches the member's copy through team_sync's look
        set_statements(lead_book, 7, ["Taking the loss of a colony as her own fault"])
        at(lead)
        sent = team_sync.sync(lead_root, now=True)
        at(member)
        took = look_until(team_sync, member_root, lambda got: "P1 - Marlow" in got.get("applied", []))
        check("357: through the relay the lead's change to Marlow goes and is applied in the member's copy",
              "P1 - Marlow" in sent.get("sent", []) and "P1 - Marlow" in took.get("applied", [])
              and hashlib.sha256(lead_book.read_bytes()).hexdigest()
              == hashlib.sha256(member["book"].read_bytes()).hexdigest(), json.dumps([sent, took])[:400])

        # 8. the member's own board of Marlow, sent to its owner and taken in by the lead's look
        plan = base / "bo-plan.json"
        plan.write_text(json.dumps({"pets": [{"title": "Listening at the roof", "members": ["S1", "S2"]}]}),
                        encoding="utf-8")
        guard_was, wb_mod.WRITE_GUARD = wb_mod.WRITE_GUARD, None
        try:
            board = run(member, "board", "new", "Marlow", "--from", str(plan), "--note", "Bo's grouping")
        finally:
            wb_mod.WRITE_GUARD = guard_was
        at(member)
        name = next(b["name"] for b in themes.boards_of(themes.load(member["book"]) or {})
                    if any(g["label"] == "Listening at the roof" for g in b["groups"]))
        at(member)
        gone = routes.api_team_board({"op": "send", "workbook": str(member["book"]), "board": name})
        at(lead)
        looked = look_until(team_sync, lead_root, lambda got: "board" in (got.get("taken") or []))
        at(lead)

        def came_in() -> list:
            return [b for b in themes.boards_of(themes.load(lead_book) or {})
                    if any(g["label"] == "Listening at the roof" for g in b["groups"])]

        waits = came_in()
        # it waits, nothing written to Marlow, until Add as next board (wtreview2, 9 November 2026)
        at(lead)
        added = routes.api_team_board({"op": "answer", "workbook": str(lead_book), "accept": True})
        at(lead)
        came = came_in()
        check("357: through the relay the member's board of Marlow goes to its owner, comes in by the lead's look to "
              "wait, and Add as next board adds it",
              board[0] == 0 and gone.get("to") == "Ada" and looked.get("taken") == ["board"] and waits == []
              and added.get("accept") is True and len(came) == 1,
              board[2] + json.dumps(looked)[:300] + json.dumps(added)[:300])

        # 9. the code is nowhere on disk, in either install, their projects or History
        leaked = [str(p.relative_to(base)) for p in base.rglob("*") if p.is_file()
                  and (CODE.encode() in p.read_bytes() or WRONG.encode() in p.read_bytes())]
        check("357: the relay code, right or wrong, is in no file of any install, team.json, the device file, History "
              "or a log", not leaked, str(leaked))

        # 10a. Send through is the lead's choice alone: a member's change is refused in plain words with nothing
        # written, the lead's goes to the member in the signed list of people and his install follows it
        member_file = (member_root / team.FILE).read_bytes()
        by_api = refused(lambda: wt(member, op="set", route="folder"))
        after_api = (member_root / team.FILE).read_bytes()
        by_cli = run(member, "team", "set", "--route", "folder", "--note", "Send through the folder")
        after_cli = (member_root / team.FILE).read_bytes()
        member_view = wt(member, op="show")["team"]
        shared = base / "shared-folder"
        shared.mkdir(exist_ok=True)
        wt(lead, op="set", route="folder", folder=str(shared))
        lead_view = wt(lead, op="show")["team"]
        at(member)
        member_took = team_sync.sync(member_root)
        followed = wt(member, op="show")["team"]
        follow_data = team.read_team(member_root) or {}
        check("357: Send through is the lead's alone: a member's change is refused in plain words by the API and the "
              "command line with team.json as it was, and the member sees the team's route as it is",
              "lead chooses how the team sends" in by_api and by_cli[0] != 0
              and "lead chooses how the team sends" in by_cli[2] and after_api == member_file == after_cli
              and member_view.get("route") == "relay" and member_view.get("you_lead") is False,
              by_api + by_cli[2] + str(member_view.get("route")))
        check("357: the lead's change of route travels in the signed list of people and the member's install follows it, "
              "over the relay it was sent through",
              lead_view.get("route") == "folder" and followed.get("route") == "folder"
              and (follow_data.get("roster") or {}).get("route") == "folder" and follow_data.get("route") == "folder"
              and team.check_roster(follow_data["roster"]) is not None and "P1 - Marlow" not in member_took.get("applied", []),
              json.dumps([lead_view.get("route"), followed.get("route"), member_took])[:300])
        wt(lead, op="set", route="relay")

        # 10. removed: the relay refuses his computer from then on
        member_dev_data = dict(team.read_team(member_root), route="relay")
        at(member)
        member_dev = team.device()
        wt(lead, op="remove", member="Bo")
        import relay_transport as rt
        try:
            team.transport_for(member_dev_data, member_dev).fetch(member_dev_data["team"], 0)
            out = (0, "taken")
        except rt.RelayError as exc:
            out = (exc.status, exc.error)
        check("357: once the lead removes him the relay refuses the member's computer", out == (403, "removed"),
              str(out))

        # 11. a relay's refusals in plain words: a code that has made its twenty projects
        class Full(Exception):
            status, error = 429, "projects for this code"
        check("357: a used-up code is said plainly", team.relay_refusal(Full()).code == "code_used")
    finally:
        (server_mod.CONFIG_PATH, server_mod.ROOT_OVERRIDE, team.DEVICE_PATH, transport.OVERRIDE) = kept
