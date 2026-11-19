"""Area 431: how Working together starts (teambuild, 19 November 2026, teammock's option B, Adam's yes that night).
Project settings starts with Invite others to work on this project, which turns Working together on with this
computer as lead, and Join a project you were invited to, which joins with Working together off. Scratch installs in
one process, each its own settings folder, device file and project, through the loopback and through a shared
folder as the app registers it.

What matters: a join from a fresh project writes nothing to the project, no team.json and no History line, so the
joiner never becomes the lead of a team of one before the lead's They match, and after it is a member; a join
through a shared folder says so with `route` and `folder` and is written only once matched, with that folder; a
project holding a participant the invite does not list is refused a join, the command line alike, with nothing
written or sent, because that participant would become the lead's and be refused to this computer, while a copy of
the lead's own project joins as before; and Stop working
together and starting again keeps the team, `show`'s `start` saying a kept team with others on it. Round 2
(teambuild2, the review's findings): a participant with a transcript alone is refused as one with a workbook is;
the sealed offer is one size with 0, 100, 200 or 300 participants and names none, its list left out where it will
not fit; an offer with no list joins with no check; `joined` and `join` refuse a project in, or keeping, a team
with others; and MCP's team_join is refused for an agent while a join's dry run writes nothing. Every fixture is
invented."""
from __future__ import annotations

import json
import os
import shutil
from pathlib import Path

from . import support
from .support import check


def install(scratch: Path, name: str, project: str, people=()) -> dict:
    """A scratch install: its settings file, beside which its device file goes, and one project of its own, with a
    participant folder for each of `people` made from the demo's pristine files under new names."""
    home = scratch / f"team-431-{name}"
    shutil.rmtree(home, ignore_errors=True)
    root = home / project
    root.mkdir(parents=True)
    (root / "idiograph-project.json").write_text(json.dumps({"name": project}), encoding="utf-8")
    pristine = support.source("demo/pristine")
    for n, who in enumerate(people, 1):
        case = root / f"P{n} - {who}"
        (case / "Working").mkdir(parents=True)
        stem = f"P{n} {who} - EN & ES"
        shutil.copy2(pristine / "Juno - EN & ES.xlsx", case / f"{stem}.xlsx")
        for tail in (".themes.json", ".progress.json"):
            shutil.copy2(pristine / "Working" / f"Juno - EN & ES{tail}", case / "Working" / f"{stem}{tail}")
    config = home / "config.json"
    config.write_text(json.dumps({"projects": [{"root": str(root)}]}), encoding="utf-8")
    return {"home": home, "root": root, "config": config}


def transcripts(root: Path, people) -> None:
    """A participant folder for each of `people` holding a transcript alone, in its Source folder, no workbook yet."""
    for n, who in enumerate(people, 1):
        source = root / f"P{n} - {who}" / "Source"
        source.mkdir(parents=True)
        (source / f"{who} - interview.txt").write_text(f"Interviewer: How was the day?\n{who}: Long.\n",
                                                        encoding="utf-8")


def project_files(root: Path) -> dict:
    """Every file under a project with its bytes, by its path from there, the lock file the write takes left out."""
    return {p.relative_to(root).as_posix(): p.read_bytes() for p in sorted(root.rglob("*"))
            if p.is_file() and p.name != ".idiograph.lock"}


def test_team_start(scratch: Path):
    print("\n431. How Working together starts: Join with it off writes nothing until They match and never makes a "
          "lead, a join through a shared folder, Join refused on a project with participants of its own, Stop and start "
          "again keeps the team (teambuild)")
    import i18n
    import folder_transport as ft
    import idiograph_cli as cli_mod
    import idiograph_routes as routes
    import server as server_mod
    import team
    import transport
    from workbook import WorkbookError

    lead = install(scratch, "lead", "Canal towpath walkers", ("Wren",))
    joiner = install(scratch, "joiner", "Canal towpath walkers, Bo's")
    kept = (server_mod.CONFIG_PATH, server_mod.ROOT_OVERRIDE, team.DEVICE_PATH, transport.OVERRIDE,
            os.environ.pop(transport.ENV, None), ft.POLL)
    hub = transport.Hub()
    transport.OVERRIDE = lambda dev, data: transport.Loopback(dev.get("id") or "", hub=hub)

    def at(who):
        server_mod.CONFIG_PATH = who["config"]
        server_mod.ROOT_OVERRIDE = None
        team.DEVICE_PATH = None

    def call(who, **body):
        at(who)
        return routes.api_team(dict(body, root=str(who["root"])))

    def refused(fn) -> str:
        try:
            fn()
        except WorkbookError as exc:
            return str(exc)
        except cli_mod.cli.Refused as exc:
            return " ".join(str(x) for x in exc.args)
        return ""

    try:
        # 1. a join from a fresh project, Working together off: nothing written to it before They match
        call(lead, op="on", name="Ada")
        before_show = call(joiner, op="show")
        made = call(lead, op="invite")
        before = project_files(joiner["root"])
        asked = call(joiner, op="join", words=made["link"], name="Bo")
        after_join = project_files(joiner["root"])
        at(joiner)
        joining = (team.load_device_file() or {}).get("joining") or {}
        check("431: a fresh project starts with nothing on and nothing kept, and its join, with Working together off, "
              "writes nothing to the project, no team.json and no History line, so it never leads a team of one, "
              "while the asking waits on this computer",
              before_show["team"] == {"on": False} and before_show["start"] == {"kept": False}
              and asked["code"] and asked["team"] == {"on": False} and after_join == before
              and not (joiner["root"] / team.FILE).exists() and list(joining) == [made["invite"]]
              and joining[made["invite"]]["route"] == "relay",
              json.dumps({"start": before_show.get("start"), "files": sorted(after_join)}))
        waiting = call(joiner, op="joined", invite=made["invite"])
        check("431: before the lead says they match, joined says it has not come and still writes nothing",
              waiting["joined"] is False and project_files(joiner["root"]) == before, json.dumps(waiting.get("joined")))
        call(lead, op="admit", invite=made["invite"], match=True)
        done = call(joiner, op="joined", invite=made["invite"])
        at(joiner)
        data = team.read_team(joiner["root"])
        roster = data["roster"]
        check("431: after They match the joiner is a member of the lead's team, never its lead, the list as the lead "
              "signed it",
              done["joined"] and done["team"]["on"] and done["team"]["you_lead"] is False
              and data["member"] != roster["lead"] and [p["name"] for p in done["team"]["people"]] == ["Ada", "Bo"]
              and [p["lead"] for p in done["team"]["people"]] == [True, False],
              json.dumps({"you_lead": done["team"].get("you_lead")}))

        # 2. Stop working together and starting again keeps the team, `start` saying a kept team with others on it
        team_id, people = data["team"], [p["id"] for p in done["team"]["people"]]
        call(lead, op="off")
        stopped = call(lead, op="show")
        again = call(lead, op="on")
        check("431: Stop working together keeps the team, show's start says it is kept with others on it, and "
              "starting again picks it up with the same team and the same people",
              stopped["team"] == {"on": False} and stopped["start"]["kept"] is True
              and again["team"]["on"] and again["team"]["you_lead"]
              and [p["id"] for p in again["team"]["people"]] == people
              and team.read_team(lead["root"])["team"] == team_id,
              json.dumps(stopped.get("start")))
        alone = install(scratch, "alone", "Canal towpath walkers, alone")
        call(alone, op="on", name="Cy")
        call(alone, op="off")
        check("431: a team kept with nobody else on it is not kept for starting again, so Invite and Join show",
              call(alone, op="show")["start"] == {"kept": False})

        # 3. a project holding a participant the invite does not list refused a join, through the route and the
        #    command line, and a copy of the lead's own project joins as before
        full = install(scratch, "full", "Canal towpath walkers, Fay's", ("Fern",))
        made2 = call(lead, op="invite")
        before = project_files(full["root"])
        said = refused(lambda: call(full, op="join", words=made2["words"], name="Fay"))
        at(full)
        import argparse
        args = argparse.Namespace(words=made2["words"], name="Fay", relay_url=None, route=None, folder=None,
                                  dry_run=False, note="join Ada's project", tool="")
        said_cli = refused(lambda: cli_mod.cmd_team_join(cli_mod.Project(full["root"], False), args))
        at(full)
        check("431: a join from a project holding a participant the lead's project does not have is refused in one "
              "plain line, the command line alike, with nothing written to the project, no asking kept and no "
              "answer sent to the lead",
              said == said_cli == i18n.t("team.refused.has_participants")
              and project_files(full["root"]) == before
              and not ((team.load_device_file() or {}).get("joining") or {})
              and call(lead, op="answers", invite=made2["invite"])["answered"] is False, f"{said} | {said_cli}")
        copy = install(scratch, "copy", "Canal towpath walkers, Gil's", ("Wren",))
        made3 = call(lead, op="invite")
        copied = call(copy, op="join", words=made3["words"], name="Gil")
        check("431: a copy of the lead's own project, its participants the lead's, joins as before",
              copied.get("code") and call(lead, op="answers", invite=made3["invite"])["answered"] is True,
              json.dumps(copied.get("code")))

        # 5. a participant with a transcript alone, no workbook yet, is a participant too: refused (teambuild2)
        lark = install(scratch, "lark", "Canal towpath walkers, Lark's")
        transcripts(lark["root"], ("Lark",))
        made5 = call(lead, op="invite")
        before = project_files(lark["root"])
        said = refused(lambda: call(lark, op="join", words=made5["words"], name="Lu"))
        check("431: a join from a project whose only participant has a transcript and no workbook yet is refused as "
              "one with a workbook is, with nothing written and no answer sent",
              said == i18n.t("team.refused.has_participants") and project_files(lark["root"]) == before
              and call(lead, op="answers", invite=made5["invite"])["answered"] is False, said)

        # 6. the offer is one size whatever the number of participants, and names none: a digest of each, padded
        sizes, offers = {}, {}
        for n in (0, 100, 200, 300):
            big = install(scratch, f"big{n}", f"Allotment {n}")
            transcripts(big["root"], [f"Grower{i}" for i in range(1, n + 1)])
            call(big, op="on", name="Ada")
            got = call(big, op="invite")
            sealed = hub.boxes[team.mailbox(got["invite"])][0][2]
            sizes[n] = len(sealed)
            offers[n] = json.loads(team.aead_open(team.invite_key(team.words_secret(got["words"])), sealed))
            offers[n]["words"] = got["words"]
        plain = json.dumps(offers[100])
        check("431: an invite's sealed offer is the same size with 0, 100, 200 and 300 participants, under the relay's "
              "4,096 bytes, names no participant folder, lists a digest of each up to 200, and leaves the list out at "
              "300, where the invite is still made",
              len(set(sizes.values())) == 1 and sizes[0] == team.OFFER_BYTES + 40 and sizes[0] <= 4096
              and offers[0]["participants"] == [] and len(offers[100]["participants"]) == 100
              and len(offers[200]["participants"]) == 200 and "participants" not in offers[300]
              and "Grower" not in plain and "P1 - " not in plain, json.dumps(sizes))
        fern = install(scratch, "fern", "Canal towpath walkers, Fern's", ("Fern",))
        unlisted = call(fern, op="join", words=offers[300]["words"], name="Fay")
        check("431: an offer too long to list its participants joins with no check", bool(unlisted.get("code")))

        # 7. an offer with no participants field, made by 0.9.31 or before the update, joins as before (teambuild2)
        made_by = team.offer_body
        team.offer_body = lambda dev, body, secret, folders: team.signed(dev, body)
        try:
            old = call(lead, op="invite")
        finally:
            team.offer_body = made_by
        fern2 = install(scratch, "fern2", "Canal towpath walkers, Fern's again", ("Fern",))
        old_join = call(fern2, op="join", words=old["words"], name="Fay")
        check("431: an invite whose offer has no participants field joins a project with participants of its own, "
              "with no check, as before",
              bool(old_join.get("code")) and call(lead, op="answers", invite=old["invite"])["answered"] is True)

        # 8. joined refuses a project that has since come into a team with others, and join one that keeps a
        #    stopped team with others on it, each with nothing written (teambuild2)
        xx = install(scratch, "xx", "Canal towpath walkers, Xe's")
        yy = install(scratch, "yy", "Canal towpath walkers, Yo's")
        made8 = call(lead, op="invite")
        call(xx, op="join", words=made8["words"], name="Xe")
        call(xx, op="on", name="Xe")
        xinv = call(xx, op="invite")
        call(yy, op="join", words=xinv["words"], name="Yo")
        call(xx, op="admit", invite=xinv["invite"], match=True)
        call(lead, op="admit", invite=made8["invite"], match=True)
        before = project_files(xx["root"])
        now_team = refused(lambda: call(xx, op="joined", invite=made8["invite"]))
        after_joined = project_files(xx["root"])
        call(xx, op="off")
        made9 = call(lead, op="invite")
        before_kept = project_files(xx["root"])
        kept_team = refused(lambda: call(xx, op="join", words=made9["words"], name="Xe"))
        check("431: joined is refused for a project now in a team with others, and join for one keeping a stopped "
              "team with others on it, each in one plain line with nothing written and no answer sent",
              now_team == i18n.t("team.refused.already_team") and after_joined == before
              and kept_team == i18n.t("team.refused.kept_team") and project_files(xx["root"]) == before_kept
              and call(lead, op="answers", invite=made9["invite"])["answered"] is False, f"{now_team} | {kept_team}")

        # 9. MCP's team_join is the app's alone for an agent, and a join's dry run, through MCP and the command
        #    line, writes nothing, not even this computer's keys
        import mcp_server
        mo = install(scratch, "mo", "Canal towpath walkers, Mo's")
        (mo["root"] / "idiograph-project.json").write_text(json.dumps({
            "name": "Canal towpath walkers, Mo's", "agents": {"allowed": True, "at": "2026-11-19T09:00:00+00:00"}}),
            encoding="utf-8")
        made10 = call(lead, op="invite")
        before = project_files(mo["root"])
        at(mo)
        mcp = mcp_server.Server(root=str(mo["root"]), config=str(mo["config"]))
        asks = {"words": made10["words"], "name": "Mo", "request": "Join Ada's project"}
        # the suite stands in for the app through the command line (agent_changes.ALL_OPS): an agent's call here
        import agent_changes
        all_ops, agent_changes.ALL_OPS = agent_changes.ALL_OPS, None
        try:
            agent = mcp.call(mcp.by_name["team_join"], asks)
            dry = mcp.call(mcp.by_name["team_join"], dict(asks, dry_run=True))
        finally:
            agent_changes.ALL_OPS = all_ops
        at(mo)
        args = argparse.Namespace(words=made10["words"], name="Mo", relay_url=None, route=None, folder=None,
                                  dry_run=True, note="join Ada's project", tool="")
        cli_mod.cmd_team_join(cli_mod.Project(mo["root"], False), args)
        text = " ".join(c.get("text", "") for c in agent.get("content") or [])
        check("431: MCP's team_join is refused for an agent as the app's alone, and its dry run and the command "
              "line's answer with nothing written to the project, no keys made and no answer sent",
              agent.get("isError") is True and "Only the app" in text and dry.get("isError") is not True
              and project_files(mo["root"]) == before and not (mo["home"] / team.DEVICE_FILE).exists()
              and call(lead, op="answers", invite=made10["invite"])["answered"] is False, text)

        # 4. a join through a shared folder, with Working together off: the folder said with the join, written at
        #    They match
        transport.OVERRIDE = None
        ft.POLL = 0.05
        shared = scratch / "team-431-shared" / "OneDrive" / "Towpath"
        shutil.rmtree(scratch / "team-431-shared", ignore_errors=True)
        shared.mkdir(parents=True)
        flead = install(scratch, "flead", "Towpath, by folder")
        fjoin = install(scratch, "fjoin", "Towpath, by folder, Di's")
        call(flead, op="on", name="Hal", route="folder", folder=str(shared))
        fmade = call(flead, op="invite")
        bad = refused(lambda: call(fjoin, op="join", words=fmade["words"], name="Di", route="post"))
        by_relay = refused(lambda: call(fjoin, op="join", words=fmade["words"], name="Di", route="folder"))
        fbefore = project_files(fjoin["root"])
        fasked = call(fjoin, op="join", words=fmade["words"], name="Di", route="folder", folder=str(shared))
        fafter = project_files(fjoin["root"])
        answered = call(flead, op="answers", invite=fmade["invite"])
        call(flead, op="admit", invite=fmade["invite"], match=True)
        fdone = call(fjoin, op="joined", invite=fmade["invite"])
        at(fjoin)
        fdata = team.read_team(fjoin["root"])
        check("431: a join through a shared folder from a project with Working together off names the folder with "
              "the join, writes nothing until They match, and then the member's team sends through that folder; "
              "a route that is not one is refused, and the folder route with no folder asks for it",
              bad == i18n.t("team.refused.bad_route") and by_relay == i18n.t("team.refused.no_folder")
              and fafter == fbefore and fasked["code"] == answered["code"] and fdone["joined"]
              and fdata["route"] == "folder" and fdata["folder"] == str(shared) and fdone["team"]["you_lead"] is False,
              f"{bad} | {by_relay} | {json.dumps(fdone.get('joined'))}")
    finally:
        (server_mod.CONFIG_PATH, server_mod.ROOT_OVERRIDE, team.DEVICE_PATH, transport.OVERRIDE, env, ft.POLL) = kept
        if env is not None:
            os.environ[transport.ENV] = env
