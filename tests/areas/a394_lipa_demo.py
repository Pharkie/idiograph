"""Area 394: the longitudinal IPA demo, First year on an allotment (lipabuild, 13 November 2026).

Adam, 12 November 2026: a third demo beside the IPA and thematic analysis demos, three invented participants each
interviewed at three timepoints, opened from Home, its recordings downloaded on demand like the others.

What is checked, on the demo as committed and copies of it. A: it is a project of three timepoints with its labels
and descriptions, Home answers it as the third demo with its three participants in the study's order, each with
their own label, picture and pen portrait, every timepoint's Statements and PETs complete, and the command line and
the MCP server name it `--demo lipa`. B: each participant's PETs board at every timepoint, their LPETs with each
LPET's row at every timepoint (a state and a key quote, bold in it where the analysis gives bold), the LGETs marked
complete and Trajectories with every participant placed, all read through the app's own routes, and every board laid
out across the screen, never one long column. C: the build gives the shipped files byte for byte, and Reset demo puts
a changed LPETs board and Trajectories back. D: the manifest names each of its nine recordings for the interviews
as they stand, at the IPA demo's release, and a build stages it with no recording. E: with none on this computer
its player offers the nine as a download of their own, apart from the IPA demo's, and Download fetches, checks and
places them where each timepoint's player finds them (when this computer holds the nine; they are not committed)."""
from __future__ import annotations

import hashlib
import http.server
import json
import os
import shutil
import tempfile
import threading
from pathlib import Path

from . import support
from .support import check


def ck(name: str, condition, detail="") -> None:
    check(name, bool(condition), "" if condition else str(detail)[:600])


class Stand(http.server.BaseHTTPRequestHandler):
    """GitHub's release downloads stood in for on loopback, each path a file's bytes."""
    files: dict = {}
    asked: list = []

    def do_GET(self):
        Stand.asked.append(self.path)
        data = Stand.files.get(self.path)
        self.send_response(200 if data is not None else 404)
        self.send_header("Content-Length", str(len(data or b"")))
        self.end_headers()
        if data:
            self.wfile.write(data)

    def log_message(self, *args):
        pass


def tall_column(board: dict) -> bool:
    """Whether a board's top-level labels stand in one column, every one at the same x, three or more of them."""
    groups = board.get("groups") or []
    inner = {m for g in groups for m in g.get("members") or []}
    tops = [g for g in groups if g["id"] not in inner]
    return len(tops) >= 3 and len({round(float(g.get("x") or 0)) for g in tops}) == 1


def as_cloned(folder: str, names: list[str]) -> list[str]:
    """What a copy of the repo's demo leaves out to stand as a fresh clone's: the files the gitignore keeps out, which
    a run or a build makes beside the participants (their Working/ and Source/, the root's boards and exports, backups,
    pictures and recordings), every pristine copy kept whole."""
    if "pristine" in Path(folder).parts:
        return []
    made = {"Working", "Source", "_Archive", "pictures", "idiograph-gets.json", "idiograph-codes.json",
            "idiograph-lgets.json", "idiograph-trajectories.json"}
    return [n for n in names if n in made or n.endswith(".m4a")]


def shipped_parts(scratch: Path, root: Path) -> None:
    """Parts A to C, on `root`, the longitudinal demo the server works on."""
    import cli as family_cli
    import demo_recordings as demo_rec
    import gets as gets_mod
    import idiograph_routes as routes
    import make_demo
    import make_demo_lipa as lipa
    import server as server_mod
    import themes as themes_mod
    import trajectories as traj_mod

    books = routes.demo_workbooks(root)

    # ── A. a project of three timepoints, the third demo on Home
    project = routes.read_project(root)
    tps = routes.root_timepoints(root)
    home = routes.api_cases({})
    cards = home.get("demo_lipa_participants") or []
    people = json.loads((root / "idiograph-project.json").read_text(encoding="utf-8"))["participants"]
    ck("394: the longitudinal demo is a project of three timepoints, T1 Before the season, T2 Midsummer and T3 After "
       "the harvest, fixed as a demo is, named back as demo-lipa",
       [(t["label"], t["description"]) for t in tps] == [("T1", "Before the season"), ("T2", "Midsummer"),
                                                         ("T3", "After the harvest")]
       and project["demo"] is True and project["id"] == "demo-lipa" and routes.project_id(root) == "demo-lipa"
       and server_mod.project_named("demo-lipa") == root and server_mod.is_demo_root(root)
       and server_mod.demo_root_of(books[0]) == root and server_mod.project_of(books[0]) == root,
       json.dumps(project, default=str)[:300])
    ck("394: Home answers it as the third demo, Hollis, Nell and Arlo in the study's order, each with their own label, "
       "a picture from the set and a pen portrait, and every timepoint's statements complete",
       [c["case"] for c in cards] == ["Hollis", "Nell", "Arlo"] and home["demo_lipa_project"]["name"] == "First year on an allotment"
       and [people[c]["label"] for c in ("Hollis", "Nell", "Arlo")] == ["The new lad at the gate", "The mother of two",
                                                                      "The reluctant gardener"]
       and all(str(people[c]["picture"]).startswith("set:") and len(people[c]["portrait"]) > 200 for c in people)
       and all([(t["label"], t["state"]) for t in c["timepoints"]] == [("T1", "complete"), ("T2", "complete"),
                                                                     ("T3", "complete")] for c in cards),
       json.dumps([{k: c.get(k) for k in ("case", "timepoints")} for c in cards], default=str)[:400])
    ck("394: the command line and the MCP server name it `--demo lipa`, beside `--demo ta` and the IPA demo's `--demo`",
       family_cli.demo_words(["--demo", "lipa", "cases"]) == ["--demo", "--demo-lipa", "cases"]
       and family_cli.demo_asked(["--demo=lipa"]) == "lipa" and family_cli.demo_asked(["--demo", "ta"]) == "ta"
       and family_cli.demo_asked(["--demo"]) is True and server_mod.demo_dir_of("lipa") == root
       and server_mod.demo_dir_of("demo-lipa") == root and server_mod.demo_dir_of("ta") == server_mod.demo_ta_dir())

    # ── B. its boards, read through the app's own routes
    plan = lipa.read_analysis()
    pets_ok, pets_said, columns = True, [], []
    for name, book in zip(lipa.CASES, books):
        for n, tp in enumerate(lipa.TIMEPOINTS, start=1):
            with themes_mod.scoped(n):
                head = themes_mod.pets_complete_of(book)
                board = routes.api_themes({"workbook": str(book)})
            want = plan["cases"][name]["timepoints"][tp]["board"]["pets"]
            titles = {g["label"] for g in board["groups"]}
            if not head or not all(p["title"] in titles for p in want):
                pets_ok = False
                pets_said.append(f"{name} {tp}")
            columns.append(tall_column(board))
    ck("394: each participant's PETs board at each timepoint holds the analysis's PETs, Current and marked complete",
       pets_ok, pets_said)

    with routes.lpets_scope(books[1]):
        lp = gets_mod.load(root)
    lp_board = themes_mod.find_version(lp, lp.get("chosen") or lp.get("current"))
    traj = routes.api_trajectories({"workbook": str(books[0])})
    rows = {p["case"]: p["rows"] for p in traj["participants"]}
    want_bold = sum(1 for c in lipa.CASES for l in plan["cases"][c]["lpets"]["lpets"]
                    for r in (l.get("rows") or {}).values() if r.get("bold"))
    cells = [cell for c in lipa.CASES for r in rows.get(c, []) for cell in r["cells"].values()]
    ck("394: each participant's LPETs are their analysis's, marked complete, each LPET a row at T1, T2 and T3 with its "
       "state and its key quote ticked, and bold where the analysis gives it",
       lp.get("complete") and len(lp_board["groups"]) >= len(plan["cases"]["Nell"]["lpets"]["lpets"])
       and all(len(rows.get(c, [])) == len(plan["cases"][c]["lpets"]["lpets"]) for c in lipa.CASES)
       and all(set(r["cells"]) == {"T1", "T2", "T3"} for c in lipa.CASES for r in rows[c])
       and all(cell["state"] and cell["chosen"] and cell["quote"] and cell["quote"]["text"] for cell in cells)
       and sum(1 for cell in cells if cell["bold"]) == want_bold and all(r["domain"] for c in lipa.CASES for r in rows[c]),
       json.dumps({c: len(rows.get(c, [])) for c in lipa.CASES}))
    head = routes.api_gets_head({"workbook": str(books[0])})["gets"]
    placed = {p["case"]: p.get("column") for p in traj["participants"]}
    ck("394: the LGETs are the project's board across the three, marked complete, and Trajectories has its three "
       "trajectories, each described and coloured, with every participant placed and a note on why",
       head.get("lgets") and head.get("done") and head.get("themes") == len(plan["lgets"]["lgets"])
       and [c["title"] for c in traj["columns"]] == [c["title"] for c in plan["trajectories"]["columns"]]
       and all(c["description"] and c["colour"] for c in traj["columns"])
       and all(placed.get(c) for c in lipa.CASES) and not traj["unplaced"]
       and all(p.get("note") for p in traj["participants"]), json.dumps(head))
    lgets = json.loads((root / gets_mod.LGETS_FILE).read_text(encoding="utf-8"))
    columns += [tall_column(b) for b in lgets["boards"]]
    for book in books:
        held = json.loads(gets_mod.lpets_path(book).read_text(encoding="utf-8"))
        columns += [tall_column(b) for b in held["boards"]]
    ck("394: every board it ships is laid out across the screen as Auto-arrange to a grid leaves one, its PETs, LPETs "
       "or LGETs side by side, never one long column", not any(columns), str(columns))

    # ── C. the build gives the shipped files, and Reset demo puts them back
    with tempfile.TemporaryDirectory(prefix="lipa-394-", dir=scratch) as tmp:
        built = Path(tmp) / "lipa"
        lipa.build_all(built)
        shipped = sorted(p for p in (root / "pristine").rglob("*") if p.is_file())

        def made(p: Path) -> Path:
            who = p.name.split(" - ")[0]
            if p.suffix == ".xlsx":
                return built / who / p.name
            return built / who / "Working" / p.name if p.parent.name == "Working" else built / p.name

        same = [p.relative_to(root / "pristine").as_posix() for p in shipped
                if not made(p).is_file() or made(p).read_bytes() != p.read_bytes()]
    ck("394: make_demo_lipa builds the shipped pristine copy byte for byte from its sources", shipped and not same, same)

    work = scratch / "lipa-394-reset"
    shutil.rmtree(work, ignore_errors=True)
    shutil.copytree(root, work, ignore=shutil.ignore_patterns("Source", "_Archive"))
    lp_file = gets_mod.lpets_path(work / "Nell" / "Nell - EN & ES.xlsx")
    tj_file = traj_mod.path_of(work)
    was = (lp_file.read_bytes(), tj_file.read_bytes())
    lp_file.write_text("{}", encoding="utf-8")
    tj_file.unlink()
    (work / "Hollis" / "Working" / "Hollis - EN & ES.themes-t3.json").unlink()
    make_demo.reset_all(work / "pristine", work)
    copied = make_demo.fill(work / "pristine", work)
    ck("394: Reset demo puts a changed LPETs board, a lost later timepoint's PETs and Trajectories back the way they "
       "ship, and a fill after it finds nothing missing",
       (lp_file.read_bytes(), tj_file.read_bytes()) == was and not copied
       and (work / "Hollis" / "Working" / "Hollis - EN & ES.themes-t3.json").read_bytes()
       == (root / "pristine" / "Working" / "Hollis - EN & ES.themes-t3.json").read_bytes(), str(copied))



def test_lipa_demo(scratch: Path):
    print("\n394. The longitudinal IPA demo (lipabuild)")
    import cli as family_cli
    import demo_recordings as demo_rec
    import gets as gets_mod
    import idiograph_routes as routes
    import make_demo
    import make_demo_lipa as lipa
    import server as server_mod
    import themes as themes_mod
    import trajectories as traj_mod

    # parts A to C on the demo as a fresh clone has it, its participants' workbooks and their pristine copy and none
    # of the gitignored files a run makes beside them, filled as the server's start fills it (lipafix, 13 November
    # 2026): the boards, LPETs, LGETs and Trajectories come from the pristine copy, never from what a build or an
    # earlier run left in the repo's demo, which is never written here
    fresh = scratch / "lipa-394-clone"
    shutil.rmtree(fresh, ignore_errors=True)
    shutil.copytree(support.source("demo"), fresh, ignore=as_cloned)
    kept = (server_mod.DEMO_DIR, server_mod.SHIPPED_DEMO)
    try:
        server_mod.DEMO_DIR = server_mod.SHIPPED_DEMO = fresh
        root = server_mod.demo_lipa_dir()
        boards = [b.name for n in lipa.CASES for b in make_demo.boards_of(root / "pristine", root / n / f"{n} - EN & ES.xlsx")]
        copied = {p.relative_to(root).as_posix() for p in routes.fill_demo() if root in p.parents}
        ck("394: on a fresh clone the server's start fills the longitudinal demo from its pristine copy, each participant's "
           "progress file, a PETs board a timepoint and the LPETs, and the LGETs and Trajectories",
           len(boards) == 12 and {f"{b.split(' - ')[0]}/Working/{b}" for b in boards} <= copied
           and all(f"{n}/Working/{n} - EN & ES.progress.json" in copied for n in lipa.CASES)
           and {"idiograph-lgets.json", "idiograph-trajectories.json"} <= copied, sorted(copied))
        shipped_parts(scratch, root)
    finally:
        server_mod.DEMO_DIR, server_mod.SHIPPED_DEMO = kept

    # ── D. the manifest and the build's stage
    manifest = json.loads(support.source("demo/recordings.json").read_text(encoding="utf-8"))
    rows_m = {r["file"]: r for r in manifest["recordings"]}
    names = lipa.recording_names()
    folder = support.source("packaging/recording")
    held = [n for n in names if (folder / n).is_file()]
    sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()
    ck("394: the manifest names each of the nine recordings for the interviews as they stand, named by their CSV's "
       "hash, at the same release as the IPA demo's, and each one this computer holds matches its size and sha256",
       len(names) == 9 and all(n in rows_m for n in names)
       and all(rows_m[n]["size"] == (folder / n).stat().st_size and rows_m[n]["sha256"] == sha(folder / n) for n in held)
       and manifest["release"] == demo_rec.RELEASE
       and all(r["entry"] for r in routes.demo_interviews(routes.DEMO_LIPA_RECORDINGS)[1]), str(names))
    build_mac = support.build_mac()
    stage = scratch / "lipa-394-stage"
    shutil.rmtree(stage, ignore_errors=True)
    demo = build_mac.stage_cases(stage)
    staged = demo / "lipa"
    ck("394: a build stages the longitudinal demo whole, each participant with every board file of theirs, its LGETs and "
       "Trajectories, its sources and project file, and no recording",
       all((staged / n / "Working" / f"{n} - EN & ES.{tail}").is_file() for n in lipa.CASES
           for tail in ("progress.json", "themes.json", "themes-t2.json", "themes-t3.json", "lpets.json"))
       and (staged / "idiograph-lgets.json").is_file() and (staged / "idiograph-trajectories.json").is_file()
       and (staged / "idiograph-project.json").is_file() and (staged / "source" / "analysis.json").is_file()
       and "to download" in build_mac.demo_line(demo), sorted(p.name for p in staged.iterdir()))

    # ── E. the installed app: the nine offered as a download of their own, fetched and played
    if len(held) < 9:
        support.skip("394: the longitudinal demo's recordings download on demand",
                     "this computer does not hold the nine recordings in packaging/recording (they are not committed)")
        return
    base = scratch / "lipa-394-installed"
    shutil.rmtree(base, ignore_errors=True)
    shipped_d, work_d, proj = base / "shipped", base / "work", base / "root"
    shutil.copytree(support.source("demo"), shipped_d,
                    ignore=shutil.ignore_patterns("*.m4a", "Working", "Source", "_Archive", "ta", "idiograph-gets.json",
                                                  "idiograph-lgets.json", "idiograph-trajectories.json"))
    shutil.copytree(support.source("demo/lipa/pristine/Working"), shipped_d / "lipa" / "pristine" / "Working")
    shutil.copytree(shipped_d, work_d)
    proj.mkdir()
    release = "/github/Pharkie/idiograph/releases/download/demo-recordings-1/"
    licence = folder / make_demo.AUDIO_LICENCE
    Stand.files = {release + n: (folder / n).read_bytes() for n in names}
    Stand.files[release + licence.name] = licence.read_bytes()
    Stand.asked = []
    httpd = http.server.ThreadingHTTPServer(("127.0.0.1", 0), Stand)
    threading.Thread(target=httpd.serve_forever, kwargs={"poll_interval": 0.05}, daemon=True).start()
    kept = (server_mod.DEMO_DIR, server_mod.SHIPPED_DEMO, server_mod.ROOT_OVERRIDE, server_mod.STATE_MEMORY)
    kept_env = os.environ.get("IDIOGRAPH_SEARCH_STUB")
    kept_fetches = dict(demo_rec.FETCHES)
    try:
        server_mod.DEMO_DIR, server_mod.SHIPPED_DEMO = work_d, shipped_d
        server_mod.ROOT_OVERRIDE, server_mod.STATE_MEMORY = str(proj), {"recent": []}
        os.environ["IDIOGRAPH_SEARCH_STUB"] = f"http://127.0.0.1:{httpd.server_address[1]}"
        demo_rec.FETCHES.clear()
        routes.fill_demo()
        nell = work_d / "lipa" / "Nell" / "Nell - EN & ES.xlsx"
        offered = routes.api_audio({"path": str(nell), "sheet": "T2"})
        ipa = routes.api_demo_recordings({})
        whole = sum((folder / n).stat().st_size for n in names) + licence.stat().st_size
        ck("394: with none on this computer a timepoint's player offers the longitudinal demo's nine as a download of "
           "their own, its size theirs and the licence's, apart from the IPA demo's",
           offered["found"] is False and offered["download"]["demo"] == "lipa" and offered["download"]["bytes"] == whole
           and ipa["demo"] == "ipa" and ipa["bytes"] != whole and not Stand.asked, json.dumps(offered))
        routes.api_demo_recordings({"op": "download", "demo": "lipa"})
        running = demo_rec.current(routes.DEMO_LIPA_RECORDINGS)
        if running is not None:
            running.thread.join(timeout=120)
        done = routes.api_demo_recordings({"demo": "lipa"})
        places = {(n, tp): lipa.recording(n, tp, work_d) for n, tp in lipa.interviews()}
        played = {k: routes.api_audio({"path": str(work_d / "lipa" / k[0] / f"{k[0]} - EN & ES.xlsx"), "sheet": k[1]})
                  for k in places}
        ck("394: Download fetches the nine and the licence, checks each against the manifest and puts it where its "
           "timepoint's player finds it, and each timepoint then plays its own interview",
           done["state"] == "done" and all(p.read_bytes() == (folder / lipa.committed(n, tp).name).read_bytes()
                                           for (n, tp), p in places.items())
           and all(played[k]["found"] and played[k]["name"] == f"{k[0]}-{k[1]}.m4a" for k in places)
           and sorted(Stand.asked) == sorted(Stand.files), f"{done} {len(Stand.asked)}")
    finally:
        httpd.shutdown()
        httpd.server_close()
        server_mod.DEMO_DIR, server_mod.SHIPPED_DEMO, server_mod.ROOT_OVERRIDE, server_mod.STATE_MEMORY = kept
        if kept_env is None:
            os.environ.pop("IDIOGRAPH_SEARCH_STUB", None)
        else:
            os.environ["IDIOGRAPH_SEARCH_STUB"] = kept_env
        demo_rec.FETCHES.clear()
        demo_rec.FETCHES.update(kept_fetches)
