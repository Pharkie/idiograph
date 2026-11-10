from __future__ import annotations

import json
import re
import shutil
from pathlib import Path

from . import support
from .support import check, skip


def test_feedback_names_its_screen(scratch):
    print("\n160. A feedback note names the screen it came from, 16 October, Adam's word: every bar's bug sends one short "
          "word of a fixed list, home, project, statements, pets, gets, sift, searches or trace, which the server and "
          "the collector both keep, any other value going as none, and nothing else added to the note. Since the test "
          "review of 18 October the docs' words are review shots, and the list, the handlers, what the note carries and "
          "what the card and the README tell him goes stay")
    import subprocess
    import server as server_mod

    folder = support.source("feedback-worker")
    read = lambda path: Path(path).read_text(encoding="utf-8")
    flat = lambda text: " ".join(str(text).split())
    names = ("home", "project", "statements", "pets", "gets", "sift", "searches", "trace")
    page = support.every_page()
    scripts = {n: support.text(*paths) for n, paths in (
        ("app.js", ("family/static/shell.js", "apps/idiograph/static/distil.js")), ("themes.js", ("apps/idiograph/static/themes.js",)),
        ("trajectories.js", ("apps/idiograph/static/trajectories.js",)),
        ("codes.js", ("apps/idiograph/static/codes.js",)),
        ("sift.js", ("apps/sift/static/sift.js",)), ("sift_search.js", ("apps/sift/static/sift_search.js",)),
        ("trace.js", ("apps/trace/static/trace.js",)))}
    worker, schema = read(folder / "worker.js"), read(folder / "schema.sql")
    readme = read(support.source("README.md"))
    # an invented study on learning to swim as an adult, whose names a note must never carry
    project, case = "Swimming late", "P3 - Ottoline"
    folder_path = f"/Users/someone/{project}/{case}/{case}.xlsx"
    junk = ["", "Settings", "settings", "GETs", "Pets", " pets", "pets ", "home/project", "statements, pets", project,
            case, "Ottoline", folder_path, None, 7, True, ["pets"], {"screen": "pets"}]

    # ── A. one fixed list, the same in the server and the collector
    listed = re.search(r"^const SCREENS = \[(.*?)\];$", worker, flags=re.M)
    worker_names = tuple(re.findall(r"'(\w+)'", listed.group(1))) if listed else ()
    check("160: the server's FEEDBACK_SCREENS is the fixed list, a word for each screen a bar stands on, the first "
          "screen, a project's page, Experiential statements, PETs, GETs, Sift, its searches and Trace",
          server_mod.FEEDBACK_SCREENS == names, str(server_mod.FEEDBACK_SCREENS))
    check("160: the collector's SCREENS is the same list in the same order, written as plain words and no pattern",
          worker_names == names and listed.group(1).count(",") == len(names) - 1, str(worker_names))

    # ── B. every bar's bug names its screen, and only with a word of the list
    bugs = set()
    for text in [page, *scripts.values()]:
        bugs |= set(re.findall(r'class="rail-btn bar-tool rail-feedback" id="([\w-]+)"', text))
    handlers = {}
    for text in scripts.values():
        for bid, expr, arg in re.findall(r"\$\('([\w-]+)'\)\.onclick = \(\) => (openFeedback\((.*?)\));", text):
            handlers.setdefault(bid, []).append((expr, arg))
    fixed = re.compile(r"'(\w+)'|(?:!\$\('home-project'\) \|\| )?\$\('home-project'\)\.hidden \? '(\w+)' : '(\w+)'|TH\.mode === 'gets' \? '(\w+)' : '(\w+)'")
    sent = {w for found in handlers.values() for _, arg in found for w in re.findall(r"'(\w+)'", arg)}
    check("160: eight bars carry the bug, the first screen's head, Experiential statements, PETs and GETs, Trajectories "
          "since option C of the bars (26 October 2026), the Code list (2 November 2026), Sift, its searches and Trace, "
          "each with one handler",
          bugs == {"lib-feedback", "btn-feedback", "th-feedback", "tj-feedback", "cd-feedback", "sf-feedback", "sfs-feedback",
                   "tr-feedback"}
          and set(handlers) == bugs and all(len(v) == 1 for v in handlers.values()), f"{sorted(bugs)} {sorted(handlers)}")
    check("160: each handler passes a fixed word, or one of two by where the screen stands, never anything read from "
          "the case, the project or the page's text, and between them they send every word of the list and no other",
          all(fixed.fullmatch(arg) for found in handlers.values() for _, arg in found) and sent == set(names),
          str({k: v[0][1] for k, v in handlers.items()}))

    # ── C. the server keeps each word and drops anything else, and adds nothing else to the note
    calls = []

    def fake(method, to, headers, payload, timeout):
        calls.append(payload)
        return 200, '{"ok": true, "id": 3}'

    kept = (server_mod.CONFIG_PATH, server_mod.FEEDBACK_SEND, server_mod.FEEDBACK_URL)
    server_mod.CONFIG_PATH = scratch / "feedback-160-config.json"
    server_mod.CONFIG_PATH.write_text(json.dumps({"interviewer": "Wren", "feedback_url": "http://127.0.0.1:9/v1/feedback"}),
                                      encoding="utf-8")
    server_mod.FEEDBACK_SEND = fake
    server_mod.FEEDBACK_URL = ""
    try:
        answers = [server_mod.api_feedback({"text": "The lane rope hides the timer.", "screen": w, "agent": "UA"})
                   for w in names]
        good = [c["screen"] for c in calls]
        del calls[:]
        dropped = [server_mod.api_feedback({"text": "A note", "screen": w, "project": project, "case": case,
                                            "path": folder_path}) for w in junk]
        bad = [c["screen"] for c in calls]
        shapes = {tuple(c) for c in calls}
        flat_sent = json.dumps(calls)
    finally:
        server_mod.CONFIG_PATH, server_mod.FEEDBACK_SEND, server_mod.FEEDBACK_URL = kept
    check("160: through the route, a note from each screen goes with its word",
          good == list(names) and all(a == {"sent": True, "id": 3} for a in answers), str(good))
    check("160: and any other value goes as none, a word of another case, a list, a number, a project's or a case's "
          "name or a path alike, and the note still goes",
          bad == [""] * len(junk) and all(a.get("sent") for a in dropped), str(bad))
    check("160: the note carries the same seven keys as before, and no project, case or path whatever the page sends",
          shapes == {("text", "contact", "version", "platform", "screen", "agent", "at")}
          and project not in flat_sent and "Ottoline" not in flat_sent and "/Users/someone" not in flat_sent, str(shapes))

    # ── D. the collector, its list page and notes.sh, and no change to the table
    check("160: the table keeps its screen column as it was, so the collector needs no change to its schema",
          "  screen   TEXT NOT NULL DEFAULT ''," in schema
          and "screen: SCREENS.includes(body.screen) ? body.screen : ''," in worker)
    node = shutil.which("node")
    if not node:
        skip("160: the collector and the bars' handlers in node", "no node on this machine")
    else:
        copy = scratch / "feedback-160-worker.mjs"
        shutil.copy2(folder / "worker.js", copy)
        given = scratch / "feedback-160-input.json"
        given.write_text(json.dumps({"names": list(names), "junk": junk,
                                     "handlers": {k: v[0][0] for k, v in handlers.items()}}), encoding="utf-8")
        script = scratch / "feedback-160-run.mjs"
        script.write_text(r"""
import { readFileSync } from 'node:fs';
import { pathToFileURL } from 'node:url';
const mod = await import(pathToFileURL(process.argv[2]).href);
const input = JSON.parse(readFileSync(process.argv[3], 'utf8'));
const row = (screen) => mod.noteRow({ text: 'A note', screen }, '2026-10-16T09:00:00.000Z', 'hash').screen;
const out = { kept: input.names.map(row), dropped: input.junk.map(row) };
out.page = mod.notesPage(input.names.map((screen, i) => ({ id: i + 1, at: 'at', text: 'A note', contact: '', screen,
  version: '', platform: '', agent: '' })));
// each bar's handler run as written, in a stand-in for the page, on a screen as it stands and then the other way
const said = [];
const state = { project: false, mode: 'pets' };
const $ = (id) => ({ hidden: id === 'home-project' ? !state.project : false });
const TH = state;
const openFeedback = (screen) => { said.push(screen); };
out.handlers = {};
for (const [id, expr] of Object.entries(input.handlers)) {
  const run = new Function('$', 'TH', 'openFeedback', `return () => ${expr};`)($, TH, openFeedback);
  state.project = false; state.mode = 'pets'; run();
  state.project = true; state.mode = 'gets'; run();
  out.handlers[id] = said.splice(0);
}
console.log(JSON.stringify(out));
""", encoding="utf-8")
        run = subprocess.run([node, str(script), str(copy), str(given)], capture_output=True, text=True, encoding="utf-8")
        out = json.loads(run.stdout) if run.returncode == 0 else {}
        check("160: in node, the collector keeps each word of the list as it came and takes any other value as none",
              out.get("kept") == list(names) and out.get("dropped") == [""] * len(junk), run.stderr.strip()[:300] or str(out.get("dropped")))
        check("160: in node, the list page shows each note's screen in its Screen column",
              all(f"<td>{w}</td>" in out.get("page", "") for w in names), run.stderr.strip()[:200])
        check("160: in node, each bar's handler says its screen, the home screen's home or project by the page shown "
              "and the PETs and GETs bar's pets or gets by the canvas",
              out.get("handlers") == {"btn-feedback": ["statements", "statements"], "lib-feedback": ["home", "project"],
                                      "th-feedback": ["pets", "gets"], "tj-feedback": ["gets", "gets"],
                                      "cd-feedback": ["gets", "gets"], "sf-feedback": ["sift", "sift"],
                                      "sfs-feedback": ["searches", "searches"], "tr-feedback": ["trace", "trace"]},
              str(out.get("handlers")))

    # ── E. the card and the README tell him what goes
    card = page.split('<div class="overlay" id="feedback" hidden>', 1)[1].split("</div>", 1)[0]
    privacy = flat(readme.split("\n## Privacy\n", 1)[1].split("\n## ", 1)[0])
    check("160: the card's small type says the screen's name goes too, and nothing from the participants",
          "Sent with the app's version, your system and the name of this screen. Nothing from your participants goes." in card)
    check("160: the README's Privacy says a note carries the screen it came from, the README under 1,000 words",
          "which carries your words, the app's version, your system, the screen it came from and the time, and nothing "
          "from your projects" in privacy and len(readme.split()) < 1000, f"{len(readme.split())} words")
