"""Area 223: one page showing Idiograph, Sift or Trace (the split's third build, 20 October 2026, Adam's plan
accepted with every lean). The server names its app on the page's root, and the page holds each app's
screens, Home and Settings marked for their app, so it shows its own alone. Settings' categories per app as
drawing 8 has them, AI features each app's last, a switch per AI feature that turns that feature's calls
off, Appearance kept in the app's own settings so Sift's first start copies it, and the family at each
Home's foot, Open or Download. Invented settings and folders only, in the scratch folder."""
from __future__ import annotations

import json
import re
from html.parser import HTMLParser
from pathlib import Path

from . import support
from .support import check
import idiograph_routes
import themes_ai

# each app's Settings categories, in their order, as drawing 8 and Adam's calls of 20 October have them
TABS = {"idiograph": ["General", "Language and formats", "Experiential statements", "PETs", "AI features (experimental)"],
        "sift": ["General", "Language and formats", "Databases", "Projects", "Zotero", "AI features (experimental)"],
        "trace": ["General", "Language and formats", "Projects", "AI features (experimental)"]}


class Marked(HTMLParser):
    """Every element with an id or data-only, with its data-only, its data-pane and the words in it, and
    what holds it, so what an app's page shows can be read from the markup as the page's rule reads it."""

    VOID = {"area", "base", "br", "col", "embed", "hr", "img", "input", "link", "meta", "source", "track", "wbr",
            "use", "path", "circle", "rect"}

    def __init__(self):
        super().__init__()
        self.stack, self.items = [], []

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        item = {"tag": tag, "id": a.get("id"), "only": a.get("data-only"), "pane": a.get("data-pane"),
                "words": [], "up": [s for s in self.stack if s.get("only")], "parent": self.stack[-1] if self.stack else None}
        self.items.append(item)
        if tag not in self.VOID:
            self.stack.append(item)

    def handle_endtag(self, tag):
        if tag in self.VOID:
            return
        while self.stack:
            if self.stack.pop()["tag"] == tag:
                break

    def handle_data(self, data):
        for s in self.stack:
            s["words"].append(data)


def shown(item: dict, app: str) -> bool:
    """Whether the page's rule leaves the element shown on `app`'s page: neither it nor what holds it is
    another app's."""
    return all(app in (x["only"] or app).split() for x in item["up"] + [item])


def test_pages(scratch):
    print("\n223. One page per app: its own screens, Home and Settings, AI features per feature, Appearance "
          "kept and copied, the family at the foot")
    import app_identity
    import server as server_mod
    import sift_routes

    page = support.every_page()
    app_js = support.text("family/static/shell.js", "apps/idiograph/static/distil.js")
    css = support.text("family/static/style.css", "apps/idiograph/static/distil.css")

    # ── A. the page as each app's
    own = {app: server_mod.own_page(page, app) for app in app_identity.APPS}
    check("223: the server names its app on the page's root and in its title, the page otherwise the same",
          all(f'data-app="{app}"' in own[app] and f"<title>{app_identity.APPS[app]['name']}</title>" in own[app]
              and own[app].count("data-app=") == page.count("data-app=") + 1 for app in own),
          str({a: own[a][:120] for a in own}))
    # since the cutover (the family codebase's sixth build, 23 October 2026) each app's page is assembled from its own
    # parts alone, and another app's files are not its page's, as they are not in its bundle
    loads = {"idiograph": ("/distil.js", "/themes.js", "/trajectories.js", "/distil.css", "/themes.css", 'id="home-analysis"'),
             "sift": ("/sift.js", "/sift_search.js", "/sift_settings.js", "/sift.css", "/sift_search.css", 'id="sift-home"'),
             "trace": ("/trace.js", "/trace.css", 'id="trace-home"')}
    served = {app: server_mod.assembled(support.text("family/static/page.html"), app) for app in app_identity.APPS}
    check("223: each app's page holds its own parts, scripts and styles alone, none of another app's, since the cutover",
          all(all(mark in served[app] for mark in loads[app])
              and not any(mark in served[app] for other in loads if other != app for mark in loads[other])
              for app in app_identity.APPS), str({a: [m for o in loads if o != a for m in loads[o] if m in served[a]] for a in served}))
    files = {app: [n.lstrip("/") for n in names if n.startswith("/")] for app, names in loads.items()}
    check("223: another app's static files are not this app's page's, each app's own and the family's found",
          all(server_mod.static_file(name, app) is not None and all(server_mod.static_file(name, other) is None
                                                                     for other in app_identity.APPS if other != app)
              for app in app_identity.APPS for name in files[app])
          and all(server_mod.static_file(name, app) is not None for app in app_identity.APPS
                  for name in ("shell.js", "style.css", "tokens.css", "table.js", "page.html")))
    check("223: the page's rule hides whatever is marked for another app, on each app's page",
          all(f'html[data-app="{a}"] [data-only]:not([data-only~="{a}"])' in css for a in app_identity.APPS))
    doc = Marked()
    doc.feed(page)
    named = {i["id"]: i for i in doc.items if i["id"]}
    onlys = {w for i in doc.items if i["only"] for w in i["only"].split()}
    check("223: every element marked for an app names one of the three", onlys == set(app_identity.APPS), str(onlys))
    homes = {"idiograph": "home-analysis", "sift": "sift-home", "trace": "trace-home"}
    check("223: each app's Home shows its own projects' section alone, and the family's foot on every app",
          all(shown(named[homes[a]], a) and not any(shown(named[homes[b]], a) for b in homes if b != a) for a in homes)
          and all(shown(named["family"], a) for a in homes),
          str({a: [h for h in homes.values() if shown(named[h], a)] for a in homes}))
    check("223: the days of rounds on the Home are Idiograph's alone",
          shown(named["days"], "idiograph") and not shown(named["days"], "sift"))

    # ── B. Settings per app, the page's tabs and the categories app.js walks
    tabs = [i for i in doc.items if i["pane"] and i["parent"] and i["parent"].get("id") == "settings-nav"]
    seen = {a: [re.sub(r"\s+", " ", "".join(t["words"])).strip().replace("Experiential statementsStatements",
                                                                            "Experiential statements")
                for t in tabs if shown(t, a)] for a in TABS}
    check("223: each app's Settings shows its own categories in order, General first and AI features last",
          seen == TABS, str(seen))
    panes_js = re.search(r"const PANES_BY_APP = \{(.*?)\};", app_js, re.S)
    walked = {a: re.findall(r"'([a-z]+)'", re.search(rf"{a}: \[(.*?)\]", panes_js.group(1)).group(1)) for a in TABS} \
        if panes_js else {}
    by_pane = {t["pane"]: t for t in tabs}
    check("223: the categories the arrow keys walk are the tabs each app shows, each with its pane",
          bool(walked) and all([by_pane[p]["pane"] for p in walked[a]] == [t["pane"] for t in tabs if shown(t, a)]
                               and all(f"pane-{p}" in named for p in walked[a]) for a in TABS), str(walked))
    check("223: the statements prompt stands under Experiential statements, no longer under General, and GETs is in "
          "Project settings, out of Settings (settingsplit)",
          any(i["id"] == "set-prompt" for i in doc.items) and _inside(doc, "set-prompt", "pane-statements")
          and not _inside(doc, "set-prompt", "pane-general") and _inside(doc, "gets-fields", "projset")
          and not _inside(doc, "gets-fields", "settings") and _inside(doc, "set-ai", "pane-ai")
          and _inside(doc, "set-key", "pane-ai"))
    feature_boxes = re.findall(r'<label data-only="([a-z]+)"><input type="checkbox" data-ai-feature="([a-z]+)">', page)
    check("223: AI features holds a switch for each of each app's AI features, marked for that app",
          {f: a for a, f in feature_boxes} == {f: a for a, fs in app_identity.AI_FEATURES.items() for f in fs},
          str(feature_boxes))

    # ── C. each switch turns its feature off: the calls refuse, the screens' state says off
    real = (server_mod.CONFIG_PATH, server_mod.APP, server_mod.STATE_MEMORY)
    folder = scratch / "pages-223"
    folder.mkdir(parents=True, exist_ok=True)
    conf = folder / "config.json"
    try:
        server_mod.STATE_MEMORY = {"recent": []}
        server_mod.CONFIG_PATH = conf
        on = {"corpus": "", "gravity_reference": "", "corpus_exclude": [], "projects": [], "ai_suggest": True}
        results = {}
        for feature in ("statements", "pets", "gets", "proposals", "passages"):
            conf.write_text(json.dumps(dict(on, ai_features_off=[feature])), encoding="utf-8")
            cfg = server_mod.config()
            results[feature] = {f: server_mod.ai_on(cfg, f) for f in ("statements", "pets", "gets", "proposals", "passages")}
        check("223: a feature turned off is off alone, the others still on while AI features is",
              all(results[f][f] is False and all(v for g, v in results[f].items() if g != f) for f in results), str(results))
        conf.write_text(json.dumps(dict(on, ai_features_off=["statements", "pets", "gets"])), encoding="utf-8")
        said = [idiograph_routes.api_suggest({"turn": "The tide went out.", "prior": "", "time": "", "name": "Wren"}),
                idiograph_routes.api_themes_ai({"workbook": "nowhere.xlsx", "op": "group"}),
                idiograph_routes.api_gets_ai({"op": "group"})]
        check("223: with its switch off, a suggestion, the PETs screen's help and the GETs screen's help are each "
              "refused before anything is read or asked",
              all(s.get("error") == themes_ai.OFF for s in said), str(said))
        cfg = server_mod.config()
        check("223: the boards draw their AI by their own feature, PETs' and GETs' apart",
              server_mod.ai_state(cfg, "pets")["on"] is False and server_mod.ai_state(dict(cfg, ai_features_off=["gets"]), "pets")["on"] is True
              and server_mod.ai_state(dict(cfg, ai_features_off=["pets"]), "gets")["on"] is True)
        sift_off = dict(on, ai_features_off=["proposals"])
        refused = None
        try:
            sift_routes.sift_ai_ready(sift_off, folder)
        except server_mod.WorkbookError as exc:
            refused = str(exc)
        check("223: with AI proposals off, Sift's screening shows no AI and a proposal is refused",
              sift_routes.sift_ai_state(sift_off, folder) is None and refused == sift_routes.sift_ai.OFF, str(refused))
        check("223: with AI features off, every feature is off whatever its own switch says",
              not any(server_mod.ai_on({"ai_suggest": False}, f) for f in ("statements", "proposals", "passages")))

        # a save names only its own app's features, another app's turned off kept as the file has them
        conf.write_text(json.dumps(dict(on, ai_features_off=["statements", "proposals"])), encoding="utf-8")
        server_mod.APP = "sift"
        server_mod.api_settings({"ai_features_off": []})
        after_sift = json.loads(conf.read_text(encoding="utf-8")).get("ai_features_off")
        server_mod.APP = "idiograph"
        server_mod.api_settings({"ai_features_off": ["gets", "proposals"]})
        after_idio = json.loads(conf.read_text(encoding="utf-8")).get("ai_features_off")
        check("223: each app's save turns its own features on and off and leaves another app's alone",
              after_sift == ["statements"] and after_idio == ["gets"], f"{after_sift} {after_idio}")

        # ── D. Appearance kept in the settings, read without a write, and copied on Sift's first start
        conf.write_text(json.dumps(on), encoding="utf-8")
        server_mod.api_settings({"appearance": "dark"})
        server_mod.api_settings({"appearance": "purple"})
        held = conf.read_bytes()
        read = server_mod.api_settings({"op": "read"})
        check("223: Appearance is saved in the app's own settings, anything but its three refused, and a read writes nothing",
              json.loads(held).get("appearance") == "dark" and read["config"].get("appearance") == "dark"
              and conf.read_bytes() == held)
        # opening the page only reads (cfgwrite, 21 October): a file that holds no appearance, written by hand in
        # its own order, stays byte for byte through the page's boot read, and a tick writes that one key alone
        bare = '{"projects": [],\n "corpus": "", "gravity_reference": "", "corpus_exclude": [], "interviewer": "Rowan"}'
        conf.write_text(bare, encoding="utf-8")
        before = conf.read_bytes()
        boot = re.search(r"async function themeFromSettings\(\) \{(.*?)\n\}", app_js, re.S)
        sends = re.findall(r"api\('/api/settings', \{([^}]*)\}", boot.group(1) if boot else "")
        server_mod.api_settings({"op": "read"})
        check("223: opening the page leaves config.json byte for byte as it was, the boot asking only to read",
              conf.read_bytes() == before and bool(boot) and sends == [" op: 'read' "]
              and "themeKeep" not in boot.group(1), str(sends))
        server_mod.api_settings({"appearance": "light"})
        written = json.loads(conf.read_text(encoding="utf-8"))
        again = conf.read_bytes()
        server_mod.api_settings({"appearance": "light"})
        check("223: changing the appearance writes only that key, and the same choice again writes nothing",
              written == dict(json.loads(bare), appearance="light") and conf.read_bytes() == again, str(sorted(written)))
        conf.write_text(json.dumps(dict(on, appearance="dark")), encoding="utf-8")
        held = conf.read_bytes()
        sift_conf = folder / "config.sift.json"
        sift_conf.unlink(missing_ok=True)
        server_mod.APP = "sift"
        copied = server_mod.first_start_copy("sift", config_path=sift_conf,
                                             sources={"config": conf, "state": None, "env": None, "base": None},
                                             own_env=folder / "sift.env", own_base=folder)
        sift_cfg = json.loads(sift_conf.read_text(encoding="utf-8"))
        check("223: Sift's first start copies the appearance Idiograph's settings keep, Idiograph's file unchanged",
              copied and sift_cfg.get("appearance") == "dark" and conf.read_bytes() == held, str(sift_cfg.get("appearance")))

        # ── D2. starting leaves the settings file as it was (docsfix, 21 October): Sift's first start on a file
        # written by hand adds only what it copies and its marker, every byte before them kept, and a start after
        # that, the marker there, writes nothing
        hand = ('{\r\n    "interviewer":"Wren",\r\n    "projects": [ ],\r\n    "corpus": "", "gravity_reference": "",'
                '\r\n    "corpus_exclude": []\r\n}\r\n')
        sift_conf.write_bytes(hand.encode("utf-8"))
        conf.write_text(json.dumps(dict(on, appearance="dark")), encoding="utf-8")
        server_mod.first_start_copy("sift", config_path=sift_conf,
                                    sources={"config": conf, "state": None, "env": None, "base": None},
                                    own_env=folder / "sift.env", own_base=folder)
        first = sift_conf.read_bytes().decode("utf-8")
        kept_part = hand[:hand.rindex("]") + 1]
        got = json.loads(first)
        again = server_mod.first_start_copy("sift", config_path=sift_conf,
                                            sources={"config": conf, "state": None, "env": None, "base": None},
                                            own_env=folder / "sift.env", own_base=folder)
        check("223: Sift's first start keeps the file's own text and line ends, adding only what it copies and its "
              "marker, and a later start writes nothing",
              first.startswith(kept_part) and "\n" not in first.replace("\r\n", "")
              and got.get(server_mod.app_identity.MARKER) and got.get("appearance") == "dark"
              and got.get("interviewer") == "Wren" and again is False and sift_conf.read_bytes().decode("utf-8") == first,
              repr(first[:200]))
        # adding and removing a project write the list alone, every other setting's text as the file had it
        server_mod.APP = "idiograph"
        place = folder / "Keeping bees"
        place.mkdir(exist_ok=True)
        hand = '{\n  "interviewer": "Wren",   "corpus": "",\n  "gravity_reference": "", "corpus_exclude": []\n}\n'
        conf.write_text(hand, encoding="utf-8")
        idiograph_routes.add_project(str(place))
        added = conf.read_text(encoding="utf-8")
        listed = json.loads(added).get("projects") or []
        pid = idiograph_routes.read_project(place)["id"]
        idiograph_routes.remove_project(pid)
        removed = json.loads(conf.read_text(encoding="utf-8"))
        check("223: adding a project writes only the projects list into the file, no default among it, and "
              "removing it takes it out the same way",
              added.startswith(hand[:hand.rindex("]") + 1]) and len(listed) == 1
              and set(json.loads(added)) == {"interviewer", "corpus", "gravity_reference", "corpus_exclude", "projects"}
              and removed.get("projects") == [], repr(added[:300]))
    finally:
        server_mod.CONFIG_PATH, server_mod.APP, server_mod.STATE_MEMORY = real

    # ── E. the family at each Home's foot
    rows = {}
    for app in app_identity.APPS:
        kept = server_mod.APP
        try:
            server_mod.APP = app
            rows[app] = server_mod.family_rows()
        finally:
            server_mod.APP = kept
    check("223: each Home's foot lists the other two apps, each with its name and one line, always",
          all([r["app"] for r in rows[a]] == [b for b in app_identity.APPS if b != a]
              and all(r["name"] and r["line"] and isinstance(r["installed"], bool) for r in rows[a]) for a in rows),
          str({a: [r["app"] for r in rows[a]] for a in rows}))
    ran = []
    kept = (server_mod.FAMILY_OPENER, server_mod.installed_at)
    try:
        server_mod.FAMILY_OPENER = ran.append
        opened = server_mod.api_family_open({"app": "sift"})
        server_mod.installed_at = lambda app, system=None: None
        fetched = server_mod.api_family_open({"app": "trace"})
        try:
            server_mod.api_family_open({"app": "idiograph"})
            own_refused = False
        except server_mod.WorkbookError:
            own_refused = True
    finally:
        server_mod.FAMILY_OPENER, server_mod.installed_at = kept
    check("223: Open starts the other app installed, from source its own server, and Download opens its releases page",
          opened["did"] == "run" and ran[0]["command"][-2:] == ["--app", "sift"] and fetched["did"] == "browse"
          and ran[1]["url"] == "https://github.com/Pharkie/trace-releases/releases/latest" and own_refused, str(ran))


def _inside(doc: Marked, child: str, holder: str) -> bool:
    """Whether the element `child` names sits inside the one `holder` names."""
    item = next((i for i in doc.items if i["id"] == child), None)
    while item is not None:
        if item["id"] == holder:
            return True
        item = item["parent"]
    return False
