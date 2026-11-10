"""Area 341: Working together's keys and pairing (wtkeys, 8 November 2026, the first build of the design Adam chose
that evening about 19:10). Two scratch installs in one process, each its own settings folder, device file and
project, sending through the loopback transport. What matters: a device's keys are made once and kept, a message
seals and opens, a tampered envelope and a roster not signed by the lead are refused, an invite answered and matched
leaves both installs with the same project key after both read the same six digits, a used invite is refused a
second time, and while Working together is off nothing is shown or written. Every fixture is invented."""
from __future__ import annotations

import json
import os
import shutil
from pathlib import Path

from . import support
from .support import check


def install(scratch: Path, name: str, project: str) -> dict:
    """A scratch install: its settings file, beside which its device file goes, and one project of its own."""
    home = scratch / f"team-341-{name}"
    shutil.rmtree(home, ignore_errors=True)
    root = home / project
    root.mkdir(parents=True)
    (root / "idiograph-project.json").write_text(json.dumps({"name": project}), encoding="utf-8")
    config = home / "config.json"
    config.write_text(json.dumps({"projects": [{"root": str(root)}]}), encoding="utf-8")
    return {"home": home, "root": root, "config": config}


def test_team_keys(scratch: Path):
    print("\n341. Working together's keys and pairing: device keys made once, seal and open, a tampered envelope and a "
          "roster not the lead's refused, invite then join on loopback, a used invite refused, nothing while off (wtkeys)")
    import i18n
    import idiograph_routes as routes
    import server as server_mod
    import team
    import transport
    from workbook import WorkbookError

    lead = install(scratch, "lead", "Allotment growers")
    joiner = install(scratch, "joiner", "Allotment growers, a copy")
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

    try:
        # 1. off: shown as off, and nothing written anywhere
        before = {p.name for p in lead["home"].rglob("*")}
        shown = call(lead, op="show")["team"]
        dry = call(lead, op="on", name="Ada", dry_run=True)
        check("341: while Working together is off the section is off alone, a dry run of on says what it would do, "
              "and no team.json, no device file and no History are written",
              shown == {"on": False} and dry["changes"] and dry["team"] == {"on": False}
              and {p.name for p in lead["home"].rglob("*")} == before, json.dumps(shown))

        # 2. on: keys made once and kept, the file readable by its owner alone
        call(lead, op="on", name="Ada", route="relay")
        dev_file = lead["home"] / team.DEVICE_FILE
        first = json.loads(dev_file.read_text(encoding="utf-8"))["device"]
        call(lead, op="off")
        call(lead, op="on", name="Ada")
        again = json.loads(dev_file.read_text(encoding="utf-8"))["device"]
        mode = oct(os.stat(dev_file).st_mode & 0o777)
        check("341: turning on makes this computer's Ed25519 and X25519 keys once, in team-device.json beside the "
              "settings, mode 600, kept through off and on again, its id the first 16 bytes of SHA-256 of its "
              "signing key",
              first == again and first["id"] == team.device_id(team.unb64(first["sign_pub"]))
              and (mode == "0o600" or os.name == "nt") and (lead["root"] / team.FILE).is_file()
              and not (lead["root"] / team.DEVICE_FILE).exists(), mode)

        # 3. seal and open, and a tampered envelope refused
        at(lead)
        data = team.read_team(lead["root"])
        dev = team.device()
        key = team.project_key(data["team"], 1)
        raw = team.seal_envelope(data["team"], 1, key, dev, data["member"], 1, "comment", {"text": "The bees came back"})
        opened = team.open_envelope(raw, data["roster"], {1: key})
        env = json.loads(raw)
        sealed = bytearray(team.unb64(env["sealed"]))
        sealed[40] ^= 1
        bent = json.dumps(dict(env, sealed=team.b64(bytes(sealed)))).encode()
        moved = json.dumps(dict(env, seq=2)).encode()
        refusals = []
        for bad in (bent, moved):
            try:
                team.open_envelope(bad, data["roster"], {1: key})
                refusals.append("")
            except team.TeamError as exc:
                refusals.append(exc.code)
        check("341: a message sealed under the project key opens to its body, signed by its device, and an envelope "
              "with one bit of its seal changed, or its number changed, is refused as tampered",
              opened["body"] == {"text": "The bees came back"} and opened["device"] == dev["id"]
              and len(team.unb64(env["sealed"])) == 24 + 4096 + 16 and refusals == ["tampered", "tampered"],
              str(refusals))

        # 4. invite, answer, match: both installs with the same key and the same six digits
        made = call(lead, op="invite")
        joined = call(joiner, op="join", words=made["link"], name="Bo")
        answered = call(lead, op="answers", invite=made["invite"])
        call(lead, op="admit", invite=made["invite"], match=True)
        done = call(joiner, op="joined", invite=made["invite"])
        at(lead)
        lead_team = team.read_team(lead["root"])
        lead_key = team.project_key(lead_team["team"], 1)
        at(joiner)
        joiner_team = team.read_team(joiner["root"])
        joiner_key = team.project_key(joiner_team["team"], 1)
        check("341: an invite's twelve words and link answered from a second install show both the same six digits, "
              "and They match leaves both with the same team, the same roster and the same project key",
              len(made["words"].split()) == 12 and made["link"].endswith("#" + made["words"].replace(" ", "-"))
              and answered["answered"] and answered["name"] == "Bo" and joined["code"] == answered["code"]
              and len(joined["code"]) == 7 and done["joined"] and lead_key and lead_key == joiner_key
              and joiner_team["team"] == lead_team["team"] and joiner_team["roster"] == lead_team["roster"]
              and [p["name"] for p in done["team"]["people"]] == ["Ada", "Bo"],
              json.dumps({"code": [joined.get("code"), answered.get("code")], "joined": done.get("joined")}))
        at(lead)
        held = json.loads((lead["root"] / "idiograph-history.json").read_text(encoding="utf-8"))
        history = [h["op"] for h in held["history"]]
        check("341: each change goes into the project's History, the dry run none",
              history == ["team on", "team off", "team on", "team invite", "team admit"], str(history))

        # 5. a second join with a used invite refused, on both sides
        third = install(scratch, "third", "Allotment growers, another copy")
        try:
            call(third, op="join", words=made["words"], name="Cy")
            second = ""
        except WorkbookError as exc:
            second = str(exc)
        try:
            call(lead, op="admit", invite=made["invite"], match=True)
            again = ""
        except WorkbookError as exc:
            again = str(exc)
        check("341: a second join with an invite already used is refused, and so is a second match of it",
              second == again == i18n.t("team.refused.invite_used"), f"{second} | {again}")

        # 6. a roster not signed by the lead refused, the lead's taken
        at(joiner)
        jdev = team.device()
        forged = dict(joiner_team["roster"], n=joiner_team["roster"]["n"] + 1, lead=joiner_team["member"])
        forged = team.sign_roster(jdev, forged)
        at(lead)
        try:
            team.take_roster(lead["root"], forged)
            forged_said = ""
        except team.TeamError as exc:
            forged_said = exc.code
        call(lead, op="remove", member="Bo")
        at(lead)
        newer = team.read_team(lead["root"])["roster"]
        at(joiner)
        taken = team.take_roster(joiner["root"], newer)
        check("341: a roster signed by a member's device, naming him lead, is refused, and the lead's next roster, "
              "which removes him and makes epoch 2's key, is taken but gives him no key for it",
              forged_said == "roster_not_lead" and newer["epoch"] == 2 and taken["epoch"] == 2
              and team.project_key(joiner_team["team"], 2) is None, forged_said)
    finally:
        (server_mod.CONFIG_PATH, server_mod.ROOT_OVERRIDE, team.DEVICE_PATH, transport.OVERRIDE) = kept
