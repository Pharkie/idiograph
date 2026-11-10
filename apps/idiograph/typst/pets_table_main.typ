// The table of PETs, the main file: the data from the server as the input `data`, the JSON text of
// `themes_print.typst_data`, and the view of pets_table.typ, this folder Typst's root (typst2, 9 November 2026).
#import "pets_table.typ": pets-table
#let d = json(bytes(sys.inputs.data))
#set document(title: d.title, author: if d.author != "" { d.author } else { () })
#pets-table(d)
