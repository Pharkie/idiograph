from __future__ import annotations

import nudges

from .support import check


def test_nudges():
    print("\n6. Nudges, from the audit checks")
    cases = [
        ("Cracking first, every morning", [], "one of the demo's own, four words"),
        ("She cracks first every morning and goes down to the dog", ["lead"], "She lead"),
        ("A house never empty, and a dog always at the door", [], "A opening is no lead flag"),
        ("The dog decides when the morning begins", [], "The opening is no lead flag"),
        ("He waits at the door until the dog is back", ["lead"], "He lead"),
        ("His mornings begin with the dog", ["lead"], "His lead"),
        ("They walk before the street wakes", ["lead"], "They lead"),
        ("Reads the barking as her fault and a shame to confess to the neighbours", ["readsas"], "reads-as"),
        ("Mornings hers; evenings the dog's", ["semicolon"], "semicolon"),
        ("Pulled down the stairs \u2014 by a lead", ["emdash"], "em dash"),
        ("Grief → grievance", ["arrow"], "arrow, two words and no minimum"),
        ("Understood she needs to 'let him be a dog'", ["quote"], "quoted fragment"),
    ]
    for text, expected, label in cases:
        flags = {f["check"] for f in nudges.check_statement(text)}
        check(f"{label}", set(expected) <= flags or (not expected and not flags),
              f"flags: {sorted(flags) or 'none'}")
    field = nudges.check_field("Softening before the day has properly started\nShe cracks first every morning")
    leads = [f["check"] for line in field for f in line["flags"] if f["check"] == "lead"]
    check("the field checks each line on its own",
          len(field) == 1 and field[0]["line"] == 1 and leads == ["lead"],
          f"{len(field)} flagged line, the second one")
