"""Area 288: every date, time, number and length of time onto the formats (fmtsweep, 28 October 2026). The places
that wrote a time of day by hand (a board's History, the AI review's line, Mark complete's time, Updates' last
check), Sift's and Search's British dates and counts and the numbers with decimals in a sentence go through
i18n.js's tTime, tDate and tNum, so they follow Settings, Language and formats. The end card's time left and the
break's line say a length of time one way, from the catalogue. The server's dates for a person to read, a print
view's head and its marked-complete line and the interviewer notes file's Exported on, go through family/formats.py,
the month's name from the language's dates.json.

What is checked, in English (UK) and English (US): a sample of each kind of place under each choice, the settings'
choice first, the computer's own followed when the setting is empty, and the language's own with neither. In node on
the page's own functions: a board's History times, Mark complete's time, Updates' last check, Sift's review day, a
count over 999 in Sift's truncation table, the kappa, and the end card's and the break's lengths. In Python: a print
view's head and done line, and the notes file an export writes. Fixtures are the demo's invented workbook copied to
the scratch folder and invented times."""
from __future__ import annotations

import datetime as dt
import json
import os
import re
import shutil
from pathlib import Path

from . import support
from .support import check, demo_copy, demo_sheet, skip, DEMO_SHEET

UNSET = {"dates": "", "time": "", "numbers": ""}


def stmt(src: str, start: str) -> str:
    """A top-level statement or function of a script, from the line starting `start` to its end."""
    head = src.index("\n" + start) + 1
    if start.startswith(("function ", "async function ")):
        return src[head:src.index("\n}\n", head) + 3]
    return src[head:src.index(";\n", head) + 2]


def test_format_places(scratch: Path):
    print("\n288. Every date, time, number and length of time onto Language and formats: a board's History, Sift's "
          "review day and counts, the end card's length, a print head and the notes export, in English (UK) and (US) "
          "(28 October 2026)")
    import boot
    import i18n
    import formats
    import export as export_mod
    import themes_print
    import workbook as wb_mod

    # ── on screen, in node on the page's own functions
    if not shutil.which("node"):
        skip("288: the places on screen in node", "node is not on this machine")
    else:
        themes = support.text("apps/idiograph/static/themes.js")
        distil = support.text("apps/idiograph/static/distil.js")
        shell = support.text("family/static/shell.js")
        sset = support.text("apps/sift/static/sift_settings.js")
        ssearch = support.text("apps/sift/static/sift_search.js")
        pieces = "".join([
            stmt(themes, "const TH_DAY = "), stmt(themes, "const TH_DAY_YEAR = "), stmt(themes, "const thSameDay = "),
            stmt(themes, "const thClockOf = "), stmt(themes, "function thWhen("), stmt(themes, "function thDayOf("),
            stmt(themes, "function thHistoryDays("), stmt(themes, "function thReviewMade("),
            stmt(distil, "function whenOf("), stmt(distil, "function formatMinutes("), stmt(distil, "function haulTime("),
            stmt(shell, "const esc = "), stmt(shell, "function updWhen("), stmt(sset, "function reviewDay("),
            stmt(ssearch, "function sfsExported("), stmt(ssearch, "function sfsCheckable("),
            stmt(ssearch, "function sfsDrawCheck("),
            stmt(support.text("apps/sift/static/sift.js"), "const sfTwoKappa = "),
        ])
        cases = r"""
const els = {};
const $ = (id) => els[id] || (els[id] = { hidden: false, disabled: false, innerHTML: '', textContent: '' });
const sfsIsOther = () => false;
const sfsUnsaved = () => false;
const SFS = { data: { current: { version: 1 }, truncated: 1 }, plan: { databases: ['scopus'] }, checking: false,
  catalog: { truncates: ['scopus'], keyless: [], apis: ['scopus'] }, how: { scopus: 'api' },
  terms: { rows: [{ term: 'orchard*', name: 'Scopus', with: 1284, without: 12045.5, flag: '', said: '' }] } };
const now = new Date(2026, 9, 28, 18, 0);
const at = new Date(2026, 9, 28, 14, 5);
const history = [{ at: at.toISOString() }, { at: new Date(2026, 9, 1, 9, 4).toISOString() }];
const sample = () => {
  sfsDrawCheck(null);
  const cells = [...$('sfs-check').innerHTML.matchAll(/<td class="sfs-num"[^>]*>([^<]*)</g)].map((m) => m[1]);
  return {
    history: thHistoryDays(history, now).map((d) => [d.day, d.items.map((i) => i.time)]),
    when: [thWhen(at, now), thWhen(new Date(2025, 9, 1, 9, 4), now)],
    review: thReviewMade({ at: new Date(2026, 9, 1, 9, 4).toISOString(), model: 'Wren' }, now),
    mark: whenOf('2026-10-03T14:05:00'),
    updates: updWhen(new Date(2026, 8, 30, 14, 5).toISOString()),
    reviewDay: reviewDay('2026-10-28'),
    counts: cells,
    kappa: sfTwoKappa(0.8312),
    lengths: [formatMinutes(45), formatMinutes(60), formatMinutes(85), formatMinutes(150), haulTime(85 * 60), haulTime(20)],
  };
};
const out = {};
I18N_DATA.formats = { dates: 'dmy', time: '24', numbers: 'comma' };
out.uk = sample();
I18N_DATA.formats = { dates: 'mdy', time: '12', numbers: 'point' };
out.us = sample();
I18N_DATA.formats = { dates: 'ymd', time: '24', numbers: 'space' };
out.ymd = sample();
I18N_DATA.formats = { dates: '', time: '', numbers: '' };
I18N_DATA.computer_formats = { dates: 'mdy', time: '12', numbers: 'apostrophe' };
out.computer = sample();
I18N_DATA.computer_formats = { dates: '', time: '', numbers: '' };
out.own = sample();
console.log(JSON.stringify(out));
"""
        roots = boot.roots()
        lib = support.text("family/static/i18n.js")
        js = {}
        for tag in ("en", "en-US"):
            inline = i18n.script(tag, roots)[len("<script>"):-len("</script>")]
            ran = support.run_node(inline + "\n" + lib + "\n" + pieces + cases, scratch, f"a288-{tag}.js")
            js[tag] = (json.loads(ran.stdout.strip().splitlines()[-1]) if ran.returncode == 0 and ran.stdout.strip()
                       else {"error": ran.stderr[-600:]})
        # Intl writes a narrow no-break space before am and pm in some versions, which reads as a space
        plain = lambda v: json.loads(json.dumps(v).replace("\\u202f", " ").replace("\\u00a0", " "))
        en, us = plain(js["en"]), plain(js["en-US"])
        uk = en.get("uk", {})
        check("288: a board's History in 14:05, the day's heading and an older revision's day before its time, as before "
              "the sweep, in English (UK) with 28 Oct 2026 and 14:05 chosen",
              uk.get("history") == [["Today", ["14:05"]], ["1 October 2026", ["09:04"]]]
              and uk.get("when") == ["14:05", "1 October 2025 09:04"]
              and uk.get("review") == "Made by Wren on 1 October at 09:04." and uk.get("mark") == {"day": "3 Oct 2026", "time": "14:05"}
              and uk.get("updates") == "30 September at 14:05", str(uk or en))
        uk12 = en.get("us", {})
        check("288: with Oct 28, 2026 and 2:05 pm chosen the same places say 2:05 pm and 9:04 am, no leading zero, and "
              "the day in the month's order, in English (UK)",
              uk12.get("history") == [["Today", ["2:05 pm"]], ["October 1, 2026", ["9:04 am"]]]
              and uk12.get("when") == ["2:05 pm", "October 1, 2025 9:04 am"]
              and uk12.get("mark") == {"day": "Oct 3, 2026", "time": "2:05 pm"}
              and uk12.get("updates") == "September 30 at 2:05 pm", str(uk12))
        check("288: Sift's review day and a count over 999 follow the choice: 28 October 2026 and 1,284 and 12,045.5, "
              "October 28, 2026 and 1.284 and 12.045,5, 2026-10-28 and 1 284, the kappa 0.83 or 0,83",
              uk.get("reviewDay") == "28 October 2026" and uk.get("counts") == ["1,284", "12,045.5"] and uk.get("kappa") == "0.83"
              and uk12.get("reviewDay") == "October 28, 2026" and uk12.get("counts") == ["1.284", "12.045,5"]
              and uk12.get("kappa") == "0,83"
              and en.get("ymd", {}).get("reviewDay") == "2026-10-28" and en.get("ymd", {}).get("counts") == ["1 284", "12 045,5"],
              str([uk.get("counts"), uk12.get("counts"), en.get("ymd", {}).get("counts")]))
        lengths = ["45 min", "1 h", "1 h 25 min", "2 h 30 min", "1 h 25 min", ""]
        check("288: the end card's time left and the break's line say a length one way, 45 min, 1 h, 1 h 25 min, "
              "whatever the formats",
              all(v.get("lengths") == lengths for v in (uk, uk12, en.get("ymd", {}), us.get("uk", {}), us.get("own", {}))),
              str([uk.get("lengths"), us.get("own", {}).get("lengths")]))
        comp = en.get("computer", {})
        check("288: with the settings empty the computer's own is followed, its Oct 28, 2026, 2:05 pm and 1’284 in the "
              "same places",
              comp.get("history") == [["Today", ["2:05 pm"]], ["October 1, 2026", ["9:04 am"]]]
              and comp.get("reviewDay") == "October 28, 2026" and comp.get("counts") == ["1’284", "12’045.5"], str(comp))
        own_uk, own_us = en.get("own", {}), us.get("own", {})
        check("288: with neither, the language's own: British 14:05 and 28 October 2026, American 2:05 PM and "
              "October 28, 2026, both 1,284",
              own_uk.get("history") == [["Today", ["14:05"]], ["1 October 2026", ["09:04"]]]
              and own_uk.get("reviewDay") == "28 October 2026" and own_uk.get("counts") == ["1,284", "12,045.5"]
              and own_us.get("history") == [["Today", ["2:05 PM"]], ["October 1, 2026", ["9:04 AM"]]]
              and own_us.get("updates") == "September 30 at 2:05 PM"
              and own_us.get("reviewDay") == "October 28, 2026" and own_us.get("counts") == ["1,284", "12,045.5"],
              str([own_uk, own_us]))
        us_uk = us.get("uk", {})
        check("288: in English (US) a choice of 28 Oct 2026 and 14:05 is kept, the words American",
              us_uk.get("history") == [["Today", ["14:05"]], ["1 October 2026", ["09:04"]]]
              and us_uk.get("reviewDay") == "28 October 2026" and us_uk.get("updates") == "30 September at 14:05",
              str(us_uk))

    # ── the server's dates: a print head, a short date and the notes export
    saved = (i18n.CHOSEN_FORMATS, i18n.LANGUAGE, os.environ.get(i18n.COMPUTER_FORMATS))
    printed = dt.datetime(2026, 10, 28, 14, 5)
    done = {"at": "2026-10-04T19:02:00", "name": "Board 3"}
    root = scratch / "format-places"
    work = demo_copy(root, "Juno", "Juno - EN & ES.xlsx")
    _, _, him = demo_sheet(work)
    first = next(r["row"] for s in wb_mod.read_case(work)["sheets"] if s["name"] == DEMO_SHEET
                 for r in s["rows"] if r["name"] == him)
    wb_mod.save_interviewer_note(work, DEMO_SHEET, first, "Too soon", him)

    def server_side(lang: str, chosen: dict, computer: str | None) -> list:
        i18n.LANGUAGE = lambda: lang
        i18n.CHOSEN_FORMATS = lambda: chosen
        if computer is None:
            os.environ.pop(i18n.COMPUTER_FORMATS, None)
        else:
            os.environ[i18n.COMPUTER_FORMATS] = computer
        out = root / f"notes-{len(list(root.glob('notes-*.md')))}.md"
        export_mod.export_notes(work, "Juno", out=out, today=dt.date(2026, 10, 3))
        exported = next(ln for ln in out.read_text(encoding="utf-8").splitlines() if ln.startswith("Exported"))
        return [themes_print.when_printed(printed), formats.date_words(dt.datetime.fromisoformat(done["at"]), short=True), exported]

    american = json.dumps({"date": "10/28/26", "time": "2:05 PM", "number": "1,234.50"})
    try:
        py = {
            "dmy": server_side("en-GB", {"dates": "dmy"}, None),
            "mdy": server_side("en-GB", {"dates": "mdy"}, None),
            "ymd": server_side("en-GB", {"dates": "ymd"}, None),
            "computer": server_side("en-GB", {}, american),
            "own_uk": server_side("en-GB", {}, None),
            "own_us": server_side("en-US", {}, None),
            "us_dmy": server_side("en-US", {"dates": "dmy"}, american),
        }
    finally:
        i18n.CHOSEN_FORMATS, i18n.LANGUAGE = saved[0], saved[1]
        if saved[2] is None:
            os.environ.pop(i18n.COMPUTER_FORMATS, None)
        else:
            os.environ[i18n.COMPUTER_FORMATS] = saved[2]
    uk = ["28 October 2026", "4 Oct 2026", "Exported on 3 October 2026."]
    mdy = ["October 28, 2026", "Oct 4, 2026", "Exported on October 3, 2026."]
    check("288: a print view's head, a short date and the notes file's Exported on follow the dates "
          "choice: 28 October 2026, October 28, 2026 or 2026-10-28",
          py["dmy"] == uk and py["mdy"] == mdy
          and py["ymd"] == ["2026-10-28", "2026-10-04", "Exported on 2026-10-03."],
          str(py))
    check("288: with the setting empty the server follows the computer's own, else the language's own, British day "
          "first and American month first, and a choice is kept in English (US)",
          py["computer"] == mdy and py["own_uk"] == uk and py["own_us"] == mdy and py["us_dmy"] == uk, str(py))
    months = [i18n.t(k) for k in ("dates.month.january", "dates.mon.sep")]
    check("288: the month's names come from the language's dates.json, every month a key, Sep never Sept",
          months == ["January", "Sep"] and len(formats.LONG) == 12 and len(formats.SHORT) == 12
          and all(re.fullmatch(r"[A-Z][a-z]+", formats.LONG[n]()) for n in formats.LONG), str(months))
