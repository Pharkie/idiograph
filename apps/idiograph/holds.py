"""An agent's action that waits for the researcher's yes in the app (holdsbuild, 27 October 2026, Adam's ruling of
Section 13: "build it as drawn", on the holds design of 26 October).

Adam, 26 October: "agent actions that delete boards or replace across a project wait for the yes in the app ...
an option in settings as to whether to have that approval or not ... dangerously skip permissions". So an op of
`HELD`, asked by an agent through the command line or the MCP server with the setting off, writes nothing: its
dry run is kept as a hold in the project's `idiograph-holds.json` at its root, and the answer says it waits, with
what it would do. The app shows the hold on every screen that shows an agent's line, and only the app approves or
declines it (`/api/holds`, the page's own): Approve runs the op as the agent asked, under its own lock, History
naming the agent "approved in the app", and Decline writes nothing but History's line. The agent asks after it
with `idiograph hold` and `idiograph hold show <id>` (MCP `hold`, `hold_show`). With "Dangerously skip
permissions" ticked, `skip_permissions` in the app's settings, the op runs at once and History says "without
asking".

Every op passes through `gate` in one place, `idiograph_cli.run_in_scope`, so no op holds itself. A hold whose dry
run no longer matches, or whose files changed since (`fingerprint`), says so on the card, and Approve runs the dry
run again first, running nothing when it differs.
"""
from __future__ import annotations

import argparse
import copy
import json
import re
from datetime import datetime
from pathlib import Path

import cli
import formats
import i18n
import locks
import server as srv
import themes
import themes_ai
from workbook import WorkbookError

FILE = "idiograph-holds.json"
LOCK = ".idiograph-holds.lock"
SETTING = "skip_permissions"
APPROVED = "approved in the app"
WITHOUT = "without asking"
# the suite's own: its checks of each op run them at once, as they ran before holds, and area 276 checks the holds
# themselves (see tests/test_idiograph.py). No agent's call has a way to it
RUN_AT_ONCE: bool | None = None

# the project's choices a run takes, never kept with a hold: the app runs an approved op on the hold's own project
PROJECT_KEYS = ("project", "root", "demo", "config", "json")
# an op's file read once as the hold is made, so Approve runs on what the agent sent, whatever the file says later
FILE_KEYS = ("ops", "source")
LABEL_GONE = ("merge", "apart")
NOT_HERE = "No action of that id waits in this project."
NO_REQUEST = "Say his request in his own words with --note, so the board and its History name it."


# ------------------------------------------------------------------ which ops wait

def is_agent_board(board: dict | None) -> bool:
    """A board an agent made in a conversation, whose mark says so (`idiograph_cli.mark`)."""
    return isinstance(board, dict) and isinstance(board.get("made"), dict) and board["made"].get("by") == "agent"


def takes_labels_off(args) -> bool:
    """Whether a board apply's operations take a PET, a sub-PET or a GET off the board: a merge or an apart."""
    spec = args.ops if isinstance(args.ops, (dict, list)) else {}
    ops = spec.get("operations") if isinstance(spec, dict) else spec
    return any(isinstance(op, dict) and str(op.get("op") or "").strip().lower() in LABEL_GONE for op in ops or [])


def board_of(p, args, gets: bool) -> dict | None:
    """The board an op names, as the op finds it, or None."""
    import idiograph_cli as icli
    try:
        if gets:
            return icli.gets_named(p, args, "canvas")[1]
        data = icli.load_board_file(Path(p.case(args.case)["workbook"]))
        return icli.pick_board(data, args.board, default="canvas")
    except (cli.Refused, WorkbookError, OSError, KeyError):
        return None


def whole_send(p, args) -> bool:
    """A send of every participant, or one written outside the project's folder."""
    if getattr(args, "list", False):
        return False
    import idiograph_cli as icli
    every = not getattr(args, "participant", None)
    try:
        target = icli.sent_target(args.to, p.info["name"])
    except (cli.Refused, TypeError):
        return every
    return every or not srv.inside(target, p.root)


# Each op that waits, by the command and its act, and when: the destructive ones always, the rest on what their
# dry run says (holds design, 26 October, its table). `when(p, args, answer)` with the dry run's answer
HELD = {
    ("board", "delete"): lambda p, args, answer: True,
    ("gets", "delete"): lambda p, args, answer: True,
    ("board", "restore"): lambda p, args, answer: True,
    ("gets", "restore"): lambda p, args, answer: True,
    ("transcript", "replace"): lambda p, args, answer: bool(getattr(args, "all", False)) and answer.get("replaced", 0) > 0,
    ("transcript", "replace-undo"): lambda p, args, answer: len(answer.get("participants") or []) >= 2,
    ("turn", "trim"): lambda p, args, answer: True,
    ("turn", "write"): lambda p, args, answer: any(c.get("removed") for c in answer.get("cards") or []),
    ("board", "apply"): lambda p, args, answer: takes_labels_off(args) and not is_agent_board(board_of(p, args, False)),
    ("gets", "apply"): lambda p, args, answer: takes_labels_off(args) and not is_agent_board(board_of(p, args, True)),
    ("trajectories", "apply"): lambda p, args, answer: any(
        isinstance(op, dict) and str(op.get("op") or "").lower() == "remove"
        for op in ((args.ops.get("operations") if isinstance(args.ops, dict) else args.ops) or [])),
    ("gets", "take"): lambda p, args, answer: bool((answer.get("changes") or {}).get("gone")),
    ("participant", "rename"): lambda p, args, answer: bool(getattr(args, "folder", False)),
    ("project", "send"): lambda p, args, answer: whole_send(p, args),
    # Remove from Idiograph with its folder to the Trash (removetrash, 10 November 2026): it looks permanent
    ("project", "remove"): lambda p, args, answer: bool(getattr(args, "trash", False)),
    # a thematic analysis project's code list (codes, 2 November 2026): a rename and a merge write every workbook
    # and every board, and a delete takes a code off the list
    ("codes", "rename"): lambda p, args, answer: bool(answer.get("changes")),
    ("codes", "merge"): lambda p, args, answer: bool(answer.get("changes")),
    ("codes", "delete"): lambda p, args, answer: bool(answer.get("changes")),
    # Working together (wtkeys, 8 November 2026): who may read the project, which outlives the conversation
    ("team", "on"): lambda p, args, answer: not getattr(args, "off", False) and bool(answer.get("changes")),
    ("team", "invite"): lambda p, args, answer: True,
    ("team", "admit"): lambda p, args, answer: not getattr(args, "differ", False),
    ("team", "join"): lambda p, args, answer: True,
    ("team", "remove"): lambda p, args, answer: True,
    ("team", "lead"): lambda p, args, answer: True,
    # a teammate's board accepted or declined (wtboard, 9 November 2026): the owner's to judge, as a suggestion is
    ("team", "board-answer"): lambda p, args, answer: True,
    # a teammate's suggestion accepted or declined (wtsuggest, 10 November 2026): the owner's to judge
    ("team", "suggestion-answer"): lambda p, args, answer: True,
}


# the ops that can carry his relay code from the standard input (relaywire), which with the setting off are refused
# rather than held, since the code is kept nowhere and Approve would run without it (smokefix, 9 November 2026)
CODE_OPS = (("team", "on"), ("team", "set"))


# The risk each op's hold answers (agentholds, Adam, 2 November 2026, by dialog: the shared statement at the head of
# docs/agents.md, from Harbour's): 1, steering, it acts on text it reads, which anyone may have written. 2, speed
# and volume, it does in a minute what he does in a day. 3, no screen, it can act on the wrong thing with nobody
# looking. 4, standing access, a setting that outlives the conversation. Area 261 fails on an op of `HELD` with none,
# and on a row of agents.md's table of holds that says otherwise.
RISKS = {1: "steering", 2: "speed and volume", 3: "no screen", 4: "standing access"}
RISK = {
    ("board", "delete"): (3,),
    ("gets", "delete"): (3,),
    ("board", "restore"): (3,),
    ("gets", "restore"): (3,),
    ("transcript", "replace"): (1, 2),
    ("transcript", "replace-undo"): (2,),
    ("turn", "trim"): (3,),
    ("turn", "write"): (3,),
    ("board", "apply"): (3,),
    ("gets", "apply"): (3,),
    ("trajectories", "apply"): (3,),
    ("gets", "take"): (2,),
    ("participant", "rename"): (2, 3),
    ("project", "send"): (1,),
    ("project", "remove"): (3,),
    ("codes", "rename"): (2,),
    ("codes", "merge"): (2,),
    ("codes", "delete"): (3,),
    ("team", "on"): (4,),
    ("team", "invite"): (4,),
    ("team", "admit"): (4,),
    ("team", "join"): (4,),
    ("team", "remove"): (4,),
    ("team", "lead"): (4,),
    ("team", "board-answer"): (1,),
    ("team", "suggestion-answer"): (1,),
}


def skip_on() -> bool:
    """Whether "Dangerously skip permissions" is ticked, in the settings this run reads, off by default."""
    try:
        return srv.config().get(SETTING) is True
    except (OSError, ValueError):
        return False


# ------------------------------------------------------------------ the words

def agent_of(tool: str, inside: bool = False) -> str:
    """The agent by its name, else "The agent", or "the agent" `inside` a sentence, in the run's language."""
    return agent_words(tool, NAME_MOST) or (i18n.t("server.holds_agent_inside") if inside else i18n.t("server.holds_agent"))


# The agent's own words as the card quotes them (agentholds, Adam, 2 November 2026, by dialog, from Harbour's
# `keyWords`): what it says he asked, a replace's find and put words and a new name it gives, never shown as his.
# On one line, with no character a reader cannot see (a control, a direction mark, a zero-width space or joiner, a
# variation selector, which can carry a hidden message), no quotation mark or lookalike that could close the card's
# own, every "://" broken so no address is drawn as a link, and no longer than `most`
WORDS_MOST = 300
NAME_MOST = 60
# the cleaning itself is the family's since 3 November 2026, so the agent log cleans the same (agent_log.py)
from agent_log import QUOTE_LIKE, UNSEEN, agent_words, unseen  # noqa: E402,F401


def said_by(s, most: int = WORDS_MOST) -> dict:
    """An agent's words kept as they came, said through `agent_words` whenever the card or a line says them."""
    return {"agent": str(s or ""), "most": most}


def up(s: str) -> str:
    return s[:1].upper() + s[1:]


# What a hold keeps when the agent asks (i18nleft2, 1 November 2026): `what`, `done`, `kept` and `would_do` in
# English, as the command line and MCP read them, and beside them in `said` the same words as keys of the catalogue
# (`holds.json`) and their slots, so the card says them in the reader's language. A slot may itself be such a pair,
# or the agent's or the command line's own words, kept as they came. A hold kept before this has no `said`, and its
# card shows its English as it was written.

def t(key: str, **slots) -> dict:
    """A sentence kept as its key and slots, said when the card shows it (see `text_of`)."""
    return {"key": key, "slots": slots}


def upper(x):
    """A sentence said with its first letter a capital, a kept one or words as they came."""
    return dict(x, up=True) if isinstance(x, dict) else up(str(x))


def lead(x, by: str = "  "):
    """A sentence said after `by`, the card's indent for a line under another."""
    return dict(x, lead=by) if isinstance(x, dict) else by + str(x)


def when_of(at: str, now: str) -> dict:
    """A revision's time kept to be said when the card shows it (i18nleft3), as the History said it at `now`."""
    return {"when": str(at), "now": str(now)}


def names_of(items) -> dict:
    """Names kept to be joined as the reader's language joins a list when the card shows them (i18nleft3)."""
    return {"list": [str(x) for x in items]}


def text_of(x, lang: str | None = None) -> str:
    """A kept sentence in `lang`, or the run's language, its slots said first, or words as they came. English is
    read in IPA's words, as the file keeps it, a time and a list in English's own formats."""
    if isinstance(x, dict) and "when" in x and "key" not in x:
        try:
            now = datetime.fromisoformat(str(x.get("now"))).astimezone()
        except (TypeError, ValueError):
            now = None
        return themes.when_said(x["when"], now, lang=lang)
    if isinstance(x, dict) and isinstance(x.get("list"), list) and "key" not in x:
        return formats.list_words([text_of(v, lang) for v in x["list"]], lang=lang)
    if isinstance(x, dict) and "agent" in x and "key" not in x:
        return agent_words(x["agent"], int(x.get("most") or WORDS_MOST))
    if not isinstance(x, dict) or "key" not in x:
        return str(x)
    vals = {k: (text_of(v, lang) if isinstance(v, (dict, str)) else v) for k, v in (x.get("slots") or {}).items()}
    # a replace's words kept as plain text by a hold made before `said_by`, cleaned as its are
    vals.update({k: agent_words(v) for k, v in (x.get("slots") or {}).items()
                 if k in ("find", "put") and isinstance(v, str)})
    said = i18n.t(x["key"], vals, lang=lang, method="ipa" if lang == "en" else None)
    return str(x.get("lead") or "") + (up(said) if x.get("up") else said)


def english(x) -> str:
    return text_of(x, "en")


def pets_counted(state: dict | None) -> dict:
    """A PETs board's or a revision's counts as the card says them: "6 PETs and 31 statements placed"."""
    v = themes.normalise(state or {})
    parents = themes.parents_of(v["groups"])
    tops = sum(1 for g in v["groups"] if g["id"] not in parents)
    placed = sum(1 for k in v["cards"] if k in parents)
    return t("holds.counts", groups=t("holds.n.pets", n=tops), placed=t("holds.n.statements", n=placed))


def gets_counted(state: dict | None) -> dict:
    """A GETs board's or a revision's counts, "3 GETs and 14 cards placed", a card a participant's PET or
    sub-theme."""
    groups = [g for g in (state or {}).get("groups") or [] if isinstance(g, dict)]
    parents = {m for g in groups for m in g.get("members") or []}
    tops = sum(1 for g in groups if g.get("id") not in parents)
    placed = sum(1 for k in (state or {}).get("cards") or {} if k in parents)
    return t("holds.counts", groups=t("holds.n.gets", n=tops), placed=t("holds.n.cards", n=placed))


def pets_counts(state: dict | None) -> str:
    return english(pets_counted(state))


def gets_counts(state: dict | None) -> str:
    return english(gets_counted(state))


def file_of(p, args, gets: bool) -> dict | None:
    """The participant's boards file, or the project's GETs file, as the op reads it."""
    import gets as gets_mod
    import idiograph_cli as icli
    try:
        if gets:
            return gets_mod.load(p.root)
        return icli.load_board_file(Path(p.case(args.case)["workbook"]))
    except (cli.Refused, WorkbookError, OSError, KeyError, ValueError):
        return None


def named_board(data: dict | None, said, default: str) -> dict | None:
    import idiograph_cli as icli
    try:
        return icli.pick_board(data, said, default=default)
    except (cli.Refused, WorkbookError, KeyError):
        return None


def current_line(data: dict | None, vid: str, gone: bool) -> dict:
    """Which board stays the Current board, or becomes it when the one deleted was it."""
    boards = themes.boards_of(data)
    by_id = {str(b.get("id")): str(b.get("name")) for b in boards}
    chosen = themes.chosen_of(data)
    if chosen and (chosen != vid or not gone):
        return t("holds.current.stays", name=by_id[chosen])
    if chosen:
        left = [i for i in by_id if i != vid]
        return t("holds.current.becomes", name=by_id[left[0]]) if len(left) == 1 else t("holds.current.none_after")
    return t("holds.current.none")


def would_lines(p, args, answer: dict, lines: list) -> list:
    """What the op would do, line by line, from its own dry run: what goes or changes with its counts, where a
    copy is kept, and what stays, as Adam's drawing of 26 October says a delete: "Board 2 of Juno, 6 PETs and 31
    statements placed, is deleted." / "A copy is kept in Juno's Archive folder." / "Board 1 stays the Current board."
    Read before the op runs, so the counts are the board's as it stands. Each line kept as its key and slots, or
    the command line's own words where the line is its."""
    key = (args.command, args.act)
    case = answer.get("case") or getattr(args, "case", None) or ""
    if key[0] in ("board", "gets") and key[1] in ("delete", "restore", "apply"):
        gets = key[0] == "gets"
        counted = gets_counted if gets else pets_counted
        data = file_of(p, args, gets)
        board = named_board(data, getattr(args, "board", None), "canvas" if key[1] == "apply" else "chosen") or {}
        vid, name = str(board.get("id") or answer.get("board") or ""), str(board.get("name") or answer.get("name") or "")
        thing = upper(t("holds.gets_board", name=name)) if gets else t("holds.pets_board", name=name, case=case)
        kept = t("holds.would.kept_history")
        if key[1] == "delete":
            where = t("holds.where.project") if gets else t("holds.where.case", case=case)
            return [t("holds.would.deleted", thing=thing, counts=counted(board)), t("holds.would.copy_kept", where=where),
                    current_line(data, vid, True)]
        if key[1] == "restore":
            rev = next((r for r in themes.history_of(board) if str(r["id"]).lower() == str(args.revision).lower()), None)
            then = (t("holds.would.its_revision", when=when_of(rev["at"], themes.now_iso()),
                      counts=counted(rev["state"])) if rev else t("holds.would.an_old_revision"))
            return [t("holds.would.becomes", thing=thing, counts=counted(board), then=then), kept,
                    current_line(data, vid, False)]
        said = str(answer.get("said") or "")
        said = up(said.split(" it would have: ", 1)[1]) if " it would have: " in said else said
        return [t("holds.would.changed_head", thing=thing, counts=counted(board)), lead(said), kept,
                current_line(data, vid, False)]
    if key == ("project", "remove"):
        name = answer.get("name") or p.info["name"]
        return [t("holds.would.project_trash", name=name),
                t("holds.would.project_trash_folder", where=answer.get("where") or "", folder=answer.get("folder") or "")]
    if key == ("trajectories", "apply"):
        return [t("holds.would.trajectories_head")] + [lead(x) for x in answer.get("changes") or []]
    if key[0] == "team":
        # Working together (wtkeys): its dry run's own lines, who works on the project being what changes
        return [str(x) for x in answer.get("changes") or []]
    if key[0] == "codes":
        out = [t("holds.would.codes_head")] + [lead(x) for x in answer.get("changes") or []]
        if answer.get("rows"):
            out.append(t("holds.would.codes_rows", rows=t("holds.n.rows", n=answer["rows"]),
                         participants=t("holds.n.participants", n=len(answer.get("participants_changed") or []))))
            out.append(t("holds.would.codes_copies"))
        return out
    if key == ("gets", "take"):
        import gets as gets_mod
        import idiograph_cli as icli
        who = gets_mod.who(case)
        n = len(themes.boards_of(file_of(p, args, True)))
        return ([t("holds.would.take_head", who=who, boards=t("holds.n.boards", n=n))]
                + [lead(x) for x in icli.changes_lines(who, answer.get("changes") or {})]
                + [t("holds.would.take_kept", who=who)])
    if key in (("transcript", "replace"), ("transcript", "replace-undo")):
        each = answer.get("participants") or []
        rows_of = lambda a: len({(x["sheet"], x["row"]) for x in a.get("places") or []})
        total = t("holds.n.occurrences", n=answer.get("replaced", 0))
        where = t("holds.would.where_rows", rows=t("holds.n.rows", n=sum(rows_of(a) for a in each)),
                  participants=t("holds.n.participants", n=len(each)))
        if key[1] == "replace":
            out = [t("holds.would.replaced_words", total=total, find=said_by(answer["find"]), put=said_by(answer["put"]),
                     where=where)
                   if "find" in answer else t("holds.would.replaced", total=total, where=where)]
            tail = [t("holds.would.batch_kept")]
        else:
            out = [t("holds.would.redone", total=total, batch=answer.get("batch"), where=where) if answer.get("redo")
                   else t("holds.would.put_back", total=total, batch=answer.get("batch"), where=where)]
            tail = []
        for a in each:
            cards = sum(b.get("cards", 0) for b in a.get("boards") or [])
            occ, rows = t("holds.n.occurrences", n=a["replaced"]), t("holds.n.rows", n=rows_of(a))
            out.append(lead(t("holds.would.participant_cards", case=a["case"], total=occ, rows=rows,
                              cards=t("holds.n.cards", n=cards)) if cards
                            else t("holds.would.participant", case=a["case"], total=occ, rows=rows)))
        out += [lead(t("holds.would.participant_refused", case=x["case"], reason=x["reason"]))
                for x in answer.get("refused") or []]
        return out + tail
    if key == ("turn", "trim"):
        rows = answer.get("first") != answer.get("last")
        span = (t("holds.span.rows", first=answer.get("first"), last=answer.get("last")) if rows
                else t("holds.span.row", first=answer.get("first")))
        if answer.get("from"):
            span = t("holds.span.times", span=span, start=answer["from"], end=answer["to"])
        cut = dict(case=case, sheet=args.sheet, span=span, count=t("holds.n.rows", n=answer.get("count", 0)),
                   marked=answer.get("marked", 0))
        return [t("holds.would.trim_are", **cut) if rows else t("holds.would.trim_is", **cut),
                t("holds.would.workbook_copy", case=case),
                t("holds.would.trim_left", left=t("holds.n.rows", n=answer.get("left", 0)))]
    if key == ("turn", "write"):
        out = [t("holds.done.write", case=case, sheet=args.sheet, row=args.row)]
        for b in answer.get("cards") or []:
            for m in b.get("removed") or []:
                out.append(lead(t("holds.would.card_off", board=b["name"], card=m["key"], text=m["text"])))
            for m in b.get("moved") or []:
                out.append(lead(t("holds.would.card_moves", board=b["name"], card=m["from"], text=m["text"],
                                  to=m["to"])))
        names = sorted({b["name"] for b in answer.get("cards") or []})
        out.append(t("holds.would.workbook_copy", case=case))
        if len(names) == 1:
            out.append(t("holds.would.one_kept", name=names[0]))
        elif names:
            out.append(t("holds.would.several_kept", names=names_of(names)))
        return out
    if key == ("participant", "rename"):
        return ([t("holds.would.renamed_head", old=answer.get("old") or case,
                   new=said_by(answer.get("new") or args.name, NAME_MOST))]
                + [lead(f"{up(x)}.") for x in (answer.get("changes") or []) + (answer.get("folder_changes") or [])]
                + [t("holds.would.archive_each")])
    # project send: what goes, from its dry run's lines, and that nothing in the project changes
    out, head = [], f"It would write {answer.get('file')}, "
    for x in (str(x) for x in lines):
        if x.startswith("Dry run, nothing was written."):
            continue
        if x.startswith(head) and ": " in x:
            what, said = x[len(head):].rsplit(": ", 1)
            out += [f"{up(what)} is written to one file, {said}", t("holds.would.goes_to", file=answer.get("file"))]
            continue
        out.append(x.replace("It would hold:", "It holds:").replace("It would give", "It gives"))
    return out + [t("holds.would.nothing_changes")]


def said_of(p, args, answer: dict, lines: list | None = None) -> dict:
    """What the op would do, said for the line, the card and the line after each answer: `what`, a verb phrase,
    `would_do`, the card's lines (`would_lines`), `done`, after Approve, and `kept`, after Decline, each in English,
    and `said`, the same as keys and slots (see `t`)."""
    key = (args.command, args.act)
    case = answer.get("case") or getattr(args, "case", None) or ""
    name = answer.get("name") or ""
    if not name and key in (("board", "apply"), ("gets", "apply")):
        board = board_of(p, args, key[0] == "gets")
        name = str((board or {}).get("name") or getattr(args, "board", "") or "")
    pets = t("holds.pets_board", name=name, case=case)
    gets = t("holds.gets_board", name=name)
    kept = None
    if key == ("board", "delete"):
        what, done, thing = t("holds.what.delete", thing=pets), t("holds.done.deleted_case", thing=pets, case=case), pets
    elif key == ("gets", "delete"):
        what, done, thing = (t("holds.what.delete", thing=gets), t("holds.done.deleted_project", thing=upper(gets)),
                             gets)
    elif key in (("board", "restore"), ("gets", "restore")):
        thing = pets if key[0] == "board" else gets
        what = t("holds.what.restore", thing=thing)
        done = t("holds.done.restored", thing=thing if key[0] == "board" else upper(thing))
    elif key in (("board", "apply"), ("gets", "apply")):
        thing = pets if key[0] == "board" else gets
        what = t("holds.what.apply_pets", thing=pets) if key[0] == "board" else t("holds.what.apply_gets", thing=gets)
        done = t("holds.done.changed", thing=thing if key[0] == "board" else upper(thing))
    elif key == ("trajectories", "apply"):
        what, thing, done = (t("holds.what.trajectories"), t("holds.thing.trajectories"), t("holds.done.trajectories"))
    elif key[0] == "codes":
        named = answer.get("named") or {}
        if key[1] == "rename":
            what = t("holds.what.codes_rename", old=named.get("code") or args.code, new=said_by(args.name, NAME_MOST))
        elif key[1] == "merge":
            what = t("holds.what.codes_merge", old=named.get("code") or args.code, new=named.get("into") or args.into)
        else:
            what = t("holds.what.codes_delete", name=named.get("code") or args.code)
        thing, done = t("holds.thing.codes"), t("holds.done.codes")
    elif key == ("gets", "take"):
        who = case.split(" - ")[-1]
        what, thing = t("holds.what.take", who=who), t("holds.thing.gets")
        done = t("holds.done.take", who=who)
    elif key == ("transcript", "replace"):
        # the agent's own words in the line, the card and its row (holdbatchA, 1 November 2026)
        if "find" in answer:
            find, put = said_by(answer["find"]), said_by(answer["put"])
            what = t("holds.what.replace", find=find, put=put)
            done = t("holds.done.replace", find=find, put=put)
        else:
            what, done = t("holds.what.replace_words"), t("holds.done.replace_words")
        thing = t("holds.thing.transcripts")
    elif key == ("transcript", "replace-undo"):
        n = len(answer.get("participants") or [])
        if getattr(args, "redo", False):
            what, done = t("holds.what.redo", n=n), t("holds.done.redo", n=n)
        else:
            what, done = t("holds.what.undo", n=n), t("holds.done.undo", n=n)
        thing = t("holds.thing.transcripts")
    elif key == ("turn", "trim"):
        span = (t("holds.span.rows", first=answer.get("first"), last=answer.get("last"))
                if answer.get("first") != answer.get("last") else t("holds.span.row", first=answer.get("first")))
        what, thing = t("holds.what.trim", span=span, case=case, sheet=args.sheet), t("holds.thing.transcript", case=case)
        done = t("holds.done.trim", span=upper(span), case=case, sheet=args.sheet)
    elif key == ("turn", "write"):
        what = t("holds.what.write", case=case, sheet=args.sheet, row=args.row)
        thing, done = t("holds.thing.passage"), t("holds.done.write", case=case, sheet=args.sheet, row=args.row)
    elif key[0] == "team":
        # Working together (wtkeys, 8 November 2026)
        what, done = {"on": (t("holds.what.team_on"), t("holds.done.team_on")),
                      "invite": (t("holds.what.team_invite"), t("holds.done.team_invite")),
                      "admit": (t("holds.what.team_admit"), t("holds.done.team_admit")),
                      "join": (t("holds.what.team_join"), t("holds.done.team_join")),
                      "remove": ((t("holds.what.team_remove_computer"), t("holds.done.team_remove_computer"))
                                 if getattr(args, "computer", None) else
                                 (t("holds.what.team_remove"), t("holds.done.team_remove"))),
                      "lead": (t("holds.what.team_lead"), t("holds.done.team_lead")),
                      "board-answer": (t("holds.what.team_board_decline") if getattr(args, "decline", False)
                                       else t("holds.what.team_board_accept"),
                                       t("holds.done.team_board_decline") if getattr(args, "decline", False)
                                       else t("holds.done.team_board_accept")),
                      "suggestion-answer": (t("holds.what.team_suggestion_decline") if getattr(args, "decline", False)
                                            else t("holds.what.team_suggestion_accept"),
                                            t("holds.done.team_suggestion_decline") if getattr(args, "decline", False)
                                            else t("holds.done.team_suggestion_accept"))}[key[1]]
        thing = t("holds.thing.team")
    elif key == ("project", "remove"):
        named, where = answer.get("name") or p.info["name"], answer.get("where") or ""
        what, thing = t("holds.what.project_trash", name=named, where=where), named
        done = t("holds.done.project_trash", name=named, where=where)
    elif key == ("participant", "rename"):
        old, new = answer.get("old") or case, said_by(answer.get("new") or args.name, NAME_MOST)
        what, thing = t("holds.what.rename", old=old, new=new), old
        done = t("holds.done.rename", old=old, new=new)
    else:
        whole = not getattr(args, "participant", None)
        what = t("holds.what.send_whole") if whole else t("holds.what.send_part")
        thing, done, kept = "", t("holds.done.sent"), t("holds.kept.sent")
    would = would_lines(p, args, answer, lines or [])
    said = {"what": what, "done": t("holds.done.line", done=done), "would_do": would,
            "kept": kept or t("holds.kept.stays", thing=upper(thing))}
    return {"what": english(said["what"]), "done": english(said["done"]), "would_do": [english(x) for x in would],
            "kept": english(said["kept"]), "said": said}


def said_now(h: dict, part: str):
    """A part of what the hold keeps in the reader's language: from its keys, or as it was written for a hold kept
    before them."""
    said = h.get("said") if isinstance(h.get("said"), dict) else {}
    if part == "would_do":
        return ([text_of(x) for x in said["would_do"]] if isinstance(said.get("would_do"), list)
                else list(h.get("would_do") or []))
    return text_of(said[part]) if part in said else str(h.get(part) or "")


def take_would(h: dict, would: list, codes) -> None:
    """The hold takes what it would do now, in English and as keys, or with no keys when the dry run refused."""
    h["would_do"] = would
    said = h.get("said") if isinstance(h.get("said"), dict) else None
    if said is not None:
        if codes is None:
            said.pop("would_do", None)
        else:
            said["would_do"] = codes


def asked_line(at: str, request: str, now: datetime | None = None, tool: str = "") -> str:
    """When it was asked and what the agent says he asked, in its words, cleaned (`agent_words`), as the card says
    them: never as his own request, which only the agent reports."""
    try:
        when = datetime.fromisoformat(at)
    except (TypeError, ValueError):
        when = None
    now = now or datetime.now().astimezone()
    if when is None:
        head = i18n.t("server.holds_asked")
    elif when.date() == now.date():
        head = i18n.t("server.holds_asked_at", time=formats.clock_words(when))
    else:
        head = i18n.t("server.holds_asked_on", day=formats.day_words(when), time=formats.clock_words(when))
    said = agent_words(request)
    return (i18n.t("server.holds_asked_request", asked=head, agent=agent_of(tool), request=said) if said
            else i18n.t("server.holds_asked_alone", asked=head))


def method_at(root) -> str | None:
    """The method of the project at `root` as its file holds it, None when it cannot be read (i18nleft3)."""
    try:
        data = json.loads((Path(root) / srv.PROJECT_FILE).read_text(encoding="utf-8"))
    except (OSError, ValueError, TypeError):
        return None
    return i18n.method_of(data.get("method")) if isinstance(data, dict) else None


def shown(h: dict, root=None) -> dict:
    """A hold as the page and an agent read it: what it is and where it stands, with its words for the line, in
    the words of the method of the project at `root` (a thematic analysis project's), else the run's."""
    with i18n.in_method(method_at(root) if root is not None else None):
        return shown_here(h)


def shown_here(h: dict) -> dict:
    agent = agent_of(h.get("tool"))
    what = said_now(h, "what")
    # the agent's name and what it says he asked, cleaned as the card quotes them (agentholds)
    out = {"id": h["id"], "op": h["op"], "status": h["status"], "tool": agent_words(h.get("tool"), NAME_MOST),
           "at": h["at"], "request": agent_words(h.get("request")),
           "question": i18n.t("server.holds_question", what=up(what)),
           "waiting": i18n.t("server.holds_waiting", agent=agent, what=what),
           "asked": asked_line(h["at"], h.get("request"), tool=h.get("tool") or ""),
           "would_do": said_now(h, "would_do"), "changed": bool(h.get("changed")),
           # whose files changed since the agent asked, "Mabel's boards", and whether his own answers since
           # changed what it would do, "deleted" or "changed" (holdbatchA)
           "changed_what": h.get("changed_what") or "", "since_yours": h.get("since_yours") or ""}
    if h.get("answered"):
        out["answered"] = h["answered"]
    if h["status"] == "approved":
        out["line"] = said_now(h, "done")
    elif h["status"] == "declined":
        out["line"] = i18n.t("server.holds_declined", kept=said_now(h, "kept"), agent=agent_of(h.get("tool"), inside=True))
    if out.get("line"):
        # the same words without "Done." or "Declined." before them, for a row of the card for several, whose
        # state stands beside it
        out["said"] = re.sub(r"^\w+\. ", "", out["line"], count=1)
    if h.get("result"):
        out["result"] = h["result"]
    return out


# ------------------------------------------------------------------ the file

def path_of(root: Path) -> Path:
    return Path(root) / FILE


def load(root: Path) -> dict:
    try:
        data = json.loads(path_of(root).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {"holds": []}
    if not isinstance(data, dict) or not isinstance(data.get("holds"), list):
        return {"holds": []}
    data["holds"] = [h for h in data["holds"] if isinstance(h, dict) and h.get("id")]
    return data


def save(root: Path, data: dict) -> None:
    srv.save_json(path_of(root), data)


def held(root: Path):
    """The holds file's own lock, apart from the project's and a case's, so a hold is written while an op holds
    those."""
    return locks.held(Path(root) / LOCK)


def find(data: dict, hid: str) -> dict:
    said = str(hid or "").strip().lower()
    h = next((h for h in data["holds"] if str(h["id"]).lower() == said), None)
    if h is None:
        raise cli.Refused(NOT_HERE)
    return h


# ------------------------------------------------------------------ the gate

def frozen(args) -> argparse.Namespace:
    """The op's arguments with every file it reads read once, so the dry run, the hold and Approve run on the same."""
    out = copy.copy(args)
    for key in FILE_KEYS:
        value = getattr(out, key, None)
        if isinstance(value, (str, Path)) and value:
            setattr(out, key, cli.read_spec(value))
    if (args.command, args.act) == ("transcript", "replace") and isinstance(getattr(out, "pairs", None), (str, Path)):
        import idiograph_cli as icli
        out.pairs = icli.pairs_from(out.pairs)
    return out


def kept_args(args) -> dict:
    """The arguments as a hold keeps them, without the project's choices or anything of the run's own."""
    out = {}
    for k, v in vars(args).items():
        if k in PROJECT_KEYS or k.startswith("_"):
            continue
        try:
            json.dumps(v)
        except (TypeError, ValueError):
            continue
        out[k] = v
    return out


def norm(lines: list[str]) -> list[str]:
    """A dry run's lines with the clock taken out, so a revision named "Before restoring 12:04" reads the same a
    minute later."""
    return [re.sub(r"\b\d{1,2}:\d{2}\b", "", str(x)) for x in lines]


def touched(p, args) -> list[Path]:
    """The files an op reads and writes, whose change since the hold the card says."""
    import gets as gets_mod
    import trajectories as traj_mod
    key = (args.command, args.act)
    files: list[Path] = []
    if getattr(args, "case", None):
        books = [p.case(args.case)]
    elif key[0] in ("transcript",):
        books = list(p.books)
    else:
        books = []
    for b in books:
        book = Path(b["workbook"])
        # a board op reads the participant's boards alone, and every other op the workbook and its files too
        if key[0] == "board":
            files += sorted(book.parent.joinpath("Working").glob(f"{book.stem}*themes*.json"))
        else:
            files += [book] + sorted(book.parent.joinpath("Working").glob(f"{book.stem}*.json"))
    if key[0] in ("gets", "trajectories"):
        files += [gets_mod.gets_path(p.root), Path(p.root) / "idiograph-lgets.json", Path(p.root) / traj_mod.FILE]
    if key[0] == "codes":
        import codes as codes_mod
        files += [Path(b["workbook"]) for b in p.books]
        files += [gets_mod.gets_path(p.root), codes_mod.path_of(p.root)]
    return files


def fingerprint(p, args) -> dict:
    """Each touched file's mtime and size, by its path with any link resolved, so the project reached as the agent
    named it and as the app's list names it, /var or /private/var on a Mac, gives the same keys (holdbatchA)."""
    out = {}
    for f in touched(p, args):
        key = str(Path(f).resolve())
        try:
            st = f.stat()
            out[key] = [st.st_mtime_ns, st.st_size]
        except OSError:
            out[key] = None
    return out


def changed_what(p, old: dict | None, new: dict | None) -> str:
    """What changed since the agent asked, by whose files, for the card and the refusal (holdbatchA, 1 November
    2026): "Mabel's boards", "Juno's transcript and Rowan's boards", "The GETs". Empty when no file differs."""
    import gets as gets_mod
    import idiograph_cli as icli
    import trajectories as traj_mod
    old, new = old or {}, new or {}
    moved = [Path(f) for f in sorted(set(old) | set(new)) if old.get(f) != new.get(f)]
    if not moved:
        return ""
    parts = []
    for b in p.books:
        book = Path(b["workbook"]).resolve()
        mine = [f for f in moved if f == book or (f.parent == book.parent / "Working" and f.name.startswith(book.stem))]
        if not mine:
            continue
        name = icli.case_name(Path(b["workbook"]))
        if any(f == book or "themes" not in f.name for f in mine):
            parts.append(i18n.t("server.holds_part_transcript", name=name))
        if any("themes" in f.name for f in mine):
            parts.append(i18n.t("server.holds_part_boards", name=name))
    root = Path(p.root).resolve()
    for path, said in ((Path(gets_mod.gets_path(p.root)).resolve(), lambda: i18n.t("server.holds_part_gets")),
                       (root / "idiograph-lgets.json", lambda: i18n.t("server.holds_part_lgets")),
                       (root / traj_mod.FILE, lambda: i18n.t("server.holds_part_trajectories"))):
        if path in moved:
            parts.append(said())
    out = formats.list_words(list(dict.fromkeys(parts)))
    return up(out) if out else ""


def gate(p, args, run):
    """One op as an agent asked it: an op of `HELD` with the setting off waits as a hold, its dry run kept, and
    any other runs at once through `run`. With the setting on a held op runs at once, its History saying
    "without asking"."""
    key = (args.command, getattr(args, "act", None))
    if (key in CODE_OPS and getattr(args, "code_stdin", False) and not getattr(args, "off", False)
            and not args.dry_run and not getattr(args, "_approved", False) and not RUN_AT_ONCE and not skip_on()):
        # a relay code is never kept, so a hold could not carry it to his Approve: refused, nothing read or written
        raise cli.Refused(i18n.t("team.cli.code_held"))
    if key not in HELD or args.dry_run or getattr(args, "_approved", False) or RUN_AT_ONCE:
        return run(args)
    if skip_on():
        args.tool = f"{agent_of(args.tool) if themes_ai.one_line(args.tool) else cli.TOOL}, {WITHOUT}"
        return run(args)
    args = frozen(args)
    dry = copy.copy(args)
    dry.dry_run = True
    answer, lines = run(dry)
    # an apply names his request in its file, which its dry run takes as the note
    request = themes_ai.one_line(getattr(dry, "note", "") or args.note)
    if not HELD[key](p, args, answer):
        return run(args)
    if not request:
        # the op's own refusal, asking for his request
        return run(args)
    args.note = request
    said = said_of(p, args, answer, lines)
    when = datetime.now().astimezone().isoformat(timespec="seconds")
    with held(p.root):
        data = load(p.root)
        n = max([int(m.group(1)) for h in data["holds"] for m in [re.match(r"h(\d+)$", str(h["id"]))] if m] or [0]) + 1
        h = {"id": f"h{n}", "op": " ".join(x for x in key if x), "status": "waiting", "at": when,
             "tool": themes_ai.one_line(args.tool), "request": request, "dry": [str(x) for x in lines],
             "args": kept_args(args), "fingerprint": fingerprint(p, args), **said}
        data["holds"].append(h)
        save(p.root, data)
    view = shown(h)
    ask = cli.opener("hold_show", {"id": h["id"]}, ["hold", "show", h["id"]])
    line = (f"Waiting for his yes in Idiograph: {h['what']}. Nothing was written. Ask after it with {ask['command']}, "
            "or hold_show through MCP.")
    out = {"held": view, "ask": ask, "said": line}
    return out, [line, "", "What it would do:"] + [f"  {x}" for x in h["would_do"]]


# ------------------------------------------------------------------ the agent asks after it

def hold_lines(v: dict) -> list[str]:
    head = {"waiting": "Waiting for his yes", "approved": "Approved in the app", "declined": "Declined in the app",
            "approving": "Being run in the app now", "failed": "Approved in the app, and refused"}[v["status"]]
    lines = [f"{v['id']}: {v['question']} {head}" + (f", {cli.when_said(v['answered'])}." if v.get("answered") else ".")]
    if v.get("changed") and v["status"] == "waiting":
        lines.append("  It changed since it was asked. He sees what it would do now.")
    if v.get("result"):
        lines += [f"  {x}" for x in v["result"].get("lines") or []]
    return lines


def cmd_hold(p, args) -> tuple:
    """`hold`: every action of this project that waited for his yes, the waiting first, then the answered newest
    first. Only reads."""
    data = load(p.root)
    views = [shown(h) for h in data["holds"]]
    views = ([v for v in views if v["status"] == "waiting"]
             + sorted((v for v in views if v["status"] != "waiting"), key=lambda v: v.get("answered") or v["at"], reverse=True))
    lines = [f"{cli.plural(sum(v['status'] == 'waiting' for v in views), 'action')} waiting for his yes in {p.info['name']}."]
    for v in views:
        lines += hold_lines(v)
    return {"holds": views}, lines


def ids_of(args) -> list[str]:
    """The ids `hold show` was given, one or several: he answers several at once in the app's card for several
    (holdbatchA, 1 November 2026), and the agent reads each one's outcome in one call."""
    given = args.id if isinstance(args.id, list) else [args.id]
    return [str(x).strip() for x in given if str(x or "").strip()] or [""]


def cmd_hold_show(p, args) -> tuple:
    """`hold show <id> [<id> ...]`: each action that waited, where it stands, and once approved, the op's own
    answer. One id answers `hold`, several `holds` in the order given."""
    data = load(p.root)
    views = [shown(find(data, hid)) for hid in ids_of(args)]
    lines = []
    for v in views:
        lines += hold_lines(v) + ([""] + ["What it would do:"] + [f"  {x}" for x in v["would_do"]]
                                  if v["status"] == "waiting" else [])
    return ({"hold": views[0]} if len(views) == 1 else {"holds": views}), lines


def show_in(projects: list, args) -> tuple:
    """`hold show <id>` over every project a run reads: the one that holds the ids, refused when none or two do."""
    said = {i.lower() for i in ids_of(args)}
    found = [p for p in projects if said <= {str(h["id"]).lower() for h in load(p.root)["holds"]}]
    if not found:
        raise cli.Refused(NOT_HERE)
    if len(found) > 1:
        names = " and ".join(p.info["name"] for p in found)
        raise cli.Refused(f"{', '.join(ids_of(args))} {'is an action' if len(said) == 1 else 'are actions'} of "
                          f"{names}. Name one with --project.")
    return cmd_hold_show(found[0], args)


# ------------------------------------------------------------------ the app answers

def project_of(root: Path):
    import idiograph_cli as icli
    root = Path(root)
    return icli.Project(root, srv.is_demo_root(root))


def args_of(h: dict) -> argparse.Namespace:
    given = {k: v for k, v in (h.get("args") or {}).items() if not str(k).startswith("_") and k not in PROJECT_KEYS}
    args = argparse.Namespace(**given)
    args.json, args.project, args.root, args.demo, args.config = True, None, None, False, None
    return args


def scoped_run(p, args):
    import idiograph_cli as icli
    return icli.run_scoped(icli.COMMANDS[(args.command, getattr(args, "act", None))], p, args)


def dry_now(p, h: dict) -> tuple:
    """The hold's dry run again: its lines, the card's lines from it (`said_of`), its files' fingerprint and the
    card's lines as keys, or the op's refusal as the lines and no keys."""
    args = args_of(h)
    args.dry_run = True
    try:
        answer, lines = scoped_run(p, args)
    except cli.Refused as exc:
        return list(exc.lines), list(exc.lines), None, None
    lines = [str(x) for x in lines]
    said = said_of(p, args_of(h), answer, lines)
    return lines, said["would_do"], fingerprint(p, args_of(h)), said["said"]["would_do"]


def differs(h: dict, lines: list, prints) -> bool:
    """Whether the dry run, clock times aside, or the files differ from the hold's."""
    return norm(lines) != norm(h.get("dry") or h.get("would_do") or []) or prints != h.get("fingerprint")


def check(root: Path, hid: str) -> dict:
    """The card's look at a hold as it opens: its dry run again, and when that or its files changed since, the
    hold taking what it would do now, marked changed. Answers the hold as the page reads it."""
    p = project_of(root)
    with held(root):
        data = load(root)
        h = find(data, hid)
        if h["status"] != "waiting":
            return {"hold": shown(h, root), "changed": False}
    lines, would, prints, codes = dry_now(p, h)
    changed = differs(h, lines, prints if prints is not None else h.get("fingerprint"))
    if changed:
        with held(root):
            data = load(root)
            h = find(data, hid)
            h.update(dry=lines, fingerprint=prints or {}, changed=True,
                     changed_what=changed_what(p, h.get("fingerprint"), prints) or h.get("changed_what") or "")
            take_would(h, would, codes)
            save(root, data)
    return {"hold": shown(h, root), "changed": changed}


def approve(root: Path, hid: str) -> dict:
    """Approve: the op run as the agent asked it, under its own lock, History naming the agent and "approved in
    the app". Its dry run again first, and when that or its files changed since the card read it, nothing runs
    and the hold takes what it would do now. Answers the hold, and `changed` when nothing ran."""
    p = project_of(root)
    with held(root):
        data = load(root)
        h = find(data, hid)
        if h["status"] != "waiting":
            raise WorkbookError(i18n.t("server.action_answered_already"))
        h["status"] = "approving"
        save(root, data)
    try:
        lines, would, prints, codes = dry_now(p, h)
        if differs(h, lines, prints):
            with held(root):
                data = load(root)
                h = find(data, hid)
                h.update(status="waiting", dry=lines, fingerprint=prints or {}, changed=True,
                         changed_what=changed_what(p, h.get("fingerprint"), prints) or h.get("changed_what") or "")
                take_would(h, would, codes)
                save(root, data)
            return {"hold": shown(h, root), "changed": True}
        args = args_of(h)
        args.dry_run = False
        args._approved = True
        args.tool = f"{agent_of(h.get('tool')) if h.get('tool') else cli.TOOL}, {APPROVED}"
        try:
            answer, done = scoped_run(p, args)
            status, result = "approved", {"lines": [str(x) for x in done], "answer": answer}
        except (cli.Refused, WorkbookError) as exc:
            status, result = "failed", {"lines": list(getattr(exc, "lines", None) or [str(exc)])}
        if status == "approved" and not Path(root).is_dir():
            # the project's folder went to the Trash with its holds file (removetrash): nothing more is written
            # there, so no lock makes the folder again
            h.update(status=status, answered=datetime.now().astimezone().isoformat(timespec="seconds"), result=result)
            return {"hold": shown(h, root), "changed": False, "gone": True}
        after = fingerprint(p, args_of(h))
    except BaseException:
        with held(root):
            data = load(root)
            find(data, hid)["status"] = "waiting"
            save(root, data)
        raise
    with held(root):
        data = load(root)
        h = find(data, hid)
        h.update(status=status, answered=datetime.now().astimezone().isoformat(timespec="seconds"), result=result)
        save(root, data)
    carry(p, root, hid, prints, after, "deleted" if status == "approved" and h["op"].endswith("delete") else "changed")
    if status == "failed":
        raise WorkbookError(" ".join(result["lines"]))
    return {"hold": shown(h, root), "changed": False}


def decline(root: Path, hid: str) -> dict:
    """Decline: nothing of the op written, and History's line where the op names a board, a revision of it named
    for the decline, the agent and his request. The holds file keeps the answer, which `hold show` gives."""
    p = project_of(root)
    with held(root):
        data = load(root)
        h = find(data, hid)
        if h["status"] != "waiting":
            raise WorkbookError(i18n.t("server.action_answered_already"))
        h.update(status="declined", answered=datetime.now().astimezone().isoformat(timespec="seconds"))
        save(root, data)
    logged_decline(p, h)
    before = fingerprint(p, args_of(h))
    history_line(p, h)
    carry(p, root, hid, before, fingerprint(p, args_of(h)))
    return {"hold": shown(h, root)}


def logged_decline(p, h: dict) -> None:
    """A declined action into the agent log (agentlog, 3 November 2026, see agent_log.py): the agent, the project,
    the op with its flag names, and his request as the agent gave it, never what it would have written."""
    import agent_log
    try:
        flags = sorted(f"--{k.replace('_', '-')}" for k, v in (h.get("args") or {}).items()
                       if v not in (None, False, "", []) and k not in cli.NAMES and k != "note")
        op = str(h.get("op") or "")
        agent_log.add(agent_log.entry(
            via="hold", agent=str(h.get("tool") or ""), request=str(h.get("request") or ""), code=agent_log.DECLINED,
            line=i18n.t("agentlog.declined"), op=op, project=p.info["name"],
            call=agent_log.call_of(["idiograph", *op.split(), *flags], len(op.split()) + 1)))
    except Exception:            # the log never fails his answer
        return


def carry(p, root: Path, hid: str, before: dict | None, after: dict, how: str = "changed") -> list[str]:
    """His own answer carried into the other holds (holdbatchA, 1 November 2026): an approved delete changes that
    participant's boards file, as a decline's History line does, and the next hold on the same files read it as
    changed, so ten deletes on one participant took about 37 clicks. A waiting hold whose files stood as `before`
    when he answered, and stand as `after` now, takes the new fingerprint and its dry run afresh, so a change made
    by his own answers is never counted as a change since the agent asked. A file changed by anything else, before
    his answer or since, leaves the hold as it was, and its card and Approve say it changed. When what it would do
    differs now, the hold says so as his own doing, `since_yours` `how`: "deleted" after an approved delete, else
    "changed", never as a change since the agent asked. Answers the ids carried."""
    if not before:
        return []
    moved = {f for f in set(before) | set(after) if before.get(f) != after.get(f)}
    if not moved:
        return []
    out = []
    for h in [h for h in load(root)["holds"] if h.get("status") == "waiting" and h["id"] != hid]:
        mine = h.get("fingerprint") or {}
        if not moved & set(mine) or any(mine.get(f) != before.get(f) for f in moved & set(mine)):
            continue
        mine_would = list(h.get("would_do") or [])
        lines, would, prints, codes = dry_now(p, h)
        if prints is None:
            continue
        # every file his answer left alone as the hold has it, and those it changed as it left them
        expect = {f: v for f, v in mine.items() if f not in moved}
        expect.update({f: after[f] for f in moved if f in after and f in prints})
        if prints != expect:
            # another file changed by something else: the hold still reads as changed, but the files his answer
            # changed are taken as his answer left them, so the card names only what changed elsewhere
            ours = moved & set(mine)
            if all(prints.get(f) == after.get(f) for f in ours):
                with held(root):
                    data = load(root)
                    w = find(data, h["id"])
                    if w.get("status") == "waiting" and w.get("fingerprint") == mine:
                        w["fingerprint"] = dict({f: v for f, v in mine.items() if f not in ours},
                                                **{f: after[f] for f in ours if f in after})
                        save(root, data)
            continue
        with held(root):
            data = load(root)
            w = find(data, h["id"])
            if w.get("status") != "waiting" or w.get("fingerprint") != mine:
                continue
            w.update(dry=lines, fingerprint=prints)
            take_would(w, would, codes)
            if norm(would) != norm(mine_would):
                w["since_yours"] = how
            save(root, data)
        out.append(h["id"])
    return out


def answer_all(items: list, op: str) -> dict:
    """The card for several (holdbatchA, Adam's option A of 1 November 2026): approve or decline a list of holds,
    `items` of `(root, id)`, in the order given, each one's outcome in the same order. Each runs as Approve or
    Decline runs it alone, so one whose files changed since the agent asked, other than by his own answers
    (`carry`), runs nothing and still waits, and one answered already or gone is passed over with its reason. No
    agent reaches it: it is the page's own route's (`/api/holds`), and no command or tool approves or declines."""
    run = approve if op == "approve" else decline
    out = []
    for root, hid in items:
        row = {"root": str(root), "id": str(hid)}
        try:
            got = run(Path(root), str(hid))
        except cli.Refused as exc:
            out.append(dict(row, outcome="gone", reason=" ".join(exc.lines)))
            continue
        except WorkbookError as exc:
            try:
                h = find(load(Path(root)), hid)
            except cli.Refused:
                h = None
            failed = h is not None and h.get("status") == "failed"
            out.append(dict(row, outcome="failed" if failed else "answered", reason=str(exc),
                            hold=shown(h, root) if h else None))
            continue
        h = got["hold"]
        if got.get("changed"):
            out.append(dict(row, outcome="changed", hold=h,
                            reason=(i18n.t("server.holds_what_changed_waits", {"what": h["changed_what"], "agent": agent_of(h.get("tool"))})
                    if h.get("changed_what") else
                    i18n.t("server.holds_changed_waits", {"agent": agent_of(h.get("tool"))}))))
        else:
            out.append(dict(row, outcome="approved" if op == "approve" else "declined", hold=h))
    done = sum(1 for x in out if x["outcome"] in ("approved", "declined"))
    return {"outcomes": out, "done": done, "asked": len(out)}


def history_line(p, h: dict) -> None:
    """A declined board op's line in that board's History, through the op that saves a revision."""
    given = args_of(h)
    command, act = given.command, getattr(given, "act", None)
    if command not in ("board", "gets") or act not in ("delete", "restore", "apply"):
        return
    args = argparse.Namespace(command=command, act="revision", json=True, project=None, root=None, demo=False,
                              config=None, dry_run=False, case=getattr(given, "case", None),
                              board=getattr(given, "board", None), timepoint=getattr(given, "timepoint", None),
                              lpets=getattr(given, "lpets", None),
                              name=f"Declined in the app: {h['what'][0].upper() + h['what'][1:]}",
                              note=h.get("request") or h["what"],
                              tool=f"{agent_of(h.get('tool')) if h.get('tool') else cli.TOOL}, declined in the app")
    try:
        scoped_run(p, args)
    except (cli.Refused, WorkbookError, OSError):
        pass


def waiting(roots: list[Path]) -> list[dict]:
    """Every hold waiting across the app's projects, oldest first, each with its project's root, for the line."""
    out = []
    for root in roots:
        for h in load(root)["holds"]:
            if h.get("status") == "waiting":
                out.append(dict(shown(h, root), root=str(root)))
    return sorted(out, key=lambda v: v["at"])


def __getattr__(name: str) -> str:
    """The refusals other modules and the checks name as this module's, each read in the run's language when
    asked for (the text layer, 28 October 2026)."""
    said = {
        "ANSWERED": lambda: i18n.t("server.action_answered_already"),
    }
    if name in said:
        return said[name]()
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
