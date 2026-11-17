"""Area 405: the website's What's new (sitenews, 16 November 2026, Adam: "when we do a release update the website
with the release to show that").

packaging/site_whats_new.py writes site/holding/whats-new.html from docs/whats-new.md and versions.json, and the
release dates the nav's count reads into every page's nav script. The committed site must be what it writes, so a
version bump that forgets to run it goes red here; a version above versions.json's stays off the site; the page
shows the newest three released versions newest first, its notes the app's own lines, with a link to every release on GitHub; and every page with the site's nav
carries the What's new link and its script."""
from __future__ import annotations

import html
import importlib.util
import json
import re

from . import support
from .support import check as _check


def check(name, condition, detail="") -> None:
    _check(name, bool(condition), "" if condition else str(detail)[:600])


def load():
    path = support.TOOL / "packaging" / "site_whats_new.py"
    spec = importlib.util.spec_from_file_location("site_whats_new", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_site_whats_new():
    print("\n405. The website's What's new: the page and the nav's release dates are the generator's, released "
          "versions alone (sitenews)")
    sw = load()
    files = sw.outputs()
    stale = [p.name for p, text in files.items() if not p.is_file() or p.read_text(encoding="utf-8") != text]
    check("the committed site is what packaging/site_whats_new.py writes (run it after a version bump)",
          not stale, f"differs: {stale}")
    check("the generator gives the same bytes twice", files == sw.outputs())

    site = support.TOOL / "site" / "holding"
    with_nav = [p.name for p in site.glob("*.html") if 'class="site-nav"' in p.read_text(encoding="utf-8")]
    lacking = [n for n in with_nav if 'href="whats-new.html"' not in (site / n).read_text(encoding="utf-8")
               or 'id="nav-new-js"' not in (site / n).read_text(encoding="utf-8")]
    check("every page with the nav has What's new and its count's script", with_nav and not lacking, lacking)
    no_menu = [n for n in with_nav if not re.search(
        r'<button class="nav-burger" id="nav-burger" type="button" aria-label="Menu" aria-expanded="false" '
        r'aria-controls="site-nav">.*?</button>\s*<nav class="site-nav" id="site-nav"',
        (site / n).read_text(encoding="utf-8"), re.S)]
    check("every page with the nav has its Menu button for phones, named Menu and controlling the nav", not no_menu,
          no_menu)
    marked = {n: re.findall(r'href="([a-z-]+\.html)" aria-current="page"', (site / n).read_text(encoding="utf-8"))
              for n in with_nav}
    check("each page marks itself in the nav, the home page none",
          all(v == ([] if n == "index.html" else [n]) for n, v in marked.items()), marked)

    text = (support.TOOL / "docs" / "whats-new.md").read_text(encoding="utf-8")
    version = json.loads((support.TOOL / "versions.json").read_text(encoding="utf-8"))["idiograph"]
    import server as srv
    app_side = srv.whats_new_versions(text)
    rels = sw.releases(text, version)
    check("the site's versions are the app's, up to versions.json's",
          [(r["version"], r["date"], r["lines"]) for r in rels]
          == [(v["version"], v["date"], v["lines"]) for v in app_side
              if sw.as_tuple(v["version"]) <= sw.as_tuple(version)])
    page = files[site / sw.PAGE]
    shown = re.findall(r"Idiograph (\d+\.\d+\.\d+)<", page)
    top = rels[:sw.SHOWN]
    check("the page lists the newest three released versions once, newest first, and none older",
          shown == [r["version"] for r in top] and len(top) == min(3, len(rels)), shown)
    check("every line of those versions is on the page",
          all(f"<li>{html.escape(line)}</li>" in page for r in top for line in r["lines"]))
    check("the page links to every release on GitHub",
          'href="https://github.com/Pharkie/idiograph/releases"' in page and "All releases on GitHub" in page)

    five = "".join(f"## 0.{n}.0, {n} November 2026\n\nLine of version {n}.\n\n" for n in (5, 4, 3, 2, 1))
    made_up = sw.releases(five, "0.5.0")
    for layout in ("A", "B"):
        made = sw.page(made_up, layout)
        check(f"layout {layout}, five versions released: the newest three in order, none older, the GitHub link",
              re.findall(r"Idiograph (\d+\.\d+\.\d+)<", made) == ["0.5.0", "0.4.0", "0.3.0"]
              and "Line of version 2." not in made and "Line of version 1." not in made
              and "All releases on GitHub" in made)
    check("with five released, the nav's count still reads all five dates",
          len(re.findall(r'"\d{4}-\d{2}-\d{2}"', sw.nav_script(made_up))) == 5)
    check("with two released, the page shows two",
          re.findall(r"Idiograph (\d+\.\d+\.\d+)<", sw.page(sw.releases(five, "0.2.0"))) == ["0.2.0", "0.1.0"])

    ahead = "## 99.0.0, 1 January 2027\n\nA line not released yet.\n\n"
    marker = text.index("\n## ") + 1
    later = text[:marker] + ahead + text[marker:]
    held = sw.releases(later, version)
    check("a section above versions.json's version stays off the site",
          [r["version"] for r in held] == [r["version"] for r in rels]
          and "not released yet" not in sw.page(held))
    check("its date stays out of the nav's count", "2027-01-01" not in sw.nav_script(held))
    check("once versions.json reaches it, it heads the page",
          sw.releases(later, "99.0.0")[0]["version"] == "99.0.0")

    for layout in ("A", "B"):
        made = sw.page(rels, layout)
        check(f"layout {layout} shows the shown versions' notes",
              all(f"<li>{html.escape(line)}</li>" in made for r in top for line in r["lines"]))
    b = sw.page(rels, "B")
    check("layout B: the newest open, every older one shown a details row closed",
          b.count("<details") == len(top) - 1 and "<details open" not in b)
    check("layout A: no details rows", "<details" not in sw.page(rels, "A"))

    script = sw.nav_script(rels)
    check("the nav script holds every released version's date",
          all(r["iso"] in script for r in rels) and len(re.findall(r'"\d{4}-\d{2}-\d{2}"', script)) == len(rels))
    check("a date not like 16 November 2026 is refused",
          raises(lambda: sw.iso_date("16 Novembre 2026")) and sw.iso_date("1 November 2026") == "2026-11-01")
    check("no served page carries a comment", all("<!--" not in t for t in files.values()))


def raises(fn) -> bool:
    try:
        fn()
    except ValueError:
        return True
    return False
