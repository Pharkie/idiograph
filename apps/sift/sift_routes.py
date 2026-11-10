"""Sift's routes on the family's server (22 October 2026, the family codebase's third build, from
server.py): its projects, `/api/sift-review`, a screening, `/api/sift`, a review's searches, `/api/sift-search`,
his databases, `/api/databases`, the sync to Zotero, `/api/zotero`, a record's PDF for the pane, `/sift/pdf`,
its cards on the home screen, its Search, its settings, the file its keys go to and the work that holds a
quit, each registered with the server by `register`, which the server's start imports this module for
(`boot.load`).

Sift, a systematic review's searches and its screening (see `sift.py` and `sift_search.py`). A review is one
folder, kept in the list of reviews, `sift_reviews` in the app's state, newest first, which the home
screen's Sift section lists. A route reads or writes a review's files only when the list holds the review,
a run's screening by the review above it.

The server's names are read from it as each request comes, `srv.PICK_FOLDER` and the rest, so a check that
stands in a dialog or a platform of its own is heard here too.
"""
from __future__ import annotations

import base64
import sift_words
import binascii
import json
import re
import threading
import time
from datetime import datetime
from pathlib import Path

import app_identity
import app_search
import server as srv
import sift as sift_mod
import sift_ai
import sift_find
import sift_oa
import sift_second
import sift_search as search_mod
import sift_zotero as zotero_mod
from errors import WorkbookError


# -------------------------------------------------------------------- sift

# Sift, a systematic review's searches and its screening (see `sift.py` and `sift_search.py`). A
# review is one folder, one holding search_plan.json with its runs under runs/, or one holding
# screening.csv alone, a screening with no searches. New review makes one and Open review takes one,
# writing nothing into it, and both keep it in the list of reviews, `sift_reviews` in state.json,
# newest first, which the home screen's Sift section lists, each entry with `run`, the run whose
# screening he opened last, which its Screening step opens. The two lists before it, `sift` and
# `sift_searches`, are read into it until it is first written, and go then. A route reads or writes a
# review's files only when the list holds the review, a run's screening by the review above it. An
# entry's `second` holds the project's second screener settings (see `sift_second.py`), saved under
# Sift in Settings as its name and question are, and passed to each act that needs them.
REVIEWS_KEPT = 16


# This module's words for a person, read in the run's language when said: inside the module through `_w`,
# from others and the checks as the module's names (`__getattr__`), `sift_routes.NOT_OPENED`
SAID = {
    "NEW_REVIEW_PROMPT": lambda: sift_words.t("sift_server.routes.new_prompt"),
    "OPEN_REVIEW_PROMPT": lambda: sift_words.t("sift_server.routes.open_prompt"),
    "NOT_OPENED": lambda: sift_words.t("sift_server.routes.not_opened"),
    "REVIEW_NOT_OPENED": lambda: sift_words.t("sift_server.routes.review_not_opened"),
    "NOT_A_REVIEW": lambda: sift_words.t("sift_server.routes.not_a_review"),
    "SEVERAL_REVIEWS": lambda: sift_words.t("sift_server.routes.several"),
    "NO_SEARCHES": lambda: sift_words.t("sift_server.routes.no_searches"),
    "REVIEW_NOT_MADE": lambda: sift_words.t("sift_server.routes.not_made"),
}


def _w(name: str) -> str:
    return SAID[name]()


def __getattr__(name: str) -> str:
    """This module's words other modules and the checks name, read in the run's language."""
    if name in SAID:
        return SAID[name]()
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


def review_of(folder: Path) -> Path | None:
    """The review a folder is or sits in by Sift's own layout: the folder holding search_plan.json,
    the review above its runs folder, or the review above a run folder, else None. Only reads."""
    folder = Path(folder)
    runs = search_mod.RUNS_DIR
    for review, fits in ((folder, True), (folder.parent, folder.name == runs),
                         (folder.parent.parent, folder.parent.name == runs)):
        if fits and search_mod.plan_path(review).is_file():
            return review
    return None


def has_searches(folder: Path) -> bool:
    """Whether a review has searches: it holds search_plan.json, or it holds no screening.csv of its
    own and so is one whose searches were opened before it had a plan."""
    return search_mod.plan_path(folder).is_file() or not sift_mod.is_screening(folder)


def run_folders(folder: Path) -> list[Path]:
    """A review's run folders, newest first in the order they were made, as `sift_search.runs` lists
    them, a later run of a day after the day's first."""
    try:
        return search_mod.run_dirs(folder)
    except OSError:
        return []


def newest_screening(folder: Path) -> Path | None:
    """A review's newest screening: its newest run holding one with records, else its newest run
    holding one at all, else its own screening.csv, else None. A run that brought nothing, its CSV a
    header alone, never stands before an earlier run with records. Only reads."""
    if has_searches(folder):
        held = [run for run in run_folders(folder) if sift_mod.is_screening(run)]
        for run in held:
            if sift_mod.has_records(run):
                return run
        if held:
            return held[0]
    return folder if sift_mod.is_screening(folder) else None


def kept_run(folder: Path, entry: dict | None) -> Path | None:
    """The run whose screening he opened last, `run` in the review's entry in the list of reviews,
    while it still holds a screening, else None. Only reads."""
    name = str((entry or {}).get("run") or "")
    if not name or not has_searches(folder):
        return None
    try:
        run = search_mod.run_path(folder, name)
    except WorkbookError:
        return None
    return run if sift_mod.is_screening(run) else None


def screening_of(folder: Path, entry: dict | None = None) -> Path | None:
    """The screening a review's Screening step opens: the run he opened last, kept in the list of
    reviews and never in the review's folder, until he opens another, so a newer run never takes it
    over by itself, or for a review he has never opened a run of its newest screening. Only reads."""
    return kept_run(folder, entry) or newest_screening(folder)


def reviews_old(held: dict) -> list[dict]:
    """The list of reviews from the two lists before it: each screening's review, a run folder by the
    review above it and any other by its own folder, and each folder whose searches were opened,
    newest first and each folder once, so every folder he opened stays."""
    found = []
    for key in ("sift", "sift_searches"):
        rows = held.get(key) if isinstance(held.get(key), list) else []
        for e in rows:
            if not isinstance(e, dict) or not e.get("folder"):
                continue
            folder = srv.abs_path(str(e["folder"]))
            if key == "sift":
                folder = review_of(folder) or folder
            try:
                opened = int(e.get("opened") or 0)
            except (TypeError, ValueError):
                opened = 0
            found.append({"folder": srv.rel_path(folder), "opened": opened})
    found.sort(key=lambda e: e["opened"], reverse=True)
    out: list[dict] = []
    for e in found:
        if not any(srv.same_folder(srv.abs_path(o["folder"]), srv.abs_path(e["folder"])) for o in out):
            out.append(e)
    return out[:REVIEWS_KEPT]


def reviews_kept() -> list[dict]:
    """The reviews in the list, newest first, each `{"folder", "opened"}` and `name` when he gave one,
    or until the list is first written the two lists before it, read into one."""
    held = srv.state()
    rows = held.get("sift_reviews")
    if not isinstance(rows, list):
        return reviews_old(held)
    return [e for e in rows if isinstance(e, dict) and e.get("folder")]


def kept_review(folder: Path) -> dict | None:
    """The list's entry for a review's folder, or None."""
    return next((e for e in reviews_kept() if srv.same_folder(srv.abs_path(e["folder"]), folder)), None)


def remember_review(folder: Path, name: str | None = None, run: str | None = None) -> None:
    """A review to the head of the list, with the name he gave, `name`, or the one it had when that is
    None, and `run`, the run whose screening he opened, or the one it had when that is None, and the
    two lists before it gone. The cases' entries stay as they were."""
    data = srv.state()
    kept = reviews_kept()
    was = next((e for e in kept if srv.same_folder(srv.abs_path(e["folder"]), folder)), None)
    entry = {"folder": srv.rel_path(folder), "opened": int(time.time())}
    given = (was or {}).get("name") if name is None else name
    if given:
        entry["name"] = given
    opened = (was or {}).get("run") if run is None else run
    if opened:
        entry["run"] = opened
    # the question he gave under Sift in Settings, kept as the name is, and the second screener's settings
    if isinstance((was or {}).get("question"), str):
        entry["question"] = was["question"]
    if isinstance((was or {}).get("second"), dict):
        entry["second"] = was["second"]
    data["sift_reviews"] = ([entry] + [e for e in kept if e is not was])[:REVIEWS_KEPT]
    data.pop("sift", None)
    data.pop("sift_searches", None)
    srv.save_state(data)


def review_name(folder: Path, entry: dict | None = None) -> str:
    """A review's name: the one he gave on opening it, else its plan's own, else its folder's."""
    return str((entry or {}).get("name") or "") or search_mod.own_name(folder) or Path(folder).name


def review_question(folder: Path, entry: dict | None = None) -> str:
    """A review's research question: the one he gave in Settings, kept in the list as his name for it
    is, even an empty one, else its plan's own, New project's (12 October)."""
    if isinstance((entry or {}).get("question"), str):
        return entry["question"]
    return search_mod.own_question(folder)


def edit_review(folder: Path, name, question) -> None:
    """A review's name and question as he gave them under Sift in Settings, kept in its entry in the
    list in place, its order and its run as they were, and never in its folder. A name or question
    the same as its plan's own leaves the entry without one, so the plan's own shows."""
    data = srv.state()
    kept = reviews_kept()
    entry = next((e for e in kept if srv.same_folder(srv.abs_path(e["folder"]), folder)), None)
    if entry is None:
        raise srv.OutsideRoot(_w("REVIEW_NOT_OPENED"))
    entry = dict(entry)
    if name is not None:
        given = sift_mod.one_line(name)[:120]
        own = search_mod.own_name(folder) or Path(folder).name
        if given and given != own:
            entry["name"] = given
        else:
            entry.pop("name", None)
    if question is not None:
        asked = sift_mod.one_line(question)[:600]
        if asked != search_mod.own_question(folder):
            entry["question"] = asked
        else:
            entry.pop("question", None)
    data["sift_reviews"] = [entry if srv.same_folder(srv.abs_path(e["folder"]), folder) else e for e in kept]
    data.pop("sift", None)
    data.pop("sift_searches", None)
    srv.save_state(data)


def save_second(folder: Path, raw) -> dict:
    """A project's second screener settings as he gave them under Sift in Settings, cleaned and kept
    in its entry in the list in place, its order, name, question and run as they were, and never in
    its folder. Answers the settings kept."""
    data = srv.state()
    kept = reviews_kept()
    entry = next((e for e in kept if srv.same_folder(srv.abs_path(e["folder"]), folder)), None)
    if entry is None:
        raise srv.OutsideRoot(_w("REVIEW_NOT_OPENED"))
    entry = dict(entry, second=sift_second.settings_of(raw))
    data["sift_reviews"] = [entry if srv.same_folder(srv.abs_path(e["folder"]), folder) else e for e in kept]
    data.pop("sift", None)
    data.pop("sift_searches", None)
    srv.save_state(data)
    return entry["second"]


def second_of(screening: Path) -> dict:
    """The second screener settings of the project a screening belongs to, the defaults when it has
    none. Only reads."""
    review = review_holding(screening)
    entry = kept_review(review) if review is not None else None
    return sift_second.settings_of((entry or {}).get("second"))


def eligibility_of(screening: Path) -> list[str]:
    """The eligibility the plan version a run ran sets beyond its reasons, its years and document
    types, each a line for the second screener's workbook, or none. Only reads."""
    review = review_holding(screening)
    if review is None or not is_run(screening, review):
        return []
    try:
        meta = json.loads((screening / search_mod.RUN_FILE).read_text(encoding="utf-8"))
        v = search_mod.version_of(search_mod.read_file(review), meta.get("version")) if isinstance(meta, dict) else None
    except (OSError, ValueError, UnicodeDecodeError, WorkbookError):
        return []
    plan = (v or {}).get("plan") if isinstance(v, dict) else None
    if not isinstance(plan, dict):
        return []
    out = []
    years = plan.get("years") if isinstance(plan.get("years"), dict) else {}
    if years.get("from") or years.get("to"):
        out.append(sift_words.t("sift_server.routes.years_to", first=years.get('from') or sift_words.t("sift_server.routes.years_any"),
                          last=years.get('to') or sift_words.t("sift_server.routes.years_now")))
    types = [search_mod.TYPE_WORDS.get(t, str(t)) for t in plan.get("types") or [] if isinstance(t, str)]
    if types:
        out.append(sift_words.t("sift_server.routes.document_types", types=", ".join(types)))
    return out


def forget_review(folder: Path) -> str:
    """A review taken out of the list, as Distil's Remove from Idiograph takes a project out, its
    folder and every file in it left as they are. Answers the name it had."""
    data = srv.state()
    kept = reviews_kept()
    entry = next((e for e in kept if srv.same_folder(srv.abs_path(e["folder"]), folder)), None)
    if entry is None:
        raise srv.OutsideRoot(_w("REVIEW_NOT_OPENED"))
    name = review_name(folder, entry) if folder.is_dir() else str(entry.get("name") or folder.name)
    data["sift_reviews"] = [e for e in kept if e is not entry]
    data.pop("sift", None)
    data.pop("sift_searches", None)
    srv.save_state(data)
    return name


def review_folder(value) -> Path:
    """A review's folder from a request, refused unless the list of reviews holds it, so no request
    reads or writes a folder he never chose."""
    folder = srv.there_folder(value)
    if kept_review(folder) is None:
        raise srv.OutsideRoot(_w("REVIEW_NOT_OPENED"))
    return folder


def review_holding(screening: Path) -> Path | None:
    """The review in the list a screening belongs to: its own folder, or the review above a run."""
    if kept_review(screening) is not None:
        return screening
    above = screening.parent.parent
    if screening.parent.name == search_mod.RUNS_DIR and kept_review(above) is not None:
        return above
    return None


def sift_folder(value) -> Path:
    """A screening's folder from a request, refused unless it holds screening.csv and the list of
    reviews holds its review, so no request reads a folder he never chose."""
    folder = srv.there_folder(value)
    if not sift_mod.is_screening(folder):
        raise WorkbookError(sift_words.t("sift_server.routes.that_folder_holds_no", csv_name=sift_mod.CSV_NAME))
    if review_holding(folder) is None:
        raise srv.OutsideRoot(_w("NOT_OPENED"))
    return folder


def is_run(screening: Path | None, folder: Path) -> bool:
    """Whether a screening is one of a review's runs, not the review's own screening.csv."""
    return (screening is not None and screening.parent.name == search_mod.RUNS_DIR
            and not srv.same_folder(screening, folder))


def review_view(folder: Path, screening: Path | None = None) -> dict:
    """A review as its steps draw it: its folder as the page names it back, its name, whether it has
    searches, the screening its Screening step opens and `opens`, that run's folder name, or None for
    the review's own screening or none, `run`, the folder name of the run whose screening `screening`
    is, or None, and `label`, that run named in words with its mark when its version was a draft.
    Only reads."""
    entry = kept_review(folder)
    shown = screening_of(folder, entry)
    run = screening.name if is_run(screening, folder) else None
    return {"folder": srv.rel_path(folder), "name": review_name(folder, entry), "question": review_question(folder, entry),
            "searches": has_searches(folder), "screening": srv.rel_path(shown) if shown else None,
            "opens": shown.name if is_run(shown, folder) else None, "run": run,
            "label": search_mod.run_title(screening) if run else None,
            "second": sift_second.settings_of((entry or {}).get("second"))}


def review_stands(folder: Path, entry: dict | None = None) -> dict:
    """Where a review stands, for its row's line: with no searches its screening's counts at each
    stage, else its newest version and whether it is a draft, and the run its Screening step opens,
    its folder name and its name in words with that run's counts, never a newer run that brought
    nothing, or with no run holding a screening its newest run. One line, `said`, when it cannot be
    read. Only reads."""
    if not has_searches(folder):
        return dict({"searches": False}, **sift_mod.summary(folder))
    try:
        last = search_mod.newest(search_mod.read_file(folder))
    except WorkbookError as exc:
        return {"searches": True, "said": str(exc)}
    runs = run_folders(folder)
    shown = screening_of(folder, entry)
    run = None
    if is_run(shown, folder):
        run = dict({"date": shown.name, "label": search_mod.run_said(shown.name, folder), "screening": True},
                   **sift_mod.summary(shown))
    elif runs:
        run = {"date": runs[0].name, "label": search_mod.run_said(runs[0].name, folder),
               "screening": sift_mod.is_screening(runs[0])}
    return {"searches": True, "version": last["version"] if last else None,
            "draft": bool(last and not last.get("registered")), "run": run}


def review_rows() -> list[dict]:
    """The home screen's Sift cards: each review in the list, its folder as the page names it back,
    its name, the folder above it, whether it is there, where it stands, and `screening`, the
    screening its Screening step opens as the page names it back, or None, whose AI proposals
    Settings shows under Sift. Only reads."""
    out = []
    for e in reviews_kept():
        folder = srv.abs_path(e["folder"])
        there = folder.is_dir()
        row = {"folder": e["folder"], "name": review_name(folder, e) if there else (e.get("name") or folder.name),
               "question": review_question(folder, e) if there else str(e.get("question") or ""),
               "where": srv.display_path(srv.rel_path(folder.parent)), "there": there, "opened": e.get("opened"),
               "screening": None, "second": sift_second.settings_of(e.get("second"))}
        if there:
            row.update(review_stands(folder, e))
            shown = screening_of(folder, e)
            row["screening"] = srv.rel_path(shown) if shown else None
        out.append(row)
    return out


class SeveralReviews(WorkbookError):
    """A folder chosen in Open review that holds more than one review folder directly inside it,
    `found`, each to be chosen by its folder's name."""

    def __init__(self, found: list[Path]):
        super().__init__(_w("SEVERAL_REVIEWS"))
        self.found = found


def reviews_inside(folder: Path) -> list[Path]:
    """The review folders directly inside a folder, by name: each one holding search_plan.json, or
    screening.csv alone. Only reads."""
    try:
        subs = sorted((p for p in Path(folder).iterdir() if p.is_dir() and not p.name.startswith(".")),
                      key=lambda p: p.name.lower())
    except OSError:
        return []
    return [p for p in subs if search_mod.plan_path(p).is_file() or sift_mod.is_screening(p)]


def review_to_open(value) -> Path:
    """The review a folder chosen in Open review opens: the folder holding search_plan.json, the
    review above a run folder or its runs folder, a folder holding screening.csv alone, or the one
    review folder directly inside a folder that is none of these, each read to be sure it opens. A
    folder holding several is refused with them, `SeveralReviews`, to be chosen from, and any other
    in one line saying what a review's folder holds. Writes nothing."""
    folder = srv.there_folder(value)
    review = review_of(folder)
    if review is not None:
        search_mod.read_file(review)
        return review
    if sift_mod.is_screening(folder):
        sift_mod.load(folder)
        return folder
    inside = reviews_inside(folder)
    if len(inside) == 1:
        return review_to_open(inside[0])
    if inside:
        raise SeveralReviews([p.resolve() for p in inside])
    raise WorkbookError(_w("NOT_A_REVIEW"))


def new_review_place(value) -> Path:
    """The folder New review was given, refused in one line when it holds a review or a screening or
    is part of a review. Writes nothing."""
    folder = srv.there_folder(value)
    if search_mod.plan_path(folder).is_file():
        raise WorkbookError(sift_words.t("sift_server.routes.that_folder_holds_a_sift"))
    if review_of(folder) is not None:
        raise WorkbookError(sift_words.t("sift_server.routes.that_folder_is_part_of"))
    if sift_mod.is_screening(folder):
        raise WorkbookError(sift_words.t("sift_server.routes.that_folder_holds_a_screening"))
    return folder


def make_review(target: Path, name: str, question: str) -> None:
    """A new review: its folder when it is new, and its blank plan with its name and question. A
    write that fails takes away what it made and says one line."""
    made = not target.exists()
    try:
        target.mkdir(exist_ok=True)
        search_mod.new_plan(target, name, question)
    except OSError:
        try:
            search_mod.plan_path(target).unlink(missing_ok=True)
            if made:
                target.rmdir()
        except OSError:
            pass
        raise WorkbookError(_w("REVIEW_NOT_MADE")) from None


def api_sift_review(body: dict) -> dict:
    """Sift's reviews, with `op`. `folder` takes the folder typed as `path`, or with none the Mac's
    folder dialog, whose Cancel answers `chosen` false, for New review with `mode` new or for Open
    review with `mode` open, and answers the folder and the name the card fills in, refused in one
    line as `new` or `open` would refuse it, or for a folder holding several reviews `choices`, each
    review's folder and its folder's name, with `chosen` false. `new` makes a review in `folder`, or in a new folder
    inside it named for the review when it holds anything, its `name` and `question` in a blank plan,
    and keeps it in the list. `open` keeps a review in the list, the review above a run folder for a
    run folder and the one review inside a folder holding one, with the `name` given when it is not
    its own, and writes nothing into either folder.
    `read` is a review the list holds, for its steps. Each answers the review as `review_view` says it.
    `rename` keeps the `name` and `question` he gives a review under Sift in Settings in its entry in
    the list, `second` keeps its second screener settings there, and `forget` takes a review out of the
    list, its folder and files left as they are or with `trash` moved to the system's Trash first
    (removetrash), each answering the list's cards afresh as `reviews`."""
    op = str(body.get("op") or "")
    if op == "folder":
        mode = "open" if body.get("mode") == "open" else "new"
        if str(body.get("path") or "").strip():
            chosen = body["path"]
        else:
            if srv.PLATFORM != "darwin":
                raise WorkbookError(srv.NO_DIALOG)
            chosen = srv.PICK_FOLDER(_w("OPEN_REVIEW_PROMPT") if mode == "open" else _w("NEW_REVIEW_PROMPT"))
            if chosen is None:
                return {"chosen": False}
        if mode == "open":
            try:
                folder = review_to_open(chosen)
            except SeveralReviews as exc:
                return {"chosen": False, "folder": str(srv.there_folder(chosen)),
                        "choices": [{"folder": str(p), "label": p.name} for p in exc.found]}
            return {"chosen": True, "folder": str(folder), "name": review_name(folder, kept_review(folder))}
        folder = new_review_place(chosen)
        return {"chosen": True, "folder": str(folder), "name": folder.name if srv.is_empty(folder) else ""}
    if op == "new":
        place = new_review_place(body.get("folder"))
        name = sift_mod.one_line(body.get("name"))
        if not name:
            raise WorkbookError(sift_words.t("sift_server.routes.name_the_project_first"))
        target = srv.review_target(place, name)
        with srv._lock:
            make_review(target, name, sift_mod.one_line(body.get("question")))
            remember_review(target.resolve(), "")
        return {"made": True, "review": review_view(target.resolve())}
    if op == "open":
        folder = review_to_open(body.get("folder"))
        given = sift_mod.one_line(body.get("name"))
        own = search_mod.own_name(folder) or folder.name
        with srv._lock:
            remember_review(folder, given if given != own else "")
        return {"opened": True, "review": review_view(folder)}
    if op == "read":
        return {"review": review_view(review_folder(body.get("folder")))}
    if op == "rename":
        # his name and question for a project, from Sift in Settings, kept in the list alone
        folder = review_folder(body.get("folder"))
        with srv._lock:
            edit_review(folder, body.get("name") if isinstance(body.get("name"), str) else None,
                        body.get("question") if isinstance(body.get("question"), str) else None)
        return {"review": review_view(folder), "reviews": review_rows()}
    if op == "second":
        # the project's second screener settings, from Sift in Settings, kept in the list alone
        folder = review_folder(body.get("folder"))
        with srv._lock:
            save_second(folder, body.get("second"))
        return {"review": review_view(folder), "reviews": review_rows()}
    if op == "forget":
        # Remove from Idiograph: the project out of the list, its folder and files left as they are, a
        # folder no longer there among them
        text = str(body.get("folder") or "").strip()
        if not text:
            raise WorkbookError(sift_words.t("sift_server.routes.name_the_folder_first"))
        folder = srv.abs_path(text)
        trash, where = body.get("trash") is True, ""
        if trash:
            # his tick on Remove's card (removetrash, 10 November 2026): the folder to the system's Trash first, a
            # move refused keeping the project in the list
            entry = kept_review(folder)
            if entry is None:
                raise srv.OutsideRoot(_w("REVIEW_NOT_OPENED"))
            named = review_name(folder, entry) if folder.is_dir() else str(entry.get("name") or folder.name)
            chosen = srv.trash_guard(folder, named, lambda at: srv.inside(srv.abs_path(at), folder),
                                     str(body.get("page") or ""))
            where = srv.trash_move(chosen, named)
        with srv._lock:
            name = forget_review(folder)
        srv.record_removal(name, folder, trash)
        return {"forgotten": True, "name": name, "trash": trash, "where": where, "reviews": review_rows()}
    if op == "reveal":
        # Show in Finder on the project's menu, on its card on Home and behind its name in the band (barsD)
        return srv.reveal_folder(review_folder(body.get("folder")))
    raise WorkbookError(sift_words.t("sift_server.routes.the_op_is_folder_new"))


SIFT_PDF_MAX = 200 * 1024 * 1024


def sift_ai_state(cfg: dict, folder: Path) -> dict | None:
    """What the screen draws its AI parts by, None with the app's AI switch off, when Sift shows no
    proposal and no AI control: the screening's own switch, the prompt it would send, the default
    beside it and the model the calls go to, named from the settings alone, the key never looked up."""
    if not srv.ai_on(cfg, "proposals"):
        return None
    held = sift_ai.settings(folder)
    return {"on": held["ai_proposals"], "prompt": sift_ai.prompt_of(held), "default": sift_ai.DEFAULT_PROMPT,
            "custom": bool(held["prompt"]), "model_name": srv.ai_model_words(cfg)}


def sift_ai_ready(cfg: dict, folder: Path) -> None:
    """Refused unless the app's AI switch, its AI proposals and the screening's own are all on."""
    if not srv.ai_on(cfg, "proposals"):
        raise WorkbookError(sift_ai.OFF)
    if not sift_ai.settings(folder)["ai_proposals"]:
        raise WorkbookError(sift_ai.SIFT_OFF)


def api_sift(body: dict) -> dict:
    """Sift's screening, with `op`, on a screening of a review in the list of reviews (see
    `api_sift_review`). `read` is the whole screening for the screen, with the app's AI switch, the
    screening's AI settings, `review`, its review for the steps, and `email`, the one Find open-access
    PDFs gives Unpaywall, gives a run's record with no PDF the one an earlier run holds for its paper
    (see `sift.gather_pdfs`), writes `prisma.md` afresh, gives each record without a number its number in
    sift.json and puts its review at the head of the list, a run's screening kept there as the one its
    review's Screening step opens until he opens another. `email` saves that email. `oa_plan` names
    the records with no PDF and `oa_find` looks for one record's open-access PDF, the looking done
    outside the server's lock and the PDF kept under it, never over one there (see `sift_oa.py`).
    `titles` is the records of a `stage` with their numbers and titles, for the bench under Sift in
    Settings. With the app's AI switch on, `try` is that bench, one record sent with the
    prompt as the box holds it and what came back answered, nothing written. `list` is a
    round's records, `stage` and `round`. `decide`, `note` and `undo` each add a line to the log and
    write the CSV's decision columns afresh, answering the record, the counts and the flow, a decision's
    line saying whether it matched the suggestions shown, by the app's AI switch. `stamp`
    and `counts` only read, the stamp saying whether another writer has touched the files since, and
    `export` writes the counts beside the CSV, and `included` the records accepted at full text as RIS and CSV. `reset` starts the screening again, its log moved into
    `_Archive/` and every column Sift writes emptied, or with `dry_run` says the decisions and notes it
    would clear. `pdf` keeps a dropped PDF, `data` in base64, as
    `pdfs/<rec_id>.pdf`, one already there only with `replace`. `field` writes one of his own fields
    on a record, `field` and `value`, a line in the log, answering as the acts do. `view` keeps the
    table's view, its columns, its filters, its find boxes' words and the filters' sidebar's width,
    `sidebar`, in sift.json. `cited_plan` names the records with a DOI that Find citation counts asks
    about, and `cited` asks OpenAlex for the next fifty from `at` and writes their counts of citations
    into Sift's own columns (see `sift_search.find_citations`). `fill_plan` names the records with a DOI
    that Fill from OpenAlex goes through, with how many lack one of Sift's own columns, and `fill` asks
    OpenAlex and Crossref about the next fifty from `at`, those that lack one, and writes what they say
    into Sift's own columns and `screening.references.json`, Cited by among them (see
    `sift_search.fill_columns`). `study` is his link of reports of one study, `act` link, `rec_id` and
    `with`, or unlink and `rec_id`, a line in the log, answering as the acts do with `records`, each
    record it moved (see `sift.study`). `excerpt` is one of his key excerpts, `act` add, `rec_id`, `stage`
    and `pieces`, or remove, `rec_id`, `at` and `text`, a line in the log that Undo takes back (see
    `sift.excerpt`). `column` adds,
    changes or removes a column of his, `act`, `key`, `name`, `type` and `options`, each answering the
    table's settings, and `form` is Extract and appraise's form, its fields and their order, its records
    and its export (see `sift_form_op`). `second` is the second screener's side (see `sift_second.py`), `act` draw, a
    further draw at `stage`, workbook, their workbook, differences, the differences workbook, take, a
    returned workbook, `data` in base64 and `name`, outcome, a difference's `outcome` with its
    `decision`, each answering the side afresh as `second`, as `read`, `decide` and `undo` do, the
    project's settings passed to each. `ai` reads the
    screening's own switch and prompt for Settings, under Sift, whatever the app's switch says. With
    the app's AI switch on, `settings` saves them, and with both switches on `plan` names the records
    a proposal for the rows shown would ask about, those of `ids` when the screen names the table's
    rows, and `propose` asks the app's AI for one record's
    proposal, written into Sift's own columns."""
    op = str(body.get("op") or "read")
    folder = sift_folder(body.get("folder"))
    if op == "read":
        with srv._lock:
            # a PDF an earlier run of the review holds for a record's paper, added there since, reaches it
            sift_mod.gather_pdfs(folder)
            sift_mod.refresh_prisma(folder)
            sift_mod.keep_numbers(folder)
        answer = sift_mod.screen(folder)
        cfg = srv.config()
        review = review_holding(folder) or folder
        with srv._lock:
            # a run's screening opened is the one his Screening step opens from now on
            remember_review(review, run=folder.name if is_run(folder, review) else None)
        return dict(answer, folder=srv.rel_path(folder), config={"ai_suggest": srv.ai_on(cfg, "proposals")},
                    ai=sift_ai_state(cfg, folder), review=review_view(review, folder),
                    email=str(cfg.get("sift_email") or ""), second=sift_second.view(folder, second_of(folder)))
    if op == "email":
        return {"email": save_sift_email(body.get("email"))}
    if op == "oa_plan":
        return sift_oa.plan(folder)
    if op == "oa_find":
        email = str(srv.config().get("sift_email") or "")
        if not email:
            raise WorkbookError(sift_oa.NO_EMAIL)
        rec = body.get("rec_id")

        def keep(data: bytes) -> dict:
            with srv._lock:
                return sift_mod.save_pdf(folder, rec, data, replace=False)

        # the looking done outside the server's lock, so the screen goes on while a copy downloads
        found = sift_oa.find(folder, rec, email, keep=keep)
        held = found.pop("answer", None)
        return dict(held or {}, **found)
    if op == "cited_plan":
        # Find citation counts, for a screening made before: its records with a DOI. Only reads
        return search_mod.citation_plan(folder)
    if op == "cited":

        def keep_cited(counts: dict, day: str) -> int:
            with srv._lock:
                return sift_mod.write_cited(folder, counts, day)

        # the next fifty records with a DOI from `at`, asked of OpenAlex outside the server's lock and
        # their counts written under it
        try:
            at = int(body.get("at") or 0)
        except (TypeError, ValueError):
            at = 0
        return search_mod.find_citations(folder, at, keep=keep_cited)
    if op == "fill_plan":
        # Fill from OpenAlex, for a screening made before: its records with a DOI. Only reads
        return search_mod.fill_plan(folder)
    if op == "fill":

        def keep_filled(cells: dict, refs: dict) -> int:
            with srv._lock:
                return sift_mod.write_filled(folder, cells, refs)

        # the next fifty records with a DOI from `at`, asked of OpenAlex and Crossref outside the server's
        # lock and what they say written under it, Crossref's polite pool given the email Sift's settings keep
        try:
            at = int(body.get("at") or 0)
        except (TypeError, ValueError):
            at = 0
        return search_mod.fill_columns(folder, at, keep=keep_filled, email=str(srv.config().get("sift_email") or ""))
    if op == "study":
        with srv._lock:
            return sift_mod.study(folder, body.get("act"), body.get("rec_id"), body.get("with"))
    if op == "try":
        cfg = srv.config()
        if not srv.ai_on(cfg, "proposals"):
            raise WorkbookError(sift_ai.OFF)
        started = time.monotonic()
        result = sift_ai.trial(folder, body.get("rec_id"), body.get("stage") or "ta",
                               srv.ai_route(cfg, {"research_question": ""}),
                               body.get("prompt") if isinstance(body.get("prompt"), str) else None)
        if "error" in result:
            return dict(result, status=502)
        return dict(result, seconds=round(time.monotonic() - started, 1),
                    model_name=(sift_ai_state(cfg, folder) or {}).get("model_name", ""))
    if op == "titles":
        # the bench's records under Sift in Settings for a screening not open, each with its number and
        # title, those of the stage alone. Only reads
        sc = sift_mod.load(folder)
        held = sift_mod.states(sift_mod.read_log(folder))
        stage = sift_mod.stage_key(body.get("stage") or "ta")
        numbers = sift_mod.numbers_of(folder, sc)
        return {"stage": stage, "records": [{"rec_id": rec, "n": numbers.get(rec), "title": sift_mod.plain(sc.cell(rec, "title"))}
                                            for rec in sc.ids if sift_mod.in_stage(sc, held, rec, stage)]}
    if op == "list":
        sc = sift_mod.load(folder)
        return {"ids": sift_mod.listed(sc, sift_mod.read_log(folder), body.get("stage") or "ta",
                                       str(body.get("round") or "undecided"))}
    if op == "decide":
        second = second_of(folder)
        # the app's AI switch, so the log says whether his decision matched the suggestions the record showed
        shown = srv.ai_on(srv.config(), "proposals")
        with srv._lock:
            done = sift_mod.decide(folder, body.get("rec_id"), body.get("stage") or "ta", body.get("decision"),
                                   body.get("reason") or "", body.get("note"), second=second, ai_on=shown)
        return dict(done, second=sift_second.view(folder, second))
    if op == "note":
        with srv._lock:
            return sift_mod.note(folder, body.get("rec_id"), body.get("stage") or "ta", body.get("note") or "")
    if op == "undo":
        second = second_of(folder)
        with srv._lock:
            done = sift_mod.undo(folder, second=second)
        return dict(done, second=sift_second.view(folder, second))
    if op == "second":
        return sift_second_op(folder, body)
    if op == "field":
        with srv._lock:
            return sift_mod.set_field(folder, body.get("rec_id"), body.get("field"), body.get("value"))
    if op == "excerpt":
        with srv._lock:
            return sift_mod.excerpt(folder, body.get("act"), body.get("rec_id"), body.get("stage") or "ta",
                                    body.get("pieces"), body.get("at"), body.get("text"))
    if op == "view":
        columns = body.get("columns")
        with srv._lock:
            return {"table": sift_mod.save_view(folder, body.get("view"), columns if isinstance(columns, list) else None,
                                                body.get("filters"), body.get("find"), sidebar=body.get("sidebar"))}
    if op == "column":
        with srv._lock:
            return sift_mod.column(folder, body.get("act"), body.get("key"), body.get("name"), body.get("type"),
                                   body.get("options"))
    if op == "form":
        return sift_form_op(folder, body)
    if op == "stamp":
        return {"stamp": sift_mod.stamp(folder), "config": {"ai_suggest": srv.ai_on(srv.config(), "proposals")}}
    if op == "counts":
        c = sift_mod.counts(sift_mod.load(folder))
        return {"counts": c, "rows": sift_mod.count_rows(c)}
    if op == "export":
        with srv._lock:
            done = sift_mod.export(folder)
        return dict(done, path=srv.display_path(srv.rel_path(Path(done["path"]))))
    if op == "included":
        # Export included records, the records accepted at full text as RIS and CSV beside the CSV
        with srv._lock:
            return sift_mod.export_included(folder)
    if op == "reset":
        with srv._lock:
            return sift_mod.reset(folder, dry_run=body.get("dry_run") is True)
    if op == "pdf":
        try:
            data = base64.b64decode(str(body.get("data") or ""), validate=True)
        except (binascii.Error, ValueError):
            raise WorkbookError(sift_words.t("sift_server.routes.that_file_did_not_arrive")) from None
        if len(data) > SIFT_PDF_MAX:
            raise WorkbookError(sift_words.t("sift_server.routes.that_pdf_is_over_200"))
        with srv._lock:
            return sift_mod.save_pdf(folder, body.get("rec_id"), data, body.get("replace") is True)
    if op == "ai":
        # the screening's own AI settings for Settings, under Sift, whatever the app's switch says, so
        # the switch turned on in the same card shows them. Only reads
        return {"ai": sift_ai_state(dict(srv.config(), ai_suggest=True, **{app_identity.AI_OFF_KEY: []}), folder)}
    if op in ("settings", "plan", "propose"):
        cfg = srv.config()
        if op == "settings":
            if not srv.ai_on(cfg, "proposals"):
                raise WorkbookError(sift_ai.OFF)
            with srv._lock:
                sift_ai.save_settings(folder, body.get("ai_proposals") if isinstance(body.get("ai_proposals"), bool) else None,
                                      body.get("prompt") if isinstance(body.get("prompt"), str) else None)
            return {"ai": sift_ai_state(cfg, folder)}
        sift_ai_ready(cfg, folder)
        if op == "plan":
            plan = sift_ai.plan(folder, body.get("stage") or "ta", str(body.get("round") or "undecided"))
            # the rows the table shows, when the screen names them, the undecided among them alone
            ids = body.get("ids")
            if isinstance(ids, list):
                shown = {str(i) for i in ids}
                plan["ids"] = [rec for rec in plan["ids"] if rec in shown]
                plan["calls"] = len(plan["ids"])
            return plan
        started = time.monotonic()
        result = sift_ai.propose(folder, body.get("rec_id"), body.get("stage") or "ta",
                                 srv.ai_route(cfg, {"research_question": ""}))
        if "error" in result:
            return dict(result, status=502)
        return dict(result, seconds=round(time.monotonic() - started, 1))
    raise WorkbookError(sift_words.t("sift_server.routes.the_op_is_read_list"))


def sift_form_op(folder: Path, body: dict) -> dict:
    """Extract and appraise's form (13 October, later), with `act`: `list`, its records, those included at
    full text and the benchmark papers, with the form's sections and fields, `read`, the form and each record's row as the export writes it,
    `field`, one field set whole, `key` the field's when it changes one and none to add, `field` its
    definition, `order`, the sections and their fields in order, `sections`, `remove`, a field by its
    `key`, its values kept in the log, and `export`, `screening.form.csv` beside the CSV, or with `dry_run`
    only counted. A value on a record goes through the `field` op as his columns' values do. No act calls a
    model."""
    act = str(body.get("act") or "list")
    if act == "list":
        return sift_mod.form_round(folder)
    if act == "read":
        return sift_mod.form_read(folder)
    with srv._lock:
        if act == "field":
            return sift_mod.form_field(folder, body.get("key") or None, body.get("field"))
        if act == "order":
            return sift_mod.order_form(folder, body.get("sections"))
        if act == "remove":
            return sift_mod.column(folder, "remove", key=sift_mod.own_key(body.get("key")))
        if act == "export":
            return sift_mod.export_form(folder, dry_run=body.get("dry_run") is True)
    raise WorkbookError(sift_words.t("sift_server.routes.the_form_s_act_is"))


def sift_second_op(folder: Path, body: dict) -> dict:
    """The second screener's side of a screening, with `act` (see `api_sift`), the project's settings
    passed in and the side answered afresh as `second` with the counts and the flow."""
    act = str(body.get("act") or "")
    second = second_of(folder)
    stage = body.get("stage") or "ta"
    review = review_holding(folder) or folder
    question = review_question(review, kept_review(review))
    if act == "draw":
        with srv._lock:
            done = sift_second.draw(folder, stage, second)
    elif act == "workbook":
        with srv._lock:
            done = sift_second.make_workbook(folder, stage, second, question, eligibility_of(folder))
    elif act == "differences":
        with srv._lock:
            done = sift_second.make_differences(folder, stage, second, question)
    elif act == "take":
        try:
            data = base64.b64decode(str(body.get("data") or ""), validate=True)
        except (binascii.Error, ValueError):
            raise WorkbookError(sift_words.t("sift_server.routes.that_file_did_not_arrive_2")) from None
        with srv._lock:
            done = sift_second.take_back(folder, data, str(body.get("name") or ""), second)
    elif act == "outcome":
        with srv._lock:
            done = sift_second.settle_one(folder, body.get("rec_id"), stage, str(body.get("outcome") or ""),
                                          body.get("decision"), second, ai_on=srv.ai_on(srv.config(), "proposals"))
    else:
        raise WorkbookError(sift_words.t("sift_server.routes.the_act_is_draw_workbook"))
    sc = sift_mod.load(folder)
    c = sift_mod.counts(sc)
    out = dict(done, second=sift_second.view(folder, second, sc), counts=c, prisma=sift_mod.prisma_source(c),
               stamp=sift_mod.stamp(folder))
    if act == "outcome" and isinstance(done.get("record"), dict):
        out["record"] = done["record"]
    return out


SIFT_EMAIL = re.compile(r"[^@\s]+@[^@\s]+\.[^@\s]+")


def save_sift_email(value) -> str:
    """The email Unpaywall asks of Find open-access PDFs, written to config.json as `sift_email`,
    every other setting as it was, or emptied. One that is not an address is refused."""
    email = " ".join(str(value or "").split())
    if email and not SIFT_EMAIL.fullmatch(email):
        raise WorkbookError(sift_words.t("sift_server.routes.that_is_not_an_email"))
    with srv._lock:
        srv.write_config_keys({"sift_email": email})
    return email


SIFT_PDF_PATH = "/sift/pdf"


def sift_pdf(query: dict) -> tuple[int, bytes, str]:
    """A record's PDF for the pane, `pdfs/<rec_id>.pdf` beside the CSV of a screening he opened,
    for a record the CSV holds, and nothing from anywhere else."""
    try:
        folder = sift_folder(query.get("folder"))
        rec = str(query.get("rec") or "")
        if rec not in sift_mod.load(folder).at:
            return 404, b"No such record.", "text/plain; charset=utf-8"
    except srv.OutsideRoot as exc:
        return 403, str(exc).encode("utf-8"), "text/plain; charset=utf-8"
    except (WorkbookError, OSError) as exc:
        return 404, str(exc).encode("utf-8"), "text/plain; charset=utf-8"
    found = sift_mod.pdf_path(folder, rec)
    if found is None:
        return 404, b"No PDF.", "text/plain; charset=utf-8"
    return 200, found.read_bytes(), "application/pdf"


# ----------------------------------------------------------- sift searches

# Sift's searches (see `sift_search.py`), on a review in the list of reviews (see `api_sift_review`)
# that has searches. A run goes on a thread of its own, which the page asks after, and holds the
# review folder's own lock, never the server's, so the rest of the app goes on while the databases
# answer.
SEARCH_EXPORT_MAX = 100 * 1024 * 1024


SEARCH_RUNS: dict[str, dict] = {}


# the file of a review's folder Search strategy opens in the computer's own app for it, by the word the
# page sends, never written: search_plan.md, once Export has written it. The exclusion reasons are
# edited on the screen itself, so reasons.csv is never opened (12 October, later)
SEARCH_FILES = {"plan": search_mod.PLAN_MD}


def search_folder(value) -> Path:
    """A review's folder from a request, refused unless the list of reviews holds it and it has
    searches, so no request reads or writes a folder he never chose, and a screening alone never
    gains a plan."""
    folder = review_folder(value)
    if not has_searches(folder):
        raise WorkbookError(_w("NO_SEARCHES"))
    return folder


def search_run_thread(folder: Path, key: str, listed: list | None = None, follows=None) -> None:
    """A run on its own thread, each database's state kept for the page as it goes, following the
    earlier run the page chose."""
    held = SEARCH_RUNS[key]
    # Crossref's polite pool, asked in the run's fill, takes the email Sift's settings keep
    ctx = search_mod.Context(email=str(srv.config().get("sift_email") or ""))

    def heard(source: str, said: dict) -> None:
        held["sources"][source] = said

    try:
        # the dry run's truncation check first, its table kept in the run folder (14 October)
        held["result"] = search_mod.run(folder, which="newest", progress=heard, ctx=ctx, listed=listed, follows=follows,
                                        check_terms=True)
    except WorkbookError as exc:
        held["error"] = ctx.scrub(str(exc))
    except Exception as exc:                          # said on the page, never a key
        held["error"] = ctx.scrub(f"{type(exc).__name__}: {exc}")
    finally:
        held["running"] = False


def search_catalog() -> dict:
    """The databases Sift knows, their names, those it searches by API and their key fields, the
    platforms, each database's own search page and its platform's, the field scopes and the document
    types, which the plan screen and the list under Projects in Settings draw their choices from."""
    return {"sources": list(search_mod.SOURCES), "names": search_mod.NAMES, "keyless": list(search_mod.KEYLESS),
            "keyed": search_mod.KEYS, "apis": list(search_mod.APIS), "fields": search_mod.KEY_FIELDS,
            "platformed": list(search_mod.PLATFORMED), "sites": search_mod.SITES,
            "platform_sites": search_mod.PLATFORM_SITES, "hosts": search_mod.PLATFORM_HOSTS,
            "platforms": [[k, search_mod.PLATFORM_NAMES[k]] for k in search_mod.PLATFORMS],
            "offered": {s: [[k, search_mod.PLATFORM_NAMES[k]] for k in ks] for s, ks in search_mod.OFFERED.items()},
            "scopes": [[k, search_mod.scope_said(k)[:1].upper() + search_mod.scope_said(k)[1:]] for k in search_mod.SCOPES],
            "types": [[k, search_mod.TYPE_WORDS[k][:1].upper() + search_mod.TYPE_WORDS[k][1:]] for k in search_mod.TYPES],
            # the databases whose truncation Check truncation counts, by API (14 October)
            "truncates": list(search_mod.TRUNCATES)}


def search_read(folder: Path) -> dict:
    """The plan and the runs for the screen, with each database by API or by export by the user's own
    list, that list in its order, whether each keyed database has its key, never the key, today's
    date, a run under way, and the catalogue the screen draws its choices from."""
    have = search_mod.keys_set()
    listed = search_mod.databases(srv.config())
    answer = search_mod.state(folder, with_runs=True)
    return dict(answer, folder=srv.rel_path(folder), keys=have, today=datetime.now().date().isoformat(),
                how={s: search_mod.how_of(s, have, listed) for s in search_mod.SOURCES}, listed=listed,
                running=SEARCH_RUNS.get(str(folder)), catalog=search_catalog())


def api_sift_search(body: dict) -> dict:
    """Sift's searches, with `op`, on a review's folder. `read` is the plan, its versions, each
    database's string, whether each keyed database has its key, the runs, a run under way and
    `review`, the review for its steps, and puts the review at the head of the list of reviews. `save`
    keeps `plan`, a draft of
    the next version when the newest is registered, with `reason`. `export` writes the newest version
    to search_plan.md, a draft or registered, and answers its Markdown. `register`, Mark as registered,
    freezes the newest version with `registry` and `registration`, its number or link, both asked
    for. `reasons` writes the exclusion reasons, `rows`, to the review's reasons.csv and saves the plan
    with them. `title` answers the title of a benchmark paper by its `doi`, asked of OpenAlex, writing
    nothing. `works` answers the works OpenAlex holds for a key work's `text`, a DOI or a title, to pick
    from, writing nothing, and `key_works` writes the review's key works, `rows`, beside the plan's
    versions (see `sift_search.save_key_works`). `run` starts a run of the newest version on a thread of its
    own, a new run folder, carrying the screening of `follows`, an earlier run's folder name, or of
    none, and `progress` says how it goes, and once it ends the runs, the benchmark's titles and the
    review, whose Screening step a new run never takes over. `drop` keeps a database's export,
    `source`, `name` and `data` in base64, in the day's newest run folder and writes that run afresh,
    answering the runs, the titles and the review. `screening` answers a run's folder, `date`, its
    folder's name, for Sift to open. `open` opens search_plan.md of the review's folder, `file` plan,
    in the computer's own app for it, writing nothing. A `save` of a plan holding a phrase with
    truncation writes nothing and answers the plan as it stands with `unsaved`, the lines that stand in
    the way, and the problems of the plan sent, so the screen marks the term (14 October). `terms`,
    Check truncation, answers the dry run's truncation check of the newest version, its counts asked of
    the databases it searches by API, writing nothing, and a run checks first and keeps the table in its
    folder (see `sift_search.truncation_check`)."""
    op = str(body.get("op") or "read")
    folder = search_folder(body.get("folder"))
    key = str(folder)
    if op == "read":
        answer = search_read(folder)
        with srv._lock:
            remember_review(folder)
        return dict(answer, review=review_view(folder))
    if op == "save":
        reason = body.get("reason") if isinstance(body.get("reason"), str) else None
        try:
            return dict(search_mod.save(folder, body.get("plan"), reason, seen=body.get("seen")),
                        folder=srv.rel_path(folder), unsaved=[])
        except search_mod.StalePlan as exc:
            # the plan changed since the page read it: nothing written, and the version it holds now,
            # which Overwrite sends back (19 October)
            return {"error": str(exc), "stale": {"version": exc.now}, "status": 409}
        except search_mod.Unsaved as exc:
            return dict(search_mod.state(folder), **exc.view, unsaved=exc.lines, folder=srv.rel_path(folder))
    if op == "terms":
        if (SEARCH_RUNS.get(key) or {}).get("running"):
            raise WorkbookError(sift_words.t("sift_server.routes.a_run_of_this_plan"))
        return search_mod.check_terms(folder, "newest", search_mod.databases(srv.config()),
                                      search_mod.Context(email=str(srv.config().get("sift_email") or "")))
    if op == "register":
        registry = " ".join(str(body.get("registry") or "").split())
        registration = " ".join(str(body.get("registration") or "").split())
        if not registry or not registration:
            raise WorkbookError(sift_words.t("sift_server.routes.say_where_the_plan_is"))
        return dict(search_mod.register(folder, body.get("reason") if isinstance(body.get("reason"), str) else None,
                                        registry=registry, registration=registration), folder=srv.rel_path(folder))
    if op == "export":
        return dict(search_mod.export(folder), folder=srv.rel_path(folder))
    if op == "reasons":
        rows = body.get("rows")
        if not isinstance(rows, list):
            raise WorkbookError(sift_words.t("sift_server.routes.the_reasons_are_a_list"))
        try:
            return dict(search_mod.save_reasons(folder, rows, seen=body.get("seen")), folder=srv.rel_path(folder))
        except search_mod.StalePlan as exc:
            return {"error": str(exc), "stale": {"version": exc.now}, "status": 409}
    if op == "title":
        return search_mod.paper_title(body.get("doi"))
    if op == "works":
        return search_mod.find_works(body.get("text"))
    if op == "key_works":
        return dict(search_mod.save_key_works(folder, body.get("rows")), folder=srv.rel_path(folder))
    if op == "run":
        if (SEARCH_RUNS.get(key) or {}).get("running"):
            raise WorkbookError(sift_words.t("sift_server.routes.a_run_of_this_plan"))
        listed = search_mod.databases(srv.config())
        follows = search_mod.follow_day(body.get("follows"))
        plan = search_mod.run(folder, which="newest", dry_run=True, listed=listed, follows=follows)
        SEARCH_RUNS[key] = {"running": True, "date": plan["date"], "version": plan["version"], "sources": {
            s["source"]: {"name": s["name"], "state": "waiting", "how": s["how"]} for s in plan["sources"]},
            "result": None, "error": "", "follows": plan["follows"]}
        threading.Thread(target=search_run_thread, args=(folder, key, listed, follows), daemon=True).start()
        return {"started": True, "running": SEARCH_RUNS[key]}
    if op == "progress":
        held = SEARCH_RUNS.get(key)
        done = bool(held and not held["running"])
        return {"running": held, "runs": search_mod.runs(folder) if done else None,
                "titles": search_mod.benchmark_titles(folder) if done else None,
                "review": review_view(folder) if done else None}
    if op == "drop":
        try:
            data = base64.b64decode(str(body.get("data") or ""), validate=True)
        except (binascii.Error, ValueError):
            raise WorkbookError(sift_words.t("sift_server.routes.that_file_did_not_arrive")) from None
        if len(data) > SEARCH_EXPORT_MAX:
            raise WorkbookError(sift_words.t("sift_server.routes.that_export_is_over_100"))
        if (SEARCH_RUNS.get(key) or {}).get("running"):
            raise WorkbookError(sift_words.t("sift_server.routes.a_run_of_this_plan_2"))
        # into the run the screen shows, by its folder's name, never an earlier run of its day
        done = search_mod.take_export(folder, str(body.get("source") or ""), data, str(body.get("name") or ""),
                                      listed=search_mod.databases(srv.config()), run=str(body.get("run") or "") or None,
                                      ctx=search_mod.Context(email=str(srv.config().get("sift_email") or "")))
        return dict(done, runs=search_mod.runs(folder), titles=search_mod.benchmark_titles(folder), review=review_view(folder))
    if op == "runs":
        return {"runs": search_mod.runs(folder)}
    if op == "screening":
        run_dir = search_mod.run_path(folder, str(body.get("date") or ""))
        if not sift_mod.is_screening(run_dir):
            raise WorkbookError(sift_words.t("sift_server.routes.that_run_holds_no", csv_name=sift_mod.CSV_NAME))
        return {"folder": srv.rel_path(run_dir.resolve())}
    if op == "open":
        name = SEARCH_FILES.get(str(body.get("file") or ""))
        if not name:
            raise WorkbookError(sift_words.t("sift_server.routes.the_file_is_plan"))
        target = folder / name
        if not target.is_file():
            raise WorkbookError(sift_words.t("sift_server.routes.there_is_no_in_the", name=name))
        srv.OPEN_FILE(target)
        return {"opened": name}
    raise WorkbookError(sift_words.t("sift_server.routes.the_op_is_read_save"))


# --------------------------------------------------------------- databases

DATABASE_OPS = ("read", "key", "clear", "check", "save")


def save_databases(rows) -> list[dict]:
    """Sift's databases written to the settings file as `rows` has them, in their order, the rest of
    the file as it was, never a key. Answers the list as kept."""
    with srv._lock:
        databases = search_mod.clean_databases(rows if isinstance(rows, list) else [])
        srv.write_config_keys({"databases": databases})
    return databases


def api_databases(body: dict) -> dict:
    """Sift's databases under Sift in Settings, with `op`. `read` is the user's list as saved, in
    its order, the catalogue and whether each key is saved, never what it is. `key` stores `key` under
    `service`, one of the keychain services the databases' keys go by, as the Anthropic key is
    stored, and answers that it was saved. `clear` removes it. `check` sends a search for one record
    to `source` with its key and answers one line on whether the database took it. `save` writes the
    list, `rows`, at once, as a database's cog and Add database on Search strategy change it, and
    Settings saves it with the rest, through `/api/settings`. No exception from below is passed on,
    since the argv of the `security` call carries the key, and no answer carries a key."""
    op = str(body.get("op") or "read")
    if op not in DATABASE_OPS:
        raise WorkbookError(sift_words.t("sift_server.routes.the_op_is_read_key"))
    try:
        if op == "save":
            return {"rows": save_databases(body.get("rows"))}
        if op == "key":
            return search_mod.save_key(str(body.get("service") or ""), body.get("key"))
        if op == "clear":
            return search_mod.clear_key(str(body.get("service") or ""))
        if op == "check":
            return search_mod.check(str(body.get("source") or ""))
        return {"rows": search_mod.databases(srv.config()), "catalog": search_catalog(),
                "saved": {s: search_mod.key_saved(s) for s in search_mod.SERVICES}}
    except WorkbookError as exc:
        raise WorkbookError(str(exc)) from None
    except Exception:
        return {"error": sift_words.t("sift_server.routes.that_could_not_be_done"), "status": 500}


# --------------------------------------------------------------- zotero

# Sift's sync to Zotero (see `sift_zotero.py`). A sync goes on a thread of its own, which the page
# asks after, and holds the screening's own `zotero.lock`, never the server's, so the rest of the app
# goes on while Zotero answers.
ZOTERO_OPS = ("read", "key", "clear", "check", "plan", "sync", "progress")


ZOTERO_SYNCS: dict[str, dict] = {}


def zotero_name(folder: Path) -> str:
    """The collection a screening syncs to, named for its Sift project as the home screen names it."""
    review = review_holding(folder) or folder
    return review_name(review, kept_review(review))


def zotero_sync_thread(folder: Path, key: str, cfg: dict, which: str, ids) -> None:
    """A sync on its own thread, how far it has gone kept for the page."""
    held = ZOTERO_SYNCS[key]

    def heard(done: int, of: int) -> None:
        held["done"], held["of"] = done, of

    try:
        held["result"] = zotero_mod.sync(folder, cfg, which, ids, name=zotero_name(folder), progress=heard)
    except WorkbookError as exc:
        held["error"] = str(exc)
    except Exception:                                 # said on the page in a plain line, never a key
        held["error"] = sift_words.t("sift_server.routes.the_sync_ran_into_something")
    finally:
        held["running"] = False


def api_zotero(body: dict) -> dict:
    """Sift's sync to Zotero, with `op`. `read` is the library and its ids as `config.json` keeps them
    under `zotero` and `saved`, whether the key is in the keychain, never what it is. `key` stores
    `key` under ZOTERO_API_KEY as every key is stored and answers that it was saved, and `clear`
    removes it. `check` reads the key's own record and the library's name from Zotero, with `settings`
    as Settings holds them before Save, and answers one line, `said`. `plan`, on a screening's `folder`, is the preview, what a sync of `which` records,
    `included`, `filter` with `ids` or `all`, would add, update and leave and the PDFs it would upload,
    nothing written. `sync` starts the sync on a thread of its own and `progress` says how it goes and
    once it ends what it did. No exception from below is passed on, since the argv of the `security`
    call carries the key, and no answer carries a key."""
    op = str(body.get("op") or "read")
    if op not in ZOTERO_OPS:
        raise WorkbookError(sift_words.t("sift_server.routes.the_op_is_read_key_2"))
    try:
        if op == "read":
            return {"settings": zotero_mod.settings_of(srv.config()), "saved": zotero_mod.key_saved()}
        if op == "key":
            return zotero_mod.save_key(body.get("key"))
        if op == "clear":
            return zotero_mod.clear_key()
        if op == "check":
            given = body.get("settings") if isinstance(body.get("settings"), dict) else None
            return zotero_mod.check(srv.config(), given)
        folder = sift_folder(body.get("folder"))
        key = str(folder)
        which = str(body.get("which") or "included")
        ids = body.get("ids") if isinstance(body.get("ids"), list) else None
        if op == "plan":
            return zotero_mod.sync(folder, srv.config(), which, ids, name=zotero_name(folder), dry_run=True)
        if op == "sync":
            if (ZOTERO_SYNCS.get(key) or {}).get("running"):
                raise WorkbookError(sift_words.t("sift_server.routes.a_sync_of_this_screening"))
            zotero_mod.chosen_ids(sift_mod.load(folder), {}, which, ids)        # a wrong `which` refused here
            ZOTERO_SYNCS[key] = {"running": True, "done": 0, "of": 0, "result": None, "error": ""}
            threading.Thread(target=zotero_sync_thread, args=(folder, key, srv.config(), which, ids), daemon=True).start()
            return {"started": True, "running": dict(ZOTERO_SYNCS[key])}
        return {"running": dict(ZOTERO_SYNCS[key]) if key in ZOTERO_SYNCS else None}
    except srv.OutsideRoot:
        raise
    except WorkbookError as exc:
        raise WorkbookError(str(exc)) from None
    except Exception:
        return {"error": sift_words.t("sift_server.routes.that_could_not_be_done"), "status": 500}


# ------------------------------------------------------------------ Search

def search_sift_place(value) -> tuple[Path | None, Path | None]:
    """The review and the screening a Sift search reaches from the folder the page names: a review's own
    folder, from Search strategy, with the screening its Screening step opens, or a screening, from the Sift
    screen, with the review it belongs to. A folder in no Sift project he opened is refused."""
    folder = srv.there_folder(value)
    entry = kept_review(folder)
    if entry is not None:
        return folder, screening_of(folder, entry)
    screening = sift_folder(value)
    return review_holding(screening), screening


def search_sift_project(review: Path | None, screening: Path | None, entry: dict | None = None) -> dict:
    """A Sift project as a search takes it: the screening's folder and the review's as the page names them,
    and the review's plan where it has one."""
    review = Path(review).resolve() if review is not None else None
    screening = Path(screening).resolve() if screening is not None else None
    plan = review if review is not None and search_mod.plan_path(review).is_file() else None
    return {"id": srv.rel_path(review) if review is not None else "", "screening": screening,
            "screening_id": srv.rel_path(screening) if screening is not None else "", "review": plan,
            "review_id": srv.rel_path(plan) if plan is not None else "",
            "name": review_name(review, entry or kept_review(review)) if review is not None else ""}


def search_scope(body: dict, kinds: list[str]) -> dict:
    """Search's This Sift project: the project of `folder`, a review's or a screening's, its screening's
    records and its plan (see `search_sift_place`)."""
    if not body.get("folder"):
        raise WorkbookError(sift_find.NO_SIFT)
    p = search_sift_project(*search_sift_place(body["folder"]))
    whole, match_case = app_search.options(body)
    return sift_find.search_sift(body.get("q") or "", p["screening"], p["screening_id"], p["review"], p["review_id"],
                                 kinds=kinds, whole=whole, match_case=match_case)


def search_rows() -> list[dict]:
    """Everything's Sift projects, each there now, in the home screen's order, with the screening its
    Screening step opens."""
    rows = []
    for e in reviews_kept():
        folder = srv.abs_path(e["folder"])
        if folder.is_dir():
            rows.append(search_sift_project(folder, screening_of(folder, e), e))
    return rows


# ------------------------------------------------------------ the family's hooks

# Sift's own settings and their defaults, under Sift in Settings: his list of databases, empty on a new install,
# each a database Sift knows or another by name, its platform and whether it goes by API or by export, never a
# key, which is in the keychain (see `sift_search.save_key`), the email Unpaywall asks of Find open-access PDFs,
# and the Zotero library a sync goes to, his own, the key's owner's, or a group's by the id zotero.org gives,
# never the key (see `sift_zotero.py`)
SETTINGS_DEFAULTS = (("quit_when_closed", {"databases": [], "sift_email": "", "zotero": {"library": "user", "group_id": ""}}),)
OWN_SETTINGS = ("databases", "sift_email", "zotero")


def holding() -> str:
    """Sift's work under way that holds a quit, in a few words, or "" for none: a search run or a
    Zotero sync."""
    if any((held or {}).get("running") for held in list(SEARCH_RUNS.values())):
        return sift_words.t("sift_server.routes.a_search_run")
    if any((held or {}).get("running") for held in list(ZOTERO_SYNCS.values())):
        return sift_words.t("sift_server.routes.a_zotero_sync")
    return ""


srv.register("sift", routes={"/api/sift": api_sift, "/api/sift-search": api_sift_search,
                             "/api/sift-review": api_sift_review, "/api/databases": api_databases,
                             "/api/zotero": api_zotero},
             post_only=("/api/sift", "/api/sift-search", "/api/sift-review", "/api/databases", "/api/zotero"),
             get_paths={SIFT_PDF_PATH: sift_pdf}, home=("reviews", review_rows), search_scope=("sift", search_scope),
             search_rows=search_rows,
             # a database's key rides in /api/databases' `key` op and his Zotero key in /api/zotero's
             silent=("/api/databases", "/api/zotero"),
             # his databases and his Zotero library as Settings saves them, never a key
             settings={"databases": (list, search_mod.clean_databases), "zotero": (dict, zotero_mod.clean_settings)},
             # Sift's own settings and their defaults, out of the family's since the sixth build (23 October 2026),
             # before the closing tick as a file has always held them, which another app's save leaves alone
             defaults=SETTINGS_DEFAULTS, own_settings=OWN_SETTINGS,
             key_files=(search_mod,), holding=holding)
