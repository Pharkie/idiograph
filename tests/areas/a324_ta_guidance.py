"""Area 324: a thematic analysis project's own guidance on screen (tarail, 3 November 2026, Adam's "ta guidance
reviewed and approved" that afternoon). The Coding screen's rail reads ta_guidance.md, its lines, their examples, the
framing under them and the craft prompts, beside IPA's from guidance.md, and the Themes board's Guidance tab reads
ta_themes_guidance.md where an IPA project's GETs board reads the GETs sections of pet_guidance.md. The page picks
the one of the project in front. The projects are scratch copies of the demo, its invented topic."""
from __future__ import annotations

import json
from pathlib import Path

from . import support
from .support import check, demo_copy

TA_HEADS = ["What a theme is", "Generating themes", "Developing and reviewing", "Defining and naming",
            "The thematic map", "Before you finish"]

HARNESS = r"""
const out = {};
TH.mode = 'gets';
TH.ai = { on: true };
TH.project = { method: 'ta' };
TH.guidanceTa = true;
out.taTabs = thTabsOf('gets');
TH.guidanceTa = false;
out.taOldServer = thTabsOf('gets');
TH.project = { method: 'ipa' };
out.ipaTabs = thTabsOf('gets');
// the tab buttons as thTabsDraw leaves them, AI features on, in each method
const buttons = ['inspector', 'guidance', 'history', 'review', 'revise'].map((tab) => ({ dataset: { tab }, hidden: false,
  classList: { toggle() {} }, setAttribute() {} }));
globalThis.document = { querySelectorAll: () => buttons };
const shown = () => buttons.filter((b) => !b.hidden).map((b) => b.dataset.tab);
TH.tab = 'inspector';
thTabsDraw();
out.ipaDrawn = shown();
TH.project = { method: 'ta' };
TH.guidanceTa = true;
thTabsDraw();
out.taDrawn = shown();
console.log(JSON.stringify(out));
"""


def test_ta_guidance(scratch: Path):
    print("\n324. A thematic analysis project's guidance: the Coding rail from ta_guidance.md and the Themes board's "
          "Guidance tab from ta_themes_guidance.md, an IPA project's as before")
    import app_identity
    import i18n
    import idiograph_routes as routes
    import server as server_mod
    import themes_ai

    # ── A. the rail: IPA's as guidance.md has it, and a TA project's from its own file in the same shape
    rail = routes.api_guidance({})
    ta = rail.get("ta") or {}
    ta_file = support.source("apps/idiograph/ta_guidance.md")
    check("324: the rail's IPA lines, examples, framing and prompts are guidance.md's, as before",
          rail["lines"] == routes.guidance_lines() and rail["examples"] == routes.guidance_examples()
          and rail["framing"] == routes.guidance_framing() and rail["prompts"] == routes.placeholder_prompts()
          and rail["lines"] != ta.get("lines"))
    check("324: a TA project's rail is ta_guidance.md's eleven lines, each with its two examples, the framing and "
          "seven craft prompts",
          len(ta.get("lines") or []) == 11 and all(ta.get("examples") or [None])
          and len(ta.get("examples") or []) == 11
          and ta.get("lines", [""])[0].startswith("Read the whole dataset before you code")
          and ta.get("examples", [{}])[9] == {"less": "One pass, in interview order",
                                              "more": "A second pass, from the last participant to the first"}
          and ta.get("framing", "").startswith("1 to 3 are about the whole dataset")
          and "A codebook approach" in ta.get("framing", "") and len(ta.get("prompts") or []) == 7
          and not set(ta.get("prompts") or []) & set(ta.get("lines") or []), str(ta)[:400])
    check("324: both TA files ship with the app",
          {"ta_guidance.md", "ta_themes_guidance.md"} <= set(app_identity.FILES["idiograph"])
          and ta_file.exists() and support.source("apps/idiograph/ta_themes_guidance.md").exists())

    # ── B. the Themes board's Guidance tab: a TA project's from its file, an IPA project's GETs lines as before
    base = scratch / "ta-guidance-324"
    roots = {"ta": base / "Dogs", "ipa": base / "Dogs IPA"}
    books = {}
    for method, root in roots.items():
        books[method] = demo_copy(root, "Juno", "Juno - EN & ES.xlsx")
        (root / "idiograph-project.json").write_text(json.dumps({"name": f"A home with a dog ({method})",
                                                                 "method": method}), encoding="utf-8")
    config_file = base / "config.json"
    config_file.write_text(json.dumps({"projects": [{"root": str(r)} for r in roots.values()], "interviewer": "Adam",
                                       "corpus": "", "gravity_reference": "", "corpus_exclude": []}), encoding="utf-8")
    kept = (server_mod.CONFIG_PATH, server_mod.ROOT_OVERRIDE, server_mod.STATE_MEMORY)

    def gets(method):
        server_mod.CONFIG_PATH, server_mod.ROOT_OVERRIDE, server_mod.STATE_MEMORY = config_file, None, {"recent": []}
        body = {"workbook": str(books[method])}
        try:
            with server_mod.scoped("/api/gets", body):
                return server_mod.ROUTES["/api/gets"](body)
        finally:
            server_mod.CONFIG_PATH, server_mod.ROOT_OVERRIDE, server_mod.STATE_MEMORY = kept

    got_ta, got_ipa = gets("ta"), gets("ipa")
    check("324: a TA project's Themes board carries ta_themes_guidance.md's six sections, in its order, and says so",
          [s["heading"] for s in got_ta.get("guidance") or []] == TA_HEADS and got_ta.get("guidance_ta") is True
          and got_ta["guidance"] == routes.themes_guidance(i18n.long_text(routes.TA_THEMES_GUIDANCE))
          and got_ta["guidance"][0]["lines"][0].startswith("A theme is a pattern of shared meaning"),
          str([s.get("heading") for s in got_ta.get("guidance") or []]))
    check("324: an IPA project's GETs board carries the GETs sections of pet_guidance.md, as before",
          got_ipa.get("guidance") == themes_ai.gets_guidance_lines() and got_ipa.get("guidance_ta") is False
          and got_ipa["guidance"] and got_ipa["guidance"] != got_ta["guidance"])

    # ── C. the page: the Guidance tab shows in a TA project when its lines came, and on IPA's board as before
    support.node_text_layer(scratch)
    js = support.text("apps/idiograph/static/themes.js")
    stubs = ("const $ = () => null; const say = () => {}; const api = async () => ({});\n"
             "const tList = (xs) => xs.join(', ');\n")
    run = support.run_node(stubs + js + HARNESS, scratch, "ta-guidance-324.js", timeout=60)
    try:
        out = json.loads(run.stdout.strip().splitlines()[-1])
    except (ValueError, IndexError):
        out = {}
    why = (run.stdout + run.stderr)[-600:]
    check("324: a TA project's Themes board has the Guidance tab, and an IPA project's keeps it",
          "guidance" in (out.get("taTabs") or []) and "guidance" in (out.get("ipaTabs") or []), why)
    check("324: from a server before it, sending no TA lines, a TA project's board leaves the tab out, as before",
          "guidance" not in (out.get("taOldServer") or ["guidance"]), why)
    # its own AI review since taaibuild, and still no AI revise (area 326)
    check("324: with AI features on, a TA project's board shows its own AI review and hides AI revise, and an "
          "IPA project's board shows all five tabs",
          out.get("taDrawn") == ["inspector", "guidance", "history", "review"]
          and out.get("ipaDrawn") == ["inspector", "guidance", "history", "review", "revise"], why)
    opened = js.split("async function themesOpen(", 1)[1].split("\n}\n", 1)[0]
    method_at = opened.find("tMethod(TH.project && TH.project.method);")
    check("324: opening a board sets the AI's controls again once the project's method is known, so a TA board opened "
          "after an IPA screen shows none of the AI's buttons",
          method_at > 0 and "aiPage(TH.config);" in opened[method_at:])
    shell = support.text("family/static/shell.js")
    check("324: on the Coding screen IPA's AI suggestions and every IPA AI control stay away in a TA project",
          "if (typeof tMethodNow === 'function' && tMethodNow() === 'ta') return false;" in shell.split("function aiFor(", 1)[1][:400]
          and "document.body.classList.add('ai-off')" in shell.split("function aiPage(", 1)[1][:500])
