#!/usr/bin/env python3
"""Sift's second screener, as PRISMA 2020 item 8 asks: how many people screened each record and
whether they worked apart. The second screener has no Idiograph, so their side is an Excel workbook
Sift makes, and the two talk their differences through by a second workbook. The defaults follow the
book, every record screened by two (Cochrane's practice), and his own habits are settings.

The settings are the project's, kept by the server in the list of reviews beside its name and
question (see `server.py`): `on`, off on a new project, `first` and `name`, his name or initials and
theirs, `share`, the share drawn at each stage from 1 to 100, 100 every record, `calibration`, the
records the two screen together first, and `kappa`, the kappa below which Sift offers a further draw,
0.6 by default (McHugh 2012). The server passes them in, and every figure that matters later is in
the log, so the counts and the flow need none of them.

Every act is one line of the screening's log, `act` `second`, which `sift.read_log` passes over, so no
line here ever moves a decision of his. Each line names its stage and one of these `change`s:

`draw`, the share drawn at a stage: its number, 1 up, its seed, the share, the calibration records,
the pool it drew from, the stage's records less the calibration and earlier draws in record number
order, and the rec_ids drawn, `random.Random(seed).sample(pool, k)`, so the draw repeats from its seed.
`workbook`, a workbook made, `kind` second or differences, its file and its rec_ids. `decision`, a
second screener's decision taken from their workbook, its reason and note and what it was before.
`unblind`, his decisions on a draw's records as they stood when he had decided every one of them,
before he could see any of theirs. `agreement`, once both have decided a draw's records, at once and
for good: the records, those decided alike, the proportion, Cohen's kappa on going forward, Yes or
Maybe, against No, and the table of the two decisions with each record's pair. `reply`, a reply
from the differences workbook, agree or keep, with its note. `outcome`, a difference agreed with its
decision, sent to a third reviewer, or open again. `third`, the third reviewer's decision.

His own decisions carry two marks of this module's: `calibration` on a calibration record, and
`after`, discussion or third reviewer, on a change to a drawn record once he can see theirs. At full
text a decision is Include or Exclude, so his Maybe there counts as not yet decided for the draw. The
workbooks show each stage's words, `sift.SHOWN_WORDS`, and the log and `screening.second.csv` keep
include, maybe and exclude, as they always have (12 October).
`screening.second.csv` beside the CSV holds the second screener's decisions as the log stands,
written afresh after each act that moves them. The workbooks and a full text draw's PDFs folder go
beside the CSV, each a new file, never one written over.
"""
from __future__ import annotations

import csv
import io
import math
import random
import re
import shutil
from datetime import datetime
from pathlib import Path

import sift_words
import locks
import sift
from sift import SiftError

ACT = "second"
MIRROR_NAME = "screening.second.csv"
DEFAULTS = {"on": False, "first": "", "name": "", "share": 100, "calibration": 0, "kappa": 0.6}
NAME_MAX = 40
CALIBRATION_MAX = 2000
FORWARD = ("include", "maybe")
SEED_LOW, SEED_HIGH = 100000, 1000000
KINDS = ("second", "differences")
REPLIES = {"agree with you": "agree", "keep mine": "keep"}
REPLY_WORDS = {"agree": "Agree with you", "keep": "Keep mine"}
OUTCOMES = ("agreed", "third", "open")
# a decision as a returned workbook gives it, the stage's words since 12 October, Yes, Maybe and No or
# Include and Exclude, and the older Accept and Reject still read, each kept as include, maybe or exclude
SAID = {"yes": "include", "no": "exclude", "include": "include", "exclude": "exclude",
        "accept": "include", "reject": "exclude", "maybe": "maybe"}
# the hidden sheet that says which screening, stage and draws a workbook was made for
MARK_SHEET = "sift"
RECORDS_SHEET = "Records"
DIFFERENCES_SHEET = "Differences"
ABOUT_SHEET = "About"
BOOK_MAX = 50 * 1024 * 1024
CELL_MAX = 32000

# This module's words for a person, read in the run's language when said: inside the module through `_w`,
# from others and the checks as the module's names (`__getattr__`), `sift_second.NOT_OURS` (SAID above is the
# workbook's decisions)
WORDS = {
    "NOT_OURS": lambda: sift_words.t("sift_server.two.not_ours"),
    "TURNED_OFF": lambda: sift_words.t("sift_server.two.turned_off"),
    "FT_WAITS": lambda: sift_words.t("sift_server.two.ft_waits"),
    "NONE_LEFT": lambda: sift_words.t("sift_server.two.none_left"),
    "ALL_BACK": lambda: sift_words.t("sift_server.two.all_back"),
    "NOT_APART": lambda: sift_words.t("sift_server.two.not_apart"),
    "NOT_THIRD": lambda: sift_words.t("sift_server.two.not_third"),
}
NO_REASON = {"ta": lambda: sift_words.t("sift_server.two.no_reason_ta"), "ft": lambda: sift_words.t("sift_server.two.no_reason_ft")}


def _w(name: str) -> str:
    return WORDS[name]()


def __getattr__(name: str) -> str:
    """This module's words other modules and the checks name, read in the run's language."""
    if name in WORDS:
        return WORDS[name]()
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


# ------------------------------------------------------------------ settings

def whole(value, low: int, high: int, default: int) -> int:
    """A whole number between two ends, or the default for anything that is not one."""
    if isinstance(value, bool):
        return default
    try:
        n = int(str(value).strip())
    except (TypeError, ValueError):
        return default
    return max(low, min(high, n))


def settings_of(raw) -> dict:
    """The second screener's settings as kept, each set to its default when missing or of another
    shape: the switch, the two names on one line, the share 1 to 100, the calibration records and
    the kappa 0 to 1 to two places."""
    raw = raw if isinstance(raw, dict) else {}
    out = dict(DEFAULTS)
    out["on"] = raw.get("on") is True
    for key in ("first", "name"):
        out[key] = sift.one_line(raw.get(key))[:NAME_MAX]
    out["share"] = whole(raw.get("share"), 1, 100, DEFAULTS["share"])
    out["calibration"] = whole(raw.get("calibration"), 0, CALIBRATION_MAX, DEFAULTS["calibration"])
    try:
        k = float(raw.get("kappa"))
    except (TypeError, ValueError):
        k = DEFAULTS["kappa"]
    out["kappa"] = round(min(1.0, max(0.0, k)), 2) if math.isfinite(k) else DEFAULTS["kappa"]
    return out


# ------------------------------------------------------------------ the log

def lines_of(folder) -> list[dict]:
    """Every line of the log that is this module's, oldest first."""
    return [e for e in sift.read_lines(folder) if e.get("act") == ACT]


def stage_of(entry: dict) -> str:
    return sift.STAGE_SAID.get(str(entry.get("stage") or "").lower(), "")


def forward(decision) -> bool:
    return decision in FORWARD


def his(sc, held: dict, rec: str, stage: str) -> str:
    """His decision on a record at a stage as the draw counts it, empty while undecided, and at full
    text a Maybe counted as undecided, since a full text decision is Include or Exclude."""
    d = sift.state_of(sc, held, rec, stage)["decision"]
    return "" if stage == "ft" and d == "maybe" else d


def agreement(pairs: dict) -> dict:
    """The agreement of two screeners over records, each `[his, theirs]`: the records, those decided
    alike and the proportion, both on going forward, Yes or Maybe, against No, Cohen's kappa
    on the same, None when both put every record one way, and the whole table of his decisions
    against theirs."""
    n = len(pairs)
    table = {a: {b: 0 for b in sift.DECISIONS} for a in sift.DECISIONS}
    both = first = second = neither = 0
    for mine, theirs in pairs.values():
        if mine in table and theirs in table[mine]:
            table[mine][theirs] += 1
        fm, ft = forward(mine), forward(theirs)
        if fm and ft:
            both += 1
        elif fm:
            first += 1
        elif ft:
            second += 1
        else:
            neither += 1
    if not n:
        return {"records": 0, "alike": 0, "proportion": None, "kappa": None, "table": table,
                "forward": {"both": 0, "first": 0, "second": 0, "neither": 0}}
    observed = (both + neither) / n
    pm, pt = (both + first) / n, (both + second) / n
    chance = pm * pt + (1 - pm) * (1 - pt)
    kappa = None if chance >= 1 else round((observed - chance) / (1 - chance), 3)
    return {"records": n, "alike": both + neither, "proportion": round(observed, 3), "kappa": kappa, "table": table,
            "forward": {"both": both, "first": first, "second": second, "neither": neither}}


def redraw(pool: list, seed: int, k: int) -> list:
    """A draw as Sift makes it and anyone can make it again: k of the pool, in the order given, by
    Python's `random.Random(seed).sample`."""
    return random.Random(seed).sample(list(pool), k)


class Two:
    """The second screener's side of a screening as its log holds it, read once: each stage's draws,
    its calibration records, their decisions, his decisions as they stood when each draw was
    unblinded, the agreements, the workbooks made, the replies and each difference's outcome."""

    def __init__(self, folder, sc, held: dict, lines: list[dict], settings=None):
        self.folder = Path(folder)
        self.sc = sc
        self.held = held
        self.settings = settings_of(settings) if settings is not None else None
        self.numbers = sift.numbers_of(folder, sc)
        self.first = self.name = ""
        self.st = {stage: {"draws": [], "calibration": None, "theirs": {}, "unblind": {}, "agreements": {},
                           "workbooks": [], "replies": {}, "outcome": {}} for stage in sift.STAGES}
        for e in lines:
            stage = stage_of(e)
            if not stage:
                continue
            s = self.st[stage]
            change = e.get("change")
            rec = str(e.get("rec_id") or "")
            if change == "draw":
                s["draws"].append(e)
                if s["calibration"] is None:
                    s["calibration"] = [str(r) for r in e.get("calibration") or []]
                self.first = str(e.get("first") or self.first)
                self.name = str(e.get("name") or self.name)
            elif change == "decision" and rec:
                if sift.decision_word(e.get("decision")):
                    s["theirs"][rec] = {"decision": sift.decision_word(e.get("decision")), "reason": str(e.get("reason") or ""),
                                        "note": str(e.get("note") or ""), "at": e.get("at")}
                else:
                    s["theirs"].pop(rec, None)
            elif change == "unblind":
                s["unblind"][e.get("draw")] = {str(r): list(v) for r, v in (e.get("mine") or {}).items()}
            elif change == "agreement":
                s["agreements"][e.get("draw")] = e
            elif change == "workbook":
                s["workbooks"].append(e)
            elif change == "reply" and rec:
                s["replies"].setdefault(rec, []).append(e)
            elif change in ("outcome", "third") and rec:
                s["outcome"][rec] = e

    # the names, the settings' while the second screener is on, else those the last draw kept
    def names(self) -> tuple[str, str]:
        s = self.settings
        if s and s["on"]:
            return s["first"] or self.first, s["name"] or self.name
        return self.first or (s["first"] if s else ""), self.name or (s["name"] if s else "")

    def by_number(self, ids) -> list[str]:
        return sorted(ids, key=lambda r: (self.numbers.get(r, 10 ** 9), sift.natural(r)))

    def stage_ids(self, stage: str) -> list[str]:
        """The stage's records in record number order."""
        return self.by_number([r for r in self.sc.ids if sift.in_stage(self.sc, self.held, r, stage)])

    def calibration(self, stage: str) -> list[str]:
        """The stage's calibration records: those the first draw kept, or before any draw the first
        of the stage's records in number order, as many as the settings say while the screener is on."""
        kept = self.st[stage]["calibration"]
        if kept is not None:
            return [r for r in kept if r in self.sc.at]
        s = self.settings
        n = s["calibration"] if s and s["on"] else 0
        return self.stage_ids(stage)[:n] if n else []

    def live(self, stage: str, draw: dict) -> list[str]:
        """A draw's records still in the stage, so one no longer there never holds it up."""
        return [r for r in (str(x) for x in draw.get("rec_ids") or [])
                if r in self.sc.at and sift.in_stage(self.sc, self.held, r, stage)]

    def drawn(self, stage: str) -> dict[str, int]:
        """Each drawn record of a stage and the draw it came in."""
        out = {}
        for d in self.st[stage]["draws"]:
            for r in d.get("rec_ids") or []:
                out.setdefault(str(r), d.get("draw"))
        return out

    def visible(self, stage: str, rec: str) -> bool:
        """Whether he can see the second screener's side of a record: it is drawn and its draw is
        unblinded, since he has decided every record of it."""
        k = self.drawn(stage).get(rec)
        return k is not None and k in self.st[stage]["unblind"]

    def pairs(self, stage: str) -> dict[str, list]:
        """Each record of an unblinded draw whose decision has come back, his decision as it stood at
        the unblinding against theirs, the agreement's own pairs once it is recorded."""
        s = self.st[stage]
        out = {}
        for d in s["draws"]:
            k = d.get("draw")
            if k in s["agreements"]:
                out.update({str(r): list(v) for r, v in (s["agreements"][k].get("pairs") or {}).items()})
                continue
            mine = s["unblind"].get(k)
            if mine is None:
                continue
            for r in self.live(stage, d):
                if r in mine and r in s["theirs"]:
                    out[r] = [mine[r][0], s["theirs"][r]["decision"]]
        return out

    def differences(self, stage: str) -> list[str]:
        """The records where the two went different ways before any discussion, one forward and the
        other rejecting, in number order."""
        return self.by_number([r for r, (a, b) in self.pairs(stage).items() if forward(a) != forward(b) and r in self.sc.at])

    def outcome(self, stage: str, rec: str) -> dict:
        """Where a difference stands: `open`, `agreed` with the decision, `third` while it waits on a
        third reviewer, or `decided` with the third reviewer's decision, from the newest line."""
        e = self.st[stage]["outcome"].get(rec)
        if e is None:
            return {"state": "open", "decision": "", "reason": "", "by": ""}
        if e.get("change") == "third":
            return {"state": "decided", "decision": sift.decision_word(e.get("decision")), "reason": str(e.get("reason") or ""),
                    "by": "third reviewer"}
        state = e.get("outcome") if e.get("outcome") in OUTCOMES else "open"
        return {"state": state, "decision": sift.decision_word(e.get("decision")) if state == "agreed" else "",
                "reason": str(e.get("reason") or "") if state == "agreed" else "", "by": str(e.get("by") or "")}

    def open_ones(self, stage: str) -> list[str]:
        return [r for r in self.differences(stage) if self.outcome(stage, r)["state"] == "open"]

    def tally(self, stage: str) -> dict:
        """The differences of a stage by where they stand."""
        out = {"all": 0, "open": 0, "agreed": 0, "third": 0, "decided": 0}
        for r in self.differences(stage):
            out["all"] += 1
            out[self.outcome(stage, r)["state"]] += 1
        return out


def stamp_line(folder, change: str, stage: str, tool: str, **rest) -> dict:
    return dict({"n": sift.next_n(folder), "at": sift.now_iso(), "act": ACT, "change": change,
                 "stage": sift.STAGE_WORDS[stage]}, **rest, tool=tool)


def add(folder, line: dict, lines: list[dict]) -> dict:
    sift.append(folder, line)
    lines.append(line)
    return line


def two_of(folder, sc, entries: list[dict] | None = None, settings=None, lines=None) -> Two:
    entries = sift.read_log(folder) if entries is None else entries
    return Two(folder, sc, sift.states(entries), lines_of(folder) if lines is None else lines, settings)


# ----------------------------------------------------------------- his side

def marks(sc, entries: list[dict], rec: str, stage: str, settings=None) -> dict:
    """What a decision of his on a record carries in the log beside it: `calibration` on a calibration
    record, and `after` discussion on a drawn record whose second decision he can see."""
    two = two_of(sc.folder, sc, entries, settings)
    out = {}
    if rec in two.calibration(stage):
        out["calibration"] = True
    if two.visible(stage, rec) and rec in two.st[stage]["theirs"]:
        out["after"] = "discussion"
    return out


def settle(sc, entries: list[dict], settings=None, tool: str = sift.TOOL) -> list[dict]:
    """The lines a screening's state now calls for, written at once: a draw unblinded once he has
    decided every one of its records, his decisions as they stand kept beside it, and a draw's
    agreement once theirs have all come back too, recorded once and for good. The caller holds the
    lock. Answers the lines written."""
    folder = sc.folder
    lines = lines_of(folder)
    two = Two(folder, sc, sift.states(entries), lines, settings)
    first, name = two.names()
    out = []
    for stage in sift.STAGES:
        s = two.st[stage]
        for d in s["draws"]:
            k = d.get("draw")
            live = two.live(stage, d)
            if not live:
                continue
            if k not in s["unblind"] and all(his(sc, two.held, r, stage) for r in live):
                mine = {r: [his(sc, two.held, r, stage), sift.state_of(sc, two.held, r, stage)["reason"]] for r in live}
                out.append(add(folder, stamp_line(folder, "unblind", stage, tool, draw=k, mine=mine), lines))
                s["unblind"][k] = mine
            if k in s["unblind"] and k not in s["agreements"] and all(r in s["theirs"] for r in live):
                pairs = {r: [s["unblind"][k][r][0], s["theirs"][r]["decision"]] for r in live if r in s["unblind"][k]}
                figures = agreement(pairs)
                line = stamp_line(folder, "agreement", stage, tool, draw=k, **figures, pairs=pairs, first=first, name=name)
                if two.settings is not None:
                    line["threshold"] = two.settings["kappa"]
                out.append(add(folder, line, lines))
                s["agreements"][k] = line
    return out


# ----------------------------------------------------------------- the draw

def waits(two: Two, stage: str, further: bool = False) -> str:
    """Why a draw at a stage cannot be made now, in one line, or empty when it can."""
    s = two.settings
    if not s or not s["on"]:
        return _w("TURNED_OFF")
    if stage == "ft" and any(not sift.state_of(two.sc, two.held, r, "ta")["decision"] for r in two.sc.ids):
        return _w("FT_WAITS")
    left = [r for r in two.calibration(stage) if not his(two.sc, two.held, r, stage)]
    if left:
        return sift_words.t("sift_server.two.calibration_left", n=len(left), stage=sift.stage_said(stage))
    if further and not offer(two, stage):
        return sift_words.t("sift_server.two.further_offered")
    return ""


def offer(two: Two, stage: str) -> bool:
    """Whether a further draw is on offer: every draw of the stage has its agreement, the newest's
    kappa is below the setting and a record is left to draw."""
    s = two.st[stage]
    if not s["draws"] or not two.settings or not two.settings["on"]:
        return False
    if any(d.get("draw") not in s["agreements"] for d in s["draws"]):
        return False
    last = s["agreements"][s["draws"][-1].get("draw")]
    k = last.get("kappa")
    return k is not None and k < two.settings["kappa"] and bool(pool_of(two, stage))


def pool_of(two: Two, stage: str) -> list[str]:
    """The records a draw takes from: the stage's, less its calibration records and those drawn
    before, in record number order."""
    skip = set(two.calibration(stage)) | set(two.drawn(stage))
    return [r for r in two.stage_ids(stage) if r not in skip]


def size_of(two: Two, stage: str) -> int:
    """How many a draw takes: the share of the stage's records beyond the calibration, rounded up."""
    n = len(two.stage_ids(stage)) - len(two.calibration(stage))
    return max(0, math.ceil(n * two.settings["share"] / 100)) if n > 0 else 0


def draw_in(two: Two, stage: str, lines: list[dict], tool: str) -> dict:
    """A draw made and logged, the caller holding the lock: the seed Sift chooses, the share, the
    calibration records, the pool and the rec_ids drawn."""
    pool = pool_of(two, stage)
    k = min(size_of(two, stage), len(pool))
    if not k:
        raise SiftError(_w("NONE_LEFT"))
    seed = random.SystemRandom().randrange(SEED_LOW, SEED_HIGH)
    drawn = two.by_number(redraw(pool, seed, k))
    first, name = two.names()
    line = stamp_line(two.folder, "draw", stage, tool, draw=len(two.st[stage]["draws"]) + 1, seed=seed,
                      share=two.settings["share"], calibration=two.calibration(stage), pool=pool, rec_ids=drawn,
                      first=first, name=name)
    add(two.folder, line, lines)
    two.st[stage]["draws"].append(line)
    if two.st[stage]["calibration"] is None:
        two.st[stage]["calibration"] = list(line["calibration"])
    return line


def draw(folder, stage, settings, further: bool = True, tool: str = sift.TOOL, wait: float | None = None) -> dict:
    """A further draw at a stage, offered when the newest draw's kappa is below the setting, taking the
    same share from the records not yet drawn, its own seed logged. The first draw is made with the
    first workbook. Answers the draw."""
    stage = sift.stage_key(stage)
    with locks.held(sift.lock_path(folder), wait):
        sc = sift.load(folder)
        entries = sift.read_log(folder)
        lines = lines_of(folder)
        two = Two(folder, sc, sift.states(entries), lines, settings)
        said = waits(two, stage, further=further and bool(two.st[stage]["draws"]))
        if said:
            raise SiftError(said)
        line = draw_in(two, stage, lines, tool)
        settle(sc, entries, settings, tool)
        return {"draw": line["draw"], "seed": line["seed"], "records": len(line["rec_ids"]), "stage": stage}


# ----------------------------------------------------------------- the workbooks

def put(ws, row: int, col: int, value, bold: bool = False, wrap: bool = True):
    """A cell written as text that stays text, a leading equals sign never read as a formula and
    the characters a workbook cannot hold taken out, wrapped and set at the top, bold where asked.
    No fill, ever."""
    from openpyxl.cell.cell import ILLEGAL_CHARACTERS_RE
    from openpyxl.styles import Alignment, Font
    cell = ws.cell(row=row, column=col)
    if value is None or value == "":
        cell.value = None
    elif isinstance(value, (int, float)) and not isinstance(value, bool):
        cell.value = value
    else:
        text = ILLEGAL_CHARACTERS_RE.sub("", str(value))[:CELL_MAX]
        cell.value = text
        cell.data_type = "s"
    cell.alignment = Alignment(wrap_text=wrap, vertical="top")
    if bold:
        cell.font = Font(bold=True)
    return cell


def height_of(texts: list[tuple[str, int]]) -> float:
    """A row's height to show its longest cell whole, by its lines at the column's width, as Excel
    does not work it out for a file it did not write."""
    lines = 1
    for text, width in texts:
        per = max(8, width - 2)
        n = sum(max(1, math.ceil(len(p) / per)) for p in str(text or "").split("\n"))
        lines = max(lines, n)
    return float(min(409, max(15, lines * 15)))


def unique_path(folder: Path, stem: str, suffix: str = ".xlsx") -> Path:
    """A new file or folder beside the screening, `stem` and then ` (2)` up when one is there, so
    nothing is ever written over."""
    path, n = folder / f"{stem}{suffix}", 2
    while path.exists():
        path, n = folder / f"{stem} ({n}){suffix}", n + 1
    return path


def guard(wb, ws_list) -> None:
    """Each sheet protected with no password, so only the cells left open take typing, and the
    workbook's sheets kept as they are."""
    from openpyxl.workbook.protection import WorkbookProtection
    for ws in ws_list:
        ws.protection.sheet = True
        ws.protection.formatColumns = False
        ws.protection.formatRows = False
    wb.security = WorkbookProtection(lockStructure=True)


def mark_sheet(wb, kind: str, stage: str, folder: Path, seeds: list, ids: list[str], choices: list[str]):
    """The sheet no one sees, which says what the workbook was made for: its kind, its stage, the
    screening's folder name, the draws' seeds and its records, with the reasons the Reason column
    offers in column D."""
    ws = wb.create_sheet(MARK_SHEET)
    rows = [("kind", kind), ("stage", stage), ("screening", folder.name), ("seeds", " ".join(str(s) for s in seeds)),
            ("made", sift.now_iso()), ("records", len(ids))]
    for i, (k, v) in enumerate(rows, 1):
        put(ws, i, 1, k, wrap=False)
        put(ws, i, 2, v, wrap=False)
    for i, rec in enumerate(ids, len(rows) + 2):
        put(ws, i, 1, rec, wrap=False)
    for i, choice in enumerate(choices, 1):
        put(ws, i, 4, choice, wrap=False)
    ws.sheet_state = "veryHidden"
    wb.properties.creator = sift.TOOL
    wb.properties.keywords = f"sift {kind} {stage} {' '.join(str(s) for s in seeds)}"
    return ws


def about_sheet(wb, title: str, question: str, stage: str, n: int, eligibility: list[str], how: str, codes: list[dict]):
    """The first sheet: the review's question, the stage, the records, the eligibility criteria from
    the plan, how to fill the workbook and the reasons at the stage, for No or for Exclude."""
    from openpyxl.styles import Font
    ws = wb.active
    ws.title = ABOUT_SHEET
    ws.column_dimensions["A"].width = 24
    ws.column_dimensions["B"].width = 90
    put(ws, 1, 1, title, bold=True, wrap=False).font = Font(bold=True, size=14)
    row = 3
    for label, value in (("Research question", question), ("Stage", sift.STAGE_WORDS[stage].capitalize()),
                         ("Records", n)):
        if value in ("", None):
            continue
        put(ws, row, 1, label, bold=True)
        put(ws, row, 2, value)
        ws.row_dimensions[row].height = height_of([(str(value), 90)])
        row += 1
    if eligibility:
        put(ws, row, 1, "Eligibility", bold=True)
        for line in eligibility:
            put(ws, row, 2, line)
            row += 1
    put(ws, row, 1, "How to fill it", bold=True)
    put(ws, row, 2, how)
    ws.row_dimensions[row].height = height_of([(how, 90)])
    row += 2
    if codes:
        put(ws, row, 1, REASONS_HEAD[stage], bold=True)
        row += 1
        put(ws, row, 1, "Code", bold=True)
        put(ws, row, 2, "Meaning", bold=True)
        row += 1
        for c in codes:
            put(ws, row, 1, c["code"])
            put(ws, row, 2, c["meaning"])
            row += 1
    return ws


def choices_of(codes: list[dict]) -> list[str]:
    """The Reason column's choices, each code and its meaning after a space."""
    return [f"{c['code']} {c['meaning']}".strip() for c in codes]


def code_of(text, codes: list[str]) -> str:
    """A reason from the workbook as its code: the code itself, or a choice that starts with a code and
    a space, the longest such code, or the words as typed when they name none."""
    t = sift.one_line(text)
    if not t or t in codes:
        return t
    hits = [c for c in codes if t.startswith(c + " ")]
    return max(hits, key=len) if hits else t[:60]


def open_cells(ws, first_row: int, last_row: int, cols: list[int]) -> None:
    from openpyxl.styles import Protection
    for row in range(first_row, last_row + 1):
        for col in cols:
            ws.cell(row=row, column=col).protection = Protection(locked=False)


def dropdown(ws, formula: str, cells: str, error: str):
    from openpyxl.worksheet.datavalidation import DataValidation
    dv = DataValidation(type="list", formula1=formula, allow_blank=True)
    dv.error = error
    dv.errorTitle = "Sift"
    dv.showErrorMessage = True
    ws.add_data_validation(dv)
    dv.add(cells)
    return dv


RECORD_COLUMNS = (("rec_id", 12), ("Title", 44), ("Authors", 28), ("Year", 7), ("Journal", 24), ("Abstract", 80),
                  ("Decision", 12), ("Reason", 34), ("Note", 36))
# how to fill the second screener's workbook, and the head of the reasons on its first sheet, in the
# stage's words (12 October)
HOW_SECOND = {
    "ta": ("On the Records sheet choose a Decision for each record, Yes or Maybe to take it on to full text or No "
           "to leave it out, a Reason when you choose No, and a Note if you wish. A row left blank is still to "
           "screen. Then send the workbook back as it is."),
    "ft": ("On the Records sheet choose a Decision for each record, Include or Exclude, a Reason when you choose "
           "Exclude, and a Note if you wish. A row left blank is still to screen. Then send the workbook back as it is."),
}
REASONS_HEAD = {"ta": "Reasons for No", "ft": "Reasons to exclude"}
# the Decision column's choices at each stage, Maybe only at title and abstract
CHOICES = {"ta": ("Yes", "Maybe", "No"), "ft": ("Include", "Exclude")}


def second_book(path: Path, sc, two: Two, stage: str, ids: list[str], codes: list[dict], question: str,
                eligibility: list[str]) -> None:
    """The second screener's workbook: the first sheet, then a row for each record with its rec_id,
    title, authors, year, journal and abstract laid out to read, then Decision, Reason and Note, the
    only cells that take typing, Decision and Reason as dropdowns. Nothing of his decisions,
    proposals or ratings goes in."""
    from openpyxl import Workbook
    from openpyxl.utils import get_column_letter
    wb = Workbook()
    words = sift.STAGE_WORDS[stage]
    about_sheet(wb, f"Second screening, {words}", question, stage, len(ids), eligibility, HOW_SECOND[stage], codes)
    ws = wb.create_sheet(RECORDS_SHEET)
    for i, (head, width) in enumerate(RECORD_COLUMNS, 1):
        put(ws, 1, i, head, bold=True, wrap=False)
        ws.column_dimensions[get_column_letter(i)].width = width
    for row, rec in enumerate(ids, 2):
        values = [rec, sift.plain(sc.cell(rec, "title")), sift.plain(sc.cell(rec, "authors")), sc.cell(rec, "year").strip(),
                  sift.plain(sc.cell(rec, "journal")), sift.plain(sc.cell(rec, "abstract"))]
        for col, value in enumerate(values, 1):
            put(ws, row, col, value)
        ws.row_dimensions[row].height = height_of([(values[1], 44), (values[2], 28), (values[5], 80)])
    last = len(ids) + 1
    ws.freeze_panes = "B2"
    choices = choices_of(codes)
    offered = CHOICES[stage]
    dropdown(ws, f'"{",".join(offered)}"', f"G2:G{last}",
             f"Choose {', '.join(offered[:-1])} or {offered[-1]}.")
    if choices:
        dropdown(ws, f"{MARK_SHEET}!$D$1:$D${len(choices)}", f"H2:H{last}", "Choose one of the reasons on the About sheet.")
    open_cells(ws, 2, last, [7, 8, 9])
    seeds = [d.get("seed") for d in two.st[stage]["draws"] if set(two.live(stage, d)) & set(ids)]
    mark = mark_sheet(wb, "second", stage, sc.folder, seeds, ids, choices)
    guard(wb, [wb[ABOUT_SHEET], ws, mark])
    wb.active = 1
    wb.save(path)


def differences_book(path: Path, sc, two: Two, stage: str, ids: list[str], codes: list[dict], question: str) -> None:
    """The differences workbook: a row for each open difference with its rec_id, title, his decision,
    reason and note, theirs, then their reply, Agree with you or Keep mine, and a note on it, the
    only cells that take typing."""
    from openpyxl import Workbook
    from openpyxl.utils import get_column_letter
    wb = Workbook()
    first, name = two.names()
    me, them = first or "First screener", name or "Second screener"
    words = sift.STAGE_WORDS[stage]
    how = (f"Each row is a record you and {me} decided differently at {words}. Choose a Reply, Agree with you to "
           f"take {me}'s decision or Keep mine to keep yours, and add a note if you wish. Then send the workbook back.")
    about_sheet(wb, f"Differences, {words}", question, stage, len(ids), [], how, codes)
    ws = wb.create_sheet(DIFFERENCES_SHEET)
    heads = (("rec_id", 12), ("Title", 44), (f"{me}: decision", 14), (f"{me}: reason", 24), (f"{me}: note", 32),
             (f"{them}: decision", 14), (f"{them}: reason", 24), (f"{them}: note", 32), ("Reply", 16), ("Reply note", 36))
    for i, (head, width) in enumerate(heads, 1):
        put(ws, 1, i, head, bold=True)
        ws.column_dimensions[get_column_letter(i)].width = width
    s = two.st[stage]
    for row, rec in enumerate(ids, 2):
        mine = sift.state_of(sc, two.held, rec, stage)
        theirs = s["theirs"].get(rec) or {}
        shown = sift.SHOWN_WORDS[stage]
        values = [rec, sift.plain(sc.cell(rec, "title")), shown.get(mine["decision"], ""), mine["reason"], mine["note"],
                  shown.get(theirs.get("decision"), ""), theirs.get("reason", ""), theirs.get("note", "")]
        for col, value in enumerate(values, 1):
            put(ws, row, col, value)
        ws.row_dimensions[row].height = height_of([(values[1], 44), (values[4], 32), (values[7], 32)])
    last = len(ids) + 1
    ws.freeze_panes = "B2"
    dropdown(ws, f'"{REPLY_WORDS["agree"]},{REPLY_WORDS["keep"]}"', f"I2:I{last}", "Choose Agree with you or Keep mine.")
    open_cells(ws, 2, last, [9, 10])
    seeds = [d.get("seed") for d in s["draws"]]
    mark = mark_sheet(wb, "differences", stage, sc.folder, seeds, ids, [])
    guard(wb, [wb[ABOUT_SHEET], ws, mark])
    wb.active = 1
    wb.save(path)


def copy_pdfs(folder: Path, book: Path, ids: list[str]) -> tuple[Path | None, int]:
    """At full text, the PDFs the run holds for the records in a workbook copied into a new folder
    beside it, each named by its rec_id. Answers the folder, None when no record has a PDF, and how
    many records have none."""
    found = [(rec, sift.pdf_path(folder, rec)) for rec in ids]
    have = [(rec, p) for rec, p in found if p is not None]
    if not have:
        return None, len(ids)
    target = unique_path(folder, f"{book.stem} PDFs", "")
    target.mkdir()
    for rec, p in have:
        shutil.copyfile(p, target / f"{rec}.pdf")
    return target, len(ids) - len(have)


def make_workbook(folder, stage, settings, question: str = "", eligibility=None, tool: str = sift.TOOL,
                  wait: float | None = None) -> dict:
    """The second screener's workbook for a stage, beside the screening: the first draw made when
    there is none yet, then every drawn record whose decision has not come back. At full text the
    PDFs of its records are copied into a folder beside it, to zip and send. Logged as a `workbook`
    line. Answers the file, its records, the PDFs' folder and how many records have no PDF."""
    stage = sift.stage_key(stage)
    folder = Path(folder)
    with locks.held(sift.lock_path(folder), wait):
        sc = sift.load(folder)
        entries = sift.read_log(folder)
        lines = lines_of(folder)
        two = Two(folder, sc, sift.states(entries), lines, settings)
        made = None
        if not two.st[stage]["draws"]:
            said = waits(two, stage)
            if said:
                raise SiftError(said)
            made = draw_in(two, stage, lines, tool)
        elif not two.settings or not two.settings["on"]:
            raise SiftError(_w("TURNED_OFF"))
        s = two.st[stage]
        ids = two.by_number([r for d in s["draws"] for r in two.live(stage, d) if r not in s["theirs"]])
        if not ids:
            raise SiftError(_w("ALL_BACK"))
        codes = sift.reasons(folder, sc)[stage]
        path = unique_path(folder, f"Second screener, {sift.STAGE_WORDS[stage]}")
        second_book(path, sc, two, stage, ids, codes, question, list(eligibility or []))
        pdfs, missing = (copy_pdfs(folder, path, ids) if stage == "ft" else (None, 0))
        add(folder, stamp_line(folder, "workbook", stage, tool, kind="second", file=path.name, rec_ids=ids,
                               seeds=[d.get("seed") for d in s["draws"]], pdfs=pdfs.name if pdfs else None), lines)
        settle(sc, entries, settings, tool)
        return {"file": path.name, "records": len(ids), "pdfs": pdfs.name if pdfs else None, "missing": missing,
                "drew": made["draw"] if made else None, "seed": made["seed"] if made else None, "stage": stage}


def make_differences(folder, stage, settings=None, question: str = "", tool: str = sift.TOOL,
                     wait: float | None = None) -> dict:
    """The differences workbook for a stage, beside the screening, of the differences still open,
    logged as a `workbook` line of kind differences. Answers the file and its records."""
    stage = sift.stage_key(stage)
    folder = Path(folder)
    with locks.held(sift.lock_path(folder), wait):
        sc = sift.load(folder)
        entries = sift.read_log(folder)
        lines = lines_of(folder)
        two = Two(folder, sc, sift.states(entries), lines, settings)
        ids = two.open_ones(stage)
        if not ids:
            raise SiftError(sift_words.t("sift_server.two.none_open", stage=sift.stage_said(stage)))
        codes = sift.reasons(folder, sc)[stage]
        path = unique_path(folder, f"Differences, {sift.STAGE_WORDS[stage]}")
        differences_book(path, sc, two, stage, ids, codes, question)
        add(folder, stamp_line(folder, "workbook", stage, tool, kind="differences", file=path.name, rec_ids=ids,
                               seeds=[d.get("seed") for d in two.st[stage]["draws"]]), lines)
        return {"file": path.name, "records": len(ids), "stage": stage}


# ----------------------------------------------------------------- taking a workbook back

def read_mark(wb) -> dict | None:
    """What a returned workbook says it was made for, from its hidden sheet, or from its properties
    and its rows when the sheet is gone, or None."""
    if MARK_SHEET in wb.sheetnames:
        ws = wb[MARK_SHEET]
        held = {}
        for row in range(1, 7):
            key = str(ws.cell(row=row, column=1).value or "").strip()
            held[key] = ws.cell(row=row, column=2).value
        ids, row = [], 8
        while True:
            v = ws.cell(row=row, column=1).value
            if v in (None, ""):
                break
            ids.append(str(v).strip())
            row += 1
        seeds = [whole(s, 0, 10 ** 9, -1) for s in str(held.get("seeds") or "").split()]
        return {"kind": str(held.get("kind") or ""), "stage": str(held.get("stage") or ""), "seeds": seeds, "ids": ids,
                "screening": str(held.get("screening") or "")}
    words = str(getattr(wb.properties, "keywords", "") or "").split()
    if len(words) >= 3 and words[0] == "sift":
        return {"kind": words[1], "stage": words[2], "seeds": [whole(s, 0, 10 ** 9, -1) for s in words[3:]], "ids": None,
                "screening": ""}
    return None


def rows_of(ws) -> list[dict]:
    """A sheet's rows below its header, each by its column's heading in lower case."""
    rows = list(ws.iter_rows(values_only=True))
    if not rows:
        return []
    head = [str(h or "").strip().lower() for h in rows[0]]
    return [{head[i]: v for i, v in enumerate(r) if i < len(head) and head[i]} for r in rows[1:]]


def text_of(value) -> str:
    if value is None:
        return ""
    if isinstance(value, float) and value.is_integer():
        return str(int(value))
    return str(value).strip()


def take_back(folder, data: bytes, filename: str = "", settings=None, tool: str = sift.TOOL,
              wait: float | None = None) -> dict:
    """A workbook Sift made, returned: the second screener's decisions, reasons and notes, or their
    replies on the differences, each taken in as a line of the log, a row left blank staying as it
    was. A workbook that is not one Sift made for this screening, its stage and draws, is refused in
    one line. A record whose draw has its agreement keeps the decision it had. Answers what it took."""
    from openpyxl import load_workbook
    folder = Path(folder)
    if not isinstance(data, (bytes, bytearray)) or len(data) > BOOK_MAX:
        raise SiftError(_w("NOT_OURS"))
    try:
        wb = load_workbook(io.BytesIO(bytes(data)), data_only=True)
    except Exception as exc:
        # a file that is no workbook, or one openpyxl cannot read for any reason, each refused alike
        raise SiftError(_w("NOT_OURS")) from exc
    mark = read_mark(wb)
    name = Path(str(filename or "")).name or "the workbook"
    with locks.held(sift.lock_path(folder), wait):
        sc = sift.load(folder)
        entries = sift.read_log(folder)
        lines = lines_of(folder)
        two = Two(folder, sc, sift.states(entries), lines, settings)
        if not mark or mark["kind"] not in KINDS or mark["stage"] not in sift.STAGES:
            raise SiftError(_w("NOT_OURS"))
        stage = mark["stage"]
        s = two.st[stage]
        seeds = {d.get("seed") for d in s["draws"]}
        drawn = two.drawn(stage)
        sheet = RECORDS_SHEET if mark["kind"] == "second" else DIFFERENCES_SHEET
        if not mark["seeds"] or not set(mark["seeds"]) <= seeds or sheet not in wb.sheetnames:
            raise SiftError(_w("NOT_OURS"))
        if mark["screening"] and mark["screening"] != folder.name:
            raise SiftError(_w("NOT_OURS"))
        rows = rows_of(wb[sheet])
        ids = mark["ids"] if mark["ids"] is not None else [text_of(r.get("rec_id")) for r in rows if text_of(r.get("rec_id"))]
        if not ids or any(r not in drawn for r in ids):
            raise SiftError(_w("NOT_OURS"))
        allowed = set(ids)
        if mark["kind"] == "second":
            out = take_decisions(folder, two, stage, rows, allowed, name, lines, tool)
            write_mirror(folder, Two(folder, sc, two.held, lines, settings))
            settle(sc, entries, settings, tool)
        else:
            out = take_replies(folder, sc, two, stage, rows, allowed, name, lines, tool)
        return dict(out, kind=mark["kind"], stage=stage, file=name)


def take_decisions(folder, two: Two, stage: str, rows: list[dict], allowed: set, name: str, lines: list[dict],
                   tool: str) -> dict:
    s = two.st[stage]
    codes = [c["code"] for c in sift.reasons(folder, two.sc)[stage]]
    drawn = two.drawn(stage)
    taken = blank = same = kept = 0
    for row in rows:
        rec = text_of(row.get("rec_id"))
        if rec not in allowed:
            continue
        word = SAID.get(text_of(row.get("decision")).lower(), "")
        if stage == "ft" and word == "maybe":
            word = ""
        if not word:
            blank += 1
            continue
        if drawn.get(rec) in s["agreements"]:
            kept += 1
            continue
        reason = code_of(row.get("reason"), codes) if word == "exclude" else ""
        note = sift.clean_note(text_of(row.get("note")))
        was = s["theirs"].get(rec)
        now = {"decision": word, "reason": reason, "note": note}
        if was and all(was[k] == now[k] for k in now):
            same += 1
            continue
        add(folder, stamp_line(folder, "decision", stage, tool, rec_id=rec, **now,
                               was={k: (was or {}).get(k, "") for k in now}, file=name), lines)
        s["theirs"][rec] = dict(now, at=sift.now_iso())
        taken += 1
    return {"taken": taken, "blank": blank, "same": same, "kept": kept}


def take_replies(folder, sc, two: Two, stage: str, rows: list[dict], allowed: set, name: str, lines: list[dict],
                 tool: str) -> dict:
    open_now = set(two.open_ones(stage))
    taken = agreed = keep = blank = passed = 0
    for row in rows:
        rec = text_of(row.get("rec_id"))
        if rec not in allowed:
            continue
        reply = REPLIES.get(text_of(row.get("reply")).lower(), "")
        if not reply:
            blank += 1
            continue
        if rec not in open_now:
            passed += 1
            continue
        note = sift.clean_note(text_of(row.get("reply note")))
        add(folder, stamp_line(folder, "reply", stage, tool, rec_id=rec, reply=reply, note=note, file=name), lines)
        taken += 1
        if reply == "agree":
            mine = sift.state_of(sc, two.held, rec, stage)
            add(folder, stamp_line(folder, "outcome", stage, tool, rec_id=rec, outcome="agreed", decision=mine["decision"],
                                   reason=mine["reason"], by="reply"), lines)
            agreed += 1
        else:
            keep += 1
        open_now.discard(rec)
    return {"taken": taken, "agreed": agreed, "keep": keep, "blank": blank, "passed": passed}


def write_mirror(folder, two: Two) -> bool:
    """`screening.second.csv` beside the CSV written afresh from the log: a row for each record the
    second screener has decided, its stage, rec_id, decision, reason, note and draw. Answers whether
    it wrote."""
    out = io.StringIO(newline="")
    writer = csv.writer(out, lineterminator="\n")
    writer.writerow(["stage", "rec_id", "decision", "reason", "note", "draw"])
    for stage in sift.STAGES:
        s = two.st[stage]
        drawn = two.drawn(stage)
        for rec in two.by_number(list(s["theirs"])):
            t = s["theirs"][rec]
            writer.writerow([sift.STAGE_WORDS[stage], rec, t["decision"], t["reason"], t["note"], drawn.get(rec, "")])
    path = Path(folder) / MIRROR_NAME
    text = out.getvalue()
    try:
        if path.read_text(encoding="utf-8") == text:
            return False
    except (OSError, UnicodeDecodeError):
        pass
    sift.write_atomic(path, text)
    return True


# ----------------------------------------------------------------- where we differ

def reason_for(sc, two: Two, rec: str, stage: str) -> str:
    """The reason a reject settled on a difference takes: his own when he rejected it, else theirs
    when it is a code of the stage or the stage has none, else refused."""
    mine = sift.state_of(sc, two.held, rec, stage)
    if mine["decision"] == "exclude" and mine["reason"]:
        return mine["reason"]
    codes = [c["code"] for c in sift.reasons(two.folder, sc)[stage]]
    theirs = (two.st[stage]["theirs"].get(rec) or {}).get("reason", "")
    if theirs in codes or not codes:
        return theirs
    raise SiftError(NO_REASON[stage]())


def settle_one(folder, rec_id, stage, outcome: str, decision=None, settings=None, tool: str = sift.TOOL,
               wait: float | None = None, ai_on: bool = False) -> dict:
    """A difference's outcome, by his hand: `agreed` with the decision, include or exclude, `third`, sent
    to a third reviewer, `open`, opened again, or `decided`, the third reviewer's decision once it
    comes. A decision of his that the outcome changes is changed by one more decision of his in the
    log, marked after discussion or after the third reviewer, saying as every decision does whether it
    matched the suggestions shown, `ai_on` the app's AI switch. Answers what every act answers."""
    if outcome not in OUTCOMES + ("decided",):
        raise SiftError(sift_words.t("sift_server.two.outcome_is"))
    folder = Path(folder)
    with locks.held(sift.lock_path(folder), wait):
        sc = sift.load(folder)
        entries = sift.read_log(folder)
        lines = lines_of(folder)
        held = sift.states(entries)
        rec, stage = sift.checked(sc, held, rec_id, stage)
        two = Two(folder, sc, held, lines, settings)
        if rec not in two.differences(stage):
            raise SiftError(_w("NOT_APART"))
        now = two.outcome(stage, rec)
        word = ""
        if outcome in ("agreed", "decided"):
            word = sift.decision_word(decision)
            if word not in ("include", "exclude"):
                raise SiftError(sift_words.t("sift_server.two.decision_is"))
        if outcome == "decided" and now["state"] != "third":
            raise SiftError(_w("NOT_THIRD"))
        reason = reason_for(sc, two, rec, stage) if word == "exclude" else ""
        if outcome == "decided":
            add(folder, stamp_line(folder, "third", stage, tool, rec_id=rec, decision=word, reason=reason), lines)
        else:
            add(folder, stamp_line(folder, "outcome", stage, tool, rec_id=rec, outcome=outcome, decision=word,
                                   reason=reason, by="discussion" if outcome == "agreed" else ""), lines)
        mine = sift.state_of(sc, held, rec, stage)
        if word and (mine["decision"], mine["reason"]) != (word, reason):
            after = "third reviewer" if outcome == "decided" else "discussion"
            sift.decide_in(sc, entries, rec, stage, word, reason, None, tool, {"after": after}, ai_on)
            sift.rebuild(sc, entries)
        return sift.settled(sc, entries, rec)


# ----------------------------------------------------------------- what the screen and the counts show

def view(folder, settings=None, sc=None, entries=None) -> dict:
    """The second screener's side as the screen shows it, blind both ways: the settings, each stage's
    calibration records, draws, how many came back and while a draw is blind how many of its records
    he has still to decide, never which way theirs went. Once a draw is unblinded its records show
    both sides, and once it has its agreement, the figures. `records` holds a calibration record's
    mark and an unblinded record's two sides, its difference and outcome and the replies."""
    sc = sift.load(folder) if sc is None else sc
    entries = sift.read_log(folder) if entries is None else entries
    lines = lines_of(folder)
    two = Two(folder, sc, sift.states(entries), lines, settings)
    s = two.settings or dict(DEFAULTS)
    first, name = two.names()
    out = {"on": s["on"], "any": bool(lines), "first": first, "name": name, "share": s["share"],
           "calibration": s["calibration"], "kappa": s["kappa"], "stages": {}, "records": {}}
    for stage in sift.STAGES:
        st = two.st[stage]
        cal = two.calibration(stage)
        draws, drawn, back, blind_left = [], [], 0, 0
        for d in st["draws"]:
            live = two.live(stage, d)
            draws.append({"draw": d.get("draw"), "seed": d.get("seed"), "share": d.get("share"), "records": len(live),
                          "unblinded": d.get("draw") in st["unblind"]})
            drawn += live
            back += sum(1 for r in live if r in st["theirs"])
            if d.get("draw") not in st["unblind"]:
                blind_left += sum(1 for r in live if not his(sc, two.held, r, stage))
        agreements = [{k: st["agreements"][d.get("draw")].get(k) for k in ("draw", "records", "alike", "proportion", "kappa", "table")}
                      for d in st["draws"] if d.get("draw") in st["agreements"]]
        pooled = None
        if len(agreements) > 1:
            pooled = agreement({r: v for d in st["draws"] if d.get("draw") in st["agreements"]
                                for r, v in (st["agreements"][d.get("draw")].get("pairs") or {}).items()})
            pooled.pop("forward", None)
        first_draw = not st["draws"]
        said = waits(two, stage) if first_draw else ""
        out["stages"][stage] = {
            "calibration": len(cal), "calibration_left": sum(1 for r in cal if not his(sc, two.held, r, stage)),
            "draws": draws, "drawn": len(drawn), "back": back, "blind_left": blind_left,
            "to_send": sum(1 for r in drawn if r not in st["theirs"]),
            "size": size_of(two, stage) if two.settings and two.settings["on"] and first_draw else None,
            # why the first draw waits, and whether it is the calibration records, which the card says already
            "waits": said, "waits_calibration": bool(said) and said not in (_w("TURNED_OFF"), _w("FT_WAITS")),
            "agreements": agreements, "pooled": pooled, "further": offer(two, stage), "differences": two.tally(stage)}
        for r in cal:
            out["records"].setdefault(r, {})[stage] = {"calibration": True}
        apart = set(two.differences(stage))
        for d in st["draws"]:
            k = d.get("draw")
            if k not in st["unblind"]:
                continue
            for r in two.live(stage, d):
                theirs = st["theirs"].get(r)
                before = (st["unblind"][k].get(r) or ["", ""])
                out["records"].setdefault(r, {})[stage] = {
                    "drawn": k, "before": {"decision": before[0], "reason": before[1] if len(before) > 1 else ""},
                    "theirs": dict(theirs) if theirs else None, "differs": r in apart,
                    "outcome": two.outcome(stage, r) if r in apart else None,
                    "replies": [{"reply": e.get("reply"), "note": e.get("note", ""), "at": e.get("at")}
                                for e in st["replies"].get(r, [])]}
    return out


def differences_of(folder, sc, stage) -> list[str]:
    """The records where the two differ at a stage, for Sift's round Where we differ."""
    return two_of(folder, sc).differences(sift.stage_key(stage))


def hidden_lines(folder, sc, entries) -> set:
    """The line numbers of the second screener's decisions he cannot see yet, which a record's history
    leaves out, blind as the screen is."""
    two = two_of(folder, sc, entries)
    out = set()
    for e in lines_of(folder):
        stage = stage_of(e)
        if stage and e.get("change") == "decision" and not two.visible(stage, str(e.get("rec_id") or "")):
            out.add(e.get("n"))
    return out


def report(folder, sc, entries=None) -> dict | None:
    """What the counts and the PRISMA flow say of the two screeners, from the log alone, or None
    with no draw: by stage the two names, the share, each draw's seed and records, the calibration
    records, the agreement and kappa before any discussion, each draw's and pooled over the stage's
    draws, and the differences, settled by discussion, decided by a third reviewer, waiting on one
    or open."""
    two = two_of(folder, sc, entries)
    if not any(two.st[stage]["draws"] for stage in sift.STAGES):
        return None
    out = {}
    for stage in sift.STAGES:
        st = two.st[stage]
        if not st["draws"]:
            continue
        agreed = [st["agreements"][d.get("draw")] for d in st["draws"] if d.get("draw") in st["agreements"]]
        pairs = {r: v for a in agreed for r, v in (a.get("pairs") or {}).items()}
        pooled = agreement(pairs) if agreed else None
        first, name = two.first, two.name
        out[stage] = {"first": first, "name": name, "share": st["draws"][0].get("share"),
                      "calibration": len(st["calibration"] or []),
                      "draws": [{"draw": d.get("draw"), "seed": d.get("seed"), "share": d.get("share"),
                                 "records": len(d.get("rec_ids") or [])} for d in st["draws"]],
                      "agreements": [{k: a.get(k) for k in ("draw", "records", "alike", "proportion", "kappa", "table")}
                                     for a in agreed],
                      "pooled": {k: pooled[k] for k in ("records", "alike", "proportion", "kappa", "table")} if pooled else None,
                      "differences": tally_logged(two, stage, pairs)}
    return out


def tally_logged(two: Two, stage: str, pairs: dict) -> dict:
    out = {"all": 0, "open": 0, "agreed": 0, "third": 0, "decided": 0}
    for r, (a, b) in pairs.items():
        if forward(a) != forward(b):
            out["all"] += 1
            out[two.outcome(stage, r)["state"]] += 1
    return out


def percent(p) -> str:
    return f"{round(p * 100)}%" if isinstance(p, (int, float)) else ""


def screeners(r: dict) -> str:
    """The two screeners as the counts and the flow name them."""
    return sift_words.t("sift_server.two.screeners", first=r['first'] or sift_words.t("sift_server.two.the_first"),
                  second=r['name'] or sift_words.t("sift_server.two.a_second"))


def count_rows(rep: dict | None) -> list[list]:
    """The rows `screening.counts.csv` adds for the two screeners, `stage,measure,count`, in the files'
    words, a name or a seed in the count column where the measure is one."""
    rows = []
    for stage, r in (rep or {}).items():
        name = sift.STAGE_WORDS[stage]
        rows += [[name, "first screener", r["first"]], [name, "second screener", r["name"]],
                 [name, "share drawn for the second screener (%)", r["share"]],
                 [name, "calibration records, screened together", r["calibration"]]]
        for d in r["draws"]:
            rows += [[name, f"draw {d['draw']} seed", d["seed"]], [name, f"draw {d['draw']} records", d["records"]]]
        many = len(r["agreements"]) > 1
        for a in r["agreements"]:
            if many:
                rows += [[name, f"draw {a['draw']} decided alike before discussion", a["alike"]],
                         [name, f"draw {a['draw']} kappa before discussion", "" if a["kappa"] is None else a["kappa"]]]
        p = r["pooled"]
        if p:
            rows += [[name, "records screened by both", p["records"]], [name, "decided alike before discussion", p["alike"]],
                     [name, "proportion decided alike before discussion", p["proportion"]],
                     [name, "kappa before discussion, going forward against reject", "" if p["kappa"] is None else p["kappa"]]]
            rows += [[name, f"first screener {a}, second screener {b}", p["table"][a][b]]
                     for a in sift.DECISIONS for b in sift.DECISIONS if stage == "ta" or "maybe" not in (a, b)]
        t = r["differences"]
        rows += [[name, "differences", t["all"]], [name, "differences settled by discussion", t["agreed"]],
                 [name, "differences decided by a third reviewer", t["decided"]],
                 [name, "differences with a third reviewer", t["third"]], [name, "differences open", t["open"]]]
    return rows


def flow_lines(r: dict) -> list[str]:
    """A stage's box of the two screeners in the PRISMA flow, line by line, kept short for a narrow
    sidebar."""
    n = sift.n_of
    w = sift.mermaid_text
    out = [w(sift_words.t("sift_server.two.flow.by", who=screeners(r)))]
    share = r["share"]
    out.append(w(sift_words.t("sift_server.two.flow.every")) if share == 100 else w(sift_words.t("sift_server.two.flow.share", share=share)))
    if r["calibration"]:
        out.append(w(sift_words.t("sift_server.two.flow.calibration", count=n(r['calibration']))))
    for d in r["draws"]:
        out.append(w(sift_words.t("sift_server.two.flow.draw", draw=d['draw'], seed=d['seed'], count=n(d['records']))))
    p = r["pooled"]
    if p:
        out.append(w(sift_words.t("sift_server.two.flow.alike", alike=p['alike'], records=p['records'], pc=percent(p['proportion']))))
        kappa = sift_words.t("sift_server.two.flow.kappa_none") if p["kappa"] is None else f"{p['kappa']:.2f}"
        out.append(w(sift_words.t("sift_server.two.flow.kappa", kappa=kappa)))
        t = r["differences"]
        out.append(w(sift_words.t("sift_server.two.flow.settled", count=n(t['agreed']))))
        out.append(w(sift_words.t("sift_server.two.flow.third", count=n(t['decided']))))
        if t["third"] or t["open"]:
            out.append(w(sift_words.t("sift_server.two.flow.still", count=n(t['third'] + t['open']))))
    return out
