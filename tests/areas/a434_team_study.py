"""Area 434: the study's settings travel with the copy and keep in step (teamsettings, 20 November 2026, Adam's ruling
that day about 01:05). Two scratch installs in one process, each its own settings folder, device file and project,
paired over the loopback transport as area 349 pairs them.

What matters: the first full copy brings the lead's name, research question, method, demographics and each
participant's profile with its picture; a later change of the lead's reaches the member; a member's change to a
profile reaches the lead and comes back, and on a conflict the lead's word wins; the member's own reflexivity,
interviewer name and PET labels never leave nor change, and the lead's never arrive; a picture changed travels once;
a dry run sends nothing and writes nothing; and a member that has the lead's versions but never the study (a team
from before this build) asks once and is sent the whole study. Every fixture is invented."""
from __future__ import annotations

import hashlib
import json
import shutil
from pathlib import Path

from . import support
from .support import check, skip

PEOPLE = ("Wren", "Fern")


def install(scratch: Path, name: str, project: dict, people=()) -> dict:
    home = scratch / f"team-434-{name}"
    shutil.rmtree(home, ignore_errors=True)
    root = home / "Hedgerow"
    root.mkdir(parents=True)
    (root / "idiograph-project.json").write_text(json.dumps(project), encoding="utf-8")
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


def read(who: dict) -> dict:
    return json.loads((who["root"] / "idiograph-project.json").read_text(encoding="utf-8"))


def write(who: dict, **changed) -> None:
    data = read(who)
    for key, value in changed.items():
        if value is None:
            data.pop(key, None)
        else:
            data[key] = value
    (who["root"] / "idiograph-project.json").write_text(json.dumps(data), encoding="utf-8")


def sha(path: Path) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def test_team_study(scratch: Path):
    print("\n434. Working together: the study's settings travel with the copy and keep in step, each person's own "
          "stay their own (teamsettings)")
    try:
        import cryptography  # noqa: F401
    except ImportError:
        return skip("434: the study's settings travel", "no cryptography in this Python")
    import idiograph_routes as routes
    import project_history as hist_mod
    import server as server_mod
    import team
    import team_study
    import team_sync
    import trajectories as traj_mod
    import transport

    demographics = [{"name": "Age range", "kind": "list", "values": [{"word": "30 to 39", "colour": 2}]}]
    lead = install(scratch, "lead", {
        "name": "Hedgerow walkers", "research_question": "How do walkers live with hedgerows?", "method": "ipa",
        "demographics": demographics, "reflexivity": "Ada's own positioning.", "interviewer": "Ada Lane",
        "participants": {"P1 - Wren": {"label": "The early riser", "portrait": "Wren walks at dawn.",
                                       "picture": "Wren.png", "values": {"Age range": "30 to 39"}},
                         "P2 - Fern": {"label": "The dog walker", "picture": "set:peep07"}}}, PEOPLE)
    pictures = lead["root"] / "pictures"
    pictures.mkdir()
    (pictures / "Wren.png").write_bytes(traj_mod.png_write(4, 4, bytearray([200, 40, 40, 255] * 16)))
    member = install(scratch, "member", {"name": "Bo's copy", "method": "ta", "reflexivity": "Bo's own positioning.",
                                         "interviewer": "Bo Moss", "pet_labels": "numbers"})
    kept = (server_mod.CONFIG_PATH, server_mod.ROOT_OVERRIDE, team.DEVICE_PATH, transport.OVERRIDE, team_sync.WAIT,
            team_study.packed)
    hub = transport.Hub()
    transport.OVERRIDE = lambda dev, data: transport.Loopback(dev.get("id") or "", hub=hub)
    went = []

    def packed(files):
        went.append({name: raw for name, raw in files.items()})
        return kept[5](files)

    team_study.packed = packed

    def at(who):
        server_mod.CONFIG_PATH = who["config"]
        server_mod.ROOT_OVERRIDE = None
        team.DEVICE_PATH = None

    def call(who, **body):
        at(who)
        return routes.api_team(dict(body, root=str(who["root"])))

    def everything_sent() -> bytes:
        return b"".join(raw for one in went for raw in one.values())

    def state(who) -> dict:
        at(who)
        return team_sync.load_state(who["root"]).get("study") or {}

    try:
        call(lead, op="on", name="Ada")
        made = call(lead, op="invite")
        call(member, op="join", words=made["link"], name="Bo")
        call(lead, op="admit", invite=made["invite"], match=True)
        call(member, op="joined", invite=made["invite"])
        call(lead, op="set", owners={"P2 - Fern": "Bo"})
        team_sync.WAIT = 0

        # 1. the first full copy brings the study's settings, and each person's own stay where they are
        call(lead, op="send")
        call(member, op="send")
        got, had = read(member), read(lead)
        check("434: the first copy brings the lead's name, research question, method, demographics and each "
              "participant's profile with its picture",
              got.get("name") == "Hedgerow walkers" and got.get("research_question") == had["research_question"]
              and routes.method_of(got) == "ipa"
              and [(c["name"], [v["word"] for v in c["values"]]) for c in got.get("demographics") or []]
              == [("Age range", ["30 to 39"])]
              and got.get("participants") == had["participants"]
              and (member["root"] / "pictures" / "Wren.png").is_file()
              and sha(member["root"] / "pictures" / "Wren.png") == sha(pictures / "Wren.png"),
              json.dumps({"got": got, "sent": len(went)}))
        check("434: the member's reflexivity, interviewer name and PET labels are his own after the copy, and the "
              "lead's reflexivity and interviewer name never left her computer",
              got.get("reflexivity") == "Bo's own positioning." and got.get("interviewer") == "Bo Moss"
              and got.get("pet_labels") == "numbers" and b"Ada's own positioning" not in everything_sent()
              and b"Ada Lane" not in everything_sent(), json.dumps(got))
        at(member)
        lines = [c for h in hist_mod.load(member["root"]) for c in h.get("changes") or []]
        check("434: the member's project History says the study's settings came in from Ada",
              any(line.startswith("Ada's settings for the study came in") for line in lines), json.dumps(lines))

        # 2. a later change of the lead's reaches the member
        write(lead, research_question="How do walkers keep hedgerows?")
        people = read(lead)["participants"]
        people["P2 - Fern"]["label"] = "The night walker"
        write(lead, participants=people)
        call(lead, op="send")
        call(member, op="send")
        got = read(member)
        check("434: the lead's later change to the question and to a profile reaches the member",
              got.get("research_question") == "How do walkers keep hedgerows?"
              and got["participants"]["P2 - Fern"]["label"] == "The night walker"
              and got.get("reflexivity") == "Bo's own positioning.", json.dumps(got))

        # 3. the member's own settings never leave nor change
        before = len(went)
        write(member, reflexivity="Bo's positioning, written again.", interviewer="Bo M.")
        call(member, op="send")
        call(lead, op="send")
        check("434: the member's change to his reflexivity and interviewer name sends nothing, and the lead's stay "
              "her own", len(went) == before and read(lead).get("reflexivity") == "Ada's own positioning."
              and read(lead).get("interviewer") == "Ada Lane", json.dumps({"went": len(went) - before}))

        # 4. a member's change to a profile reaches the lead and comes back as the lead has it
        people = read(member)["participants"]
        people["P2 - Fern"]["portrait"] = "Fern walks her spaniel after work."
        write(member, participants=people)
        call(member, op="send")
        call(lead, op="send")
        call(member, op="send")
        check("434: a member's change to a participant's pen portrait reaches the lead, and the two stay in step",
              read(lead)["participants"]["P2 - Fern"].get("portrait") == "Fern walks her spaniel after work."
              and read(member)["participants"] == read(lead)["participants"]
              and read(member).get("interviewer") == "Bo M.", json.dumps(read(lead).get("participants")))

        # 5. a conflict: both change the question before either has the other's, and the lead's word wins
        write(member, research_question="Bo's question.")
        write(lead, research_question="Ada's question.")
        call(member, op="send")
        call(lead, op="send")
        call(member, op="send")
        call(lead, op="send")
        check("434: when the lead and a member both change the question, the lead's word wins on both computers",
              read(lead).get("research_question") == "Ada's question."
              and read(member).get("research_question") == "Ada's question.",
              json.dumps([read(lead).get("research_question"), read(member).get("research_question")]))

        # 6. a picture changed travels once
        people = read(lead)["participants"]
        (pictures / "Wren-2.png").write_bytes(traj_mod.png_write(4, 4, bytearray([40, 40, 200, 255] * 16)))
        people["P1 - Wren"]["picture"] = "Wren-2.png"
        write(lead, participants=people)
        before = len(went)
        call(lead, op="send")
        call(member, op="send")
        with_picture = [one for one in went[before:] if "pictures/Wren-2.png" in one]
        write(lead, research_question="Ada's question, once more.")
        before_again = len(went)
        call(lead, op="send")
        call(member, op="send")
        pictures_again = [name for one in went[before_again:] for name in one if name.startswith("pictures/")]
        check("434: a changed picture goes once with the study that names it, a later change carries no picture, and "
              "the member has it", len(with_picture) == 1 and not pictures_again
              and sha(member["root"] / "pictures" / "Wren-2.png") == sha(pictures / "Wren-2.png")
              and read(member)["participants"]["P1 - Wren"]["picture"] == "Wren-2.png"
              and read(member).get("research_question") == "Ada's question, once more.",
              json.dumps({"with": len(with_picture), "again": pictures_again}))

        # 7. a dry run sends nothing and writes nothing
        write(lead, research_question="Ada's question, not sent.")
        at(lead)
        sync_file = lead["root"] / ".idiograph-team" / "sync.json"
        was = (sync_file.read_bytes(), sum(len(box) for box in hub.boxes.values()), len(went))
        dry = call(lead, op="send", dry_run=True)
        check("434: a dry run of team send sends nothing and writes nothing",
              dry.get("dry_run") is True and was == (sync_file.read_bytes(), sum(len(b) for b in hub.boxes.values()),
                                                     len(went)), json.dumps({"dry": dry.get("dry_run")}))
        call(lead, op="send")
        call(member, op="send")

        # 8. a team from before: the member has the lead's versions but never the study, asks once, and has it all
        at(member)
        st = team_sync.load_state(member["root"])
        st.pop("study", None)
        team_sync.save_state(member["root"], st)
        write(member, name="Bo's copy", research_question=None, participants=None)
        (member["root"] / "pictures" / "Wren-2.png").unlink()
        call(member, op="send")
        asked = state(member).get("asked")
        call(lead, op="send")
        call(member, op="send")
        again = state(member).get("asked")
        call(member, op="send")
        check("434: a member with the lead's versions and no study asks once, is sent the whole study with every "
              "picture, and does not ask again",
              bool(asked) and asked == again and read(member).get("name") == "Hedgerow walkers"
              and read(member).get("research_question") == "Ada's question, not sent."
              and (member["root"] / "pictures" / "Wren-2.png").is_file()
              and read(member).get("reflexivity") == "Bo's positioning, written again.",
              json.dumps({"asked": asked, "got": read(member)}))

        # 9. a join from Home (teamjoin) makes the project with the lead's name and method only, and the study's
        # settings meet it on the first copy: question, demographics, profiles and their pictures
        cy_home = scratch / "team-434-cy"
        shutil.rmtree(cy_home, ignore_errors=True)
        cy_home.mkdir(parents=True)
        cy = {"home": cy_home, "root": cy_home / "Joined", "config": cy_home / "config.json"}
        cy["config"].write_text(json.dumps({"projects": [], "your_name": "Cy"}), encoding="utf-8")
        call(lead, op="send")
        made = call(lead, op="invite")
        at(cy)
        joined = routes.api_team({"op": "join", "words": made["link"], "into": str(cy["root"]), "route": "relay"})
        made_at = read(cy)
        check("434: a join from Home makes the project with the lead's name and method and nothing more of the study",
              made_at.get("name") == "Hedgerow walkers" and routes.method_of(made_at) == "ipa"
              and not made_at.get("research_question") and not made_at.get("participants"),
              json.dumps({"made": made_at, "joined": joined.get("project")}))
        call(lead, op="admit", invite=made["invite"], match=True)
        cy["root"] = Path((joined.get("project") or {}).get("id") or cy["root"])
        at(cy)
        routes.api_team({"op": "joined", "invite": made["invite"], "root": str(cy["root"])})
        for _ in range(3):
            call(lead, op="send")
            call(cy, op="send")
        had, got = read(lead), read(cy)
        check("434: a project joined from Home ends with the study's name, question, method, demographics and "
              "profiles with their pictures once the first copy is in, and its own settings its own",
              got.get("name") == had.get("name") and got.get("research_question") == had["research_question"]
              and routes.method_of(got) == "ipa"
              and [(c["name"], [v["word"] for v in c["values"]]) for c in got.get("demographics") or []]
              == [("Age range", ["30 to 39"])]
              and got.get("participants") == had["participants"]
              and (cy["root"] / "pictures" / "Wren-2.png").is_file()
              and b"Ada's own positioning" not in everything_sent() and not got.get("reflexivity"),
              json.dumps({"got": got}))

        # 10. both change one participant's picture to a file of the same name before either has the other's, and
        # the member also changes a portrait: the portrait is taken, the lead's picture keeps its own bytes, and the
        # member ends with the lead's (teamfix4, the review's finding 3)
        call(member, op="send")
        call(lead, op="send")
        call(member, op="send")
        ada_png = traj_mod.png_write(4, 4, bytearray([10, 160, 10, 255] * 16))
        bo_png = traj_mod.png_write(4, 4, bytearray([160, 10, 160, 255] * 16))
        (pictures / "Wren-3.png").write_bytes(ada_png)
        people = read(lead)["participants"]
        people["P1 - Wren"]["picture"] = "Wren-3.png"
        write(lead, participants=people)
        (member["root"] / "pictures" / "Wren-3.png").write_bytes(bo_png)
        people = read(member)["participants"]
        people["P1 - Wren"]["picture"] = "Wren-3.png"
        people["P2 - Fern"]["portrait"] = "Fern walks at dusk."
        write(member, participants=people)
        call(member, op="send")
        call(lead, op="send")
        lead_after = sha(pictures / "Wren-3.png")
        call(member, op="send")
        check("434: a member's change that names a picture the lead changed too takes the portrait and never "
              "replaces the lead's picture, and the member ends with the lead's",
              lead_after == hashlib.sha256(ada_png).hexdigest()
              and read(lead)["participants"]["P2 - Fern"].get("portrait") == "Fern walks at dusk."
              and sha(member["root"] / "pictures" / "Wren-3.png") == hashlib.sha256(ada_png).hexdigest(),
              json.dumps({"lead": read(lead)["participants"]}))

        # 11. a member on a team from before this build, with settings of its own the lead does not hold, keeps them
        # on the first study taken and they go to the lead; the project file goes to _Archive first (finding 2)
        at(member)
        st = team_sync.load_state(member["root"])
        st.pop("study", None)
        team_sync.save_state(member["root"], st)
        write(member, names={"P1 - Wren": "Robin"}, research_question="Bo's old question.")
        call(member, op="send")
        call(lead, op="send")
        call(member, op="send")
        call(lead, op="send")
        call(member, op="send")
        archived = sorted(p.name for p in (member["root"] / "_Archive").glob("idiograph-project (pre-study *).json"))
        check("434: a member's own Rename names, which the lead did not hold, are kept on the first study taken and "
              "reach the lead, the lead's question is taken, and the project file was kept in _Archive first",
              read(member).get("names") == {"P1 - Wren": "Robin"} and read(lead).get("names") == {"P1 - Wren": "Robin"}
              and read(member).get("research_question") == read(lead).get("research_question")
              and read(lead).get("research_question") != "Bo's old question." and bool(archived),
              json.dumps({"member": read(member).get("names"), "lead": read(lead).get("names"), "archived": archived}))

        # 11b. a picture that comes is read whole: a PNG larger than the app's picture size, or one that only starts
        # as a PNG, is refused, and one the app would keep is taken (teamfix4)
        side = traj_mod.PICTURE_SIZE + 1
        check("434: a picture that comes is kept only when it reads as a PNG no larger than the app's picture size",
              team_study.picture_ok("Wren-9.png", ada_png)
              and not team_study.picture_ok("Wren-9.png", traj_mod.png_write(side, side, bytearray(
                  [1, 2, 3, 255] * side * side)))
              and not team_study.picture_ok("Wren-9.png", b"\x89PNG\r\n\x1a\n" + b"\x00" * 64), "")

        # 11c. a small PNG whose image data inflates to far more than its header's rows is refused without being
        # inflated whole (teamfix4, the recheck's low 1)
        import struct
        import zlib

        def chunk(tag, body):
            return struct.pack(">I", len(body)) + tag + body + struct.pack(">I", zlib.crc32(tag + body) & 0xffffffff)

        bomb = (b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", 1, 1, 8, 6, 0, 0, 0))
                + chunk(b"IDAT", zlib.compress(b"\x00" * (8 * 1024 * 1024), 9)) + chunk(b"IEND", b""))
        check("434: a PNG of one pixel whose data inflates to megabytes is refused", len(bomb) < 64 * 1024
              and not team_study.picture_ok("Wren-9.png", bomb), str(len(bomb)))

        # 11d. a member's change that names another participant's picture file never replaces the lead's bytes of
        # it (the recheck's low 3)
        call(member, op="send")
        call(lead, op="send")
        call(member, op="send")
        (member["root"] / "pictures" / "Wren-3.png").write_bytes(bo_png)
        people = read(member)["participants"]
        people["P2 - Fern"]["picture"] = "Wren-3.png"
        write(member, participants=people)
        call(member, op="send")
        call(lead, op="send")
        check("434: a member's change setting one participant's picture to another's file name leaves the lead's "
              "file as it was", sha(pictures / "Wren-3.png") == hashlib.sha256(ada_png).hexdigest()
              and read(lead)["participants"]["P1 - Wren"]["picture"] == "Wren-3.png",
              json.dumps(read(lead)["participants"]))

        # 12. the lead's second computer joined from Home holds only the name and the method: it asks for the study
        # and takes it before it ever sends one, so the lead's study is never wiped (finding 1)
        whole = read(lead)
        call(lead, op="remove", member="Bo")
        call(lead, op="send")
        own = call(lead, op="invite", own=True)
        two_home = scratch / "team-434-lead2"
        shutil.rmtree(two_home, ignore_errors=True)
        two_home.mkdir(parents=True)
        two = {"home": two_home, "root": two_home / "Second", "config": two_home / "config.json"}
        two["config"].write_text(json.dumps({"projects": []}), encoding="utf-8")
        at(two)
        joined = routes.api_team({"op": "join", "words": own["link"], "into": str(two["root"]), "route": "relay"})
        call(lead, op="admit", invite=own["invite"], match=True)
        two["root"] = Path((joined.get("project") or {}).get("id") or two["root"])
        at(two)
        routes.api_team({"op": "joined", "invite": own["invite"], "root": str(two["root"])})
        call(two, op="send")
        call(lead, op="send")
        kept_whole = read(lead)
        check("434: the lead's second computer joined from Home sends no study before it has one, and the lead's "
              "project keeps its whole study",
              all(kept_whole.get(k) == whole.get(k) for k in ("name", "research_question", "demographics",
                                                               "participants", "names")),
              json.dumps({"kept": kept_whole}))
        for _ in range(3):
            call(two, op="send")
            call(lead, op="send")
            call(cy, op="send")
        got, had, cy_got = read(two), read(lead), read(cy)

        def study(project):
            return [project.get(k) for k in ("name", "research_question", "participants", "names")] + [
                [(c["name"], [v["word"] for v in c["values"]]) for c in project.get("demographics") or []]]

        check("434: the lead's second computer then has the lead's study, and the lead and a member keep theirs",
              study(got) == study(had) == study(whole)
              and cy_got.get("research_question") == whole.get("research_question")
              and cy_got.get("participants") == whole.get("participants"),
              json.dumps({"two": got, "cy": cy_got}))

        # 13. a member's change of the method or the timepoints never reaches a lead's project with work in it, and
        # one with no participant takes it (lowsW)
        method_was = routes.method_of(read(lead))
        write(cy, method="ta")
        for _ in range(2):
            call(cy, op="send")
            call(lead, op="send")
        kept_method = routes.method_of(read(lead))
        empty = scratch / "team-434-empty"
        shutil.rmtree(empty, ignore_errors=True)
        empty.mkdir(parents=True)
        at(lead)
        with_work = team_study.kept_as_is(lead["root"], {"method": "ipa"}, {"method": "ta", "timepoints": [
            {"label": "T1", "description": ""}, {"label": "T2", "description": ""}]})
        without = team_study.kept_as_is(empty, {"method": "ipa"}, {"method": "ta"})
        check("434: a member's change of the method or the timepoints is not taken by a lead's project that holds "
              "participants, and a project with none takes it",
              method_was == "ipa" and kept_method == "ipa" and with_work == {"method": "ipa"}
              and without == {"method": "ta"}, json.dumps([method_was, kept_method, with_work, without]))
        write(cy, method="ipa")

        # 14. a change of the study or a "stopped" handed again, by a relay or a shared folder that keeps it, is
        # taken once: the lead's computer keeps the id of each it has taken (lowsW)
        people = read(cy)["participants"]
        old_label = read(lead)["participants"]["P1 - Wren"]["label"]
        people["P1 - Wren"]["label"] = "The replayed label"
        write(cy, participants=people)
        call(cy, op="send")
        call(lead, op="send")
        taken_once = read(lead)["participants"]["P1 - Wren"]["label"]
        write(lead, participants=dict(read(lead)["participants"], **{
            "P1 - Wren": dict(read(lead)["participants"]["P1 - Wren"], label=old_label)}))

        def look_again(forget=False):
            at(lead)
            held = team_sync.load_state(lead["root"])
            held["cursors"] = {}
            if forget:
                held["once"] = []
            team_sync.save_state(lead["root"], held)
            call(lead, op="send")

        look_again()
        after_replay = read(lead)["participants"]["P1 - Wren"]["label"]
        look_again(forget=True)
        forgotten = read(lead)["participants"]["P1 - Wren"]["label"]
        check("434: a change of the study handed to the lead's computer again is not taken a second time, while the "
              "same message taken with no id kept would be",
              taken_once == "The replayed label" and after_replay == old_label and forgotten == "The replayed label",
              json.dumps([taken_once, after_replay, forgotten]))
    finally:
        (server_mod.CONFIG_PATH, server_mod.ROOT_OVERRIDE, team.DEVICE_PATH, transport.OVERRIDE, team_sync.WAIT,
         team_study.packed) = kept
