from __future__ import annotations

import json
import re
import shutil
from pathlib import Path

from workbook import WorkbookError

from . import support

from .support import DEMO_SHEET, check, demo_copy, skip
import idiograph_routes


def test_themes_boards(scratch):
    print("\n44. Themes, boards: the word, a schema 1 file read as boards, copy to board, each board's "
          "history, and the three principles")
    import http.server
    import subprocess
    import threading
    import urllib.error
    import urllib.request
    import server as server_mod
    import themes as themes_mod

    root = scratch / "boards-root"
    work = demo_copy(root, "Juno", "Juno - EN & ES.xlsx")
    path = themes_mod.themes_path(work)
    read = themes_mod.read_cards(work)
    texts = {c["key"]: c["text"] for c in read["cards"]}
    K = lambda row, line: f"{DEMO_SHEET}:{row}:{line}"

    def file():
        return json.loads(path.read_text(encoding="utf-8"))

    def body_of(state, groups, discarded=(), picks=None, **meta):
        return {**state["version"], **meta,
                "cards": {c["key"]: {"x": c["x"], "y": c["y"], "text": c["text"]} for c in state["cards"]},
                "groups": groups, "discarded": list(discarded), "picks": picks or {}}

    saved_root = server_mod.ROOT_OVERRIDE
    server_mod.ROOT_OVERRIDE = str(root)
    try:
        # ── A. a schema 1 file, written by hand, read as boards
        old = demo_copy(root, "Old", "Juno - EN & ES.xlsx")
        old_path = themes_mod.themes_path(old)
        old_path.parent.mkdir(parents=True, exist_ok=True)
        blank = themes_mod.blank_version(read["cards"])
        mornings = [{"id": "g1", "label": "Mornings", "members": [K(3, 0), K(3, 1)], "x": 0, "y": 0}]
        note = ("Proposed by Haiku 4.5 from Version 1 on 2 October 2026 at 12:02, up to 5 themes. 1 theme, "
                "2 placed, 0 discarded, 16 unplaced.")
        schema1 = {"schema": 1, "case": "Old", "workbook": old.name, "created": "2026-10-01T09:00:00+01:00",
                   "updated": "2026-10-01T10:00:00+01:00", "current": "v3", "versions": [
                       dict(blank, id="v1", name="Version 1", groups=mornings),
                       dict(blank, id="v2", name="Version 1 copy"),
                       dict(blank, id="v3", name="AI proposal 2", note=note, groups=mornings),
                       dict(blank, id="v4", name="Mornings apart")]}
        old_path.write_text(json.dumps(schema1, indent=1) + "\n", encoding="utf-8")
        old_bytes = old_path.read_bytes()
        loaded = themes_mod.load(old)
        check("a schema 1 file is read as schema 2, its boards under boards and the old key gone",
              loaded["schema"] == 2 and "versions" not in loaded and len(loaded["boards"]) == 4
              and loaded["current"] == "v3" and loaded["created"] == schema1["created"])
        check("Version N becomes Board N, a copy's name too, and AI proposal N becomes AI board N",
              [b["name"] for b in loaded["boards"]] == ["Board 1", "Board 1 copy", "AI board 2", "Mornings apart"],
              str([b["name"] for b in loaded["boards"]]))
        check("an AI board's note names the board it came from the new way, and a name he gave stays",
              loaded["boards"][2]["note"].startswith("Proposed by Haiku 4.5 from Board 1 on ")
              and loaded["boards"][3]["name"] == "Mornings apart")
        shown = idiograph_routes.api_themes({"workbook": str(old)})
        check("the screen opens a schema 1 file with the new names, and opening writes nothing",
              [v["name"] for v in shown["versions"]] == ["Board 1", "Board 1 copy", "AI board 2", "Mornings apart"]
              and shown["version"]["name"] == "AI board 2" and shown["history"] == []
              and old_path.read_bytes() == old_bytes)
        column, _ = themes_mod.pet_table(old_path)
        text, _ = themes_mod.draft_markdown(old, "Old")
        check("a schema 1 file exports as it stands, its boards found under the old key",
              column.get(K(3, 0)) == "Mornings" and text.startswith("# Old: PET grouping draft (AI board 2)")
              and old_path.read_bytes() == old_bytes)
        check("the next AI board takes the next free number, as New board names one, after the renamed ones (184)",
              themes_mod.proposal_name(loaded["boards"]) == "Board 5")
        idiograph_routes.api_themes_save({"workbook": str(old), "version": body_of(shown, mornings)})
        written = json.loads(old_path.read_text(encoding="utf-8"))
        check("the next save writes schema 2, boards and the new names, the other boards as they were",
              written["schema"] == 2 and "versions" not in written
              and [b["name"] for b in written["boards"]] == ["Board 1", "Board 1 copy", "AI board 2", "Mornings apart"]
              and written["boards"][0]["groups"] == mornings and written["created"] == schema1["created"]
              and written["current"] == "v3")

        # ── B. a board copied onto another
        first = idiograph_routes.api_themes({"workbook": str(work)})
        source_groups = [{"id": "g1", "label": "Mornings", "members": [K(3, 0), K(3, 1), "g2"], "x": 0, "y": 0},
                         {"id": "g2", "label": "Rain", "members": [K(13, 0), K(13, 1)], "x": 0, "y": 0},
                         {"id": "g3", "label": "Evenings", "members": [K(5, 0), K(5, 1)], "x": 0, "y": 0}]
        source_picks = {"g1": [K(13, 0)], "g2": [K(13, 0)]}
        idiograph_routes.api_themes_save({"workbook": str(work), "version": body_of(first, source_groups, [K(11, 2)], source_picks)})
        idiograph_routes.api_themes_boards({"workbook": str(work), "op": "revision", "id": "v1", "name": "Mornings first"})
        dup = idiograph_routes.api_themes_versions({"workbook": str(work), "op": "duplicate", "id": "v1"})
        check("a duplicate starts with a history of its own, empty, the board it copies keeping its own",
              dup["current"] == "v2" and "history" not in file()["boards"][1] and dup["history"] == []
              and [r["name"] for r in file()["boards"][0]["history"]] == ["Mornings first"])
        target_groups = [{"id": "g1", "label": "Walks", "members": [K(3, 0), K(7, 0)], "x": 0, "y": 0},
                         {"id": "g2", "label": "Only one", "members": [K(3, 1)], "x": 0, "y": 0},
                         {"id": "g3", "label": "Holder", "members": ["g2"], "x": 0, "y": 0},
                         {"id": "g4", "label": "Evenings", "members": [K(5, 0), K(5, 1)], "x": 0, "y": 0}]
        idiograph_routes.api_themes_save({"workbook": str(work), "version": body_of(dup, target_groups, [K(13, 1), K(11, 2)])})
        before_v1 = file()["boards"][0]
        before_v2 = themes_mod.board_state(file()["boards"][1])
        answer = idiograph_routes.api_themes_boards({"workbook": str(work), "op": "copy", "id": "v1", "group": "g1", "to": "v2"})
        v2 = themes_mod.normalise(file()["boards"][1])
        by_label = {g["label"]: g for g in v2["groups"]}
        new, sub = by_label.get("Mornings"), by_label.get("Rain")
        check("the copy arrives as a fresh theme, its label and its sub-theme in the same shape",
              new is not None and sub is not None and new["id"] not in ("g1", "g2", "g3", "g4")
              and sub["id"] not in ("g1", "g2", "g3", "g4") and new["members"] == [K(3, 0), K(3, 1), sub["id"]]
              and sub["members"] == [K(13, 0), K(13, 1)], str([(g["id"], g["label"], g["members"]) for g in v2["groups"]]))
        check("every card of the copy leaves the group that held it there, and a group that keeps some keeps the rest",
              by_label["Walks"]["members"] == [K(7, 0)] and by_label["Evenings"]["members"] == [K(5, 0), K(5, 1)])
        check("a group the copy empties goes, and so does the group above it left with none",
              "Only one" not in by_label and "Holder" not in by_label)
        check("a card of the copy comes out of the bin there, and the rest of the bin stays",
              K(13, 1) not in v2["discarded"] and K(11, 2) in v2["discarded"])
        check("the copy carries its picks, each under its new label",
              v2["picks"].get(new["id"]) == [K(13, 0)] and v2["picks"].get(sub["id"]) == [K(13, 0)])
        held = [m for g in v2["groups"] for m in g["members"] if m in v2["cards"]]
        check("nothing is duplicated: a card sits in one group at most and the board holds the same cards",
              len(held) == len(set(held)) and set(v2["cards"]) == set(texts) and len(v2["cards"]) == len(texts))
        last = file()["boards"][1]["history"][-1]
        check("before the copy the target keeps a revision of itself, named for what came from where",
              last["name"] == "Before Mornings copied from Board 1" and last["auto"] is False
              and last["state"] == before_v2 and answer["revision"]["id"] == last["id"])
        check("the source board is exactly as it was, and the copy leaves the current board current",
              file()["boards"][0] == before_v1 and answer["current"] == "v2" == file()["current"]
              and answer["copied"] == {"label": "Mornings", "group": new["id"], "to": "v2", "to_name": "Board 1 copy",
                                       "from": "Board 1"})
        drawn = themes_mod.layout_boxes(v2)
        mine = {new["id"], sub["id"]}
        copy_keys = {K(3, 0), K(3, 1), K(13, 0), K(13, 1)}
        own = [b for k, b in drawn["cards"].items() if k in copy_keys] + [drawn["labels"][g] for g in mine]
        others = ([b for k, b in drawn["cards"].items() if k not in copy_keys]
                  + [b for g, b in drawn["labels"].items() if g not in mine]
                  + [b for g, b in drawn["frames"].items() if g not in mine])
        near = [(a, b) for a in own + [drawn["frames"][new["id"]]] for b in others
                if themes_mod.clash(a, b, themes_mod.MARGIN - 1)]
        check("the copy is laid out as a blob a margin clear of every card, label and frame already there",
              not near, f"{len(near)} too near")
        src = themes_mod.normalise(before_v1)
        was_read = [m for m in themes_mod.theme_order(src, "g1") if m in src["cards"]]
        rows = themes_mod.read_order({k: (v2["cards"][k]["x"], v2["cards"][k]["y"]) for k in (K(3, 0), K(3, 1))})
        check("its cards keep the order they read in on the board they came from", rows == was_read, f"{was_read} {rows}")

        def refused(call):
            before = path.read_bytes()
            try:
                call()
            except WorkbookError as exc:
                return str(exc) if path.read_bytes() == before else ""
            return ""

        boards = lambda **b: idiograph_routes.api_themes_boards({"workbook": str(work), **b})
        check("a copy onto its own board, onto a board not there or of a theme not there is refused and writes nothing",
              "already" in refused(lambda: boards(op="copy", id="v1", group="g1", to="v1"))
              and "no longer" in refused(lambda: boards(op="copy", id="v1", group="g1", to="v9"))
              and "no longer" in refused(lambda: boards(op="copy", id="v1", group="g99", to="v2"))
              and "not something a board can do" in refused(lambda: boards(op="merge"))
              and "no longer in the board's history" in refused(lambda: boards(op="view", id="v2", revision="r99")))

        # from a revision on view, back into the board it belongs to
        rid = last["id"]
        bytes_now = path.read_bytes()
        seen = boards(op="view", id="v2", revision=rid)
        check("a revision on view comes as the canvas draws it, and showing it writes nothing",
              [g["label"] for g in seen["groups"]] == ["Walks", "Only one", "Holder", "Evenings"]
              and seen["revision"]["id"] == rid and len(seen["cards"]) == len(texts) and K(13, 1) in seen["discarded"]
              and path.read_bytes() == bytes_now)
        back = boards(op="copy", id="v2", revision=rid, group="g2", to="v2")
        v2 = themes_mod.normalise(file()["boards"][1])
        by_label = {g["label"]: g for g in v2["groups"]}
        check("a theme of a revision copies into its own board, and the card leaves the theme that held it",
              by_label["Only one"]["members"] == [K(3, 1)] and K(3, 1) not in by_label["Mornings"]["members"]
              and file()["boards"][1]["history"][-1]["name"].startswith("Before Only one copied from Board 1 copy at ")
              and back["copied"]["to"] == "v2")

        # ── C. each board's history
        made = boards(op="revision", id="v2", name="  Before   the walk ")
        check("a revision kept by hand keeps its name, and comes first in the history the screen gets",
              made["revision"]["name"] == "Before the walk" and made["revision"]["auto"] is False
              and made["history"][0] == made["revision"]
              and all(set(r) - {"kind", "slots"} == {"id", "at", "name", "auto"} for r in made["history"])
              and "kind" not in made["revision"])
        named = made["revision"]["id"]
        unnamed = boards(op="revision")["revision"]
        check("a revision with no name is kept too, on the current board", unnamed["name"] == "" and not unnamed["auto"])
        state = idiograph_routes.api_themes({"workbook": str(work)})
        page = body_of(state, state["groups"], state["discarded"], state["picks"])
        quiet = idiograph_routes.api_themes_save({"workbook": str(work), "version": page, "revision": "auto"})
        check("an automatic revision is not made when the board is as its last revision has it",
              "revision" not in quiet and len(file()["boards"][1]["history"]) == len(made["history"]) + 1)
        # each save carries the version the last one wrote, as the page's own do
        page["v"] = quiet["version"]["v"]
        page["cards"][K(9, 0)]["x"] += 400
        moved = idiograph_routes.api_themes_save({"workbook": str(work), "version": page})
        kept_state = themes_mod.board_state(file()["boards"][1])
        page["v"] = moved["version"]["v"]
        page["cards"][K(9, 0)]["x"] += 400
        auto = idiograph_routes.api_themes_save({"workbook": str(work), "version": page, "revision": "auto"})
        r = file()["boards"][1]["history"][-1]
        check("once the board has changed, the timer's save keeps it as it stood before, at the time of that save",
              auto["revision"]["auto"] is True and r["state"] == kept_state and r["at"] == auto["updated"]
              and auto["history"][0]["id"] == r["id"])
        page["v"] = auto["version"]["v"]
        again = idiograph_routes.api_themes_save({"workbook": str(work), "version": page, "revision": "auto"})
        page["v"] = again["version"]["v"]
        nothing =idiograph_routes.api_themes_save({"workbook": str(work), "version": page, "revision": "auto"})
        check("and only once for each change, compared by a stable hash of the state",
              again["revision"]["auto"] and "revision" not in nothing
              and themes_mod.state_hash({"b": 1, "a": [1, 2]}) == themes_mod.state_hash({"a": [1, 2], "b": 1}))
        check("a save from the page, which sends no history, keeps the board's history",
              len(file()["boards"][1]["history"]) >= 6 and "history" not in page)

        holder = {}
        for i in range(60):
            themes_mod.add_revision(holder, auto=True, state={"cards": {}, "groups": [], "discarded": [], "picks": {"n": [str(i)]}})
            if i in (5, 30):
                themes_mod.add_revision(holder, name=f"Named {i}", state={"cards": {}, "groups": [], "discarded": [], "picks": {}})
        autos = [x for x in holder["history"] if x["auto"]]
        check("every named revision is kept, and the last 48 automatic ones, the oldest going first",
              len(autos) == themes_mod.AUTO_KEEP == 48 and [x["name"] for x in holder["history"] if not x["auto"]] == ["Named 5", "Named 30"]
              and autos[0]["state"]["picks"]["n"] == ["12"] and autos[-1]["state"]["picks"]["n"] == ["59"])

        before_restore = themes_mod.board_state(file()["boards"][1])
        target = next(x for x in file()["boards"][1]["history"] if x["id"] == named)
        restored = boards(op="restore", id="v2", revision=named)
        board2 = file()["boards"][1]
        first_back = board2["history"][-1]
        check("restore keeps the board as it stood first, named Before restoring and the time restored",
              first_back["name"] == f"Before restoring {themes_mod.when_said(target['at'])}"
              and re.fullmatch(r"Before restoring \d\d:\d\d", first_back["name"]) is not None
              and first_back["state"] == before_restore and restored["revision"]["id"] == first_back["id"])
        check("then the revision's state is the board's, and the answer draws it",
              themes_mod.board_state(board2) == target["state"] and restored["restored"]["id"] == named
              and {c["key"]: c["x"] for c in restored["cards"]} == {k: c["x"] for k, c in target["state"]["cards"].items()})
        # the times in this machine's own zone, as the History tab says them, so the check reads the
        # same on a machine kept to UTC, as GitHub's are, as on one in London (14 October)
        from datetime import datetime as clock
        local = lambda *at: clock(*at).astimezone()
        evening = local(2026, 10, 2, 18, 0)
        check("when a revision was made is said the way the History tab says it",
              themes_mod.when_said(local(2026, 10, 2, 12, 4).isoformat(), evening) == "12:04"
              and themes_mod.when_said(local(2026, 10, 1, 12, 4).isoformat(), evening) == "1 October 12:04"
              and themes_mod.when_said(local(2025, 12, 31, 12, 4).isoformat(), evening) == "31 December 2025 12:04")

        # the size of a history: a revision of a hundred statements, and the file with 48 of them
        hundred = {f"{DEMO_SHEET}:{100 + i}:{i % 3}": {"x": -2000 + 37 * i, "y": 1500 - 29 * i, "text": "w" * 60}
                   for i in range(100)}
        keys100 = list(hundred)
        dozen = [{"id": f"g{n + 1}", "label": "A grounded title of about seven words long",
                  "members": keys100[n * 8:(n + 1) * 8], "x": -1200, "y": -800} for n in range(12)]
        big = {"cards": hundred, "groups": dozen, "discarded": keys100[96:],
               "picks": {f"g{n + 1}": [keys100[n * 8].rsplit(":", 1)[0] + ":0"] for n in range(6)}}
        one = themes_mod.add_revision({}, auto=True, state=themes_mod.board_state(big))
        size = len(json.dumps(one, ensure_ascii=False, separators=(",", ":")).encode("utf-8"))
        holder = dict(themes_mod.normalise(big), id="v1", name="Board 1")
        for i in range(48):
            state48 = themes_mod.board_state(big)
            state48["cards"][keys100[0]]["x"] = i
            themes_mod.add_revision(holder, auto=True, state=state48)
        rendered = themes_mod.render({"schema": 2, "boards": [holder]})
        check("a revision of a hundred statements of sixty characters is under 15 KB, and 48 of them under a megabyte",
              size < 15000 and len(rendered.encode("utf-8")) < 1_000_000, f"{size} bytes, {len(rendered.encode('utf-8'))} in all")
        check("each revision is one line of its own in the file, the rest indented as before",
              rendered.count('"state":') == 48 and sum(1 for l in rendered.splitlines() if '"state":' in l) == 48
              and json.loads(rendered)["boards"][0]["history"][0]["state"]["picks"] == big["picks"]
              and '\n   "name": "Board 1",' in rendered)

        # ── D. the route
        outside = demo_copy(scratch, "boards-elsewhere", "Juno - EN & ES.xlsx")
        try:
            idiograph_routes.api_themes_boards({"workbook": str(outside), "op": "revision"})
            far = False
        except server_mod.OutsideRoot:
            far = True
        httpd = http.server.ThreadingHTTPServer(("127.0.0.1", 0), server_mod.Handler)
        threading.Thread(target=httpd.serve_forever, kwargs={"poll_interval": 0.05}, daemon=True).start()

        def post(route, payload):
            req = urllib.request.Request(f"http://127.0.0.1:{httpd.server_address[1]}{route}",
                                         data=json.dumps(payload).encode("utf-8"),
                                         headers={"Content-Type": "application/json"})
            try:
                with urllib.request.urlopen(req, timeout=10) as resp:
                    return resp.status, json.loads(resp.read())
            except urllib.error.HTTPError as exc:
                return exc.code, json.loads(exc.read())

        held_route = server_mod.ROUTES.pop("/api/themes-boards")
        try:
            stale = post("/api/themes-boards", {"workbook": str(work), "op": "revision"})
        finally:
            server_mod.ROUTES["/api/themes-boards"] = held_route
        try:
            fresh = post("/api/themes-boards", {"workbook": str(work), "op": "view", "id": "v2", "revision": named})
        finally:
            httpd.shutdown()
            httpd.server_close()
        check("the boards route is in the dispatch table, answers over HTTP and refuses a workbook outside the root",
              server_mod.ROUTES.get("/api/themes-boards") is idiograph_routes.api_themes_boards and far
              and fresh[0] == 200 and fresh[1]["revision"]["id"] == named and not themes_mod.themes_path(outside).exists())
        check("a server from before it answers with the line the page turns into the restart line",
              stale == (404, {"error": "No such endpoint.", "code": "no_endpoint"}))

        # ── E. the export names its file for the board
        plain = demo_copy(root, "Plain", "Juno - EN & ES.xlsx")
        drafted = themes_mod.write_draft(plain, "Plain")
        check("the PET draft is named for the board, Board 1 on a fresh case",
              Path(drafted["path"]).name == "Juno - PET draft (Board 1).md"
              and Path(drafted["path"]).read_text(encoding="utf-8").startswith("# Plain: PET grouping draft (Board 1)")
              and themes_mod.FIRST_NAME == "Board 1")
    finally:
        server_mod.ROOT_OVERRIDE = saved_root

    # ── F. no version on the screen, in its script or in what the AI's help says
    static = server_mod.HERE / "static"
    js = support.text("apps/idiograph/static/themes.js")
    fn = lambda text, name: text.split(f"function {name}(", 1)[1].split("\n}", 1)[0]

    # ── G. the screen's wiring
    check("restore asks the server, then is one step of undo, and says so in one line",
          "thBoardOp('restore'" in fn(js, "thRestoreRevision") and "thStep(before," in fn(js, "thRestoreRevision")
          and "t('themes.revision.restored'" in fn(js, "thRestoreRevision"))
    check("a copy onto the board on screen is one step of undo, and onto another says so in one line",
          "thBoardOp('copy', extra, TH_BOARDS_ROUTE)" in fn(js, "thCopyTo") and "thStep(before, t('themes.step.copied_in', { label }));" in fn(js, "thCopyTo")
          and "say(t('themes.copy.there', { label, target }), 6000);" in fn(js, "thCopyTo") and "extra.revision = TH.viewing.rev.id;" in fn(js, "thCopyTo"))
    check("the timer asks for an automatic revision through the save, and waits while a revision is on view",
          "if (due) body.revision = 'auto';" in fn(js, "thSaveOnce") and "const v = thLiveV();" in fn(js, "thSaveOnce")
          and "if (!TH.live || TH.viewing" in fn(js, "thRevisionTick") and "setInterval(thRevisionTick, 60 * 1000);" in js
          and "TH_REVISION_EVERY = 15 * 60 * 1000" in js)

    # ── I. the model half in node: a revision on view is read-only
    node = shutil.which("node")
    if not node:
        return skip("the boards model in node", "no node on this machine")
    run = subprocess.run([node, "--check", str(support.source("apps/idiograph/static/themes.js"))], capture_output=True, text=True, encoding="utf-8")
    model = scratch / "themes-boards.js"
    model.write_text(support.i18n_js() + js + r"""
const card = (x, y, text) => ({ x, y, text, sheet: 'S', row: 1, line: 0 });
const v = { cards: { 'S:1:0': card(0, 0, 'A'), 'S:2:0': card(220, 0, 'B'), 'S:3:0': card(0, 300, 'C') },
  groups: [{ id: 'g1', label: 'One', members: ['S:1:0'], x: 0, y: -30 }], discarded: [], picks: {}, readonly: true };
const was = JSON.stringify(v);
const size = () => ({ w: 200, h: 80 });
const out = {};
out.acts = [thMakeGroup(v, ['S:2:0'], 'New'), thJoin(v, ['S:2:0'], 'g1'), thDiscard(v, ['S:3:0']), thDelete(v, 'g1'),
  thTogglePick(v, 'g1', 'S:1:0'), thArrange(v, 'g1', size), thRestore(v, 'S:3:0', 5, 5), thLeave(v, 'S:1:0'),
  thDrop(v, new Set(['S:2:0']), 'g1', null), thSettle(v, size, ['S:2:0'], {}, [])];
thShift(v, ['S:1:0'], 50, 50);
thPut(v, { cards: {}, groups: [], discarded: [], picks: {}, removed: [] });
out.same = JSON.stringify(v) === was;
out.may = [thMayAct(v, 'drag'), thMayAct(v, 'group'), thMayAct(v, 'undo'), thMayAct(v, 'lasso'), thMayAct(v, 'copy'),
  thMayAct(v, 'panel'), thMayAct({ readonly: false }, 'drag')];
const live = JSON.parse(was); delete live.readonly;
out.menu = [thMenuItems(v, { kind: 'group', id: 'g1' }).map((i) => i.label), thMenuItems(v, { kind: 'card', id: 'S:1:0' }).length,
  thMenuItems(live, { kind: 'group', id: 'g1' }, false).filter((i) => i.act === 'copyto').map((i) => i.off)];
out.moved = thMakeGroup(live, ['S:2:0'], 'New');
const boards = [{ id: 'v1', name: 'Board 1' }, { id: 'v2', name: 'Board 2' }, { id: 'v3', name: 'AI board 1' }];
out.targets = [thCopyTargets(boards, 'v1', false), thCopyTargets(boards, 'v1', true).map((t) => [t.id, t.here])];
const now = new Date(2026, 9, 2, 18, 0);
out.when = [thWhen(new Date(2026, 9, 2, 12, 4).toISOString(), now), thWhen(new Date(2026, 9, 1, 12, 4).toISOString(), now),
  thWhen(new Date(2025, 11, 31, 9, 5).toISOString(), now)];
out.days = thHistoryDays([{ id: 'r3', at: new Date(2026, 9, 2, 12, 4).toISOString(), name: '', auto: true },
  { id: 'r2', at: new Date(2026, 9, 2, 9, 30).toISOString(), name: 'Mine', auto: false },
  { id: 'r1', at: new Date(2026, 9, 1, 16, 0).toISOString(), name: '', auto: true },
  { id: 'r0', at: new Date(2026, 8, 28, 10, 0).toISOString(), name: '', auto: false }], now)
  .map((d) => [d.day, d.items.map((i) => `${i.id} ${i.time}`)]);
const t0 = 1000000;
out.due = [thRevisionDue(t0 + TH_REVISION_EVERY, t0, true), thRevisionDue(t0 + TH_REVISION_EVERY, t0, false),
  thRevisionDue(t0 + TH_REVISION_EVERY - 1, t0, true)];
console.log(JSON.stringify(out));
""", encoding="utf-8")
    run = subprocess.run([node, str(model)], capture_output=True, text=True, encoding="utf-8")
    if run.returncode != 0:
        return check("the boards model runs in node", False, run.stderr.strip()[:300])
    out = json.loads(run.stdout)
    check("a revision on view is read-only in the model: every act leaves it exactly as it was",
          out["same"] is True and out["acts"] == [None, [], [], False, False, False, False, None,
                                                  {"joined": [], "left": [], "dest": None}, False], str(out["acts"]))
    check("on a revision only what changes nothing is allowed: the lasso, the panel and the copy, never a drag or a key",
          out["may"] == [False, False, False, True, True, True, True], str(out["may"]))
    check("its right-click menu is Inspect and Copy to board on a label, and Inspect and Go to the passage on a card, which "
          "changes nothing (183, 156)",
          out["menu"][0] == ["Inspect", "Copy to board\u2026"] and out["menu"][1] == 2 and out["menu"][2] == [True]
          and out["moved"] == "g2", str(out["menu"]))
    check("Copy to board lists the other boards, and on a revision the board it belongs to first",
          out["targets"][0] == [{"id": "v2", "name": "Board 2", "here": False}, {"id": "v3", "name": "AI board 1", "here": False}]
          and out["targets"][1] == [["v1", True], ["v2", False], ["v3", False]], str(out["targets"]))
    check("the page says a revision's time as the server does, and lists the history by day, newest first",
          out["when"] == ["12:04", "1 October 12:04", "31 December 2025 09:05"]
          and out["days"] == [["Today", ["r3 12:04", "r2 09:30"]], ["Yesterday", ["r1 16:00"]], ["28 September 2026", ["r0 10:00"]]],
          f"{out['when']} {out['days']}")
    check("the timer is due fifteen minutes on, and only after an act", out["due"] == [True, False, False])
