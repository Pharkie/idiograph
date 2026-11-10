from __future__ import annotations

import csv
import json
import os
import re
import shutil

from . import support
from .support import MINI_PAGE_JS, check, follow_stub, refusal_of, sift_words_js, skip, urllib_path


def tick_problems(sources: dict) -> tuple[list[str], int]:
    """Every checkbox and radio the page can draw that sits in no <label> and is named by no <label
    for>, as `file:line`, and how many ticks it saw. Every tick toggles from its whole row (13
    October), which its label gives it, so this is the rule's guard. `sources` maps a file's name to
    its text, the page's index.html and each static/*.js but the vendor's. A tick in markup, in a
    template string or in strings joined with +, is inside a label when a <label opens before it and
    has not closed again, in the same top-level function or statement of a script, or anywhere before
    it in the page, comments set aside. One a <label for> names by its id is labelled too. A tick a
    script makes with createElement, its type set to checkbox or radio, is labelled when the same
    function makes a label to hold it."""
    def blank(text, pattern):
        return re.sub(pattern, lambda m: re.sub(r"[^\n]", " ", m.group(0)), text, flags=re.S)

    def tag_end(text, at):
        # the > that closes the tag begun at `at`, any ${...} in it passed over whole
        depth, i = 0, at
        while i < len(text):
            if text.startswith("${", i):
                depth, i = depth + 1, i + 2
                continue
            ch = text[i]
            if depth and ch == "{":
                depth += 1
            elif depth and ch == "}":
                depth -= 1
            elif not depth and ch == ">":
                return i
            i += 1
        return len(text)

    top = re.compile(r"(?m)^(?:async function|function|const|let|var|class)\b")
    tick = re.compile(r"""\btype\s*=\s*\\?["']?(?:checkbox|radio)\b""")
    computed = re.compile(r"""\btype\s*=\s*\\?["']?\$\{""")
    made = re.compile(r"""(?:\.type\s*=\s*|setAttribute\(\s*['"]type['"]\s*,\s*)['"](?:checkbox|radio)['"]""")
    clean = {}
    for name, text in sources.items():
        clean[name] = (blank(text, r"<!--.*?-->") if name.endswith(".html")
                       else blank(blank(text, r"/\*.*?\*/"), r"(?m)^[ \t]*//[^\n]*"))
    fors = set()
    for text in clean.values():
        fors |= set(re.findall(r"""<label\b[^>]*?\bfor\s*=\s*\\?["']([^"'\\]+)""", text))
    problems, seen = [], 0
    for name, text in clean.items():
        script = not name.endswith(".html")
        for m in re.finditer(r"<input\b", text):
            tag = text[m.start():tag_end(text, m.start()) + 1]
            if not (tick.search(tag) or computed.search(tag)):
                continue
            seen += 1
            starts = [s.start() for s in top.finditer(text, 0, m.start())] if script else []
            before = text[starts[-1] if starts else 0:m.start()]
            inside = len(re.findall(r"<label\b", before)) > len(re.findall(r"</label>", before))
            ident = re.search(r"""\bid\s*=\s*\\?["']([^"'\\]+)""", tag)
            if not inside and not (ident and ident.group(1) in fors):
                problems.append(f"{name}:{text.count(chr(10), 0, m.start()) + 1}")
        if script:
            for m in made.finditer(text):
                seen += 1
                starts = [s.start() for s in top.finditer(text, 0, m.start())]
                after = top.search(text, m.end())
                body = text[starts[-1] if starts else 0:after.start() if after else len(text)]
                if not re.search(r"""createElement\(\s*['"]label['"]\s*\)""", body):
                    problems.append(f"{name}:{text.count(chr(10), 0, m.start()) + 1}")
    return problems, seen


@support.as_app("sift")
def test_sift_rows(scratch):
    print("\n127. Whole rows, 13 October: every checkbox and radio ticking from its whole row, Distil and Sift alike, "
          "and a scan that keeps it so, the record's ID the table's first column in place of its number, sorting R2 "
          "before R10 and naming the record in Screening's words, Done at the foot right of a card that applies its "
          "changes as you go, a Number type for his own columns, and his columns carried into a later run")
    import datetime as dt
    import http.server
    import subprocess
    import threading
    import sift
    import sift_search as ss

    page = support.page_text()
    app_src = support.text("family/static/shell.js", "apps/idiograph/static/distil.js")
    sift_src = support.text("apps/sift/static/sift.js")
    fn = lambda src, name: src.split(f"function {name}(", 1)[1].split("\n}", 1)[0] if f"function {name}(" in src else ""
    whole = lambda src, name: f"function {name}(" + fn(src, name) + "\n}"
    line = lambda src, start: next((l for l in src.splitlines() if l.startswith(start)), "")
    node = shutil.which("node")
    base = scratch / "sift-rows-127"
    shutil.rmtree(base, ignore_errors=True)
    base.mkdir(parents=True)

    # ── A. every tick in a label, and the scan that keeps it so
    sources = {"index.html": page}
    for path in sorted(p for folder in support.static_folders() for p in folder.glob("*.js")):
        sources[path.name] = path.read_text(encoding="utf-8")
    problems, seen = tick_problems(sources)
    check("127: every checkbox and radio in the app sits inside a <label> or is named by a <label for>, so a press "
          "anywhere on its row ticks it, the rule since 13 October, and a tick outside one is named here by file and line",
          not problems and seen >= 20 and "vendor" not in " ".join(sources), f"{seen} ticks seen, outside a label: {problems}")
    planted = {
        "bare.js": "function bare() {\n  return '<div><input type=\"checkbox\"> Loose</div>';\n}\n",
        "joined.js": "function joined(x) {\n  return `<label><input type=\"radio\" ${x > 1 ? 'checked' : ''}> One</label>`\n"
                     "    + `<input type=\"checkbox\"${x > 1 ? ' checked' : ''}>`;\n}\n",
        "kept.js": "function kept() {\n  return '<label class=\"row\">' + '<input type=\"checkbox\">' + 'Two</label>';\n}\n",
        "made.js": "function made() {\n  const box = document.createElement('input');\n  box.type = 'checkbox';\n  return box;\n}\n",
        "held.js": "function held() {\n  const row = document.createElement('label');\n  const box = document.createElement('input');\n"
                   "  box.type = 'radio';\n  row.append(box, 'Three');\n  return row;\n}\n",
        "apart.js": "function one() {\n  return '<label>Four</label>';\n}\nfunction two() {\n  return '<input type=\"checkbox\">';\n}\n",
        "said.js": "// a <label> in a comment opens nothing\nfunction said() {\n  /* <label> */\n  return '<input type=\"checkbox\">';\n}\n",
        "page.html": '<!-- <label> -->\n<p><label for="t1">Five</label> <input type="checkbox" id="t1"></p>\n<input type="checkbox" id="t2">\n',
    }
    found, count = tick_problems(planted)
    check("127: the scan finds a tick outside a label however the markup is built, in a string, a template string with a "
          "> inside it, strings joined with +, createElement, and after a label in a comment or in an earlier function, "
          "and passes one in a label, one named by <label for> and one made with its label",
          sorted(found) == sorted(["bare.js:2", "joined.js:3", "made.js:3", "apart.js:5", "said.js:4", "page.html:3"])
          and count == 10, f"{found} {count}")
    # ── B. in node: a press on a row ticks its box, a press on its other controls does not, and Done closes
    cols_card = page.split('<div class="overlay" id="sf-cols" hidden>', 1)[1].split("\n</div>", 1)[0]
    if not node:
        skip("127: a press on a row, its controls and Done in node", "node is not installed")
    else:
        lead = app_src[app_src.index("const esc = "):app_src.index("// a line from the server with a command in backticks")]
        block = sift_src.split("/* ── the table's rows: its columns, sort and filter, worked out with no page ── */", 1)[-1].split(
            "/* ── the table, drawn ── */", 1)[0]
        block = support.table_js() + "\n" + block
        pieces = [lead, line(app_src, "const TICK_SKIP = "), "let tickPressed = null;", whole(app_src, "tickRowClick"),
                  whole(app_src, "cardDone"), whole(app_src, "gripHtml"), whole(app_src, "nudgeRow"),
                  "const INFO_ICON = " + app_src.split("const INFO_ICON = ", 1)[1].split(";\n", 1)[0] + ";",
                  sift_words_js(sift_src), block, whole(sift_src, "sfColsDraw"), MINI_PAGE_JS]
        harness = r"""
const els = {};
const $ = (id) => els[id] || (els[id] = { innerHTML: '', disabled: false });
const SF = { table: { columns: [{ key: 'title', shown: true }, { key: 'authors', shown: true }, { key: 'year', shown: false },
                                { key: 'col_glaze', shown: true }, { key: 'col_kilns', shown: false }],
                      own: [{ key: 'col_glaze', name: 'Glaze', type: 'choice', options: ['Ash', 'Celadon'] },
                            { key: 'col_kilns', name: 'Kilns', type: 'number', options: [] }], defaults: [] } };
sfColsDraw();
const list = parse(`<ol id="sf-cols-list">${$('sf-cols-list').innerHTML}</ol>`);
const changes = [];
list.addEventListener('change', (e) => changes.push(`${e.target.closest('li').attrs['data-key']}:${e.target.checked}`));
const row = (key) => list.querySelectorAll('li').find((li) => li.attrs['data-key'] === key);
const out = { rows: list.querySelectorAll('li').map((li) => li.attrs['data-key']) };
const title = row('title');
press(title.querySelector('.sf-col-label'));
press(title);
press(title.querySelector('button.pc-grip'));
press(title.querySelector('circle'));
press(title, title.querySelector('button.pc-grip'));
out.builtin = changes.splice(0);
const glaze = row('col_glaze');
press(glaze.querySelector('input.sf-col-name'));
press(glaze.querySelector('button.sf-col-remove'));
press(glaze.querySelector('textarea'));
press(glaze);
press(glaze.querySelector('input[type="checkbox"]'));
out.own = changes.splice(0);
out.labelled = list.querySelectorAll('input[type="checkbox"]').every((b) => !!b.closest('label'));
const nudge = parse(nudgeRow('long', 'Long statements', 'A statement past twenty words.', false));
nudge.addEventListener('change', (e) => changes.push(`${e.target.attrs['data-nudge']}:${e.target.checked}`));
press(nudge.querySelector('label'));
press(nudge.querySelector('button.info-mark'));
press(nudge.querySelector('path'));
press(nudge.querySelector('label'));
out.nudge = changes.splice(0);
const card = parse(CARD);
let closed = 0;
card.querySelector('button.card-close').addEventListener('click', () => { closed += 1; });
out.done = [cardDone({ target: card.querySelector('button[data-done]') }), closed,
  cardDone({ target: card.querySelector('#sf-cols-reset') }), closed];
console.log(JSON.stringify(out));
"""
        script = base / "rows-127.js"
        script.write_text("\n".join(pieces) + f"\nconst CARD = {json.dumps(cols_card)};\n" + harness, encoding="utf-8")
        ran = subprocess.run([node, str(script)], capture_output=True, text=True, encoding="utf-8", timeout=60)
        out = json.loads(ran.stdout) if ran.returncode == 0 and ran.stdout.strip() else {}
        check("127: in node, on Set columns a press on a column's name or anywhere on its row ticks or unticks it once, and "
              "a press on its handle, or a drag of the handle let go on the row, ticks nothing",
              out.get("builtin") == ["title:false", "title:true"] and out.get("labelled") is True
              and out.get("rows") == ["title", "authors", "year", "col_glaze", "col_kilns"], (ran.stderr or json.dumps(out))[:400])
        check("127: in node, on a row of his own column a press on its name box, Remove or its choices ticks nothing, and a "
              "press on the row or on its box ticks it once each",
              out.get("own") == ["col_glaze:false", "col_glaze:true"], str(out.get("own")))
        check("127: in node, an Analysis tick, a nudge in Settings, ticks from a press on its words and not from its info "
              "mark", out.get("nudge") == ["long:true", "long:false"], str(out.get("nudge")))
        check("127: in node, Done presses the card's own X, so Set columns closes as the X closes it, and another button "
              "of the card closes nothing", out.get("done") == [True, 1, False, 1], str(out.get("done")))

    # ── D. the ID first, the number gone, a Number column of his
    folder = base / "kiln-review"
    folder.mkdir()
    head = ["rec_id", "title", "authors", "year", "journal", "doi", "sources", "abstract"]
    rows = [["R10", "Firing at dawn", "Ash, B.", "2021", "Invented Kiln Review", "10.5555/kiln.10", "PsycInfo",
             "Nine invented potters spoke of the kiln at dawn."],
            ["R2", "Glaze and patience", "Celadon, C.", "2019", "Invented Kiln Review", "", "PsycInfo",
             "Six invented potters on waiting for a glaze."],
            ["R1", "Wood smoke notes", "Cone, D.", "2023", "Invented Clay Studies", "", "Europe PMC",
             "Twelve invented makers at a wood kiln."],
            ["R11", "Cracks in the bisque", "Slip, E.", "2020", "Invented Clay Studies", "10.5555/kiln.11", "Europe PMC",
             "Four invented apprentices and their first firing."]]
    with open(folder / sift.CSV_NAME, "w", newline="", encoding="utf-8") as fh:
        csv.writer(fh).writerows([head] + rows)
    (folder / sift.REASONS_NAME).write_text("stage,code,meaning\nta,E1,Not about kilns\nft,F1,No interviews\n", encoding="utf-8")
    sift.write_settings(folder, {"table": {"columns": [{"key": "rec_id", "shown": True}, {"key": "title", "shown": True}],
                                           "first": sift.FIRST}})
    named = sift.table_settings(folder)
    check("127: the ID is in none of the table's columns, so Set columns offers no row for it, and a sift.json that "
          "names it passes it over",
          "rec_id" not in dict(sift.TABLE_COLUMNS) and "rec_id" not in [c["key"] for c in named["columns"]]
          and "rec_id" not in [c["key"] for c in named["defaults"]]
          and named["columns"][:2] == [{"key": "found", "shown": True}, {"key": "title", "shown": True}]
          and "rec_id: {" not in sift_src.split("const SF_COLS = ", 1)[1].split("};", 1)[0], str(named["columns"][:3]))
    added = sift.column(folder, "add", name="Analysts", kind="number")
    sift.set_field(folder, "R2", "col_analysts", "3")
    sift.set_field(folder, "R10", "col_analysts", "012")
    sift.set_field(folder, "R1", "col_analysts", " 2 ")
    refused = refusal_of(lambda: sift.set_field(folder, "R11", "col_analysts", "three"))
    half = refusal_of(lambda: sift.set_field(folder, "R11", "col_analysts", "2.5"))
    sc = sift.load(folder)
    check("127: a Number column is his own like the others, its col_ column in the CSV and its entry in own with the "
          "type number",
          sift.COLUMN_TYPES[:3] == ("text", "choice", "number") == sift.TABLE_TYPES
          and added["table"]["own"] == [{"key": "col_analysts", "name": "Analysts", "type": "number", "options": [], "where": "table",
                                         "not_reported": False, "when": None, "section": "", "from": ""}]
          and "col_analysts" in sc.header and sift.read_settings(folder)["table"]["own"][0]["type"] == "number",
          str(added["table"]["own"]))
    check("127: a Number column holds a whole number or nothing, written plain, and anything else is refused",
          [sc.cell(r, "col_analysts") for r in ("R10", "R2", "R1", "R11")] == ["12", "3", "2", ""]
          and bool(refused) and bool(half), f"{refused} {half}")
    sift.save_view(folder, filters={"col_analysts": {"from": 2, "to": 5, "none": True}})
    held = sift.table_settings(folder)["filters"]
    sift.save_view(folder, filters={"col_analysts": ["3"]})
    ticked = sift.table_settings(folder)["filters"]
    check("127: sift.json keeps a Number column's filter as a slider's, its two ends and Unknown, and lets go a list of "
          "ticks on it", held == {"col_analysts": {"from": 2, "to": 5, "none": True}} and ticked == {}
          and sift.range_keys(added["table"]["own"]) == set(sift.RANGE_COLUMNS) | {"col_analysts"}, f"{held} {ticked}")
    sift.save_view(folder, filters={})
    view = sift.screen(folder)
    if not node:
        skip("127: the ID and a Number column in node", "node is not installed")
    else:
        lead = app_src[app_src.index("const esc = "):app_src.index("// a line from the server with a command in backticks")]
        block = sift_src.split("/* ── the table's rows: its columns, sort and filter, worked out with no page ── */", 1)[-1].split(
            "/* ── the table, drawn ── */", 1)[0]
        block = support.table_js() + "\n" + block
        parts = [lead, sift_words_js(sift_src), block,
                 "function sfMeaning(code) { return code === 'E1' ? 'Not about kilns' : ''; }",
                 "const SF = " + json.dumps({"stage": "ta", "filters": {}, "table": view["table"], "records": view["records"]}) + ";",
                 "SF.facetsMore = new Set();", "SF.facetsFind = {};"]
        parts += [whole(sift_src, name) for name in ("sfPillHtml", "sfLinked", "sfStars", "sfTvCell",
                                                     "sfRangeEnds", "sfBarsHtml", "sfRangeHtml", "sfFieldNow", "sfTvEdit",
                                                     "sfReasonsDraw")]
        probe = base / "id-127.js"
        probe.write_text("\n".join(parts) + r"""
const byId = new Map(SF.records.map((r) => [r.rec_id, r]));
const ids = SF.records.map((r) => r.rec_id);
const cols = sfAllCols();
const col = (k) => cols.find((c) => c.key === k);
const groups = sfGroups(SF.records, SF.records, cols, 'ta', [], {});
const g = groups.find((x) => x.key === 'col_analysts');
const counts = tbFacetCounts(SF.records, groups, {}, sfRead('ta'));
const bars = sfRangeBars(SF.records, groups, {}, 'ta');
const sortBy = (key, dir) => tbSortRows(ids, byId, [{ key, dir }], cols, sfRead('ta'));
const pass = (f) => tbFilterRows(ids, byId, { col_analysts: f }, cols, sfRead('ta'));
// a cell opened for typing, as a press on it opens one
const made = [];
const document = { createElement: (tag) => { const e = { tagName: tag.toUpperCase(), attrs: {}, setAttribute(k, v) { this.attrs[k] = v; },
  addEventListener() {}, focus() {} }; made.push(e); return e; } };
const td = { textContent: 'x', appendChild(e) { this.child = e; } };
Object.assign(SF, { byId, editing: null, tvRows: new Map() });
sfTvEdit(td, 'R11', 'col_analysts');
// the reasons' heading, the record by its ID
const els = {};
const $ = (id) => els[id] || (els[id] = { hidden: false, textContent: '', innerHTML: '', querySelectorAll: () => [] });
const sfRecord = () => byId.get('R10');
const sfReasonChoices = () => [{ code: 'E1', meaning: 'Not about kilns' }];
const sfCodes = () => sfReasonChoices();
Object.assign(SF, { picking: true, pick: 0 });
const heads = [];
sfReasonsDraw(); heads.push($('sf-why-head').textContent);
SF.stage = 'ft'; sfReasonsDraw(); heads.push($('sf-why-head').textContent); SF.stage = 'ta';
console.log(JSON.stringify({
  first: [cols[0].key, cols[0].label, cols[0].kind], number: cols.some((c) => c.key === 'n' || c.label === '#'),
  shownFirst: sfStageCols([SF_ID, ...sfColumns(SF.table).filter((c) => c.shown)], 'ft')[0].key,
  idUp: sortBy('rec_id', 'asc'), idDown: sortBy('rec_id', 'desc'),
  idCell: sfTvCell(byId.get('R2'), col('rec_id')), idGroup: groups.some((x) => x.key === 'rec_id'),
  kind: col('col_analysts').kind, up: sortBy('col_analysts', 'asc'), down: sortBy('col_analysts', 'desc'),
  group: g ? [g.range, g.low, g.high, g.choices.map((c) => [c.value, c.label])] : null,
  bars: (bars.col_analysts || []).map((b) => [b.from, b.to, b.n]),
  between: pass({ from: 2, to: 5, none: false }), unknown: pass({ from: null, to: null, none: true }),
  both: pass({ from: 10, to: null, none: true }),
  kept: sfKeptRead({ col_analysts: { from: 2, to: 5, none: true } }, groups),
  range: sfRangeHtml(g, counts.col_analysts, 0, bars.col_analysts),
  cells: ['R2', 'R11'].map((id) => sfTvCell(byId.get(id), col('col_analysts'))),
  edit: [td.child.tagName, td.child.type, td.child.inputMode, td.child.attrs['aria-label'], td.child.value],
  heads,
}));
""", encoding="utf-8")
        ran = subprocess.run([node, str(probe)], capture_output=True, text=True, encoding="utf-8", timeout=60)
        out = json.loads(ran.stdout) if ran.returncode == 0 and ran.stdout.strip() else {}
        check("127: in node, the ID is the table's first column, at full text too, and no number column is left",
              out.get("first") == ["rec_id", "ID", "id"] and out.get("number") is False and out.get("shownFirst") == "rec_id"
              and out.get("idCell") == '<td class="mono sf-c-id">R2</td>' and out.get("idGroup") is False,
              (ran.stderr or json.dumps(out))[:400])
        check("127: in node, sorting by ID goes in natural order, R1, R2, R10 and R11, and back the other way",
              out.get("idUp") == ["R1", "R2", "R10", "R11"] and out.get("idDown") == ["R11", "R10", "R2", "R1"],
              f"{out.get('idUp')} {out.get('idDown')}")
        check("127: in node, a Number column sorts as numbers, 2 before 3 before 12, a record with none last whichever way",
              out.get("kind") == "number" and out.get("up") == ["R1", "R2", "R10", "R11"]
              and out.get("down") == ["R10", "R2", "R1", "R11"], f"{out.get('up')} {out.get('down')}")
        check("127: in node, a Number column filters by a slider with the participants' bars and Unknown for a blank, "
              "between its two ends, Unknown alone, or both, and is kept as a slider's filter",
              out.get("group") == [True, 2, 12, [["|none", "Unknown"]]] and out.get("bars") == [[2, 5, 2], [6, 10, 0], [11, 12, 1]]
              and out.get("between") == ["R2", "R1"] and out.get("unknown") == ["R11"] and out.get("both") == ["R10", "R11"]
              and out.get("kept") == {"col_analysts": {"from": 2, "to": 5, "none": True}}
              and out.get("range", "").count('type="range"') == 2 and ">Unknown<" in out.get("range", "")
              and 'data-runs="2-5 6-10 11-12"' in out.get("range", ""), json.dumps(out.get("group")) + str(out.get("bars")))

    # ── E. his columns carried into a later run that keeps the decisions, as they already were before today
    kept_clock, kept_env, kept_runner = ss.CLOCK, os.environ.pop(ss.STUB_ENV, None), ss.RUNNER
    ss.CLOCK = lambda: dt.date(2031, 6, 2)
    # no key in the keychain, so the run never asks the real `security` tool
    ss.RUNNER = lambda argv, **_: ss.Done(44, "\n")
    httpd = http.server.ThreadingHTTPServer(("127.0.0.1", 0), follow_stub({"phase": 1}))
    threading.Thread(target=httpd.serve_forever, kwargs={"poll_interval": 0.05}, daemon=True).start()
    stub = f"http://127.0.0.1:{httpd.server_address[1]}"
    ctx = lambda: ss.Context(base={s: stub + urllib_path(u) for s, u in ss.ENDPOINTS.items()}, pause=lambda s: None)
    try:
        review = base / "kiln-search"
        review.mkdir()
        (review / "reasons.csv").write_text("stage,code,meaning\nta,E1,Not about kilns\nft,F1,No interviews\n", encoding="utf-8")
        ss.save(review, {"databases": ["psycinfo"], "blocks": [{"name": "Kilns", "terms": ["kiln*"]}], "years": {"from": 2010}})
        ss.register(review)
        d1, d2 = "2031-06-01", "2031-06-02"
        ris = lambda *recs: "".join(f"TY  - JOUR\nTI  - {t}\nPY  - {y}\n" + (f"DO  - {d}\n" if d else "")
                                    + "AB  - An invented abstract on potters and their kilns.\nER  - \n\n" for t, y, d in recs).encode("utf-8")
        ss.take_export(review, "psycinfo", ris(("Firing at dawn", "2021", "10.5555/kiln.1"), ("Glaze and patience", "2019", ""),
                                               ("Wood smoke notes", "2023", "")), "p.ris", day=d1, ctx=ctx())
        ss.run(review, day=d1, ctx=ctx())
        f1 = review / "runs" / d1
        sc1 = sift.load(f1)
        rec = {sc1.cell(r, "title"): r for r in sc1.ids}
        sift.decide(f1, rec["Firing at dawn"], "ta", "include")
        sift.column(f1, "add", name="Analysts", kind="number")
        sift.column(f1, "add", name="Method", kind="choice", options=["IPA", "Thematic"])
        sift.column(f1, "add", name="Setting")
        sift.set_field(f1, rec["Firing at dawn"], "col_analysts", "2")
        sift.set_field(f1, rec["Glaze and patience"], "col_analysts", "3")
        sift.set_field(f1, rec["Glaze and patience"], "col_method", "IPA")
        sift.set_field(f1, rec["Wood smoke notes"], "col_setting", "A shared studio")
        cols = sift.table_settings(f1)["columns"]
        order = [{"key": "col_analysts", "shown": True}] + [c for c in cols if c["key"] != "col_analysts"]
        sift.save_view(f1, columns=[dict(c, shown=False) if c["key"] == "col_setting" else c for c in order])
        before = sift.table_settings(f1)
        # the later run finds the first record by its DOI under a title written otherwise, the second by its
        # title and year, and one new record
        ss.take_export(review, "psycinfo", ris(("Firing at Dawn: potters at work", "2021", "10.5555/kiln.1"),
                                               ("Glaze and patience", "2019", ""), ("Cracks in the bisque", "2024", "")),
                       "p.ris", day=d2, ctx=ctx())
        ss.run(review, day=d2, ctx=ctx(), follows=d1)
        f2 = review / "runs" / d2
        after = sift.table_settings(f2)
        sc2 = sift.load(f2)
        own = {sc2.cell(r, "title"): {k: v for k, v in sift.fields_of(sc2, r)["own"].items() if v} for r in sc2.ids}
        first = sift.read_lines(f2)[0]
        mine = lambda t: [(c["key"], c["shown"]) for c in t["columns"] if c["key"].startswith("col_")]
        check("127: his own columns come into a later run that keeps the decisions, their names, types, choices, order and "
              "whether they show, as they did before 13 October, a Number column among them",
              after["own"] == before["own"] and [c["type"] for c in after["own"]] == ["number", "choice", "text"]
              and after["own"][1]["options"] == ["IPA", "Thematic"] and mine(after) == mine(before)
              and mine(after) == [("col_analysts", True), ("col_method", True), ("col_setting", False)]
              and after["columns"][0]["key"] == "col_analysts", str(mine(after)))
        check("127: their values come with the records matched across runs, by DOI under a new title and by title and year, "
              "a record not found again keeps its own, and a new record holds none",
              own.get("Firing at dawn") == {"col_analysts": "2"}
              and own.get("Glaze and patience") == {"col_analysts": "3", "col_method": "IPA"}
              and own.get("Wood smoke notes") == {"col_setting": "A shared studio"}
              and own.get("Cracks in the bisque") == {}
              and first["act"] == "follow" and sorted(first["again"]) == sorted([rec["Firing at dawn"], rec["Glaze and patience"]]),
              str(own))
    finally:
        httpd.shutdown()
        ss.CLOCK, ss.RUNNER = kept_clock, kept_runner
        if kept_env is not None:
            os.environ[ss.STUB_ENV] = kept_env

