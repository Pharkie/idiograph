from __future__ import annotations

import datetime as dt
import json
import os
import shutil
import subprocess
import sys
import time

import openpyxl

from . import support
from .support import check, skip
import idiograph_routes

# An invented study of keeping bees, Wren and Odile the participants and Ivo asking, every word made up. Each
# row is (speaker, time, statements), a statement cell's entries split by a blank line.
ROWS = [
    ("Ivo", "00:12:00", None),
    ("{who}", "00:12:04", "Feeling trusted when the bees stay calm on her hands"),
    ("{who}", "00:12:10", "Taking the calm as a gift"),
    ("{who}", "00:12:16", "The bees' calm read as a sign she is accepted"),
    ("{who}", "00:13:10", "Moving slowly so as not to alarm them"),
    ("{who}", "00:23:02", "Wanting to do right by the colony"),
    ("{who}", "00:23:20", "Duty felt as a weight she chose"),
]
HEAD = ["Name", "Timestamp", "Experiential statements", "Transcript", "Exploratory notes", "Key quotes"]


def made_book(path, who) -> None:
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Initial"
    ws.append(HEAD)
    for speaker, at, said in ROWS:
        name = speaker.format(who=who)
        ws.append([name, dt.time(*map(int, at.split(":"))), said, f"{name} says something about the bees.",
                   "Calm as being let in." if said else None, None])
    wb.save(path)


def test_boards_feedback(scratch):
    print("\n217. Adam's calls from a tester's feedback on the boards (20 October): a change from a window of the app "
          "comes in by itself and one from outside raises the notice, GETs taking a case's changes as one step of "
          "undo, a PET's stack on GETs under its top, Take out of PET a move, Group and Ungroup on the card's menu, "
          "Notes on cards and what the app wrote kept across a restart, and Every PET placed only when it is so")
    import gets as gets_mod
    import server as server_mod
    import themes
    import workbook as wb_mod

    root = scratch / "boards-feedback-root"
    shutil.rmtree(root, ignore_errors=True)
    books = {}
    for who in ("Wren", "Odile"):
        (root / who / "Working").mkdir(parents=True)
        books[who] = root / who / f"{who} - EN & ES.xlsx"
        made_book(books[who], who)
    (root / server_mod.PROJECT_FILE).write_text(json.dumps({
        "name": "Bees, a boards project", "agents": {"allowed": True, "at": "2026-10-20T20:00:00+01:00"}}), encoding="utf-8")
    cfg = scratch / "boards-feedback-config.json"
    cfg.write_text(json.dumps({"root": str(root), "interviewer": "Ivo"}), encoding="utf-8")
    keys = {who: [c["key"] for c in themes.read_cards(books[who])["cards"]] for who in books}

    def board_of(who, title="Being trusted by the hive"):
        k = keys[who]
        cards = {key: {"x": (i % 3) * 210, "y": (i // 3) * 100} for i, key in enumerate(k)}
        return {"id": "v1", "name": "Board 1", "cards": cards, "discarded": [], "picks": {}, "stacks": {k[0]: [k[1]]},
                "groups": [{"id": "g1", "label": title, "members": [k[0], k[1], k[2]], "x": 0, "y": -40},
                           {"id": "g2", "label": "Living alongside the colony", "members": [k[3], k[4]], "x": 0, "y": 400}]}

    for who in books:
        themes.save(books[who], board_of(who), who)

    def agent(who, title):
        ops = scratch / "boards-feedback-ops.json"
        ops.write_text(json.dumps([{"op": "retitle", "label": "g1", "title": title}]), encoding="utf-8")
        return subprocess.run([sys.executable, str(support.source("cli.py")), "--root", str(root), "--config", str(cfg), "board", "apply",
                               who, "v1", "--note", "Retitle it", "--tool", "Claude Code", "--ops", str(ops)],
                              capture_output=True, text=True, encoding="utf-8", timeout=120)

    kept = (server_mod.CONFIG_PATH, server_mod.ROOT_OVERRIDE, server_mod.STATE_MEMORY)
    written_before, hook_before = dict(wb_mod.WRITTEN), wb_mod.WRITTEN_HOOK
    try:
        server_mod.CONFIG_PATH, server_mod.ROOT_OVERRIDE = cfg, str(root)
        server_mod.STATE_MEMORY = {"recent": []}
        idiograph_routes._gets_books.clear()

        # ── A. the PETs board: a write of this process is the app's own, one from the command line is outside
        stamp = idiograph_routes.api_stamp({"workbook": str(books["Wren"])})
        check("217: a board the app itself last wrote is no change from outside", stamp.get("outside") is False, str(stamp)[:300])
        ran = agent("Wren", "Trusted by the hive")
        stamp = idiograph_routes.api_stamp({"workbook": str(books["Wren"])})
        check("217: a board an AI agent's command line changed is a change from outside, so the open board raises the notice",
              ran.returncode == 0 and stamp.get("outside") is True, (ran.stdout + ran.stderr)[:300])

        # ── B. GETs: the cases come in, a change made in the app comes in by itself, one from outside is said
        books_now = idiograph_routes.gets_books(root)
        gets_mod.settings_op(root, books_now, {"one_per_pet": True})
        stamp = idiograph_routes.api_stamp({"workbook": str(books["Wren"]), "gets": True})
        check("217: GETs just written by the app, with every case in and unchanged, list no case and no change from outside",
              stamp.get("cases") == [] and stamp.get("outside") is False, str(stamp)[:300])
        themes.save(books["Odile"], board_of("Odile", "Trusted, slowly, by the hive"), "Odile")
        idiograph_routes._gets_books.clear()
        stamp = idiograph_routes.api_stamp({"workbook": str(books["Wren"]), "gets": True})
        check("217: a case's PETs changed in a window of the app are listed as the app's own, which GETs take by themselves",
              stamp.get("cases") == [{"case": "Odile", "outside": False}], str(stamp.get("cases")))
        # the arrival to the nanosecond: a workbook written outside in the very second Odile's PETs came in is
        # written since, one as it stood when they came in is not, and a case kept before `seen` goes by its
        # `came` to the whole second, as it always has
        rec = dict(gets_mod.load(root)["cases"]["Odile"])
        wb_seen = rec["seen"]["workbook"][0]
        same = gets_mod.written_since(rec, "workbook", books["Odile"])
        # a write 100 ns on, the finest tick NTFS keeps: one a single nanosecond on reads back unmoved on
        # Windows (22 October, the 0.9.3 run), where a Mac keeps the nanosecond itself
        os.utime(books["Odile"], ns=(wb_seen + 100, wb_seen + 100))
        later = gets_mod.written_since(rec, "workbook", books["Odile"])
        second = (wb_seen // 1_000_000_000) * 1_000_000_000
        came = dt.datetime.fromtimestamp(second / 1e9).astimezone().isoformat(timespec="seconds")
        before_seen = {"came": came}
        os.utime(books["Odile"], ns=(second - 1_000_000, second - 1_000_000))
        old_before = gets_mod.written_since(before_seen, "workbook", books["Odile"])
        os.utime(books["Odile"], ns=(second + 1_000_000, second + 1_000_000))
        old_in = gets_mod.written_since(before_seen, "workbook", books["Odile"])
        os.utime(books["Odile"], ns=(wb_seen, wb_seen))
        check("217: a case's arrival is kept to the nanosecond, a write in its very second shows and an untouched file "
              "never does, and one kept to the whole second reads as before",
              same is False and later is True and old_before is False and old_in is True
              and gets_mod.untouched(books["Odile"], dict(rec, seen=gets_mod.seen_of(books["Odile"]))),
              str([same, later, old_before, old_in]))
        took = gets_mod.take(root, idiograph_routes.gets_books(root), "Odile")
        board = gets_mod.load(root)["boards"][0]
        check("217: taking them keeps a line in each GETs board's History, as the canvas's step of undo goes with it",
              took.get("taken") == "Odile" and any("Before Odile's changes came in" in str(h.get("name"))
                                                   for h in themes.history_of(board)), str(themes.history_list(board))[:300])
        # ── the mark keeps the size with the time (seenmark, 23 November): on a coarse clock a file rewritten
        # inside the tick it was read in keeps its time, so a rewrite to another size must still read as written
        rec = dict(gets_mod.load(root)["cases"]["Odile"])
        themes_file = themes.themes_path(books["Odile"])
        marks = rec["seen"]
        form = (isinstance(marks["workbook"], list) and len(marks["workbook"]) >= 2
                and marks["workbook"][1] == books["Odile"].stat().st_size
                and isinstance(marks["themes"], list) and marks["themes"][1] == themes_file.stat().st_size)
        bare = dict(rec, seen={n: (m[0] if isinstance(m, list) else m) for n, m in marks.items()})
        was_bytes = {p: p.read_bytes() for p in (books["Odile"], themes_file)}
        was_times = {p: p.stat().st_mtime_ns for p in was_bytes}
        got = {}
        try:
            got["quiet"] = [gets_mod.written_since(rec, n, p) for n, p in gets_mod.case_files(books["Odile"])]
            got["bare_quiet"] = [gets_mod.written_since(bare, n, p) for n, p in gets_mod.case_files(books["Odile"])]
            got["untouched"] = gets_mod.untouched(books["Odile"], rec)
            # each file rewritten to another size, then given back the time the snapshot read: the coarse clock's tick
            for n, p in gets_mod.case_files(books["Odile"]):
                p.write_bytes(was_bytes[p] + b" ")
                os.utime(p, ns=(was_times[p], was_times[p]))
                got["size_" + n] = gets_mod.written_since(rec, n, p)
                # an old bare time compares the time alone, as it always did: this very file reads as untouched
                got["bare_" + n] = gets_mod.written_since(bare, n, p)
                p.write_bytes(was_bytes[p])
                os.utime(p, ns=(was_times[p], was_times[p]))
            # the copy of a participant whose workbook was rewritten to another size is not read as standing
            books["Odile"].write_bytes(was_bytes[books["Odile"]] + b" ")
            os.utime(books["Odile"], ns=(was_times[books["Odile"]],) * 2)
            got["copies"] = gets_mod.copies_untouched(root, books["Odile"])
            got["outside"] = gets_mod.changed_outside({"workbook": str(books["Odile"])}, rec)
            books["Odile"].write_bytes(was_bytes[books["Odile"]])
            os.utime(books["Odile"], ns=(was_times[books["Odile"]],) * 2)
            got["copies_back"] = gets_mod.copies_untouched(root, books["Odile"])
            # the same size inside one tick: kept by the sha, where the clock is coarse and the file was just written
            was_coarse = gets_mod.COARSE
            gets_mod.COARSE = True
            try:
                now = time.time_ns()
                os.utime(books["Odile"], ns=(now, now))
                shaped = dict(rec, seen=gets_mod.seen_of(books["Odile"]))
                got["sha_kept"] = len(shaped["seen"]["workbook"]) == 3
                same = bytearray(was_bytes[books["Odile"]])
                same[-1] ^= 0x01
                books["Odile"].write_bytes(bytes(same))
                os.utime(books["Odile"], ns=(now, now))
                got["same_size"] = gets_mod.written_since(shaped, "workbook", books["Odile"])
                books["Odile"].write_bytes(was_bytes[books["Odile"]])
                os.utime(books["Odile"], ns=(now, now))
                got["same_back"] = gets_mod.written_since(shaped, "workbook", books["Odile"])
                # a file written long before the reading keeps no sha, so a quiet open reads nothing
                os.utime(books["Odile"], ns=(now - 60_000_000_000,) * 2)
                got["old_file_no_sha"] = len(gets_mod.seen_of(books["Odile"])["workbook"]) == 2
            finally:
                gets_mod.COARSE = was_coarse
        finally:
            for p, data in was_bytes.items():
                p.write_bytes(data)
                os.utime(p, ns=(was_times[p], was_times[p]))
        check("217: a case's files are kept by time and size: a file rewritten to another size inside the tick it was read in "
              "reads as written since, a bare time kept before reads by the time alone, a file untouched since never reads as "
              "written, and the copy of a rewritten workbook is not read as standing",
              form and got["quiet"] == [False, False] and got["bare_quiet"] == [False, False] and got["untouched"] is True
              and got["size_workbook"] is True and got["size_themes"] is True
              and got["bare_workbook"] is False and got["bare_themes"] is False
              and got["copies"].get("Odile") is False and got["outside"] is True and got["copies_back"].get("Odile") is True,
              str(got))
        check("217: on a coarse clock a rewrite to the same size inside one tick is told by the sha kept for a file written "
              "within a tick of the reading, and a file written long before it keeps none",
              got["sha_kept"] and got["same_size"] is True and got["same_back"] is False and got["old_file_no_sha"], str(got))
        # ── what the app wrote is kept by time and size too: another process rewriting the file to another size inside the
        # same tick is a change from outside, and a bare time kept by an earlier run still compares by the time alone
        book = books["Odile"]
        rec = dict(gets_mod.load(root)["cases"]["Odile"], seen=gets_mod.seen_of(book))
        book_bytes, book_at = book.read_bytes(), book.stat().st_mtime_ns
        key = str(book.resolve())
        kept_here = dict(wb_mod.WRITTEN)
        got2 = {}
        try:
            wb_mod.note_written(book)
            got2["form"] = wb_mod.WRITTEN.get(key) == [book_at, len(book_bytes)]
            got2["here"] = wb_mod.written_here(book)
            got2["quiet"] = gets_mod.changed_outside({"workbook": str(book)}, rec)
            book.write_bytes(book_bytes + b" " * 20)
            os.utime(book, ns=(book_at, book_at))
            got2["rewritten_here"] = wb_mod.written_here(book)
            got2["outside"] = gets_mod.changed_outside({"workbook": str(book)}, rec)
            wb_mod.WRITTEN[key] = book_at
            got2["bare_here"] = wb_mod.written_here(book)
            got2["still"] = sorted(wb_mod.still_written({key: book_at, "x": True, key + "2": [1, 2]}))
            got2["still_list"] = sorted(wb_mod.still_written({key: [book_at, len(book_bytes) + 20]}))
            got2["still_old_size"] = sorted(wb_mod.still_written({key: [book_at, len(book_bytes)]}))
        finally:
            book.write_bytes(book_bytes)
            os.utime(book, ns=(book_at, book_at))
            wb_mod.WRITTEN.clear()
            wb_mod.WRITTEN.update(kept_here)
        check("217: a file the app wrote is kept by time and size, so another process rewriting it to another size inside the "
              "same tick is a change from outside, a bare time kept before compares by the time alone, and one a restart finds as "
              "it was written is still the app's",
              got2["form"] and got2["here"] is True and got2["quiet"] is False and got2["rewritten_here"] is False
              and got2["outside"] is True and got2["bare_here"] is True and got2["still"] == [key]
              and got2["still_list"] == [key] and got2["still_old_size"] == [], str(got2))
        ran = agent("Wren", "Accepted by the hive")
        idiograph_routes._gets_books.clear()
        stamp = idiograph_routes.api_stamp({"workbook": str(books["Wren"]), "gets": True})
        check("217: a case's PETs changed by an AI agent's command line are a change from outside, said with Update",
              ran.returncode == 0 and stamp.get("cases") == [{"case": "Wren", "outside": True}], str(stamp.get("cases")))
        snap = gets_mod.snapshot(books["Odile"])
        k = keys["Odile"]
        check("217: a statement stacked under another on a case's board comes to GETs naming its top, in its top's PET",
              snap["lines"][k[1]].get("stacked") == k[0] and snap["lines"][k[1]]["pet"] == "g1"
              and k[1] not in snap["pets"][0]["statements"], str(snap["lines"][k[1]]))

        # ── C. Notes on cards: off on a new install, kept across a restart
        fresh = server_mod.merge_config({})
        server_mod.api_settings({"card_notes": True})
        saved = support.board_file(cfg)
        again = server_mod.merge_config(saved)
        check("217: Notes on cards is off on a new install, and turned on it is kept across a restart",
              fresh.get("card_notes") is False and saved.get("card_notes") is True and again.get("card_notes") is True,
              str({"fresh": fresh.get("card_notes"), "saved": saved.get("card_notes")}))

        # ── E. the files the app wrote, kept in its state across a restart
        server_mod.STATE_MEMORY = {"recent": []}
        wb_mod.WRITTEN.clear()
        idiograph_routes.keep_written_on()
        themes.save(books["Odile"], board_of("Odile", "Trusted at last by the hive"), "Odile")
        kept_list = dict((server_mod.STATE_MEMORY or {}).get("written") or {})
        wb_mod.WRITTEN.clear()
        wb_mod.WRITTEN_HOOK = None
        idiograph_routes.keep_written_on()
        stamp = idiograph_routes.api_stamp({"workbook": str(books["Odile"])})
        check("217: after a restart a board the app last wrote is still its own, the list of what it wrote kept in its state",
              str(themes.themes_path(books["Odile"]).resolve()) in kept_list and stamp.get("outside") is False,
              str(stamp.get("outside")) + " " + str(len(kept_list)))
        held = themes.themes_path(books["Odile"])
        later = held.stat().st_mtime_ns + 5_000_000_000
        os.utime(held, ns=(later, later))
        wb_mod.WRITTEN.clear()
        wb_mod.WRITTEN_HOOK = None
        idiograph_routes.keep_written_on()
        stamp = idiograph_routes.api_stamp({"workbook": str(books["Odile"])})
        check("217: a board changed while the app was closed is a change from outside after the restart",
              stamp.get("outside") is True, str(stamp.get("outside")))
    finally:
        server_mod.CONFIG_PATH, server_mod.ROOT_OVERRIDE, server_mod.STATE_MEMORY = kept
        wb_mod.WRITTEN.clear()
        wb_mod.WRITTEN.update(written_before)
        wb_mod.WRITTEN_HOOK = hook_before
        idiograph_routes._gets_books.clear()

    # ── D. the page's model in node
    node = shutil.which("node")
    if not node:
        skip("217: the boards' model in node", "node is not installed")
        return
    js = support.text("apps/idiograph/static/themes.js")
    script = scratch / "boards-feedback-model.js"
    script.write_text(support.i18n_js() + """
globalThis.$ = () => null;
globalThis.esc = (s) => String(s);
globalThis.escAttr = (s) => String(s);
globalThis.say = () => {};
""" + js + r"""
const out = {};
thRender = () => {}; thEase = () => {}; thSoon = () => {}; thAck = () => {}; thInspectorOpen = () => {}; thPanelFollow = () => {};
thSettle = () => false; thFlash = (n) => { out.flashed = (out.flashed || []).concat([n]); };
// a GETs board: two PETs and a sub-theme of Wren's, one PET of Odile's with no card, a GET holding the first
TH.mode = 'gets'; TH.live = true; TH.layout = {};
TH.gets = { cases: [
  { case: 'Wren', who: 'Wren', in: true, status: 'in', pets: [{ id: 'g1', parent: null }, { id: 'g2', parent: null }, { id: 'g3', parent: 'g2' }],
    lines: { 'Initial:2:0': { text: 'Feeling trusted', pet: 'g1' }, 'Initial:3:0': { text: 'Taking the calm as a gift', pet: 'g1', stacked: 'Initial:2:0' },
             'Initial:5:0': { text: 'Moving slowly', pet: null }, 'Initial:4:0': { text: 'A sign', pet: 'g1' } } },
  { case: 'Odile', who: 'Odile', in: true, status: 'in', pets: [{ id: 'g1', parent: null }], lines: {} }] };
TH.gets.cases[0].pets[0].statements = ['Initial:2:0', 'Initial:4:0'];
const card = (key, kind) => ({ key, kind, case: key.split('/')[0], x: 0, y: 0, text: key });
const v = { cards: { 'Wren/g1': card('Wren/g1', 'pet'), 'Wren/g2': card('Wren/g2', 'pet'), 'Wren/g3': card('Wren/g3', 'sub') },
  groups: [{ id: 'G1', label: 'Calm', members: ['Wren/g1'] }], discarded: [], picks: {}, stickies: [], stacks: {}, not_same: [] };
TH.v = v;
out.tally = gtTally(v);
v.discarded.push('Wren/g2', 'Wren/g3');
out.binned = gtTally(v);
// an act that only bins raises no count and no Every PET placed
const before = thSnap(v, new Set());
v.discarded = [];
const was = thSnap(v, new Set());
v.discarded = ['Wren/g2', 'Wren/g3'];
thMomentum(was);
out.binFlash = out.flashed || [];
// the Cases panel's tree: the stacked statement under its top, not under Not in a PET
const tree = gtTree(TH.gets.cases[0]);
out.tree = { own: tree.tops[0].own, under: tree.under, none: tree.none };
// a search that finds only a stacked statement opens the PET holding its top, and the stack under the top
const list = { innerHTML: '', scrollTop: 0 };
$ = (id) => (id === 'gt-cases' ? list : null);
Object.assign(TH, { casesOpen: true, cfind: 'calm as a gift', cflip: new Set(), cfold: new Set() });
// with the PET holding the top off the board, since the panel lists only what is not on it (toolbar10)
TH.v = Object.assign({}, v, { cards: {} });
gtCasesDraw();
TH.v = v;
out.found = { stack: list.innerHTML.includes('Taking the calm as a gift'), top: list.innerHTML.includes('Feeling trusted') };
$ = () => null;
TH.cfind = '';
// Group and Ungroup on a card's menu, and Take out of GET a move, not a bin
TH.sel = { cards: new Set(['Wren/g1']), groups: new Set(), stickies: new Set() };
const items = thMenuItems(v, { kind: 'card', id: 'Wren/g1' }, false);
out.menu = items.map((it) => [it.act, TH_TAKES.includes(it.act)]);
TH.sel = { cards: new Set(['Wren/g2']), groups: new Set(), stickies: new Set() };
v.discarded = [];
out.loose = thMenuItems(v, { kind: 'card', id: 'Wren/g2' }, false).map((it) => it.act);
thLeave(v, 'Wren/g1');
out.left = { parent: thParents(v)['Wren/g1'] === undefined, binned: v.discarded.includes('Wren/g1'), card: !!v.cards['Wren/g1'] };
// Notes on cards: a statement card's exploratory notes only while the switch is on, and on GETs alone
TH.gets.cases[0].lines['Initial:5:0'].notes = ['Calm as being let in.'];
v.cards['Wren/es/Initial:5:0'] = card('Wren/es/Initial:5:0', 'es');
TH.config = { card_notes: false };
out.notesOff = thEnHtml(v, 'Wren/es/Initial:5:0');
TH.config = { card_notes: true };
out.notesOn = thEnHtml(v, 'Wren/es/Initial:5:0');
TH.mode = 'pets';
out.notesPets = thEnHtml(v, 'Wren/es/Initial:5:0');
console.log(JSON.stringify(out));
""", encoding="utf-8")
    ran = subprocess.run([node, str(script)], capture_output=True, text=True, encoding="utf-8", timeout=60)
    try:
        o = json.loads(ran.stdout.strip().splitlines()[-1])
    except (ValueError, IndexError):
        o = {}
    said = (ran.stdout + ran.stderr)[:600]
    check("217: what is left on GETs counts every PET and sub-theme of the study, one with no card on the board too",
          o.get("tally") == {"left": 3, "placed": 1}, said)
    check("217: a PET in the bin is not left, and an act that only bins raises no count and no Every PET placed",
          o.get("binned") == {"left": 1, "placed": 1} and o.get("binFlash") == [], said)
    check("217: a statement stacked under its top goes under it in the Cases panel, never under Not in a PET",
          (o.get("tree") or {}).get("under") == {"Initial:2:0": ["Initial:3:0"]}
          and "Initial:3:0" not in (o.get("tree") or {}).get("none", ["Initial:3:0"])
          and (o.get("tree") or {}).get("own") == ["Initial:2:0", "Initial:4:0"], said)
    check("217: a search that finds only a stacked statement opens its PET and its stack, the top shown above it",
          o.get("found") == {"stack": True, "top": True}, said)
    acts = [a for a, _ in o.get("menu") or []]
    check("217: a card that is the whole of its GET has Group and Ungroup on its menu, and Take out of GET is no bin",
          "groupsel" in acts and "ungroup" in acts and ["leave", False] in (o.get("menu") or []), said)
    check("217: a card in no GET has Group and no Ungroup", "groupsel" in (o.get("loose") or [])
          and "ungroup" not in (o.get("loose") or []), said)
    check("217: Take out leaves the card on the board, in no GET and not in the bin",
          o.get("left") == {"parent": True, "binned": False, "card": True}, said)
    check("217: a statement card shows its exploratory notes only with Notes on cards on, and on GETs alone",
          o.get("notesOff") == "" and "Calm as being let in." in str(o.get("notesOn")) and o.get("notesPets") == "", said)
