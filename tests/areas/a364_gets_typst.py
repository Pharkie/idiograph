"""Area 364: the GETs print as Typst templates (typst3, 9 November 2026). On the demo's GETs board, the thematic
analysis demo's and an invented board of six participants, every word invented: `gets_print.typst_data` read from
the same walk as the HTML print view, the GET table and the audit trail typeset through `typeset.render` with
apps/idiograph/typst/gets.typ, their pages counted, each page's first row, the text each PDF carries against the HTML
view's text for the same board (the drift check: the design lives twice now), a GET's bar or a participant's name
never the last thing on a page, and the foot's three parts on every page, the project cut at a word when the line is
too long. A design's look is the review shots', never a check here."""
from __future__ import annotations

import html
import json
import re
import shutil
from pathlib import Path

from . import support
from .support import check, skip


def squash(text: str) -> str:
    """Text as two renderings are compared by: no spaces, folded, the ellipsis and quotes as they are."""
    return re.sub(r"\s+", "", html.unescape(str(text))).casefold()


def html_words(page: str) -> list[str]:
    """Each run of words the HTML view prints between its tags in `<main>` and its head, one string a run."""
    body = page.split('<header class="head">', 1)[1].split("</main>", 1)[0]
    body = re.sub(r"<script.*?</script>", " ", body, flags=re.S)
    return [t for t in (html.unescape(x).strip() for x in re.split(r"<[^>]+>", body)) if t]


def copy_demo(src: Path, project: Path, root: Path) -> Path:
    shutil.rmtree(root, ignore_errors=True)
    for name in ("Juno", "Mabel", "Rowan"):
        (root / name / "Working").mkdir(parents=True)
        shutil.copy2(src / f"{name} - EN & ES.xlsx", root / name / f"{name} - EN & ES.xlsx")
        for side in sorted((src / "Working").glob(f"{name} - *")):
            shutil.copy2(side, root / name / "Working" / side.name)
    for extra in ("idiograph-gets.json", "idiograph-codes.json"):
        if (src / extra).exists():
            shutil.copy2(src / extra, root / extra)
    shutil.copy2(project, root / "idiograph-project.json")
    return root


def invented(root: Path, routes, srv) -> Path:
    """Six invented participants on the demo's invented words, under one GET their two PETs and a statement each
    (deep spines), a sub-GET, two participant notes and row notes, a GET of one participant under the minimum, and a
    project name long enough that the foot must cut it."""
    shutil.rmtree(root, ignore_errors=True)
    src = support.DEMO_SHIPPED
    names, from_ = ["Ivy", "Hal", "Orla", "Tam", "Bea", "Kit"], ["Juno", "Mabel", "Rowan"]
    for i, name in enumerate(names):
        base = from_[i % 3]
        (root / name / "Working").mkdir(parents=True)
        shutil.copy2(src / f"{base} - EN & ES.xlsx", root / name / f"{name} - EN & ES.xlsx")
        for side in sorted((src / "Working").glob(f"{base} - *")):
            to = root / name / "Working" / side.name.replace(base, name, 1)
            to.write_text(side.read_text(encoding="utf-8").replace(f'"case": "{base}"', f'"case": "{name}"'), encoding="utf-8")
    project = json.loads(support.source("demo/idiograph-project.json").read_text(encoding="utf-8"))
    project["name"] = ("Living with a dog, a longer invented study of six households across one winter, the spring after "
                       "it and the summer that followed, told in their own words and read again a year on, with the "
                       "walks, the mornings and the evenings set side by side")
    (root / "idiograph-project.json").write_text(json.dumps(project), encoding="utf-8")
    srv.ROOT_OVERRIDE = str(root)
    book = str(root / "Ivy" / "Ivy - EN & ES.xlsx")
    shown = routes.api_gets({"workbook": book})
    cases = {c["case"]: c for c in shown["cases"]}
    cards = {c["key"]: {"x": c["x"], "y": c["y"]} for c in shown["cards"]}
    a, b = [], []
    for i, name in enumerate(names):
        a += [f"{name}/g1", f"{name}/g2"]
        line = next(k for k, ln in cases[name]["lines"].items() if ln.get("quotes"))
        cards[f"{name}/es/{line}"] = {"x": 900, "y": 40 * i, "text": ""}
        a.append(f"{name}/es/{line}")
    cards["Kit/pn/1"] = {"x": 1640, "y": 80, "text": "Invented: the household moved during the study."}
    cards["Tam/pn/1"] = {"x": 1640, "y": 0, "text": "Invented: he kept a diary of the walks for a month."}
    a.append("Kit/pn/1")
    b += ["Bea/g3", "Tam/pn/1"]
    groups = [{"id": "G1", "label": "Days run to the dog's clock, given a shape or closed in over a long winter",
               "description": "A start for some, a closing timetable for others", "note": "Invented note.\nIts second line.",
               "members": a + ["G3"], "x": 0, "y": -60},
              {"id": "G3", "label": "Early starts", "members": ["Hal/g5"], "x": 0, "y": 600},
              {"id": "G2", "label": "A reason nobody argues with", "members": b, "x": 1400, "y": -60}]
    rows = {"G1": {"Ivy": {"quote": "", "note": "Invented row note: her mornings are the dog's."}}}
    routes.api_gets_save({"workbook": book, "version": dict(shown["version"], cards=cards, groups=groups, discarded=[],
                                                             picks={}, notes=[], rows=rows)})
    return root


def test_gets_typst(scratch: Path):
    print("\n364. The GETs print as Typst: the GET table and the audit trail, their pages, their text and their foot")
    try:
        import typeset
    except ImportError:
        skip("364: the GETs print's Typst views", "family/typeset.py is not here yet")
        return
    import gets as gt
    import gets_print
    import i18n
    import idiograph_routes as routes
    import pdftext
    import server as srv

    template = gets_print.TEMPLATE
    check("364: one main template and one file a view, beside it the shared parts, so a full set can import each view",
          template.is_file() and all((template.parent / f).is_file() for f in ("gets-table.typ", "gets-trail.typ", "gets-parts.typ"))
          and "#let gets-table(d)" in (template.parent / "gets-table.typ").read_text(encoding="utf-8")
          and "#let gets-trail(d)" in (template.parent / "gets-trail.typ").read_text(encoding="utf-8"))

    saved = (srv.ROOT_OVERRIDE, srv.STATE_MEMORY)
    srv.STATE_MEMORY = {"recent": []}
    made: dict = {}

    def both(name: str, root: Path, what: str, **query):
        """The HTML view through its route and the Typst data and PDF of the same board, in the route's scope."""
        srv.ROOT_OVERRIDE = str(root)
        q = dict({"root": str(root), "what": what, "auto": "0"}, **query)
        code, page = routes.gets_print_page(q)
        with srv._lock, routes.route_scope(routes.GETS_PRINT_PATH, q):
            data = gets_print.typst_data(root, routes.gets_books(root), routes.read_project(root), None, what=what,
                                         detail=q.get("detail", "full"), notes=q.get("notes") == "1",
                                         researcher=routes.researcher_name())
        pdf = typeset.render(template, data)
        made[(name, what, q.get("detail", "full"))] = (code, page, data, pdf, pdftext.pages_text(pdf))
        return made[(name, what, q.get("detail", "full"))]

    try:
        demo = copy_demo(support.DEMO_SHIPPED, support.source("demo/idiograph-project.json"), scratch / "a364" / "demo")
        ta = copy_demo(support.source("demo/ta/pristine"), support.source("demo/ta/idiograph-project.json"), scratch / "a364" / "ta")
        big = invented(scratch / "a364" / "big", routes, srv)
        for name, root in (("demo", demo), ("ta", ta), ("big", big)):
            for what in ("table", "trail"):
                both(name, root, what, notes="1")
        both("demo", demo, "table", detail="selected")
        both("demo", demo, "trail", detail="selected")
    finally:
        srv.ROOT_OVERRIDE, srv.STATE_MEMORY = saved

    # ── A. the PDFs made, their pages counted
    counts = {k: len(v[4]) for k, v in made.items()}
    check("364: every view typeset to a PDF of pages, the demo's GET table on 3 pages as its HTML view prints, its trail "
          "and the invented board's on more than the table's",
          all(v[0] == 200 and v[3][:5] == b"%PDF-" and len(v[4]) >= 1 for v in made.values())
          and counts[("demo", "table", "full")] == 3 and counts[("demo", "trail", "full")] > 3
          and counts[("big", "trail", "full")] > counts[("big", "table", "full")], json.dumps({"/".join(k): n for k, n in counts.items()}))

    # ── B. the head on the first page and each page's first row
    first_ok, rows_ok, trail_ok = [], [], []
    for (name, what, detail), (_c, _p, data, _pdf, pages) in made.items():
        head = data["head"]
        first_ok.append(squash(pages[0]).startswith(squash(head["title"] + head["labels"]["project"] + head["project"])))
        if what == "table":
            # the table's column heads repeat at the top of every page after the first
            heads = squash("".join(data["table"][0]["heads"])) if data["table"] else ""
            rows_ok += [squash(p).startswith(heads) or any(squash(p).startswith(squash(g["label"])) for g in data["table"])
                        for p in pages[1:]]
        else:
            # a trail's page opens on a GET's bar, a participant's block or a row of the paths, never on a stray line
            opens = [squash(g["label"]) for g in data["trail"]] + [squash("".join(g["heads"])) for g in data["trail"]]
            for g in data["trail"]:
                for b in g["blocks"]:
                    # a block with no paths opens on its name, with no heads above it
                    opens.append(squash(b["badge"] + b["who"]) if not b["rows"] else "")
                    for r in b["rows"]:
                        c = next((c for c in r["cells"] if c and c["kind"] not in ("pass",)), None)
                        if c and c["kind"] == "turn":
                            opens.append(squash(c["where"] or ""))
            trail_ok += [any(squash(p).startswith(o) for o in opens if o) for p in pages[1:]]
    check("364: every PDF opens with the head, the document's name, then PROJECT and the project", all(first_ok))
    check("364: each page of a table after the first opens on its column heads or a GET's bar, each page of a trail on "
          "a GET's bar, a block's heads or a row's passage", all(rows_ok) and all(trail_ok) and rows_ok and trail_ok,
          f"{rows_ok} {trail_ok}")

    # ── C. the drift check: every run of words the HTML view prints is in the PDF, in the same order within a GET
    drift = {}
    foot_of = lambda d: [squash("".join(d["foot"]["left"])), squash(d["foot"]["middle"])]
    for key, (_c, page, data, _pdf, pages) in made.items():
        whole = squash(" ".join(pages))
        missing = [w for w in html_words(page) if squash(w) not in whole]
        if missing:
            drift["/".join(key)] = missing[:5]
    check("364: every run of words the HTML view prints for a board is in the Typst PDF of the same board, the table "
          "and the trail, Full and Selected, IPA and thematic analysis", not drift, json.dumps(drift, ensure_ascii=False)[:600])

    # ── D. a heading never ends a page: no page but the last ends on a GET's bar, its note or a participant's name
    enders = []
    for key, (_c, _p, data, _pdf, pages) in made.items():
        heads = []
        for g in data.get("table", []) + data.get("trail", []):
            heads += [g["label"] + (g["desc"] or "") + g["count"]["short"], g["note"]]
            heads += [b["badge"] + b["who"] for b in g.get("blocks", [])]
        heads = [squash(h) for h in heads if h]
        for i, p in enumerate(pages[:-1]):
            body = squash(p)
            for part in foot_of(data):
                body = body.replace(part, "")
            body = re.sub(r"page\d+of\d+$", "", body)
            if any(body.endswith(h) for h in heads):
                enders.append(f"{'/'.join(key)} page {i + 1}")
    check("364: no page but the last ends on a GET's bar, its note or a participant's name before their first row",
          not enders, ", ".join(enders))

    # ── E. the foot's three parts on every page, the page counted, the project cut at a word when too long
    feet = []
    for key, (_c, _p, data, _pdf, pages) in made.items():
        f = data["foot"]
        for i, p in enumerate(pages, 1):
            said = f["page"][0] + str(i) + f["page"][1] + str(len(pages)) + f["page"][2]
            feet.append(squash(said) in squash(p) and squash(f["middle"]) in squash(p) and squash(f["left"][-1]) in squash(p))
    big_foot = made[("big", "table", "full")]
    left = big_foot[2]["foot"]["left"]
    cut = big_foot[2]["foot"]["fit"]
    # the last page, whose text is the rows and the foot, the head with the project's whole name being the first's
    first = squash(big_foot[4][-1])
    check("364: every page's foot carries the part printed, the researcher, Confidential and the day, and Page n of N "
          "counted right", all(feet) and len(feet) == sum(len(v[4]) for v in made.values())
          and big_foot[2]["foot"]["middle"].startswith(routes.researcher_name()))
    check("364: a project name too long for the foot cut at a word with an ellipsis, the board, the part and the middle kept",
          0 <= cut < len(left) and squash(left[cut]) not in first and squash(left[cut].split(" ")[0]) + "" in first
          and "…" in big_foot[4][-1] and squash(left[-1]) in first, big_foot[4][-1][-260:])

    # ── F. the variants: Selected, thematic analysis's Theme table and four columns, the LGETs' and LPETs' names
    sel = made[("demo", "table", "selected")][2]
    ta_trail = made[("ta", "trail", "full")][2]
    ta_table = made[("ta", "table", "full")][2]
    check("364: Selected leaves out the column of what sits under a GET and every statement but the key quote",
          len(sel["table"][0]["heads"]) == 3 and all(not r["items"] or all(i["kind"] == "pn" for i in r["items"])
                                                      for g in sel["table"] for r in g["rows"]))
    with i18n.in_method("ta"):
        theme_words = (i18n.t("page_print.kind.get"), i18n.t("page_print.kind.quote"))
    check("364: a thematic analysis project's trail in four columns with no PET's, in its own words, its participants "
          "with no PETs marks", all(g["four"] and len(g["heads"]) == 4 for g in ta_trail["trail"])
          and ta_trail["trail"][0]["heads"][-1] == theme_words[0] and ta_trail["trail"][0]["heads"][1] == theme_words[1]
          and all(len(r["cells"]) == 4 for g in ta_trail["trail"] for b in g["blocks"] for r in b["rows"])
          and not ta_table["head"]["waiting"] and squash(theme_words[0]) in squash(" ".join(made[("ta", "trail", "full")][4][:1])))
    names = {}
    for var, key in ((gt.LGETS, "page_print.gets.lget_table_name"), (gt.NAMES, "page_print.gets.lpet_table_name")):
        token = var.set({})
        try:
            names[key] = gets_print.head_of({"name": "Invented"}, {"board": {}, "data": {}, "inside": [], "changed": set()},
                                            "table")["title"]
        finally:
            var.reset(token)
    check("364: a timepoints project's table is titled as the LGETs' or the LPETs', from the head both renderings read",
          all(names[k] == i18n.t(k) for k in names), json.dumps(names))

    # ── G. the HTML print view set in the two faces through the fonts' own style sheet
    page = made[("demo", "table", "full")][1]
    check("364: the HTML print view links the fonts' style sheet the server serves from family/static/fonts/",
          f'<link rel="stylesheet" href="{gets_print.FONTS_CSS}">' in page and gets_print.FONTS_CSS == "/fonts/fonts.css")
