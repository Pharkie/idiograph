"""Area 437: the first invite of a project is where its Send through is chosen (inviteroute, 20 November 2026,
Adam's ruling that evening). The page asks how the project's updates travel before it makes the link, and what it asks
is Project settings' own Send through, written by the same ops. This checks, on scratch installs, what the server
does for that: `show` says `first_invite` for a lead who has made no invite and has no one else on the team, the
folder route chosen with the first turning on or set before the first invite writes the route and the folder, makes
nothing on the relay and sends the invite through the folder, the relay as before, the flag gone once an invite has
been made even if it is cancelled, never there for a member or for a team with others, and `show` on a project that
Working together never started writing nothing. The card's Cancel and its wording are the page's and are looked at
in the review shots. Every fixture is invented."""
from __future__ import annotations

import json
import os
import shutil
from pathlib import Path

from . import support
from .support import check
from .a431_team_start import install, project_files


def test_invite_route(scratch: Path):
    print("\n437. The first invite chooses the project's Send through: the first-invite flag, the folder route written "
          "with nothing on the relay, the relay as before, never asked again (inviteroute)")
    import folder_transport as ft
    import idiograph_routes as routes
    import server as server_mod
    import team
    import transport

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

    try:
        # 1. the relay chosen: asked at the first invite, never after
        lead = install(scratch, "route-lead", "Reed bed counters", ("Wren",))
        before = project_files(lead["root"])
        shown = call(lead, op="show")
        check("437: a project Working together never started shows off, and showing it writes nothing",
              shown["team"] == {"on": False} and project_files(lead["root"]) == before)
        call(lead, op="on", name="Ada", route="relay")
        first = call(lead, op="show")["team"]
        check("437: a lead alone with no invite made is asked the route at the first invite", first["first_invite"] is True
              and first["route"] == "relay", str(first.get("first_invite")))
        made = call(lead, op="invite")
        after = call(lead, op="show")["team"]
        at(lead)
        check("437: once an invite is made the question is not asked again, team.json records it, and the relay stays "
              "the route", after["first_invite"] is False and team.read_team(lead["root"])["invited"] is True
              and after["route"] == "relay" and made["link"], str(after.get("first_invite")))
        call(lead, op="cancel", invite=made["invite"])
        check("437: a cancelled first invite does not bring the question back",
              call(lead, op="show")["team"]["first_invite"] is False)
        call(lead, op="invite")
        check("437: a second invite is made with nothing asked",
              call(lead, op="show")["team"]["first_invite"] is False and len(call(lead, op="show")["team"]["invites"]) == 1)

        # 2. the folder chosen at the first invite, Working together already on through the relay
        transport.OVERRIDE = None
        ft.POLL = 0.05
        shared = scratch / "team-437-shared" / "OneDrive" / "Reeds"
        shutil.rmtree(scratch / "team-437-shared", ignore_errors=True)
        shared.mkdir(parents=True)
        mid = install(scratch, "route-mid", "Reed bed counters, two", ("Wren",))
        call(mid, op="on", name="Bea")
        flag = call(mid, op="show")["team"]["first_invite"]
        call(mid, op="set", route="folder", folder=str(shared))
        got = call(mid, op="invite")
        view = call(mid, op="show")["team"]
        at(mid)
        data = team.read_team(mid["root"])
        check("437: choosing the folder at the first invite sets the project's route and folder as Project settings "
              "does, makes no project on the relay, and the invite goes through the folder and says so",
              flag is True and view["route"] == "folder" and view["folder"] == str(shared) and not view["on_relay"]
              and "relay" not in (data.get("roster") or {}) and "via=folder" in got["link"] and view["first_invite"] is False,
              f"{view.get('route')} {got.get('link')}")

        # 3. the folder chosen with the first turning on, the page's way when Working together was off
        off = install(scratch, "route-off", "Reed bed counters, three", ("Wren",))
        call(off, op="on", name="Cal", route="folder", folder=str(shared))
        offview = call(off, op="show")["team"]
        offmade = call(off, op="invite")
        at(off)
        check("437: turning on with the folder route and its folder writes both, first_invite still true until the "
              "invite is made, and nothing is made on the relay",
              offview["route"] == "folder" and offview["folder"] == str(shared) and offview["first_invite"] is True
              and not offview["on_relay"] and "via=folder" in offmade["link"]
              and "relay" not in (team.read_team(off["root"]).get("roster") or {}))

        # 4. never asked of a team with others, and the dry run of an invite leaves the question as it was
        transport.OVERRIDE = lambda dev, data: transport.Loopback(dev.get("id") or "", hub=hub)
        lone = install(scratch, "route-dry", "Reed bed counters, four", ("Wren",))
        call(lone, op="on", name="Dee")
        dry = call(lone, op="invite", dry_run=True)
        check("437: an invite's dry run writes nothing and leaves the first invite still to ask",
              dry["dry_run"] is True and call(lone, op="show")["team"]["first_invite"] is True
              and not (team.read_team(lone["root"]) or {}).get("invited"))
        joiner = install(scratch, "route-joiner", "Reed bed counters, Eli's")
        inv = call(lone, op="invite")
        call(joiner, op="join", words=inv["words"], name="Eli")
        call(lone, op="admit", invite=inv["invite"], match=True)
        call(joiner, op="joined", invite=inv["invite"])
        member = call(joiner, op="show")["team"]
        check("437: a member and a team with others are never asked", member["first_invite"] is False
              and call(lone, op="show")["team"]["first_invite"] is False)

        # 5. a team kept alone (on, then off): `on` keeps its route, the choice is then set as Project settings sets
        #    it, and the first invite goes through the folder with no project on the relay; the off project's start
        #    rows say the kept route and folder for the card to open at (review H1, H2)
        transport.OVERRIDE = None
        keptd = install(scratch, "route-kept", "Reed bed counters, five", ("Wren",))
        call(keptd, op="on", name="Fay", route="relay")
        call(keptd, op="off")
        said = call(keptd, op="show")
        call(keptd, op="on", name="Fay", route="folder", folder=str(shared))
        after_on = call(keptd, op="show")["team"]
        call(keptd, op="set", route="folder", folder=str(shared))
        kmade = call(keptd, op="invite")
        kview = call(keptd, op="show")["team"]
        check("437: a team kept alone says its route and folder in the off project's start rows, turning it on keeps "
              "that route, and set then writes the folder route before the first invite, which makes no relay project",
              said["start"].get("route") == "relay" and after_on["route"] == "relay" and kview["route"] == "folder"
              and kview["folder"] == str(shared) and not kview["on_relay"] and "via=folder" in kmade["link"],
              f"{said.get('start')} {after_on.get('route')} {kview.get('route')}")

        # 6. one rule for the first invite: only a team never more than one member on one computer, with nothing
        #    kept that says it has been used (review H3, H4)
        at(keptd)
        base = team.read_team(keptd["root"])
        two = json.loads(json.dumps(base))
        two["roster"]["members"][0]["devices"].append({"id": "second", "name": "Other", "added": "x"})
        fresh = install(scratch, "route-fresh", "Reed bed counters, six", ("Wren",))
        call(fresh, op="on", name="Gus", route="relay")
        at(fresh)
        plain = team.read_team(fresh["root"])
        def with_roster(**extra):
            data = json.loads(json.dumps(plain))
            data["roster"].update(extra.pop("roster", {}))
            data.update(extra)
            return data
        check("437: the first invite is asked only of a team that has never been more than one member on one "
              "computer: a second computer of the lead's, a later epoch, an asked change, a stopped member, a "
              "project already on the relay, a recorded invite or one the device remembers each end the question",
              team.first_invite_of(plain, {}) is True
              and team.first_invite_of(two, {}) is False
              and team.first_invite_of(with_roster(roster={"epoch": 2}), {}) is False
              and team.first_invite_of(with_roster(asked=[{"x": 1}]), {}) is False
              and team.first_invite_of(with_roster(stopped={"m": True}), {}) is False
              and team.first_invite_of(with_roster(roster={"relay": {"project": "p"}}), {}) is False
              and team.first_invite_of(with_roster(invited=True), {}) is False
              and team.first_invite_of(plain, {"invited": True}) is False
              and team.first_invite_of(plain, {"invites": {"a": {}}}) is False)

        # 7. a folder that is not there is refused before anything is written, turning on and set alike (review M5)
        gone = scratch / "team-437-shared" / "not there"
        nope = install(scratch, "route-nope", "Reed bed counters, seven", ("Wren",))
        wrote = project_files(nope["root"])
        refusals = []
        for body in ({"op": "on", "name": "Hal", "route": "folder", "folder": str(gone), "folder_must_exist": True},):
            try:
                call(nope, **body)
                refusals.append("")
            except Exception as exc:  # noqa: BLE001
                refusals.append(str(exc))
        call(nope, op="on", name="Hal", route="relay")
        before_set = project_files(nope["root"])
        try:
            call(nope, op="set", route="folder", folder=str(gone), folder_must_exist=True)
            refusals.append("")
        except Exception as exc:  # noqa: BLE001
            refusals.append(str(exc))
        import i18n
        check("437: a shared folder that is not there is refused with the folder-missing line before anything is "
              "written, when turning on and when setting the route",
              refusals == [i18n.t("team.page.folder_missing")] * 2 and project_files(nope["root"]) == before_set
              and wrote != before_set, str(refusals))

        # 8. a first invite the relay refuses is still recorded as attempted, so choosing the folder next is never
        #    asked over a project already made for the relay (review M6)
        class Refuses:
            def send(self, *a, **k):
                exc = RuntimeError("busy")
                exc.status = 429
                exc.error = "slow down"
                raise exc

        transport.OVERRIDE = lambda dev, data: Refuses()
        bad = install(scratch, "route-bad", "Reed bed counters, eight", ("Wren",))
        call(bad, op="on", name="Ida", route="relay")
        asked_before = call(bad, op="show")["team"]["first_invite"]
        try:
            call(bad, op="invite")
            refused_line = ""
        except Exception as exc:  # noqa: BLE001
            refused_line = str(exc)
        check("437: a relay refusal of the first invite leaves it recorded as attempted, never asked again",
              asked_before is True and refused_line and call(bad, op="show")["team"]["first_invite"] is False,
              refused_line)
    finally:
        (server_mod.CONFIG_PATH, server_mod.ROOT_OVERRIDE, team.DEVICE_PATH, transport.OVERRIDE, env, ft.POLL) = kept
        if env is not None:
            os.environ[transport.ENV] = env
