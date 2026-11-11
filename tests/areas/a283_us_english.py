"""Area 283: American English, the text layer's first overlay, and the Language row under Settings, General
(i18nus, 28 October 2026, Adam's yes of that night). `en-US` folders beside the English catalogues hold only the
messages whose American English differs, whole sentences by key: spelling (color, center, capitalized, labeled,
anymore, Acknowledgments), words (quotation marks, apartment, checked, Eggplant), and
dates in American order through tDate. The row offers Same as this computer, named as the app reads it, English
(UK) and English (US), saved at once and applied by loading the page again.

What is checked: every key of the overlay is in English with the same slots and the same plural forms and differs
from it, the overlay ships in the window's bundle, en-US gives Center where English gives Centre through t() in Python,
in the served page and in the scripts, a date in American order, the window's menus reading the same in both, the
row's choice saved alone and kept across a restart (a fresh process reading the settings file), an empty choice
following the computer, and the row ticking what the settings hold. Fixtures are invented settings files in the
scratch folder. Since i18nus2 (28 October 2026) English says Set aside where it said Bin, as the boards' sidebar
does, so the overlay holds no word for the bin."""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

from . import support
from .support import check, skip

US = "en-US"


def slots(message) -> set:
    import i18n
    parts = message.values() if isinstance(message, dict) else [message]
    return {m for p in parts for m in i18n.SLOT.findall(str(p))}


def test_us_english(scratch: Path):
    print("\n283. American English and the Language row: the en-US overlay's keys in English with the same slots and "
          "plural forms, Center where English says Centre in Python, the page and the scripts, American dates, the "
          "choice saved and kept across a restart, and an empty one following the computer (28 October 2026)")
    import boot
    import i18n
    import server

    roots = boot.roots()
    english = i18n.own(i18n.BASE, roots)
    overlay = i18n.own(US, roots)
    folders = sorted({p.parent.relative_to(support.TOOL).as_posix() for p in i18n.files(US, roots)})
    check("283: the en-US overlay is a folder beside the family's English and Idiograph's",
          {"family/static/i18n/en-US", "apps/idiograph/static/i18n/en-US"} <= set(folders) and len(overlay) >= 30,
          f"{folders}, {len(overlay)} keys")
    wrong = []
    for key, message in overlay.items():
        base = english.get(key)
        if base is None:
            wrong.append(f"{key} is not in English")
        elif isinstance(base, dict) != isinstance(message, dict) or (isinstance(base, dict) and set(base) != set(message)):
            wrong.append(f"{key} has other plural forms than English")
        elif slots(base) != slots(message):
            wrong.append(f"{key} has other slots than English")
        elif base == message:
            wrong.append(f"{key} says what English says")
    check("283: every key of the overlay is in English with the same slots and plural forms, and says it otherwise",
          not wrong, "; ".join(wrong[:6]))

    sys.path.insert(0, str(support.source("packaging")))
    import build_mac
    carried = set(build_mac.static_files("idiograph"))
    check("283: the window's bundle carries the overlay in its static/i18n/en-US/, beside English",
          {"i18n/en-US/page.json", "i18n/en-US/themes.json", "i18n/en-US/page_idiograph.json"} <= carried
          and "i18n/en/menus.json" in carried, str(sorted(p for p in carried if p.startswith("i18n/en-US"))))

    # ── Center where English says Centre, through t() in Python and in the served page
    # (the overlay's one count, a review round's "checked", went with the AI review on 11 November 2026, aiout)
    said = {tag: (i18n.t("page_idiograph.screens.centre", lang=tag),
                  i18n.t("server.colour_another_participant_s_nothing", lang=tag)) for tag in ("en", "en-GB", US)}
    check("283: in Python en-US says Center where English, and English (UK), says Centre, its refusals too",
          said["en"] == said["en-GB"] == ("Centre", "That colour is another participant's, so nothing was changed.")
          and said[US] == ("Center", "That color is another participant's, so nothing was changed."), str(said))
    check("283: a message the overlay leaves alone reads English's in en-US",
          i18n.t("themes.pile.put_back", lang=US) == i18n.t("themes.pile.put_back", lang="en") == "Put back")
    menus = {k: v for k, v in i18n.messages(US, roots).items() if k.startswith("menus.")}
    check("283: the window's menus read the same in en-US as in English, none of their words differing",
          menus == {k: v for k, v in english.items() if k.startswith("menus.")} and menus.get("menus.minimize") == "Minimize",
          str(len(menus)))

    saved_path = server.CONFIG_PATH
    config = scratch / "a283-config.json"
    pages = {}
    try:
        server.CONFIG_PATH = config
        config.write_text(json.dumps({"interviewer": "Ada", "appearance": "dark"}, indent=2), encoding="utf-8")
        for tag in ("en-GB", US):
            answer = server.api_settings({"language": tag})
            pages[tag] = server.own_page(support.page_text(), "idiograph")
            pages[tag + ":language"] = answer["config"].get("language")
        kept = json.loads(config.read_text(encoding="utf-8"))
        server.api_settings({"language": "English please"})
        refused = json.loads(config.read_text(encoding="utf-8")).get("language")
    finally:
        server.CONFIG_PATH = saved_path
    check("283: the row's choice sent alone is saved alone, the rest of the settings file as it was, and a tag that "
          "is no language refused",
          pages["en-GB:language"] == "en-GB" and pages[US + ":language"] == US
          and kept == {"interviewer": "Ada", "appearance": "dark", "language": US} and refused == US, str(kept))
    check("283: the served page is in the language chosen, its lang the locale and the palette's Center in en-US",
          '<html lang="en-US"' in pages[US] and '<span class="th-pal-word">Center</span>' in pages[US]
          and '<html lang="en-GB"' in pages["en-GB"] and '<span class="th-pal-word">Centre</span>' in pages["en-GB"]
          and '"computer":"en-GB"' in pages[US], pages[US][:200])

    # ── kept across a restart: a fresh process reads the settings file and is in American English
    fresh = (
        "import sys, json\nfrom pathlib import Path\nsys.path.insert(0, %r)\nimport boot\nboot.setup()\n"
        "import server, i18n\nserver.CONFIG_PATH = Path(%r)\n"
        "print(json.dumps([server.page_language(), i18n.t('page_idiograph.screens.centre'), i18n.locale_of(server.page_language())]))\n"
    ) % (str(support.TOOL), str(config))
    env = dict(os.environ, **{i18n.COMPUTER_STANDIN: "en-GB"})
    run = subprocess.run([sys.executable, "-I", "-c", fresh], capture_output=True, text=True, encoding="utf-8",
                         timeout=120, env=env)
    after = json.loads(run.stdout.strip().splitlines()[-1]) if run.returncode == 0 and run.stdout.strip() else run.stderr[-300:]
    check("283: the choice is kept across a restart, a fresh process reading en-US and Center from the settings file",
          after == [US, "Center", US], str(after))

    # ── unset follows the computer: an empty choice in a computer whose language is American English, then British
    standin = os.environ.get(i18n.COMPUTER_STANDIN)
    follows = {}
    try:
        server.CONFIG_PATH = config
        server.api_settings({"language": ""})
        follows["saved"] = json.loads(config.read_text(encoding="utf-8")).get("language")
        for computer in (US, "en-GB", "fr-FR"):
            os.environ[i18n.COMPUTER_STANDIN] = computer
            i18n._COMPUTER.clear()
            follows[computer] = (server.page_language(), i18n.t("page_idiograph.screens.centre"),
                                 json.loads(i18n.script()[len("<script>var I18N = "):-len(";</script>")])["computer"])
    finally:
        server.CONFIG_PATH = saved_path
        if standin is None:
            os.environ.pop(i18n.COMPUTER_STANDIN, None)
        else:
            os.environ[i18n.COMPUTER_STANDIN] = standin
        i18n._COMPUTER.clear()
    check("283: an empty choice follows the computer, Center on one in American English, Centre on one in British "
          "English, and English (UK) on one in a language the app has no words for",
          follows.get("saved") == "" and follows.get(US) == (US, "Center", US)
          and follows.get("en-GB") == ("en-GB", "Centre", "en-GB") and follows.get("fr-FR") == ("fr-FR", "Centre", "en-GB"),
          str(follows))

    # ── the scripts' side: t() and tDate in each language, and the row ticking what the settings hold
    node = shutil.which("node")
    if not node:
        skip("283: the scripts' side under node", "node is not on this machine")
        return
    lib = support.text("family/static/i18n.js")
    shell = support.text("family/static/shell.js")
    piece = lambda name: f"function {name}(" + shell.split(f"function {name}(", 1)[1].split("\n}\n", 1)[0] + "\n}\n"
    row = next(ln for ln in shell.splitlines() if ln.startswith("const LANGUAGE_ROW = ")) + "\n"
    cases = r"""
const rows = ['', 'en-GB', 'en-US'].map((value) => ({ value, checked: false }));
const word = { textContent: '' };
const $ = (id) => (id === 'language-computer-word' ? word : null);
globalThis.document = { querySelectorAll: () => rows };
const out = {
  centre: t('page_idiograph.screens.centre'),
  color: t('themes.sticky.colour'),
  date: tDate(new Date(Date.UTC(2026, 9, 28)), { day: 'numeric', month: 'long', year: 'numeric', timeZone: 'UTC' }),
  short: tDate(new Date(Date.UTC(2026, 8, 3)), { day: 'numeric', month: 'short', year: 'numeric', timeZone: 'UTC' }),
  ticked: {},
};
for (const set of ['', 'en-US', 'en-GB', 'en']) {
  LANGUAGE_ROW.set = set;
  drawLanguage();
  out.ticked[set] = rows.filter((r) => r.checked).map((r) => r.value);
}
out.computer = word.textContent;
console.log(JSON.stringify(out));
"""
    js = {}
    # each on a computer of its own country, whose formats the window hands the server (fmtcore): the order of a
    # date is the computer's or the setting's since then, the month's name the language's
    countries = {"en": '{"date": "28/10/2026", "time": "14:05", "number": "1,234.5"}',
                 US: '{"date": "10/28/26", "time": "2:05 PM", "number": "1,234.50"}'}
    held_formats = os.environ.get(i18n.COMPUTER_FORMATS)
    for tag in ("en", US):
        os.environ[i18n.COMPUTER_FORMATS] = countries[tag]
        try:
            inline = i18n.script(tag, roots)[len("<script>"):-len("</script>")]
        finally:
            if held_formats is None:
                os.environ.pop(i18n.COMPUTER_FORMATS, None)
            else:
                os.environ[i18n.COMPUTER_FORMATS] = held_formats
        harness = scratch / f"a283-{tag}.js"
        harness.write_text(inline + "\n" + lib + "\n" + row + piece("drawLanguage") + cases, encoding="utf-8")
        ran = subprocess.run([node, str(harness)], capture_output=True, text=True, encoding="utf-8", timeout=60)
        js[tag] = json.loads(ran.stdout.strip().splitlines()[-1]) if ran.returncode == 0 and ran.stdout.strip() else {"error": ran.stderr[-300:]}
    en, us = js["en"], js[US]
    check("283: in the scripts en-US says Center and Color where English says Centre and Colour",
          [en.get("centre"), en.get("color")] == ["Centre", "Colour"]
          and [us.get("centre"), us.get("color")] == ["Center", "Color"],
          str([en, us]))
    check("283: a date through tDate is in American order in en-US and British in English, Sep kept in British",
          en.get("date") == "28 October 2026" and us.get("date") == "October 28, 2026"
          and en.get("short") == "3 Sep 2026" and us.get("short") == "Sep 3, 2026", str([en.get("date"), us.get("date"), en.get("short"), us.get("short")]))
    check("283: the Language row ticks what the settings hold, Same as this computer for none, English (UK) for en-GB "
          "or en, and names the computer's language as the app reads it",
          en.get("ticked") == {"": [""], "en-US": ["en-US"], "en-GB": ["en-GB"], "en": ["en-GB"]}
          and en.get("computer") == "Same as this computer (English, UK)", str([en.get("ticked"), en.get("computer")]))
