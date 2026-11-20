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
