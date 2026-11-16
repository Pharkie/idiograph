"""Area 395: an agent's first act on the GETs and LGETs makes their file as the screen's does, and a reworded quote
keeps the key quote ticked on Trajectories (getsfirst, 16 November 2026).

One API, two clients: `gets show`, `gets fresh` and `gets apply` refused a project with no GETs file yet ("It comes
with the first act on the GETs screen"), so only the app's /api/gets-save could make it. What is checked, on scratch
copies of the demos as a fresh clone has them, filled from their pristine copy, with the GETs file of the one-timepoint
demo and the LGETs file of the longitudinal one taken away. `gets show` answers the board the screen opens on, every
card in the pile, with the version `none` and nothing written, and a change carrying `none` back is refused once a
file is there (getsfix). The dry runs of `gets fresh` and `gets apply` say the file
would be made and write nothing. The real ones make it with the same participants' copies the screen's first save
makes, the change recorded as an agent's and undone by its Undo, which takes the file away again.

Then a quote reworded with `turn write` on the longitudinal demo: every Trajectories cell he ticked keeps its tick and
its key, takes the quote's new words, and his bold follows where the words survive, a check that it was already so
(quotefollow, cardsync, 13 November: the table's tick is kept by the quote's place, `<sheet>:<row>:<place>`).
"""
from __future__ import annotations

import json
import shutil
from pathlib import Path

from . import support
from .support import check as said_check


def check(name, ok, detail=""):
    said_check(name, ok, str(detail)[:700])


MADE = {"Working", "Source", "_Archive", "pictures", "idiograph-gets.json", "idiograph-codes.json",
        "idiograph-lgets.json", "idiograph-trajectories.json", "lipa", "ta"}


def as_cloned(folder: str, names: list[str]) -> list[str]:
    """What a fresh clone of the demo lacks, every pristine copy kept whole (as area 394 has it), and the other demos."""
    if "pristine" in Path(folder).parts:
        return []
    return [n for n in names if n in MADE or n.endswith(".m4a")]


def tree(at: Path) -> dict:
    """The project's files and their bytes, the lock and the record of agents' changes set aside."""
    return {p.relative_to(at).as_posix(): p.read_bytes() for p in sorted(at.rglob("*"))
            if p.is_file() and p.suffix != ".lock" and ".idiograph-restore" not in p.parts
            and p.name != "idiograph-agent-changes.jsonl"}


def whole(at: Path) -> dict:
    """Every file under the project and its bytes, hidden ones and the lock files among them: what a dry run must
    leave as it found it."""
    return {p.relative_to(at).as_posix(): p.read_bytes() for p in sorted(at.rglob("*")) if p.is_file()}


def unlocked(at: Path) -> None:
    """The lock files setting up the copy made taken away, so the copy stands as a project before any write."""
    for lock in at.rglob(".idiograph.lock"):
        lock.unlink()


def test_gets_first(scratch: Path):
    print("\n395. gets show, fresh and apply on a project with no GETs or LGETs file make it as the screen's first act "
          "does, and a reworded quote keeps Trajectories' tick (getsfirst, 16 November)")
    import cli
    import gets as gets_mod
    import idiograph_routes
    import make_demo
    import server as server_mod

    base = scratch / "a395"
    shutil.rmtree(base, ignore_errors=True)
    base.mkdir(parents=True)
    cfg_file = scratch / "a395-config.json"
    cfg_file.write_text(json.dumps({"projects": [], "interviewer": "Adam", "corpus": "", "gravity_reference": "",
                                    "corpus_exclude": []}), encoding="utf-8")
    kept = (server_mod.CONFIG_PATH, server_mod.ROOT_OVERRIDE, server_mod.STATE_PATH, server_mod.STATE_MEMORY)

    def copy_of(demo: str, name: str) -> Path:
        at = base / name
        shutil.copytree(support.source(demo), at, ignore=as_cloned)
        make_demo.fill(at / "pristine", at)
        # the GETs and LGETs files the fill brings taken away again: a project before its first act on them
        (at / gets_mod.FILE).unlink(missing_ok=True)
        (at / gets_mod.LGETS_FILE).unlink(missing_ok=True)
        # agents allowed, as Project settings' tick does, with the copy the one project for the call
        server_mod.ROOT_OVERRIDE = str(at)
        try:
            idiograph_routes.api_project({"root": str(at), "agents": True})
        finally:
            server_mod.ROOT_OVERRIDE = None
        return at

    def run(root: Path, *args) -> tuple[int, str, str]:
        return cli.run(["--root", str(root), "--config", str(cfg_file), *args])

    def answer(root: Path, *args) -> tuple[int, dict]:
        code, out, err = run(root, *args, "--json")
        return code, (support.plain(json.loads(out)) if out.strip() else {"error": err})

    def spec(name: str, value) -> str:
        path = base / f"{name}.json"
        path.write_text(json.dumps(value), encoding="utf-8")
        return str(path)

    def call(route: str, body: dict) -> dict:
        with idiograph_routes.route_scope(route, body):
            return server_mod.ROUTES[route](body)

    def copies(path: Path) -> dict:
        data = json.loads(path.read_text(encoding="utf-8"))
        return {c: rec.get("hash") for c, rec in (data.get("cases") or {}).items()}

    try:
        server_mod.CONFIG_PATH, server_mod.ROOT_OVERRIDE = cfg_file, None
        server_mod.STATE_PATH, server_mod.STATE_MEMORY = scratch / "a395-state.json", {"recent": []}

        # ── A. the one-timepoint demo with no GETs file
        ipa = copy_of("demo", "ipa")
        gfile = ipa / gets_mod.FILE
        check("395: the scratch copy of the demo has its participants and no GETs file",
              not gfile.exists() and len([x for x in ipa.glob("*/*.xlsx") if x.parent.name != "pristine"]) == 3, sorted(tree(ipa))[:12])
        unlocked(ipa)
        bare = whole(ipa)
        was = tree(ipa)
        code, shown = answer(ipa, "gets", "show")
        check("395: gets show answers the board the screen opens on, every card in the pile, version none, nothing written",
              code == 0 and shown.get("saved") is False and shown.get("version") == "none" and not shown.get("themes")
              and len(shown.get("unplaced") or []) > 10 and tree(ipa) == was, shown)
        code, dry = answer(ipa, "gets", "fresh", "--name", "By the walks", "--dry-run")
        check("395: gets fresh's dry run says the file would be made and writes nothing",
              code == 0 and dry.get("dry_run") is True and dry.get("made_file") == gets_mod.FILE
              and gets_mod.FILE in dry.get("said", "") and tree(ipa) == was, dry)
        # a dry run leaves the folder byte for byte as it was, no lock file made, the project's or a participant's
        ops = {"request": "Group the two timetables", "version": shown.get("version"), "operations": [
            {"op": "make", "ref": "t", "title": "Days given their shape by the dog", "inside": None,
             "members": ["Mabel/g1", "Rowan/g1"]}]}
        dries = [answer(ipa, "gets", "apply", "b1", "--ops", spec("ipa-ops", ops), "--dry-run")[0],
                 answer(ipa, "gets", "complete", "--dry-run")[0],
                 answer(ipa, "board", "fresh", "Rowan", "--name", "Trial", "--dry-run")[0]]
        after = whole(ipa)
        # apply and board fresh run their dry runs through (board fresh under a participant's lock), complete refuses
        # under the project's lock, so each kind of lock is met with no file there (getsfix)
        check("395: the dry runs of gets show, fresh, apply, complete and board fresh leave the folder byte for byte as "
              "it was, no lock file made at the root or in a participant's Working",
              dries[0] == 0 and dries[1] != 0 and dries[2] == 0
              and after == bare and not list(ipa.rglob(".idiograph.lock")),
              (dries, sorted(set(after) ^ set(bare)), [k for k in bare if after.get(k) != bare[k]]))
        code, made = answer(ipa, "gets", "fresh", "--name", "By the walks", "--note", "A board by the walks",
                            "--tool", "Claude Code")
        held = json.loads(gfile.read_text(encoding="utf-8")) if gfile.exists() else {}
        check("395: gets fresh makes the GETs file with the one board it names, every card in the pile, on the canvas, "
              "no Board 1 beside it, every participant's copy in",
              code == 0 and made.get("made_file") == gets_mod.FILE and made.get("id") == "b1"
              and [(b["id"], b["name"]) for b in held.get("boards") or []] == [("b1", "By the walks")]
              and not (held.get("boards") or [{}])[0].get("groups")
              and len((held.get("boards") or [{}])[0].get("cards") or {}) == len(shown.get("unplaced") or [])
              and held.get("current") == "b1" and sorted(held.get("cases") or {}) == ["Juno", "Mabel", "Rowan"], made)
        code, changes = answer(ipa, "agents", "changes")
        code_u, text_u, err_u = run(ipa, "agents", "undo-change", "c1")
        check("395: the first file is an agent's change in the record, and its Undo takes the file away again",
              code == 0 and "c1" in json.dumps(changes) and code_u == 0 and not gfile.exists() and tree(ipa) == was,
              (changes, text_u, err_u))

        # the same first act through the screen's save, on another copy, to compare the file each makes
        screen = copy_of("demo", "ipa-screen")
        server_mod.ROOT_OVERRIDE = str(screen)
        try:
            first = call("/api/gets", {"root": str(screen)})
            call("/api/gets-save", {"root": str(screen), "version": first["version"]})
        finally:
            server_mod.ROOT_OVERRIDE = None
        # a change planned on no file, `none` carried back, where a file was made meanwhile: refused, nothing written
        held_screen = tree(screen)
        code, late = answer(screen, "gets", "apply", "b1", "--ops", spec("late-ops", ops), "--tool", "Claude Code")
        code_d, late_dry = answer(screen, "gets", "apply", "b1", "--ops", spec("late-ops", ops), "--dry-run")
        check("395: a gets apply carrying version none is refused, nothing written, when a GETs file is there by then",
              ops["version"] == "none" and code != 0 and code_d != 0 and tree(screen) == held_screen
              and "gets show" in json.dumps(late), (late, late_dry))
        code, dry = answer(ipa, "gets", "apply", "b1", "--ops", spec("ipa-ops", ops), "--dry-run")
        check("395: gets apply's dry run on no GETs file says what it would do and that the file would be made, "
              "writing nothing",
              code == 0 and dry.get("dry_run") is True and dry.get("made_file") == gets_mod.FILE
              and gets_mod.FILE in dry.get("said", "") and tree(ipa) == was, dry)
        code, done = answer(ipa, "gets", "apply", "b1", "--ops", spec("ipa-ops", ops), "--tool", "Claude Code")
        held = json.loads(gfile.read_text(encoding="utf-8")) if gfile.exists() else {}
        board = (held.get("boards") or [{}])[0]
        get = next((g for g in board.get("groups") or [] if g.get("label") == "Days given their shape by the dog"), {})
        check("395: gets apply makes the GETs file with the change on Board 1, the participants' copies the same as the "
              "screen's first save makes",
              code == 0 and done.get("made_file") == gets_mod.FILE and get.get("members") == ["Mabel/g1", "Rowan/g1"]
              and copies(gfile) == copies(screen / gets_mod.FILE), (done, sorted(copies(gfile))))
        code, again = answer(ipa, "gets", "show")
        check("395: once made, gets show reads the file, its version and the GET",
              code == 0 and again.get("saved") is True and again.get("version")
              and [t["label"] for t in again.get("themes") or []] == ["Days given their shape by the dog"], again)

        # ── B. the longitudinal demo with no LGETs file
        lipa = copy_of("demo/lipa", "lipa")
        lfile = lipa / gets_mod.LGETS_FILE
        check("395: the scratch copy of the longitudinal demo has its LPETs and no LGETs file",
              not lfile.exists() and len([x for x in lipa.glob("*/Working/*.lpets.json") if "pristine" not in x.parts]) == 3, sorted(tree(lipa))[:12])
        unlocked(lipa)
        bare = whole(lipa)
        was = tree(lipa)
        code, shown = answer(lipa, "gets", "show")
        cards = [c["key"] for c in shown.get("unplaced") or []]
        check("395: gets show on no LGETs file answers the board with every participant's LPETs in the pile, nothing written",
              code == 0 and shown.get("saved") is False and gets_mod.LGETS_FILE in json.dumps(run(lipa, "gets", "show")[1])
              and {k.split("/")[0] for k in cards} == {"Arlo", "Hollis", "Nell"} and tree(lipa) == was, shown)
        pair = [next(k for k in cards if k.startswith(who + "/")) for who in ("Arlo", "Hollis")]
        lops = {"request": "Two LPETs together", "operations": [
            {"op": "make", "ref": "q", "title": "Quiet found on the plot", "inside": None, "members": pair}]}
        code, dry = answer(lipa, "gets", "apply", "b1", "--ops", spec("lipa-ops", lops), "--dry-run")
        check("395: gets apply's dry run on no LGETs file names idiograph-lgets.json and writes nothing",
              code == 0 and dry.get("made_file") == gets_mod.LGETS_FILE and whole(lipa) == bare, dry)
        code, done = answer(lipa, "gets", "apply", "b1", "--ops", spec("lipa-ops", lops), "--tool", "Claude Code")
        held = json.loads(lfile.read_text(encoding="utf-8")) if lfile.exists() else {}
        groups = [g for b in held.get("boards") or [] for g in b.get("groups") or []]
        check("395: gets apply makes the LGETs file with the change, every participant's copy in, and no GETs file",
              code == 0 and done.get("made_file") == gets_mod.LGETS_FILE
              and [g.get("members") for g in groups] == [pair]
              and len(held.get("cases") or {}) == 3 and not (lipa / gets_mod.FILE).exists(), done)
        code_u, text_u, err_u = run(lipa, "agents", "undo-run", "r1")
        check("395: the run's Undo takes the LGETs file away again", code_u == 0 and not lfile.exists(), (text_u, err_u))
        code, fresh = answer(lipa, "gets", "fresh", "--name", "Second look", "--note", "Another board", "--tool", "Claude Code")
        held = json.loads(lfile.read_text(encoding="utf-8")) if lfile.exists() else {}
        check("395: gets fresh on no LGETs file makes it with the one board it names",
              code == 0 and fresh.get("made_file") == gets_mod.LGETS_FILE
              and [b["name"] for b in held.get("boards") or []] == ["Second look"], fresh)

        # ── C. a reworded quote keeps Trajectories' tick (quotefollow): already so, checked here
        traj = copy_of("demo/lipa", "lipa-quote")

        def cells() -> dict:
            got = answer(traj, "trajectories", "show")[1]
            return {(p["case"], r["id"], tp): c for p in got.get("participants") or [] for r in p["rows"]
                    for tp, c in r["cells"].items()}

        before = cells()
        ticked = [(k, c) for k, c in before.items() if c["chosen"] and (c["quote"] or {}).get("key")]
        worded = []
        for (case, _lpet, _tp), c in ticked:
            key = c["quote"]["key"]
            sheet, row, place = key.split(":")
            if (case, key) in worded or len(worded) == 3:
                continue
            turn = answer(traj, "turn", "show", case, sheet, row)[1]["turns"][0]
            pairs = [{"statement": p["statement"], "quote": p.get("quote") or ""} for p in turn["pairs"]]
            words = pairs[int(place)]["quote"].split()
            if len(words) < 6:
                continue
            # the quote shortened, its last three words gone, every other quote of the passage sent back as it was
            short = " ".join(words[:-3]).rstrip(",.;:")
            pairs[int(place)]["quote"] = short + ("\"" if short.startswith("\"") else "")
            code, out, err = run(traj, "turn", "write", case, sheet, row, "--from", spec(f"turn-{len(worded)}", {"pairs": pairs}),
                                 "--note", "A shorter quote", "--tool", "Claude Code")
            if code == 0:
                worded.append((case, key))
        after = cells()
        moved = [k for k, c in before.items() if (k[0], (c["quote"] or {}).get("key")) in worded]
        kept_tick = [k for k in moved if after[k]["chosen"] and after[k]["quote"]["key"] == before[k]["quote"]["key"]
                     and after[k]["quote"]["text"] != before[k]["quote"]["text"]]
        bold_ok = all(all(0 <= a < b <= len(after[k]["quote"]["text"]) for a, b in after[k]["bold"]) for k in moved)
        check("395: a quote reworded with turn write keeps every Trajectories cell he ticked on it, its key and its tick, "
              "with the new words, and his bold on them",
              len(worded) == 3 and len(moved) >= 3 and kept_tick == moved and bold_ok,
              [(k, before[k]["chosen"], after[k]["chosen"]) for k in moved])
        check("395: and no other cell's tick on Trajectories changed",
              all(after[k]["chosen"] == c["chosen"] and (after[k]["quote"] or {}).get("key") == (c["quote"] or {}).get("key")
                  for k, c in before.items()),
              [k for k, c in before.items() if after[k]["chosen"] != c["chosen"]])
    finally:
        server_mod.CONFIG_PATH, server_mod.ROOT_OVERRIDE, server_mod.STATE_PATH, server_mod.STATE_MEMORY = kept
