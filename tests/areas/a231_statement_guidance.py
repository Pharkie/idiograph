"""Area 231: the experiential statement guidance, Adam's revision of 20 October 2026 and its rewrite of 21
October. A colon after the phenomenon passes every nudge on a statement, while a semicolon still gets its
nudge. The panel's framing is the plain paragraph under the rail's heading in `guidance.md`, read beside its
lines and never mixed with them or with the placeholders. Each line's two examples, Less this and More this,
are the indented bullets under it, read in the lines' order and never taken for a line."""
from __future__ import annotations

from pathlib import Path

import nudges

from .support import check
import idiograph_routes


def test_statement_guidance(scratch: Path):
    print("\n231. The statement guidance, Adam's revision, with its examples")
    # invented statements on a made-up topic, beekeeping in a cold spring
    colons = ["Swarming: a welcome surprise", "Late frost: as unsettling as the swarm",
              "Smoke: a calm before the frames come out"]
    flagged = {s: [f["check"] for f in nudges.check_statement(s)] for s in colons}
    field = nudges.check_field("\n".join(colons))
    check("231: a colon after the phenomenon passes every nudge, statement by statement and in the field",
          all(not v for v in flagged.values()) and field == [], f"{flagged} {field}")
    semi = [f["check"] for f in nudges.check_statement("Swarming: a surprise; then a worry")]
    check("231: a semicolon in a statement with a colon still gets the semicolon nudge, and only that one",
          semi == ["semicolon"], str(semi))

    import server as server_mod
    made = scratch / "guidance-231.md"
    made.write_text("# Guidance rail\n\nAn intro the panel never shows.\n\n## Holding the craft\n\n"
                    "First line of the framing,\nits second line.\n\n- Rule one.\n  - Less this: Bees as a chore\n"
                    "  - More this: Tending as a quiet hour\n- Rule two.\n  - Less this: only one side\n\n"
                    "## Placeholders\n\nAbout the prompts.\n\n* A prompt?\n  * Less this: never read\n", encoding="utf-8")
    sections = idiograph_routes.guidance_sections(made)
    check("231: the framing is the prose under the rail's own heading, joined into one paragraph, apart from "
          "the file's intro, its lines, their examples and the placeholders' prose",
          idiograph_routes.guidance_framing(made) == "First line of the framing, its second line."
          and sections.get("holding the craft") == ["Rule one.", "Rule two."]
          and sections.get("placeholders") == ["A prompt?"], repr(idiograph_routes.guidance_framing(made)))
    check("231: each line's examples are the indented Less this and More this under it, in the lines' order, and a line "
          "without both has none",
          idiograph_routes.guidance_examples(made) == [{"less": "Bees as a chore", "more": "Tending as a quiet hour"}, None],
          str(idiograph_routes.guidance_examples(made)))
    check("231: a missing guidance file gives no framing and no examples",
          idiograph_routes.guidance_framing(scratch / "none-231.md") == "" and idiograph_routes.guidance_examples(scratch / "none-231.md") == [])
    lines, framing, prompts = idiograph_routes.guidance_lines(), idiograph_routes.guidance_framing(), idiograph_routes.placeholder_prompts()
    examples = idiograph_routes.guidance_examples()
    check("231: the app's own guidance.md gives eleven lines, a framing and a pair of examples for every line, none of "
          "them a placeholder",
          len(lines) == 11 and framing and not set(lines) & set(prompts) and framing not in lines
          and len(examples) == 11 and all(e and e["less"] and e["more"] for e in examples)
          and not {e["less"] for e in examples} & set(lines),
          f"{len(lines)} lines, {len(examples)} examples, framing {bool(framing)}")
    import inspect
    check("231: /api/guidance sends the examples beside the lines",
          idiograph_routes.api_guidance({})["examples"] == examples
          and '"examples": guidance_examples(path)' in inspect.getsource(idiograph_routes.rail_of))
