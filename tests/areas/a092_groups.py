from __future__ import annotations

import json
import re
import shutil

from . import support
from .support import DEMO_QUESTION, check, demo_copy, skip
import idiograph_routes
import idiograph_cli


def test_groups(scratch):
    print("\n92. Groups: a label inside a sub-theme a group, groups inside groups at any depth, numbered PET 1, "
          "PET 1a, 1a.1 and on in Word, print and the PET draft from one function, Not placed (n) and Discarded (n), "
          "board new with groups, board current, and groups riding inside their sub-theme's card on GETs (207)")
    import html
    import subprocess
    import xml.etree.ElementTree as ET
    import zipfile
    from datetime import datetime
    import cli
    import gets as gets_mod
    import mcp_server
    import server as server_mod
    import themes as themes_mod
    import themes_ai
    import themes_print
    import themes_word

    js = support.text("apps/idiograph/static/themes.js")
    pristine = support.DEMO_PRISTINE
    W = themes_word.W
    tag = lambda name: f"{{{W}}}{name}"

    # ── A. the names, by a label's depth, on the server
    check("92: a label is named by its depth, a PET, a sub-theme, a group, and a group inside a group a group too",
          [themes_mod.layer(d) for d in range(6)] == ["PET", "sub-theme", "group", "group", "group", "group"])
    check("92: a count names the labels a label holds by its own depth, sub-themes under a PET and groups under the rest",
          themes_mod.count_text(7, 2) == "2 sub-themes · 7 statements" and themes_mod.count_text(7, 2, 1) == "2 groups · 7 statements"
          and themes_mod.count_text(3, 1, 2) == "1 group · 3 statements" and themes_mod.count_text(4, 0, 3) == "4 statements"
          and themes_mod.count_text(1, 1, 0) == "1 sub-theme · 1 statement")

    # ── B. the fixture: an invented case on the demo's words, a board five labels deep, as an agent's board
    # apply made some, a second PET with a sub-theme, two discards and the rest not placed
    root = scratch / "groups-root"
    shutil.rmtree(root, ignore_errors=True)
    folder = root / "P{} - {}-{}".format(8, "Linden", "Testname")
    book = demo_copy(folder, "P8 Linden - EN & ES.xlsx")
    read = themes_mod.read_cards(book)
    k = [c["key"] for c in read["cards"]]
    board = themes_mod.blank_version(read["cards"])
    for key, (x, y) in {k[0]: (0, 100), k[1]: (0, 300), k[2]: (0, 500), k[3]: (0, 700), k[4]: (0, 900),
                        k[5]: (0, 1300), k[6]: (2000, 100), k[7]: (2000, 300)}.items():
        board["cards"][key].update(x=x, y=y)
    deep = [
        {"id": "g1", "label": "Home before the town wakes", "note": "An invented note on the PET.",
         "members": [k[0], "g2", "g6"], "x": 0, "y": 40},
        {"id": "g2", "label": "Mornings on the stair", "members": [k[1], "g3"], "x": 0, "y": 240},
        {"id": "g3", "label": "Early light", "members": [k[2], "g4"], "x": 0, "y": 440},
        {"id": "g4", "label": "The first sound", "note": "An invented note on a group inside a group.",
         "members": [k[3], "g5"], "x": 0, "y": 640},
        {"id": "g5", "label": "The fifth step", "members": [k[4]], "x": 0, "y": 840},
        {"id": "g6", "label": "Evenings in", "members": [k[5]], "x": 0, "y": 1240},
        {"id": "g7", "label": "A walk that closes the day", "members": [k[6], "g8"], "x": 2000, "y": 40},
        {"id": "g8", "label": "The long way round", "members": [k[7]], "x": 2000, "y": 240}]
    board["groups"] = json.loads(json.dumps(deep))
    board["discarded"] = [k[8], k[9]]
    themes_mod.save(book, board, "P8 - Linden")
    stored = themes_mod.themes_path(book).read_bytes()
    left = len(k) - 10
    outline = themes_word.board_of(book)[0]
    # this area keeps to the numbers, a project's setting since 208, and area 93 takes the book's letters
    numbers = themes_mod.pet_numbers(outline["themes"], "numbers")
    check("92: one function numbers every layer, PET 1, PET 1a, 1a.1, 1a.1.1 and 1a.1.1.1, each counted in canvas order",
          numbers == {"g1": "PET 1", "g2": "PET 1a", "g3": "1a.1", "g4": "1a.1.1", "g5": "1a.1.1.1", "g6": "PET 1b",
                      "g7": "PET 2", "g8": "PET 2a"}
          and themes_mod.numbered("PET 1a", "Mornings") == "PET 1a. Mornings" and themes_mod.numbered("1a.1", "Early light") == "1a.1 Early light",
          str(numbers))

    # ── C. Word: a heading a level down for each layer, stopping at Heading 5
    made = themes_word.write(book, "P8 - Linden", now=datetime(2026, 10, 6, 21, 0).astimezone(), labels="numbers", unplaced=True, binned=True)
    with zipfile.ZipFile(folder / made["name"]) as z:
        parts = {n: z.read(n).decode("utf-8") for n in z.namelist()}
    doc = []
    for p in ET.fromstring(parts["word/document.xml"]).iter(tag("p")):
        style = p.find(f"{tag('pPr')}/{tag('pStyle')}")
        runs = [{k_: r.find(f"{tag('rPr')}/{tag(k_)}") is not None for k_ in ("b", "i", "caps")} for r in p.iter(tag("r"))]
        doc.append((style.get(tag("val")) if style is not None else "Normal",
                    "".join(t.text or "" for t in p.iter(tag("t"))), [(r["b"], r["i"], r["caps"]) for r in runs]))
    heads = [(s, t, f) for s, t, f in doc if s.startswith("Heading") and s != "Heading1"]
    check("92: Word numbers PET 1 under Heading 2 in bold capitals, PET 1a under Heading 3 in bold, 1a.1 under Heading 4 "
          "in bold italic, a group inside a group under Heading 5 and anything deeper staying at Heading 5",
          heads == [("Heading2", "PET 1. Home before the town wakes", [(True, False, True)]),
                    ("Heading3", "PET 1a. Mornings on the stair", [(True, False, False)]),
                    ("Heading4", "1a.1 Early light", [(True, True, False)]),
                    ("Heading5", "1a.1.1 The first sound", [(True, True, False)]),
                    ("Heading5", "1a.1.1.1 The fifth step", [(True, True, False)]),
                    ("Heading3", "PET 1b. Evenings in", [(True, False, False)]),
                    ("Heading2", "PET 2. A walk that closes the day", [(True, False, True)]),
                    ("Heading3", "PET 2a. The long way round", [(True, False, False)]),
                    ("Heading2", f"Not placed ({left})", [(False, False, False)]),
                    ("Heading2", "Experiential statements set aside (2)", [(False, False, False)])], str(heads))
    styles = parts["word/styles.xml"]
    check("92: Heading 5 is in the styles, bold italic at the body's size like Heading 4, and no Heading 6",
          'w:styleId="Heading5"' in styles and "Heading6" not in styles + parts["word/document.xml"]
          and '<w:i/><w:iCs/>' in styles.split('w:styleId="Heading5"', 1)[1].split("</w:style>", 1)[0]
          and '<w:sz w:val="22"/>' in styles.split('w:styleId="Heading5"', 1)[1].split("</w:style>", 1)[0]
          and themes_word.HEADING_SIZES[4] == themes_word.HEADING_SIZES[3])
    texts = [t for _s, t, _f in doc]
    check("92: every statement under every layer is in the Word document, the note of a group inside a group in italics under it",
          all(any(t.startswith(read_text) for t in texts) for read_text in (c["text"] for c in read["cards"]))
          and texts[texts.index("1a.1.1 The first sound") + 1] == "An invented note on a group inside a group."
          and made["counts"]["statements"] == 8 and made["counts"]["not_placed"] == left and made["counts"]["discarded"] == 2)

    # ── D. print: the same numbers, the steps stopping at the fifth
    page = themes_print.page(book, "P8 - Linden", auto=False, labels="numbers", unplaced=True, binned=True)
    main = page.split("<main>", 1)[1].split("</main>", 1)[0]
    shown = [html.unescape(re.sub(r"<[^>]+>", "", m.group(0))).strip() for m in re.finditer(r"<h[2-6][^>]*>.*?</h[2-6]>", main)]
    check("92: the print view numbers every layer as Word does, its headings h2 to h5 and no further",
          shown == [f"{n} {t}" if not n.startswith("PET ") else f"{n}. {t}" for n, t in (
              ("PET 1", "Home before the town wakes"), ("PET 1a", "Mornings on the stair"), ("1a.1", "Early light"),
              ("1a.1.1", "The first sound"), ("1a.1.1.1", "The fifth step"), ("PET 1b", "Evenings in"),
              ("PET 2", "A walk that closes the day"), ("PET 2a", "The long way round"))] + [f"Not placed ({left})", "Experiential statements set aside (2)"]
          and '<h5 class="group-title">1a.1.1 The first sound</h5>' in main and '<h5 class="group-title">1a.1.1.1 The fifth step</h5>' in main
          and "<h6" not in main and '<span class="number">PET 1.</span>' in main, str(shown))

    # ── E. the PET draft: the same numbers, its headings stopping at five
    draft, _v = themes_mod.draft_markdown(book, "P8 - Linden", labels="numbers")
    dheads = [ln for ln in draft.splitlines() if ln.startswith("#")][1:]
    listed = [ln for ln in draft.splitlines() if re.match(r"^ *- (PET \d|\d+[a-z]\.)", ln)]
    check("92: the draft heads each label with its number, a level down for each layer to #####, and counts its lists",
          dheads == ["## PET 1. Home before the town wakes", "### PET 1a. Mornings on the stair", "#### 1a.1 Early light",
                     "##### 1a.1.1 The first sound", "##### 1a.1.1.1 The fifth step", "### PET 1b. Evenings in",
                     "## PET 2. A walk that closes the day", "### PET 2a. The long way round", f"## Not placed ({left})",
                     "## Experiential statements set aside (2)"], " | ".join(dheads))
    check("92: the draft's list at the head names each layer's count by its depth, groups under a sub-theme",
          listed[:5] == ["- PET 1. Home before the town wakes (2 sub-themes · 6 statements)",
                         "  - PET 1a. Mornings on the stair (1 group · 4 statements)",
                         "    - 1a.1 Early light (1 group · 3 statements)",
                         "      - 1a.1.1 The first sound (1 group · 2 statements)",
                         "        - 1a.1.1.1 The fifth step (1 statement)"], " | ".join(listed[:5]))
    word_order = [t for s, t, _f in heads][:-2]
    draft_order = [h.lstrip("#").strip() for h in dheads][:-2]
    print_order = shown[:-2]
    check("92: Word, print and the draft carry the same numbers and titles in the same order",
          word_order == draft_order == print_order and len(word_order) == 8)
    check("92: reading and exporting a board five deep changes nothing in its themes file, every label kept",
          themes_mod.themes_path(book).read_bytes() == stored
          and [(g["id"], g["members"]) for g in themes_mod.load(book)["boards"][0]["groups"]] == [(g["id"], g["members"]) for g in deep]
          and [themes_mod.unit(board, g) for g in ("g1", "g2", "g3", "g4", "g5", "g7", "g8")]
          == ["PET", "sub-theme", "group", "group", "group", "PET", "sub-theme"])
    kept_root = server_mod.ROOT_OVERRIDE
    try:
        server_mod.ROOT_OVERRIDE = str(root)
        opened = idiograph_routes.api_themes({"workbook": str(book)})
    finally:
        server_mod.ROOT_OVERRIDE = kept_root
    check("92: an old board deeper than three layers still opens on the canvas with every label and member",
          sorted((g["id"], tuple(g["members"])) for g in opened["groups"]) == sorted((g["id"], tuple(g["members"])) for g in deep))

    # ── F. a board of two layers reads as before: PET and sub-theme, no group, nothing written
    two = scratch / "groups-two"
    shutil.rmtree(two, ignore_errors=True)
    book2 = demo_copy(two, "Juno", "Juno - EN & ES.xlsx")
    read2 = themes_mod.read_cards(book2)
    k2 = [c["key"] for c in read2["cards"]]
    b2 = themes_mod.blank_version(read2["cards"])
    b2["groups"] = [{"id": "g1", "label": "Mornings", "members": [k2[0], "g2"], "x": 0, "y": 0},
                    {"id": "g2", "label": "The stair", "members": [k2[1], k2[2]], "x": 0, "y": 200}]
    themes_mod.save(book2, b2, "Juno")
    held2 = themes_mod.themes_path(book2).read_bytes()
    o2 = themes_word.board_of(book2)[0]
    w2 = [(p["style"], themes_word.plain([p])[0]) for p in themes_word.blocks("Juno", o2, "numbers", unplaced=True, binned=True) if p["style"] in (2, 3, 4, 5)]
    check("92: a two-layer board is unchanged, a PET and its sub-theme numbered PET 1 and PET 1a, no group anywhere",
          w2[:2] == [(2, "PET 1. MORNINGS"), (3, "PET 1a. The stair")] and not any(s in (4, 5) for s, _t in w2)
          and o2["themes"][0]["count"] == "1 sub-theme · 3 statements" and o2["themes"][0]["themes"][0]["count"] == "2 statements"
          and themes_mod.themes_path(book2).read_bytes() == held2
          and "#### " not in themes_mod.draft_markdown(book2, "Juno")[0])

    # ── G. the canvas, in node: the names, the counts, a drop into a sub-theme and into a group (the Merge's own line went
    # on 18 October, when a drop merges only on a title strip and the strip says "Merge into" and the title, area 188)
    node = shutil.which("node")
    if not node:
        skip("92: the canvas's names and drops in node", "no node on this machine")
    else:
        script = scratch / "groups-check.js"
        script.write_text(support.i18n_js() + js + r"""
const card = (x, y) => ({ x, y, text: 't', sheet: 'S', row: 1, line: 0 });
const v = { cards: {}, groups: [], discarded: [], picks: {} };
for (let i = 1; i <= 8; i += 1) v.cards[`S:${i}:0`] = card(0, i * 100);
const pet = thMakeGroup(v, ['S:1:0', 'S:2:0', 'S:3:0', 'S:4:0', 'S:5:0'], 'Home');
const sub = thMakeGroup(v, ['S:2:0', 'S:3:0', 'S:4:0', 'S:5:0'], 'Mornings');
const grp = thMakeGroup(v, ['S:3:0', 'S:4:0', 'S:5:0'], 'Early light');
const deep = thMakeGroup(v, ['S:4:0', 'S:5:0'], 'First sound');
const one = thMakeGroup(v, ['S:6:0'], 'Evenings');
const two = thMakeGroup(v, ['S:7:0'], 'Late');
const three = thMakeGroup(v, ['S:8:0'], 'Walks');
const intoSub = thDrop(v, new Set([one]), null, sub).joined;
const intoGroup = thDrop(v, new Set([two]), null, deep).joined;
const parents = thParents(v);
TH.gets = { cases: [{ in: true, none: false, pets: [{ id: 'g1', parent: null }, { id: 'g2', parent: 'g1' },
  { id: 'g3', parent: 'g2' }, { id: 'g4', parent: 'g3' }, { id: 'g5', parent: 'g1' }] }] };
console.log(JSON.stringify({
  units: [pet, sub, grp, deep, one, two, three].map((id) => thUnit(v, id)),
  heads: [pet, sub, grp].map((id) => thUnitHead(thUnit(v, id))),
  counts: [pet, sub, grp, deep].map((id) => thCountText(v, id)),
  intoSub, intoGroup, up: [parents[one] === sub, parents[two] === deep, thAncestors(v, two).length],
  menus: ['S:2:0', 'S:5:0', 'S:7:0'].map((key) => thMenuItems(v, { kind: 'card', id: key }).map((i) => i.label)),
  ai: gtAiCount(true),
}));
""", encoding="utf-8")
        run = subprocess.run([node, str(script)], capture_output=True, text=True, encoding="utf-8")
        if run.returncode != 0:
            check("92: the canvas model runs in node", False, run.stderr.strip()[:300])
        else:
            out = json.loads(run.stdout)
            check("92: in node, a PET at the top, a sub-theme inside it, and a group inside a sub-theme or a group, at any depth",
                  out["units"] == ["PET", "sub-theme", "group", "group", "group", "group", "PET"]
                  and out["heads"] == ["PET", "Sub-theme", "Group"], str(out["units"]))
            check("92: in node, the counts name sub-themes under a PET and groups under a sub-theme or a group",
                  out["counts"] == ["1 sub-theme · 7 statements", "2 groups · 6 statements", "1 group · 4 statements",
                                    "1 group · 3 statements"], str(out["counts"]))
            check("92: in node, a label dropped into a sub-theme becomes a group, and one dropped into a group a group inside it, refused nowhere",
                  out["intoSub"] == ["g5"] and out["intoGroup"] == ["g6"] and out["up"] == [True, True, 4], str(out))
            check("92: in node, Take out of sub-theme for a card a sub-theme holds and Take out of group for one a group holds, "
                  "Ungroup too for the card that is the whole of its group (20 October)",
                  out["menus"] == [["Inspect", "Go to the passage", "Group", "Take out of sub-theme", "Set aside"],
                                   ["Inspect", "Go to the passage", "Group", "Take out of group", "Set aside"],
                                   ["Inspect", "Go to the passage", "Group", "Ungroup", "Take out of group", "Set aside"]], str(out["menus"]))
            check("92: in node, New AI board on GETs counts the PETs and sub-themes it sends, a sub-theme's groups riding inside it",
                  out["ai"] == {"pets": 1, "subs": 2}, str(out["ai"]))

    # ── H. the command line and MCP: board new with groups at any depth, board current, an apply keeping groups
    proj = scratch / "groups-cli-root"
    shutil.rmtree(proj, ignore_errors=True)
    for name in ("Juno", "Rowan"):
        case = proj / name
        (case / "Working").mkdir(parents=True)
        shutil.copy2(pristine / f"{name} - EN & ES.xlsx", case / f"{name} - EN & ES.xlsx")
        for side in (pristine / "Working").glob(f"{name} - *"):
            shutil.copy2(side, case / "Working" / side.name)
    (proj / "idiograph-project.json").write_text(json.dumps(
        {"name": "Dogs, a scratch project", "research_question": DEMO_QUESTION,
         "agents": {"allowed": True, "at": "2026-10-06T10:00:00+01:00"}}), encoding="utf-8")
    config_file = scratch / "groups-cli-config.json"
    config_file.write_text(json.dumps({"root": str(proj), "interviewer": "Adam"}), encoding="utf-8")
    juno = proj / "Juno" / "Juno - EN & ES.xlsx"
    side = themes_mod.themes_path(juno)
    rj = themes_mod.read_cards(juno)
    sids = themes_mod.short_ids(rj["cards"])
    keyed = {v: k_ for k_, v in sids.items()}
    quoted = {q["key"] for row in rj["quotes"].values() for q in row["quotes"]}
    with_quote = [sids[c["key"]] for c in rj["cards"] if c["key"] in quoted]
    rest = [sids[c["key"]] for c in rj["cards"] if c["key"] not in quoted]
    ids = with_quote + rest
    spec = {"pets": [{"title": "Mornings arranged round the dog", "note": "An invented reason for the PET.",
                      "members": [ids[0]],
                      "subs": [{"title": "The stair before light", "members": [ids[1]],
                                "groups": [{"title": "Listening for the first sound", "members": [ids[2]],
                                            "picks": [keyed[ids[2]]] if ids[2] in with_quote else [],
                                            "groups": [{"title": "The fifth step", "members": [ids[3]],
                                                        "groups": [{"title": "A sound she knows", "members": [ids[4]]}]}]},
                                           {"title": "The hall still dark", "members": [ids[5]]}]}]},
                     {"title": "Walks that close the day", "members": [ids[6], ids[7]]}],
            "not_placed": {i: "An invented reason it fits no PET" for i in ids[8:]}}

    def put(name: str, value) -> str:
        path = scratch / f"groups-{name}.json"
        path.write_text(json.dumps(value), encoding="utf-8")
        return str(path)

    saved = (server_mod.CONFIG_PATH, server_mod.ROOT_OVERRIDE, server_mod.STATE_MEMORY)
    try:
        server_mod.CONFIG_PATH = config_file
        server_mod.ROOT_OVERRIDE = str(proj)
        server_mod.STATE_MEMORY = {"recent": []}
        cmd = lambda *a: cli.run(["--root", str(proj), "--config", str(config_file), *a])
        before = side.read_bytes() if side.exists() else None
        code, out, err = cmd("board", "new", "Juno", "--from", put("spec", spec), "--dry-run")
        check("92: board new takes groups inside a sub-theme and inside a group, and its dry run writes nothing",
              code == 0 and out.startswith("Dry run, nothing was written.") and "8 statements placed" in out
              and (side.read_bytes() if side.exists() else None) == before, (out + err)[:300])
        code, out, err = cmd("board", "new", "Juno", "--from", put("spec", spec), "--note", "A board with groups", "--tool", "Claude Code", "--json")
        made_board = json.loads(out) if code == 0 else {}
        data = themes_mod.load(juno)
        nb = themes_mod.find_version(data, made_board.get("id")) or {"groups": []}
        by_label = {g["label"]: g for g in nb["groups"]}
        ol = themes_mod.outline(rj, nb) if nb["groups"] else {"themes": []}
        sub_titles = [t["label"] for t in ol["themes"][0]["themes"][0]["themes"]] if ol["themes"] else []
        num = themes_mod.pet_numbers(ol["themes"], "numbers")
        check("92: the board made nests each group inside its sub-theme or its group, a statement once, as given",
              code == 0 and themes_mod.unit(nb, by_label["The stair before light"]["id"]) == "sub-theme"
              and all(themes_mod.unit(nb, by_label[t]["id"]) == "group"
                      for t in ("Listening for the first sound", "The fifth step", "A sound she knows", "The hall still dark"))
              and by_label["The fifth step"]["id"] in by_label["Listening for the first sound"]["members"]
              and by_label["A sound she knows"]["id"] in by_label["The fifth step"]["members"]
              and by_label["The fifth step"]["members"][0] == keyed[ids[3]]
              and keyed[ids[2]] in by_label["Listening for the first sound"]["members"]
              and keyed[ids[2]] not in by_label["The stair before light"]["members"], (out + err)[:300])
        check("92: the canvas order follows the order given, the PETs and the groups inside a sub-theme alike",
              [t["label"] for t in ol["themes"]] == ["Mornings arranged round the dog", "Walks that close the day"]
              and sub_titles == ["Listening for the first sound", "The hall still dark"]
              and sorted(num.values()) == sorted(["PET 1", "PET 1a", "1a.1", "1a.1.1", "1a.1.1.1", "1a.2", "PET 2"]), str(sub_titles))
        check("92: a pick on a group lands on it, and the layout lays no card over another",
              (nb.get("picks") or {}).get(by_label["Listening for the first sound"]["id"]) == ([keyed[ids[2]]] if ids[2] in with_quote else None)
              and not [1 for i, a in enumerate(list(themes_mod.layout_boxes(nb)["cards"].values()))
                       for b in list(themes_mod.layout_boxes(nb)["cards"].values())[i + 1:] if themes_mod.clash(a, b)])
        wrong = {"pets": [{"title": "A", "members": [ids[0]], "groups": [{"title": "B", "members": [ids[1]]}],
                           "subs": [{"title": "C", "members": [ids[2]], "subs": [{"title": "D", "members": [ids[3]]}],
                                     "groups": [{"title": "E", "members": [ids[2], ids[4]]}]}]}]}
        held = side.read_bytes()
        code, out, err = cmd("board", "new", "Juno", "--from", put("wrong", wrong), "--note", "A wrong board")
        check("92: a PET carrying groups, a sub-theme carrying sub-themes and a statement in a group and its sub-theme are refused, nothing written",
              code == 1 and "'A' is a PET, and a PET holds statements and sub-themes, and a group goes inside a sub-theme." in err
              and "'C' is a sub-theme, and a sub-theme holds statements and groups, not sub-themes." in err
              and f"{ids[2]} {keyed[ids[2]]} is placed twice, in 'C' and in 'E'." in err and side.read_bytes() == held, err[:400])

        # board current, its dry run, its record in History. A case with no themes file takes the first
        # board made as its only one (95), so a second board, empty, is the one to mark, the made board
        # left on the canvas
        themes_mod.version_op(juno, "new", {}, "Juno")
        themes_mod.version_op(juno, "switch", {"id": made_board.get("id")}, "Juno")
        bid = made_board.get("id")
        others = [b for b in themes_mod.boards_of(themes_mod.load(juno)) if b.get("id") != bid]
        target = others[0] if others else None
        tname = target.get("name") if target else ""
        held = side.read_bytes()
        code, out, err = cmd("board", "current", "Juno", tname, "--dry-run")
        check("92: board current's dry run says what it would mark and writes nothing",
              code == 0 and out.startswith(f"Dry run, nothing was written. It would mark {tname} as the Current board on Juno")
              and side.read_bytes() == held, out + err)
        code, out, err = cmd("board", "current", "Juno", tname)
        check("92: board current needs his request, as every write does", code == 1 and err.strip() == idiograph_cli.NO_REQUEST and side.read_bytes() == held)
        code, out, err = cmd("board", "current", "Juno", tname, "--note", "Go with this one for now", "--tool", "Claude Code", "--json")
        answer = json.loads(out) if code == 0 else {}
        data = themes_mod.load(juno)
        marked = themes_mod.find_version(data, target.get("id")) if target else {}
        last = themes_mod.history_of(marked)[-1] if marked and themes_mod.history_of(marked) else {}
        check("92: board current marks the Current board through choose, and records it in that board's History with who and why",
              code == 0 and themes_mod.chosen_of(data) == target.get("id") and answer.get("changed") is True
              and last.get("name") == "Marked the Current board: Go with this one for now"
              and (last.get("made") or {}).get("tool") == "Claude Code" and (last.get("made") or {}).get("request") == "Go with this one for now"
              and themes_mod.current_version(data)["id"] == made_board.get("id"), out + err)
        held = side.read_bytes()
        code, out, err = cmd("board", "current", "Juno", tname, "--note", "Again")
        check("92: a board marked already writes nothing, and the file still validates",
              code == 0 and out.strip() == f"{tname} is the Current board already. Nothing was written." and side.read_bytes() == held
              and cmd("validate")[0] == 0, out + err)

        # MCP: board_current, and board_new with groups
        srv = mcp_server.Server(str(proj), config=str(config_file))
        srv.receive(json.dumps({"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {"protocolVersion": "2025-06-18",
                                                                                                "clientInfo": {"name": "claude-ai"}}}))
        listed = {t["name"]: t for t in srv.receive(json.dumps({"jsonrpc": "2.0", "id": 2, "method": "tools/list"}))["result"]["tools"]}
        call = lambda name, args: srv.receive(json.dumps({"jsonrpc": "2.0", "id": 3, "method": "tools/call",
                                                         "params": {"name": name, "arguments": args}}))["result"]
        cur = listed.get("board_current") or {}
        check("92: MCP offers board_current, case, board and his request, marking a board and changing nothing on it",
              cur and cur["inputSchema"]["required"] == ["case", "board", "request"] and "dry_run" in cur["inputSchema"]["properties"]
              and cur["annotations"]["destructiveHint"] is False
              and "groups" in json.dumps(listed["board_new"]["inputSchema"]))
        held = side.read_bytes()
        res = call("board_new", {"case": "Juno", "pets": spec["pets"], "not_placed": spec["not_placed"],
                                 "request": "A board with groups", "dry_run": True})
        res2 = call("board_current", {"case": "Juno", "board": made_board.get("name") or "", "request": "Go with the new one", "dry_run": True})
        check("92: through MCP, board_new takes groups at any depth and board_current its dry run, neither writing",
              res["isError"] is False and res["structuredContent"]["dry_run"] is True
              and res2["isError"] is False and res2["structuredContent"]["dry_run"] is True
              and "It would mark" in res2["content"][0]["text"] and side.read_bytes() == held, str(res2)[:300])
        res3 = call("board_current", {"case": "Juno", "board": made_board.get("name") or "", "request": "Go with the new one"})
        data = themes_mod.load(juno)
        check("92: board_current through MCP marks the board, its History naming the client",
              res3["isError"] is False and themes_mod.chosen_of(data) == made_board.get("id")
              and themes_mod.history_of(themes_mod.find_version(data, made_board.get("id")))[-1]["made"]["tool"] == "Claude Desktop")

        # an apply on a board with groups keeps every group he made
        ops = {"operations": [{"op": "retitle", "label": "g1", "title": "Mornings the dog arranges"},
                              {"op": "move", "items": [ids[8]], "to": by_label["The fifth step"]["id"]}]}
        code, out, err = cmd("board", "apply", "Juno", made_board.get("id"), "--ops", put("ops", ops), "--note", "Retitle and move one in",
                             "--tool", "Claude Code")
        after = themes_mod.find_version(themes_mod.load(juno), made_board.get("id"))
        ab = {g["id"]: g for g in after["groups"]}
        check("92: board apply on a board with groups keeps every group, its members and its depth, and lands the change",
              code == 0 and all(g["id"] in ab for g in nb["groups"])
              and all([m for m in ab[g["id"]]["members"] if m != keyed[ids[8]]] == g["members"] for g in nb["groups"])
              and keyed[ids[8]] in ab[by_label["The fifth step"]["id"]]["members"]
              and ab["g1"]["label"] == "Mornings the dog arranges"
              and themes_mod.unit(after, by_label["A sound she knows"]["id"]) == "group", (out + err)[:300])
        start = themes_ai.revise_start(rj, themes_mod.follow(after, rj["cards"], rj["quotes"]))
        revised, applied, refused_ops, _info = themes_ai.revise_ops(start, [{"op": "retitle", "label": "g2", "title": "An invented title"}])
        check("92: an AI revise that touches none of his groups keeps every one as it stood",
              not refused_ops and {g["id"]: g["members"] for g in revised["groups"]} == {g["id"]: g["members"] for g in start["groups"]})
    finally:
        server_mod.CONFIG_PATH, server_mod.ROOT_OVERRIDE, server_mod.STATE_MEMORY = saved

    # ── I. GETs: a case's groups ride inside their sub-theme's card, through opening, New board, Take, lay_in and
    # Add every sub-theme
    groot = scratch / "groups-gets-root"
    shutil.rmtree(groot, ignore_errors=True)
    case = groot / "Rowan"
    (case / "Working").mkdir(parents=True)
    shutil.copy2(pristine / "Rowan - EN & ES.xlsx", case / "Rowan - EN & ES.xlsx")
    for side_file in (pristine / "Working").glob("Rowan - *"):
        shutil.copy2(side_file, case / "Working" / side_file.name)
    wren = demo_copy(groot, "Wren", "Wren - EN & ES.xlsx")
    wk = [c["key"] for c in themes_mod.read_cards(wren)["cards"]]

    def wren_file(groups):
        b = themes_mod.blank_version(themes_mod.read_cards(wren)["cards"])
        b.update(id="v1", name="Board 1", groups=groups)
        themes_mod.write(wren, {"schema": 2, "case": "Wren", "workbook": wren.name, "current": "v1", "chosen": "v1", "boards": [b]})

    nest = [{"id": "g1", "label": "Mornings that start at the stair", "members": [wk[0], "g2"], "x": 0, "y": 0},
            {"id": "g2", "label": "Early light in the hall", "members": [wk[1], "g3"], "x": 0, "y": 250},
            {"id": "g3", "label": "The first sound", "members": [wk[2], "g4"], "x": 0, "y": 450},
            {"id": "g4", "label": "The fifth step", "members": [wk[3]], "x": 0, "y": 650},
            {"id": "g5", "label": "Walks that close the day", "members": wk[4:6], "x": 0, "y": 900}]
    wren_file(nest)
    (groot / "idiograph-project.json").write_text(json.dumps({"name": "Dogs, a scratch project", "research_question": DEMO_QUESTION}),
                                                  encoding="utf-8")
    gconfig = scratch / "groups-gets-config.json"
    gconfig.write_text(json.dumps({"root": str(groot), "interviewer": "Adam"}), encoding="utf-8")
    gfile = gets_mod.gets_path(groot)

    def overlaps(b, data):
        drawn = themes_mod.layout_boxes(gets_mod.named(gets_mod.normal(b, data), data), gets_mod.card_height)
        boxes = list(drawn["cards"].items())
        return [(x, y) for i, (x, bx) in enumerate(boxes) for y, by in boxes[i + 1:] if themes_mod.clash(bx, by)]

    saved = (server_mod.CONFIG_PATH, server_mod.ROOT_OVERRIDE, server_mod.STATE_MEMORY)
    try:
        server_mod.CONFIG_PATH = gconfig
        server_mod.ROOT_OVERRIDE = str(groot)
        server_mod.STATE_MEMORY = {"recent": []}
        shown = idiograph_routes.api_gets({"workbook": str(wren)})
        cards = {c["key"]: c for c in shown["cards"]}
        wrec = {c["case"]: c for c in shown["cases"]}["Wren"]
        check("92: on GETs a PET and a sub-theme each have a card, and the groups at any depth ride inside the sub-theme's",
              {k_ for k_ in cards if k_.startswith("Wren/")} == {"Wren/g1", "Wren/g2", "Wren/g5"}
              and cards["Wren/g2"]["statements"] == 3 and cards["Wren/g1"]["statements"] == 4
              and {p["id"] for p in wrec["pets"]} == {"g1", "g2", "g3", "g4", "g5"}
              and gets_mod.depths({"pets": wrec["pets"]}) == {"g1": 0, "g2": 1, "g3": 2, "g4": 3, "g5": 0}, str(sorted(cards)))
        rec = {"pets": wrec["pets"]}
        check("92: cards_of and subs_of give no group a card of its own",
              [k_ for k_, _t in gets_mod.cards_of("Wren", rec)] == ["Wren/g1", "Wren/g2", "Wren/g5"]
              and [k_ for k_, _t in gets_mod.subs_of("Wren", rec)] == ["Wren/g2"])
        body = dict(shown["version"], cards={k_: {"x": c["x"], "y": c["y"]} for k_, c in cards.items()},
                    groups=[], discarded=[], picks={}, notes=[])
        idiograph_routes.api_gets_save({"workbook": str(wren), "version": body})
        newb = idiograph_routes.api_gets_ops({"workbook": str(wren), "op": "new"})
        check("92: New board lays every PET and sub-theme in the pile and no group",
              {c["key"] for c in newb["cards"] if c["key"].startswith("Wren/")} == {"Wren/g1", "Wren/g2", "Wren/g5"})
        held = json.loads(gfile.read_text(encoding="utf-8"))
        study = gets_mod.ai_study(held, [{"case": "Wren", "status": "in"}, {"case": "Rowan", "status": "in"}])
        wpets = {p["key"]: p for p in next(e for e in study if e["case"] == "Wren")["pets"]}
        sub_item = wpets["Wren/g1"]["subs"][0]
        check("92: New AI board sends a sub-theme as one item, its groups' statements riding inside it after its own",
              sub_item["key"] == "Wren/g2" and sub_item["subs"] == []
              and [s["key"] for s in sub_item["statements"]] == [f"Wren/es/{wk[1]}", f"Wren/es/{wk[2]}", f"Wren/es/{wk[3]}"]
              and [s["key"] for s in wpets["Wren/g1"]["statements"]] == [f"Wren/es/{wk[0]}"])
        # a group and a sub-theme new to the case, then Take
        nest2 = json.loads(json.dumps(nest))
        nest2[1]["members"].append("g6")
        nest2[0]["members"].append("g7")
        nest2 += [{"id": "g6", "label": "A new group in the hall", "members": [wk[6]], "x": 0, "y": 1100},
                  {"id": "g7", "label": "A new sub-theme", "members": [wk[7]], "x": 0, "y": 1300}]
        wren_file(nest2)
        took = idiograph_routes.api_gets_cases({"workbook": str(wren), "op": "take", "case": "Wren"})
        held = json.loads(gfile.read_text(encoding="utf-8"))
        check("92: Take brings the new sub-theme in, clear of the rest, and the new group rides inside its sub-theme's card",
              took["op"] == "take" and all("Wren/g7" in b["cards"] and "Wren/g6" not in b["cards"] for b in held["boards"])
              and not any(overlaps(b, held) for b in held["boards"]))
        # lay_in on a board with no card of Wren's, and Add every sub-theme on it
        bare = gets_mod.blank_board(held, "b9", "Board 9", themes_mod.now_iso())
        bare["cards"] = {k_: c for k_, c in bare["cards"].items() if not k_.startswith("Wren/")}
        gets_mod.lay_in(bare, gets_mod.cards_of("Wren", held["cases"]["Wren"]), held)
        check("92: lay_in sets a case's PET and sub-theme cards clear of everything, no group among them",
              {k_ for k_ in bare["cards"] if k_.startswith("Wren/")} == {"Wren/g1", "Wren/g2", "Wren/g5", "Wren/g7"}
              and not overlaps(bare, held))
        bare["cards"] = {k_: c for k_, c in bare["cards"].items() if k_ not in ("Wren/g2", "Wren/g7")}
        held["boards"].append(bare)
        gets_mod.write(groot, held)
        res = idiograph_routes.api_gets_boards({"workbook": str(wren), "op": "subs", "id": "b9"})
        added = {c["key"] for c in res["added"]}
        check("92: Add every sub-theme adds the sub-themes a board lacks and never a group",
              {"Wren/g2", "Wren/g7"} <= added and not {"Wren/g3", "Wren/g4", "Wren/g6"} & added, str(sorted(added)))
    finally:
        server_mod.CONFIG_PATH, server_mod.ROOT_OVERRIDE, server_mod.STATE_MEMORY = saved
