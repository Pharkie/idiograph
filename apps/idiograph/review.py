"""Working together's comments and review (wtreview, 8 November 2026, the spec of that day, sections 4, 7 and 8,
Adam's yes to all its defaults about 19:10, review comments drafts until Send review, made one with the team layer
by wtreview2, 9 November 2026).

One analyst owns each participant. A teammate who does not own it asks nothing of its files: he comments on a
passage, a statement, a PET or a GET, each comment a draft on his machine until Send review, and the owner sees one
line when the review comes, opens it, and answers each comment with Reply or Resolve. Replies and a thread's state
go at once. The owner asks for a review from the participant's menu, with a line for the reviewer, and the
participant shows "With Curt for review" on the project's page until Curt's review or board comes back
(`team_sync.REVIEW_WITH`).

The messages are the spec's: `review_asked`, `comment` (a thread's first comment and every reply), `thread_state`
(resolved, unresolved, kept visible, or reopened) and `review` (the ids it sends). Each is sealed by team.py under
the project's present key and signed by this computer, and goes through team_sync's one loop (`team_sync.post`), so
it travels by the relay or the shared folder alike. What comes is opened and checked there, where a message from a
device not on the roster or with a bad seal is dropped, and one of these kinds sealed under an older epoch's key is
dropped too (`team_sync.EPOCH_NOW`). It then comes here (`came`, through `team_sync.HANDLERS`), where a kind its
member may not send is dropped and noted in the team log. A board a teammate sends (team_board.py) shows on the
same line and card as the rest of that teammate's review, waiting for Add as next board or Decline, whose `answer`
goes back through the same loop. Who is who, the roster, the owners and the names, is team.py's alone.

What came and what was drafted is kept in `.idiograph-team/review.json` at the project's root, this install's own,
never in Share a copy (`project_pack.LEFT_OUT`). A participant is named in a message by its folder from the root,
the GETs board by "". While Working together is off every op here refuses in one line, and the app shows nothing.

Every op runs through this module, the page's `/api/team-review` and the command line's `team ...` (MCP `team_*`)
alike (one API, two clients), each with a dry run, and each write adds one record to the project's History
(`project_history`). A teammate's words reach an agent marked as untrusted text (`cli.mark`), never under a plain
key.
"""
from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from pathlib import Path

import i18n
import locks
import project_history as hist_mod
import team as team_mod
import team_sync

STATE = "review.json"
LOCK = ".review.lock"
SCHEMA = 2
KINDS_ON = ("passage", "statement", "pet", "get")
# what a suggestion is on (wtsuggest, 10 November 2026): a statement's wording, a PET's title or a GET's
SUGGEST_ON = ("statement", "pet", "get")
STATES = ("resolved", "unresolved", "reopened")
# the kinds this module sends and takes in, each through team_sync's one loop. An `answer` to a suggestion comes
# through team_sync's `answer` taker, shared with a board's (see `take_answer`)
KINDS = ("review_asked", "comment", "thread_state", "review", "suggestion")
TEXT_MAX = 4000
WORDS_MAX = 600
# the GETs board, as a message and a review of it name it
GETS = ""


class Refused(Exception):
    """An op that cannot go ahead, in one plain line, with nothing written."""


class _Said:
    """The catalogue's words, each key written out whole where it is said, so the catalogue's check finds it."""

    @staticmethod
    def t(key: str, **vals) -> str:
        return i18n.t(key, vals)


SAID = _Said()


# what a comment is on, and a thread's new state as History says it, each its catalogue key written out
ON_WHAT = {"passage": lambda: SAID.t("review.on.passage"), "statement": lambda: SAID.t("review.on.statement"),
           "pet": lambda: SAID.t("review.on.pet"), "get": lambda: SAID.t("review.on.get")}
STATE_SAID = {"resolved": lambda **v: SAID.t("review.history.resolved", **v),
              "unresolved": lambda **v: SAID.t("review.history.unresolved", **v),
              "reopened": lambda **v: SAID.t("review.history.reopened", **v)}


def one_line(text) -> str:
    return " ".join(str(text or "").split())


def now_iso() -> str:
    return datetime.now().astimezone().isoformat(timespec="seconds")


def when(text) -> datetime:
    """A time as a message or the record keeps it, for comparing, the earliest time when it cannot be read."""
    try:
        at = datetime.fromisoformat(str(text))
    except (TypeError, ValueError):
        return datetime.min.replace(tzinfo=timezone.utc)
    return at if at.tzinfo else at.replace(tzinfo=timezone.utc)


def new_id() -> str:
    return uuid.uuid4().hex[:16]


def folder(root: Path) -> Path:
    return Path(root) / team_mod.LOG_DIR


# ------------------------------------------------------------------ the team, as team.py keeps it

def team(root: Path) -> dict | None:
    """Working together in this project as this install sees it, or None while it is off: the members by id from
    the roster, this install's member and computer, the lead and the GETs board's owner."""
    if root is None:
        return None
    data = team_sync.team_on(Path(root))
    if data is None:
        return None
    roster = data["roster"]
    members = {}
    for m in team_mod.roster_members(roster):
        mid = str(m.get("id") or "")
        if mid:
            members[mid] = {"id": mid, "name": one_line(m.get("name")) or mid,
                            "devices": [str(d.get("id")) for d in m.get("devices") or [] if isinstance(d, dict)]}
    me = str(data.get("member") or "")
    if me not in members:
        return None
    lead = str(roster.get("lead") or "")
    return {"data": data, "members": members, "me": me, "device": (team_mod.device() or {}).get("id") or "",
            "lead": lead, "gets_owner": team_sync.gets_owner(roster)}


def is_on(root: Path) -> bool:
    return team(root) is not None


def need(root: Path) -> dict:
    t = team(root)
    if t is None:
        raise Refused(SAID.t("review.off"))
    return t


def owner_of(t: dict, participant: str) -> str:
    """The member who owns a participant, by its folder, or the GETs board's for ""."""
    if participant == GETS:
        return t["gets_owner"]
    return team_mod.owner_here(t["data"], participant)


def name_of(t: dict, member: str) -> str:
    m = t["members"].get(member)
    return m["name"] if m else member


def said_by(t: dict, member: str, tool: str = "") -> str:
    """A comment's author as the screens say it, "Curt", or "Curt (Claude Code)" for his agent's."""
    who = name_of(t, member)
    return SAID.t("review.by_agent", name=who, tool=tool) if tool else who


# ------------------------------------------------------------------ participants, by folder

def names(root: Path) -> dict:
    """Each participant's pseudonym by its folder, as a line names it, `Juno` for `P1 - Juno`."""
    import idiograph_routes as routes
    return {p["folder"]: team_sync.pseudonym(p["label"]) for p in routes.participant_books(root)}


def what_of(named: dict, participant: str) -> str:
    """A participant by its pseudonym, or the GETs board."""
    if participant == GETS:
        return SAID.t("review.gets_board")
    return named.get(participant) or team_sync.pseudonym(Path(participant).name)


def folder_named(root: Path, case) -> str:
    """A participant's folder from its pseudonym or label, "" (the GETs board) for none. Refused when there is no
    such participant."""
    import team_board as board_mod
    if case is None or not str(case).strip():
        return GETS
    try:
        return board_mod.participant(root, str(case))["folder"]
    except team_mod.TeamError as exc:
        raise Refused(str(exc)) from None


def folder_of_path(root: Path, path) -> str:
    """A participant's folder from its workbook's path, "" when it is in no participant's folder of the project."""
    import workbook as wb_mod
    try:
        rel = wb_mod.case_folder(Path(path)).resolve().relative_to(Path(root).resolve()).as_posix()
    except ValueError:
        return GETS
    return "" if rel == "." else rel


# ------------------------------------------------------------------ what this install holds

def _blank() -> dict:
    return {"schema": SCHEMA, "applied": [], "drafts": [], "asks": [], "threads": {}, "reviews": [], "suggestions": []}


def load(root: Path) -> dict:
    try:
        held = json.loads((folder(root) / STATE).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        held = {}
    st = _blank()
    for k, v in (held if isinstance(held, dict) else {}).items():
        if k in st and isinstance(v, type(st[k])):
            st[k] = v
    return st


def _save(root: Path, st: dict) -> None:
    target = folder(root) / STATE
    target.parent.mkdir(parents=True, exist_ok=True)
    tmp = target.with_name(target.name + ".tmp")
    tmp.write_text(json.dumps(st, ensure_ascii=False, indent=1) + "\n", encoding="utf-8", newline="\n")
    locks.replace(tmp, target)


def _lock(root: Path):
    return locks.held(folder(root) / LOCK)


def _history(root: Path, op: str, changes: list[str], who: dict | None) -> None:
    with locks.root(root):
        hist_mod.record(root, op, changes, who or {"by": "app"})


# ------------------------------------------------------------------ messages out and in

def _sendable(root: Path) -> None:
    """Refused before anything is written when this computer cannot seal for the team: no keys, or no key for the
    roster's epoch yet."""
    data = team_sync.team_on(Path(root)) or {}
    dev = team_mod.device()
    epoch = int((data.get("roster") or {}).get("epoch") or 1)
    if not dev or team_mod.project_key(str(data.get("team") or ""), epoch) is None:
        raise Refused(i18n.t("team.refused.no_key"))


def _send(t: dict, st: dict, out: list, kind: str, body: dict, tool: str = "") -> dict:
    """One message applied here as it is sent, and added to `out`, which `_post` hands to team_sync's loop once the
    record is saved."""
    body = dict(body, **({"tool": tool} if tool else {}))
    msg = {"id": new_id(), "kind": kind, "member": t["me"], "device": t["device"], "sent": now_iso(), "body": body}
    _apply(t, st, msg)
    out.append((kind, body))
    return msg


def _post(root: Path, out: list) -> None:
    """Each message sealed and sent through team_sync's loop, in order, kept sealed until a connection takes it."""
    for kind, body in out:
        try:
            team_sync.post(root, kind, body)
        except team_mod.TeamError as exc:
            raise Refused(str(exc)) from None


def _may(t: dict, st: dict, msg: dict) -> str:
    """Why a message may not apply, or "": its member on the roster, and a kind he may send of what he may send it
    on. The seal, the device and the signature were checked by team.py before it came here."""
    member, kind, body = str(msg.get("member") or ""), msg.get("kind"), msg.get("body")
    if member not in t["members"]:
        return "not_on_roster"
    if not isinstance(body, dict):
        return "no_body"
    if kind == "review_asked":
        return "" if owner_of(t, str(body.get("participant") or "")) == member else "not_owner"
    if kind == "comment":
        on = body.get("on") if isinstance(body.get("on"), dict) else {}
        th = st["threads"].get(str(body.get("thread") or ""))
        if th is None and owner_of(t, str(on.get("participant") or "")) == member:
            return "own_thread"
        if th is not None and member not in (owner_of(t, th["participant"]), th["by"]):
            return "not_his_thread"
        return "" if str(body.get("text") or "").strip() else "no_words"
    if kind == "thread_state":
        th = st["threads"].get(str(body.get("thread") or ""))
        if th is None:
            return "no_thread"
        ok = member in (owner_of(t, th["participant"]), th["by"]) and body.get("state") in STATES
        return "" if ok else "not_his_thread"
    if kind == "review":
        return "" if owner_of(t, str(body.get("participant") or "")) != member else "own_review"
    if kind == "suggestion":
        on = body.get("on") if isinstance(body.get("on"), dict) else {}
        if on.get("kind") not in SUGGEST_ON or not str(body.get("text") or "").strip():
            return "no_words"
        if owner_of(t, str(on.get("participant") or "")) == member:
            return "own_suggestion"
        return "" if _op_ok(body.get("op"), on.get("kind")) else "not_an_op"
    if kind == "answer":
        s = next((x for x in st["suggestions"] if x["id"] == str(body.get("of") or "")), None)
        if s is None or s["by"] != t["me"]:
            return "no_suggestion"
        return "" if owner_of(t, s["participant"]) == member else "not_owner"
    return "kind_not_allowed"


def _apply(t: dict, st: dict, msg: dict) -> None:
    """A message's change to what this install holds, each kind as the spec's section 4 has it."""
    if msg["id"] in st["applied"]:
        return
    st["applied"].append(msg["id"])
    kind, body, member, at = msg["kind"], msg["body"], msg["member"], msg.get("sent") or now_iso()
    tool = one_line(body.get("tool"))[:80]
    if kind == "review_asked":
        st["asks"].append({"id": msg["id"], "participant": str(body.get("participant") or ""), "by": member,
                           "to": [str(x) for x in body.get("to") or []], "line": str(body.get("line") or ""),
                           "n": body.get("n") or 0, "at": at})
    elif kind == "comment":
        on = body.get("on") if isinstance(body.get("on"), dict) else {}
        tid = str(body.get("thread") or body.get("id"))
        th = st["threads"].get(tid)
        if th is None:
            th = st["threads"][tid] = {"id": tid, "participant": str(on.get("participant") or ""), "on": {
                "kind": str(on.get("kind") or ""), "key": str(on.get("key") or ""),
                "words": str(on.get("words") or "")[:WORDS_MAX], "time": str(on.get("time") or ""),
                "label": str(on.get("label") or "")}, "by": member, "status": "open", "review": "", "comments": []}
        if not any(c["id"] == body.get("id") for c in th["comments"]):
            th["comments"].append({"id": str(body.get("id") or msg["id"]), "member": member, "tool": tool,
                                   "text": str(body.get("text") or "")[:TEXT_MAX], "at": at})
            # a word in a thread its owner left open asks for him again
            if member != owner_of(t, th["participant"]) and th["status"] == "unresolved":
                th["status"] = "open"
    elif kind == "thread_state":
        th = st["threads"][str(body["thread"])]
        th["status"] = "open" if body["state"] == "reopened" else body["state"]
        th["status_by"], th["status_at"] = member, at
    elif kind == "review":
        items = [str(x) for x in body.get("items") or []]
        offered = [str(x) for x in body.get("suggestions") or []]
        rid = str(body.get("id") or msg["id"])
        st["reviews"].append({"id": rid, "participant": str(body.get("participant") or ""),
                              "by": member, "line": str(body.get("line") or ""), "items": items, "suggestions": offered,
                              "n": body.get("n") or 0, "sent": at, "seen": member == t["me"], "tool": tool})
        for tid in items:
            if tid in st["threads"]:
                st["threads"][tid]["review"] = rid
        for s in st["suggestions"]:
            if s["id"] in offered:
                s["review"] = rid
    elif kind == "suggestion":
        sid = str(body.get("id") or msg["id"])
        on = body["on"]
        mine = member == t["me"]
        held = next((x for x in st["suggestions"] if x["id"] == sid), None)
        if held is None:
            held = {"id": sid, "participant": str(on.get("participant") or "")}
            st["suggestions"].append(held)
        held.update({"by": member, "tool": tool, "on": _on_kept(on), "seen": str(body.get("seen") or "")[:WORDS_MAX],
                     "text": one_line(body.get("text"))[:WORDS_MAX], "reason": str(body.get("reason") or "")[:TEXT_MAX],
                     "op": body.get("op") if isinstance(body.get("op"), dict) else {}, "at": at,
                     "status": "sent" if mine else "waiting", "answer": "", "review": held.get("review") or ""})
    elif kind == "answer":
        s = next(x for x in st["suggestions"] if x["id"] == str(body.get("of") or ""))
        if not s.get("answer"):
            s.update(answer="accepted" if body.get("accept") is True else "declined",
                     answer_reason=str(body.get("reason") or "")[:TEXT_MAX], answered=at, answered_by=member)


def came(root: Path, _data: dict, inner: dict) -> None:
    """A message of one of these kinds, opened and checked by team_sync's loop, applied here, or dropped and noted
    in the team log when its member may not send it. One taken in before is passed over."""
    t = team(root)
    if t is None:
        return
    with _lock(root):
        st = load(root)
        if inner.get("id") in st["applied"]:
            return
        msg = {k: inner.get(k) for k in ("id", "kind", "member", "device", "sent", "body")}
        why = _may(t, st, msg)
        if why:
            st["applied"].append(msg["id"])
            team_mod.note_dropped(root, why, str(msg.get("device") or ""))
        else:
            _apply(t, st, msg)
        _save(root, st)


def review_with(root: Path) -> dict:
    """`team_sync.REVIEW_WITH`: each participant of this member's asked for review, by its folder, with the first
    teammate asked whose review or board has not come back since, for the project page's "With Curt for review"."""
    t = team(root)
    if t is None:
        return {}
    st = load(root)
    import team_board as board_mod
    boards = board_mod.read_ledger(root)["came"]
    latest = {}
    for a in st["asks"]:
        if a["by"] == t["me"] and a["participant"] != GETS and owner_of(t, a["participant"]) == t["me"]:
            latest[a["participant"]] = a
    out = {}
    for participant, a in latest.items():
        asked = when(a["at"])
        for member in a["to"]:
            back = any(r["by"] == member and r["participant"] == participant and when(r["sent"]) >= asked
                       for r in st["reviews"]) or any(
                b.get("from") == member and b.get("folder") == participant and when(b.get("sent")) >= asked
                for b in boards)
            if not back and member in t["members"]:
                out[participant] = member
                break
    return out


# ------------------------------------------------------------------ the ops

def _counts(n_comments: int, n_suggestions: int = 0) -> str:
    """"2 comments", "1 suggestion" or "2 comments, 1 suggestion"."""
    comments = i18n.t("review.n.comments", {"n": n_comments})
    if not n_suggestions:
        return comments
    suggestions = i18n.t("review.n.suggestions", {"n": n_suggestions})
    return i18n.t("review.n.pair", {"comments": comments, "suggestions": suggestions}) if n_comments else suggestions


def ask(root: Path, participant: str, to: list[str], line: str, who: dict | None = None, dry: bool = False) -> dict:
    """Ask teammates to review a participant he owns, with a line for them (review_asked)."""
    t = need(root)
    named = names(root)
    if participant == GETS or owner_of(t, participant) != t["me"]:
        raise Refused(SAID.t("review.ask_not_yours", name=what_of(named, participant),
                             owner=name_of(t, owner_of(t, participant))))
    others = {m["id"]: m for m in t["members"].values() if m["id"] != t["me"]}
    picked = []
    for x in to or []:
        said = one_line(x).lower()
        hit = next((m["id"] for m in others.values() if said in (m["id"].lower(), m["name"].lower())), None)
        if hit is None:
            raise Refused(SAID.t("review.ask_who", names=", ".join(m["name"] for m in others.values()) or "-"))
        if hit not in picked:
            picked.append(hit)
    if not picked:
        raise Refused(SAID.t("review.ask_who", names=", ".join(m["name"] for m in others.values()) or "-"))
    change = SAID.t("review.history.asked", name=what_of(named, participant),
                    names=", ".join(name_of(t, m) for m in picked))
    if dry:
        return {"dry_run": True, "changes": [change]}
    _sendable(root)
    out = []
    with _lock(root):
        st = load(root)
        msg = _send(t, st, out, "review_asked", {"participant": participant, "to": picked,
                                                 "line": str(line or "").strip()[:TEXT_MAX], "n": 0})
        _save(root, st)
    _post(root, out)
    _history(root, "team ask", [change], who)
    return {"dry_run": False, "changes": [change], "id": msg["id"]}


def _tool(who: dict | None) -> str:
    return ((who or {}).get("tool") or "") if (who or {}).get("by") == "agent" else ""


def comment(root: Path, participant: str, on: dict, text: str, who: dict | None = None, dry: bool = False) -> dict:
    """A comment on a passage, a statement, a PET or a GET of a participant he does not own, kept as a draft of his
    review for its owner until Send review."""
    t = need(root)
    named = names(root)
    kind = str(on.get("kind") or "")
    if kind not in KINDS_ON:
        raise Refused(SAID.t("review.on_what"))
    if kind == "get":
        participant = GETS
    text = str(text or "").strip()
    if not text:
        raise Refused(SAID.t("review.no_words"))
    owner = owner_of(t, participant)
    if owner == t["me"]:
        raise Refused(SAID.t("review.comment_yours", name=what_of(named, participant)))
    on = {"participant": participant, "kind": kind, "key": str(on.get("key") or ""),
          "words": str(on.get("words") or "")[:WORDS_MAX], "time": one_line(on.get("time")),
          "label": one_line(on.get("label"))}
    change = SAID.t("review.history.drafted", what=ON_WHAT[kind](), name=what_of(named, participant),
                    owner=name_of(t, owner))
    if dry:
        return {"dry_run": True, "changes": [change]}
    draft = {"id": new_id(), "thread": new_id(), "participant": participant, "on": on, "text": text[:TEXT_MAX],
             "at": now_iso(), "tool": _tool(who)}
    with _lock(root):
        st = load(root)
        st["drafts"].append(draft)
        _save(root, st)
    _history(root, "team comment", [change], who)
    return {"dry_run": False, "changes": [change], "id": draft["id"], "thread": draft["thread"]}


def drafts_of(st: dict, participant: str | None = None) -> list[dict]:
    return [d for d in st["drafts"] if participant is None or d["participant"] == participant]


def send(root: Path, participant: str, line: str = "", who: dict | None = None, dry: bool = False) -> dict:
    """Send review: every draft on a participant goes to its owner, each comment first, then the review naming
    them. Nothing goes before this."""
    t = need(root)
    named = names(root)
    st = load(root)
    drafts = drafts_of(st, participant)
    offered = suggestion_drafts(st, participant)
    if not drafts and not offered:
        raise Refused(SAID.t("review.nothing_to_send", name=what_of(named, participant)))
    owner = owner_of(t, participant)
    change = SAID.t("review.history.sent", owner=name_of(t, owner), name=what_of(named, participant),
                    counts=_counts(len(drafts), len(offered)))
    if dry:
        return {"dry_run": True, "changes": [change]}
    _sendable(root)
    out = []
    with _lock(root):
        st = load(root)
        drafts = drafts_of(st, participant)
        offered = suggestion_drafts(st, participant)
        rid = new_id()
        for d in drafts:
            _send(t, st, out, "comment", {"id": d["id"], "thread": d["thread"],
                                          "on": dict(d["on"], participant=participant), "text": d["text"], "n": 0},
                  tool=d.get("tool") or "")
        # each suggestion the op it would run, not run, with what it changes as he saw it (spec, section 4, kind 6)
        for s in offered:
            _send(t, st, out, "suggestion", {"id": s["id"], "on": dict(s["on"], participant=participant),
                                             "op": s["op"], "seen": s["seen"], "text": s["text"],
                                             "reason": s.get("reason") or "", "n": 0}, tool=s.get("tool") or "")
        _send(t, st, out, "review", {"id": rid, "participant": participant, "n": 0, "line": str(line or "").strip(),
                                     "items": [d["thread"] for d in drafts],
                                     "suggestions": [s["id"] for s in offered]}, tool=_tool(who))
        sent = {d["id"] for d in drafts}
        st["drafts"] = [d for d in st["drafts"] if d["id"] not in sent]
        _save(root, st)
    _post(root, out)
    _history(root, "team review send", [change], who)
    return {"dry_run": False, "changes": [change], "id": rid}


def _thread(st: dict, tid: str) -> dict:
    th = st["threads"].get(str(tid or ""))
    if th is None:
        raise Refused(SAID.t("review.no_thread"))
    return th


def reply(root: Path, tid: str, text: str, who: dict | None = None, dry: bool = False) -> dict:
    """A reply in a thread, sent at once, by its participant's owner or the teammate who began it."""
    t = need(root)
    st = load(root)
    th = _thread(st, tid)
    if t["me"] not in (owner_of(t, th["participant"]), th["by"]):
        raise Refused(SAID.t("review.not_your_thread"))
    text = str(text or "").strip()
    if not text:
        raise Refused(SAID.t("review.no_words"))
    change = SAID.t("review.history.replied", what=ON_WHAT[th['on']['kind']](),
                    name=what_of(names(root), th["participant"]))
    if dry:
        return {"dry_run": True, "changes": [change]}
    _sendable(root)
    out = []
    with _lock(root):
        st = load(root)
        th = _thread(st, tid)
        cid = new_id()
        _send(t, st, out, "comment", {"id": cid, "thread": th["id"], "on": dict(th["on"], participant=th["participant"]),
                                      "text": text[:TEXT_MAX], "n": 0}, tool=_tool(who))
        _save(root, st)
    _post(root, out)
    _history(root, "team reply", [change], who)
    return {"dry_run": False, "changes": [change], "id": cid}


def thread_state(root: Path, tid: str, state: str, who: dict | None = None, dry: bool = False) -> dict:
    """A thread resolved, kept unresolved or reopened, sent at once (thread_state)."""
    t = need(root)
    if state not in STATES:
        raise Refused(SAID.t("review.which_state"))
    st = load(root)
    th = _thread(st, tid)
    if t["me"] not in (owner_of(t, th["participant"]), th["by"]):
        raise Refused(SAID.t("review.not_your_thread"))
    change = STATE_SAID[state](what=ON_WHAT[th['on']['kind']](), name=what_of(names(root), th["participant"]))
    if dry:
        return {"dry_run": True, "changes": [change]}
    _sendable(root)
    out = []
    with _lock(root):
        st = load(root)
        _send(t, st, out, "thread_state", {"thread": th["id"], "state": state})
        _save(root, st)
    _post(root, out)
    _history(root, "team thread", [change], who)
    return {"dry_run": False, "changes": [change]}


def done(root: Path, rid: str, who: dict | None = None, dry: bool = False) -> dict:
    """Done on a review: it is read, and each of its threads he neither resolved nor kept goes to its sender as
    kept unresolved, still on view on both machines. A board of it still waiting keeps waiting."""
    t = need(root)
    st = load(root)
    rv = next((r for r in st["reviews"] if r["id"] == rid and r["by"] != t["me"]), None)
    if rv is None:
        raise Refused(SAID.t("review.no_review"))
    open_ids = [x for x in rv["items"] if x in st["threads"] and st["threads"][x]["status"] == "open"]
    change = SAID.t("review.history.read", owner=name_of(t, rv["by"]), name=what_of(names(root), rv["participant"]),
                    counts=_counts(len(open_ids)))
    if dry:
        return {"dry_run": True, "changes": [change]}
    if open_ids:
        _sendable(root)
    out = []
    with _lock(root):
        st = load(root)
        rv = next(r for r in st["reviews"] if r["id"] == rid)
        rv["seen"] = True
        for x in open_ids:
            _send(t, st, out, "thread_state", {"thread": x, "state": "unresolved"})
        _save(root, st)
    _post(root, out)
    _history(root, "team review done", [change], who)
    return {"dry_run": False, "changes": [change]}


# ------------------------------------------------------------------ suggestions (wtsuggest, 10 November 2026)
#
# Adam, 10 November about 10:55, by dialog: Working together's suggestions next, the spec's build 5 as drawn and
# approved (wtshots 08, 09 and 11). A teammate on a participant he does not own suggests a statement's wording,
# a PET's title or a GET's, each a draft in his tray until Send review. What goes is the op the command line would
# run, not run: `turn write` with the passage's pairs for a wording, `board apply` with a `retitle` for a PET's
# title, `gets apply` with one for a GET's, with `seen`, the words as he saw them, and his reason. On the owner's
# install it waits on the review card, Now beside the teammate's words. Accept runs the op as `holds.approve`
# runs a held one, on the target as it stands now, found by its words first and its key second (the rule
# `themes.follow` keeps), so a passage changed since keeps every other change (Choice 4: a changed suggestion is
# still accepted, by its dry run). Its History record carries `by: "member"`, `member`, `accepted_by` and
# `suggestion`, its tool "Curt's suggestion, accepted in the app". Decline writes nothing to the files. Either
# goes back to the teammate as an `answer`. A suggestion whose statement, PET or GET is gone is Decline only.

def suggestion_drafts(st: dict, participant: str | None = None) -> list[dict]:
    return [s for s in st["suggestions"] if s.get("status") == "draft"
            and (participant is None or s["participant"] == participant)]


def _on_kept(on: dict) -> dict:
    return {"kind": str(on.get("kind") or ""), "key": str(on.get("key") or ""), "time": one_line(on.get("time")),
            "label": one_line(on.get("label")), "board": one_line(on.get("board"))}


def _op_ok(op, kind) -> bool:
    """Whether a suggestion's op is the one its kind runs, and nothing else."""
    if not isinstance(op, dict):
        return False
    want = {"statement": ("turn", "write"), "pet": ("board", "apply"), "get": ("gets", "apply")}.get(kind)
    return want is not None and (op.get("command"), op.get("act")) == want


def _book(root: Path, participant: str) -> Path:
    import team_board as board_mod
    return Path(board_mod.participant(root, folder=participant)["workbook"])


def _target(root: Path, participant: str, on: dict, seen: str) -> dict:
    """What a suggestion changes, as the files here hold it now, found by its words first and its key second:
    `{"gone": False, "now", "stale", ...}`, the statement's `sheet`, `row`, `line` and its `turn`, or the PET's or
    GET's `board` and `label`. `stale` when only the key found it, its words changed since. `{"gone": True}` when
    neither finds it."""
    import cli as family_cli
    import idiograph_cli as icli
    import gets as gets_mod
    import themes as themes_mod
    from workbook import WorkbookError
    kind = on.get("kind")
    want = themes_mod.words(seen)
    try:
        if kind == "statement":
            sheet, row, line = themes_mod.split_card_key(on.get("key"))
            if row is None:
                return {"gone": True}
            rows, _cols = icli.turns_of(_book(root, participant), sheet)
            turn = next((x for x in rows if x["row"] == row), None)
            if turn is None:
                return {"gone": True}
            said = turn["statements"]
            hits = [i for i, x in enumerate(said) if themes_mod.words(x) == want] if want else []
            if hits:
                at, stale = (line if line in hits else hits[0]), False
            elif line is not None and 0 <= line < len(said):
                at, stale = line, True
            else:
                return {"gone": True}
            return {"gone": False, "now": said[at], "stale": stale, "sheet": sheet, "row": row, "line": at, "turn": turn}
        data = themes_mod.load(_book(root, participant)) if kind == "pet" else gets_mod.load(root)
        boards = [b for b in themes_mod.boards_of(data) if not b.get(themes_mod.OWN)]
        board = next((b for b in boards if str(b.get("id")) == on.get("board")), None)
        if board is None:
            chosen = themes_mod.chosen_of(data)
            canvas = themes_mod.current_version(data) or {}
            board = (next((b for b in boards if str(b.get("id")) == chosen), None)
                     or next((b for b in boards if b.get("id") == canvas.get("id")), None) or (boards[0] if boards else None))
        if board is None:
            return {"gone": True}
        groups = [g for g in board.get("groups") or [] if isinstance(g, dict)]
        hit = next((g for g in groups if want and themes_mod.words(g.get("label")) == want), None)
        stale = False
        if hit is None:
            hit, stale = next((g for g in groups if str(g.get("id")) == on.get("key")), None), True
        if hit is None:
            return {"gone": True}
        return {"gone": False, "now": str(hit.get("label") or ""), "stale": stale, "board": str(board.get("id")),
                "board_name": str(board.get("name") or ""), "label": str(hit.get("id"))}
    except (family_cli.Refused, team_mod.TeamError, WorkbookError, OSError, ValueError):
        return {"gone": True}


def _op_for(root: Path, participant: str, kind: str, found: dict, text: str, request: str) -> dict:
    """The op a suggestion runs, as the command line would run it, on the target as `_target` found it."""
    import themes as themes_mod
    case = what_of(names(root), participant) if participant != GETS else ""
    if kind == "statement":
        turn, sheet, row = found["turn"], found["sheet"], found["row"]
        places = turn["places"]
        # every statement of the passage as it stands, each by its key, the one suggested in its new words, its quote
        # kept, as board import writes a passage's rewording
        pairs = [{"statement": text if i == found["line"] else x, "quote": places[i] if i < len(places) else "",
                  "key": themes_mod.card_key(sheet, row, i)} for i, x in enumerate(turn["statements"])]
        return {"command": "turn", "act": "write", "case": case, "sheet": sheet, "row": str(row),
                "from": {"pairs": pairs, "request": request}}
    ops = {"operations": [{"op": "retitle", "label": found["label"], "title": text}], "request": request}
    if kind == "pet":
        return {"command": "board", "act": "apply", "case": case, "board": found["board"], "ops": ops}
    return {"command": "gets", "act": "apply", "board": found["board"], "ops": ops}


def _what_on(kind: str) -> str:
    return ON_WHAT[kind]()


def suggest(root: Path, participant: str, on: dict, text: str, reason: str = "", who: dict | None = None,
            dry: bool = False) -> dict:
    """A suggestion on a statement, a PET or a GET of a participant he does not own, kept as a draft of his review
    for its owner until Send review, as a comment is (Choice 5). `on` is `{kind, key, words, time, label, board}`,
    `words` what it reads as he sees it, read from his copy when left out."""
    t = need(root)
    named = names(root)
    kind = str(on.get("kind") or "")
    if kind not in SUGGEST_ON:
        raise Refused(SAID.t("review.suggest.on_what"))
    if kind == "get":
        participant = GETS
    owner = owner_of(t, participant)
    if owner == t["me"]:
        raise Refused(SAID.t("review.suggest.yours", name=what_of(named, participant)))
    text = one_line(text)[:WORDS_MAX]
    if not text:
        raise Refused(SAID.t("review.suggest.no_words"))
    kept = _on_kept(on)
    seen = one_line(on.get("words"))
    found = _target(root, participant, kept, seen)
    if found["gone"]:
        raise Refused(SAID.t("review.suggest.not_there", name=what_of(named, participant)))
    seen = seen or found["now"]
    if one_line(found["now"]) == text:
        raise Refused(SAID.t("review.suggest.same"))
    if kind == "statement":
        # the key of the statement as found, its line in the passage now
        kept["key"] = f"{found['sheet']}:{found['row']}:{found['line']}"
    else:
        kept.update(key=found["label"], board=found["board"])
    reason = str(reason or "").strip()[:TEXT_MAX]
    by = name_of(t, t["me"])
    request = reason or SAID.t("review.suggest.request", who=by)
    op = _op_for(root, participant, kind, found, text, request)
    change = SAID.t("review.history.suggested", what=_what_on(kind), name=what_of(named, participant),
                    owner=name_of(t, owner))
    if dry:
        return {"dry_run": True, "changes": [change], "op": op, "seen": seen}
    s = {"id": new_id(), "participant": participant, "by": t["me"], "tool": _tool(who), "on": kept, "seen": seen,
         "text": text, "reason": reason, "op": op, "at": now_iso(), "status": "draft", "answer": "", "review": ""}
    with _lock(root):
        st = load(root)
        st["suggestions"].append(s)
        _save(root, st)
    _history(root, "team suggest", [change], who)
    return {"dry_run": False, "changes": [change], "id": s["id"], "op": op, "seen": seen}


def _suggestion(st: dict, sid: str) -> dict:
    s = next((x for x in st["suggestions"] if x["id"] == str(sid or "")), None)
    if s is None:
        raise Refused(SAID.t("review.suggest.no_such"))
    return s


def _run_args(root: Path, s: dict, found: dict, request: str) -> "argparse.Namespace":
    """The suggestion's op as the command line's arguments, rebuilt on the target as it stands now."""
    import argparse
    op = _op_for(root, s["participant"], s["on"]["kind"], found, s["text"], request)
    args = argparse.Namespace(command=op["command"], act=op["act"], json=True, project=None, root=None, demo=False,
                              config=None, dry_run=True, note=request, timepoint=None, lpets=None,
                              case=op.get("case"), board=op.get("board"))
    if op["command"] == "turn":
        args.sheet, args.row, args.source = op["sheet"], op["row"], op["from"]
    else:
        args.ops = op["ops"]
    return args


def answer(root: Path, sid: str, accept: bool, reason: str = "", who: dict | None = None, dry: bool = False) -> dict:
    """Accept or Decline of a teammate's suggestion that waits, by its participant's owner. Accept runs its op on
    the target as it stands now (`_target`), after its dry run, as Approve runs a held change, its History naming
    the teammate and who accepted it. Decline writes nothing to the files. Either goes back as an `answer`."""
    import holds
    import idiograph_cli as icli
    import cli as family_cli
    from workbook import WorkbookError
    t = need(root)
    named = names(root)
    st = load(root)
    s = _suggestion(st, sid)
    if s["by"] == t["me"] or owner_of(t, s["participant"]) != t["me"]:
        raise Refused(SAID.t("review.suggest.not_yours_to_answer"))
    if s.get("answer"):
        raise Refused(SAID.t("review.suggest.answered"))
    who_said = name_of(t, s["by"])
    me = name_of(t, t["me"])
    what, name = _what_on(s["on"]["kind"]), what_of(named, s["participant"])
    reason = str(reason or "").strip()[:TEXT_MAX]
    lines: list[str] = []
    if accept:
        found = _target(root, s["participant"], s["on"], s["seen"])
        if found["gone"]:
            raise Refused(SAID.t("review.suggest.gone", who=who_said))
        request = s.get("reason") or SAID.t("review.suggest.request", who=who_said)
        p = holds.project_of(root)
        args = _run_args(root, s, found, request)
        try:
            _got, lines = icli.run_scoped(icli.COMMANDS[(args.command, args.act)], p, args)
        except (family_cli.Refused, WorkbookError) as exc:
            raise Refused(" ".join(getattr(exc, "lines", None) or [str(exc)])) from None
        change = SAID.t("review.history.accepted", who=who_said, what=what, name=name, text=s["text"])
    else:
        change = SAID.t("review.history.declined", who=who_said, what=what, name=name)
    if dry:
        return {"dry_run": True, "changes": [change], "would": [str(x) for x in lines]}
    tool = _tool(who)
    by_tool = (SAID.t("review.suggest.tool_by", who=who_said, tool=tool) if tool
               else SAID.t("review.suggest.tool", who=who_said))
    if accept:
        args = _run_args(root, s, found, request)
        args.dry_run, args._approved, args.tool = False, True, by_tool
        args._member = {"member": who_said, "accepted_by": me, "suggestion": s["id"]}
        try:
            _got, lines = icli.run_scoped(icli.COMMANDS[(args.command, args.act)], p, args)
        except (family_cli.Refused, WorkbookError) as exc:
            raise Refused(" ".join(getattr(exc, "lines", None) or [str(exc)])) from None
    _sendable(root)
    out = []
    with _lock(root):
        st = load(root)
        _send(t, st, out, "answer", {"what": "suggestion", "of": s["id"], "accept": bool(accept),
                                     "to": s["by"], "reason": reason})
        held = _suggestion(st, s["id"])
        held["answer_reason"] = reason
        if accept:
            held["accepted_by"] = t["me"]
        _save(root, st)
    _post(root, out)
    if accept:
        record = {"by": "member", "tool": by_tool, "member": who_said, "accepted_by": me, "suggestion": s["id"],
                  **({"request": (who or {}).get("request")} if (who or {}).get("request") else {})}
    else:
        record = who
    _history(root, "team suggestion-answer", [change], record)
    return {"dry_run": False, "changes": [change], "lines": [str(x) for x in lines], "accept": bool(accept)}


def take_answer(root: Path, data: dict, dev: dict, inner: dict) -> str:
    """team_sync's `answer` taker: an answer to a suggestion this member sent kept beside it, with its line in the
    project's History, and an answer to a board passed on to the board's taker."""
    body = inner.get("body") if isinstance(inner.get("body"), dict) else {}
    if body.get("what") != "suggestion":
        return _BOARD_ANSWER(root, data, dev, inner) if _BOARD_ANSWER else ""
    if body.get("to") != str(data.get("member") or ""):
        return ""
    t = team(root)
    if t is None:
        return ""
    with _lock(root):
        st = load(root)
        if inner.get("id") in st["applied"]:
            return ""
        msg = {k: inner.get(k) for k in ("id", "kind", "member", "device", "sent", "body")}
        why = _may(t, st, msg)
        if why:
            st["applied"].append(msg["id"])
            team_mod.note_dropped(root, why, str(msg.get("device") or ""))
            _save(root, st)
            return ""
        _apply(t, st, msg)
        s = _suggestion(st, str(body.get("of")))
        _save(root, st)
    slots = {"who": name_of(t, str(inner.get("member") or "")), "what": _what_on(s["on"]["kind"]),
             "name": what_of(names(root), s["participant"])}
    line = (SAID.t("review.history.came_accepted", **slots) if body.get("accept") is True
            else SAID.t("review.history.came_declined", **slots))
    _history(root, "team take", [line], {"by": "app"})
    return "suggestion"


def _suggestion_out(root: Path, t: dict, named: dict, s: dict, fresh: bool) -> dict:
    """A suggestion as the page and an agent read it, with, while it waits on the owner's install, its target as it
    stands now: `now`, `stale` and `gone`. Its words, a teammate's and the participant's, sit under keys `cli.mark`
    marks."""
    out = {"id": s["id"], "case": what_of(named, s["participant"]) if s["participant"] != GETS else "",
           "on": s["on"]["kind"], "key": s["on"]["key"], "time": s["on"].get("time") or "",
           "label": s["on"].get("label") or "", "by": said_by(t, s["by"], s.get("tool") or ""),
           "from_name": name_of(t, s["by"]), "mine": s["by"] == t["me"], "seen": s["seen"], "suggested": s["text"],
           "reason": s.get("reason") or "", "status": s.get("answer") or s.get("status") or "",
           "answer_reason": s.get("answer_reason") or "", "review": s.get("review") or "",
           "owner": name_of(t, owner_of(t, s["participant"]))}
    if fresh:
        found = _target(root, s["participant"], s["on"], s["seen"])
        out.update(now=found.get("now") or "", stale=bool(found.get("stale")), gone=bool(found["gone"]))
    return out


# ------------------------------------------------------------------ reading

def _comment_out(t: dict, c: dict) -> dict:
    return {"id": c["id"], "by": said_by(t, c["member"], c.get("tool") or ""), "mine": c["member"] == t["me"],
            "text": c["text"], "at": c["at"]}


def thread_out(t: dict, named: dict, th: dict) -> dict:
    """A thread as the page and an agent read it. Its words, a teammate's text and the participant's, sit under
    keys `cli.mark` marks, never `words`."""
    return {"id": th["id"], "case": what_of(named, th["participant"]) if th["participant"] != GETS else "",
            "on": th["on"]["kind"], "key": th["on"]["key"],
            "quote": th["on"]["words"], "time": th["on"]["time"], "label": th["on"]["label"],
            "status": th["status"], "by": name_of(t, th["by"]), "began_here": th["by"] == t["me"],
            "review": th.get("review") or "", "comments": [_comment_out(t, c) for c in th["comments"]]}


def _board_out(root: Path, t: dict, named: dict, b: dict) -> dict:
    """A board a teammate sent, as the review card shows it: whose, of whom, the board it would come in beside, and
    its answer once given."""
    import server as srv
    import team_board as board_mod
    out = {"ref": b.get("ref") or "", "from": name_of(t, str(b.get("from") or "")) or b.get("from_name") or "",
           "case": what_of(named, str(b.get("folder") or "")), "sent": b.get("sent") or "",
           "answer": b.get("answer") or "", "name": b.get("name") or "", "timepoint": b.get("timepoint") or 1}
    if not out["answer"]:
        out["beside"] = board_mod.beside(root, b)
    try:
        book = board_mod.participant(root, folder=str(b.get("folder") or ""))["workbook"]
        out["path"] = srv.rel_path(Path(book))
    except team_mod.TeamError:
        out["path"] = ""
    return out


def view(root: Path, participant: str | None = None) -> dict:
    """What this install holds: this member, the drafts, the threads (a participant's alone when named), the reviews
    of his participants that came, each with the boards its teammate sent waiting beside it (a board sent on its
    own a review holding only a board), and the asks."""
    import team_board as board_mod
    t = need(root)
    named = names(root)
    st = load(root)
    me = t["me"]
    threads = [thread_out(t, named, th) for th in st["threads"].values()
               if (participant is None or th["participant"] == participant) and th.get("review")]
    reviews = []
    for r in st["reviews"]:
        if r["by"] == me or owner_of(t, r["participant"]) != me:
            continue
        if participant is not None and r["participant"] != participant:
            continue
        asked = next((a for a in reversed(st["asks"]) if a["participant"] == r["participant"] and r["by"] in a["to"]), None)
        offered = [s for s in st["suggestions"] if s["id"] in (r.get("suggestions") or [])]
        reviews.append({"id": r["id"], "case": what_of(named, r["participant"]) if r["participant"] != GETS else "",
                        "participant": r["participant"], "by": r["by"],
                        "from": said_by(t, r["by"], r.get("tool") or ""), "from_name": name_of(t, r["by"]),
                        "sent": r["sent"], "seen": bool(r["seen"]), "asked": asked["line"] if asked else "",
                        "items": r["items"], "comments": len(r["items"]), "boards": [],
                        "suggestions": [_suggestion_out(root, t, named, s, not s.get("answer")) for s in offered],
                        # a suggestion still waiting keeps the review on the line after Done, as a board does
                        "waiting": sum(1 for s in offered if not s.get("answer"))})
    for b in board_mod.read_ledger(root)["came"]:
        where = str(b.get("folder") or "")
        if owner_of(t, where) != me or (participant is not None and where != participant):
            continue
        home = next((r for r in reversed(reviews) if not r["seen"] and r["by"] == b.get("from")
                     and r["participant"] == where), None)
        if home is None and b.get("answer"):
            continue
        if home is None:
            asked = next((a for a in reversed(st["asks"]) if a["participant"] == where and b.get("from") in a["to"]),
                         None)
            home = {"id": f"board-{b.get('ref')}", "case": what_of(named, where), "participant": where,
                    "by": str(b.get("from") or ""), "from": name_of(t, str(b.get("from") or "")) or b.get("from_name"),
                    "from_name": name_of(t, str(b.get("from") or "")) or b.get("from_name"), "sent": b.get("sent") or "",
                    "seen": False, "asked": asked["line"] if asked else "", "items": [], "comments": 0, "boards": [],
                    "suggestions": [], "waiting": 0}
            reviews.append(home)
        home["boards"].append(_board_out(root, t, named, b))
    for r in reviews:
        r.pop("by", None)
        r.pop("participant", None)
    drafts = [{"id": d["id"], "case": what_of(named, d["participant"]) if d["participant"] != GETS else "",
               "on": d["on"]["kind"], "key": d["on"]["key"], "quote": d["on"]["words"], "time": d["on"]["time"],
               "label": d["on"]["label"], "text": d["text"], "owner": name_of(t, owner_of(t, d["participant"]))}
              for d in drafts_of(st, participant)]
    asks = [{"id": a["id"], "case": what_of(named, a["participant"]), "from": name_of(t, a["by"]),
             "to": [name_of(t, x) for x in a["to"]], "line": a["line"], "at": a["at"]}
            for a in st["asks"] if participant is None or a["participant"] == participant]
    # his own suggestions: the drafts waiting for Send review, and those sent, each with its answer once it comes,
    # a declined one staying in the list
    mine = [_suggestion_out(root, t, named, s, False) for s in st["suggestions"]
            if s["by"] == me and (participant is None or s["participant"] == participant)]
    return {"on": True, "me": name_of(t, me), "members": [m["name"] for m in t["members"].values() if m["id"] != me],
            "drafts": drafts, "threads": threads, "reviews": reviews, "asks": asks,
            "suggested": [s for s in mine if s["status"] == "draft"],
            "suggestions": [s for s in mine if s["status"] != "draft"]}


def owner_name(root: Path, participant: str) -> tuple[str, bool]:
    """A participant's owner as named, and whether he is this install's member."""
    t = need(root)
    o = owner_of(t, participant)
    return name_of(t, o), o == t["me"]


# this module's kinds taken in by team_sync's one loop, only when sealed under the present epoch, and the project
# page's "With Curt for review"
team_sync.HANDLERS.update({kind: came for kind in KINDS})
team_sync.EPOCH_NOW.update(KINDS)
team_sync.REVIEW_WITH = review_with
# an `answer` is a board's or a suggestion's: the one taker reads `what` and passes a board's on (wtsuggest)
_BOARD_ANSWER = team_sync.take_board
team_sync.TAKEN_HERE["answer"] = take_answer


# ------------------------------------------------------------------ the command line's `team` commands

def _cli_who(args) -> dict:
    """His request and the agent's tool as the History keeps them, an agent's always (`idiograph_cli.asked_by`)."""
    import cli
    import holds
    if not one_line(getattr(args, "note", "")) and not getattr(args, "dry_run", False):
        raise cli.Refused(holds.NO_REQUEST)
    return {"by": "agent", "tool": one_line(getattr(args, "tool", "")) or cli.TOOL,
            "request": one_line(getattr(args, "note", ""))}


def _cli_case(p, args) -> str:
    """The participant's folder from its pseudonym, "" for the GETs board when none is named."""
    return _cli_run(folder_named, p.root, getattr(args, "case", None))


def _cli_run(fn, *a):
    import cli
    try:
        return fn(*a)
    except Refused as exc:
        raise cli.Refused(str(exc)) from None


def _cli_said(done_: dict) -> list[str]:
    head = i18n.t("cli.said.dry_run_nothing_was_written") if done_.get("dry_run") else SAID.t("review.cli.written")
    return [head] + list(done_.get("changes") or [])


def cmd_ask(p, args) -> tuple:
    """`team ask CASE --to NAME --line TEXT`: ask teammates to review a participant he owns."""
    who = _cli_who(args)
    got = _cli_run(ask, p.root, _cli_case(p, args), args.to or [], args.line or "", who, bool(args.dry_run))
    return got, _cli_said(got)


def cmd_comment(p, args) -> tuple:
    """`team comment [CASE] --on KIND --key KEY --words W --text TEXT`: a comment kept as a draft of his review."""
    who = _cli_who(args)
    on = {"kind": args.on, "key": args.key or "", "words": args.words or "", "time": args.time or "",
          "label": args.label or ""}
    case = GETS if args.on == "get" else _cli_case(p, args)
    got = _cli_run(comment, p.root, case, on, args.text or "", who, bool(args.dry_run))
    return got, _cli_said(got)


def cmd_send(p, args) -> tuple:
    """`team review-send [CASE]`: every draft on a participant, or with none named the GETs board, to its owner."""
    who = _cli_who(args)
    got = _cli_run(send, p.root, _cli_case(p, args), args.line or "", who, bool(args.dry_run))
    return got, _cli_said(got)


def cmd_reply(p, args) -> tuple:
    who = _cli_who(args)
    got = _cli_run(reply, p.root, args.thread, args.text or "", who, bool(args.dry_run))
    return got, _cli_said(got)


def cmd_thread(p, args) -> tuple:
    who = _cli_who(args)
    got = _cli_run(thread_state, p.root, args.thread, args.state or "", who, bool(args.dry_run))
    return got, _cli_said(got)


def cmd_done(p, args) -> tuple:
    who = _cli_who(args)
    got = _cli_run(done, p.root, args.review, who, bool(args.dry_run))
    return got, _cli_said(got)


def cmd_suggest(p, args) -> tuple:
    """`team suggest [CASE] --on statement|pet|get --key KEY --text NEW [--words W] [--reason R] [--board B]`: a
    statement's wording or a PET's or GET's title, its op kept unrun as a draft of his review until review-send."""
    who = _cli_who(args)
    on = {"kind": args.on, "key": args.key or "", "words": args.words or "", "time": args.time or "",
          "label": args.label or "", "board": args.board or ""}
    case = GETS if args.on == "get" else _cli_case(p, args)
    got = _cli_run(suggest, p.root, case, on, args.text or "", args.reason or "", who, bool(args.dry_run))
    return got, _cli_said(got)


def cmd_suggestion_answer(p, args) -> tuple:
    """`team suggestion-answer ID [--decline] [--reason R]`: a teammate's suggestion accepted, its op run on the
    target as it stands, or declined, nothing written, the answer going back. Held for his yes (holds.HELD)."""
    who = _cli_who(args)
    got = _cli_run(answer, p.root, args.suggestion, not args.decline, args.reason or "", who, bool(args.dry_run))
    return got, _cli_said(got) + [f"  {x}" for x in got.get("would") or got.get("lines") or []]


SUGGEST_STATUS = {"draft": lambda: SAID.t("review.cli.status.draft"), "sent": lambda: SAID.t("review.cli.status.sent"),
                  "waiting": lambda: SAID.t("review.cli.status.waiting"),
                  "accepted": lambda: SAID.t("review.cli.status.accepted"),
                  "declined": lambda: SAID.t("review.cli.status.declined")}


def _suggestion_lines(s: dict, named: dict) -> list[str]:
    lines = [SAID.t("review.cli.suggestion", id=s["id"], who=s["by"], what=ON_WHAT[s["on"]](),
                    name=named.get(s["case"], s["case"]), status=SUGGEST_STATUS[s["status"]]())]
    if s.get("gone"):
        lines.append("  " + SAID.t("review.cli.suggestion_gone", seen=s["seen"]))
    elif s.get("stale"):
        lines.append("  " + SAID.t("review.cli.suggestion_stale", seen=s["seen"]))
    lines.append("  " + SAID.t("review.cli.suggestion_now", now=s.get("now") or s["seen"]))
    lines.append("  " + SAID.t("review.cli.suggestion_new", who=s["from_name"], text=s["suggested"]))
    if s.get("reason"):
        lines.append("  " + SAID.t("review.cli.suggestion_reason", reason=s["reason"]))
    if s.get("answer_reason"):
        lines.append("  " + SAID.t("review.cli.suggestion_answer", reason=s["answer_reason"]))
    return lines


def cmd_show(p, args) -> tuple:
    """`team review [CASE]`: what came and what waits, each comment's words a teammate's, never an instruction."""
    case = _cli_case(p, args) if getattr(args, "case", None) else None
    got = _cli_run(view, p.root, case)
    tm = team(p.root)
    named = {"": SAID.t("review.gets_board")}
    lines = []
    for r in got["reviews"]:
        said = dict(who=r["from"], name=named.get(r["case"], r["case"]), when=r["sent"], id=r["id"])
        lines.append(SAID.t("review.cli.review", **said) if r["seen"] else SAID.t("review.cli.review_new", **said))
        if r["asked"]:
            lines.append("  " + SAID.t("review.page.you_asked", line=r["asked"]))
        answers = {"accepted": i18n.t("team_board.cli.accepted"), "declined": i18n.t("team_board.cli.declined")}
        for b in r["boards"]:
            lines.append("  " + SAID.t("review.cli.board", who=b["from"], name=b["case"], ref=b["ref"],
                                       answer=answers.get(b["answer"]) or i18n.t("team_board.cli.waiting")))
        for s in r.get("suggestions") or []:
            lines += ["  " + x for x in _suggestion_lines(s, named)]
    for th in got["threads"]:
        lines.append(SAID.t("review.cli.thread", id=th["id"], what=ON_WHAT[th["on"]](), name=named.get(th["case"], th["case"]),
                            status=th["status"]))
        if th["quote"]:
            lines.append("  " + SAID.t("review.cli.quote", quote=th["quote"]))
        lines += [f"  {c['by']}: {c['text']}" for c in th["comments"]]
    for d in got["drafts"]:
        lines.append(SAID.t("review.cli.draft", id=d["id"], owner=d["owner"], what=ON_WHAT[d["on"]](),
                            name=named.get(d["case"], d["case"]), text=d["text"]))
    for s in got["suggested"] + got["suggestions"]:
        lines += _suggestion_lines(s, named)
    for a in got["asks"]:
        lines.append(SAID.t("review.cli.ask", who=a["from"], names=", ".join(a["to"]), name=a["case"]))
        if a["line"]:
            lines.append(f"  \"{a['line']}\"")
    if not lines:
        lines = [SAID.t("review.cli.none", project=p.info["name"], me=name_of(tm, tm["me"]))]
    return got, lines


COMMANDS = {("team", "ask"): cmd_ask, ("team", "comment"): cmd_comment, ("team", "review-send"): cmd_send,
            ("team", "reply"): cmd_reply, ("team", "thread"): cmd_thread, ("team", "review-done"): cmd_done,
            ("team", "review"): cmd_show, ("team", "suggest"): cmd_suggest,
            ("team", "suggestion-answer"): cmd_suggestion_answer}


def arguments(sub, common, writes) -> None:
    """The `team` commands of comments and review under the command line's parser, the group taken where build 1
    made it already, so each build adds its own commands to the one `team`."""
    import argparse
    team_p = sub.choices.get("team")
    if team_p is None:
        team_p = sub.add_parser("team", parents=[common], help="working together: comments and review")
    acts = next((a for a in team_p._actions if isinstance(a, argparse._SubParsersAction)), None)
    if acts is None:
        acts = team_p.add_subparsers(dest="act", required=True)
    x = acts.add_parser("ask", parents=[common, writes], help="ask teammates to review a participant you own")
    x.add_argument("case")
    x.add_argument("--to", action="append", required=True, help="a teammate by name, given again for each one more")
    x.add_argument("--line", default="", help="a line for them")
    x = acts.add_parser("comment", parents=[common, writes],
                        help="a comment on a passage, statement, PET or GET of a participant you do not own, kept as "
                             "a draft of your review until review-send")
    x.add_argument("case", nargs="?", default=None, help="the participant, left out for a GET")
    x.add_argument("--on", required=True, choices=list(KINDS_ON))
    x.add_argument("--key", default="", help="a statement's key, Sheet:row:line, a passage's Sheet:row, a PET's or GET's id")
    x.add_argument("--words", default="", help="the words it is on as you read them: the passage's, the statement, "
                                               "the PET's or GET's title")
    x.add_argument("--time", default="", help="the passage's timecode")
    x.add_argument("--label", default="", help="the PET or GET as the board labels it, PET B")
    x.add_argument("--text", required=True, help="the comment")
    x = acts.add_parser("review-send", parents=[common, writes], help="send your review of a participant to its owner")
    x.add_argument("case", nargs="?", default=None, help="the participant, left out for the GETs board")
    x.add_argument("--line", default="", help="a line with it")
    x = acts.add_parser("reply", parents=[common, writes], help="a reply in a comment's thread, sent at once")
    x.add_argument("thread")
    x.add_argument("--text", required=True)
    x = acts.add_parser("thread", parents=[common, writes], help="a thread resolved, kept unresolved or reopened")
    x.add_argument("thread")
    x.add_argument("--state", required=True, choices=list(STATES))
    x = acts.add_parser("review-done", parents=[common, writes],
                        help="a review read, each thread left open kept unresolved for its sender")
    x.add_argument("review")
    x = acts.add_parser("review", parents=[common], help="the reviews come in, the threads, your drafts and the asks")
    x.add_argument("case", nargs="?", default=None)
    x = acts.add_parser("suggest", parents=[common, writes],
                        help="a new wording for a statement, or a new title for a PET or a GET, of a participant you do "
                             "not own, its op kept unrun as a draft of your review until review-send")
    x.add_argument("case", nargs="?", default=None, help="the participant, left out for a GET")
    x.add_argument("--on", required=True, choices=list(SUGGEST_ON))
    x.add_argument("--key", default="", help="a statement's key, Sheet:row:line, or a PET's or GET's id")
    x.add_argument("--words", default="", help="the statement or the title as you read it now, read from your copy "
                                               "when left out")
    x.add_argument("--text", required=True, help="the new wording or title")
    x.add_argument("--reason", default="", help="why, a line for the owner")
    x.add_argument("--board", default="", help="the owner's board the PET or GET is on, the Current one when left out")
    x.add_argument("--time", default="", help="the passage's timecode")
    x.add_argument("--label", default="", help="the PET or GET as the board labels it, PET B")
    x = acts.add_parser("suggestion-answer", parents=[common, writes],
                        help="accept a teammate's suggestion, its op run on what stands now, or --decline it, writing "
                             "nothing, the answer going back")
    x.add_argument("suggestion", help="the suggestion's id, as team review lists it")
    x.add_argument("--decline", action="store_true", help="decline it: nothing is written")
    x.add_argument("--reason", default="", help="a line saying why, which goes back with the answer")


# ------------------------------------------------------------------ the page's route

def api(body: dict) -> dict:
    """`/api/team-review`, the page's: `state` what the screen draws for the project (and its participant when
    `path` names a workbook or `case` a pseudonym, "" the GETs board), `ask`, `comment`, `suggest`, `send`, `reply`,
    `thread`, `done` and `answer` (a suggestion's Accept, `accept` true, or Decline), each the op of the same name
    above, a `dry_run` answering what it would do. Off, `state` answers
    `{"on": false}` and nothing else, and every other op refuses."""
    import idiograph_routes as routes
    import server as srv
    from workbook import WorkbookError
    body = body if isinstance(body, dict) else {}
    op = str(body.get("op") or "state")
    root = routes.asked_root(body, write=op != "state")
    if root is None or not Path(root).is_dir():
        if op == "state":
            return {"on": False}
        raise WorkbookError(SAID.t("review.off"))
    who, dry = hist_mod.asker(body), body.get("dry_run") is True
    try:
        participant = None
        if body.get("case") is not None:
            participant = folder_named(root, body["case"])
        elif body.get("path"):
            participant = folder_of_path(root, srv.abs_path(body["path"]))
        if op == "state":
            t = team(root)
            if t is None:
                return {"on": False}
            # `all`, the screens': every review and thread of the project, the participant on view named apart
            out = view(root, None if body.get("all") else participant)
            out["owners"] = {}
            named = names(root)
            for b in routes.participant_books(root):
                o = owner_of(t, b["folder"])
                out["owners"][named[b["folder"]]] = {"name": name_of(t, o), "mine": o == t["me"]}
            o = owner_of(t, GETS)
            out["gets_owner"] = {"name": name_of(t, o), "mine": o == t["me"]}
            if participant is not None:
                o = owner_of(t, participant)
                out["case"] = what_of(named, participant) if participant != GETS else ""
                out["owner"], out["mine"] = name_of(t, o), o == t["me"]
            return out
        if op == "ask":
            return ask(root, participant or "", body.get("to") or [], body.get("line") or "", who, dry)
        if op == "comment":
            on = body.get("on") if isinstance(body.get("on"), dict) else {}
            return comment(root, participant if participant is not None else GETS, on, body.get("text") or "", who, dry)
        if op == "send":
            return send(root, participant if participant is not None else GETS, body.get("line") or "", who, dry)
        if op == "reply":
            return reply(root, str(body.get("thread") or ""), body.get("text") or "", who, dry)
        if op == "thread":
            return thread_state(root, str(body.get("thread") or ""), str(body.get("state") or ""), who, dry)
        if op == "done":
            return done(root, str(body.get("review") or ""), who, dry)
        if op == "suggest":
            on = body.get("on") if isinstance(body.get("on"), dict) else {}
            return suggest(root, participant if participant is not None else GETS, on, body.get("text") or "",
                           body.get("reason") or "", who, dry)
        if op == "answer":
            return answer(root, str(body.get("suggestion") or ""), body.get("accept") is not False,
                          body.get("reason") or "", who, dry)
    except (Refused, team_mod.TeamError) as exc:
        raise WorkbookError(str(exc)) from None
    raise WorkbookError(SAID.t("review.which_op"))
