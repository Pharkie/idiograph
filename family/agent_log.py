"""The agent log (agentlog, 3 November 2026, Adam's option B by dialog that morning, on refusaldraw's drawings).

Each time the app refuses an agent, through the command line or the MCP server, one entry goes into
`agent-log.json` in the app's settings folder, beside its settings file, each of the three apps its own since siftlog
the same day (Adam: Sift and Trace too), never in a project, a review or a screening's folder, so it never travels
with a send, an export or Send feedback. An entry says when, the agent by the name it gave, the project (a project
agents may not read by a count, never its name), the command with its flag names alone, the refusal's code (see
`KINDS`), the refusal's line and the request the agent said he made, cut to 300 characters. Never the values given:
a word the agent handed in is taken out of the line wherever it shows, and no file's words are kept.

Dangerously skip permissions turned on or off is an entry too, read from agentlock's record of the switch
(`server.switch_record_path`), which stays the one record of it. The window shows the log under Settings, AI
features, Using your own AI agents (the pane's line, and Open with the sheet), and agents read it with
`idiograph agents log` and MCP `agent_log`, which only read. Nothing clears it (Adam, 3 November 2026: no Clear and
no setting): it keeps the last DAYS days, an older entry dropped as the log is written or read, so it never grows
and never needs tidying.

Kept: the last DAYS days, and the latest MOST entries within them, a backstop against a flood. The same refusal again within MERGE seconds adds to
the entry's count, so a flood of one refusal is one line. A write waits at most WAIT seconds for the file's lock and
is dropped after: logging never fails a command, and the MCP server writes on a thread of its own after its answer.

The standard library only, with the family's locks.
"""
from __future__ import annotations

import json
import os
import queue
import re
import threading
import unicodedata
from datetime import datetime, timedelta
from pathlib import Path

FILE = "agent-log.json"
LOCK = ".agent-log.lock"
# the suite's own file, so no check's refusal lands in this machine's log (tests/test_idiograph.py, run_all)
PLACE = "IDIOGRAPH_AGENT_LOG"
MOST = 500
DAYS = 7
MERGE = 60
WAIT = 0.5
WORDS_MOST = 300
NAME_MOST = 60
CALL_MOST = 160
# the family's first app, whose log keeps PLACE's own name in the suite (see `place`)
DEFAULT_APP = "idiograph"

# What each entry's code means. A refusal that carries one of errors.CODES keeps it, and these are the rest.
KINDS = {
    "not_allowed": "the project does not allow AI agents to read it, or none it names does",
    "no_command": "the command line or the MCP server has no such command or tool, or it is another app's",
    "page_only": "only the app's own window does it, never an agent",
    "declined": "it waited for his yes in the app and he declined it",
    "invalid": "the command was given in a shape it does not take",
    "refused": "any other refusal, its line saying why",
}
DECLINED = "declined"

# The agent's own words as the app quotes them (agentholds, 2 November 2026, from Harbour's `keyWords`, moved here
# from holds.py on 3 November so the log cleans them the same): on one line, with no character a reader cannot see
# (a control, a direction mark, a zero-width space or joiner, a variation selector, which can carry a hidden
# message), no quotation mark or lookalike that could close a card's own, every "://" broken so no address is drawn
# as a link, and no longer than `most`
QUOTE_LIKE = set("\"'„‚〝〞〟＂＇″‴‶‷ˮʺ˝"
                 "˶ʹʻʼ〃״׳⹂❛❜❝❞❮❯"
                 "\U0001f676\U0001f677\U0001f678̋")
UNSEEN = set("ᅟᅠ⠀ㅤﾠ͏")


def unseen(ch: str) -> bool:
    n = ord(ch)
    return (unicodedata.category(ch) in ("Cf", "Cc", "Co", "Cs") or ch in UNSEEN or 0xFE00 <= n <= 0xFE0F
            or 0xE0100 <= n <= 0xE01EF)


def agent_words(s, most: int = WORDS_MOST) -> str:
    """An agent's words as a hold or the log quotes them: one line, nothing unseen, no quotation mark, no link, at
    most `most` characters and an ellipsis."""
    s = re.sub(r"[\r\n  \t\v\f\x85]+", " ", str(s or ""))
    s = "".join("'" if ch in QUOTE_LIKE or unicodedata.category(ch) in ("Pi", "Pf") else ch
                for ch in s if not unseen(ch))
    s = re.sub(r"\s{2,}", " ", s.replace("://", ": //")).strip()
    return s if len(s) <= most else s[:most].rstrip() + "…"


# ------------------------------------------------------------------ where

def place(config=None) -> Path:
    """The log's file: the suite's when PLACE names one, else beside the settings file this run reads, `config`
    when given (a command's --config), else the server's. Each of the three apps keeps its own beside its own
    settings (siftlog, 3 November 2026), and in the suite Sift's and Trace's are PLACE's with the app's name added,
    `suite-agent-log-sift.json`, so no app's refusal lands in another's log."""
    import server as srv
    given = os.environ.get(PLACE)
    if given:
        given = Path(given)
        return given if srv.APP == DEFAULT_APP else given.with_name(f"{given.stem}-{srv.APP}{given.suffix}")
    if not config:
        config = srv.CONFIG_PATH
    return Path(config).expanduser().resolve().with_name(FILE)


def now() -> datetime:
    return datetime.now().astimezone()


def stamp(when: datetime | None = None) -> str:
    return (when or now()).isoformat(timespec="seconds")


def parsed(iso) -> datetime | None:
    try:
        d = datetime.fromisoformat(str(iso))
    except (TypeError, ValueError):
        return None
    return d if d.tzinfo else d.astimezone()


def load(path: Path) -> dict:
    """The file as it stands, its `entries`, or none when it is not there or not readable."""
    try:
        data = json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {"entries": []}
    if not isinstance(data, dict):
        return {"entries": []}
    return {"entries": [e for e in data.get("entries") or [] if isinstance(e, dict)]}


def save(path: Path, data: dict) -> None:
    """Written whole through a file beside it, so a reader never sees half of it."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_name(path.name + ".part")
    temp.write_text(json.dumps(data, ensure_ascii=False, indent=1), encoding="utf-8", newline="\n")
    import locks
    locks.replace(temp, path)


def kept(entries: list, at: datetime | None = None) -> list:
    """The entries still kept: none older than DAYS days, and the latest MOST, oldest first."""
    edge = (at or now()) - timedelta(days=DAYS)
    fresh = [e for e in entries if (parsed(e.get("time") or e.get("at")) or edge) > edge]
    return fresh[-MOST:]


SAME = ("via", "agent", "project", "closed", "call", "code", "line", "request")


def merged(entries: list, entry: dict, at: datetime) -> list:
    """`entries` with `entry` at the end, or, when the same refusal came within MERGE seconds, that one's count up
    and moved to the end."""
    key = tuple(entry.get(k) for k in SAME)
    for i in range(len(entries) - 1, -1, -1):
        old = entries[i]
        last = parsed(old.get("time") or old.get("at"))
        if last is None or (at - last).total_seconds() > MERGE:
            continue
        if tuple(old.get(k) for k in SAME) == key:
            old = dict(old, count=int(old.get("count") or 1) + 1, time=entry["time"])
            return entries[:i] + entries[i + 1:] + [old]
    return entries + [entry]


def add(entry: dict, path: Path | None = None) -> bool:
    """One entry into the log, under its lock, kept within MOST and DAYS. Answers whether it was written: a busy
    lock or a file that cannot be written drops it, and a command never fails for it."""
    import locks
    from errors import WorkbookError
    path = Path(path) if path else place()
    at = now()
    entry = dict(entry, at=entry.get("at") or stamp(at), time=entry.get("time") or entry.get("at") or stamp(at),
                 count=int(entry.get("count") or 1))
    try:
        with locks.held(path.with_name(LOCK), wait=WAIT):
            data = load(path)
            save(path, {"entries": kept(merged(data["entries"], entry, at), at)})
        return True
    except (WorkbookError, OSError, ValueError, TypeError):
        return False


# The MCP server's writes, on a thread of their own after its answer, so a flood never slows the agent's answer
LATER: queue.Queue = queue.Queue()
WRITER: dict = {"thread": None}


def _write_later() -> None:
    while True:
        entry, path = LATER.get()
        try:
            add(entry, path)
        finally:
            LATER.task_done()


def later(entry: dict, path: Path | None = None) -> None:
    """`add` on the writer's thread, started on the first."""
    if WRITER["thread"] is None:
        WRITER["thread"] = threading.Thread(target=_write_later, name="agent-log", daemon=True)
        WRITER["thread"].start()
    LATER.put((entry, path))


def flush() -> None:
    """Every write handed to the thread done, for the suite."""
    if WRITER["thread"] is not None:
        LATER.join()


# ------------------------------------------------------------------ reading

def switches(record: Path, at: datetime) -> list:
    """Dangerously skip permissions turned on or off, from agentlock's record beside the settings (see
    `server.record_switch`), those of the last DAYS days, as entries. The record itself is never changed."""
    edge = at - timedelta(days=DAYS)
    out = []
    try:
        lines = Path(record).read_text(encoding="utf-8").splitlines()
    except OSError:
        return []
    for line in lines:
        try:
            got = json.loads(line)
        except ValueError:
            continue
        when = parsed(got.get("at")) if isinstance(got, dict) else None
        if when is None or when <= edge:
            continue
        out.append({"kind": "switch", "at": stamp(when), "time": stamp(when), "count": 1, "on": got.get("on") is True,
                    "from": "window" if got.get("from") == "window" else "browser"})
    return out


def read(path: Path | None = None, config=None) -> list:
    """Every entry the log keeps, the switch's among them, newest first, at most MOST: the log beside the settings
    `config` names, the server's by default, and the switch's record beside them."""
    import server as srv
    path = Path(path) if path else place(config)
    at = now()
    data = load(path)
    entries = [dict(e, kind="refusal") for e in kept(data["entries"], at)]
    every = entries + switches(srv.switch_record_path(config), at)
    every.sort(key=lambda e: parsed(e.get("time")) or at, reverse=True)
    return every[:MOST]


# ------------------------------------------------------------------ an entry from a refusal

def scrubbed(line: str, values) -> str:
    """A refusal's line with every value the agent handed in taken out, longest first, so no text, quote, find
    or put or note it gave stays in the log."""
    out = str(line or "")
    for v in sorted({str(v) for v in values if len(str(v).strip()) >= 3}, key=len, reverse=True):
        out = out.replace(v, "…")
    return out


def strings(value, skip=()) -> list:
    """Every string in a value, a record's or a list's, a record's keys of `skip` left out."""
    if isinstance(value, str):
        return [value]
    if isinstance(value, dict):
        return [s for k, v in value.items() if k not in skip for s in strings(v, skip)]
    if isinstance(value, (list, tuple)):
        return [s for v in value for s in strings(v, skip)]
    return []


def call_of(words: list, known: int) -> str:
    """The command as given, its first `known` words and every flag's name, never a value."""
    out = [str(w) for w in words[:known] if not str(w).startswith("-")]
    for w in words[known:]:
        w = str(w)
        if w == "--":
            break
        if w.startswith("-") and len(w) > 1 and not w[1:2].isdigit():
            out.append(w.split("=", 1)[0])
    return agent_words(" ".join(out), CALL_MOST)


def entry(*, via: str, agent: str, call: str, code: str, line: str, request: str, values=(), project: str = "",
          closed: int = 0, op: str = "") -> dict:
    """An entry as the log keeps it, every word of the agent's cleaned and cut, the values it gave taken out."""
    return {"via": via, "agent": agent_words(agent, NAME_MOST), "project": "" if closed else str(project or ""),
            "closed": int(closed or 0), "op": op, "call": call, "code": code,
            "line": agent_words(scrubbed(line, values), WORDS_MOST), "request": agent_words(request, WORDS_MOST)}


# Where the command that was refused stood, which the app's own code says as it opens a project (see
# idiograph_cli.open_projects), so its entry names the project, or counts those agents may not read
HERE: dict = {"project": "", "closed": 0}


def begin() -> None:
    HERE.update(project="", closed=0)


def at_project(name: str) -> None:
    HERE.update(project=str(name or ""), closed=0)


def at_closed(n: int) -> None:
    HERE.update(project="", closed=int(n or 0))


# ------------------------------------------------------------------ the window's and the agents' reading

# A refusal's line as the window says it to him (agentlog, 3 November 2026, moved here from Idiograph's routes for
# Sift and Trace, siftlog, the same day): the agent's line speaks of him, so the window has its own words where one
# is drawn, and elsewhere the agent's line with him as "you", Sift's "field of his" and "are his alone" as "of
# yours" and "are yours"
YOU = ((r"\bhe ticks\b", "you tick"), (r"\bhe does\b", "you do"), (r"\bhe says\b", "you say"),
       (r"\bhe answers\b", "you answer"), (r"\bhe gives\b", "you give"), (r"\bhe asks\b", "you ask"),
       (r"\bhe made\b", "you made"), (r"\bHe\b", "You"), (r"\bhe\b", "you"), (r"\bhis own\b", "your own"),
       (r"\b(is|are) his(?=\s+alone\b|[,.;:]|$)", r"\1 yours"), (r"\bof his(?=[,.;:]|$)", "of yours"),
       (r"\bHis\b", "Your"), (r"\bhis\b", "your"), (r"\bhim\b", "you"))


def said(e: dict) -> str:
    """The line the window shows for a refusal: its own for one the drawings word, else the agent's to him."""
    import i18n
    op, code = str(e.get("op") or ""), str(e.get("code") or "")
    if op in ("hold approve", "hold decline"):
        return i18n.t("agentlog.why_hold")
    if code == "not_allowed":
        return i18n.t("agentlog.why_not_allowed")
    line = str(e.get("line") or "")
    for find, put in YOU:
        line = re.sub(find, put, line)
    return line


def api_agent_log(_body=None) -> dict:
    """The agent log as the window shows it under Settings, AI features, Using your own AI agents, the family's
    route `/api/agent-log` since siftlog (3 November 2026), so each app shows its own: the entries newest first,
    each refusal with its line as the window says it, `said`, and `total`. The page names each op for people by
    its words (agentlog.js, and each app's own table). It reads alone. An agent reads the same with `agents log`."""
    out = [e if e.get("kind") == "switch" else dict(e, said=said(e)) for e in read()]
    return {"entries": out, "total": len(out)}


def public(e: dict) -> dict:
    """An entry as an agent reads it: a refusal's when, agent, project, call, code, line and request, or a turn of
    the switch, on or off and from where. Every word of the agent's comes back marked (see `cli.mark`)."""
    out = {"kind": e.get("kind"), "at": e.get("at"), "time": e.get("time"), "count": int(e.get("count") or 1)}
    if e.get("kind") == "switch":
        return dict(out, on=e.get("on") is True, **{"from": e.get("from")})
    return dict(out, agent=e.get("agent") or "", project=e.get("project") or "", call=e.get("call") or "",
                code=e.get("code") or "", line=e.get("line") or "", request=e.get("request") or "")
