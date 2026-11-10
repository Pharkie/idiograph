"""Area 338: Whole word finds a typed word's own plural and singular, the command line's and MCP's answer says
what was asked, and Show in Finder on Windows hands Explorer its path as Explorer reads it (searchfix, 8 November
2026, after bugcheck found "feeling" missing "feelings" with Whole word on, an answer saying false when no project
answered, and a path with a space opening Explorer's default folder). The page, the API, the command line and MCP
all read their words through `app_search.query`, so the engine is checked with each tick on and off.

The fixtures are invented texts."""
from __future__ import annotations

from pathlib import Path

from .support import check


def test_search_forms_and_small_faults(scratch: Path):
    print("\n338. Whole word and an -ing noun's plural, the answer's own ticks, Explorer's select argument (8 November)")
    import app_search as eng
    import cli

    def found(text, q, whole=True, case=False) -> bool:
        _q, words, phrase = eng.query(q, whole, case)
        return eng.hit({"f": eng.fold(text), "text": text}, words) and (not phrase or eng.phrase_in(text, phrase))

    pairs = [("feeling", "feelings"), ("meaning", "meanings"), ("healing", "healings"),
             ("belonging", "belongings"), ("understanding", "understandings")]
    for case in (False, True):
        tag = "with Match case" if case else "without Match case"
        check(f"338: Whole word finds each -ing noun's plural and the plural finds the noun, {tag}",
              all(found(f"the {b} stayed", a, True, case) and found(f"the {a} stayed", b, True, case)
                  for a, b in pairs), str([p for p in pairs if not found(f"the {p[1]} stayed", p[0], True, case)]))
    check("338: Whole word still finds the word itself and its other forms, and cat never finds catch or catalogue",
          found("she feels it", "feeling") and found("they felt it", "feeling") and found("two cats", "cat")
          and found("a cat", "cats") and not found("we catch it", "cat") and not found("the catalogue", "cat")
          and not found("catches", "cat"), "")
    check("338: a word ending in y, in s or in ch takes its plural and gives it back",
          found("many cities", "city") and found("one city", "cities") and found("the boxes", "box")
          and found("one church", "churches") and found("two churches", "church"), "")
    check("338: with Whole word off the word is still found inside a longer one",
          found("we catch it", "cat", whole=False), "")

    # the command line's and MCP's answer says what was asked when no project answers
    said, _text = cli.search_said("feeling", "", "project", [], set(), 0, 10, None, [], True, False)
    check("338: an answer from no project says Whole word was asked and Match case was not",
          said["whole_word"] is True and said["match_case"] is False and said["total"] == 0, str(said)[:200])
    said, _text = cli.search_said("feeling", "", "project", [], set(), 0, 10, None, [], False, True)
    check("338: and the other way about", said["whole_word"] is False and said["match_case"] is True, str(said)[:200])

    # Show in Finder on Windows, the command that would run
    import server as server_mod
    import idiograph_routes as routes
    ran = []
    folder = Path("C:/Users/Ann Lee/Studies/Night fishing")
    real_run = server_mod.subprocess.run
    real_platform, real_srv = server_mod.PLATFORM, routes.srv.PLATFORM
    try:
        server_mod.subprocess.run = lambda *a, **k: ran.append(a[0])
        server_mod.PLATFORM = routes.srv.PLATFORM = "win32"
        server_mod.show_in_folder(folder)
        routes.show_folder(folder)
    finally:
        server_mod.subprocess.run = real_run
        server_mod.PLATFORM, routes.srv.PLATFORM = real_platform, real_srv
    want = f'explorer /select,"{folder}"'
    check("338: Explorer is given /select, and the quoted path as one command string, in both places that ask",
          ran == [want, want], str(ran))
