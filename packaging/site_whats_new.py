"""The website's What's new (sitenews, 16 November 2026, Adam: "when we do a release update the website with the
release to show that").

Reads docs/whats-new.md, the notes the app's own What's new shows, and versions.json, and writes two things into
site/holding/, the site on idiograph.app:

- `whats-new.html`, the newest released version's notes and the two before it, each with its version and date
  (SHOWN), the sections up to and including the version versions.json names, so a next version's section, written
  before its release, stays off the site until the bump, and under them a link to every release on GitHub;
- `manual.html`, the manual (docs/manual.md) as a page of the site (sitemanual, 18 November 2026), its markdown read
  by the app's own renderer (family/server.py, `manual_blocks`), so every heading's anchor is the app's own, and a
  link to a file in the repo going to that file on GitHub;
- in every page with the site's nav, the small script after the nav that holds the date of each release the page shows (the newest SHOWN) and shows the
  count of those in the visitor's last seven days on What's new, worked out in their browser as the page loads
  (the site is static). Without scripts the link works and shows no count.

Same input, same bytes: nothing here reads the clock. Run it whenever docs/whats-new.md or versions.json changes,
which the version bump does:

    .venv/bin/python packaging/site_whats_new.py

`--check` writes nothing and exits 1 naming each file that differs from what it would write (area 405 holds the
committed site to it). The updates sign-up form goes on Download and What's new only while UPDATES_FORM is True (off until Amazon
SES grants production access), and `--out <folder> --updates-form` writes a copy with it for review. `--layout A` or `B` and `--out <folder>` write a copy of the site's pages elsewhere, for
review shots of the layout not shipped.
"""
from __future__ import annotations

import argparse
import html
import json
import posixpath
import re
import shutil
import sys
from pathlib import Path

TOOL = Path(__file__).resolve().parent.parent
WHATS_NEW = TOOL / "docs" / "whats-new.md"
VERSIONS = TOOL / "versions.json"
SITE = TOOL / "site" / "holding"
PAGE = "whats-new.html"
MANUAL = "manual.html"
MANUAL_SOURCE = TOOL / "docs" / "manual.md"
REPO_FILES = "https://github.com/Pharkie/idiograph/blob/main/"

# The layout the site ships: "A" one long page with every release open, "B" the newest open and the older ones
# listed by version and date, each opening on a click (native details, so it works without scripts)
LAYOUT = "B"
# How many versions the page shows, the newest and the ones just before it (Adam, 17 November 2026: the past three,
# GitHub holds the full history); the nav's count still reads every release's date
SHOWN = 3
HISTORY = "https://github.com/Pharkie/idiograph/releases"

HEAD = re.compile(r"^## (\d+\.\d+\.\d+), (.+?)\s*$")
MONTHS = ("January", "February", "March", "April", "May", "June", "July", "August", "September", "October",
          "November", "December")
NAV_BLOCK = re.compile(r'(?:<button class="nav-burger".*?</button>\s*)?<nav class="site-nav".*?</nav>\s*'
                       r'<script id="nav-new-js">.*?</script>', re.S)
CURRENT = re.compile(r'<a (?:class="nav-dl" )?href="([a-z-]+\.html)" aria-current="page">')
VERSION_LINE = re.compile(r'<p class="get-version">Version [0-9.]+</p>')


def as_tuple(version: str) -> tuple[int, ...]:
    return tuple(int(x) for x in version.split("."))


def iso_date(date: str) -> str:
    """`16 November 2026` as `2026-11-16`; anything else refused, so a heading's typo cannot pass."""
    m = re.fullmatch(r"(\d{1,2}) ([A-Z][a-z]+) (\d{4})", date.strip())
    if not m or m.group(2) not in MONTHS:
        raise ValueError(f"docs/whats-new.md: a version's date is not like 16 November 2026: {date!r}")
    return f"{m.group(3)}-{MONTHS.index(m.group(2)) + 1:02d}-{int(m.group(1)):02d}"


def releases(text: str, version: str) -> list[dict]:
    """Each released version's number, date (as written and as ISO) and lines, in the file's order, newest first,
    read as the app reads them (family/server.py, whats_new_versions); a version above `version` is not released."""
    out: list[dict] = []
    for line in text.splitlines():
        head = HEAD.match(line)
        if head:
            out.append({"version": head.group(1), "date": head.group(2), "iso": iso_date(head.group(2)), "lines": []})
        elif out and line.strip() and not line.startswith("#"):
            out[-1]["lines"].append(line.strip())
    top = as_tuple(version)
    return [r for r in out if as_tuple(r["version"]) <= top]


def nav_script(rels: list[dict]) -> str:
    """The script after every page's nav. It marks the page as scripted (`navjs`), so under 560 pixels the nav folds
    into the Menu button, which opens and closes it, Escape and a click outside closing it; and it shows the count of
    releases dated in the visitor's last seven days, today one of them, on What's new (its words in the link's name
    for a screen reader) and on the Menu button. Without scripts the nav stays a row of links that wraps."""
    dates = json.dumps([r["iso"] for r in rels[:SHOWN]], separators=(",", ":"))
    return ('<script id="nav-new-js">(function(){var h=document.documentElement,d=' + dates + ','
            't=new Date(),n=0,i,p,x,g=function(k){return document.getElementById(k);},'
            'now=Date.UTC(t.getFullYear(),t.getMonth(),t.getDate()),b=g("nav-burger"),v=g("site-nav");'
            'h.classList.add("navjs");'
            'for(i=0;i<d.length;i++){p=d[i].split("-");x=(now-Date.UTC(+p[0],p[1]-1,+p[2]))/864e5;'
            'if(x>=0&&x<7)n++;}'
            'if(n){g("nav-new-n").textContent=n;g("nav-new-w").textContent=n===1?" new release":" new releases";'
            'g("nav-new").hidden=false;g("nav-new-b").textContent=n;g("nav-new-b").hidden=false;}'
            'if(!b||!v)return;var head=b.parentNode,'
            'set=function(o){head.classList.toggle("nav-open",o);b.setAttribute("aria-expanded",o?"true":"false");},'
            'open=function(){return b.getAttribute("aria-expanded")==="true";};'
            'b.addEventListener("click",function(){set(!open());});'
            'document.addEventListener("keydown",function(e){if(e.key==="Escape"&&open()){set(false);b.focus();}});'
            'document.addEventListener("click",function(e){if(open()&&!head.contains(e.target))set(false);});'
            'v.addEventListener("click",function(e){if(e.target.closest("a"))set(false);});'
            '})();</script>')


BURGER = ('<button class="nav-burger" id="nav-burger" type="button" aria-label="Menu" aria-expanded="false" '
          'aria-controls="site-nav"><svg viewBox="0 0 24 24" aria-hidden="true" focusable="false"><path '
          'd="M4 7h16M4 12h16M4 17h16" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>'
          '</svg><span class="nav-new" id="nav-new-b" aria-hidden="true" hidden></span></button>')


def nav(current: str = "") -> str:
    """The site's Menu button and nav, as every page has them, the page you are on marked."""
    links = [("about.html", "About"), ("features.html", "Features"), ("screenshots.html", "Screenshots")]
    here = ' aria-current="page"'
    parts = [f'<a href="{href}"{here if href == current else ""}>{name}</a>' for href, name in links]
    parts.append(f'<a href="{PAGE}"{here if current == PAGE else ""}>What&#x27;s new'
                 '<span class="nav-new" id="nav-new" hidden><span class="vh">, </span><span id="nav-new-n"></span>'
                 '<span class="vh" id="nav-new-w"></span></span></a>')
    if current == "download.html":
        parts.append(f'<a href="download.html"{here}>Download</a>')
    else:
        parts.append('<a class="nav-dl" href="download.html">Download</a>')
    return BURGER + '\n  <nav class="site-nav" id="site-nav" aria-label="Site">' + "".join(parts) + "</nav>"


CHEV = ('<svg class="chev" viewBox="0 0 16 16" aria-hidden="true" focusable="false"><path d="M3.5 6l4.5 4.5L12.5 6" '
        'fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"/></svg>')


def anchor(version: str) -> str:
    return "v" + version.replace(".", "-")


def notes(r: dict) -> str:
    return ('<ul class="wn-notes">' + "".join(f"<li>{html.escape(line)}</li>" for line in r["lines"]) + "</ul>")


def open_version(r: dict) -> str:
    a = anchor(r["version"])
    return (f'  <section class="wn-v" id="{a}" aria-labelledby="{a}-h">\n'
            f'    <h2 id="{a}-h">Idiograph {r["version"]}</h2>\n'
            f'    <p class="wn-date"><time datetime="{r["iso"]}">{html.escape(r["date"])}</time></p>\n'
            f'    {notes(r)}\n'
            '  </section>\n')


def closed_version(r: dict) -> str:
    a = anchor(r["version"])
    return (f'    <details class="wn-row" id="{a}"><summary><span class="wn-name">Idiograph {r["version"]}</span>'
            f'<time class="wn-when" datetime="{r["iso"]}">{html.escape(r["date"])}</time>{CHEV}</summary>'
            f'{notes(r)}</details>\n')


def body(rels: list[dict], layout: str) -> str:
    rels = rels[:SHOWN]
    if layout == "A" or len(rels) < 2:
        return "".join(open_version(r) for r in rels)
    return (open_version(rels[0])
            + '  <section class="wn-earlier" aria-labelledby="wn-earlier-h">\n'
            + '    <h2 id="wn-earlier-h">Earlier versions</h2>\n'
            + "".join(closed_version(r) for r in rels[1:])
            + "  </section>\n")


SYMBOL = ('<svg class="symbols" aria-hidden="true" focusable="false"><symbol id="idiograph" viewBox="0 0 24 24" '
          'fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="square" stroke-linejoin="miter">\n'
          '  <path d="M8.5 3.5H4.5V20.5H8.5M15.5 3.5H19.5V20.5H15.5"/>\n'
          '  <circle cx="12" cy="12" r="2.7" stroke="none" style="fill: var(--mark-dot, currentColor)"/>\n'
          '</symbol></svg>\n')

LOCKUP = ('<a class="site-home" href="index.html" aria-label="Idiograph, home"><span class="pe"><svg class="lockup" '
          'viewBox="0 0 107.33 15" role="img" aria-label="Idiograph" fill="none"><use href="#idiograph" width="15" '
          'height="15"/><path transform="translate(19.2 12.5)" stroke="currentColor" stroke-width="1.3" '
          'stroke-linecap="square" stroke-linejoin="miter" d="M0.65 -9.35V-0.65M5.35 -0.65V-9.35H8.3A4.35 4.35 0 0 1 '
          '8.3 -0.65ZM16.95 -9.35V-0.65M21.65 -5a4.35 4.35 0 1 0 8.7 0a4.35 4.35 0 1 0 -8.7 0M41.93 -7.91A4.35 4.35 0 '
          '1 0 43.05 -5H39.5M47.35 -0.65V-9.35H50.9A2.17 2.17 0 0 1 50.9 -5H47.35M50.7 -5L54.3 -0.65M58.15 -0.65L62.1 '
          '-9.35L66.05 -0.65M59.8 -3.4H64.4M70.15 -0.65V-9.35H73.5A2.38 2.38 0 0 1 73.5 -4.6H70.15M80.18 -9.35V-0.65M87.47 '
          '-9.35V-0.65M80.18 -5H87.47"/></svg><span class="pe-stamp">Preview Edition</span></span></a>')


def page(rels: list[dict], layout: str = LAYOUT) -> str:
    """whats-new.html in the site's own look: the header, the nav and the download at the foot as every page has it."""
    return ('<!DOCTYPE html>\n<html lang="en-GB">\n<head>\n<meta charset="utf-8">\n'
            '<meta name="viewport" content="width=device-width, initial-scale=1">\n'
            "<title>What&#x27;s new in Idiograph</title>\n"
            '<meta name="description" content="What is new in each version of Idiograph, software for Interpretative '
            'Phenomenological Analysis.">\n'
            '<meta name="robots" content="noindex">\n<meta name="color-scheme" content="light dark">\n'
            '<meta name="theme-color" content="#FBF7EF" media="(prefers-color-scheme: light)">\n'
            '<meta name="theme-color" content="#16130E" media="(prefers-color-scheme: dark)">\n'
            '<link rel="icon" href="favicon.svg" type="image/svg+xml">\n'
            '<link rel="icon" href="favicon.png" type="image/png" sizes="32x32">\n'
            '<link rel="stylesheet" href="style.css">\n</head>\n<body>\n'
            + SYMBOL
            + '<header class="site-head">\n  ' + LOCKUP + "\n  " + nav(PAGE) + "\n  " + nav_script(rels) + "\n</header>\n"
            + f'<main class="wn wn-{layout.lower()}">\n  <h1>What&#x27;s new</h1>\n'
            + body(rels, layout)
            + f'  <p class="wn-all"><a href="{HISTORY}">All releases on GitHub</a></p>\n'
            + '  <div class="fp-foot">\n  <div class="get" id="get">\n'
            '    <p class="get-line" id="get-line">Idiograph is for Mac, Windows and Linux computers.</p>\n'
            '  </div>\n  </div>\n</main>\n<script src="get.js"></script>\n</body>\n</html>\n')


# Updates by email (updates-site, 23 November 2026, Adam): the sign-up form under the Download page's download and
# under What's new's notes. It goes live only after Amazon SES grants production access, so it is off here and the
# pages come out without it. `--updates-form` writes it into a copy (`--out`) for review shots. Turn it on by setting
# UPDATES_FORM to True and running this, which writes both pages with the form and `updates.js` after `get.js`.
UPDATES_FORM = True
# The wording the person agrees to is the form's purpose line. Its version travels with every sign-up (the contract
# with updates-worker and the app's Settings), so a change to the line takes a new version here and in the app.
UPDATES_CONSENT = "updates-2026-11-23"
UPDATES_PAGES = ("download.html", PAGE)
UPDATES_SCRIPT = '<script src="updates.js"></script>\n'
UPDATES_BLOCK = re.compile(r'  <section class="up" id="up".*?</section>\n', re.S)


def updates_form() -> str:
    """The form, hidden until updates.js shows it, so a visitor without scripts never meets a form that cannot send.
    `website` is the honeypot: off the screen, out of the tab order and hidden from a screen reader."""
    return ('  <section class="up" id="up" aria-labelledby="up-h" hidden>\n'
            '    <h2 id="up-h">Updates by email</h2>\n'
            '    <p class="up-line">Get an email when there is a new version or news of Idiograph. '
            'I send a few emails a year.</p>\n'
            f'    <form class="up-form" id="up-form" data-consent="{UPDATES_CONSENT}" novalidate>\n'
            '      <label class="up-label" for="up-email">Email address</label>\n'
            '      <div class="up-row"><input id="up-email" name="email" type="email" autocomplete="email" '
            'maxlength="254" spellcheck="false" aria-describedby="up-said"><button class="up-send" id="up-send" '
            'type="submit">Sign up</button></div>\n'
            '      <div class="up-hp" aria-hidden="true"><label for="up-website">Website</label><input id="up-website" '
            'name="website" type="text" tabindex="-1" autocomplete="off"></div>\n'
            '      <p class="up-said" id="up-said" role="status" tabindex="-1"></p>\n'
            '    </form>\n'
            '    <p class="up-small">Every email has a link to leave the list. The <a href="privacy.html">privacy page</a> '
            'says what is kept.</p>\n'
            '  </section>\n')


def with_updates(text: str, name: str, on: bool) -> str:
    """A page with the form and its script, or without either: whatever was there before is taken out first, so
    turning the flag off again gives the page as it was. On Download it goes after the download block, below the
    first-open steps and the manual's link. On What's new it goes after the link to every release."""
    text = UPDATES_BLOCK.sub("", text).replace(UPDATES_SCRIPT, "")
    if not on or name not in UPDATES_PAGES:
        return text
    if name == PAGE:
        at = text.index('  <div class="fp-foot">')
    else:
        at = text.index("</main>")
    text = text[:at] + updates_form() + text[at:]
    at = text.index('<script src="get.js"></script>\n') + len('<script src="get.js"></script>\n')
    return text[:at] + UPDATES_SCRIPT + text[at:]


def manual_link(target: str) -> str | None:
    """Where a link in docs/manual.md goes on the site: a link to a heading stays where it is, and a link to a file
    in the repo, written from docs/, goes to that file on GitHub. Anything else keeps its words alone."""
    if target.startswith("#"):
        return target
    if re.fullmatch(r"[A-Za-z0-9_./-]+", target):
        return REPO_FILES + posixpath.normpath(posixpath.join("docs", target))
    return None


def manual_render(text: str) -> tuple[list, list]:
    """The manual's blocks and the contents' links, from the app's own renderer, one implementation for both."""
    sys.path.insert(0, str(TOOL))
    import boot
    boot.setup()
    import server
    return server.manual_blocks(text, local=manual_link)


def manual_page(rels: list[dict], text: str | None = None) -> str:
    """manual.html in the site's own look: the header and nav (the manual is no nav item), the manual's title, a list of
    its sections, its body and the download at the foot as every page has it."""
    if text is None:
        text = MANUAL_SOURCE.read_text(encoding="utf-8")
    blocks, contents = manual_render(text)
    blocks = [b.replace("<pre>", '<pre tabindex="0">') for b in blocks]
    toc = ('  <nav class="mn-contents" aria-label="Contents"><ul>'
           + "".join(f"<li>{c}</li>" for c in contents) + "</ul></nav>\n")
    return ('<!DOCTYPE html>\n<html lang="en-GB">\n<head>\n<meta charset="utf-8">\n'
            '<meta name="viewport" content="width=device-width, initial-scale=1">\n'
            "<title>Idiograph manual</title>\n"
            '<meta name="description" content="The Idiograph manual: what to do when something goes wrong, what a term '
            'means and where your data goes.">\n'
            '<meta name="robots" content="noindex">\n<meta name="color-scheme" content="light dark">\n'
            '<meta name="theme-color" content="#FBF7EF" media="(prefers-color-scheme: light)">\n'
            '<meta name="theme-color" content="#16130E" media="(prefers-color-scheme: dark)">\n'
            '<link rel="icon" href="favicon.svg" type="image/svg+xml">\n'
            '<link rel="icon" href="favicon.png" type="image/png" sizes="32x32">\n'
            '<link rel="stylesheet" href="style.css">\n</head>\n<body>\n'
            + SYMBOL
            + '<header class="site-head">\n  ' + LOCKUP + "\n  " + nav() + "\n  " + nav_script(rels) + "\n</header>\n"
            + '<main class="mn">\n  ' + "\n  ".join(blocks[:1]) + "\n" + toc
            + "  " + "\n  ".join(blocks[1:]) + "\n"
            + '  <div class="fp-foot">\n  <div class="get" id="get-foot">\n'
            '    <p class="get-line" id="get-line">Idiograph is for Mac, Windows and Linux computers.</p>\n'
            '  </div>\n  </div>\n</main>\n<script src="get.js"></script>\n</body>\n</html>\n')


def outputs(site: Path = SITE, text: str | None = None, version: str | None = None,
            layout: str = LAYOUT, updates: bool | None = None) -> dict[Path, str]:
    """Every file this writes and what it holds: the page, and each other page with the nav script put in fresh.
    A page with the site's nav and no nav script is refused, so no page goes without the count. `updates` puts the
    sign-up form on Download and What's new, UPDATES_FORM when not given."""
    if text is None:
        text = WHATS_NEW.read_text(encoding="utf-8")
    if version is None:
        version = json.loads(VERSIONS.read_text(encoding="utf-8"))["idiograph"]
    rels = releases(text, version)
    if not rels:
        raise ValueError(f"docs/whats-new.md has no section for {version} or any version before it")
    if updates is None:
        updates = UPDATES_FORM
    script = nav_script(rels)
    out = {site / PAGE: with_updates(page(rels, layout), PAGE, updates), site / MANUAL: manual_page(rels)}
    for path in sorted(site.glob("*.html")):
        if path.name in (PAGE, MANUAL):
            continue
        old = path.read_text(encoding="utf-8")
        if 'class="site-nav"' not in old:
            continue
        block = NAV_BLOCK.search(old)
        if not block:
            raise ValueError(f"{path.name} has the site's nav and no nav-new-js script after it")
        here = CURRENT.search(block.group(0))
        fresh = nav(here.group(1) if here else "") + "\n  " + script
        new = old[:block.start()] + fresh + old[block.end():]
        if path.name == "download.html":
            if not VERSION_LINE.search(new):
                raise ValueError("download.html has no get-version line")
            new = VERSION_LINE.sub(f'<p class="get-version">Version {rels[0]["version"]}</p>', new)
        out[path] = with_updates(new, path.name, updates)
    return out


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Write the website's What's new and manual from docs/")
    ap.add_argument("--check", action="store_true", help="write nothing; exit 1 naming each file that differs")
    ap.add_argument("--layout", choices=("A", "B"), default=LAYOUT, help="A every release open, B the newest open")
    ap.add_argument("--out", help="write a copy of the site's pages here, never the site itself")
    ap.add_argument("--updates-form", action="store_true",
                    help="with --out, put the updates sign-up form in the copy (the site itself follows UPDATES_FORM)")
    args = ap.parse_args(argv)
    if args.updates_form and not args.out:
        raise SystemExit("--updates-form is for a copy (--out); set UPDATES_FORM to put the form on the site")
    if args.out:
        dest = Path(args.out)
        if dest.resolve() == SITE.resolve():
            raise SystemExit("--out is for a copy, never site/holding itself")
        shutil.copytree(SITE, dest, dirs_exist_ok=True)
        for path, content in outputs(dest, layout=args.layout, updates=args.updates_form or None).items():
            path.write_text(content, encoding="utf-8", newline="\n")
        print(f"WHATS-NEW: copy in {dest}, layout {args.layout}" + (", the updates form on" if args.updates_form else ""))
        return 0
    files = outputs(layout=args.layout)
    stale = [p for p, content in files.items()
             if not p.is_file() or p.read_text(encoding="utf-8") != content]
    if args.check:
        for p in stale:
            print(f"differs: site/holding/{p.name}")
        print("WHATS-NEW: " + ("current" if not stale else f"{len(stale)} file(s) to write"))
        return 1 if stale else 0
    for p in stale:
        p.write_text(files[p], encoding="utf-8", newline="\n")
    print(f"WHATS-NEW: {len(stale)} file(s) written" if stale else "WHATS-NEW: current, nothing written")
    return 0


if __name__ == "__main__":
    sys.exit(main())
