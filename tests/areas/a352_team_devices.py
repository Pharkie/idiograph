"""Area 352: Working together's members and computers (wtdevices, 9 November 2026, build 8 of the design Adam chose
on 8 November). Three scratch installs in one process, each its own settings folder, device file and project,
sending through the loopback transport: the lead, a member, and the member's second computer. What matters: a
second computer of a member who is not the lead joins with the six digits and opens the team's messages at once,
and goes on the list when the lead's install takes the asking in. A lost computer removed makes a new key, which
the member's other computer opens and the removed one cannot. The lead removing someone's only computer, or the one
he is on, is refused. Make lead moves the signing, so the old lead's list is refused afterwards and the new lead's
taken. Every fixture is invented."""
from __future__ import annotations

import json
import shutil
from pathlib import Path

from .support import check


def install(scratch: Path, name: str, project: str) -> dict:
    """A scratch install: its settings file, beside which its device file goes, and one project of its own."""
    home = scratch / f"team-352-{name}"
    shutil.rmtree(home, ignore_errors=True)
    root = home / project
    root.mkdir(parents=True)
    (root / "idiograph-project.json").write_text(json.dumps({"name": project}), encoding="utf-8")
    config = home / "config.json"
    config.write_text(json.dumps({"projects": [{"root": str(root)}]}), encoding="utf-8")
    return {"home": home, "root": root, "config": config}


def test_team_devices(scratch: Path):
    print("\n352. Working together's members and computers: a member's second computer added and reading at once, a "
          "lost computer removed with a new key it cannot open, Make lead moving the signing (wtdevices)")
    import i18n
    import idiograph_routes as routes
    import server as server_mod
    import team
    import team_sync
    import transport
    from workbook import WorkbookError

    ada = install(scratch, "ada", "Pond dipping")
    bo = install(scratch, "bo", "Pond dipping, Bo's copy")
    bo2 = install(scratch, "bo2", "Pond dipping, Bo's laptop")
    kept = (server_mod.CONFIG_PATH, server_mod.ROOT_OVERRIDE, team.DEVICE_PATH, transport.OVERRIDE)
    hub = transport.Hub()
    transport.OVERRIDE = lambda dev, data: transport.Loopback(dev.get("id") or "", hub=hub)

    def at(who):
        server_mod.CONFIG_PATH = who["config"]
        server_mod.ROOT_OVERRIDE = None
        team.DEVICE_PATH = None

    def call(who, **body):
        at(who)
        return routes.api_team(dict(body, root=str(who["root"])))

    def refused(who, **body):
        try:
            call(who, **body)
            return ""
        except WorkbookError as exc:
            return str(exc)

    def held(who):
        at(who)
        data = team.read_team(who["root"])
        return data, team.device(), team.project_keys(data["team"])

    def send(who, text):
        """A message from this install to the team, sealed under the newest key it holds."""
        data, dev, keys = held(who)
        epoch = max(keys)
        return team.seal_envelope(data["team"], epoch, keys[epoch], dev, data["member"], team.next_seq(data["team"]),
                                  "comment", {"text": text})

    def opens(who, raw):
        data, _dev, keys = held(who)
        try:
            return team.open_envelope(raw, data["roster"], keys)["body"]["text"]
        except team.TeamError as exc:
            return exc.code

    try:
        # Ada leads, Bo joins
        call(ada, op="on", name="Ada")
        made = call(ada, op="invite")
        call(bo, op="join", words=made["words"], name="Bo")
        call(ada, op="admit", invite=made["invite"], match=True)
        call(bo, op="joined", invite=made["invite"])

        # 1. Bo, not the lead, adds his laptop: the same pairing, read at once, on the list once Ada's install takes it
        own = call(bo, op="invite", own=True)
        joining = call(bo2, op="join", words=own["link"], name="Bo")
        answered = call(bo, op="answers", invite=own["invite"])
        call(bo, op="admit", invite=own["invite"], match=True)
        came = call(bo2, op="joined", invite=own["invite"])
        waiting = call(bo, op="show")["team"]["asked"]
        from_ada = send(ada, "The newts are back")
        before_on = opens(bo2, from_ada)
        took = call(ada, op="take")
        bo_people = [p for p in took["team"]["people"] if p["name"] == "Bo"][0]
        check("352: a member who is not the lead adds a computer of his own with the six digits on both screens, it "
              "opens the team's messages at once, and Ada's install, taking the asking in, puts it on Bo's row",
              joining["code"] == answered["code"] and answered["own"] and came["joined"]
              and len(waiting) == 1 and before_on == "The newts are back"
              and bo_people["computers"] == 2 and any(c for c in took["changes"]),
              json.dumps({"opened": before_on, "computers": bo_people["computers"], "asked": waiting}))
        call(bo, op="take")
        call(bo2, op="take")
        from_laptop = send(bo2, "Frogspawn by the reeds")
        check("352: once on the list, the laptop's own messages open on the lead's install, and Bo's waiting line goes",
              opens(ada, from_laptop) == "Frogspawn by the reeds" and call(bo, op="show")["team"]["asked"] == [],
              opens(ada, from_laptop))

        # 2. Bo's laptop is lost: removed from his other computer, a new key the laptop cannot open
        at(ada)
        ada_dev = team.device()
        bo_dev = held(bo)[1]
        laptop = held(bo2)[1]
        call(bo, op="remove", computer=laptop["id"])
        # taken in by the server's own loop, team_sync's, which reads every kind (landwt), not by team take
        at(ada)
        looked = team_sync.sync(ada["root"])
        at(bo)
        team_sync.sync(bo["root"])
        call(bo2, op="take")
        epochs = {"ada": max(held(ada)[2]), "bo": max(held(bo)[2]), "laptop": max(held(bo2)[2])}
        after = send(ada, "The heron took two")
        check("352: Bo removes his lost laptop from his other computer, Ada's install makes epoch 2's key, Bo's "
              "computer opens what is sent under it and the laptop cannot",
              epochs == {"ada": 2, "bo": 2, "laptop": 1} and opens(bo, after) == "The heron took two"
              and opens(bo2, after) == "no_key", json.dumps(epochs))
        check("352: the asking is taken in by the server's loop on the lead's computer, as team take takes it",
              looked.get("taken") == ["devices"], json.dumps(looked))
        late = send(bo2, "Still here")
        check("352: what the removed laptop sends after is refused on the lead's install",
              opens(ada, late) in ("no_key", "not_on_roster"), opens(ada, late))
        bo_row = [p for p in call(ada, op="show")["team"]["people"] if p["name"] == "Bo"][0]
        check("352: Bo's row lists one computer again, the one he kept",
              [d["id"] for d in bo_row["devices"]] == [bo_dev["id"]], json.dumps(bo_row))

        # 3. the lead cannot remove the computer he is on, nor someone's only computer
        here = refused(ada, op="remove", computer=ada_dev["id"])
        only = refused(ada, op="remove", computer=bo_dev["id"])
        check("352: the lead removing the computer he is on is refused, and so is a member's only computer",
              here == i18n.t("team.refused.this_computer")
              and only == i18n.t("team.refused.last_computer", name="Bo"), f"{here} | {only}")

        # 4. Make lead: the signing moves to Bo, the old lead's list refused after, the new lead's taken
        dry = call(ada, op="lead", member="Bo", dry_run=True)
        call(ada, op="lead", member="Bo")
        call(bo, op="take")
        bo_view = call(bo, op="show")["team"]
        stale = refused(ada, op="invite")
        call(bo, op="set", gets_owner="Bo")
        call(ada, op="take")
        ada_view = call(ada, op="show")["team"]
        at(ada)
        a_data = team.read_team(ada["root"])
        forged = team.sign_roster(team.device(), dict(a_data["roster"], n=a_data["roster"]["n"] + 1, gets_owner="x"))
        at(bo)
        try:
            team.take_roster(bo["root"], forged)
            forged_said = ""
        except team.TeamError as exc:
            forged_said = exc.code
        check("352: Make lead hands the list to Bo: Bo's install takes it and leads, Ada's can no longer invite, a "
              "list Ada signs afterwards is refused, and the one Bo signs is taken on Ada's install",
              dry["changes"] and bo_view["you_lead"] and not ada_view["you_lead"]
              and stale == i18n.t("team.refused.lead_only") and forged_said == "roster_not_lead"
              and ada_view["gets_owner"] == bo_view["member"],
              json.dumps({"forged": forged_said, "stale": stale}))
        at(ada)
        history = [h["op"] for h in json.loads((ada["root"] / "idiograph-history.json").read_text(
            encoding="utf-8"))["history"]]
        check("352: each change goes into the project's History, the dry run none",
              history.count("team lead") == 1 and "team take" in history, str(history))
    finally:
        (server_mod.CONFIG_PATH, server_mod.ROOT_OVERRIDE, team.DEVICE_PATH, transport.OVERRIDE) = kept
