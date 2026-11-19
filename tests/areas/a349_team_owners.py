"""Area 349: Working together's owners and versions (wtowners, 8 November 2026, the spec's build 2, Adam's choices
that evening about 19:10: all the spec's defaults, what came in and what waits under the project's question). Two
scratch installs in one process, each its own settings folder, device file and project, paired over the loopback
transport, then once more through the relay run on this computer under Miniflare as area 342 runs it.

What matters: a new member gets a first full copy, a recording going as a sealed blob of its own, and a recording
travels once, sent again only when it changes (relayopen). The
lead's change to his participant reaches the member's copy, as a change made elsewhere, and the member's write to
it is refused, the app's route and the GETs file alike, while an export still works. The member's change to the
participant he works on goes a minute after his last save, or at once on Send now, and comes in at the lead's. A
version is applied only when its count is higher than the one held. What came in today and how many changes wait
with no connection are what the project's page shows under the question. Every fixture is invented."""
from __future__ import annotations

import base64
import hashlib
import json
import os
import shutil
import subprocess
import threading
import time
from pathlib import Path

from . import support
from .support import check, skip

PEOPLE = ("Wren", "Fern")


def sha(path: Path) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def install(scratch: Path, name: str, project: str, people=()) -> dict:
    """A scratch install: its settings file, beside which its device file goes, and one project of its own, with
    a participant folder for each of `people` made from the demo's pristine files under new names."""
    home = scratch / f"team-349-{name}"
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
    if people:
        shutil.copy2(pristine / "idiograph-gets.json", root / "idiograph-gets.json")
    config = home / "config.json"
    config.write_text(json.dumps({"projects": [{"root": str(root)}]}), encoding="utf-8")
    return {"home": home, "root": root, "config": config}


def book(who: dict, n: int, name: str) -> Path:
    return who["root"] / f"P{n} - {name}" / f"P{n} {name} - EN & ES.xlsx"


def progress(who: dict, n: int, name: str) -> Path:
    return who["root"] / f"P{n} - {name}" / "Working" / f"P{n} {name} - EN & ES.progress.json"


class Mapped:
    """A transport whose project is another's id, the relay's own for the team (the relay makes its ids)."""

    def __init__(self, inner, project: str):
        self.inner, self.project = inner, project

    def send(self, _pid, sealed):
        return self.inner.send(self.project, sealed)

    def fetch(self, _pid, after):
        return self.inner.fetch(self.project, after)

    def listen(self, _pid, on_new):
        return lambda: None

    def put_blob(self, _pid, blob, sealed):
        return self.inner.put_blob(self.project, blob, sealed)

    def get_blob(self, _pid, blob):
        return self.inner.get_blob(self.project, blob)


class Unreachable:
    """A transport with no connection: every send fails, and nothing comes."""

    def send(self, *_a):
        raise OSError("no connection")

    def fetch(self, *_a):
        raise OSError("no connection")

    def listen(self, *_a):
        return lambda: None

    def put_blob(self, *_a):
        raise OSError("no connection")


def trace(who: dict) -> dict:
    """What an install's team_sync has kept, for a failed check's line: the computers given a full copy, each
    count sent and held, the cursors, when a send last failed, and the team log's dropped messages."""
    folder = who["root"] / ".idiograph-team"
    try:
        state = json.loads((folder / "sync.json").read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        state = {"unread": repr(exc)}
    try:
        log = [json.loads(line).get("dropped") for line in (folder / "log.jsonl").read_text(encoding="utf-8").splitlines()]
    except (OSError, ValueError):
        log = []
    return {"copied": [d[:6] for d in state.get("copied") or []],
            "sent": {k: (v or {}).get("n") for k, v in (state.get("sent") or {}).items()},
            "held": state.get("held"), "cursors": state.get("cursors"), "failed": state.get("failed"),
            "unread": state.get("unread"), "dropped": log}


def test_team_owners(scratch: Path):
    print("\n349. Working together's owners and versions: the first full copy, a change reaching the other's copy, "
          "a write to another's participant refused, a version applied only when newer, what came in and waits "
          "(wtowners)")
    try:
        import cryptography  # noqa: F401
    except ImportError:
        return skip("349: Working together's owners and versions", "no cryptography in this Python")
    import gets as gets_mod
    import i18n
    import idiograph_routes as routes
    import server as server_mod
    import team
    import team_sync
    import transport
    import workbook as wb_mod
    from workbook import WorkbookError

    lead = install(scratch, "lead", "Hedgerow walkers", PEOPLE)
    member = install(scratch, "member", "Hedgerow walkers, Bo's")
    kept = (server_mod.CONFIG_PATH, server_mod.ROOT_OVERRIDE, team.DEVICE_PATH, transport.OVERRIDE, team_sync.WAIT)
    hub = transport.Hub()
    loop = lambda dev, data: transport.Loopback(dev.get("id") or "", hub=hub)
    transport.OVERRIDE = loop

    def at(who):
        server_mod.CONFIG_PATH = who["config"]
        server_mod.ROOT_OVERRIDE = None
        team.DEVICE_PATH = None

    def call(who, **body):
        at(who)
        return routes.api_team(dict(body, root=str(who["root"])))

    def mark(who, n, name, op="mark"):
        at(who)
        return routes.api_complete({"workbook": str(book(who, n, name)), "op": op})

    def refused(fn) -> str:
        try:
            fn()
        except WorkbookError as exc:
            return str(exc)
        return ""

    def refused_cli(fn, project, args) -> str:
        import idiograph_cli as cli_mod
        try:
            fn(project, args)
        except cli_mod.cli.Refused as exc:
            return " ".join(str(x) for x in exc.args)
        except WorkbookError as exc:
            return str(exc)
        return ""

    try:
        # pairing, as area 341 does it, then Fern given to Bo and the recordings ticked
        call(lead, op="on", name="Ada")
        made = call(lead, op="invite")
        call(member, op="join", words=made["link"], name="Bo")
        call(lead, op="admit", invite=made["invite"], match=True)
        call(member, op="joined", invite=made["invite"])
        call(lead, op="set", owners={"P2 - Fern": "Bo"}, recordings=True)
        recording = lead["root"] / "P1 - Wren" / "P1 Wren.m4a"
        recording.write_bytes(os.urandom(1300 * 1024))

        # 1. the first full copy
        sent = call(lead, op="send")
        took = call(member, op="send")
        pairs = [(book(lead, 1, "Wren"), book(member, 1, "Wren")), (book(lead, 2, "Fern"), book(member, 2, "Fern")),
                 (progress(lead, 1, "Wren"), progress(member, 1, "Wren")), (recording, member["root"] / "P1 - Wren" / "P1 Wren.m4a"),
                 (lead["root"] / "idiograph-gets.json", member["root"] / "idiograph-gets.json")]
        same = [b.is_file() and sha(a) == sha(b) for a, b in pairs]
        check("349: a member who joins gets a first full copy at once, every participant and the GETs board, each "
              "file as the lead has it, and a recording over a message's size goes as a sealed blob",
              all(same) and sorted(sent["sent"]) == ["P1 - Wren", "P2 - Fern", "gets"]
              and sorted(took["applied"]) == ["P1 - Wren", "P2 - Fern", "gets"] and len(hub.blobs) == 1
              and len(list(hub.blobs.values())[0]) > team_sync.INLINE_MOST,
              json.dumps({"same": same, "sent": sent.get("sent"), "applied": took.get("applied"), "blobs": len(hub.blobs)}))
        at(member)
        shown = routes.project_section(member["root"], [], server_mod.config())
        check("349: on the member's page Wren carries the lead's tag and Fern none, and a first copy is no arrival",
              shown["team"]["tags"].get("P1 - Wren") == {"owner": "Ada"} and "P2 - Fern" not in shown["team"]["tags"]
              and shown["team"]["arrivals"] == [] and shown["team"]["waiting"] == 0, json.dumps(shown.get("team")))

        # 2. the member's write to the lead's participant refused, his export not
        before = sha(progress(member, 1, "Wren"))
        said = refused(lambda: mark(member, 1, "Wren"))
        gets_said = refused(lambda: gets_mod.write(member["root"], {"boards": []}))
        # the agents' gets ops too: the owner's refusal comes first, before "Nothing to change" and in a dry run
        import argparse
        import idiograph_cli as cli_mod
        at(member)
        member_project = cli_mod.Project(member["root"], False)
        said_cli = []
        for fn, extra in ((cli_mod.cmd_gets_apply, {"ops": None, "board": None}), (cli_mod.cmd_gets_fresh, {"name": ""})):
            for dry in (True, False):
                said_cli.append(refused_cli(fn, member_project, argparse.Namespace(dry_run=dry, note="", tool="t", **extra)))
        at(member)
        exported = routes.api_export({"path": str(book(member, 1, "Wren"))})
        check("349: on the member's install a write to the lead's participant is refused in one plain line, the "
              "GETs board's too, nothing written, and an export of it still made",
              said == i18n.t("team.refused.not_yours", participant="Wren", name="Ada")
              and gets_said == i18n.t("team.refused.not_yours_gets", name="Ada")
              and sha(progress(member, 1, "Wren")) == before and bool(exported)
              and all(i18n.t("team.refused.not_yours_gets", name="Ada") in x for x in said_cli),
              f"{said} | {gets_said} | {said_cli}")

        # 3. the lead's change reaches the member's copy, as a change made elsewhere
        mark(lead, 1, "Wren", op="reopen")
        call(lead, op="send")
        took = call(member, op="send")
        at(member)
        page = team_sync.status(member["root"])
        check("349: the lead's change to Wren reaches the member's copy, written in place, seen as a change made "
              "elsewhere, and said under the question as Ada's changes to Wren",
              took["applied"] == ["P1 - Wren"] and sha(progress(lead, 1, "Wren")) == sha(progress(member, 1, "Wren"))
              and not wb_mod.written_here(progress(member, 1, "Wren"))
              and [(a["name"], a["participant"]) for a in page["arrivals"]] == [("Ada", "Wren")]
              and not list((member["root"] / "P1 - Wren" / "Working").glob(".*.incoming")), json.dumps(page))

        # 3a. a recording travels once (relayopen, Adam's ruling of 18 November 2026): Wren changed twice more, its
        # recording not sent again, and a changed recording sent once more, to a member who then has it
        blobs_after_copy = len(hub.blobs)
        mark(lead, 1, "Wren")
        call(lead, op="send")
        call(member, op="send")
        mark(lead, 1, "Wren", op="reopen")
        twice = call(lead, op="send")
        took_twice = call(member, op="send")
        unchanged = len(hub.blobs)
        recording.write_bytes(os.urandom(900 * 1024))
        at(lead)
        waits = team_sync.status(lead["root"])["waiting"]
        changed = call(lead, op="send")
        call(member, op="send")
        check("349: a recording travels once: Wren changed twice more goes twice with no recording sent again, and only "
              "when the recording itself changes is it sent, once, and the member then has it",
              blobs_after_copy == 1 and twice["sent"] == ["P1 - Wren"] and took_twice["applied"] == ["P1 - Wren"]
              and unchanged == 1 and waits == 1 and changed["sent"] == [] and len(hub.blobs) == 2
              and sha(recording) == sha(member["root"] / "P1 - Wren" / "P1 Wren.m4a"),
              json.dumps({"copy": blobs_after_copy, "twice": twice.get("sent"), "unchanged": unchanged, "waits": waits,
                          "changed": changed.get("sent"), "blobs": len(hub.blobs), "lead": trace(lead)}))

        # 3b. the relay's refusal kept and said (relayopen): the day's bytes used holds what waits until midnight UTC,
        # the page says why in place of no connection, and the next look tries nothing more
        class DayUsed(Exception):
            status, error = 429, "day"

        tries = []

        class Full:
            def send(self, *_a, **_k):
                tries.append("send")
                raise DayUsed()

            def put_blob(self, *_a, **_k):
                tries.append("blob")
                raise DayUsed()

            def fetch(self, *_a):
                return []

            def listen(self, *_a):
                return lambda: None

        transport.OVERRIDE = lambda dev, data: Full()
        try:
            mark(lead, 1, "Wren")
            first = call(lead, op="send")
            at(lead)
            held_page = team_sync.status(lead["root"])
            tried = len(tries)
            again = call(lead, op="send")
            at(lead)
            state = team_sync.load_state(lead["root"])
        finally:
            transport.OVERRIDE = loop
        check("349: the relay's refusal of the day's bytes holds what waits until midnight UTC: the page says so in its "
              "own line, not as no connection, and the next look tries nothing more",
              first["sent"] == [] and tried == 1 and len(tries) == 1 and again["sent"] == []
              and held_page["held"] == i18n.t("team.held.day") and held_page["waiting"] >= 1
              and state["hold"].get("word") == "day" and state["hold"].get("until", "").endswith("T00:00:00+00:00"),
              json.dumps({"first": first.get("sent"), "tries": tries, "page": held_page, "hold": state.get("hold")}))
        state["hold"] = {}
        team_sync.save_state(lead["root"], state)
        mark(lead, 1, "Wren", op="reopen")
        call(lead, op="send")
        call(member, op="send")

        # 4. the member's own participant goes a minute after his last save, or at once on Send now
        mark(member, 2, "Fern", op="reopen")
        team_sync.WAIT = 600
        at(member)
        quiet = team_sync.sync(member["root"])
        at(lead)
        nothing = team_sync.sync(lead["root"])
        team_sync.WAIT = 0
        at(member)
        later = team_sync.sync(member["root"])
        took = call(lead, op="send")
        at(lead)
        page = team_sync.status(lead["root"])
        check("349: the member's change to Fern waits a minute after his last save and then goes by itself, and at "
              "the lead's it comes in as Bo's changes to Fern",
              quiet["sent"] == [] and quiet["waiting"] == 1 and nothing["applied"] == [] and later["sent"] == ["P2 - Fern"]
              and took["applied"] == ["P2 - Fern"] and sha(progress(lead, 2, "Fern")) == sha(progress(member, 2, "Fern"))
              and [(a["name"], a["participant"]) for a in page["arrivals"]] == [("Bo", "Fern")]
              and page["tags"].get("P2 - Fern") == {"owner": "Bo"}, json.dumps({"q": quiet, "l": later, "page": page}))

        # 5. a version applied only when its count is higher than the one held
        at(lead)
        data = team.read_team(lead["root"])
        dev = team.device()
        other = scratch / "team-349-other.progress.json"
        other.write_text('{"version": 1, "rows": {}}\n', encoding="utf-8")
        item = {"what": "P1 - Wren", "files": [(other, "Working/P1 Wren - EN & ES.progress.json")],
                "lock": lead["root"] / "P1 - Wren" / "Working" / "team-349.lock"}
        way = team.transport_for(data, dev)
        held = team_sync.load_state(member["root"])["held"]["P1 - Wren"]
        was = sha(progress(member, 1, "Wren"))
        team_sync.send_one(lead["root"], data, dev, way, item, held)
        call(member, op="send")
        kept_older = sha(progress(member, 1, "Wren")) == was
        team_sync.send_one(lead["root"], data, dev, way, item, held + 5)
        # the lead's own count moved on as a version of his would move it, so his next one comes after it
        at(lead)
        own = team_sync.load_state(lead["root"])
        own["sent"]["P1 - Wren"]["n"] = held + 5
        team_sync.save_state(lead["root"], own)
        call(member, op="send")
        check("349: a version numbered no higher than the one held is passed over, and one numbered higher is applied",
              kept_older and sha(progress(member, 1, "Wren")) == sha(other)
              and team_sync.load_state(member["root"])["held"]["P1 - Wren"] == held + 5, str(held))

        # 6. no connection: the changes wait and the page says how many
        before6 = trace(lead)
        mark(lead, 1, "Wren", op="mark")
        transport.OVERRIDE = lambda dev, data: Unreachable()
        at(lead)
        gone = team_sync.sync(lead["root"], now=True)
        shown = routes.project_section(lead["root"], [], server_mod.config())["team"]
        transport.OVERRIDE = loop
        back = call(lead, op="send")
        at(lead)
        after = team_sync.status(lead["root"])
        check("349: with no connection a change waits, the page says one waiting to send, and it goes once the "
              "connection is back",
              gone["offline"] and shown["waiting"] == 1 and shown["offline"] is True
              and back["sent"] == ["P1 - Wren"] and after["waiting"] == 0 and after["offline"] is False,
              json.dumps({"gone": gone, "shown": shown, "back": back, "after": after, "lead": trace(lead),
                          "before": before6, "member": trace(member)}))
        call(member, op="send")

        # 6a. what this install has sent and taken in, or its keys, there but not readable a moment: the look is
        # refused with nothing written, never begun afresh, and goes as before once they read (teamflake)
        import locks
        kept_tries = (locks.READ_TRIES, locks.READ_PAUSE)
        locks.READ_TRIES, locks.READ_PAUSE = 2, 0.01
        state_file = lead["root"] / team.LOG_DIR / "sync.json"
        at(lead)
        dev_file = team.device_path()
        whole, whole_dev, counts = state_file.read_bytes(), dev_file.read_bytes(), trace(lead)
        refusals = []
        try:
            for broken, good in ((state_file, whole), (dev_file, whole_dev)):
                broken.write_bytes(good[: len(good) // 2])
                try:
                    at(lead)
                    team_sync.sync(lead["root"], now=True)
                    refusals.append("")
                except WorkbookError as exc:
                    refusals.append(getattr(exc, "code", "") or str(exc))
                left_alone = broken.read_bytes() == good[: len(good) // 2]
                refusals.append(left_alone)
                broken.write_bytes(good)
        finally:
            locks.READ_TRIES, locks.READ_PAUSE = kept_tries
        at(lead)
        again = team_sync.sync(lead["root"], now=True)
        check("349: what this install has kept, its counts or its keys, there but not readable, refuses the look with "
              "nothing written over it, and once it reads the look goes on from the same counts, sending nothing again",
              refusals == ["busy", True, "busy", True] and again["sent"] == [] and not again["offline"]
              and {k: trace(lead)[k] for k in ("copied", "sent", "held")} == {k: counts[k] for k in ("copied", "sent", "held")},
              json.dumps({"refusals": refusals, "again": again, "before": counts, "lead": trace(lead)}))

        # 6b. a participant the member adds is his to work on, at his install and then at the lead's (landwt)
        moss = ("Kit: [00:00:03] What did the hedge give you?\nMoss: [00:00:08] Sloes, late in the year.\n"
                "Kit: [00:00:40] And the birds?\nMoss: [00:01:15] They had the haws first.\n")
        at(member)
        added = routes.api_add_transcripts({"op": "add", "root": routes.project_id(member["root"]), "files": [
            {"name": "moss.txt", "data": base64.b64encode(moss.encode("utf-8")).decode("ascii"), "pseudonym": "Moss",
             "interview": "Autumn", "speakers": {"Kit": "interviewer", "Moss": "participant"}}]})
        folder = (added.get("cases") or [""])[0]
        n = int(folder.split(" ")[0][1:]) if folder.startswith("P") else 0
        at(member)
        own_said = refused(lambda: mark(member, n, "Moss", op="mark"))
        gone = call(member, op="send")
        took = call(lead, op="send")
        at(lead)
        lead_data = team.read_team(lead["root"])
        bo = next(m["id"] for m in team.roster_members(lead_data["roster"]) if m.get("name") == "Bo")
        lead_said = refused(lambda: mark(lead, n, "Moss", op="reopen"))
        call(member, op="send")
        at(member)
        member_data = team.read_team(member["root"])
        check("349: a participant the member adds is his: Add works on his install and so does his next change, it "
              "goes to the lead, whose computer takes it in and names it Bo's in the list, and there the lead's own "
              "write to it is refused",
              folder.endswith("Moss") and own_said == "" and folder in gone["sent"] and folder in took["applied"]
              and (lead_data["roster"].get("owners") or {}).get(folder) == bo
              and lead_said == i18n.t("team.refused.not_yours", participant="Moss", name="Bo")
              and (member_data["roster"].get("owners") or {}).get(folder) == bo
              and team_sync.owner_of(member_data, folder) == bo,
              json.dumps({"added": added.get("cases"), "own": own_said, "sent": gone.get("sent"),
                          "applied": took.get("applied"), "lead": lead_said}))

        # 6c. the app's paths when the relay says no or a file cannot be had (relayfix, the review's T5)
        app_paths(lead, member, call, mark, at, hub, loop)

        # 7. through the relay, run on this computer as area 342 runs it
        relay_part(scratch, lead, member, call, mark, sha, book, progress, at)
    finally:
        (server_mod.CONFIG_PATH, server_mod.ROOT_OVERRIDE, team.DEVICE_PATH, transport.OVERRIDE, team_sync.WAIT) = kept


class Refusal(Exception):
    """The relay's refusal as relay_transport raises it: a status, a word, and the computers behind."""

    def __init__(self, status, error, behind=None):
        super().__init__(error)
        self.status, self.error, self.behind = status, error, behind or []


class Wrap:
    """The loopback with some of its calls changed for one check."""

    def __init__(self, inner, **changed):
        self.inner, self.changed = inner, changed
        self.tries = []

    def __getattr__(self, name):
        if name in self.changed:
            def call(*a, **k):
                self.tries.append(name)
                return self.changed[name](*a, **k)
            return call
        return getattr(self.inner, name)


class Loopback(Wrap):
    """The wrapper under the loopback's own name, so the look keeps the loopback's count of what it has read
    (team_sync.way_key names a route's count by its class)."""


def app_paths(lead, member, call, mark, at, hub, loop):
    import i18n
    import team
    import team_sync
    import transport
    from workbook import WorkbookError
    recording = lead["root"] / "P1 - Wren" / "P1 Wren.m4a"
    there = member["root"] / "P1 - Wren" / "P1 Wren.m4a"

    def state_of(who):
        at(who)
        return team_sync.load_state(who["root"])

    def files_refused(*_a, **_k):
        raise Refusal(429, "day files")

    # a. a recording refused for the day's files holds files alone: the version of the same change still goes, the
    # line says so, and the next look tries no file while a later change still goes (A2)
    way = Loopback(None, put_blob=files_refused)
    transport.OVERRIDE = lambda dev, data: (setattr(way, "inner", loop(dev, data)) or way)
    try:
        recording.write_bytes(os.urandom(700 * 1024))
        mark(lead, 1, "Wren", op="reopen")
        first = call(lead, op="send")
        at(lead)
        page = team_sync.status(lead["root"])
        blob_tries = way.tries.count("put_blob")
        mark(lead, 1, "Wren")
        second = call(lead, op="send")
        hold = state_of(lead)["files_hold"]
    finally:
        transport.OVERRIDE = loop
    check("349: a recording refused for the day's files holds files alone: the change to Wren still goes, the page "
          "says the files wait in their own line, and the next look tries no file while a later change goes",
          first["sent"] == ["P1 - Wren"] and second["sent"] == ["P1 - Wren"] and blob_tries == 1
          and way.tries.count("put_blob") == 1 and page["held"] == i18n.t("team.held.files_day")
          and hold.get("word") == "day_files" and hold.get("until", "").endswith("T00:00:00+00:00"),
          json.dumps({"first": first, "second": second, "tries": way.tries, "page": page, "hold": hold}))
    st = state_of(lead)
    st["files_hold"] = {}
    team_sync.save_state(lead["root"], st)
    call(lead, op="send")
    call(member, op="send")

    # b. the project full holds what waits an hour, and the line names the computer that has not fetched (item 4)
    at(member)
    bo_device = team.device()["id"]

    def project_full(*_a, **_k):
        raise Refusal(429, "project full", [bo_device])
    way = Loopback(None, send=project_full)
    transport.OVERRIDE = lambda dev, data: (setattr(way, "inner", loop(dev, data)) or way)
    try:
        mark(lead, 1, "Wren", op="reopen")
        call(lead, op="send")
        at(lead)
        page = team_sync.status(lead["root"])
        hold = state_of(lead)["hold"]
    finally:
        transport.OVERRIDE = loop
    check("349: the relay holding as much of the project as it keeps holds what waits for an hour, and the page names "
          "the computer that has not fetched it, so the lead knows which to remove",
          hold.get("word") == "project_full" and hold.get("behind") == [bo_device]
          and not hold.get("until", "").endswith("T00:00:00+00:00") and "Bo" in page["held"]
          and page["held"].startswith(i18n.t("team.held.project_full_who", who="Bo").split("Bo")[0]),
          json.dumps({"page": page, "hold": hold}))
    st = state_of(lead)
    st["hold"] = {}
    team_sync.save_state(lead["root"], st)
    call(lead, op="send")
    call(member, op="send")

    # c. a recording over the route's limit is never read or sent, said in its line, and the line goes with the file
    # (A6, A12)
    small = Loopback(None)
    small.max_blob = 1024 * 1024
    transport.OVERRIDE = lambda dev, data: (setattr(small, "inner", loop(dev, data)) or small)
    try:
        recording.write_bytes(os.urandom(1300 * 1024))
        at(lead)
        big = team_sync.sync(lead["root"], now=True)
        at(lead)
        line = team_sync.status(lead["root"])["too_large"]
        kept = dict(state_of(lead)["too_large"])
        recording.unlink()
        at(lead)
        team_sync.sync(lead["root"], now=True)
        at(lead)
        line_after = team_sync.status(lead["root"])["too_large"]
    finally:
        transport.OVERRIDE = loop
    check("349: a recording over the route's limit is not sent, its line names the participant and the limit, and "
          "once the file is gone the line goes",
          not big["sent"] and list(kept) == ["P1 - Wren\tP1 Wren.m4a"]
          and line == i18n.t("team.held.too_large", participant="Wren", mb=1) and line_after == "",
          json.dumps({"big": big, "line": line, "after": line_after, "kept": kept}))

    # d. a recording whose file cannot be fetched just now, and one whose participant's lock is busy, stop the look
    # with the cursor unmoved, and the next look takes it (the cursor's part of H3, A4)
    recording.write_bytes(os.urandom(800 * 1024))
    call(lead, op="send")
    before = dict(state_of(member)["cursors"])

    def no_connection(*_a, **_k):
        raise OSError("no connection")
    way = Loopback(None, get_blob=no_connection)
    transport.OVERRIDE = lambda dev, data: (setattr(way, "inner", loop(dev, data)) or way)
    try:
        call(member, op="send")
        unfetched = dict(state_of(member)["cursors"])
    finally:
        transport.OVERRIDE = loop
    placed = team_sync.place
    busy_once = []

    def busy(files, base):
        if not busy_once:
            busy_once.append(1)
            raise WorkbookError("busy", code="busy")
        return placed(files, base)
    team_sync.place = busy
    try:
        call(member, op="send")
        busy_cursors = dict(state_of(member)["cursors"])
        arrived_busy = there.is_file() and there.read_bytes() == recording.read_bytes()
        call(member, op="send")
    finally:
        team_sync.place = placed
    check("349: a recording that cannot be fetched just now, or whose participant is busy, leaves the look's cursor "
          "where it was, and the next look takes it in",
          unfetched == before and busy_cursors == before and not arrived_busy
          and there.read_bytes() == recording.read_bytes(),
          json.dumps({"before": before, "unfetched": unfetched, "busy": busy_cursors}))

    # e. a dry run sends nothing and rewrites nothing, the outbox kept by other builds included (A15)
    transport.OVERRIDE = lambda dev, data: Loopback(loop(dev, data), send=no_connection)
    try:
        at(lead)
        team_sync.post(lead["root"], "seen", {"what": "a check's message"})
    finally:
        transport.OVERRIDE = loop
    out = lead["root"] / team.LOG_DIR / team_sync.OUT_FILE
    kept_out, boxes = out.read_bytes(), json.dumps({k: len(v) for k, v in hub.boxes.items()}, sort_keys=True)
    at(lead)
    dry = team_sync.sync(lead["root"], now=True, dry_run=True)
    check("349: a dry run sends nothing, not even what other builds kept to send, and rewrites nothing",
          dry.get("dry_run") is True and out.read_bytes() == kept_out
          and json.dumps({k: len(v) for k, v in hub.boxes.items()}, sort_keys=True) == boxes, json.dumps(dry))
    call(lead, op="send")
    call(member, op="send")

    # f. a first full copy stopped partway goes on, and what changes meanwhile of what it has sent goes too (A1)
    st = state_of(lead)
    others = list(st["copied"])
    st["copied"], st["copying"] = [], {"for": others, "done": ["P1 - Wren"]}
    team_sync.save_state(lead["root"], st)
    mark(lead, 1, "Wren")
    resumed = call(lead, op="send")
    after = state_of(lead)
    check("349: a first full copy stopped partway sends what it had not sent, and a change since to what it had "
          "sent goes as well, the copy then done",
          "P1 - Wren" in resumed["sent"] and "P2 - Fern" in resumed["sent"] and "gets" in resumed["sent"]
          and after["copied"] == others
          and after["copying"] == {}, json.dumps({"sent": resumed.get("sent"), "copying": after.get("copying")}))
    call(member, op="send")

    # g. Cloudflare's own refusals, HTML and not the relay's JSON, are a hold with a line of their own: its rate rule
    # for a minute, a closed relay (its day used, error 1027) for an hour, and no call to the relay meanwhile (H8)
    import relay_transport as rt
    words = (rt.not_json(429, b"<html>You are being rate limited</html>"),
             rt.not_json(503, b"<html>error code: 1027</html>"), rt.not_json(502, b"<html>bad gateway</html>"))
    out = {}
    for word in ("blocked", "closed"):
        def stopped(*_a, word=word, **_k):
            raise Refusal(429 if word == "blocked" else 503, word)
        way = Loopback(None, send=stopped, put_blob=stopped, fetch=stopped)
        transport.OVERRIDE = lambda dev, data, way=way: (setattr(way, "inner", loop(dev, data)) or way)
        try:
            mark(lead, 1, "Wren", op="reopen")
            call(lead, op="send")
            at(lead)
            page = team_sync.status(lead["root"])
            hold = state_of(lead)["hold"]
            tried = len(way.tries)
            call(lead, op="send")
            out[word] = (page["held"], hold.get("word"), hold.get("until", ""), len(way.tries) - tried)
        finally:
            transport.OVERRIDE = loop
        st = state_of(lead)
        st["hold"] = {}
        team_sync.save_state(lead["root"], st)
    from datetime import datetime, timezone
    left = {w: (datetime.fromisoformat(v[2]) - datetime.now(timezone.utc)).total_seconds() for w, v in out.items()}
    check("349: a page from Cloudflare in place of the relay's answer is read as its rate rule or the relay closed, "
          "each holds what waits with a line of its own, a minute and an hour, and no call goes meanwhile",
          words == ("blocked", "closed", "not the relay")
          and out["blocked"][:2] == (i18n.t("team.held.blocked"), "blocked") and 0 < left["blocked"] <= 60
          and out["closed"][:2] == (i18n.t("team.held.closed"), "closed") and 60 < left["closed"] <= 3600
          and out["blocked"][3] == 0 and out["closed"][3] == 0, json.dumps({"words": words, "out": out}))
    mark(lead, 1, "Wren")
    call(lead, op="send")
    call(member, op="send")

    # g2. a project the relay no longer holds (the operator deleted it): its 404 "no project"
    # is kept as a hold of its own, said on the page and to an agent whether or not anything waits, and no call goes
    # meanwhile, in either direction (relayfix3). It lifts once the team no longer sends through the relay
    def project_gone(*_a, **_k):
        raise Refusal(404, "no project")
    way = Loopback(None, send=project_gone, put_blob=project_gone, fetch=project_gone)
    transport.OVERRIDE = lambda dev, data, way=way: (setattr(way, "inner", loop(dev, data)) or way)
    try:
        mark(lead, 1, "Wren", op="reopen")
        first = call(lead, op="send")
        at(lead)
        page = team_sync.status(lead["root"])
        hold = state_of(lead)["hold"]
        tried = len(way.tries)
        call(lead, op="send")
        call(lead, op="send", dry_run=True)
        quiet = len(way.tries) - tried
        # a member's own look reads the same refusal and keeps it
        member_first = call(member, op="send")
        member_page = team_sync.status(member["root"])
        # nothing small waits in the outbox is sent either (the review's L1)
        # the lead's switch to a shared folder while the project is gone is no error (the review's M2)
        shared = lead["root"].parent / "shared-gone"
        shared.mkdir(exist_ok=True)
        switch = ""
        try:
            call(lead, op="set", route="folder", folder=str(shared))
        except Exception as exc:  # noqa: BLE001
            switch = str(exc)
        at(lead)
        routed = team_sync.team_on(lead["root"]).get("route")
        call(lead, op="set", route="relay")
    finally:
        transport.OVERRIDE = loop
    import relay_transport as rt_mod
    from datetime import datetime, timedelta, timezone
    left = (datetime.fromisoformat(hold.get("until", "2000-01-01T00:00:00+00:00")) - datetime.now(timezone.utc)).total_seconds()
    data = team_sync.team_on(lead["root"])
    elsewhere = {"hold": dict(hold)}
    team_sync.lift_gone(dict(data, route="folder"), elsewhere)
    renamed = {"hold": dict(hold)}
    team_sync.lift_gone(dict(data, roster=dict(data["roster"], relay={"project": "another", "open": True})), renamed)
    same = {"hold": dict(hold)}
    team_sync.lift_gone(data, same)
    check("349: a project the relay no longer holds is a hold of its own, said on the page in its own line and not as no "
          "connection, with no call after it in either direction, kept an hour, and let go once the team sends "
          "through another route or names another project",
          first["sent"] == [] and not first["offline"] and page["held"] == i18n.t("team.held.gone")
          and not page["offline"] and hold.get("word") == "gone" and hold.get("project") == "" and quiet == 0
          and 3000 < left <= 3600 and member_page["held"] == i18n.t("team.held.gone")
          and team_sync.refused_word(rt_mod.RelayError(404, "no project")) == "gone"
          and team_sync.refused_word(rt_mod.RelayError(404, "not started")) == ""
          and switch == "" and routed == "folder"
          and elsewhere["hold"] == {} and renamed["hold"] == {} and same["hold"] == hold and not member_first["offline"],
          json.dumps({"first": first.get("sent"), "page": page, "hold": hold, "quiet": quiet, "left": left,
                      "member": member_page}))
    st = state_of(lead)
    st["hold"] = {}
    team_sync.save_state(lead["root"], st)
    st = state_of(member)
    st["hold"] = {}
    team_sync.save_state(member["root"], st)
    # the refusals of the list of computers say what comes next, the day's one after midnight too
    refused = {"list_refused": {"word": "lists today", "until": "2000-01-01T00:00:00+00:00"}}
    removed = {"list_refused": {"word": "too many removed", "until": ""}}
    check("349: the line for a list of computers refused for the day says what comes next and stays until a list is "
          "taken, and the one for too many removed computers says it does not lift by itself",
          team_sync.list_refused_line(refused) == i18n.t("team.held.list_today")
          and "midnight UTC" in i18n.t("team.held.list_today") and "sends the list again" in i18n.t("team.held.list_today")
          and team_sync.list_refused_line(removed) == i18n.t("team.held.list_removed")
          and "does not lift by itself" in i18n.t("team.held.list_removed"),
          json.dumps({"today": team_sync.list_refused_line(refused), "removed": team_sync.list_refused_line(removed)}))
    mark(lead, 1, "Wren")
    # the lead's own look sends the list again once the day it was refused for has ended (the review's L3)
    sent_lists = []
    state = state_of(lead)
    state["list_refused"] = {"word": "lists today", "until": "2000-01-01T00:00:00+00:00"}
    team_sync.save_state(lead["root"], state)
    # a dry run with that refusal due calls no relay and leaves sync.json as it was, byte for byte
    kept_file = team_sync.state_path(lead["root"])
    before_bytes = kept_file.read_bytes()
    dry_tries = []
    way = Loopback(None, set_devices=lambda *a, **k: dry_tries.append(a) or {})
    transport.OVERRIDE = lambda dev, data, way=way: (setattr(way, "inner", loop(dev, data)) or way)
    try:
        call(lead, op="send", dry_run=True)
    finally:
        transport.OVERRIDE = loop
    check("349: a dry run send with the day's refusal due calls no relay and leaves sync.json byte for byte",
          not dry_tries and not way.tries and kept_file.read_bytes() == before_bytes, str(dry_tries))
    way = Loopback(None, set_devices=lambda *a, **k: sent_lists.append(a) or {})
    transport.OVERRIDE = lambda dev, data, way=way: (setattr(way, "inner", loop(dev, data)) or way)
    try:
        team_sync.resend_list(lead["root"], team_sync.team_on(lead["root"]))
    finally:
        transport.OVERRIDE = loop
    check("349: the lead's look sends the list of computers again once the day it was refused for has ended, and the "
          "refusal is cleared when the relay takes it",
          len(sent_lists) == 1 and not state_of(lead).get("list_refused"), str(sent_lists))
    mark(lead, 1, "Wren")
    call(lead, op="send")
    call(member, op="send")

    # h. a version too large for a message goes as a sealed blob and the member takes it in whole (review2's N1:
    # every version over INLINE_MOST was dropped as could_not_read, its file freed)
    inline = team_sync.INLINE_MOST
    team_sync.INLINE_MOST = 1024
    blobs_before = len(hub.blobs)
    try:
        mark(lead, 1, "Wren", op="reopen")
        went = call(lead, op="send")
        took = call(member, op="send")
    finally:
        team_sync.INLINE_MOST = inline
    wren_lead = progress(lead, 1, "Wren")
    wren_member = progress(member, 1, "Wren")
    check("349: a version too large for a message goes as a sealed blob, and the member's look fetches it and takes "
          "the participant in whole",
          went["sent"] == ["P1 - Wren"] and took["applied"] == ["P1 - Wren"] and len(hub.blobs) > blobs_before
          and sha(wren_lead) == sha(wren_member), json.dumps({"went": went, "took": took}))
    mark(lead, 1, "Wren")
    call(lead, op="send")
    call(member, op="send")

    # h2. the same at the real size (relayfix3, review's R3): a version of over 640 KB zipped, INLINE_MOST left as it
    # ships, goes as a sealed blob and comes in whole. A LPETs file of random text in Working makes it so
    assert team_sync.INLINE_MOST == 640 * 1024
    bulk = lead["root"] / "P1 - Wren" / "Working" / (book(lead, 1, "Wren").stem + ".lpets.json")
    bulk.parent.mkdir(exist_ok=True)
    bulk.write_text(base64.b64encode(os.urandom(1000 * 1024)).decode("ascii") + "\n", encoding="utf-8")
    blobs_before = len(hub.blobs)
    mark(lead, 1, "Wren", op="reopen")
    went = call(lead, op="send")
    took = call(member, op="send")
    big_member = member["root"] / "P1 - Wren" / "Working" / (book(lead, 1, "Wren").stem + ".lpets.json")
    check("349: a version over 640 KB, as it ships and not with the limit lowered, goes as a sealed blob through the "
          "loopback and the member's look takes the participant in whole, the large file too",
          went["sent"] == ["P1 - Wren"] and took["applied"] == ["P1 - Wren"] and len(hub.blobs) > blobs_before
          and max(len(v) for v in hub.blobs.values()) > team_sync.INLINE_MOST
          and big_member.is_file() and sha(bulk) == sha(big_member)
          and sha(progress(lead, 1, "Wren")) == sha(progress(member, 1, "Wren")),
          json.dumps({"went": went, "took": took, "blobs": [len(v) for v in hub.blobs.values()]}))
    bulk.unlink()
    big_member.unlink(missing_ok=True)
    mark(lead, 1, "Wren")
    call(lead, op="send")
    call(member, op="send")


def relay_part(scratch, lead, member, call, mark, sha, book, progress, at):
    import transport
    import team
    from .a342_relay import CODE, free_port, miniflare_folder
    node = shutil.which("node")
    folder = miniflare_folder()
    if not node or not folder:
        return skip("349: owners and versions through the relay", "no node or no Miniflare on this machine")
    import sys
    sys.path.insert(0, str(support.source("family")))
    import relay_transport as rt
    port = free_port()
    child = subprocess.Popen([node, str(support.source("relay/test/serve.mjs")), "--port", str(port), "--codes", CODE,
                              "--miniflare", str(folder)], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                             stderr=subprocess.STDOUT, cwd=str(scratch), encoding="utf-8", errors="replace")
    said, ready = [], threading.Event()

    def read():
        for line in child.stdout:
            said.append(line.rstrip())
            if line.startswith("ready "):
                ready.set()
    threading.Thread(target=read, daemon=True).start()
    try:
        if not ready.wait(60):
            return check("349: the relay starts on this computer", False, " | ".join(said[-10:]))
        url = f"http://127.0.0.1:{port}/relay/v1"
        at(lead)
        lead_dev = team.device()
        at(member)
        member_dev = team.device()
        relays = {d["id"]: rt.RelayTransport(base64.b64decode(d["sign"]), url) for d in (lead_dev, member_dev)}
        project = relays[lead_dev["id"]].make_project()
        relays[lead_dev["id"]].set_devices(project, [relays[lead_dev["id"]].public_key,
                                                     relays[member_dev["id"]].public_key])
        transport.OVERRIDE = lambda dev, data: Mapped(rt.TeamRelay(relays[dev["id"]]), project)
        recording = lead["root"] / "P1 - Wren" / "P1 Wren.m4a"
        recording.write_bytes(os.urandom(1200 * 1024))
        mark(lead, 1, "Wren", op="reopen")
        sent = call(lead, op="send")
        # the member's looks, as the app's come every few seconds, until it has come or ten seconds have passed: a
        # relay under load may answer a look late or not at all, and the next look reads it (teamflake)
        tries, deadline = [], time.monotonic() + 10
        while True:
            took = call(member, op="send")
            tries.append({k: took.get(k) for k in ("applied", "offline")})
            if took.get("applied") or time.monotonic() > deadline:
                break
            time.sleep(0.25)
        refused = ""
        try:
            mark(member, 1, "Wren", op="reopen")
        except Exception as exc:
            refused = str(exc)
        check("349: through the relay the lead's change to Wren, a recording over a message's size among it as a blob "
              "in R2, reaches the member's copy, which still refuses his write",
              sent["sent"] == ["P1 - Wren"] and took["applied"] == ["P1 - Wren"]
              and sha(progress(lead, 1, "Wren")) == sha(progress(member, 1, "Wren"))
              and sha(recording) == sha(member["root"] / "P1 - Wren" / "P1 Wren.m4a") and "Wren is Ada's" in refused,
              json.dumps({"sent": sent.get("sent"), "tries": tries, "refused": refused, "lead": trace(lead),
                          "member": trace(member)}))

        # a version too large for a message, through the relay as a named file in R2 (review2's N1)
        import team_sync
        inline = team_sync.INLINE_MOST
        team_sync.INLINE_MOST = 1024
        try:
            mark(lead, 1, "Wren")
            big = call(lead, op="send")
        finally:
            team_sync.INLINE_MOST = inline
        big_tries, deadline = [], time.monotonic() + 10
        while True:
            took_big = call(member, op="send")
            big_tries.append({k: took_big.get(k) for k in ("applied", "offline")})
            if took_big.get("applied") or time.monotonic() > deadline:
                break
            time.sleep(0.25)
        check("349: through the relay a version too large for a message goes as a file in R2, and the member's look "
              "fetches it and takes the participant in whole",
              big["sent"] == ["P1 - Wren"] and took_big["applied"] == ["P1 - Wren"]
              and sha(progress(lead, 1, "Wren")) == sha(progress(member, 1, "Wren")),
              json.dumps({"sent": big.get("sent"), "tries": big_tries, "lead": trace(lead), "member": trace(member)}))

        # the same at the real size, INLINE_MOST as it ships: a LPETs file of random text makes the version over 640 KB
        bulk = lead["root"] / "P1 - Wren" / "Working" / (book(lead, 1, "Wren").stem + ".lpets.json")
        bulk.parent.mkdir(exist_ok=True)
        bulk.write_text(base64.b64encode(os.urandom(1000 * 1024)).decode("ascii") + "\n", encoding="utf-8")
        mark(lead, 1, "Wren", op="reopen")
        real = call(lead, op="send")
        real_tries, deadline = [], time.monotonic() + 15
        while True:
            took_real = call(member, op="send")
            real_tries.append({k: took_real.get(k) for k in ("applied", "offline")})
            if took_real.get("applied") or time.monotonic() > deadline:
                break
            time.sleep(0.25)
        there = member["root"] / "P1 - Wren" / "Working" / (book(lead, 1, "Wren").stem + ".lpets.json")
        check("349: through the relay a version over 640 KB, with the limit as it ships, goes as a file in R2 and "
              "the member's look takes the participant in whole, the large file too",
              real["sent"] == ["P1 - Wren"] and took_real["applied"] == ["P1 - Wren"]
              and there.is_file() and sha(bulk) == sha(there)
              and sha(progress(lead, 1, "Wren")) == sha(progress(member, 1, "Wren")),
              json.dumps({"sent": real.get("sent"), "tries": real_tries, "there": there.is_file(), "size": bulk.stat().st_size,
                          "same": there.is_file() and sha(bulk) == sha(there)}))
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
