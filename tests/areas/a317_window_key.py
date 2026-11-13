"""Area 317: no local program approves for him (agentlock, 2 November 2026, Adam's ruling by dialog about 19:00:
close it).

`own_origin` passes any program on this machine that names the server's own address, so a shell's curl could
tick a project open to agents or set them up. What governs agents now asks for the window's key, made at each start
and never served by any route to the window's own run. What is checked, on an invented copy of the demo's dog
owners: a plain localhost POST to each guarded route, with no Origin, with the server's own Origin forged and with a
wrong key, refused in one line with nothing written. The page's own call, carrying the key, answered. A settings
save naming Dangerously skip permissions, removed with the holds (noholds, 13 November 2026), keeping nothing and
writing no record. A run in a browser carrying its key in the page and the window's run never. The key read from
standard input and handed on at a restart, never in an argument or the environment. And the agents' command line
and MCP unchanged."""
from __future__ import annotations

import hashlib
import http.client
import io
import json
import os
import shutil
import threading
from http.server import ThreadingHTTPServer
from pathlib import Path

from .support import DEMO_SHIPPED, check
from . import support

ASKED = "Tidy up the boards, keep only the one I am using."
KEY = "k" * 20 + "0123456789abcdef0123456789abcdef"


def sha(path: Path) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest() if Path(path).exists() else ""


def make_project(root: Path) -> None:
    shutil.rmtree(root, ignore_errors=True)
    root.mkdir(parents=True)
    for name in ("Juno", "Rowan"):
        case = root / name
        (case / "Working").mkdir(parents=True)
        shutil.copy2(DEMO_SHIPPED / f"{name} - EN & ES.xlsx", case / f"{name} - EN & ES.xlsx")
        for kind in ("progress", "themes"):
            side = DEMO_SHIPPED / "Working" / f"{name} - EN & ES.{kind}.json"
            if side.exists():
                shutil.copy2(side, case / "Working" / side.name)
    (root / "idiograph-project.json").write_text(json.dumps({
        "name": "Living with a dog, a scratch copy", "agents": {"allowed": True, "at": "2026-11-02T19:00:00+00:00"}}),
        encoding="utf-8")


def test_window_key(scratch: Path):
    print("\n317. No local program approves for him: what governs agents asks for the window's key, a plain localhost "
          "POST refused, the page's own call answered, the switch's record, the browser's run and the key's way "
          "across a restart (2 November)")
    import cli
    import mcp_server
    import server as server_mod
    import themes

    base = scratch / "window-key-317"
    root = base / "Dogs"
    make_project(root)
    config_file = base / "config.json"
    config = {"projects": [{"root": str(root)}], "interviewer": "Adam", "corpus": "", "gravity_reference": "",
              "corpus_exclude": [], "skip_permissions": False}
    config_file.write_text(json.dumps(config), encoding="utf-8")
    record = config_file.with_name("config.skip-permissions.jsonl")
    record.unlink(missing_ok=True)
    kept = (server_mod.CONFIG_PATH, dict(server_mod.WINDOW_KEY), server_mod.READ_KEY, server_mod.POPEN)
    book = root / "Juno" / "Juno - EN & ES.xlsx"

    def run(*args):
        return cli.run(["--config", str(config_file), "--root", str(root), *args])

    def boards() -> list[str]:
        return [b["name"] for b in themes.boards_of(themes.load(book))]

    httpd = None
    try:
        # a second board on Juno, which no plain POST may touch
        made = run("board", "duplicate", "Juno", "Board 1", "--name", "Board 2", "--note", "A second board")
        check("317: the fixture: a second board on Juno", made[0] == 0 and "Board 2" in boards(), made[2])

        server_mod.CONFIG_PATH = config_file
        server_mod.WINDOW_KEY.update(key=KEY, window=True)
        httpd = ThreadingHTTPServer(("127.0.0.1", 0), server_mod.Handler)
        port = httpd.server_address[1]
        threading.Thread(target=httpd.serve_forever, kwargs={"poll_interval": 0.05}, daemon=True).start()
        own = f"http://127.0.0.1:{port}"

        def call(method, path, body=None, key=None, origin=None):
            conn = http.client.HTTPConnection("127.0.0.1", port, timeout=20)
            headers = {"Host": f"127.0.0.1:{port}"}
            if body is not None:
                headers["Content-Type"] = "application/json"
            if key is not None:
                headers[server_mod.KEY_HEADER] = key
            if origin:
                headers["Origin"] = origin
            conn.request(method, path, None if body is None else json.dumps(body), headers)
            res = conn.getresponse()
            raw = res.read()
            conn.close()
            try:
                return res.status, json.loads(raw or b"{}")
            except ValueError:
                return res.status, raw.decode("utf-8", "replace")

        refused = (403, {"error": server_mod.named(server_mod.i18n.t("errors.window_only"))})
        project_file = root / "idiograph-project.json"
        guarded = [
            ("/api/names", {"op": "list", "root": str(root)}),
            ("/api/project", {"root": str(root), "agents": False}),
            ("/api/mcp", {"root": str(root), "op": "add"}),
            ("/api/agents-guide", {"root": str(root)}),
        ]
        before = (sha(config_file), sha(project_file), sha(book), sha(root / "AGENTS.md"))
        answers = {}
        for path, body in guarded:
            answers[path + " " + json.dumps(body)[:30]] = [
                call("POST", path, body),
                call("POST", path, body, origin=own),
                call("POST", path, body, origin=f"http://localhost:{port}"),
                call("POST", path, body, key="not-the-key", origin=own),
            ]
        got_guide = call("GET", f"/api/agents-guide?root={root}")
        after = (sha(config_file), sha(project_file), sha(book), sha(root / "AGENTS.md"))
        check("317: a plain localhost POST to each guarded route is refused in one line, with no Origin, with the "
              "server's own forged and with a wrong key, and a GET of one too",
              all(a == refused for got in answers.values() for a in got) and got_guide == refused,
              json.dumps({k: [a[0] for a in v] for k, v in answers.items()}) + str(got_guide))
        check("317: and nothing is written: the board is there, the settings, the project's tick and AGENTS.md as they "
              "were", before == after and "Board 2" in boards() and not record.exists())

        # what governs nothing is answered as before, the key or not
        open_settings = call("POST", "/api/settings", {"op": "read"})
        open_project = call("POST", "/api/project", {"root": str(root)})
        check("317: the rest is answered as before, the settings read and a project read with no key",
              open_settings[0] == 200 and open_project[0] == 200
              and open_project[1]["project"]["agents"]["allowed"] is True)

        # the page's own call, carrying the key: the list of names to replace read
        listed = call("POST", "/api/names", {"op": "list", "root": str(root)}, key=KEY, origin=own)
        check("317: the page's own call with the key is answered", listed[0] == 200, str(listed)[:300])

        # the switch went with the holds (noholds, 13 November 2026): a save naming it keeps nothing, records nothing
        on = call("POST", "/api/settings", {"skip_permissions": True}, key=KEY, origin=own)
        check("317: a settings save naming Dangerously skip permissions is answered and ignored, the setting kept "
              "nowhere and no record of it written",
              on[0] == 200 and json.loads(config_file.read_text(encoding="utf-8")).get("skip_permissions") is not True
              and not record.exists(), str(on)[:200])
        ticked = call("POST", "/api/project", {"root": str(root), "agents": False}, key=KEY, origin=own)
        check("317: and the project's tick from the window", ticked[0] == 200
              and json.loads(project_file.read_text(encoding="utf-8"))["agents"]["allowed"] is False)
        call("POST", "/api/project", {"root": str(root), "agents": True}, key=KEY, origin=own)

        # the window's own run serves no key in its page; a run in a browser puts it in the page, a second step
        status, page = call("GET", "/")
        window_page = isinstance(page, str) and KEY not in page and 'name="idiograph-key"' not in page
        server_mod.WINDOW_KEY.update(key=KEY, window=False)
        status_b, page_b = call("GET", "/")
        in_page = isinstance(page_b, str) and f'<meta name="idiograph-key" content="{KEY}">' in page_b
        plain_b = call("POST", "/api/names", {"op": "list", "root": str(root)})
        page_b_call = call("POST", "/api/names", {"op": "list", "root": str(root)}, key=KEY, origin=own)
        check("317: the window's page never holds the key, a browser's page carries it, and there a plain POST is "
              "still refused while the page's call is answered",
              status == 200 and window_page and status_b == 200 and in_page and plain_b == refused
              and page_b_call[0] == 200)
        httpd.shutdown()
        httpd.server_close()
        httpd = None

        # the key's way in: standard input when the window says so, never an argument or the environment
        server_mod.READ_KEY = lambda: KEY
        server_mod.take_window_key({server_mod.WINDOW_KEY_FROM: "stdin"})
        from_window = dict(server_mod.WINDOW_KEY)
        server_mod.READ_KEY = lambda: ""
        server_mod.take_window_key({server_mod.WINDOW_KEY_FROM: "stdin"})
        missing = dict(server_mod.WINDOW_KEY)
        server_mod.READ_KEY = None
        server_mod.take_window_key({})
        own_key = dict(server_mod.WINDOW_KEY)
        read, write = os.pipe()
        os.write(write, (KEY + "\n").encode("ascii"))
        os.close(write)
        piped = server_mod.key_line(read)
        os.close(read)
        check("317: the window's key read from standard input, a run without one making its own for the page, and "
              "one that never came going on as a browser's",
              from_window == {"key": KEY, "window": True} and missing["window"] is False and len(missing["key"]) >= 32
              and own_key["window"] is False and own_key["key"] not in (KEY, missing["key"]) and piped == KEY)

        # a restart hands it on, on Windows on the new process's standard input, never in its command or environment
        server_mod.WINDOW_KEY.update(key=KEY, window=True)
        command, env = server_mod.relaunch()

        class Child:
            def __init__(self):
                self.stdin = io.BytesIO()
                self.stdin.close = lambda: None

        started = []

        def popen(cmd, **kw):
            started.append((cmd, kw, Child()))
            return started[-1][2]

        server_mod.POPEN = popen
        server_mod.spawn_again(command, env, key=KEY)
        cmd, kw, child = started[0]
        check("317: a restart hands the key on, on a pipe as the new run's standard input, never in its command or "
              "its environment",
              kw["stdin"] == server_mod.subprocess.PIPE and child.stdin.getvalue() == (KEY + "\n").encode("ascii")
              and KEY not in json.dumps(cmd) and KEY not in json.dumps(kw["env"]))

        # the agents' ops are unchanged: the command line and MCP read and ask as before
        code_cli, out_cli, err_cli = run("--json", "board", "list", "Juno")
        srv = mcp_server.Server(str(root), config=str(config_file))
        got = srv.receive(json.dumps({"jsonrpc": "2.0", "id": 1, "method": "tools/call",
                                      "params": {"name": "agent_changes", "arguments": {}}}))
        check("317: the command line and MCP answer an agent as before, no key asked of either",
              code_cli == 0 and "result" in got and not got["result"].get("isError"), err_cli or json.dumps(got)[:300])

        # the page sends the key on every call, and the window hands it over on a pipe and in its page's script alone
        shell = support.source("family/static/shell.js").read_text(encoding="utf-8")
        shell_rs = support.source("packaging/tauri/src-tauri/src/main.rs").read_text(encoding="utf-8")
        check("317: the page's every call carries the key, and the window writes it to the server's standard input and "
              "its page's script, never an argument",
              "{ 'X-Idiograph-Key': held }" in shell and 'idiograph-key' in shell and ".stdin(Stdio::piped())" in shell_rs
              and 'writeln!(input, "{}", key::key())' in shell_rs and "window.__IDIOGRAPH_KEY__" in shell_rs
              and ".env(key::FROM, \"stdin\")" in shell_rs and ".arg(key::key())" not in shell_rs)
    finally:
        if httpd is not None:
            httpd.shutdown()
            httpd.server_close()
        server_mod.CONFIG_PATH = kept[0]
        server_mod.WINDOW_KEY.clear()
        server_mod.WINDOW_KEY.update(kept[1])
        server_mod.READ_KEY, server_mod.POPEN = kept[2], kept[3]
