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
                    "First line of the framing,\nits second line.\n\n- Rule one.\n  - {less} Bees as a chore\n"
                    "  - {more} Tending as a quiet hour\n- Rule two.\n  - {less} only one side\n\n"
                    "## Placeholders {placeholders}\n\nAbout the prompts.\n\n* A prompt?\n  * {less} never read\n", encoding="utf-8")
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
    # read by markers, never by a language's words (langready, 21 November 2026): the same file in another language
    other = scratch / "guidance-231.zz.md"
    other.write_text("# Guia\n\nIntro.\n\n## Oficio\n\nPrimera linea del marco.\n\n- Regla uno.\n  - {less} Abejas como tarea\n"
                     "  - {more} Cuidar como una hora tranquila\n\n## Frases guia {placeholders}\n\n* Una pregunta?\n", encoding="utf-8")
    check("231: the rail, its examples, its framing and its prompts are found by their markers in a language that has none of "
          "the English words",
          idiograph_routes.guidance_lines(other) == ["Regla uno."]
          and idiograph_routes.guidance_examples(other) == [{"less": "Abejas como tarea", "more": "Cuidar como una hora tranquila"}]
          and idiograph_routes.guidance_framing(other) == "Primera linea del marco."
          and idiograph_routes.placeholder_prompts(other) == ["Una pregunta?"]
          and idiograph_routes.placeholder_prompts(made) == ["A prompt?"],
          str([idiograph_routes.guidance_lines(other), idiograph_routes.guidance_examples(other),
               idiograph_routes.placeholder_prompts(other)]))
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
