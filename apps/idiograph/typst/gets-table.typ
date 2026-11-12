// The GET table in Typst (typst3, 9 November 2026), from gets_print.py's `table_section`: each GET's bar in its tint
// with its count, its note, then a row for every participant of the study, the participant with the badge and any
// mark, what of the participant sits under the GET (left out under Selected), the key quote and the row's note.
// The column heads repeat on each page, a row is never split, and a bar never ends a page. The same for a thematic
// analysis project's Theme table and a timepoints project's LGETs and LPETs, whose words come in the data.
#import "gets-parts.typ": *

#let small(s, fill: faint, weight: "regular") = text(font: sans, size: 8pt, fill: fill, weight: weight, s)
#let kind(s) = text(font: sans, size: 7.5pt, weight: "semibold", tracking: 0.04em, fill: faint, s)
// a timecode and its sheet, in the quiet sans (the print's monospace is the system's, which Typst is not given)
#let place-of(time, sheet) = {
  let parts = (time, sheet).filter(x => x != "")
  if parts.len() > 0 { h(3pt); text(font: sans, size: 8pt, fill: soft, parts.join("  ")) }
}

// what of the participant sits under the GET, one item a paragraph
#let item(it) = {
  let body = if it.kind == "pn" {
    block(stroke: (left: (paint: rule-firm, thickness: 1.5pt, dash: "dashed")), inset: (left: 6pt), {
      kind(it.kind_said); [ ]; it.text; [ ]; small(it.mine)
    })
  } else if it.kind == "pet" {
    kind(it.kind_said); [ ]; it.title; [ ]; small(it.n)
    if it.within != "" { [ ]; small(it.within) }
    if it.gone != "" { h(4pt); small(it.gone) }
  } else {
    kind(it.kind_said); [ ]; it.text
    place-of(it.time, it.sheet)
    if it.gone != "" { h(4pt); small(it.gone) }
    if it.within != "" { [ ]; small(it.within) }
    for q in it.quotes { block(above: 2pt, below: 0pt, inset: (left: 10pt), emph(q)) }
    for n in it.notes { block(above: 2pt, below: 0pt, inset: (left: 10pt), text(font: sans, size: 8.5pt, fill: soft, n)) }
  }
  block(above: 0pt, below: 4pt, lh(1.35, text(font: serif, size: 10.5pt, body)))
}

// the key quote, with his bold in it on its words where he made some on Trajectories (lpetmarks), as the trail
// sets a quote's words in bold
#let quote-of(r) = if r.quote != none {
  let said = if r.quote.at("words", default: none) == none { r.quote.text } else {
    { "\u{2018}"; r.quote.words.map(((t, b)) => if b { text(weight: "bold", t) } else { t }).join(); "\u{2019}" }
  }
  lh(1.35, { emph(said); place-of(r.quote.time, r.quote.sheet) })
} else if r.no_quote != "" {
  text(font: sans, size: 9pt, fill: faint, r.no_quote)
}

#let who-of(r) = {
  lh(1.49, text(font: serif, size: 11pt, fill: if r.empty { faint } else { ink }, { badge(r); r.who }))
  for m in r.marks { block(above: 2pt, below: 0pt, text(font: sans, size: 7.5pt, fill: amber, m)) }
}

#let nothing-of(r) = if r.nothing != "" {
  block(above: 0pt, below: 2pt, inset: (left: 6pt), text(font: sans, size: 9pt, fill: faint, r.nothing))
}

// one GET: its bar, its note, its table
#let get-table(g, selected) = {
  get-bar(g)
  get-note(g.note)
  // the HTML's 22mm, 70mm and 50mm, which the browser's table widens a little to hold a participant's badge and
  // name on one line, and under Selected shares out at the same proportions over the page
  let widths = if selected { (44mm, 1fr, 91mm) } else { (24mm, 1fr, 70mm, 50mm) }
  let made = g.rows.map(r => {
    let note = lh(1.4, text(font: sans, size: 9pt, fill: soft, r.note))
    if selected {
      (who-of(r), { nothing-of(r); quote-of(r); for it in r.items { item(it) } }, note)
    } else {
      (who-of(r), { nothing-of(r); for it in r.items { item(it) } }, quote-of(r), note)
    }
  })
  // a row is never split, as the HTML's break-inside: avoid, unless it is taller than a page can hold under the
  // column heads, where the browser splits it too, and so here it flows rather than leaving a page bare
  layout(size => {
    let fixed = widths.filter(w => type(w) == length).sum()
    let room = size.height - 24pt
    let rows = ()
    for cells in made {
      let tall = calc.max(..cells.zip(widths).map(((c, w)) => {
        let wide = if type(w) == length { w } else { size.width - fixed }
        measure(block(width: wide - 12pt, c)).height + 8pt
      }))
      rows += cells.map(c => table.cell(breakable: tall > room, c))
    }
    block(above: 0pt, below: 0pt, table(
      columns: widths, inset: (x: 6pt, y: 4pt), align: left + top,
      stroke: (x, y) => if y == 0 { (bottom: px + rule-firm) } else { (bottom: px + rule) },
      table.header(repeat: true, ..g.heads.map(h => table.cell(inset: (x: 6pt, top: 2pt, bottom: 3pt),
        caps(h, size: 7.5pt, weight: "semibold")))),
      ..rows))
  })
  v(16pt, weak: true)
}

// the table: every GET on the board, or the board's empty line
#let gets-table(d) = {
  if d.table.len() == 0 { text(font: sans, size: 9pt, fill: faint, d.none) }
  for g in d.table { get-table(g, d.selected) }
}
