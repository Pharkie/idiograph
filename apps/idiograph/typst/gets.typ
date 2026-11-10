// The GETs print in Typst (typst3, 9 November 2026): the GET table, the audit trail, or both, of a board of the
// GETs, from `gets_print.typst_data` as the string input `data`. The head and the foot are the table of PETs'
// (Adam, 1 November 2026), the parts the views in gets-table.typ and gets-trail.typ, which a full set imports.
#import "gets-parts.typ": gets-page, head
#import "gets-table.typ": gets-table
#import "gets-trail.typ": gets-trail

#let d = json(bytes(sys.inputs.data))

#show: gets-page.with(d)
#head(d.head)
#if "table" in d { gets-table(d) }
#if "table" in d and "trail" in d { pagebreak(weak: true) }
#if "trail" in d { gets-trail(d) }
