from __future__ import annotations

import re
import shutil
from pathlib import Path

from . import support
from .support import COLOUR_FUNCTION, HEX_COLOUR, blanked, check, css_rules, tokens_of


# The colours that may stand outside a token, each with its reason (15 October). A line is the file, where
# in it, a CSS rule's selector or a script's top-level function or constant, and the colour as written,
# `*` for any colour there.
COLOUR_ALLOWED = (
    ("style.css", ".transcript", "#000", "an alpha mask, black meaning shown, never a colour on screen"),
    ("sift.js", "SF_MAP_PAPER", "*", "a saved map is always light, whatever the theme, and --sf-map-* mirror it"),
    ("themes.js", "thCanvasPage", "*", "the canvas's print page is always light, a white sheet on paper"),
)
NAMED_COLOURS = frozenset((
    "aliceblue antiquewhite aqua aquamarine azure beige bisque black blanchedalmond blue blueviolet brown "
    "burlywood cadetblue chartreuse chocolate coral cornflowerblue cornsilk crimson cyan darkblue darkcyan "
    "darkgoldenrod darkgray darkgreen darkgrey darkkhaki darkmagenta darkolivegreen darkorange darkorchid "
    "darkred darksalmon darkseagreen darkslateblue darkslategray darkslategrey darkturquoise darkviolet "
    "deeppink deepskyblue dimgray dimgrey dodgerblue firebrick floralwhite forestgreen fuchsia gainsboro "
    "ghostwhite gold goldenrod gray green greenyellow grey honeydew hotpink indianred indigo ivory khaki "
    "lavender lavenderblush lawngreen lemonchiffon lightblue lightcoral lightcyan lightgoldenrodyellow "
    "lightgray lightgreen lightgrey lightpink lightsalmon lightseagreen lightskyblue lightslategray "
    "lightslategrey lightsteelblue lightyellow lime limegreen linen magenta maroon mediumaquamarine "
    "mediumblue mediumorchid mediumpurple mediumseagreen mediumslateblue mediumspringgreen mediumturquoise "
    "mediumvioletred midnightblue mintcream mistyrose moccasin navajowhite navy oldlace olive olivedrab "
    "orange orangered orchid palegoldenrod palegreen paleturquoise palevioletred papayawhip peachpuff peru "
    "pink plum powderblue purple rebeccapurple red rosybrown royalblue saddlebrown salmon sandybrown "
    "seagreen seashell sienna silver skyblue slateblue slategray slategrey snow springgreen steelblue tan "
    "teal thistle tomato turquoise violet wheat white whitesmoke yellow yellowgreen").split())
COLOUR_PROPS = re.compile(r"^(?:color|background(?:-color|-image)?|border(?:-[a-z]+)*|outline(?:-color)?|box-shadow|"
                          r"text-shadow|fill|stroke|caret-color|accent-color|text-decoration(?:-color)?|column-rule(?:-color)?|"
                          r"filter|scrollbar-color|-webkit-text-fill-color|-webkit-text-stroke(?:-color)?|stop-color|flood-color)$")
TOKEN_SELECTOR = re.compile(r'^(?::root|(?:html)?\[data-theme(?:="[a-z]+")?\])$')


def is_token_block(selector: str) -> bool:
    """A rule of tokens alone: the root, an element's theme, or both."""
    return all(TOKEN_SELECTOR.match(s.strip()) for s in selector.split(","))


def colours_in(value: str, named: bool) -> list:
    value = re.sub(r"\"[^\"]*\"|'[^']*'", " ", value)
    found = HEX_COLOUR.findall(value) + [m.group(0).split("(")[0] + "(" for m in COLOUR_FUNCTION.finditer(value)]
    if named:
        found += [w for w in re.findall(r"(?<![\w-])([a-z]+)(?![\w-])", value.lower()) if w in NAMED_COLOURS]
    return found


def colour_allowed(name: str, where: str, what: str, allowed=COLOUR_ALLOWED) -> bool:
    return any(f == name and (w == where or where.startswith(w + " ")) and (c == "*" or c.lower() == what.lower())
               for f, w, c, _ in allowed)


def colour_problems(static, allowed=COLOUR_ALLOWED) -> dict:
    """What area 147 holds the app's look to, read from the files in `static`, the vendor folder set
    aside: `colours`, each colour written outside a token as `file:line colour in where`, `undefined`, each
    var(--name) that no stylesheet, script or page defines, `dark`, each stylesheet whose two dark blocks
    differ or stand one without the other, `font_sizes` and `radii`, the distinct values across the
    stylesheets with a token counted by its value, and `defined`, every custom property defined."""
    # one folder, or since the family codebase each folder the page is merged from, the root's, the family's and
    # each app's static/ (22 October 2026)
    folders = [Path(f) for f in static] if isinstance(static, (list, tuple)) else [Path(static)]
    files = lambda pattern: sorted((p for f in folders for p in f.glob(pattern)), key=lambda p: p.name)
    sheets = {p.name: p.read_text(encoding="utf-8") for p in files("*.css")}
    scripts = {p.name: p.read_text(encoding="utf-8") for p in files("*.js")}
    pages = {p.name: p.read_text(encoding="utf-8") for p in files("*.html")}
    same = tokens_of(sheets.get("tokens.css", ""))["same"]
    worth = lambda v: re.sub(r"var\((--[\w-]+)\)", lambda m: same.get(m.group(1), m.group(0)), v)
    colours, defined, used, dark, sizes, radii = [], set(), {}, [], set(), set()
    for name, text in sheets.items():
        blocks = {}
        for selector, decls, at in css_rules(text):
            token = is_token_block(selector)
            if token and selector == '[data-theme="dark"]' and not at:
                blocks["dark"] = {p: v for p, v, _ in decls}
            if token and selector == '[data-theme="auto"], [data-theme="system"]' and "prefers-color-scheme: dark" in at:
                blocks["system"] = {p: v for p, v, _ in decls}
            for prop, value, line in decls:
                for v in re.findall(r"var\(\s*(--[\w-]+)", value):
                    used.setdefault(v, f"{name}:{line}")
                if prop.startswith("--"):
                    defined.add(prop)
                if prop == "font-size":
                    sizes.add(worth(value))
                if prop == "border-radius":
                    radii.add(worth(value))
                if prop.startswith("--") and token:
                    continue
                for c in colours_in(value, bool(COLOUR_PROPS.match(prop)) or prop.startswith("--")):
                    if not colour_allowed(name, selector, c, allowed):
                        colours.append(f"{name}:{line} {c} in {selector}")
        if len(blocks) == 1:
            dark.append(f"{name}: one dark block alone")
        elif blocks and blocks["dark"] != blocks["system"]:
            dark.append(f"{name}: " + ", ".join(sorted(k for k in set(blocks["dark"]) | set(blocks["system"])
                                                       if blocks["dark"].get(k) != blocks["system"].get(k))))
    top = re.compile(r"(?m)^(?:async function|function|const|let|var|class)\s+([\w$]+)")
    styled = re.compile(r"(?:color|background|border[\w-]*|fill|stroke|outline|shadow)\s*[:=]\s*['\"`]?\s*([a-z]+)\b", re.I)
    for name, text in scripts.items():
        clean = blanked(blanked(text, r"/\*.*?\*/"), r"(?m)(?<![:'\"`\\])//[^\n]*")
        heads = [(m.start(), m.group(1)) for m in top.finditer(clean)]
        # a script defines a property it names in a string, as setProperty('--band', ...) does
        for m in re.finditer(r"""['"`](--[a-z][\w-]*)['"`]|(?<![\w-])(--[a-z][\w-]*)\s*:""", clean):
            defined.add(m.group(1) or m.group(2))
        for m in re.finditer(r"var\(\s*(--[\w-]+)", clean):
            used.setdefault(m.group(1), f"{name}:{clean.count(chr(10), 0, m.start()) + 1}")
        found = [(m.start(), m.group(0)) for m in HEX_COLOUR.finditer(clean) if clean[max(0, m.start() - 1)] in "'\"` (:,"]
        found += [(m.start(), m.group(0).split("(")[0] + "(") for m in COLOUR_FUNCTION.finditer(clean)]
        found += [(m.start(1), m.group(1)) for m in styled.finditer(clean) if m.group(1).lower() in NAMED_COLOURS]
        for at, what in found:
            where = next((h for s, h in reversed(heads) if s <= at), "")
            if not colour_allowed(name, where, what, allowed):
                colours.append(f"{name}:{clean.count(chr(10), 0, at) + 1} {what} in {where}")
    for name, text in pages.items():
        clean = blanked(text, r"<!--.*?-->")
        for m in re.finditer(r"var\(\s*(--[\w-]+)", clean):
            used.setdefault(m.group(1), f"{name}:{clean.count(chr(10), 0, m.start()) + 1}")
        for m in re.finditer(r"""\bstyle\s*=\s*"([^"]*)"|<style[^>]*>(.*?)</style>|\b(?:fill|stroke|color|bgcolor)\s*=\s*"([^"]*)\"""",
                             clean, re.S):
            body = m.group(1) or m.group(2) or m.group(3) or ""
            defined.update(re.findall(r"(--[\w-]+)\s*:", body))
            for c in colours_in(body, True):
                colours.append(f"{name}:{clean.count(chr(10), 0, m.start()) + 1} {c}")
    undefined = sorted(f"{v} at {at}" for v, at in used.items() if v not in defined)
    return {"colours": colours, "undefined": undefined, "dark": dark, "font_sizes": len(sizes), "radii": len(radii),
            "defined": defined}


def test_colour_problems(scratch):
    print("\n147. The design system's foundation, 15 October: every value that means something a token in "
          "tokens.css, linked first, on [data-theme] so a panel can carry its own, the colours written outside "
          "tokens moved in, the warning line in amber, the faint ink at 4.5 to 1, docs/design.md and /design. Since the "
          "test review of 18 October the colours, contrasts and counts are review shots, and the scan that keeps both "
          "themes whole and /design served stay")
    import http.server
    import threading
    import urllib.request
    import server as server_mod

    read = lambda path: Path(path).read_text(encoding="utf-8")
    tokens_css, themes_css = (support.text(p) for p in ("family/static/tokens.css", "apps/idiograph/static/themes.css"))
    sift_css = support.text("apps/sift/static/sift.css")
    design = support.page_text("family/static/design.html")

    # ── A. the scan
    found = colour_problems(support.static_folders())
    check("147: no colour is written outside a token in any stylesheet, the page's markup or a script's style "
          "string, but the three allowed with their reasons, the mask's black, the saved map's and the print page's",
          not found["colours"] and len(COLOUR_ALLOWED) == 3 and all(len(a) == 4 and a[3] for a in COLOUR_ALLOWED),
          "; ".join(found["colours"][:6]))
    check("147: every var(--name) in a stylesheet, a script or a page names a property something defines",
          not found["undefined"] and {"--paper", "--band", "--sf-side-w", "--th-dot"} <= found["defined"],
          ", ".join(found["undefined"][:6]))
    check("147: the two dark blocks agree in tokens.css, themes.css and sift.css, the theme's and the system's",
          not found["dark"] and all('[data-theme="dark"] {' in t and '[data-theme="auto"], [data-theme="system"] {' in t
                                    for t in (tokens_css, themes_css, sift_css)), "; ".join(found["dark"]))

    planted = scratch / "colours-147"
    shutil.rmtree(planted, ignore_errors=True)
    planted.mkdir(parents=True)
    (planted / "tokens.css").write_text(
        ':root, [data-theme="light"] { --paper: #FFFFFF; --ink: #111111; }\n'
        ':root { --fs-a: 12px; --r-a: 3px; }\n'
        '[data-theme="dark"] { --paper: #000000; --ink: #EEEEEE; }\n'
        '@media (prefers-color-scheme: dark) {\n  [data-theme="auto"], [data-theme="system"] { --paper: #010101; --ink: #EEEEEE; }\n}\n',
        encoding="utf-8")
    (planted / "a.css").write_text(
        ".one { color: #C25E0B; background: var(--paper); }\n"
        ".two { border: 1px solid rgba(0, 0, 0, .2); color: var(--paperr); }\n"
        ".three { box-shadow: 0 0 0 1px white; font-size: var(--fs-a); }\n"
        ".four { --local: #ABCDEF; font-size: 12px; border-radius: var(--r-a); }\n"
        ".kept { mask: url(\"data:image/svg+xml,%3Csvg stroke='black'%3E%3C/svg%3E\"); font-family: \"Snow Sans\"; }\n"
        ".ok { color: var(--ink); border-radius: 3px; }\n", encoding="utf-8")
    (planted / "b.js").write_text(
        "const TINTS = ['#F79646', '#C25E0B'];\nfunction ok() { return '#add-row'; }\n"
        "function painted(el) { el.style.color = 'red'; }\nconst KEPT = { paper: '#FFFFFF' };\n", encoding="utf-8")
    (planted / "c.html").write_text('<p style="color: #123456">x</p>\n<!-- <p style="color: red"> -->\n', encoding="utf-8")
    seen = colour_problems(planted, allowed=(("b.js", "KEPT", "*", "a test's own exception"),))
    check("147: the scan finds a colour planted in a rule, a shadow's named colour, a token-like property outside a "
          "token block, a script's tint and style, and a page's style, passes a data URI, a font's name, a "
          "comment and the allowed, and finds a misspelt var and two dark blocks that differ",
          sorted(c.split(" in ")[0] for c in seen["colours"]) == sorted([
              "a.css:1 #C25E0B", "a.css:2 rgba(", "a.css:3 white", "a.css:4 #ABCDEF", "b.js:1 #F79646", "b.js:1 #C25E0B",
              "b.js:3 red", "c.html:1 #123456"])
          and seen["undefined"] == ["--paperr at a.css:2"] and seen["dark"] == ["tokens.css: --paper"]
          and seen["font_sizes"] == 1 and seen["radii"] == 1, f"{seen['colours']} {seen['undefined']} {seen['dark']}")

    httpd = http.server.ThreadingHTTPServer(("127.0.0.1", 0), server_mod.Handler)
    threading.Thread(target=httpd.serve_forever, kwargs={"poll_interval": 0.05}, daemon=True).start()
    got = {}
    try:
        for path in ("/design", "/tokens.css"):
            with urllib.request.urlopen(f"http://127.0.0.1:{httpd.server_address[1]}{path}", timeout=10) as r:
                got[path] = (r.status, r.headers.get("Content-Type", ""), r.read().decode("utf-8"))
    finally:
        httpd.shutdown()
        httpd.server_close()
    check("147: over HTTP /design answers the reference page and /tokens.css the tokens",
          got.get("/design", (0, "", ""))[0] == 200 and got["/design"][1].startswith("text/html") and got["/design"][2] == design
          and got.get("/tokens.css", (0, "", ""))[2] == tokens_css, str({k: v[:2] for k, v in got.items()}))
