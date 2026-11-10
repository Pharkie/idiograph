// The canvas's page, from canvas_out.typst_data: in the PDF a landscape A4 page, the board scaled to fit
// under its title, never past its own size, and in the picture a page sized to the board.
#import "canvas.typ": canvas

#let d = json(bytes(sys.inputs.data))
#let image-mode = d.at("image", default: false)

#set document(title: d.title)
#set text(lang: d.lang, region: d.at("region", default: none), hyphenate: false)
#set par(leading: 0pt, spacing: 0pt, justify: false, linebreaks: "simple")
#set page(paper: "a4", flipped: true, margin: 10mm, fill: white) if not image-mode
#set page(width: auto, height: auto, margin: 0pt, fill: white) if image-mode

#canvas(d)
