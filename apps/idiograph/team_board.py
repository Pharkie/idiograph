"""A reviewer's board sent straight in (wtboard, 9 November 2026, Working together's sixth build, the spec's `board`
message, sections 4 and 7). Adam's words: "for Curt to send me a PETs board directly in the app and me receive it".

**His own boards** (ownboards, 9 November 2026). A member who does not own a participant makes, edits and keeps his
own boards of it as any board is, from the canvas, the board ops and an agent's `board` ops, with their dry runs and
History. They are kept apart in his copy, in the team folder (`own_file`, `themes.OWN_FILE`), never in the owner's
PETs file: the one writer refuses every other write to the participant, a version of it never carries them, and a
new version coming in never touches them. His board menu lists the owner's boards and then his own, each marked
Yours.

**Sending.** A member who does not own a participant sends one of his own boards of that participant's PETs with
Send board, in the board's menu, or `team board-send`. The board goes whole as the canvas keeps it (its PETs, titles,
descriptions, notes, stacks, the bin, Not placed and where each card sits), less its History, its review, its revise
thread and an agent's marks, with the print of each statement as his copy read it (`project_pack.statement_print`)
and its places print (`themes.places_print`). It is sealed on this computer (team.py `seal_envelope`) as a `board`
message to the participant's owner and goes through the project's transport. The send is kept in the team folder's
`boards.json` with a reference of its own, `ref`, which the answer names.

**Coming in, held until he answers** (wtreview2, 9 November 2026, the spec's sections 4, 7 and 9). The owner's
install takes it in (team_sync's one loop, the PETs screen's `take`, or `team board-take`): each message after the
last one read is opened, and a board meant for this member is kept whole in the team folder's `boards.json`,
waiting, with nothing written to the participant. It shows on the owner's line and review card with the rest of
that teammate's review (review.py), "Curt's board of Juno's PETs", Decline and Add as next board. A board waiting
is kept across a restart. A board already taken in is never taken twice.

**The answer.** Add as next board (`answer` with accept) turns the board by `idiograph_routes.board_coming` as a
shared copy's is, every card in its place and matched by its words then its key against the statements as they are
now, and adds it as the participant's next board, never current, or with no board before it as their only board,
on the canvas as a first board always is and with no empty Board 1 beside it, named "Curt's board, 9 Nov", its note "Curt's
board, sent 9 Nov: 63 statements as sent, 2 reworded since." (the wording 2 note), its `origin` naming the message
(`team`), and one revision in its History, "Sent by Curt". Nothing else is written: no statement, note, setting or
other board. Decline writes nothing to the participant's files: the record keeps it, without the board, with its
reason, and the team log notes it. Either goes back to the sender as the spec's `answer`, `{what: "board", of: ref,
accept, reason}`, through team_sync's `post`. The sender's install takes it in the same way and keeps it beside the
send. Each step is a line in the project's History.

Every message goes through team.py's envelope and a transport of transport.py's shape. Reading is `view`, writing
is under the project's lock through `idiograph_routes.api_team_board`.
"""
from __future__ import annotations

import json
import os
import secrets
from pathlib import Path

import i18n
import locks
import project_pack as pack_mod
import server as srv
import team as team_mod
import themes as themes_mod
import workbook as wb_mod

LEDGER = "boards.json"
KIND = "board"
# what a board leaves behind when it goes: its History, its review and revise thread, an agent's marks, its origin
LEFT = ("history", "review", "revise", themes_mod.ORIGIN, themes_mod.OWN) + themes_mod.AGENT_KEYS
REASON_MOST = 400
# the key in this device's held team where the last message read by `take` is kept
AFTER = "board_after"
# where a member's own boards of the participants someone else works on are kept, in the team folder
OWN_DIR = "own-boards"


def routes():
    import idiograph_routes
    return idiograph_routes


# ------------------------------------------------------------------ the team folder's record

def ledger_path(root: Path) -> Path:
    return Path(root) / team_mod.LOG_DIR / LEDGER


def read_ledger(root: Path) -> dict:
    # one there that will not read is refused as busy, never taken as empty and written over (teamflake)
    data = locks.read_json(ledger_path(root)) or {}
    data = data if isinstance(data, dict) else {}
    return {"sent": [x for x in data.get("sent") or [] if isinstance(x, dict)],
            "came": [x for x in data.get("came") or [] if isinstance(x, dict)]}


def write_ledger(root: Path, data: dict) -> None:
    target = ledger_path(root)
    target.parent.mkdir(exist_ok=True)
    tmp = locks.new_tmp(target)
    tmp.write_text(json.dumps(data, indent=1, ensure_ascii=False) + "\n", encoding="utf-8", newline="\n")
    os.replace(tmp, target)


# ------------------------------------------------------------------ who

def team_here(root: Path) -> tuple[dict, dict]:
    """team.json of a project where Working together is on, and this computer's keys, or a refusal."""
    data = team_mod.held_on(root)
    dev = team_mod.device()
    if not dev:
        raise team_mod.TeamError(i18n.t("team.refused.no_device"), "no_device")
    return data, dev


def name_of(roster: dict, member: str) -> str:
    return str((team_mod.member_of(roster, member) or {}).get("name") or "")


def owner_of(data: dict, folder: str) -> str:
    return team_mod.owner_here(data, folder)


def participant(root: Path, case: str = "", workbook=None, folder: str = "") -> dict:
    """A participant of the project by its folder, its workbook, or its label or pseudonym, as `participant_books`
    reads it, or a refusal."""
    import gets as gets_mod
    every = routes().participant_books(root)
    hit = None
    if folder:
        hit = next((p for p in every if p["folder"] == folder), None)
    if hit is None and workbook:
        book = Path(workbook).resolve()
        hit = next((p for p in every if Path(p["workbook"]).resolve() == book), None)
    if hit is None and case:
        said = " ".join(str(case).split()).lower()
        hit = next((p for p in every if p["label"].lower() == said), None) or next(
            (p for p in every if gets_mod.who(p["label"]).lower() == gets_mod.who(said).lower()), None)
    if hit is None:
        raise team_mod.TeamError(i18n.t("team.refused.no_participant", who=team_mod.one_line(case or folder)),
                                 "no_participant")
    return hit


def timepoint_of(root: Path, n) -> int:
    tps = routes().timepoints_of(routes().project_file(root))
    try:
        n = int(n or 1)
    except (TypeError, ValueError):
        n = 1
    return n if 1 <= n <= max(1, len(tps)) else 1


# ------------------------------------------------------------------ his own boards

def own_file(workbook: Path) -> Path | None:
    """`themes.OWN_FILE`: for a participant someone else works on, in a project worked on together, the file this
    member's own boards of it are kept in at the timepoint in scope, `.idiograph-team/own-boards/<participant's
    folder>/<the PETs file's name>`. The team folder is his copy's alone: a version of a participant is its
    workbook, PETs files and progress file, so his boards never go as one, and a version coming in never writes
    here. None for a participant of his own, and for every participant while Working together is off."""
    import team_sync
    case = wb_mod.case_folder(Path(workbook))
    root = team_sync.project_root_of(case)
    if root is None:
        return None
    data = team_sync.team_on(root)
    if data is None:
        return None
    try:
        folder = case.resolve().relative_to(Path(root).resolve()).as_posix()
    except ValueError:
        return None
    if folder == "." or owner_of(data, folder) == str(data.get("member") or ""):
        return None
    return Path(root) / team_mod.LOG_DIR / OWN_DIR / folder / themes_mod.themes_path(Path(workbook)).name


def install() -> None:
    themes_mod.OWN_FILE = own_file


def own_boards(data: dict | None) -> list[dict]:
    """His own boards of a participant, as `themes.load` marks them."""
    return [{"id": str(b.get("id") or ""), "name": str(b.get("name") or "")}
            for b in themes_mod.boards_of(data) if b.get(themes_mod.OWN)]


# ------------------------------------------------------------------ sending

def board_named(data: dict, board) -> dict | None:
    """A board of a themes file by its id or its name, or the one on the canvas for none."""
    if not board:
        return themes_mod.current_version(data)
    said = " ".join(str(board).split()).lower()
    return themes_mod.find_version(data, board) or next(
        (b for b in themes_mod.boards_of(data) if " ".join(str(b.get("name") or "").split()).lower() == said), None)


def going(board: dict) -> dict:
    """The board as it goes: whole, less what is this computer's alone."""
    out = json.loads(json.dumps(themes_mod.normalise(board)))
    for key in LEFT:
        out.pop(key, None)
    return out


def send(root: Path, case: str = "", workbook=None, board=None, timepoint=None, dry_run: bool = False) -> dict:
    """His own board of a participant someone else owns, sent to its owner, sealed. Refused when nobody else works on
    the project, when the participant is his own, or when the board is not there."""
    data, dev = team_here(root)
    roster = data.get("roster") or {}
    me = str(data.get("member") or "")
    if len(team_mod.roster_members(roster)) <= 1:
        raise team_mod.TeamError(i18n.t("team_board.refused.alone"), "alone")
    p = participant(root, case, workbook)
    owner = owner_of(data, p["folder"])
    if owner == me:
        raise team_mod.TeamError(i18n.t("team_board.refused.yours", participant=p["label"]), "yours")
    n = timepoint_of(root, timepoint)
    book = Path(p["workbook"])
    with themes_mod.scoped(n):
        held = themes_mod.load(book) or {}
        chosen = board_named(held, board)
        cards = themes_mod.read_cards(book)["cards"] if chosen else []
    if chosen is None:
        raise team_mod.TeamError(i18n.t("team_board.refused.no_board", participant=p["label"]), "no_board")
    name = " ".join(str(chosen.get("name") or "").split()) or themes_mod.FIRST_NAME
    to_name = name_of(roster, owner)
    # only a board of his own goes, the owner's being the owner's already (ownboards, 9 November 2026)
    if not chosen.get(themes_mod.OWN):
        raise team_mod.TeamError(i18n.t("team_board.refused.not_own", board=name, name=to_name), "not_own")
    changes = [i18n.t("team_board.history.sent", board=name, participant=p["label"], name=to_name)]
    out = {"changes": changes, "dry_run": dry_run, "participant": p["label"], "board": name, "to": to_name}
    if dry_run:
        return out
    v = going(chosen)
    ref = secrets.token_bytes(8).hex()
    body = {"ref": ref, "to": owner, "participant": p["folder"], "label": p["label"], "timepoint": n, "name": name,
            "board": v, "places": themes_mod.places_print(v),
            "statements": {c["key"]: pack_mod.statement_print(themes_mod.words(c["text"])) for c in cards}}
    team = str(data.get("team") or "")
    epoch = int(roster.get("epoch") or 1)
    key = team_mod.project_key(team, epoch)
    if key is None:
        raise team_mod.TeamError(i18n.t("team.refused.no_key"), "no_key")
    sealed = team_mod.seal_envelope(team, epoch, key, dev, me, team_mod.next_seq(team), KIND, body)
    team_mod.transport_for(data, dev).send(team, sealed)
    kept = read_ledger(root)
    kept["sent"].append({"ref": ref, "participant": p["label"], "folder": p["folder"], "timepoint": n,
                         "board": str(chosen.get("id") or ""), "name": name, "to": owner, "to_name": to_name,
                         "at": team_mod.now_iso(), "answer": ""})
    write_ledger(root, kept)
    return dict(out, ref=ref)


# ------------------------------------------------------------------ taking in

def note_of(who: str, day: str, counts: dict, own_note: str) -> str:
    """The board's note (Adam's wording 2 of 8 November 2026, as a shared copy's board has it): whose board and when
    it was sent, how its statements came, then the sender's own note as it was."""
    head = routes().board_in_note(who, day, counts, team=True)
    return head + (f"\n{own_note}" if own_note else "")


def came_in(root: Path, inner: dict, roster: dict, kept: dict, dry_run: bool = False) -> dict | None:
    """One `board` message meant for this member kept waiting in the record, whole, nothing written to the
    participant. None when it was taken in before. The caller holds the project's lock."""
    body = inner.get("body") if isinstance(inner.get("body"), dict) else {}
    ref = str(body.get("ref") or inner.get("id") or "")
    if not ref or any(x.get("ref") == ref for x in kept["came"]):
        return None
    if not isinstance(body.get("board"), dict):
        raise team_mod.TeamError(i18n.t("team.refused.tampered"), "tampered")
    p = participant(root, str(body.get("label") or ""), folder=str(body.get("participant") or ""))
    sender = name_of(roster, str(inner.get("member") or "")) or team_mod.one_line(inner.get("member"))
    who = routes().whose(sender) or i18n.t("team_board.someone")
    statements = body.get("statements") if isinstance(body.get("statements"), dict) else {}
    entry = {"ref": ref, "from": str(inner.get("member") or ""), "from_name": sender, "participant": p["label"],
             "folder": p["folder"], "timepoint": timepoint_of(root, body.get("timepoint")), "board": "", "name": "",
             "sent_name": " ".join(str(body.get("name") or "").split()) or themes_mod.FIRST_NAME,
             "sent": str(inner.get("sent") or ""), "at": themes_mod.now_iso(), "answer": "",
             "held": {"board": body["board"], "statements": {str(k): v for k, v in statements.items()}}}
    if not dry_run:
        kept["came"].append(entry)
    out = {k: v for k, v in entry.items() if k != "held"}
    return dict(out, change=i18n.t("team_board.history.came", whose=who, participant=p["label"]))


def add_board(root: Path, entry: dict) -> dict:
    """A board waiting turned into the participant's next board, never current, or their only board when they have
    none, with its note and its History. The
    caller holds the project's lock. Answers the board as written."""
    held = entry.get("held") if isinstance(entry.get("held"), dict) else {}
    if not isinstance(held.get("board"), dict):
        raise team_mod.TeamError(i18n.t("team_board.refused.no_such"), "no_such")
    p = participant(root, entry.get("participant") or "", folder=entry.get("folder") or "")
    n = timepoint_of(root, entry.get("timepoint"))
    sender = entry.get("from_name") or ""
    who = routes().whose(sender) or i18n.t("team_board.someone")
    day = routes().day_said(entry.get("sent") or "")
    book = Path(p["workbook"])
    statements = held.get("statements") if isinstance(held.get("statements"), dict) else {}
    when = themes_mod.now_iso()
    with wb_mod.case_held(book), themes_mod.scoped(n):
        read = themes_mod.read_cards(book)
        data = themes_mod.load(book) or {}
        v, said = routes().board_coming(held["board"], read["cards"], read["quotes"], statements, who)
        v["note"] = note_of(who, day, routes().came_counts(said), str(held["board"].get("note") or "").strip())
        v[themes_mod.ORIGIN] = {"team": entry["ref"], "who": sender, "board": entry.get("sent_name") or "",
                                "sent": entry.get("sent") or "", "at": when}
        versions = themes_mod.boards_of(data)
        ids = [str(x.get("id")) for x in versions]
        v.update(id=themes_mod._next_id(versions),
                 name=themes_mod._free_name(versions, i18n.t("team_board.name", whose=who, day=day)),
                 created=when, updated=when)
        # the board on the canvas stays, and with no board before it the board sent is the participant's only
        # board and on the canvas, as a first board always is, with no empty Board 1 made beside it (smokefix)
        current = str(data.get("current")) if str(data.get("current")) in ids else (ids[0] if ids else v["id"])
        v.pop("history", None)
        themes_mod.add_revision(v, name=themes_mod.revision_name("team_board", who=sender), at=when)
        versions.append(v)
        themes_mod.write(book, themes_mod._file(book, routes().case_label(book), data, versions, current, when))
    return {"board": v["id"], "name": v["name"], "statements": said["statements"], "came": routes().came_counts(said),
            "path": srv.rel_path(book)}


def beside(root: Path, entry: dict) -> str:
    """The board on the canvas of a waiting board's participant, which it would come in beside, "" when none."""
    try:
        p = participant(root, entry.get("participant") or "", folder=entry.get("folder") or "")
        with themes_mod.scoped(timepoint_of(root, entry.get("timepoint"))):
            now = themes_mod.current_version(themes_mod.load(Path(p["workbook"])) or {})
    except (team_mod.TeamError, wb_mod.WorkbookError, OSError):
        return ""
    return " ".join(str((now or {}).get("name") or "").split()) if now else ""


def answered(root: Path, inner: dict, roster: dict, kept: dict, dry_run: bool = False) -> dict | None:
    """An `answer` to a board this member sent, kept beside the send. None for any other answer."""
    body = inner.get("body") if isinstance(inner.get("body"), dict) else {}
    if body.get("what") != KIND:
        return None
    sent = next((x for x in kept["sent"] if x.get("ref") == body.get("of")), None)
    if sent is None or sent.get("answer"):
        return None
    accept = body.get("accept") is True
    who = name_of(roster, str(inner.get("member") or "")) or sent.get("to_name") or ""
    reason = team_mod.one_line(body.get("reason"))[:REASON_MOST]
    if not dry_run:
        sent.update(answer="accepted" if accept else "declined", reason=reason, answered=str(inner.get("sent") or ""))
    key = "team_board.history.accepted" if accept else "team_board.history.declined"
    return {"ref": sent["ref"], "accept": accept, "name": who, "board": sent.get("name") or "",
            "participant": sent.get("participant") or "", "reason": reason,
            "change": i18n.t(key, name=who, board=sent.get("name") or "", participant=sent.get("participant") or "")}


def take(root: Path, dry_run: bool = False) -> dict:
    """What has come for this member since the last read: each board meant for it added as a next board, and each
    answer to a board it sent kept. A message that does not open is dropped and noted in the team folder's log. With
    `dry_run` what would come, nothing written and nothing marked read. The caller holds the project's lock."""
    data, dev = team_here(root)
    roster = data.get("roster") or {}
    me = str(data.get("member") or "")
    team = str(data.get("team") or "")
    keys = team_mod.project_keys(team)
    held = team_mod.held_team(team)
    after = int(held.get(AFTER) or 0)
    if len(team_mod.roster_members(roster)) <= 1:
        return {"changes": [], "came": [], "answers": [], "dry_run": dry_run}
    got = team_mod.transport_for(data, dev).fetch(team, after)
    kept = read_ledger(root)
    came, answers, last = [], [], after
    for seq, sender, raw in got:
        last = max(last, int(seq))
        if sender == dev["id"]:
            continue
        try:
            inner = team_mod.open_envelope(raw, roster, keys)
        except (team_mod.TeamError, ValueError) as exc:
            if not dry_run:
                team_mod.note_dropped(root, getattr(exc, "code", "") or "tampered", sender)
            continue
        body = inner.get("body") if isinstance(inner.get("body"), dict) else {}
        try:
            if inner.get("kind") == KIND and body.get("to") == me:
                one = came_in(root, inner, roster, kept, dry_run)
                if one:
                    came.append(one)
            elif inner.get("kind") == "answer" and body.get("to") == me:
                one = answered(root, inner, roster, kept, dry_run)
                if one:
                    answers.append(one)
        except (team_mod.TeamError, wb_mod.WorkbookError) as exc:
            if not dry_run:
                team_mod.note_dropped(root, getattr(exc, "code", "") or "board_not_taken", sender)
    if not dry_run:
        if came or answers:
            write_ledger(root, kept)
        if last != after:
            held = team_mod.held_team(team)
            held[AFTER] = last
            team_mod.keep_team(team, held)
    changes = [c.pop("change") for c in came] + [a.pop("change") for a in answers]
    return {"changes": changes, "came": came, "answers": answers, "dry_run": dry_run}


# ------------------------------------------------------------------ the answer

def answer(root: Path, ref: str = "", accept: bool = True, reason: str = "", workbook=None,
           dry_run: bool = False) -> dict:
    """Add as next board, or Decline, of a board that came in and waits, and either goes back to its sender. The
    board is named by its `ref`, or by its participant's `workbook`, the newest of it waiting. Decline writes
    nothing to the participant's files. A board answered before is refused. The caller holds the project's lock."""
    import team_sync
    data, _dev = team_here(root)
    roster = data.get("roster") or {}
    kept = read_ledger(root)
    entry = next((x for x in kept["came"] if ref and x.get("ref") == ref), None)
    if entry is None and workbook:
        p = participant(root, workbook=workbook)
        named = [x for x in kept["came"] if x.get("folder") == p["folder"] and not x.get("answer")]
        entry = named[-1] if named else None
    if entry is None:
        raise team_mod.TeamError(i18n.t("team_board.refused.no_such"), "no_such")
    if entry.get("answer"):
        raise team_mod.TeamError(i18n.t("team_board.refused.answered"), "answered")
    who = routes().whose(entry.get("from_name")) or i18n.t("team_board.someone")
    slots = {"whose": who, "participant": entry.get("participant") or ""}
    out = {"dry_run": dry_run, "accept": bool(accept), "participant": entry.get("participant"), "ref": entry["ref"]}
    if dry_run:
        said = i18n.t("team_board.history.kept_dry", **slots) if accept else i18n.t("team_board.history.declined_in",
                                                                                      **slots)
        return dict(out, changes=[said], added="")
    reason = team_mod.one_line(reason)[:REASON_MOST]
    if accept:
        made = add_board(root, entry)
        entry.update(board=made["board"], name=made["name"])
        changes = [i18n.t("team_board.history.kept", name=made["name"], **slots)]
    else:
        made = {}
        changes = [i18n.t("team_board.history.declined_in", **slots)]
        team_mod.note_dropped(root, "board_declined", "")
    entry.pop("held", None)
    entry.update(answer="accepted" if accept else "declined", answered=team_mod.now_iso(), reason=reason)
    write_ledger(root, kept)
    if team_mod.member_of(roster, str(entry.get("from") or "")):
        team_sync.post(root, "answer", {"what": KIND, "of": entry["ref"], "accept": bool(accept),
                                        "to": entry.get("from"), "reason": reason})
    return dict(out, changes=changes, added=made.get("board") or "", name=made.get("name") or "")


# ------------------------------------------------------------------ what the page and the agents read

def view(root: Path, workbook=None, timepoint=None) -> dict:
    """Boards sent and come in, for the page and `team boards`. Off, `{"on": false}` and nothing more. With a
    participant's `workbook`, `can_send`, whether his board of it can go, and to whom, and `waiting`, the boards of it
    come in and not yet answered, at `timepoint`."""
    data = team_mod.read_team(root)
    if not data or data.get("on") is not True:
        return {"on": False}
    roster = data.get("roster") or {}
    me = str(data.get("member") or "")
    kept = read_ledger(root)
    came = [{k: v for k, v in x.items() if k != "held"} for x in kept["came"]]
    out = {"on": True, "alone": len(team_mod.roster_members(roster)) <= 1, "sent": kept["sent"], "came": came}
    if workbook:
        try:
            p = participant(root, workbook=workbook)
        except team_mod.TeamError:
            return out
        n = timepoint_of(root, timepoint)
        owner = owner_of(data, p["folder"])
        out["can_send"] = not out["alone"] and owner != me
        out["owner"] = name_of(roster, owner)
        # his own boards of it, kept apart in his copy (see `own_file`), the ones Send board sends
        if owner != me:
            with themes_mod.scoped(n):
                try:
                    out["own"] = own_boards(themes_mod.load(Path(p["workbook"])))
                except wb_mod.WorkbookError:
                    out["own"] = []
        out["waiting"] = [x for x in out["came"] if x.get("folder") == p["folder"] and not x.get("answer")
                          and int(x.get("timepoint") or 1) == n]
        out["participant"] = p["label"]
    return out

