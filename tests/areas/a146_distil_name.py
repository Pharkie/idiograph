from __future__ import annotations

from pathlib import Path

from . import support
from .support import check


def test_distil_name(scratch):
    print("\n146. Distil, 15 October, Adam's word: Analyse renamed Distil, to sit with Sift and Trace, the route from "
          "transcript to experiential statements to PETs to GETs, spelt with one l, its ids, keys, routes and files "
          "unchanged, the version 0.9.1, and Settings' fields kept clear of the scrollbar at 360. Since the test review "
          "of 18 October the name's words are review shots, and the ids, keys, routes and settings that every project "
          "and config.json open by stay")
    import server as server_mod

    read = lambda path: Path(path).read_text(encoding="utf-8")
    page, app = support.page_text(), support.text("family/static/shell.js", "apps/idiograph/static/distil.js")

    check("146, updated 15 October (149): the ids, the fold's key, the panes, the routes and the settings keep their "
          "names, so every project and config.json open as before, the panes' names in their order, formats after general, GETs, Export and Projects out of Settings since settingsplit (5 November)",
          all(f'id="{i}"' in page for i in ("home-analysis", "analysis-head", "analysis-body"))
          and "foldable($('home-analysis'), $('analysis-head'), 'analysis');" in app
          and "idiograph: ['general', 'formats', 'statements', 'pets', 'ai']," in app
          and not any("distil" in str(k).lower() for k in list(server_mod.ROUTES) + list(server_mod.defaults())))
