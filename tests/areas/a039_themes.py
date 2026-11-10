from __future__ import annotations

import json
import re
import shutil

import rounds as rounds_mod
import workbook as wb_mod
from workbook import WorkbookError

from . import support
from .support import DEMO_SHEET, ISO_OFFSET, add_second_sheet, check, demo_copy, json_strings, skip
import idiograph_routes


def test_themes(scratch):
    print("\n39. Themes: the cards, the pile, the merge, the themes file, the routes and the canvas")
    import http.server
    import subprocess
    import threading
    import urllib.error
    import urllib.request
    import server as server_mod
    import themes as themes_mod

    root = scratch / "themes-root"
    work = demo_copy(root, "Juno", "Juno - EN & ES.xlsx")
    add_second_sheet(work)

    # ── A. one card per entry of column C, on every sheet
    read = themes_mod.read_cards(work)
    case = wb_mod.read_case(work)
    lines = sum(len(r["es"].splitlines()) for s in case["sheets"] for r in s["rows"] if r["es"].strip())
    keys = [c["key"] for c in read["cards"]]
    check("the canvas reads both sheets, in workbook order", read["sheets"] == [DEMO_SHEET, "2d"],
          ", ".join(read["sheets"]))
    check("one card for every line of column C across the sheets", len(read["cards"]) == lines,
          f"{len(read['cards'])} cards, {lines} lines")
    check("every card's key is its own, sheet, row and line",
          len(set(keys)) == len(keys)
          and all(k == themes_mod.card_key(c["sheet"], c["row"], c["line"]) for k, c in zip(keys, read["cards"]))
          and themes_mod.split_card_key("Initial:12:2") == ("Initial", 12, 2))
    rows = {(s["name"], r["row"]): r for s in case["sheets"] for r in s["rows"]}
    texts = {(c["sheet"], c["row"]): [] for c in read["cards"]}
    for c in read["cards"]:
        texts[(c["sheet"], c["row"])].append(c["text"])
    check("each card carries its line's own words, in order",
          all(texts[k] == rows[k]["es"].splitlines() for k in texts), f"{len(texts)} rows with statements")
    check("each card's timecode is its row's, the way the player's clock writes it",
          all(c["seconds"] == rows[(c["sheet"], c["row"])]["seconds"]
              and c["time"] == rows[(c["sheet"], c["row"])]["time"] for c in read["cards"])
          and any(c["sheet"] == "2d" and c["time"] == "02:00" for c in read["cards"]),
          ", ".join(f"{c['key']} {c['time']}" for c in read["cards"][:3]))
    check("a project with no timecodes reads H:MM:SS past the hour, below it MM:SS",
          wb_mod.timecode(75) == "01:15" and wb_mod.timecode(3725) == "1:02:05"
          and wb_mod.timecode(0) == "00:00" and wb_mod.timecode(None) == "")

    # ── B. the pile: round, packed, the same every time, and no two cards intersecting
    spots = themes_mod.pile(read["cards"])
    again = themes_mod.pile(list(reversed(read["cards"])))
    n = len(keys)

    def pile_boxes(cards, at):
        return [(at[c["key"]]["x"], at[c["key"]]["y"], themes_mod.CARD_W, themes_mod.card_height(c["text"]))
                for c in cards]

    def too_near(boxes, gap):
        return [(i, j) for i in range(len(boxes)) for j in range(i + 1, len(boxes))
                if themes_mod.clash(boxes[i], boxes[j], gap)]

    boxes = pile_boxes(read["cards"], spots)
    check("the pile is seeded from the keys, so it is the same whatever the order",
          spots == again and spots == themes_mod.pile(read["cards"]), f"{n} cards")
    check("no two cards of the pile intersect, the margin, a twentieth of a card's width, between neighbours",
          not too_near(boxes, 0) and not too_near(boxes, themes_mod.MARGIN - 1) and themes_mod.MARGIN == themes_mod.CARD_W // 20 == 10,
          f"{len(too_near(boxes, themes_mod.MARGIN - 1))} pairs nearer than {themes_mod.MARGIN}px")
    whole = themes_mod.union(boxes)
    check("the pile lies round the middle of the canvas, about as tall as it is wide",
          abs(whole[0] + whole[2] / 2) <= 1 and abs(whole[1] + whole[3] / 2) <= 1
          and 0.6 <= whole[2] / whole[3] <= 1.7, f"{whole[2]:.0f} by {whole[3]:.0f}")
    eighty = [{"key": f"Initial:{i}:0", "text": "a word " * (i % 23 + 1)} for i in range(80)]
    heights = {themes_mod.card_height(c["text"]) for c in eighty}
    big = pile_boxes(eighty, themes_mod.pile(eighty))
    span = themes_mod.union(big)
    check("a pile of eighty cards of mixed heights has no two intersecting, and stays round",
          len(heights) >= 3 and not too_near(big, themes_mod.MARGIN - 1) and 0.6 <= span[2] / span[3] <= 1.7,
          f"{len(heights)} heights, {span[2]:.0f} by {span[3]:.0f}")
    first = themes_mod.state(work, "Juno")
    second = themes_mod.state(work, "Juno")
    check("the same case opens the same way until he moves something",
          [(c["key"], c["x"], c["y"]) for c in first["cards"]] == [(c["key"], c["x"], c["y"]) for c in second["cards"]]
          and all((c["x"], c["y"]) == (spots[c["key"]]["x"], spots[c["key"]]["y"]) for c in first["cards"]))
    check("opening writes nothing, and offers Board 1 with no groups",
          not themes_mod.themes_path(work).exists() and first["saved"] is False
          and first["version"]["name"] == "Board 1" and first["current"] == "v1"
          and first["groups"] == [] and first["discarded"] == [])

    # ── C. the merge: changed, missing, new
    version = themes_mod.blank_version(read["cards"])
    some = read["cards"][0]["key"]
    version["cards"][some]["text"] = "An older wording of this line"
    gone = "Initial:999:0"
    version["cards"][gone] = {"x": 5, "y": 6, "text": "A line that has since been taken out"}
    fresh = read["cards"][1]["key"]
    del version["cards"][fresh]
    merged = {c["key"]: c for c in themes_mod.merge(read["cards"], version)["cards"]}
    check("a stored card whose line now reads differently is marked changed, the stored text beside it",
          merged[some].get("changed") is True and merged[some]["stored"] == "An older wording of this line"
          and merged[some]["text"] == read["cards"][0]["text"])
    check("a stored card whose line has gone is marked missing, in its place, with its stored text",
          merged[gone].get("missing") is True and (merged[gone]["x"], merged[gone]["y"]) == (5, 6)
          and merged[gone]["text"] == "A line that has since been taken out" and merged[gone]["row"] == 999)
    drawn = [(c["x"], c["y"], themes_mod.CARD_W, themes_mod.card_height(c["text"])) for k, c in merged.items() if k != fresh]
    new_box = (merged[fresh]["x"], merged[fresh]["y"], themes_mod.CARD_W, themes_mod.card_height(merged[fresh]["text"]))
    check("a line the board has never seen gets a new card, in a free spot clear of every card by the gap",
          merged[fresh].get("new") is True and not any(themes_mod.clash(new_box, b, themes_mod.MARGIN - 1) for b in drawn)
          and merged[fresh]["x"] == themes_mod.merge(read["cards"], version)["cards"][1]["x"])
    check("every other card is just where the board put it",
          all(not c.get("changed") and not c.get("missing") and not c.get("new")
              for k, c in merged.items() if k not in (some, gone, fresh)))

    # through the workbook itself: a statement rewritten in the turn screen reads as changed
    edited = demo_copy(root, "Edited", "Juno - EN & ES.xlsx")
    e_cards = themes_mod.read_cards(edited)["cards"]
    themes_mod.save(edited, themes_mod.blank_version(e_cards), "Edited")
    turn = next(r for r in wb_mod.read_case(edited)["sheets"][0]["rows"] if r["es"].count("\n") >= 2)
    parts = turn["es"].splitlines()
    wb_mod.save_turn(edited, DEMO_SHEET, turn["row"], "\n".join(["A rewritten first line", parts[1]]),
                     turn["en"], turn["kq"])
    reopened = {c["key"]: c for c in themes_mod.state(edited, "Edited")["cards"]}
    k0, k2 = (themes_mod.card_key(DEMO_SHEET, turn["row"], i) for i in (0, 2))
    check("a statement rewritten on the turn screen reads as changed, and one taken out as missing",
          reopened[k0].get("changed") and reopened[k0]["text"] == "A rewritten first line"
          and reopened[k0]["stored"] == parts[0] and reopened[k2].get("missing")
          and reopened[k2]["text"] == parts[2], f"row {turn['row']}")

    # ── D. the routes, the file, and the root guard
    saved_root = server_mod.ROOT_OVERRIDE
    server_mod.ROOT_OVERRIDE = str(root)
    try:
        before = work.read_bytes()
        answer = idiograph_routes.api_themes({"workbook": str(work)})
        check("/api/themes answers with the cards, the board and the case by its pseudonym",
              answer["case"] == "Juno" and answer["workbook"] == work.name and len(answer["cards"]) == lines
              and answer["sheets"] == [DEMO_SHEET, "2d"] and answer["schema"] == themes_mod.SCHEMA
              and answer["demo"] is False and answer["versions"][0]["id"] == "v1")
        check("the old name for the field, path, is read as well",
              len(idiograph_routes.api_themes({"path": str(work)})["cards"]) == lines)

        def page_body(state, groups, discarded):
            return {**state["version"], "cards": {c["key"]: {"x": c["x"], "y": c["y"], "text": c["text"]}
                                                  for c in state["cards"]},
                    "groups": groups, "discarded": discarded}

        k = [c["key"] for c in answer["cards"]]
        groups = [{"id": "g1", "label": "Mornings first", "members": [k[0], k[1]], "x": 0, "y": -40},
                  {"id": "g2", "label": "", "members": [k[2]], "x": 300, "y": -40},
                  {"id": "g3", "label": "Over both", "members": ["g1", "g2"], "x": 0, "y": -90}]
        saved = idiograph_routes.api_themes_save({"workbook": str(work), "version": page_body(answer, groups, [k[3]])})
        path = themes_mod.themes_path(work)
        data = json.loads(path.read_text(encoding="utf-8"))
        check("the themes file sits beside the progress file, named for the workbook's stem",
              path.parent == rounds_mod.progress_path(work).parent and path.name == f"{work.stem}.themes.json"
              and path.exists(), str(path.relative_to(scratch)))
        check("the file carries the case, the workbook, the schema, the current board and when",
              data["case"] == "Juno" and data["workbook"] == work.name and data["schema"] == themes_mod.SCHEMA
              and data["current"] == "v1" and len(data["boards"]) == 1
              and bool(ISO_OFFSET.match(data["created"])) and bool(ISO_OFFSET.match(data["updated"]))
              and saved["saved"] is True, f"updated {data['updated']}")
        v = data["boards"][0]
        check("a board carries an id, a name, a note, its times, the cards, the groups, the discards and the picks",
              set(v) == {"id", "name", "note", "created", "updated", "cards", "groups", "discarded", "picks"}
              and v["name"] == "Board 1" and v["note"] == "" and bool(ISO_OFFSET.match(v["updated"]))
              and all(set(c) == {"x", "y", "text"} for c in v["cards"].values()))
        back = idiograph_routes.api_themes({"workbook": str(work)})
        check("a label over labels comes back exactly as it was written",
              [(g["id"], g["members"]) for g in back["groups"]]
              == [("g1", [k[0], k[1]]), ("g2", [k[2]]), ("g3", ["g1", "g2"])]
              and back["saved"] is True)
        check("a label left blank is saved as Untitled",
              [g["label"] for g in back["groups"]] == ["Mornings first", "Untitled", "Over both"])
        idiograph_routes.api_themes_save({"workbook": str(work), "version": page_body(
            back, [{"id": "g1", "label": "Mornings first", "members": [k[0], k[1], k[3]], "x": 0, "y": 0}], [k[1], k[3]])})
        kept = json.loads(path.read_text(encoding="utf-8"))["boards"][0]
        check("a discarded card belongs to no group, whatever the page sent",
              kept["groups"][0]["members"] == [k[0]] and kept["discarded"] == [k[1], k[3]])
        check("the board keeps the time it was made, and the file the time it was first written",
              kept["created"] == v["created"] and json.loads(path.read_text(encoding="utf-8"))["created"] == data["created"])
        check("the canvas never writes the workbook, opening or saving", work.read_bytes() == before)

        # the pseudonym alone, from a GRAVITY-shaped folder, and never its second part
        folder = "P9 - {}-{}".format("Alpha", "Beta")
        gravity = demo_copy(root, folder, "P9 Alpha - EN & ES.xlsx")
        shown = idiograph_routes.api_themes({"workbook": str(gravity)})
        idiograph_routes.api_themes_save({"workbook": str(gravity), "version": page_body(shown, [], [])})
        text = themes_mod.themes_path(gravity).read_text(encoding="utf-8")
        check("a GRAVITY case is named by its pseudonym, on the screen and in the file",
              shown["case"] == "P9 - Alpha" and json.loads(text)["case"] == "P9 - Alpha")
        check("the second part of the folder name reaches neither the file nor what the page draws",
              "Beta" not in text and not any("Beta" in s for s in json_strings(shown, skip_keys=("path",))))

        # outside the root, the field missing
        outside = demo_copy(scratch, "themes-elsewhere", "Juno - EN & ES.xlsx")
        refused = []
        for call in (idiograph_routes.api_themes, idiograph_routes.api_themes_save):
            try:
                call({"workbook": str(outside), "version": {}})
            except server_mod.OutsideRoot:
                refused.append(call.__name__)
        check("a workbook outside the root is refused by both routes",
              refused == ["api_themes", "api_themes_save"] and not themes_mod.themes_path(outside).exists())
        try:
            idiograph_routes.api_themes({})
            missing_field = False
        except KeyError as exc:
            missing_field = exc.args == ("workbook",)
        check("a request with no workbook names the field it lacks", missing_field)

        # Excel's lock file beside it changes nothing: the canvas only reads
        lock = wb_mod.lock_file(work)
        lock.write_text("", encoding="utf-8")
        try:
            locked = idiograph_routes.api_themes({"workbook": str(work)})
            check("a workbook Excel has open is read, with no lock error and nothing said about it",
                  len(locked["cards"]) == lines and "error" not in locked
                  and not any("Excel" in s for s in json_strings(locked)))
        finally:
            lock.unlink()

        # a themes file that cannot be read is refused rather than written over
        broken = demo_copy(root, "Broken", "Juno - EN & ES.xlsx")
        bad = themes_mod.themes_path(broken)
        bad.parent.mkdir(parents=True, exist_ok=True)
        bad.write_text("{ not json", encoding="utf-8")
        outcomes = []
        for call in (lambda: idiograph_routes.api_themes({"workbook": str(broken)}),
                     lambda: idiograph_routes.api_themes_save({"workbook": str(broken), "version": {}})):
            try:
                call()
                outcomes.append("answered")
            except WorkbookError:
                outcomes.append("refused")
        check("a themes file that cannot be read is refused, and left as it was",
              outcomes == ["refused", "refused"] and bad.read_text(encoding="utf-8") == "{ not json")

        # the two routes over HTTP, and the answer a server from before them gives
        httpd = http.server.ThreadingHTTPServer(("127.0.0.1", 0), server_mod.Handler)
        threading.Thread(target=httpd.serve_forever, kwargs={"poll_interval": 0.05}, daemon=True).start()

        def post(route, body):
            req = urllib.request.Request(f"http://127.0.0.1:{httpd.server_address[1]}{route}",
                                         data=json.dumps(body).encode("utf-8"),
                                         headers={"Content-Type": "application/json"})
            try:
                with urllib.request.urlopen(req, timeout=10) as r:
                    return r.status, json.loads(r.read())
            except urllib.error.HTTPError as exc:
                return exc.code, json.loads(exc.read())

        held = {r: server_mod.ROUTES.pop(r) for r in ("/api/themes", "/api/themes-save")}
        try:
            old = [post(r, {"workbook": str(work)}) for r in held]
        finally:
            server_mod.ROUTES.update(held)
        try:
            now = post("/api/themes", {"workbook": str(work)})
            far = post("/api/themes", {"workbook": str(outside)})
        finally:
            httpd.shutdown()
            httpd.server_close()
        check("over HTTP the canvas answers, and a path outside the root is a 403",
              now[0] == 200 and len(now[1]["cards"]) == lines and far[0] == 403)
        check("a server from before the routes answers with the line the page turns into the restart line",
              all(code == 404 and body == {"error": "No such endpoint.", "code": "no_endpoint"} for code, body in old))
    finally:
        server_mod.ROOT_OVERRIDE = saved_root
    check("the two routes are in the dispatch table",
          server_mod.ROUTES.get("/api/themes") is idiograph_routes.api_themes
          and server_mod.ROUTES.get("/api/themes-save") is idiograph_routes.api_themes_save)

    # ── E. normalising what the page sends
    loose = themes_mod.normalise({
        "cards": {"a:1:0": {"x": 1.6, "y": "2", "text": "A"}, "a:2:0": {"x": 0, "y": 0, "text": "B"}},
        "groups": [{"id": "g1", "members": ["a:1:0", "g2", "nowhere"]},
                   {"id": "g2", "members": ["g1", "a:1:0", "a:2:0", "g2"]},
                   {"id": "g1", "members": ["a:2:0"]}],
        "discarded": ["a:2:0", "a:2:0", "nowhere"]})
    check("a member belongs to one group, a loop is broken, and what does not exist goes",
          [(g["id"], g["members"]) for g in loose["groups"]] == [("g1", ["a:1:0"]), ("g2", ["g1"])]
          and loose["discarded"] == ["a:2:0"] and loose["cards"]["a:1:0"] == {"x": 2, "y": 2, "text": "A"})
    check("a changed card keeps the text it was made with and the line as it reads now beside it",
          themes_mod.normalise({"cards": {"a:1:0": {"x": 0, "y": 0, "text": "old", "live": "new"}}})
          ["cards"]["a:1:0"] == {"x": 0, "y": 0, "text": "old", "live": "new"})

    # ── F. the page: its file, the ways in, the keys, the restart line
    static = server_mod.HERE / "static"
    page = support.page_text()
    app = support.text("family/static/shell.js", "apps/idiograph/static/distil.js")
    js = support.text("apps/idiograph/static/themes.js")
    src = support.source("apps/idiograph/themes.py").read_text(encoding="utf-8")
    fn = lambda text, name: text.split(f"function {name}(", 1)[1].split("\n}", 1)[0]
    check("a PETs half on every annotated case's card, the demo's included, and PETs on every annotated row under Files",
          "if (!raw) {" in fn(app, "renderFiles") and "openThemesIn(item.path, item.case)" in fn(app, "renderFiles")
          and "else if (what === 'pets') openThemesIn(p.path, p.case);" in fn(app, "drawCards"))
    check("and in the turn screen's top bar, with p beside it, the PETs step of Distil's steps since 18 October "
          "(area 177), where it was a tool among View and Guidance",
          'id="es-step-pets"' in page.split('<section id="work"', 1)[1].split("</section>", 1)[0]
          and "$('es-step-pets').onclick = () => esStep('pets');" in app
          and "if (step === 'pets') navGo(again, () => openThemes(S.data.path, 'work', S.data.name" in fn(app, "esStep")
          and "if (key === 'p' && !$('work').hidden && S.data" in fn(app, "distilKeys"))
    check("the turn screen saves a field typed into before it goes, and the back arrow returns to it",
          "await commit(current(), false);" in fn(app, "openThemes") and "focusEntry();" in fn(app, "openThemes")
          and "loadLibrary()" in fn(app, "openThemes") and "if (TH.back) await TH.back();" in fn(js, "themesLeave"))
    check("the path names the case by what the server sends, the pseudonym (its name alone in the chooser since option C "
          "of the bars, 26 October 2026)",
          "thWhoDraw(data.case || TH.label);" in fn(js, "themesOpen"))
    check("a server from before the screen gets the restart line and nothing else",
          "thNote(needsRestart(err) ? RESTART_LINE : err.message, !needsRestart(err));\n    return;" in fn(js, "themesOpen")
          and "TH.live = true;" in fn(js, "themesOpen")
          and fn(js, "themesOpen").index("needsRestart") < fn(js, "themesOpen").index("TH.live = true;"))
    check("the screen talks to its six routes, the settings for its limit and the recording's, its project for PET labels, the statements' export for the interviewer notes (settingsplit, 5 November), and writes a workbook through one route alone, a statement edited in place (124, 208)",
          sorted(set(re.findall(r"'(/api/[a-z-]+)'", js)))
          == ["/api/board-order", "/api/codes", "/api/codes-ops", "/api/edit-statement", "/api/export", "/api/gets", "/api/gets-ai", "/api/gets-boards", "/api/gets-cases", "/api/gets-ops", "/api/gets-save",
              "/api/gets-settings", "/api/gets-trail", "/api/project", "/api/settings", "/api/stamp", "/api/themes", "/api/themes-ai", "/api/themes-boards", "/api/themes-cases",
              "/api/themes-export", "/api/themes-save", "/api/themes-versions"]
          and js.count("TH_EDIT_ROUTE") == 3
          and "api(`/api/audio?${" in js and "/api/commit" not in js and "/api/rows" not in js)
    check("its keys are taken before app.js hears them, and its undo is its own",
          "window.addEventListener('keydown', thKeyDown, true);" in js and "e.stopPropagation();" in fn(js, "thKeyDown")
          and "S.undoStack" not in js and "if (TH.undoPath !== canvas) { TH.undo = []; TH.redo = []; TH.undoPath = canvas; }" in js)
    check("the save waits about 300 ms after the last act, and one save follows another",
          "setTimeout(() => { TH.saveTimer = null; thSave(); }, 300);" in js and "TH.again = true;" in fn(js, "thSave"))
    check("themes.py opens the workbook read-only, never against the lock, and never saves it",
          "load_workbook(workbook, read_only=True" in src and "guard_lock" not in src
          and "book.save" not in src and "save_turn" not in src)

    node = shutil.which("node")
    if not node:
        return skip("the canvas's model in node", "no node on this machine")
    run = subprocess.run([node, "--check", str(support.source("apps/idiograph/static/themes.js"))], capture_output=True, text=True, encoding="utf-8")
    script = scratch / "themes-model.js"
    script.write_text(support.i18n_js() + js + r"""
const size = (item) => (item.startsWith('g') ? { w: 100, h: 20 } : { w: 200, h: 80 });
const card = (x, y, text) => ({ x, y, text });
const v = { cards: { 'a:1:0': card(0, 0, 'A'), 'a:2:0': card(220, 0, 'B'), 'a:3:0': card(0, 300, 'C'),
  'a:4:0': card(600, 600, 'D') }, groups: [], discarded: [] };
const out = {};
// every answer is copied as it is taken, because later steps change the same arrays
const keep = (x) => JSON.parse(JSON.stringify(x));
const g1 = thMakeGroup(v, ['a:1:0', 'a:2:0'], '');
const g2 = thMakeGroup(v, ['a:3:0'], 'Three');
out.made = keep([g1, thGroup(v, g1).label, thGroup(v, g1).members, g2]);
const g3 = thMakeGroup(v, [g1, g2, 'a:1:0'], 'Over');
out.over = keep(thGroup(v, g3).members);
const sub = thMakeGroup(v, ['a:2:0'], 'Inside');
out.sub = keep([thGroup(v, g1).members, thParents(v)[sub]]);
thDelete(v, sub);
out.freed = keep(thGroup(v, g1).members);
out.cycle = thJoin(v, [g3], g1);
const lay = thLayout(v, size, null);
out.label = [thGroup(v, g1).x, thGroup(v, g1).y];
out.upper = keep([thGroup(v, g3).x, thGroup(v, g3).y, lay[g3].body]);
const moving = thMoving(v, new Set(['a:3:0']), new Set());
out.followed = moving.has(g2);
const twoMoving = thMoving(v, new Set(['a:1:0']), new Set());
out.alone = [twoMoving.has(g1), twoMoving.size];
v.cards['a:1:0'].x = 30;
out.near = keep(thDrop(v, twoMoving, undefined, null));
v.cards['a:1:0'].x = 1500;
const lay2 = thLayout(v, size, twoMoving);
out.far = keep(thDrop(v, twoMoving, undefined, thFrameAt(v, lay2, { x: 1600, y: 40 }, twoMoving)));
out.afterFar = keep(thGroup(v, g1).members);
const join = thMoving(v, new Set(['a:4:0']), new Set());
out.join = keep(thDrop(v, join, g1, null));
const snap = thSnap(v, new Set());
thDiscard(v, ['a:2:0']);
out.discard = keep([thGroup(v, g1).members, v.discarded, thCounts(v)]);
thRestore(v, 'a:2:0', 10.4, 20.6);
out.restored = keep([v.discarded, v.cards['a:2:0'].x, v.cards['a:2:0'].y, thParents(v)['a:2:0'] === undefined]);
thPut(v, snap);
out.put = keep([thGroup(v, g1).members, v.discarded]);
v.cards['a:4:0'].changed = true; v.cards['a:4:0'].stored = 'D before';
const body = thBody(v, { id: 'v1', name: 'Board 1', note: '', created: 'c', updated: 'u' });
out.body = [body.cards['a:4:0'], body.groups.length, Object.keys(body)];
const nine = thTints({ cards: {}, discarded: [], groups: ['g1', 'g8', 'g9'].map((id) => ({ id, members: [] })) });
out.hue = [nine.g1.hue, nine.g8.hue, nine.g9.hue];
console.log(JSON.stringify(out));
""", encoding="utf-8")
    run = subprocess.run([node, str(script)], capture_output=True, text=True, encoding="utf-8")
    if run.returncode != 0:
        return check("the canvas's model runs in node", False, run.stderr.strip()[:300])
    out = json.loads(run.stdout)
    check("g over two cards makes Untitled, the next id, holding them",
          out["made"] == ["g1", "Untitled", ["a:1:0", "a:2:0"], "g2"], str(out["made"]))
    check("g over labels makes a label over labels, and a card inside one of them stays inside it",
          out["over"] == ["g1", "g2"], str(out["over"]))
    check("cards that all sat in one theme make a group inside it, in their place",
          out["sub"] == [["a:1:0", "g4"], "g1"], str(out["sub"]))
    check("deleting a label frees what it held into the group above, where it stood",
          out["freed"] == ["a:1:0", "a:2:0"], str(out["freed"]))
    check("a label never joins a group it holds", out["cycle"] == [])
    check("moving every member of a group moves its label, moving one of two does not",
          out["followed"] is True and out["alone"] == [False, 1], str(out["alone"]))
    check("a member dropped near its cluster stays, and dropped far from it stays too",
          out["near"] == {"joined": [], "left": [], "dest": None} and out["far"] == {"joined": [], "left": [], "dest": None}
          and out["afterFar"] == ["a:1:0", "a:2:0"], f"{out['near']} {out['far']}")
    check("a card dropped on a cluster joins it", out["join"] == {"joined": ["a:4:0"], "left": [], "dest": "g1"})
    check("a discarded card leaves its group and is counted, and comes back unplaced",
          out["discard"][0] == ["a:1:0", "a:4:0"] and out["discard"][1] == ["a:2:0"]
          and out["discard"][2] == {"placed": 3, "unplaced": 0, "discarded": 1, "missing": 0}
          and out["restored"] == [[], 10, 21, True], f"{out['discard']} {out['restored']}")
    check("a snapshot put back restores the groups and the discards",
          out["put"] == [["a:1:0", "a:2:0", "a:4:0"], []], str(out["put"]))
    check("a changed card goes to the file with its stored text and the live line beside it",
          out["body"][0] == {"x": 600, "y": 600, "text": "D before", "live": "D"}
          and out["body"][2] == ["id", "name", "note", "created", "updated", "v", "cards", "groups", "discarded", "picks"])
