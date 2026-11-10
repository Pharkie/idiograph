// The canvas of a PETs, LPETs or GETs board on one page, drawn from the board's saved layout alone
// (typst4, 9 November 2026), where until then the canvas page in a window or a found browser drew it
// (thCanvasPage in themes.js). The data is canvas_out.typst_data's: the cards, labels, frames' members
// and sticky notes where the board keeps them, every word in the user's language.
//
// The frame rule is the app's own, carried whole from themes.js. The template measures each card twice,
// as the screen shows it (its statement four lines at most) and whole, each label and note as the
// screen does, and then lays the board out as thCanvasWhole does: each card taller whole than on
// screen takes its whole height in the order the canvas reads, what it comes to sit on makes way
// (thSettle with `stay`), and every frame runs round its label and what it holds (thLayout). So a board
// never opened in a window comes out as one that was.
//
// One CSS pixel of the canvas is `px`: 0.75pt in the PDF, as a browser prints it, and 1pt in the
// picture, so 144 pixels an inch give twice the canvas's size, as the picture had. No drop shadows:
// the cards, notes and labels are drawn flat.

#let SERIF = ("Charis SIL",)
#let SANS = ("Nunito Sans",)
// each face's ascent and descent over its em, for the half-leading the browser puts round a line
#let CHARIS = (asc: 2450 / 2048, desc: 900 / 2048)
#let NUNITO = (asc: 1.011, desc: 0.353)

// the light theme's ink and paper (tokens.css), on white paper as the canvas page sets it
#let INK = rgb("#1F1B16")
#let SOFT = rgb("#554C41")
#let FAINT = rgb("#756A5C")
#let RULE = rgb("#E3D9C7")
#let FIRM = rgb("#CBBFA8")
#let CARD = rgb("#FFFDF8")
#let PAPER = rgb("#FFFFFF")
#let CRUX = rgb("#B04E00")
#let ACCENT = rgb("#786850")
#let AMBER = rgb("#936000")
#let STICKY-INK = rgb("#1E3770")

// themes.js's measures
#let GAP = 8
#let MARGIN = 10
#let ROW = 40
#let FRAME-X = 14
#let FRAME-Y = 12
#let PASSES = 8
#let LABEL-W = 340
#let BADGE-X = 12
#let BADGE-H = 14
#let FIRM-YIELDS = 4000
#let FIRM-LEADS = 3000
#let FIRM-GREW = 2000
#let FIRM-PUSHED = 1000
#let CANVAS-MARGIN = 24
#let CARD-W = 200

#let mix(a, p, b) = color.mix((a, p), (b, 100% - p), space: rgb)
#let alpha(c, p) = c.transparentize(100% - p)
#let tint(o) = if o.step == 0 { rgb(o.hue) } else if o.step == 1 { mix(rgb(o.hue), 64%, white) } else { mix(rgb(o.hue), 42%, white) }
// JavaScript's Math.round, half up, where calc.round takes half away from zero
#let jsround(x) = calc.floor(x + 0.5)

// ---- type, each line exactly its line-height, the glyphs set in it as the browser sets them

#let edges(lh, m) = {
  let top = (lh - (m.asc + m.desc)) / 2 + m.asc
  (top-edge: top * 1em, bottom-edge: -(lh - top) * 1em)
}

#let run(px, words, font: SERIF, size: 14.5, lh: 1.38, fill: INK, style: "normal", weight: "regular",
  tracking: 0, tabular: false, caps: false) = {
  let m = if font == SANS { NUNITO } else { CHARIS }
  let e = edges(lh, m)
  let said = if caps { upper(words) } else { words }
  let lines = said.split("\n")
  text(font: font, size: size * px, fill: fill, style: style, weight: weight, tracking: tracking * 1em,
    number-width: if tabular { "tabular" } else { auto }, top-edge: e.top-edge, bottom-edge: e.bottom-edge,
    lines.join(linebreak()))
}

// a run's height in canvas pixels set `w` wide, its lines, and its width on one line
#let tall(px, w, body) = measure(block(width: w * px, body)).height / px
#let wide(px, body) = measure(box(body)).width / px
#let count-lines(h, line) = calc.max(1, jsround(h / line))

// `said` cut at a word with "…" so it sets in `n` lines at most `w` wide, as the browser's line-clamp ends the last
// line it shows with an ellipsis (typst5), `make` the run for a string. A run that fits comes back whole.
#let clamp(px, w, said, n, line, make) = {
  if count-lines(tall(px, w, make(said)), line) <= n { return said }
  let words = said.split(" ")
  let cut(k) = words.slice(0, k).join(" ").trim(regex("[\\s,;:.]+"), at: end) + "\u{2026}"
  let lo = 0
  let hi = words.len() - 1
  while lo < hi {
    let mid = calc.quo(lo + hi + 1, 2)
    if count-lines(tall(px, w, make(cut(mid))), line) <= n { lo = mid } else { hi = mid - 1 }
  }
  cut(lo)
}

// a thematic analysis project's code card's foot (gtCodeCardHtml, codes.css `.gt-whos`): each participant's letter
// on their colour and how many of the code's extracts are theirs, flowing in rows as the foot's flex wraps them, each
// item its badge, 3px, its count and 8px after it
#let WHO-ROW = 10.5 * 1.5
#let who-badge(px, w) = calc.max(15, wide(px, run(px, w.badge, font: SANS, size: 10, weight: "semibold")) + 8)
#let whos-rows(px, whos, inner) = {
  let rows = ((),)
  let used = 0
  for w in whos {
    let b = who-badge(px, w)
    let item = b + 3 + wide(px, run(px, w.n, font: SANS, size: 10.5, tabular: true)) + 8
    if rows.at(rows.len() - 1).len() > 0 and used + item > inner {
      rows.push(())
      used = 0
    }
    rows.at(rows.len() - 1).push((w: w, b: b, x: used))
    used += item
  }
  rows
}
#let whos-height(px, whos, inner) = {
  let n = whos-rows(px, whos, inner).len()
  6 + n * WHO-ROW + (n - 1) * 2
}

// where the line between a close pair runs (thLinkPath), in the board's own units. One card over the other, sharing
// a stretch of their width, a short line from the upper's foot into the lower's top when no card stands between. Two
// of one row, out of each foot and along the gap under the row. Otherwise out of the upper's foot, along the gap
// under it, down the gap beside the lower and into its side. Its points, and the two dots at its ends.
#let link-path(A, B, others) = {
  let m = MARGIN / 2
  let ca = A.x + A.w / 2
  let cb = B.x + B.w / 2
  let (U, L) = if A.y < B.y { (A, B) } else { (B, A) }
  if U.y + U.h <= L.y {
    let lo = calc.max(U.x, L.x) + 14
    let hi = calc.min(U.x + U.w - 14, L.x + L.w - 16 - 8)
    if hi >= lo {
      let x = jsround(calc.min(hi, calc.max(lo, (U.x + U.w / 2 + L.x + L.w / 2) / 2)))
      let (y0, y1) = (U.y + U.h, L.y)
      let between = others.any(o => o.x < x and x < o.x + o.w and o.y < y1 and o.y + o.h > y0)
      if not between { return (pts: ((x, y0), (x, y1)), ends: ((x, y0), (x, y1))) }
    }
  }
  if calc.abs(A.y - B.y) < 80 / 2 {
    let y = calc.max(A.y + A.h, B.y + B.h) + m
    return (pts: ((ca, A.y + A.h), (ca, y), (cb, y), (cb, B.y + B.h)), ends: ((ca, A.y + A.h), (cb, B.y + B.h)))
  }
  let cu = U.x + U.w / 2
  let right = L.x + L.w / 2 >= cu
  let x = if right { L.x - m } else { L.x + L.w + m }
  let y = L.y + calc.min(L.h / 2, 28)
  let edge = if right { L.x } else { L.x + L.w }
  (pts: ((cu, U.y + U.h), (cu, U.y + U.h + m), (x, U.y + U.h + m), (x, y), (edge, y)), ends: ((cu, U.y + U.h), (edge, y)))
}

#let mark(name, c) = {
  let svg = read("marks/" + name + ".svg").replace("currentColor", c.to-hex())
  image(bytes(svg), format: "svg")
}

// ---- the board's geometry, themes.js's own (thUnion, thMeets, thPad, the binary heap)

#let union(boxes) = {
  let x = calc.min(..boxes.map(b => b.x))
  let y = calc.min(..boxes.map(b => b.y))
  let r = calc.max(..boxes.map(b => b.x + b.w))
  let b = calc.max(..boxes.map(q => q.y + q.h))
  (x: x, y: y, w: r - x, h: b - y)
}
#let meets(a, b, margin) = (a.x < b.x + b.w + margin and b.x < a.x + a.w + margin
  and a.y < b.y + b.h + margin and b.y < a.y + a.h + margin)
#let pad(b) = (x: b.x - FRAME-X, y: b.y - FRAME-Y, w: b.w + 2 * FRAME-X, h: b.h + 2 * FRAME-Y)

#let heap-push(heap, item) = {
  heap.push(item)
  let i = heap.len() - 1
  while i > 0 {
    let up = calc.quo(i - 1, 2)
    if heap.at(up).at(0) <= heap.at(i).at(0) { break }
    let t = heap.at(up)
    heap.at(up) = heap.at(i)
    heap.at(i) = t
    i = up
  }
  heap
}
#let heap-pop(heap) = {
  let top = heap.at(0)
  let last = heap.pop()
  if heap.len() > 0 {
    heap.at(0) = last
    let i = 0
    while true {
      let l = 2 * i + 1
      let r = l + 1
      let m = i
      if l < heap.len() and heap.at(l).at(0) < heap.at(m).at(0) { m = l }
      if r < heap.len() and heap.at(r).at(0) < heap.at(m).at(0) { m = r }
      if m == i { break }
      let t = heap.at(m)
      heap.at(m) = heap.at(i)
      heap.at(i) = t
      i = m
    }
  }
  (heap, top)
}

// ---- the board: where each card, label and note stands, and what each group holds

#let is-group(st, id) = id in st.members
#let is-sticky(st, id) = id in st.sin

#let parents-of(st) = {
  let out = (:)
  for g in st.groups { for m in st.members.at(g) { out.insert(m, g) } }
  for (n, gid) in st.sin { if gid != none and gid in st.members { out.insert(n, gid) } }
  out
}
#let ancestors(par, id) = {
  let out = ()
  let at = par.at(id, default: none)
  while at != none and at not in out { out.push(at); at = par.at(at, default: none) }
  out
}
#let descendants(st, id, out: ()) = {
  for m in st.members.at(id, default: ()) {
    if m in out { continue }
    out.push(m)
    out = descendants(st, m, out: out)
  }
  out
}

// every group after the groups it holds, so each frame is known before the frame round it
#let post-order(st) = {
  let out = ()
  let visit(id, busy, out) = {
    if id in out or id in busy { return out }
    for m in st.members.at(id) { if is-group(st, m) { out = visit(m, busy + (id,), out) } }
    out.push(id)
    out
  }
  for g in st.groups { out = visit(g, (), out) }
  out
}

#let size-of(sizes, id) = sizes.at(id)

/* thLayout: each label above what it holds, its left edge on theirs, and its frame round them. The
   group's place is written back, as thLayout writes g.x and g.y. */
#let layout(st, sizes) = {
  let out = (:)
  let pos = st.pos
  for id in post-order(st) {
    let boxes = ()
    let present = st.members.at(id) + st.stickies.filter(n => st.sin.at(n) == id)
    for m in present {
      if is-group(st, m) {
        if m in out { boxes.push(out.at(m).frame) }
      } else {
        let c = pos.at(m)
        let s = size-of(sizes, m)
        boxes.push((x: c.x, y: c.y, w: s.w, h: s.h))
      }
    }
    let s = size-of(sizes, id)
    let body = if boxes.len() > 0 { union(boxes) } else { none }
    if body != none { pos.insert(id, (x: jsround(body.x), y: jsround(body.y - GAP - s.h))) }
    let g = pos.at(id)
    let label = (x: g.x, y: g.y, w: s.w, h: s.h)
    let all = if body != none { union((label, body)) } else { label }
    out.insert(id, (label: label, body: body, all: all, frame: pad(all)))
  }
  (out, pos)
}

#let solid(st, sizes, lay, id) = {
  if is-group(st, id) {
    let l = lay.at(id, default: none)
    if l == none { none } else if l.body != none { l.frame } else { l.label }
  } else {
    let c = st.pos.at(id)
    let s = size-of(sizes, id)
    (x: c.x, y: c.y, w: s.w, h: s.h)
  }
}

// who stands beside whom: the canvas, "", and each group, in the order themes.js adds them
#let neighbours(st, par) = {
  let out = ("": ())
  for g in st.groups { out.insert(g, ()) }
  let add(out, id) = {
    let p = par.at(id, default: none)
    let at = if p == none or p not in out { "" } else { p }
    out.at(at).push(id)
    out
  }
  for g in st.groups { out = add(out, g) }
  for k in st.cards { out = add(out, k) }
  for n in st.stickies { out = add(out, n) }
  out
}

/* thFreeOffset: the shortest shift that leaves every box of `block` at least `gap` clear of every box
   of `others`, best first from where it landed, past `limit` tries beside everything to the right */
#let free-offset(block, others, gap, limit: 3000, homes: false) = {
  if block.len() == 0 or others.len() == 0 { return (0, 0) }
  let first(dx, dy) = {
    for b in block {
      let at = (x: b.box.x + dx, y: b.box.y + dy, w: b.box.w, h: b.box.h)
      for o in others { if (not homes or b.home == o.home) and meets(at, o.box, gap) { return (at, o.box) } }
    }
    none
  }
  let heap = ((0, 0, 0),)
  let seen = ("0,0": true)
  while heap.len() > 0 and limit > 0 {
    limit -= 1
    let (h, top) = heap-pop(heap)
    heap = h
    let dx = top.at(1)
    let dy = top.at(2)
    let hit = first(dx, dy)
    if hit == none { return (dx, dy) }
    let (b, o) = hit
    for (nx, ny) in ((dx + o.x + o.w + gap - b.x, dy), (dx + o.x - gap - b.w - b.x, dy),
      (dx, dy + o.y + o.h + gap - b.y), (dx, dy + o.y - gap - b.h - b.y)) {
      let sx = if nx > dx { calc.ceil(nx) } else { calc.floor(nx) }
      let sy = if ny > dy { calc.ceil(ny) } else { calc.floor(ny) }
      let key = str(sx) + "," + str(sy)
      if key in seen { continue }
      seen.insert(key, true)
      heap = heap-push(heap, (sx * sx + sy * sy, sx, sy))
    }
  }
  let right = calc.max(..others.map(o => o.box.x + o.box.w))
  (calc.ceil(right + gap - calc.min(..block.map(b => b.box.x))), 0)
}

// what moves as one: the items named and everything a label among them holds, its notes included
#let block-of(st, ids) = {
  let out = ()
  for id in ids {
    if id not in out { out.push(id) }
    if is-group(st, id) { for d in descendants(st, id) { if d not in out { out.push(d) } } }
  }
  for n in st.stickies { if st.sin.at(n) != none and st.sin.at(n) in out and n not in out { out.push(n) } }
  out
}
#let shift(st, ids, dx, dy) = {
  for id in ids {
    let at = st.pos.at(id)
    st.pos.insert(id, (x: jsround(at.x + dx), y: jsround(at.y + dy)))
  }
  st
}

#let label-boxes(lay) = {
  let out = (:)
  for (id, l) in lay { out.insert(id, (label: l.label, solid: if l.body != none { l.frame } else { l.label })) }
  out
}
#let grew(was, id, box) = {
  let w = was.at(id, default: none)
  if w == none { return true }
  let at = w.solid
  (box.x < at.x - 0.5 or box.y < at.y - 0.5 or box.x + box.w > at.x + at.w + 0.5 or box.y + box.h > at.y + at.h + 0.5)
}
#let frame-at(st, lay, pt) = {
  let best = none
  let area = float.inf
  for g in st.groups {
    let l = lay.at(g, default: none)
    if l == none { continue }
    let f = l.frame
    if pt.x < f.x or pt.x > f.x + f.w or pt.y < f.y or pt.y > f.y + f.h { continue }
    if f.w * f.h < area { best = g; area = f.w * f.h }
  }
  best
}

// thReadOrder: top to bottom, and left to right along a row of tops within ROW of the first
#let read-order(spots) = {
  let rest = spots.sorted(key: s => s.x).sorted(key: s => s.y)
  let out = ()
  while rest.len() > 0 {
    let top = rest.at(0).y
    let row = rest.filter(s => s.y - top < ROW).sorted(key: s => s.y).sorted(key: s => s.x)
    for s in row {
      out.push(s.id)
      rest = rest.filter(r => r.id != s.id)
    }
  }
  out
}

/* thSettle with `stay`, a drop's settle: what the act moved stays where it is and leads, and what it
   comes inside the margin of shifts clear by the least distance, a theme as a block with all it holds,
   and pushes on what it then meets in the next pass, for PASSES passes, the inside of a theme first.
   A card in no theme left inside a frame joins that theme, as a drop there does. */
#let settle(st, sizes, acted, was, stay: true) = {
  let block = block-of(st, acted)
  let par = parents-of(st)
  let kids = neighbours(st, par)
  let home(id) = par.at(id, default: "")
  let top = block.filter(id => par.at(id, default: none) not in block)
  // without `stay` a card, and a theme at the top of the canvas, yields, and a sub-theme leads
  let yields = if stay { () } else { top.filter(id => not is-group(st, id) or par.at(id, default: none) == none) }
  let leads = top.filter(id => id not in yields)
  let depth(h) = if h == "" { 0 } else { ancestors(par, h).len() + 1 }
  let places = kids.keys().sorted(key: h => -depth(h))
  let pushed = (:)
  let moved = false
  for pass in range(PASSES) {
    let (lay, pos) = layout(st, sizes)
    st.pos = pos
    if yields.len() > 0 {
      let mine = yields.map(id => (id: id, home: home(id), box: solid(st, sizes, lay, id)))
      let rest = ()
      for h in mine.map(b => b.home).dedup() {
        for id in kids.at(h) { if id not in block { rest.push((id: id, home: h, box: solid(st, sizes, lay, id))) } }
      }
      if mine.any(b => rest.any(o => b.home == o.home and meets(b.box, o.box, MARGIN))) {
        let (dx, dy) = free-offset(mine, rest, MARGIN, homes: true)
        if dx != 0 or dy != 0 {
          st = shift(st, block, dx, dy)
          moved = true
          continue
        }
      }
    }
    let shifted = false
    let stale = false
    for h in places {
      if stale {
        let (l2, p2) = layout(st, sizes)
        lay = l2
        st.pos = p2
        stale = false
      }
      let items = kids.at(h).enumerate().map(((i, id)) => {
        let box = solid(st, sizes, lay, id)
        let firm = if id in yields { FIRM-YIELDS } else if id in leads { FIRM-LEADS } else if id in pushed { FIRM-PUSHED - pushed.at(id) } else if (
          id not in block and is-group(st, id) and grew(was, id, box)) { FIRM-GREW } else { -1 }
        (id: id, i: i, box: box, firm: firm)
      })
      let standing = range(items.len()).filter(j => items.at(j).firm >= 0)
      let over(o, n) = (o.i != n.i and o.firm >= 0 and not (o.id in block and n.id in block)
        and (o.firm > n.firm or (o.firm == n.firm and o.i < n.i)))
      let order = range(items.len()).sorted(key: j => items.at(j).i).sorted(key: j => items.at(j).firm)
      for j in order {
        let n = items.at(j)
        if not standing.any(l => over(items.at(l), n) and meets(items.at(l).box, n.box, MARGIN)) { continue }
        let (dx, dy) = free-offset((n,), items.filter(o => over(o, n)), MARGIN)
        if dx == 0 and dy == 0 { continue }
        st = shift(st, block-of(st, (n.id,)), dx, dy)
        items.at(j).box = (x: n.box.x + dx, y: n.box.y + dy, w: n.box.w, h: n.box.h)
        items.at(j).firm = FIRM-PUSHED - pass
        pushed.insert(n.id, pass)
        moved = true
        shifted = true
        stale = true
      }
    }
    if not shifted { break }
  }
  if moved {
    let (lay, pos) = layout(st, sizes)
    st.pos = pos
    let now = parents-of(st)
    for key in (yields + pushed.keys()).dedup() {
      let note = is-sticky(st, key)
      if is-group(st, key) or key in now { continue }
      let b = solid(st, sizes, lay, key)
      let at = frame-at(st, lay, (x: b.x + b.w / 2, y: b.y + b.h / 2))
      if at != none and lay.at(at).body != none {
        if note { st.sin.insert(key, at) } else { st.members.at(at).push(key) }
      }
    }
  }
  (st: st, moved: moved)
}

/* thMakeRoom: once the page has measured a board, each pair of neighbours nearer than the margin makes
   room, a card or a note before a theme and the second of two themes settling clear as a drop there does,
   and of two cards or notes the one that reads first staying and leading. One pair at a time, each tried
   once. */
#let clashes(st, sizes) = {
  let (lay, _) = layout(st, sizes)
  let out = ()
  for (_, ids) in neighbours(st, parents-of(st)) {
    let boxes = ids.map(id => (id, solid(st, sizes, lay, id)))
    for i in range(boxes.len()) {
      for j in range(i + 1, boxes.len()) {
        if boxes.at(i).at(1) != none and boxes.at(j).at(1) != none and meets(boxes.at(i).at(1), boxes.at(j).at(1), MARGIN) {
          out.push((boxes.at(i).at(0), boxes.at(j).at(0)))
        }
      }
    }
  }
  out
}
#let make-room(st, sizes) = {
  let tried = ()
  for pass in range(64) {
    let pair = clashes(st, sizes).find(p => (p.at(0) + " " + p.at(1)) not in tried)
    if pair == none { break }
    let (a, b) = pair
    tried.push(a + " " + b)
    let (lay, pos) = layout(st, sizes)
    st.pos = pos
    let was = label-boxes(lay)
    let theme(id) = if is-group(st, id) { 1 } else { 0 }
    if theme(a) == 1 or theme(b) == 1 {
      let gives = if theme(a) < theme(b) { a } else { b }
      st = settle(st, sizes, (gives,), was, stay: false).st
    } else {
      let first = read-order((a, b).map(id => (id: id, x: st.pos.at(id).x, y: st.pos.at(id).y))).at(0)
      st = settle(st, sizes, (first,), was).st
    }
  }
  st
}

/* thBadgeSpots: each badge a corner's radius in along its frame's foot, stepped right past a
   sub-theme's badge that comes down to the same corner */
#let badge-spots(st, lay, widths) = {
  let par = parents-of(st)
  let order = st.groups.filter(id => id in lay).sorted(key: id => -ancestors(par, id).len())
  let spots = (:)
  for id in order {
    let f = lay.at(id).frame
    let spot = (x: f.x + BADGE-X, y: f.y + f.h - BADGE-H / 2, w: widths.at(id, default: 20), h: BADGE-H)
    let inner = st.members.at(id).filter(m => m in spots).map(m => spots.at(m)).sorted(key: o => o.x)
    for o in inner { if meets(spot, o, 4) { spot.x = o.x + o.w + 4 } }
    spots.insert(id, spot)
  }
  let out = (:)
  for id in order { out.insert(id, jsround(spots.at(id).x - lay.at(id).frame.x)) }
  out
}

// ---- the parts as the canvas's sheet sets them (themes.css), measured and drawn from one model

// a statement card: its height on screen (the statement four lines at most) and whole, and its parts
#let card-model(px, d, k) = {
  let gets = d.mode == "gets"
  let inner = CARD-W - 24
  let line = 14.5 * 1.38
  let words = if k.empty { run(px, k.text, style: "italic", fill: FAINT) } else { run(px, k.text) }
  let tn = count-lines(tall(px, inner, words), line)
  let parts = ()
  let kicker = if gets { 15 + 3 } else { 0 }
  let desc = if gets and k.desc != "" {
    2 + calc.min(2, count-lines(tall(px, inner, run(px, k.desc, size: 13, lh: 1.3)), 13 * 1.3)) * 13 * 1.3
  } else { 0 }
  let from = if gets and k.from != "" { 4 + 14 } else { 0 }
  let q = 0
  if k.quote != "" {
    let qn = count-lines(tall(px, inner - 10, run(px, k.quote, size: 12.5, style: "italic")), 12.5 * 1.38)
    if d.quotes == "short" { qn = calc.min(3, qn) }
    q = 6 + qn * 12.5 * 1.38
  }
  // the foot's line: the timecode's, the sheet's tag, a mark, and on screen a stack's count
  let foot-print = calc.max(14,
    if k.time != "" or k.count != "" { 10.5 * 1.5 } else { 0 },
    if k.sheet != "" { 9.5 * 1.5 + 2 } else { 0 },
    if k.mark != "" { 9.5 * 1.5 } else { 0 },
    if gets and k.marks.len() > 0 { 10 * 1.5 } else { 0 })
  // a GETs card's mark goes to a line of its own when it and the count do not fit side by side
  if gets and k.marks.len() > 0 {
    let first = if k.time != "" { wide(px, run(px, k.time, font: SANS, size: 10.5, tabular: true)) } else if k.count != "" {
      wide(px, run(px, k.count, font: SANS, size: 10.5)) } else { 0 }
    let m = wide(px, run(px, k.marks.join(" "), font: SANS, size: 10, tracking: 0.02))
    if first > 0 and first + 8 + m > inner { foot-print = 10.5 * 1.5 + 2 + 10 * 1.5 }
  }
  // a code's card: its participants' letters and counts in rows under its name, the foot's own 6px above them
  if gets and k.kind == "code" { foot-print = whos-height(px, k.at("whos", default: ()), inner) - 5 }
  let foot-screen = foot-print
  if k.stack != "" { foot-screen = calc.max(foot-screen, 17) }
  // on screen a PET's count is the button that unfolds it, a quarter of a pixel taller than its words
  if gets and k.fold { foot-screen += 0.25 }
  let why = if k.why != "" {
    3 + calc.min(2, count-lines(tall(px, inner, run(px, k.why, font: SANS, size: 11.5, lh: 1.4)), 11.5 * 1.4)) * 11.5 * 1.4
  } else { 0 }
  let rest = kicker + desc + from + q + 5 + why + 18
  (lines: tn, line: line, kicker: kicker, desc: desc, from: from, q: q, why: why,
   whole: rest + tn * line + foot-print, screen: rest + calc.min(4, tn) * line + foot-screen, foot: foot-print)
}

// a label's size on screen: its title, its description under it, its marks and its two hidden controls
#let label-words(px, g, room) = {
  let size = if g.upper { 21 } else { 17.5 }
  let title = run(px, g.label, size: size, lh: 1.28, tracking: if g.upper { 0.005 } else { 0 })
  let desc = if g.desc != "" { run(px, g.desc, size: size * 0.8, lh: 1.3, fill: SOFT) } else { none }
  (size: size, title: title, desc: desc)
}
#let label-size(px, g, most, chrome) = {
  let w = label-words(px, g, most)
  let marks = (if g.noted { 1 } else { 0 }) + (if g.picked { 1 } else { 0 })
  let room = most - chrome - 20 * marks
  let natural = calc.max(wide(px, w.title), if w.desc != none { wide(px, w.desc) } else { 0 })
  let words-w = calc.min(natural, room)
  let tline = w.size * 1.28
  let tn = count-lines(tall(px, words-w, w.title), tline)
  let h = tn * tline
  let dn = 0
  if w.desc != none {
    let dline = w.size * 0.8 * 1.3
    dn = calc.min(6, count-lines(tall(px, words-w, w.desc), dline))
    h += 2 + dn * dline
  }
  let width = calc.min(most, chrome + 20 * marks + natural)
  (w: jsround(width), h: jsround(h + 6 + (if g.upper { 3 } else { 2 })), words: words-w, tn: tn, dn: dn)
}

#let sticky-run(px, n) = run(px, n.text, font: SANS, size: 16, lh: 1.3, style: "italic", fill: STICKY-INK)
#let sticky-size(px, n) = {
  let r = sticky-run(px, n)
  let w = calc.min(160, calc.max(64, wide(px, r) + 24))
  let h = 26 + count-lines(tall(px, w - 24, r), 16 * 1.3) * 16 * 1.3
  (w: jsround(w), h: jsround(h), inner: w - 24)
}

#let badge-text(px, g) = run(px, g.badge, font: SANS, size: 10.5, lh: 12 / 10.5, tabular: true)
#let badge-width(px, g) = jsround(calc.max(20, wide(px, badge-text(px, g)) + 12))

// ---- drawing

#let at-px(px, o, body) = place(top + left, dx: o.x * px, dy: o.y * px, body)

#let draw-frame(px, d, g, f, spot, bw) = {
  let c = tint(g)
  let base = rgb(g.hue)
  at-px(px, f, rect(width: f.w * px, height: f.h * px, radius: 12 * px, stroke: px + alpha(c, 38%), fill: alpha(c, 4%)))
  let dash = if g.under { "dashed" } else { none }
  at-px(px, (x: f.x + 1 + spot, y: f.y + f.h - 7), box(width: bw * px, height: BADGE-H * px, radius: 12 * px,
    fill: PAPER, stroke: (paint: alpha(c, 70%), thickness: px, dash: dash),
    align(center + horizon, text(fill: mix(base, 65%, INK), badge-text(px, g)))))
}

#let draw-label(px, d, g, at, most) = {
  let c = tint(g)
  let gets = d.mode == "gets"
  let line = if gets { INK } else { c }
  let w = label-words(px, g, most)
  let marks = ()
  if g.noted { marks.push(mark("note", c)) }
  if g.picked { marks.push(mark("quote", c)) }
  // drawn without its two controls, which the canvas page takes away, in the room it had on screen
  let chrome = 23
  let room = most - chrome - 20 * marks.len()
  let natural = calc.max(wide(px, w.title), if w.desc != none { wide(px, w.desc) } else { 0 })
  let words-w = calc.min(natural, room)
  let words = {
    block(width: words-w * px, w.title)
    if w.desc != none {
      let dline = w.size * 0.8 * 1.3
      v(2 * px)
      let said = clamp(px, words-w, g.desc, 6, dline, s => run(px, s, size: w.size * 0.8, lh: 1.3, fill: SOFT))
      block(width: words-w * px, run(px, said, size: w.size * 0.8, lh: 1.3, fill: SOFT))
    }
  }
  let described = g.desc != ""
  let tline = w.size * 1.28
  let dot-top = if described { w.size * 0.5 } else { (tline - 8) / 2 }
  let first-h = tline
  let swatch = box(inset: (top: dot-top * px), circle(radius: 4 * px, fill: if gets { INK } else { c }))
  let mark-box(m) = box(inset: (top: (if described { 2 } else { (first-h - 13) / 2 }) * px), box(width: 13 * px, height: 13 * px, m))
  at-px(px, at, box(fill: alpha(PAPER, 82%), radius: 3 * px,
    inset: (left: 2 * px, right: 6 * px, top: 2 * px, bottom: 4 * px),
    stroke: (bottom: (if g.upper { 3 } else { 2 }) * px + line),
    grid(columns: (8 * px, words-w * px, ..marks.map(_ => 13 * px)), column-gutter: 7 * px, align: top,
      swatch, words, ..marks.map(mark-box))))
}

#let draw-sticky(px, n, at, s) = {
  at-px(px, at, block(width: (s.inner + 24.01) * px, height: s.h * px, radius: 2 * px, fill: rgb(n.colour),
    inset: (x: 12 * px, top: 12 * px, bottom: 14 * px), sticky-run(px, n)))
}

#let draw-card(px, d, k, at, ch, m) = {
  let gets = d.mode == "gets"
  let c = if k.in { tint(k) } else { none }
  let pn = gets and k.kind == "pn"
  let fill = if pn and k.in { mix(c, 9%, CARD) } else if pn { mix(ACCENT, 6%, CARD) } else if k.in { mix(c, 11%, CARD) } else { CARD }
  let edge = if k.in { mix(c, 45%, FIRM) } else { FIRM }
  let fade(x) = if k.missing { mix(x, 45%, white) } else { x }
  let dash = if k.missing or pn { "dashed" } else { none }
  let small = if k.in { SOFT } else { FAINT }
  // a stack's paper edges under its top, a step down and right for each statement under it up to four
  for i in range(k.edges, 0, step: -1) {
    at-px(px, (x: at.x + 3 * i, y: at.y + 3 * i), rect(width: CARD-W * px, height: ch * px, radius: 4 * px,
      fill: CARD, stroke: px + FIRM))
  }
  if k.more {
    at-px(px, (x: at.x + CARD-W + 6, y: at.y + ch + 6), box(width: 13 * px, height: 13 * px, radius: 50%,
      fill: CARD, stroke: px + FIRM, align(center + horizon, run(px, "+", font: SANS, size: 11, lh: 1, weight: "semibold", fill: SOFT))))
  }
  let stroke = if gets and not pn and k.case != "" {
    (top: (paint: fade(rgb(k.case)), thickness: 3 * px), rest: (paint: fade(edge), thickness: px, dash: dash))
  } else { (paint: fade(edge), thickness: px, dash: dash) }
  let inner = CARD-W - 24
  let y = 0
  let body = {
    if k.in { place(top + left, dx: -11 * px, dy: -10 * px, rect(width: 4 * px, height: (ch + 4) * px, fill: fade(if gets { INK } else { c }))) }
    if gets {
      let up = d.at("badge-up", default: 1)
      let far = d.at("badge-far", default: false)
      let badge = if k.kind != "code" and (k.kind != "pn" or k.badge != "") {
        box(width: calc.max(15, wide(px, run(px, k.badge, font: SANS, size: 10, weight: "semibold")) + 8) * up * px, height: 15 * up * px, radius: 10 * up * px, fill: fade(rgb(k.case)),
          align(center + horizon, run(px, k.badge, font: SANS, size: 10 * up, lh: 1.5, weight: "semibold", fill: if far { fade(rgb(k.case)) } else { CARD })))
      }
      place(top + left, dy: (15 - 15 * up) * px, block(width: inner * px, height: 15 * up * px, clip: true,
        align(bottom, stack(dir: ltr, spacing: 5 * px, ..(if badge != none { (badge,) } else { () }),
          run(px, k.kicker, font: SANS, size: 11, lh: 15 / 11, weight: "semibold", tracking: 0.02,
            fill: fade(if k.kind == "pet" or k.kind == "sub" { SOFT } else { FAINT }))))))
      y += m.kicker
    }
    let words = if k.empty { run(px, k.text, style: "italic", fill: fade(FAINT)) } else { run(px, k.text, fill: fade(INK)) }
    place(top + left, dy: y * px, block(width: inner * px, words))
    y += m.lines * m.line
    if m.desc > 0 {
      let said = clamp(px, inner, k.desc, 2, 13 * 1.3, s => run(px, s, size: 13, lh: 1.3))
      place(top + left, dy: (y + 2) * px, block(width: inner * px, height: (m.desc - 2) * px, clip: true,
        run(px, said, size: 13, lh: 1.3, fill: fade(SOFT))))
      y += m.desc
    }
    if m.from > 0 {
      place(top + left, dy: (y + 4) * px, block(width: inner * px, height: 14 * px, clip: true,
        run(px, k.from, font: SANS, size: 11, lh: 14 / 11, fill: fade(SOFT))))
      y += m.from
    }
    if m.q > 0 {
      let quoted = "\u{2018}" + k.quote + "\u{2019}"
      let said = if d.quotes == "short" {
        clamp(px, inner - 10, quoted, 3, 12.5 * 1.38, s => run(px, s, size: 12.5, style: "italic"))
      } else { quoted }
      place(top + left, dy: (y + 6) * px, block(width: inner * px, height: (m.q - 6) * px, clip: true,
        stroke: (left: 2 * px + fade(CRUX)), inset: (left: 8 * px),
        run(px, said, size: 12.5, style: "italic", fill: fade(SOFT))))
      y += m.q
    }
    // the foot, its parts on one baseline, a mark at its right
    y += 5
    let parts = ()
    if k.time != "" { parts.push(run(px, k.time, font: SANS, size: 10.5, lh: 1.5, tabular: true, fill: fade(small))) }
    if k.count != "" { parts.push(run(px, k.count, font: SANS, size: 10.5, lh: 1.5, fill: fade(small))) }
    if k.sheet != "" {
      parts.push(box(stroke: px + fade(FIRM), radius: 2 * px, inset: (x: 4 * px),
        run(px, k.sheet, font: SANS, size: 9.5, lh: 1.5, weight: "semibold", tracking: 0.1, caps: true, fill: fade(SOFT))))
    }
    let right = if k.mark != "" {
      run(px, k.mark, font: SANS, size: 9.5, lh: 1.5, weight: "semibold", tracking: 0.1, caps: true, fill: fade(AMBER))
    } else if gets and k.marks.len() > 0 {
      run(px, k.marks.join("  "), font: SANS, size: 10, lh: 1.5, tracking: 0.02, fill: fade(AMBER))
    } else { none }
    let two = gets and k.marks.len() > 0 and m.foot > 20
    if gets and k.kind == "code" {
      let ry = y + 1
      for row in whos-rows(px, k.at("whos", default: ()), inner) {
        for it in row {
          place(top + left, dx: it.x * px, dy: (ry + (WHO-ROW - 15) / 2) * px, box(width: it.b * px, height: 15 * px,
            radius: 10 * px, fill: fade(rgb(it.w.colour)),
            align(center + horizon, run(px, it.w.badge, font: SANS, size: 10, lh: 1.5, weight: "semibold", fill: CARD))))
          place(top + left, dx: (it.x + it.b + 3) * px, dy: ry * px,
            run(px, it.w.n, font: SANS, size: 10.5, lh: 1.5, tabular: true, fill: fade(SOFT)))
        }
        ry += WHO-ROW + 2
      }
      parts = ()
    }
    place(top + left, dy: y * px, block(width: inner * px, {
      set par(leading: 2 * px)
      parts.map(x => box(x)).join(h(8 * px))
      if right != none {
        if two { linebreak(); box(right) } else { h(1fr); box(right) }
      }
    }))
    y += m.foot
    if m.why > 0 {
      let said = clamp(px, inner, k.why, 2, 11.5 * 1.4, s => run(px, s, font: SANS, size: 11.5, lh: 1.4))
      place(top + left, dy: (y + 3) * px, block(width: inner * px, height: (m.why - 3) * px, clip: true,
        run(px, said, font: SANS, size: 11.5, lh: 1.4, fill: fade(FAINT))))
    }
  }
  at-px(px, at, block(width: CARD-W * px, height: ch * px, radius: 4 * px, fill: fade(fill), stroke: stroke, clip: true,
    inset: (left: 11 * px, right: 11 * px, top: (if gets and not pn and k.case != "" { 7 } else { 9 }) * px), body))
}

// ---- the page

#let canvas(d) = context {
  let image-mode = d.at("image", default: false)
  let px = if image-mode { 1pt } else { 0.75pt }
  let gets = d.mode == "gets"

  // the board as the file keeps it
  let cards = d.cards.map(k => k.key)
  let by-key = (:)
  for k in d.cards { by-key.insert(k.key, k) }
  let st = (groups: d.groups.map(g => g.id), cards: cards, stickies: d.stickies.map(n => n.id),
    members: (:), sin: (:), pos: (:))
  for g in d.groups {
    st.members.insert(g.id, g.members)
    st.pos.insert(g.id, (x: g.x, y: g.y))
  }
  for k in d.cards { st.pos.insert(k.key, (x: k.x, y: k.y)) }
  for n in d.stickies {
    let gid = n.at("in", default: none)
    st.sin.insert(n.id, if gid != none and gid in st.members { gid } else { none })
    st.pos.insert(n.id, (x: n.x, y: n.y))
  }

  // each part measured: on screen, and each card whole
  let models = (:)
  let screen = (:)
  let whole = (:)
  for k in d.cards {
    let m = card-model(px, d, k)
    models.insert(k.key, m)
    screen.insert(k.key, (w: CARD-W, h: jsround(m.screen)))
    if k.drawn { whole.insert(k.key, (w: CARD-W, h: jsround(m.whole))) }
  }
  let stickies = (:)
  for n in d.stickies {
    let s = sticky-size(px, n)
    stickies.insert(n.id, s)
    screen.insert(n.id, (w: s.w, h: s.h))
  }
  // thLabelsWiden: each label at its widest, then one with a description over a wider body as wide as that
  let most = (:)
  for g in d.groups {
    most.insert(g.id, LABEL-W)
    let s = label-size(px, g, LABEL-W, 73)
    screen.insert(g.id, (w: s.w, h: s.h))
  }
  if d.groups.any(g => g.desc != "") {
    let (lay, _) = layout(st, screen)
    for g in d.groups.filter(g => g.desc != "") {
      let body = lay.at(g.id).body
      if body != none and body.w > LABEL-W {
        most.insert(g.id, calc.floor(body.w))
        let s = label-size(px, g, calc.floor(body.w), 73)
        screen.insert(g.id, (w: s.w, h: s.h))
      }
    }
  }
  // where the screen puts each label at rest, and the room it makes once it has measured the board
  let (lay, pos) = layout(st, screen)
  st.pos = pos
  st = make-room(st, screen)
  let (lay, pos) = layout(st, screen)
  st.pos = pos

  // thCanvasWhole
  let sizes = screen
  let taller = d.cards.filter(k => k.key in whole and whole.at(k.key).h > screen.at(k.key).h)
  for key in read-order(taller.map(k => (id: k.key, x: st.pos.at(k.key).x, y: st.pos.at(k.key).y))) {
    let (lay, pos) = layout(st, sizes)
    st.pos = pos
    let was = label-boxes(lay)
    sizes.insert(key, whole.at(key))
    st = settle(st, sizes, (key,), was).st
  }
  let (lay, pos) = layout(st, sizes)
  st.pos = pos
  let widths = (:)
  for g in d.groups { widths.insert(g.id, badge-width(px, g)) }
  let spots = badge-spots(st, lay, widths)

  // the box round everything drawn, the margin all round
  let boxes = ()
  for g in d.groups {
    let l = lay.at(g.id)
    if l.body != none { boxes.push(l.frame) }
    let at = st.pos.at(g.id)
    boxes.push((x: at.x, y: at.y, w: sizes.at(g.id).w, h: sizes.at(g.id).h))
  }
  for k in d.cards.filter(k => k.drawn) {
    let at = st.pos.at(k.key)
    boxes.push((x: at.x, y: at.y, w: sizes.at(k.key).w, h: sizes.at(k.key).h))
  }
  for n in d.stickies {
    let at = st.pos.at(n.id)
    boxes.push((x: at.x, y: at.y, w: sizes.at(n.id).w, h: sizes.at(n.id).h))
  }
  let u = union(boxes.filter(b => b.w > 0 and b.h > 0))
  let bx = calc.floor(u.x - CANVAS-MARGIN)
  let by = calc.floor(u.y - CANVAS-MARGIN)
  let W = calc.ceil(u.x + u.w + CANVAS-MARGIN) - bx
  let H = calc.ceil(u.y + u.h + CANVAS-MARGIN) - by

  // what the checks read: every frame, card and label as laid out
  let frames-out = (:)
  for g in d.groups { if lay.at(g.id).body != none { frames-out.insert(g.id, lay.at(g.id).frame) } }
  let rec = (frames: frames-out, sizes: sizes, screen: screen, whole: whole, box: (x: bx, y: by, w: W, h: H),
    pos: st.pos, members: st.members)
  [#metadata(rec) <canvas-layout>]

  // the title over the canvas, the print view's heading, and the room left under it
  let title = block(width: (if image-mode { W } else { 1047 }) * px, inset: (bottom: 8 * 4 / 3 * px), stroke: (bottom: px + FIRM), below: 0pt,
    run(px, d.heading, size: 22 * 4 / 3, lh: 1.15))
  let title-h = measure(title).height / px + 16
  let page-w = if image-mode { W + 48 } else { 1047 }
  let room-h = if image-mode { H } else { 718 - title-h }
  let s = if image-mode { 1 } else { calc.min(1, page-w / W, room-h / H) }
  // a case's badge grows by the scale the canvas is drawn at, as the canvas does by its zoom (gtBadgeUp)
  let need = 9 / (10 * s)
  let d2 = d
  d2.insert("badge-up", calc.min(25 / 15, calc.max(1, need)))
  d2.insert("badge-far", need > 25 / 15 + 1e-9)

  let board = box(width: W * px, height: H * px, {
    let o(at) = { let r = at; r.x = at.x - bx; r.y = at.y - by; r }
    for g in d.groups {
      let l = lay.at(g.id)
      if l.body != none { draw-frame(px, d2, g, o(l.frame), spots.at(g.id), widths.at(g.id)) }
    }
    // the close pairs' lines where the cards now stand, while Close pairs is on (thLinksDraw, typst5)
    let card-box(key) = (x: st.pos.at(key).x, y: st.pos.at(key).y, w: sizes.at(key).w, h: sizes.at(key).h)
    let drawn-keys = d.cards.filter(k => k.drawn).map(k => k.key)
    let links = ()
    for pair in d.at("pairs", default: ()) {
      let (a, b) = pair
      if a in st.pos and b in st.pos and a in drawn-keys and b in drawn-keys {
        let others = drawn-keys.filter(k => k != a and k != b).map(card-box)
        links.push(link-path(card-box(a), card-box(b), others))
      }
    }
    let at-board(pt) = ((pt.at(0) - bx) * px, (pt.at(1) - by) * px)
    for l in links {
      place(top + left, curve(stroke: (paint: alpha(AMBER, 70%), thickness: 2 * px, dash: (5 * px, 3 * px), join: "round"),
        curve.move(at-board(l.pts.at(0))), ..l.pts.slice(1).map(pt => curve.line(at-board(pt)))))
    }
    for k in d.cards.filter(k => k.drawn) {
      draw-card(px, d2, k, o(st.pos.at(k.key)), sizes.at(k.key).h, models.at(k.key))
    }
    for l in links {
      for pt in l.ends {
        let (x, y) = at-board(pt)
        place(top + left, dx: x - 3.5 * px, dy: y - 3.5 * px, circle(radius: 3.5 * px, fill: CARD,
          stroke: 1.6 * px + alpha(AMBER, 80%)))
      }
    }
    for n in d.stickies { draw-sticky(px, n, o(st.pos.at(n.id)), stickies.at(n.id)) }
    for g in d.groups { draw-label(px, d2, g, o(st.pos.at(g.id)), most.at(g.id)) }
  })
  if image-mode {
    block(inset: 24 * px, {
      title
      v(16 * px)
      board
    })
  } else {
    title
    v(16 * px)
    align(center, scale(s * 100%, origin: top + left, reflow: true, board))
  }
}
