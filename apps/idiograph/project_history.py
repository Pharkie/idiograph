"""The project's own History (projhistory, 2 November 2026, Adam's yes by dialog that evening).

A change to the project itself, or to a participant as a whole, kept no History before: `project set` (the name,
the research question, the PET labels, the timecodes, and from the app the privacy tick), `timepoints`, `length`,
`participant rename`, `participant complete` and its reopen, and `gets settings` (the minimum, one per PET, the
most a new AI board proposes, a participant out of the study or back in). Each now adds one record to
`idiograph-history.json` at the project's root: when, the op, what changed from what to what, a line each, and
who asked, the app, or an agent by its tool with his request, as a board's History records an agent's change, the
tool carrying "approved in the app" or "without asking" where a hold applies (`holds.APPROVED`, `holds.WITHOUT`).

The record is written by the route that makes the change, under the same lock, the project's own
(`locks.root`), as the project file and the GETs file are, never by a second writer. A dry run, a refusal or a
change that changes nothing writes none. Agents read it with `project history` (MCP `project_history`). A send
never carries it (`project_pack.LEFT_OUT`), since its lines name participants a partial send leaves out.

    {"schema": 1, "history": [{"when": "2026-11-02T19:04:00+00:00", "op": "project set",
                               "changes": ["Name from \\"Bees\\" to \\"Keeping bees\\"."],
                               "by": "agent", "tool": "Claude Code", "request": "his words"}]}

A record of the app's has `"by": "app"` and no tool or request.
"""
from __future__ import annotations

import json
from pathlib import Path

import locks
import server as srv
from themes import now_iso

FILE = "idiograph-history.json"
SCHEMA = 1
HISTORY_MAX = 500
TOOL_MAX = 80
REQUEST_MAX = 2000


def one_line(text) -> str:
    return " ".join(str(text or "").split())


def path_of(root: Path) -> Path:
    return Path(root) / FILE


def load(root: Path) -> list[dict]:
    """The records at a root, oldest first, an empty list for no file or one that cannot be read."""
    try:
        data = json.loads(path_of(root).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return []
    held = data.get("history") if isinstance(data, dict) else None
    return [h for h in held if isinstance(h, dict)] if isinstance(held, list) else []


def asker(body: dict | None) -> dict:
    """Who asked, from a route's body: an agent's `tool` and `request` (or `note`), the command line's and MCP's,
    or the app's, which sends neither."""
    body = body if isinstance(body, dict) else {}
    tool = one_line(body.get("tool") or "")[:TOOL_MAX]
    request = one_line(body.get("request") or body.get("note") or "")[:REQUEST_MAX]
    if tool or request:
        return {"by": "agent", "tool": tool, "request": request}
    return {"by": "app"}


def record(root: Path, op: str, changes: list[str], who: dict | None = None, when: str | None = None) -> dict | None:
    """One record added, the caller holding the project's lock. No line, no record. Answers the record."""
    lines = [str(c) for c in changes or [] if str(c).strip()]
    # the demo, which ships as it is, keeps none
    if root is None or not lines or not Path(root).is_dir() or srv.is_demo_root(root):
        return None
    entry = dict({"when": when or now_iso(), "op": op, "changes": lines}, **(who or {"by": "app"}))
    held = load(root)[-(HISTORY_MAX - 1):] + [entry]
    target = path_of(root)
    tmp = target.with_name(target.name + ".tmp")
    tmp.write_text(json.dumps({"schema": SCHEMA, "history": held}, indent=1, ensure_ascii=False) + "\n",
                   encoding="utf-8", newline="\n")
    locks.replace(tmp, target)
    return entry


def snapshot(root: Path) -> tuple:
    """The file as it stands, for a change that may have to put it back: ("bytes", path, data) or ("file", path)."""
    target = path_of(root)
    return ("bytes", target, target.read_bytes()) if target.is_file() else ("file", target)


def newest(root: Path, limit: int | None = None, offset: int = 0, by: str = "") -> tuple[list[dict], int]:
    """The records newest first, from `offset` on and `limit` of them when it is a whole number above 0, those by
    the app alone or by an agent alone when `by` is "app" or "agent", and how many there are in all with that `by`:
    what `project history`, MCP's `project_history` and the page's Project history read alike, the page a page at a
    time."""
    held = list(reversed(load(root))) if root is not None else []
    if by in ("app", "agent"):
        held = [h for h in held if (h.get("by") == "agent") == (by == "agent")]
    start = offset if isinstance(offset, int) and offset > 0 else 0
    end = start + limit if isinstance(limit, int) and limit > 0 else None
    return held[start:end], len(held)


def line_shown(text) -> str:
    """A change's line as the page shows it: one line, nothing a reader cannot see, no address drawn as a link. Its
    quotation marks stay, since the line is the app's own sentence round the words it names."""
    import holds
    clean = "".join(ch for ch in one_line(text) if not holds.unseen(ch))
    return " ".join(clean.replace("://", ": //").split())


def for_page(h: dict) -> dict:
    """One record as Project history on Home shows it (historyui, 3 November 2026): when, its lines,
    and who asked, the app, or an agent by its name with `hold`, "approved" or "without", where a hold applied, and
    his request, the agent's words cleaned as a held change's card cleans them (`holds.agent_words`)."""
    import holds
    out = {"when": str(h.get("when") or ""), "op": str(h.get("op") or ""),
           "changes": [line_shown(c) for c in h.get("changes") or [] if line_shown(c)]}
    if h.get("by") == "member":
        # a teammate's suggestion accepted (wtsuggest, 10 November 2026): who suggested it, and who accepted it
        return dict(out, by="member", member=holds.agent_words(h.get("member"), holds.NAME_MOST),
                    accepted_by=holds.agent_words(h.get("accepted_by"), holds.NAME_MOST))
    if h.get("by") != "agent":
        return dict(out, by="app")
    tool, hold = one_line(h.get("tool")), ""
    for word, ending in (("approved", holds.APPROVED), ("without", holds.WITHOUT)):
        if tool.endswith(", " + ending):
            tool, hold = tool[:-len(", " + ending)], word
    return dict(out, by="agent", agent=holds.agent_words(tool, holds.NAME_MOST), hold=hold,
                request=holds.agent_words(h.get("request")))
