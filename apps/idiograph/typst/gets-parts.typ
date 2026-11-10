// What the GETs print's Typst views share (typst3, 9 November 2026), from gets_print.py's HTML and the print rules
// of 31 October and 1 November: the inks, the two faces, the line heights, a GET's bar and its count, a
// participant's badge, the head (the document's name as the main title, PROJECT and RESEARCH QUESTION to its
// right) and the three-part foot that never collides. Every word comes in the data.

#let serif = ("Charis SIL",)
#let sans = ("Nunito Sans",)
#let ink = rgb("#1F1B16")
#let soft = rgb("#554C41")
#let faint = rgb("#756A5C")
#let amber = rgb("#936000")
#let rule = rgb("#E3D9C7")
#let rule-firm = rgb("#CBBFA8")
#let paper = white
// a colour mixed with white, `color-mix(in srgb, c p%, #fff)`
#let mixw(c, p) = color.mix((rgb(c), p), (white, 100% - p), space: rgb)
// a CSS pixel is three quarters of a point
#let px = 0.75pt

// CSS's line-height: each line a box of h em, the font's own height (about 1.06 em) with the rest shared above and
// below, and no gap between the lines
#let lh(h, body) = {
  let half = (h - 1.06) / 2
  set text(top-edge: (0.82 + half) * 1em, bottom-edge: -(0.24 + half) * 1em)
  set par(leading: 0pt, spacing: 0pt)
  body
}

// a small label in capitals, as the head's PROJECT and the table's column heads
#let caps(s, size: 8pt, weight: "regular") = text(font: sans, size: size, tracking: 0.08em, weight: weight,
  fill: faint, upper(s))

// a participant's badge, the initial in the paper's white on the case's colour, 13pt high
#let badge(p) = if p.colour != "" {
  let said = text(font: sans, size: 8.5pt, weight: "semibold", fill: paper, top-edge: "cap-height",
    bottom-edge: "baseline", p.badge)
  context {
    let wide = calc.max(measure(said).width + 7pt, 13pt)
    box(baseline: 2.5pt, width: wide, height: 13pt, radius: 6.5pt, fill: rgb(p.colour),
      place(center + horizon, said))
  }
  h(4pt)
}

// a GET's count, "3 of 5" in a rounded edge of its tint, dashed under the minimum with its line after it
#let count(c, hue) = {
  box(inset: (x: 6pt, y: 1.5pt), radius: 8pt,
    stroke: (paint: mixw(hue, 60%), thickness: px, dash: if c.under { "dashed" } else { none }),
    text(font: sans, size: 8.5pt, fill: soft, c.short))
  if c.under { h(10pt); text(font: sans, size: 8pt, fill: soft, c.said) }
}

// a GET's bar: its title and description at the left, its count at the right, on its tint with a rule of it at
// the left, kept with what follows
#let get-bar(g) = block(sticky: true, width: 100%, fill: mixw(g.hue, 16%), stroke: (left: 4pt + rgb(g.hue)),
  inset: (x: 8pt, y: 4pt), above: 0pt, below: 4pt, breakable: false,
  grid(columns: (1fr, auto), column-gutter: 10pt, align: (left + top, right + top),
    {
      lh(1.3, text(font: serif, size: 13pt, fill: ink, g.label))
      if g.desc != "" { block(above: 1pt, below: 0pt, lh(1.35, text(font: serif, size: 10pt, fill: soft, g.desc))) }
    },
    count(g.count, g.hue)))

// the GET's note under its bar, its lines as typed
#let get-note(s, below: 5pt) = if s != "" {
  block(sticky: true, above: 0pt, below: below, inset: (x: 8pt), width: 100%,
    lh(1.4, text(font: serif, size: 10pt, fill: soft, s)))
}

// the head, a grid of two rows: the document's name at the left, PROJECT and its value level with it and
// RESEARCH QUESTION and its value under, the labels in a column of their own, then the board's note and the
// participants waiting
#let head(h) = {
  {
    set text(top-edge: "baseline", bottom-edge: "descender")
    set par(leading: 1.1em)
    let rows = ()
    if h.project != "" { rows.push((h.labels.project, h.project)) }
    if h.question != "" { rows.push((h.labels.question, h.question)) }
    let cells = (text(font: serif, size: 18pt, fill: ink, h.title),)
    for (i, r) in rows.enumerate() {
      if i > 0 { cells.push([]) }
      cells.push(pad(left: 16pt, caps(r.at(0))))
      cells.push(text(font: serif, size: 10pt, fill: ink, r.at(1)))
    }
    if rows.len() == 0 { cells += ([], []) }
    // the title's first baseline its line's height under the margin, as the browser sets it
    block(inset: (top: 16pt), below: 10pt, grid(columns: (auto, auto, 1fr), column-gutter: 8pt, row-gutter: 9pt, align: left + top,
      ..cells))
  }
  if h.note != "" {
    block(above: 0pt, below: 12pt, lh(1.4, text(font: sans, size: 8.5pt, fill: soft, h.note)))
  }
  for line in h.waiting {
    block(above: 0pt, below: 3pt, text(font: sans, size: 9pt, fill: amber, line))
  }
  if h.waiting.len() > 0 { v(7pt) }
}

// the foot: at the left the project, the board and the part, the project shortened at a word when the three
// parts would not keep 6mm apart, in the middle the researcher, Confidential and the day, centred in the room
// between the left's end and the right's start, at the right "Page n of N"
#let foot(f) = context layout(size => {
  set text(font: sans, size: 7pt, fill: faint)
  let n = counter(page).get().first()
  let total = counter(page).final().first()
  let right = f.page.at(0) + str(n) + f.page.at(1) + str(total) + f.page.at(2)
  let room = size.width
  let gap = 6mm
  let w(s) = measure(text(font: sans, size: 7pt, s)).width
  let widest = w(f.page.at(0) + "00" + f.page.at(1) + "00" + f.page.at(2))
  let centre = w(f.page.at(0) + "0" + f.page.at(1) + "0" + f.page.at(2))
  let middle = w(f.middle)
  let parts = if f.middle != "" { 2 } else { 1 }
  let fits(s) = w(s) + middle + widest + gap * parts <= room
  let left = f.left.join()
  if not fits(left) and f.fit >= 0 and f.fit < f.left.len() {
    let whole = f.left.at(f.fit)
    let words = whole.split(" ")
    let cut(k) = {
      let p = f.left
      let said = words.slice(0, k).join(" ").trim(regex("[\s,;:.]+"), at: end)
      p.at(f.fit) = said + "\u{2026}"
      p.join()
    }
    let k = words.len() - 1
    while k > 0 and not fits(cut(k)) { k -= 1 }
    left = cut(k)
  }
  let wide = w(left)
  let start = wide + (room - centre - wide - middle) / 2
  box(width: room, {
    left
    if f.middle != "" { h(calc.max(start - wide, 2mm)); f.middle }
    h(1fr)
    right
  })
})

// the page: A4 landscape with a 14mm margin, the foot in the bottom margin
#let gets-page(d, body) = {
  set document(title: d.title)
  set text(font: serif, size: 10pt, fill: ink, lang: d.lang, region: if d.region != "" { d.region } else { none })
  set par(spacing: 0pt, justify: false)
  set page(paper: "a4", flipped: true, margin: 14mm, footer: foot(d.foot), footer-descent: 4.5mm)
  body
}
