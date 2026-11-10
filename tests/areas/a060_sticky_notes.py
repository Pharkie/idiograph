from __future__ import annotations

import json
import shutil

import export as export_mod

from . import support
from .support import DEMO_QUESTION, check, css_block, demo_copy, skip
import idiograph_routes


def test_sticky_notes(scratch):
    print("\n60. Sticky notes on the PETs canvas (128), and the Inspector for a statement: "
          "edited in place there (143), and shown once (144)")
    import subprocess
    import server as server_mod
    import themes as themes_mod
    import themes_ai
    import themes_print

    js = support.text("apps/idiograph/static/themes.js")
    css = support.text("apps/idiograph/static/themes.css")
    style = support.text("family/static/style.css", "apps/idiograph/static/distil.css")
    fn = lambda src, name: src.split(f"function {name}(", 1)[1].split("\n}", 1)[0]

    # ── A. the file
    root = scratch / "stickies-root"
    work = demo_copy(root, "Juno", "Juno - EN & ES.xlsx")
    (root / "idiograph-project.json").write_text(json.dumps({"name": "Scratch", "research_question": DEMO_QUESTION}),
                                                 encoding="utf-8")
    path = themes_mod.themes_path(work)
    read = themes_mod.read_cards(work)
    k = [c["key"] for c in read["cards"]]
    WORDS = "Not sure about this one\nmerge with group 4?"
    OTHER = "Think about splitting this one"

    def file():
        return json.loads(path.read_text(encoding="utf-8"))

    def board(bid):
        return next(b for b in file()["boards"] if b["id"] == bid)

    raw = themes_mod.blank_version(read["cards"])
    for key, (x, y) in zip(k, [(0, 0), (220, 0), (0, 300), (900, 0)]):
        raw["cards"][key].update(x=x, y=y)
    raw["groups"] = [{"id": "g1", "label": "Mornings", "members": [k[0], k[1]], "x": 0, "y": -40}]
    raw["notes"] = [{"id": "n1", "text": f"  {WORDS.replace(chr(10), chr(13) + chr(10))}\n ", "colour": "pink", "x": 440, "y": 0, "in": "g1"},
                    {"id": "n2", "text": OTHER, "colour": "mauve", "x": 1400.6, "y": 0, "in": "g9"},
                    {"id": "n1", "text": "a second n1"}, {"id": "g1", "text": "a group's id"},
                    {"id": k[3], "text": "a card's key"}, "junk", {"id": "", "text": "no id"}]
    kept = themes_mod.normalise(raw)
    check("128: normalise keeps each note as its id, text, colour, x, y and in, its lines kept and its ends stripped",
          kept["notes"][0] == {"id": "n1", "text": WORDS, "colour": "pink", "x": 440, "y": 0, "in": "g1"}
          and list(kept["notes"][0]) == ["id", "text", "colour", "x", "y", "in"], str(kept["notes"][:1]))
    check("128: a note whose in names no group stands free, a colour not one of the four is yellow, and no id is taken twice",
          kept["notes"][1] == {"id": "n2", "text": OTHER, "colour": "yellow", "x": 1401, "y": 0} and len(kept["notes"]) == 2,
          str(kept["notes"]))
    check("128: a note is never a member, and a board with none carries none, the schema still 2",
          kept["groups"][0]["members"] == [k[0], k[1]] and "notes" not in themes_mod.normalise(dict(raw, notes=[]))
          and "notes" not in themes_mod.blank_version(read["cards"]) and themes_mod.SCHEMA == 2
          and themes_mod.normalise(kept) == kept)
    plain = {key: value for key, value in kept.items() if key != "notes"}
    hash_of = lambda b: themes_mod.state_hash(themes_mod.state_of(themes_mod.normalise(b)))
    check("128: a revision's state holds the notes, and its hash takes a note's words and its colour",
          themes_mod.state_of(kept)["notes"] == kept["notes"] and "notes" not in themes_mod.state_of(plain)
          and hash_of(kept) != hash_of(dict(kept, notes=[dict(kept["notes"][0], text="other words"), kept["notes"][1]]))
          and hash_of(kept) != hash_of(dict(kept, notes=[dict(kept["notes"][0], colour="blue"), kept["notes"][1]]))
          and hash_of(kept) == hash_of(json.loads(json.dumps(kept))) and "notes" in themes_mod.STATE_KEYS)
    drawn = themes_mod.layout_boxes(kept)
    bare = themes_mod.layout_boxes(plain)
    check("128: the server's layout draws a note in a PET inside its frame, and a free note as a box of its own",
          drawn["frames"]["g1"][2] > bare["frames"]["g1"][2] and drawn["notes"]["n2"][:3] == (1401, 0, themes_mod.NOTE_W)
          and themes_mod.note_height("") == themes_mod.NOTE_MIN_H
          and themes_mod.note_height("word " * 80) > themes_mod.NOTE_MIN_H, str(drawn["frames"]["g1"]))
    alone = {"cards": {}, "groups": [], "notes": [{"id": "n1", "text": "", "colour": "yellow", "x": -80, "y": -70}]}
    new = themes_mod.place_new(["S:1:0"], {"S:1:0": "A new line"}, alone)["S:1:0"]
    check("128: a new card takes the nearest spot the margin clear of a sticky note",
          not themes_mod.clash((new["x"], new["y"], themes_mod.CARD_W, themes_mod.card_height("A new line")),
                               (-80, -70, themes_mod.NOTE_W, themes_mod.NOTE_MIN_H), themes_mod.MARGIN), str(new))

    saved_root = server_mod.ROOT_OVERRIDE
    real_config = server_mod.CONFIG_PATH
    server_mod.ROOT_OVERRIDE = str(root)
    server_mod.CONFIG_PATH = scratch / "stickies-config.json"
    try:
        opened = idiograph_routes.api_themes({"workbook": str(work)})
        check("128: /api/themes carries the board's sticky notes as stickies, and notes still says a save keeps a PET's note",
              opened.get("stickies") == [] and opened.get("notes") is True)
        book = work.read_bytes()
        idiograph_routes.api_themes_save({"workbook": str(work), "version": raw})
        check("128: a save writes the notes into the themes file, and the workbook is never touched",
              board("v1").get("notes") == kept["notes"] and work.read_bytes() == book)
        shown = idiograph_routes.api_themes({"workbook": str(work)})
        check("128: the screen's state carries them back as stickies", shown["stickies"] == kept["notes"])
        idiograph_routes.api_themes_save({"workbook": str(work), "version": plain})
        check("128: a save from a page that sends no notes leaves the file's as they were",
              board("v1").get("notes") == kept["notes"])
        idiograph_routes.api_themes_save({"workbook": str(work), "version": dict(plain, groups=[])})
        check("128: and one that takes a note's PET away leaves the note standing free",
              board("v1")["notes"][0] == {key: value for key, value in kept["notes"][0].items() if key != "in"})
        idiograph_routes.api_themes_save({"workbook": str(work), "version": kept})
        made = idiograph_routes.api_themes_boards({"workbook": str(work), "op": "revision", "id": "v1", "name": "With notes"})
        rid = made["revision"]["id"]
        idiograph_routes.api_themes_save({"workbook": str(work), "version": dict(kept, notes=[])})
        cleared = "notes" not in board("v1")
        held = next(r for r in board("v1")["history"] if r["id"] == rid)["state"].get("notes")
        view = idiograph_routes.api_themes_boards({"workbook": str(work), "op": "view", "id": "v1", "revision": rid})
        restored = idiograph_routes.api_themes_boards({"workbook": str(work), "op": "restore", "id": "v1", "revision": rid})
        check("128: a save that sends none clears them, a revision holds them, its view shows them and Restore brings them back",
              cleared and held == kept["notes"] and view["stickies"] == kept["notes"]
              and board("v1").get("notes") == kept["notes"] and restored["stickies"] == kept["notes"])
        twin = idiograph_routes.api_themes_versions({"workbook": str(work), "op": "duplicate", "id": "v1"})
        check("128: Duplicate copies the notes with the board",
              twin["current"] == "v2" and board("v2").get("notes") == kept["notes"] and twin["stickies"] == kept["notes"])
        idiograph_routes.api_themes_versions({"workbook": str(work), "op": "new"})
        own = [{"id": "n1", "text": "the new board's own", "colour": "green", "x": 3000, "y": 3000}]
        idiograph_routes.api_themes_save({"workbook": str(work), "version": dict(themes_mod.normalise(board("v3")), notes=own)})
        copied = idiograph_routes.api_themes_boards({"workbook": str(work), "op": "copy", "id": "v1", "group": "g1", "to": "v3"})
        check("128: Copy to board carries no note, and the notes of the board it goes to stay as they were",
              copied["copied"]["label"] == "Mornings" and board("v3").get("notes") == own
              and "Not sure about this one" not in json.dumps(board("v3"), ensure_ascii=False))
        proposed = themes_mod.version_op(work, themes_mod.PROPOSE, {"version": kept, "note": "Proposed"}, "Juno")
        check("128: an AI board starts with no notes",
              "notes" not in board(proposed["current"]) and proposed["stickies"] == [])

        # ── B. nowhere a statement goes: the counts, the draft, the CSV, the print view, the outline, the prompts
        idiograph_routes.api_themes_versions({"workbook": str(work), "op": "switch", "id": "v1"})
        idiograph_routes.api_themes_export({"workbook": str(work), "version": "v1"})
        draft = themes_mod.draft_path(work, "Board 1").read_text(encoding="utf-8")
        csv_text = export_mod.output_path(work).read_text(encoding="utf-8-sig")
        printed = themes_print.page(work, "Juno", "v1", DEMO_QUESTION, auto=False)
        outline = themes_mod.outline(read, board("v1"))
        merged = themes_mod.merge(read["cards"], board("v1"))
        prompts = (themes_ai.review_user(outline)
                   + themes_ai.group_user(themes_ai.statements_of(merged), themes_ai.labels_of(merged), "")
                   + themes_ai.pet_user(themes_ai.names_target(read, board("v1"), "g1")))
        words = ("Not sure about this one", "merge with group 4", OTHER)
        found = [name for name, text in (("draft", draft), ("CSV", csv_text), ("print", printed),
                                          ("outline", json.dumps(outline, ensure_ascii=False)), ("prompts", prompts))
                 if any(w in text for w in words)]
        check("128: the PET draft, the CSV, the print view, the outline and every prompt carry no note's words",
              not found and "## A. Mornings" in draft and "Mornings" in prompts, ", ".join(found) or "none")
        check("128: a note inside a PET is never counted, 2 statements staying 2 statements",
              outline["themes"][0]["count"] == "2 statements"
              # the PET's rows up to the next PET's title, its lead and the rest after it (311)
              and printed.split('<span class="title">Mornings</span>', 1)[1].split('<h2 class="pet-title"', 1)[0]
              .split("</main>", 1)[0].count('<div class="item">') == 2
              and "## A. Mornings" in draft and draft.split("## A. Mornings", 1)[1].split("\n## ", 1)[0].count("\n- ") == 2)
    finally:
        server_mod.ROOT_OVERRIDE = saved_root
        server_mod.CONFIG_PATH = real_config

    # ── C. the page
    hand = '--hand: "Bradley Hand", "Noteworthy", "Segoe Print", "Segoe Script", "Comic Sans MS", cursive;'
    check("128: the words are in the system's handwriting stack, nothing downloaded and no font file shipped for them",
          # the faces are tokens in tokens.css since 15 October. The one font file is Ko-fi's Quicksand for its
          # button on each Home (22 October), so style.css's one face is that and nothing else
          hand in support.text("family/static/tokens.css")
          and "font-family: var(--hand)" in css_block(css, ".th-sticky") and "@font-face" not in css
          and style.count("@font-face") == 1 and 'font-family: "Quicksand"' in style.split("@font-face", 1)[1].split("}", 1)[0]
          # every page's folder since the fifth build (23 October 2026), the family's and each app's. The two text
          # fonts Adam ruled on 9 November 2026 (Charis SIL and Nunito Sans, family/static/fonts, for the typeset
          # pages) are the only others, and never a handwriting face
          and [p.relative_to(support.TOOL).as_posix()
               for folder in [support.TOOL / "family" / "static"] + sorted((support.TOOL / "apps").glob("*/static"))
               for p in sorted(folder.rglob("*"))
               if p.suffix.lower() in (".woff", ".woff2", ".ttf", ".otf")
               and not (p.parent == support.TOOL / "family" / "static" / "fonts"
                        and p.name.startswith(("CharisSIL-", "NunitoSans-")))]
          == ["family/static/vendor/quicksand/quicksand-latin-700-normal.woff2"])
    items = fn(js, "thMenuItems")
    check("128: a right-click on empty canvas opens a menu with New sticky note, one on a note its colours, Take out of PET and Delete note",
          # and on GETs Arrange by participant after it (19 October, area 205)
          "return [{ label: t('themes.menu.new_sticky'), act: 'sticky' }].concat(" in items
          and "TH_STICKY_COLOURS.map((c) => ({ label: thColourName(c), act: 'colour', colour: c, on: note.colour === c }))" in items
          and "out.push({ label: thLeaveLabel(v, owner), act: 'leave', rule: true });" in items
          and "out.push({ label: t('themes.sticky.delete_label'), act: 'unstick', rule: true });" in items
          and "thMenuOpen({ kind: 'canvas', x: e.clientX, y: e.clientY }, e.clientX, e.clientY);" in fn(js, "thContextMenu")
          and "pop.className = 'row-menu th-cmenu';" in fn(js, "thMenuOpen"))
    up = fn(js, "thPointerUp")
    check("128: a double-click on empty canvas, or in a frame's empty space, makes a note, and one on a note opens its words",
          "if (!l.moved && !l.add && thEmptyTwice(e)) thStickyNew(e.clientX, e.clientY);" in up
          and "if (thEmptyTwice(e)) thStickyNew(e.clientX, e.clientY);" in up
          and "if (item.kind === 'sticky') thStickyEditOpen(item.id);" in up
          and "now - last.at < 450" in fn(js, "thEmptyTwice"))
    made_js = fn(js, "thStickyNew")
    check("128: in front of a server from before the notes the double-click says to restart and makes none",
          "if (!TH.stickable) { say(RESTART_LINE, 6000); return; }" in made_js
          and made_js.index("TH.stickable") < made_js.index("thStickyMake(") and "thRefuse('sticky')" in made_js
          and "TH.stickable = Array.isArray(data.stickies);" in fn(js, "thLoad"))
    edit_open = fn(js, "thStickyEditOpen")
    edit_done = fn(js, "thStickyEditDone")
    check("128: Enter keeps the words and leaves the box, Shift + Enter is a new line, a click away keeps them, Esc on none removes the note",
          "if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); thStickyEditDone(true); }" in edit_open
          and "box.addEventListener('blur', () => thStickyEditDone(true));" in edit_open
          and "if (!keep && !text) {" in edit_done and "TH.removed = thPut(v, ed.before);" in edit_done
          and "thDone(ed.before, t('themes.step.made_sticky')" in edit_done and "thStickyEditDone(keep);" in fn(js, "thTitleDone"))
    check("128: nothing about a note carries the sparkles, and the bin never takes one",
          not any("TH_SPARK_ICON" in fn(js, name) for name in ("thStickyNew", "thStickyEditOpen", "thStickyHtml",
                                                                "thMenuItems", "thStickyDelete", "thStickyRecolour"))
          and "thDiscard" not in fn(js, "thStickyDelete") and "thIsSticky" not in fn(js, "thDiscardKey")
          and "a\n    // sticky note too, since the sidebar is for statements alone" in fn(js, "thDragEnd"))
    body = fn(js, "thBody")
    check("128: a save sends the notes as the file's notes, even none, and a board from a server before them sends no key",
          "if (Array.isArray(v.stickies)) {" in body and "out.notes = base.stickies.map(" in body
          and "stickies: Array.isArray(v.stickies) ? base.stickies : null," in fn(js, "thSnap"))

    # ── D. the model in node
    node = shutil.which("node")
    if node:
        script = scratch / "stickies-model.js"
        script.write_text(support.i18n_js() + """
const els = {};
globalThis.$ = (id) => els[id] || (els[id] = { id, className: '', textContent: '', title: '', innerHTML: '', hidden: false,
  scrollTop: 0, classList: { toggle() {}, add() {}, remove() {} }, querySelector: () => null });
globalThis.esc = (s) => String(s).replace(/[&<>]/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;' }[c]));
globalThis.escAttr = (s) => esc(s).replace(/"/g, '&quot;');
globalThis.say = () => {};
globalThis.RESTART_LINE = 'Restart the server to finish this update.';
globalThis.PLAY_GLYPH = '>';
""" + js + r"""
thPlayerDraw = () => {};
const keep = (x) => JSON.parse(JSON.stringify(x));
const size = (item) => (item.startsWith('g') ? { w: 100, h: 20 } : item.startsWith('n') ? { w: 160, h: 140 } : { w: 200, h: 80 });
const card = (x, y, text) => ({ x, y, text, time: '00:01' });
const LONG = 'She feels the house go quiet when the dog is out walking with him';
const v = { cards: { 'a:1:0': card(0, 0, LONG), 'a:2:0': card(220, 0, 'B'), 'a:3:0': card(0, 300, 'C') },
  groups: [], discarded: [], picks: {}, stickies: [] };
const out = {};
const g1 = thMakeGroup(v, ['a:1:0', 'a:2:0'], 'Mornings');
const n1 = thStickyMake(v, 440, 0, g1);
const n2 = thStickyMake(v, 900, 900);
out.made = [n1, n2, keep(v.stickies)];
out.count = [thCountText(v, g1), keep(thCounts(v)), v.groups.every((g) => !g.members.includes(n1))];
const lay = thLayout(v, size, null);
out.body = keep(lay[g1].body);
out.neighbours = [thNeighbours(v).get(g1).includes(n1), thNeighbours(v).get('').includes(n2)];
out.moving = [...thMoving(v, new Set(), new Set([g1]))].sort();
const mv = thMoving(v, new Set(), new Set(), new Set([n2]));
out.drop = keep(thDrop(v, mv, null, g1));
out.dropIn = thSticky(v, n2).in;
out.alt = keep(thDrop(v, mv, null, null, true));
out.altIn = thSticky(v, n2).in === undefined;
const snap = thSnap(v, new Set());
thStickyRemove(v, n1);
out.removed = thStickies(v).length;
thPut(v, snap);
out.back = keep(thSticky(v, n1));
out.colour = [thStickyColour(v, n1, 'pink'), thStickyColour(v, n1, 'pink'), thStickyColour(v, n1, 'red'), thSticky(v, n1).colour];
out.text = [thStickyText(v, n1, '  merge with\r\ngroup 4  '), thSticky(v, n1).text];
const g2 = thMakeGroup(v, ['a:3:0'], 'Three');
thStickiesJoin(v, [n2], g2);
out.g2 = [thSticky(v, n2).in, thCountText(v, g2)];
thDelete(v, g2);
out.freed = thSticky(v, n2).in === undefined;
const g3 = thMakeGroup(v, ['a:2:0'], 'Inside');
thStickiesJoin(v, [n2], g3);
out.inner = thParents(v)[g3] === g1 && thSticky(v, n2).in === g3;
thDelete(v, g3);
out.up = thSticky(v, n2).in;
thLeave(v, n2);
out.left = thSticky(v, n2).in === undefined && thParents(v)[n2] === undefined;
const meta = { id: 'v1', name: 'Board 1', note: '', created: 'c', updated: 'u' };
out.file = keep(thBody(v, meta).notes);
out.none = 'notes' in thBody({ cards: {}, groups: [], discarded: [], picks: {}, stickies: null }, meta);
out.empty = keep(thBody({ cards: {}, groups: [], discarded: [], picks: {}, stickies: [] }, meta).notes);
out.arranged = thArrange(v, g1, size);
const placed = thSticky(v, n1);
out.arrange = [thClashes(v, size).length, placed.y > Math.max(v.cards['a:1:0'].y, v.cards['a:2:0'].y)];
const w = { cards: { 'b:1:0': card(0, 0, 'X') }, groups: [], discarded: [], picks: {},
  stickies: [{ id: 'n1', text: '', colour: 'yellow', x: 50, y: 20 }] };
out.settle = [thClashes(w, size).length > 0, thSettle(w, size, ['n1'], null, []), thClashes(w, size).length,
  w.cards['b:1:0'].x, w.cards['b:1:0'].y];
out.menus = [thMenuItems(v, { kind: 'canvas' }).map((i) => i.label),
  thMenuItems(v, { kind: 'sticky', id: n1 }).map((i) => `${i.label}${i.on ? '*' : ''}`),
  thMenuItems(v, { kind: 'sticky', id: n2 }).map((i) => i.label),
  thMenuItems(Object.assign({}, v, { readonly: true }), { kind: 'canvas' }).length,
  thMenuItems(Object.assign({}, v, { readonly: true }), { kind: 'sticky', id: n1 }).length];
const locked = Object.assign({}, v, { readonly: true, stickies: v.stickies.slice() });
out.lockedMake = thStickyMake(locked, 0, 0);
out.oldMake = thStickyMake({ cards: {}, groups: [], discarded: [], picks: {}, stickies: null }, 0, 0);
TH.v = v;
thPanelHead(v, { kind: 'card', id: 'a:1:0' });
out.headCard = [els['th-panel-head'].className, els['th-panel-name'].textContent, els['th-panel-name'].title];
thPanelHead(v, { kind: 'sticky', id: n1 });
out.headNote = [els['th-panel-head'].className, els['th-panel-name'].textContent];
thPanelHead(v, { kind: 'group', id: g1 });
out.headGroup = [els['th-panel-head'].className.startsWith('th-phead hue-'), els['th-panel-name'].innerHTML];
Object.assign(TH, { panel: { kind: 'card', id: 'a:1:0' }, panelOpen: true, hasQuotes: true, quotes: {}, sheets: ['a'] });
thPanelDraw();
out.bodyCard = els['th-panel-body'].innerHTML;
TH.panel = { kind: 'sticky', id: n1 };
thPanelDraw();
out.bodyNote = els['th-panel-body'].innerHTML;
out.paper = els['th-panel-body'].className;
console.log(JSON.stringify(out));
""", encoding="utf-8")
        run = subprocess.run([node, str(script)], capture_output=True, text=True, encoding="utf-8")
        if run.returncode != 0:
            check("128: the sticky notes' model runs in node", False, run.stderr.strip()[:300])
        else:
            out = json.loads(run.stdout)
            check("128: in node, a note is made yellow and empty, inside the PET whose frame it is made in, its id the next n",
                  out["made"] == ["n1", "n2", [{"id": "n1", "text": "", "colour": "yellow", "x": 440, "y": 0, "in": "g1"},
                                               {"id": "n2", "text": "", "colour": "yellow", "x": 900, "y": 900}]], str(out["made"]))
            check("128: in node, a note inside a PET is never a member and never counted, and its frame runs round it",
                  out["count"] == ["2 statements", {"placed": 2, "unplaced": 1, "discarded": 0, "missing": 0}, True]
                  and out["body"] == {"x": 0, "y": 0, "w": 600, "h": 140}
                  and out["neighbours"] == [True, True], f"{out['count']} {out['body']}")
            check("128: in node, a PET that moves takes its notes, a note dropped in a frame joins it, and Alt-drop takes it out",
                  out["moving"] == ["a:1:0", "a:2:0", "g1", "n1"] and out["drop"] == {"joined": ["n2"], "left": [], "dest": "g1"}
                  and out["dropIn"] == "g1" and out["alt"] == {"joined": [], "left": ["n2"], "dest": None} and out["altIn"],
                  f"{out['moving']} {out['drop']} {out['alt']}")
            check("128: in node, a snapshot brings a deleted note back where it was, in the PET it was in",
                  out["removed"] == 1 and out["back"] == {"id": "n1", "text": "", "colour": "yellow", "x": 440, "y": 0, "in": "g1"},
                  str(out["back"]))
            check("128: in node, a colour is one of the four, and the words keep their lines with the ends stripped",
                  out["colour"] == [True, False, False, "pink"] and out["text"] == [True, "merge with\ngroup 4"], str(out["colour"]))
            check("128: in node, g takes a note into the new PET, a label deleted leaves its notes in the label above or free, Remove takes one out",
                  out["g2"] == ["g2", "1 statement"] and out["freed"] is True and out["inner"] is True and out["up"] == "g1"
                  and out["left"] is True, f"{out['g2']} {out['up']}")
            check("128: in node, the save sends the notes as the file holds them, an empty list when there are none, and no key from before them",
                  out["file"] == [{"id": "n1", "text": "merge with\ngroup 4", "colour": "pink", "x": 440, "y": 0, "in": "g1"},
                                  {"id": "n2", "text": "", "colour": "yellow", "x": 900, "y": 900}]
                  and out["none"] is False and out["empty"] == [], str(out["file"]))
            check("128: in node, Auto-arrange sets a PET's notes at the end of its block, nothing overlapping",
                  out["arranged"] is True and out["arrange"] == [0, True], str(out["arrange"]))
            check("128: in node, a note that lands on a card shifts clear of it by the margin, the card staying where it was",
                  out["settle"] == [True, True, 0, 0, 0], str(out["settle"]))
            check("128: in node, the canvas's menu, a note's menu in a PET and out of one, and none on a revision on view",
                  out["menus"] == [["New sticky note"], ["Yellow", "Pink*", "Green", "Blue", "Take out of PET", "Delete note"],
                                   ["Yellow", "Pink", "Green", "Blue", "Delete note"], 0, 0], str(out["menus"]))
            check("128: in node, no note is made on a revision on view or on a board from a server before them",
                  out["lockedMake"] is None and out["oldMake"] is None)
    else:
        skip("128: the sticky notes' model in node", "no node on this machine")

    # ── E. the Inspector for a statement
    open_js = fn(js, "thCardEditOpen")
    check("143: a double-click on the statement in the Inspector opens it by the card's own path, the same box, keys and route",
          "panel.addEventListener('dblclick', (e) => {" in js
          and "if (words && TH.panel && TH.panel.kind === 'card') thCardEditOpen(words.dataset.edit, { panel: true });" in js
          and "async function thCardEditOpen(key, opts = {}) {" in js and "box.className = 'th-title-edit th-card-edit';" in open_js
          and "if (words) box.classList.add('th-panel-edit');" in open_js and js.count("api(TH_EDIT_ROUTE,") == 2
          and "thRefuse('edit')" in open_js and ".th-panel-edit {" in css)
    check("143: the write puts the new words on the card and in the Inspector, and undo goes back through the same route",
          "thRender();\n  if (thInFile(() => thSettle(TH.v, thSize, [key], was, []))) thPlace();\n  if (TH.panelOpen) thPanelDraw();" in fn(js, "thStatementWrite")
          and "if (stack[stack.length - 1].edit) { thStatementStep(stack[stack.length - 1], backwards); return; }" in fn(js, "thUndo"))
