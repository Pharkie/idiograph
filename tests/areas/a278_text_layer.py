"""Area 278: the text layer's core (i18ncore, 28 October 2026, Adam's ruling of that night). Every word the page shows
comes from one catalogue of messages by key, English first and British, other languages and overlays (en-US, later
en.ta, es) files of the same shape that replace whole messages by key. family/i18n.py is its Python side, the
server's t() and the page's {{key}} markers filled as the page is put together, family/static/i18n.js its scripts'
side, t(), tDate and tList, and the shell's own words (shell.js and page.html) the first slice moved into it.

What is checked: the catalogue's shape (one JSON object a file, every key under its file's name, a plural with
`other`), every key the scripts, the page and the server use is in English and every English key is used, every key
of another language or overlay is in English with the same slots, plurals and slots fill and a missing key falls
back to English and then to the key itself on both sides, alike, the served page has every marker filled, the dates
the three month tables wrote come out of Intl the same, and the language setting is saved and followed. Fixtures
are invented, a catalogue about garden birds."""
from __future__ import annotations

import json
import re
import shutil
import subprocess
from pathlib import Path

from . import support
from .support import check, skip

PLURALS = {"zero", "one", "two", "few", "many", "other"}
# the three tables the page wrote its months from until i18ncore, which Intl's output must match
MONTHS_LONG = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October",
               "November", "December"]
MONTHS_SHORT = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
WEEKDAYS = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]


def catalogue_problems(roots) -> list[str]:
    """What is wrong with the catalogue under `roots`: a file that is not one object, a key not under its file's
    name or not a key, a message neither text nor plural forms with `other`, a file name in two folders of one
    language (the bundle merges every static/ into one), and a key of another language missing from English or
    with other slots than English's."""
    import i18n
    out = []
    english = i18n.own(i18n.BASE, roots)
    for tag in i18n.languages(roots):
        seen: dict = {}
        for path in i18n.files(tag, roots):
            if path.name in seen:
                out.append(f"{tag}/{path.name} in two folders")
            seen[path.name] = path
            try:
                data = json.loads(path.read_text(encoding="utf-8"))
            except ValueError as exc:
                out.append(f"{path.name}: {exc}")
                continue
            if not isinstance(data, dict):
                out.append(f"{tag}/{path.name} is not one object")
                continue
            for key, value in data.items():
                if not i18n.KEY.match(key) or not key.startswith(path.stem + "."):
                    out.append(f"{tag}/{path.name}: {key} is not under {path.stem}.")
                if isinstance(value, dict):
                    if "other" not in value or set(value) - PLURALS or not all(isinstance(v, str) for v in value.values()):
                        out.append(f"{tag}: {key}'s plural forms")
                elif not isinstance(value, str):
                    out.append(f"{tag}: {key} is neither text nor plural forms")
                if tag == i18n.BASE:
                    continue
                if key not in english:
                    out.append(f"{tag}: {key} is not in English")
                elif slots(value) != slots(english[key]):
                    out.append(f"{tag}: {key} has other slots than English")
    return out


def slots(message) -> set:
    import i18n
    parts = message.values() if isinstance(message, dict) else [message]
    return {m for p in parts for m in i18n.SLOT.findall(str(p))} - {"n"}


def used_keys(stems: set) -> tuple[set, list]:
    """Every key the page's scripts and markup and the server's Python name, and where: a quoted literal in a script
    whose first word is a catalogue file's name, a {{key}} marker in the markup, and in Python a t("key") call."""
    import i18n
    found: set = set()
    places: list = []
    lit = re.compile(r"""['"`]([a-z][a-z0-9_]*(?:\.[a-z0-9_]+)+)['"`]""")
    pycall = re.compile(r"""\bt\(\s*['"]([a-z][a-z0-9_]*(?:\.[a-z0-9_]+)+)['"]""")
    for folder in support.static_folders():
        for path in sorted(folder.glob("*.js")):
            # comments set aside, since one may name a setting or a function, `themes.cap`, under a file's name
            code = re.sub(r"(?m)^\s*//.*$", "", re.sub(r"/\*.*?\*/", "", path.read_text(encoding="utf-8"), flags=re.S))
            for key in lit.findall(code):
                if key.split(".", 1)[0] in stems:
                    found.add(key)
                    places.append((path.name, key))
        for path in sorted(folder.glob("*.html")):
            for key in i18n.MARK.findall(path.read_text(encoding="utf-8")):
                found.add(key)
                places.append((path.name, key))
    for path in support.code_files():
        for key in pycall.findall(path.read_text(encoding="utf-8")):
            found.add(key)
            places.append((path.name, key))
    # the window's own words, its menus and messages, through words.rs's t, t_app and t_with (i18nserver)
    rscall = re.compile(r"""\bt(?:_app|_with)?\(\s*"([a-z][a-z0-9_]*(?:\.[a-z0-9_]+)+)\"""")
    for path in sorted((support.TOOL / "packaging" / "tauri" / "src-tauri" / "src").glob("*.rs")):
        for key in rscall.findall(path.read_text(encoding="utf-8")):
            found.add(key)
            places.append((path.name, key))
    return found, places


def test_text_layer(scratch: Path):
    print("\n278. The text layer: the catalogue's shape, every key used in English and every English key used, other "
          "languages' keys in English, plurals, slots and fallback alike in Python and the scripts, every marker "
          "filled, the month tables' dates out of Intl the same, and the language setting (28 October 2026)")
    import boot
    import i18n
    import server

    roots = boot.roots()
    english = i18n.own(i18n.BASE, roots)
    problems = catalogue_problems(roots)
    check("278: every catalogue file is one object, every key under its file's name, every plural with other, and "
          "every other language's key in English with English's slots", not problems, "; ".join(problems[:6]))
    stems = {p.stem for p in i18n.files(i18n.BASE, roots)}
    check("278: the shell's slice is in the catalogue, family/static/i18n/en/shell.json and page.json",
          {"shell", "page"} <= stems, str(sorted(stems)))
    used, places = used_keys(stems)
    missing = sorted(used - set(english))
    check("278: every key a script, the page's markup or the server names is in English", not missing,
          ", ".join(f"{f}: {k}" for f, k in places if k in missing)[:400])
    stale = sorted(set(english) - used)
    check("278: every English key is used somewhere, so the catalogue keeps no stale words", not stale, ", ".join(stale[:10]))

    # ── a fixture catalogue: English, Spanish lacking one message, an en-US overlay replacing one, and a stray key
    fx = scratch / "i18n-278"
    shutil.rmtree(fx, ignore_errors=True)
    base = fx / "static" / "i18n"
    files = {
        "en/birds.json": {"birds.count": {"one": "{n} bird", "other": "{n} birds"},
                          "birds.seen": "{who} saw {n} birds at the feeder.",
                          "birds.colour": "The colour of the {bird}"},
        "es/birds.json": {"birds.count": {"one": "{n} pájaro", "other": "{n} pájaros"}},
        "en-US/birds.json": {"birds.colour": "The color of the {bird}"},
    }
    for rel, data in files.items():
        (base / rel).parent.mkdir(parents=True, exist_ok=True)
        (base / rel).write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
    froots = [fx]
    check("278: a fixture catalogue in good shape has no problems", not catalogue_problems(froots),
          str(catalogue_problems(froots)))
    check("278: a lookup takes the most specific folder first and English last, only folders that exist",
          i18n.chain("en-US", froots) == ["en-US", "en"] and i18n.chain("es-MX", froots) == ["es", "en"]
          and i18n.chain("fr", froots) == ["en"] and i18n.chain("en-GB", froots) == ["en"],
          str([i18n.chain(t, froots) for t in ("en-US", "es-MX", "fr", "en-GB")]))
    check("278: the locale is the folder's, English's being en-GB, so a computer in en-AU reads en-GB while no en-AU "
          "overlay is there, and en-US reads en-US in the app's own catalogue since its overlay (i18nus)",
          i18n.locale_of("en-US", froots) == "en-US" and i18n.locale_of("en-AU", froots) == "en-GB"
          and i18n.locale_of("en-US", roots) == "en-US"
          and i18n.locale_of("es-MX", froots) == "es" and i18n.locale_of("fr", froots) == "en-GB")
    py = {
        "one": i18n.t("birds.count", {"n": 1}, lang="en", roots=froots),
        "none": i18n.t("birds.count", {"n": 0}, lang="en", roots=froots),
        "many": i18n.t("birds.count", n=12, lang="en", roots=froots),
        "slots": i18n.t("birds.seen", {"who": "Wren", "n": 3}, lang="en", roots=froots),
        "es_one": i18n.t("birds.count", {"n": 1}, lang="es", roots=froots),
        "es_fallback": i18n.t("birds.seen", {"who": "Wren", "n": 3}, lang="es", roots=froots),
        "us": i18n.t("birds.colour", {"bird": "robin"}, lang="en-US", roots=froots),
        "gb": i18n.t("birds.colour", {"bird": "robin"}, lang="en-GB", roots=froots),
        "missing": i18n.t("birds.nowhere", lang="es", roots=froots),
        "slot_left": i18n.t("birds.colour", lang="en", roots=froots),
    }
    want = {"one": "1 bird", "none": "0 birds", "many": "12 birds", "slots": "Wren saw 3 birds at the feeder.",
            "es_one": "1 pájaro", "es_fallback": "Wren saw 3 birds at the feeder.", "us": "The color of the robin",
            "gb": "The colour of the robin", "missing": "birds.nowhere", "slot_left": "The colour of the {bird}"}
    check("278: in Python a count picks its plural form, slots fill, Spanish falls back to English for a message it "
          "lacks, an overlay replaces a whole message, a key nowhere is the key itself", py == want,
          str({k: v for k, v in py.items() if want[k] != v}))
    (base / "es" / "stray.json").write_text(json.dumps({"stray.word": "palabra", "birds.extra": "x"}), encoding="utf-8")
    (base / "es" / "birds.json").write_text(json.dumps({"birds.count": {"one": "{n} pájaro", "other": "{count} pájaros"},
                                                        "birds.seen": "{quien} vio pájaros."}), encoding="utf-8")
    bad = catalogue_problems(froots)
    check("278: a key of another language missing from English, one under another file's name and one with other "
          "slots than English's are each named",
          any("stray.word is not in English" in b for b in bad) and any("birds.extra is not under stray" in b for b in bad)
          and any("birds.seen has other slots" in b for b in bad) and any("birds.count has other slots" in b for b in bad),
          "; ".join(bad))
    (base / "es" / "stray.json").unlink()
    (base / "es" / "birds.json").write_text(json.dumps(files["es/birds.json"], ensure_ascii=False), encoding="utf-8")

    # ── the page: every marker filled in each app's page, the catalogue there for the scripts, its lang the locale
    for app in boot.APPS:
        page = server.own_page(support.page_text(app=app), app)
        left = sorted(set(re.findall(r"\{\{[^}]*\}\}", page)))
        check(f"278: {app}'s page has every marker filled and the catalogue inline before the first script",
              not left and "var I18N = " in page and page.index("var I18N = ") < page.index('<script src="/i18n.js">')
              < page.index('<script src="/shell.js">') and '<html lang="en-GB"' in page, str(left[:5]))
    filled = i18n.fill('<p title="{{birds.colour}}">{{birds.seen}} &amp; {{birds.gone}}</p>', "en", froots,
                       {"bird": 'a "robin"', "who": "<Wren>", "n": 2})
    check("278: a marker's message is escaped in the markup, its slots filled, and a missing one shows its key",
          filled == '<p title="The colour of the a &quot;robin&quot;">&lt;Wren&gt; saw 2 birds at the feeder. &amp; '
                    'birds.gone</p>', filled)

    node = shutil.which("node")
    if not node:
        skip("278: the scripts' side under node", "node is not on this machine")
    else:
        lib = support.text("family/static/i18n.js")
        cases = r"""
const out = {};
const warned = [];
console.warn = (m) => warned.push(String(m));
out.one = t('birds.count', { n: 1 }); out.none = t('birds.count', { n: 0 }); out.many = t('birds.count', { n: 12 });
out.slots = t('birds.seen', { who: 'Wren', n: 3 }); out.colour = t('birds.colour', { bird: 'robin' });
out.missing = t('birds.nowhere'); t('birds.nowhere'); out.slot_left = t('birds.colour');
out.warned = warned.length;
out.list = tList(['Wren', 'Robin', 'Jay']);
console.log(JSON.stringify(out));
"""
        js = {}
        for tag in ("en", "es", "en-US"):
            inline = i18n.script(tag, froots)[len("<script>"):-len("</script>")]
            harness = scratch / f"a278-{tag}.js"
            harness.write_text(inline + "\n" + lib + "\n" + cases, encoding="utf-8")
            run = subprocess.run([node, str(harness)], capture_output=True, text=True, encoding="utf-8", timeout=60)
            js[tag] = json.loads(run.stdout.strip().splitlines()[-1]) if run.returncode == 0 and run.stdout.strip() else {"error": run.stderr[-300:]}
        en, es, us = js["en"], js["es"], js["en-US"]
        check("278: in the scripts a count picks its plural form and slots fill as in Python",
              [en.get(k) for k in ("one", "none", "many", "slots", "slot_left")]
              == [py["one"], py["none"], py["many"], py["slots"], py["slot_left"]], str(en))
        check("278: in the scripts Spanish falls back to English for a message it lacks and an overlay replaces a "
              "whole message, as in Python",
              es.get("one") == py["es_one"] and es.get("slots") == py["es_fallback"] and us.get("colour") == py["us"]
              and en.get("colour") == py["gb"], str([es, us]))
        check("278: in the scripts a key nowhere shows as itself and is named in the console once however often it is "
              "asked", en.get("missing") == "birds.nowhere" and en.get("warned") == 1, str(en))
        check("278: a list joins as the locale joins it, British English with no comma before and",
              en.get("list") == "Wren, Robin and Jay" and us.get("list") == "Wren, Robin, and Jay", str([en.get("list"), us.get("list")]))

        # ── the month tables: the same English out of Intl, in each of the three places
        table = support.text("family/static/table.js")
        distil = support.text("apps/idiograph/static/distil.js")
        themes = support.text("apps/idiograph/static/themes.js")
        fn = lambda src, name: f"function {name}(" + src.split(f"function {name}(", 1)[1].split("\n}\n", 1)[0] + "\n}\n"
        line = lambda src, start: next(ln for ln in src.splitlines() if ln.startswith(start)) + "\n"
        pieces = (fn(table, "tbDayWords") + fn(distil, "whenOf")
                  + line(themes, "const TH_DAY = ") + line(themes, "const TH_DAY_YEAR = ")
                  + "const thSameDay = (a, b) => a.getFullYear() === b.getFullYear() && a.getMonth() === b.getMonth()\n"
                    "  && a.getDate() === b.getDate();\n"
                  + line(themes, "const thClockOf = ") + fn(themes, "thWhen") + fn(themes, "thDayOf"))
        dates = r"""
const out = { long: [], short: [], when: [], day: [] };
const now = new Date(2026, 9, 28, 9, 0);
for (let m = 1; m <= 12; m++) {
  const mm = String(m).padStart(2, '0');
  out.long.push(tbDayWords(`2026-${mm}-12`));
  out.short.push(whenOf(`2026-${mm}-03T14:05:00`).day);
  out.when.push(thWhen(new Date(2025, m - 1, 1, 12, 4).toISOString(), now));
  out.day.push(thDayOf(new Date(2026, m - 1, 9, 8, 0), now));
}
out.notDate = [tbDayWords('soon'), whenOf('soon').day, tbDayWords('2026-13-01')];
console.log(JSON.stringify(out));
"""
        harness = scratch / "a278-dates.js"
        harness.write_text(support.i18n_js() + pieces + dates, encoding="utf-8")
        run = subprocess.run([node, str(harness)], capture_output=True, text=True, encoding="utf-8", timeout=60)
        if run.returncode != 0:
            check("278: the month tables' functions run in node", False, run.stderr.strip()[-400:])
        else:
            d = json.loads(run.stdout.strip().splitlines()[-1])
            check("278: Lists' and Sift's days (tbDayWords) say 12 October 2026 for every month as the table did",
                  d["long"] == [f"12 {m} 2026" for m in MONTHS_LONG], str(d["long"]))
            check("278: Mark complete's day (whenOf) says 3 Oct 2026 for every month as the table did, Sep never Sept",
                  d["short"] == [f"3 {m} 2026" for m in MONTHS_SHORT], str(d["short"]))
            check("278: the boards' history says 1 October 2025 12:04 for another year's revision and 9 October 2026 for "
                  "a day this year, every month as the table did",
                  d["when"] == [f"1 {m} 2025 12:04" for m in MONTHS_LONG]
                  and d["day"] == [f"9 {m} 2026" for m in MONTHS_LONG], str([d["when"], d["day"]]))
            check("278: what is not a date stands as it is, as before", d["notDate"] == ["soon", "", "2026-13-01"],
                  str(d["notDate"]))

    # ── the language setting: saved from Settings' save when sent, a bad tag refused, and the page following it
    saved = server.CONFIG_PATH
    try:
        server.CONFIG_PATH = scratch / "language-config.json"
        server.CONFIG_PATH.write_text(json.dumps({"interviewer": "Adam"}), encoding="utf-8")
        server.api_settings({"language": "es"})
        first = json.loads(server.CONFIG_PATH.read_text(encoding="utf-8")).get("language")
        server.api_settings({"language": "Español!"})
        kept = json.loads(server.CONFIG_PATH.read_text(encoding="utf-8")).get("language")
        chosen = server.page_language()
        server.api_settings({"language": ""})
        cleared = json.loads(server.CONFIG_PATH.read_text(encoding="utf-8")).get("language")
        following = server.page_language()
    finally:
        server.CONFIG_PATH = saved
    check("278: a language sent with the settings is saved, a tag that is no language is refused, and an empty one "
          "saved as following the computer", first == "es" and kept == "es" and chosen == "es" and cleared == ""
          and following == i18n.computer_language(), str([first, kept, chosen, cleared, following]))
    check("278: the computer's language is a tag the catalogue can look up",
          bool(i18n.TAG.match(i18n.computer_language())), i18n.computer_language())
    check("278: a tag is read in the catalogue's form whatever the system writes",
          [i18n.normal(x) for x in ("en_GB.UTF-8", "es-mx", "C", "", "pt_BR@euro")] == ["en-GB", "es-MX", "", "", "pt-BR"])
