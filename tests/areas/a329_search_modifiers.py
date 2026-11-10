"""Area 329: Whole word and Match case in Search (searchmods, 6 November 2026, Adam: "cat" found "catch" and
"catching", and he asked for the typical modifiers, whole word only and similar). Two ticks beside the Search field,
both off until set, the engine's, the HTTP route's, the command line's and MCP's alike: Whole word finds each word
typed, and its other forms, only as a whole word, a phrase in quotation marks only on word edges, and Match case
finds the word in the case typed with its accents still set aside, its other forms in that case. The marks in each
hit, on the page and in an agent's snippet, follow the same rules. The card's keys are the tool's and the command
line's, so an agent can do what the card can.

The fixtures are invented: a ferry crossing, one made-up participant, Haddie, and a Sift-style record made up
for the engine."""
from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
from pathlib import Path

import openpyxl

from . import support
from .support import check, skip


def make_workbook(root: Path, name: str) -> Path:
    """A made-up ferry passenger's workbook: the cat on the rail in two passages and two statements, a name with a
    capital in the middle, a word with an accent and a word of the same stem in a longer word."""
    import workbook as wb_mod
    folder = root / name
    (folder / "Source").mkdir(parents=True)
    raw = openpyxl.Workbook()
    first = raw.active
    first.title = "Initial"
    first.append(["Name", "Timestamp", "Transcript"])
    first.append(["Interviewer", "00:00:04", "Tell me about the crossing."])
    first.append([name, "00:00:09", "The ferry cat sat by the rail. We would catch the early boat and the cat slept on "
                                    "my coat, and sleeps there still."])
    first.append(["Interviewer", "00:00:20", "What else mattered?"])
    first.append([name, "00:00:26", "Catching the tide mattered more than any cat. The tide table hung in the café. "
                                    "Will wrote in it. Will it hold? I will see. She kept the catalogue of tides current."])
    first.append(["Interviewer", "00:00:40", "Who kept it?"])
    first.append([name, "00:00:47", "Dr McKee kept the log, and a second sleepless watch."])
    source = folder / "Source" / f"{name} - interview.xlsx"
    raw.save(source)
    book = wb_mod.create_from_source(source, folder / f"{name} - EN & ES.xlsx")
    wb = openpyxl.load_workbook(book, rich_text=True)
    ws = wb["Initial"]
    cols = wb_mod.detect_columns(ws)
    ws.cell(3, cols["es"]).value = "A cat on the rail"
    ws.cell(5, cols["es"]).value = "Catching the tide"
    wb.save(book)
    return book


def js_function(src: str, name: str) -> str:
    """A function of the page's script whole, async or not, or "" when there is none."""
    at = src.find(f"function {name}(")
    if at < 0:
        return ""
    head = "async " if src[max(0, at - 6):at] == "async " else ""
    return head + src[at:src.index("\n}", at) + 2]


def js_line(src: str, start: str) -> str:
    return next((ln for ln in src.splitlines() if ln.startswith(start)), "")


def test_search_modifiers(scratch: Path):
    print("\n329. Search's Whole word and Match case: the engine with each tick, a part-word, a quoted phrase, case, "
          "accents and the other forms, the route, the command line and MCP taking the same two options, the page's "
          "marks beside the server's (6 November)")
    import app_search as eng
    import cli
    import idiograph_find
    import mcp_server
    import server as server_mod

    def found(text, q, whole=False, case=False) -> bool:
        """Whether one text is a hit for what was typed, a phrase narrowing it as the finders narrow theirs."""
        _q, words, phrase = eng.query(q, whole, case)
        return eng.hit({"f": eng.fold(text), "text": text}, words) and (not phrase or eng.phrase_in(text, phrase))

    def marks(text, q, whole=False, case=False) -> str:
        return eng.marked(text, eng.query(q, whole, case)[1])

    # ── A. the engine on texts, each tick on its own
    check("329: the engine, asked for no tick, finds a word typed inside a longer one as ever, cat in catch, catalogue "
          "and Catching, and a request's default is Whole word on and Match case off, Whole word off only when it says "
          "false and Match case on only when it says true",
          all(found(t, "cat") for t in ("We would catch the boat", "the catalogue of tides", "Catching the tide",
                                          "the ferry cat", "two cats"))
          and eng.options({}) == (True, False) and eng.options({"whole_word": False}) == (False, False)
          and eng.options({"whole_word": 0, "match_case": 1}) == (True, False)
          and eng.options({"whole_word": "false", "match_case": "true"}) == (True, False)
          and eng.options({"match_case": True}) == (True, True) and eng.options(None) == (True, False)
          and eng.options({"whole_word": False, "match_case": True}) == (False, True))
    check("329: Whole word finds cat and cats and never catch, catalogue or Catching, a letter or a digit beside the word "
          "ruling the place out and a stop, a comma or an apostrophe not",
          found("the ferry cat", "cat", whole=True) and found("two cats", "cat", whole=True)
          and found("the cat's coat", "cat", whole=True) and found("Cat, then dog", "cat", whole=True)
          and not any(found(t, "cat", whole=True) for t in ("We would catch the boat", "the catalogue of tides",
                                                           "Catching the tide", "a cat2 label", "the bobcat")))
    check("329: Whole word keeps the word's other forms as whole words, sleep finding slept, sleeps and sleeping and "
          "never sleepless, and a form typed finding its plain one",
          all(found(t, "sleep", whole=True) for t in ("he slept", "she sleeps", "no sleeping here", "a sleep"))
          and not found("a sleepless night", "sleep", whole=True) and found("a sleepless night", "sleep")
          and found("the cat", "cats", whole=True) and not found("a catalogue", "cats", whole=True))
    check("329: Whole word takes a word at its edges as Find and replace does, so cannot never finds inside also and "
          "so is found in so, and So",
          not found("also here", "so", whole=True) and not found("a sofa", "so", whole=True)
          and found("so, then", "so", whole=True) and found("So then", "so", whole=True))
    check("329: a phrase in quotation marks is found anywhere as typed, and under Whole word only where it starts and ends "
          "on word edges",
          found("and the cat slept", '"the cat"') and found("the catalogue of tides", '"the cat"')
          and found("and the cat slept", '"the cat"', whole=True) and not found("the catalogue of tides", '"the cat"', whole=True)
          and not found("bathe cat", '"the cat"', whole=True) and found("bathe cat", '"the cat"'))
    check("329: Match case finds the word in the case typed, Will never finding will and will never finding Will, and "
          "with no Match case both are found",
          found("Will wrote in it", "Will", case=True) and not found("I will see", "Will", case=True)
          and found("I will see", "will", case=True) and not found("Will wrote in it", "will", case=True)
          and found("I will see", "Will") and found("Will wrote in it", "will"))
    check("329: Match case sets accents aside still, cafe finding café and Cafe finding Café, and not the other way "
          "round in case",
          found("the café", "cafe", case=True) and found("The Café", "Cafe", case=True)
          and not found("the café", "Cafe", case=True) and not found("The Café", "cafe", case=True))
    check("329: under Match case the other forms keep the case the word was typed in, sleep finding slept and sleeps and "
          "never Slept, Sleep finding Slept and Sleeps and never slept, SLEEP finding SLEPT",
          all(found(t, "sleep", case=True) for t in ("he slept", "she sleeps"))
          and not found("Slept badly", "sleep", case=True)
          and all(found(t, "Sleep", case=True) for t in ("Slept badly", "Sleeps late", "Sleep well"))
          and not found("he slept", "Sleep", case=True) and found("SLEPT", "SLEEP", case=True)
          and not found("Slept", "SLEEP", case=True))
    check("329: a word of mixed case under Match case is found as typed and has no other forms, McKee finding McKee and "
          "never Mckee, mckee or McKees",
          found("Dr McKee", "McKee", case=True) and not found("Dr Mckee", "McKee", case=True)
          and not found("Dr McKee", "mckee", case=True) and not found("the McKees", "McKee", case=True, whole=True)
          and not eng.words_of("McKee", case=True)[0].forms and eng.words_of("Sleep", case=True)[0].forms
          and found("Dr McKee", "mckee"))
    check("329: both ticks together find the word whole and in the case typed, with its forms in that case",
          found("Cat, then dog", "Cat", whole=True, case=True) and not found("cat, then dog", "Cat", whole=True, case=True)
          and not found("Catching it", "Cat", whole=True, case=True) and found("Cats came", "Cat", whole=True, case=True)
          and not found("cats came", "Cat", whole=True, case=True))
    # the words and the modifiers they were read under
    _q, ws, ph = eng.query('"the cat"', True, True)
    _q, plain_ws, plain_ph = eng.query("the cat")
    check("329: the words and the phrase carry the modifiers they were typed under, and a search with none carries none",
          ws.whole and ws.case and ph.whole and ph.case and str(ph) == "the cat"
          and not plain_ws.whole and not plain_ws.case and plain_ph == "" and not eng.query("cat")[1].loose
          and eng.query("cat", False, True)[1].loose is not None)

    # ── B. the marks in a hit, as an agent's snippet gives them and as a long text is cut
    check("329: the marks follow the rules, Whole word marking cat and cats and not the cat in catch, and Match case "
          "marking the capital Will alone",
          marks("a cat, catch and cats", "cat", whole=True) == "a **cat**, catch and **cats**"
          and marks("a cat, catch and cats", "cat") == "a **cat**, **cat**ch and **cats**"
          and marks("Will wrote it. I will see.", "Will", case=True) == "**Will** wrote it. I will see."
          and marks("Will wrote it. I will see.", "will", case=True) == "Will wrote it. I **will** see."
          and marks("a café, a Café", "cafe", case=True) == "a **café**, a Café"
          and marks("he slept, Slept", "Sleep", case=True) == "he slept, **Slept**", marks("a cat, catch and cats", "cat", whole=True))
    long_text = "We catch " + "filler " * 60 + "the cat sat on the rail " + "after " * 60
    plain_cut = eng.snippet(long_text, eng.query("cat")[1])
    whole_cut = eng.snippet(long_text, eng.query("cat", True)[1])
    check("329: a long text is cut round the first place the word is found by the rule in force, catch at its head with "
          "no tick and the cat further on under Whole word",
          plain_cut.startswith("We catch") and "the cat sat" not in plain_cut
          and "the cat sat" in whole_cut and not whole_cut.startswith("We catch"), whole_cut[:80])
    # a record Sift searches on its ID with its title, where the folded text is made of more than the title
    record = eng.item("record", "Cats of the harbour", "R12 · Title", {}, (0, 0))
    record["s"] = "R12 Cats of the harbour"
    record["f"] = eng.fold(record["s"])
    check("329: an item searched on more than its text, a record's ID with its title, is read as written under Match case",
          eng.hit(record, eng.query("R12", False, True)[1]) and not eng.hit(record, eng.query("r12", False, True)[1])
          and eng.hit(record, eng.query("r12")[1]) and eng.hit(record, eng.query("Cats", False, True)[1])
          and not eng.hit(record, eng.query("cats", False, True)[1]) and eng.hit(record, eng.query("cats", True)[1]),
          str(record))

    # ── C. an invented project, the route
    base = scratch / "search-modifiers-329"
    shutil.rmtree(base, ignore_errors=True)
    root = base / "Ferry crossing"
    book = make_workbook(root, "Haddie")
    (root / server_mod.PROJECT_FILE).write_text(json.dumps({
        "name": "Ferry crossing", "research_question": "What does the early boat come to mean?",
        "agents": {"allowed": True, "at": "2026-11-06T10:00:00+00:00"}}), encoding="utf-8")
    config_file = base / "config.json"
    config_file.write_text(json.dumps({"root": str(root), "interviewer": "Interviewer", "projects": [], "corpus": "",
                                       "gravity_reference": "", "corpus_exclude": []}), encoding="utf-8")
    saved = (server_mod.ROOT_OVERRIDE, server_mod.STATE_MEMORY)
    server_mod.ROOT_OVERRIDE = str(root)
    server_mod.STATE_MEMORY = {"recent": []}
    eng.HELD.clear()
    try:
        def ask(q, scope="case", **more):
            return server_mod.api_search(dict({"q": q, "scope": scope, "path": str(book)}, **more))

        def kinds_of(got):
            return sorted(r["kind"] for r in got["results"])

        # a request that names neither tick is Whole word on, Match case off, as the card opens
        default_hits, whole_hits = ask("cat"), ask("cat", whole_word=True, match_case=False)
        part_hits = ask("cat", whole_word=False)
        case_hits, capital_hits = ask("cat", whole_word=False, match_case=True), ask("Cat", whole_word=False, match_case=True)
        both_hits = ask("cat", match_case=True)
        check("329: a request that says nothing of the ticks is Whole word on and Match case off, the passages and the "
              "statement that hold cat found and Catching the tide not, the same as with Whole word asked for, and the "
              "answer says how it read the words",
              default_hits["total"] == 3 and kinds_of(default_hits) == ["passage", "passage", "statement"]
              and default_hits["whole_word"] is True and default_hits["match_case"] is False and "cats" in default_hits["forms"]
              and json.dumps(default_hits["results"]) == json.dumps(whole_hits["results"]),
              str([r["text"][:30] for r in default_hits["results"]]))
        check("329: Whole word false finds cat in all four places as before, two passages and two statements, the inside "
              "of Catching included",
              part_hits["total"] == 4 and kinds_of(part_hits) == ["passage", "passage", "statement", "statement"]
              and part_hits["whole_word"] is False and part_hits["match_case"] is False, str(part_hits["total"]))
        check("329: Match case finds cat in lower case alone, so the statement Catching the tide is dropped, and Cat only "
              "where the capital stands, in Catching, each with Whole word false so a part-word is in reach",
              case_hits["total"] == 3 and case_hits["match_case"] is True and case_hits["whole_word"] is False
              and kinds_of(case_hits) == ["passage", "passage", "statement"]
              and [r["text"] for r in case_hits["results"] if r["kind"] == "statement"] == ["A cat on the rail"]
              and capital_hits["total"] == 2 and kinds_of(capital_hits) == ["passage", "statement"]
              and [r["text"] for r in capital_hits["results"] if r["kind"] == "statement"] == ["Catching the tide"],
              str([r["text"][:30] for r in capital_hits["results"]]))
        check("329: both ticks together give the whole lower-case word, Cat under them finding none of Catching, and the "
              "counts by kind are those of the hits kept",
              both_hits["total"] == 3 and both_hits["counts"]["passage"] == 2 and both_hits["counts"]["statement"] == 1
              and both_hits["whole_word"] and both_hits["match_case"] and part_hits["counts"]["statement"] == 2
              and ask("Cat", match_case=True)["total"] == 0)
        phrase_part, phrase_whole = ask('"the cat"', whole_word=False), ask('"the cat"')
        stem_part, stem_whole = ask("sleep", whole_word=False), ask("sleep")
        check("329: a quoted phrase and a word's forms through the route, the cat in the catalogue and sleepless found "
              "with Whole word false and dropped by the default, slept and sleeps kept",
              phrase_part["total"] == 2 and phrase_whole["total"] == 1 and stem_part["total"] == 2 and stem_whole["total"] == 1
              and stem_whole["results"][0]["text"].startswith("The ferry cat"))
        project_whole = server_mod.api_search({"q": "cat", "scope": "project", "root": str(root)})
        will_hits, will_lower = ask("Will", match_case=True), ask("will", match_case=True)
        check("329: This project and the passages' marks agree, the answer's text the place the word stands and Will found "
              "only where the capital stands",
              project_whole["total"] == 3 and project_whole["whole_word"] is True
              and will_hits["total"] == 1 and will_lower["total"] == 1
              and eng.marked(will_hits["results"][0]["text"], eng.query("Will", False, True)[1]).count("**") == 4
              and eng.marked(will_lower["results"][0]["text"], eng.query("will", False, True)[1]).count("**") == 2)
        mine = [r for r in server_mod.SEARCH_ROWS["idiograph"]() if r["name"] == "Ferry crossing"]
        every = eng.search_all("cat", whole=True, distil=mine)
        every_plain = eng.search_all("cat", distil=mine)
        every_case = eng.search_all("Cat", match_case=True, distil=mine)
        check("329: Everything takes the two options as well, its answer saying so, the project's hits those of the ticks",
              every["total"] == 3 and every_plain["total"] == 4 and every_case["total"] == 2
              and every["whole_word"] is True and every_case["match_case"] is True and every_plain["whole_word"] is False)
        with support.as_app("idiograph"):
            wide_default = server_mod.api_search({"q": "cat", "scope": "all", "app": "idiograph"})
            wide_part = server_mod.api_search({"q": "cat", "scope": "all", "app": "idiograph", "whole_word": False})

        def ferry(got):
            return next((p["count"] for p in got["projects"] if p["name"] == "Ferry crossing"), None)
        check("329: Everything through the route is Whole word on unless the request says false, three hits in the ferry "
              "project and four with it false",
              wide_default["whole_word"] is True and ferry(wide_default) == 3 and wide_part["whole_word"] is False
              and ferry(wide_part) == 4, str([ferry(wide_default), ferry(wide_part)]))

        # ── D. the command line
        def run(*args):
            return cli.run(["--root", str(root), "--config", str(config_file), "--json", *args])

        def answer(*args):
            code, out, err = run(*args)
            return code, (support.plain(json.loads(out)) if out.strip() and code == 0 else {}), err

        code, c_default, err = answer("search", "cat")
        _, c_whole, _ = answer("search", "cat", "--whole-word")
        _, c_part, _ = answer("search", "cat", "--no-whole-word")
        _, c_case, _ = answer("search", "Cat", "--no-whole-word", "--match-case")
        _, c_both, _ = answer("search", "cat", "--match-case", "--kinds", "passages")
        _, c_phrase, _ = answer("search", '"the cat"')
        snippets = [r["snippet"] for r in c_default.get("results", [])]
        check("329: the command line's search is Whole word on and Match case off when it is given neither, --no-whole-word "
              "turning Whole word off and --match-case Match case on, the answer saying which were on",
              code == 0 and c_default["total"] == 3 and c_whole["total"] == 3 and c_part["total"] == 4 and c_case["total"] == 2
              and c_default["whole_word"] is True and c_default["match_case"] is False
              and c_whole["whole_word"] is True and c_part["whole_word"] is False and c_part["match_case"] is False
              and c_case["match_case"] is True and c_case["whole_word"] is False
              and c_both["total"] == 2 and c_both["whole_word"] and c_both["match_case"] and c_phrase["total"] == 1,
              err or json.dumps([c_default.get("total"), c_whole.get("total"), c_part.get("total"), c_case.get("total")]))
        check("329: the command line's snippets mark the words by the same rules, no asterisks round the cat of catch by "
              "default and the cat of catch marked under --no-whole-word",
              snippets and all("**cat**ch" not in s and "**Cat**ching" not in s for s in snippets)
              and any("**cat**" in s for s in snippets) and any("**Cat**ching" in r["snippet"] for r in c_part["results"]),
              str(snippets)[:300])
        code, plain_text, _ = cli.run(["--root", str(root), "--config", str(config_file), "search", "cat"])
        check("329: the plain-text answer of a search with no option lists the three hits Whole word leaves",
              code == 0 and plain_text.splitlines()[0].startswith("3 hits"), plain_text[:200])
        # a participant's pseudonym stays --case, the ticks being --whole-word and --match-case
        _, c_one, _ = answer("search", "cat", "--case", "Haddie")
        parser = cli.parser()
        sub = next(a for a in parser._actions if isinstance(a, argparse._SubParsersAction)).choices["search"]
        flags = {s for a in sub._actions for s in a.option_strings}
        sift_parser = cli.parser("sift", search=True)
        on = sift_parser.parse_args(["search", "pond", "--folder", str(base)])
        both = sift_parser.parse_args(["search", "pond", "--folder", str(base), "--no-whole-word", "--match-case"])
        check("329: --case is still a participant, --whole-word, --no-whole-word and --match-case are flags of search, Whole "
              "word on and Match case off when left out, and Sift's and Trace's search by folder take them too",
              c_one["total"] == 3 and {"--whole-word", "--no-whole-word", "--match-case", "--case"} <= flags
              and on.whole_word is True and on.match_case is False
              and both.whole_word is False and both.match_case is True, str(sorted(flags)))

        # ── E. MCP
        tools = {t["name"]: t for t in mcp_server.Server(str(root), config=str(config_file)).receive(json.dumps(
            {"jsonrpc": "2.0", "id": 1, "method": "tools/list"}))["result"]["tools"]}
        props = tools["search"]["inputSchema"]["properties"]
        srv = mcp_server.Server(str(root), config=str(config_file))

        def call(**given):
            return srv.receive(json.dumps({"jsonrpc": "2.0", "id": 2, "method": "tools/call",
                                           "params": {"name": "search", "arguments": given}}))["result"]

        m_default, m_whole = call(words="cat"), call(words="cat", whole_word=True)
        m_part = call(words="cat", whole_word=False)
        m_case, m_off = call(words="Cat", whole_word=False, match_case=True), call(words="cat", whole_word="yes", match_case=1)
        check("329: MCP's search takes whole_word and match_case as booleans, Whole word true and Match case false when left "
              "out, whole_word false finding the part-word, a word or a number in their place refused with nothing "
              "searched, and answers as the command line does",
              props["whole_word"]["type"] == "boolean" and props["match_case"]["type"] == "boolean"
              and "whole_word" not in tools["search"]["inputSchema"].get("required", [])
              and not m_default["isError"] and m_default["structuredContent"]["total"] == 3
              and m_default["structuredContent"]["whole_word"] is True and m_default["structuredContent"]["match_case"] is False
              and m_whole["structuredContent"]["total"] == 3 and m_part["structuredContent"]["total"] == 4
              and m_part["structuredContent"]["whole_word"] is False
              and m_case["structuredContent"]["total"] == 2 and m_case["structuredContent"]["match_case"] is True
              and m_off["isError"] and "true or false" in m_off["content"][0]["text"] and "results" not in m_off["structuredContent"],
              json.dumps([m_default.get("isError"), props.get("whole_word")])[:300])
        # the card's keys are the tool's and the command line's: the parity of the page with the agents' two ways
        sjs = support.text("family/static/search.js")
        sent = re.findall(r"(\w+): !!\$\('search-(?:word|case)'\)\.checked", js_function(sjs, "searchOptions") or js_line(
            sjs, "const searchOptions"))
        own = [mcp_server.own_search("sift", "x", "y", "z")["inputSchema"]["properties"],
               mcp_server.own_search("trace", "x", "y", "z")["inputSchema"]["properties"]]
        check("329: every key the card sends for its two ticks is a property of MCP's search, of Sift's and of Trace's, and a "
              "flag of the command line's, so an agent can do what the card does",
              sorted(sent) == ["match_case", "whole_word"] and all(k in props for k in sent) and all(k in p for k in sent for p in own)
              and all("--" + k.replace("_", "-") in flags for k in sent), str(sent))
    finally:
        server_mod.ROOT_OVERRIDE, server_mod.STATE_MEMORY = saved
        eng.HELD.clear()

    # ── F. the page: the ticks, the marks beside the server's
    html = support.text("family/static/page.html")
    mods = re.search(r'<div class="search-mods">(.*?)</div>', html, re.S)
    ticks = re.findall(r'<label class="search-mod"><input type="checkbox" id="(search-word|search-case)"( checked)?> \{\{([\w.]+)\}\}</label>',
                       mods.group(1) if mods else "")
    open_close = js_function(sjs, "openSearch") + js_function(sjs, "closeSearch")
    family = json.loads(support.text("family/static/i18n/en/page.json"))
    idiograph = json.loads(support.text("apps/idiograph/static/i18n/en/page_idiograph.json"))
    check("329: the card has Whole word and Match case as two ticks, each inside its label so the whole row ticks, Whole "
          "word ticked as the card first shows and Match case not, neither touched when the card opens or closes so they "
          "keep between openings as Find and replace's do, and in Find and replace's own words",
          [t[0] for t in ticks] == ["search-word", "search-case"] and [bool(t[1]) for t in ticks] == [True, False]
          and "search-word" not in open_close
          and "search-case" not in open_close
          and family.get("page.search.whole_word") == idiograph["page_idiograph.work.whole_word"]
          and family.get("page.search.match_case") == idiograph["page_idiograph.work.match_case"], str(ticks))
    node = shutil.which("node")
    if not node:
        skip("329: the page's marks in node", "node is not on this machine")
        return
    # texts the page and the server both mark, each with the forms the server's answer hands the page
    texts = [("a cat, catch and cats", "cat", {}), ("a cat, catch and cats", "cat", {"whole_word": True}),
             ("Will wrote it. I will see.", "Will", {"match_case": True}), ("Will wrote it. I will see.", "will", {"match_case": True}),
             ("a café, a Café", "cafe", {"match_case": True}), ("he slept, Slept", "Sleep", {"match_case": True}),
             ("he slept, Slept", "sleep", {"match_case": True}), ("also so, So", "so", {"whole_word": True}),
             ("cat2 cat", "cat", {"whole_word": True}), ("and the cat, the catalogue", '"the cat"', {"whole_word": True}),
             ("Cat, cat, Catching, Cats", "Cat", {"whole_word": True, "match_case": True}),
             ("sleepless, slept, sleeps", "sleep", {"whole_word": True}), ("Dr McKee, Dr Mckee", "McKee", {"match_case": True}),
             ("a cat", "cat", {})]
    cases = []
    server_marks = []
    for text, q, opts in texts:
        _q, words, _p = eng.query(q, opts.get("whole_word", False), opts.get("match_case", False))
        cases.append({"text": text, "q": q, "forms": eng.forms_said(words), "opts": opts})
        server_marks.append(eng.marked(text, words))
    app = support.text("family/static/shell.js", "apps/idiograph/static/distil.js")
    code = "\n".join([js_line(app, "const esc = "), js_line(sjs, "const searchPlain = "), js_line(sjs, "const searchFold = "),
                      js_line(sjs, "const SEARCH_ALNUM = "), js_function(sjs, "searchMarked")]) + "\nconst CASES = " + json.dumps(cases) + r""";
const mark = (c) => searchMarked(c.text, c.q, c.forms, c.opts).replace(/<mark class="search-mark">/g, '**').replace(/<\/mark>/g, '**');
console.log(JSON.stringify(CASES.map(mark)));
"""
    script = scratch / "search-modifiers-329.js"
    script.write_text(code, encoding="utf-8")
    run_ = subprocess.run([node, str(script)], capture_output=True, text=True, encoding="utf-8", timeout=60)
    page_marks = json.loads(run_.stdout) if run_.returncode == 0 and run_.stdout.strip() else []
    check("329: in node, the page marks the same places as the server's snippet does in each of those texts, the forms "
          "the answer hands it in the case typed, the places that touch marked as one",
          page_marks == server_marks and len(page_marks) == len(texts), run_.stderr[:300] + str(list(zip(page_marks, server_marks))))
    check("329: and those places are the rules' own, cat and cats and not catch under Whole word, the capital Will alone "
          "under Match case, an accent set aside, a form in the case typed, a digit or a letter beside the word ruling it out",
          server_marks[0] == "a **cat**, **cat**ch and **cats**" and server_marks[1] == "a **cat**, catch and **cats**"
          and server_marks[2] == "**Will** wrote it. I will see." and server_marks[3] == "Will wrote it. I **will** see."
          and server_marks[4] == "a **café**, a Café" and server_marks[5] == "he slept, **Slept**"
          and server_marks[6] == "he **slept**, Slept" and server_marks[7] == "also **so**, **So**"
          and server_marks[8] == "cat2 **cat**" and server_marks[9] == "and **the** **cat**, **the** catalogue"
          and server_marks[10] == "**Cat**, cat, Catching, **Cats**" and server_marks[11] == "sleepless, **slept**, **sleeps**"
          and server_marks[12] == "Dr **McKee**, Dr Mckee" and server_marks[13] == "a **cat**", str(server_marks))
