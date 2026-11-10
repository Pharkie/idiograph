from __future__ import annotations

from . import support
from .support import check


def test_round_two():
    print("\n21. The playhead, the margin, the panels, the theme and undo")
    import server as server_mod
    static = server_mod.HERE / "static"
    js = support.text("family/static/shell.js", "apps/idiograph/static/distil.js")
    quote_js = support.text("family/static/quote.js")

    check("the mark moves and the turn being worked on does not",
          "S.listening" in js and "S.at" not in js.split("function markTurn(")[1].split("\n}")[0],
          "markTurn carries one class and touches nothing else")
    check("the column follows the mark, but not mid-selection, mid-drag or on the current turn",
          "function followListening(" in js and "S.scrubbing || S.selecting" in js
          and "classList.contains('current')" in js.split("function followListening(")[1].split("\n}")[0]
          and "isCollapsed" in js.split("function followListening(")[1].split("\n}")[0])

    check("an older store of light or dark is still honoured",
          "saved === 'light' || saved === 'dark'" in js)

    # 7. the whole row answers a click
    handler = js.split("$('transcript').addEventListener('click'", 1)[1].split("\n  });", 1)[0]
    stop_branch = handler.split("if (row.stop) {", 1)[1].split("\n    }", 1)[0]
    check("a plain click on her row goes to that turn",
          "goTo(row.pos, { count: true });" in stop_branch and "return;" in stop_branch)
    check("a plain click on the turn being worked on cues the recording back to it (item 32)",
          "if (row.pos === S.at) cueAudio(row.seconds);" in stop_branch
          and stop_branch.index("cueAudio(row.seconds);") < stop_branch.index("goTo(row.pos, { count: true });"))
    check("a plain click on one of his cues the recording and leaves the turn alone",
          "cueAudio(row.seconds);" in handler and "markTurn(row.i);" in handler
          and "S.at" not in handler.split("cueAudio(row.seconds);")[-1])
    check("the timecode keeps playing from there",
          "playFrom(Number(seek.dataset.seek))" in handler)
    check("a selection, a drag or a held modifier never navigates",
          "e.metaKey || e.ctrlKey || e.shiftKey || e.altKey" in handler
          and "pressMoved(e) || selectionLive()" in handler
          and "function selectionLive(" in js and "pressAt = { x: e.clientX, y: e.clientY }" in js,
          "the text stays free to select, which is what h and q run on")
    check("the menu control keeps its own click, and no flag mark is left to",
          "e.target.closest('[data-menu]')" in handler and ".flag-mark" not in handler)

    # 6. undo
    check("undo and redo are on the two keys",
          "e.key === 'z' || e.key === 'Z'" in js and "undoStep(backwards)" in js
          and "const backwards = !e.shiftKey && !REDO_Y(e);" in js)
    check("the stack holds several levels, newest first",
          "S.undoStack.push(entry)" in js and "S.redoStack" in js and "UNDO_DEPTH" in js)
    check("an entry on another turn goes to that turn first",
          "await goTo(row.pos)" in js.split("async function undoStep(")[1][:900])
    check("a field being typed in keeps the browser's own undo",
          "function nativeUndoOwns(" in js and "S.lastInput[el.id]" in js
          and "S.lastInput[field.id] = Date.now();" in js and "S.lastInput.en = Date.now();" in js)
    check("a pair q added comes out through statementPut, and a statement typed in it since stays, where until 16 "
          "October a highlight was reversed here through the endpoint that set it",
          "else if (el) el.querySelector('.pair-kq').value = '';" in js.split("async function statementPut(", 1)[-1][:1400]
          and "function cruxRestore(" not in js and "'/api/crux'" not in js,
          "the page makes no highlight since 16 October, so it has none to reverse")
    check("the quote comes out of its pair and the pieces come back (198)",
          "function quoteOut(" in quote_js and "quoteOut(pairsNow()" in js
          and "S.pending = entry.pieces" in js)
    check("a quote already written to the workbook is written again on undo",
          "entry.resaved" in js and "await commit(row, false);" in js.split("async function quotePut(")[1][:1600])
    check("the stack clears when another workbook opens",
          "undoClear()" in js.split("function startCase(")[1][:300] and "function undoClear(" in js)
