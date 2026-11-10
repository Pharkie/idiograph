from __future__ import annotations

import corpus

from .support import CORPUS_MD, REFERENCE_WORKBOOK, check, skip


def test_corpus():
    print("\n7. Examples panel")
    if not CORPUS_MD.exists():
        return skip("corpus", "no corpus markdown")
    whole = corpus.load_corpus(CORPUS_MD)
    # the source to leave out is the corpus's smallest, chosen here, never read from this machine's
    # config.json, which a downloaded copy and the gate's snapshot do not have (14 October)
    sizes = {}
    for item in whole:
        sizes[item["source"]] = sizes.get(item["source"], 0) + 1
    left_out = [min(sorted(sizes), key=sizes.get)] if sizes else []
    items = corpus.load_corpus(CORPUS_MD, left_out)
    check("corpus parses", 1400 < len(items) < 1600, f"{len(items)} statements, less what config leaves out")
    check("the sources config.json leaves out are left out, as the audit leaves them out",
          bool(left_out) and not any(x in i["source"] for i in items for x in left_out)
          and len(whole) > len(items), f"{len(whole) - len(items)} statements left out")
    if not REFERENCE_WORKBOOK.exists():
        skip("the GRAVITY anchor pool", "no reference workbook under Main Data")
    else:
        gravity = corpus.load_gravity(REFERENCE_WORKBOOK)
        check("the finished set loads as the GRAVITY anchor", len(gravity) > 100, f"{len(gravity)} statements")
        three = corpus.sample(CORPUS_MD, REFERENCE_WORKBOOK, 3, gravity_only=True)
        check("GRAVITY only draws from the anchor set",
              len(three) == 3 and all(t["pool"] == "gravity" for t in three))
    three = corpus.sample(CORPUS_MD, REFERENCE_WORKBOOK, 3)
    check("three of your own", len(three) == 3, " / ".join(t["text"][:34] for t in three))
