from __future__ import annotations

from . import support
from .support import check, css_block


def test_row_menu():
    print("\n31. One menu for the row, the trim card, and the timecode corrected in the margin")
    js = support.text("family/static/shell.js", "apps/idiograph/static/distil.js")
    css = support.text("family/static/style.css", "apps/idiograph/static/distil.css")

    # ── A. one menu for the whole row, and one popover kind for it
    groups = js.split("function rowMenuGroups(", 1)[1].split("\n}", 1)[0]
    chooser = js.split("function chooseFromMenu(", 1)[1].split("\n}", 1)[0]
    click = js.split("$('transcript').addEventListener('click'", 1)[1].split("\n  });", 1)[0]
    check("each entry takes the route it names",
          "'unhighlight'" not in chooser and "dropCrux" not in chooser
          and "if (item.act === 'edit') openEditor(open.row);" in chooser
          and "else if (item.act === 'time') openTimeEdit(open.row);" in chooser
          and "else if (item.act === 'cut') confirmTrim(open.row, item.direction);" in chooser
          and "else if (item.words && open.pick) assignWords(open.pick, item.to);" in chooser,
          "Edit text is the double-click on the text, Edit timecode the double-click on the timecode")
    check("the small control in the margin opens the same menu, from the timecode's line",
          'class="row-menu-open" data-menu="${row.i}"' in js
          and '<span class="gutter-time"><button type="button" tabindex="-1" class="row-menu-open"' in js
          and "display: inline-flex" in css_block(css, "\n.gutter-time")
          and "if (opener) {\n      e.stopPropagation();" in click
          and "openRowMenu(row, { pick: assignSelection(), at: { x: box.left, y: box.bottom } });" in click
          and "data-trim" not in js and ".trim-open" not in css)
    check("c opens the same menu with the assignments alone",
          "only: 'assign' });" in js and "if (only === 'assign') return groups;" in groups
          and groups.index("if (only === 'assign') return groups;") < groups.index("t('distil.assign.edit_text')"))
    check("Esc and a click anywhere else close the menu",
          "if (S.rowMenu) { e.preventDefault(); closeRowMenu(); return true; }" in js
          and "if (S.rowMenu && !S.rowMenu.el.contains(e.target)) closeRowMenu();" in js
          and "closeRowMenu();" in click)

    # ── B. the trim card: one title, and what decides
    confirm = js.split("function confirmTrim(", 1)[1].split("\n}", 1)[0]
    check("a cut goes straight to the card, and its line names the cut",
          "$('trim-line').textContent = trimLine(span);" in confirm
          and "$('trim-warn').hidden = span.marked === 0;" in confirm
          and "show('trim');" in confirm and "$('trim-go').focus();" in confirm
          and "function openTrim(" not in js)
    check("Enter cuts and Esc cancels",
          "if (!$('trim').hidden && e.key === 'Enter' && !MOD(e)) { e.preventDefault(); runTrim(); return true; }" in js
          and "'trim'" in js.split("const OVERLAYS = ", 1)[1].split("\n", 1)[0]
          and "S.trimRow = null;" in js.split("async function runTrim(", 1)[1].split("\n}", 1)[0])

    # ── C. the timecode, corrected where it stands
    check("a click on the timecode plays, and the second click of a double-click leaves the player alone",
          "if (seek) { if (e.detail < 2) playFrom(Number(seek.dataset.seek)); return; }" in click
          and "if (seek) { playFrom(" not in click,
          "the first click has cued and started it, and nothing pauses or cues again")
    dbl = js.split("$('transcript-rows').addEventListener('dblclick'", 1)[1].split("\n  });", 1)[0]
    check("a double-click on the timecode opens the box in the margin",
          "if (e.target.closest('.turn-gutter .time')) { e.preventDefault(); openTimeEdit(row); return; }" in dbl
          and dbl.index("openTimeEdit(row)") < dbl.index("openEditor(row)"))
    box_fn = js.split("function openTimeEdit(", 1)[1].split("\n}", 1)[0]
    check("Enter saves and Esc cancels, and neither reaches the page",
          "if (e.key === 'Escape') { e.preventDefault(); e.stopPropagation(); closeTimeEdit(); return; }" in box_fn
          and "if (e.key === 'Enter') { e.preventDefault(); e.stopPropagation(); saveTimeEdit(); return; }" in box_fn
          and "if (S.timeEdit) { e.preventDefault(); closeTimeEdit(); return true; }" in js)
    check("a click anywhere else cancels, and a click inside the box stays the box's own",
          "if (S.timeEdit && e.target !== S.timeEdit.field) closeTimeEdit();" in js
          and "if (e.target.closest('.time-edit')) return;" in click
          and click.index("if (e.target.closest('.time-edit')) return;") < click.index("closeTimeEdit();"))
    save_fn = js.split("async function saveTimeEdit(", 1)[1].split("\n}", 1)[0]
    caught = save_fn.split("} catch (err) {", 1)[1].split("\n  }", 1)[0]
    check("Enter sends the new timecode with the text unchanged",
          "const text = row.text;" in save_fn and "data = await editApply(row.key, text, typed);" in save_fn
          and "if (timecode !== undefined) body.timecode = timecode;" in js,
          "the field /api/edit-turn already reads, so nothing new is asked of the server")
    check("a timecode the server cannot read is refused with its line, and the box stays open",
          "say(needsRestart(err) ? RESTART_LINE : err.message, 9000);" in caught
          and "return;" in caught and "closeTimeEdit" not in caught)
    applier = js.split("async function editApply(", 1)[1].split("\n}", 1)[0]
    redraw = js.split("function drawRowTime(", 1)[1].split("\n}", 1)[0]
    check("the timecode, the cue point and the playhead take the new time with no reload",
          "row.seconds = data.seconds;" in applier and "drawRowTime(row);" in applier
          and "el.outerHTML = timeHtml(row);" in redraw and "S.spansSheet = null;" in redraw
          and "markTurnAt(" in redraw and "cueAudio" not in redraw and "play()" not in redraw
          and "reloadInPlace" not in save_fn,
          "the button plays from the new place, and the player itself is left where it is")
    check("a server from before the timecode field is told apart, with nothing written",
          "if (timecode !== undefined && data.time === undefined) throw new Error(RESTART_LINE);" in applier)
    pusher = js.split("function pushEditUndo(", 1)[1].split("\n}", 1)[0]
    check("the undo entry for an edit carries the old and the new timecode",
          "pushEditUndo(row, { text, time: open.was }, { text, time: typed });" in save_fn
          and "was,\n    now," in pusher
          and "undo: (e) => editApply(e.key, e.was.text, e.was.time)," in pusher
          and "redo: (e) => editApply(e.key, e.now.text, e.now.time)," in pusher,
          "one entry for a text or a timecode, so Cmd + Z puts either back")
