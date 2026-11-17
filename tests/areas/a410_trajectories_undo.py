"""Area 410: Undo and Redo on the Trajectories screen (trajundo, 16 November 2026, Adam's ruling that every tab's
toolbar ends with them).

Each change the screen makes through `/api/trajectories-ops` with `step` is one step of its undo, every file it wrote
kept as it was before and after (`trajectories.Watch`, `step_kept`), and `/api/trajectories-undo` puts them back. What
is checked, on a scratch copy of the longitudinal demo as a fresh clone has it, worked on as a project of its own. A:
on opening there is nothing to undo or redo, and Undo and Redo then are refused with nothing written. B: one change, a
cell's key quote: Undo puts the LPETs file and the Trajectories file back byte for byte, and Redo puts the change back
byte for byte. C: several in a row, a key quote's bold, a state, a trajectory renamed, a participant moved, a picture of
the set and one of his own: undone one by one the project reads as before them, every file byte for byte (the History
of the project and the pictures' _Archive aside), and redone one by one as after them; one Undo more is refused,
nothing written. D: a change after an Undo clears Redo. E: a dry run, and the LPETs screen's domain sent without
`step`, keep no step. F: an agent's change over a file of his last step (the command line, never these steps) drops
them: the board answers nothing to undo, and an Undo asked straight after the agent's write, before any read, is
refused in one line with nothing written. G: the page holds the buttons, their keys, and the route's flag."""
from __future__ import annotations

import base64
import json
import os
import shutil
from pathlib import Path

from . import support
from .a394_lipa_demo import as_cloned
from .support import check as said_check

WHO = "Arlo"


def check(name, ok, detail=""):
    said_check(name, bool(ok), "" if ok else str(detail)[:700])


def test_trajectories_undo(scratch: Path):
    print("\n410. Undo and Redo on the Trajectories screen: each change one step, every file it wrote put back byte "
          "for byte and made again, several in a row, Redo cleared by a new change, nothing written with nothing to "
          "undo, and an agent's change over his steps dropping them (trajundo, 16 November)")
    import agent_log
    import cli
    import gets as gets_mod
    import idiograph_routes as routes
    import server as server_mod
    import trajectories as traj_mod
    from server import WorkbookError

    fresh = scratch / "undo-410-clone"
    shutil.rmtree(fresh, ignore_errors=True)
    shutil.copytree(support.source("demo"), fresh, ignore=as_cloned)
    kept = (server_mod.DEMO_DIR, server_mod.SHIPPED_DEMO, os.environ.get(agent_log.PLACE), server_mod.CONFIG_PATH)
    cfg = scratch / "undo-410-config.json"
    cfg.write_text(json.dumps({"projects": [], "interviewer": "Interviewer", "corpus": "", "gravity_reference": "",
                               "corpus_exclude": []}), encoding="utf-8")
    try:
        server_mod.DEMO_DIR = server_mod.SHIPPED_DEMO = fresh
        os.environ[agent_log.PLACE] = str(scratch / "undo-410-agent-log.json")
        demo = server_mod.demo_lipa_dir()
        routes.fill_demo()
        root = scratch / "undo-410-allotment"
        shutil.rmtree(root, ignore_errors=True)
        shutil.copytree(demo, root, ignore=shutil.ignore_patterns("pristine", "source"))
        cfg.write_text(json.dumps({"projects": [{"root": str(root)}], "interviewer": "Interviewer", "corpus": "",
                                   "gravity_reference": "", "corpus_exclude": []}), encoding="utf-8")
        server_mod.CONFIG_PATH = cfg
        routes.api_project({"root": str(root), "agents": True})
        book = next(root.glob(f"{WHO}/{WHO} - *.xlsx"))
        lpfile = gets_mod.lpets_path(book)
        tjfile = traj_mod.path_of(root)
        project = root / server_mod.PROJECT_FILE

        def call(route: str, body: dict) -> dict:
            with routes.route_scope(route, body):
                return server_mod.ROUTES[route](body)

        def refused(route: str, body: dict) -> str:
            try:
                call(route, body)
            except WorkbookError as exc:
                return str(exc)
            return "answered"

        def ops(*given, step=True, **more) -> dict:
            return call("/api/trajectories-ops", dict({"workbook": str(book), "ops": list(given)},
                                                      **({"step": True} if step else {}), **more))

        def undo(redo=False) -> dict:
            return call("/api/trajectories-undo", {"workbook": str(book), "redo": redo})

        def tree() -> dict:
            # every file of the project but the project's History, which keeps its line of each change, the archive
            # copies a change or an undo adds to, and the locks
            return {p.relative_to(root).as_posix(): p.read_bytes() for p in sorted(root.rglob("*"))
                    if p.is_file() and "_Archive" not in p.parts and p.name != "idiograph-history.json"
                    and not p.name.endswith(".lock")}

        def differs(a: dict, b: dict) -> list:
            return sorted(k for k in set(a) | set(b) if a.get(k) != b.get(k))

        def cell(answer: dict, lpet: str, tp: str) -> dict:
            person = next(p for p in answer["participants"] if p["case"] == WHO)
            return next(r for r in person["rows"] if r["id"] == lpet)["cells"][tp]

        # ── A. nothing to undo on opening, and Undo and Redo then write nothing
        first = call("/api/trajectories", {"workbook": str(book)})
        start = tree()
        nothing = refused("/api/trajectories-undo", {"workbook": str(book)})
        nothing_redo = refused("/api/trajectories-undo", {"workbook": str(book), "redo": True})
        check("410: on opening there is nothing to undo or redo, and Undo and Redo are refused, nothing written",
              first.get("steps") == {"undo": False, "redo": False} and nothing != "answered"
              and nothing_redo != "answered" and tree() == start, [first.get("steps"), nothing, nothing_redo])

        # ── B. one change, Undo byte for byte, Redo byte for byte
        lp0, tj0 = lpfile.read_bytes(), tjfile.read_bytes()
        was = cell(first, "G1", "T1")
        other = next(c["key"] for c in was["choices"] if not c.get("chosen") and c["key"] != (was.get("quote") or {}).get("key"))
        done = ops({"op": "quote", "participant": WHO, "lpet": "G1", "timepoint": "T1", "quote": other})
        lp1, tj1 = lpfile.read_bytes(), tjfile.read_bytes()
        check("410: a key quote ticked is one step, its LPETs file and the Trajectories file written",
              done.get("steps") == {"undo": True, "redo": False} and lp1 != lp0 and tj1 != tj0, done.get("steps"))
        back = undo()
        check("410: Undo puts the LPETs file and the Trajectories file back byte for byte, and the whole project as "
              "it was", lpfile.read_bytes() == lp0 and tjfile.read_bytes() == tj0 and tree() == start
              and back.get("steps") == {"undo": False, "redo": True}, differs(tree(), start))
        check("410: the board answers the key quote as it was", cell(back, "G1", "T1").get("quote") == was.get("quote"),
              [cell(back, "G1", "T1").get("quote"), was.get("quote")])
        again = undo(redo=True)
        check("410: Redo puts the change back byte for byte",
              lpfile.read_bytes() == lp1 and tjfile.read_bytes() == tj1
              and again.get("steps") == {"undo": True, "redo": False}, again.get("steps"))
        undo()
        check("410: and Undo again puts it back as it was", tree() == start, differs(tree(), start))

        # ── C. several in a row
        quote = (cell(first, "G2", "T2").get("quote") or {}).get("text") or ""
        png = traj_mod.png_write(4, 4, bytearray([120, 90, 60, 255] * 16))
        picture = "data:image/png;base64," + base64.b64encode(png).decode("ascii")
        column = first["columns"][0]
        elsewhere = next(c["id"] for c in first["columns"] if c["id"] != (next(
            p for p in first["participants"] if p["case"] == WHO).get("column")))
        acts = [
            ({"op": "bold", "participant": WHO, "lpet": "G2", "timepoint": "T2", "spans": [[0, min(5, len(quote))]]},),
            ({"op": "state", "participant": WHO, "lpet": "G3", "timepoint": "T3", "state": "Steadier by the harvest"},),
            ({"op": "rename", "column": column["id"], "title": column["title"] + " again"},),
            ({"op": "place", "participant": WHO, "column": elsewhere},),
            ({"op": "picture", "participant": WHO, "set": "peep07"},),
            ({"op": "picture", "participant": WHO, "data": picture},),
        ]
        trees = [tree()]
        steps = []
        for act in acts:
            steps.append(ops(*act).get("steps"))
            trees.append(tree())
        check("410: six changes in a row, each a step that changed the project",
              all(s == {"undo": True, "redo": False} for s in steps)
              and all(trees[i] != trees[i + 1] for i in range(len(acts))), steps)
        check("410: the participant's own picture went into the project's pictures folder, and the set's picture "
              "into the project file", any("pictures/" in k for k in differs(trees[5], trees[6]))
              and server_mod.PROJECT_FILE in differs(trees[4], trees[5]), [differs(trees[4], trees[5]), differs(trees[5], trees[6])])
        undone = []
        for i in range(len(acts), 0, -1):
            undo()
            undone.append(tree() == trees[i - 1])
        check("410: undone one by one, the project reads as before each change, every file byte for byte",
              all(undone) and tree() == start, [undone, differs(tree(), start)])
        left = refused("/api/trajectories-undo", {"workbook": str(book)})
        check("410: one Undo more is refused, nothing written", left != "answered" and tree() == start, left)
        redone = []
        for i in range(1, len(acts) + 1):
            undo(redo=True)
            redone.append(tree() == trees[i])
        check("410: redone one by one, the project reads as after each change, byte for byte, his own picture written "
              "back", all(redone), redone)
        more = refused("/api/trajectories-undo", {"workbook": str(book), "redo": True})
        check("410: one Redo more is refused, nothing written", more != "answered" and tree() == trees[-1], more)

        # ── D. a change after an Undo clears Redo
        undo()
        undo()
        mid = tree()
        new = ops({"op": "note", "participant": WHO, "note": "Asked next door by midsummer"})
        check("410: a change after an Undo clears Redo", new.get("steps") == {"undo": True, "redo": False}
              and refused("/api/trajectories-undo", {"workbook": str(book), "redo": True}) != "answered", new.get("steps"))
        undo()
        check("410: and its Undo puts back the project as the Undo left it", tree() == mid, differs(tree(), mid))
        undone_too = undo()
        check("410: the steps before it are undone as before", tree() == trees[-4]
              and undone_too.get("steps", {}).get("redo") is True, differs(tree(), trees[-4]))

        # ── E. a dry run, and the LPETs screen's domain, keep no step
        before = tree()
        held = call("/api/trajectories", {"workbook": str(book)})["steps"]
        dry = ops({"op": "rename", "column": column["id"], "title": "Not kept"}, dry_run=True)
        check("410: a dry run writes nothing and keeps no step", tree() == before and dry.get("steps") == held, dry.get("steps"))
        ops({"op": "domain", "participant": WHO, "lpet": "G1", "domain": "Ground"}, step=False)
        lp_domain = lpfile.read_bytes()
        state = call("/api/trajectories", {"workbook": str(book)})["steps"]
        check("410: the LPETs screen's domain, sent without step, keeps none, and the steps it wrote over are dropped",
              state == {"undo": False, "redo": False}
              and refused("/api/trajectories-undo", {"workbook": str(book)}) != "answered"
              and lpfile.read_bytes() == lp_domain, state)

        # ── F. an agent's change over his last step's file drops the steps
        ops({"op": "describe", "column": column["id"], "description": "They found their feet."})
        spec = scratch / "undo-410-spec.json"
        spec.write_text(json.dumps([{"op": "rename", "column": column["id"], "title": "Settled"}]), encoding="utf-8")
        code, out, err = cli.run(["--root", str(root), "--config", str(cfg), "trajectories", "apply", "--ops", str(spec),
                                  "--note", "Rename the first trajectory", "--tool", "Claude Code", "--json"])
        agent_wrote = tree()
        said = refused("/api/trajectories-undo", {"workbook": str(book)})
        check("410: an Undo straight after an agent's write over his last step is refused in one line, nothing written",
              code == 0 and said != "answered" and "\n" not in said and tree() == agent_wrote, [code, err, said])
        state = call("/api/trajectories", {"workbook": str(book)})["steps"]
        check("410: and the board then answers nothing to undo or redo", state == {"undo": False, "redo": False}, state)
        ops({"op": "describe", "column": column["id"], "description": "They found their feet again."})
        cli.run(["--root", str(root), "--config", str(cfg), "trajectories", "apply", "--ops", str(spec),
                 "--note", "Rename it again", "--tool", "Claude Code", "--json"])
        spec.write_text(json.dumps([{"op": "rename", "column": column["id"], "title": "Settled in"}]), encoding="utf-8")
        cli.run(["--root", str(root), "--config", str(cfg), "trajectories", "apply", "--ops", str(spec),
                 "--note", "Rename it again", "--tool", "Claude Code", "--json"])
        state = call("/api/trajectories", {"workbook": str(book)})["steps"]
        check("410: any read after an agent's change finds no step to offer", state == {"undo": False, "redo": False}, state)

        # ── H. a file that cannot be read, two archived in one second, the bytes kept (trajfix)
        real = traj_mod._bytes_of
        failing = {"path": None}

        def flaky(path):
            if failing["path"] is not None and Path(path) == failing["path"]:
                failing["path"] = None
                return traj_mod.UNREAD
            return real(path)

        traj_mod._bytes_of = flaky
        try:
            failing["path"] = tjfile
            ops({"op": "describe", "column": column["id"], "description": "A change whose file would not read."})
            state = call("/api/trajectories", {"workbook": str(book)})["steps"]
            check("410: a change with a file that could not be read before it keeps no step",
                  failing["path"] is None and state == {"undo": False, "redo": False}, [failing, state])
            ops({"op": "describe", "column": column["id"], "description": "A change that reads."})
            before_undo = tree()
            failing["path"] = tjfile
            said = refused("/api/trajectories-undo", {"workbook": str(book)})
            state = call("/api/trajectories", {"workbook": str(book)})["steps"]
            check("410: an Undo with a file that cannot be read is refused in one line, nothing written, the step kept",
                  said != "answered" and "\n" not in said and tree() == before_undo
                  and state == {"undo": True, "redo": False}, [said, state])
            back = undo()
            check("410: and the Undo then goes through", back.get("steps", {}).get("redo") is True
                  and tree() != before_undo, back.get("steps"))
        finally:
            traj_mod._bytes_of = real
        keep = root / "_Archive"
        moved = []
        for n in range(2):
            victim = root / f"undo-410-victim{n}.txt"
            victim.write_text(str(n), encoding="utf-8")
            traj_mod._put(victim, None, "2026-11-16T22:00:00")
            moved.append(victim)
        mine = sorted(keep.glob("undo-410-victim*"))
        check("410: two files archived in one second keep their own copies", len(mine) == 2
              and {p.read_text(encoding="utf-8") for p in mine} == {"0", "1"}, [p.name for p in mine])
        small = traj_mod.UNDO_BYTES
        traj_mod.UNDO_BYTES = 6000
        try:
            key = f"{str(root.resolve())}"
            traj_mod._STEPS.pop(key, None)
            watch = traj_mod.Watch()
            for n in range(5):
                watch.before.clear()
                fake = root / "undo-410-held.bin"
                fake.write_bytes(bytes([n]) * 2000)
                watch.before[fake] = bytes([n + 100]) * 2000
                traj_mod.step_kept(root, watch, [f"step {n}"])
            held = traj_mod._STEPS[key]["undo"]
            check("410: a project's steps hold only so many bytes, the oldest dropped first and the newest kept",
                  1 <= len(held) < 5 and held[-1]["what"] == ["step 4"], [len(held), [h["what"] for h in held]])
        finally:
            traj_mod.UNDO_BYTES = small
            traj_mod._STEPS.pop(str(root.resolve()), None)
            (root / "undo-410-held.bin").unlink(missing_ok=True)

        # ── G. the page
        html = (support.source("apps") / "idiograph" / "static" / "idiograph.html").read_text(encoding="utf-8")
        js = (support.source("apps") / "idiograph" / "static" / "trajectories.js").read_text(encoding="utf-8")
        bar = html.split('id="tj-bar"', 1)[1].split("</div>", 1)[0]
        buttons = [bar[bar.index(f'id="{i}"'):].split("</button>", 1)[0] for i in ("tj-undo", "tj-redo")]
        check("410: the Trajectories toolbar ends with Undo and Redo, the boards' buttons, never greyed out",
              bar.index('id="tj-export"') < bar.index('id="tj-undo"') < bar.index('id="tj-redo"')
              and not any("disabled" in x for x in buttons) and "undo_cmd_z" in bar and "redo_shift_cmd_z" in bar, bar[:300])
        check("410: pressed with nothing to undo or redo the page says the boards' lines",
              "sayNothingToUndo(backwards)" in js
              and "disabled" not in js.split("function trajStepsDraw", 1)[1].split("}", 1)[0], "")
        check("410: the page sends each change as a step, asks the undo route, and takes Cmd + Z and Shift + Cmd + Z "
              "outside a field", "step: true" in js and "/api/trajectories-undo" in js and "REDO_Y(e)" in js
              and "trajUndo(!e.shiftKey" in js, "")
    finally:
        server_mod.DEMO_DIR, server_mod.SHIPPED_DEMO, server_mod.CONFIG_PATH = kept[0], kept[1], kept[3]
        if kept[2] is None:
            os.environ.pop(agent_log.PLACE, None)
        else:
            os.environ[agent_log.PLACE] = kept[2]
