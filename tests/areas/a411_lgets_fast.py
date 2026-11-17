"""Area 411: the copies follow a statement edit with less work and the same bytes (lgetsfast, 16 November 2026).

A statement edit on a longitudinal project spent about half its time carrying the edit to the LGETs: `themes.render`
walked the whole file in Python, `gets.write_at` copied it through JSON first, the workbook was read again for the
participant's timepoints after the write, and the read before it timed every line it never looked at. Now a file
JSON gives back as it is (`themes.plain_json`) is written by `json.dumps` itself, only its lines are copied to be
retimed (`gets.lines_copied`), the timepoints read before the write are kept over it (`books_kept`, `LPETS_BOOKS`),
and the read of the cases' marks leaves the times alone (`load(cited=False)`). Every file written must be byte for
byte what the old way writes.

What is checked, on two copies of the longitudinal demo as a fresh clone fills it, each worked on as a project of its
own with the clock and the History's ids frozen alike, one the new way and one with the old way put back: the same
series of writes, the app's statement edit on a board (a statement in an LGET at the last timepoint, one at the first,
the same words again, one just added and so in no LGET), the agents' `turn write` (reworded in place, a statement
added, the passage's statements moved, the added one removed) and the statements screen's save, on a participant
whose LGETs copy stands as its files do and one whose LPETs copy does, leaves every file of the two projects the same
after each step, the workbooks part for part, every board file, History chunk, copy and restore point, each file's
time in a copy's marks read as the file it is; each reword writes the LGETs file; both answer the same; and
`idiograph validate` finds the project clean. And `render` gives `json.dumps`'s text for plain data and keeps its own
walk, and its own text, for a tuple, a key that is not a string and a History inside the file."""
from __future__ import annotations

import datetime as dt_mod
import hashlib
import json
import os
import random
import re
import secrets
import shutil
import sys
import zipfile
from pathlib import Path

from . import support
from .a394_lipa_demo import as_cloned
from .support import check as said_check

ISO = re.compile(r"\d{4}-\d{2}-\d{2}[T ]\d{2}:\d{2}(:\d{2}(\.\d+)?)?([+-]\d{2}:?\d{2}|Z)?")
NS = re.compile(r"(?<![0-9a-f])1\d{18}(?![0-9a-f])")
SHA = re.compile(r"(?<![0-9a-f])[0-9a-f]{64}(?![0-9a-f])")
STAMP = re.compile(r"\d{8}-\d{4,6}(-\d+)?")
ADDED = "An added statement for the check"


def check(name, ok, detail=""):
    said_check(name, bool(ok), "" if ok else str(detail)[:700])


def old_render(value, depth: int = 0, rows: bool = False) -> str:
    """`themes.render` as it was before lgetsfast, its own walk alone."""
    inner = " " * (depth + 1)
    if isinstance(value, dict) and value:
        body = ",\n".join(f"{inner}{json.dumps(str(k), ensure_ascii=False)}: {old_render(v, depth + 1, k == 'history')}"
                          for k, v in value.items())
        return "{\n" + body + "\n" + " " * depth + "}"
    if isinstance(value, list) and value:
        body = ",\n".join(inner + (json.dumps(v, ensure_ascii=False, separators=(",", ":")) if rows
                                   else old_render(v, depth + 1)) for v in value)
        return "[\n" + body + "\n" + " " * depth + "]"
    return json.dumps(value, ensure_ascii=False)


class Frozen:
    """The clock every module reads and the random ids a History head takes, frozen alike for each run: each step one
    minute on from the last, the ids from one seeded stream. Put back as they were on leaving."""

    def __init__(self):
        real = dt_mod.datetime
        held = self

        class FrozenDT(real):
            @classmethod
            def now(cls, tz=None):
                return held.at if tz is None else held.at.astimezone(tz)

            @classmethod
            def today(cls):
                return held.at

        self.real, self.cls = real, FrozenDT

    def __enter__(self):
        self.at = self.cls(2026, 1, 1, 12, 0, 0)
        rng = random.Random(411)
        self.token = secrets.token_hex
        secrets.token_hex = lambda n=16: "".join(f"{rng.randrange(256):02x}" for _ in range(n))
        self.swapped = [m for m in list(sys.modules.values()) if getattr(m, "datetime", None) is self.real]
        for m in self.swapped:
            m.datetime = self.cls
        dt_mod.datetime = self.cls
        return self

    def tick(self):
        self.at = self.at + dt_mod.timedelta(minutes=1)

    def __exit__(self, *exc):
        secrets.token_hex = self.token
        dt_mod.datetime = self.real
        for m in list(sys.modules.values()):
            if getattr(m, "datetime", None) is self.cls:
                m.datetime = self.real
        return False


def run_times(value, now: dict, rel: str = ""):
    """A restore point's run file with each time it holds read against the file it is the time of: `now` where it is
    that file's time as it stands, `then` where it is not. Each [time, size] in a run sits under the path of its own
    file (`point`, `after`, a step's `before_stat` and `after_stat`), so the path says whose time it is. Read as
    the file whose time it is now, as the other files are, a time shared by two files written within one tick of a
    coarse clock (Windows's, about 15 ms) read as whichever came last by path, so two projects whose writes fell in
    different ticks read otherwise (Windows CI, 16 and 17 November)."""
    if isinstance(value, dict):
        # a key holding a dot or a slash is a file's path, though the file is gone since
        return {k: run_times(v, now, k if k in now or "." in k or "/" in k else rel) for k, v in value.items()}
    if isinstance(value, list):
        return [run_times(v, now, rel) for v in value]
    if isinstance(value, int) and not isinstance(value, bool) and value >= 10 ** 18:
        return "<now>" if rel and now.get(rel) == value else "<then>"
    return value


def digest(p: Path, times: dict, now: dict | None = None) -> str:
    data = p.read_bytes()
    if now is not None:
        run = run_times(json.loads(data.decode("utf-8")), now)
        return "r" + hashlib.sha256(SHA.sub("<sha>", ISO.sub("<t>", json.dumps(run, sort_keys=True))).encode()).hexdigest()
    if p.suffix == ".xlsx" or data[:4] == b"PK\x03\x04":
        # a workbook part for part, its save time apart
        h = hashlib.sha256()
        with zipfile.ZipFile(p) as z:
            for n in sorted(z.namelist()):
                if n != "docProps/core.xml":
                    h.update(n.encode() + b"\0" + z.read(n) + b"\0")
        return "x" + h.hexdigest()
    try:
        text = data.decode("utf-8")
    except UnicodeDecodeError:
        return "b" + hashlib.sha256(data).hexdigest()
    # a file's time in nanoseconds read as the file whose time it is now, so a copy's marks that follow their files
    # read otherwise than marks that do not; and a restore point's content addresses, which hash bytes holding them
    text = NS.sub(lambda m: f"<mtime {times.get(int(m.group(0)), '?')}>", ISO.sub("<t>", text))
    return "t" + hashlib.sha256(SHA.sub("<sha>", text).encode()).hexdigest()


def tree(root: Path) -> dict:
    files = [p for p in sorted(root.rglob("*")) if p.is_file() and not p.name.endswith(".lock")
             and p.name != ".DS_Store"]
    times = {p.stat().st_mtime_ns: STAMP.sub("<stamp>", p.relative_to(root).as_posix()) for p in files}
    now = {p.relative_to(root).as_posix(): p.stat().st_mtime_ns for p in files}
    out, objects = {}, []
    for p in files:
        rel = STAMP.sub("<stamp>", p.relative_to(root).as_posix())
        if rel.startswith(".idiograph-restore/objects/"):
            objects.append(digest(p, times))
            continue
        key, n = rel, 2
        while key in out:
            key, n = f"{rel}#{n}", n + 1
        out[key] = digest(p, times, now if rel.startswith(".idiograph-restore/runs/") else None)
    out[".idiograph-restore/objects/*"] = "".join(sorted(objects))
    return out


def aligned(root: Path, latest: dict) -> None:
    """Each participant's files set to the time the demo's copies saw them at, so their copies stand as their files
    do: for a participant `latest` names, the LGETs copy (the workbook at the time the LGETs saw it), for the others
    every timepoint of their LPETs."""
    want: dict = {}
    lg = json.loads((root / "idiograph-lgets.json").read_text(encoding="utf-8"))
    for case, rec in lg["cases"].items():
        book = root / case / rec["workbook"]
        want.setdefault(book, set()).add(rec["seen"]["workbook"])
        want.setdefault(book.parent / "Working" / (book.stem + ".lpets.json"), set()).add(rec["seen"]["themes"])
    for lp in root.glob("*/Working/*.lpets.json"):
        stem = lp.name[:-len(".lpets.json")]
        book = lp.parent.parent / (stem + ".xlsx")
        for tk, rec in json.loads(lp.read_text(encoding="utf-8"))["cases"].items():
            n = int(tk[1:])
            themes_file = lp.parent / (stem + (".themes.json" if n == 1 else f".themes-t{n}.json"))
            want.setdefault(book, set()).add(rec["seen"]["workbook"])
            want.setdefault(themes_file, set()).add(rec["seen"]["themes"])
    for p, seen in want.items():
        ns = (max if p.parent.name in latest or p.parent.parent.name in latest else min)(seen)
        os.utime(p, ns=(ns, ns))


def test_lgets_fast(scratch: Path):
    print("\n411. The copies follow a statement edit with less work and the same bytes: the same series of statement "
          "edits, turn writes and statements screen saves on two copies of the longitudinal demo, one the new way and "
          "one the old, leave every file the same after each step, and render keeps its own walk where it must "
          "(lgetsfast, 16 November)")
    import agent_log
    import cli
    import gets as gets_mod
    import idiograph_routes as routes
    import server as server_mod
    import themes
    from server import WorkbookError

    # ── A. render: json.dumps's text for plain data, its own walk for anything else, the same text either way
    plain = {"a": [1, 2.5, None, True, {"b": "é — \"q\"", "c": []}], "d": {}, "history": [], "e": -0.0}
    odd = [{"t": (1, 2)}, {1: "x"}, {"boards": [{"history": [{"id": 1, "state": {"a": 1}}]}]}, {"s": str}]
    falls = [not themes.plain_json(v) for v in odd]
    same_odd = all(themes.render(v) == old_render(v) for v in odd[:3])
    check("411: render gives json.dumps's text for plain data, byte for byte the old walk's, and keeps its own walk "
          "for a tuple, a key that is not a string and a History inside the file, with the old walk's text",
          themes.plain_json(plain) and themes.render(plain) == old_render(plain)
          == json.dumps(plain, ensure_ascii=False, indent=1) and all(falls) and same_odd, [falls, same_odd])

    fresh = scratch / "lgetsfast-411-clone"
    shutil.rmtree(fresh, ignore_errors=True)
    shutil.copytree(support.source("demo"), fresh, ignore=as_cloned)
    kept = (server_mod.DEMO_DIR, server_mod.SHIPPED_DEMO, os.environ.get(agent_log.PLACE), server_mod.CONFIG_PATH,
            server_mod.STATE_MEMORY)
    saved = (themes.plain_json, routes.lpets_books, routes.books_kept, gets_mod.copies_untouched)

    def old_books(path: Path) -> list[dict]:
        # `lpets_books` before lgetsfast: read every time, never kept
        return [{"case": routes.tp_label(t["n"]), "workbook": Path(path), "timepoint": t["n"], "cite": t["label"],
                 "missing": t["state"] == "none", "pets_complete": None} for t in routes.participant_timepoints(path)]

    def old_untouched(root, workbook, books=None):
        # `copies_untouched` before lgetsfast: the file read with every time and label
        try:
            data, entries = gets_mod.held_of(root, workbook, books, move=False)
        except WorkbookError:
            return {}
        held = (data or {}).get("cases") or {}
        return {e["case"]: bool(gets_mod.at_timepoint(e, gets_mod.untouched, Path(workbook), held[e["case"]]))
                for e in entries}

    def old_way(on: bool) -> None:
        if on:
            themes.plain_json = lambda value: False
            routes.lpets_books = old_books
            routes.books_kept = lambda path, before: old_books(path)
            gets_mod.copies_untouched = old_untouched
        else:
            themes.plain_json, routes.lpets_books, routes.books_kept, gets_mod.copies_untouched = saved

    try:
        server_mod.DEMO_DIR = server_mod.SHIPPED_DEMO = fresh
        os.environ[agent_log.PLACE] = str(scratch / "lgetsfast-411-agent-log.json")
        demo = server_mod.demo_lipa_dir()
        routes.fill_demo()

        def run_series(name: str, old: bool) -> tuple[dict, dict, Path]:
            root = scratch / f"lgetsfast-411-{name}"
            shutil.rmtree(root, ignore_errors=True)
            shutil.copytree(demo, root, ignore=support.leave("pristine", "source"))
            cfg = scratch / f"lgetsfast-411-{name}-config.json"
            cfg.write_text(json.dumps({"projects": [{"root": str(root)}], "interviewer": "Interviewer", "corpus": "",
                                       "gravity_reference": "", "corpus_exclude": []}), encoding="utf-8")
            server_mod.CONFIG_PATH = cfg
            server_mod.STATE_MEMORY = {"recent": []}
            routes.LPETS_BOOKS.clear()
            steps: dict = {}
            answers: dict = {}
            old_way(old)
            try:
                with Frozen() as clock:
                    routes.api_project({"root": str(root), "agents": True})
                    aligned(root, {"Hollis"})

                    def run(*args):
                        code, text, err = cli.run(["--root", str(root), "--config", str(cfg), *args, "--json"])
                        return code, (cli.unmark(json.loads(text)) if text.strip() else {}), err

                    def step(label: str, fn) -> None:
                        clock.tick()
                        out = fn()
                        answers[label] = SHA.sub("<sha>", NS.sub("<ns>", ISO.sub("<t>", json.dumps(
                            out, sort_keys=True, default=str))))
                        steps[label] = tree(root)

                    steps["start"] = tree(root)
                    for who in ("Hollis", "Nell"):
                        book = next((root / who).glob("*.xlsx"))
                        statements = {}
                        for n in sorted(set(themes.placed_sheets(book).values()) | {1}):
                            with themes.scoped(n):
                                for c in themes.read_cards(book)["cards"]:
                                    statements[c["key"]] = n
                        lg = json.loads((root / gets_mod.LGETS_FILE).read_text(encoding="utf-8"))
                        lines = lg["cases"][who]["lines"]
                        placed = sorted(k for k in statements if (lines.get(k) or {}).get("pet"))
                        last = [k for k in placed if statements[k] == max(statements.values())]
                        a = last[len(last) // 2]
                        c = next(k for k in placed if statements[k] == 1)
                        sa, ra, _ = themes.split_card_key(a)
                        sc, rc, _ = themes.split_card_key(c)

                        def now_text(key):
                            with themes.scoped(statements[key]):
                                return next(x["text"] for x in themes.read_cards(book)["cards"] if x["key"] == key)

                        def edit(key, same=False):
                            sheet, row, line = themes.split_card_key(key)
                            was = now_text(key)
                            body = {"workbook": str(book), "sheet": sheet, "row": row, "line": line,
                                    "text": was if same else was + " again", "old": was, "timepoint": statements[key]}
                            with routes.route_scope("/api/edit-statement", body):
                                return routes.api_edit_statement(body)

                        def shown(sheet, row):
                            code, d, err = run("turn", "show", who, sheet, str(row))
                            assert code == 0, err
                            return d["turns"][0]

                        def write(pairs_of):
                            t = shown(sa, ra)
                            spec = scratch / f"lgetsfast-411-{name}-turn.json"
                            spec.write_text(json.dumps({"pairs": pairs_of(t["pairs"]), "version": t["version"],
                                                        "request": "Check the copies"}), encoding="utf-8")
                            code, d, err = run("turn", "write", who, sa, str(ra), "--from", str(spec),
                                               "--tool", "Claude Code")
                            assert code == 0, (d.get("error"), err)
                            return d

                        def commit():
                            t = shown(sc, rc)
                            body = {"path": str(book), "sheet": sc, "row": rc,
                                    "pairs": [{"es": p["statement"] + (" saved" if p["key"] == c else ""),
                                               "kq": p["quote"]} for p in t["pairs"]]}
                            return routes.api_commit(body)

                        step(f"{who}: an edit of a statement in an LGET, last timepoint", lambda: edit(a))
                        step(f"{who}: an edit at the first timepoint", lambda: edit(c))
                        step(f"{who}: an edit, the same words", lambda: edit(a, same=True))
                        step(f"{who}: turn write, reworded in place", lambda: write(
                            lambda ps: [dict(p, statement=p["statement"] + " written") if p["key"] == a else p
                                        for p in ps]))
                        step(f"{who}: turn write, a statement added", lambda: write(
                            lambda ps: ps + [{"statement": ADDED, "quote": ""}]))
                        added = next(p["key"] for p in shown(sa, ra)["pairs"] if p["statement"] == ADDED)
                        statements[added] = statements[a]
                        step(f"{who}: an edit of the added statement, in no LGET", lambda: edit(added))
                        step(f"{who}: turn write, the passage's statements moved", lambda: write(
                            lambda ps: list(reversed(ps))))
                        step(f"{who}: turn write, the added statement removed", lambda: write(
                            lambda ps: [p for p in ps if not p["statement"].startswith(ADDED)]))
                        step(f"{who}: the statements screen's save, reworded", commit)
                        step(f"{who}: an edit of a statement in an LGET, again", lambda: edit(a))
                    code, valid, _err = run("validate")
                    answers["validate"] = json.dumps([code, valid], sort_keys=True, default=str)
            finally:
                old_way(False)
            return steps, answers, root

        new_steps, new_answers, new_root = run_series("new", False)
        old_steps, old_answers, _old_root = run_series("old", True)

        differ = {k: sorted(f for f in set(v) | set(old_steps.get(k, {})) if v.get(f) != old_steps.get(k, {}).get(f))
                  for k, v in new_steps.items()}
        differ = {k: v for k, v in differ.items() if v}
        check("411: the same series of writes leaves every file of the two projects the same after each step, the new "
              "way and the old: the workbooks part for part, every board file, History chunk, copy and restore point",
              len(new_steps) == len(old_steps) == 21 and not differ, differ or len(new_steps))
        check("411: and both answer every step the same", new_answers == old_answers,
              [k for k in new_answers if new_answers[k] != old_answers.get(k)])

        names = list(new_steps)
        # the statements screen's save keeps its words to the workbook, the copies taking only a History line (see
        # `api_commit`), so it is not among them
        rewords = [i for i, n in enumerate(names) if "turn write, reworded" in n or "an edit of" in n
                   or "first timepoint" in n]
        lgets_written = [names[i] for i in rewords
                         if new_steps[names[i]]["idiograph-lgets.json"] == new_steps[names[i - 1]]["idiograph-lgets.json"]]
        same_words = [n for n in names if n.endswith("the same words")]
        kept_same = all(new_steps[n]["idiograph-lgets.json"] == new_steps[names[names.index(n) - 1]]["idiograph-lgets.json"]
                        for n in same_words)
        check("411: each reword writes the LGETs file, and an edit to the same words leaves it as it is",
              rewords and not lgets_written and kept_same, [lgets_written, kept_same])
        code_valid = json.loads(new_answers["validate"])
        check("411: idiograph validate finds the project clean after the series",
              code_valid[0] == 0 and code_valid[1].get("valid") is True and not code_valid[1].get("problems"), code_valid)
    finally:
        old_way(False)
        (server_mod.DEMO_DIR, server_mod.SHIPPED_DEMO, place, server_mod.CONFIG_PATH, server_mod.STATE_MEMORY) = kept
        if place is None:
            os.environ.pop(agent_log.PLACE, None)
        else:
            os.environ[agent_log.PLACE] = place
        routes.LPETS_BOOKS.clear()
