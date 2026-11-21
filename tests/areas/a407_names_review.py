"""Area 407: names decided find by find in the review (namesbuild, Adam's design of 17 November 2026, wording A, in
place of the per-name ticks Review each and Also an ordinary word, which go with their data).

On the demo's three participants made a project, with three names the demo holds: "Will" (once with its capital, many
times as the ordinary word), "Sunday" (three times, with its capital) and "Mum" (twice with its capital, twice in lower
case). The app's Replace writes exactly the finds ticked: a capitalised find unticked is left, a lower-case find left
unless ticked, and a workbook with no ticked find stays byte for byte. An entry with a find he unticked is marked in the
list; an agent's replace replaces capitalised finds alone, leaves every find of a marked entry, counts it in its dry
run, is one record line and is undone byte for byte; an agent cannot tick or clear the mark. Adding a transcript that
holds a listed name writes only the finds ticked in its review, and a write he did not review holds the marked
entries. Old `review`, `word` and `case` keys are dropped on the next save, the key file has three columns, and no
answer, record, History or agent log line holds a real name."""
from __future__ import annotations

import base64
import hashlib
import json
import os
import re
import shutil
from pathlib import Path

import openpyxl

from . import support
from .a244_qdpx import package
from .support import check

NAMES = ("Will", "Sunday", "Mum", "Joy")


def word(w: str, flags=0):
    return re.compile(r"(?<![^\W_])" + w + r"(?![^\W_])", flags)


def text_of(book: Path) -> str:
    wb = openpyxl.load_workbook(book)
    try:
        return "\n".join(str(v) for ws in wb.worksheets for row in ws.iter_rows(values_only=True) for v in row
                         if isinstance(v, str))
    finally:
        wb.close()


def leaked(blob) -> list:
    s = blob if isinstance(blob, str) else json.dumps(blob)
    return [n for n in NAMES if word(n).search(s)]


def folders_digest(root: Path) -> dict:
    """Every file of the participants' folders but the archives and locks, by its path and digest."""
    return {p.relative_to(root).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in sorted(root.glob("P*/**/*")) if p.is_file() and "_Archive" not in p.parts
            and not p.name.endswith(".lock")}


def b64(text: str) -> str:
    return base64.b64encode(text.encode("utf-8")).decode("ascii")


def refused(fn) -> str:
    try:
        fn()
    except Exception as exc:
        return str(exc) or "refused"
    return ""


def folder_of(n: int, who: str) -> str:
    """A participant's folder name, made at run time, never written out where area 74 reads the tests for a demo's names."""
    return f"P{n} - {who}"


def memos_writes(base: Path):
    """A participant's memos files in Source, written by Replace (datalows, 21 November 2026): a file the researcher makes
    between an agent's writes is in the run's restore point and so is never taken away by its undo; each is written under
    its participant's own lock, so Working together's guard is asked and refuses one that is not his; a numbered file's
    finds read apart on the Review card under "memos 2"; and a tick lands on the find the Check showed whatever happens
    to the workbooks before it (a participant's folder gone between Check and Replace)."""
    import agent_changes
    import agent_log
    import cli
    import idiograph_routes as routes
    import names as names_mod
    import server as server_mod
    import workbook as wb_mod

    root = base / "Bees with memos"
    shutil.rmtree(root, ignore_errors=True)
    root.mkdir(parents=True)
    (root / server_mod.PROJECT_FILE).write_text(json.dumps({
        "name": "Bees with memos", "research_question": support.DEMO_QUESTION,
        "agents": {"allowed": True, "at": "2026-11-17T09:00:00+00:00"}}), encoding="utf-8")
    for n, who in enumerate(("Juno", "Mabel", "Rowan"), start=1):
        folder = root / f"P{n} - {who}"
        (folder / "Working").mkdir(parents=True)
        shutil.copy2(support.DEMO_SHIPPED / f"{who} - EN & ES.xlsx", folder / f"{who} - EN & ES.xlsx")
        for side in sorted((support.DEMO_SHIPPED / "Working").glob(f"{who} - EN & ES.*")):
            shutil.copy2(side, folder / "Working" / side.name)
    config = base / "agent-config-memos.json"
    config.write_text(json.dumps({"root": str(root), "interviewer": "Interviewer"}), encoding="utf-8")
    routes.add_project(root)
    rid = routes.project_id(root)
    rowan = root / folder_of(3, "Rowan") / "Source"
    rowan.mkdir()
    juno = root / folder_of(1, "Juno") / "Source"
    juno.mkdir()
    names_mod.save_at(root, [{"real": ["Zed"], "to": "[z]", "for": None}])

    def run(*args):
        code, out, err = cli.run(["--config", str(config), "--root", str(root), "--json", *args, "--tool", "Claude Code"])
        return code, (support.plain(json.loads(out)) if out.strip() and code == 0 else {}), err + (out if code else "")

    def restore(*files: tuple):
        for path, text in files:
            path.write_text(text, encoding="utf-8")

    def zed_in(book: Path):
        wb = openpyxl.load_workbook(book)
        done = False
        for ws in wb.worksheets:
            for row in ws.iter_rows(min_row=2):
                for c in row:
                    if isinstance(c.value, str) and len(c.value) > 20 and not done:
                        c.value = c.value + " Zed."
                        done = True
        wb.save(book)
        wb.close()

    # ── 1. the Review card tells a participant's two memos files apart, by the number and never a file's name
    for p in (rowan / "Rowan - memos.txt", rowan / "Rowan - memos 2.txt"):
        p.write_text("Zed said hello.\n", encoding="utf-8")
    shown = routes.api_names({"op": "check", "root": rid, "names_preview": True})
    places = sorted({f["where"]["interview"] for f in shown["names"]["finds"] if f["where"]["part"] == "memos"})
    check("407: a participant's two memos files read apart on the Review card, as memos and memos 2, and a find in a memos "
          "file carries no timepoint", places == ["memos", "memos 2"]
          and all("timepoint" not in f["where"] for f in shown["names"]["finds"] if f["where"]["part"] == "memos"),
          json.dumps(places))

    # ── 2. a memos file is written under its participant's lock: Working together's guard is asked, and one that is not
    # his is refused with the files as they were
    asked = []

    def guard(path):
        asked.append(Path(path).name)
        if folder_of(3, "Rowan") in str(path) or folder_of(1, "Juno") in str(path):
            raise wb_mod.WorkbookError("This participant is not yours.")

    (juno / "Juno - memos.txt").write_text("Nothing to change here.\n", encoding="utf-8")
    wb_mod.WRITE_GUARD = guard
    try:
        code, _o, err = run("names", "replace", "--note", "Replace the names", "--run", "g1")
    finally:
        wb_mod.WRITE_GUARD = None
    kept = [(rowan / "Rowan - memos.txt").read_text(encoding="utf-8"), (rowan / "Rowan - memos 2.txt").read_text(encoding="utf-8")]
    check("407: a memos file of a participant who is not his is refused by Working together's guard as a line, not an error "
          "in the middle of the run, the files as they were, and a memos file with no find asks no guard",
          code == 0 and kept == ["Zed said hello.\n", "Zed said hello.\n"] and any(n.startswith("Rowan - memos") for n in asked)
          and not any(n.startswith("Juno - memos") for n in asked),
          err[:200] + json.dumps([asked, kept]))

    # ── 3. a memos file he makes between an agent's writes is in the run's restore point, so the run's undo never takes
    # it away
    (juno / "Juno - memos.txt").write_text("Zed told Juno. Mum was there.\n", encoding="utf-8")
    code, _o, err = run("names", "add", "--real", "Hope", "--to", "[h]", "--note", "Add Hope", "--run", "mid")
    (juno / "Juno - memos 2.txt").write_text("Made by him mid-run, with Zed in it.\n", encoding="utf-8")
    code2, _o2, err2 = run("names", "replace", "--note", "Replace the names", "--run", "mid")
    mid =next((r for r in agent_changes.all_runs(root) if r.get("key") == "run:mid"), {})
    code3, dry, err3 = run("agents", "undo-run", mid.get("id", "r0"), "--dry-run")
    check("407: a memos file made by him between an agent's writes is no file the run made, and the run's undo puts it back "
          "as it stood and takes none away",
          code == 0 and code2 == 0 and f"{folder_of(1, 'Juno')}/Source/Juno - memos 2.txt" not in (mid.get("made") or [])
          and f"{folder_of(1, 'Juno')}/Source/Juno - memos 2.txt" in (mid.get("changed") or []) and code3 == 0 and dry.get("taken_away") == 0,
          err + err2 + err3 + json.dumps([mid.get("made"), mid.get("changed"), dry]))
    # the memos back as they were for what follows
    restore((juno / "Juno - memos.txt", "Zed told Juno.\n"), (juno / "Juno - memos 2.txt", "Zed again.\n"))

    # ── 4. a tick lands on the find the Check showed, a participant's folder gone between Check and Replace or not
    for who in ("Juno", "Mabel", "Rowan"):
        zed_in(next(root.glob(f"P* - {who}")) / f"{who} - EN & ES.xlsx")
    restore((rowan / "Rowan - memos.txt", "Zed said hello.\n"), (rowan / "Rowan - memos 2.txt", "Zed again.\n"),
            (juno / "Juno - memos.txt", "Nothing here.\n"), (juno / "Juno - memos 2.txt", "Nothing here either.\n"))
    seen = routes.api_names({"op": "check", "root": rid, "names_preview": True})
    memo_finds = [f for f in seen["names"]["finds"] if f["where"]["part"] == "memos"]
    target = memo_finds[0]
    shutil.rmtree(next(root.glob(folder_of(2, "*"))))
    done = routes.api_names({"op": "replace", "root": rid, "names_reviewed": True, "skip": [f"{target['entry']}:{target['nth']}"],
                             "memos_seen": seen.get("memos_seen") or []})
    check("407: a tick on a memos file's find lands on that find though a participant's folder is gone between Check and "
          "Replace, the file ticked left and the other replaced",
          (rowan / "Rowan - memos 2.txt").read_text(encoding="utf-8") == "Zed again.\n"
          and (rowan / "Rowan - memos.txt").read_text(encoding="utf-8") == "[z] said hello.\n" and done["books_changed"] >= 1,
          json.dumps([[f["nth"], f["where"]["interview"]] for f in memo_finds]) + json.dumps(done)[:200])


def test_names_review(scratch: Path):
    print("\n407. Names decided find by find in the review: Replace writes the ticked alone, lower case unticked, an "
          "entry he unticked marked and left whole by an agent's replace, Add with names reviewed first, and no real "
          "name said back (namesbuild, 17 November)")
    import agent_changes
    import agent_log
    import cli
    import idiograph_routes as routes
    import mcp_server
    import names as names_mod
    import project_history as hist_mod
    import server as server_mod

    base = scratch / "names-review-407"
    shutil.rmtree(base, ignore_errors=True)
    root = base / "Bees at home"
    root.mkdir(parents=True)
    (root / server_mod.PROJECT_FILE).write_text(json.dumps({
        "name": "Bees at home", "research_question": support.DEMO_QUESTION,
        "agents": {"allowed": True, "at": "2026-11-17T09:00:00+00:00"}}), encoding="utf-8")
    shipped = support.DEMO_SHIPPED
    for n, who in enumerate(("Juno", "Mabel", "Rowan"), start=1):
        folder = root / f"P{n} - {who}"
        (folder / "Working").mkdir(parents=True)
        shutil.copy2(shipped / f"{who} - EN & ES.xlsx", folder / f"{who} - EN & ES.xlsx")
        for side in sorted((shipped / "Working").glob(f"{who} - EN & ES.*")):
            shutil.copy2(side, folder / "Working" / side.name)
    juno, mabel, rowan = (next(root.glob(f"P{n}*")) / f"{w} - EN & ES.xlsx"
                          for n, w in ((1, "Juno"), (2, "Mabel"), (3, "Rowan")))
    cfg = base / "config.json"
    cfg.write_text(json.dumps({"projects": [], "interviewer": "Interviewer"}), encoding="utf-8")
    config = base / "agent-config.json"
    config.write_text(json.dumps({"root": str(root), "interviewer": "Interviewer"}), encoding="utf-8")
    log = base / "agent-log.json"
    kept = (server_mod.CONFIG_PATH, server_mod.ROOT_OVERRIDE, server_mod.STATE_PATH, server_mod.STATE_MEMORY,
            agent_changes.ALL_OPS, os.environ.get(agent_log.PLACE))
    outs: list[str] = []

    def run(*args, tool="Claude Code"):
        given = ["--config", str(config), "--root", str(root), "--json", *args] + (["--tool", tool] if tool else [])
        code, out, err = cli.run(given)
        outs.append(out + err)
        return code, (support.plain(json.loads(out)) if out.strip() and code == 0 else {}), err + (out if code else "")

    try:
        server_mod.CONFIG_PATH, server_mod.ROOT_OVERRIDE = cfg, None
        server_mod.STATE_PATH, server_mod.STATE_MEMORY = base / "state.json", {"recent": []}
        agent_changes.ALL_OPS = None
        os.environ[agent_log.PLACE] = str(log)
        routes.add_project(root)
        rid = routes.project_id(root)
        was = {b: text_of(b) for b in (juno, mabel, rowan)}
        count = lambda w, t, flags=0: len(word(w, flags).findall(t))
        check("407: the demo holds Will with its capital once and as the ordinary word, Sunday three times, Mum with "
              "its capital and in lower case",
              count("Will", was[mabel]) == 1 and count("will", was[juno]) >= 2 and count("Sunday", was[juno]) == 3
              and count("Mum", was[mabel]) == 2 and count("mum", was[juno]) == 2
              and not any(count(w, was[rowan], re.I) for w in ("will", "sunday", "mum")),
              json.dumps({str(b.name): [count(w, t) for w in ("Will", "will", "Sunday", "Mum", "mum")] for b, t in was.items()}))

        # ── 1. an old list's Review each, Also an ordinary word and Match case read as nothing, dropped on the next save
        listed = root / names_mod.FILE
        listed.write_text(json.dumps({"entries": [
            {"real": ["Will"], "to": "[son]", "for": None, "word": True},
            {"real": ["Sunday"], "to": "[day]", "for": None, "review": True},
            {"real": ["Mum"], "to": "[mother]", "for": None, "case": True}]}), encoding="utf-8")
        app_list = routes.api_names({"op": "list", "root": rid})
        check("407: an old entry's review, word and case keys are read as nothing",
              [sorted(e) for e in app_list["entries"]] == [["entry", "for", "real", "to"]] * 3, json.dumps(app_list)[:300])
        routes.api_names({"op": "set", "root": rid, "entries": [
            {k: v for k, v in e.items() if k != "entry"} for e in app_list["entries"]]})
        saved = json.loads(listed.read_text(encoding="utf-8"))["entries"]
        check("407: the next save writes every entry without them",
              saved == [{"real": ["Will"], "to": "[son]", "for": None}, {"real": ["Sunday"], "to": "[day]", "for": None},
                        {"real": ["Mum"], "to": "[mother]", "for": None}], json.dumps(saved))

        # ── 2. the app's check: every find in its sentence with its place, the lower-case ones marked
        app_check = routes.api_names({"op": "check", "root": rid, "names_preview": True})
        finds = app_check["names"]["finds"]
        by = lambda found: [f for f in finds if f["found"] == found]
        sun = by("Sunday")
        check("407: Check gives each find with its sentence, its passage's time and whether it is in lower case",
              len(by("Will")) == 1 and not by("Will")[0]["lower"] and len(by("will")) == count("will", was[juno]) + count("will", was[mabel])
              and all(f["lower"] for f in by("will") + by("mum")) and len(sun) == 3 and not any(f["lower"] for f in sun)
              and all(isinstance(f["where"].get("seconds"), int) for f in sun if f["where"]["part"] == "words")
              and all(f["before"] or f["after"] for f in finds) and all("\n" not in f["before"] + f["after"] for f in finds),
              json.dumps(sun)[:600])
        code, agent_check, err = run("names", "check", tool=None)
        lows = len(by("will")) + len(by("mum"))
        check("407: an agent's check counts the capitalised finds to replace and the lower-case ones left, no words",
              code == 0 and agent_check["names"]["replaced"] == 1 + 3 + 2 and agent_check["names"]["left"] == lows
              and "finds" not in agent_check["names"], err + json.dumps(agent_check)[:300])

        # ── 3. an agent cannot tick a find
        took = refused(lambda: routes.api_names({"op": "replace", "root": rid, "take": ["1:2"], "tool": "Claude Code",
                                                 "request": "x"}))
        check("407: an agent's take is refused, nothing written", bool(took) and was[juno] == text_of(juno), took)

        # ── 3b. a workbook changed between Check and Replace is left as it is, the others replaced (lowsfix)
        snap = {b: b.read_bytes() for b in (juno, mabel, rowan)}
        wb_touched = openpyxl.load_workbook(juno)
        wb_touched.save(juno)
        wb_touched.close()
        late = routes.api_names({"op": "replace", "root": rid, "names_reviewed": True,
                                 "memos_seen": app_check.get("memos_seen") or []})
        check("407: a workbook changed since Check is left as it is and said, the others still replaced",
              late["books_changed"] == 1 and text_of(juno) == was[juno] and count("Will", text_of(mabel)) == 0,
              json.dumps({k: late[k] for k in ("books_changed", "participants")}))
        for b, data in snap.items():
            b.write_bytes(data)

        # ── 4. the app's Replace writes the ticked alone: one Sunday unticked, one lower-case will ticked
        rowan_bytes = rowan.read_bytes()
        juno_will = [f for f in by("will") if f["where"]["participant"] == "Juno"]
        skip = [f"{sun[1]['entry']}:{sun[1]['nth']}"]
        take = [f"{juno_will[0]['entry']}:{juno_will[0]['nth']}"]
        done = routes.api_names({"op": "replace", "root": rid, "skip": skip, "take": take, "names_reviewed": True,
                                 "memos_seen": app_check.get("memos_seen") or []})
        now = {b: text_of(b) for b in (juno, mabel, rowan)}
        check("407: Replace writes the ticked finds: the capitalised ones but the one unticked, the one lower-case find "
              "ticked, and no other lower-case find",
              done["names"]["replaced"] == 1 + 2 + 2 + 1
              and count("Sunday", now[juno]) == 1 and now[juno].count("[day]") == was[juno].count("[day]") + 2
              and count("Will", now[mabel]) == 0 and count("Mum", now[mabel]) == 0
              and count("will", now[juno]) == count("will", was[juno]) - 1 and count("will", now[mabel]) == count("will", was[mabel])
              and count("mum", now[juno]) == 2, json.dumps(done["names"])[:400])
        check("407: a workbook with no ticked find is left byte for byte", rowan.read_bytes() == rowan_bytes)
        marked = [bool(e.get("unticked")) for e in routes.pseudo_list(root)]
        check("407: the entry with a find he unticked is marked in the list, and only that one",
              marked == [False, True, False], json.dumps(routes.pseudo_list(root)))

        # ── 5. an agent's names list shows the mark; its replace leaves every find of the marked entry, counted
        code, agent_list, err = run("names", "list", tool=None)
        code2, added, err2 = run("names", "add", "--real", "Joy", "--to", "[friend]", "--note", "Add Joy", "--run", "a1")
        check("407: names list shows the mark on the entry he unticked, and an agent's names add comes in without one",
              code == 0 and agent_list["entries"][1].get("unticked") is True and "unticked" not in agent_list["entries"][0]
              and code2 == 0 and "unticked" not in routes.pseudo_list(root)[-1], err + err2 + json.dumps(agent_list)[:300])
        before_folders = folders_digest(root)
        code, dry, err = run("names", "replace", "--note", "Replace the names", "--dry-run")
        dry_same = folders_digest(root) == before_folders
        rows_before = len(agent_changes.read(root))
        code2, rep, err2 = run("names", "replace", "--note", "Replace the names", "--run", "r1")
        after = {b: text_of(b) for b in (juno, mabel, rowan)}
        new_lines = agent_changes.read(root)[rows_before:]
        check("407: an agent's dry run counts the marked entry left and the one capitalised find it would replace, "
              "writing nothing",
              code == 0 and dry_same and dry["names"]["held"] == 1 and dry["names"]["replaced"] == 1
              and any(e["entry"] == 2 and e.get("held") for e in dry["names"]["by_entry"]), err + json.dumps(dry)[:400])
        check("407: an agent's replace writes the capitalised find alone, leaves the marked entry's find and every "
              "lower-case find, in one record line",
              code2 == 0 and rep["names"]["replaced"] == 1 and count("Joy", after[rowan]) == 0
              and count("joy", after[juno]) == count("joy", was[juno]) and count("Sunday", after[juno]) == 1
              and count("will", after[juno]) == count("will", now[juno]) and len(new_lines) == 1
              and new_lines[0]["op"] == "names replace", err2 + json.dumps(new_lines)[:400])
        code, _u, err = run("agents", "undo-change", new_lines[0]["id"], "--note", "Put it back")
        check("407: the agent's replace is undone byte for byte", code == 0 and folders_digest(root) == before_folders,
              err + json.dumps(sorted(set(folders_digest(root).items()) ^ set(before_folders.items())))[:400])

        # ── 6. no agent clears the mark; his own edit of the entry in the app does
        code, set_done, err = run("names", "set", "2", "--to", "[weekday]", "--note", "Write it as weekday", "--run", "s1")
        kept_mark = routes.pseudo_list(root)[1]
        app_now = routes.api_names({"op": "list", "root": rid})["entries"]
        routes.api_names({"op": "set", "root": rid, "entries": [{k: v for k, v in e.items() if k not in ("entry", "unticked")}
                                                                for e in app_now]})
        still = routes.pseudo_list(root)[1]
        edited = [{k: v for k, v in e.items() if k not in ("entry", "unticked")} for e in app_now]
        edited[1]["to"] = "[day]"
        routes.api_names({"op": "set", "root": rid, "entries": edited})
        cleared = routes.pseudo_list(root)[1]
        check("407: an agent's names set keeps the mark, the app's save keeps it on an entry he left as it was, and "
              "his own edit of the entry clears it",
              code == 0 and kept_mark.get("unticked") is True and kept_mark["to"] == "[weekday]"
              and still.get("unticked") is True and "unticked" not in cleared and cleared["to"] == "[day]",
              err + json.dumps([kept_mark, still, cleared]))
        names_mod.save_at(root, names_mod.with_marks(routes.pseudo_list(root), {1}))

        # ── 7. Add transcripts with names: the preview flags each find, and the Add writes the ticked alone
        said = ("Interviewer: [00:00:01] How was the week?\n"
                "Ash: [00:00:05] Will came on Sunday. I will go back, and Will said so too.\n")
        files = [{"name": "ash.txt", "data": b64(said), "pseudonym": "Ash", "interview": "Week",
                  "speakers": {"Interviewer": "interviewer", "Ash": "participant"}}]
        shown = routes.api_names({"op": "preview", "root": rid, "files": files})
        f_add = [f for f in shown["files"][0]["finds"] if f["where"].get("part") == "words"]
        wills = [f for f in f_add if f["found"].lower() == "will"]
        unreviewed = routes.api_add_transcripts({"op": "add", "root": rid, "files": files, "dry_run": True})
        reviewed = routes.api_add_transcripts({"op": "add", "root": rid, "files": files, "dry_run": True,
                                               "names_reviewed": True})
        check("407: the Add's preview flags each find, the lower-case one marked, with its passage's time and its whole "
              "sentence",
              [f["lower"] for f in wills] == [False, True, False] and all(f["where"].get("seconds") == 5 for f in f_add)
              and wills[0]["before"] == "" and wills[0]["after"] == " came on Sunday.", json.dumps(f_add)[:500])
        check("407: a write he did not review leaves every find of the marked entry, his reviewed Add none",
              unreviewed["names"]["held"] == 1 and reviewed["names"]["held"] == 0,
              json.dumps([unreviewed["names"], reviewed["names"]])[:400])
        added_ash = routes.api_add_transcripts({"op": "add", "root": rid, "files": files, "names_reviewed": True,
                                                "skip": [f"{wills[2]['entry']}:{wills[2]['nth']}"],
                                                "take": [f"{wills[1]['entry']}:{wills[1]['nth']}"]})
        ash = next(root.glob("P* - Ash"))
        ash_text = text_of(next(ash.glob("*EN & ES.xlsx")))
        check("407: the Add writes exactly the finds ticked in its review, and marks the entry he unticked",
              added_ash["added"] and "[son] came on [day]. I [son] go back, and Will said so too." in ash_text
              and routes.pseudo_list(root)[0].get("unticked") is True, ash_text[:300])

        # ── 8. the key file: three columns, and an old five-column key reads its names and its except phrases
        key = names_mod.write_key(routes.pseudo_list(root))
        old_key = names_mod.read_key("key.csv", "Real name,Pseudonym,Review each,Except in,Also an ordinary word\n"
                                                "Wilbur,[son],yes,Wilbur Road,yes\n".encode("utf-8"))
        check("407: the key file has three columns, and an old five-column key reads its names and except phrases alone",
              all(len(line.split(",")) == 3 for line in key.splitlines()[:1])
              and old_key == [{"real": ["Wilbur"], "to": "[son]", "for": None, "except": ["Wilbur Road"]}], key + json.dumps(old_key))

        # a trailing comma or a notes column never moves Except in: the old shape is known by its heading (namesfix L1)
        trailing = names_mod.read_key("key.csv", b"Wilbur,[son],Wilbur Road,\n")
        noted = names_mod.read_key("key.csv", "Real name,Pseudonym,Except in,Notes\n"
                                              "Wilbur,[son],Wilbur Road,his road\n".encode("utf-8"))
        old_four = names_mod.read_key("key.csv", b"Real name,Pseudonym,Review each,Except in\nWilbur,[son],,Wilbur Road\n")
        wilbur = [{"real": ["Wilbur"], "to": "[son]", "for": None, "except": ["Wilbur Road"]}]
        check("407: a key with a trailing comma or a notes column keeps its except phrase, and an old four-column key "
              "known by its heading reads its own",
              trailing == wilbur and noted == wilbur and old_four == wilbur, json.dumps([trailing, noted, old_four]))

        # ── 9. the per-name ticks are gone from the command line and MCP
        code, _o, err = run("names", "add", "--real", "Hope", "--to", "[daughter]", "--ordinary-word", "--dry-run")
        code2, _o2, err2 = run("names", "set", "1", "--review-each", "on", "--dry-run")
        srv = mcp_server.Server(str(root), config=str(config))
        srv.receive(json.dumps({"jsonrpc": "2.0", "id": 0, "method": "initialize",
                                "params": {"protocolVersion": "2025-06-18", "clientInfo": {"name": "claude-code"}}}))
        tools = {t["name"]: t for t in srv.receive(json.dumps({"jsonrpc": "2.0", "id": 9, "method": "tools/list"}))["result"]["tools"]}
        props = tools["names_add"]["inputSchema"]["properties"]["entries"]["items"]["properties"]
        check("407: names add --ordinary-word and names set --review-each are refused, and MCP's names_add and "
              "names_set take neither word nor review",
              code != 0 and code2 != 0 and not {"word", "review", "case"} & set(props)
              and not {"word", "review"} & set(tools["names_set"]["inputSchema"]["properties"]), err[:200] + err2[:200])

        # ── 11. an agent cannot take off an entry he unticked, so removing and adding it again never clears the mark
        # (namesfix M1)
        names_file = (root / names_mod.FILE).read_bytes()
        rows_before = len(agent_changes.read(root))
        code, _o, err = run("names", "remove", "1", "--note", "Take Will off", "--dry-run")
        code2, _o2, err2 = run("names", "remove", "1", "--note", "Take Will off", "--run", "m1")
        left_alone = (root / names_mod.FILE).read_bytes() == names_file and len(agent_changes.read(root)) == rows_before
        code3, _o3, err3 = run("names", "add", "--real", "Will", "--to", "[son]", "--note", "Add Will", "--run", "m2")
        check("407: an agent's names remove of an entry he unticked is refused in one line, dry run alike, nothing "
              "written, and its add again leaves the entry marked",
              code != 0 and code2 != 0 and left_alone
              and routes.pseudo_list(root)[0].get("unticked") is True
              and len([e for e in routes.pseudo_list(root) if e["real"] == ["Will"]]) == 1
              and len(agent_changes.read(root)) - rows_before <= (1 if code3 == 0 else 0),
              err + err2 + err3)
        (root / names_mod.FILE).write_bytes(names_file)
        code, _o, err = run("names", "remove", "4", "--note", "Take Joy off", "--dry-run")
        check("407: an agent may still remove an entry with no mark", code == 0, err)

        # an agent cannot change a marked entry's Name or In either, so set-then-add never clears the mark; its Replace
        # with stays changeable (namesfix2 L1)
        rows_before = len(agent_changes.read(root))
        tries = [run("names", "set", "1", "--real", "Wilbur", "--note", "x", "--dry-run"),
                 run("names", "set", "1", "--real", "Wilbur", "--note", "x", "--run", "l1"),
                 run("names", "set", "1", "--for", "Juno", "--note", "x", "--dry-run"),
                 run("names", "set", "1", "--for", "Juno", "--note", "x", "--run", "l1")]
        left_alone = (root / names_mod.FILE).read_bytes() == names_file and len(agent_changes.read(root)) == rows_before
        code_a, _a, err_a = run("names", "add", "--real", "Will", "--to", "[son]", "--note", "Add Will", "--run", "l2")
        wills_now = [e for e in routes.pseudo_list(root) if [s.casefold() for s in e["real"]] == ["will"]]
        code_t, to_dry, err_t = run("names", "set", "1", "--to", "[boy]", "--note", "x", "--dry-run")
        check("407: an agent's names set of a marked entry's Name or In is refused in one line, dry run alike, nothing "
              "written, so an add after it leaves the entry marked, and its Replace with stays changeable",
              all(c != 0 and len(json.loads(e)["lines"]) == 2 for c, _o, e in tries) and left_alone
              and len(wills_now) == 1 and wills_now[0].get("unticked") is True
              and code_t == 0 and to_dry["changed"]["to"]["after"] == "[boy]",
              json.dumps([e for _c, _o, e in tries]) + err_a + err_t)
        (root / names_mod.FILE).write_bytes(names_file)

        # ── 12. an import into a participant opens the same review: the read gives its finds, and the make writes
        # the ticked alone and marks an entry he unticked; an agent's import keeps the agents' rule (namesfix L3)
        said_in = ("Interviewer: [00:00:01] How was it?\n"
                   "Bay: [00:00:04] Will came on Sunday with Joy. Mum said I will stay.\n")
        bay = root / "P5 - Bay"
        bay.mkdir()
        (bay / "bay.txt").write_text(said_in.replace("Bay:", "Bay:"), encoding="utf-8")
        roles = {"Interviewer": "Interviewer", "Bay": "Participant"}
        read = routes.api_import({"op": "read", "path": str(bay / "bay.txt"), "speakers": roles, "names_preview": True})
        bay_finds = [f for f in read["names"]["finds"] if f["where"].get("part") == "words"]
        plain = routes.api_import({"op": "read", "path": str(bay / "bay.txt"), "speakers": roles})
        by_found = {f["found"]: f for f in bay_finds}
        check("407: the import card's read for its review gives each find with its sentence, time and number, the "
              "lower-case one marked, and a plain read none",
              sorted(by_found) == ["Joy", "Mum", "Sunday", "Will", "will"] and by_found["will"]["lower"]
              and all(f["where"].get("seconds") == 4 for f in bay_finds) and "names" not in plain
              and len(read["names"]["list"]) == len(routes.pseudo_list(root)), json.dumps(bay_finds)[:500])
        pick = lambda f: f"{f['entry']}:{f['nth']}"
        routes.api_import({"op": "make", "path": str(bay / "bay.txt"), "speakers": roles, "names_reviewed": True,
                           "skip": [pick(by_found["Mum"])], "take": [pick(by_found["will"])]})
        bay_text = text_of(bay / "bay.xlsx")
        check("407: the import's make writes exactly the finds ticked, a marked entry's too, and marks the entry he "
              "unticked",
              "[son] came on [day] with [friend]. Mum said I [son] stay." in bay_text
              and routes.pseudo_list(root)[2].get("unticked") is True, bay_text[:300])
        fen = root / "P6 - Fen"
        fen.mkdir()
        (fen / "fen.txt").write_text(said_in.replace("Bay:", "Fen:"), encoding="utf-8")
        code, _o, err = run("import", str(fen / "fen.txt"), "--speakers", "Interviewer=Interviewer,Fen=Participant",
                            "--note", "Import Fen", "--run", "i1")
        # its answer shows the first passages as written, the names it left among them, so its names part alone is
        # swept below (namesfix2)
        outs.pop()
        outs.append(json.dumps(_o.get("names")))
        fen_text = text_of(fen / "fen.xlsx") if (fen / "fen.xlsx").exists() else ""
        check("407: an agent's import replaces the capitalised finds of an entry with no mark alone, every find of a "
              "marked entry and every lower-case find left",
              code == 0 and "Will came on Sunday with [friend]. Mum said I will stay." in fen_text, err + fen_text[:300])

        # ── 13. a REFI-QDA import opens the same review: its read gives the finds, its make writes the ticked alone
        qtext = "Kit: What happened?\nLark: Will came on Sunday with Joy. Mum said I will stay.\n"
        qsrc = '<TextSource guid="t1" name="Lark interview" plainTextPath="internal://t1.txt"></TextSource>'
        (base / "lark.qdpx").write_bytes(package("ATLAS.ti 23.2", "", qsrc, {"Sources/t1.txt": qtext.encode("utf-8")}))
        asks = {"sources": [{"source": 1, "pseudonym": "Lark"}]}
        q_read = routes.qdpx_import(root, base / "lark.qdpx", dict(asks, names_preview=True, names_reviewed=True))
        q_finds = {f["found"]: f for f in q_read["names"]["finds"] if f["where"].get("part") == "words"}
        check("407: a REFI-QDA read for the review gives each find with its sentence and number, and the list",
              sorted(q_finds) == ["Joy", "Mum", "Sunday", "Will", "will"] and q_finds["Will"]["after"].startswith(" came on")
              and q_read["names"]["list"], json.dumps(q_finds)[:400])
        routes.qdpx_import(root, base / "lark.qdpx", dict(asks, names_reviewed=True, skip=[pick(q_finds["Joy"])],
                                                          take=[pick(q_finds["will"])]), make=True)
        lark = next(root.glob("P* - Lark"))
        lark_text = text_of(next(lark.glob("*EN & ES.xlsx")))
        check("407: the REFI-QDA import writes exactly the finds ticked in its review, and marks the entry he unticked",
              "[son] came on [day] with Joy. [mother] said I [son] stay." in lark_text
              and routes.pseudo_list(root)[3].get("unticked") is True, lark_text[:300])

        # ── 15. Add transcripts with a REFI-QDA file, in a project made in a folder that holds a list already: the mark his review writes
        # stays, and an agent's replace then leaves that entry's finds (namesfix2 M1)
        hives = base / "Hives"
        hives.mkdir()
        (hives / server_mod.PROJECT_FILE).write_text(json.dumps({
            "name": "Hives", "agents": {"allowed": True, "at": "2026-11-17T09:00:00+00:00"}}), encoding="utf-8")
        names_mod.save_at(hives, [{"real": ["Will"], "to": "[son]", "for": None},
                                  {"real": ["Joy"], "to": "[friend]", "for": None}])
        htext = "Kit: What happened?\nWren: Will came on Sunday with Joy. Then Joy said I will stay.\n"
        hsrc = '<TextSource guid="t1" name="Wren interview" plainTextPath="internal://t1.txt"></TextSource>'
        hpkg = package("ATLAS.ti 23.2", "", hsrc, {"Sources/t1.txt": htext.encode("utf-8")})
        (base / "wren.qdpx").write_bytes(hpkg)
        hasks = {"sources": [{"source": 1, "pseudonym": "Wren"}]}
        h_read = routes.qdpx_import(hives, base / "wren.qdpx", dict(hasks, names_preview=True, names_reviewed=True))
        joys = [f for f in h_read["names"]["finds"] if f["where"].get("part") == "words" and f["found"] == "Joy"]
        held_key = routes.qdpx_hold({"name": "wren.qdpx", "data": base64.b64encode(hpkg).decode("ascii")})
        hives_made = routes.make_project({"folder": str(hives), "name": "Hives", "files": []})
        routes.api_qdpx(dict(hasks, op="make", held=held_key, root=hives_made["project"]["id"], names_reviewed=True,
                             skip=[pick(joys[1])]))
        hives_list = routes.pseudo_list(hives)
        wren_book = next(next(hives.glob("P* - Wren")).glob("*EN & ES.xlsx"))
        made_text = text_of(wren_book)
        cfg_h = base / "agent-config-hives.json"
        cfg_h.write_text(json.dumps({"root": str(hives), "interviewer": "Interviewer"}), encoding="utf-8")
        code, out_h, err_h = cli.run(["--config", str(cfg_h), "--root", str(hives), "--json", "names", "replace",
                                      "--note", "Replace the names", "--run", "h1", "--tool", "Claude Code"])
        outs.append(out_h + err_h)
        after_text = text_of(wren_book)
        check("407: New project with a REFI-QDA file in a folder holding a list keeps the mark his review wrote, and an "
              "agent's replace afterwards leaves that entry's finds",
              len(joys) == 2 and [e.get("unticked") for e in hives_list] == [None, True]
              and "[son] came on Sunday with [friend]. Then Joy said I will stay." in made_text
              and code == 0 and "Then Joy said" in after_text and routes.pseudo_list(hives)[1].get("unticked") is True,
              json.dumps(hives_list) + made_text[:300] + err_h)

        # ── 16. a participant's memos files in Source: lock, restore point, place on the card and numbering (datalows)
        memos_writes(base)

        # ── 14. a find after a title shows its whole sentence, and one find left says so in the singular (namesfix)
        check("407: a find's sentence cut inside a quotation shows its quotation marks balanced, or none (namesfix2)",
              names_mod.sentence('"So it went. It comes back on a Sunday night, chucking it down"', 32, 38)
              == ("It comes back on a ", " night, chucking it down")
              and names_mod.sentence('She said "Sunday is fine" and left.', 10, 16) == ('She said "', ' is fine" and left.')
              and names_mod.sentence('“Come Sunday.” Then he left.', 6, 12) == ("“Come ", ".”"))
        check("407: a title's full stop ends no sentence",
              names_mod.sentence("He went. Then Dr. Ann came.", 18, 21) == ("Then Dr. ", " came.")
              and names_mod.sentence("Dr. Ann came.", 4, 7) == ("Dr. ", " came."))
        one = names_mod.lines({"by_entry": [{"entry": 1, "to": "[x]", "in": [], "held": True, "left": 1, "lower": 0},
                                            {"entry": 2, "to": "[y]", "in": [], "lower": 1, "left": 1}]})
        check("407: one find left is said in the singular", "1 left as it is" in one[1] and "1 in lower case left as it is" in one[3],
              json.dumps(one))

        # ── 10. nothing said back anywhere: the answers, the record, History's names lines and the agent log
        agent_log.flush()
        log_text = log.read_text(encoding="utf-8") if log.exists() else ""
        record = (root / agent_changes.FILE).read_text(encoding="utf-8")
        history = json.dumps([h for h in hist_mod.load(root) if str(h.get("op") or "").startswith("names")])
        check("407: no answer, record line, History line of the names or agent log line holds a real name",
              not leaked(" ".join(outs)) and not leaked(record) and not leaked(log_text) and not leaked(history),
              str(leaked(" ".join(outs))) + str(leaked(record)) + str(leaked(log_text)) + str(leaked(history)))
    finally:
        (server_mod.CONFIG_PATH, server_mod.ROOT_OVERRIDE, server_mod.STATE_PATH, server_mod.STATE_MEMORY,
         agent_changes.ALL_OPS, place) = kept
        if place is None:
            os.environ.pop(agent_log.PLACE, None)
        else:
            os.environ[agent_log.PLACE] = place
