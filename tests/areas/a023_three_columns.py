from __future__ import annotations

from . import support
from .support import check


def test_three_columns():
    print("\n22. Three columns, the order of the fields and the way back to the rail")
    import server as server_mod
    static = server_mod.HERE / "static"
    page = support.page_text()
    js = support.text("family/static/shell.js", "apps/idiograph/static/distil.js")
    css = support.text("family/static/style.css", "apps/idiograph/static/distil.css")

    # 3. Tab and the help card follow the same order
    # FIELDS keeps its own order, which is only the set of ids the input watcher walks
    # each pair's bin after its key quote since 18 October, and a field of a hidden column passed over (186), and on
    # a thematic analysis project's Coding screen each extract's Add a code after the pairs, a list an IPA project
    # never has (a11yfix, 8 November)
    check("Tab cycles the fields in the order they sit in, pair by pair, then the notes",
          "const order = [...$('pairs').querySelectorAll('.pair-es, .pair-kq, .pair-remove'),\n"
          "        ...($('cx-list') ? $('cx-list').querySelectorAll('.cx-field') : []), $('en')]\n"
          "        .filter((el) => el.getClientRects().length);" in support.keydown_text(js)
          and "if (!on) { if (list) list.remove(); return; }" in support.text("apps/idiograph/static/codes.js")
          and "const order = ['es', 'kq', 'en']" not in js)

    check("the guidance comes back from a tool on the bar, the slim tab gone with its rail",
          'id="btn-guide"' in page and "guide-handle" not in page + js + css
          and "$('btn-guide').onclick = () => toggleGuide(true);" in js,
          "the bar's Guidance tool, where a slim tab with the arrow pointing left once stood")
    check("the choice survives a reload",
          "const GUIDE_KEY = 'idiograph-guide'" in js and "guide(guideStored());" in js
          and "localStorage.setItem(GUIDE_KEY" in js,
          "stored the way the theme is stored, and read on boot")
    check("g still toggles it and the help card lists it",
          "else if (key === 'g' && !$('work').hidden) { toggleGuide(); }" in js and "toggleGuide(); }" in js
          and '<td class="mono">G</td><td>Show or hide the guidance</td>' in page)
