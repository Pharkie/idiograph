from __future__ import annotations

import json
import shutil

import ai_suggest as ai_mod

from . import support
from .support import GRAVITY_QUESTION, check, demo_copy, skip
import idiograph_routes


def test_theme_notes(scratch):
    print("\n47. Themes, a note per theme: the file, the board ops, the draft, the print view and the AI")
    import html
    import subprocess
    import server as server_mod
    import themes as themes_mod
    import themes_ai
    import themes_print

    root = scratch / "notes-root"
    work = demo_copy(root, "Juno", "Juno - EN & ES.xlsx")
    (root / "idiograph-project.json").write_text(json.dumps(
        {"name": "Scratch", "research_question": GRAVITY_QUESTION}), encoding="utf-8")
    path = themes_mod.themes_path(work)
    read = themes_mod.read_cards(work)
    k = [c["key"] for c in read["cards"]]
    texts = {c["key"]: c["text"] for c in read["cards"]}
    WHY = "Mornings are the dog's before they are hers.\nThe walk comes first, and the day after it."
    WHY_LINE = " ".join(WHY.split())
    SUB = "The walks she takes alone, apart from the house."

    def file():
        return json.loads(path.read_text(encoding="utf-8"))

    def board(bid):
        return next(b for b in file()["boards"] if b["id"] == bid)

    def notes_of(groups):
        return {g.get("id", g.get("label")): g.get("note") for g in groups}

    # ── A. the file: a note beside the id, the label and the members, stripped, and none when blank
    raw = themes_mod.blank_version(read["cards"])
    for key, (x, y) in zip(k, [(0, 0), (0, 100), (0, 400), (0, 500), (900, 0), (1800, 0)]):
        raw["cards"][key].update(x=x, y=y)
    raw["groups"] = [{"id": "g1", "label": "Mornings", "note": f"  {WHY}\n ", "members": [k[0], k[1], "g2"], "x": 0, "y": -40},
                     {"id": "g2", "label": "Walks", "note": SUB, "members": [k[2], k[3]], "x": 0, "y": 360},
                     {"id": "g3", "label": "Blank", "note": "   \n ", "members": [k[4]], "x": 900, "y": -40},
                     {"id": "g4", "label": "Old", "members": [k[5]], "x": 1800, "y": -40}]
    plain = dict(raw, groups=[{key: value for key, value in g.items() if key != "note"} for g in raw["groups"]])
    kept = themes_mod.normalise(raw)
    by = {g["id"]: g for g in kept["groups"]}
    check("normalise keeps a theme's note as a stripped string, beside its id, its label and its members",
          by["g1"]["note"] == WHY and by["g2"]["note"] == SUB
          and list(by["g1"]) == ["id", "label", "note", "members", "x", "y"], str(list(by["g1"])))
    check("a blank note is none, and a group from before the notes reads as it did, the schema still 2",
          "note" not in by["g3"] and "note" not in by["g4"] and themes_mod.SCHEMA == 2
          and themes_mod.normalise(kept) == kept
          and all("note" not in g for g in themes_mod.normalise(plain)["groups"])
          and themes_mod.board_state(plain) == themes_mod.board_state(dict(plain, groups=[dict(g, note="") for g in plain["groups"]])))

    saved_root = server_mod.ROOT_OVERRIDE
    real = (server_mod.CONFIG_PATH, ai_mod.find_key, ai_mod.http_call)
    server_mod.ROOT_OVERRIDE = str(root)
    try:
        opened = idiograph_routes.api_themes({"workbook": str(work)})
        check("/api/themes says a save keeps a theme's note, which a server from before the notes does not",
              opened.get("notes") is True)
        book = work.read_bytes()
        idiograph_routes.api_themes_save({"workbook": str(work), "version": raw})
        check("a save writes each note into the themes file and the workbook is never touched",
              notes_of(board("v1")["groups"]) == {"g1": WHY, "g2": SUB, "g3": None, "g4": None}
              and work.read_bytes() == book)
        shown = idiograph_routes.api_themes({"workbook": str(work)})
        check("the screen's state carries each note back to the page",
              notes_of(shown["groups"]) == {"g1": WHY, "g2": SUB, "g3": None, "g4": None})

        # ── B. it travels with the board
        twin = idiograph_routes.api_themes_versions({"workbook": str(work), "op": "duplicate", "id": "v1"})
        check("Duplicate copies every theme's note with the board",
              twin["current"] == "v2" and notes_of(board("v2")["groups"]) == {"g1": WHY, "g2": SUB, "g3": None, "g4": None})
        idiograph_routes.api_themes_versions({"workbook": str(work), "op": "new"})
        copied = idiograph_routes.api_themes_boards({"workbook": str(work), "op": "copy", "id": "v1", "group": "g1", "to": "v3"})
        check("Copy to board carries the theme's note, and its sub-theme's, onto the fresh labels there",
              copied["copied"]["label"] == "Mornings"
              and {g["label"]: g.get("note") for g in board("v3")["groups"]} == {"Mornings": WHY, "Walks": SUB})
        made = idiograph_routes.api_themes_boards({"workbook": str(work), "op": "revision", "id": "v1", "name": "With notes"})
        rid = made["revision"]["id"]
        idiograph_routes.api_themes_save({"workbook": str(work), "version": dict(plain, groups=[dict(g, note="") for g in plain["groups"]])})
        cleared = notes_of(board("v1")["groups"])
        held = notes_of(next(r for r in board("v1")["history"] if r["id"] == rid)["state"]["groups"])
        restored = idiograph_routes.api_themes_boards({"workbook": str(work), "op": "restore", "id": "v1", "revision": rid})
        check("a revision holds the notes, and Restore brings them back after they were cleared",
              held == {"g1": WHY, "g2": SUB, "g3": None, "g4": None} and set(cleared.values()) == {None}
              and notes_of(board("v1")["groups"]) == held and notes_of(restored["groups"]) == held)

        # ── C. the PET draft, and the CSV
        idiograph_routes.api_themes_export({"workbook": str(work), "version": "v1"})
        draft = themes_mod.draft_path(work, "Board 1").read_text(encoding="utf-8")
        line = lambda key: f"- {texts[key]} ("
        check("the PET draft has a theme's note under its heading as a plain paragraph, before its statements",
              f"## A. Mornings\n\n{WHY}\n\n{line(k[0])}" in draft and draft.index(WHY) < draft.index(line(k[1])))
        check("and a sub-theme's under its own heading, a level down, before its own statements",
              f"### A1. Walks\n\n{SUB}\n\n{line(k[2])}" in draft)
        csv_text = "".join(p.read_text(encoding="utf-8-sig") for p in (work.parent / "Working").glob("*.csv"))
        check("a theme with no note has no paragraph, and the CSV carries no note at all",
              f"## B. Blank\n\n{line(k[4])}" in draft and f"## C. Old\n\n{line(k[5])}" in draft
              and csv_text and "Mornings are the dog" not in csv_text and SUB not in csv_text)

        # ── D. the print view
        page = themes_print.page(work, "Juno", "v1", GRAVITY_QUESTION, auto=False)
        why_html, sub_html = html.escape(WHY, quote=True), html.escape(SUB, quote=True)
        check("the print view sets a theme's note under its title and before its statements (206)",
              f'<span class="title">Mornings</span></h2>\n<p class="tnote">{why_html}</p>\n<div class="item">' in page)
        check("and a sub-theme's under its own title, before its statements (206)",
              f'<h3 class="sub-title">A1. Walks</h3>\n<p class="tnote">{sub_html}</p>\n<div class="item">' in page
              and page.count('<p class="tnote">') == 2)

        # ── E. the outline (the review went on 11 November 2026, aiout)
        outline = themes_mod.outline(read, board("v1"))
        bare = themes_mod.outline(read, plain)
        check("outline carries each theme's note when it has one, a sub-theme's too, and none otherwise",
              outline["themes"][0]["note"] == WHY and outline["themes"][0]["themes"][0]["note"] == SUB
              and all("note" not in t for t in outline["themes"][1:]) and "note" not in bare["themes"][0])
        # ── F. the titles (New AI board went on 11 November 2026, aiout)
        named = themes_ai.names_user(["one", "two"], "Mornings", ["Walks"], WHY)
        check("AI suggest for theme titles sends the label's note, saying in one line what it is",
              f"{themes_ai.NOTE_NAMES} {WHY_LINE}" in named and named.count(themes_ai.NOTE_NAMES) == 1)
        check("and a label with no note sends the titles prompt as it did",
              themes_ai.names_user(["one", "two"], "Mornings", ["Walks"]) == themes_ai.names_user(["one", "two"], "Mornings", ["Walks"], "  \n ")
              and themes_ai.NOTE_NAMES not in themes_ai.names_user(["one", "two"], "Mornings", ["Walks"]))

        # ── G. the routes, through a transport that stands in for the provider
        config_path = scratch / "notes" / "config.json"
        config_path.parent.mkdir(parents=True, exist_ok=True)
        config_path.write_text(json.dumps({"ai_provider": "anthropic", "model": "claude-haiku-4-5", "ai_suggest": True}),
                               encoding="utf-8")
        sent, replies = [], []

        def wire(method, url, headers, payload, timeout):
            sent.append(payload)
            return 200, json.dumps({"content": [{"type": "text", "text": replies[0](payload)}], "stop_reason": "end_turn"})

        server_mod.CONFIG_PATH = config_path
        ai_mod.find_key = lambda *a, **kw: "k-test"
        ai_mod.http_call = wire
        replies[:] = [lambda payload: json.dumps({"names": ["A", "B", "C"]})]
        idiograph_routes.api_themes_ai({"workbook": str(work), "op": "names", "statements": ["one", "two"],
                                  "label": "Mornings", "others": ["Walks"], "note": WHY})
        idiograph_routes.api_themes_ai({"workbook": str(work), "op": "names", "statements": ["one", "two"],
                                  "label": "Mornings", "others": ["Walks"]})
        check("the titles route takes the label's note from the page into the prompt, and none without one",
              f"{themes_ai.NOTE_NAMES} {WHY_LINE}" in sent[0]["messages"][0]["content"]
              and themes_ai.NOTE_NAMES not in sent[1]["messages"][0]["content"])
    finally:
        server_mod.ROOT_OVERRIDE = saved_root
        server_mod.CONFIG_PATH, ai_mod.find_key, ai_mod.http_call = real

    # ── H. the page
    js = support.text("apps/idiograph/static/themes.js")
    fn = lambda src, name: src.split(f"function {name}(", 1)[1].split("\n}", 1)[0]
    box = fn(js, "thNoteHtml")
    keys = js.split("panel.addEventListener('keydown', (e) => {", 1)[1].split("\n  });", 1)[0]
    check("Cmd + Enter keeps it, Esc leaves it as it was, a click away keeps it, and nothing else hears its keys",
          "if (e.key === 'Enter' && MOD(e)) { e.preventDefault(); thNoteDone(true); }" in keys
          and "else if (e.key === 'Escape') { e.preventDefault(); thNoteDone(false); }" in keys
          and keys.index("e.stopPropagation();") < keys.index("thNoteDone(true)")
          and "if (e.target && e.target.id === 'th-gnote' && !TH.noteRedraw) thNoteDone(true);" in js
          and "'.th-title-edit, .th-vedit'" in fn(js, "thKeyDown"))
    done = fn(js, "thNoteDone")
    check("a note kept is one step of undo like a rename, and undo and redo show it in the Inspector, opened when closed (114)",
          "thSetNote(v, ed.id, text)" in done and "thDone(before," in done and "note: ed.id" in done
          and "thStep(before, what, opts.note);" in fn(js, "thDone")
          and "if (noted) thInspectorOpen({ kind: 'group', id: noted });" in fn(js, "thUndo"))
    check("Note in a label's right-click menu opens the Inspector on it with the box taken",
          "else if (choice.act === 'note') thNoteOpen(item.id);" in fn(js, "thMenuDo")
          and "thInspectorOpen({ kind: 'group', id });" in fn(js, "thNoteOpen") and "box.focus();" in fn(js, "thNoteOpen"))
    check("on a revision on view the note shows read-only, and in front of an old server the box says to restart",
          "if (thLocked(v)) return note ?" in box and "th-gnote-read" in box and "esc(RESTART_LINE)" in box
          and "if (!TH.notable)" in box and "TH.notable = !!data.notes;" in fn(js, "themesOpen"))
    check("a save sends a theme's note only when it has one, each label going whole (22 October, 247)",
          "if (thNoteOf(g)) out.note = thNoteOf(g);" in fn(js, "thLabelOut") and "base.groups.map(thLabelOut)" in fn(js, "thBody"))
    check("the Themes screen never writes the workbook: the note rides on the board's own save",
          "/api/themes-note" not in js and "api('/api/themes-save', body)" in fn(js, "thSaveOnce"))

    node = shutil.which("node")
    if not node:
        return skip("the theme notes model in node", "no node on this machine")
    script = scratch / "themes-notes.js"
    script.write_text(support.i18n_js() + js + r"""
const card = (x, y, text) => ({ x, y, text, sheet: 'S', row: 1, line: 0 });
const v = { cards: { 'S:1:0': card(0, 0, 'one'), 'S:2:0': card(0, 100, 'two'), 'S:3:0': card(400, 0, 'three') },
  groups: [], discarded: [], picks: {} };
const g1 = thMakeGroup(v, ['S:1:0', 'S:2:0'], 'Mornings');
const keep = (x) => JSON.parse(JSON.stringify(x));
const out = {};
const before = thSnap(v, []);
out.set = [thSetNote(v, g1, '  Why it holds.\n '), thGroup(v, g1).note, thSetNote(v, g1, 'Why it holds.'), thSetNote(v, 'g9', 'x')];
const after = thSnap(v, []);
out.body = keep(thBody(v, { id: 'v1', name: 'B', note: '' }).groups);
out.names = thNamesBody(v, { kind: 'group', id: g1 });
thPut(v, before);
out.undone = [thNoteOf(thGroup(v, g1)), 'note' in thGroup(v, g1)];
thPut(v, after);
out.redone = thNoteOf(thGroup(v, g1));
const r = keep(v);
r.readonly = true;
out.locked = [thSetNote(r, g1, 'no'), thNoteOf(thGroup(r, g1))];
out.cleared = [thSetNote(v, g1, '   '), 'note' in thGroup(v, g1), keep(thBody(v, { id: 'v1', name: 'B' }).groups[0]),
  thNamesBody(v, { kind: 'group', id: g1 })];
out.menu = [thMenuItems(v, { kind: 'group', id: g1 }).map((i) => i.label), thMenuItems(v, { kind: 'card', id: 'S:3:0' }).map((i) => i.label),
  thMenuItems(r, { kind: 'group', id: g1 }).map((i) => i.label)];
console.log(JSON.stringify(out));
""", encoding="utf-8")
    run = subprocess.run([node, str(script)], capture_output=True, text=True, encoding="utf-8")
    if run.returncode != 0:
        return check("the theme notes model runs in node", False, run.stderr.strip()[:300])
    out = json.loads(run.stdout)
    check("the page keeps a note stripped, and a note the same as before, or on no label, changes nothing",
          out["set"] == [True, "Why it holds.", False, False], str(out["set"]))
    check("a save sends the note beside the id and the label, and the titles go with it",
          out["body"] == [{"id": "g1", "label": "Mornings", "note": "Why it holds.", "description": "", "members": ["S:1:0", "S:2:0"],
                           "x": 0, "y": 0}]
          and out["names"] == {"version": None, "group": "g1", "statements": ["one", "two"], "label": "Mornings", "others": [], "note": "Why it holds."},
          str(out["body"]))
    check("undo puts the old note back, none, and redo the new one",
          out["undone"] == ["", False] and out["redone"] == "Why it holds.", str(out["undone"]))
    check("a revision on view keeps its note as it is",
          out["locked"] == [False, "Why it holds."], str(out["locked"]))
    check("a note cleared is none, so a save and the titles send none",
          out["cleared"] == [True, False, {"id": "g1", "label": "Mornings", "description": "", "members": ["S:1:0", "S:2:0"], "x": 0, "y": 0},
                             {"version": None, "group": "g1", "statements": ["one", "two"], "label": "Mornings", "others": []}], str(out["cleared"]))
