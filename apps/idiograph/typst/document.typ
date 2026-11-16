// The documents no screen exported before, in Typst (exportnew, 16 November 2026): the Trajectories board, the
// annotated transcript and the code list, from `documents.typst_data` as the string input `data`. The head and the
// foot are the print views' own (gets-parts.typ), the blocks a heading, a paragraph or a table, each word in the
// data. A heading is kept with what follows it and a table's head repeats on each page (Adam's print rules of 31
// October 2026: rows flow across pages, a heading never ends one).
#import "gets-parts.typ": serif, sans, ink, soft, faint, rule, rule-firm, px, lh, caps, foot

#let d = json(bytes(sys.inputs.data))

// a paragraph's runs: bold and italics on their words, a timecode in the quiet sans
#let runs(rs) = {
  for r in rs {
    if r.at("small", default: false) {
      text(font: sans, size: 7pt, fill: faint, style: "normal", weight: "regular", r.text)
    } else {
      let c = [#r.text]
      if r.at("b", default: false) { c = strong(c) }
      if r.at("i", default: false) { c = emph(c) }
      c
    }
  }
}

#let para(p, size: 10pt) = {
  let st = p.at("style", default: "plain")
  let fill = if st == "soft" or st == "note" { soft } else { ink }
  let s = if st == "quote" { size - 0.5pt } else { size }
  block(above: 0pt, below: 3pt, sticky: p.at("keep", default: false), lh(1.4, text(font: serif, size: s, fill: fill,
    style: if st == "note" { "italic" } else { "normal" }, runs(p.runs))))
}

#let heading-block(h) = {
  let title = if h.level == 1 {
    block(width: 100%, stroke: (bottom: 0.75pt + rule-firm), inset: (bottom: 3pt),
      lh(1.3, text(font: serif, size: 15pt, fill: ink, h.text)))
  } else if h.level == 2 {
    lh(1.3, text(font: serif, size: 12pt, weight: "bold", fill: ink, h.text))
  } else {
    lh(1.3, text(font: sans, size: 10pt, weight: "semibold", fill: ink, h.text))
  }
  block(sticky: true, breakable: false, above: if h.level == 1 { 16pt } else { 11pt }, below: 5pt, {
    title
    if h.at("desc", default: "") != "" {
      block(above: 2pt, below: 0pt, lh(1.35, text(font: serif, size: 10pt, fill: soft, h.desc)))
    }
  })
}

#let doc-table(t) = {
  block(above: 4pt, below: 10pt, table(
    columns: t.widths.map(w => w * 1fr), inset: (x: 5pt, y: 4pt), align: left + top,
    stroke: (x, y) => if y == 0 { (bottom: px + rule-firm) } else { (bottom: px + rule) },
    table.header(repeat: true, ..t.heads.map(h => table.cell(inset: (x: 5pt, top: 2pt, bottom: 3pt),
      caps(h, size: 7.5pt, weight: "semibold")))),
    ..t.rows.enumerate().map(((i, r)) => r.map(c => table.cell(breakable: t.split.at(i), {
      for p in c { para(p, size: 9.5pt) }
    }))).flatten()))
}

// the head: the document's name at the left with the table's name under it, PROJECT and RESEARCH QUESTION to its
// right, the labels in a column of their own, as the table of PETs' head
#let doc-head(h) = {
  set text(top-edge: "baseline", bottom-edge: "descender")
  set par(leading: 1.1em)
  let cells = (text(font: serif, size: 18pt, fill: ink, h.title),)
  if h.project != "" {
    cells.push(pad(left: 16pt, caps(h.labels.project)))
    cells.push(text(font: serif, size: 10pt, fill: ink, h.project))
  } else { cells += ([], []) }
  cells.push(if h.subtitle != "" { text(font: serif, size: 11pt, fill: soft, h.subtitle) } else { [] })
  if h.question != "" {
    cells.push(pad(left: 16pt, caps(h.labels.question)))
    cells.push(text(font: serif, size: 10pt, fill: ink, h.question))
  } else { cells += ([], []) }
  block(inset: (top: 16pt), below: 12pt, grid(columns: (auto, auto, 1fr), column-gutter: 8pt, row-gutter: 9pt,
    align: left + top, ..cells))
}

// the participant's label and pen portrait under the head, with Pen portrait ticked
#let who(w) = block(above: 0pt, below: 12pt, width: 190mm, {
  if w.label != "" { block(above: 0pt, below: 2pt, lh(1.35, text(font: serif, size: 11pt, style: "italic", fill: ink, w.label))) }
  if w.values != "" { block(above: 0pt, below: 2pt, lh(1.35, text(font: serif, size: 10pt, fill: soft, w.values))) }
  if w.portrait != "" { block(above: 0pt, below: 0pt, lh(1.4, text(font: serif, size: 10pt, fill: soft, w.portrait))) }
})

#set document(title: d.title)
#set text(font: serif, size: 10pt, fill: ink, lang: d.lang, region: if d.region != "" { d.region } else { none })
#set par(spacing: 0pt, justify: false)
#set page(paper: "a4", flipped: true, margin: 14mm, footer: foot(d.foot), footer-descent: 4.5mm)

#doc-head(d.head)
#if "who" in d { who(d.who) }
#for b in d.blocks {
  if b.kind == "heading" { heading-block(b) }
  else if b.kind == "para" { para(b) }
  else if b.kind == "table" { doc-table(b) }
}
#if d.blocks.len() == 0 { para((style: "soft", runs: ((text: d.none),))) }
