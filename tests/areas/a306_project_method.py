"""Area 306: a project's method, IPA or thematic analysis (tadraw, 31 October 2026, Adam's choices of 28 October and
his "Thematic analysis, phase one" of 31 October). The method is the project file's `method`, "ipa" or "ta", chosen
on New project and fixed after, a file with none IPA's. One key swaps the words of the method's things: a method
other than IPA is a folder of the catalogue, `en.ta`, holding the whole sentences it says otherwise, and the page
and the server pick by the project in front.

What is checked: the method saved and read through the page's route and through `project new`, a file with none
read as IPA, `project show` and `cases` naming it, a method that is not one refused with nothing written, the
method fixed after (Settings' save, `project set` and a folder whose project file holds another), no timepoints in
a thematic analysis project, the MCP tools taking it, TA's catalogue swapping its keys in Python and in node, and
IPA's words unchanged. The fixtures are invented: a project on keeping an allotment through a year."""
from __future__ import annotations

import json
import re
import shutil
from pathlib import Path

from .support import check
from . import support

TRANSCRIPT = ("Sam: [00:00:03] What does the plot ask of you in March?\n"
              "Hazel Example: [00:00:08] Patience. The soil is cold and I want it to be warm.\n"
              "Sam: [00:00:20] And when the first beans come?\n"
              "Hazel Example: [00:00:26] I forget the cold. I stand there eating them off the stalk.\n")


def test_project_method(scratch: Path):
    print("\n306. A project's method, IPA or thematic analysis: saved and read, missing as IPA, fixed after creation "
          "through the route and the command line alike, and TA's words swapping by one key (31 October)")
    import base64
    import cli
    import i18n
    import idiograph_routes as routes
    import mcp_server
    import server as server_mod
    from workbook import WorkbookError

    base = scratch / "method-306"
    shutil.rmtree(base, ignore_errors=True)
    base.mkdir(parents=True)
    talk = base / "Hazel interview.txt"
    talk.write_text(TRANSCRIPT, encoding="utf-8")
    config_file = base / "config-306.json"
    config_file.write_text(json.dumps({"projects": [], "interviewer": "Sam", "corpus": "", "gravity_reference": "",
                                       "corpus_exclude": []}), encoding="utf-8")
    kept = (server_mod.CONFIG_PATH, server_mod.ROOT_OVERRIDE, server_mod.STATE_MEMORY)

    def as_page(fn, body):
        server_mod.CONFIG_PATH, server_mod.ROOT_OVERRIDE = config_file, None
        server_mod.STATE_MEMORY = {"recent": []}
        try:
            return fn(body)
        finally:
            server_mod.CONFIG_PATH, server_mod.ROOT_OVERRIDE, server_mod.STATE_MEMORY = kept

    def refused(fn, body) -> str:
        try:
            as_page(fn, body)
        except WorkbookError as exc:
            return str(exc)
        return ""

    def run(*args):
        return cli.run(["--config", str(config_file), *args])

    def run_json(*args):
        code, out, err = run("--json", *args)
        got = support.plain(json.loads(out)) if out.strip() else {}
        return code, (got if code == 0 else {}), err + (got.get("error", "") if code != 0 else "")

    def held(root: Path) -> dict:
        return json.loads((root / server_mod.PROJECT_FILE).read_text(encoding="utf-8"))

    data = base64.b64encode(talk.read_bytes()).decode("ascii")
    try:
        # 1. made as thematic analysis by the page's route and by the command line, IPA by default
        page_ta = base / "page-ta"
        page_ta.mkdir()
        read = as_page(routes.api_new_project, {"op": "read", "name": talk.name, "data": data})
        made = as_page(routes.api_new_project, {"op": "make", "folder": str(page_ta), "name": "Allotment year",
                                                "research_question": "How is a year on an allotment lived?",
                                                "method": "ta", "files": [{"name": talk.name, "data": data,
                                                                          "pseudonym": "Hazel",
                                                                          "interview": read["interview"],
                                                                          "speakers": read["speaker_roles"]}]})
        check("306: New project's route makes a thematic analysis project, `method` ta in its file and read so",
              held(page_ta).get("method") == "ta" and made["project"]["method"] == "ta"
              and routes.read_project(page_ta)["method"] == "ta", json.dumps(held(page_ta)))
        agent_ta, agent_ipa = base / "agent-ta", base / "agent-ipa"
        agent_ta.mkdir()
        agent_ipa.mkdir()
        code, dry, err = run_json("project", "new", str(agent_ta), "--name", "Allotment year", "--method", "ta",
                                  "--transcript", str(talk), "--pseudonym", "Hazel", "--dry-run")
        check("306: project new's dry run names the method and writes nothing",
              code == 0 and dry.get("method") == "ta" and not list(agent_ta.iterdir()), err + json.dumps(dry))
        code, got, err = run_json("project", "new", str(agent_ta), "--name", "Allotment year", "--method", "ta",
                                  "--transcript", str(talk), "--pseudonym", "Hazel", "--note", "A TA project")
        code2, got2, err2 = run_json("project", "new", str(agent_ipa), "--name", "Allotment year",
                                     "--transcript", str(talk), "--pseudonym", "Hazel", "--note", "An IPA project")
        check("306: project new makes it as the route does, and with no --method an IPA project",
              code == 0 and code2 == 0 and held(agent_ta).get("method") == "ta" and got["project"]["method"] == "ta"
              and held(agent_ipa).get("method") == "ipa" and got2["project"]["method"] == "ipa", err + err2)

        # 2. a file with no method is IPA's, and project show and cases name the method
        old = base / "old-ipa"
        old.mkdir()
        (old / server_mod.PROJECT_FILE).write_text(json.dumps({"name": "Old plot", "research_question": "",
                                                               "agents": {"allowed": True, "at": "2026-10-31T09:00:00+00:00"}}),
                                                   encoding="utf-8")
        for root in (page_ta, agent_ta):
            as_page(routes.api_project, {"root": routes.project_id(root), "agents": True})
        code, shown, err = run_json("--root", str(old), "project", "show")
        code2, shown2, err2 = run_json("--root", str(page_ta), "project", "show")
        _, said, _ = run("--root", str(page_ta), "project", "show")
        code3, study, err3 = run_json("--root", str(page_ta), "cases")
        check("306: a project file with no method reads as IPA, and project show and cases name each project's",
              routes.read_project(old)["method"] == "ipa" and code == 0 and shown["project"]["method"] == "ipa"
              and code2 == 0 and shown2["project"]["method"] == "ta" and "Method: Thematic analysis" in said
              and "PET labels" not in said and code3 == 0 and study["project"]["method"] == "ta", err + err2 + err3)

        # 3. refused: a method that is not one, and another than the file's, nothing written
        bad = base / "bad"
        bad.mkdir()
        settings = config_file.read_bytes()
        said = refused(routes.api_new_project, {"op": "make", "folder": str(bad), "name": "Plot", "method": "gt",
                                                "files": [{"name": talk.name, "data": data, "pseudonym": "Fenn",
                                                           "interview": read["interview"], "speakers": read["speaker_roles"]}]})
        check("306: a method that is not ipa or ta is refused in one line, nothing written",
              "ipa or ta" in said and not list(bad.iterdir()) and config_file.read_bytes() == settings, said)
        (bad / server_mod.PROJECT_FILE).write_text(json.dumps({"name": "Plot"}), encoding="utf-8")
        before = (bad / server_mod.PROJECT_FILE).read_bytes()
        said = refused(routes.api_new_project, {"op": "make", "folder": str(bad), "name": "Plot", "method": "ta",
                                                "files": [{"name": talk.name, "data": data, "pseudonym": "Fenn",
                                                           "interview": read["interview"], "speakers": read["speaker_roles"]}]})
        folder = as_page(routes.api_new_project, {"op": "folder", "path": str(bad)})
        check("306: New project in a folder whose project file is IPA's keeps IPA, thematic analysis refused, and the "
              "card is told the method it holds",
              "chosen when it was made" in said and (bad / server_mod.PROJECT_FILE).read_bytes() == before
              and sorted(p.name for p in bad.iterdir()) == [server_mod.PROJECT_FILE] and folder.get("method") == "ipa",
              said + json.dumps(folder))
        before = (page_ta / server_mod.PROJECT_FILE).read_bytes()
        said = refused(routes.api_project, {"root": routes.project_id(page_ta), "method": "ipa", "name": "Plot two"})
        same = as_page(routes.api_project, {"root": routes.project_id(page_ta), "method": "ta"})
        code, _, err = run("--root", str(agent_ta), "project", "set", "--method", "ipa", "--note", "Make it IPA")
        code2, _, err2 = run("--root", str(agent_ta), "project", "set", "--method", "ta", "--dry-run")
        check("306: the method is fixed after creation: Settings' save and project set refuse another, nothing "
              "written, and the project's own changes nothing",
              "chosen when it was made" in said and (page_ta / server_mod.PROJECT_FILE).read_bytes() == before
              and same["project"]["method"] == "ta" and code != 0 and "chosen when it was made" in err
              and held(agent_ta).get("method") == "ta" and code2 == 0, said + err + err2)
        said = refused(routes.api_project, {"root": routes.project_id(page_ta), "timepoints": 2})
        check("306: a thematic analysis project takes no timepoints yet",
              "no timepoints" in said and (page_ta / server_mod.PROJECT_FILE).read_bytes() == before, said)

        # 4. MCP takes the method
        mcp = mcp_server.Server(root=str(page_ta), config=str(config_file))
        res = mcp.call(mcp.by_name["project_show"], {})
        other = base / "mcp-new"
        other.mkdir()
        res2 = mcp.call(mcp.by_name["project_new"], {"folder": str(other), "method": "ta", "dry_run": True,
                                                     "request": "Look first",
                                                     "transcripts": [{"file": str(talk), "pseudonym": "Fenn"}]})
        check("306: MCP's project_show and project_new answer the method as the command line does",
              not res.get("isError") and (res.get("structuredContent") or {}).get("project", {}).get("method") == "ta"
              and not res2.get("isError") and (res2.get("structuredContent") or {}).get("method") == "ta"
              and not list(other.iterdir()), json.dumps([res, res2])[:600])
    except WorkbookError as exc:
        check("306: the page's calls run", False, str(exc))
    finally:
        server_mod.CONFIG_PATH, server_mod.ROOT_OVERRIDE, server_mod.STATE_MEMORY = kept

    # 5. TA's words: the catalogue's method folder, every key in English under its file's name with no slot
    # English lacks, swapping by one key in Python, and IPA's words what they were
    import boot
    roots = boot.roots(server_mod.apps_served("idiograph"))
    english = i18n.own(i18n.BASE, roots)
    problems = []
    for path in sorted(p for base_dir in i18n.folders(roots) for p in (base_dir / "en.ta").glob("*.json")):
        for key, value in json.loads(path.read_text(encoding="utf-8")).items():
            slots = {m for part in (value.values() if isinstance(value, dict) else [value]) for m in i18n.SLOT.findall(part)}
            given = english.get(key)
            known = {m for part in ((given.values() if isinstance(given, dict) else [given]) if given else [])
                     for m in i18n.SLOT.findall(part)}
            if given is None or not key.startswith(path.stem + ".") or not slots <= known | {"n"}:
                problems.append(f"{path.name}: {key}")
            elif isinstance(value, dict) and "other" not in value:
                problems.append(f"{path.name}: {key}'s plural forms")
    ta = i18n.method_messages("ta", "en", roots)
    check("306: TA's terms folder, every key in English under its file's name with no slot English lacks",
          len(ta) > 100 and not problems, "; ".join(problems[:6]))
    check("306: one key swaps TA's words in Python, IPA's unchanged",
          i18n.t("distil.card.statements", roots=roots) == "Experiential statements"
          and i18n.t("distil.card.statements", roots=roots, method="ta") == "Codes"
          and i18n.t("themes.unit.gets", roots=roots, method="ta") == "themes"
          and i18n.t("distil.find.statements", roots=roots, method="ta", n=3) == "3 codes"
          and i18n.t("distil.find.statements", roots=roots, method="ipa", n=3) == "3 statements"
          and all(i18n.messages("en", roots)[k] == english[k] for k in ta)
          and i18n.messages("en-US", roots, method="ta")["distil.card.statements"] == "Codes")
    page = support.page_text("family/static/page.html", "idiograph")
    served = server_mod.assembled(support.text("family/static/page.html"), "idiograph")
    marked = json.loads(re.search(r"var I18N = (\{.*?\});</script>", served, re.S).group(1))["marked"]
    check("306: the served page is IPA's words, its markup's words a method says otherwise named for the page",
          "Experiential statements" in page and "page_idiograph.work.gets" in marked
          and "page_idiograph.screens.gets" in marked and "page_idiograph.lede.software_interpretative_phenomenological_analysis" not in marked)

    # 6. and in node: t() in the method in front, a card drawn in its own, and back to IPA's
    script = support.i18n_js("idiograph") + """
const out = {};
out.ipa = t('distil.card.statements');
out.inTa = tIn('ta', () => t('distil.card.statements'));
out.after = t('distil.card.statements');
tMethod('ta');
out.ta = t('distil.find.statements', { n: 1 }) + ' / ' + t('distil.find.statements', { n: 4 });
out.kept = t('distil.card.files');
out.base = tBase('distil.card.statements');
tMethod('ipa');
out.back = t('distil.card.statements');
console.log(JSON.stringify(out));
"""
    ran = support.run_node(script, scratch, "method-306.js")
    try:
        o = json.loads(ran.stdout.strip().splitlines()[-1])
    except (ValueError, IndexError):
        o = {}
    check("306: in the page's scripts the method in front swaps the words and IPA's come back",
          o.get("ipa") == "Experiential statements" and o.get("inTa") == "Codes" and o.get("after") == "Experiential statements"
          and o.get("ta") == "1 code / 4 codes" and o.get("kept") == "Show files" and o.get("base") == "Experiential statements"
          and o.get("back") == "Experiential statements", (ran.stdout + ran.stderr)[-600:])

    # 7. the gaps phase one left (tagaps, 1 November 2026): the server's lines, the exports and the print in TA's
    # words, the search result never opening a PETs board, and IPA's what they were
    ta_gaps(scratch)


def ta_gaps(scratch: Path):
    """A thematic analysis project and an IPA one made from the demo as it ships, the TA one's board of codes saved
    through the GETs screen's own route, each run through the routes, the print, Save as PDF, the CSV, Search and
    the command line, each as the page or an agent calls them."""
    import cli
    import export as export_mod
    import i18n
    import idiograph_routes as routes
    import server as server_mod
    from workbook import WorkbookError

    base = scratch / "ta-gaps-306"
    shutil.rmtree(base, ignore_errors=True)
    roots = {"ta": base / "ta", "ipa": base / "ipa"}
    pristine = support.DEMO_SHIPPED
    for method, root in roots.items():
        for name in ("Juno", "Mabel", "Rowan"):
            (root / name / "Working").mkdir(parents=True, exist_ok=True)
            shutil.copy2(pristine / f"{name} - EN & ES.xlsx", root / name / f"{name} - EN & ES.xlsx")
            for side in sorted((pristine / "Working").glob(f"{name} - *")):
                shutil.copy2(side, root / name / "Working" / side.name)
        project = json.loads(support.source("demo/idiograph-project.json").read_text(encoding="utf-8"))
        project.update(method=method, name="Sharing a home with a dog" if method == "ta" else "Living with a dog",
                       agents={"allowed": True, "at": "2026-11-01T10:00:00+00:00"})
        (root / server_mod.PROJECT_FILE).write_text(json.dumps(project), encoding="utf-8")
    # the IPA project keeps the demo's GETs board of PETs, the TA one starts with none
    shutil.copy2(pristine / "idiograph-gets.json", roots["ipa"] / "idiograph-gets.json")
    config_file = base / "config-306.json"
    config_file.write_text(json.dumps({"projects": [{"root": str(r)} for r in roots.values()], "interviewer": "Sam",
                                       "your_name": "Ada Lark", "corpus": "", "gravity_reference": "",
                                       "corpus_exclude": [], "skip_permissions": True}), encoding="utf-8")
    kept = (server_mod.CONFIG_PATH, server_mod.ROOT_OVERRIDE, server_mod.STATE_MEMORY)
    ipa_words = re.compile(r"\b(PETs?|GETs?|[Ss]tatements?|[Qq]uotes?|[Ee]xperiential|[Ss]ub-themes?)\b")

    def call(route: str, body: dict):
        """A route as the page calls it, in the scope the server runs it in: its answer, or its refusal's words."""
        with server_mod.scoped(route, body):
            try:
                return server_mod.ROUTES[route](body)
            except WorkbookError as exc:
                return str(exc)

    def printed(root: Path, what: str) -> str:
        code, page = routes.gets_print_page({"root": str(root), "what": what, "detail": "full", "auto": "0"})
        return page if code == 200 else ""

    def text_of(page: str) -> str:
        body = re.sub(r"<style.*?</style>|<script.*?</script>", "", page, flags=re.S)
        return re.sub(r"<[^>]+>", " ", body.split("<body>", 1)[-1])

    title = lambda page: (re.search(r"<title>(.*?)</title>", page) or [None, ""])[1]
    server_mod.CONFIG_PATH, server_mod.ROOT_OVERRIDE, server_mod.STATE_MEMORY = config_file, None, {"recent": []}
    try:
        ta, ipa = roots["ta"], roots["ipa"]
        # the TA board as the canvas makes it: codes of each participant under a theme, one each under a subtheme
        state = call("/api/gets", {"root": str(ta)})
        cases = (state.get("cases") or []) if isinstance(state, dict) else []
        keys = {c["case"]: [f"{c['case']}/es/{k}" for k in list(c.get("lines") or {})[:3]] for c in cases}
        cards = {k: {"x": 100 + n * 220, "y": 100 + i * 160} for i, ks in enumerate(keys.values()) for n, k in enumerate(ks)}
        saved = call("/api/gets-save", {"root": str(ta), "version": {
            "id": "b1", "name": "Board 1", "cards": cards, "discarded": [],
            "groups": [{"id": "G1", "label": "The dog sets the shape of the day", "x": 0, "y": 0,
                        "members": ["G2"] + [k for ks in keys.values() for k in ks[1:]]},
                       {"id": "G2", "label": "Walks as the frame of the morning", "x": 0, "y": 0,
                        "members": [ks[0] for ks in keys.values() if ks]}]}})
        check("306: a thematic analysis project's board of codes saved through the GETs screen's route",
              isinstance(saved, dict) and len(cases) == 3 and all(len(k) == 3 for k in keys.values()), str(saved)[:300])

        # the print views: the table's, the trail's and the full set's names, heads and labels TA's, no PET column
        pages = {what: printed(ta, what) for what in ("table", "trail", "all")}
        left = [sorted(set(ipa_words.findall(text_of(p)))) for p in pages.values()]
        check("306: a TA project's printed table, trail and full set say Table of themes, Theme table, Extract, Code and "
              "Theme, with no PET column, no PET tables and no PET, GET, statement or quote anywhere",
              title(pages["table"]) == "Sharing a home with a dog - Board 1 - Theme table"
              and "<h1>Table of themes</h1>" in pages["table"] and title(pages["all"]).endswith(" - Themes")
              and "Under this theme" in pages["table"] and 'class="tr-wide tr-four"' in pages["trail"]
              and "<span>Extract</span><span>Code</span><span>Theme</span>" in pages["trail"]
              and 'href="#pets"' not in pages["all"] and left == [[], [], []],
              f"{[title(p) for p in pages.values()]} {left}")
        ipa_page, ipa_trail = printed(ipa, "table"), printed(ipa, "trail")
        check("306: an IPA project's printed GET table and trail keep IPA's words and five columns",
              title(ipa_page) == "Living with a dog - Board 1 - GET table" and "Table of Group Experiential Themes" in ipa_page
              and "Under this GET" in ipa_page and 'class="tr-wide tr-four"' not in ipa_trail
              and "<span>Statement</span><span>PET</span><span>GET</span>" in ipa_trail, title(ipa_page))

        # Save as PDF's name, and the agents' `gets export`, in the method's words
        place = call("/api/gets-boards", {"root": str(ta), "board": "b1", "op": "pdf", "what": "table"})
        ipa_place = call("/api/gets-boards", {"root": str(ipa), "board": "b1", "op": "pdf", "what": "table"})
        # the Save as PDF above now writes its file (Typst), so the dry run finds the plain name taken and dates its own
        code, out, err = cli.run(["--config", str(config_file), "--json", "gets", "--root", str(ta), "export", "--dry-run"])
        said = support.plain(json.loads(out)).get("said", "") if code == 0 and out.strip() else err
        check("306: Save as PDF and gets export name a TA project's PDF Theme table, an IPA project's GET table",
              isinstance(place, dict) and place.get("name", "").endswith("Board 1 - Theme table.pdf")
              and isinstance(ipa_place, dict) and ipa_place.get("name", "").endswith("Board 1 - GET table.pdf")
              and "Theme table" in said and ".pdf" in said and ": Theme table," in said, f"{place} | {ipa_place} | {said}")

        # the codes' CSV: its name and headings
        csv_ta = call("/api/export", {"path": str(ta / "Juno" / "Juno - EN & ES.xlsx"), "dry_run": True})
        csv_ipa = call("/api/export", {"path": str(ipa / "Juno" / "Juno - EN & ES.xlsx"), "dry_run": True})
        with i18n.in_method("ta"):
            head_ta = export_mod.header()
        check("306: a TA project's CSV is All Codes with Code, Proposed theme and Extract, an IPA one's as it was",
              isinstance(csv_ta, dict) and str(csv_ta.get("path", "")).endswith("Juno - All Codes.csv")
              and isinstance(csv_ipa, dict) and str(csv_ipa.get("path", "")).endswith("Juno - All Experiential Statements.csv")
              and head_ta[2:] == ["Code", "Proposed theme (blank for you)", "Extract"]
              and export_mod.header()[2] == "Experiential statement", f"{csv_ta} {csv_ipa} {head_ta}")

        # a refusal in the method's words, and IPA's in its own
        refused_ta = call("/api/gets-cases", {"root": str(ta), "op": "nothing"})
        refused_ipa = call("/api/gets-cases", {"root": str(ipa), "op": "nothing"})
        check("306: the server's refusals in a TA project are TA's, an IPA project's IPA's, and the run is IPA's again after",
              refused_ta == "That is not something the Themes screen does, so nothing was changed."
              and refused_ipa == "That is not something the GETs screen does, so nothing was changed."
              and i18n.method_now() == "ipa", f"{refused_ta} | {refused_ipa}")

        # Search: a PET's title in a TA project's themes file is no result, since no PETs board opens there
        hits = {m: call("/api/search", {"q": "Caught going soft", "scope": "project", "root": str(r)}) for m, r in roots.items()}
        screens = {m: sorted({x["go"]["screen"] for x in (h.get("results") or [])}) if isinstance(h, dict) else h
                   for m, h in hits.items()}
        found = call("/api/search", {"q": "stair", "scope": "project", "root": str(ta)})
        check("306: Search in a TA project opens no PETs board and still finds its codes, an IPA project's PET found",
              "pets" not in screens["ta"] and "pets" in screens["ipa"] and isinstance(found, dict)
              and "statements" in {x["go"]["screen"] for x in found.get("results") or []}, str(screens))

        # 8. the theme table in Word, the command line's lines and Search's kinds in TA's words (taword, 1 November)
        ta_word(ta, ipa, call, config_file, ipa_words)
    finally:
        server_mod.CONFIG_PATH, server_mod.ROOT_OVERRIDE, server_mod.STATE_MEMORY = kept


def ta_word(ta: Path, ipa: Path, call, config_file: Path, ipa_words):
    """A TA project's theme table as Microsoft Word on its Table view and through `gets export --word`, an IPA
    project's refused, then the command line's own lines and Search's kind names in each project's words."""
    import zipfile
    import cli

    before = sorted(p.name for p in ta.iterdir())
    made = call("/api/gets-boards", {"root": str(ta), "board": "b1", "op": "word", "detail": "full", "notes": False,
                                     "sending": False, "descriptions": True})
    path = Path(made["path"]) if isinstance(made, dict) and made.get("path") else None
    body, author = "", ""
    if path is not None and path.is_file():
        with zipfile.ZipFile(path) as z:
            body = z.read("word/document.xml").decode("utf-8")
            author = z.read("docProps/core.xml").decode("utf-8")
    words = re.sub(r"<[^>]+>", " ", body)
    check("306: a TA project's Microsoft Word writes its table of themes at the project's root, named as its PDF, "
          "Table of themes under the project, its themes, subthemes, codes with whose they are and their extracts, "
          "no IPA word, its author Your name",
          path is not None and path.parent == ta and path.name == "Sharing a home with a dog - Board 1 - Theme table.docx"
          and "Table of themes" in words and "The dog sets the shape of the day" in words
          and "Walks as the frame of the morning" in words and "(Juno, Initial, " in words and "‘" in words
          and '<w:pStyle w:val="Heading3"/>' in body and not ipa_words.findall(words)
          and "<dc:creator>Ada Lark</dc:creator>" in author
          and sorted(p.name for p in ta.iterdir()) == sorted(before + [path.name]),
          f"{made} {sorted(set(ipa_words.findall(words)))}")
    again = call("/api/gets-boards", {"root": str(ta), "board": "b1", "op": "word", "sending": True})
    refused = call("/api/gets-boards", {"root": str(ipa), "board": "b1", "op": "word"})
    check("306: a second Word export never writes over the first, Leave out the board's name names the project alone, "
          "and an IPA project's GETs are refused it with nothing written",
          isinstance(again, dict) and again.get("name") == "Sharing a home with a dog - Theme table.docx"
          and path is not None and path.is_file() and isinstance(refused, str) and "thematic analysis" in refused
          and not list(ipa.glob("*.docx")), f"{again} | {refused}")

    def said(root: Path, *args) -> str:
        code, out, err = cli.run(["--config", str(config_file), "--root", str(root), *args])
        return out if code == 0 else err

    dry = said(ta, "gets", "export", "--word", "--dry-run")
    check("306: gets export --word names the Word document as the app does and writes nothing, and board export in a "
          "TA project points to it",
          "Board 1 - Theme table (" in dry and ".docx in " in dry and "Dry run" in dry and len(list(ta.glob("*.docx"))) == 2
          and "gets export --word" in said(ta, "board", "export", "Juno", "--word"), dry)
    shown = {m: said(r, "gets", "show") for m, r in (("ta", ta), ("ipa", ipa))}
    own = {m: said(r, "statements", "Juno") for m, r in (("ta", ta), ("ipa", ipa))}
    kinds = {m: said(r, "search", "stair") for m, r in (("ta", ta), ("ipa", ipa))}
    check("306: the command line's own lines in a TA project are TA's (gets show, statements, project show, search's "
          "kinds) and an IPA project's IPA's",
          shown["ta"].startswith("Themes, Board 1 (b1).") and "  Code Juno: " in shown["ta"]
          and shown["ipa"].startswith("GETs, Board 1 (b1). A GET needs") and own["ta"].startswith("Juno: ")
          and " codes, short ids" in own["ta"] and "Extract Initial:" in own["ta"]
          and " statements, short ids" in own["ipa"] and "Quote Initial:" in own["ipa"]
          and "Code length:" in said(ta, "project", "show") and "Statement length:" in said(ipa, "project", "show")
          and "Codes " in kinds["ta"] and "Statements " not in kinds["ta"] and "Statements " in kinds["ipa"],
          f"{shown['ta'][:80]} | {own['ta'][:60]} | {kinds['ta'][:160]}")
    named = {m: call("/api/search", {"q": "stair", "scope": "project", "root": str(r)}) for m, r in (("ta", ta), ("ipa", ipa))}
    check("306: Search's answer in a TA project names its kinds in TA's words for the card, Codes, Extracts and Notes, "
          "and an IPA project's carries none",
          isinstance(named["ta"], dict) and (named["ta"].get("names") or {}).get("statement") == ["Code", "Codes"]
          and named["ta"]["names"].get("quote") == ["Extract", "Extracts"] and isinstance(named["ipa"], dict)
          and "names" not in named["ipa"], str((named["ta"] or {}).get("names") if isinstance(named["ta"], dict) else named))
    # i18nleft3 (2 November 2026): the command line's board lines in a TA project are TA's, an IPA project's IPA's
    fresh = {m: said(r, "gets", "fresh", "--name", "Board 9", "--dry-run") for m, r in (("ta", ta), ("ipa", ipa))}
    kept_said = {m: said(r, "gets", "revision", "--name", "Kept", "--dry-run") for m, r in (("ta", ta), ("ipa", ipa))}
    check("306: the command line's GETs board lines in a TA project name the themes board, an IPA project's the GETs "
          "board",
          "It would make the themes board Board 9, every card" in fresh["ta"]
          and "It would make the GETs board Board 9, every card" in fresh["ipa"]
          and "It would keep the themes board Board 1 as it stands" in kept_said["ta"]
          and "It would keep the GETs board Board 1 as it stands" in kept_said["ipa"]
          and not ipa_words.search(fresh["ta"] + kept_said["ta"]), f"{fresh} | {kept_said}")
