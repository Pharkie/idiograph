// The audit trail in Typst (typst3, 9 November 2026), from gets_print.py's `trail_section`: for each GET its bar and
// note, then a block per participant, the columns' heads, the participant, and the paths in five columns
// (transcript passage, quote, statement, PET, GET, or four in a thematic analysis project, the PETs' left out), each
// node a box of its GET's tint, the lines between them in the tint, a participant note's dashed. A passage shows
// the sentence round its quote with the quoted words in bold. Rows flow from page to page, a row is never split,
// and a heading (a GET's bar, a participant's name) never ends a page.
//
// Each row is a grid of its own, the gap between two columns two half-gaps wide, and three grid rows: the strip
// down to the line's height (11px), the rest of the nodes, and the row's space under them (6px). A stub of line is
// the strip's foot in a half-gap, and an upright piece the edge between a gap's two halves, so the lines meet at
// any height.
#import "gets-parts.typ": *

#let half = 7.5pt
#let strip = 11 * px
#let space = 6 * px
#let shares = (31, 21, 21, 15, 12)

#let kind(s) = block(above: 0pt, below: 0pt, text(font: sans, size: 7.5pt, weight: "semibold", tracking: 0.04em, fill: faint, s))
#let quiet(s, fill: faint) = block(above: 0pt, below: 0pt, text(font: sans, size: 7.5pt, fill: fill, s))

// what a node says, as `cell_html` has it
#let node-body(c) = {
  set text(size: 9pt)
  lh(1.35, if c.kind == "get" {
    text(font: serif, size: 10pt, fill: ink, c.title)
  } else if c.kind == "pet" {
    kind(c.kind_said)
    text(font: serif, size: 10pt, c.title)
    if c.within != "" { quiet(c.within) }
    if c.gone != "" { quiet(c.gone, fill: amber) }
  } else if c.kind == "pn" {
    kind(c.kind_said)
    block(above: 0pt, below: 0pt, text(font: serif, size: 9pt, fill: soft, c.text))
    quiet(c.mark, fill: amber)
  } else if c.kind == "es" {
    for (i, s) in c.statements.enumerate() {
      block(above: if i > 0 { 3 * px } else { 0pt }, below: 0pt, text(font: serif, size: 9.5pt, s))
    }
    if c.where != "" { quiet(c.where) }
    if c.gone != "" { quiet(c.gone, fill: amber) }
  } else if c.kind == "quote" {
    text(font: serif, size: 9.5pt, style: "italic", c.text)
    if c.key != "" { quiet(c.key, fill: soft) }
  } else {
    if c.where != "" { quiet(c.where) }
    if c.words == none {
      block(above: 0pt, below: 0pt, text(font: sans, size: 9pt, fill: faint, c.unread))
    } else {
      block(above: 0pt, below: 0pt, text(font: serif, size: 9pt, fill: soft,
        c.words.map(((t, b)) => if b { text(weight: "bold", fill: ink, t) } else { t }).join()))
    }
  })
}

// one row of a block's paths: its nodes, the stubs to their parents and children, and the upright pieces
#let trail-row(r, hue) = {
  let n = r.cells.len()
  let line = (paint: rgb(hue), thickness: px)
  let dashed = (paint: rgb(hue), thickness: px, dash: "dashed")
  let cols = ()
  for i in range(n) {
    if i > 0 { cols += (half, half) }
    cols.push(shares.at(if n == 4 and i == 3 { 4 } else { i }) * 1fr)
  }
  // the strokes each cell carries, by its place
  let marks = (:)
  let add(marks, x, y, side, s) = {
    let all = marks
    let k = str(x) + "," + str(y)
    let m = all.at(k, default: (:))
    m.insert(side, s)
    all.insert(k, m)
    all
  }
  let nodes = ()
  for (i, c) in r.cells.enumerate() {
    let x = 3 * i
    if c == none { continue }
    if c.kind == "pass" {
      let s = if c.dashed { dashed } else { line }
      for xx in (x - 1, x, x + 1) { if xx >= 0 and xx < cols.len() { marks = add(marks, xx, 0, "bottom", s) } }
      continue
    }
    if c.in and x + 1 < cols.len() { marks = add(marks, x + 1, 0, "bottom", if c.dashed { dashed } else { line }) }
    if c.out and x > 0 { marks = add(marks, x - 1, 0, "bottom", line) }
    let pn = c.kind == "pn"
    nodes.push(grid.cell(x: x, y: 0, rowspan: 2,
      fill: if pn { paper } else { mixw(hue, 5%) },
      stroke: if pn { (paint: rule-firm, thickness: px, dash: "dashed") } else { px + mixw(hue, 45%) },
      inset: (x: 7 * px, top: 3 * px, bottom: 4 * px), node-body(c)))
  }
  for (i, how) in r.spines.enumerate() {
    if how == "" or i == 0 { continue }
    let x = 3 * i - 2
    let ys = if how == "down" { (1, 2) } else if how == "full" { (0, 1, 2) } else { (0,) }
    for y in ys { marks = add(marks, x, y, "right", line) }
  }
  let edges = marks.pairs().map(((k, m)) => {
    let (x, y) = k.split(",").map(int)
    grid.cell(x: x, y: y, stroke: m, [])
  })
  block(breakable: false, above: 0pt, below: 0pt, width: 100%,
    grid(columns: cols, rows: (strip, auto, space), ..nodes, ..edges))
}

// the columns' heads, at the top of each participant's block
#let heads-row(names) = {
  let cols = ()
  let n = names.len()
  for i in range(n) {
    if i > 0 { cols.push(2 * half) }
    cols.push(shares.at(if n == 4 and i == 3 { 4 } else { i }) * 1fr)
  }
  let cells = ()
  for (i, h) in names.enumerate() {
    if i > 0 { cells.push([]) }
    cells.push(caps(h, size: 7pt, weight: "semibold"))
  }
  block(sticky: true, above: 0pt, below: 4pt, grid(columns: cols, ..cells))
}

// one participant's block: the rule, the heads, the name and its marks, then the rows
#let trail-block(b, g) = {
  block(sticky: true, above: 0pt, below: 0pt, width: 100%, stroke: (top: px + rule), inset: (top: 6pt), {
    if b.rows.len() > 0 { heads-row(g.heads) }
    block(above: 0pt, below: 5pt, {
      lh(1.49, text(font: serif, size: 12pt, { badge(b); b.who }))
      for m in b.marks { quiet(m, fill: amber) }
    })
    if b.none != "" { block(above: 0pt, below: 4pt, text(font: sans, size: 9pt, fill: faint, b.none)) }
  })
  for r in b.rows { trail-row(r, g.hue) }
  v(4pt)
}

// one GET's trail, on a page of its own after the first
#let get-trail(g, first) = {
  if not first { pagebreak(weak: true) }
  get-bar(g)
  get-note(g.note, below: 6pt)
  for b in g.blocks { trail-block(b, g) }
}

// the trail: every GET's, or the board's empty line
#let gets-trail(d) = {
  if d.trail.len() == 0 { text(font: sans, size: 9pt, fill: faint, d.none) }
  for (i, g) in d.trail.enumerate() { get-trail(g, i == 0) }
}
