"""Every change an agent makes, recorded, and a restore point for each of its runs (noholds, 13 November 2026).

Adam, 13 November 2026, on the holds that made an agent's deletes, merges and replaces wait for his yes: "approvals
theatre ... if someone's using AI agents, they're doing it because they want to make mass changes quickly ... Let's
assume that AI agents act intelligently, but also provide a safety net if they don't ... review afterwards, across
the board". So an agent's op runs at once, as it ran with Dangerously skip permissions on, and this module is the
net, the same for everyone with no setting:

- The ops undo cannot reach are the app's alone (`APP_ONLY`): an agent asking for one is refused in a plain line
  naming where to do it in the app, nothing waiting. Its dry run still answers.
- Every write an agent makes, through the command line or the MCP server, is one line in the project's change
  record, `idiograph-agent-changes.jsonl` at its root: when, the agent by its tool, the run, the request it gave
  (`--note`), the op and its target (participant, board, sheet and row), what changed in a line, said by which of
  the project's files changed, and how to undo it, the run's restore point and the op's own undo where it has one
  (a board's revision, the workbook copy kept, a replace's or an assignment's undo id). Never a participant's words:
  the target is named by pseudonym, board name, sheet and row, and the line by the files' kinds.
- A run is the agent's session: one MCP connection, the writes of the command line sharing a `--run` id, or those
  from the same tool within IDLE minutes of each other. A connection's writes more than IDLE minutes apart start a
  new run too, so a client left open for days is not one run of days.
- Before a run's first write the project's working files are kept as its restore point: every workbook and every
  JSON file of the project (`tracked`), its archive copies, its History, Working together's files and this module's
  own left out, the list of real names kept since namesop (16 November 2026) so an agent's add is undone, mode 600. They are kept once by their contents in `.idiograph-restore/objects`, so a
  file unchanged since an earlier restore point costs nothing again and the next point copies only what changed
  since. Each write's files are read before and after it by their size and time alone, so the run knows which
  files it changed, which it made, and which changed between its writes by someone else.
- `undo_run` puts back every file the run changed as it was before the run's first write, and takes away the files
  it made, keeping them first, as a run of its own that can be undone in its turn. A file changed since the run's
  last write, or by someone else between its writes, would lose that change, so the undo is refused whole, naming
  each, nothing written. A run that renamed a participant's folder is refused too, until the folder is renamed back.

Kept: restore points for KEEP_DAYS days after their run's last write, and the last KEEP_RUNS whatever their age,
the copies no point names any more taken away as a new point is made. The change record is kept whole.

Review afterwards (agentreview2, 13 November 2026, Adam by dialog: "C, with A's Home line"). Project history's By an
agent reads the record grouped by run (`review`), each change a plain line with its own Undo and each run with Undo
this run, and Home's project card says how many changes agents made since he last looked (`unseen`), from two small
files in the store, `tally.json`, kept up to date as each line is written, and `seen.json`, written as By an agent is
read, so Home never reads the record itself. Each write now keeps its files as they stood before and after it, by
their contents, in its run's `steps`, so one change is undone alone (`undo_changes`, `agents undo-change`): every
file it changed put back as it stood just before it, refused, nothing written, while anything has changed one of
them since, the researcher's own edit or a later change of an agent's. The op's own undo (`undo_with`) stays in the
record for agents: a board's revision restored takes back every later change on that board too, his among them, so
the page never uses it.
"""
from __future__ import annotations

import contextlib
import hashlib
import json
import os
import re
import secrets
import tempfile
from datetime import datetime, timedelta
from pathlib import Path

import agent_log
import i18n
import locks
import server as srv

FILE = "idiograph-agent-changes.jsonl"
STORE = ".idiograph-restore"
# how many changes agents have made and the newest's number, and how many he had seen, for Home's line (agentreview2)
TALLY = "tally.json"
SEEN = "seen.json"
# the runs By an agent reads at a time
REVIEW_RUNS = 20
# the agents' lock's ending (see `held`)
LOCK = locks.NAME
IDLE = 30
KEEP_DAYS = 30
KEEP_RUNS = 10
WORDS_MOST = 2000
# what a restore point keeps: the workbooks and every JSON file, and of those never these, by name, wherever they
# stand: the project's History, Working together's team file, the holds file of before, and a shared copy's own
# record
TRACKED = (".xlsx", ".json")
# and in a boards file's History folder beside it, its chunks (historybuild, 16 November 2026), kept by their contents
# like any file, so a sealed chunk costs nothing again
CHUNKS = ".jsonl"
NEVER = frozenset(("idiograph-history.json", "team.json", "idiograph-holds.json", "idiograph-sent.json"))
# The list of real names (namesop, 16 November 2026, Adam: an agent adds entries on his word). Kept by restore points
# since then, so an agent's add is undone like any write: its copies stand in this store, in the project's own hidden
# `.idiograph-restore` beside the list itself, mode 600, which a shared copy (`project_pack.LEFT_OUT`), Working
# together's sync (hidden folders) and every export leave out, so the names reach nowhere the list does not
NAMES = "idiograph-names.json"
# folders never walked: archive copies, which a run only adds to, and every hidden folder, this store and Working
# together's among them
SKIP_DIRS = frozenset(("_Archive",))
# the suite's own: a check of this module names the clock
NOW = None
# and the suite's own again: its checks of Working together and the other ops only the app does drive them through the
# command line as they did before, and areas 321, 351, 357, 368 and 380 check the refusals. No agent's call has a way
# to it
ALL_OPS: bool | None = None

# The four risks an agent brings, as the head of docs/agents.md names them (agentholds, Adam, 2 November 2026, from
# Harbour's): 1, steering, it acts on text it reads, which anyone may have written. 2, speed and volume, it does in a
# minute what he does in a day. 3, no screen, it can act on the wrong thing with nobody looking. 4, standing access,
# a setting that outlives the conversation. The record and a run's undo answer 2 and 3, the ops only the app does 1
# and 4, and each route the page keeps to itself names the one it answers (area 261).
RISKS = {1: "steering", 2: "speed and volume", 3: "no screen", 4: "standing access"}

# The ops undo cannot reach (Adam, 13 November 2026, by dialog: "app only"), refused for agents with the place in
# the app that does each, nothing waiting. Sending to another person, Working together's outward ops, its keys and
# relay codes, and who is on the team. Settings, which are the app's and no project's, so no restore point holds
# them (Your name, the AI prompt, the AI's provider, address and model, the AI switch and keys having no op). The
# list of real names is no longer among them: since namesop (16 November 2026, Adam's word) an agent adds entries, which
# restore points reach, and since namesset the same day (Adam: "if you're not able to do it via MCP or the API, you
# should be able to") it changes and takes them off by number, each undone the same way. Removing a project from
# Idiograph stays an agent's, its folder moved to the Trash or left as it is, never deleted.
TEAM_ONLY = ("on", "set", "invite", "admit", "join", "joined", "send", "remove", "lead", "board-send",
             "board-answer", "ask", "review-send", "reply", "thread", "review-done", "suggestion-answer")
SETTINGS_KEYS = ("your_name", "ai_prompt_file", "ai_prompt_default", "ai_provider", "ai_address", "ai_deployment",
                 "ai_model")


def app_only(args) -> str:
    """The line refusing an op only the app does, or "" for any other. A dry run is never refused: it writes
    nothing, and tells the agent what the app would do."""
    command, act = getattr(args, "command", None), getattr(args, "act", None)
    if command == "team" and act in TEAM_ONLY:
        return i18n.t("agentchanges.only.team")
    if (command, act) == ("project", "send"):
        return i18n.t("agentchanges.only.send")
    if command == "settings" and act is None and any(getattr(args, k, None) not in (None, False) for k in SETTINGS_KEYS):
        return i18n.t("agentchanges.only.settings")
    return ""


# an export writes a file of its own and changes nothing of the project, so it is no change to record


# ------------------------------------------------------------------ the clock and the places

def now() -> datetime:
    return NOW() if callable(NOW) else datetime.now().astimezone()


def stamp(when: datetime | None = None) -> str:
    return (when or now()).isoformat(timespec="seconds")


def parsed(iso) -> datetime | None:
    try:
        d = datetime.fromisoformat(str(iso))
    except (TypeError, ValueError):
        return None
    return d if d.tzinfo else d.astimezone()


def one_line(text) -> str:
    return " ".join(str(text or "").split())


def record_path(root) -> Path:
    return Path(root) / FILE


def store(root) -> Path:
    return Path(root) / STORE


def held(root):
    """The agents' lock of a project, held for an agent's whole write, so two agents' writes on one project take
    turns and each one's files are read before and after it alone. It stands in the system's own folder for passing
    files, named by the project's folder, never in the project, so a write refused or writing nothing leaves the
    project exactly as it was."""
    key = hashlib.sha1(str(Path(root).resolve()).encode("utf-8")).hexdigest()[:16]
    return locks.held(Path(tempfile.gettempdir()) / f"idiograph-agents-{key}{LOCK}")


def kept_here(root) -> bool:
    """Whether a project keeps a record: every one but the two demos, which ship as they are, as History keeps none."""
    return root is not None and Path(root).is_dir() and not srv.is_demo_root(root)


# ------------------------------------------------------------------ the files

def is_memos(folder: str, name: str) -> bool:
    """Whether a file is a participant's memos file in their Source folder (`<folder>/Source/<x> - memos.txt`), which
    an agent's `names replace` writes (wordfix2, 16 November 2026), so a restore point keeps it like a workbook and
    the replace is undone byte for byte."""
    import names as names_mod
    parts = folder.split("/")
    return len(parts) == 2 and parts[1] == "Source" and bool(names_mod.MEMOS_FILE.match(name))


def tracked(root) -> dict:
    """Every file a restore point keeps, by its path from the root with forward slashes, with its time and size:
    the workbooks and the JSON files, never NEVER's, and each participant's memos files in Source (`is_memos`), under
    no hidden folder nor an _Archive."""
    root = Path(root)
    out = {}
    for here, dirs, files in os.walk(root):
        dirs[:] = sorted(d for d in dirs if not d.startswith(".") and d not in SKIP_DIRS)
        for name in files:
            if name.startswith((".", "~$")) or name in NEVER:
                continue
            if not (name.lower().endswith(TRACKED) or (name.endswith(CHUNKS) and here.endswith(".history"))
                    or is_memos(Path(here).relative_to(root).as_posix(), name)):
                continue
            path = Path(here) / name
            try:
                st = path.stat()
            except OSError:
                continue
            out[path.relative_to(root).as_posix()] = [st.st_mtime_ns, st.st_size]
    return out


def moved(before: dict, after: dict) -> list:
    """The files that differ between two readings, made, changed or gone, sorted."""
    return sorted(f for f in set(before) | set(after) if before.get(f) != after.get(f))


def objects(root) -> Path:
    return store(root) / "objects"


def read_in(root, rel: str) -> tuple[bytes, list] | None:
    """A file's bytes and the time and size it had as it was read, read again when it changed under the read. None
    when it cannot be read."""
    path = Path(root) / rel
    for _ in range(3):
        try:
            st = path.stat()
            data = path.read_bytes()
            again = path.stat()
        except OSError:
            return None
        if (st.st_mtime_ns, st.st_size) == (again.st_mtime_ns, again.st_size):
            break
    return data, [again.st_mtime_ns, again.st_size]


def keep(root, sha: str, data: bytes) -> None:
    """A copy kept by its contents in the store, once whatever its name."""
    target = objects(root) / sha
    if not target.is_file():
        target.parent.mkdir(parents=True, exist_ok=True)
        tmp = target.with_name(f".{sha}.{secrets.token_hex(4)}")
        # read by its owner alone, as the list of names it may be a copy of is (namesop)
        fd = os.open(tmp, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
        with os.fdopen(fd, "wb") as fh:
            fh.write(data)
        os.replace(tmp, target)


def put_back(tmp: Path, data: bytes, rel: str) -> None:
    """A file an undo puts back written to its temporary name, the list of names made mode 600 from its first byte,
    as the list's own write makes it, so it is never readable by others on the way (namesop)."""
    if rel.split("/")[-1] != NAMES:
        tmp.write_bytes(data)
        return
    fd = os.open(tmp, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    with os.fdopen(fd, "wb") as fh:
        fh.write(data)
    with contextlib.suppress(OSError):
        os.chmod(tmp, 0o600)


def secret_words(root, args=None) -> list[str]:
    """The words no agent's request may keep as the record, History or the agent log write it (namesop): every
    spelling and except phrase of the project's list of names, and those an op was given (`args.secret_words`,
    `names add`'s), longest first."""
    import names as names_mod
    words = set(str(w) for w in (getattr(args, "secret_words", None) or ()) if str(w).strip())
    if root is not None:
        for e in names_mod.entries_at(root):
            words.update(e.get("real") or [])
            words.update(e.get("except") or [])
    return sorted({w.strip() for w in words if w.strip()}, key=len, reverse=True)


def hide_request(root, args) -> None:
    """An agent's request with the project's real names taken out before anything writes it (namesop): `args.note`
    rewritten in place, and `args.secret_words` holding the words, for the agent log's refusals to take out too."""
    words = secret_words(root, args)
    args.secret_words = words
    if getattr(args, "note_raw", None) is None:
        # his words as given, kept in memory alone, so a longer name given later is taken out whole
        args.note_raw = getattr(args, "note", None) or ""
    if words and getattr(args, "note", None):
        args.note = agent_log.hidden_words(args.note_raw, words)


def copy_in(root, rel: str) -> tuple[str, list] | None:
    """A file kept by its contents in the store, and its sha and the time and size it had as it was read."""
    got = read_in(root, rel)
    if got is None:
        return None
    sha = hashlib.sha256(got[0]).hexdigest()
    keep(root, sha, got[0])
    return sha, got[1]


# ------------------------------------------------------------------ the runs

def runs_dir(root) -> Path:
    return store(root) / "runs"


def run_path(root, rid: str) -> Path:
    return runs_dir(root) / f"{rid}.json"


def load_run(root, rid: str) -> dict | None:
    try:
        data = json.loads(run_path(root, rid).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    return data if isinstance(data, dict) and data.get("id") == rid else None


def save_run(root, run: dict) -> None:
    path = run_path(root, run["id"])
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(f".{path.name}.{secrets.token_hex(4)}")
    tmp.write_text(json.dumps(run, ensure_ascii=False, indent=1) + "\n", encoding="utf-8", newline="\n")
    locks.replace(tmp, path)


def all_runs(root) -> list[dict]:
    """Every run the store keeps, the newest started last."""
    out = []
    try:
        names = sorted(runs_dir(root).glob("r*.json"))
    except OSError:
        return []
    for f in names:
        run = load_run(root, f.stem)
        if run is not None:
            out.append(run)
    return sorted(out, key=lambda r: (str(r.get("started") or ""), number(r["id"])))


def number(rid: str) -> int:
    m = re.fullmatch(r"r(\d+)", str(rid or ""))
    return int(m.group(1)) if m else 0


def next_id(root) -> str:
    """The next run's id, r1, r2, never one given before, though its run is gone."""
    index = store(root) / "index.json"
    try:
        n = int(json.loads(index.read_text(encoding="utf-8")).get("next") or 1)
    except (OSError, ValueError, TypeError, AttributeError):
        n = 1
    n = max([n] + [number(r["id"]) + 1 for r in all_runs(root)])
    index.parent.mkdir(parents=True, exist_ok=True)
    tmp = index.with_name(f".index.{secrets.token_hex(4)}")
    tmp.write_text(json.dumps({"next": n + 1}) + "\n", encoding="utf-8", newline="\n")
    locks.replace(tmp, index)
    return f"r{n}"


def session_of(args) -> tuple[str, bool]:
    """The session an agent's write belongs to, and whether it is named outright: the MCP connection's, the
    `--run` the command line was given, or the command line's tool, whose writes within IDLE minutes are one run."""
    given = one_line(getattr(args, "run", "") or "")
    if given:
        return f"run:{given}", True
    session = one_line(getattr(args, "session", "") or "")
    if session:
        return session, False
    tool = one_line(getattr(args, "tool", "") or "").lower()
    return f"cli:{tool}", False


def current_run(root, args) -> dict | None:
    """The run this write belongs to, or None for a new one: a `--run` naming a run's id, r4, or its session, or the
    session's latest run while its last write was within IDLE minutes."""
    key, named = session_of(args)
    runs = all_runs(root)
    given = one_line(getattr(args, "run", "") or "")
    by_id = next((r for r in runs if r["id"].lower() == given.lower()), None) if given else None
    if by_id is not None and not by_id.get("undone"):
        return by_id
    mine = [r for r in runs if r.get("key") == key and not r.get("undone") and not r.get("undoes")
            and not r.get("undoes_changes")]
    if not mine:
        return None
    last = mine[-1]
    if named:
        return last
    when = parsed(last.get("last"))
    return last if when is not None and now() - when <= timedelta(minutes=IDLE) else None


def point(root) -> tuple[dict, dict]:
    """The project's tracked files as they stand, each by its contents' sha, a file unchanged since an earlier point
    taking that point's copy with no read, and the copies the store lacks, held in memory until the run is kept
    (`keep_run`), so a run whose first op writes nothing leaves nothing behind."""
    known = {}
    for run in all_runs(root):
        for rel, e in (run.get("point") or {}).items():
            if isinstance(e, dict) and e.get("sha"):
                known[(rel, tuple(e.get("stat") or ()))] = e["sha"]
    out, pending = {}, {}
    for rel, st in tracked(root).items():
        sha = known.get((rel, tuple(st)))
        if sha and (objects(root) / sha).is_file():
            out[rel] = {"sha": sha, "stat": st}
            continue
        got = read_in(root, rel)
        if got is not None:
            sha = hashlib.sha256(got[0]).hexdigest()
            out[rel] = {"sha": sha, "stat": got[1]}
            pending[sha] = got[0]
    return out, pending


def new_run(root, args, via: str, agent: str, undoes: str = "") -> dict:
    """A new run with its restore point, the files as they stand before its first write, kept nowhere yet: no id and
    its copies in memory until `keep_run`."""
    key, _named = session_of(args) if not undoes else (f"undo:{undoes}", True)
    at = stamp()
    files, pending = point(root)
    run = {"id": "", "key": key, "via": via, "agent": agent, "started": at, "last": at, "point": files,
           "changed": [], "made": [], "foreign": [], "changes": 0, "_pending": pending}
    run["after"] = {rel: e["stat"] for rel, e in files.items()}
    if undoes:
        run["undoes"] = undoes
    return run


def keep_run(root, run: dict) -> dict:
    """A new run kept once it has written: old points let go first, its copies written and its id given."""
    tidy(root, run)
    for sha, data in (run.pop("_pending", None) or {}).items():
        keep(root, sha, data)
    run["id"] = next_id(root)
    save_run(root, run)
    return run


def sweep(root, kept: list) -> None:
    """Every copy in the store that no kept run names taken away."""
    named = {e.get("sha") for r in kept for e in (r.get("point") or {}).values() if isinstance(e, dict)}
    named |= {sha for r in kept for sha in (r.get("kept_made") or {}).values()}
    # and each change's own copies, before and after it (agentreview2)
    named |= {s.get(k) for r in kept for step in (r.get("steps") or {}).values() if isinstance(step, dict)
              for s in step.values() if isinstance(s, dict) for k in ("before", "after")}
    try:
        for f in objects(root).iterdir():
            if f.is_file() and not f.name.startswith(".") and f.name not in named:
                f.unlink()
    except OSError:
        pass


def tidy(root, new: dict | None = None) -> None:
    """Restore points older than KEEP_DAYS days after their run's last write let go, the last KEEP_RUNS kept
    whatever their age, and every copy no point names taken away, the `new` run's own among those named."""
    runs = all_runs(root)
    edge = now() - timedelta(days=KEEP_DAYS)
    keep_ids = {r["id"] for r in runs[-KEEP_RUNS:]}
    kept = []
    for r in runs:
        when = parsed(r.get("last"))
        if r["id"] in keep_ids or (when is not None and when > edge):
            kept.append(r)
            continue
        try:
            run_path(root, r["id"]).unlink()
        except OSError:
            pass
    if len(kept) < len(runs):
        sweep(root, kept + ([new] if new else []))


# ------------------------------------------------------------------ what a file is, as a line says it

ROOT_KINDS = {"idiograph-project.json": "project", "idiograph-gets.json": "gets", "idiograph-lgets.json": "lgets",
              NAMES: "names",
              "idiograph-trajectories.json": "trajectories", "idiograph-codes.json": "codes"}
# each kind's words, by its key in full
KIND_SAID = {"project": lambda: i18n.t("agentchanges.kind.project"), "gets": lambda: i18n.t("agentchanges.kind.gets"),
             "lgets": lambda: i18n.t("agentchanges.kind.lgets"),
             "trajectories": lambda: i18n.t("agentchanges.kind.trajectories"),
             "codes": lambda: i18n.t("agentchanges.kind.codes"),
             "names": lambda: i18n.t("agentchanges.kind.names"),
             "project_files": lambda: i18n.t("agentchanges.kind.project_files")}
PART_SAID = {"transcript": lambda: i18n.t("agentchanges.part.transcript"),
             "boards": lambda: i18n.t("agentchanges.part.boards"),
             "working": lambda: i18n.t("agentchanges.part.working"),
             "memos": lambda: i18n.t("agentchanges.part.memos")}


def case_names(p) -> dict:
    """Each participant's folder by its name, their pseudonym as every line names them."""
    import gets as gets_mod
    import workbook as wb_mod
    out = {}
    for b in getattr(p, "books", None) or []:
        try:
            out[wb_mod.case_folder(Path(b["workbook"])).name] = gets_mod.who(str(b["case"]))
        except (KeyError, TypeError, ValueError):
            continue
    return out


def kind_of(rel: str, names: dict) -> tuple[str, str]:
    """A file as a line says it: its kind and whose, ("boards", "Juno"), ("gets", ""), never its folder's second
    name."""
    parts = rel.split("/")
    if len(parts) == 1:
        return ROOT_KINDS.get(parts[0], "project_files"), ""
    # a root boards file's History, `idiograph-gets.history/<chunk>`, is that file's kind
    if len(parts) == 2 and parts[0].endswith(".history"):
        return ROOT_KINDS.get(parts[0][:-len(".history")] + ".json", "project_files"), ""
    import gets as gets_mod
    who = names.get(parts[0]) or gets_mod.who(srv.display_case(parts[0]))
    name = parts[-1].lower()
    if name.endswith(".xlsx"):
        return "transcript", who
    if is_memos("/".join(parts[:-1]), parts[-1]):
        return "memos", who
    if re.search(r"\.(themes(-t\d+)?|lpets|own)[^/]*\.json$", name) or "themes" in name \
            or (len(parts) > 2 and parts[-2].endswith(".history")):
        return "boards", who
    return "working", who


def said_files(rels, names: dict) -> str:
    """The files said in one line, "Juno's boards and transcript and the GETs", each kind once."""
    import formats
    whose: dict = {}
    for rel in rels:
        kind, who = kind_of(rel, names)
        whose.setdefault(who, [])
        if kind not in whose[who]:
            whose[who].append(kind)
    parts = []
    for who, kinds in whose.items():
        if who:
            parts.append(i18n.t("agentchanges.whose", who=who,
                                what=formats.list_words([PART_SAID[k]() for k in kinds])))
        else:
            parts += [KIND_SAID[k]() for k in kinds]
    return formats.list_words(parts)


def changed_line(changed: list, made: list, names: dict) -> str:
    """What a write changed, in a line by its files: "Juno's boards changed.", "Rowan's transcript made." or
    nothing changed in the project's files."""
    # a History chunk a write began is part of the board it changed, not a file made (asidefix, 17 November 2026)
    made = [f for f in made if not any(part.endswith(".history") for part in f.split("/")[:-1])]
    made_set = set(made)
    old = [f for f in changed if f not in made_set]
    lines = []
    if old:
        lines.append(i18n.t("agentchanges.changed", what=said_files(old, names)))
    if made:
        lines.append(i18n.t("agentchanges.made", what=said_files(made, names)))
    return " ".join(lines) or i18n.t("agentchanges.no_files")


# ------------------------------------------------------------------ the record

def target_of(args, answer: dict) -> dict:
    """What an op worked on, by name: the participant, the board, the sheet and the row, the timepoint, never a
    participant's words."""
    import cli
    answer = answer if isinstance(answer, dict) else {}
    out = {}
    who = answer.get("case") if isinstance(answer.get("case"), str) else None
    who = who or getattr(args, "case", None) or getattr(args, "lpets", None)
    if who:
        out["case"] = cli.scrub(one_line(who))
    if args.command in ("board", "gets"):
        board = getattr(args, "board", None) or (answer.get("name") if isinstance(answer.get("name"), str) else None)
        if isinstance(answer.get("board"), str):
            board = board or answer["board"]
        if board:
            out["board"] = one_line(board)
        if args.command == "gets" and not getattr(args, "lpets", None):
            out["gets"] = True
    # `rows` the passages turn skip names, 12,15,20-22 (leaveout, 16 November 2026)
    for k in ("sheet", "row", "rows", "timepoint"):
        v = getattr(args, k, None)
        if v not in (None, ""):
            out[k] = v if isinstance(v, int) else one_line(v)
    return out


def undo_of(args, answer: dict, rid: str) -> dict:
    """How to undo a change: its run's restore point always, and the op's own undo where it answered one, a board's
    revision made, the workbook copy kept, a replace's or an assignment's or a trim's undo id."""
    import cli
    answer = answer if isinstance(answer, dict) else {}
    out = {"run": rid, "command": f"idiograph agents undo-run {rid}" if rid else ""}
    key = (args.command, getattr(args, "act", None))
    case = answer.get("case") if isinstance(answer.get("case"), str) else getattr(args, "case", None)
    if key == ("transcript", "replace") and answer.get("batch"):
        out.update(batch=str(answer["batch"]), own=f"idiograph transcript replace-undo {answer['batch']}")
    elif key in (("turn", "assign"), ("turn", "trim")) and answer.get("id") and case:
        out.update(id=str(answer["id"]), own=f"idiograph turn {key[1]}-undo {cli.quoted_arg(case)} {answer['id']}")
    if isinstance(answer.get("backup"), str) and answer["backup"]:
        out["copy"] = cli.scrub(Path(answer["backup"]).name)
    rev = answer.get("revision")
    if isinstance(rev, dict) and rev.get("id"):
        out["revision"] = str(rev["id"])
        # and its hash, so its restore takes that revision and no other given its id since (historybuild)
        if rev.get("hash"):
            out["hash"] = str(rev["hash"])
    if args.command == "codes" and key[1] not in ("undo", "redo", "list", "show"):
        out["own"] = "idiograph codes undo"
    return out


def append(root, entry: dict) -> dict:
    """One change into the record, its id the next, under the store's lock the caller holds."""
    path = record_path(root)
    held_now = read(root)
    n = max([change_number(e.get("id")) for e in held_now] + [0])
    entry = dict({"id": f"c{n + 1}"}, **entry)
    with open(path, "a", encoding="utf-8", newline="\n") as fh:
        fh.write(json.dumps(entry, ensure_ascii=False) + "\n")
    write_tally(root, held_now + [entry])
    return entry


def change_number(cid) -> int:
    m = re.fullmatch(r"c(\d+)", str(cid or ""))
    return int(m.group(1)) if m else 0


def by_agent(e: dict) -> bool:
    """Whether a line of the record is an agent's change, not an undo pressed in the app (agentreview2)."""
    return str(e.get("via") or "") != "app"


def small(path: Path) -> dict | None:
    try:
        data = json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    return data if isinstance(data, dict) else None


def write_small(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(f".{path.name}.{secrets.token_hex(4)}")
    tmp.write_text(json.dumps(data) + "\n", encoding="utf-8", newline="\n")
    locks.replace(tmp, path)


def tally_of(entries: list) -> dict:
    """How many changes agents made and the newest change's number, from the record's lines."""
    return {"agents": sum(1 for e in entries if by_agent(e)),
            "last": max([change_number(e.get("id")) for e in entries] + [0])}


def write_tally(root, entries: list) -> dict:
    tally = tally_of(entries)
    write_small(store(root) / TALLY, tally)
    return tally


def unseen(root) -> int:
    """How many changes agents made since he last looked at By an agent, for Home's line: two small files read,
    never the record, and a project with no record nothing read at all. A record from before the tally is counted
    once and its tally kept."""
    if root is None or not record_path(root).is_file():
        return 0
    tally = small(store(root) / TALLY)
    if tally is None:
        tally = write_tally(root, read(root))
    seen = small(store(root) / SEEN) or {}
    try:
        return max(0, int(tally.get("agents") or 0) - int(seen.get("agents") or 0))
    except (TypeError, ValueError):
        return 0


def mark_seen(root) -> dict:
    """Every change in the record so far seen, as By an agent shows them: Home's line goes, and New with it."""
    tally = small(store(root) / TALLY) or write_tally(root, read(root))
    seen = {"agents": int(tally.get("agents") or 0), "last": int(tally.get("last") or 0), "at": stamp()}
    write_small(store(root) / SEEN, seen)
    return seen


def read(root) -> list[dict]:
    """Every change the record keeps, oldest first, a line that cannot be read passed over."""
    try:
        lines = record_path(root).read_text(encoding="utf-8").splitlines()
    except OSError:
        return []
    out = []
    for line in lines:
        try:
            e = json.loads(line)
        except ValueError:
            continue
        if isinstance(e, dict):
            out.append(e)
    return out


def take_out(root, cid: str) -> None:
    """A change taken back out of the record, for an op that failed after its line was written first."""
    kept = [e for e in read(root) if e.get("id") != cid]
    path = record_path(root)
    tmp = path.with_name(f".{path.name}.{secrets.token_hex(4)}")
    tmp.write_text("".join(json.dumps(e, ensure_ascii=False) + "\n" for e in kept), encoding="utf-8", newline="\n")
    locks.replace(tmp, path)
    if store(root).is_dir():
        write_tally(root, kept)


def names_said(args, answer) -> str:
    """What a names set or names remove changed, for the record's line and By an agent: the entry's number and the
    fields by their names alone, never a word of the list (namesset review), "" for any other op."""
    key = (args.command, getattr(args, "act", None))
    answer = answer if isinstance(answer, dict) else {}
    if key == ("names", "set") and isinstance(answer.get("changed"), dict) and answer.get("entry"):
        changed = answer["changed"]
        fields = []
        if "review" in changed:
            fields.append(i18n.t("names.record_field.review_on") if changed["review"].get("after")
                          else i18n.t("names.record_field.review_off"))
        if "word" in changed:
            fields.append(i18n.t("names.record_field.word_on") if changed["word"].get("after")
                          else i18n.t("names.record_field.word_off"))
        if "for" in changed:
            fields.append(i18n.t("names.record_field.for"))
        if "to" in changed:
            fields.append(i18n.t("names.record_field.to"))
        if "real" in changed:
            fields.append(i18n.t("names.record_field.real"))
        if "except" in changed:
            fields.append(i18n.t("names.record_field.except"))
        return i18n.t("names.record_set", entry=int(answer["entry"]), fields=", ".join(fields))
    if key == ("names", "remove") and isinstance(answer.get("gone"), list) and answer["gone"]:
        nums = [str(int(g["entry"])) for g in answer["gone"] if isinstance(g, dict) and g.get("entry")]
        return i18n.t("names.record_remove", entries=", ".join(nums))
    return ""


def entry_for(p, args, run: dict, answer, changed: list, made: list) -> dict:
    request = agent_log.hidden_words(one_line(getattr(args, "note", "")), getattr(args, "secret_words", ()))
    if args.command == "names" and request:
        # a names op's whole request kept as "…", as the agent log keeps it, since it may hold a name typed in it
        # alone (namesfix2)
        request = "…"
    entry = {"at": stamp(), "run": run["id"], "via": run.get("via") or "cli", "agent": run.get("agent") or "",
             "request": request[:WORDS_MOST],
             "op": " ".join(x for x in (args.command, getattr(args, "act", None)) if x),
             "target": target_of(args, answer), "what_changed": changed_line(changed, made, case_names(p)),
             "files": len(changed), "undo_with": undo_of(args, answer, run["id"])}
    said = names_said(args, answer)
    if said:
        entry["what_changed"] = said
    # turn shift-times's shift in counts alone, the seconds, the rows and how many it moved (timeshift, 16 November 2026)
    if (args.command, getattr(args, "act", None)) == ("turn", "shift-times") and isinstance(answer, dict):
        try:
            entry["shift"] = {"by": int(answer["by"]), "from_row": int(answer["from_row"]),
                              "to_row": int(answer["to_row"]), "rows": int(answer["count"])}
        except (KeyError, TypeError, ValueError):
            pass
    # turn skip's reason for passages left with no statement, which the app keeps nowhere (leaveout, 16 November
    # 2026), kept in this line alone, never in a participant's notes, and no other op's reason with it
    reason = skip_reason(args)
    if reason:
        entry["reason"] = reason
        # the passages named that were decided with no statement already, the reason recorded for them too, by row
        # alone (skipreason, 16 November 2026): a reason once kept in a note moves here
        already = reason_already(answer)
        if already:
            entry["reason_rows"] = {"marked": [int(n) for n in (answer or {}).get("marked") or []], "already": already}
            said = i18n.t("agentchanges.reason_recorded", n=len(already), rows=formats_list(already))
            entry["what_changed"] = f"{entry['what_changed']} {said}" if changed else said
    return entry


def skip_reason(args) -> str:
    """turn skip's reason as the record keeps it, one line, the names to keep out taken out, or nothing for another
    op."""
    if (args.command, getattr(args, "act", None)) != ("turn", "skip"):
        return ""
    return agent_log.hidden_words(one_line(getattr(args, "reason", "") or ""),
                                  getattr(args, "secret_words", ()))[:WORDS_MOST]


def reason_already(answer) -> list[int]:
    """The rows a turn skip named that were decided with no statement already, as its answer gives them."""
    answer = answer if isinstance(answer, dict) else {}
    return sorted(int(n) for n in answer.get("already") or [] if isinstance(n, int) or str(n).isdigit())


def reason_alone(args, answer) -> bool:
    """A turn skip with a reason whose passages were all decided with no statement already: it writes no file, and
    its reason is still one line in the record (skipreason, 16 November 2026), so a reason an agent once kept in a
    note can move to the record. Without a reason such a call is no change and no line, as before."""
    return (bool(skip_reason(args)) and bool(reason_already(answer))
            and not (answer if isinstance(answer, dict) else {}).get("marked"))


# ------------------------------------------------------------------ an agent's write

def agent_name(args) -> str:
    import cli
    return one_line(getattr(args, "tool", "") or "")[:80] or cli.TOOL


def through(p, args, run_op, writes: frozenset):
    """One op as an agent asked it: refused when it is the app's alone, else run at once, and when it writes, kept
    in the project's change record with its run's restore point made before the run's first write. A dry run, a
    read and an op of the demo run as ever."""
    import cli
    key = (args.command, getattr(args, "act", None))
    refusal = app_only(args)
    if refusal and not getattr(args, "dry_run", False):
        if not ALL_OPS:
            raise cli.Refused(refusal, code="app_only")
        # the suite's checks standing in for the app, whose own op is no agent's change
        return run_op(args)
    root = getattr(p, "root", None)
    if getattr(args, "dry_run", False) or key not in writes or not kept_here(root):
        return run_op(args)
    if key == ("project", "remove"):
        return removing(p, args, run_op)
    via = getattr(args, "via", "") or "cli"
    with held(root):
        run = current_run(root, args)
        fresh = run is None
        run = run or new_run(root, args, via, agent_name(args))
        before = tracked(root)
        # a file that differs from the run's last reading changed between its writes, by someone else
        foreign = set(moved(run.get("after") or {}, before)) & (set(run.get("changed") or []) | set(run.get("point") or {}))
        # and each file as it stands, by its contents, so this change keeps its files as they were before it: known
        # from the restore point or the run's last change, else read now, which only a file changed since by
        # someone else needs (agentreview2)
        known = known_shas(run)
        unread = {}
        for rel, st in before.items():
            if (rel, tuple(st)) not in known:
                got = read_in(root, rel)
                if got is not None and list(got[1]) == list(st):
                    unread[rel] = got[0]
        try:
            answer, lines = run_op(args)
        except BaseException:
            after = tracked(root)
            if moved(before, after):
                # a write that failed part way: the run kept, so what it wrote can be undone
                if fresh:
                    keep_run(root, run)
                settle(root, run, foreign, before, after)
            raise
        after = tracked(root)
        changed = moved(before, after)
        if not changed and not reason_alone(args, answer):
            # it wrote nothing of the project's: no line, and a new run no restore point, nothing left behind. A turn
            # skip's reason for passages decided already is the one line with no file (skipreason): its step holds
            # no file, so its undo puts nothing back
            return answer, lines
        if fresh:
            # a run of a line with no file keeps its restore point as every run does, so a later write that joins it
            # by its id is undone by putting files back (skipreason's third review)
            keep_run(root, run)
        settle(root, run, foreign, before, after)
        made = [f for f in changed if f not in (run.get("point") or {})]
        step = step_of(root, changed, before, known, unread)
        e = append(root, entry_for(p, args, run, answer, changed, made))
        run.setdefault("steps", {})[e["id"]] = step
        run["changes"] = int(run.get("changes") or 0) + 1
        if e.get("reason") and isinstance(answer, dict):
            # turn skip's answer says its reason went into the record (skipreason)
            answer["recorded"] = True
        if key == ("participant", "rename") and getattr(args, "folder", False):
            run["folder_renamed"] = True
        save_run(root, run)
    return answer, lines


def settle(root, run: dict, foreign: set, before: dict, after: dict) -> list:
    """The run's reading after a write: what it changed, made and found changed by others, its files as they now
    stand, its last write's time. Answers the files this write changed."""
    changed = moved(before, after)
    run["foreign"] = sorted(set(run.get("foreign") or []) | foreign)
    run["changed"] = sorted(set(run.get("changed") or []) | set(changed))
    run["made"] = sorted(set(run.get("made") or []) | {f for f in changed if f not in (run.get("point") or {})})
    run["after"] = after
    if changed:
        run["last"] = stamp()
    save_run(root, run)
    return changed


def known_shas(run: dict) -> dict:
    """Each file's contents the run already holds, by its path and the time and size it had: the restore point's,
    and what each of the run's changes left (agentreview2)."""
    out = {}
    for rel, e in (run.get("point") or {}).items():
        if isinstance(e, dict) and e.get("sha"):
            out[(rel, tuple(e.get("stat") or ()))] = e["sha"]
    for step in (run.get("steps") or {}).values():
        for rel, s in (step or {}).items():
            if isinstance(s, dict) and s.get("after") and s.get("after_stat"):
                out[(rel, tuple(s["after_stat"]))] = s["after"]
    return out


def step_of(root, changed: list, before: dict, known: dict, unread: dict) -> dict:
    """One change's own files, each as it stood before the change and after it, by its contents in the store and
    the time and size it had, so the change is undone alone (`undo_changes`). A file the change made has no before,
    and one it took away no after. A before that could not be read is left out of `before`, its time and size kept,
    so the change is undone only with its run."""
    out = {}
    for rel in changed:
        st = before.get(rel)
        sha = None
        if st is not None:
            sha = known.get((rel, tuple(st)))
            if sha is None and rel in unread:
                sha = hashlib.sha256(unread[rel]).hexdigest()
                keep(root, sha, unread[rel])
        got = copy_in(root, rel) if (Path(root) / rel).is_file() else None
        out[rel] = {"before": sha, "before_stat": st, "after": got[0] if got else None,
                    "after_stat": got[1] if got else None}
    return out


def trash_where() -> str:
    import trash
    return trash.where()


def removing(p, args, run_op):
    """Remove from Idiograph by an agent: its line written into the record before the op, since with the Trash the
    record goes with the folder, and taken out again when the op is refused, the record itself when it was the
    first. It takes no restore point: the folder stays as it is, or goes whole to the Trash. The line names the
    agent's run when it has one."""
    root = p.root
    via = getattr(args, "via", "") or "cli"
    with held(root):
        run = current_run(root, args) or {"id": "", "via": via, "agent": agent_name(args)}
        first = not record_path(root).exists()
        had_store = store(root).is_dir()
        e = dict(entry_for(p, args, run, {}, [], []),
                 what_changed=i18n.t("agentchanges.removed_trash", where=trash_where()) if getattr(args, "trash", False)
                 else i18n.t("agentchanges.removed"))
        e["undo_with"] = {"run": run["id"], "trash": bool(getattr(args, "trash", False))}
        written = append(root, e)
    try:
        return run_op(args)
    except BaseException:
        if Path(root).is_dir():
            with held(root):
                take_out(root, written["id"])
                if first and not read(root):
                    record_path(root).unlink(missing_ok=True)
                    # and the tally its line made, with the store, when the store was made for it
                    if not had_store:
                        (store(root) / TALLY).unlink(missing_ok=True)
                        with contextlib.suppress(OSError):
                            store(root).rmdir()
        raise


# ------------------------------------------------------------------ reading the record

def run_view(r: dict) -> dict:
    """A run as an agent and the review screen read it: its id, the agent, when it began and last wrote, how many
    changes and files, whether it was undone, and the command that undoes it."""
    out = {"id": r["id"], "agent": r.get("agent") or "", "via": r.get("via") or "", "started": r.get("started"),
           "last": r.get("last"), "changes": int(r.get("changes") or 0), "files": len(r.get("changed") or []),
           "command": f"idiograph agents undo-run {r['id']}"}
    if r.get("undone"):
        out["undone"] = r["undone"]
    if r.get("undoes"):
        out["undoes"] = r["undoes"]
    if r.get("undoes_changes"):
        out["undoes_changes"] = list(r["undoes_changes"])
    return out


def listing(root, since: str = "", run: str = "", limit: int | None = None) -> dict:
    """The record newest first, from `since`, a day, on, of `run` alone when named, `limit` the newest, with each
    run it names. What `agents changes` and MCP `agent_changes` answer, and the review screen reads."""
    since = one_line(since)
    if since and not re.fullmatch(r"\d{4}-\d{2}-\d{2}", since):
        import cli
        raise cli.Refused(i18n.t("family_cli.agents_log.since_not_a_date", since=since))
    every = list(reversed(read(root)))
    shown = [e for e in every if (not since or str(e.get("at") or "")[:10] >= since)
             and (not run or str(e.get("run") or "").lower() == run.lower())]
    if limit and limit > 0:
        shown = shown[:limit]
    ids = {str(e.get("run") or "") for e in shown}
    runs = [run_view(r) for r in reversed(all_runs(root)) if r["id"] in ids or (run and r["id"].lower() == run.lower())]
    return {"changes": shown, "runs": runs, "total": len(every)}


# ------------------------------------------------------------------ a run undone

def conflicts(root, run: dict, names: dict) -> list[str]:
    """Each file a run's undo would lose a later change of, in a line: changed since the run's last write, or by
    someone else between its writes."""
    now_files = tracked(root)
    after = run.get("after") or {}
    late = [f for f in run.get("changed") or [] if now_files.get(f) != after.get(f)]
    between = [f for f in run.get("foreign") or [] if f in set(run.get("changed") or []) and f not in late]
    out = []
    if late:
        out.append(i18n.t("agentchanges.undo.later", what=said_files(late, names)))
    if between:
        out.append(i18n.t("agentchanges.undo.between", what=said_files(between, names)))
    return out


def lock_of(root, rel: str) -> Path:
    """The lock a file is written under: its participant's, in their Working folder, or the project's own."""
    parts = rel.split("/")
    if len(parts) == 2 and parts[0].endswith(".history"):
        return locks.root_lock(Path(root))
    return (Path(root) / parts[0] / "Working" / locks.NAME) if len(parts) > 1 else locks.root_lock(Path(root))


def undo_run(p, args) -> tuple:
    """`agents undo-run <id>`: every file the run changed put back as it was before its first write, and each file it
    made taken away, kept first, all under the files' own locks. Refused whole when a file would lose a later
    change, or when the run renamed a participant's folder. Itself a run of its own, so undone in its turn. With
    --dry-run what it would put back and take away."""
    import cli
    root = p.root
    rid = one_line(getattr(args, "id", ""))
    names = case_names(p)
    if not kept_here(root):
        raise cli.Refused(i18n.t("agentchanges.undo.demo"))
    with held(root):
        run = load_run(root, rid.lower()) or load_run(root, rid)
        if run is None:
            raise cli.Refused(i18n.t("agentchanges.undo.no_run", id=rid))
        if run.get("undone"):
            if not run["undone"].get("run"):
                # a run of no file, marked undone as it stood (skipreason)
                raise cli.Refused(i18n.t("agentchanges.undo.already_alone", id=run["id"]))
            raise cli.Refused(i18n.t("agentchanges.undo.already", id=run["id"], by=run["undone"].get("run") or ""))
        if run.get("folder_renamed"):
            raise cli.Refused(i18n.t("agentchanges.undo.folder", id=run["id"]))
        lost = conflicts(root, run, names)
        if lost:
            raise cli.Refused(*([i18n.t("agentchanges.undo.refused", id=run["id"])] + lost
                                + [i18n.t("cli.said.nothing_was_written")]))
        point_files = run.get("point") or {}
        back = [f for f in run.get("changed") or [] if f in point_files]
        gone = [f for f in run.get("made") or [] if f not in point_files and (Path(root) / f).is_file()]
        missing = [f for f in back if not (objects(root) / point_files[f]["sha"]).is_file()]
        if missing:
            raise cli.Refused(i18n.t("agentchanges.undo.copies_gone", id=run["id"], what=said_files(missing, names)))
        answer = {"run": run["id"], "put_back": len(back), "taken_away": len(gone), "dry_run": bool(args.dry_run),
                  "back_said": said_files(back, names), "gone_said": said_files(gone, names)}
        n_changes = i18n.t("agentchanges.n.changes", n=int(run.get("changes") or 0))
        head = (i18n.t("agentchanges.undo.would", id=run["id"], changes=n_changes) if args.dry_run
                else i18n.t("agentchanges.undo.done", id=run["id"], changes=n_changes))
        lines = [i18n.t("cli.said.dry_run_nothing_was_written")] if args.dry_run else []
        lines.append(head)
        if back:
            lines.append("  " + i18n.t("agentchanges.undo.back", what=answer["back_said"]))
        if gone:
            lines.append("  " + i18n.t("agentchanges.undo.gone", what=answer["gone_said"]))
        if args.dry_run:
            return answer, lines
        if not (back or gone):
            # a run that changed no file, a turn skip's reason alone or the undo of one (skipreason): nothing to put
            # back, so it is marked undone as it stands, with no run of its own, and By an agent offers no Undo
            run["undone"] = {"at": stamp(), "run": "", "by": agent_name(args) if (getattr(args, "via", "") or "cli") != "app"
                             else "app"}
            save_run(root, run)
            return answer, lines
        via = getattr(args, "via", "") or "cli"
        mine = keep_run(root, new_run(root, args, via, agent_name(args), undoes=run["id"]))
        before = tracked(root)
        kept_made = {}
        with contextlib.ExitStack() as stack:
            for lock in sorted({lock_of(root, f) for f in back + gone}, key=str):
                stack.enter_context(locks.held(lock))
            for f in gone:
                got = copy_in(root, f)
                if got is not None:
                    kept_made[f] = got[0]
                (Path(root) / f).unlink(missing_ok=True)
            for f in back:
                target = Path(root) / f
                target.parent.mkdir(parents=True, exist_ok=True)
                tmp = target.with_name(f".{target.name}.{secrets.token_hex(4)}.restore")
                put_back(tmp, (objects(root) / point_files[f]["sha"]).read_bytes(), f)
                # its time as it was too, so the file reads exactly as it stood, and an earlier run undone after
                # this one finds its files as its last write left them
                stamp_ns = (point_files[f].get("stat") or [None])[0]
                if isinstance(stamp_ns, int):
                    os.utime(tmp, ns=(stamp_ns, stamp_ns))
                locks.replace(tmp, target)
        after = tracked(root)
        changed = moved(before, after)
        mine.update(changed=changed, made=[f for f in changed if f not in mine["point"]], after=after, last=stamp(),
                    changes=1, kept_made=kept_made)
        save_run(root, mine)
        run["undone"] = {"at": stamp(), "run": mine["id"], "by": agent_name(args) if via != "app" else "app"}
        save_run(root, run)
        e = append(root, {"at": stamp(), "run": mine["id"], "via": via, "agent": mine["agent"],
                          "request": one_line(getattr(args, "note", ""))[:WORDS_MOST], "op": "agents undo-run",
                          "target": {"run": run["id"]}, "what_changed": changed_line(changed, [], names),
                          "files": len(changed), "undo_with": {"run": mine["id"],
                                                          "command": f"idiograph agents undo-run {mine['id']}"}})
        answer.update(undo_run=mine["id"], change=e["id"])
        lines.append(i18n.t("agentchanges.undo.again", id=mine["id"]))
        return answer, lines


# ------------------------------------------------------------------ one change undone alone (agentreview2)

class Files:
    """The project's files as they stand, read once, each one's contents read only when its time and size do not
    settle whether it stands as a change left it, and a file as an undo of later changes would leave it."""

    def __init__(self, root, real: dict | None = None, shas: dict | None = None):
        self.root = root
        self.real = tracked(root) if real is None else real
        self.shas: dict = {} if shas is None else shas
        self.then: dict = {}

    def fresh(self) -> "Files":
        """The files as they stand again, no undo imagined, what was read kept."""
        return Files(self.root, self.real, self.shas)

    def sha(self, rel: str):
        if rel not in self.shas:
            got = read_in(self.root, rel)
            self.shas[rel] = hashlib.sha256(got[0]).hexdigest() if got else None
        return self.shas[rel]

    def state(self, rel: str):
        """A file as it stands, or as the undo of later changes would leave it: its time and size and its
        contents' sha when known, None when it is not there."""
        if rel in self.then:
            return self.then[rel]
        st = self.real.get(rel)
        return None if st is None else {"stat": st, "sha": None, "real": True}

    def stands(self, rel: str, s: dict) -> bool:
        """Whether a file stands as a change left it."""
        state = self.state(rel)
        if s.get("after_stat") is None:
            return state is None
        if state is None:
            return False
        if list(state["stat"]) == list(s["after_stat"]):
            return True
        sha = state["sha"] if state.get("sha") or not state.get("real") else self.sha(rel)
        return bool(sha) and sha == s.get("after")

    def undo(self, step: dict) -> None:
        """Each file of a change as its undo leaves it: as it stood just before the change."""
        for rel, s in step.items():
            self.then[rel] = (None if s.get("before_stat") is None
                              else {"stat": s["before_stat"], "sha": s.get("before"), "real": False})

    def when(self, rel: str):
        """When a file last changed, as it stands or as an undo would leave it."""
        state = self.state(rel)
        if state is None:
            return None
        return datetime.fromtimestamp(state["stat"][0] / 1e9).astimezone().isoformat(timespec="seconds")


def undoable(step) -> bool:
    """Whether a change keeps its files as they stood before it, so it is undone alone. A change of no file, a turn
    skip's reason for passages decided already (skipreason), keeps an empty step: undone alone, nothing put back."""
    return isinstance(step, dict) and all(isinstance(s, dict) and (s.get("before_stat") is None or s.get("before"))
                              for s in step.values())


def undone_alone(runs: dict) -> dict:
    """Each change undone alone, by the undo's run, while that run is not undone in its turn."""
    out = {}
    for r in runs.values():
        if r.get("undoes_changes") and not r.get("undone"):
            for cid in r["undoes_changes"]:
                out[str(cid)] = {"run": r["id"], "at": r.get("last") or r.get("started"), "via": r.get("via") or ""}
    return out


def undo_changes(p, args) -> tuple:
    """`agents undo-change <id> [<id> ...]`: each change named undone alone, every file it changed put back as it
    stood just before it from the copies its run kept, a file it made taken away, kept first, newest change first, so
    a later change named with it is undone before it. Refused whole, nothing written, when anything changed one of
    its files since, the researcher's edit or a later change not named, when it is undone already or its run is,
    and when it keeps no copies (a change from before 13 November's agentreview2, or a participant's folder renamed),
    which is then undone with its run. Itself a run of its own, which `agents undo-run` undoes in its turn. With
    --dry-run what it would put back and take away."""
    import cli
    root = p.root
    ids = [one_line(x).lower() for x in (getattr(args, "ids", None) or []) if one_line(x)]
    names = case_names(p)
    if not kept_here(root):
        raise cli.Refused(i18n.t("agentchanges.undo.demo"))
    if not ids:
        raise cli.Refused(i18n.t("agentchanges.undo_change.none_named"))
    with held(root):
        entries = {str(e.get("id") or "").lower(): e for e in read(root)}
        runs = {r["id"]: r for r in all_runs(root)}
        alone = undone_alone(runs)
        todo = []
        for cid in sorted(set(ids), key=change_number, reverse=True):
            e = entries.get(cid)
            if e is None:
                raise cli.Refused(i18n.t("agentchanges.undo_change.no_change", id=cid))
            run = runs.get(str(e.get("run") or ""))
            step = ((run or {}).get("steps") or {}).get(e["id"])
            if e["id"] in alone:
                raise cli.Refused(i18n.t("agentchanges.undo_change.already", id=e["id"], by=alone[e["id"]]["run"]))
            if run is not None and run.get("undone"):
                raise cli.Refused(i18n.t("agentchanges.undo_change.run_undone", id=e["id"], run=run["id"]))
            if not undoable(step) or e.get("op") == "participant rename":
                raise cli.Refused(i18n.t("agentchanges.undo_change.no_copies", id=e["id"], run=e.get("run") or ""))
            todo.append((e, run, step))
        files = Files(root)
        lost = []
        for e, _run, step in todo:
            late = [rel for rel in sorted(step) if not files.stands(rel, step[rel])]
            if late:
                lost.append(i18n.t("agentchanges.undo_change.later", id=e["id"], what=said_files(late, names)))
            files.undo(step)
        if lost:
            raise cli.Refused(*([i18n.t("agentchanges.undo_change.refused")] + lost
                                + [i18n.t("cli.said.nothing_was_written")]))
        missing = sorted({rel for _e, _r, step in todo for rel, s in step.items()
                          if s.get("before") and not (objects(root) / s["before"]).is_file()})
        if missing:
            raise cli.Refused(i18n.t("agentchanges.undo_change.copies_gone", what=said_files(missing, names)))
        named = formats_list([e["id"] for e, _r, _s in reversed(todo)])
        back = sorted({rel for _e, _r, step in todo for rel, s in step.items() if s.get("before_stat") is not None})
        gone = sorted({rel for _e, _r, step in todo for rel, s in step.items()
                       if s.get("before_stat") is None and (Path(root) / rel).is_file()})
        answer = {"changes": [e["id"] for e, _r, _s in reversed(todo)], "put_back": len(back),
                  "taken_away": len(gone), "dry_run": bool(args.dry_run), "back_said": said_files(back, names),
                  "gone_said": said_files(gone, names)}
        lines = [i18n.t("cli.said.dry_run_nothing_was_written")] if args.dry_run else []
        lines.append(i18n.t("agentchanges.undo_change.would", ids=named) if args.dry_run
                     else i18n.t("agentchanges.undo_change.done", ids=named))
        if back:
            lines.append("  " + i18n.t("agentchanges.undo.back", what=answer["back_said"]))
        if gone:
            lines.append("  " + i18n.t("agentchanges.undo.gone", what=answer["gone_said"]))
        if args.dry_run:
            return answer, lines
        via = getattr(args, "via", "") or "cli"
        mine = new_run(root, args, via, agent_name(args))
        mine.update(key=f"undo-changes:{','.join(answer['changes'])}", undoes_changes=answer["changes"])
        mine = keep_run(root, mine)
        before = tracked(root)
        kept_made = {}
        with contextlib.ExitStack() as stack:
            for lock in sorted({lock_of(root, rel) for _e, _r, step in todo for rel in step}, key=str):
                stack.enter_context(locks.held(lock))
            for _e, _r, step in todo:
                for rel, s in sorted(step.items()):
                    target = Path(root) / rel
                    if s.get("before_stat") is None:
                        if target.is_file():
                            got = copy_in(root, rel)
                            if got is not None:
                                kept_made[rel] = got[0]
                            target.unlink(missing_ok=True)
                        continue
                    target.parent.mkdir(parents=True, exist_ok=True)
                    tmp = target.with_name(f".{target.name}.{secrets.token_hex(4)}.restore")
                    put_back(tmp, (objects(root) / s["before"]).read_bytes(), rel)
                    # its time as it was too, so the change before it finds the file as it left it
                    stamp_ns = s["before_stat"][0]
                    if isinstance(stamp_ns, int):
                        os.utime(tmp, ns=(stamp_ns, stamp_ns))
                    locks.replace(tmp, target)
        after = tracked(root)
        changed = moved(before, after)
        mine.update(changed=changed, made=[f for f in changed if f not in mine["point"]], after=after, last=stamp(),
                    changes=1, kept_made=kept_made)
        save_run(root, mine)
        e = append(root, {"at": stamp(), "run": mine["id"], "via": via, "agent": mine["agent"],
                          "request": one_line(getattr(args, "note", ""))[:WORDS_MOST], "op": "agents undo-change",
                          "target": {"changes": answer["changes"]}, "what_changed": changed_line(changed, [], names),
                          "files": len(changed), "undo_with": {"run": mine["id"],
                                                          "command": f"idiograph agents undo-run {mine['id']}"}})
        answer.update(undo_run=mine["id"], change=e["id"])
        lines.append(i18n.t("agentchanges.undo.again", id=mine["id"]))
        return answer, lines


def formats_list(items) -> str:
    import formats
    return formats.list_words([str(x) for x in items])


# ------------------------------------------------------------------ review afterwards (agentreview2)

# each op's line in the app's own past tense, by its command and act, the record's line of what changed for the rest
OPS_SAID = {
    ("board", "apply"): (lambda: i18n.t("agentchanges.op.board_apply")), ("board", "new"): (lambda: i18n.t("agentchanges.op.board_new")),
    ("board", "fresh"): (lambda: i18n.t("agentchanges.op.board_new")), ("board", "import"): (lambda: i18n.t("agentchanges.op.board_new")),
    ("board", "duplicate"): (lambda: i18n.t("agentchanges.op.board_duplicate")), ("board", "rename"): (lambda: i18n.t("agentchanges.op.board_rename")),
    ("board", "delete"): (lambda: i18n.t("agentchanges.op.board_delete")), ("board", "note"): (lambda: i18n.t("agentchanges.op.board_note")),
    ("board", "restore"): (lambda: i18n.t("agentchanges.op.board_restore")), ("board", "revision"): (lambda: i18n.t("agentchanges.op.board_revision")),
    ("board", "current"): (lambda: i18n.t("agentchanges.op.board_current")), ("board", "complete"): (lambda: i18n.t("agentchanges.op.board_complete")),
    ("board", "copy"): (lambda: i18n.t("agentchanges.op.board_copy")), ("board", "canvas"): (lambda: i18n.t("agentchanges.op.board_canvas")),
    ("gets", "apply"): (lambda: i18n.t("agentchanges.op.gets_apply")), ("gets", "take"): (lambda: i18n.t("agentchanges.op.gets_take")),
    ("turn", "write"): (lambda: i18n.t("agentchanges.op.turn_write")), ("turn", "edit"): (lambda: i18n.t("agentchanges.op.turn_edit")),
    ("turn", "interviewer-note"): (lambda: i18n.t("agentchanges.op.turn_note")), ("transcript", "replace"): (lambda: i18n.t("agentchanges.op.replace")),
    ("turn", "skip"): (lambda: i18n.t("agentchanges.op.turn_skip")),
    ("turn", "shift-times"): (lambda: i18n.t("agentchanges.op.turn_shift_times")),
    ("clear-formatting", None): (lambda: i18n.t("agentchanges.op.clear_formatting")),
    ("clear-made-notes", None): (lambda: i18n.t("agentchanges.op.clear_made_notes")),
    ("participant", "set"): (lambda: i18n.t("agentchanges.op.participant_set")),
    ("participant", "rename"): (lambda: i18n.t("agentchanges.op.participant_rename")),
    ("participant", "complete"): (lambda: i18n.t("agentchanges.op.participant_complete")), ("length", None): (lambda: i18n.t("agentchanges.op.length")),
    ("project", "set"): (lambda: i18n.t("agentchanges.op.project_set")), ("timepoints", None): (lambda: i18n.t("agentchanges.op.timepoints")),
    ("codes", "new"): (lambda: i18n.t("agentchanges.op.codes_new")), ("codes", "rename"): (lambda: i18n.t("agentchanges.op.codes_rename")),
    ("codes", "describe"): (lambda: i18n.t("agentchanges.op.codes_describe")), ("codes", "merge"): (lambda: i18n.t("agentchanges.op.codes_merge")),
    ("codes", "delete"): (lambda: i18n.t("agentchanges.op.codes_delete")), ("codes", "add"): (lambda: i18n.t("agentchanges.op.codes_add")),
    ("trajectories", "apply"): (lambda: i18n.t("agentchanges.op.trajectories")), ("demographics", "apply"): (lambda: i18n.t("agentchanges.op.demographics")),
    ("agents", "undo-run"): (lambda: i18n.t("agentchanges.op.undo_run")), ("agents", "undo-change"): (lambda: i18n.t("agentchanges.op.undo_change")),
}
# the screen a change is on, by its command
WHERE_SAID = {"board": (lambda: i18n.t("agentchanges.where.pets")), "turn": (lambda: i18n.t("agentchanges.where.statements")),
              "transcript": (lambda: i18n.t("agentchanges.where.statements")), "statements": (lambda: i18n.t("agentchanges.where.statements")),
              "codes": (lambda: i18n.t("agentchanges.where.codes")), "trajectories": (lambda: i18n.t("agentchanges.where.trajectories"))}


def line_of(e: dict) -> str:
    """A change in one line, what it did, in the app's own past tense: its op's, else the record's line of what
    changed. Never a participant's words, which the record never holds."""
    op = str(e.get("op") or "").split(" ", 1)
    if e.get("op") == "turn skip" and e.get("reason_rows") and not e.get("files"):
        # a reason recorded for passages decided already, no passage marked (skipreason, 16 November 2026)
        return i18n.t("agentchanges.op.turn_skip_reason")
    key = OPS_SAID.get((op[0], op[1] if len(op) > 1 else None))
    return key() if key else str(e.get("what_changed") or "").rstrip(".")


def where_of(e: dict) -> str:
    """Where a change was: the participant and the screen, "Mabel, PETs", the GETs, or nothing for the whole
    project."""
    import gets as gets_mod
    target = e.get("target") if isinstance(e.get("target"), dict) else {}
    command = str(e.get("op") or "").split(" ", 1)[0]
    parts = [gets_mod.who(str(target["case"]))] if target.get("case") else []
    if command == "gets":
        parts.append(i18n.t("agentchanges.where.lpets") if target.get("case") else i18n.t("agentchanges.where.gets"))
    elif command in WHERE_SAID and (target.get("case") or command in ("codes", "trajectories")):
        parts.append(WHERE_SAID[command]())
    return ", ".join(parts)


def review(p, offset: int = 0, limit: int = REVIEW_RUNS, mark: bool = False) -> dict:
    """By an agent, as Project history shows it: the agents' changes grouped by run, newest run first, `limit` runs
    from `offset`, each run with its agent, when it began and last changed, its count, the request it gave, New
    while it holds a change he has not seen, and how it is undone, and each change with its line, where it was and
    whether Undo can take it back now. With `mark`, every change so far is seen once the answer is made, so New and
    Home's line go. The app's own undos are no agent's and are not listed, their changes marked undone."""
    root = p.root
    names = case_names(p)
    entries = read(root)
    runs = {r["id"]: r for r in all_runs(root)}
    seen = small(store(root) / SEEN) or {}
    seen_last = int(seen.get("last") or 0) if str(seen.get("last") or "0").isdigit() else 0
    alone = undone_alone(runs)
    groups: dict = {}
    for e in entries:
        if not by_agent(e):
            continue
        key = str(e.get("run") or "") or f"-{e.get('id')}"
        groups.setdefault(key, []).append(e)
    order = sorted(groups, key=lambda k: max(change_number(x.get("id")) for x in groups[k]), reverse=True)
    total = sum(len(v) for v in groups.values())
    new = sum(1 for v in groups.values() for x in v if change_number(x.get("id")) > seen_last)
    files = Files(root)
    # each change whose files can still be put back, by file, to find what stands in another's way
    live_by_file: dict = {}
    for e in entries:
        run = runs.get(str(e.get("run") or ""))
        step = ((run or {}).get("steps") or {}).get(e.get("id"))
        if not by_agent(e) or not step or e.get("id") in alone or (run or {}).get("undone"):
            continue
        for rel, s in step.items():
            live_by_file.setdefault(rel, []).append((change_number(e["id"]), e, s))
    shown = []
    for key in order[offset:offset + limit if limit else None]:
        mine = groups[key]
        run = runs.get(key) or {}
        out_changes = []
        for e in sorted(mine, key=lambda x: change_number(x.get("id")), reverse=True):
            out_changes.append(dict(change_view(e, run, alone, files, live_by_file, names), new=change_number(e.get("id")) > seen_last))
        out = {"id": key, "agent": agent_said(mine[0].get("agent")), "via": str(mine[0].get("via") or ""),
               "started": mine[0].get("at"), "last": mine[-1].get("at"), "count": len(mine),
               "request": next((agent_request(x) for x in mine if x.get("request")), ""),
               "new": any(c["new"] for c in out_changes), "changes": out_changes}
        if run.get("undone"):
            out["undone"] = {"at": run["undone"].get("at"), "by": run["undone"].get("by") or ""}
        out.update(run_action(run, mine, alone, files.fresh()))
        shown.append(out)
    answer = {"runs": shown, "total": total, "runs_total": len(order), "new": new,
              "new_runs": sum(1 for k in order if any(change_number(x.get("id")) > seen_last for x in groups[k]))}
    if mark and new:
        mark_seen(root)
    return answer


def agent_said(name) -> str:
    """An agent's name as the page shows it, cleaned as the agent log cleans it."""
    from agent_log import NAME_MOST, agent_words
    return agent_words(name, NAME_MOST)


def agent_request(e: dict) -> str:
    from agent_log import agent_words
    return agent_words(e.get("request"))


def change_view(e: dict, run: dict, alone: dict, files: Files, live_by_file: dict, names: dict) -> dict:
    """One change as By an agent lists it: its line and where, and its state. `ok`, Undo takes it back now.
    `undone`, undone alone, with when. `yours`, a file of it changed since by him, with which and when. `later`, a
    later change of another run's stands in its way, with its agent and when. `same`, a later change of its own run
    does, which Undo this run takes back first. `none`, it keeps no copies or its run is undone."""
    import cli
    out = {"id": e.get("id"), "at": e.get("at"), "line": line_of(e), "where": cli.scrub(where_of(e))}
    # turn skip's reason, the agent's words, cleaned as its request is (leaveout, 16 November 2026)
    if e.get("reason"):
        from agent_log import agent_words
        out["reason"] = agent_words(e.get("reason"))
    step = (run.get("steps") or {}).get(e.get("id"))
    if e.get("id") in alone:
        return dict(out, state="undone", undone_at=alone[e["id"]]["at"])
    if run.get("undone") or not undoable(step) or e.get("op") == "participant rename":
        return dict(out, state="none")
    late = [rel for rel in sorted(step) if not files.stands(rel, step[rel])]
    if not late:
        return dict(out, state="ok")
    n = change_number(e.get("id"))
    for rel in late:
        later = [(m, x) for m, x, s in live_by_file.get(rel, []) if m > n and files.stands(rel, s)]
        if later:
            m, x = max(later, key=lambda t: t[0])
            if str(x.get("run") or "") == str(e.get("run") or ""):
                return dict(out, state="same")
            return dict(out, state="later", by=agent_said(x.get("agent")), by_at=x.get("at"))
    # a file that is there now says when, before one taken away since (a History chunk a later write replaced)
    rel = next((r for r in late if files.when(r)), late[0])
    return dict(out, state="yours", what=said_files([rel], names), changed_at=files.when(rel))


def run_action(run: dict, mine: list, alone: dict, files: Files) -> dict:
    """How a run is undone from By an agent: `undo` "changes" with the ids Undo puts back, newest first as each
    leaves the files for the next, every one of them for Undo this run or the others when a change cannot be, or
    "run", the whole run from its restore point, for a run whose changes keep no copies of their own (from before
    agentreview2) or an agent's undo, which `agents undo-run` refuses in place when a later change stands in its way.
    None when nothing can be undone."""
    if not run or run.get("undone"):
        return {"undo": None}
    steps = run.get("steps") or {}
    if any(not undoable(steps.get(e.get("id"))) for e in mine) and not any(e.get("id") in steps for e in mine):
        return {"undo": "run", "undo_n": len(mine), "whole": True}
    ids = []
    for e in sorted(mine, key=lambda x: change_number(x.get("id")), reverse=True):
        step = steps.get(e.get("id"))
        if e.get("id") in alone or not undoable(step) or e.get("op") == "participant rename":
            continue
        if all(files.stands(rel, s) for rel, s in step.items()):
            ids.append(e["id"])
            files.undo(step)
    if not ids:
        return {"undo": None}
    return {"undo": "changes", "undo_ids": ids, "undo_n": len(ids), "whole": len(ids) == len(mine)}


# ------------------------------------------------------------------ the holds of before

HOLDS_FILE = "idiograph-holds.json"
HOLDS_LOCK = ".idiograph-holds.lock"


def clear_holds(root) -> int:
    """A project's actions that waited for his yes before approvals were removed (13 November 2026), dropped the
    first time the project is opened, never applied, and their count said once in the agent log. The holds file
    goes, with its lock. Answers how many waited."""
    path = Path(root) / HOLDS_FILE
    if not path.is_file():
        return 0
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        holds = data.get("holds") if isinstance(data, dict) else []
        n = sum(1 for h in holds or [] if isinstance(h, dict) and h.get("status") == "waiting")
    except (OSError, ValueError):
        n = 0
    try:
        path.unlink()
        (Path(root) / HOLDS_LOCK).unlink(missing_ok=True)
    except OSError:
        return 0
    if n:
        try:
            import agent_log
            name = srv.load_json(Path(root) / srv.PROJECT_FILE, {}).get("name") or Path(root).name
            agent_log.add(agent_log.entry(via="app", agent="", call="", code="cleared",
                                          line=i18n.t("agentchanges.holds_cleared", n=n), request="",
                                          project=str(name), op="holds cleared"))
        except Exception:        # the log never fails an open
            pass
    return n
