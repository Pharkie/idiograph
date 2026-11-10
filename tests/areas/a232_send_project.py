"""Area 232: a project sent to someone else's Idiograph as one file and opened there as a copy (Adam's
ruling of 20 October 2026, topic 10). Send writes the whole folder as it is and changes nothing in it,
the copy is file for file the same in a folder of its own, a folder already there gives the copy a name
with "copy" after it, a file from a newer Idiograph is refused, and the dry runs write nothing. The
command line's `project send` and `project open-copy`, the MCP server's tools and the page's route all
call the same code. Every fixture is invented, a beekeeping project."""
from __future__ import annotations

import base64
import json
import shutil
import zipfile
from pathlib import Path

import cli
import locks
import mcp_server
import project_pack
import server as server_mod

from .support import check
from . import support
import idiograph_routes


def test_send_project(scratch: Path):
    print("\n232. Send a project, open a sent one as a copy")
    base = scratch / "send-232"
    shutil.rmtree(base, ignore_errors=True)
    root = base / "Keeping bees"
    (root / "P1 - Wren" / "Source" / "Spring").mkdir(parents=True)
    (root / "P1 - Wren" / "Working").mkdir(parents=True)
    (root / "P2 - Hollis" / "_Archive").mkdir(parents=True)
    (root / "idiograph-project.json").write_text(json.dumps({"name": "Keeping bees", "research_question":
                                                           "How do beekeepers live through a cold spring?",
                                                           "agents": {"allowed": True, "at": "2026-10-21T00:00:00+01:00"},
                                                           # its own id, which a send writes when there is none (area 260)
                                                           "uid": "a232beef0000cafe"}),
                                                 encoding="utf-8")
    (root / "P1 - Wren" / "P1 Wren - EN & ES.xlsx").write_bytes(b"PK\x03\x04 a workbook stands in here")
    (root / "P1 - Wren" / "Source" / "Spring" / "spring.txt").write_text("Wren: The hive was quiet.\n", encoding="utf-8")
    (root / "P1 - Wren" / "Source" / "spring.m4a").write_bytes(bytes(range(256)) * 400)
    (root / "P1 - Wren" / "Working" / "P1 Wren - EN & ES - themes.json").write_text('{"boards": []}', encoding="utf-8")
    (root / "P2 - Hollis" / "_Archive" / "old.xlsx").write_bytes(b"an older copy")
    (root / "gets.json").write_text('{"boards": []}', encoding="utf-8")
    (root / ".DS_Store").write_bytes(b"finder")
    # a case's lock, which is never sent, and none at the root, which a send never makes
    (root / "P1 - Wren" / "Working" / locks.NAME).write_text("", encoding="utf-8")
    out_dir, into = base / "out", base / "into"
    out_dir.mkdir()
    into.mkdir()
    config_file = base / "config-232.json"
    config_file.write_text(json.dumps({"projects": [], "interviewer": "Sam", "corpus": "", "gravity_reference": "",
                                       "corpus_exclude": []}), encoding="utf-8")

    def files(at: Path) -> dict:
        return {p.relative_to(at).as_posix(): p.read_bytes() for p in sorted(at.rglob("*")) if p.is_file()}

    def own(at: Path) -> dict:
        return {k: v for k, v in files(at).items() if Path(k).name not in (locks.NAME, ".DS_Store")}

    def opened(at: Path) -> dict:
        # a copy as it was shared, its project file read past the `copy_of` that marks it a copy (area 240)
        held = files(at)
        data = support.plain(json.loads(held.pop(server_mod.PROJECT_FILE)))
        data.pop("copy_of", None)
        # and the id it came with, the project's own, which a copy never takes as its own (area 260)
        data.pop("uid", None)
        return dict(held, **{server_mod.PROJECT_FILE: json.dumps(data, sort_keys=True)})

    def sent_as(at: Path) -> dict:
        held = own(at)
        data = support.plain(json.loads(held[server_mod.PROJECT_FILE]))
        data.pop("uid", None)
        return dict(held, **{server_mod.PROJECT_FILE: json.dumps(data, sort_keys=True)})

    def run(*args):
        return cli.run(["--config", str(config_file), *args])

    kept = (server_mod.CONFIG_PATH, server_mod.ROOT_OVERRIDE, server_mod.STATE_MEMORY)
    live = server_mod.CONFIG_PATH.read_bytes() if server_mod.CONFIG_PATH.exists() else None
    try:
        before = files(root)
        settings = config_file.read_bytes()

        # the dry runs write nothing
        code, said, err = run("--root", str(root), "project", "send", "--to", str(out_dir), "--dry-run")
        check("232: project send --dry-run says what it would write and writes nothing",
              code == 0 and "Dry run" in said and "Keeping bees.idiograph" in said and not list(out_dir.iterdir())
              and files(root) == before, said + err)

        code, said, err = run("--root", str(root), "project", "send", "--to", str(out_dir))
        sent = out_dir / "Keeping bees.idiograph"
        check("232: project send writes <Project name>.idiograph and changes nothing in the project",
              code == 0 and sent.is_file() and files(root) == before, said + err)
        with zipfile.ZipFile(sent) as zf:
            names = set(zf.namelist())
        check("232: the file holds every file of the folder, and not the lock or the Mac's folder settings",
              names == {project_pack.MANIFEST} | {project_pack.TOP + k for k in own(root)}, str(sorted(names)))
        code, said, err = run("--root", str(root), "project", "send", "--to", str(out_dir))
        check("232: a sent file there already is never written over", code == 1 and "already" in err, said + err)

        code, said, err = run("project", "open-copy", str(sent), "--into", str(into), "--dry-run")
        check("232: project open-copy --dry-run names the folder it would make and writes nothing",
              code == 0 and "Dry run" in said and "Keeping bees" in said and not list(into.iterdir())
              and config_file.read_bytes() == settings, said + err)

        # opened as a copy, file for file the same, and one of the projects
        code, said, err = run("project", "open-copy", str(sent), "--into", str(into), "--json")
        copy = into / "Keeping bees"
        answer = support.plain(json.loads(said)) if code == 0 else {}
        roots = [e["root"] for e in json.loads(config_file.read_text(encoding="utf-8"))["projects"]]
        check("232: the copy opens in a new folder of its own name, file for file the same as the project sent",
              code == 0 and copy.is_dir() and opened(copy) == sent_as(root), said + err)
        check("232: the copy is added to the projects, its name the project's",
              len(roots) == 1 and server_mod.same_folder(server_mod.configured(roots[0]), copy)
              and answer.get("project", {}).get("name") == "Keeping bees", str(roots))

        # a name taken gets a copy name, never a folder written over
        before_copy = files(copy)
        code, said, err = run("project", "open-copy", str(sent), "--into", str(into))
        second = into / "Keeping bees copy"
        check("232: a folder there already gives the copy its name with copy after it, the first copy untouched",
              code == 0 and second.is_dir() and opened(second) == sent_as(root) and files(copy) == before_copy, said + err)
        check("232: the free name after copy is copy 2",
              project_pack.copy_folder(into, "Keeping bees").name == "Keeping bees copy 2")

        # a file from a newer Idiograph is refused, with nothing written
        newer = out_dir / "Newer.idiograph"
        with zipfile.ZipFile(sent) as src, zipfile.ZipFile(newer, "w") as dst:
            head = json.loads(src.read(project_pack.MANIFEST))
            head["format"] = project_pack.FORMAT + 1
            dst.writestr(project_pack.MANIFEST, json.dumps(head))
            for name in src.namelist():
                if name != project_pack.MANIFEST:
                    dst.writestr(name, src.read(name))
        held = sorted(p.name for p in into.iterdir())
        settings = config_file.read_bytes()
        code, said, err = run("project", "open-copy", str(newer), "--into", str(into))
        check("232: a file from a newer Idiograph is refused in plain words, nothing written",
              code == 1 and project_pack.NEWER in err and sorted(p.name for p in into.iterdir()) == held
              and config_file.read_bytes() == settings, said + err)
        plain = out_dir / "notes.idiograph"
        plain.write_bytes(b"not a zip at all")
        code, said, err = run("project", "open-copy", str(plain), "--into", str(into))
        check("232: a file that is no sent project is refused", code == 1 and project_pack.NOT_SENT in err, err)

        # a file whose list climbs out of its folder is refused
        climbing = out_dir / "Climbing.idiograph"
        with zipfile.ZipFile(climbing, "w") as zf:
            zf.writestr(project_pack.MANIFEST, json.dumps({"kind": project_pack.KIND, "format": 1, "folder": "Up",
                                                          "files": [{"path": "../out.txt", "bytes": 1, "sha256": ""}]}))
            zf.writestr(project_pack.TOP + "../out.txt", "x")
        code, said, err = run("project", "open-copy", str(climbing), "--into", str(into))
        check("232: a file whose list reaches out of the copy's folder is refused, nothing written",
              code == 1 and not (into / "out.txt").exists() and not (into / "Up").exists(), err)

        # the page's way: the file's contents from a browser's chooser, the folder typed
        server_mod.CONFIG_PATH, server_mod.ROOT_OVERRIDE, server_mod.STATE_MEMORY = config_file, None, {"recent": []}
        done = idiograph_routes.api_open_sent({"data": base64.b64encode(sent.read_bytes()).decode("ascii"), "into": str(into)})
        third = into / "Keeping bees copy 2"
        check("232: Open a shared copy on the page opens a browser's file as a copy and lists it with the projects",
              done.get("opened") is True and third.is_dir() and opened(third) == sent_as(root)
              and len(done["projects"]) == 3, str(done.get("folder")))
        checked = idiograph_routes.api_open_sent({"file": str(sent), "check": True})
        check("232: the window's check reads the file alone and writes nothing",
              checked == {"checked": True, "name": "Keeping bees", "folder": "Keeping bees"} and not (into / "Keeping bees copy 3").exists())
        # Send in the window: a project with a large recording written by the server straight to the
        # path its save dialog chose, the page handed a short answer and never the file (21 October)
        big = copy / "P1 - Wren" / "Source" / "long walk.m4a"
        with open(big, "wb") as fh:
            fh.truncate(200 * 1000 * 1000)
        try:
            to = out_dir / "Chosen in the dialog"
            answer = idiograph_routes.api_send_project({"root": str(copy), "to": str(to)})
            landed = out_dir / "Chosen in the dialog.idiograph"
            with zipfile.ZipFile(landed) as zf:
                held = zf.getinfo(project_pack.TOP + "P1 - Wren/Source/long walk.m4a").file_size
            check("232: Send in the window writes a project with a 200 MB recording straight to the chosen path",
                  answer.get("sent") is True and held == 200 * 1000 * 1000 and len(json.dumps(answer)) < 1000
                  and server_mod.same_folder(Path(answer["file"]), landed), json.dumps(answer)[:300])
            check("232: the path chosen is written over through a file beside it, nothing else left there",
                  idiograph_routes.api_send_project({"root": str(copy), "to": str(landed)}).get("sent") is True
                  and sorted(p.name for p in out_dir.iterdir() if p.name.startswith((".", "Chosen")))
                  == ["Chosen in the dialog.idiograph"])
            try:
                idiograph_routes.api_send_project({"root": str(copy), "to": str(base / "nowhere" / "x.idiograph")})
                refused = False
            except server_mod.WorkbookError:
                refused = True
            check("232: a path in a folder that is not there is refused, nothing written",
                  refused and not (base / "nowhere").exists())
        finally:
            big.unlink(missing_ok=True)
            for made in out_dir.glob("Chosen in the dialog*"):
                made.unlink()

        server_mod.ROOT_OVERRIDE = str(root)
        try:
            idiograph_routes.api_open_sent({"file": str(sent), "into": str(into)})
            one_run = False
        except server_mod.WorkbookError:
            one_run = True
        server_mod.ROOT_OVERRIDE = None
        check("232: a run of one project opens no sent project", one_run and not (into / "Keeping bees copy 3").exists())

        # the MCP server's two tools, their dry runs writing nothing
        mcp = mcp_server.Server(root=str(root), config=str(config_file))
        names = {t["name"] for t in mcp.tools}
        res = mcp.call(mcp.by_name["project_send"], {"to": str(base / "mcp.idiograph"), "dry_run": True})
        res2 = mcp.call(mcp.by_name["project_open_copy"], {"file": str(sent), "into": str(into), "dry_run": True})
        check("232: the MCP server lists project_send and project_open_copy, and their dry runs write nothing",
              {"project_send", "project_open_copy"} <= names and not res["isError"] and not res2["isError"]
              and not (base / "mcp.idiograph").exists() and not (into / "Keeping bees copy 3").exists(),
              json.dumps([res["content"], res2["content"]])[:300])
        check("232: sending leaves the project exactly as it was", files(root) == before)
    finally:
        server_mod.CONFIG_PATH, server_mod.ROOT_OVERRIDE, server_mod.STATE_MEMORY = kept
    check("232: the live settings file is exactly as it was",
          (server_mod.CONFIG_PATH.read_bytes() if server_mod.CONFIG_PATH.exists() else None) == live)
