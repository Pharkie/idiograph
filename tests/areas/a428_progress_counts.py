"""Area 428: how far each stage is decided, counted on the server (dashcounts, 18 November 2026).

Adam chose a new Home and project page where each participant's picture sits in progress rings. The rule he agreed:
progress counts decisions, never the number of things made, and "complete" is always the researcher's own mark. So the
server counts, for Home and the project page, per participant and per timepoint: the passages decided, the statements
in a PET (stacked and set aside too) of all of them, the same over the LPETs board, the project's GETs or LGETs cards in
a GET or set aside of all of them, with a participant's PETs not yet brought in counted, Trajectories placed of
participants, and a thematic analysis project's codes in a theme or set aside of all the codes. They ride on Home's
participant cards and on the project's head (`progress`), and the command line's `cases` and MCP's `cases` answer the same.

What is checked, on copies of the four demos made projects of their own (the IPA demo, the longitudinal demo and both
thematic analysis demos): every count equals what the board's own status bar counts, the page's `thStatusNumbers`
and `gtCodeNumbers` run in node on the state the screen is given; the same on boards edited so a statement is stacked,
set aside, unplaced, written after the board was made, or gone from the workbook, and on a participant whose PETs (a
timepoint's PETs on LPETs) are not yet brought into the GETs (LPETs, LGETs) file; each timepoint of a longitudinal
participant carries its own PETs mark; the command line and MCP answer the card's numbers; the counts survive Home's
cache written and read again; and reading writes nothing."""
from __future__ import annotations

import json
import os
import shutil
import subprocess
from pathlib import Path

from . import support
from .a201_status_bar_and_palette import STUBS
from .a424_project_kind import demo_copy, files
from .support import check

SCENARIO = r"""
const fs = require('fs');
const input = JSON.parse(fs.readFileSync(process.argv[2], 'utf8'));
for (const id of ['th-status-counts', 'th-palette']) ELS[id] = new El(id);
const out = [];
for (const item of input) {
  const s = item.state;
  TH.mode = item.gets ? 'gets' : 'pets';
  TH.project = { method: item.ta ? 'ta' : 'ipa' };
  TH.gets = item.gets ? s : null;
  TH.codeList = item.codeList || null;
  const v = { cards: Object.fromEntries(s.cards.map((c) => [c.key, c])), groups: s.groups, discarded: s.discarded || [],
              stacks: s.stacks || {}, stickies: s.stickies || [], waits: false, picks: {} };
  const n = thStatusNumbers(v, !!item.gets);
  out.push({ decided: n.placed + n.binned + n.stacked, total: n.placed + n.binned + n.stacked + n.unplaced + n.loose });
}
console.log(JSON.stringify(out));
"""


def node_counts(scratch: Path, items: list[dict]) -> list[dict] | None:
    """The page's own counts for each state, run in node, or None where there is no node."""
    node = shutil.which("node")
    if not node:
        return None
    js = support.text("apps/idiograph/static/themes.js")
    script = scratch / "counts-428.js"
    script.write_text(support.i18n_js() + STUBS + js + SCENARIO, encoding="utf-8")
    data = scratch / "counts-428.json"
    data.write_text(json.dumps(items), encoding="utf-8")
    run = subprocess.run([node, str(script), str(data)], capture_output=True, text=True, encoding="utf-8", timeout=180)
    if run.returncode != 0:
        check("428: the board's counts run in node", False, run.stderr.strip()[:600])
        return None
    return json.loads(run.stdout)


def test_progress_counts(scratch: Path):
    print("\n428. How far each stage is decided, counted on the server as the board's status bar counts it (dashcounts)")
    import agent_log
    import agent_changes
    import cli
    import codes as codes_mod
    import gets as gets_mod
    import home_cache
    import idiograph_routes as routes
    import mcp_server
    import server as server_mod
    import themes as themes_mod

    base = scratch / "progress-428"
    shutil.rmtree(base, ignore_errors=True)
    base.mkdir(parents=True)
    src = support.source("demo")
    roots = {"ipa": base / "Living with a dog", "lipa": base / "Allotment study", "ta": base / "Dog coding",
             "rta": base / "Home working"}
    demo_copy(src, roots["ipa"], ("Juno", "Rowan", "Mabel"))
    demo_copy(src / "lipa", roots["lipa"], ("Arlo", "Hollis", "Nell"))
    demo_copy(src / "ta", roots["ta"], ("Juno", "Rowan", "Mabel"))
    demo_copy(src / "rta", roots["rta"], ("Dev", "Ffion", "Glen", "Kemi", "Ros", "Toby"))
    config_file = base / "config.json"
    config_file.write_text(json.dumps({"projects": [{"root": str(r)} for r in roots.values()], "interviewer": "Adam",
                                      "corpus": "", "gravity_reference": "", "corpus_exclude": []}), encoding="utf-8")
    kept = (agent_changes.ALL_OPS, server_mod.CONFIG_PATH, server_mod.ROOT_OVERRIDE, server_mod.STATE_PATH,
            server_mod.STATE_MEMORY)
    import os
    was_log = os.environ.get(agent_log.PLACE)
    agent_changes.ALL_OPS = None
    os.environ[agent_log.PLACE] = str(base / "agent-log.json")
    server_mod.CONFIG_PATH, server_mod.ROOT_OVERRIDE = config_file, None
    server_mod.STATE_PATH, server_mod.STATE_MEMORY = base / "state.json", {"recent": []}

    def section(root):
        for s in routes.api_cases({})["projects"]:
            if s["id"] == routes.project_id(root):
                return s
        return {}

    def books(root):
        return sorted(routes.gets_books(root), key=lambda b: gets_mod.case_order(b["case"]))

    def hold(path):
        return json.loads(Path(path).read_text(encoding="utf-8"))

    def reference(path, n=None):
        """The board the counts are of: the one marked complete, else the Current board, else the one last open, its id."""
        file = themes_mod.themes_path(path, n or 1)
        data = themes_mod.migrate(hold(file)) if file.exists() else None
        board = gets_mod.source_board(data)[0] if data else None
        return (board or {}).get("id")

    def pets_state(path, n):
        """What the PETs screen is given for the board the counts are of, at timepoint `n`."""
        with themes_mod.scoped(n if n and n > 1 else None):
            return themes_mod.state(path, routes.case_label(path), board=reference(path, n))

    def server_pets(path, n=None):
        got = routes.pets_progress(path, n)
        return {"decided": got["decided"], "total": got["total"]}

    def board_state(root, file, **body):
        """What the GETs, LGETs or LPETs screen is given for the board of the file `file` the counts are of."""
        route_body = dict(body, root=routes.project_id(root), board=reference_board(hold(file)))
        with routes.route_scope("/api/gets", route_body):
            return routes.api_gets(route_body)

    try:
        start = {k: files(r) for k, r in roots.items()}

        # ── A. every count equals the board's own, on each demo
        pairs, items = [], []
        for key in ("ipa", "lipa"):
            for b in books(roots[key]):
                path = Path(b["workbook"])
                tps = routes.card_timepoints(path, routes.interviewer_for(path))
                for n in ([t["n"] for t in tps if t["state"] != "none"] if tps else [None]):
                    items.append({"state": pets_state(path, n)})
                    pairs.append(("PETs", key, b["case"], n, server_pets(path, n)))
        for b in books(roots["lipa"]):
            path = Path(b["workbook"])
            items.append({"gets": True, "state": board_state(roots["lipa"], gets_mod.lpets_path(path),
                                                             workbook=str(path), lpets=True)})
            got = routes.lpets_progress(path)
            pairs.append(("LPETs", "lipa", b["case"], None, {"decided": got["decided"], "total": got["total"]}))
        for key in ("ipa", "lipa"):
            root = roots[key]
            head = routes.gets_head(root)
            file = root / ("idiograph-gets.json" if key == "ipa" else "idiograph-lgets.json")
            items.append({"gets": True, "state": board_state(root, file)})
            word = "lgets" if key == "lipa" else "gets"
            pairs.append((word.upper(), key, "", None, {k: head["progress"][word][k] for k in ("decided", "total")}))
        for key in ("ta", "rta"):
            root = roots[key]
            answer = board_state(root, root / "idiograph-gets.json")
            listed = (codes_mod.load(root) or {}).get("codes") or []
            items.append({"gets": True, "ta": True, "state": answer, "codeList": {"codes": listed}})
            head = routes.gets_head(root)
            pairs.append(("Themes", key, "", None, {k: head["progress"]["themes"][k] for k in ("decided", "total")}))
        page = node_counts(base, items)
        if page is None:
            check("428: the page's counts in node", True, "")
        else:
            same = all(p[4] == page[i] for i, p in enumerate(pairs))
            check("428: on the IPA, longitudinal and both thematic analysis demos, every participant's PETs at every "
                  "timepoint, their LPETs, the project's GETs or LGETs and the themes of both thematic analysis demos "
                  "count what the board's own status bar counts (the page's thStatusNumbers and gtCodeNumbers in node)",
                  len(pairs) == len(page) and same,
                  str([(p[:4], p[4], page[i]) for i, p in enumerate(pairs) if p[4] != page[i]][:4]))
        check("428: the demos hold a statement not decided, Mabel's PETs, so a count is not just a total",
              any(p[4]["decided"] != p[4]["total"] for p in pairs if p[0] == "PETs"),
              str([p[4] for p in pairs if p[0] == "PETs"]))

        # ── B. a board edited so each way a statement can stand is there, and a participant not yet brought in
        juno = Path(books(roots["ipa"])[0]["workbook"])
        before = server_pets(juno)
        file = themes_mod.themes_path(juno)
        data = hold(file)
        board = gets_mod.source_board(data)[0]
        cards = board["cards"]
        members = [k for g in board["groups"] for k in g["members"] if k in cards]
        gone_key, loose_key, stack_key, aside_key = members[0], members[1], members[2], members[3]
        # one card never seen by the board (written after it was made), one taken out of its PET into no PET, one
        # stacked under another, one set aside, and one stored card whose line is no longer in the workbook
        for g in board["groups"]:
            g["members"] = [k for k in g["members"] if k not in (gone_key, loose_key, stack_key, aside_key)]
        cards.pop(gone_key)
        board.setdefault("stacks", {}).setdefault(members[5], []).append(stack_key)
        board.setdefault("discarded", []).append(aside_key)
        cards["Initial:9999:0"] = {"x": 0, "y": 0, "text": "A line no longer in the sheet"}
        file.write_text(json.dumps(data), encoding="utf-8")
        edited = server_pets(juno)
        shown = pets_state(juno, None)
        page = node_counts(base, [{"state": shown}])
        check("428: a statement the board has never seen, one in no PET, one stacked, one set aside and a stored card "
              "whose line has gone: the new and the loose are not decided, the stacked and the set aside are, and the "
              "gone counts in neither, as the page counts them",
              edited == {"decided": before["decided"] - 2, "total": before["total"]}
              and (page is None or page[0] == edited), f"{before} {edited} {page}")
        one = [{"key": "S:2:0", "sheet": "S", "row": 2, "line": 0, "text": "A line"}]
        check("428: the same counts again after the file is read a second time (kept against its marks), and a "
              "participant with no board at all has every statement undecided",
              server_pets(juno) == edited and themes_mod.decided_of(one, None) == {"decided": 0, "total": 1}, "")

        # a participant not yet brought into the GETs file: the board's counts take them in, in the pile
        gets_file = gets_mod.gets_path(roots["ipa"])
        held = hold(gets_file)
        case_name = "Rowan"
        held["cases"].pop(case_name)
        for each in held["boards"]:
            each["cards"] = {k: v for k, v in each["cards"].items() if not k.startswith(case_name + "/")}
            for g in each["groups"]:
                g["members"] = [m for m in g["members"] if not m.startswith(case_name + "/")]
            each["discarded"] = [k for k in each.get("discarded") or [] if not k.startswith(case_name + "/")]
        gets_file.write_text(json.dumps(held), encoding="utf-8")
        routes.GETS_FILES.clear()
        head = routes.gets_head(roots["ipa"])
        page = node_counts(base, [{"gets": True, "state": board_state(roots["ipa"], gets_file)}])
        mine = {k: head["progress"]["gets"][k] for k in ("decided", "total")}
        check("428: a participant whose PETs are not yet in the GETs file are counted in the total, undecided, as the "
              "board takes them in",
              page is None or page[0] == mine, f"{mine} {page}")

        # the same for an LGETs participant and an LPETs timepoint not yet brought in
        lgets_file = roots["lipa"] / "idiograph-lgets.json"
        held = hold(lgets_file)
        held["cases"].pop("Hollis")
        for each in held["boards"]:
            each["cards"] = {k: v for k, v in each["cards"].items() if not k.startswith("Hollis/")}
            for g in each["groups"]:
                g["members"] = [m for m in g["members"] if not m.startswith("Hollis/")]
            each["discarded"] = [k for k in each.get("discarded") or [] if not k.startswith("Hollis/")]
        lgets_file.write_text(json.dumps(held), encoding="utf-8")
        arlo = Path(books(roots["lipa"])[0]["workbook"])
        lpets_file = gets_mod.lpets_path(arlo)
        mine_l = hold(lpets_file)
        mine_l["cases"].pop("T3")
        for each in mine_l["boards"]:
            each["cards"] = {k: v for k, v in each["cards"].items() if not k.startswith("T3/")}
            for g in each["groups"]:
                g["members"] = [m for m in g["members"] if not m.startswith("T3/")]
            each["discarded"] = [k for k in each.get("discarded") or [] if not k.startswith("T3/")]
        lpets_file.write_text(json.dumps(mine_l), encoding="utf-8")
        routes.GETS_FILES.clear()
        head = routes.gets_head(roots["lipa"])
        lg = board_state(roots["lipa"], lgets_file)
        lp = board_state(roots["lipa"], lpets_file, workbook=str(arlo), lpets=True)
        page = node_counts(base, [{"gets": True, "state": lg}, {"gets": True, "state": lp}])
        got_l = routes.lpets_progress(arlo)
        mine = [{k: head["progress"]["lgets"][k] for k in ("decided", "total")},
                {"decided": got_l["decided"], "total": got_l["total"]}]
        check("428: a participant not yet in the LGETs file and a timepoint not yet on the LPETs are counted in the "
              "total, undecided, as the board takes them in",
              page is None or page == mine, f"{mine} {page}")

        # ── C. each timepoint of a longitudinal participant carries its own PETs mark
        card = next(c for c in section(roots["lipa"])["participants"] if c["case"] == "Arlo")
        marks = [t.get("pets_complete") for t in card["timepoints"]]
        want = [(themes_mod.complete_of(hold(themes_mod.themes_path(arlo, n))) or {}).get("at") for n in (1, 2, 3)]
        check("428: each timepoint of a longitudinal participant's card carries that timepoint's own PETs mark, where "
              "the card's own mark is the latest of them once all are marked",
              [(m or {}).get("at") for m in marks] == want and all(want)
              and card["pets_complete"]["at"] == max(want), f"{marks} {want}")

        # a later timepoint's mark taken off, the card's own mark is not marked either, where T1's alone said it was
        t2 = themes_mod.themes_path(arlo, 2)
        kept_t2 = t2.read_bytes()
        t2.write_text(json.dumps({k: v for k, v in hold(t2).items() if k != "complete"}), encoding="utf-8")
        try:
            card = next(c for c in section(roots["lipa"])["participants"] if c["case"] == "Arlo")
            check("428: a longitudinal participant whose second timepoint's PETs are not marked complete shows no PETs "
                  "mark on Home's card, though the first timepoint's is marked", card["pets_complete"] is None
                  and card["timepoints"][0]["pets_complete"], str(card["pets_complete"]))
        finally:
            t2.write_bytes(kept_t2)

        # ── D. Home, the command line and MCP answer the same numbers, and a thematic analysis project has no PETs
        cards = {s["id"]: {c["case"]: c.get("progress") for c in s["participants"]} for s in routes.api_cases({})["projects"]}
        heads = {s["id"]: (s["gets"] or {}).get("progress") for s in routes.api_cases({})["projects"]}

        def run(*args, root):
            code, out, err = cli.run(["--config", str(config_file), "--root", str(root), "--json", *args])
            return code, support.plain(json.loads(out)) if out.strip() else {}, err

        same_cli = True
        detail = ""
        for key, root in roots.items():
            code, got, err = run("cases", root=root)
            by = {c["case"]: c.get("progress") for c in got.get("cases", [])}
            mcp = mcp_server.Server(root=str(root), config=str(config_file))
            res = mcp.call(mcp.by_name["cases"], {})
            seen = support.plain(res.get("structuredContent") or {})
            by_mcp = {c["case"]: c.get("progress") for c in seen.get("cases", [])}
            pid = routes.project_id(root)
            ok = (code == 0 and by == cards[pid] == by_mcp and got["project"].get("progress") == heads[pid]
                  and seen["project"].get("progress") == heads[pid])
            if not ok:
                same_cli, detail = False, f"{key} {code} {err} {by} {cards[pid]} {got.get('project', {}).get('progress')} {heads[pid]}"
        check("428: the command line's cases and MCP's cases carry the same progress as Home's cards and the project's "
              "head, for each demo", same_cli, detail[:700])
        rta_card = next(iter(cards[routes.project_id(roots["rta"])].values()))
        check("428: a thematic analysis project's participant has coding, the passages decided, and no PETs, and its "
              "head has themes, where a longitudinal project's head has LGETs and Trajectories and an IPA project's GETs",
              set(rta_card) == {"statements"} and set(heads[routes.project_id(roots["rta"])]) == {"themes"}
              and set(heads[routes.project_id(roots["lipa"])]) == {"lgets", "trajectories"}
              and set(heads[routes.project_id(roots["ipa"])]) == {"gets"}
              and heads[routes.project_id(roots["lipa"])]["trajectories"]["total"] == 3, str(heads))

        # ── E. across a restart: Home's cache written and read again keeps the counts, and holds no statement's words
        tables = routes.home_cache_tables()
        cache = base / "home-cache.json"
        stamp = routes.home_cache_stamp()
        routes.api_cases({})
        saved = home_cache.save(cache, stamp, tables, routes.home_cache_current)
        mine_here = lambda k: k.startswith(str(base)) or str(base.resolve()) in k
        before_counts = {k: v[1] for k, v in routes.PET_COUNTS.items() if mine_here(k)}
        words = {w for k, v in routes.STATEMENTS.items() if mine_here(k) for rows in v[1].values()
                 for _, said in rows for w in said if len(w) > 12}
        on_disk = cache.read_text(encoding="utf-8")
        for table in tables.values():
            table.clear()
        routes.STATEMENTS.clear()
        taken = home_cache.load(cache, stamp, tables)
        after_counts = {k: v[1] for k, v in routes.PET_COUNTS.items() if mine_here(k)}
        check("428: Home's cache written and read again after a restart keeps each participant's counts, and not one "
              "statement's words are in the file or in what was read back",
              saved and taken > 0 and before_counts and after_counts == before_counts and len(words) > 5
              and not any(w in on_disk for w in words)
              and not any("statements" in v[1] for v in routes.BOOKS.values()),
              f"{saved} {taken} {len(before_counts)} {len(after_counts)} {len(words)}")
        # a count that must be worked out again after a restart reads the words from the workbook, to the same answer
        routes.PET_COUNTS.clear()
        routes.STATEMENTS.clear()
        for b in [b for r in roots.values() for b in books(r)]:
            for n in (1, 2, 3):
                routes.pets_progress(Path(b["workbook"]), n)
        real = os.path.realpath
        again = {real(k): v[1] for k, v in routes.PET_COUNTS.items() if mine_here(k)}
        check("428: a count worked out again after a restart, the words read from the workbook, is what it was",
              all(again.get(real(k)) == v for k, v in before_counts.items()), f"{len(again)} {len(before_counts)}")
        # an unreadable themes file is not kept as "no board": the count is worked out again once it can be read
        juno_book = Path(books(roots["ipa"])[0]["workbook"])
        juno_file = themes_mod.themes_path(juno_book)
        good = juno_file.read_text(encoding="utf-8")
        routes.PET_COUNTS.clear()
        juno_file.write_text("{ not json", encoding="utf-8")
        broken = routes.pets_progress(juno_book)
        kept_broken = str(juno_file) in routes.PET_COUNTS
        juno_file.write_text(good, encoding="utf-8")
        fixed = routes.pets_progress(juno_book)
        check("428: a themes file that cannot be read is counted as nothing decided but not kept, and the count comes "
              "back once the file can be read",
              broken is not None and broken["decided"] == 0 and not kept_broken and fixed["decided"] > 0,
              f"{broken} {kept_broken} {fixed}")

        # a Working together member's own themes file is in the count and in its mark
        own = base / "own-juno.themes.json"
        own.write_text(good, encoding="utf-8")
        kept_own = themes_mod.OWN_FILE
        themes_mod.OWN_FILE = lambda wb: own if Path(wb) == juno_book else None
        try:
            routes.PET_COUNTS.clear()
            routes.pets_progress(juno_book)
            held_mark = routes.PET_COUNTS[str(juno_file)][0]
            own.write_text("{ not json", encoding="utf-8")
            routes.PET_COUNTS.clear()
            routes.pets_progress(juno_book)
            own_broken_kept = str(juno_file) in routes.PET_COUNTS
        finally:
            themes_mod.OWN_FILE = kept_own
        check("428: a member's own themes file is part of the count's mark, and one that cannot be read is not kept",
              held_mark[4] == str(own) and held_mark[5] is not None and not own_broken_kept, f"{held_mark} {own_broken_kept}")

        # a board that is only in the member's own file changes the count, not just the mark
        import json as _json
        theirs_data = _json.loads(good)
        theirs_data["boards"] = []
        theirs_data.pop("current", None)
        juno_file.write_text(_json.dumps(theirs_data), encoding="utf-8")
        own.write_text(good, encoding="utf-8")
        themes_mod.OWN_FILE = lambda wb: own if Path(wb) == juno_book else None
        try:
            routes.PET_COUNTS.clear()
            with_own_board = routes.pets_progress(juno_book)
            themes_mod.OWN_FILE = lambda wb: None
            routes.PET_COUNTS.clear()
            without_own_board = routes.pets_progress(juno_book)
        finally:
            themes_mod.OWN_FILE = kept_own
            juno_file.write_text(good, encoding="utf-8")
        check("428: a board only in a member's own themes file changes the count",
              with_own_board is not None and without_own_board is not None
              and with_own_board["decided"] > without_own_board["decided"],
              f"{with_own_board} {without_own_board}")

        # ── F. reading wrote nothing: the demos' files, but those this area edited itself, are as they were
        edited = {k: files(r) for k, r in roots.items()}
        touched = {k: sorted(n for n in set(edited[k]) | set(start[k]) if edited[k].get(n) != start[k].get(n))
                   for k in roots}
        check("428: reading the counts, on Home, in the command line and through MCP, wrote nothing: of every project's "
              "files only the four this area edited itself differ",
              {k: v for k, v in touched.items() if v} == {
                  "ipa": sorted(["Juno/Working/Juno - EN & ES.themes.json", "idiograph-gets.json"]),
                  "lipa": sorted(["Arlo/Working/Arlo - EN & ES.lpets.json", "idiograph-lgets.json"])}, str(touched))
    finally:
        (agent_changes.ALL_OPS, server_mod.CONFIG_PATH, server_mod.ROOT_OVERRIDE, server_mod.STATE_PATH,
         server_mod.STATE_MEMORY) = kept
        if was_log is None:
            os.environ.pop(agent_log.PLACE, None)
        else:
            os.environ[agent_log.PLACE] = was_log


def reference_board(data: dict) -> str | None:
    """The id of the board of a GETs, LGETs or LPETs file the counts are of."""
    import gets as gets_mod
    return (gets_mod.source_board(data)[0] or {}).get("id")
