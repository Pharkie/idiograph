"""Area 353: Working together's shared-folder route (wtfolder, 9 November 2026, the spec's section 6). Two scratch
installs in one process, each its own settings folder, device file and project, sharing a temp folder as OneDrive
would be shared, through the route as the app registers it ("folder"), no loopback. What matters: the invite, the
join and the match go through the folder, messages and a blob go both ways and open, a half-written file is never
taken until it is whole, each device writes only in its own subfolder, what every device has seen is dropped, the
watch notices a new message, and a folder not there is refused in plain words and said on the page. Every fixture is
invented."""
from __future__ import annotations

import json
import os
import shutil
import threading
from pathlib import Path

from .support import check


def install(scratch: Path, name: str, project: str) -> dict:
    home = scratch / f"team-353-{name}"
    shutil.rmtree(home, ignore_errors=True)
    root = home / project
    root.mkdir(parents=True)
    (root / "idiograph-project.json").write_text(json.dumps({"name": project}), encoding="utf-8")
    config = home / "config.json"
    config.write_text(json.dumps({"projects": [{"root": str(root)}]}), encoding="utf-8")
    return {"home": home, "root": root, "config": config}


def files_under(folder: Path) -> dict:
    """Every file under `folder` with its bytes, by its path from there."""
    return {p.relative_to(folder).as_posix(): p.read_bytes() for p in sorted(folder.rglob("*")) if p.is_file()}


def test_team_folder(scratch: Path):
    print("\n353. Working together's shared-folder route: invite and join through the folder, messages and a blob both "
          "ways, a half-written file ignored, each device in its own subfolder alone, what all have seen dropped, the "
          "watch, a missing folder said plainly (wtfolder)")
    import i18n
    import folder_transport as ft
    import idiograph_routes as routes
    import server as server_mod
    import team
    import transport
    from workbook import WorkbookError

    shared = scratch / "team-353-shared" / "OneDrive" / "Hedgerow survey"
    shutil.rmtree(scratch / "team-353-shared", ignore_errors=True)
    shared.mkdir(parents=True)
    lead = install(scratch, "lead", "Hedgerow survey")
    joiner = install(scratch, "joiner", "Hedgerow survey, a copy")
    kept = (server_mod.CONFIG_PATH, server_mod.ROOT_OVERRIDE, team.DEVICE_PATH, transport.OVERRIDE,
            os.environ.pop(transport.ENV, None), ft.POLL, ft._Watch.TICK)
    transport.OVERRIDE = None

    def at(who):
        server_mod.CONFIG_PATH = who["config"]
        server_mod.ROOT_OVERRIDE = None
        team.DEVICE_PATH = None

    def call(who, **body):
        at(who)
        return routes.api_team(dict(body, root=str(who["root"])))

    def way(who):
        at(who)
        data = team.read_team(who["root"])
        return data, team.device(), team.transport_for(data, team.device())

    try:
        # 1. the folder route registered, and a folder that is not there refused in plain words and said on the page
        call(lead, op="on", name="Hazel")
        call(lead, op="set", route="folder", folder=str(shared.parent / "Not synced yet"))
        shown = call(lead, op="show")["team"]
        try:
            call(lead, op="invite")
            refused = ""
        except WorkbookError as exc:
            refused = str(exc)
        check("353: the shared folder is a route of its own, and one that is not there is said on the page and "
              "refuses an invite in plain words, nothing made in its place",
              "folder" in transport.FACTORIES and shown["folder_state"] == "missing"
              and refused == i18n.t("team.refused.folder_missing", folder=str(shared.parent / "Not synced yet"))
              and not (shared.parent / "Not synced yet").exists(), refused)

        # 2. invite, join and match, all through the folder
        call(lead, op="set", folder=str(shared))
        call(joiner, op="on", name="Rowan")
        call(joiner, op="set", route="folder", folder=str(shared))
        made = call(lead, op="invite")
        joined = call(joiner, op="join", words=made["words"], name="Rowan")
        answered = call(lead, op="answers", invite=made["invite"])
        call(lead, op="admit", invite=made["invite"], match=True)
        done = call(joiner, op="joined", invite=made["invite"])
        lead_data, lead_dev, lead_way = way(lead)
        joiner_data, joiner_dev, joiner_way = way(joiner)
        team_dir = shared / f"Idiograph {lead_data['team'][:8]}"
        answers_in = sorted(p.name for p in (team_dir / "invites" / made["invite"]).iterdir())
        check("353: an invite answered and matched through the shared folder leaves both installs on one team with "
              "one key, its mailbox Idiograph <8 letters>/invites/<invite>/ with a file for each message",
              answered["answered"] and joined["code"] == answered["code"] and done["joined"]
              and joiner_data["team"] == lead_data["team"] and joiner_data["route"] == "folder"
              and team.project_key(lead_data["team"], 1) == team.project_key(joiner_data["team"], 1)
              and len(answers_in) == 4 and all(n.endswith(".join") for n in answers_in), str(answers_in))

        # 3. messages both ways, the same bytes as an envelope, under the sender's own folder
        tid = lead_data["team"]
        key = team.project_key(tid, 1)
        others = {k: v for k, v in files_under(team_dir).items() if not k.startswith(f"devices/{lead_dev['id']}/")}
        at(lead)
        sent = team.seal_envelope(tid, 1, key, lead_dev, lead_data["member"], team.next_seq(tid), "comment",
                                  {"text": "The blackthorn flowered early"})
        n_sent = lead_way.send(tid, sent)
        at(lead)
        put = lead_way.put_blob(tid, "blob0123456789abcdef", b"sealed recording bytes" * 100)
        lead_files = sorted(p.name for p in (team_dir / "devices" / lead_dev["id"] / "messages").iterdir())
        after_others = {k: v for k, v in files_under(team_dir).items() if not k.startswith(f"devices/{lead_dev['id']}/")}
        at(joiner)
        got = joiner_way.fetch(tid, 0)
        opened = [team.open_envelope(raw, joiner_data["roster"], {1: key}) for _n, _d, raw in got]
        at(joiner)
        back = team.seal_envelope(tid, 1, key, joiner_dev, joiner_data["member"], team.next_seq(tid), "comment",
                                  {"text": "Two wrens by the stile"})
        joiner_way.send(tid, back)
        at(lead)
        lead_got = lead_way.fetch(tid, n_sent)
        at(joiner)
        blob = joiner_way.get_blob(tid, "blob0123456789abcdef")
        check("353: a message sent through the folder is the envelope's own bytes at devices/<device>/messages/"
              "<seq>.sealed, read and opened on the other install, one sent back the same way, and a blob comes "
              "back whole from the sender's blobs folder",
              (team_dir / "devices" / lead_dev["id"] / "messages" / lead_files[-1]).read_bytes() == sent
              and opened[-1]["body"] == {"text": "The blackthorn flowered early"} and opened[0]["kind"] == "roster"
              and [d for _n, d, _r in got] == [lead_dev["id"]] * len(got)
              and [r for _n, _d, r in lead_got] == [back] and lead_got[0][1] == joiner_dev["id"]
              and blob == b"sealed recording bytes" * 100 and put == len(blob)
              and all(f.endswith(".sealed") and f.split(".")[0].isdigit() for f in lead_files),
              json.dumps({"lead_files": lead_files, "got": len(got)}))
        check("353: sending a message and a blob writes nothing outside the sender's own device folder: the other's "
              "folder and the invite's files are byte for byte as they were",
              others == after_others and others, str(sorted(set(after_others) ^ set(others))))

        # 4. a half-written file ignored until it is whole, and counted as one that will not open yet
        jdir = team_dir / "devices" / joiner_dev["id"] / "messages"
        nxt = 1 + max(int(p.stem) for p in jdir.glob("*.sealed"))
        later = team.seal_envelope(tid, 1, key, joiner_dev, joiner_data["member"], 99, "comment",
                                   {"text": "A hare in the far field"})
        (jdir / f".{nxt}.sealed.ab12cd34.tmp").write_bytes(later[:40])
        at(lead)
        before_half = lead_way.fetch(tid, 0)
        (jdir / f"{nxt}.sealed").write_bytes(later[: len(later) // 2])
        at(lead)
        half = lead_way.fetch(tid, 0)
        half_view = call(lead, op="show")["team"]
        (jdir / f"{nxt}.sealed").write_bytes(later)
        at(lead)
        whole = lead_way.fetch(tid, 0)
        check("353: a file still being written, under its temporary name or cut short under its own, is not taken, "
              "and the page says a file will not open yet; once whole it comes in after the ones before it",
              len(before_half) == len(half) and half_view["folder_state"] == "unopened" and half_view["unopened"] == 1
              and len(whole) == len(half) + 1 and whole[-1][2] == later
              and call(lead, op="show")["team"]["folder_state"] == "", json.dumps(half_view.get("folder_state")))

        # 5. what all have seen dropped, by its sender alone
        lead_msgs = jdir.parent.parent / lead_dev["id"] / "messages"
        count_before = len(list(lead_msgs.glob("*.sealed")))
        at(lead)
        dropped_early = lead_way.seen(tid, whole[-1][0])
        joiner_had = len(list(jdir.glob("*.sealed")))
        at(joiner)
        top = joiner_way.fetch(tid, 0)[-1][0]
        joiner_dropped = joiner_way.seen(tid, top)
        lead_still = len(list(lead_msgs.glob("*.sealed")))
        at(lead)
        dropped = lead_way.seen(tid, whole[-1][0])
        seen_mark = json.loads((jdir.parent / "seen.json").read_text(encoding="utf-8"))
        check("353: a sender deletes its own messages once the other device's seen.json covers them, never before "
              "and never another's: the lead's first look drops nothing, the joiner's drops his own the lead has "
              "read and leaves the lead's, and the lead's next drops the lead's",
              dropped_early == 0 and joiner_had == joiner_dropped == 2 and lead_still == count_before
              and dropped == count_before and not list(lead_msgs.glob("*.sealed"))
              and seen_mark.get(lead_dev["id"]) == count_before,
              json.dumps({"early": dropped_early, "joiner": [joiner_had, joiner_dropped], "lead": [count_before,
                          lead_still, dropped], "mark": seen_mark}))

        # 6. the watch: on starting, and when a new message comes
        ft.POLL = 0.2
        ft._Watch.TICK = 0.05
        came = threading.Event()
        calls = []

        def on_new():
            calls.append(1)
            if len(calls) >= 2:
                came.set()
        at(joiner)
        stop = joiner_way.listen(tid, on_new)
        at(lead)
        lead_way.send(tid, team.seal_envelope(tid, 1, key, lead_dev, lead_data["member"], team.next_seq(tid),
                                              "comment", {"text": "Sloes ripening"}))
        heard = came.wait(5)
        stop()
        check("353: the watch looks on starting and again on its round, and says when a new message has come",
              heard and len(calls) >= 2, str(len(calls)))

        # 7. the folder gone from under it: refused in plain words, then back
        away = shared.with_name("Hedgerow survey (offline)")
        shared.rename(away)
        try:
            at(joiner)
            joiner_way.fetch(tid, 0)
            gone = ""
        except team.TeamError as exc:
            gone = exc.code
        gone_view = call(joiner, op="show")["team"]
        away.rename(shared)
        at(joiner)
        back_again = joiner_way.fetch(tid, 0)
        check("353: with the shared folder gone, a look is refused as not there and the page says so, and once it is "
              "back the messages are read again",
              gone == "folder_missing" and gone_view["folder_state"] == "missing" and back_again, gone)

        # 8. the versions of a participant through the folder, by team_sync's own send and fetch (landwt)
        import hashlib
        import team_sync
        from . import support
        pristine = support.source("demo/pristine")
        case = lead["root"] / "P1 - Sloe"
        (case / "Working").mkdir(parents=True)
        shutil.copy2(pristine / "Juno - EN & ES.xlsx", case / "P1 Sloe - EN & ES.xlsx")
        shutil.copy2(pristine / "Working" / "Juno - EN & ES.progress.json",
                     case / "Working" / "P1 Sloe - EN & ES.progress.json")
        at(lead)
        went = team_sync.sync(lead["root"], now=True)
        at(joiner)
        took = team_sync.sync(joiner["root"])
        copy = joiner["root"] / "P1 - Sloe" / "P1 Sloe - EN & ES.xlsx"
        digest = lambda p: hashlib.sha256(p.read_bytes()).hexdigest() if p.is_file() else ""
        mark = json.loads((jdir.parent / "seen.json").read_text(encoding="utf-8"))
        newest = max(int(p.stem) for p in lead_msgs.glob("*.sealed")) if list(lead_msgs.glob("*.sealed")) else 0
        check("353: the lead's participant goes as a version through the shared folder by the server's own send, the "
              "joiner's look takes it in whole, and his seen.json then covers the lead's newest message",
              "P1 - Sloe" in went["sent"] and took["applied"] == ["P1 - Sloe"] and not took["offline"]
              and digest(copy) == digest(case / "P1 Sloe - EN & ES.xlsx") != "" and newest
              and mark.get(lead_dev["id"]) == newest,
              json.dumps({"went": went, "took": took, "mark": mark, "newest": newest}))
    finally:
        (server_mod.CONFIG_PATH, server_mod.ROOT_OVERRIDE, team.DEVICE_PATH, transport.OVERRIDE, env, ft.POLL,
         ft._Watch.TICK) = kept
        if env is not None:
            os.environ[transport.ENV] = env
