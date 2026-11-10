from __future__ import annotations

import csv
import json
import re
import shutil

from . import support
from .support import check, line_of_js, refusal_of, skip


@support.as_app("sift")
def test_sift_steps(scratch):
    print("\n122. Sift's steps from use, 12 October: one row of steps, PRISMA flow beside Set columns, the flow's sidebar "
          "dragged wider, the shared width, the decisions' colours in the filters, the charts' tips, a click to open, "
          "Back and Forward, and Maybe's hover")
    import subprocess
    import server as server_mod
    import sift_routes
    import sift

    page = support.page_text()
    sjs = support.text("apps/sift/static/sift.js")
    ssjs = support.text("apps/sift/static/sift_search.js")
    app = support.text("family/static/shell.js", "apps/idiograph/static/distil.js")
    fn = lambda src, name: src.split(f"function {name}(", 1)[1].split("\n}", 1)[0] if f"function {name}(" in src else ""
    whole = lambda src, name: f"function {name}(" + fn(src, name) + "\n}"
    node = shutil.which("node")
    base = scratch / "sift-steps-122"
    shutil.rmtree(base, ignore_errors=True)
    base.mkdir(parents=True)
    lead = app[app.index("const esc = "):app.index("// a line from the server with a command in backticks")]

    def ferries(folder: Path, n: int = 6) -> Path:
        """An invented screening on ferry crossings, years 2016 to 2021, half proposed for inclusion."""
        folder.mkdir(parents=True, exist_ok=True)
        with open(folder / sift.CSV_NAME, "w", encoding="utf-8", newline="") as fh:
            w = csv.writer(fh)
            w.writerow(["rec_id", "title", "authors", "year", "journal", "doi", "sources", "abstract", "proposed_decision",
                        "proposed_reason", "grounds"])
            for i in range(1, n + 1):
                w.writerow([f"F{i:02d}", f"Crossing the strait {i}", "Pike, O.", str(2015 + i), "Invented Ferry Review",
                            f"10.5555/ferry.{i}", "Index A", f"Passengers spoke of the crossing {i}.",
                            "include" if i % 2 else "exclude", "" if i % 2 else "C1", ""])
        (folder / sift.REASONS_NAME).write_text("stage,code,meaning\nta,C1,Not about crossings\n", encoding="utf-8")
        return folder

    # ── A. one row of steps on both screens
    check("122: the row is drawn by the searches' script from rvStepsHtml, on Screening by sfBar at the stage shown with "
          "the screen's counts, on Search strategy by rvHead with the counts asked of the screening its steps open",
          "if (typeof rvStepsDraw === 'function') rvStepsDraw($('sf-steps'), SF.review, SF.form ? 'ex' : SF.stage, all);" in fn(sjs, "sfBar")
          and "if (step === 'searches') rvStepsDraw(box, review, step, SFS.stages);" in fn(ssjs, "rvHead")
          and "got = await api('/api/sift', { op: 'counts', folder: review.screening });" in fn(ssjs, "rvStageCounts")
          and "rvStageCounts(SFS.review);" in fn(ssjs, "sfsOpen") and "SFS.stages = null;" in fn(ssjs, "sfsOpen")
          and "rvStepsDraw($('sfs-steps'), SFS.review, 'searches', SFS.stages);" in fn(ssjs, "sfsDrawRun"))
    check("122: a step chosen on the screening changes its stage, Full text only once a record has passed, and from Search "
          "strategy opens the screening at the stage chosen, a screening opening on the stage it is given",
          "if (sfShown()) { sfStageTo(to); return; }" in fn(ssjs, "rvStep")
          and "if (got.review.screening) siftOpen(got.review.screening, null, to);" in fn(ssjs, "rvStep")
          and "if (!['ta', 'ft', 'ex'].includes(stage) || (SF.form ? 'ex' : SF.stage) === stage || (stage === 'ft' && !sfFtOn())) return;"
          in fn(sjs, "sfStageTo")
          and "SF.stage = SF.form || ((stage || kept.stage) === 'ft' && sfFtOn()) ? 'ft' : 'ta';" in fn(sjs, "siftOpen")
          and "async function siftOpen(folder, gone, stage) {" in sjs)
    steps_js = "\n".join([lead, line_of_js(ssjs, "const RV_TA_LATER = "), line_of_js(ssjs, "const RV_FT_LATER = "),
                          line_of_js(ssjs, "const RV_FORM_NAME = "), line_of_js(ssjs, "const RV_EX_LATER = "),
                          line_of_js(ssjs, "const RV_DRAWN = "), "const SFS = { runs: [] };", whole(ssjs, "rvStepsHtml"),
                          whole(ssjs, "rvStepsDraw"), line_of_js(ssjs, "const RV_WATCHED = "), whole(ssjs, "rvStepsSeps"),
                          whole(ssjs, "rvStepsWatch")])
    if node and "function rvStepsHtml(" in ssjs:
        probe = scratch / "sift-steps-122.js"
        probe.write_text(steps_js + r"""
const counts = (ta, ft) => ({ ta: { records: ta }, ft: { records: ft } });
const html = {
  waiting: rvStepsHtml({ searches: true, screening: null }, 'searches', null),
  plan: rvStepsHtml({ searches: true, screening: 'r/1' }, 'searches', counts(58, 0)),
  ta: rvStepsHtml({ searches: true, screening: 'r/1' }, 'ta', counts(58, 0)),
  passed: rvStepsHtml({ searches: true, screening: 'r/1' }, 'ta', counts(58, 7)),
  ft: rvStepsHtml({ searches: true, screening: 'r/1' }, 'ft', counts(58, 7)),
  alone: rvStepsHtml({ searches: false, screening: 'p' }, 'ta', counts(12, 0)),
  none: rvStepsHtml(null, 'ta', counts(3, 1)),
};
const box = { innerHTML: '', hidden: true };
rvStepsDraw(box, { searches: true, screening: 'r/1' }, 'ta', counts(58, 0));
const first = box.innerHTML;
box.innerHTML = 'kept';
rvStepsDraw(box, { searches: true, screening: 'r/1' }, 'ta', counts(58, 0));
const kept = box.innerHTML;
console.log(JSON.stringify({ html, first, kept, hidden: box.hidden, click: typeof box.onclick }));
""", encoding="utf-8")
        ran = subprocess.run([node, str(probe)], capture_output=True, text=True, encoding="utf-8", timeout=60)
        o = json.loads(ran.stdout) if ran.returncode == 0 and ran.stdout.strip() else {}
        h = o.get("html", {})
        why = (ran.stderr or ran.stdout)[:400]
        sep = '<span class="sf-step-sep" aria-hidden="true">&#8250;</span>'
        # each step's words over a hidden bold copy of themselves, so the step in front is no wider (barsD, 6 November 2026)
        w = lambda words: f'<span class="tab-w" data-bold="{words}">{words}</span>'
        check("122, updated 12 October (123), 13 October, later (129), 14 October (143), 15 October (145) and 6 November "
              "2026 (330): in node, the row reads Search strategy, Screen by title and abstract, Screen by full text and "
              "Extract and appraise in order, Check references gone to Trace, each stage named with its verb, with a chevron "
              "between each, each stage with its count of records, the step shown marked, and each step's words with their "
              "bold copy, so the row never moves",
              h.get("ta") == '<button type="button" data-step="searches">' + w("Search strategy") + '</button>' + sep
              + '<button type="button" data-step="ta" aria-current="step">' + w("Screen by title and abstract")
              + ' <span class="sf-step-c">58</span></button>'
              + sep + '<button type="button" data-step="ft" aria-disabled="true" title="Screen by full text, once a record has '
              'Yes or Maybe at title and abstract">' + w("Screen by full text") + ' <span class="sf-step-c">0</span></button>'
              + sep + '<button type="button" data-step="ex">' + w("Extract and appraise") + ' <span class="sf-step-c">0</span></button>',
              why + str(h.get("ta")))
        check("122, updated 12 October (123): in node, Screen by full text is greyed with its reason on hover until a record "
              "has passed title and abstract, and then a step like the others, marked when shown",
              'data-step="ft" aria-disabled="true"' in h.get("plan", "") and 'data-step="ft" aria-disabled' not in h.get("passed", "x")
              and 'data-step="ft" aria-current="step"><span class="tab-w" data-bold="Screen by full text">Screen by full text</span> '
              '<span class="sf-step-c">7</span>' in h.get("ft", "")
              and 'data-step="searches" aria-current="step"' in h.get("plan", ""), why + str(h))
        check("122, updated 12 October (123), 13 October, later (129), 14 October (143) and 15 October (145): in node, Screen "
              "by title and abstract and Extract and appraise wait on Search strategy until a run has a screening, each its "
              "reason on hover, a review with no searches has the three stages alone, Check references in Trace now, and a "
              "screening with no review still shows its stages",
              'data-step="ta" aria-disabled="true" title="Screen by title and abstract, once a run brings in records">'
              '<span class="tab-w" data-bold="Screen by title and abstract">Screen by title and abstract</span></button>'
              in h.get("waiting", "") and "Search strategy" not in h.get("alone", "x") and h.get("alone", "").count("<button") == 3
              and "Search strategy" not in h.get("none", "x") and h.get("none", "").count("<button") == 3
              and 'data-step="refs"' not in h.get("waiting", "x") + h.get("alone", "x")
              and 'data-step="ex" aria-disabled="true" title="Extract and appraise, once a run brings in records">' in h.get("waiting", ""),
              why + str(h))
        check("122: in node, the row is built again only when it changes, so a step keeps the focus, and its box shown with "
              "one press handler for every step",
              o.get("first", "").startswith('<button type="button" data-step="searches">') and o.get("kept") == "kept"
              and o.get("hidden") is False and o.get("click") == "function", why)
        # no chevron alone at a wrapped line's end or start (17 October, later): each step and chevron a box with
        # the rows it stands on, as the browser lays them at a narrow width
        seps = scratch / "sift-steps-seps-122.js"
        seps.write_text(steps_js + r"""
const row = (tops) => {
  const items = tops.map((top, i) => ({ i, sep: i % 2 === 1, style: { display: '', visibility: '' },
    getBoundingClientRect: () => ({ top, bottom: top + (top < 0 ? 0 : 20), height: top < 0 ? 0 : 20 }) }));
  items.forEach((it, i) => { it.previousElementSibling = items[i - 1] || null; it.nextElementSibling = items[i + 1] || null; });
  return { items, querySelectorAll: (sel) => (sel === '.sf-step-sep' ? items.filter((it) => it.sep) : []) };
};
const look = (tops) => { const box = row(tops); rvStepsSeps(box); return box.items.filter((it) => it.sep).map((it) => `${it.style.display || '-'}/${it.style.visibility || '-'}`); };
const out = {
  one: look([0, 0, 0, 0, 0]),
  endsLine: look([0, 0, 0, 0, 24]),
  startsLine: look([0, 0, 0, 24, 24]),
  shut: look([-1, -1, -1, -1, -1]),
  again: (() => { const box = row([0, 0, 0, 0, 0]); box.items[3].style.visibility = 'hidden'; rvStepsSeps(box); return box.items[3].style.visibility; })(),
};
rvStepsSeps({ innerHTML: '' });
rvStepsWatch({ innerHTML: '' });
console.log(JSON.stringify(out));
""", encoding="utf-8")
        ran = subprocess.run([node, str(seps)], capture_output=True, text=True, encoding="utf-8", timeout=60)
        s = json.loads(ran.stdout) if ran.returncode == 0 and ran.stdout.strip() else {}
        check("122, 17 October, later: in node, where the steps wrap no chevron stands alone, one that ends a line hidden in "
              "its place and one that starts a line taken out, neither moving a step to another line, a row on one line and "
              "a row not shown keeping every chevron, each measured afresh, and a box with no elements left alone",
              s == {"one": ["-/-", "-/-"], "endsLine": ["-/-", "-/hidden"], "startsLine": ["-/-", "none/-"],
                    "shut": ["-/-", "-/-"], "again": ""}
              and "rvStepsSeps(box);\n  rvStepsWatch(box);" in fn(ssjs, "rvStepsDraw"), (ran.stderr or ran.stdout)[:400])
    else:
        skip("122: the steps in node", "no node on this machine")
    check("122: a press on a step that waits, or on the step shown, does nothing",
          "if (!b || b.getAttribute('aria-disabled') === 'true' || b.dataset.step === step) return;" in fn(ssjs, "rvStepsDraw"))

    # ── C. the flow's sidebar dragged wider or narrower, its width kept per screening
    check("122: one set of functions drags both sidebars, the filters' edge at their right and the flow's at its left, "
          "each width set as a property, kept through the view op and read back as a screening opens",
          "flow: { box: 'sf-side', edge: 'sf-side-edge', prop: '--sf-side-w', first: 300, min: 240, max: 720, step: 16," in sjs
          and "way: -1, table: 'flow', op: 'flow' }," in sjs and "way: 1, table: 'sidebar', op: 'filters' }," in sjs
          and "now = sfEdgeWidth(which, from + s.way * (ev.clientX - x0)) || now;" in fn(sjs, "sfEdgeBoot")
          and "edge.setPointerCapture(e.pointerId);" in fn(sjs, "sfEdgeBoot")
          and "ArrowLeft: now - s.way * s.step, ArrowRight: now + s.way * s.step, Home: s.min, End: s.max" in fn(sjs, "sfEdgeKey")
          and "sfQueue(() => api('/api/sift', { op: 'view', folder, sidebar: { [s.op]: width } }));" in fn(sjs, "sfEdgeKeep")
          and "sfEdgeWidth('flow', table.flow);" in fn(sjs, "siftOpen") and "sfEdgeBoot('flow');" in fn(sjs, "sfTvBoot")
          and "if (sfEdgeKey(e)) return;" in fn(sjs, "sfKeyDown") and "function sfFacetsEdgeBoot(" not in sjs)
    kept = ferries(base / "kept")
    first = sift.table_settings(kept)
    one = sift.save_view(kept, sidebar={"flow": 333.6})
    both = sift.save_view(kept, sidebar={"filters": 250, "flow": 9000})
    low = sift.save_view(kept, sidebar={"flow": 10})
    alone = sift.save_view(kept, sidebar=300)
    held = json.loads((kept / sift.SETTINGS_NAME).read_text(encoding="utf-8"))["table"]
    check("122: sift.json keeps the flow's width beside the filters', a whole number within 240 and 720, a number alone "
          "still the filters', and none until he drags it",
          first["flow"] is None and one["flow"] == 334 and one["sidebar"] is None and both["sidebar"] == 250 and both["flow"] == 720
          and low["flow"] == 240 and alone["sidebar"] == 300 and alone["flow"] == 240 and held.get("flow") == 240
          and held.get("sidebar") == 300 and (sift.FLOW_MIN, sift.FLOW_MAX) == (240, 720), str(held))
    check("122: a width that is no number, a sidebar it does not know, or none named is refused in one line, nothing written",
          all(refusal_of(lambda v=v: sift.save_view(kept, sidebar=v)) == "The sidebar's width is a number of pixels."
              for v in ({"flow": "wide"}, {"panel": 300}, {}, {"flow": True}, "wide"))
          and json.loads((kept / sift.SETTINGS_NAME).read_text(encoding="utf-8"))["table"] == held)
    kept_state = (server_mod.CONFIG_PATH, server_mod.ROOT_OVERRIDE, server_mod.STATE_MEMORY)
    config_file = base / "config.json"
    config_file.write_text(json.dumps({"interviewer": "Adam"}), encoding="utf-8")
    try:
        server_mod.CONFIG_PATH = config_file
        server_mod.ROOT_OVERRIDE = str(base)
        server_mod.STATE_MEMORY = {"recent": []}
        through = ferries(base / "through")
        sift_routes.api_sift_review({"op": "open", "folder": str(through)})
        sift.decide(through, "F01", "ta", "include")
        files = {p.name: p.read_bytes() for p in through.iterdir() if p.is_file()}
        counted = sift_routes.api_sift({"op": "counts", "folder": str(through)})
        unchanged = files == {p.name: p.read_bytes() for p in through.iterdir() if p.is_file()}
        viewed = sift_routes.api_sift({"op": "view", "folder": str(through), "sidebar": {"flow": 410}})
        read = sift_routes.api_sift({"op": "read", "folder": str(through)})
    finally:
        (server_mod.CONFIG_PATH, server_mod.ROOT_OVERRIDE, server_mod.STATE_MEMORY) = kept_state
    check("122: through the server, view keeps the flow's width and read gives it back with the table, and counts, which the "
          "steps on Search strategy ask, gives each stage's records and writes nothing",
          viewed["table"]["flow"] == 410 and read["table"]["flow"] == 410 and unchanged
          and counted["counts"]["stages"]["ta"]["records"] == 6 and counted["counts"]["stages"]["ft"]["records"] == 1,
          str(counted.get("counts", {}).get("stages")))

    # ── E. the decisions' colours in the filters
    if node and "function tbChoiceHtml(" in support.table_js():
        probe = scratch / "sift-steps-122-dots.js"
        probe.write_text("\n".join([lead, whole(support.table_js(), "tbChoiceHtml"), whole(sjs, "sfBarsHtml")]) + r"""
const dots = [['undecided', ''], ['include', 'include'], ['maybe', 'maybe'], ['exclude', 'exclude']]
  .map(([value, dec]) => tbChoiceHtml({ value, label: value, dec }, 1, false));
const sub = tbChoiceHtml({ value: 'exclude:C1', label: 'C1', meaning: 'Not about crossings', sub: true }, 1, false);
const db = tbChoiceHtml({ value: 'psycinfo', label: 'PsycInfo', db: 'psycinfo' }, 0, true);
const year = sfBarsHtml([{ from: 2015, to: 2019, label: '2015–2019', n: 1 }, { from: 2020, to: 2021, label: '2020–2024', n: 12 }], 2016, 2021, 'year');
const rating = sfBarsHtml([{ from: 1, to: 1, label: '1', n: 0 }, { from: 3, to: 3, label: '3', n: 1 }], 1, 5, 'rating');
const cited = sfBarsHtml([{ from: 6, to: 10, label: '6–10', n: 3 }, { from: 1001, to: 1250, label: '1001 and over', n: 1 }], 0, 1250, 'cited');
console.log(JSON.stringify({ dots, sub, db, year, rating, cited }));
""", encoding="utf-8")
        ran = subprocess.run([node, str(probe)], capture_output=True, text=True, encoding="utf-8", timeout=60)
        o = json.loads(ran.stdout) if ran.returncode == 0 and ran.stdout.strip() else {}
        why = (ran.stderr or ran.stdout)[:400]
        check("122: in node, each decision in the filters carries a dot of its colour, To screen's grey, a reason under "
              "No none, and a database its own dot as before",
              [re.search(r'<span class="sf-decdot" data-decision="([a-z]*)" aria-hidden="true"></span>', d or "").group(1)
               for d in o.get("dots", [""] * 4) if re.search(r'sf-decdot', d or "")] == ["", "include", "maybe", "exclude"]
              and "sf-decdot" not in o.get("sub", "x") and "sf-dbdot" not in o.get("sub", "x")
              and '<span class="sf-dbdot" data-db="psycinfo" aria-hidden="true"></span>' in o.get("db", ""), why)
        check("122: in node, each bar of a chart says its run in words and its count of records for the tip, 2020 to 2024: 12 "
              "records, a star's run in stars, 1001 and over, and no native title left to show late",
              'data-tip="2020 to 2024: 12 records"' in o.get("year", "") and 'data-tip="2015 to 2019: 1 record"' in o.get("year", "")
              and 'data-tip="3 stars: 1 record"' in o.get("rating", "") and 'data-tip="1 star: 0 records"' in o.get("rating", "")
              and 'data-tip="6 to 10: 3 records"' in o.get("cited", "") and 'data-tip="1001 and over: 1 record"' in o.get("cited", "")
              and "title=" not in o.get("year", "") + o.get("rating", "") + o.get("cited", "")
              and re.findall(r'<span class="sf-bar( in)?" data-from="(\d+)"', o.get("year", "")) == [("", "2015"), (" in", "2020")], why)
    else:
        skip("122: the dots and the charts' words in node", "no node on this machine")

    # ── G. a click opens a row, and Back and Forward
    boot = fn(sjs, "sfTvBoot")
    check("122: a click on a row opens its record, while a star, a guess, a link or a control does its own work, a cell of "
          "his opens for typing, a press that ends the typing opens nothing, and words selected across the row stay so",
          "sfOpenRecord(true);" in boot and "if (e.target.closest('a, button, input, select, textarea, label')) return;" in boot
          and "if (SF.tvTyping) return;" in boot and "SF.tvTyping = !!SF.editing;" in boot
          and "if (td && td.isConnected && !SF.editing) { sfTvEdit(td, rec, td.dataset.edit); return; }" in boot
          and "if (sel && String(sel).trim() && tr.contains(sel.anchorNode)) return;" in boot
          and "addEventListener('dblclick'" not in boot and boot.index("const star = ") < boot.index("sfOpenRecord(true);"))
    check("122: the second press of a double-click on a row does nothing on the record the first opened, and Enter still "
          "opens the chosen row",
          "if (SF.openedAt && Date.now() - SF.openedAt < SF_SECOND_PRESS) { e.preventDefault(); e.stopPropagation(); }" in fn(sjs, "sfBoot")
          and "const SF_SECOND_PRESS = 500;" in sjs and "SF.openedAt = byClick ? Date.now() : 0;" in fn(sjs, "sfOpenRecord")
          and "if (key === 'Enter') { e.preventDefault(); sfOpenRecord(); return; }" in fn(sjs, "sfKeyDown")
          and '<td class="mono">Enter or a click</td><td>In the table, open the row</td>' in page)
    check("122, updated 6 November 2026 (330, the path's name its project's menu): a record opened is an entry of the "
          "browser's history, the way back and Esc go Back, the browser's Back and "
          "Forward are heard, and an entry left from before lets go as a screening opens or is left",
          "sfHistoryPush();" in fn(sjs, "sfOpenRecord") and "sfHistoryKeep();" in fn(sjs, "sfDraw")
          and "bandMenuWire('sf-name', () => siftBandMenu());" in fn(sjs, "sfBoot")
          and "if (!SF.picking && SF.view === 'record' && key === 'Escape') { e.preventDefault(); sfToTable(); return; }" in fn(sjs, "sfKeyDown")
          and "window.addEventListener('popstate', sfPopState);" in fn(sjs, "sfBoot")
          and "sfHistoryDrop();" in fn(sjs, "siftOpen") and "sfHistoryDrop();" in fn(sjs, "sfLeave")
          and "pushState" not in ssjs)
    hist = [line_of_js(sjs, "const SF_HISTORY = "), *(whole(sjs, n) for n in ("sfOnRecordEntry", "sfHistoryPush", "sfHistoryKeep",
                                                                                "sfHistoryDrop", "sfToTable", "sfPopState", "sfOpenRecord"))]
    if node and all(hist):
        probe = scratch / "sift-steps-122-history.js"
        probe.write_text("\n".join(hist) + r"""
const H = { stack: [{ state: null }], at: 0 };
const copy = (v) => (v === null ? null : JSON.parse(JSON.stringify(v)));
const history = {
  get state() { return H.stack[H.at].state; },
  pushState(st) { H.stack = H.stack.slice(0, H.at + 1); H.stack.push({ state: copy(st) }); H.at += 1; },
  replaceState(st) { H.stack[H.at].state = copy(st); },
  back() { if (H.at > 0) { H.at -= 1; sfPopState({ state: history.state }); } },
  forward() { if (H.at < H.stack.length - 1) { H.at += 1; sfPopState({ state: history.state }); } },
};
const SF = { folder: 'f', view: 'table', ids: ['A', 'B', 'C'], at: 1, openedAt: 0 };
const views = [];
const sfShown = () => true;
const sfFtEmpty = () => false;
const sfRecord = () => (SF.ids[SF.at] ? { rec_id: SF.ids[SF.at] } : null);
function sfSetView(v) { views.push(v); SF.view = v; }
const out = {};
sfOpenRecord(true);
out.opened = [SF.view, H.at, history.state && history.state.rec, SF.openedAt > 0];
SF.at = 2; sfHistoryKeep();
out.walked = history.state.rec;
sfToTable();
out.back = [SF.view, H.at];
SF.at = 0;
history.forward();
out.forward = [SF.view, SF.ids[SF.at], H.at];
history.back();
out.again = [SF.view, H.at];
SF.view = 'record';
sfToTable();
out.plain = [SF.view, H.at];
sfOpenRecord();
sfHistoryDrop();
out.dropped = [history.state, SF.view];
history.back(); history.forward();
out.dead = SF.view;
SF.view = 'table';
history.pushState({ kind: 'idiograph-sift-record', folder: 'other', rec: 'A' }, '');
sfPopState({ state: history.state });
out.other = SF.view;
console.log(JSON.stringify({ out, views }));
""", encoding="utf-8")
        ran = subprocess.run([node, str(probe)], capture_output=True, text=True, encoding="utf-8", timeout=60)
        o = json.loads(ran.stdout) if ran.returncode == 0 and ran.stdout.strip() else {}
        out = o.get("out", {})
        why = (ran.stderr or ran.stdout)[:400]
        check("122: in node, a record opened pushes its entry, walking the records keeps the one he is on, the way back goes "
              "Back to the table, and Forward opens the record he left",
              out.get("opened") == ["record", 1, "B", True] and out.get("walked") == "C" and out.get("back") == ["table", 0]
              and out.get("forward") == ["record", "C", 1] and out.get("again") == ["table", 0], why + str(out))
        check("122: in node, with no entry of its own the way back shows the table at once, an entry let go opens nothing, "
              "and an entry of another screening is passed over",
              out.get("plain") == ["table", 0] and out.get("dropped") == [None, "record"] and out.get("other") == "table", why + str(out))
    else:
        skip("122: Back and Forward in node", "no node on this machine")
