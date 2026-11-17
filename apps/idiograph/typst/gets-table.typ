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

// An LPET timepoints across (drawsbuild, 17 November 2026, Adam's option B, as Nizza's Table 8): its bar, then a
// table, a column a timepoint, its heads over a rule repeated on each page it runs onto, then its rows State, Key
// quote with its cite and Draws on, each label kept with what follows it, then its note. The rows flow onto the next
// page where the page ends, never a half page left empty (Adam, 31 October 2026).
#let k-of(s, below: 3pt, sticky: false) = block(sticky: sticky, above: 0pt, below: below, text(font: sans, size: 7pt, weight: "semibold", tracking: 0.08em, fill: faint, upper(s)))
// each cell a row's label and what it holds, one block that never splits where it fits on a page, so a label never
// ends a page alone; one taller than a page (a State may run to 4000 characters, a key quote taken from the
// transcript to 20000) flows onto the next, its label kept with its first line, so nothing is cut (drawsbuild5)
#let lpet-state(c, w, split: false) = block(above: 0pt, below: 0pt, breakable: split, width: 100%, {
  k-of(w.state, sticky: true)
  lh(1.35, text(font: serif, size: 10.5pt, fill: ink, c.state))
})
#let lpet-quote(c, w, split: false) = block(above: 0pt, below: 0pt, breakable: split, width: 100%, {
  k-of(w.quote, sticky: true)
  if c.quote != none {
    let said = if c.quote.at("words", default: none) == none { c.quote.text } else {
      { "\u{201C}"; c.quote.words.map(((t, b)) => if b { text(weight: "bold", t) } else { t }).join(); "\u{201D}" }
    }
    lh(1.35, text(font: serif, size: 10pt, emph(said)))
    block(above: 3pt, below: 0pt, text(font: sans, size: 7.5pt, fill: soft, c.quote.cite))
  } else {
    text(font: sans, size: 9pt, fill: faint, w.no_quote)
  }
})
// Draws on may be long, so it flows, its label kept with its first item
#let lpet-draws(c, w) = block(above: 0pt, below: 0pt, breakable: true, width: 100%, {
  k-of(w.draws, below: 5pt, sticky: true)
  if c.draws.len() == 0 {
    text(font: sans, size: 9pt, fill: faint, c.nothing)
  }
  for d in c.draws {
    block(above: 0pt, below: 3pt, inset: (top: 4pt), breakable: false, {
      block(above: 0pt, below: 2pt, text(font: sans, size: 7pt, weight: "semibold", tracking: 0.04em, fill: faint, d.kind_said))
      lh(1.35, text(font: serif, size: 10pt, { d.words; if d.time != "" { h(3pt); text(font: sans, size: 7.5pt, fill: soft, d.time) } }))
    })
  }
})

#let lpet-table(g, w) = {
  get-bar(g)
  let a = g.across
  let n = calc.max(1, a.cols.len())
  // the State and Key quote rows each stay whole where their tallest cell fits on a page under the heads, as the GET
  // table's rows do, and flow where it does not
  layout(size => {
    let wide = (size.width - 16pt - 14pt * (n - 1)) / n
    let room = size.height - 24pt
    let fits(cells) = calc.max(..cells.map(x => measure(block(width: wide, x)).height)) <= room
    let row(make) = {
      let whole = fits(a.cols.map(c => make(c, false)))
      a.cols.map(c => table.cell(breakable: not whole, make(c, not whole)))
    }
    block(above: 0pt, below: 0pt, inset: (x: 8pt, top: 2pt), breakable: true,
      table(columns: range(n).map(_ => 1fr), column-gutter: 14pt, row-gutter: 8pt, inset: 0pt, stroke: none,
        align: left + top,
        table.header(repeat: true, ..a.cols.map(c => table.cell(
          block(above: 0pt, below: 0pt, width: 100%, stroke: (bottom: px + rule-firm), inset: (bottom: 3pt),
            text(font: sans, size: 9pt, fill: soft, c.head))))),
        ..row((c, split) => lpet-state(c, w, split: split)),
        ..row((c, split) => lpet-quote(c, w, split: split)),
        ..a.cols.map(c => lpet-draws(c, w))))
  })
  if a.note != "" {
    block(above: 6pt, below: 0pt, inset: (x: 8pt), width: 100%, lh(1.4, text(font: serif, size: 10pt, fill: soft, a.note)))
  }
  v(16pt, weak: true)
}

// the PETs no LPET draws on, with his reasons, after the LPETs (drawsbuild), the GET table's rules and heads
#let unplaced-table(u) = if u.rows.len() > 0 {
  block(sticky: true, above: 2pt, below: 6pt, text(font: serif, size: 13pt, fill: ink, u.head))
  table(
    columns: (40mm, 1fr, 90mm), inset: (x: 6pt, y: 4pt), align: left + top,
    stroke: (x, y) => if y == 0 { (bottom: px + rule-firm) } else { (bottom: px + rule) },
    table.header(repeat: true, ..u.heads.map(h => table.cell(inset: (x: 6pt, top: 2pt, bottom: 3pt),
      caps(h, size: 7.5pt, weight: "semibold")))),
    ..u.rows.map(r => (
      table.cell(breakable: false, lh(1.4, text(font: sans, size: 9pt, fill: soft, r.head))),
      table.cell(breakable: false, lh(1.35, text(font: serif, size: 10.5pt, { kind(r.kind_said); [ ]; r.title }))),
      table.cell(breakable: false, lh(1.4, text(font: serif, size: 10pt, fill: ink, r.why))),
    )).flatten())
}

// the table: every GET on the board, or the board's empty line, and a participant's LPETs timepoints across with the
// PETs no LPET draws on after them
#let gets-table(d) = {
  if d.table.len() == 0 { text(font: sans, size: 9pt, fill: faint, d.none) }
  for g in d.table {
    if "across" in g { lpet-table(g, d.across) } else { get-table(g, d.selected) }
  }
  if "unplaced" in d { unplaced-table(d.unplaced) }
}
