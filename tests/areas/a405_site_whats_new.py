"""Area 405: the website's What's new (sitenews, 16 November 2026, Adam: "when we do a release update the website
with the release to show that").

packaging/site_whats_new.py writes site/holding/whats-new.html from docs/whats-new.md and versions.json, and the
release dates the nav's count reads into every page's nav script. The committed site must be what it writes, so a
version bump that forgets to run it goes red here; a version above versions.json's stays off the site; the page
shows the newest three released versions newest first, its notes the app's own lines, with a link to every release on GitHub; and every page with the site's nav
carries the What's new link and its script. The manual's page (manual.html, sitemanual, 18 November 2026) is written
by the same generator from docs/manual.md with the app's own renderer, so the committed page must be current and
every heading's anchor the app's own."""
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
    check("each page marks itself in the nav, the home page, the manual and the join page none",
          all(v == ([] if n in ("index.html", sw.MANUAL, "join.html") else [n]) for n, v in marked.items()), marked)

    dl = (site / "download.html").read_text(encoding="utf-8")
    others = [n for n in with_nav if n != "download.html"]
    check("on the Download page the nav's Download is a plain link marked current, on every other page a button",
          '<a href="download.html" aria-current="page">Download</a>' in dl and 'class="nav-dl"' not in dl
          and all('<a class="nav-dl" href="download.html">Download</a>' in (site / n).read_text(encoding="utf-8")
                  for n in others), others)
    foots = {n: re.search(r'<div class="get"[^>]*>(.*?)</div>', (site / n).read_text(encoding="utf-8"), re.S)
             for n in others}
    check("every other page's foot holds the visitor's button alone: no link, no details, no other downloads",
          all(m and 'class="get-line"' in m.group(1) and "<a" not in m.group(1) and "get-more" not in m.group(1)
              and "get-install" not in m.group(1) and "first-open" not in m.group(1) for m in foots.values()),
          [n for n, m in foots.items() if not m or "<a" in m.group(1)])
    get_js = (site / "get.js").read_text(encoding="utf-8")
    check("no foot's button carries #start: it opens the Download page alone (Adam, 17 November 2026)",
          "#start" not in get_js and not [n for n in with_nav if "download.html#start" in (site / n).read_text(encoding="utf-8")]
          and "full ? FILES + file : 'download.html')" in get_js)
    check("get.js starts no download on load: no click it makes, no download link, no reading the address",
          ".click(" not in get_js and "'download'" not in get_js and "location" not in get_js
          and "history." not in get_js)
    check("the Download page holds both first-open steps, the version and the other links, and the latest version",
          'id="fo-mac"' in dl and 'id="fo-windows"' in dl and 'id="get-other"' in dl
          and f'<p class="get-version">Version {sw.releases((support.TOOL / "docs" / "whats-new.md").read_text(encoding="utf-8"), json.loads((support.TOOL / "versions.json").read_text(encoding="utf-8"))["idiograph"])[0]["version"]}</p>' in dl)
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
    check("with five released and all within seven days, the nav script holds exactly the three shown releases' dates, so the count reaches three at most",
          re.search(r"d=(\[[^\]]*\])", sw.nav_script(made_up)).group(1)
          == '["2026-11-05","2026-11-04","2026-11-03"]'
          and len(re.findall(r'"\d{4}-\d{2}-\d{2}"', sw.nav_script(made_up))) == sw.SHOWN)
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
    check("the nav script holds exactly the shown releases' dates, no older release's",
          all(r["iso"] in script for r in top) and len(re.findall(r'"\d{4}-\d{2}-\d{2}"', script)) == len(top))
    check("a date not like 16 November 2026 is refused",
          raises(lambda: sw.iso_date("16 Novembre 2026")) and sw.iso_date("1 November 2026") == "2026-11-01")
    check("no served page carries a comment, but the join page's, which says why it must never read the address",
          all("<!--" not in t for p, t in files.items() if p.name != "join.html"))
    test_site_join(files, site)
    test_site_manual()
    test_site_release()


def test_site_join(files, site):
    """The page an invite link opens (joinpage, 20 November 2026): idiograph.app/join#<words>. The words after the #
    are the invite's secret, so the page must exist, offer the Download page, and carry no script that could read
    the address or send it anywhere."""
    page = (site / "join.html").read_text(encoding="utf-8") if (site / "join.html").is_file() else ""
    check("the join page exists, is written like the other pages and links Download and the manual's Working "
          "together", page and (site / "join.html") in files and 'href="download.html"' in page
          and 'href="manual.html#working-together"' in page and 'class="site-nav"' in page)
    bare = re.sub(r"<!--.*?-->", "", page, flags=re.S)
    scripts = re.findall(r"<script\b([^>]*)>(.*?)</script>", bare, re.S)
    srcs = [re.search(r'src="([^"]*)"', a).group(1) for a, _ in scripts if "src=" in a]
    inline = " ".join(body for _, body in scripts)
    mod = site / "get.js"
    code = inline + (mod.read_text(encoding="utf-8") if "get.js" in srcs else "")
    check("the join page's scripts are the site's own, none from another site", srcs == ["get.js"], srcs)
    check("no script on the join page reads the address: no location, hash, search, history, fetch or beacon",
          not re.search(r"location|\.hash|\.search|history\.|fetch\(|sendBeacon|XMLHttpRequest|document\.URL|"
                        r"documentURI|referrer", code), code[:200])
    check("the join page has no form, no iframe, no image or link to another site's script or tracker, and turns "
          "the referrer off", not re.search(r"<form|<iframe|<img|<link[^>]+href=\"https?:", bare)
          and 'name="referrer" content="no-referrer"' in page)


def test_site_manual():
    print("\n405b. The website's manual: the page is the generator's from docs/manual.md, and every heading's anchor is "
          "the app's own (sitemanual)")
    sw = load()
    site = support.TOOL / "site" / "holding"
    page = (site / sw.MANUAL).read_text(encoding="utf-8")
    check("the committed manual.html is what the generator writes from docs/manual.md",
          page == sw.outputs()[site / sw.MANUAL])
    import server as srv
    code, app_page = srv.manual_page()
    heads = lambda t: re.findall(r'<h([1-4]) id="([^"]+)"', t)
    check("every heading has the same level and the same anchor as the app's manual page, in the same order",
          code == 200 and heads(page) and heads(page) == heads(app_page), (len(heads(page)), len(heads(app_page))))
    ids = re.findall(r'\sid="([^"]+)"', page)
    check("no id on the page is used twice, so no heading's anchor is taken by the header or the foot",
          len(ids) == len(set(ids)), [i for i in set(ids) if ids.count(i) > 1])
    links = re.findall(r'href="#([^"]+)"', page)
    check("every link to a heading, the contents' among them, lands on one", links and all(l in ids for l in links),
          [l for l in links if l not in ids])
    sections = re.findall(r"(?m)^## (.*)", (support.TOOL / "docs" / "manual.md").read_text(encoding="utf-8"))
    contents = re.search(r'<nav class="mn-contents".*?</nav>', page, re.S).group(0)
    check("the contents list every ## section", len(re.findall(r"<li>", contents)) == len(sections), len(sections))
    check("a link to a file of the repo goes to it on GitHub, and no link is left pointing at a page the site lacks",
          'href="https://github.com/Pharkie/idiograph/blob/main/docs/internals.md"' in page
          and 'href="https://github.com/Pharkie/idiograph/blob/main/README.md"' in page
          and not re.search(r'href="(?!https?:|#|[a-z-]+\.html|favicon|style\.css)[^"]*"', page))
    check("the manual is no item in the nav, and the Download and Features pages link to it",
          'href="manual.html"' not in re.search(r'<nav class="site-nav".*?</nav>', page, re.S).group(0)
          and all('href="manual.html"' in (site / n).read_text(encoding="utf-8")
                  for n in ("download.html", "features.html")))
    check("the page carries no comment and asks nothing of another site",
          "<!--" not in page and not re.search(r'(?:src|href)="https?://(?!github\.com/Pharkie/)', page))


def test_site_release():
    print("\n405c. The release's site step: site_release.py check passes a current site and fails a stale manual "
          "(sitecheck)")
    import shutil
    import tempfile
    from pathlib import Path
    spec = importlib.util.spec_from_file_location("site_release", support.TOOL / "packaging" / "site_release.py")
    sr = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(sr)
    version = json.loads((support.TOOL / "versions.json").read_text(encoding="utf-8"))["idiograph"]
    tag = "v" + version
    with tempfile.TemporaryDirectory() as tmp:
        scratch = Path(tmp) / "holding"
        shutil.copytree(support.TOOL / "site" / "holding", scratch)
        check("a current site is ready for its release", sr.site_problems(tag, scratch) == [],
              sr.site_problems(tag, scratch))
        manual = scratch / "manual.html"
        manual.write_text(manual.read_text(encoding="utf-8").replace("</main>", "<p>stale</p></main>"), encoding="utf-8")
        stale = sr.site_problems(tag, scratch)
        check("a stale manual page is a problem that names it and the script to run",
              len(stale) == 1 and "manual.html" in stale[0] and "site_whats_new.py" in stale[0], stale)
    wrong = sr.site_problems("v99.0.0")
    check("a tag that is not the version in versions.json is a problem", wrong and "versions.json" in wrong[0], wrong)

    clips, shared = sr.clip_map()
    scripts = sorted(f.stem for f in sr.CLIPS.glob("*.mjs") if f.name != "app.mjs")
    check("every clip script has a map of the files it shows", sorted(clips) == scripts and all(clips.values()),
          {k: v for k, v in clips.items() if not v})
    missing = [p for paths in clips.values() for p in paths
               if not (support.TOOL / p).exists()] + [p for p in shared if not (support.TOOL / p).exists()]
    check("the shared screens are named", shared)
    check("a prefixed tag is read like release.py reads it", sr.version_of("idiograph-v0.9.31") == "0.9.31")
    check("every file or folder a clip's map names exists", not missing, missing)


def raises(fn) -> bool:
    try:
        fn()
    except ValueError:
        return True
    return False
