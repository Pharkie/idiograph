"""Area 307: codes, not English, between the page and the server, and Python's own tList and tDate (i18ncodes,
31 October 2026, Adam's ruling by dialog of that day: make Idiograph ready for a second language). A refusal the
page reacts to carries a code beside its words, one of family/errors.py's CODES, the page tests the code
(shell.js's `refusedAs`, `needsRestart`) and the ways back name the screen they return to by its step's key. The
server joins a list a person reads through formats.list_words, as the page's tList joins one, and writes a date
through formats.date_words, as the page's tDate writes one.

What is checked: every code the page tests is one of CODES and raised by the server, no script deciding by a
refusal's words or a step's English name; then on a made-up language, zz, whose catalogue words every coded
refusal otherwise, each refusal over HTTP in zz's words with its code, and in node on shell.js's own `api` the
page's every reaction taking it so, distil.js's own `trimRestore` saying to restart; and Python's list and date in
zz, British and American English and each dates choice, its lists the same as the page's Intl in both Englishes.
Part E (i18nleft, 1 November 2026): in zz, a board saved with the English Untitled reads as untitled, the keys' names
come from the catalogue, an AI change line and the hold card's question and waiting line are in its words.
Part F (i18nleft2, 1 November 2026): a revision the app names carries its kind and slots, one kept before marks is
found by its English name, and in zz the History shows both in its words, undo's steps are its words and a hold's
own lines, kept as keys, are too, an older hold reading as written.
Part G (i18nleft3, 2 November 2026): a revision's time in the formats and the run's language, its English name in
English's own, the History saying it from its ISO, a hold's time and its boards' list said as the card shows them, a
hold in its project's method's words, and TA's History and undo. Two checks that pinned one overlay word each,
Trace's en-US judgment and Sift's en-US percent, went on 2 November (testspeed): wording, which review holds.
Part H (i18nleft4, 2 November 2026): the command line's lines of the three apps, the Rename card's lines, the
family's lines on Home and Trace's card line in a made-up language, English as before, and TA's Rename card and
command line in its words.
Fixtures are the demo's invented workbook copied to the scratch folder and invented names."""
from __future__ import annotations

import http.server
import json
import re
import shutil
import threading
import urllib.error
import urllib.request
from datetime import datetime, timedelta, timezone
from pathlib import Path

from . import support
from .support import check, demo_copy, skip

# the made-up language: each refusal the page reacts to in words of its own, a list joined by its own marks and a
# month of its own, so a reaction that still read English words would miss every one
ZZ = {
    "errors.json": {
        "errors.such_endpoint": "Zz: there is no door here.",
        "errors.another_write_these_files_under": "Zz: the files are held by another hand.",
    },
    "server.json": {
        "server.something_board_can_do_nothing": "Zz: a board knows no such move.",
        "server.something_gets_screen_does_nothing": "Zz: the GETs know no such move.",
        "server.something_ai_help_does_nothing": "Zz: the helper knows no such question.",
        "server.rows_assigned_previewed_restored_untrimmed": "Zz: rows know no such move.",
        "server.board_changed_conversation_canvas_saved": "Zz: someone talked to this board, your canvas is in its History.",
        "server.project_s_file_longer_held": "Zz: the file has slipped away, drop it again.",
    },
    "lists.json": {
        "lists.and.two": "{a} & {b}", "lists.and.start": "{a} / {b}", "lists.and.middle": "{a} / {b}",
        "lists.and.end": "{a} & {b}",
        "lists.or.two": "{a} | {b}", "lists.or.start": "{a} / {b}", "lists.or.middle": "{a} / {b}",
        "lists.or.end": "{a} | {b}",
    },
    "dates.json": {"dates.dmy": "{day}. {month} {year}", "dates.mdy": "{month} the {day}th of {year}",
                   "dates.month.october": "Zoktober", "dates.mon.oct": "Zok"},
    # i18nleft (1 November 2026): the untitled label, the keys' names, the AI's change lines and the hold card's
    "themes.json": {"themes.untitled": "Zz nameless",
                    # i18nleft2 (1 November 2026): the History's names, undo's steps and a hold's own lines
                    "themes.revision.named.before_restoring": "Zz back to before {when}",
                    "themes.revision.named.canvas_kept": "Zz the talked-over canvas",
                    "themes.revision.named.statement_edited": "Zz {who} rewrote <{old}> as <{new}>",
                    "themes.step.aligned_centre": "Zz {n} to the middle line",
                    "themes.step.stacked": {"one": "Zz one stacked", "other": "Zz {n} stacked"}},
    "shell.json": {"shell.keys.cmd": "Zcmd", "shell.keys.ctrl": "Zctl"},
    "themes_ai.json": {"themes_ai.change.retitled": "zz renamed <{label}> to <{title}>",
                       "themes_ai.change.apart": "zz split <{label}>", "themes_ai.change.line": "{changes}!"},
}
# i18nleft3 (2 November 2026): a revision's time, a day with no year, the clock's am and pm, and a hold's time and
# list of boards
ZZ["dates.json"].update({"dates.dm": "{day}. {month}", "dates.md": "{month}/{day}",
                         "dates.clock.am": "{hour}h{minute} zam", "dates.clock.pm": "{hour}h{minute} zpm"})
ZZ["themes.json"].update({"themes.history.when": "{day} um {time}"})
CODE_CALL = re.compile(r"refusedAs\(\s*err\s*,\s*'([a-z_]+)'\s*\)")


def stmt(src: str, start: str) -> str:
    """A top-level statement or function of a script, from the line starting `start` to its end."""
    head = src.index("\n" + start) + 1
    if start.startswith(("function ", "async function ")):
        return src[head:src.index("\n}\n", head) + 3]
    return src[head:src.index(";\n", head) + 2]


def page_scripts() -> dict:
    """Every script of the page by its name, comments set aside."""
    out = {}
    for folder in support.static_folders():
        for path in sorted(folder.glob("*.js")):
            code = path.read_text(encoding="utf-8")
            out[path.name] = re.sub(r"(?m)^\s*//.*$", "", re.sub(r"/\*.*?\*/", "", code, flags=re.S))
    return out


def python_codes() -> set:
    """Every code a refusal of the server's carries where it is raised or answered."""
    found = set()
    for path in support.code_files():
        if "tests" in path.parts:
            continue
        text = path.read_text(encoding="utf-8")
        found |= set(re.findall(r"""\bcode=["']([a-z_]+)["']""", text))
        found |= set(re.findall(r"""["']code["']:\s*["']([a-z_]+)["']""", text))
    return found


def test_refusal_codes(scratch: Path):
    print("\n307. Codes, not English: every refusal the page tests carrying its code, a made-up language leaving every "
          "reaction working, the ways back by key, and Python's tList and tDate following the language and the "
          "formats (31 October 2026)")
    import boot
    import errors
    import formats
    import gets as gets_mod
    import i18n
    import idiograph_routes
    import locks
    import server as server_mod
    import themes as themes_mod
    import themes_print
    from workbook import WorkbookError

    # ── A. what the page tests, and the server raising each
    scripts = page_scripts()
    tested = {}
    for name, code in scripts.items():
        for c in CODE_CALL.findall(code):
            tested.setdefault(c, []).append(name)
    shell = support.text("family/static/shell.js")
    needs = stmt(shell, "const needsRestart = ")
    older = stmt(shell, "const olderServer = ")
    raised = python_codes()
    check("307: every code the page tests is one of errors.CODES and raised by the server: needsRestart's no_endpoint, "
          "and unknown_op, board_changed_outside and file_not_held",
          {"unknown_op", "board_changed_outside", "file_not_held"} <= set(tested)
          and "refusedAs(err, 'no_endpoint')" in needs and "code: 'no_endpoint'" in older
          and set(tested) | {"no_endpoint"} <= set(errors.CODES) and set(tested) | {"no_endpoint"} <= raised
          and raised <= set(errors.CODES), f"{sorted(tested)} {sorted(raised)}")
    words_test = re.compile(r"""\b(?:err|e|error|exc)\.message\)?\s*(?:===|!==|==|!=)|\.message[^;\n]*?\.(?:includes|startsWith|endsWith|indexOf|match)\(""")
    deciding = [f"{n}: {m.group(0)}" for n, code in scripts.items() for m in words_test.finditer(code)]
    english = re.compile(r"""\bto:\s*'(?:PETs|GETs|LPETs|LGETs|Trajectories|Experiential statements)'|"""
                         r"""(?:===|!==)\s*'(?:PETs|GETs|LPETs|LGETs|Trajectories)'|TH_STEP_NAMES|NO_ENDPOINT|"""
                         r"""TH_OUTSIDE_REFUSED|TH_REVIEW_OFF|GT_OLD_OP|OLD_ROWS|QD_GONE""")
    named = [f"{n}: {m.group(0)}" for n, code in scripts.items() for m in english.finditer(code)]
    check("307: no script decides by a refusal's words or passes a step by its English name, the ways back naming "
          "the step's key (TH_STEPS)",
          not deciding and not named and "const TH_STEPS = [" in support.text("apps/idiograph/static/themes.js"),
          "; ".join(deciding + named)[:400])
    # a refusal raised with its words alone, where a page or a module tests its code, would read as no code at all
    plain = []
    for path in support.code_files():
        if "tests" in path.parts:
            continue
        text = path.read_text(encoding="utf-8")
        for m in re.finditer(r"WorkbookError\((themes(?:_mod)?\.NOT_A_BOARD_OP|gets(?:_mod)?\.NOT_A_GETS_OP|"
                             r"i18n\.t\(\"(?:server\.something_board_can_do_nothing|server\.rows_assigned_previewed_"
                             r"restored_untrimmed|server\.board_changed_conversation_canvas_saved|server\.project_s_"
                             r"file_longer_held|errors\.another_write_these_files_under)\"\))\)", text):
            plain.append(f"{path.name}: {m.group(0)}")
    check("307: every raise of a refusal a script tests gives its code, none its words alone", not plain, "; ".join(plain))

    # ── B. a made-up language: the server's refusals in its words, each with its code
    fx = scratch / "a307-zz"
    shutil.rmtree(fx, ignore_errors=True)
    (fx / "static" / "i18n" / "zz").mkdir(parents=True)
    for name, messages in ZZ.items():
        (fx / "static" / "i18n" / "zz" / name).write_text(json.dumps(messages, ensure_ascii=False, indent=1),
                                                         encoding="utf-8")
    root = scratch / "a307-project"
    shutil.rmtree(root, ignore_errors=True)
    work = demo_copy(root, "P1 - Wren", "Wren - EN & ES.xlsx")
    cfg = scratch / "a307-config.json"
    cfg.write_text(json.dumps({"projects": [], "ai_suggest": True, "interviewer": "Adam"}), encoding="utf-8")
    kept = (i18n.LANGUAGE, i18n.ROOTS, i18n.CHOSEN_FORMATS, server_mod.CONFIG_PATH, server_mod.ROOT_OVERRIDE)
    real_roots = boot.roots()
    answers, direct = {}, {}
    try:
        i18n.ROOTS = lambda: [*real_roots, fx]
        i18n.LANGUAGE = lambda: "zz"
        i18n.CHOSEN_FORMATS = lambda: {}
        server_mod.CONFIG_PATH, server_mod.ROOT_OVERRIDE = cfg, root

        def code_of(fn):
            try:
                fn()
            except WorkbookError as exc:
                return [str(exc), exc.code]
            return None

        # a board an agent changed after the page last saw it, the page's save then refused
        first = themes_mod.blank_version(themes_mod.read_cards(work)["cards"])
        themes_mod.save(work, first, "Wren")
        held = themes_mod.load(work)
        board = themes_mod.boards_of(held)[0]
        later = (datetime.now(timezone.utc) + timedelta(minutes=5)).isoformat(timespec="seconds")
        board["changed"] = {"by": "agent", "tool": "Claude Code", "request": "tidy the hedgerow PETs", "at": later}
        themes_mod.write(work, held)
        seen = dict(board, updated="2026-10-30T09:00:00+00:00")
        seen.pop("changed", None)
        direct = {
            "themes version_op": code_of(lambda: themes_mod.version_op(work, "fly", {}, "Wren")),
            "themes board_op": code_of(lambda: themes_mod.board_op(work, "fly", {}, "Wren")),
            "gets version_op": code_of(lambda: gets_mod.version_op(root, [], "fly", {})),
            "gets board_op": code_of(lambda: gets_mod.board_op(root, [], "fly", {})),
            "qdpx": code_of(lambda: idiograph_routes.qdpx_held("gone")),
        }
        lock = scratch / "a307.lock"
        with locks.held(lock):
            direct["busy"] = code_of(lambda: locks.held(lock, wait=0).__enter__())

        httpd = http.server.ThreadingHTTPServer(("127.0.0.1", 0), server_mod.Handler)
        threading.Thread(target=httpd.serve_forever, kwargs={"poll_interval": 0.05}, daemon=True).start()
        base = f"http://127.0.0.1:{httpd.server_address[1]}"

        def call(route, body=None):
            req = urllib.request.Request(base + route, data=None if body is None else json.dumps(body).encode("utf-8"),
                                         headers={"Content-Type": "application/json"})
            try:
                with urllib.request.urlopen(req, timeout=20) as r:
                    return [r.status, json.loads(r.read())]
            except urllib.error.HTTPError as exc:
                return [exc.code, json.loads(exc.read())]

        try:
            answers = {
                "no_endpoint": call("/api/no-such-door", {}),
                "no_endpoint_get": call("/api/no-such-door"),
                "rows": call("/api/rows", {"op": "fly", "path": str(work)}),
                "versions": call("/api/themes-versions", {"workbook": str(work), "op": "fly"}),
                "ai": call("/api/themes-ai", {"workbook": str(work), "op": "fly"}),
                "qdpx": call("/api/qdpx", {"op": "read", "held": "gone"}),
                "outside": call("/api/themes-save", {"workbook": str(work), "version": seen}),
            }
        finally:
            httpd.shutdown()
            httpd.server_close()
        zz_list = [formats.list_words(["Ash"]), formats.list_words(["Ash", "Bryn"]),
                   formats.list_words(["Ash", "Bryn", "Cole", "Dara"]), formats.list_words(["Ash", "Bryn", "Cole"], "or")]
        i18n.CHOSEN_FORMATS = lambda: {"dates": "dmy"}
        zz_dates = [formats.date_words(datetime(2026, 10, 28)), formats.date_words(datetime(2026, 10, 4), short=True),
                    themes_print.when_printed(datetime(2026, 10, 28, 14, 5))]
        i18n.CHOSEN_FORMATS = lambda: {"dates": "mdy"}
        zz_dates.append(formats.date_words(datetime(2026, 10, 28)))
        i18n.CHOSEN_FORMATS = lambda: {"dates": "ymd"}
        zz_dates.append(formats.date_words(datetime(2026, 10, 28)))
        i18n.CHOSEN_FORMATS = lambda: {}
        twins = code_of(lambda: idiograph_routes.join_case(
            {"pseudonym": "Wren"}, [{"label": "P1 - Wren"}, {"label": "P4 - Wren"}, {"label": "P7 - Wren"}]))
        zz_script = i18n.script("zz")
    finally:
        i18n.LANGUAGE, i18n.ROOTS, i18n.CHOSEN_FORMATS, server_mod.CONFIG_PATH, server_mod.ROOT_OVERRIDE = kept

    zz = {k: v for m in ZZ.values() for k, v in m.items()}
    check("307: in the made-up language each refusal a script tests is in that language's words with its code, raised "
          "by the boards' ops, the GETs', the file a card sent and the lock",
          direct == {"themes version_op": [zz["server.something_board_can_do_nothing"], "unknown_op"],
                     "themes board_op": [zz["server.something_board_can_do_nothing"], "unknown_op"],
                     "gets version_op": [zz["server.something_board_can_do_nothing"], "unknown_op"],
                     "gets board_op": [zz["server.something_board_can_do_nothing"], "unknown_op"],
                     "qdpx": [zz["server.project_s_file_longer_held"], "file_not_held"],
                     "busy": [zz["errors.another_write_these_files_under"], "busy"]}, str(direct))
    want = {
        "no_endpoint": [404, {"error": zz["errors.such_endpoint"], "code": "no_endpoint"}],
        "no_endpoint_get": [404, {"error": zz["errors.such_endpoint"], "code": "no_endpoint"}],
        "rows": [409, {"error": zz["server.rows_assigned_previewed_restored_untrimmed"], "code": "unknown_op"}],
        "versions": [409, {"error": zz["server.something_board_can_do_nothing"], "code": "unknown_op"}],
        "ai": [200, {"error": zz["server.something_ai_help_does_nothing"], "code": "unknown_op"}],
        "qdpx": [409, {"error": zz["server.project_s_file_longer_held"], "code": "file_not_held"}],
        "outside": [409, {"error": zz["server.board_changed_conversation_canvas_saved"], "code": "board_changed_outside"}],
    }
    check("307: over HTTP in the made-up language the server answers each with its words and its code beside them: no "
          "such route, no such op of the rows, the boards and the AI help, the file no longer held, the board changed "
          "in a conversation",
          answers == want, json.dumps({k: v for k, v in answers.items() if want.get(k) != v}, ensure_ascii=False)[:600])

    # ── C. the page's every reaction on those answers, in node in the made-up language
    if not shutil.which("node"):
        skip("307: the page's reactions in node", "node is not on this machine")
    else:
        distil = support.text("apps/idiograph/static/distil.js")
        pieces = "".join([
            stmt(shell, "async function api("), stmt(shell, "const refusedAs = "), stmt(shell, "const RESTART_LINE = "),
            needs, older, stmt(distil, "async function trimRestore("),
        ])
        harness = r"""
const FAMILY_APPS = {};
const ANSWERS = """ + json.dumps(answers, ensure_ascii=False) + r""";
const TESTED = """ + json.dumps(sorted(tested)) + r""";
let next = null;
globalThis.fetch = async () => ({ ok: next[0] < 400, status: next[0], json: async () => next[1] });
const S = { dirty: false, data: { path: 'Wren.xlsx' } };
const current = () => ({ sheet: 'Initial', row: 4, key: 'Initial:4' });
const said = [];
const say = (line) => said.push(line);
async function asked(name) {
  next = ANSWERS[name];
  try { await api('/api/anything', {}); return null; } catch (err) { return err; }
}
(async () => {
  const out = { codes: {}, words: {}, restart: {}, english: RESTART_LINE };
  for (const name of Object.keys(ANSWERS)) {
    const err = await asked(name);
    out.codes[name] = err ? err.code : null;
    out.words[name] = err ? err.message : null;
    out.restart[name] = !!err && needsRestart(err);
  }
  // each code a page's reaction tests, met by the made-up language's answer that carries it
  out.reacts = {};
  for (const code of TESTED) {
    const name = Object.keys(ANSWERS).find((k) => ANSWERS[k][1].code === code);
    out.reacts[code] = !!name && refusedAs(await asked(name), code);
  }
  out.older = [needsRestart(olderServer()), olderServer().message === RESTART_LINE];
  // distil.js's own Cmd + Z of a trim, in front of a server that knows no untrim and one with no such route
  for (const name of ['rows', 'no_endpoint']) {
    next = ANSWERS[name];
    try { await trimRestore({ result: { id: 'cut-1' } }); out['trim_' + name] = 'went on'; }
    catch (err) { out['trim_' + name] = err.message; }
  }
  console.log(JSON.stringify(out));
})();
"""
        lib = support.text("family/static/i18n.js")
        ran = support.run_node(zz_script[len("<script>"):-len("</script>")] + "\n" + lib + "\n" + pieces + harness,
                               scratch, "a307-reactions.js")
        o = json.loads(ran.stdout.strip().splitlines()[-1]) if ran.returncode == 0 and ran.stdout.strip() else {}
        restart = i18n.t("shell.restart_line")
        check("307: in node on shell.js's own api in the made-up language, each refusal reaches the page with its code "
              "and its words, needsRestart taking no such route alone",
              o.get("codes") == {k: v[1]["code"] for k, v in answers.items()}
              and o.get("words") == {k: v[1]["error"] for k, v in answers.items()}
              and o.get("restart") == {k: k.startswith("no_endpoint") for k in answers}
              and o.get("older") == [True, True], (ran.stdout + ran.stderr)[:600])
        check("307: every reaction a script tests a code for takes the made-up language's answer, and distil.js's own "
              "trimRestore says to restart in front of a server with no untrim and with no such route",
              o.get("reacts") == {c: True for c in tested} and o.get("trim_rows") == restart
              and o.get("trim_no_endpoint") == restart and o.get("english") == restart,
              str({k: o.get(k) for k in ("reacts", "trim_rows", "trim_no_endpoint")}))

    # ── D. Python's tList and tDate, in the made-up language, British and American English
    check("307: Python's list in the made-up language is joined by its own marks, Ash / Bryn / Cole & Dara and a "
          "choice Ash / Bryn | Cole, and a refusal naming three participants joins them so",
          zz_list == ["Ash", "Ash & Bryn", "Ash / Bryn / Cole & Dara", "Ash / Bryn | Cole"]
          and twins is not None and "P1 - Wren / P4 - Wren & P7 - Wren" in twins[0], str([zz_list, twins]))
    check("307: Python's date in the made-up language takes its month and its sentence, the order the formats' choice, "
          "a print view's head with it",
          zz_dates == ["28. Zoktober 2026", "4. Zok 2026", "28. Zoktober 2026", "Zoktober the 28th of 2026", "2026-10-28"],
          str(zz_dates))
    lists = {}
    saved_lang = i18n.LANGUAGE
    try:
        for tag in ("en-GB", "en-US"):
            i18n.LANGUAGE = lambda tag=tag: tag
            lists[tag] = [formats.list_words(items, kind) for kind in ("and", "or")
                          for items in (["Ash"], ["Ash", "Bryn"], ["Ash", "Bryn", "Cole"], ["Ash", "Bryn", "Cole", "Dara"])]
    finally:
        i18n.LANGUAGE = saved_lang
    check("307: Python's list in English: Ash, Bryn and Cole in British and Ash, Bryn, and Cole in American, or for a "
          "choice",
          lists["en-GB"][2] == "Ash, Bryn and Cole" and lists["en-US"][2] == "Ash, Bryn, and Cole"
          and lists["en-GB"][7] == "Ash, Bryn, Cole or Dara" and lists["en-US"][7] == "Ash, Bryn, Cole, or Dara", str(lists))
    if not shutil.which("node"):
        skip("307: Python's lists beside the page's tList", "node is not on this machine")
    else:
        page = {}
        lib = support.text("family/static/i18n.js")
        for tag in ("en", "en-US"):
            inline = i18n.script(tag, real_roots)[len("<script>"):-len("</script>")]
            ran = support.run_node(inline + "\n" + lib + "\nconst out = [];\nfor (const type of ['conjunction', 'disjunction'])"
                                   " for (const items of [['Ash'], ['Ash', 'Bryn'], ['Ash', 'Bryn', 'Cole'], ['Ash', 'Bryn', 'Cole', 'Dara']])"
                                   " out.push(tList(items, type));\nconsole.log(JSON.stringify(out));\n",
                                   scratch, f"a307-lists-{tag}.js")
            page[tag] = json.loads(ran.stdout.strip().splitlines()[-1]) if ran.returncode == 0 and ran.stdout.strip() else ran.stderr
        check("307: Python's lists come out as the page's tList writes them, every length, and and or, in British and "
              "American English",
              page["en"] == lists["en-GB"] and page["en-US"] == lists["en-US"], str([page, lists]))

    # ── E. what i18ncodes left (i18nleft, 1 November 2026): the untitled label by the file's word, the keys' names,
    # the AI's change lines, each in the made-up language (the hold card's went with the holds, noholds, 13 November)
    import themes_ai
    kept = (i18n.LANGUAGE, i18n.ROOTS)
    try:
        i18n.ROOTS = lambda: [*real_roots, fx]
        i18n.LANGUAGE = lambda: "zz"
        zz_script = i18n.script("zz")
        board = {"groups": [{"id": "A", "label": "Walks"}, {"id": "B", "label": "Mornings"}], "unit": "statement"}
        zz_change = themes_ai.change_line([{"op": "retitle", "label": "A", "title": "Evening walks"},
                                           {"op": "apart", "label": "B"}], board)
    finally:
        i18n.LANGUAGE, i18n.ROOTS = kept
    en_change = themes_ai.change_line([{"op": "retitle", "label": "A", "title": "Evening walks"},
                                       {"op": "apart", "label": "B"}], board)
    check("307: the AI's change line is in the made-up language's words, joined by its own marks, and in English as "
          "it was",
          zz_change == "Zz renamed <Walks> to <Evening walks> & zz split <Mornings>!"
          and en_change == "Retitled 'Walks' as 'Evening walks' and took 'Mornings' apart.", f"{zz_change} | {en_change}")
    if not shutil.which("node"):
        skip("307: the untitled label and the keys' names in node", "node is not on this machine")
    else:
        themes_js = support.text("apps/idiograph/static/themes.js")
        pieces = "".join(stmt(themes_js, s) for s in ("const TH_UNTITLED_SAVED = ", "const TH_UNTITLED = ",
                                                      "const thUntitled = ", "const thLabelKept = ",
                                                      "const thLabelShown = ", "function thNamesBody("))
        keys = stmt(shell, "const keyName = ")
        harness = r"""
const TH = { meta: null };
const thGroup = (v, id) => v.groups.find((g) => g.id === id);
const thCardsUnder = () => [];
const thNoteOf = () => '';
const v = { cards: {}, groups: [{ id: 'A', label: 'Walks' }, { id: 'B', label: 'Untitled' }, { id: 'C', label: 'Zz nameless' }] };
const out = {
  untitled: ['Untitled', 'Zz nameless', '', 'Walks'].map(thUntitled),
  shown: [thLabelShown('Untitled'), thLabelShown('Walks')],
  kept: [thLabelKept('Zz nameless'), thLabelKept(''), thLabelKept('Untitled'), thLabelKept('Walks')],
  others: thNamesBody(v, { id: 'B' }),
};
let MAC = false;
out.windows = [keyName('Zcmd / Zctl + F'), keyName('Undo (Zcmd + Z)')];
console.log(JSON.stringify(out));
"""
        lib = support.text("family/static/i18n.js")
        ran = support.run_node(zz_script[len("<script>"):-len("</script>")] + "\n" + lib + "\n" + pieces + keys + harness,
                               scratch, "a307-untitled.js")
        o = json.loads(ran.stdout.strip().splitlines()[-1]) if ran.returncode == 0 and ran.stdout.strip() else {}
        check("307: a board saved in English reads as untitled under another language: its Untitled is shown in that "
              "language's word, a label left blank or typed as that word is kept as the file's own Untitled, and a name "
              "suggestion sends neither as a title",
              o.get("untitled") == [True, True, True, False] and o.get("shown") == ["Zz nameless", "Walks"]
              and o.get("kept") == ["Untitled", "Untitled", "Untitled", "Walks"]
              and (o.get("others") or {}).get("label") == "" and (o.get("others") or {}).get("others") == ["Walks"],
              (ran.stdout + ran.stderr)[:600])
        check("307: the keys' names come from the catalogue, the made-up language's Cmd and Ctrl, Ctrl alone off a Mac",
              o.get("windows") == ["Zctl + F", "Undo (Zctl + Z)"], str(o.get("windows")))

    # ── F. what i18nleft left (i18nleft2, 1 November 2026): a revision the app names carries its kind and slots and
    # is shown through the catalogue, one kept before marks found by its English name, undo's steps and a hold's own
    # lines in the made-up language, and Trace's American spelling
    blank = {"cards": {}, "groups": []}
    old_board = {"history": [{"id": "r1", "at": "2026-10-03T10:04:00+00:00", "name": str(themes_mod.CANVAS_KEPT),
                              "auto": False, "state": blank},
                             {"id": "r2", "at": "2026-10-03T10:05:00+00:00", "name": "Before restoring 10:04",
                              "auto": False, "state": blank}]}
    old_marks = [themes_mod.revision_mark(r) for r in old_board["history"]]
    old_board["history"] = old_board["history"][:1]
    themes_mod.keep_canvas(old_board, blank, at="2026-10-03T11:00:00+00:00")
    kept_one = old_board["history"]
    edited: dict = {}
    themes_mod.add_revision(edited, name=themes_mod.edit_line("Ash", "the long walk home", "the short walk home"))
    check("307: a revision kept before marks is found by its English name, Before restoring with its time and the "
          "canvas kept over an agent's change, which the next keep takes the place of",
          old_marks == [("canvas_kept", {}), ("before_restoring", {"when": "10:04"})]
          and len(kept_one) == 1 and kept_one[0]["at"] == "2026-10-03T11:00:00+00:00", f"{old_marks} {kept_one}")
    check("307: a new revision the app names carries its mark, kind and slots, beside its English name",
          kept_one[0].get("kind") == "canvas_kept" and kept_one[0]["name"] == themes_mod.CANVAS_KEPT
          and edited["history"][0].get("kind") == "statement_edited"
          and edited["history"][0].get("slots") == {"who": "Ash", "old": "the long walk home", "new": "the short walk home"}
          and edited["history"][0]["name"] == "Ash's statement edited: \"the long walk home\" to \"the short walk home\"",
          json.dumps(edited["history"][0]))
    kept = (i18n.LANGUAGE, i18n.ROOTS)
    try:
        i18n.ROOTS = lambda: [*real_roots, fx]
        i18n.LANGUAGE = lambda: "zz"
        zz_script = i18n.script("zz")
    finally:
        i18n.LANGUAGE, i18n.ROOTS = kept
    part_g(scratch, fx, real_roots)
    part_h(scratch, real_roots)
    if not shutil.which("node"):
        skip("307: the History's names and undo's steps in node", "node is not on this machine")
        return
    summaries = [themes_mod.revision_summary(r) for r in (
        {"id": "r1", "name": "Before restoring 10:04", "at": ""},
        {"id": "r2", "name": "", "at": "", "kind": "canvas_kept", "slots": {}},
        edited["history"][0], {"id": "r4", "name": "Walks sorted", "at": ""})]
    themes_js = support.text("apps/idiograph/static/themes.js")
    pieces = "".join(stmt(themes_js, s) for s in ("const TH_REVISION_SAID = ", "function thRevisionSaid(",
                                                  "const TH_ALIGN_STEP = "))
    harness = "const rs = " + json.dumps(summaries) + r""";
console.log(JSON.stringify({ names: rs.map(thRevisionSaid), steps: [TH_ALIGN_STEP.centre(3),
  t('themes.step.stacked', { n: 1 }), t('themes.step.stacked', { n: 4 })] }));
"""
    lib = support.text("family/static/i18n.js")
    ran = support.run_node(zz_script[len("<script>"):-len("</script>")] + "\n" + lib + "\n" + pieces + harness,
                           scratch, "a307-revisions.js")
    o = json.loads(ran.stdout.strip().splitlines()[-1]) if ran.returncode == 0 and ran.stdout.strip() else {}
    check("307: the History shows a revision the app named in the made-up language, one kept before marks too, and "
          "one named by hand as it was named",
          o.get("names") == ["Zz back to before 10:04", "Zz the talked-over canvas",
                             "Zz Ash rewrote <the long walk home> as <the short walk home>", "Walks sorted"],
          (ran.stdout + ran.stderr)[:600])
    check("307: undo's steps are in the made-up language's words, a count in its plural",
          o.get("steps") == ["Zz 3 to the middle line", "Zz one stacked", "Zz 4 stacked"], str(o.get("steps")))


def part_g(scratch: Path, fx: Path, real_roots: list) -> None:
    """Part G (i18nleft3, 2 November 2026): a revision's time through the formats and the run's language, its English
    name kept in English's own, the History saying it from its ISO in the page's language, a TA project's History and
    undo in TA's words, and Sift's American English. A hold's lines went with the holds (noholds, 13 November)."""
    import boot
    import i18n
    import server as server_mod
    import themes as themes_mod

    local = lambda *a: datetime(*a).astimezone()  # noqa: E731
    evening = local(2026, 10, 2, 20, 0)
    times = [local(2026, 10, 2, 12, 4), local(2026, 10, 1, 12, 4), local(2025, 10, 1, 13, 4)]
    kept = (i18n.LANGUAGE, i18n.ROOTS, i18n.CHOSEN_FORMATS)
    said: dict = {}
    try:
        i18n.CHOSEN_FORMATS = lambda: {"dates": "dmy", "time": "24"}
        i18n.LANGUAGE = lambda: "en"
        said["en"] = [themes_mod.when_said(x.isoformat(), evening) for x in times]
        i18n.ROOTS = lambda: [*real_roots, fx]
        i18n.LANGUAGE = lambda: "zz"
        said["zz"] = [themes_mod.when_said(x.isoformat(), evening) for x in times]
        i18n.CHOSEN_FORMATS = lambda: {"dates": "mdy", "time": "12"}
        said["zz12"] = themes_mod.when_said(times[2].isoformat(), evening)
        said["kept"] = themes_mod.when_said(times[2].isoformat(), evening, lang="en")
        i18n.ROOTS = lambda: real_roots
        i18n.LANGUAGE = lambda: "en-US"
        said["us"] = themes_mod.when_said(times[1].replace(hour=13).isoformat(), evening)
        i18n.LANGUAGE = lambda: "zz"
        i18n.ROOTS = lambda: [*real_roots, fx]
        i18n.CHOSEN_FORMATS = lambda: {"dates": "dmy", "time": "24"}
        last_year = datetime(datetime.now().year - 1, 10, 1, 12, 4).astimezone().isoformat()
        named = themes_mod.revision_name("before_restoring", when_at=last_year)
        zz_script = i18n.script("zz")
    finally:
        i18n.LANGUAGE, i18n.ROOTS, i18n.CHOSEN_FORMATS = kept
    year = int(last_year[:4])
    check("307: a revision's time follows the formats and the run's language as the History's does, English as it "
          "was, a made-up language's day, month and clock, the 12-hour clock's pm, American English's PM, and a fixed "
          "English in English's own formats",
          said["en"] == ["12:04", "1 October 12:04", "1 October 2025 13:04"]
          and said["zz"] == ["12:04", "1. Zoktober um 12:04", "1. Zoktober 2025 um 13:04"]
          and said["zz12"] == "Zoktober the 1th of 2025 um 1h04 zpm" and said["kept"] == "1 October 2025 13:04"
          and said["us"] == "October 1 1:04 PM", json.dumps(said))
    check("307: a revision named with a time keeps its English name in English's own formats under another language, "
          "the time's ISO beside its slots",
          str(named) == f"Before restoring 1 October {year} 12:04" and named.kind == "before_restoring"
          and named.slots == {"when": f"1 October {year} 12:04", "when_at": last_year}, f"{named} {named.slots}")
    if not shutil.which("node"):
        skip("307: the History's time from its ISO and TA's History and undo in node", "node is not on this machine")
        return
    themes_js = support.text("apps/idiograph/static/themes.js")
    pieces = "".join(stmt(themes_js, s) for s in ("const TH_DAY = ", "const TH_DAY_YEAR = ", "const thSameDay = ",
                                                  "const thClockOf = ", "function thWhen(", "const TH_REVISION_SAID = ",
                                                  "function thRevisionSaid("))
    lib = support.text("family/static/i18n.js")
    fixed = "\nI18N.formats = { dates: 'dmy', time: '24', numbers: '' };\n"
    made = datetime.now().astimezone().isoformat()
    revs = [{"id": "r1", "at": made, "name": str(named), "kind": "before_restoring",
             "slots": {"when": "stale words", "when_at": last_year}},
            {"id": "r2", "at": made, "name": "Before restoring 10:04", "kind": "before_restoring",
             "slots": {"when": "10:04"}}]
    harness = "const rs = " + json.dumps(revs) + ";\nconsole.log(JSON.stringify(rs.map(thRevisionSaid)));\n"
    ran = support.run_node(zz_script[len("<script>"):-len("</script>")] + fixed + lib + "\n" + pieces + harness,
                           scratch, "a307-when.js")
    o = json.loads(ran.stdout.strip().splitlines()[-1]) if ran.returncode == 0 and ran.stdout.strip() else []
    check("307: the History says a revision's time from its ISO in the page's language and formats, as it read when "
          "the revision was made, and one from before by its kept words",
          len(o) == 2 and o[0].startswith("Zz back to before ") and o[0].endswith(f"{year} um 12:04")
          and "stale" not in o[0] and o[1] == "Zz back to before 10:04", (ran.stdout + ran.stderr)[:600])
    en_script = i18n.script("en", real_roots)
    edited = themes_mod.revision_summary({"id": "r3", "at": "", "name": "", "kind": "statement_edited",
                                          "slots": {"who": "Ash", "old": "a walk", "new": "the walk"}})
    harness = "const r = " + json.dumps(edited) + r""";
const said = (m) => tIn(m, () => [thRevisionSaid(r), t('themes.step.statement_edited'), t('themes.step.picked'),
  t('themes.step.put_on_board', { n: 3 })]);
console.log(JSON.stringify({ ta: said('ta'), ipa: said('ipa') }));
"""
    ran = support.run_node(en_script[len("<script>"):-len("</script>")] + "\n" + lib + "\n" + pieces + harness,
                           scratch, "a307-ta-history.js")
    o = json.loads(ran.stdout.strip().splitlines()[-1]) if ran.returncode == 0 and ran.stdout.strip() else {}
    check("307: a thematic analysis project's History and undo steps are in TA's words, an IPA project's as before",
          o.get("ta") == ["Ash's code edited: \"a walk\" to \"the walk\"", "Edited a code", "Picked an extract",
                          "Put 3 codes on the board"]
          and o.get("ipa") == ["Ash's statement edited: \"a walk\" to \"the walk\"", "Edited a statement",
                               "Picked a quote", "Put 3 statements on the board"], (ran.stdout + ran.stderr)[:600])


def part_h(scratch: Path, real_roots: list) -> None:
    """Part H (i18nleft4, 2 November 2026): the last English in code moved, nothing in English changed. In a
    made-up language whose every moved message says "ZZ " first, the command line's lines of the three apps
    (Idiograph's cases and statements, a refusal of each app), the Rename card's lines, the family's lines on Home
    and Trace's card line come from the catalogue; in English they read as they did; and a thematic analysis
    project's Rename card and command line say its own words. That every moved line's English is the old one word
    for word was compared line by line in the build (its same.py, 1,000 lines and more)."""
    import cli
    import i18n
    import idiograph_routes
    import server as server_mod
    import trace_claims

    own = {"apps/idiograph/static/i18n/en/cli.json": None, "family/static/i18n/en/family_cli.json": None,
           "apps/sift/static/i18n/en/sift_cli.json": None, "apps/trace/static/i18n/en/trace_cli.json": None,
           "apps/trace/static/i18n/en/trace_server.json": None,
           "apps/idiograph/static/i18n/en/server.json": "server.rename.",
           "family/static/i18n/en/shell.json": "shell.family.line."}
    fx = scratch / "a307-zz-h"
    shutil.rmtree(fx, ignore_errors=True)
    (fx / "static" / "i18n" / "zz").mkdir(parents=True)
    for rel, only in own.items():
        english = json.loads(support.text(rel))
        zz = {k: ({f: "ZZ " + w for f, w in v.items()} if isinstance(v, dict) else "ZZ " + v)
              for k, v in english.items() if only is None or k.startswith(only)}
        (fx / "static" / "i18n" / "zz" / Path(rel).name).write_text(json.dumps(zz, ensure_ascii=False), encoding="utf-8")
    # a project of one participant, Juno, with a GETs file naming her, IPA's and a thematic analysis one's
    roots = {}
    for method in ("ipa", "ta"):
        root = scratch / f"a307-h-{method}"
        shutil.rmtree(root, ignore_errors=True)
        demo_copy(root, "Juno", "Juno - EN & ES.xlsx")
        (root / server_mod.PROJECT_FILE).write_text(json.dumps({"name": "Hedgerows", "method": method,
                                                                 "agents": {"allowed": True, "at": None}}), encoding="utf-8")
        (root / "idiograph-gets.json").write_text(json.dumps({"cases": {"Juno": {}}}), encoding="utf-8")
        roots[method] = root
    cfg = scratch / "a307-h-config.json"
    cfg.write_text(json.dumps({"projects": [], "interviewer": "Adam"}), encoding="utf-8")
    nowhere = scratch / "a307-h-nowhere"

    def lines_of(argv: list) -> list:
        _code, out, err = cli.run(argv)
        return [x for x in (out + err).splitlines() if x.strip()]

    def runs(root: Path) -> dict:
        own_args = ["--config", str(cfg), "--root", str(root)]
        out = {"cases": lines_of([*own_args, "cases"]), "statements": lines_of([*own_args, "statements", "Juno"]),
               "nobody": lines_of([*own_args, "statements", "Nobody"]),
               "nothing": []}
        with support.as_app("sift"):
            out["sift"] = lines_of(["sift", str(root), "counts"])
        with support.as_app("trace"):
            out["trace"] = lines_of(["trace", str(nowhere)])
        plan, _ = idiograph_routes.rename_plan(root, root / "Juno", "Wren", True, {"interviewer": "Adam"})
        out["rename"] = plan["lines"] + plan["folder_lines"]
        # the family's lines as Sift's Home shows them, Idiograph's naming no other app since nosiftrace (12 November 2026)
        with support.as_app("sift"):
            out["family"] = [r["line"] for r in server_mod.family_rows()]
        out["idiograph family"] = server_mod.family_rows()
        out["card"] = [trace_claims.stands(root)]
        return out

    kept = (i18n.LANGUAGE, i18n.ROOTS, server_mod.CONFIG_PATH, server_mod.ROOT_OVERRIDE, server_mod.STATE_MEMORY)
    said: dict = {}
    try:
        server_mod.CONFIG_PATH, server_mod.ROOT_OVERRIDE, server_mod.STATE_MEMORY = cfg, None, {"recent": []}
        i18n.ROOTS = lambda: [*real_roots, fx]
        i18n.LANGUAGE = lambda: "zz"
        said["zz"] = runs(roots["ipa"])
        i18n.ROOTS = lambda: real_roots
        i18n.LANGUAGE = lambda: "en"
        said["en"] = runs(roots["ipa"])
        with i18n.in_method("ta"):
            ta_plan, _ = idiograph_routes.rename_plan(roots["ta"], roots["ta"] / "Juno", "Wren", True,
                                                      {"interviewer": "Adam"})
        said["ta"] = {"rename": ta_plan["lines"],
                      "statements": lines_of(["--config", str(cfg), "--root", str(roots["ta"]), "statements", "Juno"])[:1]}
    finally:
        i18n.LANGUAGE, i18n.ROOTS, server_mod.CONFIG_PATH, server_mod.ROOT_OVERRIDE, server_mod.STATE_MEMORY = kept
    zz, en = said["zz"], said["en"]
    # every line but the project's own name and the participant's workbook carries a catalogue word here
    bare = [x for k in ("cases", "nobody", "sift", "trace", "rename", "family", "card") for x in zz[k]
            if "ZZ" not in x and x.strip() not in ("Hedgerows", "Juno: Juno - EN & ES.xlsx")]
    check("307: in a made-up language the command line's lines of the three apps, a refusal of each, the Rename "
          "card's lines, the family's lines on Home and Trace's card line all come from the catalogue",
          not bare and zz["statements"] and "ZZ" in zz["statements"][0] and len(zz["rename"]) >= 3
          and len(zz["family"]) == 2, json.dumps({"bare": bare, "statements": zz["statements"][:2]})[:900])
    check("307: in English the same lines read as they did, word for word: the Rename card's, the family's, Trace's "
          "card and a refusal of Idiograph and Trace",
          "The project's GETs" in en["rename"] and "The folder Juno becomes Wren" in en["rename"]
          and "The annotated workbook takes the new name" in en["rename"]
          and en["family"] == ["Interpretative Phenomenological Analysis: statements, PETs and GETs",
                               "Each claim a manuscript makes, held against its reference"]
          and en["idiograph family"] == []
          and en["card"] == ["No document yet"] and en["trace"] == ["That folder is not there."]
          and en["nobody"][0].startswith("No participant called Nobody in this project. Its participants: ")
          and not any("ZZ" in x for k in en for x in en[k]), json.dumps(en)[:900])
    check("307: a thematic analysis project's Rename card names its themes and its command line its codes, an IPA "
          "project's its GETs and statements",
          "The project's themes" in said["ta"]["rename"] and "The project's GETs" not in said["ta"]["rename"]
          and bool(said["ta"]["statements"]) and " codes, short ids" in said["ta"]["statements"][0]
          and " statements, short ids" in en["statements"][0], json.dumps([said["ta"], en["statements"][:1]])[:600])
