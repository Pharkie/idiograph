from __future__ import annotations

import json
import re
import shutil
from pathlib import Path

from workbook import WorkbookError

from . import support
from .support import DEMO_QUESTION, check, demo_copy, skip
import idiograph_routes


def test_pet_labels(scratch):
    print("\n93. PET labels: the book's letters by default, A, A1, A1.1, or numbers, PET 1, PET 1a, 1a.1, a setting "
          "of the project under Export and in Settings, Projects, which Word, print, the PET draft, the command line "
          "and MCP all follow (208, 209)")
    import html
    import inspect as inspect_mod
    import subprocess
    import xml.etree.ElementTree as ET
    import zipfile
    import cli
    import mcp_server
    import server as server_mod
    import themes as themes_mod
    import themes_print
    import themes_word

    js = support.text("apps/idiograph/static/themes.js")
    app = support.text("family/static/shell.js", "apps/idiograph/static/distil.js")
    schema = json.loads(support.source("docs/schemas/project.schema.json").read_text(encoding="utf-8"))
    fn = lambda src, name: src.split(f"function {name}(", 1)[1].split("\n}", 1)[0] if f"function {name}(" in src else ""
    pristine = support.DEMO_PRISTINE
    W = themes_word.W
    tag = lambda name: f"{{{W}}}{name}"

    # ── A. one function, two schemes
    tree = [{"id": "a", "themes": [{"id": "b", "themes": [{"id": "c", "themes": [{"id": "d", "themes": [{"id": "e"}]}]}]},
                                   {"id": "f"}]},
            {"id": "g", "themes": [{"id": "h"}]}]
    check("93: a project file with no pet_labels, or anything else in it, gives the book's letters, and numbers only when it says so",
          [themes_mod.pet_labels_of(v) for v in (None, "", "letters", "Numbers", "roman", 1, "numbers")]
          == ["letters"] * 6 + ["numbers"] and themes_mod.PET_LABELS == ("letters", "numbers")
          and inspect_mod.signature(themes_mod.pet_numbers).parameters["labels"].default == "letters"
          and idiograph_routes.read_project(None)["pet_labels"] == "letters")
    check("93: letters at five depths, A, A1, A1.1, A1.1.1 and A1.1.1.1, a second sub-theme A2 and a second PET B",
          themes_mod.pet_numbers(tree) == themes_mod.pet_numbers(tree, "letters")
          == {"a": "A", "b": "A1", "c": "A1.1", "d": "A1.1.1", "e": "A1.1.1.1", "f": "A2", "g": "B", "h": "B1"},
          str(themes_mod.pet_numbers(tree)))
    check("93: numbers at five depths, PET 1, PET 1a, 1a.1, 1a.1.1 and 1a.1.1.1, a second sub-theme PET 1b and a second PET PET 2",
          themes_mod.pet_numbers(tree, "numbers")
          == {"a": "PET 1", "b": "PET 1a", "c": "1a.1", "d": "1a.1.1", "e": "1a.1.1.1", "f": "PET 1b", "g": "PET 2", "h": "PET 2a"},
          str(themes_mod.pet_numbers(tree, "numbers")))
    many = [{"id": f"p{i}", "themes": [{"id": f"p{i}s{j}"} for j in range(1, 12)] if i == 1 else []} for i in range(1, 29)]
    lettered, counted = themes_mod.pet_numbers(many), themes_mod.pet_numbers(many, "numbers")
    check("93: past Z the letters run on AA, AB, a sub-theme past nine A10 and A11, and the numbers PET 27 and PET 1k",
          [lettered[f"p{i}"] for i in (1, 2, 26, 27, 28)] == ["A", "B", "Z", "AA", "AB"]
          and [lettered[f"p1s{j}"] for j in (1, 9, 10, 11)] == ["A1", "A9", "A10", "A11"]
          and [counted[f"p{i}"] for i in (26, 27)] == ["PET 26", "PET 27"] and counted["p1s11"] == "PET 1k", str(lettered["p27"]))
    check("93: a heading takes a full stop after a PET's label and a sub-theme's and none after a group's, under each scheme",
          [themes_mod.numbered(n, "T") for n in ("A", "AA", "A1", "A10", "A1.1", "A1.1.1", "PET 1", "PET 1a", "1a.1", "1a.1.1")]
          == ["A. T", "AA. T", "A1. T", "A10. T", "A1.1 T", "A1.1.1 T", "PET 1. T", "PET 1a. T", "1a.1 T", "1a.1.1 T"])

    # ── B. the fixture: an invented case on the demo's words in an invented project, a board five labels deep
    root = scratch / "labels-root"
    shutil.rmtree(root, ignore_errors=True)
    folder = root / "P{} - {}-{}".format(7, "Hazel", "Example")
    book = demo_copy(folder, "P7 Hazel - EN & ES.xlsx")
    read = themes_mod.read_cards(book)
    k = [c["key"] for c in read["cards"]]
    board = themes_mod.blank_version(read["cards"])
    for key, (x, y) in {k[0]: (0, 100), k[1]: (0, 300), k[2]: (0, 500), k[3]: (0, 700), k[4]: (0, 900),
                        k[5]: (0, 1300), k[6]: (2000, 100), k[7]: (2000, 300)}.items():
        board["cards"][key].update(x=x, y=y)
    board["groups"] = [
        {"id": "g1", "label": "Days shaped round the dog", "members": [k[0], "g2", "g6"], "x": 0, "y": 40},
        {"id": "g2", "label": "Waking before the house", "members": [k[1], "g3"], "x": 0, "y": 240},
        {"id": "g3", "label": "The lead by the door", "members": [k[2], "g4"], "x": 0, "y": 440},
        {"id": "g4", "label": "A bark at the gate", "members": [k[3], "g5"], "x": 0, "y": 640},
        {"id": "g5", "label": "The sixth stair", "members": [k[4]], "x": 0, "y": 840},
        {"id": "g6", "label": "Nights on the sofa", "members": [k[5]], "x": 0, "y": 1240},
        {"id": "g7", "label": "Walks in all weather", "members": [k[6], "g8"], "x": 2000, "y": 40},
        {"id": "g8", "label": "The field past the church", "members": [k[7]], "x": 2000, "y": 240}]
    themes_mod.save(book, board, "P7 - Hazel")
    titles = [g["label"] for g in board["groups"]]
    order = ["g1", "g2", "g3", "g4", "g5", "g6", "g7", "g8"]
    marks = {"letters": ["A", "A1", "A1.1", "A1.1.1", "A1.1.1.1", "A2", "B", "B1"],
             "numbers": ["PET 1", "PET 1a", "1a.1", "1a.1.1", "1a.1.1.1", "PET 1b", "PET 2", "PET 2a"]}
    by_id = {g["id"]: g["label"] for g in board["groups"]}
    want = {s: [themes_mod.numbered(m, by_id[g]) for m, g in zip(marks[s], order)] for s in marks}
    check("93: the headings the two schemes give, the book's letters and the numbers",
          want["letters"][:3] == ["A. Days shaped round the dog", "A1. Waking before the house", "A1.1 The lead by the door"]
          and want["numbers"][:3] == ["PET 1. Days shaped round the dog", "PET 1a. Waking before the house", "1a.1 The lead by the door"]
          and len(titles) == 8)
    project = {"name": "Hens, a scratch project", "research_question": DEMO_QUESTION,
               "agents": {"allowed": True, "at": "2026-10-06T10:00:00+01:00"}, "order": ["P7 - Hazel"],
               "updated": "2026-10-06T10:00:00+01:00", "colour": "an invented key the app does not know"}
    pfile = root / "idiograph-project.json"
    pfile.write_text(json.dumps(project), encoding="utf-8")
    cfg = scratch / "labels-config.json"
    cfg.write_text(json.dumps({"projects": [{"root": str(root)}], "interviewer": "Adam"}), encoding="utf-8")

    def word_heads(path: Path) -> list[str]:
        with zipfile.ZipFile(path) as z:
            body = z.read("word/document.xml").decode("utf-8")
        out = []
        for p in ET.fromstring(body).iter(tag("p")):
            style = p.find(f"{tag('pPr')}/{tag('pStyle')}")
            name = style.get(tag("val")) if style is not None else ""
            if name.startswith("Heading") and name != "Heading1":
                out.append("".join(t.text or "" for t in p.iter(tag("t"))))
        return out

    def print_heads(page: str) -> list[str]:
        main = page.split("<main>", 1)[1].split("</main>", 1)[0]
        return [html.unescape(re.sub(r"<[^>]+>", "", m.group(0))).strip() for m in re.finditer(r"<h[2-6][^>]*>.*?</h[2-6]>", main)]

    def draft_heads(text: str) -> list[str]:
        return [ln.lstrip("#").strip() for ln in text.splitlines() if ln.startswith("#")][1:]

    ends = [f"Not placed ({len(k) - 8})"]

    # ── C. Word, print and the PET draft from the modules, each scheme
    outline = themes_word.board_of(book)[0]
    agree = {}
    for scheme in ("letters", "numbers"):
        w = [themes_word.plain([p])[0] if False else "".join(r["text"] for r in p["runs"])
             for p in themes_word.blocks("P7 - Hazel", outline, scheme, unplaced=True, binned=True) if p["style"] in (2, 3, 4, 5)]
        pr = print_heads(themes_print.page(book, "P7 - Hazel", auto=False, labels=scheme, unplaced=True, binned=True))
        dr = draft_heads(themes_mod.draft_markdown(book, "P7 - Hazel", labels=scheme)[0])
        agree[scheme] = (w, pr, dr)
    check("93: under letters Word, print and the PET draft carry the same labels in the same order, A to B1",
          agree["letters"][0] == agree["letters"][1] == agree["letters"][2] == want["letters"] + ends, str(agree["letters"][1][:3]))
    check("93: under numbers the three carry PET 1 to PET 2a alike, as before",
          agree["numbers"][0] == agree["numbers"][1] == agree["numbers"][2] == want["numbers"] + ends, str(agree["numbers"][1][:3]))
    shown = themes_word.plain(themes_word.blocks("P7 - Hazel", outline, unplaced=True, binned=True))
    printed = themes_print.page(book, "P7 - Hazel", auto=False, unplaced=True, binned=True)
    check("93: with no scheme named the modules take the letters, a PET in Word in capitals, A. DAYS SHAPED ROUND THE DOG, and in "
          "print under its letter and a full stop",
          "A. DAYS SHAPED ROUND THE DOG" in shown and "B. WALKS IN ALL WEATHER" in shown
          and '<span class="number">A.</span> <span class="title">Days shaped round the dog</span>' in printed
          and '<h5 class="group-title">A1.1.1 A bark at the gate</h5>' in printed and "PET 1" not in printed
          and themes_mod.draft_markdown(book, "P7 - Hazel")[0].split("\n\n", 2)[1].splitlines()[0]
          == "- A. Days shaped round the dog (2 sub-themes · 6 statements)")

    # ── D. through the server: the project's setting, switched both ways from the Export menu's route
    kept = (server_mod.CONFIG_PATH, server_mod.ROOT_OVERRIDE, server_mod.STATE_MEMORY)
    try:
        server_mod.CONFIG_PATH, server_mod.ROOT_OVERRIDE = cfg, str(root)
        server_mod.STATE_MEMORY = {"recent": []}

        def exported() -> tuple:
            word = idiograph_routes.api_themes_export({"workbook": str(book), "op": "word", "unplaced": True, "binned": True})
            draft = idiograph_routes.api_themes_export({"workbook": str(book)})
            code, page = idiograph_routes.themes_print_page({"workbook": str(book), "auto": "0", "unplaced": "1", "binned": "1"})
            return (word_heads(folder / Path(word["word"]).name), print_heads(page),
                    draft_heads(themes_mod.draft_path(book, "Board 1").read_text(encoding="utf-8")),
                    word.get("labels"), draft.get("labels"), code)

        opened = idiograph_routes.api_themes({"workbook": str(book)})
        first = exported()
        check("93: a project with no pet_labels sends letters with the case, and its Word, print and draft are lettered",
              (opened.get("project") or {}).get("pet_labels") == "letters" and idiograph_routes.pet_labels_for(book) == "letters"
              and first[0] == first[1] == first[2] == want["letters"] + ends and first[3:] == ("letters", "letters", 200),
              str(first[0][:2]))
        before = json.loads(pfile.read_text(encoding="utf-8"))
        saved = idiograph_routes.api_project({"path": str(book), "pet_labels": "numbers"})
        after = json.loads(pfile.read_text(encoding="utf-8"))
        check("93: PET labels saves pet_labels in the project file at once, every other key kept, order and an unknown one among them",
              saved["project"]["pet_labels"] == "numbers" and after == dict(before, pet_labels="numbers")
              and after["order"] == ["P7 - Hazel"] and after["colour"] == project["colour"]
              and after["updated"] == project["updated"] and after["agents"] == project["agents"], str(after)[:200])
        second = exported()
        check("93: switched to 1 2 3, Word, print and the draft all follow at once, PET 1 to PET 2a",
              second[0] == second[1] == second[2] == want["numbers"] + ends and second[3:] == ("numbers", "numbers", 200),
              str(second[0][:2]))
        idiograph_routes.api_project({"path": str(book), "pet_labels": "letters"})
        third = exported()
        check("93: and switched back to A B C, the three follow again, the file saying letters",
              third[0] == third[1] == third[2] == want["letters"] + ends
              and json.loads(pfile.read_text(encoding="utf-8")) == dict(before, pet_labels="letters"))
        held = pfile.read_bytes()
        refused = lambda body: (lambda: idiograph_routes.api_project(body))
        try:
            idiograph_routes.api_project({"path": str(book), "pet_labels": "roman"})
            bad = ""
        except WorkbookError as exc:
            bad = str(exc)
        demo_file = server_mod.DEMO_PROJECT.read_bytes()
        try:
            idiograph_routes.api_project({"root": "demo", "pet_labels": "numbers"})
            demo_said = ""
        except WorkbookError as exc:
            demo_said = str(exc)
        check("93: anything but letters or numbers is refused with nothing written, and so is a save for the demo",
              bad == "PET labels are letters or numbers, so nothing was saved." and pfile.read_bytes() == held
              and demo_said == "The demo's project is fixed." and server_mod.DEMO_PROJECT.read_bytes() == demo_file
              and callable(refused({})))

        # ── E. the command line and MCP: the project's setting, --labels and labels for one run
        cmd = lambda *a: cli.run(["--root", str(root), "--config", str(cfg), *a])
        docx = lambda: sorted(p.name for p in folder.iterdir() if p.suffix == ".docx")
        code1, out1, err1 = cmd("board", "export", "Hazel", "--word", "--json")
        own = support.plain(json.loads(out1)) if code1 == 0 else {}
        idiograph_routes.api_project({"path": str(book), "pet_labels": "numbers"})
        code2, out2, err2 = cmd("board", "export", "Hazel", "--word", "--json")
        theirs = support.plain(json.loads(out2)) if code2 == 0 else {}
        code3, out3, err3 = cmd("board", "export", "Hazel", "--word", "--labels", "letters", "--json")
        over = support.plain(json.loads(out3)) if code3 == 0 else {}
        check("93: board export follows the project's setting, letters and then numbers, and --labels overrides it for one run",
              code1 == code2 == code3 == 0 and own.get("labels") == "letters" and theirs.get("labels") == "numbers"
              and over.get("labels") == "letters"
              and word_heads(folder / own["file"])[:2] == want["letters"][:2]
              and word_heads(folder / theirs["file"])[:2] == want["numbers"][:2]
              and word_heads(folder / over["file"])[:2] == want["letters"][:2]
              and json.loads(pfile.read_text(encoding="utf-8"))["pet_labels"] == "numbers", (err1 + err2 + err3)[:300])
        have = docx()
        code4, out4, err4 = cmd("board", "export", "Hazel", "--word", "--labels", "roman")
        code5, out5, _e5 = cmd("board", "export", "Hazel", "--word", "--labels", "numbers", "--dry-run")
        check("93: --labels takes letters or numbers alone, anything else refused in one line and nothing written, and its dry run writes nothing",
              code4 == 1 and err4.strip() == "Say --labels letters or --labels numbers." and docx() == have
              and code5 == 0 and out5.startswith("Dry run, nothing was written.") and docx() == have, err4[:200])
        tool = mcp_server.BY_NAME["board_export"]
        mcp = mcp_server.Server(str(root), config=str(cfg))
        made_m = mcp.call(tool, {"case": "Hazel", "labels": "letters"})
        made_p = mcp.call(tool, {"case": "Hazel"})
        bad_m = mcp.call(tool, {"case": "Hazel", "labels": "roman"})
        check("93: MCP's board_export takes labels, letters or numbers, the project's setting without it, and refuses anything else",
              tool["inputSchema"]["properties"]["labels"]["enum"] == ["letters", "numbers"]
              and "labels" not in tool["inputSchema"]["required"]
              and made_m["isError"] is False and support.plain(made_m["structuredContent"])["labels"] == "letters"
              and word_heads(folder / support.plain(made_m["structuredContent"])["file"])[:2] == want["letters"][:2]
              and made_p["isError"] is False and support.plain(made_p["structuredContent"])["labels"] == "numbers"
              and word_heads(folder / support.plain(made_p["structuredContent"])["file"])[:2] == want["numbers"][:2]
              and bad_m["isError"] is True and "dry_run and labels" in mcp_server.TOOLS_LINE, str(bad_m)[:200])
        code6, out6, _e6 = cmd("validate")
        pfile.write_text(json.dumps(dict(json.loads(pfile.read_text(encoding="utf-8")), pet_labels="roman")), encoding="utf-8")
        code7, out7, err7 = cmd("validate")
        check("93: validate reads pet_labels against the project schema, letters or numbers and nothing else",
              code6 == 0 and "Every file of the project reads as its schema says" in out6
              and code7 == 0 and 'The project file: project.pet_labels should be one of "letters", "numbers", not "roman".' in out7 + err7
              and schema["properties"]["pet_labels"]["enum"] == ["letters", "numbers"]
              and idiograph_routes.read_project(root)["pet_labels"] == "letters", (out7 + err7)[:200])
        idiograph_routes.api_project({"path": str(book), "pet_labels": "letters"})
    finally:
        server_mod.CONFIG_PATH, server_mod.ROOT_OVERRIDE, server_mod.STATE_MEMORY = kept

    # ── F. two projects: Settings' Projects saves the one shown and leaves the other alone
    two_a, two_b = scratch / "labels-two-a", scratch / "labels-two-b"
    for at in (two_a, two_b):
        shutil.rmtree(at, ignore_errors=True)
        demo_copy(at / "Juno", "Juno - EN & ES.xlsx")
        (at / "idiograph-project.json").write_text(json.dumps({"name": at.name, "research_question": DEMO_QUESTION,
                                                              "order": ["Juno"]}), encoding="utf-8")
    cfg2 = scratch / "labels-two-config.json"
    cfg2.write_text(json.dumps({"projects": [{"root": str(two_a)}, {"root": str(two_b)}], "interviewer": "Adam"}), encoding="utf-8")
    b_held = (two_b / "idiograph-project.json").read_bytes()
    kept = (server_mod.CONFIG_PATH, server_mod.ROOT_OVERRIDE, server_mod.STATE_MEMORY)
    try:
        server_mod.CONFIG_PATH, server_mod.ROOT_OVERRIDE = cfg2, None
        server_mod.STATE_MEMORY = {"recent": []}
        listed = idiograph_routes.api_projects({"op": "read"})["projects"]
        answer = idiograph_routes.api_project({"root": idiograph_routes.project_id(two_a), "pet_labels": "numbers"})
        listed2 = {p["name"]: p["pet_labels"] for p in idiograph_routes.api_projects({"op": "read"})["projects"]}
        try:
            idiograph_routes.api_project({"pet_labels": "numbers"})
            unnamed = ""
        except WorkbookError as exc:
            unnamed = str(exc)
    finally:
        server_mod.CONFIG_PATH, server_mod.ROOT_OVERRIDE, server_mod.STATE_MEMORY = kept
    check("93: Settings' Projects lists each project's pet_labels, saves the one it names by its id, and asks which when it names none",
          [p["pet_labels"] for p in listed] == ["letters", "letters"] and answer["project"]["pet_labels"] == "numbers"
          and listed2 == {"labels-two-a": "numbers", "labels-two-b": "letters"}
          and (two_b / "idiograph-project.json").read_bytes() == b_held
          and json.loads((two_a / "idiograph-project.json").read_text(encoding="utf-8"))["order"] == ["Juno"]
          and unnamed == "Say which project, so nothing was saved.", str(listed2))

    # ── G. the demo keeps the book's letters
    demo_data = json.loads(server_mod.DEMO_PROJECT.read_text(encoding="utf-8"))
    rowan = demo_copy(scratch / "labels-demo" / "Rowan", "Rowan - EN & ES.xlsx")
    for side in (pristine / "Working").glob("Rowan - *"):
        (rowan.parent / "Working").mkdir(exist_ok=True)
        shutil.copy2(side, rowan.parent / "Working" / side.name)
    shutil.copy2(pristine / "Rowan - EN & ES.xlsx", rowan)
    demo_print = themes_print.page(rowan, "Rowan", auto=False, labels=idiograph_routes.read_project(server_mod.DEMO_DIR)["pet_labels"])
    check("93: the demo's project file carries no pet_labels, so the demo reads the book's letters, its PETs lettered A, B",
          "pet_labels" not in demo_data and idiograph_routes.read_project(server_mod.DEMO_DIR)["pet_labels"] == "letters"
          and idiograph_routes.pet_labels_for(server_mod.DEMO_WORKBOOK) == "letters"
          and '<span class="number">A.</span>' in demo_print and '<span class="number">B.</span>' in demo_print
          and '<span class="number">PET 1.</span>' not in demo_print)

    # ── H. the Export menu's choice, in the page and in node
    clicker = js.split("$('th-xmenu').addEventListener('click', (e) => {", 1)[1].split("});", 1)[0]
    check("93: a press on the pair saves at once and leaves the menu open, the export entries as they were, the pair drawn on open",
          "if (pick) { thLabels(pick.dataset.labels); return; }" in clicker
          and clicker.index("[data-labels]") < clicker.index("[data-xop]") and "thLabelsDraw();" in fn(js, "thXmenu")
          and "api('/api/project', { path: TH.path, pet_labels: value })" in fn(js, "thLabels")
          and "b.disabled = !p || !!p.demo;" in fn(js, "thLabelsDraw"))
    node = shutil.which("node")
    if not node:
        skip("93: the Export menu's choice in node", "no node on this machine")
    else:
        script = scratch / "labels-check.js"
        script.write_text(support.i18n_js() + js + r"""
const RESTART_LINE = 'Restart the server to finish this update.';
const needsRestart = () => false;
const sent = [];
const said = [];
function say(m) { said.push(m); }
let reply = (body) => ({ project: { id: 'hens', name: 'Hens', pet_labels: body.pet_labels } });
async function api(path, body) { sent.push([path, body]); return reply(body); }
function fake(v) {
  const b = { dataset: { labels: v }, disabled: false, on: false, checked: '' };
  b.classList = { toggle: (c, on) => { if (c === 'on') b.on = !!on; } };
  b.setAttribute = (k, val) => { if (k === 'aria-checked') b.checked = val; };
  return b;
}
const pair = [fake('letters'), fake('numbers')];
const $ = (id) => (id === 'th-xlabels' ? { querySelectorAll: () => pair } : null);
(async () => {
  TH.live = true;
  TH.path = '/scratch/hens/P7/book.xlsx';
  TH.project = { id: 'hens', name: 'Hens', research_question: 'q', pet_labels: 'letters', demo: false };
  thLabelsDraw();
  const first = pair.map((b) => [b.on, b.checked, b.disabled]);
  await thLabels('numbers');
  const after = { sent: JSON.parse(JSON.stringify(sent)), project: TH.project, pair: pair.map((b) => [b.on, b.checked]) };
  await thLabels('numbers');
  const again = sent.length;
  TH.project = { id: 'demo', demo: true };
  thLabelsDraw();
  const demo = pair.map((b) => [b.on, b.disabled]);
  await thLabels('numbers');
  const demoSent = sent.length;
  TH.project = { id: 'hens', pet_labels: 'letters' };
  reply = () => ({ project: { id: 'hens' } });
  await thLabels('numbers');
  console.log(JSON.stringify({ first, after, again, demo, demoSent, old: [said, TH.project.pet_labels] }));
})();
""", encoding="utf-8")
        run = subprocess.run([node, str(script)], capture_output=True, text=True, encoding="utf-8")
        if run.returncode != 0:
            check("93: the Export menu's choice runs in node", False, run.stderr.strip()[:300])
        else:
            out = support.plain(json.loads(run.stdout))
            check("93: in node, A B C pressed for a project with letters, a press on 1 2 3 posts pet_labels for this case and presses it",
                  out["first"] == [[True, "true", False], [False, "false", False]]
                  and out["after"]["sent"] == [["/api/project", {"path": "/scratch/hens/P7/book.xlsx", "pet_labels": "numbers"}]]
                  and out["after"]["project"] == {"id": "hens", "name": "Hens", "research_question": "q", "pet_labels": "numbers", "demo": False}
                  and out["after"]["pair"] == [[False, "false"], [True, "true"]] and out["again"] == 1, str(out)[:300])
            check("93: in node, the demo's pair is fixed on the letters and sends nothing, and a server from before it says to restart",
                  out["demo"] == [[True, True], [False, True]] and out["demoSent"] == 1
                  and out["old"] == [["Restart the server to finish this update."], "letters"], str(out)[:300])

    # ── I. Settings' Projects, in the page and in node
    region = app.split("const petLabelsOf", 1)[1].split("/* ──────────────────────────────────────────────────────"
                                                        " AI agents ── */", 1)[0] if "const petLabelsOf" in app else ""
    if not node or not region:
        check("93: Settings' pair is there to run", bool(region))
    else:
        script = scratch / "labels-settings.js"
        script.write_text("const petLabelsOf" + region + r"""
const RESTART_LINE = 'Restart the server to finish this update.';
const needsRestart = () => false;
const sent = [];
const pair = [];
for (const v of ['letters', 'numbers']) {
  const b = { dataset: { labels: v }, disabled: false, on: false, checked: '' };
  b.classList = { toggle: (c, on) => { if (c === 'on') b.on = !!on; } };
  b.setAttribute = (k, val) => { if (k === 'aria-checked') b.checked = val; };
  pair.push(b);
}
const said = { hidden: true, textContent: '' };
const $ = (id) => (id === 'set-labels' ? { querySelectorAll: () => pair } : id === 'labels-said' ? said : null);
const shown = { id: 'bees', name: 'Bees', pet_labels: 'letters' };
const PROJ = { own: { id: 'bees', pet_labels: 'letters' }, list: [shown] };
const S = { data: { project: { id: 'bees', pet_labels: 'letters' } } };
const TH = { project: { id: 'bees', pet_labels: 'letters' } };
let at = shown;
const projectAt = () => at;
const projectBody = (p) => ({ root: p.id });
async function api(path, body) { sent.push([path, body]); return { project: { id: body.root, pet_labels: body.pet_labels } }; }
(async () => {
  drawLabels(shown);
  const first = pair.map((b) => [b.on, b.disabled]);
  await saveLabels('numbers');
  const copies = [shown.pet_labels, PROJ.own.pet_labels, S.data.project.pet_labels, TH.project.pet_labels];
  const now = pair.map((b) => [b.on, b.checked]);
  at = { id: 'demo', demo: true };
  drawLabels(at);
  const demo = pair.map((b) => [b.on, b.disabled]);
  await saveLabels('numbers');
  console.log(JSON.stringify({ first, sent, copies, now, demo }));
})();
""", encoding="utf-8")
        run = subprocess.run([node, str(script)], capture_output=True, text=True, encoding="utf-8")
        if run.returncode != 0:
            check("93: Settings' pair runs in node", False, run.stderr.strip()[:300])
        else:
            out = support.plain(json.loads(run.stdout))
            check("93: in node, Settings' pair saves pet_labels for the project shown by its id at once, every copy the page holds "
                  "taking it, the PETs screen's among them, and the demo's fixed",
                  out["first"] == [[True, False], [False, False]]
                  and out["sent"] == [["/api/project", {"root": "bees", "pet_labels": "numbers"}]]
                  and out["copies"] == ["numbers"] * 4 and out["now"] == [[False, "false"], [True, "true"]]
                  and out["demo"] == [[True, True], [False, True]], str(out)[:300])
