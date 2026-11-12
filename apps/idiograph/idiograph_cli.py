"""Idiograph's command line (22 October 2026, the family codebase's fourth build, from cli.py): an AI agent
in a conversation, Claude Code, Claude Desktop or Codex, reads and writes a project's statements, PETs and
GETs through it, on the app's own code, its commands at the top of `idiograph`, registered with the family's
command line by `cli.register_own`, which the command line's import of this module by its name makes
(`boot.load`).

    ./idiograph cases                  # from the app's folder, idiograph.bat on Windows
    ./idiograph statements Rowan --json
    ./idiograph board new Rowan --from board.json --note "his request" --dry-run

Every rule is the app's: the cards are read by `themes.read_cards`, a board is laid out by
`themes_ai.lay_out` and added through `themes.version_op`, a change to one goes through the
board's applier, `themes_ai.revise_ops`, a turn is written as `/api/commit` writes it,
and every write takes the file lock the server takes (see `locks.py`). Nothing here re-implements
any of them. It works with the server running or not, and the page notices what it writes.

With no option it reads every project Idiograph holds, and a case is named by its pseudonym alone,
unless two projects share it. `--project <name>` takes one project by its name, `--root <folder>`
one by its folder and `--demo` the demo. A project answers only once Project settings, "Allow AI
agents to read this project" is ticked, and the demo always does. Plain readable text by default, and
`--json` for exact output. Every case goes by its pseudonym, and a case folder's second part never reaches
any output or error. Standard library and openpyxl only. The guide an agent reads is `docs/agents.md`.
"""
from __future__ import annotations

import argparse
import base64
import contextlib
import copy
import json
import re
import time
import urllib.parse
from datetime import datetime
from pathlib import Path

import openpyxl

import agent_log
import ai_suggest as ai_mod
import audio as audio_mod
import boot
import canvas_out
import cli
import convert as convert_mod
import demographics as demo_mod
import export as export_mod
import formats
import gets as gets_mod
import gets_word
import holds
import i18n
import idiograph_find
import idiograph_routes as routes
import locks
import print_pdf
import project_history as hist_mod
import project_pack as pack_mod
import review as review_mod
import rounds as rounds_mod
import server as srv
import statement_prompts as prompts
import table_import as table_mod
import themes
import themes_ai
import themes_word
import trajectories as traj_mod
import codes as codes_mod
import workbook as wb_mod
from workbook import WorkbookError

# The words this module says, read in the run's language when said (i18nleft4, 2 November 2026): other
# modules and the checks read them as the module's names, through `__getattr__`, as themes_ai's are
SAID = {
    "PRIVATE": lambda **v: i18n.t("cli.said.private", v),
    "NO_REQUEST": lambda **v: i18n.t("cli.said.no_request", v),
    "NEVER_BIN": lambda **v: i18n.t("cli.said.never_bin", v),
    "LOOSE_SAID": lambda **v: i18n.t("cli.said.loose_said", v),
    "NO_DELETE": lambda **v: i18n.t("cli.said.no_delete", v),
    "NO_PROJECT": lambda **v: i18n.t("cli.said.no_project", v),
    "NAME_ONE": lambda **v: i18n.t("cli.said.name_one", v),
    "NO_TP_REQUEST": lambda **v: i18n.t("cli.said.no_tp_request", v),
    "NO_TRAJ_REQUEST": lambda **v: i18n.t("cli.said.no_traj_request", v),
    "NO_CODES_REQUEST": lambda **v: i18n.t("cli.said.no_codes_request", v),
    "NO_LENGTH_REQUEST": lambda **v: i18n.t("cli.said.no_length_request", v),
    "NO_SETTINGS_REQUEST": lambda **v: i18n.t("cli.said.no_settings_request", v),
    "AI_PROMPT_EMPTY": lambda **v: i18n.t("cli.said.ai_prompt_empty", v),
    "AI_PROMPT_UNREAD": lambda **v: i18n.t("cli.said.ai_prompt_unread", v),
    "AI_PROMPT_ONE": lambda **v: i18n.t("cli.said.ai_prompt_one", v),
    "SETTINGS_NOTHING": lambda **v: i18n.t("cli.said.settings_nothing", v),
    "AI_PROVIDER_UNKNOWN": lambda **v: i18n.t("cli.said.ai_provider_unknown", v),
    "AI_NO_ADDRESS": lambda **v: i18n.t("cli.said.ai_no_address", v),
    "AI_ADDRESS_HTTP": lambda **v: i18n.t("cli.said.ai_address_http", v),
    "AI_DEPLOYMENT_AZURE": lambda **v: i18n.t("cli.said.ai_deployment_azure", v),
    "AI_MODEL_AZURE": lambda **v: i18n.t("cli.said.ai_model_azure", v),
    "AI_MODEL_EMPTY": lambda **v: i18n.t("cli.said.ai_model_empty", v),
    "UID_MADE": lambda **v: i18n.t("cli.said.uid_made", v),
    "NO_WHOSE": lambda **v: i18n.t("cli.said.no_whose", v),
    "NO_SET": lambda **v: i18n.t("cli.said.no_set", v),
    "NO_PROJECT_REQUEST": lambda **v: i18n.t("cli.said.no_project_request", v),
    "NOT_PAIRED": lambda **v: i18n.t("cli.said.not_paired", v),
    "AGENTS_OFF": lambda **v: i18n.t("cli.said.agents_off", v),
    "CANVAS_ALONE": lambda **v: i18n.t("cli.said.canvas_alone", v),
    "DRAFT_ALONE": lambda **v: i18n.t("cli.said.draft_alone", v),
    "TURN_SHAPE": lambda **v: i18n.t("cli.said.turn_shape", v),
    "NOTES_OR_ADD": lambda **v: i18n.t("cli.said.notes_or_add", v),
    "NOT_LONE": lambda **v: i18n.t("cli.said.not_lone", v),
    "PAIRS_SHAPE": lambda **v: i18n.t("cli.said.pairs_shape", v),
    "PAIRS_OR_LISTS": lambda **v: i18n.t("cli.said.pairs_or_lists", v),
    "STALE_WRITE": lambda **v: i18n.t("cli.said.stale_write", v),
    "NOT_THIS_LINE": lambda **v: i18n.t("cli.said.not_this_line", v),
    "KEY_TWICE": lambda **v: i18n.t("cli.said.key_twice", v),
    "NO_TURN_REQUEST": lambda **v: i18n.t("cli.said.no_turn_request", v),
    "EDIT_NEEDS": lambda **v: i18n.t("cli.said.edit_needs", v),
    "WORDS_OR_SPAN": lambda **v: i18n.t("cli.said.words_or_span", v),
    "SPAN_BOTH": lambda **v: i18n.t("cli.said.span_both", v),
    "WORDS_NOT_THERE": lambda **v: i18n.t("cli.said.words_not_there", v),
    "WORDS_TWICE": lambda **v: i18n.t("cli.said.words_twice", v),
    "TRIM_SIDE": lambda **v: i18n.t("cli.said.trim_side", v),
    "ADD_SHAPE": lambda **v: i18n.t("cli.said.add_shape", v),
    "OUTSIDE": lambda **v: i18n.t("cli.said.outside", v),
    "NOT_IN_CASE": lambda **v: i18n.t("cli.said.not_in_case", v),
    "NO_IMPORT_REQUEST": lambda **v: i18n.t("cli.said.no_import_request", v),
    "NOT_A_ROLE": lambda **v: i18n.t("cli.said.not_a_role", v),
    "RAW_TAKES_NONE": lambda **v: i18n.t("cli.said.raw_takes_none", v),
    "NO_COLUMNS": lambda **v: i18n.t("cli.said.no_columns", v),
    "NAME_FOR_RAW": lambda **v: i18n.t("cli.said.name_for_raw", v),
    "NOT_A_TIME_FORMAT": lambda **v: i18n.t("cli.said.not_a_time_format", v),
    "NOT_A_SPEAKER_ROLE": lambda **v: i18n.t("cli.said.not_a_speaker_role", v),
    "SPEAKERS_OR_INTERVIEWER": lambda **v: i18n.t("cli.said.speakers_or_interviewer", v),
    "HEADING_CASE_OR_ALL": lambda **v: i18n.t("cli.said.heading_case_or_all", v),
    "HEADING_NEITHER": lambda **v: i18n.t("cli.said.heading_neither", v),
    "NO_HEADING_REQUEST": lambda **v: i18n.t("cli.said.no_heading_request", v),
    "REPLACE_CASE_OR_ALL": lambda **v: i18n.t("cli.said.replace_case_or_all", v),
    "REPLACE_FIND_OR_PAIRS": lambda **v: i18n.t("cli.said.replace_find_or_pairs", v),
    "NO_REPLACE_REQUEST": lambda **v: i18n.t("cli.said.no_replace_request", v),
    "NO_PAIRS": lambda **v: i18n.t("cli.said.no_pairs", v),
    "PAIRS_UNREAD": lambda **v: i18n.t("cli.said.pairs_unread", v),
    "PAIR_LINE": lambda **v: i18n.t("cli.said.pair_line", v),
    "NO_BATCH_HERE": lambda **v: i18n.t("cli.said.no_batch_here", v),
    "SOURCES_SHAPE": lambda **v: i18n.t("cli.said.sources_shape", v),
    "BOARD_NEEDS_CASE": lambda **v: i18n.t("cli.said.board_needs_case", v),
}


def _w(name: str, **vals) -> str:
    return SAID[name](**vals)


def __getattr__(name: str) -> str:
    """This module's words other modules and the checks name, read in the run's language."""
    if name in SAID:
        return SAID[name]()
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")

HERE = boot.ROOT
GUIDE = boot.resource("docs/agents.md")
SID = re.compile(r"^[Ss](\d+)$")
NOT_PLACED = "Not placed"
# what the bin held is Set aside since 20 October (Adam, way A), the data key `discarded` kept
BIN = themes.SET_ASIDE


def now_iso() -> str:
    """The time of a write, to the microsecond, so a page that saved in the same second before it
    is still told from one that has seen it (see `themes.outside_since`)."""
    return datetime.now().astimezone().isoformat(timespec="microseconds")


# ----------------------------------------------------------------- the project

class Project:
    """The project a command works on: its root, whether it is the demo, its settings and its study."""

    def __init__(self, root: Path, demo: bool):
        self.root = Path(root)
        self.demo = demo
        self.info = routes.read_project(self.root)
        self.books = sorted(routes.gets_books(self.root), key=lambda b: gets_mod.case_order(b["case"]))

    def found(self, name: str) -> list[dict]:
        """The cases of the study a pseudonym names, `Rowan`, `P4 - Alder`, `Alder` or `P4`."""
        said = " ".join(str(name or "").split()).lower()
        return [b for b in self.books if said in (b["case"].lower(), gets_mod.who(b["case"]).lower())
                or b["case"].lower().split(" - ")[0] == said]

    def case(self, name: str) -> dict:
        """A case of the study by its pseudonym, `Rowan`, `P4 - Alder`, `Alder` or `P4`."""
        found = self.found(name)
        if len(found) == 1:
            return found[0]
        names = ", ".join(b["case"] for b in self.books) or "none"
        if not found:
            raise cli.Refused(i18n.t("cli.case.no_participant_called_in_this_project", name=name, names=names))
        raise cli.Refused(i18n.t("cli.case.names_more_than_one_case", name=name, list=', '.join(b['case'] for b in found)))




def open_projects(args) -> tuple[list[Project], list[str]]:
    """The projects a command reads, and the names of those it may not. `--demo` the demo, `--root`
    a run of that one folder, `--project` the project of that name, and with none of them every
    project Idiograph holds, in the order they were added. A project agents may not read is never
    opened, and one named on its own is refused. Never the recent list: a run here never reads or
    writes `state.json`."""
    if getattr(args, "config", None):
        srv.CONFIG_PATH = Path(args.config).expanduser().resolve()
    srv.STATE_MEMORY = {"recent": []}
    named = getattr(args, "project", None)
    if args.demo:
        routes.fill_demo()
        # `--demo` the IPA demo, `--demo ta` the thematic analysis demo (demos, 3 November 2026)
        roots, demo = [srv.demo_dir_of(args.demo)], True
    elif args.root:
        root = Path(args.root).expanduser().resolve()
        srv.ROOT_OVERRIDE = str(root)
        roots, demo = [root], srv.is_demo_root(root)
    else:
        roots, demo = srv.project_roots(), False
        if not roots:
            raise cli.Refused(_w("NO_PROJECT"))
        if named:
            said = " ".join(str(named).split()).lower()
            picked = [r for r in roots if routes.read_project(r)["name"].lower() == said]
            if not picked:
                names = ", ".join(routes.read_project(r)["name"] for r in roots)
                raise cli.Refused(i18n.t("cli.open_projects.no_project_called_the_projects", named=named, names=names))
            roots = picked[:1]
    alone = bool(args.demo or args.root or named or len(roots) == 1)
    if alone and not Path(roots[0]).is_dir():
        raise cli.Refused(i18n.t("cli.open_projects.the_participants_folder_is_not_there"))
    opened, closed = [], []
    for root in roots:
        if not Path(root).is_dir():
            continue
        if not routes.read_project(root)["agents"]["allowed"] and not demo:
            closed.append(routes.read_project(root)["name"])
            continue
        opened.append(Project(root, demo))
    if not opened:
        # the agent log counts the projects agents may not read, never naming one (agent_log.py)
        agent_log.at_closed(len(closed))
        raise cli.Refused(_w("PRIVATE"))
    if len(opened) == 1:
        agent_log.at_project(opened[0].info["name"])
    return opened, closed


def open_project(args) -> Project:
    """The one project a command works on, refused unless agents may read it. With several, the
    first, and `perform` sees to the choice."""
    return open_projects(args)[0][0]


def project_for(projects: list[Project], name: str) -> Project:
    """The project of the case a command names, across every project it reads. A pseudonym two
    projects share is refused in one line asking for `--project`, and one no project has names
    every case there is."""
    holding = [p for p in projects if p.found(name)]
    if len(holding) == 1:
        return holding[0]
    if len(holding) > 1:
        names = " and ".join(p.info["name"] for p in holding)
        raise cli.Refused(i18n.t("cli.project_for.is_a_participant_in", name=name, names=names, name_one=_w("NAME_ONE")))
    names = ". ".join(f"{p.info['name']}: {', '.join(b['case'] for b in p.books) or 'none'}" for p in projects)
    raise cli.Refused(i18n.t("cli.project_for.no_participant_called_in_any_project", name=name, names=names))


TIMEPOINT_HELP = ("in a project of two or more timepoints, the timepoint whose PETs canvas this is, by its "
                  "number, 2, or its label, T2, T1 without it")
LPETS_HELP = ("in a project of two or more timepoints, this participant's LPETs, made from their PETs at each "
              "timepoint, in place of the project's GETs")


@contextlib.contextmanager
def scope_of(p: Project, args):
    """A command on a board at a timepoint, `--timepoint`, or on a participant's LPETs, `--lpets` (21
    October), run there through the server's own scopes, so it reads and writes what the canvas does. The
    project as the command sees it, on LPETs with the participant's timepoints for its study. Every line the
    server's code says through it reads in the words of the project's method (tagaps, 1 November 2026)."""
    root = getattr(p, "root", None)
    with i18n.in_method(routes.method_of(routes.project_file(root)) if root is not None else None):
        with place_of(p, args) as q:
            yield q


@contextlib.contextmanager
def place_of(p: Project, args):
    """A command on a board at a timepoint or on a participant's LPETs, run there (see `scope_of`)."""
    tp = getattr(args, "timepoint", None)
    lpets = getattr(args, "lpets", None)
    if args.command in ("board", "statements") and tp not in (None, ""):
        book = Path(p.case(args.case)["workbook"])
        with themes.scoped(routes.board_timepoint(book, tp)):
            yield p
    elif args.command == "gets" and lpets:
        b = p.case(lpets)
        with routes.lpets_scope(Path(b["workbook"])):
            q = copy.copy(p)
            q.books = routes.gets_books(p.root)
            yield q
    elif args.command == "gets":
        # in a project of two or more timepoints the project's board is its LGETs, made from the LPETs
        with routes.board_scope(p.root):
            yield p
    else:
        yield p


def run_scoped(command, p: Project, args) -> tuple:
    """A command run in its scope as it stands, which the app's Approve of a held action runs (see `holds`)."""
    with scope_of(p, args) as q:
        return command(q, args)


def run_in_scope(command, p: Project, args) -> tuple:
    """A command as an agent asked it, in its scope: one that waits for his yes in the app kept as a hold while
    "Dangerously skip permissions" is off (`holds.gate`, 27 October 2026), every other run at once."""
    agent_log.at_project(p.info["name"])
    with scope_of(p, args) as q:
        return holds.gate(q, args, lambda given: command(q, given))


def case_name(workbook: Path) -> str:
    """The case as the themes file names it, by its pseudonym, the way the server writes it."""
    return routes.case_label(Path(workbook))


def load_board_file(workbook: Path) -> dict | None:
    try:
        return themes.load(workbook)
    except WorkbookError as exc:
        raise cli.Refused(str(exc))


def pick_board(data: dict | None, name: str | None, default: str = "chosen") -> dict:
    """A board of a themes or GETs file by its id or its name, or with none named the Current board,
    else the one on the canvas."""
    boards = themes.boards_of(data)
    if not boards:
        raise cli.Refused(i18n.t("cli.pick_board.there_are_no_boards_yet"))
    if name:
        said = " ".join(str(name).split()).lower()
        for b in boards:
            if str(b.get("id")).lower() == said or " ".join(str(b.get("name") or "").split()).lower() == said:
                return b
        raise cli.Refused(i18n.t("cli.pick_board.no_board_called_the_boards", name=name, list=', '.join(str(b.get('name')) for b in boards)))
    chosen = themes.chosen_of(data) if default == "chosen" else None
    return themes.find_version(data, chosen) if chosen else themes.current_version(data)


# ------------------------------------------------------------------ ids

def ids_of(read: dict) -> tuple[dict, dict]:
    """Each statement's short id by its key, and its key by its short id."""
    sids = themes.short_ids(read["cards"])
    return sids, {v: k for k, v in sids.items()}


def statement_key(name, read: dict, keys: dict) -> str | None:
    """A statement named by its short id, `S12`, or by its key, `Initial:12:0`, as the key, or None."""
    text = str(name or "").strip()
    m = SID.match(text)
    if m:
        return keys.get(f"S{int(m.group(1))}")
    live = {c["key"] for c in read["cards"]}
    return text if text in live else None


def pair(key: str, sids: dict) -> str:
    """A statement as every line names it, its short id and its key together."""
    return f"{sids[key]} {key}" if key in sids else key


# ------------------------------------------------------------------- cases

def cmd_cases(p: Project, args) -> tuple:
    cfg = srv.config()
    try:
        held = gets_mod.load(p.root)
    except WorkbookError:
        held = None
    study = gets_mod.study_of(held, [b["case"] for b in p.books])
    inside = [b for b in p.books if study[b["case"]]["in"]]
    minimum, band = gets_mod.minimum_of(gets_mod.settings_of(held), len(inside))
    people = routes.people_view(p.root)
    rows = []
    for b in p.books:
        book = Path(b["workbook"])
        try:
            data = themes.load(book)
            unread = None
        except WorkbookError as exc:
            data, unread = None, str(exc)
        chosen = themes.chosen_of(data)
        canvas = (themes.current_version(data) or {}).get("id")
        boards = []
        for board in themes.boards_of(data):
            entry = {"id": board.get("id"), "name": board.get("name"), "current": board.get("id") == chosen,
                     "canvas": board.get("id") == canvas}
            for key in themes.AGENT_KEYS:
                mark = themes.agent_mark(board.get(key))
                if mark:
                    entry[key] = mark
            boards.append(entry)
        # in a project of two or more timepoints, each one with its sheets and where it stands
        tps = routes.card_timepoints(book, cfg.get("interviewer") or "") if routes.longitudinal(p.info["timepoints"]) else None
        # their picture, label and pen portrait (pbiobuild), as participant show gives them
        person = routes.person_of(p.root, people, b["case"])
        rows.append({"case": b["case"], "workbook": book.name, "in_study": study[b["case"]]["in"],
                     "label": person["label"], "portrait": person["portrait"], "picture": person["picture"],
                     "values": person.get("values") or {},
                     "statements_complete": rounds_mod.complete_of(book), "pets_complete": themes.complete_of(data),
                     "current": next((x["name"] for x in boards if x["current"]), None), "boards": boards,
                     **({"timepoints": [timepoint_entry(t) for t in tps]} if tps else {}),
                     **({"unread": unread} if unread else {})})
    project = {"name": p.info["name"], "research_question": p.info["research_question"], "demo": p.demo,
               "method": p.info.get("method", "ipa"),
               "gets_minimum": minimum, "smith_band": band, "cases_in_study": len(inside),
               "gets_file": held is not None}
    if routes.longitudinal(p.info["timepoints"]):
        project["timepoints"] = [{"n": t["n"], "label": t["label"], "description": t["description"]}
                                 for t in p.info["timepoints"]]
    whose = i18n.t("cli.said.smiths_band") if band else i18n.t("cli.cases.set_in_settings")
    # a thematic analysis project's lines in its words, with no minimum for its themes and no PETs (taword)
    ta = i18n.method_now() == "ta"
    lines = [f"{project['name']}{i18n.t('cli.said.the_demo') if p.demo else ''}",
             i18n.t("cli.said.research_question", research_question=project['research_question'] or i18n.t("cli.said.none_set_yet")),
             *([i18n.t("cli.said.timepoints", timepoints=timepoints_said(project['timepoints']))] if project.get("timepoints") else []),
             *([] if ta else [i18n.t("cli.cases.a_get_needs_of_the", minimum=minimum, participants=i18n.t("cli.n.participant", n=len(inside)), whose=whose)]), ""]
    for r in rows:
        lines.append(f"{r['case']}{', ' + r['label'] if r['label'] else ''}: {r['workbook']}"
                     f"{'' if r['in_study'] else i18n.t('cli.cases.out_of_the_study')}")
        said = [i18n.t("cli.statements_complete", when=cli.when_said(r["statements_complete"])) if r["statements_complete"]
                else i18n.t("cli.statements_progress")]
        if r.get("timepoints"):
            said = [timepoint_said(t) for t in r["timepoints"]]
        if r["pets_complete"] and not ta:
            said.append(i18n.t("cli.cases.pets_complete_on", name=r['pets_complete']['name']))
        if r.get("unread"):
            said.append(r["unread"])
        lines.append("  " + " ".join(said))
        if r["boards"]:
            parts = []
            for x in r["boards"]:
                marks = [w for w, on in ((i18n.t("cli.said.the_current_board"), x["current"]), (i18n.t("cli.said.on_the_canvas"), x["canvas"]),
                                         (i18n.t("cli.cases.made_in_a_conversation"), "made" in x)) if on]
                parts.append(f"{x['name']} ({x['id']}{', ' + ', '.join(marks) if marks else ''})")
            lines.append(i18n.t("cli.cases.boards") + ", then ".join(parts))
        else:
            lines.append(i18n.t("cli.cases.no_boards_yet"))
    return {"project": project, "cases": rows}, lines


def timepoint_entry(t: dict) -> dict:
    """A participant's timepoint as `cases` answers it: its place, label, description, sheets,
    `state` (none, not interviewed, progress or complete), the passages decided of those there and
    when its statements were marked complete."""
    return {"n": t["n"], "label": t["label"], "description": t["description"], "sheets": t["sheets"],
            "state": t["state"], "done": t["done"], "total": t["total"], "statements_complete": t["complete"]}


def timepoint_said(t: dict) -> str:
    """A participant's timepoint in a line: T2 (Midsummer) on Follow-up, 12 of 40 passages decided."""
    name = f"{t['label']}{' (' + t['description'] + ')' if t['description'] else ''}"
    if t["state"] == "none":
        return i18n.t("cli.timepoint_said.not_interviewed", name=name)
    where = f" on {', '.join(t['sheets'])}"
    if t["state"] == "complete":
        return i18n.t("cli.timepoint_said.statements_marked_complete_on", name=name, where=where, when=cli.when_said(t['statements_complete']))
    return i18n.t("cli.timepoint_said.of_decided", name=name, where=where, done=t['done'], passages=i18n.t("cli.n.passage", n=t['total']))


def timepoints_said(tps: list[dict]) -> str:
    return ", ".join(f"{t['label']}{' (' + t['description'] + ')' if t['description'] else ''}" for t in tps)


# ----------------------------------------------------------------- timepoints



def cmd_timepoints(p: Project, args) -> tuple:
    """The project's timepoints, read, or set from --from as Project settings sets them: a list, each
    a label and a description, or a number. Lowering the number is refused while a timepoint that
    would go holds an interview, naming the participants (see `routes.write_timepoints`)."""
    source = getattr(args, "source", None)
    if source is None:
        tps = p.info["timepoints"]
        lines = [f"{p.info['name']} has {i18n.t('cli.n.timepoint', n=len(tps))}"
                 + (f": {timepoints_said(tps)}." if routes.longitudinal(tps) else i18n.t("cli.timepoints.so_nothing_longitudinal_shows"))]
        return {"timepoints": tps, "longitudinal": routes.longitudinal(tps)}, lines
    if p.demo:
        raise cli.Refused(i18n.t("cli.said.the_demos_project_is_fixed"))
    if not themes_ai.one_line(args.note) and not args.dry_run:
        raise cli.Refused(_w("NO_TP_REQUEST"))
    spec = cli.read_spec(source)
    given = spec.get("timepoints") if isinstance(spec, dict) else spec
    try:
        if args.dry_run:
            done = routes.write_timepoints(p.root, given, dry_run=True)
        else:
            with locks.root(p.root):
                done = routes.write_timepoints(p.root, given, who=hist_mod.asker(asked_by(args)))
    except WorkbookError as exc:
        raise cli.Refused(str(exc), i18n.t("cli.said.nothing_was_written")) from None
    tps = done["project"]["timepoints"]
    head = (i18n.t("cli.said.dry_run_nothing_was_written") if args.dry_run else
            i18n.t("cli.said.saved_in_the_project_file") if done["changes"] else i18n.t("cli.said.nothing_changed"))
    lines = [head] + done["changes"] + [i18n.t("cli.said.timepoints", timepoints=timepoints_said(tps)) if routes.longitudinal(tps)
                                        else i18n.t("cli.timepoints.one_timepoint_so_nothing_longitudinal_shows")]
    return {"timepoints": tps, "changes": done["changes"], "dry_run": bool(args.dry_run)}, lines


# ----------------------------------------------------------------- trajectories



TRAJ_SOURCES = {"lpet": lambda: i18n.t("cli.traj_lines.source_lpet"),
                 "interview": lambda: i18n.t("cli.traj_lines.source_interview"),
                 "transcript": lambda: i18n.t("cli.traj_lines.source_transcript")}


def traj_lines(answer: dict) -> list[str]:
    """The Trajectories board in plain lines: each trajectory with its participants, their LPETs and notes, and
    under each cell the quotes it can take with where each comes from, the ticked one starred (trajchoose)."""
    cards = {c["case"]: c for c in answer["participants"]}

    def card(case: str) -> list[str]:
        c = cards[case]
        out = [f"   {c['who']}" + (f", {c['title']}" if c.get("title") else "")
               + (f" [{', '.join(t['word'] for t in c.get('tags') or [])}]" if c.get("tags") else "")
               + (f": {'; '.join(c['lpets'])}" if c["lpets"] else i18n.t("cli.traj_lines.no_lpets_yet"))]
        for r in c.get("rows") or []:
            if not r.get("shown", True):
                continue
            out.append(f"      {r['id']} {r['title']}" + (f" ({r['domain']})" if r.get("domain") else ""))
            for key, cell in (r.get("cells") or {}).items():
                q = cell.get("quote")
                said = ((f"\"{q['text']}\" {q.get('time') or ''}".strip()
                         + ("" if cell.get("chosen") else " " + i18n.t("cli.traj_lines.first"))
                         + (f" ({TRAJ_SOURCES[q['source']]()})" if q.get("source") in ("interview", "transcript") else ""))
                        if q else i18n.t("cli.traj_lines.no_quote"))
                out.append(f"         {key}: {cell.get('state') or '-'} | {said}")
                ticked = q.get("key") if q and cell.get("chosen") else None
                for ch in cell.get("choices") or []:
                    out.append(i18n.t("cli.traj_lines.choice", mark="*" if ch["key"] == ticked else "-",
                                      source=TRAJ_SOURCES.get(ch.get("source"), TRAJ_SOURCES["lpet"])(),
                                      text=ch["text"], time=ch.get("time") or "", qkey=ch["key"]))
        if c["note"]:
            out.append(i18n.t("cli.traj_lines.why", note=c['note']))
        return out

    lines = [i18n.t("cli.traj_lines.board_note", note=answer["note"])] if answer.get("note") else []
    for col in answer["columns"]:
        lines += [f"{col['title']} ({col['id']}, {i18n.t('cli.n.participant', n=len(col['participants']))})"
                  + (f": {col['description']}" if col.get("description") else "")]
        for case in col["participants"]:
            lines += card(case)
    lines += [i18n.t("cli.traj_lines.not_placed", n_unplaced=len(answer['unplaced']))]
    for case in answer["unplaced"]:
        lines += card(case)
    return lines


def traj_answer(answer: dict) -> dict:
    """The board as the command line gives it, each cell's `choices` every quote it can take: the LPET's own,
    `source` `lpet`, then the participant's other quotes of that interview, `interview`, each with `lpet`, the id
    of the LPET it sits in, None for none (trajchoose, 11 November 2026). A passage of the transcript is taken by
    the `quote` op's `passage`, its turns read with `turn show`. Called on the answer before `traj_lines`."""
    keep = ("note", "columns", "unplaced", "participants", "tags", "updated", "timepoints", "palette", "icons", "faces")
    out = {k: answer[k] for k in keep if k in answer}
    people = []
    for c in out.get("participants") or []:
        quotes = c.get("quotes") or {}
        sits = {ch["key"]: r["id"] for r in c.get("rows") or [] for cell in (r.get("cells") or {}).values()
                for ch in cell.get("choices") or []}
        rows = []
        for r in c.get("rows") or []:
            cells = {}
            for key, cell in (r.get("cells") or {}).items():
                own = [dict(ch, source="lpet") for ch in cell.get("choices") or []]
                taken = {ch["key"] for ch in own}
                others = [dict(q, source="interview", lpet=sits.get(q["key"])) for q in quotes.get(key) or []
                          if q["key"] not in taken]
                cells[key] = dict(cell, choices=own + others)
            rows.append(dict(r, cells=cells))
        people.append(dict({k: v for k, v in c.items() if k != "quotes"}, rows=rows))
    if "participants" in out:
        out["participants"] = people
    return out


def cmd_trajectories_show(p: Project, args) -> tuple:
    """The project's Trajectories board, as the Trajectories tab shows it."""
    try:
        answer = routes.traj_reply(routes.traj_check(p.root), {}, traj_mod.load(p.root))
    except WorkbookError as exc:
        raise cli.Refused(str(exc)) from None
    head = [i18n.t("cli.trajectories_show.trajectories_of", name=p.info['name']) + (i18n.t("cli.n.trajectory", n=len(answer["columns"]))
                                                    if answer["columns"] else i18n.t("cli.trajectories_show.none_named_yet"))]
    out = traj_answer(answer)
    return out, head + traj_lines(out)


def cmd_trajectories_apply(p: Project, args) -> tuple:
    """A change to the Trajectories board with the board's own operations, all or nothing, a dry run
    first: the board's own note, add, rename, move and remove a trajectory, its sentence, colour and icon, place a
    participant or take
    them out, their order, note, label, tags and picture, a tag's colour, an LPET hidden or shown, and on a
    participant's LPETs board an LPET's state, key quote and bold at a timepoint, its domain, and the states
    moved from the LPETs' notes (trajbuild2, 10 November 2026). A key quote is the LPET's own, another statement's
    of that interview by its key, or a passage of any of the participant's interviews (trajchoose, 11 November 2026).
    An LPET's operation is on the board their LPETs come into LGETs from, or the one its `board` names (lpetmarks)."""
    if p.demo:
        raise cli.Refused(i18n.t("cli.said.the_demos_project_is_fixed"))
    if not themes_ai.one_line(args.note) and not args.dry_run:
        raise cli.Refused(_w("NO_TRAJ_REQUEST"))
    spec = cli.read_spec(args.ops)
    ops = spec.get("operations") if isinstance(spec, dict) else spec
    body = {"ops": ops, "dry_run": bool(args.dry_run), "note": themes_ai.one_line(args.note), "tool": args.tool or ""}
    try:
        routes.traj_check(p.root)
        if args.dry_run:
            answer = routes.traj_apply(p.root, body)
        else:
            with locks.root(p.root):
                answer = routes.traj_apply(p.root, body)
    except WorkbookError as exc:
        raise cli.Refused(str(exc), i18n.t("cli.said.nothing_was_written")) from None
    head = (i18n.t("cli.said.dry_run_nothing_was_written") if args.dry_run else
            i18n.t("cli.trajectories_apply.saved_in_the_projects_trajectories_file") if answer["changes"] else i18n.t("cli.said.nothing_changed"))
    out = dict(traj_answer(answer), changes=answer["changes"], dry_run=bool(args.dry_run))
    return out, [head] + answer["changes"] + [""] + traj_lines(out)


# ----------------------------------------------------------------- the code list (codes, 2 November 2026)



def codes_check(p: Project) -> None:
    """A thematic analysis project's alone, and never the demo's."""
    try:
        codes_mod.refuse_unless_ta(p.info.get("method"))
    except WorkbookError as exc:
        raise cli.Refused(str(exc)) from None


def codes_line(c: dict) -> str:
    counts = (f"{i18n.t('cli.n.extract', n=c['extracts'])}, {i18n.t('cli.n.participant', n=c['participants'])}"
              if c["extracts"] else i18n.t("cli.codes_line.no_extracts"))
    return f"{c['name']} ({c['id']}, {counts})"


def codes_lines(view: dict) -> list[str]:
    """The list in plain lines, each code with its counts and its description."""
    lines = []
    for c in view["codes"]:
        lines.append(codes_line(c))
        if c["description"]:
            lines.append(f"   {c['description']}")
    return lines


def codes_answer(view: dict) -> dict:
    keep = ("codes", "total", "participants", "v", "updated", "recent", "undo", "redo")
    return {k: view[k] for k in keep if k in view}


def codes_view(p: Project) -> dict:
    with locks.root(p.root):
        data = codes_mod.ensure(p.root, p.books, themes.now_iso(), tool=cli.TOOL)
    return codes_mod.listing(data, codes_mod.study_rows(p.books))


def cmd_codes_list(p: Project, args) -> tuple:
    """`codes list`: every code of a thematic analysis project's list, by name, with its extracts and participants
    counted and its description, as the Code list tab shows it. A project made before the list has it made first."""
    codes_check(p)
    try:
        view = codes_view(p)
    except WorkbookError as exc:
        raise cli.Refused(str(exc)) from None
    t = view["total"]
    head = (i18n.t("cli.codes_list.code_list_of_from", name=p.info['name'], codes=i18n.t("cli.n.code", n=t['codes']), extracts=i18n.t("cli.n.extract", n=t['extracts']), participants=i18n.t("cli.n.participant", n=t['participants'])))
    # the codes used last, the last one first, as the Coding screen's quick keys take them (quickkeysB)
    recent = [i18n.t("cli.codes_list.used_last", names=", ".join(view["recent"]))] if view.get("recent") else []
    return codes_answer(view), [head] + recent + codes_lines(view)


def cmd_codes_show(p: Project, args) -> tuple:
    """`codes show <code>`: one code, its description and its extracts by participant, each with its sheet, row
    and time, as the Code list tab shows the code open."""
    codes_check(p)
    try:
        view = codes_view(p)
        c = codes_mod.code_of(view, args.code)
    except WorkbookError as exc:
        raise cli.Refused(str(exc)) from None
    lines = [codes_line(c)] + ([i18n.t("cli.codes_show.description", description=c['description'])] if c["description"] else [])
    if not c["extracts"]:
        lines.append(i18n.t("cli.codes_show.no_extract_has_this_code_yet"))
    for by in c["by"]:
        lines.append(f"{by['who']}, {i18n.t('cli.n.extract', n=len(by['extracts']))}:")
        for x in by["extracts"]:
            lines.append(i18n.t("cli.codes_show.row", sheet=x['sheet'], row=x['row'], time=x['time'] or i18n.t("cli.said.no_time"), quote=x['quote']))
    return {"code": c, "v": view["v"]}, lines


def codes_change(p: Project, args, ops: list) -> tuple:
    """A change to the list through the route's own code, all or nothing, a dry run first."""
    codes_check(p)
    if p.demo:
        raise cli.Refused(i18n.t("cli.said.the_demos_project_is_fixed"))
    if not themes_ai.one_line(args.note) and not args.dry_run:
        raise cli.Refused(_w("NO_CODES_REQUEST"))
    body = {"ops": ops, "dry_run": bool(args.dry_run), "note": themes_ai.one_line(args.note), "tool": args.tool or cli.TOOL}
    try:
        answer = routes.codes_apply(p.root, body)
    except WorkbookError as exc:
        raise cli.Refused(str(exc), i18n.t("cli.said.nothing_was_written")) from None
    if answer.get("stale"):
        raise cli.Refused(answer.get("error") or i18n.t("cli.codes_change.the_code_list_changed"), i18n.t("cli.said.nothing_was_written"))
    head = (i18n.t("cli.said.dry_run_nothing_was_written") if args.dry_run else
            i18n.t("cli.said.saved") if answer["changes"] else i18n.t("cli.said.nothing_changed"))
    reach = []
    if answer.get("rows"):
        reach.append((i18n.t("cli.codes_change.it_would_write") if args.dry_run else i18n.t("cli.codes_change.it_wrote")) + i18n.t("cli.codes_change.of_and_every_board", passages=i18n.t("cli.n.passage", n=answer['rows']), list=', '.join(answer.get('participants') or []))
                     + ("" if args.dry_run else i18n.t("cli.codes_change.a_copy_of_each_file_kept")) + ".")
    out = dict(codes_answer(answer), changes=answer["changes"], dry_run=bool(args.dry_run),
               files=answer.get("files") or [], rows=answer.get("rows") or 0,
               participants_changed=answer.get("participants") or [], named=answer.get("named") or {})
    return out, [head] + answer["changes"] + reach


def cmd_codes_new(p: Project, args) -> tuple:
    """`codes new <name>`: a code added to the list, with no extracts yet, its description with --description."""
    return codes_change(p, args, [{"op": "new", "name": args.name, "description": args.description or ""}])


def cmd_codes_rename(p: Project, args) -> tuple:
    """`codes rename <code> <name>`: a code's name changed everywhere, the list, every participant's workbook and
    every board."""
    return codes_change(p, args, [{"op": "rename", "code": args.code, "name": args.name}])


def cmd_codes_describe(p: Project, args) -> tuple:
    """`codes describe <code> <description>`: a code's description, "" clearing it."""
    return codes_change(p, args, [{"op": "describe", "code": args.code, "description": args.description}])


def cmd_codes_merge(p: Project, args) -> tuple:
    """`codes merge <code> --into <other>`: every extract of one code given to the other everywhere, an extract
    that had both keeping one, and the code leaving the list."""
    return codes_change(p, args, [{"op": "merge", "code": args.code, "into": args.into}])


def cmd_codes_delete(p: Project, args) -> tuple:
    """`codes delete <code>`: a code with no extracts taken off the list."""
    return codes_change(p, args, [{"op": "delete", "code": args.code}])


def cmd_codes_extract(p: Project, args) -> tuple:
    """`codes add` and `codes remove`: a code put on an extract of a passage, or taken off it, as the Codes
    screen's Add a code and a chip's x do."""
    codes_check(p)
    if p.demo:
        raise cli.Refused(i18n.t("cli.said.the_demos_project_is_fixed"))
    if not themes_ai.one_line(args.note) and not args.dry_run:
        raise cli.Refused(_w("NO_CODES_REQUEST"))
    b = p.case(args.case)
    try:
        with locks.root(p.root):
            with wb_mod.case_held(Path(b["workbook"])):
                done = codes_mod.extract_change(p.root, p.books, args.act, b["case"], args.sheet, args.row, args.extract,
                                                args.code, themes.now_iso(), dry_run=bool(args.dry_run),
                                                note=themes_ai.one_line(args.note), tool=args.tool or cli.TOOL)
    except WorkbookError as exc:
        raise cli.Refused(str(exc), i18n.t("cli.said.nothing_was_written")) from None
    head = i18n.t("cli.said.dry_run_nothing_was_written") if args.dry_run else i18n.t("cli.said.saved")
    lines = [head] + done["changes"] + [i18n.t("cli.codes_extract.the_passages_codes")] + [
        f"   {x['es'] or i18n.t('cli.codes_extract.no_code')}: {x['kq']}" for x in done["pairs"]]
    return done, lines


def cmd_codes_quick(p: Project, args) -> tuple:
    """`codes apply-last` and `codes in-vivo`: the Coding screen's quick keys, R and 1 to 5, and V (quickkeysB, 9
    November 2026). Words a passage holds become a new extract with the code used last, or with --recent 2 to 5 that
    one of the codes used last, or with a code named by the words themselves, which joins the list."""
    codes_check(p)
    if p.demo:
        raise cli.Refused(i18n.t("cli.said.the_demos_project_is_fixed"))
    if not themes_ai.one_line(args.note) and not args.dry_run:
        raise cli.Refused(_w("NO_CODES_REQUEST"))
    b = p.case(args.case)
    how = "last" if args.act == "apply-last" else "in-vivo"
    try:
        with locks.root(p.root):
            with wb_mod.case_held(Path(b["workbook"])):
                done = codes_mod.quick(p.root, p.books, how, b["case"], args.sheet, args.row, args.words,
                                       themes.now_iso(), n=getattr(args, "recent", 1) or 1, dry_run=bool(args.dry_run),
                                       note=themes_ai.one_line(args.note), tool=args.tool or cli.TOOL)
    except WorkbookError as exc:
        raise cli.Refused(str(exc), i18n.t("cli.said.nothing_was_written")) from None
    head = i18n.t("cli.said.dry_run_nothing_was_written") if args.dry_run else i18n.t("cli.said.saved")
    lines = [head] + done["changes"] + [i18n.t("cli.codes_extract.the_passages_codes")] + [
        f"   {x['es'] or i18n.t('cli.codes_extract.no_code')}: {x['kq']}" for x in done["pairs"]]
    if done.get("recent"):
        lines.append(i18n.t("cli.codes_list.used_last", names=", ".join(done["recent"])))
    return done, lines


def cmd_codes_undo(p: Project, args) -> tuple:
    """`codes undo` and `codes redo`: the list's last change put back, or made again, every file it wrote put back
    whole, refused when one changed since."""
    codes_check(p)
    if p.demo:
        raise cli.Refused(i18n.t("cli.said.the_demos_project_is_fixed"))
    try:
        with locks.root(p.root):
            done = codes_mod.undo(p.root, p.books, themes.now_iso(), redo=args.act == "redo",
                                  dry_run=bool(args.dry_run), tool=args.tool or cli.TOOL)
    except WorkbookError as exc:
        raise cli.Refused(str(exc), i18n.t("cli.said.nothing_was_written")) from None
    head = i18n.t("cli.said.dry_run_nothing_was_written") if args.dry_run else i18n.t("cli.said.saved")
    return dict(codes_answer(done["list"]), changes=done["changes"], dry_run=bool(args.dry_run)), [head] + done["changes"]


# ----------------------------------------------------------------- the statement length





def settings_prompt_given(args):
    """The statements' AI prompt an agent asks to set: its text from `--ai-prompt-file` (or the text an MCP
    call hands over), `DEFAULT_PROMPT` for `--ai-prompt-default`, as Settings' Put the default back fills
    its box and Save keeps it, or None when it asks for neither. An empty text or a file that cannot be
    read is refused in one line and nothing of its words is said."""
    text = getattr(args, "ai_prompt_text", None)
    path = getattr(args, "ai_prompt_file", None)
    reset = bool(getattr(args, "ai_prompt_default", False))
    if reset and (text is not None or path is not None):
        raise cli.Refused(_w("AI_PROMPT_ONE"))
    if reset:
        return prompts.DEFAULT_PROMPT
    if path is not None:
        try:
            text = Path(str(path)).expanduser().read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            raise cli.Refused(_w("AI_PROMPT_UNREAD")) from None
    if text is None:
        return None
    text = str(text).lstrip("\ufeff")
    if not text.strip():
        raise cli.Refused(_w("AI_PROMPT_EMPTY"))
    return text


# ------------------------------------------------- the AI's provider (aipage, 8 November 2026)

# the settings that hold each provider's address, as Settings' Address row keeps them
AI_ADDRESS_KEY = {ai_mod.AZURE: "ai_address", ai_mod.OTHER: "ai_address", ai_mod.LOCAL: "local_url",
                  ai_mod.LMSTUDIO: "lmstudio_url"}


def ai_address_of(cfg: dict, provider: str) -> str:
    """The address a provider's calls go to as the settings hold it, the local ones' usual one when none is set."""
    held = str(cfg.get(AI_ADDRESS_KEY.get(provider, "")) or "").strip()
    if provider == ai_mod.LOCAL:
        return held or ai_mod.LOCAL_URL
    if provider == ai_mod.LMSTUDIO:
        return held if ai_mod.address_ok(held) else ai_mod.LMSTUDIO_URL
    return held


def ai_model_of(cfg: dict, provider: str) -> str:
    """The model a provider is asked as the settings hold it: Anthropic's, Ollama's, Azure's deployment, or an
    OpenAI-style provider's own (Another service's `other_model`, the rest `ai_models`, the preset's own)."""
    if provider == ai_mod.ANTHROPIC:
        return ai_mod.plain_model(cfg.get("model")) or ai_mod.MODEL
    if provider == ai_mod.LOCAL:
        return str(cfg.get("local_model") or "").strip()
    if provider == ai_mod.AZURE:
        return str(cfg.get("ai_deployment") or "").strip()
    return srv.ai_route_fields(cfg, provider)["model"]


def ai_where(provider: str, address: str) -> str:
    """Where the passages go, Settings' line under the Provider list, in the same words."""
    host = ai_mod.host_of(address)
    if provider in (ai_mod.LOCAL, ai_mod.LMSTUDIO):
        local = urllib.parse.urlparse(address).hostname in ai_mod.LOOPBACK if address else True
        return i18n.t("shell.ai.where_local") if local else i18n.t("shell.ai.where_host", host=host)
    if provider == ai_mod.OTHER:
        return i18n.t("shell.ai.where_host", host=host) if host else ""
    return i18n.t(f"shell.ai.where_{provider}")


def settings_ai(cfg: dict) -> tuple:
    """The AI's settings as Settings, AI features shows them: the switch, the provider, its address, Azure's
    deployment, the model and where the passages go. Never a key, and never whether one is stored."""
    provider = cfg.get("ai_provider") if cfg.get("ai_provider") in ai_mod.PROVIDERS else ai_mod.ANTHROPIC
    address = ai_address_of(cfg, provider) if provider in AI_ADDRESS_KEY else ""
    model = ai_model_of(cfg, provider)
    held = {"ai_on": bool(cfg.get("ai_suggest")), "ai_provider": provider, "ai_address": address,
            "ai_deployment": str(cfg.get("ai_deployment") or "").strip() if provider == ai_mod.AZURE else "",
            "ai_model": model, "ai_where": ai_where(provider, address)}
    lines = [i18n.t("cli.settings.ai_on") if held["ai_on"] else i18n.t("cli.settings.ai_off"),
             i18n.t("cli.settings.ai_provider", name=i18n.t(f"page.ai.provider_{provider}"))]
    if provider in AI_ADDRESS_KEY:
        lines.append(i18n.t("cli.settings.ai_address", address=address or i18n.t("cli.settings.ai_none")))
    if provider == ai_mod.AZURE:
        lines.append(i18n.t("cli.settings.ai_deployment", name=held["ai_deployment"] or i18n.t("cli.settings.ai_none")))
    else:
        lines.append(i18n.t("cli.settings.ai_model", model=model or i18n.t("cli.settings.ai_none")))
    if held["ai_where"]:
        lines.append(held["ai_where"])
    return held, lines


def settings_ai_given(args, cfg: dict) -> dict | None:
    """What an agent asks to set of the AI's provider, as the body `/api/settings` takes from Settings' Save, or
    None when it asks for none of it. The address, the deployment and the model are the provider's named with
    --ai-provider, else the one the settings hold. Each is refused in one line, nothing written, where Settings
    has no such row: an address for a provider with none, a deployment but for Azure, a model for Azure, and an
    address that is not https unless on this computer. Never a key: a key is put in Settings alone."""
    provider = getattr(args, "ai_provider", None)
    address = getattr(args, "ai_address", None)
    deployment = getattr(args, "ai_deployment", None)
    model = getattr(args, "ai_model", None)
    if provider is None and address is None and deployment is None and model is None:
        return None
    if provider is not None and provider not in ai_mod.PROVIDERS:
        raise cli.Refused(_w("AI_PROVIDER_UNKNOWN", providers=", ".join(ai_mod.PROVIDERS)))
    target = provider or (cfg.get("ai_provider") if cfg.get("ai_provider") in ai_mod.PROVIDERS else ai_mod.ANTHROPIC)
    body = {"ai_provider": provider} if provider is not None else {}
    if address is not None:
        address = str(address).strip()
        if target not in AI_ADDRESS_KEY:
            raise cli.Refused(_w("AI_NO_ADDRESS", provider=target))
        if target == ai_mod.LOCAL:
            if address and not re.match(r"^https?://[^\s/]+", address):
                raise cli.Refused(_w("AI_ADDRESS_HTTP"))
        elif address and not ai_mod.address_ok(address):
            raise cli.Refused(i18n.t("errors.address_must_be_https"))
        body[AI_ADDRESS_KEY[target]] = address or {ai_mod.LOCAL: ai_mod.LOCAL_URL,
                                                   ai_mod.LMSTUDIO: ai_mod.LMSTUDIO_URL}.get(target, "")
    if deployment is not None:
        if target != ai_mod.AZURE:
            raise cli.Refused(_w("AI_DEPLOYMENT_AZURE"))
        body["ai_deployment"] = str(deployment).strip()
    if model is not None:
        model = str(model).strip()
        if target == ai_mod.AZURE:
            raise cli.Refused(_w("AI_MODEL_AZURE"))
        if target == ai_mod.ANTHROPIC:
            if not model:
                raise cli.Refused(_w("AI_MODEL_EMPTY"))
            body["model"] = model
        elif target == ai_mod.LOCAL:
            body["local_model"] = model
        elif target == ai_mod.OTHER:
            body["other_model"] = model
        else:
            body["ai_models"] = {target: model}
    return body


def settings_prompt_lines(cfg: dict) -> tuple:
    """The statements' AI prompt as it stands, whether it is the default or his own, and its text."""
    now = str(cfg.get("ai_prompt") or "")
    default = not now.strip() or now == prompts.DEFAULT_PROMPT
    line = i18n.t("cli.settings.ai_prompt_default") if default else i18n.t("cli.settings.ai_prompt_own", n=len(now.split()))
    return {"ai_prompt": now if now.strip() else prompts.DEFAULT_PROMPT, "ai_prompt_is_default": default}, line


def cmd_settings(p: Project, args) -> tuple:
    """His own settings an agent reads, or sets as Settings does (31 October 2026): `--your-name`, Your name, the
    name documents carry, the print views' foot and Word's author, the Interviewer's name standing in while it
    is empty, and (4 November 2026) the statements' AI prompt, `--ai-prompt-file` from a text file or
    `--ai-prompt-default` for the default, saved through the app's own `/api/settings`, with --dry-run
    saying what would change. With no option it reads them. The prompt is his, so it is set only with his
    request in --note. And (aipage, 8 November 2026) the AI's provider, its address, Azure's deployment and the
    model, `--ai-provider`, `--ai-address`, `--ai-deployment` and `--ai-model`, as AI features in Settings sets
    them, read with the rest. Never a key."""
    cfg = srv.config()
    carried = routes.researcher_name()
    given = getattr(args, "your_name", None)
    prompt = settings_prompt_given(args)
    ai_body = settings_ai_given(args, cfg)
    if given is None and prompt is None and ai_body is None:
        if getattr(args, "setting", False):
            raise cli.Refused(_w("SETTINGS_NOTHING"))
        mine = " ".join(str(cfg.get("your_name") or "").split())
        held, pline = settings_prompt_lines(cfg)
        ai_held, ai_lines = settings_ai(cfg)
        return ({"your_name": mine, "interviewer": str(cfg.get("interviewer") or ""), "documents_carry": carried, **held,
                 **ai_held},
                [i18n.t("cli.settings.your_name_2", mine=mine or i18n.t("cli.settings.none_so_documents_carry_the_interviewer")),
                 i18n.t("cli.settings.documents_carry", carried=carried or i18n.t("cli.settings.no_name")), pline]
                + ai_lines)
    if not themes_ai.one_line(args.note) and not args.dry_run:
        raise cli.Refused(_w("NO_SETTINGS_REQUEST"))
    body = {}
    if given is not None:
        name = " ".join(str(given).split())[:120]
        body["your_name"] = name
    if prompt is not None:
        body["ai_prompt"] = prompt
    if ai_body is not None:
        body.update(ai_body)
    if not args.dry_run:
        srv.api_settings(body)
        cfg = srv.config()
        carried = routes.researcher_name()
    head = i18n.t("cli.said.dry_run_nothing_was_written") if args.dry_run else i18n.t("cli.settings.saved_in_the_settings")
    out, lines = {"dry_run": bool(args.dry_run)}, [head]
    if given is not None:
        out.update(your_name=name, documents_carry=carried if not args.dry_run else (name or str(cfg.get("interviewer") or "")))
        lines.append(i18n.t("cli.settings.your_name", name=name or i18n.t("cli.settings.none_so_documents_carry_the_interviewer")))
    if prompt is not None:
        if args.dry_run:
            default = prompt == prompts.DEFAULT_PROMPT
            out.update(ai_prompt=prompt, ai_prompt_is_default=default)
            lines.append(i18n.t("cli.settings.ai_prompt_default") if default
                         else i18n.t("cli.settings.ai_prompt_own", n=len(prompt.split())))
        else:
            held, pline = settings_prompt_lines(cfg)
            out.update(held)
            lines.append(pline)
    if ai_body is not None:
        # as it now stands, or with --dry-run as it would, the settings with the body over them
        would = cfg if not args.dry_run else {**cfg, **{k: v for k, v in ai_body.items() if k != "ai_models"},
                                             "ai_models": {**(cfg.get("ai_models") or {}), **ai_body.get("ai_models", {})}}
        ai_held, ai_lines = settings_ai(would)
        out.update(ai_held)
        lines += ai_lines
    return out, lines


def cmd_length(p: Project, args) -> tuple:
    """The project's statement length, the words past which the length nudge speaks, 15 by default,
    read, or set from the number given as Settings, Experiential statements sets it, with --dry-run
    saying what would change (see `routes.write_statement_words`)."""
    given = getattr(args, "words", None)
    if given is None:
        n = p.info.get("statement_words", 15)
        return ({"statement_words": n},
                [i18n.t("cli.length.nudges_a_statement_past", name=p.info['name'], words=i18n.t("cli.n.word", n=n))])
    if p.demo:
        raise cli.Refused(i18n.t("cli.said.the_demos_project_is_fixed"))
    if not themes_ai.one_line(args.note) and not args.dry_run:
        raise cli.Refused(_w("NO_LENGTH_REQUEST"))
    try:
        if args.dry_run:
            done = routes.write_statement_words(p.root, given, dry_run=True)
        else:
            with locks.root(p.root):
                done = routes.write_statement_words(p.root, given, who=hist_mod.asker(asked_by(args)))
    except WorkbookError as exc:
        raise cli.Refused(str(exc), i18n.t("cli.said.nothing_was_written")) from None
    n = done["project"]["statement_words"]
    head = (i18n.t("cli.said.dry_run_nothing_was_written") if args.dry_run else
            i18n.t("cli.said.saved_in_the_project_file") if done["changes"] else i18n.t("cli.said.nothing_changed"))
    lines = [head] + done["changes"] + [i18n.t("cli.length.the_length_nudge_speaks_past", words=i18n.t("cli.n.word", n=n))]
    return {"statement_words": n, "changes": done["changes"], "dry_run": bool(args.dry_run)}, lines


# ------------------------------------------------- send a project, open a sent one

def sent_target(to: str, name: str) -> Path:
    """Where `project send --to` writes: in a folder given, the project's own file name, and a file
    named without `.idiograph` given it."""
    target = Path(str(to or "")).expanduser()
    if target.is_dir():
        return (target / pack_mod.sent_name(name)).resolve()
    if target.suffix.lower() != pack_mod.SUFFIX:
        target = target.with_name(target.name + pack_mod.SUFFIX)
    return target.resolve()


def cmd_project_send(p: Project, args) -> tuple:
    """The whole project as one file, `<Project name>.idiograph`, as Share a copy on its card on Home writes it,
    every file of the folder as it is, nothing in the project changed. A file there already is never
    written over. With --dry-run what it would write."""
    if p.demo:
        raise cli.Refused(i18n.t("cli.project_send.the_demo_ships_with_idiograph_so"))
    if getattr(args, "list", False):
        return send_listed(p)
    if not str(getattr(args, "to", "") or "").strip():
        raise cli.Refused(i18n.t("cli.project_send.say_where_to_write_it_with"))
    target = sent_target(args.to, p.info["name"])
    if target.exists():
        raise cli.Refused(i18n.t("cli.project_send.there_is_a_file_at_already", target=target))
    if not target.parent.is_dir():
        raise cli.Refused(i18n.t("cli.project_send.the_folder_is_not_there_so", parent=target.parent))
    options = dict(participants=getattr(args, "participant", None), leave_out=getattr(args, "leave_out", None),
                   with_kinds=getattr(args, "with_kinds", None), blind=bool(getattr(args, "blind", False)),
                   pets=getattr(args, "pets", None), audio=getattr(args, "audio", None),
                   boards=getattr(args, "boards", None))
    try:
        done = routes.send_project(p.root, None if args.dry_run else target, dry_run=bool(args.dry_run), **options)
    except WorkbookError as exc:
        raise cli.Refused(str(exc)) from None
    answer, lines = send_lines(p, args, target, done)
    if done.get("uid_made"):
        # the project's own id, written at its first send, so a copy coming back is known as its own
        said = (UID_DRY if args.dry_run else _w("UID_MADE"))
        unchanged = i18n.t("cli.send_lines.nothing_in_the_project_changed")
        lines = [said if x == unchanged else x for x in lines]
        if said not in lines:
            lines.append(said)
        answer["uid_made"] = True
    return answer, lines


UID_DRY = "It would give the project file an id of its own, so a copy that comes back can be matched to it."


def cmd_project_export_qdpx(p: Project, args) -> tuple:
    """The project, or the participants named, as a REFI-QDA project (.qdpx) for NVivo, ATLAS.ti, MAXQDA and
    QualCoder, as Export as REFI-QDA on its menu writes it (`routes.qdpx_export`), the recordings in it with
    --recordings. Nothing in the project changes and a file there already is never written over, so it needs
    no request. With --dry-run what it would hold, nothing written."""
    import qdpx_out
    if not args.dry_run and not str(getattr(args, "to", "") or "").strip():
        raise cli.Refused(i18n.t("cli.project_export_qdpx.say_where"))
    target = qdpx_out.target(args.to, p.info["name"]) if str(getattr(args, "to", "") or "").strip() else None
    try:
        done = routes.qdpx_export(p.root, target, getattr(args, "participant", None),
                                  bool(getattr(args, "recordings", False)), dry_run=bool(args.dry_run))
    except WorkbookError as exc:
        raise cli.Refused(str(exc)) from None
    out = {k: done[k] for k in ("file", "method", "participants", "counts", "lines", "dry_run")}
    if not done["dry_run"]:
        out.update(path=done["path"], bytes=done["bytes"])
    return out, done["lines"]


def send_lines(p: Project, args, target: Path, done: dict) -> tuple:
    """`project send`'s answer and its lines, as `cmd_project_send` says them."""
    said = f"{cli.plural(done['files'], 'file')}, {done['size']}"
    answer = {"file": str(target), "files": done["files"], "bytes": done["bytes"], "dry_run": bool(args.dry_run)}
    options = dict(pets=getattr(args, "pets", None), audio=getattr(args, "audio", None))
    if not done.get("chosen"):
        if args.dry_run:
            lines = ["Dry run, nothing was written.", f"It would write {target}, the whole of {p.info['name']}: {said}."]
        else:
            lines = [i18n.t("cli.send_lines.wrote_the_whole_of", target=target, name=p.info['name'], said=said), i18n.t("cli.send_lines.nothing_in_the_project_changed")]
        return answer, lines
    if done.get("whole"):
        # the whole project, less its recordings or with the current boards alone, every folder as it is,
        # so no file is listed by name
        held = len(done["left"].get("audio", []))
        less = "audio" in done["kinds_out"]
        what = f"the whole of {p.info['name']}" + (" without its recordings" if less else "")
        lines = (["Dry run, nothing was written.", f"It would write {target}, {what}: {said}."] if args.dry_run
                 else [i18n.t("cli.send_lines.wrote", target=target, what=what, said=said)])
        lines += boards_lines(done)
        if less:
            lines.append(i18n.t("cli.send_lines.left_out_recordings", files=i18n.t("cli.n.file", n=held)) if held
                         else i18n.t("cli.send_lines.left_out_with_none_in_the_2"))
        for kind, rels in done["left"].items():
            if kind != "audio":
                lines.append(i18n.t("cli.send_lines.left_out", left_said=pack_mod.LEFT_SAID[kind], files=i18n.t("cli.n.file", n=len(rels))))
        if not args.dry_run:
            lines.append(i18n.t("cli.send_lines.nothing_in_the_project_changed"))
        answer.update({k: done[k] for k in ("participants", "kinds_out", "left", "notes", "boards")}, whole=True,
                      board_choice=done.get("board_choice", "all"))
        return answer, lines
    who = ", ".join(done["participants"]) or "no participant"
    if args.dry_run:
        lines = ["Dry run, nothing was written.", f"It would write {target}, {p.info['name']} with {who}: {said}.",
                 "It would hold:"] + [f"  {rel}" for rel in done["listed"]]
    else:
        lines = [i18n.t("cli.send_lines.wrote_with", target=target, name=p.info['name'], who=who, said=said)]
    if options["pets"] or options["audio"]:
        # what goes for each participant, the PETs and recordings chosen one by one
        words = {"pets": "PETs", "audio": "recordings", "notes": i18n.t("cli.send_lines.working_notes"), "source": "Source"}
        for label, kinds in done.get("each", {}).items():
            going = [words[k] for k in kinds]
            lines.append(i18n.t("cli.send_lines.the_statements", label=label) + (", " + ", ".join(going) if going else " alone") + ".")
    lines += boards_lines(done)
    for kind, held in done["left"].items():
        lines.append(i18n.t("cli.send_lines.left_out", left_said=pack_mod.LEFT_SAID[kind], files=i18n.t("cli.n.file", n=len(held))))
        if args.dry_run:
            lines += [f"  {rel}" for rel in held]
    kept_out = [k for k in pack_mod.KINDS if k in done["kinds_out"] and k not in done["left"]]
    if kept_out:
        lines.append(i18n.t("cli.send_lines.left_out_with_none_in_the") + ", ".join(pack_mod.LEFT_SAID[k] for k in kept_out) + ".")
    lines += done["notes"]
    if not args.dry_run:
        lines.append(i18n.t("cli.send_lines.nothing_in_the_project_changed"))
    answer.update({k: done[k] for k in ("participants", "kinds_out", "listed", "left", "notes", "each", "boards")},
                  board_choice=done.get("board_choice", "all"))
    return answer, lines


def board_said(row: dict) -> str:
    """A board file's board in a line: "Rowan's PETs at t2, Board 3 of 5 boards"."""
    at = f" at {row['timepoint']}" if row.get("timepoint") else ""
    whose = f"{row['participant']}'s " if row.get("participant") else ""
    return i18n.t("cli.board_said.of", whose=whose, kind=row['kind'], at=at, board=row['board'], boards=i18n.t("cli.n.board", n=row['of']))


def boards_lines(done: dict) -> list[str]:
    """A send of the current board alone, each board file's board that goes, one line each."""
    if done.get("board_choice") != "current":
        return []
    rows = done.get("boards") or []
    if not rows:
        return [i18n.t("cli.boards_lines.the_current_board_alone_with_no")]
    return [i18n.t("cli.boards_lines.the_current_board_alone")] + [f"  {board_said(r)}." for r in rows]


def send_listed(p: Project) -> tuple:
    """`project send --list`: what Share a copy's card draws itself from, read only, nothing written
    (see `routes.send_list`)."""
    got = routes.send_list(p.root)
    lines = [f"{got['name']}: {i18n.t('cli.n.participant', n=len(got['participants']))}, {got['size']}"
             + (i18n.t("cli.send_listed.recordings", audio_size=got['audio_size']) if got["audio"] else i18n.t("cli.send_listed.no_recordings"))
             + (" GETs." if got["gets"] else "")]
    for row in got["participants"]:
        has = (["PETs"] if row["pets"] else []) + ([f"recordings {row['audio_size']}"] if row["audio"] else [])
        lines.append(f"  {row['label']}: " + (", ".join(has) if has else i18n.t("cli.send_listed.the_statements_alone")) + ".")
        for b in row.get("boards") or []:
            # each board file's count, and the board a send of the current board alone takes
            at = f" at {b['timepoint']}" if b.get("timepoint") else ""
            lines.append(i18n.t("cli.send_listed.current_2", kind=b['kind'], at=at, boards=i18n.t("cli.n.board", n=b['boards']), current=b['current']))
    for b in got.get("gets_boards") or []:
        lines.append(i18n.t("cli.send_listed.current", kind=b['kind'], boards=i18n.t("cli.n.board", n=b['boards']), current=b['current']))
    return got, lines


def settings_said() -> str:
    """The settings file a command that adds a project wrote, named in its answer (26 October): the
    command line run from source writes the repository's own, never the installed app's."""
    return i18n.t("cli.settings_said.added_to_the_projects_in_the", config_path=srv.CONFIG_PATH)


def cmd_project_open_copy(args) -> tuple:
    """A sent project opened as a copy, as Open a shared copy on Home opens one: unpacked into a new
    folder in --into, its own name or with "copy" after it, never over a folder there, then added to
    Idiograph's projects. A file from a newer Idiograph is refused. With --dry-run what it would write."""
    file = Path(str(args.file or "")).expanduser().resolve()
    into = Path(str(args.into or "")).expanduser().resolve()
    try:
        done = routes.open_copy(file, into, dry_run=bool(args.dry_run), from_name=getattr(args, "from_name", "") or "")
    except WorkbookError as exc:
        raise cli.Refused(str(exc)) from None
    said = f"{i18n.t('cli.n.file', n=done['files'])}, {done['size']}"
    if args.dry_run:
        lines = [i18n.t("cli.said.dry_run_nothing_was_written"),
                 i18n.t("cli.project_open_copy.it_would_make_with_and_add", folder=done['folder'], name=done['name'], said=said)]
    else:
        lines = [i18n.t("cli.project_open_copy.opened_as_a_copy_in", name=done['name'], folder=done['folder'], said=said), i18n.t("cli.said.it_is_one_of_idiographs_projects"),
                 settings_said()]
    if done.get("returning"):
        # a copy coming back to one of his projects, whose boards can be added to it instead (26 October)
        lines.append(i18n.t("cli.project_open_copy.it_is_a_copy_of_coming", returning=done['returning']))
    answer = {"folder": done["folder"], "name": done["name"], "files": done["files"], "bytes": done["bytes"],
              "dry_run": bool(args.dry_run)}
    if done.get("returning"):
        answer["returning"] = done["returning"]
    if not args.dry_run:
        answer["project"] = done["project"]
        answer["settings"] = str(srv.CONFIG_PATH)
    return answer, lines


# ------------------------------------------------- a shared copy coming back

KIND_WORDS = {"own": lambda who: i18n.t("cli.kind_words.own", who=who),
              "edited": lambda who: i18n.t("cli.kind_words.edited"), "gone": lambda who: i18n.t("cli.kind_words.gone"),
              "differs": lambda who: i18n.t("cli.kind_words.differs"),
              "missing": lambda who: i18n.t("cli.kind_words.missing")}


def returning_project(projects: list[Project], file: Path) -> Project:
    """The project of those the command reads that a copy coming back belongs to, by its id, else by its
    name, refused in one line when none of them is, or two are, and --project then names one."""
    root = routes.returning_to(file, [p.root for p in projects])
    if root is not None:
        return next(p for p in projects if p.root == root)
    names = " or ".join(p.info["name"] for p in projects)
    raise cli.Refused(i18n.t("cli.returning_project.is_not_a_copy_of_one", name=file.name, names=names, name_one=_w("NAME_ONE")))


def board_in_line(b: dict, who: str, dry: bool) -> list[str]:
    """One board coming in, its counts, then each statement that does not read as the project's, with its
    reason: those linked to the project's statement by their key, in its wording now, and those placed in
    the copy's wording, no longer in the project (copyback, 6 November 2026). Every card is placed as in
    the copy."""
    kinds = ", ".join(f"{n} {KIND_WORDS[k](who)}" for k, n in b["kinds"].items() if n)
    head = (i18n.t("cli.board_in_line.as_of_match_this_projects", from_=b['from'], name=b['name'], matched=b['matched'], statements=i18n.t("cli.n.statement", n=b['statements'])) + (f", {kinds}" if kinds else "") + i18n.t("cli.board_in_line.every_one_placed_as_in_the") + ".")
    lines = [head]
    linked = [s for s in b["not_matched"] if s.get("wording") == "yours"]
    theirs = [s for s in b["not_matched"] if s.get("wording") != "yours"]
    if linked:
        lines.append(i18n.t("cli.board_in_line.linked"))
        lines += ["      " + i18n.t("cli.board_in_line.now_reads", where=s["key"], text=s["text"], now=s.get("now", ""),
                                    reason=s["reason"]) for s in linked]
    if theirs:
        lines.append(i18n.t("cli.board_in_line.copy_wording"))
        lines += [f"      {s['key']} \"{s['text']}\": {s['reason']}" for s in theirs]
    return lines


def boards_asked(args) -> list | None:
    """The boards of a copy coming back asked for, as `routes.boards_chosen` takes them: each --board a name, or
    from MCP a choice of participant, board and timepoint, and each --board-of a participant, a board and, when
    given, a timepoint, the same choice the card's ticks make (copyback2, 8 November 2026)."""
    out = list(getattr(args, "board", None) or [])
    for words in getattr(args, "board_of", None) or []:
        if len(words) not in (2, 3):
            raise cli.Refused(i18n.t("cli.project_boards_in.board_of_words"))
        out.append({"participant": words[0], "board": words[1], "timepoint": words[2] if len(words) == 3 else ""})
    return out or None


def cmd_project_boards_in(projects: list[Project], args) -> tuple:
    """A shared copy coming back: its boards added to the same participants' boards in the project it was
    sent from, each the next board, not current, named whose and when, as `routes.boards_in` adds them.
    With --dry-run what it would add, and each statement it could not match, with nothing written. A board
    that is the sender's own as he sent it is said and left out unless --board names it (copyback2)."""
    file = Path(str(args.file or "")).expanduser().resolve()
    if not file.is_file():
        raise cli.Refused(i18n.t("cli.project_boards_in.that_file_is_not_there"))
    p = projects[0] if len(projects) == 1 else returning_project(projects, file)
    if p.demo:
        raise cli.Refused(i18n.t("cli.said.the_demos_project_is_fixed"))
    # whose copy it is: --from-name, else the name the file carries, its sender's own (6 November 2026)
    try:
        sender = " ".join(str(routes.returned_from(file).get("from") or "").split())
    except WorkbookError as exc:
        raise cli.Refused(str(exc)) from None
    given = " ".join(str(getattr(args, "from_name", "") or "").split())
    who_name = given or sender
    if not args.dry_run and not who_name:
        raise cli.Refused(_w("NO_WHOSE"), i18n.t("cli.project_boards_in.nothing_was_brought_in"))
    if not themes_ai.one_line(args.note) and not args.dry_run:
        raise cli.Refused(_w("NO_REQUEST"))
    try:
        done = routes.boards_in(p.root, file, from_name=who_name, participants=getattr(args, "participant", None),
                                boards=boards_asked(args), dry_run=bool(args.dry_run),
                                request=themes_ai.one_line(args.note))
    except WorkbookError as exc:
        raise cli.Refused(str(exc)) from None
    who = routes.whose(who_name) or i18n.t("cli.project_boards_in.the_other_analysts")
    dry = bool(args.dry_run)
    lines = ([i18n.t("cli.said.dry_run_nothing_was_written")] if dry else [])
    by = (i18n.t("cli.project_boards_in.by_its_name_alone_as_it") if done["matched_by"] == "name" else "")
    lines.append(i18n.t("cli.project_boards_in.is_a_copy_of_coming_back", name=file.name, project=done['project'], by=by, day=routes.day_said(done['sent']))
                 + (i18n.t("cli.project_boards_in.from_idiograph", version=done['version']) if done["version"] else "") + ".")
    if not who_name:
        lines.append(_w("NO_WHOSE"))
    elif not given:
        lines.append(i18n.t("cli.project_boards_in.whose_from_file", name=who_name))
    added = 0
    for row in done["participants"]:
        at = f" at {row['timepoint_label']}" if row.get("timepoint_label") else ""
        n = len(row["boards"])
        added += n
        if n:
            lines.append(f"{row['case']}{at}: " + (i18n.t("cli.project_boards_in.it_would_add") if dry else "added ") + i18n.t("cli.n.board", n=n)
                         + i18n.t("cli.project_boards_in.not_current"))
            for b in row["boards"]:
                lines += board_in_line(b, who, dry)
                if b.get("as_sent"):
                    lines.append(i18n.t("cli.board_in_line.as_sent"))
                if b["statements"] and b.get("copy_words", 0) * 2 > b["statements"]:
                    lines.append(i18n.t("cli.project_boards_in.most_in_copy_wording", from_=b['from']))
        if row["already"]:
            lines.append(i18n.t("cli.project_boards_in.in_the_project_already_so_left", case=row['case'], at=at, list=', '.join(row['already'])))
        if row.get("as_sent"):
            # his own boards as he sent them, untouched in the copy (copyback2, 8 November 2026)
            lines.append(i18n.t("cli.project_boards_in.as_sent_left", case=row['case'], at=at,
                                list=', '.join(b["from"] for b in row["as_sent"])))
    if dry:
        lines.append(i18n.t("cli.project_boards_in.nothing_else_in_the_project_would"))
    else:
        lines.append((i18n.t("cli.project_boards_in.each_ones_history_records_it_as") + file.name + "\". " if added else "")
                     + i18n.t("cli.project_boards_in.the_board_on_the_canvas_and"))
    return done, lines


# ------------------------------------- the project and its participants (26 October)
# The page's own routes for the project, each called here as the page calls it, so the checks, the lock,
# the files written and the refusals are the route's: Settings' save (`routes.api_project`), New project
# (`routes.api_new_project`), Rename on a participant's menu (`routes.api_rename`) and Mark complete on the
# statements screen (`routes.api_complete`). Each write takes his request and a dry run.



def project_body(p: Project) -> dict:
    """The project as the page names it to its routes, by its id."""
    return {"root": routes.project_id(p.root) if p.demo else str(p.root)}


def asked_by(args) -> dict:
    """Who asks, as the project's History keeps it (projhistory, 2 November 2026): the agent's tool, "approved in
    the app" or "without asking" with it where a hold applies, and his request."""
    return {"tool": themes_ai.one_line(getattr(args, "tool", "")) or cli.TOOL,
            "request": themes_ai.one_line(getattr(args, "note", ""))}


def history_line(h: dict) -> str:
    """One record of the project's History as a line: when, who, and his request when an agent asked."""
    when = cli.when_said(h.get("when"))
    if h.get("by") == "agent":
        who = i18n.t("cli.project_history.by_agent", tool=h.get("tool") or cli.TOOL)
        if h.get("request"):
            who += i18n.t("cli.project_history.asked", request=h["request"])
    elif h.get("by") == "member":
        who = i18n.t("cli.project_history.by_member", member=h.get("member") or "", by=h.get("accepted_by") or "")
    else:
        who = i18n.t("cli.project_history.by_app")
    return f"{when}, {who}"


def cmd_project_history(p: Project, args) -> tuple:
    """The project's own History (projhistory, 2 November 2026), newest first: each change to the project's
    settings, its timepoints, its statement length, the study's GETs settings, or a participant renamed or
    their statements marked complete or reopened, with when, who asked, his request and what changed from what
    to what (see `project_history`). It reads and writes nothing else."""
    shown, total = hist_mod.newest(p.root, getattr(args, "limit", None))
    if not total:
        return {"history": [], "total": 0}, [i18n.t("cli.project_history.none_yet", name=p.info["name"])]
    lines = [i18n.t("cli.project_history.head", name=p.info["name"], changes=i18n.t("cli.n.change", n=total))]
    for h in shown:
        lines.append(history_line(h))
        lines += [f"  {c}" for c in h.get("changes") or []]
    return {"history": shown, "total": total}, lines


def cmd_agents_log(args) -> tuple:
    """The agent log (agentlog, 3 November 2026, see agent_log.py), newest first, read alone through the family's
    reader (`cli.agents_log`, every app's since siftlog the same day), given the names of the projects agents may
    read now, so a refusal naming another, or none it could, comes back only in the count `closed`."""
    kept = (srv.CONFIG_PATH, srv.STATE_MEMORY)
    try:
        if getattr(args, "config", None):
            srv.CONFIG_PATH = Path(args.config).expanduser().resolve()
        srv.STATE_MEMORY = {"recent": []}
        roots = [r for r in srv.project_roots() if Path(r).is_dir()]
        roots += [r for r in (srv.DEMO_DIR, srv.demo_ta_dir()) if r.is_dir()]
        allowed = {routes.read_project(r)["name"] for r in roots
                   if srv.is_demo_root(r) or routes.read_project(r)["agents"]["allowed"]}
    finally:
        srv.CONFIG_PATH, srv.STATE_MEMORY = kept
    return cli.agents_log(args, allowed)


def cmd_project_set(p: Project, args) -> tuple:
    """The project's name, its research question, how the exports label its PETs and how its timecodes are
    written, saved as Project settings saves them (`routes.api_project`), each left out kept as it is,
    with --dry-run saying what would change and writing nothing."""
    name, question, labels, form = (getattr(args, k, None) for k in ("name", "question", "pet_labels", "timecodes"))
    method = getattr(args, "method", None)
    if name is None and question is None and labels is None and form is None and method is None:
        raise cli.Refused(_w("NO_SET"))
    if not themes_ai.one_line(args.note) and not args.dry_run:
        raise cli.Refused(_w("NO_PROJECT_REQUEST"))
    body = dict(project_body(p), dry_run=bool(args.dry_run), **asked_by(args))
    if method is not None:
        # the method is fixed once the project is made (tadraw): its own changes nothing, another is refused
        body["method"] = method
    if name is not None or question is not None:
        # the page sends both, so the one not given goes as the project file holds it
        held = routes.project_file(p.root)
        body["name"] = str(held.get("name") or "") if name is None else name
        body["research_question"] = str(held.get("research_question") or "") if question is None else question
    if labels is not None:
        body["pet_labels"] = labels
    if form is not None:
        body["timecodes"] = form
    try:
        done = routes.api_project(body)
    except (WorkbookError, srv.OutsideRoot) as exc:
        raise cli.Refused(str(exc)) from None
    got = done["project"]
    # the method alone, the project's own, changes nothing and the route answers no changes (tadraw)
    done.setdefault("changes", [])
    head = (i18n.t("cli.said.dry_run_nothing_was_written") if args.dry_run else
            i18n.t("cli.said.saved_in_the_project_file") if done["changes"] else i18n.t("cli.said.nothing_changed"))
    lines = [head] + done["changes"] + [i18n.t("cli.project_set.name", name=got['name']),
                                        i18n.t("cli.said.research_question", research_question=got['research_question'] or i18n.t("cli.said.none_set_yet")),
                                        i18n.t("cli.said.pet_labels", pet_labels=got['pet_labels']), i18n.t("cli.said.timecodes", timecodes=got['timecodes'])]
    answer = {"project": {k: got[k] for k in ("name", "research_question", "pet_labels", "timecodes")},
              "changes": done["changes"], "dry_run": bool(args.dry_run)}
    return answer, lines


def cmd_project_remove(p: Project, args) -> tuple:
    """`project remove`: the project taken out of Idiograph's list, as Remove from Idiograph on its menu takes it
    (removetrash, 10 November 2026), its folder and every file in it left as they are, or with --trash moved to the
    system's Trash first, never deleted, once nothing refuses it (`srv.trash_guard`). With --trash it waits for his
    yes in the app (`holds.HELD`) unless Dangerously skip permissions is ticked. The dry run names the folder and
    moves nothing. The demo stays, and a run of one project, --root, removes none."""
    if p.demo:
        raise cli.Refused(i18n.t("server.demo_stays_nothing_removed"))
    trash = bool(getattr(args, "trash", False))
    if not themes_ai.one_line(args.note) and not args.dry_run:
        raise cli.Refused(_w("NO_PROJECT_REQUEST"))
    who = asked_by(args)
    by = who["tool"] + (f": {who['request']}" if who["request"] else "")
    try:
        done = routes.remove_project(str(p.root), trash=trash, dry_run=bool(args.dry_run), by=by)
    except (WorkbookError, srv.OutsideRoot) as exc:
        raise cli.Refused(str(exc)) from None
    name, folder = done["name"], done["folder"]
    if args.dry_run:
        lines = [i18n.t("cli.said.dry_run_nothing_was_written"),
                 i18n.t("cli.project_remove.would_trash", name=name, where=done["where"], folder=folder) if trash
                 else i18n.t("cli.project_remove.would_keep", name=name, folder=folder)]
    else:
        lines = [i18n.t("cli.project_remove.trashed", name=name, where=done["where"], folder=folder) if trash
                 else i18n.t("cli.project_remove.kept", name=name, folder=folder)]
    answer = {"name": name, "folder": folder, "trash": trash, "removed": bool(done.get("removed")),
              "dry_run": bool(args.dry_run)}
    if trash:
        answer["where"] = done["where"]
    return answer, lines


def cmd_project_show(p: Project, _args) -> tuple:
    """The project's settings as Project settings shows them (tadraw, 31 October 2026, for the method): its name,
    its research question, its method, IPA or thematic analysis, fixed when it was made, how the exports label its
    PETs, how its timecodes are written, its timepoints and its statement length. It reads and writes nothing."""
    got = routes.api_project(project_body(p))["project"]
    keys = ("name", "research_question", "method", "pet_labels", "timecodes", "statement_words", "demo")
    answer = {k: got[k] for k in keys}
    answer["timepoints"] = [{"n": t["n"], "label": t["label"], "description": t["description"]} for t in got["timepoints"]]
    ta = got["method"] == "ta"
    lines = [f"{got['name']}{i18n.t('cli.said.the_demo') if got['demo'] else ''}",
             i18n.t("cli.said.research_question", research_question=got['research_question'] or i18n.t("cli.said.none_set_yet")),
             i18n.t("cli.project_show.method_fixed_when_the_project_was", method_name=routes.method_name(got['method'])),
             *([] if ta else [i18n.t("cli.said.pet_labels", pet_labels=got['pet_labels'])]), i18n.t("cli.said.timecodes", timecodes=got['timecodes']),
             *([i18n.t("cli.said.timepoints", timepoints=timepoints_said(answer['timepoints']))] if routes.longitudinal(got["timepoints"]) else []),
             i18n.t("cli.statement_length", n=got["statement_words"])]
    return {"project": answer}, lines


def team_lines(view: dict) -> list[str]:
    """Working together as Project settings shows it, a line each."""
    if not view.get("on"):
        return [i18n.t("team.cli.off")]
    route = (i18n.t("team.cli.route_relay") if view["route"] == "relay"
             else i18n.t("team.cli.route_folder", folder=view["folder"] or i18n.t("team.page.no_folder")))
    lines = [i18n.t("team.cli.on", route=route)]
    if view.get("folder_state") == "missing":
        lines.append("  " + i18n.t("team.page.folder_missing"))
    elif view.get("folder_state") == "unopened":
        lines.append("  " + i18n.t("team.page.folder_unopened", n=view.get("unopened") or 0))
    if view.get("needs_code"):
        lines.append("  " + i18n.t("team.cli.needs_code"))
    names = {p["id"]: p["name"] for p in view["people"]}
    for p in view["people"]:
        roles = [i18n.t("team.cli.lead")] if p["lead"] else []
        roles += [i18n.t("team.page.computers", n=p["computers"])] + ([i18n.t("team.cli.you")] if p["you"] else [])
        lines.append("  " + i18n.t("team.cli.person", name=p["name"], roles=", ".join(roles)))
        for d in p.get("devices") or []:
            said = d.get("name") or i18n.t("team.page.a_computer")
            lines.append("    " + (i18n.t("team.cli.this_computer", computer=said, id=d.get("id") or "") if d.get("this")
                                   else i18n.t("team.cli.computer", computer=said, id=d.get("id") or "")))
    for row in view["participants"]:
        lines.append("  " + i18n.t("team.cli.owner", participant=row["label"], name=names.get(row["owner"], "")))
    lines.append("  " + i18n.t("team.cli.gets_owner", name=names.get(view["gets_owner"], "")))
    lines.append(i18n.t("team.cli.recordings_on") if view["recordings"] else i18n.t("team.cli.recordings_off"))
    lines += [i18n.t("team.cli.asked", computer=a.get("name") or "") for a in view.get("asked") or []]
    if view.get("removed"):
        lines.append(i18n.t("team.cli.removed"))
    return lines


def team_call(p: Project, args, body: dict) -> dict:
    """One of Working together's ops through the route the app calls (`routes.api_team`), refused as it refuses."""
    try:
        return routes.api_team(dict(project_body(p), **body))
    except (WorkbookError, srv.OutsideRoot) as exc:
        raise cli.Refused(str(exc)) from None


def team_writes(p: Project, args, body: dict, needs_note: bool = True) -> tuple:
    """A team op that writes: his request asked for unless a dry run, or `needs_note` false for Send now, which
    writes no History line to name it in, the answer's changes said, then the section."""
    if needs_note and not themes_ai.one_line(args.note) and not args.dry_run:
        raise cli.Refused(_w("NO_PROJECT_REQUEST"))
    done = team_call(p, args, dict(body, dry_run=bool(args.dry_run), **asked_by(args)))
    changes = done.get("changes") or []
    head = (i18n.t("cli.said.dry_run_nothing_was_written") if args.dry_run else
            i18n.t("cli.said.saved_in_the_project_file") if changes else i18n.t("cli.said.nothing_changed"))
    answer = {k: v for k, v in done.items() if k not in ("team",)}
    answer["team"] = done.get("team") or {}
    return answer, [head] + changes, done


def cmd_team_show(p: Project, _args) -> tuple:
    """Working together as Project settings shows it: off, or the route, the people, who works on each participant
    and on the GETs board, and whether recordings go. It reads and writes nothing, and off it reads team.json alone."""
    view = team_call(p, _args, {"op": "show"})["team"]
    return {"team": view}, team_lines(view)


def cmd_team_on(p: Project, args) -> tuple:
    """Working together turned on, or with --off turned off, as the tick in Project settings does. The first time it
    makes this computer's keys and the team, with him as its lead under --name."""
    if getattr(args, "agent_relay", False):
        # an operator code is his, never an agent's (relaywire, 9 November 2026)
        raise cli.Refused(i18n.t("team.cli.agent_relay"))
    if args.off:
        answer, lines, done = team_writes(p, args, {"op": "off"})
    else:
        body = {"op": "on", "name": args.name or "", "route": args.route, "folder": args.folder or ""}
        if getattr(args, "relay_url", None):
            body["relay_url"] = args.relay_url
        answer, lines, done = team_writes(p, args, dict(body, **relay_code(args)))
    return answer, lines + ([] if args.dry_run else team_lines(done["team"]))


def relay_code(args) -> dict:
    """The relay code read from the standard input with --code-stdin, its first line, never an argument, so it is
    in no shell history and no log: `{"code": ...}`, or nothing without --code-stdin."""
    if not getattr(args, "code_stdin", False):
        return {}
    import sys
    return {"code": sys.stdin.readline().strip()}


def cmd_team_set(p: Project, args) -> tuple:
    """The route, the shared folder, whether recordings go, and, by the lead, who works on each participant and on
    the GETs board, each left out kept as it is."""
    body = {"op": "set"}
    if args.route:
        body["route"] = args.route
    if args.folder is not None:
        body["folder"] = args.folder
    if args.recordings:
        body["recordings"] = args.recordings == "on"
    if args.owner:
        body["owners"] = dict(pair.split("=", 1) for pair in args.owner if "=" in pair)
    if args.gets_owner:
        body["gets_owner"] = args.gets_owner
    body.update(relay_code(args))
    if len(body) == 1:
        raise cli.Refused(i18n.t("team.cli.no_ask"))
    answer, lines, done = team_writes(p, args, body)
    return answer, lines + ([] if args.dry_run else team_lines(done["team"]))


def cmd_team_invite(p: Project, args) -> tuple:
    """An invite, its link and its twelve words, for someone new, or with --own for another computer of his. It works
    once, for seven days. `team answers` says when someone has answered, with the six digits to read on a call."""
    answer, lines, done = team_writes(p, args, {"op": "invite", "own": bool(args.own)})
    if not args.dry_run:
        lines += [i18n.t("team.cli.invite_made", expires=cli.when_said(done["expires"])),
                  i18n.t("team.cli.invite_link", link=done["link"]), i18n.t("team.cli.invite_words", words=done["words"])]
    return answer, lines


def cmd_team_answers(p: Project, args) -> tuple:
    """Whether an invite has been answered, and when it has the joiner's name and the six digits. It writes nothing."""
    done = team_call(p, args, {"op": "answers", "invite": args.invite})
    line = (i18n.t("team.cli.answered", name=done["name"], code=done["code"]) if done.get("answered")
            else i18n.t("team.cli.not_answered"))
    return done, [line]


def cmd_team_admit(p: Project, args) -> tuple:
    """They match: the one who answered the invite joins, the project key sealed to his computer. --differ throws his
    answer away."""
    answer, lines, _done = team_writes(p, args, {"op": "admit", "invite": args.invite, "match": not args.differ})
    return answer, lines


def cmd_team_join(p: Project, args) -> tuple:
    """This project joins another's team from its invite, the link or the twelve words, under --name: the six digits
    to read to the lead on a call, then `team joined` once the lead says they match."""
    asked = {"op": "join", "words": args.words, "name": args.name or ""}
    if getattr(args, "relay_url", None):
        asked["relay_url"] = args.relay_url
    answer, lines, done = team_writes(p, args, asked)
    if not args.dry_run:
        lines.append(i18n.t("team.cli.join_code", code=done["code"], name=done.get("from") or "",
                            invite=done["invite"]))
    return answer, lines


def cmd_team_joined(p: Project, args) -> tuple:
    """The lead's They match taken in, once it has come: the team, its people and the project key on this computer."""
    answer, lines, done = team_writes(p, args, {"op": "joined", "invite": args.invite})
    lines.append(i18n.t("team.cli.joined") if done.get("joined") else i18n.t("team.cli.not_joined"))
    return answer, lines


def team_what(done: list, view: dict) -> str:
    """The participants and the GETs board a send or an arrival names, by their labels, in one line."""
    labels = {row["folder"]: row["label"] for row in view.get("participants") or []}
    return ", ".join(i18n.t("team.cli.gets_board") if w == "gets" else labels.get(w, w) for w in done)


def cmd_team_send(p: Project, args) -> tuple:
    """Send now: what came for the project taken in, and every change of his to a participant he works on, or to the
    GETs board when it is his, sent at once, not a minute after his last save. With --dry-run what would go. --note
    is not asked for, since Send now writes no line in History (smokefix, 9 November 2026), and is kept when given."""
    answer, lines, done = team_writes(p, args, {"op": "send"}, needs_note=False)
    view = done.get("team") or {}
    if args.dry_run:
        due = done.get("due") or []
        lines.append(i18n.t("team.cli.would_send", what=team_what(due, view)) if due else i18n.t("team.cli.nothing_sent"))
        return answer, lines
    lines = []
    if done.get("applied"):
        lines.append(i18n.t("team.cli.came_in", what=team_what(done["applied"], view)))
    lines.append(i18n.t("team.cli.sent", what=team_what(done["sent"], view)) if done.get("sent")
                 else i18n.t("team.cli.nothing_sent"))
    if done.get("offline") and done.get("waiting"):
        lines.append(i18n.t("team.cli.waiting", n=done["waiting"]))
    return answer, lines


def cmd_team_remove(p: Project, args) -> tuple:
    """The lead removes someone: their computers off the list and a new project key for everyone left. What they
    already have stays on their computer. With --computer, one computer, a lost one, by its id: the lead's any
    member's, a member's another of his own, asked of the lead's Idiograph (wtdevices, 9 November 2026)."""
    if not args.member and not args.computer:
        raise cli.Refused(i18n.t("team.cli.no_remove"))
    body = {"op": "remove", "computer": args.computer} if args.computer else {"op": "remove", "member": args.member}
    answer, lines, _done = team_writes(p, args, body)
    return answer, lines


def cmd_team_lead(p: Project, args) -> tuple:
    """Make lead: the lead hands the list of people to another member, who from then on adds and removes people."""
    answer, lines, done = team_writes(p, args, {"op": "lead", "member": args.member})
    return answer, lines + ([] if args.dry_run else team_lines(done["team"]))


def cmd_team_take(p: Project, args) -> tuple:
    """What has come for the list of people taken in: a newer list from the lead, and on the lead's computer a
    member's own computer added or removed, as Project settings does when it opens."""
    answer, lines, done = team_writes(p, args, {"op": "take"})
    return answer, lines + ([] if args.dry_run else team_lines(done["team"]))


def board_call(p: Project, body: dict) -> dict:
    """One of a reviewer's board's ops through the route the PETs screen calls (`routes.api_team_board`, wtboard)."""
    try:
        return routes.api_team_board(dict(project_body(p), **body))
    except (WorkbookError, srv.OutsideRoot) as exc:
        raise cli.Refused(str(exc)) from None


def board_writes(p: Project, args, body: dict) -> tuple:
    """A board op that writes: his request asked for unless a dry run, then the answer's changes said."""
    if not themes_ai.one_line(args.note) and not args.dry_run:
        raise cli.Refused(_w("NO_PROJECT_REQUEST"))
    done = board_call(p, dict(body, dry_run=bool(args.dry_run), **asked_by(args)))
    changes = done.get("changes") or []
    head = (i18n.t("cli.said.dry_run_nothing_was_written") if args.dry_run else
            i18n.t("cli.said.saved_in_the_project_file") if changes else i18n.t("cli.said.nothing_changed"))
    answer = {k: v for k, v in done.items() if k != "state"}
    return answer, [head] + changes, done


def cmd_team_board_send(p: Project, args) -> tuple:
    """His own board of a participant someone else works on, sent to them sealed, as Send board in the board's menu
    sends it (wtboard, 9 November 2026). It waits on their computer until they add it as the participant's next board,
    never current, or decline it. The board on the canvas unless --board names another."""
    body = {"op": "send", "case": args.case, "board": args.board or None, "timepoint": getattr(args, "timepoint", None)}
    answer, lines, done = board_writes(p, args, body)
    if not args.dry_run:
        lines.append(i18n.t("team_board.cli.sent", name=done.get("to") or ""))
    return answer, lines


def cmd_team_board_take(p: Project, args) -> tuple:
    """What has come since the last time: each board a teammate sent of a participant of his, kept waiting for his
    answer with nothing written to the participant, and each answer to a board he sent (wtreview2, 9 November 2026)."""
    answer, lines, done = board_writes(p, args, {"op": "take"})
    if done.get("board", {}).get("on") is False:
        return answer, [i18n.t("team.cli.off")]
    for c in done.get("came") or []:
        lines.append(i18n.t("team_board.cli.came", participant=c["participant"], name=c.get("from_name") or ""))
    if not done.get("came") and not done.get("answers"):
        lines.append(i18n.t("team_board.cli.none"))
    return answer, lines


def cmd_team_board_answer(p: Project, args) -> tuple:
    """Add as next board of a board a teammate sent and that waits, --decline writing nothing, and either goes back
    to them, with --reason when given. The board by the ref `team boards` lists, or by its participant when one board
    of it waits."""
    body = {"op": "answer", "ref": args.ref or "", "accept": not args.decline, "reason": args.reason or ""}
    if not args.ref:
        if not args.case:
            raise cli.Refused(i18n.t("team_board.refused.no_such"))
        body.update(workbook=str(p.case(args.case)["workbook"]))
    answer, lines, _done = board_writes(p, args, body)
    return answer, lines


def cmd_team_boards(p: Project, args) -> tuple:
    """The boards he has sent and the boards come in, each with its answer, and with a participant whether his board of
    it can go and to whom. It reads and writes nothing."""
    body = {"op": "show"}
    if getattr(args, "case", None):
        body["case"] = args.case
    view = board_call(p, body)["board"]
    if not view.get("on"):
        return {"board": view}, [i18n.t("team.cli.off")]
    said = {"": i18n.t("team_board.cli.waiting"), "accepted": i18n.t("team_board.cli.accepted"),
            "declined": i18n.t("team_board.cli.declined")}
    lines = [i18n.t("team_board.cli.sent_line", board=x.get("name") or "", participant=x.get("participant") or "",
                    name=x.get("to_name") or "", answer=said.get(x.get("answer") or "", "")) for x in view["sent"]]
    lines += [i18n.t("team_board.cli.came_line", name=x.get("name") or x.get("sent_name") or "",
                     participant=x.get("participant") or "",
                     from_name=x.get("from_name") or "", answer=said.get(x.get("answer") or "", ""))
              + f" ({x.get('ref')})" for x in view["came"]]
    return {"board": view}, lines or [i18n.t("team_board.cli.no_boards")]


def cmd_project_new(args) -> tuple:
    """A new project, as New project on Home makes one (`routes.api_new_project`): a folder of his made a
    project with its name and research question, each transcript given made a participant at the folder's
    next free number, `P<n> - Pseudonym`, its raw source and its workbook, and the folder added to
    Idiograph's projects. Each speaker's role is the card's guess, or as --speakers gives them. Every
    check is the card's, and a failure on the way takes away what it wrote. With --dry-run what it
    would make, and nothing written."""
    files, names = list(getattr(args, "transcript", None) or []), list(getattr(args, "pseudonym", None) or [])
    interviews = list(getattr(args, "interview", None) or [])
    if files and len(names) != len(files):
        raise cli.Refused(_w("NOT_PAIRED"))
    if not themes_ai.one_line(args.note) and not args.dry_run:
        raise cli.Refused(_w("NO_PROJECT_REQUEST"))
    given = speakers_given(getattr(args, "speakers", None))
    sheets, columns = list(getattr(args, "sheet", None) or []), list(getattr(args, "columns", None) or [])
    entries = []
    try:
        items = []
        for i, file in enumerate(files):
            path = Path(str(file)).expanduser().resolve()
            if not path.is_file():
                raise cli.Refused(i18n.t("cli.project_new.is_not_there_so_nothing_was", name=path.name))
            # the same reader Add transcripts' entries go through: the card's read of the file, for the sheet, the
            # columns, the speakers' roles and the interview's name it guesses
            items.append({"file": str(path), "pseudonym": names[i], "interview": interviews[i] if i < len(interviews) else "",
                          "sheet": sheets[i] if i < len(sheets) else "",
                          "columns": (columns[i] or None) if i < len(columns) else None,
                          **({"speakers": dict(given)} if given else {})})
        entries = [{k: v for k, v in row.items() if k not in ("number", "timepoint")}
                   for row in (read_entries(Path.cwd(), items) if items else [])]
        done = routes.api_new_project({"op": "make", "folder": str(args.folder or ""), "name": args.name or "",
                                       "research_question": args.question or "", "files": entries,
                                       "method": getattr(args, "method", None) or "",
                                       "dry_run": bool(args.dry_run)})
    except (WorkbookError, srv.OutsideRoot) as exc:
        raise cli.Refused(str(exc)) from None
    if args.dry_run:
        lines = [i18n.t("cli.said.dry_run_nothing_was_written"),
                 i18n.t("cli.project_new.it_would_make_in_research_question", name=done['name'], folder=done['folder'], research_question=done['research_question'] or i18n.t("cli.said.none_set_yet"), method_name=routes.method_name(done['method']))]
        for case in done["cases"]:
            for one in case["interviews"]:
                roles = ", ".join(f"{who} ({convert_mod.SPEAKER_ROLES.get(role, role)})" for who, role in one["speakers"].items())
                lines.append(i18n.t("cli.project_new.as_from", label=case['label'], file=one['file'], interview=one['interview'], roles=roles))
                if one.get("sheet"):
                    lines.append("  " + i18n.t("cli.import.sheet_read", sheet=one["sheet"]))
                lines += ["  " + line for line in routes.quote_lines(one.get("quotes"))]
        answer = {"folder": done["folder"], "name": done["name"], "research_question": done["research_question"],
                  "method": done["method"],
                  "cases": [{"label": c["label"], "interviews": c["interviews"]} for c in done["cases"]], "dry_run": True}
        return answer, lines
    got = done["project"]
    lines = [i18n.t("cli.project_new.made_in_with", name=got['name'], root=got['root'], participants=i18n.t("cli.n.participant", n=len(done['cases'])), list=', '.join(done['cases'])), i18n.t("cli.project_new.its_method_fixed_now_it_is", method_name=routes.method_name(got['method'])),
             i18n.t("cli.said.it_is_one_of_idiographs_projects"), settings_said(), _w("AGENTS_OFF")]
    return {"project": {k: got[k] for k in ("name", "research_question", "method", "root", "id")}, "cases": done["cases"],
            "settings": str(srv.CONFIG_PATH), "dry_run": False}, lines


def cmd_participant_rename(p: Project, args) -> tuple:
    """A participant renamed as Rename on their menu on the project's page renames them
    (`routes.api_rename`): their name on the passages of each sheet, their PETs boards, every file at the
    project's root that names them (`case_files.PROJECT`: the GETs, the LGETs, the Trajectories board, the
    list of names to replace and the project's file), and with --folder their folder and the files named
    after them too, their LPETs and their picture on Trajectories among them, a copy of each file changed
    kept in `_Archive/` first but the list of names to replace, which is copied nowhere. With --dry-run what
    would change, and nothing written."""
    b = p.case(args.case)
    if not themes_ai.one_line(args.note) and not args.dry_run:
        raise cli.Refused(_w("NO_PROJECT_REQUEST"))
    with_folder = bool(getattr(args, "folder", False))
    body = dict(project_body(p), case=b["case"], name=args.name, folder=with_folder)
    try:
        if args.dry_run:
            # the route's plan, and the refusal its rename would give, with nothing written
            root = srv.project_named(body["root"])
            folder = routes.rename_folder_of(root, b["case"])
            with srv._lock:
                answer, plan = routes.rename_plan(root, folder, args.name, with_folder, srv.config())
                said = routes.rename_refusal(root, folder, plan, srv.config())
            if said:
                raise WorkbookError(said)
        else:
            answer = routes.api_rename(dict(body, op="rename", **asked_by(args)))
    except (WorkbookError, srv.OutsideRoot) as exc:
        raise cli.Refused(str(exc)) from None
    new_label = answer.get("label") or answer.get("case")
    old = gets_mod.who(answer["old"])
    what = [f"  {line}." for line in answer["lines"] + answer["folder_lines"]]
    if args.dry_run:
        lines = [i18n.t("cli.said.dry_run_nothing_was_written"), i18n.t("cli.participant_rename.renaming_as_would_change", old=old, new=answer['new'])] + what
    else:
        lines = ([i18n.t("cli.participant_rename.renamed_as_now_it_changed", old=old, new=answer['new'], new_label=new_label)] + what
                 + [i18n.t("cli.participant_rename.a_copy_of_each_file_it")])
        # the list of names to replace holds real names, so Idiograph copies it nowhere (renamefix)
        if i18n.t("server.rename.names_list") in answer["lines"]:
            lines.append(i18n.t("cli.participant_rename.names_no_copy"))
    out = {"case": b["case"], "old": old, "new": answer["new"], "label": new_label,
           "changes": answer["lines"], "folder_changes": answer["folder_lines"], "dry_run": bool(args.dry_run)}
    return out, lines


def person_answer(person: dict) -> dict:
    """A participant's set as the command line answers it: their label, pseudonym, label, pen portrait and
    picture, `set:peep07`, a file's name in the project's pictures folder, or "" for none, and their demographics'
    values by category (demobuild), a list's one word and free words a list."""
    return dict({k: person.get(k) or "" for k in ("case", "who", "label", "portrait", "picture")},
                values=dict(person.get("values") or {}))


def values_said(values: dict) -> str:
    """A participant's values in a line, "Gender Female, Nationality Spanish and Irish"."""
    return ", ".join(f"{name} {formats.list_words(demo_mod.given_words(v))}" for name, v in (values or {}).items())


def person_lines(person: dict) -> list[str]:
    """A participant's set in plain lines, the participant first."""
    none = i18n.t("cli.participant_show.none")
    picture = person.get("picture") or ""
    said = (picture if picture.startswith("set:") else i18n.t("cli.participant_show.own_picture", name=picture)) \
        if picture else none
    return [person.get("case") or "",
            "  " + i18n.t("cli.participant_show.label", label=person.get("label") or none),
            "  " + i18n.t("cli.participant_show.picture", picture=said),
            "  " + i18n.t("cli.participant_show.portrait", portrait=person.get("portrait") or none),
            "  " + i18n.t("demographics.cli.values", values=values_said(person.get("values")) or none)]


def values_asked(given) -> dict:
    """`--value "Category=..."` read into `{category: value}`, given again for each category, commas between free
    words and nothing after the = clearing it (demobuild)."""
    out = {}
    for raw in given or []:
        name, sep, value = str(raw).partition("=")
        if not sep or not name.strip():
            raise cli.Refused(i18n.t("demographics.cli.value_shape", given=raw))
        out[name.strip()] = value.strip()
    return out


def cmd_participant_show(p: Project, args) -> tuple:
    """`participant show`: a participant's picture, label and pen portrait (pbiobuild, 11 November 2026), as the
    project page's row shows them, or with no participant named every participant's of the project, in case order.
    It reads and writes nothing."""
    named = getattr(args, "case", None)
    try:
        if named:
            got = routes.api_participant(dict(project_body(p), op="show", case=named))
            return {"participant": person_answer(got["person"])}, person_lines(got["person"])
        people = routes.people_view(p.root)
        cases = sorted(routes.project_cases(p.root), key=gets_mod.case_order)
        listed = [routes.person_of(p.root, people, case) for case in cases]
    except (WorkbookError, srv.OutsideRoot) as exc:
        raise cli.Refused(str(exc)) from None
    lines = [i18n.t("cli.participant_show.head_all", name=p.info["name"])]
    for person in listed:
        lines += person_lines(person)
    return {"participants": [person_answer(x) for x in listed]}, lines


def cmd_participant_set(p: Project, args) -> tuple:
    """`participant set`: a participant's picture, label and pen portrait (pbiobuild, 11 November 2026), as the
    project page's row sets them (`routes.api_participant`): --label and --portrait, "" clearing either, --picture
    one of the set, `set:peep07`, --picture-file an image file of his, kept in the project's pictures folder, made
    square and small, or --no-picture, each left out kept as it is. A label or a pen portrait holding a name from the
    project's list of names to replace is refused, nothing written. The demo's are fixed. With --dry-run what would
    change, and nothing written. One record in the project's History."""
    if p.demo:
        raise cli.Refused(i18n.t("cli.said.the_demos_project_is_fixed"))
    body = dict(project_body(p), op="set", case=args.case)
    for key, given in (("label", args.label), ("portrait", args.portrait), ("picture", args.picture),
                       ("from", args.picture_file)):
        if given is not None:
            body[key] = given
    if args.no_picture:
        body["picture"] = ""
    # their demographics, --value "Gender=Female" for each category (demobuild)
    values = values_asked(getattr(args, "value", None))
    if isinstance(getattr(args, "values", None), dict):
        values.update(args.values)
    if values:
        body["values"] = values
    if not any(k in body for k in ("label", "portrait", "picture", "from", "values")):
        raise cli.Refused(i18n.t("cli.participant_set.none_given"))
    if not themes_ai.one_line(args.note) and not args.dry_run:
        raise cli.Refused(_w("NO_PROJECT_REQUEST"))
    try:
        if args.dry_run:
            got = routes.api_participant(dict(body, dry_run=True))
        else:
            # the route takes the project's lock itself, as the app's own call does
            got = routes.api_participant(dict(body, **asked_by(args)))
    except (WorkbookError, srv.OutsideRoot) as exc:
        raise cli.Refused(str(exc), i18n.t("cli.said.nothing_was_written")) from None
    head = (i18n.t("cli.said.dry_run_nothing_was_written") if args.dry_run else
            i18n.t("cli.said.saved_in_the_project_file") if got["changes"] else i18n.t("cli.said.nothing_changed"))
    lines = [head] + got["changes"] + [""] + person_lines(got["person"])
    return {"participant": person_answer(got["person"]), "changes": got["changes"],
            "dry_run": bool(args.dry_run)}, lines


# ----------------------------------------------------------------- demographics (demobuild, 12 November 2026)

def demographics_lines(answer: dict) -> list[str]:
    """The project's demographics in plain lines: each category with its kind and values, then each participant's
    values, then a line while Trajectories' old tags wait to move."""
    lines = []
    for c in answer["demographics"]:
        kind = i18n.t("demographics.cli.list") if c["kind"] == "list" else i18n.t("demographics.cli.words")
        shown = i18n.t("demographics.cli.shown") if c["show"] else ""
        values = ", ".join(f"{v['word']} ({demo_mod.COLOURS[v['colour']]})" for v in c["values"])
        lines.append(i18n.t("demographics.cli.category", name=c["name"], kind=kind, shown=shown,
                            values=values or i18n.t("cli.participant_show.none")))
    if not answer["demographics"]:
        lines.append(i18n.t("demographics.cli.none"))
    lines.append(i18n.t("demographics.cli.table_each") if answer["table"] == "each" else i18n.t("demographics.cli.table_sum"))
    lines.append("")
    for p in answer["participants"]:
        lines.append(f"{p['case']}: {values_said(p['values']) or i18n.t('cli.participant_show.none')}")
    if answer.get("pending"):
        lines += ["", i18n.t("demographics.cli.pending")]
    return lines


def demographics_out(answer: dict) -> dict:
    return {k: answer[k] for k in ("demographics", "table", "participants", "pending")}


def cmd_demographics_show(p: Project, args) -> tuple:
    """`demographics show`: the project's categories, each with its kind, its values in order and their colours, and
    whether it shows as a pill, how the participants table carries them, and each participant's values, as Project
    settings shows them. It reads and writes nothing."""
    try:
        answer = routes.api_demographics(dict(project_body(p), op="show"))
    except (WorkbookError, srv.OutsideRoot) as exc:
        raise cli.Refused(str(exc)) from None
    return demographics_out(answer), [i18n.t("demographics.cli.head", name=p.info["name"])] + demographics_lines(answer)


def cmd_demographics_apply(p: Project, args) -> tuple:
    """`demographics apply`: the categories and their values changed with their operations, as Project settings
    changes them, all or nothing, a dry run first: add, rename, kind, show, move, remove, export, table, and on a
    value value_add, value_rename, value_colour, value_move, value_remove and value_to. A value taken off anyone
    copies the project file to _Archive first, and the History record keeps the values that went."""
    if p.demo:
        raise cli.Refused(i18n.t("cli.said.the_demos_project_is_fixed"))
    if not themes_ai.one_line(args.note) and not args.dry_run:
        raise cli.Refused(_w("NO_PROJECT_REQUEST"))
    spec = cli.read_spec(args.ops)
    ops = spec.get("operations") if isinstance(spec, dict) else spec
    body = dict(project_body(p), op="apply", ops=ops, dry_run=bool(args.dry_run))
    try:
        answer = routes.api_demographics(body if args.dry_run else dict(body, **asked_by(args)))
    except (WorkbookError, srv.OutsideRoot) as exc:
        raise cli.Refused(str(exc), i18n.t("cli.said.nothing_was_written")) from None
    head = (i18n.t("cli.said.dry_run_nothing_was_written") if args.dry_run else
            i18n.t("cli.said.saved_in_the_project_file") if answer["changes"] else i18n.t("cli.said.nothing_changed"))
    return (dict(demographics_out(answer), changes=answer["changes"], dry_run=bool(args.dry_run)),
            [head] + answer["changes"] + [""] + demographics_lines(answer))


def cmd_demographics_move_tags(p: Project, args) -> tuple:
    """`demographics move-tags`: Trajectories' old tags moved into each participant's values in the Tags category
    now, as the project page's next listing would move them, each word keeping its colour, both files copied to
    _Archive first. With --dry-run each participant's tags that would move, and nothing written."""
    if p.demo:
        raise cli.Refused(i18n.t("cli.said.the_demos_project_is_fixed"))
    if not themes_ai.one_line(args.note) and not args.dry_run:
        raise cli.Refused(_w("NO_PROJECT_REQUEST"))
    body = dict(project_body(p), op="move_tags", dry_run=bool(args.dry_run))
    try:
        answer = routes.api_demographics(body if args.dry_run else dict(body, **asked_by(args)))
    except (WorkbookError, srv.OutsideRoot) as exc:
        raise cli.Refused(str(exc), i18n.t("cli.said.nothing_was_written")) from None
    head = (i18n.t("cli.said.dry_run_nothing_was_written") if args.dry_run else
            i18n.t("cli.said.saved_in_the_project_file") if answer["changes"] else i18n.t("demographics.cli.no_tags"))
    return (dict(demographics_out(answer), changes=answer["changes"], dry_run=bool(args.dry_run)),
            [head] + answer["changes"])


def cmd_participant_complete(p: Project, args) -> tuple:
    """A participant's experiential statements marked complete, or with --reopen reopened, as the
    statements screen's Mark complete does (`routes.api_complete`), in a project of two or more timepoints
    at --timepoint, T1 without it. Only the mark in the progress file changes. With --dry-run what would
    change, and nothing written."""
    b = p.case(args.case)
    if not themes_ai.one_line(args.note) and not args.dry_run:
        raise cli.Refused(_w("NO_PROJECT_REQUEST"))
    op = "reopen" if getattr(args, "reopen", False) else "mark"
    body = {"workbook": str(b["workbook"]), "op": op, "timepoint": getattr(args, "timepoint", None)}
    try:
        before = routes.api_complete(dict(body, dry_run=True))
        done = before if args.dry_run else routes.api_complete(dict(body, **asked_by(args)))
    except (WorkbookError, srv.OutsideRoot) as exc:
        raise cli.Refused(str(exc)) from None
    except FileNotFoundError:
        raise cli.Refused(i18n.t("cli.said.the_participants_workbook_is_not_there")) from None
    tp = before["timepoint"]
    whose = i18n.t("cli.participant_complete.s_statements", who=gets_mod.who(b['case'])) + (i18n.t("cli.participant_complete.at_t", tp=tp) if tp > 1 else "")
    was = before["complete"]
    lines = [i18n.t("cli.said.dry_run_nothing_was_written")] if args.dry_run else []
    if not before["changed"]:
        said = (i18n.t("cli.participant_complete.are_marked_complete_already_since_so", whose=whose, when=cli.when_said(was))
                if op == "mark" else i18n.t("cli.participant_complete.are_not_marked_complete_so_nothing", whose=whose))
        lines.append(said + (i18n.t("cli.participant_complete.would_change") if args.dry_run else "changed."))
    elif args.dry_run:
        lines.append(i18n.t("cli.participant_complete.it_would_mark_complete", whose=whose) if op == "mark" else
                     i18n.t("cli.participant_complete.it_would_reopen_marked_complete_since", whose=whose, when=cli.when_said(was)))
    else:
        lines.append(i18n.t("cli.participant_complete.marked_complete", whose=whose) if op == "mark" else i18n.t("cli.participant_complete.reopened", whose=whose))
    return {"case": b["case"], "op": op, "timepoint": tp, "complete": done["complete"],
            "changed": before["changed"], "dry_run": bool(args.dry_run)}, lines


def cmd_participant_export(p: Project, args) -> tuple:
    """A participant's experiential statements as the statements CSV, as Export in Settings writes it
    (`routes.api_export`), `<stem> - All Experiential Statements.csv` in their `Working/` folder, in its
    place when there is one, its PET column from the Current board when they have a board, every
    timepoint's in a project of two or more. With --notes the interviewer notes go to a markdown file of
    their own beside it, as the Include interviewer notes tick sends them. It changes nothing he made, so
    it needs no request and keeps no History, as the page's export keeps none. With --dry-run what it
    would write, and nothing written."""
    b = p.case(args.case)
    book = Path(b["workbook"])
    notes = bool(getattr(args, "notes", False))
    body = {"path": str(book), "dry_run": bool(args.dry_run)}
    if notes:
        body["notes"] = True
    there = export_mod.output_path(book).exists()
    try:
        done = routes.api_export(body)
    except (WorkbookError, srv.OutsideRoot) as exc:
        raise cli.Refused(str(exc)) from None
    except FileNotFoundError:
        raise cli.Refused(i18n.t("cli.said.the_participants_workbook_is_not_there")) from None
    head = i18n.t("cli.said.dry_run_nothing_was_written_it") if args.dry_run else "Wrote"
    lines = [i18n.t("cli.participant_export.s_to", head=head, case=b['case'], statements=i18n.t("cli.n.statement", n=done['statements']), path=done['path'])
             + (i18n.t("cli.participant_export.in_place_of_the_csv_there") if there else ".")]
    if notes:
        if done.get("notes_path"):
            lines.append(i18n.t("cli.participant_export.to", v_=i18n.t("cli.said.it_would_write") if args.dry_run else 'Wrote', notes=i18n.t("cli.n.interviewer_note", n=done['notes']), notes_path=done['notes_path']))
        else:
            lines.append(i18n.t("cli.participant_export.has_no_interviewer_notes_so_no", case=b['case'], v_=i18n.t("cli.participant_export.would_be") if args.dry_run else 'was'))
    out = {"case": b["case"], "file": done["path"], "statements": done["statements"], "replaced": there,
           "dry_run": bool(args.dry_run)}
    if notes:
        out.update(notes=done.get("notes", 0), notes_file=done.get("notes_path"))
    return out, lines


# --------------------------------------------------------------- statements

def placements(read: dict, data: dict | None) -> list[dict]:
    """For each board of the file, where it places each statement: the labels over it, top first,
    Not placed, or Set aside, with the reason a statement left out or set aside was given."""
    out = []
    for board in themes.boards_of(data):
        v = themes.follow(board, read["cards"], read["quotes"])
        paths = themes.label_paths(v)
        parents = themes.parents_of(v["groups"])
        reasons = (v.get("ai") or {}).get("discarded") or {}
        where = {}
        for c in read["cards"]:
            k = c["key"]
            if k in v["discarded"]:
                where[k] = {"where": BIN, "label": None}
            elif k in parents:
                where[k] = {"where": paths.get(k, ""), "label": parents[k]}
            else:
                where[k] = {"where": NOT_PLACED, "label": None}
            if reasons.get(k) and where[k]["label"] is None:
                where[k]["reason"] = reasons[k]
        out.append({"id": v["id"], "name": v["name"], "where": where})
    return out


def cmd_statements(p: Project, args) -> tuple:
    """Every statement of a participant. In a project of two or more timepoints (21 October) each row
    carries its `timepoint` and `timepoint_label`, and without `--timepoint` every timepoint's
    statements come, T1's first, each timepoint's short ids its own, as its board's ops take them."""
    b = p.case(args.case)
    book = Path(b["workbook"])
    tps = routes.project_timepoints(book)
    if not routes.longitudinal(tps):
        return statements_at(b, book)
    asked = getattr(args, "timepoint", None)
    wanted = [routes.timepoint_asked(asked, tps)] if asked not in (None, "") else [t["n"] for t in tps]
    rows, lines = [], []
    for n in wanted:
        label, about = tps[n - 1]["label"], tps[n - 1]["description"]
        with themes.scoped(n):
            answer, said = statements_at(b, book)
        for r in answer["statements"]:
            rows.append(dict(r, timepoint=n, timepoint_label=label))
        lines += ([""] if lines else []) + [f"{label}{', ' + about if about else ''}"] + said
    return {"case": b["case"], "workbook": book.name, "statements": rows}, lines


def statements_at(b: dict, book: Path) -> tuple:
    """A participant's statements at the timepoint in scope, T1's in a project of one."""
    read = themes.read_cards(book, explore=True, turns=True)
    sids, _ = ids_of(read)
    placed = placements(read, load_board_file(book))
    rows = []
    for c in read["cards"]:
        row = themes.row_key(c["sheet"], c["row"])
        own = themes.own_quote(read["quotes"], c["key"])
        # a statement carries its own quote, and a quote past the turn's statements stays its turn's
        rows.append({"id": sids[c["key"]], "key": c["key"], "sheet": c["sheet"], "row": c["row"], "line": c["line"],
                     "time": c["time"], "text": c["text"], "turn": read["turns"].get(row, ""),
                     "quotes": [dict({"key": own["key"], "text": own["text"]},
                                     **{k: own[k] for k in ("time", "rows") if own.get("span")})] if own else [],
                     "notes": list(read["explored"].get(row) or []),
                     "boards": [dict({"board": x["id"], "name": x["name"]}, **x["where"][c["key"]]) for x in placed]})
    lines, last = [i18n.t("cli.statements_head", case=b["case"], n=len(rows)) if rows
                   else i18n.t("cli.no_statements", case=b["case"])], None
    stated = {c["key"] for c in read["cards"]}
    for r in rows:
        turn = (r["sheet"], r["row"])
        if turn != last:
            last = turn
            lines += ["", i18n.t("cli.statements_at.row", sheet=r['sheet'], row=r['row'], time=r['time'] or i18n.t("cli.said.no_timecode")), i18n.t("cli.statements_at.turn", turn=r['turn'])]
            for n in r["notes"]:
                lines.append(i18n.t("cli.statements_at.note", n=n))
            for q in (read["quotes"].get(themes.row_key(*turn)) or {}).get("quotes") or []:
                if q["key"] not in stated:
                    lines.append("  " + i18n.t("cli.quote_alone", ref=q["key"], text=themes.quoted(q["text"])))
        lines.append(f"  {r['id']} {r['key']}  {r['text']}")
        for q in r["quotes"]:
            # a quote that takes in the same speaker's passages next to its own says which (quotespan)
            ran = i18n.t("cli.said.rows", listed=listed([str(x) for x in q['rows']]), time=q['time']) if q.get("rows") else ""
            lines.append("      " + i18n.t("cli.quote", ref=q["key"], text=themes.quoted(q["text"])) + ran)
        for x in r["boards"]:
            why = f" ({x['reason']})" if x.get("reason") else ""
            lines.append(f"      {x['name']}: {x['where']}{why}")
    return {"case": b["case"], "workbook": book.name, "statements": rows}, lines


# ------------------------------------------------------------------ boards

def board_entry(board: dict, data: dict, read: dict | None = None) -> dict:
    """A board as `board list` gives it, its counts read with `read`, the workbook as `themes.read_cards`
    reads it, so a statement written after the board was made counts as waiting in Not placed, as the
    canvas and `board show` have it (30 October)."""
    v = themes.normalise(board) if read is None else themes.with_new(
        themes.follow(board, read["cards"], read["quotes"]), read["cards"])
    parents = themes.parents_of(v["groups"])
    tops = [g for g in v["groups"] if g["id"] not in parents]
    placed = sum(1 for k in v["cards"] if k in parents)
    stacked = len(themes.stacked_keys(v))
    out = {"id": v["id"], "name": v["name"], "note": v["note"], "created": v["created"], "updated": v["updated"],
           "current": v["id"] == themes.chosen_of(data), "canvas": v["id"] == (themes.current_version(data) or {}).get("id"),
           "pets": len(tops), "placed": placed, "not_placed": len(v["cards"]) - placed - len(v["discarded"]) - stacked,
           "waiting": len(themes.waiting_keys(v)),
           "discarded": len(v["discarded"]), "set_aside": len(v["discarded"]), "stacked": stacked,
           "revisions": len(themes.history_of(board))}
    for key in themes.AGENT_KEYS:
        if v.get(key):
            out[key] = v[key]
    # a reviewer's own board of a participant someone else works on, kept apart in his copy (ownboards)
    if board.get(themes.OWN):
        out["own"] = True
    return out


def cmd_board_list(p: Project, args) -> tuple:
    b = p.case(args.case)
    data = load_board_file(Path(b["workbook"]))
    read = themes.read_cards(Path(b["workbook"])) if themes.boards_of(data) else None
    boards = [board_entry(x, data, read) for x in themes.boards_of(data)]
    lines = [f"{b['case']}: {i18n.t('cli.n.board', n=len(boards))}" if boards else i18n.t("cli.board_list.no_boards_yet", case=b['case'])]
    for x in boards:
        marks = [w for w, on in ((i18n.t("cli.said.the_current_board"), x["current"]), (i18n.t("cli.said.on_the_canvas"), x["canvas"]),
                                        (i18n.t("team_board.cli.own"), x.get("own"))) if on]
        lines.append(i18n.t("cli.board_list.placed_not_placed_set_aside_stacked", id=x['id'], name=x['name'], v_=' (' + ', '.join(marks) + ')' if marks else '', pets=i18n.t("cli.n.pet", n=x['pets']), placed=x['placed'], not_placed=x['not_placed'], discarded=x['discarded'], stacked=x['stacked'], revisions=i18n.t("cli.n.revision", n=x['revisions'])))
        if x["note"]:
            lines.append(f"      {x['note']}")
        if x.get("changed"):
            lines.append(i18n.t("cli.board_list.last_changed_by_in_a_conversation", tool=x['changed']['tool'] or cli.TOOL, when=cli.when_said(x['changed']['at'])))
    return {"case": b["case"], "boards": boards}, lines


def shown_board(read: dict, board: dict, sids: dict, labels: str = themes.LETTERS) -> dict:
    """A board as `board show` sets it out: `themes.outline`'s tree, each statement with its short
    id, each label with `export_label`, the label the PDF, the Word document and the PET draft give
    it, A1 or PET 1a by `labels`, and Not placed with the reason each was left out when it was given
    one. A top carries `stacked`, the statements stacked under it, each with its short id."""
    v = themes.follow(board, read["cards"], read["quotes"])
    tree = themes.outline(read, v)
    reasons = (v.get("ai") or {}).get("discarded") or {}
    numbers = themes.pet_numbers(tree["themes"], labels)

    loose = {k for k, c in v["cards"].items() if c.get(themes.LOOSE)}

    def statement(s: dict) -> dict:
        out = dict(s, id=sids.get(s["key"]))
        # one in no PET that he put on the canvas, where the rest of Not placed waits in the sidebar
        if s["key"] in loose:
            out["loose"] = True
        if s["key"] in reasons and "reason" not in out:
            out["reason"] = reasons[s["key"]]
        if s.get("stacked"):
            out["stacked"] = [dict(x, id=sids.get(x["key"])) for x in s["stacked"]]
        return out

    def theme(t: dict) -> dict:
        return dict(t, export_label=numbers.get(t["id"], ""), statements=[statement(s) for s in t["statements"]],
                    themes=[theme(x) for x in t["themes"]])

    out = dict(tree, id=v["id"], themes=[theme(t) for t in tree["themes"]],
               unplaced=[statement(s) for s in tree["unplaced"]], discarded=[statement(s) for s in tree["discarded"]])
    out["set_aside"] = out["discarded"]
    for key in themes.AGENT_KEYS:
        if v.get(key):
            out[key] = v[key]
    return out


def gap_said(seconds: int) -> str:
    """A gap as words, "1 minute", "2 minutes", "30 seconds"."""
    n = int(seconds)
    if n % 60 == 0:
        return i18n.t("cli.gap_said.1_minute") if n == 60 else f"{n // 60} minutes"
    return i18n.t("cli.gap_said.1_second") if n == 1 else f"{n} seconds"


def close_of(read: dict, board: dict, sids: dict, gap: int, labels: dict | None = None) -> dict:
    """A board's close pairs as `board show` gives them (see `themes.close_pairs`): the gap they were
    found within, each pair with its two short ids and keys, its sheet, how far apart in seconds or
    rows and in words, and the group both stand in, with its title, and the pairs marked Not the same."""
    v = themes.follow(board, read["cards"], read["quotes"])
    titles = labels if labels is not None else {g["id"]: g["label"] for g in v["groups"]}
    pairs = [{"items": [sids.get(k, k) for k in x["items"]], "keys": x["items"], "sheet": x["sheet"],
              "gap": x["gap"], "unit": x["unit"], "words": themes.pair_words(x), "group": x["group"],
              "label": titles.get(x["group"], "")}
             for x in themes.close_pairs(v, read["cards"], gap)]
    apart = [{"items": [sids.get(k, k) for k in x], "keys": list(x)} for x in v.get("not_same") or []]
    return {"within_s": gap, "pairs": pairs, "not_same": apart}


def close_gap_asked(args) -> int:
    """The gap `board show` looks within: `--close` for this one look, else the setting, a minute on a
    new install."""
    asked = getattr(args, "close", None)
    if asked is not None:
        gap = themes.close_gap(asked, free=True)
        if str(gap) != str(asked).strip():
            raise cli.Refused(i18n.t("cli.close_gap_asked.say_close_as_whole_seconds_from", close_most=themes.CLOSE_MOST))
        return gap
    return themes.close_gap(srv.config().get("close_gap"))


def statement_line(s: dict, pad: str) -> list[str]:
    head = pad + "  ".join(x for x in (f"{s.get('id') or ''} {s['key']}".strip(), s.get("time") or "", s["text"]) if x)
    out = [head + (i18n.t("cli.statement_line.no_longer_in_the_workbook") if s.get("missing") else "") + (f"  ({_w('LOOSE_SAID')})" if s.get("loose") else "")]
    if s.get("reason"):
        out.append(i18n.t("cli.statement_line.why", pad=pad, reason=s['reason']))
    for x in s.get("close") or []:
        out.append(i18n.t("cli.statement_line.close_to", pad=pad, id=x['id'] or x['key'], v_=x['words'][0].lower() + x['words'][1:]))
    for x in s.get("stacked") or []:
        out.append(pad + i18n.t("cli.statement_line.stacked_under_it") + "  ".join(
            y for y in (f"{x.get('id') or ''} {x['key']}".strip(), x.get("time") or "", x["text"]) if y))
    return out


def tree_lines(t: dict, depth: int = 1) -> list[str]:
    pad = "   " * depth
    lines = [f"{'   ' * (depth - 1)}{t['id']} {t['label']} ({t['count']})"]
    if t.get(themes.DESCRIPTION):
        lines.append(i18n.t("cli.tree_lines.description", pad=pad, t=t[themes.DESCRIPTION]))
    if t.get("note"):
        lines.append(i18n.t("cli.said.note", pad=pad, note=t['note']))
    for s in t["statements"]:
        lines += statement_line(s, pad)
    for q in t["picks"]:
        lines.append(i18n.t("cli.tree_lines.picked", pad=pad, key_=q['key'], quoted=themes.quoted(q['text'])))
    for sub in t["themes"]:
        lines += tree_lines(sub, depth + 1)
    return lines


def board_text(case: str, shown: dict) -> list[str]:
    lines = [f"{shown['name']} ({shown['id']}), {case}"]
    if shown.get("note"):
        lines.append(i18n.t("cli.board_text.note", note=shown['note']))
    if shown.get("changed"):
        lines.append(i18n.t("cli.board_text.last_changed_by_in_a_conversation", tool=shown['changed']['tool'] or cli.TOOL, when=cli.when_said(shown['changed']['at'])))
    if shown.get("version"):
        lines.append(i18n.t("cli.said.version", version=shown['version']))
    for t in shown["themes"]:
        lines += [""] + tree_lines(t)
    lines += ["", f"{NOT_PLACED} ({len(shown['unplaced'])})"]
    for s in shown["unplaced"]:
        lines += statement_line(s, "   ")
    lines += ["", f"{BIN} ({len(shown['discarded'])})"]
    for s in shown["discarded"]:
        lines += statement_line(s, "   ")
    close = shown.get("close")
    if close is not None:
        marked = len(close["not_same"])
        lines += ["", i18n.t("cli.board_text.close_pairs_within_in_one_group", n_pairs=len(close['pairs']), gap=gap_said(close['within_s']))
                  + (i18n.t("cli.board_text.marked_not_the_same", marked=marked) if marked else "")]
    return lines


def cmd_board_show(p: Project, args) -> tuple:
    b = p.case(args.case)
    book = Path(b["workbook"])
    read = themes.read_cards(book)
    sids, _ = ids_of(read)
    data = load_board_file(book)
    board = pick_board(data, args.board)
    asked = getattr(args, "labels", None)
    if asked and asked not in themes.PET_LABELS:
        raise cli.Refused(i18n.t("cli.said.say_labels_letters_or_labels_numbers"))
    shown = shown_board(read, board, sids, asked or p.info["pet_labels"])
    # its close pairs (20 October), each statement of one saying its partner and the gap, as the canvas
    # links them, within the gap the settings hold or `--close` for this one look
    shown["close"] = close_of(read, board, sids, close_gap_asked(args))
    near: dict[str, list] = {}
    for x in shown["close"]["pairs"]:
        one, two = x["keys"]
        near.setdefault(one, []).append({"id": sids.get(two), "key": two, "words": x["words"]})
        near.setdefault(two, []).append({"id": sids.get(one), "key": one, "words": x["words"]})

    def with_close(t: dict) -> dict:
        return dict(t, statements=[dict(st, close=near[st["key"]]) if st["key"] in near else st for st in t["statements"]],
                    themes=[with_close(x) for x in t["themes"]])

    shown["themes"] = [with_close(t) for t in shown["themes"]]
    # its version, which board apply carries back so a change over a board changed since is refused
    shown["version"] = themes.board_version(board)
    return dict(shown, case=b["case"]), board_text(b["case"], shown)


def cmd_board_export(p: Project, args) -> tuple:
    """A board as a Word document or a PDF, the IPA book's table of PETs, the exports the PETs
    screen makes, written at the case's root beside the workbook, the PDF where `--out` names when it
    names a folder or a file, and never over a file there (see `themes_word.py` and
    `print_pdf.py`), a PDF over its own name only with `--replace`. It changes
    nothing he made, so it needs no request. With no board named, the Current board. Its PETs are
    labelled as the project labels them, the book's letters unless its file says numbers, and
    `--labels letters` or `--labels numbers` overrides that for this run. Not placed and the binned
    statements stay out, as the app's ticks are on a new install, unless `--not-placed` or
    `--binned` asks for them, a top stands for the statements stacked under it unless `--stacked`
    puts them under it, as Include stacked statements does, and `--for-sending` names the file by the
    case alone and leaves the board's name off the page, as Leave out the board's name does. `--board-note` puts the
    board's note under the PDF's head, as the print view's Board note does. `--portrait` puts the participant's
    label and pen portrait under the head, never their picture, as Pen portrait does (pbioexport). The PDF is made
    by Typst from the board, as the app's Export as PDF makes it, with no window and no browser. `--draft` writes
    the PET draft and the statements CSV, as the PETs screen's Export does (see `board_draft`)."""
    word, pdf = bool(getattr(args, "word", False)), bool(getattr(args, "pdf", False))
    if getattr(args, "canvas", None):
        if word or pdf or getattr(args, "draft", False):
            raise cli.Refused(i18n.t("cli.board_export.say_word_pdf_canvas_or_draft"))
        return board_canvas(p, args)
    if getattr(args, "draft", False):
        if word or pdf:
            raise cli.Refused(i18n.t("cli.board_export.say_word_pdf_canvas_or_draft"))
        return board_draft(p, args)
    if word == pdf:
        raise cli.Refused(i18n.t("cli.board_export.say_word_pdf_canvas_or_draft"))
    # a thematic analysis project's table is its table of themes, on the project's board (taword, 1 November 2026)
    if i18n.method_now() == "ta":
        raise cli.Refused(i18n.t("cli.board_export.a_thematic_analysis_projects_table_is"))
    if word and getattr(args, "replace", False):
        raise cli.Refused(i18n.t("cli.board_export.replace_is_for_pdf_alone_a"))
    if word and (getattr(args, "out", None) or getattr(args, "board_note", False)):
        raise cli.Refused(i18n.t("cli.board_export.out_and_board_note_are_for"))
    asked = getattr(args, "labels", None)
    if asked and asked not in themes.PET_LABELS:
        raise cli.Refused(i18n.t("cli.said.say_labels_letters_or_labels_numbers"))
    labels = asked or p.info["pet_labels"]
    b = p.case(args.case)
    book = Path(b["workbook"])
    board = pick_board(load_board_file(book), args.board)
    ticks = {"unplaced": bool(getattr(args, "not_placed", False)), "binned": bool(getattr(args, "binned", False)),
             "stacked": bool(getattr(args, "stacked", False)), "sending": bool(getattr(args, "for_sending", False)),
             # each label's description under its title, as the Descriptions tick, on unless --no-descriptions
             "descriptions": not getattr(args, "no_descriptions", False)}
    # the participant's label and pen portrait under the head with --portrait, as Pen portrait (pbioexport)
    portrait = bool(getattr(args, "portrait", False))
    who = routes.portrait_printed(book, {"portrait": portrait})
    # the case named as the PETs screen names it in the document and the file, from its folder
    with wb_mod.case_held(book, export=True):
        if pdf:
            try:
                made = print_pdf.write(book, case_name(book), board.get("id"), p.info["research_question"],
                                       labels=labels, note=bool(getattr(args, "board_note", False)),
                                       out=getattr(args, "out", None), replace=bool(getattr(args, "replace", False)),
                                       dry_run=args.dry_run, project=p.info.get("name") or "",
                                       researcher=routes.researcher_name(), who=who, **ticks)
            except WorkbookError as exc:
                raise cli.Refused(str(exc)) from None
        else:
            made = themes_word.write(book, case_name(book), board.get("id"), dry_run=args.dry_run, labels=labels,
                                     author=routes.researcher_name(), who=who, **ticks)
    beside = not pdf or Path(made["folder"]).resolve() == book.parent.resolve()
    where = i18n.t("cli.said.at_the_root_of_s_folder", case=b['case']) if beside else f"in {made['folder']}"
    counts = made["counts"]
    said = (i18n.t("cli.board_export.placed_not_placed_and_in_the", pets=i18n.t("cli.n.pet", n=counts['pets']), statements=i18n.t("cli.n.statement", n=counts['statements']), not_placed=counts['not_placed'], discarded=counts['discarded']))
    dated = i18n.t("cli.said.the_plain_name_was_taken_so") if made["dated"] else ""
    if made.get("replaced"):
        dated = i18n.t("cli.said.it_took_the_place_of_the")
    if args.dry_run:
        text = i18n.t("cli.board_export.dry_run_nothing_was_written_it", name=made['name'], where=where, said=said, dated=dated)
    else:
        text = i18n.t("cli.board_export.wrote", name=made['name'], where=where, said=said, dated=dated)
    out = {"case": b["case"], "board": made["version"]["id"], "name": made["version"]["name"], "file": made["name"],
           "format": "pdf" if pdf else "word", "dated": made["dated"], "replaced": bool(made.get("replaced")),
           "for_sending": ticks["sending"], "portrait": portrait, "counts": counts, "labels": labels, "said": text}
    if pdf:
        out.update(path=made["path"], folder=made["folder"], board_note=bool(getattr(args, "board_note", False)),
                   not_placed=ticks["unplaced"], binned=ticks["binned"], stacked=ticks["stacked"])
    return (dict(out, dry_run=True) if args.dry_run else out), [text]




def canvas_refused(args, flags) -> None:
    """--canvas refused with a flag only the table takes."""
    given = [flag for flag, attr in flags if getattr(args, attr, None)]
    if given:
        raise cli.Refused(f"{', '.join(given)}: {_w('CANVAS_ALONE')}")


def canvas_said(made: dict, where: str, dry_run: bool) -> str:
    """The line a canvas export says."""
    dated = i18n.t("cli.said.the_plain_name_was_taken_so") if made["dated"] else ""
    if made.get("replaced"):
        dated = i18n.t("cli.canvas_said.it_took_the_place_of_the", upper=made['kind'].upper())
    if dry_run:
        return i18n.t("cli.canvas_said.dry_run_nothing_was_written_it", name=made['name'], where=where, dated=dated)
    size = i18n.t("cli.canvas_said.by_pixels", pixels=made['pixels'][0], pixels2=made['pixels'][1]) if made.get("pixels") else ""
    return i18n.t("cli.canvas_said.wrote", name=made['name'], where=where, size=size, dated=dated)


def board_canvas(p: Project, args) -> tuple:
    """A board's canvas as a PDF or a PNG (`--canvas pdf` or `--canvas png`, 1 November 2026, exportA), as the PETs
    screen's Export makes it on the canvas: the canvas's own page, every statement whole, on one landscape page or
    pictured whole at twice its scale, beside the workbook where the table's PDF goes, named as the table's with
    " canvas" after it, or where `--out` names. Typst draws it from the board as its file keeps it, laid out by the
    canvas's own rule, as the app's Export makes it (see `canvas_out`), with no window and no browser. Never over a
    file there unless `--replace`. It changes nothing he made."""
    canvas_refused(args, (("--labels", "labels"), ("--not-placed", "not_placed"), ("--set-aside", "binned"),
                          ("--stacked", "stacked"), ("--for-sending", "for_sending"),
                          ("--no-descriptions", "no_descriptions"), ("--board-note", "board_note"),
                          ("--portrait", "portrait")))
    b = p.case(args.case)
    book = Path(b["workbook"])
    board = pick_board(load_board_file(book), args.board)
    try:
        kind = canvas_out.kind_of(args.canvas)
        title = routes.themes_print.title_of(case_name(book), board.get("name") or themes.FIRST_NAME)
        made = canvas_out.place(book.parent, canvas_out.stem_of(title), kind, out=getattr(args, "out", None),
                                replace=bool(getattr(args, "replace", False)))
        if not args.dry_run:
            # the board read in the run's scope, at its timepoint when --timepoint names one
            with wb_mod.case_held(book, export=True):
                data = canvas_out.pets_data(book, case_name(book), str(board.get("id") or "") or None,
                                            quotes=canvas_out.quotes_of(srv.config()),
                                            close=canvas_out.close_of(srv.config()))
                made = canvas_out.made(made, data)
    except WorkbookError as exc:
        raise cli.Refused(str(exc)) from None
    beside = Path(made["folder"]).resolve() == book.parent.resolve()
    where = i18n.t("cli.said.at_the_root_of_s_folder", case=b['case']) if beside else f"in {made['folder']}"
    text = canvas_said(made, where, args.dry_run)
    out = {"case": b["case"], "board": str(board.get("id") or ""), "name": board.get("name") or themes.FIRST_NAME,
           "file": made["name"], "path": made["path"], "folder": made["folder"], "format": kind, "canvas": True,
           "dated": made["dated"], "replaced": bool(made.get("replaced")), "said": text,
           **{k: made[k] for k in ("bytes", "pixels") if k in made}}
    return (dict(out, dry_run=True) if args.dry_run else out), [text]




def board_draft(p: Project, args) -> tuple:
    """A board's PET grouping draft in markdown and the statements CSV with its Proposed PET column from the
    same board, both in the participant's `Working/` folder, as the PETs screen's Export writes them (26
    October), through the route's own function, `routes.api_themes_export`, its dry run the route's. Each
    writes over the file of its name, as the screen's Export does, since the next export writes them again.
    It changes nothing he made."""
    given = [flag for flag, on in (("--labels", getattr(args, "labels", None)), ("--not-placed", getattr(args, "not_placed", False)),
                                   ("--set-aside", getattr(args, "binned", False)),
                                   ("--for-sending", getattr(args, "for_sending", False)),
                                   ("--no-descriptions", getattr(args, "no_descriptions", False)),
                                   ("--replace", getattr(args, "replace", False)),
                                   ("--board-note", getattr(args, "board_note", False)), ("--out", getattr(args, "out", None)),
                                   ("--portrait", getattr(args, "portrait", False)))
             if on]
    if given:
        raise cli.Refused(f"{', '.join(given)}: {_w('DRAFT_ALONE')}")
    b = p.case(args.case)
    book = Path(b["workbook"])
    board = pick_board(load_board_file(book), args.board)
    body = {"workbook": str(book), "version": str(board.get("id")), "stacked": bool(getattr(args, "stacked", False)),
            "dry_run": bool(args.dry_run)}
    try:
        done = routes.api_themes_export(body)
    except (WorkbookError, srv.OutsideRoot) as exc:
        raise cli.Refused(str(exc)) from None
    files = " and ".join(done["shown"])
    out = {"case": b["case"], "board": done["version"]["id"], "name": done["version"]["name"], "format": "draft",
           "markdown": done["shown"][0], "csv": done["shown"][1], "labels": done["labels"],
           "stacked": body["stacked"]}
    if args.dry_run:
        over = (i18n.t("cli.board_draft.it_would_write_over_as_the", list=' and '.join(done['there']))
                if done["there"] else "")
        text = i18n.t("cli.board_draft.dry_run_nothing_was_written_it", files=files, case=b['case'], name=out['name'], over=over)
        return dict(out, dry_run=True, there=done["there"], said=text), [text]
    text = (i18n.t("cli.board_draft.wrote_in_s_folder_from_in", files=files, case=b['case'], name=out['name'], statements=i18n.t("cli.n.statement", n=done['statements'])))
    return dict(out, statements=done["statements"], said=text), [text]


def cmd_gets_export(p: Project, args) -> tuple:
    """A GETs board as a PDF at the project's root, beside the GETs file, or where `--out` names, a
    folder or a file, as the GETs screen's print card
    makes it (see `print_pdf.write_gets`): the GET table, the audit trail or the full set by `--what`,
    every item or with `--selected` the quote alone, participant notes only with `--notes`, the
    board's name off with `--for-sending`, one GET's trail with `--get`, and with `--participants` a first page
    listing each participant with their label and pen portrait, as Participants table does (pbioexport). With no
    board named, the Current board. Never over a file there unless `--replace`. It reads the GETs file and the
    workbooks and changes nothing."""
    data = gets_data(p)
    board = pick_board(data, args.board)
    if getattr(args, "word", False):
        return gets_word_export(p, args, board)
    if getattr(args, "canvas", None):
        return gets_canvas(p, args, board)
    get = " ".join(str(getattr(args, "get", None) or "").split()) or None
    what = getattr(args, "what", None) or "table"
    people = routes.people_printed(p.root, {"participants": bool(getattr(args, "participants", False))})
    try:
        made = print_pdf.write_gets(p.root, p.books, p.info, board, what=what,
                                    detail="selected" if getattr(args, "selected", False) else "full",
                                    notes=bool(getattr(args, "notes", False)), get=get,
                                    sending=bool(getattr(args, "for_sending", False)), out=getattr(args, "out", None),
                                    replace=bool(getattr(args, "replace", False)), dry_run=args.dry_run,
                                    descriptions=not getattr(args, "no_descriptions", False), researcher=routes.researcher_name(),
                                    people=people)
    except WorkbookError as exc:
        raise cli.Refused(str(exc)) from None
    c = made["counts"]
    said = f"{cli.plural(c['gets'], 'theme' if i18n.method_now() == 'ta' else 'GET')} of {i18n.t('cli.n.participant', n=c['participants'])}"
    dated = i18n.t("cli.said.the_plain_name_was_taken_so") if made["dated"] else ""
    if made.get("replaced"):
        dated = i18n.t("cli.said.it_took_the_place_of_the")
    head = i18n.t("cli.said.dry_run_nothing_was_written_it") if args.dry_run else "Wrote"
    text = i18n.t("cli.gets_export.in", head=head, name=made['name'], folder=made['folder'], gets_what=print_pdf.gets_what(made['what']), said=said, dated=dated)
    out = {"board": made["version"]["id"], "name": made["version"]["name"], "file": made["name"], "path": made["path"],
           "folder": made["folder"], "format": "pdf", "what": made["what"], "detail": made["detail"],
           "notes": made["notes"], "get": made["get"], "for_sending": bool(getattr(args, "for_sending", False)),
           "participants": people is not None, "dated": made["dated"], "replaced": bool(made.get("replaced")),
           "counts": c, "said": text}
    return (dict(out, dry_run=True) if args.dry_run else out), [text]


def gets_word_export(p: Project, args, board: dict) -> tuple:
    """A thematic analysis project's table of themes as a Word document (`--word`, taword, 1 November 2026), as
    Microsoft Word on its Table view makes it (see `gets_word`): at the project's root where its PDF goes, never over
    a file there, every code and extract or with `--selected` each participant's key extract alone, participant notes
    only with `--notes`, the board's name left out with `--for-sending`, the participants table on its first page
    with `--participants`, its author Your name. Refused in an IPA project, whose tables of PETs go to Word through
    board export. It changes nothing."""
    given = [flag for flag, attr in (("--pdf", "pdf"), ("--canvas", "canvas"), ("--out", "out"), ("--what", "what"),
                                     ("--get", "get"), ("--replace", "replace")) if getattr(args, attr, None)]
    if given:
        raise cli.Refused(i18n.t("cli.gets_word_export.word_takes_selected_notes_for_sending", list=', '.join(given)))
    people = routes.people_printed(p.root, {"participants": bool(getattr(args, "participants", False))})
    try:
        gets_word.refuse_unless_ta()
        made = gets_word.write(p.root, p.books, p.info, board, detail="selected" if getattr(args, "selected", False) else "full",
                               notes=bool(getattr(args, "notes", False)), sending=bool(getattr(args, "for_sending", False)),
                               descriptions=not getattr(args, "no_descriptions", False), author=routes.researcher_name(),
                               dry_run=args.dry_run, people=people)
    except WorkbookError as exc:
        raise cli.Refused(str(exc)) from None
    c = made["counts"]
    said = i18n.t("cli.gets_word_export.of", themes=i18n.t("cli.n.theme", n=c['themes']), codes=i18n.t("cli.n.code", n=c['codes']), participants=i18n.t("cli.n.participant", n=c['participants']))
    dated = i18n.t("cli.said.the_plain_name_was_taken_so") if made["dated"] else ""
    head = i18n.t("cli.said.dry_run_nothing_was_written_it") if args.dry_run else "Wrote"
    text = i18n.t("cli.gets_word_export.in", head=head, name=made['name'], folder=made['folder'], said=said, dated=dated)
    out = {"board": made["version"]["id"], "name": made["version"]["name"], "file": made["name"], "path": made["path"],
           "folder": made["folder"], "format": "word", "detail": made["detail"], "notes": made["notes"],
           "for_sending": bool(getattr(args, "for_sending", False)), "participants": people is not None,
           "dated": made["dated"], "counts": c, "said": text}
    return (dict(out, dry_run=True) if args.dry_run else out), [text]


def gets_canvas(p: Project, args, board: dict) -> tuple:
    """A GETs board's canvas as a PDF or a PNG (`--canvas pdf` or `--canvas png`, 1 November 2026, exportA), as the
    GETs print card's Canvas on one page makes it, Save as PDF or Save as an image: the canvas's own page, a
    participant note on it only with `--notes`, at the project's root where the card's PDF goes, "Study - Board 2 -
    GETs canvas.png", a participant's LPETs (`--lpets`) beside their workbook, or where `--out` names, drawn by
    Typst as `board export --canvas` draws it. Never over a file there unless `--replace`. It changes nothing."""
    if getattr(args, "what", None) not in (None, "table"):
        raise cli.Refused(f"--what: {_w('CANVAS_ALONE')}")
    canvas_refused(args, (("--selected", "selected"), ("--for-sending", "for_sending"),
                          ("--no-descriptions", "no_descriptions"), ("--get", "get"), ("--participants", "participants")))
    if not p.books:
        raise cli.Refused(i18n.t("cli.gets_canvas.this_project_has_no_participants_yet"))
    name = str(board.get("name") or themes.FIRST_NAME)
    lpets = getattr(args, "lpets", None)
    try:
        kind = canvas_out.kind_of(args.canvas)
        if lpets:
            # a participant's LPETs beside their workbook, named by the participant (the app's own LPETs canvas), the
            # command run inside their LPETs (`place_of`), whose "participants" are the timepoints
            book = Path(routes.LPETS_FOR.get() or p.case(lpets)["workbook"])
            folder, heading = book.parent, case_name(book)
            title = f"{heading} - {name} - LPETs"
        else:
            folder, heading = p.root, p.info.get('name') or 'GETs'
            title = i18n.t("cli.gets_canvas.gets", get=heading, name=name)
        made = canvas_out.place(folder, canvas_out.stem_of(title), kind,
                                out=getattr(args, "out", None), replace=bool(getattr(args, "replace", False)))
        if not args.dry_run:
            data = canvas_out.gets_data(p.root, p.books, heading, str(board.get("id") or "") or None,
                                        notes=bool(getattr(args, "notes", False)),
                                        quotes=canvas_out.quotes_of(srv.config()))
            made = canvas_out.made(made, data)
    except WorkbookError as exc:
        raise cli.Refused(str(exc)) from None
    text = canvas_said(made, f"in {made['folder']}", args.dry_run)
    out = {"board": str(board.get("id") or ""), "name": name, "file": made["name"], "path": made["path"],
           "folder": made["folder"], "format": kind, "canvas": True, "notes": bool(getattr(args, "notes", False)),
           "dated": made["dated"], "replaced": bool(made.get("replaced")), "said": text,
           **{k: made[k] for k in ("bytes", "pixels") if k in made}}
    return (dict(out, dry_run=True) if args.dry_run else out), [text]


def tops_of(v: dict) -> dict[str, str]:
    """Each statement's PET on a board, the label no other label holds over it, by its key."""
    parents = themes.parents_of(v["groups"])
    out = {}
    for k in v["cards"]:
        at, seen = parents.get(k), set()
        while at is not None and parents.get(at) is not None and at not in seen:
            seen.add(at)
            at = parents[at]
        if at is not None:
            out[k] = at
    return out


def compare(read: dict, boards: list[dict]) -> dict:
    """Two or more boards side by side. For each pair of boards, the share of statement pairs placed
    alike: two statements are together on a board when one PET holds both, and a pair is placed alike
    when the two boards agree on whether it is together. A statement in no PET, Not placed or in the
    bin, is together with none. Then for each board, where each PET of every other board went on it:
    its statements counted under each of this board's PETs, Not placed and the bin."""
    keys = [c["key"] for c in read["cards"]]
    shown = [themes.follow(b, read["cards"], read["quotes"]) for b in boards]
    tops = [tops_of(v) for v in shown]
    titles = [{g["id"]: g["label"] for g in v["groups"]} for v in shown]
    pairs = []
    for i in range(len(shown)):
        for j in range(i + 1, len(shown)):
            alike = total = 0
            for x in range(len(keys)):
                for y in range(x + 1, len(keys)):
                    a, b = keys[x], keys[y]
                    one = tops[i].get(a) is not None and tops[i].get(a) == tops[i].get(b)
                    two = tops[j].get(a) is not None and tops[j].get(a) == tops[j].get(b)
                    total += 1
                    alike += one == two
            pairs.append({"a": shown[i]["id"], "a_name": shown[i]["name"], "b": shown[j]["id"], "b_name": shown[j]["name"],
                          "alike": alike, "pairs": total, "share": round(alike / total, 4) if total else 1.0})
    went = []
    for j, to in enumerate(shown):
        for i, frm in enumerate(shown):
            if i == j:
                continue
            pets = []
            order = [g["id"] for g in frm["groups"] if g["id"] not in themes.parents_of(frm["groups"])]
            for gid in order:
                mine = [k for k in keys if tops[i].get(k) == gid]
                counted: dict = {}
                for k in mine:
                    there = tops[j].get(k)
                    spot = there if there is not None else (BIN if k in to["discarded"] else NOT_PLACED)
                    counted[spot] = counted.get(spot, 0) + 1
                pets.append({"id": gid, "title": titles[i][gid], "count": len(mine),
                             "went": [{"to": spot if spot not in (BIN, NOT_PLACED) else None,
                                       "title": titles[j].get(spot, spot), "count": n}
                                      for spot, n in sorted(counted.items(), key=lambda kv: (-kv[1], str(kv[0])))]})
            went.append({"from": frm["id"], "from_name": frm["name"], "to": to["id"], "to_name": to["name"], "pets": pets})
    return {"boards": [{"id": v["id"], "name": v["name"]} for v in shown], "statements": len(keys),
            "pairs": pairs, "where": went}


def cmd_board_compare(p: Project, args) -> tuple:
    b = p.case(args.case)
    book = Path(b["workbook"])
    read = themes.read_cards(book)
    data = load_board_file(book)
    names = args.boards or [str(x.get("id")) for x in themes.boards_of(data)]
    boards = []
    for name in names:
        board = pick_board(data, name)
        if board not in boards:
            boards.append(board)
    if len(boards) < 2:
        raise cli.Refused(i18n.t("cli.board_compare.compare_takes_two_boards_or_more"))
    out = compare(read, boards)
    lines = [i18n.t("cli.board_compare.over", case=b['case'], list=', '.join(x['name'] for x in out['boards']), statements=i18n.t("cli.n.statement", n=out['statements'])), ""]
    for x in out["pairs"]:
        lines.append(i18n.t("cli.board_compare.and_of_statement_pairs_placed_alike", a_name=x['a_name'], b_name=x['b_name'], alike=x['alike'], pairs=x['pairs'], v_=round(100 * x['share'])))
    for w in out["where"]:
        lines += ["", i18n.t("cli.board_compare.where_s_pets_went_on", from_name=w['from_name'], to_name=w['to_name'])]
        for pet in w["pets"]:
            lines.append(f"  {pet['title']} ({pet['count']})")
            for g in pet["went"]:
                lines.append(f"    {g['count']} to {g['title']}")
    return dict(out, case=b["case"]), lines


def as_reasons(value, read: dict, keys: dict, problems: list) -> dict[str, str]:
    """The statements left out on purpose, `{"S9": "why"}` or `[{"id": "S9", "reason": "why"}]`,
    as their keys with their reasons."""
    items = []
    if isinstance(value, dict):
        items = list(value.items())
    elif isinstance(value, list):
        for x in value:
            if isinstance(x, dict):
                items.append((x.get("id") or x.get("key"), x.get("reason")))
            else:
                items.append((x, ""))
    elif value is not None:
        problems.append(i18n.t("cli.as_reasons.not_placed_is_a_list_or"))
    out = {}
    for name, why in items:
        key = statement_key(name, read, keys)
        if key is None:
            problems.append(i18n.t("cli.as_reasons.is_not_a_statement_of_this", name=name))
            continue
        out[key] = " ".join(str(why or "").split())
    return out


def build_board(spec, read: dict, sids: dict, keys: dict) -> dict:
    """A plain structure read strictly into what `themes_ai.lay_out` takes, every problem a line:
    every id known, a statement once, picks inside their label, no label without a title and no
    statement in the bin. A PET holds statements and sub-themes under `subs`, and a sub-theme or a
    group holds statements and groups under `groups`, at any depth."""
    problems: list[str] = []
    if not isinstance(spec, dict) or not isinstance(spec.get("pets"), list):
        raise cli.Refused(i18n.t("cli.build_board.a_board_is_pets_title_note"))
    for word in ("discarded", "bin", "discard"):
        if word in spec:
            problems.append(_w("NEVER_BIN"))
    quotes = {q["key"]: themes.row_key(row["sheet"], row["row"]) for row in read["quotes"].values() for q in row["quotes"]}
    rows = {c["key"]: themes.row_key(c["sheet"], c["row"]) for c in read["cards"]}
    seen: dict[str, str] = {}
    # what a label holds besides its statements, `subs` on a PET and `groups` below it, and the key it
    # may not carry, said as a refusal says it
    inner = lambda depth: "subs" if depth == 0 else "groups"
    wrong = lambda depth: (("groups", i18n.t("cli.build_board.a_pet_holds_statements_and_sub"))
                           if depth == 0 else ("subs", i18n.t("cli.build_board.a_holds_statements_and_groups_not", layer=themes.layer(depth))))

    def label(raw, where: str, depth: int):
        if not isinstance(raw, dict):
            problems.append(i18n.t("cli.build_board.is_not_a_label_with_a", where=where))
            return None
        title = themes_ai.clean_label(raw.get("title") or raw.get("label"))
        if not title:
            problems.append(i18n.t("cli.build_board.has_no_title", where=where))
        name = f"'{title}'" if title else where
        members = []
        for m in raw.get("members") or []:
            key = statement_key(m, read, keys)
            if key is None:
                problems.append(i18n.t("cli.build_board.in_is_not_a_statement_of", m=m, name=name))
            elif key in seen:
                problems.append(i18n.t("cli.build_board.is_placed_twice_in_and_in", pair=pair(key, sids), seen=seen[key], name=name))
            else:
                seen[key] = name
                members.append(key)
        key, why = wrong(depth)
        if key in raw:
            problems.append(i18n.t("cli.build_board.is_a_and", name=name, layer=themes.layer(depth), why=why))
        held = raw.get(inner(depth))
        if held is not None and not isinstance(held, list):
            problems.append(i18n.t("cli.build_board.the_of_is_not_a_list", inner=inner(depth), name=name))
        subs = []
        for i, s in enumerate(held if isinstance(held, list) else []):
            made = label(s, f"{themes.layer(depth + 1).capitalize()} {i + 1} of {name}", depth + 1)
            if made:
                subs.append(made)
        said = raw.get("description")
        if said is not None and not isinstance(said, str):
            problems.append(i18n.t("cli.build_board.the_description_of_is_not_words", name=name))
        return {"title": title, "note": themes_ai.clean_note(raw.get("note")), "members": members, "subs": subs,
                "description": themes.description_of({themes.DESCRIPTION: said if isinstance(said, str) else ""}),
                "picks": [str(k) for k in (raw.get("picks") or [])], "name": name}

    def under(item: dict) -> list[str]:
        return item["members"] + [k for s in item["subs"] for k in under(s)]

    def every(item: dict) -> list[dict]:
        return [item] + [x for s in item["subs"] for x in every(s)]

    made = [label(raw, f"PET {i + 1}", 0) for i, raw in enumerate(spec["pets"])]
    made = [m for m in made if m]
    dropped = []
    for pet in made:
        for item in every(pet):
            if not under(item):
                problems.append(i18n.t("cli.build_board.holds_no_statements", name=item['name']))
            kept = []
            for q in item["picks"]:
                if q not in quotes:
                    problems.append(i18n.t("cli.build_board.the_pick_on_is_not_a", q=q, name=item['name']))
                # a pick names a quote of a passage with a statement under the label, as the canvas keeps
                # one, and one whose passage has none under it is dropped and said, as a turn write drops one
                elif quotes[q] not in {rows.get(k) for k in under(item)}:
                    dropped.append({"key": q, "label": item["name"]})
                else:
                    kept.append(q)
            item["picks"] = kept
    reasons = as_reasons(spec.get("not_placed"), read, keys, problems)
    for key in reasons:
        if key in seen:
            problems.append(i18n.t("cli.build_board.is_under_not_placed_and_also", pair=pair(key, sids), seen=seen[key]))
    stacks = as_stacks(spec.get("stacked"), read, sids, keys, seen, reasons, problems)
    if not made:
        problems.append(i18n.t("cli.build_board.the_board_has_no_pets"))
    if problems:
        raise cli.Refused(*dict.fromkeys(problems))
    return {"pets": made, "reasons": reasons, "note": themes_ai.clean_note(spec.get("note")), "dropped": dropped,
            "stacks": stacks}


def as_stacks(value, read: dict, sids: dict, keys: dict, seen: dict, reasons: dict, problems: list) -> dict[str, list[str]]:
    """A new board's stacks, `{"S77": ["S79", "S80"]}`, each top a statement placed or not placed and
    each statement under it in no label, not under not_placed and under one top alone, as their keys,
    every problem a line."""
    if value is None:
        return {}
    if not isinstance(value, dict):
        problems.append(i18n.t("cli.as_stacks.stacked_is_a_mapping_of_each"))
        return {}
    out: dict[str, list[str]] = {}
    under: dict[str, str] = {}
    for name, items in value.items():
        top = statement_key(name, read, keys)
        if top is None:
            problems.append(i18n.t("cli.as_stacks.under_stacked_is_not_a_statement", name=name))
            continue
        if not isinstance(items, list) or not items:
            problems.append(i18n.t("cli.as_stacks.the_stack_under_names_no_statements", pair=pair(top, sids)))
            continue
        for item in items:
            key = statement_key(item, read, keys)
            if key is None:
                problems.append(i18n.t("cli.as_stacks.in_the_stack_under_is_not", item=item, pair=pair(top, sids)))
            elif key == top:
                problems.append(i18n.t("cli.as_stacks.is_stacked_under_itself", pair=pair(key, sids)))
            elif key in seen:
                problems.append(i18n.t("cli.as_stacks.is_stacked_under_and_also_in", pair=pair(key, sids), pair2=pair(top, sids), seen=seen[key]))
            elif key in reasons:
                problems.append(i18n.t("cli.as_stacks.is_stacked_under_and_also_under", pair=pair(key, sids), pair2=pair(top, sids)))
            elif key in under:
                problems.append(i18n.t("cli.as_stacks.is_stacked_under_and_under", pair=pair(key, sids), pair2=pair(top, sids), pair3=pair(under[key], sids)))
            else:
                under[key] = top
                out.setdefault(top, []).append(key)
    for top in out:
        if top in under:
            problems.append(i18n.t("cli.as_stacks.tops_a_stack_and_is_stacked", pair=pair(top, sids), pair2=pair(under[top], sids)))
    return out


def dropped_line(dropped: list[dict], dry: bool) -> str:
    """The one line a new board says of the picks it dropped, each one's statement not under its label."""
    if not dropped:
        return ""
    verb = i18n.t("cli.dropped_line.it_would_drop") if dry else i18n.t("cli.dropped_line.it_dropped")
    said = ", ".join(f"{d['key']} on {d['label']}" for d in dropped)
    return (i18n.t("cli.dropped_line.whose_statement_is_not_under_label", verb=verb, picks=i18n.t("cli.n.pick", n=len(dropped)), v_='its' if len(dropped) == 1 else 'their', said=said))


def lay_board(built: dict, read: dict) -> dict:
    """The structure laid out by `themes_ai.lay_out`, its titles, notes and picks put on the labels
    it made, PETs first and then each sub-theme followed by its groups, at any depth, in the same
    order, the picks' words beside them and the reasons for what was left out under `ai`."""
    def shape(item: dict) -> dict:
        return {"label": item["title"], "members": item["members"], "groups": [shape(s) for s in item["subs"]],
                "description": item.get("description") or ""}

    # the stacked statements are left out of the layout, as the bin's are, since they lie under their tops
    stacked = [k for keys in built.get("stacks", {}).values() for k in keys]
    version = themes_ai.lay_out([shape(pet) for pet in built["pets"]], read["cards"], stacked)
    version["discarded"] = []
    by_id = {g["id"]: g for g in version["groups"]}
    picks = {}

    def put(item: dict, gid: str) -> None:
        if item["note"]:
            by_id[gid]["note"] = item["note"]
        if item.get("description"):
            by_id[gid][themes.DESCRIPTION] = item["description"]
        if item["picks"]:
            picks[gid] = themes.picks_kept(item["picks"])
        # the labels inside it, in the order its members list them, which is the order given
        for sub, sid in zip(item["subs"], [m for m in by_id[gid]["members"] if m in by_id]):
            put(sub, sid)

    for i, pet in enumerate(built["pets"]):
        put(pet, f"g{i + 1}")
    version["picks"] = picks
    version["quoted"] = themes_ai.quoted_of(picks, read["quotes"])
    if built["reasons"]:
        version["ai"] = {"discarded": {k: why for k, why in built["reasons"].items() if why}}
    return version


FRESH = "fresh"
BIN_HOLD = "bin:"


def match_labels(built: dict, source: dict) -> dict[int, str]:
    """Each label of a new board, by `id()` of its item in `built`, matched to the label of the
    source board it keeps: the same title first, at any level, and then the label whose statements,
    at any depth, are half or more the same, the closest first. A source label is kept once."""
    by_id = {g["id"]: g for g in source["groups"]}
    under = {g: set(themes.cards_under(by_id, g)) for g in by_id}
    title = lambda t: themes.words(t).lower()

    def every(item: dict) -> list[dict]:
        return [item] + [x for s in item["subs"] for x in every(s)]

    def held(item: dict) -> set:
        return set(item["members"]) | {k for s in item["subs"] for k in held(s)}

    items = [x for pet in built["pets"] for x in every(pet)]
    out: dict[int, str] = {}
    taken: set[str] = set()
    for item in items:
        same = next((g for g in by_id if g not in taken and title(by_id[g]["label"]) == title(item["title"])), None)
        if same:
            out[id(item)] = same
            taken.add(same)
    scored = []
    for item in items:
        if id(item) in out:
            continue
        mine = held(item)
        for g in by_id:
            if g in taken or not mine or not under[g]:
                continue
            share = len(mine & under[g]) / len(mine | under[g])
            if share >= 0.5:
                scored.append((-share, len(scored), id(item), g))
    for _, _, item, g in sorted(scored):
        if item not in out and g not in taken:
            out[item] = g
            taken.add(g)
    return out


def carry_layout(built: dict, read: dict, source: dict) -> dict | None:
    """A new board laid out from `source`, the board it came from, keeping the place of every label
    and statement it keeps (see `themes.land_kept`), in the order `built` gives, the PETs and inside
    each label its statements and then its labels. A statement in the source's bin comes back where it
    goes, the new board having none in its bin. None when the order cannot be set on that layout, for
    a fresh one."""
    shown = themes.merge(read["cards"], source, read["quotes"])
    live = [c for c in shown["cards"] if not c.get("missing")]
    src = dict(themes.follow(source, read["cards"], read["quotes"]))
    for key in ("notes", "ai", "review", "revise", "history", "made", "changed", "quoted", "cut", "stacks"):
        src.pop(key, None)
    src = themes.normalise(dict(src, picks={}))
    src["cards"] = {c["key"]: {"x": c["x"], "y": c["y"], "text": c["text"]} for c in live}
    thrown = [k for k in src["discarded"] if k in src["cards"]]
    src["discarded"] = []
    numbers = [int(g["id"][1:]) for g in src["groups"] if re.match(r"^g\d+$", str(g["id"]))]
    top = max(numbers, default=0)
    if thrown:
        # the bin's statements held, for the landing, in a label the new board does not have
        src["groups"].append({"id": BIN_HOLD, "label": themes.DISCARDED, "members": thrown, "x": 0, "y": 0})
    src = themes.normalise(src)
    old_by = {g["id"]: g for g in src["groups"]}
    matched = match_labels(built, dict(src, groups=[g for g in src["groups"] if g["id"] != BIN_HOLD]))
    groups, picks, spec_order = [], {}, {}

    def put(item: dict) -> str:
        nonlocal top
        gid = matched.get(id(item))
        if gid is None:
            top += 1
            gid = f"g{top}"
        subs = [put(s) for s in item["subs"]]
        members = list(item["members"]) + subs
        old = old_by.get(gid)
        if old and set(old["members"]) == set(members):
            members = list(old["members"])
        groups.append({"id": gid, "label": item["title"], "members": members,
                       **({"note": item["note"]} if item["note"] else {}),
                       **({themes.DESCRIPTION: item["description"]} if item.get("description") else {})})
        if item["picks"]:
            picks[gid] = themes.picks_kept(item["picks"])
        spec_order[gid] = list(item["members"]) + subs
        return gid

    pets = [put(pet) for pet in built["pets"]]
    landed = themes.land_kept(src, {"groups": groups, "picks": picks})
    parents = themes.parents_of(landed["groups"])
    ids = {g["id"] for g in groups}
    try:
        for gid in sorted(spec_order, key=lambda g: -themes.depth_of(parents, g)):
            # its statements in the order given and its labels in the order given, each in the places
            # statements and labels read in now, so a sub-theme standing among the cards stays among them
            now = themes.order_of(landed, gid)
            cards = iter([m for m in spec_order[gid] if m not in ids])
            labels = iter([m for m in spec_order[gid] if m in ids])
            wanted = [next(labels) if m in ids else next(cards) for m in now]
            landed, _ = themes.reorder(landed, gid, wanted)
        landed, _ = themes.reorder(landed, None, pets)
    except WorkbookError:
        return None
    landed["picks"] = picks
    # the labels numbered g1 on as a fresh layout numbers them, the PETs in the order given first, then
    # each sub-theme followed by its groups, so ids read the same however the board is laid out
    by_id = {g["id"]: g for g in landed["groups"]}
    order = list(pets)

    def under_of(gid: str) -> list[str]:
        out = []
        for m in spec_order.get(gid, []):
            if m in by_id:
                out += [m] + under_of(m)
        return out

    for gid in pets:
        order += under_of(gid)
    names = {g: f"g{i + 1}" for i, g in enumerate(order)}
    landed["groups"] = [dict(g, id=names.get(g["id"], g["id"]), members=[names.get(m, m) for m in g["members"]])
                        for g in landed["groups"]]
    landed["picks"] = {names.get(g, g): k for g, k in picks.items()}
    landed = themes.normalise(landed)
    version = {"cards": landed["cards"], "groups": landed["groups"], "discarded": [], "picks": landed["picks"]}
    version["quoted"] = themes_ai.quoted_of(version["picks"], read["quotes"])
    if built["reasons"]:
        version["ai"] = {"discarded": {k: why for k, why in built["reasons"].items() if why}}
    return version


def carried_stacks(built: dict, source: dict) -> None:
    """The stacks of `source`, the board a new one keeps the layout of, put into `built`'s, each with
    its top: a statement under a top stays under it when the structure names it nowhere, in no label,
    not under not_placed and in none of its own stacks, and the top is not itself stacked there."""
    named = set(built["reasons"]) | {k for t, ks in built["stacks"].items() for k in [t, *ks]}

    def walk(item: dict) -> None:
        named.update(item["members"])
        for s in item["subs"]:
            walk(s)

    for pet in built["pets"]:
        walk(pet)
    inside = {k for ks in built["stacks"].values() for k in ks}
    for top, keys in (source.get("stacks") or {}).items():
        if top in inside:
            continue
        kept = [k for k in keys if k not in named]
        if kept:
            built["stacks"][top] = built["stacks"].get(top, []) + kept


def board_note(tool: str, request: str, counts: dict, when: str, own: str = "") -> str:
    """A board made in a conversation, said in its note: who made it, when, for what, and its counts."""
    said = (f"Made by {tool} in a conversation on {cli.when_said(when)}, for the request '{themes_ai.one_line(request)}'. "
            f"{cli.plural(counts['pets'], 'PET')}, {counts['placed']} placed, {counts['left']} not placed.")
    return said + (f" Its note: {own}" + ("" if own[-1:] in ".?!" else ".") if own else "")


def mark(args, when: str, made_from: str = "") -> dict:
    """Who made a board in a conversation, the tool and his request, and `from`, the board it came
    from."""
    out = {"by": "agent", "tool": themes_ai.one_line(args.tool) or cli.TOOL, "request": themes_ai.one_line(args.note), "at": when}
    # a teammate's suggestion accepted (wtsuggest, 10 November 2026): by the member who suggested it, and who accepted
    member = getattr(args, "_member", None)
    if isinstance(member, dict):
        out.update(by="member", **{k: str(member.get(k) or "") for k in themes.MEMBER_KEYS})
    if made_from:
        out["from"] = made_from
    return out


def source_of(data: dict | None) -> str:
    """What an agent's new board came from: the board on the canvas by its name, or all statements on a
    case with no board yet."""
    board = themes.current_version(data)
    return str(board.get("name") or themes.FIRST_NAME) if board else themes_ai.FROM_ALL


def cmd_board_new(p: Project, args) -> tuple:
    if not themes_ai.one_line(args.note) and not args.dry_run:
        raise cli.Refused(_w("NO_REQUEST"))
    return make_board(p, args, cli.read_spec(args.source))


def make_board(p: Project, args, spec, wanted: str = "", fresh: bool = False) -> tuple:
    """A new board from a plain structure, as `board new` makes one: named `wanted` when given, kept clear of
    every other name, else the next Board N, and laid out afresh with `fresh` (a table's PETs, `board import`)."""
    b = p.case(args.case)
    book = Path(b["workbook"])
    with wb_mod.case_held(book, boards=True):
        read = themes.read_cards(book)
        sids, keys = ids_of(read)
        data = load_board_file(book)
        built = build_board(spec, read, sids, keys)
        asked = FRESH if fresh else themes_ai.one_line(getattr(args, "layout", None))
        source = None if asked.lower() == FRESH else pick_board(data, asked) if asked else themes.current_version(data)
        version = carry_layout(built, read, source) if source is not None else None
        laid = str(source.get("name")) if version is not None else ""
        version = version or lay_board(built, read)
        if laid:
            # a board kept from another's layout keeps that board's stacks, each with its top, for the
            # statements the structure names nowhere
            carried_stacks(built, themes.follow(source, read["cards"], read["quotes"]))
        if built["stacks"]:
            version["stacks"] = built["stacks"]
        parents = themes.parents_of(version["groups"])
        placed = sum(1 for k in version["cards"] if k in parents)
        stacked = {k for keys in built["stacks"].values() for k in keys}
        left = [k for k in version["cards"] if k not in parents and k not in stacked]
        counts = {"pets": len(built["pets"]), "placed": placed, "left": len(left), "stacked": len(stacked)}
        tops = i18n.t("cli.n.top", n=len(built["stacks"]))
        stacked_said = i18n.t("cli.board_new.stacked_under", n_stacked=len(stacked), tops=tops) if stacked else ""
        name = themes.board_name(themes.boards_of(data), wanted) if wanted else themes.proposal_name(themes.boards_of(data))
        when = now_iso()
        made_from = source_of(data)
        version["made"] = mark(args, when, made_from)
        note = board_note(version["made"]["tool"], args.note, counts, when, built["note"])
        why = sum(1 for k in left if built["reasons"].get(k))
        said = (i18n.t("cli.board_new.placed_left_in", pets=i18n.t("cli.n.pet", n=counts['pets']), statements=i18n.t("cli.n.statement", n=placed), n_left=len(left), not_placed=NOT_PLACED, v_=i18n.t("cli.board_new.of_them_with_a_reason", why=why) if left else '', stacked_said=stacked_said))
        said += (i18n.t("cli.board_new.it_keeps_the_layout_of_for", laid=laid) if laid
                 else i18n.t("cli.board_new.it_is_laid_out_afresh"))
        dropped = built["dropped"]
        if args.dry_run:
            text = i18n.t("cli.board_new.dry_run_nothing_was_written_it", name=name, case=b['case'], made_from=made_from, said=said)
            lines = [text] + [x for x in (dropped_line(dropped, True),) if x]
            return {"dry_run": True, "case": b["case"], "name": name, "from": made_from, "counts": counts, "note": note,
                    "board": version, "layout": laid or FRESH, "dropped_picks": dropped, "said": " ".join(lines)}, lines
        # no empty Board 1 first on a case with no themes file, so the board is the one its dry run names
        answer = themes.version_op(book, themes.PROPOSE, {"version": version, "note": note, "seed": False, "name": name},
                                   case_name(book))
    made = answer["version"]
    others = [x["name"] for x in answer["versions"] if x["id"] != made["id"]]
    text = (i18n.t("cli.board_new.made_on_from_it_is_the", name=made['name'], case=b['case'], made_from=made_from, said=said)
            + (i18n.t("cli.board_new.as_before", list=', '.join(others), v_='is' if len(others) == 1 else 'are') if others else i18n.t("cli.board_new.nothing_else_changed")))
    lines = [text] + [x for x in (dropped_line(dropped, False),) if x]
    return {"case": b["case"], "id": made["id"], "name": made["name"], "from": made_from, "counts": counts, "note": note,
            "layout": laid or FRESH, "dropped_picks": dropped, "said": " ".join(lines)}, lines


# ------------------------------------------------------------ a table of PETs, and of LPETs
# (ayabuild34, 9 November 2026, the Ayahuasca plan's builds 3 and 4, Adam, 9 November about 13:40)

IMPORTED = "From Excel"


def table_file(p: Project, given) -> Path:
    """A table named by its path from the project's folder or in full."""
    path = Path(str(given or "")).expanduser()
    return path if path.is_absolute() else Path(p.root) / path


def table_read(p: Project, args) -> tuple[Path, list, list, str]:
    path = table_file(p, args.source)
    try:
        heads, rows, sheet = table_mod.read_table(path, getattr(args, "sheet", None))
    except table_mod.TableError as exc:
        raise cli.Refused(str(exc)) from None
    return path, heads, rows, sheet


def from_said(path: Path, sheet: str) -> str:
    return i18n.t("cli.table_import.from_sheet", file=path.name, sheet=sheet) if sheet else path.name


def import_row_line(m: dict) -> str:
    """One row of a table of PETs as its import says it: how it matched, and where."""
    where = (i18n.t("cli.board_import.where", sheet=m["sheet"], time=m["time"]) if m["time"]
             else i18n.t("cli.board_import.where_row", sheet=m["sheet"], row=m["passage"])) if m["sheet"] else ""
    said = {"row": m["row"], "statement": m["statement"], "where": where, "was": m["was"],
            "ratio": f"{m['ratio']:.2f}" if m["ratio"] is not None else "", "by": m["by"], "of": m.get("of", "")}
    if m["how"] in ("fuzzy", "rewritten") and m["why"] == "interviewer":
        return i18n.t("cli.board_import.row.kept_interviewer", **said)
    if m["how"] == "skipped" and m["why"] == "nowhere":
        return i18n.t("cli.board_import.row.nowhere", **said)
    if m["how"] == "added" and m.get("no_quote"):
        return i18n.t("cli.board_import.row.added_no_quote", **said)
    say = {"added": lambda: i18n.t("cli.board_import.row.added", **said),
           "duplicate": lambda: i18n.t("cli.board_import.row.duplicate", **said),
           "exact": lambda: i18n.t("cli.board_import.row.exact", **said),
           "fuzzy": lambda: i18n.t("cli.board_import.row.fuzzy", **said),
           "rewritten": lambda: i18n.t("cli.board_import.row.rewritten", **said),
           "skipped": lambda: i18n.t("cli.board_import.row.skipped", **said)}
    return say[m["how"]]()


def cmd_board_import(p: Project, args) -> tuple:
    """A board of PETs made from his own table of them (`table_import`): each row matched to a statement at the
    timepoint, the statements whose wording the table changed rewritten and those it adds written by `turn write`'s
    own code, each with History, then the board made by `board new`'s, named as asked, laid out afresh, everything
    else waiting in Not placed. The dry run lists every row's match and writes nothing."""
    if not themes_ai.one_line(args.note) and not args.dry_run:
        raise cli.Refused(_w("NO_REQUEST"))
    b = p.case(args.case)
    book = Path(b["workbook"])
    path, heads, rows, sheet = table_read(p, args)
    try:
        trows = table_mod.pet_rows(heads, rows, path.name)
    except table_mod.TableError as exc:
        raise cli.Refused(str(exc)) from None
    read = themes.read_cards(book)
    turns = [t for s in read["sheets"] for t in turns_of(book, s)[0]]
    interviewer = str(srv.config().get("interviewer") or "")
    add = (getattr(args, "unmatched", None) or "skip") == "add"
    matched = table_mod.match_pets(trows, turns, interviewer, add)
    counted = table_mod.counts(matched)
    tps = routes.project_timepoints(book)
    n = routes.board_timepoint(book, getattr(args, "timepoint", None))
    at = i18n.t("cli.board_import.at", label=tps[n - 1]["label"]) if n else ""
    wanted = themes_ai.one_line(getattr(args, "name", None)) or IMPORTED
    said_counts = i18n.t("cli.board_import.counts", counted, rows=i18n.t("cli.n.row", n=counted["rows"]))
    own_note = i18n.t("cli.board_import.note", source=from_said(path, sheet), counts=said_counts)
    spec, left_out = table_mod.board_spec(matched, own_note)
    row_lines = [import_row_line(m) for m in matched]
    left_lines = [i18n.t("cli.board_import.pet_left_out", title=t) for t in left_out]
    writes = table_mod.passage_writes(matched)
    out = {"case": b["case"], "timepoint": n, "file": str(path), "sheet": sheet, "counts": counted,
           "rows": [{k: m.get(k) for k in ("row", "pet", "sub", "statement", "location", "quote", "how", "ratio", "key",
                                           "was", "by", "sheet", "passage", "time", "of", "why")} for m in matched],
           "left_out": left_out}
    if args.dry_run:
        data = load_board_file(book)
        name = themes.board_name(themes.boards_of(data), wanted)
        placed = sum(1 for m in matched if m["how"] in ("exact", "fuzzy", "rewritten", "added"))
        total = len(read["cards"]) + counted["added"]
        text = i18n.t("cli.board_import.dry", source=from_said(path, sheet), counts=said_counts, name=name,
                      case=b["case"], at=at, pets=i18n.t("cli.n.pet", n=len(spec["pets"])),
                      statements=i18n.t("cli.n.statement", n=placed), left=total - placed,
                      passages=i18n.t("cli.n.passage", n=len(writes)))
        lines = [text] + row_lines + left_lines
        return dict(out, dry_run=True, name=name, placed=placed, not_placed=total - placed, said=text), lines
    if not spec["pets"]:
        raise cli.Refused(i18n.t("cli.board_import.nothing_placed", source=from_said(path, sheet)),
                          i18n.t("cli.said.nothing_was_written"))
    # each passage the table changes written as an edit of it, its statements reworded in their places by their
    # keys so every board's cards follow them, and the new ones after them with their quotes
    edited = []
    for (sh, row), change in writes.items():
        turn = next(t for t in turns if t["sheet"] == sh and t["row"] == row)
        pairs = [{"statement": change["reword"].get(i, s), "quote": turn["places"][i] if i < len(turn["places"]) else "",
                  "key": themes.card_key(sh, row, i)} for i, s in enumerate(turn["statements"])]
        for i, a in enumerate(change["add"]):
            pairs.append({"statement": a["m"]["statement"], "quote": a["quote"]})
            a["m"]["key"] = themes.card_key(sh, row, len(turn["statements"]) + i)
        one = argparse.Namespace(command="turn", act="write", json=True, case=args.case, sheet=sh, row=str(row),
                                 source={"pairs": pairs}, note=args.note, tool=args.tool, dry_run=False)
        done, _lines = turn_write(p, one)
        edited.append({"sheet": sh, "row": row, "backup": done.get("backup"), "written": done.get("written")})
    spec, left_out = table_mod.board_spec(matched, own_note)
    made, made_lines = make_board(p, args, spec, wanted, fresh=True)
    text = i18n.t("cli.board_import.made", name=made["name"], case=b["case"], at=at, source=from_said(path, sheet),
                  counts=said_counts, passages=i18n.t("cli.n.passage", n=len(edited)))
    out.update(id=made["id"], name=made["name"], board=made, edited=edited,
               rows=[dict(r, key=m["key"]) for r, m in zip(out["rows"], matched)])
    return dict(out, said=text), [text] + made_lines + row_lines + left_lines


def cmd_gets_import(p: Project, args) -> tuple:
    """A participant's LPETs made from his own table of them (`table_import`): a new LPETs board, named as asked,
    each row an LPET with its title, its description and a note of a paragraph for each timepoint, the PETs its
    cells' quotes and words match proposed as its members for him to confirm on the canvas, through `gets new`'s and
    `gets apply`'s own code, every other card waiting in Not placed. The dry run lists each LPET and the PETs
    proposed for it with why, and writes nothing."""
    if not getattr(args, "lpets", None):
        raise cli.Refused(i18n.t("cli.gets_import.lpets_only"))
    gets_request(args)
    path, heads, rows, sheet = table_read(p, args)
    tps = list(p.books)
    labels = {t["case"]: t.get("cite") or t["case"] for t in tps}
    try:
        lrows = table_mod.lpet_rows(heads, rows, tps, path.name)
    except table_mod.TableError as exc:
        raise cli.Refused(str(exc)) from None
    book = Path(tps[0]["workbook"])
    who = case_name(book)
    wanted = themes_ai.one_line(getattr(args, "name", None)) or IMPORTED
    with locks.root(p.root):
        data, _cases, _disk, _taken = gets_mod.assemble(p.root, p.books, now_iso())
        name = themes.board_name(themes.boards_of(data), wanted)
    proposed = table_mod.propose(lrows, {t["case"]: table_mod.pets_at(data, t["case"]) for t in tps})
    members = sum(len(r["members"]) for r in proposed)
    unmatched = [r["title"] for r in proposed if not r["members"]]
    lines = []
    for r in proposed:
        if not r["members"]:
            lines.append(i18n.t("cli.gets_import.lpet_none", title=r["title"]))
        else:
            lines.append(i18n.t("cli.gets_import.lpet", title=r["title"], pets=i18n.t("cli.n.pet", n=len(r["members"]))))
        for h in r["members"]:
            by = {"quote": lambda **k: i18n.t("cli.gets_import.by_quote", **k),
                  "words": lambda **k: i18n.t("cli.gets_import.by_words", **k)}[h["by"]]
            lines.append(by(card=h["card"], pet=h["pet"], at=labels.get(h["timepoint"]),
                            said=h["said"], statement=h["statement"]))
        for h in r["also"]:
            lines.append(i18n.t("cli.gets_import.taken", card=h["card"], pet=h["pet"], other=h["taken_by"]))
        if r["unmatched"] and r["members"]:
            lines.append(i18n.t("cli.gets_import.cells_unmatched", at=listed([labels.get(t, t) for t in r["unmatched"]])))
    head = {"source": from_said(path, sheet), "lpets": i18n.t("cli.n.lpet", n=len(proposed)),
            "members": i18n.t("cli.n.pet", n=members), "none": len(unmatched), "name": name, "case": who}
    out = {"case": who, "file": str(path), "sheet": sheet, "name": name,
           "lpets": [{"row": r["row"], "title": r["title"], "description": r["description"],
                      "note": table_mod.note_of(r, labels),
                      "members": [{k: h[k] for k in ("card", "pet", "timepoint", "by", "said", "statement", "key")}
                                  for h in r["members"]],
                      "also": [{k: h[k] for k in ("card", "pet", "timepoint", "taken_by")} for h in r["also"]],
                      "unmatched": r["unmatched"]} for r in proposed],
           "proposed": members, "unmatched": unmatched}
    if args.dry_run:
        text = i18n.t("cli.gets_import.dry", **head)
        return dict(out, dry_run=True, said=text), [text] + lines
    with locks.root(p.root):
        gets_op(p, "new", {"name": name})
    ops = []
    for i, r in enumerate(proposed):
        ref = f"lpet{i + 1}"
        ops.append({"op": "make", "ref": ref, "title": r["title"], "inside": None,
                    "members": [h["card"] for h in r["members"]]})
        if r["description"]:
            ops.append({"op": "describe", "label": ref, "description": r["description"]})
    one = copy.copy(args)
    one.board, one.ops, one.dry_run = name, {"operations": ops}, False
    applied, _lines = cmd_gets_apply(p, one)
    made = list(applied.get("made") or [])
    # each LPET's note, a paragraph for each timepoint headed by its label, which a revise's one-paragraph note
    # cannot hold, written on the board the change left under the same lock as every GETs write
    notes = {gid: table_mod.note_of(r, labels) for gid, r in zip(made, proposed)}
    with locks.root(p.root):
        held = gets_mod.load(p.root) or {}
        board = next((x for x in gets_mod.boards_of(held) if str(x.get("name")) == name), None)
        if board is not None and any(notes.values()):
            for g in board.get("groups") or []:
                if notes.get(g["id"]):
                    g["note"] = notes[g["id"]]
            when = now_iso()
            board["updated"] = when
            if isinstance(board.get("changed"), dict):
                board["changed"]["hash"] = themes.state_hash(themes.made_state(gets_mod.normal(board, held)))
            gets_mod.write(p.root, gets_mod._file(held, when))
    text = i18n.t("cli.gets_import.made", **head)
    out.update(board=applied.get("board"), made=made, revision=applied.get("revision"))
    for item, gid in zip(out["lpets"], made):
        item["id"] = gid
    return dict(out, said=text), [text] + lines


# ------------------------------------------------------------ board current

CURRENT = "Marked the Current board"


def cmd_board_current(p: Project, args) -> tuple:
    """Mark a board as the Current board, the one he is going with, through `themes.version_op`'s
    `choose`, as the board menu's Mark as current does. The board as it stands is kept first in its
    History, named for the mark and his request, which records the change there. A board marked
    already writes nothing."""
    if not themes_ai.one_line(args.note) and not args.dry_run:
        raise cli.Refused(_w("NO_REQUEST"))
    b = p.case(args.case)
    book = Path(b["workbook"])
    with wb_mod.case_held(book, boards=True):
        data = load_board_file(book)
        board = pick_board(data, args.board)
        boards = themes.boards_of(data)
        name, vid = board.get("name"), str(board.get("id"))
        was = themes.chosen_of(data)
        before = next((x.get("name") for x in boards if str(x.get("id")) == was), None) if was else None
        out = {"case": b["case"], "board": vid, "name": name, "was": was}
        if was == vid:
            text = i18n.t("cli.board_current.is_the_current_board_already_nothing", name=name)
            return dict(out, changed=False, said=text), [text]
        instead = i18n.t("cli.board_current.in_place_of", before=before) if before else ""
        if args.dry_run:
            text = i18n.t("cli.board_current.dry_run_nothing_was_written_it", name=name, case=b['case'], instead=instead)
            return dict(out, dry_run=True, said=text), [text]
        when = now_iso()
        cut = themes_ai.revision_name(args.note)[len(themes_ai.BEFORE):]
        made = themes.add_revision(board, name=f"{CURRENT}: {cut}", at=when)
        made["made"] = mark(args, when)
        current = str(data.get("current") or vid)
        themes.write(book, themes._file(book, case_name(book), data, boards, current, when))
        themes.version_op(book, "choose", {"id": vid}, case_name(book))
    text = (i18n.t("cli.board_current.is_now_the_current_board_on", name=name, case=b['case'], instead=instead, name2=made["name"]))
    return dict(out, changed=True, revision=themes.revision_summary(made), said=text), [text]


# ------------------------------------------------------- board housekeeping
#
# The board menu's own acts, each through `themes.version_op` as the app makes them: a board put on
# the canvas, renamed, duplicated or deleted. Each takes his request and a dry run, as every write does.

RENAMED = "Renamed from"


def housekeeping(p: Project, args):
    """The case, its workbook, its themes file and the board a housekeeping command names, his
    request asked for first unless it is a dry run."""
    if not themes_ai.one_line(args.note) and not args.dry_run:
        raise cli.Refused(_w("NO_REQUEST"))
    b = p.case(args.case)
    book = Path(b["workbook"])
    return b, book


def on_canvas(data: dict | None) -> dict | None:
    return themes.current_version(data)


def cmd_board_canvas(p: Project, args) -> tuple:
    """Put a board on the canvas, as choosing it in the board menu does, through `version_op`'s
    `switch`. Nothing on any board changes, and the board on the canvas already writes nothing."""
    b, book = housekeeping(p, args)
    with wb_mod.case_held(book, boards=True):
        data = load_board_file(book)
        board = pick_board(data, args.board)
        name, vid = board.get("name"), str(board.get("id"))
        was = on_canvas(data) or {}
        out = {"case": b["case"], "board": vid, "name": name, "was": was.get("id")}
        if str(was.get("id")) == vid:
            text = i18n.t("cli.board_canvas.is_on_the_canvas_already_nothing", name=name)
            return dict(out, changed=False, said=text), [text]
        if args.dry_run:
            text = i18n.t("cli.board_canvas.dry_run_nothing_was_written_it", name=name, case=b['case'], get=was.get('name'))
            return dict(out, dry_run=True, said=text), [text]
        themes.version_op(book, "switch", {"id": vid}, case_name(book))
    text = (i18n.t("cli.board_canvas.is_now_on_the_canvas_on", name=name, case=b['case'], get=was.get('name')))
    return dict(out, changed=True, said=text), [text]


def cmd_board_rename(p: Project, args) -> tuple:
    """Rename a board, as Rename in the board menu does, through `version_op`'s `rename`. The board as
    it stands is kept first in its History, named for the old name and his request."""
    b, book = housekeeping(p, args)
    wanted = " ".join(str(args.name or "").split())
    if not wanted:
        raise cli.Refused(i18n.t("cli.board_rename.give_the_boards_new_name"))
    with wb_mod.case_held(book, boards=True):
        data = load_board_file(book)
        board = pick_board(data, args.board)
        name, vid = str(board.get("name")), str(board.get("id"))
        out = {"case": b["case"], "board": vid, "was": name, "name": wanted}
        if wanted == name:
            text = i18n.t("cli.board_rename.is_called_that_already_nothing_was", name=name)
            return dict(out, changed=False, said=text), [text]
        if any(" ".join(str(x.get("name") or "").split()).lower() == wanted.lower() and x is not board
               for x in themes.boards_of(data)):
            raise cli.Refused(i18n.t("cli.board_rename.another_board_is_called_already_so", wanted=wanted))
        if args.dry_run:
            text = i18n.t("cli.board_rename.dry_run_nothing_was_written_it", name=name, case=b['case'], wanted=wanted)
            return dict(out, dry_run=True, said=text), [text]
        when = now_iso()
        cut = themes_ai.revision_name(args.note)[len(themes_ai.BEFORE):]
        made = themes.add_revision(board, name=f"{RENAMED} {name}: {cut}", at=when)
        made["made"] = mark(args, when)
        boards = themes.boards_of(data)
        themes.write(book, themes._file(book, case_name(book), data, boards, str(data.get("current") or vid), when))
        try:
            themes.version_op(book, "rename", {"id": vid, "name": wanted}, case_name(book))
        except WorkbookError as exc:
            raise cli.Refused(str(exc))
    text = i18n.t("cli.board_rename.renamed_on_as_it_is_recorded", name=name, case=b['case'], wanted=wanted, name2=made['name'])
    return dict(out, changed=True, revision=themes.revision_summary(made), said=text), [text]


def cmd_board_duplicate(p: Project, args) -> tuple:
    """Duplicate a board, as Duplicate in the board menu does, through `version_op`'s `duplicate`:
    a copy under a new name, its own note saying who made it for which request, with no history,
    put on the canvas. The board copied is left as it was."""
    b, book = housekeeping(p, args)
    with wb_mod.case_held(book, boards=True):
        data = load_board_file(book)
        board = pick_board(data, args.board)
        name = str(board.get("name"))
        boards = themes.boards_of(data)
        wanted = " ".join(str(getattr(args, "name", "") or "").split())
        copy_name = themes._free_name(boards, wanted or f"{name} copy")
        when = now_iso()
        note = (f"Duplicated from {name} by {themes_ai.one_line(args.tool) or cli.TOOL} in a conversation on "
                f"{cli.when_said(when)}, for the request '{themes_ai.one_line(args.note)}'.")
        out = {"case": b["case"], "from": str(board.get("id")), "from_name": name, "name": copy_name}
        if args.dry_run:
            text = i18n.t("cli.board_duplicate.dry_run_nothing_was_written_it", name=name, case=b['case'], copy_name=copy_name)
            return dict(out, dry_run=True, said=text), [text]
        answer = themes.version_op(book, "duplicate", {"id": str(board.get("id")), "name": copy_name, "note": note},
                                   case_name(book))
    made = next((x for x in answer["versions"] if x["name"] == copy_name), {})
    text = i18n.t("cli.board_duplicate.copied_on_as_which_is_now", name=name, case=b['case'], copy_name=copy_name)
    return dict(out, id=made.get("id"), note=note, said=text), [text]


def cmd_board_fresh(p: Project, args) -> tuple:
    """A new board with no PETs, as New board in the board menu does, through `version_op`'s `new`, put on
    the canvas: with `--start empty` every statement waits in the sidebar's Not placed, and with `--start
    canvas` every statement lies on the canvas as a pile in the middle, in no PET yet (Adam, 20 October).
    His other boards are left as they were."""
    b, book = housekeeping(p, args)
    start = args.start if args.start in themes.STARTS else "empty"
    with wb_mod.case_held(book, boards=True):
        data = load_board_file(book)
        # a participant with no board yet is given Board 1 first, the board an open offers (see `themes.version_op`),
        # so the new one is named past it and the answer names the board made (30 October)
        boards = themes.boards_of(data) or [themes.blank_version([])]
        name = themes.board_name(boards, " ".join(str(getattr(args, "name", "") or "").split()))
        how = (i18n.t("cli.board_fresh.every_statement_waiting_in_the_sidebars") if start == "empty"
               else i18n.t("cli.board_fresh.every_statement_on_the_canvas_as"))
        out = {"case": b["case"], "name": name, "start": start}
        if args.dry_run:
            text = i18n.t("cli.board_fresh.dry_run_nothing_was_written_it", name=name, case=b['case'], how=how)
            return dict(out, dry_run=True, said=text), [text]
        answer = themes.version_op(book, "new", {"name": name, "start": start}, case_name(book))
    made = next((x for x in answer["versions"] if x["name"] == name), {})
    others = [x["name"] for x in answer["versions"] if x["id"] != made.get("id")]
    text = (i18n.t("cli.board_fresh.made_on_it_is_the_board", name=name, case=b['case'], how=how)
            + (i18n.t("cli.board_fresh.and_as_before", list=', '.join(others), v_='is' if len(others) == 1 else 'are') if others else "."))
    return dict(out, id=made.get("id"), said=text), [text]


def cmd_board_delete(p: Project, args) -> tuple:
    """Delete a board, as Delete in the board menu does, through `version_op`'s `delete`, the last
    board refused. Deleting has no History to undo it, so the board as it stood, its History with it,
    is copied first into the case's `_Archive/` as JSON, which says where."""
    b, book = housekeeping(p, args)
    with wb_mod.case_held(book, boards=True):
        data = load_board_file(book)
        board = pick_board(data, args.board)
        boards = themes.boards_of(data)
        name, vid = str(board.get("name")), str(board.get("id"))
        if len(boards) == 1:
            raise cli.Refused(i18n.t("cli.board_delete.the_last_board_cannot_be_deleted"))
        marks = [w for w, on in ((i18n.t("cli.said.the_current_board"), themes.chosen_of(data) == vid),
                                 (i18n.t("cli.said.on_the_canvas"), str((on_canvas(data) or {}).get("id")) == vid)) if on]
        was = f", {' and '.join(marks)}," if marks else ""
        out = {"case": b["case"], "board": vid, "name": name, "current": themes.chosen_of(data) == vid}
        if args.dry_run:
            text = (i18n.t("cli.board_delete.dry_run_nothing_was_written_it", name=name, was=was, case=b['case']))
            return dict(out, dry_run=True, said=text), [text]
        archive = wb_mod.case_folder(book) / "_Archive"
        archive.mkdir(parents=True, exist_ok=True)
        stem = f"{book.stem} board {name.translate(themes.UNSAFE)} (deleted {datetime.now():%Y%m%d-%H%M})"
        kept, n = archive / f"{stem}.json", 2
        while kept.exists():
            kept, n = archive / f"{stem}-{n}.json", n + 1
        kept.write_text(json.dumps(board, ensure_ascii=False, indent=1), encoding="utf-8", newline="\n")
        answer = themes.version_op(book, "delete", {"id": vid}, case_name(book))
    shown = (answer.get("version") or {}).get("name")
    text = (i18n.t("cli.board_delete.deleted_on_a_copy_of_it", name=name, was=was, case=b['case'], name2=kept.name) + (i18n.t("cli.said.is_on_the_canvas", shown=shown) if shown else ""))
    return dict(out, backup=kept.name, said=text), [text]


def cmd_board_complete(p: Project, args) -> tuple:
    """A participant's PETs marked complete on the Current board, as Mark PETs complete at the foot of the
    board menu does, or with --reopen reopened, as Reopen PETs does, through `version_op`'s `complete` and
    `reopen` under the case's lock, refused in the route's words while no board is marked current. Only the
    mark at the top of the themes file changes, as the page's call leaves it: no board and no History, and a
    mark already there keeps its first time (26 October, petsdone)."""
    b, book = housekeeping(p, args)
    op = "reopen" if getattr(args, "reopen", False) else "complete"
    with wb_mod.case_held(book, boards=True):
        data = load_board_file(book)
        held = themes.complete_of(data)
        out = {"case": b["case"], "op": op, "was": held}
        if (op == "complete") == bool(held):
            text = (i18n.t("cli.board_complete.pets_are_marked_complete_already_on", case=b['case'], when=cli.when_said(held['at']), get=held.get('name')) if held else
                    i18n.t("cli.board_complete.pets_are_not_marked_complete_on", case=b['case']))
            return dict(out, changed=False, complete=held, said=text), [text]
        try:
            themes.version_op(book, op, {}, case_name(book), dry_run=True)
        except WorkbookError as exc:
            raise cli.Refused(str(exc)) from None
        if args.dry_run:
            chosen = themes.chosen_of(data)
            name = next((str(x.get("name")) for x in themes.boards_of(data) if str(x.get("id")) == chosen), None)
            text = (i18n.t("cli.board_complete.dry_run_nothing_was_written_it_2", name=name, case=b['case'])
                    if op == "complete" else
                    i18n.t("cli.board_complete.dry_run_nothing_was_written_it", case=b['case'], when=cli.when_said(held['at'])))
            return dict(out, dry_run=True, said=text), [text]
        themes.version_op(book, op, {}, case_name(book))
        now = themes.complete_of(themes.load(book))
    text = (i18n.t("cli.board_complete.marked_pets_complete_on_on", get=now.get('name'), case=b['case']) if op == "complete"
            else i18n.t("cli.board_complete.reopened_pets_on", case=b['case']))
    return dict(out, changed=True, complete=now, said=text), [text]


# ------------------------------------------------ a board's note and History (26 October)
#
# The PETs screen's board note (`/api/themes-versions`' `note`) and a board's History (`/api/themes-boards`:
# Save a revision, a revision on view, Restore, Copy to board), each through the route's own function,
# `themes.version_op` and `themes.board_op`, under the lock the route takes, its dry run the function's own
# (`dry_run`), so every check and refusal is the route's. What a write keeps in History is the page's, and
# the revision it keeps names the tool and his request, as every board write here does.

NOTED = "Board note changed"


def request_cut(args) -> str:
    """His request as a revision's name carries it, cut to one line."""
    return themes_ai.revision_name(args.note)[len(themes_ai.BEFORE):]


def revision_by(board: dict, rid: str) -> dict:
    """A revision of a board by its id, r3, refused in the route's words when its History has none."""
    said = " ".join(str(rid or "").split()).lower()
    found = next((r for r in themes.history_of(board) if str(r["id"]).lower() == said), None)
    if found is None:
        raise cli.Refused(themes.LOST)
    return found


def revision_line(r: dict) -> str:
    return f"  {r['id']}  {themes.when_said(r['at'])}  {r['name'] or ('Automatic' if r['auto'] else i18n.t('cli.revision_line.no_name'))}"


def stamp_pets(book: Path, vid: str, rid: str | None, args, changed: bool) -> None:
    """The tool and his request on the revision a board op kept, and with `changed` the board marked as
    changed in a conversation, as `board apply` marks it, so an open PETs screen says so."""
    when = now_iso()
    data = load_board_file(book) or {}
    boards = themes.boards_of(data)
    board = next((x for x in boards if str(x.get("id")) == vid), None)
    if board is None:
        return
    for r in themes.history_of(board):
        if rid and str(r["id"]) == rid:
            r["made"] = mark(args, when)
    if changed:
        board["changed"] = mark(args, when)
        board["changed"]["hash"] = themes.state_hash(themes.made_state(themes.normalise(board)))
    themes.write(book, themes._file(book, case_name(book), data, boards, str(data.get("current") or vid), when))


def cmd_board_note(p: Project, args) -> tuple:
    """A board's note set, or taken off with an empty one, as the board note on the PETs screen sets it,
    through `version_op`'s `note`. The board as it stands is kept first in its History, named for the note
    and his request."""
    b, book = housekeeping(p, args)
    words = str(args.text or "").strip()
    with wb_mod.case_held(book, boards=True):
        data = load_board_file(book)
        board = pick_board(data, args.board)
        name, vid = str(board.get("name")), str(board.get("id"))
        was = str(board.get("note") or "").strip()
        out = {"case": b["case"], "board": vid, "name": name, "was": was, "note": words}
        if words == was:
            text = i18n.t("cli.board_note.s_note_reads_that_already_nothing", name=name)
            return dict(out, changed=False, said=text), [text]
        try:
            themes.version_op(book, "note", {"id": vid, "note": words}, case_name(book), dry_run=True)
        except WorkbookError as exc:
            raise cli.Refused(str(exc))
        how = i18n.t("cli.board_note.take_s_note_off", name=name) if not words else i18n.t("cli.board_note.set_s_note_to_2", name=name, words=words)
        if args.dry_run:
            text = i18n.t("cli.board_note.dry_run_nothing_was_written_it", how=how, case=b['case'])
            return dict(out, dry_run=True, said=text), [text]
        when = now_iso()
        made = themes.add_revision(board, name=f"{NOTED}: {request_cut(args)}", at=when)
        made["made"] = mark(args, when)
        themes.write(book, themes._file(book, case_name(book), data, themes.boards_of(data),
                                        str(data.get("current") or vid), when))
        themes.version_op(book, "note", {"id": vid, "note": words}, case_name(book))
    done = i18n.t("cli.board_note.took_s_note_off", name=name) if not words else i18n.t("cli.board_note.set_s_note_to", name=name, words=words)
    text = i18n.t("cli.board_note.on_it_is_recorded_in_its", done=done, case=b['case'], name=made['name'])
    return dict(out, changed=True, revision=themes.revision_summary(made), said=text), [text]


def cmd_board_history(p: Project, args) -> tuple:
    """A board's History, its revisions newest first as the History tab lists them, and with --revision one
    of them as `board show` sets a board out, as the History tab shows one on view. Only reads."""
    b = p.case(args.case)
    book = Path(b["workbook"])
    data = load_board_file(book)
    board = pick_board(data, args.board)
    name, vid = str(board.get("name")), str(board.get("id"))
    listed = themes.history_list(board)
    if not getattr(args, "revision", None):
        lines = [i18n.t("cli.board_history.s_history_on_newest_first", name=name, case=b['case'], revisions=i18n.t("cli.n.revision", n=len(listed)))]
        lines += [revision_line(r) for r in listed] or [i18n.t("cli.said.none_yet_one_is_kept_every")]
        return {"case": b["case"], "board": vid, "name": name, "history": listed}, lines
    revision = revision_by(board, args.revision)
    try:
        themes.board_op(book, "view", {"id": vid, "revision": revision["id"]}, case_name(book))
    except WorkbookError as exc:
        raise cli.Refused(str(exc))
    read = themes.read_cards(book)
    sids, _ = ids_of(read)
    shown = shown_board(read, dict(revision["state"], id=vid, name=name), sids, p.info["pet_labels"])
    summary = themes.revision_summary(revision)
    lines = [i18n.t("cli.board_history.s_revision_of", name=name, id=summary['id'], when=themes.when_said(summary['at']))
             + (f", {summary['name']}" if summary["name"] else "") + i18n.t("cli.board_history.restore_makes_it_the_board")]
    return dict(shown, case=b["case"], board=vid, revision=summary), lines + board_text(b["case"], shown)


def cmd_board_revision(p: Project, args) -> tuple:
    """Save a revision, as the board menu's and the History tab's Save a revision keep one, through
    `board_op`'s `revision`: the board as it stands kept in its History under --name, or his request.
    Nothing on the board changes."""
    b, book = housekeeping(p, args)
    with wb_mod.case_held(book, boards=True):
        data = load_board_file(book)
        board = pick_board(data, args.board)
        name, vid = str(board.get("name")), str(board.get("id"))
        called = " ".join(str(getattr(args, "name", "") or "").split()) or request_cut(args)
        try:
            done = themes.board_op(book, "revision", {"id": vid, "name": called}, case_name(book),
                                   dry_run=bool(args.dry_run))
        except WorkbookError as exc:
            raise cli.Refused(str(exc))
        out = {"case": b["case"], "board": vid, "name": name}
        if args.dry_run:
            text = i18n.t("cli.board_revision.dry_run_nothing_was_written_it", name=name, called=called)
            return dict(out, dry_run=True, said=text), [text]
        stamp_pets(book, vid, done["revision"]["id"], args, changed=False)
    text = i18n.t("cli.board_revision.kept_as_it_stands_in_its", name=name, case=b["case"], called=called)
    return dict(out, revision=done["revision"], said=text), [text]


def cmd_board_restore(p: Project, args) -> tuple:
    """Restore a revision, as the History tab's Restore does, through `board_op`'s `restore`: the board as it
    stands kept in its History first, "Before restoring 12:04", then the revision made the board, its
    statements following their words."""
    b, book = housekeeping(p, args)
    with wb_mod.case_held(book, boards=True):
        data = load_board_file(book)
        board = pick_board(data, args.board)
        name, vid = str(board.get("name")), str(board.get("id"))
        revision = revision_by(board, args.revision)
        try:
            done = themes.board_op(book, "restore", {"id": vid, "revision": revision["id"]}, case_name(book),
                                   dry_run=bool(args.dry_run))
        except WorkbookError as exc:
            raise cli.Refused(str(exc))
        when = themes.when_said(revision["at"])
        out = {"case": b["case"], "board": vid, "name": name, "restored": done["restored"]}
        if args.dry_run:
            text = (i18n.t("cli.board_restore.dry_run_nothing_was_written_it", name=name, when=when, case=b['case'], name2=done["revision"]["name"]))
            return dict(out, dry_run=True, said=text), [text]
        stamp_pets(book, vid, done["revision"]["id"], args, changed=True)
    text = (i18n.t("cli.board_restore.restored_s_revision_of_on_the", name=name, when=when, case=b['case'], name2=done["revision"]["name"]))
    return dict(out, revision=done["revision"], said=text), [text]


def label_named(groups: list[dict], said: str) -> str:
    """A label of a board by its id, g3, or its title, refused in one line when it has none."""
    words = " ".join(str(said or "").split()).lower()
    for g in groups:
        if str(g.get("id")).lower() == words or " ".join(str(g.get("label") or "").split()).lower() == words:
            return str(g.get("id"))
    raise cli.Refused(i18n.t("cli.label_named.no_label_called_on_that_board", said=said))


def cmd_board_copy(p: Project, args) -> tuple:
    """A label copied to another board, as Copy to board on a label does, through `board_op`'s `copy`, or
    from one of its board's revisions with --revision, onto the board it belongs to or another. The board
    it goes to keeps a revision first, "Before Mornings copied from Board 1", and is marked as changed in a
    conversation."""
    b, book = housekeeping(p, args)
    with wb_mod.case_held(book, boards=True):
        data = load_board_file(book)
        board = pick_board(data, args.board)
        target = pick_board(data, args.to)
        name, vid, to = str(board.get("name")), str(board.get("id")), str(target.get("id"))
        body = {"id": vid, "to": to}
        source = board
        if getattr(args, "revision", None):
            revision = revision_by(board, args.revision)
            body["revision"] = revision["id"]
            source = revision["state"]
        body["group"] = label_named(themes.normalise(source)["groups"], args.label)
        try:
            done = themes.board_op(book, "copy", body, case_name(book), dry_run=bool(args.dry_run))
        except WorkbookError as exc:
            raise cli.Refused(str(exc))
        c = done["copied"]
        out = {"case": b["case"], "board": vid, "name": name, "to": to, "copied": c}
        if args.dry_run:
            text = (i18n.t("cli.board_copy.dry_run_nothing_was_written_it", label=c['label'], from_=c['from'], to_name=c['to_name'], case=b["case"], name=done["revision"]["name"]))
            return dict(out, dry_run=True, said=text), [text]
        stamp_pets(book, to, done["revision"]["id"], args, changed=True)
    text = (i18n.t("cli.board_copy.copied_from_to_on_as", label=c['label'], from_=c['from'], to_name=c['to_name'], case=b['case'], group=c['group'], kept_line=kept_line(c['to_name'], done['revision']['name'])))
    return dict(out, revision=done["revision"], said=text), [text]


# -------------------------------------------------------------- board apply

def read_ops(spec, args) -> tuple[list, str]:
    """The operations of a change and his request: `{"request", "operations"}` or a bare list."""
    if isinstance(spec, dict):
        ops = next((spec[k] for k in ("operations", "ops", "changes") if isinstance(spec.get(k), list)), None)
        request = spec.get("request") or args.note
    else:
        ops, request = spec, args.note
    if not isinstance(ops, list) or not ops:
        raise cli.Refused(i18n.t("cli.read_ops.the_change_is_operations_each_one"))
    return ops, themes_ai.one_line(request)


def fresh_or_refused(spec, board: dict, show: str) -> None:
    """A change that carries `version`, the board's version as `show` gave it, refused with nothing
    written when the board holds another now, from the app or another write (19 October)."""
    seen = spec.get("version") if isinstance(spec, dict) else None
    if themes.stale_since(board, seen):
        raise cli.Refused(themes.STALE_WRITE.format(show=show))


def name_ids(ops: list, read: dict, keys: dict) -> list:
    """Every short id in the operations made the key it names, so revise's applier reads them."""
    def one(value):
        if isinstance(value, str):
            m = SID.match(value.strip())
            return keys.get(f"S{int(m.group(1))}", value) if m else value
        return value

    out = []
    for op in ops:
        if not isinstance(op, dict):
            out.append(op)
            continue
        op = dict(op)
        for field in ("items", "members", "item"):
            if isinstance(op.get(field), list):
                op[field] = [one(v) for v in op[field]]
            elif isinstance(op.get(field), str):
                op[field] = one(op[field])
        out.append(op)
    return out


def check_ops(ops: list, numbers: list[int] | None = None) -> list[str]:
    """What the applier lets through and a write from here does not: a new label with no title,
    which the applier calls Untitled, and the bin, said in the words an agent needs. `numbers` gives
    each operation the number it has in the whole change, when an order stood among them."""
    out = []
    for i, op in zip(numbers or range(1, len(ops) + 1), ops):
        kind = str(op.get("op") or "").lower() if isinstance(op, dict) else ""
        if kind == "make" and not themes_ai.clean_label(op.get("title") or op.get("label")):
            out.append(i18n.t("cli.check_ops.operation_makes_a_label_with_no", i=i))
        if kind == "delete":
            out.append(i18n.t("cli.check_ops.operation", i=i, no_delete=_w("NO_DELETE")))
    return out


def apply_ops(start: dict, ops: list, numbers: list[int] | None = None) -> tuple[dict, list, dict]:
    """The operations applied in order through `themes_ai.revise_ops`, whole or not at all: any one
    it refuses refuses the lot, each reason a line with the operation's number, the one `numbers`
    gives it in the whole change when an order stood among them."""
    numbers = numbers or list(range(1, len(ops) + 1))
    problems = check_ops(ops, numbers)
    after, applied, refused, info = themes_ai.revise_ops(start, ops)
    if refused and not problems:
        # the applier passes over what it refuses, so a run on each run of the first operations
        # tells which ones they were, each read on the board the ones before it left
        stood = 0
        for i in range(1, len(ops) + 1):
            trial = themes_ai.revise_ops(start, ops[:i])
            if len(trial[1]) > stood:
                stood = len(trial[1])
            else:
                problems.append(i18n.t("cli.apply_ops.operation", numbers=numbers[i - 1], trial=trial[2][-1]))
    if problems:
        raise cli.Refused(*problems, i18n.t("cli.said.nothing_was_written"))
    return after, applied, info


def kept_line(name: str, revision: str) -> str:
    """What the answer says of the revision kept before the change, which History and Restore undo."""
    return i18n.t("cli.kept_line.as_it_stood_is_kept_first", name=name, revision=revision)


def reasons_after(v: dict, ops: list, before: dict) -> dict:
    """The reasons kept under `ai` after a change: a statement now in a label loses its own, and one
    a move sent out to Not placed with a `reason` takes it."""
    parents = themes.parents_of(v["groups"])
    stacked = themes.stacked_keys(v)
    # a statement stacked loses its reason too, since its top stands for it
    reasons = {k: why for k, why in ((before.get("ai") or {}).get("discarded") or {}).items()
               if (k in v["discarded"] or k not in parents) and k not in stacked}
    for op in ops:
        if isinstance(op, dict) and str(op.get("op")).lower() == "move" and op.get("to") in (None, "", "null") and op.get("reason"):
            for k in op.get("items") or []:
                if k in v["cards"] and k not in parents and k not in stacked:
                    reasons[k] = " ".join(str(op["reason"]).split())
    return reasons


def sent_to_wait(start: dict, ops: list, applied: list, followed: dict) -> tuple[list, list[str], list[str]]:
    """What each move of a change to null does to the statements it names (30 October). One in a label, or
    lying loose on the canvas in no PET, goes to wait in the sidebar's Not placed, as Back to Not placed does
    on the canvas, and one waiting there already stays as it was. `ops` are the applier's operations,
    `applied` what it applied of them, one for each, from `start`, and `followed` the board they ran on.
    Answers `applied` with each such move naming only the statements and labels it took out, for the
    answer's words, then the statements sent to wait and those named that waited there already."""
    loose = {k for k, c in followed["cards"].items() if c.get(themes.LOOSE)}
    said, sent, already = [], [], []
    for i, op in enumerate(applied):
        kind = op.get("op")
        if kind == "move" and op.get("to") is None:
            # where everything stood as this move came to it, on the board the ones before it left
            before = themes_ai.revise_ops(start, ops[:i])[0] if i else start
            parents = themes.parents_of(before["groups"])
            labels = {g["id"] for g in before["groups"]}
            took = [k for k in op["items"] if k in labels or k in parents or k in loose]
            for k in op["items"]:
                into = None if k in labels else sent if k in took else already
                if into is not None and k not in into:
                    into.append(k)
            loose -= set(op["items"])
            if took:
                said.append(dict(op, items=took))
            continue
        # a statement a move or a make puts in a label is on the canvas no longer loose
        if kind == "move":
            loose -= set(op["items"])
        elif kind == "make":
            loose -= set(op.get("members") or [])
        said.append(op)
    return said, sent, already


ORDER = "order"


def is_order(op) -> bool:
    """An operation that sets an order, which the canvas keeps as where things stand, not as what
    holds what, so it runs here after the applier's and never through it."""
    return isinstance(op, dict) and themes_ai.one_line(op.get("op") or op.get("type")).lower() == ORDER


# the operations on stacks (19 October): a statement stacked under a better one, which then stands for it,
# one taken out again just below its stack, and one made the top of the stack it is in, and on a close
# pair (20 October): two statements marked Not the same, which the board then stops marking as a pair, and
# a pair so marked shown again
STACK_OPS = ("stack", "unstack", "top", "not_same", "show_again")
# the sidebar's (20 October, Adam's way A): statements set aside, as X does, put back to wait in Not placed,
# and every statement waiting in Not placed put on the canvas, as the sidebar's Put all on the board does.
# The bin's old names answer as Set aside's, so no agent that knew them breaks
SIDEBAR_OPS = {"set_aside": "set_aside", "discard": "set_aside", "bin": "set_aside",
               "put_back": "put_back", "unbin": "put_back", "restore": "put_back", "undiscard": "put_back",
               "put_all_on": "put_all_on", "place_all": "put_all_on"}
STACK_OPS = STACK_OPS + tuple(SIDEBAR_OPS)


def is_stack(op) -> bool:
    """An operation on a stack, which runs here after the applier's, on the board its changes left."""
    return isinstance(op, dict) and themes_ai.one_line(op.get("op") or op.get("type")).lower() in STACK_OPS


def listed(words: list[str]) -> str:
    """Words in a line, "S1, S2 and S3"."""
    return words[0] if len(words) == 1 else ", ".join(words[:-1]) + " and " + words[-1]


# where a command's own list of operations is called `listed`
listed_words = listed


# Arrange by participant on a GETs board (Adam, 19 October, way 2 of the drawings), as its board menu does it
ARRANGE = "arrange"


def is_arrange(op) -> bool:
    """`{"op": "arrange", "by": "participant"}`, which runs after the change's other operations and its
    orders, on the board they leave (see `gets.by_participant`)."""
    return isinstance(op, dict) and themes_ai.one_line(op.get("op") or op.get("type")).lower() == ARRANGE


# The toolbar's tools (21 October): a label's cards arranged a way, Grid, Column or Row, as Auto-arrange's
# menu does, and cards lined up or spread as Align and Spread do, each moving where things stand, so they
# run last, on the board the change and its orders leave
LAYOUT_OPS = ("arrange", "align", "spread")


def is_layout(op) -> bool:
    """`{"op": "arrange", "label": "g1", "way": "column"}`, `{"op": "align", "items": [...], "to": "left"}` or
    `{"op": "spread", "items": [...], "to": "across"}`. An arrange by participant on a GETs board is not one."""
    if not isinstance(op, dict):
        return False
    kind = themes_ai.one_line(op.get("op") or op.get("type")).lower()
    return kind in LAYOUT_OPS and not (kind == ARRANGE and "by" in op and "label" not in op)


def run_layouts(landed: dict, ops: list, refs: dict, resolve, name, problems: list, height=None) -> tuple[dict, list[str]]:
    """Each arrange, align and spread of a change, `ops` by its number in the change, done in turn on the
    board the rest left, through `themes.arrange` and `themes.align_items`: the board afterwards and what
    each did, said plainly, a line in `problems` for each that cannot stand. `resolve` gives a card's key
    from the name an agent gave it, and `name` says a label or a card as the answer names it."""
    said = []
    for n, op in ops:
        kind = themes_ai.one_line(op.get("op") or op.get("type")).lower()
        by_id = {g["id"]: g for g in landed["groups"]}
        how = themes_ai.one_line(op.get("way") or op.get("to") or ("grid" if kind == "arrange" else "")).lower()
        if kind == "arrange":
            label = refs.get(themes_ai.one_line(op.get("label")), themes_ai.one_line(op.get("label")))
            if label not in by_id:
                problems.append(i18n.t("cli.run_layouts.operation_names_which_is_not_a", n=n, get=op.get('label') or i18n.t("cli.run_layouts.no_label")))
                continue
            if how not in themes.ARRANGE_WAYS:
                problems.append(i18n.t("cli.run_layouts.operation_arranges_as_give_way_grid", n=n, how=how or 'nothing'))
                continue
            try:
                landed = themes.arrange(landed, label, how, height)
            except WorkbookError as exc:
                problems.append(i18n.t("cli.said.operation", n=n, exc=exc))
                continue
            said.append(i18n.t("cli.run_layouts.arranged_as_in_the_order_its", label=by_id[label]['label'], v_=i18n.t("cli.run_layouts.a_grid") if how == 'grid' else i18n.t("cli.run_layouts.a_column") if how == 'column' else i18n.t("cli.run_layouts.a_row")))
            continue
        ways = themes.ALIGN_WAYS if kind == "align" else themes.SPREAD_WAYS
        if how not in ways:
            problems.append(i18n.t("cli.run_layouts.operation_give_to", n=n, v_='aligns' if kind == 'align' else 'spreads', how=how or i18n.t("cli.run_layouts.no_way"))
                            + listed([f'"{w}"' for w in ways]).replace(" and ", " or ") + ".")
            continue
        items = named_list(op.get("items"))
        keys, bad = [], []
        for x in items:
            given = refs.get(themes_ai.one_line(x), themes_ai.one_line(x))
            key = given if given in by_id else resolve(given) or (given if given in landed["cards"] else None)
            if key is None and any(isinstance(m, dict) and m.get("id") == given for m in landed.get("notes") or []):
                key = given
            (keys if key is not None else bad).append(key if key is not None else themes_ai.one_line(x))
        if bad:
            problems.append(i18n.t("cli.run_layouts.operation_names_not_on_the_board", n=n, listed=listed(bad)))
            continue
        try:
            landed, moved = themes.align_items(landed, keys, how, height)
        except WorkbookError as exc:
            problems.append(i18n.t("cli.said.operation", n=n, exc=exc))
            continue
        verb = "aligned" if kind == "align" else "spread"
        said.append(f"{verb} {listed([name(k) for k in keys])} {how}" if moved else
                    i18n.t("cli.run_layouts.left_as_they_stood_already", listed=listed([name(k) for k in keys]), verb=verb, how=how))
    return landed, said


# Remove (20 October): a card whose statement is no longer in the workbook taken off the board, as the
# sidebar's Remove on a card marked Missing from the workbook does, one by its key or every one at once
REMOVE_OPS = ("remove", "remove_missing")


def is_remove(op) -> bool:
    """An operation that takes a missing card off the board, which runs before the rest."""
    return isinstance(op, dict) and themes_ai.one_line(op.get("op") or op.get("type")).lower() in REMOVE_OPS


def run_removes(board: dict, ops: list, read: dict, keys: dict, sids: dict) -> tuple[dict, list[str], list[str]]:
    """Each remove of a change, `ops` by its number in the change, done on `board`, the board as it
    reads now, through `themes.drop_cards`: the board afterwards, what each did, said plainly, and the
    keys taken off. `{"op": "remove", "items": ["Initial:12:3"]}` takes off each card named by its key,
    and `{"op": "remove_missing"}` every card on the board whose statement is missing from the
    workbook. A card whose statement is in the workbook is never removed. Refused whole, nothing
    written, when one cannot stand."""
    live = {c["key"] for c in read["cards"]}
    missing = [k for k in sorted(board["cards"], key=themes._order) if k not in live]
    said, gone, problems = [], [], []
    text = lambda k: board["cards"][k].get("text") or ""
    for n, op in ops:
        kind = themes_ai.one_line(op.get("op") or op.get("type")).lower()
        if kind == "remove_missing":
            fresh = [k for k in missing if k not in gone]
            if not fresh:
                problems.append(i18n.t("cli.run_removes.operation_no_card_on_is_missing", n=n, name=board['name']))
                continue
            gone += fresh
            said.append(i18n.t("cli.run_removes.removed_missing_from_the_workbook", cards=i18n.t("cli.n.card", n=len(fresh)))
                        + listed([f"{k} '{text(k)}'" for k in fresh]))
            continue
        given = named_list(op.get("items")) or named_list(op.get("item"))
        if not given:
            problems.append(i18n.t("cli.run_removes.operation_names_no_cards_to_remove", n=n))
            continue
        took = []
        for x in given:
            key = statement_key(x, read, keys)
            name = themes_ai.one_line(x)
            if key is not None:
                problems.append(i18n.t("cli.run_removes.operation_names_whose_statement_is_in", n=n, pair=pair(key, sids)))
            elif name not in board["cards"]:
                problems.append(i18n.t("cli.run_removes.operation_names_which_is_not_a", n=n, name=name))
            elif name not in gone and name not in took:
                took.append(name)
        if took:
            gone += took
            said.append("removed " + listed([i18n.t("cli.run_removes.the_card", k=k, text=text(k)) for k in took]) + i18n.t("cli.run_removes.missing_from_the_workbook"))
    if problems:
        raise cli.Refused(*problems, i18n.t("cli.said.nothing_was_written"))
    return (themes.drop_cards(board, gone) if gone else board), said, gone


def named_list(value) -> list:
    return value if isinstance(value, list) else [value] if isinstance(value, str) and value.strip() else []


def run_stacks(landed: dict, ops: list, read: dict, keys: dict, sids: dict, problems: list) -> tuple[dict, list[str]]:
    """Each operation on a stack, `ops` by its number in the change, done in turn on the board the
    others left, through `themes.stack_onto`, `themes.take_out` and `themes.make_top`: the board
    afterwards and what each did, said plainly, a line in `problems` for each that cannot stand.

    `{"op": "stack", "items": ["S79", "S80"], "under": "S77"}` stacks S79 and S80 under S77, which
    then stands for them, `{"op": "unstack", "items": ["S79"]}` takes S79 out again just below its stack,
    and `{"op": "top", "item": "S79"}` puts S79 on top of the stack it is in. `{"op": "not_same", "items":
    ["S11", "S12"]}` marks a close pair Not the same, kept with the board, and `{"op": "show_again", "items":
    ["S11", "S12"]}` takes the mark off, so the board marks the pair again while it stays close."""
    said = []
    name = lambda k: sids.get(k, k)
    for n, op in ops:
        kind = themes_ai.one_line(op.get("op") or op.get("type")).lower()
        kind = SIDEBAR_OPS.get(kind, kind)
        if kind == "put_all_on":
            landed, put = themes.put_all_on(landed)
            if not put:
                problems.append(i18n.t("cli.run_stacks.operation_puts_every_statement_in_not", n=n))
                continue
            said.append(i18n.t("cli.run_stacks.put_the_waiting_in_on_the", statements=i18n.t("cli.n.statement", n=len(put)), not_placed=NOT_PLACED))
            continue
        given = named_list(op.get("items")) or named_list(op.get("item"))
        items, ok = [], True
        for x in given:
            key = statement_key(x, read, keys)
            if key is None or key not in landed["cards"]:
                problems.append(i18n.t("cli.run_stacks.operation_names_which_is_not_a", n=n, x=x))
                ok = False
            elif key not in items:
                items.append(key)
        if not given:
            problems.append(i18n.t("cli.run_stacks.operation_names_no_statements", n=n))
            ok = False
        if not ok:
            continue
        if kind in ("not_same", "show_again"):
            if len(items) != 2:
                problems.append(i18n.t("cli.run_stacks.operation_names_statements_a_close_pair", n=n, n_items=len(items)))
                continue
            pair_keys = themes.pair_of(*items)
            marked = [list(x) for x in landed.get("not_same") or []]
            if kind == "not_same":
                if pair_keys in marked:
                    problems.append(i18n.t("cli.run_stacks.operation_marks_not_the_same_which", n=n, listed=listed([name(k) for k in pair_keys])))
                    continue
                landed = dict(landed, not_same=marked + [pair_keys])
                said.append(i18n.t("cli.run_stacks.marked_not_the_same_so_the", listed=listed([name(k) for k in pair_keys])))
            else:
                if pair_keys not in marked:
                    problems.append(i18n.t("cli.run_stacks.operation_shows_again_which_are_not", n=n, listed=listed([name(k) for k in pair_keys])))
                    continue
                landed = dict(landed, not_same=[x for x in marked if x != pair_keys])
                said.append(i18n.t("cli.run_stacks.took_not_the_same_off_so", listed=listed([name(k) for k in pair_keys])))
            continue
        if kind == "set_aside":
            under = [k for k in items if themes.top_of(landed, k) is not None]
            if under:
                problems.append(i18n.t("cli.run_stacks.operation_sets_aside_stacked_under_another", n=n, list=', '.join(pair(k, sids) for k in under)))
                continue
            already = [k for k in items if k in landed["discarded"]]
            if already:
                problems.append(i18n.t("cli.run_stacks.operation_sets_aside_set_aside_already", n=n, list=', '.join(pair(k, sids) for k in already), v_=i18n.t("cli.run_stacks.which_is") if len(already) == 1 else i18n.t("cli.run_stacks.which_are")))
                continue
            landed, done = themes.set_aside(landed, items)
            said.append(i18n.t("cli.run_stacks.set_aside", listed=listed([name(k) for k in done])))
            continue
        if kind == "put_back":
            out = [k for k in items if k not in landed["discarded"]]
            if out:
                problems.append(i18n.t("cli.run_stacks.operation_puts_back_not_set_aside", n=n, list=', '.join(pair(k, sids) for k in out), v_=i18n.t("cli.run_stacks.which_is") if len(out) == 1 else i18n.t("cli.run_stacks.which_are")))
                continue
            landed, done = themes.put_back(landed, items)
            said.append(i18n.t("cli.run_stacks.put_back_waiting_in", listed=listed([name(k) for k in done]), not_placed=NOT_PLACED))
            continue
        if kind == "stack":
            raw = op.get("under", op.get("onto"))
            top = statement_key(raw, read, keys) if raw is not None else None
            if top is None or top not in landed["cards"]:
                problems.append(i18n.t("cli.run_stacks.operation_stacks_under_which_is_not", n=n, raw=raw)
                                if raw is not None else
                                i18n.t("cli.run_stacks.operation_gives_no_under_the_statement", n=n))
                continue
            above = themes.top_of(landed, top)
            if above is not None:
                problems.append(i18n.t("cli.run_stacks.operation_stacks_under_which_is_stacked", n=n, pair=pair(top, sids), pair2=pair(above, sids), name=name(above), name2=name(top)))
                continue
            if top in landed["discarded"]:
                problems.append(i18n.t("cli.run_stacks.operation_stacks_under_which_is_set", n=n, pair=pair(top, sids)))
                continue
            if top in items:
                problems.append(i18n.t("cli.run_stacks.operation_stacks_under_itself", n=n, pair=pair(top, sids)))
                continue
            landed = themes.stack_onto(landed, items, top)
            said.append(i18n.t("cli.run_stacks.stacked_under_which_stands_for", listed=listed([name(k) for k in items]), name=name(top), v_='it' if len(items) == 1 else 'them'))
        elif kind == "unstack":
            loose = [k for k in items if themes.top_of(landed, k) is None]
            if loose:
                problems.append(i18n.t("cli.run_stacks.operation_takes_out_which_in_no", n=n, list=', '.join(pair(k, sids) for k in loose), v_='is' if len(loose) == 1 else 'are'))
                continue
            tops = {k: themes.top_of(landed, k) for k in items}
            landed = themes.take_out(landed, items)
            said.append("took " + listed([i18n.t("cli.run_stacks.out_of_the_stack_under", name=name(k), name2=name(t)) for k, t in tops.items()])
                        + i18n.t("cli.run_stacks.just_below_it"))
        else:
            key = items[0]
            if len(items) > 1:
                problems.append(i18n.t("cli.run_stacks.operation_names_more_than_one_statement", n=n))
                continue
            top = themes.top_of(landed, key)
            if top is None:
                problems.append(i18n.t("cli.run_stacks.operation_puts_on_top_which_is", n=n, pair=pair(key, sids))
                                if not (landed.get("stacks") or {}).get(key) else
                                i18n.t("cli.run_stacks.operation_puts_on_top_where_it", n=n, pair=pair(key, sids)))
                continue
            landed = themes.make_top(landed, key)
            said.append(i18n.t("cli.run_stacks.put_on_top_of_its_stack", name=name(key), name2=name(top)))
    return landed, said


def made_refs(start: dict, ops: list) -> dict[str, str]:
    """The id each `make` of the change gives its new label, by its ref, as `themes_ai.revise_ops`
    numbers them, so an order names a label a make made by its ref."""
    numbers = [int(str(g["id"])[1:]) for g in start["groups"] if str(g["id"])[:1] == "g" and str(g["id"])[1:].isdigit()]
    top, refs = max(numbers, default=0), {}
    for op in ops:
        if isinstance(op, dict) and themes_ai.one_line(op.get("op") or op.get("type")).lower() == "make":
            top += 1
            ref = themes_ai.one_line(op.get("ref"))
            if ref:
                refs[ref] = f"g{top}"
    return refs


def order_target(op: dict, n: int, v: dict, refs: dict, resolve, sids: dict, problems: list, height=None,
                 top: str | None = None):
    """What an order names, `under`, a label or null for the labels at the top, and `items`, each a
    statement, a card or a label directly under it, as the label's id and the cards' keys, `resolve`
    giving a card's key from the name an agent gave it, or None with a line in `problems` for each
    thing that cannot stand. `height` is as `themes.layout_boxes` takes it, and `top` what a label at
    the top is called."""
    top = top if top is not None else i18n.t("cli.said.a_pet")
    by_id = {g["id"]: g for g in v["groups"]}
    said = op.get("under", op.get("label"))
    if said is None or themes_ai.one_line(said).lower() in ("", "null", "none", "pets"):
        under = None
    else:
        under = refs.get(themes_ai.one_line(said), themes_ai.one_line(said))
        if under not in by_id:
            problems.append(i18n.t("cli.order_target.operation_names_which_is_not_a", n=n, said=said))
            return None
    items = op.get("items")
    if not isinstance(items, list) or not items:
        problems.append(i18n.t("cli.order_target.operation_gives_no_items_to_set", n=n))
        return None
    held = themes.order_of(v, under, themes.layout_boxes(v, height))
    where = top if under is None else i18n.t("cli.order_target.directly_under", label=by_id[under]['label'])
    out, ok = [], True
    for item in items:
        name = refs.get(themes_ai.one_line(item), themes_ai.one_line(item))
        key = name if name in by_id else resolve(name) or name
        if key not in held:
            problems.append(i18n.t("cli.order_target.operation_names_which_is_not", n=n, pair=pair(key, sids) if key in sids else item, where=where))
            ok = False
        elif key in out:
            problems.append(i18n.t("cli.order_target.operation_names_twice", n=n, pair=pair(key, sids) if key in sids else item))
            ok = False
        else:
            out.append(key)
    return (under, out) if ok else None


def run_orders(landed: dict, orders: list, refs: dict, resolve, sids: dict, problems: list, height=None,
               top: str | None = None) -> tuple[dict, list]:
    """Each order of a change, `orders` by its number in the change, set in turn on the board the
    others left, through `themes.reorder`: the board afterwards and what each order did, a line in
    `problems` for each that cannot stand."""
    ordered = []
    for n, op in orders:
        target = order_target(op, n, landed, refs, resolve, sids, problems, height, top)
        if target is None:
            continue
        try:
            landed, done = themes.reorder(landed, *target, height=height)
        except WorkbookError as exc:
            problems.append(i18n.t("cli.said.operation", n=n, exc=exc))
            continue
        ordered.append(done)
    return landed, ordered


def order_said(info: dict, v: dict, sids: dict, top: str | None = None) -> str:
    """What an order did, said plainly: where, the order it set and how the layout took it."""
    top = top if top is not None else i18n.t("cli.said.the_pets")
    titles = {g["id"]: g["label"] for g in v["groups"]}
    name = lambda m: f"'{titles[m]}'" if m in titles else sids.get(m, m)
    where = top if info["under"] is None else i18n.t("cli.order_said.what_sits_in", get=titles.get(info['under'], info['under']))
    listed = [name(m) for m in info["order"]]
    listed = listed[0] if len(listed) == 1 else ", ".join(listed[:-1]) + " and " + listed[-1]
    if not info["moved"]:
        return i18n.t("cli.order_said.left_as_they_read", where=where, listed=listed)
    how = (i18n.t("cli.order_said.each_taking_the_place_of_the_2") if info["how"] == "kept"
           else i18n.t("cli.order_said.each_taking_the_place_of_the"))
    room = [(top if a is None else f"'{titles.get(a, a)}'") for a in info["arranged"]]
    more = i18n.t("cli.order_said.and_made_room_for_it", list=' and '.join(room)) if room else ""
    return i18n.t("cli.order_said.set_in_the_order", where=where, listed=listed, how=how, more=more)


def named_in(plain: list) -> list[str]:
    """What a change's operations name, in the order they name it, its moves' items first among them."""
    out: list[str] = []
    for _, op in plain:
        for x in op.get("items") or op.get("members") or []:
            if isinstance(x, str) and x not in out:
                out.append(x)
    return out


def laid_places(landed: dict, layouts: list, refs: dict, resolve) -> list:
    """The places whose order a change's arrange, align or spread may set: an arranged label and every label
    in it, and the place each aligned or spread item stands in, None for the PETs."""
    by_id = {g["id"]: g for g in landed["groups"]}
    parents = themes.parents_of(landed["groups"])
    out: list = []
    for _, op in layouts:
        label = refs.get(themes_ai.one_line(op.get("label")), themes_ai.one_line(op.get("label")))
        if label in by_id:
            out += [g for g, _ in themes._tree(by_id, label)]
        for x in named_list(op.get("items")):
            given = refs.get(themes_ai.one_line(x), themes_ai.one_line(x))
            key = given if given in by_id or given in landed["cards"] else resolve(given)
            # a sticky note's place is its label's
            note = next((n for n in landed.get("notes") or [] if isinstance(n, dict) and n.get("id") == given), None)
            out.append(note.get("in") if note and note.get("in") in by_id else parents.get(key) if key else None)
    return list(dict.fromkeys(out))


def cmd_board_apply(p: Project, args) -> tuple:
    b = p.case(args.case)
    book = Path(b["workbook"])
    spec = cli.read_spec(args.ops)
    ops, request = read_ops(spec, args)
    if not request and not args.dry_run:
        raise cli.Refused(_w("NO_REQUEST"))
    args.note = request
    with wb_mod.case_held(book, boards=True):
        read = themes.read_cards(book)
        sids, keys = ids_of(read)
        data = load_board_file(book)
        board = pick_board(data, args.board, default="canvas")
        fresh_or_refused(spec, board, i18n.t("cli.board_apply.board_show"))
        # a statement written after the board was made is one of its statements, waiting in Not placed as the
        # canvas shows it, so every operation takes it (30 October)
        followed = themes.with_new(themes.follow(board, read["cards"], read["quotes"]), read["cards"])
        # a card missing from the workbook comes off first, so the rest run on the board without it
        removing = [(n, op) for n, op in enumerate(ops, start=1) if is_remove(op)]
        followed, removed_said, removed = run_removes(followed, removing, read, keys, sids)
        # a pick from here is his, so it keeps every quote it names, as a tick on the PETs screen
        # does, and not the two an AI answer is held to (see `themes.picks_kept`)
        # and a description from here is his too, which the applier takes from board apply alone (21 October)
        start = dict(themes_ai.revise_start(read, followed), pick_max=None)
        ops = name_ids(ops, read, keys)
        # an order runs after the rest, on the board they leave, since it moves where things stand, and
        # an operation on a stack runs after the applier's and before an order
        plain = [(n, op) for n, op in enumerate(ops, start=1)
                 if not is_order(op) and not is_stack(op) and not is_remove(op) and not is_layout(op)]
        orders = [(n, op) for n, op in enumerate(ops, start=1) if is_order(op)]
        # Auto-arrange's ways, Align and Spread (21 October) after the orders, on the board they leave
        layouts = [(n, op) for n, op in enumerate(ops, start=1) if is_layout(op)]
        stacking = [(n, op) for n, op in enumerate(ops, start=1) if is_stack(op)]
        if plain:
            after, applied, info = apply_ops(start, [op for _, op in plain], [n for n, _ in plain])
        else:
            after, applied, info = start, [], {}
        structural = themes_ai._structure(after) != themes_ai._structure(start)
        if structural:
            # a change of levels keeps the layout as the canvas does, and one that puts a statement
            # into a label elsewhere lays out afresh the themes it touches
            revised = {"groups": after["groups"], "picks": after["picks"], "made": info.get("made") or []}
            # and a statement put into a label elsewhere goes in under what it holds, its neighbours where they
            # stood (agentorder, 10 November 2026: a fresh layout of the PET it went into read its sub-PETs and
            # statements in another order)
            landed = (themes.land_kept(followed, revised, strict=True, statements_in=True)
                      or themes.land(followed, revised))
        else:
            landed = themes.normalise(json.loads(json.dumps(followed)))
        # a move to null sends a statement lying loose on the canvas to wait in Not placed too, as Back to Not
        # placed does there, and the answer names only what each such move took out (30 October)
        words, sent, waited = sent_to_wait(start, [op for _, op in plain], applied, followed)
        parents = themes.parents_of(landed["groups"])
        unloosed = [k for k in sent if k not in parents and (landed["cards"].get(k) or {}).get(themes.LOOSE)]
        for k in unloosed:
            landed["cards"][k] = {x: y for x, y in landed["cards"][k].items() if x != themes.LOOSE}
        ordered, problems = [], []
        landed, stacked_said = run_stacks(landed, stacking, read, keys, sids, problems)
        refs = made_refs(start, [op for _, op in plain])
        landed, ordered = run_orders(landed, orders, refs, lambda name: statement_key(name, read, keys), sids, problems)
        titles = lambda k: (f"'{next(g['label'] for g in landed['groups'] if g['id'] == k)}'"
                            if any(g["id"] == k for g in landed["groups"]) else pair(k, sids))
        laid_from = json.dumps([landed.get("cards"), landed.get("groups"), landed.get("notes")], sort_keys=True)
        landed, laid_said = run_layouts(landed, layouts, refs, lambda name: statement_key(name, read, keys), titles,
                                        problems)
        # the order an order or a tool of the toolbar left in a place stands as it left it
        wanted = {o["under"]: o["order"] for o in ordered}
        wanted.update({p: themes.order_of(landed, p) for p in laid_places(landed, layouts, refs, lambda name: statement_key(name, read, keys))})
        laid = json.dumps([landed.get("cards"), landed.get("groups"), landed.get("notes")], sort_keys=True) != laid_from
        if problems:
            raise cli.Refused(*problems, i18n.t("cli.said.nothing_was_written"))
        # what the change left nearer than the margin to what it touched makes way, as a drop makes it on the
        # canvas, so a board an agent leaves has no card over another and none over a frame (31 October)
        themes.settle_change(followed, landed)
        # and every place on the board reads as it did, but where an order or a tool set it, what came in from
        # elsewhere reading last, in the order the change named it (agentorder, 10 November 2026)
        landed, _kept = themes.keep_order(followed, landed, wanted, named_in(plain))
        if (not structural and not unloosed and not any(o["moved"] for o in ordered) and not stacked_said
                and not removed and not laid):
            text = i18n.t("cli.said.nothing_to_change_already_reads_that", name=followed['name'])
            return {"case": b["case"], "board": followed["id"], "changed": False, "said": text}, [text]
        parts = list(removed_said)
        parts += [themes_ai.change_line(words, start)] if words else []
        if waited:
            parts.append(i18n.t("cli.board_apply.left_waiting_in_as_already", listed=listed([sids.get(k, k) for k in waited]), not_placed=NOT_PLACED, v_=i18n.t("cli.board_apply.it_was") if len(waited) == 1 else i18n.t("cli.board_apply.they_were")))
        parts += stacked_said
        parts += [order_said(o, landed, sids) for o in ordered]
        parts += laid_said
        said = " ".join(x[0].upper() + x[1:] + ("" if x.endswith(".") else ".") for x in parts)
        reasons = reasons_after(landed, ops, followed)
        landed["ai"] = {"discarded": reasons} if reasons else {}
        landed["quoted"] = themes_ai.quoted_of(landed["picks"], read["quotes"])
        landed = themes.normalise(landed)
        revision = themes_ai.revision_name(request)
        shown_orders = [{"under": o["under"], "order": [sids.get(m, m) for m in o["order"]],
                         "moved": [sids.get(m, m) for m in o["moved"]], "how": o["how"], "arranged": o["arranged"]}
                        for o in ordered]
        if args.dry_run:
            text = i18n.t("cli.board_apply.dry_run_nothing_was_written_on", name=followed['name'], v_=said[0].lower() + said[1:])
            return {"dry_run": True, "case": b["case"], "board": followed["id"], "applied": applied,
                    "ordered": shown_orders, "removed": removed, "said": text, "revision": revision}, [text]
        when = now_iso()
        boards = themes.boards_of(data)
        made = themes.add_revision(board, name=revision, at=when)
        made["made"] = mark(args, when)
        state = themes.state_of(landed)
        for key in themes.STATE_OPTIONAL:
            board.pop(key, None)
        board.update({k: state[k] for k in themes.STATE_KEYS if k in state}, updated=when, changed=mark(args, when))
        # the state the change left, so his next save is not taken for an edit of his own
        board["changed"]["hash"] = themes.state_hash(themes.made_state(themes.normalise(board)))
        current = str(data.get("current") or board.get("id"))
        themes.write(book, themes._file(book, case_name(book), data, boards, current, when))
    text = f"{said} {kept_line(board.get('name'), revision)}"
    return {"case": b["case"], "board": board.get("id"), "name": board.get("name"), "applied": applied,
            "ordered": shown_orders, "removed": removed, "made": info.get("made"), "gone": info.get("gone"),
            "revision": themes.revision_summary(made), "said": text}, [text]


# --------------------------------------------------------------------- GETs

def gets_data(p: Project) -> dict:
    try:
        data = gets_mod.load(p.root)
    except WorkbookError as exc:
        raise cli.Refused(str(exc))
    if data is None:
        raise cli.Refused(i18n.t("cli.gets_data.this_project_has_no_gets_file"))
    return data


def gets_tree(answer: dict, board: dict, data: dict) -> dict:
    """A GETs board as `gets show` sets it out: each GET with its count of participants and its
    cards, sub-GETs under it, then the cards in no GET and those in the bin."""
    cards = {c["key"]: c for c in answer["cards"]}
    groups = {g["id"]: g for g in answer["groups"]}
    parents = themes.parents_of(answer["groups"])
    inside = {c for c, s in answer["study"].items() if s["in"]}
    kept = gets_mod.normal(board, data)
    # the order the canvas reads, top to bottom and left to right, as `board show` gives a PETs board's
    drawn = themes.layout_boxes(kept, gets_mod.card_height)
    by_kept = {g["id"]: g for g in kept["groups"]}

    def in_order(gid: str) -> list[str]:
        held = list(groups[gid]["members"])
        read = [m for m in themes.theme_order(kept, gid, drawn) if m in held] if gid in by_kept else []
        return read + [m for m in held if m not in read]

    def card(k: str) -> dict:
        c = cards[k]
        return {"key": k, "kind": c.get("kind"), "case": c.get("case"), "text": c.get("text"), "time": c.get("time") or "",
                "sheet": c.get("sheet") or "", "gone": bool(c.get("gone"))}

    def theme(gid: str, seen: frozenset) -> dict:
        g = groups[gid]
        members = in_order(gid)
        return {"id": gid, "label": g["label"], "note": g.get("note") or "", "description": themes.description_of(g),
                "participants": gets_mod.count(kept, gid, inside),
                "cards": [card(m) for m in members if m in cards],
                "themes": [theme(m, seen | {m}) for m in members if m in groups and m not in seen],
                "order": [m for m in members if m in cards or (m in groups and m not in seen)]}

    tops = [g["id"] for g in answer["groups"] if g["id"] not in parents]
    tops = themes.canvas_order([t for t in tops if t in by_kept], by_kept) + [t for t in tops if t not in by_kept]
    return {"id": answer["version"]["id"], "name": answer["version"]["name"], "minimum": answer["minimum"],
            "total": answer["total"], "themes": [theme(g, frozenset({g})) for g in tops],
            "unplaced": [card(k) for k in cards if k not in parents and k not in answer["discarded"]],
            "discarded": [card(k) for k in answer["discarded"] if k in cards]}


def gets_card_line(c: dict, pad: str) -> str:
    # a code and a subtheme in a thematic analysis project's words (taword)
    kind = {"pet": "PET", "sub": i18n.t("cli.card.sub"), "es": i18n.t("cli.card.es"),
            "pn": "Participant note"}.get(c["kind"], c["kind"] or "")
    where = f" ({', '.join(x for x in (c['sheet'], c['time']) if x)})" if c["kind"] == "es" else ""
    gone = f"  {i18n.t('cli.card.gone')}" if c["gone"] else ""
    return f"{pad}{kind} {gets_mod.who(c['case'])}: {c['text']}{where}  [{c['key']}]{gone}"


def gets_theme_lines(t: dict, total: int, depth: int = 1) -> list[str]:
    pad = "   " * depth
    lines = [i18n.t("cli.gets_theme_lines.of", v_='   ' * (depth - 1), id=t['id'], label=t['label'], participants=t['participants'], participants2=i18n.t("cli.n.participant", n=total))]
    if t["description"]:
        lines.append(i18n.t("cli.gets_theme_lines.description", pad=pad, description=t['description']))
    if t["note"]:
        lines.append(i18n.t("cli.said.note", pad=pad, note=t['note']))
    lines += [gets_card_line(c, pad) for c in t["cards"]]
    for sub in t["themes"]:
        lines += gets_theme_lines(sub, total, depth + 1)
    return lines


def cmd_gets_show(p: Project, args) -> tuple:
    data = gets_data(p)
    board = pick_board(data, args.board)
    answer = gets_mod.state(p.root, p.books, board=str(board.get("id")))
    tree = gets_tree(answer, board, json.loads(json.dumps(data)))
    lines = [i18n.t("cli.gets_head", name=tree["name"], id=tree["id"], minimum=tree["minimum"],
                    participants=i18n.t("cli.n.participant", n=tree["total"]))]
    # its version, which gets apply carries back so a change over a board changed since is refused
    tree["version"] = themes.board_version(board)
    if tree["version"]:
        lines.append(i18n.t("cli.said.version", version=tree['version']))
    # a case whose PETs changed since its copy came in, which stands until its changes are taken
    tree["changed"] = [{"case": c["case"], "changes": c["changes"]} for c in answer["cases"]
                       if c["status"] == "changed" and c.get("changes")]
    for c in tree["changed"]:
        who = gets_mod.who(c["case"])
        lines += [i18n.t("cli.gets_show.changed_since_it_came_in_and", who=who)]
        lines += ["   " + x for x in changes_lines(who, c["changes"])]
    for t in tree["themes"]:
        lines += [""] + gets_theme_lines(t, tree["total"])
    lines += ["", f"{NOT_PLACED} ({len(tree['unplaced'])})"] + [gets_card_line(c, "   ") for c in tree["unplaced"]]
    lines += ["", f"{BIN} ({len(tree['discarded'])})"] + [gets_card_line(c, "   ") for c in tree["discarded"]]
    return tree, lines


def as_gets(after: dict, info: dict) -> tuple[dict, dict]:
    """The labels a change made on a GETs board numbered as the GETs screen numbers them, G1 on,
    past every G there, since the applier numbers new labels as PETs, g1 on."""
    taken = [int(g["id"][1:]) for g in after["groups"] if re.match(r"^G\d+$", g["id"])]
    top = max(taken, default=0)
    names = {}
    for gid in info.get("made") or []:
        top += 1
        names[gid] = f"G{top}"
    if not names:
        return after, info
    groups = [dict(g, id=names.get(g["id"], g["id"]), members=[names.get(m, m) for m in g["members"]])
              for g in after["groups"]]
    return dict(after, groups=groups), dict(info, made=[names.get(g, g) for g in info.get("made") or []])


def gets_guard(p: Project) -> None:
    """The GETs board's owner first: a member who does not work on it is refused before anything else is said,
    a dry run and "Nothing to change" too, as `turn_write` has it."""
    if gets_mod.WRITE_GUARD is not None:
        try:
            gets_mod.WRITE_GUARD(Path(p.root))
        except WorkbookError as exc:
            raise cli.Refused(str(exc)) from None


# A statement brought onto a GETs, LPETs or LGETs board from the Participants panel, as a row dragged onto the canvas
# brings its card (lpetadd, 11 November 2026, found by a data run on a participant's LPETs): `{"op": "bring_in",
# "statement": "S12", "timepoint": "T2", "to": "G1"}`, the statement alone, never its PET's other statements, into a
# label or, with no `to`, onto the board in none. It runs first, so the change's other operations can name its card
BRING_IN = ("bring_in", "bring")


def is_bring_in(op) -> bool:
    return isinstance(op, dict) and themes_ai.one_line(op.get("op") or op.get("type")).lower() in BRING_IN


def bring_in_unit() -> str:
    """What a label is on the board in front: an LPET, an LGET, or a GET (a theme in a thematic analysis project)."""
    if gets_mod.in_lpets():
        return i18n.t("cli.bring_in.unit_lpet")
    if gets_mod.in_lgets():
        return i18n.t("cli.bring_in.unit_lget")
    return i18n.t("cli.bring_in.unit_get")


def bring_in_whose(case: str) -> str:
    """Whose a statement is on the board in front, "T2's" on LPETs, "Rowan's" on GETs."""
    return i18n.t("cli.bring_in.whose", who=gets_mod.who(case))


def bring_in_entry(p: Project, op: dict, n: int, said: str) -> tuple[dict, str | None]:
    """The study's entry whose statement an operation names by its id or its key, with the timepoint to read it
    at: on LPETs the timepoint, `timepoint`, by its key, number or label, on GETs and LGETs the participant,
    `participant`, and on LGETs a timepoint too for an id, since each of their timepoints numbers its own."""
    if gets_mod.in_lpets():
        labels = gets_mod.NAMES.get() or {}
        given = op.get("timepoint")
        if given in (None, ""):
            raise cli.Refused(i18n.t("cli.bring_in.no_timepoint", n=n, statement=said,
                                     listed=listed(list(labels) or ["T1"])), i18n.t("cli.said.nothing_was_written"))
        key = gets_mod.timepoint_of(given, labels)
        entry = next((b for b in p.books if b["case"] == key), None)
        if entry is None:
            raise cli.Refused(i18n.t("cli.bring_in.no_such_timepoint", n=n, given=themes_ai.one_line(given),
                                     listed=listed(list(labels) or ["T1"])), i18n.t("cli.said.nothing_was_written"))
        return entry, entry.get("timepoint")
    given = themes_ai.one_line(op.get("participant"))
    if not given:
        raise cli.Refused(i18n.t("cli.bring_in.no_participant", n=n, statement=said),
                          i18n.t("cli.said.nothing_was_written"))
    entry = p.case(given)
    if not gets_mod.in_lgets():
        return entry, entry.get("timepoint")
    labels = gets_mod.LGETS.get() or {}
    key = gets_mod.timepoint_of(op.get("timepoint"), labels) if op.get("timepoint") not in (None, "") else None
    if key is None and SID.match(said):
        raise cli.Refused(i18n.t("cli.bring_in.no_timepoint", n=n, statement=said, listed=listed(list(labels) or ["T1"])),
                          i18n.t("cli.said.nothing_was_written"))
    return entry, (int(key[1:]) if key else None)


def bring_ins(p: Project, ops: list, kept: dict, data: dict) -> list[dict]:
    """Each `bring_in` of a change read against the board as the file holds it, `kept`, and the study's copies in
    `data`: the card's key, its case, its words and where it goes. A statement named by its card's key as `gets show`
    gives one, `T2/es/Midsummer:5:0`, or by its id or its key with its timepoint or its participant (see
    `bring_in_entry`), as `statements` gives them. Refused whole, nothing written, for one of no copy here, another
    participant's on LPETs, one on the board already, said where, or one brought in twice."""
    out, problems = [], []
    lp = gets_mod.in_lpets()
    mine = case_name(Path(routes.LPETS_FOR.get())) if lp and routes.LPETS_FOR.get() is not None else ""
    parents = themes.parents_of(kept.get("groups") or [])
    titles = {g["id"]: g["label"] for g in kept.get("groups") or []}
    aside = set(kept.get("discarded") or [])
    held = data.get("cases") or {}
    # the refs a make of the change gives the labels it makes, which a bring_in after it may name
    refs = set()
    for n, op in enumerate(ops, start=1):
        if isinstance(op, dict) and themes_ai.one_line(op.get("op") or op.get("type")).lower() == "make":
            if themes_ai.one_line(op.get("ref")):
                refs.add(themes_ai.one_line(op.get("ref")))
        if not is_bring_in(op):
            continue
        said = themes_ai.one_line(op.get("statement") or op.get("item"))
        if not said:
            problems.append(i18n.t("cli.bring_in.no_statement", n=n))
            continue
        other = themes_ai.one_line(op.get("participant"))
        if lp and other and other.lower() not in (mine.lower(), gets_mod.who(mine).lower(), mine.lower().split(" - ")[0]):
            problems.append(i18n.t("cli.bring_in.other_participant", n=n, other=other, who=gets_mod.who(mine)))
            continue
        try:
            if "/es/" in said:
                case, _, ident = said.partition("/es/")
            else:
                entry, at = bring_in_entry(p, op, n, said)
                case, ident = entry["case"], said
                if SID.match(said):
                    # its id as `statements` gives it at that timepoint, read from the workbook as it stands
                    with themes.scoped(at):
                        read = themes.read_cards(Path(entry["workbook"]))
                    ident = ids_of(read)[1].get(f"S{int(SID.match(said).group(1))}") or said
        except cli.Refused as exc:
            problems += [x for x in exc.lines if x != i18n.t("cli.said.nothing_was_written")]
            continue
        key = gets_mod.card_of(case, "es", ident)
        line = gets_mod.statement_line(data, key)
        if line is None:
            if lp and case not in held:
                problems.append(i18n.t("cli.bring_in.not_theirs", n=n, statement=said, who=gets_mod.who(mine)))
            else:
                problems.append(i18n.t("cli.bring_in.not_a_statement", n=n, statement=said, whose=bring_in_whose(case)))
            continue
        shown = f"'{line.get('text') or said}'"
        if key in kept["cards"]:
            if key in aside:
                problems.append(i18n.t("cli.bring_in.on_board_aside", n=n, statement=shown))
            elif parents.get(key):
                problems.append(i18n.t("cli.bring_in.on_board_in", n=n, statement=shown, label=titles.get(parents[key], parents[key])))
            else:
                problems.append(i18n.t("cli.bring_in.on_board_loose", n=n, statement=shown, unit=bring_in_unit()))
            continue
        first = next((b["n"] for b in out if b["key"] == key), None)
        if first is not None:
            problems.append(i18n.t("cli.bring_in.twice", first=first, n=n, statement=shown))
            continue
        to = themes_ai.one_line(op.get("to") or op.get("into"))
        if to.lower() in ("", "null", "none"):
            to = None
        elif to not in titles and to not in refs:
            # a label by its title too, when one label has it, as trajectories apply names an LPET
            named = [g for g, t in titles.items() if " ".join(str(t).split()).lower() == to.lower()]
            if len(named) != 1:
                problems.append(i18n.t("cli.bring_in.no_label", n=n, statement=shown, to=to, unit=bring_in_unit()))
                continue
            to = named[0]
        out.append({"n": n, "key": key, "case": case, "text": str(line.get("text") or ""), "to": to})
    if problems:
        raise cli.Refused(*problems, i18n.t("cli.said.nothing_was_written"))
    return out


def bring_in_said(brought: list[dict], landed: dict) -> list[str]:
    """What each statement brought in did, where it stands on the board the change left."""
    parents = themes.parents_of(landed.get("groups") or [])
    titles = {g["id"]: g["label"] for g in landed.get("groups") or []}
    out = []
    for b in brought:
        gid = parents.get(b["key"])
        b.update(label=gid, title=titles.get(gid) if gid else None)
        out.append(i18n.t("cli.bring_in.into", whose=bring_in_whose(b["case"]), text=b["text"], label=titles.get(gid, gid))
                   if gid else i18n.t("cli.bring_in.loose", whose=bring_in_whose(b["case"]), text=b["text"], unit=bring_in_unit()))
    return out


def cmd_gets_apply(p: Project, args) -> tuple:
    gets_guard(p)
    gets_data(p)
    spec = cli.read_spec(args.ops)
    ops, request = read_ops(spec, args)
    if not request and not args.dry_run:
        raise cli.Refused(_w("NO_REQUEST"))
    args.note = request
    with locks.root(p.root):
        when = now_iso()
        data, cases, _disk, _taken = gets_mod.assemble(p.root, p.books, when)
        board = pick_board(data, args.board, default="canvas")
        fresh_or_refused(spec, gets_mod.on_disk(gets_mod.load(p.root), board), i18n.t("cli.gets_apply.gets_show"))
        kept = gets_mod.normal(board, data)
        # a statement brought in from the Participants panel (lpetadd) comes onto the board first, alone, in no
        # label, where the other operations can name its card, as the page's drag puts it there
        brought = bring_ins(p, ops, kept, data)
        gets_mod.bring_in(kept, data, [b["key"] for b in brought])
        texts = {c["key"]: gets_mod.layout_text(c["text"], c.get(themes.DESCRIPTION)) for c in gets_mod.cards_shown(kept, data)}
        plain = dict(kept, cards={k: dict(c, text=texts.get(k) or c.get("text") or "") for k, c in kept["cards"].items()})
        start = {"items": [k for k in plain["cards"] if k not in plain["discarded"]],
                 "groups": [dict({"id": g["id"], "label": g["label"], "members": list(g["members"])},
                                 **({"note": g["note"]} if g.get("note") else {}),
                                 **({themes.DESCRIPTION: g[themes.DESCRIPTION]} if g.get(themes.DESCRIPTION) else {}))
                            for g in plain["groups"]],
                 "picks": {}, "quotes": {}}
        # an order runs after the rest, on the board they leave, as on a PETs board
        # and Arrange by participant after that, on the board the change and its orders leave (19 October)
        listed = [(n, op) for n, op in enumerate(ops, start=1) if not is_order(op) and not is_arrange(op) and not is_layout(op)]
        orders = [(n, op) for n, op in enumerate(ops, start=1) if is_order(op)]
        arranges = [(n, op) for n, op in enumerate(ops, start=1) if is_arrange(op) and not is_layout(op)]
        # a GET's cards arranged a way, Align and Spread (21 October), last of all
        layouts = [(n, op) for n, op in enumerate(ops, start=1) if is_layout(op)]
        bad = [i18n.t("cli.gets_apply.operation_arranges_by_give_by_participant", n=n, one_line=themes_ai.one_line(op.get("by")) or "nothing") for n, op in arranges
               if themes_ai.one_line(op.get("by")).lower() != "participant"]
        if bad:
            raise cli.Refused(*bad, i18n.t("cli.said.nothing_was_written"))
        # a statement brought in goes into its label by a move where its operation stands, so a label a make made
        # before it takes it by its ref, and one brought in to no label stays where it came in
        into = {b["n"]: {"op": "move", "items": [b["key"]], "to": b["to"]} for b in brought if b["to"] is not None}
        listed = [(n, into.get(n, op)) for n, op in listed if not is_bring_in(op) or n in into]
        if listed:
            after, applied, info = apply_ops(start, [op for _, op in listed], [n for n, _ in listed])
        else:
            after, applied, info = start, [], {}
        # the moves that took them in are said as bringing them in, not as moves
        if len(applied) == len(listed):
            applied = [a for (n, _), a in zip(listed, applied) if n not in into]
        structural = themes_ai._structure(after) != themes_ai._structure(start)
        made_before = list(info.get("made") or [])
        after, info = as_gets(after, info)
        if structural:
            # a GET it made may take the id of one it took away, and carries nothing of that one's but its place
            revised = {"groups": after["groups"], "picks": {}, "made": info.get("made") or []}
            # one brought into a label lands under what it holds, as board apply lands a statement moved into a PET
            landed = (themes.land_kept(plain, revised, gets_mod.card_height, strict=True, statements_in=bool(into))
                      or themes.land(plain, revised, gets_mod.card_height))
        else:
            landed = themes.normalise(json.loads(json.dumps(plain)))
        renamed = dict(zip(made_before, info.get("made") or []))
        refs = {ref: renamed.get(g, g) for ref, g in made_refs(start, [op for _, op in listed]).items()}
        problems = []
        landed, ordered = run_orders(landed, orders, refs, lambda name: name if name in landed["cards"] else None, {},
                                     problems, gets_mod.card_height, i18n.t("cli.gets_apply.a_get"))
        if problems:
            raise cli.Refused(*problems, i18n.t("cli.said.nothing_was_written"))
        arranged, loose = [], []
        if arranges:
            before_rows = json.dumps(landed.get("cards"), sort_keys=True)
            loose = gets_mod.by_participant(landed, data, [e["case"] for e in cases], gets_mod.card_height)
            arranged = loose if json.dumps(landed.get("cards"), sort_keys=True) != before_rows else []
        laid_from = json.dumps([landed.get("cards"), landed.get("groups"), landed.get("notes")], sort_keys=True)
        titles = lambda k: (f"'{next(g['label'] for g in landed['groups'] if g['id'] == k)}'"
                            if any(g["id"] == k for g in landed["groups"]) else k)
        landed, laid_said = run_layouts(landed, layouts, refs, lambda name: name if name in landed["cards"] else None,
                                        titles, problems, gets_mod.card_height)
        laid = json.dumps([landed.get("cards"), landed.get("groups"), landed.get("notes")], sort_keys=True) != laid_from
        if problems:
            raise cli.Refused(*problems, i18n.t("cli.said.nothing_was_written"))
        if not structural and not brought and not any(o["moved"] for o in ordered) and not arranged and not laid:
            text = (i18n.t("cli.gets_apply.nothing_to_change_every_pet_and", name=kept['name'])
                    if arranges and not loose else
                    i18n.t("cli.said.nothing_to_change_already_reads_that", name=kept['name']))
            return {"board": kept["id"], "changed": False, "said": text}, [text]
        parts = bring_in_said(brought, landed)
        parts += [themes_ai.change_line(applied, start)] if applied else []
        parts += [order_said(o, landed, {}, i18n.t("cli.gets_apply.the_gets")) for o in ordered]
        if arranged:
            rows = list(dict.fromkeys(gets_mod.who(gets_mod.split_key(k)["case"]) for k in arranged))
            parts.append(i18n.t("cli.gets_apply.arranged_in_no_get_by_participant", cards=i18n.t("cli.n.pet_and_sub_theme_card", n=len(arranged)), listed=listed_words(rows)))
        parts += laid_said
        said = " ".join(x[0].upper() + x[1:] + ("" if x.endswith(".") else ".") for x in parts)
        landed = gets_mod.normal(dict(landed, rows=board.get("rows") or {}), data)
        # in a thematic analysis project a code's other cards follow the one moved, a code split refused (codes)
        if gets_mod.ta_now():
            try:
                landed = codes_mod.follow_moved(kept, landed, data)
            except WorkbookError as exc:
                raise cli.Refused(str(exc), i18n.t("cli.said.nothing_was_written")) from None
        revision = themes_ai.revision_name(request)
        shown_orders = [{k: o[k] for k in ("under", "order", "moved", "how", "arranged")} for o in ordered]
        # each statement brought in: its card's key, whose it is, its words and the label it went into, or none
        brought_out = [{"key": b["key"], "case": b["case"], "who": gets_mod.who(b["case"]), "text": b["text"],
                        "label": b.get("label"), "title": b.get("title")} for b in brought]
        if args.dry_run:
            text = i18n.t("cli.gets_apply.dry_run_nothing_was_written_on", name=kept['name'], v_=said[0].lower() + said[1:])
            return {"dry_run": True, "board": kept["id"], "applied": applied, "ordered": shown_orders, "arranged": arranged,
                    "brought": brought_out, "said": text, "revision": revision}, [text]
        made = themes.add_revision(board, name=revision, at=when)
        made["made"] = mark(args, when)
        state = themes.state_of(landed)
        for key in ("notes", "ai", "quoted", "cut"):
            board.pop(key, None)
        board.update({k: state[k] for k in themes.STATE_KEYS if k in state}, updated=when, changed=mark(args, when))
        board["changed"]["hash"] = themes.state_hash(themes.made_state(gets_mod.normal(board, data)))
        gets_mod.write(p.root, gets_mod._file(data, when))
    text = f"{said} {kept_line(board.get('name'), revision)}"
    return {"board": board.get("id"), "name": board.get("name"), "applied": applied, "ordered": shown_orders,
            "arranged": arranged, "brought": brought_out, "made": info.get("made"), "gone": info.get("gone"),
            "revision": themes.revision_summary(made), "said": text}, [text]


def changes_lines(name: str, said: dict) -> list[str]:
    """What changed in a case's PETs since its copy came into the GETs, said plainly, as the card
    over Take the changes lists it."""
    out = []
    for word, key in (("added", "added"), ("gone", "gone")):
        if said.get(key):
            out.append(i18n.t("cli.changes_lines.pets", word=word) + ", ".join(f"'{t}'" for t in said[key]) + ".")
    for old, new in said.get("retitled") or []:
        out.append(i18n.t("cli.changes_lines.is_now", old=old, new=new))
    if said.get("moved"):
        out.append(f"{i18n.t('cli.n.statement', n=len(said['moved']))} moved: "
                   + ", ".join(i18n.t("cli.changes_lines.from_to", text=m['text'], from_=m['from'] or 'nowhere', to=m['to'] or 'nowhere')
                               for m in said["moved"][:6])
                   + (i18n.t("cli.changes_lines.and_more", v_=len(said['moved']) - 6) if len(said["moved"]) > 6 else "") + ".")
    if said.get("marked"):
        out.append(i18n.t("cli.changes_lines.s_pets_were_marked_complete_since", name=name))
    if said.get("board"):
        out.append(i18n.t("cli.changes_lines.the_copy_comes_from_now", board=said['board']))
    return out or [i18n.t("cli.changes_lines.the_copy_differs_in_a_statements")]


def cmd_gets_colour(p: Project, args) -> tuple:
    """A participant's colour on the GETs board set from the 25, by its name, as the swatch on its row in the
    Participants panel does (21 October), or `default` for the colour it is given in participant order. A
    colour another participant has is refused, as the picker strikes it through. Kept in the GETs file at
    once, no part of any board, so no History."""
    if not themes_ai.one_line(args.note) and not args.dry_run:
        raise cli.Refused(_w("NO_REQUEST"))
    gets_data(p)
    b = p.case(args.case)
    name = gets_mod.who(b["case"])
    said = themes_ai.one_line(args.colour).lower()
    names = [n.lower() for n in gets_mod.COLOUR_NAMES]
    if said in ("default", "none", "null", ""):
        colour = None
    elif said in names:
        colour = names.index(said)
    else:
        raise cli.Refused(i18n.t("cli.gets_colour.is_not_one_of_the_participants", colour=args.colour)
                      + listed_words(list(gets_mod.COLOUR_NAMES)) + i18n.t("cli.gets_colour.nothing_was_changed"))
    with locks.root(p.root):
        data, cases, _disk, _taken = gets_mod.assemble(p.root, p.books, now_iso())
        look = gets_mod.looks([e["case"] for e in cases], data)
        if b["case"] not in look:
            raise cli.Refused(gets_mod.NOT_A_CASE)
        mine = look[b["case"]]
        word = gets_mod.COLOUR_NAMES
        if colour is not None:
            other = next((c for c, lk in look.items() if c != b["case"] and lk["colour"] == colour), None)
            if other is not None:
                raise cli.Refused(i18n.t("cli.gets_colour.is_s_colour_so_nothing_was", word=word[colour], who=gets_mod.who(other)))
        after = mine["default"] if colour is None else colour
        if after == mine["colour"] and (colour is None) == (not mine["chosen"]):
            text = i18n.t("cli.gets_colour.s_colour_is_already_nothing_was", name=name, word=word[after])
            return {"case": b["case"], "changed": False, "colour": word[after], "said": text}, [text]
        line = (i18n.t("cli.gets_colour.s_colour_from_to", name=name, v_=i18n.t("cli.gets_colour.would_go") if args.dry_run else 'went', word=word[mine['colour']])
                + (i18n.t("cli.gets_colour.the_default", word=word[after]) if colour is None else word[after]) + ".")
        if args.dry_run:
            text = i18n.t("cli.gets_colour.dry_run_nothing_was_written", line=line)
            return {"dry_run": True, "case": b["case"], "colour": word[after], "said": text}, [text]
        try:
            gets_mod.colour_op(p.root, p.books, b["case"], colour)
        except WorkbookError as exc:
            raise cli.Refused(str(exc))
    return {"case": b["case"], "colour": word[after], "said": line}, [line]


def cmd_gets_take(p: Project, args) -> tuple:
    """Take the changes of a case into the GETs, as Update on the GETs screen does (see `gets.take`):
    the GETs file keeps a copy of each case's PETs from when it came in. A change made in the app comes
    in by itself (20 October), and one made here stands apart until he presses Update or this runs. Each GETs board keeps a revision first, and is marked as changed in a
    conversation, so an open GETs screen says so."""
    if not themes_ai.one_line(args.note) and not args.dry_run:
        raise cli.Refused(_w("NO_REQUEST"))
    gets_data(p)
    b = p.case(args.case)
    name = gets_mod.who(b["case"])
    with locks.root(p.root):
        when = now_iso()
        data, cases, _disk, _taken = gets_mod.assemble(p.root, p.books, when)
        entry = next((e for e in cases if e["case"] == b["case"]), None)
        old = (data.get("cases") or {}).get(b["case"])
        if entry is None or old is None or entry["status"] == "pending":
            raise cli.Refused(gets_mod.NOT_IN)
        if entry["status"] == "unread":
            raise cli.Refused(entry["said"] or i18n.t("cli.gets_take.s_themes_file_could_not_be", name=name))
        if entry["status"] == "in":
            text = i18n.t("cli.gets.take_none", name=name)
            return {"case": b["case"], "changed": False, "said": text}, [text]
        said = gets_mod.changes(old, entry["fresh"])
        lines = changes_lines(name, said)
        out = {"case": b["case"], "changes": said}
        if args.dry_run:
            text = i18n.t("cli.gets.take_dry", name=name)
            return dict(out, dry_run=True, said=" ".join([text] + lines)), [text] + lines
        try:
            gets_mod.take(p.root, p.books, b["case"])
        except WorkbookError as exc:
            raise cli.Refused(str(exc))
        data = gets_mod.load(p.root)
        for board in gets_mod.boards_of(data):
            board["changed"] = mark(args, when)
            board["changed"]["hash"] = themes.state_hash(themes.made_state(gets_mod.normal(board, data)))
        gets_mod.write(p.root, gets_mod._file(data, now_iso()))
    text = i18n.t("cli.gets.take", name=name)
    return dict(out, said=" ".join([text] + lines)), [text] + lines


# ------------------------------------------ the GETs boards, their History and the study (26 October)
#
# The GETs screen's board menu (`/api/gets-ops`: New board, Duplicate, Rename, the board note, a board put on
# the canvas, Delete, Mark as current and GETs complete), its History (`/api/gets-boards`: Save a revision, a
# revision on view, Restore, Add every sub-theme) and the study's settings (`/api/gets-settings`), each
# through the route's own function, `gets.version_op`, `gets.board_op` and `gets.settings_op`, under the
# project's lock the route takes, its dry run the function's own, so every check and refusal is the route's.
# A write that changes a board keeps it first in its History, as the PETs boards' ops here do.

def gets_op(p: Project, op: str, body: dict, dry: bool = False) -> dict:
    """One of the GETs screen's board ops through `gets.version_op`, refused in its own words."""
    try:
        return gets_mod.version_op(p.root, p.books, op, body, dry_run=dry)
    except WorkbookError as exc:
        raise cli.Refused(str(exc)) from None


def gets_board_op(p: Project, op: str, body: dict, dry: bool = False) -> dict:
    """One of a GETs board's History ops through `gets.board_op`, refused in its own words."""
    try:
        return gets_mod.board_op(p.root, p.books, op, body, dry_run=dry)
    except WorkbookError as exc:
        raise cli.Refused(str(exc)) from None


def gets_revision_first(p: Project, vid: str, name: str, args) -> dict:
    """The GETs board as it stands kept first in its History under `name`, the tool and his request on it."""
    when = now_iso()
    data = gets_mod.load(p.root) or {}
    board = next((x for x in gets_mod.boards_of(data) if str(x.get("id")) == vid), None)
    if board is None:
        raise cli.Refused(gets_mod.GONE)
    made = themes.add_revision(board, name=name, at=when)
    made["made"] = mark(args, when)
    gets_mod.write(p.root, gets_mod._file(data, when))
    return made


def stamp_gets(p: Project, vid: str, rid: str | None, args, changed: bool) -> None:
    """The tool and his request on the revision a GETs board op kept, and with `changed` the board marked as
    changed in a conversation, as `gets apply` marks it."""
    when = now_iso()
    data = gets_mod.load(p.root) or {}
    board = next((x for x in gets_mod.boards_of(data) if str(x.get("id")) == vid), None)
    if board is None:
        return
    for r in themes.history_of(board):
        if rid and str(r["id"]) == rid:
            r["made"] = mark(args, when)
    if changed:
        board["changed"] = mark(args, when)
        board["changed"]["hash"] = themes.state_hash(themes.made_state(gets_mod.normal(board, data)))
    gets_mod.write(p.root, gets_mod._file(data, when))


def gets_named(p: Project, args, default: str = "chosen") -> tuple[dict, dict]:
    """The GETs file and the board a command names, the Current board, else the one on the canvas, when it
    names none."""
    data = gets_data(p)
    return data, pick_board(data, getattr(args, "board", None), default=default)


def gets_request(args) -> None:
    if not themes_ai.one_line(args.note) and not args.dry_run:
        raise cli.Refused(_w("NO_REQUEST"))


def cmd_gets_fresh(p: Project, args) -> tuple:
    """A new GETs board, every card back in the pile, as New board in the GETs board menu makes one,
    through `version_op`'s `new`, put on the canvas. His other boards are left as they were."""
    gets_guard(p)
    gets_request(args)
    data = gets_data(p)
    boards = themes.boards_of(data)
    name = themes.board_name(boards, " ".join(str(getattr(args, "name", "") or "").split()))
    with locks.root(p.root):
        if args.dry_run:
            gets_op(p, "new", {"name": name}, dry=True)
            text = i18n.t("cli.gets.fresh_dry", name=name)
            return {"name": name, "dry_run": True, "said": text}, [text]
        answer = gets_op(p, "new", {"name": name})
    made = next((x for x in answer["versions"] if x["name"] == name), {})
    text = i18n.t("cli.gets.fresh", name=name)
    return {"name": name, "id": made.get("id"), "said": text}, [text]


def cmd_gets_duplicate(p: Project, args) -> tuple:
    """A GETs board copied under a new name, as Duplicate in the GETs board menu does, through `version_op`'s
    `duplicate`, the copy put on the canvas with a note that names the tool and his request. The board
    copied is left as it was."""
    gets_request(args)
    with locks.root(p.root):
        data, board = gets_named(p, args)
        name, vid = str(board.get("name")), str(board.get("id"))
        wanted = " ".join(str(getattr(args, "name", "") or "").split())
        copy_name = themes._free_name(themes.boards_of(data), wanted or f"{name} copy")
        note = (f"Duplicated from {name} by {themes_ai.one_line(args.tool) or cli.TOOL} in a conversation on "
                f"{cli.when_said(now_iso())}, for the request '{themes_ai.one_line(args.note)}'.")
        out = {"from": vid, "from_name": name, "name": copy_name}
        if args.dry_run:
            gets_op(p, "duplicate", {"id": vid, "name": copy_name}, dry=True)
            text = i18n.t("cli.gets.duplicate_dry", name=name, copy=copy_name)
            return dict(out, dry_run=True, said=text), [text]
        answer = gets_op(p, "duplicate", {"id": vid, "name": copy_name})
        made = next((x for x in answer["versions"] if x["name"] == copy_name), {})
        gets_op(p, "note", {"id": made.get("id"), "note": note})
    text = i18n.t("cli.gets.duplicate", name=name, copy=copy_name)
    return dict(out, id=made.get("id"), note=note, said=text), [text]


def cmd_gets_rename(p: Project, args) -> tuple:
    """A GETs board renamed, as Rename in the GETs board menu does, through `version_op`'s `rename`. The
    board as it stands is kept first in its History, named for its old name and his request."""
    gets_request(args)
    wanted = " ".join(str(args.name or "").split())
    with locks.root(p.root):
        _data, board = gets_named(p, args)
        name, vid = str(board.get("name")), str(board.get("id"))
        out = {"board": vid, "was": name, "name": wanted}
        if wanted == name:
            text = i18n.t("cli.gets.rename_same", name=name)
            return dict(out, changed=False, said=text), [text]
        gets_op(p, "rename", {"id": vid, "name": wanted}, dry=True)
        if args.dry_run:
            text = i18n.t("cli.gets.rename_dry", name=name, wanted=wanted)
            return dict(out, dry_run=True, said=text), [text]
        made = gets_revision_first(p, vid, f"{RENAMED} {name}: {request_cut(args)}", args)
        gets_op(p, "rename", {"id": vid, "name": wanted})
    text = i18n.t("cli.gets.rename", name=name, wanted=wanted, kept=made["name"])
    return dict(out, changed=True, revision=themes.revision_summary(made), said=text), [text]


def cmd_gets_note(p: Project, args) -> tuple:
    """A GETs board's note set, or taken off with an empty one, as the board note on the GETs screen sets
    it, through `version_op`'s `note`. The board as it stands is kept first in its History."""
    gets_request(args)
    words = str(args.text or "").strip()
    with locks.root(p.root):
        _data, board = gets_named(p, args)
        name, vid = str(board.get("name")), str(board.get("id"))
        was = str(board.get("note") or "").strip()
        out = {"board": vid, "name": name, "was": was, "note": words}
        if words == was:
            text = i18n.t("cli.gets.note_same", name=name)
            return dict(out, changed=False, said=text), [text]
        gets_op(p, "note", {"id": vid, "note": words}, dry=True)
        if args.dry_run:
            text = (i18n.t("cli.gets.note_off_dry", name=name) if not words
                    else i18n.t("cli.gets.note_set_dry", name=name, words=words))
            return dict(out, dry_run=True, said=text), [text]
        made = gets_revision_first(p, vid, f"{NOTED}: {request_cut(args)}", args)
        gets_op(p, "note", {"id": vid, "note": words})
    text = (i18n.t("cli.gets.note_off", name=name, kept=made["name"]) if not words
            else i18n.t("cli.gets.note_set", name=name, words=words, kept=made["name"]))
    return dict(out, changed=True, revision=themes.revision_summary(made), said=text), [text]


def cmd_gets_canvas(p: Project, args) -> tuple:
    """A GETs board put on the canvas, as choosing it in the GETs board menu does, through `version_op`'s
    `switch`. Nothing on any board changes."""
    gets_request(args)
    with locks.root(p.root):
        data, board = gets_named(p, args)
        name, vid = str(board.get("name")), str(board.get("id"))
        was = themes.current_version(data) or {}
        out = {"board": vid, "name": name, "was": was.get("id")}
        if str(was.get("id")) == vid:
            text = i18n.t("cli.gets.canvas_same", name=name)
            return dict(out, changed=False, said=text), [text]
        if args.dry_run:
            gets_op(p, "switch", {"id": vid}, dry=True)
            text = i18n.t("cli.gets.canvas_dry", name=name, was=was.get("name"))
            return dict(out, dry_run=True, said=text), [text]
        gets_op(p, "switch", {"id": vid})
    text = i18n.t("cli.gets.canvas", name=name, was=was.get("name"))
    return dict(out, changed=True, said=text), [text]


def cmd_gets_current(p: Project, args) -> tuple:
    """A GETs board marked as the Current board, as Mark as current in the GETs board menu does, through
    `version_op`'s `choose`. The board as it stands is kept first in its History, named for the mark and
    his request."""
    gets_request(args)
    with locks.root(p.root):
        data, board = gets_named(p, args)
        name, vid = str(board.get("name")), str(board.get("id"))
        was = themes.chosen_of(data)
        before = next((str(x.get("name")) for x in themes.boards_of(data) if str(x.get("id")) == was), None) if was else None
        out = {"board": vid, "name": name, "was": was}
        if was == vid:
            text = i18n.t("cli.gets.current_same", name=name)
            return dict(out, changed=False, said=text), [text]
        gets_op(p, "choose", {"id": vid}, dry=True)
        if args.dry_run:
            text = (i18n.t("cli.gets.current_dry_instead", name=name, before=before) if before
                    else i18n.t("cli.gets.current_dry", name=name))
            return dict(out, dry_run=True, said=text), [text]
        made = gets_revision_first(p, vid, f"{CURRENT}: {request_cut(args)}", args)
        gets_op(p, "choose", {"id": vid})
    text = (i18n.t("cli.gets.current_instead", name=name, before=before, kept=made["name"]) if before
            else i18n.t("cli.gets.current", name=name, kept=made["name"]))
    return dict(out, changed=True, revision=themes.revision_summary(made), said=text), [text]


def cmd_gets_delete(p: Project, args) -> tuple:
    """A GETs board deleted, as Delete in the GETs board menu does, through `version_op`'s `delete`, the last
    board refused. A copy of the board as it stood, its History with it, goes first into the `_Archive/`
    beside the GETs file as JSON, which the answer names."""
    gets_request(args)
    with locks.root(p.root):
        data, board = gets_named(p, args)
        name, vid = str(board.get("name")), str(board.get("id"))
        gets_op(p, "delete", {"id": vid}, dry=True)
        marks = [w for w, on in ((i18n.t("cli.said.the_current_board"), themes.chosen_of(data) == vid),
                                 (i18n.t("cli.said.on_the_canvas"), str((themes.current_version(data) or {}).get("id")) == vid)) if on]
        was = f", {' and '.join(marks)}," if marks else ""
        out = {"board": vid, "name": name, "current": themes.chosen_of(data) == vid}
        if args.dry_run:
            text = i18n.t("cli.gets.delete_dry", name=name, was=was)
            return dict(out, dry_run=True, said=text), [text]
        held = gets_mod.gets_path(p.root)
        archive = held.parent / "_Archive"
        archive.mkdir(parents=True, exist_ok=True)
        stem = f"{held.stem} board {name.translate(themes.UNSAFE)} (deleted {datetime.now():%Y%m%d-%H%M})"
        kept, n = archive / f"{stem}.json", 2
        while kept.exists():
            kept, n = archive / f"{stem}-{n}.json", n + 1
        kept.write_text(json.dumps(board, ensure_ascii=False, indent=1), encoding="utf-8", newline="\n")
        answer = gets_op(p, "delete", {"id": vid})
    shown = (answer.get("version") or {}).get("name")
    text = (i18n.t("cli.gets.delete", name=name, was=was, file=kept.name)
            + (i18n.t("cli.said.is_on_the_canvas", shown=shown) if shown else ""))
    return dict(out, backup=kept.name, said=text), [text]


def cmd_gets_complete(p: Project, args) -> tuple:
    """GETs marked complete on the Current board, as GETs complete on the GETs screen does, or with --reopen
    reopened, through `version_op`'s `complete` and `reopen`, refused while a participant of the study is not
    in from their marked board unchanged. Only the mark at the top of the GETs file changes, and a mark
    already there keeps its first time."""
    gets_request(args)
    op = "reopen" if getattr(args, "reopen", False) else "complete"
    with locks.root(p.root):
        data = gets_data(p)
        held = themes.complete_of(data)
        out = {"op": op, "was": held}
        if (op == "complete") == bool(held):
            text = (i18n.t("cli.gets_complete.gets_are_marked_complete_already_since", when=cli.when_said(held['at']), get=held.get('name'))
                    if held else i18n.t("cli.gets_complete.gets_are_not_marked_complete_nothing"))
            return dict(out, changed=False, complete=held, said=text), [text]
        dry = gets_op(p, op, {}, dry=True)
        if args.dry_run:
            text = (i18n.t("cli.gets_complete.dry_run_nothing_was_written_it_2", get=(dry.get('complete') or {}).get('name')) if op == "complete" else
                    i18n.t("cli.gets_complete.dry_run_nothing_was_written_it", when=cli.when_said(held['at'])))
            return dict(out, dry_run=True, complete=dry.get("complete"), said=text), [text]
        gets_op(p, op, {})
        now = themes.complete_of(gets_mod.load(p.root))
    text = i18n.t("cli.gets_complete.marked_gets_complete_on", get=now.get('name')) if op == "complete" else i18n.t("cli.gets_complete.reopened_gets")
    return dict(out, changed=True, complete=now, said=text), [text]


def cmd_gets_history(p: Project, args) -> tuple:
    """A GETs board's History, newest first as the History tab lists it, and with --revision one revision as
    `gets show` sets a board out, as the History tab shows one on view. Only reads."""
    data, board = gets_named(p, args)
    name, vid = str(board.get("name")), str(board.get("id"))
    listed = themes.history_list(board)
    if not getattr(args, "revision", None):
        lines = [i18n.t("cli.gets_history", name=name, n=len(listed))]
        lines += [revision_line(r) for r in listed] or [i18n.t("cli.said.none_yet_one_is_kept_every")]
        return {"board": vid, "name": name, "history": listed}, lines
    revision = revision_by(board, args.revision)
    viewed = gets_board_op(p, "view", {"id": vid, "revision": revision["id"]})
    state = dict(revision["state"], id=vid, name=name)
    answer = gets_mod.state(p.root, p.books, board=vid)
    answer = dict(answer, cards=viewed["cards"], groups=viewed["groups"], discarded=viewed["discarded"])
    tree = gets_tree(answer, state, json.loads(json.dumps(data)))
    summary = themes.revision_summary(revision)
    said = dict(name=name, id=summary["id"], when=themes.when_said(summary["at"]), called=summary["name"])
    lines = [i18n.t("cli.gets_revision_named", **said) if summary["name"] else i18n.t("cli.gets_revision", **said)]
    for t in tree["themes"]:
        lines += [""] + gets_theme_lines(t, tree["total"])
    lines += ["", f"{NOT_PLACED} ({len(tree['unplaced'])})"] + [gets_card_line(c, "   ") for c in tree["unplaced"]]
    lines += ["", f"{BIN} ({len(tree['discarded'])})"] + [gets_card_line(c, "   ") for c in tree["discarded"]]
    return dict(tree, revision=summary), lines


def cmd_gets_revision(p: Project, args) -> tuple:
    """Save a revision of a GETs board, as Save a revision does, through `board_op`'s `revision`, under --name
    or his request. Nothing on the board changes."""
    gets_request(args)
    with locks.root(p.root):
        _data, board = gets_named(p, args)
        name, vid = str(board.get("name")), str(board.get("id"))
        called = " ".join(str(getattr(args, "name", "") or "").split()) or request_cut(args)
        done = gets_board_op(p, "revision", {"id": vid, "name": called}, dry=bool(args.dry_run))
        out = {"board": vid, "name": name}
        if args.dry_run:
            text = i18n.t("cli.gets.revision_dry", name=name, called=called)
            return dict(out, dry_run=True, said=text), [text]
        stamp_gets(p, vid, done["revision"]["id"], args, changed=False)
    text = i18n.t("cli.gets.revision", name=name, called=called)
    return dict(out, revision=done["revision"], said=text), [text]


def cmd_gets_restore(p: Project, args) -> tuple:
    """Restore a revision of a GETs board, as the History tab's Restore does, through `board_op`'s `restore`:
    the board as it stands kept first in its History, "Before restoring 12:04", then the revision made the
    board, which is marked as changed in a conversation."""
    gets_request(args)
    with locks.root(p.root):
        _data, board = gets_named(p, args)
        name, vid = str(board.get("name")), str(board.get("id"))
        revision = revision_by(board, args.revision)
        done = gets_board_op(p, "restore", {"id": vid, "revision": revision["id"]}, dry=bool(args.dry_run))
        when = themes.when_said(revision["at"])
        out = {"board": vid, "name": name, "restored": done["restored"]}
        if args.dry_run:
            text = i18n.t("cli.gets.restore_dry", name=name, when=when, kept=done["revision"]["name"])
            return dict(out, dry_run=True, said=text), [text]
        stamp_gets(p, vid, done["revision"]["id"], args, changed=True)
    text = i18n.t("cli.gets.restore", name=name, when=when, kept=done["revision"]["name"])
    return dict(out, revision=done["revision"], said=text), [text]


def cmd_gets_subs(p: Project, args) -> tuple:
    """Add every sub-theme, as the GETs board menu's Add every sub-theme does, through `board_op`'s `subs`:
    a card for each sub-theme of the study the board has none of, each where the route places it, in the
    nearest free spot. The board as it stood is kept first in its History, as "Before: " and his request."""
    gets_request(args)
    gets_data(p)
    with locks.root(p.root):
        # the board as the route reads it, every participant not yet in come in, as gets apply reads it
        data, _cases, _disk, _taken = gets_mod.assemble(p.root, p.books, now_iso())
        board = pick_board(data, getattr(args, "board", None), default="canvas")
        name, vid = str(board.get("name")), str(board.get("id"))
        added = gets_board_op(p, "subs", {"id": vid})["added"]
        listed = [{"key": c["key"], "who": c.get("who") or gets_mod.who(c.get("case") or ""), "text": c.get("text") or ""}
                  for c in added]
        out = {"board": vid, "name": name, "added": listed}
        said = [f"  {c['who']}: {c['text']}  [{c['key']}]" for c in listed]
        if args.dry_run:
            text = (i18n.t("cli.gets_subs.dry_run_nothing_was_written_it", cards=i18n.t("cli.n.sub_theme_card", n=len(listed)), name=name))
            return dict(out, dry_run=True, said=text), [text] + said
        when = now_iso()
        revision = themes_ai.revision_name(args.note)
        made = themes.add_revision(board, name=revision, at=when)
        made["made"] = mark(args, when)
        for c in added:
            board.setdefault("cards", {})[c["key"]] = {"x": c["x"], "y": c["y"]}
        board.update(updated=when, changed=mark(args, when))
        board["changed"]["hash"] = themes.state_hash(themes.made_state(gets_mod.normal(board, data)))
        gets_mod.write(p.root, gets_mod._file(data, when))
    text = (i18n.t("cli.gets_subs.added_to_the_gets_board_each", cards=i18n.t("cli.n.sub_theme_card", n=len(listed)), name=name, kept_line=kept_line(name, revision)))
    return dict(out, revision=themes.revision_summary(made), said=text), [text] + said


def settings_lines(view: dict) -> list[str]:
    """The study's settings as Project settings shows them."""
    band = i18n.t("cli.settings_lines.smiths_band_for", participants=i18n.t("cli.n.participant", n=view['total'])) if view["band"] else ""
    lines = [i18n.t("cli.settings_lines.a_get_needs_of_the_in", minimum=view['minimum'], participants=i18n.t("cli.n.participant", n=view['total']), band=band),
             i18n.t("cli.settings_lines.one_per_pet", v_='on' if view['settings']['one_per_pet'] else 'off')]
    for s in view["study"]:
        lines.append(f"  {s['who']}: " + (i18n.t("cli.settings_lines.in_the_study") if s["in"] else i18n.t("cli.settings_lines.out_of_the_study", reason=s['reason'])))
    return lines


def cmd_gets_settings(p: Project, args) -> tuple:
    """The study's own settings, under GETs in Project settings, read as `settings_view` reads them, or saved as its
    save does through `gets.settings_op`: --minimum, a whole number or band for Smith's band, --one-per-pet on
    or off, --out Name=reason taking a participant out of the
    study with his reason and --in putting one back. Kept in the GETs file, no part of any board, so no
    History. With --dry-run what would change, and nothing written."""
    view = gets_mod.settings_view(p.root, p.books)
    body: dict = {}
    minimum = getattr(args, "minimum", None)
    if minimum is not None:
        body["minimum"] = None if str(minimum).strip().lower() in ("band", "smith", "") else minimum
    if getattr(args, "one_per_pet", None) is not None:
        said = str(args.one_per_pet).strip().lower()
        if said not in ("on", "off", "true", "false", "yes", "no"):
            raise cli.Refused(i18n.t("cli.gets_settings.say_one_per_pet_on_or"))
        body["one_per_pet"] = said in ("on", "true", "yes")
    study = {}
    for item in getattr(args, "out", None) or []:
        who, _, reason = str(item).partition("=")
        study[p.case(who.strip())["case"]] = {"in": False, "reason": reason.strip()}
    for who in getattr(args, "back_in", None) or []:
        study[p.case(str(who).strip())["case"]] = {"in": True}
    if study:
        body["study"] = study
    if not body:
        return dict(view, project=p.info["name"]), settings_lines(view)
    gets_request(args)
    gets_data(p)
    with locks.root(p.root):
        try:
            after = gets_mod.settings_op(p.root, p.books, body, dry_run=True)
        except WorkbookError as exc:
            raise cli.Refused(str(exc)) from None
        changes = []
        was, now = view["settings"], after["settings"]
        if was.get("minimum") != now.get("minimum"):
            said = lambda m: i18n.t("cli.said.smiths_band") if m is None else str(m)
            changes.append(i18n.t("cli.gets_settings.the_minimum_from_to", said=said(was.get('minimum')), said2=said(now.get('minimum'))))
        if was["one_per_pet"] != now["one_per_pet"]:
            changes.append(i18n.t("cli.gets_settings.one_per_pet_from_to", v_='on' if was['one_per_pet'] else 'off', v_2='on' if now['one_per_pet'] else 'off'))
        before = {s["case"]: s for s in view["study"]}
        for case, mark_ in after["study"].items():
            old = before.get(case) or {"in": True, "reason": ""}
            if old["in"] != mark_["in"] or (not mark_["in"] and old["reason"] != mark_["reason"]):
                changes.append(f"{gets_mod.who(case)} " + (i18n.t("cli.gets_settings.back_in_the_study") if mark_["in"]
                                                          else i18n.t("cli.gets_settings.out_of_the_study", reason=mark_['reason'])))
        out = {"changes": changes, "settings": now, "study": after["study"]}
        if not changes:
            text = i18n.t("cli.gets_settings.the_studys_settings_are_so_already")
            return dict(out, changed=False, said=text), [text]
        if args.dry_run:
            return dict(out, dry_run=True), [i18n.t("cli.gets_settings.dry_run_nothing_was_written_it")] + ["  " + c for c in changes]
        gets_mod.settings_op(p.root, p.books, body, asker=hist_mod.asker(asked_by(args)))
    return dict(out, changed=True), [i18n.t("cli.gets_settings.saved_in_the_gets_file")] + ["  " + c for c in changes]


# ------------------------------------------------------------------- turns

def keyed_pairs(sheet: str, row: int, pairs: list[dict]) -> list[dict]:
    """A passage's pairs as turn show gives them, each statement with its key, `Initial:12:0`, which a
    write sends back to say which statement each pair is (20 October)."""
    out, line = [], 0
    for p in pairs:
        item = {"statement": p["es"], "quote": p["kq"]}
        if p["es"]:
            item["key"] = themes.card_key(sheet, row, line)
            line += 1
        out.append(item)
    return out


def turns_of(book: Path, sheet: str) -> tuple[list[dict], dict]:
    """Every row of a sheet as the turn screen reads it, read-only: its speaker, timecode, words,
    statements, exploratory notes and quotes, its timecode as the project writes them."""
    form = wb_mod.timecodes_for(book)
    try:
        wb = openpyxl.load_workbook(book, read_only=True, data_only=True)
    except Exception as exc:
        raise cli.Refused(i18n.t("cli.turns_of.could_not_be_read", name=book.name, exc=exc))
    try:
        if sheet not in wb.sheetnames:
            raise cli.Refused(i18n.t("cli.turns_of.no_sheet_called_the_sheets", sheet=sheet, list=', '.join(wb.sheetnames)))
        ws = wb[sheet]
        cols = wb_mod.detect_columns(ws)
        if not {"name", "ts", "transcript"} <= set(cols):
            raise cli.Refused(i18n.t("cli.turns_of.is_not_a_transcript_sheet", sheet=sheet))
        width = max(cols.values())
        rows = []
        for r, values in enumerate(ws.iter_rows(min_row=2, max_col=width, values_only=True), start=2):
            values = tuple(values) + (None,) * (width - len(values))
            get = lambda role: values[cols[role] - 1] if role in cols else None
            if get("name") is None and get("ts") is None and get("transcript") is None:
                continue
            seconds = wb_mod.ts_seconds(get("ts"))
            # each statement with its own quote, by place, "(no quote)" read as none
            rows.append({"sheet": sheet, "row": r, "name": str(get("name") or "").strip(), "time": wb_mod.timecode(seconds, form),
                         "seconds": seconds, "text": str(get("transcript") or "").strip(),
                         "statements": wb_mod.split_entries(get("es")), "notes": wb_mod.split_entries(get("en")),
                         "quotes": [q for q in wb_mod.quote_entries(get("kq")) if q],
                         "pairs": keyed_pairs(sheet, r, wb_mod.pairs_of(get("es"), get("kq"))),
                         "unpaired": wb_mod.unpaired(get("es"), get("kq")),
                         "places": wb_mod.quote_entries(get("kq")),
                         # what its three cells hold, which a write carries back (18 October)
                         "version": wb_mod.passage_version(get("es"), get("en"), get("kq")),
                         # another speaker's turn, skipped when moving from passage to passage (20 October)
                         "context": bool(str(get("ctx") or "").strip())})
    finally:
        wb.close()
    return rows, cols


def row_span(text: str) -> tuple[int, int]:
    m = re.match(r"^\s*(\d+)\s*(?:-\s*(\d+))?\s*$", str(text))
    if not m:
        raise cli.Refused(i18n.t("cli.row_span.is_not_a_row_number_or", text=text))
    first = int(m.group(1))
    return first, int(m.group(2) or first)


def turn_lines(t: dict, interviewer: str) -> list[str]:
    his = t["name"].strip().lower() == interviewer.strip().lower()
    lines = [i18n.t("cli.turn_lines.row", sheet=t['sheet'], row=t['row'], time=t['time'] or i18n.t("cli.said.no_timecode"), name=t['name'] or i18n.t("cli.turn_lines.no_speaker"))
             + (i18n.t("cli.turn_lines.the_interviewer") if his else i18n.t("cli.turn_lines.another_speaker") if t.get("context") else ""), f"  {t['text']}"]
    # each statement with its own quote under it, and a quote past the statements on its own
    for p in t["pairs"]:
        # a quote that takes in the same speaker's passages next to its own says which, and its range (quotespan)
        ran = i18n.t("cli.said.rows", listed=listed([str(r) for r in p['rows']]), time=p['time']) if p.get("rows") else ""
        if p["statement"]:
            lines.append(i18n.t("cli.turn_lines.statement", statement=p['statement']) + (f"  ({p['key']})" if p.get("key") else ""))
            if p["quote"]:
                lines.append(i18n.t("cli.turn_lines.quote", quote=p['quote'], ran=ran))
        else:
            lines.append(i18n.t("cli.turn_lines.quote_with_no_statement", quote=p['quote'], ran=ran))
    for item in t["notes"]:
        lines.append(i18n.t("cli.turn_lines.note", item=item))
    if not his and t.get("version"):
        lines.append(i18n.t("cli.turn_lines.version", version=t['version']))
    return lines


def cmd_turn_show(p: Project, args) -> tuple:
    b = p.case(args.case)
    book = Path(b["workbook"])
    rows, _cols = turns_of(book, args.sheet)
    first, last = row_span(args.row)
    shown = [{k: v for k, v in t.items() if k != "places"} for t in rows if first <= t["row"] <= last]
    if not shown:
        raise cli.Refused(i18n.t("cli.said.no_turn_on_at_row", sheet=args.sheet, row=args.row))
    interviewer = str(srv.config().get("interviewer") or "")
    form = wb_mod.timecodes_for(book)
    at = {t["row"]: i for i, t in enumerate(rows)}
    for t in shown:
        for pair in t["pairs"]:
            took = quote_rows(rows, at[t["row"]], pair["quote"], interviewer) if pair["quote"] else []
            if took:
                pair.update(rows=[rows[k]["row"] for k in took],
                            time=wb_mod.time_span(rows[took[0]]["seconds"], rows[took[-1]]["seconds"], form))
    lines = []
    for t in shown:
        lines += turn_lines(t, interviewer) + [""]
    return {"case": b["case"], "turns": shown}, lines[:-1]


CURLY = str.maketrans({"’": "'", "‘": "'", "“": '"', "”": '"'})


def flat_words(text: str) -> str:
    """Words as a quote is matched against its turn: curly marks made straight, double inverted
    commas dropped, and the case and the spacing set aside."""
    return " ".join(str(text).translate(CURLY).replace('"', "").lower().split())


# where a quote is cut into pieces: an ellipsis for words left out, and a clarifying insert in
# square brackets, "my rational [mind] tells me", which is the analyst's and not the turn's
QUOTE_CUTS = r"\s*(?:\.\.\.|…|\[[^\]]*\])\s*"


def quote_in(quote: str, turn: str) -> bool:
    """A quote is the participant's own words: every piece of it, split at an ellipsis or a
    clarifying insert in square brackets, in the turn in that order."""
    said = flat_words(turn)
    at = 0
    for piece in re.split(QUOTE_CUTS, str(quote)):
        piece = flat_words(piece).strip(" .,'")
        if not any(ch.isalnum() for ch in piece):
            continue
        found = said.find(piece, at)
        if found < 0:
            return False
        at = found + len(piece)
    return True


def quote_rows(rows: list[dict], at: int, quote: str, interviewer: str) -> list[int]:
    """The rows a quote takes in, as indexes into `rows`, a sheet's turns as `turns_of` reads them, when it runs
    on from the passage at `at` into the same speaker's passages next to it (quotespan, 30 October 2026), and
    [] for a quote in its own passage alone or not there at all. The rule is workbook.py's `quote_turns`, the
    one the page and print find a quote's passages by."""
    took = sorted({k for k, _, _ in wb_mod.quote_turns(rows, at, quote, interviewer)})
    return took if len(took) > 1 else []


def quote_refusal(rows: list[dict], at: int, quote: str, interviewer: str) -> str | None:
    """Why a quote is not the participant's words in the passage at `at` or the same speaker's passages next
    to it, when one of its pieces is elsewhere on the sheet: in the interviewer's turn, in another speaker's
    passage, or in her own passage past one it skips. None when no piece says why."""
    who = interviewer.strip().lower()
    mine_name = rows[at]["name"].strip().lower()
    if not mine_name or mine_name == who or rows[at].get("context"):
        return None
    run, home = wb_mod.speakers_run(rows, at, interviewer, len(rows))
    holds = lambda k, piece: bool(wb_mod.quote_reach(f'"{piece}"', [rows[k]["text"]], 0))
    said = themes.quoted(quote)
    places = []
    for piece in wb_mod.quote_pieces(quote):
        mine = [n for n, k in enumerate(run) if holds(k, piece)]
        if mine:
            places.append(min(mine, key=lambda n: abs(n - home)))
            continue
        hits = sorted((k for k in range(len(rows)) if k != at and holds(k, piece)), key=lambda k: abs(k - at))
        if not hits:
            return None
        k = hits[0]
        name = rows[k]["name"].strip().lower()
        if not name or name == who:
            return (i18n.t("cli.quote_refusal.the_quote_takes_words_from_the", said=said, row=rows[k]['row']))
        if name == mine_name and not rows[k].get("context"):
            return (i18n.t("cli.quote_refusal.the_quote_takes_words_from_row", said=said, row=rows[k]['row']))
        return (i18n.t("cli.quote_refusal.the_quote_takes_words_from_another", said=said, row=rows[k]['row']))
    lo, hi = min(places + [home]), max(places + [home])
    skipped = [run[n] for n in range(lo, hi + 1) if n not in places]
    if skipped:
        return (i18n.t("cli.quote_refusal.the_quote_skips_the_passage_at", said=said, row=rows[skipped[0]]['row']))
    return None


def field(value) -> list[str] | None:
    if value is None:
        return None
    if isinstance(value, str):
        return [line.strip() for line in value.splitlines() if line.strip()]
    if isinstance(value, list):
        return [" ".join(str(x).split()) for x in value if str(x).strip()]
    raise cli.Refused(i18n.t("cli.said.a_turns_statements_notes_and_quotes"))




def places_of(value) -> list[str] | None:
    """The quotes list as the two lists send it, one place a statement in order: an empty entry,
    null or "(no quote)" is a statement with none."""
    if value is None:
        return None
    if isinstance(value, str):
        items = value.rstrip().splitlines()
    elif isinstance(value, list):
        items = value
    else:
        raise cli.Refused(i18n.t("cli.said.a_turns_statements_notes_and_quotes"))
    out = [" ".join(str(x if x is not None else "").split()) for x in items]
    return ["" if wb_mod.no_quote(q) else q for q in out]


def pairs_given(raw) -> tuple[list[str], list[str], list[str]]:
    """`pairs` read strictly into the statements and their quotes by place, a statement's quote
    empty for none, and the lone quotes, each a pair with a quote and no statement, in the order
    given. A pair with neither is passed over."""
    if not isinstance(raw, list) or not all(isinstance(x, dict) for x in raw):
        raise cli.Refused(_w("PAIRS_SHAPE"))
    statements, places, lone = [], [], []
    for x in raw:
        statement = " ".join(str(x.get("statement") or "").split())
        quote = " ".join(str(x.get("quote") or "").split())
        quote = "" if wb_mod.no_quote(quote) else quote
        if statement:
            statements.append(statement)
            places.append(quote)
        elif quote:
            lone.append(quote)
    return statements, places, lone




def pair_keys(raw, sheet: str, row: int, held: int) -> tuple[list | None, list[str]]:
    """The line of the passage each statement of `pairs` says it is, by the key turn show gave it, None
    for a pair with no key, a statement new to the passage, and None for the whole when no pair sends
    one. `held` is how many statements the passage holds. With the lines, a line for each key that
    cannot stand."""
    if not isinstance(raw, list):
        return None, []
    named, problems, seen = [], [], set()
    for x in raw:
        if not isinstance(x, dict) or not " ".join(str(x.get("statement") or "").split()):
            continue
        key = str(x.get("key") or "").strip()
        if not key:
            named.append(None)
            continue
        s, r, line = themes.split_card_key(key)
        if (s, r) != (sheet, row) or line is None or not 0 <= line < held:
            problems.append(f"{key} {_w('NOT_THIS_LINE')}")
            named.append(None)
        elif line in seen:
            problems.append(f"{key} {_w('KEY_TWICE')}")
            named.append(None)
        else:
            seen.add(line)
            named.append(line)
    return (named if seen else None), problems


def quote_lines(old_places: list[str], held: int, new_places: list[str], made: int, lines: dict) -> dict:
    """Where each quote of a passage goes when a write moves its lines: a statement's own quote
    with its statement, by `lines`, and a lone quote, past the `held` statements' places, to the lone
    place of the `made` statements' passage with the same words, or None when it has gone."""
    out = {i: lines.get(i) for i in range(held)}
    free = [j for j in range(made, len(new_places)) if new_places[j]]
    for i in range(held, len(old_places)):
        if not old_places[i]:
            continue
        hit = next((j for j in free if themes.quote_words(new_places[j]) == themes.quote_words(old_places[i])), None)
        out[i] = hit
        if hit is not None:
            free.remove(hit)
    return out


def card_lines(boards: list[dict], dry: bool) -> list[str]:
    """What a write does to the boards' cards, a line each: a card moved to its statement's new line,
    and a card taken off with its removed statement."""
    out = []
    for b in boards:
        for m in b["moved"]:
            went = i18n.t("cli.card_lines.would_move_to") if dry else i18n.t("cli.card_lines.moved_to")
            out.append(i18n.t("cli.card_lines.on_the_card_where_its_statement", name=b['name'], from_=m['from'], text=m['text'], went=went, to=m['to']))
        for m in b["removed"]:
            went = i18n.t("cli.card_lines.would_be_taken_off") if dry else i18n.t("cli.card_lines.was_taken_off")
            out.append(i18n.t("cli.card_lines.on_the_card_its_statement_removed", name=b['name'], key_=m['key'], text=m['text'], went=went))
    return out


def lone_of(turn: dict) -> list[str]:
    """A turn's lone quotes, each a quote past its statements' places with no statement of its own,
    in their order, as the turn screen saves one, last (item 198)."""
    return [q for q in turn["places"][len(turn["statements"]):] if q]


def lone_after(held: list[str], given: list[str], named: list[str]) -> list[str]:
    """The lone quotes a write leaves. Each of the turn's own that the write does not name keeps its
    place among them, as it stands, and the ones the write gives fill the places round them, in its
    order. A quote is named when the write gives the same words, its inverted commas set aside, for
    a statement or on its own, so a lone quote can be moved on purpose."""
    said = {themes.quote_words(q) for q in named if q}
    out = list(given)
    for i, q in enumerate(held):
        if themes.quote_words(q) not in said:
            out.insert(min(i, len(out)), q)
    return out


def effect_lines(kept: list[str], given: list[str], picks: list[dict], dry: bool, gone: list[str] = ()) -> list[str]:
    """What a turn write says of the lone quotes it keeps, writes and removes, and of each pick it
    moves or drops on a board."""
    lines = []
    if gone:
        verb = i18n.t("cli.effect_lines.it_would_remove") if dry else i18n.t("cli.effect_lines.it_removed")
        lines.append(i18n.t("cli.effect_lines.as_asked", verb=verb, quotes=i18n.t("cli.n.lone_quote", n=len(gone))) + ", ".join(themes.quoted(q) for q in gone) + ".")
    if kept:
        verb = i18n.t("cli.effect_lines.it_would_keep") if dry else i18n.t("cli.effect_lines.it_kept")
        lines.append(i18n.t("cli.effect_lines.the_turns_with_no_statement_of", verb=verb, quotes=i18n.t("cli.n.lone_quote", n=len(kept)), v_='its' if len(kept) == 1 else 'their', v_2=i18n.t("cli.effect_lines.it_stands") if len(kept) == 1 else i18n.t("cli.effect_lines.they_stand"))
                     + ", ".join(themes.quoted(q) for q in kept) + ".")
    if given:
        verb = i18n.t("cli.said.it_would_write") if dry else i18n.t("cli.effect_lines.it_wrote")
        lines.append(f"{verb} {i18n.t('cli.n.lone_quote', n=len(given))}: " + ", ".join(themes.quoted(q) for q in given) + ".")
    for m in picks:
        title = f"'{m['title']}'" if m["title"] else m["label"]
        if m["to"]:
            went = (i18n.t("cli.effect_lines.would_move_to", to=m['to']) if dry else i18n.t("cli.effect_lines.moved_to", to=m['to'])) + i18n.t("cli.effect_lines.where_its_words_now_are")
        else:
            went = (i18n.t("cli.effect_lines.would_be_dropped") if dry else i18n.t("cli.effect_lines.was_dropped")) + i18n.t("cli.effect_lines.its_words_no_longer_on_a")
        lines.append(i18n.t("cli.effect_lines.on_the_pick_on", name=m['name'], key_=m['key'], title=title, went=went))
    return lines


def span_lines(spans: list[dict], sheet: str, dry: bool) -> list[str]:
    """A line for each quote of a write that takes in the same speaker's passages next to its own, the rows
    and the range print gives it (quotespan)."""
    verb = i18n.t("cli.said.would_take") if dry else "takes"
    return [i18n.t("cli.span_lines.the_quote_in_rows_of", quote=s['quote'], verb=verb, listed=listed([str(r) for r in s['rows']]), sheet=sheet, time=s['time'])
            for s in spans]


def added_lines(added, held, dry: bool) -> list[str]:
    """What `add_notes` adds and keeps, in one line."""
    if not added:
        return []
    new = [n for n in added if n not in held]
    verb = i18n.t("cli.added_lines.it_would_add") if dry else i18n.t("cli.added_lines.it_added")
    kept = i18n.t("cli.added_lines.keeping_the_there", notes=i18n.t("cli.n.note", n=len(held))) if held else ""
    return [f"{verb} {i18n.t('cli.n.exploratory_note', n=len(new))}{kept}."] if new else []


def cmd_turn_write(p: Project, args) -> tuple:
    """A turn written, its statements' cards carried on the boards of the timepoint its sheet is at
    (21 October), T1's in a project of one timepoint, as always."""
    book = Path(p.case(args.case)["workbook"])
    with themes.scoped(themes.placed_sheets(book).get(str(args.sheet), 1)):
        return turn_write(p, args)


def turn_write(p: Project, args) -> tuple:
    b = p.case(args.case)
    book = Path(b["workbook"])
    # a participant another member of the team works on is refused first, whatever the write would change, its
    # dry run too, never "Nothing to write" (smokefix, 9 November 2026)
    if wb_mod.WRITE_GUARD is not None:
        try:
            wb_mod.WRITE_GUARD(book)
        except WorkbookError as exc:
            raise cli.Refused(str(exc)) from None
    spec = cli.read_spec(args.source)
    if not isinstance(spec, dict):
        raise cli.Refused(_w("TURN_SHAPE"))
    request = themes_ai.one_line(spec.get("request") or args.note)
    if not request:
        raise cli.Refused(_w("NO_REQUEST"))
    args.note = request
    if spec.get("pairs") is not None and (spec.get("statements") is not None or spec.get("quotes") is not None):
        raise cli.Refused(_w("PAIRS_OR_LISTS"))
    # a statement and its quote go by place: `pairs` says so outright, and the two lists by order
    if spec.get("pairs") is not None:
        statements, places, given_lone = pairs_given(spec["pairs"])
    else:
        statements, places, given_lone = field(spec.get("statements")), places_of(spec.get("quotes")), []
    notes = field(spec.get("notes"))
    # `add_notes` adds exploratory notes after those the passage holds, every one of them kept (19 October)
    added = field(spec.get("add_notes"))
    if added is not None and notes is not None:
        raise cli.Refused(_w("NOTES_OR_ADD"))
    # `remove` names lone quotes to take out on purpose, the one way a write drops a lone quote
    remove = field(spec.get("remove"))
    if statements is None and places is None and notes is None and added is None and not remove:
        raise cli.Refused(i18n.t("cli.turn_write.the_file_names_no_statements_notes"))
    first, last = row_span(args.row)
    if first != last:
        raise cli.Refused(i18n.t("cli.said.a_write_takes_one_turn_at"))
    rows, cols = turns_of(book, args.sheet)
    turn = next((t for t in rows if t["row"] == first), None)
    if turn is None:
        raise cli.Refused(i18n.t("cli.turn_write.no_turn_on_at_row", sheet=args.sheet, first=first))
    if added is not None:
        # the passage's notes as they stand, then each added one it does not hold already
        notes = list(turn["notes"]) + [n for n in added if n not in turn["notes"]]
    # the version the agent read with turn show, refused when the passage reads otherwise now
    seen = spec.get("version")
    if seen is not None and str(seen).strip() != turn["version"]:
        raise cli.Refused(_w("STALE_WRITE"))
    interviewer = str(srv.config().get("interviewer") or "")
    problems = []
    if turn["name"].strip().lower() == interviewer.strip().lower():
        problems.append(i18n.t("cli.turn_write.that_turn_is_the_interviewers_and"))
    # each pair's key, as turn show gave it, says which statement of the passage it is, so every
    # board's card follows its statement whatever a write removes or rewords (20 October)
    named, bad_keys = pair_keys(spec.get("pairs"), args.sheet, first, len(turn["statements"]))
    problems += bad_keys
    named_quotes = (places or []) + given_lone
    for role, word, given in (("es", "statements", statements), ("en", i18n.t("cli.turn_write.exploratory_notes"), notes),
                              ("kq", "quotes", named_quotes if any(named_quotes) else None)):
        if given is not None and role not in cols:
            problems.append(i18n.t("cli.turn_write.the_sheet_has_no_column_for", word=word))
    # the turn's lone quotes, past its statements' places with no statement of their own, are kept
    # by every write that does not name them, in their places
    held_lone = lone_of(turn)
    gone = []
    for q in remove or []:
        hit = next((h for h in held_lone if themes.quote_words(h) == themes.quote_words(q) and h not in gone), None)
        if hit is None:
            problems.append(i18n.t("cli.turn_write.the_quote", quoted=themes.quoted(q), not_lone=_w("NOT_LONE")))
        else:
            gone.append(hit)
    held_lone = [h for h in held_lone if h not in gone]
    # statements alone on a turn saved before the pairs leave its quotes as they are, for him to pair,
    # and on a turn with a lone quote they go with the quotes in their places, the lone ones kept after
    keep_quotes = places is None and not given_lone and turn["unpaired"] and not held_lone and not gone
    pairing = (statements is not None or places is not None or bool(gone)) and not keep_quotes
    final_s = statements if statements is not None else turn["statements"]
    # a quote goes in inverted commas, once, as `q` on the turn screen writes one
    own = turn["places"][:len(turn["statements"])]
    final_q = [themes.quoted(q) if q else "" for q in (places if places is not None else own)]
    if gone and statements is None and places is None:
        # a removal alone leaves the statements' own quotes as they stand, one a statement
        final_q = list(own) + [""] * (len(final_s) - len(own))
    lone = lone_after(held_lone, [themes.quoted(q) for q in given_lone], named_quotes) if pairing else held_lone
    named_words = {themes.quote_words(q) for q in named_quotes if q}
    kept_lone = [q for q in held_lone if themes.quote_words(q) not in named_words] if pairing else held_lone
    if pairing and any(final_q) and len(final_q) != len(final_s):
        if places is not None:
            problems.append(i18n.t("cli.turn_write.for_a_statement_and_its_quote", quotes=i18n.t("cli.n.quote", n=len(final_q)), statements=i18n.t("cli.n.statement", n=len(final_s))))
        else:
            problems.append(i18n.t("cli.turn_write.the_turns_quotes_go_with_its", statements=i18n.t("cli.n.statement", n=len(final_s)), quotes=i18n.t("cli.n.quote", n=len(final_q))))
    # a quote the turn already holds, a sibling sent back unchanged, is not checked again
    held_words = {themes.quote_words(h) for h in list(turn["places"]) + lone_of(turn) if h}
    # and one not in the turn's own words may take in the same speaker's passages next to it (quotespan)
    at = rows.index(turn)
    form = wb_mod.timecodes_for(book)
    spans = []
    for q in (final_q if places is not None else []) + given_lone:
        if q and themes.quote_words(q) not in held_words and not quote_in(q, turn["text"]):
            took = quote_rows(rows, at, q, interviewer)
            if took:
                spans.append({"quote": themes.quoted(q), "rows": [rows[k]["row"] for k in took],
                              "time": wb_mod.time_span(rows[took[0]]["seconds"], rows[took[-1]]["seconds"], form)})
                continue
            problems.append(quote_refusal(rows, at, q, interviewer)
                            or i18n.t("cli.turn_write.the_quote_is_not_in_the", quoted=themes.quoted(q)))
    if problems:
        raise cli.Refused(*problems, i18n.t("cli.said.nothing_was_written"))
    pairs = [{"es": s, "kq": final_q[i] if i < len(final_q) else ""} for i, s in enumerate(final_s)]
    # a lone quote is a pair with no statement, which `pairs_to_cells` keeps after the statements' places
    pairs += [{"es": "", "kq": q} for q in lone] if pairing else []
    es_cell, kq_cell = wb_mod.pairs_to_cells(pairs)
    before = {"es": turn["statements"], "en": turn["notes"],
              "kq": [q or wb_mod.NO_QUOTE for q in turn["places"]] if any(turn["places"]) else []}
    wanted = {"es": wb_mod.split_entries(es_cell) if pairing else statements, "en": notes,
              "kq": wb_mod.split_entries(kq_cell) if pairing else None}
    changing = {r: v for r, v in wanted.items() if v is not None and v != before[r]}
    names = {"es": "statements", "en": i18n.t("cli.turn_write.exploratory_notes"), "kq": "quotes"}
    if not changing:
        text = i18n.t("cli.turn_write.nothing_to_write_the_turn_already")
        return {"case": b["case"], "changed": False, "said": text}, [text]
    counted = lambda r, v: len([x for x in v if not wb_mod.no_quote(x)]) if r == "kq" else len(v)
    said = ", ".join(i18n.t("cli.turn_write.before_and_after", names=names[r], counted=counted(r, before[r]), counted2=counted(r, v)) for r, v in changing.items())
    where = i18n.t("cli.turn_write.row_of", sheet=args.sheet, first=first, case=b['case'])
    # the turn as the write leaves it, read against every board of the case for the picks it moves
    # or drops, and the lone quotes it keeps and writes
    written_lone = [themes.quoted(q) for q in given_lone] if pairing else []
    after_s = wb_mod.split_entries(es_cell) if pairing else (statements if statements is not None else turn["statements"])
    after_q = wb_mod.quote_entries(kq_cell) if pairing else turn["places"]
    # each statement's line before and after, by the keys the pairs sent or else by their words, and
    # each quote's with it, so every board's cards and picks follow them (20 October)
    moves_lines = moves_quotes = None
    if {"es", "kq"} & set(changing):
        moves_lines = themes.passage_lines(turn["statements"], after_s, named)
        moves_quotes = (quote_lines(turn["places"], len(turn["statements"]), after_q, len(after_s), moves_lines)
                        if pairing else {i: i for i in range(len(turn["places"]))})
    history = themes_ai.revision_name(request)

    def carry(now: dict, then: dict, dry: bool, changed: dict | None = None) -> tuple[list[dict], list[str]]:
        if moves_lines is None:
            return [], []
        try:
            return themes.passage_written(book, args.sheet, first, turn["statements"], after_s, moves_lines,
                                          moves_quotes, now, then, dry=dry, history=history, changed=changed), []
        except (WorkbookError, OSError) as exc:
            return [], [i18n.t("cli.turn_write.the_boards_could_not_be_read", exc=exc)]

    def effects_of(boards: list[dict]) -> dict:
        picks = [dict(m, board=x["board"], name=x["name"]) for x in boards for m in x["picks"]]
        cards = [{k: x[k] for k in ("board", "name", "moved", "removed")} for x in boards if x["moved"] or x["removed"]]
        return {"lone_kept": kept_lone, "lone_written": written_lone, "lone_removed": gone, "picks": picks,
                "cards": cards}

    def history_line(boards: list[dict], dry: bool) -> list[str]:
        if not boards:
            return []
        names = listed([x["name"] for x in boards])
        verb = i18n.t("cli.said.would_keep") if dry else "keeps"
        return [i18n.t("cli.turn_write.the_board_as_it_stood_first", names=names, verb=verb, history=history)]

    # each statement reworded in its own place, by its key, which the GETs' copies follow as an edit on a board
    # does (getsedit, 30 October), one that moves or goes left for him to take with the participant's changes
    reworded = {themes.card_key(args.sheet, first, i): (turn["statements"][i], after_s[i])
                for i, j in (moves_lines or {}).items()
                if j == i and i < len(after_s) and themes.words(turn["statements"][i]) != themes.words(after_s[i])}

    if args.dry_run:
        try:
            now = themes.read_cards(book)
            boards, failed = carry(now, themes.with_row(now, args.sheet, first, after_s, after_q), True)
        except (WorkbookError, OSError):
            boards, failed = [], []
        copies = routes.follow_statements(book, reworded, {}, dry=True) if reworded else {}
        effects = effects_of(boards)
        text = i18n.t("cli.turn_write.dry_run_nothing_was_written_it", said=said, where=where)
        lines = ([text] + span_lines(spans, args.sheet, True) + added_lines(added, turn["notes"], True)
                 + card_lines(boards, True)
                 + effect_lines(kept_lone, written_lone, effects["picks"], True, gone) + history_line(boards, True) + failed
                 + copy_lines(copies, history, True))
        return {"dry_run": True, "case": b["case"], "before": before, "after": {**before, **changing}, "said": text,
                "copies": copies, "spans": spans, **effects}, lines
    wb_mod.guard_lock(book)
    # the root's lock first, as the app takes it, since the GETs' copies are written with the workbook
    with locks.root(p.root), wb_mod.case_held(book):
        wb_mod.guard_lock(book)
        copies_were = routes.copies_before(book) if reworded else {}
        backup = wb_mod.archive_copy(book, "pre-agent")
        paired = pairing and ("es" in changing or "kq" in changing)
        try:
            now = themes.read_cards(book) if moves_lines is not None else None
        except (WorkbookError, OSError):
            now = None
        try:
            # the passage as this write read it, so a save made between the read and the lock is
            # never written over
            wb_mod.save_turn(book, args.sheet, first,
                             "\n".join(changing["es"]) if "es" in changing and not paired else None,
                             "\n".join(changing["en"]) if "en" in changing else None, None,
                             pairs=pairs if paired else None, was=turn["version"])
        except wb_mod.StaleTurn:
            raise cli.Refused(_w("STALE_WRITE")) from None
        progress = rounds_mod.load_progress(book)
        key = rounds_mod.row_key(args.sheet, first)
        has = bool(changing.get("es", before["es"]))
        progress["rows"][key] = rounds_mod.HAS_CONTENT if has else rounds_mod.REVIEWED_EMPTY
        at = now_iso()
        who = mark(args, at)
        progress.setdefault("edits", []).append({
            "sheet": args.sheet, "row": first, "by": who["by"], "tool": who["tool"], "request": request,
            **{k: who[k] for k in themes.MEMBER_KEYS if k in who},
            "when": datetime.now().isoformat(timespec="seconds"),
            "before": {r: before[r] for r in changing}, "after": changing, "backup": backup.name})
        rounds_mod.save_progress(book, progress)
        # every board moves with the passage's lines, the removed statements' cards taken off, and a
        # statement reworded takes its new words on every card that held the old
        boards, failed = carry(now, themes.read_cards(book), False, mark(args, at)) if now is not None else ([], [])
        # and the GETs' copies of the participant, a board with a card of it marked changed in a conversation
        copies = routes.follow_statements(book, reworded, copies_were, changed=mark(args, at),
                                          history=history) if reworded else {}
    effects = effects_of(boards)
    carried = [{"board": x["board"], "name": x["name"], "keys": x["reworded"]} for x in boards if x["reworded"]]
    text = (i18n.t("cli.turn_write.wrote_the_on_after_a_copy", said=said, where=where, name=backup.name))
    lines = ([text] + span_lines(spans, args.sheet, False) + added_lines(added, before["en"], False)
             + card_lines(boards, False) + effect_lines(kept_lone, written_lone, effects["picks"], False, gone))
    if carried:
        names = [c["name"] for c in carried]
        lines.append(i18n.t("cli.turn_write.on_took_the_new_words", cards=i18n.t("cli.n.card", n=sum(len(c['keys']) for c in carried)), list=', '.join(names)))
    if boards:
        lines += history_line(boards, False)
        lines.append(i18n.t("cli.turn_write.each_is_marked_as_changed_in"))
    lines += failed + copy_lines(copies, history, False)
    return {"case": b["case"], "sheet": args.sheet, "row": first, "written": changing, "backup": backup.name,
            "boards_reworded": carried, "copies": copies, "spans": spans, "said": text, **effects}, lines


def copy_lines(copies: dict, history: str, dry: bool) -> list[str]:
    """What a write's reworded statements do to the GETs' copies of the participant (see
    `routes.follow_statements`), a line for each file whose copy takes the words, naming the boards with a card
    of them, and the line of a file that could not be read."""
    out = []
    for kind in routes.COPY_NAMES:
        done = copies.get(kind)
        if not done:
            continue
        name = routes.COPY_NAMES[kind]
        verb = i18n.t("cli.said.would_take") if dry else "took"
        line = i18n.t("cli.copy_lines.the_copy_of_the_participant_the", name=name, verb=verb)
        if done["boards"]:
            n = sum(len(x["keys"]) for x in done["boards"])
            names = listed([x["name"] for x in done["boards"]])
            line += (i18n.t("cli.copy_lines.and_on_with_them", cards=i18n.t("cli.n.card", n=n), names=names)
                     + (i18n.t("cli.said.would_keep") if dry else "keeps") + i18n.t("cli.copy_lines.the_board_as_it_stood_first", history=history, name=name))
        else:
            line += "."
        out.append(line)
    return out + list(copies.get("failed") or [])


# ------------------------------------------------------- the statements screen's own writes
# (26 October 2026, parity with the page, group 1: a route the statements screen calls had no op for an
# agent.) A passage's words corrected (`/api/edit-turn`), the interviewer's note on his own passage
# (`/api/interviewer-note`), words assigned to another speaker and its undo (`/api/rows`), the consent
# talk or the goodbyes cut off a sheet and its undo (`/api/trim`, `/api/rows`), and transcripts added to a
# project (`/api/add-transcripts`), each by calling the route itself with the body the page sends, its
# dry run, his request and the agent's tool beside it. The route holds the lock, the checks, the History
# record and the refusals, so nothing here repeats them.



def route_call(route, body: dict) -> dict:
    """A route the page calls, called with the page's body: its answer, or its refusal as one line with
    nothing written."""
    try:
        return route(body)
    except (WorkbookError, srv.OutsideRoot) as exc:
        raise cli.Refused(str(exc), i18n.t("cli.said.nothing_was_written")) from None


def turn_marks(args) -> dict:
    """What every write here sends the route beside the page's body: its dry run, his request and the
    agent's tool, refused without his request unless it is a dry run."""
    request = themes_ai.one_line(args.note)
    if not args.dry_run and not request:
        raise cli.Refused(_w("NO_TURN_REQUEST"))
    return {"dry_run": bool(args.dry_run), "request": request, "tool": themes_ai.one_line(args.tool) or cli.TOOL}


def one_row(args) -> int:
    """The one passage a write names, by its row."""
    first, last = row_span(args.row)
    if first != last:
        raise cli.Refused(i18n.t("cli.said.a_write_takes_one_turn_at"))
    return first


def passage_words(book: Path, sheet: str, row: int) -> str:
    """A passage's words as the workbook holds them, every character, as the page holds them when it
    sends a timecode alone or counts a selection's place."""
    rows, _cols = turns_of(book, sheet)
    if not any(t["row"] == row for t in rows):
        raise cli.Refused(i18n.t("cli.said.no_turn_on_at_row", sheet=sheet, row=row))
    wb = openpyxl.load_workbook(book, read_only=True)
    try:
        ws = wb[sheet]
        cols = wb_mod.detect_columns(ws)
        return wb_mod.plain_text(ws.cell(row, cols["transcript"]).value)
    finally:
        wb.close()


def cmd_turn_edit(p: Project, args) -> tuple:
    """A passage's words corrected in place, and its timecode with them, as the statements screen's Edit
    does (`routes.api_edit_turn`): the cell keeps its style, a highlight is found again by its words or
    dropped and named, and the progress file keeps the old words and the new under `edits`."""
    b = p.case(args.case)
    book = Path(b["workbook"])
    row = one_row(args)
    if args.text is None and args.time is None:
        raise cli.Refused(_w("EDIT_NEEDS"))
    marks = turn_marks(args)
    text = args.text if args.text is not None else passage_words(book, args.sheet, row)
    body = dict({"path": str(book), "sheet": args.sheet, "row": row, "text": text}, **marks)
    if args.time is not None:
        body["timecode"] = args.time
    done = route_call(routes.api_edit_turn, body)
    where = i18n.t("cli.said.row", case=b['case'], sheet=args.sheet, row=row)
    answer = dict(done, case=b["case"])
    if args.dry_run:
        if not done["changed"]:
            return answer, [i18n.t("cli.turn_edit.dry_run_nothing_was_written_reads", where=where)]
        lines = [i18n.t("cli.turn_edit.dry_run_nothing_was_written_the", where=where)
                 + (i18n.t("cli.turn_edit.and_the_timecode_go_from_to", old_time=done['old_time'], time=done['time']) if done["old_time"] != done["time"] else "")
                 + "."]
        if done["dropped"]:
            lines.append(i18n.t("cli.turn_edit.would_be_dropped_its_words_gone", highlights=i18n.t("cli.n.highlight", n=len(done['dropped'])))
                         + ", ".join(f'"{d}"' for d in done["dropped"]) + ".")
        return answer, lines
    if not done["changed"]:
        return answer, [i18n.t("cli.turn_edit.reads_so_already_so_nothing_was", where=where)]
    lines = [i18n.t("cli.turn_edit.corrected_its_timecode_the_progress_file", where=where, time=done['time'] or 'none')]
    if done["dropped"]:
        lines.append(i18n.t("cli.turn_edit.dropped_its_words_gone", highlights=i18n.t("cli.n.highlight", n=len(done['dropped']))) + ", ".join(f'"{d}"' for d in done["dropped"]) + ".")
    return answer, lines


def cmd_turn_interviewer_note(p: Project, args) -> tuple:
    """The interviewer's note on one of his own passages, in the workbook's Interviewer notes column, as
    the statements screen writes it (`routes.api_interviewer_note`), an empty one clearing it. His passage
    stays context: its row's state and the rounds are as they were, and History keeps the note."""
    b = p.case(args.case)
    book = Path(b["workbook"])
    row = one_row(args)
    marks = turn_marks(args)
    done = route_call(routes.api_interviewer_note,
                      dict({"path": str(book), "sheet": args.sheet, "row": row, "text": args.text or ""}, **marks))
    where = i18n.t("cli.said.row", case=b['case'], sheet=args.sheet, row=row)
    answer = dict(done, case=b["case"])
    verb = "cleared" if not done["text"] else "written"
    if args.dry_run:
        return answer, [i18n.t("cli.turn_interviewer_note.dry_run_nothing_was_written_the_2", where=where, verb=verb)
                        if done["changed"] else i18n.t("cli.turn_interviewer_note.dry_run_nothing_was_written_the", where=where)]
    if not done["changed"]:
        return answer, [i18n.t("cli.turn_interviewer_note.the_interviewers_note_on_reads_so", where=where)]
    return answer, [i18n.t("cli.turn_interviewer_note.the_interviewers_note_on_the_progress", where=where, verb=verb)]


def assign_span(book: Path, args, row: int) -> tuple:
    """The words of a passage an assignment takes, by --words found once in it or by --start and --end,
    or none for the whole passage."""
    if args.words is not None and (args.start is not None or args.end is not None):
        raise cli.Refused(_w("WORDS_OR_SPAN"))
    if (args.start is None) != (args.end is None):
        raise cli.Refused(_w("SPAN_BOTH"))
    if args.words is None:
        return args.start, args.end
    text = passage_words(book, args.sheet, row)
    found = [m.start() for m in re.finditer(re.escape(args.words), text)] if args.words else []
    if not found:
        raise cli.Refused(_w("WORDS_NOT_THERE"))
    if len(found) > 1:
        raise cli.Refused(_w("WORDS_TWICE").format(n=len(found)))
    return found[0], found[0] + len(args.words)


def cmd_turn_assign(p: Project, args) -> tuple:
    """Words of a passage, or the whole of it, assigned to another speaker, as the statements screen's
    Assign does (`routes.api_rows`, op assign): a passage of their own, or joined to the next speaker's
    beside it, a copy of the workbook in _Archive first, the progress file and every board moving with
    the rows. The dry run answers what the confirm card says, what merges and what the rows carry."""
    b = p.case(args.case)
    book = Path(b["workbook"])
    row = one_row(args)
    start, end = assign_span(book, args, row)
    marks = turn_marks(args)
    done = route_call(routes.api_rows, dict({"op": "assign", "path": str(book), "sheet": args.sheet, "row": row,
                                             "to": args.to, "start": start, "end": end}, **marks))
    answer = dict(done, case=b["case"])
    if args.dry_run:
        return answer, [i18n.t("cli.turn_assign.dry_run_nothing_was_written", case=b['case'], line=done['line']), done["carries"]]
    if not done["whole"]:
        said = (i18n.t("cli.turn_assign.the_words_are_s_now_joined", to=done['to']) if done["merged"]
                else i18n.t("cli.turn_assign.the_words_are_s_now_in", to=done['to']))
    else:
        said = (i18n.t("cli.turn_assign.the_passage_is_s_now_one", to=done['to'], v_=i18n.t("cli.turn_assign.s_either_side") if done['merged'] > 1 else i18n.t("cli.turn_assign.beside_it"))
                if done["merged"] else i18n.t("cli.turn_assign.the_passage_is_s_now", to=done['to']))
    lines = [i18n.t("cli.turn_assign.row", case=b['case'], sheet=args.sheet, row=row, said=said),
             i18n.t("cli.turn_assign.a_copy_of_the_workbook_as", case=b['case'], id=done['id'])]
    if done.get("themes"):
        lines.append(done["themes"])
    return answer, lines


def cmd_turn_assign_undo(p: Project, args) -> tuple:
    """An assignment undone by the id it answered with, as Cmd + Z does on the statements screen
    (`routes.api_rows`, op restore): the rows put back from its copy in _Archive, anything written on
    them since landing on the passage it was made on."""
    b = p.case(args.case)
    marks = turn_marks(args)
    done = route_call(routes.api_rows, dict({"op": "restore", "path": str(b["workbook"]), "id": args.id}, **marks))
    answer = dict(done, case=b["case"])
    if args.dry_run:
        return answer, [i18n.t("cli.turn_assign_undo.dry_run_nothing_was_written_the", case=b['case'], sheet=done['sheet'], row=done['row'], to=done['to'], name=Path(done['backup']).name)]
    lines = [i18n.t("cli.turn_assign_undo.the_rows_are_back_as_they", case=b['case'])
             + (i18n.t("cli.turn_assign_undo.written_since_went_onto_the_passage", lines=i18n.t("cli.n.line", n=done['appended'])) if done.get("appended") else "")]
    if done.get("themes"):
        lines.append(done["themes"])
    return answer, lines


def cmd_turn_trim(p: Project, args) -> tuple:
    """The consent talk cut off the front of a sheet, the passage named and every one above it, or the
    goodbyes off its back, the passage named and every one below, as the statements screen's trim card
    does (`routes.api_trim`): a copy of the workbook in _Archive first, the progress file and every board
    moving with the rows, each board keeping the cut rows' cards aside for the undo."""
    b = p.case(args.case)
    book = Path(b["workbook"])
    row = one_row(args)
    if args.before == args.after:
        raise cli.Refused(_w("TRIM_SIDE"))
    marks = turn_marks(args)
    done = route_call(routes.api_trim, dict({"path": str(book), "sheet": args.sheet, "row": row,
                                             "direction": "before" if args.before else "after"}, **marks))
    answer = dict(done, case=b["case"])
    span = (i18n.t("cli.turn_trim.rows_to", first=done['first'], last=done['last']) if done["first"] != done["last"] else f"row {done['first']}")
    times = i18n.t("cli.turn_trim.to", from_=done['from'], to=done['to']) if done.get("from") else ""
    if args.dry_run:
        return answer, [i18n.t("cli.turn_trim.dry_run_nothing_was_written_it", case=b['case'], sheet=args.sheet, span=span, times=times, rows=i18n.t("cli.n.row", n=done['count']), marked=done['marked'], rows2=i18n.t("cli.n.row", n=done['left']))]
    lines = [i18n.t("cli.turn_trim.cut_after_a_copy_of_the", case=b['case'], sheet=args.sheet, span=span, times=times, rows=i18n.t("cli.n.row", n=done['removed']), id=done['id'])]
    if done.get("themes"):
        lines.append(done["themes"])
    return answer, lines


def cmd_turn_trim_undo(p: Project, args) -> tuple:
    """A trim undone by the id it answered with, as Cmd + Z does on the statements screen (`routes.api_rows`,
    op untrim): the rows it cut put back where they were from its copy in _Archive, the boards' cards with
    them. A later trim on the sheet is undone first."""
    b = p.case(args.case)
    marks = turn_marks(args)
    done = route_call(routes.api_rows, dict({"op": "untrim", "path": str(b["workbook"]), "id": args.id}, **marks))
    answer = dict(done, case=b["case"])
    if args.dry_run:
        return answer, [i18n.t("cli.turn_trim_undo.dry_run_nothing_was_written_rows", case=b['case'], sheet=done['sheet'], first=done['first'], last=done['last'])]
    lines = [i18n.t("cli.turn_trim_undo.back_where_they_were_cut_from", case=b['case'], sheet=done['sheet'], rows=i18n.t("cli.n.row", n=done['restored']))]
    if done.get("themes"):
        lines.append(done["themes"])
    return answer, lines


def add_entries(p: Project, spec) -> list[dict]:
    """The transcripts an Add names (see `read_entries`), a file by its path from the project's folder or in full."""
    return read_entries(p.root, spec)


def read_entries(base: Path, spec) -> list[dict]:
    """The transcripts an Add or a new project names, each read from its file, by its path from `base` or in
    full, into the row the page's card sends: the file's name and its contents, the columns, the sheet and the
    speakers' roles in the card's words, the pseudonym, the interview (guessed from the file's name as the
    card guesses it when none is given), the number and the timepoint, and a recording to copy in with its offset
    (audioop, 9 November 2026). New project's `--sheet` and `--columns` go through here too."""
    items = spec.get("files") if isinstance(spec, dict) else spec
    if not isinstance(items, list) or not items or not all(isinstance(x, dict) and x.get("file") for x in items):
        raise cli.Refused(_w("ADD_SHAPE"))
    rows = []
    for item in items:
        path = Path(str(item["file"])).expanduser()
        path = path if path.is_absolute() else Path(base) / path
        try:
            data = path.read_bytes()
        except OSError:
            raise cli.Refused(i18n.t("cli.add_entries.could_not_be_read_so_nothing", file=item['file'])) from None
        speakers = item.get("speakers")
        if speakers is not None:
            if not isinstance(speakers, dict):
                raise cli.Refused(i18n.t("cli.add_entries.give_each_speakers_role_as_sam"))
            roles = {}
            for name, role in speakers.items():
                word = convert_mod.role_word(role)
                if word is None:
                    raise cli.Refused(f"{role} {_w('NOT_A_SPEAKER_ROLE')}")
                roles[" ".join(str(name).split())] = word
            speakers = roles
        row = {"name": path.name, "data": base64.b64encode(data).decode("ascii"),
               "columns": import_roles(item.get("columns")),
               **({"sheet": " ".join(str(item["sheet"]).split())} if item.get("sheet") else {})}
        # the file read as the card reads it when it is dropped (New project's `read`), so each speaker's
        # role is the card's guess where none is given, and the interview's name the card's
        read = route_call(routes.api_new_project, dict(row, op="read", speakers=speakers))
        if read.get("said"):
            raise cli.Refused(f"{path.name}: {read['said']}", i18n.t("cli.said.nothing_was_written"))
        audio = {}
        if str(item.get("audio") or "").strip():
            recording = Path(str(item["audio"])).expanduser()
            audio = {"audio": str(recording if recording.is_absolute() else (Path(base) / recording).resolve()),
                     "offset": item.get("offset")}
        rows.append(dict(row, speakers=read["speaker_roles"], pseudonym=item.get("pseudonym") or "",
                         interview=item.get("interview") or read["interview"],
                         number=item.get("number"), timepoint=item.get("timepoint"), **audio))
    return rows


def cmd_project_add_transcripts(p: Project, args) -> tuple:
    """Transcripts added to the project, as Add transcripts on the project's page adds them
    (`routes.api_add_transcripts`, op add): a file under a new pseudonym a new participant at the next free
    number, one under a pseudonym there a further interview of that participant, every row checked before
    anything is written, and a failure putting back all it changed."""
    marks = turn_marks(args)
    files = add_entries(p, cli.read_spec(args.source))
    done = route_call(routes.api_add_transcripts,
                      dict({"op": "add", "root": routes.project_id(p.root), "files": files,
                            "skip": getattr(args, "skip", None)}, **marks))
    answer = {k: v for k, v in done.items() if k != "project"}
    answer["project_name"] = done["project"]["name"]
    said = names_lines(done)
    if args.dry_run:
        lines = [i18n.t("cli.project_add_transcripts.dry_run_nothing_was_written_it", participants=i18n.t("cli.n.participant", n=len(done['cases'])), name=done['project']['name'], participants2=i18n.t("cli.n.participant", n=len(done['joined'])))]
        for c in done["plan"]:
            for i in c["interviews"]:
                roles = ", ".join(f"{s['name']} {s['role']}" for s in i["speakers"])
                lines.append(i18n.t("cli.project_add_transcripts.from", label=c['label'], v_=i18n.t("cli.project_add_transcripts.there_already") if c['joins'] else '', interview=i['interview'], file=i['file'], passages=i18n.t("cli.n.passage", n=i['passages']))
                             + (i18n.t("cli.project_add_transcripts.at_timepoint", timepoint=i['timepoint']) if i["timepoint"] != 1 else "") + i18n.t("cli.project_add_transcripts.speakers", roles=roles))
                if i.get("sheet"):
                    lines.append("  " + i18n.t("cli.import.sheet_read", sheet=i["sheet"]))
                lines += ["  " + line for line in routes.quote_lines(i.get("quotes"))]
        return answer, lines + said
    lines = [i18n.t("cli.project_add_transcripts.added_to", list=', '.join(done['cases']) or i18n.t("cli.project_add_transcripts.no_new_participant"), name=done['project']['name'])
             + (i18n.t("cli.project_add_transcripts.and_further_interviews_to", list=', '.join(done['joined'])) if done["joined"] else "") + "."]
    lines.append(i18n.t("cli.project_add_transcripts.each_workbook_made_names_who_made"))
    return answer, lines + said


def names_lines(done: dict) -> list[str]:
    """What an answer says of the project's list of names, counts only, the line and one for each entry found
    (namesrule, 8 November 2026): none for a project with no list."""
    held = done.get("names")
    if not held:
        return []
    return [i18n.t("names.line_names", said=held["said"])] + list(held["lines"])


def cmd_names_list(p: Project, args) -> tuple:
    """The project's list of names as an agent is told it (namesrule, 8 November 2026): each entry's number, what it
    is written as, whom it is for and how many spellings it has, never a real name. The list is made in the app."""
    done = route_call(routes.api_names, {"op": "list", "root": routes.project_id(p.root),
                                         "tool": themes_ai.one_line(getattr(args, "tool", None)) or cli.TOOL})
    lines = [i18n.t("names.line_listed", n=done["count"])] if done["entries"] else [i18n.t("names.no_list")]
    for e in done["entries"]:
        lines.append(i18n.t("names.line_entry_listed", entry=e["entry"], to=e["to"],
                            spellings=i18n.t("names.spelled", n=e["spellings"]),
                            where=i18n.t("names.in_participant", who=e["for"]) if e["for"] else "",
                            case=i18n.t("names.match_case") if e["case"] else ""))
    return done, lines


def cmd_names_check(p: Project, args) -> tuple:
    """The transcripts already in the project searched for the list's names, notes, statements and quotes too,
    counts only, nothing written."""
    done = route_call(routes.api_names, {"op": "check", "root": routes.project_id(p.root),
                                         "tool": themes_ai.one_line(getattr(args, "tool", None)) or cli.TOOL})
    return done, names_lines(done) or [i18n.t("names.no_list")]


def cmd_names_replace(p: Project, args) -> tuple:
    """The list's names replaced in the transcripts already in, as Review and replace does in the app (namesui, 8
    November 2026): each workbook changed kept first in its participant's _Archive, the boards and the GETs
    following, a find left as written by --skip. Counts only, never a name."""
    done = route_call(routes.api_names, dict({"op": "replace", "root": routes.project_id(p.root),
                                              "skip": getattr(args, "skip", None)}, **turn_marks(args)))
    held = done["names"]
    who = i18n.t("cli.n.participant", n=done["participants"])
    first = (i18n.t("names.dry_replace", replaced=held["replaced"], participants=who) if done["dry_run"]
             else i18n.t("names.replaced_said", replaced=held["replaced"], participants=who))
    return done, [first] + names_lines(done)


def cmd_names_remove(p: Project, args) -> tuple:
    """Entries taken off the list by their numbers. Removing shows nothing of the list, so an agent may, with his
    request."""
    done = route_call(routes.api_names, dict({"op": "remove", "root": routes.project_id(p.root),
                                              "entries": list(args.numbers)}, **turn_marks(args)))
    said = i18n.t("names.dry_removed", n=done["removed"]) if done["dry_run"] else i18n.t("names.removed", n=done["removed"])
    return done, [said]


# ------------------------------------------------------------------ import
# (20 October, from the fresh agent's trial: an agent asked to bring in a transcript had no way but
# around the API.) A transcript file is made into its raw source as the import card's Make makes it,
# and a raw source into the case's workbook as the create card makes it, by the server's own code
# (`routes.import_read`, `routes.import_make`, `workbook.create_from_source`), never over a file there.

ROLE_WORDS = {"speaker": "name", "time": "ts", "transcript": "text", "exploratory notes": "en", "notes": "en",
              "experiential statements": "es", "statements": "es", "quote": "kq", "quotes": "kq",
              "key quotes": "kq", "leave out": "", "": ""}


def import_path(p: Project, given) -> Path:
    """The file an import names, by its path from the project's folder or in full, refused unless it
    sits in a case's folder or that folder's own Source, under the project's folder."""
    raw = Path(str(given or "").strip()).expanduser()
    root = p.root.resolve()
    path = (raw if raw.is_absolute() else root / raw).resolve()
    try:
        parts = path.relative_to(root).parts
    except ValueError:
        raise cli.Refused(_w("OUTSIDE")) from None
    inside = len(parts) == 2 or (len(parts) == 3 and parts[1] == "Source")
    if not inside or parts[0] in routes.SKIP_DIRS or path.name.startswith(("~$", ".")):
        raise cli.Refused(_w("NOT_IN_CASE"))
    if not path.is_file():
        raise cli.Refused(i18n.t("cli.said.there_is_no_there", name=path.name))
    return path


def import_project(projects: list[Project], given) -> Project:
    """The project an import's file belongs to, across every project it reads: the one whose folder
    holds it, or the one project there is for a path from a project's folder. A file in a project
    agents may not read is refused as that project is."""
    raw = Path(str(given or "").strip()).expanduser()
    if not raw.is_absolute():
        if len(projects) == 1:
            return projects[0]
        names = " or ".join(p.info["name"] for p in projects)
        raise cli.Refused(i18n.t("cli.said.this_reads_one_project", names=names, name_one=_w("NAME_ONE")))
    path = raw.resolve()
    for p in projects:
        try:
            path.relative_to(p.root.resolve())
            return p
        except ValueError:
            continue
    for root in srv.project_roots():
        try:
            path.relative_to(Path(root).resolve())
        except ValueError:
            continue
        if not routes.read_project(root)["agents"]["allowed"]:
            raise cli.Refused(_w("PRIVATE"))
    raise cli.Refused(_w("OUTSIDE"))


def import_roles(value) -> list[str] | None:
    """The role of each column as a call gives them, a list or one line with commas, in the card's
    words, Speaker, Time, Transcript, Exploratory notes, Experiential statements, Quote or Leave out, or
    the card's own keys, as `convert.choose` takes them. None when none were given."""
    if value is None:
        return None
    items = value.split(",") if isinstance(value, str) else list(value)
    out, bad = [], []
    for item in items:
        word = " ".join(str(item if item is not None else "").split()).lower()
        role = ROLE_WORDS.get(word, word if word in convert_mod.ROLES else None)
        if role is None:
            bad.append(str(item))
        else:
            out.append(role)
    if bad:
        raise cli.Refused(f"{', '.join(bad)} {_w('NOT_A_ROLE')}")
    return out


# a time format by its key, by the example the card names it by, or by the letters of before
TIME_WORDS = {"hh:mm:ss": "hms", "h:mm:ss": "hms", "hms": "hms", "mm:ss": "ms", "m:ss": "ms", "ms": "ms",
              "hh:mm:ss.s": "fraction", "fraction": "fraction",
              "seconds": "seconds", "hh:mm:ss:ff": "frames", "frames": "frames", "": "", "as found": "", "found": "",
              **{name.lower(): key for key, name in convert_mod.TIME_FORMATS.items()}}


def import_speakers(value, names: list[str]) -> dict | None:
    """Each speaker's role as a call gives them, a `{name: role}` or one line, Sam=Interviewer,
    Hazel=Participant, in the card's words, every name one the file's speakers carry. None when none
    were given."""
    if value is None:
        return None
    if isinstance(value, str):
        pairs = [part.split("=", 1) for part in value.split(",") if part.strip()]
        if any(len(pair) != 2 for pair in pairs):
            raise cli.Refused(i18n.t("cli.said.give_each_speakers_role_as_name"))
        value = {" ".join(k.split()): v for k, v in pairs}
    if not isinstance(value, dict):
        raise cli.Refused(i18n.t("cli.said.give_each_speakers_role_as_name"))
    out = {}
    for name, role in value.items():
        name = " ".join(str(name).split())
        match = [n for n in names if n.lower() == name.lower()]
        if not match:
            raise cli.Refused(i18n.t("cli.import_speakers.no_speaker_called_the_speakers", name=name, list=', '.join(names) or 'none'))
        word = convert_mod.role_word(role)
        if word is None:
            raise cli.Refused(f"{role} {_w('NOT_A_SPEAKER_ROLE')}")
        out[match[0]] = word
    return out


def import_timing(fmt, fps) -> dict | None:
    """How a Time column is read as a call gives it, its format in the card's words and the frame rate."""
    if fmt is None and fps is None:
        return None
    word = TIME_WORDS.get(" ".join(str(fmt or "").split()).lower())
    if word is None:
        raise cli.Refused(f"{fmt} {_w('NOT_A_TIME_FORMAT')}")
    if fps is not None:
        try:
            rate = float(str(fps).replace(",", "."))
        except ValueError:
            rate = 0
        if rate != int(rate) or not 1 <= rate <= 120:
            raise cli.Refused(i18n.t("cli.import_timing.give_the_frame_rate_as_a"))
    return {"format": word, "fps": fps}


def made_by(args, source: Path) -> str:
    """Who made a workbook in a conversation, for which request and from which file, as a board's note
    says how it was made, kept in the workbook's own description."""
    return (i18n.t("cli.made_by.made_by_in_a_conversation_on", one_line=themes_ai.one_line(args.tool) or cli.TOOL, when=cli.when_said(now_iso()), one_line2=themes_ai.one_line(args.note), name=source.name))


def landed(turns: list, notes, chosen: str, setting: str, roles: dict | None = None, form: str | None = None) -> list[dict]:
    """The first passages as they will land, the interviewer's under Settings' name, with the notes
    and statements a table brings beside each, and another speaker's marked, each time as `form` says, the
    project's timecodes."""
    notes = list(notes or [])
    held = lambda i, role: routes.preview_words(notes[i].get(role) or "") if i < len(notes) and isinstance(notes[i], dict) else ""
    out = []
    for i, (name, seconds, words) in enumerate(convert_mod.as_interviewer(turns, chosen, setting)[:convert_mod.PREVIEW]):
        one = {"speaker": name, "time": wb_mod.timecode(seconds, form), "words": routes.preview_words(words)}
        if roles and roles.get(turns[i][0]) == "other":
            one["other_speaker"] = True
        for key, role in (("notes", "en"), ("statements", "es")):
            if held(i, role):
                one[key] = held(i, role)
        out.append(one)
    return out


def passage_line(t: dict) -> str:
    head = " ".join(x for x in (t["speaker"], t["time"]) if x)
    extra = "".join(f" [{k}: {' '.join(t[k].split())}]" for k in ("notes", "statements") if t.get(k))
    return f"  {head}: {t['words']}{extra}"


def cmd_import(p: Project, args) -> tuple:
    if not themes_ai.one_line(args.note) and not args.dry_run:
        raise cli.Refused(_w("NO_IMPORT_REQUEST"))
    path = import_path(p, args.file)
    root = p.root.resolve()
    shown = lambda q: Path(q).resolve().relative_to(root).as_posix()
    case = routes.case_label(path)
    roles = import_roles(getattr(args, "columns", None))
    asked = getattr(args, "interviewer", None)
    name = themes_ai.one_line(getattr(args, "name", None))
    sheet = " ".join(str(getattr(args, "sheet", None) or "").split()) or None
    if sheet and path.suffix.lower() != ".xlsx":
        raise cli.Refused(i18n.t("cli.import.sheet_for_excel"))
    book = routes.read_sheets(path) if path.suffix.lower() == ".xlsx" else None
    if book and book[0] == "annotated":
        raise cli.Refused(i18n.t("cli.import.is_a_participants_workbook_already_so", name=path.name))
    if book:
        return import_raw(p, args, path, book[1], case, shown, roles, asked, name)
    if name:
        raise cli.Refused(_w("NAME_FOR_RAW"))
    if path.suffix.lower() not in convert_mod.FORMATS:
        raise cli.Refused(i18n.t("cli.import.that_file_is_not_a_transcript"))
    setting = str(srv.config().get("interviewer") or "").strip()
    timing = import_timing(getattr(args, "time_format", None), getattr(args, "frame_rate", None))
    try:
        read, out, said = routes.import_read(path, roles, not args.dry_run, timing, sheet)
    except WorkbookError as exc:
        raise cli.Refused(str(exc)) from None
    if roles is not None and not read.get("headers"):
        raise cli.Refused(_w("NO_COLUMNS"))
    if timing is not None and not (read.get("headers") and (read.get("mapping") or {}).get("ts") is not None):
        raise cli.Refused(i18n.t("cli.import.this_file_has_no_time_column"))
    turns = read["turns"]
    view = routes.turns_view(read, setting, p.info.get("timecodes"))
    names = [s["name"] for s in view["speakers"]]
    given = import_speakers(getattr(args, "speakers", None), names)
    if given is not None and asked is not None:
        raise cli.Refused(_w("SPEAKERS_OR_INTERVIEWER"))
    if asked is not None:
        said_name = " ".join(str(asked).split())
        match = [n for n in names if n.lower() == said_name.lower()]
        if said_name and not match:
            raise cli.Refused(i18n.t("cli.import.no_speaker_called_the_speakers", said_name=said_name, list=', '.join(names) or 'none'))
    asks = {"speakers": given, "interviewer": (match[0] if match else "") if asked is not None and given is None else None,
            "audio": str(getattr(args, "audio", None) or "").strip(), "offset": getattr(args, "offset", None),
            "timepoint": getattr(args, "timepoint", None)}
    if asks["audio"]:
        audio = Path(asks["audio"]).expanduser()
        asks["audio"] = str(audio if audio.is_absolute() else (p.root / audio).resolve())
    try:
        plan = routes.import_plan(path, read, asks, setting)
    except WorkbookError as exc:
        raise cli.Refused(str(exc), i18n.t("cli.said.nothing_was_written")) from None
    said = said or plan["said"]
    roles_now = plan["roles"]
    chosen = convert_mod.the_interviewer(roles_now)
    guessed = given is None and asked is None
    goes_as = view["as"].get(chosen) if chosen else None
    columns = [{"heading": h, "role": convert_mod.ROLE_NAMES.get(r, "Leave out") if r else i18n.t("cli.import.leave_out")}
               for h, r in zip(read.get("headers") or [], read.get("roles") or [])]
    first = landed(turns, read.get("notes"), chosen, setting, roles_now, p.info.get("timecodes"))
    suggested = wb_mod.suggested_output(out)
    timed = bool(read.get("headers")) and (read.get("mapping") or {}).get("ts") is not None
    chosen_format = (read.get("timing") or {}).get("format") or ""
    answer = {"case": case, "file": shown(path), "kind": read["kind"], "makes": i18n.t("cli.said.raw_source"),
              "columns": columns or None, "count": len(turns),
              "speakers": [dict(s, role=convert_mod.SPEAKER_ROLES[roles_now.get(s["name"], "participant")]) for s in view["speakers"]],
              "speakers_guessed": guessed,
              "interviewer": chosen or None, "interviewer_guessed": guessed,
              "interviewer_written_as": goes_as, "cases": [case],
              "time_found": convert_mod.TIME_NAMES.get(read.get("time_found") or "") if timed else None,
              "time_format": convert_mod.TIME_FORMATS.get(chosen_format) if timed else None,
              "frame_rate": (read.get("timing") or {}).get("fps") if timed else None,
              "times_unread": list(read.get("bad_times") or []) if timed else [],
              "audio": shown(plan["audio"]) if plan["audio"] and srv.inside(plan["audio"], p.root) else (str(plan["audio"]) if plan["audio"] else None),
              "audio_offset": plan["offset"],
              # the name the copy takes, the participant's pseudonym and timepoint, never the source's (ayabuild12)
              "audio_name": plan.get("audio_name"),
              "audio_writes": (shown(wb_mod.case_folder(path) / "Source" / (plan.get("sheet") or convert_mod.SHEET) / "Source"
                                     / plan["audio_name"]) if plan["audio"] else None),
              "sheet_read": read.get("sheet") if read.get("kind") == "xlsx" else None,
              "sheets": list(read.get("sheets") or []) or None,
              "quotes": routes.quote_counts(read),
              "passages": first,
              "left_out": list(read.get("left") or []), "brings": view["brings"] or None,
              "writes": shown(out), "then": shown(suggested), "said": said}
    tps = p.info["timepoints"]
    if routes.longitudinal(tps):
        answer["timepoint"] = tps[plan["timepoint"] - 1]["label"]
        if plan.get("joins"):
            answer.update(joins=shown(plan["joins"]), sheet=plan["sheet"], then=None)
    lines = []
    if answer["sheet_read"]:
        lines.append(i18n.t("cli.import.sheet_read", sheet=answer["sheet_read"]))
    if columns:
        lines.append(i18n.t("cli.import.columns") + ", ".join(f"{c['heading']} as {c['role']}" for c in columns) + ".")
    lines += routes.quote_lines(answer["quotes"])
    if timed:
        found_name = answer["time_found"] or i18n.t("cli.said.no_time")
        lines.append(i18n.t("cli.import.times_found_as", found_name=found_name) + (i18n.t("cli.import.read_as", time_format=answer['time_format']) if chosen_format else "")
                     + (i18n.t("cli.import.at_frames_a_second", frame_rate=answer['frame_rate']) if "frames" in (chosen_format, read.get("time_found")) else "") + ".")
        for bad in answer["times_unread"]:
            lines.append(i18n.t("cli.import.the_time_on_passage_cannot_be", time=bad['time'], passage=bad['passage']))
    lines.append(i18n.t("cli.import.from", passages=i18n.t("cli.n.passage", n=len(turns)), speakers=i18n.t("cli.n.speaker", n=len(names)))
                 + ", ".join(f"{s['name']} ({s['turns']}, {s['role']})" for s in answer["speakers"]) + ".")
    who = (i18n.t("cli.import.the_interviewer", chosen=chosen, v_='guessed' if guessed else i18n.t("cli.import.as_asked")) if chosen
           else i18n.t("cli.import.no_interviewer_is_chosen"))
    if goes_as:
        who += i18n.t("cli.import.his_passages_go_under_the_name", goes_as=goes_as)
    lines.append(who)
    lines.append(i18n.t("cli.import.it_makes_one_participant_as_one", case=case))
    if answer.get("timepoint"):
        lines.append(f"At {answer['timepoint']}" + (i18n.t("cli.import.as_the_sheet_added_at_the", sheet=answer['sheet'], name=Path(answer['joins']).name) if answer.get("joins") else "."))
    if plan["audio"]:
        lines.append(i18n.t("cli.import.the_recording_is_copied_into_the", name=plan['audio'].name, offset=audio_mod.offset_said(plan['offset']))
                     + " " + i18n.t("cli.import.recording_named", name=plan["audio_name"]))
    if first:
        lines.append(i18n.t("cli.import.the_first_passages_as_they_will", n_first=len(first)))
        lines += [passage_line(t) for t in first]
    lines += list(read.get("left") or [])
    if args.dry_run:
        if said:
            text = i18n.t("cli.import.dry_run_nothing_was_written_cannot", name=path.name, said=said)
            return dict(answer, dry_run=True), [text] + lines
        text = (i18n.t("cli.import.dry_run_nothing_was_written_it", shown=shown(out), name=path.name, case=case) + (i18n.t("cli.import.it_would_add_its_sheet_to", name=Path(answer['joins']).name)
                                   if answer.get("joins") else i18n.t("cli.import.importing_that_next_makes_the_participants", name=suggested.name)))
        return dict(answer, dry_run=True), [text] + lines
    if said:
        raise cli.Refused(said, i18n.t("cli.said.nothing_was_written"))
    try:
        routes.import_make(path, read, out, plan, setting, made_by(args, path))
    except WorkbookError as exc:
        raise cli.Refused(str(exc), i18n.t("cli.said.nothing_was_written")) from None
    if answer.get("joins"):
        text = (i18n.t("cli.import.wrote_the_raw_source_from_for_2", shown=shown(out), name=path.name, case=case, sheet=answer['sheet'], name2=Path(answer['joins']).name, timepoint=answer['timepoint']))
        return dict(answer, written=shown(out)), [text] + lines
    text = (i18n.t("cli.import.wrote_the_raw_source_from_for", shown=shown(out), name=path.name, case=case, name2=suggested.name))
    return dict(answer, written=shown(out)), [text] + lines


def cmd_offset(p: Project, args) -> tuple:
    """A sheet's recording given a new offset in seconds, which playback adds to every time code, as
    the Offset card under the player sets it (see `routes.set_audio_offset`)."""
    b = p.case(args.case)
    book = Path(b["workbook"])
    try:
        done = routes.set_audio_offset(book, args.sheet, args.seconds, dry_run=args.dry_run)
    except WorkbookError as exc:
        raise cli.Refused(str(exc), i18n.t("cli.said.nothing_was_written")) from None
    root = p.root.resolve()
    answer = dict(done, case=b["case"], file=srv.abs_path(done["file"]).resolve().relative_to(root).as_posix())
    move = (f"{audio_mod.offset_said(done['was'])} to {audio_mod.offset_said(done['offset'])}" if done["changed"]
            else i18n.t("cli.offset.as_it_is_already", offset=audio_mod.offset_said(done['offset'])))
    if args.dry_run:
        return dict(answer, dry_run=True), [i18n.t("cli.offset.dry_run_nothing_was_written_the", recording=done['recording'], sheet=args.sheet, case=b['case'], move=move)]
    return answer, [i18n.t("cli.offset.the_offset_of_on_of_went", recording=done['recording'], sheet=args.sheet, case=b['case'], move=move)]


def cmd_audio_attach(p: Project, args) -> tuple:
    """A recording copied onto a participant's interview already in, as an import's --audio copies one as a
    transcript comes in (`routes.attach_audio`): named by the participant's pseudonym and the timepoint, never the
    file's own name, set as that interview's recording, kept in History. The file is only read. With --dry-run the
    name it will have, and nothing written."""
    b = p.case(args.case)
    marks = turn_marks(args)
    file = Path(str(args.file)).expanduser()
    file = file if file.is_absolute() else (p.root / file).resolve()
    done = route_call(routes.api_audio_attach, dict({
        "path": str(b["workbook"]), "file": str(file), "timepoint": getattr(args, "timepoint", None),
        "interview": getattr(args, "interview", None), "replace": bool(getattr(args, "replace", False)),
        "offset": getattr(args, "offset", None)}, **marks))
    root = p.root.resolve()
    shown = lambda value: srv.abs_path(value).resolve().relative_to(root).as_posix()
    answer = dict(done, case=b["case"], writes=shown(done["writes"]),
                  **({"kept": shown(done["kept"])} if done.get("kept") else {}))
    if args.dry_run:
        text = i18n.t("cli.audio_attach.dry_run", sheet=done["sheet"], case=b["case"], name=done["recording"],
                      writes=answer["writes"])
        if done.get("replaces"):
            text += " " + i18n.t("cli.audio_attach.replaces", old=done["replaces"])
        return answer, [text]
    lines = [i18n.t("cli.audio_attach.done", writes=answer["writes"], name=done["recording"], sheet=done["sheet"],
                    case=b["case"])]
    if done.get("kept"):
        lines.append(i18n.t("cli.audio_attach.kept", old=done["replaces"], kept=answer["kept"]))
    return answer, lines


# ------------------------------------------------------------- quote heading
# (23 October, Adam's ruling.) A workbook made before 22 October heads its quotes column Key quotes, and
# this renames that heading Quote on every annotation sheet of one participant's workbook, or of every
# participant's with --all, each workbook its own write, by the server's own code
# (`routes.rename_quote_heading`). Nothing but the heading changes.



def heading_lines(case: str, sheets: list[dict], dry: bool) -> list[str]:
    """What the op does, or would do, to each sheet of one participant's workbook, a line a sheet."""
    lines = []
    for s in sheets:
        where = f"{s['sheet']} of {case}"
        if s["change"] == "rename":
            verb = i18n.t("cli.heading_lines.would_rename") if dry else "renamed"
            lines.append(i18n.t("cli.heading_lines.the_quotes_columns_heading_1_from", where=where, verb=verb, column=s['column'], was=s['was'], now=s['now']))
        elif s["change"] == "already":
            lines.append(i18n.t("cli.heading_lines.headed_already_left_as_it_is", where=where, now=s['now']))
        elif s["change"] == "other":
            lines.append(i18n.t("cli.heading_lines.its_quotes_column_is_headed_left", where=where, was=s['was']))
        else:
            lines.append(i18n.t("cli.heading_lines.no_quotes_column_left_as_it", where=where))
    if not sheets:
        lines.append(i18n.t("cli.heading_lines.no_annotation_sheet_left_as_it", case=case))
    return lines


def cmd_quote_heading(p: Project, args) -> tuple:
    """The quotes column's heading renamed from Key quotes to Quote on every annotation sheet of a
    participant's workbook, or with --all of every participant's, each workbook its own write. A dry run
    says per sheet what it would change and writes nothing. A workbook open in Excel or under another
    write is refused and left as it is, and with --all the others go ahead."""
    every = bool(getattr(args, "all", False))
    if every == bool(getattr(args, "case", None)):
        raise cli.Refused(_w("HEADING_CASE_OR_ALL") if every else _w("HEADING_NEITHER"))
    request = themes_ai.one_line(args.note)
    if not args.dry_run and not request:
        raise cli.Refused(_w("NO_HEADING_REQUEST"))
    tool = themes_ai.one_line(args.tool) or cli.TOOL
    books = list(p.books) if every else [p.case(args.case)]
    root = p.root.resolve()
    answers, lines, refused = [], [], []
    for b in books:
        book = Path(b["workbook"])
        try:
            done = routes.rename_quote_heading(book, dry_run=args.dry_run, tool=tool, request=request)
        except WorkbookError as exc:
            if not every:
                raise cli.Refused(str(exc), i18n.t("cli.said.nothing_was_written")) from None
            refused.append({"case": b["case"], "reason": str(exc)})
            lines.append(i18n.t("cli.said.nothing_was_written_to_it", case=b['case'], exc=exc))
            continue
        try:
            file = book.resolve().relative_to(root).as_posix()
        except ValueError:
            file = book.name
        answers.append(dict(done, case=b["case"], file=file))
        lines += heading_lines(b["case"], done["sheets"], args.dry_run)
        if done["changed"]:
            lines.append(i18n.t("cli.quote_heading.a_copy_of_the_workbook_as", case=b['case'], backup=done['backup']))
    renamed = sum(1 for a in answers for s in a["sheets"] if s["change"] == "rename")
    if args.dry_run:
        head = (i18n.t("cli.quote_heading.dry_run_nothing_was_written_it", headings=i18n.t("cli.n.heading", n=renamed), workbooks=i18n.t("cli.n.workbook", n=len([a for a in answers if any(s['change'] == 'rename' for s in a['sheets'])]))))
    else:
        head = (i18n.t("cli.quote_heading.renamed_in", headings=i18n.t("cli.n.heading", n=renamed), workbooks=i18n.t("cli.n.workbook", n=len([a for a in answers if a['changed']])))
                if renamed else i18n.t("cli.quote_heading.nothing_to_rename_every_quotes_column"))
    answer = {"workbooks": answers, "refused": refused, "renamed": renamed, "said": head}
    if args.dry_run:
        answer["dry_run"] = True
    return answer, [head] + lines


# ------------------------------------------------------ transcript replace
# (24 October 2026, the PhD session's gap: no op changed a passage's words.) The app's Find and replace on
# the command line, by the route's own code (`routes.replace_in_case`, `routes.undo_in_case`): the words
# found change in the transcript, the statements, the quotes and the notes alike, under the case's lock,
# recorded in the progress file under one batch id, every board and every copy following, the GETs', and in a
# project of timepoints the LPETs' and the LGETs' (histreplace, 30 October 2026), and undone by
# that id. With --pairs a file of finds and their replacements drives it, so a list of real names reaches
# no command line, and with it or --mask no line, answer, record or refusal carries the words found.



def pairs_from(given) -> list[list[str]]:
    """The pairs a --pairs file holds, or a list of them an agent handed over through MCP: a line a
    pair, the words to find, a tab and their replacement, blank lines and lines starting with # left out,
    or JSON, a list of [find, replace] or an object of find to replace. A line with no tab is refused by
    its number alone, and nothing of the file's words is ever said."""
    if isinstance(given, list):
        items = given
    elif isinstance(given, dict):
        items = list(given.items())
    else:
        try:
            raw = Path(str(given)).expanduser().read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            raise cli.Refused(_w("PAIRS_UNREAD")) from None
        stripped = raw.lstrip("﻿").strip()
        if stripped[:1] in ("[", "{"):
            try:
                data = json.loads(stripped)
            except ValueError:
                raise cli.Refused(_w("PAIRS_SHAPE")) from None
            items = list(data.items()) if isinstance(data, dict) else data
        else:
            items = []
            for n, line in enumerate(raw.lstrip("﻿").splitlines(), start=1):
                if not line.strip() or line.lstrip().startswith("#"):
                    continue
                if "\t" not in line:
                    raise cli.Refused(_w("PAIR_LINE").format(n=n))
                find, _, put = line.partition("\t")
                items.append([find, put])
    out = []
    for item in items if isinstance(items, list) else []:
        if not (isinstance(item, (list, tuple)) and len(item) == 2 and all(isinstance(x, str) for x in item)):
            raise cli.Refused(_w("PAIRS_SHAPE"))
        out.append([item[0], item[1]])
    if not out:
        raise cli.Refused(_w("NO_PAIRS"))
    return out


def place_line(case: str, place: dict, dry: bool) -> str:
    """One column of one row a replace changes, or would, its words never said."""
    column = wb_mod.ROLE_NAMES.get(place["column"], place["column"])
    at = f" ({place['time']})" if place.get("time") else ""
    verb = i18n.t("cli.place_line.would_replace") if dry else "replaced"
    return (i18n.t("cli.place_line.row", case=case, sheet=place['sheet'], row=place['row'], at=at, column=column, verb=verb, occurrences=i18n.t("cli.n.occurrence", n=int(place['count']))))


def followed_lines(case: str, done: dict) -> list[str]:
    """What took the new words beside the workbook: each board, each copy of the participant, the GETs', the
    LPETs' and the LGETs', and anything that could not be read."""
    lines = []
    for b in done.get("boards") or []:
        lines.append(i18n.t("cli.followed_lines.took_the_new_words_on", case=case, name=b['name'], cards=i18n.t("cli.n.card", n=len(b['keys']))))
    for kind, name in routes.COPY_NAMES.items():
        if done.get(kind):
            lines.append(i18n.t("cli.followed_lines.the_copy_took_the_new_words", case=case, name=name, statements=i18n.t("cli.n.statement", n=len(done[kind]))))
    return lines + [f"{case}: {x}" for x in done.get("failed") or []]


def followed_counts(done: dict) -> dict:
    """The statements each copy of the participant took the new words on, by its kind, as an answer gives them."""
    return {kind: len(done.get(kind) or []) for kind in routes.COPY_NAMES}


def cmd_transcript_replace(p: Project, args) -> tuple:
    """Find and replace across a participant's workbook, or with --all every participant's, as the app's
    Find and replace does, the words changing in the transcript, the statements, the quotes and the
    notes alike (`routes.replace_in_case`). Every workbook's write takes one batch id, which
    transcript replace-undo undoes. A dry run counts and lists each place, participant, sheet, row,
    timecode and column, and writes nothing. A workbook open in Excel or under another write is refused
    and left as it is, and with --all the others go ahead."""
    every = bool(getattr(args, "all", False))
    if every == bool(getattr(args, "case", None)):
        raise cli.Refused(_w("REPLACE_CASE_OR_ALL"))
    given_pairs = getattr(args, "pairs", None)
    if (given_pairs is not None) == (args.find is not None):
        raise cli.Refused(_w("REPLACE_FIND_OR_PAIRS"))
    mask = bool(getattr(args, "mask", False)) or given_pairs is not None
    pairs = pairs_from(given_pairs) if given_pairs is not None else None
    request = themes_ai.one_line(args.note)
    if not args.dry_run and not request:
        raise cli.Refused(_w("NO_REPLACE_REQUEST"))
    tool = themes_ai.one_line(args.tool) or cli.TOOL
    find, put = (None, None) if pairs is not None else (args.find, args.put or "")
    try:
        wb_mod.replace_pairs(find, put, pairs)
    except WorkbookError as exc:
        raise cli.Refused(str(exc)) from None
    books = list(p.books) if every else [p.case(args.case)]
    batch = rounds_mod.new_batch()
    answers, lines, refused = [], [], []
    for b in books:
        book = Path(b["workbook"])
        try:
            done = routes.replace_in_case(book, find, put, pairs=pairs, word=args.word, case=args.match_case,
                                          dry_run=args.dry_run, mask=mask, tool=tool, request=request,
                                          batch=batch)
        except WorkbookError as exc:
            # a refusal is one of the replace's own lines, none of which says the words
            if not every:
                raise cli.Refused(str(exc), i18n.t("cli.said.nothing_was_written")) from None
            refused.append({"case": b["case"], "reason": str(exc)})
            lines.append(i18n.t("cli.said.nothing_was_written_to_it", case=b['case'], exc=exc))
            continue
        if not done["replaced"]:
            continue
        answers.append({"case": b["case"], "replaced": done["replaced"], "counts": done["counts"],
                        "places": done["places"],
                        "boards": [{"board": x["board"], "name": x["name"], "cards": len(x["keys"])}
                                   for x in done.get("boards") or []],
                        **followed_counts(done), "failed": done.get("failed") or []})
        lines += [place_line(b["case"], x, args.dry_run) for x in done["places"]]
        lines += followed_lines(b["case"], done)
    total = sum(a["replaced"] for a in answers)
    rows = len({(a["case"], x["sheet"], x["row"]) for a in answers for x in a["places"]})
    what = "" if mask else (i18n.t("cli.transcript_replace.with", find=find, put=put) if pairs is None else "")
    where = f"{i18n.t('cli.n.row', n=rows)} of {i18n.t('cli.n.participant', n=len(answers))}"
    if args.dry_run:
        head = (i18n.t("cli.transcript_replace.dry_run_nothing_was_written_it", what=what, occurrences=i18n.t("cli.n.occurrence", n=total), where=where)
                if total else i18n.t("cli.transcript_replace.dry_run_nothing_was_written_nothing"))
    elif total:
        head = (i18n.t("cli.transcript_replace.replaced_in_under_batch_idiograph_transcript", what=what, occurrences=i18n.t("cli.n.occurrence", n=total), where=where, batch=batch))
    else:
        head = i18n.t("cli.transcript_replace.nothing_to_replace_the_words_are")
    answer = {"batch": batch if total and not args.dry_run else None, "replaced": total, "participants": answers,
              "refused": refused, "said": head}
    if not mask and pairs is None:
        answer.update(find=find, put=put)
    if args.dry_run:
        answer["dry_run"] = True
    return answer, [head] + lines


def cmd_transcript_replace_undo(p: Project, args) -> tuple:
    """A replace undone by its batch id, or with --redo applied again, in every participant's workbook
    that holds it (`routes.undo_in_case`), each refused whole when a passage reads otherwise now. A dry
    run says what it would put back and writes nothing. Its lines never say the words."""
    batch = str(args.batch or "").strip()
    request = themes_ai.one_line(args.note)
    if not args.dry_run and not request:
        raise cli.Refused(_w("NO_REPLACE_REQUEST"))
    tool = themes_ai.one_line(args.tool) or cli.TOOL
    books = [p.case(args.case)] if getattr(args, "case", None) else list(p.books)
    held = [b for b in books if rounds_mod.replace_records(rounds_mod.load_progress(Path(b["workbook"])), batch)]
    if not held:
        raise cli.Refused(_w("NO_BATCH_HERE"))
    answers, lines, refused = [], [], []
    for b in held:
        try:
            done = routes.undo_in_case(Path(b["workbook"]), batch, redo=args.redo, dry_run=args.dry_run,
                                       tool=tool, request=request)
        except WorkbookError as exc:
            refused.append({"case": b["case"], "reason": str(exc)})
            lines.append(i18n.t("cli.said.nothing_was_written_to_it", case=b['case'], exc=exc))
            continue
        answers.append({"case": b["case"], "replaced": done["replaced"], "counts": done["counts"],
                        "places": done["places"],
                        "boards": [{"board": x["board"], "name": x["name"], "cards": len(x["keys"])}
                                   for x in done.get("boards") or []],
                        **followed_counts(done), "failed": done.get("failed") or []})
        verb = (i18n.t("cli.transcript_replace_undo.would_apply_again") if args.redo else i18n.t("cli.transcript_replace_undo.would_put_back")) if args.dry_run else (
            i18n.t("cli.transcript_replace_undo.applied_again") if args.redo else i18n.t("cli.transcript_replace_undo.put_back"))
        lines.append(i18n.t("cli.transcript_replace_undo.in", case=b['case'], verb=verb, occurrences=i18n.t("cli.n.occurrence", n=done['replaced']), rows=i18n.t("cli.n.row", n=len({(x['sheet'], x['row']) for x in done['places']}))))
        lines += followed_lines(b["case"], done)
    total = sum(a["replaced"] for a in answers)
    verb = i18n.t("cli.transcript_replace_undo.applied_again") if args.redo else i18n.t("cli.transcript_replace_undo.put_back")
    head = (i18n.t("cli.transcript_replace_undo.dry_run_nothing_was_written_batch", batch=batch, occurrences=i18n.t("cli.n.occurrence", n=total), verb=verb)
            if args.dry_run else i18n.t("cli.transcript_replace_undo.batch", batch=batch, occurrences=i18n.t("cli.n.occurrence", n=total), verb=verb))
    answer = {"batch": batch, "redo": bool(args.redo), "replaced": total, "participants": answers,
              "refused": refused, "said": head}
    if args.dry_run:
        answer["dry_run"] = True
    return answer, [head] + lines


def import_raw(p: Project, args, path: Path, sheets: list[str], case: str, shown, roles, asked, name: str) -> tuple:
    """A raw source made into the case's workbook, as the create card makes it, in the case's folder,
    by the name given or the one the card suggests, never over a file there and never into Source."""
    if roles is not None or asked is not None:
        raise cli.Refused(_w("RAW_TAKES_NONE"))
    folder = wb_mod.case_folder(path)
    if name:
        if Path(name).name != name or name in (".", ".."):
            raise cli.Refused(i18n.t("cli.import_raw.name_is_a_files_name_alone"))
        out = folder / (name if name.lower().endswith(".xlsx") else f"{name}.xlsx")
    else:
        out = wb_mod.suggested_output(path)
    try:
        read = convert_mod.read_file(path)
    except convert_mod.Unreadable:
        read = {"turns": []}
    turns = read["turns"]
    first = landed(turns, None, "", "", form=p.info.get("timecodes"))
    said = i18n.t("cli.import_raw.is_already_there", name=out.name) if out.exists() else None
    tps = p.info["timepoints"]
    try:
        timepoint = routes.timepoint_asked(getattr(args, "timepoint", None), tps)
    except WorkbookError as exc:
        raise cli.Refused(str(exc), i18n.t("cli.said.nothing_was_written")) from None
    answer = {"case": case, "file": shown(path), "kind": i18n.t("cli.said.raw_source"), "makes": "workbook", "sheets": sheets,
              "count": len(turns), "speakers": convert_mod.speakers(turns), "passages": first,
              "writes": shown(out), "said": said}
    if routes.longitudinal(tps):
        answer["timepoint"] = tps[timepoint - 1]["label"]
    lines = [i18n.t("cli.import_raw.is_a_raw_source_its_sheets", name=path.name, list=', '.join(sheets), passages=i18n.t("cli.n.passage", n=len(turns)))]
    if first:
        lines.append(i18n.t("cli.import_raw.the_first_passages", n_first=len(first)))
        lines += [passage_line(t) for t in first]
    if args.dry_run:
        text = (i18n.t("cli.import_raw.dry_run_nothing_was_written_cannot", name=path.name, said=said) if said else
                i18n.t("cli.import_raw.dry_run_nothing_was_written_it", shown=shown(out), name=path.name, case=case))
        return dict(answer, dry_run=True), [text] + lines
    if said:
        raise cli.Refused(said, i18n.t("cli.said.nothing_was_written"))
    try:
        with routes.writing(out):
            wb_mod.create_from_source(path, out, made_by(args, path))
            if timepoint > 1:
                rounds_mod.tag_sheets(out, routes.read_sheets(out)[1], timepoint)
    except WorkbookError as exc:
        raise cli.Refused(str(exc), i18n.t("cli.said.nothing_was_written")) from None
    text = (i18n.t("cli.import_raw.wrote_the_participants_workbook_from_for", shown=shown(out), name=path.name, case=case))
    return dict(answer, written=shown(out)), [text] + lines


# ------------------------------------------------------------------- qdpx
# (21 October) A REFI-QDA project from ATLAS.ti, NVivo or MAXQDA brought in as participants, by the
# server's own function (`routes.qdpx_import`), which the coming import card calls too.



def qdpx_path(p: Project, given) -> Path:
    """The .qdpx a call names, by its path from the project's folder or in full, refused unless it is
    under the project's folder."""
    raw = Path(str(given or "").strip()).expanduser()
    root = p.root.resolve()
    path = (raw if raw.is_absolute() else root / raw).resolve()
    try:
        path.relative_to(root)
    except ValueError:
        raise cli.Refused(_w("OUTSIDE")) from None
    if not path.is_file():
        raise cli.Refused(i18n.t("cli.said.there_is_no_there", name=path.name))
    if path.suffix.lower() != ".qdpx":
        raise cli.Refused(routes.NOT_A_QDPX)
    return path


def qdpx_sources(value) -> list[dict] | None:
    """The sources a call brings in, as the server takes them: a list of records, or one line,
    1=Wren:3:T1, 2=Ash, each a source's number, its pseudonym, and the participant's number, the
    timepoint and the interview's name when given."""
    if value is None or isinstance(value, list):
        return value
    out = []
    for part in str(value).split(","):
        if not part.strip():
            continue
        n, eq, rest = part.partition("=")
        bits = [b.strip() for b in rest.split(":")]
        if not eq or not n.strip() or not bits[0] or len(bits) > 4:
            raise cli.Refused(_w("SOURCES_SHAPE"))
        bits += [""] * (4 - len(bits))
        out.append({"source": n.strip(), "pseudonym": bits[0], "number": bits[1] or None,
                    "timepoint": bits[2] or None, "interview": bits[3] or None})
    return out


def speakers_given(value) -> dict | None:
    """Each speaker's role as a call gives them, a record or one line, Sam=Interviewer, Hazel=Participant,
    each role in the card's words, refused in one line when a pair or a role is not one. None for none."""
    speakers = value
    if isinstance(speakers, str):
        pairs = [part.split("=", 1) for part in speakers.split(",") if part.strip()]
        if any(len(pair) != 2 for pair in pairs):
            raise cli.Refused(i18n.t("cli.said.give_each_speakers_role_as_name"))
        speakers = {" ".join(k.split()): " ".join(v.split()) for k, v in pairs}
    for role in (speakers or {}).values():
        if convert_mod.role_word(role) is None:
            raise cli.Refused(f"{role} {_w('NOT_A_SPEAKER_ROLE')}")
    return speakers


def qdpx_source_line(view: dict) -> str:
    """One source as the dry run lists it."""
    if view.get("left_out"):
        return i18n.t("cli.qdpx_source_line.source", source=view['source'], name=view['name'], left_out=view['left_out'])
    speakers = ", ".join(f"{s['name']} ({s['turns']}, {s['role']})" for s in view["speakers"])
    extra = "".join(x for x in (i18n.t("cli.qdpx_source_line.its_recording", recording=view['recording']) if view.get("recording") else "",
                                i18n.t("cli.qdpx_source_line.coded_by", list=', '.join(view['coders'])) if view.get("coders") else "",
                                f", {i18n.t('cli.n.memo', n=view['memos'])}" if view.get("memos") else ""))
    return i18n.t("cli.qdpx_source_line.source_from", source=view['source'], name=view['name'], kind=view['kind'], passages=i18n.t("cli.n.passage", n=view['count']), speakers=speakers, extra=extra)


def cmd_qdpx(p: Project, args) -> tuple:
    if not themes_ai.one_line(args.note) and not args.dry_run:
        raise cli.Refused(_w("NO_IMPORT_REQUEST"))
    path = qdpx_path(p, args.file)
    shown = lambda q: Path(q).resolve().relative_to(p.root.resolve()).as_posix()
    speakers = speakers_given(getattr(args, "speakers", None))
    body = {"sources": qdpx_sources(getattr(args, "sources", None)), "speakers": speakers,
            "codes": getattr(args, "codes", None), "comments": getattr(args, "comments", None),
            "loose": getattr(args, "loose", None), "memos": getattr(args, "memos", None),
            "recordings": getattr(args, "recordings", None), "pets": getattr(args, "pets", False) is True,
            "user": getattr(args, "user", None), "skip": getattr(args, "skip", None),
            # the package's variables as the participants' demographics unless --no-demographics (demobuild)
            "demographics": not getattr(args, "no_demographics", False)}
    try:
        answer = routes.qdpx_import(p.root, path, body, make=not args.dry_run, made=made_by(args, path))
    except WorkbookError as exc:
        raise cli.Refused(str(exc), *([] if args.dry_run else [i18n.t("cli.said.nothing_was_written")])) from None
    answer = dict(answer, file=shown(path))
    who = [f"{c['label']}" + (" (joins)" if c["joins"] else "") for c in answer["participants"]]
    lines = [i18n.t("cli.qdpx.is_a_refi_qda_project_from", name=path.name, package=answer['package'], sources=i18n.t("cli.n.source", n=len(answer['sources'])))]
    lines += [qdpx_source_line(v) for v in answer["sources"]]
    if answer["groups"]:
        lines.append(i18n.t("cli.qdpx.its_code_groups", list=', '.join(answer['groups'])))
    # an Idiograph package's LPETs and LGETs (qdpxlpets)
    if answer.get("lpets"):
        lines.append(i18n.t("cli.qdpx.its_lpets", list=', '.join(answer['lpets'])))
    if answer.get("lgets"):
        lines.append(i18n.t("cli.qdpx.its_lgets", list=', '.join(answer['lgets'])))
    lines += answer["lines"] + names_lines(answer)
    if args.dry_run:
        if answer["said"]:
            return dict(answer, dry_run=True), [i18n.t("cli.qdpx.dry_run_nothing_was_written_cannot", name=path.name, said=answer['said'])] + lines
        board = (i18n.t("cli.qdpx.each_gets_a_pets_board_from", package=answer['package']) if body["pets"] else "")
        return dict(answer, dry_run=True), [i18n.t("cli.qdpx.dry_run_nothing_was_written_it", list=', '.join(who), name=path.name, board=board)] + lines
    return dict(answer, written=answer["made"]), [i18n.t("cli.qdpx.brought_in_from_the_file_itself", list=', '.join(who), name=path.name)] + lines


def problems_in(path: Path, name: str, label: str) -> list[str]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        return [i18n.t("cli.problems_in.the_file_could_not_be_read", label=label, name=type(exc).__name__)]
    schema = cli.schema_of(name)
    out: list[str] = []
    cli.conform(value, schema, name, schema.get("$defs") or {}, out)
    return [f"{label}: {line}" for line in out]


def cmd_validate(p: Project, args) -> tuple:
    problems, files = [], []
    project = p.root / srv.PROJECT_FILE
    if project.is_file():
        files.append(i18n.t("cli.validate.the_project_file_2"))
        problems += problems_in(project, "project", i18n.t("cli.validate.the_project_file"))
    held = gets_mod.gets_path(p.root)
    if held.is_file():
        files.append(i18n.t("cli.validate.the_gets_file_2"))
        problems += problems_in(held, "gets", i18n.t("cli.validate.the_gets_file"))
    for b in p.books:
        book = Path(b["workbook"])
        for path, name, word in ((rounds_mod.progress_path(book), "progress", i18n.t("cli.validate.progress_file")),
                                 (themes.themes_path(book), "themes", i18n.t("cli.validate.themes_file"))):
            if path.is_file():
                files.append(f"{b['case']}'s {word}")
                problems += problems_in(path, name, i18n.t("cli.validate.the", case=b['case'], word=word))
    if problems:
        lines = problems
    else:
        lines = [i18n.t("cli.validate.every_file_of_the_project_reads", list=', '.join(files) if files else i18n.t("cli.validate.none_yet"))]
    return {"files": files, "problems": problems, "valid": not problems}, lines


def each_project(projects: list[Project], closed: list[str], command, args) -> tuple:
    """A command that names no case, `cases` or `validate`, run on every project it reads, each
    project's answer under its name in `projects`, its lines under its name, and a line for each
    project agents may not read."""
    answers, lines = [], []
    for p in projects:
        answer, said = command(p, args)
        answers.append(dict(answer, name=p.info["name"]))
        lines += ([""] if lines else []) + said
    for name in closed:
        lines += ["", i18n.t("cli.each_project.closed_to_ai_agents_settings_projects", name=name)]
    return {"projects": answers, "closed": closed}, lines


class SearchCase:
    """A case's statements and the board its hits are placed on, read once for a page of hits."""

    def __init__(self, p: "Project", name: str, board: str | None):
        self.b = p.case(name)
        book = Path(self.b["workbook"])
        self.read = themes.read_cards(book)
        self.sids, _ = ids_of(self.read)
        self.data = themes.load(book)
        self.labels = p.info["pet_labels"]
        try:
            self.board = pick_board(self.data, board) if themes.boards_of(self.data) else None
        except cli.Refused:
            self.board = None
        self.where, self.marks = {}, {}
        if self.board is not None:
            got = [x for x in placements(self.read, {"boards": [self.board]})]
            self.where = got[0]["where"] if got else {}
            try:
                self.marks = idiograph_find.pet_marks(self.board, self.labels)
            except Exception:
                self.marks = {}

    def placed(self, key: str) -> dict | None:
        """Where the board places a statement, its label's id, export label and path of titles."""
        if self.board is None or key not in self.where:
            return None
        at = self.where[key]
        out = {"board": str(self.board.get("id")), "name": str(self.board.get("name") or ""), "where": at["where"]}
        if at.get("label"):
            out["label"] = at["label"]
            out["export_label"] = self.marks.get(at["label"], (0, ""))[1]
        return out


def cmd_search(projects: list, closed: list[str], args) -> tuple:
    """`search <words>`: the app's Search (`app_search`, 17 October) for an agent (20 October), every word
    in any order, case and accents set aside, or a phrase in quotation marks, over a project, every project
    it reads when none is named, a case with `--case`, one of its boards with `--board` too, or with
    `--folder` a Sift project or a Trace project. `--whole-word` and `--match-case` are the card's two ticks,
    Whole word on unless `--no-whole-word` is given and Match case off unless given. `--kinds` narrows the kinds, `--limit` the hits a page
    holds, and `more` the cursor the answer before gave. Each hit names its case, where it is, its speaker,
    the snippet with each word between two asterisks, a statement's id and key with where the board places
    it, and the tool that opens it whole. Only reads."""
    started = time.perf_counter()
    q, words, phrase = cli.search_words(getattr(args, "words", ""), *cli.search_modifiers(args))
    kinds = cli.search_kinds(getattr(args, "kinds", None))
    start, limit = cli.search_page(args)
    case_named, board_named = getattr(args, "case", None), getattr(args, "board", None)
    if board_named and not case_named:
        raise cli.Refused(_w("BOARD_NEEDS_CASE"))
    answers = []                    # (project name, project, scope, the app's answer)
    if case_named:
        p = project_for(projects, case_named) if len(projects) > 1 else projects[0]
        b = p.case(case_named)
        book = Path(b["workbook"])
        cases = [{"case": routes.case_label(book), "workbook": book, "path": srv.rel_path(book)}]
        found = idiograph_find.distil_found(words, "case", cases, p.info, None, p.info["pet_labels"])
        board_id = None
        if board_named:
            board_id = str(pick_board(load_board_file(book), board_named).get("id"))
            found = [it for it in found if it["go"].get("screen") != "pets" or str(it["go"].get("board")) == board_id]
        scope = "board" if board_named else "case"
        answers.append((p.info["name"], p, "case", cli.search_answer(q, words, phrase, found, "case", started)))
    else:
        scope = "project"
        for p in projects:
            found = idiograph_find.distil_found(words, "project", routes.search_cases(p.root), p.info,
                                            gets_mod.gets_path(p.root), p.info["pet_labels"])
            answers.append((p.info["name"], p, "project", cli.search_answer(q, words, phrase, found, "project", started)))
    # the kinds named in the words of the projects' method, a thematic analysis project's Codes and Extracts, when
    # every project answering has the one method (taword, 1 November 2026)
    methods = {i18n.method_of(p.info.get("method")) for _name, p, *_ in answers}
    with i18n.in_method(methods.pop() if len(methods) == 1 else None):
        return cli.search_said(q, phrase, scope, answers, kinds, start, limit, board_named, closed, words.whole, words.case)


COMMANDS = {("cases", None): cmd_cases, ("statements", None): cmd_statements,
            ("board", "list"): cmd_board_list, ("board", "show"): cmd_board_show,
            ("board", "compare"): cmd_board_compare, ("board", "new"): cmd_board_new,
            ("board", "import"): cmd_board_import, ("gets", "import"): cmd_gets_import,
            ("board", "apply"): cmd_board_apply, ("board", "current"): cmd_board_current,
            ("board", "export"): cmd_board_export, ("board", "canvas"): cmd_board_canvas,
            ("board", "rename"): cmd_board_rename, ("board", "duplicate"): cmd_board_duplicate,
            ("board", "fresh"): cmd_board_fresh,
            ("board", "delete"): cmd_board_delete,
            ("board", "note"): cmd_board_note, ("board", "history"): cmd_board_history,
            ("board", "revision"): cmd_board_revision, ("board", "restore"): cmd_board_restore,
            ("board", "copy"): cmd_board_copy, ("board", "complete"): cmd_board_complete,
            ("gets", "show"): cmd_gets_show, ("gets", "apply"): cmd_gets_apply, ("gets", "take"): cmd_gets_take, ("gets", "colour"): cmd_gets_colour,
            ("gets", "export"): cmd_gets_export,
            ("gets", "fresh"): cmd_gets_fresh, ("gets", "duplicate"): cmd_gets_duplicate,
            ("gets", "rename"): cmd_gets_rename, ("gets", "note"): cmd_gets_note, ("gets", "canvas"): cmd_gets_canvas,
            ("gets", "current"): cmd_gets_current, ("gets", "delete"): cmd_gets_delete,
            ("gets", "complete"): cmd_gets_complete, ("gets", "history"): cmd_gets_history,
            ("gets", "revision"): cmd_gets_revision, ("gets", "restore"): cmd_gets_restore,
            ("gets", "subs"): cmd_gets_subs, ("gets", "settings"): cmd_gets_settings,
            ("turn", "show"): cmd_turn_show, ("turn", "write"): cmd_turn_write, ("validate", None): cmd_validate,
            ("turn", "edit"): cmd_turn_edit, ("turn", "interviewer-note"): cmd_turn_interviewer_note,
            ("turn", "assign"): cmd_turn_assign, ("turn", "assign-undo"): cmd_turn_assign_undo,
            ("turn", "trim"): cmd_turn_trim, ("turn", "trim-undo"): cmd_turn_trim_undo,
            ("project", "add-transcripts"): cmd_project_add_transcripts,
            ("names", "list"): cmd_names_list, ("names", "check"): cmd_names_check, ("names", "remove"): cmd_names_remove,
            ("names", "replace"): cmd_names_replace,
            ("import", None): cmd_import, ("qdpx", None): cmd_qdpx, ("offset", None): cmd_offset, ("audio", "attach"): cmd_audio_attach,
            ("timepoints", None): cmd_timepoints,
            ("length", None): cmd_length, ("settings", None): cmd_settings, ("quote-heading", None): cmd_quote_heading,
            ("transcript", "replace"): cmd_transcript_replace, ("transcript", "replace-undo"): cmd_transcript_replace_undo,
            ("trajectories", "show"): cmd_trajectories_show, ("trajectories", "apply"): cmd_trajectories_apply,
            ("codes", "list"): cmd_codes_list, ("codes", "show"): cmd_codes_show, ("codes", "new"): cmd_codes_new,
            ("codes", "rename"): cmd_codes_rename, ("codes", "describe"): cmd_codes_describe,
            ("codes", "merge"): cmd_codes_merge, ("codes", "delete"): cmd_codes_delete,
            ("codes", "add"): cmd_codes_extract, ("codes", "remove"): cmd_codes_extract,
            ("codes", "apply-last"): cmd_codes_quick, ("codes", "in-vivo"): cmd_codes_quick,
            ("codes", "undo"): cmd_codes_undo, ("codes", "redo"): cmd_codes_undo,
            ("project", "send"): cmd_project_send,
            ("project", "export-qdpx"): cmd_project_export_qdpx,
            ("project", "boards-in"): lambda p, args: cmd_project_boards_in([p], args),
            ("project", "set"): cmd_project_set,
            ("project", "show"): cmd_project_show,
            ("project", "remove"): cmd_project_remove,
            ("project", "history"): cmd_project_history,
            ("team", "show"): cmd_team_show, ("team", "on"): cmd_team_on, ("team", "set"): cmd_team_set,
            ("team", "invite"): cmd_team_invite, ("team", "answers"): cmd_team_answers, ("team", "admit"): cmd_team_admit,
            ("team", "join"): cmd_team_join, ("team", "joined"): cmd_team_joined, ("team", "remove"): cmd_team_remove,
            ("team", "send"): cmd_team_send,
            ("team", "lead"): cmd_team_lead, ("team", "take"): cmd_team_take,
            # a reviewer's board sent straight in (wtboard, 9 November 2026)
            ("team", "board-send"): cmd_team_board_send, ("team", "board-take"): cmd_team_board_take,
            ("team", "board-answer"): cmd_team_board_answer, ("team", "boards"): cmd_team_boards,
            ("project", "new"): lambda p, args: cmd_project_new(args),
            ("agents", "log"): lambda p, args: cmd_agents_log(args),
            ("participant", "rename"): cmd_participant_rename, ("participant", "complete"): cmd_participant_complete,
            ("participant", "export"): cmd_participant_export,
            # each participant's picture, label and pen portrait (pbiobuild, 11 November 2026)
            ("participant", "set"): cmd_participant_set, ("participant", "show"): cmd_participant_show,
            # the project's demographics (demobuild, 12 November 2026)
            ("demographics", "show"): cmd_demographics_show, ("demographics", "apply"): cmd_demographics_apply,
            ("demographics", "move-tags"): cmd_demographics_move_tags,
            ("hold", None): lambda p, args: holds.cmd_hold(p, args), ("hold", "show"): lambda p, args: holds.cmd_hold_show(p, args),
            # Working together's comments and review (wtreview, 8 November 2026, see review.py)
            **review_mod.COMMANDS}


def case_hit(hit: dict, r: dict, go: dict, named: str, cases: dict, p, board: str | None) -> None:
    """A Search hit on one of Idiograph's screens, as the family's `cli.search_hit` asks (the family codebase's
    fourth build, 22 October 2026, from it): a passage's or a statement's sheet, row, time and speaker, a
    statement's id and key with where the board places it, a PET's or a GET's board and label, and the tool
    that opens each whole, `named` the project when the answer holds several."""
    screen = go.get("screen")
    case = r.get("case", "")
    if screen == "statements":
        sheet, row = go.get("sheet", ""), go.get("row")
        hit.update(sheet=sheet, row=row, time=r["where"][len(sheet):].strip(), speaker=go.get("speaker", ""))
        hit["open"] = cli.opener("turn_show", {"case": case, "sheet": sheet, "row": row},
                             ["turn", "show", case, sheet, str(row)], named)
        if r["kind"] == "statement" and p is not None:
            if case not in cases:
                cases[case] = SearchCase(p, case, board)
            c = cases[case]
            key = themes.card_key(sheet, row, go.get("line", 0))
            hit.update(id=c.sids.get(key, ""), key=key)
            placed = c.placed(key)
            if placed:
                hit["placed"] = placed
    elif screen == "pets":
        hit["board"] = go.get("board", "")
        if go.get("item") in ("group", "sticky"):
            hit["label" if go["item"] == "group" else "sticky"] = go.get("id", "")
        hit["open"] = cli.opener("board_show", {"case": case, "board": go.get("board", "")},
                             ["board", "show", case, go.get("board", "")], named)
    elif screen == "gets":
        hit["board"] = go.get("board", "")
        if go.get("item") == "group":
            hit["label"] = go.get("id", "")
        hit["open"] = cli.opener("gets_show", {"board": go.get("board", "")}, ["gets", "show", go.get("board", "")], named)
    elif screen == "project":
        hit["open"] = cli.opener("cases", {}, ["cases"], named)


def arguments(sub, common, writes) -> None:
    """Idiograph's commands under the family's parser at the top of `idiograph` (`cli.parser`, the family
    codebase's fourth build, 22 October 2026, from it), each with the options every command takes, `common`,
    and a write's, `writes`, its dry run, his request and the agent's tool."""
    sub.add_parser("cases", parents=[common], help="the study, each participant with its workbook, phases and boards")
    one = sub.add_parser("statements", parents=[common], help="every statement of a participant, with where each board places it")
    one.add_argument("case")
    one.add_argument("--timepoint", default=None, help=TIMEPOINT_HELP)
    board = sub.add_parser("board", parents=[common], help="a participant's PETs boards").add_subparsers(dest="act", required=True)
    x = board.add_parser("list", parents=[common])
    x.add_argument("case")
    x = board.add_parser("show", parents=[common])
    x.add_argument("case")
    x.add_argument("board", nargs="?")
    x.add_argument("--labels", default=None,
                   help="letters or numbers for each label's export_label in place of the project's setting")
    x.add_argument("--close", default=None,
                   help="the close pairs within this many seconds, for this one look, in place of the setting")
    x = board.add_parser("compare", parents=[common])
    x.add_argument("case")
    x.add_argument("boards", nargs="*")
    x = board.add_parser("new", parents=[common, writes])
    x.add_argument("case")
    x.add_argument("--from", dest="source", required=True)
    x.add_argument("--layout", default=None,
                   help="the board whose layout it keeps, the board on the canvas by default, or fresh to lay it out afresh")
    x = board.add_parser("import", parents=[common, writes],
                         help="a new board made from his own table of PETs, a CSV or an Excel sheet with PET, Sub-theme, "
                              "Experiential statements, Location and Quote columns, each row matched to a statement")
    x.add_argument("case")
    x.add_argument("--from", dest="source", required=True, help="the table, by its path from the project's folder or in full")
    x.add_argument("--sheet", default=None, help="an Excel file's sheet by its name, the first with anything in it without it")
    x.add_argument("--name", default="", help=f"the board's name, {IMPORTED} without it")
    x.add_argument("--unmatched", choices=("add", "skip"), default="skip",
                   help="a row with nothing close on its passage: add makes it a new statement there with its quote, "
                        "skip, the default, leaves it out")
    x = board.add_parser("apply", parents=[common, writes])
    x.add_argument("case")
    x.add_argument("board")
    x.add_argument("--ops", required=True)
    x = board.add_parser("current", parents=[common, writes])
    x.add_argument("case")
    x.add_argument("board")
    x = board.add_parser("canvas", parents=[common, writes], help="put a board on the canvas")
    x.add_argument("case")
    x.add_argument("board")
    x = board.add_parser("rename", parents=[common, writes], help="rename a board")
    x.add_argument("case")
    x.add_argument("board")
    x.add_argument("name")
    x = board.add_parser("duplicate", parents=[common, writes], help="copy a board and put the copy on the canvas")
    x.add_argument("case")
    x.add_argument("board")
    x.add_argument("--name", default="", help="the copy's name, the board's name and copy by default")
    x = board.add_parser("fresh", parents=[common, writes],
                         help="a new board with no PETs, as New board in the board menu, put on the canvas")
    x.add_argument("case")
    x.add_argument("--start", choices=themes.STARTS, default="empty",
                   help="empty: every statement waiting in the sidebar's Not placed, the default; canvas: every "
                        "statement on the canvas as a pile in the middle")
    x.add_argument("--name", default="", help="the board's name, the next Board N by default")
    x = board.add_parser("delete", parents=[common, writes], help="delete a board, a copy of it kept in _Archive")
    x.add_argument("case")
    x.add_argument("board")
    x = board.add_parser("note", parents=[common, writes], help="a board's note, as the board note on the PETs screen sets it")
    x.add_argument("case")
    x.add_argument("board")
    x.add_argument("text", help="the board's note, his words, or empty to take it off")
    x = board.add_parser("history", parents=[common], help="a board's History, or one revision of it as board show sets it out")
    x.add_argument("case")
    x.add_argument("board", nargs="?")
    x.add_argument("--revision", default=None, help="one revision, by its id, r3, as the History lists it")
    x = board.add_parser("revision", parents=[common, writes], help="save a revision, the board as it stands kept in its History")
    x.add_argument("case")
    x.add_argument("board", nargs="?")
    x.add_argument("--name", default="", help="the revision's name, his request when left out")
    x = board.add_parser("restore", parents=[common, writes],
                         help="a revision made the board, the board as it stands kept in its History first")
    x.add_argument("case")
    x.add_argument("board")
    x.add_argument("revision", help="the revision, by its id, r3, as board history lists it")
    x = board.add_parser("copy", parents=[common, writes], help="a label copied to another board, as Copy to board does")
    x.add_argument("case")
    x.add_argument("board", help="the board the label is on")
    x.add_argument("label", help="the label, by its id, g3, or its title")
    x.add_argument("--to", required=True, help="the board it goes to")
    x.add_argument("--revision", default=None, help="copy the label from this revision of the board, by its id, r3")
    x = board.add_parser("complete", parents=[common, writes], help="PETs marked complete on the Current board, or reopened")
    x.add_argument("case")
    x.add_argument("--reopen", action="store_true", help="reopen PETs in place of marking them complete")
    x = board.add_parser("export", parents=[common])
    x.add_argument("case")
    x.add_argument("board", nargs="?")
    x.add_argument("--word", action="store_true", help="a Word document, the IPA book's table of PETs")
    x.add_argument("--draft", action="store_true",
                   help="the PET draft in markdown and the statements CSV with its Proposed PET column, in the "
                        "participant's Working folder, as the PETs screen's Export writes them")
    x.add_argument("--pdf", action="store_true",
                   help="a PDF, the print view's table of PETs on landscape A4, printed by Chrome, Chromium, Brave "
                        "or Edge headless")
    x.add_argument("--canvas", default=None, choices=("pdf", "png"),
                   help="the canvas itself, every statement whole, as the PETs screen's Export makes it on the canvas: "
                        "pdf on one landscape page, or png, the whole canvas pictured at twice its scale, beside the "
                        "workbook, named as the table's PDF with canvas after it. Made by the app's own page in "
                        "Chrome, Chromium, Brave or Edge headless. Takes --out, --replace and --dry-run alone")
    x.add_argument("--labels", default=None,
                   help="letters, A, A1, A1.1, as the book has them, or numbers, PET 1, PET 1a, 1a.1, for this run "
                        "in place of the project's setting")
    x.add_argument("--not-placed", action="store_true", help="put Not placed at the end, left out without it")
    # --binned, its name before 20 October, says the same
    x.add_argument("--set-aside", "--binned", dest="binned", action="store_true",
                   help="put the statements set aside at the end, left out without it")
    x.add_argument("--stacked", action="store_true",
                   help="put the statements stacked under a top beneath it, left out without it")
    x.add_argument("--for-sending", action="store_true",
                   help="name the file by the participant alone, P1 - Ada.pdf, with no board's name on the page")
    x.add_argument("--no-descriptions", action="store_true",
                   help="leave each PET's and sub-PET's description out from under its title, as Descriptions unticked does")
    x.add_argument("--replace", action="store_true",
                   help="with --pdf, write over a PDF of the same name in place of putting the date in the name")
    x.add_argument("--board-note", action="store_true",
                   help="with --pdf, put the board's note under the head, as the print view's Board note does")
    x.add_argument("--portrait", action="store_true",
                   help="put the participant's label and pen portrait under the head, never their picture, as Pen "
                        "portrait does, left out without it")
    x.add_argument("--out", default=None,
                   help="with --pdf, where it goes, a folder or a file name ending .pdf, beside the workbook "
                        "without it")
    x.add_argument("--dry-run", action="store_true", help="say what would be written and write nothing")
    # every board command takes the timepoint whose canvas it works on
    for one in board.choices.values():
        one.add_argument("--timepoint", default=None, help=TIMEPOINT_HELP)
    g = sub.add_parser("gets", parents=[common], help="the project's GETs").add_subparsers(dest="act", required=True)
    x = g.add_parser("export", parents=[common],
                     help="a GETs board as a PDF, as the GETs screen's print card makes it")
    x.add_argument("board", nargs="?")
    x.add_argument("--pdf", action="store_true", help="a PDF of the print view, the default")
    x.add_argument("--word", action="store_true",
                   help="a thematic analysis project's table of themes as a Word document at the project's root, "
                        "never over a file there. Takes --selected, --notes, --for-sending, --no-descriptions, "
                        "--participants and --dry-run")
    x.add_argument("--canvas", default=None, choices=("pdf", "png"),
                   help="the canvas itself, as the print card's Canvas on one page makes it: pdf on one landscape "
                        "page, or png, the whole canvas pictured at twice its scale, at the project's root. Takes "
                        "--notes, --out, --replace and --dry-run alone")
    x.add_argument("--out", default=None, help="where it goes, a folder or a file name ending .pdf, the "
                                                "project's root, beside the GETs file, without it")
    x.add_argument("--what", default=None, choices=("table", "trail", "all"),
                   help="the GET table, the default, the audit trail, or all, the full set: a contents page, each "
                        "participant's table of PETs, the GET table and the trail")
    x.add_argument("--selected", action="store_true", help="the quote alone, as Their key quote only does, every item without it")
    x.add_argument("--notes", action="store_true", help="put the participant notes in, left out without it")
    x.add_argument("--for-sending", action="store_true", help="no board's name on the page or in the file's name")
    x.add_argument("--no-descriptions", action="store_true",
                   help="leave each GET's and PET's description out from under its title, as Descriptions unticked does")
    x.add_argument("--get", default=None, help="one GET's audit trail alone, by its id, G2")
    x.add_argument("--participants", action="store_true",
                   help="a first page listing each participant, their number, pseudonym, label and pen portrait, "
                        "never their picture, as Participants table does, left out without it")
    x.add_argument("--replace", action="store_true",
                   help="write over a PDF of the same name in place of putting the date in the name")
    x.add_argument("--dry-run", action="store_true", help="say what would be written and write nothing")
    x = g.add_parser("show", parents=[common])
    x.add_argument("board", nargs="?")
    x = g.add_parser("apply", parents=[common, writes])
    x.add_argument("board")
    x.add_argument("--ops", required=True)
    x = g.add_parser("import", parents=[common, writes],
                     help="with --lpets, a participant's LPETs made from his own table of them, a row an LPET with a "
                          "cell for each timepoint, the PETs its cells quote proposed as its members")
    x.add_argument("--from", dest="source", required=True, help="the table, by its path from the project's folder or in full")
    x.add_argument("--sheet", default=None, help="an Excel file's sheet by its name, the first with anything in it without it")
    x.add_argument("--name", default="", help=f"the board's name, {IMPORTED} without it")
    x = g.add_parser("take", parents=[common, writes], help="take a participant's changes into the GETs")
    x.add_argument("case")
    x = g.add_parser("colour", parents=[common, writes], help="a participant's colour on the GETs board, from the 25")
    x.add_argument("case")
    x.add_argument("colour", help="the colour's name, Teal, or default")
    x = g.add_parser("fresh", parents=[common, writes], help="a new GETs board, every card in the pile, put on the canvas")
    x.add_argument("--name", default="", help="the board's name, the next Board N by default")
    x = g.add_parser("duplicate", parents=[common, writes], help="copy a GETs board and put the copy on the canvas")
    x.add_argument("board")
    x.add_argument("--name", default="", help="the copy's name, the board's name and copy by default")
    x = g.add_parser("rename", parents=[common, writes], help="rename a GETs board")
    x.add_argument("board")
    x.add_argument("name")
    x = g.add_parser("note", parents=[common, writes], help="a GETs board's note, as the board note sets it")
    x.add_argument("board")
    x.add_argument("text", help="the board's note, his words, or empty to take it off")
    x = g.add_parser("canvas", parents=[common, writes], help="put a GETs board on the canvas")
    x.add_argument("board")
    x = g.add_parser("current", parents=[common, writes], help="mark a GETs board as the Current board")
    x.add_argument("board")
    x = g.add_parser("delete", parents=[common, writes], help="delete a GETs board, a copy of it kept in _Archive")
    x.add_argument("board")
    x = g.add_parser("complete", parents=[common, writes], help="GETs marked complete on the Current board, or reopened")
    x.add_argument("--reopen", action="store_true", help="reopen GETs in place of marking them complete")
    x = g.add_parser("history", parents=[common], help="a GETs board's History, or one revision of it as gets show sets it out")
    x.add_argument("board", nargs="?")
    x.add_argument("--revision", default=None, help="one revision, by its id, r3, as the History lists it")
    x = g.add_parser("revision", parents=[common, writes], help="save a revision of a GETs board")
    x.add_argument("board", nargs="?")
    x.add_argument("--name", default="", help="the revision's name, his request when left out")
    x = g.add_parser("restore", parents=[common, writes], help="a revision made the GETs board, the board kept first")
    x.add_argument("board")
    x.add_argument("revision", help="the revision, by its id, r3, as gets history lists it")
    x = g.add_parser("subs", parents=[common, writes], help="Add every sub-theme: a card for each sub-theme with none")
    x.add_argument("board", nargs="?")
    x = g.add_parser("settings", parents=[common, writes],
                     help="the study's settings under GETs in Project settings, read, or saved with the options given")
    x.add_argument("--minimum", default=None, help="the participants a GET needs, a whole number, or band for Smith's band")
    x.add_argument("--one-per-pet", dest="one_per_pet", default=None, help="on or off")
    x.add_argument("--out", action="append", default=None,
                   help="a participant out of the study with his reason, Name=reason, given again for each one more")
    x.add_argument("--in", dest="back_in", action="append", default=None,
                   help="a participant back in the study, given again for each one more")
    # and every GETs command a participant's LPETs in place of the project's GETs
    for one in g.choices.values():
        one.add_argument("--lpets", default=None, metavar="PARTICIPANT", help=LPETS_HELP)
    t = sub.add_parser("turn", parents=[common], help="one passage of a participant").add_subparsers(dest="act", required=True)
    x = t.add_parser("show", parents=[common])
    x.add_argument("case")
    x.add_argument("sheet")
    x.add_argument("row")
    x = t.add_parser("write", parents=[common, writes])
    x.add_argument("case")
    x.add_argument("sheet")
    x.add_argument("row")
    x.add_argument("--from", dest="source", required=True)
    x = t.add_parser("edit", parents=[common, writes],
                     help="a passage's words corrected in place, and its timecode, as the statements screen's Edit does")
    x.add_argument("case")
    x.add_argument("sheet")
    x.add_argument("row")
    x.add_argument("--text", default=None, help="the passage's words as they should read, whole")
    x.add_argument("--time", default=None, help="the passage's timecode, MM:SS or H:MM:SS")
    x = t.add_parser("interviewer-note", parents=[common, writes],
                     help="the interviewer's note on one of his own passages, an empty one clearing it")
    x.add_argument("case")
    x.add_argument("sheet")
    x.add_argument("row")
    x.add_argument("--text", required=True, help="the note, a line an entry, empty to clear it")
    x = t.add_parser("assign", parents=[common, writes],
                     help="words of a passage, or the whole of it, assigned to another speaker")
    x.add_argument("case")
    x.add_argument("sheet")
    x.add_argument("row")
    x.add_argument("--to", required=True, help="the speaker the words go to, by name")
    x.add_argument("--words", default=None, help="the words to assign, exactly as the passage has them, once in it")
    x.add_argument("--start", type=int, default=None, help="the words' first character in the passage, from 0")
    x.add_argument("--end", type=int, default=None, help="the character after the words' last")
    x = t.add_parser("assign-undo", parents=[common, writes], help="an assignment undone by the id it answered with")
    x.add_argument("case")
    x.add_argument("id")
    x = t.add_parser("trim", parents=[common, writes],
                     help="the consent talk cut off a sheet's front, or the goodbyes off its back")
    x.add_argument("case")
    x.add_argument("sheet")
    x.add_argument("row")
    x.add_argument("--before", action="store_true", help="cut this passage and every one above it")
    x.add_argument("--after", action="store_true", help="cut this passage and every one below it")
    x = t.add_parser("trim-undo", parents=[common, writes], help="a trim undone by the id it answered with")
    x.add_argument("case")
    x.add_argument("id")
    x = sub.add_parser("import", parents=[common, writes],
                       help="a transcript file made into its raw source, or a raw source into the participant's workbook, "
                            "as the import and create cards make them")
    x.add_argument("file", help="the file, from the project's folder or in full, in a participant's folder or its Source")
    x.add_argument("--columns", default=None,
                   help="each column's role in the file's order, with commas: Speaker, Time, Transcript, Exploratory "
                        "notes, Experiential statements, Quote or Leave out, the guess when left out. A Quote column's "
                        "lines pair with the statements on the same row by order")
    x.add_argument("--sheet", default=None, help="for an Excel file, the sheet to read by its name, the first with "
                                                 "anything in it when left out")
    x.add_argument("--interviewer", default=None, help="the speaker who is the interviewer, the guess when left out, "
                                                       "empty for nobody")
    x.add_argument("--name", default=None, help="the new workbook's name, for a raw source, the card's suggestion when left out")
    x.add_argument("--speakers", default=None, help="each speaker's role, Name=Role with commas, each Interviewer, "
                                                    "Participant or Other speaker, the guess when left out")
    x.add_argument("--time-format", default=None, help="how the Time column's times are read: hms (1:02:03), ms (02:03), "
                                                       "fraction (1:02:03.5), seconds (62.5) or frames (1:02:03:12), "
                                                       "the one found when left out")
    x.add_argument("--frame-rate", default=None, help="the frames a second of frames times, 25 when left out")
    x.add_argument("--audio", default=None, help="a recording to copy into the participant's folder, .m4a, .mp3, .wav or .m4b, "
                                                 "named by the participant's pseudonym and timepoint, Wren T2.m4a")
    x.add_argument("--offset", default=None, help="the recording's offset in seconds, plus or minus, which playback adds "
                                                  "to every time code, 0 when left out")
    x.add_argument("--timepoint", default=None, help="in a project of two or more timepoints, the one this interview was "
                                                     "at, by its number or its label, T1 when left out. A participant "
                                                     "with a workbook gains it as a sheet at the end")
    x = sub.add_parser("qdpx", parents=[common, writes],
                       help="a REFI-QDA project (.qdpx) from ATLAS.ti, NVivo or MAXQDA brought in as participants, "
                            "each source a participant's transcript")
    x.add_argument("file", help="the .qdpx, from the project's folder or in full, under the project's folder")
    x.add_argument("--sources", default=None,
                   help="the sources to bring in, number=Pseudonym:participant number:timepoint:interview with commas, "
                        "1=Wren:3:T1,2=Ash, all but the pseudonym optional. The dry run lists the sources")
    x.add_argument("--codes", default=None, help="each code on a passage as statements (the default, its quotations "
                                                 "the quote), notes, or leave")
    x.add_argument("--comments", default=None, help="each comment on a quotation as notes (the default) or statements")
    x.add_argument("--loose", default=None, help="a quotation with no code and no comment as blank (a blank "
                                                 "experiential statement with its quote, the default) or leave")
    x.add_argument("--memos", default=None, help="a source's memos to a text file in Source (source, the default) or leave")
    x.add_argument("--recordings", default=None, help="a recording in the project copied into Source (copy, the "
                                                      "default) or leave")
    x.add_argument("--pets", action="store_true", help="with codes as statements, a PETs board From <package>, a PET "
                                                       "a code group, and from Idiograph's own package in a project of "
                                                       "timepoints each participant's LPETs and the LGETs as boards too")
    x.add_argument("--no-demographics", action="store_true",
                   help="leave the package's variables out, which otherwise come in as the participants' demographics, "
                        "each variable a category")
    x.add_argument("--user", default=None, help="one coder's work alone, by name, every coder's when left out")
    x.add_argument("--speakers", default=None, help="each speaker's role, Name=Role with commas, the guess when left out")
    x.add_argument("--skip", action="append", default=None, metavar="ENTRY:N",
                   help="leave this find of the project's list of names as written, the entry's number and its place "
                        "among that entry's finds, 3:1, given again for each one more")
    nm = sub.add_parser("names", parents=[common],
                        help="the project's list of real names and what each is written as, replaced as a transcript "
                             "comes in: counts and numbers only, never a real name").add_subparsers(dest="act", required=True)
    nm.add_parser("list", parents=[common], help="each entry's number, its replacement, whom it is for and its spellings counted")
    nm.add_parser("check", parents=[common], help="the transcripts already in searched for the list's names, counts only")
    x = nm.add_parser("remove", parents=[common, writes], help="entries taken off the list by their numbers")
    x.add_argument("numbers", type=int, nargs="+", help="the entries' numbers, from the list")
    x = nm.add_parser("replace", parents=[common, writes],
                      help="the list's names replaced in the transcripts already in, each workbook kept in its "
                           "participant's _Archive first, counts only")
    x.add_argument("--skip", action="append", default=None, metavar="ENTRY:N",
                   help="leave this find as written, the entry's number and its place among that entry's finds as "
                        "names check counts them, 3:1, given again for each one more")
    x = sub.add_parser("timepoints", parents=[common, writes],
                       help="the project's timepoints, read, or set from --from as Project settings sets them")
    x.add_argument("--from", dest="source", default=None,
                   help='a JSON file, [{"label": "T1", "description": "Before the season"}, ...] or a number')
    tj = sub.add_parser("trajectories", parents=[common],
                        help="in a project of two or more timepoints, the Trajectories board: the project's own "
                             "trajectories, each participant placed in one with a note on why").add_subparsers(dest="act", required=True)
    tj.add_parser("show", parents=[common], help="the board, each trajectory with its participants, and each cell's "
                                                 "quotes with where each comes from")
    x = tj.add_parser("apply", parents=[common, writes], help="change the board with its operations, all or nothing")
    x.add_argument("--ops", required=True, help='a JSON file, a list of operations or {"operations": [...]}: '
                                                '{"op": "add", "title": "Positive"}, rename, move, remove, describe, '
                                                'colour, icon, {"op": "place", "participant": "Wren", "column": '
                                                '"Positive"}, order, note, title, tags, tag_colour, picture, hide, '
                                                'show, and on an LPET state, quote (a quote\'s key, or a passage: '
                                                'interview, turn and start and end), bold, domain, states_from_notes, '
                                                'each on the LPETs board LGETs take or the one its "board" names')
    cd = sub.add_parser("codes", parents=[common],
                        help="in a thematic analysis project, the code list: codes many extracts share, each extract "
                             "one quote").add_subparsers(dest="act", required=True)
    cd.add_parser("list", parents=[common], help="every code with its extracts and participants counted")
    x = cd.add_parser("show", parents=[common], help="one code, its description and its extracts by participant")
    x.add_argument("code", help="the code, by its name or its id, k3")
    x = cd.add_parser("new", parents=[common, writes], help="a code added to the list, with no extracts yet")
    x.add_argument("name")
    x.add_argument("--description", default="", help="what the code means")
    x = cd.add_parser("rename", parents=[common, writes], help="a code renamed everywhere: the list, every workbook, every board")
    x.add_argument("code")
    x.add_argument("name", help="its new name, not another code's")
    x = cd.add_parser("describe", parents=[common, writes], help="a code's description, \"\" clearing it")
    x.add_argument("code")
    x.add_argument("description")
    x = cd.add_parser("merge", parents=[common, writes], help="a code's extracts given to another everywhere, the code leaving the list")
    x.add_argument("code")
    x.add_argument("--into", required=True, help="the code that keeps them")
    x = cd.add_parser("delete", parents=[common, writes], help="a code with no extracts taken off the list")
    x.add_argument("code")
    for act, said in (("add", i18n.t("cli.arguments.a_code_put_on_an_extract")),
                      ("remove", i18n.t("cli.arguments.a_code_taken_off_an_extract"))):
        x = cd.add_parser(act, parents=[common, writes], help=said)
        x.add_argument("case", help="the participant")
        x.add_argument("sheet")
        x.add_argument("row", type=int)
        x.add_argument("code")
        x.add_argument("--extract", required=True, help="the extract's words, as the passage holds it")
    # the Coding screen's quick keys, R and 1 to 5, and V (quickkeysB, 9 November 2026)
    for act, said in (("apply-last", i18n.t("cli.arguments.codes_apply_last")),
                      ("in-vivo", i18n.t("cli.arguments.codes_in_vivo"))):
        x = cd.add_parser(act, parents=[common, writes], help=said)
        x.add_argument("case", help="the participant")
        x.add_argument("sheet")
        x.add_argument("row", type=int)
        x.add_argument("--words", required=True, help="the words of the passage that become the new extract")
        if act == "apply-last":
            x.add_argument("--recent", type=int, default=1, choices=range(1, codes_mod.RECENT_MAX + 1),
                           help="which of the codes used last, 1 the last one (R), 2 to 5 the ones before it")
    cd.add_parser("undo", parents=[common, writes], help="the list's last change put back, every file it wrote")
    cd.add_parser("redo", parents=[common, writes], help="the change undone made again")
    x = sub.add_parser("settings", parents=[common, writes],
                       help="his own settings, read, or set as Settings sets them: --your-name, the name the print "
                            "views' foot and Word's author carry, the Interviewer name standing in while it is empty")
    x.add_argument("--your-name", dest="your_name", default=None, help="Your name, or \"\" to leave it empty")
    x.add_argument("--ai-prompt-file", dest="ai_prompt_file", default=None,
                   help="set the statements' AI prompt from this UTF-8 text file, with {research_question}, "
                        "{guidance} and {examples} where they go, an empty file refused")
    x.add_argument("--ai-prompt-default", dest="ai_prompt_default", action="store_true",
                   help="put the statements' AI prompt back to the default")
    x.add_argument("--ai-provider", dest="ai_provider", default=None,
                   help="the AI's provider, as AI features' Provider list: anthropic, mistral, gemini, openai, azure, "
                        "other (another service, by its address), local (Ollama) or lmstudio. Never a key")
    x.add_argument("--ai-address", dest="ai_address", default=None,
                   help="the provider's address, for azure, other, local and lmstudio: https, or http on this "
                        "computer, \"\" for a local one's usual address")
    x.add_argument("--ai-deployment", dest="ai_deployment", default=None, help="Azure OpenAI's deployment, by its name")
    x.add_argument("--ai-model", dest="ai_model", default=None,
                   help="the model the provider is asked, by its id, as its Model list names it")
    x = sub.add_parser("length", parents=[common, writes],
                       help="the project's statement length, the words past which the length nudge speaks, 15 by "
                            "default, read, or set as Settings, Experiential statements sets it")
    x.add_argument("words", nargs="?", default=None, help="the new length, a whole number of words from 5 to 60")
    x = sub.add_parser("offset", parents=[common, writes], help="a sheet's recording's offset in seconds, plus or minus")
    x.add_argument("case")
    x.add_argument("sheet")
    x.add_argument("seconds", help="the offset in seconds, plus or minus, such as 1.5 or -2")
    au = sub.add_parser("audio", parents=[common], help="a participant's recordings").add_subparsers(dest="act", required=True)
    x = au.add_parser("attach", parents=[common, writes],
                      help="a recording copied onto an interview already in, named by the participant's pseudonym and "
                           "timepoint, Wren T2.m4a, never by the file's own name. The file is only read")
    x.add_argument("case", help="the participant, by their pseudonym")
    x.add_argument("--file", required=True, help="the recording, .m4a, .mp3, .wav or .m4b, from the project's folder or in full")
    x.add_argument("--timepoint", default=None, help="in a project of two or more timepoints, the interview's timepoint, by "
                                                     "its number or its label, T1 when left out")
    x.add_argument("--interview", default=None, help="the interview's name, when the participant has two at the timepoint")
    x.add_argument("--replace", action="store_true",
                   help="put this recording in place of the one the interview has, which goes to _Archive")
    x.add_argument("--offset", default=None, help="the recording's offset in seconds, plus or minus, 0 when left out")
    x = sub.add_parser("quote-heading", parents=[common, writes],
                       help="the quotes column's heading renamed from Key quotes to Quote on every annotation sheet "
                            "of a participant's workbook, or with --all of every participant's")
    x.add_argument("case", nargs="?", default=None, help="the participant, by their pseudonym")
    x.add_argument("--all", action="store_true", help="every participant of the project, each workbook its own write")
    tr = sub.add_parser("transcript", parents=[common], help="the app's Find and replace, the words changing in the "
                                                             "transcript, the statements, the quotes and the notes "
                                                             "alike").add_subparsers(dest="act", required=True)
    x = tr.add_parser("replace", parents=[common, writes],
                      help="find and replace in a participant's workbook, or with --all every participant's, one "
                           "batch id undoing it all")
    x.add_argument("case", nargs="?", default=None, help="the participant, by their pseudonym")
    x.add_argument("--all", action="store_true", help="every participant of the project, each workbook its own write")
    x.add_argument("--find", default=None, help="the words to find, literal, never a pattern")
    x.add_argument("--with", dest="put", default=None, help="the words to put in their place, empty when left out")
    x.add_argument("--pairs", default=None,
                   help="a file of finds and their replacements, a line a pair, the words to find, a tab and their "
                        "replacement, or JSON, so no name is on the command line. It masks as --mask does")
    x.add_argument("--mask", action="store_true",
                   help="never say the words found: the output, the answer and the progress file say [match]")
    x.add_argument("--word", action=argparse.BooleanOptionalAction, default=True,
                   help="whole words only, on by default, as the app's Whole word tick")
    x.add_argument("--case", dest="match_case", action="store_true",
                   help="match case, as the app's Match case tick, off by default")
    x = tr.add_parser("replace-undo", parents=[common, writes],
                      help="a replace undone by its batch id, in every participant's workbook that holds it")
    x.add_argument("batch", help="the batch id the replace answered with")
    x.add_argument("--participant", dest="case", default=None, help="this participant's workbook alone")
    x.add_argument("--redo", action="store_true", help="apply the replace again after an undo")
    sub.add_parser("validate", parents=[common], help="every file of the project against its schema")
    hp = sub.add_parser("hold", parents=[common],
                        help="the actions that waited for his yes in the app, a board deleted, an old revision put "
                             "over a board or words replaced across every participant, each waiting, approved or "
                             "declined. Only the app answers one")
    x = hp.add_subparsers(dest="act").add_parser("show", parents=[common],
                                                 help="one action that waited, by its id, or several, each by its id")
    x.add_argument("id", nargs="+", help="the action's id, h3, as the answer that waited gave it, or several ids")
    ag = sub.add_parser("agents", parents=[common], help="the app's record of agents: the agent log, each refusal of "
                                                         "an agent and each turn of Dangerously skip permissions, read "
                                                         "alone").add_subparsers(dest="act", required=True)
    x = ag.add_parser("log", parents=[common], help="the agent log, newest first, a project agents may not read by a "
                                                    "count alone")
    cli.add_agents_log(x)
    pj = sub.add_parser("project", parents=[common], help="the whole project sent as one file, or a sent one opened "
                                                          "as a copy, its settings saved, or a new project "
                                                          "made").add_subparsers(dest="act", required=True)
    x = pj.add_parser("send", parents=[common, writes], help="the project as one file, <Project name>.idiograph, the "
                                                             "whole of it, or some participants and kinds chosen")
    x.add_argument("--to", default=None, help="the file to write, or a folder to write it in under the project's name")
    x.add_argument("--list", action="store_true",
                   help="write nothing, and say each participant's PETs and recordings and their size, and the "
                        "whole project's, as Share a copy's card shows them")
    x.add_argument("--participant", action="append", default=None,
                   help="this participant alone, by label or pseudonym, given again for each one more, every one "
                        "when left out")
    x.add_argument("--pets", action="append", default=None,
                   help="this participant's PETs go, by label or pseudonym, given again for each one more, every "
                        "other participant's staying")
    x.add_argument("--audio", action="append", default=None,
                   help="this participant's recordings go, by label or pseudonym, given again for each one more, "
                        "every other participant's staying")
    x.add_argument("--leave-out", dest="leave_out", action="append", default=None,
                   help="kinds left out, pets, gets, audio, notes or source, joined by commas or given again")
    x.add_argument("--with", dest="with_kinds", action="append", default=None,
                   help="kinds asked for, audio, notes (working notes) or source, which a chosen send leaves out unless asked, "
                        "or gets, refused when the GETs hold a participant not sent")
    x.add_argument("--blind", action="store_true",
                   help="the PETs and the GETs left out, the analyst's grouping, so another analyst starts from "
                        "the statements alone")
    x.add_argument("--boards", choices=("current", "all"), default=None,
                   help="current: each participant's PETs, and the GETs, with the board each is going with "
                        "alone, the progress files without their History, or all, the default, every board")
    x = pj.add_parser("export-qdpx", parents=[common, writes],
                      help="the project, or the participants named, as a REFI-QDA project (.qdpx) for NVivo, ATLAS.ti, "
                           "MAXQDA and QualCoder, nothing in the project changed")
    x.add_argument("--to", default=None, help="the file to write, or a folder to write it in under the project's name")
    x.add_argument("--participant", action="append", default=None,
                   help="this participant alone, by label or pseudonym, given again for each one more, every one "
                        "when left out")
    x.add_argument("--recordings", action="store_true",
                   help="each interview's recording in the file too, its transcript linked to it by the passages' times")
    x = pj.add_parser("open-copy", parents=[common, writes],
                      help="a sent project unpacked as a copy into a new folder, then added to Idiograph's projects")
    x.add_argument("file", help="the .idiograph file")
    x.add_argument("--into", required=True, help="the folder to put the copy's folder in")
    x.add_argument("--from-name", dest="from_name", default=None,
                   help="whose copy it is, so the project's name says so: Night swimming, Curt's copy")
    x = pj.add_parser("add-transcripts", parents=[common, writes],
                      help="transcripts added to the project, as Add transcripts on its page adds them, a new "
                           "pseudonym a new participant, one there a further interview")
    x.add_argument("--from", dest="source", required=True,
                   help='a JSON list of transcripts, each {"file", "pseudonym", "interview", "number", "timepoint", '
                        '"columns", "speakers", "sheet"}, "sheet" an Excel file\'s sheet by its name')
    x.add_argument("--skip", action="append", default=None, metavar="ENTRY:N",
                   help="leave this find of the project's list of names as written, the entry's number and its place "
                        "among that entry's finds, 3:1, given again for each one more. The dry run counts them")
    x = pj.add_parser("boards-in", parents=[common, writes],
                      help="a shared copy coming back: its boards added to the same participants in the project it "
                           "was sent from, each the next board, not current")
    x.add_argument("file", help="the .idiograph file sent back")
    x.add_argument("--from-name", dest="from_name", default=None,
                   help="whose copy it is, so each board's name says so: Curt's board, 30 Oct. Left out, the name "
                        "the file carries, its sender's Your name in Settings, when it has one")
    x.add_argument("--participant", action="append", default=None,
                   help="this participant's boards alone, by label or pseudonym, given again for each one more")
    x.add_argument("--board", action="append", default=None,
                   help="this board of the copy alone, by its name there, given again for each one more. A board "
                        "that is your own as you sent it, its cards where you sent them, is left out unless named here")
    x.add_argument("--board-of", dest="board_of", nargs="+", action="append", default=None,
                   metavar="WORDS",
                   help="one participant's board alone, as Open a shared copy's card ticks it: the participant, the "
                        "board's name in the copy and, in a project of two or more timepoints, the timepoint, T2 or "
                        "its label, for that timepoint's board alone. Given again for each one more")
    x = pj.add_parser("set", parents=[common, writes],
                      help="the project's name, research question, PET labels or timecodes saved as Project settings "
                           "saves them")
    x.add_argument("--name", default=None, help="the project's name")
    x.add_argument("--question", default=None, help="the project's research question, empty for none")
    x.add_argument("--pet-labels", dest="pet_labels", choices=themes.PET_LABELS, default=None,
                   help="how the exports label its PETs: letters, A, A1, A1.1, or numbers, PET 1, PET 1a, 1a.1")
    x.add_argument("--timecodes", dest="timecodes", choices=wb_mod.TIMECODES, default=None,
                   help="how every timecode of the project is written, at an hour and a quarter: 75:12, the hours "
                        "folded into the minutes, 1:15:12, the hours once past the hour, or 01:15:12, the hours always")
    x.add_argument("--method", choices=i18n.METHODS, default=None,
                   help="the project's method, fixed when it was made: its own changes nothing, the other is refused")
    pj.add_parser("show", parents=[common], help="the project's settings as Project settings shows them, its method "
                                                  "among them")
    x = pj.add_parser("remove", parents=[common, writes],
                      help="the project taken out of Idiograph's list, as Remove from Idiograph on its menu takes it, "
                           "its folder and files left as they are")
    x.add_argument("--trash", action="store_true",
                   help="move the project's folder to the system's Trash as well, never a delete, which waits for his "
                        "yes in the app")
    x = pj.add_parser("history", parents=[common],
                      help="the project's own History, newest first: its settings, timepoints and statement length, the "
                           "GETs settings, and each participant renamed or marked complete, who asked and what changed")
    x.add_argument("--limit", type=int, default=None, help="the newest records alone, this many")
    x = pj.add_parser("new", parents=[common, writes],
                      help="a folder made a new project with its first participants, as New project on Home makes one")
    x.add_argument("folder", help="the folder, there already, that becomes the project")
    x.add_argument("--name", default=None, help="the project's name, the folder's own when left out")
    x.add_argument("--question", default=None, help="the project's research question")
    x.add_argument("--method", choices=i18n.METHODS, default=None,
                   help="the project's method, ipa, Interpretative Phenomenological Analysis, the default, or ta, "
                        "thematic analysis, fixed once the project is made")
    x.add_argument("--transcript", action="append", default=None,
                   help="a transcript file, a participant's interview, given again for each one more")
    x.add_argument("--pseudonym", action="append", default=None,
                   help="the pseudonym of each --transcript, one capitalised word, in the same order")
    x.add_argument("--interview", action="append", default=None,
                   help="the interview's name of each --transcript, in the same order, guessed from the file's name "
                        "when left out")
    x.add_argument("--sheet", action="append", default=None,
                   help="for an Excel --transcript, the sheet to read by its name, in the same order, \"\" for the first "
                        "with anything in it")
    x.add_argument("--columns", action="append", default=None,
                   help="for a table --transcript, each column's role in the file's order with commas, Speaker, Time, "
                        "Transcript, Exploratory notes, Experiential statements, Quote or Leave out, in the same order, "
                        "\"\" for the guess. A Quote column's lines pair with the statements on the same row by order")
    x.add_argument("--speakers", default=None, help="each speaker's role, Name=Role with commas, each Interviewer, "
                                                    "Participant or Other speaker, the guess when left out")
    tm = sub.add_parser("team", parents=[common], help="Working together: the project shared with others, its "
                                                       "people, invites and who works on each "
                                                       "participant").add_subparsers(dest="act", required=True)
    tm.add_parser("show", parents=[common], help="Working together as Project settings shows it, off or its route, "
                                                 "people and who works on each participant")
    x = tm.add_parser("on", parents=[common, writes], help="Working together turned on, as its tick in Project settings "
                                                           "does, this computer's keys and the team made the first time")
    x.add_argument("--name", default=None, help="your name, as the others will see it, the first time")
    x.add_argument("--route", choices=("relay", "folder"), default="relay",
                   help="what it sends through, the relay or a shared folder")
    x.add_argument("--folder", default=None, help="the shared folder, for --route folder")
    x.add_argument("--off", action="store_true", help="turn it off in place of on: nothing more sent or taken in")
    x.add_argument("--code-stdin", dest="code_stdin", action="store_true",
                   help="read the relay code from the standard input, its first line, to make the project on the relay")
    x.add_argument("--relay-url", dest="relay_url", default=None,
                   help="a relay the team runs itself, its address ending /relay/v1, in place of idiograph.app's")
    x = tm.add_parser("set", parents=[common, writes],
                      help="the route, the shared folder, whether recordings go, and by the lead who works on each")
    x.add_argument("--route", choices=("relay", "folder"), default=None, help="what it sends through")
    x.add_argument("--folder", default=None, help="the shared folder")
    x.add_argument("--recordings", choices=("on", "off"), default=None, help="whether the recordings go too")
    x.add_argument("--owner", action="append", default=None, metavar="PARTICIPANT=NAME",
                   help="who works on a participant, given again for each one more")
    x.add_argument("--gets-owner", dest="gets_owner", default=None, help="who works on the GETs board")
    x.add_argument("--code-stdin", dest="code_stdin", action="store_true",
                   help="read the relay code from the standard input, its first line, to make the project on the relay")
    x = tm.add_parser("invite", parents=[common, writes],
                      help="an invite, a link and twelve words, for someone new, working once for seven days")
    x.add_argument("--own", action="store_true", help="for another computer of yours in place of someone new")
    x = tm.add_parser("answers", parents=[common], help="whether an invite has been answered, with the six digits")
    x.add_argument("--invite", required=True, help="the invite's id, as team invite gave it")
    x = tm.add_parser("admit", parents=[common, writes],
                      help="They match: the one who answered joins. With --differ, They differ: the answer thrown away")
    x.add_argument("--invite", required=True, help="the invite's id, as team invite gave it")
    x.add_argument("--differ", action="store_true", help="the six digits differed: throw the answer away")
    x = tm.add_parser("join", parents=[common, writes], help="this project joins another's team from its invite")
    x.add_argument("words", help="the invite's link, or its twelve words in quotation marks")
    x.add_argument("--name", default=None, help="your name, as the others will see it")
    x.add_argument("--relay-url", dest="relay_url", default=None,
                   help="the team's own relay's address, when its link does not carry it")
    x = tm.add_parser("joined", parents=[common, writes], help="the lead's They match taken in, once it has come")
    x.add_argument("--invite", required=True, help="the invite's id, as team join gave it")
    x = tm.add_parser("remove", parents=[common, writes],
                      help="the lead removes someone, or one computer, and the project's key changes for everyone left")
    x.add_argument("member", nargs="?", default=None, help="the one to remove, by name")
    x.add_argument("--computer", default=None, help="one computer in place of a person, a lost one, by its id from "
                                                    "team show")
    x = tm.add_parser("lead", parents=[common, writes],
                      help="Make lead: the lead hands the list of people to another member")
    x.add_argument("member", help="the new lead, by name")
    tm.add_parser("take", parents=[common, writes], help="what has come for the list of people taken in: a newer "
                                                         "list from the lead, a member's computer added or removed")
    tm.add_parser("send", parents=[common, writes], help="Send now: what came taken in, and your changes to the "
                                                         "participants you work on sent at once")
    x = tm.add_parser("board-send", parents=[common, writes],
                      help="his own board of a participant someone else works on, sent to them for their answer")
    x.add_argument("case", help="the participant, by their pseudonym")
    x.add_argument("--board", default=None, help="the board, by its name, the one on the canvas when left out")
    x.add_argument("--timepoint", default=None, help="the timepoint, in a project of two or more")
    tm.add_parser("board-take", parents=[common, writes],
                  help="the boards teammates sent, kept waiting for his answer, and the answers to his, taken in")
    x = tm.add_parser("board-answer", parents=[common, writes],
                      help="Add a board a teammate sent as the next board, or --decline it, the answer going back")
    x.add_argument("--ref", default=None, help="the board's ref, as team boards lists it")
    x.add_argument("--case", default=None, help="the participant whose newest board waits, in place of --ref")
    x.add_argument("--decline", action="store_true", help="decline it: nothing is written to the participant")
    x.add_argument("--reason", default=None, help="a line saying why, which goes back with the answer")
    x = tm.add_parser("boards", parents=[common], help="the boards sent and come in, each with its answer")
    x.add_argument("--case", default=None, help="a participant, to say whether his board of it can go")
    pt = sub.add_parser("participant", parents=[common], help="a participant renamed, their statements marked "
                                                              "complete, exported as the statements CSV, or their "
                                                              "picture, label and pen portrait set or "
                                                              "shown").add_subparsers(dest="act", required=True)
    x = pt.add_parser("rename", parents=[common, writes],
                      help="a participant renamed, as Rename on their menu on the project's page renames them")
    x.add_argument("case", help="the participant, by their pseudonym")
    x.add_argument("name", help="the new pseudonym, one capitalised word")
    x.add_argument("--folder", action="store_true",
                   help="the participant's folder and the files named after them take the new name too")
    x = pt.add_parser("complete", parents=[common, writes],
                      help="a participant's experiential statements marked complete, as Mark complete does, or reopened")
    x.add_argument("case", help="the participant, by their pseudonym")
    x.add_argument("--reopen", action="store_true", help="reopen the statements in place of marking them complete")
    x.add_argument("--timepoint", default=None, help="in a project of two or more timepoints, the timepoint, by its "
                                                     "number or its label, T1 when left out")
    x = pt.add_parser("set", parents=[common, writes],
                      help="a participant's picture, label and pen portrait, as their row on the project's page sets "
                           "them, each left out kept as it is")
    x.add_argument("case", help="the participant, by their pseudonym")
    x.add_argument("--label", default=None, help="a few words, \"\" clearing it")
    x.add_argument("--portrait", default=None, help="the pen portrait, one short paragraph, \"\" clearing it")
    x.add_argument("--picture", default=None, help="one of the app's drawn set, set:peep01 to set:peep40")
    x.add_argument("--picture-file", default=None, help="an image file of his, PNG, JPEG or SVG, kept in the "
                                                         "project's pictures folder, made square and small")
    x.add_argument("--no-picture", action="store_true", help="take the picture off, the initial on their colour shown")
    x.add_argument("--value", action="append", default=None, metavar="CATEGORY=VALUE",
                   help="one of their demographics, \"Gender=Female\", a list's value or free words with commas "
                        "between them, nothing after the = clearing it, given again for each category")
    x = pt.add_parser("show", parents=[common],
                      help="a participant's picture, label and pen portrait, or with none named every participant's")
    x.add_argument("case", nargs="?", default=None, help="the participant, by their pseudonym, every one when left out")
    # the project's demographics (demobuild, 12 November 2026)
    dm = sub.add_parser("demographics", parents=[common],
                        help="the participants' demographics: the project's categories, each a list or free words, "
                             "and each participant's values").add_subparsers(dest="act", required=True)
    dm.add_parser("show", parents=[common], help="every category with its values and colours, and each participant's "
                                                 "values")
    x = dm.add_parser("apply", parents=[common, writes], help="change the categories and their values with their "
                                                               "operations, all or nothing")
    x.add_argument("--ops", required=True, help='a JSON file, a list of operations or {"operations": [...]}: '
                                                '{"op": "add", "name": "Gender", "kind": "list", "values": ["Female", '
                                                '"Male"]}, rename, kind, show, move, remove, export, table, and on a '
                                                'value value_add, value_rename, value_colour, value_move, value_remove '
                                                'and value_to')
    dm.add_parser("move-tags", parents=[common, writes], help="Trajectories' old tags moved into each participant's "
                                                              "values in the Tags category now, each word keeping its "
                                                              "colour")
    x = pt.add_parser("export", parents=[common, writes],
                      help="a participant's statements as the statements CSV, as Export in Settings writes it")
    x.add_argument("case", help="the participant, by their pseudonym")
    x.add_argument("--notes", action="store_true",
                   help="the interviewer notes too, in a markdown file of their own beside the CSV")
    # Working together's comments and review (wtreview, 8 November 2026), in the one `team` group
    review_mod.arguments(sub, common, writes)


def perform(args) -> tuple[dict, list[str]]:
    """One of Idiograph's commands on its parsed arguments, as the family's `cli.perform` hands it (the family
    codebase's fourth build, 22 October 2026, from it): its answer and its plain lines, or Refused. The
    server's settings it reads by are put back after it however it ends."""
    if (args.command, getattr(args, "act", None)) == ("agents", "log"):
        # the agent log, the app's own and no project's (agent_log.py)
        return cmd_agents_log(args)
    if (args.command, getattr(args, "act", None)) in (("project", "open-copy"), ("project", "new")):
        # a sent file, or a folder made a new project, needs no project of Distil's, and adds one to the
        # settings `--config` names
        kept = (srv.CONFIG_PATH, srv.STATE_MEMORY)
        try:
            if getattr(args, "config", None):
                srv.CONFIG_PATH = Path(args.config).expanduser().resolve()
            srv.STATE_MEMORY = {"recent": []}
            return cmd_project_open_copy(args) if args.act == "open-copy" else cmd_project_new(args)
        finally:
            srv.CONFIG_PATH, srv.STATE_MEMORY = kept
    kept = (srv.CONFIG_PATH, srv.ROOT_OVERRIDE, srv.STATE_MEMORY)
    try:
        projects, closed = open_projects(args)
        if args.command == "search":
            # every project it reads when none is named, each hit naming its project
            return cmd_search(projects, closed, args)
        if (args.command, getattr(args, "act", None)) == ("project", "boards-in"):
            # with no project named, the one the copy coming back belongs to
            return cmd_project_boards_in(projects, args)
        command = COMMANDS[(args.command, getattr(args, "act", None))]
        if len(projects) == 1 and not closed:
            return run_in_scope(command, projects[0], args)
        if args.command in ("import", "qdpx"):
            return command(import_project(projects, args.file), args)
        if args.command in ("cases", "validate") or (args.command, getattr(args, "act", None)) == ("hold", None):
            return each_project(projects, closed, command, args)
        if (args.command, getattr(args, "act", None)) == ("hold", "show"):
            # an action's id is its project's, so the one project that holds it
            return holds.show_in(projects, args)
        if getattr(args, "case", None) or getattr(args, "lpets", None):
            return run_in_scope(command, project_for(projects, getattr(args, "case", None) or args.lpets), args)
        if len(projects) == 1:
            return run_in_scope(command, projects[0], args)
        names = " or ".join(p.info["name"] for p in projects)
        raise cli.Refused(i18n.t("cli.said.this_reads_one_project", names=names, name_one=_w("NAME_ONE")))
    finally:
        srv.CONFIG_PATH, srv.ROOT_OVERRIDE, srv.STATE_MEMORY = kept


# the line the command line's parser describes itself with at the top of `idiograph`
ABOUT = ("Idiograph's command line, for an AI agent in a conversation: "
         "cases, statements, board, gets, turn, transcript, import, validate and search across the participants. "
         "Sift and Trace have their own, sift and trace. See docs/agents.md.")

# What only the app's own window does, which an agent may ask for by its words, each refused in one line saying so
# and kept in the agent log as page-only (agentlog, 3 November 2026)
PAGE_ONLY = {
    ("hold", "approve"): lambda: i18n.t("cli.page_only.hold"),
    ("hold", "decline"): lambda: i18n.t("cli.page_only.hold"),
}

def log_where(project, root, demo, config) -> tuple[str, int]:
    """The project a refusal was asked of before one opened, for the agent log (agent_log.py): its name and 0 where
    agents may read it, "" and 1 where they may not, never its name, and "" and 0 where none is known. Only a named
    project, a run of one folder, the demo, or the one project the app holds."""
    kept = (srv.CONFIG_PATH, srv.STATE_MEMORY)
    try:
        if config:
            srv.CONFIG_PATH = Path(config).expanduser().resolve()
        srv.STATE_MEMORY = {"recent": []}
        if demo:
            return routes.read_project(srv.demo_dir_of(demo))["name"], 0
        roots = [Path(root).expanduser().resolve()] if root else [r for r in srv.project_roots() if Path(r).is_dir()]
        if project:
            said = " ".join(str(project).split()).lower()
            roots = [r for r in roots if routes.read_project(r)["name"].lower() == said]
        if len(roots) != 1 or not Path(roots[0]).is_dir():
            return "", 0
        info = routes.read_project(roots[0])
        return (info["name"], 0) if info["agents"]["allowed"] else ("", 1)
    finally:
        srv.CONFIG_PATH, srv.STATE_MEMORY = kept


cli.register_own("idiograph", arguments, perform, ABOUT,
                 hits={screen: case_hit for screen in ("statements", "pets", "gets", "project")}, page_only=PAGE_ONLY,
                 where=log_where)
