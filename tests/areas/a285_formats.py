"""Area 285: Language and formats (fmtcore, 28 October 2026, Adam's B and wording 1 of that day). A Settings page
of its own after General in all three apps, Language first, then Dates, Times of day and Numbers, each first Same
as this computer. The settings hold `formats`, `dates`, `time` and `numbers`, each "" for the computer's own, which
the window reads on the Mac and on Windows and hands the server in IDIOGRAPH_COMPUTER_FORMATS. The page writes
dates through tDate in the order chosen, times through tTime and numbers through tNum. The line under Language opens
the page on translating the app carries, /translating.

What is checked: each format sent alone saved alone, the rest of the settings file as it was, a choice that is not
one refused by name, each kept across a restart (a fresh process putting it in the page's I18N) and an empty one
following the computer; the computer's own writings mapped to the nearest choice (a made-up 28/10/2026, 10/28/2026,
2026-10-28, 24-hour and 12-hour, 1.234,5 and the rest); each choice's dates, times and numbers through the page's
own functions in node, in English and in American English, and the rows naming each choice and the computer's; and
the line's link served as a page of its own with its lists, the bundle carrying the file. Fixtures are invented
settings files in the scratch folder."""
from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

from . import support
from .support import check, skip


def test_formats(scratch: Path):
    print("\n285. Language and formats: Dates, Times of day and Numbers saved alone and kept across a restart, an "
          "empty one following the computer, the computer's own mapped to the nearest choice, each choice through "
          "tDate, tTime and tNum, and the line under Language opening the page on translating (28 October 2026)")
    import boot
    import i18n
    import server

    # ── saved alone, refused by name, kept across a restart
    saved_path = server.CONFIG_PATH
    config = scratch / "a285-config.json"
    answers = {}
    try:
        server.CONFIG_PATH = config
        config.write_text(json.dumps({"interviewer": "Ada", "language": "en-GB"}, indent=2), encoding="utf-8")
        answers["dates"] = server.api_settings({"formats": {"dates": "mdy"}})["config"].get("formats")
        answers["time"] = server.api_settings({"formats": {"time": "12"}})["config"].get("formats")
        answers["numbers"] = server.api_settings({"formats": {"numbers": "point"}})["config"].get("formats")
        kept = json.loads(config.read_text(encoding="utf-8"))
        refusals = []
        for bad in ({"dates": "dym"}, {"weeks": "monday"}, "mdy"):
            try:
                server.api_settings({"formats": bad})
                refusals.append(None)
            except server.WorkbookError as exc:
                refusals.append(str(exc))
        after_refusals = json.loads(config.read_text(encoding="utf-8"))
    finally:
        server.CONFIG_PATH = saved_path
    want = {"dates": "mdy", "time": "12", "numbers": "point"}
    check("285: each format sent alone is saved alone into `formats`, the others kept, the rest of the settings file "
          "as it was",
          answers["dates"] == {"dates": "mdy", "time": "", "numbers": ""} and answers["numbers"] == want
          and kept == {"interviewer": "Ada", "language": "en-GB", "formats": want}, str(kept))
    check("285: a choice that is not one is refused naming it, and nothing is written",
          refusals[0] == "dates dym is not one of the choices under Language and formats."
          and refusals[1] and "weeks" in refusals[1] and refusals[2] and after_refusals == kept, str(refusals))

    fresh = (
        "import sys, json\nfrom pathlib import Path\nsys.path.insert(0, %r)\nimport boot\nboot.setup()\n"
        "import server, i18n\nserver.CONFIG_PATH = Path(%r)\n"
        "data = json.loads(i18n.script()[len('<script>var I18N = '):-len(';</script>')])\n"
        "print(json.dumps([data['formats'], data['computer_formats']]))\n"
    ) % (str(support.TOOL), str(config))
    run = lambda env: subprocess.run([sys.executable, "-I", "-c", fresh], capture_output=True, text=True,
                                     encoding="utf-8", timeout=120, env=env)
    base = {k: v for k, v in os.environ.items() if k != i18n.COMPUTER_FORMATS}
    ran = run(dict(base, **{i18n.COMPUTER_STANDIN: "en-GB"}))
    after = json.loads(ran.stdout.strip().splitlines()[-1]) if ran.returncode == 0 and ran.stdout.strip() else ran.stderr[-300:]
    check("285: the formats are kept across a restart, a fresh process putting them in the page's I18N, and with no "
          "window the computer's own says nothing",
          after == [want, {"dates": "", "time": "", "numbers": ""}], str(after))

    try:
        server.CONFIG_PATH = config
        for kind in want:
            server.api_settings({"formats": {kind: ""}})
        emptied = json.loads(config.read_text(encoding="utf-8")).get("formats")
    finally:
        server.CONFIG_PATH = saved_path
    american = json.dumps({"date": "10/28/26", "time": "2:05 PM", "number": "1,234.50"})
    ran = run(dict(base, **{i18n.COMPUTER_STANDIN: "en-GB", i18n.COMPUTER_FORMATS: american}))
    follows = json.loads(ran.stdout.strip().splitlines()[-1]) if ran.returncode == 0 and ran.stdout.strip() else ran.stderr[-300:]
    check("285: an empty format follows the computer, the window's American formats read as Oct 28, 2026, 2:05 pm "
          "and 1,234.5",
          emptied == {"dates": "", "time": "", "numbers": ""}
          and follows == [emptied, {"dates": "mdy", "time": "12", "numbers": "comma"}], str(follows))

    # ── the computer's own mapped to the nearest choice
    nearest = {
        "28/10/2026": "dmy", "10/28/2026": "mdy", "2026-10-28": "ymd", "28.10.26": "dmy", "10/28/26": "mdy",
        "2026/10/28": "ymd", "28 Oct 2026": "dmy", "Oct 28, 2026": "mdy", "28-okt-2026": "dmy", "": "",
    }
    clocks = {"14:05": "24", "2:05 PM": "12", "2:05 pm": "12", "14.05": "24", "下午2:05": "12", "": ""}
    numbers = {"1,234.5": "comma", "1.234,5": "point", "1 234,5": "space", "1 234,5": "space",
               "1'234.5": "apostrophe", "1’234.50": "apostrophe", "1234,50": "space", "1234.5": "comma", "x": ""}
    wrong = [f"{k} gave {i18n.nearest_date(k)}" for k, v in nearest.items() if i18n.nearest_date(k) != v]
    wrong += [f"{k} gave {i18n.nearest_time(k)}" for k, v in clocks.items() if i18n.nearest_time(k) != v]
    wrong += [f"{k} gave {i18n.nearest_number(k)}" for k, v in numbers.items() if i18n.nearest_number(k) != v]
    bad_json = i18n.computer_formats({i18n.COMPUTER_FORMATS: "not json"})
    check("285: the computer's own writing of 28 October 2026, 14:05 and 1234.5 is taken as the nearest choice, and "
          "what is not read says nothing",
          not wrong and bad_json == {"dates": "", "time": "", "numbers": ""}, "; ".join(wrong))
    main_rs = support.text("packaging/tauri/src-tauri/src/main.rs")
    formats_rs = support.text("packaging/tauri/src-tauri/src/formats.rs")
    check("285: the window hands the server the computer's own formats in IDIOGRAPH_COMPUTER_FORMATS, read on the Mac "
          "and on Windows",
          "cmd.env(formats::VARIABLE, said)" in main_rs and f'"{i18n.COMPUTER_FORMATS}"' in formats_rs
          and "GetDateFormatEx" in formats_rs and "NSDateFormatter" in formats_rs)

    # ── each choice through the page's own functions in node
    node_ok = __import__("shutil").which("node")
    if not node_ok:
        skip("285: the formats through tDate, tTime and tNum under node", "node is not on this machine")
    else:
        roots = boot.roots()
        lib = support.text("family/static/i18n.js")
        shell = support.text("family/static/shell.js")
        piece = lambda name: f"function {name}(" + shell.split(f"function {name}(", 1)[1].split("\n}\n", 1)[0] + "\n}\n"
        line = lambda start: next(ln for ln in shell.splitlines() if ln.startswith(start)) + "\n"
        cases = r"""
const at = new Date(2026, 9, 28, 14, 5);
const out = {};
for (const dates of ['dmy', 'mdy', 'ymd']) {
  I18N_DATA.formats = { dates, time: '', numbers: '' };
  out[dates] = [tDate(at, { day: 'numeric', month: 'short', year: 'numeric' }), tDate(at, { day: 'numeric', month: 'long', year: 'numeric' }),
    tDate(at, { day: 'numeric', month: 'short' }), tDate(tDay('2026-09-03T10:00'), { day: 'numeric', month: 'short', year: 'numeric', timeZone: 'UTC' })];
}
for (const time of ['24', '12']) {
  I18N_DATA.formats = { dates: '', time, numbers: '' };
  out[time] = [tTime(at), tTime(new Date(2026, 9, 28, 9, 5))];
}
for (const numbers of ['comma', 'point', 'space', 'apostrophe']) {
  I18N_DATA.formats = { dates: '', time: '', numbers };
  out[numbers] = [tNum(1234.5), tNum(1284), tNum(0.83, { minimumFractionDigits: 2 })];
}
I18N_DATA.formats = { dates: '', time: '', numbers: '' };
I18N_DATA.computer_formats = { dates: '', time: '', numbers: '' };
out.none =[tDate(at, { day: 'numeric', month: 'long', year: 'numeric' }), tTime(at), tNum(1234.5)];
I18N_DATA.computer_formats = { dates: 'ymd', time: '12', numbers: 'point' };
out.computer = [tDate(at, { day: 'numeric', month: 'long', year: 'numeric' }), tTime(at), tNum(1234.5)];
I18N_DATA.formats = { dates: 'dmy', time: '24', numbers: 'comma' };
out.chosen = [tDate(at, { day: 'numeric', month: 'long', year: 'numeric' }), tTime(at), tNum(1234.5)];
// the rows: each choice named as an example of itself, the computer's first, the one the settings hold ticked
const rows = {};
const row = (kind, value) => { const word = { textContent: '' }; const box = { value, checked: false, parentElement: { querySelector: () => word } }; (rows[kind] = rows[kind] || []).push([box, word]); };
for (const v of ['', 'dmy', 'mdy', 'ymd']) row('dates', v);
for (const v of ['', '24', '12']) row('time', v);
for (const v of ['', 'comma', 'point', 'space', 'apostrophe']) row('numbers', v);
globalThis.document = { querySelectorAll: (q) => rows[/set-(\w+)/.exec(q)[1]].map((r) => r[0]) };
I18N_DATA.computer_formats = { dates: 'mdy', time: '', numbers: '' };
FORMATS_ROW.set = { dates: 'ymd', time: '', numbers: 'space' };
drawFormats();
out.rows = Object.fromEntries(Object.entries(rows).map(([k, rs]) => [k, rs.map(([b, w]) => (b.checked ? '(x) ' : '( ) ') + w.textContent)]));
console.log(JSON.stringify(out));
"""
        js = {}
        for tag in ("en", "en-US"):
            inline = i18n.script(tag, roots)[len("<script>"):-len("</script>")]
            harness = (inline + "\n" + lib + "\n" + line("const FORMATS_ROW = ") + line("const FORMAT_SAMPLE = ")
                       + piece("drawFormats") + cases)
            ran = support.run_node(harness, scratch, f"a285-{tag}.js")
            js[tag] = json.loads(ran.stdout.strip().splitlines()[-1]) if ran.returncode == 0 and ran.stdout.strip() else {"error": ran.stderr[-400:]}
        # Intl writes a narrow no-break space before am and pm in some versions, which reads as a space
        plain = lambda v: json.loads(json.dumps(v).replace("\\u202f", " "))
        en, us = plain(js["en"]), plain(js["en-US"])
        check("285: each dates choice writes the order it names, the month's name the language's, 2026-10-28 all numbers",
              en.get("dmy") == ["28 Oct 2026", "28 October 2026", "28 Oct", "3 Sep 2026"]
              and en.get("mdy") == ["Oct 28, 2026", "October 28, 2026", "Oct 28", "Sep 3, 2026"]
              and en.get("ymd") == ["2026-10-28", "2026-10-28", "10-28", "2026-09-03"]
              and us.get("dmy") == en.get("dmy") and us.get("mdy") == en.get("mdy"), str([en, us])[:600])
        check("285: each clock writes 14:05 or 2:05 pm, no leading zero in 12-hour, am and pm the language's way",
              en.get("24") == ["14:05", "09:05"] and en.get("12") == ["2:05 pm", "9:05 am"]
              and us.get("24") == ["14:05", "09:05"] and us.get("12") == ["2:05 PM", "9:05 AM"], str([en.get("12"), us.get("12")]))
        check("285: each numbers choice puts its own marks between the thousands and before the decimals",
              en.get("comma") == ["1,234.5", "1,284", "0.83"] and en.get("point") == ["1.234,5", "1.284", "0,83"]
              and en.get("space") == ["1 234,5", "1 284", "0,83"] and en.get("apostrophe") == ["1’234.5", "1’284", "0.83"],
              str([en.get(k) for k in ("comma", "point", "space", "apostrophe")]))
        check("285: with nothing chosen the language writes its own, the computer's own come next, and a choice in "
              "Settings wins over both",
              en.get("none") == ["28 October 2026", "14:05", "1,234.5"] and us.get("none") == ["October 28, 2026", "2:05 PM", "1,234.5"]
              and en.get("computer") == ["2026-10-28", "2:05 pm", "1.234,5"] and en.get("chosen") == ["28 October 2026", "14:05", "1,234.5"],
              str([en.get("none"), us.get("none"), en.get("computer"), en.get("chosen")]))
        check("285: the rows name each choice as an example of itself and the computer's own first, the one the "
              "settings hold ticked",
              en.get("rows") == {
                  "dates": ["( ) Same as this computer (Oct 28, 2026)", "( ) 28 Oct 2026", "( ) Oct 28, 2026", "(x) 2026-10-28"],
                  "time": ["(x) Same as this computer (14:05)", "( ) 14:05", "( ) 2:05 pm"],
                  "numbers": ["( ) Same as this computer (1,234.5)", "( ) 1,234.5", "( ) 1.234,5", "(x) 1 234,5", "( ) 1’234.5"]},
              str(en.get("rows")))

    # ── the page in every app, and the line opening the page on translating
    pages = {app: support.page_text(app=app) for app in ("idiograph", "sift", "trace")}
    order = {app: next(ln for ln in shell_lines() if ln.strip().startswith(f"{app}: [")) for app in pages}
    check("285: Language and formats follows General in each app's Settings, holding the Language rows and the "
          "three formats, General no longer holding Language",
          all('id="pane-formats"' in p and 'name="set-dates"' in p and 'name="set-numbers"' in p
              and p.index('id="pane-formats"') < p.index('id="set-language-computer"') for p in pages.values())
          and all(f"['general', 'formats'," in ln for ln in order.values())
          and all("set-language" not in general_of(p) for p in pages.values()), str(order))
    check("285: the line under Language is the whole link to the page on translating, in each app's name",
          '<a href="/translating" target="_blank" rel="noopener" id="translate-link">Help translate Idiograph into your language.</a>' in pages["idiograph"]
          and "Help translate Sift into your language." in pages["sift"])
    code, page = server.translating_page()
    gone_code, gone = server.translating_page(scratch / "no-such.md")
    sys.path.insert(0, str(support.source("packaging")))
    import build_mac
    shipped = {str(where) for _, where in build_mac.data_files("idiograph")}
    shipped_files = {Path(found).as_posix() for found, _ in build_mac.data_files("sift")}
    check("285: /translating serves docs/translating.md as a page with its lists, the bundle of every app carries it, "
          "and a copy without it says so",
          code == 200 and "<h1" in page and "Translating Idiograph" in page and "<ol><li>Copy each" in page
          and "<ul><li><code>family/static/i18n/en/</code>" in page and server.ROUTE_APP.get(server.TRANSLATING_PATH) == "shared"
          and "docs" in shipped and any(f.endswith("docs/translating.md") for f in shipped_files)
          and gone_code == 404 and "The page on translating is not in this copy of" in gone, f"{code} {gone_code}")


def general_of(page: str) -> str:
    """General's pane alone, from its opening to its section's end."""
    rest = page[page.index('id="pane-general"'):]
    return rest[:rest.index("</section>")]


def shell_lines() -> list[str]:
    return support.text("family/static/shell.js").splitlines()
