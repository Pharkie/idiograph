from __future__ import annotations

import nudges

from . import support

from .support import check


def test_polish():
    print("\n26. The AI block under the field, navigation in the sheet, the popover and the count")
    import server as server_mod
    static = server_mod.HERE / "static"
    js = support.text("family/static/shell.js", "apps/idiograph/static/distil.js")

    # ── A. the suggestions sit where their answers appear
    reset = js.split("function resetAI(", 1)[1].split("\n}", 1)[0]
    check("a new turn draws the button again, and only when the switch is on",
          "$('ai').hidden = true;" in reset
          and "$('btn-ai').hidden = !(S.data && aiFor(S.data.config, 'statements'));" in reset
          and "resetAI();" in js.split("function drawTurn(", 1)[1].split("\n}", 1)[0])

    # ── B. the turn buttons under the player went in 131, Previous sat with the operations until 17 October,
    check("the shortcuts still move between turns",
          "e.key === 'j'" in js and "e.key === 'k'" in js
          and "$('btn-prev')" not in js and "if (MOD(e) && (e.key === 'j' || e.key === 'J')) { e.preventDefault(); move(-1); return; }" in js)

    # ── C. the key quote in place of the highlight since 16 October: a live selection, where it goes, and the
    # mark a click brings the statement forward from
    quote_fn = js.split("async function commitQuote(", 1)[1].split("\n}\n", 1)[0] if "async function commitQuote(" in js else ""
    check("q reads the selection every press, in the passage, held with Cmd or in another passage",
          "const there = selectionElsewhere();" in quote_fn
          and "if (!there && !S.pending.length && !selectionInTurn()) {" in quote_fn
          and "} else if (!S.pending.length) takeSelection(false);" in quote_fn,
          "where until 16 October h read it every press for a highlight")
    check("where the quote goes is worked out from the pair in hand and the words go there",
          "const { place, added, old } = quoteTarget(pairsNow(), workingPlace());" in quote_fn
          and "const el = added ? insertPair({ es: '', kq: quote }) : pairEls()[place];" in quote_fn
          and "function cruxOpFor(" not in js and "function cruxRunAt(" not in js)
    check("undo gives a filled key quote back what it held and takes a pair q added out, a statement typed since kept",
          "if (out) els[out.place].querySelector('.pair-kq').value = entry.old || '';" in js
          and "entry.taken = !!el && !el.querySelector('.pair-es').value.trim();" in js
          and "async function cruxRestore(" not in js,
          "where until 16 October undo walked a highlight back stretch by stretch")
    click = js.split("$('transcript').addEventListener('click', (e) => {", 1)[1].split("\n  });", 1)[0]
    check("a plain click on a key quote's mark brings its statement forward, and no click offers Unhighlight",
          "function openCruxPop(" not in js and "data-unhighlight" not in js and ">Unhighlight<" not in js
          and "const quoted = e.detail >= 2 ? null : e.target.closest('.turn-text .kq');" in click
          and "toStatement(row, Number(String(quoted.dataset.kq).split(' ')[0]))" in click,
          "and a click on another passage's mark goes there first")
    ctx = js.split("$('transcript').addEventListener('contextmenu'", 1)[1].split("\n  });", 1)[0]
    groups = js.split("function rowMenuGroups(", 1)[1].split("\n}", 1)[0]
    check("a right-click opens the row's menu with the assignments first, and no Unhighlight at its head",
          "openRowMenu(row, { pick: inThis ? pick : null, at: { x: e.clientX, y: e.clientY } });" in ctx
          and "Unhighlight" not in groups and "groups.push(assign);" in groups
          and "dropCrux" not in js,
          "where until 16 October an orange phrase put Unhighlight above a rule")

    # ── D. the count
    check("the words are counted the way the nudges count them",
          "const WORD = /[A-Za-z0-9']+/g;" in js
          and nudges.WORD.pattern == "[A-Za-z0-9']+",
          "so the number and the flag never disagree")

    # ── E. a turn open for correction keeps the caret and the clicks inside its own box.
    # A click in the box bubbled to the column's whole-row handler, which read it as a click on
    # the row: on one of her turns that is goTo at the position it is already on, which re-centres
    # and puts the caret back in the statement field.
    check("one place puts the caret back, and it stands down while a turn or a timecode is open",
          "function focusEntry(" in js
          # with no scroll of its own since 17 October, the card standing in the scrolling columns (172)
          and "if (S.editing || S.timeEdit) return;" in js.split("function focusEntry(", 1)[1].split("\n}", 1)[0]
          # with the statements hidden it goes into the notes instead (colslayout, 18 October)
          and "const pair = colsHidden('statements') ? null : workingPair();\n"
              "  if (pair) pair.querySelector('.pair-es').focus({ preventScroll: true });" in js
          and js.count("pair.querySelector('.pair-es').focus(") == 1 and "$('es')" not in js,
          "every other caller goes through it, the statement of the pair being worked on (198)")
    click = js.split("$('transcript').addEventListener('click'", 1)[1].split("\n  });", 1)[0]
    check("a click inside the open box navigates nothing and re-centres nothing",
          "if (e.target.closest('.turn-edit')) return;" in click
          and "if (!S.editing && pressFocus && isEntryField(pressFocus) && pressFocus.isConnected)" in click,
          "the handler steps around the editor before it reads the row")
    check("the turn it is already on is not re-centred while a turn is open",
          "if (!S.editing) { centreCurrent(true); focusEntry(); }" in js
          and "if (next === S.at) { centreCurrent(true)" not in js)
    check("a drag inside the box is the box's own, never a piece of a quote, nor one in the notes field beside the "
          "current passage (16 October), its card or an interviewer note (17 October)",
          "if (e.target.closest('.turn-edit') || e.target.closest('.turn.current .turn-notes, #es-card, #note-entry')) "
          "{ S.selecting = false; return; }" in js)
    check("opening the box clears the quote being built, with no popover left to take away",
          "closeTimeEdit();\n  clearPending(true);" in js and "closeCruxPop" not in js)
