"""Area 433: Join a project on Home (teamjoin, 20 November 2026, Adam's rulings that night after teamflow's drawings p1,
p2 and p5). A fresh install with no project of its own joins from Home: the invite read first (`offer`) for who
sent it and the project's name, the folder offered under ~/Documents/Idiograph named after it, then `join` with
`into`, which makes the folder and the project under the lead's name, adds it to Idiograph's projects and joins
into it, through the route and the command line. Scratch installs in one process, each its own settings folder and
device file, the home folder a scratch one, through the loopback and through a shared folder.

What matters: a joiner never makes an empty project first; the project made is the one the lead named and is on
Home; the link says the route its invite went by, so a folder invite asks for the folder and a link from before
links said it still joins by the relay; another computer of the member's joins from Home with no name asked and is
the member's own; and a refusal (words that are not an invite, a folder that holds anything) and every dry run
write nothing, not even the folder or this computer's keys. Every fixture is invented."""
from __future__ import annotations

import json
import os
import shutil
from pathlib import Path

from . import support
from .support import check


def install(scratch: Path, name: str, project: str = "", people=(), your_name: str = "") -> dict:
    """A scratch install: its settings file, beside which its device file goes, and with `project` one project of
    its own, a participant folder for each of `people` from the demo's pristine files; with none, a fresh install."""
    home = scratch / f"team-433-{name}"
    shutil.rmtree(home, ignore_errors=True)
    home.mkdir(parents=True)
    projects = []
    root = None
    if project:
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
        projects = [{"root": str(root)}]
    config = home / "config.json"
    config.write_text(json.dumps(dict({"projects": projects}, **({"your_name": your_name} if your_name else {}))),
                      encoding="utf-8")
    return {"home": home, "root": root, "config": config}


def plain(value):
    """A value of the command line's answer as an agent reads it, its words marked as data, taken out."""
    return value.get("untrusted_text") if isinstance(value, dict) and "untrusted_text" in value else value


def tree(folder: Path) -> dict:
    """Every file under a folder with its bytes, by its path from there, {} when it is not there."""
    if not folder.exists():
        return {}
    return {p.relative_to(folder).as_posix(): p.read_bytes() for p in sorted(folder.rglob("*")) if p.is_file()}


def test_team_join_home(scratch: Path):
    print("\n433. Join a project on Home: a fresh install joins into a new folder named for the lead's project, "
          "through the route and the command line, a folder invite by its link, an old link, another computer of "
          "the member's, and refusals and dry runs writing nothing (teamjoin)")
    import argparse  # noqa: F401 - the command line's own namespace, through cli.run
    import agent_changes
    import cli
    import folder_transport as ft
    import i18n
    import idiograph_routes as routes
    import mcp_server
    import server as server_mod
    import team
    import transport
    from workbook import WorkbookError

    lead = install(scratch, "lead", "Dogs at home", ("Wren",))
    places = scratch / "team-433-home"
    shutil.rmtree(places, ignore_errors=True)
    places.mkdir(parents=True)
    kept = (server_mod.CONFIG_PATH, server_mod.ROOT_OVERRIDE, team.DEVICE_PATH, transport.OVERRIDE,
            os.environ.pop(transport.ENV, None), ft.POLL, os.environ.get("HOME"), os.environ.get("USERPROFILE"))
    # the home folder a scratch one, so the folder offered, ~/Documents/Idiograph, is the suite's
    # (Windows reads USERPROFILE for "~", the Mac and Linux read HOME, so both point at the scratch one)
    os.environ["HOME"] = str(places)
    os.environ["USERPROFILE"] = str(places)
    hub = transport.Hub()
    transport.OVERRIDE = lambda dev, data: transport.Loopback(dev.get("id") or "", hub=hub)
    base = places / "Documents" / "Idiograph"

    def at(who):
        server_mod.CONFIG_PATH = who["config"]
        server_mod.ROOT_OVERRIDE = None
        team.DEVICE_PATH = None

    def call(who, **body):
        at(who)
        if who.get("root") is not None and body.get("op") not in ("offer",) and not body.get("into"):
            body = dict(body, root=str(who["root"]))
        return routes.api_team(body)

    def refused(fn) -> str:
        try:
            fn()
        except WorkbookError as exc:
            return str(exc)
        return ""

    def roots(who) -> list:
        at(who)
        return [str(r) for r in server_mod.project_roots()]

    def device_there(who) -> bool:
        return (who["home"] / team.DEVICE_FILE).exists()

    try:
        call(lead, op="on", name="Ada")
        made = call(lead, op="invite")
        bo = install(scratch, "bo")
        config_before = bo["config"].read_bytes()

        # 0. where Documents is: on Windows what the system says, a OneDrive one included, else ~/Documents, and on
        # the Mac and Linux ~/Documents whatever such a call would say (this Mac has no such call, so a stand-in)
        moved = places / "OneDrive" / "Documentos"
        was_calls = (routes.on_windows, routes.system_documents)
        try:
            routes.on_windows, routes.system_documents = (lambda: True), (lambda: moved)
            win = routes.join_free_folder("Dogs at home")
            routes.system_documents = lambda: None
            win_none = routes.join_free_folder("Dogs at home")
            routes.on_windows, routes.system_documents = (lambda: False), (lambda: moved)
            other = routes.join_free_folder("Dogs at home")
        finally:
            routes.on_windows, routes.system_documents = was_calls
        check("433: Join a project on Home offers its folder in the Documents folder the system names on Windows, "
              "falling back to ~/Documents where the call does not answer, and always ~/Documents on the Mac and Linux",
              win == moved / "Idiograph" / "Dogs at home" and win_none == base / "Dogs at home"
              and other == base / "Dogs at home", f"{win} {win_none} {other}")

        # 1. the invite read first: who sent it, the project as the lead named it, the folder offered after it
        empty = call(bo, op="offer")
        offer = call(bo, op="offer", words=made["link"])
        check("433: the invite's link says the route it went by, and read on Home before joining it names the lead "
              "and the project as she named it, offering ~/Documents/Idiograph/<project>, with nothing written, not "
              "even this computer's keys or the folder",
              "?via=relay#" in made["link"] and team.link_via(made["link"]) == "relay"
              and empty["into"] == "~/Documents/Idiograph/" + i18n.t("team.home.default_project")
              and offer["from"] == "Ada" and offer["project"] == "Dogs at home" and offer["own"] is False
              and offer["via"] == "relay" and offer["into"] == "~/Documents/Idiograph/Dogs at home"
              and not device_there(bo) and not (places / "Documents").exists()
              and bo["config"].read_bytes() == config_before, json.dumps({k: offer.get(k) for k in ("from", "project", "into")}))

        # 2. refusals write nothing: words that are not an invite, a folder that holds anything
        bad = refused(lambda: call(bo, op="join", words="pepper dune gull", into=str(base / "Bad"), name="Bo"))
        full = places / "Full"
        full.mkdir()
        (full / "notes.txt").write_text("mine", encoding="utf-8")
        not_empty = refused(lambda: call(bo, op="join", words=made["link"], into=str(full), name="Bo"))
        check("433: a join from Home is refused with nothing written for words that are not an invite and for a "
              "folder that holds anything: no folder made, the folder as it was, no keys, Idiograph's projects as "
              "they were and the invite unanswered",
              bad == i18n.t("team.refused.bad_words") and not_empty == i18n.t("team.home.not_empty")
              and not (base / "Bad").exists() and tree(full) == {"notes.txt": b"mine"} and not device_there(bo)
              and bo["config"].read_bytes() == config_before
              and call(lead, op="answers", invite=made["invite"])["answered"] is False, f"{bad} | {not_empty}")

        # 2b. a folder holding only what Finder leaves is empty, and a folder that cannot be made (a name too long
        # for the disk) is refused in one line with nothing left behind (teamfix4)
        shown = places / "Shown"
        shown.mkdir()
        (shown / ".DS_Store").write_bytes(b"\x00\x00\x00\x01Bud1")
        shown_dry = call(bo, op="join", words=made["link"], into=str(shown), name="Bo", dry_run=True)
        long_parent = places / "Long"
        too_long = refused(lambda: call(bo, op="join", words=made["link"], into=str(long_parent / ("a" * 300)),
                                        name="Bo"))
        check("433: a join from Home takes a folder holding only .DS_Store as empty, and refuses a folder it cannot "
              "make in one line, leaving no folder, no keys and Idiograph's projects as they were",
              shown_dry.get("dry_run") is True and too_long == i18n.t("team.home.not_made")
              and not long_parent.exists() and not device_there(bo) and bo["config"].read_bytes() == config_before
              and call(lead, op="answers", invite=made["invite"])["answered"] is False, too_long)

        # 3. dry runs, the route's and the command line's, write nothing, not even the folder
        into = base / "Dogs at home"
        dry = call(bo, op="join", words=made["link"], into="~/Documents/Idiograph/Dogs at home", name="Bo",
                   dry_run=True)
        code, out, err = cli.run(["--config", str(bo["config"]), "--json", "team", "join", made["link"], "--into",
                                  str(into), "--name", "Bo", "--dry-run"])
        check("433: a join from Home's dry run, through the route and the command line, checks the words and the "
              "folder and writes nothing, no folder, no keys and no project added",
              dry["dry_run"] is True and dry["into"] == str(into) and code == 0 and not into.exists()
              and not (places / "Documents").exists() and not device_there(bo)
              and bo["config"].read_bytes() == config_before
              and call(lead, op="answers", invite=made["invite"])["answered"] is False, err or out[:300])

        # 4. the join: the folder and the project made, on Home, joined once the lead says they match
        asked = call(bo, op="join", words=made["link"], into="~/Documents/Idiograph/Dogs at home", name="Bo")
        held = json.loads((into / server_mod.PROJECT_FILE).read_text(encoding="utf-8"))
        listed = roots(bo)
        waiting = call(dict(bo, root=into), op="joined", invite=asked["invite"])
        answered = call(lead, op="answers", invite=made["invite"])
        check("433: Join on Home makes the folder offered and in it the project under the lead's name, of her "
              "project's method, adds it to Idiograph's projects as New project does, and sends the answer with the "
              "six digits, writing no team.json before They match",
              asked["code"] == answered.get("code") and asked["project"]["name"] == "Dogs at home"
              and asked["into"] == str(into.resolve()) and held.get("name") == "Dogs at home"
              and held.get("method") == "ipa" and listed == [str(into.resolve())]
              and not (into / team.FILE).exists() and waiting["joined"] is False
              and answered.get("name") == "Bo", json.dumps({"roots": listed, "name": held.get("name")}))
        call(lead, op="admit", invite=made["invite"], match=True)
        done = call(dict(bo, root=into), op="joined", invite=asked["invite"])
        at(bo)
        data = team.read_team(into)
        check("433: once the lead says they match, the project joined from Home is the member's copy of the lead's "
              "team, Bo a member and never its lead, and it stands among the projects Home lists",
              done["joined"] is True and data["on"] is True and done["team"]["you_lead"] is False
              and data["route"] == "relay" and any(p["name"] == "Dogs at home" for p in routes.projects_view()["projects"]),
              json.dumps(done.get("team", {}).get("you_lead")))

        # 5. the command line: team offer and team join --into, with no project of his
        cy = install(scratch, "cy")
        made2 = call(lead, op="invite")
        code_o, out_o, _ = cli.run(["--config", str(cy["config"]), "--json", "team", "offer", made2["link"]])
        said_o = json.loads(out_o) if code_o == 0 else {}
        cy_into = base / "Dogs at home 2"
        code_j, out_j, err_j = cli.run(["--config", str(cy["config"]), "--json", "team", "join", made2["link"],
                                        "--into", str(cy_into), "--name", "Cy", "--note", "Join Ada's project",
                                        "--tool", "Claude Code"])
        said_j = json.loads(out_j) if code_j == 0 else {}
        cy_listed = roots(cy)
        check("433: the command line's team offer reads the invite and offers the next free folder, Dogs at home 2 "
              "beside the one Bo joined into, and team join --into makes it, adds the project and sends the answer, "
              "with no project of his needed",
              code_o == 0 and str(plain(said_o.get("into")) or "").endswith("Dogs at home 2")
              and code_j == 0 and (cy_into / server_mod.PROJECT_FILE).is_file() and cy_listed == [str(cy_into.resolve())]
              and call(lead, op="answers", invite=made2["invite"])["answered"] is True,
              (err_j or out_j)[:400])
        call(lead, op="admit", invite=made2["invite"], match=True)
        cy_done = call(dict(cy, root=cy_into), op="joined", invite=plain(said_j.get("invite")))
        check("433: the project the command line joined into takes the lead's They match as one joined from the "
              "card does", cy_done["joined"] is True, json.dumps(cy_done.get("joined")))

        # 6. an old link, made before links said the route, still joins by the relay
        made3 = call(lead, op="invite")
        old = made3["link"].replace("?via=relay", "")
        dee = install(scratch, "dee")
        dee_into = places / "Elsewhere" / "Dee's copy"
        dee_offer = call(dee, op="offer", words=old)
        dee_asked = call(dee, op="join", words=old, into=str(dee_into), name="Dee")
        at(dee)
        dee_route = ((team.load_device_file() or {}).get("joining") or {}).get(dee_asked["invite"], {}).get("route")
        check("433: a link from before links said the route reads and joins by the relay as before, into a folder "
              "anywhere he types, its parents made",
              "via=" not in old and dee_offer["via"] == "" and dee_offer["route"] == "relay"
              and dee_asked["code"] and dee_route == "relay" and dee_into.is_dir(), str(dee_route))

        # 7. a folder invite: the link says folder, so the joiner gives the folder and no route
        transport.OVERRIDE = None
        ft.POLL = 0.05
        shared = scratch / "team-433-shared" / "OneDrive" / "Dogs"
        shutil.rmtree(scratch / "team-433-shared", ignore_errors=True)
        shared.mkdir(parents=True)
        flead = install(scratch, "flead", "Dogs by folder")
        call(flead, op="on", name="Hal", route="folder", folder=str(shared))
        fmade = call(flead, op="invite")
        di = install(scratch, "di")
        di_into = base / "Dogs by folder"
        no_folder = refused(lambda: call(di, op="offer", words=fmade["link"]))
        fo = call(di, op="offer", words=fmade["link"], folder=str(shared))
        fasked = call(di, op="join", words=fmade["link"], into=str(di_into), name="Di", folder=str(shared))
        call(flead, op="admit", invite=fmade["invite"], match=True)
        fdone = call(dict(di, root=di_into), op="joined", invite=fasked["invite"])
        at(di)
        fdata = team.read_team(di_into) or {}
        check("433: a folder invite's link says folder, so Home asks only for the folder: without it the invite "
              "cannot be read, with it the join goes through that folder and the member's team sends through it",
              "?via=folder#" in fmade["link"] and no_folder == i18n.t("team.refused.no_folder")
              and fo["via"] == "folder" and fo["route"] == "folder" and fo["project"] == "Dogs by folder"
              and fdone["joined"] is True and fdata.get("route") == "folder" and fdata.get("folder") == str(shared),
              f"{no_folder} | {json.dumps(fdata.get('route'))}")
        transport.OVERRIDE = lambda dev, data: transport.Loopback(dev.get("id") or "", hub=hub)
        ft.POLL = kept[5]

        # 8. another computer of Bo's joins from Home: no name asked, the member's own team, not a new one
        bo_root = dict(bo, root=into)
        own = call(bo_root, op="invite", own=True)
        bo2 = install(scratch, "bo2")
        own_offer = call(bo2, op="offer", words=own["link"])
        bo2_into = places / "Laptop" / "Dogs at home"
        own_asked = call(bo2, op="join", words=own["link"], into=str(bo2_into))
        own_said = call(bo_root, op="answers", invite=own["invite"])
        call(bo_root, op="admit", invite=own["invite"], match=True)
        own_done = call(dict(bo2, root=bo2_into), op="joined", invite=own_asked["invite"])
        at(bo2)
        own_data = team.read_team(bo2_into) or {}
        at(bo)
        bo_member = (team.read_team(into) or {}).get("member")
        check("433: another computer of Bo's joins from Home with no name asked: the invite says it is his own, the "
              "answer carries his name, and once his first computer says they match it is Bo on Ada's team, not a "
              "new one",
              own_offer["own"] is True and own_offer["from"] == "Bo" and own_offer["project"] == "Dogs at home"
              and own_asked["own"] is True and own_said.get("name") == "Bo" and own_done["joined"] is True
              and own_data.get("member") == bo_member and own_data.get("team") == (team.read_team(into) or {}).get("team"),
              json.dumps({"own": own_offer.get("own"), "joined": own_done.get("joined")}))

        # 9. for an agent the join is the app's alone; its dry run, through MCP, writes nothing
        eve = install(scratch, "eve")
        made4 = call(lead, op="invite")
        at(eve)
        mcp = mcp_server.Server(config=str(eve["config"]))
        eve_into = base / "Eve"
        asks = {"words": made4["link"], "name": "Eve", "into": str(eve_into), "request": "Join Ada's project"}
        all_ops, agent_changes.ALL_OPS = agent_changes.ALL_OPS, None
        try:
            agent = mcp.call(mcp.by_name["team_join"], asks)
            mdry = mcp.call(mcp.by_name["team_join"], dict(asks, dry_run=True))
            mread = mcp.call(mcp.by_name["team_offer"], {"words": made4["link"]})
        finally:
            agent_changes.ALL_OPS = all_ops
        text = " ".join(c.get("text", "") for c in agent.get("content") or [])
        check("433: MCP's team_join with into is refused for an agent as the app's alone, its dry run writes "
              "nothing, no folder, no keys, no project, and team_offer reads the invite",
              agent.get("isError") is True and "Only the app" in text and mdry.get("isError") is not True
              and mread.get("isError") is not True and not eve_into.exists() and not device_there(eve)
              and roots(eve) == [] and call(lead, op="answers", invite=made4["invite"])["answered"] is False, text[:300])

        # 10. a join from Home that does not complete takes the empty project away, and tells a joiner of a cancel
        # (lowsW): the lead cancels the invite before saying They match, and the joiner's next look says so
        fay = install(scratch, "fay")
        made5 = call(lead, op="invite")
        fay_into = base / "Fay's copy"
        fay_asked = call(fay, op="join", words=made5["link"], into=str(fay_into), name="Fay")
        fay_there = fay_into.is_dir() and roots(fay) == [str(fay_into.resolve())]
        call(lead, op="cancel", invite=made5["invite"])
        fay_said = refused(lambda: call(dict(fay, root=fay_into), op="joined", invite=fay_asked["invite"]))
        check("433: the lead cancelling an invite is said to a joiner who had answered it, and the project the Join "
              "on Home made for it is taken away again, folder and entry, with no keys left on that computer",
              fay_there and fay_said == i18n.t("team.refused.invite_closed") and not fay_into.exists()
              and roots(fay) == [] and not device_there(fay), f"{fay_said} | {fay_into.exists()}")
        # a project that holds a participant by then, or a folder he named that was empty, is not taken away whole
        gus = install(scratch, "gus")
        made6 = call(lead, op="invite")
        gus_into = base / "Gus's copy"
        gus_asked = call(gus, op="join", words=made6["link"], into=str(gus_into), name="Gus")
        shutil.copytree(lead["root"] / "P1 - Wren", gus_into / "P1 - Wren")
        call(lead, op="cancel", invite=made6["invite"])
        gus_said = refused(lambda: call(dict(gus, root=gus_into), op="joined", invite=gus_asked["invite"]))
        check("433: a project made by a join from Home that holds a participant when the join ends is left as it is",
              gus_said == i18n.t("team.refused.invite_closed") and (gus_into / "P1 - Wren").is_dir()
              and roots(gus) == [str(gus_into.resolve())], gus_said)
        # an invite that lapsed after They differ ends the same way, and an empty folder he named stays, emptied
        hal = install(scratch, "hal")
        made7 = call(lead, op="invite")
        hal_into = places / "Hal's folder"
        hal_into.mkdir()
        hal_asked = call(hal, op="join", words=made7["link"], into=str(hal_into), name="Hal")
        call(lead, op="admit", invite=made7["invite"], match=False)
        at(hal)
        held = team.load_device_file()
        held["joining"][hal_asked["invite"]]["expires"] = "2020-01-01T00:00:00+00:00"
        team.save_device_file(held)
        hal_said = refused(lambda: call(dict(hal, root=hal_into), op="joined", invite=hal_asked["invite"]))
        check("433: an invite that lapsed after They differ ends the join the same way: said, the project taken away "
              "and the empty folder he named left there with nothing in it",
              hal_said == i18n.t("team.refused.invite_expired") and hal_into.is_dir() and not list(hal_into.iterdir())
              and roots(hal) == [], hal_said)

        # 11. a lead and a project with long names in a script of four bytes a character: the offer keeps its list
        # of participants (the project's name cut to fit), and one size, as for short names
        dev = team.new_device()
        secret = b"0123456789abcdef"
        body = {"kind": "invite", "device": team.public(dev), "lead": "L" * 16, "from": "\U0001d4d0" * 60, "own": False,
                "expires": "2026-12-01T00:00:00+00:00", "team_digest": team.team_digest(secret, "t"),
                "project": "\U0001d4d1" * 80, "method": "ipa"}
        long_offer = team.offer_body(dev, body, secret, [{"folder": f"P{n}", "made": ""} for n in range(30)])
        short_offer = team.offer_body(dev, dict(body, project="Dogs", **{"from": "Ada"}), secret,
                                      [{"folder": f"P{n}", "made": ""} for n in range(30)])
        check("433: an invite's offer from a lead and a project with long names in a script of four bytes a character "
              "still lists its participants and is one size, the project's name cut to fit",
              len(long_offer.get("participants") or []) == team.LIST_N and len(short_offer.get("participants") or []) == team.LIST_N
              and len(team.canon(long_offer)) == len(team.canon(short_offer)) == team.OFFER_BYTES
              and 0 < len(long_offer.get("project") or "") < 80 and short_offer.get("project") == "Dogs",
              str(len(team.canon(long_offer))))

        # 12. a project gone from the relay says so in Invite and They match, not the general refusal (review of
        # relayfix3, L5)
        class Gone(Exception):
            status, error = 404, "no project"

        class Other(Exception):
            status, error = 404, "no blob"

        gone = team.relay_refusal(Gone())
        check("433: the relay's answer that it has no project is said as the project no longer being on the relay, "
              "where any other refusal keeps the general line",
              gone.code == "relay_gone" and str(gone) == i18n.t("team.refused.relay_gone")
              and team.relay_refusal(Other()).code == "relay_refused", str(gone))

        # 13. on a shared folder the welcome and the closing line are two files that a sync may bring in either
        # order: the closing line seen alone ends nothing, the welcome then lands and the join completes with
        # nothing deleted; seen alone a minute on, it ends the join and the project goes (lowsW, review)
        transport.OVERRIDE = None
        ft.POLL = 0.05
        shared2 = scratch / "team-433-shared2" / "Dogs"
        shutil.rmtree(scratch / "team-433-shared2", ignore_errors=True)
        shared2.mkdir(parents=True)
        glead = install(scratch, "glead", "Dogs by sync")
        call(glead, op="on", name="Gil", route="folder", folder=str(shared2))
        gmade = call(glead, op="invite")
        gem = install(scratch, "gem")
        gem_into = base / "Gem's copy"
        gasked = call(gem, op="join", words=gmade["link"], into=str(gem_into), name="Gem", folder=str(shared2))
        call(glead, op="admit", invite=gmade["invite"], match=True)
        files = sorted(p for p in shared2.rglob("*.join"))
        welcome_file = files[-2]
        held_back = welcome_file.with_name(welcome_file.name + ".away")
        welcome_file.rename(held_back)
        early = call(dict(gem, root=gem_into), op="joined", invite=gasked["invite"])
        still_there = gem_into.is_dir() and roots(gem) == [str(gem_into.resolve())] and device_there(gem)
        held_back.rename(welcome_file)
        late = call(dict(gem, root=gem_into), op="joined", invite=gasked["invite"])
        check("433: on a shared folder a closing line that comes before the lead's welcome ends nothing: the join "
              "waits, the project and keys stay, and when the welcome lands the join completes",
              early["joined"] is False and still_there and late["joined"] is True and gem_into.is_dir()
              and (team.read_team(gem_into) or {}).get("on") is True, json.dumps([early, late.get("joined")]))
        gwen = install(scratch, "gwen")
        gwen_into = base / "Gwen's copy"
        gmade2 = call(glead, op="invite")
        gwen_asked = call(gwen, op="join", words=gmade2["link"], into=str(gwen_into), name="Gwen", folder=str(shared2))
        call(glead, op="cancel", invite=gmade2["invite"])
        first = call(dict(gwen, root=gwen_into), op="joined", invite=gwen_asked["invite"])
        at(gwen)
        held = team.load_device_file()
        held["joining"][gwen_asked["invite"]]["closed_seen"] = "2020-01-01T00:00:00+00:00"
        team.save_device_file(held)
        final = refused(lambda: call(dict(gwen, root=gwen_into), op="joined", invite=gwen_asked["invite"]))
        check("433: a closing line seen alone on a shared folder a minute apart ends the join as the relay's does, "
              "and the project it made is taken away", first["joined"] is False
              and final == i18n.t("team.refused.invite_closed") and not gwen_into.exists(), final)
        transport.OVERRIDE = lambda dev, data: transport.Loopback(dev.get("id") or "", hub=hub)
        ft.POLL = kept[5]
    finally:
        (server_mod.CONFIG_PATH, server_mod.ROOT_OVERRIDE, team.DEVICE_PATH, transport.OVERRIDE, env, ft.POLL,
         home, profile) = kept
        if env is not None:
            os.environ[transport.ENV] = env
        if home is not None:
            os.environ["HOME"] = home
        if profile is None:
            os.environ.pop("USERPROFILE", None)
        else:
            os.environ["USERPROFILE"] = profile
