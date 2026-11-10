// Boxes and crops for review shots, measured in the page itself (20 October 2026, the shotlint build).
// Plain JavaScript with no dependency: a capture script injects this file's text into the page it shoots
// (Runtime.evaluate through the DevTools protocol, or any page.evaluate), then calls
//
//     shotPlan(['#pets .card[data-id="b3"] .menu-group'], { margin: 24 })
//
// and gets back what `packaging/review_shot.js --boxes-from` reads: each box, the crop to shoot, the
// smallest text inside it, the device scale, any problem, and `pad`, the mat (review_shot.js --pad) a box
// flush with the window's edge needs, with a note saying so. The script shoots the crop (a clip at scale 1
// with the device scale at 2) and writes the plan as JSON beside the PNG, `notes-after.png` beside
// `notes-after.shot.json`. Every rectangle is in CSS pixels, the boxes in the crop's own coordinates.
//
// shotBox(target) is the element's rectangle plus 8 pixels on every side, checked against the words, the
// pictures, the dividers and the borders round it. When the box would cross or touch any of them it climbs
// to the next larger enclosing element (a row, a card, a menu or a bar) until one clears, and says which it
// chose. Since the shotlint2 build (20 October) the box also lies at least 8 pixels inside the edge of
// every menu, card, panel, list, section or bar it sits in, an edge being a border, or a background or a
// shadow standing out from what it sits on, or it climbs to that container, and says so as `container`,
// with each edge it cleared as `edges` for review_shot.js to hold it to. A side on the window's edge is the
// mat's to answer, as a bar's is. shotCrop(boxes, margin) holds every box with room and grows until no card, row or menu is cut at
// its edges. shotMinText(crop) is the smallest text drawn inside the crop, a scaled board's included.
//
// Each takes the page's window as `opts.window` when it is not the global one, which is how area 183
// runs them in node on a made-up page.

(function (root) {
  'use strict';

  const PAD = 8; // the box's room round what it marks, and the least room from the frame's edge
  const MARGIN = 24; // the crop's room round the boxes
  const MAX_SPAN = 0.75; // a part longer than this share of the window along a side is never grown to

  const r4 = (r) => ({ x: r.x, y: r.y, w: r.w, h: r.h });
  const fromDom = (b) => ({ x: b.left, y: b.top, w: b.right - b.left, h: b.bottom - b.top });
  const inflate = (r, m) => ({ x: r.x - m, y: r.y - m, w: r.w + 2 * m, h: r.h + 2 * m });
  const empty = (r) => !(r.w > 0 && r.h > 0);
  // touching counts: a box whose line lies along a word's edge touches it
  const meets = (a, b) => a.x <= b.x + b.w && b.x <= a.x + a.w && a.y <= b.y + b.h && b.y <= a.y + a.h;
  const holds = (outer, inner) => inner.x >= outer.x && inner.y >= outer.y &&
    inner.x + inner.w <= outer.x + outer.w && inner.y + inner.h <= outer.y + outer.h;
  const union = (rs) => {
    const x = Math.min(...rs.map((r) => r.x));
    const y = Math.min(...rs.map((r) => r.y));
    return { x, y, w: Math.max(...rs.map((r) => r.x + r.w)) - x, h: Math.max(...rs.map((r) => r.y + r.h)) - y };
  };
  const round = (r) => ({ x: Math.round(r.x * 10) / 10, y: Math.round(r.y * 10) / 10, w: Math.round(r.w * 10) / 10, h: Math.round(r.h * 10) / 10 });

  function env(opts) {
    const win = (opts && opts.window) || root;
    if (!win || !win.document) throw new Error('shot_box.js runs in a page: no window or document');
    return { win, doc: win.document };
  }

  function contains(a, node) {
    if (a.contains) return a.contains(node);
    for (let n = node; n; n = n.parentNode) if (n === a) return true;
    return false;
  }

  function describe(el) {
    if (!el || !el.tagName) return 'text';
    let s = String(el.tagName).toLowerCase();
    if (el.id) s += '#' + el.id;
    const cls = typeof el.className === 'string' ? el.className.trim().split(/\s+/).filter(Boolean).slice(0, 2) : [];
    if (cls.length) s += '.' + cls.join('.');
    return s;
  }

  // what an element is, for the report of which one a box chose
  function kindOf(el) {
    const tag = String(el.tagName || '').toLowerCase();
    const role = (el.getAttribute && el.getAttribute('role')) || '';
    // a class names a part by its last word, `row-menu` a menu, `card-close` not a card
    const words = typeof el.className === 'string' ? el.className.toLowerCase().split(/\s+/).filter(Boolean) : [];
    const ends = (re) => words.some((w) => re.test(w));
    if (/^(menu|menubar|listbox)$/.test(role) || ends(/(^|[-_])(menu|popover|dropdown|popup)$/)) return 'menu';
    if (role === 'dialog' || role === 'alertdialog' || tag === 'dialog' || ends(/(^|[-_])(dialog|modal|sheet)$/)) return 'dialog';
    if (/^(toolbar|status|banner|navigation|tablist)$/.test(role) || /^(header|footer|nav)$/.test(tag) || ends(/bar$|(^|[-_])rail$/)) return 'bar';
    if (ends(/(^|[-_])(card|tile|panel|notice)$/)) return 'card';
    if (/^(row|listitem|option|menuitem|treeitem)$/.test(role) || /^(tr|li)$/.test(tag) || ends(/(^|[-_])(row|item|entry)$/)) return 'row';
    return 'block';
  }

  function shown(win, el) {
    for (let e = el; e && e.nodeType === 1; e = e.parentNode) {
      const cs = win.getComputedStyle(e);
      if (cs.display === 'none' || cs.visibility === 'hidden' || cs.visibility === 'collapse' || Number(cs.opacity) === 0) return false;
    }
    return true;
  }

  const px = (v) => parseFloat(v) || 0;
  const transparent = (c) => !c || c === 'transparent' || /rgba\([^)]*,\s*0(\.0+)?\s*\)$/.test(c);

  // Everything a box must stay clear of, from the whole page once: each line of text, each picture, each
  // divider and each side of a visible border, with the node it belongs to.
  function obstacles(win, doc) {
    const out = [];
    const range = doc.createRange();
    const walk = (node) => {
      if (node.nodeType === 3) {
        if (!/\S/.test(node.nodeValue || '')) return;
        range.selectNodeContents(node);
        for (const b of Array.from(range.getClientRects())) {
          const r = fromDom(b);
          if (!empty(r)) out.push({ node, what: 'text', r, says: String(node.nodeValue).trim().slice(0, 40) });
        }
        return;
      }
      if (node.nodeType !== 1) return;
      const cs = win.getComputedStyle(node);
      if (cs.display === 'none' || cs.visibility === 'hidden' || Number(cs.opacity) === 0) return;
      const tag = String(node.tagName).toLowerCase();
      const r = fromDom(node.getBoundingClientRect());
      if (!empty(r)) {
        const cls = typeof node.className === 'string' ? node.className.toLowerCase() : '';
        if (/^(img|svg|canvas|video|picture)$/.test(tag) || (node.getAttribute && node.getAttribute('role') === 'img') || /avatar|icon/.test(cls)) {
          out.push({ node, what: 'picture', r, says: describe(node) });
        } else if (tag === 'hr' || ((r.h <= 2 || r.w <= 2) && !transparent(cs.backgroundColor))) {
          out.push({ node, what: 'divider', r, says: describe(node) });
        }
        const side = (name, rect) => {
          const w = px(cs['border' + name + 'Width']);
          const style = cs['border' + name + 'Style'];
          if (w > 0 && style && style !== 'none' && style !== 'hidden' && !transparent(cs['border' + name + 'Color'])) {
            out.push({ node, what: 'border', r: rect(w), says: describe(node) + "'s " + name.toLowerCase() + ' border' });
          }
        };
        side('Top', (w) => ({ x: r.x, y: r.y, w: r.w, h: w }));
        side('Bottom', (w) => ({ x: r.x, y: r.y + r.h - w, w: r.w, h: w }));
        side('Left', (w) => ({ x: r.x, y: r.y, w, h: r.h }));
        side('Right', (w) => ({ x: r.x + r.w - w, y: r.y, w, h: r.h }));
        if (tag === 'svg') return; // a picture's insides are the picture
      }
      for (const c of Array.from(node.childNodes || [])) walk(c);
    };
    walk(doc.body);
    return out;
  }

  // What the box `b` round `el` would cross or touch: anything not inside `el`, a picture lying
  // under the whole of `el` (a board's backdrop) apart, and the border of a bar holding `el`, since a bar is too thin for
  // a button's room: the button keeps its own box while it clears the bar's other buttons and words.
  function clash(el, b, all) {
    const own = fromDom(el.getBoundingClientRect());
    for (const o of all) {
      if (contains(el, o.node)) continue;
      if (!meets(b, o.r)) continue;
      if (o.what === 'picture' && holds(o.r, own)) continue;
      if (o.what === 'border' && contains(o.node, el) && kindOf(o.node) === 'bar') continue;
      return o;
    }
    return null;
  }

  // The sides of `a` a reader sees as its edge: every side when its background stands out from what it sits
  // on or it casts a shadow (a menu, a card, a panel), else each side with a visible border (a section's
  // divider at its foot). A side on or past the window's edge is the window's, which the crop's mat answers.
  const SIDES = ['top', 'right', 'bottom', 'left'];
  function backdropOf(win, el) {
    for (let e = el; e && e.nodeType === 1; e = e.parentNode) {
      const bg = win.getComputedStyle(e).backgroundColor;
      if (!transparent(bg)) return bg;
    }
    return null;
  }
  function markedSides(win, a) {
    const cs = win.getComputedStyle(a);
    const shadow = cs.boxShadow && cs.boxShadow !== 'none';
    const bg = cs.backgroundColor;
    if (shadow || (!transparent(bg) && bg !== backdropOf(win, a.parentNode))) return SIDES.slice();
    return SIDES.filter((s) => {
      const n = s[0].toUpperCase() + s.slice(1);
      const st = cs['border' + n + 'Style'];
      return px(cs['border' + n + 'Width']) > 0 && st && st !== 'none' && st !== 'hidden' && !transparent(cs['border' + n + 'Color']);
    });
  }

  // Each enclosing element of `e` whose edge shows, with the sides a box round `e` must keep 8 pixels inside.
  // A page-sized one is no container, and a bar too thin to hold `e` with room across it keeps its earlier
  // rule: the button's box may cross the bar's long sides while it clears the bar's other buttons and words.
  function containers(win, e, own) {
    const vw = win.innerWidth;
    const vh = win.innerHeight;
    const out = [];
    for (let a = e.parentNode; a && a.nodeType === 1; a = a.parentNode) {
      const r = fromDom(a.getBoundingClientRect());
      if (empty(r) || (r.w > MAX_SPAN * vw && r.h > MAX_SPAN * vh)) continue;
      let sides = markedSides(win, a);
      if (!sides.length) continue;
      const atWindow = { top: r.y <= 1, left: r.x <= 1, bottom: r.y + r.h >= vh - 1, right: r.x + r.w >= vw - 1 };
      sides = sides.filter((s) => !atWindow[s]);
      if (kindOf(a) === 'bar') {
        if (r.w >= r.h && r.h < own.h + 4 * PAD) sides = sides.filter((s) => s !== 'top' && s !== 'bottom');
        if (r.h > r.w && r.w < own.w + 4 * PAD) sides = sides.filter((s) => s !== 'left' && s !== 'right');
      }
      if (sides.length) out.push({ node: a, r, sides });
    }
    return out;
  }

  // The room the box `b` leaves inside each of `edges` on its sides, and the first side under PAD.
  function tightEdge(b, edges) {
    for (const c of edges) {
      const room = { top: b.y - c.r.y, left: b.x - c.r.x, bottom: c.r.y + c.r.h - (b.y + b.h), right: c.r.x + c.r.w - (b.x + b.w) };
      for (const s of c.sides) if (room[s] < PAD) return { c, side: s, room: room[s] };
    }
    return null;
  }

  function resolve(doc, target) {
    if (target && typeof target === 'object' && target.nodeType === 1) return target;
    const el = doc.querySelector(String(target));
    return el || null;
  }

  // The box round `target` (a selector or an element), or the nearest larger enclosing one that clears.
  function shotBox(target, opts) {
    const o = opts || {};
    const { win, doc } = env(o);
    const pad = o.pad === undefined ? PAD : o.pad;
    const of = typeof target === 'string' ? target : describe(target);
    const el = resolve(doc, target);
    if (!el) return { of, problem: 'nothing on the page matches ' + of };
    if (!shown(win, el)) return { of, problem: of + ' is hidden' };
    const all = o.obstacles || obstacles(win, doc);
    const vw = win.innerWidth;
    const vh = win.innerHeight;
    let last = null;
    let nearest = null;
    let container = null; // the last enclosing element whose edge made the box climb to it
    for (let e = el, step = 0; e && e.nodeType === 1; e = e.parentNode, step++) {
      const r = fromDom(e.getBoundingClientRect());
      if (empty(r)) continue;
      if (last && r.w <= last.w + 1 && r.h <= last.h + 1) continue; // a wrapper the same size adds nothing
      if (step > 0 && (r.w > MAX_SPAN * vw && r.h > MAX_SPAN * vh)) break; // the whole page is no box
      last = r;
      const b = inflate(r, pad);
      const hit = clash(e, b, all);
      const edges = containers(win, e, r);
      const tight = tightEdge(b, edges);
      const chose = e === el ? 'element' : kindOf(e);
      if (!hit && !tight) {
        const done = Object.assign(round(b), { of, chose, element: describe(e), climbed: step });
        if (container) done.container = container.says;
        done.edges = edges.map((c) => Object.assign(round(c.r), { of: kindOf(c.node) + ' ' + describe(c.node), sides: c.sides }));
        return done;
      }
      if (tight) {
        // the box sits on or near an edge of what holds it: the climb goes on to that container, since
        // everything between holds the element as near the same edge
        if (!container || container.node !== tight.c.node) {
          container = { node: tight.c.node, says: kindOf(tight.c.node) + ' ' + describe(tight.c.node) + ' (the room round ' + describe(e) + ' ' +
            Math.round(tight.room) + 'px from its ' + tight.side + ' edge)' };
        }
      }
      nearest = { e, hit, tight };
      if (e === doc.body) break;
    }
    const n = nearest;
    const why = !n ? 'the page' : n.hit ? n.hit.what + ' "' + n.hit.says + '"' :
      describe(n.tight.c.node) + "'s " + n.tight.side + ' edge, ' + Math.round(n.tight.room) + 'px from it';
    return {
      of,
      problem: 'no box round ' + of + ' clears its neighbours: the last tried, ' + describe(n ? n.e : el) +
        ', would touch ' + why + ': shoot it with more room round it, or box a part of its own',
    };
  }

  // Elements a crop must not cut: cards, rows, menus, bars and dialogs, each no longer along a side than
  // MAX_SPAN of the window, so a full-width bar is cut at its ends but never through its height.
  function units(win, doc) {
    const out = [];
    const walk = (node) => {
      if (node.nodeType !== 1) return;
      const cs = win.getComputedStyle(node);
      if (cs.display === 'none' || cs.visibility === 'hidden') return;
      let kind = kindOf(node);
      if (kind === 'block') {
        const sides = ['Top', 'Right', 'Bottom', 'Left'].filter((s) => px(cs['border' + s + 'Width']) > 0 &&
          cs['border' + s + 'Style'] && cs['border' + s + 'Style'] !== 'none' && !transparent(cs['border' + s + 'Color']));
        if (sides.length >= 3) kind = 'card'; // a box with a border reads as a card whatever its class
      }
      if (kind !== 'block') {
        const r = fromDom(node.getBoundingClientRect());
        if (!empty(r)) out.push({ node, kind, r });
      }
      for (const c of Array.from(node.childNodes || [])) walk(c);
    };
    walk(doc.body);
    return out;
  }

  const cutOn = (crop, r) => ({
    x: (r.x < crop.x && r.x + r.w > crop.x) || (r.x < crop.x + crop.w && r.x + r.w > crop.x + crop.w),
    y: (r.y < crop.y && r.y + r.h > crop.y) || (r.y < crop.y + crop.h && r.y + r.h > crop.y + crop.h),
  });
  const overlapsInside = (crop, r) => r.x < crop.x + crop.w && r.x + r.w > crop.x && r.y < crop.y + crop.h && r.y + r.h > crop.y;

  // A crop holding every box with `margin` round it, grown so no card, row or menu is cut at an edge,
  // inside the window. Its problems: a box too near the window's edge for room, or a part the window cuts.
  function shotCrop(boxes, margin, opts) {
    const o = opts || {};
    const { win, doc } = env(o);
    const m = margin === undefined || margin === null ? MARGIN : margin;
    const good = (boxes || []).filter((b) => b && !b.problem);
    const problems = [];
    if (!good.length) return { x: 0, y: 0, w: 0, h: 0, grown: [], problems: ['no box to crop round'] };
    const vw = win.innerWidth;
    const vh = win.innerHeight;
    const clamp = (r) => {
      const x = Math.max(0, r.x);
      const y = Math.max(0, r.y);
      return { x, y, w: Math.min(vw, r.x + r.w) - x, h: Math.min(vh, r.y + r.h) - y };
    };
    let crop = clamp(inflate(union(good.map(r4)), m));
    const parts = o.units || units(win, doc);
    const grown = [];
    const cut = [];
    for (let round_ = 0; round_ < 12; round_++) {
      let changed = false;
      for (const u of parts) {
        if (!overlapsInside(crop, u.r)) continue;
        const c = cutOn(crop, u.r);
        const grow = {};
        if (c.x && u.r.w <= MAX_SPAN * vw) grow.x = true;
        if (c.y && u.r.h <= MAX_SPAN * vh) grow.y = true;
        if (!grow.x && !grow.y) continue;
        const want = {
          x: grow.x ? Math.min(crop.x, u.r.x) : crop.x,
          y: grow.y ? Math.min(crop.y, u.r.y) : crop.y,
        };
        want.w = (grow.x ? Math.max(crop.x + crop.w, u.r.x + u.r.w) : crop.x + crop.w) - want.x;
        want.h = (grow.y ? Math.max(crop.y + crop.h, u.r.y + u.r.h) : crop.y + crop.h) - want.y;
        const next = clamp(want);
        if (next.x !== crop.x || next.y !== crop.y || next.w !== crop.w || next.h !== crop.h) {
          crop = next;
          changed = true;
          grown.push(u.kind + ' ' + describe(u.node));
        }
      }
      if (!changed) break;
    }
    for (const u of parts) {
      if (!overlapsInside(crop, u.r)) continue;
      const c = cutOn(crop, u.r);
      if ((c.x && u.r.w <= MAX_SPAN * vw) || (c.y && u.r.h <= MAX_SPAN * vh)) {
        const where = [];
        if (u.r.x < crop.x) where.push('left');
        if (u.r.x + u.r.w > crop.x + crop.w) where.push('right');
        if (u.r.y < crop.y) where.push('top');
        if (u.r.y + u.r.h > crop.y + crop.h) where.push('bottom');
        cut.push(u.kind + ' ' + describe(u.node) + ' (' + where.join(', ') + ')');
      }
    }
    if (cut.length) problems.push('the window cuts ' + cut.join(', ') + ': scroll it in, or shoot a larger window');
    // a box the window's edge leaves without its room (a full-width bar's, a top bar's) is no fault of the
    // capture: the composite gives it a mat, --pad, of at least 16
    let pad = 0;
    const notes = [];
    for (const b of good) {
      const room = Math.min(b.x - crop.x, b.y - crop.y, crop.x + crop.w - (b.x + b.w), crop.y + crop.h - (b.y + b.h));
      if (room < PAD) {
        const want = Math.max(16, Math.ceil(PAD - room));
        pad = Math.max(pad, want);
        notes.push('the box round ' + b.of + ' is flush with the window\'s edge (' + Math.round(room) + 'px of room): compose with --pad ' + want);
      }
    }
    // a crop as wide as the window is a bar to show whole: shoot it at scale 1 and compose it with --whole
    if (crop.w >= vw - 1) notes.push('the crop spans the window: shoot at 1280 wide and device scale 1, compose with --whole');
    return Object.assign(round(crop), { grown, problems, pad, notes });
  }

  // The smallest text drawn inside `crop`, in CSS pixels as it shows, a transform's scale included.
  function shotMinText(crop, opts) {
    const o = opts || {};
    const { win, doc } = env(o);
    const range = doc.createRange();
    let best = null;
    let count = 0;
    const walk = (node) => {
      if (node.nodeType === 3) {
        if (!/\S/.test(node.nodeValue || '')) return;
        const el = node.parentNode;
        range.selectNodeContents(node);
        const rects = Array.from(range.getClientRects()).map(fromDom).filter((r) => !empty(r) && overlapsInside(crop, r));
        if (!rects.length) return;
        const cs = win.getComputedStyle(el);
        if (transparent(cs.color)) return;
        const box = fromDom(el.getBoundingClientRect());
        // a transform's scale, from the drawn width over the laid-out one, which is whole pixels, so a
        // difference under 3 percent is rounding, not a scale
        const ratio = el.offsetWidth > 0 && box.w > 0 ? box.w / el.offsetWidth : 1;
        const scale = Math.abs(ratio - 1) < 0.03 ? 1 : ratio;
        const size = Math.round(px(cs.fontSize) * scale * 10) / 10;
        if (!(size > 0)) return;
        count++;
        if (!best || size < best.px) best = { px: size, text: String(node.nodeValue).trim().slice(0, 40), in: describe(el) };
        return;
      }
      if (node.nodeType !== 1) return;
      const cs = win.getComputedStyle(node);
      if (cs.display === 'none' || cs.visibility === 'hidden' || Number(cs.opacity) === 0) return;
      for (const c of Array.from(node.childNodes || [])) walk(c);
    };
    walk(doc.body);
    return best ? Object.assign(best, { count }) : { px: null, text: '', in: '', count: 0 };
  }

  // Everything a capture writes beside its PNG: the boxes in the crop's coordinates, the crop, the smallest
  // text, the device scale and every problem, which review_shot.js refuses.
  function shotPlan(targets, opts) {
    const o = Object.assign({}, opts || {});
    const { win, doc } = env(o);
    o.obstacles = obstacles(win, doc);
    o.units = units(win, doc);
    const list = Array.isArray(targets) ? targets : [targets];
    const boxes = list.map((t) => shotBox(t, o));
    const problems = boxes.filter((b) => b.problem).map((b) => b.problem);
    const crop = shotCrop(boxes, o.margin, o);
    problems.push(...crop.problems);
    const good = boxes.filter((b) => !b.problem);
    for (let i = 0; i < good.length; i++) {
      for (let j = i + 1; j < good.length; j++) {
        if (meets(good[i], good[j])) problems.push('the boxes round ' + good[i].of + ' and ' + good[j].of + ' overlap: box their shared row or card once');
      }
    }
    const minText = shotMinText(crop, o);
    return {
      tool: 'shot_box',
      scale: win.devicePixelRatio || 1,
      viewport: { w: win.innerWidth, h: win.innerHeight },
      crop: { x: crop.x, y: crop.y, w: crop.w, h: crop.h },
      grown: crop.grown,
      pad: crop.pad,
      notes: crop.notes,
      boxes: good.map((b) => {
        const at = (v, o) => Math.round((v - o) * 10) / 10;
        const out = { x: at(b.x, crop.x), y: at(b.y, crop.y), w: b.w, h: b.h, of: b.of, chose: b.chose, element: b.element };
        if (b.container) out.container = b.container;
        // the edges round the box, in the crop's coordinates, which review_shot.js holds it 8 pixels inside
        out.edges = (b.edges || []).map((c) => ({ x: at(c.x, crop.x), y: at(c.y, crop.y), w: c.w, h: c.h, of: c.of, sides: c.sides }));
        return out;
      }),
      minText,
      problems,
    };
  }

  const api = { PAD, MARGIN, MAX_SPAN, shotBox, shotCrop, shotMinText, shotPlan, kindOf, markedSides };
  if (typeof module !== 'undefined' && module.exports) module.exports = api;
  else Object.assign(root, api);
})(typeof window !== 'undefined' ? window : globalThis);
