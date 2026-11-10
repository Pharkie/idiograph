// The table of Personal Experiential Themes, the print view of a PETs board, as a Typst view (typst2, 9 November
// 2026). It is the HTML view's design, themes_print.py's HEAD, ROW, PAGE, BLOCKS and the foot, set a second time:
// a change to either is made in both, and area 363 compares their text. Its data is `themes_print.typst_data`,
// from the walk of the board the HTML view reads, every word already in the run's language, so nothing here is
// English. `pets-table(d)` is the view, which a full set can import. Started from pdfengine2's proof, typ/table.typ.

#let serif = ("Charis SIL",)
#let sans = ("Nunito Sans",)
#let ink = rgb("#1F1B16")
#let soft = rgb("#554C41")
#let faint = rgb("#756A5C")
#let rule-firm = rgb("#CBBFA8")
#let mixw(c, p) = color.mix((rgb(c), p), (white, 100% - p), space: rgb)
#let mixk(c, p) = color.mix((c, p), (black, 100% - p), space: rgb)
// a step lighter for a sub-theme, as `.step-1` and `.step-2`
#let tint(t) = if t.step == 0 { rgb(t.hue) } else if t.step == 1 { mixw(t.hue, 64%) } else { mixw(t.hue, 42%) }
// the depth the indent and type steps stop at, a group inside a group (themes_print.DEEP)
#let deep = 3

// CSS's line-height: each line a box of h em, the font's own height (about 1.06 em) with the rest shared above
// and below, and no gap between the boxes
#let lh(h, body) = {
  let half = (h - 1.06) / 2
  set text(top-edge: (0.82 + half) * 1em, bottom-edge: -(0.24 + half) * 1em)
  set par(leading: 0pt)
  body
}

// CSS's line-height of normal, a line as tall as the font's own ascender and descender
#let normal(body) = {
  set text(top-edge: "ascender", bottom-edge: "descender")
  body
}

#let label(s) =text(font: sans, size: 8pt, tracking: 0.08em, fill: faint, upper(s))
// where a statement was said, "(Initial, 12:04)", in the quiet sans with tabular figures so the timecodes line up
#let ref(s) = if s != "" {
  box(text(font: sans, size: 7pt, tracking: 0.02em, fill: faint, number-width: "tabular", s))
}

// ---------------------------------------------------------------- the foot

// The foot in three parts (Adam, 31 October and 1 November 2026): at the left the participant, the board, the
// project and the table, in the middle the researcher, Confidential and the day, centred in the room between the
// left's end and the right's start, and at the right "Page n of N". When the three would come closer than the gap,
// the project alone is cut at a word with "…", as the HTML view's script (FOOT_FIT) cuts it.
#let foot(f) = context {
  set text(font: sans, size: 7pt, fill: faint)
  let n = counter(page).get().first()
  let total = counter(page).final().first()
  let page-of(a, b) = f.page_of.replace("{page}", str(a)).replace("{pages}", str(b))
  let width(s) = measure(text(font: sans, size: 7pt, s)).width
  let room = f.room_mm * 1mm
  let gap = f.gap_mm * 1mm
  let rw = width(page-of(total, total))
  let middle = if f.middle != "" { width(f.middle) } else { 0pt }
  let parts = (if f.middle != "" { 1 } else { 0 }) + 1
  let fits(s) = width(s) + middle + rw + gap * parts <= room
  let pieces = f.left
  let said = pieces.join()
  if not fits(said) and f.fit >= 0 and f.fit < pieces.len() {
    let whole = pieces.at(f.fit)
    let ends = (0,) + whole.matches(regex("\\S\\s")).map(m => m.start + 1)
    let cut(k) = {
      let p = pieces
      p.at(f.fit) = whole.slice(0, k).trim(regex("[\\s,;:.]+"), at: end) + "…"
      p.join()
    }
    said = cut(0)
    for k in ends.rev() {
      if fits(cut(k)) { said = cut(k); break }
    }
  }
  let wide = width(said)
  if f.middle != "" {
    let start = calc.max(wide + gap, wide + (room - rw - wide - middle) / 2)
    grid(columns: (start, 1fr, auto), align(left, said), align(left, f.middle), align(right, page-of(n, total)))
  } else {
    grid(columns: (1fr, auto), column-gutter: gap, align(left, said), align(right, page-of(n, total)))
  }
}

// ---------------------------------------------------------------- the head

// a grid of two rows and two sides (Adam, 1 November 2026): the participant with the table's name under it at the
// left, in no more than two fifths of the width, PROJECT and RESEARCH QUESTION at the right, each level with one of
// them, the labels in their own column, each cell's top edge its first baseline, so the rows share their first line
#let head(d) = layout(size => {
  set text(top-edge: "baseline", bottom-edge: "descender")
  set par(leading: 1.1em)
  let title = text(size: 18pt, d.case)
  let name = text(size: 11pt, fill: soft, d.table)
  let first = calc.min(calc.max(measure(title).width, measure(name).width), size.width * 0.4)
  let about = ((d.labels.project, d.project), (d.labels.question, d.question))
  let cells = ()
  for (i, side-cell) in (title, name).enumerate() {
    let (l, v) = about.at(i)
    cells += (side-cell, if v != "" { label(l) }, if v != "" { text(size: 10pt, v) })
  }
  // each cell's top edge is its baseline, so the title's first line is set down by the height above its baseline in
  // a line of 1.15, as the HTML's h1 has it, which keeps the type inside the page's margin
  v(15.6pt)
  grid(columns: (first, auto, 1fr), column-gutter: (8pt + 16pt, 8pt), row-gutter: 13pt, align: left + top, ..cells)
})

// ---------------------------------------------------------------- a statement's row

// the statement and where it was said at the left, its quote at the right, 136 mm at every level so the quotes
// line up down the page, a discard's reason and the statements stacked under it under it on the left, the row
// never split across a page
#let row(s) = block(breakable: false, below: 0pt, above: 0pt, inset: (bottom: 4.5pt), grid(
  columns: (1fr, 136mm), column-gutter: 7mm,
  {
    lh(1.35)[#s.text #h(3pt)#ref(s.ref)]
    if s.reason != "" {
      block(above: 1pt, below: 0pt, normal(text(font: sans, size: 7.5pt, fill: faint, s.reason)))
    }
    if s.stacked != none {
      pad(left: 2pt, top: 2pt, block(stroke: (left: 1pt + rule-firm), inset: (left: 7pt), above: 0pt, below: 0pt, {
        block(above: 0pt, below: 1pt, normal(text(font: sans, size: 7pt, fill: faint, s.stacked.head)))
        for x in s.stacked.items {
          block(above: 0pt, below: 0pt, lh(1.35, text(size: 9pt, fill: soft)[#x.text #h(3pt)#ref(x.ref)]))
        }
      }))
    }
  },
  // its first baseline level with the statement's, as the HTML's grid aligns them
  if s.quote != "" { pad(top: 0.74pt, lh(1.4, text(size: 9pt, style: "italic", fill: soft, s.quote))) },
))

// ---------------------------------------------------------------- the blocks

#let head-of(t) = {
  let desc = if t.desc != "" {
    block(above: 1pt, below: 0pt, lh(1.35, text(size: 9pt, weight: "regular", style: "normal", tracking: 0pt, fill: soft, t.desc)))
  }
  if t.depth == 0 {
    let c = tint(t)
    // the 5pt under the band after the pad, since a block's own space below is dropped at the end of its container
    pad(left: -11pt, block(fill: mixw(t.hue, 11%), width: 100%, inset: (left: 11pt, right: 8pt, y: 3.5pt), above: 0pt,
      below: 0pt, breakable: false, grid(columns: (auto, 1fr), column-gutter: 6pt,
      lh(1.3, text(size: 11.5pt, weight: "bold", tracking: 0.05em, fill: mixk(c, 82%), t.number)),
      { lh(1.3, text(size: 11.5pt, weight: "bold", tracking: 0.05em, upper(t.label))); desc })))
    v(5pt)
  } else {
    block(above: 0pt, below: 3.5pt, breakable: false, {
      lh(1.3, text(size: if t.depth == 1 { 10.5pt } else { 10pt }, weight: "bold",
        style: if t.depth == 1 { "normal" } else { "italic" }, t.label))
      desc
    })
  }
}

// the rule down a block's side, a PET's 2pt with 11pt inside, a sub-theme's 1pt with 10pt inside and 3pt before
// it, a block deeper than a group inside a group set in no further (`.deep`)
#let side(t, body, is-lead) = {
  let c = tint(t)
  if t.depth == 0 {
    block(stroke: (left: 2pt + c), inset: (left: 11pt), above: 0pt, below: 0pt, breakable: not is-lead, width: 100%, body)
  } else {
    if is-lead { v(7pt) }
    pad(left: if t.depth > deep { -11pt } else { 3pt }, block(stroke: (left: 1pt + c), inset: (left: 10pt),
      above: 0pt, below: 0pt, breakable: not is-lead, width: 100%, body))
  }
}

// a label's block as two parts, the lead, its heading, its note and its first row (or its first sub-theme's lead),
// which a page never splits, so a heading never ends a page, and the rest, which flows a row at a time
#let lead-and-rest(t, empty) = {
  let items = t.items
  let lead = (head-of(t),)
  if t.note != "" {
    lead.push(block(above: 0pt, below: 5pt, lh(1.4, text(size: 9pt, style: "italic", fill: soft, t.note))))
  }
  let rest = ()
  if items.len() > 0 {
    let first = items.first()
    if first.kind == "theme" {
      let (l, r) = lead-and-rest(first, empty)
      lead.push(side(first, l, true))
      if r != none { rest.push(side(first, r, false)) }
    } else { lead.push(row(first)) }
    for it in items.slice(1) {
      if it.kind == "theme" {
        let (l, r) = lead-and-rest(it, empty)
        rest.push(side(it, l, true))
        if r != none { rest.push(side(it, r, false)) }
      } else { rest.push(row(it)) }
    }
  } else if empty != "" {
    lead.push(block(above: 1pt, below: 4.5pt, normal(text(font: sans, size: 8.5pt, fill: faint, empty))))
  }
  (lead.join(), if rest.len() > 0 { rest.join() } else { none })
}

// the PETs, each block a lead a page never splits and the rest flowing after it, which the table of PETs and a full
// set's table of each participant's PETs (gets-all.typ) both set
#let pets-blocks(themes, empty) = {
  for (i, t) in themes.enumerate() {
    let (l, r) = lead-and-rest(t, empty)
    side(t, l, true)
    if r != none { side(t, r, false) }
    if i < themes.len() - 1 { v(14pt) }
  }
}

// ---------------------------------------------------------------- the page

#let pets-table(d) = {
  set text(font: serif, size: 10pt, fill: ink, lang: d.lang, region: if d.region != "" { d.region } else { none })
  set par(spacing: 0pt, justify: false)
  set page(paper: "a4", flipped: true, margin: (top: 14mm, x: 16mm, bottom: 16mm),
    footer: foot(d.foot), footer-descent: 6.5mm)

  head(d)
  v(10pt)
  if d.note != "" {
    block(above: 0pt, below: 12pt, lh(1.4, text(font: sans, size: 8.5pt, fill: soft)[#label(d.labels.board_note)#h(6pt)#d.note]))
  }
  pets-blocks(d.themes, d.empty)
  if d.none != "" {
    block(above: 1pt, below: 4.5pt, normal(text(font: sans, size: 8.5pt, fill: faint, d.none)))
  }
  // Not placed and the statements set aside, each with its count, its heading kept with its first row
  for (i, part) in d.rest.enumerate() {
    v(if i == 0 { 16pt } else { 12pt })
    let heading = block(above: 0pt, below: 6pt, stroke: (bottom: 0.75pt + rule-firm), inset: (bottom: 3pt), width: 100%,
      normal(text(size: 12pt, part.heading)))
    block(breakable: false, above: 0pt, below: 0pt, { heading; if part.items.len() > 0 { row(part.items.first()) } })
    for s in part.items.slice(1) { row(s) }
  }
}
