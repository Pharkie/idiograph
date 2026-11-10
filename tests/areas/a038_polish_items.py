from __future__ import annotations

import inspect
import json
import re
from pathlib import Path

import ai_suggest as ai_mod
import corpus
import workbook as wb_mod

from . import support
from .support import CORPUS_MD, MAIN, PARTICIPANTS, STUDY_PSEUDONYMS, check, skip
import idiograph_routes


def words_of(text) -> str:
    """Lower case words and nothing else, so a phrase is found whatever the punctuation round it."""
    return " ".join(re.findall(r"[a-z0-9]+(?:'[a-z0-9]+)*", str(text).lower().replace("’", "'")))


def test_polish_items(scratch):
    print("\n38. The bench asks as the button does, the examples fall back to the demo, and nothing from the "
          "studies in the shipped folder (items 60 and 63)")
    import server as server_mod
    static = server_mod.HERE / "static"
    js = support.text("family/static/shell.js", "apps/idiograph/static/distil.js")
    readme = support.source("README.md").read_text(encoding="utf-8")
    manual = support.source("docs/manual.md").read_text(encoding="utf-8")
    internals = support.source("docs/internals.md").read_text(encoding="utf-8")
    docs = readme + manual + internals

    # ── 60. the bench is the real thing
    body_fn = js.split("function suggestBody(", 1)[1].split("\n}", 1)[0]
    asker = js.split("async function askAI(", 1)[1].split("\n}", 1)[0]
    runner = js.split("async function runBench(", 1)[1].split("\n}", 1)[0]
    extra = set(re.findall(r"body\.(\w+) =", runner))
    check("one function builds the body for the button and the bench: turn, prior, time, name, case",
          "const body = { turn, prior, time, name, path: S.data ? S.data.path : '' };" in body_fn
          and "return body;" in body_fn
          and "api('/api/suggest', suggestBody(row.text, before ? before.text : '', row.time, row.name," in asker
          and "suggestBody(text, $('bench-prior').value, S.bench.time, S.bench.name)" in runner
          and "api('/api/suggest-sample', body)" in runner)
    check("the bench adds only the panel's own choices to that body",
          extra == {"ai_prompt", "research_question"} and "aiTryBody(body);" in runner
          and set(re.findall(r"body\.(\w+) =", js.split("function aiTryBody(", 1)[1].split("\n}", 1)[0]))
          == {"provider", "model", "local_model", "ai_deployment", "lmstudio_url", "ai_address"}, ", ".join(sorted(extra)))

    real = (server_mod.CONFIG_PATH, ai_mod.find_key, ai_mod.http_call)
    sent = []

    def wire(method, url, headers, payload, timeout):
        sent.append(payload)
        body = {"tags": ["t"], "candidates": ["A candidate"]}
        return 200, json.dumps({"content": [{"type": "text", "text": json.dumps(body)}], "stop_reason": "end_turn"})

    shared = scratch / "polish-items"
    shared.mkdir(parents=True, exist_ok=True)
    try:
        server_mod.CONFIG_PATH = shared / "config.json"
        server_mod.CONFIG_PATH.write_text(json.dumps({"ai_suggest": True, "ai_provider": "anthropic"}), encoding="utf-8")
        ai_mod.find_key = lambda *a, **kw: "k-test"
        ai_mod.http_call = wire
        sample = idiograph_routes.api_suggest_sample({})
        fields = {"turn": sample["turn"], "prior": sample["prior"], "time": sample["time"], "name": sample["name"],
                  "path": str(server_mod.DEMO_WORKBOOK)}
        idiograph_routes.api_suggest(dict(fields))
        from_button = [p["messages"][0]["content"] for p in sent]
        sent.clear()
        answer = idiograph_routes.api_suggest_sample(dict(fields, provider="anthropic", model="claude-haiku-4-5"))
        from_bench = [p["messages"][0]["content"] for p in sent]
        check("the bench's request carries exactly what the button's does, pass for pass",
              len(from_button) == 2 and from_button == from_bench
              and sample["prior"] in from_bench[0] and f"at {sample['time']}" in from_bench[0]
              and f"{sample['name']}'s passage" in from_bench[0], answer.get("model_name", ""))
        sent.clear()
        old_page = idiograph_routes.api_suggest_sample({"text": f"Adam: {sample['prior']}\n{sample['name']}: {sample['turn']}",
                                                  "provider": "anthropic"})
        check("a page from before still gets its one box read", old_page.get("candidates") == ["A candidate"])

        # ── 63. the examples fall back to the demo, for the rail and the prompt alike
        demo_texts = {e["text"] for e in corpus.load_gravity(server_mod.DEMO_EXAMPLES)}
        server_mod.CONFIG_PATH.write_text(json.dumps({"ai_suggest": True, "corpus": "", "gravity_reference": ""}),
                                          encoding="utf-8")
        rail = idiograph_routes.api_examples({})["examples"]
        narrowed = idiograph_routes.api_examples({"gravity_only": True})["examples"]
        check("with no corpus and no reference set the rail shows the demo's own statements",
              len(rail) == 3 and all(e["text"] in demo_texts and e["pool"] == "demo" for e in rail)
              and len(narrowed) == 3 and all(e["text"] in demo_texts for e in narrowed)
              and server_mod.DEMO_EXAMPLES == server_mod.DEMO_DIR / "pristine" / server_mod.DEMO_WORKBOOK.name,
              " / ".join(e["text"] for e in rail))
        server_mod.CONFIG_PATH.write_text(json.dumps({"ai_suggest": True, "corpus": "nowhere/corpus.md",
                                                      "gravity_reference": "nowhere/P0 - Nobody*/x.xlsx"}),
                                          encoding="utf-8")
        check("so it does when the configured files are not on the machine",
              all(e["text"] in demo_texts for e in idiograph_routes.api_examples({})["examples"]))
        sent.clear()
        idiograph_routes.api_suggest({"turn": sample["turn"], "prior": sample["prior"], "path": str(server_mod.DEMO_WORKBOOK)})
        block = sent[0]["system"].split("as the register to match:\n", 1)[1].split("\n\n", 1)[0] if sent else ""
        lines = [ln[2:] for ln in block.splitlines() if ln.startswith("- ")]
        check("and the prompt's {examples} fills from the same source",
              len(lines) == 6 and all(ln in demo_texts for ln in lines), f"{len(lines)} lines")
        check("with no demo to fall back on there are no examples at all, never a hard-coded one",
              corpus.sample(None, None, 3) == [] and corpus.sample(Path("nowhere.md"), Path("nowhere.xlsx"), 3) == []
              and not any(t in src for t in demo_texts
                          for src in (inspect.getsource(corpus), inspect.getsource(server_mod), js)))
        defaults = server_mod.defaults()
        check("a shared copy's first run writes a config with no pool and no name in it",
              defaults["corpus"] == "" and defaults["gravity_reference"] == "" and defaults["corpus_exclude"] == []
              and "if not CONFIG_PATH.exists():\n        save_json(CONFIG_PATH, shipped_config())" in inspect.getsource(server_mod.start_up)
              and not any(name in json.dumps(defaults) for name in STUDY_PSEUDONYMS))
        server_mod.CONFIG_PATH = real[0]
        if server_mod.resolve_path(server_mod.saved_config().get("gravity_reference") or "nowhere").is_file():
            mine = idiograph_routes.api_examples({"gravity_only": True})["examples"]
            check("this install's own config still draws on its own reference set",
                  mine and all(e["pool"] == "gravity" for e in mine))
        else:
            skip("this install's own reference set", "no reference workbook on this machine")
    finally:
        server_mod.CONFIG_PATH, ai_mod.find_key, ai_mod.http_call = real

    # ── 63. nothing from the studies in the interface or the shipped folder
    # the page's own files, the vendored third-party ones in static/vendor/ (area 99) set aside
    audited = sorted(p for p in static.glob("*") if p.is_file()) + [support.source("family/ai_suggest.py"), support.source("apps/idiograph/themes_ai.py"), support.source("apps/idiograph/corpus.py"),
                                          support.source("apps/idiograph/guidance.md"), support.source("apps/idiograph/pet_guidance.md"), support.source("apps/idiograph/themes_print.py")]
    # the studies' pseudonyms come from the local gate file, so with none on this machine there is
    # nothing to look for
    if not STUDY_PSEUDONYMS:
        skip("no study pseudonym in the shipped files or the docs", "no local gate file naming them")
    else:
        named = [f"{path.name}: {name}" for path in audited for name in STUDY_PSEUDONYMS
                 if re.search(rf"\b{name}\b", path.read_text(encoding="utf-8"))]
        check("no study pseudonym in the static files, ai_suggest.py, themes_ai.py, corpus.py, guidance.md, "
              "pet_guidance.md or themes_print.py",
              not named, ", ".join(named) or f"{len(audited)} files, {len(STUDY_PSEUDONYMS)} names")
        in_readme = sorted({name for name in STUDY_PSEUDONYMS if re.search(rf"\b{name}\b", docs)})
        check("the README, the manual and the internals name no study pseudonym",
              in_readme == [], ", ".join(in_readme) or "none")
    shipped = {path.name: f" {words_of(path.read_text(encoding='utf-8'))} " for path in audited}
    statements, turns = [], []
    if CORPUS_MD.exists():
        statements += [m.group(1) for m in (re.match(r"^-\s+(.*\S)\s*$", line)
                                           for line in CORPUS_MD.read_text(encoding="utf-8").splitlines()) if m]
    workbooks = sorted(MAIN.glob("P* - */*- EN & ES.xlsx")) if MAIN.exists() else []
    for path in workbooks:
        case = wb_mod.read_case(path)
        for sheet in case["sheets"]:
            for row in sheet["rows"]:
                statements += [line for line in row["es"].splitlines() if line.strip()]
                turns.append(row["text"])
    transcripts = sorted(PARTICIPANTS.glob("*/*_T[1-3]_Transcript.csv")) if PARTICIPANTS.exists() else []
    for path in transcripts:
        with path.open(encoding="utf-8-sig", newline="") as handle:
            import csv
            rows_in = list(csv.reader(handle))
        turns += [" ".join(cells) for cells in rows_in[1:]]
    if not statements and not turns:
        skip("no participant's words in the shipped files", "no corpus, workbook or transcript on this machine")
    else:
        # each file's words split once, and its runs of four and of eight words as sets, so a statement is
        # looked for only in a file holding its first four words, and the transcripts' runs of eight are met
        # by one set each, where splitting each file again for every word took minutes (18 October)
        split = {name: body.split() for name, body in shipped.items()}
        fours = {name: {" ".join(w[i:i + 4]) for i in range(len(w) - 3)} for name, w in split.items()}
        eights = {name: {" ".join(w[i:i + 8]) for i in range(len(w) - 7)} for name, w in split.items()}
        said_of = [(text, words_of(text)) for text in statements]
        quoted = sorted({f"{name}: {text[:30]}" for text, said in said_of if len(said.split()) >= 4
                         for name, body in shipped.items()
                         if " ".join(said.split()[:4]) in fours[name] and f" {said} " in body})
        check("no statement from the corpus or a case workbook in those files", not quoted,
              ", ".join(quoted) or f"{len(statements)} statements checked")
        runs = set()
        for text in turns:
            said = words_of(text).split()
            runs.update(" ".join(said[i:i + 8]) for i in range(len(said) - 7))
        echoed = sorted(name for name, grams in eights.items() if grams & runs)
        check("no eight words running from a transcript in those files", not echoed,
              ", ".join(echoed) or f"{len(turns)} turns from {len(workbooks)} workbooks and {len(transcripts)} transcripts")
