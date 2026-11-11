from __future__ import annotations

import json
import re
import shutil
from pathlib import Path

import rounds as rounds_mod
from workbook import WorkbookError

from . import support
from .support import check, demo_copy, skip
import idiograph_routes


def test_phase_complete_and_settings(scratch):
    print("\n53. The experiential statements phase complete (112), and Settings by scope (116)")
    import subprocess
    import make_demo
    import server as server_mod

    page = support.page_text()
    app = support.text("family/static/shell.js", "apps/idiograph/static/distil.js")
    fn = lambda src, name: src.split(f"function {name}(", 1)[1].split("\n}", 1)[0]

    # ── A. the record: `complete` in the progress file, and nothing else written
    root = scratch / "complete"
    work = demo_copy(root, "Juno", "Juno - EN & ES.xlsx")
    side = rounds_mod.progress_path(work)
    seeded = rounds_mod.load_progress(work)
    seeded["rows"] = {"Initial:3": "reviewed-empty"}
    seeded["flags"] = ["Initial:3"]
    rounds_mod.save_progress(work, seeded)
    old = side.read_bytes()
    book = work.read_bytes()
    check("112: an old progress file, with no mark in it, reads as not complete",
          rounds_mod.complete_at(rounds_mod.load_progress(work)) is None
          and rounds_mod.complete_of(work) is None and "complete" not in json.loads(old))
    check("112: anything but a time in the shape reads as not complete too",
          all(rounds_mod.complete_at(p) is None for p in (None, {}, {"complete": "yes"}, {"complete": {"at": 5}},
                                                          {"complete": {"at": " "}}, {"complete": None}))
          and rounds_mod.complete_at({"complete": {"at": "2026-10-03T14:05:00"}}) == "2026-10-03T14:05:00")
    saved = (server_mod.ROOT_OVERRIDE, server_mod.STATE_PATH, server_mod.CONFIG_PATH, server_mod.STATE_MEMORY)
    server_mod.ROOT_OVERRIDE = str(root)
    server_mod.STATE_PATH = scratch / "complete-state.json"
    server_mod.STATE_MEMORY = None
    try:
        check("112: the route is there", server_mod.ROUTES.get("/api/complete") is idiograph_routes.api_complete)
        answer = idiograph_routes.api_complete({"workbook": str(work), "op": "mark"})
        after = json.loads(side.read_text(encoding="utf-8"))
        at = answer["complete"]
        check("112: /api/complete marks the case with the time, in the shape {\"at\": ...}",
              isinstance(at, str) and re.match(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}$", at)
              and after.get("complete") == {"at": at}, str(after.get("complete")))
        check("112: and writes nothing else, not another key of the progress file and never the workbook",
              {k: v for k, v in after.items() if k != "complete"} == json.loads(old) and work.read_bytes() == book)
        check("112: the summary the server sends carries it", answer["progress"]["complete"] == at
              and idiograph_routes.refresh_summary(work)["complete"] == at and idiograph_routes.case_payload(work)["progress"]["complete"] == at)
        again = idiograph_routes.api_complete({"path": str(work), "op": "mark"})
        check("112: marking a case already marked keeps the time it was first marked",
              again["complete"] == at and json.loads(side.read_text(encoding="utf-8"))["complete"] == {"at": at})
        progress = rounds_mod.load_progress(work)
        progress["rows"]["Initial:5"] = rounds_mod.REVIEWED_EMPTY
        rounds_mod.save_progress(work, progress)
        check("112: a save of the progress file for anything else keeps the mark where it was",
              rounds_mod.complete_of(work) == at)
        del progress["rows"]["Initial:5"]
        rounds_mod.save_progress(work, progress)

        # the rows of the case list, Recent among them, carry the mark, through what they already fetch
        plain = demo_copy(root, "Plain", "Plain - EN & ES.xlsx")
        server_mod.save_state({"recent": [{"path": server_mod.rel_path(work), "name": work.stem, "case": "Juno", "opened": 1}]})
        listed = idiograph_routes.api_cases({})
        rows = {Path(c["path"]).name: c for c in listed["cases"]}
        check("112: a marked case's row carries the time, an unmarked one carries none",
              rows[work.name]["complete"] == at and rows[plain.name]["complete"] is None, str({k: v.get("complete") for k, v in rows.items()}))
        check("112: and so does its entry in the recent list", listed["recent"] and listed["recent"][0]["complete"] == at)
        check("112: the demo's card carries the key too", "complete" in (idiograph_routes.demo_entry() or {"complete": None}))

        before_reopen = side.read_bytes()
        shut = idiograph_routes.api_complete({"workbook": str(work), "op": "reopen"})
        check("112: reopen clears the record and the file is byte for byte what it was before the mark",
              shut["complete"] is None and shut["progress"]["complete"] is None and side.read_bytes() == old
              and before_reopen != old and work.read_bytes() == book)
        stamp = side.stat().st_mtime_ns
        idiograph_routes.api_complete({"workbook": str(work), "op": "reopen"})
        check("112: reopening a case that is not marked writes nothing", side.stat().st_mtime_ns == stamp and side.read_bytes() == old)
        refused = []
        for body in ({"workbook": str(work), "op": "toggle"}, {"workbook": str(work)}):
            try:
                idiograph_routes.api_complete(body)
            except WorkbookError as exc:
                refused.append(str(exc))
        check("112: an op other than mark or reopen is refused with a line, and nothing written",
              len(refused) == 2 and all("marked complete or reopened" in r for r in refused) and side.read_bytes() == old)
        try:
            idiograph_routes.api_complete({"workbook": str(scratch / "elsewhere.xlsx"), "op": "mark"})
            outside = False
        except server_mod.OutsideRoot:
            outside = True
        check("112: a workbook outside the case root is refused", outside)
        bare = demo_copy(root, "Bare", "Bare - EN & ES.xlsx")
        idiograph_routes.api_complete({"workbook": str(bare), "op": "mark"})
        made = json.loads(rounds_mod.progress_path(bare).read_text(encoding="utf-8"))
        check("112: a case with no progress file yet gets one holding the mark alone, which reads as before",
              list(made) == ["complete"] and rounds_mod.load_progress(bare)["rows"] == {}
              and idiograph_routes.refresh_summary(bare)["complete"] == made["complete"]["at"])
        broken = demo_copy(root, "Broken", "Broken - EN & ES.xlsx")
        rounds_mod.progress_path(broken).parent.mkdir(parents=True, exist_ok=True)
        rounds_mod.progress_path(broken).write_text("{not json", encoding="utf-8")
        try:
            idiograph_routes.api_complete({"workbook": str(broken), "op": "mark"})
            kept = False
        except WorkbookError:
            kept = rounds_mod.progress_path(broken).read_text(encoding="utf-8") == "{not json"
        check("112: a progress file that cannot be read is refused and never written over", kept)
        check("112: the list reads such a file as not complete rather than failing",
              rounds_mod.complete_of(broken) is None
              and {Path(c["path"]).name: c for c in idiograph_routes.api_cases({})["cases"]}[broken.name]["complete"] is None)

        # aiout (11 November 2026): the PETs category's limit went with New AI board, and a file that holds one keeps it
        server_mod.CONFIG_PATH = scratch / "complete-config.json"
        server_mod.CONFIG_PATH.write_text(json.dumps({"interviewer": "Adam", "themes": {"cap": 5}}), encoding="utf-8")
        wrote = server_mod.api_settings({"interviewer": "Adam", "themes": {"cap": 7}})
        on_disk = json.loads(server_mod.CONFIG_PATH.read_text(encoding="utf-8"))
        check("116, aiout: a Save no longer writes a limit, the file's left as it was, and the bar's AI state has none",
              on_disk["themes"] == {"cap": 5} and "cap" not in wrote["ai"])
    finally:
        (server_mod.ROOT_OVERRIDE, server_mod.STATE_PATH, server_mod.CONFIG_PATH, server_mod.STATE_MEMORY) = saved

    # ── Reset demo clears the mark with the rest
    where = scratch / "complete-demo"
    kept_paths = (make_demo.CASE, make_demo.WORKBOOK, make_demo.PRISTINE)
    # the suite's fixture in a pristine copy's shape, Juno's with no mark (support.DEMO_PRISTINE)
    shutil.copytree(support.DEMO_PRISTINE, where / "pristine")
    make_demo.CASE = where / "Juno"
    make_demo.WORKBOOK = make_demo.CASE / "Juno - EN & ES.xlsx"
    make_demo.PRISTINE = where / "pristine"
    try:
        demo_copy(where, "Juno", "Juno - EN & ES.xlsx")
        rounds_mod.set_complete(make_demo.WORKBOOK, True)
        marked = rounds_mod.complete_of(make_demo.WORKBOOK)
        make_demo.reset()
        pristine = json.loads((make_demo.PRISTINE / "Working" / rounds_mod.progress_path(make_demo.WORKBOOK).name).read_text(encoding="utf-8"))
        check("112: Reset demo clears the mark with the rest, the pristine progress file carrying none",
              marked and rounds_mod.complete_of(make_demo.WORKBOOK) is None and "complete" not in pristine)
    finally:
        make_demo.CASE, make_demo.WORKBOOK, make_demo.PRISTINE = kept_paths

    # ── B. the page: the bar, the cards and the rows
    keys = support.keydown_text(app)
    check("112: Enter on the case-complete card marks, and Enter on the card the line opens reopens",
          "if (!$('round-done').hidden && !$('done-mark').hidden && e.key === 'Enter' && !MOD(e)) {" in keys
          and "markComplete('mark'); return;" in keys
          and "if (!$('complete').hidden && e.key === 'Enter' && !MOD(e)) { e.preventDefault(); reopenComplete(); return; }" in keys
          and keys.index("reopenComplete(); return;") < keys.index("if (anyOverlayOpen()) return;"))
    marker = fn(app, "markComplete")
    check("112: the mark goes to /api/complete with the workbook and the op, the timepoint too in a project of two "
          "or more (20 October), and nothing else is called",
          "await api('/api/complete', { workbook: path, op, ...(tp ? { timepoint: tp.n } : {}) });" in marker and "/api/commit" not in marker
          and "/api/round-complete" not in marker and "$('done-mark').onclick = () => markComplete('mark');" in app
          and "$('rail-markable').onclick = () => markComplete('mark');" in app)
    check("112: a server from before the mark offers neither the control nor the button",
          "const known = p.complete !== undefined;" in fn(app, "drawMark") and "const known = p.complete !== undefined;" in fn(app, "drawDoneMark")
          and "needsRestart(err) ? RESTART_LINE : err.message" in marker)
    check("112: a save on the last turn of a round already recorded moves on with no card while the case is marked",
          "const again = !!(tally && tally.recorded);" in fn(app, "afterCommit"))

    # ── C. in node: the bar's four states, the card and the date
    node = shutil.which("node")
    if not node:
        skip("112: the bar and the card in node", "no node on this machine")
    else:
        months = support.i18n_js()
        day_line = next(line for line in app.splitlines() if line.startswith("const dayOf = "))
        # with Work in rounds ticked, where the round text stands beside the mark (15 October)
        source = "\n".join([months, "function whenOf(" + fn(app, "whenOf") + "\n}", day_line, "\n".join(ln for ln in app.splitlines() if ln.startswith(("function roundsOn(", "function roundsHere("))),
                            "function drawMark(" + fn(app, "drawMark") + "\n}",
                            "function drawDoneMark(" + fn(app, "drawDoneMark") + "\n}"])
        script = scratch / "complete-check.js"
        script.write_text(
            "const els = {};\n"
            "const $ = (id) => els[id] || (els[id] = { id, textContent: '', innerHTML: '', title: '', hidden: false,\n"
            "  classList: { on: new Set(), toggle(c, v) { if (v) this.on.add(c); else this.on.delete(c); } } });\n"
            "$('rail-round').textContent = '3'; $('rail-rounds').textContent = '3';\n"
            "const S = { data: { progress: null, config: { work_in_rounds: true } } };\n"
            + source + "\n"
            "const view = () => ({ mark: !$('rail-mark').hidden, markable: !$('rail-markable').hidden,\n"
            "  counts: !$('rail-place').hidden && !$('rail-round-item').hidden,\n"
            "  sep: !$('rail-mark-sep').hidden, daily: !$('rail-daily').hidden, gone: $('work').classList.on.has('es-complete'),\n"
            "  undecided: $('rail-mark').classList.on.has('undecided'), left: $('rail-mark-left').innerHTML.replace(/<[^>]+>/g, ''),\n"
            "  date: $('rail-mark-date').textContent, title: $('rail-mark').title, ctl: $('rail-markable').title });\n"
            "const n = (done) => ({ caseDone: done, caseTotal: 39, roundDone: 5, roundTotal: 5 });\n"
            "const at = '2026-10-03T14:05:00';\n"
            "const out = {};\n"
            "drawMark(n(37), { complete: null }); out.open = view();\n"
            "drawMark(n(39), { complete: null }); out.ready = view();\n"
            "drawMark(n(39), { complete: at }); out.marked = view();\n"
            "drawMark(n(37), { complete: at }); out.back = view();\n"
            "drawMark(n(38), { complete: at }); out.one = view();\n"
            "drawMark(n(39), {}); out.old = view();\n"
            "const card = () => ({ offer: !$('done-mark').hidden, said: $('done-marked').hidden ? '' : $('done-marked').textContent,\n"
            "  libFilled: $('done-library').classList.on.has('primary') && !$('done-library').classList.on.has('ghost') });\n"
            "S.data.progress = { complete: null }; drawDoneMark(true); out.cardOffer = card();\n"
            "S.data.progress = { complete: at }; drawDoneMark(true); out.cardMarked = card();\n"
            "S.data.progress = {}; drawDoneMark(true); out.cardOld = card();\n"
            "S.data.progress = { complete: null }; drawDoneMark(false); out.cardRound = card();\n"
            "out.when = whenOf(at); out.none = whenOf(''); out.jan = dayOf('2027-01-09T08:00:00');\n"
            "console.log(JSON.stringify(out));\n", encoding="utf-8")
        run = subprocess.run([node, str(script)], capture_output=True, text=True, encoding="utf-8")
        if run.returncode != 0:
            check("112: the bar and the card run in node", False, run.stderr.strip()[:300])
        else:
            out = json.loads(run.stdout)
            check("112: in node, with turns undecided and no mark the bar is the bar it was",
                  out["open"]["counts"] and not out["open"]["mark"] and not out["open"]["markable"] and out["open"]["daily"]
                  and not out["open"]["gone"], str(out["open"]))
            check("112: in node, every turn decided and not marked, the counts give way to the one control, the numbers in its tooltip",
                  out["ready"]["markable"] and not out["ready"]["counts"] and not out["ready"]["mark"] and out["ready"]["daily"]
                  and "39 of 39 passages decided" in out["ready"]["ctl"], str(out["ready"]))
            check("112: in node, marked, the tick, the words and the date in their place, the line and the target gone, the numbers in the tooltip",
                  out["marked"]["mark"] and not out["marked"]["counts"] and not out["marked"]["markable"] and not out["marked"]["daily"]
                  and out["marked"]["gone"] and out["marked"]["date"] == "3 Oct 2026" and not out["marked"]["undecided"]
                  and "marked complete on 3 Oct 2026 at 14:05" in out["marked"]["title"] and "39 of 39 passages decided" in out["marked"]["title"],
                  str(out["marked"]))
            check("112: in node, a turn undecided while marked keeps the mark and brings the counts back beside it",
                  out["back"]["mark"] and out["back"]["counts"] and out["back"]["sep"] and out["back"]["undecided"]
                  and out["back"]["left"] == " · 2 passages undecided" and out["back"]["date"] == "" and not out["back"]["gone"]
                  and out["one"]["left"] == " · 1 passage undecided" and "2 passages undecided" in out["back"]["title"], str(out["back"]))
            check("112: in node, a server from before the mark leaves the round text as it was, with no control",
                  out["old"]["counts"] and not out["old"]["markable"] and not out["old"]["mark"], str(out["old"]))
            check("112: in node, an old server's card and a round's card offer nothing",
                  not out["cardOld"]["offer"] and out["cardOld"]["libFilled"] and not out["cardRound"]["offer"])
            check("112: in node, the date reads 3 Oct 2026 and the time 14:05, with no time zone brought in",
                  out["when"] == {"day": "3 Oct 2026", "time": "14:05"} and out["none"] == {"day": "", "time": ""}
                  and out["jan"] == "9 Jan 2027", str(out["when"]))

    # ── D. Settings by scope
    card = page.split('<div class="overlay" id="settings"', 1)[1].split('<div class="overlay"', 1)[0]
    # Idiograph's keys of the card in its own hook since the fifth build (23 October 2026)
    saver = fn(app, "distilSettingsBody")
    check("116, aiout: the PETs category has no limit's stepper and Save sends none",
          "capNow" not in saver and "themes" not in saver and "set-cap" not in app and "set-cap" not in card and "capStep" not in app)
