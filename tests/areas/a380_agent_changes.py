"""Area 380: the record of agents' changes and their runs' restore points (noholds, 13 November 2026, Adam: the holds
were "approvals theatre", so agents act at once, with "a safety net if they don't ... review afterwards", and by
dialog the actions undo cannot reach are the app's alone, and a restore point for each agent run).

What is checked, on an invented project about keeping bees in a city, Ada, Bryn and Cass. An agent's write kept once
in the project's change record with its run, op, target and a line of what changed, and never a participant's words.
A dry run and a read recording nothing. Two writes of one tool within 30 minutes one run, another tool's its own,
`--run` its own, and a write after 30 minutes a new run. A run undone putting every file it changed back byte for
byte as it was before its first write and taking a board it made away, its undo a run of its own that undoes it in
its turn, and a second undo refused. The undo refused whole, nothing written, naming the file when a later change
would be lost, and when the run renamed a participant's folder. A restore point copying only what changed since the
last. The ops only the app does refused with nothing written and logged as app_only, their dry runs answering. An
MCP connection one run and a second its own. And the actions that waited before approvals were removed dropped as
the project opens, their count noted once in the agent log. One change undone alone (agentreview2, 13 November):
each change keeping its files before and after it,  putting them back byte for byte, the
change before it kept, a second undo refused, a change whose file he changed since refused whole with nothing
written, and MCP's agent_undo_change doing the same. A run's undo reaching Source (undosource, 17 November 2026), on
a scratch copy of the demo made a project of its own: an agent's Add transcripts of a new participant undone leaves
the project byte for byte as before, no Source file and no folder left, and the undo undone brings the participant
back whole; a further interview undone leaves the participant's other Source files untouched; a recording replaced
comes back from the participant's _Archive; and no restore point keeps a copy of a recording."""
from __future__ import annotations

import hashlib
import json
import os
import shutil
import tempfile
import zlib
from datetime import datetime, timedelta
from pathlib import Path

from .support import check
from . import support

ASKED = "Tidy the labels before my supervision."


def digest(root: Path) -> dict:
    """Every workbook and JSON file of the project by its contents, the record and the store set aside."""
    out = {}
    for p in sorted(Path(root).rglob("*")):
        rel = p.relative_to(root).as_posix()
        if p.is_file() and not rel.startswith(".idiograph-restore") and p.suffix in (".xlsx", ".json") \
                and "_Archive" not in rel and p.name != "idiograph-history.json":
            out[rel] = hashlib.sha256(p.read_bytes()).hexdigest()
    return out


def tree(root: Path) -> dict:
    """Every file and folder of the project, each file by its contents, Source's among them: the record of agents'
    changes and its store, lock files, archive copies and the project's History set aside."""
    import agent_changes
    out = {}
    for p in sorted(Path(root).rglob("*")):
        rel = p.relative_to(root).as_posix()
        if (rel == agent_changes.FILE or rel.startswith(agent_changes.STORE) or p.name.endswith(".lock")
                or "_Archive" in rel.split("/") or p.name in agent_changes.NEVER):
            continue
        out[rel] = "folder" if p.is_dir() else hashlib.sha256(p.read_bytes()).hexdigest()
    return out


def source_undo(scratch: Path):
    """An agent's Add transcripts of a new participant, then its run undone, on a scratch copy of the demo made a
    project of its own: the project byte for byte as before, no Source file and no folder left, the undo undone
    bringing the participant back whole. A further interview added to that participant and undone leaves their other
    Source files as they were. A recording a run replaced is put back from the participant's _Archive, and no
    restore point keeps a copy of a recording (undosource, 17 November 2026)."""
    import agent_changes
    import cli
    import server as server_mod

    base = scratch / "agent-changes-380-source"
    shutil.rmtree(base, ignore_errors=True)
    root = base / "Dogs"
    root.mkdir(parents=True)
    demo = support.source("demo")
    held = json.loads((demo / server_mod.PROJECT_FILE).read_text(encoding="utf-8"))
    held["agents"] = {"allowed": True, "at": "2026-11-17T09:00:00+00:00"}
    (root / server_mod.PROJECT_FILE).write_text(json.dumps(held), encoding="utf-8")
    for who in ("Juno", "Mabel", "Rowan"):
        (root / who / "Working").mkdir(parents=True)
        shutil.copy2(demo / "pristine" / f"{who} - EN & ES.xlsx", root / who / f"{who} - EN & ES.xlsx")
        for one in sorted((demo / "pristine" / "Working").glob(f"{who} - EN & ES.*")):
            shutil.copy2(one, root / who / "Working" / one.name)
    shutil.copy2(demo / "pristine" / "idiograph-gets.json", root / "idiograph-gets.json")
    config_file = base / "config.json"
    config_file.write_text(json.dumps({"projects": [{"root": str(root)}], "interviewer": "Sam", "corpus": "",
                                       "gravity_reference": "", "corpus_exclude": []}), encoding="utf-8")
    given = base / "given"
    given.mkdir()
    for name, said in (("Initial", "Mud, mostly, and a shed with no roof."),
                       ("Follow-up", "The shed has a roof now, and a chair in it.")):
        (given / f"{name}.vtt").write_text(
            "WEBVTT\n\n00:00:01.000 --> 00:00:04.000\n<v Sam>What did the plot look like?</v>\n\n"
            f"00:00:05.000 --> 00:00:09.000\n<v Wren>{said}</v>\n", encoding="utf-8")
    # two recordings, invented bytes, only ever copied
    (given / "first.m4a").write_bytes(b"\x00\x00\x00\x18ftypM4A " + os.urandom(4000))
    (given / "second.m4a").write_bytes(b"\x00\x00\x00\x18ftypM4A " + os.urandom(5000))
    roles = {"Sam": "interviewer", "Wren": "participant"}
    first = base / "first.json"
    first.write_text(json.dumps([{"file": str(given / "Initial.vtt"), "pseudonym": "Wren", "interview": "Initial",
                                  "speakers": roles, "audio": str(given / "first.m4a")}]), encoding="utf-8")
    again = base / "again.json"
    again.write_text(json.dumps([{"file": str(given / "Follow-up.vtt"), "pseudonym": "Wren", "interview": "Follow-up",
                                  "speakers": roles}]), encoding="utf-8")

    def run(*args):
        words = ["--config", str(config_file), "--root", str(root), "--json", *args, "--tool", "Claude Code"]
        code, out, err = cli.run(words)
        return code, (support.plain(json.loads(out)) if out.strip() else {}), err + (out if code else "")

    def stored() -> set:
        return {agent_changes.read_object(f) for f in (root / agent_changes.STORE / "objects").iterdir() if f.is_file()}

    start = tree(root)
    code, _x, err = run("project", "add-transcripts", "--from", str(first), "--run", "add-wren", "--note", "Add Wren")
    wren = next((p for p in root.iterdir() if p.is_dir() and p.name.endswith("Wren")), None)
    added = tree(root)
    made_source = sorted(k for k in set(added) - set(start) if "/Source/" in k and added[k] != "folder")
    check("380: an agent's Add transcripts of a new participant makes their folder, Source's transcript as given and "
          "its recording among its files", code == 0 and wren is not None
          and any(k.endswith("Initial.vtt") for k in made_source) and any(k.endswith(".m4a") for k in made_source),
          err + json.dumps(made_source))
    recording = (given / "first.m4a").read_bytes()
    check("380: no restore point keeps a copy of a recording, watched by its time and size alone",
          recording not in stored())
    rid = agent_changes.read(root)[-1]["run"]
    code, dry, err = run("agents", "undo-run", rid, "--dry-run", "--note", "Undo Wren")
    check("380: undo-run's dry run counts every file the run made, Source's among them, and writes nothing",
          code == 0 and dry.get("taken_away") == len([k for k in set(added) - set(start) if added[k] != "folder"])
          and tree(root) == added, err + json.dumps(dry))
    code, undone, err = run("agents", "undo-run", rid, "--note", "Undo Wren")
    after = tree(root)
    check("380: the add undone leaves the project byte for byte as before, no Source file and no empty folder, the "
          "participant's own folder gone", code == 0 and after == start and wren is not None and not wren.exists(),
          err + json.dumps(sorted(set(after) ^ set(start))))
    code, _x, err = run("agents", "undo-run", undone.get("undo_run", ""), "--note", "Put Wren back")
    check("380: the undo undone brings the participant back whole, Source and the recording byte for byte",
          code == 0 and tree(root) == added, err + json.dumps(sorted(set(tree(root)) ^ set(added))))

    # a further interview for the participant, undone: their other Source files untouched
    kept_files = {k: (root / k).stat().st_mtime_ns for k in added if "/Source/" in k and added[k] != "folder"
                  and not k.endswith(".xlsx")}
    code, _x, err = run("project", "add-transcripts", "--from", str(again), "--run", "join-wren", "--note",
                        "Add Wren's follow-up")
    joined = tree(root)
    check("380: a further interview added to the participant writes its own Source folder",
          code == 0 and any(k.endswith("Follow-up.vtt") for k in set(joined) - set(added)), err)
    rid = agent_changes.read(root)[-1]["run"]
    code, _x, err = run("agents", "undo-run", rid, "--note", "Undo the follow-up")
    check("380: the further interview undone puts the participant back as they were, their other Source files "
          "untouched and the new interview's folder gone", code == 0 and tree(root) == added
          and all((root / k).stat().st_mtime_ns == t for k, t in kept_files.items()),
          err + json.dumps(sorted(set(tree(root)) ^ set(added))))

    # a recording replaced, kept in the participant's _Archive by audio attach, put back from there by the undo
    code, _x, err = run("audio", "attach", "Wren", "--file", str(given / "second.m4a"), "--replace",
                        "--run", "swap", "--note", "Swap the recording")
    swapped = tree(root)
    check("380: a recording replaced by an agent keeps the one there in _Archive", code == 0 and swapped != added
          and any(p.suffix == ".m4a" for p in (wren / "_Archive").rglob("*")), err)
    rid = agent_changes.read(root)[-1]["run"]
    code, put, err = run("agents", "undo-run", rid, "--note", "Put the first recording back")
    check("380: the replace undone puts the first recording back from _Archive byte for byte over the second",
          code == 0 and tree(root) == added, err + json.dumps(sorted(k for k in set(tree(root)) | set(added)
                                                                     if tree(root).get(k) != added.get(k))))
    code, _x, err = run("agents", "undo-run", put.get("undo_run", ""), "--note", "The second recording again")
    check("380: the undo kept the second recording before writing the first over it, so its undo brings the second "
          "back byte for byte (undosource2)", code == 0 and tree(root) == swapped, err)

    # a participant added and given a further interview in one run, undone: the participant goes whole, the
    # workbook's archive copy the further interview made in their folder with it (undosource2)
    before_ivo = tree(root)
    for name, spec in (("Initial", "ivo-1.json"), ("Follow-up", "ivo-2.json")):
        (base / spec).write_text(json.dumps([{"file": str(given / f"{name}.vtt"), "pseudonym": "Ivo",
                                              "interview": name, "speakers": {"Sam": "interviewer", "Ivo": "participant"}}]),
                                 encoding="utf-8")
    (given / "Initial.vtt").write_text((given / "Initial.vtt").read_text(encoding="utf-8").replace("Wren", "Ivo"),
                                       encoding="utf-8")
    (given / "Follow-up.vtt").write_text((given / "Follow-up.vtt").read_text(encoding="utf-8").replace("Wren", "Ivo"),
                                         encoding="utf-8")
    c1, _x, e1 = run("project", "add-transcripts", "--from", str(base / "ivo-1.json"), "--run", "ivo", "--note", "Add Ivo")
    c2, _x, e2 = run("project", "add-transcripts", "--from", str(base / "ivo-2.json"), "--run", "ivo", "--note", "More")
    ivo = next((p for p in root.iterdir() if p.is_dir() and p.name.endswith("Ivo")), None)
    code, _x, err = run("agents", "undo-run", agent_changes.read(root)[-1]["run"], "--note", "Undo Ivo")
    check("380: a participant added and given a further interview in one run, undone, goes whole, the archive copy "
          "in their folder too", c1 == c2 == code == 0 and ivo is not None and not ivo.exists()
          and tree(root) == before_ivo, e1 + e2 + err)

    # a file the researcher drops in the participant's _Archive between two writes of the run is not the run's: its
    # undo leaves it, takes the archive copy the run made, and the undo undone puts that copy back (lowsfix)
    for name, spec in (("Initial", "zed-1"), ("Follow-up", "zed-2")):
        words = given / f"{name}.vtt"
        (given / f"{spec}.vtt").write_text(words.read_text(encoding="utf-8").replace("Ivo", "Zed"), encoding="utf-8")
        (base / f"{spec}.json").write_text(json.dumps([{"file": str(given / f"{spec}.vtt"), "pseudonym": "Zed",
                                                        "interview": name, "speakers": {"Sam": "interviewer", "Zed": "participant"}}]),
                                           encoding="utf-8")
    before_zed = tree(root)
    c1, _x, e1 = run("project", "add-transcripts", "--from", str(base / "zed-1.json"), "--run", "zed", "--note", "Add Zed")
    zed = next((p for p in root.iterdir() if p.is_dir() and p.name.endswith("Zed")), None)
    dropped = zed / "_Archive" / "by-hand.txt" if zed is not None else None
    if dropped is not None:
        dropped.parent.mkdir(exist_ok=True)
        dropped.write_bytes(b"the researcher's own file")
        # and a folder of his own with an _Archive of its own, made between the writes
        (zed / "Notes" / "_Archive").mkdir(parents=True)
        (zed / "Notes" / "_Archive" / "also.txt").write_bytes(b"his too")
    c2, _x, e2 = run("project", "add-transcripts", "--from", str(base / "zed-2.json"), "--run", "zed", "--note", "More")
    zed_run = agent_changes.read(root)[-1]["run"]
    made_copies = sorted(p.name for p in (zed / "_Archive").iterdir()) if zed is not None else []
    with_zed = tree(root)
    c3, undone_zed, e3 = run("agents", "undo-run", zed_run, "--note", "Undo Zed")
    left = sorted(p.name for p in (zed / "_Archive").iterdir()) if zed is not None and (zed / "_Archive").exists() else []
    check("380: an undo of a participant a run added leaves a file the researcher dropped in their _Archive between "
          "its writes and takes the archive copies the run made", c1 == c2 == c3 == 0 and zed is not None
          and "by-hand.txt" in made_copies and len(made_copies) > 1 and left == ["by-hand.txt"]
          and (zed / "Notes" / "_Archive" / "also.txt").read_bytes() == b"his too"
          and {k: v for k, v in tree(root).items() if not k.startswith(zed.name)} == before_zed,
          e1 + e2 + e3 + json.dumps([made_copies, left]))
    kept_copies = {p.name: p.read_bytes() for p in (zed / "_Archive").iterdir() if p.name != "by-hand.txt"} if zed else {}
    c4, redone, e4 = run("agents", "undo-run", undone_zed.get("undo_run", ""), "--note", "Put Zed back")
    back = {p.name: p.read_bytes() for p in (zed / "_Archive").iterdir()} if zed is not None and (zed / "_Archive").exists() else {}
    check("380: that undo undone puts the archive copies it took away back, byte for byte, and tree is as before it",
          c4 == 0 and not kept_copies and sorted(back) == made_copies and back["by-hand.txt"] == b"the researcher's own file"
          and tree(root) == with_zed, e4 + json.dumps(sorted(back)))
    # the redo is a run of its own that knows the copies it put back: undone, it takes them away again (lowsfix)
    c5, again, e5 = run("agents", "undo-run", redone.get("undo_run", ""), "--note", "Take them away again")
    left = sorted(p.name for p in (zed / "_Archive").iterdir())
    check("380: the undo of that redo takes the archive copies it put back away again and leaves the researcher's file",
          c5 == 0 and left == ["by-hand.txt"], e5 + json.dumps(left))
    # a file of the researcher's at a copy's own path is kept before the redo writes over it, and comes back
    copy_name = next(n for n in made_copies if n != "by-hand.txt")
    (zed / "_Archive" / copy_name).write_bytes(b"mine, at the copy's name")
    c6, redo2, e6 = run("agents", "undo-run", again.get("undo_run", ""), "--note", "Put the copies back again")
    wrote = (zed / "_Archive" / copy_name).read_bytes() != b"mine, at the copy's name"
    c7, _x, e7 = run("agents", "undo-run", redo2.get("undo_run", ""), "--note", "And his file again")
    check("380: a file of his at a copy's path is kept before an undo writes the copy over it, and that undo undone "
          "brings his file back", c6 == c7 == 0 and wrote
          and (zed / "_Archive" / copy_name).read_bytes() == b"mine, at the copy's name", e6 + e7)

    # a copy that cannot be kept refuses the undo whole, nothing taken away (undosource2)
    (given / "Initial.vtt").write_text((given / "Initial.vtt").read_text(encoding="utf-8").replace("Ivo", "Pip"),
                                       encoding="utf-8")
    (base / "pip.json").write_text(json.dumps([{"file": str(given / "Initial.vtt"), "pseudonym": "Pip",
                                                "interview": "Initial", "speakers": {"Sam": "interviewer", "Pip": "participant"},
                                                "audio": str(given / "first.m4a")}]), encoding="utf-8")
    code, _x, err = run("project", "add-transcripts", "--from", str(base / "pip.json"), "--run", "pip", "--note", "Add Pip")
    pip = next((p for p in root.iterdir() if p.is_dir() and p.name.endswith("Pip")), None)
    pip_run = agent_changes.read(root)[-1]["run"]
    with_pip = tree(root)
    n_runs = len(agent_changes.all_runs(root))
    real_keep = agent_changes.keep_file
    agent_changes.keep_file = lambda r, rel: None if rel.endswith(".m4a") else real_keep(r, rel)
    try:
        code, _x, err = run("agents", "undo-run", pip_run, "--note", "Undo Pip")
    finally:
        agent_changes.keep_file = real_keep
    check("380: a file the undo cannot keep first refuses it in one line, nothing taken away, no run of its own",
          code != 0 and "could not keep a copy of" in err and tree(root) == with_pip
          and len(agent_changes.all_runs(root)) == n_runs
          and not agent_changes.load_run(root, pip_run).get("undone"), err)

    # an undo that fails part way keeps its own run, which puts back what it took (undosource2)
    real_clear = agent_changes.clear_folders

    def failing(*_a, **_k):
        raise OSError("the disk went away")
    agent_changes.clear_folders = failing
    try:
        try:
            code, _x, err = run("agents", "undo-run", pip_run, "--note", "Undo Pip")
        except OSError as exc:
            code, err = 1, str(exc)
    finally:
        agent_changes.clear_folders = real_clear
    half = agent_changes.all_runs(root)[-1]
    check("380: an undo failing part way keeps its run, naming what it changed, and is not marked done",
          code != 0 and half.get("undoes") == pip_run and half.get("changed")
          and not agent_changes.load_run(root, pip_run).get("undone"), err + json.dumps(half.get("changed")))
    code, _x, err = run("agents", "undo-run", half["id"], "--note", "Put Pip back")
    check("380: that half undo undone puts the participant back byte for byte", code == 0 and tree(root) == with_pip, err)

    # a folder he made after the run, inside the participant's, stays with what holds it (undosource2)
    (pip / "Photos").mkdir()
    (pip / "Photos" / ".DS_Store").write_bytes(b"\x00Bud1")
    code, _x, err = run("agents", "undo-run", pip_run, "--note", "Undo Pip")
    left = sorted(p.relative_to(pip).as_posix() for p in pip.rglob("*")) if pip.exists() else []
    check("380: the undo leaves a folder he made after the run, and the participant's folder holding it, and takes "
          "every file the run made", code == 0 and left == ["Photos", "Photos/.DS_Store"], err + json.dumps(left))


def packed_undo(root, ask, run, lines, clock, store):
    """Restore points keep each copy deflated, `<sha>.z`, the sha that of its bytes as they were (restoresize, 21
    November 2026), and a store of before, copies named by their sha alone, still serves a run's undo. A run that
    writes, then has a file of the project taken away inside a later write while a file is made by hand beside, is
    undone byte for byte, the hand-made file left as it stands."""
    import agent_changes
    import idiograph_cli

    objects = store / "objects"
    names = [f.name for f in objects.iterdir() if f.is_file() and not f.name.startswith(".")]
    sound = all(hashlib.sha256(agent_changes.read_object(objects / n)).hexdigest() == n[:-2]
                for n in names if n.endswith(".z"))
    check("380: every copy the restore points keep is deflated and holds, inflated, the bytes its name is the sha of",
          names and all(n.endswith(".z") for n in names) and sound, str(len(names)))
    # the store as it was before restoresize: every copy whole, named by its sha alone
    for n in names:
        (objects / n[:-2]).write_bytes(agent_changes.read_object(objects / n))
        (objects / n).unlink()
    clock["at"] += timedelta(minutes=40)
    start = tree(root)
    ask("length", "31", "--run", "packed")
    after_one = tree(root)
    victim = sorted(f for f in agent_changes.tracked(root) if f.endswith(".json") and "/" in f)[0]
    kept_victim = (root / victim).read_bytes()
    clock["at"] += timedelta(minutes=1)
    (root / "made-by-hand.json").write_text('{"by": "hand"}', encoding="utf-8")
    real_scope = idiograph_cli.run_in_scope

    def taking(command, p, args):
        def op(q, given):
            answer = command(q, given)
            (root / victim).unlink()
            return answer
        return real_scope(op, p, args)

    idiograph_cli.run_in_scope = taking
    try:
        ask("length", "32", "--run", "packed")
    finally:
        idiograph_cli.run_in_scope = real_scope
    gone = not (root / victim).exists()
    packed_run = lines()[-1]["run"]
    made =sorted(f.name for f in objects.iterdir() if f.is_file() and not f.name.startswith("."))
    check("380: copies made after the store of before are deflated beside its whole ones",
          any(n.endswith(".z") for n in made) and any(not n.endswith(".z") for n in made), str(len(made)))
    code, _x, err = run("agents", "undo-run", packed_run, "--note", "Undo the packed run")
    back = tree(root)
    hand = back.pop("made-by-hand.json", None)
    check("380: a run's undo over a store of whole and deflated copies puts every file back byte for byte, one the "
          "run took away among them, a file made by hand beside it left as it stands",
          code == 0 and gone and back == start and (root / victim).read_bytes() == kept_victim
          and hand == hashlib.sha256(b'{"by": "hand"}').hexdigest() and after_one != start, err)
    code, _x, err = run("agents", "undo-run", lines()[-1]["run"], "--note", "Put the packed run back")
    check("380: and that undo undone brings the run's files back as it left them, the taken file gone again",
          code == 0 and not (root / victim).exists(), err)
    (root / "made-by-hand.json").unlink(missing_ok=True)
    # a copy cut short or empty (a power loss before it reached the disk) refuses the undo whole, nothing taken away
    ask("length", "33", "--run", "cut")
    cut_run = lines()[-1]["run"]
    changed = tree(root)
    step = next(iter((agent_changes.load_run(root, cut_run).get("steps") or {}).values()))
    rel, mine = next((r, s) for r, s in step.items() if s.get("before"))
    copy = agent_changes.object_path(root, mine["before"])
    whole = copy.read_bytes()
    if not copy.name.endswith(".z"):
        copy.write_bytes(whole)
    for label, bad in (("cut short", whole[:len(whole) // 2]), ("empty", b"")):
        copy.write_bytes(bad)
        code, _x, err = run("agents", "undo-run", cut_run, "--note", "Undo the cut run")
        check(f"380: an undo whose kept copy is {label} is refused whole in one line with nothing written",
              code != 0 and tree(root) == changed and not agent_changes.load_run(root, cut_run).get("undone"), err)
    copy.write_bytes(whole)
    code, _x, err = run("agents", "undo-run", cut_run, "--note", "Undo the cut run")
    check("380: and the same undo goes through once the copy is whole again", code == 0 and tree(root) != changed, err)


def compacted_store(root, ask, run, lines, runs, clock, store):
    """`restore compact` (compact, 21 November 2026): the whole copies a store holds from before restoresize deflated
    in place, each checked before its whole copy goes, so every undo after it puts back the same bytes."""
    import agent_changes

    objects = store / "objects"

    def listing() -> dict:
        return {f.name: (f.stat().st_size, hashlib.sha256(f.read_bytes()).hexdigest())
                for f in sorted(objects.iterdir()) if f.is_file()}

    # a store of whole copies only, named by their sha, as before restoresize, with a run on top of it
    clock["at"] += timedelta(minutes=40)
    first = tree(root)
    ask("length", "34", "--run", "compact")
    compact_run = lines()[-1]["run"]
    second = tree(root)
    for f in list(objects.iterdir()):
        if f.is_file() and f.name.endswith(".z"):
            (objects / f.name[:-2]).write_bytes(agent_changes.read_object(f))
            f.unlink()
    plain = sorted(f.name for f in objects.iterdir() if f.is_file() and not f.name.startswith("."))
    # one copy named by its sha that does not hold its bytes, and one whole copy with a deflated twin that is cut
    orphan = hashlib.sha256(b"a copy no run names").hexdigest()
    (objects / orphan).write_bytes(b"not the bytes it is named for")
    twin = plain[0]
    (objects / (twin + ".z")).write_bytes(b"cut")
    start_runs, start_lines = sorted(runs()), len(lines())
    before = listing()
    code, dry, err = run("restore", "compact", "--dry-run")
    check("380: restore compact --dry-run counts what it would deflate and what would stay and the sizes, and writes "
          "nothing: no copy, no temporary file, no run and no line of the record",
          code == 0 and dry["dry_run"] and dry["packed"] == len(plain) and dry["left"] == 1
          and 0 < dry["bytes_after"] < dry["bytes_before"] and listing() == before
          and not any(f.name.startswith(".") for f in objects.iterdir())
          and sorted(runs()) == start_runs and len(lines()) == start_lines, err + json.dumps(dry))
    # a copy whose deflated twin does not check out stays whole, its temporary file taken away
    real_check = agent_changes.inflates_to
    agent_changes.inflates_to = lambda path, sha: False
    try:
        code, held_back, err = run("restore", "compact")
    finally:
        agent_changes.inflates_to = real_check
    check("380: a copy whose deflated twin does not inflate to its sha stays whole and is counted, nothing taken away "
          "and no temporary file left", code == 0 and held_back["packed"] == 0 and held_back["left"] == len(plain) + 1
          and listing() == before and not any(f.name.startswith(".") for f in objects.iterdir()), err + json.dumps(held_back))
    # and one whole copy with a sound twin beside it: the whole one goes, the twin stays as it is
    sound_name = plain[1]
    sound_bytes = zlib.compress((objects / sound_name).read_bytes(), 9)
    (objects / (sound_name + ".z")).write_bytes(sound_bytes)
    code, got, err = run("restore", "compact")
    after = listing()
    names = sorted(after)
    inflates = all(hashlib.sha256(agent_changes.read_object(objects / n)).hexdigest() == n[:-2]
                   for n in names if n.endswith(".z"))
    check("380: restore compact deflates every whole copy to its `<sha>.z`, the cut twin written again, the copy that "
          "does not hold its sha left whole and counted, and the store the smaller for it",
          code == 0 and got["packed"] == len(plain) and got["left"] == 1 and not got["dry_run"]
          and names == sorted([orphan] + [n + ".z" for n in plain]) and inflates
          and after[orphan] == before[orphan] and got["bytes_after"] < got["bytes_before"]
          and not any(f.name.startswith(".") for f in objects.iterdir()), err + json.dumps(got))
    check("380: a whole copy with a deflated twin that checks out beside it is taken away and the twin left as it was",
          not (objects / sound_name).exists() and (objects / (sound_name + ".z")).read_bytes() == sound_bytes)
    check("380: restore compact keeps no run and no line of the record", sorted(runs()) == start_runs
          and len(lines()) == start_lines)
    # every undo after it puts back byte for byte, and its undo does too
    code, _x, err = run("agents", "undo-run", compact_run, "--note", "Undo the compact run")
    check("380: a run made before the compact is undone byte for byte from the deflated copies", code == 0
          and tree(root) == first, err)
    code, _x, err = run("agents", "undo-run", lines()[-1]["run"], "--note", "Put the compact run back")
    check("380: and the undo undone brings the run's files back as it left them", code == 0 and tree(root) == second, err)
    again = listing()
    code, got, err = run("restore", "compact")
    check("380: a second restore compact deflates nothing and changes nothing, the copy that does not hold its sha "
          "still whole and counted", code == 0 and got["packed"] == 0 and got["left"] == 1 and listing() == again
          and got["bytes_after"] == got["bytes_before"], err + json.dumps(got))
    (objects / orphan).unlink()
    fresh_store(store.parent.parent / "fresh-compact")


def fresh_store(base):
    """A dry run leaves no lock file, a busy lock part way answers the counts so far and the next run finishes, and
    a temporary file a killed compact left is cleared while other dot-files stay."""
    import agent_changes
    import errors

    shutil.rmtree(base, ignore_errors=True)
    root = base / "Fresh"
    objects = root / agent_changes.STORE / "objects"
    objects.mkdir(parents=True)
    shas = []
    for n in range(3):
        data = (f"copy {n} " * 200).encode()
        sha = hashlib.sha256(data).hexdigest()
        (objects / sha).write_bytes(data)
        shas.append(sha)
    key = hashlib.sha1(str(root.resolve()).encode("utf-8")).hexdigest()[:16]
    lock = Path(tempfile.gettempdir()) / f"idiograph-agents-{key}{agent_changes.LOCK}"
    lock.unlink(missing_ok=True)
    got = agent_changes.compact(root, True)
    check("380: a dry run of restore compact on a fresh project leaves no lock file and no copy changed",
          got["packed"] == 3 and not lock.exists() and sorted(f.name for f in objects.iterdir()) == sorted(shas))
    stray = "." + shas[0] + "." + "ab12cd34"
    other = ["." + shas[0], ".hidden", "." + shas[0] + ".xyz"]
    (objects / stray).write_bytes(b"left by a kill")
    for n in other:
        (objects / n).write_bytes(b"not ours")
    real = agent_changes.held
    calls = {"n": 0}

    def busy_third(r):
        calls["n"] += 1
        if calls["n"] == 3:
            raise errors.WorkbookError("busy", code="busy")
        return real(r)

    agent_changes.held = busy_third
    try:
        part = agent_changes.compact(root, False)
    finally:
        agent_changes.held = real
    check("380: a lock busy part way stops with the counts so far and says so, the copies done kept and the rest whole",
          part["busy"] and part["packed"] == 1 and sum(1 for f in objects.iterdir() if f.name in shas) == 2,
          json.dumps(part))
    check("380: a temporary file a killed compact left is cleared and a dot-file of another shape is left",
          not (objects / stray).exists() and all((objects / n).exists() for n in other))
    done = agent_changes.compact(root, False)
    check("380: the next restore compact finishes what the busy one left",
          not done["busy"] and done["packed"] == 2 and done["failed"] == 0
          and sorted(f.name for f in objects.iterdir() if not f.name.startswith(".")) == sorted(s + ".z" for s in shas))
    shutil.rmtree(base, ignore_errors=True)


def test_agent_changes(scratch: Path):
    print("\n380. The record of agents' changes and each run's restore point: a write kept once with its run, a dry "
          "run and a read none, runs by tool, --run and 30 minutes, a run undone whole and refused over a later "
          "change, the ops only the app does refused, an MCP connection one run, the old holds dropped (13 November)")
    import agent_changes
    import agent_log
    import cli
    import mcp_server
    import server as server_mod
    from .a351_team_board import make_workbook

    base = scratch / "agent-changes-380"
    shutil.rmtree(base, ignore_errors=True)
    root = base / "Bees in the city"
    root.mkdir(parents=True)
    (root / server_mod.PROJECT_FILE).write_text(json.dumps({
        "name": "Bees in the city", "research_question": "How do people keep bees on a city roof?",
        "agents": {"allowed": True, "at": "2026-11-13T09:00:00+00:00"}}), encoding="utf-8")
    for n, who in enumerate(("Ada", "Bryn", "Cass"), 1):
        make_workbook(root, f"P{n} - {who}", who)
    # an action that waited before approvals were removed, and one answered
    (root / "idiograph-holds.json").write_text(json.dumps({"holds": [{"id": "h1", "status": "waiting"},
                                                                     {"id": "h2", "status": "approved"}]}),
                                               encoding="utf-8")
    config_file = base / "config.json"
    config_file.write_text(json.dumps({"projects": [{"root": str(root)}], "interviewer": "Interviewer",
                                       "corpus": "", "gravity_reference": "", "corpus_exclude": []}), encoding="utf-8")
    log = base / "agent-log.json"
    kept = (agent_changes.ALL_OPS, agent_changes.NOW, os.environ.get(agent_log.PLACE), server_mod.CONFIG_PATH)
    agent_changes.ALL_OPS = None
    os.environ[agent_log.PLACE] = str(log)
    record = root / agent_changes.FILE
    store = root / agent_changes.STORE
    clock = {"at": datetime(2026, 11, 13, 10, 0).astimezone()}
    agent_changes.NOW = lambda: clock["at"]

    def run(*args, tool="Claude Code"):
        words = ["--config", str(config_file), "--root", str(root), "--json", *args]
        if tool is not None:
            words += ["--tool", tool]
        code, out, err = cli.run(words)
        return code, (support.plain(json.loads(out)) if out.strip() else {}), err + (out if code else "")

    def ask(*args, tool="Claude Code"):
        return run(*args, "--note", ASKED, tool=tool)

    def lines() -> list:
        return agent_changes.read(root)

    def runs() -> dict:
        return {r["id"]: r for r in agent_changes.all_runs(root)}

    try:
        # ── 1. the holds of before dropped as the project opens, counted once in the agent log
        run("cases", tool=None)
        run("cases", tool=None)
        agent_log.flush()
        notes = [e for e in agent_log.load(log)["entries"] if e.get("code") == "cleared"]
        check("380: the actions that waited are dropped as the project first opens, never applied, and their count "
              "said once in the agent log", not (root / "idiograph-holds.json").exists() and len(notes) == 1
              and notes[0]["line"] == "1 action that waited was cleared when approvals were removed."
              and notes[0]["project"] == "Bees in the city", json.dumps(notes))

        # ── 2. a dry run and a read keep nothing
        before = digest(root)
        run("participant", "set", "Ada", "--label", "First summer", "--note", ASKED, "--dry-run")
        run("agents", "changes", tool=None)
        check("380: a dry run and a read keep no record and no restore point", not record.exists()
              and not (store / "runs").exists() and digest(root) == before)

        # ── 3. writes: kept once each, a run by tool, never a participant's words
        start = digest(root)
        code1, got1, err1 = ask("participant", "set", "Ada", "--label", "First summer")
        clock["at"] += timedelta(minutes=10)
        code2, got2, err2 = ask("turn", "edit", "Ada", "Initial", "3", "--text",
                                "Quiet, a hum you feel through the glove more than you hear it.")
        clock["at"] += timedelta(minutes=10)
        code3, got3, err3 = ask("board", "fresh", "Ada", "--name", "Sketch")
        after_r1 = digest(root)
        got = lines()
        first = runs().get("r1") or {}
        check("380: three writes of one tool within 30 minutes are three lines of one run, r1, each with its op, its "
              "target by name and a line of what changed by the project's files",
              code1 == code2 == code3 == 0 and [e["run"] for e in got] == ["r1"] * 3
              and [e["op"] for e in got] == ["participant set", "turn edit", "board fresh"]
              and got[0]["target"] == {"case": "Ada"} and got[1]["target"].get("sheet") == "Initial"
              and str(got[1]["target"].get("row")) == "3" and "Made Ada's boards" in got[2]["what_changed"]
              and got[1]["what_changed"].startswith("Changed Ada's transcript") and got[0]["agent"] == "Claude Code"
              and got[0]["request"] == ASKED and first.get("changes") == 3, err1 + err2 + err3 + json.dumps(got)[:900])
        check("380: the record never holds a participant's words, the passage's new words nowhere in it",
              "a hum you feel" not in record.read_text(encoding="utf-8"))
        check("380: each line says how to undo it, the run's undo and the op's own where it has one",
              all(e["undo_with"]["command"] == "idiograph agents undo-run r1" for e in got), json.dumps(got)[:600])

        # another tool, --run, and a gap of over 30 minutes each start a run of their own
        clock["at"] += timedelta(minutes=5)
        ask("length", "20", tool="Codex")
        ask("length", "21", "--run", "tidy-session")
        clock["at"] += timedelta(minutes=31)
        ask("length", "22")
        got = lines()
        check("380: another tool's write is a run of its own, a --run its own, and a write over 30 minutes after the "
              "tool's last a new run", [e["run"] for e in got[3:]] == ["r2", "r3", "r4"]
              and runs()["r2"]["agent"] == "Codex", json.dumps([e["run"] for e in got]))

        # ── 4. a restore point copies only what changed since the last
        objects = len(list((store / "objects").iterdir()))
        files = len(agent_changes.tracked(root))
        check("380: the first restore point kept each file once, and the later ones only the files changed since",
              objects < 2 * files and objects >= files, f"{objects} copies for {files} files")

        # ── 5. a run undone: its dry run writes nothing, then every file back and the board it made taken away
        now_files = digest(root)
        code, dry, err = run("agents", "undo-run", "r4", "--dry-run", "--note", "Undo the last length")
        check("380: undo-run's dry run says what it would put back and writes nothing",
              code == 0 and dry.get("put_back") == 1 and digest(root) == now_files, err + json.dumps(dry))
        # r1's files changed since by r2 to r4? The project file did, so its undo is refused, naming it
        code, _x, err = run("agents", "undo-run", "r1", "--note", "Undo the tidy")
        check("380: a run whose file changed after it is refused whole, naming the file, nothing written",
              code != 0 and "the project's settings, changed after the run's last change" in err
              and digest(root) == now_files, err)
        for rid in ("r4", "r3", "r2"):
            run("agents", "undo-run", rid, "--note", "Undo the lengths")
        code, undone, err = run("agents", "undo-run", "r1", "--note", "Undo the tidy")
        check("380: once the later runs are undone, r1 is undone: every file it changed back byte for byte as it was "
              "before its first write, and the board it made taken away",
              code == 0 and digest(root) == start and undone.get("taken_away") == 2,
              err + json.dumps(undone)[:400] + json.dumps(sorted(k for k in set(start) | set(digest(root))
                                                                 if start.get(k) != digest(root).get(k))))
        again = run("agents", "undo-run", "r1", "--note", "Undo the tidy")
        undo_id = undone.get("undo_run", "")
        check("380: a run undone is marked so, the undo a run of its own and a line of the record, and a second undo "
              "of the run refused", runs()["r1"].get("undone", {}).get("run") == undo_id
              and runs()[undo_id].get("undoes") == "r1" and lines()[-1]["op"] == "agents undo-run"
              and again[0] != 0 and "undone already" in again[2], again[2])
        code, _x, err = run("agents", "undo-run", undo_id, "--note", "Put the tidy back")
        check("380: the undo undone in its turn puts the run's changes back, the board it made among them",
              code == 0 and digest(root) == after_r1, err)

        # ── 6. a later change of his own between the run's writes refuses its undo
        clock["at"] += timedelta(hours=2)
        ask("participant", "set", "Bryn", "--label", "The roof keeper")
        rid = lines()[-1]["run"]
        code, _x, err = cli.run(["--config", str(config_file), "--root", str(root), "participant", "set", "Bryn",
                                 "--label", "Roof keeper", "--note", "his own", "--tool", "Idiograph by hand"])
        clock["at"] += timedelta(minutes=1)
        ask("participant", "set", "Cass", "--label", "New to it")
        code, _x, err = run("agents", "undo-run", rid, "--note", "Undo it")
        check("380: a file changed by someone else between the run's writes refuses the undo, naming it",
              code != 0 and "changed by someone else between the run's changes" in err, err)

        # ── 7. a folder renamed refuses the undo until it is renamed back
        clock["at"] += timedelta(hours=2)
        ask("participant", "rename", "Cass", "Cara", "--folder")
        rid = lines()[-1]["run"]
        code, _x, err = run("agents", "undo-run", rid, "--note", "Undo the rename")
        check("380: a run that renamed a participant's folder is not undone whole, the folder to be renamed back first",
              code != 0 and "renamed a participant's folder" in err, err)

        # ── 8. the ops only the app does: refused, nothing written, logged as app_only, their dry runs answering
        before = digest(root)
        cfg_before = config_file.read_bytes()
        refused = {
            "settings": ask("settings", "--your-name", "A. Keeper"),
            "send": ask("project", "send", "--to", str(base / "out")),
            "invite": ask("team", "invite"),
        }
        dry_send = ask("project", "send", "--to", str(base / "out"), "--dry-run")
        agent_log.flush()
        app_only = [e for e in agent_log.load(log)["entries"] if e.get("code") == "app_only"]
        # a name taken off the list is an agent's since namesset (16 November 2026), area 406
        check("380: Settings, a send and Working together are refused for an agent in a line naming where in the app, "
              "nothing written, each logged as app_only",
              all(c != 0 and "Only the app" in e for c, _g, e in refused.values()) and digest(root) == before
              and config_file.read_bytes() == cfg_before and not (base / "out").exists() and len(app_only) == 3,
              json.dumps({k: v[2][:120] for k, v in refused.items()}))
        check("380: an op only the app does still answers its dry run", dry_send[0] == 0, dry_send[2])

        # ── 9. an MCP connection is one run, a second its own
        clock["at"] += timedelta(hours=2)
        n = len(lines())
        for _ in range(2):
            mcp = mcp_server.Server(root=str(root), config=str(config_file))
            mcp.client = "Claude Desktop"
            for words in (25, 26):
                mcp.call(mcp.by_name["statement_length_set"], {"words": words, "request": ASKED})
        got = lines()[n:]
        listed = mcp.call(mcp.by_name["agent_changes"], {"limit": 2})
        shown = support.plain(listed.get("structuredContent") or {})
        check("380: an MCP connection's writes are one run and a second connection's another, and agent_changes "
              "reads them newest first", len(got) == 4 and got[0]["run"] == got[1]["run"] != got[2]["run"] == got[3]["run"]
              and got[0]["via"] == "mcp" and got[0]["agent"] == "Claude Desktop"
              and [e["id"] for e in shown.get("changes") or []] == [got[3]["id"], got[2]["id"]],
              json.dumps([e["run"] for e in got]) + json.dumps(shown)[:300])

        # ── 10. one change undone alone (agentreview2): its files back as they were just before it, the rest kept
        clock["at"] += timedelta(hours=2)
        ask("participant", "set", "Ada", "--label", "Second summer")
        label_change = lines()[-1]["id"]
        before_board = digest(root)
        ask("board", "fresh", "Bryn", "--name", "Trial")
        board_change = lines()[-1]["id"]
        made_board = digest(root)
        step = (runs()[lines()[-1]["run"]].get("steps") or {}).get(board_change) or {}
        check("380: each change keeps its files as they stood before and after it, by their contents in the store",
              step and all(agent_changes.object_path(root, s["after"]) and (
                  s["before"] is None or agent_changes.object_path(root, s["before"])) for s in step.values()),
              json.dumps(step)[:400])
        code, dry, err = run("agents", "undo-change", board_change, "--dry-run", "--note", "Undo the trial board")
        check("380: undo-change's dry run says what it would put back, nothing written",
              code == 0 and dry.get("changes") == [board_change] and digest(root) == made_board, err + json.dumps(dry))
        code, undone, err = run("agents", "undo-change", board_change, "--note", "Undo the trial board")
        check("380: a change undone alone puts every file it changed back byte for byte as it was just before it, the "
              "change before it in the same run kept", code == 0 and digest(root) == before_board
              and undone.get("undo_run") and lines()[-1]["op"] == "agents undo-change", err + json.dumps(undone)[:300])
        again = run("agents", "undo-change", board_change, "--note", "Undo the trial board")
        check("380: a change undone already is refused, naming the undo's run", again[0] != 0
              and "undone already" in again[2], again[2])
        # a write that changes a file an earlier write of its run made says it changed it, never made it again (lowsE,
        # 21 November 2026)
        clock["at"] += timedelta(minutes=1)
        ask("board", "fresh", "Bryn", "--name", "Trial B")
        made_line = lines()[-1]["what_changed"]
        ask("board", "fresh", "Bryn", "--name", "Trial C")
        changed_line = lines()[-1]["what_changed"]
        check("380: a board file the run made says made on the write that made it and changed on the next that "
              "changed it", made_line.startswith("Made Bryn's boards")
              and changed_line.startswith("Changed Bryn's boards") and "Made" not in changed_line,
              json.dumps([made_line, changed_line]))
        # his own edit of the project file through the app's own call, outside the record, then the label's undo
        cfg_kept = (server_mod.CONFIG_PATH, server_mod.ROOT_OVERRIDE)
        server_mod.CONFIG_PATH, server_mod.ROOT_OVERRIDE = config_file, None
        try:
            import idiograph_routes
            idiograph_routes.api_project({"root": idiograph_routes.project_id(root),
                                          "research_question": "How do people keep bees on a roof in a city?"})
        finally:
            server_mod.CONFIG_PATH, server_mod.ROOT_OVERRIDE = cfg_kept
        his = digest(root)
        code, _x, err = run("agents", "undo-change", label_change, "--note", "Undo the label")
        check("380: a change whose file he changed since is refused whole, naming the file, nothing written",
              code != 0 and "the project's settings, changed since" in err and digest(root) == his, err)
        # through MCP, one change undone in its turn
        mcp = mcp_server.Server(root=str(root), config=str(config_file))
        mcp.client = "Claude Desktop"
        mcp.call(mcp.by_name["board_fresh"], {"case": "Ada", "name": "Draft", "request": ASKED})
        last = lines()[-1]["id"]
        mcp.call(mcp.by_name["agent_undo_change"], {"changes": [last], "request": "Undo the draft board"})
        check("380: MCP's agent_undo_change undoes one change as the command line does",
              digest(root) == his and lines()[-1]["op"] == "agents undo-change"
              and lines()[-1]["target"] == {"changes": [last]}, json.dumps(lines()[-2:])[:500])

        # ── 11. a participant added by an agent undone whole, Source and folders too (undosource)
        source_undo(scratch)

        # ── 12. copies kept deflated (restoresize, 21 November 2026), older whole ones still read
        packed_undo(root, ask, run, lines, clock, store)

        # ── 13. the whole copies a store holds deflated in place (compact, 21 November 2026)
        compacted_store(root, ask, run, lines, runs, clock, store)
    finally:
        agent_changes.ALL_OPS, agent_changes.NOW = kept[0], kept[1]
        if kept[2] is None:
            os.environ.pop(agent_log.PLACE, None)
        else:
            os.environ[agent_log.PLACE] = kept[2]
        server_mod.CONFIG_PATH = kept[3]
