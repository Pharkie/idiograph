// The full set of a board of the GETs in Typst (typst5, 9 November 2026), from `gets_print.typst_data` with `all`, as
// the HTML print view's full set orders it: the head and the contents on the first page, then each part from a new
// page under its heading, the participants table with Participants table ticked (pbioexport, 11 November 2026),
// each participant's table of PETs (each from a new page, the table of PETs' own blocks from pets_table.typ), the GET
// table and the audit trail (gets-table.typ, gets-trail.typ). A thematic analysis project's full set has no tables of
// PETs, its participants having none. Every word comes in the data. A part's heading is gets-parts.typ's.
#import "gets-parts.typ": gets-page, head, part-head, people-table, serif, sans, ink, soft, faint, lh, caps
#import "gets-table.typ": gets-table
#import "gets-trail.typ": gets-trail
#import "pets_table.typ": pets-blocks

#let d = json(bytes(sys.inputs.data))

// the contents, a numbered list two deep, as the HTML's `.contents ol`
#let contents(d) = {
  part-head(d.names.contents)
  set text(font: serif, size: 11pt, fill: ink)
  let entry(n, s, kids) = {
    block(above: 0pt, below: 0pt, lh(1.6, grid(columns: (18pt, 1fr), [#n.], s)))
    if kids.len() > 0 {
      pad(left: 18pt, for (i, k) in kids.enumerate() {
        block(above: 0pt, below: 0pt, lh(1.6, grid(columns: (18pt, 1fr), [#(i + 1).], k)))
      })
    }
  }
  let n = 1
  if "people" in d { entry(n, d.names.people, ()); n += 1 }
  if d.contents.pets { entry(n, d.names.pets, d.contents.cases); n += 1 }
  entry(n, d.names.table, ())
  entry(n + 1, d.names.trail, d.contents.gets)
}

// a participant's table of PETs: the kicker, the participant and their board, whether their PETs are complete, then
// the PETs, or the line saying they have none
#let case-table(c) = {
  block(sticky: true, above: 0pt, below: 10pt, {
    caps(c.kicker)
    block(above: 6pt, below: 0pt, text(font: serif, size: 16pt, fill: ink, {
      c.who
      if c.board != "" { text(fill: soft, [, #c.board]) }
    }))
    if c.done != "" { block(above: 6pt, below: 0pt, text(font: sans, size: 9pt, fill: soft, c.done)) }
  })
  if c.none != "" {
    text(font: sans, size: 9pt, fill: faint, c.none)
  } else {
    pets-blocks(c.themes, c.empty)
  }
}

#show: gets-page.with(d)
#head(d.head)
#contents(d)
#if "people" in d {
  pagebreak()
  part-head(d.names.people)
  people-table(d.people)
}
#if d.contents.pets {
  pagebreak()
  part-head(d.names.pets)
  for (i, c) in d.pets.enumerate() {
    if i > 0 { pagebreak() }
    case-table(c)
  }
}
#pagebreak()
#part-head(d.names.table)
#gets-table(d)
#pagebreak()
#part-head(d.names.trail)
#gets-trail(d)
