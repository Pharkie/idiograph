from __future__ import annotations

from . import support

from .support import check
import idiograph_routes


def test_ai_surface():
    print("\n23. One press, the buttons, the key in settings and the placeholder")
    import server as server_mod
    static = server_mod.HERE / "static"
    js = support.text("family/static/shell.js", "apps/idiograph/static/distil.js")

    check("the endpoint is /api/suggest, with the old name kept as an alias",
          "'/api/suggest'" in js
          and server_mod.ROUTES["/api/suggest"] is idiograph_routes.api_suggest
          and server_mod.ROUTES["/api/haiku"] is idiograph_routes.api_suggest)
    check("an existing config keeps the switch it had",
          server_mod.merge_config({"haiku": True})["ai_suggest"] is True
          and server_mod.merge_config({"haiku": True, "ai_suggest": False})["ai_suggest"] is False
          and server_mod.merge_config({})["ai_suggest"] is False,
          "the old key is the fallback for the new one, and never beats it")

    check("the page empties the field as soon as the value is on its way",
          "field.value = '';" in js.split("async function checkKey(", 1)[1].split("\n}", 1)[0],
          "nothing is left sitting in the page")

    check("the sections are read by their heading, so neither leaks into the other",
          "placeholder" in " ".join(idiograph_routes.guidance_sections()),
          ", ".join(h for h in idiograph_routes.guidance_sections() if h))
