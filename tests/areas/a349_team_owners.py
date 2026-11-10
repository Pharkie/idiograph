"""Area 349: Working together's owners and versions (wtowners, 8 November 2026, the spec's build 2, Adam's choices
that evening about 19:10: all the spec's defaults, what came in and what waits under the project's question). Two
scratch installs in one process, each its own settings folder, device file and project, paired over the loopback
transport, then once more through the relay run on this computer under Miniflare as area 342 runs it.

What matters: a new member gets a first full copy, a recording over a message's size going as a sealed blob. The
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

        # 7. through the relay, run on this computer as area 342 runs it
        relay_part(scratch, lead, member, call, mark, sha, book, progress, at)
    finally:
        (server_mod.CONFIG_PATH, server_mod.ROOT_OVERRIDE, team.DEVICE_PATH, transport.OVERRIDE, team_sync.WAIT) = kept


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
        project = relays[lead_dev["id"]].make_project(CODE)
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
