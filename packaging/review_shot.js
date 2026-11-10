// A review shot that explains itself (18 October 2026, the reviewshot build), in the format Harbour's
// scripts/lib/review-shot.ts makes: a heading band saying what changed and "Check:" with what to look at,
// above the shot, or above a Before and an After side by side, stacked when a panel is wider than twice its
// height, both at one scale and labelled, with a dashed box round the changed part on each. Beside the PNG
// goes `<name>.caption.json`, which the pack reads to list every shot's heading in order.
//
//     osascript -l JavaScript packaging/review_shot.js --out <review>/01-notes.png \
//         --before <raw>/notes-before.png --after <raw>/notes-after.png \
//         --changed "Notes column: wider" --check "the notes wrap without a scroll bar" \
//         --boxes-from-before <raw>/notes-before.shot.json --boxes-from-after <raw>/notes-after.shot.json
//     osascript -l JavaScript packaging/review_shot.js pack <review>
//
// --before and --changed go together, and a shot with no before takes --shows, a line saying what it
// shows, then --check. The boxes come from the capture's sidecar, `<raw>.shot.json`, which
// packaging/shot_box.js measures in the page (20 October, the shotlint build): --boxes-from marks both
// panels, --boxes-from-before and --boxes-from-after one each, and the sidecar's device scale is the
// shot's. --box x,y,w,h, --box-before and --box-after still take boxes by hand, in the shot's own pixels at
// --scale 1 (CSS pixels when the shots were taken at --scale 2). --stack or --side overrides the layout.
// --whole (or a sidecar whose notes say the crop "spans the window") is for a full-width bar shot at the window's
// width at device scale 1 (26 October, bump097): Before stacked above After, and the smallest text held to 10
// pixels at its real size, not at 900 wide, since a bar is read zoomed in. The 1,400 pixel limit stays, which
// a 1280 bar and its mat keep under. Everything else is shot at scale 2 as before.
// --pad N draws a mat of N pixels in the page's colour round each shot, its own edge kept as a thin line,
// for a box flush with the window's edge (a full-width bar's): its 8 pixels count from the mat's edge, and a
// sidecar that asks for a mat refuses a composite without it.
//
// It refuses, exit 1 with the reason, the faults review checks kept finding: a box within 8 pixels of its
// panel's edge, two boxes overlapping on a panel, a composite over 1,400 pixels wide, and, when a sidecar
// is there (given, or beside a raw shot under its name), a capture's own problems, a sidecar made for
// another crop, a box under 8 pixels inside the edge of the menu, card, panel or section it sits in (the
// sidecar's `edges`, since the shotlint2 build), and text that would show under 12 pixels with the
// composite shown 900 wide. The pack
// prints `name.png: heading` for each shot in the folder in the order of their names, and refuses, exit 1,
// a shot with no caption file or one that reads wrong.
//
// AppKit draws it offscreen, as heading.js does, so nothing is installed and no screen is read. The layout
// maths, the caption, the boxes, the refusals and the pack are pure functions, and the same file runs in
// node for the suite's checks (area 183) and for the pack, `node packaging/review_shot.js pack <review>`.
// In node a shot goes through every refusal and stops only at the drawing.

const MIN_HEADING_PX = 20; // below this a heading is hard to read even at full size
const HEADING_RATIO = 46; // the heading is 1/46 of the composite's width, so it reads when a chat pane scales it down
const STACK_ASPECT = 2; // a panel wider than twice its height stacks, since two side by side make a thin strip
const MAX_RENDER_PX = 16000; // the longest side drawn, past which the render scale comes down
const EDGE_CLEAR = 8; // a box keeps this much of its panel clear on every side
const MAX_COMPOSITE_PX = 1400; // the widest composite, in its own pixels
const MIN_WHOLE_TEXT = 10; // the smallest text, in pixels, of a bar shown whole at its real size
const SHOWN_WIDTH = 900; // the width a chat pane shows a composite at
const MIN_SHOWN_TEXT = 12; // the smallest text, in pixels, at that width
const HEADING_LINE = 1.3; // the heading's line height over its size, fixed so measuring and drawing agree

const COLOURS = {
  page: [0xe8, 0xeb, 0xee], band: [0x1c, 0x27, 0x33], text: [0xff, 0xff, 0xff], check: [0xff, 0xd2, 0x7a],
  before: [0xc9, 0xce, 0xd4], beforeInk: [0x2b, 0x33, 0x3b], after: [0x0f, 0x76, 0x6e], afterInk: [0xff, 0xff, 0xff],
  edge: [0xb7, 0xbe, 0xc6], mark: [0xe6, 0x00, 0x7e], halo: [0xff, 0xff, 0xff],
};

function fail(message) {
  const e = new Error(message);
  e.refused = true;
  return e;
}

// Where everything goes, in CSS pixels. `after` and `before` are the PNGs' own pixels, `scale` the device
// scale they were shot at (1 unless they were taken at 2). The heading is 1/46 of the composite's width,
// the width the gutters make with it, never under 20 pixels. `pad` is a mat round each shot, in CSS pixels,
// part of its panel: `before` and `after` are the panels' sizes, the mat in them.
function layout(after, before, opts) {
  const o = opts || {};
  const scale = o.scale === undefined ? 1 : o.scale;
  const pad = o.pad === undefined ? 0 : o.pad;
  const whole = !!o.whole;
  if (!(scale > 0)) throw fail('the scale must be above 0, not ' + scale);
  if (!(pad >= 0)) throw fail('--pad must be 0 or more, not ' + pad);
  const css = (s) => ({ width: s.width / scale + 2 * pad, height: s.height / scale + 2 * pad });
  const a = css(after);
  const b = before ? css(before) : null;
  let arrangement = 'single';
  if (b) {
    const wide = Math.max(a.width, b.width);
    const tall = Math.max(a.height, b.height);
    arrangement = whole ? 'stacked' : o.arrange || (wide > STACK_ASPECT * tall ? 'stacked' : 'side');
  }
  const panels = arrangement === 'side' ? a.width + b.width : Math.max(a.width, b ? b.width : 0);
  const gutters = arrangement === 'side' ? 3 : 2;
  const gutterOf = (h) => Math.max(16, Math.round(h * 0.6));
  const widthOf = (h) => Math.ceil(panels + gutters * gutterOf(h));
  // the heading read off the whole width, gutters and all: the width grows with the heading, so a few
  // rounds settle it, and the rule never goes down, so it always does
  let headingPx = Math.max(MIN_HEADING_PX, Math.round(panels / HEADING_RATIO));
  for (let i = 0; i < 8; i++) {
    const next = Math.max(MIN_HEADING_PX, Math.round(widthOf(headingPx) / HEADING_RATIO));
    if (next === headingPx) break;
    headingPx = next;
  }
  const labelPx = Math.max(16, Math.round(headingPx * 0.75));
  return {
    arrangement, scale, pad, whole, before: b, after: a, gutter: gutterOf(headingPx), headingPx, labelPx,
    width: widthOf(headingPx), line: Math.max(3, Math.round(headingPx / 7)),
  };
}

// Every rectangle of the composite, in CSS pixels from its top left, once the heading's text is measured
// at `textHeight` CSS pixels. The label pills' widths come from their text, so a label gives its place and
// height alone.
function place(l, textHeight) {
  const g = l.gutter;
  const band = Math.ceil(textHeight + 2 * g);
  const padY = Math.round(l.labelPx * 0.35);
  const pill = l.labelPx + 2 * padY;
  const labelBlock = pill + Math.round(l.labelPx * 0.5);
  const top = band + g;
  const panels = [];
  if (l.arrangement === 'single') {
    panels.push({ name: 'after', label: null, image: { x: g, y: top, w: l.after.width, h: l.after.height } });
  } else if (l.arrangement === 'side') {
    panels.push({ name: 'before', label: { x: g, y: top, h: pill, padY, padX: Math.round(l.labelPx * 0.6) },
      image: { x: g, y: top + labelBlock, w: l.before.width, h: l.before.height } });
    const x = g + l.before.width + g;
    panels.push({ name: 'after', label: { x, y: top, h: pill, padY, padX: Math.round(l.labelPx * 0.6) },
      image: { x, y: top + labelBlock, w: l.after.width, h: l.after.height } });
  } else {
    panels.push({ name: 'before', label: { x: g, y: top, h: pill, padY, padX: Math.round(l.labelPx * 0.6) },
      image: { x: g, y: top + labelBlock, w: l.before.width, h: l.before.height } });
    const y = top + labelBlock + l.before.height + g;
    panels.push({ name: 'after', label: { x: g, y, h: pill, padY, padX: Math.round(l.labelPx * 0.6) },
      image: { x: g, y: y + labelBlock, w: l.after.width, h: l.after.height } });
  }
  const bottom = Math.max(...panels.map((p) => p.image.y + p.image.h));
  const height = Math.ceil(bottom + g);
  const longest = Math.max(l.width, height);
  const renderScale = Math.min(l.scale, Math.floor((MAX_RENDER_PX / longest) * 100) / 100);
  return { width: l.width, height, band, text: { x: g, y: g, w: l.width - 2 * g, h: textHeight }, panels, renderScale };
}

// `x,y,w,h` as four numbers, or why not.
function parseBox(text) {
  const parts = String(text).split(',').map((s) => s.trim());
  const nums = parts.map(Number);
  if (parts.length !== 4 || parts.some((s) => s === '') || nums.some((n) => !isFinite(n))) {
    throw fail('a box is x,y,w,h, four numbers, not "' + text + '"');
  }
  if (nums[2] <= 0 || nums[3] <= 0) throw fail('a box needs a width and a height above 0, not "' + text + '"');
  return nums;
}

// The dashes of a box's outline, as filled rectangles inside `r`, `line` thick: each side starts and ends
// on a corner, so every corner is marked, with the gaps evened out between.
function dashes(r, line) {
  const dash = 3 * line;
  const gap = 2 * line;
  const out = [];
  const along = (len, put) => {
    if (len <= dash + gap) return put(0, len);
    const n = Math.max(2, Math.round((len + gap) / (dash + gap)));
    const step = (len - dash) / (n - 1);
    for (let i = 0; i < n; i++) put(i * step, dash);
  };
  along(r.w, (at, len) => {
    out.push({ x: r.x + at, y: r.y, w: len, h: line });
    out.push({ x: r.x + at, y: r.y + r.h - line, w: len, h: line });
  });
  along(r.h, (at, len) => {
    out.push({ x: r.x, y: r.y + at, w: line, h: len });
    out.push({ x: r.x + r.w - line, y: r.y + at, w: line, h: len });
  });
  return out;
}

// Whitespace collapsed and a "Check:" the caller wrote taken off, or a refusal: every shot needs a check
// and a first line, a before what changed (--changed), a shot with no before what it shows (--shows).
function normaliseCaption(c, hasBefore) {
  const tidy = (s) => String(s).replace(/\s+/g, ' ').trim();
  const changed = c.changed == null ? '' : tidy(c.changed);
  const shows = c.shows == null ? '' : tidy(c.shows);
  const check = c.check == null ? '' : tidy(c.check).replace(/^check:\s*/i, '');
  if (check === '') throw fail('a review shot needs --check, what to look at');
  if (hasBefore && changed === '') throw fail('a Before and After needs --changed, what changed between them');
  if (hasBefore && shows !== '') throw fail('a Before and After says what changed with --changed, not --shows');
  if (!hasBefore && changed !== '') throw fail('a shot with no --before says what it shows with --shows, not --changed');
  if (!hasBefore && shows === '') throw fail('a shot with no --before needs --shows, a line saying what it shows, then --check');
  return hasBefore ? { changed, check } : { changed: null, shows, check };
}

// The heading as one line, what the pack prints and a report repeats.
function headingText(c) {
  const first = c.changed != null ? c.changed : c.shows ? c.shows : '';
  const lead = first === '' ? '' : /[.!?]$/.test(first) ? first + ' ' : first + '. ';
  return lead + 'Check: ' + c.check;
}

// `01-notes.png` to `01-notes.caption.json`, beside it.
function captionPath(png) {
  return png.replace(/\.[^./]+$/, '') + '.caption.json';
}

function captionFile(c, l, boxes) {
  const f = { changed: c.changed, check: c.check, beforeAfter: l.arrangement !== 'single', arrangement: l.arrangement, boxes };
  if (c.shows) f.shows = c.shows;
  return f;
}

// A caption file's text as a caption, or why not.
function parseCaptionFile(text) {
  let d;
  try {
    d = JSON.parse(text);
  } catch (e) {
    return 'is not JSON';
  }
  if (typeof d !== 'object' || d === null || Array.isArray(d)) return 'is not an object';
  if (typeof d.check !== 'string' || d.check.trim() === '') return 'has no check';
  if (d.changed !== null && typeof d.changed !== 'string') return 'has no changed (null when there is no before)';
  if (d.beforeAfter === true && (d.changed === null || d.changed.trim() === '')) return 'is a Before and After with no changed';
  if (d.shows !== undefined && typeof d.shows !== 'string') return 'has a shows that is not words';
  const c = { changed: d.changed, check: d.check, beforeAfter: d.beforeAfter === true, arrangement: d.arrangement || 'single' };
  if (d.shows) c.shows = d.shows;
  return c;
}

// The pack of a folder, from its file names and a reader that gives a file's text or null: each shot's
// line in the order of the names, and the problems, a shot with no caption or one that reads wrong, a
// caption with no shot, or a folder with no shots.
function pack(names, readText) {
  const sorted = names.slice().sort((a, b) => (a < b ? -1 : a > b ? 1 : 0));
  const shots = sorted.filter((n) => /\.png$/i.test(n));
  const lines = [];
  const problems = [];
  if (shots.length === 0) problems.push('no shots (.png) in the folder');
  for (const name of shots) {
    const sidecar = captionPath(name);
    const text = readText(sidecar);
    if (text === null) {
      problems.push(name + ' has no heading (no ' + sidecar + '): make it with packaging/review_shot.js');
      continue;
    }
    const c = parseCaptionFile(text);
    if (typeof c === 'string') {
      problems.push(sidecar + ' ' + c + ': make the shot again with packaging/review_shot.js');
      continue;
    }
    lines.push(name + ': ' + headingText(c));
  }
  for (const name of sorted.filter((n) => /\.caption\.json$/.test(n))) {
    const png = name.replace(/\.caption\.json$/, '.png');
    if (!sorted.includes(png)) problems.push(name + ' has no shot beside it (no ' + png + ')');
  }
  return { lines, problems };
}

// The command line as options, or a refusal.
function parseArgs(argv) {
  const args = argv.slice();
  if (args[0] === 'pack') {
    if (args.length !== 2) throw fail('usage: review_shot.js pack <folder>');
    return { mode: 'pack', folder: args[1] };
  }
  const o = { mode: 'shot', boxes: { both: [], before: [], after: [] }, boxesFrom: { both: null, before: null, after: null }, arrange: null, scale: null, pad: 0, whole: false };
  const valued = { '--out': 'out', '--after': 'after', '--before': 'before', '--changed': 'changed', '--shows': 'shows', '--check': 'check', '--scale': 'scale', '--pad': 'pad' };
  for (let i = 0; i < args.length; i++) {
    const a = args[i];
    if (a === '--whole') {
      o.whole = true;
      continue;
    }
    if (a === '--stack' || a === '--side') {
      o.arrange = a === '--stack' ? 'stacked' : 'side';
      continue;
    }
    const boxKind = { '--box': 'both', '--box-before': 'before', '--box-after': 'after' }[a];
    const fromKind = { '--boxes-from': 'both', '--boxes-from-before': 'before', '--boxes-from-after': 'after' }[a];
    if (!(a in valued) && !boxKind && !fromKind) throw fail('no option ' + a + ' (see the head of review_shot.js)');
    if (i + 1 >= args.length) throw fail(a + ' needs a value');
    const v = args[++i];
    if (boxKind) o.boxes[boxKind].push(parseBox(v));
    else if (fromKind) {
      if (o.boxesFrom[fromKind]) throw fail(a + ' is given twice: one sidecar a panel');
      o.boxesFrom[fromKind] = v;
    } else if (a === '--scale') o.scale = Number(v);
    else if (a === '--pad') {
      if (!/^\d+$/.test(v)) throw fail('--pad is a whole number of pixels, not ' + v);
      o.pad = Number(v);
    }
    else o[valued[a]] = v;
  }
  if (!o.out || !o.after) throw fail('usage: review_shot.js --out x.png --after a.png [--before b.png --changed "..." | --shows "..."] --check "..." [--boxes-from a.shot.json | --box x,y,w,h]');
  if (!/\.png$/i.test(o.out)) throw fail('--out must be a .png, not ' + o.out);
  if (!o.before && o.boxes.before.length) throw fail('--box-before needs a --before');
  if (!o.before && o.boxesFrom.before) throw fail('--boxes-from-before needs a --before');
  if (o.whole && o.arrange === 'side') throw fail('--whole stacks Before above After: leave out --side');
  if (!o.before && o.arrange) throw fail('--stack and --side need a --before');
  return o;
}

// `notes-after.png` to `notes-after.shot.json`, the capture's sidecar beside its raw shot.
function sidecarPath(png) {
  return png.replace(/\.[^./]+$/, '') + '.shot.json';
}

// A sidecar's text (what shot_box.js's shotPlan gives) as the parts the composite uses, or a refusal.
function parseSidecar(text, path) {
  let d;
  try {
    d = JSON.parse(text);
  } catch (e) {
    throw fail(path + ' is not JSON: write shotPlan\'s result as it comes');
  }
  const num = (v) => typeof v === 'number' && isFinite(v);
  if (typeof d !== 'object' || d === null || Array.isArray(d)) throw fail(path + ' is not a shot_box sidecar (not an object)');
  if (!d.crop || !num(d.crop.w) || !num(d.crop.h)) throw fail(path + ' has no crop: write shotPlan\'s result as it comes');
  if (!Array.isArray(d.boxes) || d.boxes.some((b) => !b || !num(b.x) || !num(b.y) || !num(b.w) || !num(b.h) || b.w <= 0 || b.h <= 0)) {
    throw fail(path + ' has no boxes, or a box that is not x, y, w and h');
  }
  if (d.scale !== undefined && !(num(d.scale) && d.scale > 0)) throw fail(path + ' has a scale that is not a number above 0');
  const problems = Array.isArray(d.problems) ? d.problems.map(String) : [];
  const minText = d.minText && num(d.minText.px) ? { px: d.minText.px, text: String(d.minText.text || '') } : null;
  const pad = num(d.pad) && d.pad > 0 ? d.pad : 0;
  const notes = Array.isArray(d.notes) ? d.notes.map(String) : [];
  return {
    notes, path, crop: { w: d.crop.w, h: d.crop.h }, scale: d.scale === undefined ? null : d.scale, problems, minText, pad,
    boxes: d.boxes.map((b) => ({
      box: [b.x, b.y, b.w, b.h], of: b.of ? String(b.of) : '',
      edges: (Array.isArray(b.edges) ? b.edges : []).filter((c) => c && num(c.x) && num(c.y) && num(c.w) && num(c.h) && Array.isArray(c.sides))
        .map((c) => ({ x: c.x, y: c.y, w: c.w, h: c.h, of: String(c.of || 'its container'), sides: c.sides.map(String) })),
    })),
  };
}

// A sidecar's boxes held 8 pixels inside the edges of what each sits in, the menu, card, panel or section
// shotBox found round it: a box on or near one is refused, as a box near the panel's edge is.
function edgeRoom(s) {
  for (const b of s.boxes) {
    const [x, y, w, h] = b.box;
    for (const c of b.edges) {
      const room = { top: y - c.y, left: x - c.x, bottom: c.y + c.h - (y + h), right: c.x + c.w - (x + w) };
      for (const side of c.sides) {
        if (!(side in room) || room[side] >= EDGE_CLEAR - 0.01) continue;
        throw fail(s.path + ': the box ' + (b.of ? 'round ' + b.of : b.box.join(',')) + ' comes ' + Math.round(room[side] * 10) / 10 +
          'px inside the ' + side + ' edge of ' + c.of + ', under the ' + EDGE_CLEAR + ' it needs: box that whole ' +
          c.of.split(' ')[0] + ' instead (shotBox in packaging/shot_box.js climbs to it), never by hand');
      }
    }
  }
}

// The scale the shots were taken at: --scale, else the sidecars' (which must agree), else 1.
function resolveScale(given, sidecars) {
  const said = sidecars.filter((s) => s && s.scale !== null);
  for (const s of said) {
    if (given !== null && s.scale !== given) throw fail(s.path + ' was shot at device scale ' + s.scale + ', not the --scale ' + given + ' given: leave --scale out');
    if (s.scale !== said[0].scale) throw fail(said[0].path + ' and ' + s.path + ' were shot at different device scales, ' + said[0].scale + ' and ' + s.scale + ': shoot Before and After alike');
  }
  if (given !== null) return given;
  return said.length ? said[0].scale : 1;
}

// The pad the tool puts round a box given by hand. A sidecar's box has its room already.
function handPad(l) {
  return l.line + Math.max(2, Math.round(l.gutter / 6));
}

// Each panel's boxes as rectangles of the panel, from the hand boxes and the sidecars', checked: inside
// the shot, 8 pixels clear of its edges, and never over another box. `sidecars` holds the sidecar given
// for both panels and each panel's own.
function panelBoxes(o, l, sidecars) {
  const out = {};
  const pad = handPad(l);
  for (const name of l.before ? ['before', 'after'] : ['after']) {
    const panel = name === 'before' ? l.before : l.after;
    const mat = l.pad || 0;
    const size = { width: panel.width - 2 * mat, height: panel.height - 2 * mat }; // the shot, the mat round it
    const entries = [];
    for (const box of o.boxes.both.concat(o.boxes[name])) entries.push({ box, pad, label: box.join(',') });
    for (const s of [sidecars.both, sidecars[name]]) {
      if (!s) continue;
      for (const b of s.boxes) entries.push({ box: b.box, pad: 0, label: b.of ? 'round ' + b.of : b.box.join(',') });
    }
    const rects = [];
    for (const e of entries) {
      const [x, y, w, h] = e.box;
      const slack = 0.5;
      if (x < -mat - slack || y < -mat - slack || x + w > size.width + mat + slack || y + h > size.height + mat + slack) {
        throw fail('the box ' + e.box.join(',') + ' runs past the ' + name + ' shot' + (mat ? ' and its mat' : '') + ', which is ' +
          Math.round(size.width) + ' by ' + Math.round(size.height) + ' (at --scale ' + l.scale + (mat ? ', --pad ' + mat : '') + ')');
      }
      // in the panel's coordinates, the mat in them, so the 8 pixels count from the padded edge
      const r = { x: x - e.pad + mat, y: y - e.pad + mat, w: w + 2 * e.pad, h: h + 2 * e.pad };
      const room = { left: r.x, top: r.y, right: panel.width - (r.x + r.w), bottom: panel.height - (r.y + r.h) };
      const side = Object.keys(room).reduce((a, b) => (room[b] < room[a] ? b : a));
      if (room[side] < EDGE_CLEAR - 0.01) {
        throw fail('the box ' + e.label + ' on the ' + name + ' shot comes ' + Math.max(0, Math.round(room[side] * 10) / 10) +
          'px from its ' + side + ' edge, under the ' + EDGE_CLEAR + ' it needs: shoot the crop with more room round it (shotCrop in packaging/shot_box.js)' +
          (mat ? '' : ', or, at the window\'s edge, --pad 16'));
      }
      for (const q of rects) {
        if (r.x < q.r.x + q.r.w && q.r.x < r.x + r.w && r.y < q.r.y + q.r.h && q.r.y < r.y + r.h) {
          throw fail('the boxes ' + q.label + ' and ' + e.label + ' on the ' + name + ' shot overlap: box the row or card that holds both, once');
        }
      }
      rects.push({ r, label: e.label, box: e.box, pad: e.pad });
    }
    out[name] = rects;
  }
  return out;
}

// The refusals that read the whole composite: its width, and with a sidecar, its smallest text as shown.
function lintComposite(l, texts) {
  const px = Math.round(l.width * l.scale);
  if (px > MAX_COMPOSITE_PX) {
    throw fail('the composite would be ' + px + ' pixels wide, over ' + MAX_COMPOSITE_PX.toLocaleString('en-GB') + ': crop tighter' +
      (l.arrangement === 'side' ? ', or --stack the pair' : ''));
  }
  for (const name of ['before', 'after']) {
    const t = texts[name];
    if (!t) continue;
    const shown = l.whole ? Math.round(t.px * l.scale * 10) / 10 : Math.round((t.px * l.scale * SHOWN_WIDTH) / px * 10) / 10;
    const least = l.whole ? MIN_WHOLE_TEXT : MIN_SHOWN_TEXT;
    if (shown < least) {
      throw fail('the smallest text in the ' + name + ' shot, ' + t.px + 'px' + (t.text ? ' ("' + t.text + '")' : '') + ', would show at ' +
        shown + 'px ' + (l.whole ? 'at its real size' : 'with the composite shown ' + SHOWN_WIDTH + ' wide') + ', under ' + least + ': crop tighter' +
        (l.arrangement === 'side' ? ', or --stack the pair' : ''));
    }
  }
}

// Each panel's boxes placed on the composite, and the caption's list of them.
function placeBoxes(boxes, l, p) {
  const out = { before: [], after: [] };
  const rects = [];
  for (const panel of p.panels) {
    for (const b of boxes[panel.name] || []) {
      rects.push({ x: panel.image.x + b.r.x, y: panel.image.y + b.r.y, w: b.r.w, h: b.r.h });
      out[panel.name].push(b.box.join(','));
    }
  }
  return { boxes: out, rects };
}

// ── the command, through an `io` of the machine it runs on

// a path from the root, a Windows drive's or a share's as well, where node runs the pack
function absolute(path, cwd) {
  return /^(\/|[A-Za-z]:[\\/]|\\\\)/.test(path) ? path : cwd.replace(/[\\/]+$/, '') + '/' + path;
}

function shot(o, io) {
  const out = absolute(o.out, io.cwd);
  const after = absolute(o.after, io.cwd);
  const before = o.before ? absolute(o.before, io.cwd) : null;
  if (out === after || out === before) throw fail('--out must not overwrite a raw shot: keep raw shots in a folder of their own');
  const caption = normaliseCaption({ changed: o.changed, shows: o.shows, check: o.check }, before !== null);
  const sidecar = captionPath(out);
  for (const path of [out, sidecar]) if (io.isLink(path)) throw fail(path + ' is a symbolic link: write a new name');

  // the sidecars: each given one, and each raw shot's own beside it
  const read = (path) => {
    const text = io.readText(path);
    if (text === null) throw fail('no sidecar at ' + path);
    return parseSidecar(text, path);
  };
  const given = {};
  for (const k of ['both', 'before', 'after']) given[k] = o.boxesFrom[k] ? read(absolute(o.boxesFrom[k], io.cwd)) : null;
  const beside = {};
  for (const [k, raw] of [['after', after], ['before', before]]) {
    if (!raw) continue;
    const text = io.readText(sidecarPath(raw));
    beside[k] = text === null ? null : parseSidecar(text, sidecarPath(raw));
  }
  const own = { after: given.after || beside.after || given.both, before: before ? given.before || beside.before || given.both : null };
  const all = [given.both, given.before, given.after, beside.after, beside.before].filter(Boolean);
  for (const s of all) {
    if (s.problems.length) {
      throw fail(s.path + ' lists the capture\'s problems: ' + s.problems.join(' | ') + ' | fix the crop and shoot again');
    }
    edgeRoom(s);
  }
  if (o.scale !== null && !(o.scale > 0)) throw fail('the scale must be above 0, not ' + o.scale);
  const scale = resolveScale(o.scale, all);

  const afterSize = io.size(after);
  const beforeSize = before ? io.size(before) : null;
  // a sidecar describes one crop: the panel it marks must be that crop
  const fits = (s, size, name) => {
    if (!s || !size) return;
    const w = size.width / scale;
    const h = size.height / scale;
    if (Math.abs(w - s.crop.w) > 2 || Math.abs(h - s.crop.h) > 2) {
      throw fail(s.path + ' was written for a ' + s.crop.w + ' by ' + s.crop.h + ' crop, but the ' + name + ' shot is ' +
        Math.round(w) + ' by ' + Math.round(h) + ' at scale ' + scale + ': give each panel its own capture\'s sidecar');
    }
  };
  fits(given.both, afterSize, 'after');
  fits(given.both, beforeSize, 'before');
  fits(given.after || beside.after, afterSize, 'after');
  fits(given.before || beside.before, beforeSize, 'before');

  for (const s of [given.both, given.before, given.after]) {
    if (s && s.pad > (o.pad || 0)) {
      throw fail(s.path + ' says a box sits flush with the window\'s edge: compose with --pad ' + s.pad +
        ', a mat round the shot that gives the box its room');
    }
  }
  const whole = !!o.whole || all.some((x) => x.notes.some((n) => /spans the window/.test(n)));
  if (whole && o.arrange === 'side') throw fail('a bar shown whole is stacked, Before above After: leave out --side');
  const l = layout(afterSize, beforeSize, { scale, pad: o.pad || 0, arrange: o.arrange || undefined, whole });
  const boxes = panelBoxes(o, l, { both: given.both, before: given.before, after: given.after });
  lintComposite(l, { after: own.after && own.after.minText, before: own.before && own.before.minText });
  if (!io.draw) throw fail('a shot is drawn by AppKit: run it with osascript -l JavaScript on a Mac');
  const drawn = io.draw({ out, after, before, caption, l, boxes });
  io.writeText(sidecar, JSON.stringify(captionFile(caption, l, drawn.boxes), null, 2) + '\n');
  return 'wrote ' + out + ' (' + l.arrangement + ', ' + drawn.width + ' by ' + drawn.height + ') and ' + sidecar +
    '\n' + out.split('/').pop() + ': ' + headingText(caption) + '\n';
}

function main(argv, io) {
  let o;
  try {
    o = parseArgs(argv);
    if (o.mode === 'pack') {
      const folder = absolute(o.folder, io.cwd).replace(/[\\/]+$/, '');
      if (!io.isDir(folder)) throw fail('no folder ' + folder);
      const r = pack(io.list(folder), (name) => io.readText(folder + '/' + name));
      if (r.lines.length) io.out(r.lines.join('\n') + '\n');
      if (r.problems.length) {
        io.err('review_shot.js pack: ' + r.problems.length + ' refused in ' + folder + '\n' + r.problems.map((p) => '  ' + p).join('\n') + '\n');
        return 1;
      }
      return 0;
    }
    io.out(shot(o, io));
    return 0;
  } catch (e) {
    io.err('review_shot.js: ' + e.message + '\n');
    return e.refused ? (/^usage/.test(e.message) ? 2 : 1) : 1;
  }
}

// ── AppKit, on a Mac, through osascript

function appKitIO() {
  ObjC.import('AppKit');
  const fm = $.NSFileManager.defaultManager;
  const write = (handle, text) => handle.writeData($(text).dataUsingEncoding($.NSUTF8StringEncoding));
  return {
    cwd: fm.currentDirectoryPath.js,
    isDir: (p) => {
      const dir = Ref();
      return fm.fileExistsAtPathIsDirectory(p, dir) && dir[0] === true;
    },
    isLink: (p) => {
      const attrs = fm.attributesOfItemAtPathError(p, null);
      return !attrs.isNil() && ObjC.unwrap(attrs.objectForKey($.NSFileType)) === 'NSFileTypeSymbolicLink';
    },
    list: (p) => ObjC.deepUnwrap(fm.contentsOfDirectoryAtPathError(p, null)) || [],
    readText: (p) => {
      const s = $.NSString.stringWithContentsOfFileEncodingError(p, $.NSUTF8StringEncoding, null);
      return s.isNil() ? null : s.js;
    },
    writeText: (p, text) => {
      if (!$(text).writeToFileAtomicallyEncodingError(p, true, $.NSUTF8StringEncoding, null)) throw fail('could not write ' + p);
    },
    size: (p) => {
      const rep = readRep(p);
      return { width: Number(rep.pixelsWide), height: Number(rep.pixelsHigh) };
    },
    out: (text) => write($.NSFileHandle.fileHandleWithStandardOutput, text),
    err: (text) => write($.NSFileHandle.fileHandleWithStandardError, text),
    draw: drawAppKit,
  };
}

function readRep(path) {
  const data = $.NSData.dataWithContentsOfFile(path);
  const rep = data.isNil() ? null : $.NSBitmapImageRep.imageRepWithData(data);
  if (!rep || rep.isNil()) throw fail('no picture at ' + path);
  return rep;
}

function drawAppKit(job) {
  const l = job.l;
  const colour = (c, alpha) => $.NSColor.colorWithSRGBRedGreenBlueAlpha(c[0] / 255, c[1] / 255, c[2] / 255, alpha === undefined ? 1 : alpha);
  const semibold = (px) => {
    const f = $.NSFont.systemFontOfSizeWeight(px, 0.3);
    return f.isNil() ? $.NSFont.boldSystemFontOfSize(px) : f;
  };
  const attrs = (font, ink, extra) => {
    const keys = [$.NSFontAttributeName, $.NSForegroundColorAttributeName];
    const values = [font, ink];
    if (extra && extra.para) { keys.push($.NSParagraphStyleAttributeName); values.push(extra.para); }
    if (extra && extra.kern) { keys.push($.NSKernAttributeName); values.push($.NSNumber.numberWithDouble(extra.kern)); }
    return $.NSDictionary.dictionaryWithObjectsForKeys($(values), $(keys));
  };
  // a mutable string built a run at a time, since the bridge offers no initWithString:attributes:
  const append = (s, text, a) => {
    const at = Number(s.length);
    s.replaceCharactersInRangeWithString($.NSMakeRange(at, 0), text);
    s.setAttributesRange(a, $.NSMakeRange(at, text.length));
    return s;
  };
  const heading = (rs) => {
    const px = l.headingPx * rs;
    const para = $.NSMutableParagraphStyle.alloc.init;
    // a fixed line height: with a multiple, AppKit draws the lines taller than it measures them, and the
    // last line ran past the band's foot (fbboards2's 01 and 09, 20 October)
    para.minimumLineHeight = Math.round(l.headingPx * HEADING_LINE) * rs;
    para.maximumLineHeight = Math.round(l.headingPx * HEADING_LINE) * rs;
    para.paragraphSpacing = Math.round(l.headingPx * 0.25) * rs;
    const s = $.NSMutableAttributedString.alloc.init;
    const first = job.caption.changed !== null ? job.caption.changed : job.caption.shows || '';
    if (first !== '') append(s, first + '\n', attrs(semibold(px), colour(COLOURS.text), { para }));
    append(s, 'Check: ', attrs($.NSFont.boldSystemFontOfSize(px), colour(COLOURS.check), { para }));
    append(s, job.caption.check, attrs($.NSFont.systemFontOfSize(px), colour(COLOURS.text), { para }));
    return s;
  };
  const measure = (s, width) => {
    const r = s.boundingRectWithSizeOptions($.NSMakeSize(width, 1e7), $.NSStringDrawingUsesLineFragmentOrigin | $.NSStringDrawingUsesFontLeading);
    return { w: Math.ceil(r.size.width), h: Math.ceil(r.size.height) };
  };

  // the heading measured at one CSS pixel a pixel for the render scale, then again at that scale to draw
  let p = place(l, measure(heading(1), l.width - 2 * l.gutter).h);
  const rs = p.renderScale;
  const text = heading(rs);
  p = place(l, measure(text, (l.width - 2 * l.gutter) * rs).h / rs);
  const placed = placeBoxes(job.boxes, l, p);
  const W = Math.round(p.width * rs);
  const H = Math.round(p.height * rs);

  const out = $.NSBitmapImageRep.alloc.initWithBitmapDataPlanesPixelsWidePixelsHighBitsPerSampleSamplesPerPixelHasAlphaIsPlanarColorSpaceNameBytesPerRowBitsPerPixel(
    null, W, H, 8, 4, true, false, $.NSDeviceRGBColorSpace, 0, 0).bitmapImageRepByRetaggingWithColorSpace($.NSColorSpace.sRGBColorSpace);
  const ctx = $.NSGraphicsContext.graphicsContextWithBitmapImageRep(out);
  $.NSGraphicsContext.saveGraphicsState;
  $.NSGraphicsContext.setCurrentContext(ctx);
  ctx.imageInterpolation = $.NSImageInterpolationHigh;
  // AppKit's origin is the bottom left, the layout's the top left
  const R = (r) => $.NSMakeRect(r.x * rs, H - (r.y + r.h) * rs, r.w * rs, r.h * rs);
  const fill = (r, c, alpha) => { colour(c, alpha).setFill; $.NSRectFill(R(r)); };
  const fillOver = (r, c, alpha) => { colour(c, alpha).setFill; $.NSRectFillUsingOperation(R(r), $.NSCompositingOperationSourceOver); };

  fill({ x: 0, y: 0, w: p.width, h: p.height }, COLOURS.page);
  fill({ x: 0, y: 0, w: p.width, h: p.band }, COLOURS.band);
  text.drawWithRectOptions(R({ x: p.text.x, y: p.text.y, w: p.text.w, h: p.text.h + l.gutter }), $.NSStringDrawingUsesLineFragmentOrigin | $.NSStringDrawingUsesFontLeading);

  const pictures = { after: readRep(job.after), before: job.before ? readRep(job.before) : null };
  for (const panel of p.panels) {
    if (panel.label) {
      const word = panel.name === 'before' ? 'BEFORE' : 'AFTER';
      const ink = colour(panel.name === 'before' ? COLOURS.beforeInk : COLOURS.afterInk);
      const s = append($.NSMutableAttributedString.alloc.init, word, attrs(semibold(l.labelPx * rs), ink, { kern: l.labelPx * 0.06 * rs }));
      const size = measure(s, 1e6);
      const lb = panel.label;
      const pill = { x: lb.x, y: lb.y, w: size.w / rs + 2 * lb.padX, h: lb.h };
      colour(panel.name === 'before' ? COLOURS.before : COLOURS.after).setFill;
      const radius = Math.round(l.labelPx * 0.3) * rs;
      $.NSBezierPath.bezierPathWithRoundedRectXRadiusYRadius(R(pill), radius, radius).fill;
      s.drawWithRectOptions(R({ x: lb.x + lb.padX, y: lb.y + (lb.h - size.h / rs) / 2, w: size.w / rs + 2, h: size.h / rs + 2 }), $.NSStringDrawingUsesLineFragmentOrigin | $.NSStringDrawingUsesFontLeading);
    }
    // the mat, when there is one, stays the page's colour, and the thin edge line marks the shot's own border
    const mat = l.pad || 0;
    const im = { x: panel.image.x + mat, y: panel.image.y + mat, w: panel.image.w - 2 * mat, h: panel.image.h - 2 * mat };
    fill({ x: im.x - 1 / rs, y: im.y - 1 / rs, w: im.w + 2 / rs, h: im.h + 2 / rs }, COLOURS.edge);
    fill(im, [0xff, 0xff, 0xff]);
    pictures[panel.name].drawInRectFromRectOperationFractionRespectFlippedHints(R(im), $.NSMakeRect(0, 0, 0, 0), $.NSCompositingOperationSourceOver, 1, false, $());
  }
  // The halo follows the picture under the box: the pixels just outside and just inside its line are read from
  // the composite so far (the pictures are drawn, the dashes not yet). A light picture keeps the white halo, a
  // dark one gets its own average colour, so the dashes stand clear without a glow round the box.
  ctx.flushGraphics;
  const haloColour = (r, line) => {
    const pts = [];
    const steps = 24;
    for (let i = 0; i <= steps; i++) {
      const x = r.x + (r.w * i) / steps;
      const y = r.y + (r.h * i) / steps;
      for (const o of [-2 * line, 2 * line]) {
        pts.push([x, r.y + o], [x, r.y + r.h - o], [r.x + o, y], [r.x + r.w - o, y]);
      }
    }
    let sum = [0, 0, 0];
    let n = 0;
    for (const [x, y] of pts) {
      const px = Math.round(x * rs);
      const py = Math.round(y * rs);
      if (px < 0 || py < 0 || px >= W || py >= H) continue;
      const c = out.colorAtXY(px, py);
      if (c.isNil()) continue;
      const q = c.colorUsingColorSpace($.NSColorSpace.sRGBColorSpace);
      if (q.isNil()) continue;
      sum[0] += Number(q.redComponent) * 255;
      sum[1] += Number(q.greenComponent) * 255;
      sum[2] += Number(q.blueComponent) * 255;
      n++;
    }
    if (n === 0) return COLOURS.halo;
    const mean = sum.map((v) => Math.round(v / n));
    const lum = (0.2126 * mean[0] + 0.7152 * mean[1] + 0.0722 * mean[2]) / 255;
    return lum >= 0.5 ? COLOURS.halo : mean;
  };
  for (const r of placed.rects) {
    const halo = Math.max(1, Math.round(l.line / 3));
    const under = haloColour(r, l.line);
    for (const d of dashes(r, l.line)) fillOver({ x: d.x - halo, y: d.y - halo, w: d.w + 2 * halo, h: d.h + 2 * halo }, under, 0.9);
    for (const d of dashes(r, l.line)) fill(d, COLOURS.mark);
  }
  $.NSGraphicsContext.restoreGraphicsState;

  const dir = job.out.replace(/\/[^/]*$/, '');
  $.NSFileManager.defaultManager.createDirectoryAtPathWithIntermediateDirectoriesAttributesError(dir, true, $(), null);
  const png = out.representationUsingTypeProperties($.NSBitmapImageFileTypePNG, $());
  if (!png.writeToFileAtomically(job.out, true)) throw fail('could not write ' + job.out);
  return { width: W, height: H, boxes: placed.boxes };
}

// osascript calls this with the command line's words
function run(argv) {
  ObjC.import('stdlib');
  const code = main(ObjC.deepUnwrap(argv) || [], appKitIO());
  $.exit(code);
}

// A PNG's width and height from its header, for node, which has no AppKit to ask.
function pngSize(fs, path) {
  let head;
  try {
    const fd = fs.openSync(path, 'r');
    head = Buffer.alloc(24);
    fs.readSync(fd, head, 0, 24, 0);
    fs.closeSync(fd);
  } catch (e) {
    throw fail('no picture at ' + path);
  }
  if (head.readUInt32BE(0) !== 0x89504e47 || head.toString('latin1', 12, 16) !== 'IHDR') throw fail('no picture at ' + path + ' (not a PNG)');
  return { width: head.readUInt32BE(16), height: head.readUInt32BE(20) };
}

// node: the pure functions for the suite, and the pack from the command line
if (typeof module !== 'undefined' && module.exports) {
  module.exports = {
    MIN_HEADING_PX, HEADING_RATIO, STACK_ASPECT, MAX_RENDER_PX, EDGE_CLEAR, MAX_COMPOSITE_PX, SHOWN_WIDTH, MIN_SHOWN_TEXT,
    COLOURS, layout, place, parseBox, dashes, normaliseCaption, headingText, captionPath, captionFile, parseCaptionFile,
    pack, parseArgs, sidecarPath, parseSidecar, edgeRoom, resolveScale, handPad, panelBoxes, lintComposite, placeBoxes, shot, main,
  };
  if (require.main === module) {
    const fs = require('fs');
    const io = {
      cwd: process.cwd(),
      isDir: (p) => { try { return fs.statSync(p).isDirectory(); } catch (e) { return false; } },
      isLink: (p) => { try { return fs.lstatSync(p).isSymbolicLink(); } catch (e) { return false; } },
      list: (p) => fs.readdirSync(p),
      readText: (p) => { try { return fs.readFileSync(p, 'utf8'); } catch (e) { return null; } },
      writeText: (p, t) => fs.writeFileSync(p, t, 'utf8'),
      size: (p) => pngSize(fs, p),
      out: (t) => process.stdout.write(t),
      err: (t) => process.stderr.write(t),
      draw: null,
    };
    process.exitCode = main(process.argv.slice(2), io);
  }
}
