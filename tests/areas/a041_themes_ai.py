from __future__ import annotations

import inspect
import json
import shutil

import ai_suggest as ai_mod
from workbook import WorkbookError

from . import support
from .support import GRAVITY_QUESTION, check, demo_copy, skip
import idiograph_routes


def test_themes_ai(scratch):
    print("\n41. Themes, stage 3: the AI's titles, and a structure laid out as a board (the AI's grouping, review and revise went on 11 November 2026, aiout)")
    import http.server
    import subprocess
    import threading
    import urllib.error
    import urllib.request
    import server as server_mod
    import themes as themes_mod
    import themes_ai

    root = scratch / "themes-ai-root"
    work = demo_copy(root, "Juno", "Juno - EN & ES.xlsx")
    (root / "idiograph-project.json").write_text(json.dumps(
        {"name": "Scratch", "research_question": GRAVITY_QUESTION}), encoding="utf-8")
    read = themes_mod.read_cards(work)
    k = [c["key"] for c in read["cards"]]

    cards = {c["key"]: c for c in read["cards"]}

    # ── A. a label as the canvas keeps it, through every board made or changed through the API
    check("a label loses inverted commas round the whole of it, its em dash and its semicolon",
          themes_ai.clean_label("\u201cA label \u2014 with a dash; and more\u201d") == "A label, with a dash, and more")

    # ── C. the layout: a round blob for each theme, the rest in a pile
    proposal = {"groups": [
        {"label": "Mornings that belong to the dog and to nobody else in the house", "members": k[0:4], "groups": []},
        {"label": "A house that holds two", "members": [k[4]],
         "groups": [{"label": "Walks taken alone", "members": k[5:8]}, {"label": "Nights", "members": k[8:10]}]},
        {"label": "A third theme", "members": k[10:13], "groups": []}]}
    source = themes_mod.blank_version(read["cards"])
    source["discarded"] = [k[-1]]
    source["cards"][k[-1]].update(x=77, y=88)
    m2 = themes_mod.merge(read["cards"], source)
    laid = themes_ai.lay_out(proposal["groups"], m2["cards"], m2["discarded"])
    by_id = {g["id"]: g for g in laid["groups"]}
    parents = {m: g["id"] for g in laid["groups"] for m in g["members"]}
    pos = laid["cards"]
    check("every card of the board is laid out, and the discarded one stays discarded where it was",
          set(pos) == set(k) and laid["discarded"] == [k[-1]] and (pos[k[-1]]["x"], pos[k[-1]]["y"]) == (77, 88)
          and laid["picks"] == {} and all(pos[key]["text"] == cards[key]["text"] for key in k))
    check("the themes are g1 on, the sub-themes after them inside their theme",
          [g["id"] for g in laid["groups"]] == ["g1", "g2", "g3", "g4", "g5"]
          and by_id["g2"]["members"] == [k[4], "g4", "g5"] and parents["g4"] == "g2" and parents["g5"] == "g2"
          and [by_id[g]["label"] for g in ("g4", "g5")] == ["Walks taken alone", "Nights"])
    drawn_at = themes_mod.layout_boxes(laid)
    frames, label_boxes, card_boxes = drawn_at["frames"], drawn_at["labels"], drawn_at["cards"]
    within = lambda a, b: b[0] <= a[0] and b[1] <= a[1] and a[0] + a[2] <= b[0] + b[2] and a[1] + a[3] <= b[1] + b[3]
    inside = all(within(card_boxes[m] if m in card_boxes else frames[m], frames[g["id"]])
                 for g in laid["groups"] for m in g["members"])
    check("every member lies inside its theme's frame, and each sub-theme's frame inside its theme's",
          inside and within(frames["g4"], frames["g2"]) and within(frames["g5"], frames["g2"]))
    check("each label stands where the page sets it, above what it holds, its left edge on theirs",
          all((g["x"], g["y"]) == tuple(label_boxes[g["id"]][:2]) for g in laid["groups"])
          and all(label_boxes[g["id"]][1] < min(card_boxes[m][1] for m in g["members"] if m in card_boxes)
                  for g in laid["groups"] if any(m in card_boxes for m in g["members"])))
    top_frames = [frames[g] for g in ("g1", "g2", "g3")]
    check("the themes are blobs on the plane, their frames apart with clear gaps",
          not any(themes_mod.clash(top_frames[i], top_frames[j], themes_ai.THEME_GAP - 1) for i in range(3) for j in range(i + 1, 3))
          and themes_ai.THEME_GAP == 2 * themes_mod.MARGIN)
    shape = [frames[g][2] / frames[g][3] for g in ("g1", "g3")]
    check("a theme's own cards fill a roughly round blob, not a column",
          all(0.5 <= r <= 2.2 for r in shape), ", ".join(f"{r:.2f}" for r in shape))
    under_of = {}
    for g in laid["groups"]:
        under_of[g["id"]] = set(g["members"])
    for g in laid["groups"]:
        for m in list(under_of[g["id"]]):
            under_of[g["id"]] |= under_of.get(m, set())
    items = [(key, box) for key, box in card_boxes.items()] + [(gid, box) for gid, box in label_boxes.items()]
    overlaps = [(a, b) for i, (a, ba) in enumerate(items) for b, bb in items[i + 1:]
                if themes_mod.clash(ba, bb) and b not in under_of.get(a, ()) and a not in under_of.get(b, ())]
    check("no card or label over another card or label",
          not overlaps, ", ".join(f"{a}/{b}" for a, b in overlaps[:4]) or f"{len(items)} cards and labels")
    drawn = [key for key in k if key not in laid["discarded"]]
    left = [key for key in drawn if key not in parents]
    edge = max(f[0] + f[2] for f in frames.values())
    check("the cards left out lie in a pile to the right of the themes, in transcript order",
          left and all(pos[key]["x"] > edge for key in left)
          and [key for key in sorted(left, key=lambda key: (pos[key]["y"], pos[key]["x"]))] == left,
          f"{len(left)} unplaced")
    check("the layout survives the file's own tidying unchanged",
          themes_mod.normalise(laid)["groups"] == [dict(g) for g in laid["groups"]])

    # ── D. the route, through a transport that stands in for the provider
    real = (server_mod.CONFIG_PATH, server_mod.ROOT_OVERRIDE, ai_mod.find_key, ai_mod.http_call)
    config_path = scratch / "themes-ai" / "config.json"
    config_path.parent.mkdir(parents=True, exist_ok=True)
    sent, replies, looked = [], [], []

    def wire(method, url, headers, payload, timeout):
        sent.append({"url": url, "payload": payload, "timeout": timeout, "headers": headers})
        text = replies[0](payload) if replies else ""
        if "/api/chat" in url:
            return 200, json.dumps({"message": {"content": text}, "done_reason": "stop"})
        return 200, json.dumps({"content": [{"type": "text", "text": text}], "stop_reason": "end_turn"})

    def settings(**extra):
        config_path.write_text(json.dumps({"ai_provider": "anthropic", "model": "claude-haiku-4-5", **extra}),
                               encoding="utf-8")

    path = themes_mod.themes_path(work)
    titles = lambda p: json.dumps({"names": ["Mornings that belong to the dog", "A walk before the house wakes",
                                             "mornings that belong to the dog"]})
    try:
        server_mod.CONFIG_PATH = config_path
        server_mod.ROOT_OVERRIDE = str(root)
        ai_mod.find_key = lambda *a, **kw: looked.append(1) or "k-test"
        ai_mod.http_call = wire
        settings(ai_suggest=False)
        off = idiograph_routes.api_themes_ai({"workbook": str(work), "op": "names", "statements": ["x"]})
        check("with the switch off the titles are refused with one line, and nothing is sent or written",
              off == {"error": themes_ai.OFF} and not sent and not looked and not path.exists())
        opened = idiograph_routes.api_themes({"workbook": str(work)})
        check("/api/themes says whether the switch is on and which model answers, never the key, and no limit",
              opened["ai"] == {"on": False, "provider": "anthropic", "model_name": "Haiku 4.5"} and not looked
              and "from_all" not in opened and "revisable" not in opened)
        settings(ai_suggest=True)
        opened = idiograph_routes.api_themes({"workbook": str(work)})
        check("and says so when it is on", opened["ai"]["on"] is True and not looked)
        body = {**opened["version"], "cards": {c["key"]: {"x": c["x"], "y": c["y"], "text": c["text"]}
                                               for c in opened["cards"]},
                "groups": [{"id": "g1", "label": "Mornings first", "members": [k[0], k[1]], "x": 0, "y": 0}],
                "discarded": [k[2]], "picks": {}}
        idiograph_routes.api_themes_save({"workbook": str(work), "version": body})
        book = work.read_bytes()

        # aiout (11 November 2026): New AI board, AI review and AI revise are gone, each op refused with nothing
        # sent or written, the titles the one op left
        before = path.read_bytes()
        gone = [idiograph_routes.api_themes_ai({"workbook": str(work), "op": op, "version": "v1", "text": "words"})
                for op in ("group", "review", "reply", "revise", "write")]
        check("aiout: a new AI board, a review, a reply and a revise are each refused as an op the help does not do, "
              "nothing sent or written",
              all(g.get("code") == "unknown_op" and "error" in g for g in gone) and not sent
              and path.read_bytes() == before and work.read_bytes() == book, str(gone[0]))
        check("aiout: the server keeps none of their code",
              not any(hasattr(themes_ai, n) for n in ("group", "review", "reply", "revise", "pick_quotes", "parse_grouping",
                                                      "parse_review", "parse_revise", "gets_group", "gets_review"))
              and not hasattr(idiograph_routes, "ta_board_ai") and not hasattr(idiograph_routes, "review_item"))

        # the names
        replies[:] = [titles]
        named = idiograph_routes.api_themes_ai({"workbook": str(work), "op": "names",
                                          "statements": ["Waking before the house does", "The lead by the door"],
                                          "label": "Mornings first", "others": ["A house that holds two"]})
        call = sent[-1]
        asked = call["payload"]["messages"][0]["content"]
        check("names come back tidied and each once, with the model that gave them",
              named["names"] == ["Mornings that belong to the dog", "A walk before the house wakes"]
              and named["model_name"] == "Haiku 4.5" and isinstance(named["seconds"], float), str(named))
        check("the request carries the statements, the title it has, the other labels and the question",
              "- Waking before the house does" in asked and "Its title now: Mornings first" in asked
              and "- A house that holds two" in asked and "Three titles" in asked
              and GRAVITY_QUESTION in call["payload"]["system"] and '{"names"' in call["payload"]["system"]
              and call["payload"]["max_tokens"] == themes_ai.NAMES_MAX_TOKENS and call["url"] == ai_mod.ENDPOINT)
        check("the key rides in the request's header and nowhere else",
              call["headers"].get("x-api-key") == "k-test" and "k-test" not in json.dumps(named)
              and "k-test" not in path.read_text(encoding="utf-8") and "k-test" not in json.dumps(call["payload"]))
        check("asking for names writes nothing", path.read_bytes() == before and work.read_bytes() == book)
        check("a selection with no statements is one line and no call",
              idiograph_routes.api_themes_ai({"workbook": str(work), "op": "names", "statements": ["  "]})
              == {"error": themes_ai.NOTHING_TO_NAME} and len(sent) == 1)
        by_id = idiograph_routes.api_themes_ai({"workbook": str(work), "op": "names", "version": "v1", "group": "g1"})
        asked = sent[-1]["payload"]["messages"][0]["content"]
        check("a label by its id is set out from the board and the workbook, its statements under its title",
              by_id["names"] == named["names"] and "Theme: Mornings first" in asked
              and cards[k[0]]["text"] in asked and cards[k[1]]["text"] in asked)

        def failing(method, url, headers, payload, timeout):
            return 529, '{"error": "do not print me"}'

        ai_mod.http_call = failing
        failed = idiograph_routes.api_themes_ai({"workbook": str(work), "op": "names", "statements": ["x"]})
        ai_mod.http_call = wire
        check("an API error says its status and nothing else", failed == {"error": "Anthropic did not answer (HTTP 529)."})
        ai_mod.find_key = lambda *a, **kw: None
        sent.clear()
        keyless = idiograph_routes.api_themes_ai({"workbook": str(work), "op": "names", "statements": ["x"]})
        ai_mod.find_key = lambda *a, **kw: looked.append(1) or "k-test"
        check("no key is one line and no call", keyless == {"error": ai_mod.NO_KEY} and not sent)
        refused = []
        for call_body, route in ((dict(op="names", version="v9", group="g1"), idiograph_routes.api_themes_ai),
                                 (dict(op="propose", version={"cards": {}}), idiograph_routes.api_themes_versions)):
            try:
                route({"workbook": str(work), **call_body})
            except WorkbookError as exc:
                refused.append(str(exc))
        check("a board the file does not hold is refused, and the boards route never takes a proposal",
              len(refused) == 2 and "no longer" in refused[0] and "not something a board can do" in refused[1]
              and path.read_bytes() == before)
        outside = demo_copy(scratch, "themes-ai-elsewhere", "Juno - EN & ES.xlsx")
        try:
            idiograph_routes.api_themes_ai({"workbook": str(outside), "op": "names", "statements": ["x"]})
            stray = True
        except server_mod.OutsideRoot:
            stray = False
        check("a workbook outside the root is refused", not stray and not themes_mod.themes_path(outside).exists())

        # Local: the titles through Ollama, with the room asked for and no key looked up
        settings(ai_suggest=True, ai_provider="local", local_model="llama3.1:8b")
        sent.clear()
        looked.clear()
        replies[:] = [titles]
        local = idiograph_routes.api_themes_ai({"workbook": str(work), "op": "names", "statements": ["x"]})
        options = sent[-1]["payload"].get("options", {})
        check("through Local the titles go to Ollama with room for the answer, and no key is looked up",
              sent[-1]["url"].endswith("/api/chat") and options.get("num_predict") == themes_ai.NAMES_MAX_TOKENS
              and options.get("num_ctx") == ai_mod.LOCAL_CONTEXT and not looked
              and local["model_name"] == "llama3.1:8b on this machine", str(local))
        check("a suggestion's own request is as it was, with no ceiling of its own",
              "options" not in ai_mod.local_payload("s", "u", "m")
              and ai_mod.anthropic_payload("s", "u", "claude-haiku-4-5")["max_tokens"] == ai_mod.MAX_TOKENS)

        # over HTTP, and a server from before the help
        httpd = http.server.ThreadingHTTPServer(("127.0.0.1", 0), server_mod.Handler)
        threading.Thread(target=httpd.serve_forever, kwargs={"poll_interval": 0.05}, daemon=True).start()

        def post(route, payload):
            req = urllib.request.Request(f"http://127.0.0.1:{httpd.server_address[1]}{route}",
                                         data=json.dumps(payload).encode("utf-8"),
                                         headers={"Content-Type": "application/json"})
            try:
                with urllib.request.urlopen(req, timeout=10) as r:
                    return r.status, json.loads(r.read())
            except urllib.error.HTTPError as exc:
                return exc.code, json.loads(exc.read())

        held = server_mod.ROUTES.pop("/api/themes-ai")
        try:
            old = post("/api/themes-ai", {"workbook": str(work), "op": "names"})
        finally:
            server_mod.ROUTES["/api/themes-ai"] = held
        try:
            far = post("/api/themes-ai", {"workbook": str(outside), "op": "names"})
        finally:
            httpd.shutdown()
            httpd.server_close()
        check("a server from before the help answers with the line the page turns into the restart line",
              old == (404, {"error": "No such endpoint.", "code": "no_endpoint"}) and far[0] == 403)
        check("the route is in the dispatch table and goes through ai_route, by way of the PETs route",
              server_mod.ROUTES.get("/api/themes-ai") is idiograph_routes.api_themes_ai
              and "pets_route(cfg" in inspect.getsource(idiograph_routes.api_themes_ai)
              and "ai_route(cfg" in inspect.getsource(idiograph_routes.pets_route))
    finally:
        server_mod.CONFIG_PATH, server_mod.ROOT_OVERRIDE, ai_mod.find_key, ai_mod.http_call = real

    # ── E. the names, read
    check("three titles come back as three, a fourth dropped",
          themes_ai.parse_names(json.dumps({"names": ["One title", "Two titles", "Three titles", "Four"]}))
          == {"names": ["One title", "Two titles", "Three titles"]})
    check("two come back as two, a fenced answer read and a repeat dropped",
          themes_ai.parse_names('```json\n{"names": ["A walk", "a walk", "The door"]}\n```')
          == {"names": ["A walk", "The door"]})
    check("none is one line, and so is an answer that is not JSON or was cut off",
          themes_ai.parse_names('{"names": []}') == {"error": themes_ai.NO_TITLES}
          and themes_ai.parse_names('{"names": ["  "]}') == {"error": themes_ai.NO_TITLES}
          and themes_ai.parse_names("nothing") == {"error": themes_ai.NOT_JSON}
          and themes_ai.parse_names('{"names": ["A', truncated=True) == {"error": ai_mod.TOO_LONG})
    check("a label with no title, or Untitled, is sent as having none",
          "It has no title yet." in themes_ai.names_user(["a"], "") and "It has no title yet." in themes_ai.names_user(["a"], "Untitled"))

    # ── F. the page
    js = support.text("apps/idiograph/static/themes.js")
    app = support.text("family/static/shell.js", "apps/idiograph/static/distil.js")
    page = support.text("apps/idiograph/static/idiograph.html")
    fn = lambda text, name: text.split(f"function {name}(", 1)[1].split("\n}", 1)[0]
    check("the titles are drawn only with the switch on, and n asks only then",
          "if (!thAiOn() || !item || item.kind !== 'group') return '';" in fn(js, "thNamesHtml")
          and "&& thAiOn()) { e.preventDefault(); thNamesAsk(); }" in fn(js, "thKeyDown")
          and "t('themes.names.pets')" in fn(js, "thNamesHtml"))
    check("aiout: the board menu has no New AI board, the sidebar no Review or Revise, and the page no AI board card",
          'data-vop="ai"' not in js and "thAutoGroup" not in js and "thReviewDraw" not in js and "thReviseDraw" not in js
          and 'id="th-aicard"' not in page and 'data-tab="review"' not in page and 'data-tab="revise"' not in page
          and "'th-aicard'" not in app.split("const OVERLAYS = ", 1)[1].split("\n", 1)[0])
    apply = fn(js, "thNameApply")
    check("a name picked is one step of undo, a rename on its label, Edit to type over it, and no label made over a selection (123)",
          "thDone(before, t('themes.step.renamed')" in apply and "thDone(before, t('themes.step.made_theme')" not in apply
          and "thMakeGroup(" not in apply
          and "thTitleOpen(g.id, { value: name });" in apply
          and "opts.value !== undefined ? opts.value" in fn(js, "thTitleOpen"))

    node = shutil.which("node")
    if not node:
        return skip("the names model in node", "no node on this machine")
    run = subprocess.run([node, "--check", str(support.source("apps/idiograph/static/themes.js"))], capture_output=True, text=True, encoding="utf-8")
    run = subprocess.run([node, "--check", str(support.source("apps/idiograph/static/distil.js"))], capture_output=True, text=True, encoding="utf-8")
    script = scratch / "themes-names.js"
    script.write_text(support.i18n_js() + js + r"""
const card = (row, text) => ({ sheet: 'S', row, line: 0, x: 0, y: 0, text, seconds: row, time: '' });
const v = { cards: { 'S:1:0': card(1, 'one'), 'S:2:0': card(2, 'two'), 'S:3:0': card(3, 'three'),
  'S:4:0': card(4, 'four') }, groups: [], discarded: [], picks: {} };
const g1 = thMakeGroup(v, ['S:1:0', 'S:2:0'], 'First');
const g2 = thMakeGroup(v, ['S:3:0'], '');
const g3 = thMakeGroup(v, [g1], 'Over');
const none = { cards: new Set(), groups: new Set() };
const out = {};
out.label = thNamesTarget(v, { cards: new Set(), groups: new Set([g1]) }, null);
out.labelAndOwnCard = thNamesTarget(v, { cards: new Set(['S:1:0']), groups: new Set([g1]) }, null);
out.bare = thNamesTarget(v, { cards: new Set(['S:4:0', 'S:3:0']), groups: new Set() }, null);
out.panelCard = thNamesTarget(v, none, { kind: 'card', id: 'S:4:0' });
out.panelLabel = thNamesTarget(v, none, { kind: 'group', id: g2 });
out.nothing = thNamesTarget(v, none, null);
out.body = thNamesBody(v, { kind: 'group', id: g1 });
out.keys = [thNamesKey({ kind: 'group', id: g1 }), thPanelKey({ kind: 'group', id: g1 }), thPanelKey({ kind: 'card', id: 'S:4:0' })];
out.rows = thPanelRows(v, { kind: 'group', id: g3 }, {}, ['S']).map((r) => r.row);
out.selCards = typeof thSelCards;
console.log(JSON.stringify(out));
""", encoding="utf-8")
    run = subprocess.run([node, str(script)], capture_output=True, text=True, encoding="utf-8")
    if run.returncode != 0:
        return check("the names model runs in node", False, run.stderr.strip()[:300])
    out = json.loads(run.stdout)
    check("one label selected is that label to rename, its own card beside it changes nothing",
          out["label"] == {"kind": "group", "id": "g1"} and out["labelAndOwnCard"] == {"kind": "group", "id": "g1"})
    check("123: cards selected with no label say to group them first, and with nothing selected only the panel's label is a target",
          out["bare"] == {"kind": "cards"} and out["panelCard"] is None
          and out["panelLabel"] == {"kind": "group", "id": "g2"} and out["nothing"] is None)
    check("122: a label sends its id and its board, and beside them the old shape a server from before reads",
          out["body"] == {"version": None, "group": "g1", "statements": ["one", "two"], "label": "First", "others": ["Over"]})
    check("the names show beside the label they were asked for, and the bare selection's keys are gone (123)",
          out["keys"] == ["g:g1", "g:g1", "s:S:4:0"] and out["selCards"] == "undefined")
    check("a label over labels lists the rows of every card under it, in transcript order",
          out["rows"] == ["S:1", "S:2"])
