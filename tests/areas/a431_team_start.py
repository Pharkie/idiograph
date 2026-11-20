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
import time
import unicodedata
import zipfile
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


def made_on(book: Path, when: str) -> None:
    """A workbook's made time, as its properties say, set to `when`: a namesake made elsewhere is not a copy."""
    tmp = book.with_suffix(".tmp")
    with zipfile.ZipFile(book) as src, zipfile.ZipFile(tmp, "w", zipfile.ZIP_DEFLATED) as out:
        for item in src.infolist():
            data = src.read(item.filename)
            if item.filename == "docProps/core.xml":
                text = data.decode("utf-8")
                at = text.index("W3CDTF\">") + len("W3CDTF\">")
                data = (text[:at] + when + text[text.index("</dcterms:created>"):]).encode("utf-8")
            out.writestr(item, data)
    tmp.replace(book)


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
              before_show["team"] == {"on": False} and before_show["start"] == {"kept": False, "joining": []}
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
              {k: call(alone, op="show")["start"][k] for k in ("kept", "joining")} == {"kept": False, "joining": []})

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
              "4,096 bytes, names no participant folder, lists 200 digests whatever the number, so its length says nothing, "
              "and leaves the list out at 300, where the invite is still made",
              len(set(sizes.values())) == 1 and sizes[0] == team.OFFER_BYTES + 40 and sizes[0] <= 4096
              and len(offers[0]["participants"]) == len(offers[100]["participants"]) == team.LIST_N
              and len(offers[200]["participants"]) == team.LIST_N and "participants" not in offers[300]
              and "Grower" not in plain and "P1 - " not in plain, json.dumps(sizes))
        fern = install(scratch, "fern", "Canal towpath walkers, Fern's", ("Fern",))
        unlisted = call(fern, op="join", words=offers[300]["words"], name="Fay")
        check("431: an offer too long to list its participants joins with no check", bool(unlisted.get("code")))

        # 7. an offer with no participants field, made by 0.9.31 or before the update, joins as before (teambuild2)
        made_by = team.offer_body
        team.offer_body = lambda dev, body, secret, entries: team.signed(dev, body)
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

        # 10. teamfix: one rule for a project that holds others, on or off (R1), a copy of a lead's folder joins (R2),
        #     a name composed another way is the same one and an offer of 0.9.32's still matches (R3), the list is
        #     padded (R4), a second joined after team.json is written says joined (R5), a member's own invite takes a
        #     copy of the team's project (review 5), a failed join leaves no keys and a pending join is offered
        #     (review 7), and a namesake that is not a copy is refused (review 8)
        two = install(scratch, "two", "Canal towpath walkers, Two", ())
        two_b = install(scratch, "two-b", "Canal towpath walkers, Two's other computer", ())
        call(two, op="on", name="Ivy")
        own = call(two, op="invite", own=True)
        call(two_b, op="join", words=own["words"], name="Ivy")
        call(two, op="admit", invite=own["invite"], match=True)
        call(two_b, op="joined", invite=own["invite"])
        made11 = call(lead, op="invite")
        on_said = refused(lambda: call(two, op="join", words=made11["words"], name="Ivy"))
        call(two, op="off")
        off_said = refused(lambda: call(two, op="join", words=made11["words"], name="Ivy"))
        check("431: a lead alone with two computers is refused a join by one rule, Working together on or off, and "
              "starting again is offered in both",
              on_said == i18n.t("team.refused.already_team") and off_said == i18n.t("team.refused.kept_team")
              and call(two, op="show")["start"]["kept"] is True, f"{on_said} | {off_said}")

        lead_member = team.read_team(lead["root"])["member"]
        stale = install(scratch, "stale", "Canal towpath walkers, Stale", ())
        shutil.rmtree(stale["root"])
        shutil.copytree(lead["root"], stale["root"])
        at(stale)
        made12 = call(lead, op="invite")
        copied_team = call(stale, op="join", words=made12["words"], name="Sam", copy=True)
        stale3 = install(scratch, "stale3", "Canal towpath walkers, Stale 3", ())
        shutil.rmtree(stale3["root"])
        shutil.copytree(two["root"], stale3["root"])
        shown = call(stale3, op="show")
        no_copy = refused(lambda: call(stale3, op="join", words=made12["words"], name="Sam"))
        # the invite is another team's (the lead's, where this project is a copy of a team of two's): asked first
        before_ask = project_files(stale3["root"])
        asked_said = refused(lambda: call(stale3, op="join", words=made12["words"], name="Sam", copy=True))
        at(stale3)
        try:
            call(stale3, op="join", words=made12["words"], name="Sam", copy=True)
            asked_code = ""
        except WorkbookError as exc:
            asked_code = getattr(exc, "code", "")
        at(stale3)
        import argparse
        cli_args = argparse.Namespace(words=made12["words"], name="Sam", relay_url=None, route=None, folder=None,
                                      copy=True, replace=False, dry_run=False, note="join", tool="")
        cli_said = refused(lambda: cli_mod.cmd_team_join(cli_mod.Project(stale3["root"], False), cli_args))
        at(stale3)
        check("431: a join as a copy from a project whose list names others, to an invite of another team, is "
              "refused with its own code and one plain line, the command line alike, and writes and sends nothing "
              "until the join says replace",
              asked_said == cli_said and asked_said.startswith("Leave ") and "--replace" in asked_said
              and asked_code == "replace_team"
              and project_files(stale3["root"]) == before_ask
              and not ((team.load_device_file() or {}).get("joining") or {}), f"{asked_said} | {cli_said}")
        check("431: a Finder copy of a lead's project folder, team.json in it, joins when the lead is alone, and a "
              "copy of a stopped team with others on it joins only when the join says it is a copy and, to another "
              "team's invite, that it replaces the team, the page's Join beside the line that this computer is not on "
              "the list",
              bool(copied_team.get("code")) and shown["start"]["kept"] is True and shown["start"]["unlisted"] is True
              and no_copy == i18n.t("team.refused.kept_team")
              and bool(call(stale3, op="join", words=made12["words"], name="Sam", copy=True,
                            replace=True).get("code")),
              json.dumps(shown.get("start")))
        # the invite of the project's own team, a computer its list names, asks nothing
        stale4 = install(scratch, "stale4", "Canal towpath walkers, Stale 4", ())
        shutil.rmtree(stale4["root"])
        shutil.copytree(two["root"], stale4["root"])
        call(two, op="on", name="Ivy")
        own_made = call(two, op="invite", own=True)
        same = call(stale4, op="join", words=own_made["words"], name="Ivy", copy=True)
        check("431: a copy of a team's project joining an invite from a computer its list names, as Add a computer "
              "of mine makes, asks nothing",
              bool(same.get("code")) and call(two, op="answers", invite=own_made["invite"])["answered"] is True,
              json.dumps(same.get("code")))
        # the exemption holds for the project's own team alone: an invite from a computer its list names, leading
        # another team of its own, is another team's and asks (review of smallfix20, finding 1)
        other_root = two_b["root"].parent / "Team B"
        other_root.mkdir(parents=True)
        (other_root / "idiograph-project.json").write_text(json.dumps({"name": "Team B"}), encoding="utf-8")
        cfg_b = json.loads(two_b["config"].read_text(encoding="utf-8"))
        cfg_b["projects"].append({"root": str(other_root)})
        two_b["config"].write_text(json.dumps(cfg_b), encoding="utf-8")
        team_b = dict(two_b, root=other_root)
        call(team_b, op="on", name="Ivy")
        made_b = call(team_b, op="invite")
        stale5 = install(scratch, "stale5", "Canal towpath walkers, Stale 5", ())
        shutil.rmtree(stale5["root"])
        shutil.copytree(two["root"], stale5["root"])
        before_b = project_files(stale5["root"])
        said_b = refused(lambda: call(stale5, op="join", words=made_b["words"], name="Ivy", copy=True))
        check("431: a copy of a team's project joining another team's invite, from a computer its own list names that "
              "leads a team of its own, is asked about like any other, and nothing is sent",
              said_b.startswith("Make this project a copy of Ivy's project?") and project_files(stale5["root"]) == before_b
              and call(team_b, op="answers", invite=made_b["invite"])["answered"] is False, said_b)
        # a join begun as a copy whose project then gains others before They match is refused at joined, with the
        # project's team.json as it was (review finding 2)
        late = install(scratch, "late", "Canal towpath walkers, Late", ())
        made_late = call(lead, op="invite")
        call(late, op="join", words=made_late["words"], name="Lia", copy=True)
        shutil.copy(two["root"] / "team.json", late["root"] / "team.json")
        before_late = (late["root"] / "team.json").read_bytes()
        call(lead, op="admit", invite=made_late["invite"], match=True)
        late_said = refused(lambda: call(late, op="joined", invite=made_late["invite"]))
        check("431: joined refuses the replace the join never said yes to, when the project's list gained others "
              "after the join began, before team.json is written",
              late_said == i18n.t("team.refused.replace_late") and (late["root"] / "team.json").read_bytes() == before_late, late_said)
        stale_show = call(stale, op="show")
        check("431: a Finder copy of a lead's project with Working together on, its roster not listing this computer, "
              "shows the team as it stands with unlisted, and its start naming it, for Join alone",
              stale_show["team"]["on"] is True and stale_show["team"]["unlisted"] is True
              and stale_show["start"]["unlisted"] is True and stale_show["team"]["member"] == lead_member,
              json.dumps(stale_show.get("team"))[:200])
        call(lead, op="admit", invite=made12["invite"], match=False)
        stale2 = install(scratch, "stale2", "Canal towpath walkers, Stale 2", ())
        shutil.rmtree(stale2["root"])
        shutil.copytree(lead["root"], stale2["root"])
        stale2_before = project_files(stale2["root"])
        started = call(stale2, op="on", name="Sam")
        check("431: Invite others on such a copy writes nothing, so the lead's team is never replaced from a computer "
              "its list does not name",
              project_files(stale2["root"]) == stale2_before and started["changes"] == []
              and team.read_team(stale2["root"])["team"] == team.read_team(lead["root"])["team"])

        # R3: a name composed another way, against an offer of this version and one 0.9.32's lead made
        zoe = "Zo\u00eb"
        nfc_lead = install(scratch, "nfc-lead", "Canal towpath walkers, NFC", (unicodedata.normalize("NFC", zoe),))
        nfd_copy = install(scratch, "nfd-copy", "Canal towpath walkers, NFD", ())
        shutil.rmtree(nfd_copy["root"])
        shutil.copytree(nfc_lead["root"], nfd_copy["root"])
        old_name = next(nfd_copy["root"].glob("P1 - *"))
        old_name.rename(old_name.with_name(unicodedata.normalize("NFD", old_name.name)))
        call(nfc_lead, op="on", name="Neil")
        made13 = call(nfc_lead, op="invite")
        raw_digest = team.digest_of
        joined_nfd = call(nfd_copy, op="join", words=made13["words"], name="Ned")
        made_by = team.offer_body

        def old_offer(dev, body, secret, entries):
            listed = dict(body, participants=sorted(team.digest_of(secret, e["folder"]) for e in entries), pad="")
            return team.signed(dev, listed)
        team.offer_body = old_offer
        try:
            made14 = call(nfc_lead, op="invite")
        finally:
            team.offer_body = made_by
        nfd_two = install(scratch, "nfd-two", "Canal towpath walkers, NFD 2", ())
        shutil.rmtree(nfd_two["root"])
        shutil.copytree(nfd_copy["root"], nfd_two["root"])
        joined_old = call(nfd_two, op="join", words=made14["words"], name="Ned")
        check("431: a copy whose folder name is composed another way (NFD against NFC) joins, against an offer of "
              "this version and against one a 0.9.32 lead made from the raw bytes of its folder",
              bool(joined_nfd.get("code")) and bool(joined_old.get("code")) and raw_digest is team.digest_of)

        # review 8: a participant of the same folder name made elsewhere is not a copy and is refused, nothing sent
        name_lead = install(scratch, "name-lead", "Canal towpath walkers, Namesakes", ("Wren",))
        namesake = install(scratch, "namesake", "Canal towpath walkers, Namesake's", ("Wren",))
        made_on(next(namesake["root"].glob("P1 - Wren/*.xlsx")), "2026-01-02T03:04:05Z")
        call(name_lead, op="on", name="Nan")
        made15 = call(name_lead, op="invite")
        before = project_files(namesake["root"])
        said = refused(lambda: call(namesake, op="join", words=made15["words"], name="Nat"))
        check("431: a project whose participant has the lead's folder name but a workbook made at another time is "
              "refused as holding a participant the lead does not have, with nothing written or sent, where it "
              "would have had its work replaced by the lead's first full copy",
              said == i18n.t("team.refused.has_participants") and project_files(namesake["root"]) == before
              and call(name_lead, op="answers", invite=made15["invite"])["answered"] is False, said)

        # R4: the list is the same length whether the project has none or some, and holds no more than digests
        listed = {n: len(json.loads(team.aead_open(team.invite_key(team.words_secret(w)),
                                                   hub.boxes[team.mailbox(i)][0][2]))["participants"])
                  for n, (w, i) in {"none": (made13["words"], made13["invite"]),
                                    "one": (made15["words"], made15["invite"])}.items()}
        check("431: an offer lists as many digests for a project of one participant as of none", listed["none"] == listed["one"] == team.LIST_N, json.dumps(listed))

        # review 5: a member's own invite lists none, so a copy of the team's project joins it though the inviting
        # computer holds fewer participants
        member_a = install(scratch, "member-a", "Canal towpath walkers, Mo A", ())
        call(member_a, op="join", words=call(name_lead, op="invite")["words"], name="Mo")
        pending_a = call(member_a, op="show")["start"]["joining"]
        call(name_lead, op="admit", invite=pending_a[0]["invite"], match=True)
        call(member_a, op="joined", invite=pending_a[0]["invite"])
        own2 = call(member_a, op="invite", own=True)
        mo_two = install(scratch, "member-b", "Canal towpath walkers, Mo B", ("Wren",))
        joined_own = call(mo_two, op="join", words=own2["words"], name="Mo")
        sealed_own = json.loads(team.aead_open(team.invite_key(team.words_secret(own2["words"])),
                                               hub.boxes[team.mailbox(own2["invite"])][0][2]))
        check("431: a member's own computer that is a copy of the team's project joins the member's invite though "
              "the computer that made it holds fewer participants, the offer listing none and the same size",
              bool(joined_own.get("code")) and "participants" not in sealed_own and call(member_a, op="answers", invite=own2["invite"])["answered"] is True)

        # R5: a second joined after team.json was written says joined, and drops the entry
        r5 = install(scratch, "r5", "Canal towpath walkers, R5", ())
        made17 = call(name_lead, op="invite")
        call(r5, op="join", words=made17["words"], name="Rae")
        at(r5)
        entry = json.loads(json.dumps(team.load_device_file()["joining"]))
        call(name_lead, op="admit", invite=made17["invite"], match=True)
        call(r5, op="joined", invite=made17["invite"])
        at(r5)
        data_dev = team.load_device_file()
        data_dev["joining"] = entry
        team.save_device_file(data_dev)
        again_joined = call(r5, op="joined", invite=made17["invite"])
        at(r5)
        check("431: a second joined, asked after team.json holds this invite's team, answers joined and drops the "
              "asking, where it answered the project is shared with others",
              again_joined["joined"] is True and not (team.load_device_file() or {}).get("joining"))

        # review 7: a refused join leaves no keys, a join left waiting is offered to finish and can be stopped, and
        # a join whose invite has lapsed is dropped
        keyless = install(scratch, "keyless", "Canal towpath walkers, Keyless", ("Fern",))
        refused(lambda: call(keyless, op="join", words=made17["words"], name="Kay"))
        refused(lambda: call(keyless, op="join", words=made15["words"], name="Kay"))
        check("431: a join refused by the check leaves no device file and no asking behind",
              not (keyless["home"] / team.DEVICE_FILE).exists())
        waiting_p = install(scratch, "waiting", "Canal towpath walkers, Waiting", ())
        made18 = call(name_lead, op="invite")
        call(waiting_p, op="join", words=made18["words"], name="Wil")
        offered = call(waiting_p, op="show")["start"]["joining"]
        check("431: a join begun and not finished is offered in Working together with its six digits",
              len(offered) == 1 and offered[0]["invite"] == made18["invite"] and offered[0]["code"]
              and offered[0]["code"] == call(name_lead, op="answers", invite=made18["invite"])["code"])
        dry_stop = call(waiting_p, op="unjoin", invite=made18["invite"], dry_run=True)
        still = call(waiting_p, op="show")["start"]["joining"]
        stopped_join = call(waiting_p, op="unjoin", invite=made18["invite"])
        check("431: Stop joining drops the asking and the keys the join made, its dry run writing nothing, and "
              "writes nothing to the project",
              dry_stop["dry_run"] is True and len(still) == 1 and stopped_join["changes"] == []
              and call(waiting_p, op="show")["start"]["joining"] == []
              and not (waiting_p["home"] / team.DEVICE_FILE).exists()
              and not (waiting_p["root"] / team.FILE).exists())
        lapsed = install(scratch, "lapsed", "Canal towpath walkers, Lapsed", ())
        made19 = call(name_lead, op="invite")
        call(lapsed, op="join", words=made19["words"], name="Lee")
        at(lapsed)
        data_dev = team.load_device_file()
        data_dev["joining"][made19["invite"]]["expires"] = "2026-01-01T00:00:00+00:00"
        team.save_device_file(data_dev)
        lapsed_file = (lapsed["home"] / team.DEVICE_FILE).read_bytes()
        left_out = call(lapsed, op="show")["start"]["joining"]
        dry_lapsed = call(lapsed, op="unjoin", invite=made19["invite"], dry_run=True)
        read_only = (lapsed["home"] / team.DEVICE_FILE).read_bytes() == lapsed_file
        call(lapsed, op="unjoin", invite=made19["invite"])
        check("431: a join whose invite has lapsed is left out as Working together reads it, and neither the read "
              "nor Stop joining's dry run deletes it or its keys, while Stop joining does",
              left_out == [] and dry_lapsed["dry_run"] is True and read_only
              and not (lapsed["home"] / team.DEVICE_FILE).exists())

        # teamfix2: a computer the list does not name, finding 1. member_a is Mo's computer in name_lead's team, with
        # Nan leading
        def twin(who, tag):
            home = scratch / f"team-431-{tag}"
            shutil.rmtree(home, ignore_errors=True)
            home.mkdir(parents=True)
            config = home / "config.json"
            config.write_text(json.dumps({"projects": [{"root": str(who["root"])}]}), encoding="utf-8")
            return {"home": home, "root": who["root"], "config": config}

        second_mac = twin(member_a, "second-mac")
        rival = install(scratch, "rival", "Rival towpath walkers", ())
        call(rival, op="on", name="Cy")
        made20 = call(rival, op="invite")
        live_before = project_files(member_a["root"])
        seen_second = call(second_mac, op="show")
        on_second = call(second_mac, op="on", name="Mo")
        join_second = refused(lambda: call(second_mac, op="join", words=made20["words"], name="Mo"))
        check("431: a second computer on the same folder of a live team reads the team as it stands, with unlisted, "
              "writes nothing when Invite is pressed and is refused a join to another team",
              seen_second["team"]["on"] is True and seen_second["team"]["unlisted"] is True
              and len(seen_second["team"]["people"]) == 2 and on_second["changes"] == []
              and project_files(member_a["root"]) == live_before
              and join_second == i18n.t("team.refused.already_team")
              and not (second_mac["home"] / team.DEVICE_FILE).exists(), json.dumps(seen_second["team"])[:200])
        lost = twin(member_a, "lost-device")
        call(lost, op="on", name="Mo")
        check("431: the same with a device file lost, one press of Invite leaves the team as it was",
              project_files(member_a["root"]) == live_before
              and team.read_team(member_a["root"])["team"] == team.read_team(name_lead["root"])["team"])
        # teamfix3, recheck A: the lead's second Mac on the same synced folder joins with an "Add a computer of mine"
        # invite. The lead's admit reaches the shared team.json before this computer's joined, and it still keeps
        # the team's key
        nan_mac2 = twin(name_lead, "nan-mac2")
        own = call(name_lead, op="invite", own=True)
        call(nan_mac2, op="join", words=own["words"], name="Nan", copy=True)
        call(name_lead, op="admit", invite=own["invite"], match=True)
        mac2_done = call(nan_mac2, op="joined", invite=own["invite"])
        at(nan_mac2)
        mac2_file = team.load_device_file() or {}
        mac2_id = (mac2_file.get("device") or {}).get("id")
        lead_team = team.read_team(name_lead["root"])
        mac2_keys = ((mac2_file.get("teams") or {}).get(lead_team["team"]) or {}).get("keys") or {}
        mac2_show = call(nan_mac2, op="show")["team"]
        nan_devices = [d["id"] for m in lead_team["roster"]["members"] if m["id"] == lead_team["roster"]["lead"]
                       for d in m["devices"]]
        check("431: the lead's second computer on the same synced folder joins with its own invite after the "
              "admit reached team.json, keeps the team's key, reads the team as listed, and the list holds it once",
              mac2_done["joined"] is True and bool(mac2_keys) and not mac2_file.get("joining")
              and mac2_show["unlisted"] is False and len(nan_devices) == 2 and mac2_id in nan_devices,
              json.dumps({"keys": bool(mac2_keys), "unlisted": mac2_show.get("unlisted"), "n": len(nan_devices)}))
        # a Finder copy of that project, the copy flag of Join beside the line: accepted, and the project is then the
        # other team's
        finder = install(scratch, "finder", "Canal towpath walkers, Finder copy", ())
        shutil.rmtree(finder["root"])
        shutil.copytree(member_a["root"], finder["root"])
        finder_show = call(finder, op="show")
        no_flag = refused(lambda: call(finder, op="join", words=made20["words"], name="Mo"))
        finder_files = project_files(finder["root"])
        asked_first = refused(lambda: call(finder, op="join", words=made20["words"], name="Mo", copy=True))
        flagged = call(finder, op="join", words=made20["words"], name="Mo", copy=True, replace=True)
        call(rival, op="admit", invite=made20["invite"], match=True)
        finder_done = call(finder, op="joined", invite=made20["invite"])
        check("431: a Finder copy of a member's project, its list not naming this computer, shows Join with the "
              "line, is refused without the copy flag and joins another team with it, written once the lead says "
              "they match",
              finder_show["start"]["unlisted"] is True and no_flag == i18n.t("team.refused.already_team")
              and asked_first.startswith("Leave ") and "--replace" in asked_first
              and flagged["code"] and finder_done["joined"] is True and finder_done["team"]["you_lead"] is False
              and team.read_team(finder["root"])["team"] == team.read_team(rival["root"])["team"]
              and project_files(member_a["root"]) == live_before and finder_files != project_files(finder["root"]))
        check("431: a removed member's project, its list naming neither the person nor this computer, holds no team "
              "of this computer's",
              team.holds_others({"on": True, "member": "gone",
                                 "roster": team.read_team(name_lead["root"])["roster"]}) is False)

        # finding 5: forgetting a join under the device file's lock
        held_n = []
        real_held = team.device_held

        @team.contextlib.contextmanager
        def counting():
            held_n.append(1)
            with real_held():
                yield
        locked = install(scratch, "locked", "Canal towpath walkers, Locked", ())
        made21 = call(name_lead, op="invite")
        call(locked, op="join", words=made21["words"], name="Lou")
        team.device_held = counting
        try:
            call(locked, op="unjoin", invite=made21["invite"])
        finally:
            team.device_held = real_held
        check("431: forgetting a join reads and writes the device file under its lock", len(held_n) >= 1)

        # finding 6: Stop joining after They match keeps the computer's keys, and a welcome waiting past the seventh
        # day still joins
        ghost = install(scratch, "ghost", "Canal towpath walkers, Ghost", ())
        made22 = call(name_lead, op="invite")
        call(ghost, op="join", words=made22["words"], name="Gus")
        call(name_lead, op="admit", invite=made22["invite"], match=True)
        at(ghost)
        ghost_id = team.load_device_file()["device"]["id"]
        call(ghost, op="unjoin", invite=made22["invite"])
        at(ghost)
        kept_file = team.load_device_file() or {}
        listed_ids = [d["id"] for m in call(name_lead, op="show")["team"]["people"] for d in m["devices"]]
        check("431: Stop joining once the lead has said they match drops the asking and keeps this computer's keys, "
              "which the lead's list names",
              (kept_file.get("device") or {}).get("id") == ghost_id and not kept_file.get("joining")
              and ghost_id in listed_ids)
        late = install(scratch, "late", "Canal towpath walkers, Late", ())
        made23 = call(name_lead, op="invite")
        call(late, op="join", words=made23["words"], name="Lyn")
        call(name_lead, op="admit", invite=made23["invite"], match=True)
        at(late)
        data_dev = team.load_device_file()
        data_dev["joining"][made23["invite"]]["expires"] = "2026-01-01T00:00:00+00:00"
        team.save_device_file(data_dev)
        late_done = call(late, op="joined", invite=made23["invite"])
        check("431: a welcome waiting past the invite's seventh day still joins", late_done["joined"] is True)

        # finding 7: an asking kept by 0.9.32 has no name for the lead, and reads without one
        nameless = install(scratch, "nameless", "Canal towpath walkers, Nameless", ())
        made24 = call(name_lead, op="invite")
        call(nameless, op="join", words=made24["words"], name="Nim")
        at(nameless)
        data_dev = team.load_device_file()
        for key in ("from", "expires"):
            data_dev["joining"][made24["invite"]].pop(key, None)
        team.save_device_file(data_dev)
        nameless_view = call(nameless, op="show")["start"]["joining"]
        check("431: an asking with no name for the lead is offered with an empty name and the six digits, and can be "
              "stopped",
              len(nameless_view) == 1 and nameless_view[0]["from"] == "" and nameless_view[0]["code"]
              and call(nameless, op="unjoin", invite=made24["invite"])["dry_run"] is False)

        # finding 9: team show on the command line carries start
        at(stale)
        cli_show = cli_mod.cmd_team_show(cli_mod.Project(stale["root"], False), type("A", (), {"agent_relay": False})())
        check("431: the command line's team show carries start, as the route does",
              cli_show[0].get("start", {}).get("unlisted") is True and "team" in cli_show[0])

        # 3b. teamsmall (20 November 2026): the journey's small fixes. Open invites are rows in People that stay
        # whatever the card did, once answered the row's digits are those the joiner has, Cancel the invite drops one
        # and closes it; the second computer's join says it is the member's own; a participant handed over is said on
        # the member's page; a member who stops tells the lead
        import team_sync
        sm_lead = install(scratch, "sm-lead", "Canal towpath walkers, teamsmall", ("Wren", "Fern"))
        sm_bo = install(scratch, "sm-bo", "Canal towpath walkers, teamsmall, Bo's")
        call(sm_lead, op="on", name="Ada")
        first = call(sm_lead, op="invite")
        second = call(sm_lead, op="invite")
        rows = call(sm_lead, op="show")["team"]["invites"]
        quiet = call(sm_lead, op="answers", invite=first["invite"])
        asked_bo = call(sm_bo, op="join", words=first["words"], name="Bo")
        answered_row = call(sm_lead, op="answers", invite=first["invite"])
        check("431: each open invite this computer made is listed in the team's view, answered or not, whatever the "
              "invite's card did, and an answer carries the six digits the joiner has",
              sorted(i["invite"] for i in rows) == sorted([first["invite"], second["invite"]]) and not any(i["own"] for i in rows)
              and quiet["answered"] is False and answered_row["answered"] is True and answered_row["name"] == "Bo"
              and answered_row["code"] == asked_bo["code"] and asked_bo["own"] is False, json.dumps(rows))
        dry_cancel = call(sm_lead, op="cancel", invite=second["invite"], dry_run=True)
        after_dry = call(sm_lead, op="show")["team"]["invites"]
        cancelled = call(sm_lead, op="cancel", invite=second["invite"])
        after_cancel = call(sm_lead, op="show")["team"]
        late_join = refused(lambda: call(install(scratch, "sm-late", "Canal towpath walkers, teamsmall, Late"),
                                         op="join", words=second["words"], name="Lia"))
        admit_gone = refused(lambda: call(sm_lead, op="admit", invite=second["invite"], match=True))
        again = refused(lambda: call(sm_lead, op="cancel", invite=second["invite"]))
        check("431: Cancel the invite drops that invite alone, its dry run changing nothing, the other open invite and "
              "its answer staying, the cancelled one closed so nobody can join with it or be let in, and a second "
              "cancel refused as no invite",
              dry_cancel["dry_run"] is True and len(after_dry) == 2 and cancelled["changes"] == [i18n.t("team.history.invite_cancelled")]
              and [i["invite"] for i in after_cancel["invites"]] == [first["invite"]]
              and call(sm_lead, op="answers", invite=first["invite"])["answered"] is True
              and late_join == i18n.t("team.refused.invite_used") and admit_gone == i18n.t("team.refused.no_invite")
              and again == i18n.t("team.refused.no_invite") and after_cancel["people"][0]["name"] == "Ada"
              and len(after_cancel["people"]) == 1, f"{late_join} | {admit_gone} | {again}")
        agent_all, agent_changes.ALL_OPS = agent_changes.ALL_OPS, None
        sm_text = ""
        try:
            at(sm_lead)
            (sm_lead["root"] / "idiograph-project.json").write_text(json.dumps({
                "name": "Canal towpath walkers, teamsmall", "agents": {"allowed": True, "at": "2026-11-20T09:00:00+00:00"}}),
                encoding="utf-8")
            sm_mcp = mcp_server.Server(root=str(sm_lead["root"]), config=str(sm_lead["config"]))
            sm_agent = sm_mcp.call(sm_mcp.by_name["team_cancel"], {"invite": first["invite"], "request": "Cancel it"})
            sm_dry = sm_mcp.call(sm_mcp.by_name["team_cancel"], {"invite": first["invite"], "request": "Cancel it", "dry_run": True})
            sm_text = " ".join(c.get("text", "") for c in sm_agent.get("content") or [])
        finally:
            agent_changes.ALL_OPS = agent_all
        check("431: MCP's team_cancel is the app's alone for an agent and the invite is still open after it, while "
              "its dry run is answered",
              sm_agent.get("isError") is True and "Only the app" in sm_text and sm_dry.get("isError") is not True
              and len(call(sm_lead, op="show")["team"]["invites"]) == 1, sm_text)
        call(sm_lead, op="admit", invite=first["invite"], match=True)
        call(sm_bo, op="joined", invite=first["invite"])
        # an invite for the member's own other computer says so on both computers
        own_made = call(sm_bo, op="invite", own=True)
        bo_two = install(scratch, "sm-bo-two", "Canal towpath walkers, teamsmall, Bo's laptop")
        own_asked = call(bo_two, op="join", words=own_made["words"], name="Bo")
        own_row = call(sm_bo, op="answers", invite=own_made["invite"])
        own_view = call(sm_bo, op="show")["team"]["invites"]
        check("431: an invite for the member's own other computer says it is his own at the answer and at the join, "
              "so neither side is told to read the number to someone on a call, the join names the project, and its row says so",
              own_asked["own"] is True and own_row["own"] is True and own_row["code"] == own_asked["code"]
              and own_asked["project"] == "Canal towpath walkers, teamsmall, Bo's"
              and [(i["invite"], i["own"]) for i in own_view] == [(own_made["invite"], True)])
        pending_own = call(bo_two, op="show")["start"]["joining"]
        check("431: a second computer's join begun and left is offered again as the member's own",
              len(pending_own) == 1 and pending_own[0]["own"] is True
              and pending_own[0]["project"] == "Canal towpath walkers, teamsmall, Bo's")

        # a member who stops tells the lead, whose People marks the person until they start again
        before_stop = call(sm_lead, op="show")["team"]["people"]
        call(sm_bo, op="off", dry_run=True)
        sent_before = sum(len(v) for v in hub.boxes.values())
        call(sm_bo, op="off")
        sent_after = sum(len(v) for v in hub.boxes.values())
        call(sm_lead, op="send")
        marked = call(sm_lead, op="show")["team"]["people"]
        call(sm_lead, op="take")
        marked_again = call(sm_lead, op="show")["team"]["people"]
        check("431: a member who stops working together sends the lead one line, a dry run sends none, the lead's "
              "People marks that person as having stopped once and the lead's own look and take leave it so, and the "
              "lead who stops sends none",
              [p["stopped"] for p in before_stop] == [False, False] and sent_after == sent_before + 1
              and [p["stopped"] for p in marked] == [False, True] and marked_again == marked,
              json.dumps(marked))
        call(sm_bo, op="on")
        call(sm_lead, op="send")
        call(sm_lead, op="take")
        back = call(sm_lead, op="show")["team"]["people"]
        sent_lead = sum(len(v) for v in hub.boxes.values())
        call(sm_lead, op="off")
        check("431: a member who starts again is no longer marked, and the lead who stops tells no one",
              [p["stopped"] for p in back] == [False, False] and sum(len(v) for v in hub.boxes.values()) == sent_lead)
        call(sm_lead, op="on")

        # offline, a member's Stop and Start again each wait on the route a few seconds at most, and both are
        # written (teamfix4)
        class Stalled:
            def __init__(self, dev):
                self.dev = dev

            def send(self, project_id, sealed):
                time.sleep(6)
                raise OSError("offline")

        loop_way = transport.OVERRIDE
        transport.OVERRIDE = lambda dev, data: Stalled(dev)
        try:
            t0 = time.monotonic()
            call(sm_bo, op="off")
            off_s = time.monotonic() - t0
            off_kept = json.loads((sm_bo["root"] / team.FILE).read_text(encoding="utf-8")).get("on")
            t0 = time.monotonic()
            call(sm_bo, op="on")
            on_s = time.monotonic() - t0
            on_kept = json.loads((sm_bo["root"] / team.FILE).read_text(encoding="utf-8")).get("on")
        finally:
            transport.OVERRIDE = loop_way
        check("431: offline, a member's Stop working together and Start working together again each wait a few "
              "seconds at most on the route, and each is written",
              off_s < 5 and on_s < 5 and off_kept is False and on_kept is True,
              json.dumps({"off": round(off_s, 2), "on": round(on_s, 2)}))

        # what the lead hands over is said on the member's page, once, for what is his now
        call(sm_bo, op="send")
        call(sm_lead, op="set", owners={"P2 - Fern": "Bo"}, gets_owner="Bo")
        call(sm_lead, op="send")
        call(sm_bo, op="send")
        at(sm_bo)
        bo_page = team_sync.status(sm_bo["root"])
        at(sm_lead)
        lead_page = team_sync.status(sm_lead["root"])
        check("431: a participant and the GETs board the lead hands to a member are said on the member's page with who "
              "gave them, newest first, and the lead's page says nothing of them, and the page says who leads",
              sorted((g["name"], g["participant"], g["gets"]) for g in bo_page["gave"]) == [("Ada", "", True), ("Ada", "Fern", False)]
              and bo_page["lead"] is False and lead_page["gave"] == [] and lead_page["lead"] is True,
              json.dumps(bo_page))
        call(sm_lead, op="set", owners={"P2 - Fern": "Ada"})
        call(sm_lead, op="send")
        call(sm_bo, op="send")
        at(sm_bo)
        bo_back = team_sync.status(sm_bo["root"])
        check("431: a participant handed back is no longer said as given to the member",
              [(g["participant"], g["gets"]) for g in bo_back["gave"]] == [("", True)], json.dumps(bo_back["gave"]))

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
